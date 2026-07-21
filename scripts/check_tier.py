#!/usr/bin/env python3
"""Sanity anchors for the archetype-aware tier floor (deck.py, improvement #4).

`tier_band` now weights an AGGRO deck's floor on its clock (curve + cheap threats +
reach) instead of the interaction suite it doesn't want — so a genuinely fast deck
isn't floored at C for light removal. These checks lock the two safety properties that
keep that change from mis-grading, the same way check_suggest/check_engines guard their
models:

  1. NON-AGGRO decks are graded EXACTLY as before — for any plan other than 'aggro' the
     clock is 0, so tier_band equals the pure interaction+card-advantage floor. (Zero
     blast radius for control/midrange/combo — the vast majority of the roster.)
  2. The clock only ever RAISES a band, never lowers one — an aggro deck's floor is
     always ≥ the floor the same vector would get as midrange (monotonic).
  3. A genuinely fast aggro deck (low curve, cheap threats, reach, light interaction)
     clears at least B — the whole point — while a slow, reach-less "aggro" deck does
     not get a free pass.
  4. `_clock_score` is bounded to [0, 7] and `deck_plan` respects an explicit header.

Distribution-independent. Returns a list of error strings; empty == healthy.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _pure_floor(inter, ca, uncast=0):
    """The original interaction+card-advantage floor, for the no-regression check."""
    if uncast > 0:
        return "C"
    resil = inter + ca
    if inter >= 5 and resil >= 7:
        return "A"
    if inter >= 3 and resil >= 4:
        return "B"
    if resil >= 2:
        return "C"
    return "D"


def check():
    """Return a list of error strings (empty == healthy). Never raises."""
    try:
        import deck
    except Exception as e:  # pragma: no cover - import guard
        return [f"tier floor: could not import deck.py ({e})"]

    errs = []
    tb = deck.tier_band
    RANK = deck.TIER_RANK

    def vec(plan, inter, ca, uncast=0, avg_mv=3.0, early=0, reach=0):
        return {"plan": plan, "interaction": inter, "card_advantage": ca,
                "uncastable": uncast, "avg_mv": avg_mv, "early_drops": early, "reach": reach}

    # (1) non-aggro == pure floor, across a grid.
    for plan in ("midrange", "control", "combo", "tempo-ish-unknown"):
        for inter in (0, 2, 3, 5, 7):
            for ca in (0, 2, 4):
                for unc in (0, 1):
                    got = tb(vec(plan, inter, ca, unc, avg_mv=2.0, early=20, reach=20))
                    exp = _pure_floor(inter, ca, unc)
                    if got != exp:
                        errs.append(f"tier_band regressed for non-aggro plan {plan!r} "
                                    f"(int {inter}, ca {ca}, unc {unc}): got {got}, expected {exp} "
                                    "— a non-aggro floor must ignore the clock.")

    # (2) monotonic: aggro floor >= same-vector midrange floor.
    for inter in (0, 2, 3, 5):
        for ca in (0, 2, 4):
            for avg_mv, early, reach in ((2.0, 16, 10), (3.5, 2, 0), (2.4, 10, 5)):
                a = tb(vec("aggro", inter, ca, 0, avg_mv, early, reach))
                m = tb(vec("midrange", inter, ca, 0, avg_mv, early, reach))
                if RANK.get(a, 0) < RANK.get(m, 0):
                    errs.append(f"tier_band: aggro floor {a} is BELOW the midrange floor {m} "
                                f"(int {inter}, ca {ca}) — the clock must never lower a band.")

    # (3) a fast aggro deck clears >= B; a slow reach-less one does not benefit.
    fast = tb(vec("aggro", inter=2, ca=0, avg_mv=2.0, early=16, reach=10))
    if RANK.get(fast, 0) < RANK.get("B", 0):
        errs.append(f"tier_band: a fast aggro deck (low curve, cheap threats, reach) floored "
                    f"{fast} < B — the #4 fix isn't crediting the clock.")
    slow = tb(vec("aggro", inter=2, ca=0, avg_mv=3.6, early=1, reach=0))
    if slow != _pure_floor(2, 0):
        errs.append(f"tier_band: a slow, reach-less 'aggro' deck floored {slow} — it should get "
                    f"no clock benefit (expected {_pure_floor(2, 0)}).")

    # (4) clock bounds + explicit-plan honoring.
    cs = deck._clock_score
    for v in (vec("aggro", 0, 0, 0, 2.0, 20, 20), vec("aggro", 0, 0, 0, 9.0, 0, 0)):
        if not (0 <= cs(v) <= 7):
            errs.append(f"_clock_score out of [0,7]: {cs(v)} for {v}.")
    if deck.deck_plan({"plan": "aggro"}) != "aggro" or deck.deck_plan({"plan": "control"}) != "control":
        errs.append("deck_plan must honor an explicit `#: plan:` header.")
    if deck.deck_plan({"archetype": "Golgari midrange value"}) != "midrange":
        errs.append("deck_plan should read 'midrange' from a midrange archetype line.")

    return errs


def main():
    errs = check()
    if errs:
        print("Tier floor sanity: FAIL")
        for e in errs[:20]:
            print(f"  ✗ {e}")
        return 1
    print("Tier floor sanity: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
