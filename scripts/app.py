#!/usr/bin/env python3
"""Local, browser-based editor for card-library.csv (OPTIONAL Flask app).

This is the one part of the toolkit with a dependency (Flask). The core scripts
stay pure standard library; nothing here is imported by them or by check_all.py.

An editable grid: it serves your collection with card art (from
image-manifest.json), lets you search/filter, and shows each card's Quantity
Owned and Synergies as inline fields with live "dirty" tracking. You can also
add a printing (auto-enriched from Scryfall), remove one, and revert the last
save. Every mutation goes through the same safe path — rows are written to a
temp file and run through validate() first; only if that passes is the current
CSV backed up to a timestamped .bak and atomically replaced — so a bad edit
can't corrupt the inventory. Adding a card also appends a card-mana.csv row so
the integrity gate's INV-02 stays satisfied.

The /decks pages edit decks with live buildability: as you change quantities or
add/remove cards, owned-vs-needed updates in the browser. You can edit the `#:`
metadata fields, create a new numbered deck, and open Stats/Mana/Tribes/
Suggestions analysis tabs (deck.py output). Saving writes the deck's .txt file
through the same validated, backed-up, atomic path, gated on INV-04 (the file
must re-parse with every card line intact) and preserving the file's section
comments.

Run:
    make app                     # venv + install + launch + open browser (one command)
    # ...or manually:
    pip install -r requirements-app.txt
    python3 scripts/app.py                 # opens http://127.0.0.1:5000 in your browser
    python3 scripts/app.py --port 8000 --no-browser

Bound to 127.0.0.1 by default — it's a personal, local tool, so there's no auth.
"""

import argparse
import contextlib
import csv
import datetime
import functools
import hashlib
import html
import io
import json
import os
import re
import shutil
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

try:
    from flask import Flask, jsonify, request
except ModuleNotFoundError:
    import sys
    sys.stderr.write(
        "This editor needs Flask, which isn't installed. Install it with:\n"
        "    pip install -r requirements-app.txt\n"
        "or just run `make app`, which sets up an isolated venv for you.\n")
    raise SystemExit(1)

import deck as deckmod
import scryfall
from scryfall import ScryfallUnavailable
from lib import (DEFAULT_CSV, REPO_ROOT, load_rows, write_rows, atomic_write, backup_path,
                 latest_backup as backup_path_latest, card_colors)
from validate import validate

MANIFEST_PATH = os.path.join(REPO_ROOT, "image-manifest.json")
TEMPLATE_PATH = os.path.join(REPO_ROOT, "templates", "collection.html")
MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")

app = Flask(__name__)

# Werkzeug's dev server is threaded, so mutating endpoints can run concurrently.
# Each does load → modify → write with no coordination, so two overlapping requests
# can lose an update (the second write clobbers the first) — widened by the in-band
# Scryfall lookup in add(). Serialize every write through one lock (audit F13). This
# is a single-user local tool, so full serialization is fine; the only cost is that
# a save waits behind an in-flight add's Scryfall call (bounded by its short timeout).
_WRITE_LOCK = threading.Lock()


def _serialized(fn):
    """Run a mutating request handler under the global write lock (audit F13)."""
    @functools.wraps(fn)
    def wrapper(*a, **k):
        with _WRITE_LOCK:
            return fn(*a, **k)
    return wrapper


# ── Request guard: same-origin + loopback-Host (audit F-10) ─────────────────────
# This editor has no auth by design (personal, localhost). That is fine for someone
# who can already reach the port, but it left two browser-driven holes open:
#
#   * CSRF. Most endpoints are accidentally safe because `request.get_json(silent=True)`
#     returns None for the content types an HTML form can send, so they 400. But
#     `/api/revert` reads no body at all — a plain cross-origin
#     `<form method="POST" action="http://127.0.0.1:5000/api/revert">` on ANY page
#     visited while the editor is running would roll the collection back.
#   * DNS rebinding. With no Host check, a hostile name resolving to 127.0.0.1 can
#     script the editor (and read the whole collection) from a page the user visits.
#
# Both are closed here rather than per-endpoint, so a future route can't forget.
_LOCAL_HOSTNAMES = {"127.0.0.1", "localhost", "::1"}
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_bind_host = "127.0.0.1"   # set by main(); a deliberate non-local bind relaxes the Host check


def _hostname_of(netloc):
    """Bare hostname from a `host[:port]` / `[v6]:port` string ('' if unparseable)."""
    return (urllib.parse.urlsplit("//" + (netloc or "")).hostname or "").lower()


def _authority(netloc):
    """(hostname, port) from a `host[:port]` string — the comparable identity of an
    origin. Split out so the same-origin test reads as one comparison."""
    parts = urllib.parse.urlsplit("//" + (netloc or ""))
    return ((parts.hostname or "").lower(), parts.port)


def _same_origin(origin, host):
    """True when an `Origin` header denotes the same host:port we're serving on.
    `Origin: null` (a file:// or sandboxed page) parses to an empty authority and is
    correctly rejected."""
    o = urllib.parse.urlsplit(origin or "")
    return bool(o.hostname) and _authority(o.netloc) == _authority(host)


