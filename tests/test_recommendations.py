"""Unit tests for the recommendation feedback ledger.

`swap --apply` is the only place a human's real add/cut decision is observable, and
nothing recorded it — so every ranking model in this repo has been graded on argument
and anchor tests, never against a decision anyone actually made. That is the gap
CLAUDE.md records for the `Decks` column: it read as working right up until someone
measured it.

Two things these tests exist to protect. First that the ledger is MEASUREMENT ONLY —
the scoring terms are bounded and anchored by check_suggest precisely so they can't
silently reorder a tuned deck, and a feedback loop that quietly re-weighted them would
defeat that by construction. Second that recording can never cost a swap: telemetry that
can fail the edit it observes is worse than no telemetry."""
import csv
import os

import deck


def _row(**kw):
    r = {c: "" for c in deck.RECS_HEADER}
    r.update({"Date": "2026-07-28", "Deck": "21", "Source": "swap",
              "Cut": "A Card", "Add": "B Card", "Cut Protected": "no"})
    r.update(kw)
    return r


class TestPercentile:
    """0.0 = the model's top cut candidate, 1.0 = the card it most wanted kept."""

    def test_the_top_cut_candidate_reads_zero(self):
        assert deck._rec_percentile(_row(**{"Cut Rank": 1, "Cut Of": 36})) == 0.0

    def test_the_strongest_keep_reads_one(self):
        assert deck._rec_percentile(_row(**{"Cut Rank": 36, "Cut Of": 36})) == 1.0

    def test_the_middle_reads_a_half(self):
        assert deck._rec_percentile(_row(**{"Cut Rank": 6, "Cut Of": 11})) == 0.5

    def test_an_unrankable_row_reads_none(self):
        """A protected card is excluded from the cut ranking, so it has no position —
        None, never a silent 0 that would read as 'the model agreed'."""
        for bad in ({}, {"Cut Rank": "", "Cut Of": 36}, {"Cut Rank": 1, "Cut Of": ""},
                    {"Cut Rank": "x", "Cut Of": "y"}, {"Cut Rank": 1, "Cut Of": 1}):
            assert deck._rec_percentile(_row(**bad)) is None


class TestSummary:
    def test_a_cut_the_model_wanted_kept_is_a_disagreement(self):
        rows = [_row(**{"Cut Rank": 30, "Cut Of": 36})]
        n, agreed, dis, median, _ = deck.recommendation_summary(rows)
        assert (n, agreed, len(dis)) == (1, 0, 1)

    def test_a_cut_the_model_ranked_weakest_is_agreement(self):
        rows = [_row(**{"Cut Rank": 1, "Cut Of": 36})]
        n, agreed, dis, median, _ = deck.recommendation_summary(rows)
        assert (n, agreed, dis) == (1, 1, [])

    def test_disagreements_sort_worst_first(self):
        """The point of the report is to put the model's biggest miss at the top."""
        rows = [_row(Cut="mild", **{"Cut Rank": 21, "Cut Of": 40}),
                _row(Cut="worst", **{"Cut Rank": 40, "Cut Of": 40}),
                _row(Cut="mid", **{"Cut Rank": 30, "Cut Of": 40})]
        _, _, dis, _, _ = deck.recommendation_summary(rows)
        assert [r["Cut"] for r in dis] == ["worst", "mid", "mild"]

    def test_unrankable_rows_are_excluded_from_n_not_counted_as_agreement(self):
        """Counting an unmeasurable row as agreement is how a metric saturates into
        meaninglessness — the failure mode CLAUDE.md records for the `Decks` column."""
        rows = [_row(**{"Cut Rank": 1, "Cut Of": 36}), _row()]
        n, agreed, _, _, _ = deck.recommendation_summary(rows)
        assert (n, agreed) == (1, 1)

    def test_the_median_is_the_middle_position(self):
        rows = [_row(**{"Cut Rank": r, "Cut Of": 11}) for r in (1, 6, 11)]
        _, _, _, median, _ = deck.recommendation_summary(rows)
        assert median == 0.5

    def test_an_even_count_averages_the_two_middles(self):
        rows = [_row(**{"Cut Rank": r, "Cut Of": 11}) for r in (1, 3, 9, 11)]
        _, _, _, median, _ = deck.recommendation_summary(rows)
        assert median == 0.5

    def test_unsurfaced_adds_are_collected(self):
        rows = [_row(**{"Add Surfaced": "yes"}), _row(**{"Add Surfaced": "no"}),
                _row(**{"Add Surfaced": ""})]
        *_, unsurfaced = deck.recommendation_summary(rows)
        assert len(unsurfaced) == 1

    def test_an_empty_ledger_summarizes_cleanly(self):
        assert deck.recommendation_summary([]) == (0, 0, [], None, [])


