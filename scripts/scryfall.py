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
import socket
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
_TRANSIENT = (socket.timeout, TimeoutError, ConnectionError,
              json.JSONDecodeError, urllib.error.URLError)


class NotFound(Exception):
    """Scryfall reached, but the resource does not exist (HTTP 404)."""


class ScryfallUnavailable(Exception):
    """Scryfall unreachable / unusable after retries — transient, NOT 'no such
    card'. Callers should degrade (show unknown / warn), not treat it as a miss."""


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
            if attempt < retries - 1:
                wait = (float(e.headers.get("Retry-After", 0) or 0)
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
