#!/usr/bin/env python3
"""Import an MTG Arena deck/collection export into card-library.csv.

Arena's "Export" produces lines like:

    Deck
    1 Agent Maria Hill (MSH) 2
    4 Llanowar Elves (DOM) 168
    1 Nick Fury, Agent of S.H.I.E.L.D. (MSH) 25

i.e.  <quantity> <Card Name> (<SET>) <collector#>. This parses that format and
merges the cards into the library, keyed by Card Name + Set Code + Collector #
(one row per unique printing). It fills Card Name, Set Code, Collector # and
Quantity Owned; Type / Card Text / Color(s) are left blank for `enrich.py` to
backfill from Scryfall, and Synergies is left for you.

Quantity semantics: MTG Arena decks all draw from ONE shared collection, so a
card appearing in several decks does NOT mean you own several copies — the line
count is how many that deck uses, which is a *lower bound* on what you own.
Re-importing therefore takes the MAX quantity seen for a printing (never sums),
so pasting overlapping decks won't inflate your counts. Use --sum to add instead
(only correct if each export is a disjoint slice of the collection).

Usage:
    python3 scripts/import_arena.py batch.txt          # merge a file
    pbpaste | python3 scripts/import_arena.py -         # merge from stdin
    python3 scripts/import_arena.py batch.txt --dry-run # preview only
    python3 scripts/import_arena.py batch.txt --sum     # add quantities

After importing, regenerate the derived data — a newly imported card has no
card-mana.csv row and INV-02 requires one:

    make refresh
    python3 scripts/verify_ingest.py batch.txt   # confirm the batch landed

This used to spell the chain out here, and had it in the WRONG ORDER (build_mana
ahead of build_pool, which build_mana reads) while asserting "IN THIS ORDER". The
Makefile is the one executable definition; see its `refresh` target for why the
order is what it is.
"""

import argparse
import re
import sys

from lib import BASICS as lib_BASICS, DEFAULT_CSV, load_rows, write_rows, eprint

# <qty> <name> optionally followed by (SET) and a collector number.
LINE_RE = re.compile(
    r"^\s*(\d+)\s*[xX]?\s+(.+?)\s*(?:\(([^)]+)\)\s*([^\s]+)?)?\s*$"
)
# Section headers Arena emits that aren't cards.
SECTIONS = {"deck", "sideboard", "commander", "companion", "maybeboard", "about"}
# Basic lands are unlimited in Arena and don't belong in the owned collection;
# skip them when reconciling the library from a deck list (--skip-basics).
BASICS = lib_BASICS          # one definition, in lib.py


def parse(text, skip_basics=False):
    """Return (entries, warnings). entries: list of (qty, name, set, collector),
    ONE entry per printing, aggregated section-aware:

    Within one deck block, Deck and Sideboard copies of a card draw from the
    collection SIMULTANEOUSLY — a Bo3 export with 2 Duress maindeck and 2 more in
    the sideboard proves ownership of 4, and the old flat list handed both rows to
    merge()'s max(), recording 2 (broad-scan batch 5). So: SUM across a block's
    sections, MAX for a repeat within one section (one holding stated twice), MAX
    across separate `Deck` blocks (decks share the collection, so the lower bound
    over many decks is the best single block). A Companion line duplicates its
    Sideboard row in Arena exports, so it is folded into that section."""
    entries, warnings = [], []
    idx, disp = {}, {}
    block, block_secs = {}, {}

    def _fold_block():
        for k, q in block.items():
            i = idx.get(k)
            if i is None:
                idx[k] = len(entries)
                entries.append((q, *disp[k]))
            elif q > entries[i][0]:
                entries[i] = (q, *entries[i][1:])
        block.clear()
        block_secs.clear()

    section = "deck"
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.lower() in SECTIONS:
            if line.lower() == "deck":
                _fold_block()          # a new deck block starts
            section = line.lower()
            continue
        if line.startswith("#") or line.startswith("//"):
            continue
        m = LINE_RE.match(line)
        if not m:
            warnings.append(f"line {lineno}: could not parse {raw.strip()!r}")
            continue
        qty = int(m.group(1))
        name = m.group(2).strip()
        set_code = (m.group(3) or "").strip()
        collector = (m.group(4) or "").strip()
        if skip_basics and name.lower() in BASICS:
            continue
        k = key(name, set_code, collector)
        disp.setdefault(k, (name, set_code, collector))
        sec = "sideboard" if section == "companion" else section
        if sec in block_secs.get(k, ()):
            block[k] = max(block[k], qty)              # same-section repeat
        else:
            block_secs.setdefault(k, set()).add(sec)
            block[k] = block.get(k, 0) + qty           # a NEW section: sums
    _fold_block()
    return entries, warnings


