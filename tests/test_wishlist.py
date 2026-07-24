"""Unit tests for pure scoring helpers in scripts/wishlist.py."""
import math

import wishlist


class TestReuseBonus:
    def test_zero_for_zero_or_one_home(self):
        assert wishlist._reuse_bonus(0) == 0
        assert wishlist._reuse_bonus(1) == 0

    def test_non_decreasing(self):
        seq = [wishlist._reuse_bonus(k) for k in (1, 2, 3, 4, 8, 20)]
        assert all(a <= b for a, b in zip(seq, seq[1:]))

    def test_capped(self):
        assert wishlist._reuse_bonus(8) == wishlist._reuse_bonus(20)
        assert wishlist._reuse_bonus(20) <= 2.0

    def test_non_numeric_is_zero(self):
        assert wishlist._reuse_bonus("x") == 0.0
        assert wishlist._reuse_bonus(None) == 0.0


class TestRankScoresPowerParsing:
    """The Power cell parsing inside _rank_scores (A10/F9): a non-finite or non-numeric
    Power must be flagged and scored 0.0, never silently poison `combined`."""

    def _score(self, power):
        row = {"Card Name": "T", "Rarity": "Rare", "Color(s)": "",
               "Synergies": "etb; tokens", "Target": "", "Power": power}
        return wishlist._rank_scores([row])[0]

    def test_valid_power(self):
        s = self._score("7")
        assert s["power"] == 7.0 and not s["bad_power"]
        assert math.isfinite(s["combined"])

    def test_nan_flagged_and_finite_combined(self):
        s = self._score("nan")
        assert s["power"] == 0.0 and s["bad_power"] is True
        assert math.isfinite(s["combined"])

    def test_inf_flagged(self):
        s = self._score("inf")
        assert s["power"] == 0.0 and s["bad_power"] is True
        assert math.isfinite(s["combined"])

    def test_garbage_flagged(self):
        s = self._score("~9")
        assert s["power"] == 0.0 and s["bad_power"] is True


class TestPipsCastable:
    """Hybrid-aware castability behind the wishlist target audit (Sun-Spider fix)."""

    def test_hybrid_castable_in_one_color(self):
        # {3}{W/U} -> strict {}, hybrid [{'W','U'}] -> castable in a W/B deck (pay W).
        assert wishlist._pips_castable({}, [frozenset({"W", "U"})], {"W", "B"})

    def test_strict_offcolor_not_castable(self):
        # {3}{U} -> strict {'U':1} -> NOT castable in a W/B deck.
        assert not wishlist._pips_castable({"U": 1}, [], {"W", "B"})

    def test_hybrid_needs_at_least_one_color(self):
        # {U/R} in a mono-W deck: neither color available -> not castable.
        assert not wishlist._pips_castable({}, [frozenset({"U", "R"})], {"W"})

    def test_strict_oncolor_castable(self):
        assert wishlist._pips_castable({"W": 2, "B": 1}, [], {"W", "B"})

    def test_no_pips_castable_anywhere(self):
        assert wishlist._pips_castable({}, [], {"W"})


class TestSeedPowerBonuses:
    """The two bounded seed bonuses that fixed the Meteor-Sword under-read."""

    def _p(self, rarity, ty, text):
        return wishlist._seed_power({"Rarity": rarity, "Type": ty, "Card Text": text})

    def test_flexible_removal_beats_creature_only(self):
        flex = self._p("Uncommon", "Instant", "Destroy target permanent.")
        crea = self._p("Uncommon", "Instant", "Destroy target creature.")
        assert flex > crea

    def test_removal_on_a_permanent_is_a_two_for_one(self):
        # Same removal, but stapled to an equipment (stays on board) -> higher.
        equip = self._p("Uncommon", "Artifact — Equipment",
                        "When this Equipment enters, destroy target permanent. "
                        "Equipped creature gets +3/+3.")
        spell = self._p("Uncommon", "Sorcery", "Destroy target permanent.")
        assert equip > spell

    def test_meteor_sword_no_longer_underseeded(self):
        meteor = self._p("Uncommon", "Artifact — Equipment",
                         "When this Equipment enters, destroy target permanent. "
                         "Equipped creature gets +3/+3.")
        assert meteor >= 4.0            # was 3.0 before the fix

    def test_bonuses_stay_in_range_and_below_a_bomb(self):
        vanilla = self._p("Common", "Creature — Bear", "")
        meteor = self._p("Uncommon", "Artifact — Equipment",
                         "When this Equipment enters, destroy target permanent.")
        bomb = self._p("Mythic", "Legendary Planeswalker",
                       "Destroy target permanent. Draw two cards.")
        assert 0.0 <= vanilla < meteor <= bomb <= 10.0

    def test_wildcard_letter_rarity_matches_the_word(self):
        # deck.rank_cut_candidates / deck._card_power pass load_rarities() values, which
        # are Arena wildcard LETTERS. A letter used to miss _SEED_RARITY and default to
        # 2.0, seeding every rare/mythic as an uncommon (audit F-01).
        for letter, word in (("M", "Mythic"), ("R", "Rare"),
                             ("U", "Uncommon"), ("C", "Common")):
            assert self._p(letter, "Creature — Bear", "") == self._p(word, "Creature — Bear", "")

    def test_mythic_floor_outranks_common_floor(self):
        assert self._p("M", "Creature — Bear", "") > self._p("C", "Creature — Bear", "")

    def test_unknown_rarity_falls_back_to_neutral(self):
        # '?' (rarity unresolved) and a blank cell must both take the neutral default,
        # not a wrong floor.
        neutral = self._p("", "Creature — Bear", "")
        assert self._p("?", "Creature — Bear", "") == neutral
        assert self._p("Nonsense", "Creature — Bear", "") == neutral

    def test_rot_penalty_bounded(self):
        assert 0 < wishlist._ROT_PENALTY <= 2.0
