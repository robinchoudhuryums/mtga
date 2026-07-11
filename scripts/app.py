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
the integrity gate's INV-02 stays satisfied. (In-browser deck editing is a
later phase.)

Run:
    pip install -r requirements-app.txt
    python3 scripts/app.py                 # then open http://127.0.0.1:5000
    python3 scripts/app.py --port 8000     # different port

Bound to 127.0.0.1 by default — it's a personal, local tool, so there's no auth.
"""

import argparse
import contextlib
import csv
import io
import json
import os
import shutil
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

from flask import Flask, jsonify, request

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, write_rows
from validate import validate

MANIFEST_PATH = os.path.join(REPO_ROOT, "image-manifest.json")
TEMPLATE_PATH = os.path.join(REPO_ROOT, "templates", "collection.html")
MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")

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


# --------------------------------------------------------------------------- #
# Safe write + card-mana maintenance (shared by save / add / remove)
# --------------------------------------------------------------------------- #
def _safe_write(rows):
    """Validate rows in a temp file, then back up + atomically replace the CSV.

    Returns (ok, backup_basename_or_None, errors). The real CSV is only touched
    once the temp file passes validate(), and the swap is atomic.
    """
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
            return False, None, ["Validation failed — nothing written.", *tail]
        backup = f"{target}.{time.strftime('%Y%m%d-%H%M%S')}.bak"
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


def _append_mana(name, cost, mv, keywords):
    """Append a card-mana.csv row so INV-02 (every library name has a mana row)
    holds after an add — even if enrichment was offline (then cost/kw are blank,
    and a later build_mana.py/refresh fills them in)."""
    exists = os.path.exists(MANA_CSV)
    with open(MANA_CSV, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if not exists:
            w.writerow(["Card Name", "Mana Cost", "Mana Value", "Keywords"])
        w.writerow([name, cost or "", mv if isinstance(mv, int) else "", keywords or ""])


def _lookup_card(name):
    """One-shot, best-effort Scryfall lookup for a single card (exact name, short
    timeout, no long retry — keeps 'add' snappy). Returns a field dict or None if
    unreachable / not found. Never raises."""
    from enrich import oracle_fields, color_shorthand
    try:
        url = "https://api.scryfall.com/cards/named?" + urllib.parse.urlencode({"exact": name})
        req = urllib.request.Request(
            url, headers={"User-Agent": "mtga-card-library/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            card = json.load(resp)
    except (urllib.error.URLError, ValueError):
        return None
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
    }


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
    ok, backup, errors = _safe_write(rows)
    if not ok:
        return jsonify(ok=False, errors=errors), 400
    return jsonify(ok=True, updated=applied, backup=backup)


@app.route("/api/add", methods=["POST"])
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

    info = _lookup_card(name)
    enriched = info is not None
    if info:
        from enrich import SET_ALIASES
        from tag_synergies import tags_for
        stored = info["name"]
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

    # Keep INV-02 intact: ensure card-mana.csv has a row for this name first.
    if not _mana_has(stored):
        if info:
            _append_mana(stored, info["mana_cost"], info["mv"], info["keywords"])
        else:
            _append_mana(stored, "", "", "")

    rows.append(new)
    ok, backup, errors = _safe_write(rows)
    if not ok:
        return jsonify(ok=False, errors=errors), 400
    return jsonify(ok=True, backup=backup, enriched=enriched, name=stored)


@app.route("/api/remove", methods=["POST"])
def remove():
    """Remove a single printing (by name/set/collector key) from the collection.

    Leaves card-mana.csv untouched — an extra mana row is harmless (INV-02 only
    requires library names to be present in it), and a later refresh prunes it.
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
    return jsonify(ok=True, backup=backup, removed=key.get("name"))


@app.route("/api/revert", methods=["POST"])
def revert():
    """Undo the last save by restoring the most recent .bak snapshot.

    The backup is validated before it's restored. Other .bak files are left in
    place (gitignored), so nothing is permanently lost.
    """
    target = os.path.abspath(DEFAULT_CSV)
    d, base = os.path.dirname(target), os.path.basename(target)
    baks = sorted(f for f in os.listdir(d)
                  if f.startswith(base + ".") and f.endswith(".bak"))
    if not baks:
        return jsonify(ok=False, errors=["No backup to revert to yet — nothing has been saved."]), 409
    newest = os.path.join(d, baks[-1])  # timestamped names sort chronologically
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = validate(newest)
    if rc != 0:
        return jsonify(ok=False, errors=[f"Backup {baks[-1]} failed validation; not restoring."]), 400
    shutil.copy2(newest, target)
    return jsonify(ok=True, restored=baks[-1])


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