@app.before_request
def _guard_request():
    # (1) Host must be a loopback name when we're bound to loopback. A rebinding
    #     attack arrives with an attacker-controlled Host, so this rejects it while
    #     leaving normal 127.0.0.1 / localhost use untouched.
    if _hostname_of(_bind_host) in _LOCAL_HOSTNAMES:
        if _hostname_of(request.host) not in _LOCAL_HOSTNAMES:
            return jsonify(ok=False, errors=[
                f"Refused: unexpected Host {request.host!r}. This editor only serves "
                "loopback hosts (127.0.0.1 / localhost) — see DNS-rebinding note in "
                "app.py."]), 403
    # (2) A state-changing request must be same-origin. Browsers send `Origin` on every
    #     cross-site POST, including form posts, and `Origin: null` from a file:// or
    #     sandboxed page — both fail this check. A request with NO Origin at all is a
    #     non-browser client (curl, a script), which CSRF doesn't apply to.
    if request.method not in _SAFE_METHODS:
        origin = request.headers.get("Origin")
        if origin is not None and not _same_origin(origin, request.host):
            return jsonify(ok=False, errors=[
                f"Refused: cross-origin {request.method} from {origin!r}. Use the editor "
                "in its own tab; another site cannot post to it."]), 403
    return None


def load_manifest():
    """name_lower -> image URL, from the committed manifest (may be absent)."""
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def build_cards():
    """Shape card-library.csv rows into the card objects the page consumes.

    (name, set, cn) is the printing key the save step will match on in Phase 2.
    """
    _, rows = load_rows(DEFAULT_CSV)
    manifest = load_manifest()
    cards = []
    for r in rows:
        name = (r.get("Card Name") or "").strip()
        if not name:
            continue
        color_str = (r.get("Color(s)") or "").strip()
        # Route through lib.card_colors so the literal "Colorless" reads as no colors,
        # not {'R'} (the word contains an R — audit F1); the CLI/dashboard already guard
        # this, and the editor grid must agree.
        letters = sorted(card_colors(color_str)) or ["C"]
        cards.append({
            "name": name,
            "type": (r.get("Type") or "").strip(),
            "text": (r.get("Card Text") or "").strip(),
            "colorStr": color_str,
            "colors": letters,
            "synergies": (r.get("Synergies") or "").strip(),
            "set": (r.get("Set Code") or "").strip(),
            "cn": (r.get("Collector #") or "").strip(),
            "qty": (r.get("Quantity Owned") or "").strip(),
            "img": manifest.get(name.lower(), ""),
        })
    return cards


def render_page():
    """Read the static template and inject the card data as JSON.

    We string-replace a placeholder (not Jinja) so the page's CSS/JS braces need
    no escaping. "<" is escaped so a card field can't break out of the <script>
    data block (same guard as build_gallery.py).
    """
    with open(TEMPLATE_PATH, encoding="utf-8") as fh:
        template = fh.read()
    data_json = json.dumps(build_cards(), ensure_ascii=False).replace("<", "\\u003c")
    return template.replace("__DATA__", data_json)


@app.route("/")
def index():
    return render_page()


# --------------------------------------------------------------------------- #
# Safe write + card-mana maintenance (shared by save / add / remove)
# --------------------------------------------------------------------------- #
def _backup_path(target):
    """A unique timestamped `.bak` path for `target` — delegates to the shared
    `lib.backup_path` so every backup in the toolkit uses one collision-free,
    sort-safe naming scheme (audit F22). `revert` selects the newest via
    `lib.latest_backup`, which keys on the CREATION stamp in the NAME — never on
    mtime, which `shutil.copy2` copies from the source and which broke a
    revert→save→revert sequence (broad-scan F-04)."""
    return backup_path(target)


def _safe_write(rows):
    """Validate rows in a temp file, then back up + atomically replace the CSV.

    Returns (ok, backup_basename_or_None, errors). The real CSV is only touched
    once the temp file passes validate(), and the swap is atomic.
    """
    target = os.path.abspath(DEFAULT_CSV)
    fd, tmp = tempfile.mkstemp(suffix=".csv", dir=os.path.dirname(target))
    os.close(fd)
    try:
        write_rows(rows, tmp, backup=False)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = validate(tmp)
        if rc != 0:
            tail = [ln for ln in buf.getvalue().splitlines() if ln.strip()][-8:]
            return False, None, ["Validation failed — nothing written.", *tail]
        backup = _backup_path(target)
        shutil.copy2(target, backup)
        os.replace(tmp, target)
        tmp = None
        return True, os.path.basename(backup), []
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


def _mana_has(name):
    """True if card-mana.csv already has a row for this name (case-insensitive)."""
    if not os.path.exists(MANA_CSV):
        return False
    nl = name.strip().lower()
    with open(MANA_CSV, newline="", encoding="utf-8") as fh:
        return any((r.get("Card Name") or "").strip().lower() == nl
                   for r in csv.DictReader(fh))


