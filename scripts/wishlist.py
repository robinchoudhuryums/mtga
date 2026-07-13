#!/usr/bin/env python3
"""Craft-target / wishlist manager — unowned cards you want to craft or build around.

Separate from card-library.csv (what you OWN) and card-pool.csv (EVERY Arena
card): this is your curated shortlist of unowned cards worth crafting, slotting
into a deck, or building a new concept around — plus a per-set summary so you can
pick which packs to open with gems.

card-wishlist.csv columns:
    Card Name, Type, Card Text, Color(s), Synergies, Set Code, Collector #,
    Rarity, Target, Note

Rarity / Color(s) / Type / Card Text / Synergies are auto-filled from
card-pool.csv (with a Scryfall fallback for cards the pool lacks — e.g. newer
double-faced cards, stored under their full "Front // Back" name). `Target` and
`Note` are yours to annotate: a deck id it's for, "general", "concept: ...", or
why it caught your eye.

Usage:
    # add a batch pasted from MTG Arena ("<qty> <Name> (<SET>) <#>" lines)
    python3 scripts/wishlist.py --add batch.txt
    pbpaste | python3 scripts/wishlist.py --add -

    # browse / filter (case-insensitive substring, AND-ed)
    python3 scripts/wishlist.py                        # the whole wishlist
    python3 scripts/wishlist.py --set SOS --rarity rare,mythic
    python3 scripts/wishlist.py --color R --synergy firebending
    python3 scripts/wishlist.py --target 14 --note ""  # by annotation

    # pack optimization: how many wishlist cards each set would net you, by rarity
    python3 scripts/wishlist.py --by-set

    # cards you've since acquired (time to drop them from the wishlist)
    python3 scripts/wishlist.py --owned

Set a card's Target/Note by editing card-wishlist.csv directly (it's a plain CSV).
"""

import argparse
import csv
import os
import sys

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint

WISHLIST_CSV = os.path.join(REPO_ROOT, "card-wishlist.csv")
POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")

HEADER = ["Card Name", "Type", "Card Text", "Color(s)", "Synergies",
          "Set Code", "Collector #", "Rarity", "Target", "Note"]
RARITY_RANK = {"Mythic": 0, "Rare": 1, "Uncommon": 2, "Common": 3, "": 4, "?": 5}

# "<qty> <Name>" with optional "(SET)" + collector number — mirrors deck.py/import_arena.
import re
LINE_RE = re.compile(r"^\s*(\d+)\s*[xX]?\s+(.+?)\s*(?:\(([^)]+)\)\s*([^\s]+)?)?\s*$")
SECTIONS = {"deck", "sideboard", "commander", "companion", "maybeboard", "about"}


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def load_pool_index():
    """name_lower (full name AND front-face) -> pool row, for enrichment."""
    idx = {}
    if not os.path.exists(POOL_CSV):
        return idx
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            if not n:
                continue
            idx.setdefault(n, r)
            idx.setdefault(n.split(" // ")[0], r)
    return idx


def owned_index():
    """name_lower (full AND front-face) -> total quantity owned across printings."""
    counts = {}
    try:
        _, rows = load_rows(DEFAULT_CSV)
    except FileNotFoundError:
        return counts
    for r in rows:
        n = (r.get("Card Name") or "").strip().lower()
        if not n:
            continue
        q = (r.get("Quantity Owned") or "").strip()
        c = int(q) if q.isdigit() else 0
        for k in (n, n.split(" // ")[0]):
            counts[k] = counts.get(k, 0) + c
    return counts


