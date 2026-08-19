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
                 "Collector #": "159", "Quantity Owned": "2"},
                # A printing the library stores under the FULL `A // B` name (the DSK
                # Rooms really are stored this way — the front-name convention is not
                # universal in the data).
                {"Card Name": "Bottomless Pool // Locker Room", "Type": "Enchantment — Room",
                 "Set Code": "DSK", "Collector #": "43", "Quantity Owned": "1"}])
    _write_csv(paths["MANA"], MANA_HEADER,
               [{"Card Name": "Shock", "Mana Cost": "{R}", "Mana Value": "1"},
                {"Card Name": "Bottomless Pool // Locker Room", "Mana Cost": "{U}",
                 "Mana Value": "1"}])
    _write_csv(paths["POOL"], POOL_HEADER, [
        {"Card Name": "Shock", "Type": "Instant", "Card Text": "Shock deals 2 damage to any target.",
         "Color(s)": "R", "Set Code": "M21", "Collector #": "159", "Rarity": "Common"},
        {"Card Name": "Duress", "Type": "Sorcery", "Card Text": "Target opponent reveals their hand.",
         "Color(s)": "B", "Set Code": "M21", "Collector #": "96", "Rarity": "Common"},
        # A DFC, keyed the way the pool really keys one: full `Front // Back`.
        {"Card Name": "Bruce Banner // The Incredible Hulk", "Type": "Legendary Creature — Human // Creature — Monster",
         "Card Text": "Whenever you cast a spell, transform Bruce Banner.",
         "Color(s)": "U/G", "Set Code": "MSH", "Collector #": "5", "Rarity": "Mythic"},
        {"Card Name": "Bottomless Pool // Locker Room", "Type": "Enchantment — Room",
         "Card Text": "Return up to one target creature to its owner's hand.",
         "Color(s)": "U", "Set Code": "DSK", "Collector #": "43", "Rarity": "Common"},
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

    def test_writes_land_even_when_stdout_dies_mid_report(self, world, monkeypatch):
        """DURABLE WORK BEFORE NARRATION. The report used to run before any write, and
        every print() is a chance to die: with stdout a pipe that closes early
        (`reconcile_crafts.py ... --apply | head -6`) the next print raises
        BrokenPipeError, the process exits 1, and NOTHING is written — after the user
        has already read what looks like a success summary. Two real batches were lost
        that way on 2026-08-18 (Nexus of Becoming + Racers' Scoreboard, then Krang &
        Shredder), each caught only by re-grepping the library afterwards. `check_all`
        is structurally blind to it: a card missing from the inventory breaks no
        invariant. Pin the ORDER, not the symptom."""
        import builtins
        real_print = builtins.print
        seen = {"n": 0}

        def dying_print(*a, **kw):
            seen["n"] += 1
            if seen["n"] > 2:                      # die partway through the report
                raise BrokenPipeError(32, "Broken pipe")
            return real_print(*a, **kw)

        monkeypatch.setattr(builtins, "print", dying_print)
        with pytest.raises(BrokenPipeError):
            rc.reconcile(["1 Duress (M21) 96"], apply=True)
        monkeypatch.setattr(builtins, "print", real_print)
        # The whole point: the row is on disk even though the report never finished.
        assert any(r["Card Name"] == "Duress" for r in _read_csv(world["LIB"])), \
            "library write was lost when stdout closed mid-report"
        assert "Duress" in {r["Card Name"] for r in _read_csv(world["MANA"])}
        assert all(r["Card Name"] != "Duress" for r in _read_csv(world["WISH"]))

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

    def test_front_name_paste_of_a_full_name_stored_printing_does_not_duplicate(self, world):
        """BS2-02: the library stores the DSK Rooms under the full `A // B` name,
        and the exact-front-name join missed those rows — so re-ingesting an owned
        printing APPENDED a second row under the front name. The count then split
        across two spellings where `lib.owned_qty` resolves only one, and the
        collection silently under-reported. The join must match on front faces."""
        rc.reconcile(["2 Bottomless Pool (DSK) 43"], apply=True)
        lib = _read_csv(world["LIB"])
        rooms = [r for r in lib if r["Card Name"].startswith("Bottomless Pool")]
        assert len(rooms) == 1                                   # no duplicate row
        assert rooms[0]["Card Name"] == "Bottomless Pool // Locker Room"
        assert rooms[0]["Quantity Owned"] == "2"                 # max(1, 2) bumped in place
        # And no spurious front-named mana row: the stored full-name row is the one
        # INV-02 needs, and it already exists.
        mana_names = [r["Card Name"] for r in _read_csv(world["MANA"])]
        assert mana_names.count("Bottomless Pool // Locker Room") == 1
        assert "Bottomless Pool" not in mana_names


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


class TestBasicLands:
    """BS4-03: basic lands are NOT part of the collection (unlimited in Arena) — which is
    why `import_arena` offers --skip-basics and `import_collection` skips them outright.
    This tool had no guard at all, and it is the one G-10 names as the FASTEST fix for
    reconciling from an Arena export, i.e. the one most likely to be handed a full deck
    list. The pool carries real basic-land rows, so `7 Forest (BLB) 280` resolved and
    --apply wrote a basics row into the inventory with no invariant able to object."""

    def _world_with_basics(self, world):
        rows = _read_csv(world["POOL"])
        rows.append({"Card Name": "Forest", "Type": "Basic Land — Forest", "Card Text": "",
                     "Color(s)": "G", "Set Code": "BLB", "Collector #": "280",
                     "Rarity": "Common", "Synergies": ""})
        _write_csv(world["POOL"], POOL_HEADER, rows)
        return world

    def test_a_basic_never_enters_the_library(self, world, capsys):
        self._world_with_basics(world)
        rc.reconcile(["1 Duress (M21) 96", "7 Forest (BLB) 280"], apply=True)
        names = [r["Card Name"] for r in _read_csv(world["LIB"])]
        assert "Forest" not in names
        assert "Duress" in names            # the real card on the same paste still lands

    def test_a_basic_gets_no_mana_row_either(self, world):
        self._world_with_basics(world)
        rc.reconcile(["7 Forest (BLB) 280"], apply=True)
        assert all(r["Card Name"] != "Forest" for r in _read_csv(world["MANA"]))

    def test_the_skip_is_reported_not_silent(self, world, capsys):
        """A dropped line the user pasted must be visible, or the tool looks broken."""
        self._world_with_basics(world)
        rc.reconcile(["7 Forest (BLB) 280"], apply=False)
        out = capsys.readouterr().out
        assert "Basic lands (skipped" in out and "Forest" in out
