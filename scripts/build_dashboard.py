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
        # Canonical once-per-card interaction (matches deck.py stats / the triage Int
        # column); the old bucket-sum double-counted a card in >1 interaction role (F7).
        "interaction": deckmod.role_tally(cards, carddata)["interaction"],
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
            # Card multiset for the client-side "stale deck" compare — SAME semantics
            # as `deck.py verify` (deckmod._multiset: keyed by lowercased name,
            # quantities summed, printings/basics fungible), so the browser diff and
            # the CLI can't disagree. Stored as {name_lower: [display, qty]}.
            "cards": {nl: [disp, q] for nl, (disp, q) in deckmod._multiset(cards).items()},
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
  :root, [data-theme="dark"] {
    --bg:#0a0c0f; --panel:#171b21; --panel2:#12151a; --elev:#141820; --elev2:#101318;
    --ink:#e6e9ef; --ink-bright:#f2f4f8; --ink-soft:#d5dae3; --ink2:#8b93a1; --ink2b:#9aa4b2; --ink3:#6b7480;
    --line:rgba(255,255,255,.07); --line2:rgba(255,255,255,.1); --hair:rgba(255,255,255,.05);
    --fill:rgba(255,255,255,.03); --fill2:rgba(255,255,255,.02);
    --accent:#8f7bf2; --accent-ink:#c9c0ff; --accent-bg:rgba(143,123,242,.16); --accent-line:rgba(143,123,242,.3);
    --header:rgba(10,12,15,.82); --cardsh:rgba(0,0,0,.6);
    --ok:#4bbd83; --warn:#c68b18; --bad:#dd6a4d;
    --code-bg:#0b0e13; --code-ink:#cdd6e4;
  }
  [data-theme="light"] {
    --bg:#eef0f4; --panel:#ffffff; --panel2:#f6f7fa; --elev:#ffffff; --elev2:#f1f3f7;
    --ink:#1b1e25; --ink-bright:#0e1116; --ink-soft:#39414f; --ink2:#5a6472; --ink2b:#48505e; --ink3:#8a93a1;
    --line:rgba(18,24,34,.1); --line2:rgba(18,24,34,.15); --hair:rgba(18,24,34,.07);
    --fill:rgba(18,24,34,.035); --fill2:rgba(18,24,34,.02);
    --accent:#6a57e0; --accent-ink:#5646c4; --accent-bg:rgba(106,87,224,.12); --accent-line:rgba(106,87,224,.32);
    --header:rgba(238,240,244,.85); --cardsh:rgba(30,42,66,.14);
    --ok:#1c9d5f; --warn:#b7770d; --bad:#c9482b;
    --code-bg:#f4f5f8; --code-ink:#2b3240;
  }
  /* Self-hosted-free typography: the design's faces first, system fallbacks so the
     page stays fully offline (no CDN, no committed font bloat). */
  :root {
    --font-display:'Space Grotesk', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    --font-body:'Manrope', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    --font-mono:'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    --W:#efe4bf; --U:#5aa9ec; --B:#b9a6d6; --R:#ec7a63; --G:#6cc684; --Cc:#b9c0cc;
    --Wf:#2a2618; --Uf:#06263d; --Bf:#241833; --Rf:#350e08; --Gf:#06280f; --Ccf:#1c2129;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); font-family:var(--font-body);
    -webkit-font-smoothing:antialiased; transition:background .3s,color .3s; }
  a { color:var(--accent); text-decoration:none; }
  a:hover { color:var(--accent-ink); text-decoration:underline; }
  ::selection { background:var(--accent-bg); }
  ::-webkit-scrollbar { height:10px; width:10px; }
  ::-webkit-scrollbar-thumb { background:var(--line2); border-radius:6px; }
  ::-webkit-scrollbar-track { background:transparent; }
  pre { margin:0; }
  h1,h2,h3,h4 { font-family:var(--font-display); }
  .mono { font-family:var(--font-mono); }
  @keyframes auraDrift { 0%{transform:translate(-3%,-2%) scale(1)} 50%{transform:translate(4%,4%) scale(1.1)} 100%{transform:translate(-3%,-2%) scale(1)} }
  @keyframes auraDrift2 { 0%{transform:translate(3%,0) scale(1.05)} 50%{transform:translate(-5%,3%) scale(1)} 100%{transform:translate(3%,0) scale(1.05)} }
  @keyframes auraPulse { 0%,100%{opacity:.75} 50%{opacity:1} }
  @keyframes foilShift { to{background-position:200% 0} }
  @keyframes previewIn { from{opacity:0;transform:scale(.96)} to{opacity:1;transform:none} }
  @keyframes spin { to{transform:rotate(360deg)} }
  @keyframes impactPulse { 0%,100%{box-shadow:0 0 0 1px var(--accent-line),0 0 26px -6px var(--accent-line)} 50%{box-shadow:0 0 0 1px var(--accent),0 0 34px -2px var(--accent-line)} }
  @media (prefers-reduced-motion: reduce) { * { animation-duration:.001ms !important; animation-iteration-count:1 !important; transition-duration:.001ms !important; } }

  /* aura background */
  .aura { position:fixed; inset:0; pointer-events:none; z-index:0; overflow:hidden; }
  .aura b { position:absolute; border-radius:50%; display:block; }
  .aura .a1 { top:-170px; left:16%; width:540px; height:380px; background:radial-gradient(circle,rgba(143,123,242,.26),transparent 68%); filter:blur(52px); animation:auraDrift 15s ease-in-out infinite, auraPulse 7s ease-in-out infinite; }
  .aura .a2 { top:-130px; right:10%; width:440px; height:320px; background:radial-gradient(circle,rgba(90,169,236,.15),transparent 66%); filter:blur(58px); animation:auraDrift2 19s ease-in-out infinite; }
  .aura .a3 { top:-90px; left:52%; width:360px; height:260px; background:radial-gradient(circle,rgba(108,198,132,.09),transparent 64%); filter:blur(60px); animation:auraDrift 23s ease-in-out infinite; }
  [data-theme="light"] .aura { opacity:.6; }

  /* header */
  header { position:sticky; top:0; z-index:10; background:var(--header); backdrop-filter:blur(14px);
    -webkit-backdrop-filter:blur(14px); border-bottom:1px solid var(--line); padding:18px 24px; }
  .hwrap { max-width:1180px; margin:0 auto; display:flex; flex-wrap:wrap; align-items:flex-end; justify-content:space-between; gap:18px; }
  .htitle { display:flex; align-items:center; gap:11px; }
  .hdot { width:9px; height:9px; border-radius:2px; background:var(--accent); box-shadow:0 0 12px 2px var(--accent-line); }
  h1 { margin:0; font-size:23px; font-weight:600; letter-spacing:-.01em; color:var(--ink-bright); text-shadow:0 0 34px var(--accent-bg); }
  h1 .dim { color:var(--ink3); font-weight:500; }
  .hsub { margin-top:6px; color:var(--ink2); font-size:12.5px; }
  .hsub .link { cursor:pointer; color:var(--accent-ink); }
  .kbd { font-family:var(--font-mono); border:1px solid var(--line2); border-radius:5px; padding:1px 6px; font-size:11px; }
  .stalechip { cursor:pointer; font-size:11px; font-weight:600; padding:1px 8px; border-radius:999px;
    background:rgba(214,150,40,.16); color:#c68b18; border:1px solid rgba(230,177,60,.3); }
  .hactions { display:flex; gap:11px; flex-wrap:wrap; align-items:stretch; }
  .iconbtn { align-self:stretch; width:42px; border-radius:12px; border:1px solid var(--line); background:var(--fill);
    color:var(--ink2); font-size:15px; cursor:pointer; transition:all .15s; }
  .iconbtn:hover { color:var(--accent-ink); border-color:var(--accent-line); }
  .kpi { background:var(--fill); border:1px solid var(--line); border-radius:12px; padding:9px 16px; min-width:90px; }
  .kpi.hot { background:var(--accent-bg); border-color:var(--accent-line); box-shadow:0 0 22px -8px var(--accent-line); }
  .kpi .n { font-family:var(--font-display); font-size:24px; font-weight:600; color:var(--ink-bright); line-height:1.1; font-variant-numeric:tabular-nums; }
  .kpi.hot .n { color:var(--accent-ink); }
  .kpi .n small { color:var(--ink2); font-size:16px; }
  .kpi .lbl { font-size:10px; text-transform:uppercase; letter-spacing:.12em; color:var(--ink2); margin-top:3px; }
  .kpi.hot .lbl { color:var(--accent-ink); opacity:.8; }

  main { position:relative; z-index:1; max-width:1180px; margin:0 auto; padding:28px 24px 64px; }
  section { margin-bottom:40px; scroll-margin-top:90px; }
  h2.sec { display:flex; align-items:center; gap:10px; font-size:12px; font-weight:600; text-transform:uppercase;
    letter-spacing:.16em; color:var(--ink2); margin:0 0 16px; padding-bottom:10px; border-bottom:1px solid var(--line); }
  h2.sec .tick { width:14px; height:2px; background:var(--accent); box-shadow:0 0 8px var(--accent); border-radius:2px; }
  .panel { background:linear-gradient(180deg,var(--elev),var(--elev2)); border:1px solid var(--line); border-radius:14px; }
  .ptitle { font-family:var(--font-display); font-size:11px; text-transform:uppercase; letter-spacing:.12em; color:var(--ink2); margin-bottom:13px; }

  /* analytics */
  .analytics { display:flex; gap:16px; flex-wrap:wrap; align-items:stretch; margin-bottom:16px; }
  .ring-card { flex:0 0 auto; display:flex; align-items:center; gap:16px; padding:16px 20px; }
  .ring { width:78px; height:78px; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow:0 0 24px -6px var(--accent-line); }
  .ring .hole { width:57px; height:57px; border-radius:50%; background:var(--elev2); display:flex; flex-direction:column; align-items:center; justify-content:center; }
  .ring .rn { font-family:var(--font-display); font-size:18px; font-weight:600; color:var(--ink-bright); line-height:1; }
  .ring .rl { font-size:8px; text-transform:uppercase; letter-spacing:.1em; color:var(--ink2); margin-top:2px; }
  .needs-card { flex:1; min-width:290px; padding:15px 20px 12px; }
  .needbar { display:flex; align-items:center; gap:12px; margin-bottom:10px; }
  .needbar .nl { width:82px; font-size:12px; color:var(--ink-soft); font-family:var(--font-mono); }
  .needbar .nt { flex:1; height:9px; border-radius:6px; background:var(--hair); overflow:hidden; }
  .needbar .nf { height:100%; border-radius:6px; }
  .needbar .nc { width:24px; text-align:right; font-family:var(--font-mono); font-size:12px; color:var(--ink-bright); }
  .distgrid { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:16px; }
  .dist-card { padding:15px 18px; }
  .cbars { display:flex; align-items:flex-end; justify-content:space-around; height:96px; gap:10px; }
  .cbar { flex:1; display:flex; flex-direction:column; align-items:center; gap:6px; height:100%; justify-content:flex-end; }
  .cbar .cn { font-size:11px; font-family:var(--font-mono); color:var(--ink-soft); }
  .cbar .cf { width:100%; max-width:34px; border-radius:5px 5px 0 0; transition:height .4s ease; }
  .cbar .cp { width:16px; height:16px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-size:9px; font-weight:800; border:1px solid rgba(0,0,0,.28); }
  .fbar { display:flex; align-items:center; gap:12px; margin-bottom:10px; }
  .fbar .fl { width:96px; font-size:12px; color:var(--ink-soft); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .fbar .ft { flex:1; height:9px; border-radius:6px; background:var(--hair); overflow:hidden; }
  .fbar .ff { height:100%; border-radius:6px; background:linear-gradient(90deg,#9a86ff,#6a57e0); }
  .fbar .fc { width:24px; text-align:right; font-family:var(--font-mono); font-size:12px; color:var(--ink-bright); }
  .rcurve { display:flex; align-items:flex-end; justify-content:space-around; height:96px; gap:8px; }
  .rcol { flex:1; display:flex; flex-direction:column; align-items:center; gap:6px; height:100%; justify-content:flex-end; }
  .rcol .rn2 { font-size:10px; font-family:var(--font-mono); color:var(--ink2); }
  .rcol .rf { width:100%; border-radius:4px 4px 0 0; background:linear-gradient(180deg,#9a86ff,#6a57e0); box-shadow:0 0 10px -3px var(--accent-line); }
  .rcol .rm { font-size:9.5px; font-family:var(--font-mono); color:var(--ink3); }

  /* controls */
  .controls { display:flex; justify-content:space-between; align-items:center; gap:14px; flex-wrap:wrap; margin-bottom:14px; }
  .ctl-left { display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
  input.filter { padding:9px 13px; border:1px solid var(--line2); border-radius:9px; background:var(--fill2); color:var(--ink); font-size:13px; font-family:inherit; outline:none; }
  input.filter:focus { border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-bg); }
  #deckfilter { width:250px; max-width:100%; }
  .colchips { display:flex; gap:5px; }
  .colchip { width:26px; height:26px; border-radius:8px; display:inline-flex; align-items:center; justify-content:center; font-family:var(--font-display); font-size:12px; font-weight:700; cursor:pointer; user-select:none; transition:all .15s; background:var(--fill); color:var(--ink2); border:1px solid var(--line2); }
  .viewbtns { display:flex; gap:6px; }
  .pill, .viewbtn, .simchip { font-family:inherit; font-size:11.5px; font-weight:600; padding:6px 12px; cursor:pointer; user-select:none; transition:all .15s; border:1px solid var(--line2); background:var(--fill2); color:var(--ink2); }
  .pill { border-radius:999px; }
  .viewbtn, .simchip { border-radius:8px; }
  .pill.on, .viewbtn.on, .simchip.on { border-color:var(--accent); background:var(--accent-bg); color:var(--accent-ink); }
  .quickrow { display:flex; align-items:center; gap:14px; flex-wrap:wrap; margin-bottom:16px; }
  .quickrow .pills { display:flex; gap:6px; flex-wrap:wrap; }
  .grow { flex:1; }
  .ghostbtn { font-size:11.5px; font-weight:600; padding:6px 12px; border-radius:8px; cursor:pointer; color:var(--ink2); border:1px solid var(--line2); background:var(--fill2); transition:all .15s; }
  .ghostbtn:hover { color:var(--accent-ink); border-color:var(--accent-line); }
  .impactbanner { display:flex; align-items:center; gap:10px; margin-bottom:14px; padding:9px 14px; border-radius:10px; background:var(--accent-bg); border:1px solid var(--accent-line); font-size:12.5px; color:var(--ink); }
  .impactbanner strong.c { color:var(--accent-ink); }
  .impactbanner .x { cursor:pointer; font-size:12px; font-weight:600; color:var(--accent-ink); }

  /* deck grid */
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(324px,1fr)); gap:14px; align-items:start; }
  .deck { background:linear-gradient(180deg,var(--panel),var(--panel2)); border:1px solid var(--line); border-radius:14px; padding:16px; box-shadow:0 12px 30px -22px var(--cardsh); transition:border-color .15s,transform .15s; }
  .deck:hover { border-color:var(--accent-line); transform:translateY(-2px); }
  .deck.impacted { animation:impactPulse 1.6s ease-in-out infinite; border-color:var(--accent-line); }
  .deck .dtop { display:flex; justify-content:space-between; align-items:flex-start; gap:8px; }
  .deck h3 { margin:0; font-size:15.5px; font-weight:600; color:var(--ink-bright); }
  .deck h3 .id { color:var(--ink3); font-weight:500; font-size:12.5px; }
  .pin { cursor:pointer; color:var(--ink3); margin-right:5px; }
  .pin.on { color:var(--accent-ink); }
  .badges { display:flex; gap:6px; flex-wrap:wrap; justify-content:flex-end; }
  .badge { font-size:11px; font-weight:600; padding:2px 9px; border-radius:999px; white-space:nowrap; }
  .b-ok { background:rgba(58,204,138,.14); color:#4bbd83; border:1px solid rgba(99,214,154,.28); }
  .b-missing { background:rgba(236,110,90,.16); color:#dd6a4d; border:1px solid rgba(240,138,114,.3); }
  .b-short { background:rgba(214,150,40,.16); color:#c68b18; border:1px solid rgba(230,177,60,.3); }
  .deck .arch { color:var(--ink2); font-size:12.5px; margin:7px 0 9px; line-height:1.45; min-height:2.6em; }
  .deck .metaline { display:flex; gap:9px; align-items:center; flex-wrap:wrap; font-size:11.5px; color:var(--ink2); }
  .vtag { border:1px dashed var(--line2); border-radius:999px; padding:1px 9px; color:var(--ink2b); }
  .pips { display:inline-flex; gap:4px; }
  .pip { width:16px; height:16px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-size:9px; font-weight:800; border:1px solid rgba(0,0,0,.28); }
  .pip.W{background:var(--W);color:var(--Wf)} .pip.U{background:var(--U);color:var(--Uf)} .pip.B{background:var(--B);color:var(--Bf)}
  .pip.R{background:var(--R);color:var(--Rf)} .pip.G{background:var(--G);color:var(--Gf)} .pip.C{background:var(--Cc);color:var(--Ccf)}
  .minirow { display:flex; align-items:flex-end; gap:14px; margin-top:13px; padding:11px 12px; background:var(--fill2); border:1px solid var(--hair); border-radius:10px; }
  .minipie-wrap { display:flex; flex-direction:column; align-items:center; gap:4px; }
  .minipie { width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow:0 0 14px -3px var(--cardsh); }
  .minipie .hole { width:23px; height:23px; border-radius:50%; background:var(--panel2); display:flex; align-items:center; justify-content:center; font-family:var(--font-mono); font-size:9.5px; font-weight:800; color:var(--accent-ink); }
  .minicap { font-size:8.5px; text-transform:uppercase; letter-spacing:.1em; color:var(--ink3); }
  .minicurve { flex:1; min-width:0; }
  .minicurve .bars { display:flex; align-items:flex-end; gap:4px; height:36px; }
  .minicurve .bars i { flex:1; background:linear-gradient(180deg,#9a86ff,#6a57e0); border-radius:3px 3px 0 0; min-height:3px; box-shadow:0 0 8px -2px var(--accent-line); }
  .minicurve .lbls { display:flex; gap:4px; margin-top:4px; }
  .minicurve .lbls i { flex:1; text-align:center; font-size:8.5px; color:var(--ink3); font-family:var(--font-mono); font-style:normal; }
  .curvena { flex:1; font-size:11px; color:var(--ink3); font-family:var(--font-mono); }
  .wcline { margin-top:11px; font-family:var(--font-mono); font-size:12px; color:var(--ink2); }
  .wcline b { color:var(--accent-ink); font-weight:600; }
  .drow { display:flex; gap:10px; align-items:center; margin-top:12px; flex-wrap:wrap; }
  .cta { font-family:inherit; font-size:12px; font-weight:600; padding:7px 12px; border-radius:9px; cursor:pointer; color:#fff; background:linear-gradient(180deg,#9a86ff,#7c66f0); border:1px solid rgba(255,255,255,.14); box-shadow:0 0 0 1px var(--accent-line),0 6px 16px -8px var(--accent-line); }
  .cta:hover { filter:brightness(1.08); }
  .expand { cursor:pointer; user-select:none; font-size:12px; font-weight:600; color:var(--accent); }
  .iconlink { cursor:pointer; font-size:13px; color:var(--ink3); padding:2px 4px; }
  .iconlink:hover { color:var(--accent-ink); }
  .detail { margin-top:13px; border-top:1px solid var(--line); padding-top:12px; }
  .tabs { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px; align-items:center; }
  .tab { font-size:12px; padding:5px 11px; border-radius:8px; cursor:pointer; transition:all .15s; font-family:inherit; border:1px solid var(--line2); background:var(--fill2); color:var(--ink2); }
  .tab.on { border-color:var(--accent); background:var(--accent-bg); color:var(--accent-ink); box-shadow:0 0 14px -3px var(--accent-line); }
  pre.code { background:var(--code-bg); border:1px solid var(--line); color:var(--code-ink); padding:13px; border-radius:10px; font-family:var(--font-mono); font-size:12px; line-height:1.55; overflow-x:auto; white-space:pre; }
  table.dt { width:100%; border-collapse:collapse; font-size:12.5px; }
  table.dt th { text-align:left; padding:6px 8px; border-bottom:1px solid var(--line2); font-weight:600; font-size:10.5px; text-transform:uppercase; letter-spacing:.08em; cursor:pointer; user-select:none; white-space:nowrap; color:var(--ink2); }
  table.dt th.num, table.dt td.num { text-align:right; }
  table.dt th.on { color:var(--accent-ink); }
  table.dt td { padding:6px 8px; border-bottom:1px solid var(--hair); color:var(--ink-soft); }
  table.dt td.re { text-align:right; font-variant-numeric:tabular-nums; color:var(--accent-ink); }
  table.dt td.mt { color:var(--ink2); font-size:11.5px; }
  .hovname { cursor:help; border-bottom:1px dotted var(--line2); }
  .scry { font-size:10px; color:var(--ink3); text-decoration:none; }
  .wcp { font-family:var(--font-mono); font-weight:800; font-size:12.5px; }
  .wcp.Rare{color:#c99b1e} .wcp.Uncommon{color:#8595a8} .wcp.Common{color:#8a94a2}
  .wcp.Mythic { background:linear-gradient(100deg,#f4a03a,#ffe4ab,#f4a03a,#ffca6d); background-size:200% 100%; -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; color:transparent; animation:foilShift 2.6s linear infinite; }

  /* compact */
  .compact { background:linear-gradient(180deg,var(--elev),var(--elev2)); border:1px solid var(--line); border-radius:12px; overflow:hidden; }
  table.ct { width:100%; border-collapse:collapse; font-size:13px; }
  table.ct th { text-align:left; padding:9px 12px; border-bottom:1px solid var(--line2); font-weight:600; font-size:10.5px; text-transform:uppercase; letter-spacing:.08em; cursor:pointer; user-select:none; white-space:nowrap; color:var(--ink2); }
  table.ct th.num, table.ct td.num { text-align:right; }
  table.ct th.on { color:var(--accent-ink); }
  table.ct td { padding:9px 12px; border-bottom:1px solid var(--hair); color:var(--ink-soft); }
  table.ct td .id { color:var(--ink3); font-weight:400; font-size:11.5px; }
  table.ct td.wc { font-family:var(--font-mono); font-size:12px; color:var(--accent-ink); }
  .miniimport { font-family:inherit; font-size:12px; font-weight:600; padding:5px 9px; border-radius:8px; cursor:pointer; color:var(--accent-ink); background:var(--accent-bg); border:1px solid var(--accent-line); }
  .emptymsg { color:var(--ink2); font-size:13px; padding:20px 0; }

  /* leverage */
  .levgrid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:12px; }
  .lev { display:flex; align-items:center; gap:10px; padding:12px 14px; border-radius:12px; cursor:pointer; background:linear-gradient(180deg,var(--panel),var(--panel2)); border:1px solid var(--line); transition:border-color .15s; }
  .lev:hover { border-color:var(--accent-line); }
  .lev.on { border-color:var(--accent); box-shadow:0 0 18px -6px var(--accent-line); }
  .lev .cnt { width:34px; height:34px; flex:0 0 auto; border-radius:9px; display:flex; align-items:center; justify-content:center; font-family:var(--font-display); font-size:15px; font-weight:700; color:var(--accent-ink); background:var(--accent-bg); border:1px solid var(--accent-line); }
  .lev .body { min-width:0; flex:1; }
  .lev .nm { font-size:13.5px; font-weight:600; color:var(--ink-bright); cursor:help; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .lev .ds { font-size:11px; color:var(--ink2); margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .sechint { font-size:12.5px; color:var(--ink2); margin-bottom:14px; line-height:1.5; max-width:640px; }

  /* wishlist */
  .wltop { display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom:16px; }
  #wlfilter { width:340px; max-width:100%; }
  .wltip { font-size:11px; color:var(--ink3); }
  .simbar { display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom:8px; padding:12px 15px; border-radius:12px; background:linear-gradient(180deg,var(--elev),var(--elev2)); border:1px solid var(--line); }
  .simbar .st { font-family:var(--font-display); font-size:11px; text-transform:uppercase; letter-spacing:.1em; color:var(--ink2); }
  .simbar .sr { font-size:13px; color:var(--ink-soft); }
  .simbar .sr b { font-family:var(--font-display); color:var(--accent-ink); font-size:16px; }
  .simbar .sr .slash { color:var(--ink3); }
  .simdelta { font-weight:700; font-size:12.5px; }
  .simdelta.up { color:#4bbd83; } .simdelta.zero { color:var(--ink3); }
  .tierhdr { display:flex; justify-content:space-between; align-items:baseline; margin:18px 0 6px; gap:12px; flex-wrap:wrap; }
  .tierhdr h3 { margin:0; font-size:14px; font-weight:600; color:var(--ink); display:flex; align-items:center; gap:9px; }
  .tierdot { width:8px; height:8px; border-radius:50%; }
  .tierhdr .roll { color:var(--ink2); font-size:11.5px; font-family:var(--font-mono); }
  .wltable { background:linear-gradient(180deg,var(--elev),var(--elev2)); border:1px solid var(--line); border-radius:12px; overflow:hidden; }
  table.wt { width:100%; border-collapse:collapse; font-size:13px; }
  table.wt th { text-align:left; padding:8px 12px; border-bottom:1px solid var(--line2); font-weight:600; font-size:10.5px; text-transform:uppercase; letter-spacing:.08em; cursor:pointer; user-select:none; white-space:nowrap; color:var(--ink2); }
  table.wt th.num, table.wt td.num { text-align:right; }
  table.wt th.on { color:var(--accent-ink); }
  table.wt td { padding:8px 12px; border-bottom:1px solid var(--hair); color:var(--ink-soft); }
  table.wt td.re { text-align:right; font-variant-numeric:tabular-nums; color:var(--accent-ink); }
  table.wt td.tg { color:var(--ink2b); }
  table.wt td.sg { color:var(--ink2); font-size:12px; }
  .wlname { cursor:pointer; border-bottom:1px dotted var(--line2); }

  /* roster triage (preserved) */
  .auditsummary { display:flex; gap:8px; flex-wrap:wrap; margin:2px 0 12px; }
  .auditsummary .chip { font-size:12px; color:var(--ink2); border:1px solid var(--line2); border-radius:999px; padding:3px 10px; }
  .auditsummary .chip b { color:var(--ink); }
  table.at { width:100%; border-collapse:collapse; font-size:13px; }
  table.at th { text-align:left; padding:7px 10px; border-bottom:1px solid var(--line2); font-weight:600; font-size:10.5px; text-transform:uppercase; letter-spacing:.06em; cursor:pointer; user-select:none; color:var(--ink2); white-space:nowrap; }
  table.at th.num, table.at td.num { text-align:right; }
  table.at th.on { color:var(--accent-ink); }
  table.at td { padding:7px 10px; border-bottom:1px solid var(--hair); color:var(--ink-soft); }
  table.at tbody tr.clk { cursor:pointer; }
  table.at tbody tr.clk:hover td { background:var(--accent-bg); }
  a.goto { color:var(--accent); cursor:pointer; }
  .vpill { font-size:11px; font-weight:700; padding:2px 9px; border-radius:999px; white-space:nowrap; text-transform:uppercase; letter-spacing:.03em; }
  .v-tune { background:rgba(236,110,90,.16); color:#dd6a4d; } .v-craft { background:rgba(214,150,40,.16); color:#c68b18; }
  .v-review { background:var(--accent-bg); color:var(--accent-ink); } .v-ok { background:rgba(58,204,138,.14); color:#4bbd83; }
  .tierpill { font-size:11px; font-weight:800; padding:2px 8px; border-radius:6px; min-width:20px; display:inline-block; text-align:center; }
  .t-s { background:rgba(143,123,242,.28); color:var(--accent-ink); } .t-a { background:rgba(58,204,138,.2); color:#4bbd83; }
  .t-b { background:rgba(214,150,40,.2); color:#c68b18; } .t-c { background:rgba(236,110,90,.16); color:#dd6a4d; }
  .t-d { background:var(--line2); color:var(--ink2); }
  .cell-flag { color:var(--bad); font-weight:600; } .cell-ok { color:var(--ink3); } .cell-muted { color:var(--ink3); }
  .why { color:var(--ink2); font-size:11.5px; }
  .auditnote { color:var(--ink2); font-size:12px; margin:10px 0 0; line-height:1.5; }

  /* card finder + stale (preserved) */
  .cardfind-row { border-top:1px solid var(--hair); padding:9px 2px; }
  .cardfind-row:first-child { border-top:none; }
  .cardfind-name { font-weight:600; font-size:14px; color:var(--ink-bright); }
  .cardfind-count { font-weight:400; font-size:12px; color:var(--ink2); margin-left:6px; }
  .cardfind-decks { margin-top:6px; display:flex; flex-wrap:wrap; gap:6px; }
  .deckchip { font-size:12px; padding:3px 9px; border:1px solid var(--line2); border-radius:12px; cursor:pointer; background:var(--fill2); color:var(--ink); }
  .deckchip:hover { border-color:var(--accent); color:var(--accent-ink); }
  .deckchip b { font-variant-numeric:tabular-nums; }
  .staletext { width:100%; min-height:120px; padding:10px 12px; border:1px solid var(--line2); border-radius:9px; background:var(--fill2); color:var(--ink); font-family:var(--font-mono); font-size:12.5px; resize:vertical; }
  .staleactions { margin:10px 0 4px; display:flex; gap:8px; }
  .stalecard { border:1px solid var(--line); border-radius:10px; padding:10px 14px; margin:10px 0; background:linear-gradient(180deg,var(--elev),var(--elev2)); }
  .stalecard h4 { margin:0 0 4px; font-size:14px; color:var(--ink-bright); }
  .stalecard .sub2 { font-size:12px; color:var(--ink2); margin-bottom:6px; }
  .stale-sync { color:#4bbd83; font-weight:600; } .stale-drift { color:#c68b18; font-weight:600; } .stale-nomatch { color:#dd6a4d; font-weight:600; }
  .difflist { font-family:var(--font-mono); font-size:12px; margin:6px 0 0; }
  .diffadd { color:#4bbd83; } .diffrem { color:#dd6a4d; }
  .staletot { font-size:13px; margin:2px 0 10px; }

  /* viz stats/mana (preserved, restyled) */
  .viz { display:flex; flex-direction:column; gap:15px; }
  .vizsec h4 { margin:0 0 7px; font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--ink2); }
  .hbar { display:grid; grid-template-columns:96px 1fr auto; align-items:center; gap:8px; margin:3px 0; font-size:12.5px; }
  .hbar .lbl { color:var(--ink); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .hbar .track { background:var(--fill2); border:1px solid var(--line2); border-radius:5px; height:14px; overflow:hidden; }
  .hbar .fill { height:100%; background:var(--accent); border-radius:4px; min-width:2px; }
  .hbar .val { font-variant-numeric:tabular-nums; color:var(--ink2); min-width:1.6em; text-align:right; }
  .curve { display:flex; align-items:flex-end; gap:6px; height:92px; }
  .curvecol { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100%; gap:4px; }
  .curvebar { width:100%; max-width:34px; background:linear-gradient(180deg,#9a86ff,#6a57e0); border-radius:4px 4px 0 0; min-height:2px; }
  .curvecol .cn, .curvecol .cx { font-size:11px; color:var(--ink2); font-variant-numeric:tabular-nums; }
  .fill.W,.pipfill.W{background:var(--W)} .fill.U,.pipfill.U{background:var(--U)} .fill.B,.pipfill.B{background:var(--B)}
  .fill.R,.pipfill.R{background:var(--R)} .fill.G,.pipfill.G{background:var(--G)} .fill.C,.pipfill.C{background:var(--Cc)}
  .flags { display:flex; flex-wrap:wrap; gap:6px; }
  .flag { font-size:11.5px; border:1px solid var(--line2); border-radius:6px; padding:2px 7px; background:var(--fill2); }
  .castlist { font-size:12px; margin:4px 0 0; padding-left:18px; color:var(--ink); }
  .metaline2 { font-size:12px; color:var(--ink2); margin-top:5px; }

  /* palette / modal / preview / toast */
  .overlay { position:fixed; inset:0; z-index:60; background:rgba(6,8,11,.6); backdrop-filter:blur(4px); -webkit-backdrop-filter:blur(4px); display:flex; align-items:flex-start; justify-content:center; }
  .palette { width:min(560px,94vw); background:linear-gradient(180deg,var(--panel),var(--panel2)); border:1px solid var(--accent-line); border-radius:14px; box-shadow:0 30px 80px -20px rgba(0,0,0,.6),0 0 44px -14px var(--accent-line); overflow:hidden; }
  .palette .pin { display:flex; align-items:center; gap:10px; padding:14px 16px; border-bottom:1px solid var(--line); color:var(--ink3); }
  .palette input { flex:1; background:transparent; border:none; outline:none; color:var(--ink); font-size:15px; font-family:inherit; }
  .palette .body { max-height:52vh; overflow-y:auto; padding:6px; }
  .pitem { display:flex; align-items:center; justify-content:space-between; gap:10px; padding:10px 12px; border-radius:9px; cursor:pointer; }
  .pitem.sel { background:var(--accent-bg); }
  .pitem .pt { font-size:13.5px; color:var(--ink); font-weight:500; }
  .pitem .ps { font-size:11px; color:var(--ink2); }
  .pitem .tag { font-size:10px; font-weight:700; padding:2px 8px; border-radius:6px; background:var(--fill); color:var(--ink2); border:1px solid var(--line2); }
  .palette .foot { display:flex; gap:14px; padding:9px 16px; border-top:1px solid var(--line); font-size:10.5px; color:var(--ink3); font-family:var(--font-mono); }
  .modal { width:min(680px,96vw); background:linear-gradient(180deg,var(--panel),var(--panel2)); border:1px solid var(--accent-line); border-radius:16px; box-shadow:0 40px 100px -24px rgba(0,0,0,.7),0 0 50px -16px var(--accent-line); overflow:hidden; margin-bottom:16px; }
  .modal .mhead { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; padding:18px 20px 14px; border-bottom:1px solid var(--line); }
  .modal h3 { margin:0; font-size:19px; font-weight:600; color:var(--ink-bright); }
  .modal h3 .id { color:var(--ink3); font-weight:500; font-size:14px; }
  .modal .mx { cursor:pointer; font-size:18px; color:var(--ink3); line-height:1; padding:2px 4px; }
  .modal .mbody { padding:16px 20px 20px; }
  .preview { position:fixed; width:224px; height:312px; border-radius:14px; box-shadow:0 22px 60px -12px rgba(0,0,0,.7),0 0 0 1px var(--accent-line); z-index:80; pointer-events:none; background:#0b0e13; overflow:hidden; animation:previewIn .12s ease both; }
  .preview img { width:100%; height:100%; object-fit:cover; }
  .preview .spin { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; }
  .preview .spin i { width:26px; height:26px; border-radius:50%; border:3px solid rgba(255,255,255,.15); border-top-color:#9a86ff; animation:spin .8s linear infinite; display:block; }
  .preview .err { position:absolute; inset:0; display:flex; flex-direction:column; gap:6px; align-items:center; justify-content:center; color:#8b93a1; font-size:12px; text-align:center; padding:0 16px; }
  .preview .cap { position:absolute; left:0; right:0; bottom:0; padding:14px 10px 8px; font-size:11px; font-weight:600; color:#fff; text-align:center; background:linear-gradient(0deg,rgba(0,0,0,.82),transparent); text-shadow:0 1px 3px rgba(0,0,0,.8); }
  .toast { position:fixed; left:50%; bottom:28px; transform:translateX(-50%) translateY(16px); background:var(--panel); color:var(--ink); border:1px solid var(--accent-line); box-shadow:0 0 26px -6px var(--accent-line); padding:10px 18px; border-radius:10px; font-size:13px; opacity:0; pointer-events:none; transition:opacity .2s,transform .2s; z-index:70; }
  .toast.show { opacity:1; transform:translateX(-50%) translateY(0); }
  .foot { color:var(--ink3); font-size:11.5px; margin-top:18px; border-top:1px solid var(--line); padding-top:14px; line-height:1.55; }
  .foot code { font-family:var(--font-mono); color:var(--ink2b); }
</style>
</head>
<body>
<div class="aura"><b class="a1"></b><b class="a2"></b><b class="a3"></b></div>

<header>
  <div class="hwrap">
    <div>
      <div class="htitle"><span class="hdot"></span>
        <h1>MTG Arena <span class="dim">— Roster Dashboard</span></h1>
      </div>
      <div class="hsub" id="hsub"></div>
    </div>
    <div class="hactions">
      <button class="iconbtn" id="btnsync" title="Sync live from GitHub Pages">⟳</button>
      <button class="iconbtn" id="btnshare" title="Copy shareable link to this view">🔗</button>
      <button class="iconbtn" id="btntheme" title="Toggle light / dark">◐</button>
      <div class="kpi"><div class="n" id="kpiPrint">0</div><div class="lbl">printings</div></div>
      <div class="kpi"><div class="n" id="kpiDecks">0</div><div class="lbl">decks</div></div>
      <div class="kpi hot"><div class="n" id="kpiBuild">0</div><div class="lbl">buildable now</div></div>
    </div>
  </div>
</header>

<main>
  <section style="margin-bottom:20px">
    <div class="analytics">
      <div class="panel ring-card">
        <div class="ring" id="ring"><div class="hole"><span class="rn" id="ringLabel">0%</span><span class="rl">ready</span></div></div>
        <div>
          <div style="font-family:var(--font-display);font-size:14px;color:var(--ink);font-weight:600">Buildable now</div>
          <div style="font-size:12px;color:var(--ink2);margin-top:4px;max-width:168px;line-height:1.45" id="buildSummary"></div>
        </div>
      </div>
      <div class="panel needs-card">
        <div class="ptitle">Wildcards needed · whole roster</div>
        <div id="needbars"></div>
      </div>
    </div>
    <div class="distgrid">
      <div class="panel dist-card"><div class="ptitle">Color identity · decks per color</div><div class="cbars" id="colorDist"></div></div>
      <div class="panel dist-card"><div class="ptitle">Formats</div><div id="formatDist"></div></div>
      <div class="panel dist-card"><div class="ptitle">Mana curve · whole roster</div><div class="rcurve" id="rosterCurve"></div></div>
    </div>
  </section>

  <section id="sec-find">
    <h2 class="sec"><span class="tick"></span>Find a card — which decks run it</h2>
    <input class="filter" id="cardfind" style="width:340px;max-width:100%" placeholder="type a card name (incl. variants)…" autocomplete="off" spellcheck="false">
    <div id="cardfindout" style="margin-top:10px"></div>
  </section>

  <section id="sec-triage">
    <h2 class="sec"><span class="tick"></span>Roster triage — which decks need a tune</h2>
    <div class="auditsummary" id="auditsummary"></div>
    <div id="audit"></div>
    <p class="auditnote" id="auditnote"></p>
  </section>

  <section id="sec-stale">
    <h2 class="sec"><span class="tick"></span>Check for stale decks — paste your Arena export(s)</h2>
    <p class="auditnote" id="stalenote">Paste one deck's Arena export to see if it drifted from the stored list, or paste several <code>Deck</code> blocks at once for a roster staleness report. Each block is auto-matched to its closest stored deck (variants included) — Arena exports don't carry a deck name. Compared by card name + quantity; printings and basic-land art are treated as the same card (same rules as <code>deck.py verify</code>). Nothing is uploaded — the compare runs entirely in your browser.</p>
    <textarea id="staletext" class="staletext" placeholder="Deck&#10;1 Y'shtola Rhul (FIN) 86&#10;…"></textarea>
    <div class="staleactions"><button class="cta" id="stalego">Compare</button><button class="ghostbtn" id="staleclear">Clear</button></div>
    <div id="staleout"></div>
  </section>

  <section id="sec-decks">
    <h2 class="sec"><span class="tick"></span>Decks &amp; variants</h2>
    <div class="controls">
      <div class="ctl-left">
        <input class="filter" id="deckfilter" placeholder="filter by id, name, or colors…">
        <div class="colchips" id="colchips"></div>
      </div>
      <div class="viewbtns">
        <span class="viewbtn on" id="viewGrid">▦ Grid</span>
        <span class="viewbtn" id="viewCompact">≣ Compact</span>
      </div>
    </div>
    <div class="quickrow">
      <div class="pills" id="quickpills"></div>
      <span class="grow"></span>
      <span class="ghostbtn" id="copyall">⧉ Copy all imports</span>
    </div>
    <div id="impactbanner"></div>
    <div id="deckview"></div>
  </section>

  <section id="sec-leverage">
    <h2 class="sec"><span class="tick"></span>Crafting leverage — most-shared cards</h2>
    <div class="sechint">Cards that appear in the most decks' craft lists — one wildcard here advances several decks at once. Click a card to highlight the decks it touches.</div>
    <div id="leverage"></div>
  </section>

  <section id="sec-wishlist">
    <h2 class="sec"><span class="tick"></span>Wildcard priority — wishlist</h2>
    <div class="wltop">
      <input class="filter" id="wlfilter" placeholder="filter wishlist by card, target, or signal…">
      <span class="grow"></span>
      <span class="wltip">tip: click a card to see which decks it unlocks</span>
      <span class="ghostbtn" id="exportwl">⧉ Export wishlist</span>
    </div>
    <div class="simbar">
      <span class="st">Payoff simulator</span>
      <div class="pills" id="simchips" style="display:flex;gap:6px;flex-wrap:wrap"></div>
      <span class="grow"></span>
      <span class="sr">Projected buildable&nbsp; <b id="simBuild">0</b><span class="slash">/<span id="simTotal">0</span></span> <span class="simdelta zero" id="simDelta"></span></span>
    </div>
    <div id="wishlist"></div>
  </section>

  <section id="sec-plan">
    <h2 class="sec"><span class="tick"></span>Craft plan — whole roster</h2>
    <pre class="code" id="plan" style="padding:16px 18px;font-size:12.5px;line-height:1.6"></pre>
  </section>

  <div class="foot" id="foot"></div>
</main>

<div id="overlays"></div>
<div id="preview"></div>
<div id="toast" class="toast"></div>

<script id="data" type="application/json">__DATA__</script>
<script>
"use strict";
// A live sync stashes the fresher payload in sessionStorage and reloads; prefer it
// over the embedded snapshot so the fresher data survives the reload (and a new
// tab/session falls back to the committed embedded data).
const _live = (function(){ try { return sessionStorage.getItem('mtga-live'); } catch(e){ return null; } })();
const D = JSON.parse(_live || document.getElementById('data').textContent);
const esc = s => (s==null?'':''+s).replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
const WC = {Mythic:'M',Rare:'R',Uncommon:'U',Common:'C'};
const RANK = {Mythic:3,Rare:2,Uncommon:1,Common:0};
const rankOf = r => (r in RANK ? RANK[r] : -1);
const COLBG = {W:'#efe4bf',U:'#5aa9ec',B:'#b9a6d6',R:'#ec7a63',G:'#6cc684',C:'#b9c0cc'};
const COLFG = {W:'#2a2618',U:'#06263d',B:'#241833',R:'#350e08',G:'#06280f',C:'#1c2129'};
const LIVE_URL = 'https://robinchoudhuryums.github.io/mtga/';   // Pages serves the dashboard AS index.html
const STALE_DAYS = 7;
const $ = id => document.getElementById(id);
const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
const preOf = txt => { const p = el('pre','code'); p.textContent = txt; return p; };
const scryUrl = name => 'https://scryfall.com/search?q=' + encodeURIComponent('!"' + (name||'').split('//')[0].trim() + '"');

// ---------- prefs + deep-link ----------
const STATE = { theme:'dark', viewMode:'grid', quickFilter:'all', activeColors:{}, open:{}, pinned:{},
  deckFilter:'', wlFilter:'', simMode:'off', impactCard:'', modalDeck:'', paletteOpen:false, paletteQuery:'', paletteIndex:0, gPrefix:false };
function parseHash(){
  const raw = (location.hash||'').replace(/^#/,''); if (!raw) return {};
  if (raw.startsWith('deck-')) return {d:raw.slice(5)};
  const o = {}; raw.split('&').forEach(kv => { const [k,v] = kv.split('='); if (k) o[k] = decodeURIComponent(v||''); }); return o;
}
function restorePrefs(){
  let p = {}; try { p = JSON.parse(localStorage.getItem('mtga-prefs')||'{}')||{}; } catch(e){}
  STATE.theme = p.theme || 'dark'; STATE.viewMode = p.viewMode || 'grid'; STATE.quickFilter = p.quickFilter || 'all';
  STATE.activeColors = p.activeColors || {}; STATE.open = p.open || {}; STATE.pinned = p.pinned || {};
  const h = parseHash();
  if (h.v) STATE.viewMode = h.v;
  if (h.f) STATE.quickFilter = h.f;
  if (h.q != null) STATE.deckFilter = h.q;
  if (h.c != null) { STATE.activeColors = {}; [...h.c].forEach(c => { if ('WUBRG'.includes(c)) STATE.activeColors[c] = true; }); }
  if (h.d) { h.d.split(',').forEach(id => { if (id) STATE.open[id] = true; }); STATE._jump = h.d.split(',')[0]; }
  document.documentElement.setAttribute('data-theme', STATE.theme);
}
function buildHash(){
  const p = [];
  if (STATE.viewMode !== 'grid') p.push('v=' + STATE.viewMode);
  if (STATE.quickFilter !== 'all') p.push('f=' + STATE.quickFilter);
  if (STATE.deckFilter) p.push('q=' + encodeURIComponent(STATE.deckFilter));
  const cols = ['W','U','B','R','G'].filter(c => STATE.activeColors[c]).join('');
  if (cols) p.push('c=' + cols);
  const open = Object.keys(STATE.open).filter(k => STATE.open[k]);
  if (open.length) p.push('d=' + open.join(','));
  return p.length ? '#' + p.join('&') : ' ';
}
function persist(){
  try { history.replaceState(null,'',buildHash()); } catch(e){}
  try { localStorage.setItem('mtga-prefs', JSON.stringify({theme:STATE.theme, viewMode:STATE.viewMode, quickFilter:STATE.quickFilter, activeColors:STATE.activeColors, open:STATE.open, pinned:STATE.pinned})); } catch(e){}
}
// Restore prefs + deep-link BEFORE anything renders, so control highlights (color
// chips, quick pills, view toggle) and the deck/wishlist views all reflect saved state.
restorePrefs();
document.documentElement.setAttribute('data-theme', STATE.theme);

// ---------- toast + clipboard ----------
const toastEl = $('toast'); let toastT;
function toast(msg){ toastEl.textContent = msg; toastEl.classList.add('show'); clearTimeout(toastT); toastT = setTimeout(() => toastEl.classList.remove('show'), 1700); }
function writeClip(text, done){
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done).catch(() => fallbackCopy(text, done));
  else fallbackCopy(text, done);
}
function fallbackCopy(text, done){
  const ta = el('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
  document.body.appendChild(ta); ta.select();
  try { document.execCommand('copy'); done(); } catch(e){ toast('Copy failed'); }
  document.body.removeChild(ta);
}

// ---------- derived per-deck ----------
function colorCount(colors){ return [...(colors||'')].filter(c => 'WUBRG'.includes(c)).length; }
function pieFor(colors){
  const cols = [...(colors||'')].filter(c => 'WUBRG'.includes(c));
  if (!cols.length) return 'conic-gradient(#b9c0cc 0% 100%)';
  if (cols.length === 1) return 'conic-gradient(' + COLBG[cols[0]] + ' 0% 100%)';
  const seg = 100/cols.length; let acc = 0; const stops = [];
  cols.forEach(c => { stops.push(COLBG[c] + ' ' + acc + '% ' + (acc+seg) + '%'); acc += seg; });
  return 'conic-gradient(' + stops.join(',') + ')';
}
// Mini curve from the STRUCTURED viz.curve (MV 1..6+), not text-parsed.
function miniCurve(viz){
  if (!viz || !viz.curve) return null;
  const b = [0,0,0,0,0,0];
  for (let mv = 0; mv <= 7; mv++){ const n = viz.curve[String(mv)] || 0; const i = Math.min(6, Math.max(1, mv)) - 1; b[i] += n; }
  if (!b.some(x => x)) return null;
  const max = Math.max(...b, 1); const labels = ['1','2','3','4','5','6+'];
  return b.map((c,i) => ({mv:labels[i], count:c, h:Math.round(c/max*100) + '%', title:'MV ' + labels[i] + ' · ' + c + ' cards'}));
}
D.decks.forEach(d => { d._cc = colorCount(d.colors); d._pie = pieFor(d.colors); d._curve = miniCurve(d.viz); });

// ---------- header + KPIs ----------
$('hsub').innerHTML = 'Read-only snapshot · generated ' + esc(D.generated) +
  ' · numbers match <code>deck.py</code> · <span class="link" id="palettehint">press <span class="kbd">⌘K</span> to search</span>';
const t = D.totals;
$('kpiPrint').textContent = t.printings;
$('kpiDecks').textContent = t.decks;
$('kpiBuild').innerHTML = t.buildable + '<small>/' + t.decks + '</small>';
$('simTotal').textContent = t.decks;
(function(){
  const pct = t.decks ? Math.round(100 * t.buildable / t.decks) : 0;
  $('ring').style.background = 'conic-gradient(var(--accent) ' + pct + '%, var(--line2) 0)';
  $('ringLabel').textContent = pct + '%';
  $('buildSummary').textContent = t.buildable + ' of ' + t.decks + ' decks are fully owned and ready to play right now.';
})();
$('plan').textContent = D.roster_plan || '(no craft plan)';

// ---------- analytics: needs / color / format / roster curve ----------
(function(){
  const N = {M:0,R:0,U:0,C:0};
  D.decks.forEach(d => { const re = /(\d+)\s*([MRUC])/g; let m; while ((m = re.exec(d.wc||''))) N[m[2]] += +m[1]; });
  const order = [['M','Mythic'],['R','Rare'],['U','Uncommon'],['C','Common']];
  const max = Math.max(1, ...order.map(o => N[o[0]]));
  const grad = {M:'linear-gradient(90deg,#f4a03a,#ffca6d)', R:'linear-gradient(90deg,#caa63a,#e6c866)', U:'linear-gradient(90deg,#7f8ba0,#9aa4b2)', C:'linear-gradient(90deg,#6b7480,#8a94a2)'};
  const wrap = $('needbars');
  order.forEach(([k,lab]) => {
    const row = el('div','needbar');
    row.innerHTML = '<span class="nl">' + lab + '</span><div class="nt"><div class="nf" style="width:' + Math.round(100*N[k]/max) + '%;background:' + grad[k] + '"></div></div><span class="nc">' + N[k] + '</span>';
    wrap.appendChild(row);
  });
})();
(function(){
  const counts = {W:0,U:0,B:0,R:0,G:0};
  D.decks.forEach(d => [...(d.colors||'')].forEach(c => { if (c in counts) counts[c]++; }));
  const max = Math.max(1, ...Object.values(counts));
  const wrap = $('colorDist');
  ['W','U','B','R','G'].forEach(c => {
    const col = el('div','cbar');
    col.innerHTML = '<span class="cn">' + counts[c] + '</span>'
      + '<div class="cf" style="height:' + Math.round(100*counts[c]/max) + '%;background:' + COLBG[c] + ';box-shadow:0 0 12px -3px ' + COLBG[c] + '"></div>'
      + '<span class="cp" style="background:' + COLBG[c] + ';color:' + COLFG[c] + '">' + c + '</span>';
    wrap.appendChild(col);
  });
})();
(function(){
  const fmt = {};
  D.decks.forEach(d => { const f = (d.format||'—').trim() || '—'; fmt[f] = (fmt[f]||0) + 1; });
  const rows = Object.entries(fmt).sort((a,b) => b[1]-a[1]);
  const max = Math.max(1, ...rows.map(r => r[1]));
  const wrap = $('formatDist');
  rows.forEach(([label,n]) => {
    const row = el('div','fbar');
    row.innerHTML = '<span class="fl">' + esc(label) + '</span><div class="ft"><div class="ff" style="width:' + Math.round(100*n/max) + '%"></div></div><span class="fc">' + n + '</span>';
    wrap.appendChild(row);
  });
})();
(function(){
  const b = [0,0,0,0,0,0];
  D.decks.forEach(d => { if (!d.viz || !d.viz.curve) return; for (let mv = 0; mv <= 7; mv++){ const n = d.viz.curve[String(mv)] || 0; const i = Math.min(6, Math.max(1, mv)) - 1; b[i] += n; } });
  const max = Math.max(1, ...b); const labels = ['1','2','3','4','5','6+']; const wrap = $('rosterCurve');
  b.forEach((c,i) => {
    const col = el('div','rcol');
    col.innerHTML = '<span class="rn2">' + c + '</span><div class="rf" title="MV ' + labels[i] + ' · ' + c + ' cards" style="height:' + Math.round(100*c/max) + '%"></div><span class="rm">' + labels[i] + '</span>';
    wrap.appendChild(col);
  });
})();

// ---------- Scryfall hover preview (non-blocking) ----------
const imgCache = {};
const previewBox = $('preview');
let previewOn = false;
function cardDeckCount(name){ return D.decks.filter(d => (d.craft||[]).some(c => c.name === name)).length; }
function showPreview(name, x, y){
  const front = (name||'').split('//')[0].trim(); if (!front) return;
  previewOn = true;
  const src = 'https://api.scryfall.com/cards/named?fuzzy=' + encodeURIComponent(front) + '&format=image&version=normal';
  const n = cardDeckCount(name);
  const cap = n ? name + ' · in ' + n + ' deck' + (n===1?'':'s') : name;
  previewBox.className = 'preview'; previewBox.style.display = 'block';
  previewBox.innerHTML = '<div class="spin"><i></i></div><div class="cap">' + esc(cap) + '</div>';
  positionPreview(x, y);
  const img = new Image();
  img.onload = () => { if (!previewOn) return; imgCache[src] = 'ok'; previewBox.innerHTML = ''; previewBox.appendChild(img); const cp = el('div','cap'); cp.textContent = cap; previewBox.appendChild(cp); };
  img.onerror = () => { if (!previewOn) return; imgCache[src] = 'err'; previewBox.innerHTML = '<div class="err"><span style="font-size:20px">🂠</span>No card image found</div><div class="cap">' + esc(cap) + '</div>'; };
  img.src = src; img.alt = 'card preview';
}
function positionPreview(x, y){
  const w = 224, h = 312, pad = 18;
  let left = x + pad; if (left + w > window.innerWidth - 8) left = x - w - pad;
  let top = Math.max(8, Math.min(y - h/2, window.innerHeight - h - 8));
  previewBox.style.left = left + 'px'; previewBox.style.top = top + 'px';
}
function hidePreview(){ previewOn = false; previewBox.style.display = 'none'; previewBox.innerHTML = ''; }
function attachHover(node, name){
  node.addEventListener('mouseenter', e => showPreview(name, e.clientX, e.clientY));
  node.addEventListener('mousemove', e => { if (previewOn) positionPreview(e.clientX, e.clientY); });
  node.addEventListener('mouseleave', hidePreview);
}

// ---------- generic sortable table ----------
function sortableTable(cls, cols, rows, sortState, onRowExtra){
  const tbl = el('table', cls);
  const thead = el('thead'), htr = el('tr');
  cols.forEach(c => {
    const th = el('th', (c.num?'num':'') + (sortState.key===c.key?' on':''), '');
    th.textContent = c.label + (sortState.key===c.key ? (sortState.dir>0?' ▲':' ▼') : '');
    th.onclick = () => { if (sortState.key===c.key) sortState.dir = -sortState.dir; else { sortState.key = c.key; sortState.dir = c.num?-1:1; } redraw(); };
    htr.appendChild(th);
  });
  thead.appendChild(htr); tbl.appendChild(thead);
  const tb = el('tbody'); tbl.appendChild(tb);
  function redraw(){
    let rs = rows.slice();
    if (sortState.key){ const {key,dir} = sortState; rs.sort((a,b) => { const va=a[key], vb=b[key]; const cmp = (typeof va==='number'&&typeof vb==='number') ? va-vb : (''+va).localeCompare(''+vb); return cmp*dir; }); }
    tb.innerHTML = '';
    rs.forEach(r => {
      const tr = el('tr');
      cols.forEach(c => { const td = el('td', (c.num?'num ':'') + (c.cls||'')); if (c.node) td.appendChild(c.node(r)); else if (c.html) td.innerHTML = c.html(r); else td.textContent = c.get(r); tr.appendChild(td); });
      if (onRowExtra) onRowExtra(tr, r);
      tb.appendChild(tr);
    });
    // rebuild header arrows
    [...htr.children].forEach((th,i) => { const c = cols[i]; th.className = (c.num?'num':'') + (sortState.key===c.key?' on':''); th.textContent = c.label + (sortState.key===c.key ? (sortState.dir>0?' ▲':' ▼') : ''); });
  }
  redraw();
  return tbl;
}
function wcPill(rarity){ const s = el('span','wcp ' + rarity); s.textContent = WC[rarity]||'?'; return s; }
function craftNameCell(r){
  const td = el('span');
  const nm = el('span','hovname', r.name); attachHover(nm, r.name); td.appendChild(nm);
  td.appendChild(document.createTextNode(' '));
  const a = el('a','scry','↗'); a.href = scryUrl(r.name); a.target = '_blank'; a.rel = 'noopener'; a.title = 'Open on Scryfall'; td.appendChild(a);
  return td;
}

// ---------- viz stats/mana (fed by deck.viz — same numbers as the CLI) ----------
function bar(label, value, max, cls){ const pct = max>0 ? Math.round(100*value/max) : 0; return '<div class="hbar"><span class="lbl">' + esc(label) + '</span><span class="track"><span class="fill ' + (cls||'') + '" style="width:' + pct + '%"></span></span><span class="val">' + value + '</span></div>'; }
function vizSection(title, inner){ return '<div class="vizsec"><h4>' + esc(title) + '</h4>' + inner + '</div>'; }
function renderStats(v){
  let html = ''; const cur = v.curve, cmax = Math.max(1, ...Object.values(cur).map(Number)); let cols = '';
  for (let b = 0; b < 8; b++){ const n = cur[String(b)] || 0; cols += '<div class="curvecol"><span class="cn">' + (n||'') + '</span><div class="curvebar" style="height:' + (n?Math.max(Math.round(100*n/cmax),3):0) + '%" title="MV ' + (b===7?'7+':b) + ': ' + n + '"></div><span class="cx">' + (b===7?'7+':b) + '</span></div>'; }
  html += vizSection('Mana curve' + (v.curve_unknown ? ' · ' + v.curve_unknown + ' unknown' : ''), '<div class="curve">' + cols + '</div>');
  const tmax = Math.max(1, ...v.types.map(x => x.n));
  html += vizSection('Types', v.types.map(x => bar(x.t, x.n, tmax)).join(''));
  const ck = Object.keys(v.colors), clmax = Math.max(1, ...ck.map(c => v.colors[c]));
  if (ck.length) html += vizSection('Color identity', ck.map(c => bar(c, v.colors[c], clmax, c)).join(''));
  if (v.roles.length){ const rmax = Math.max(1, ...v.roles.map(r => r.n)); html += vizSection('Functional roles', v.roles.map(r => bar(r.label, r.n, rmax)).join('') + '<div class="metaline2">interaction total: <b>' + v.interaction + '</b> (removal + sweeper + counter)</div>'); }
  if (v.cheaper.length || v.gated.length){ const chips = v.cheaper.map(x => '<span class="flag" title="' + esc(x.why) + '">◊ ' + esc(x.name) + '</span>').join('') + v.gated.map(x => '<span class="flag" title="' + esc(x.why) + '">△ ' + esc(x.name) + '</span>').join(''); html += vizSection('Cost flags — ◊ cheaper than MV · △ added cost', '<div class="flags">' + chips + '</div>'); }
  const wrap = el('div','viz'); wrap.innerHTML = html; return wrap;
}
function renderMana(v){
  const m = v.mana; let html = '';
  if (m.strict.length){ const smax = Math.max(1, ...m.strict.map(x => x.pips)); html += vizSection('Strict color requirements (pips that MUST be paid with that color)', m.strict.map(x => '<div class="hbar"><span class="lbl">' + x.c + '</span><span class="track"><span class="fill pipfill ' + x.c + '" style="width:' + Math.round(100*x.pips/smax) + '%"></span></span><span class="val">' + x.pips + ' · ' + x.cards + 'c</span></div>').join('')); }
  else html += vizSection('Strict color requirements', '<div class="metaline2">No strict single-color pips.</div>');
  if (m.hybrids.length) html += vizSection('Hybrid pips (payable with either color)', '<div class="flags">' + m.hybrids.map(h => '<span class="flag"><b>' + esc(h.colors) + '</b> ×' + h.n + '</span>').join('') + '</div>');
  let cast;
  if (!m.declared) cast = '<div class="metaline2">No declared colors — castability lint off.</div>';
  else if (!m.uncastable.length && !m.off_ident.length) cast = '<span class="badge b-ok">every nonland card fits ' + esc(m.declared) + ' ✓</span>';
  else { cast = ''; if (m.uncastable.length) cast += '<div class="metaline2"><span class="badge b-missing">' + m.uncastable.length + ' uncastable off ' + esc(m.declared) + '</span></div><ul class="castlist">' + m.uncastable.map(x => '<li>' + esc(x.name) + ' — ' + esc(x.why) + '</li>').join('') + '</ul>'; if (m.off_ident.length) cast += '<div class="metaline2"><span class="badge b-short">' + m.off_ident.length + ' stray outside ' + esc(m.declared) + '</span></div><ul class="castlist">' + m.off_ident.map(x => '<li>' + esc(x.name) + ' — ' + esc(x.why) + '</li>').join('') + '</ul>'; }
  html += vizSection('Castability', cast);
  const notes = []; if (m.hybrid_only) notes.push(m.hybrid_only + ' hybrid-only card(s)'); if (m.unknown) notes.push(m.unknown + ' card(s) with no cost data');
  if (notes.length) html += '<div class="metaline2">' + notes.join(' · ') + '</div>';
  const wrap = el('div','viz'); wrap.innerHTML = html; return wrap;
}

// ---------- deck filtering ----------
const TABS = [['craft','Craft picks'],['arena','Arena import'],['stats','Stats'],['mana','Mana'],['cuts','Cuts'],['legal','Legal']];
const QUICK = [['all','All'],['buildable','Buildable now'],['needsMythic','Needs mythic'],['incomplete','Needs work']];
function filteredDecks(){
  const q = (STATE.deckFilter||'').toLowerCase().trim();
  const cols = Object.keys(STATE.activeColors).filter(c => STATE.activeColors[c]);
  let list = D.decks.filter(d => {
    if (q && !((d.id+' '+d.name+' '+d.colors+' '+d.format+' '+d.archetype).toLowerCase().includes(q))) return false;
    if (cols.length && !cols.every(c => (d.colors||'').includes(c))) return false;
    if (STATE.quickFilter === 'buildable' && !d.buildable) return false;
    if (STATE.quickFilter === 'incomplete' && d.buildable) return false;
    if (STATE.quickFilter === 'needsMythic' && !/\dM/.test(d.wc||'')) return false;
    return true;
  });
  list.sort((a,b) => (STATE.pinned[b.id]?1:0) - (STATE.pinned[a.id]?1:0));
  return list;
}
const craftSort = {}, compactSort = {key:null,dir:1};
function craftTable(d){
  const cols = [
    {key:'name', label:'Card', node:craftNameCell},
    {key:'_rank', label:'WC', num:true, node:r => wcPill(r.rarity)},
    {key:'decks', label:'reuse', num:true, cls:'re', get:r => r.decks},
    {key:'matchesStr', label:'matches', cls:'mt', get:r => r.matchesStr},
  ];
  const rows = (d.craft||[]).map(r => ({...r, _rank:rankOf(r.rarity), matchesStr:(r.matches||[]).join(', ')}));
  if (!(d.id in craftSort)) craftSort[d.id] = {key:null,dir:1};
  return sortableTable('dt', cols, rows, craftSort[d.id]);
}
function detailBody(d, k){
  if (k === 'craft'){ if (!(d.craft||[]).length) return preOf('No craft picks — nothing on-color and on-theme to craft here.'); return craftTable(d); }
  if (k === 'stats') return renderStats(d.viz);
  if (k === 'mana') return renderMana(d.viz);
  return preOf((d.detail && d.detail[k]) || '(no output)');
}
function deckBadges(d){
  const wrap = el('div','badges');
  if (d.buildable){ wrap.appendChild(el('span','badge b-ok','buildable ✓')); }
  else { if (d.missing) wrap.appendChild(el('span','badge b-missing', d.missing + ' missing')); if (d.short) wrap.appendChild(el('span','badge b-short', d.short + ' short')); }
  return wrap;
}
function pipsRow(colors){
  const s = el('span','pips');
  [...(colors||'')].filter(c => 'WUBRGC'.includes(c)).forEach(c => s.appendChild(el('span','pip ' + c, c)));
  return s;
}
function deckCard(d){
  const card = el('div','deck' + (STATE.impactCard && (d.craft||[]).some(c => c.name === STATE.impactCard) ? ' impacted' : ''));
  card.id = 'deck-' + d.id;
  const top = el('div','dtop');
  const h = el('h3');
  const pin = el('span','pin' + (STATE.pinned[d.id]?' on':''), STATE.pinned[d.id]?'★':'☆'); pin.title = 'Pin to top';
  pin.onclick = () => { STATE.pinned[d.id] = !STATE.pinned[d.id]; persist(); renderDecks(); };
  h.appendChild(pin); h.appendChild(document.createTextNode(d.name + ' ')); const ids = el('span','id','#' + d.id); h.appendChild(ids);
  top.appendChild(h); top.appendChild(deckBadges(d)); card.appendChild(top);
  card.appendChild(el('div','arch', d.archetype));
  const meta = el('div','metaline');
  if (d.variant) meta.appendChild(el('span','vtag','variant of #' + d.core));
  if (d.format) { const f = el('span',null,d.format); f.style.color = 'var(--ink2b)'; meta.appendChild(f); }
  meta.appendChild(pipsRow(d.colors));
  meta.appendChild(el('span',null,d.total + ' cards'));
  card.appendChild(meta);
  // mini row: pie + curve
  const mini = el('div','minirow');
  const pieWrap = el('div','minipie-wrap');
  const pie = el('div','minipie'); pie.style.background = d._pie; const hole = el('div','hole', d._cc + 'c'); pie.appendChild(hole);
  pieWrap.appendChild(pie); pieWrap.appendChild(el('span','minicap','colors')); mini.appendChild(pieWrap);
  if (d._curve){
    const mc = el('div','minicurve'); const bars = el('div','bars'); const lbls = el('div','lbls');
    d._curve.forEach(cv => { const i = el('i'); i.style.height = cv.h; i.title = cv.title; bars.appendChild(i); const l = el('i',null,cv.mv); lbls.appendChild(l); });
    mc.appendChild(bars); mc.appendChild(lbls); mini.appendChild(mc);
  } else mini.appendChild(el('div','curvena','curve n/a'));
  card.appendChild(mini);
  // wc line
  if (d.buildable){ const w = el('div'); w.style.marginTop = '11px'; w.appendChild(el('span','badge b-ok','no wildcards needed')); card.appendChild(w); }
  else { const w = el('div','wcline'); w.innerHTML = 'to finish&nbsp; <b>' + esc(d.wc||'—') + '</b>'; card.appendChild(w); }
  // actions
  const drow = el('div','drow');
  const copy = el('button','cta','⧉ Copy Arena import'); copy.onclick = () => writeClip((d.detail&&d.detail.arena)||'', () => toast('#' + d.id + ' ' + d.name + ' import copied'));
  drow.appendChild(copy);
  const exp = el('span','expand', STATE.open[d.id] ? '▾ analysis' : '▸ analysis');
  exp.onclick = () => { STATE.open[d.id] = !STATE.open[d.id]; persist(); renderDecks(); };
  drow.appendChild(exp);
  drow.appendChild(el('span','grow'));
  const mod = el('span','iconlink','⤢'); mod.title = 'Open detail'; mod.onclick = () => openModal(d.id); drow.appendChild(mod);
  const prn = el('span','iconlink','🖨'); prn.title = 'Print craft plan'; prn.onclick = () => printDeck(d); drow.appendChild(prn);
  card.appendChild(drow);
  // detail
  if (STATE.open[d.id]){
    const det = el('div','detail'); const tabs = el('div','tabs');
    const curTab = (STATE._tab && STATE._tab[d.id]) || 'craft';
    const body = el('div');
    TABS.forEach(([k,label]) => { const tb = el('span','tab' + (k===curTab?' on':''), label); tb.onclick = () => { STATE._tab = STATE._tab||{}; STATE._tab[d.id] = k; body.innerHTML=''; body.appendChild(detailBody(d,k)); [...tabs.children].forEach(x => x.classList.remove('on')); tb.classList.add('on'); }; tabs.appendChild(tb); });
    det.appendChild(tabs); body.appendChild(detailBody(d, curTab)); det.appendChild(body); card.appendChild(det);
  }
  return card;
}
function compactTable(list){
  const wrap = el('div','compact');
  const cols = [
    {key:'name', label:'Deck', html:d => esc(d.name) + ' <span class="id">#' + esc(d.id) + '</span>'},
    {key:'colors', label:'Colors', node:d => pipsRow(d.colors)},
    {key:'format', label:'Format', get:d => d.format||'—'},
    {key:'total', label:'Cards', num:true, get:d => d.total},
    {key:'_status', label:'Status', num:true, node:d => deckBadges(d)},
    {key:'wc', label:'To finish', cls:'wc', get:d => d.buildable ? '—' : (d.wc||'—')},
    {key:'_copy', label:'', node:d => { const b = el('button','miniimport','⧉'); b.title = 'Copy Arena import'; b.onclick = () => writeClip((d.detail&&d.detail.arena)||'', () => toast('#' + d.id + ' import copied')); return b; }},
  ];
  const rows = list.map(d => ({...d, _status:(d.buildable?3:0)-(d.missing||0)-(d.short||0)}));
  wrap.appendChild(sortableTable('ct', cols, rows, compactSort));
  return wrap;
}
function renderDecks(){
  const list = filteredDecks();
  const host = $('deckview'); host.innerHTML = '';
  // impact banner
  const ib = $('impactbanner'); ib.innerHTML = '';
  if (STATE.impactCard){
    const n = D.decks.filter(d => (d.craft||[]).some(c => c.name === STATE.impactCard)).length;
    const bn = el('div','impactbanner');
    bn.innerHTML = 'Crafting <strong class="c">' + esc(STATE.impactCard) + '</strong> advances <strong>' + n + '</strong> deck' + (n===1?'':'s') + ' — highlighted below.';
    bn.appendChild(el('span','grow'));
    const x = el('span','x','clear ✕'); x.onclick = () => { STATE.impactCard = ''; renderDecks(); }; bn.appendChild(x);
    ib.appendChild(bn);
  }
  $('copyall').textContent = '⧉ Copy all imports (' + list.length + ')';
  if (!list.length){ host.appendChild(el('div','emptymsg','No decks match the current filters.')); return; }
  if (STATE.viewMode === 'grid'){ const g = el('div','grid'); list.forEach(d => g.appendChild(deckCard(d))); host.appendChild(g); }
  else host.appendChild(compactTable(list));
}
// controls wiring
$('deckfilter').value = STATE.deckFilter;
$('deckfilter').addEventListener('input', e => { STATE.deckFilter = e.target.value; persist(); renderDecks(); });
(function(){
  const wrap = $('colchips');
  ['W','U','B','R','G'].forEach(c => {
    const chip = el('span','colchip', c); chip.title = c;
    const paint = () => { const on = !!STATE.activeColors[c]; chip.style.background = on?COLBG[c]:'var(--fill)'; chip.style.color = on?COLFG[c]:'var(--ink2)'; chip.style.borderColor = on?COLBG[c]:'var(--line2)'; chip.style.boxShadow = on?('0 0 12px -2px '+COLBG[c]):'none'; };
    chip.onclick = () => { STATE.activeColors[c] = !STATE.activeColors[c]; persist(); paint(); renderDecks(); };
    paint(); wrap.appendChild(chip);
  });
})();
(function(){
  const wrap = $('quickpills');
  QUICK.forEach(([k,label]) => { const p = el('span','pill' + (STATE.quickFilter===k?' on':''), label); p.onclick = () => { STATE.quickFilter = k; persist(); [...wrap.children].forEach(x => x.classList.remove('on')); p.classList.add('on'); renderDecks(); }; wrap.appendChild(p); });
})();
$('viewGrid').classList.toggle('on', STATE.viewMode==='grid');
$('viewCompact').classList.toggle('on', STATE.viewMode==='compact');
$('viewGrid').onclick = () => { STATE.viewMode = 'grid'; persist(); $('viewGrid').classList.add('on'); $('viewCompact').classList.remove('on'); renderDecks(); };
$('viewCompact').onclick = () => { STATE.viewMode = 'compact'; persist(); $('viewCompact').classList.add('on'); $('viewGrid').classList.remove('on'); renderDecks(); };
$('copyall').onclick = () => { const list = filteredDecks(); const text = list.map(d => '// #' + d.id + ' ' + d.name + '\n' + ((d.detail&&d.detail.arena)||'')).join('\n\n'); writeClip(text, () => toast(list.length + ' deck imports copied')); };
renderDecks();

// ---------- leverage ----------
(function(){
  const map = {};
  D.decks.forEach(d => (d.craft||[]).forEach(c => { if (!map[c.name]) map[c.name] = {name:c.name, rarity:c.rarity, decks:[]}; map[c.name].decks.push(d.name); }));
  const list = Object.values(map).filter(x => x.decks.length >= 2).sort((a,b) => b.decks.length - a.decks.length || (RANK[b.rarity]||0) - (RANK[a.rarity]||0) || a.name.localeCompare(b.name));
  const host = $('leverage');
  if (!list.length){ host.appendChild(el('div','emptymsg','No cards are shared across multiple decks yet.')); return; }
  const g = el('div','levgrid');
  list.forEach(lv => {
    const card = el('div','lev' + (STATE.impactCard===lv.name?' on':''));
    const cnt = el('div','cnt', lv.decks.length); card.appendChild(cnt);
    const body = el('div','body');
    const nmrow = el('div'); nmrow.style.display='flex'; nmrow.style.alignItems='center'; nmrow.style.gap='6px';
    const nm = el('span','nm', lv.name); attachHover(nm, lv.name); nmrow.appendChild(nm);
    nmrow.appendChild(wcPill(lv.rarity));
    const a = el('a','scry','↗'); a.href = scryUrl(lv.name); a.target='_blank'; a.rel='noopener'; nmrow.appendChild(a);
    body.appendChild(nmrow);
    body.appendChild(el('div','ds', lv.decks.join(', ')));
    card.appendChild(body);
    card.onclick = e => { if (e.target.tagName === 'A') return; STATE.impactCard = STATE.impactCard===lv.name ? '' : lv.name; renderDecks(); [...g.children].forEach(x => x.classList.remove('on')); if (STATE.impactCard) card.classList.add('on'); const s = $('sec-decks'); if (s) window.scrollTo({top:s.getBoundingClientRect().top + window.scrollY - 82, behavior:'smooth'}); };
    g.appendChild(card);
  });
  host.appendChild(g);
})();

// ---------- wishlist + simulator ----------
const wlSort = {};
const WL_LABELS = {A:'Tier A — craft first', B:'Tier B — targeted upgrade', C:'Tier C — situational'};
const TIERDOT = {A:'#f4a03a', B:'var(--accent)', C:'#7d8595'};
function rollStr(o){ return ['Mythic','Rare','Uncommon','Common'].filter(k => o && o[k]).map(k => o[k] + ' ' + k).join(' · '); }
const anyWl = ['A','B','C'].some(k => (D.wishlist[k]||[]).length);
function renderWishlist(){
  const host = $('wishlist'); host.innerHTML = '';
  if (!anyWl){ $('sec-wishlist').style.display = 'none'; return; }
  const q = (STATE.wlFilter||'').toLowerCase().trim();
  ['A','B','C'].forEach(tier => {
    let rows = (D.wishlist[tier]||[]).map(r => ({...r, _rank:rankOf(r.rarity), priNum:(typeof r.pri==='number'?r.pri:parseFloat(r.pri)||0), target:(r.target||'').toString(), sig:r.sig||''}));
    if (q) rows = rows.filter(r => (r.name+' '+r.target+' '+r.sig).toLowerCase().includes(q));
    if (!rows.length) return;
    const hdr = el('div','tierhdr');
    hdr.innerHTML = '<h3><span class="tierdot" style="background:' + TIERDOT[tier] + ';box-shadow:0 0 8px ' + TIERDOT[tier] + '"></span>' + WL_LABELS[tier] + '</h3><span class="roll">' + rows.length + ' cards · ' + esc(rollStr(D.wishlist_rollup[tier])) + '</span>';
    host.appendChild(hdr);
    const cols = [
      {key:'name', label:'Card', node:r => { const s = el('span'); const nm = el('span','wlname', r.name); nm.onclick = () => { STATE.impactCard = STATE.impactCard===r.name ? '' : r.name; renderDecks(); const sec = $('sec-decks'); if (sec) window.scrollTo({top:sec.getBoundingClientRect().top + window.scrollY - 82, behavior:'smooth'}); }; attachHover(nm, r.name); s.appendChild(nm); s.appendChild(document.createTextNode(' ')); const a = el('a','scry','↗'); a.href = scryUrl(r.name); a.target='_blank'; a.rel='noopener'; s.appendChild(a); return s; }},
      {key:'_rank', label:'WC', num:true, node:r => wcPill(r.rarity)},
      {key:'target', label:'Target', cls:'tg', get:r => r.target},
      {key:'reuse', label:'reuse', num:true, cls:'re', get:r => r.reuse},
      {key:'priNum', label:'pri', num:true, get:r => (typeof r.pri==='number'?r.pri.toFixed(2):r.pri)},
      {key:'sig', label:'signal', cls:'sg', get:r => r.sig},
    ];
    if (!(tier in wlSort)) wlSort[tier] = {key:null,dir:1};
    const box = el('div','wltable'); box.appendChild(sortableTable('wt', cols, rows, wlSort[tier])); host.appendChild(box);
  });
}
$('wlfilter').addEventListener('input', e => { STATE.wlFilter = e.target.value; renderWishlist(); });
$('exportwl').onclick = () => { const lines = ['MTGA WILDCARD WISHLIST']; ['A','B','C'].forEach(k => { const rows = D.wishlist[k]||[]; if (!rows.length) return; lines.push('', WL_LABELS[k]); rows.forEach(r => lines.push('  [' + (WC[r.rarity]||'?') + '] ' + r.name + ' — ' + (r.target||'') + ' (pri ' + (typeof r.pri==='number'?r.pri.toFixed(2):r.pri) + ')')); }); writeClip(lines.join('\n'), () => toast('Wishlist copied to clipboard')); };
// simulator
const SIM = [['off','Off'],['A','+ Tier A'],['AB','+ Tier A & B'],['all','+ All tiers']];
function craftedSet(mode){ const set = new Set(); const tiers = mode==='A'?['A']:mode==='AB'?['A','B']:mode==='all'?['A','B','C']:[]; tiers.forEach(k => (D.wishlist[k]||[]).forEach(r => set.add(r.name))); return set; }
function projectedBuildable(mode){ if (mode==='off') return D.totals.buildable; const set = craftedSet(mode); return D.decks.filter(d => d.buildable || ((d.craft||[]).length > 0 && d.craft.every(c => set.has(c.name)))).length; }
function renderSim(){
  const b = projectedBuildable(STATE.simMode); $('simBuild').textContent = b;
  const delta = b - D.totals.buildable; const de = $('simDelta');
  de.textContent = delta > 0 ? '▲ +' + delta : (delta === 0 ? '±0' : '' + delta);
  de.className = 'simdelta ' + (delta > 0 ? 'up' : 'zero');
}
(function(){ const wrap = $('simchips'); SIM.forEach(([k,label]) => { const c = el('span','simchip' + (STATE.simMode===k?' on':''), label); c.onclick = () => { STATE.simMode = k; [...wrap.children].forEach(x => x.classList.remove('on')); c.classList.add('on'); renderSim(); }; wrap.appendChild(c); }); })();
renderWishlist(); renderSim();

// ---------- roster triage (preserved) ----------
(function(){
  const SEV = {TUNE:0, craft:1, review:2, ok:3};
  const VLAB = {TUNE:'★ tune', craft:'craft', review:'review', ok:'ok'};
  const VCLS = {TUNE:'v-tune', craft:'v-craft', review:'v-review', ok:'v-ok'};
  const TCLS = {S:'t-s', A:'t-a', B:'t-b', C:'t-c', D:'t-d'};
  const rows = D.decks.map(d => { const a = d.audit; const cast = (!a.uncast && !a.stray) ? '✓' : [a.uncast?a.uncast+'u':'', a.stray?a.stray+'s':''].filter(Boolean).join(' ');
    return { id:d.id, name:d.name, deck:'#'+d.id+' '+d.name, sz:a.sz, tier:a.tier||'', _tierord:({S:0,A:1,B:2,C:3,D:4})[a.tier] ?? 5, short:a.short, illegal:a.illegal, uncast:a.uncast, stray:a.stray, cast, _castsev:a.uncast*100+a.stray, int:a.int, thm:a.thm, verdict:a.verdict, why:a.why, _sev:SEV[a.verdict] }; });
  rows.sort((x,y) => x._sev - y._sev || (''+x.id).length - (''+y.id).length || (''+x.id).localeCompare(''+y.id));
  const flag = (n, sfx) => n ? '<span class="cell-flag">' + n + sfx + '</span>' : '<span class="cell-ok">✓</span>';
  const cols = [
    {key:'deck', label:'Deck', html:r => '<a class="goto" data-goto="' + esc(r.name) + '">' + esc(r.deck) + '</a>'},
    {key:'_tierord', label:'Tier', num:true, html:r => r.tier ? '<span class="tierpill ' + TCLS[r.tier] + '">' + r.tier + '</span>' : '<span class="cell-muted">·</span>'},
    {key:'sz', label:'Sz', num:true, get:r => r.sz},
    {key:'short', label:'Own', num:true, html:r => flag(r.short,'✗')},
    {key:'illegal', label:'Legal', num:true, html:r => flag(r.illegal,'✗')},
    {key:'_castsev', label:'Cast', num:true, html:r => (r.uncast||r.stray) ? '<span class="cell-flag">' + esc(r.cast) + '</span>' : '<span class="cell-ok">✓</span>'},
    {key:'int', label:'Int', num:true, get:r => r.int},
    {key:'thm', label:'Thm', num:true, get:r => r.thm},
    {key:'_sev', label:'Verdict', num:true, html:r => '<span class="vpill ' + VCLS[r.verdict] + '">' + VLAB[r.verdict] + '</span>' + (r.why ? ' <span class="why">' + esc(r.why) + '</span>' : '')},
  ];
  const sort = {key:null,dir:1};
  const tbl = sortableTable('at', cols, rows, sort, (tr) => tr.classList.add('clk'));
  $('audit').appendChild(tbl);
  const c = {TUNE:0,craft:0,review:0,ok:0}; rows.forEach(r => c[r.verdict]++);
  $('auditsummary').innerHTML = '<span class="chip"><b>' + c.TUNE + '</b> to tune</span><span class="chip"><b>' + c.craft + '</b> to craft</span><span class="chip"><b>' + c.review + '</b> to review</span><span class="chip"><b>' + c.ok + '</b> ok</span>';
  $('auditnote').textContent = 'Offline triage — same numbers as deck.py audit. Tier = competitive grade (S→D, · = ungraded) from each deck’s #: tier: header; click the Tier header to sort. Own/Legal/Cast ✓ = clean; Cast Nu = uncastable, Ns = off-identity stray. ★ tune = a hard problem; craft = unbuilt; review = a soft flag. Click a deck to filter the list below.';
  $('audit').addEventListener('click', e => { const a = e.target.closest('[data-goto]'); if (!a) return; STATE.deckFilter = a.dataset.goto; $('deckfilter').value = a.dataset.goto; persist(); renderDecks(); $('sec-decks').scrollIntoView({behavior:'smooth', block:'start'}); });
})();

// ---------- card finder (preserved) ----------
(function(){
  const idx = new Map();
  for (const d of D.decks){ for (const nl in (d.cards||{})){ const [disp, qty] = d.cards[nl]; let e = idx.get(nl); if (!e){ e = {disp, decks:[]}; idx.set(nl, e); } e.decks.push({id:d.id, name:d.name, qty}); } }
  const entries = [...idx.values()].sort((a,b) => a.disp.localeCompare(b.disp));
  const out = $('cardfindout'), inp = $('cardfind');
  function draw(q){
    q = (q||'').trim().toLowerCase();
    if (!q){ out.innerHTML = '<p class="auditnote">Searches ' + entries.length + ' distinct cards across every deck and variant. Click a deck to jump to it.</p>'; return; }
    if (q.length < 2){ out.innerHTML = ''; return; }
    const hits = entries.filter(e => e.disp.toLowerCase().includes(q)).slice(0, 50);
    if (!hits.length){ out.innerHTML = '<p class="auditnote">No card matching “' + esc(q) + '” in any deck.</p>'; return; }
    out.innerHTML = hits.map(e => { const decks = e.decks.slice().sort((a,b) => (''+a.id).localeCompare(''+b.id, undefined, {numeric:true})); const chips = decks.map(d => '<span class="deckchip" data-id="' + esc(d.id) + '"><b>' + esc(d.id) + '</b>' + (d.qty>1?' ×'+d.qty:'') + ' · ' + esc(d.name||d.id) + '</span>').join(''); return '<div class="cardfind-row"><div class="cardfind-name">' + esc(e.disp) + '<span class="cardfind-count">in ' + decks.length + ' deck' + (decks.length>1?'s':'') + '</span></div><div class="cardfind-decks">' + chips + '</div></div>'; }).join('');
    out.querySelectorAll('.deckchip').forEach(ch => ch.addEventListener('click', () => { STATE.deckFilter = ch.dataset.id; $('deckfilter').value = ch.dataset.id; persist(); renderDecks(); $('sec-decks').scrollIntoView({behavior:'smooth', block:'start'}); }));
  }
  draw(''); inp.addEventListener('input', e => draw(e.target.value));
})();

// ---------- stale-deck compare (preserved) ----------
(function(){
  const SECTION = /^(sideboard|commander|companion|maybeboard)\b/i;
  function parseLine(raw){ const line = raw.trim(); if (!line) return null; const m = line.match(/^(\d+)\s+(.+?)(?:\s+\(([^)]+)\)(?:\s+\S+)?)?$/); if (!m) return null; const name = m[2].trim(); if (!name) return null; return {nl:name.toLowerCase(), disp:name, qty:parseInt(m[1],10)}; }
  function splitDecks(text){ const segs = []; let cur = null, started = false; for (const ln of text.split(/\r?\n/)){ const t = ln.trim(); if (/^deck\s*$/i.test(t)){ cur = []; segs.push(cur); started = true; continue; } if (SECTION.test(t)) continue; if (!started){ cur = []; segs.push(cur); started = true; } cur.push(ln); } return segs.filter(s => s.length); }
  function multiset(lines){ const m = {}; for (const ln of lines){ const p = parseLine(ln); if (!p) continue; if (m[p.nl]) m[p.nl][1] += p.qty; else m[p.nl] = [p.disp, p.qty]; } return m; }
  function diffSets(pasted, stored){ const names = new Set([...Object.keys(pasted), ...Object.keys(stored)]); let added = 0, removed = 0; const diffs = []; for (const nl of names){ const p = pasted[nl]?pasted[nl][1]:0, s = stored[nl]?stored[nl][1]:0; const disp = (pasted[nl]&&pasted[nl][0]) || (stored[nl]&&stored[nl][0]) || nl; if (p > s){ added += p-s; diffs.push({sign:'+', qty:p-s, name:disp}); } else if (s > p){ removed += s-p; diffs.push({sign:'-', qty:s-p, name:disp}); } } diffs.sort((a,b) => a.sign===b.sign ? a.name.localeCompare(b.name) : (a.sign==='-'?-1:1)); return {added, removed, diffs}; }
  function bestMatch(pasted){ let best = null, second = null; for (const d of D.decks){ const r = diffSets(pasted, d.cards||{}); const drift = r.added + r.removed; const shared = Object.keys(pasted).filter(nl => (d.cards||{})[nl]).length; const cand = {deck:d, drift, shared, ...r}; if (!best || drift < best.drift){ second = best; best = cand; } else if (!second || drift < second.drift){ second = cand; } } if (best) best.runnerUp = second; return best; }
  function analyzeOne(seg){ const pasted = multiset(seg); const nCards = Object.values(pasted).reduce((a,v) => a+v[1], 0); if (!nCards) return null; const uniq = Object.keys(pasted).length; const m = bestMatch(pasted); if (!m || m.shared < Math.max(3, uniq*0.3)) return {unmatched:true, nCards, uniq}; const ru = m.runnerUp; const lowconf = !!(ru && (ru.drift - m.drift) <= 2 && ru.shared >= m.shared*0.8); return {unmatched:false, deck:m.deck, sync:m.drift===0, added:m.added, removed:m.removed, diffs:m.diffs, shared:m.shared, nCards, lowconf, runnerUp:lowconf?ru.deck:null}; }
  function stalecardEl(r){ const box = el('div','stalecard'); if (r.unmatched){ box.innerHTML = '<h4>Unmatched paste <span class="stale-nomatch">no close deck</span></h4><div class="sub2">' + r.nCards + ' cards, ' + r.uniq + ' unique — doesn’t closely match any stored deck.</div>'; return box; } const d = r.deck; const status = r.sync ? '<span class="stale-sync">✓ in sync</span>' : '<span class="stale-drift">⟳ drifted — ' + r.added + ' added / ' + r.removed + ' removed</span>'; const conf = r.lowconf && r.runnerUp ? ' · <span class="stale-nomatch">⚠ low confidence — #' + esc(r.runnerUp.id) + ' ' + esc(r.runnerUp.name) + ' is nearly as close</span>' : ''; box.innerHTML = '<h4>#' + esc(d.id) + ' ' + esc(d.name) + ' ' + status + '</h4><div class="sub2">matched by ' + r.shared + ' shared cards' + (d.variant?' · variant':'') + (r.sync?'':' · update it in Arena or in the repo') + conf + '</div>'; if (!r.sync){ const dl = el('div','difflist'); dl.innerHTML = r.diffs.map(x => '<div class="' + (x.sign==='+'?'diffadd':'diffrem') + '">' + x.sign + x.qty + '  ' + esc(x.name) + '</div>').join(''); box.appendChild(dl); const note = el('div','metaline2', '+ = your Arena paste has more · − = the stored repo deck has more'); box.appendChild(note); } return box; }
  const out = $('staleout');
  $('stalego').addEventListener('click', () => { out.innerHTML = ''; const segs = splitDecks($('staletext').value); if (!segs.length){ out.innerHTML = '<div class="metaline2">Nothing to compare — paste an Arena export above.</div>'; return; } const results = segs.map(analyzeOne).filter(Boolean); if (!results.length){ out.innerHTML = '<div class="metaline2">No card lines found in the paste.</div>'; return; } if (results.length > 1){ const drifted = results.filter(r => !r.unmatched && !r.sync); const synced = results.filter(r => !r.unmatched && r.sync).length; const unm = results.filter(r => r.unmatched).length; const s = el('div','staletot'); s.innerHTML = '<b>' + results.length + '</b> decks checked · <span class="stale-sync">' + synced + ' in sync</span> · <span class="stale-drift">' + drifted.length + ' drifted</span>' + (unm?' · <span class="stale-nomatch">'+unm+' unmatched</span>':'') + (drifted.length?'<br>Update in Arena: ' + drifted.map(r => '#'+esc(r.deck.id)+' '+esc(r.deck.name)).join(', '):''); out.appendChild(s); } results.forEach(r => out.appendChild(stalecardEl(r))); });
  $('staleclear').addEventListener('click', () => { $('staletext').value = ''; out.innerHTML = ''; });
})();

// ---------- modal ----------
function modalDeckObj(id){ return D.decks.find(d => d.id === id); }
function openModal(id){ STATE.modalDeck = id; renderOverlays(); }
function closeModal(){ STATE.modalDeck = ''; renderOverlays(); }
function printDeck(d){
  const escp = t => (t||'').replace(/</g,'&lt;');
  const rows = (d.craft||[]).map(c => '<tr><td>' + escp(c.name) + '</td><td>' + c.rarity + '</td><td>' + (c.decks||0) + '</td><td>' + escp((c.matches||[]).join(', ')) + '</td></tr>').join('');
  const css = 'body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:#111;margin:32px;max-width:640px}h1{font-size:20px;margin:0 0 2px}.sub{color:#666;font-size:13px;margin-bottom:18px}table{width:100%;border-collapse:collapse;font-size:13px;margin:8px 0 22px}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #ddd}th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#666}pre{background:#f4f4f6;padding:12px;border-radius:8px;font-size:12px;white-space:pre-wrap}h2{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:#666;margin:20px 0 6px}';
  const table = rows ? '<table><thead><tr><th>Card</th><th>WC</th><th>reuse</th><th>matches</th></tr></thead><tbody>' + rows + '</tbody></table>' : '<p>No craft picks.</p>';
  const body = '<h1>' + escp(d.name) + ' <span style="color:#999">#' + d.id + '</span></h1><div class="sub">' + escp(d.format) + ' · ' + d.total + ' cards · to finish: ' + escp(d.wc) + '</div><h2>Craft picks</h2>' + table + '<h2>Arena import</h2><pre>' + escp((d.detail&&d.detail.arena)||'') + '</pre>';
  const auto = '<scr' + 'ipt>window.onload=function(){setTimeout(function(){window.print()},250)}</scr' + 'ipt>';
  const doc = '<!doctype html><html><head><meta charset="utf-8"><title>' + escp(d.name) + ' — craft plan</title><style>' + css + '</style></head><body>' + body + auto + '</body></html>';
  const w = window.open('', '_blank'); if (!w){ toast('Allow pop-ups to print'); return; }
  w.document.open(); w.document.write(doc); w.document.close();
}
function renderOverlays(){
  const host = $('overlays'); host.innerHTML = '';
  if (STATE.paletteOpen) host.appendChild(paletteEl());
  if (STATE.modalDeck){ const d = modalDeckObj(STATE.modalDeck); if (d) host.appendChild(modalEl(d)); }
}
function modalEl(d){
  const ov = el('div','overlay'); ov.style.zIndex = 65; ov.style.alignItems = 'flex-start'; ov.style.padding = '7vh 16px 16px'; ov.style.overflowY = 'auto';
  ov.onclick = closeModal;
  const m = el('div','modal'); m.onclick = e => e.stopPropagation();
  const head = el('div','mhead');
  const left = el('div');
  left.innerHTML = '<h3>' + esc(d.name) + ' <span class="id">#' + esc(d.id) + '</span></h3><div style="color:var(--ink2);font-size:12.5px;margin-top:5px;line-height:1.45;max-width:520px">' + esc(d.archetype) + '</div>';
  const meta = el('div','metaline'); meta.style.marginTop = '8px';
  if (d.format){ const f = el('span',null,d.format); f.style.color = 'var(--ink2b)'; meta.appendChild(f); }
  meta.appendChild(pipsRow(d.colors)); meta.appendChild(el('span',null,d.total + ' cards'));
  const bg = deckBadges(d); [...bg.children].forEach(c => meta.appendChild(c));
  left.appendChild(meta); head.appendChild(left);
  const x = el('span','mx','✕'); x.onclick = closeModal; head.appendChild(x); m.appendChild(head);
  const body = el('div','mbody');
  const tabs = el('div','tabs'); const cur = {k:(STATE._mtab||'craft')}; const bodyIn = el('div');
  const bar = el('div'); bar.style.display='flex'; bar.style.gap='6px'; bar.style.flexWrap='wrap'; bar.style.alignItems='center'; bar.style.marginBottom='12px';
  TABS.forEach(([k,label]) => { const tb = el('span','tab' + (k===cur.k?' on':''), label); tb.onclick = () => { STATE._mtab = k; cur.k = k; bodyIn.innerHTML=''; bodyIn.appendChild(detailBody(d,k)); [...tabs.children].forEach(z => z.classList.remove('on')); tb.classList.add('on'); }; tabs.appendChild(tb); });
  bar.appendChild(tabs); bar.appendChild(el('span','grow'));
  const imp = el('button','miniimport','⧉ Import'); imp.onclick = () => writeClip((d.detail&&d.detail.arena)||'', () => toast('#'+d.id+' import copied')); bar.appendChild(imp);
  const prn = el('button','ghostbtn','🖨 Print'); prn.onclick = () => printDeck(d); bar.appendChild(prn);
  body.appendChild(bar); bodyIn.appendChild(detailBody(d, cur.k)); body.appendChild(bodyIn); m.appendChild(body);
  ov.appendChild(m); return ov;
}

// ---------- command palette ----------
function paletteItems(){
  const q = (STATE.paletteQuery||'').toLowerCase().trim();
  const secs = [ {title:'Decks & variants', sub:'jump to section', tag:'§', act:() => jumpTo('sec-decks')},
    {title:'Wildcard priority', sub:'wishlist', tag:'§', act:() => jumpTo('sec-wishlist')},
    {title:'Craft plan', sub:'whole roster', tag:'§', act:() => jumpTo('sec-plan')},
    {title:'Crafting leverage', sub:'most-shared cards', tag:'§', act:() => jumpTo('sec-leverage')},
    {title:'Roster triage', sub:'which decks need a tune', tag:'§', act:() => jumpTo('sec-triage')} ];
  const decks = D.decks.map(d => ({title:d.name + '  #' + d.id, sub:(d.format?d.format+' · ':'') + (d.colors||'—') + ' · ' + (d.buildable?'buildable':(d.wc||'')), tag:'deck', act:() => { STATE.open[d.id] = true; persist(); renderDecks(); setTimeout(() => { const e2 = $('deck-'+d.id); if (e2) window.scrollTo({top:e2.getBoundingClientRect().top + window.scrollY - 82, behavior:'smooth'}); }, 40); }}));
  let items = secs.concat(decks);
  if (q) items = items.filter(it => (it.title + ' ' + it.sub).toLowerCase().includes(q));
  return items;
}
function openPalette(){ STATE.paletteOpen = true; STATE.paletteQuery = ''; STATE.paletteIndex = 0; renderOverlays(); setTimeout(() => { const i = document.querySelector('.palette input'); if (i) i.focus(); }, 20); }
function closePalette(){ STATE.paletteOpen = false; renderOverlays(); }
function paletteEl(){
  const ov = el('div','overlay'); ov.style.alignItems = 'flex-start'; ov.style.padding = '12vh 16px 16px'; ov.onclick = closePalette;
  const p = el('div','palette'); p.onclick = e => e.stopPropagation();
  const top = el('div','pin'); top.innerHTML = '<span style="color:var(--accent);font-size:15px">⌘</span>';
  const inp = el('input'); inp.value = STATE.paletteQuery; inp.placeholder = 'Jump to a deck or section…';
  inp.addEventListener('input', e => { STATE.paletteQuery = e.target.value; STATE.paletteIndex = 0; drawItems(); });
  top.appendChild(inp); top.appendChild(el('span','kbd','esc')); p.appendChild(top);
  const body = el('div','body'); p.appendChild(body);
  function drawItems(){
    const items = paletteItems(); body.innerHTML = '';
    if (!items.length){ body.appendChild(el('div',null,'No matches')).style.cssText = 'padding:18px;text-align:center;color:var(--ink2);font-size:13px'; return; }
    items.forEach((it,i) => { const row = el('div','pitem' + (i===STATE.paletteIndex?' sel':'')); row.innerHTML = '<div style="display:flex;flex-direction:column;gap:1px"><span class="pt">' + esc(it.title) + '</span><span class="ps">' + esc(it.sub) + '</span></div><span class="tag">' + it.tag + '</span>'; row.onmouseenter = () => { STATE.paletteIndex = i; [...body.children].forEach(z => z.classList.remove('sel')); row.classList.add('sel'); }; row.onclick = () => { closePalette(); it.act(); }; body.appendChild(row); });
  }
  drawItems(); p._draw = drawItems;
  const foot = el('div','foot'); foot.innerHTML = '<span>↑↓ navigate</span><span>⏎ open</span><span>esc close</span>'; p.appendChild(foot);
  ov.appendChild(p); return ov;
}

// ---------- header buttons + keyboard ----------
$('btntheme').onclick = () => { STATE.theme = STATE.theme==='dark'?'light':'dark'; document.documentElement.setAttribute('data-theme', STATE.theme); persist(); };
$('btnshare').onclick = () => { const url = location.href.split('#')[0] + buildHash().replace(/^ $/,''); writeClip(url, () => toast('View link copied to clipboard')); };
$('btnsync').onclick = () => syncLive(false);
$('palettehint').onclick = openPalette;
function jumpTo(id){ const e = $(id); if (e) window.scrollTo({top:e.getBoundingClientRect().top + window.scrollY - 82, behavior:'smooth'}); }
function isTyping(e){ const t = e.target; return t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable); }
window.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k'){ e.preventDefault(); openPalette(); return; }
  if (STATE.paletteOpen){
    const items = paletteItems();
    if (e.key === 'Escape'){ e.preventDefault(); closePalette(); }
    else if (e.key === 'ArrowDown'){ e.preventDefault(); STATE.paletteIndex = Math.min(items.length-1, STATE.paletteIndex+1); const p = document.querySelector('.palette'); if (p && p._draw) p._draw(); }
    else if (e.key === 'ArrowUp'){ e.preventDefault(); STATE.paletteIndex = Math.max(0, STATE.paletteIndex-1); const p = document.querySelector('.palette'); if (p && p._draw) p._draw(); }
    else if (e.key === 'Enter'){ e.preventDefault(); const it = items[STATE.paletteIndex]; if (it){ closePalette(); it.act(); } }
    return;
  }
  if (STATE.modalDeck && e.key === 'Escape'){ closeModal(); return; }
  if (isTyping(e) || e.metaKey || e.ctrlKey || e.altKey) return;
  if (STATE.gPrefix){ STATE.gPrefix = false; const map = {d:'sec-decks', w:'sec-wishlist', p:'sec-plan'}; if (map[e.key]){ e.preventDefault(); jumpTo(map[e.key]); return; } }
  if (e.key === 'g'){ e.preventDefault(); STATE.gPrefix = true; clearTimeout(window._gt); window._gt = setTimeout(() => STATE.gPrefix = false, 1200); return; }
  if (e.key === 't'){ e.preventDefault(); $('btntheme').click(); return; }
  if (e.key === '/'){ e.preventDefault(); $('deckfilter').focus(); return; }
  if (e.key === '?'){ e.preventDefault(); openPalette(); return; }
});

// ---------- live sync (fixed to Pages index.html) ----------
let syncing = false;
function syncLive(silent){
  if (syncing) return; syncing = true;
  if (!silent) toast('Syncing from GitHub Pages…');
  const re = new RegExp('<scr' + 'ipt id="data"[^>]*>([\\s\\S]*?)</scr' + 'ipt>');
  fetch(LIVE_URL, {cache:'no-store'}).then(r => r.text()).then(html => {
    const m = html.match(re); if (!m) throw new Error('no data block');
    const data = JSON.parse(m[1]);   // JSON.parse un-escapes the island's < automatically
    const fresh = Date.parse((data.generated||'').replace(' ','T'));
    const cur = Date.parse((D.generated||'').replace(' ','T'));
    if (!(fresh > cur)){ syncing = false; if (!silent) toast('Already up to date — ' + esc(D.generated)); return; }
    // Stash the fresher payload and reload; the top-of-script loader prefers it, so
    // every section cleanly re-derives from the new data without a manual re-render.
    try { sessionStorage.setItem('mtga-live', m[1]); } catch(e){}
    syncing = false; toast('Synced live — ' + (data.totals ? data.totals.decks : D.decks.length) + ' decks · reloading');
    setTimeout(() => location.reload(), 450);
  }).catch(e => { console.warn('live sync failed', e); syncing = false; if (!silent) toast('Live sync failed — showing last snapshot'); });
}
// Auto background-sync only when the snapshot is stale (>7 days).
(function(){ const ts = Date.parse((D.generated||'').replace(' ','T')); if (!isNaN(ts) && (Date.now() - ts) > STALE_DAYS*864e5){ const chip = document.createElement('span'); chip.className = 'stalechip'; chip.textContent = 'stale · sync ⟳'; chip.title = 'Snapshot is over a week old — click to sync'; chip.onclick = () => syncLive(false); $('hsub').appendChild(document.createTextNode(' · ')); $('hsub').appendChild(chip); } })();

$('foot').innerHTML = 'Live snapshot from committed data — hit ⟳ to re-sync from GitHub Pages, or regenerate with <code>python3 scripts/build_dashboard.py</code>. Card previews &amp; links via Scryfall. The judgment calls (craft X or Y, tuning) still live in the chat — this shows state, not decisions.';

// ---------- init ----------
// (Prefs were restored at the top, so every section above already rendered with saved
// state.) Deep-link: scroll to a linked deck once the grid is in the DOM.
if (STATE._jump){ setTimeout(() => { const e2 = $('deck-' + STATE._jump); if (e2) window.scrollTo({top:e2.getBoundingClientRect().top + window.scrollY - 82, behavior:'smooth'}); }, 150); }
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

    # Aggregate self-check (audit A6): per-deck analysis errors are tolerated — one
    # bad card must not fail the whole build (that's why _capture swallows them) — but
    # a WHOLESALE failure (analysis erroring for a majority of decks, i.e. a real
    # deck.py cmd_* regression) must NOT deploy as a green success. Mirror
    # build_gallery.py: the file is still written for inspection, but say so plainly
    # and exit non-zero so CI/Pages doesn't publish a page of "[analysis error]" panels.
    MARK = "[analysis error"
    err_decks = [d["id"] for d in payload["decks"]
                 if any(MARK in (d.get("detail", {}).get(k) or "")
                        for k in ("legal", "cuts", "arena"))]
    ndecks = len(payload["decks"])
    if ndecks and len(err_decks) * 2 >= ndecks:
        eprint(f"WARN:  deck analysis failed for {len(err_decks)}/{ndecks} decks "
               f"(e.g. {', '.join(err_decks[:6])}) — a deck.py command likely regressed. "
               f"The dashboard was written but is DEGRADED; refusing to report success.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
