#!/usr/bin/env python3
"""Search the Arena card pool, flagging what you own vs. what you'd craft.

Reads card-pool.csv (the reference of Arena-playable cards, built by
build_pool.py) and joins it against card-library.csv (what you own) so every
result shows whether you have it or need to craft it — and at what wildcard cost
(the card's rarity).

Use it while brewing to see all your options, not just cards you already have.

Examples:
    # All blue counterspells, owned or not
    python3 scripts/pool.py --color U --text "counter target"

    # Green ramp you don't own yet, with wildcard cost
    python3 scripts/pool.py --color G --synergy ramp --unowned

    # Rare/Mythic removal you're missing
    python3 scripts/pool.py --synergy removal --unowned --rarity rare,mythic

    # Just count how many Merfolk exist vs. how many you own
    python3 scripts/pool.py --type Merfolk --count

Filters are case-insensitive substring matches, AND-ed together.
"""

import argparse
import csv
import os
import sys
import textwrap

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint, owned_qty
from deck import classify_roles   # functional-role classifier (removal/ramp/draw/…)

# Friendly --role aliases → the canonical labels classify_roles emits, so you can survey
# the collection by what a card DOES (the axis you deckbuild on), not just its synergy tags.
_ROLE_ALIASES = {
    "removal": "Removal (spot)", "spot-removal": "Removal (spot)",
    "sweeper": "Sweeper", "wrath": "Sweeper",
    "counter": "Counter", "counterspell": "Counter",
    "draw": "Card advantage", "card-advantage": "Card advantage", "cardadvantage": "Card advantage",
    "ramp": "Ramp / fixing", "fixing": "Ramp / fixing",
    "cheat": "Cost reduction / cheat", "cost-reduction": "Cost reduction / cheat",
    "payoff": "Payoff / engine", "engine": "Payoff / engine",
}

POOL_PATH = os.path.join(REPO_ROOT, "card-pool.csv")
MANA_PATH = os.path.join(REPO_ROOT, "card-mana.csv")
WC = {"Common": "C", "Uncommon": "U", "Rare": "R", "Mythic": "M"}


