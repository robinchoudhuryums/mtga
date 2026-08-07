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
import os
import sys
import textwrap

from lib import csv_schema_error, HEADER, DEFAULT_CSV, REPO_ROOT, load_rows, eprint, color_matches


def keywords_map():
    """name_lower -> [keywords] from card-mana.csv (Scryfall's per-card list), so a
    --full read can surface named mechanics (Warp, Increment, …) explicitly instead
    of letting them read as ordinary words. Empty if card-mana.csv isn't built."""
    path = os.path.join(REPO_ROOT, "card-mana.csv")
    out = {}
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                n = (r.get("Card Name") or "").strip().lower()
                kw = [k for k in (r.get("Keywords") or "").split(";") if k.strip()]
                if n and kw:
                    out[n] = kw
    return out


def print_full(rows, kwmap):
    """Full oracle text + keyword line per card — the phased-ingestion read for
    scanning owned cards as possible deck additions (grade from text, not a label)."""
    for r in rows:
        name = (r.get("Card Name") or "").strip()
        colors = (r.get("Color(s)") or "").strip()
        print(f"\n• {name}   [{(r.get('Type') or '').strip() or '?'}]"
              + (f"  ·  {colors}" if colors else ""))
        kw = kwmap.get(name.lower())
        if kw:
            print(f"    ⌘ keywords: {', '.join(k.title() for k in kw)}")
        text = (r.get("Card Text") or "").strip()
        for para in (text or "(no oracle text on file)").split("\n"):
            for line in (textwrap.wrap(para, width=90) or [""]):
                print(f"    {line}")


def matches(row, args):
    def has(col, needle):
        return needle is None or needle.lower() in (row.get(col) or "").lower()

    if not has("Card Name", args.name):
        return False
    if not has("Type", args.type):
        return False
    if not has("Card Text", args.text):
        return False
    # Identity is SET-matched via lib.color_matches, never substring — "r" is in
    # "colorless", so the substring test returned every Colorless card (BS-10).
    if not color_matches(row.get("Color(s)"), args.color):
        return False
    if not has("Synergies", args.synergy):
        return False
    if not has("Set Code", args.set):
        return False

    if args.min_owned is not None:
        # SUMMED across printings (BS2-36): owned copies are fungible in Arena, so the
        # per-row read dropped every card whose copies are split across sets — at
        # `--min-owned 3` it dropped Rugged Highlands (1+2 across two printings), the
        # exact card the sibling fix in card.py cites. The totals index is built once
        # in main() and carried on args.
        name = (row.get("Card Name") or "").strip().lower()
        if args._owned_totals.get(name, 0) < args.min_owned:
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
    ap.add_argument("--full", action="store_true",
                    help="print each hit's full oracle text + keywords (deep read for adds)")
    args = ap.parse_args()

    try:
        _, hdr_rows = load_rows(args.path)
        rows = hdr_rows
    except FileNotFoundError:
        eprint(f"ERROR: file not found: {args.path}")
        return 1
    # `--csv` writes lib.HEADER, so pointing this at a DERIVED file and redirecting
    # produces a file that looks like a pool and isn't — Rarity/Legalities/Released
    # dropped, a blank Quantity Owned invented. The F-02 accident's read-side shape;
    # the writers refuse it, the reader had no equivalent (broad-scan Batch G).
    if args.csv:
        problem = csv_schema_error(args.path)
        if problem:
            eprint(f"ERROR: --csv emits the card-library columns, so it cannot faithfully "
                   f"re-emit this file.\n       {problem}")
            return 1

    # Per-name owned totals for --min-owned (fungible across printings, BS2-36).
    args._owned_totals = {}
    for r in rows:
        q = (r.get("Quantity Owned") or "").strip()
        if q.isdigit():
            nm = (r.get("Card Name") or "").strip().lower()
            args._owned_totals[nm] = args._owned_totals.get(nm, 0) + int(q)

    hits = [r for r in rows if matches(r, args)]

    if args.count:
        # DISTINCT CARDS, not rows (BS2-36): the module's own usage line advertises
        # `--min-owned 1 --count` as "how many distinct cards you own", and a row
        # count over-reads any card printed in two sets (2085 rows vs 2081 cards).
        print(len({(r.get("Card Name") or "").strip().lower() for r in hits}))
        return 0

    if not hits:
        eprint("No cards matched.")
        return 0

    if args.full:
        print_full(hits, keywords_map())
        print(f"\n{len(hits)} card(s) matched.")
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
