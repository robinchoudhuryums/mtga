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
        # `cut_keep_score` is the DELEGATE both cut rankings read — check_agreement
        # treats it as the single definition of the cut score — and it was absent
        # from this list, so a ledger read placed there satisfied every assertion
        # while CLAUDE.md claimed the rule was "structurally forbidden". One call
        # level deep is not structural (broad-scan Batch G).
        for fn in (deck.rank_cut_candidates, deck.cut_keep_score, deck.suggest_scored,
                   deck.fit_strength, deck.deck_quality_vector, deck.tier_band,
                   deck._weakest_cut):
            src = inspect.getsource(fn)
            assert "load_recommendations" not in src, fn.__name__
            assert "RECS_CSV" not in src, fn.__name__
            # OUTCOMES are banned from the scoring stack for a stronger reason than the
            # ledger is. `swap_outcomes` joins applied swaps to games played, and a win
            # rate is the single most tempting thing to feed back into a ranking — it
            # looks like ground truth. Wiring it in would destroy the property
            # `check_suggest` exists to hold (the scoring terms are bounded and anchored
            # so they cannot silently reorder a tuned deck) AND would make the models
            # chase an 8-match sample. Report-only, structurally (broad-scan E2).
            assert "swap_outcomes" not in src, fn.__name__
            assert "MATCHES_CSV" not in src, fn.__name__
            assert "load_match_counts" not in src, fn.__name__


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


class TestSegments:
    """The pooled agreement rate averages two regimes that differ by ~2x. A single
    number over a healthy and a broken channel reads as healthy — the saturation
    failure this project keeps re-learning (the `Decks` column at 99%, the `review`
    verdict at 22-of-63). These pin the split, not the current roster's numbers."""

    @staticmethod
    def _creatures(*names):
        """A fake injected classifier: named cards are creatures, 'Mystery ...' is
        unknown, everything else is a noncreature."""
        want = {n.lower() for n in names}
        def check(name):
            nl = (name or "").strip().lower()
            if nl.startswith("mystery"):
                return None
            return nl in want
        return check

    def test_it_splits_creature_from_noncreature(self):
        rows = ([_row(Cut="Body", **{"Cut Rank": 30, "Cut Of": 36})] * 3
                + [_row(Cut="Bolt", **{"Cut Rank": 2, "Cut Of": 36})] * 2)
        segs = deck.recommendation_segments(rows, self._creatures("Body"))
        assert segs["creature"][0] == 3 and segs["creature"][1] == 0
        assert segs["noncreature"][0] == 2 and segs["noncreature"][1] == 2

    def test_an_unknown_card_is_its_own_bucket_not_a_noncreature(self):
        """The whole point of the split is that the noncreature rate reads as
        well-calibrated. Folding a card we cannot classify into it would corrupt
        exactly that number — same rule as lib.card_power returning None for `*`."""
        rows = [_row(Cut="Mystery Thing", **{"Cut Rank": 30, "Cut Of": 36})]
        segs = deck.recommendation_segments(rows, self._creatures())
        assert segs["unknown"][0] == 1
        assert "noncreature" not in segs and "creature" not in segs

    def test_an_unrankable_row_is_excluded_entirely(self):
        """Mirrors recommendation_summary: no position means no data point, never a
        silent 0 that would read as agreement."""
        rows = [_row(Cut="Body", **{"Cut Rank": "", "Cut Of": ""})]
        assert deck.recommendation_segments(rows, self._creatures("Body")) == {}

    def test_agreed_matches_the_summary_definition(self):
        """Both answer the same question of the same rows; a disagreement is pct > 0.5,
        so the boundary case at exactly 0.5 must count as agreement in BOTH."""
        rows = [_row(Cut="Body", **{"Cut Rank": 6, "Cut Of": 11})]   # pct == 0.5
        n, agreed, dis, _median, _uns = deck.recommendation_summary(rows)
        segs = deck.recommendation_segments(rows, self._creatures("Body"))
        assert agreed == 1 and dis == []
        assert segs["creature"][1] == 1

    # A SYNTHETIC card universe, injected via load_card_data. Without it the report
    # path classifies every fixture name as `unknown` (they are not real cards), no
    # split can ever print, and the two report tests below pass vacuously — verified
    # by mutation: dropping the per-segment floor left them green.
    _UNIVERSE = {"bolt": {"type": "Instant"}, "body": {"type": "Creature — Bear"}}

    def _inject(self, monkeypatch, tmp_path):
        monkeypatch.setattr(deck, "RECS_CSV", str(tmp_path / "recs.csv"))
        monkeypatch.setattr(deck, "load_card_data", lambda *a, **k: dict(self._UNIVERSE))

    def test_a_thin_segment_prints_no_split_rate(self, capsys, tmp_path, monkeypatch):
        """Each segment is held to the same _RECS_MIN_SAMPLE floor as the pooled rate.
        Splitting a sample is exactly when that restraint gets forgotten."""
        self._inject(monkeypatch, tmp_path)
        for _ in range(deck._RECS_MIN_SAMPLE):
            deck.append_recommendation(_row(Cut="Bolt", **{"Cut Rank": 1, "Cut Of": 36}))
        deck.append_recommendation(_row(Cut="Body", **{"Cut Rank": 30, "Cut Of": 36}))
        deck.cmd_feedback(type("A", (), {"id": None})())
        out = capsys.readouterr().out
        assert "Agreement:" in out            # the pooled rate still prints
        assert "By segment" not in out        # but no split off a 1-row segment
        assert f"n={1}" in out                # and it SAYS why, rather than going quiet

    def test_two_full_segments_print_both_rates(self, capsys, tmp_path, monkeypatch):
        """The positive case the floor test cannot prove on its own."""
        self._inject(monkeypatch, tmp_path)
        for _ in range(deck._RECS_MIN_SAMPLE):
            deck.append_recommendation(_row(Cut="Bolt", **{"Cut Rank": 1, "Cut Of": 36}))
            deck.append_recommendation(_row(Cut="Body", **{"Cut Rank": 36, "Cut Of": 36}))
        deck.cmd_feedback(type("A", (), {"id": None})())
        out = capsys.readouterr().out
        assert "By segment" in out
        assert "noncreature cuts   20/20 (100%)" in out
        assert "creature cuts      0/20 (0%)" in out
        # The weak segment must carry context, not just a number — but NOT a claimed
        # CAUSE. It used to assert "no normalization for tag count", and that mechanism
        # was pre-registered, tested and refuted (BS3-04): normalizing lifts creatures
        # 53% → 68% and collapses noncreature 83% → 51%, so the tool was pointing its
        # reader at a change that would make it worse. Pin the honest shape instead —
        # the flag, and that a tested-and-rejected hypothesis is named.
        assert "coin flip" in out
        assert "rejected" in out and "2026-08" in out
        assert "no normalization for tag count" not in out

    def test_the_classifier_resolves_a_dfc_by_its_front_face(self):
        check = deck.cut_creature_classifier({"front": {"type": "Creature — Bird"}})
        assert check("Front // Back") is True
        assert check("Front") is True
        assert check("Absent Card") is None


