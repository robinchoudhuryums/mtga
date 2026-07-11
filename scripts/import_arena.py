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

After importing, run:  python3 scripts/enrich.py   then   python3 scripts/validate.py
"""

import argparse
import re
import sys

from lib import DEFAULT_CSV, load_rows, write_rows, eprint

# <qty> <name> optionally followed by (SET) and a collector number.
LINE_RE = re.compile(
    r"^\s*(\d+)\s*[xX]?\s+(.+?)\s*(?:\(([^)]+)\)\s*([^\s]+)?)?\s*$"
)
# Section headers Arena emits that aren't cards.
SECTIONS = {"deck", "sideboard", "commander", "companion", "maybeboard", "about"}
# Basic lands are unlimited in Arena and don't belong in the owned collection;
# skip them when reconciling the library from a deck list (--skip-basics).
BASICS = {"plains", "island", "swamp", "mountain", "forest", "wastes"}


def parse(text, skip_basics=False):
    """Return (entries, warnings). entries: list of (qty, name, set, collector)."""
    entries, warnings = [], []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.lower() in SECTIONS:
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
        entries.append((qty, name, set_code, collector))
    return entries, warnings


def key(name, set_code, collector):
    return (name.lower(), set_code.lower(), collector.lower())


def merge(rows, entries, sum_mode):
    """Merge parsed entries into rows (list of dicts). Returns (added, updated)."""
    index = {}
    for r in rows:
        index[key(r.get("Card Name", ""), r.get("Set Code", ""),
                  r.get("Collector #", ""))] = r

    added = updated = 0
    for qty, name, set_code, collector in entries:
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
    return added, updated


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

    text = sys.stdin.read() if args.source == "-" else open(args.source, encoding="utf-8").read()
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

    added, updated = merge(rows, entries, args.sum)

    if args.dry_run:
        print(f"[dry-run] {len(entries)} card line(s): would add {added} new, "
              f"update {updated} existing. Nothing written.")
        return 0

    write_rows(rows, args.library)
    print(f"Imported {len(entries)} card line(s): {added} added, {updated} updated. "
          f"Library now has {len(rows)} row(s). Wrote {args.library}.")
    print("Next: python3 scripts/enrich.py   then   python3 scripts/validate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
