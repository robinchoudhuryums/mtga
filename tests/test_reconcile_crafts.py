"""Behavioral coverage for scripts/reconcile_crafts.py — a canonical-file WRITER
(library + mana + wishlist) that had nothing beyond a --help smoke (broad-scan
BS-20/batch 6): a regression here ships with every gate green, the exact
"capability nothing exercises" shape G-53 documents.

The world is a tmp copy of all four CSVs with the module's path constants
repointed, so `--apply` runs are real end-to-end writes with real .bak files —
never against the repo's own data."""
import csv
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import reconcile_crafts as rc  # noqa: E402


LIB_HEADER = rc.LIB_HEADER
MANA_HEADER = ["Card Name", "Mana Cost", "Mana Value", "Keywords"]
POOL_HEADER = ["Card Name", "Type", "Card Text", "Color(s)", "Synergies",
               "Set Code", "Collector #", "Rarity"]
WISH_HEADER = ["Card Name", "Type", "Card Text", "Color(s)", "Synergies",
               "Set Code", "Collector #", "Target", "Note", "Power", "Power Source"]


def _write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in header})


def _read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture
def world(tmp_path, monkeypatch):
    """Repoint the module's four canonical paths at tmp copies."""
    paths = {"LIB": tmp_path / "card-library.csv", "MANA": tmp_path / "card-mana.csv",
             "POOL": tmp_path / "card-pool.csv", "WISH": tmp_path / "card-wishlist.csv"}
    _write_csv(paths["LIB"], LIB_HEADER,
               [{"Card Name": "Shock", "Type": "Instant", "Set Code": "M21",
                 "Collector #": "159", "Quantity Owned": "2"}])
    _write_csv(paths["MANA"], MANA_HEADER,
               [{"Card Name": "Shock", "Mana Cost": "{R}", "Mana Value": "1"}])
    _write_csv(paths["POOL"], POOL_HEADER, [
        {"Card Name": "Shock", "Type": "Instant", "Card Text": "Shock deals 2 damage to any target.",
         "Color(s)": "R", "Set Code": "M21", "Collector #": "159", "Rarity": "Common"},
        {"Card Name": "Duress", "Type": "Sorcery", "Card Text": "Target opponent reveals their hand.",
         "Color(s)": "B", "Set Code": "M21", "Collector #": "96", "Rarity": "Common"},
        # A DFC, keyed the way the pool really keys one: full `Front // Back`.
        {"Card Name": "Bruce Banner // The Incredible Hulk", "Type": "Legendary Creature — Human // Creature — Monster",
         "Card Text": "Whenever you cast a spell, transform Bruce Banner.",
         "Color(s)": "U/G", "Set Code": "MSH", "Collector #": "5", "Rarity": "Mythic"},
    ])
    _write_csv(paths["WISH"], WISH_HEADER,
               [{"Card Name": "Duress", "Type": "Sorcery", "Set Code": "M21",
                 "Collector #": "96", "Target": "52", "Power": "5", "Power Source": "hand"}])
    for attr, p in paths.items():
        monkeypatch.setattr(rc, attr, str(p))
    return paths


class TestDryRunSafety:
    def test_dry_run_writes_nothing(self, world):
        before = {k: open(p, encoding="utf-8").read() for k, p in world.items()}
        rc.reconcile(["1 Duress (M21) 96"], apply=False)
        after = {k: open(p, encoding="utf-8").read() for k, p in world.items()}
        assert before == after
        assert not [f for f in os.listdir(os.path.dirname(world["LIB"]))
                    if f.endswith(".bak")]


class TestApply:
    def test_new_card_lands_in_library_mana_and_leaves_wishlist(self, world):
        """The full contract in one pass: a reconciled craft adds the library row,
        adds a BLANK mana row (INV-02 must hold immediately, cost filled by the
        next refresh), and drops the card from the wishlist (G-10)."""
        rc.reconcile(["1 Duress (M21) 96"], apply=True)
        lib = _read_csv(world["LIB"])
        assert any(r["Card Name"] == "Duress" and r["Quantity Owned"] == "1" for r in lib)
        mana_names = {r["Card Name"] for r in _read_csv(world["MANA"])}
        assert "Duress" in mana_names                     # INV-02: every library name
        assert all(r["Card Name"] != "Duress" for r in _read_csv(world["WISH"]))
        # Hand-annotated wishlist columns for OTHER cards must survive a write —
        # here the whole wishlist emptied, so assert the file still parses.
        assert _read_csv(world["WISH"]) == []

    def test_apply_writes_bak_backups(self, world):
        rc.reconcile(["1 Duress (M21) 96"], apply=True)
        baks = [f for f in os.listdir(os.path.dirname(world["LIB"])) if f.endswith(".bak")]
        assert baks, "an --apply write must leave timestamped .bak files"

    def test_existing_card_bumps_not_duplicates(self, world):
        rc.reconcile(["3 Shock (M21) 159"], apply=True)
        rows = [r for r in _read_csv(world["LIB"]) if r["Card Name"] == "Shock"]
        assert len(rows) == 1 and rows[0]["Quantity Owned"] == "3"   # max(2, 3)

    def test_lower_line_cannot_drop_a_count(self, world):
        """Deck-dump lines are LOWER BOUNDS (G-10): owning 2, pasting 1 keeps 2."""
        rc.reconcile(["1 Shock (M21) 159"], apply=True)
        rows = [r for r in _read_csv(world["LIB"]) if r["Card Name"] == "Shock"]
        assert rows[0]["Quantity Owned"] == "2"


class TestDFCResolution:
    def test_front_name_paste_resolves_via_pool_alias(self, world):
        """BS-16's pin: an Arena export names a DFC by its FRONT face, with a
        printing the pool may not key — the front-face-aliased name index must
        still resolve it (the old fallback was dead code and the card was
        skipped as NOT FOUND)."""
        rc.reconcile(["1 Bruce Banner (ZZZ) 999"], apply=True)
        lib = _read_csv(world["LIB"])
        # Library convention: the DFC is stored under its FRONT name (G-10).
        assert any(r["Card Name"] == "Bruce Banner" for r in lib)
        mana_names = {r["Card Name"] for r in _read_csv(world["MANA"])}
        assert "Bruce Banner" in mana_names


class TestInputHygiene:
    def test_unparseable_line_is_reported_not_dropped(self, world, capsys):
        rc.reconcile(["Bruce Banner"], apply=False)     # no qty/printing — F18
        out = capsys.readouterr().out
        assert "COULD NOT PARSE" in out and "Bruce Banner" in out

    def test_pool_absent_card_is_skipped_loudly(self, world, capsys):
        rc.reconcile(["1 Not A Card (XXX) 1"], apply=True)
        out = capsys.readouterr().out
        assert "NOT FOUND in pool" in out
        assert all(r["Card Name"] != "Not A Card" for r in _read_csv(world["LIB"]))
