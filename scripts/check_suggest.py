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

    # (7) cuts power co-signal (#3): the keep-score nudge from a card's 0–10 power must
    #     be BOUNDED (±cap), neutral at the center, and monotonic (a bomb is protected,
    #     a weak on-theme body sorts up) — so it only breaks near-ties in the cut ranking
    #     and never overrides theme fit (mirrors the suggest power co-signal, anchor 5).
    cpa = deck._cuts_power_adj
    cap = deck._CUTS_POWER_CAP
    if not all(abs(cpa(p)) <= cap for p in (0, 1, 2.5, 5, 7.5, 10)):
        errs.append(f"_cuts_power_adj escapes ±{cap} for an in-range power (0–10): "
                    f"{[cpa(p) for p in (0, 5, 10)]}.")
    if not (cpa(100) == cap and cpa(-100) == -cap):
        errs.append(f"_cuts_power_adj clamp doesn't engage on an out-of-range power: "
                    f"cpa(100)={cpa(100)}, cpa(-100)={cpa(-100)} (want ±{cap}).")
    if cpa(deck._CUTS_POWER_NEUTRAL) != 0.0:
        errs.append(f"_cuts_power_adj not neutral at center {deck._CUTS_POWER_NEUTRAL}: "
                    f"got {cpa(deck._CUTS_POWER_NEUTRAL)}.")
    if not (cpa(9) > cpa(5) > cpa(1)):
        errs.append(f"_cuts_power_adj not monotonic in power: {[cpa(1), cpa(5), cpa(9)]} "
                    "— a bomb must be protected and a weak card made more cuttable.")
    if cap > 3.0:
        errs.append(f"_CUTS_POWER_CAP too large ({cap}): the power nudge must stay a "
                    "tie-breaker next to theme fit, not a lever.")

    # (8) cuts ability-distinctiveness co-signal: the keep-score nudge from a card's 0–10
    #     distinctiveness must be BOUNDED (±cap), neutral at the center, and monotonic (a
    #     distinctive-mechanic card is protected, a generic-ability filler sorts up) — so it
    #     only breaks near-ties and never overrides theme fit. Mirrors anchor 7; also proves
    #     it stays ORTHOGONAL to power (its own bounded term, not folded into the power adj).
    cua = deck._cuts_uniq_adj
    ucap = deck._CUTS_UNIQ_CAP
    if not all(abs(cua(u)) <= ucap for u in (0, 1.5, 4, 6, 8, 10)):
        errs.append(f"_cuts_uniq_adj escapes ±{ucap} for an in-range distinctiveness (0–10): "
                    f"{[cua(u) for u in (0, 4, 10)]}.")
    if not (cua(100) == ucap and cua(-100) == -ucap):
        errs.append(f"_cuts_uniq_adj clamp doesn't engage out-of-range: "
                    f"cua(100)={cua(100)}, cua(-100)={cua(-100)} (want ±{ucap}).")
    if cua(deck._CUTS_UNIQ_NEUTRAL) != 0.0:
        errs.append(f"_cuts_uniq_adj not neutral at center {deck._CUTS_UNIQ_NEUTRAL}: "
                    f"got {cua(deck._CUTS_UNIQ_NEUTRAL)}.")
    if not (cua(9) > cua(4) > cua(1)):
        errs.append(f"_cuts_uniq_adj not monotonic in distinctiveness: {[cua(1), cua(4), cua(9)]} "
                    "— a distinctive card must be protected and a generic-ability filler cut.")
    if ucap > 3.0:
        errs.append(f"_CUTS_UNIQ_CAP too large ({ucap}): the distinctiveness nudge must stay a "
                    "tie-breaker next to theme fit, not a lever.")

    # The distinctiveness metric itself: a vanilla card (only a tribe tag) must read ~0, a
    # rare-mechanic tag must outscore a generic one, and everything stays in [0, 10].
    import lib
    idf = {"etb": 1.6, "landcycling": 7.0, "Bear": 6.0}
    n = 15000
    vanilla = lib.distinctiveness_score(["Bear"], idf, {"Bear"}, n)
    generic = lib.distinctiveness_score(["etb"], idf, {"Bear"}, n)
    rare = lib.distinctiveness_score(["landcycling", "etb"], idf, {"Bear"}, n)
    if not (0.0 <= vanilla <= 0.0):
        errs.append(f"distinctiveness_score: a vanilla card (tribe tag only) must be 0.0, got {vanilla}.")
    if not (0.0 <= generic < rare <= 10.0):
        errs.append(f"distinctiveness_score: a rare mechanic ({rare}) must outscore a generic "
                    f"tag ({generic}); both in [0,10].")

    # Structural signal (oracle-text shape): a vanilla / plain-ETB / bare-mana body must read
    # LOW; an unusual dies-trigger-that-recurs must read high; and card_distinctiveness must
    # take the MAX so a generically-TAGGED but structurally-rich card is RESCUED, never a
    # generic one inflated (structural only ever raises).
    sd = lib.structural_distinctiveness
    sd_vanilla = sd("Trample")
    sd_etb = sd("When this creature enters, create a 1/1 white Soldier creature token.")
    sd_mana = sd("{T}: Add {G}.")
    sd_rich = sd("When this creature dies, destroy target permanent and return target "
                 "nonlegendary permanent card from your graveyard to the battlefield.")
    if not all(0.0 <= v <= 10.0 for v in (sd_vanilla, sd_etb, sd_mana, sd_rich)):
        errs.append(f"structural_distinctiveness out of [0,10]: "
                    f"{sd_vanilla}, {sd_etb}, {sd_mana}, {sd_rich}.")
    if not (sd_vanilla <= 1.0 and sd_mana <= 1.0 and sd_etb <= 2.0):
        errs.append(f"structural_distinctiveness must read a vanilla/plain-ETB/bare-mana card "
                    f"LOW (vanilla {sd_vanilla}, ETB {sd_etb}, mana {sd_mana}).")
    if not (sd_rich > sd_etb):
        errs.append(f"structural_distinctiveness: an unusual dies-trigger ({sd_rich}) must "
                    f"outscore a plain ETB token-maker ({sd_etb}).")
    # The MAX combine: a generically-tagged card with rich structure is rescued (uses the
    # real pool model for the tag term; structural is pure).
    rescue_text = ("When this creature dies, destroy target permanent and return target card "
                   "from your graveyard to the battlefield.")
    if lib.card_distinctiveness(["etb", "tokens"], rescue_text) < 4.0:
        errs.append("card_distinctiveness: the structural signal must RESCUE a mis-tagged "
                    "distinctive card (etb/tokens tags + a rich dies-trigger) above generic.")
    if lib.card_distinctiveness(["etb", "tokens"], "") > lib.card_distinctiveness(["etb", "tokens"], rescue_text):
        errs.append("card_distinctiveness: structural must only ever RAISE (max), never lower, "
                    "the tag-only score.")

    # (9) `suggest --lands` co-signals: the SYNERGY and SHORTFALL nudges must stay BOUNDED and
    #     non-negative, so a land is chosen for FIXING first and the ability/scarcity terms
    #     only re-rank near-ties (fixing is 0–10; these caps are ≤2). A land sharing nothing /
    #     producing no scarce color reads 0.
    lsb = deck._land_synergy_bonus
    lfb = deck._land_shortfall_bonus
    themes = {"equipment": 17, "counters": 3, "pump": 15}
    if lsb([], themes) != 0.0 or lsb(["counters"], {}) != 0.0:
        errs.append("_land_synergy_bonus must be 0 with no tags or no themes.")
    if not all(0.0 <= lsb(t, themes) <= deck._LAND_SYN_CAP
               for t in ([], ["counters"], ["equipment"], ["equipment", "pump"])):
        errs.append(f"_land_synergy_bonus escapes [0, {deck._LAND_SYN_CAP}].")
    if not (lsb(["equipment"], themes) > lsb(["counters"], themes)):
        errs.append("_land_synergy_bonus: a land on the deck's TOP theme must beat one on a "
                    "minor theme.")
    deficit = {"W": 0.30, "R": 0.05}
    if not all(0.0 <= lfb(c, deficit) <= deck._LAND_SHORT_CAP
               for c in ([], ["W"], ["R"], ["W", "R"])):
        errs.append(f"_land_shortfall_bonus escapes [0, {deck._LAND_SHORT_CAP}].")
    if not (lfb(["W"], deficit) > lfb(["R"], deficit)):
        errs.append("_land_shortfall_bonus: producing the SCARCER color (W) must beat the "
                    "well-served one (R).")
    if lfb(["W"], {}) != 0.0 or lfb(["W"], {"W": 0.0, "R": 0.0}) != 0.0:
        errs.append("_land_shortfall_bonus must be 0 when nothing is scarce.")
    if deck._LAND_SYN_CAP > 3.0 or deck._LAND_SHORT_CAP > 3.0:
        errs.append("land co-signal caps too large: fixing (0–10) must stay dominant.")

    # (10) the NEEDS-model co-signals (--ramp / --interaction) stay bounded: accel-want in
    #      [0,1] and rising with curve; restriction-fit centered/bounded (± for match/mismatch,
    #      0 unrestricted); scaling-boost bounded/non-negative and rising with deck support.
    aw = deck._accel_want
    if not (aw(2.0, 0.0) == 0.0 and 0.0 <= aw(3.0, 0.3) <= 1.0 and aw(4.0, 0.6) >= aw(3.0, 0.3)):
        errs.append(f"_accel_want must be 0 for a lean curve, ≤1, and rise with top-heaviness "
                    f"(got {aw(2.0, 0.0)}, {aw(3.0, 0.3)}, {aw(4.0, 0.6)}).")
    rf = deck._ramp_restriction_fit
    cap = deck._RAMP_RESTRICT_CAP
    if rf("no restriction here", {"equipment": 0.4}) != 0.0:
        errs.append("_ramp_restriction_fit must be 0 for unrestricted mana.")
    hi = rf("Spend this mana only to cast an Equipment spell.", {"equipment": 0.5})
    lo = rf("Spend this mana only to cast an Equipment spell.", {"equipment": 0.0})
    if not (0 < hi <= cap and -cap <= lo < 0):
        errs.append(f"_ramp_restriction_fit: + when the type is dense, − when scarce, ±{cap} "
                    f"(got hi {hi}, lo {lo}).")
    sb = deck._int_scaling_boost
    scap = deck._INT_SCALE_CAP
    if sb(None, 1.0) != 0.0:
        errs.append("_int_scaling_boost must be 0 for a non-scaling card.")
    if not (0.0 <= sb("fight", 0.9) <= scap and sb("fight", 0.9) > sb("fight", 0.1)):
        errs.append(f"_int_scaling_boost must be [0,{scap}] and rise with deck support "
                    f"(got {sb('fight', 0.9)} vs {sb('fight', 0.1)}).")
    if any(c > 3.0 for c in (deck._RAMP_ACCEL_CAP, cap, scap)):
        errs.append("needs-model caps too large: they must stay bounded tie-breakers.")

    # (11) fit_strength must NOT credit a bare BROAD-TRIBE overlap as a home (the
    #      Hawkeye-"KEY"-in-every-Hero/Human-deck over-assignment, tagging-misreads #4):
    #      a broad background tribe (_GENERIC_TRIBES) can't mint KEY even as the top theme
    #      or via a #: protect: signature — while a NARROW tribe and a specific theme still
    #      do. This keeps the tribe demotion from silently regressing into a false KEY.
    fs = deck.fit_strength
    if fs(["Human", "Hero"], {"Human": 19, "Hero": 15}, "", 8, 8) != "tangential":
        errs.append("fit_strength: a bare broad-tribe overlap must be tangential, not KEY.")
    if fs(["Human"], {"Human": 19}, "", 8, 8, signature={"Human"}) != "tangential":
        errs.append("fit_strength: a broad tribe must not mint KEY via a #: protect: signature.")
    if fs(["Ninja"], {"Ninja": 10}, "", 8, 8) != "KEY":
        errs.append("fit_strength: a narrow build-around tribe must still read KEY.")
    if fs(["Human", "Dinosaur"], {"Human": 5, "Dinosaur": 10}, "", 8, 8) != "KEY":
        errs.append("fit_strength: a specific theme alongside a broad tribe must still read KEY.")
    if not deck._GENERIC_TRIBES or "wizard" in deck._GENERIC_TRIBES:
        errs.append("_GENERIC_TRIBES must be non-empty and must NOT include real tribal "
                    "signatures (e.g. Wizard).")

    # (12a) the suggest-homes curve co-signal `_home_curve_fit` stays a bounded, never-
    #       boosting SORT nudge: 1.0 within ~2 MV of a deck's average, penalized beyond,
    #       capped at _HOME_CURVE_CAP, and 1.0 on an unknown MV — so it can only reorder
    #       same-strength fits, never relabel or override theme fit (finding #5).
    hcf = deck._home_curve_fit
    if hcf(None, 3.0) != 1.0 or hcf(5.0, 0.0) != 1.0:
        errs.append("_home_curve_fit must be 1.0 when a MV is unknown.")
    if hcf(4.0, 2.5) != 1.0:
        errs.append("_home_curve_fit must not penalize a card within ~2 MV of the average.")
    heavy = hcf(6.0, 2.4)
    if not (1.0 - deck._HOME_CURVE_CAP <= heavy < 1.0):
        errs.append(f"_home_curve_fit must penalize a top-heavy card within [1-cap,1) (got {heavy}).")
    if hcf(11.0, 2.0) < 1.0 - deck._HOME_CURVE_CAP:
        errs.append("_home_curve_fit must never exceed the _HOME_CURVE_CAP penalty.")
    if deck._HOME_CURVE_CAP > 0.25:
        errs.append("_HOME_CURVE_CAP too large: the curve nudge must stay a bounded tie-breaker.")

    # (12b) `_central_themes` admits a curated high-precision mechanical sub-theme
    #       (_MECHANIC_SUBTHEMES) at a flat floor of 2 so a secondary payoff surfaces, but a
    #       GENERIC theme at the same low weight STAYS gated behind the 25% cutoff (the
    #       relaxation can't fake a generic overlap into a home) — centrality residual fix.
    mech = next(iter(deck._MECHANIC_SUBTHEMES))
    tw = {"tokens": 20, mech: 2}                 # mech at wt 2, cutoff = 0.25*20 = 5
    cen = deck._central_themes(tw)
    if mech not in cen:
        errs.append(f"_central_themes must admit a mechanical sub-theme ({mech}) at floor 2.")
    if "counters" in deck._central_themes({"tokens": 20, "counters": 2}):
        errs.append("_central_themes must still gate a GENERIC theme at low weight (no free pass).")
    if not deck._MECHANIC_SUBTHEMES or deck._MECHANIC_SUBTHEMES & deck.GENERIC_THEMES:
        errs.append("_MECHANIC_SUBTHEMES must be non-empty and disjoint from GENERIC_THEMES.")

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