def keywords_map():
    """name_lower -> [keywords] from card-mana.csv, to surface named mechanics in a
    --full read (empty if card-mana.csv isn't built)."""
    out = {}
    if os.path.exists(MANA_PATH):
        with open(MANA_PATH, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                n = (r.get("Card Name") or "").strip().lower()
                kw = [k for k in (r.get("Keywords") or "").split(";") if k.strip()]
                if n and kw:
                    out[n] = kw
    return out


def print_full(rows, owned, kwmap):
    """Full oracle text + keyword line + owned/craft per card — the phased-ingestion
    read for scanning the pool as possible additions / craft targets."""
    for c in rows:
        name = (c.get("Card Name") or "").strip()
        have = owned_of(owned, name)
        tag = f"×{have}" if have > 0 else "craft"
        print(f"\n• {name}   [{(c.get('Type') or '').strip() or '?'}]  ·  "
              f"{(c.get('Rarity') or '?')} · {tag}")
        kw = kwmap.get(name.lower())
        if kw:
            print(f"    ⌘ keywords: {', '.join(k.title() for k in kw)}")
        text = (c.get("Card Text") or "").strip()
        for para in (text or "(no oracle text on file)").split("\n"):
            for line in (textwrap.wrap(para, width=90) or [""]):
                print(f"    {line}")


def owned_counts():
    """name_lower -> total quantity owned across all printings."""
    counts = {}
    try:
        _, rows = load_rows(DEFAULT_CSV)
    except FileNotFoundError:
        return counts
    for r in rows:
        name = (r.get("Card Name") or "").strip().lower()
        if not name:
            continue
        q = (r.get("Quantity Owned") or "").strip()
        counts[name] = counts.get(name, 0) + (int(q) if q.isdigit() else 0)
    return counts


def owned_of(owned, name):
    """Copies owned for a pool card name — DFC-aware via the shared lib primitive."""
    return owned_qty(owned, name)


def load_pool(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def matches(card, args, owned):
    def has(col, needle):
        return needle is None or needle.lower() in (card.get(col) or "").lower()

    if not (has("Card Name", args.name) and has("Type", args.type)
            and has("Card Text", args.text) and has("Color(s)", args.color)
            and has("Synergies", args.synergy)):
        return False
    if args.rarity:
        rarities = [r.strip().lower() for r in args.rarity.split(",")]
        if (card.get("Rarity") or "").lower() not in rarities:
            return False
    if args.legal:
        legal = {x.strip() for x in (card.get("Legalities") or "").split(";") if x.strip()}
        if args.legal.lower() not in legal:
            return False
    if args.role:
        want = {_ROLE_ALIASES.get(r.strip().lower(), r.strip()) for r in args.role.split(",")}
        if not (want & classify_roles(card.get("Card Text") or "")):
            return False
    have = owned_of(owned, card.get("Card Name"))
    if args.owned and have <= 0:
        return False
    if args.unowned and have > 0:
        return False
    return True


def print_table(hits, owned):
    cols = ["Have", "Card Name", "Type", "Color(s)", "Rarity"]
    def have_of(c):
        h = owned_of(owned, c.get("Card Name"))
        return f"×{h}" if h > 0 else "craft"
    widths = {c: len(c) for c in cols}
    rowdata = []
    for c in hits:
        vals = {"Have": have_of(c), "Card Name": c.get("Card Name", ""),
                "Type": c.get("Type", ""), "Color(s)": c.get("Color(s)", ""),
                "Rarity": c.get("Rarity", "")}
        rowdata.append(vals)
        for col in cols:
            widths[col] = max(widths[col], len(str(vals[col])))
    widths["Type"] = min(widths["Type"], 34)

    def fmt(vals):
        return "  ".join(str(vals[c])[:widths[c]].ljust(widths[c]) for c in cols)
    print(fmt({c: c for c in cols}))
    print(fmt({c: "-" * widths[c] for c in cols}))
    for vals in rowdata:
        print(fmt(vals))


def main():
    ap = argparse.ArgumentParser(description="Search the Arena card pool with ownership.")
    ap.add_argument("--pool", default=POOL_PATH)
    ap.add_argument("--name"); ap.add_argument("--type"); ap.add_argument("--text")
    ap.add_argument("--color"); ap.add_argument("--synergy")
    ap.add_argument("--role", help="functional role(s), comma-separated: removal, sweeper, "
                    "counter, draw, ramp, cheat, payoff (survey the pool by what a card DOES)")
    ap.add_argument("--rarity", help="comma-separated: common,uncommon,rare,mythic")
    ap.add_argument("--legal", metavar="FMT",
                    help="only cards legal in FMT (e.g. standard, historic) — "
                         "needs a legality-aware pool (build_pool.py)")
    ap.add_argument("--owned", action="store_true", help="only cards you own")
    ap.add_argument("--unowned", action="store_true", help="only cards to craft")
    ap.add_argument("--count", action="store_true")
    ap.add_argument("--csv", action="store_true")
    ap.add_argument("--full", action="store_true",
                    help="print each hit's full oracle text + keywords (deep read for adds)")
    args = ap.parse_args()

    try:
        pool = load_pool(args.pool)
    except FileNotFoundError:
        eprint(f"No pool at {args.pool}. Build it: python3 scripts/build_pool.py")
        return 1

    if args.legal and not (pool and "Legalities" in pool[0]):
        eprint("Pool has no Legalities column — rebuild with build_pool.py to use "
               "--legal. Ignoring the filter.")
        args.legal = None

    owned = owned_counts()
    hits = [c for c in pool if matches(c, args, owned)]

    if args.count:
        have = sum(1 for c in hits
                   if owned_of(owned, c.get("Card Name")) > 0)
        print(f"{len(hits)} match — {have} owned, {len(hits) - have} to craft")
        return 0
    if not hits:
        eprint("No cards matched.")
        return 0

    if args.full:
        print_full(hits, owned, keywords_map())
        craft = sum(1 for c in hits if owned_of(owned, c.get("Card Name")) == 0)
        print(f"\n{len(hits)} match — {len(hits) - craft} owned, {craft} to craft")
        return 0
    if args.csv:
        w = csv.DictWriter(sys.stdout, fieldnames=pool[0].keys())
        w.writeheader()
        w.writerows(hits)
        return 0

    print_table(hits, owned)
    # Summary: wildcard cost of the craftable results by rarity.
    craft = [c for c in hits
             if owned_of(owned, c.get("Card Name")) == 0]
    by_r = {}
    for c in craft:
        r = c.get("Rarity", "?")
        by_r[r] = by_r.get(r, 0) + 1
    print(f"\n{len(hits)} match — {len(hits) - len(craft)} owned, {len(craft)} to craft"
          + (f" ({', '.join(f'{n} {r}' for r, n in sorted(by_r.items()))})" if craft else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
