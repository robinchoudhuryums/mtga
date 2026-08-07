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

from lib import REPO_ROOT, eprint, atomic_write, csv_schema_error
from enrich import color_shorthand, oracle_fields
from tag_synergies import tags_for
import scryfall
from scryfall import ScryfallUnavailable, NotFound

POOL_PATH = os.path.join(REPO_ROOT, "card-pool.csv")
# Sidecar stamping when the pool was last built, so `deck.py suggest` can warn that
# Standard legality may be stale (cards rotate on a schedule) and prompt a rebuild.
POOL_BUILD_STAMP = os.path.join(REPO_ROOT, "card-pool.build")
POOL_HEADER = ["Card Name", "Type", "Card Text", "Color(s)", "Synergies",
               "Set Code", "Collector #", "Rarity", "Legalities", "Released",
               "Power", "Toughness"]
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
        # Base printed power/toughness, front face for a DFC. Kept as the RAW string,
        # never coerced to an int: Magic prints `*`, `1+*`, `X` and `∞`, and rounding
        # those to a number would invent a fact. `lib.card_power()` parses it and
        # returns None for anything non-numeric, so a caller has to handle "unknown".
        #
        # Why this exists: nothing in the repo stored P/T, so a whole class of card was
        # ungradeable by ANY tool — "whenever a creature with power 4 or greater enters,
        # draw a card" (Garruk's Uprising), Doran-style toughness-matters payoffs, and
        # "power 4 or greater" conditions generally. Grading those had to be done by
        # hand, and it produced a real mis-read: Mossborn Hydra looks like a big body but
        # is printed 0/0 and enters with one counter, so it does NOT trigger Garruk.
        **_pt_fields(card),
    }


def _pt_fields(card):
    """{'Power': str, 'Toughness': str} for a card, using the FRONT face of a DFC (the
    same convention build_mana.py uses for mana cost). Empty strings for a noncreature."""
    p, t = card.get("power"), card.get("toughness")
    if p is None and t is None:
        faces = card.get("card_faces") or []
        if faces:
            p, t = faces[0].get("power"), faces[0].get("toughness")
    return {"Power": "" if p is None else str(p), "Toughness": "" if t is None else str(t)}


FRESH_DAYS = 7          # a pool younger than this is reused unless --refetch


def tagger_fingerprint():
    """Hash of tag_synergies.py — the file whose `tags_for()` derives every pool row's
    Synergies at fetch time. Recorded in the build stamp so a tag-pattern edit defeats
    the freshness reuse: K-10 mandates `build_pool.py --all` after one, and the reuse
    made that mandated command a silent no-op for up to a week (broad-scan BS2-23).
    Returns "" when unreadable, which compares equal to nothing and so never forces a
    rebuild on its own."""
    import hashlib
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "tag_synergies.py"), "rb") as fh:
            return hashlib.sha1(fh.read()).hexdigest()[:16]
    except OSError:
        return ""


def read_stamp():
    """(iso_date, query, tag_fingerprint) from the card-pool.build sidecar.

    The sidecar has always held the build DATE on its first line; the QUERY is a second
    line added for the freshness check. `deck.pool_staleness_days` reads `[:10]` of the
    stripped file, so the date must stay first — that keeps the older reader working
    unchanged.
    """
    if not os.path.exists(POOL_BUILD_STAMP):
        return None, None, None
    try:
        lines = open(POOL_BUILD_STAMP, encoding="utf-8").read().splitlines()
    except OSError:
        return None, None, None
    date = (lines[0].strip() if lines else "") or None
    # Line 3 (optional) is the tag-pattern fingerprint — absent in a stamp written
    # before BS2-23, which reads as "unknown" and must NOT force a rebuild.
    return (date, (lines[1].strip() if len(lines) > 1 else None),
            (lines[2].strip() if len(lines) > 2 else None))


