"""Mutation tests for scripts/check_all.py — the gate runner itself (BS2-29).

Every other gate has a "watched it fail" layer (test_check_agreement.TestGateFires,
test_check_commands.TestGateFires, test_check_docs' mutation tests, and — since BS4-30 —
test_gates_fire.py for the seven that had none) because the project's standing rule is
that a check never watched failing is not a check. That claim was made HERE while being
false of seven gates, which is its own instance of the rule: this docstring asserted the
coverage rather than the coverage existing. The
runner implementing INV-01…04 was the one component exempt from its own rule: it was
exercised only by CI running it against a healthy repo, which by construction cannot
demonstrate that anything fails. BS2-14 was the concrete cost — INV-04's documented
malformed-line check simply did not exist, and nothing could notice.

Each test here BREAKS an invariant in a tmp world and asserts the corresponding
check function reports it (and stays quiet on the healthy twin).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import check_all as ca  # noqa: E402
import deck as deckmod  # noqa: E402


def _write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class TestInv02ManaCoverage:
    def _world(self, tmp_path, monkeypatch, lib_rows, mana_names):
        lib = tmp_path / "card-library.csv"
        mana = tmp_path / "card-mana.csv"
        _write(lib, "Card Name,Type,Card Text,Color(s),Synergies,Set Code,Collector #,Quantity Owned\n"
               + "".join(f"{n},,,,,M21,{i},1\n" for i, n in enumerate(lib_rows, 1)))
        _write(mana, "Card Name,Mana Cost,Mana Value,Keywords\n"
               + "".join(f"{n},{{B}},1,\n" for n in mana_names))
        monkeypatch.setattr(ca, "DEFAULT_CSV", str(lib))
        monkeypatch.setattr(ca, "MANA_CSV", str(mana))

    def test_a_missing_mana_row_is_a_hard_error_naming_the_card(self, tmp_path, monkeypatch):
        self._world(tmp_path, monkeypatch, ["Shock", "Duress"], ["Shock"])
        errs, ncards, nmiss = ca.check_mana_coverage()
        assert errs and "duress" in errs[0].lower()
        assert nmiss == 1

    def test_full_coverage_is_quiet(self, tmp_path, monkeypatch):
        self._world(tmp_path, monkeypatch, ["Shock"], ["Shock"])
        errs, _, nmiss = ca.check_mana_coverage()
        assert errs == [] and nmiss == 0

    def test_a_missing_mana_file_is_reported(self, tmp_path, monkeypatch):
        self._world(tmp_path, monkeypatch, ["Shock"], ["Shock"])
        monkeypatch.setattr(ca, "MANA_CSV", str(tmp_path / "absent.csv"))
        errs, _, _ = ca.check_mana_coverage()
        assert errs and "missing" in errs[0]


class TestInv03DerivedSchema:
    """The F-02 class: a derived file rewritten with another file's header keeps its
    name and loses everything that makes it that file."""

    def _world(self, tmp_path, monkeypatch, pool_header):
        mana = tmp_path / "card-mana.csv"
        pool = tmp_path / "card-pool.csv"
        gal = tmp_path / "gallery.html"
        _write(mana, "Card Name,Mana Cost,Mana Value,Keywords\n")
        _write(pool, pool_header + "\n")
        # A REALISTIC gallery stub. `_write(gal, "<html></html>")` encoded the old
        # existence-only rule, and BS4-27 made INV-03 check that the artifact has usable
        # content (non-trivial size + the data island every card is read from) — because
        # a truncated or half-written build passed the old test exactly as a healthy one
        # did. The stub is padded past the size floor and carries the island.
        _write(gal, '<html><body><script id="data" type="application/json">[]</script>'
                    + "<!-- " + ("x" * 1200) + " -->" + "</body></html>")
        dash = tmp_path / "dashboard.html"
        _write(dash, '<html><body><script id="data" type="application/json">[]</script>'
                     + "<!-- " + ("x" * 1200) + " -->" + "</body></html>")
        monkeypatch.setattr(ca, "MANA_CSV", str(mana))
        monkeypatch.setattr(ca, "POOL_CSV", str(pool))
        monkeypatch.setattr(ca, "GALLERY", str(gal))
        monkeypatch.setattr(ca, "DASHBOARD", str(dash))

    FULL = ("Card Name,Type,Card Text,Color(s),Synergies,Set Code,Collector #,"
            "Rarity,Legalities,Released,Power,Toughness")

    def test_a_pool_rewritten_with_the_library_header_is_hard(self, tmp_path, monkeypatch):
        self._world(tmp_path, monkeypatch,
                    "Card Name,Type,Card Text,Color(s),Synergies,Set Code,Collector #,Quantity Owned")
        errs, warns = ca.check_derived_files()
        assert errs and "Rarity" in errs[0]

    def test_a_pool_missing_only_optional_columns_warns_soft(self, tmp_path, monkeypatch):
        self._world(tmp_path, monkeypatch,
                    "Card Name,Type,Card Text,Color(s),Synergies,Set Code,Collector #,Rarity")
        errs, warns = ca.check_derived_files()
        assert errs == []
        assert warns and "Legalities" in warns[0]

    def test_a_healthy_pool_is_quiet(self, tmp_path, monkeypatch):
        self._world(tmp_path, monkeypatch, self.FULL)
        errs, warns = ca.check_derived_files()
        assert errs == [] and warns == []

    def test_a_gutted_gallery_is_hard_not_just_a_missing_one(self, tmp_path, monkeypatch):
        """BS4-27: INV-03's gallery leg tested EXISTENCE only, so a zero-byte or truncated
        artifact passed exactly as a healthy one did — the same exists-but-gutted shape the
        CSV half was hardened against in F-02, on the third derived file."""
        self._world(tmp_path, monkeypatch, self.FULL)
        _write(tmp_path / "gallery.html", "")
        errs, _ = ca.check_derived_files()
        assert any("no usable content" in e for e in errs)

    def test_a_gallery_that_lost_its_data_island_is_hard(self, tmp_path, monkeypatch):
        """Big enough to pass a size floor, but every card is read from `#data` — so
        without it the page renders empty chrome."""
        self._world(tmp_path, monkeypatch, self.FULL)
        _write(tmp_path / "gallery.html", "<html>" + ("x" * 4000) + "</html>")
        errs, _ = ca.check_derived_files()
        assert any("data island MISSING" in e for e in errs)

    def test_a_gutted_DASHBOARD_is_hard_too(self, tmp_path, monkeypatch):
        """The same BS4-27 shape, one file over. `dashboard.html` is committed, tracked
        and carries the same `#data` island, but was never added to INV-03's list — so a
        truncated one passed every gate, the staleness sweep included (it asks whether the
        page is CURRENT, never whether it is INTACT)."""
        self._world(tmp_path, monkeypatch, self.FULL)
        _write(tmp_path / "dashboard.html", "")
        errs, _ = ca.check_derived_files()
        assert any("dashboard.html" in e and "no usable content" in e for e in errs), errs

    def test_a_dashboard_that_lost_its_data_island_is_hard(self, tmp_path, monkeypatch):
        self._world(tmp_path, monkeypatch, self.FULL)
        _write(tmp_path / "dashboard.html", "<html>" + ("x" * 4000) + "</html>")
        errs, _ = ca.check_derived_files()
        assert any("dashboard.html" in e and "data island MISSING" in e for e in errs), errs

    def test_a_missing_dashboard_is_hard(self, tmp_path, monkeypatch):
        self._world(tmp_path, monkeypatch, self.FULL)
        monkeypatch.setattr(ca, "DASHBOARD", str(tmp_path / "absent.html"))
        errs, _ = ca.check_derived_files()
        assert any("dashboard.html missing" in e for e in errs), errs

    def test_a_missing_derived_file_is_hard(self, tmp_path, monkeypatch):
        self._world(tmp_path, monkeypatch, self.FULL)
        monkeypatch.setattr(ca, "POOL_CSV", str(tmp_path / "absent.csv"))
        errs, _ = ca.check_derived_files()
        assert any("card-pool.csv missing" in e for e in errs)


class TestInv04Decks:
    """The deck half, including the malformed-line channel this file's absence let
    ship without one (BS2-14)."""

    def _world(self, tmp_path, monkeypatch, body):
        p = tmp_path / "deck.txt"
        _write(p, body)
        monkeypatch.setattr(ca.deckmod, "discover_decks",
                            lambda: [{"id": "1", "name": "T", "path": str(p)}])
        monkeypatch.setattr(ca.deckmod, "load_collection", lambda: ({}, {}, {}))
        monkeypatch.setattr(ca.deckmod, "printing_problems", lambda cards: ([], []))

    def test_a_malformed_card_line_is_a_hard_error_naming_it(self, tmp_path, monkeypatch):
        self._world(tmp_path, monkeypatch, "4 Shock (M21) 159\nLightning Bolt (DMU) 137\n")
        errs, warns, info, n = ca.check_decks()
        assert any("Lightning Bolt" in e and "EXCLUDED" in e for e in errs)

    def test_a_file_with_no_parseable_cards_is_hard(self, tmp_path, monkeypatch):
        self._world(tmp_path, monkeypatch, "# only a comment\n")
        errs, _, _, _ = ca.check_decks()
        assert any("no parseable cards" in e for e in errs)

    def test_a_clean_deck_is_quiet(self, tmp_path, monkeypatch):
        self._world(tmp_path, monkeypatch, "Deck\n#: name: T\n4 Shock (M21) 159\n")
        errs, warns, info, n = ca.check_decks()
        assert errs == [] and n == 1

    def test_a_duplicate_deck_id_is_a_hard_error_naming_both_files(self, tmp_path, monkeypatch):
        # DD-6: two files CAN claim one id (two NN-* dirs sharing a number; two NNa-*.txt
        # variants in a parent) and find_deck picks one silently — every by-id command
        # then validates/edits one file while the other exists unchecked.
        a, b = tmp_path / "a.txt", tmp_path / "b.txt"
        _write(a, "4 Shock (M21) 159\n")
        _write(b, "4 Shock (M21) 159\n")
        monkeypatch.setattr(ca.deckmod, "discover_decks",
                            lambda: [{"id": "31", "name": "A", "path": str(a)},
                                     {"id": "31", "name": "B", "path": str(b)}])
        monkeypatch.setattr(ca.deckmod, "load_collection", lambda: ({}, {}, {}))
        monkeypatch.setattr(ca.deckmod, "printing_problems", lambda cards: ([], []))
        monkeypatch.setattr(ca.deckmod, "DECKS_DIR", str(tmp_path))
        errs, _, _, _ = ca.check_decks()
        assert any("duplicate deck id" in e and "a.txt" in e and "b.txt" in e for e in errs)

    def test_a_variant_shaped_top_level_directory_is_a_hard_error(self, tmp_path, monkeypatch):
        # DD-6's near-miss shape: decks/73a-posse/ created while 73a lived inside the
        # parent dir — different ids, so the duplicate check can't see it, and preflight
        # validated the OTHER file. Variants live inside the parent's directory.
        (tmp_path / "73a-posse").mkdir()
        self._world(tmp_path, monkeypatch, "4 Shock (M21) 159\n")
        monkeypatch.setattr(ca.deckmod, "DECKS_DIR", str(tmp_path))
        errs, _, _, _ = ca.check_decks()
        assert any("variant-shaped directory" in e and "73a-posse" in e for e in errs)

    def test_a_bad_set_code_is_hard_and_an_unheld_number_is_soft(self, tmp_path, monkeypatch):
        self._world(tmp_path, monkeypatch, "4 Shock (M21) 159\n")
        monkeypatch.setattr(ca.deckmod, "printing_problems",
                            lambda cards: ([("Shock", "ZZZ", "1")],
                                           [("Shock", "M21", "999", [("m21", "159")])]))
        errs, warns, _, _ = ca.check_decks()
        assert any("does not exist" in e for e in errs)
        assert any("not a printing we hold" in w for w in warns)
