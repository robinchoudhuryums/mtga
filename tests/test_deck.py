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