def _pool_has(name):
    """True if `name` is a card-pool.csv row (full name or DFC front). A mana row for a
    POOL card is legitimate even with nothing in the library — `build_mana.py --pool`
    covers the whole pool — so pruning must never touch one."""
    pool = os.path.join(REPO_ROOT, "card-pool.csv")
    if not os.path.exists(pool):
        return False
    nl = name.strip().lower()
    with open(pool, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            if n == nl or n.split(" // ")[0] == nl:
                return True
    return False


def _prune_mana(name, rows):
    """Drop `name`'s card-mana.csv row after its LAST library printing was removed.

    `remove()` used to leave the row behind, reasoning that a spare row is harmless
    (INV-02 only requires library names to be PRESENT in the mana file). True for the
    invariant, but repeated add/remove cycles accumulate orphans, and a stale row is
    worse than untidy: `add()` skips writing a mana row when `_mana_has()` is true, so
    a BLANK row left by an offline add suppresses the real one on a later re-add.

    Two guards keep this conservative — prune only when the name is gone from the
    library (`rows` is the post-removal set) AND is not a pool card, since a pool-scoped
    mana file legitimately carries rows no library card references. Returns True if a
    row was dropped."""
    nl = name.strip().lower()
    if any((r.get("Card Name") or "").strip().lower() == nl for r in rows):
        return False                      # another printing still needs it (INV-02)
    if not os.path.exists(MANA_CSV) or _pool_has(name):
        return False
    with open(MANA_CSV, newline="", encoding="utf-8") as fh:
        mana = [r for r in csv.reader(fh)]
    if not mana:
        return False
    header, body = mana[0], mana[1:]
    kept = [r for r in body if not (r and (r[0] or "").strip().lower() == nl)]
    if len(kept) == len(body):
        return False
    atomic_write(MANA_CSV, lambda fh: csv.writer(fh).writerows([header] + kept))
    return True


def _append_mana(name, cost, mv, keywords):
    """Append a card-mana.csv row so INV-02 (every library name has a mana row)
    holds after an add — even if enrichment was offline (then cost/kw are blank,
    and a later build_mana.py/refresh fills them in).

    Reads the file, appends in memory, and rewrites atomically (temp + os.replace),
    so a crash mid-write can't leave a half-written or header-less mana file — the
    plain ``open("a")`` append also mis-treated an existing-but-empty file as already
    having a header (audit F11)."""
    rows = []
    if os.path.exists(MANA_CSV):
        with open(MANA_CSV, newline="", encoding="utf-8") as fh:
            rows = [r for r in csv.reader(fh)]
    if not rows:
        rows = [["Card Name", "Mana Cost", "Mana Value", "Keywords"]]
    rows.append([name, cost or "", mv if isinstance(mv, int) else "", keywords or ""])
    # Back the mana file up to a timestamped .bak like every other canonical-CSV
    # mutation (CLAUDE.md's atomic_write + backup invariant); the previous backup=False
    # skipped it (audit A12). backup=True is atomic_write's default.
    atomic_write(MANA_CSV, lambda fh: csv.writer(fh).writerows(rows))


def _lookup_card(name):
    """One-shot, best-effort Scryfall lookup for a single card (exact name, short
    timeout, minimal retry — keeps 'add' snappy). Returns (fields|None, status) where
    status is 'ok' | 'miss' (no such card) | 'offline' (Scryfall unreachable). Never
    raises.

    Goes through the shared `scryfall` client. The hand-rolled urllib call this
    replaces caught only ``(URLError, ValueError)``, but a READ timeout — the common
    slow-Scryfall case — raises ``TimeoutError``/``socket.timeout``, an OSError that is
    NOT a URLError subclass. So it escaped the handler and turned /api/add into a 500
    instead of the name-only add the endpoint advertises: precisely the failure class
    scryfall.py's docstring says it exists to eliminate (audit F-09). `retries=1,
    timeout=10` preserves the original snappiness rather than inheriting the client's
    6-retry rebuild defaults."""
    from enrich import oracle_fields, color_shorthand
    try:
        card = scryfall.named({"exact": name}, retries=1, timeout=10)
    except scryfall.NotFound:
        return None, "miss"
    except ScryfallUnavailable:
        return None, "offline"
    type_line, text = oracle_fields(card)
    mc = card.get("mana_cost")
    if not mc and card.get("card_faces"):
        mc = card["card_faces"][0].get("mana_cost", "")
    mv = card.get("cmc", 0)
    return {
        "name": card.get("name") or name,
        "type": type_line, "text": text, "color": color_shorthand(card),
        "set": (card.get("set") or "").lower(),
        "collector": str(card.get("collector_number") or ""),
        "mana_cost": mc or "", "mv": int(mv) if isinstance(mv, (int, float)) else "",
        "keywords": ";".join(card.get("keywords") or []),
    }, "ok"


def _list_of_objs(x):
    """True iff x is a list whose every element is a JSON object (dict). Guards the
    mutating endpoints so a payload like [1, 2, 3] returns a clean 400 instead of a
    500 when the handler calls .get() on a non-dict element (audit F9)."""
    return isinstance(x, list) and all(isinstance(e, dict) for e in x)


@app.route("/api/save", methods=["POST"])
@_serialized
def save():
    """Persist edited Quantity Owned / Synergies back to card-library.csv.

    Safety flow, so a bad edit can never corrupt the inventory:
      1. field-validate quantities (blank or non-negative int) up front;
      2. fresh-load the CSV and apply edits by (name, set, collector) key —
         only the two editable columns are touched;
      3. write the result to a temp file in the SAME directory and run the
         project's validate() on it;
      4. only if clean: back up the current CSV to a timestamped .bak, then
         atomically os.replace() the temp file into place.
    On any failure the real CSV is left untouched and errors are returned.
    """
    edits = request.get_json(silent=True)
    if not _list_of_objs(edits):
        return jsonify(ok=False, errors=["Malformed request: expected a JSON list of edit objects."]), 400
    if not edits:
        return jsonify(ok=True, updated=0, backup=None)

    # 1. Field validation with clear, per-card messages.
    problems = []
    for e in edits:
        q = str(e.get("quantity", "")).strip()
        if q and not q.isdigit():
            nm = (e.get("key") or {}).get("name", "?")
            problems.append(f"{nm}: quantity {q!r} must be a non-negative integer or blank.")
    if problems:
        return jsonify(ok=False, errors=problems), 400

    # 2. Fresh-load + apply by printing key.
    _, rows = load_rows(DEFAULT_CSV)
    index = {}
    for r in rows:
        k = ((r.get("Card Name") or "").strip().lower(),
             (r.get("Set Code") or "").strip().lower(),
             (r.get("Collector #") or "").strip().lower())
        index[k] = r
    applied, missing = 0, []
    for e in edits:
        key = e.get("key") or {}
        k = ((key.get("name") or "").strip().lower(),
             (key.get("set") or "").strip().lower(),
             (key.get("collector") or "").strip().lower())
        row = index.get(k)
        if row is None:
            missing.append(key.get("name", "?"))
            continue
        row["Quantity Owned"] = str(e.get("quantity", "")).strip()
        row["Synergies"] = str(e.get("synergies", "")).strip()
        applied += 1
    if missing:
        return jsonify(ok=False, errors=[f"No matching printing for: {', '.join(missing)} "
                                         "(reload the page — the CSV may have changed)."]), 409

    # 3/4. Temp write -> validate -> backup -> atomic promote.
    ok, backup, errors = _safe_write(rows)
    if not ok:
        return jsonify(ok=False, errors=errors), 400
    return jsonify(ok=True, updated=applied, backup=backup)


@app.route("/api/add", methods=["POST"])
@_serialized
def add():
    """Add a new printing to the collection.

    Best-effort Scryfall enrichment fills Type/Card Text/Color(s)/Synergies (and
    the Collector # when the set matches). Crucially, it also appends a
    card-mana.csv row for the new name so INV-02 stays satisfied — offline, a
    blank mana row is written and a later refresh fills it in.
    """
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    set_code = str(data.get("set", "")).strip()
    collector = str(data.get("collector", "")).strip()
    qty = str(data.get("quantity", "")).strip()
    if not name:
        return jsonify(ok=False, errors=["Card Name is required."]), 400
    if qty and not qty.isdigit():
        return jsonify(ok=False, errors=[f"Quantity {qty!r} must be a non-negative integer or blank."]), 400

    _, rows = load_rows(DEFAULT_CSV)
    want = (name.lower(), set_code.lower(), collector.lower())
    for r in rows:
        rk = ((r.get("Card Name") or "").strip().lower(),
              (r.get("Set Code") or "").strip().lower(),
              (r.get("Collector #") or "").strip().lower())
        if rk == want:
            return jsonify(ok=False, errors=[f"That printing already exists: "
                                             f"{name} ({set_code or '—'}) {collector}."]), 409

    info, enrich_status = _lookup_card(name)
    enriched = info is not None
    if info:
        from enrich import SET_ALIASES
        from tag_synergies import tags_for
        # The library keys a double-faced card under its FRONT name only (matching
        # reconcile_crafts.py and deck.py's owned() join); Scryfall returns the full
        # "Front // Back". Store the front face so ownership joins resolve and the
        # appended card-mana.csv row shares the same key (audit F6).
        stored = (info["name"] or "").split(" // ")[0]
        row_set = SET_ALIASES.get(set_code.lower(), set_code.lower()) if set_code else ""
        coll = collector or (info["collector"] if (row_set and info["set"] == row_set) else "")
        synergies = "; ".join(tags_for({"Type": info["type"], "Card Text": info["text"]},
                                       [k for k in info["keywords"].split(";") if k]))
        new = {"Card Name": stored, "Type": info["type"], "Card Text": info["text"],
               "Color(s)": info["color"], "Synergies": synergies,
               "Set Code": set_code, "Collector #": coll, "Quantity Owned": qty}
    else:
        stored = name
        new = {"Card Name": stored, "Type": "", "Card Text": "", "Color(s)": "",
               "Synergies": "", "Set Code": set_code, "Collector #": collector,
               "Quantity Owned": qty}

    rows.append(new)
    ok, backup, errors = _safe_write(rows)
    if not ok:
        return jsonify(ok=False, errors=errors), 400
    # Only NOW keep INV-02 intact by appending a card-mana.csv row for the new
    # name. Doing it after the library write succeeds avoids leaving an orphan
    # mana row when the add is rejected by validation (audit F7); offline, a blank
    # row is written and a later build_mana.py/refresh fills in cost/keywords.
    if not _mana_has(stored):
        try:
            if info:
                _append_mana(stored, info["mana_cost"], info["mv"], info["keywords"])
            else:
                _append_mana(stored, "", "", "")
        except Exception as e:
            # The library write already landed; if the mana-row write fails we'd leave
            # a card with no mana row (INV-02). Roll the library back to the .bak
            # _safe_write just made, so the add is all-or-nothing (audit F11).
            #
            # Staged restore, NOT a bare copy2 over the target (BS2-27): this branch
            # is reached exactly when a write just FAILED — disk full, permissions —
            # which is when a direct copy is likeliest to die mid-write and leave a
            # truncated card-library.csv behind an error message claiming a clean
            # rollback. `revert()` above stages into a temp and os.replace()s for
            # precisely this reason (its comment says so); this was the one restore
            # path that didn't.
            if backup:
                target = os.path.abspath(DEFAULT_CSV)
                bpath = os.path.join(os.path.dirname(target), backup)
                if os.path.exists(bpath):
                    fd, tmp = tempfile.mkstemp(suffix=".csv", dir=os.path.dirname(target))
                    os.close(fd)
                    try:
                        shutil.copy2(bpath, tmp)
                        os.replace(tmp, target)
                        tmp = None
                    finally:
                        if tmp and os.path.exists(tmp):
                            os.remove(tmp)
            return jsonify(ok=False, errors=[
                f"Card written but its card-mana.csv row failed ({e}); rolled the "
                "library add back to keep INV-02. Try again."]), 500
    # `enrich_status` distinguishes a real miss (check the spelling) from a transient
    # outage (the blanks will fill in on a later build_mana/refresh) — the same
    # distinction wishlist.py draws, rather than reporting both as "not enriched".
    return jsonify(ok=True, backup=backup, enriched=enriched, name=stored,
                   enrich_status=enrich_status)


@app.route("/api/remove", methods=["POST"])
@_serialized
def remove():
    """Remove a single printing (by name/set/collector key) from the collection.

    When that was the card's LAST printing, its card-mana.csv row is pruned too (see
    `_prune_mana`) — but only if the card isn't in the pool, since a pool-scoped mana
    file legitimately carries rows the library doesn't reference.
    """
    data = request.get_json(silent=True) or {}
    key = data.get("key") or {}
    want = ((key.get("name") or "").strip().lower(),
            (key.get("set") or "").strip().lower(),
            (key.get("collector") or "").strip().lower())
    _, rows = load_rows(DEFAULT_CSV)
    kept, removed = [], False
    for r in rows:
        rk = ((r.get("Card Name") or "").strip().lower(),
              (r.get("Set Code") or "").strip().lower(),
              (r.get("Collector #") or "").strip().lower())
        if rk == want and not removed:
            removed = True
            continue
        kept.append(r)
    if not removed:
        return jsonify(ok=False, errors=["No matching printing to remove "
                                         "(reload the page — the CSV may have changed)."]), 409
    ok, backup, errors = _safe_write(kept)
    if not ok:
        return jsonify(ok=False, errors=errors), 400
    # Only AFTER the library write lands, so a rejected removal can't strand the mana
    # file out of step with it (the ordering `add()` uses for the same reason).
    pruned = _prune_mana((key.get("name") or ""), kept)
    return jsonify(ok=True, backup=backup, removed=key.get("name"), mana_pruned=pruned)


@app.route("/api/revert", methods=["POST"])
@_serialized
def revert():
    """Undo the last save by restoring the most recent .bak snapshot.

    The backup is validated before it's restored. Other .bak files are left in
    place (gitignored), so nothing is permanently lost.
    """
    target = os.path.abspath(DEFAULT_CSV)
    d, base = os.path.dirname(target), os.path.basename(target)
    baks = [f for f in os.listdir(d)
            if f.startswith(base + ".") and f.endswith(".bak")]
    if not baks:
        return jsonify(ok=False, errors=["No backup to revert to yet — nothing has been saved."]), 409
    # Newest by the CREATION stamp in the name, via the shared `lib.latest_backup`. This
    # used to select on mtime, which is wrong for a file made by `shutil.copy2`: copy2
    # copies the SOURCE's mtime, so after one revert (which restores an old-mtime file)
    # the next save's backup carries that old mtime and sorts before newer ones — and the
    # revert after that restored the very state the first revert discarded (broad-scan
    # F-04). `latest_backup` still falls back to mtime for unstamped legacy names.
    newest = backup_path_latest([os.path.join(d, f) for f in baks])
    newest_base = os.path.basename(newest)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = validate(newest)
    if rc != 0:
        return jsonify(ok=False, errors=[f"Backup {newest_base} failed validation; not restoring."]), 400
    # Snapshot the CURRENT state before clobbering it, so a revert is itself
    # undoable (audit F5) — otherwise the pre-revert inventory is lost. Then
    # restore atomically: stage the backup into a temp file and os.replace() it
    # in, so an interruption mid-restore can't leave a truncated CSV.
    if os.path.exists(target):
        shutil.copy2(target, _backup_path(target))
    fd, tmp = tempfile.mkstemp(suffix=".csv", dir=d)
    os.close(fd)
    try:
        shutil.copy2(newest, tmp)
        os.replace(tmp, target)
        tmp = None
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)
    # Report the file actually restored (newest by mtime), not the lexically-last
    # name — they can differ under legacy/mixed .bak naming (audit A13).
    return jsonify(ok=True, restored=newest_base)


