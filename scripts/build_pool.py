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

from lib import REPO_ROOT, eprint, atomic_write
from enrich import color_shorthand, oracle_fields
from tag_synergies import tags_for
import scryfall
from scryfall import ScryfallUnavailable, NotFound

POOL_PATH = os.path.join(REPO_ROOT, "card-pool.csv")
# Sidecar stamping when the pool was last built, so `deck.py suggest` can warn that
# Standard legality may be stale (cards rotate on a schedule) and prompt a rebuild.
POOL_BUILD_STAMP = os.path.join(REPO_ROOT, "card-pool.build")
POOL_HEADER = ["Card Name", "Type", "Card Text", "Color(s)", "Synergies",
               "Set Code", "Collector #", "Rarity", "Legalities", "Released"]
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


def _get(url):
    """Fetch a Scryfall URL as JSON via the shared resilient client (retries
    429/5xx/timeout; raises ScryfallUnavailable on give-up)."""
    return scryfall.get_json(url)


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
        # Set release date (YYYY-MM-DD) — feeds deck.py suggest's rotation-risk flag
        # (Standard holds ~the last 3 years of sets).
        "Released": card.get("released_at", ""),
    }


def main():
    ap = argparse.ArgumentParser(description="Build the Arena card-pool reference.")
    ap.add_argument("--query", help="custom Scryfall query (overrides --all)")
    ap.add_argument("--all", action="store_true", help="every Arena card (not just Standard)")
    ap.add_argument("--out", default=POOL_PATH)
    ap.add_argument("--allow-shrink", action="store_true",
                    help="permit overwriting even when the new pool is empty or far "
                         "smaller than the existing file (a deliberate narrow --query)")
    args = ap.parse_args()

    query = args.query or ("game:arena" if args.all else "game:arena legal:standard")
    eprint(f"Fetching pool for query: {query!r}")
    try:
        cards = fetch_all(query)
    except ScryfallUnavailable as e:
        eprint(f"ERROR: could not reach Scryfall: {e}\n"
               f"       A slow/blocked Scryfall stopped the pool build; the existing "
               f"card-pool.csv was left unchanged. Rerun where it's reachable.")
        return 1
    except NotFound:
        # Scryfall's search endpoint 404s when a query matches nothing — the empty
        # result F3 guards against. Treat it as zero cards so the guard below refuses
        # to overwrite instead of crashing with a traceback.
        cards = []

    # Sanity floor before we overwrite (audit F3): a query typo or a short/garbled
    # first page can return [] (or a tiny slice) with NO exception, and writing that
    # would silently destroy the ~15.8k-row reference AND stamp it fresh. Refuse to
    # clobber a healthy existing pool with an empty/drastically-smaller result unless
    # --allow-shrink says the shrink is intended.
    existing = 0
    if os.path.exists(args.out):
        try:
            with open(args.out, newline="", encoding="utf-8") as fh:
                existing = sum(1 for _ in csv.DictReader(fh))
        except OSError:
            existing = 0
    if not args.allow_shrink:
        if not cards:
            eprint(f"ERROR: Scryfall returned 0 cards for query {query!r}; refusing to "
                   f"overwrite {args.out} with an empty pool ({existing} existing row(s) "
                   f"left unchanged). Check the query, or pass --allow-shrink to force.")
            return 1
        if existing and len(cards) < existing // 2:
            eprint(f"ERROR: query {query!r} returned {len(cards)} cards, less than half "
                   f"the existing {existing}; refusing to overwrite {args.out} (left "
                   f"unchanged). If this shrink is intended, pass --allow-shrink.")
            return 1

    # Sort by set then collector number for readability.
    def sort_key(c):
        cn = c.get("collector_number", "")
        return (c.get("set", ""), int(cn) if cn.isdigit() else 0, cn)
    cards.sort(key=sort_key)

    def _write(fh):
        writer = csv.DictWriter(fh, fieldnames=POOL_HEADER, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for c in cards:
            writer.writerow(row_for(c))
    atomic_write(args.out, _write)
    # Stamp the build date so suggest can flag a stale pool (rotation happened since).
    import datetime
    if args.out == POOL_PATH:
        atomic_write(POOL_BUILD_STAMP,
                     lambda fh: fh.write(datetime.date.today().isoformat() + "\n"))
    print(f"Wrote {args.out}: {len(cards)} cards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
