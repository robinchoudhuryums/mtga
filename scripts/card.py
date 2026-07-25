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
from lib import REPO_ROOT  # noqa: E402

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


def _find(query, rows):
    """(best_row, distinct_matches). An exact hit (case-insensitive, including a DFC
    front face) wins outright; otherwise substring matches are ranked closest-first and
    deduped by name, so both the pick and the "N cards match" count are honest."""
    nl = query.strip().lower()
    exact = [r for r in rows if (r.get("Card Name") or "").strip().lower() == nl
             or _front(r.get("Card Name") or "") == nl]
    if exact:
        return exact[0], _distinct(exact)
    subs = _rank(query, [r for r in rows if nl in (r.get("Card Name") or "").lower()])
    return (subs[0] if subs else None), _distinct(subs)


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

    lrow, lmatches = _find(query, lib)
    prow, pmatches = _find(query, pool)
    if lrow is None and prow is None:
        print(f"No card matching {query!r} in library or pool.")
        return 1
    name = (lrow or prow).get("Card Name", "").strip()

    matches = lmatches or pmatches
    is_exact = any((r.get("Card Name") or "").strip().lower() == query.strip().lower()
                   or _front(r.get("Card Name") or "") == query.strip().lower()
                   for r in matches)
    if not is_exact and len(matches) > 1:
        print(f"{len(matches)} cards match {query!r}; showing the closest. Others:")
        for r in matches[:12]:
            if (r.get("Card Name") or "").strip() != name:
                print(f"   - {r.get('Card Name')}")
        print()

    # Resolve every field from the best-named library row, then the pool row.
    lr = _find(name, lib)[0] or {}
    pr = _find(name, pool)[0] or {}
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
    qty = (lr.get("Quantity Owned") or "").strip()
    owned = int(qty) if qty.isdigit() else 0

    print(f"━━ {name} ━━")
    head = typ + (f"   ·   {cost}" if cost else "") + (f" (MV {mv})" if mv else "")
    print(head)

    meta = [f"colors(identity): {colors or 'C'}"]
    if rarity:
        meta.append(f"rarity: {rarity} ({rarity[:1].upper()} wildcard)")
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
