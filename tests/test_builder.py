"""Builder projects (scripts/builder.py): the data model, its derivation and its CLI.

Every test works on a scratch `builds/` directory and a scratch COPY of a deck file, so the
repo's own builds and decks are never written (G-88). Deck 96 is used as the source deck
because it is a real, legal 100-card list; only the copy is edited.
"""
import json
import re
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


class TestProtectPicks:
    COPY = ("Glarb ({deck}):\n"
            "  protect: Counterspell; Murder\n"
            "  unprotect: Counterspell\n")

    def test_parse_reads_protect_and_unprotect(self):
        p = B.parse_picks(self.COPY.format(deck="96"))["decks"]["96"]
        assert p["protect"] == ["Counterspell", "Murder"] and p["unprotect"] == ["Counterspell"]

    def test_report_checks_requests_against_the_header(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        lines = B.picks_report(b, self.COPY.format(deck=deck_path))
        assert any(ln.startswith("#   protect (header edit): Counterspell") for ln in lines)
        assert any("Murder is not in" in ln for ln in lines)               # not run by the deck
        assert any("Counterspell is not protected" in ln for ln in lines)  # cannot unprotect it


class TestVerdicts:
    """A verdict is one card's hand grade for one deck, stamped with that deck's list hash."""

    def test_aliases_normalise_and_unknown_marks_are_refused(self):
        assert [B.norm_verdict(x) for x in ("3", "strong", "*", "s", "m", "out")] == \
            ["★★★", "★★", "★", "◇", "△", "✗"]
        with pytest.raises(B.BuildError):
            B.norm_verdict("A+")

    def test_set_clear_and_pre_draft(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        B.add_cards(b, ["Opt", "Murder"], pile="G")
        B.set_verdict(b, "Opt", "G", "2")
        B.set_verdict(b, "Murder", "g", "◇", pre=True)                 # key match is case-insensitive
        assert b["verdicts"]["Opt"]["G"]["m"] == "★★" and b["verdicts"]["Opt"]["G"]["graded_at"]
        assert b["verdicts"]["Murder"]["G"]["graded_at"] is None
        B.set_verdict(b, "Murder", "G", "-")
        assert "Murder" not in b["verdicts"]
        with pytest.raises(B.BuildError):
            B.set_verdict(b, "Opt", "Nope", "★")

    def test_derive_and_check_report_pre_draft_and_stale(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        B.add_cards(b, ["Opt", "Murder", "Counterspell"], pile="G")
        B.set_verdict(b, "Opt", "G", "★★")
        B.set_verdict(b, "Murder", "G", "★", pre=True)
        text = open(deck_path, encoding="utf-8").read()
        open(deck_path, "w", encoding="utf-8").write(text.replace("8 Island", "7 Island", 1))
        cards = {c["n"]: c for c in B.derive(b, tempo=False)["cards"]}
        assert cards["Opt"]["vd"] == {"G": "★★"} and cards["Opt"]["vs"] == {"G": "stale"}
        assert cards["Murder"]["vs"] == {"G": "pre"} and cards["Counterspell"]["vd"] == {}
        line = next(m for s, m in B.check_build(b) if s == "verdicts")
        assert "1 with no verdict" in line and "1 pre-draft" in line and "1 graded before" in line

    def test_cli_file_validates_every_line_before_writing(self, scratch):
        deck_path, tmp = scratch
        B.save_build("t", _new(deck_path))
        b = B.load_build("t")
        B.add_cards(b, ["Opt"], pile="G")
        B.save_build("t", b)
        bad = tmp / "v.tsv"
        bad.write_text("Opt\tG\t★★\nOpt\tG\tA+\n", encoding="utf-8")
        assert B.main(["verdict", "t", "--file", str(bad)]) == 2
        assert "verdicts" not in B.load_build("t")                       # nothing half-written
        bad.write_text("# a comment\nOpt\tG\tstrong\n", encoding="utf-8")
        assert B.main(["verdict", "t", "--file", str(bad)]) == 0
        assert B.load_build("t")["verdicts"]["Opt"]["G"]["m"] == "★★"


class TestBenchAndKeepOutPicks:
    """Bench and Keep out are per deck: they sit in that deck's block of the copied text and
    are checked against the deck. A bench becomes a `deck.py flex --add` command (the deck
    file's #~ block); Keep out stays a no-edit note."""
    COPY = ("Glarb ({deck}):\n"
            "  bench: Murder; Counterspell\n"
            "  keep out: Krang, the All-Powerful\n")

    def test_parse_reads_bench_and_keep_out_per_deck(self):
        p = B.parse_picks(self.COPY.format(deck="96"))["decks"]["96"]
        assert p["bench"] == ["Murder", "Counterspell"] and p["out"] == ["Krang, the All-Powerful"]

    def test_report_lists_them_without_an_edit(self, scratch):
        deck_path, _ = scratch
        lines = B.picks_report(_new(deck_path), self.COPY.format(deck=deck_path))
        assert any(ln.startswith('python3 scripts/deck.py flex') and '"+Murder | BENCH (builder' in ln
                   and "--apply" not in ln for ln in lines)                # a dry-run command per card
        assert any(ln.startswith("#   keep out (no edit): Krang") for ln in lines)
        assert any("Counterspell is in" in ln and "cut it instead" in ln for ln in lines)
        assert not any(ln.startswith("python3 scripts/deck.py swap") for ln in lines)


class TestRender:
    URL = "https://cards.scryfall.io/normal/front/a/b/{}.jpg"

    def _fake_urls(self, monkeypatch):
        monkeypatch.setattr(B, "image_urls",
                            lambda slug, names, fetch=True: {n: self.URL.format(i) for i, n in enumerate(names)})

    def _data(self, path):
        import re
        s = open(path, encoding="utf-8").read()
        m = re.search(r'<script type="application/json" id="data">(.*?)</script>', s, re.S)
        return s, json.loads(m.group(1).replace("<\\/", "</"))

    def test_pages_render_is_a_whole_document_with_remote_images(self, scratch, monkeypatch):
        deck_path, tmp = scratch
        self._fake_urls(monkeypatch)
        b = B.new_build("t", [deck_path], keys=["G"], title="Test <&> build")
        B.add_cards(b, ["Counterspell"], pile="G")
        B.save_build("t", b)
        r = B.render("t", "pages", str(tmp / "out"), tempo=False)
        s, data = self._data(r["page"])
        assert s.startswith("<!doctype html>") and "__DATA__" not in s and "__TITLE__" not in s
        assert "<title>Test &lt;&amp;&gt; build</title>" in s
        assert data["meta"]["img"] == "remote" and data["meta"]["target"] == "pages"
        assert data["cards"][0]["im"].startswith("https://cards.scryfall.io/normal/")

    def test_artifact_render_uses_local_files(self, scratch, monkeypatch):
        deck_path, tmp = scratch
        self._fake_urls(monkeypatch)
        b = _new(deck_path)
        B.add_cards(b, ["Counterspell"], pile="G")
        B.save_build("t", b)
        r = B.render("t", "artifact", str(tmp / "out"), tempo=False, images=False)
        s, data = self._data(r["page"])
        assert not s.startswith("<!doctype") and data["meta"]["img"] == "local"
        assert "im" not in data["cards"][0]
        assert not os.path.exists(tmp / "out" / "img")                   # images=False fetches nothing

    def test_unknown_target_is_refused(self, scratch):
        deck_path, tmp = scratch
        _new(deck_path)
        with pytest.raises(B.BuildError, match="unknown target"):
            B.render("t", "pdf", str(tmp / "out"), tempo=False, images=False)


class TestBatch2b:
    def test_hidden_roles_are_recorded_validated_and_removable(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        B.add_cards(b, ["Opt"], pile="G")
        B.set_hidden(b, "opt", "card-advantage")
        assert b["hidden"] == {"Opt": ["card advantage"]}
        with pytest.raises(B.BuildError, match="unknown role"):
            B.set_hidden(b, "Opt", "ramp")
        with pytest.raises(B.BuildError, match="not in this build"):
            B.set_hidden(b, "Counterspell", "interaction")
        B.set_hidden(b, "Opt", "card advantage", remove=True)
        assert b["hidden"] == {}

    def test_derive_adds_deck_only_cards_and_the_2b_fields(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        B.add_cards(b, ["Opt"], pile="G")
        B.set_hidden(b, "Opt", "card advantage")
        data = B.derive(b, tempo=False)
        opt = next(c for c in data["cards"] if c["n"] == "Opt")
        assert opt["hc"] == ["card advantage"] and isinstance(opt["hr"], list)
        assert re.fullmatch(r"[A-Z0-9]{2,6} \S+", opt["pr"])            # a printing for /ingest
        listed = {x["n"] for x in data["meta"]["live"]["G"]["list"]}
        deck_only = [c for c in data["cards"] if c["p"] is None]
        assert {c["n"] for c in deck_only} == listed - {"Opt"}          # every list card has a record
        assert all(c["iG"] for c in deck_only)

    def test_ownership_and_hidden_lines_round_trip_through_picks(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        text = ("Ownership (I own exactly — /ingest it with reconcile_crafts --set-exact):\n"
                "  3 Deathrite Shaman (EA3) 15\n  0 Opt\n"
                "Counts as interaction:\n  - Deathrite Shaman\n")
        p = B.parse_picks(text)
        assert p["own"] == [(3, "Deathrite Shaman", "EA3", "15"), (0, "Opt", None, None)]
        assert p["hidden"] == [("Deathrite Shaman", "interaction")]
        lines = B.picks_report(b, text, "t")
        assert "3 Deathrite Shaman (EA3) 15" in lines
        assert any(ln.startswith("0 Opt") and "no printing" in ln for ln in lines)
        assert any("reconcile_crafts.py <file> --set-exact" in ln for ln in lines)
        assert 'python3 scripts/builder.py hidden t "Deathrite Shaman" --role interaction' in lines


class TestSite:
    """Batch 3: every build rendered for GitHub Pages, plus the picker and the index."""

    def test_site_writes_picker_index_and_one_page_per_build(self, scratch, monkeypatch):
        deck_path, tmp = scratch
        monkeypatch.setattr(B, "image_urls", lambda slug, names, fetch=True: {
            n: f"https://cards.scryfall.io/normal/front/a/b/{i}.jpg" for i, n in enumerate(names)})
        b = B.new_build("t", [deck_path], keys=["G"], title="Test <pile>")
        B.add_cards(b, ["Opt"], pile="G")
        B.save_build("t", b)
        out = tmp / "site"
        projects, failures = B.site(str(out), tempo=False)
        assert failures == [] and [p["slug"] for p in projects] == ["t"]
        idx = json.load(open(out / "builds" / "index.json"))
        assert idx["projects"][0]["page"] == "builds/t.html" and idx["projects"][0]["cards"] == 1
        picker = (out / "builder.html").read_text()
        assert 'href="builds/t.html"' in picker and "Test &lt;pile&gt;" in picker
        assert picker.startswith("<!doctype html>") and 'href="index.html"' in picker
        page = (out / "builds" / "t.html").read_text()
        import re as _re
        data = json.loads(_re.search(r'id="data">(.*?)</script>', page, _re.S).group(1).replace("<\\/", "</"))
        assert data["meta"]["target"] == "pages" and data["meta"]["home"] == "../index.html"

    def test_one_broken_build_is_reported_not_fatal(self, scratch, monkeypatch):
        deck_path, tmp = scratch
        monkeypatch.setattr(B, "image_urls", lambda slug, names, fetch=True: {})
        B.save_build("good", {**B.new_build("good", [deck_path], keys=["G"])})
        os.makedirs(os.path.join(B.BUILDS_DIR, "bad"))
        with open(os.path.join(B.BUILDS_DIR, "bad", "build.json"), "w") as fh:
            fh.write('{"decks": [{"key": "G", "id": "no-such-deck"}], "cards": [], "reasons": {}}')
        projects, failures = B.site(str(tmp / "site"), tempo=False)
        assert [p["slug"] for p in projects] == ["good"]
        assert len(failures) == 1 and failures[0].startswith("bad:")

    def test_summaries_feed_the_dashboard(self, scratch):
        deck_path, _ = scratch
        b = _new(deck_path)
        B.add_cards(b, ["Opt", "Counterspell"], pile="G")
        B.save_build("t", b)
        s = B.summaries()
        assert s == [{"slug": "t", "title": "Test", "decks": [{"id": deck_path, "label": b["decks"][0]["label"]}],
                      "cards": 2, "reasons": 0, "page": "builds/t.html"}]


class TestDashboardAndDeploy:
    def test_dashboard_has_the_builder_link_section_and_payload(self):
        import build_dashboard as bd
        t = bd.TEMPLATE
        assert 'id="btnbuilder"' in t and 'id="sec-builder"' in t and "['sec-builder','Builder'" in t
        assert "renderBuilder()" in t
        assert set(bd._builds()) >= {"projects"}

    def test_pages_workflow_builds_and_verifies_the_builder(self):
        y = open(os.path.join(REPO, ".github", "workflows", "pages.yml"), encoding="utf-8").read()
        assert "python3 scripts/builder.py site --out _site" in y
        assert "_site/builder.html is missing" in y and "has no data island" in y


class TestAddDeck:
    def test_a_deck_joins_with_its_own_pile_before_the_shared_ones(self, scratch):
        deck_path, tmp = scratch
        other = tmp / "deck75.txt"
        shutil.copy(D.find_deck("75-historic-brawl")["path"], other)
        b = _new(deck_path)
        B.add_cards(b, ["Opt"], pile="G")
        B.set_reason(b, "Opt", "fine")
        k = B.add_deck(b, str(other), key="T", label="Thranduil")
        assert k == "T" and [d["key"] for d in b["decks"]] == ["G", "T"]
        # a second deck brings the shared pile, and "Doesn't fit" (one deck) becomes "Fits neither"
        assert [(p["key"], p["label"]) for p in b["piles"]][1:] == \
            [("T", "Thranduil's pile"), ("B", "Either deck"), ("N", "Fits neither")]
        assert set(b["reasons"]["Opt"]["graded_at"]) == {deck_path}       # not re-stamped
        with pytest.raises(B.BuildError, match="already in this build"):
            B.add_deck(b, str(other))
        with pytest.raises(B.BuildError, match="already used"):
            B.add_deck(b, D.find_deck("96")["path"], key="N")


class TestPrintingArts:
    """View-only alternate Arena printings: one entry per ILLUSTRATION (Scryfall unique:art),
    cached per build; a card with one art is cached as [] and never returned."""

    def _fake_scryfall(self, monkeypatch, calls):
        import scryfall
        def post_collection(names, **kw):
            calls.append(("collection", tuple(names)))
            return {"data": [{"name": n, "oracle_id": f"oid-{n}"} for n in names]}
        def get_json(url, **kw):
            calls.append(("search", url))
            data = [{"oracle_id": "oid-Opt", "set": "xln", "collector_number": "65", "rarity": "common",
                     "released_at": "2017-09-29", "artist": "A", "set_name": "Ixalan",
                     "image_uris": {"art_crop": "https://x/art_crop/a.jpg", "normal": "https://x/normal/a.jpg"},
                     "frame_effects": ["legendary"], "border_color": "black"},
                    {"oracle_id": "oid-Opt", "set": "sta", "collector_number": "82", "rarity": "uncommon",
                     "released_at": "2021-04-23", "artist": "B", "set_name": "Mystical Archive",
                     "image_uris": {"art_crop": "https://x/art_crop/b.jpg", "normal": "https://x/normal/b.jpg"},
                     "frame_effects": ["showcase"], "border_color": "borderless"},
                    {"oracle_id": "oid-Counterspell", "set": "mar", "collector_number": "52", "rarity": "uncommon",
                     "released_at": "2025-01-01", "artist": "C", "set_name": "X",
                     "image_uris": {"art_crop": "https://x/art_crop/c.jpg", "normal": "https://x/normal/c.jpg"}}]
            return {"data": data, "has_more": False}
        monkeypatch.setattr(scryfall, "post_collection", post_collection)
        monkeypatch.setattr(scryfall, "get_json", get_json)

    def test_arts_are_fetched_once_cached_and_single_art_cards_dropped(self, scratch, monkeypatch):
        deck_path, _ = scratch
        _new(deck_path)
        calls = []
        self._fake_scryfall(monkeypatch, calls)
        arts = B.printing_arts("t", ["Opt", "Counterspell"])
        assert list(arts) == ["Opt"]                                  # Counterspell has one art
        assert [p["set"] for p in arts["Opt"]] == ["XLN", "STA"]
        assert arts["Opt"][0]["fx"] == [] and arts["Opt"][1]["fx"] == ["borderless", "showcase"]
        assert "unique%3Aart" in next(u for k, u in calls if k == "search")
        cache = json.load(open(os.path.join(B.BUILDS_DIR, "t", "printings.json")))
        assert cache["Counterspell"] == [] and len(cache["Opt"]) == 2
        calls.clear()
        assert B.printing_arts("t", ["Opt", "Counterspell"]) == arts and calls == []   # cache only

    def test_offline_render_reads_the_cache_and_attaches_al(self, scratch, monkeypatch):
        deck_path, tmp = scratch
        b = _new(deck_path)
        B.add_cards(b, ["Opt", "Counterspell"], pile="G")
        B.save_build("t", b)
        calls = []
        self._fake_scryfall(monkeypatch, calls)
        B.printing_arts("t", ["Opt", "Counterspell"])
        monkeypatch.setattr(B, "image_urls", lambda slug, names, fetch=True: {})
        import scryfall
        monkeypatch.setattr(scryfall, "get_json", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network")))
        r = B.render("t", "pages", str(tmp / "out"), tempo=False, fetch=False)
        import re as _re
        s = open(r["page"], encoding="utf-8").read()
        data = json.loads(_re.search(r'id="data">(.*?)</script>', s, _re.S).group(1).replace("<\\/", "</"))
        by = {c["n"]: c for c in data["cards"]}
        assert len(by["Opt"]["al"]) == 2 and "al" not in by["Counterspell"]


class TestDeckCount:
    """The deck-less piles are named for the number of decks, and a build of one or of three
    decks renders like a build of two (Batch C)."""

    def _copies(self, tmp, deck_path, n):
        out = []
        for i in range(n):
            p = tmp / f"copy{i}.txt"
            shutil.copy(deck_path, p)
            out.append(str(p))
        return out

    def test_pile_labels_follow_the_deck_count(self, scratch):
        deck_path, tmp = scratch
        paths = self._copies(tmp, deck_path, 3)
        assert [p["label"] for p in B.new_build("one", paths[:1])["piles"]][1:] == ["Doesn't fit"]
        assert [p["label"] for p in B.new_build("two", paths[:2])["piles"]][2:] == ["Either deck", "Fits neither"]
        three = B.new_build("three", paths)
        assert [p["label"] for p in three["piles"]][3:] == ["More than one deck", "Fits none"]
        assert len({d["key"] for d in three["decks"]}) == 3            # three Glarbs, three keys

    def test_add_deck_retitles_default_labels_and_keeps_renamed_ones(self, scratch):
        deck_path, tmp = scratch
        paths = self._copies(tmp, deck_path, 3)
        b = B.new_build("grow", paths[:1])
        B.add_deck(b, paths[1])                                         # 1 → 2: the shared pile appears
        assert [(p["key"], p["label"]) for p in b["piles"] if p["deck"] is None] == \
            [("B", "Either deck"), ("N", "Fits neither")]
        next(p for p in b["piles"] if p["key"] == "N")["label"] = "Bin"  # the owner renamed it
        B.add_deck(b, paths[2])                                         # 2 → 3
        assert [(p["key"], p["label"]) for p in b["piles"] if p["deck"] is None] == \
            [("B", "More than one deck"), ("N", "Bin")]

    @pytest.mark.parametrize("n", [1, 3])
    def test_one_and_three_deck_builds_render(self, scratch, monkeypatch, n):
        deck_path, tmp = scratch
        monkeypatch.setattr(B, "image_urls",
                            lambda slug, names, fetch=True: {x: "https://cards.scryfall.io/normal/front/a/b/x.jpg" for x in names})
        paths = self._copies(tmp, deck_path, n)
        b = B.new_build(f"r{n}", paths)
        B.add_cards(b, ["Murder"], pile=b["piles"][0]["key"])
        B.save_build(f"r{n}", b)
        r = B.render(f"r{n}", "pages", str(tmp / f"out{n}"), tempo=False, fetch=False)
        s = open(r["page"], encoding="utf-8").read()
        data = json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', s, re.S)
                          .group(1).replace("<\\/", "</"))
        assert len(data["meta"]["decks"]) == n == len(data["meta"]["live"])
        assert [p["label"] for p in data["meta"]["piles"]][n:] == \
            ([B.shared_pile_labels(n)[0]] if n > 1 else []) + [B.shared_pile_labels(n)[1]]
        assert any(c["n"] == "Murder" for c in data["cards"])


class TestSharedPileKeys:
    """A deck key is its pile's key, so it can never be a shared pile's key: a Bruvac deck used to
    get "B" and collide with the "Either deck" pile."""

    def test_derived_key_steps_aside_and_explicit_one_is_refused(self, scratch, monkeypatch):
        deck_path, tmp = scratch
        monkeypatch.setattr(B, "deck_ref", lambda ref: {"id": ref, "path": deck_path, "name": ref})
        monkeypatch.setattr(B._deck(), "parse_deck_file",
                            lambda path: ({"commander": "Bruvac the Grandiloquent"}, []))
        b = B.new_build("bb", ["d1", "d2"])
        keys = [p["key"] for p in b["piles"]]
        assert len(keys) == len(set(keys)) and b["decks"][0]["key"] != "B"
        with pytest.raises(B.BuildError, match="shared piles' keys"):
            B.new_build("bb2", ["d1", "d2"], keys=["B", "G"])
        one = B.new_build("bb3", ["d1"])
        with pytest.raises(B.BuildError, match="already used"):
            B.add_deck(one, "d2", key="B")                  # reserved even before the pile exists
        k = B.add_deck(one, "d2")
        assert k not in ("B", "N") and "B" in [p["key"] for p in one["piles"]]
