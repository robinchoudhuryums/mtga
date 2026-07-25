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

    # --- Under-count fixes. Each string below scored ZERO roles before the list-aware
    # removal pattern / widened Counter pattern / library-tuck pattern went in, so the
    # cards read as having no interaction at all and the tier floor graded on that.
    NONCREATURE_REMOVAL = [
        # Origin of Metalbending, Seedship Impact — a two-type "or" list.
        "Destroy target artifact or enchantment.",
        # Broken Wings, Shattered Wings, Spider Food — a comma list ending in a creature.
        "Destroy target artifact, enchantment, or creature with flying.",
    ]
    ADJECTIVE_REMOVAL = [
        # The hand-kept alternation spelled these out; the rewrite must not lose them.
        "Destroy target creature.", "Exile target attacking creature.",
        "Destroy target tapped creature.", "Destroy target nonland permanent.",
        "Exile target creature or planeswalker.",
    ]

    def test_noncreature_permanent_removal_counts(self):
        for text in self.NONCREATURE_REMOVAL:
            assert "Removal (spot)" in deck.classify_roles(text), text

    def test_adjective_and_plain_removal_still_counts(self):
        for text in self.ADJECTIVE_REMOVAL:
            assert "Removal (spot)" in deck.classify_roles(text), text

    def test_counter_up_to_n_target_counts(self):
        # Repulsive Mutation. Missed by the Counter pattern AND by the coverage net,
        # so the under-read was invisible to the audit meant to catch it.
        assert "Counter" in deck.classify_roles(
            "Put X +1/+1 counters on target creature you control. Then counter up to one "
            "target spell unless its controller pays mana equal to the greatest power "
            "among creatures you control.")

    def test_library_tuck_is_removal(self):
        # Floodpits Drowner's activated ability — the creature leaves the battlefield.
        assert "Removal (spot)" in deck.classify_roles(
            "{1}{U}, {T}: Shuffle this creature and target creature with a stun counter "
            "on it into their owners' libraries.")

    def test_equal_draw_discard_loot_is_not_card_advantage(self):
        # Kiora, the Rising Tide: net zero cards, so not advantage — the same rule that
        # excludes a single-draw cantrip.
        assert "Card advantage" not in deck.classify_roles(
            "When Kiora enters, draw two cards, then discard two cards.")

    def test_net_positive_draw_survives_the_loot_filter(self):
        # Draw 3 / discard 1 is +2 cards: the loot filter must not swallow it.
        assert "Card advantage" in deck.classify_roles("Draw three cards. Discard a card.")
        # And a loot alongside a real draw keeps the role.
        assert "Card advantage" in deck.classify_roles(
            "Draw two cards, then discard two cards. Then draw three cards.")

    def test_half_x_draw_counts(self):
        # Wan Shi Tong, Librarian — "draw half X cards" was in neither the role pattern
        # nor the audit cue, so it was uncounted AND unflagged.
        assert "Card advantage" in deck.classify_roles(
            "When this creature enters, put X +1/+1 counters on him. Then draw half X "
            "cards, rounded down.")


class TestCoverageNetIsSuperset:
    """The audit net must see everything the precise classifier can, or a phrasing is
    missed by BOTH — the hole that hid Repulsive Mutation's counter."""

    def test_interaction_net_covers_every_precise_pattern(self):
        for label in deck._INTERACTION_ROLES:
            for pat in deck._ROLE_COMPILED_MAP[label]:
                assert pat in deck._INT_CUE_PATS, f"{label}: {pat.pattern}"

    def test_card_advantage_net_covers_every_precise_pattern(self):
        for pat in deck._ROLE_COMPILED_MAP["Card advantage"]:
            assert pat in deck._CA_CUE_PATS, pat.pattern


class TestRotationOverride:
    """A reprint inherits the newest printing's date, so a card reprinted into a set with
    an announced LONG Standard legality read as rotating in three years."""

    def test_foundations_uses_its_announced_window(self):
        # Genesis Wave (FDN, 2024-11-15): 2029, not 2027.
        assert deck.rotation_year("2024-11-15", set_code="FDN") == 2029
        assert deck.rotation_risk("2024-11-15", set_code="FDN") is False

    def test_ordinary_set_still_uses_release_plus_three(self):
        assert deck.rotation_year("2024-02-09", set_code="MKM") == 2027
        assert deck.rotation_year("2023-09-08", set_code="WOE") == 2026

    def test_blank_release_is_graceful(self):
        assert deck.rotation_year("") is None
        assert deck.rotation_risk("") is False

    def test_risk_is_calendar_year_based(self):
        # Rotation happens at a fall rotation, not on a card's 3rd birthday: a 2023 set
        # rotates during 2026, so it is at risk for all of 2026.
        import datetime
        y = datetime.date.today().year
        assert deck.rotation_risk(f"{y - 3}-09-01") is True
        assert deck.rotation_risk(f"{y - 1}-09-01") is False


