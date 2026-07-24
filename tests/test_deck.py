"""Unit tests for the pure analysis helpers in scripts/deck.py.

Covers the mana-pip parser, the canonical role tally, tier floor, engine-role
classifier, rotation math, and the git-independent card-delta arithmetic — the
functions the whole grading/ranking stack is built on. The check_* gates assert the
same models at the integration level; these pin the isolated edge cases fast."""
from datetime import date, timedelta

import deck


class TestParsePips:
    def test_strict_pips(self):
        strict, hybrid = deck.parse_pips("{2}{W}{U}")
        assert strict == {"W": 1, "U": 1}
        assert hybrid == []

    def test_true_multicolor_hybrid(self):
        strict, hybrid = deck.parse_pips("{W/U}")
        assert strict == {}
        assert hybrid == [frozenset({"W", "U"})]

    def test_monocolor_hybrid_is_len1(self):
        # {2/W} is payable without W, so it must not constrain castable colors.
        _strict, hybrid = deck.parse_pips("{2/W}")
        assert hybrid == [frozenset({"W"})]
        assert all(len(h) < 2 for h in hybrid)

    def test_phyrexian_is_len1(self):
        _strict, hybrid = deck.parse_pips("{W/P}")
        assert all(len(h) < 2 for h in hybrid)

    def test_empty(self):
        assert deck.parse_pips("") == ({}, [])


class TestClassifyRoles:
    def test_spot_removal(self):
        assert "Removal (spot)" in deck.classify_roles("Destroy target creature.")

    def test_card_advantage(self):
        assert "Card advantage" in deck.classify_roles("Draw two cards.")

    def test_single_cantrip_not_card_advantage(self):
        # A one-card draw is deliberately NOT counted as card advantage.
        assert "Card advantage" not in deck.classify_roles("Draw a card.")

    def test_vanilla_has_no_interaction_role(self):
        # Combat keywords are not functional interaction/card-advantage.
        roles = deck.classify_roles("Flying. Vigilance.")
        assert not (roles & deck._INTERACTION_ROLES)
        assert "Card advantage" not in roles


class TestRoleTally:
    CD = {
        "go for the throat": {"type": "Instant", "text": "Destroy target creature.", "colors": "B"},
        "divination": {"type": "Sorcery", "text": "Draw two cards.", "colors": "U"},
        "forest": {"type": "Basic Land — Forest", "text": "", "colors": ""},
    }

    def test_quantity_weighted_and_land_skipped(self):
        cards = [(2, "Go for the Throat", "", ""), (1, "Divination", "", ""), (4, "Forest", "", "")]
        t = deck.role_tally(cards, self.CD)
        assert t["interaction"] == 2      # 2 copies of removal
        assert t["card_advantage"] == 1   # Divination
        # a basic land contributes to neither

    def test_split_across_lines_sums(self):
        cards = [(2, "Go for the Throat", "S1", ""), (1, "Go for the Throat", "S2", "")]
        assert deck.role_tally(cards, self.CD)["interaction"] == 3

    def test_interaction_count_matches_role_tally(self):
        cards = [(2, "Go for the Throat", "", "")]
        assert deck._interaction_count(cards, self.CD) == deck.role_tally(cards, self.CD)["interaction"]


class TestMultisetAndDelta:
    def test_multiset_case_insensitive_sums(self):
        ms = deck._multiset([(2, "Shock", "", ""), (1, "shock", "", "")])
        assert ms == {"shock": ("Shock", 3)}  # first spelling kept

    def test_ms_delta(self):
        prev = deck._multiset([(2, "A", "", ""), (1, "B", "", "")])
        cur = deck._multiset([(1, "A", "", ""), (1, "C", "", "")])
        added, removed = deck._ms_delta(prev, cur)
        assert added == [("C", 1)]
        assert removed == [("A", 1), ("B", 1)]

    def test_ms_delta_no_change(self):
        ms = deck._multiset([(1, "A", "", "")])
        assert deck._ms_delta(ms, ms) == ([], [])


