#!/usr/bin/env python3
"""card.py — single-card inspector.

Prints the COMPLETE, untruncated oracle text of a card in one place, alongside
its mana cost, FORMAT LEGALITY, owned quantity, rarity/wildcard, and which decks
run it. It exists to prevent two recurring analysis mistakes:

  1. Grading a card from a truncated text slice (e.g. `query.py --full | head`
     hid Morningtide's Light's damage-prevention clause) — this NEVER truncates.
  2. Recommending a craft without checking legality (Champion of Rhonas / Chord
     of Calling are Historic-only, not Standard) — legality is printed up front.

Usage:
    python3 scripts/card.py "morningtide"            # substring / fuzzy match
    python3 scripts/card.py "Ghalta, Primal Hunger"  # exact
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (REPO_ROOT, front_face_cost, mana_value, owned_qty,  # noqa: E402
                 alias_front)

LIBRARY = os.path.join(REPO_ROOT, "card-library.csv")
POOL = os.path.join(REPO_ROOT, "card-pool.csv")
MANA = os.path.join(REPO_ROOT, "card-mana.csv")
DECKS = os.path.join(REPO_ROOT, "decks")


def _load(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _front(name):
    return name.split(" // ")[0].strip().lower()


def _distinct(rows):
    """Rows deduped by card NAME, first spelling kept. card-library.csv holds one row per
    PRINTING, so a card owned in three sets is three rows — counting those as three
    "cards match" over-reported the ambiguity it was warning about (audit F-14)."""
    out, seen = [], set()
    for r in rows:
        nl = (r.get("Card Name") or "").strip().lower()
        if nl and nl not in seen:
            seen.add(nl)
            out.append(r)
    return out


def _rank(query, rows):
    """Substring matches, genuinely CLOSEST first. The caller prints "showing the
    closest", but this used to return whatever came first in CSV order — so
    `card.py "bolt"` could lead with a card whose name merely contains the query deep
    inside it (audit F-14). Rank: a name that STARTS with the query, then a word-start
    match, then the shortest name (the least padded around the query), then
    alphabetical for stability. Mirrors how `deck.py resolve` / `suggest-homes`
    disambiguate."""
    q = query.strip().lower()

    def key(r):
        n = (r.get("Card Name") or "").strip().lower()
        return (0 if n.startswith(q) else 1 if re.search(rf"\b{re.escape(q)}", n) else 2,
                len(n), n)
    return sorted(rows, key=key)


def _exact(query, rows):
    """Rows whose name — or DFC FRONT face — equals the query, case-insensitive."""
    nl = query.strip().lower()
    return [r for r in rows if (r.get("Card Name") or "").strip().lower() == nl
            or _front(r.get("Card Name") or "") == nl]


def _find(query, rows):
    """(best_row, distinct_matches) WITHIN one source. An exact hit (case-insensitive,
    including a DFC front face) wins outright; otherwise substring matches are ranked
    closest-first and deduped by name, so both the pick and the "N cards match" count
    are honest. Cross-SOURCE resolution lives in `_resolve` — exactness must outrank
    source there, so don't chain two `_find`s with `or`."""
    exact = _exact(query, rows)
    if exact:
        return exact[0], _distinct(exact)
    subs = _rank(query, [r for r in rows
                         if query.strip().lower() in (r.get("Card Name") or "").lower()])
    return (subs[0] if subs else None), _distinct(subs)


def _resolve(query, lib, pool):
    """(best_row, distinct_matches, is_exact) across BOTH sources.

    EXACTNESS OUTRANKS SOURCE. The old shape — `lib_hit or pool_hit`, `lmatches or
    pmatches` — preferred the library unconditionally, so a library SUBSTRING match
    shadowed a pool card exactly named the query and dropped the pool's matches from
    the "Others" list entirely: `card.py "Mimic"` showed Gogo, Master of Mimicry and
    the pool card named "Mimic" appeared nowhere (broad-scan BS-02), on the surface
    G-01 mandates for pre-grading reads. Between two EXACT hits the library still
    wins, matching `load_card_data`'s library-first precedence; substring matches are
    ranked across the merged sources, library first on a same-name tie (stable sort)."""
    lex, pex = _exact(query, lib), _exact(query, pool)
    if lex or pex:
        return (lex or pex)[0], _distinct(lex + pex), True
    subs = _rank(query, [r for r in lib + pool
                         if query.strip().lower() in (r.get("Card Name") or "").lower()])
    return (subs[0] if subs else None), _distinct(subs), False