class TestPersistence:
    def test_append_roundtrips_and_keeps_its_own_header(self, tmp_path):
        """Its own DictWriter on its own fieldnames — never lib.write_rows, which emits
        the canonical 8 LIBRARY columns and would rewrite this file with the wrong
        header (audit F-02)."""
        p = str(tmp_path / "recs.csv")
        assert deck.append_recommendation(_row(Cut="one"), p) == 1
        assert deck.append_recommendation(_row(Cut="two"), p) == 2
        back = deck.load_recommendations(p)
        assert [r["Cut"] for r in back] == ["one", "two"]
        with open(p, newline="", encoding="utf-8") as fh:
            assert next(csv.reader(fh)) == deck.RECS_HEADER

    def test_a_missing_ledger_reads_as_empty(self, tmp_path):
        assert deck.load_recommendations(str(tmp_path / "nope.csv")) == []

    def test_the_path_resolves_the_global_at_call_time(self, tmp_path, monkeypatch):
        """A `path=RECS_CSV` default argument would bind the real file at import time and
        keep writing there even after a caller repoints the global — the stale-path bug
        `_file_memo` documents, in the one place a test would not notice."""
        p = str(tmp_path / "repointed.csv")
        monkeypatch.setattr(deck, "RECS_CSV", p)
        deck.append_recommendation(_row())
        assert os.path.exists(p)
        assert len(deck.load_recommendations()) == 1

    def test_a_card_name_with_a_comma_survives_the_roundtrip(self, tmp_path):
        """Card names contain commas — the reason `#: protect:` is semicolon-separated."""
        p = str(tmp_path / "recs.csv")
        deck.append_recommendation(_row(Cut="Pizza Face, Gastromancer"), p)
        assert deck.load_recommendations(p)[0]["Cut"] == "Pizza Face, Gastromancer"


class TestScoringAgainstARealDeck:
    """Against the live roster, so the wiring is exercised end to end. Anchor 13 in
    check_suggest exists because pure-function anchors cannot see WIRING — a model
    correct in every part can still be handed the wrong shape."""

    def _deck(self):
        return deck.find_deck("21")

    def test_the_weakest_card_records_as_rank_one(self):
        d = self._deck()
        rows, *_ = deck.rank_cut_candidates(d)
        r = deck.recommendation_row(d, rows[0][1], "Some Add", "swap")
        assert r["Cut Rank"] == 1 and r["Cut Of"] == len(rows)
        assert r["Cut Protected"] == "no"

    def test_the_strongest_card_records_as_the_last_rank(self):
        d = self._deck()
        rows, *_ = deck.rank_cut_candidates(d)
        r = deck.recommendation_row(d, rows[-1][1], "Some Add", "swap")
        assert r["Cut Rank"] == len(rows)
        assert deck._rec_percentile(r) == 1.0

    def test_a_top_suggestion_records_as_surfaced(self):
        d = self._deck()
        picks = deck.suggest_scored(d, limit=0)["picks"]
        r = deck.recommendation_row(d, "Anything", picks[0]["name"], "swap")
        assert r["Add Surfaced"] == "yes" and r["Add Rank"] == 1

    def test_a_pick_below_the_display_window_is_not_surfaced(self):
        """"Surfaced" must mean "a human running the default command would have SEEN
        it", not "it appears somewhere in 2,500 scored picks"."""
        d = self._deck()
        picks = deck.suggest_scored(d, limit=0)["picks"]
        deep = picks[deck._RECS_SUGGEST_WINDOW + 5]["name"]
        r = deck.recommendation_row(d, "Anything", deep, "swap")
        assert r["Add Surfaced"] == "no"
        assert int(r["Add Rank"]) > deck._RECS_SUGGEST_WINDOW

    def test_every_column_is_a_declared_column(self):
        d = self._deck()
        r = deck.recommendation_row(d, "Anything", "Anything Else", "swap")
        assert set(r) == set(deck.RECS_HEADER)

    def test_the_source_is_recorded(self):
        d = self._deck()
        assert deck.recommendation_row(d, "x", "y", "flex")["Source"] == "flex"