class TestSegmentConcentration:
    """A segment rate dominated by one deck is that deck's rate wearing the segment's
    name — the same "a pooled number hides a split" failure the segmentation itself
    exists for, one level down. Testing the creature hypothesis found the creature
    segment running 0% to 100% per deck, so 45% says more about which decks were
    edited than about how `cuts` grades bodies."""

    @staticmethod
    def _creatures(*names):
        want = {n.lower() for n in names}
        return lambda name: (name or "").strip().lower() in want

    def test_it_breaks_a_segment_down_by_deck(self):
        rows = ([_row(Deck="46", Cut="Body", **{"Cut Rank": 30, "Cut Of": 36})] * 3
                + [_row(Deck="20", Cut="Body", **{"Cut Rank": 2, "Cut Of": 36})] * 3)
        got = deck.segment_concentration(rows, self._creatures("Body"),
                                         segment="creature", min_rows=3)
        assert [(d, n, ok) for d, n, ok, _s in got] == [("46", 3, 0), ("20", 3, 3)]
        assert all(abs(s - 0.5) < 1e-9 for _d, _n, _ok, s in got)

    def test_worst_agreement_sorts_first(self):
        """The reader is looking for the deck dragging the segment down."""
        rows = ([_row(Deck="a", Cut="Body", **{"Cut Rank": 2, "Cut Of": 36})] * 4
                + [_row(Deck="b", Cut="Body", **{"Cut Rank": 34, "Cut Of": 36})] * 4)
        got = deck.segment_concentration(rows, self._creatures("Body"),
                                         segment="creature", min_rows=3)
        assert got[0][0] == "b"

    def test_there_is_no_share_threshold(self):
        """The regression this function shipped with. The first draft disclosed a deck
        holding >20% of the segment, and deck 46 — the case that motivated it — sits at
        6/31 = 19.4% and did not print. A cutoff tuned until the finding you already
        believe appears is the finding smuggled into a constant, so there is no share
        parameter: a deck with enough rows for a rate always gets a line."""
        import inspect
        sig = inspect.signature(deck.segment_concentration)
        assert "threshold" not in sig.parameters
        # 1 deck at 19.4% of the segment must still be reported.
        rows = ([_row(Deck="46", Cut="Body", **{"Cut Rank": 30, "Cut Of": 36})] * 6
                + [_row(Deck=str(i), Cut="Body", **{"Cut Rank": 2, "Cut Of": 36})
                   for i in range(25)])
        got = deck.segment_concentration(rows, self._creatures("Body"),
                                         segment="creature", min_rows=3)
        assert [d for d, *_ in got] == ["46"]
        assert abs(got[0][3] - 6 / 31) < 1e-9

    def test_a_deck_too_thin_for_a_rate_is_omitted(self):
        rows = [_row(Deck="x", Cut="Body", **{"Cut Rank": 2, "Cut Of": 36})] * 2
        assert deck.segment_concentration(rows, self._creatures("Body"),
                                          segment="creature", min_rows=3) == []

    def test_it_reads_only_the_named_segment(self):
        rows = ([_row(Deck="a", Cut="Body", **{"Cut Rank": 2, "Cut Of": 36})] * 3
                + [_row(Deck="a", Cut="Bolt", **{"Cut Rank": 2, "Cut Of": 36})] * 3)
        cre = deck.segment_concentration(rows, self._creatures("Body"),
                                         segment="creature", min_rows=3)
        non = deck.segment_concentration(rows, self._creatures("Body"),
                                         segment="noncreature", min_rows=3)
        assert cre[0][1] == 3 and non[0][1] == 3