def key(name, set_code, collector):
    """Printing key, FRONT-face named. The library stores most DFCs under the front
    name but a handful under the full "A // B" (the DSK Rooms), and a paste can name
    either spelling. An exact-name key missed the full-name rows, so re-importing an
    owned DFC APPENDED a second row for the same physical printing — the owned count
    then SPLIT across two spellings where `lib.owned_qty` resolves only one, and the
    collection silently under-reported (broad-scan BS2-02). Two distinct cards can
    never share (front, set, collector): a collector number is unique within a set."""
    return (name.split(" // ")[0].strip().lower(), set_code.lower(), collector.lower())


def merge(rows, entries, sum_mode):
    """Merge parsed entries into rows (list of dicts). Returns (added, updated, notes).

    `notes` are per-line advisories the caller should surface (currently only the
    set-less-line handling below)."""
    index = {}
    for r in rows:
        index[key(r.get("Card Name", ""), r.get("Set Code", ""),
                  r.get("Collector #", ""))] = r
    # Summed owned per FRONT name, for the set-less path: copies are fungible across
    # printings, so a name-only claim compares against the TOTAL, never one row.
    by_front = {}
    for r in rows:
        f = key(r.get("Card Name", ""), "", "")[0]
        by_front.setdefault(f, []).append(r)

    added = updated = 0
    notes = []
    for qty, name, set_code, collector in entries:
        # A line with no COLLECTOR NUMBER (`4 Llanowar Elves`, a website list; or
        # `4 Llanowar Elves (DOM)`, a set-stamped list) is a NAME-level claim, not a
        # printing. It keys on ("name", set, "") which matches no real row — every real
        # row carries a collector number — so merge APPENDED a phantom printing, and
        # since every consumer SUMS across printings a real 4 then read as 8: the one
        # OVER-count path in a subsystem whose documented failure mode is uniformly
        # undercount, later legitimized by enrich backfilling the phantom row into an
        # exact-duplicate printing that breaks INV-01 long after the import that caused
        # it (broad-scan BS2-24, extended to set-stamped lines by BS4-04;
        # reconcile_crafts already refuses such lines). For a card the library holds,
        # compare against the summed total and top up the first row only if the line
        # exceeds it (lower-bound semantics); for an unknown card, keep the append but
        # SAY so, since nothing else can represent it.
        #
        # A row whose Collector # is legitimately blank (enrich leaves it blank rather
        # than guessing an unconfirmed printing — G-11) is part of `fam` like any other
        # printing, so it is topped up through this path rather than duplicated.
        if not collector:
            shape = "set-less line" if not set_code else f"({set_code}) line with no collector #"
            fam = by_front.get(key(name, "", "")[0])
            if fam:
                total = sum(int(q) for r in fam
                            if (q := (r.get("Quantity Owned") or "").strip()).isdigit())
                if sum_mode or qty > total:
                    first = fam[0]
                    cur = (first.get("Quantity Owned") or "").strip()
                    cur_n = int(cur) if cur.isdigit() else 0
                    bump = qty if sum_mode else qty - total
                    first["Quantity Owned"] = str(cur_n + bump)
                    updated += 1
                    notes.append(f"{name}: {shape} ({qty}) exceeded the summed "
                                 f"owned total ({total}) — topped up the "
                                 f"({first.get('Set Code') or '?'}) printing"
                                 if not sum_mode else
                                 f"{name}: {shape} summed onto the "
                                 f"({first.get('Set Code') or '?'}) printing")
                else:
                    notes.append(f"{name}: {shape} ({qty}) already covered by the "
                                 f"summed owned total ({total}) — no change")
                continue
            notes.append(f"{name}: {shape} for a card not in the library — added with a "
                         + ("BLANK set code" if not set_code else "BLANK collector #")
                         + "; prefer a printed Arena export or reconcile_crafts.py so "
                           "the printing is real")
        k = key(name, set_code, collector)
        existing = index.get(k)
        if existing is None:
            row = {
                "Card Name": name,
                "Type": "",
                "Card Text": "",
                "Color(s)": "",
                "Synergies": "",
                "Set Code": set_code,
                "Collector #": collector,
                "Quantity Owned": str(qty),
            }
            rows.append(row)
            index[k] = row
            added += 1
        else:
            cur = (existing.get("Quantity Owned") or "").strip()
            cur_n = int(cur) if cur.isdigit() else 0
            new_n = cur_n + qty if sum_mode else max(cur_n, qty)
            if str(new_n) != cur:
                existing["Quantity Owned"] = str(new_n)
                updated += 1
    return added, updated, notes