class TestTelemetryNeverCostsASwap:
    """A swap must not fail because scoring it did. This is the whole reason both model
    calls sit in their own try/except rather than one shared block."""

    def test_a_broken_cut_model_still_yields_the_add_side(self, monkeypatch):
        d = deck.find_deck("21")
        monkeypatch.setattr(deck, "rank_cut_candidates",
                            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
        r = deck.recommendation_row(d, "x", "y", "swap")
        assert r is not None and r["Cut Rank"] == "" and r["Add Of"] != ""

    def test_a_broken_suggest_model_still_yields_the_cut_side(self, monkeypatch):
        d = deck.find_deck("21")
        monkeypatch.setattr(deck, "suggest_scored",
                            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
        rows, *_ = deck.rank_cut_candidates(d)
        r = deck.recommendation_row(d, rows[0][1], "y", "swap")
        assert r is not None and r["Cut Rank"] == 1 and r["Add Surfaced"] == ""

    def test_both_broken_yields_none_rather_than_an_empty_row(self, monkeypatch):
        """An all-blank row would pad the ledger with rows that measure nothing while
        looking like data — the same objection as a 50%-accurate match record."""
        d = deck.find_deck("21")
        for name in ("rank_cut_candidates", "suggest_scored"):
            monkeypatch.setattr(deck, name,
                                lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
        assert deck.recommendation_row(d, "x", "y", "swap") is None


class TestItIsReportOnly:
    """The ledger must never become an input to a score. The scoring terms are bounded
    and anchored by check_suggest so they can't silently reorder a tuned deck; a
    feedback loop that re-weighted them would defeat that by construction, and it would
    do so invisibly, since every anchor would still pass on the pure functions."""

    def test_the_ranking_models_do_not_read_the_ledger(self, tmp_path, monkeypatch):
        d = deck.find_deck("21")
        before = [(r[0], r[1]) for r in deck.rank_cut_candidates(d)[0]]
        before_picks = [p["name"] for p in deck.suggest_scored(d, limit=0)["picks"][:25]]

        p = str(tmp_path / "recs.csv")
        monkeypatch.setattr(deck, "RECS_CSV", p)
        for r in deck.rank_cut_candidates(d)[0][:10]:
            deck.append_recommendation(_row(Cut=r[1], **{"Cut Rank": 1, "Cut Of": 36}))
        assert len(deck.load_recommendations()) == 10

        after = [(r[0], r[1]) for r in deck.rank_cut_candidates(d)[0]]
        after_picks = [p["name"] for p in deck.suggest_scored(d, limit=0)["picks"][:25]]
        assert after == before
        assert after_picks == before_picks

    def test_no_scoring_function_references_the_ledger(self):
        """Structural backstop: the read paths are named, so nothing in the scoring
        stack may call them. A future edit that wires feedback into a score has to
        delete this test, which is the point — it makes the decision visible."""
        import inspect
        for fn in (deck.rank_cut_candidates, deck.suggest_scored,
                   deck.fit_strength, deck.deck_quality_vector, deck.tier_band):
            src = inspect.getsource(fn)
            assert "load_recommendations" not in src, fn.__name__
            assert "RECS_CSV" not in src, fn.__name__


class TestReportOutput:
    def test_an_empty_ledger_says_how_rows_accrue(self, capsys, tmp_path, monkeypatch):
        monkeypatch.setattr(deck, "RECS_CSV", str(tmp_path / "none.csv"))
        deck.cmd_feedback(type("A", (), {"id": None})())
        out = capsys.readouterr().out
        assert "swap --apply" in out

    def test_a_small_sample_prints_no_rate(self, capsys, tmp_path, monkeypatch):
        p = str(tmp_path / "recs.csv")
        monkeypatch.setattr(deck, "RECS_CSV", p)
        deck.append_recommendation(_row(**{"Cut Rank": 1, "Cut Of": 36}))
        deck.cmd_feedback(type("A", (), {"id": None})())
        out = capsys.readouterr().out
        assert "too few to summarize" in out and "Agreement:" not in out

    def test_a_large_sample_prints_a_rate_with_the_bias_caveat(self, capsys, tmp_path,
                                                              monkeypatch):
        p = str(tmp_path / "recs.csv")
        monkeypatch.setattr(deck, "RECS_CSV", p)
        for i in range(deck._RECS_MIN_SAMPLE):
            deck.append_recommendation(_row(**{"Cut Rank": 1 + i % 3, "Cut Of": 36}))
        deck.cmd_feedback(type("A", (), {"id": None})())
        out = capsys.readouterr().out
        assert "Agreement:" in out
        # The caveat is not optional garnish: without it a high agreement rate reads as
        # validation when it partly measures the shortlist's own influence.
        assert "INFLUENCE" in out

    def test_it_leads_with_the_disagreements(self, capsys, tmp_path, monkeypatch):
        p = str(tmp_path / "recs.csv")
        monkeypatch.setattr(deck, "RECS_CSV", p)
        deck.append_recommendation(_row(Cut="Kept Card", **{"Cut Rank": 36, "Cut Of": 36}))
        deck.append_recommendation(_row(Cut="Weak Card", **{"Cut Rank": 1, "Cut Of": 36}))
        deck.cmd_feedback(type("A", (), {"id": None})())
        out = capsys.readouterr().out
        assert "Kept Card" in out
        assert out.index("wanted to KEEP") < out.index("too few to summarize")

    def test_it_filters_to_one_deck(self, capsys, tmp_path, monkeypatch):
        p = str(tmp_path / "recs.csv")
        monkeypatch.setattr(deck, "RECS_CSV", p)
        deck.append_recommendation(_row(Deck="21", Cut="In Scope",
                                        **{"Cut Rank": 36, "Cut Of": 36}))
        deck.append_recommendation(_row(Deck="30", Cut="Out Of Scope",
                                        **{"Cut Rank": 36, "Cut Of": 36}))
        deck.cmd_feedback(type("A", (), {"id": "21"})())
        out = capsys.readouterr().out
        assert "In Scope" in out and "Out Of Scope" not in out

    def test_the_report_only_disclaimer_always_prints(self, capsys, tmp_path, monkeypatch):
        p = str(tmp_path / "recs.csv")
        monkeypatch.setattr(deck, "RECS_CSV", p)
        deck.append_recommendation(_row(**{"Cut Rank": 1, "Cut Of": 36}))
        deck.cmd_feedback(type("A", (), {"id": None})())
        assert "never feeds back into a score" in capsys.readouterr().out
