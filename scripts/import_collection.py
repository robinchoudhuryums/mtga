#!/usr/bin/env python3
"""Import a FULL-COLLECTION export (a third-party tracker's CSV) into card-library.csv.

This is the counterpart to `import_arena.py`, and the difference is the whole point.

    import_arena.py   ingests a DECK dump. Each line is how many that deck plays, which
                      is a LOWER BOUND on what you own, so it takes max(existing, line)
                      and can never learn that you own fewer.
    import_collection.py  ingests a COLLECTION export. That is AUTHORITATIVE, so it sets
                      Quantity Owned EXACTLY — including DOWN, which nothing else here
                      could do without `reconcile_crafts.py --set-exact` one card at a
                      time.

That gap is the project's stated bottleneck (ROADMAP: "the recurring bottleneck is data
entry — keeping owned quantities accurate is manual because Arena no longer logs the
collection"), and it is why "not in library for a card you own" is a RECURRING symptom
and why reconcile_crafts.py exists at all — a repair tool for a problem that only exists
because ingestion undercounts by construction.

FORMAT: deliberately not hard-coded to one tracker. Every exporter writes "a CSV with a
name column and a quantity column" under a different spelling, so columns are detected by
ALIAS (see `_ALIASES`) against the header row, case- and punctuation-insensitively, and
the delimiter is sniffed so TSV works too. If a required column can't be identified the
tool STOPS and prints the header it actually saw plus a `--map` example — it never
guesses, because a mis-mapped quantity column would silently rewrite the whole inventory.

SAFETY, because this is the only tool here that can lower a count:
  * dry-run by default; `--apply` writes, via lib.write_rows (temp -> timestamped .bak ->
    atomic replace), so an interrupted write can't truncate the inventory;
  * a SHRINK GUARD refuses an export covering far fewer cards than the library already
    has (the same guard build_pool.py / build_mana.py use), since the likeliest mistake
    is feeding it a partial export;
  * cards absent from the export are LEFT ALONE by default and only zeroed with
    `--zero-missing`, so a filtered export can't quietly delete your collection;
  * a new card name gets a BLANK card-mana.csv row so INV-02 holds immediately (the same
    thing reconcile_crafts.py and app.py do); build_mana.py fills the cost later.

Usage:
    python3 scripts/import_collection.py collection.csv              # dry run
    python3 scripts/import_collection.py collection.csv --apply
    python3 scripts/import_collection.py collection.csv --apply --zero-missing
    python3 scripts/import_collection.py export.tsv --map name=Card,qty=Have
    python3 scripts/import_collection.py - --apply                   # from stdin

After --apply, regenerate derived data (a new card has no mana cost or tags yet):
    make refresh
    python3 scripts/verify_ingest.py export.tsv --exact   # authoritative route

(This used to restate the chain, in the wrong order — the Makefile's `refresh`
target is the one executable definition. `--exact` is right HERE and nowhere else:
a tracker export is authoritative, so owned must equal pasted.)
"""

import argparse
import csv
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (DEFAULT_CSV, REPO_ROOT, load_rows, write_rows,  # noqa: E402
                 atomic_write, eprint)

MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")
MANA_HEADER = ["Card Name", "Mana Cost", "Mana Value", "Keywords"]

# Basic lands are unlimited in Arena and deliberately absent from the collection
# (CLAUDE.md); a tracker that exports them must not add them.
BASICS = {"plains", "island", "swamp", "mountain", "forest", "wastes"}

# Column aliases, lowercased with punctuation/space stripped by `_norm_key`. Ordered
# most-specific first so "collector number" can't be eaten by "number".
_ALIASES = {
    "name": ["cardname", "name", "card", "title", "englishname"],
    "qty": ["quantityowned", "quantity", "qty", "count", "have", "owned",
            "numberowned", "amount", "total"],
    "set": ["setcode", "set", "edition", "expansion", "setid"],
    "collector": ["collectornumber", "collectorno", "collector", "cardnumber",
                  "number", "num", "cn"],
    # Optional: foil/non-foil live on separate export rows sharing (name, set,
    # collector) in real tracker exports — the finish column is what tells them
    # apart, and ignoring it halved those holdings (broad-scan BS-15).
    "finish": ["finish", "foil", "isfoil", "foiltype", "printingtype"],
}
# Fraction of the library the export must cover before it is trusted to rewrite counts.
_SHRINK_FLOOR = 0.5


def _norm_key(s):
    """Header cell -> comparable key: lowercase, alphanumerics only."""
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())


