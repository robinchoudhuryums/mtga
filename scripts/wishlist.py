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
import math
import os
import sys

from lib import (DEFAULT_CSV, REPO_ROOT, load_rows, eprint, atomic_write, owned_qty,
                 alias_front, card_colors, card_distinctiveness, color_matches,
                 primary_type)
from scryfall import ScryfallUnavailable

WISHLIST_CSV = os.path.join(REPO_ROOT, "card-wishlist.csv")
POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")

HEADER = ["Card Name", "Type", "Card Text", "Color(s)", "Synergies",
          "Set Code", "Collector #", "Rarity", "Target", "Note", "Power", "Power Source"]

# PROVENANCE for the Power column. Both `--add` and `--seed-power` write a heuristic
# estimate into the same cell a hand grade goes in, so nothing could tell an auto-seed
# from a human judgment — which meant "verify this number" had to be said about EVERY
# row, including the ones already graded. Written as "seed" by the estimators.
#
# NOTE the trust rule, because this comment used to state the OPPOSITE of the code: only
# `hand` is trusted. `seed`, `unknown` AND BLANK are all untrusted — see
# `power_is_seeded`, which is the definition, and G-17. A blank cell is a row nobody has
# graded, so treating it as a human judgment is the one reading that cannot be right
# (BS4-21).
POWER_SEEDED = "seed"       # written by --add / --seed-power
POWER_HAND = "hand"         # a human graded it; trust the number
POWER_UNKNOWN = "unknown"   # predates this column — provenance genuinely not recorded


def power_is_seeded(row):
    """True when this row's Power should NOT be trusted as a human judgment — either a
    heuristic seed, or a row from before provenance was recorded.

    `unknown` is a deliberate third value rather than a guess. Rows predating the column
    were mostly `--add` auto-seeds but some were hand-graded, and forcing either default
    would be wrong in one direction: marking them all `seed` re-flags real judgments,
    marking them all `hand` silently blesses estimates. Unknown says so."""
    return (row.get("Power Source") or "").strip().lower() in (POWER_SEEDED, POWER_UNKNOWN, "")
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
    # SECOND pass per lib.alias_front's contract (BS2-40): the in-loop `setdefault`
    # on the front name is order-dependent — a full-name row seen early claims the
    # front before a real card of that name arrives, and `enrich()` would then store
    # the WRONG card's fields into a new wishlist row. Latent (0 front-name
    # collisions in today's pool), and registered in check_dfc's _ALIASED_LOADERS.
    return alias_front(idx)


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
        # Sum under the card's REAL stored name only (audit F13's per-name sum across
        # printings). The front-face alias is a SECOND pass below.
        counts[n] = counts.get(n, 0) + c
    # A front alias is added only where NO real row already claims that name — the rule
    # `lib.alias_front` exists to enforce. The predecessor loop added the count to BOTH
    # keys unconditionally, so a distinct real card sharing a DFC's front name ("Life" vs
    # "Life // Death") had the DFC's copies ADDED to its own total (BS4-20).
    #
    # Now the shared helper rather than a fourth private copy of it. The copy was
    # behaviourally identical, which is exactly why it was worth removing: G-63 gives
    # aliasing ONE home so a future correction reaches every caller, and a loop that
    # merely happens to agree today is the drift shape this repo keeps paying for. Its
    # three siblings (`deck.load_collection`, `pool.owned_counts`, `card._owned_index`)
    # were routed through `alias_front` in BS6-01; this was the last hold-out.
    return alias_front(counts)


def _owned_of(owned, name):
    """Copies owned for a wishlist card name — DFC-aware via the shared lib primitive."""
    return owned_qty(owned, name)


