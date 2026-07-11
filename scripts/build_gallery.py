#!/usr/bin/env python3
"""Generate a filterable visual gallery (gallery.html) from card-library.csv.

Card images are resolved from Scryfall and cached in .image-cache.json (keyed by
card name, gitignored) so the canonical CSV is never modified and images aren't
re-fetched on every build. Image lookups use Scryfall's batch /cards/collection
endpoint (up to 75 cards per request) to stay well under rate limits.

The output is a single self-contained gallery.html: card data is embedded as
JSON and filtering happens in the browser. Images are hotlinked from Scryfall's
CDN (cards.scryfall.io), so an internet connection is needed to see the art but
the file itself is tiny and portable.

Usage:
    python3 scripts/build_gallery.py                 # resolve images + build
    python3 scripts/build_gallery.py --no-fetch      # build from cache only
    python3 scripts/build_gallery.py --out foo.html  # custom output path

Requires outbound access to api.scryfall.com (data) and cards.scryfall.io
(images) — the same hosts enrich.py uses.
"""

import argparse
import json
import os
import time
import urllib.error
import urllib.request

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint

COLLECTION_URL = "https://api.scryfall.com/cards/collection"
USER_AGENT = "mtga-card-library/1.0"
CACHE_PATH = os.path.join(REPO_ROOT, ".image-cache.json")
DEFAULT_OUT = os.path.join(REPO_ROOT, "gallery.html")


def load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_cache(cache):
    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, indent=0, sort_keys=True)


def _image_url(card):
    """Best available image URL for a card, handling double-faced cards."""
    uris = card.get("image_uris") or {}
    if not uris and card.get("card_faces"):
        uris = card["card_faces"][0].get("image_uris", {}) or {}
    return uris.get("normal") or uris.get("large") or uris.get("small") or ""


