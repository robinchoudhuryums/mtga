#!/usr/bin/env python3
"""Render a self-contained roster dashboard (dashboard.html).

A read-only, always-current view of the two things that otherwise only live
behind a terminal prompt: the roster-wide CRAFT PLAN (deck.py wildcards +
wishlist --rank) and every deck's ANALYSIS (stats / mana / legal / cuts / craft
picks). It reuses deck.py's own commands verbatim — capturing their output — so
the numbers match the CLI exactly, with no reimplemented logic to drift.

Offline by design: deck.py's live-Scryfall fallbacks are disabled here, so the
build never blocks on (or crashes from) a slow network and runs in CI. It reads
only committed data (card-library.csv, card-mana.csv, card-pool.csv,
card-wishlist.csv, decks/), so an unowned WIP card missing from those may show as
unknown / '?', exactly as the CLI's offline path does.

Usage:
    python3 scripts/build_dashboard.py             # writes dashboard.html
    python3 scripts/build_dashboard.py --out x.html
"""

import argparse
import contextlib
import io
import json
import os
import time
from types import SimpleNamespace

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint
import deck as deckmod
import wishlist

OUT = os.path.join(REPO_ROOT, "dashboard.html")


def _no_network():
    """Neutralize deck.py's live-Scryfall fallbacks so the build stays offline
    and can't hang/crash on a slow or blocked Scryfall (the audit's F1)."""
    deckmod.fetch_missing_mana = lambda names, mana: mana
    deckmod.fetch_missing_rarities = lambda names, rar: rar


