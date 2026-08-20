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
import check_roles       # noqa: E402
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


class TestTagRoleDisagreementSweepFires:
    """BS6-10 follow-up. The zero-role radar is ROSTER-scoped, which is why it could not
    see the removal Auras: those are cards you do not own. This sweep is the pool-scoped
    half, and it asks the one pool-wide question that is readable — where the tagger and
    the classifier disagree about the same text (K-09).

    A baselined sweep is the easiest kind of gate to make vacuous: bless the current set
    and it goes quiet forever, whether or not it still detects anything. So the mutation
    here is the real one — remove the pattern that FIXED BS6-10 and assert the card that
    found the bug comes back."""

    def test_quiet_on_the_healthy_repo(self):
        assert check_roles.check_tags() == []

    def test_it_fires_when_the_removal_aura_pattern_regresses(self, monkeypatch):
        import re
        pats = deck._ROLE_PATTERNS["Removal (spot)"]
        kept = [p for p in pats if "enchanted creature gets -" not in p]
        assert len(kept) == len(pats) - 1, "the Aura pattern moved — update this mutation"
        patched = dict(deck._ROLE_PATTERNS, **{"Removal (spot)": kept})
        monkeypatch.setattr(deck, "_ROLE_PATTERNS", patched)
        monkeypatch.setattr(deck, "_ROLE_COMPILED",
                            [(l, [re.compile(x) for x in patched[l]]) for l in deck.ROLE_ORDER])
        flagged = {n for n, _t, _x in check_roles.check_tags()}
        assert "Dead Weight" in flagged, flagged

    def test_the_keyword_path_is_excluded_by_construction(self):
        """deathtouch → removal comes from KEYWORD_THEMES, not MECHANIC_RULES, so a
        deathtouch body must never reach this sweep. That exclusion is 250 of the 388
        raw disagreements; if it ever became an allowlist it would rot."""
        import tag_synergies
        rules = check_roles._removal_text_rules()
        assert rules, "the tagger's removal text rules vanished — the sweep is vacuous"
        vanilla_deathtouch = "deathtouch"
        assert not any(check_roles._safe(p, "creature — snake", vanilla_deathtouch)
                       for p in rules)
        assert "removal" in tag_synergies.KEYWORD_THEMES["deathtouch"]

    def test_the_baseline_suppresses_an_acknowledged_one(self, monkeypatch):
        everything = {n.lower() for n, _t, _x
                      in check_roles.check_tags(include_baselined=True)}
        monkeypatch.setattr(check_roles, "load_tag_baseline", lambda: everything)
        assert check_roles.check_tags() == []


class TestDashboardFreshnessFires:
    """BS6-04. `make postedit` rebuilds the committed dashboard after every deck edit,
    and skipping it is silent: the page keeps its old numbers and check_all stays green.
    INV-03 gives gallery.html a content contract; the dashboard had none."""

    def test_the_committed_page_carries_fingerprints(self):
        """Non-vacuity, not freshness. `dashboard_staleness` returns None for a page
        built before fingerprints existed, so a committed page missing the `sources`
        key would silence the check permanently while every test still passed.

        It deliberately does NOT assert the page is CURRENT: staleness is a SOFT
        check_all warning by design (the deployed copy is rebuilt on push), and a
        pytest hard-fail the moment someone edits a deck would contradict that — the
        author would learn to skip the suite rather than run `make dashboard`."""
        import json
        import re
        import build_dashboard
        src = open(build_dashboard.OUT, encoding="utf-8").read()
        m = re.search(r'<script id="data"[^>]*>(.*?)</script>', src, re.S)
        assert m, "dashboard.html has no data island — INV-03's business, but fatal here too"
        stored = json.loads(m.group(1)).get("sources")
        assert isinstance(stored, dict) and stored, "no source fingerprints — check is inert"
        assert any(k.endswith(".txt") for k in stored), "deck files are not fingerprinted"
        assert all(k in stored for k in build_dashboard._SOURCES)

    def test_it_fires_when_a_source_changes(self, tmp_path, monkeypatch):
        """CONTENT, not mtime. The first version of this test touched a deck file's
        mtime, which is what the first version of the CHECK read — and mtime is
        invented by `git checkout`, so the check reported every fresh clone as
        permanently stale and failed CI. Mutating bytes is the real trigger."""
        import json
        import build_dashboard
        monkeypatch.setattr(build_dashboard, "REPO_ROOT", str(tmp_path))
        (tmp_path / "decks" / "7-scratch").mkdir(parents=True)
        deckf = tmp_path / "decks" / "7-scratch" / "deck.txt"
        deckf.write_text("1 Island (FDN) 1\n", encoding="utf-8")
        (tmp_path / "card-library.csv").write_text("Card Name\n", encoding="utf-8")

        page = tmp_path / "dashboard.html"

        def _write_page():
            payload = json.dumps({"generated": "2026-01-01 00:00",
                                  "sources": build_dashboard.source_fingerprints()})
            page.write_text(f'<script id="data" type="application/json">{payload}</script>',
                            encoding="utf-8")

        _write_page()
        assert build_dashboard.dashboard_staleness(str(page)) is None

        # Same length, different bytes — so this cannot pass on a size comparison either.
        deckf.write_text("1 Forest (FDN) 2\n", encoding="utf-8")
        res = build_dashboard.dashboard_staleness(str(page))
        assert res is not None
        assert res[0] == 1 and res[1].endswith(".txt")

        # And a NEW source file counts as a change, not just an edited one.
        _write_page()
        (tmp_path / "decks" / "8-scratch").mkdir()
        (tmp_path / "decks" / "8-scratch" / "deck.txt").write_text("1 Swamp (FDN) 3\n",
                                                                  encoding="utf-8")
        assert build_dashboard.dashboard_staleness(str(page))[0] == 1

    def test_mtime_alone_is_not_staleness(self, tmp_path, monkeypatch):
        """The regression pin for the CI failure this class caused: rewriting a source
        with IDENTICAL bytes moves its mtime and must stay quiet."""
        import json
        import os
        import time
        import build_dashboard
        monkeypatch.setattr(build_dashboard, "REPO_ROOT", str(tmp_path))
        (tmp_path / "decks" / "7-scratch").mkdir(parents=True)
        deckf = tmp_path / "decks" / "7-scratch" / "deck.txt"
        deckf.write_text("1 Island (FDN) 1\n", encoding="utf-8")
        page = tmp_path / "dashboard.html"
        payload = json.dumps({"generated": "2026-01-01 00:00",
                              "sources": build_dashboard.source_fingerprints()})
        page.write_text(f'<script id="data" type="application/json">{payload}</script>',
                        encoding="utf-8")
        os.utime(deckf, (time.time() + 7200, time.time() + 7200))
        assert build_dashboard.dashboard_staleness(str(page)) is None

    def test_a_missing_or_unstamped_page_is_not_reported_as_stale(self, tmp_path):
        """Absence is not staleness — a missing page is INV-03's business for the
        gallery and nobody's for this one, and reporting it here would be a second,
        disagreeing answer to 'does the artifact exist'."""
        import build_dashboard
        assert build_dashboard.dashboard_staleness(str(tmp_path / "nope.html")) is None
        junk = tmp_path / "junk.html"
        junk.write_text("<html>no data island</html>", encoding="utf-8")
        assert build_dashboard.dashboard_staleness(str(junk)) is None
