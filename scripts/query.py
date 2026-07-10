#!/usr/bin/env python3
"""Search and filter the card library from the command line.

All text filters are case-insensitive substring matches and are AND-ed together,
so you can narrow a collection quickly during deck-building.

Examples:
    # All blue Merfolk you own
    python3 scripts/query.py --color U --type Merfolk

    # Anything tagged for a counters deck
    python3 scripts/query.py --synergy counters

    # Cards from a specific set that mention "draw a card"
    python3 scripts/query.py --set MSH --text "draw a card"

    # Only cards you actually own at least one copy of, as a count
    python3 scripts/query.py --min-owned 1 --count

Output is a readable table by default; use --csv to emit valid CSV (handy for
piping back into other tools).
"""

import argparse
import csv
import sys

from lib import HEADER, DEFAULT_CSV, load_rows, eprint


def matches(row, args):
    def has(col, needle):
        return needle is None or needle.lower() in (row.get(col) or "").lower()

    if not has("Card Name", args.name):
        return False
    if not has("Type", args.type):
        return False
    if not has("Card Text", args.text):
        return False
    if not has("Color(s)", args.color):
        return False
    if not has("Synergies", args.synergy):
        return False
    if not has("Set Code", args.set):
        return False

    if args.min_owned is not None:
        qty = (row.get("Quantity Owned") or "").strip()
        owned = int(qty) if qty.isdigit() else 0
        if owned < args.min_owned:
            return False
    return True


def print_table(rows):
    """Compact table: name, type, colors, set/collector, quantity."""
    cols = ["Card Name", "Type", "Color(s)", "Set Code", "Collector #", "Quantity Owned"]
    widths = {c: len(c) for c in cols}
    for r in rows:
        for c in cols:
            widths[c] = max(widths[c], len(str(r.get(c, "") or "")))
    # Cap the very wide columns so the table stays terminal-friendly.
    widths["Type"] = min(widths["Type"], 34)

    def fmt(vals):
        return "  ".join(str(v)[: widths[c]].ljust(widths[c]) for c, v in zip(cols, vals))

    print(fmt(cols))
    print(fmt(["-" * widths[c] for c in cols]))
    for r in rows:
        print(fmt([r.get(c, "") or "" for c in cols]))


def main():
    ap = argparse.ArgumentParser(description="Search the MTG Arena card library.")
    ap.add_argument("path", nargs="?", default=DEFAULT_CSV, help="CSV path")
    ap.add_argument("--name", help="substring match on Card Name")
    ap.add_argument("--type", help="substring match on Type line")
    ap.add_argument("--text", help="substring match on Card Text")
    ap.add_argument("--color", help="substring match on Color(s) (e.g. U, B/G)")
    ap.add_argument("--synergy", help="substring match on Synergies tags")
    ap.add_argument("--set", help="substring match on Set Code")
    ap.add_argument("--min-owned", type=int, metavar="N",
                    help="only cards with Quantity Owned >= N (blank counts as 0)")
    ap.add_argument("--csv", action="store_true", help="emit CSV instead of a table")
    ap.add_argument("--count", action="store_true", help="print only the number of matches")
    args = ap.parse_args()

    try:
        _, rows = load_rows(args.path)
    except FileNotFoundError:
        eprint(f"ERROR: file not found: {args.path}")
        return 1

    hits = [r for r in rows if matches(r, args)]

    if args.count:
        print(len(hits))
        return 0

    if not hits:
        eprint("No cards matched.")
        return 0

    if args.csv:
        writer = csv.DictWriter(sys.stdout, fieldnames=HEADER)
        writer.writeheader()
        for r in hits:
            writer.writerow({c: r.get(c, "") or "" for c in HEADER})
    else:
        print_table(hits)
        print(f"\n{len(hits)} card(s) matched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