# --------------------------------------------------------------------------- #
# Deck editing (live buildability)
# --------------------------------------------------------------------------- #
def _render_template(filename, replacements):
    # `src`, NOT `html`: the local used to shadow the `html` MODULE (imported for
    # escaping, the BS-09 fix) inside the one function whose whole job is emitting
    # HTML — so the next person adding `html.escape(...)` here would get a runtime
    # AttributeError on a str (Batch D minor).
    with open(os.path.join(REPO_ROOT, "templates", filename), encoding="utf-8") as fh:
        src = fh.read()
    for k, v in replacements.items():
        src = src.replace(k, v)
    return src


def _decks_overview():
    """Per-deck buildability summary for the deck-list page."""
    _, _, by_name_qty = deckmod.load_collection()
    out = []
    for d in deckmod.discover_decks():
        _, cards = deckmod.parse_deck_file(d["path"])
        total = sum(q for q, *_ in cards)
        short = missing = 0
        for q, n, s, c in cards:
            have, found = deckmod.owned(by_name_qty, n)
            if not found:
                missing += 1
            elif have < q:
                short += 1
        out.append({"id": d["id"], "name": d["name"] or d["id"], "unique": len(cards),
                    "total": total, "short": short, "missing": missing,
                    "variant": bool(d["variant"])})
    return out