def load_wishlist():
    if not os.path.exists(WISHLIST_CSV):
        return []
    with open(WISHLIST_CSV, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_wishlist(rows):
    # Sort for stable, browsable output: set, then rarity (mythic first), then name.
    rows = sorted(rows, key=lambda r: (
        (r.get("Set Code") or "").upper(),
        RARITY_RANK.get((r.get("Rarity") or "").capitalize(), 9),
        (r.get("Card Name") or "").lower()))
    with open(WISHLIST_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow({c: (r.get(c, "") or "") for c in HEADER})


# --------------------------------------------------------------------------- #
# Enrichment (pool first, Scryfall fallback)
# --------------------------------------------------------------------------- #
def _from_scryfall(name, set_code):
    """Best-effort single lookup for a card the pool lacks (e.g. a new DFC). Returns
    an enrichment dict or None. Imports network/enrich bits lazily so the common
    (pool-hit) path stays dependency- and network-free."""
    import json
    import time
    import urllib.error
    import urllib.parse
    import urllib.request
    from enrich import color_shorthand, oracle_fields
    from tag_synergies import tags_for

    def _get(params):
        url = "https://api.scryfall.com/cards/named?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(
            url, headers={"User-Agent": "mtga-card-library/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)

    card = None
    for params in ({"exact": name, "set": set_code.lower()} if set_code else {"exact": name},
                   {"fuzzy": name}):
        try:
            card = _get(params)
            break
        except (urllib.error.URLError, ValueError):
            continue
    time.sleep(0.1)
    if not card:
        return None
    type_line, text = oracle_fields(card)
    tags = tags_for({"Type": type_line, "Card Text": text}, card.get("keywords"))
    return {
        "Card Name": card.get("name", name),
        "Type": type_line, "Card Text": text,
        "Color(s)": color_shorthand(card),
        "Synergies": "; ".join(tags),
        "Rarity": (card.get("rarity") or "").capitalize(),
    }


def enrich(name, set_code, collector, pool):
    """Build a wishlist row for one card. Uses the canonical (full) name from the
    pool/Scryfall so double-faced cards join cleanly with the rest of the tooling."""
    p = pool.get(name.lower())
    if p:
        data = {"Card Name": p.get("Card Name", name), "Type": p.get("Type", ""),
                "Card Text": p.get("Card Text", ""), "Color(s)": p.get("Color(s)", ""),
                "Synergies": p.get("Synergies", ""), "Rarity": p.get("Rarity", "")}
    else:
        s = _from_scryfall(name, set_code)
        if s is None:
            eprint(f"WARN:  could not resolve {name!r} in pool or Scryfall — "
                   "added with name only.")
            data = {"Card Name": name, "Type": "", "Card Text": "", "Color(s)": "",
                    "Synergies": "", "Rarity": ""}
        else:
            data = s
    data["Set Code"] = set_code
    data["Collector #"] = collector
    data.setdefault("Target", "")
    data.setdefault("Note", "")
    return data


def cmd_add(path):
    text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    entries = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.lower() in SECTIONS or line.startswith("#") or line.startswith("//"):
            continue
        m = LINE_RE.match(line)
        if not m:
            eprint(f"WARN:  line {lineno}: could not parse {raw.strip()!r}")
            continue
        entries.append((m.group(2).strip(), (m.group(3) or "").strip(),
                        (m.group(4) or "").strip()))
    if not entries:
        eprint("No card lines found.")
        return 1

    pool = load_pool_index()
    owned = owned_index()
    existing = load_wishlist()
    seen = {((r.get("Card Name") or "").strip().lower(),
             (r.get("Set Code") or "").strip().lower(),
             (r.get("Collector #") or "").strip().lower()) for r in existing}

    added, dupes, owned_hits, warns = 0, 0, [], 0
    for name, setc, cn in entries:
        row = enrich(name, setc, cn, pool)
        key = (row["Card Name"].strip().lower(), setc.lower(), cn.lower())
        if key in seen:
            dupes += 1
            continue
        if owned.get(name.lower(), 0) > 0:
            owned_hits.append(row["Card Name"])
        if not row.get("Rarity") and not row.get("Type"):
            warns += 1
        existing.append(row)
        seen.add(key)
        added += 1

    write_wishlist(existing)
    print(f"Added {added} card(s) to the wishlist ({dupes} already listed). "
          f"Wishlist now has {len(existing)} card(s). Wrote {os.path.basename(WISHLIST_CSV)}.")
    if owned_hits:
        print(f"NOTE: {len(owned_hits)} added card(s) you ALREADY OWN "
              f"(consider removing): {', '.join(owned_hits[:8])}"
              + ("…" if len(owned_hits) > 8 else ""))
    return 0


# --------------------------------------------------------------------------- #
# Query / summary
# --------------------------------------------------------------------------- #
def _match(card, args):
    def has(col, needle):
        return needle is None or needle.lower() in (card.get(col) or "").lower()
    if not (has("Card Name", args.name) and has("Type", args.type)
            and has("Card Text", args.text) and has("Color(s)", args.color)
            and has("Synergies", args.synergy) and has("Set Code", args.set)
            and has("Target", args.target) and has("Note", args.note)):
        return False
    if args.rarity:
        want = {x.strip().lower() for x in args.rarity.split(",")}
        if (card.get("Rarity") or "").lower() not in want:
            return False
    return True


def cmd_by_set(rows, owned):
    """Pack-optimization view: wishlist cards per set, broken down by rarity."""
    from collections import Counter
    per_set, per_setrar = Counter(), Counter()
    still = 0
    for c in rows:
        if owned.get((c.get("Card Name") or "").strip().lower(), 0) > 0:
            continue  # already acquired — don't count toward crafting/packs
        still += 1
        s = (c.get("Set Code") or "?").upper()
        per_set[s] += 1
        per_setrar[(s, (c.get("Rarity") or "?").capitalize())] += 1
    if not per_set:
        print("Wishlist is empty (or everything on it is already owned).")
        return 0
    print(f"Wishlist by set — {still} unowned card(s). Open packs of the top sets first.\n")
    print(f"  {'Set':5} {'Cards':>5}   Rarity breakdown")
    print("  " + "-" * 52)
    for s, n in sorted(per_set.items(), key=lambda kv: (-kv[1], kv[0])):
        rr = "  ".join(f"{per_setrar[(s, x)]} {x}"
                       for x in ("Mythic", "Rare", "Uncommon", "Common", "?")
                       if per_setrar[(s, x)])
        print(f"  {s:5} {n:>5}   {rr}")
    return 0


def print_table(hits, owned):
    cols = ["Have", "Card Name", "Type", "Color(s)", "Set", "Rarity", "Target"]
    def have_of(c):
        return "own" if owned.get((c.get("Card Name") or "").strip().lower(), 0) > 0 else ""
    data = []
    for c in hits:
        data.append({"Have": have_of(c), "Card Name": c.get("Card Name", ""),
                     "Type": c.get("Type", ""), "Color(s)": c.get("Color(s)", ""),
                     "Set": c.get("Set Code", ""), "Rarity": c.get("Rarity", ""),
                     "Target": c.get("Target", "")})
    widths = {col: len(col) for col in cols}
    for d in data:
        for col in cols:
            widths[col] = max(widths[col], len(str(d[col])))
    widths["Type"] = min(widths["Type"], 32)
    widths["Card Name"] = min(widths["Card Name"], 32)

    def fmt(vals):
        return "  ".join(str(vals[c])[:widths[c]].ljust(widths[c]) for c in cols)
    print(fmt({c: c for c in cols}))
    print(fmt({c: "-" * widths[c] for c in cols}))
    for d in data:
        print(fmt(d))


def main():
    ap = argparse.ArgumentParser(description="Manage the craft-target / wishlist.")
    ap.add_argument("--add", metavar="FILE",
                    help="append an Arena-export batch (or '-' for stdin), enriching each card")
    ap.add_argument("--by-set", action="store_true",
                    help="summarize unowned wishlist cards per set (pack optimization)")
    ap.add_argument("--owned", action="store_true",
                    help="show only wishlist cards you now OWN (drop candidates)")
    ap.add_argument("--name"); ap.add_argument("--type"); ap.add_argument("--text")
    ap.add_argument("--color"); ap.add_argument("--synergy"); ap.add_argument("--set")
    ap.add_argument("--target"); ap.add_argument("--note")
    ap.add_argument("--rarity", help="comma-separated: common,uncommon,rare,mythic")
    ap.add_argument("--count", action="store_true")
    args = ap.parse_args()

    if args.add:
        return cmd_add(args.add)

    rows = load_wishlist()
    if not rows:
        eprint("Wishlist is empty. Add cards: python3 scripts/wishlist.py --add batch.txt")
        return 0
    owned = owned_index()

    if args.by_set:
        return cmd_by_set(rows, owned)

    hits = [c for c in rows if _match(c, args)]
    if args.owned:
        hits = [c for c in hits if owned.get((c.get("Card Name") or "").strip().lower(), 0) > 0]

    if args.count:
        print(len(hits))
        return 0
    if not hits:
        eprint("No wishlist cards matched.")
        return 0

    print_table(hits, owned)
    still = sum(1 for c in hits
                if owned.get((c.get("Card Name") or "").strip().lower(), 0) == 0)
    from collections import Counter
    by_r = Counter((c.get("Rarity") or "?").capitalize() for c in hits
                   if owned.get((c.get("Card Name") or "").strip().lower(), 0) == 0)
    tail = ", ".join(f"{by_r[x]} {x}" for x in ("Mythic", "Rare", "Uncommon", "Common", "?")
                     if by_r[x])
    print(f"\n{len(hits)} card(s) — {still} to craft" + (f" ({tail})" if tail else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
