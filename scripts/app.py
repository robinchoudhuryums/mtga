#!/usr/bin/env python3
"""Local, browser-based editor for card-library.csv (OPTIONAL Flask app).

This is the one part of the toolkit with a dependency (Flask). The core scripts
stay pure standard library; nothing here is imported by them or by check_all.py.

Phase 1 (this file): a read-and-edit grid. It serves your collection with card
art (from image-manifest.json), lets you search/filter, and shows each card's
Quantity Owned and Synergies as editable fields with live "dirty" tracking. It
does NOT write anything yet — saving back to the CSV (with validation + backup)
lands in Phase 2.

Run:
    pip install -r requirements-app.txt
    python3 scripts/app.py                 # then open http://127.0.0.1:5000
    python3 scripts/app.py --port 8000     # different port

Bound to 127.0.0.1 by default — it's a personal, local tool, so there's no auth.
"""

import argparse
import json
import os

from flask import Flask

from lib import DEFAULT_CSV, REPO_ROOT, load_rows

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