def detect_columns(header, overrides=None):
    """{role: actual_header_name} for name/qty/set/collector, or raise ValueError.

    Only `name` and `qty` are required — set/collector merely make the match precise.
    Raises rather than guessing: a mis-identified quantity column would rewrite every
    count in the inventory, so an unrecognised header must stop the run."""
    got = {}
    by_norm = {_norm_key(h): h for h in header if h}
    for role, names in _ALIASES.items():
        for cand in names:
            if cand in by_norm:
                got[role] = by_norm[cand]
                break
    for role, actual in (overrides or {}).items():
        if role not in _ALIASES:
            raise ValueError(f"unknown --map role {role!r}; expected one of "
                             f"{', '.join(sorted(_ALIASES))}")
        if actual not in header:
            raise ValueError(f"--map {role}={actual!r}: no such column. "
                             f"The file's columns are: {', '.join(header)}")
        got[role] = actual
    missing = [r for r in ("name", "qty") if r not in got]
    if missing:
        raise ValueError(
            f"could not identify the {' and '.join(missing)} column(s).\n"
            f"       Columns found: {', '.join(header) or '(none)'}\n"
            f"       Map them explicitly, e.g. "
            f"--map name=<column>,qty=<column>")
    return got


def _read_table(text):
    """(header, rows) from CSV or TSV text. Sniffs the delimiter, falling back to comma."""
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    return (reader.fieldnames or []), [dict(r) for r in reader]


def _front(name):
    """The front face of a `A // B` name."""
    return (name or "").split(" // ")[0].strip()


# CLAUDE.md states the library keys a double-faced card under its FRONT name — and that
# is true of DFCs, but NOT universal in the data: the six DSK Room cards are stored under
# the full "Bottomless Pool // Locker Room". Front-truncating every export name therefore
# reported all six as brand-new cards on the first real run. Match the way `lib.owned_qty`
# does — full name first, then the front face — so both conventions resolve.


def parse_export(text, overrides=None):
    """(entries, warnings, unreadable) from a tracker export.
    entries: [(qty, name, set, collector)]. unreadable: card names whose quantity cell
    could not be read as a non-negative integer.

    Quantities are read strictly: a blank or non-numeric count is reported rather than
    silently treated as 0, because this tool SETS counts and a mis-read cell would
    delete a card's copies. The `unreadable` names exist so `plan` can honour that
    promise on the --zero-missing path too: a dropped row used to leave the card out of
    `entries`, and the zero pass then read "not in entries" as "absent from the export"
    — so an unreadable cell ("1,024", "4 (foil)", "2.0") became 0 by a different route,
    the exact outcome the strict read exists to prevent (broad-scan BS2-03). A tracker
    whose whole quantity column is formatted that way zeroed the collection in one
    --apply --zero-missing."""
    header, rows = _read_table(text)
    cols = detect_columns(header, overrides)
    warnings, unreadable = [], []
    # One output entry per (front, set, collector) printing, FINISH-aware: foil and
    # non-foil are separate Arena copies that real tracker exports emit as separate
    # rows sharing set and collector, distinguished only by a finish column. The old
    # key-blind path fed both rows to plan(), whose repeated-key collapse takes max —
    # so 2 foil + 2 non-foil imported as 2, and since this is the ONE tool that can
    # lower a count, a correct prior 4 was REDUCED (broad-scan BS-15; the same
    # failure shape as F-01, one column over). Per (printing, finish) a repeat still
    # takes MAX (one holding stated twice); DISTINCT finishes SUM.
    #
    # That max-on-repeat reading rests on the printing key being REAL. When the export
    # has NO set/collector column at all, every row of a card shares the degenerate key
    # ("name", "", ""), so two genuinely distinct printings (2× M19 + 1× DOM = 3 owned)
    # collapsed to max = 2 — a silent LOWERING on the one tool that can lower a count,
    # F-01's failure one column over (broad-scan BS2-04). A tracker exports one row per
    # PRINTING (the premise the summing rule above already rests on), so with no
    # printing columns a repeated name means distinct printings: SUM, and say so.
    fin_col = cols.get("finish")
    printing_cols = bool(cols.get("set") or cols.get("collector"))
    groups, order, name_rows = {}, [], {}
    for i, r in enumerate(rows, start=2):          # row 1 is the header
        name = (r.get(cols["name"]) or "").strip()
        if not name:
            continue                               # blank spacer row
        raw = (r.get(cols["qty"]) or "").strip()
        if not raw.isdigit():
            warnings.append(f"row {i} ({name}): quantity {raw!r} is not a "
                            f"non-negative integer — row left unchanged (it is NOT "
                            f"treated as absent, so --zero-missing cannot zero it)")
            unreadable.append(name)
            continue
        setc = (r.get(cols.get("set", "")) or "").strip() if cols.get("set") else ""
        coll = (r.get(cols.get("collector", "")) or "").strip() if cols.get("collector") else ""
        if _front(name).lower() in BASICS:
            continue                               # unlimited in Arena; not collection data
        fin = (r.get(fin_col) or "").strip().lower() if fin_col else ""
        key = (_front(name).lower(), setc.lower(), coll.lower())
        g = groups.get(key)
        if g is None:
            g = groups[key] = {"disp": (name, setc, coll), "fins": {}}
            order.append(key)
        if printing_cols:
            g["fins"][fin] = max(g["fins"].get(fin, 0), int(raw))
        else:
            # No printing columns: each row is a distinct printing — sum them.
            g["fins"][fin] = g["fins"].get(fin, 0) + int(raw)
            name_rows[key] = name_rows.get(key, 0) + 1
    for key, n in name_rows.items():
        if n > 1:
            warnings.append(f"{groups[key]['disp'][0]}: {n} export rows share no "
                            f"set/collector column — read as distinct printings and "
                            f"SUMMED to {sum(groups[key]['fins'].values())}")
    entries = [(sum(groups[k]["fins"].values()), *groups[k]["disp"]) for k in order]
    return entries, warnings, unreadable