def _post_collection(names, retries=6):
    """POST a batch of name identifiers to Scryfall, returning the card list."""
    body = json.dumps({"identifiers": [{"name": n} for n in names]}).encode("utf-8")
    req = urllib.request.Request(
        COLLECTION_URL,
        data=body,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                wait = float(e.headers.get("Retry-After", 0) or 0) or 1.0 * (2 ** attempt)
                eprint(f"       rate limited; waiting {wait:.0f}s...")
                time.sleep(wait)
                continue
            raise
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(1.0 * (2 ** attempt))
                continue
            raise


def resolve_images(rows, cache):
    """Populate cache[name_lower] = image URL for any card missing one."""
    names = []
    seen = set()
    for r in rows:
        n = (r.get("Card Name") or "").strip()
        key = n.lower()
        if n and key not in seen and key not in cache:
            seen.add(key)
            names.append(n)
    if not names:
        return 0

    resolved = 0
    for i in range(0, len(names), 75):
        chunk = names[i:i + 75]
        try:
            data = _post_collection(chunk)
        except urllib.error.URLError as e:
            eprint(f"ERROR: could not reach Scryfall: {e}")
            save_cache(cache)
            break
        # Index returned cards by full and front-face name for matching.
        by_name = {}
        for card in data.get("data", []):
            full = card.get("name", "").lower()
            by_name[full] = card
            by_name[full.split(" // ")[0]] = card
        for n in chunk:
            card = by_name.get(n.lower())
            cache[n.lower()] = _image_url(card) if card else ""
            if card and cache[n.lower()]:
                resolved += 1
        eprint(f"       resolved {min(i + 75, len(names))}/{len(names)} names")
        save_cache(cache)
        time.sleep(0.15)
    return resolved


def color_letters(s):
    """Parse a Color(s) string into WUBRG / C letters for filtering."""
    s = (s or "").strip()
    if not s or s.lower() == "colorless":
        return ["C"]
    letters = [c for c in s.upper() if c in "WUBRG"]
    return letters or ["C"]


def build_cards(rows, cache):
    cards = []
    for r in rows:
        name = (r.get("Card Name") or "").strip()
        if not name:
            continue
        cards.append({
            "name": name,
            "type": (r.get("Type") or "").strip(),
            "text": (r.get("Card Text") or "").strip(),
            "colors": color_letters(r.get("Color(s)")),
            "colorStr": (r.get("Color(s)") or "").strip(),
            "synergies": (r.get("Synergies") or "").strip(),
            "set": (r.get("Set Code") or "").strip(),
            "cn": (r.get("Collector #") or "").strip(),
            "qty": (r.get("Quantity Owned") or "").strip(),
            "img": cache.get(name.lower(), ""),
        })
    return cards


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MTG Arena Card Library</title>
<style>
  :root {
    --bg: #0f1115; --panel: #191c23; --panel2: #21252e; --line: #2c313c;
    --text: #e7e9ee; --muted: #949bab; --accent: #d9a441;
    --W:#f4e7c3; --U:#a5c8e8; --B:#b7a3c7; --R:#e39a8a; --G:#9dc7a3; --C:#c9ccd3;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--text);
    font: 15px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  header { position: sticky; top: 0; z-index: 5; background: rgba(15,17,21,.95);
    backdrop-filter: blur(6px); border-bottom: 1px solid var(--line); padding: 14px 20px; }
  .titlebar { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; }
  h1 { font-size: 19px; margin: 0; letter-spacing: .2px; }
  .stats { color: var(--muted); font-size: 13px; }
  .controls { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; align-items: center; }
  input[type=search], select { background: var(--panel2); color: var(--text);
    border: 1px solid var(--line); border-radius: 8px; padding: 8px 11px; font-size: 14px; }
  input[type=search] { min-width: 240px; flex: 1 1 240px; }
  .pips { display: flex; gap: 6px; }
  .pip { width: 30px; height: 30px; border-radius: 50%; border: 2px solid transparent;
    cursor: pointer; font-weight: 700; color: #1a1a1a; display: grid; place-items: center;
    font-size: 13px; opacity: .45; transition: opacity .12s, border-color .12s; user-select: none; }
  .pip.on { opacity: 1; border-color: var(--text); }
  .pip.W{background:var(--W)} .pip.U{background:var(--U)} .pip.B{background:var(--B)}
  .pip.R{background:var(--R)} .pip.G{background:var(--G)} .pip.C{background:var(--C)}
  .grid { display: grid; gap: 14px; padding: 20px;
    grid-template-columns: repeat(auto-fill, minmax(184px, 1fr)); }
  .card { position: relative; border-radius: 11px; overflow: hidden; background: var(--panel);
    border: 1px solid var(--line); aspect-ratio: 5 / 7; }
  .card img { width: 100%; height: 100%; object-fit: cover; display: block; background: var(--panel2); }
  .card .fallback { position: absolute; inset: 0; display: none; flex-direction: column;
    padding: 14px; gap: 6px; }
  .card.noimg .fallback { display: flex; }
  .card.noimg img { display: none; }
  .fallback .fname { font-weight: 700; font-size: 15px; }
  .fallback .ftype { color: var(--muted); font-size: 12px; }
  .fallback .ftext { color: var(--muted); font-size: 11px; overflow: hidden; }
  .qty { position: absolute; top: 8px; right: 8px; background: rgba(10,11,14,.85);
    border: 1px solid var(--line); color: var(--accent); font-weight: 700; font-size: 12px;
    padding: 2px 7px; border-radius: 20px; }
  .setcode { position: absolute; bottom: 8px; left: 8px; background: rgba(10,11,14,.8);
    color: var(--muted); font-size: 10px; letter-spacing: .5px; padding: 2px 6px; border-radius: 5px; }
  .empty { padding: 60px 20px; text-align: center; color: var(--muted); }
  footer { color: var(--muted); font-size: 12px; text-align: center; padding: 20px; }
</style>
</head>
<body>
<header>
  <div class="titlebar">
    <h1>MTG Arena Card Library</h1>
    <span class="stats" id="stats"></span>
  </div>
  <div class="controls">
    <input type="search" id="q" placeholder="Search name, type, or text…" autocomplete="off">
    <div class="pips" id="pips">
      <div class="pip W" data-c="W" title="White">W</div>
      <div class="pip U" data-c="U" title="Blue">U</div>
      <div class="pip B" data-c="B" title="Black">B</div>
      <div class="pip R" data-c="R" title="Red">R</div>
      <div class="pip G" data-c="G" title="Green">G</div>
      <div class="pip C" data-c="C" title="Colorless">C</div>
    </div>
    <select id="set"></select>
    <select id="sort">
      <option value="name">Sort: Name</option>
      <option value="set">Sort: Set</option>
      <option value="qty">Sort: Quantity</option>
    </select>
  </div>
</header>
<div class="grid" id="grid"></div>
<div class="empty" id="empty" style="display:none">No cards match your filters.</div>
<footer>Generated from card-library.csv · images © Wizards of the Coast, via Scryfall</footer>
<script id="data" type="application/json">__DATA__</script>
<script>
  const CARDS = JSON.parse(document.getElementById('data').textContent);
  const grid = document.getElementById('grid'), empty = document.getElementById('empty');
  const q = document.getElementById('q'), setSel = document.getElementById('set');
  const sortSel = document.getElementById('sort'), statsEl = document.getElementById('stats');
  const activeColors = new Set();

  // Populate set dropdown.
  const sets = [...new Set(CARDS.map(c => c.set).filter(Boolean))].sort();
  setSel.innerHTML = '<option value="">All sets</option>' +
    sets.map(s => `<option value="${s}">${s}</option>`).join('');

  document.getElementById('pips').addEventListener('click', e => {
    const pip = e.target.closest('.pip'); if (!pip) return;
    const c = pip.dataset.c;
    if (activeColors.has(c)) { activeColors.delete(c); pip.classList.remove('on'); }
    else { activeColors.add(c); pip.classList.add('on'); }
    render();
  });
  q.addEventListener('input', render);
  setSel.addEventListener('change', render);
  sortSel.addEventListener('change', render);

  function matches(c) {
    const term = q.value.trim().toLowerCase();
    if (term && !(c.name + ' ' + c.type + ' ' + c.text + ' ' + c.synergies)
        .toLowerCase().includes(term)) return false;
    if (setSel.value && c.set !== setSel.value) return false;
    if (activeColors.size && !c.colors.some(x => activeColors.has(x))) return false;
    return true;
  }

  function render() {
    let list = CARDS.filter(matches);
    const s = sortSel.value;
    list.sort((a, b) =>
      s === 'qty' ? (parseInt(b.qty || 0) - parseInt(a.qty || 0)) || a.name.localeCompare(b.name)
      : s === 'set' ? (a.set.localeCompare(b.set) || a.name.localeCompare(b.name))
      : a.name.localeCompare(b.name));

    grid.innerHTML = list.map(c => {
      const noimg = c.img ? '' : ' noimg';
      const qty = c.qty ? `<span class="qty">×${c.qty}</span>` : '';
      const set = c.set ? `<span class="setcode">${c.set}${c.cn ? ' · ' + c.cn : ''}</span>` : '';
      return `<div class="card${noimg}" title="${esc(c.name)}">
        <img loading="lazy" src="${c.img}" alt="${esc(c.name)}"
             onerror="this.closest('.card').classList.add('noimg')">
        <div class="fallback"><div class="fname">${esc(c.name)}</div>
          <div class="ftype">${esc(c.type)}</div><div class="ftext">${esc(c.text)}</div></div>
        ${qty}${set}</div>`;
    }).join('');

    empty.style.display = list.length ? 'none' : 'block';
    const owned = list.reduce((n, c) => n + (parseInt(c.qty) || 0), 0);
    statsEl.textContent = `${list.length} of ${CARDS.length} printings · ${owned} copies shown`;
  }
  function esc(s) { return (s || '').replace(/[&<>"]/g, m =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m])); }
  render();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="Build a visual gallery from the card library.")
    ap.add_argument("--csv", default=DEFAULT_CSV)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--no-fetch", action="store_true", help="use cached images only")
    args = ap.parse_args()

    _, rows = load_rows(args.csv)
    cache = load_cache()

    if not args.no_fetch:
        added = resolve_images(rows, cache)
        eprint(f"       {added} new image(s) resolved this run")

    cards = build_cards(rows, cache)
    with_img = sum(1 for c in cards if c["img"])
    html = HTML_TEMPLATE.replace("__DATA__", json.dumps(cards, ensure_ascii=False))
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"Wrote {args.out}: {len(cards)} cards, {with_img} with images.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
