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
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint, atomic_write
import scryfall
from scryfall import ScryfallUnavailable, NotFound

MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")
POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")


def _front_mana(card):
    """Mana cost of a card, using the front face for double-faced cards."""
    mc = card.get("mana_cost")
    if not mc and card.get("card_faces"):
        mc = card["card_faces"][0].get("mana_cost", "")
    return mc or ""


def _store(out, card):
    """Index one Scryfall card under its full and front-face name."""
    cost = _front_mana(card)
    mv = card.get("cmc", 0)
    kw = ";".join(card.get("keywords", []) or [])
    full = (card.get("name") or "").lower()
    for key in (full, full.split(" // ")[0]):
        if key:
            out.setdefault(key, (cost, mv, kw))


def fetch(names):
    """Return {name_lower: (mana_cost, mana_value, keywords)} via Scryfall batch lookups,
    with a single-card fallback for the names the batch can't match."""
    out = {}
    for i in range(0, len(names), 75):
        chunk = names[i:i + 75]
        # Shared resilient client: retries 429/5xx/timeout and raises
        # ScryfallUnavailable on give-up, which main() turns into a clean error
        # (leaving the existing card-mana.csv untouched) instead of a traceback.
        data = scryfall.post_collection(chunk)
        for card in data.get("data", []):
            _store(out, card)
        eprint(f"       fetched {min(i + 75, len(names))}/{len(names)}")
        time.sleep(0.1)

    # Fallback for names /cards/collection won't match by full name — overwhelmingly
    # SPLIT and room cards ("Life // Death", "Bottomless Pool // Locker Room"), which
    # /cards/named resolves from the FRONT face. Without it those rows are written BLANK,
    # so the card reads as having no cost anywhere downstream; a full-pool build left 631
    # such rows (surfaced only because the unresolved-name report exists — audit F-12).
    # enrich.py has used this same front-face fallback for the same reason.
    missing = [n for n in names if n.lower() not in out]
    if missing:
        eprint(f"       {len(missing)} name(s) unmatched by batch — trying front-face lookups")
    for j, n in enumerate(missing, 1):
        front = n.split(" // ")[0]
        try:
            card = scryfall.named({"exact": front}, retries=2, timeout=20)
        except NotFound:
            continue                      # genuinely no such card — leave it blank
        except ScryfallUnavailable as e:
            eprint(f"WARN:  Scryfall went unreachable during front-face lookups ({e}); "
                   f"{len(missing) - j + 1} name(s) left blank.")
            break
        # Accept ONLY when the resolved card IS the one asked for. A bare front name can
        # name a DIFFERENT card ("Life" is also a card), and writing a wrong cost is worse
        # than writing none — the whole point of this file is that costs are trustworthy.
        got = (card.get("name") or "").lower()
        if got == n.lower() or got.split(" // ")[0] == n.lower():
            _store(out, card)
        if j % 100 == 0:
            eprint(f"       front-face {j}/{len(missing)}")
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


def load_existing(path):
    """{name_lower: (cost, mv, keywords)} for the rows already RESOLVED in `path`.

    A row counts as resolved when its **Mana Value** is non-blank. That is the load-
    bearing distinction: an unmatched name is written cost/mv/keywords all blank, while
    a LAND legitimately has a blank Mana Cost but a real Mana Value of 0 — 673 of them
    in the current pool against 1 genuinely unresolved row. Keying "resolved" off the
    cost would therefore re-fetch every land forever and, worse, would let a truly
    unresolved row look settled.

    Keyed by the row's exact Card Name only — deliberately NOT also under the DFC front
    face the way `_store` indexes a fetched card. Reuse must never answer for a name it
    was not written for: a wrong cost that persists across runs is far worse than a
    redundant fetch, and an exact-match miss just costs one lookup.
    """
    out = {}
    if not os.path.exists(path):
        return out
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                name = (r.get("Card Name") or "").strip()
                mv = (r.get("Mana Value") or "").strip()
                if not name or not mv:
                    continue
                out[name.lower()] = ((r.get("Mana Cost") or "").strip(), mv,
                                     (r.get("Keywords") or "").strip())
    except OSError:
        return {}
    return out


