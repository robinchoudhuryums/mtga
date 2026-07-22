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

    # (5) power co-signal (#6): bounded to a modest additive contribution, and a mythic
    #     bomb outweighs a common vanilla — but the weighted power (≤10) stays small next
    #     to a strongly-on-theme card's theme_w, so it can't override theme fit.
    ps = deck._power_seed
    bomb = {"Rarity": "Mythic", "Type": "Legendary Planeswalker",
            "Card Text": "Destroy target permanent. Draw two cards."}
    vanilla = {"Rarity": "Common", "Type": "Creature — Bear", "Card Text": ""}
    pb, pv = ps(bomb), ps(vanilla)
    if not (0.0 <= pv <= 10.0 and 0.0 <= pb <= 10.0):
        errs.append(f"_power_seed out of [0,10]: bomb {pb}, vanilla {pv}.")
    if not pb > pv:
        errs.append(f"_power_seed: a mythic bomb ({pb}) should outrank a common vanilla ({pv}).")
    if deck._SUGGEST_POWER_W * 10 > 15:
        errs.append(f"_SUGGEST_POWER_W too large ({deck._SUGGEST_POWER_W}): max power "
                    "contribution should stay a modest co-signal (≤ ~role-credit scale), "
                    "not override theme fit.")

    # (6) color-fixer overlay (suggest-homes): the fixer boost must be 0 below 3
    #     colors (mono/two-color decks don't want rainbow fixing), non-decreasing in
    #     color count, and CAPPED — so it re-ranks fixer-eligible decks without ever
    #     dwarfing a genuine theme match. And `_is_color_fixer` must require BOTH a
    #     fixing tag AND rainbow text, so a mono-color ramp spell never qualifies.
    fb = deck._fixer_boost
    boosts = [fb(n) for n in range(1, 7)]
    if not (fb(0) == 0 and fb(1) == 0 and fb(2) == 0):
        errs.append(f"_fixer_boost must be 0 below 3 colors; got {boosts[:2]} for 1–2 colors "
                    "— a mono/two-color deck must not get a rainbow-fixer bump.")
    if not all(a <= b for a, b in zip(boosts, boosts[1:])):
        errs.append(f"_fixer_boost not non-decreasing in color count: {boosts} "
                    "— a fixer must be worth at least as much in a wider deck.")
    if fb(5) != fb(6) or fb(6) != fb(20):
        errs.append(f"_fixer_boost is not CAPPED (fb(5)={fb(5)}, fb(6)={fb(6)}, fb(20)={fb(20)}) "
                    "— an uncapped bump could dwarf theme fit.")
    isf = deck._is_color_fixer
    if isf({"ramp"}, "Add {G}{G}."):
        errs.append("_is_color_fixer flagged a mono-color ramp spell (tag but no rainbow text) "
                    "— it must require explicit any-color/every-basic-land-type text.")
    if isf({"tokens"}, "create a land token that is every basic land type"):
        errs.append("_is_color_fixer flagged a card with rainbow text but NO fixing tag "
                    "— it must require both a ramp/mana tag and the text cue.")
    if not isf({"ramp", "mana"}, "create a tapped land token that is every basic land type"):
        errs.append("_is_color_fixer failed to flag a canonical rainbow fixer "
                    "(ramp/mana tag + every-basic-land-type) — the Overlord anchor.")

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
