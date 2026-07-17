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
    """The text analysis panels, captured from the real deck.py commands. (Stats
    and Mana are rendered visually from deck_viz instead — see below.)"""
    return {
        "legal": _capture(deckmod.cmd_legal, SimpleNamespace(id=did, fmt=None)),
        "cuts": _capture(deckmod.cmd_cuts, SimpleNamespace(id=did, limit=8)),
        # The clean Arena-importable block (Deck-prefixed, comments/metadata
        # stripped) — what the copy button hands to the clipboard.
        "arena": _capture(deckmod.cmd_arena, SimpleNamespace(id=did)),
    }


def deck_viz(meta, cards, carddata, mana, keywords, by_key, by_name):
    """Structured data for the visual Stats/Mana tabs — the SAME per-card
    primitives cmd_stats/cmd_mana use (deckmod._primary_type, classify_roles,
    classify_cost, parse_pips, _castability), just aggregated for charting instead
    of ASCII bars, so the numbers match the CLI. Pass the big lookup tables in
    (loaded once by collect) so this stays cheap per deck."""
    B = deckmod.BASICS
    types, colors, curve, roles = {}, {}, {}, {}
    cheaper, gated, seen_flag = [], [], set()
    curve_unknown = 0
    for q, n, s, c in cards:
        nl = n.lower()
        cd = carddata.get(nl)
        tline = (cd["type"] if cd else "") or ""
        ptype = "Land" if nl in B else deckmod._primary_type(tline)
        types[ptype] = types.get(ptype, 0) + q
        if ptype == "Land":
            continue
        col = (cd["colors"] if cd else "") or ""
        if col.lower() == "colorless":
            colors["C"] = colors.get("C", 0) + q
        else:
            for ch in col.upper():
                if ch in "WUBRG":
                    colors[ch] = colors.get(ch, 0) + q
        entry = mana.get(nl)
        mv = entry[1] if entry else None
        if mv is None:
            curve_unknown += q
        else:
            curve[min(mv, 7)] = curve.get(min(mv, 7), 0) + q
        for label in deckmod.classify_roles(cd["text"] if cd else ""):
            roles[label] = roles.get(label, 0) + q
        if n not in seen_flag:
            ch2, ga = deckmod.classify_cost(keywords.get(nl), cd["text"] if cd else "")
            if ch2:
                cheaper.append({"name": n, "why": ", ".join(ch2)})
            if ga:
                gated.append({"name": n, "why": ", ".join(ga)})
            seen_flag.add(n)

    # Mana requirements (hybrid-aware) + castability lint — mirrors cmd_mana.
    declared = deckmod._declared_colors(meta)
    strict_pips = {c: 0 for c in "WUBRG"}
    cards_need = {c: 0 for c in "WUBRG"}
    hyb, hybrid_only, mana_unknown = {}, 0, 0
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in B:
            continue
        row = by_key.get((nl, s.lower(), c.lower())) or by_name.get(nl)
        if row and "Land" in deckmod._primary_type((row.get("Type") or "")):
            continue
        entry = mana.get(nl)
        if entry is None:
            mana_unknown += q
            continue
        if not entry[0]:
            continue
        strict, hybrid = deckmod.parse_pips(entry[0])
        for col, cnt in strict.items():
            strict_pips[col] += cnt * q
        for col in strict:
            cards_need[col] += q
        for h in hybrid:
            k = "/".join(sorted(h))
            hyb[k] = hyb.get(k, 0) + q
        if hybrid and not strict:
            hybrid_only += q
    uncastable, off_ident = deckmod._castability(cards, declared, mana, carddata)

    return {
        "types": [{"t": t, "n": types[t]} for t in sorted(types, key=lambda x: -types[x])],
        "colors": {c: colors[c] for c in "WUBRGC" if colors.get(c)},
        "curve": {str(b): curve.get(b, 0) for b in range(8)},
        "curve_unknown": curve_unknown,
        "roles": [{"label": l, "n": roles[l]} for l in deckmod.ROLE_ORDER if roles.get(l)],
        "interaction": sum(roles.get(k, 0) for k in ("Removal (spot)", "Sweeper", "Counter")),
        "cheaper": cheaper, "gated": gated,
        "mana": {
            "declared": "".join(sorted(declared)),
            "strict": [{"c": c, "pips": strict_pips[c], "cards": cards_need[c]}
                       for c in "WUBRG" if cards_need[c]],
            "hybrids": [{"colors": k, "n": v}
                        for k, v in sorted(hyb.items(), key=lambda kv: -kv[1])],
            "hybrid_only": hybrid_only, "unknown": mana_unknown,
            "uncastable": [{"name": n, "why": w} for n, w in uncastable],
            "off_ident": [{"name": n, "why": w} for n, w in off_ident],
        },
    }