def _parse_deck_doc(path):
    """Split a deck file into (meta, body). meta is an ordered list of
    {key, value} from the `#:` header; body preserves comments/blank/card lines so
    the editor round-trips a deck without flattening its section comments."""
    meta, body = [], []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            s = line.strip()
            mm = deckmod.META_RE.match(s)
            if mm:
                meta.append({"key": mm.group(1).lower(), "value": mm.group(2).strip()})
                continue
            if not s or s.startswith("#"):
                body.append({"kind": "other", "raw": line})
                continue
            cm = deckmod.LINE_RE.match(line.split("#", 1)[0].strip())
            if cm:
                body.append({"kind": "card", "qty": int(cm.group(1)), "name": cm.group(2).strip(),
                             "set": (cm.group(3) or "").strip(), "cn": (cm.group(4) or "").strip()})
            else:
                body.append({"kind": "other", "raw": line})
    return meta, body


def _serialize_doc(meta, body):
    """Reassemble a deck file: `#:` header lines, a blank, then the body."""
    out = [f"#: {k}: {(p.get('value') or '').strip()}"
           for p in meta for k in [(p.get("key") or "").strip()] if k]
    b = list(body)
    while b and b[0].get("kind") == "other" and not (b[0].get("raw") or "").strip():
        b.pop(0)  # avoid a double blank between header and body
    if out and b:
        out.append("")
    for t in b:
        if t.get("kind") == "card":
            name = (t.get("name") or "").strip()
            if not name:
                continue
            qty = str(t.get("qty", "")).strip() or "1"
            s = (t.get("set") or "").strip()
            cn = (t.get("cn") or "").strip()
            row = f"{qty} {name}"
            if s:
                row += f" ({s})" + (f" {cn}" if cn else "")
            out.append(row)
        else:
            out.append(t.get("raw", ""))
    return "\n".join(out).rstrip("\n") + "\n"