class TargetAuditUnavailable(Exception):
    """The wishlist-target audit could not run because the deck roster wouldn't load.

    A distinct exception rather than a swallowed error because the two outcomes it
    separates look identical downstream and mean opposite things: "no issues found" and
    "nothing was checked" are both an empty list (BS4-08)."""


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
    def _write(fh):
        w = csv.DictWriter(fh, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow({c: (r.get(c, "") or "") for c in HEADER})
    # Atomic + timestamped .bak: the hand-annotated Target/Note/Power columns are the
    # source of truth and had no backup before (audit F5).
    atomic_write(WISHLIST_CSV, _write)


# --------------------------------------------------------------------------- #
# Enrichment (pool first, Scryfall fallback)
# --------------------------------------------------------------------------- #
def _from_scryfall(name, set_code):
    """Best-effort single lookup for a card the pool lacks (e.g. a new DFC).

    Returns an enrichment dict on success, or None if Scryfall genuinely has no
    such card. Raises ScryfallUnavailable when Scryfall can't be reached (429 /
    5xx / timeout / bad body) — the caller MUST NOT treat that transient outage as
    a real 'not found' and silently store a blank row (audit F14). Imports the
    enrich/tag bits lazily so the common (pool-hit) path stays dependency-free."""
    import time
    import scryfall
    from enrich import color_shorthand, oracle_fields
    from tag_synergies import tags_for

    card, transient = None, False
    for params in ({"exact": name, "set": set_code.lower()} if set_code else {"exact": name},
                   {"fuzzy": name}):
        try:
            card = scryfall.named(params)
            break
        except scryfall.NotFound:
            continue  # this query didn't match — try the next (fuzzy) one
        except ScryfallUnavailable:
            transient = True  # outage; still try the remaining query in case it hits
            continue
        finally:
            time.sleep(0.1)
    if card is None:
        if transient:
            raise ScryfallUnavailable(f"could not reach Scryfall for {name!r}")
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
    """Build a wishlist row for one card, using the canonical (full) name from the
    pool/Scryfall so double-faced cards join cleanly with the rest of the tooling.

    Returns (row, status) where status is:
      'pool'     – enriched from card-pool.csv,
      'scryfall' – enriched via a live Scryfall lookup,
      'miss'     – Scryfall has no such card; row is name-only (check spelling),
      'error'    – Scryfall was UNREACHABLE; row is name-only, but the blanks are
                   transient (rerun to fill them), NOT a confirmed miss (F14)."""
    p = pool.get(name.lower())
    if p:
        data = {"Card Name": p.get("Card Name", name), "Type": p.get("Type", ""),
                "Card Text": p.get("Card Text", ""), "Color(s)": p.get("Color(s)", ""),
                "Synergies": p.get("Synergies", ""), "Rarity": p.get("Rarity", "")}
        status = "pool"
    else:
        try:
            s = _from_scryfall(name, set_code)
        except ScryfallUnavailable as e:
            eprint(f"WARN:  Scryfall unreachable while enriching {name!r} ({e}); "
                   "added with name only — rerun the add when Scryfall is reachable.")
            s, status = None, "error"
        else:
            status = "scryfall" if s is not None else "miss"
            if s is None:
                eprint(f"WARN:  no Scryfall match for {name!r} — added with name only.")
        if s is None:
            data = {"Card Name": name, "Type": "", "Card Text": "", "Color(s)": "",
                    "Synergies": "", "Rarity": ""}
        else:
            data = s
    data["Set Code"] = set_code
    data["Collector #"] = collector
    data.setdefault("Target", "")
    data.setdefault("Note", "")
    return data, status


def _try_seed_power(row, _warned=[]):
    """`_seed_power(row)`, or None if the seeding model is unavailable (warned once).

    `_seed_power` does `import deck`, and `cmd_add` called it in a bare loop AFTER the
    Scryfall fetches and BEFORE `write_wishlist` — so a broken deck.py threw away an
    entire enriched batch, the expensive part, over a cosmetic estimate (BS4-22). A blank
    Power is a recoverable state the tool already models (`cmd_seed_power` exists to fill
    exactly those cells); a lost batch is not. pool.py made `classify_roles` a lazy proxy
    for this same reason — this is that discipline on the write path."""
    try:
        return _seed_power(row)
    except Exception as e:
        if not _warned:
            _warned.append(True)
            eprint(f"WARN:  Power seeding unavailable ({type(e).__name__}: {e}) — rows are "
                   "being written with a BLANK Power. The batch is safe; fill the "
                   "estimates later with `wishlist.py --seed-power --write`.")
        return None


def cmd_add(path):
    if path == "-":
        text = sys.stdin.read()
    else:
        # A clean error, like query.py / pool.py / parse_matches all give. This was a bare
        # `open(...).read()`, so a mistyped filename dumped a FileNotFoundError traceback
        # (BS4-22) — and it leaked the handle besides.
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as e:
            eprint(f"Could not read {path!r}: {e}")
            return 1
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

    def _key(r):
        return ((r.get("Card Name") or "").strip().lower(),
                (r.get("Set Code") or "").strip().lower(),
                (r.get("Collector #") or "").strip().lower())
    by_key = {_key(r): r for r in existing}
    seen = set(by_key)

    added, dupes, owned_hits, reenriched = 0, 0, [], 0
    unenriched_miss, unenriched_err = [], []
    new_rows = []
    for name, setc, cn in entries:
        row, status = enrich(name, setc, cn, pool)
        key = (row["Card Name"].strip().lower(), setc.lower(), cn.lower())
        if key in seen:
            prev = by_key.get(key)
            # F20: a row added NAME-ONLY during a Scryfall outage (blank Type+Text) is
            # otherwise stuck — a re-add hits the dedupe and never enriches. If this
            # pass DID enrich it, backfill the blanks in place instead of counting a dupe.
            if prev is not None and status in ("pool", "scryfall") \
                    and not (prev.get("Type") or "").strip() \
                    and not (prev.get("Card Text") or "").strip():
                for col in ("Type", "Card Text", "Color(s)", "Synergies", "Rarity"):
                    if row.get(col):
                        prev[col] = row[col]
                # An outage-era row's Power was seeded from BLANK Type/Text/Rarity —
                # a flat 2.0, so a Mythic bomb ranked like filler Uncommon — and it
                # stuck: seeding below iterates new_rows only, and cmd_seed_power
                # fills only BLANK cells (broad-scan BS-17). Now that the data
                # arrived, recompute an UNTRUSTED power (seed/unknown/blank per
                # G-17's provenance rule); a hand grade is never touched.
                if power_is_seeded(prev):
                    est = _try_seed_power(prev)
                    if est is not None:
                        prev["Power"] = str(est)
                        prev["Power Source"] = POWER_SEEDED
                reenriched += 1
            else:
                dupes += 1
            continue
        if _owned_of(owned, row["Card Name"]) > 0:
            owned_hits.append(row["Card Name"])
        if status == "miss":
            unenriched_miss.append(row["Card Name"])
        elif status == "error":
            unenriched_err.append(row["Card Name"])
        existing.append(row)
        new_rows.append(row)
        seen.add(key)
        by_key[key] = row
        added += 1

    # Auto-seed a first-pass Power estimate for the newly-added rows so they don't
    # rank at 0.0 (which repeatedly buried real cards until hand-graded). It's an
    # ESTIMATE — the printed reminder says to hand-adjust bombs the heuristic misses.
    seeded = 0
    for row in new_rows:
        if not (row.get("Power") or "").strip():
            est = _try_seed_power(row)
            if est is None:
                break          # already warned; write the batch rather than lose it
            row["Power"] = str(est)
            row["Power Source"] = POWER_SEEDED
            seeded += 1

    write_wishlist(existing)
    print(f"Added {added} card(s) to the wishlist ({dupes} already listed). "
          f"Wishlist now has {len(existing)} card(s). Wrote {os.path.basename(WISHLIST_CSV)}.")
    if reenriched:
        print(f"Re-enriched {reenriched} previously name-only row(s) (added during an "
              "earlier Scryfall outage) now that their details resolved.")
    if seeded:
        print(f"Auto-seeded a heuristic Power estimate for {seeded} new card(s) — "
              "REVIEW and hand-adjust (the classifier undersells bombs); see `--rank`.")
    if owned_hits:
        print(f"NOTE: {len(owned_hits)} added card(s) you ALREADY OWN "
              f"(consider removing): {', '.join(owned_hits[:8])}"
              + ("…" if len(owned_hits) > 8 else ""))
    # A transient Scryfall outage must be called out distinctly from a genuine
    # not-found: these rows are name-only ONLY because Scryfall was down, and a
    # re-add (or build_pool.py) will fill them in — they aren't confirmed misses.
    if unenriched_err:
        print(f"WARN: {len(unenriched_err)} card(s) added NAME-ONLY because Scryfall "
              f"was unreachable — transient; re-add them (or run build_pool.py) to "
              f"enrich: {', '.join(unenriched_err[:8])}"
              + ("…" if len(unenriched_err) > 8 else ""))
    if unenriched_miss:
        print(f"NOTE: {len(unenriched_miss)} card(s) had no Scryfall match and were "
              f"added name-only (check spelling): {', '.join(unenriched_miss[:8])}"
              + ("…" if len(unenriched_miss) > 8 else ""))
    return 0


# --------------------------------------------------------------------------- #
# Query / summary
# --------------------------------------------------------------------------- #
def _match(card, args):
    def has(col, needle):
        return needle is None or needle.lower() in (card.get(col) or "").lower()
    if not (has("Card Name", args.name) and has("Type", args.type)
            and has("Card Text", args.text)
            and has("Synergies", args.synergy) and has("Set Code", args.set)
            and has("Target", args.target) and has("Note", args.note)):
        return False
    # Identity is SET-matched via lib.color_matches, never substring — "r" is in
    # "colorless", so the substring test matched every Colorless card (BS-10).
    if not color_matches(card.get("Color(s)"), args.color):
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
        if _owned_of(owned, c.get("Card Name")) > 0:
            continue  # already acquired — don't count toward crafting/packs (DFC-aware)
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


def _theme_model():
    """Build the deck theme model for target suggestion. Returns (fps, idf, spec_idf):

      fps  – [(deck_id, colors:set, central:set, tw_norm:dict)] — one entry per
             CORE archetype (variant builds / raw piles / pools are collapsed to
             their primary, and untuned placeholder lists are skipped) so breadth
             and idf count each real deck once, not once per alternate build.
      idf  – {theme: inverse-deck-frequency weight}. A theme CENTRAL to few decks
             (food, earthbend, firebending, Ninja, …) scores high; one central to
             most decks (etb, counters, tokens, mana, lifegain, …) scores ~0.

    idf-weighting is what stops broad decks from acting as catch-alls: a card that
    only overlaps a deck on generic themes gets a near-zero score and is flagged
    for review, while a specific-theme match (the real signal) ranks confidently.
    """
    import math
    import deck as dk
    meta = dk.load_card_meta()
    fps, df = [], {}
    for dd in dk.discover_decks():
        # One fingerprint per CORE archetype. Variants (alternate builds, raw
        # piles, pre-trim pools) share a core deck's themes, so counting them as
        # separate decks double-counts a theme's centrality (idf) and inflates a
        # card's cross-deck breadth (reuse) — e.g. a Bird card "reaching" 19, 19b
        # AND 19c. Skip variants (keep the primary) and skip any untuned list
        # (the 26-card example placeholder, an 83-card raw pile, an 86-card pool).
        if dd["variant"]:
            continue
        # Explicit roster membership (a `#: status: example` placeholder is not a deck),
        # sharing deck.py's predicate so the two agree on what the roster IS. The card-
        # count filter below still stands: it also catches untuned piles that carry no
        # status header.
        if not dk.is_roster_deck(dd):
            continue
        dm, cards = dk.parse_deck_file(dd["path"])
        # 60-card constructed OR 100-card singleton (Historic Brawl). The window used to
        # be 55-70 alone, which silently dropped any 100-card deck from the fingerprint
        # set — so cards targeted at one would rank "review"/generic while
        # `--audit-targets` still accepted its id as valid, two views disagreeing about
        # whether a deck exists. The roster has no 100-card deck yet and the handoff
        # names building one as a live plan, so this is a trap laid for the next session
        # rather than a live bug (BS4-23). The filter's real job is excluding untuned
        # PILES, which both bands still do.
        _total = sum(q for q, _n, _s, _c in cards)
        if not (55 <= _total <= 70 or 95 <= _total <= 105):
            continue
        colors, ident, tw = dk._declared_colors(dm), set(), {}
        for q, n, s, c in cards:
            if n.lower() in dk.BASICS:
                continue
            m = meta.get(n.lower())
            if not m:
                continue
            ident |= m["colors"]
            for t in m["synergies"]:
                tw[t] = tw.get(t, 0) + q
        central = dk._central_themes(tw)
        mx = max(tw.values()) if tw else 1
        fps.append((dd["id"], colors or ident, central, {t: tw[t] / mx for t in central}))
        for t in central:
            df[t] = df.get(t, 0) + 1
    n = len(fps)
    # Clamp at 0: a theme central to (almost) every deck yields log(n/(1+c)) <= 0,
    # and a *negative* weight would drag down the score of a card that also matches
    # a genuinely specific theme. Floor it so a generic theme is worth zero signal,
    # never negative (audit F15). Values above 0 are unchanged, so ranking output
    # only moves for the pathological central-to-all case.
    idf = {t: max(0.0, math.log(n / (1 + c))) for t, c in df.items()}
    # "specific" cutoff as a fraction of the pool (self-adjusts to deck count):
    # a theme central to <= SPECIFIC_MAX_FRAC of decks clears it.
    spec_idf = math.log(n / (1 + SPECIFIC_MAX_FRAC * n)) if n else 0.0
    return fps, idf, spec_idf


# A theme counts as "specific" (real signal, not a catch-all) when it is central to
# only a small SHARE of decks. Expressed as a FRACTION of the deck pool so the cutoff
# self-adjusts to the deck count — an absolute idf constant silently mis-calibrates when
# decks are added/removed: collapsing variants (34 -> 25 decks) once pushed the 5-deck
# "Villain" tribe below a hard 1.5 cutoff, mislabeling Doctor Doom & other Villain
# payoffs as "generic". 0.25 => central to <= ~1/4 of decks (<= ~6 of 25) is signal.
SPECIFIC_MAX_FRAC = 0.25

# Evergreen keywords / generic role descriptors are rare across decks (so they'd
# score as "specific") but are INCIDENTAL to a card — a trample creature isn't
# thereby a fit for the one deck that happens to run trample. Excluded from the
# confidence signal so they don't manufacture false-confident matches; a strategic
# theme (food, earthbend, reanimator, Ninja, spellslinger, …) still has to carry it.
NON_SIGNAL_TAGS = {
    "flying", "trample", "menace", "deathtouch", "lifelink", "vigilance", "haste",
    "reach", "first strike", "double strike", "ward", "hexproof", "shroud",
    "prowess", "defender", "indestructible", "protection", "intimidate", "fear",
    "evasion", "combat", "aggro", "tempo", "pump", "defense", "resilience",
}


def cmd_suggest_targets(rows, write=False, overwrite=False):
    """Propose a Target per card via idf-weighted theme fit + a confidence flag.

    STRONG/ok picks share a SPECIFIC (rare) theme with the deck; `review` picks
    match only generic themes (or nothing) — those are the catch-all-prone cards a
    human should judge from card text. With --write, fills STRONG/ok picks into
    blank Targets (or all, with --overwrite); `review` cards are always left for you.
    """
    fps, idf, spec_idf = _theme_model()
    strong = ok = review = wrote = 0
    print(f"  {'Card':30} {'Conf':6} {'Target':9} Signal")
    print("  " + "-" * 84)
    for r in rows:
        ccols = card_colors(r.get("Color(s)"))
        ctags = {t.strip() for t in (r.get("Synergies") or "").split(";") if t.strip()}
        fits = []
        for did, dcols, central, twn in fps:
            if not ccols.issubset(dcols):
                continue
            shared = ctags & central
            if not shared:
                continue
            score = sum(idf.get(t, 0) * twn[t] for t in shared)
            # `(-idf, tag)`, not `-idf` alone: `shared` is a SET, so a tie in idf left
            # the order to set iteration and the result changed between runs — Aura,
            # aura and enchant all score 3.1135, and the displayed `sig` flipped among
            # them on every build (PYTHONHASHSEED changes it too). That churned
            # dashboard.html's #data island on every rebuild for no real change, and let
            # the live ⟳ sync show different signals from the local snapshot. The tag
            # itself is a total order, so ties now break alphabetically and stably.
            specific = sorted((t for t in shared if idf.get(t, 0) >= spec_idf
                               and t.lower() not in NON_SIGNAL_TAGS),
                              key=lambda t: (-idf[t], t))
            fits.append((round(score, 2), did, specific, sorted(shared)))
        fits.sort(reverse=True)

        proposal = None
        if not fits:
            conf, tgt, sig = "review", "?", "no central-theme fit — general/concept?"
        else:
            best = fits[0]
            alts = ",".join(d for _, d, _, _ in fits[1:3])
            spec_best = next((f for f in fits if f[2]), None)
            if best[2]:  # shares a specific (rare) theme — real signal
                lead = len(fits) < 2 or best[0] >= fits[1][0] + 0.5
                conf = "STRONG" if (lead or best[0] >= 1.5) else "ok"
                tgt = proposal = best[1]
                sig = f"{'/'.join(best[2][:2])}  (score {best[0]}; alts {alts or '—'})"
            elif spec_best:
                # BS2-39: the top-scoring deck won on summed GENERIC overlap while a
                # lower-scoring deck shares a genuinely specific theme. The old path
                # printed `review` and proposed the GENERIC deck with a `?` — pointing
                # the human at the wrong home while the real one was never shown
                # (Splash Portal → 27 `blink`, Aloe Alchemist → 50 `cost-reduction`).
                # Propose the specific home at `ok` (it was not the top score), naming
                # both so the trade is visible.
                conf = "ok"
                tgt = proposal = spec_best[1]
                sig = (f"{'/'.join(spec_best[2][:2])}  (specific home; "
                       f"generic-top {best[1]})")
            else:  # only generic-theme overlap — the catch-all zone
                conf, tgt = "review", best[1] + "?"
                sig = f"only generic: {','.join(best[3][:3])}  (alts {alts or '—'})"

        strong += conf == "STRONG"; ok += conf == "ok"; review += conf == "review"
        if write and proposal and (overwrite or not (r.get("Target") or "").strip()):
            r["Target"] = proposal
            wrote += 1
        print(f"  {r['Card Name'][:30]:30} {conf:6} {str(tgt):9} {sig[:52]}")

    print(f"\n  {strong} strong · {ok} ok · {review} review "
          "(review = generic/no theme match — judge these from card text).")
    if write:
        write_wishlist(rows)
        print(f"  Wrote {wrote} target(s) to {os.path.basename(WISHLIST_CSV)} "
              f"(review cards left blank/unchanged).")
    else:
        print("  Read-only. Re-run with --write to fill blank Targets with strong/ok picks.")
    return 0


_WC_RANK = {"Mythic": 3, "Rare": 2, "Uncommon": 1, "Common": 0}


def _deck_colors_map():
    """deck_id(lower) -> declared color set, for land manabase scoring."""
    try:
        import deck as dk
        return {d["id"].lower(): card_colors(d["meta"].get("colors"))
                for d in dk.discover_decks()}
    except Exception as e:
        # Degrade (lands score neutral) but don't do it silently — a broken deck load
        # would quietly drop the land manabase axis from --rank (audit A14).
        eprint(f"WARN:  deck colors unavailable for land manabase scoring "
               f"({type(e).__name__}: {e}); lands will score neutral.")
        return {}


def _is_land(row):
    """FRONT-face land test, via `lib.primary_type` — a whole-type-line substring scan
    reads the BACK face's `// Land` (`lib.primary_type`'s own worked examples), so the
    three live God/door DFCs (Ojer Axonil / Ojer Kaslem / Matzalantli) took the
    manabase-value ranking branch: theme fit discarded, `fitN` replaced by a bogus
    "manabase" score for a creature, tier re-assigned from `land_val` — Ojer Axonil was
    bought at pick #6 of a live `--budget` as a phantom manabase upgrade, and
    Matzalantli moved a whole tier (broad-scan BS2-11). The front face is what a land
    drop can play, which is the only sense in which the wishlist ranks a "land"."""
    return primary_type(row.get("Type") or "") == "Land"


def _land_value(row, deck_colors):
    """0–10 MANABASE value of a land for its target deck (F03) — the theme-fit axis
    is meaningless for lands (no synergy tags), so score fixing instead: reward
    producing colors the deck actually runs (a WB dual in mono-W is half-dead),
    require the deck to span >=2 of the land's colors for a dual to matter, and
    prize untapped fixing. Colorless/utility or unknown-deck lands score neutral."""
    txt = (row.get("Card Text") or "")
    prod = card_colors(row.get("Color(s)"))
    # Only an ADD clause is color PRODUCTION: a bare `{W}` anywhere in the text
    # counted an ACTIVATION COST as fixing ("{W}: …" read as producing white),
    # inflating a land's manabase score (broad-scan batch 5).
    #
    # RESTRICTED production is tracked separately. A Village cycle land reads
    # "{T}: Add {B}. Spend this mana only to cast a creature spell." — that {B} is a real
    # black source for creatures and NOTHING for a removal spell, so scoring it as plain
    # fixing over-rates it. Mudflat Village ranked #1 of deck 52's land suggestions on
    # exactly this (G-37's live scoring miss). The restriction is detected PER LINE,
    # because that is how Magic prints it: the qualifying sentence follows the Add
    # sentence inside one ability, and the `[^.\n]*` clause scan deliberately stops at
    # the period before it.
    restricted_only = set()
    free = set()
    for line in txt.splitlines():
        limited = "spend this mana only" in line.lower()
        for m in re.finditer(r"[Aa]dd\b[^.\n]*", line):
            cols = {c for c in "WUBRG" if "{" + c + "}" in m.group(0)}
            prod |= cols
            (restricted_only if limited else free).update(cols)
    restricted_only -= free                       # a color also added freely is free
    if not prod or not deck_colors:
        return 3.5  # colorless/utility land, or no known target — neutral
    used = prod & deck_colors
    match = len(used) / len(prod)                 # fraction of its colors the deck uses
    multi = 1.0 if len(used) >= 2 else 0.5 if len(used) == 1 else 0.0
    base = 3.5 + 4.5 * match * multi              # ~3.5..8 by color usefulness
    if "enters tapped" not in txt.lower() and "enters the battlefield tapped" not in txt.lower():
        base += 1.5                               # untapped fixing is premium
    # Halve the fixing PREMIUM (never the 3.5 neutral floor) when every color this deck
    # wants from the land is restricted. Bounded and one-directional: it can only lower a
    # land, never raise one, so it cannot invent a recommendation. Half rather than zero
    # because the restriction is real but narrow — a creature-only source is close to full
    # value in a creature deck and near-dead in a spell deck, and `_land_value` is only
    # told the deck's COLORS, so the honest move is a modest discount plus the
    # `·restricted` marker `suggest --lands` now prints for the human to judge.
    if used and used <= restricted_only:
        base = 3.5 + (base - 3.5) * 0.5
    return round(min(10.0, base), 1)


def _deck_status():
    """deck_id(lower) -> (tier_letter, remaining_craft_count).

    remaining = distinct non-basic cards in the deck the collection doesn't own.
    Lets `--rank` show whether a card's target deck is BUILT (an upgrade to a deck
    you play — high value) or UNBUILT (a build project — lower value per wildcard),
    and surface cards that are the LAST few crafts finishing a near-complete deck.
    """
    try:
        import deck as dk
    except Exception as e:
        # Degrade (the --rank 'state' column blanks out) but surface it (audit A14).
        eprint(f"WARN:  deck build-state unavailable ({type(e).__name__}: {e}); "
               "the --rank 'state' column will be blank.")
        return {}
    _bk, _bn, by_name_qty = dk.load_collection()
    out = {}
    for d in dk.discover_decks():
        meta, cards = dk.parse_deck_file(d["path"])
        tier = dk._deck_tier(meta) or "·"
        need = set()
        for _qty, name, _s, _c in cards:
            cnt, in_lib = dk.owned(by_name_qty, name)
            if cnt == 0 and not in_lib and name.strip().lower() not in dk.BASICS:
                need.add(name.strip().lower())
        out[d["id"].lower()] = (tier, len(need))
    return out


def _status_label(target, status_map):
    """Compact 'built-state' tag for a card's target deck: '<tier>·<remaining>'.
    '★' marks a deck this card would help FINISH (<=3 crafts left). '—' for
    general/concept targets that aren't a single buildable deck."""
    first = ""
    for tok in re.split(r"[;,]", target or ""):
        tok = tok.strip().lower()
        if tok and tok not in ("—", "general") and not tok.startswith("concept"):
            first = tok
            break
    if not first or first not in status_map:
        return "—"
    tier, rem = status_map[first]
    star = "★" if 0 < rem <= 3 else ""
    return f"{tier}·{rem}{star}"


# Cross-deck reuse (breadth) as an explicit, BOUNDED contributor to the combined
# value-per-wildcard score: a craft that fits several of your decks is worth more per
# wildcard than a one-deck sidegrade ("craft this — it helps 4 decks"). Bounded so
# breadth NUDGES the ranking without ever overriding a real fit+power gap — the same
# discipline check_suggest applies to its co-signals. Guarded by check_rankings.
_REUSE_BONUS_W = 0.6      # per EXTRA deck the card fits (beyond the first)
_REUSE_BONUS_CAP = 1.8    # capped (~a 4-home card) — small next to the 0–10 fit+power blend


# A soon-to-rotate Standard card is a worse wildcard investment, so deprioritize it in
# the craft ranking — a BOUNDED nudge (it sinks WITHIN its tier, never crosses tiers,
# so a genuinely great rotating card is still visible, just lower). Guarded by
# check_rankings. Only fires for a Standard-legal set rotating this year/next (the same
# `rot` flag that prints ⚠rot).
_ROT_PENALTY = 1.25


def _reuse_bonus(reuse):
    """Bounded breadth bonus added to `combined`: 0 for a 0/1-home card, non-decreasing
    in `reuse`, capped at _REUSE_BONUS_CAP."""
    try:
        r = int(reuse)
    except (TypeError, ValueError):
        return 0.0
    return round(min(_REUSE_BONUS_CAP, _REUSE_BONUS_W * max(0, r - 1)), 2)


def _specific_themes_of(central, idf, spec_idf):
    """This model's notion of a deck's SPECIFIC (identity-carrying) themes: central
    themes that are rare enough across the roster (idf >= the self-calibrating
    `spec_idf` cutoff) and aren't evergreen keywords. Deliberately different from
    deck.py's denylist-based test — see `deck.cross_deck_breadth`."""
    return {t for t in central
            if idf.get(t, 0) >= spec_idf and t.lower() not in NON_SIGNAL_TAGS}


def _breadth_of(ccols, ctags, fps, idf, spec_idf):
    """Cross-deck breadth for one card, via the SHARED rule in deck.cross_deck_breadth
    (castable in the deck AND shares >=1 specific theme). Falls back to a local count
    only if deck.py can't be imported, so the column degrades rather than vanishing."""
    trimmed = [(did, dcols, _specific_themes_of(central, idf, spec_idf))
               for did, dcols, central, _twn in fps]
    try:
        import deck as dk
        return dk.cross_deck_breadth(ccols, ctags, trimmed)
    except Exception:
        return sum(1 for _d, dc, dt in trimmed if ccols <= dc and (ctags & dt))


def _rank_scores(rows, keep=None):
    """Score `rows`; if `keep` is given (a set of card names), score everything and
    return only those — so a FILTERED view is normalized against the whole wishlist.

    `fitN` is `pri` scaled to the maximum in the scored set, and `combined` blends it
    50/50 with a power that is NOT rescaled. Scoring only the filtered subset therefore
    inflates fit relative to power and can genuinely reorder the picks, so a
    `--budget --set TMT` plan would not agree with the same cards' places in the full
    `--rank`. The normalization denominator is a property of the CORPUS, not of the
    view someone happens to be looking through."""
    """Score every wishlist card for wildcard-spend priority. Reuses the idf theme
    model (so it stays consistent with --suggest-targets):

      fit    – idf-weighted theme fit to the card's best-matching deck (→ pri, fitN).
      reuse  – # decks the card is castable in AND shares a SPECIFIC (idf-signal)
               theme with — real cross-deck breadth, not generic overlap. A FIRST-CLASS
               axis: it adds a bounded `_reuse_bonus` directly to `combined`, so a
               multi-home craft outranks an equal fit+power one-deck sidegrade.
      pri    – the home-run single-deck fit (breadth now lives in combined, not here).

    Tiers: A = confident theme home (fit>=1.5 on a specific theme) OR breadth>=3;
    B = a specific-theme fit / castable-on-theme in >=1 deck; C = generic/none.
    """
    fps, idf, spec_idf = _theme_model()
    status_map = _deck_status()
    deck_colors = _deck_colors_map()
    # Rotation guard: join each craft target to the pool's Released date so a card whose
    # Standard-legal set rotates this year or next is flagged ⚠rot — don't spend a
    # wildcard on a card about to leave the format. Uses the shared deck.rotation_year
    # primitive; empty (no flags) when the pool lacks the Released column.
    pool_rot, _has_rel, _rot_soon_year = {}, False, None
    try:
        import deck as dk
        import datetime
        pool_rot, _has_rel = dk._pool_rotation_index()
        _rot_soon_year = datetime.date.today().year + 1
        if not _has_rel:
            # `_pool_rotation_index`'s docstring exists for exactly this: "callers
            # then warn instead of silently reporting nothing." This caller bound the
            # flag to an underscore and never read it, so a pool built before the
            # Released column made `--rank`/`--budget` print ZERO ⚠rot flags and say
            # nothing — which reads as "nothing on this plan is rotating", the precise
            # wrong answer G-19/G-30 exist to prevent (broad-scan BS2-38).
            eprint("WARN:  card-pool.csv has no Released column — rotation (⚠rot) "
                   "flags are OFF, not clear. Rebuild with build_pool.py --all.")
            _rot_soon_year = None
    except Exception as e:
        # Degrade, but never silently (audit A14 — the two sibling loaders above
        # already eprint on their own failures for the same reason).
        eprint(f"WARN:  rotation index unavailable ({e}) — ⚠rot flags are OFF, "
               "not clear.")
    out = []
    for r in rows:
        ccols = card_colors(r.get("Color(s)"))
        ctags = {t.strip() for t in (r.get("Synergies") or "").split(";") if t.strip()}
        best, best_specific, reuse = 0.0, [], 0
        best_spec_score, best_spec_list = 0.0, []
        for did, dcols, central, twn in fps:
            if not ccols.issubset(dcols):
                continue
            shared = ctags & central
            if not shared:
                continue
            # `(-idf, tag)`, not `-idf` alone: `shared` is a SET, so a tie in idf left
            # the order to set iteration and the result changed between runs — Aura,
            # aura and enchant all score 3.1135, and the displayed `sig` flipped among
            # them on every build (PYTHONHASHSEED changes it too). That churned
            # dashboard.html's #data island on every rebuild for no real change, and let
            # the live ⟳ sync show different signals from the local snapshot. The tag
            # itself is a total order, so ties now break alphabetically and stably.
            specific = sorted((t for t in shared if idf.get(t, 0) >= spec_idf
                               and t.lower() not in NON_SIGNAL_TAGS),
                              key=lambda t: (-idf[t], t))
            score = sum(idf.get(t, 0) * twn[t] for t in shared)
            if score > best:
                best, best_specific = score, specific
            # BS2-39: `specific` used to be retained only for the single highest-
            # SCORING deck — and generic themes are floored, not zeroed, so three
            # near-generic overlaps could outscore one genuinely specific theme.
            # The card then read `review`/"generic/no-theme" while a real specific
            # home existed (5 of 206 live rows: Splash Portal's blink home in deck
            # 27, Aloe Alchemist's cost-reduction home in 50, …). Track the best
            # SPECIFIC-theme deck separately so that signal survives.
            if specific and score > best_spec_score:
                best_spec_score, best_spec_list = score, specific
        # Breadth via the SHARED counting rule (deck.cross_deck_breadth), fed this
        # model's own idf-based notion of a specific theme. It used to be an inline
        # `reuse += 1` in the loop above — a second hand-written copy of the rule, which
        # is exactly how the two breadth signals drifted apart (broad-scan F-04).
        reuse = _breadth_of(ccols, ctags, fps, idf, spec_idf)
        if best_specific and best >= 1.5:
            conf = "STRONG"
        elif best_specific:
            conf = "ok"
        elif best_spec_list:
            # BS2-39 rescue: the top-scoring deck won on summed generic overlap, but
            # a lower-scoring deck shares a genuinely SPECIFIC theme — that is a real
            # home, not a "judge from text" case. Capped at `ok` (never STRONG: it was
            # not the top-scoring fit), and the sig shows the specific themes so the
            # reader sees why.
            conf = "ok"
            best_specific = best_spec_list
        else:
            conf = "review"
        # pri is the home-run single-deck fit; breadth is applied as a bounded bonus to
        # `combined` below (was `best + 0.6*(reuse-1)` — moved out so fit and breadth are
        # separate, legible axes and reuse can't be double-counted).
        pri = best
        tier = "A" if (conf == "STRONG" or reuse >= 3) else \
               "B" if (best_specific or reuse >= 1) else "C"
        raw_power = (r.get("Power") or "").strip()
        try:
            power = float(raw_power) if raw_power else 0.0
            bad_power = False
            # float() accepts "nan"/"inf"/"-inf" — a non-finite Power would escape the
            # bad-value flag and poison the `combined` score (nan scrambles the sort,
            # inf pins to the top), audit A10. Treat it like a non-numeric typo.
            # OUT-OF-RANGE is the same trap one notch subtler: the scale is 0–10, and
            # a large FINITE typo passes both guards and pins the rank — Pensive
            # Professor's cell read 78.0 and topped Tier A at combined 42.3
            # (broad-scan batch 6). Flag, score 0.0, tell the user to fix the cell.
            if not math.isfinite(power) or not (0.0 <= power <= 10.0):
                power, bad_power = 0.0, True
        except ValueError:
            # A non-numeric typo ("~9", "4,5", "TBD") must NOT silently score 0.0 and
            # sink a bomb without a flag (audit F9) — surface it like a blank cell.
            power = 0.0
            bad_power = True
        target = (r.get("Target") or "").strip() or "—"
        # F03: lands score on manabase value (not synergy themes), against the
        # target deck's colors. Resolve the first real deck id in the Target.
        land_val = None
        if _is_land(r):
            dcols = set()
            for tok in re.split(r"[;,]", target):
                t = tok.strip().lower()
                if t in deck_colors:
                    dcols = deck_colors[t]
                    break
            land_val = _land_value(r, dcols)
        # ⚠rot: flag a craft target whose Standard-legal set rotates this year or next.
        rot, rot_year = False, None
        if _rot_soon_year is not None:
            nm = (r.get("Card Name") or "").strip().lower()
            info = pool_rot.get(nm) or pool_rot.get(nm.split(" // ")[0])
            if info and "standard" in info[1]:
                # info = (released, legalities, set_code) — pass the set so an
                # announced long-legality reprint (Foundations) isn't false-flagged.
                rot_year = dk.rotation_year(info[0], set_code=info[2])
                rot = rot_year is not None and rot_year <= _rot_soon_year
        out.append({
            "name": r.get("Card Name", ""), "rarity": (r.get("Rarity") or "").capitalize(),
            "target": target,
            "conf": conf, "fit": round(best, 2), "reuse": reuse,
            "pri": round(pri, 2), "tier": tier, "power": round(power, 1),
            "state": _status_label(target, status_map),
            "blank_power": not raw_power,
            "bad_power": bad_power, "raw_power": raw_power,
            "land_val": land_val, "rot": rot, "rot_year": rot_year,
            # A conditional card's Power can't be estimated in isolation. Now that the
            # `Power Source` column records PROVENANCE, this fires only where the number
            # is still a heuristic SEED (or blank) — a hand grade on a conditional card
            # is precisely what the flag was asking for, so re-flagging it was noise.
            "cond_power": is_conditional_power(r)
                          and (power_is_seeded(r) or not raw_power),
            "uniq": card_distinctiveness(ctags, r.get("Card Text") or ""),
            "sig": "/".join(best_specific[:2]) or ("generic/no-theme" if conf == "review" else ""),
        })
    # Normalize fit (pri) to 0-10 and blend 50/50 with the hand-graded power
    # (already 0-10) into a combined value-per-wildcard score. fitN is exposed so
    # the artifact can re-blend live at any fit/power weight.
    mx = max((s["pri"] for s in out), default=0) or 1
    for s in out:
        if s.get("land_val") is not None:
            # F03: a land's "fit" IS its manabase value; blend land-heavy with any
            # hand-graded Power (usually blank for lands → land value carries it),
            # and re-tier from the land value so a well-matched untapped dual ranks
            # like a real upgrade instead of at a 0.0 theme-fit.
            s["fitN"] = s["land_val"]
            # `s["power"] or …` is the exact or-with-0 trap lib.card_power's comment
            # names: a land hand-graded Power 0 is a real judgment and `0 or x`
            # collapses it to "ungraded". Blank-ness is what raw_power records.
            pw = s["land_val"] if s["blank_power"] else s["power"]
            s["combined"] = round(0.65 * s["land_val"] + 0.35 * pw, 2)
            s["tier"] = "A" if s["land_val"] >= 7 else "B" if s["land_val"] >= 5 else "C"
            s["sig"] = "manabase (land)"
        else:
            s["fitN"] = round(s["pri"] / mx * 10, 2)
            # Breadth is a first-class, bounded term in the value-per-wildcard score: a
            # card that fits several decks outranks an equal fit+power one-deck sidegrade.
            s["combined"] = round(0.5 * s["fitN"] + 0.5 * s["power"]
                                  + _reuse_bonus(s["reuse"]), 2)
        # Rotation deprioritization: a bounded nudge so a soon-to-rotate Standard card
        # sinks within its tier (don't burn a wildcard on a card about to leave the format).
        if s.get("rot"):
            s["combined"] = round(max(0.0, s["combined"] - _ROT_PENALTY), 2)
    # ONE entry per card NAME, keeping the best-`combined` row: the wishlist
    # legitimately holds one row per (name, set) — Drakuseth and Sally Pride are
    # live duplicates — and scoring ROWS made a duplicated card rank twice, so a
    # 3-slot `--budget` could silently be a 2-card plan spending two wildcard
    # slots on one card (broad-scan batch 5). A wildcard crafts the CARD, not a
    # printing, so the spend views must be name-unique.
    best = {}
    for s in out:
        cur = best.get(s["name"])
        if cur is None or s["combined"] > cur["combined"]:
            best[s["name"]] = s
    out = list(best.values())
    order = {"A": 0, "B": 1, "C": 2}
    out.sort(key=lambda s: (order[s["tier"]], -s["pri"], -_WC_RANK.get(s["rarity"], 0), s["name"]))
    if keep is not None:
        out = [s for s in out if s["name"] in keep]   # filter AFTER normalizing
    return out


def cmd_rank(rows, all_rows=None):
    """Rank the wishlist by wildcard-spend priority — theme fit + hand-graded power
    blended into a `combined` score — grouped by recommendation tier."""
    # Exclude cards already crafted — the wishlist keeps them until pruned, but a
    # craft PLAN must not tell you to spend a wildcard on a card you own (audit F19).
    owned = owned_index()
    unowned = [r for r in rows if not _owned_of(owned, r.get("Card Name"))]
    owned_skipped = len(rows) - len(unowned)
    # Normalize against the WHOLE wishlist even when the view is filtered (see
    # `_rank_scores`) — otherwise a --set/--rarity view rescales fit against its own
    # subset and can reorder picks relative to the full ranking.
    norm = [r for r in (all_rows or rows) if not _owned_of(owned, r.get("Card Name"))]
    scored = _rank_scores(norm, keep={r.get("Card Name") for r in unowned})
    order = {"A": 0, "B": 1, "C": 2}
    scored.sort(key=lambda s: (order.get(s["tier"], 9), -s["combined"], s["name"]))
    labels = {"A": "TIER A — craft first (confident theme home and/or real cross-deck breadth)",
              "B": "TIER B — solid targeted upgrade (one clear deck)",
              "C": "TIER C — situational / build-around (niche; craft when you build that deck)"}
    cur = None
    for s in scored:
        if s["tier"] != cur:
            cur = s["tier"]
            n = sum(1 for x in scored if x["tier"] == cur)
            print(f"\n{labels[cur]}  ({n} cards)")
            print(f"  {'#':>3} {'Card':28} {'WC':3} {'Deck':6} {'state':6} {'fit':>4} "
                  f"{'pow':>4} {'uq':>3} {'use':>3} {'comb':>5}  signal")
            print("  " + "-" * 102)
            i = 0
        i += 1
        wc = (s["rarity"] or "?")[:1] or "?"
        pw = f"{s['power']:>4.1f}" + ("?" if s["blank_power"] else "!" if s["bad_power"]
                                      else "~" if s.get("cond_power") else " ")
        use = f"{s['reuse']}★" if s["reuse"] >= 3 else str(s["reuse"])
        sig = s["sig"][:22] + (f"  ⚠rot~{s['rot_year']}" if s.get("rot") else "")
        print(f"  {i:>3} {s['name'][:28]:28} {wc:3} {s['target']:6} {s['state']:6} "
              f"{s['fitN']:>4.1f} {pw} {s['uniq']:>3.0f} {use:>3} {s['combined']:>5.1f}  {sig}")
    print("\n" + "=" * 60)
    print("Wildcard cost by tier (you spend that rarity's wildcards):")
    for t in ("A", "B", "C"):
        by = {}
        for s in scored:
            if s["tier"] == t:
                by[s["rarity"]] = by.get(s["rarity"], 0) + 1
        line = ", ".join(f"{by[k]} {k}" for k in ("Mythic", "Rare", "Uncommon", "Common") if by.get(k))
        print(f"  Tier {t}: {line}")
    blanks = [s["name"] for s in scored if s["blank_power"]]
    print("\ncomb = 50/50 blend of theme fit (fit, 0–10) and hand-graded power (pow), "
          "plus a bounded breadth bonus. uq = ability-distinctiveness (0–10): how rare "
          "this card's ABILITIES are across the pool — ~0 is generic templating (etb/"
          "tokens/sacrifice, the overlap that trips broad synergy checks), high is a "
          "distinctive mechanic. Diagnostic here (it does not feed comb); a low uq on a "
          "'review' card confirms filler, a high uq says the tags under-read it — grade "
          "from text. use = cross-deck reuse: # of your decks the card "
          "is castable in AND shares a central theme with (★ = fits ≥3 — craft once, play "
          "everywhere; copies are fungible). state = target deck's tier·remaining-crafts "
          "(★ = this card helps FINISH a near-complete deck; '—' = general/concept). A "
          "high-value wildcard upgrades a BUILT deck (low remaining) — a big remaining "
          "count is a build PROJECT.")
    if blanks:
        print(f"⚠ {len(blanks)} card(s) have BLANK Power (shown as 'pow?', ranked low until "
              f"graded): {', '.join(blanks[:8])}{' …' if len(blanks) > 8 else ''}. "
              "Run `--seed-power --write` then hand-adjust the bombs.")
    cond = [s["name"] for s in scored if s.get("cond_power")]
    if cond:
        print(f"~ {len(cond)} card(s) have a CONDITIONAL power (X-cost / kicker / landfall / "
              f"'equal to …'), shown as 'pow~'. The heuristic grades a card in ISOLATION, so "
              f"it structurally can't price one that scales with YOUR deck — and the CSV "
              f"their Power is not a recorded hand grade (`Power Source` is seed/unknown). "
              f"Verify from full text and hand-grade, then set Power Source=hand: " + ", ".join(cond[:6]) + ("…" if len(cond) > 6 else ""))
    bad = [(s["name"], s["raw_power"]) for s in scored if s["bad_power"]]
    if bad:
        # A malformed Power scored 0.0 and would otherwise sink silently (F9).
        print(f"⚠ {len(bad)} card(s) have a NON-NUMERIC or OUT-OF-RANGE Power "
              f"(shown as 'pow!', scored 0.0): "
              f"{', '.join(f'{n} ({v!r})' for n, v in bad[:6])}"
              f"{' …' if len(bad) > 6 else ''}. Fix the cell to a 1–10 number.")
    rot = [s for s in scored if s.get("rot")]
    if rot:
        # A wildcard on a card leaving Standard this year/next is poor value.
        names = ", ".join(f"{s['name']} (~{s['rot_year']})" for s in rot[:6])
        print(f"⚠ {len(rot)} craft target(s) are on a set ROTATING soon (⚠rot~YEAR) — a "
              f"wildcard there won't last: {names}"
              f"{' …' if len(rot) > 6 else ''}. Verify against the official schedule (a "
              "reprint can read early).")
    if owned_skipped:
        print(f"({owned_skipped} already-owned card(s) excluded from the ranking — "
              "prune them with `--owned` / reconcile_crafts.py.)")
    print("For an optimal craft plan within your wildcards use "
          '`--budget "9M 10R 38U 48C"`.')
    return 0


_RARITY_LETTER = {"M": "Mythic", "R": "Rare", "U": "Uncommon", "C": "Common"}


def _parse_budget(s):
    """'9M 10R 38U 48C' (any order/spacing, case-insensitive) -> {rarity: count}."""
    caps = {}
    for num, let in re.findall(r"(\d+)\s*([MmRrUuCc])", s or ""):
        caps[_RARITY_LETTER[let.upper()]] = caps.get(_RARITY_LETTER[let.upper()], 0) + int(num)
    return caps


def cmd_budget(rows, budget_str, all_rows=None):
    """Given a wildcard budget ('9M 10R 38U 48C'), pick the highest-`combined`
    cards affordable within each rarity's cap (it's separable per rarity, so the
    top-K-by-combined per rarity IS optimal), with 1-2 alternates each and an
    Arena import block of the picks."""
    caps = _parse_budget(budget_str)
    if not caps:
        eprint('Could not parse budget. Example: --budget "9M 10R 38U 48C"')
        return 1
    # Don't spend the budget on cards already owned (audit F19).
    owned = owned_index()
    rows = [r for r in rows if not _owned_of(owned, r.get("Card Name"))]
    norm = [r for r in (all_rows or rows) if not _owned_of(owned, r.get("Card Name"))]
    scored = _rank_scores(norm, keep={r.get("Card Name") for r in rows})
    by_rar = {}
    for s in scored:
        by_rar.setdefault(s["rarity"], []).append(s)
    for r in by_rar:
        by_rar[r].sort(key=lambda s: (-s["combined"], s["name"]))

    print(f"Wildcard-spend plan for budget: "
          + ", ".join(f"{caps[r]} {r}" for r in ("Mythic", "Rare", "Uncommon", "Common") if caps.get(r)))
    print("(picks = highest combined fit+power within each cap; alts = next best)\n")

    # G-19: "`--budget` must show every check `--rank` runs." The rotation half was
    # fixed first; the three Power-PROVENANCE flags (`pow?` blank, `pow!` malformed,
    # `pow~` conditional-and-unhand-graded) were still computed by _rank_scores and
    # DISCARDED here — so a card whose confident-looking number is a seed, a blank, or
    # structurally unpriceable could be picked into the plan with no "verify from
    # text" marker, on the one view that spends real wildcards (broad-scan BS2-37).
    def _pow_mark(s):
        return (" pow!" if s.get("bad_power") else
                " pow?" if s.get("blank_power") else
                " pow~" if s.get("cond_power") else "")

    rotating, flagged_pow = [], []
    for rar in ("Mythic", "Rare", "Uncommon", "Common"):
        cap = caps.get(rar, 0)
        if not cap:
            continue
        pool = by_rar.get(rar, [])
        picks, alts = pool[:cap], pool[cap:cap + 2]
        print(f"=== {rar}  ({len(picks)} pick(s) of {cap} WC"
              + (f"; {cap - len(picks)} WC left over — wishlist has no more {rar}s)" if len(picks) < cap else ")"))
        for s in picks:
            # ⚠rot on the SPEND view, not just on `--rank`. This is the command that
            # says "craft these", so it is the one place the warning has to appear —
            # it was computing `rot` in _rank_scores and discarding it, and a 3-slot
            # uncommon budget came back with 2 cards leaving Standard.
            flag = f"  ⚠rot~{s['rot_year']}" if s.get("rot") else ""
            if s.get("rot"):
                rotating.append((s["name"], s["rot_year"], rar))
            mark = _pow_mark(s)
            if mark:
                flagged_pow.append((s["name"], mark.strip()))
            print(f"   {s['combined']:>4.1f}  {s['name'][:34]:34} "
                  f"deck {s['target']:6}  (fit {s['fitN']:.1f} / pow {s['power']:.1f}{mark}){flag}")
        for s in alts:
            print(f"    alt {s['combined']:>3.1f}  {s['name'][:32]:32} deck {s['target']}"
                  + _pow_mark(s)
                  + (f"  ⚠rot~{s['rot_year']}" if s.get("rot") else ""))
        print()
    if flagged_pow:
        print(f"⚠ {len(flagged_pow)} pick(s) carry an UNTRUSTED Power number — "
              + "; ".join(f"{n} ({m})" for n, m in flagged_pow[:6])
              + (" …" if len(flagged_pow) > 6 else "") + ".")
        print("  pow? = blank (ranked on fit alone) · pow! = non-numeric/out-of-range "
              "(scored 0.0 — fix the cell) · pow~ = conditional and not hand-graded "
              "(the seed structurally can't price it). Verify from full text before "
              "spending; hand-grade and set Power Source=hand.\n")
    if rotating:
        print(f"⚠ {len(rotating)} of the picks sit on a set ROTATING soon — a wildcard "
              f"there won't last: "
              + "; ".join(f"{n} (~{y}, {r})" for n, y, r in rotating[:4])
              + (" …" if len(rotating) > 4 else ""))
        print(f"  These already carry the bounded -{_ROT_PENALTY} `combined` "
              f"deprioritization and STILL rank top of their rarity, so the pick is "
              f"defensible on value — but verify against the official rotation "
              f"schedule before spending (a reprint can read early).\n")

    # Arena import block of the picks (front/full name is what the wishlist stores).
    wl_by = {(r.get("Card Name") or ""): r for r in rows}
    print("Import block (recommended crafts):\n```")
    print("Deck")
    for rar in ("Mythic", "Rare", "Uncommon", "Common"):
        for s in by_rar.get(rar, [])[:caps.get(rar, 0)]:
            r = wl_by.get(s["name"], {})
            setc, coll = r.get("Set Code", ""), r.get("Collector #", "")
            print(f"1 {s['name']}" + (f" ({setc}) {coll}" if setc else ""))
    print("```")
    return 0


# Heuristic power SEED (a first pass for blank Power cells — NOT authoritative;
# the role classifier underrates bombs whose value is unique text, so treat the
# number as an estimate to hand-adjust). Rarity is the objective floor.
_SEED_RARITY = {"Mythic": 4.5, "Rare": 3.2, "Uncommon": 2.0, "Common": 1.0}
_SEED_ROLE = {"Sweeper": 2.0, "Reanimation": 1.6, "Cost reduction / cheat": 1.6,
              "Payoff / engine": 1.5, "Card advantage": 1.3, "Removal (spot)": 1.1,
              "Burn / drain": 1.1, "Counter": 0.8, "Recursion": 0.7, "Ramp / fixing": 0.6,
              "Team pump / anthem": 0.6, "Protection / trick": 0.4, "Lifegain": 0.3}
# Two bounded bonuses that correct the seed's biggest under-reads (the Meteor-Sword miss):
_SEED_FLEX_REMOVAL = 0.8   # removal that answers MORE than creatures (any permanent / pw)
_SEED_PERMANENT_VALUE = 0.6  # an impact effect STAPLED to a permanent — a 2-for-1 vs a spell
_FLEX_REMOVAL_RE = re.compile(
    r"(destroy|exile) (target |up to \w+ target |all )?"
    r"(nonland permanent|permanent|creature or planeswalker|planeswalker|"
    r"artifact or enchantment|enchantment or artifact|artifact, creature, or enchantment)",
    re.I)
# Impact roles worth a 2-for-1 bump when they ride on a permanent (not a one-shot spell).
_IMPACT_SEED_ROLES = {"Removal (spot)", "Sweeper", "Card advantage", "Payoff / engine",
                      "Reanimation", "Cost reduction / cheat"}

# Rarity reaches this seed in TWO shapes across the toolkit: the pool/wishlist store the
# WORD ("Mythic"), while `deck.load_rarities()` maps a card to its Arena WILDCARD LETTER
# ("M") — and that is the shape `deck.rank_cut_candidates` / `deck._card_power` hand us.
# A bare letter fell through `.capitalize()` to the 2.0 default, so EVERY rare and mythic
# seeded as an uncommon: the cuts power co-signal was pinned negative for exactly the
# bombs it exists to protect, and `cuts` tagged them "on-theme but low power" (audit F-01).
# Normalize both shapes here, at the single consumer, so no caller can get it wrong.
_RARITY_FROM_LETTER = {"M": "Mythic", "R": "Rare", "U": "Uncommon", "C": "Common"}


def _norm_rarity(value):
    """Canonical rarity WORD from either a word ('mythic', 'Rare') or an Arena wildcard
    LETTER ('M', 'r'). Returns '' when it is neither — an unresolved '?' or a blank cell —
    which the caller turns into the neutral default floor rather than a wrong one."""
    s = (value or "").strip()
    if not s:
        return ""
    if len(s) == 1:
        return _RARITY_FROM_LETTER.get(s.upper(), "")
    w = s.capitalize()
    return w if w in _SEED_RARITY else ""


# Cards whose power is CONDITIONAL ON THE DECK, so a single number is the wrong shape of
# answer. The seed grades a card in isolation; these scale with something it can't see —
# your board, your land drops, your mana, your greatest creature. Every miss this session
# was one of these: Repulsive Mutation seeded near-zero (its counter is unconditional
# once the threat is big), Mona Lisa at 2.5 (a 3-mana rock that taps for 3), Procrastinate
# at 1.0 (twice-X stun counters locks a creature for four untaps), Genesis Wave and The
# Legend of Kyoshi both scale off the board.
#
# The fix is NOT a better number — a synergy/rarity model structurally cannot price these.
# It's to say so, so the reader grades from text instead of trusting a confident 2.0.
_CONDITIONAL_POWER_RE = re.compile(
    r"\{x\}"
    r"|\bkicker\b|\bexhaust\b|\bwarp\b|\blandfall\b"
    r"|equal to (?:the )?(?:number|greatest|its|that|twice)"
    r"|for each \w+ you control"
    r"|where x is",
    re.I)


def is_conditional_power(row, _mana={}):
    """True when a card's power depends on the DECK it's in (X-cost, kicker, landfall,
    'equal to …', 'for each … you control'), so its heuristic Power is a placeholder to
    grade from text rather than a usable estimate.

    The mana COST is joined from card-mana.csv (`deck.load_mana`, full-pool scope per
    G-18): wishlist rows carry NO `Mana Cost` column, so the old `row.get('Mana Cost')`
    read was always '' and the `\\{x\\}` alternative — written for the cost — was dead
    for the flag's whole life. Genesis Wave `{X}{G}{G}{G}`, named in this very block's
    own design comment as a card the mechanism exists to catch, was unflagged
    (broad-scan BS2-07-adjacent, batch B). Cached once per process; a missing mana
    file degrades to the text-only read, which is the old behavior."""
    if not _mana:
        try:
            import deck as dk
            _mana.update(dk.load_mana() or {"": None})
        except Exception:
            _mana[""] = None
    nl = (row.get("Card Name") or "").strip().lower()
    entry = _mana.get(nl) or _mana.get(nl.split(" // ")[0])
    cost = entry[0] if entry else ""
    blob = f"{row.get('Card Text') or ''}\n{cost}"
    return bool(_CONDITIONAL_POWER_RE.search(blob))


def _seed_power(r):
    """Heuristic 0–10 power for a wishlist card (rarity floor + functional roles + a few
    bounded bombs the role map can't see). REVIEW it — it undersells unique bombs; this
    just gets a fresh card off a 0.0 blank. The two extra bonuses credit what the flat
    role map missed: FLEXIBLE removal (destroy any permanent, not just a creature) and an
    impact effect on a PERMANENT (a body/equipment that also removes is a 2-for-1).

    `Rarity` may be a word OR an Arena wildcard letter — see `_norm_rarity` (audit F-01)."""
    import deck as dk
    text = r.get("Card Text") or ""
    # FRONT face only (G-63, batch B): the merged `A // B` type line made a DFC whose
    # BACK is an Instant/Sorcery fail the permanent-value gate below — Decadent
    # Dragon // Expensive Taste seeded 4.5 against a correct 5.5, and the wrong
    # number was live in the CSV as `Power Source: seed`. The mirror hazard is a
    # back-face Planeswalker granting the +2.0.
    ty = (r.get("Type") or "").split("//")[0].lower()
    roles = set(dk.classify_roles(text))
    p = _SEED_RARITY.get(_norm_rarity(r.get("Rarity")), 2.0)
    p += sum(_SEED_ROLE.get(x, 0) for x in roles)
    if "planeswalker" in ty:
        p += 2.0
    if "legendary" in ty:
        p += 0.3
    if _FLEX_REMOVAL_RE.search(text):
        p += _SEED_FLEX_REMOVAL
    # A permanent = anything that isn't a one-shot instant/sorcery. An impact effect that
    # stays on the board (equipment/creature/artifact/enchantment) beats the same effect
    # as a spell — Meteor Sword ("destroy target permanent" on a +3/+3 equipment) is the
    # canonical miss the flat Removal(1.1) credit under-read.
    if not any(k in ty for k in ("instant", "sorcery")) and (roles & _IMPACT_SEED_ROLES):
        p += _SEED_PERMANENT_VALUE
    return min(10.0, round(p * 2) / 2)  # nearest 0.5


def cmd_seed_power(rows, write=False):
    """Fill BLANK Power cells with a heuristic first-pass estimate (rarity floor +
    functional-role signals). Never touches a Power you've already graded. It's an
    ESTIMATE to review — the classifier can't see a bomb's unique text."""
    blanks = [r for r in rows if not (r.get("Power") or "").strip()]
    if not blanks:
        print("Every wishlist card already has a Power grade — nothing to seed.")
        return 0
    print(f"Heuristic Power seed for {len(blanks)} blank cell(s) "
          "(estimate — review & adjust):\n")
    print(f"  {'seed':>4}  {'WC':3} Card")
    for r in sorted(blanks, key=lambda r: -_seed_power(r)):
        est = _seed_power(r)
        if write:
            r["Power"] = str(est)
            r["Power Source"] = POWER_SEEDED
        wc = (r.get("Rarity") or "?")[:1]
        print(f"  {est:>4.1f}  {wc:3} {r.get('Card Name', '')[:44]}")
    if write:
        write_wishlist(rows)
        print(f"\nWrote {len(blanks)} Power estimate(s) to {os.path.basename(WISHLIST_CSV)}. "
              "Review and hand-adjust the bombs the heuristic undersells.")
    else:
        print("\nRead-only. Re-run with --write to fill the blank Power cells.")
    return 0


def print_table(hits, owned):
    cols = ["Have", "Card Name", "Type", "Color(s)", "Set", "Rarity", "Target"]
    def have_of(c):
        return "own" if _owned_of(owned, c.get("Card Name")) > 0 else ""
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


def _pips_castable(strict, hybrid, deck_colors):
    """True if a cost with these STRICT color pips (dict color->count) and HYBRID pips
    (list of color-sets) is castable by a deck producing `deck_colors` — every strict
    color must be in the deck, and each hybrid pip is payable with EITHER of its colors.
    Pure/deterministic (unit-tested); the hybrid-aware core of the target audit so a
    {W/U} card isn't flagged 'off-color' in a mono-W deck (matches deck castability)."""
    if not set(strict).issubset(deck_colors):
        return False
    return all((set(h) & set(deck_colors)) for h in hybrid)


def _audit_target_issues(color_only=False):
    """Return [(severity, card, message)] for wishlist-target problems, checked
    against the CURRENT decks: 'color' = the target deck can't cast the card (the
    drift you get when a deck changes colors, e.g. 14 Mardu->Rakdos orphaned Neriv);
    'target' = an unknown deck id; 'power' = a blank Power cell. With color_only,
    returns just the castability/target-drift issues (for check_all's soft pass).

    RAISES `TargetAuditUnavailable` if the deck roster can't be loaded. It used to
    `except Exception: pass`, which left `deck_ids` and `mana` empty — and every check
    below is gated on those being non-empty, so the function returned `[]` and
    `cmd_audit_targets` printed "Wishlist targets are clean: every target deck can cast
    its card" having checked nothing. Worse on the automated path: `check_all`'s soft
    sweep has its own try/except that would have reported a skip, but the exception was
    swallowed one level down, so the gate saw an empty list rather than a failure and the
    roster sweep became an invisible no-op (BS4-08). Every sibling loader in this file
    eprints on this exact failure (audit A14); this was the one that didn't."""
    rows = load_wishlist()
    issues = []
    deck_cols, deck_ids = {}, set()
    dk = None
    mana = {}
    try:
        import deck as dk
        for d in dk.discover_decks():
            deck_ids.add(d["id"].lower())
            deck_cols[d["id"].lower()] = card_colors(d["meta"].get("colors"))
        mana = dk.load_mana()
    except Exception as e:
        raise TargetAuditUnavailable(
            f"the deck roster could not be loaded ({type(e).__name__}: {e}), so wishlist "
            "targets cannot be checked against it — this is a SKIP, not a clean bill") from e

    def _castable_in(name, ident, dc):
        """Can a deck of colors `dc` cast this card? Hybrid-aware: a hybrid pip is
        payable with EITHER of its colors, so identity over-states the requirement
        (a {W/U} card is castable in a mono-W deck). Use the mana cost's STRICT pips
        + per-hybrid 'any of these colors' when a cost is on file; fall back to the
        identity-subset test otherwise. Mirrors deck.py's castability logic so the
        audit doesn't flag a hybrid the deck itself plays fine (e.g. Sun-Spider
        {3}{W/U} in a W/B deck)."""
        entry = mana.get(name.lower()) if mana else None
        if dk is not None and entry and entry[0]:
            strict, hybrid = dk.parse_pips(entry[0])
            return _pips_castable(strict, hybrid, dc)
        return ident.issubset(dc)          # no cost data -> identity fallback

    for r in rows:
        name = (r.get("Card Name") or "").strip()
        if not color_only and not (r.get("Power") or "").strip():
            issues.append(("power", name, "blank Power (ranks low until graded)"))
        ident = card_colors(r.get("Color(s)"))
        for tok in re.split(r"[;,]", (r.get("Target") or "")):
            tok = tok.strip().lower()
            if not tok or tok in ("—", "general") or tok.startswith("concept"):
                continue
            if deck_ids and tok not in deck_ids:
                issues.append(("target", name, f"target '{tok}' is not a known deck id"))
                continue
            dc = deck_cols.get(tok)
            if dc and ident and not _castable_in(name, ident, dc):
                issues.append(("color", name, f"identity {''.join(sorted(ident)) or 'C'} "
                               f"can't be cast in deck {tok} ({''.join(sorted(dc)) or 'C'})"))
    return issues


def cmd_audit_targets(_rows):
    """Audit wishlist Targets against the current decks: flag cards whose target
    deck can't cast them (color/theme drift after a retune) and blank Power cells."""
    try:
        issues = _audit_target_issues()
    except TargetAuditUnavailable as e:
        # Non-zero: an audit that could not run must not read as a pass.
        eprint(f"Wishlist target audit SKIPPED — {e}")
        return 1
    if not issues:
        print("Wishlist targets are clean: every target deck can cast its card, "
              "and every card has a Power grade.")
        return 0
    groups = {}
    for sev, name, msg in issues:
        groups.setdefault(sev, []).append((name, msg))
    for sev, label in [("color", "OFF-COLOR — target deck can't cast this (re-home the Target)"),
                       ("target", "UNKNOWN TARGET — deck id not found"),
                       ("power", "BLANK POWER — ranks low until graded")]:
        g = groups.get(sev)
        if not g:
            continue
        print(f"\n{label}  ({len(g)})")
        for name, msg in g:
            print(f"  {name[:32]:32} {msg}")
    print(f"\n{len(issues)} issue(s). Re-home color/target drift by editing the Target; "
          "fill blank Power with `--seed-power --write`, then hand-adjust bombs.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Manage the craft-target / wishlist.")
    ap.add_argument("--add", metavar="FILE",
                    help="append an Arena-export batch (or '-' for stdin), enriching each card")
    ap.add_argument("--by-set", action="store_true",
                    help="summarize unowned wishlist cards per set (pack optimization)")
    ap.add_argument("--suggest-targets", action="store_true",
                    help="propose a Target per card (idf-weighted theme fit + confidence); "
                         "review flags are cards to judge from card text")
    ap.add_argument("--write", action="store_true",
                    help="with --suggest-targets: write strong/ok picks into blank Targets")
    ap.add_argument("--overwrite", action="store_true",
                    help="with --suggest-targets --write: also overwrite existing Targets")
    ap.add_argument("--rank", action="store_true",
                    help="rank cards by wildcard-spend priority (theme fit + hand-graded "
                         "power, blended), grouped by recommendation tier")
    ap.add_argument("--budget", metavar="SPEC",
                    help='optimal craft plan within a wildcard budget, e.g. '
                         '"9M 10R 38U 48C" (picks highest combined score per rarity cap)')
    ap.add_argument("--seed-power", dest="seed_power", action="store_true",
                    help="first-pass heuristic estimate for BLANK Power cells "
                         "(add --write to persist; review — it's an estimate)")
    ap.add_argument("--audit-targets", dest="audit_targets", action="store_true",
                    help="flag wishlist cards whose target deck can't cast them "
                         "(color/theme drift after a retune) or have blank Power")
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

    # The filter flags used to apply ONLY to the default browse, so `--budget "3R"
    # --set TMT` silently planned against the whole wishlist and returned FIN cards.
    # A flag the user passed must never be quietly dropped — that is a plan they
    # believe is scoped. `_match` is a no-op when no filter is given, so unfiltered
    # invocations are unchanged. The MAINTENANCE commands below (suggest-targets,
    # audit-targets, seed-power) deliberately keep the FULL list: they exist to find
    # gaps across everything, and auditing a filtered subset would report "clean"
    # while leaving the rest unchecked.
    planning = [c for c in rows if _match(c, args)]
    if planning != rows and (args.rank or args.budget or args.by_set):
        eprint(f"(filtered: {len(planning)} of {len(rows)} wishlist cards)")

    if args.by_set:
        return cmd_by_set(planning, owned)
    if args.suggest_targets:
        return cmd_suggest_targets(rows, write=args.write, overwrite=args.overwrite)
    if args.rank:
        return cmd_rank(planning, all_rows=rows)
    if args.audit_targets:
        return cmd_audit_targets(rows)
    if args.budget:
        return cmd_budget(planning, args.budget, all_rows=rows)
    if args.seed_power:
        return cmd_seed_power(rows, write=args.write)

    hits = planning
    if args.owned:
        hits = [c for c in hits if _owned_of(owned, c.get("Card Name")) > 0]

    if args.count:
        print(len(hits))
        return 0
    if not hits:
        eprint("No wishlist cards matched.")
        return 0

    print_table(hits, owned)
    still = sum(1 for c in hits
                if _owned_of(owned, c.get("Card Name")) == 0)
    from collections import Counter
    by_r = Counter((c.get("Rarity") or "?").capitalize() for c in hits
                   if _owned_of(owned, c.get("Card Name")) == 0)
    tail = ", ".join(f"{by_r[x]} {x}" for x in ("Mythic", "Rare", "Uncommon", "Common", "?")
                     if by_r[x])
    print(f"\n{len(hits)} card(s) — {still} to craft" + (f" ({tail})" if tail else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