class TestRotation:
    def test_rotation_year(self):
        assert deck.rotation_year("2023-11-17", 3) == 2026
        assert deck.rotation_year("2024-01-01", 2) == 2026

    def test_rotation_year_blank_or_bad(self):
        assert deck.rotation_year("", 3) is None
        assert deck.rotation_year("not-a-date", 3) is None
        assert deck.rotation_year(None, 3) is None

    def test_rotation_risk_relative_to_today(self):
        old = (date.today() - timedelta(days=365 * 4)).isoformat()
        new = (date.today() - timedelta(days=365)).isoformat()
        assert deck.rotation_risk(old, 3) is True
        assert deck.rotation_risk(new, 3) is False

    def test_rotation_risk_blank_is_false(self):
        assert deck.rotation_risk("", 3) is False
        assert deck.rotation_risk(None, 3) is False


def _vec(plan, inter, ca, uncast=0, avg_mv=3.0, early=0, reach=0):
    return {"plan": plan, "interaction": inter, "card_advantage": ca,
            "uncastable": uncast, "avg_mv": avg_mv, "early_drops": early, "reach": reach}


class TestTierBand:
    def test_a_floor(self):
        assert deck.tier_band(_vec("midrange", 5, 3)) == "A"

    def test_b_floor(self):
        assert deck.tier_band(_vec("midrange", 3, 1)) == "B"

    def test_d_floor(self):
        assert deck.tier_band(_vec("midrange", 0, 0)) == "D"

    def test_uncastable_caps_at_c(self):
        assert deck.tier_band(_vec("midrange", 5, 3, uncast=1)) == "C"

    def test_aggro_clock_only_raises(self):
        fast = deck.tier_band(_vec("aggro", 2, 0, avg_mv=2.0, early=16, reach=10))
        mid = deck.tier_band(_vec("midrange", 2, 0, avg_mv=2.0, early=16, reach=10))
        assert deck.TIER_RANK[fast] >= deck.TIER_RANK[mid]

    def test_clock_score_bounded(self):
        for v in (_vec("aggro", 0, 0, avg_mv=2.0, early=20, reach=20),
                  _vec("aggro", 0, 0, avg_mv=9.0, early=0, reach=0)):
            assert 0 <= deck._clock_score(v) <= 7

    def test_deck_plan_honours_header(self):
        assert deck.deck_plan({"plan": "aggro"}) == "aggro"
        assert deck.deck_plan({"plan": "control"}) == "control"
        assert deck.deck_plan({"archetype": "Golgari midrange value"}) == "midrange"


class TestScoringTermsBounded:
    def test_role_credit_flat_and_zero(self):
        R = next(iter(deck.IMPACT_ROLES))
        assert deck._role_credit({R}) == 9   # base 3 + impact 6
        assert deck._role_credit(set()) == 0

    def test_role_credit_diminishing(self):
        R = next(iter(deck.IMPACT_ROLES))
        seq = [deck._role_credit({R}, {R: k}) for k in (0, 1, 2, 4, 8)]
        assert all(a > b for a, b in zip(seq, seq[1:]))
        assert min(seq) >= 3

    def test_curve_gap_factor_bounded(self):
        curves = [{}, {1: 4, 2: 4, 3: 2}, {2: 12}]
        for cv in curves:
            for mv in (None, 0, 1, 3, 6, 12):
                assert 0.85 <= deck._curve_gap_factor(mv, cv) <= 1.15