def _owned_index(rows):
    """{name_lower: total copies} SUMMED across every printing.

    card-library.csv holds one row per PRINTING, and Arena copies are fungible across
    sets — CLAUDE.md's "Owned copies are fungible across printings … never count a single
    printing in isolation". This file read `Quantity Owned` off the FIRST matching row, so
    it under-reported every card owned in more than one set: Rugged Highlands showed
    OWNED: 1 against a real 3, Lightning Strike 1 against 2. `card.py` is the surface G-01
    names as the default way to read a card before grading it, so the one number a craft
    decision leans on was the one that was wrong (broad-scan F-03).

    `deck.py` (`load_collection`), `pool.py` (`owned_counts`) and `wishlist.py` all build
    this same summed index; the lookup goes through `lib.owned_qty` so the DFC front-face
    fallback is shared rather than re-implemented (the A3/A4/F6 rule).

    Front-face aliased in a SECOND pass, like those three. `owned_qty` resolves the full
    `A // B` name DOWN to a front key — the direction the library's stated convention
    calls for — but eight rows are stored under the FULL name (the DSK Rooms and two
    DFCs), so a query by the FRONT name resolved to nothing and this surface reported
    OWNED: 0 for a card in the collection (broad-scan BS6-01). `alias_front` adds a
    front key only where no real row claims it, so a distinct card named `Front` is
    never shadowed (G-63)."""
    idx = {}
    for r in rows:
        n = (r.get("Card Name") or "").strip().lower()
        if not n:
            continue
        q = (r.get("Quantity Owned") or "").strip()
        idx[n] = idx.get(n, 0) + (int(q) if q.isdigit() else 0)
    return alias_front(idx)


def _owned_printings(rows, name):
    """`[(set, collector, qty)]` for every OWNED printing of `name`, so a multi-printing
    count shows its working instead of asserting a bare total. Front-face aware, matching
    `lib.owned_qty`'s resolution order."""
    nl = (name or "").strip().lower()
    front = nl.split(" // ")[0]
    out = []
    for r in rows:
        rn = (r.get("Card Name") or "").strip().lower()
        if rn != nl and rn != front:
            continue
        q = (r.get("Quantity Owned") or "").strip()
        if q.isdigit() and int(q) > 0:
            out.append(((r.get("Set Code") or "").strip(),
                        (r.get("Collector #") or "").strip(), int(q)))
    return out


def _decks_using(name):
    # Join on FRONT faces BOTH sides (the `_ms_key` convention, G-63): the resolved
    # name may be the library's front-only spelling while the deck file stores the
    # full `Front // Back` — an exact match against (nl, front) missed those lines,
    # so `card.py "Cecil, Dark Knight"` printed "in decks: (none)" for a card deck 42
    # runs, and "(none)" is the field that decides "safe to cut / homeless craft"
    # (broad-scan BS2-12; five cards across six deck files at the time).
    front = _front(name).lower()
    hits = []
    if not os.path.isdir(DECKS):
        return hits
    for root, _dirs, files in os.walk(DECKS):
        for fn in sorted(files):
            if not fn.endswith(".txt"):
                continue
            path = os.path.join(root, fn)
            for raw in open(path, encoding="utf-8"):
                line = raw.split("#", 1)[0].strip()
                m = re.match(r"^\d+\s*[xX]?\s+(.+?)\s*(?:\([^)]+\).*)?$", line)
                if m and _front(m.group(1)).lower() == front:
                    tag = (os.path.basename(root) if fn == "deck.txt"
                           else os.path.splitext(fn)[0])
                    hits.append(tag)
                    break
    return sorted(set(hits))


