"""Behavioral coverage for scripts/scryfall.py `_run` — the shared resilience layer
every Scryfall consumer depends on (G-14). Previously untested (BS-20/batch 6),
which mattered: its documented contract ("immediately for a non-retryable HTTP
status") and its code disagreed for a full cycle — a 400 got ~63s of backoff
before surfacing as a fake outage (fixed batch 5; pinned here). The network is
faked at urllib.request.urlopen; the retry/backoff/classification logic is real
(sleeps are stubbed out)."""
import io
import json
import sys
import os
import urllib.error

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import scryfall  # noqa: E402


def _http_error(code, headers=None):
    hdrs = {k: str(v) for k, v in (headers or {}).items()}

    class _H(dict):
        def get(self, k, d=None):
            return hdrs.get(k, d)
    return urllib.error.HTTPError("http://x", code, f"code {code}", _H(), io.BytesIO(b""))


class _Responder:
    """Scripted urlopen: pops one outcome per call; records how many were made."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def __call__(self, req, timeout=None):
        self.calls += 1
        out = self.outcomes.pop(0)
        if isinstance(out, Exception):
            raise out

        class _Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        return _Resp(json.dumps(out).encode())


@pytest.fixture(autouse=True)
def quiet_sleep(monkeypatch):
    monkeypatch.setattr(scryfall.time, "sleep", lambda s: None)


def _wire(monkeypatch, responder):
    monkeypatch.setattr(scryfall.urllib.request, "urlopen", responder)


class TestRunClassification:
    def test_success_returns_parsed_json(self, monkeypatch):
        r = _Responder([{"ok": True}])
        _wire(monkeypatch, r)
        assert scryfall.get_json("http://x") == {"ok": True}
        assert r.calls == 1

    def test_404_raises_NotFound_immediately(self, monkeypatch):
        """404 is 'no such card' — a MISS, never an outage; consumers must be able
        to tell the two apart (writing a blank for an outage is data loss)."""
        r = _Responder([_http_error(404)])
        _wire(monkeypatch, r)
        with pytest.raises(scryfall.NotFound):
            scryfall.get_json("http://x")
        assert r.calls == 1

    def test_400_is_not_retried(self, monkeypatch):
        """The batch-5 pin: a malformed query is a 400 EVERY time. It used to get
        6 attempts of backoff (~63s) and then surface as 'could not reach
        Scryfall' — a permanent client error misdiagnosed as an outage."""
        r = _Responder([_http_error(400)] * 6)
        _wire(monkeypatch, r)
        with pytest.raises(scryfall.ScryfallUnavailable) as e:
            scryfall.get_json("http://x")
        assert r.calls == 1
        assert "client error" in str(e.value)

    def test_429_retries_and_then_succeeds(self, monkeypatch):
        r = _Responder([_http_error(429, {"Retry-After": "0"}), {"ok": 1}])
        _wire(monkeypatch, r)
        assert scryfall.get_json("http://x") == {"ok": 1}
        assert r.calls == 2

    def test_5xx_retries_then_raises_unavailable(self, monkeypatch):
        r = _Responder([_http_error(503)] * 3)
        _wire(monkeypatch, r)
        with pytest.raises(scryfall.ScryfallUnavailable):
            scryfall.get_json("http://x", retries=3)
        assert r.calls == 3

    def test_timeout_is_transient_not_a_crash(self, monkeypatch):
        """G-14's founding incident: a read TIMEOUT is not a URLError — it must
        map to ScryfallUnavailable so interactive tools degrade, not traceback."""
        r = _Responder([TimeoutError("read timed out")] * 2)
        _wire(monkeypatch, r)
        with pytest.raises(scryfall.ScryfallUnavailable):
            scryfall.get_json("http://x", retries=2)
        assert r.calls == 2

    def test_transient_then_success_recovers(self, monkeypatch):
        r = _Responder([TimeoutError("blip"), {"ok": 2}])
        _wire(monkeypatch, r)
        assert scryfall.get_json("http://x") == {"ok": 2}
