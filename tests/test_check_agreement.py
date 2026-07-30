"""Pin the agreement gate (`scripts/check_agreement.py`).

The gate asserts that two functions answering the same question give the same answer —
the class of bug eleven per-model gates are structurally blind to, because a divergence
exists only BETWEEN functions and every anchor evaluates one in isolation.

These tests exist because the gate's own first draft was VACUOUS on the pair it was
written for. `_agree_role_fillers` ran green with the format filter deliberately deleted
from `owned_role_fillers` — twice — for two independent reasons:

  1. it read the DEFAULT `limit`, so it saw the cheapest ten rows rather than the
     filtered set, and the illegal card sorted below the cut; and
  2. it asked only about the INTERACTION role set, whose one illegal filler (Dovin's
     Veto) is off-color for every deck in the sampled slice — while the card the
     original bug actually offered (Deadly Dispute) is a CARD-ADVANTAGE filler.

Both were found by mutating the code and watching the check stay green, which is the
only way this class is ever found. So the tests below assert the two properties that
made it real, not just that it passes today.
"""
import check_agreement as ca
import deck
import pytest


class TestStaleRegistry:
    """A registered pair naming a function that no longer exists must FAIL, not skip.
    An entry covering nothing reads as a considered decision — the hand-kept-registry
    rot `check_patterns`' completeness check and `_INLINE_PARSE_ALLOW` exist for."""

    def test_missing_attribute_is_reported(self, monkeypatch):
        monkeypatch.setattr(ca, "REQUIRED",
                            list(ca.REQUIRED) + [("deck", "no_such_function_xyz")])
        errs = ca._stale_entries()
        assert any("no_such_function_xyz" in e for e in errs)

    def test_stale_entry_short_circuits_check(self, monkeypatch):
        monkeypatch.setattr(ca, "REQUIRED", [("deck", "definitely_not_here")])
        errs = ca.check()
        assert errs and all("definitely_not_here" in e for e in errs)

    def test_live_registry_is_current(self):
        assert ca._stale_entries() == []


class TestRoleFillerParity:
    """The pair that was vacuous twice. Both properties are asserted structurally,
    since a green run proves nothing about a check that cannot fire."""

    def test_asks_both_role_axes(self):
        """Interaction alone cannot see Deadly Dispute, the card the real bug offered."""
        src = ca._agree_role_fillers.__code__.co_consts
        flat = " ".join(str(c) for c in src)
        assert "card advantage" in flat.lower(), (
            "the role-filler pair must ask about the card-advantage axis too — with "
            "interaction alone it ran green against the deleted format filter")

    def test_lifts_the_default_limit(self):
        """Both halves sort cheapest-first then truncate; the default view is the cheap
        corner of the filtered set, not the set."""
        consts = [c for c in ca._agree_role_fillers.__code__.co_consts
                  if isinstance(c, int)]
        assert any(c >= 1000 for c in consts), (
            "the role-filler pair must lift `limit`, or an illegal card below the "
            "top-N cut is invisible to it")

    def test_reports_an_illegal_filler(self, monkeypatch):
        """Mutate the answer, not the code: a filler the deck's format forbids must be
        named. This is the assertion the two vacuous drafts could not make."""
        d = deck.roster_decks()[0]
        meta, _ = deck.parse_deck_file(d["path"])
        fmt = (meta.get("format") or "standard").strip().lower()
        # An owned filler that is legal nowhere near this deck's format.
        monkeypatch.setattr(deck, "owned_role_fillers",
                            lambda *a, **k: [(1, "Bogus Illegal Card", "B", ["x"], "")])
        monkeypatch.setattr(deck, "craft_role_fillers", lambda *a, **k: [])
        monkeypatch.setattr(deck, "load_legalities",
                            lambda: {"bogus illegal card": {"vintage"}})
        errs = []
        ca._agree_role_fillers(errs)
        assert errs, "an illegal owned filler must be reported"
        assert "Bogus Illegal Card" in errs[0]
        assert fmt in errs[0]


class TestWeakestCutPair:
    """The pair the gate was built for: `suggest-homes`' cut hint vs what `cuts` ranks
    first. They disagreed on 36 of 64 decks with every other gate green."""

    def test_roster_agrees_today(self):
        errs = []
        ca._agree_weakest_cut(errs)
        assert errs == [], errs

    def test_divergence_is_reported(self, monkeypatch):
        """Force the hint to answer differently and confirm the gate says so — a check
        never watched failing is not a check."""
        monkeypatch.setattr(deck, "_weakest_cut",
                            lambda *a, **k: "A Card That Is Not Ranked First")
        errs = []
        ca._agree_weakest_cut(errs)
        assert errs, "a disagreeing cut hint must be reported"
        assert "most-cuttable" in errs[0]


class TestSharedCutScore:
    """`cut_keep_score` is the single definition both cut rankings now read. The point
    of the extraction was that the hint stopped carrying its own formula."""

    def test_hint_matches_the_printed_ranking(self):
        d = deck.roster_decks()[0]
        meta, cards = deck.parse_deck_file(d["path"])
        hint = deck._weakest_cut(meta, cards, deck.load_card_meta(),
                                 deck.load_card_data())
        rows, _c, _p, _i = deck.rank_cut_candidates(d)
        assert hint == rows[0][1]

    def test_ties_break_on_name_like_the_ranking(self):
        """`rank_cut_candidates` sorts on (keep, name.lower()). A min-scan keeping the
        first-seen winner would resolve a tie by deck-file order instead, and disagree
        on exactly the cards that scored equal."""
        import inspect
        src = inspect.getsource(deck._weakest_cut)
        assert "n.lower()" in src and "key <" in src

    def test_qty_reaches_the_off_tribe_reason(self):
        """The off-tribe reason compares tribal support against the card's OWN copies;
        an extraction that hardcoded 1 would mis-flag every 2-of."""
        import inspect
        src = inspect.getsource(deck.cut_keep_score)
        assert "tribal <= qty" in src


@pytest.mark.parametrize("fn", ca.PAIRS)
def test_every_registered_pair_runs_clean(fn):
    errs = []
    fn(errs)
    assert errs == [], f"{fn.__name__}: {errs}"