def _capture(fn, ns):
    """Run a deck.py cmd_* with stdout/stderr captured; never raise."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            fn(ns)
        except Exception as e:  # best-effort: one bad card shouldn't kill the build
            buf.write(f"\n[analysis error: {e}]")
    return buf.getvalue().rstrip()


def deck_detail(did):
    """The per-deck analysis panels, captured from the real deck.py commands."""
    return {
        "stats": _capture(deckmod.cmd_stats, SimpleNamespace(id=did)),
        "mana": _capture(deckmod.cmd_mana, SimpleNamespace(id=did, fmt=None)),
        "legal": _capture(deckmod.cmd_legal, SimpleNamespace(id=did, fmt=None)),
        "cuts": _capture(deckmod.cmd_cuts, SimpleNamespace(id=did, limit=8)),
        "craft": _capture(deckmod.cmd_suggest, SimpleNamespace(
            id=did, unowned=True, owned=False, limit=15, any_format=False, fmt=None)),
    }


def collect():
    """Gather the structured dashboard payload from committed data only."""
    _no_network()
    _, rows = load_rows(DEFAULT_CSV)
    _, _, qty = deckmod.load_collection()
    rarities = deckmod.load_rarities()
    rar_of = lambda name: rarities.get(name.lower(), "?")

    decks, buildable = [], 0
    for d in deckmod.discover_decks():
        meta, cards = deckmod.parse_deck_file(d["path"])
        need, total = {}, 0
        for q, n, s, c in cards:
            total += q
            if n.lower() in deckmod.BASICS:
                continue
            need[n] = need.get(n, 0) + q
        missing = short = 0
        shorts = []
        for n, req in need.items():
            have, found = deckmod.owned(qty, n)
            miss = max(0, req - have)
            if not found:
                missing += 1
            elif have < req:
                short += 1
            if miss > 0:
                shorts.append((n, miss))
        ok = (missing == 0 and short == 0)
        buildable += 1 if ok else 0
        wc = deckmod._wc_str(deckmod._wc_breakdown(shorts, rar_of))
        decks.append({
            "id": d["id"],
            "name": d["name"] or d["id"],
            "archetype": deckmod._deck_identity(meta, width=140),
            "format": (meta.get("format") or "").strip(),
            "colors": (meta.get("colors") or "").strip().upper(),
            "variant": bool(d["variant"]),
            "total": total,
            "missing": missing,
            "short": short,
            "buildable": ok,
            "wc": wc,
            "detail": deck_detail(d["id"]),
        })

    # Wishlist wildcard-priority tiers (structured, from the real _rank_scores).
    tiers = {"A": [], "B": [], "C": []}
    rollup = {"A": {}, "B": {}, "C": {}}
    try:
        wl = wishlist.load_wishlist()
        for s in (wishlist._rank_scores(wl) if wl else []):
            t = s.get("tier", "C")
            tiers.setdefault(t, []).append(s)
            r = s.get("rarity") or "?"
            rollup.setdefault(t, {})[r] = rollup.setdefault(t, {}).get(r, 0) + 1
    except Exception as e:
        eprint(f"WARN: wishlist ranking unavailable ({e})")

    return {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "totals": {"printings": len(rows), "decks": len(decks), "buildable": buildable},
        "roster_plan": _capture(deckmod.cmd_wildcards, SimpleNamespace()),
        "decks": decks,
        "wishlist": tiers,
        "wishlist_rollup": rollup,
    }


# --------------------------------------------------------------------------- #
# Rendering — a single self-contained page. Data is embedded as JSON and drawn
# client-side; all card text goes into the DOM via textContent, so no field can
# inject markup. "<" in the JSON is escaped so it can't close the <script> block.
# --------------------------------------------------------------------------- #
TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MTGA Roster Dashboard</title>
<style>
  :root {
    --bg:#f6f7f9; --panel:#fff; --ink:#1a1c20; --muted:#6b7280; --line:#e5e7eb;
    --accent:#4f46e5; --ok:#16a34a; --warn:#d97706; --bad:#dc2626; --code:#0b1020; --codeink:#e5e9f0;
    --W:#f7e7b6; --U:#7ab7e0; --B:#9a86a8; --R:#e08b7a; --G:#8bc79a; --C:#c9cdd3;
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#0e1116; --panel:#161b22; --ink:#e6edf3; --muted:#9aa4b2; --line:#2a313c;
            --accent:#8b8cf7; }
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
    font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; }
  header { padding:20px 22px; border-bottom:1px solid var(--line); background:var(--panel);
    position:sticky; top:0; z-index:5; }
  h1 { margin:0; font-size:19px; }
  .sub { color:var(--muted); font-size:13px; margin-top:4px; }
  .kpis { display:flex; gap:18px; margin-top:12px; flex-wrap:wrap; }
  .kpi { background:var(--bg); border:1px solid var(--line); border-radius:10px; padding:8px 14px; }
  .kpi b { font-size:20px; } .kpi span { color:var(--muted); font-size:12px; display:block; }
  main { max-width:1150px; margin:0 auto; padding:22px; }
  section { margin-bottom:30px; }
  h2 { font-size:15px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted);
    border-bottom:1px solid var(--line); padding-bottom:6px; }
  pre { background:var(--code); color:var(--codeink); padding:14px; border-radius:10px;
    overflow-x:auto; font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; margin:0; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:12px; }
  .card { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:14px; }
  .card .top { display:flex; justify-content:space-between; align-items:flex-start; gap:8px; }
  .card h3 { margin:0; font-size:15px; } .card .id { color:var(--muted); font-size:12px; }
  .card .arch { color:var(--muted); font-size:12.5px; margin:6px 0 8px; min-height:1.5em; }
  .meta { font-size:12px; color:var(--muted); display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
  .badge { font-size:11px; font-weight:600; padding:2px 8px; border-radius:999px; white-space:nowrap; }
  .b-ok { background:color-mix(in srgb,var(--ok) 18%,transparent); color:var(--ok); }
  .b-short { background:color-mix(in srgb,var(--warn) 20%,transparent); color:var(--warn); }
  .b-missing { background:color-mix(in srgb,var(--bad) 18%,transparent); color:var(--bad); }
  .pips { display:inline-flex; gap:3px; }
  .pip { width:13px; height:13px; border-radius:50%; border:1px solid rgba(0,0,0,.15); font-size:9px;
    display:inline-flex; align-items:center; justify-content:center; color:#222; font-weight:700; }
  .pip.W{background:var(--W)}.pip.U{background:var(--U)}.pip.B{background:var(--B)}
  .pip.R{background:var(--R)}.pip.G{background:var(--G)}.pip.C{background:var(--C)}
  .wc { font-family:ui-monospace,monospace; font-size:12px; margin-top:8px; }
  .detail { margin-top:12px; border-top:1px solid var(--line); padding-top:10px; display:none; }
  .card.open .detail { display:block; }
  .tabs { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:8px; }
  .tab { font-size:12px; padding:4px 10px; border:1px solid var(--line); border-radius:8px;
    background:var(--bg); cursor:pointer; }
  .tab.active { background:var(--accent); color:#fff; border-color:var(--accent); }
  .expand { cursor:pointer; user-select:none; font-size:12px; color:var(--accent); margin-top:8px;
    display:inline-block; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th,td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--line); }
  th { color:var(--muted); font-weight:600; font-size:12px; }
  td.num { text-align:right; font-variant-numeric:tabular-nums; }
  .tierhdr { display:flex; justify-content:space-between; align-items:baseline; margin:16px 0 4px; }
  .tierhdr h3 { margin:0; font-size:14px; } .tierhdr .roll { color:var(--muted); font-size:12px; }
  .wcpill { font-family:ui-monospace,monospace; font-weight:700; }
  .r-M{color:#d97706}.r-R{color:#ca8a04}.r-U{color:#64748b}.r-C{color:#94a3b8}
  input.filter { width:100%; max-width:340px; padding:8px 10px; border:1px solid var(--line);
    border-radius:8px; background:var(--panel); color:var(--ink); margin-bottom:12px; }
  .foot { color:var(--muted); font-size:12px; margin-top:24px; border-top:1px solid var(--line); padding-top:12px; }
</style>
</head>
<body>
<header>
  <h1>MTG Arena — Roster Dashboard</h1>
  <div class="sub" id="sub"></div>
  <div class="kpis" id="kpis"></div>
</header>
<main>
  <section>
    <h2>Craft plan — whole roster</h2>
    <pre id="plan"></pre>
  </section>
  <section id="wl-sec">
    <h2>Wildcard priority — wishlist</h2>
    <div id="wishlist"></div>
  </section>
  <section>
    <h2>Decks</h2>
    <input class="filter" id="filter" placeholder="filter by id, name, or colors…">
    <div class="grid" id="decks"></div>
  </section>
  <div class="foot" id="foot"></div>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
  const D = JSON.parse(document.getElementById('data').textContent);
  const esc = s => (s||'').toString().replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
  const WC = {Mythic:'M',Rare:'R',Uncommon:'U',Common:'C'};

  document.getElementById('sub').textContent = 'Read-only snapshot · generated ' + D.generated +
    ' · numbers match `deck.py` exactly (captured from the same commands).';
  const t = D.totals;
  document.getElementById('kpis').innerHTML =
    `<div class="kpi"><b>${t.printings}</b><span>printings</span></div>` +
    `<div class="kpi"><b>${t.decks}</b><span>decks</span></div>` +
    `<div class="kpi"><b>${t.buildable}/${t.decks}</b><span>buildable now</span></div>`;
  document.getElementById('plan').textContent = D.roster_plan || '(no craft plan)';

  // Wishlist tiers
  const labels = {A:'Tier A — craft first', B:'Tier B — targeted upgrade', C:'Tier C — situational'};
  function rollStr(o){ return ['Mythic','Rare','Uncommon','Common'].filter(k=>o&&o[k]).map(k=>`${o[k]} ${k}`).join(' · '); }
  let wl = '';
  let anyWl = false;
  for (const tier of ['A','B','C']) {
    const rows = (D.wishlist[tier]||[]);
    if (!rows.length) continue;
    anyWl = true;
    wl += `<div class="tierhdr"><h3>${labels[tier]}</h3><span class="roll">${rows.length} cards · ${esc(rollStr(D.wishlist_rollup[tier]))}</span></div>`;
    wl += `<table><thead><tr><th>Card</th><th>WC</th><th>Target</th><th class="num">reuse</th><th class="num">pri</th><th>signal</th></tr></thead><tbody>`;
    for (const s of rows) {
      const w = WC[s.rarity] || '?';
      wl += `<tr><td>${esc(s.name)}</td><td class="wcpill r-${w}">${w}</td><td>${esc(s.target)}</td>`+
            `<td class="num">${s.reuse}</td><td class="num">${s.pri}</td><td>${esc(s.sig)}</td></tr>`;
    }
    wl += `</tbody></table>`;
  }
  if (anyWl) document.getElementById('wishlist').innerHTML = wl;
  else document.getElementById('wl-sec').style.display = 'none';

  // Decks
  const TABS = [['craft','Craft picks'],['stats','Stats'],['mana','Mana'],['cuts','Cuts'],['legal','Legal']];
  function pips(colors){
    if(!colors) return '';
    return '<span class="pips">'+[...colors].filter(c=>'WUBRGC'.includes(c))
      .map(c=>`<span class="pip ${c}">${c}</span>`).join('')+'</span>';
  }
  function badge(d){
    if (d.buildable) return '<span class="badge b-ok">buildable ✓</span>';
    const parts=[];
    if (d.missing) parts.push(`<span class="badge b-missing">${d.missing} missing</span>`);
    if (d.short) parts.push(`<span class="badge b-short">${d.short} short</span>`);
    return parts.join(' ');
  }
  const grid = document.getElementById('decks');
  function render(list){
    grid.innerHTML = list.map(d => {
      const tabs = TABS.map((t,i)=>`<span class="tab${i===0?' active':''}" data-k="${t[0]}">${t[1]}</span>`).join('');
      return `<div class="card" data-id="${esc(d.id)}">
        <div class="top"><div><h3>${esc(d.name)} <span class="id">#${esc(d.id)}${d.variant?' · variant':''}</span></h3></div>${badge(d)}</div>
        <div class="arch">${esc(d.archetype)}</div>
        <div class="meta">${d.format?`<span>${esc(d.format)}</span>·`:''}${pips(d.colors)}<span>${d.total} cards</span></div>
        <div class="wc">${d.buildable?'<span class="badge b-ok">no wildcards needed</span>':'to finish: '+esc(d.wc||'—')}</div>
        <span class="expand">▸ analysis</span>
        <div class="detail"><div class="tabs">${tabs}</div><pre class="out"></pre></div>
      </div>`;
    }).join('');
    grid.querySelectorAll('.card').forEach(cardEl=>{
      const d = list.find(x=>x.id===cardEl.dataset.id);
      const out = cardEl.querySelector('.out');
      const show = k => { out.textContent = (d.detail[k]||'(no output)'); };
      show('craft');
      cardEl.querySelector('.expand').onclick = () => {
        cardEl.classList.toggle('open');
        cardEl.querySelector('.expand').textContent = cardEl.classList.contains('open') ? '▾ analysis' : '▸ analysis';
      };
      cardEl.querySelectorAll('.tab').forEach(tab=>{
        tab.onclick = () => {
          cardEl.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
          tab.classList.add('active'); show(tab.dataset.k);
        };
      });
    });
  }
  render(D.decks);
  document.getElementById('filter').addEventListener('input', e => {
    const q = e.target.value.toLowerCase().trim();
    render(D.decks.filter(d => !q ||
      (d.id+' '+d.name+' '+d.colors+' '+d.format+' '+d.archetype).toLowerCase().includes(q)));
  });
  document.getElementById('foot').textContent =
    'Offline snapshot from committed data. Regenerate with `python3 scripts/build_dashboard.py`. ' +
    'The judgment calls (craft X or Y, tuning) still live in the Claude Code chat — this shows state, not decisions.';
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="Render the roster dashboard (dashboard.html).")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    eprint("Collecting deck analysis (offline)...")
    payload = collect()
    data_json = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    html = TEMPLATE.replace("__DATA__", data_json)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html)
    t = payload["totals"]
    print(f"Wrote {args.out}: {t['decks']} decks ({t['buildable']} buildable), "
          f"{t['printings']} printings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
