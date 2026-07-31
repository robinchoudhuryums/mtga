#!/usr/bin/env python3
"""Did the ingest actually land? Check a paste against the library it was supposed to
write to.

Five tools write owned-card data and every failure mode they have is a SILENT
UNDERCOUNT: `import_arena` takes `max()` by construction, `reconcile_crafts` can't lower
a count, a deck-dump line is a lower bound, and a card that never parsed is reported once
and then forgotten. Each tool reports what IT did; nothing reads the result back and
answers the only question that matters afterwards — "of the N cards I pasted, are all N
in the library at the count I expect?"

That question has no gate. `check_all` verifies the library is INTERNALLY consistent
(INV-01) and fully covered by card-mana.csv (INV-02); both stay green when a card you
pasted never arrived, because a card that isn't there breaks no invariant. This closes
the loop by comparing the paste to the result.

Three checks per pasted line:

  1. PRESENT   — the card is in card-library.csv at all.
  2. QUANTITY  — owned >= pasted (the lower-bound routes), or == with `--exact` (the
                 authoritative `import_collection.py` route, the only one that may
                 lower a count).
  3. INV-02    — the card has a card-mana.csv row. This is the step people skip: a new
                 card has no mana row until `build_mana.py` runs, so its cost and
                 keyword tags are blank and check_all is already red. Scoped per card,
                 so you learn WHICH of your new cards is missing rather than a total.

Ownership lookups go through `lib.owned_qty`, so a double-faced card pasted as
`Front // Back` resolves against the library's FRONT-name key instead of reading as
missing (audit F6). The Arena-export parser is `import_arena.parse` rather than a fourth
copy of the same regex.

Basic lands are skipped by default: they are unlimited in Arena and deliberately absent
from the collection, so checking them would report a false miss on every paste that
contains one. (`import_arena`'s flag is the opposite polarity on purpose — it decides
what to WRITE, this decides what to CHECK.)

Usage:
    python3 scripts/verify_ingest.py cards.txt        # after /ingest
    pbpaste | python3 scripts/verify_ingest.py -
    python3 scripts/verify_ingest.py cards.txt --exact       # tracker-export route
    python3 scripts/verify_ingest.py cards.txt --include-basics
"""

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint, owned_qty  # noqa: E402
from import_arena import parse, BASICS  # noqa: E402

MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")

# `mana_names()` returns None to mean "card-mana.csv does not exist", so None cannot also
# mean "caller didn't supply it" — one sentinel for two states is how a caller passing the
# real absent-file value gets silently re-routed into loading the file again. A distinct
# sentinel keeps the two apart.
_UNSET = object()


def library_index(path=None):
    """(quantities, names) — {name_lower: total copies} and the set of library keys.

    Quantities are SUMMED across printings: owned copies are fungible in Arena, so a
    card owned 1x in two sets is 2 (CLAUDE.md). Counting a single printing would report
    a real ingest as short.
    """
    path = path or DEFAULT_CSV
    qty, names = {}, set()
    _, rows = load_rows(path)
    for r in rows:
        name = (r.get("Card Name") or "").strip()
        if not name:
            continue
        names.add(name.lower())
        raw = (r.get("Quantity Owned") or "").strip()
        try:
            qty[name.lower()] = qty.get(name.lower(), 0) + (int(raw) if raw else 0)
        except ValueError:
            continue                      # INV-01's problem, not this tool's
    return qty, names


def mana_names(path=None):
    path = path or MANA_CSV
    if not os.path.exists(path):
        return None                       # distinct from "empty" — see report()
    with open(path, newline="", encoding="utf-8") as fh:
        return {(r.get("Card Name") or "").strip().lower() for r in csv.DictReader(fh)}


def _library_key(names, name):
    """The key the LIBRARY stores this card under: the full name if present, else the
    front face. Mirrors `owned_qty`'s resolution order so the quantity check and the
    INV-02 check can't disagree about which row they are talking about."""
    nl = (name or "").strip().lower()
    if nl in names:
        return nl
    front = nl.split(" // ")[0]
    return front if front in names else None