class TestConsistencyMath:
    """The hypergeometric manabase/opening-hand model behind `deck.py consistency`."""

    def test_hypergeom_bounds(self):
        # k=0 is certain; wanting more successes than exist is impossible.
        assert deck.hypergeom_at_least(60, 24, 7, 0) == 1.0
        assert deck.hypergeom_at_least(60, 3, 7, 4) == 0.0   # only 3 successes, want 4
        assert deck.hypergeom_at_least(60, 24, 0, 1) == 0.0  # draw nothing, want 1

    def test_hypergeom_monotonic_in_sources(self):
        # More sources in the deck -> higher P of hitting the pip requirement.
        seq = [deck.hypergeom_at_least(60, k, 9, 2) for k in (4, 8, 12, 16, 20)]
        assert all(a < b for a, b in zip(seq, seq[1:]))

    def test_hypergeom_matches_known_value(self):
        # P(>=1 of 24 lands in the opening 7 of 60) = 1 - C(36,7)/C(60,7) ≈ 0.978.
        import math
        p = deck.hypergeom_at_least(60, 24, 7, 1)
        assert abs(p - (1 - math.comb(36, 7) / math.comb(60, 7))) < 1e-9
        assert 0.97 < p < 0.99

    def test_cards_seen_play_vs_draw(self):
        assert deck.cards_seen(1, on_play=True) == 7     # opening, no turn-1 draw
        assert deck.cards_seen(1, on_play=False) == 8    # on the draw, +1
        assert deck.cards_seen(3, on_play=True) == 9

    def test_cast_probability_multicolor_is_product(self):
        srcs = {"B": 16, "R": 1, "W": 0, "U": 0, "G": 0}
        # A {B}{R} card on turn 2 with a single red source should be dismal.
        p = deck.cast_probability(60, srcs, 2, {"B": 1, "R": 1})
        assert 0.0 < p < 0.3
        # An empty pip demand is always castable.
        assert deck.cast_probability(60, srcs, 2, {}) == 1.0

    def test_min_sources_for_increases_with_pip_count(self):
        one = deck.min_sources_for(60, 3, 1, target=0.90)
        two = deck.min_sources_for(60, 3, 2, target=0.90)
        assert two > one > 0

    def test_opening_land_stats_partition(self):
        st = deck.opening_land_stats(60, 24)
        # keepable + screw + flood covers 0..7 lands exactly (a partition).
        assert abs(st["keepable"] + st["screw"] + st["flood"] - 1.0) < 1e-9
        assert 0.0 <= st["hit2"] <= 1.0 and st["hit3"] < st["hit2"]

    def test_more_lands_fewer_screw(self):
        assert deck.opening_land_stats(60, 26)["screw"] < deck.opening_land_stats(60, 20)["screw"]


class TestCutsPowerAdj:
    """The bounded card-quality co-signal folded into the cut ranking (#3)."""

    def test_bounded_both_directions(self):
        for p in (0, 2.5, 5, 7.5, 10):
            assert -deck._CUTS_POWER_CAP <= deck._cuts_power_adj(p) <= deck._CUTS_POWER_CAP
        # The clamp is a safety rail for out-of-range power (seed is always 0–10).
        assert deck._cuts_power_adj(100) == deck._CUTS_POWER_CAP
        assert deck._cuts_power_adj(-100) == -deck._CUTS_POWER_CAP

    def test_neutral_at_center(self):
        assert deck._cuts_power_adj(deck._CUTS_POWER_NEUTRAL) == 0.0

    def test_monotonic_bomb_beats_weak(self):
        assert deck._cuts_power_adj(9) > deck._cuts_power_adj(3)


class TestCutsUniqAdj:
    """The bounded ability-distinctiveness co-signal folded into the cut ranking."""

    def test_bounded_both_directions(self):
        for u in (0, 1.5, 4, 6, 8, 10):
            assert -deck._CUTS_UNIQ_CAP <= deck._cuts_uniq_adj(u) <= deck._CUTS_UNIQ_CAP
        assert deck._cuts_uniq_adj(100) == deck._CUTS_UNIQ_CAP
        assert deck._cuts_uniq_adj(-100) == -deck._CUTS_UNIQ_CAP

    def test_neutral_at_center(self):
        assert deck._cuts_uniq_adj(deck._CUTS_UNIQ_NEUTRAL) == 0.0

    def test_monotonic_distinctive_beats_generic(self):
        # A distinctive-mechanic card is protected; a generic-ability filler sorts up.
        assert deck._cuts_uniq_adj(9) > deck._cuts_uniq_adj(1)

    def test_cap_stays_a_tiebreaker(self):
        # Smaller than the theme-fit scale — it can't override a real fit gap.
        assert deck._CUTS_UNIQ_CAP <= 3.0


