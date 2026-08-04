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
from lib import REPO_ROOT, owned_qty  # noqa: E402

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
    fallback is shared rather than re-implemented (the A3/A4/F6 rule)."""
    idx = {}
    for r in rows:
        n = (r.get("Card Name") or "").strip().lower()
        if not n:
            continue
        q = (r.get("Quantity Owned") or "").strip()
        idx[n] = idx.get(n, 0) + (int(q) if q.isdigit() else 0)
    return idx


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
    nl = name.strip().lower()
    front = _front(name)
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
                if m and m.group(1).strip().lower() in (nl, front):
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
    text = lr.get("Card Text") or pr.get("Card Text") or "(no oracle text on file)"
    colors = lr.get("Color(s)") or pr.get("Color(s)") or ""
    syn = lr.get("Synergies") or pr.get("Synergies") or ""
    cost = (m.get("Mana Cost") or "").strip()
    mv = (m.get("Mana Value") or "").strip()
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
        std = "standard" in legal.lower()
        flag = "✓ STANDARD-LEGAL" if std else "✗ NOT Standard-legal"
        print(f"  legality: {flag}   [{legal}]")
    else:
        print("  legality: (unknown — not in pool; verify before crafting)")
    if kw:
        print(f"  keywords: {kw}")
    # Flag mechanics the synergy tagger doesn't index (a new set's keyword), so a
    # card is never evaluated with a hidden/mis-tagged mechanic.
    try:
        import check_keywords as ck
        unindexed = ck.unknown_for_card(kw)
        if unindexed:
            print(f"  ⚠ unindexed mechanic(s): {', '.join(unindexed)} "
                  "(not in the synergy map — grade its effect from the text above)")
    except Exception:
        pass

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