def main():
    if len(sys.argv) < 2:
        print('usage: card.py "<card name>"')
        return 2
    query = " ".join(sys.argv[1:])

    lib, pool = _load(LIBRARY), _load(POOL)
    mana = {(r.get("Card Name") or "").strip().lower(): r for r in _load(MANA)}

    best, matches, is_exact = _resolve(query, lib, pool)
    if best is None:
        print(f"No card matching {query!r} in library or pool.")
        return 1
    name = best.get("Card Name", "").strip()

    if not is_exact and len(matches) > 1:
        print(f"{len(matches)} cards match {query!r}; showing the closest. Others:")
        for r in matches[:12]:
            if (r.get("Card Name") or "").strip() != name:
                print(f"   - {r.get('Card Name')}")
        print()

    # Resolve every field from the best-named library row, then the pool row —
    # EXACT lookups only: `name` is already a resolved display name, and a substring
    # fallback here re-introduces the shadow `_resolve` exists to prevent (a library
    # row containing the name as a substring would supply the fields for a pool card).
    lr = (_exact(name, lib) or [{}])[0]
    pr = (_exact(name, pool) or [{}])[0]
    m = mana.get(name.lower()) or mana.get(_front(name)) or {}

    typ = lr.get("Type") or pr.get("Type") or ""
    # Blank text on a row that otherwise resolved (a real type line from the pool) is
    # almost always a GENUINE vanilla creature (K-11), not an enrichment failure — the
    # old "(no oracle text on file)" read as "go re-fetch" and sent a session to
    # Scryfall to learn Quakestrider Ceratops is a 12/8 with no abilities
    # (broad-implement #3). No row at all is still a data gap.
    text = lr.get("Card Text") or pr.get("Card Text")
    if not text:
        text = ("(no rules text — a vanilla creature (K-11), not a data gap)"
                if (pr.get("Type") or lr.get("Type"))
                else "(no oracle text on file — card not resolved; enrich/build the pool)")
    colors = lr.get("Color(s)") or pr.get("Color(s)") or ""
    syn = lr.get("Synergies") or pr.get("Synergies") or ""
    cost = (m.get("Mana Cost") or "").strip()
    mv = (m.get("Mana Value") or "").strip()
    # G-02 residual 2, closed. card-mana.csv stores Scryfall's Mana Value, which for a
    # split / Room / Adventure card is the COMBINED total of both halves — and you never
    # pay both. `deck.load_mana` recomputes it from the front face for exactly this
    # reason; this file read the column straight off the CSV, so Mirror Room // Fractured
    # Realm displayed MV 10 when it is a {2}{U} three-drop whose back door unlocks
    # separately. That put the inspection surface G-01 mandates for pre-grading reads in
    # direct contradiction with every analysis surface (stats, the curve, consistency),
    # which have all used the front face for a year (broad-scan BS5-08).
    split = " // " in cost
    if split:
        mv = str(mana_value(front_face_cost(cost)))
    kw = (m.get("Keywords") or "").strip()
    rarity = (pr.get("Rarity") or "").strip()
    legal = (pr.get("Legalities") or "").strip()
    setc = lr.get("Set Code") or pr.get("Set Code") or ""
    # SUMMED across printings, never one row's cell — see _owned_index (broad-scan F-03).
    owned = owned_qty(_owned_index(lib), name)
    printings = _owned_printings(lib, name)

    print(f"━━ {name} ━━")
    head = typ + (f"   ·   {cost}" if cost else "") + (f" (MV {mv})" if mv else "")
    print(head)
    if split:
        # Say WHICH half the number describes. The cost line shows both — that is the
        # printed card and the reader wants it — so an unqualified MV beside it invites
        # the same misreading in a human that the raw column caused in the code.
        print(f"  ↳ two castable halves; MV {mv} is the FRONT half "
              f"({front_face_cost(cost)}) — the one you pay to cast it. The other half "
              f"is paid separately, so never add them (G-02).")

    meta = [f"colors(identity): {colors or 'C'}"]
    if rarity:
        meta.append(f"rarity: {rarity} ({rarity[:1].upper()} wildcard)")
    # Show the working when the total comes from more than one printing — the case the
    # single-row read used to get wrong, so a reader can see WHY the number is what it is.
    if len(printings) > 1:
        where = ", ".join(f"{s or '—'}×{q}" for s, _c, q in printings)
        meta.append(f"OWNED: {owned}  [{len(printings)} printings: {where}]")
    else:
        meta.append(f"OWNED: {owned}" + (f"  [set {setc}]" if setc else ""))
    print("  " + " | ".join(meta))

    # LEGALITY — the guardrail, printed prominently and never guessed.
    if legal:
        # TOKEN, not substring (Batch G): every other legality read in the repo splits
        # on ";" into a set first (pool.py, deck.craft_rot_note, wishlist._rank_scores),
        # and Scryfall's key list includes `standardbrawl` — which CONTAINS "standard".
        # Safe today only because build_pool.POOL_FORMATS happens to omit it; adding it
        # would silently mark every Brawl-only card "✓ STANDARD-LEGAL". Same shape as
        # the `"r" in "colorless"` trap lib.color_matches exists to kill.
        std = "standard" in {x.strip().lower() for x in legal.split(";") if x.strip()}
        flag = "✓ STANDARD-LEGAL" if std else "✗ NOT Standard-legal"
        print(f"  legality: {flag}   [{legal}]")
    else:
        print("  legality: (unknown — not in pool; verify before crafting)")
    if kw:
        print(f"  keywords: {kw}")
    # Flag mechanics the synergy tagger doesn't index (a new set's keyword), so a
    # card is never evaluated with a hidden/mis-tagged mechanic. A crash in the
    # checker must SAY so on stderr — the bare `except: pass` silently turned the
    # K-01 warning off on the exact surface built to show it, and "no unindexed
    # mechanics" was indistinguishable from "the checker died" (batch 5).
    try:
        import check_keywords as ck
        unindexed = ck.unknown_for_card(kw)
        if unindexed:
            print(f"  ⚠ unindexed mechanic(s): {', '.join(unindexed)} "
                  "(not in the synergy map — grade its effect from the text above)")
    except Exception as e:
        print(f"  (unindexed-mechanic check unavailable: {type(e).__name__}: {e})",
              file=sys.stderr)

    # FULL oracle text — never truncated (this is the whole point).
    print("\n  Oracle text:")
    for ln in text.split("\n"):
        print(f"    {ln}")
    if syn:
        print(f"\n  synergy tags: {syn}")

    decks = _decks_using(name)
    print(f"\n  in decks: {', '.join(decks) if decks else '(none)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