def plan(rows, entries, *, zero_missing=False, unreadable=()):
    """Work out the changes without touching anything. Returns a dict of:
        updated   [(name, old, new)]      a printing whose count changes
        added     [(name, set, coll, n)]  a printing the library doesn't have
        zeroed    [(name, old)]           owned here, absent from the export
        ambiguous [(name, n, printings)]  name-only row, several printings to choose from
    A name-only export row for a card the library holds in SEVERAL printings is reported,
    never guessed at: the export says how many you own in total but not which printing to
    put them on, and picking one would silently zero the other.

    `unreadable` (from `parse_export`) names cards whose quantity cell could not be
    read. They are marked SEEN so the --zero-missing pass leaves them alone: the export
    mentioned them, so "absent from the export" is false — dropping them into the zero
    pass was how a mis-read cell deleted a card's copies (broad-scan BS2-03)."""
    by_print, by_name = {}, {}
    for r in rows:
        stored = (r.get("Card Name") or "").strip()
        setc = (r.get("Set Code") or "").strip().lower()
        coll = (r.get("Collector #") or "").strip().lower()
        # Index under BOTH the stored name and its front face, so an export naming the
        # full "A // B" and one naming just "A" both resolve to the same printing.
        for alias in {stored.lower(), _front(stored).lower()}:
            by_print.setdefault((alias, setc, coll), r)
            by_name.setdefault(alias, [])
            if r not in by_name[alias]:
                by_name[alias].append(r)

    updated, added, ambiguous = [], [], []
    seen_rows = set()
    # Unreadable-quantity cards are PRESENT in the export even though no count could be
    # read — protect every library row they resolve to (full name or front face) from
    # the zero pass, matching the strict-read promise in parse_export's docstring.
    for name in unreadable:
        for alias in {name.lower(), _front(name).lower()}:
            for r in by_name.get(alias, []):
                seen_rows.add(id(r))

    # SEVERAL export rows can resolve to ONE library row, and they must SUM.
    #
    # A tracker exports one row per PRINTING while the library may hold fewer printings
    # of that card, so an export listing `2x (M19) 314` + `1x (DOM) 168` against a library
    # holding only the DOM printing resolves both entries onto that single row. Assigning
    # each in turn made the LAST one win and silently drop the rest: the row landed on 1
    # or 2 depending on export order, against a real 3. Order-dependent, and invisible in
    # the report — the surviving-entry-last case prints one clean "1 -> 2" line and looks
    # correct. This is the ONLY tool here that may lower a count, so a silent undercount
    # from it is the worst failure in the ingest subsystem (broad-scan F-01).
    #
    # Two passes: accumulate the intended total per row, then write each row ONCE, so
    # `updated` also reports one net change per row instead of a self-cancelling pair.
    #
    # Summing is right for DISTINCT printings and wrong for a repeated one: a tracker that
    # emits the same (name, set, collector) twice is stating one holding twice, not two
    # holdings, and summing there would over-count exactly where the old last-wins was
    # correct. So collapse identical export keys FIRST, taking the max — the same reading
    # `import_arena` applies to a repeated line — and only then sum across the distinct
    # printings that remain.
    deduped, seen_keys = [], {}
    for qty, name, setc, coll in entries:
        ek = (_front(name).lower(), setc.lower(), coll.lower())
        if ek in seen_keys:
            i = seen_keys[ek]
            deduped[i] = (max(deduped[i][0], qty), *deduped[i][1:])
            continue
        seen_keys[ek] = len(deduped)
        deduped.append((qty, name, setc, coll))
    entries = deduped

    totals, order = {}, []
    new_idx, new_order = {}, []

    def _want(row, n):
        k = id(row)
        seen_rows.add(k)
        if k not in totals:
            totals[k] = [row, 0]
            order.append(k)
        totals[k][1] += n

    for qty, name, setc, coll in entries:
        # Full name first, then the front face — `lib.owned_qty`'s rule.
        aliases = [name.lower()]
        if _front(name).lower() != aliases[0]:
            aliases.append(_front(name).lower())
        exact = next((by_print[(a, setc.lower(), coll.lower())] for a in aliases
                      if (a, setc.lower(), coll.lower()) in by_print), None)
        if exact is not None:
            _want(exact, qty)
            continue
        same_name = next((by_name[a] for a in aliases if by_name.get(a)), [])
        nl = aliases[0]
        if len(same_name) == 1:
            _want(same_name[0], qty)
        elif len(same_name) > 1:
            # Deduped by name: a name-only export carries one row per printing, so the
            # same unresolvable name would otherwise be reported once per copy.
            if not any(a[0] == name for a in ambiguous):
                ambiguous.append((name, qty,
                                  [f"{(r.get('Set Code') or '?')} {(r.get('Collector #') or '?')}"
                                   for r in same_name]))
            for r in same_name:
                seen_rows.add(id(r))               # not a "missing" card, just unresolved
        else:
            # A genuinely new card is stored under its FRONT name, the convention every
            # ownership join here expects (reconcile_crafts.py / app.py do the same).
            # Keyed and summed for the same reason the library rows are: two export lines
            # naming the SAME new printing would otherwise append two rows for it, which
            # is a duplicate (Card Name, Set Code, Collector #) — an INV-01 break written
            # by the importer itself.
            ak = (_front(name).lower(), setc.lower(), coll.lower())
            if ak in new_idx:
                new_idx[ak][3] += qty
            else:
                new_idx[ak] = [_front(name), setc, coll, qty]
                new_order.append(ak)

    # Apply the accumulated totals — one write, and one `updated` line, per row.
    for k in order:
        row, n = totals[k]
        old = (row.get("Quantity Owned") or "").strip()
        if old != str(n):
            updated.append(((row.get("Card Name") or "").strip(), old or "0", str(n)))
            row["Quantity Owned"] = str(n)
    added = [tuple(new_idx[k]) for k in new_order]

    zeroed = []
    for r in rows:
        if id(r) in seen_rows:
            continue
        old = (r.get("Quantity Owned") or "").strip()
        if old and old != "0":
            zeroed.append(((r.get("Card Name") or "").strip(), old))
            if zero_missing:
                r["Quantity Owned"] = "0"
    return {"updated": updated, "added": added, "zeroed": zeroed, "ambiguous": ambiguous}


