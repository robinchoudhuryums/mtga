"""Builder projects (scripts/builder.py): the data model, its derivation and its CLI.

Every test works on a scratch `builds/` directory and a scratch COPY of a deck file, so the
repo's own builds and decks are never written (G-88). Deck 96 is used as the source deck
because it is a real, legal 100-card list; only the copy is edited.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "scripts"))
import builder as B  # noqa: E402
import deck as D  # noqa: E402


@pytest.fixture
def scratch(tmp_path, monkeypatch):
    """A scratch builds/ dir plus a scratch copy of deck 96; returns (deck_path, tmp_path)."""
    monkeypatch.setattr(B, "BUILDS_DIR", str(tmp_path / "builds"))
    src = D.find_deck("96")["path"]
    dst = tmp_path / "deck96.txt"
    shutil.copy(src, dst)
    return str(dst), tmp_path


def _new(deck_path):
    return B.new_build("t", [deck_path], keys=["G"], title="Test")


class TestBuildFile:
    def test_new_writes_decks_and_default_piles(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        assert [d["key"] for d in b["decks"]] == ["G"]
        assert [p["key"] for p in b["piles"]] == ["G", "N"]   # one deck: no "either" pile
        assert os.path.exists(B.build_path("t"))
        with pytest.raises(B.BuildError):
            _new(deck_path)                                     # never overwrites

    def test_two_decks_get_an_either_pile_and_distinct_keys(self, scratch):
        deck_path, tmp = scratch
        other = tmp / "deck75.txt"
        shutil.copy(D.find_deck("75-historic-brawl")["path"], other)
        b = B.new_build("two", [deck_path, str(other)])
        keys = [d["key"] for d in b["decks"]]
        assert len(set(keys)) == 2
        assert "B" in [p["key"] for p in b["piles"]]

    def test_add_resolves_names_and_refuses_unknown_before_writing(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        added, present = B.add_cards(b, ["krang, the all-powerful", "Counterspell"], pile="G")
        assert added == ["Krang, the All-Powerful", "Counterspell"] and present == []
        assert B.add_cards(b, ["Counterspell"], pile="G") == ([], ["Counterspell"])
        before = list(b["cards"])
        with pytest.raises(B.BuildError, match="not a known Arena card"):
            B.add_cards(b, ["Opt", "Hedron Crab"], pile="G")   # Hedron Crab is not on Arena
        assert b["cards"] == before                              # nothing half-added

    def test_place_and_reason_validate_their_inputs(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        B.add_cards(b, ["Opt"], pile="G")
        with pytest.raises(B.BuildError, match="no pile"):
            B.place_card(b, "Opt", "Z")
        with pytest.raises(B.BuildError, match="not in this build"):
            B.set_reason(b, "Counterspell", "x")
        B.set_reason(b, "Opt", "Scry then draw; Matoya draws again.", group="Draw")
        r = b["reasons"]["Opt"]
        assert r["group"] == "Draw" and set(r["graded_at"]) == {deck_path}


class TestCheck:
    def test_clean_build_reports_only_work_in_progress(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        B.add_cards(b, ["Opt"], pile="G")
        B.add_cards(b, ["Preordain"])                    # no pile yet
        sev = {s for s, _ in B.check_build(b)}
        assert "stale" not in sev and "unknown" not in sev
        assert "unplaced" in sev and "reasonless" in sev

    def test_a_deck_change_marks_its_reasons_stale(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        B.add_cards(b, ["Opt"], pile="G")
        B.set_reason(b, "Opt", "fine")
        assert not [m for s, m in B.check_build(b) if s == "stale"]
        text = open(deck_path, encoding="utf-8").read()
        assert "8 Island" in text
        open(deck_path, "w", encoding="utf-8").write(text.replace("8 Island", "7 Island", 1))
        stale = [m for s, m in B.check_build(b) if s == "stale"]
        assert stale and "Opt" in stale[0]

    def test_a_notes_edit_does_not_mark_reasons_stale(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        B.add_cards(b, ["Opt"], pile="G")
        B.set_reason(b, "Opt", "fine")
        with open(deck_path, "a", encoding="utf-8") as fh:
            fh.write("#: notes: an extra line of prose\n")
        assert not [m for s, m in B.check_build(b) if s == "stale"]

    def test_stale_summary_is_none_when_clean_and_names_the_command_when_not(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        B.add_cards(b, ["Opt"], pile="G")
        B.set_reason(b, "Opt", "fine")
        B.save_build("t", b)
        assert B.stale_summary("t") is None
        text = open(deck_path, encoding="utf-8").read()
        open(deck_path, "w", encoding="utf-8").write(text.replace("8 Island", "7 Island", 1))
        line = B.stale_summary("t")
        assert line and "builder.py check t" in line


class TestPicks:
    COPY = (
        "Notes:\n  - Krang, the All-Powerful — check with Bruvac\n"
        "Add to Glarb:\n  - Krang, the All-Powerful\n\n"
        "Glarb ({deck}):\n"
        '  python3 scripts/deck.py swap {deck} --package "Dictate of Kruphix=Krang, the All-Powerful" '
        '"Opt=Visions of Beyond"\n'
        "  adds with no cut chosen: Drowned Secrets\n"
    )

    def test_parse_reads_pairs_loose_adds_and_notes(self):
        p = B.parse_picks(self.COPY.format(deck="96"))
        assert p["decks"]["96"]["pairs"] == [("Dictate of Kruphix", "Krang, the All-Powerful"),
                                             ("Opt", "Visions of Beyond")]
        assert p["decks"]["96"]["adds"] == ["Drowned Secrets"]
        assert p["notes"] == ["Krang, the All-Powerful — check with Bruvac"]

    def test_report_keeps_valid_pairs_and_explains_the_rest(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        lines = B.picks_report(b, self.COPY.format(deck=deck_path))
        swap = [ln for ln in lines if ln.startswith("python3 scripts/deck.py swap")]
        assert len(swap) == 1 and '"Dictate of Kruphix=Krang, the All-Powerful"' in swap[0]
        assert any("Opt is not in" in ln for ln in lines)       # cut must be in the deck
        assert any("Drowned Secrets" in ln for ln in lines)


class TestDerive:
    def test_derive_fills_the_fields_the_board_reads(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        B.add_cards(b, ["Counterspell", "Opt"], pile="G")
        B.set_reason(b, "Opt", "fine", group="Draw")
        data = B.derive(b, tempo=False)
        cs = next(c for c in data["cards"] if c["n"] == "Counterspell")
        opt = next(c for c in data["cards"] if c["n"] == "Opt")
        for f in ("c", "mv", "t", "r", "o", "p", "x", "ro", "ri", "rc", "mf", "land", "iG", "pG"):
            assert f in cs, f
        assert cs["iG"] is True and opt["iG"] is False           # deck 96 runs Counterspell
        assert cs["ri"] == 1 and "Interaction" in cs["ro"]
        assert opt["w"] == "fine" and opt["g"] == "Draw"
        live = data["meta"]["live"]["G"]
        assert live["floor"] in "ABCD" and live["req"]["A"][0] >= live["req"]["B"][0]
        assert live["list"] and all("r" in x for x in live["list"])
        assert "W" not in live["sources"]                        # declared colours only


class TestRepoBuilds:
    def test_every_repo_build_is_well_formed(self):
        """Structure only — staleness is a soft warning by design, so it is not asserted."""
        for slug in B.all_builds():
            b = B.load_build(slug)
            piles = {p["key"] for p in b["piles"]}
            assert b["decks"] and all(D.find_deck(d["id"]) for d in b["decks"]), slug
            assert all(c["pile"] in piles for c in b["cards"]), slug
            assert set(b["reasons"]) <= {c["name"] for c in b["cards"]}, slug
            assert all("graded_at" in r for r in b["reasons"].values()), slug


class TestCli:
    def _run(self, *args):
        p = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "builder.py"), *args],
                           capture_output=True, text=True, cwd=REPO)
        return p.returncode, p.stdout + p.stderr

    def test_unknown_build_exits_2_with_a_message(self):
        rc, out = self._run("check", "no-such-build")
        assert rc == 2 and "no build" in out

    def test_bad_build_name_is_refused(self):
        rc, out = self._run("check", "Bad Name")
        assert rc == 2 and "bad build name" in out