class TestLandSuggestBonuses:
    """The bounded synergy + shortfall co-signals of the manabase recommender."""
    THEMES = {"equipment": 17, "counters": 3, "pump": 15}
    DEFICIT = {"W": 0.30, "R": 0.05}

    def test_synergy_zero_without_overlap(self):
        assert deck._land_synergy_bonus([], self.THEMES) == 0.0
        assert deck._land_synergy_bonus(["landfall"], self.THEMES) == 0.0
        assert deck._land_synergy_bonus(["counters"], {}) == 0.0

    def test_synergy_bounded_and_scaled(self):
        for tags in ([], ["counters"], ["equipment"], ["equipment", "pump"]):
            assert 0.0 <= deck._land_synergy_bonus(tags, self.THEMES) <= deck._LAND_SYN_CAP
        # a land on the deck's TOP theme beats one on a minor theme
        assert (deck._land_synergy_bonus(["equipment"], self.THEMES)
                > deck._land_synergy_bonus(["counters"], self.THEMES))

    def test_shortfall_bounded(self):
        for cols in ([], ["W"], ["R"], ["W", "R"]):
            assert 0.0 <= deck._land_shortfall_bonus(cols, self.DEFICIT) <= deck._LAND_SHORT_CAP

    def test_shortfall_favors_scarce_color(self):
        assert (deck._land_shortfall_bonus(["W"], self.DEFICIT)
                > deck._land_shortfall_bonus(["R"], self.DEFICIT))
        # a land covering the scarce color scores == the scarce single, via max()
        assert (deck._land_shortfall_bonus(["W", "R"], self.DEFICIT)
                == deck._land_shortfall_bonus(["W"], self.DEFICIT))

    def test_shortfall_zero_when_nothing_scarce(self):
        assert deck._land_shortfall_bonus(["W"], {}) == 0.0
        assert deck._land_shortfall_bonus(["W"], {"W": 0.0, "R": 0.0}) == 0.0

    def test_caps_keep_fixing_dominant(self):
        # Both nudges must be small next to the 0–10 fixing axis.
        assert deck._LAND_SYN_CAP <= 3.0 and deck._LAND_SHORT_CAP <= 3.0


class TestNeedsModelSignals:
    """The bounded co-signals of the --ramp / --interaction needs-aware recommenders."""

    def test_accel_want_lean_curve_is_zero(self):
        assert deck._accel_want(2.0, 0.0) == 0.0
        assert deck._accel_want(2.2, 0.1) == 0.0

    def test_accel_want_bounded_and_rising(self):
        for mv, h in ((2.0, 0.0), (3.0, 0.3), (3.8, 0.5), (6.0, 0.9)):
            assert 0.0 <= deck._accel_want(mv, h) <= 1.0
        assert deck._accel_want(4.0, 0.6) > deck._accel_want(3.0, 0.3)

    def test_restriction_fit_unrestricted_is_zero(self):
        assert deck._ramp_restriction_fit("{T}: Add {G}.", {"equipment": 0.4}) == 0.0

    def test_restriction_fit_match_vs_mismatch(self):
        hi = deck._ramp_restriction_fit(
            "Spend this mana only to cast an Equipment spell.", {"equipment": 0.5})
        lo = deck._ramp_restriction_fit(
            "Spend this mana only to cast an Equipment spell.", {"equipment": 0.0})
        assert 0 < hi <= deck._RAMP_RESTRICT_CAP
        assert -deck._RAMP_RESTRICT_CAP <= lo < 0

    def test_scaling_axis_detection(self):
        assert deck._int_scaling("Target creature you control fights target creature.") == "fight"
        assert deck._int_scaling(
            "deals damage equal to the number of creatures you control") == "creatures"
        assert deck._int_scaling("Deal {X} damage") == "x-cost"
        assert deck._int_scaling("Destroy target creature.") is None

    def test_scaling_boost_bounded_and_rising(self):
        assert deck._int_scaling_boost(None, 1.0) == 0.0
        for m in (0.0, 0.3, 0.7, 1.0):
            assert 0.0 <= deck._int_scaling_boost("fight", m) <= deck._INT_SCALE_CAP
        assert deck._int_scaling_boost("fight", 0.9) > deck._int_scaling_boost("fight", 0.1)

    def test_caps_stay_tiebreakers(self):
        assert deck._RAMP_ACCEL_CAP <= 3.0
        assert deck._RAMP_RESTRICT_CAP <= 3.0
        assert deck._INT_SCALE_CAP <= 3.0