def craft_rows(d):
    """Structured craft picks (unowned, on-color, on-theme) for the interactive
    table — from the SAME suggest_scored() the `deck.py suggest` CLI renders, so
    the dashboard table can't drift from the command."""
    try:
        res = deckmod.suggest_scored(d, unowned=True, limit=15)
    except Exception as e:
        eprint(f"WARN: craft picks for deck {d['id']} unavailable ({e})")
        return []
    if not res.get("ok"):
        return []
    return [{"name": p["name"], "rarity": p["rarity"], "decks": p["decks"],
             "matches": p["matches"]} for p in res["picks"]]


def collect():
    """Gather the structured dashboard payload from committed data only."""
    _no_network()
    _, rows = load_rows(DEFAULT_CSV)
    by_key, by_name, qty = deckmod.load_collection()
    rarities = deckmod.load_rarities()
    rar_of = lambda name: rarities.get(name.lower(), "?")
    # Big lookup tables loaded ONCE and shared across every deck's viz (each is a
    # multi-MB CSV read), instead of re-reading them per deck.
    carddata = deckmod.load_card_data()
    mana = deckmod.load_mana()
    keywords = deckmod.load_keywords()
    leg = deckmod.load_legalities()
    cmeta = deckmod.load_card_meta()

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
            "core": d["core"],
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
            "craft": craft_rows(d),
            "viz": deck_viz(meta, cards, carddata, mana, keywords, by_key, by_name),
            "detail": deck_detail(d["id"]),
            # Roster-triage score from the SAME audit_deck() the `deck.py audit` CLI
            # uses (shared scorer, so the dashboard view can't drift from the command).
            "audit": deckmod.audit_deck(d, by_name_qty=qty, carddata=carddata,
                                        mana=mana, leg=leg, cmeta=cmeta),
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
  .actions { display:flex; gap:8px; align-items:center; margin-top:10px; flex-wrap:wrap; }
  .copy { font-size:12px; font-weight:600; padding:5px 11px; border-radius:8px; cursor:pointer;
    background:var(--accent); color:#fff; border:1px solid var(--accent); }
  .copy:hover { filter:brightness(1.08); }
  .vtag { font-size:11px; color:var(--muted); border:1px dashed var(--line); border-radius:999px; padding:1px 8px; }
  .toast { position:fixed; left:50%; bottom:26px; transform:translateX(-50%) translateY(20px);
    background:var(--ink); color:var(--bg); padding:9px 16px; border-radius:8px; font-size:13px;
    opacity:0; pointer-events:none; transition:opacity .18s, transform .18s; z-index:20; }
  .toast.show { opacity:1; transform:translateX(-50%) translateY(0); }
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
  .vpill { font-size:11px; font-weight:700; padding:2px 9px; border-radius:999px; white-space:nowrap;
    text-transform:uppercase; letter-spacing:.03em; }
  .v-tune   { background:color-mix(in srgb,var(--bad) 18%,transparent);   color:var(--bad); }
  .v-craft  { background:color-mix(in srgb,var(--warn) 20%,transparent);  color:var(--warn); }
  .v-review { background:color-mix(in srgb,var(--accent) 18%,transparent);color:var(--accent); }
  .v-ok     { background:color-mix(in srgb,var(--ok) 16%,transparent);    color:var(--ok); }
  .auditsummary { display:flex; gap:8px; flex-wrap:wrap; margin:2px 0 12px; }
  .auditsummary .chip { font-size:12px; color:var(--muted); border:1px solid var(--line);
    border-radius:999px; padding:3px 10px; }
  .auditsummary .chip b { color:var(--ink); }
  #audit td .why { color:var(--muted); font-size:11.5px; }
  #audit tr.clk { cursor:pointer; } #audit tr.clk:hover td { background:color-mix(in srgb,var(--accent) 7%,transparent); }
  .auditnote { color:var(--muted); font-size:12px; margin:10px 0 0; }
  .cell-flag { color:var(--bad); font-weight:600; } .cell-ok { color:var(--muted); }
  #audit a.goto { color:var(--accent); cursor:pointer; text-decoration:none; }
  #audit a.goto:hover { text-decoration:underline; }
  input.filter { width:100%; max-width:340px; padding:8px 10px; border:1px solid var(--line);
    border-radius:8px; background:var(--panel); color:var(--ink); margin-bottom:12px; }
  .foot { color:var(--muted); font-size:12px; margin-top:24px; border-top:1px solid var(--line); padding-top:12px; }
  /* --- visual Stats / Mana panels --- */
  .viz { display:flex; flex-direction:column; gap:15px; }
  .vizsec h4 { margin:0 0 7px; font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); }
  .hbar { display:grid; grid-template-columns:96px 1fr auto; align-items:center; gap:8px; margin:3px 0; font-size:12.5px; }
  .hbar .lbl { color:var(--ink); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .hbar .track { background:var(--bg); border:1px solid var(--line); border-radius:5px; height:14px; overflow:hidden; }
  .hbar .fill { height:100%; background:var(--accent); border-radius:4px; min-width:2px; }
  .hbar .val { font-variant-numeric:tabular-nums; color:var(--muted); min-width:1.6em; text-align:right; }
  .curve { display:flex; align-items:flex-end; gap:6px; height:92px; }
  .curvecol { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100%; gap:4px; }
  .curvebar { width:100%; max-width:34px; background:var(--accent); border-radius:4px 4px 0 0; min-height:2px; }
  .curvecol .cn, .curvecol .cx { font-size:11px; color:var(--muted); font-variant-numeric:tabular-nums; }
  .fill.W,.pipfill.W{background:var(--W)}.fill.U,.pipfill.U{background:var(--U)}.fill.B,.pipfill.B{background:var(--B)}
  .fill.R,.pipfill.R{background:var(--R)}.fill.G,.pipfill.G{background:var(--G)}.fill.C,.pipfill.C{background:var(--C)}
  .flags { display:flex; flex-wrap:wrap; gap:6px; }
  .flag { font-size:11.5px; border:1px solid var(--line); border-radius:6px; padding:2px 7px; background:var(--bg); }
  .castlist { font-size:12px; margin:4px 0 0; padding-left:18px; color:var(--ink); }
  .metaline { font-size:12px; color:var(--muted); margin-top:5px; }
</style>
</head>
<body>
<header>
  <h1>MTG Arena — Roster Dashboard</h1>
  <div class="sub" id="sub"></div>
  <div class="kpis" id="kpis"></div>
</header>
<main>
  <section id="audit-sec">
    <h2>Roster triage — which decks need a tune</h2>
    <div class="auditsummary" id="auditsummary"></div>
    <div id="audit"></div>
    <p class="auditnote" id="auditnote"></p>
  </section>
  <section>
    <h2>Decks &amp; variants</h2>
    <input class="filter" id="filter" placeholder="filter by id, name, or colors…">
    <div class="grid" id="decks"></div>
  </section>
  <section id="wl-sec">
    <h2>Wildcard priority — wishlist</h2>
    <input class="filter" id="wlfilter" placeholder="filter wishlist by card, target, or signal…">
    <div id="wishlist"></div>
  </section>
  <section>
    <h2>Craft plan — whole roster</h2>
    <pre id="plan"></pre>
  </section>
  <div class="foot" id="foot"></div>
</main>
<div id="toast" class="toast"></div>
<script id="data" type="application/json">__DATA__</script>
<script>
  const D = JSON.parse(document.getElementById('data').textContent);
  const esc = s => (s||'').toString().replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
  const WC = {Mythic:'M',Rare:'R',Uncommon:'U',Common:'C'};
  const RANK = {Mythic:3,Rare:2,Uncommon:1,Common:0};
  const rankOf = r => (r in RANK ? RANK[r] : -1);
  const wcCell = r => { const w = WC[r]||'?'; return `<span class="wcpill r-${w}">${w}</span>`; };
  const preOf = txt => { const p = document.createElement('pre'); p.textContent = txt; return p; };

  // Generic sortable table. cols: [{key,label,num,get,html?}]. Click a header to
  // sort (numeric desc-first, text asc-first); click again to flip. Cells go in
  // via textContent — or a fixed, safe html() for the rarity pill only — so no
  // data field can inject markup.
  function buildTable(cols, rows){
    const tbl = document.createElement('table');
    const thead = document.createElement('thead'), htr = document.createElement('tr');
    let sortKey = null, dir = 1;
    cols.forEach(c => {
      const th = document.createElement('th'); th.textContent = c.label;
      if (c.num) th.classList.add('num');
      th.style.cursor = 'pointer';
      th.onclick = () => { if (sortKey === c.key) dir = -dir; else { sortKey = c.key; dir = c.num ? -1 : 1; } draw(); };
      htr.appendChild(th);
    });
    thead.appendChild(htr); tbl.appendChild(thead);
    const tbody = document.createElement('tbody'); tbl.appendChild(tbody);
    function draw(){
      let rs = rows.slice();
      if (sortKey) rs.sort((a,b) => {
        const va = a[sortKey], vb = b[sortKey];
        const cmp = (typeof va === 'number' && typeof vb === 'number') ? va - vb : ('' + va).localeCompare('' + vb);
        return cmp * dir;
      });
      tbody.innerHTML = '';
      for (const r of rs) {
        const tr = document.createElement('tr');
        cols.forEach(c => {
          const td = document.createElement('td'); if (c.num) td.classList.add('num');
          if (c.html) td.innerHTML = c.html(r); else td.textContent = c.get(r);
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      }
    }
    draw(); return tbl;
  }

  // --- visual Stats / Mana renderers (fed by deck.viz; same numbers as the CLI) ---
  function bar(label, value, max, cls) {
    const pct = max > 0 ? Math.round(100 * value / max) : 0;
    return `<div class="hbar"><span class="lbl">${esc(label)}</span>`
      + `<span class="track"><span class="fill ${cls||''}" style="width:${pct}%"></span></span>`
      + `<span class="val">${value}</span></div>`;
  }
  function section(title, inner) { return `<div class="vizsec"><h4>${esc(title)}</h4>${inner}</div>`; }
  function vizEl(html) { const el = document.createElement('div'); el.className = 'viz'; el.innerHTML = html; return el; }

  function renderStats(v) {
    let html = '';
    const cur = v.curve, cmax = Math.max(1, ...Object.values(cur));
    let cols = '';
    for (let b = 0; b < 8; b++) {
      const n = cur[String(b)] || 0;
      cols += `<div class="curvecol"><span class="cn">${n||''}</span>`
        + `<div class="curvebar" style="height:${n?Math.max(Math.round(100*n/cmax),3):0}%" title="MV ${b===7?'7+':b}: ${n}"></div>`
        + `<span class="cx">${b===7?'7+':b}</span></div>`;
    }
    html += section('Mana curve' + (v.curve_unknown ? ` · ${v.curve_unknown} unknown` : ''), `<div class="curve">${cols}</div>`);
    const tmax = Math.max(1, ...v.types.map(t => t.n));
    html += section('Types', v.types.map(t => bar(t.t, t.n, tmax)).join(''));
    const ck = Object.keys(v.colors), clmax = Math.max(1, ...ck.map(c => v.colors[c]));
    if (ck.length) html += section('Color identity', ck.map(c => bar(c, v.colors[c], clmax, c)).join(''));
    if (v.roles.length) {
      const rmax = Math.max(1, ...v.roles.map(r => r.n));
      html += section('Functional roles', v.roles.map(r => bar(r.label, r.n, rmax)).join('')
        + `<div class="metaline">interaction total: <b>${v.interaction}</b> (removal + sweeper + counter)</div>`);
    }
    if (v.cheaper.length || v.gated.length) {
      const chips = v.cheaper.map(x => `<span class="flag" title="${esc(x.why)}">◊ ${esc(x.name)}</span>`).join('')
        + v.gated.map(x => `<span class="flag" title="${esc(x.why)}">△ ${esc(x.name)}</span>`).join('');
      html += section('Cost flags — ◊ cheaper than MV · △ added cost', `<div class="flags">${chips}</div>`);
    }
    return vizEl(html);
  }

  function renderMana(v) {
    const m = v.mana; let html = '';
    if (m.strict.length) {
      const smax = Math.max(1, ...m.strict.map(x => x.pips));
      html += section('Strict color requirements (pips that MUST be paid with that color)',
        m.strict.map(x => `<div class="hbar"><span class="lbl">${x.c}</span>`
          + `<span class="track"><span class="fill pipfill ${x.c}" style="width:${Math.round(100*x.pips/smax)}%"></span></span>`
          + `<span class="val">${x.pips} · ${x.cards}c</span></div>`).join(''));
    } else {
      html += section('Strict color requirements', '<div class="metaline">No strict single-color pips.</div>');
    }
    if (m.hybrids.length) {
      html += section('Hybrid pips (payable with either color)',
        `<div class="flags">${m.hybrids.map(h => `<span class="flag"><b>${esc(h.colors)}</b> ×${h.n}</span>`).join('')}</div>`);
    }
    let cast;
    if (!m.declared) cast = '<div class="metaline">No declared colors — castability lint off.</div>';
    else if (!m.uncastable.length && !m.off_ident.length) cast = `<span class="badge b-ok">every nonland card fits ${esc(m.declared)} ✓</span>`;
    else {
      cast = '';
      if (m.uncastable.length) cast += `<div class="metaline"><span class="badge b-missing">${m.uncastable.length} uncastable off ${esc(m.declared)}</span></div>`
        + `<ul class="castlist">${m.uncastable.map(x => `<li>${esc(x.name)} — ${esc(x.why)}</li>`).join('')}</ul>`;
      if (m.off_ident.length) cast += `<div class="metaline"><span class="badge b-short">${m.off_ident.length} stray outside ${esc(m.declared)}</span></div>`
        + `<ul class="castlist">${m.off_ident.map(x => `<li>${esc(x.name)} — ${esc(x.why)}</li>`).join('')}</ul>`;
    }
    html += section('Castability', cast);
    const notes = [];
    if (m.hybrid_only) notes.push(`${m.hybrid_only} hybrid-only card(s)`);
    if (m.unknown) notes.push(`${m.unknown} card(s) with no cost data`);
    if (notes.length) html += `<div class="metaline">${notes.join(' · ')}</div>`;
    return vizEl(html);
  }

  document.getElementById('sub').textContent = 'Read-only snapshot · generated ' + D.generated +
    ' · numbers match `deck.py` exactly (captured from the same commands).';
  const t = D.totals;
  document.getElementById('kpis').innerHTML =
    `<div class="kpi"><b>${t.printings}</b><span>printings</span></div>` +
    `<div class="kpi"><b>${t.decks}</b><span>decks</span></div>` +
    `<div class="kpi"><b>${t.buildable}/${t.decks}</b><span>buildable now</span></div>`;
  document.getElementById('plan').textContent = D.roster_plan || '(no craft plan)';

  // Wishlist — interactive: filterable, sortable, grouped by tier.
  const labels = {A:'Tier A — craft first', B:'Tier B — targeted upgrade', C:'Tier C — situational'};
  function rollStr(o){ return ['Mythic','Rare','Uncommon','Common'].filter(k=>o&&o[k]).map(k=>`${o[k]} ${k}`).join(' · '); }
  const WLCOLS = [
    {key:'name',   label:'Card',   get:r=>r.name},
    {key:'_rank',  label:'WC',     num:true, html:r=>wcCell(r.rarity)},
    {key:'target', label:'Target', get:r=>r.target},
    {key:'reuse',  label:'reuse',  num:true, get:r=>r.reuse},
    {key:'pri',    label:'pri',    num:true, get:r=>r.pri},
    {key:'sig',    label:'signal', get:r=>r.sig},
  ];
  const wlWrap = document.getElementById('wishlist');
  const anyWl = ['A','B','C'].some(t => (D.wishlist[t]||[]).length);
  function renderWishlist(q){
    q = (q||'').toLowerCase().trim();
    wlWrap.innerHTML = '';
    for (const tier of ['A','B','C']) {
      let rows = (D.wishlist[tier]||[]).map(r => ({...r, _rank: rankOf(r.rarity)}));
      if (q) rows = rows.filter(r => (r.name+' '+r.target+' '+r.sig).toLowerCase().includes(q));
      if (!rows.length) continue;
      const hdr = document.createElement('div'); hdr.className = 'tierhdr';
      hdr.innerHTML = `<h3>${labels[tier]}</h3><span class="roll">${rows.length} cards · ${esc(rollStr(D.wishlist_rollup[tier]))}</span>`;
      wlWrap.appendChild(hdr);
      wlWrap.appendChild(buildTable(WLCOLS, rows));
    }
  }
  if (anyWl) { renderWishlist(''); document.getElementById('wlfilter').addEventListener('input', e => renderWishlist(e.target.value)); }
  else document.getElementById('wl-sec').style.display = 'none';

  // Clipboard with a fallback for non-secure contexts (e.g. opening the file
  // locally); on GitHub Pages the async Clipboard API path is used.
  const toastEl = document.getElementById('toast');
  function toast(msg){ toastEl.textContent = msg; toastEl.classList.add('show');
    clearTimeout(toast._t); toast._t = setTimeout(()=>toastEl.classList.remove('show'), 1500); }
  function copyText(text, label){
    const ok = ()=>toast(label + ' copied to clipboard');
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(ok).catch(()=>fallbackCopy(text, ok));
    } else fallbackCopy(text, ok);
  }
  function fallbackCopy(text, ok){
    const ta = document.createElement('textarea'); ta.value = text;
    ta.style.position='fixed'; ta.style.opacity='0'; document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); ok(); } catch(e) { toast('Copy failed — select the Arena tab manually'); }
    document.body.removeChild(ta);
  }

  // Decks
  const TABS = [['craft','Craft picks'],['arena','Arena import'],['stats','Stats'],['mana','Mana'],['cuts','Cuts'],['legal','Legal']];
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
      const vtag = d.variant ? `<span class="vtag">variant of #${esc(d.core)}</span>` : '';
      return `<div class="card" data-id="${esc(d.id)}">
        <div class="top"><div><h3>${esc(d.name)} <span class="id">#${esc(d.id)}</span></h3></div>${badge(d)}</div>
        <div class="arch">${esc(d.archetype)}</div>
        <div class="meta">${vtag}${d.format?`<span>${esc(d.format)}</span>·`:''}${pips(d.colors)}<span>${d.total} cards</span></div>
        <div class="wc">${d.buildable?'<span class="badge b-ok">no wildcards needed</span>':'to finish: '+esc(d.wc||'—')}</div>
        <div class="actions">
          <button class="copy" data-copy>⧉ Copy Arena import</button>
          <span class="expand">▸ analysis</span>
        </div>
        <div class="detail"><div class="tabs">${tabs}</div><div class="detailbody"></div></div>
      </div>`;
    }).join('');
    grid.querySelectorAll('.card').forEach(cardEl=>{
      const d = list.find(x=>x.id===cardEl.dataset.id);
      const body = cardEl.querySelector('.detailbody');
      const CRAFTCOLS = [
        {key:'name',    label:'Card',    get:r=>r.name},
        {key:'_rank',   label:'WC',      num:true, html:r=>wcCell(r.rarity)},
        {key:'decks',   label:'reuse',   num:true, get:r=>r.decks},
        {key:'matches', label:'Matches', get:r=>r.matches.join(', ')},
      ];
      const show = k => {
        body.innerHTML = '';
        if (k === 'craft') {
          if (!d.craft.length) { body.appendChild(preOf('No craft picks — nothing on-color and on-theme to craft here.')); return; }
          body.appendChild(buildTable(CRAFTCOLS, d.craft.map(r => ({...r, _rank: rankOf(r.rarity)}))));
        } else if (k === 'stats') body.appendChild(renderStats(d.viz));
        else if (k === 'mana') body.appendChild(renderMana(d.viz));
        else body.appendChild(preOf(d.detail[k] || '(no output)'));
      };
      show('craft');
      cardEl.querySelector('[data-copy]').onclick = () => {
        const block = d.detail.arena || '';
        copyText(block, `#${d.id} ${d.name} import`);
      };
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

  // Roster triage table — one row per deck from the SAME audit_deck() scorer the
  // `deck.py audit` CLI uses. Sorted worst-first; click a row to filter the decks
  // below to that family.
  const SEV = {TUNE:0, craft:1, review:2, ok:3};
  const VLAB = {TUNE:'★ tune', craft:'craft', review:'review', ok:'ok'};
  const VCLS = {TUNE:'v-tune', craft:'v-craft', review:'v-review', ok:'v-ok'};
  const flagCell = (n, suffix) => n ? `<span class="cell-flag">${n}${suffix}</span>`
                                    : '<span class="cell-ok">✓</span>';
  const arows = D.decks.map(d => {
    const a = d.audit;
    const cast = (!a.uncast && !a.stray) ? '✓'
      : [a.uncast ? `${a.uncast}u` : '', a.stray ? `${a.stray}s` : ''].filter(Boolean).join(' ');
    return { id:d.id, name:d.name, deck:`#${d.id} ${d.name}`, sz:a.sz,
      short:a.short, illegal:a.illegal, uncast:a.uncast, stray:a.stray, cast,
      _castsev:a.uncast*100 + a.stray, int:a.int, thm:a.thm,
      verdict:a.verdict, why:a.why, _sev:SEV[a.verdict] };
  });
  arows.sort((x,y) => x._sev - y._sev || x.id.length - y.id.length || (''+x.id).localeCompare(''+y.id));
  const ACOLS = [
    {key:'deck',    label:'Deck',    html:r=>`<a class="goto" data-goto="${esc(r.name)}">${esc(r.deck)}</a>`},
    {key:'sz',      label:'Sz',      num:true, get:r=>r.sz},
    {key:'short',   label:'Own',     num:true, html:r=>flagCell(r.short, '✗')},
    {key:'illegal', label:'Legal',   num:true, html:r=>flagCell(r.illegal, '✗')},
    {key:'_castsev',label:'Cast',    num:true, html:r=>(r.uncast||r.stray)?`<span class="cell-flag">${esc(r.cast)}</span>`:'<span class="cell-ok">✓</span>'},
    {key:'int',     label:'Int',     num:true, get:r=>r.int},
    {key:'thm',     label:'Thm',     num:true, get:r=>r.thm},
    {key:'_sev',    label:'Verdict', num:true, html:r=>`<span class="vpill ${VCLS[r.verdict]}">${VLAB[r.verdict]}</span>`+(r.why?` <span class="why">${esc(r.why)}</span>`:'')},
  ];
  const auditWrap = document.getElementById('audit');
  const auditTbl = buildTable(ACOLS, arows);
  auditTbl.querySelectorAll('tbody tr').forEach(tr => tr.classList.add('clk'));
  auditWrap.appendChild(auditTbl);
  const c = {TUNE:0, craft:0, review:0, ok:0};
  arows.forEach(r => c[r.verdict]++);
  document.getElementById('auditsummary').innerHTML =
    `<span class="chip"><b>${c.TUNE}</b> to tune</span>` +
    `<span class="chip"><b>${c.craft}</b> to craft</span>` +
    `<span class="chip"><b>${c.review}</b> to review</span>` +
    `<span class="chip"><b>${c.ok}</b> ok</span>`;
  document.getElementById('auditnote').textContent =
    'Offline triage — same numbers as `deck.py audit`. Own/Legal/Cast ✓ = clean; ' +
    'Cast Nu = uncastable in the deck’s colors, Ns = off-identity stray. ★ tune = a hard ' +
    'problem (illegal or uncastable card); craft = just unbuilt; review = a soft flag ' +
    '(off-color strays or thin interaction). Click a deck to filter the list below.';
  auditWrap.addEventListener('click', e => {
    const a = e.target.closest('[data-goto]');
    if (!a) return;
    const f = document.getElementById('filter');
    f.value = a.dataset.goto;
    f.dispatchEvent(new Event('input'));
    document.getElementById('decks').scrollIntoView({behavior:'smooth', block:'start'});
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