def _row_key(r):
    """The LIBRARY ROW a result belongs to — its resolved key, else its own name. The one
    identity `verify` sums a paste on and `report` dedupes by, so the two can't disagree
    about which lines describe the same card."""
    return r["key"] or r["name"].strip().lower()


def verify(text, *, exact=False, include_basics=False, lib=None, mana=_UNSET):
    """(results, warnings) — one result dict per pasted line.

    Each result: {qty, pasted, name, owned, key, present, enough, has_mana, basic}.
    `qty` is THIS line's quantity; `pasted` is the total across every line resolving to
    the same library row. Pure over its inputs so the report and the tests read the same
    data.

    The quantity check compares owned against `pasted`, not `qty`, because the two sides
    are counted at different granularities: a tracker exports one line per PRINTING while
    `library_index` (and `lib.owned_qty`, and every ownership join in the repo) SUMS
    copies across printings. Comparing a summed total against one line's share made
    `--exact` structurally unable to pass a correct multi-printing import — `2x (M19)` +
    `1x (DOM)` against a correctly-stored 3 reported both lines wrong — and, in the
    default lower-bound mode, let a real shortfall hide: owned 2 against lines of 2 and 1
    passed both `>=` tests while the paste claimed 3. This is the read half of the
    accumulation fix in `import_collection.plan` (broad-scan F-01); the two must agree
    about what a card's quantity MEANS or the authoritative route has no working check.
    """
    entries, warnings = parse(text)
    quantities, names = lib if lib is not None else library_index()
    known_mana = mana_names() if mana is _UNSET else mana

    # Sum the paste per LIBRARY ROW first — keyed the way the library resolves the name
    # (full, else DFC front), so two spellings of one card also land on one total. An
    # unresolvable name keys on itself, so absent cards still report their own quantity.
    totals = {}
    for qty, name, _set, _cn in entries:
        if name.strip().lower() in BASICS and not include_basics:
            continue
        k = _library_key(names, name) or name.strip().lower()
        totals[k] = totals.get(k, 0) + qty

    results = []
    for qty, name, _set, _cn in entries:
        basic = name.strip().lower() in BASICS
        if basic and not include_basics:
            results.append({"qty": qty, "pasted": qty, "name": name, "owned": None,
                            "key": None, "present": True, "enough": True,
                            "has_mana": True, "basic": True})
            continue
        key = _library_key(names, name)
        have = owned_qty(quantities, name)
        pasted = totals.get(key or name.strip().lower(), qty)
        results.append({
            "qty": qty, "pasted": pasted, "name": name, "owned": have, "key": key,
            "present": key is not None,
            "enough": (have == pasted) if exact else (have >= pasted),
            # Unknown rather than False when card-mana.csv is absent — that is a
            # different failure (INV-03) and saying "no mana row" per card would
            # misattribute it to the ingest.
            "has_mana": True if known_mana is None else (
                key is not None and key in known_mana),
            "basic": basic,
        })
    return results, warnings