class TestSwapOutcomes:
    """E2: `recommendations.csv` records what the models said and what the human decided;
    `matches.csv` records what then happened. Both existed for a cycle with nothing
    joining them, so every ranking model here is graded on its own argument and on an
    agreement rate CLAUDE.md itself calls contaminated (you read the shortlist before
    deciding). An outcome is the only signal these models cannot influence.

    The split is per DECK at its FIRST recorded swap, deliberately coarse: a deck
    accumulates many swaps whose windows overlap almost completely, and attributing a
    result to one of four changes made the same week is a story, not a measurement."""

    def _m(self, deck_id, date, result):
        return {"Deck": deck_id, "Date": date, "Result": result}

    def test_it_splits_a_decks_record_at_the_first_swap(self):
        recs = [_row(Deck="7", Date="2026-08-10"), _row(Deck="7", Date="2026-08-12")]
        matches = [self._m("7", "2026-08-01", "W"), self._m("7", "2026-08-02", "L"),
                   self._m("7", "2026-08-11", "W")]
        (j,) = deck.swap_outcomes(recs, matches)
        assert j["deck"] == "7" and j["swaps"] == 2
        assert j["first_swap"] == "2026-08-10"      # the EARLIEST, not the last seen
        assert j["before"] == (1, 1) and j["after"] == (1, 0)

    def test_a_draw_or_an_unreadable_result_decides_nothing(self):
        recs = [_row(Deck="7", Date="2026-08-01")]
        matches = [self._m("7", "2026-08-02", "D"), self._m("7", "2026-08-03", ""),
                   self._m("7", "2026-08-04", "W")]
        (j,) = deck.swap_outcomes(recs, matches)
        assert j["after"] == (1, 0) and j["n_after"] == 1
        assert j["matches"] == 3                    # still COUNTED as games played

    def test_a_deck_with_no_matches_is_omitted_not_zeroed(self):
        """A deck with swaps and no games has NO record — printing it as 0-0 would read
        as a result rather than as an absence."""
        recs = [_row(Deck="7", Date="2026-08-01"), _row(Deck="99", Date="2026-08-01")]
        assert [j["deck"] for j in
                deck.swap_outcomes(recs, [self._m("7", "2026-08-02", "W")])] == ["7"]

    def test_an_unattributed_match_joins_to_nothing(self):
        """A match whose Deck is blank must never be folded into a deck's record — the
        blank is the parser refusing to guess a seat, and borrowing it would fabricate."""
        recs = [_row(Deck="7", Date="2026-08-01")]
        assert deck.swap_outcomes(recs, [self._m("", "2026-08-02", "W")]) == []

    def test_the_report_refuses_to_read_a_small_sample(self, capsys):
        """The whole record is ~8 attributed matches. The section must print the coverage
        and REFUSE the read, the same restraint `--report` and `feedback` already show."""
        deck._print_swap_outcomes([_row(Deck="7", Date="2026-08-01")])
        out = capsys.readouterr().out
        assert "far below" in out or "no matches.csv" in out
        assert "%" not in out, "a win rate must not appear at this sample size"