def stamp_age_days(date):
    if not date:
        return None
    try:
        import datetime
        return (datetime.date.today()
                - datetime.date.fromisoformat(date[:10])).days
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description="Build the Arena card-pool reference.")
    ap.add_argument("--query", help="custom Scryfall query (overrides --all)")
    ap.add_argument("--all", action="store_true", help="every Arena card (not just Standard)")
    ap.add_argument("--out", default=POOL_PATH)
    ap.add_argument("--allow-shrink", action="store_true",
                    help="permit overwriting even when the new pool is empty or far "
                         "smaller than the existing file (a deliberate narrow --query)")
    ap.add_argument("--refetch", action="store_true",
                    help="rebuild even when the existing pool is still fresh")
    ap.add_argument("--max-age", type=int, default=FRESH_DAYS, metavar="DAYS",
                    help=f"reuse a pool built within this many days (default "
                         f"{FRESH_DAYS}; 0 always rebuilds)")
    args = ap.parse_args()
    # The MIRROR of F-02 (broad-scan Batch G). lib.csv_schema_error closed "a library
    # writer pointed at a derived file"; nothing closed the other direction, so
    # `--out card-library.csv` would overwrite the inventory with THIS builder's
    # header — and the shrink guard cannot object, because 15.9k rows over 2,085 is
    # GROWTH. Refuse UP FRONT, before any Scryfall traffic, the way enrich.py does
    # (tests/test_enrich.py pins that ordering for F-02 itself).
    problem = csv_schema_error(args.out, POOL_HEADER)
    if problem:
        eprint(f"ERROR: {problem}")
        return 1

    query = args.query or ("game:arena" if args.all else "game:arena legal:standard")

    # FRESHNESS SKIP — the whole cost of this tool is the paginated fetch: measured
    # 222.5s of a 224.3s run (99%), 91 pages at ~2.4s each, against 1.8s to derive every
    # row. So the only lever is not fetching.
    #
    # Skipping is CORRECT, not just fast, because this file is the whole Arena card pool
    # and is INDEPENDENT OF WHAT YOU OWN. The motivating case — `make refresh` after an
    # ingest — changes the LIBRARY; the pool is unaffected, so re-fetching 15.9k cards
    # to write out the same rows was pure waste.
    #
    # What genuinely does go stale is `Legalities` (rotation, bans, Alchemy rebalances)
    # and the arrival of a new SET, which is why this is a time window rather than a
    # blanket reuse: past --max-age it always rebuilds. `deck.pool_staleness_days` and
    # `suggest`'s stale-pool warning already exist for exactly this question, so the
    # freshness notion is established here, not invented.
    #
    # The recorded QUERY must match too. `--all` and the Standard-only default produce
    # different files, and reusing a Standard-scoped pool for an `--all` request would
    # silently freeze the wrong scope — the shrink guard below catches a shrink, but it
    # cannot see that the file answers a different question.
    #
    # ...and the pool's `Synergies` must not be stale either (broad-scan BS2-23).
    # G-18 justifies the reuse with "the pool is independent of what you OWN, so an
    # ingest cannot change it" — true for the INGEST case, and false for the other
    # documented reason to run this: K-10 mandates `build_pool.py --all` after a
    # tag-pattern edit, because every pool row's Synergies is derived inside
    # `row_for()` at FETCH time. Skipping on freshness made that mandated command a
    # silent no-op for up to a week, with step 2/6 of `make refresh` announcing
    # itself as having run and check_all green throughout. So: a tagger newer than
    # the pool defeats the freshness reuse.
    # The signal is the tagger's CONTENT, not its mtime. A fresh clone stamps every
    # file with the same checkout time in arbitrary order, so an mtime comparison
    # would force a ~5-minute full rebuild on the first refresh after every clone —
    # and this repo already learned "content, not mtime" the hard way (F-04, where a
    # copy2'd .bak's mtime described its CONTENTS' age, not the backup's).
    # An ABSENT fingerprint (a stamp written before BS2-23) is UNKNOWN, and unknown has
    # to mean rebuild-once. It first meant "don't force a rebuild", to spare people one
    # surprise refetch — and that quietly disarmed the whole mechanism: the reuse path
    # returns before any stamp is written, so a legacy two-line stamp never ACQUIRES a
    # fingerprint, and as long as the pool stayed fresh no tag edit would ever be
    # detected. Found the only way it could be: the seven K-01 keyword mappings were
    # added, `make refresh` ran and announced build_pool, and card-pool.csv came back
    # byte-identical (broad-scan BS3-02). The grace clause is the same shape as the bug
    # it was bolted onto — a freshness check that cannot see the thing it exists to see.
    # It costs one full rebuild, exactly once per stamp, and then the escape hatch works.
    stamp_date, stamp_query, stamp_tags = read_stamp()
    tags_changed = stamp_tags is not None and stamp_tags != tagger_fingerprint()
    tags_unknown = stamp_tags is None
    age = stamp_age_days(stamp_date)
    if tags_changed and not args.refetch:
        print("tag_synergies.py is newer than the pool — rebuilding so every row's "
              "Synergies is re-derived through the current tags_for() (K-10).")
    elif tags_unknown and not args.refetch and os.path.exists(args.out):
        print("This pool was built before the tag fingerprint existed, so whether its "
              "Synergies match the current tags_for() is unknown — rebuilding once to "
              "record it. Later refreshes reuse a fresh pool as before (BS3-02).")
    if (not args.refetch and args.out == POOL_PATH and os.path.exists(args.out)
            and age is not None and args.max_age > 0 and age <= args.max_age
            and stamp_query == query and not tags_changed and not tags_unknown):
        eprint(f"Pool built {age} day(s) ago for the same query — reusing "
               f"{os.path.basename(args.out)} (--refetch to rebuild, --max-age to change "
               f"the window).")
        print(f"{args.out} is fresh ({age}d old); not rebuilt.")
        return 0
    if not args.refetch and stamp_query is not None and stamp_query != query:
        eprint(f"Existing pool was built for query {stamp_query!r}, not {query!r} — "
               f"rebuilding.")

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
    # Stamp the build date so suggest can flag a stale pool (rotation happened since),
    # plus the QUERY so the freshness skip above can tell a full-pool build from a
    # Standard-only one. Date stays on line 1 for `deck.pool_staleness_days`.
    import datetime
    if args.out == POOL_PATH:
        atomic_write(POOL_BUILD_STAMP,
                     lambda fh: fh.write(datetime.date.today().isoformat() + "\n"
                                         + query + "\n"
                                         + tagger_fingerprint() + "\n"))
    print(f"Wrote {args.out}: {len(cards)} cards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