def report(results, warnings, *, exact=False, mana_missing=False):
    """Print the verdict. Returns an exit code."""
    checked = [r for r in results if not r["basic"]]
    basics = len(results) - len(checked)
    absent = [r for r in checked if not r["present"]]
    short = [r for r in checked if r["present"] and not r["enough"]]
    nomana = [r for r in checked if r["present"] and not r["has_mana"]]
    ok = len(checked) - len(absent) - len(short)

    print(f"Pasted {len(results)} line(s); checked {len(checked)}"
          + (f" ({basics} basic land line(s) skipped — unlimited in Arena, "
             f"deliberately not in the collection)" if basics else "") + ".")
    print(f"  {ok}/{len(checked)} present at the expected count "
          f"({'exactly' if exact else 'at least'} the pasted quantity).\n")

    for w in warnings:
        eprint(f"WARN:  {w}")
    if warnings:
        eprint("       Unparseable lines were never ingested by ANY tool — they are not "
               "in the library because nothing ever wrote them.\n")

    if absent:
        print(f"✗ {len(absent)} card(s) NOT in card-library.csv — the ingest did not "
              f"write them:")
        for r in absent:
            print(f"    {r['qty']}x {r['name']}")
        print("  Re-run the ingest for these (see /ingest), or check the spelling "
              "against the export.\n")

    if short:
        # Deduped by library row: several pasted PRINTINGS of one card share ONE owned
        # total, so reporting per line would name the same card once per printing and
        # invite the reader to add the shortfalls up.
        lines_for = {}
        for r in results:
            lines_for[_row_key(r)] = lines_for.get(_row_key(r), 0) + 1
        seen_short, uniq = set(), []
        for r in short:
            if _row_key(r) not in seen_short:
                seen_short.add(_row_key(r))
                uniq.append(r)
        short = uniq
        word = "does not equal" if exact else "is below"
        print(f"✗ {len(short)} card(s) present but the owned count {word} what you "
              f"pasted:")
        for r in short:
            n_lines = lines_for.get(_row_key(r), 1)
            note = f" (summed over {n_lines} pasted printings)" if n_lines > 1 else ""
            print(f"    {r['name']}: library has {r['owned']}, paste said "
                  f"{r['pasted']}{note}")
        if not exact:
            print("  A deck-dump import takes max(existing, line), so a lower count "
                  "here means the line never applied.")
        else:
            print("  --exact is the authoritative (tracker-export) reading; a mismatch "
                  "means import_collection.py did not set this row.")
        print()

    if mana_missing:
        print("⚠ card-mana.csv is absent entirely — that is INV-03, not an ingest "
              "problem. Run: make refresh\n")
    elif nomana:
        print(f"⚠ {len(nomana)} card(s) in the library with NO card-mana.csv row — "
              f"INV-02 is currently failing for these, and their cost and keyword "
              f"tags are blank:")
        for r in nomana:
            print(f"    {r['name']}")
        print("  This is the step that gets skipped. Run: make refresh  "
              "(or at minimum build_mana.py --pool, then tag_synergies.py --merge)\n")

    if not (absent or short or nomana or mana_missing or warnings):
        print("✓ Everything you pasted is in the library at the expected count, with "
              "mana coverage. The ingest is complete.")
        return 0
    return 1


def main():
    ap = argparse.ArgumentParser(
        description="Verify that a pasted Arena export actually landed in "
                    "card-library.csv.")
    ap.add_argument("source", help="export file, or '-' for stdin")
    ap.add_argument("--exact", action="store_true",
                    help="require owned == pasted (the authoritative import_collection.py "
                         "route); default is owned >= pasted, since every other route "
                         "treats a line as a lower bound")
    ap.add_argument("--include-basics", action="store_true",
                    help="also check basic lands (they are normally absent by design)")
    ap.add_argument("--csv", default=DEFAULT_CSV, help="library CSV to check against")
    args = ap.parse_args()

    try:
        text = sys.stdin.read() if args.source == "-" else \
            open(args.source, encoding="utf-8", errors="replace").read()
    except OSError as e:
        eprint(f"Could not read {args.source!r}: {e}")
        return 1

    known_mana = mana_names()
    results, warnings = verify(text, exact=args.exact,
                               include_basics=args.include_basics,
                               lib=library_index(args.csv), mana=known_mana)
    if not results and not warnings:
        eprint("No card lines found in the paste. Expected Arena export lines like "
               "'1 Doctor Doom (MSH) 95'.")
        return 1
    return report(results, warnings, exact=args.exact, mana_missing=known_mana is None)


if __name__ == "__main__":
    sys.exit(main())
