"""The "watched it fail" layer for the seven gates that never had one (BS4-30).

`test_check_all.py` opens by asserting that *"Every other gate has a 'watched it fail'
layer … because the project's standing rule is that a check never watched failing is not
a check."* That was true of agreement, commands, dfc, docs, patterns and roles — and NOT
true of `check_colors`, `check_rankings`, `check_suggest`, `check_engines`, `check_tier`,
`check_keywords` or `check_themes`, whose anchors were presumably watched failing once at
introduction and never since.

The gap that leaves is specific and is the one this repo keeps rediscovering: a gate can
be quietly made VACUOUS — an anchor edited to compare a value against itself, a loop that
iterates an empty list, a threshold widened until nothing can breach it — and every
symptom of that is silence, which is also the symptom of health. `check_suggest` is 728
lines and was the largest untested one.

Each test here BREAKS the model a gate guards and asserts the gate reports it, then
confirms the gate is quiet against the real repo. Mutations are applied with monkeypatch
against the imported module, so nothing on disk changes.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import check_colors      # noqa: E402
import check_engines     # noqa: E402
import check_keywords    # noqa: E402
import check_rankings    # noqa: E402
import check_suggest     # noqa: E402
import check_themes      # noqa: E402
import check_tier        # noqa: E402
import deck              # noqa: E402
import lib               # noqa: E402


class TestAllSevenAreQuietOnAHealthyRepo:
    """The baseline half. A mutation test proves a gate CAN fire; this proves the firing
    below is caused by the mutation and not by a pre-existing failure."""

    @pytest.mark.parametrize("gate", [check_colors, check_rankings, check_suggest,
                                      check_engines, check_tier])
    def test_hard_gate_is_clean(self, gate):
        assert gate.check() == [], f"{gate.__name__} is failing before any mutation"

    def test_soft_gates_are_clean(self):
        assert check_themes.check() == []
        assert check_keywords.check() == []


class TestCheckColorsFires:
    """Guards the F1/F2 traps: 'Colorless' contains an R, and a slashed gold cell must
    survive the subset test. Plus the AST scans for the naive idiom and the raw-cell
    membership test (BS-10)."""

    def test_it_catches_a_colorless_card_reading_as_red(self, monkeypatch):
        monkeypatch.setattr(check_colors, "card_colors",
                            lambda s: {"R"} if s == "Colorless" else lib.card_colors(s))
        errs = check_colors.check()
        assert any("Colorless" in e for e in errs)

    def test_it_catches_a_broken_color_filter(self, monkeypatch):
        # The BS-10 shape: `--color R` matching every Colorless card.
        monkeypatch.setattr(check_colors, "color_matches", lambda cell, needle: True)
        assert check_colors.check() != []


class TestCheckRankingsFires:
    """Guards the Doctor-Doom-class regression: a real tribe silently reading as
    'generic' after a threshold drifted."""

    def test_it_catches_a_cutoff_that_is_too_STRICT(self, monkeypatch):
        """The Doctor-Doom case itself: a real, narrowly-central theme reading generic.
        The real model is kept and only the cutoff is moved, because an EMPTY model
        returns early ("too few decks to assert a distribution") — a mutation that
        proves nothing."""
        import wishlist
        real = wishlist._theme_model()
        monkeypatch.setattr(wishlist, "_theme_model",
                            lambda: (real[0], real[1], 999.0))
        assert any("TOO STRICT" in e for e in check_rankings.check())

    def test_it_catches_a_cutoff_that_is_too_LOOSE(self, monkeypatch):
        import wishlist
        real = wishlist._theme_model()
        monkeypatch.setattr(wishlist, "_theme_model",
                            lambda: (real[0], real[1], -999.0))
        assert any("TOO LOOSE" in e for e in check_rankings.check())

    def test_it_catches_a_collapsed_power_seed(self, monkeypatch):
        import wishlist
        monkeypatch.setattr(wishlist, "_seed_power", lambda r: 0.0)
        assert check_rankings.check() != []


class TestCheckSuggestFires:
    """The largest gate (728 lines) and the one with the most to lose: it keeps the
    role-credit and curve modifiers BOUNDED so they cannot silently outrank theme fit."""

    def test_it_catches_an_unbounded_role_credit(self, monkeypatch):
        monkeypatch.setattr(deck, "_role_credit", lambda *a, **k: 10_000.0)
        assert check_suggest.check() != []

    def test_it_catches_a_saturating_curve_factor(self, monkeypatch):
        monkeypatch.setattr(deck, "_curve_gap_factor", lambda *a, **k: 10_000.0)
        assert check_suggest.check() != []


class TestCheckEnginesFires:
    """Locks the enabler/payoff classifier on canonical cards so a regex edit can't
    silently break the imbalance flag."""

    def test_it_catches_a_classifier_that_sees_nothing(self, monkeypatch):
        # `engine_roles` returns {theme: {roles}}; an empty dict is the dead-regex shape.
        monkeypatch.setattr(deck, "engine_roles", lambda text: {})
        assert check_engines.check() != []

    def test_it_catches_a_classifier_that_sees_everything(self, monkeypatch):
        """The opposite failure and the harder one to notice: a pattern so broad every
        card reads as both sides, which makes the enabler/payoff imbalance flag constant."""
        themes = {t for t in getattr(deck, "ENGINE_THEMES", {})}
        monkeypatch.setattr(deck, "engine_roles",
                            lambda text: {t: {"enabler", "payoff"} for t in themes})
        assert check_engines.check() != []


class TestCheckTierFires:
    """Guards the archetype-aware floor (#4): non-aggro decks must grade exactly as
    before, and the aggro clock may only ever RAISE a band."""

    def test_it_catches_a_floor_that_grades_everything_S(self, monkeypatch):
        monkeypatch.setattr(deck, "tier_band", lambda *a, **k: ("S", "mutated"))
        assert check_tier.check() != []

    def test_it_catches_a_floor_that_grades_everything_D(self, monkeypatch):
        monkeypatch.setattr(deck, "tier_band", lambda *a, **k: ("D", "mutated"))
        assert check_tier.check() != []


class TestCheckThemesFires:
    """The mis-tag radar. Its failure mode is under-reporting, so the mutation is a card
    whose text plays a theme it carries no tag for."""

    HEADER = ("Card Name,Type,Card Text,Color(s),Synergies,Set Code,"
              "Collector #,Quantity Owned")

    def _world(self, monkeypatch, tmp_path, rows):
        csv_path = tmp_path / "lib.csv"
        csv_path.write_text("\n".join([self.HEADER] + rows) + "\n", encoding="utf-8")
        monkeypatch.setattr(check_themes, "LIB_CSV", str(csv_path))
        return csv_path

    def test_it_reports_an_untagged_theme(self, monkeypatch, tmp_path):
        # `food` is a real cue with a real satisfying tag, so this is the gate's own model.
        self._world(monkeypatch, tmp_path,
                    ['Probe Card,Creature,"Create a Food token.",G,,TST,1,1'])
        assert [f[1] for f in check_themes.flags()] == ["food"]

    def test_a_correctly_tagged_card_is_not_flagged(self, monkeypatch, tmp_path):
        self._world(monkeypatch, tmp_path,
                    ['Probe Card,Creature,"Create a Food token.",G,food,TST,1,1'])
        assert check_themes.flags() == []

    def test_the_reported_total_is_not_the_capped_length(self, monkeypatch, tmp_path):
        """BS4-29: `flags()` caps at 40 and check_all printed that as the count, so 400
        mis-tags read as '40' — a number that cannot move."""
        self._world(monkeypatch, tmp_path,
                    [f'Probe {i},Creature,"Create a Food token.",G,,TST,{i},1'
                     for i in range(45)])
        assert len(check_themes.flags()) == 40            # the capped VIEW
        assert check_themes.flags(count_only=True) == 45  # the honest TOTAL


class TestCheckKeywordsFires:
    """The unindexed-mechanic radar, plus the baseline-delta contract added in BS4-10."""

    def test_an_unindexed_keyword_is_reported(self, monkeypatch):
        monkeypatch.setattr(check_keywords, "known_keywords", lambda: set())
        monkeypatch.setattr(check_keywords, "load_baseline", lambda: set())
        assert check_keywords.check() != []

    def test_the_baseline_suppresses_an_acknowledged_one(self, monkeypatch):
        monkeypatch.setattr(check_keywords, "known_keywords", lambda: set())
        everything = {kw for kw, _ex, _sig
                      in check_keywords.check(include_baselined=True)}
        monkeypatch.setattr(check_keywords, "load_baseline", lambda: everything)
        assert check_keywords.check() == []

    def test_baseline_delta_names_new_and_pruned(self, monkeypatch):
        monkeypatch.setattr(check_keywords, "load_baseline", lambda: {"a-stale-entry"})
        monkeypatch.setattr(check_keywords, "_signal_a",
                            lambda known, owned: {"brand-new-mechanic": "Some Card"})
        new, pruned = check_keywords.baseline_delta()
        assert new == ["brand-new-mechanic"]
        assert pruned == ["a-stale-entry"]

    def test_the_engine_cross_check_is_loud_when_ENGINE_THEMES_is_renamed(
            self, monkeypatch, capsys):
        """BS4-26: `getattr(_dk, "ENGINE_THEMES", {})` made a RENAME take the silent
        default — the loop produced no engine words, the -2 signal evaporated, and the
        `except` written to stop exactly that never fired because nothing raised."""
        monkeypatch.delattr(deck, "ENGINE_THEMES", raising=False)
        check_keywords.flavor_overreach()
        assert "ENGINE_THEMES cross-check skipped" in capsys.readouterr().err
