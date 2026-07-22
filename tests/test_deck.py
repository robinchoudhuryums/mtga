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