class TestProducesMana:
    """The broad mana-source detector behind the tier tune plan's ramp-loss flag —
    catches dorks the 'Ramp / fixing' role misses (the 'add one mana' phrasing)."""

    def test_symbol_tap_dork(self):
        assert deck._produces_mana("{T}: Add {G}.")
        assert deck._produces_mana("{T}: Add {C}{C}.")

    def test_add_one_mana_phrasing(self):
        # Bloom Tender's Vivid ability — no "{T}: add {SYM}" template.
        assert deck._produces_mana(
            "Vivid — {T}: For each color among permanents you control, add one mana of that color.")
        assert deck._produces_mana("{T}: Add one mana of any color.")

    def test_not_a_mana_source(self):
        assert not deck._produces_mana("Converge — deals X damage, where X is the number of "
                                       "colors of mana spent to cast this spell.")
        assert not deck._produces_mana("Put a +1/+1 counter on target creature.")
        assert not deck._produces_mana("")


class TestFitStrength:
    """card→deck fit labels — the fix that stops a generically-good card reading KEY
    in every low-interaction deck it merely shares a generic tag with."""

    def test_generic_only_plus_role_gap_is_tangential(self):
        # A removal card sharing ONLY generic themes with a low-interaction deck must
        # NOT read KEY just because the deck is short on interaction (the Get Lost bug).
        s = deck.fit_strength(["etb", "tokens"], {"etb": 5, "tokens": 5, "Cat": 10},
                              "Destroy target creature.", deck_int=2, deck_ca=0)
        assert s == "tangential"

    def test_specific_theme_plus_role_gap_is_key(self):
        s = deck.fit_strength(["Wizard"], {"Wizard": 10},
                              "Destroy target creature.", deck_int=2, deck_ca=0)
        assert s == "KEY"

    def test_signature_match_is_key(self):
        s = deck.fit_strength(["counters"], {"counters": 10}, "", 8, 8,
                              signature={"counters"})
        assert s == "KEY"

    def test_specific_top_theme_is_key(self):
        assert deck.fit_strength(["Cat"], {"Cat": 10}, "", 8, 8) == "KEY"

    def test_specific_secondary_theme_is_role_player(self):
        assert deck.fit_strength(["Cat"], {"Cat": 2, "tokens": 10}, "", 8, 8) == "role-player"

    def test_generic_only_no_gap_is_tangential(self):
        assert deck.fit_strength(["tokens"], {"tokens": 10}, "", 8, 8) == "tangential"

    # --- broad background tribes never mint a KEY by themselves (tagging-misreads #4) ---
    def test_broad_tribe_top_theme_is_not_key(self):
        # Hawkeye sharing only Human/Hero with a mono-Human deck must NOT read KEY even
        # though Human is the deck's most-common theme (the KEY-in-every-Hero-deck fix).
        assert deck.fit_strength(["Human", "Hero"], {"Human": 19, "Hero": 15},
                                 "", 8, 8) == "tangential"

    def test_broad_tribe_not_key_via_signature(self):
        # A broad tribe can't mint KEY even when a protected card carries it.
        assert deck.fit_strength(["Human"], {"Human": 19}, "", 8, 8,
                                 signature={"Human"}) == "tangential"

    def test_broad_tribe_plus_role_gap_is_not_key(self):
        # A removal card sharing only a broad tribe stays out of KEY on a low-int deck.
        assert deck.fit_strength(["Human"], {"Human": 19}, "Destroy target creature.",
                                 deck_int=2, deck_ca=0) == "tangential"

    def test_narrow_tribe_still_key(self):
        # Narrow, build-around tribes remain real signals.
        assert deck.fit_strength(["Ninja"], {"Ninja": 10}, "", 8, 8) == "KEY"

    def test_specific_theme_survives_alongside_broad_tribe(self):
        # A card sharing a broad tribe AND a specific theme is graded on the specific one.
        assert deck.fit_strength(["Human", "Dinosaur"], {"Human": 5, "Dinosaur": 10},
                                 "", 8, 8) == "KEY"