def _validate_meta(meta):
    """Errors for `#:` header fields that would not survive the round-trip (BS2-28).

    `_serialize_doc` emits `#: {key}: {value}` for whatever the user typed, and
    nothing re-checked it: a key `deck.META_RE` cannot parse (`tier2`, `uncastable
    ok` — plausible, since `#: uncastable-ok:` is a real header) SAVED fine, toasted
    "Saved N card lines", passed INV-04 — and on the next load `_parse_deck_doc`
    filed the line under {kind: "other"}, rendering it as a grey comment while
    deck.py never saw the header at all. A success confirmation for a field the
    editor silently disabled. The key grammar is META_RE's own: a letter/underscore
    then letters/underscores/hyphens — no spaces, no digits."""
    errs = []
    for p in meta:
        k = (p.get("key") or "").strip()
        v = (p.get("value") or "").strip()
        if not k:
            if v:
                errs.append(f"A header field with no NAME would be dropped (value "
                            f"{v[:40]!r}). Name it, or clear the value.")
            continue
        if not re.fullmatch(r"[A-Za-z_][A-Za-z_-]*", k):
            errs.append(f"Header field {k!r} is not a valid `#:` key (letters, "
                        f"underscores and hyphens only, starting with a letter — no "
                        f"spaces or digits). Saved as-is it would silently become a "
                        f"comment the tooling never reads. Rename it (e.g. "
                        f"{re.sub(r'[^A-Za-z_-]+', '-', k).strip('-') or 'field'!r}).")
    return errs


def _validate_body(body):
    """(ok, errors, ncards) for a deck body — quantities must be positive ints."""
    problems, n = [], 0
    for t in body:
        if t.get("kind") != "card":
            continue
        name = (t.get("name") or "").strip()
        if not name:
            continue  # blank card row is dropped
        q = str(t.get("qty", "")).strip()
        if not q.isdigit() or int(q) < 1:
            problems.append(f"{name}: quantity must be a positive integer (got {q!r}).")
        n += 1
    if problems:
        return False, problems, n
    if n == 0:
        return False, ["A deck needs at least one card line."], n
    return True, [], n


def _body_cards(body):
    """The (qty, name, set, cn) card tuples a deck-editor body intends, in order —
    to be matched EXACTLY against parse_deck_file() output. Mirrors _serialize_doc's
    own field handling (a collector # is only emitted when a set is present) so the
    check flags genuine round-trip corruption (a name containing '(' or '#'), not
    that serialization choice. Assumes _validate_body() already vetted the qtys."""
    out = []
    for t in body:
        if t.get("kind") != "card":
            continue
        name = (t.get("name") or "").strip()
        if not name:
            continue
        qty = str(t.get("qty", "")).strip() or "1"
        s = (t.get("set") or "").strip()
        cn = (t.get("cn") or "").strip()
        out.append((int(qty), name, s, cn if s else ""))
    return out


