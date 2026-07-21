#!/usr/bin/env python3
"""Sanity anchors for the gap-aware suggest/cuts scoring (deck.py).

Improvements #1 (diminishing-returns role credit) and #2 (curve-gap factor) add
NEEDS-awareness to `suggest`/`cuts` — but a bad weighting could silently reorder a
tuned deck's recommendations. These checks lock in the properties that keep the new
terms SAFE modifiers rather than dominant ones, the same way check_rankings guards the
wishlist model and check_colors guards color parsing. Distribution-independent, so they
keep holding as the collection changes.

  1. Backward-compat: `_role_credit(roles)` with no saturation == the original flat
     credit (base 3 + 6 per impact role).
  2. Diminishing returns: for an impact role, credit STRICTLY decreases as the deck
     already runs more of it; a scarce role (0 owned) scores strictly above a
     saturated one (many owned), and the impact bonus never goes negative or exceeds
     the un-saturated max.
  3. Curve factor is BOUNDED to [0.85, 1.15] for every input — the guarantee that it
     can only re-rank near-ties, never override a clear theme-fit winner.
  4. Curve factor is archetype-SAFE: an over-full bucket is penalized (<1) at any MV,
     a thin CHEAP bucket (MV ≤ 3) is boosted (>1), and a thin EXPENSIVE bucket is left
     alone (==1) — so it never pushes an off-plan top-end card on an aggro deck.

Run standalone (`python3 scripts/check_suggest.py`) or via check_all.py. Returns a
list of human-readable error strings; empty == healthy.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check():
    """Return a list of error strings (empty == healthy). Never raises."""
    try:
        import deck
    except Exception as e:  # pragma: no cover - import guard
        return [f"suggest scoring: could not import deck.py ({e})"]

    errs = []
    rc = deck._role_credit
    R = next(iter(deck.IMPACT_ROLES))  # some impact role, e.g. "Removal (spot)"

    # (1) backward-compat: no saturation == flat original.
    if rc({R}) != 3 + 6:
        errs.append(f"_role_credit({{{R}}}) flat != 9 (base 3 + impact 6); got {rc({R})} "
                    "— the un-saturated credit changed, which shifts every existing rank.")
    if rc(set()) != 0:
        errs.append(f"_role_credit(∅) != 0; got {rc(set())}.")

    # (2) diminishing returns: strictly decreasing, bounded, non-negative.
    seq = [rc({R}, {R: k}) for k in (0, 1, 2, 4, 8)]
    if not all(a > b for a, b in zip(seq, seq[1:])):
        errs.append(f"_role_credit not strictly decreasing in saturation for {R}: {seq} "
                    "— the Nth copy of a role must be worth less than the 1st (#1).")
    if not (seq[0] <= rc({R}) and min(seq) >= 3):  # base (3) always present; never below
        errs.append(f"_role_credit saturation out of bounds for {R}: {seq} "
                    f"(un-saturated flat {rc({R})}, base 3).")

    # (3) curve factor bounded to [0.85, 1.15] for a wide sweep of inputs.
    cf = deck._curve_gap_factor
    curves = [{}, {1: 4, 2: 4, 3: 2}, {2: 12}, {5: 1}, {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1}]
    for cv in curves:
        for mv in (None, 0, 1, 2, 3, 4, 5, 6, 7, 12):
            f = cf(mv, cv)
            if not (0.85 <= f <= 1.15):
                errs.append(f"_curve_gap_factor({mv}, {cv}) = {f} escapes [0.85, 1.15] "
                            "— the bound that keeps curve a tie-breaker, not a lever.")

    # (4) archetype safety: penalize over-full at any MV; boost thin CHEAP only;
    #     leave thin EXPENSIVE alone.
    lopsided = {1: 8, 2: 8, 6: 0, 3: 0}          # cheap-heavy deck, thin at 3 and 6
    if not cf(2, lopsided) < 1.0:
        errs.append("_curve_gap_factor should PENALIZE an over-full cheap bucket "
                    f"(MV2 in {lopsided}); got {cf(2, lopsided)}.")
    if not cf(3, lopsided) > 1.0:
        errs.append("_curve_gap_factor should BOOST a thin cheap bucket "
                    f"(MV3 in {lopsided}); got {cf(3, lopsided)}.")
    if cf(6, lopsided) != 1.0:
        errs.append("_curve_gap_factor must NOT boost a thin EXPENSIVE bucket "
                    f"(MV6 in {lopsided}) — archetype-unsafe; got {cf(6, lopsided)}.")
    if cf(0, lopsided) != 1.0:
        errs.append("_curve_gap_factor must NOT boost MV 0 (lands / free spells aren't a "
                    f"spell-curve slot); got {cf(0, lopsided)}.")

    return errs


def main():
    errs = check()
    if errs:
        print("Suggest scoring sanity: FAIL")
        for e in errs:
            print(f"  ✗ {e}")
        return 1
    print("Suggest scoring sanity: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
