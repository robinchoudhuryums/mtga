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
