#!/usr/bin/env python3
"""Generate a filterable visual gallery (gallery.html) from card-library.csv.

Card images are resolved from Scryfall and cached in .image-cache.json (keyed by
card name, gitignored) so the canonical CSV is never modified and images aren't
re-fetched on every build. Image lookups use Scryfall's batch /cards/collection
endpoint (up to 75 cards per request) to stay well under rate limits.

The resolved URLs are also written to image-manifest.json, which IS committed.
That makes the gallery offline-resilient: a fresh clone (or anyone you share the
repo with) can render art and rebuild with --no-fetch without hitting Scryfall,
since the working .image-cache.json isn't in git. The manifest is refreshed on
every build (both fetch and --no-fetch).

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
import html
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint, atomic_write
import scryfall
from scryfall import NotFound, ScryfallUnavailable

COLLECTION_URL = "https://api.scryfall.com/cards/collection"
USER_AGENT = "mtga-card-library/1.0"
# Local working cache (gitignored) vs. the committed, portable manifest. The
# manifest is what makes the gallery offline-resilient: a fresh clone (or anyone
# you share the repo with) can render art and rebuild with --no-fetch without
# ever hitting Scryfall, since .image-cache.json isn't committed.
CACHE_PATH = os.path.join(REPO_ROOT, ".image-cache.json")
MANIFEST_PATH = os.path.join(REPO_ROOT, "image-manifest.json")
DEFAULT_OUT = os.path.join(REPO_ROOT, "gallery.html")


def load_cache():
    """Merge the committed manifest with the local working cache.

    Manifest is read first so a fresh clone has image URLs; the local cache is
    overlaid on top (it may hold newer entries or empty-string "known misses").
    """
    cache = {}
    for path in (MANIFEST_PATH, CACHE_PATH):
        if not os.path.exists(path):
            continue
        # A build killed mid-write (or a corrupt committed manifest in a fresh clone)
        # leaves truncated JSON; treat that as an empty file with a warning rather than
        # crashing every subsequent build — including --no-fetch (audit F4). Writes are
        # now atomic (below), so this only rescues files damaged by an older build.
        try:
            with open(path, encoding="utf-8") as fh:
                cache.update(json.load(fh))
        except (json.JSONDecodeError, OSError) as e:
            eprint(f"WARN:  {os.path.basename(path)} is unreadable/corrupt ({e}); "
                   f"ignoring it. It will be rewritten from this build.")
    return cache


def save_cache(cache):
    atomic_write(CACHE_PATH,
                 lambda fh: json.dump(cache, fh, indent=0, sort_keys=True),
                 backup=False)


def save_manifest(cache):
    """Write the committed, portable manifest (resolved URLs only, no misses)."""
    resolved = {k: v for k, v in cache.items() if v}
    atomic_write(MANIFEST_PATH,
                 lambda fh: json.dump(resolved, fh, indent=0, sort_keys=True),
                 backup=False)


def _image_url(card):
    """Best available image URL for a card, handling double-faced cards."""
    uris = card.get("image_uris") or {}
    if not uris and card.get("card_faces"):
        uris = card["card_faces"][0].get("image_uris", {}) or {}
    return uris.get("normal") or uris.get("large") or uris.get("small") or ""


def _request_named(params):
    """GET /cards/named as JSON via the shared resilient client. Raises NotFound
    (404) or ScryfallUnavailable (transient) — see scryfall.py."""
    return scryfall.named(params)


def _post_collection(names):
    """Batch /cards/collection lookup via the shared resilient client. Raises
    ScryfallUnavailable on a transient outage (timeout / 5xx / bad body)."""
    return scryfall.post_collection(names)


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

    resolved = 0
    degraded = False  # True if a Scryfall outage cut the run short (art may be missing)
    for i in range(0, len(names), 75):
        chunk = names[i:i + 75]
        try:
            data = _post_collection(chunk)
        except ScryfallUnavailable as e:
            eprint(f"ERROR: could not reach Scryfall: {e}")
            save_cache(cache)
            degraded = True
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

    # Fallback for names still without an image — notably double-faced cards
    # whose "Front // Back" name the collection endpoint rejects but the
    # single-card `named` endpoint (front-face lookup) accepts. Scans all rows so
    # it also repairs entries the batch previously stored as empty.
    misses, seen_m = [], set()
    for r in rows:
        n = (r.get("Card Name") or "").strip()
        if n and n.lower() not in seen_m and not cache.get(n.lower()):
            seen_m.add(n.lower())
            misses.append(n)
    for n in misses:
        front = n.split(" // ")[0]
        try:
            data = _request_named({"exact": front})
        except NotFound:
            # Genuinely no such card on Scryfall — a real miss, leave it blank and
            # move on. (Distinct from an outage, which must NOT be swallowed.)
            continue
        except ScryfallUnavailable as e:
            eprint(f"ERROR: could not reach Scryfall: {e}")
            degraded = True
            break
        url = _image_url(data) if data else ""
        if url:
            cache[n.lower()] = url
            resolved += 1
        time.sleep(0.15)
    if misses:
        save_cache(cache)
    # Floor: if we asked Scryfall for a real batch of names and it resolved NONE — a
    # 200-with-empty-data or a blocking proxy that scryfall.py doesn't classify as an
    # outage — treat the run as degraded rather than shipping an imageless gallery as a
    # clean success (audit F23). A handful of genuine misses won't trip the threshold.
    if not degraded and len(names) >= 5 and resolved == 0:
        eprint(f"WARN: requested {len(names)} image(s) from Scryfall but resolved NONE — "
               "treating the build as degraded (empty/blocked response, not a clean run).")
        degraded = True
    return resolved, degraded


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


def _primary_type(type_line):
    for t in ["Land", "Creature", "Planeswalker", "Battle", "Artifact",
              "Enchantment", "Instant", "Sorcery"]:
        if t.lower() in type_line.lower():
            return t
    return "Other"


def compute_stats(cards):
    colors = {c: 0 for c in "WUBRGC"}
    types, sets, syn = {}, {}, {}
    owned = 0
    for c in cards:
        q = c["qty"]
        owned += int(q) if q.isdigit() else 0
        for ch in c["colors"]:
            colors[ch] = colors.get(ch, 0) + 1
        t = _primary_type(c["type"])
        types[t] = types.get(t, 0) + 1
        if c["set"]:
            sets[c["set"]] = sets.get(c["set"], 0) + 1
        for tag in (c["synergies"].split(";") if c["synergies"] else []):
            tag = tag.strip()
            if tag:
                syn[tag] = syn.get(tag, 0) + 1
    return {"printings": len(cards), "owned": owned, "colors": colors,
            "types": types, "sets": sets, "syn": syn}


def _bars(counts, cls_by_key=None, top=None):
    items = sorted(counts.items(), key=lambda kv: -kv[1])
    if top:
        items = items[:top]
    mx = max((v for _, v in items), default=1)
    out = []
    for k, v in items:
        cls = f" {cls_by_key[k]}" if cls_by_key else ""
        pct = round(100 * v / mx)
        out.append(
            f'<div class="bar{cls}"><span>{html.escape(str(k))}</span>'
            f'<span class="track"><span class="fill" style="width:{pct}%"></span></span>'
            f'<span class="num">{v}</span></div>')
    return "".join(out)


def render_stats(stats):
    color_names = {"W": "W", "U": "U", "B": "B", "R": "R", "G": "G", "C": "C"}
    color_bars = _bars({color_names[c]: stats["colors"][c] for c in "WUBRGC"
                        if stats["colors"][c]}, cls_by_key={c: c for c in "WUBRGC"})
    type_bars = _bars(stats["types"], top=8)
    set_bars = _bars(stats["sets"], top=8)

    chips = []
    for tag, n in sorted(stats["syn"].items(), key=lambda kv: -kv[1])[:16]:
        # The tag lands in TWO contexts: a JS single-quoted string AND the
        # double-quoted onclick attribute (plus as HTML text). Escape for the JS
        # string first (backslash, quote), then HTML-escape so a '"', '<', or '&'
        # in the tag can't break out of the attribute — the deliberate __DATA__
        # escaping didn't cover this dashboard path (audit F12).
        js_tag = tag.replace("\\", "\\\\").replace("'", "\\'")
        attr = html.escape(js_tag, quote=True)
        chips.append(
            f'<span class="chip" onclick="var q=document.getElementById(\'q\');'
            f'q.value=\'{attr}\';q.dispatchEvent(new Event(\'input\'));'
            f'window.scrollTo(0,0)">{html.escape(tag)} <span class="n">{n}</span></span>')

    return f"""<details class="dash" open>
  <summary>Collection overview</summary>
  <div class="dashgrid">
    <div class="tile"><div class="kpi">{stats['printings']:,}</div><h3>printings</h3>
      <div class="kpi">{stats['owned']:,}</div><h3>copies owned</h3></div>
    <div class="tile"><h3>Colors</h3>{color_bars}</div>
    <div class="tile"><h3>Card types</h3>{type_bars}</div>
    <div class="tile"><h3>Top sets</h3>{set_bars}</div>
  </div>
  <h3 style="margin-top:16px">Top synergies — click to filter</h3>
  <div class="chips">{''.join(chips)}</div>
