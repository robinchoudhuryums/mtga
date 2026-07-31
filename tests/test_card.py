"""Unit tests for scripts/card.py — the single-card inspector.

G-01 makes this the surface you are told to read a card from before grading or
recommending it, which puts an unusual weight on the one number a craft decision leans
on: OWNED. It read `Quantity Owned` off the FIRST matching row, but card-library.csv
holds one row per PRINTING and Arena copies are fungible across sets — so every card
owned in more than one set was under-reported (broad-scan F-03). These pin the summed
read and the DFC front-face resolution it shares with `lib.owned_qty`."""
import card


def _row(name, setc="M21", coll="1", qty="1"):
    return {"Card Name": name, "Type": "", "Card Text": "", "Color(s)": "",
            "Synergies": "", "Set Code": setc, "Collector #": coll,
            "Quantity Owned": qty}


class TestOwnedIndex:
    """`_owned_index` is the summed, name-keyed view every other tool already builds
    (`deck.load_collection`, `pool.owned_counts`, `wishlist`)."""

    def test_copies_sum_across_printings(self):
        rows = [_row("Rugged Highlands", "FDN", "265", "1"),
                _row("Rugged Highlands", "M21", "249", "2")]
        assert card._owned_index(rows)["rugged highlands"] == 3

    def test_a_single_printing_is_unchanged(self):
        assert card._owned_index([_row("Shock", qty="4")])["shock"] == 4

    def test_a_blank_quantity_is_zero_not_a_crash(self):
        rows = [_row("Shock", "M21", "1", ""), _row("Shock", "DAR", "2", "2")]
        assert card._owned_index(rows)["shock"] == 2

    def test_a_non_numeric_quantity_is_ignored(self):
        # INV-01's problem, not this tool's — it must not raise on the way past.
        assert card._owned_index([_row("Shock", qty="lots")])["shock"] == 0


class TestOwnedLookupIsDfcAware:
    """The library keys a two-faced card under its FRONT name while the pool (and so the
    name `card.py` resolves for an unowned card) uses the full `Front // Back`. Routed
    through lib.owned_qty so the fallback is shared, not re-implemented (the A3/A4/F6
    rule)."""

    def test_a_full_name_query_finds_the_front_face_row(self):
        from lib import owned_qty
        idx = card._owned_index([_row("Bruce Banner", "SPM", "39", "2")])
        assert owned_qty(idx, "Bruce Banner // The Incredible Hulk") == 2

    def test_an_unowned_card_reads_zero(self):
        from lib import owned_qty
        assert owned_qty(card._owned_index([]), "Anything") == 0


class TestOwnedPrintings:
    """The count shows its working when it comes from more than one printing — the case
    the single-row read got wrong, so a reader can see WHY the number is what it is."""

    def test_lists_every_owned_printing(self):
        rows = [_row("Rugged Highlands", "FDN", "265", "1"),
                _row("Rugged Highlands", "M21", "249", "2")]
        assert card._owned_printings(rows, "Rugged Highlands") == \
            [("FDN", "265", 1), ("M21", "249", 2)]

    def test_a_zero_or_blank_printing_is_not_listed(self):
        rows = [_row("Shock", "M21", "1", "0"), _row("Shock", "DAR", "2", ""),
                _row("Shock", "MSH", "3", "1")]
        assert card._owned_printings(rows, "Shock") == [("MSH", "3", 1)]

    def test_matches_a_dfc_by_its_front_face(self):
        rows = [_row("Bruce Banner", "SPM", "39", "1")]
        assert card._owned_printings(rows, "Bruce Banner // The Incredible Hulk") == \
            [("SPM", "39", 1)]

    def test_unowned_is_an_empty_list(self):
        assert card._owned_printings([_row("Shock", qty="0")], "Shock") == []


class TestAgreesWithTheRestOfTheToolkit:
    """The failure mode was `card.py` disagreeing with every other ownership surface
    while being the one a human reads. Assert they agree on the LIVE collection rather
    than on a fixture, since that is the disagreement that mattered."""

    def test_card_and_deck_report_the_same_owned_count(self):
        import deck
        from lib import owned_qty
        _, rows = __import__("lib").load_rows()
        idx = card._owned_index(rows)
        _, _, by_name_qty = deck.load_collection()
        multi = [n for n in by_name_qty
                 if len(card._owned_printings(rows, n)) > 1][:20]
        assert multi, "expected at least one card owned across several printings"
        for n in multi:
            assert owned_qty(idx, n) == by_name_qty[n], n
