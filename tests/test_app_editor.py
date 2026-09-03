"""Editor write-safety pins (Batch D: BS2-26/27/28).

Flask lives in requirements-app.txt (the editor is optional), so this module
importorskips: it runs wherever the app's own dependency is present and skips
cleanly in the dependency-free environments, the same split `make app` draws.
"""
import json
import os

import pytest

flask = pytest.importorskip("flask", reason="editor dependency (requirements-app.txt)")

import app  # noqa: E402
import deck as deckmod  # noqa: E402


@pytest.fixture
def world(tmp_path, monkeypatch):
    folder = tmp_path / "99-scratch"
    folder.mkdir()
    path = folder / "deck.txt"
    path.write_text("#: name: Scratch\n\n4 Shock (M21) 159\n", encoding="utf-8")
    d = {"id": "99", "name": "Scratch", "path": str(path), "core": "99", "variant": None}
    monkeypatch.setattr(deckmod, "find_deck",
                        lambda i: d if str(i) == "99" else None)
    return str(path)


def _save(client, path, *, token, meta=None, body=None):
    body = body if body is not None else [
        {"kind": "card", "qty": 4, "name": "Shock", "set": "M21", "cn": "159"}]
    meta = meta if meta is not None else [{"key": "name", "value": "Scratch"}]
    return client.post("/api/deck/save",
                       data=json.dumps({"id": "99", "meta": meta, "body": body,
                                        "doc_token": token}),
                       headers={"Content-Type": "application/json"})


class TestDeckSaveStaleness:
    """BS2-26: the deck save was a blind whole-document overwrite — an open tab
    silently reverted a CLI `swap --apply` (the documented G-06 workflow writes the
    same file), and recommendations.csv then recorded a decision against a deck
    state that no longer existed. The CSV save got the same contract at BS8-18 — this
    docstring used to claim it "had it all along", which was false and is the reason
    `TestCsvSaveStaleness` below exists."""

    def test_fresh_token_saves_and_returns_the_new_token(self, world):
        c = app.app.test_client()
        r = _save(c, world, token=app._doc_token(world))
        j = r.get_json()
        assert r.status_code == 200 and j["ok"]
        assert j["doc_token"] == app._doc_token(world)

    def test_a_concurrent_change_409s_and_survives(self, world):
        c = app.app.test_client()
        tok = app._doc_token(world)
        with open(world, "a", encoding="utf-8") as fh:
            fh.write("1 Opt (M21) 1\n")          # the CLI swap under the open tab
        r = _save(c, world, token=tok)
        assert r.status_code == 409
        assert "CHANGED" in r.get_json()["errors"][0]
        assert "Opt" in open(world, encoding="utf-8").read()

    def test_an_absent_token_keeps_the_old_contract(self, world):
        """A cached pre-token page must still be able to save (no token = no gate);
        the gate is opt-in by presence, and every freshly-served page carries one."""
        c = app.app.test_client()
        r = _save(c, world, token="")
        assert r.status_code == 200


class TestMetaKeyValidation:
    """BS2-28: a key META_RE can't parse saved fine, toasted success, then silently
    demoted to a comment on the next load — deck.py never saw the header."""

    def test_a_spaced_key_is_rejected_before_any_write(self, world):
        c = app.app.test_client()
        before = open(world, encoding="utf-8").read()
        r = _save(c, world, token=app._doc_token(world),
                  meta=[{"key": "uncastable ok", "value": "Omniscience"}])
        assert r.status_code == 400
        assert "not a valid" in r.get_json()["errors"][0]
        assert open(world, encoding="utf-8").read() == before

    def test_a_hyphenated_key_is_fine(self, world):
        c = app.app.test_client()
        r = _save(c, world, token=app._doc_token(world),
                  meta=[{"key": "uncastable-ok", "value": "Omniscience"}])
        assert r.status_code == 200
        assert "#: uncastable-ok: Omniscience" in open(world, encoding="utf-8").read()

    def test_a_nameless_field_with_a_value_is_rejected(self, world):
        c = app.app.test_client()
        r = _save(c, world, token=app._doc_token(world),
                  meta=[{"key": "", "value": "orphaned prose"}])
        assert r.status_code == 400



