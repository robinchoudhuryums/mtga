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
    state that no longer existed. The CSV save has had this 409 contract all along."""

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
