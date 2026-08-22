"""Behavioral coverage for scripts/query.py and scripts/pool.py `matches()` — the
filter predicates behind every collection/pool search. Three of the seven
previously-untested scripts carried the same live bug (BS-10: `--color R`
substring-matched every Colorless card), which is the whole argument for this
file: the coverage hole and the bug map were the same map."""
import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import query  # noqa: E402
import pool  # noqa: E402


def _qargs(**kw):
    base = dict(name=None, type=None, text=None, color=None, synergy=None,
                set=None, min_owned=None, _owned_totals={})
    base.update(kw)
    return argparse.Namespace(**base)


def _pargs(**kw):
    base = dict(name=None, type=None, text=None, color=None, within=None, synergy=None,
                rarity=None, legal=None, role=None, owned=False, unowned=False,
                _roles=set())
    base.update(kw)
    return argparse.Namespace(**base)


_RED = {"Card Name": "Shock", "Type": "Instant", "Card Text": "Shock deals 2 damage.",
        "Color(s)": "R", "Synergies": "burn", "Set Code": "M21", "Quantity Owned": "2"}
_GOLD = {"Card Name": "Terminate", "Type": "Instant", "Card Text": "Destroy target creature.",
         "Color(s)": "B/R", "Synergies": "removal", "Set Code": "M21", "Quantity Owned": "1"}
_ROCK = {"Card Name": "Arcane Signet", "Type": "Artifact", "Card Text": "{T}: Add one mana of any color.",
         "Color(s)": "Colorless", "Synergies": "ramp", "Set Code": "M21", "Quantity Owned": "0",
         "Rarity": "Uncommon", "Legalities": "brawl;historic"}


class TestQueryColorFilter:
    """The BS-10 pin, on the surface a user actually types."""

    def test_color_R_excludes_colorless(self):
        assert query.matches(_RED, _qargs(color="R"))
        assert not query.matches(_ROCK, _qargs(color="R"))   # "r" in "colorless" was True

    def test_gold_card_matches_either_of_its_colors(self):
        assert query.matches(_GOLD, _qargs(color="R"))
        assert query.matches(_GOLD, _qargs(color="B"))
        assert not query.matches(_GOLD, _qargs(color="G"))

    def test_colorless_needle_matches_only_colorless(self):
        assert query.matches(_ROCK, _qargs(color="colorless"))
        assert not query.matches(_RED, _qargs(color="colorless"))


class TestQueryOtherFilters:
    def test_filters_are_anded(self):
        assert query.matches(_RED, _qargs(type="Instant", text="damage"))
        assert not query.matches(_RED, _qargs(type="Instant", text="destroy"))

    def test_min_owned(self):
        totals = {"shock": 2}
        assert query.matches(_RED, _qargs(min_owned=2, _owned_totals=totals))
        assert not query.matches(_RED, _qargs(min_owned=3, _owned_totals=totals))

    def test_min_owned_sums_across_printings(self):
        """BS2-36: copies are fungible across printings — the per-row read dropped
        Rugged Highlands (1+2 across two sets) at --min-owned 3, the exact card the
        sibling fix in card.py cites. The totals index carries the summed count."""
        totals = {"shock": 3}          # 2 in this printing + 1 in another
        assert query.matches(_RED, _qargs(min_owned=3, _owned_totals=totals))


class TestPoolFilters:
    def test_color_set_matching_mirrors_query(self):
        assert pool.matches(_GOLD, _pargs(color="R"), {})
        assert not pool.matches(_ROCK, _pargs(color="R"), {})
        assert pool.matches(_ROCK, _pargs(color="colorless"), {})

    def test_within_subset_filter_answers_the_draft_question(self):
        # DD-4: --color WRG returned five-color cards on both 2026-08-21 drafts; --within
        # is the subset complement ("castable in a deck of these colors"), colorless in.
        assert pool.matches(_GOLD, _pargs(within="BR"), {})       # B/R fits a BR deck
        assert not pool.matches(_GOLD, _pargs(within="R"), {})    # B/R does not fit mono-R
        assert pool.matches(_ROCK, _pargs(within="R"), {})        # colorless fits any deck

    def test_rarity_filter(self):
        assert pool.matches(_ROCK, _pargs(rarity="uncommon"), {})
        assert not pool.matches(_ROCK, _pargs(rarity="rare,mythic"), {})

    def test_legal_filter_reads_the_legalities_cell(self):
        assert pool.matches(_ROCK, _pargs(legal="brawl"), {})
        assert not pool.matches(_ROCK, _pargs(legal="standard"), {})

    def test_role_filter_routes_through_the_lazy_deck_proxy(self):
        """pool.classify_roles is a lazy import proxy (batch 5) — --role must
        still classify through the real deck.classify_roles."""
        rr = _pargs(role="removal", _roles={"Removal (spot)"})
        assert pool.matches(_GOLD, rr, {})
        assert not pool.matches(_RED.copy() | {"Card Text": ""}, rr, {})
