#!/usr/bin/env python3
"""Shared, resilient Scryfall HTTP client.

Every Scryfall call in this toolkit should go through here so a slow, flaky, or
rate-limited Scryfall degrades cleanly instead of crashing or silently returning
wrong data. The hand-rolled retry snippets this replaces caught only
HTTPError/URLError, so a socket read-timeout (socket.timeout / TimeoutError,
raised while reading the response body — not the connect) or a truncated/garbled
body (json.JSONDecodeError) escaped the handler and crashed the caller — the
opposite of the "degrade to unknown" behaviour those callers advertised
(audit findings F1 / F11 / F14, systemic root F16).

Two DISTINCT failure signals, because callers must never conflate them:
  * NotFound            – Scryfall answered 404: the card/resource doesn't exist.
  * ScryfallUnavailable – Scryfall couldn't be reached or returned an unusable
                          response after retries (429/5xx, connection reset,
                          read-timeout, undecodable body). Transient — the caller
                          should show "unknown" / warn, NOT record a real miss.

Pure standard library, and no network at import time, so check_all.py / CI stay
offline and dependency-free.
"""

import json
import http.client
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "mtga-card-library/1.0"
COLLECTION_URL = "https://api.scryfall.com/cards/collection"
NAMED_URL = "https://api.scryfall.com/cards/named"

# Transient connection/read failures worth retrying. HTTPError is handled
# separately (it's a URLError subclass, caught first). json.JSONDecodeError covers
# a truncated/garbled body; socket.timeout/TimeoutError a slow body read.
#
# The last two were escaping (broad-scan Batch G). This module's whole premise is
# that a failure while READING the response body becomes ScryfallUnavailable so
# callers degrade instead of crashing — and:
#   * http.client.IncompleteRead is the truncated-chunked-body case json.JSONDecodeError
#     was added for, raised one layer LOWER, so it never reached the decoder.
#   * ssl.SSLError (a TLS reset mid-body) subclasses OSError, NOT ConnectionError,
#     so it slipped past every entry here.
# Verified by issubclass against the old tuple: both False. A --refetch
# `build_mana.py --pool` dropping TLS at page 40 raised a traceback past main()'s
# `except ScryfallUnavailable` — no data loss, but no clean abort and no retry either.
_TRANSIENT = (socket.timeout, TimeoutError, ConnectionError,
              json.JSONDecodeError, urllib.error.URLError,
              http.client.IncompleteRead, ssl.SSLError)


class NotFound(Exception):
    """Scryfall reached, but the resource does not exist (HTTP 404)."""


class ScryfallUnavailable(Exception):
    """Scryfall unreachable / unusable after retries — transient, NOT 'no such
    card'. Callers should degrade (show unknown / warn), not treat it as a miss."""


def _retry_after_seconds(headers):
    """`Retry-After` as a float delay, or 0.0 when it is absent or unusable.

    RFC 7231 allows Retry-After in TWO forms — delay-seconds AND an HTTP-date — and this
    was a bare `float(...)`, so the date form raised ValueError INSIDE the HTTPError
    handler. That escapes both `_TRANSIENT` and `ScryfallUnavailable`, crossing this
    module's whole premise that every transport failure degrades to one exception type:
    the interactive tools would traceback instead of degrading and the rebuild scripts
    would abort on a traceback rather than a clean "existing file left unchanged"
    message. Not hypothetical here — this environment routes through an agent proxy that
    can inject its own 429/503 with its own headers (BS4-17).

    The date form is parsed rather than discarded (it is a legitimate server response),
    clamped to a sane ceiling so a far-future date can't park the process for hours.
    """
    raw = (headers.get("Retry-After") if headers else None)
    if raw is None:
        return 0.0
    raw = str(raw).strip()
    if not raw:
        return 0.0
    try:
        return max(0.0, float(raw))
    except ValueError:
        pass
    try:
        from email.utils import parsedate_to_datetime
        when = parsedate_to_datetime(raw)
    except Exception:
        return 0.0
    if when is None:
        return 0.0
    try:
        import datetime as _dt
        now = _dt.datetime.now(_dt.timezone.utc)
        if when.tzinfo is None:
            when = when.replace(tzinfo=_dt.timezone.utc)
        return max(0.0, min((when - now).total_seconds(), _RETRY_AFTER_CAP))
    except Exception:
        return 0.0


# A server (or a proxy) can name a far-future Retry-After; honouring it literally would
# park a rebuild for hours, so the date form is capped at the longest ordinary backoff.
_RETRY_AFTER_CAP = 60.0


def _run(req, retries=6, timeout=30):
    """Execute a urllib Request with retry/backoff; return parsed JSON.

    Raises NotFound on 404, ScryfallUnavailable on any transient failure once
    retries are exhausted (or immediately for a non-retryable HTTP status)."""
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise NotFound()
            last = f"HTTP {e.code}: {e.reason}"
            # 429 (rate limit) and 5xx are worth retrying; honour Retry-After on 429.
            # Any OTHER 4xx is a permanent CLIENT error (a malformed --query is a
            # 400 every time) — the docstring promised an immediate raise, but only
            # 404 short-circuited, so a bad query burned ~63s of backoff before
            # surfacing as "could not reach Scryfall", misdiagnosing a permanent
            # error as an outage (broad-scan batch 5).
            if 400 <= e.code < 500 and e.code != 429:
                raise ScryfallUnavailable(last + " (client error — not retried; "
                                          "check the request, not the network)")
            if attempt < retries - 1:
                wait = (_retry_after_seconds(e.headers)
                        if e.code == 429 else 0) or 1.0 * (2 ** attempt)
                time.sleep(wait)
                continue
            raise ScryfallUnavailable(last)
        except _TRANSIENT as e:  # HTTPError handled above, so it won't land here
            last = str(e) or e.__class__.__name__
            if attempt < retries - 1:
                time.sleep(1.0 * (2 ** attempt))
                continue
            raise ScryfallUnavailable(last)
    raise ScryfallUnavailable(last or "exhausted retries")


def _headers(post=False):
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if post:
        h["Content-Type"] = "application/json"
    return h


def get_json(url, **kw):
    """GET a Scryfall URL as JSON. Raises NotFound (404) / ScryfallUnavailable."""
    return _run(urllib.request.Request(url, headers=_headers()), **kw)


def post_json(url, payload, **kw):
    """POST a JSON payload and return the parsed JSON response."""
    body = json.dumps(payload).encode("utf-8")
    return _run(urllib.request.Request(url, data=body, headers=_headers(post=True)), **kw)


def post_collection(names, **kw):
    """Batch /cards/collection lookup by name. Returns the parsed JSON (never 404s
    — unmatched names come back in the response's `not_found` list)."""
    return post_json(COLLECTION_URL, {"identifiers": [{"name": n} for n in names]}, **kw)


def named(params, **kw):
    """GET /cards/named (exact / fuzzy / set params). Raises NotFound on 404."""
    return get_json(NAMED_URL + "?" + urllib.parse.urlencode(params), **kw)