</details>"""


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
  .dash { margin: 16px 20px 0; background: var(--panel); border: 1px solid var(--line);
    border-radius: 12px; padding: 4px 16px 16px; }
  .dash > summary { cursor: pointer; padding: 12px 0; font-weight: 700; list-style: none; }
  .dash > summary::-webkit-details-marker { display: none; }
  .dash > summary::before { content: "▾ "; color: var(--muted); }
  .dashgrid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); }
  .tile { background: var(--panel2); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }
  .tile .kpi { font-size: 26px; font-weight: 800; letter-spacing: .3px; }
  .tile h3 { font-size: 12px; text-transform: uppercase; letter-spacing: .6px;
    color: var(--muted); margin: 0 0 10px; font-weight: 700; }
  .bar { display: grid; grid-template-columns: 82px 1fr 30px; align-items: center;
    gap: 8px; margin: 4px 0; font-size: 12px; }
  .bar > span:first-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .bar .track { height: 10px; background: #0f1115; border-radius: 6px; overflow: hidden; }
  .bar .fill { height: 100%; background: var(--accent); border-radius: 6px; }
  .bar .num { text-align: right; color: var(--muted); }
  .bar.W .fill{background:var(--W)} .bar.U .fill{background:var(--U)} .bar.B .fill{background:var(--B)}
  .bar.R .fill{background:var(--R)} .bar.G .fill{background:var(--G)} .bar.C .fill{background:var(--C)}
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
  .chip { background: var(--panel2); border: 1px solid var(--line); border-radius: 20px;
    padding: 3px 11px; font-size: 12px; cursor: pointer; color: var(--text); }
  .chip:hover { border-color: var(--accent); color: var(--accent); }
  .chip .n { color: var(--muted); }
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
__STATS__
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

    degraded = False
    if not args.no_fetch:
        added, degraded = resolve_images(rows, cache)
        eprint(f"       {added} new image(s) resolved this run")

    # Keep the committed manifest in step with whatever we resolved, so offline
    # rebuilds (and anyone who clones the repo) keep their art.
    save_manifest(cache)

    cards = build_cards(rows, cache)
    with_img = sum(1 for c in cards if c["img"])
    # Escape "<" as < so a card field containing "</script>" can't terminate
    # the embedded <script type="application/json"> block (JSON.parse decodes it
    # back). Valid JSON, so the browser reads the data unchanged.
    data_json = json.dumps(cards, ensure_ascii=False).replace("<", "\\u003c")
    html = (HTML_TEMPLATE
            .replace("__STATS__", render_stats(compute_stats(cards)))
            .replace("__DATA__", data_json))
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html)
    missing = len(cards) - with_img
    print(f"Wrote {args.out}: {len(cards)} cards, {with_img} with images.")
    # A Scryfall outage mid-run leaves cards without art. Say so plainly and exit
    # non-zero rather than presenting an incomplete gallery as a clean success —
    # the missing art is transient, so a later rebuild (or --no-fetch from the
    # manifest) will fill it in.
    if degraded:
        eprint(f"WARN:  Scryfall was unreachable during this build — {missing} "
               f"card(s) have no art yet. This is transient: rerun when Scryfall "
               f"is reachable, or use --no-fetch to rebuild from the cache/manifest.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
