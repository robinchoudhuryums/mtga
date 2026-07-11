#!/usr/bin/env python3
"""Local, browser-based editor for card-library.csv (OPTIONAL Flask app).

This is the one part of the toolkit with a dependency (Flask). The core scripts
stay pure standard library; nothing here is imported by them or by check_all.py.

An editable grid: it serves your collection with card art (from
image-manifest.json), lets you search/filter, and shows each card's Quantity
Owned and Synergies as inline fields with live "dirty" tracking. Save writes the
changes back to card-library.csv through a safe path — the edited rows are
written to a temp file and run through validate() first; only if that passes is
the current CSV backed up to a timestamped .bak and atomically replaced. A bad
edit therefore can't corrupt the inventory. (Adding/removing cards and deck
editing are later phases.)

Run:
    pip install -r requirements-app.txt
    python3 scripts/app.py                 # then open http://127.0.0.1:5000
    python3 scripts/app.py --port 8000     # different port

Bound to 127.0.0.1 by default — it's a personal, local tool, so there's no auth.
"""

import argparse
import contextlib
import io
import json
import os
import shutil
import tempfile
import time

from flask import Flask, jsonify, request

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, write_rows
from validate import validate

MANIFEST_PATH = os.path.join(REPO_ROOT, "image-manifest.json")
TEMPLATE_PATH = os.path.join(REPO_ROOT, "templates", "collection.html")

app = Flask(__name__)


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
        letters = [c for c in color_str.upper() if c in "WUBRG"] or ["C"]
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


@app.route("/api/save", methods=["POST"])
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
    if not isinstance(edits, list):
        return jsonify(ok=False, errors=["Malformed request: expected a JSON list of edits."]), 400
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
    target = os.path.abspath(DEFAULT_CSV)
    fd, tmp = tempfile.mkstemp(suffix=".csv", dir=os.path.dirname(target))
    os.close(fd)
    try:
        write_rows(rows, tmp)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = validate(tmp)
        if rc != 0:
            tail = [ln for ln in buf.getvalue().splitlines() if ln.strip()][-8:]
            return jsonify(ok=False, errors=["Validation failed — nothing written.", *tail]), 400
        backup = f"{target}.{time.strftime('%Y%m%d-%H%M%S')}.bak"
        shutil.copy2(target, backup)
        os.replace(tmp, target)
        tmp = None
        return jsonify(ok=True, updated=applied, backup=os.path.basename(backup))
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


def main():
    ap = argparse.ArgumentParser(description="Local card-library.csv editor (Flask).")
    ap.add_argument("--host", default="127.0.0.1", help="bind address (default localhost)")
    ap.add_argument("--port", type=int, default=5000, help="port (default 5000)")
    ap.add_argument("--debug", action="store_true", help="Flask debug/auto-reload")
    args = ap.parse_args()
    print(f"Collection editor → http://{args.host}:{args.port}  (Ctrl-C to stop)")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
