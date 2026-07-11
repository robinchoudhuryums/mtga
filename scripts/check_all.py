#!/usr/bin/env python3
"""Project integrity check — the deterministic gate for the card library.

Verifies the invariants that keep the interdependent files consistent (see the
Invariant Library in CLAUDE.md). This is the project's "Test Command": it exits
non-zero on any hard integrity break, so /broad-implement and CI can rely on it.

Checks (hard = fails the run):
  INV-01  card-library.csv passes validate.py (header, columns, quantities,
          no duplicate printings).                                    [hard]
  INV-02  every library Card Name has a row in card-mana.csv.          [hard]
  INV-03  the derived reference files exist (card-mana.csv, card-pool.csv,
          gallery.html).                                               [hard]
  INV-04  every deck file under decks/ parses with no bad lines.       [hard]
  (info)  deck buildability summary vs. the collection — not a hard
          invariant (CLAUDE.md's INV-05 is the Color(s)=identity rule). [info]

Usage:
    python3 scripts/check_all.py          # full check, exit 1 on hard failures
    python3 scripts/check_all.py --quiet  # one-line summary only (for hooks)
"""

import argparse
import csv
import os
import sys

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint
from validate import validate
import deck as deckmod

MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")
POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")
GALLERY = os.path.join(REPO_ROOT, "gallery.html")


def check_mana_coverage():
    """INV-02: every library card name appears in card-mana.csv."""
    if not os.path.exists(MANA_CSV):
        return ["card-mana.csv missing (run build_mana.py)"], 0, 0
    have = set()
    with open(MANA_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            have.add((r.get("Card Name") or "").strip().lower())
    _, rows = load_rows(DEFAULT_CSV)
    names = {(r.get("Card Name") or "").strip().lower() for r in rows if (r.get("Card Name") or "").strip()}
    missing = sorted(n for n in names if n not in have)
    return [f"card-mana.csv missing {len(missing)} card(s): {', '.join(missing[:8])}"
            + ("…" if len(missing) > 8 else "")] if missing else [], len(names), len(missing)


def check_derived_files():
    """INV-03: derived reference files exist."""
    errs = []
    for path, name in [(MANA_CSV, "card-mana.csv"), (POOL_CSV, "card-pool.csv"),
                       (GALLERY, "gallery.html")]:
        if not os.path.exists(path):
            errs.append(f"{name} missing")
    return errs


def check_decks():
    """INV-04 (deck parse) + buildability summary (info, not a hard invariant)."""
    errs, info = [], []
    decks = deckmod.discover_decks()
    _, _, by_name_qty = deckmod.load_collection()
    for d in decks:
        _, cards = deckmod.parse_deck_file(d["path"])
        if not cards:
            errs.append(f"deck {d['id']} ({os.path.relpath(d['path'], REPO_ROOT)}) has no parseable cards")
            continue
        missing = short = 0
        for q, n, s, c in cards:
            have, found = deckmod.owned(by_name_qty, n)
            if not found:
                missing += 1
            elif have < q:
                short += 1
        status = "buildable" if (missing == 0 and short == 0) else \
            f"{missing} missing, {short} short"
        info.append(f"  deck {d['id']:>4}  {d['name'] or d['id']:<28} {status}")
    return errs, info, len(decks)


def main():
    ap = argparse.ArgumentParser(description="Card-library integrity check.")
    ap.add_argument("--quiet", action="store_true", help="one-line summary only")
    args = ap.parse_args()

    hard = []

    # INV-01 — suppress validate's per-row chatter in quiet mode.
    if args.quiet:
        import contextlib
        with open(os.devnull, "w") as null, \
                contextlib.redirect_stdout(null), contextlib.redirect_stderr(null):
            inv01 = validate(DEFAULT_CSV)
    else:
        inv01 = validate(DEFAULT_CSV)  # prints its own errors/warnings
    if inv01 != 0:
        hard.append("card-library.csv failed validate.py")

    # INV-02
    mana_errs, ncards, nmiss = check_mana_coverage()
    hard += mana_errs

    # INV-03
    hard += check_derived_files()

    # INV-04 / INV-05
    deck_errs, deck_info, ndecks = check_decks()
    hard += deck_errs

    if args.quiet:
        state = "OK" if not hard else f"{len(hard)} ISSUE(S)"
        print(f"[card-library] {ncards} cards, {ndecks} decks — integrity: {state}")
        return 1 if hard else 0

    print(f"\n=== Integrity: {ncards} cards, {ndecks} decks ===")
    for line in deck_info:
        print(line)
    if hard:
        eprint("\nHARD FAILURES:")
        for e in hard:
            eprint(f"  ✗ {e}")
        print(f"\n{len(hard)} hard failure(s).")
        return 1
    print("\nAll invariants hold. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