HEADER = "Card Name,Type,Card Text,Color(s),Synergies,Set Code,Collector #,Quantity Owned\n"


@pytest.fixture
def library(tmp_path, monkeypatch):
    lib = tmp_path / "card-library.csv"
    lib.write_text(HEADER + "Shock,Instant,Shock deals 2 damage to any target.,R,burn,M21,159,1\n",
                   encoding="utf-8")
    mana = tmp_path / "card-mana.csv"
    mana.write_text("Card Name,Mana Cost,Mana Value,Keywords\nShock,{R},1,\n", encoding="utf-8")
    monkeypatch.setattr(app, "DEFAULT_CSV", str(lib))
    monkeypatch.setattr(app, "MANA_CSV", str(mana), raising=False)
    return lib


def _csv_save(client, edits, token=None):
    body = {"edits": edits}
    if token is not None:
        body["lib_token"] = token
    return client.post("/api/save", data=json.dumps(body),
                       headers={"Content-Type": "application/json"})


class TestCsvSaveStaleness:
    """BS8-18: `/api/save` wrote quantity AND synergies from the client with no check
    that the CSV still matched what the page loaded, so a stale tab editing only a
    card's synergies regressed a quantity a CLI import had raised. The token is the
    same content-hash contract the deck editor has carried since BS2-26."""

    EDIT = [{"key": {"name": "Shock", "set": "M21", "collector": "159"},
             "quantity": "1", "synergies": "burn; reach"}]

    def test_a_fresh_token_saves_and_a_new_token_comes_back(self, library):
        c = app.app.test_client()
        r = _csv_save(c, self.EDIT, token=app._lib_token())
        assert r.status_code == 200 and r.get_json()["ok"]
        assert r.get_json()["lib_token"] == app._lib_token()

    def test_a_stale_token_is_refused_and_the_file_is_untouched(self, library):
        c = app.app.test_client()
        stale = app._lib_token()
        # a CLI write lands underneath the open page
        library.write_text(library.read_text(encoding="utf-8").replace(",159,1", ",159,9"),
                           encoding="utf-8")
        r = _csv_save(c, self.EDIT, token=stale)
        assert r.status_code == 409
        assert ",159,9" in library.read_text(encoding="utf-8"), "the CLI's 9 survived"

    def test_an_absent_token_keeps_the_old_contract(self, library):
        c = app.app.test_client()
        assert _csv_save(c, self.EDIT).status_code == 200

    def test_a_bare_list_body_still_saves(self, library):
        c = app.app.test_client()
        r = c.post("/api/save", data=json.dumps(self.EDIT),
                   headers={"Content-Type": "application/json"})
        assert r.status_code == 200


class TestDeckSaveGateEqualsInv04:
    """BS8-19: the deck save was gated on parse fidelity alone, so an unknown `(SET)`
    code and a smuggled raw line both saved with a success toast and left check_all
    red. The editor now runs the same two checks the gate runs before promote."""

    def test_an_unknown_set_code_is_refused(self, world):
        c = app.app.test_client()
        body = [{"kind": "card", "qty": 4, "name": "Shock", "set": "ZZZ", "cn": "999"}]
        r = _save(c, world, token=app._doc_token(world), body=body)
        assert r.status_code == 400
        assert any("(ZZZ)" in e for e in r.get_json()["errors"])
        assert "(ZZZ)" not in open(world, encoding="utf-8").read()

    def test_a_smuggled_non_card_line_is_refused(self, world):
        c = app.app.test_client()
        body = [{"kind": "card", "qty": 4, "name": "Shock", "set": "M21", "cn": "159"},
                {"kind": "other", "raw": "Lightning Bolt (DMU) 137"}]
        r = _save(c, world, token=app._doc_token(world), body=body)
        assert r.status_code == 400
        assert any("not a card line" in e for e in r.get_json()["errors"])

    def test_the_file_keeps_its_mode_on_save(self, world):
        """BS8-42: mkstemp is 0600 and os.replace keeps the temp's mode — three app
        write paths flipped 644 files to 600 (the regression lib.atomic_write documents)."""
        os.chmod(world, 0o644)
        c = app.app.test_client()
        r = _save(c, world, token=app._doc_token(world))
        assert r.status_code == 200
        assert oct(os.stat(world).st_mode & 0o777) == "0o644"