def _first_line_mismatch(parsed, expected):
    """Human-readable reason the re-parsed deck diverged from what was intended."""
    if len(parsed) != len(expected):
        return f"expected {len(expected)} card line(s) but {len(parsed)} parsed back."
    for got, want in zip(parsed, expected):
        if got != want:
            return (f"the line for {want[1]!r} re-parsed as name={got[1]!r} "
                    f"set={got[2]!r} #={got[3]!r} qty={got[0]}.")
    return "a card line changed on round-trip."


def _write_deck(path, text, expected, backup):
    """temp write -> INV-04 content-fidelity check -> optional .bak -> atomic
    replace. Returns (payload_dict, status).

    `expected` is the (qty, name, set, cn) tuples the editor intended; the file must
    re-parse to EXACTLY that — not merely the same line COUNT — so a card name that
    round-trips to a different card/set (e.g. one containing '(' or '#', which the
    parser treats as a set delimiter / comment) is rejected instead of silently
    corrupting the deck (audit F6)."""
    target = os.path.abspath(path)
    fd, tmp = tempfile.mkstemp(suffix=".txt", dir=os.path.dirname(target))
    os.close(fd)
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
        _, parsed = deckmod.parse_deck_file(tmp)
        if parsed != expected:
            return {"ok": False, "errors": [
                "Deck didn't round-trip cleanly — " + _first_line_mismatch(parsed, expected)
                + " Card names containing '(' or '#' aren't supported. Not saved."]}, 400
        bak = None
        if backup and os.path.exists(target):
            bak = _backup_path(target)
            shutil.copy2(target, bak)
        os.replace(tmp, target)
        tmp = None
        return {"ok": True, "backup": (os.path.basename(bak) if bak else None),
                "cards": len(expected)}, 200
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


def _run_deck_analysis(kind, deck_id):
    """Capture deck.py's stats/mana/tribes/suggest output for a deck as text."""
    fn = {"stats": deckmod.cmd_stats, "mana": deckmod.cmd_mana,
          "tribes": deckmod.cmd_tribes, "suggest": deckmod.cmd_suggest}.get(kind)
    if not fn:
        return None
    ns = argparse.Namespace(id=deck_id, limit=20, unowned=False)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            fn(ns)
        except Exception as e:  # analysis is best-effort; never 500 the page
            buf.write(f"\n[analysis error: {e}]")
    return buf.getvalue()


@app.route("/decks")
def decks():
    payload = json.dumps({"decks": _decks_overview()}, ensure_ascii=False).replace("<", "\\u003c")
    return _render_template("decks.html", {"__DATA__": payload})


def _doc_token(path):
    """Content hash of a deck file — the staleness token the editor echoes back on
    save (BS2-26). Content, not mtime: a revert restores old-mtime bytes (the F-04
    lesson), and it is the CONTENT the editor loaded that matters."""
    try:
        with open(path, "rb") as fh:
            return hashlib.sha1(fh.read()).hexdigest()[:16]
    except OSError:
        return ""


def _deck_payload(d, new=False):
    _, _, by_name_qty = deckmod.load_collection()
    if new:
        meta = [{"key": "name", "value": ""}, {"key": "format", "value": "Standard"},
                {"key": "colors", "value": ""}, {"key": "notes", "value": ""}]
        body, ident, name, fname = [], None, "New deck", "(unsaved)"
        flex, token = [], ""
    else:
        meta, body = _parse_deck_doc(d["path"])
        ident, name = d["id"], (d["name"] or d["id"])
        fname = os.path.relpath(d["path"], REPO_ROOT)
        flex = deckmod.parse_flex(d["path"])
        token = _doc_token(d["path"])
    return json.dumps({"id": ident, "name": name, "file": fname, "new": new,
                       "meta": meta, "body": body, "owned": by_name_qty,
                       "flex": flex, "basics": sorted(deckmod.BASICS),
                       "doc_token": token},
                      ensure_ascii=False).replace("<", "\\u003c")


@app.route("/deck/new")
def deck_new():
    return _render_template("deck.html", {"__DATA__": _deck_payload(None, new=True)})


@app.route("/deck/<deck_id>")
def deck_editor(deck_id):
    d = deckmod.find_deck(deck_id)
    if not d:
        # Escape the user-controlled path segment: reflected unescaped, a crafted
        # /deck/<script…> link executed same-origin — defeating the same-origin/
        # rebinding guard, since injected JS can POST /api/save (broad-scan BS-09).
        return (f"No deck with id '{html.escape(deck_id)}'. "
                "<a href='/decks'>← Decks</a>", 404)
    return _render_template("deck.html", {"__DATA__": _deck_payload(d)})


@app.route("/api/deck/analysis/<deck_id>/<kind>")
def deck_analysis(deck_id, kind):
    if kind not in ("stats", "mana", "tribes", "suggest"):
        return jsonify(ok=False, error="unknown analysis kind"), 400
    if not deckmod.find_deck(deck_id):
        return jsonify(ok=False, error="no such deck"), 404
    return jsonify(ok=True, text=_run_deck_analysis(kind, deck_id) or "(no output)")


