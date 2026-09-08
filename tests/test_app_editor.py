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

    def test_an_absent_token_is_now_REFUSED(self, world):
        """BS9-06 REVERSES this pin. It asserted 200 and read "a cached pre-token page
        must still be able to save (no token = no gate)". That justification expired:
        `templates/deck.html` sends the field unconditionally, the page is served by the
        same process that validates it, and a successful save reloads. Meanwhile the hole
        re-admitted the exact failure BS2-26 exists to stop — an open tab silently
        reverting a CLI `swap --apply`. Revert by dropping `deck_save`'s `not sent`."""
        c = app.app.test_client()
        r = _save(c, world, token="")
        assert r.status_code == 409
        assert "staleness token" in r.get_json()["errors"][0]

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

    def test_an_absent_token_is_now_REFUSED(self, library):
        """BS9-06, the CSV half — see the deck-save twin above. A DICT body is the
        CURRENT wire format and must carry a token; `test_a_bare_list_body_still_saves`
        below pins the one shape that legitimately cannot."""
        c = app.app.test_client()
        r = _csv_save(c, self.EDIT)
        assert r.status_code == 409
        assert "staleness token" in r.get_json()["errors"][0]

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


class TestRequestGuard:
    """BS9-05. `_guard_request` is the WHOLE security boundary of a write-capable
    server, and nothing tested it: a grep across tests/ for Origin, Host, 403,
    `_same_origin` or `_guard_request` returned nothing. Its own docstring names the two
    holes it closes — a cross-origin form POST to `/api/revert`, which reads no body at
    all and so is not accidentally protected by the JSON content-type check the other
    endpoints get for free; and DNS rebinding, where a hostile name resolving to
    127.0.0.1 scripts the editor from a page the user merely visits.

    Both are asserted in BOTH directions, because a guard that refuses everything is as
    broken as one that refuses nothing and looks identical from a passing test that only
    checks the refusal."""

    def test_a_cross_origin_post_is_refused(self, library):
        c = app.app.test_client()
        r = c.post("/api/revert", headers={"Origin": "http://evil.example"})
        assert r.status_code == 403
        assert "cross-origin" in r.get_json()["errors"][0]

    def test_a_same_origin_post_is_allowed_through_the_guard(self, library):
        """The guard must not be the thing that fails it — 409 (no backup yet) is the
        endpoint's own answer and proves the request reached it."""
        c = app.app.test_client()
        r = c.post("/api/revert", headers={"Origin": "http://localhost"})
        assert r.status_code != 403

    def test_a_post_with_no_origin_is_allowed(self):
        """Documented and deliberate: no Origin means a non-browser client (curl, a
        script), which CSRF does not apply to. Pinned so the reasoning is visible if
        someone tightens it."""
        c = app.app.test_client()
        assert c.post("/api/revert").status_code != 403

    def test_a_safe_method_is_never_origin_checked(self):
        c = app.app.test_client()
        assert c.get("/decks", headers={"Origin": "http://evil.example"}).status_code != 403

    def test_a_rebinding_host_is_refused(self):
        c = app.app.test_client()
        r = c.get("/decks", headers={"Host": "attacker.example"})
        assert r.status_code == 403
        assert "unexpected Host" in r.get_json()["errors"][0]

    @pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "127.0.0.1:5000"])
    def test_loopback_hosts_are_allowed(self, host):
        c = app.app.test_client()
        assert c.get("/decks", headers={"Host": host}).status_code != 403

    def test_a_deliberate_non_local_bind_relaxes_the_host_check(self, monkeypatch):
        """`main()` sets `_bind_host`; binding off loopback on purpose must not make
        every request 403, or the flag would be unusable."""
        monkeypatch.setattr(app, "_bind_host", "0.0.0.0")
        c = app.app.test_client()
        assert c.get("/decks", headers={"Host": "192.168.1.5:5000"}).status_code != 403


class TestDestructiveEndpoints:
    """BS9-05. `/api/add`, `/api/remove` and `/api/revert` write card-library.csv and
    were exercised by no test at all — `test_app_editor.py` covered `/api/save` and
    `/api/deck/save` only, i.e. 2 of the editor's 10 routes. `/api/revert` is the one
    the CSRF guard was written FOR."""

    KEY = {"name": "Shock", "set": "M21", "collector": "159"}

    def test_remove_drops_the_printing_and_backs_up(self, library):
        c = app.app.test_client()
        r = c.post("/api/remove", data=json.dumps({"key": self.KEY}),
                   headers={"Content-Type": "application/json"})
        assert r.status_code == 200 and r.get_json()["ok"]
        assert "Shock" not in library.read_text(encoding="utf-8")
        assert r.get_json()["backup"], "a destructive write must leave a .bak"

    def test_remove_of_an_absent_printing_is_refused(self, library):
        c = app.app.test_client()
        r = c.post("/api/remove",
                   data=json.dumps({"key": dict(self.KEY, collector="999")}),
                   headers={"Content-Type": "application/json"})
        assert r.status_code >= 400
        assert "Shock" in library.read_text(encoding="utf-8"), "the row must survive"

    def test_revert_restores_the_backup_remove_made(self, library):
        c = app.app.test_client()
        assert c.post("/api/remove", data=json.dumps({"key": self.KEY}),
                      headers={"Content-Type": "application/json"}).status_code == 200
        assert "Shock" not in library.read_text(encoding="utf-8")
        r = c.post("/api/revert")
        assert r.status_code == 200 and r.get_json()["ok"]
        assert "Shock" in library.read_text(encoding="utf-8"), "the revert restored it"

    def test_revert_with_no_backup_is_a_clean_409_not_a_crash(self, library):
        c = app.app.test_client()
        r = c.post("/api/revert")
        assert r.status_code == 409
        assert "No backup" in r.get_json()["errors"][0]

    def test_add_appends_a_mana_row_so_inv02_holds(self, library, monkeypatch):
        """The INV-02 half of `/api/add`, offline: a new library name must gain a
        card-mana.csv row in the same request or the gate goes red on the next run."""
        monkeypatch.setattr(app, "_lookup_card", lambda n: (None, "offline"))
        c = app.app.test_client()
        r = c.post("/api/add",
                   data=json.dumps({"name": "Opt", "set": "M21", "collector": "59",
                                    "quantity": "1"}),
                   headers={"Content-Type": "application/json"})
        assert r.status_code == 200 and r.get_json()["ok"], r.get_json()
        assert "Opt" in library.read_text(encoding="utf-8")
        mana = os.path.join(os.path.dirname(str(library)), "card-mana.csv")
        assert "Opt" in open(mana, encoding="utf-8").read(), "INV-02: no mana row written"