def main():
    ap = argparse.ArgumentParser(description="Import an MTG Arena export into the library.")
    ap.add_argument("source", help="path to an export file, or '-' for stdin")
    ap.add_argument("--library", default=DEFAULT_CSV, help="card-library.csv path")
    ap.add_argument("--sum", action="store_true",
                    help="add quantities on re-import instead of taking the max")
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    ap.add_argument("--skip-basics", action="store_true",
                    help="ignore basic lands (use when reconciling from a deck list)")
    args = ap.parse_args()

    # A bad path was a raw traceback here, while import_collection / verify_ingest /
    # parse_matches all print a clean "Could not read …" (broad-scan Batch G).
    try:
        text = (sys.stdin.read() if args.source == "-"
                else open(args.source, encoding="utf-8").read())
    except OSError as e:
        eprint(f"Could not read {args.source!r}: {e}")
        return 1
    entries, warnings = parse(text, skip_basics=args.skip_basics)
    for w in warnings:
        eprint(f"WARN:  {w}")
    if not entries:
        eprint("No card lines found.")
        return 1

    try:
        _, rows = load_rows(args.library)
    except FileNotFoundError:
        rows = []

    added, updated, notes = merge(rows, entries, args.sum)
    for n in notes:
        eprint(f"NOTE:  {n}")

    if args.dry_run:
        print(f"[dry-run] {len(entries)} card line(s): would add {added} new, "
              f"update {updated} existing. Nothing written.")
        return 0

    if not (added or updated):
        # Don't rewrite (and .bak) a 614KB file that isn't changing: build_mana.py
        # avoids exactly this for exactly this reason, and import_collection gates on
        # `changed`. A re-imported paste used to litter a backup per run (Batch G).
        print(f"Checked {len(entries)} card line(s): nothing to change; "
              f"{args.library} left untouched.")
        return 0

    write_rows(rows, args.library)
    print(f"Imported {len(entries)} card line(s): {added} added, {updated} updated. "
          f"Library now has {len(rows)} row(s). Wrote {args.library}.")
    # A NEW card has no card-mana.csv row, so INV-02 is broken until build_mana.py
    # runs. This line used to say "enrich.py then validate.py", which leaves the
    # integrity gate red and gives no hint why (broad-scan F-06) — and CLAUDE.md's
    # Regression Scenario 1 repeated the same short recipe. Name the step that
    # actually restores the invariant, and only when this run introduced a card.
    # Point at the Makefile rather than restating the chain. This message USED to spell
    # it out, and had build_mana.py --pool ahead of build_pool.py --all — the wrong
    # order, in executable code, telling people to make the exact mistake the Makefile
    # comment documents. A rebuild chain written in a print statement is one more copy to
    # keep in sync, and this one had already fallen out.
    if added:
        print("\nNext — new cards need their derived data rebuilt (check_all will fail "
              "INV-02 until it runs):\n  make refresh\n"
              "Then confirm the batch actually landed:\n"
              f"  python3 scripts/verify_ingest.py <this file>")
    else:
        print("\nNext (no new cards, so nothing to rebuild):\n"
              "  python3 scripts/check_all.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
