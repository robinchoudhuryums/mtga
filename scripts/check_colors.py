#!/usr/bin/env python3
"""Anchor sanity checks for color-identity parsing (lib.card_colors + its call sites).

Guards the exact regression fixed in broad-scan F1/F2: the naive idiom
``{ch for ch in Color(s).upper() if ch in "WUBRG"}`` reads the literal string
"Colorless" as {'R'} — because the WORD contains an R — so every colorless card
(mana rocks, artifacts, Eldrazi) was mis-routed by suggest / suggest-homes /
fingerprints (excluded from non-red decks, offered to red ones). A sibling variant
``set(Color(s).replace(" ",""))`` kept the "/" so gold cards failed the subset test.

These checks are distribution-independent (they assert behavior, not card names), so
they keep working as the collection changes. check_all.py folds them in as a HARD
gate — a re-introduction of the bug fails the build, the same way check_rankings
guards the Doctor-Doom scoring regression.

Run standalone (`python3 scripts/check_colors.py`) or via check_all.py.
Returns a list of human-readable error strings; empty == healthy.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import REPO_ROOT, card_colors  # noqa: E402

LIB_CSV = os.path.join(REPO_ROOT, "card-library.csv")
POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")


def check():
    """Return a list of error strings (empty == healthy). Never raises."""
    errs = []

    # (1) The primitive itself: the two traps F1/F2 hit.
    if card_colors("Colorless"):
        errs.append("card_colors('Colorless') is non-empty — a colorless card would "
                    "read as colored (the 'COLORLESS' contains 'R' trap, audit F1). "
                    f"Got {sorted(card_colors('Colorless'))}, expected empty.")
    if card_colors("B/G") != {"B", "G"}:
        errs.append("card_colors('B/G') != {'B','G'} — a slash-joined gold card is "
                    f"mis-parsed (audit F2). Got {sorted(card_colors('B/G'))}.")
    if card_colors("W/U/B/R/G") != set("WUBRG"):
        errs.append("card_colors('W/U/B/R/G') should be all five colors; got "
                    f"{sorted(card_colors('W/U/B/R/G'))}.")

    # (2) Property: a colorless identity is castable everywhere (subset of any deck's
    #     colors) — the thing the bug broke.
    if not card_colors("Colorless").issubset(set()):  # empty ⊆ empty
        errs.append("a colorless identity is not the empty set — it must be castable "
                    "in every deck (⊆ any WUBRG set).")

    # (3) Call-site guard: pick a real colorless nonland card and assert deck.py's
    #     fingerprint builder (load_card_meta, the main F1 site) gives it NO colors.
    try:
        import deck
        meta = deck.load_card_meta()
        anchor = None
        for path in (LIB_CSV, POOL_CSV):
            if not os.path.exists(path):
                continue
            with open(path, newline="", encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    if (r.get("Color(s)") or "").strip().lower() == "colorless" \
                            and "Land" not in (r.get("Type") or ""):
                        anchor = (r.get("Card Name") or "").strip().lower()
                        break
            if anchor:
                break
        if anchor and anchor in meta and meta[anchor]["colors"]:
            errs.append(f"deck.load_card_meta parsed colorless card {anchor!r} as "
                        f"{sorted(meta[anchor]['colors'])} — expected no colors (audit F1 "
                        "call site regressed).")
    except Exception as e:  # pragma: no cover - import/deck guard
        errs.append(f"color call-site check skipped ({type(e).__name__}: {e})")

    return errs


def main():
    errs = check()
    if errs:
        print("Color parsing sanity: FAIL")
        for e in errs:
            print(f"  ✗ {e}")
        return 1
    print("Color parsing sanity: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