def _ensure_mana_rows(names):
    """Append a BLANK card-mana.csv row per new name so INV-02 (every library name has a
    mana row) holds the moment the library write lands. Same reasoning as
    reconcile_crafts.py: a blank row keeps the invariant and build_mana.py fills in the
    real cost, where a MISSING row is a hard integrity failure. Returns names added."""
    have, header, body = set(), MANA_HEADER, []
    if os.path.exists(MANA_CSV):
        with open(MANA_CSV, newline="", encoding="utf-8") as fh:
            existing = list(csv.reader(fh))
        if existing:
            header, body = existing[0], existing[1:]
        have = {(r[0] or "").strip().lower() for r in body if r}
    added = []
    for n in names:
        if n and n.lower() not in have:
            have.add(n.lower())
            body.append([n, "", "", ""])
            added.append(n)
    if added:
        atomic_write(MANA_CSV, lambda fh: csv.writer(fh).writerows([header] + body))
    return added


def _report(result, entries, rows, zero_missing):
    def section(title, items, fmt):
        print(f"\n{title}: {len(items)}")
        for x in items[:20]:
            print(f"   {fmt(x)}")
        if len(items) > 20:
            print(f"   … and {len(items) - 20} more")

    print(f"Export: {len(entries)} card line(s).  Library: {len(rows)} printing(s).")
    section("Quantity changes", result["updated"], lambda x: f"{x[0]}: {x[1]} -> {x[2]}")
    section("New to the library", result["added"],
            lambda x: f"{x[0]} ({x[1] or '—'}) {x[2]} x{x[3]}")
    if result["ambiguous"]:
        section("AMBIGUOUS — name-only row, several printings owned (left unchanged)",
                result["ambiguous"],
                lambda x: f"{x[0]} x{x[1]} — printings: {', '.join(x[2])}")
        print("   Re-export with a set/collector column, or set these by hand.")
    label = ("Set to 0 (owned here, absent from the export)" if zero_missing
             else "Owned here but ABSENT from the export (left alone; --zero-missing to zero)")
    section(label, result["zeroed"], lambda x: f"{x[0]} (was {x[1]})")


