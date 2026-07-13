#!/usr/bin/env python3
"""Capture each library card's real mana cost (for hybrid-aware analysis).

card-library.csv's Color(s) column stores color *identity*, which can't tell a
hybrid {W/U} (payable with either color) from a strict {W}{U} (needs both). For
deck-building mana math that distinction matters, so this fetches the actual
mana cost of every card from Scryfall and writes card-mana.csv:

    Card Name, Mana Cost, Mana Value, Keywords

Keywords is Scryfall's authoritative per-card ability list (Flying, Surveil,
Convoke, …), used by tag_synergies.py for accurate, complete synergy tags rather
than a hand-maintained keyword list. This file feeds `deck.py mana`. Rerun after
importing new cards. Lands (no mana cost) are written with an empty cost.

Usage:
    python3 scripts/build_mana.py            # refresh from card-library.csv
    python3 scripts/build_mana.py --pool     # also cover card-pool.csv names
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint
from enrich import USER_AGENT

MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")
POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")


def _front_mana(card):
    """Mana cost of a card, using the front face for double-faced cards."""
    mc = card.get("mana_cost")
    if not mc and card.get("card_faces"):
        mc = card["card_faces"][0].get("mana_cost", "")
    return mc or ""


def fetch(names):
    """Return {name_lower: (mana_cost, mana_value)} via Scryfall batch lookups."""
    out = {}
    for i in range(0, len(names), 75):
        chunk = names[i:i + 75]
        body = json.dumps({"identifiers": [{"name": n} for n in chunk]}).encode()
        req = urllib.request.Request(
            "https://api.scryfall.com/cards/collection", data=body,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json",
                     "Content-Type": "application/json"})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.load(resp)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 5:
                    wait = float(e.headers.get("Retry-After", 0) or 0) or 1.0 * (2 ** attempt)
                    eprint(f"       rate limited; waiting {wait:.0f}s...")
                    time.sleep(wait)
                    continue
                raise
            except urllib.error.URLError:
                # Transient network blip — back off and retry like build_pool.py's
                # _get, rather than failing the whole run on the first hiccup.
                if attempt < 5:
                    time.sleep(1.0 * (2 ** attempt))
                    continue
                raise
        for card in data.get("data", []):
            cost = _front_mana(card)
            mv = card.get("cmc", 0)
            kw = ";".join(card.get("keywords", []) or [])
            for key in (card.get("name", "").lower(),
                        card.get("name", "").lower().split(" // ")[0]):
                out.setdefault(key, (cost, mv, kw))
        eprint(f"       fetched {min(i + 75, len(names))}/{len(names)}")
        time.sleep(0.1)
    return out


def collect_names(paths):
    names, seen = [], set()
    for p in paths:
        with open(p, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                n = (r.get("Card Name") or "").strip()
                if n and n.lower() not in seen:
                    seen.add(n.lower())
                    names.append(n)
    return names


def main():
    ap = argparse.ArgumentParser(description="Build card-mana.csv from Scryfall.")
    ap.add_argument("--pool", action="store_true", help="also include card-pool.csv names")
    ap.add_argument("--out", default=MANA_CSV)
    args = ap.parse_args()

    paths = [DEFAULT_CSV] + ([POOL_CSV] if args.pool and os.path.exists(POOL_CSV) else [])
    names = collect_names(paths)
    eprint(f"Fetching mana costs for {len(names)} card(s)...")
    try:
        data = fetch(names)
    except urllib.error.URLError as e:
        eprint(f"ERROR: could not reach Scryfall: {e}")
        return 1

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Card Name", "Mana Cost", "Mana Value", "Keywords"])
        for n in names:
            cost, mv, kw = data.get(n.lower(), ("", "", ""))
            w.writerow([n, cost, int(mv) if isinstance(mv, (int, float)) else "", kw])
    print(f"Wrote {args.out}: {len(names)} cards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