class TestCostAsUpside:
    def test_kicker_land_bounce_flags_in_a_landfall_deck(self):
        text = ("Kicker—Return a land you control to its owner's hand. Target creature "
                "you control deals damage equal to its power to target creature.")
        assert deck.cost_upside_flags(text, {"landfall", "counters"})

    def test_same_card_is_silent_without_the_theme(self):
        text = "Kicker—Return a land you control to its owner's hand."
        assert deck.cost_upside_flags(text, {"lifegain", "flying"}) == []

    def test_leaves_play_trigger_flags_in_a_counters_deck(self):
        text = ("This creature enters with X +1/+1 counters on it. When this creature "
                "leaves the battlefield, put its counters on target creature you control.")
        assert deck.cost_upside_flags(text, {"counters"})

    def test_plain_card_never_flags(self):
        assert deck.cost_upside_flags("Flying. Vigilance.", {"counters", "landfall"}) == []


class TestCostThemes:
    """`graveyard` is a benefit only where the deck pays it off; elsewhere it's a cost."""
    CD = {
        "escape artist": {"type": "Creature", "colors": "U",
                          "text": "Escape—{2}{U}, Exile four other cards from your graveyard."},
        "vanilla": {"type": "Creature", "colors": "G", "text": "Flying."},
    }

    def test_theme_dropped_without_payoffs(self):
        cards = [(1, "Vanilla", "", "")]
        assert deck._drop_cost_themes(["graveyard", "counters"], cards, self.CD) == ["counters"]

    def test_theme_kept_with_enough_payoffs(self):
        cards = [(2, "Escape Artist", "", "")]
        assert "graveyard" in deck._drop_cost_themes(["graveyard"], cards, self.CD)

    def test_non_cost_themes_pass_through(self):
        cards = [(1, "Vanilla", "", "")]
        assert deck._drop_cost_themes(["counters", "landfall"], cards, self.CD) == \
            ["counters", "landfall"]


class TestSectionMismatch:
    CD = {
        "broodguard elite": {"type": "Creature", "colors": "G",
                             "text": "This creature enters with X +1/+1 counters on it."},
        "divination": {"type": "Sorcery", "colors": "U", "text": "Draw two cards."},
        "shock": {"type": "Instant", "colors": "R", "text": "Shock deals 2 damage to any target."},
    }

    def test_wrong_section_warns(self):
        lines = ["Deck", "# Card advantage", "1 Shock (M21) 159"]
        assert "Card advantage" in (deck.section_mismatch(lines, 2, "Shock", self.CD) or "")

    def test_matching_section_is_silent(self):
        lines = ["Deck", "# Card advantage", "1 Divination (M21) 56"]
        assert deck.section_mismatch(lines, 2, "Divination", self.CD) is None

    def test_ambiguous_section_is_silent(self):
        # "Counter DOUBLERS" means +1/+1 counters, not counterspells.
        lines = ["Deck", "# Counter DOUBLERS — the engine", "1 Broodguard Elite (EOE) 175"]
        assert deck.section_mismatch(lines, 2, "Broodguard Elite", self.CD) is None

    def test_no_header_is_silent(self):
        assert deck.section_mismatch(["Deck", "1 Shock (M21) 159"], 1, "Shock", self.CD) is None

    def test_unclassified_card_gets_the_softer_wording(self):
        lines = ["Deck", "# Card advantage", "1 Broodguard Elite (EOE) 175"]
        msg = deck.section_mismatch(lines, 2, "Broodguard Elite", self.CD) or ""
        assert "verify" in msg  # a prompt, not an assertion that it's misfiled