@app.route("/api/deck/save", methods=["POST"])
@_serialized
def deck_save():
    """Write an edited deck back to its .txt (structure + section comments
    preserved). Gated on INV-04: must re-parse with every card line intact, else
    the file is untouched. Backs up to a timestamped .bak, then atomic replace."""
    data = request.get_json(silent=True) or {}
    did = str(data.get("id", ""))
    meta, body = data.get("meta") or [], data.get("body")
    if not _list_of_objs(body) or not _list_of_objs(meta):
        return jsonify(ok=False, errors=["Malformed request."]), 400
    d = deckmod.find_deck(did)
    if not d:
        return jsonify(ok=False, errors=[f"No deck with id {did!r}."]), 404
    # Staleness gate (BS2-26), the same contract the CSV save() has had all along:
    # this endpoint wrote the client's ENTIRE document over the file with no check
    # that the file still matched what the page loaded — so an open tab silently
    # reverted a CLI `swap --apply` (the documented G-06 workflow writes the same
    # file), and `recommendations.csv` then recorded a decision against a deck
    # state that no longer existed. The `.bak` made it recoverable; nothing made
    # it VISIBLE. Token = content hash sent with the page, echoed on save.
    sent = str(data.get("doc_token") or "")
    if sent and sent != _doc_token(d["path"]):
        return jsonify(ok=False, errors=[
            "The deck file CHANGED since this page loaded it (a `swap --apply`, a "
            "sync, or another tab?). Saving would silently overwrite that change — "
            "reload the page, re-apply your edit, and save again."]), 409
    ok, errs, _ = _validate_body(body)
    errs = _validate_meta(meta) + errs
    if errs or not ok:
        return jsonify(ok=False, errors=errs), 400
    payload, status = _write_deck(d["path"], _serialize_doc(meta, body),
                                  _body_cards(body), backup=True)
    if payload.get("ok"):
        payload["doc_token"] = _doc_token(d["path"])
    return jsonify(**payload), status


@app.route("/api/deck/new", methods=["POST"])
@_serialized
def deck_create():
    """Create a new numbered deck (decks/NN-slug/deck.txt) from the editor."""
    data = request.get_json(silent=True) or {}
    meta, body = data.get("meta") or [], data.get("body")
    if not _list_of_objs(body) or not _list_of_objs(meta):
        return jsonify(ok=False, errors=["Malformed request."]), 400
    name = next((( p.get("value") or "").strip() for p in meta
                 if (p.get("key") or "").lower() == "name"), "")
    if not name:
        return jsonify(ok=False, errors=["Give the deck a name first (the 'name' field)."]), 400
    ok, errs, _ = _validate_body(body)
    errs = _validate_meta(meta) + errs
    if errs or not ok:
        return jsonify(ok=False, errors=errs), 400

    nums = [int(dd["core"]) for dd in deckmod.discover_decks() if str(dd["core"]).isdigit()]
    nextn = (max(nums) + 1) if nums else 1
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "deck"
    folder = os.path.join(deckmod.DECKS_DIR, f"{nextn:02d}-{slug}")
    if os.path.exists(folder):
        return jsonify(ok=False, errors=[f"Folder {os.path.basename(folder)} already exists."]), 409
    os.makedirs(folder)
    payload, status = _write_deck(os.path.join(folder, "deck.txt"),
                                  _serialize_doc(meta, body), _body_cards(body), backup=False)
    if not payload.get("ok"):
        try:
            os.rmdir(folder)  # roll back the empty folder on failure
        except OSError:
            pass
        return jsonify(**payload), status
    payload["id"] = str(nextn)
    return jsonify(**payload), status


def main():
    ap = argparse.ArgumentParser(description="Local card-library.csv editor (Flask).")
    ap.add_argument("--host", default="127.0.0.1", help="bind address (default localhost)")
    ap.add_argument("--port", type=int, default=5000, help="port (default 5000)")
    ap.add_argument("--debug", action="store_true", help="Flask debug/auto-reload")
    ap.add_argument("--no-browser", action="store_true", help="don't auto-open the browser")
    args = ap.parse_args()

    # This editor has NO auth by design (personal, localhost). Two guardrails (F12):
    #  • --debug enables the Werkzeug interactive debugger, whose console runs
    #    arbitrary code — exposing that on a non-local bind is a remote-code-exec
    #    hole, so refuse the combination outright.
    #  • Any non-local bind exposes the auth-less editor; warn loudly.
    global _bind_host
    _bind_host = args.host          # the request guard relaxes its Host check off-loopback
    local = args.host in ("127.0.0.1", "localhost", "::1")
    if args.debug and not local:
        ap.error(f"refusing --debug on non-local host {args.host!r}: the Werkzeug debugger "
                 "allows remote code execution and this editor has no auth. Bind 127.0.0.1 "
                 "for debugging, or drop --debug.")
    if not local:
        print(f"WARNING: binding {args.host} exposes this AUTH-LESS editor beyond localhost — "
              "anyone who can reach the port can read and write your files. Prefer 127.0.0.1 "
              "with an SSH tunnel or a Codespace's private port forwarding.")
    url = f"http://{args.host}:{args.port}"
    print(f"Collection & deck editor → {url}  (Ctrl-C to stop)")
    # Auto-open the browser once the server is up (localhost only, and not in the
    # debug reloader's child process, so it opens exactly once).
    if (not args.no_browser and args.host in ("127.0.0.1", "localhost")
            and not os.environ.get("WERKZEUG_RUN_MAIN")):
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
