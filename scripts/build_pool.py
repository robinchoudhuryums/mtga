#!/usr/bin/env python3
"""Build card-pool.csv — an Arena card reference for deck-building.

This is the pool of cards you could play/craft, separate from card-library.csv
(what you own). It's pulled from Scryfall's `game:arena` filter and, by default,
restricted to Standard-legal cards. Each row carries a Rarity column (the
wildcard cost of anything you don't yet own) and a Legalities column (a
`;`-joined list of formats the card is legal in) so tools can filter a
suggestion to a deck's format — `deck.py suggest` does this by default.

The pool is regenerable — rerun after a new set releases (or to change scope).
Ownership is not stored here; pool.py computes it by joining against
card-library.csv, so this file stays a pure reference.

Usage:
    python3 scripts/build_pool.py                 # Standard-legal Arena cards
    python3 scripts/build_pool.py --all           # every Arena-craftable card
    python3 scripts/build_pool.py --query "game:arena legal:pioneer"
    python3 scripts/build_pool.py --out other.csv

Needs outbound access to api.scryfall.com. No API key required.
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from lib import REPO_ROOT, eprint
from enrich import color_shorthand, oracle_fields, USER_AGENT
from tag_synergies import tags_for

POOL_PATH = os.path.join(REPO_ROOT, "card-pool.csv")
POOL_HEADER = ["Card Name", "Type", "Card Text", "Color(s)", "Synergies",
               "Set Code", "Collector #", "Rarity", "Legalities"]
SEARCH_URL = "https://api.scryfall.com/cards/search"

# Formats worth tracking for deck-building (Arena formats + the major paper
# ones). The Legalities column stores a `;`-joined subset of these in which the
# card is legal, so tools can filter a suggestion to a deck's format.
POOL_FORMATS = ["standard", "pioneer", "modern", "legacy", "vintage", "pauper",
                "historic", "timeless", "alchemy", "explorer", "brawl"]


def legalities_str(card):
    """`;`-joined POOL_FORMATS the card is legal (or restricted) in."""
    leg = card.get("legalities", {})
    return ";".join(f for f in POOL_FORMATS if leg.get(f) in ("legal", "restricted"))


def _get(url, retries=6):
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                wait = float(e.headers.get("Retry-After", 0) or 0) or 1.0 * (2 ** attempt)
                eprint(f"       rate limited; waiting {wait:.0f}s...")
                time.sleep(wait)
                continue
            raise
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(1.0 * (2 ** attempt))
                continue
            raise


def fetch_all(query):
    """Fetch every card matching a Scryfall query (unique by card)."""
    cards = []
    url = f"{SEARCH_URL}?{urllib.parse.urlencode({'q': query, 'unique': 'cards'})}"
    while url:
        data = _get(url)
        cards += data.get("data", [])
        eprint(f"       fetched {len(cards)} / {data.get('total_cards', '?')}")
        url = data.get("next_page") if data.get("has_more") else None
        time.sleep(0.1)
    return cards


def row_for(card):
    type_line, text = oracle_fields(card)
    tags = tags_for({"Type": type_line, "Card Text": text}, card.get("keywords"))
    return {
        "Card Name": card.get("name", ""),
        "Type": type_line,
        "Card Text": text,
        "Color(s)": color_shorthand(card),
        "Synergies": "; ".join(tags),
        "Set Code": card.get("set", "").upper(),
        "Collector #": card.get("collector_number", ""),
        "Rarity": card.get("rarity", "").capitalize(),
        "Legalities": legalities_str(card),
    }


def main():
    ap = argparse.ArgumentParser(description="Build the Arena card-pool reference.")
    ap.add_argument("--query", help="custom Scryfall query (overrides --all)")
    ap.add_argument("--all", action="store_true", help="every Arena card (not just Standard)")
    ap.add_argument("--out", default=POOL_PATH)
    args = ap.parse_args()

    query = args.query or ("game:arena" if args.all else "game:arena legal:standard")
    eprint(f"Fetching pool for query: {query!r}")
    try:
        cards = fetch_all(query)
    except urllib.error.URLError as e:
        eprint(f"ERROR: could not reach Scryfall: {e}")
        return 1

    # Sort by set then collector number for readability.
    def sort_key(c):
        cn = c.get("collector_number", "")
        return (c.get("set", ""), int(cn) if cn.isdigit() else 0, cn)
    cards.sort(key=sort_key)

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=POOL_HEADER, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for c in cards:
            writer.writerow(row_for(c))
    print(f"Wrote {args.out}: {len(cards)} cards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