def main():
    ap = argparse.ArgumentParser(description="Build card-mana.csv from Scryfall.")
    ap.add_argument("--pool", action="store_true", help="also include card-pool.csv names")
    ap.add_argument("--out", default=MANA_CSV)
    ap.add_argument("--allow-shrink", action="store_true",
                    help="permit overwriting even when the new file would be far smaller "
                         "(a deliberate narrowing back to library-only scope)")
    ap.add_argument("--refetch", action="store_true",
                    help="re-fetch every name instead of reusing the rows already "
                         "resolved in the output file (the slow, full rebuild)")
    args = ap.parse_args()

    paths = [DEFAULT_CSV] + ([POOL_CSV] if args.pool and os.path.exists(POOL_CSV) else [])
    names = collect_names(paths)

    # Scope guard, mirroring build_pool.py's. This tool DEFAULTS to library-only, so a
    # plain `build_mana.py` run over a pool-scoped file silently discards ~14k rows —
    # and that is not hypothetical: card-mana.csv was found at 1,695 rows against a
    # 15,850-card pool, exactly this mistake, which also silently disabled the one-card
    # keyword heuristic that needs a pool-sized corpus. CLAUDE.md warns about it in
    # prose; this makes it un-doable by accident. Refuse a big shrink unless asked.
    existing = 0
    if os.path.exists(args.out):
        try:
            with open(args.out, newline="", encoding="utf-8") as fh:
                existing = sum(1 for _ in csv.DictReader(fh))
        except OSError:
            existing = 0
    if not args.allow_shrink and existing and len(names) < existing // 2:
        eprint(f"ERROR: this run covers {len(names)} card(s) but {os.path.basename(args.out)} "
               f"already has {existing} — refusing to shrink it by more than half (left "
               f"unchanged).\n"
               f"       You are probably missing --pool: the file is pool-scoped and a plain "
               f"run is library-only. Pass --pool to keep coverage, or --allow-shrink if the "
               f"narrowing is intended.")
        return 1
    # INCREMENTAL by default: a card's printed mana cost and keywords do not change, so
    # re-pricing all ~15.9k pool cards on every `make refresh` bought nothing and cost
    # ~10 minutes against Scryfall's rate limit — the same for a four-card ingest as for
    # a full rebuild, which is why the ingest loop was the most expensive thing here.
    # Reuse the rows already resolved and fetch only what is NEW or still unresolved
    # (a blank row is retried, so a name that failed last time gets another chance).
    # `--refetch` restores the full rebuild for an errata/rebalance sweep.
    #
    # This does NOT fork the rebuild recipe. The Makefile step is still
    # `build_mana.py --pool`; it simply stops doing work it already did. Adding a second
    # "quick refresh" target was the obvious alternative and is exactly what CLAUDE.md
    # forbids — the order is the one thing that must have a single definition.
    reuse = {} if args.refetch else load_existing(args.out)
    todo = [n for n in names if n.lower() not in reuse]
    if reuse:
        eprint(f"Reusing {len(names) - len(todo)} already-resolved row(s) from "
               f"{os.path.basename(args.out)}; {len(todo)} to fetch. "
               f"(--refetch for a full rebuild.)")
    data = dict(reuse)
    if todo:
        eprint(f"Fetching mana costs for {len(todo)} card(s)...")
        try:
            data.update(fetch(todo))
        except ScryfallUnavailable as e:
            eprint(f"ERROR: could not reach Scryfall: {e}\n"
                   f"       A slow/blocked Scryfall stopped the mana build; the existing "
                   f"card-mana.csv was left unchanged. Rerun where it's reachable.")
            return 1
    else:
        # Nothing to fetch means nothing to ask Scryfall for, so a no-change refresh now
        # completes OFFLINE. Worth stating rather than leaving the reader to infer it.
        eprint("Nothing new to fetch — every name already has a resolved row.")

    # A name Scryfall's batch didn't return gets a BLANK row. That is the right value
    # (we must not invent a cost), but it must not be SILENT: this file is rewritten
    # whole, so a card that stops resolving quietly loses a cost/keywords it previously
    # had, and every downstream reader — `deck.py mana`, the curve, keyword-aware
    # tagging — just reports "unknown" with no hint that anything regressed. enrich.py
    # already warns per unmatched name; this does the same (audit F-12). Note a land
    # legitimately has an empty cost but IS returned, so it never lands here.
    unresolved = [n for n in names if n.lower() not in data]

    # Mana Value arrives in two shapes now and BOTH must render the same: Scryfall's
    # `cmc` is a float, while a reused row carries the string already in the file. The
    # original `int(mv) if isinstance(mv, (int, float)) else ""` silently blanked
    # anything non-numeric — which with reuse would have wiped the Mana Value of every
    # row it reused, i.e. the whole file on the first incremental run. A blank stays
    # blank, because that is how an unresolved name is recorded.
    def _mv_out(mv):
        if isinstance(mv, (int, float)):
            return int(mv)
        return (mv or "").strip()

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Card Name", "Mana Cost", "Mana Value", "Keywords"])
    for n in names:
        cost, mv, kw = data.get(n.lower(), ("", "", ""))
        w.writerow([n, cost, _mv_out(mv), kw])
    rendered = buf.getvalue()

    # An unchanged refresh should be a no-op, not a rewrite: `atomic_write` takes a
    # timestamped `.bak` every time, and now that a refresh is cheap enough to run often
    # that would litter backups of a file that never changed.
    if os.path.exists(args.out):
        try:
            with open(args.out, newline="", encoding="utf-8") as fh:
                if fh.read() == rendered:
                    print(f"{args.out} already up to date: {len(names)} cards, unchanged.")
                    return 0
        except OSError:
            pass

    atomic_write(args.out, lambda fh: fh.write(rendered))
    print(f"Wrote {args.out}: {len(names)} cards"
          + (f", {len(unresolved)} unresolved (blank rows)." if unresolved else "."))
    if unresolved:
        shown = ", ".join(unresolved[:8]) + ("…" if len(unresolved) > 8 else "")
        eprint(f"WARN:  {len(unresolved)} name(s) had no Scryfall match and were written "
               f"with a BLANK mana cost/keywords: {shown}\n"
               f"       They will read as 'unknown cost' in deck.py mana/stats and get "
               f"keyword-less synergy tags. Check spelling, or an Arena-only card may "
               f"need its row hand-filled.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