class TestProtectionAxis:
    def test_real_protection_detected(self):
        for text in ("Enchanted creature has ward {2}.",
                     "Target creature you control gains hexproof until end of turn.",
                     "It gains indestructible until end of turn.",
                     "Creatures you control have protection from red."):
            assert deck.protection_effects(text), text

    def test_combat_pump_is_not_protection(self):
        # The broad "Protection / trick" role counts these; this axis must not.
        for text in ("Target creature gets +2/+2 until end of turn.",
                     "Double target creature's power and toughness until end of turn.",
                     "Target creature you control gets +0/+10 until end of turn."):
            assert not deck.protection_effects(text), text

    def test_cant_be_regenerated_boilerplate_is_not_protection(self):
        # "It can't be regenerated" rides along on removal spells, so keying on the word
        # would score half the format's removal as protection.
        assert not deck.protection_effects(
            "Destroy target creature. It can't be regenerated.")

    def test_role_tally_reports_protection_quantity_weighted(self):
        cd = {"snakeskin veil": {"type": "Instant", "colors": "G",
                                 "text": "Put a +1/+1 counter on target creature you "
                                         "control. It gains hexproof until end of turn."},
              "shock": {"type": "Instant", "text": "Shock deals 2 damage to any target.",
                        "colors": "R"}}
        t = deck.role_tally([(2, "Snakeskin Veil", "", ""), (1, "Shock", "", "")], cd)
        assert t["protection"] == 2
        assert t["interaction"] == 1


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

    def test_sim_specific_signature_rescues_generic(self):
        assert not deck._sim_specific("counters", frozenset())          # generic by default
        assert deck._sim_specific("counters", frozenset({"counters"}))  # rescued as a spine
        assert deck._sim_specific("Ninja", frozenset())                 # specific always

    def test_keep_rescues_generic_in_cosine(self):
        # Rescuing a shared generic SPINE (a counters-doubler deck) makes the pair read as
        # MORE similar than treating counters as damped value overlap.
        a, b = {"counters": 10, "Ninja": 1}, {"counters": 10, "Cat": 1}
        assert deck._theme_cosine(a, b, keep=frozenset({"counters"})) > deck._theme_cosine(a, b)

    def test_strong_signature_needs_multiple_protected_cards(self):
        # A theme is a real spine only if >=2 protected cards carry it — a lone protected
        # bomb's incidental tag (card draw) must NOT be rescued.
        meta = {"protect": "A; B; C"}
        cards = [(1, "A", "", ""), (1, "B", "", ""), (1, "C", "", "")]
        cardmeta = {"a": {"synergies": ["counters", "flying"]},
                    "b": {"synergies": ["counters", "haste"]},
                    "c": {"synergies": ["card draw"]}}
        sig = deck._strong_signature_themes(meta, cards, cardmeta)
        assert "counters" in sig and "card draw" not in sig and "flying" not in sig


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


class TestSyncPaste:
    """The pure pieces behind `deck.py sync` — splitting a multi-deck paste, matching a
    block to its stored deck, and rewriting a deck file's lines to a target list."""

    def _ms(self, **kw):
        return {k.lower(): (k, v) for k, v in kw.items()}

    def _d(self, i):
        return {"id": i, "name": f"deck{i}", "path": ""}

    def test_split_multi_deck_paste(self):
        segs = deck.split_paste("Deck\n1 A\n2 B\n\nDeck\n3 C\n")
        assert len(segs) == 2
        assert [l for l in segs[0] if l.strip()] == ["1 A", "2 B"]

    def test_split_without_a_deck_marker(self):
        # A bare paste (no "Deck" header) is still one block.
        assert len(deck.split_paste("1 A\n2 B\n")) == 1

    def test_split_ignores_empty_blocks(self):
        assert deck.split_paste("Deck\n\nDeck\n1 A\n") == [["1 A"]]

    def test_diff_direction(self):
        added, removed, diffs = deck._ms_diff(self._ms(A=3, B=1), self._ms(A=1, C=2))
        assert (added, removed) == (2 + 1, 2)          # +2 A, +1 B, -2 C
        assert ("+", 2, "A") in diffs and ("-", 2, "C") in diffs

    def test_matches_closest_deck(self):
        m = deck.match_paste(self._ms(A=4, B=4, C=4),
                             [(self._d("1"), self._ms(A=4, B=4, C=4)),
                              (self._d("2"), self._ms(A=4, B=4, Z=4))])
        assert m["deck"]["id"] == "1" and m["sync"] is True

    def test_unrelated_paste_is_unmatched(self):
        m = deck.match_paste(self._ms(Q=4, R=4, S=4, T=4),
                             [(self._d("1"), self._ms(A=4, B=4, C=4))])
        assert m.get("unmatched") is True

    def test_low_confidence_between_siblings(self):
        m = deck.match_paste(self._ms(A=4, B=4, C=4, D=4, E=1),
                             [(self._d("1"), self._ms(A=4, B=4, C=4, D=4, E=2)),
                              (self._d("1a"), self._ms(A=4, B=4, C=4, D=4, E=1, F=1))])
        assert m["lowconf"] is True and m["runner_up"] is not None

    def test_clear_winner_is_not_flagged(self):
        m = deck.match_paste(self._ms(A=4, B=4, C=4),
                             [(self._d("1"), self._ms(A=4, B=4, C=4)),
                              (self._d("2"), self._ms(X=4, Y=4, Z=4))])
        assert m["lowconf"] is False

    def test_reconcile_preserves_structure_and_applies_target(self):
        lines = ["#: name: T", "", "# Creatures", "4 Foo (SET) 1", "1 Bar (SET) 2",
                 "# Lands", "20 Island", "#~ -Bar | +Baz | flex note"]
        out = deck.reconcile_lines(lines, self._ms(Foo=2, Baz=1, Island=20),
                                   {"baz": ("Baz", "NEW", "9")})
        assert "#: name: T" in out and "# Creatures" in out and "# Lands" in out
        assert "#~ -Bar | +Baz | flex note" in out          # comments/flex survive
        assert "4 Foo (SET) 1" not in out and "2 Foo (SET) 1" in out   # qty rewritten
        assert not any(l.startswith("1 Bar") for l in out)  # dropped card
        assert "1 Baz (NEW) 9" in out                       # new card, resolved printing

    def test_reconcile_new_card_without_a_known_printing(self):
        out = deck.reconcile_lines(["1 Foo (S) 1"], self._ms(Foo=1, Mystery=2), {})
        assert "2 Mystery" in out                            # bare line still parses

    def test_reconcile_totals_match_the_target(self):
        target = self._ms(Foo=3, Island=20)
        out = deck.reconcile_lines(["# c", "1 Foo (S) 1", "24 Island"], target, {})
        parsed = [deck.LINE_RE.match(l) for l in out if deck._card_line_name(l)]
        assert sum(int(m.group(1)) for m in parsed) == sum(q for _d, q in target.values())