class TestDeckSimilarity:
    """deck.py similar — cosine over central-theme weights with generic themes damped so
    IDENTITY overlap (a shared specific theme) drives the score, not shared value generics."""

    def test_identical_vectors_are_one(self):
        v = {"Dinosaur": 10, "ramp": 4}
        assert abs(deck._theme_cosine(v, dict(v)) - 1.0) < 1e-9

    def test_disjoint_is_zero(self):
        assert deck._theme_cosine({"Ninja": 5}, {"Dinosaur": 5}) == 0.0

    def test_specific_overlap_beats_generic_overlap(self):
        # Two decks sharing a SPECIFIC theme are more similar than two sharing only a
        # generic one at the same raw weight.
        specific = deck._theme_cosine({"Dinosaur": 8, "x": 1}, {"Dinosaur": 8, "y": 1})
        generic = deck._theme_cosine({"etb": 8, "x": 1}, {"etb": 8, "y": 1})
        assert specific > generic

    def test_generic_is_damped_not_removed(self):
        # A generic-only shared theme still yields SOME similarity (decks that both draw
        # cards are loosely alike), just less than the raw weight would imply.
        s = deck._theme_cosine({"card draw": 5}, {"card draw": 5})
        assert 0 < s <= 1.0

    def test_theme_is_generic(self):
        assert deck._theme_is_generic("etb") and deck._theme_is_generic("card draw")
        assert deck._theme_is_generic("Human")          # broad tribe
        assert not deck._theme_is_generic("Dinosaur") and not deck._theme_is_generic("Ninja")

    def test_specific_only_drops_generic_overlap(self):
        # A generic-only overlap scores 0 under the pure-identity lens.
        assert deck._theme_cosine({"etb": 5, "Ninja": 1}, {"etb": 5, "Cat": 1},
                                  specific_only=True) == 0.0

    def test_specific_only_keeps_specific_overlap(self):
        # Sharing a SPECIFIC theme still scores 1.0 under the identity lens (generics ignored,
        # so only the shared Ninja axis remains for both vectors).
        s = deck._theme_cosine({"Ninja": 5, "etb": 9}, {"Ninja": 5, "etb": 2}, specific_only=True)
        assert abs(s - 1.0) < 1e-9


class TestHomeCurveFit:
    """suggest-homes curve co-signal (#5): a bounded, never-boosting SORT nudge that
    penalizes a top-heavy / win-more card in a low-curve deck."""

    def test_unknown_mv_is_neutral(self):
        assert deck._home_curve_fit(None, 3.0) == 1.0
        assert deck._home_curve_fit(5.0, 0.0) == 1.0

    def test_within_two_mv_no_penalty(self):
        assert deck._home_curve_fit(4.0, 2.5) == 1.0
        assert deck._home_curve_fit(2.0, 2.4) == 1.0

    def test_top_heavy_penalized_but_bounded(self):
        m = deck._home_curve_fit(6.0, 2.4)          # excess 3.6
        assert 1.0 - deck._HOME_CURVE_CAP <= m < 1.0

    def test_never_boosts(self):
        # A cheap card in a heavy deck must NOT be boosted (curve nudge is one-sided).
        assert deck._home_curve_fit(2.0, 5.0) == 1.0

    def test_penalty_capped(self):
        assert deck._home_curve_fit(15.0, 2.0) == 1.0 - deck._HOME_CURVE_CAP