def main():
    ap = argparse.ArgumentParser(
        description="Import a full-collection tracker export (sets EXACT quantities).")
    ap.add_argument("source", help="path to the export, or '-' for stdin")
    ap.add_argument("--library", default=DEFAULT_CSV, help="card-library.csv path")
    ap.add_argument("--apply", action="store_true",
                    help="write the changes (default: dry run, nothing written)")
    ap.add_argument("--zero-missing", action="store_true",
                    help="set cards absent from the export to 0 (they are left alone by "
                         "default, so a partial export can't wipe the collection)")
    ap.add_argument("--map", default="",
                    help="explicit column mapping when auto-detection fails, e.g. "
                         "name=Card,qty=Have,set=Edition")
    ap.add_argument("--allow-shrink", action="store_true",
                    help="permit an export covering far fewer cards than the library "
                         "(the guard exists because a PARTIAL export is the likely mistake)")
    args = ap.parse_args()

    try:
        text = sys.stdin.read() if args.source == "-" else \
            open(args.source, encoding="utf-8-sig").read()
    except OSError as e:
        eprint(f"Could not read {args.source!r}: {e}")
        return 1

    overrides = {}
    for part in [p for p in args.map.split(",") if p.strip()]:
        if "=" not in part:
            eprint(f"ERROR: --map entry {part!r} is not role=column.")
            return 1
        role, actual = part.split("=", 1)
        overrides[role.strip()] = actual.strip()

    try:
        entries, warnings, unreadable = parse_export(text, overrides)
    except ValueError as e:
        eprint(f"ERROR: {e}")
        return 1
    for w in warnings:
        eprint(f"WARN:  {w}")
    if unreadable and args.zero_missing:
        eprint(f"WARN:  {len(unreadable)} card(s) had unreadable quantity cells — they "
               "are left UNCHANGED, not zeroed. Fix the export's quantity column (or "
               "--map qty=<column>) if these should be set.")
    if not entries:
        eprint("No usable card rows found in the export.")
        return 1

    try:
        _, rows = load_rows(args.library)
    except FileNotFoundError:
        rows = []

    # Shrink guard. A collection export should cover roughly the whole library; one that
    # covers a fraction of it is far more likely a filtered/partial export than a real
    # mass disenchant, and this is the one tool that can act on that difference.
    if (not args.allow_shrink and rows
            and len(entries) < len(rows) * _SHRINK_FLOOR):
        eprint(f"ERROR: the export lists {len(entries)} card(s) but the library has "
               f"{len(rows)} printing(s) — refusing to treat that as authoritative "
               f"(left unchanged).\n"
               f"       A partial or filtered export is the likely cause. Pass "
               f"--allow-shrink if the narrowing is real.")
        return 1

    result = plan(rows, entries, zero_missing=args.zero_missing, unreadable=unreadable)
    _report(result, entries, rows, args.zero_missing)

    changed = result["updated"] or result["added"] or (
        result["zeroed"] and args.zero_missing)
    if not args.apply:
        print("\n(dry run — pass --apply to write card-library.csv / card-mana.csv "
              "with .bak backups)")
        return 0
    if not changed:
        print("\nNothing to write — the library already matches the export.")
        return 0

    for name, setc, coll, qty in result["added"]:
        rows.append({"Card Name": name, "Type": "", "Card Text": "", "Color(s)": "",
                     "Synergies": "", "Set Code": setc, "Collector #": coll,
                     "Quantity Owned": str(qty)})
    write_rows(rows, args.library)
    # Only AFTER the library write lands, so a rejected write can't strand the mana file
    # out of step with it (the ordering app.py's add()/remove() use for the same reason).
    mana_added = _ensure_mana_rows([n for n, _s, _c, _q in result["added"]])
    print(f"\nApplied to {args.library} (with a .bak).")
    if mana_added:
        print(f"Added {len(mana_added)} blank card-mana.csv row(s) to keep INV-02.")
    print("Next — new cards need their derived data rebuilt (INV-02 stays red until "
          "it runs):\n  make refresh\n"
          "Then confirm the import landed, with the AUTHORITATIVE reading:\n"
          f"  python3 scripts/verify_ingest.py {args.source} --exact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