class TestPowerThresholdFlags:
    """A "power 4 or greater" payoff reads unconditional to a synergy model but only
    fires off bodies that meet the bar on their PRINTED stats — measurable only since
    card-pool.csv started carrying Power/Toughness."""
    CD = {
        "garruk's uprising": {"name": "Garruk's Uprising", "type": "Enchantment",
                              "text": "Whenever a creature you control with power 4 or "
                                      "greater enters, draw a card.",
                              "power": "", "toughness": ""},
        "x hydra": {"name": "X Hydra", "type": "Creature — Hydra",
                    "text": "This creature enters with X +1/+1 counters on it.",
                    "power": "0", "toughness": "0"},
        "big beater": {"name": "Big Beater", "type": "Creature — Beast",
                       "text": "Trample.", "power": "6", "toughness": "6"},
        "star creature": {"name": "Star Creature", "type": "Creature — Avatar",
                          "text": "Power equal to cards in your graveyard.",
                          "power": "*", "toughness": "*"},
    }

    def test_flags_a_payoff_the_creatures_dont_support(self):
        cards = [(1, "Garruk's Uprising", "", ""), (8, "X Hydra", "", "")]
        flags = deck.power_threshold_flags(cards, self.CD)
        assert flags == [("Garruk's Uprising", "power", 4, 0, 8)]

    def test_silent_when_the_deck_supports_it(self):
        cards = [(1, "Garruk's Uprising", "", ""), (8, "Big Beater", "", "")]
        assert deck.power_threshold_flags(cards, self.CD) == []

    def test_star_power_counts_as_not_qualifying(self):
        # `*` is unknowable from printed stats; guessing would invent a fact.
        cards = [(1, "Garruk's Uprising", "", ""), (8, "Star Creature", "", "")]
        assert deck.power_threshold_flags(cards, self.CD)[0][3] == 0

    def test_no_creatures_is_not_an_error(self):
        assert deck.power_threshold_flags([(1, "Garruk's Uprising", "", "")], self.CD) == []


class TestRationaleStaleness:
    """The audit must flag a stale CLAIM without flagging accurate HISTORY — a rationale
    legitimately documents the change that produced the current list."""

    def _deck(self, tmp_path, tier_lines, cards=("1 Shock (M21) 159",)):
        p = tmp_path / "d.txt"
        p.write_text("\n".join([f"#: tier: {ln}" for ln in tier_lines]
                                + ["#: colors: R", "", "Deck", *cards]) + "\n")
        return {"id": "t", "name": "t", "path": str(p)}

    def test_flags_a_cut_card_the_argument_leans_on(self, tmp_path):
        d = self._deck(tmp_path, ["B — held to B because Lightning Bolt is the only answer."])
        cards, _figs = deck.rationale_staleness(d)
        assert "Lightning Bolt" in [c for c, _h in cards]

    def test_history_citation_is_suppressed(self, tmp_path):
        d = self._deck(tmp_path, ["B — re-graded after Lightning Bolt was cut for Shock."])
        cards, _figs = deck.rationale_staleness(d)
        assert cards == []

    def test_lowercase_common_noun_is_not_a_citation(self, tmp_path):
        # "Counterspell" is a real card name; the lowercase word is not a reference.
        d = self._deck(tmp_path, ["B — light on counterspell effects."])
        cards, _figs = deck.rationale_staleness(d)
        assert cards == []

    def test_historical_figure_is_suppressed(self, tmp_path):
        # "took interaction 1->4" describes a past change, not the current state.
        d = self._deck(tmp_path, ["A — the package took interaction 1 to 4."])
        _cards, figs = deck.rationale_staleness(d)
        assert figs == []
