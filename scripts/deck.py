#!/usr/bin/env python3
"""Check a deck list against your collection.

A deck file is plain text, one card per line:

    # Lines starting with '#' are comments (deck name, format, notes).
    # Blank lines are ignored.
    4 Llanowar Elves
    2 Cheerful Osteomancer
    1 Kumena, Tyrant of Orazca (XLN)   # optional (SETCODE) pins a printing

This reports, for each card, how many you own versus how many the deck needs,
and flags any shortfalls or cards missing from the library entirely — so you can
see collection gaps before you queue up a match.

Usage:
    python3 scripts/deck.py decks/my-deck.txt
    python3 scripts/deck.py decks/my-deck.txt --library card-library.csv
"""

import argparse
import re
import sys

from lib import DEFAULT_CSV, load_rows, eprint

# "4 Card Name" or "4x Card Name", with an optional trailing "(SET)".
LINE_RE = re.compile(r"^\s*(\d+)\s*[xX]?\s+(.+?)\s*(?:\(([^)]+)\))?\s*$")


def parse_deck(path):
    """Return a list of (quantity, name, set_code_or_None) tuples."""
    entries = []
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.split("#", 1)[0].strip()  # strip inline + full-line comments
            if not line:
                continue
            m = LINE_RE.match(line)
            if not m:
                eprint(f"WARN:  {path}:{lineno}: could not parse {raw.strip()!r}")
                continue
            qty, name, set_code = m.group(1), m.group(2).strip(), m.group(3)
            entries.append((int(qty), name, set_code.strip() if set_code else None))
    return entries


def owned_count(rows, name, set_code):
    """Total copies owned of a card. If set_code is given, only that printing."""
    total = 0
    found = False
    for r in rows:
        if (r.get("Card Name") or "").strip().lower() != name.lower():
            continue
        if set_code and (r.get("Set Code") or "").strip().lower() != set_code.lower():
            continue
        found = True
        qty = (r.get("Quantity Owned") or "").strip()
        total += int(qty) if qty.isdigit() else 0
    return total, found


def main():
    ap = argparse.ArgumentParser(description="Validate a deck against your collection.")
    ap.add_argument("deck", help="path to a deck .txt file")
    ap.add_argument("--library", default=DEFAULT_CSV, help="card-library.csv path")
    args = ap.parse_args()

    try:
        _, rows = load_rows(args.library)
    except FileNotFoundError:
        eprint(f"ERROR: library not found: {args.library}")
        return 1

    entries = parse_deck(args.deck)
    if not entries:
        eprint("No cards found in deck file.")
        return 1

    total_cards = sum(q for q, _, _ in entries)
    shortfalls = []
    missing = []

    print(f"{'Have':>4} / {'Need':<4}  Card")
    print("-" * 40)
    for qty, name, set_code in entries:
        have, found = owned_count(rows, name, set_code)
        label = name + (f" ({set_code})" if set_code else "")
        flag = ""
        if not found:
            flag = "  <- NOT IN LIBRARY"
            missing.append(label)
        elif have < qty:
            flag = f"  <- short {qty - have}"
            shortfalls.append((label, qty, have))
        print(f"{have:>4} / {qty:<4}  {label}{flag}")

    print("-" * 40)
    print(f"{len(entries)} unique card(s), {total_cards} total.")
    if missing:
        print(f"{len(missing)} not in library: {', '.join(missing)}")
    if shortfalls:
        print(f"{len(shortfalls)} card(s) short of the deck's requirement.")
    if not missing and not shortfalls:
        print("You own every card in this deck. Ready to build.")
    # Non-zero exit if the deck isn't fully buildable, useful for scripting.
    return 1 if (missing or shortfalls) else 0


if __name__ == "__main__":
    sys.exit(main())
