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

    # Ranking-model sanity — guards the Doctor-Doom-class scoring regression
    # (a real tribe silently read as "generic" after a threshold drifted).
    try:
        from check_rankings import check as check_rankings
        hard += check_rankings()
    except Exception as e:
        hard.append(f"ranking model sanity check errored: {e}")

    # Color-identity parsing sanity — guards the F1/F2 regression (a colorless card
    # read as red; a slash-gold failing the subset test) that mis-routed suggest.
    try:
        from check_colors import check as check_colors
        hard += check_colors()
    except Exception as e:
        hard.append(f"color parsing sanity check errored: {e}")

    # Suggest/cuts gap-aware scoring sanity — keeps the diminishing-returns role credit
    # and the curve factor as BOUNDED modifiers (they can't silently reorder a tuned
    # deck's recommendations by overriding theme fit).
    try:
        from check_suggest import check as check_suggest
        hard += check_suggest()
    except Exception as e:
        hard.append(f"suggest scoring sanity check errored: {e}")

    # Engine-role classifier sanity — locks the enabler/payoff detection (#3) on
    # canonical cards so a regex edit can't silently break the imbalance flag.
    try:
        from check_engines import check as check_engines
        hard += check_engines()
    except Exception as e:
        hard.append(f"engine classifier sanity check errored: {e}")

    # Archetype-aware tier floor sanity (#4) — non-aggro decks grade exactly as before,
    # and the aggro clock only ever raises a band (never lowers or mis-grades one).
    try:
        from check_tier import check as check_tier
        hard += check_tier()
    except Exception as e:
        hard.append(f"tier floor sanity check errored: {e}")

    # Soft: wishlist target drift — a target deck that can no longer cast its card
    # after a retune (e.g. deck 14 Mardu->Rakdos orphaned Neriv). Informational
    # only; never fails the build.
    soft = []
    try:
        import wishlist as wl
        for _sev, name, msg in wl._audit_target_issues(color_only=True):
            soft.append(f"wishlist target drift: {name} — {msg}")
    except Exception as e:
        soft.append(f"wishlist target audit skipped ({e})")

    # Soft: NEW unindexed card mechanics (a new set's keyword not yet in the synergy
    # map). Baselined, so it stays quiet until something genuinely new appears.
    try:
        import check_keywords as ck
        for kw, ex, _sig in ck.check():
            soft.append(f"unindexed mechanic '{kw}' (e.g. {ex}) — add to tag_synergies "
                        "KEYWORD_THEMES/FLAVOR_KEYWORDS or run check_keywords.py --update-baseline")
        # Denylist overreach — a flavor keyword that may actually be a real mechanic.
        for kw, _n, note in ck.flavor_overreach():
            soft.append(f"FLAVOR_KEYWORDS overreach: '{kw}' — {note}")
    except Exception as e:
        soft.append(f"keyword radar skipped ({e})")

    # Soft: tier robustness — a deck whose claimed #: tier: sits ≥2 bands above the
    # tier its measurable quality vector supports (inflated or stale). Never gating —
    # tier is a human judgment, this only flags an indefensible letter to re-grade.
    try:
        for did, claimed, implied, msg in deckmod.tier_consistency_issues():
            soft.append(f"tier mismatch: deck {did} — {msg} "
                        "(re-grade from the CLAUDE.md rubric, or justify the bombs/meta in the rationale)")
    except Exception as e:
        soft.append(f"tier robustness check skipped ({e})")

    if args.quiet:
        state = "OK" if not hard else f"{len(hard)} ISSUE(S)"
        extra = f", {len(soft)} soft" if soft else ""
        print(f"[card-library] {ncards} cards, {ndecks} decks — integrity: {state}{extra}")
        return 1 if hard else 0

    print(f"\n=== Integrity: {ncards} cards, {ndecks} decks ===")
    for line in deck_info:
        print(line)
    if soft:
        eprint("\nSOFT WARNINGS (not gating):")
        for s in soft:
            eprint(f"  ~ {s}")
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