class TestCentralThemesMechanicSubtheme:
    """centrality residual fix: a curated mechanical sub-theme surfaces at a flat floor
    of 2 even below the 25% cutoff, but a generic theme stays gated."""

    def test_mechanic_subtheme_admitted_at_floor_two(self):
        mech = next(iter(deck._MECHANIC_SUBTHEMES))
        assert mech in deck._central_themes({"tokens": 20, mech: 2})

    def test_generic_theme_still_gated_at_low_weight(self):
        assert "counters" not in deck._central_themes({"tokens": 20, "counters": 2})

    def test_mechanic_subtheme_below_floor_excluded(self):
        mech = next(iter(deck._MECHANIC_SUBTHEMES))
        assert mech not in deck._central_themes({"tokens": 20, mech: 1})


class TestRedundancyPlanner:
    """The 'virtual copies first, duplicates as fallback' decision helper."""

    def test_already_deep(self):
        p = deck.plan_redundancy_fill(4, 5.0, [(5.0, "X")], target=4)
        assert p["need"] == 0 and p["functional"] == [] and p["duplicates"] == 0

    def test_functional_covers_stays_singleton(self):
        opts = [(5.0, "A"), (4.5, "B"), (4.0, "C"), (4.0, "D")]
        p = deck.plan_redundancy_fill(1, 5.0, opts, target=4)  # need 3, all within tol
        assert p["duplicates"] == 0
        assert [n for _, n in p["functional"]] == ["A", "B", "C"]

    def test_no_options_falls_back_to_duplicates(self):
        p = deck.plan_redundancy_fill(1, 5.0, [], target=4)
        assert p["functional"] == [] and p["duplicates"] == 3
        assert "only option" in p["reason"]

    def test_much_weaker_options_duplicate_instead(self):
        # best existing is 6.0; the only virtual copy is 3.0 (>1.5 below) -> duplicate.
        p = deck.plan_redundancy_fill(2, 6.0, [(3.0, "weak")], target=4)
        assert p["functional"] == [] and p["duplicates"] == 2
        assert "weaker" in p["reason"]

    def test_partial_functional_then_duplicate(self):
        # one acceptable virtual copy, still short -> mix.
        p = deck.plan_redundancy_fill(1, 5.0, [(5.0, "A")], target=4)
        assert [n for _, n in p["functional"]] == ["A"] and p["duplicates"] == 2

    def test_tolerance_boundary_inclusive(self):
        # exactly tol below the best is still acceptable (>=).
        p = deck.plan_redundancy_fill(3, 5.0, [(3.5, "edge")], target=4)  # 5.0-1.5==3.5
        assert [n for _, n in p["functional"]] == ["edge"] and p["duplicates"] == 0


class TestEngineRoles:
    def test_sac_outlet_is_enabler(self):
        assert "enabler" in deck.engine_roles("Sacrifice a creature: Draw a card.").get("sacrifice", set())

    def test_death_trigger_is_death_not_payoff(self):
        got = deck.engine_roles("Whenever a creature you control dies, each opponent loses 1 life.").get("sacrifice", set())
        assert "death" in got and "payoff" not in got

    def test_sac_trigger_is_payoff(self):
        assert "payoff" in deck.engine_roles("Whenever you sacrifice a permanent, draw a card.").get("sacrifice", set())

    def test_edict_is_not_our_outlet(self):
        assert "enabler" not in deck.engine_roles("Target player sacrifices a creature.").get("sacrifice", set())

    def test_flashback_self_enables_graveyard(self):
        got = deck.engine_roles("Lightning deals 3 damage to any target. Flashback {4}{R}.").get("graveyard", set())
        assert "enabler" in got
