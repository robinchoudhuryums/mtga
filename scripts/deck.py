#!/usr/bin/env python3
"""Manage constructed decks and their variations against your collection.

Decks live under decks/ as one folder per core deck, with variants as sibling
files:

    decks/
      01-avatar-tempo/
        deck.txt              # the base deck   -> id "1"
        1a-counter-heavy.txt  # a variation     -> id "1a"
        1b-aggro-splash.txt   # another         -> id "1b"
        notes.md              # optional free-form notes

Each deck file is a full, self-contained list in Arena export format
(`<qty> <Name> (<SET>) <collector#>`), optionally preceded by a metadata header
whose lines start with `#:` — for example:

    #: name: Avatar Tempo
    #: format: Standard
    #: colors: WU
    #: archetype: Azorius (W/U) fliers / tempo   (one-line identity; `list` shows it)
    #: notes: removal-heavy base build   (free-form; may span several `#: notes:` lines)

    4 Katara, Bending Prodigy (TLA) 59
    ...

Plain `#` lines are comments; blank lines are ignored. Loose `decks/<name>.txt`
files (no folder) work too, with the filename as the id.

Commands:
    python3 scripts/deck.py list                # all decks + variants, buildable?
    python3 scripts/deck.py wildcards           # roster crafting plan (wildcards to finish)
    python3 scripts/deck.py check 1a            # owned vs needed vs your collection
    python3 scripts/deck.py diff 1 1a           # what the variant changes
    python3 scripts/deck.py arena 1a            # emit an Arena-importable list
    python3 scripts/deck.py stats 1a            # mana curve, colors, types, functional roles
    python3 scripts/deck.py mana 1a             # hybrid-aware color requirements + castability lint
    python3 scripts/deck.py suggest 1a --owned  # OWNED pool cards that fit the deck (0 wildcards)
    python3 scripts/deck.py legal 1a            # construction lint: size, copy limits, format legality
    python3 scripts/deck.py cuts 1a             # rank the deck's weakest-fit cards as cut candidates
    python3 scripts/deck.py swap 1a --cut A --add B   # preview a swap's deltas (--apply to write)
    python3 scripts/deck.py apply-flex 1a 2     # promote flex swap #2 into the maindeck

Mana analysis reads card-mana.csv (real mana costs, built by build_mana.py), so
hybrid {W/U} pips are counted as flexible rather than demanding both colors.
"""

import argparse
import csv
import json
import math
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request

from lib import (DEFAULT_CSV, REPO_ROOT, load_rows, eprint, card_colors, owned_qty,
                 card_distinctiveness, backup_path, card_power, front_face_cost,
                 mana_value, primary_type, atomic_write)
from scryfall import post_collection, ScryfallUnavailable

POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")

DECKS_DIR = os.path.join(REPO_ROOT, "decks")
MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")
BASICS = {"plains", "island", "swamp", "mountain", "forest", "wastes"}


def _file_memo(*path_names):
    """Memoize a zero-arg reference-table loader on its source files' (mtime_ns, size).

    The reference tables (mana / card data / collection / meta / keywords) were read
    from CSV on EVERY call, and a roster-wide pass calls them once per deck: 65 decks
    x ~0.31s of re-parsing was ~21s of the integrity gate's runtime, and it is why a
    roster-wide rationale sweep looked too expensive to run automatically — which is
    exactly the check that then never ran, and let 13 stale figures accumulate. With
    this, check_all goes 23s -> 4s and the sweep becomes affordable.

    Takes the module-global NAMES of the source files, not their values, and resolves
    them per call. `check_suggest`'s wiring anchor repoints `deck.POOL_CSV` at a
    synthetic pool, and a path captured at decoration time would key the cache on the
    REAL file while the loader body read the synthetic one — a stale-cache bug in the
    one check whose entire job is catching wiring mistakes. The resolved path is part
    of the key, so repointing invalidates.

    Keyed on (mtime_ns, size) rather than held forever, so a rebuild (`build_mana.py`,
    an `app.py` write) invalidates it inside a long-running process. Safe because
    every caller treats these tables as READ-ONLY — verified by scanning all of
    scripts/ for external mutation of a loader's result; if you ever need to mutate
    one, copy it first, since the dict is now shared.
    """
    def deco(fn):
        cache = {}

        def stamp(name):
            path = globals().get(name)
            try:
                st = os.stat(path)
            except (OSError, TypeError):
                return (path, None)
            # ns, not getmtime()'s float seconds: app.py can rewrite a CSV twice
            # within one mtime tick, and a same-size rewrite would then serve stale.
            return (path, st.st_mtime_ns, st.st_size)

        def wrapped():
            key = tuple(stamp(n) for n in path_names)
            if cache.get("key") != key:
                cache["key"], cache["val"] = key, fn()
            return cache["val"]

        wrapped.__name__, wrapped.__doc__ = fn.__name__, fn.__doc__
        wrapped.cache_clear = cache.clear
        return wrapped
    return deco

# Formats the pool's Legalities column can carry (mirrors build_pool.py). Used to
# filter `suggest` to a deck's format so craft picks are legal to play/acquire.
POOL_FORMATS = {"standard", "pioneer", "modern", "legacy", "vintage", "pauper",
                "historic", "timeless", "alchemy", "explorer", "brawl"}

# Arena wildcard tiers. A card's Rarity == the wildcard needed to craft a copy.
WC_LETTER = {"common": "C", "uncommon": "U", "rare": "R", "mythic": "M"}
WC_NAMES = [("M", "Mythic"), ("R", "Rare"), ("U", "Uncommon"),
            ("C", "Common"), ("?", "Unknown")]

# "4 Card Name" / "4x Card Name", optional "(SET)" and collector number.
LINE_RE = re.compile(r"^\s*(\d+)\s*[xX]?\s+(.+?)\s*(?:\(([^)]+)\)\s*([^\s]+)?)?\s*$")
# A HYPHEN is legal in a `#:` key. It was not, and the deck files had been using one
# anyway: 24 `#: based-on:` lines across the roster were silently dropped — the line
# matched no meta key, fell through to the card-line branch, matched no card either, and
# vanished without a warning. Nothing read `based-on`, so nothing noticed. Found while
# adding `#: uncastable-ok:` (F-02), whose key has the same shape. Nothing iterates meta
# keys (only named lookups), so widening this adds keys without changing any output.
META_RE = re.compile(r"^#:\s*([A-Za-z_][A-Za-z_-]*)\s*:\s*(.*)$")

# Game-type (format) variant filenames: `<core>-<format>[-slug].txt`. These get the
# id `<core>-<format>` so a Brawl/Alchemy adaptation of a core deck reads as *that
# deck's* Brawl/Alchemy version, distinct from a Standard sub-variant (3a). The format
# token here is only for the id/organization; the deck's `#: format:` header remains the
# authoritative format for the legality/rotation tooling.
_FORMAT_SLUGS = ("alchemy", "historic-brawl", "brawl", "timeless", "explorer",
                 "pioneer", "modern", "pauper", "historic")
FORMAT_VARIANT_RE = re.compile(r"^(\d+)-(" + "|".join(_FORMAT_SLUGS) + r")(?:[-.])", re.I)


# --------------------------------------------------------------------------- #
# Deck discovery + parsing
# --------------------------------------------------------------------------- #
def parse_deck_file(path):
    """Return (meta_dict, [(qty, name, set, collector), ...]).

    A repeated `#:` key (notably a multi-line `#: notes:` block) is concatenated
    in order rather than overwritten, so the FULL note survives — previously only
    the last `#: notes:` line was kept, which truncated a deck's documented intent
    to a mid-sentence fragment in every tool that reads it."""
    meta, cards = {}, []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            m = META_RE.match(raw.strip())
            if m:
                key, val = m.group(1).lower(), m.group(2).strip()
                if key in meta and meta[key] and val:
                    meta[key] = f"{meta[key]} {val}"
                elif key not in meta or val:
                    meta[key] = val
                continue
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            cm = LINE_RE.match(line)
            if cm:
                cards.append((int(cm.group(1)), cm.group(2).strip(),
                              (cm.group(3) or "").strip(), (cm.group(4) or "").strip()))
    return meta, cards


def discover_decks():
    """Return a list of deck records: {id, name, path, core, variant}."""
    decks = []
    if not os.path.isdir(DECKS_DIR):
        return decks
    for entry in sorted(os.listdir(DECKS_DIR)):
        full = os.path.join(DECKS_DIR, entry)
        if os.path.isdir(full):
            m = re.match(r"^(\d+)-(.+)$", entry)
            core = str(int(m.group(1))) if m else entry
            for fn in sorted(os.listdir(full)):
                if not fn.endswith(".txt"):
                    continue
                p = os.path.join(full, fn)
                if fn == "deck.txt":
                    decks.append(_record(core, core, p, core, False))
                else:
                    # A GAME-TYPE variant — `<core>-<format>[-slug].txt` (e.g.
                    # 3-brawl-knights-edge.txt) gets the id `<core>-<format>` (e.g.
                    # `3-brawl`), so an Alchemy/Brawl adaptation of core deck 3 reads as
                    # deck 3's Brawl version, NOT as another Standard sub-variant like 3a.
                    fmv = FORMAT_VARIANT_RE.match(fn)
                    if fmv:
                        did = f"{int(fmv.group(1))}-{fmv.group(2).lower()}"
                    else:
                        vm = re.match(r"^(\d+[a-z]+)-", fn)
                        did = vm.group(1) if vm else os.path.splitext(fn)[0]
                    decks.append(_record(did, core, p, core, True))
        elif entry.endswith(".txt"):
            did = os.path.splitext(entry)[0]
            decks.append(_record(did, did, full, did, False))
    return decks


def _record(did, core, path, core_id, variant):
    meta, _ = parse_deck_file(path)
    return {"id": did, "name": meta.get("name", ""), "path": path,
            "core": core_id, "variant": variant, "meta": meta}


def find_deck(deck_id):
    for d in discover_decks():
        if d["id"].lower() == deck_id.lower():
            return d
    return None


# Decks that exist as documentation/placeholders rather than lists you'd sleeve up.
# A `#: status:` header naming one of these keeps the deck fully addressable by id —
# `check`, `stats`, `cuts`, the editor all still work on it — while dropping it from
# ROSTER-WIDE views, where it is pure noise. The example deck is a 26-card illustration
# of the file format, so it is permanently illegal: it sat at the top of `deck.py audit`
# occupying BOTH ★ TUNE slots, making the triage's most actionable output ("Full-tune
# candidates: 0, 0a") 100% false positive and permanently un-actionable (broad-scan
# F-06). It also counted as a deck a card could be "reused" in. `wishlist._theme_model`
# already excluded it by a card-count heuristic; this makes the intent explicit and
# shared, so every roster view agrees on what counts as part of the roster.
NONROSTER_STATUSES = {"example", "template", "placeholder", "retired", "archived"}


def deck_status(meta):
    """The `#: status:` keyword (lowercased first word), or '' when unset."""
    raw = (meta or {}).get("status", "") or ""
    return raw.strip().split()[0].strip().lower() if raw.strip() else ""


def is_roster_deck(d):
    """True when a deck should COUNT toward roster-wide views (audit / rotation / brawl /
    wildcards / cross-deck reuse / tier sweep). False for a documentation placeholder or a
    retired list. Never affects addressing a deck directly by id."""
    return deck_status(d.get("meta") or {}) not in NONROSTER_STATUSES


def roster_decks():
    """`discover_decks()` narrowed to the decks that are really part of the roster."""
    return [d for d in discover_decks() if is_roster_deck(d)]


# --------------------------------------------------------------------------- #
# Collection lookup
# --------------------------------------------------------------------------- #
@_file_memo("DEFAULT_CSV")
def load_collection():
    """Return (by_key, by_name, by_name_qty).

    by_key/by_name map to a representative row (for type/printing lookups);
    by_name_qty sums Quantity Owned across every printing of a name, since Arena
    copies are fungible across sets (see owned()).
    """
    _, rows = load_rows(DEFAULT_CSV)
    by_key, by_name, by_name_qty = {}, {}, {}
    for r in rows:
        name = (r.get("Card Name") or "").strip()
        if not name:
            continue
        nl = name.lower()
        key = (nl, (r.get("Set Code") or "").strip().lower(),
               (r.get("Collector #") or "").strip().lower())
        by_key[key] = r
        by_name.setdefault(nl, r)
        q = (r.get("Quantity Owned") or "").strip()
        by_name_qty[nl] = by_name_qty.get(nl, 0) + (int(q) if q.isdigit() else 0)
    return by_key, by_name, by_name_qty


_PIP_DEPTH_MIN = 3          # only 3+ pips of ONE colour are worth checking
_PIP_DEPTH_TURN = 5         # grade on-curve-ish, capped like `consistency` does
_PIP_DEPTH_TARGET = 0.70    # below this, say so; deliberately looser than consistency's 0.90


def deck_color_sources(cards, meta, carddata):
    """{colour: number of LANDS in the deck producing it} — basics by name, nonbasics by
    colour identity, mana dorks NOT counted (the same rule `deck.py mana` prints).

    Needs BOTH maps: card-meta carries colours, card-data carries the type line.
    """
    src = {c: 0 for c in "WUBRG"}
    for q, n, _s, _c in cards:
        nl = n.lower()
        if nl in BASICS:
            col = BASIC_COLOR.get(nl)
            if col:
                src[col] += q
            continue
        cd = carddata.get(nl)
        if not cd or "Land" not in _primary_type(cd.get("type") or ""):
            continue
        m = meta.get(nl)
        for col in ((m or {}).get("colors") or set()):
            if col in src:
                src[col] += q
    return src


def pip_depth_warning(cost, sources):
    """(colour, pips, have, want) when a card's DEEPEST single-colour pip demand is more
    than the deck's sources realistically support — else None.

    `suggest` / `suggest-homes` test castability as `card identity ⊆ deck colours`, which
    is a set question and cannot see DEPTH. That is how Anti-Venom, Horrifying Healer
    ({W}{W}{W}{W}{W}) was recommended as a KEY fit for two GWR decks holding 10 and 11
    white sources — about a 1% chance of casting it on turn five. Identity said yes; the
    arithmetic says never. Five pips wants roughly 33 sources for 85%, which no 60-card
    deck can reach, so this is genuinely un-castable rather than merely greedy.

    Reported as a FLAG, never a filter: a deep-pip card can still be a fine late-game
    play in a deck that leans hard on its colour, and the caller prints the numbers so a
    human decides. Hybrids are excluded (strictly easier), matching `parse_pips`.
    """
    strict, _hybrid = parse_pips(cost or "")
    if not strict:
        return None
    col, pips = max(strict.items(), key=lambda kv: kv[1])
    if pips < _PIP_DEPTH_MIN:
        return None
    have = sources.get(col, 0)
    seen = cards_seen(_PIP_DEPTH_TURN)
    if hypergeom_at_least(60, have, seen, pips) >= _PIP_DEPTH_TARGET:
        return None
    want = next((s for s in range(have + 1, 41)
                 if hypergeom_at_least(60, s, seen, pips) >= _PIP_DEPTH_TARGET), None)
    return (col, pips, have, want)


def owned(by_name_qty, name):
    """(count_owned, in_library) for a deck card.

    Basics count as unlimited. Copies are summed across ALL printings of a card,
    because an Arena playset is fungible regardless of set/collector number — a
    card owned 1x in one set and 1x in another counts as 2 toward a deck's needs
    (mirrors pool.py's owned_counts, which also sums across printings).
    """
    if name.lower() in BASICS:
        return 99, True
    nl = name.lower()
    if nl in by_name_qty:
        return by_name_qty[nl], True
    # DFC fallback. This used to be a bare `return 0, False`, on the documented
    # assumption that deck-file names are always FRONT-face by convention — an
    # assumption `deck.py resolve` falsifies, because it emits the full `A // B`
    # name (that is how the pool keys a DFC, and how Arena exports one). So a deck
    # built by `resolve` reported its own owned DFC as "NOT IN LIBRARY": deck 45a
    # said that about Norman Osborn the moment it was opened, while `lib.owned_qty`
    # resolved it correctly the whole time. Route through the shared helper rather
    # than re-implement the split — that is the A3/A4/F6 rule.
    qty = owned_qty(by_name_qty, name)
    return (qty, True) if qty else (0, False)


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def _deck_identity(meta, width=92):
    """One-line 'meant-for' summary for `list`: the `#: archetype:` field if the
    deck declares one, else the first sentence of its `#: notes:`. '' if neither."""
    txt = (meta.get("archetype") or "").strip()
    if not txt:
        note = (meta.get("notes") or "").strip()
        txt = re.split(r"(?<=[.;])\s", note, 1)[0] if note else ""
    return (txt[:width - 1].rstrip() + "…") if len(txt) > width else txt


def cmd_list(_args):
    decks = discover_decks()
    if not decks:
        print("No decks yet. Add one under decks/<NN-name>/deck.txt "
              "(see decks/README.md).")
        return 0
    _, _, by_name_qty = load_collection()
    cores = {}
    for d in decks:
        cores.setdefault(d["core"], []).append(d)

    for core in sorted(cores, key=lambda c: (len(c), c)):
        group = sorted(cores[core], key=lambda d: (d["variant"], d["id"]))
        for d in group:
            _, cards = parse_deck_file(d["path"])
            total = sum(q for q, *_ in cards)
            short = 0
            for q, n, s, c in cards:
                have, found = owned(by_name_qty, n)
                if not found or have < q:
                    short += 1
            status = "OK " if short == 0 else f"{short} short"
            label = d["name"] or os.path.basename(os.path.dirname(d["path"])) or d["id"]
            tag = "  └─ variant" if d["variant"] else "CORE"
            # `list` shows EVERY deck (it's the index), but marks the ones roster-wide
            # views skip so their absence from `audit`/`rotation`/`wildcards` isn't a
            # mystery.
            st = deck_status(d["meta"])
            mark = f"  [{st}]" if st in NONROSTER_STATUSES else ""
            print(f"  [{d['id']:>4}] {tag:12} {label:28} {total:3} cards  {status}{mark}")
            ident = _deck_identity(d["meta"])
            if ident:
                print(f"          {ident}")
    return 0


# --- wildcard (crafting) planning ------------------------------------------- #
@_file_memo("POOL_CSV")
def load_rarities():
    """name_lower -> wildcard letter (C/U/R/M) from card-pool.csv's Rarity.

    Memoized like every other reference-table loader. It was the ONE left out when
    `_file_memo` landed, and it is read per CARD-SCORING PASS rather than per command:
    `rank_cut_candidates` calls it for the power co-signal, so a full-pool re-parse ran
    for every deck a roster sweep touched. It was **85% of `deck.py cuts`' runtime**
    (0.69s of 0.81s) and, being invisible in any single command's wall clock, it only
    surfaced when a roster-wide gate made the per-deck cost add up.

    ANSWERS FOR A DFC'S FRONT FACE TOO, like every other reference-table loader
    (`load_card_data`, `load_mana`, `load_legalities`, `load_card_meta`,
    `_pool_rotation_index`). This one read the POOL, which keys only the full
    `Front // Back` name, and had no alias — so 47 distinct names across the live roster
    resolved to `""`, which is not an error anywhere: `cut_keep_score` hands the empty
    string to `_power_seed`, which falls to its default floor. Every mythic/rare DFC was
    therefore seeded as low-rarity and sorted UP the cut list — Ojer Axonil's
    `_cuts_power_adj` came out −0.70 where the real mythic gives +0.17, so the sign of
    the nudge flipped and the model treated a bomb as more cuttable. This is the SAME
    bug the note in `cut_keep_score` records as fixed for the rarity word-vs-letter
    shape (F-01); the front-face shape was never covered (broad-scan F-14).

    The alias is a SECOND PASS on purpose. Adding `out.setdefault(front, …)` inside the
    row loop would let a `Front // Back` row seen early shadow a real, distinct card
    named `Front` seen later — `"Life"` is a card as well as the front of
    `"Life // Death"`, the same trap `build_mana._front_face_retry` guards. Aliasing
    only after every real row is in the dict makes the result order-independent."""
    out = {}
    if not os.path.exists(POOL_CSV):
        return out
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            rar = (r.get("Rarity") or "").strip().lower()
            if n and rar:
                out.setdefault(n, WC_LETTER.get(rar, "?"))
    for n, letter in list(out.items()):
        front = n.split(" // ")[0]
        if front != n:
            out.setdefault(front, letter)
    return out


def fetch_missing_rarities(names, rarities):
    """Live-fetch rarity for craft targets absent from the pool (e.g. non-Standard
    WIP cards). Degrades gracefully to '?' if Scryfall is unreachable."""
    todo = [n for n in names if n.lower() not in rarities]
    for i in range(0, len(todo), 75):
        chunk = todo[i:i + 75]
        try:
            data = post_collection(chunk)
        except ScryfallUnavailable as e:
            # A slow/flaky Scryfall (timeout, 5xx, bad body) must degrade to '?'
            # here, not crash — this helper exists precisely for the offline case.
            eprint(f"WARN:  could not reach Scryfall for rarity lookup ({e}); "
                   f"{len(todo) - i} card(s) will show wildcard '?'.")
            break
        for card in data.get("data", []):
            rar = WC_LETTER.get((card.get("rarity") or "").lower(), "?")
            full = card.get("name", "").lower()
            rarities.setdefault(full, rar)
            rarities.setdefault(full.split(" // ")[0], rar)
        time.sleep(0.1)
    return rarities


def _wc_breakdown(shortfalls, rar_of):
    """{wildcard letter: copies} for a list of (name, missing_copies)."""
    by = {}
    for name, miss in shortfalls:
        r = rar_of(name)
        by[r] = by.get(r, 0) + miss
    return by


def _wc_str(by):
    return " ".join(f"{by[r]}{r}" for r, _ in WC_NAMES if by.get(r))


def cmd_wildcards(_args):
    """Roster-wide crafting plan: what to craft, and which crafts unlock the most
    decks. Owned copies are shared across decks and summed across printings, so a
    card is only ever short by (max any deck needs − total owned)."""
    decks = roster_decks()   # a documentation placeholder must not demand wildcards
    if not decks:
        print("No decks yet. Add one under decks/<NN-name>/deck.txt.")
        return 0
    _, _, by_name_qty = load_collection()
    rarities = load_rarities()

    deck_short = {}       # deck id -> [(name, missing_copies)]
    max_need = {}         # name_lower -> max copies any single deck needs
    display = {}          # name_lower -> display name
    needed_by = {}        # name_lower -> set(deck ids short on it)
    for d in decks:
        _, cards = parse_deck_file(d["path"])
        need = {}
        for q, n, s, c in cards:
            if n.lower() in BASICS:
                continue  # basics are free/unlimited in Arena
            need[n] = need.get(n, 0) + q
        shorts = []
        for n, req in need.items():
            nl = n.lower()
            display[nl] = n
            max_need[nl] = max(max_need.get(nl, 0), req)
            have, _ = owned(by_name_qty, n)
            miss = max(0, req - have)
            if miss > 0:
                shorts.append((n, miss))
                needed_by.setdefault(nl, set()).add(d["id"])
        deck_short[d["id"]] = shorts

    # Resolve rarities for every craft target (pool first, live fallback).
    short_names = sorted({n for shorts in deck_short.values() for n, _ in shorts})
    if short_names:
        fetch_missing_rarities(short_names, rarities)
    rar_of = lambda name: rarities.get(name.lower(), "?")

    # Per-deck: wildcards to finish, closest-to-done first.
    print("Roster crafting plan\n")
    print(f"{'Deck':>5}  {'Name':26}  Wildcards to finish")
    print("-" * 60)
    ordered = sorted(decks, key=lambda d: (sum(m for _, m in deck_short[d["id"]]),
                                           len(d["id"]), d["id"]))
    for d in ordered:
        shorts = deck_short[d["id"]]
        label = (d["name"] or d["id"])[:26]
        total = sum(m for _, m in shorts)
        if total == 0:
            print(f"{d['id']:>5}  {label:26}  buildable ✓")
        else:
            print(f"{d['id']:>5}  {label:26}  {total:2} copy(s):  "
                  f"{_wc_str(_wc_breakdown(shorts, rar_of))}")

    # Highest-leverage crafts: one craft, multiple decks unblocked.
    multi = sorted(((nl, ids) for nl, ids in needed_by.items() if len(ids) >= 2),
                   key=lambda kv: (-len(kv[1]), kv[0]))
    if multi:
        print("\nHighest-leverage crafts (one card, multiple decks):")
        for nl, ids in multi[:15]:
            decks_s = ", ".join(sorted(ids, key=lambda x: (len(x), x)))
            print(f"  {display[nl]} ({rar_of(display[nl])})  — {len(ids)} decks: {decks_s}")

    # Roster totals: one shared collection, so per card only max(0, maxneed-owned).
    roster = {}
    for nl, req in max_need.items():
        have, _ = owned(by_name_qty, display[nl])
        miss = max(0, req - have)
        if miss > 0:
            r = rar_of(display[nl])
            roster[r] = roster.get(r, 0) + miss
    print("\nTotal wildcards to make EVERY deck buildable (shared collection):")
    if roster:
        print("  " + "   ".join(f"{roster[r]} {name}" for r, name in WC_NAMES
                                if roster.get(r)))
        if roster.get("?"):
            print("  ('?' = rarity unresolved — rebuild card-pool.csv or check "
                  "Scryfall connectivity.)")
    else:
        print("  Nothing to craft — the whole roster is buildable. ✓")
    return 0


def _declared_colors(meta):
    """The deck's stated colors as a WUBRG set, from the `#: colors:` header."""
    return card_colors(meta.get("colors"))


def _deck_castable_colors(dmeta, cards, mana):
    """The colors a deck can actually CAST — the declared `#: colors:` if present,
    else derived from its nonland mana COSTS (never color identity, so off-color
    activated abilities don't widen it). Same rule `suggest` uses."""
    cols = _declared_colors(dmeta)
    if cols:
        return cols
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        entry = mana.get(n.lower())
        if entry and entry[0]:
            strict, hybrid = parse_pips(entry[0])
            # Only a TRUE multicolor hybrid ({W/U}) constrains castable colors; a
            # monocolor hybrid ({2/W}) or Phyrexian ({W/P}) is payable WITHOUT its
            # color, so it must not widen the deck's colors (audit F15; mirrors
            # suggest_scored line ~1401 and _castability's len(h) >= 2).
            cols |= set(strict) | {x for h in hybrid if len(h) >= 2 for x in h}
    return cols


BASIC_COLOR = {"plains": "W", "island": "U", "swamp": "B", "mountain": "R", "forest": "G"}


def _castability(cards, declared, mana, carddata, exempt=frozenset()):
    """Flag nonland cards whose color needs fall outside `declared` (a WUBRG set).

    Returns (uncastable, off_identity, off_ability, intended):
      intended     – the SUBSET of would-be-uncastable cards the deck's
                     `#: uncastable-ok:` header names on purpose (a reanimator's
                     targets). Still reported by every surface, but never counted as
                     a failure and never fed to `tier_band`. See `_uncastable_ok`.

    Returns (uncastable, off_identity, off_ability):
      uncastable   – [(name, "needs X")] : a STRICT pip, or a true multicolor
                     hybrid with NO in-declared-color option, in a color the deck
                     can't produce. These genuinely can't be cast off the stated
                     colors. (Needs real mana costs — pass a populated `mana`.)
      off_identity – [(name, why)] : castable as printed, but the card's color
                     IDENTITY strays outside declared — every stray, for display.
      off_ability  – the SUBSET of off_identity whose stray is NOT explained by a
                     hybrid pip in the mana cost, i.e. it comes from rules text (an
                     activated ability you can't pay, another face). This is the
                     only part that is ever actionable.

    The two kinds were reported as one list, and the `why` string ("identity has R")
    could not tell them apart — so `audit_deck` counted both and the roster triage's
    `review` verdict fired on 22 of 63 decks with a measured 0% actionable rate
    (broad-scan F-03). A hybrid you pay on-color costs you nothing: Knight's Edge is
    mono-W and runs two R/W hybrids that are simply white cards in that deck. An
    off-color ABILITY is different — Super-Skrull casts for {1}{B}{B}{B} but its
    {4}{R} ability is dead in a deck with no red, and that is worth a look. Splitting
    them turns a saturated flag back into a shortlist; the display keeps showing
    both, since "this card's identity is wider than the deck" is still true and
    useful to see, and only the VERDICT narrows.

    An empty `declared` disables the lint. With an empty `mana` dict the strict
    check is skipped and only the offline identity check runs (so `check` stays
    network-free) — note that with no costs to read, no stray can be shown to be
    hybrid-explained, so every stray reads as an ability stray. That is the
    conservative direction: it over-reports rather than silently clearing a deck."""
    uncastable, off_ident, off_ability, intended = [], [], [], []
    if not declared:
        return uncastable, off_ident, off_ability, intended
    seen = set()
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS or nl in seen:
            continue
        cd = carddata.get(nl)
        if cd is None:
            # No type/identity data for this card (in neither library nor pool —
            # e.g. a brand-new WIP craft target). We can't tell a land from a
            # spell or read its identity, so don't lint it rather than treat it
            # as a nonland and flag it against empty color data.
            continue
        if "Land" in _primary_type(cd["type"]):
            continue
        seen.add(nl)
        entry = mana.get(nl)
        strict, hybrid = parse_pips(entry[0] if entry else "")
        off_strict = sorted(set(strict) - declared)
        # A single-color hybrid ({2/W} generic-or-W, {W/P} phyrexian) can always be
        # paid without its color; only a true multicolor hybrid constrains castability.
        bad_hybrid = sorted({x for h in hybrid
                             if len(h) >= 2 and not (h & declared) for x in h})
        if off_strict or bad_hybrid:
            why = "needs " + "/".join(sorted(set(off_strict + bad_hybrid)))
            (intended if nl in exempt else uncastable).append((n, why))
            continue
        ident = card_colors(cd["colors"] if cd else "")
        stray = sorted(ident - declared)
        if stray:
            # A stray colour that appears ONLY as a hybrid pip in the cost is one you
            # pay on-colour — the card is a plain on-colour card in this deck. Anything
            # else came from the rules text (an off-colour activated ability, another
            # face), which is the part worth reviewing.
            #
            # Without a cost we cannot tell the two apart, and asserting either would be
            # a claim we can't support: `cmd_check` deliberately passes an empty `mana`
            # to stay offline, and every stray there would otherwise be labelled an
            # off-colour ability — false for the R/W hybrids in a mono-W deck. So say
            # "unknown" in the text, while still COUNTING it as actionable, which keeps
            # the offline path over-reporting rather than silently clearing a deck.
            hybrid_colors = set().union(*hybrid) if hybrid else set()
            known_cost = bool(entry and entry[0])
            by_hybrid = known_cost and set(stray) <= hybrid_colors
            note = (" (hybrid — paid on-color)" if by_hybrid
                    else " (off-color ability)" if known_cost
                    else " (cost unknown — run `deck.py mana` to tell hybrid from ability)")
            why = "identity has " + "/".join(stray) + note
            off_ident.append((n, why))
            if not by_hybrid:
                off_ability.append((n, why))
    return uncastable, off_ident, off_ability, intended


def cmd_check(args):
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    _, _, by_name_qty = load_collection()
    meta, cards = parse_deck_file(d["path"])

    # Aggregate copies per card first: a deck may list the same card on more than
    # one line, and owned counts are per-name (fungible across printings), so the
    # short/missing check must compare total-need vs total-owned, not line-by-line.
    need, order, printing = {}, [], {}
    for q, n, s, c in cards:
        nl = n.lower()
        if nl not in need:
            order.append(nl)
            printing[nl] = (n, s)
        need[nl] = need.get(nl, 0) + q

    print(f"Deck {d['id']}: {d['name'] or d['path']}")
    print(f"{'Have':>4} / {'Need':<4}  Card")
    print("-" * 44)
    missing, short = [], []
    for nl in order:
        n, s = printing[nl]
        req = need[nl]
        have, found = owned(by_name_qty, n)
        flag = ""
        if not found:
            flag = "  <- NOT IN LIBRARY"
            missing.append(n)
        elif have < req:
            flag = f"  <- short {req - have}"
            short.append(n)
        shown = "unlim" if nl in BASICS else have
        print(f"{str(shown):>4} / {req:<4}  {n} ({s}){flag}")
    print("-" * 44)
    total = sum(need.values())
    print(f"{len(order)} unique, {total} total.")
    if missing:
        print(f"{len(missing)} not in library: {', '.join(missing)}")
    if short:
        print(f"{len(short)} short of the deck's requirement.")
    if not missing and not short:
        print("You own everything in this deck. Ready to build.")

    # Castability lint (offline, identity-only — pass an empty mana dict). Flags
    # cards whose color identity strays outside the deck's declared colors.
    declared = _declared_colors(meta)
    _, off_ident, _, _ = _castability(cards, declared, {}, load_card_data())
    if declared and off_ident:
        cols = "".join(sorted(declared))
        print(f"\n⚠ {len(off_ident)} card(s) stray outside the deck's {cols} colors "
              f"(run `deck.py mana {d['id']}` for castability detail):")
        for n, why in off_ident:
            print(f"    {n} — {why}")
    return 1 if (missing or short) else 0


def _ms_key(name):
    """The canonical comparison key for a card NAME: lowercased, FRONT FACE only.

    Every other name-facing join in this repo resolves `Front // Back` to the front
    (`lib.owned_qty`, `load_card_data`, `load_mana`, `load_legalities`,
    `_pool_rotation_index`, `_printing_of`, `_printing_index`). `_multiset` was the
    exception, and it is the key behind `verify` / `sync` / `diff` / the dashboard's
    stale-check — the commands whose whole job is matching a pasted list against a
    stored one BY NAME. So a deck file storing `Ojer Axonil, Deepest Might // Temple of
    Power` against an export naming just the front read as a real change:

        +1  Ojer Axonil, Deepest Might
        -1  Ojer Axonil, Deepest Might // Temple of Power

    `verify` exited non-zero on an identical deck, and `sync --apply` would have
    "repaired" the file by replacing the full name with the bare front — the exact
    un-importable line P8 fixed `_printing_of` to stop writing, re-introduced from the
    other side, past a green INV-04 check (the copy count is unchanged). 14 deck files
    carry a `Front // Back` line. Fifth member of the G-63 class (broad-scan F-02)."""
    return (name or "").strip().lower().split(" // ")[0]


def _ms_display(existing, incoming):
    """Pick the display name to keep when two spellings of one card meet.

    FIRST-SEEN wins (the long-standing rule audit F4 established), with ONE exception:
    the full `Front // Back` form beats a bare front face. A bare front name parses and
    passes INV-04 but fails an Arena import (P8), so when either spelling knows the
    two-faced name it is the one that belongs in a deck file."""
    if existing is None:
        return incoming
    if " // " in (incoming or "") and " // " not in existing:
        return incoming
    return existing


def _multiset(cards):
    """{name_key: (display_name, total_qty)} — keyed case-insensitively (like every
    other command) so the SAME card spelled with different casing across two files
    isn't reported as a spurious −N / +N change (audit F4), and FRONT-FACE normalized
    (see `_ms_key`) so the two legitimate spellings of a double-faced card aren't
    either. The fullest spelling seen is kept for display, so a reconcile that has to
    write the line back writes the importable name."""
    m = {}
    for q, n, s, c in cards:
        nl = _ms_key(n)
        disp, cur = m.get(nl, (None, 0))
        m[nl] = (_ms_display(disp, n), cur + q)
    return m


def cmd_diff(args):
    a, b = find_deck(args.a), find_deck(args.b)
    if not a or not b:
        eprint("Both deck ids must exist. Try: deck.py list")
        return 1
    ma = _multiset(parse_deck_file(a["path"])[1])
    mb = _multiset(parse_deck_file(b["path"])[1])
    print(f"Diff {a['id']} -> {b['id']}  (what {b['id']} changes)")
    print("-" * 40)
    names = sorted(set(ma) | set(mb))
    added = removed = 0
    for nl in names:
        da, db = ma.get(nl, (None, 0)), mb.get(nl, (None, 0))
        disp = db[0] or da[0]  # prefer the target deck's spelling, else the base's
        if db[1] > da[1]:
            print(f"  +{db[1] - da[1]}  {disp}")
            added += db[1] - da[1]
        elif da[1] > db[1]:
            print(f"  -{da[1] - db[1]}  {disp}")
            removed += da[1] - db[1]
    if not added and not removed:
        print("  (identical)")
    else:
        print("-" * 40)
        print(f"+{added} added, -{removed} removed")
    return 0


def cmd_arena(args):
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}.")
        return 1
    _, cards = parse_deck_file(d["path"])
    print("Deck")
    for q, n, s, c in cards:
        line = f"{q} {n}"
        if s:
            line += f" ({s})" + (f" {c}" if c else "")
        print(line)
    return 0


# --- mana data: real costs from card-mana.csv, with a live fallback --------- #
@_file_memo("MANA_CSV")
def load_mana():
    """name_lower -> (mana_cost, mana_value) from card-mana.csv (built by build_mana.py)."""
    import csv as _csv
    out = {}
    if not os.path.exists(MANA_CSV):
        return out
    with open(MANA_CSV, newline="", encoding="utf-8") as fh:
        for r in _csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            if not n:
                continue
            cost = r.get("Mana Cost") or ""
            mv = (r.get("Mana Value") or "").strip()
            mv = int(mv) if mv.isdigit() else None
            if " // " in cost:
                # A split / Room card's RULES mana value is the combined total, which
                # is what Scryfall stores — and it is not the number a curve or a
                # cast-on-curve probability wants. Funeral Room came through as MV 11
                # and inflated deck 42a's average; the door you cast costs 3. Adventure
                # cards already store the front-face value, so recomputing agrees with
                # them and only corrects the split/Room shape.
                mv = mana_value(front_face_cost(cost))
            out[n] = (cost, mv)
            out.setdefault(n.split(" // ")[0], out[n])
    return out


def fetch_missing_mana(names, mana):
    """Live-fetch costs for names absent from card-mana.csv (e.g. unowned WIP cards)."""
    todo = [n for n in names if n.lower() not in mana]
    for i in range(0, len(todo), 75):
        chunk = todo[i:i + 75]
        try:
            data = post_collection(chunk)
        except ScryfallUnavailable as e:
            eprint(f"WARN:  could not reach Scryfall for live mana lookup "
                   f"({e}); {len(todo) - i} card(s) not in card-mana.csv will "
                   f"show as unknown. This is a network issue, not stale data.")
            break
        for card in data.get("data", []):
            faces = card.get("card_faces") or [{}]
            cost = card.get("mana_cost") or faces[0].get("mana_cost", "")
            mv = card.get("cmc", 0)
            full = card.get("name", "").lower()
            mana[full] = (cost or "", int(mv) if isinstance(mv, (int, float)) else None)
            mana.setdefault(full.split(" // ")[0], mana[full])
        time.sleep(0.1)
    return mana


SYMBOL_RE = re.compile(r"\{([^}]+)\}")


def parse_pips(cost):
    """Classify a mana cost's symbols into (strict, hybrid).

    strict: {color: count} of single-color pips that MUST be paid with that color.
    hybrid: list of frozensets of colors a symbol accepts (e.g. {'W','U'}) — each
            payable with ANY one of them (hybrid {W/U}, monocolor hybrid {2/W},
            or phyrexian {W/P}).

    Reads only the FRONT FACE (``lib.front_face_cost``). A split / Room / Adventure
    card's stored cost is ``A // B`` and you never pay both halves, so the merged
    string double-counted pips for all 292 such cards in the pool — Funeral Room's
    ``{2}{B} // {6}{B}{B}`` read as wanting three black pips when the door you cast
    wants one.
    """
    strict, hybrid = {}, []
    for sym in SYMBOL_RE.findall(front_face_cost(cost)):
        colors = set(ch for ch in sym.upper() if ch in "WUBRG")
        if "/" in sym:
            if colors:
                hybrid.append(frozenset(colors))
        elif len(colors) == 1:
            (c,) = colors
            strict[c] = strict.get(c, 0) + 1
    return strict, hybrid


# The definition lives in lib.primary_type — build_gallery.py needs the same answer and
# had its own copy with the same back-face bug. Kept under the private name because ~35
# call sites below, build_dashboard.py and the tests all reach for `_primary_type`.
_primary_type = primary_type


# --- card data (type + text) for synergy / cost analysis -------------------- #
@_file_memo("DEFAULT_CSV", "POOL_CSV")
def load_card_data():
    """name_lower -> {'name','type','text','colors','power','toughness'} from
    card-library.csv then card-pool.csv.

    The pool fills in oracle text/type for unowned WIP cards so analysis works on
    decks that aren't fully owned yet. `power`/`toughness` are RAW strings (Magic
    prints `*`, `1+*`, `X`), only present on pool rows — the library CSV has no such
    columns — and are '' when unknown. Parse via `lib.card_power`, never int() them.
    """
    data = {}
    for path in (DEFAULT_CSV, POOL_CSV):
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                n = (r.get("Card Name") or "").strip().lower()
                if not n:
                    continue
                if n not in data:
                    data[n] = {"name": (r.get("Card Name") or "").strip(),
                               "type": r.get("Type") or "", "text": r.get("Card Text") or "",
                               "colors": r.get("Color(s)") or "",
                               "power": r.get("Power") or "",
                               "toughness": r.get("Toughness") or ""}
                    data.setdefault(n.split(" // ")[0], data[n])
                elif not data[n]["power"] and (r.get("Power") or r.get("Toughness")):
                    # P/T is a POOL-only column — card-library.csv has no such fields.
                    # Because the library is read FIRST and wins, every card you OWN
                    # would otherwise read as unknown-P/T, i.e. the new data would be
                    # missing on exactly the cards most likely to be graded. Backfill
                    # from the pool without disturbing the library's type/text/colors,
                    # which stay authoritative.
                    data[n]["power"] = r.get("Power") or ""
                    data[n]["toughness"] = r.get("Toughness") or ""
    return data


def creature_subtypes(type_line):
    """Creature subtypes (after the em dash) across all faces of a type line."""
    subs = []
    for face in type_line.split("//"):
        if "creature" in face.lower() and "—" in face:
            subs += face.split("—", 1)[1].split()
    return subs


@_file_memo("MANA_CSV")
def load_keywords():
    """name_lower -> [keywords] from card-mana.csv (Scryfall's per-card list)."""
    kw = {}
    if not os.path.exists(MANA_CSV):
        return kw
    with open(MANA_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            raw = (r.get("Keywords") or "").strip()
            if n:
                kw[n] = [k.strip().lower() for k in raw.split(";") if k.strip()]
    return kw


# Keywords whose real cost is LOWER than the printed mana value (alt/reduced cost).
CHEAPER_KW = {
    "warp", "sneak", "plot", "convoke", "affinity", "delve", "improvise",
    "emerge", "spectacle", "evoke", "offering", "surge", "miracle", "foretell",
}
# Keywords that gate an ability or mode behind an ADDITIONAL / activated cost —
# so the card does more than its base cost implies (and you pay for it).
GATED_KW = {
    "kicker", "multikicker", "bargain", "gift", "spree", "teamwork", "saddle",
    "station", "power-up", "boast", "channel", "craft", "exhaust", "disguise",
    "cycling", "landcycling", "typecycling", "basic landcycling", "plainscycling",
    "islandcycling", "swampcycling", "mountaincycling", "forestcycling",
    "escape", "embalm", "eternalize", "flashback", "jump-start", "unearth",
    "reconfigure", "equip", "level up", "adapt", "outlast", "monstrosity",
}
CHEAPER_TEXT = [("less to cast", "cost reduction"),
                ("without paying its mana cost", "free cast"),
                ("as though it had flash", "conditional flash")]


def x_cost_cards(cards, carddata, mana):
    """Nonland cards whose printed cost contains {X} -> [(name, cost)], sorted.

    The curve, `avg_mv` and the early-drop count all read `mana_value`, which counts
    X as 0 because that is what the rules say off the stack. That is correct for
    castability and for cast-on-curve probability — you really can cast Wildwood
    Scourge for {G} — but it makes an {X} spell look like a ONE-DROP on the curve
    when you will realistically pay three to five for it.

    The distortion runs in BOTH directions and bit deck 50a twice: adding two {X}
    spells made avg MV appear to drop 3.85 -> 3.70, and removing one made it appear
    to rise 3.55 -> 3.76. Neither move changed the real curve much. Report-only —
    this deliberately does NOT feed `deck_quality_vector` or `tier_band`, because a
    new term there would silently re-grade the whole roster.
    """
    out, seen = [], set()
    for _q, n, _s, _c in cards:
        if n.lower() in BASICS or n in seen:
            continue
        d2 = carddata.get(n.lower())
        if not d2 or "Land" in _primary_type(d2["type"]):
            continue
        entry = mana.get(n.lower())
        cost = (entry[0] if entry else "") or ""
        if "{X}" in cost.upper():
            seen.add(n)
            out.append((n, cost))
    return sorted(out)


def classify_cost(keywords, text):
    """Return (cheaper_reasons, gated_reasons) for a card's cost profile."""
    kset = set(keywords or [])
    t = (text or "").lower()
    cheaper = sorted(kset & CHEAPER_KW)
    for phrase, label in CHEAPER_TEXT:
        if phrase in t:
            cheaper.append(label)
    gated = sorted(kset & GATED_KW)
    return list(dict.fromkeys(cheaper)), list(dict.fromkeys(gated))


# Functional-role heuristics: bucket a nonland card by the JOB it does for the
# deck (interaction, card advantage, ramp, ...) by pattern-matching oracle text.
# This is intentionally heuristic — a card can fill several roles, and single
# "draw a card" cantrips are NOT counted as card advantage (they're card-neutral,
# the same reason Spellbook Seeker reads as filtering, not advantage). The point
# is to MEASURE the "light on removal / card advantage" judgment the /tune-deck
# scorecard used to make by eye, not to be authoritative.
ROLE_ORDER = ["Removal (spot)", "Sweeper", "Counter", "Card advantage",
              "Ramp / fixing", "Reanimation", "Payoff / engine", "Burn / drain",
              "Lifegain", "Cost reduction / cheat", "Team pump / anthem",
              "Protection / trick", "Recursion"]
# A permanent-type LIST as MTG templates it: "creature", "artifact or enchantment",
# "artifact, enchantment, or creature with flying". The removal patterns used to spell
# out a handful of fixed combinations by hand, so anything outside that list matched
# NOTHING and the card read as having no removal role at all. Verified misses:
#   Origin of Metalbending / Seedship Impact — "Destroy target artifact or enchantment"
#   Broken Wings                             — "Destroy target artifact, enchantment,
#                                               or creature with flying"  → zero roles
# Those three all count toward `_NONCREATURE_ANSWER_CUES` (the "can it answer a
# planeswalker/enchantment/artifact" test) already, so the codebase treated them as
# answers everywhere EXCEPT the count the tier floor grades on. One list-aware pattern
# replaces the hand-kept combinations, so a new templating can't slip through again.
_PERM_TYPE = (r"(?:nonland permanent|artifact creature|artifact|enchantment|creature|"
              r"permanent|planeswalker|spacecraft|vehicle|land)")
_PERM_TYPE_LIST = rf"{_PERM_TYPE}s?(?:,? (?:or |and )?{_PERM_TYPE}s?)*"

_ROLE_PATTERNS = {
    "Removal (spot)": [
        # destroy / exile a targeted permanent, including a comma-or list of types, and
        # allowing the adjectives MTG puts before the type ("target ATTACKING creature",
        # "target TAPPED creature") — the old hand-kept alternation listed some of those
        # spellings explicitly, so the list-aware rewrite has to keep them or it would
        # LOSE coverage it previously had (caught by a roster-wide before/after diff:
        # decks 15 and 16 each dropped an interaction piece on the first draft).
        # NOTE the doubled braces: this is an f-string, so a bare {0,2} is parsed as a
        # replacement field and silently compiles to the literal text "(0, 2)". That is
        # exactly what happened on the first draft — every "destroy target creature" in
        # the collection stopped matching and 46 decks lost interaction. Caught only by
        # the roster-wide before/after diff, which is why that diff is worth running.
        rf"(?:destroy|exile) (?:up to \w+ )?target (?:[a-z-]+ ){{0,2}}?{_PERM_TYPE_LIST}",
        # SPLIT TEMPLATE: the target is named in one sentence and the destroy verb lands
        # in a later one, with an anaphor standing in for the target — Quag Feast reads
        # "CHOOSE target creature, planeswalker, or Vehicle. Mill two cards, then destroy
        # THE CHOSEN PERMANENT if …". The pattern above needs `destroy|exile` immediately
        # before `target`, so nothing matched and the card scored ZERO roles: it was
        # absent from the interaction count the tier floor grades on, not merely from the
        # noncreature-answer profile. Anchoring on the anaphor is precise on its own —
        # "destroy/exile the chosen <permanent>" only ever appears in removal text.
        r"(?:destroy|exile) the chosen (?:permanent|creature|card|artifact|enchantment)",
        r"deals? \d+ damage to (?:target|any target|another target)",
        r"deals? \d+ damage to up to \w+ target",
        # any "fight" is removal (Novel Nunchaku "fights up to one target", Longstalk
        # Brawl "fight each other") — the old pattern only caught "fights target".
        r"\bfights?\b|creatures? fight",
        r"deals damage equal to (?:twice )?.{0,20}?power to target (?:creature|creature or planeswalker|attacking)",
        # SCALING damage whose size is anything OTHER than a power reference. The pattern
        # above hard-codes "power", so Combustion Technique — "deals damage equal to 2 plus
        # the number of Lesson cards in your graveyard to target creature" — matched
        # nothing and scored ZERO roles, in the deck that PROTECTS it as a marquee payoff.
        # Same failure shape as Quag Feast above: a removal template no pattern read, so
        # the card was absent from the interaction count the tier floor grades on. `[^.]`
        # keeps the span inside one sentence so an unrelated later clause can't be swept in.
        # The `(?!player|opponent)` guard is load-bearing: "deals damage equal to its power
        # to target PLAYER" (Gravitic Punch, Sif's Spearmaster, Runebound Wolf) is reach,
        # not an answer, and a roster sweep of the first draft showed that was the ONLY
        # false-positive class among 116 newly-matched cards.
        r"deals damage equal to [^.]{0,80}?to (?:any target|target (?!player|opponent)\w+)",
        # DIVIDED damage — the Fiery Confluence / Death to Our Enemies template. Every
        # fixed-damage pattern above expects "to target"/"to any target" immediately after
        # the number, and this one says "divided as you choose among …" instead.
        r"deals? \d+ damage divided as you choose among",
        # -N/-N or -X/-X shrink on a targeted creature (incl. "creature an opponent
        # controls gets -X/-X" — Cloud of Darkness, Wick's Patrol).
        r"target creature (?:an opponent controls )?gets -[0-9x]",
        r"creature an opponent controls gets -[0-9x]",
        # BOUNCE. Note `owner'?s?` — MTG templates this as "to its OWNER'S hand", and the
        # original pattern spelled the alternation `(?:owner|their) hand`, which requires
        # the literal text "owner hand". So it matched NOTHING: every unconditional bounce
        # spell in the collection (Boomerang Basics, Into the Flood Maw, ...) scored zero
        # roles for the entire life of the pattern, while the broad audit cue DID fire —
        # which is why bounce dominated the roster-wide "possible under-count" list. The
        # type is a full `_PERM_TYPE_LIST` so "nonland permanent" is covered alongside
        # "creature", and `[^.]` keeps the span inside one sentence.
        rf"return (?:up to \w+ )?target (?:[a-z-]+ ){{0,2}}?{_PERM_TYPE_LIST}"
        rf"[^.]{{0,60}}?(?:owner'?s?|their) hand",
        # EDICT. Sacrifice-a-creature-of-their-choice is removal (it answers hexproof),
        # and it sat in the broad audit cue while missing from this list entirely.
        r"(?:target|each) (?:player|opponent) sacrifices a creature",
        r"(?:target|each) (?:player|opponent) sacrifices a permanent",
        # X-damage: the fixed patterns above require a DIGIT, so "deals X damage to target
        # creature" scored nothing (Hell to Pay).
        r"deals? x damage to (?:target|any target|up to \w+ target)",
        # Tuck via an Aura — same class as the activated-ability tuck already covered.
        r"enchanted creature'?s owner shuffles it into their library",
        r"enchanted creature can't attack or block",
        # Removal by TUCKING a creature into a library. It leaves the battlefield, so
        # it is a real answer, but no destroy/exile/damage/-N-N pattern saw it:
        # Floodpits Drowner's "{1}{U}, {T}: Shuffle this creature and target creature
        # with a stun counter on it into their owners' libraries" scored ZERO roles,
        # which is why an earlier tier note wrongly wrote it off as "taps and stuns
        # rather than answers" (session finding — the same card twice).
        r"shuffle[^.]{0,80}?target (?:creature|permanent)[^.]{0,60}?librar",
        r"target creature[^.]{0,80}?into (?:their|its) (?:owner'?s? )?librar",
    ],
    "Sweeper": [r"destroy all", r"exile all", r"all creatures get -",
                r"each (?:other )?creature (?:gets|deals|is|you don't control)",
                # one-sided / opponent-only wraths ("creatures your opponents control
                # get -2/-2" — Massacre Wurm) the "all creatures" pattern misses.
                r"creatures (?:you don't control|your opponents control|target player controls) get -",
                # scalable / conditional wipes the fixed patterns above miss
                r"creature with mana value.{0,20}?or less.{0,40}?destroy",
                r"destroy those creatures",
                r"deals? \d+ damage to each (?:other )?creature",
                # "each player sacrifices all other creatures they control" (Bringer of
                # the Last Gift) is a wrath by another name.
                r"each player sacrifices all (?:other )?creatures"],
    # "counter up to one target spell unless…" (Repulsive Mutation) matched neither
    # this pattern NOR the broad coverage net below, so it scored zero roles AND was
    # never flagged as an under-read — the worst case, a miss invisible to the very
    # audit that exists to catch misses (session finding).
    "Counter": [r"counter (?:up to \w+ )?target", r"counter (?:that|the chosen) spell"],
    # Surfaced while testing the lexicon unification: "five" and "half X" were in
    # neither the role pattern nor the audit cue, so Wan Shi Tong, Librarian ("draw
    # half X cards, rounded down") was uncounted AND unflagged — the same
    # missed-by-both hole as Repulsive Mutation, on the card-advantage axis.
    "Card advantage": [r"draws? (?:two|three|four|five|half x|x|that many) cards?",
                       r"draw a card for each", r"draws? cards? equal to",
                       # A REPEATABLE single draw accrues advantage; the cantrip rule is
                       # about ONE-SHOT single draws. Phyrexian Arena reads as a cantrip
                       # to a pattern that only counts how many cards one resolution
                       # draws, which is why deck 42's card-advantage line said 1.
                       #
                       # Repeatability is the whole test, and it comes in two templatings
                       # — the first version of this pattern only read ONE of them. A
                       # PHASE trigger recurs every turn, and "upkeep" was hardcoded while
                       # Magic puts the same effect on the end step, the draw step and
                       # combat just as often (Haliya, Guided by Light draws at the
                       # beginning of your END STEP). And a "WHENEVER" trigger recurs by
                       # construction — Exemplar of Light draws every turn it gets a
                       # counter. Neither was matched here NOR by the broad `_CA_CUES`
                       # net, so both cards were the "missable by BOTH" failure the
                       # superset comment below exists to prevent: they got a role
                       # (Payoff, Lifegain), so they were not `unclassified` either, and
                       # deck 46 reported card advantage 1 against a real 3 with the
                       # uncertainty channel silent.
                       #
                       # "When" vs "WHENEVER" is the load-bearing distinction and it is
                       # Magic's own templating rule: "When this creature enters, draw a
                       # card" is a one-shot ETB cantrip (Inspiring Overseer) and stays
                       # excluded; "Whenever X, draw a card" recurs. Matching a bare
                       # "draw a card" would have swept every cantrip in the format into
                       # card advantage and inverted the rule this pattern implements.
                       r"at the beginning of (?:your|each|the) "
                       r"(?:upkeep|end step|draw step|combat|precombat main phase)"
                       r"[^.]{0,60}?draws? a card",
                       # The draw must fall AFTER the trigger's comma. Magic templates a
                       # triggered ability as "Whenever <condition>, <effect>", so the
                       # comma is what separates a card that DRAWS from a card that CARES
                       # about drawing: "Whenever you draw a card, this creature gets
                       # +1/+1" (Chasm Skulker, Orcish Bowmasters, Queza — 45 of them on
                       # the pool) puts "draw a card" in the CONDITION, and a naive
                       # `whenever .* draw a card` swept every one into card advantage —
                       # scoring a draw-payoff as a draw, which is backwards.
                       r"\bwhenever\b[^.,]{0,80}?, [^.]{0,60}?draws? a card",
                       r"\binvestigate\b",
                       # A CLUE TOKEN *is* a delayed draw ("{2}, Sacrifice this token:
                       # Draw a card"), and `investigate` above is the KEYWORD form of
                       # exactly that. But plenty of cards spell the token out instead of
                       # using the keyword — The Mechanist, Aerial Artisan makes a Clue per
                       # noncreature spell and scored Payoff/engine only, so a deck built
                       # on it still read card advantage 0.
                       r"create (?:a|\w+|that many) clue tokens?",
                       # IMPULSE. "Exile the top card of your library. You may play that
                       # card this turn" is a card you would not otherwise have had — the
                       # same advantage a draw gives, one zone over. Nothing matched it:
                       # Zuko, Exiled Prince scored ZERO roles despite a repeatable {3}
                       # impulse ability, and it is a whole deck archetype (deck 24, deck
                       # 45) that the card-advantage axis could not see. `[^.]` keeps the
                       # span inside the sentence pair so an unrelated later clause cannot
                       # be swept in.
                       r"exile the top card of your library[^.]{0,40}\. you may play (?:it|that card)",
                       r"exile the top \w+ cards? of your library[^.]{0,60}\. (?:you may play|until )"],
    "Ramp / fixing": [r"search your library for .{0,30}?\bland",
                      r"\{t\}: add \{",
                      r"put (?:a|that|those|up to \w+).{0,40}?land.{0,40}?onto the battlefield"],
    # Return a permanent to the BATTLEFIELD from the graveyard (higher value than
    # to-hand recursion). Catches "in your graveyard … return … to the battlefield"
    # phrasing, which the old "from your graveyard" Recursion pattern silently missed
    # (Too Evil to Stay Dead, Bringer of the Last Gift, sagas, etc.).
    "Reanimation": [
        r"(?:card|creature|permanent).{0,80}?in your graveyard.{0,80}?to the battlefield",
        r"return .{0,60}?(?:creature|permanent|card).{0,40}?to the battlefield",
        r"put .{0,50}?(?:creature|card|permanent).{0,60}?onto the battlefield",
    ],
    # Repeatable/triggered engines — the death, ETB-matters, lifegain and
    # leaves-play payoffs the role map used to score as "no functional role"
    # (Judge Magister Gabranth, Rot Farm Mortipede, aristocrats/lifedrain bodies).
    "Payoff / engine": [
        r"whenever .{0,60}?dies",
        r"whenever (?:a|another|one or more) .{0,40}?(?:enters|leave|leaves|die|dies)",
        r"whenever you gain life",
        r"whenever you cast",
        r"put a \+1/\+1 counter on .{0,60}?whenever",
        r"\bwhenever\b.{0,80}?(?:draw a card|put a \+1/\+1 counter|create|each opponent loses)",
    ],
    # Direct damage / life loss to a player — reach & finishers the fixed-number
    # removal pattern misses (Cat-Gator, drain effects).
    "Burn / drain": [
        r"deals damage equal to .{0,60}?(?:any target|a player|target player|each opponent|that player)",
        r"(?:each opponent|target opponent|any opponent|that player|each player) loses \d",
        r"deals? \d+ damage to each opponent",
        r"loses life equal to",
    ],
    # `gain(s) life equal to ...` (Exsanguinate, Corrupt, Sifter Wurm — 68 pool cards)
    # was in neither this pattern nor the tag model; the tag half was fixed with the
    # `pay life` work and this is the role half, so the two agree on the phrase.
    "Lifegain": [r"\blifelink\b", r"you gain \d+ life", r"gain \d+ life",
                 r"gains? life equal to"],
    # Cost reducers / free-cast enablers — the value that makes a nominally
    # expensive card cheap (Diamond Weapon, affinity/convoke, cascade cheats).
    "Cost reduction / cheat": [
        # Magic writes "This spell costs {1} less TO CAST for each artifact you
        # control", so a `costs {1} less for each` pattern (the words adjacent)
        # matched zero of 15.8k pool cards — the third instance of this project's
        # signature bug: a regex that compiles fine and can never fire. Found by
        # `check_patterns.py` on its first run. Harmless in effect (the general
        # pattern below already covers every one of the 155 cards it was meant
        # for), which is exactly why it survived: a dead pattern hiding behind a
        # live one changes no count and shows up in no diff.
        r"costs? \{[0-9x]+\} less",
        r"\baffinity\b", r"\bconvoke\b", r"\bimprovise\b", r"\bcascade\b",
        r"without paying its mana cost",
    ],
    "Team pump / anthem": [r"(?:other )?creatures you control get \+"],
    "Protection / trick": [r"\bhexproof\b", r"\bindestructible\b", r"protection from",
                           r"gets \+\d+/\+\d+ until end of turn"],
    "Recursion": [r"from your graveyard", r"card in your graveyard",
                  r"return .{0,40}?to your hand"],
}
_ROLE_COMPILED = [(label, [re.compile(p) for p in _ROLE_PATTERNS[label]])
                  for label in ROLE_ORDER]
_ROLE_COMPILED_MAP = dict(_ROLE_COMPILED)

# The roles that make a card "interaction" for the resilience axis the tier floor
# grades on. Defined HERE, next to the patterns, because the coverage-audit net below
# is built from them — it used to sit ~1000 lines later, which is how the net and the
# classifier drifted apart in the first place.
_INTERACTION_ROLES = {"Removal (spot)", "Sweeper", "Counter"}

# "draw N, then discard N" is a LOOT — card-NEUTRAL filtering, not card advantage, for
# exactly the reason a single-draw cantrip isn't counted (see ROLE_ORDER's note). Kiora,
# the Rising Tide's "draw two cards, then discard two cards" used to score +1 card
# advantage, which both inflated her value when the deck was graded and made cutting her
# register as a regression the quality guard reported but that wasn't real (session
# finding). Only an EQUAL, adjacent draw/discard pair is filtered — a genuinely
# net-positive "draw three cards. Discard a card." is untouched, and connive (draw 1,
# discard 1) never counted in the first place.
_LOOT_RE = re.compile(
    r"draws? (two|three|four|five|x|that many) cards?,? (?:then )?"
    r"discards? (?:\1|that many) cards?")

# Real PROTECTION for a permanent you control — deliberately NARROWER than the
# "Protection / trick" role, which lumps a combat pump ("gets +2/+2 until end of turn")
# in with an actual answer to removal.
#
# This axis exists because its absence was the single biggest weakness of an all-in
# single-threat deck and NO view could see it: `stats`, `quality` and `tier` all count
# interaction and card advantage, and nothing asked "can I protect the thing I win
# with?" It was found by an ad-hoc grep, not by any tool (session finding).
#
# `regenerate` is deliberately absent: "It can't be regenerated" is boilerplate on
# removal spells, so keying on the word would score half the removal in the format as
# protection. Prefer under-counting to a wrong count on a measured axis.
_PROTECTION_RE = re.compile(
    r"\bhexproof\b|\bindestructible\b|\bward\b|protection from"
    r"|can'?t be the target of (?:spells|abilities)"
    r"|counter target spell that targets"
    r"|\bphases? out\b")


# "power 4 or greater" style conditions — the class of card that was ungradeable while
# the repo stored no P/T. The payoff reads unconditional in a synergy model ("draws you
# cards!") but only fires off bodies that actually meet the bar ON ENTRY, and a counters
# deck full of X-creatures printed 0/0 meets it far less often than it looks.
_POWER_THRESHOLD_RE = re.compile(
    r"\b(power|toughness) (\d+) or (?:greater|more)\b", re.I)
_POWER_THRESHOLD_THIN = 0.30       # <30% of creatures qualifying = worth flagging

# The flag counts YOUR creatures against the bar, so it only means anything when the
# clause is about creatures YOU CONTROL *and* is a PER-CREATURE threshold. Two shapes
# break that, and both were firing — 16 of the roster's 27 flags, 59%, were false:
#
#   * REMOVAL / opponent-facing (83 pool cards). "Destroy target creature with power 4
#     or greater" (Sandbenders' Storm, Battle Menu, Valorous Stance) measures the wrong
#     board entirely — the card wants THEIR creatures big. For a sweeper like Dusk
#     ("destroy all creatures with power 3 or greater") few of your own qualifying is
#     the whole POINT, so the warning inverted the card's reading. Same for "can't be
#     blocked by creatures with power 3 or greater", which is about their blockers.
#   * "TOTAL power/toughness N or greater" (153 pool cards). Teamwork ("tap any number
#     of creatures you control with total power 4 or more") and Betor's "if creatures
#     you control have total toughness 10 or greater" are SUMS: three 2/2s satisfy
#     "total power 4". Counting creatures at printed power >= 4 is the wrong
#     arithmetic, not a conservative read of the right one — deck 34 was told 0 of its
#     19 creatures could pay a teamwork cost it can pay trivially.
#
# Opt IN on "you control" rather than blacklisting the bad shapes: Magic's templating
# puts "you control" directly before "with power N", and an affirmative test can't be
# silently widened by a phrasing nobody has written yet. The cost is losing a scope
# spelled some other way (Gwenna's "whenever you cast a creature spell with power 5 or
# greater"), which is the right direction to err — this list exists to be read
# card-by-card, so a false cue is the expensive kind.
_POWER_SCOPE_MINE_RE = re.compile(r"you control(?:[^.]{0,25})?$", re.I)
_POWER_SCOPE_TOTAL_RE = re.compile(r"\btotal\s+$", re.I)
_POWER_SCOPE_BACK = 40


def power_threshold_flags(cards, carddata):
    """[(payoff_name, attr, N, qualifying_copies, creature_copies)] for each card whose
    text keys on "power/toughness N or greater", with how many of the deck's creatures
    meet that bar on their PRINTED stats. Only flags a payoff the deck under-supports.

    Printed P/T only — a card that grows after it enters (counters, anthems, an equip)
    still reads by its printed value, which is exactly right for an ENTERS trigger and
    conservative for anything else. Creatures whose P/T isn't a number (`*`, `X`) are
    counted as NOT qualifying and reported separately by the caller if needed, since
    guessing would re-introduce the invented-fact problem `lib.card_power` avoids.

    Scoped: only a clause about creatures YOU CONTROL, and only a per-creature bar —
    see `_POWER_SCOPE_MINE_RE` for the removal / "total power" shapes this used to
    misread and why the test opts in rather than blacklisting."""
    creatures = []
    for q, n, _s, _c in cards:
        cd = carddata.get(n.lower())
        if not cd or "Creature" not in _primary_type(cd.get("type") or ""):
            continue
        creatures.append((q, cd))
    total = sum(q for q, _ in creatures)
    out = []
    if not total:
        return out
    seen = set()
    for q, n, _s, _c in cards:
        cd = carddata.get(n.lower())
        if not cd:
            continue
        text = cd.get("text") or ""
        for m in _POWER_THRESHOLD_RE.finditer(text):
            back = text[max(0, m.start() - _POWER_SCOPE_BACK):m.start()]
            if _POWER_SCOPE_TOTAL_RE.search(back):
                continue                      # a SUM across creatures, not a per-body bar
            if not _POWER_SCOPE_MINE_RE.search(back):
                continue                      # removal / opponent-facing — wrong board
            attr, bar = m.group(1).lower(), int(m.group(2))
            key = (cd["name"], attr, bar)
            if key in seen:
                continue
            seen.add(key)
            qualify = sum(cq for cq, ccd in creatures
                          if (card_power(ccd.get(attr)) or -1) >= bar)
            if qualify / total < _POWER_THRESHOLD_THIN:
                out.append((cd["name"], attr, bar, qualify, total))
    return out


# DECK SHAPE. The single question this toolkit could never answer: "does this deck win
# WIDE or TALL, FAST or SLOW, on one threat or many?" Every distinctness call needs it,
# and answering it by reading `#: archetype:` headers produced the worst misread of the
# session — deck 30 was called a wide deck from its header while the question was
# whether a TALL counters plan duplicated it. Themes can't answer this: "counters" is
# the same tag whether they all go on one creature or spread across twelve.
_WIDE_CUES = [re.compile(p, re.I) for p in [
    r"create (?:a|an|two|three|four|five|\w+|x) .{0,60}?creature tokens?",
    r"creatures you control get \+", r"for each creature you control",
    r"creatures you control have", r"populate\b", r"\bconvoke\b",
    r"whenever (?:another )?(?:a )?creature you control enters",
]]
# TALL is about CONCENTRATION, not counters. The first draft keyed on "put a +1/+1
# counter on target creature" and "target creature gets +N/+N" — which read deck 4
# (27 creatures, a WIDE value board) as tall, because a single counter is a wide
# deck's glue too. Only AMPLIFIERS count: effects that make one body disproportionate.
_TALL_CUES = [re.compile(p, re.I) for p in [
    r"double (?:the number of )?.{0,30}?(?:\+1/\+1 counters?|counters|power)",
    r"twice (?:that much|that many|its power)",
    r"triple .{0,20}?power",
    r"equipped creature gets \+", r"enchanted creature gets \+",
    r"gets \+x/\+x", r"where x is (?:the number of|its|this creature'?s) ",
    r"base power and toughness \d+/\d+",
]]


def deck_shape(cards, carddata, mana=None):
    """Structural shape of a deck, measured from oracle text rather than tags.

    Returns a dict with WIDE / TALL scores (quantity-weighted card counts), creature
    and token counts, evasion, curve, and a plain-English verdict. It is a SHAPE read,
    not a quality read — a wide deck is not better or worse than a tall one; the point
    is that two decks sharing every theme tag can be opposite decks."""
    wide = tall = creatures = evasive = 0
    mvs, wide_cards, tall_cards = [], [], []
    for q, n, _s, _c in cards:
        if n.lower() in BASICS:
            continue
        cd = carddata.get(n.lower())
        if not cd:
            continue
        tline = cd.get("type") or ""
        if "Land" in _primary_type(tline):
            continue
        text = cd.get("text") or ""
        if "Creature" in _primary_type(tline):
            creatures += q
        if re.search(r"\bflying\b|\bmenace\b|can't be blocked|\btrample\b|\bfear\b|\bshadow\b",
                     text, re.I):
            evasive += q
        if any(p.search(text) for p in _WIDE_CUES):
            wide += q
            wide_cards.append(cd.get("name") or n)
        if any(p.search(text) for p in _TALL_CUES):
            tall += q
            tall_cards.append(cd.get("name") or n)
        if mana:
            e = mana.get(n.lower())
            if e and e[1] is not None:
                mvs += [e[1]] * q
    avg_mv = round(sum(mvs) / len(mvs), 2) if mvs else 0.0
    # A verdict only when one axis clearly leads — a deck can legitimately be neither.
    # Creature DENSITY is its own signal: a deck fielding 25+ creature copies is wide
    # almost by construction, and one fielding under ~14 cannot go wide whatever its
    # text says. Fold it in rather than trusting the text scan alone.
    if creatures >= 22:
        wide += 2
    elif creatures <= 14:
        tall += 2
    lead = abs(wide - tall)
    if lead < 2:
        axis = "BALANCED / neither" if (wide or tall) else "no board-growth axis"
    elif wide > tall:
        axis = "WIDE — many bodies, effects that scale with creature COUNT"
    else:
        axis = "TALL — few bodies, effects that scale one creature UP"
    if avg_mv and avg_mv <= 2.5:
        speed = "FAST curve"
    elif avg_mv >= 3.3:
        speed = "SLOW curve"
    else:
        speed = "MIDRANGE curve"
    return {"wide": wide, "tall": tall, "creatures": creatures, "evasive": evasive,
            "avg_mv": avg_mv, "axis": axis, "speed": speed,
            "wide_cards": sorted(set(wide_cards)), "tall_cards": sorted(set(tall_cards))}


def protection_effects(text):
    """True if a card grants/has a real protection effect (ward, hexproof,
    indestructible, protection from, untargetable, a counter-that-targets). Counts the
    CARD, not its reach — a self-only ward on an irrelevant body still counts, which is
    why the deck-level check below only flags an outright ZERO rather than scoring a
    thin count as adequate."""
    return bool(_PROTECTION_RE.search(_norm_role_text(text)))

# Mechanics whose value depends on the DECK (colors of mana available, board
# state), not the card in isolation — the cuts/grade step must check them against
# the specific deck, never rank them from the label alone (e.g. converge is dead
# in a mono-color deck; affinity/X scale with your board).
_CONTEXT_PATTERNS = {
    "converge": [r"\bconverge\b", r"for each color of mana spent"],
    "devotion": [r"\bdevotion\b"],
    "affinity": [r"\baffinity\b"],
    "convoke": [r"\bconvoke\b"],
    "improvise": [r"\bimprovise\b"],
}
_CONTEXT_COMPILED = {k: [re.compile(p) for p in v] for k, v in _CONTEXT_PATTERNS.items()}

# COST-AS-UPSIDE. A card's additional cost or drawback reads as a downside in isolation
# and every scoring model here grades cards in isolation — but in the matching deck the
# same clause is an ENGINE TRIGGER. CLAUDE.md warns humans about this in prose ("ask what
# does this do *here*"); nothing detected it, so a card whose cost is secretly an upside
# sorted like a card with a real drawback. Observed cases:
#   • Chocobo Kick's "Kicker — Return a land you control to its owner's hand" in a
#     LANDFALL deck: replaying the land re-triggers every landfall payoff, so paying the
#     kicker is pure profit.
#   • Broodguard Elite's Warp (self-exile at end of turn) in a COUNTERS deck: leaving the
#     battlefield is what moves its counters onto your threat.
#   • A "sacrifice a creature/artifact" cost in a sacrifice/aristocrats deck.
# Each entry maps a cost pattern → the deck themes that turn it into an upside. This is a
# FLAG for a human read, never a score change — the same posture as `⚠ scales w/`, and
# for the same reason: the signal is real but too fuzzy to move a ranking on its own.
_COST_UPSIDE = [
    (re.compile(r"return a land you control to its owner'?s hand", re.I),
     {"landfall", "lands", "ramp"}, "kicker returns a land → re-triggers landfall"),
    (re.compile(r"\bwarp\b|exile this creature at the beginning of the next end step", re.I),
     {"counters", "etb", "blink"}, "warp self-exile → leaves-play / re-ETB value"),
    (re.compile(r"when this .{0,30}?leaves the battlefield", re.I),
     {"counters", "sacrifice", "blink"}, "leaves-play trigger → the 'drawback' is the payoff"),
    (re.compile(r"as an additional cost.{0,60}?sacrifice", re.I),
     {"sacrifice", "food", "tokens", "aristocrats"}, "sacrifice cost → feeds your outlets"),
    (re.compile(r"\bdiscard (?:a|one|two|that) card", re.I),
     {"graveyard", "reanimator", "recursion", "madness"}, "discard cost → fills the yard"),
]


# Themes that are only a BENEFIT when the deck is built to reward them; otherwise the
# same interaction is a COST. Filling your graveyard is value in a reanimator deck and
# pure damage in a control deck that needs its counterspells in the library — but a
# theme-overlap model sees one tag either way.
#
# The observed miss: Genesis Wave read KEY for deck 40 (Simic ramp-CONTROL) purely on a
# `graveyard` match — i.e. it scored highly BECAUSE it mills you, which there is the
# reason not to play it (15 of 34 nonlands, including Finale of Revelation and the whole
# counterspell suite, get binned). The fix reuses machinery that already exists rather
# than adding a model: `engine_roles` knows which cards are graveyard PAYOFFS, so the
# theme only counts as a fit when the deck actually fields some.
_COST_THEMES = {
    "graveyard": "graveyard",
    "mill": "graveyard",
    "discard": "graveyard",
    "self-mill": "graveyard",
}
_COST_THEME_MIN_PAYOFFS = 2


def _drop_cost_themes(shared, cards, carddata):
    """Remove cost-shaped themes from a shared-theme list unless the deck fields at least
    `_COST_THEME_MIN_PAYOFFS` cards that PAY THEM OFF. Themes with no cost interpretation
    pass through untouched."""
    risky = {t for t in shared if t.lower() in _COST_THEMES}
    if not risky:
        return shared
    payoffs = {}
    for q, n, _s, _c in cards:
        cd = carddata.get(n.lower())
        if not cd:
            continue
        for theme, sides in engine_roles(cd.get("text") or "").items():
            if "payoff" in sides:
                payoffs[theme] = payoffs.get(theme, 0) + q
    keep = []
    for t in shared:
        engine = _COST_THEMES.get(t.lower())
        if engine and payoffs.get(engine, 0) < _COST_THEME_MIN_PAYOFFS:
            continue      # the deck pays the cost but collects no reward — not a fit
        keep.append(t)
    return keep


# ── Zone conflicts: a fine card that fights your own engine ────────────────────────
# The MIRROR of `cost_upside_flags` below. That flag catches a drawback that is secretly
# an UPSIDE in this deck; nothing caught an upside that is secretly a DRAWBACK here, and
# that shape shipped into two finished decks. Strategic Betrayal ("Target opponent exiles
# a creature they control and their graveyard") and Pit of Offerings ("exile up to three
# target cards from graveyards") both read as perfectly good cards — and both empty a
# graveyard that four heist cards in the same deck need FULL. `cuts` ranked Strategic
# Betrayal second-weakest, so the shortlist saw it; only a full-text read explained WHY.
# A model that grades a card in isolation structurally cannot see this.
#
# CLAUDE.md states the rule for humans — "when a deck DEPENDS on a zone being populated,
# audit every card that empties it" — and this detects that pairing.
#
# The patterns are built from the POOL's real phrasings, not from strings written to
# match them (the lesson the `heist` tag's four pattern bugs taught). Two findings from
# that survey shape the design:
#   * `exile this card from YOUR graveyard` is on 90 pool cards and is escape / flashback
#     / delve COST — a graveyard USER, the opposite of hate. Anything scoped to your own
#     yard is excluded outright.
#   * A heist card exiles an opponent's graveyard IN ORDER TO CAST FROM IT (Tinybones
#     "exile it from their graveyard with a stash counter", Hama, Azula). Those are the
#     deck's ENGINE, and a naive exile+graveyard rule flags them as hostile to
#     themselves. `tag_synergies.is_heist_text` already separates "casts cards you don't
#     own" from real hate, so the emptier test reuses it rather than adding a model.
_ZONE_MIN_DEPENDENTS = 2   # one card is a singleton, not a plan worth protecting

# Emptied scope = the OPPONENT's yard only.
_GY_HATE_OPP_RE = re.compile(
    # A GAP before "their graveyard" is required, not optional: Strategic Betrayal reads
    # "Target opponent exiles a creature they control AND their graveyard", so the verb
    # and the zone sit at opposite ends of the clause. Demanding them adjacent missed the
    # single card this detector was built for — found by running it, not by reading it.
    r"exiles?[^.]{0,60}?\b(?:their|his or her) graveyard"
    r"|exile (?:target |each )?(?:player'?s?|opponent'?s?) graveyard"
    # "that player's graveyard" (Hama) is as common as "target player's" and was absent.
    r"|exile[^.]{0,50}?\bfrom (?:an? opponent'?s?|target player'?s?|that player'?s?|their) graveyard", re.I)
# Emptied scope = EVERY yard at once, with no choice — the only shape that can hit YOUR
# graveyard against your will.
_GY_HATE_ALL_RE = re.compile(
    r"exile (?:all|each) graveyards?"
    r"|exile all cards? from (?:all|each) graveyards?"
    r"|graveyards? (?:is|are) exiled", re.I)
# TARGETED graveyard exile — "exile up to one target card from a graveyard". The
# controller PICKS the yard, so in an own-graveyard deck you simply aim it at theirs and
# there is no conflict; it only fights a plan that needs THEIR yard as a resource. Keeping
# this apart from the mass shape is what turns the flag from noise into a shortlist: on
# the roster it drops the count from 12 to the decks where it is actually a conflict.
_GY_HATE_CHOOSE_RE = re.compile(
    r"exile[^.]{0,50}?\bfrom (?:a|a single|each|target) graveyard\b"
    r"|exile[^.]{0,50}?\bfrom graveyards\b", re.I)
# The escape / delve / flashback COST family — a graveyard USER, never hate.
_GY_OWN_SCOPE_RE = re.compile(r"\byour graveyard\b|\byour own graveyard\b", re.I)
# Needs the OPPONENT's yard populated (casting or stealing from it).
_GY_NEED_OPP_RE = re.compile(
    r"(?:cast|play|return|exile)[^.]{0,60}?from (?:an? opponent'?s?|target player'?s?|that player'?s?|their) graveyard"
    r"|in your opponents'? graveyards"
    r"|cards? in (?:their|each opponent'?s?) graveyard", re.I)


def graveyard_emptier(text):
    """``'opponent'`` / ``'all'`` / ``None`` — which graveyards this card EMPTIES.

    Three scopes, because they conflict with different plans:
      ``all``      – untargeted mass exile; hits YOUR yard whether you like it or not.
      ``opponent`` – scoped to their yard.
      ``choose``   – targeted ("exile up to one target card from a graveyard"); you pick
                     the yard, so it only fights a plan that needs THEIRS populated.

    ``None`` for a card that only touches YOUR yard (escape/delve costs) and for any
    card whose exile is a heist (it exiles in order to cast, so it needs the yard full —
    it is the engine, not the hate)."""
    t = _norm_role_text(text or "")
    if not t:
        return None
    try:
        from tag_synergies import is_heist_text
        if is_heist_text(text or ""):
            return None
    except Exception:
        pass                      # tag_synergies unavailable — fall through, over-report
    if _GY_HATE_ALL_RE.search(t):
        return "all"
    if _GY_HATE_OPP_RE.search(t):
        return "opponent"
    if _GY_HATE_CHOOSE_RE.search(t):
        return "choose"
    # Left last on purpose: a card scoped ONLY to your own yard is a user, not an emptier.
    return None


def graveyard_dependent(text, type_line=""):
    """``{'own'}`` / ``{'opponent'}`` / both / empty — which graveyards this card NEEDS
    populated. Own-yard dependence reuses `engine_roles`' graveyard PAYOFF side (the
    trustworthy half of that classifier) rather than adding a second model."""
    t = text or ""
    needs = set()
    if _GY_NEED_OPP_RE.search(_norm_role_text(t)):
        needs.add("opponent")
    try:
        if "payoff" in engine_roles(t).get("graveyard", set()):
            needs.add("own")
    except Exception:
        pass
    return needs


def zone_conflict_flags(cards, carddata):
    """[(card_name, scope, why, [dependent card names])] — cards that EMPTY a graveyard
    this deck depends on being populated.

    Fires only when the deck fields >= `_ZONE_MIN_DEPENDENTS` cards needing that yard, so
    a lone graveyard payoff can't manufacture a conflict. A FLAG for a human read, never a
    score change — the same posture as `cost_upside_flags` and `scales w/`, because the
    signal is real but the judgement (is the hate worth it against this meta?) is not
    mechanical."""
    need_opp, need_own = [], []
    seen = set()
    for _q, n, _s, _c in cards:
        nl = n.lower()
        if nl in BASICS or nl in seen:
            continue
        seen.add(nl)
        cd = carddata.get(nl)
        if not cd:
            continue
        needs = graveyard_dependent(cd.get("text") or "", cd.get("type") or "")
        if "opponent" in needs:
            need_opp.append(n)
        if "own" in needs:
            need_own.append(n)

    out, seen = [], set()
    for _q, n, _s, _c in cards:
        nl = n.lower()
        if nl in BASICS or nl in seen:
            continue
        seen.add(nl)
        cd = carddata.get(nl)
        if not cd:
            continue
        scope = graveyard_emptier(cd.get("text") or "")
        if not scope:
            continue
        # Only an untargeted mass exile can hurt your OWN yard; a targeted one you aim.
        hit = list(need_opp)
        if scope == "all":
            hit += [x for x in need_own if x not in hit]
        hit = [x for x in hit if x.lower() != nl]     # a card can't conflict with itself
        if len(hit) < _ZONE_MIN_DEPENDENTS:
            continue
        where = {"all": "every graveyard, including your own",
                 "opponent": "an opponent's graveyard",
                 "choose": "a graveyard you target"}[scope]
        out.append((n, scope,
                    f"empties {where}, which {len(hit)} card(s) here need populated", hit))
    return out


def cost_upside_flags(text, deck_themes):
    """['<why>'] for each additional cost / drawback in `text` that this deck's themes
    turn into an UPSIDE. Empty when the deck doesn't support it — the point is that the
    same clause is a downside elsewhere."""
    t = _norm_role_text(text)
    themes = {str(x).lower() for x in (deck_themes or ())}
    return [why for rx, want, why in _COST_UPSIDE if rx.search(t) and (want & themes)]

# Coverage self-audit (F15). The role classifier above is PRECISE (low false
# positives) but inevitably misses phrasings, silently UNDER-counting — the recurring
# failure only a hands-on read used to catch (a creature-ETB kill, an edict, a -1/-1,
# a bounce, "exile up to one target"). These BROAD cues are the complement: high-
# recall nets for "this text interacts / draws cards." When a broad cue fires but the
# precise classifier tagged NO matching role, that's a likely under-read — flagged for
# a human verify, never silently changing a count. Tuned to the classifier's intent:
# single-card draw is a cantrip (deliberately not card advantage), and damage to a
# PLAYER is burn/reach, not creature interaction — so both are excluded here.
_INT_CUES = re.compile(
    r"(?:destroy|exile) (?:target |up to \w+ target |all |each |those |that |another )?"
    r"(?:creature|permanent|nonland permanent|artifact|enchantment|planeswalker|tapped|attacking)"
    r"|counter (?:target|that spell|it unless)"
    r"|deals? \d+ damage to (?:any target|target creature|each (?:other )?creature|up to \w+ target)"
    r"|\bfights?\b"
    r"|gets? -\d+/-[0-9x]+|gets? \-[0-9x]+/\-[0-9x]+"
    r"|(?:each opponent|target opponent|target player|each player) sacrifices"
    r"|return target (?:creature|permanent|nonland permanent)[^.]{0,40}?hand",
    re.I)
_CA_CUES = re.compile(
    r"draws? (?:two|three|four|five|x|that many) cards?"
    r"|draw cards? equal to|draw a card for each"
    r"|\binvestigate\b",
    re.I)

# The audit net MUST be a SUPERSET of what the precise classifier can match, or a
# phrasing can be missed by BOTH — which is exactly what happened to Repulsive
# Mutation ("counter up to one target spell unless…"): too narrow for the Counter
# pattern AND absent from the broad cue, so the under-read wasn't even flagged.
# Unioning the precise interaction/card-advantage patterns in makes that structurally
# impossible: anything the classifier CAN see, the net also sees, and the flag still
# only fires when the classifier tagged no matching role.
# Parenthetical REMINDER text. Non-nested is enough — MTG never nests reminders.
_REMINDER_RE = re.compile(r"\([^()]*\)")

_INT_CUE_PATS = [_INT_CUES] + [p for lbl in sorted(_INTERACTION_ROLES)
                               for p in _ROLE_COMPILED_MAP[lbl]]
_CA_CUE_PATS = [_CA_CUES] + _ROLE_COMPILED_MAP["Card advantage"]


def role_coverage_flags(cards, carddata):
    """Cards whose oracle text likely holds a role the precise classifier MISSED — a
    coverage self-audit so a silent under-count becomes an explicit 'read these.'
    Returns (unclassified, under_read):
      • unclassified — noncreature, nonland spells that matched NO functional role
        (the classifier had nothing to say about them; read the text yourself),
      • under_read   — (name, axis) where a broad interaction / card-advantage cue
        fires but classify_roles tagged no matching role (a likely under-read).
    Neither changes any count — both are review prompts (grade from full text via
    card.py / deck.py text)."""
    unclassified, under_read, no_data = [], [], []
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        cd = carddata.get(n.lower())
        if not cd:
            # No library/pool row at all (e.g. a WIP craft target): role_tally can't
            # read its text, so it silently contributes 0 interaction/card-advantage.
            # Surface it so the under-count is explicit, not invisible (audit F14).
            no_data.append(n)
            continue
        if "Land" in _primary_type(cd.get("type") or ""):
            continue
        text = cd.get("text") or ""
        roles = set(classify_roles(text))
        # Match the cues against the SAME normalized form classify_roles uses, and
        # against the superset net, so the audit can't be blind where the classifier is
        # — minus REMINDER TEXT. Ward's reminder ("…counter it unless that player pays
        # {2}.") tripped the Counter cue, so every warded creature in the collection was
        # reported as a missed interaction piece: a false cue, which is the one thing
        # that degrades this list (it exists to be read card-by-card, so noise in it is
        # expensive). Stripping reminders can't create a blind spot, because the net
        # includes the precise patterns and the flag only fires when NO role was tagged
        # — anything a role pattern sees in reminder text is already a tagged role.
        t = _REMINDER_RE.sub(" ", _norm_role_text(text))
        missed = []
        if any(p.search(t) for p in _INT_CUE_PATS) and not (roles & _INTERACTION_ROLES):
            missed.append("interaction")
        # A loot is deliberately NOT card advantage, so strip it before testing the
        # card-advantage cue — otherwise every looter would be reported as an
        # under-read of the very rule that excludes it.
        if (any(p.search(_LOOT_RE.sub(" ", t)) for p in _CA_CUE_PATS)
                and "Card advantage" not in roles):
            missed.append("card advantage")
        if missed:
            under_read.append((n, "/".join(missed)))
        elif not roles and "Creature" not in (cd.get("type") or ""):
            unclassified.append(n)
    return unclassified, under_read, no_data


def _norm_role_text(text):
    """Lowercased, unicode-minus-normalized oracle text — the one form every role
    pattern and coverage cue is matched against, so the precise classifier and its
    audit net can't disagree about the input either."""
    return (text or "").lower().replace("−", "-")


def classify_roles(text):
    """Return the set of functional-role labels a card's oracle text matches."""
    t = _norm_role_text(text)
    roles = {label for label, pats in _ROLE_COMPILED if any(p.search(t) for p in pats)}
    if "Card advantage" in roles and _LOOT_RE.search(t):
        # Blank the loot clause(s) and re-test: only drop the role when nothing ELSE
        # in the text is a real net-positive draw (a card can loot AND draw).
        stripped = _LOOT_RE.sub(" ", t)
        if not any(p.search(stripped) for p in _ROLE_COMPILED_MAP["Card advantage"]):
            roles.discard("Card advantage")
    return roles


# Mana production, detected broadly enough to catch dorks the "Ramp / fixing" role
# misses: that role keys on the "{T}: add {SYM}" template, but a flavor-keyword dork
# (Bloom Tender's "Vivid — {T}: … add one mana …") phrases it as "add one mana" and
# slips through. Used by the tier tune plan to warn when a proposed cut is a mana
# source (losing it hurts the manabase) — a heuristic flag, not a role reclassification.
_MANA_PRODUCE_RE = re.compile(
    r"\badd\s+\{[wubrgcpx0-9/]"        # "add {G}", "add {C}{C}", "add {W/U}"
    r"|\badd\b[^.\n]{0,40}?\bmana\b",  # "add one mana", "add two mana of any color"
    re.IGNORECASE)


def _produces_mana(text):
    """True if a card's text taps for / produces mana (a dork, rock, or ramp spell) —
    broader than the 'Ramp / fixing' role so an 'add one mana' phrasing still counts."""
    return bool(text and _MANA_PRODUCE_RE.search(text))


# The roles that make a card a keeper almost regardless of theme fit — a removal
# spell, a card-advantage engine, ramp, a cost-reducer, a payoff. `cuts`/`suggest-homes`
# weight these extra so a strong-but-off-tribe card (Cosmic Cube, Shuri, Mjölnir) stops
# floating to the TOP of the cut list just because its synergy tags don't match the
# deck's central themes. Incidental roles (lifegain, a combat trick, an anthem) get the
# base credit only. Still a shortlist signal — grade the finalists from oracle text.
IMPACT_ROLES = {"Removal (spot)", "Sweeper", "Counter", "Card advantage",
                "Ramp / fixing", "Cost reduction / cheat", "Payoff / engine",
                "Reanimation", "Burn / drain"}


def _role_credit(roles, saturation=None):
    """Keep-score credit for a card's functional roles: base 3 each, +6 more for each
    IMPACT role, so a card that does a high-value job clears the no-role 'filler' band
    (theme-fit only, ~0–8) and doesn't rank as a top cut. It can't fully offset a large
    theme-fit gap — an off-theme power card (Cosmic Cube, The Ten Rings) still sorts
    low in a tuned deck, which is inherent to a synergy model and exactly why `cuts`
    prints full oracle text and wishlist ranking pairs fit with a hand-graded Power.

    When `saturation` (role → how many copies the deck ALREADY runs of that role) is
    passed, the +6 IMPACT bonus DIMINISHES with saturation — the 1st removal spell is
    worth the full bonus, the 8th very little (diminishing returns, improvement #1). So
    `suggest` stops over-valuing the Nth copy of an effect the deck is already deep in,
    and `cuts` ranks a redundant piece as more cuttable while protecting a scarce one
    (the deck's only counterspell keeps its full credit). With no `saturation` the
    credit is the original flat value (unchanged for any caller that doesn't opt in)."""
    base = 3 * len(roles)
    impact_roles = set(roles) & IMPACT_ROLES
    if saturation is None:
        return base + 6 * len(impact_roles)
    bonus = 0.0
    for r in impact_roles:
        have = max(0, saturation.get(r, 0))
        bonus += 6.0 / (1 + 0.5 * have)   # have 0→6, 1→4, 2→3, 3→2.4, 6→~1.5
    return base + bonus


def _curve_gap_factor(mv, curve):
    """A bounded (0.85–1.15) multiplier on a candidate's `suggest` score by how its mana
    value fits the deck's CURVE (improvement #2). Archetype-agnostic and deliberately
    gentle so it re-ranks near-ties without overriding a clear theme-fit winner:

      • an OVER-FULL bucket (more copies than the deck's average slot) is gently
        penalized at ANY cost — you don't need the 9th three-drop;
      • a THIN CHEAP bucket (MV ≤ 3, below average) is gently boosted — nearly every
        deck wants its early plays filled;
      • a thin EXPENSIVE bucket is left alone (factor 1.0) — boosting top-end would be
        archetype-wrong for an aggro deck, so the curve signal never does it.

    `curve` is the deck's nonland MV histogram (bucket → copies). Returns 1.0 when the
    card's MV or the curve is unknown, so a missing mana row never distorts the score."""
    if mv is None or not curve:
        return 1.0
    b = min(int(mv), 7)
    avg = sum(curve.get(i, 0) for i in range(1, 8)) / 7.0
    if avg <= 0:
        return 1.0
    ratio = curve.get(b, 0) / avg
    if ratio > 1.0:
        return max(0.85, 1.0 - 0.15 * (ratio - 1.0))
    # Boost a thin CHEAP spell slot (MV 1–3) only; MV 0 (lands / free spells) isn't a
    # curve slot — the deck curve counts nonland cards, so a land would else read as a
    # perpetually-thin "0-drop" and get an unearned boost.
    if 1 <= b <= 3 and ratio < 1.0:
        return min(1.15, 1.0 + 0.15 * (1.0 - ratio))
    return 1.0


_HOME_CURVE_CAP = 0.15  # ±15%, matching _curve_gap_factor's bound


def _home_curve_fit(card_mv, deck_avg_mv):
    """A bounded (0.85–1.0) SORT multiplier for `suggest-homes` (finding #5): gently
    penalize placing a card whose mana value sits well ABOVE a deck's average nonland MV —
    a top-heavy / win-more add (an ~11-mana Aettir and Priwen) fits an aggressive low-curve
    deck worse than a midrange one, which pure theme-overlap can't see. Unlike
    `_curve_gap_factor` this is keyed to the DECK'S average (constant per card in a
    suggest-homes run, so a card-MV signal alone couldn't reorder decks). It NEVER boosts
    and is capped at _HOME_CURVE_CAP, so it only reorders same-strength fits — it can't
    relabel a KEY/role-player/tangential verdict or override theme fit. Returns 1.0 when a
    MV is unknown or the card is within ~a turn of the deck's average."""
    if not card_mv or not deck_avg_mv:
        return 1.0
    excess = card_mv - deck_avg_mv
    if excess <= 2.0:                      # within ~2 MV of the average — a normal top-end,
        return 1.0                         # not a win-more; only flag genuinely heavy cards
    return max(1.0 - _HOME_CURVE_CAP, 1.0 - 0.05 * (excess - 2.0))


# Weight of the power co-signal in `suggest` (#6): power is 0–10, so at 1.0 a bomb adds
# up to ~10 — comparable to a strong role bonus, enough to lift a modest-fit bomb above a
# same-fit vanilla, but small next to a strongly-on-theme card's theme_w. Never dominant.
_SUGGEST_POWER_W = 1.0


# Cuts power co-signal (#3): fold the wishlist power model into the cut RANKING so an
# on-theme-but-WEAK card can surface as cuttable and an on-theme BOMB is protected — the
# thing pure theme-fit can't see (a vanilla body and a bomb that share one tag look
# identical to a synergy model). Centered so an average card (~5) is neutral; BOUNDED so
# it only re-ranks near-ties (theme fit stays dominant — guarded by check_suggest #7).
_CUTS_POWER_NEUTRAL = 5.0
_CUTS_POWER_W = 0.35
_CUTS_POWER_CAP = 2.5


def _cuts_power_adj(power):
    """Bounded keep-score nudge from a card's 0–10 power: >0 protects a bomb (harder to
    cut), <0 makes a weak card more cuttable. Clamped to ±_CUTS_POWER_CAP so it can only
    break near-ties, never override theme fit."""
    adj = _CUTS_POWER_W * (power - _CUTS_POWER_NEUTRAL)
    return max(-_CUTS_POWER_CAP, min(_CUTS_POWER_CAP, adj))


# Ability-distinctiveness co-signal: theme fit and power both miss a distinct question —
# is this card's ability set GENERIC TEMPLATING (the etb/tokens/sacrifice body that trips
# broad synergy-overlap everywhere) or a distinctive mechanic? `lib.card_distinctiveness`
# scores that as the max of pool tag-rarity and a structural read of the oracle text (so a
# mis-tagged distinctive card is still caught by its text shape). A generic-ability filler
# is more cuttable; a distinctive card is mildly protected. Centered at _CUTS_UNIQ_NEUTRAL,
# BOUNDED to ±cap so
# it only breaks near-ties (theme fit stays dominant — guarded by check_suggest #8). It is
# ORTHOGONAL to power (a vanilla 6/6 is high power, low distinctiveness), so it earns its
# own small term rather than folding into the power adj.
_CUTS_UNIQ_NEUTRAL = 4.0
_CUTS_UNIQ_W = 0.30
_CUTS_UNIQ_CAP = 1.5


def _cuts_uniq_adj(uniq):
    """Bounded keep-score nudge from a card's 0–10 ability-distinctiveness: >0 protects a
    distinctive-mechanic card, <0 makes a generic-ability filler more cuttable. Clamped to
    ±_CUTS_UNIQ_CAP so it only breaks near-ties, never overrides theme fit."""
    adj = _CUTS_UNIQ_W * (uniq - _CUTS_UNIQ_NEUTRAL)
    return max(-_CUTS_UNIQ_CAP, min(_CUTS_UNIQ_CAP, adj))


# A MULTIPLIER's value lives in what it does to the REST of the deck, and both halves of
# the cut score are structurally blind to that: theme-fit sees a card with few tags, and
# `_role_credit` sees no functional role, because "doubles a trigger" is not a role. So
# Delney, Streetwise Lookout — which doubles the triggered ability of every creature in
# deck 46's small-body engine layer — ranked as the WEAKEST card in the deck, and
# Valkyrie's Call ranked near it. The information was already in the codebase: `doubler_
# axis`/`doubler_support` were built for `suggest-homes` and score Delney correctly, but
# `cuts` never asked. This routes the SAME primitives into the cut score rather than
# adding a second model, so the two cannot disagree about what a doubler is worth.
_CUTS_MULT_CAP = 3.0
_CUTS_MULT_MIN_SOURCES = 4      # below this, a doubler genuinely has nothing to double
_CUTS_MULT_PER_SOURCE = 0.35


def _cuts_multiplier_adj(support):
    """Keep-bias for a doubler, proportional to the magnitude it multiplies.

    Bounded to 0…_CUTS_MULT_CAP and ZERO below _CUTS_MULT_MIN_SOURCES — a doubler in a
    deck that does not feed its axis really is cuttable, which is why this only ever
    RAISES a keep-score and never lowers one: the no-support case is already handled by
    theme-fit, and subtracting there would punish the same card twice.
    """
    if support < _CUTS_MULT_MIN_SOURCES:
        return 0.0
    return min(_CUTS_MULT_CAP, support * _CUTS_MULT_PER_SOURCE)


# `suggest --lands` co-signals. A land's dominant value is FIXING (wishlist._land_value,
# 0–10), but a land's ABILITY can also play the deck (Abandoned Air Temple's team-pump in a
# go-wide deck, Fire Nation Palace's firebending ramp) — so a bounded SYNERGY term lifts a
# land whose text matches the deck's central themes, and a bounded SHORTFALL term favors a
# land producing the color the deck is scarcest on. Both are CAPPED so fixing stays dominant
# (a land is chosen for its mana first) — guarded by check_suggest anchor 9.
_LAND_SYN_CAP = 2.0
_LAND_SHORT_CAP = 1.5


def _land_synergy_bonus(land_tags, theme_w):
    """Bounded [0, _LAND_SYN_CAP] nudge: a land whose synergy tags hit the deck's central
    themes ranks above a vanilla dual. Scaled by the land's STRONGEST shared theme relative
    to the deck's top theme, so a land on the deck's spine gets the full cap and an incidental
    overlap gets little. 0 when the land shares nothing (a plain dual) — fixing then decides."""
    if not theme_w or not land_tags:
        return 0.0
    shared = [theme_w[t] for t in land_tags if t in theme_w]
    if not shared:
        return 0.0
    mx = max(theme_w.values()) or 1
    return round(min(_LAND_SYN_CAP, _LAND_SYN_CAP * (max(shared) / mx)), 2)


def _land_shortfall_bonus(land_colors, deficit):
    """Bounded [0, _LAND_SHORT_CAP] nudge toward the color the deck is SHORTEST on. `deficit`
    is {color: >=0 scarcity} (pip-demand share minus source share); a land producing the
    scarcest color it covers gets the most. 0 when it produces no under-served color."""
    if not deficit or not land_colors:
        return 0.0
    mx = max(deficit.values()) or 0.0
    if mx <= 0:
        return 0.0
    best = max((deficit.get(c, 0.0) for c in land_colors), default=0.0)
    return round(min(_LAND_SHORT_CAP, _LAND_SHORT_CAP * best / mx), 2)


# ── The "needs model": suggest --ramp / --interaction / --needs ──────────────────────────
# suggest_scored answers "what SYNERGIZES with my themes"; these answer "what my deck
# structurally LACKS" (fixing, acceleration, interaction) — the axes a theme model can't see
# by design (the idf model was BUILT to reject catch-alls, so we never weaken its filter; we
# add a parallel needs-aware path instead). Every nudge below is BOUNDED so it re-ranks within
# a needs-filtered candidate set and can't manufacture a catch-all pick (check_suggest #10).
_RAMP_ACCEL_CAP = 2.0       # a top-heavy deck wants acceleration; a low-curve deck wants none
_RAMP_RESTRICT_CAP = 1.5    # a restricted-mana dork ('add R only for Equipment') matching the deck
_INT_SCALE_CAP = 1.5        # a board-scaling removal spell the deck's board actually supports


def _accel_want(avg_mv, heavy_share):
    """0–1 'this deck wants acceleration', from curve top-heaviness: a high average MV and a
    large share of 4+-drops => wants ramp; a lean aggro curve => ~0. Bounded [0, 1]."""
    a = (avg_mv - 2.3) / 1.2           # 2.3 avg -> 0, 3.5 avg -> 1
    h = (heavy_share - 0.15) / 0.30    # 15% at 4+ -> 0, 45% -> 1
    return round(max(0.0, min(1.0, 0.5 * max(0.0, a) + 0.5 * max(0.0, h))), 2)


_RESTRICT_RE = re.compile(
    r"spend this mana only to (?:cast|activate)[^.\n]*?\b"
    r"(equipment|artifact|instant|sorcery|creature|enchantment)", re.I)


def _ramp_restriction_fit(text, type_share):
    """Bounded ± nudge for a RESTRICTED mana source ('add R, spend only to cast an Equipment
    spell'): + when that type is well-represented in the deck, − when it's scarce (a spell-only
    dork in a creature deck is near-dead), 0 for unrestricted mana. `type_share` maps a type
    word -> fraction of the deck's nonland cards of that type. Centered at ~20% representation."""
    m = _RESTRICT_RE.search(text or "")
    if not m:
        return 0.0
    kind = m.group(1).lower()
    share = (type_share.get("instant", 0) + type_share.get("sorcery", 0)
             if kind in ("instant", "sorcery") else type_share.get(kind, 0))
    val = _RAMP_RESTRICT_CAP * (share - 0.20) / 0.20
    return round(max(-_RAMP_RESTRICT_CAP, min(_RAMP_RESTRICT_CAP, val)), 2)


_INT_FIGHT_RE = re.compile(r"\bfights?\b[^.\n]*?target creature", re.I)
_INT_COUNT_RE = re.compile(
    r"number of (?:\w+ )?(creatures|artifacts|equipment|permanents|lands) you control", re.I)


def _int_scaling(text):
    """The deck-STATE axis a removal card scales with, or None. 'fight' scales with YOUR
    creatures' power; 'damage = number of X you control' scales with that count; an {X} deal/
    destroy scales with mana. These are the deck-dependent removal cards a tag model can't grade
    in the abstract — surface them and FLAG the axis for a human read (never silently boost)."""
    t = text or ""
    if _INT_FIGHT_RE.search(t):
        return "fight"
    m = _INT_COUNT_RE.search(t)
    if m:
        return m.group(1).lower()
    if "{X}" in t and re.search(r"\b(deal|destroy|damage)\b", t, re.I):
        return "x-cost"
    return None


def _int_scaling_boost(axis, deck_metric):
    """Bounded [0, _INT_SCALE_CAP] boost for a board-scaling removal spell the deck actually
    supports. `deck_metric` is a 0–1 strength on the card's axis (avg creature power for fight,
    board density for a count-based card). Modest by design — the human confirms from the flag;
    0 for a non-scaling card or a deck that can't turn the scaling on."""
    if not axis:
        return 0.0
    m = max(0.0, min(1.0, deck_metric))
    return round(min(_INT_SCALE_CAP, _INT_SCALE_CAP * m), 2)


def deck_needs(d):
    """The deck's STRUCTURAL profile — the axes suggest_scored's theme model can't see.
    Returns {colors, sources, deficit, avg_mv, accel, interaction, int_target, int_short,
    type_share, creature_power, board_density, central, names}. Shared by --ramp / --interaction
    / --needs so they can't drift. Pure read (no writes)."""
    meta = load_card_meta()
    dmeta, cards = parse_deck_file(d["path"])
    mana_map, carddata = load_mana(), load_card_data()
    deck_colors = _declared_colors(dmeta)
    if not deck_colors:
        for _q, n, _s, _c in cards:
            m = meta.get(n.lower())
            if n.lower() not in BASICS and m:
                deck_colors |= (m["colors"] & set("WUBRG"))

    theme_w, names = {}, set()
    sources = {c: 0 for c in deck_colors}
    demand = {c: 0 for c in deck_colors}
    nonland = mv_sum = mv_n = heavy = cre = equip = arti = inst = sorc = ench = 0
    for q, n, _s, _c in cards:
        nl = n.lower()
        names.add(nl.split(" // ")[0])
        if nl in BASICS:
            col = BASIC_COLOR.get(nl)
            if col in sources:
                sources[col] += q
            continue
        m = meta.get(nl)
        cd = carddata.get(nl)
        tline = (cd["type"] if cd else "") or ""
        if "Land" in _primary_type(tline):
            for col in (m["colors"] if m else set()):
                if col in sources:
                    sources[col] += q
            continue
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
        entry = mana_map.get(nl)
        mv = entry[1] if (entry and entry[1] is not None) else None
        nonland += q
        if mv is not None:
            mv_sum += mv * q
            mv_n += q
            if mv >= 4:
                heavy += q
        if entry and entry[0]:
            strict, _hy = parse_pips(entry[0])
            for col, cnt in strict.items():
                if col in demand:
                    demand[col] += cnt * q
        pt = _primary_type(tline)
        low = tline.lower()
        if "Creature" in pt:
            cre += q
        if "artifact" in low:
            arti += q
        if "equipment" in low:
            equip += q
        if "Instant" in pt:
            inst += q
        if "Sorcery" in pt:
            sorc += q
        if "Enchantment" in pt:
            ench += q

    tot_d = sum(demand.values()) or 1
    tot_s = sum(sources.values()) or 1
    deficit = {c: max(0.0, demand[c] / tot_d - sources[c] / tot_s) for c in deck_colors}
    avg_mv = round(mv_sum / mv_n, 2) if mv_n else 0.0
    heavy_share = heavy / mv_n if mv_n else 0.0
    tally = role_tally(cards, carddata)
    ts = (lambda x: round(x / nonland, 2) if nonland else 0.0)
    central = _central_themes(theme_w)
    return {
        "colors": deck_colors, "sources": sources, "deficit": deficit, "avg_mv": avg_mv,
        "accel": _accel_want(avg_mv, heavy_share),
        "interaction": tally.get("interaction", 0), "int_target": 5,
        "int_short": tally.get("interaction", 0) < 5,
        "type_share": {"creature": ts(cre), "artifact": ts(arti), "equipment": ts(equip),
                       "instant": ts(inst), "sorcery": ts(sorc), "enchantment": ts(ench)},
        "board_density": round(min(1.0, (cre + equip) / max(1, nonland)), 2),
        "central": central, "central_w": {t: theme_w[t] for t in central},
        "names": names, "theme_w": theme_w,
        "format": (dmeta.get("format") or "").strip().lower(),
    }


def _scaling_metric(axis, needs):
    """Map a removal card's scaling AXIS (_int_scaling) to the deck's 0–1 strength on it:
    a FIGHT card wants a deck that makes big creatures (equipment/creature density); a
    'number of X you control' card wants that permanent to be dense; an {X} card wants ramp."""
    ts = needs["type_share"]
    if axis == "fight":
        return min(1.0, ts.get("creature", 0) + ts.get("equipment", 0))
    if axis in ("creatures", "permanents"):
        return needs["board_density"]
    if axis in ("equipment", "artifacts"):
        return min(1.0, ts.get("equipment", 0) + ts.get("artifact", 0)) if axis == "artifacts" \
            else ts.get("equipment", 0)
    if axis == "x-cost":
        return needs["accel"]
    return needs["board_density"]


def _produced_colors(text, deck_colors):
    """The colors a mana source can make, scoped to the deck: an 'any color / any type' dork
    reads as all the deck's colors; else the explicit `{W}`… symbols in its text."""
    t = text or ""
    if re.search(r"any color|any type|mana of any", t, re.I):
        return set(deck_colors)
    return {c for c in "WUBRG" if "{" + c + "}" in t}


_power_seed_warned = False  # one-time guard for the A14 degradation warning


def _power_seed(row):
    """A card's heuristic power (0–10) for suggest's card-quality co-signal (#6) — the
    same rarity+role estimate the wishlist seeds Power with, so an owned/craftable bomb
    surfaces even on a modest theme fit. Lazy-imports wishlist (which itself lazy-imports
    deck) to avoid a load cycle; returns 0.0 if unavailable, so power just drops out."""
    try:
        import wishlist
        return wishlist._seed_power(row)
    except Exception as e:
        # Degrade (power drops out of the ranking) but say so ONCE — this runs per
        # candidate in a hot loop, so a silent 0.0 for every card would hide a real
        # regression in the power seed (audit A14).
        global _power_seed_warned
        if not _power_seed_warned:
            _power_seed_warned = True
            eprint(f"WARN:  power co-signal unavailable ({type(e).__name__}: {e}); "
                   "suggest ranking proceeds without the power dimension.")
        return 0.0


# --------------------------------------------------------------------------- #
# Engine roles — enabler vs payoff WITHIN a theme (improvement #3)
# --------------------------------------------------------------------------- #
# A synergy tag says "sacrifice" appears in the deck; it does NOT say which cards
# FEED the engine (sac outlets / fodder) and which cards PAY IT OFF (death triggers).
# The most common real deckbuilding flaw — payoffs with no enablers (or vice versa) —
# is invisible to a bag-of-tags model. For the handful of themes that are actual
# two-sided engines, classify each card's oracle text as ENABLER (produces/enables the
# resource) and/or PAYOFF (rewards/consumes it), so `engine_balance` can flag a
# lopsided engine. Heuristic and text-based (so it catches an untagged outlet too);
# the `engines` command prints the card lists for a human read, like `cuts`/`tribes`.
ENGINE_THEMES = {
    "counters": {
        "enabler": [
            r"put (a|one|two|three|four|x|that many|another|\d+)[^.]*\+1/\+1 counter",
            r"enters[^.]*with[^.]*\+1/\+1 counter", r"\bproliferate\b", r"\badapt\b",
            r"\bbolster\b", r"\bsupport \d", r"\bmonstrosity\b", r"\btraining\b",
        ],
        "payoff": [
            r"for each \+1/\+1 counter",
            r"\+1/\+1 counter[^.]*(among (creatures|permanents) you control|on creatures you control)",
            r"whenever[^.]*\+1/\+1 counter is (put|placed)",
            r"if[^.]*would[^.]*\+1/\+1 counter[^.]*instead", r"twice that many \+1/\+1",
            r"remove (a|one|x|\d+)[^.]*\+1/\+1 counter", r"move (a|one|any number of)[^.]*\+1/\+1 counter",
        ],
    },
    "tokens": {
        "enabler": [r"create[s]? [^.]*\btoken", r"\bpopulate\b", r"\bfabricate\b"],
        "payoff": [
            r"for each (creature|token|artifact) you control", r"creatures you control get \+",
            r"whenever a[^.]*token[^.]*enters", r"creatures you control (have|gain)",
            r"each creature you control", r"sacrifice (a|another|\w+)[^.]*token",
        ],
    },
    "sacrifice": {   # aristocrats: outlets/fodder vs death & sacrifice triggers
        # A "whenever ~ dies" trigger ('death') fires on ANY death — combat included — so
        # it is NOT sac-outlet-dependent the way a "whenever you sacrifice" payoff is.
        # engine_balance keeps them apart: only sac-triggers "sit dead" without an outlet;
        # death triggers are combat-fed when the deck has a real creature base (F-engines).
        "enabler": [r"\bsacrifice (a|an|another|two|three|\d+|x|it|them)\b", r"you may sacrifice"],
        "payoff": [r"whenever you sacrifice", r"whenever[^.]*is sacrificed"],
        "death": [r"whenever[^.]*\bdies\b"],
    },
    "graveyard": {   # fill the yard vs use the yard (reanimator / recursion)
        # Self-recursion mechanics (flashback / escape / harmonize / …) put the card into
        # the yard THEMSELVES, so a card that plays them is its own enabler — counted on
        # BOTH sides so a graveyard full of flashback spells doesn't read as "unenabled".
        "enabler": [r"\bmill\b", r"\bsurveil\b", r"discard[^.]*card", r"put[^.]*(from|into)[^.]*graveyard",
                    r"into your graveyard", r"\bdredge\b",
                    r"\bflashback\b", r"\bescape\b", r"\bdisturb\b", r"\bunearth\b", r"\bharmonize\b",
                    r"\bjump-start\b", r"\bretrace\b", r"\baftermath\b", r"cast [^.]*from (your )?graveyard"],
        "payoff": [r"return[^.]*from (your )?graveyard to the battlefield", r"from your graveyard",
                   r"for each[^.]*in your graveyard", r"\bescape\b", r"\bflashback\b", r"\bdelve\b",
                   r"\bdisturb\b", r"\bunearth\b", r"cards? in your graveyard"],
    },
    "lifegain": {
        "enabler": [r"gain (\d+|x|that much) life", r"gains? \d+ life", r"\blifelink\b"],
        "payoff": [r"whenever you gain life", r"for each[^.]*life[^.]*gained",
                   r"if you (gained|would gain)[^.]*life", r"(the amount of )?life you gained"],
    },
    "food": {
        "enabler": [r"create[s]? [^.]*food"],
        "payoff": [r"sacrifice a food", r"for each food", r"food[^.]*you control"],
    },
}
_ENGINE_COMPILED = {
    theme: {role: [re.compile(p) for p in pats] for role, pats in sides.items()}
    for theme, sides in ENGINE_THEMES.items()
}

# A deck fielding this many creatures trades in combat often enough that a "whenever ~
# dies" death trigger is fed without any sac outlet — so combat-fed death triggers are
# exempt from the sacrifice dead-payoff flag at/above this creature count.
_COMBAT_FED_MIN = 6


def engine_roles(text):
    """{theme: {roles}} — for each engine theme, which side(s) of its two-sided engine a
    card's oracle text plays: 'enabler' (feeds the engine) and/or 'payoff' (rewards it).
    A card can be both (a sac outlet that also triggers on death) or neither. Text-based,
    so an untagged piece is still caught. `− → -` normalized like classify_roles."""
    t = (text or "").lower().replace("−", "-")
    out = {}
    for theme, sides in _ENGINE_COMPILED.items():
        hit = {role for role, pats in sides.items() if any(p.search(t) for p in pats)}
        if hit:
            out[theme] = hit
    return out


def engine_balance(cards, carddata, central, signature=frozenset()):
    """For each engine theme CENTRAL to the deck, tally enabler vs payoff copies and a
    verdict. Only reports themes that are (a) real two-sided engines (in ENGINE_THEMES)
    and (b) central to THIS deck — so an incidental one-off doesn't raise a flag.

    `signature` (the deck's built-around themes, from `_signature_themes`) gates the
    NOISY verdicts: 'payoffs with no enablers' (dead payoffs) is a hard flag for ANY
    central engine, but 'enablers with no payoff' / a skew is only flagged for a
    SIGNATURE engine — a deck naturally has incidental lifegain/counters enablers it
    doesn't need to pay off, so those must not cry wolf.

    Returns {theme: {'enablers': [(name,q)], 'payoffs': [(name,q)], 'en': n, 'pay': n,
    'verdict': str, 'flag': bool}} ordered by the deck's theme centrality."""
    sig = {t.lower() for t in signature}
    central_engines = [t for t in central if t.lower() in _ENGINE_COMPILED]
    result = {}
    creatures = 0
    for theme in central_engines:
        result[theme] = {"enablers": [], "payoffs": [], "deaths": [],
                         "en": 0, "pay": 0, "death": 0}
    # Quantity-weighted per card, summed ACROSS lines (matching the canonical role_tally;
    # a `seen`-set + first-line q under-counted a card split over two lines, audit A11).
    qty_by_name, disp = {}, {}
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS:
            continue
        qty_by_name[nl] = qty_by_name.get(nl, 0) + q
        disp.setdefault(nl, n)
    for nl, q in qty_by_name.items():
        cd = carddata.get(nl)
        if not cd:
            continue
        n = disp[nl]
        if "creature" in (cd.get("type") or "").lower():
            creatures += q
        roles = engine_roles(cd.get("text") or "")
        for theme in central_engines:
            r = roles.get(theme.lower(), set())
            if "enabler" in r:
                result[theme]["enablers"].append((n, q)); result[theme]["en"] += q
            if "payoff" in r:
                result[theme]["payoffs"].append((n, q)); result[theme]["pay"] += q
            if "death" in r:
                result[theme]["deaths"].append((n, q)); result[theme]["death"] += q
    # Flags fire only off the PAYOFF side. Payoff cues ("whenever you gain life", "for
    # each +1/+1 counter") are specific, so a payoff gap is trustworthy; enabler cues
    # ("gain N life", "sacrifice a …") are broad and match incidental cards, so an
    # enabler-heavy count is NOISE — reported for the human read, never a ⚠.
    #
    # DEATH TRIGGERS ("whenever ~ dies") are combat-fed: with a real creature base they
    # never "sit dead" for lack of a sac outlet, so they count toward the payoff readout
    # but are EXEMPT from the dead-payoff flag once the deck fields ≥ _COMBAT_FED_MIN
    # creatures (fixes the go-wide/deathtouch false positive). Only genuine sac-trigger
    # payoffs ("whenever you sacrifice") stay outlet-dependent.
    for theme, d in result.items():
        en, pay, death = d["en"], d["pay"], d["death"]
        is_sig = theme.lower() in sig
        combat_fed = theme.lower() == "sacrifice" and creatures >= _COMBAT_FED_MIN
        total_pay = pay + death                          # payoffs for the readout
        dead_pay = pay + (0 if combat_fed else death)    # payoffs that truly need an enabler
        note = ""
        if death:
            note = (f", {death} combat-fed" if combat_fed
                    else f", {death} death-trigger/{creatures} creatures")
        if dead_pay >= 2 and en == 0:
            d["verdict"], d["flag"] = "payoffs but NO enablers — the payoffs sit dead", True
        elif total_pay >= 3 and en * 3 <= total_pay and dead_pay > 0:
            d["verdict"], d["flag"] = (f"payoff-heavy ({en} enabler / {total_pay} payoff{note}) — "
                                       "thin on enablers to turn the payoffs on"), True
        elif en and total_pay:
            d["verdict"], d["flag"] = f"balanced ({en} enabler / {total_pay} payoff{note})", False
        elif en >= 2 and total_pay == 0:
            d["verdict"] = (f"{en} enablers, no payoff — your engine has no reward"
                            if is_sig else f"{en} enablers, no payoff (incidental)")
            d["flag"] = False   # broad enabler side — inform, don't cry wolf
        elif total_pay and en == 0 and combat_fed:
            d["verdict"], d["flag"] = (f"death-fed ({total_pay} death-trigger payoff(s), "
                                       f"combat-fed by {creatures} creatures — no sac outlet "
                                       "needed)"), False
        elif en or total_pay:
            d["verdict"], d["flag"] = f"({en} enabler / {total_pay} payoff)", False
        else:
            d["verdict"], d["flag"] = "no enabler/payoff cards detected", False
    return result


def context_flags(text, mana_cost):
    """Mechanics whose value is deck-dependent (converge/devotion/affinity/X-cost);
    these must be graded against the deck, not from the shortlist label."""
    t = (text or "").lower()
    flags = [k for k, pats in _CONTEXT_COMPILED.items() if any(p.search(t) for p in pats)]
    if mana_cost and "{x}" in mana_cost.lower():
        flags.append("X-cost")
    return flags


def read_flags(text, mana_cost, keywords=None):
    """Caution tags for a card whose FULL text must be read before grading — the
    classes that have slipped past a role/tag label before: board-wide effects,
    modal choices, leaves-play triggers, deck-dependent scaling (context_flags),
    and alt/added costs (classify_cost). A signal to READ, not a grade."""
    t = (text or "").lower()
    flags = []
    if re.search(r"\ball creatures\b|each creature|creatures you control|"
                 r"creatures your opponents control|each opponent|each player", t):
        flags.append("board-wide")
    if re.search(r"\bchoose one\b|choose two|choose one or more|choose up to", t):
        flags.append("modal")
    if re.search(r"leaves the battlefield|\bwhen[^.]*dies\b|\bwhenever[^.]*dies\b", t):
        flags.append("leaves-play")
    flags += context_flags(text, mana_cost)
    cheaper, gated = classify_cost(keywords, text)
    if cheaper:
        flags.append("◊ " + ", ".join(cheaper))
    if gated:
        flags.append("△ " + ", ".join(gated))
    return flags


def cmd_text(args):
    """Dump the FULL oracle text of every card in a deck — the phased-ingestion read
    that grading a keep/cut/swap must be based on, never a role/tag label or a
    truncated field (the recurring mis-grade in past sessions). Flags cards whose
    text hides something a label can miss (board-wide / modal / leaves-play /
    deck-dependent / alt-cost). Basics are omitted."""
    import textwrap
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    carddata, mana, kw = load_card_data(), load_mana(), load_keywords()
    _, cards = parse_deck_file(d["path"])
    agg, order = {}, []
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS:
            continue
        if nl not in agg:
            agg[nl] = [0, n]
            order.append(nl)
        agg[nl][0] += q

    nonland, land = [], []
    for nl in order:
        cd = carddata.get(nl)
        tline = (cd["type"] if cd else "") or ""
        (land if "Land" in _primary_type(tline) else nonland).append(nl)

    print(f"Deck {d['id']}: {d['name'] or d['id']} — full card text (read before grading)")
    for group, label in ((nonland, "NONLAND"), (land, "NONBASIC LANDS")):
        if not group:
            continue
        print(f"\n══ {label} ({len(group)}) ══")
        for nl in group:
            qty, disp = agg[nl]
            cd = carddata.get(nl)
            tline = (cd["type"] if cd else "") or "?"
            text = (cd["text"] if cd else "") or ""
            cost, mv = (mana.get(nl) or (None, None))
            print(f"\n• {qty}× {disp}   [{tline}]" + (f"   ·  MV {mv}" if mv is not None else ""))
            card_kw = kw.get(nl) or []
            if card_kw:
                # Surface Scryfall's per-card keywords so a named mechanic (Warp,
                # Increment, …) is never skimmed over as "just a word" — its meaning
                # is in the oracle text below, but the label makes sure it's read.
                print(f"    ⌘ keywords: {', '.join(k.title() for k in card_kw)}")
            flags = read_flags(text, cost, kw.get(nl))
            if flags:
                print(f"    ⚠ {' · '.join(flags)}")
            for para in (text or "(no oracle text on file — enrich/build the pool)").split("\n"):
                for line in (textwrap.wrap(para, width=90) or [""]):
                    print(f"    {line}")
    print("\nGrade every keep / cut / swap from the text above — not a role or tag label.")
    return 0


def cmd_stats(args):
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}.")
        return 1
    carddata = load_card_data()
    meta, cards = parse_deck_file(d["path"])

    colors, types, total = {}, {}, 0
    nonland_names = []
    for q, n, s, c in cards:
        total += q
        cd = carddata.get(n.lower())
        tline = (cd["type"] if cd else "") or ""
        ptype = "Land" if n.lower() in BASICS else _primary_type(tline)
        types[ptype] = types.get(ptype, 0) + q
        if ptype == "Land":
            continue
        nonland_names.append(n)
        col = (cd["colors"] if cd else "") or ""
        if col.lower() == "colorless":
            colors["C"] = colors.get("C", 0) + q
        else:
            for ch in col.upper():
                if ch in "WUBRG":
                    colors[ch] = colors.get(ch, 0) + q

    print(f"Deck {d['id']}: {d['name'] or d['path']}  ({total} cards)")
    print("\nTypes:")
    for t, n in sorted(types.items(), key=lambda kv: -kv[1]):
        print(f"  {t:13} {n:3}  {'#' * n}")
    print("\nColor identity (rough — run `mana` for hybrid-aware requirements):")
    for ch in "WUBRGC":
        if colors.get(ch):
            print(f"  {ch}  {colors[ch]:3}  {'#' * colors[ch]}")

    # Mana curve from real mana values.
    mana = load_mana()
    fetch_missing_mana(sorted(set(nonland_names)), mana)
    curve, unknown = {}, 0
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        d2 = carddata.get(n.lower())
        if d2 and "Land" in _primary_type(d2["type"]):
            continue
        entry = mana.get(n.lower())
        mv = entry[1] if entry else None
        if mv is None:
            unknown += q
            continue
        bucket = mv if mv < 7 else 7
        curve[bucket] = curve.get(bucket, 0) + q
    print("\nMana curve (nonland):" + (f"  [{unknown} unknown]" if unknown else ""))
    for b in range(0, 8):
        if curve.get(b):
            label = f"{b}+" if b == 7 else str(b)
            print(f"  {label:>2} MV  {curve[b]:3}  {'#' * curve[b]}")

    # Cost nature: cheaper-than-MV cards, and cards whose abilities/modes carry
    # an added cost (from Scryfall keywords + oracle text). The printed curve
    # doesn't capture either, so surface both.
    kw_by = load_keywords()
    cheaper, gated = [], []
    seen_f = set()
    for q, n, s, c in cards:
        if n.lower() in BASICS or n in seen_f:
            continue
        d2 = carddata.get(n.lower())
        if not d2 or "Land" in _primary_type(d2["type"]):
            continue
        ch, ga = classify_cost(kw_by.get(n.lower()), d2["text"])
        if ch or ga:
            seen_f.add(n)
            if ch:
                cheaper.append((n, ", ".join(ch)))
            if ga:
                gated.append((n, ", ".join(ga)))
    if cheaper:
        print("\nEffective cost may be LOWER than printed MV (◊):")
        for n, r in cheaper:
            print(f"  ◊ {n} — {r}")
    if gated:
        print("\nAbility/mode has an ADDED cost or condition — check text (△):")
        for n, r in gated:
            print(f"  △ {n} — {r}")

    xs = x_cost_cards(cards, carddata, mana)
    if xs:
        print("\nX-COST cards — the curve books these at MV 1, X counts as 0 (✕):")
        for n, c in xs:
            print(f"  ✕ {n} — {c}")
        print(f"  Read avg MV and the early-drop count with that in mind: {len(xs)} card(s) "
              "register cheaper than you will cast them.")

    # Functional roles: what jobs the nonland spells actually do. Heuristic from
    # oracle text (see classify_roles) so the tune-deck health scorecard can
    # MEASURE interaction / card advantage / ramp instead of eyeballing it.
    role_counts = role_tally(cards, carddata)
    if any(v for k, v in role_counts.items() if k in ROLE_ORDER):
        print("\nFunctional roles (heuristic from card text; a card can fill several):")
        for label in ROLE_ORDER:
            cnt = role_counts.get(label, 0)
            if cnt:
                print(f"  {label:20} {cnt:3}  {'#' * cnt}")
        # Once-per-card union (a modal removal+counter card counts once), matching the
        # audit and quality/tier vectors — NOT the sum of the buckets above.
        print(f"  {'interaction total':20} {count_conf(role_counts, 'interaction'):>7}  "
              "(distinct removal/sweeper/counter cards; +N? = cards whose text reads like "
              "interaction the classifier could NOT tag)")
        print(f"  {'card advantage':20} {count_conf(role_counts, 'card_advantage'):>7}")

    # PROTECTION axis. The role table's "Protection / trick" bucket mixes combat pumps
    # in with real answers to removal, so a deck could show a healthy trick count while
    # having no way at all to keep its key permanent alive. Report the narrow measure,
    # and say so loudly at zero — especially when a `#: protect:` header names cards the
    # deck is built around, which is the case where a single removal spell ends the game
    # plan. (Found by hand-grepping a deck, not by any tool — that gap is the point.)
    prot = role_counts.get("protection", 0)
    print(f"  {'protection':20} {prot:3}  (ward/hexproof/indestructible-class — real "
          "answers to removal, not combat pumps)")
    if not prot:
        signature = _protected(meta)
        if signature:
            print(f"    ⚠ ZERO protection, but `#: protect:` names {len(signature)} "
                  f"build-around card(s) ({', '.join(sorted(signature)[:3])}"
                  + ("…" if len(signature) > 3 else "")
                  + ") — one removal spell undoes the plan.")
        else:
            print("    ⚠ ZERO protection — nothing here answers targeted removal on a key "
                  "permanent; fine for a spell-based deck, a real gap for a threat-based one.")

    # Power-threshold payoffs. A "power 4 or greater" trigger reads unconditional to a
    # synergy model, but only fires off bodies that meet the bar on their PRINTED stats —
    # and an X-creature or a counters payoff is very often printed 0/0. This is measurable
    # only since card-pool.csv started carrying Power/Toughness.
    for name, attr, bar, qualify, total in power_threshold_flags(cards, carddata):
        print(f"\n  ⚠ {name} keys on {attr} {bar}+, but only {qualify} of {total} creature "
              f"copies are printed at {attr} {bar}+ — the trigger is far more conditional "
              f"than the card reads. (Printed stats: a body that GROWS after it enters "
              f"still won't satisfy an ENTERS trigger.)")

    # Interaction profile (#5): the raw count treats all interaction alike, but a suite
    # that's all sorcery-speed and creature-only has real gaps. Break it down by speed
    # and by whether it can answer a NONCREATURE permanent (planeswalker / enchantment /
    # artifact), and flag the gaps — measured, not eyeballed.
    ip = interaction_profile(cards, carddata)
    if ip["total"]:
        print(f"\n  Interaction profile: {ip['total']} piece(s) — {ip['instant']} instant-speed"
              f" / {ip['sorcery']} sorcery-speed · {ip['noncreature']} can answer a noncreature "
              "permanent (pw/ench/artifact)")
        for f in ip["flags"]:
            print(f"    ⚠ {f}")

    # Coverage self-audit (F15): the classifier is precise but misses phrasings, so a
    # count can silently UNDER-read. Surface the cards whose text reads like a role it
    # didn't tag, so the miss becomes an explicit "verify" instead of a silent gap.
    unclassified, under_read, no_data = role_coverage_flags(cards, carddata)
    if no_data:
        print(f"\n⚠ {len(no_data)} card(s) not in library/pool — no oracle text on file, so"
              " the interaction / card-advantage counts are a FLOOR (they contribute 0):")
        print(f"    {', '.join(no_data[:8])}{'…' if len(no_data) > 8 else ''}"
              "  — enrich them (build_pool.py) for a real count")
    if under_read:
        print("\n⚠ Possible UNDER-COUNT — text reads like a role the classifier didn't tag;"
              " verify from full text (card.py):")
        for name, axis in under_read:
            print(f"    {name}  → looks like {axis}")
    if unclassified:
        print(f"\n  (classifier found no role for {len(unclassified)} noncreature spell(s): "
              f"{', '.join(unclassified[:6])}{'…' if len(unclassified) > 6 else ''} — read if grading)")

    # Engine balance (#3): flag a lopsided two-sided engine (payoffs with no enablers,
    # or a lopsided signature engine) among the deck's CENTRAL themes — the detail and
    # card lists are in `deck.py engines`.
    cardmeta = load_card_meta()
    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = cardmeta.get(n.lower())
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    signature = _signature_themes(meta, cards, cardmeta)
    flagged = [(t, info) for t, info in
               engine_balance(cards, carddata, _central_themes(theme_w), signature).items()
               if info["flag"]]
    if flagged:
        print(f"\n⚠ Engine balance (detail: `deck.py engines {d['id']}`):")
        for t, info in flagged:
            print(f"    {t}: {info['verdict']}")

    # Zone conflicts — a card that EMPTIES a zone this deck needs populated. Engine
    # balance above asks "are the two sides of the engine in proportion"; this asks the
    # different question "is something here working AGAINST the engine", which no other
    # view covers. Reported, never scored (see zone_conflict_flags).
    zconf = zone_conflict_flags(cards, carddata)
    if zconf:
        print(f"\n⛔ Fights your own engine ({len(zconf)}) — grade from full text "
              f"(`deck.py cuts {d['id']}`):")
        for nm, _scope, why, hit in zconf:
            print(f"    {nm}: {why}")
            print(f"      needs it populated: {', '.join(hit[:4])}"
                  + (f" … (+{len(hit) - 4})" if len(hit) > 4 else ""))
    return 0


def cmd_tribes(args):
    """Creature-subtype breakdown + type-matters synergy scan."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}.")
        return 1
    _, cards = parse_deck_file(d["path"])
    data = load_card_data()

    subcount = {}
    subs_by_card = {}   # name -> set(subtypes)
    for q, n, s, c in cards:
        d2 = data.get(n.lower())
        if not d2:
            continue
        subs = creature_subtypes(d2["type"])
        if subs:
            subs_by_card[n] = set(subs)
            for st in subs:
                subcount[st] = subcount.get(st, 0) + q

    print(f"Deck {d['id']}: {d['name'] or d['path']} — creature types & synergies\n")
    print("Creature subtypes:")
    for st, cnt in sorted(subcount.items(), key=lambda kv: -kv[1]):
        print(f"  {st:14} {cnt:3}  {'#' * cnt}")

    deck_types = {st for subs in subs_by_card.values() for st in subs}
    payoffs = []
    seen_p = set()
    for q, n, s, c in cards:
        if n in seen_p:
            continue
        d2 = data.get(n.lower())
        if not d2 or not d2["text"]:
            continue
        refs = {t for t in deck_types
                if re.search(rf"\b{re.escape(t)}\b", d2["text"])}
        if refs:
            qual = sum(q2 for q2, n2, s2, c2 in cards
                       if subs_by_card.get(n2, set()) & refs)
            seen_p.add(n)
            payoffs.append((qual, n, sorted(refs)))
    if payoffs:
        print("\nType-matters payoffs (cards whose text rewards types you run):")
        for qual, n, refs in sorted(payoffs, reverse=True):
            print(f"  {n} — rewards {', '.join(refs)}  ({qual} qualifying creatures)")
    return 0


# --- deck suggestions from the pool ----------------------------------------- #
@_file_memo("DEFAULT_CSV", "POOL_CSV")
def load_card_meta():
    """name_lower -> {'colors': set(WUBRG), 'synergies': [tags]} from library then
    pool. Color(s) is color IDENTITY, which is exactly what we want for deck fit
    (a card is playable in a deck whose identity covers it)."""
    meta = {}
    for path in (DEFAULT_CSV, POOL_CSV):
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                nl = (r.get("Card Name") or "").strip().lower()
                if not nl or nl in meta:
                    continue
                cols = card_colors(r.get("Color(s)"))
                tags = [t.strip() for t in (r.get("Synergies") or "").split(";") if t.strip()]
                meta[nl] = {"colors": cols, "synergies": tags}
                meta.setdefault(nl.split(" // ")[0], meta[nl])
    return meta


# High-confidence, high-precision mechanical SUB-themes (the tag-synergy payoffs added
# for the tagging-misreads fix): a card carrying one is a deliberate build piece even at a
# small count. They sit BELOW the 25% relative centrality cutoff in a deck with a dominant
# theme, so a secondary payoff (Bark of Doran in a toughness-swap deck, Hawkeye in a ping
# deck) never surfaced — `_central_themes` admits them at a flat floor of 2 instead. Kept
# small + specific so they can't fake a generic overlap into a home (unlike the broad
# GENERIC_THEMES, which STAY gated behind the 25% cutoff).
_MECHANIC_SUBTHEMES = {"toughness matters", "noncombat damage", "spell copy"}


def _central_themes(theme_w, frac=0.25):
    """The themes that are actually CENTRAL to a deck: those carried by at least a
    quarter of the deck's most-common theme's copies (floor of 2 copies). Filters
    out one-off tag overlaps so a generic sac/tokens card doesn't read as fitting a
    deck it only grazes. Curated high-precision mechanical sub-themes
    (`_MECHANIC_SUBTHEMES`) are also admitted at a flat floor of 2, so a real 2-card
    payoff sub-synergy reads central even under a heavier dominant theme (the
    specific-effect analog of the `#: protect:` signature rescue)."""
    if not theme_w:
        return set()
    cutoff = max(2, frac * max(theme_w.values()))
    return {t for t, w in theme_w.items()
            if w >= cutoff or (t in _MECHANIC_SUBTHEMES and w >= 2)}


# Themes carried by nearly every deck — low signal for how KEY a fit is (mirrors
# wishlist.NON_SIGNAL_TAGS's intent, kept local so deck.py has no wishlist import).
# Covers the broad "matters" generics (etb/tokens/counters/…), generic card-quality
# themes (selection/value — most decks scry/dig), AND the evergreen combat keywords
# (a card sharing only "flying" or "ward" with a deck is not a synergy fit). Keeping
# these out of the "specific" set is what stops a generically-good removal or card-
# advantage card reading KEY in every deck it merely shares an incidental tag with.
GENERIC_THEMES = {
    "etb", "tokens", "counters", "lifegain", "sacrifice", "card draw", "graveyard",
    "mana", "ramp", "combat", "aggro", "tempo", "pump", "removal", "evasion",
    "flying", "trample", "menace", "deathtouch", "lifelink", "vigilance",
    "selection", "value", "first strike", "double strike", "haste", "reach",
    "prowess", "ward", "hexproof", "indestructible", "protection", "defense",
    "defender", "resilience", "shroud", "fear", "intimidate",
}
# Creature tribes so broad they carry no HOME signal — nearly every creature in a
# superhero/anime multiverse is a Human and a Hero or Villain, so sharing one is not a
# synergy. Treated as generic by `fit_strength` (the tribal analog of GENERIC_THEMES) so a
# card doesn't read KEY in a deck merely for sharing a background tribe (the Hawkeye-"KEY"-
# in-every-Hero/Human-deck over-assignment). Narrow, build-around tribes (Ninja, Cat,
# Dinosaur, Knight, Wizard, Merfolk, …) are deliberately NOT here — those ARE real
# signature themes. A genuine broad-tribe payoff (a "Heroes you control get +1/+1" lord)
# can still read KEY via the deck's `#: protect:` signature; this only stops a BARE shared
# tribe from carrying a home by itself. Kept separate from GENERIC_THEMES so other
# consumers (which compare Title-case) are unaffected — fit_strength lowercases.
_GENERIC_TRIBES = {"human", "hero", "villain"}


def role_tally(cards, carddata):
    """The CANONICAL per-deck functional-role tally — the single source every view
    (stats, audit, quality/tier) routes through so their interaction / card-advantage
    numbers can't drift apart (they used to: three separate counters disagreed by ±1,
    which is exactly the kind of gap that could move a tier band the user couldn't
    reproduce in `stats`). Rules, fixed once here:
      • quantity-weighted (2 copies of a removal spell = 2 interaction),
      • a card counts ONCE toward 'interaction' regardless of how many interaction
        roles it fills (a modal removal+counter card is one interaction card, not
        two — the per-role buckets still credit each role for the stats display),
      • basics and nonbasic lands are skipped.
    Returns a dict: each role → weighted count, plus 'interaction' (once-per-card
    union of Removal/Sweeper/Counter), 'card_advantage', and 'protection' (real
    ward/hexproof/indestructible-class effects — see `protection_effects`)."""
    per_role = {}
    interaction = ca = prot = 0
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        cd = carddata.get(n.lower())
        if not cd or "Land" in _primary_type(cd["type"]):
            continue
        roles = set(classify_roles(cd["text"]))
        for r in roles:
            per_role[r] = per_role.get(r, 0) + q
        if roles & _INTERACTION_ROLES:
            interaction += q
        if "Card advantage" in roles:
            ca += q
        if protection_effects(cd["text"]):
            prot += q
    per_role["interaction"] = interaction
    per_role["card_advantage"] = ca
    per_role["protection"] = prot
    # CONFIDENCE, carried WITH the count. The classifier reports a false negative as a
    # fact: a card it can't parse contributes 0, and `0` reads as "none" rather than
    # "not detected". That is the single most damaging failure this toolkit has had — a
    # deck graded on interaction 3 when a hand count said 7, because three cards that
    # unambiguously interact scored zero roles. `role_coverage_flags` already computed
    # this, but printed it as a separate warning several lines away, so the NUMBER still
    # read as fact. Attaching the remainder to the tally means every consumer gets it.
    unclassified, under_read, no_data = role_coverage_flags(cards, carddata)
    # Quantity-weight the uncertainty the SAME way the counts themselves are weighted.
    # `interaction`/`card_advantage`/`protection` above are quantity-weighted (2 copies of
    # a removal spell = 2), but these remainders were CARD counts — so `8 +4?` compared a
    # weighted base against an unweighted remainder, and a deck running 4x of a card with
    # no oracle text on file reported "+1?" when four copies were unread (broad-scan
    # F-09). Understating uncertainty is the wrong direction for a signal whose entire
    # job is to stop a heuristic count from reading as fact.
    #
    # Dedupe by name first: role_coverage_flags emits one entry per LINE, so a card split
    # across two printing lines would otherwise be weighted by its full quantity twice.
    # (No deck on the roster does that today; the guard is for when one does.)
    _qty_of = {}
    for _q, _n, _s, _c in cards:
        _qty_of[(_n or "").lower()] = _qty_of.get((_n or "").lower(), 0) + _q
    def _weigh(names):
        return sum(_qty_of.get((n or "").lower(), 1) for n in dict.fromkeys(names))
    per_role["interaction_unread"] = _weigh([n for n, ax in under_read if "interaction" in ax])
    per_role["card_advantage_unread"] = _weigh([n for n, ax in under_read if "card advantage" in ax])
    # `unclassified` is the WORSE case and must not be invisible: a noncreature spell that
    # matched no role AND tripped no broad cue. That is exactly Broken Wings and Repulsive
    # Mutation — cards that unambiguously interact and scored zero. It can't be attributed
    # to a single axis, so it is reported globally rather than folded into one count.
    per_role["unclassified"] = _weigh(unclassified)
    per_role["unreadable"] = _weigh(no_data)
    return per_role


def count_conf(tally, key):
    """A measured count rendered with its uncertainty: `7`, or `3 +2?` when 2 more cards
    read like that role but the classifier couldn't tag them. Use this ANYWHERE a role
    count is shown to a human — a bare number invites exactly the over-trust that a
    heuristic classifier doesn't deserve."""
    n = tally.get(key, 0)
    unread = tally.get(f"{key}_unread", 0)
    unclass = tally.get("unclassified", 0)
    bad = tally.get("unreadable", 0)
    out = str(n)
    if unread:
        out += f" +{unread}?"
    notes = []
    if unclass:
        notes.append(f"{unclass} unclassified")
    if bad:
        notes.append(f"{bad} unreadable")
    if notes:
        out += f" ({', '.join(notes)})"
    return out


# Text cues that an interaction spell can hit a NONCREATURE permanent (planeswalker /
# enchantment / artifact) or any target — the "reach past creatures" test for #5.
_NONCREATURE_ANSWER_CUES = [re.compile(p) for p in [
    r"destroy target permanent", r"exile target permanent", r"return target permanent",
    r"destroy target (artifact|enchantment)", r"destroy target artifact or enchantment",
    r"exile target (artifact|enchantment)", r"target permanent you don't control",
    r"destroy target[^.]*planeswalker", r"destroy target[^.]*or planeswalker",
    r"exile target[^.]*planeswalker", r"destroy all permanents", r"destroy each",
    r"any target",  # burn to any target answers a planeswalker (and the opponent)
    r"deals? \d+ damage to any target", r"destroy target nonland permanent",
    # The planeswalker rows above allow ANY text between "target" and the type
    # (`[^.]*`, sentence-bounded); the artifact/enchantment rows required the type to
    # follow "target" IMMEDIATELY. So "destroy target creature or PLANESWALKER" counted
    # and "destroy target creature or ENCHANTMENT" did not — the same list, templated
    # the other way round. Measured misses when this was found: Withering Torment and
    # Feed the Swarm, i.e. the only two enchantment answers on the whole roster.
    r"destroy target[^.]*\b(artifact|enchantment)", r"exile target[^.]*\b(artifact|enchantment)",
    # Split template — see the Removal (spot) note on Quag Feast. "Choose target
    # creature, planeswalker, or Vehicle … destroy the chosen permanent" reaches past
    # creatures, but names the types a sentence away from the verb.
    r"choose target[^.]*\b(planeswalker|artifact|enchantment|vehicle|spacecraft|permanent)",
]]


def interaction_profile(cards, carddata):
    """Qualitative interaction breakdown (#5): beyond the raw count, how much of a deck's
    interaction is INSTANT-speed vs sorcery-speed, and how much can answer a NONCREATURE
    permanent (planeswalker / enchantment / artifact) — so 'thin against planeswalkers /
    all sorcery-speed' is measured, not eyeballed. Quantity-weighted, once per card.

    Returns {total, instant, sorcery, noncreature, flags:[…]}. Heuristic: instant-speed =
    an Instant, a card with Flash, or a Counter (counters resolve at instant speed);
    noncreature-answer = a Counter (answers any spell) or a removal cue that reaches past
    creatures."""
    total = instant = sorcery = noncreature = 0
    # Quantity-weighted per card, summed ACROSS lines: a card split over two lines
    # (e.g. two printings) must count its full quantity, matching the canonical
    # role_tally — a `seen`-set + first-line q under-counted it (audit A11).
    qty_by_name = {}
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS:
            continue
        qty_by_name[nl] = qty_by_name.get(nl, 0) + q
    for nl, q in qty_by_name.items():
        cd = carddata.get(nl)
        if not cd:
            continue
        text = cd.get("text") or ""
        roles = classify_roles(text)
        if not (roles & _INTERACTION_ROLES):
            continue
        total += q
        tl = (cd.get("type") or "").lower()
        tx = text.lower()
        is_counter = "Counter" in roles
        # `\bflash\b` matches the Flash keyword but NOT "flashback" — a sorcery-speed
        # flashback recast is not instant-speed interaction (audit A7).
        if "instant" in tl or re.search(r"\bflash\b", tx) or is_counter:
            instant += q
        else:
            sorcery += q
        if is_counter or any(p.search(tx) for p in _NONCREATURE_ANSWER_CUES):
            noncreature += q
    flags = []
    if total >= 3 and instant == 0:
        flags.append("all sorcery-speed — no instant-speed answers (you can't react)")
    if total >= 3 and noncreature == 0:
        flags.append("no answer to a noncreature permanent (planeswalkers / enchantments / "
                     "artifacts slip through)")
    return {"total": total, "instant": instant, "sorcery": sorcery,
            "noncreature": noncreature, "flags": flags}


def deck_role_counts(cards, carddata):
    """(interaction, card_advantage) for a deck, from the canonical `role_tally` —
    used to tell whether a candidate card FILLS A GAP (interaction / card advantage
    the deck is short on), which makes an otherwise-secondary fit a KEY one."""
    t = role_tally(cards, carddata)
    return t["interaction"], t["card_advantage"]


def fit_strength(shared, theme_w, card_text, deck_int, deck_ca, signature=frozenset()):
    """Classify a card→deck fit as KEY / role-player / tangential (F04).

      KEY          – shares the deck's SIGNATURE theme (top central theme, OR a theme
                     carried by the deck's `#: protect:` cards), OR shares a SPECIFIC
                     (non-generic) theme AND fills a role the deck is short on
                     (interaction < 5 / card advantage < 3), OR shares the deck's most-
                     common specific theme.
      role-player  – shares a specific central theme, but not the signature.
      tangential   – shares only GENERIC themes (etb/tokens/…) or broad background tribes
                     (_GENERIC_TRIBES: Human/Hero/Villain): broadly playable, not a home.

    `signature` corrects the idf blind spot: a theme in GENERIC_THEMES is still
    SPECIFIC-for-this-deck if the deck protects cards built on it — so a counter-doubler
    in a counters deck reads KEY, not tangential. Callers must pass the STRICT
    `_strong_signature_themes` (a theme carried by >=2 `#: protect:` cards), NOT the
    loose `_signature_themes` that unions every protected card's tags. With the loose
    set, deck 37's signature held 25 themes including etb / removal / sacrifice /
    combat / tempo, so almost any card sharing any of them read KEY — Azula, Cunning
    Usurper (a Human Noble Rogue) read KEY for three WIZARD-tribal decks on `Human, etb`
    alone. `similar` already used the strict set for exactly this reason. The motivating
    rescue is unaffected: deck 30's strict signature is precisely {counters}.

    The role-gap KEY is gated on a SPECIFIC-theme match (checked AFTER the `not
    specific` short-circuit below): a generically-good removal / card-advantage card
    would otherwise read KEY in every low-interaction deck it merely shares an
    etb/tokens tag with (the Get-Lost-"KEY"-in-15-decks over-assignment). Its broad
    utility is real, but it belongs to the cross-deck BREADTH signal (wishlist `use`
    column), not a specific home — so a fit resting only on generic themes stays
    tangential even when the deck happens to be short on that role.
    """
    specific = [t for t in shared
                if (t.lower() not in GENERIC_THEMES or t in signature)
                and t.lower() not in _GENERIC_TRIBES]
    # A signature-theme match is a genuine home (the deck's spine) — but a broad
    # background tribe (Human/Hero/Villain) is NOT a signature even when a protected card
    # happens to carry it, so it can't mint a KEY by itself (tagging-misreads #4).
    if signature and any(t in signature and t.lower() not in _GENERIC_TRIBES
                         for t in shared):
        return "KEY"
    # No SPECIFIC shared theme -> at most GENERICALLY playable here, not a synergy home.
    # Checked BEFORE the role-gap branch on purpose (see docstring).
    if not specific:
        return "tangential"
    roles = set(classify_roles(card_text or ""))
    gap = (bool(roles & _INTERACTION_ROLES) and deck_int < 5) or \
          ("Card advantage" in roles and deck_ca < 3)
    if gap:                       # on a specific theme AND fills a role the deck lacks
        return "KEY"
    top = max(theme_w.values()) if theme_w else 0
    if top and any(theme_w.get(t, 0) >= top for t in specific):
        return "KEY"
    return "role-player"


def cross_deck_breadth(card_colors, card_themes, fps):
    """How many decks a card is BOTH castable in AND shares ≥1 SPECIFIC theme with —
    the single definition of "cross-deck breadth" in this toolkit.

    `fps` is [(deck_id, castable_colors:set, specific_themes:set), …]. Callers supply
    their own per-deck specific-theme set, because the two ranking models legitimately
    decide "specific" differently and that difference is deliberate:
      • `deck.suggest_scored` uses the GENERIC_THEMES/_GENERIC_TRIBES denylist plus the
        `#: protect:` signature rescue (`_sim_specific`), the same test `similar` uses;
      • `wishlist._rank_scores` uses the idf threshold (`spec_idf`) + NON_SIGNAL_TAGS,
        which self-calibrates to the deck count.
    What must NOT differ is the COUNTING RULE, and it used to: two hand-written copies
    drifted until one required a specific theme and the other accepted any central one,
    so `suggest`'s column saturated at 99% while the wishlist's stayed meaningful
    (broad-scan F-04). Routing both through here makes that impossible; `check_suggest`
    anchor 13 asserts the two agree on a synthetic card."""
    return sum(1 for _id, dcols, dthemes in fps
               if card_colors <= dcols and (card_themes & dthemes))


def _deck_fingerprints(meta, exclude_id=None):
    """[(id, colors:set, specific_central_themes:set), ...] for every deck — used to
    score a craft target's cross-deck reuse (a card that fits several of your decks is
    worth more per wildcard). Colors are the deck's declared `#: colors:` (else the
    union of its cards' identities).

    Themes are the deck's central synergy tags NARROWED TO THE SPECIFIC ones — the
    same `_sim_specific` test `similar` uses, so a GENERIC theme (etb / tokens /
    counters / lifegain …) or a broad background tribe can't carry a home, while a
    generic theme that IS this deck's `#: protect:` spine still counts. Centrality
    alone was not enough: nearly every deck is central on the same handful of generic
    themes, so the reuse count saturated — 99% of a deck's picks scored >=3 and the
    median pick "fit" 31 of 56 other decks, which made the ★ high-reuse callout and
    the per-wildcard signal it feeds carry no information at all (audit F-04). This is
    the gate `wishlist._rank_scores` already applies to its own breadth column; the
    two now measure the same thing.

    VARIANTS ARE COLLAPSED to their core deck. A variant is an alternate build of the
    same archetype, so counting 19, 19b and 19c as three homes triple-counts one deck's
    worth of value — the second inflation source in this signal, and the same reasoning
    `wishlist._theme_model` documents for its own idf/breadth model. Excluding a deck by
    `exclude_id` therefore excludes its whole family, so analyzing 19b can't count 19.

    `exclude_id` drops one deck from the roster (the deck being analyzed), so a
    suggestion's reuse count is 'how many OTHER decks it fits' — otherwise the
    current deck always counts itself and inflates every score by one."""
    fps = []
    skip_core = None
    if exclude_id is not None:
        skip_core = next((d["core"] for d in roster_decks()
                          if d["id"].lower() == exclude_id.lower()), None)
    for dd in roster_decks():
        if dd["variant"]:
            continue                      # an alternate build of a core already counted
        if exclude_id is not None and (dd["id"].lower() == exclude_id.lower()
                                       or (skip_core is not None and dd["core"] == skip_core)):
            continue
        dm, cards = parse_deck_file(dd["path"])
        colors, ident, theme_w = _declared_colors(dm), set(), {}
        for q, n, s, c in cards:
            if n.lower() in BASICS:
                continue
            m = meta.get(n.lower())
            if not m:
                continue
            ident |= m["colors"]
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
        # A generic theme is rescued only when it's a real BUILD-AROUND spine (carried
        # by >=2 `#: protect:` cards) — the stricter signature test, so a lone protected
        # bomb's incidental etb/card-draw tag can't re-open the saturation it closes.
        sig = _strong_signature_themes(dm, cards, meta)
        specific = {t for t in _central_themes(theme_w) if _sim_specific(t, sig)}
        fps.append((dd["id"], colors or ident, specific))
    return fps


POOL_BUILD_STAMP = os.path.join(REPO_ROOT, "card-pool.build")


def pool_staleness_days():
    """Days since card-pool.csv was built (from the card-pool.build sidecar), or
    None if unstamped. Standard rotates on a schedule, so an old pool can still
    mark a rotated-out card as `standard` — this lets `suggest` warn and prompt a
    rebuild. Dormant until a `build_pool.py` run writes the stamp."""
    if not os.path.exists(POOL_BUILD_STAMP):
        return None
    try:
        import datetime
        built = datetime.date.fromisoformat(open(POOL_BUILD_STAMP).read().strip()[:10])
        return (datetime.date.today() - built).days
    except Exception:
        return None


# Sets whose Standard legality does NOT follow the release-date + 3 years rule, keyed
# by Arena set code → the year they actually leave Standard.
#
# FOUNDATIONS is the case that matters: it is deliberately Standard-legal for FIVE years
# (through 2029), not three. Because the pool keys ONE printing per card, a card whose
# newest printing is in FDN inherits FDN's 2024 release date and read "⚠rot~2027" — so
# Genesis Wave, legal for another four years, was flagged as "don't spend a wildcard on
# a card about to leave the format." CLAUDE.md documented the reprint caveat in prose;
# this encodes it. Add a row here whenever a set gets an announced non-standard window.
_SET_ROTATION_OVERRIDE = {
    "FDN": 2029,   # Foundations — announced Standard-legal through 2029
}


def rotation_year(released, years=3, set_code=""):
    """The year a set rotates out of Standard — its release year + `years` (Standard's
    ~3-year window), or an announced date from `_SET_ROTATION_OVERRIDE`. None if the
    date is blank/unparseable. The single primitive behind `rotation_sweep`, the
    wishlist ⚠rot flag and `rotation_risk`, so 'when does this rotate' is computed one
    way everywhere."""
    override = _SET_ROTATION_OVERRIDE.get((set_code or "").strip().upper())
    if override:
        return override
    try:
        return int((released or "")[:4]) + years
    except (ValueError, TypeError):
        return None


def rotation_risk(released, years=3, set_code=""):
    """True if a card is past ~`years` of Standard life — so a still-`standard`-marked
    pick may have rotated (stale pool) or rotates soon. Routed through `rotation_year`
    so an announced long-legality set (Foundations) can't be false-flagged. Empty or
    unparseable `released` → False (graceful before a pool rebuild captures the column)."""
    import datetime
    yr = rotation_year(released, years, set_code)
    return bool(yr) and yr <= datetime.date.today().year


def _pool_rotation_index():
    """name_lower (full AND DFC front) -> (released, {legalities}, set_code) from the pool.
    Returns (index, has_released). `has_released` is False for a pool built before the
    Released column existed — callers then warn instead of silently reporting nothing."""
    idx, has_released = {}, False
    if not os.path.exists(POOL_CSV):
        return idx, has_released
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        has_released = "Released" in (rdr.fieldnames or [])
        for r in rdr:
            nl = (r.get("Card Name") or "").strip().lower()
            if not nl:
                continue
            info = ((r.get("Released") or "").strip(),
                    {x.strip().lower() for x in (r.get("Legalities") or "").split(";") if x.strip()},
                    (r.get("Set Code") or "").strip())
            idx.setdefault(nl, info)
            idx.setdefault(nl.split(" // ")[0], info)  # DFC front-face fallback
    return idx, has_released


def rotation_sweep(fmt="standard", years=3, within=2):
    """Roster-wide rotation exposure for `fmt` (default Standard): which cards each deck
    runs are CLOSEST to rotating, so you can see what rotates NEXT and which decks it
    hits. A card's rotation year is its set's release year + `years` (Standard's ~3-year
    window); a card is surfaced when that year is within `within` years of now — i.e. it
    rotates this year, soon, or is already past-due (a stale-pool signal). Reads the
    pool's Released/Legalities snapshot (the same data `suggest`'s ⚠rot flag uses). Note:
    gating on release-age here (rather than `rotation_risk`'s strict >years boolean) is
    deliberate — on a freshly-built pool every still-legal card is BY DEFINITION inside
    the window, so the >years test would report nothing; the point is what rotates *next*.
    Offline.

    Returns (decks, rollup, meta):
      decks  = [{id, name, atrisk:[{name,set,rotates,qty}], n_slots}] for `fmt` decks,
               most-exposed first (each at-risk list sorted soonest-rotating first).
      rollup = {rotates_year: {'slots':n, 'cards':set, 'decks':set}} (a card counted per
               deck it appears in — "deck-slots" — since the point is roster exposure).
      meta   = {has_released, stale_days, unverified, n_decks, this_year, within}.

    Caveat: the pool keys one representative printing per card, so a card reprinted into a
    newer Standard set may carry an OLDER printing's Released — its rotation year can read
    earlier than reality. Verify against the official schedule before disenchanting.
    """
    import datetime
    this_year = datetime.date.today().year
    pool, has_released = _pool_rotation_index()
    fmt = (fmt or "").strip().lower()
    decks_out, rollup, unverified = [], {}, 0
    for d in roster_decks():
        dm, cards = parse_deck_file(d["path"])
        if fmt and (dm.get("format") or "").strip().lower() != fmt:
            continue
        atrisk = []
        for q, n, s, c in cards:
            nl = n.lower()
            if nl in BASICS:
                continue
            info = pool.get(nl) or pool.get(nl.split(" // ")[0])
            if not info:
                unverified += 1
                continue
            released, legals, setc = info
            if fmt and legals and fmt not in legals:
                continue  # not legal in this format anyway — it can't "rotate out" of it
            rotates = rotation_year(released, years, setc)
            if rotates is None:
                continue  # no usable release date — can't place it on the timeline
            if rotates > this_year + within:
                continue  # not rotating within the horizon
            atrisk.append({"name": n, "set": setc or s, "rotates": rotates, "qty": q})
            rr = rollup.setdefault(rotates, {"slots": 0, "cards": set(), "decks": set()})
            rr["slots"] += 1
            rr["cards"].add(n)
            rr["decks"].add(d["id"])
        atrisk.sort(key=lambda x: (x["rotates"], x["name"]))
        decks_out.append({"id": d["id"], "name": d["name"] or d["id"],
                          "atrisk": atrisk, "n_slots": len(atrisk)})
    decks_out.sort(key=lambda x: (-x["n_slots"], x["id"]))
    meta = {"has_released": has_released, "stale_days": pool_staleness_days(),
            "unverified": unverified, "n_decks": len(decks_out),
            "this_year": this_year, "within": within}
    return decks_out, rollup, meta


def _brawl_commanders(cards, carddata):
    """[(name, identity_set)] for each legendary creature/planeswalker in the deck —
    the candidate commanders. Deduped, basics/non-carddata skipped."""
    out, seen = [], set()
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in seen or nl in BASICS:
            continue
        seen.add(nl)
        cd = carddata.get(nl) or carddata.get(nl.split(" // ")[0])
        if not cd:
            continue
        t = cd.get("type", "") or ""
        if "Legendary" in t and ("Creature" in t or "Planeswalker" in t):
            out.append((n, card_colors(cd.get("colors", ""))))
    return out


def brawl_readiness(fmt_filter="standard"):
    """Roster-wide 'distance to a legal Brawl conversion' per deck (#2). For each deck in
    `fmt_filter`, pick the best in-deck commander (the legendary creature/PW whose color
    identity leaves the FEWEST cards stray), then measure how far the deck is from a legal
    Brawl build: cards to de-duplicate to singleton + cards outside that commander's
    identity + any Brawl-illegal cards. Reuses the same identity/commander rules
    `deck.py legal` enforces, so the estimate can't drift from the actual check. Offline.

    Returns rows sorted closest-first: [{id, name, colors, commander, cmd_ident, dup,
    stray, notlegal, distance, no_commander, converted}], plus a `converted` flag when a
    `<core>-brawl` variant already exists."""
    carddata = load_card_data()
    leg = load_legalities()
    # cores that already have a Brawl variant (so we can mark them done)
    converted = {d["core"] for d in roster_decks()
                 if str(d["id"]).endswith("-brawl")}
    fmt_filter = (fmt_filter or "").strip().lower()
    rows = []
    for d in roster_decks():
        meta, cards = parse_deck_file(d["path"])
        if fmt_filter and (meta.get("format") or "").strip().lower() != fmt_filter:
            continue
        declared = _declared_colors(meta)
        tot, disp = {}, {}
        for q, n, s, c in cards:
            nl = n.lower()
            if nl in BASICS:
                continue
            tot[nl] = tot.get(nl, 0) + q
            disp.setdefault(nl, n)
        dup = sum(1 for nl, q in tot.items() if q > 1)
        notlegal = sum(1 for nl in tot
                       if leg.get(nl) is not None and "brawl" not in leg[nl])
        idents = {nl: card_colors((carddata.get(nl) or carddata.get(nl.split(" // ")[0])
                                   or {}).get("colors", "")) for nl in tot}

        best = None  # (name, ident, strays)
        for name, ident in _brawl_commanders(cards, carddata):
            strays = sum(1 for nl, ci in idents.items() if not ci <= ident)
            # Prefer fewest strays; tiebreak an exact deck-color match, then broader ident.
            key = (strays, ident != declared, -len(ident), name)
            if best is None or key < best[0]:
                best = (key, name, ident, strays)
        no_commander = best is None
        stray = best[3] if best else len(tot)
        distance = dup + stray  # card-swaps to reach a legal Brawl 60 (basics refill)
        rows.append({
            "id": d["id"], "name": d["name"] or d["id"],
            "colors": (meta.get("colors") or "").strip().upper(),
            "commander": best[1] if best else None,
            "cmd_ident": "".join(sorted(best[2])) or "C" if best else "",
            "dup": dup, "stray": stray, "notlegal": notlegal,
            "distance": distance, "no_commander": no_commander,
            "converted": d["core"] in converted,
        })
    rows.sort(key=lambda r: (r["no_commander"], r["distance"], r["id"]))
    return rows


def suggest_scored(d, *, unowned=False, owned=False, limit=0, fmt=None, any_format=False):
    """Structured core of `suggest` — returns the scored, sorted, limited picks as
    plain dicts so both `cmd_suggest` (renders below) and build_dashboard.py (craft
    table) read from ONE code path and can't drift. See `cmd_suggest` for how each
    field is displayed.

    Returns a dict:
      ok         – False if there's nothing to score (see `reason`).
      reason     – 'no-pool' | 'no-themes' when ok is False.
      colors     – the deck's castable colors (WUBRG set).
      themes     – top-6 [(theme, weight)] for the header line.
      fmt/apply_fmt/has_leg – format-filter state for the header messages.
      picks      – [{name, rarity, owned, decks, score, matches:[themes]}], ranked.
                   `decks` = cross-deck reuse: other decks the card is castable in AND
                   shares a SPECIFIC central theme with (see `_deck_fingerprints`).
      total      – len(picks) (== the shown count).
      hi_reuse   – [(name, decks)] for craftable picks that fit >=3 other decks.
    """
    res = {"ok": False, "reason": None, "colors": set(), "themes": [], "fmt": "",
           "apply_fmt": False, "has_leg": False, "picks": [], "total": 0, "hi_reuse": []}
    if not os.path.exists(POOL_CSV):
        res["reason"] = "no-pool"
        return res

    dmeta, cards = parse_deck_file(d["path"])
    meta = load_card_meta()

    # Format filter: default to the deck's own `#: format:` (--format overrides,
    # --any-format disables). Only bites when the pool carries legality data.
    fmt = "" if any_format else (fmt or dmeta.get("format") or "").strip().lower()

    # Deck fingerprint: theme weights from synergy tags (copies carrying each tag).
    # Front-face normalized: deck files store a DFC under its FRONT name while the pool
    # keys the full "Front // Back", so normalizing both sides to the front lets the
    # "already in deck" filter below catch a DFC that's already maindecked (audit A8/F6).
    deck_names = {n.lower().split(" // ")[0] for _, n, _, _ in cards}
    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = meta.get(n.lower())
        if not m:
            continue
        for t in m["synergies"]:
            theme_w[t] = theme_w.get(t, 0) + q
    if not theme_w:
        res["reason"] = "no-themes"
        return res

    # Deck function + curve profile for the gap-aware scoring below (improvements
    # #1/#2): how many of each functional role the deck ALREADY runs, and its nonland
    # mana curve, so a candidate is weighted by what the deck NEEDS, not just theme fit.
    carddata = load_card_data()
    mana_map = load_mana()
    deck_roles = role_tally(cards, carddata)   # role → copies already in the deck
    deck_curve = {}                            # nonland MV bucket → copies
    for q, n, s, c in cards:
        nl2 = n.lower()
        if nl2 in BASICS:
            continue
        cd2 = carddata.get(nl2)
        if cd2 and "Land" in _primary_type(cd2.get("type") or ""):
            continue
        e = mana_map.get(nl2)
        if e and e[1] is not None:
            b = min(int(e[1]), 7)
            deck_curve[b] = deck_curve.get(b, 0) + q

    # Deck colors = the colors the deck can actually CAST. Prefer the declared
    # `#: colors:`; else derive from mana COSTS — never color identity, so a card's
    # off-color activated abilities don't widen the deck and surface uncastable picks.
    deck_colors = _declared_colors(dmeta)
    if not deck_colors:
        for q, n, s, c in cards:
            if n.lower() in BASICS:
                continue
            entry = mana_map.get(n.lower())
            if entry and entry[0]:
                strict, hybrid = parse_pips(entry[0])
                # Only a TRUE multicolor hybrid ({W/U}) constrains castable colors;
                # a monocolor hybrid ({2/W}) or Phyrexian ({W/P}) is payable WITHOUT
                # its color, so it must not widen the deck's colors and surface
                # uncastable picks (audit F3; mirrors _castability's len(h) >= 2).
                deck_colors |= set(strict) | {x for h in hybrid if len(h) >= 2 for x in h}

    # Score every pool card not already in the deck.
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        pool = list(csv.DictReader(fh))
    has_leg = bool(pool) and "Legalities" in pool[0]
    apply_fmt = bool(fmt) and fmt in POOL_FORMATS and has_leg
    _, _, by_name_qty = load_collection()
    suggestions = []
    for r in pool:
        name = (r.get("Card Name") or "").strip()
        nl = name.lower()
        if not name or nl.split(" // ")[0] in deck_names or nl in BASICS:
            continue
        # CASTABILITY IS READ FROM THE PRINTED COST, not from color identity. The block
        # above is careful to derive the DECK's colors from costs "never color identity";
        # this filter then compared CANDIDATES on identity, so the two halves disagreed.
        # A `{1}{U/R}` hybrid and a `{6}` colorless card are both castable in mono-U or
        # mono-R and both read as off-color in `Color(s)`, so `suggest` could never
        # surface either for any deck. Measured on the red pool: 55 Standard cards a red
        # filter hides that mono-red can cast, including two Dragons at MV 4 whose absence
        # led to a written conclusion that deck 49's curve could not be fixed (G-58,
        # bulk-triage variant). `_candidate_castability` mirrors `_castability_lint`, so
        # a monocolor/Phyrexian hybrid never constrains and only a TRUE multicolor one does.
        ccolors = card_colors(r.get("Color(s)"))
        cast_ok, _ = _candidate_castability(
            (mana_map.get(nl) or mana_map.get(nl.split(" // ")[0]) or ("", None))[0],
            ccolors, deck_colors)
        if not cast_ok:
            continue  # genuinely uncastable for this deck
        if apply_fmt and fmt not in {x.strip() for x in
                                     (r.get("Legalities") or "").split(";")}:
            continue  # not legal in the target format
        shared = [t for t in (r.get("Synergies") or "").split(";")
                  if t.strip() and t.strip() in theme_w]
        if not shared:
            continue
        shared = [t.strip() for t in shared]
        # Theme fit + gap-aware role credit + curve fit. Among on-theme picks, a card
        # that fills a high-value functional role the deck is THIN on (removal / card
        # advantage / ramp / cost-reduction / payoff) outranks a same-theme vanilla body
        # — but that role bonus DIMINISHES if the deck already runs plenty of it (#1), so
        # `suggest` stops recommending the 9th removal spell. The whole score is then
        # nudged by how the card's MV fits the deck's curve (#2) — bounded ±15%, so it
        # re-ranks near-ties without overriding a clear theme-fit winner. Reads the
        # pool's Card Text; a text-less / mana-less row just gets no bonus / factor 1.0.
        roles = classify_roles(r.get("Card Text") or "")
        base = sum(theme_w[t] for t in shared) + _role_credit(roles, deck_roles)
        cand_mv = (mana_map.get(nl) or (None, None))[1]
        # Card-quality (power) co-signal (#6): a heuristic 1–10 power seed (rarity floor +
        # roles + planeswalker/legendary), added modestly so an owned/craftable BOMB with
        # only MODEST theme overlap isn't buried under a well-tagged vanilla body. It can't
        # pull in off-theme junk — only cards already sharing ≥1 theme are scored here — so
        # it re-ranks WITHIN the on-theme set, the way wishlist --rank pairs fit with power.
        score = round(base * _curve_gap_factor(cand_mv, deck_curve) + _SUGGEST_POWER_W * _power_seed(r), 2)
        suggestions.append((score, name, r, shared))

    # Ownership is keyed by the LIBRARY name (DFCs stored under their front face), but
    # pool card names are the full "Front // Back" — the shared lib.owned_qty falls
    # back to the front so an owned DFC isn't mis-surfaced as a craft target (audit F6).
    owned_of = lambda nl: owned_qty(by_name_qty, nl)
    if unowned:
        suggestions = [x for x in suggestions if owned_of(x[1].lower()) == 0]
    if owned:
        suggestions = [x for x in suggestions if owned_of(x[1].lower()) > 0]
    # Rank: strongest theme fit first, then NAME for a total order (G-54).
    # Ownership used to be the tiebreaker, 'so quick adds float up' — which meant that
    # at equal fit the owned card always printed above the unowned one, and a reader
    # working down the list met the owned pool first by construction. Two reasons that
    # is wrong: the goal is the best LIST, not the cheapest one, and this repo's
    # owned/unowned data is hand-maintained, so the tiebreak silently ranks on
    # information that may be weeks stale. Ownership is still SHOWN on every row
    # (`×N` / `craft R`) — it is a note, not a ranking term. The `--owned` /
    # `--unowned` FILTERS are untouched: those are the user asking a scoped question.
    suggestions.sort(key=lambda x: (-x[0], x[1].lower()))
    top = suggestions if limit == 0 else suggestions[:limit]

    fps = _deck_fingerprints(meta, exclude_id=d["id"])
    picks, hi_reuse = [], []
    for score, name, r, shared in top:
        h = owned_of(name.lower())
        card_cols = card_colors(r.get("Color(s)"))
        card_themes = {t.strip() for t in (r.get("Synergies") or "").split(";") if t.strip()}
        fits = cross_deck_breadth(card_cols, card_themes, fps)
        if h == 0 and fits >= 3:
            hi_reuse.append((name, fits))
        picks.append({"name": name, "rarity": (r.get("Rarity") or "").strip(),
                      "owned": h, "decks": fits, "score": score, "matches": shared,
                      "rotates": rotation_risk(r.get("Released") or "", set_code=r.get("Set Code") or "")})

    res.update(ok=True, colors=deck_colors,
               themes=sorted(theme_w.items(), key=lambda kv: -kv[1])[:6],
               fmt=fmt, apply_fmt=apply_fmt, has_leg=has_leg,
               picks=picks, total=len(top), hi_reuse=hi_reuse)
    return res


def suggest_lands(d, unowned=False, owned=False, limit=20, fmt=None, any_format=False):
    """Recommend LANDS for a deck's manabase — the axis theme-based `suggest` is blind to
    (it filters candidates to cards sharing a synergy theme, and lands rarely do, so it can
    never surface a manabase upgrade). Scores each on-color land by FIXING value
    (`wishlist._land_value`: produces the deck's colors, untapped premium — the DOMINANT
    axis) PLUS a bounded SYNERGY nudge (a land whose ability plays the deck's central themes
    — Air Temple's team-pump in a go-wide deck) and a bounded SHORTFALL nudge (favor the
    color the deck is scarcest on, from pip-demand vs current sources)."""
    import wishlist
    meta = load_card_meta()
    dmeta, cards = parse_deck_file(d["path"])
    mana_map = load_mana()
    carddata = load_card_data()

    deck_colors = _declared_colors(dmeta)
    if not deck_colors:
        for _q, n, _s, _c in cards:
            if n.lower() in BASICS:
                continue
            m = meta.get(n.lower())
            if m:
                deck_colors |= (m["colors"] & set("WUBRG"))

    # central themes (for the synergy nudge) + names already in the deck
    theme_w, deck_names = {}, set()
    for q, n, _s, _c in cards:
        nl = n.lower()
        deck_names.add(nl.split(" // ")[0])
        if nl in BASICS:
            continue
        m = meta.get(nl)
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    central = _central_themes(theme_w)
    central_w = {t: theme_w[t] for t in central}

    # current color sources (lands) + strict pip demand -> per-color scarcity (deficit)
    sources = {c: 0 for c in deck_colors}
    demand = {c: 0 for c in deck_colors}
    for q, n, _s, _c in cards:
        nl = n.lower()
        if nl in BASICS:
            col = BASIC_COLOR.get(nl)
            if col in sources:
                sources[col] += q
            continue
        cd = carddata.get(nl)
        if "Land" in _primary_type((cd["type"] if cd else "") or ""):
            m = meta.get(nl)
            for col in (m["colors"] if m else set()):
                if col in sources:
                    sources[col] += q
            continue
        entry = mana_map.get(nl)
        if entry and entry[0]:
            strict, _hy = parse_pips(entry[0])
            for col, cnt in strict.items():
                if col in demand:
                    demand[col] += cnt * q
    tot_d = sum(demand.values()) or 1
    tot_s = sum(sources.values()) or 1
    deficit = {c: max(0.0, demand[c] / tot_d - sources[c] / tot_s) for c in deck_colors}

    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        pool = list(csv.DictReader(fh))
    has_leg = bool(pool) and "Legalities" in pool[0]
    # Default to the deck's own `#: format:`, exactly as the card-facing `suggest` does
    # (--format overrides, --any-format disables). Without this line the land recommender
    # only filtered when someone passed --format explicitly, so a plain
    # `suggest --lands <id>` on a Standard deck offered Underground River and Duskmantle,
    # House of Shadow as craft targets — neither is Standard-legal. This is a
    # WILDCARD-SPEND recommender, so an unfiltered pick costs real resources, and it is
    # exactly the "recommending a craft without a legality check" failure CLAUDE.md warns
    # about. Found by USING the tool to build a deck, not by any test.
    fmt = "" if any_format else (fmt or dmeta.get("format") or "").strip().lower()
    apply_fmt = bool(fmt) and fmt in POOL_FORMATS and has_leg
    _, _, by_name_qty = load_collection()
    owned_of = lambda nl: owned_qty(by_name_qty, nl)

    picks = []
    for r in pool:
        name = (r.get("Card Name") or "").strip()
        nl = name.lower()
        if not name or nl.split(" // ")[0] in deck_names or nl in BASICS:
            continue
        if "land" not in (r.get("Type") or "").lower():
            continue
        if apply_fmt and fmt not in {x.strip() for x in (r.get("Legalities") or "").split(";")}:
            continue
        prod = card_colors(r.get("Color(s)"))
        txt = (r.get("Card Text") or "")
        for c in "WUBRG":
            if "{" + c + "}" in txt:
                prod.add(c)
        on_color = prod & deck_colors
        if not on_color:
            continue  # off-color / colorless-only: doesn't fix THIS deck's manabase
        h = owned_of(nl)
        if unowned and h > 0:
            continue
        if owned and h == 0:
            continue
        fix = wishlist._land_value(r, deck_colors)
        tags = [t.strip() for t in (r.get("Synergies") or "").split(";") if t.strip()]
        syn = _land_synergy_bonus(tags, central_w)
        short = _land_shortfall_bonus(on_color, deficit)
        tapped = ("enters tapped" in txt.lower()
                  or "enters the battlefield tapped" in txt.lower())
        picks.append({
            "name": name, "rarity": (r.get("Rarity") or "").strip(), "owned": h,
            "fix": fix, "syn": syn, "short": short, "score": round(fix + syn + short, 2),
            "produces": "".join(c for c in "WUBRG" if c in on_color),
            "tapped": tapped, "text": txt, "matches": sorted(set(tags) & central),
        })
    picks.sort(key=lambda p: (-p["score"], -min(p["owned"], 1), p["name"].lower()))
    if limit and limit > 0:
        picks = picks[:limit]
    return {"ok": True, "colors": deck_colors, "picks": picks, "fmt": fmt,
            "apply_fmt": apply_fmt, "has_leg": has_leg, "sources": sources, "deficit": deficit}


def cmd_suggest_lands(args, d):
    """Render suggest_lands (the manabase recommender)."""
    res = suggest_lands(d, unowned=args.unowned, owned=getattr(args, "owned", False),
                        limit=args.limit, fmt=getattr(args, "fmt", None),
                        any_format=getattr(args, "any_format", False))
    dc = res["colors"]
    print(f"Deck {d['id']}: {d['name'] or d['path']} — LAND suggestions (manabase)\n")
    print("Colors: " + ("/".join(sorted(dc)) or "Colorless") + "  ·  current sources: "
          + ", ".join(f"{c} {res['sources'].get(c, 0)}" for c in sorted(dc)))
    scarce = sorted(res["deficit"].items(), key=lambda kv: -kv[1])
    if scarce and scarce[0][1] > 0:
        print(f"Scarcest color (strict pip-demand vs sources): {scarce[0][0]} "
              "— lands producing it get the shortfall nudge.")
    if res["apply_fmt"]:
        print(f"Format: {res['fmt']}-legal only  (override with --format / --any-format)")
    if not res["picks"]:
        print("\nNo on-color lands to suggest (rebuild card-pool.csv with build_pool.py --all?).")
        return 0
    print(f"\n  {'Have':5} {'Land':30} {'Rarity':8} {'Prod':4} {'Fix':>4} {'Syn':>4} "
          f"{'Sh':>4} {'Score':>5}")
    print("-" * 78)
    for p in res["picks"]:
        have = f"×{p['owned']}" if p["owned"] else "craft"
        tap = " ·tapped" if p["tapped"] else ""
        print(f"  {have:5} {p['name'][:30]:30} {(p['rarity'] or '?')[:8]:8} "
              f"{p['produces']:4} {p['fix']:>4.1f} {p['syn']:>4.1f} {p['short']:>4.1f} "
              f"{p['score']:>5.1f}{tap}")
    if getattr(args, "full", False):
        import textwrap
        print("\n── Oracle text of the top picks (grade the ability, not just the fixing) ──")
        for p in res["picks"][:min(8, len(res["picks"]))]:
            print(f"\n• {p['name']}"
                  + (f"   synergy: {', '.join(p['matches'])}" if p["matches"] else ""))
            for para in (p["text"] or "(no oracle text)").split("\n"):
                for line in (textwrap.wrap(para, width=86) or [""]):
                    print(f"    {line}")
    print("\nScore = FIXING value (0–10, dominant: produces your colors, untapped premium) "
          "+ bounded SYNERGY (land ability hits a deck theme) + bounded SHORTFALL (produces "
          "the scarce color). Owned first — a 0-wildcard fixer usually beats a craft.")
    return 0


def suggest_mana(d, needs, unowned=False, owned=False, limit=20, fmt=None):
    """Recommend nonland MANA SOURCES (dorks / rocks / ramp) — the structural need theme-based
    suggest can't see (a fixer shares no synergy theme). Per-card rank = FIXING (produces the
    deck's / scarce colors) + RESTRICTION-fit (a restricted-mana dork matching the deck's
    dominant type) + a small power tiebreak. Whether the deck WANTS ramp at all is the deck-
    level `needs['accel']`, shown in the header — not a per-card term (it'd just scale the list).
    """
    dc, deficit, ts = needs["colors"], needs["deficit"], needs["type_share"]
    mana_map = load_mana()
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        pool = list(csv.DictReader(fh))
    has_leg = bool(pool) and "Legalities" in pool[0]
    apply_fmt = bool(fmt) and fmt in POOL_FORMATS and has_leg
    _, _, by_name_qty = load_collection()
    owned_of = lambda nl: owned_qty(by_name_qty, nl)
    picks = []
    for r in pool:
        name = (r.get("Card Name") or "").strip()
        nl = name.lower()
        if not name or nl.split(" // ")[0] in needs["names"] or nl in BASICS:
            continue
        tline = r.get("Type") or ""
        pt = _primary_type(tline)
        if pt in ("Land", "Instant", "Sorcery"):
            continue  # lands are --lands' job; instants/sorceries are one-shot rituals, not ramp
        txt = r.get("Card Text") or ""
        # a REPEATABLE mana source: an activated mana ability (":" before "add"), so an
        # ETB-treasure body or a vanilla creature that merely mentions mana doesn't qualify.
        if not (_produces_mana(txt) and re.search(r":[^.\n]{0,40}\badd\b", txt, re.I)):
            continue
        if not card_colors(r.get("Color(s)")).issubset(dc):
            continue  # off-color / uncastable for this deck
        if apply_fmt and fmt not in {x.strip() for x in (r.get("Legalities") or "").split(";")}:
            continue
        h = owned_of(nl)
        if (unowned and h > 0) or (owned and h == 0):
            continue
        # Ramp is about ACCELERATION, not fixing (a 2-color deck's fixing is nearly solved) —
        # so the dominant axis is CHEAPNESS × the deck's accel-want (a 1-drop dork ramps a
        # top-heavy deck; a 4-mana rainbow rock barely helps). Fixing enters only as the
        # bounded scarce-color bonus (reused from --lands), and restriction-fit + power tiebreak.
        prod = _produced_colors(txt, dc)
        mv = (mana_map.get(nl) or (None, None))[1]
        cheap = max(0.0, (5 - (mv if mv is not None else 3))) / 4.0   # 1-drop→1.0, 5-drop→0.0
        accel_c = round(_RAMP_ACCEL_CAP * needs["accel"] * min(1.0, cheap), 2)
        fixb = _land_shortfall_bonus(prod & dc, deficit)
        restr = _ramp_restriction_fit(txt, ts)
        power = _power_seed(r)
        score = round(accel_c + fixb + restr + max(0.0, min(1.0, 0.2 * (power - 4))), 2)
        picks.append({"name": name, "rarity": (r.get("Rarity") or "").strip(), "owned": h,
                      "fix": fixb, "accel": accel_c, "restr": restr, "power": round(power, 1),
                      "score": score, "mv": mv if mv is not None else "?",
                      "produces": "".join(c for c in "WUBRG" if c in prod) or "?",
                      "restricted": _RESTRICT_RE.search(txt) is not None, "text": txt})
    picks.sort(key=lambda p: (-p["score"], -min(p["owned"], 1), p["name"].lower()))
    return picks[:limit] if limit and limit > 0 else picks


def suggest_interaction(d, needs, unowned=False, owned=False, limit=20, fmt=None):
    """Recommend INTERACTION (removal / sweeper / counter) — including OFF-THEME cards that
    theme-suggest filters out. Per-card rank = impact role credit + a bounded SCALING boost for
    a board-dependent removal spell the deck's board supports (fight in an equipment deck,
    'damage = creatures you control' in a go-wide deck) + a small power tiebreak. The scaling is
    FLAGGED with the deck metric so the human confirms — it's never a silent boost."""
    dc = needs["colors"]
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        pool = list(csv.DictReader(fh))
    has_leg = bool(pool) and "Legalities" in pool[0]
    apply_fmt = bool(fmt) and fmt in POOL_FORMATS and has_leg
    _, _, by_name_qty = load_collection()
    owned_of = lambda nl: owned_qty(by_name_qty, nl)
    picks = []
    for r in pool:
        name = (r.get("Card Name") or "").strip()
        nl = name.lower()
        if not name or nl.split(" // ")[0] in needs["names"] or nl in BASICS:
            continue
        if "land" in (r.get("Type") or "").lower():
            continue
        txt = r.get("Card Text") or ""
        roles = set(classify_roles(txt))
        if not (roles & _INTERACTION_ROLES):
            continue  # not interaction
        if not card_colors(r.get("Color(s)")).issubset(dc):
            continue
        if apply_fmt and fmt not in {x.strip() for x in (r.get("Legalities") or "").split(";")}:
            continue
        h = owned_of(nl)
        if (unowned and h > 0) or (owned and h == 0):
            continue
        axis = _int_scaling(txt)
        boost = _int_scaling_boost(axis, _scaling_metric(axis, needs)) if axis else 0.0
        power = _power_seed(r)
        # Rank on card QUALITY (power, 0–10) + the board-scaling boost + a small flex credit
        # for answering more than one thing (modal / covers a noncreature permanent).
        flex = 0.5 if len(roles & _INTERACTION_ROLES) > 1 else 0.0
        score = round(power + boost + flex, 2)
        picks.append({"name": name, "rarity": (r.get("Rarity") or "").strip(), "owned": h,
                      "roles": sorted(roles & _INTERACTION_ROLES), "axis": axis, "boost": boost,
                      "power": round(power, 1), "score": score, "text": txt})
    picks.sort(key=lambda p: (-p["score"], -min(p["owned"], 1), p["name"].lower()))
    return picks[:limit] if limit and limit > 0 else picks


def cmd_suggest_ramp(args, d):
    needs = deck_needs(d)
    fmt = getattr(args, "fmt", None) or needs["format"]
    picks = suggest_mana(d, needs, unowned=args.unowned, owned=getattr(args, "owned", False),
                         limit=args.limit, fmt=fmt)
    accel = needs["accel"]
    band = "HIGH" if accel >= 0.5 else "moderate" if accel >= 0.2 else "LOW"
    print(f"Deck {d['id']}: {d['name'] or d['path']} — MANA-SOURCE suggestions (dorks/rocks)\n")
    print(f"Colors: {'/'.join(sorted(needs['colors'])) or 'Colorless'}  ·  avg MV {needs['avg_mv']}"
          f"  ·  acceleration want: {band} ({accel})")
    if band == "LOW":
        print("  (a lean curve — you may not want dorks at all; ranked on FIXING value.)")
    if not picks:
        print("\nNo on-color mana sources to suggest.")
        return 0
    print(f"\n  {'Have':5} {'Card':28} {'MV':>2} {'Prod':4} {'Acl':>4} {'Fix':>4} {'Rstr':>5} "
          f"{'Pw':>3} {'Score':>5}")
    print("-" * 74)
    for p in picks:
        have = f"×{p['owned']}" if p["owned"] else "craft"
        tag = " ·restricted" if p["restricted"] else ""
        print(f"  {have:5} {p['name'][:28]:28} {str(p['mv']):>2} {p['produces']:4} "
              f"{p['accel']:>4.1f} {p['fix']:>4.1f} {p['restr']:>5.1f} {p['power']:>3.0f} "
              f"{p['score']:>5.1f}{tag}")
    print("\nScore = ACCELERATION (cheapness × the deck's accel-want — a cheap dork ramps a "
          "top-heavy deck) + bounded FIXING (scarce color) + RESTRICTION-fit (a restricted dork "
          "matching your deck type; − if mismatched) + power tiebreak. Grade ETB value from text.")
    return 0


def cmd_suggest_interaction(args, d):
    needs = deck_needs(d)
    fmt = getattr(args, "fmt", None) or needs["format"]
    picks = suggest_interaction(d, needs, unowned=args.unowned, owned=getattr(args, "owned", False),
                                limit=args.limit, fmt=fmt)
    it, tgt = needs["interaction"], needs["int_target"]
    state = f"SHORT ({it} < {tgt})" if needs["int_short"] else f"adequate ({it})"
    print(f"Deck {d['id']}: {d['name'] or d['path']} — INTERACTION suggestions (incl. off-theme)\n")
    print(f"Colors: {'/'.join(sorted(needs['colors'])) or 'Colorless'}  ·  "
          f"current interaction: {state}")
    if not needs["int_short"]:
        print("  (already at target — showing anyway; a board-scaling pick may still upgrade.)")
    if not picks:
        print("\nNo on-color interaction to suggest.")
        return 0
    print(f"\n  {'Have':5} {'Card':28} {'Rarity':8} {'Role':16} {'Pw':>3} {'Score':>5}  Scaling")
    print("-" * 86)
    for p in picks:
        have = f"×{p['owned']}" if p["owned"] else "craft"
        role = "/".join(x.split()[0] for x in p["roles"])[:16]
        scale = ""
        if p["axis"]:
            metric = _scaling_metric(p["axis"], needs)
            scale = f"⚠ scales w/ {p['axis']} (deck {metric:.0%}, +{p['boost']:.1f})"
        print(f"  {have:5} {p['name'][:28]:28} {(p['rarity'] or '?')[:8]:8} {role:16} "
              f"{p['power']:>3.0f} {p['score']:>5.1f}  {scale}")
    print("\nScore = impact role credit + a bounded SCALING boost (a board-dependent removal "
          "spell your board supports) + power tiebreak. ⚠ scaling cards are FLAGGED with your "
          "deck's strength on that axis — grade them for THIS board from full text.")
    return 0


def cmd_suggest_needs(args, d):
    """Unified structural-needs view: fixing (lands + dorks), acceleration (dorks), interaction —
    the one-stop 'what does my deck LACK' report, composing the three needs-aware recommenders."""
    needs = deck_needs(d)
    fmt = getattr(args, "fmt", None) or needs["format"]
    print(f"Deck {d['id']}: {d['name'] or d['path']} — STRUCTURAL NEEDS\n")
    dc = needs["colors"]
    scarce = sorted(needs["deficit"].items(), key=lambda kv: -kv[1])
    scarce_c = scarce[0][0] if scarce and scarce[0][1] > 0 else None
    print(f"Colors {'/'.join(sorted(dc)) or 'Colorless'} · sources "
          + ", ".join(f"{c} {needs['sources'].get(c, 0)}" for c in sorted(dc))
          + (f" · scarcest {scarce_c}" if scarce_c else " · balanced"))
    accel = needs["accel"]
    aband = "HIGH" if accel >= 0.5 else "moderate" if accel >= 0.2 else "LOW"
    print(f"Acceleration want: {aband} (avg MV {needs['avg_mv']}) · "
          f"Interaction: {needs['interaction']}/{needs['int_target']}"
          + ("  ⚠ short" if needs["int_short"] else "  ok"))

    def _top(title, rows, fmt_row, n=4):
        print(f"\n── {title} ──")
        if not rows:
            print("  (nothing to suggest)")
            return
        for p in rows[:n]:
            print("  " + fmt_row(p))

    lands = suggest_lands(d, owned=True, limit=4, fmt=fmt)["picks"]
    _top("Fixing · owned lands", lands,
         lambda p: f"×{p['owned']} {p['name'][:34]:34} {p['produces']:4} score {p['score']:.1f}")
    dorks = suggest_mana(d, needs, owned=True, limit=4, fmt=fmt)
    _top("Fixing / acceleration · owned mana sources", dorks,
         lambda p: f"×{p['owned']} {p['name'][:34]:34} {p['produces']:4} score {p['score']:.1f}"
                   + (" ·restricted" if p["restricted"] else ""))
    inter = suggest_interaction(d, needs, owned=True, limit=4, fmt=fmt)
    _top("Interaction · owned" + ("  (deck is SHORT)" if needs["int_short"] else ""), inter,
         lambda p: f"×{p['owned']} {p['name'][:30]:30} {('/'.join(x.split()[0] for x in p['roles']))[:14]:14}"
                   + (f"  ⚠{p['axis']}" if p["axis"] else "") + f"  score {p['score']:.1f}")
    print("\n(owned/0-wildcard picks shown; add --unowned to any single mode for craft targets. "
          "These are STRUCTURAL fills the theme-based `suggest` can't see — grade from text.)")
    return 0


def cmd_suggest(args):
    """Recommend pool cards that fit a deck's color identity and synergy themes.

    Scores each candidate by how strongly its tags overlap the deck's themes
    (weighted by how central each theme is to the deck), filters to the deck's
    colors, and flags owned vs. craftable with wildcard rarity. Composes
    card-pool.csv + the synergy tags + tribes-style theme matching. Rendering only —
    the scoring lives in suggest_scored() so the dashboard shares it verbatim.
    With --lands, defers to the manabase recommender (cmd_suggest_lands) instead.
    """
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    if not os.path.exists(POOL_CSV):
        eprint("No card-pool.csv. Build it: python3 scripts/build_pool.py")
        return 1
    if getattr(args, "lands", False):
        return cmd_suggest_lands(args, d)
    if getattr(args, "ramp", False):
        return cmd_suggest_ramp(args, d)
    if getattr(args, "interaction", False):
        return cmd_suggest_interaction(args, d)
    if getattr(args, "needs", False):
        return cmd_suggest_needs(args, d)

    res = suggest_scored(d, unowned=args.unowned, owned=getattr(args, "owned", False),
                         limit=args.limit, fmt=getattr(args, "fmt", None),
                         any_format=getattr(args, "any_format", False))
    if not res["ok"]:
        if res["reason"] == "no-themes":
            print(f"Deck {d['id']} has no synergy tags to match against "
                  "(run tag_synergies.py). Nothing to suggest.")
            return 0
        eprint("No card-pool.csv. Build it: python3 scripts/build_pool.py")
        return 1

    deck_colors, fmt = res["colors"], res["fmt"]
    print(f"Deck {d['id']}: {d['name'] or d['path']} — suggestions from the pool\n")
    print(f"Colors: {'/'.join(sorted(deck_colors)) or 'Colorless'}  ·  "
          f"top themes: {', '.join(f'{t}({w})' for t, w in res['themes'])}")
    if res["apply_fmt"]:
        print(f"Format: {fmt}-legal only  (override with --format <fmt> / --any-format)")
    elif fmt and not res["has_leg"]:
        print(f"Format: '{fmt}' filter requested but card-pool.csv has no legality "
              "data — rebuild with build_pool.py. Showing all.")
    elif fmt and fmt not in POOL_FORMATS:
        print(f"Format: '{fmt}' not tracked — not filtering. "
              f"(known: {', '.join(sorted(POOL_FORMATS))})")
    stale = pool_staleness_days()
    if stale is not None and stale > 180:
        print(f"⚠ card-pool.csv was built {stale} days ago — Standard legality may be "
              "stale (sets rotate). Rebuild: build_pool.py --all (or /refresh).")
    if not res["picks"]:
        print("\nNo pool cards matched this deck's colors + themes.")
        return 0
    rotn = sum(1 for p in res["picks"] if p.get("rotates"))
    if rotn:
        print(f"({rotn} pick(s) marked ⚠rot — set >3yr old, may have rotated / rotates soon)")
    print(f"\n{'Have':>5}  {'Card':28}  {'Rarity':8}  {'Decks':>5}  Matches (deck themes)")
    print("-" * 82)
    craftby = {}
    for p in res["picks"]:
        h = p["owned"]
        have = f"×{h}" if h > 0 else "craft"
        rar = p["rarity"]
        if h == 0:
            craftby[rar] = craftby.get(rar, 0) + 1
        rotflag = " ⚠rot" if p.get("rotates") else ""
        print(f"{have:>5}  {p['name'][:28]:28}  {rar[:8]:8}  {p['decks']:>5}  "
              f"{', '.join(p['matches'][:5])}{rotflag}")
    ncraft = sum(craftby.values())
    print("-" * 82)
    print(f"{res['total']} suggestion(s) — {res['total'] - ncraft} owned, {ncraft} to craft"
          + (f" ({', '.join(f'{n} {r}' for r, n in sorted(craftby.items()))})"
             if ncraft else ""))
    print("Decks = how many of your OTHER decks the card is castable in + shares a "
          "SPECIFIC central theme with — generic overlap (etb/tokens/counters/…) and "
          "broad tribes don't count (higher = more value per wildcard).")
    if res["hi_reuse"]:
        print("High cross-deck reuse: "
              + ", ".join(f"{n} ({k})" for n, k in sorted(res["hi_reuse"], key=lambda x: -x[1])[:6]))

    # --full: phased ingestion for ADDS — print the full oracle text + keywords +
    # ⚠ flags of the picks, so a craft/owned add is graded from text (like `cuts`
    # does for the deck's own cards), never from the tag-match line above.
    if getattr(args, "full", False) and res["picks"]:
        import textwrap
        carddata, mana, kw = load_card_data(), load_mana(), load_keywords()
        print(f"\n── Full text of the {len(res['picks'])} pick(s) — grade adds from THIS ──")
        for p in res["picks"]:
            nl = p["name"].lower()
            cd = carddata.get(nl)
            tline = (cd["type"] if cd else "") or "?"
            text = (cd["text"] if cd else "") or ""
            cost, mv = (mana.get(nl) or (None, None))
            have = f"×{p['owned']}" if p["owned"] else "craft"
            print(f"\n• {p['name']}   [{tline}]"
                  + (f"  ·  MV {mv}" if mv is not None else "")
                  + f"  ·  {p['rarity'] or '?'} · {have} · fits {p['decks']} other deck(s)")
            card_kw = kw.get(nl) or []
            if card_kw:
                print(f"    ⌘ keywords: {', '.join(k.title() for k in card_kw)}")
            flags = read_flags(text, cost, card_kw)
            if flags:
                print(f"    ⚠ {' · '.join(flags)}")
            for para in (text or "(no oracle text on file)").split("\n"):
                for line in (textwrap.wrap(para, width=90) or [""]):
                    print(f"    {line}")
    return 0


# --- consistency / manabase probability model (hypergeometric) ------------- #
# Pure, deck-agnostic helpers behind `deck.py consistency`. They answer the two
# questions the diagnosis-only `mana` command couldn't: "how often do I actually
# cast this on curve" (#1, a Karsten-style cast-probability model) and "how often
# is my opening hand keepable / do I hit my land drops" (#2, a hypergeometric
# land model). Kept separate from any deck I/O so they're unit-testable.

def hypergeom_at_least(N, K, n, k):
    """P(drawing AT LEAST k of the K 'successes' when drawing n from a deck of N).
    N deck size, K successes in deck, n cards drawn, k successes wanted. Exact —
    sums the hypergeometric PMF over j∈[k, min(K,n)]."""
    if k <= 0:
        return 1.0
    if N <= 0 or K < k or n < k:
        return 0.0
    n = min(n, N)
    total = math.comb(N, n)
    if total == 0:
        return 0.0
    s = 0
    for j in range(k, min(K, n) + 1):
        s += math.comb(K, j) * math.comb(N - K, n - j)
    return s / total


def cards_seen(turn, on_play=True):
    """Cards seen by the START of your `turn` (after that turn's draw). Opening 7,
    +1 per turn drawn: on the play you skip turn 1's draw (7+turn-1), on the draw
    you don't (7+turn)."""
    return 7 + (turn - 1) + (0 if on_play else 1)


def cast_probability(N, sources, turn, pips, on_play=True):
    """P(having enough colored sources to pay `pips` by `turn`). `pips` is a strict
    {color: count} demand; `sources` is {color: land count producing it}. Per-color
    hypergeometric, multiplied across colors (Karsten's independence approximation).
    Hybrid pips are excluded by the caller — they're strictly easier, so the strict
    demand is the binding constraint."""
    seen = cards_seen(turn, on_play)
    p = 1.0
    for col, cnt in pips.items():
        if cnt <= 0:
            continue
        p *= hypergeom_at_least(N, sources.get(col, 0), seen, cnt)
    return p


def min_sources_for(N, turn, pip_count, target=0.90, on_play=True):
    """Fewest sources of ONE color to hit `target` P of having `pip_count` of them by
    `turn` — the Karsten "how many sources do I need" number. Returns N if even a full
    deck of them can't (impossible target)."""
    seen = cards_seen(turn, on_play)
    for src in range(0, N + 1):
        if hypergeom_at_least(N, src, seen, pip_count) >= target:
            return src
    return N


def opening_land_stats(N, lands, on_play=True):
    """Opening-hand + land-drop consistency for a deck of N with `lands` lands:
    keepable (2–5 lands in the opening 7), screw (0–1), flood (6–7), and P(≥n lands
    by turn n) for n=2,3,4 (land-drop consistency). All exact hypergeometric."""
    seven = math.comb(N, 7) if N >= 7 else 0

    def p7(k):  # P(exactly k lands in the opening 7)
        if not seven or lands < k or N - lands < 7 - k:
            return 0.0
        return math.comb(lands, k) * math.comb(N - lands, 7 - k) / seven

    keepable = sum(p7(k) for k in range(2, 6))
    screw = sum(p7(k) for k in range(0, 2))
    flood = sum(p7(k) for k in range(6, 8))
    return {"keepable": keepable, "screw": screw, "flood": flood,
            "hit2": hypergeom_at_least(N, lands, cards_seen(2, on_play), 2),
            "hit3": hypergeom_at_least(N, lands, cards_seen(3, on_play), 3),
            "hit4": hypergeom_at_least(N, lands, cards_seen(4, on_play), 4)}


def cmd_mana(args):
    """Hybrid-aware color requirements: which colors a deck STRICTLY needs."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}.")
        return 1
    by_key, by_name, _ = load_collection()
    meta, cards = parse_deck_file(d["path"])
    mana = load_mana()
    if not mana:
        eprint("No card-mana.csv found. Build it: python3 scripts/build_mana.py")
        return 1
    nonland = [n for q, n, s, c in cards if n.lower() not in BASICS]
    fetch_missing_mana(sorted(set(nonland)), mana)

    strict_pips = {c: 0 for c in "WUBRG"}
    cards_need = {c: 0 for c in "WUBRG"}
    hybrid_pips = {}
    hybrid_only = unknown = 0
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        row = by_key.get((n.lower(), s.lower(), c.lower())) or by_name.get(n.lower())
        if row and "Land" in _primary_type((row.get("Type") or "")):
            continue
        entry = mana.get(n.lower())
        if entry is None:
            unknown += q
            continue
        strict, hybrid = parse_pips(entry[0])
        if not entry[0]:  # no mana cost (nonbasic land not in library, or 0-cost)
            continue
        for col, cnt in strict.items():
            strict_pips[col] += cnt * q
        for col in strict:
            cards_need[col] += q
        for h in hybrid:
            hybrid_pips[h] = hybrid_pips.get(h, 0) + q
        if hybrid and not strict:
            hybrid_only += q

    print(f"Deck {d['id']}: {d['name'] or d['path']} — mana requirements (hybrid-aware)\n")
    print("Strict color requirements (must be paid with that color):")
    for c in "WUBRG":
        if cards_need[c]:
            note = _commitment(cards_need[c])
            print(f"  {c}  {strict_pips[c]:3} pips across {cards_need[c]:2} card(s)   {note}")
    if hybrid_pips:
        print("\nHybrid pips (payable with EITHER color — don't demand their own sources):")
        for h, n in sorted(hybrid_pips.items(), key=lambda kv: -kv[1]):
            print(f"  {'/'.join(sorted(h))}  {n} pip(s)")
    if hybrid_only:
        print(f"\n{hybrid_only} card(s) are hybrid-only — castable with any of their colors.")
    if unknown:
        print(f"\n{unknown} card(s) had no cost data (run build_mana.py to refresh).")

    # Color-source adequacy: count how many lands can PRODUCE each color, then flag
    # cards whose strict colored-pip demand looks thin against those sources — the
    # "wants UU but this is a U-splash deck" check the identity lint can't make.
    # Nonbasic lands are approximated by their color identity; mana dorks aren't
    # counted, so read it as a review signal, not a hard failure.
    carddata = load_card_data()
    sources = {c: 0 for c in "WUBRG"}
    nlands = 0

    def _is_land(nl, s, c):
        row = by_key.get((nl, s.lower(), c.lower())) or by_name.get(nl)
        cd = carddata.get(nl)
        tline = (row.get("Type") if row else "") or (cd["type"] if cd else "")
        colid = (row.get("Color(s)") if row else "") or (cd.get("colors") if cd else "")
        return "Land" in _primary_type(tline), colid

    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS:
            col = BASIC_COLOR.get(nl)
            if col:
                sources[col] += q
            nlands += q
            continue
        land, colid = _is_land(nl, s, c)
        if land:
            nlands += q
            for col in card_colors(colid):
                sources[col] += q
    active = [c for c in "WUBRG" if sources[c] or cards_need[c]]
    if active:
        print("\nColor sources (lands producing each color):")
        print("  " + "   ".join(f"{c} {sources[c]}" for c in active) + f"   ({nlands} lands)")
        thin, seen_t = [], set()
        for q, n, s, c in cards:
            nl = n.lower()
            if nl in BASICS or n in seen_t:
                continue
            land, _ = _is_land(nl, s, c)
            entry = mana.get(nl)
            if land or not (entry and entry[0]):
                continue
            strict, _hy = parse_pips(entry[0])
            for col, cnt in sorted(strict.items(), key=lambda kv: -kv[1]):
                if cnt >= 2 and sources[col] < 9:
                    thin.append((n, f"wants {col}{col} but only {sources[col]} {col} sources"))
                    seen_t.add(n)
                    break
                if cnt == 1 and sources[col] < 4:
                    thin.append((n, f"wants {col} but only {sources[col]} {col} source(s)"))
                    seen_t.add(n)
                    break
        if thin:
            print("△ Pip-intensive vs your sources (heuristic review — not a hard fail):")
            for n, why in thin:
                print(f"    {n} — {why}")

    # Castability lint: compare each card's real color needs against the deck's
    # declared colors (the `#: colors:` header). Only meaningful when declared.
    declared = _declared_colors(meta)
    if declared:
        uncastable, off_ident, _, intended = _castability(
            cards, declared, mana, load_card_data(), _uncastable_ok(meta))
        cols = "".join(sorted(declared))
        if intended:
            print(f"\n◆ Intentionally uncastable (`#: uncastable-ok:`) — reanimation "
                  "targets you never cast from hand:")
            for n, why in intended:
                print(f"    {n} — {why}")
        if uncastable:
            print(f"\n✗ Uncastable off the deck's {cols} colors "
                  "(a pip needs a color the deck can't produce):")
            for n, why in uncastable:
                print(f"    {n} — {why}")
        if off_ident:
            print(f"\n△ Castable, but color identity strays outside {cols} "
                  "(off-color ability, or a hybrid you'd pay on-color):")
            for n, why in off_ident:
                print(f"    {n} — {why}")
        if not uncastable and not off_ident:
            print(f"\nCastability: every nonland card fits the declared {cols} colors. ✓")
    return 0


def _commitment(n):
    if n <= 3:
        return "<- light splash"
    if n <= 8:
        return "<- secondary color"
    return "<- primary color"


def _deck_source_counts(cards, by_key, by_name, carddata):
    """(sources{WUBRG:count}, nlands, total) for a cards list — the manabase side of
    the consistency model. Basics by name, nonbasic lands by color identity (mana
    dorks aren't counted as sources; they're not lands). Shared by `mana` /
    `consistency` so the two can't disagree on what a 'source' is."""
    sources = {c: 0 for c in "WUBRG"}
    nlands = total = 0
    for q, n, s, c in cards:
        total += q
        nl = n.lower()
        if nl in BASICS:
            col = BASIC_COLOR.get(nl)
            if col:
                sources[col] += q
            nlands += q
            continue
        row = by_key.get((nl, s.lower(), c.lower())) or by_name.get(nl)
        cd = carddata.get(nl)
        tline = (row.get("Type") if row else "") or (cd["type"] if cd else "")
        if "Land" in _primary_type(tline):
            nlands += q
            colid = (row.get("Color(s)") if row else "") or (cd.get("colors") if cd else "")
            for col in card_colors(colid):
                sources[col] += q
    return sources, nlands, total


def cmd_consistency(args):
    """Manabase + opening-hand CONSISTENCY (#1/#2): the probability layer `mana` lacks.
    Given the deck's land count and per-color sources, model P(keepable opening hand),
    screw/flood, land-drop consistency, and — per card — P(casting on curve) with a
    Karsten-style source recommendation for the ones that come up short. Diagnosis with
    numbers, not vibes: `mana` says 'thin', this says '62% on turn 3, want +2 sources'."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    by_key, by_name, _ = load_collection()
    meta, cards = parse_deck_file(d["path"])
    mana = load_mana()
    if not mana:
        eprint("No card-mana.csv found. Build it: python3 scripts/build_mana.py")
        return 1
    carddata = load_card_data()
    nonland = [n for q, n, s, c in cards if n.lower() not in BASICS]
    fetch_missing_mana(sorted(set(nonland)), mana)

    sources, nlands, total = _deck_source_counts(cards, by_key, by_name, carddata)
    on_play = not getattr(args, "on_draw", False)
    target = getattr(args, "target", None) or 0.90
    N = total or 60
    coin = "on the play" if on_play else "on the draw"

    print(f"Deck {d['id']}: {d['name'] or d['path']} — consistency ({N}-card deck, {coin})\n")

    # #2 — opening hand + land drops.
    ls = opening_land_stats(N, nlands, on_play)
    print(f"Lands: {nlands}/{N}  ({100*nlands/N:.0f}% of the deck)")
    print("Opening hand (7 cards):")
    print(f"  keepable (2–5 lands) : {100*ls['keepable']:5.1f}%")
    print(f"  mana screw (0–1)     : {100*ls['screw']:5.1f}%     "
          f"flood (6–7): {100*ls['flood']:4.1f}%")
    print("Land-drop consistency (P of ≥N lands by turn N):")
    print(f"  turn 2: {100*ls['hit2']:5.1f}%   turn 3: {100*ls['hit3']:5.1f}%   "
          f"turn 4: {100*ls['hit4']:5.1f}%")
    # A gentle land-count read — the classic 17-source floor is deck-dependent, so flag
    # only clear extremes rather than prescribe a number.
    if ls["keepable"] < 0.85:
        # Both directions were reachable, and on a low-curve list BOTH trip. Deck 52 at 24
        # lands read "consider FEWER"; the same list at 23 read "consider MORE", at a WORSE
        # keepable (82.5%) with three cards falling under 90% on curve. An advisory that
        # reverses and can be satisfied by nothing is worse than silence, so check the
        # neighbour before prescribing: if moving one land the suggested way makes keepable
        # worse too, say the threshold is unreachable for this shape and point at the
        # measurement that CAN be optimised.
        want = "more" if nlands < N * 0.40 else "fewer"
        step = 1 if want == "more" else -1
        alt = _keepable_at(nlands + step, N)
        if alt is not None and alt <= ls["keepable"]:
            print(f"  △ keepable {100*ls['keepable']:.0f}% is low, and moving to "
                  f"{nlands + step} lands does not improve it ({100*alt:.0f}%) — this curve "
                  "cannot clear the threshold at any land count. Optimise on the "
                  "cast-on-curve table below instead.")
        else:
            print(f"  △ keepable {100*ls['keepable']:.0f}% is low — consider {want} lands "
                  f"(most 60-card decks run 23–26).")

    # Color sources.
    active = [c for c in "WUBRG" if sources[c]]
    # A "splash" color has so few sources that a card demanding it on curve is
    # effectively a late-game card, not an on-curve one — so the per-card
    # recommendation below reframes as "cast later or cut" instead of printing an
    # impractical land count (a {B}{R} 2-drop off 1 red source wants ~15 R sources).
    SPLASH_MAX = 3
    splash = [c for c in active if sources[c] <= SPLASH_MAX]
    if active:
        print("\nColor sources (lands producing each color):")
        print("  " + "   ".join(f"{c} {sources[c]}" for c in active))
        if splash:
            print("  splash (≤%d sources): " % SPLASH_MAX
                  + ", ".join(f"{c} ({sources[c]})" for c in splash)
                  + " — a card needing one of these on curve reads low below; treat it as a "
                    "late-game splash (cast when you've drawn the source), not a curve play.")

    # #1 — per-card cast probability on curve. Cast turn = the card's MV (min 1),
    # capped so a 7-drop isn't judged as if cast on turn 7 verbatim (you've usually
    # stabilized your colors by ~turn 5). Strict pips only; hybrids are easier and
    # excluded (they don't demand their own sources — same rule `mana` uses).
    CAST_CAP = 5
    rows = []
    seen = set()
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS or nl in seen:
            continue
        row = by_key.get((nl, s.lower(), c.lower())) or by_name.get(nl)
        if row and "Land" in _primary_type((row.get("Type") or "")):
            continue
        entry = mana.get(nl)
        if not entry or not entry[0]:
            continue
        strict, _hy = parse_pips(entry[0])
        if not strict:
            continue
        seen.add(nl)
        mv = entry[1] if entry[1] is not None else sum(strict.values())
        turn = max(1, min(int(mv) if mv else 1, CAST_CAP))
        p = cast_probability(N, sources, turn, strict, on_play)
        # The tightest single-color demand drives the fix recommendation.
        worst_col = max(strict, key=lambda col: (strict[col], -sources.get(col, 0)))
        need = min_sources_for(N, turn, strict[worst_col], target, on_play)
        rows.append((p, n, turn, strict, worst_col, need))

    rows.sort(key=lambda r: r[0])
    below = [r for r in rows if r[0] < target]
    print(f"\nCast-on-curve probability (turn = mana value, capped at {CAST_CAP}; "
          f"target {100*target:.0f}%):")
    if not rows:
        print("  (no colored-pip cards with cost data)")
    else:
        show = below if below else rows[:5]
        if not below:
            print(f"  ✓ every colored card casts on curve at ≥{100*target:.0f}% — "
                  "manabase supports the deck. Lowest 5:")
        for p, n, turn, strict, worst_col, need in show:
            pipstr = "".join(f"{{{col}}}" * cnt for col, cnt in sorted(strict.items()))
            have_col = sources.get(worst_col, 0)
            flag = ""
            if p < target and need > have_col:
                if have_col <= SPLASH_MAX:
                    # Genuine splash: too few sources to ever be on-curve at this turn.
                    # Reframe as cast-late/cut rather than print an absurd land count
                    # (a {B}{R} 2-drop off 1 red source "wanting" 15 R sources).
                    flag = (f"   → {worst_col} is a {have_col}-source splash — cast it late "
                            f"(once you've drawn a source) or cut it; don't chase "
                            f"{100*target:.0f}% on curve")
                elif need > nlands:
                    # A main color, but a color-hungry EARLY cost (e.g. {B}{B} on T2) that no
                    # realistic land base guarantees on time — say so instead of "+N sources".
                    flag = (f"   → color-hungry: {100*target:.0f}% at T{turn} would need {need} "
                            f"{worst_col} sources (> the deck's {nlands} lands) — expect it a "
                            f"turn or two later than T{turn}")
                else:
                    flag = (f"   → want {need} {worst_col} sources "
                            f"(have {have_col}, +{need - have_col})")
            print(f"  {100*p:5.1f}%  T{turn}  {pipstr:10} {n[:30]:30}{flag}")
        if below:
            print(f"\n  {len(below)} card(s) below {100*target:.0f}% on curve — the → note is the "
                  f"Karsten source count to reach target, a splash flag for a thin (≤{SPLASH_MAX}-source) "
                  "color (cast late or cut), or a color-hungry flag for an early double pip.")
    print("\nModel: hypergeometric (exact); per-color independence for multi-color costs "
          "(a mild over-estimate), hybrids excluded as non-binding. A planning aid, not a "
          "guarantee — mulligans, scry, and card draw all shift the real numbers.")
    return 0


# --- flex / suggested swaps ------------------------------------------------- #
def _parse_flex_line(s):
    """Parse one stripped line into a flex entry dict, or None if it isn't a
    (non-empty) `#~` line.  Format:  #~ -Out card | +In card | reason"""
    if not s.startswith("#~"):
        return None
    e = {"out": "", "in": "", "note": ""}
    for col in (c.strip() for c in s[2:].split("|")):
        if col.startswith("-"):
            e["out"] = col[1:].strip()
        elif col.startswith("+"):
            e["in"] = col[1:].strip()
        elif col:
            e["note"] = (e["note"] + "  " + col).strip()
    return e if (e["out"] or e["in"] or e["note"]) else None


def parse_flex(path):
    """Return the deck's flex suggestions from `#~` lines.

    A flex line is a comment (so it never counts toward the 60 or reaches Arena
    import), machine-readable as:  #~ -Out card | +In card | reason
    Any of the three fields may be omitted; a lone free-text field is a note.
    """
    entries = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            e = _parse_flex_line(raw.strip())
            if e:
                entries.append(e)
    return entries


def flex_staleness(path):
    """Flex lines whose `-Out` card is NOT in the deck any more → [(out, in, why)].

    A `#~` line rots silently. `swap --apply` retires only the lines invalidated by
    the swap it is PERFORMING, and `tier --audit-rationale` reads `#: tier:` /
    `#: archetype:` prose, never the flex block — so a line can sit for rounds
    proposing a cut that already happened. Found in practice on deck 42a, where an
    Azula line still named Prideful Parent two swaps after it left, and again where an
    interaction fix pointed at a card three swaps stale.

    A line with no `-Out` (a pure note, or an add-only suggestion) is never stale —
    there is nothing to check it against.
    """
    _, cards = parse_deck_file(path)
    have = {n for _q, n, _s, _c in cards}
    have |= {n.split(" // ")[0] for n in list(have)}
    out = []
    for e in parse_flex(path):
        cut = (e.get("out") or "").strip()
        if not cut:
            continue
        if cut not in have and cut.split(" // ")[0] not in have:
            out.append((cut, (e.get("in") or "").strip(),
                        "the -Out card is no longer in the deck"))
    return out


def cmd_flex(args):
    """Show a deck's flex suggestions, enriching the +In card with cost / owned /
    rarity so you can see what each swap would take."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    entries = parse_flex(d["path"])
    print(f"Deck {d['id']}: {d['name'] or d['id']} — flex / suggested swaps")
    if not entries:
        print("  (none yet — add '#~ -Out card | +In card | reason' lines to the deck file.)")
        return 0
    mana = load_mana()
    rar = load_rarities()
    _, _, qty = load_collection()
    print("-" * 62)
    for e in entries:
        left = f"− {e['out']}" if e["out"] else ""
        right = ""
        if e["in"]:
            m = mana.get(e["in"].lower())
            cost = m[0] if (m and m[0]) else ""
            have, _ = owned(qty, e["in"])
            r = rar.get(e["in"].lower(), "")
            meta = " ".join(x for x in [cost, r, (f"×{have}" if have > 0 else "craft")] if x)
            right = f"+ {e['in']}" + (f"  ({meta})" if meta else "")
        if left and right:
            print(f"  {left}   →   {right}")
        elif left or right:
            print(f"  {left or right}")
        if e["note"]:
            print(f"      {e['note']}")
    stale = flex_staleness(d["path"])
    if stale:
        print("\n  \u26a0 STALE flex line(s) — the card they propose cutting is already gone:")
        for cut, add, _why in stale:
            print(f"      \u2212{cut}" + (f"  \u2192  +{add}" if add else "")
                  + "   (retarget or retire the line)")
    return 0


# --- swap preview / apply (and flex promotion) ------------------------------ #
def _printing_of(name):
    """Best-known `(display_name, set, collector#)` for a card name: an owned library
    printing first (so the added line matches something you have), else any known
    printing. `(name, '', '')` if unknown — a bare '1 Name' line still parses/checks.

    MATCHES A DFC BY ITS FRONT FACE TOO, and returns the CANONICAL display name. The
    CSVs key a two-faced card under its full `Front // Back` name, so an exact-only
    lookup for the front name found nothing and `swap --apply` wrote a bare `1 Runescale
    Stormbrood` with no printing. INV-04 passed and `legal` reported clean, because a
    bare line parses — but the line is not a valid Arena import, so the failure surfaced
    only when a human tried to paste the deck. Returning the display name as well is what
    stops the file recording the front-face shorthand instead of the real card name."""
    nl = name.strip().lower()
    best = (name.strip(), "", "")
    for path, owned_pref in ((DEFAULT_CSV, True), (POOL_CSV, False)):
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                disp = (r.get("Card Name") or "").strip()
                dl = disp.lower()
                if dl != nl and dl.split(" // ")[0] != nl:
                    continue
                setc = (r.get("Set Code") or "").strip()
                cn = (r.get("Collector #") or "").strip()
                if not setc:
                    continue
                if owned_pref:
                    try:
                        q = int(r.get("Quantity Owned") or 0)
                    except ValueError:
                        q = 0
                    if q > 0:
                        return (disp, setc, cn)   # an owned printing wins outright
                if not best[1]:
                    best = (disp, setc, cn)
    return best


def _card_line_name(line):
    """If a raw line is a card line, return its parsed name; else None. Comment
    lines (`#`, `#:`, `#~`) split to empty and return None."""
    body = line.split("#", 1)[0].strip()
    if not body:
        return None
    m = LINE_RE.match(body)
    return m.group(2).strip() if m else None


def _deck_summary(cards, carddata, mana):
    """Small before/after fingerprint for a cards list: totals, creature count,
    average nonland MV, and color identity (excluding basics/lands)."""
    total = crea = mv_sum = mv_n = 0
    colors = set()
    for q, n, s, c in cards:
        total += q
        nl = n.lower()
        if nl in BASICS:
            continue
        cd = carddata.get(nl)
        tline = (cd["type"] if cd else "") or ""
        if "Land" in _primary_type(tline):
            continue
        if "creature" in tline.lower():
            crea += q
        col = (cd["colors"] if cd else "") or ""
        if col.lower() != "colorless":
            colors |= {ch for ch in col.upper() if ch in "WUBRG"}
        entry = mana.get(nl)
        if entry and entry[1] is not None:
            mv_sum += entry[1] * q
            mv_n += q
    return {"total": total, "creatures": crea,
            "avg_mv": (mv_sum / mv_n if mv_n else 0.0), "colors": colors}


def _cards_after_swap(cards, cut, add, add_printing):
    """Return the cards list with one copy of `cut` replaced by `add`, or None
    if `cut` isn't present. If `add` is already in the deck, its existing line is
    bumped by one rather than adding a second line for the same card."""
    out, removed = [], False
    for (q, n, s, c) in cards:
        if not removed and n.lower() == cut.strip().lower():
            if q > 1:
                out.append((q - 1, n, s, c))
            removed = True
            continue
        out.append((q, n, s, c))
    if not removed:
        return None
    add_nl = add.strip().lower()
    for i, (q, n, s, c) in enumerate(out):
        if n.lower() == add_nl:
            out[i] = (q + 1, n, s, c)
            break
    else:
        out.append((1, add.strip(), add_printing[0], add_printing[1]))
    return out


# Section comments a swap can INHERIT and thereby falsify. The add takes the cut's line
# slot, so it lands under whatever `# ...` header preceded the cut — which is how
# Broodguard Elite (a counter battery) ended up filed under `# Card advantage`, the
# section Kiora had occupied. Harmless to the tooling, but the file then lies to the
# next reader, and these files are read far more often than they're parsed.
#
# Only sections whose meaning is UNAMBIGUOUS are checked. "# Counter DOUBLERS" means
# +1/+1 counters, not counterspells, and "# Threats" / "# Creatures" / "# Payoff" are
# too broad to contradict — a false warning on every swap would train the reader to
# ignore the real ones.
_SECTION_EXPECTATIONS = [
    (re.compile(r"card advantage|card draw", re.I), {"Card advantage"}),
    (re.compile(r"\bremoval\b|\binteraction\b|counterspell", re.I),
     {"Removal (spot)", "Sweeper", "Counter"}),
    (re.compile(r"\bramp\b|\bfixing\b|\bdorks?\b", re.I), {"Ramp / fixing"}),
]


def section_mismatch(lines, idx, add_name, carddata):
    """A warning string when the card now sitting at `lines[idx]` doesn't do what its
    enclosing `# section` comment claims, else None. Advisory only — it never edits the
    file, and it stays silent for ambiguous or absent section headers."""
    header = None
    for j in range(idx - 1, -1, -1):
        ln = lines[j].strip()
        if _card_line_name(lines[j]):
            continue                      # another card in the same section
        if ln.startswith("#:") or ln.startswith("#~") or not ln:
            continue                      # metadata / flex / blank
        if ln.startswith("#"):
            header = ln.lstrip("# ").strip()
            break
    if not header:
        return None
    cd = carddata.get((add_name or "").strip().lower())
    if not cd:
        return None
    roles = classify_roles(cd.get("text") or "")
    for rx, expected in _SECTION_EXPECTATIONS:
        if not rx.search(header):
            continue
        if roles & expected:
            return None
        if roles:
            # High confidence: we know what the card does, and it isn't this.
            return (f"{add_name} now sits under `# {header}` (inherited from the cut "
                    f"card's slot) but classifies as {', '.join(sorted(roles))} — move "
                    f"the line or retitle the section so the file doesn't mislead.")
        # Low confidence: the classifier found NO role. This session established that
        # "no role" often means a lexicon gap rather than a weak card, so this is
        # phrased as a prompt to look, not as an assertion that the card is misfiled.
        return (f"{add_name} now sits under `# {header}` (inherited from the cut card's "
                f"slot); nothing in its text matched a functional role, so verify the "
                f"section still describes it.")
    return None


def _swap_edit_lines(lines, cut, add, add_printing, drop_flex=None):
    """Apply the swap to raw file lines: -1 copy of `cut` (removed if it was a
    singleton, else decremented) with the `add` line taking its slot; optionally
    drop the flex line matching `drop_flex` (an entry dict). Raises ValueError if
    `cut` isn't a card line."""
    out = list(lines)
    ci = next((i for i, ln in enumerate(out)
               if (_card_line_name(ln) or "").lower() == cut.strip().lower()), None)
    if ci is None:
        raise ValueError(f"{cut!r} is not a card line in this deck.")
    m = LINE_RE.match(out[ci].split("#", 1)[0].strip())
    qty = int(m.group(1))
    setc, cn = add_printing
    add_line = f"1 {add.strip()}"
    if setc:
        add_line += f" ({setc})" + (f" {cn}" if cn else "")

    # If `add` is already a line in the deck, bump that line by one instead of
    # writing a second line for the same card (which would split its count).
    ai = next((i for i, ln in enumerate(out)
               if (_card_line_name(ln) or "").lower() == add.strip().lower()), None)
    if ai is not None:
        am = LINE_RE.match(out[ai].split("#", 1)[0].strip())
        a_indent = out[ai][:len(out[ai]) - len(out[ai].lstrip())]
        a_rebuilt = f"{a_indent}{int(am.group(1)) + 1} {am.group(2).strip()}"
        if am.group(3):
            a_rebuilt += f" ({am.group(3).strip()})" + (f" {am.group(4).strip()}" if am.group(4) else "")
        out[ai] = a_rebuilt
        if qty > 1:
            indent = out[ci][:len(out[ci]) - len(out[ci].lstrip())]
            rebuilt = f"{indent}{qty - 1} {m.group(2).strip()}"
            if m.group(3):
                rebuilt += f" ({m.group(3).strip()})" + (f" {m.group(4).strip()}" if m.group(4) else "")
            out[ci] = rebuilt
        else:
            del out[ci]
    elif qty > 1:
        indent = out[ci][:len(out[ci]) - len(out[ci].lstrip())]
        rebuilt = f"{indent}{qty - 1} {m.group(2).strip()}"
        if m.group(3):
            rebuilt += f" ({m.group(3).strip()})" + (f" {m.group(4).strip()}" if m.group(4) else "")
        out[ci] = rebuilt
        out.insert(ci + 1, add_line)
    else:
        out[ci] = add_line
    if drop_flex is not None:
        for j, ln in enumerate(out):
            e = _parse_flex_line(ln.strip())
            if e and e["out"].lower() == drop_flex["out"].lower() \
                    and e["in"].lower() == drop_flex["in"].lower():
                del out[j]
                break

    # Auto-retire flex lines made stale by THIS swap: a `#~ -Out | +In` proposal
    # is stale once we've maindecked its +In card, or cut its -Out card (and it's
    # no longer in the deck). Replace the first such line with an `applied` note
    # and drop the rest. Only touches `#~` comment lines, never card lines — so it
    # can't affect the copy count or INV-04. (Past sessions hand-cleaned these.)
    add_l, cut_l = add.strip().lower(), cut.strip().lower()
    maindeck = {(_card_line_name(ln) or "").lower() for ln in out if _card_line_name(ln)}
    cut_gone = cut_l not in maindeck
    cleaned, noted = [], False
    for ln in out:
        e = _parse_flex_line(ln.strip())
        if e and e["out"] and e["in"] and (
                e["in"].lower() == add_l or (e["out"].lower() == cut_l and cut_gone)):
            if not noted:
                indent = ln[:len(ln) - len(ln.lstrip())]
                cleaned.append(f"{indent}#~ note: applied — {add.strip()} in for {cut.strip()}.")
                noted = True
            continue
        cleaned.append(ln)
    return cleaned


def _safe_write_lines(path, lines, expected_total):
    """temp write -> INV-04 parse-check (parses cleanly AND total copies ==
    expected) -> timestamped .bak -> atomic replace. Returns the .bak path.

    The .bak name comes from the shared `lib.backup_path` (microsecond stamp +
    collision counter), like every other backup in the toolkit. A local
    second-precision name meant two writes in the same second — e.g. a skill applying
    a set of swaps in sequence — silently overwrote the pre-edit snapshot (audit F-03,
    the F22 fix that never reached deck.py)."""
    target = os.path.abspath(path)
    text = "\n".join(lines).rstrip("\n") + "\n"
    fd, tmp = tempfile.mkstemp(suffix=".txt", dir=os.path.dirname(target))
    os.close(fd)
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
        _, parsed = parse_deck_file(tmp)
        got = sum(q for q, *_ in parsed)
        if got != expected_total:
            raise ValueError(f"post-write copy count {got} != expected "
                             f"{expected_total}; not saved.")
        bak = backup_path(target)
        shutil.copy2(target, bak)
        os.replace(tmp, target)
        tmp = None
        return bak
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


RECS_CSV = os.path.join(REPO_ROOT, "recommendations.csv")
RECS_HEADER = ["Date", "Deck", "Source", "Cut", "Add", "Cut Rank", "Cut Of",
               "Cut Protected", "Add Surfaced", "Add Rank", "Add Of"]
# `suggest`'s default display window — "surfaced" means "a human running the default
# command would have SEEN it", not "it appears somewhere in 2,500 scored picks".
_RECS_SUGGEST_WINDOW = 20
# Below this many recorded swaps the report refuses to summarize, the same restraint
# `parse_matches --report` and `count_conf` show. A hit rate over six swaps is noise.
_RECS_MIN_SAMPLE = 20


def recommendation_row(d, cut, add, source, today=None):
    """Score an ACCEPTED swap against what the recommenders said at that moment.

    `swap --apply` is the only place in this toolkit where a human's real add/cut
    decision is observable, and nothing recorded it — so every ranking model here
    (`cuts`, `suggest`, the bounded co-signals, the whole gated stack) has been graded
    on argument and anchor tests, never against a single decision anyone actually made.
    That is the same gap CLAUDE.md records for the `Decks` column: it read as working
    right up until someone MEASURED it and found a 0% actionable rate.

    Deliberately measurement ONLY — nothing here feeds back into a score. The scoring
    terms are bounded and anchored by `check_suggest` precisely so they can't silently
    reorder a tuned deck, and a feedback loop that quietly re-weighted them would defeat
    that by construction. This writes a ledger a human reads.

    Ranks are captured NOW, against the pre-swap deck, because that is the list the
    decision was made against; re-deriving one later would score against a deck the swap
    already changed.

    Returns a row dict, or None if neither model could be computed."""
    import datetime
    row = {c: "" for c in RECS_HEADER}
    row.update({"Date": today or datetime.date.today().isoformat(),
                "Deck": d["id"], "Source": source, "Cut": cut, "Add": add})
    got = False

    # The cut side is the CLEAN measurement: `cuts` ranks the cards already in the deck,
    # so the cut always has a well-defined position in a list that always contains it.
    try:
        rows, _central, prot_present, _int = rank_cut_candidates(d)
        cl = cut.strip().lower()
        idx = next((i for i, r in enumerate(rows) if r[1].strip().lower() == cl), None)
        row["Cut Of"] = len(rows)
        row["Cut Protected"] = "yes" if cl in {p.strip().lower() for p in prot_present} \
            else "no"
        if idx is not None:
            row["Cut Rank"] = idx + 1          # 1 = the model's most-cuttable card
        got = True
    except Exception:
        # Telemetry must never cost a swap. A model that raises here (missing pool,
        # unreadable card data) loses its column, not the edit.
        pass

    # The add side is INCOMPLETE by construction and must be read as such: `suggest`
    # filters candidates to cards sharing a synergy THEME, so it is structurally blind
    # to lands and off-theme removal (that is what `--lands`/`--interaction`/`--ramp`
    # exist for). "Not surfaced" is therefore common and is NOT on its own a model miss.
    try:
        res = suggest_scored(d, limit=0)
        if res.get("ok"):
            picks = res["picks"]
            al = add.strip().lower()
            ai = next((i for i, p in enumerate(picks)
                       if p["name"].strip().lower() == al
                       or p["name"].strip().lower().split(" // ")[0] == al), None)
            row["Add Of"] = len(picks)
            row["Add Surfaced"] = "yes" if ai is not None and ai < _RECS_SUGGEST_WINDOW \
                else "no"
            if ai is not None:
                row["Add Rank"] = ai + 1
            got = True
    except Exception:
        pass
    return row if got else None


def load_recommendations(path=None):
    """Rows from the ledger, or [] if it doesn't exist yet. `path` resolves the module
    global at CALL time — a default argument would bind the real file even when a test
    repoints RECS_CSV, the stale-path bug `_file_memo` documents."""
    path = path or RECS_CSV
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def append_recommendation(row, path=None):
    """Append one row, writing through the shared atomic path so an interrupted write
    can't truncate the ledger. Its own DictWriter on its own fieldnames — never
    `lib.write_rows`, which emits the canonical 8 LIBRARY columns and would rewrite this
    file with the wrong header (audit F-02)."""
    path = path or RECS_CSV
    rows = load_recommendations(path) + [row]

    def _w(fh):
        w = csv.DictWriter(fh, fieldnames=RECS_HEADER, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in RECS_HEADER})
    atomic_write(path, _w, backup=False)
    return len(rows)


def _rec_percentile(row):
    """Where the cut sat in the cut list, 0.0 = the model's top cut candidate and 1.0 =
    the card it most wanted kept. None when unrankable."""
    try:
        rank, total = int(row.get("Cut Rank")), int(row.get("Cut Of"))
    except (TypeError, ValueError):
        return None
    if total < 2:
        return None
    return (rank - 1) / (total - 1)


def recommendation_summary(rows):
    """Pure summary of the ledger: (n, agreed, disagreements, median_pct, unsurfaced).

    `disagreements` are the swaps where the model wanted to KEEP the card the human
    cut (upper half of the cut list) — the informative direction, and the reason this
    report leads with them rather than with a hit rate. An AGREEMENT is contaminated by
    the shortlist having been read before the decision; a DISAGREEMENT is a case the
    model got wrong whether or not anyone read it."""
    scored = [(r, _rec_percentile(r)) for r in rows]
    scored = [(r, p) for r, p in scored if p is not None]
    n = len(scored)
    disagreements = sorted((r for r, p in scored if p > 0.5),
                           key=lambda r: -(_rec_percentile(r) or 0))
    agreed = n - len(disagreements)
    pcts = sorted(p for _, p in scored)
    median = None
    if pcts:
        mid = len(pcts) // 2
        median = pcts[mid] if len(pcts) % 2 else (pcts[mid - 1] + pcts[mid]) / 2
    unsurfaced = [r for r in rows if r.get("Add Surfaced") == "no"]
    return n, agreed, disagreements, median, unsurfaced


def recommendation_segments(rows, is_creature):
    """Split the ledger's cut ranking by whether the CUT card was a CREATURE.

    Returns `{segment: (n, agreed, median_pct)}` keyed `creature` / `noncreature` /
    `unknown`. Exists because ONE pooled agreement rate averages two regimes that
    differ by a factor of two, and a single number over a healthy and a broken
    channel reads as healthy — the same saturation failure as the `Decks` column at
    99% and the `review` verdict at 22-of-63. `cuts` scores a card by summing theme
    weights over its tags WITHOUT normalizing for tag count, and creatures carry far
    more tags than noncreature spells (tribes + keywords + ability tags), so they are
    systematically protected from the cut list.

    `is_creature` is INJECTED (name -> True / False / None) to keep this pure and to
    let a test supply a fake classifier. **A None is its own bucket, never folded into
    `noncreature`**: a card missing from `load_card_data` is unknown, and defaulting an
    unknown to "not a creature" would silently corrupt exactly the segment that reads
    as well-calibrated. Same rule as `lib.card_power` returning None for `*`/`X` rather
    than inventing a number.
    """
    buckets = {}
    for r in rows:
        pct = _rec_percentile(r)
        if pct is None:
            continue
        v = is_creature(r.get("Cut", ""))
        key = "unknown" if v is None else ("creature" if v else "noncreature")
        buckets.setdefault(key, []).append(pct)
    out = {}
    for key, pcts in buckets.items():
        pcts.sort()
        mid = len(pcts) // 2
        median = pcts[mid] if len(pcts) % 2 else (pcts[mid - 1] + pcts[mid]) / 2
        # `agreed` mirrors recommendation_summary: a disagreement is pct > 0.5, so an
        # agreement is everything at or below. Keep the two in step — they are the same
        # question asked of the same rows.
        out[key] = (len(pcts), sum(1 for p in pcts if p <= 0.5), median)
    return out


def cut_creature_classifier(carddata):
    """name -> True (creature) / False (noncreature) / None (not on file), for
    `recommendation_segments`. Resolves a DFC by its FRONT face the way every other
    name join here does (`load_card_data` keys it under both, but a ledger row stores
    whatever the deck line said)."""
    def check(name):
        nl = (name or "").strip().lower()
        if not nl:
            return None
        cd = carddata.get(nl) or carddata.get(nl.split(" // ")[0])
        if not cd:
            return None
        return "Creature" in (cd.get("type") or "")
    return check


_SEGMENT_LABEL = {"creature": "creature cuts", "noncreature": "noncreature cuts",
                  "unknown": "cut card not on file"}

# A segment dominated by ONE deck is not a rate for that segment — it is a rate for
# that deck wearing the segment's name. Decks with at least this many rows get their own
# line; a rate under three rows is not a rate. There is deliberately NO share threshold —
# see segment_concentration.
_RECS_CONC_MIN_ROWS = 3


def segment_concentration(rows, is_creature, segment="creature",
                          min_rows=_RECS_CONC_MIN_ROWS):
    """Per-deck breakdown of one segment, as (deck, n, agreed, share), worst-agreement
    first, for every deck contributing at least `min_rows` rows.

    Exists because testing the creature hypothesis turned up something the pooled
    segment rate hid: **the creature agreement rate is not a property of creatures.**
    Per deck it runs 0/6, 1/6, 3/6, 2/4, 4/4 — from 0% to 100% — so the 45% figure is
    largely a statement about which decks happened to be edited in the ledger window,
    not about how `cuts` grades bodies.

    The tempting story is that deck 46 (0/6) was rebuilt from scratch during the
    window, and a cut made while a deck is being BUILT means "this didn't make the 60",
    which is not the question `cuts` ranks — it scores against a coherent list a
    half-built deck does not yet have. That is a real mechanism and it fits deck 46.
    **It does not fit deck 3 at 1/6**, which was an ordinary tune. So the rebuild
    effect is at best partial, and the wider finding is the variance itself.

    Disclosed, NOT corrected for: these are post-hoc subgroups of 4-6 rows, the
    intervals are enormous and overlap everything, and excluding deck 46 moves the
    segment only 45% → 56% — still under the noncreature 90%. The honest move is to
    show the reader where the rows came from and let a pre-registered test on future
    data settle it, the same restraint `_MIN_SAMPLE` and `count_conf` apply elsewhere.

    **There is deliberately no SHARE threshold.** The first draft disclosed a deck
    holding >20% of the segment, and deck 46 — the case that motivated the whole
    function — sits at 6/31 = 19.4% and did not print. The fix is not a lower cutoff:
    a threshold tuned until the finding you already believe appears is not a
    threshold, it is the finding smuggled into a constant. Every deck with enough rows
    for a rate gets a line, and the reader sees the concentration whatever it is.
    """
    per = {}
    for r in rows:
        pct = _rec_percentile(r)
        if pct is None:
            continue
        v = is_creature(r.get("Cut", ""))
        key = "unknown" if v is None else ("creature" if v else "noncreature")
        if key != segment:
            continue
        d = r.get("Deck") or "?"
        n, ok = per.get(d, (0, 0))
        per[d] = (n + 1, ok + (1 if pct <= 0.5 else 0))
    total = sum(n for n, _ in per.values())
    if not total:
        return []
    out = [(d, n, ok, n / total) for d, (n, ok) in per.items() if n >= min_rows]
    return sorted(out, key=lambda t: (t[2] / t[1], -t[1]))


def _print_recommendation_segments(rows):
    """Print the agreement rate split by creature vs noncreature cut.

    Each segment is held to the SAME `_RECS_MIN_SAMPLE` floor the pooled rate is: a
    segment rate computed off six rows is exactly the noise the floor exists to refuse,
    and splitting a sample is the moment that becomes easy to forget."""
    segs = recommendation_segments(rows, cut_creature_classifier(load_card_data()))
    shown = {k: v for k, v in segs.items()
             if k != "unknown" and v[0] >= _RECS_MIN_SAMPLE}
    if len(shown) < 2:
        thin = [f"{_SEGMENT_LABEL[k]} n={v[0]}" for k, v in sorted(segs.items())
                if k != "unknown" and v[0] < _RECS_MIN_SAMPLE]
        if thin:
            print(f"  (by segment: {', '.join(thin)} — under ~{_RECS_MIN_SAMPLE}, "
                  f"so no split rate; the pooled figure is all this sample supports.)")
        return
    print("\n  By segment — the pooled rate above averages these, so read them instead:")
    for key in ("creature", "noncreature"):
        if key not in shown:
            continue
        n, agreed, median = shown[key]
        print(f"    {_SEGMENT_LABEL[key]:18} {agreed}/{n} ({100 * agreed / n:.0f}%)"
              f"   median {median:.0%} toward 'keep'")
    unk = segs.get("unknown")
    if unk:
        print(f"    ({unk[0]} row(s) whose cut card is not in card-library/pool — "
              f"excluded from both, not folded into either.)")
    lo = min(shown.items(), key=lambda kv: kv[1][1] / kv[1][0])
    if lo[1][1] / lo[1][0] < 0.55:
        print(f"  ⚠ {_SEGMENT_LABEL[lo[0]]} sit near a coin flip — `cuts` scores a card "
              f"by SUMMING theme weights over its tags with no normalization for tag "
              f"count, and creatures carry roughly twice as many tags as noncreature "
              f"spells, so they are systematically protected. Treat the cut ranking as "
              f"a shortlist there, not a signal; grade from the printed oracle text.")
        # Disclose a deck dominating the weak segment. One deck's rate wearing the
        # segment's name is the same "a pooled number hides a split" failure the
        # segmentation itself exists for, one level down (see segment_concentration).
        conc = segment_concentration(rows, cut_creature_classifier(load_card_data()),
                                     segment=lo[0])
        if conc:
            print(f"    Where these rows come from (≥{_RECS_CONC_MIN_ROWS} rows), "
                  f"worst agreement first:")
            for d, n, ok, share in conc:
                print(f"      deck {d:<5} {ok}/{n} ({100 * ok / n:>3.0f}%)  "
                      f"— {share:.0%} of the segment")
            print("      A deck being BUILT contributes cuts meaning \"this didn't make "
                  "the 60\", which is not the\n      question `cuts` ranks — it scores "
                  "against a coherent list a half-built deck does not\n      yet have. "
                  "Read a dominating deck's rows before trusting the segment rate.")


def cmd_feedback(args):
    """Report how the recommenders scored against the swaps actually applied."""
    rows = load_recommendations()
    if getattr(args, "id", None):
        rows = [r for r in rows if r.get("Deck") == args.id]
    if not rows:
        print("No recommendation outcomes recorded yet. They accrue automatically "
              "every time `deck.py swap --apply` or `apply-flex --apply` runs.")
        return 0

    n, agreed, disagreements, median, unsurfaced = recommendation_summary(rows)
    print(f"{len(rows)} applied swap(s) recorded"
          + (f" for deck {args.id}" if getattr(args, "id", None) else "")
          + f"; {n} with a usable cut ranking.\n")

    # Lead with the misses. An agreement is partly the shortlist's own influence — the
    # human read `cuts` before deciding — so it cannot validate the model. A
    # disagreement is a case the model got wrong whichever way the decision was reached.
    if disagreements:
        print(f"⚠ {len(disagreements)} swap(s) where the model wanted to KEEP the card "
              f"you cut (upper half of its own cut list).")
        print("  These are the informative ones — read the card and ask what the "
              "ranking couldn't see.\n")
        for r in disagreements[:12]:
            pct = _rec_percentile(r)
            print(f"    {r.get('Date','')}  deck {r.get('Deck','')}: "
                  f"−{r.get('Cut','')} → +{r.get('Add','')}")
            print(f"        cuts ranked it {r.get('Cut Rank')}/{r.get('Cut Of')} "
                  f"({pct:.0%} toward 'keep')"
                  + ("   [was #: protect:]" if r.get("Cut Protected") == "yes" else ""))
        if len(disagreements) > 12:
            print(f"    … and {len(disagreements) - 12} more")
        print()

    if unsurfaced:
        print(f"{len(unsurfaced)} add(s) that `suggest` did not surface in its default "
              f"top {_RECS_SUGGEST_WINDOW}:")
        for r in unsurfaced[:10]:
            print(f"    +{r.get('Add','')}  (deck {r.get('Deck','')})")
        if len(unsurfaced) > 10:
            print(f"    … and {len(unsurfaced) - 10} more")
        print("  EXPECTED to be high, and not on its own a model miss: `suggest` filters "
              "to cards sharing a synergy THEME, so it is structurally blind to lands "
              "and off-theme removal. That is what `suggest --lands/--interaction/--ramp` "
              "are for. Read it as 'which fills the theme model can't reach'.\n")

    if n < _RECS_MIN_SAMPLE:
        tail = ("The rows above are worth reading individually"
                if (disagreements or unsurfaced)
                else "Nothing has diverged from the models yet")
        print(f"n={n} — too few to summarize (need ~{_RECS_MIN_SAMPLE}). {tail}; "
              f"a rate computed off {n} is noise.")
    else:
        print(f"Agreement: the cut sat in the model's cut half {agreed}/{n} times "
              f"({100 * agreed / n:.0f}%); median position {median:.0%} toward 'keep' "
              f"(0% = the model's top cut candidate).")
        print("  Read with care: you saw the shortlist before deciding, so a high "
              "agreement rate partly measures the list's INFLUENCE, not its accuracy. "
              "The disagreements above are the part that doesn't suffer from that.")
        _print_recommendation_segments(rows)
    print("\nThis ledger is REPORT-ONLY and never feeds back into a score — the ranking "
          "terms are bounded and anchored by check_suggest so they can't silently "
          "reorder a tuned deck, and an automatic re-weighting would defeat that.")
    return 0


def _do_swap(d, cut, add, apply, flex_entry=None):
    """Shared engine for `swap` and `apply-flex`: preview deltas, and on --apply
    perform the edit with a .bak + INV-04 re-check."""
    # A card can't be swapped for itself: it's a no-op, and on --apply the raw-line
    # edit would decrement (or delete) the shared line instead (audit F2). The
    # INV-04 copy-count guard wouldn't catch it, since a 1-for-1 swap preserves the
    # total — so reject it up front rather than silently corrupt the count.
    if cut.strip().lower() == add.strip().lower():
        eprint(f"Cut and add are the same card ({cut!r}) — nothing to swap.")
        return 1
    carddata = load_card_data()
    mana = load_mana()
    _, cards = parse_deck_file(d["path"])
    add_disp, add_set, add_cn = _printing_of(add)
    # Write the CANONICAL name, not the front-face shorthand the caller typed.
    add = add_disp
    after = _cards_after_swap(cards, cut, add, (add_set, add_cn))
    if after is None:
        eprint(f"{cut!r} is not in deck {d['id']}. Nothing swapped.")
        return 1
    if cut.strip().lower() in _protected(d.get("meta") or {}):
        eprint(f"⚠ {cut!r} is marked protected (#: protect:) in deck {d['id']} — a "
               "signature/spice card. Proceeding, but reconsider; remove it from the "
               "header if this cut is intentional.")

    nonland = [n for q, n, s, c in cards if n.lower() not in BASICS]
    fetch_missing_mana(sorted(set(nonland + [add])), mana)
    before_s = _deck_summary(cards, carddata, mana)
    after_s = _deck_summary(after, carddata, mana)

    cut_cd = carddata.get(cut.lower()) or {}
    cut_t = cut_cd.get("type", "") or "?"
    add_cd = carddata.get(add.lower())
    add_t = (add_cd or {}).get("type", "") or "?"
    _, _, qty_by = load_collection()
    have, _ = owned(qty_by, add)
    rar = load_rarities().get(add.lower(), "")
    add_mv = (mana.get(add.lower()) or (None, None))[1]

    # Print the FULL oracle text of both cards. Grading a swap from a type line
    # (or a truncated read) hides later abilities — the whole card must be in view.
    def _oracle(cd):
        return [ln for ln in (cd.get("text", "") or "").splitlines() if ln.strip()]

    print(f"Deck {d['id']}: {d['name'] or d['id']} — swap preview\n")
    print(f"  − {cut}   [{cut_t}]")
    for ln in _oracle(cut_cd):
        print(f"        {ln}")
    tail = " ".join(x for x in [rar, (f"×{have}" if have > 0 else "craft"),
                                (f"MV {add_mv}" if add_mv is not None else "")] if x)
    print(f"  + {add}   [{add_t}]" + (f"   ({tail})" if tail else ""))
    for ln in _oracle(add_cd or {}):
        print(f"        {ln}")
    if not add_cd:
        print(f"  ⚠ '{add}' not found in library or pool — check spelling; "
              "it will be added as a bare line.")

    def delta(a, b):
        d_ = b - a
        return f"{a} → {b}" + (f"  ({d_:+d})" if d_ else "")

    print("\n  deltas:")
    print(f"    total cards     {delta(before_s['total'], after_s['total'])}")
    print(f"    creatures       {delta(before_s['creatures'], after_s['creatures'])}")
    print(f"    avg nonland MV  {before_s['avg_mv']:.2f} → {after_s['avg_mv']:.2f}"
          f"  ({after_s['avg_mv'] - before_s['avg_mv']:+.2f})")
    b_col = "/".join(sorted(before_s["colors"])) or "—"
    a_col = "/".join(sorted(after_s["colors"])) or "—"
    print(f"    color identity  {b_col} → {a_col}"
          + ("   (adds a color!)" if after_s["colors"] - before_s["colors"] else ""))

    if not apply:
        print("\n(dry run — pass --apply to write the change with a .bak)")
        return 0

    # Score the recommenders against this decision BEFORE the edit — the pre-swap deck
    # is the list the human actually chose from. Never fatal: a swap must not fail
    # because telemetry did.
    try:
        rec = recommendation_row(d, cut, add, "flex" if flex_entry is not None else "swap")
    except Exception:
        rec = None

    with open(d["path"], encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    try:
        # `(add_set, add_cn)`, the same printing tuple `_cards_after_swap` gets above.
        # P8 split `_printing_of`'s return from a 2-tuple into three values and updated
        # the first call site but not this one, leaving `add_pr` dangling — so EVERY
        # `swap --apply` raised NameError while the dry run, which returns before this
        # line, stayed clean. Nothing caught it: `check_commands` marks `swap` covered
        # because a skill REFERENCES it, and no test drives the write path.
        new_lines = _swap_edit_lines(lines, cut, add, (add_set, add_cn),
                                     drop_flex=flex_entry)
        bak = _safe_write_lines(d["path"], new_lines, before_s["total"])
    except ValueError as e:
        eprint(f"Not saved: {e}")
        return 1
    print(f"\nApplied. Wrote {os.path.relpath(d['path'], REPO_ROOT)} "
          f"(backup: {os.path.basename(bak)}).")
    if flex_entry is not None:
        print("Removed the consumed flex line.")
    # The add inherits the cut's line slot, and therefore the cut's `# section` comment.
    # Warn when that makes the file lie (advisory — the swap is already written, and
    # moving a line is a human editorial call, not something to do automatically).
    ai = next((i for i, ln in enumerate(new_lines)
               if (_card_line_name(ln) or "").lower() == add.strip().lower()), None)
    if ai is not None:
        warn = section_mismatch(new_lines, ai, add.strip(), load_card_data())
        if warn:
            print(f"  ⚠ section comment: {warn}")
    # Record how the recommenders scored this decision. Written AFTER the edit lands, so
    # a rejected write leaves no phantom row; announced rather than silent, because a
    # command that writes a second file should say so.
    if rec is not None:
        try:
            total = append_recommendation(rec)
            bits = []
            if rec.get("Cut Rank"):
                bits.append(f"cuts ranked −{cut} {rec['Cut Rank']}/{rec['Cut Of']}")
            if rec.get("Add Surfaced"):
                bits.append(f"suggest surfaced +{add}: {rec['Add Surfaced']}")
            print(f"  · recorded to {os.path.basename(RECS_CSV)} ({total} swap(s)): "
                  + "; ".join(bits) + ".  Read it: deck.py feedback")
        except OSError as e:
            eprint(f"  · could not record the outcome ({e}) — the swap itself is saved.")
    return 0


def cmd_swap(args):
    """Preview (or --apply) a single -cut/+add swap with before/after deltas."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    return _do_swap(d, args.cut, args.add, args.apply)


def cmd_apply_flex(args):
    """Promote flex swap #n (a `#~ -Out | +In` line) into the maindeck."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    swaps = [e for e in parse_flex(d["path"]) if e["out"] and e["in"]]
    if not swaps:
        print("No applicable flex swaps (need a '#~ -Out | +In' line). "
              f"See: deck.py flex {args.id}")
        return 0
    if args.n < 1 or args.n > len(swaps):
        eprint(f"Flex swap #{args.n} out of range (1..{len(swaps)}). "
               f"See: deck.py flex {args.id}")
        return 1
    e = swaps[args.n - 1]
    return _do_swap(d, e["out"], e["in"], args.apply, flex_entry=e)


# --- deck-construction legality lint ---------------------------------------- #
# Formats where the deck is singleton (at most one of each nonbasic) and/or has a
# larger minimum size than the 60-card constructed default.
SINGLETON_FORMATS = {"brawl", "historic brawl", "commander", "oathbreaker", "duel"}
BIG_DECK_FORMATS = {"commander", "historic brawl", "oathbreaker"}
# Formats led by a legendary creature/planeswalker commander with a color-identity lock
# (Oathbreaker's PW-commander + signature-spell rules differ, so it's excluded here).
_COMMANDER_FORMATS = {"brawl", "historic brawl", "commander", "duel"}


def load_legalities():
    """name_lower -> set(formats the card is legal in), from card-pool.csv's
    Legalities column. Empty if the pool is missing or predates the column."""
    out = {}
    if not os.path.exists(POOL_CSV):
        return out
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            if not n:
                continue
            legs = {x.strip().lower() for x in (r.get("Legalities") or "").split(";")
                    if x.strip()}
            out.setdefault(n, legs)
            out.setdefault(n.split(" // ")[0], legs)
    return out


def legality_report(meta, cards, fmt, leg, carddata=None):
    """Pure legality computation shared by `legal` (verbose, one deck) and `audit`
    (one line per deck) so both apply IDENTICAL size/copy/format rules. Returns a
    dict: problems (list of strings), unknown (pool-absent card names), notes
    (informational lines about untracked formats / missing legality data), plus
    total / min_size / copy_limit / singleton for the caller to render. Offline —
    `leg` is a pre-loaded load_legalities() map (pass {} to skip the format check).

    Format-aware extras:
      • Singleton formats (Brawl/Commander) enforce the 1-copy limit (already), and
        when `carddata` is supplied ALSO validate the `#: commander:` — it must be a
        legendary creature/planeswalker in the deck, and every nonbasic card's color
        identity must sit within the commander's (Brawl's defining rule).
      • Alchemy: a card that's Standard-legal but not Alchemy-legal is REBALANCED, not
        illegal — Arena plays its A- version — so it's a note, not a problem."""
    counts, order, disp, total = {}, [], {}, 0
    for q, n, s, c in cards:
        total += q
        nl = n.lower()
        if nl in BASICS:
            continue
        if nl not in counts:
            order.append(nl)
            disp[nl] = n
        counts[nl] = counts.get(nl, 0) + q

    singleton = fmt in SINGLETON_FORMATS
    copy_limit = 1 if singleton else 4
    min_size = 100 if fmt in BIG_DECK_FORMATS else 60

    problems, unknown, notes = [], [], []
    if fmt and total < min_size:
        problems.append(f"deck has {total} cards — {fmt} minimum is {min_size}")

    for nl in order:
        if counts[nl] > copy_limit:
            problems.append(f"{disp[nl]}: {counts[nl]} copies (max {copy_limit}"
                            + (", singleton format" if singleton else "") + ")")

    if fmt and fmt in POOL_FORMATS and leg:
        illegal, rebalanced = [], []
        for nl in order:
            card_leg = leg.get(nl)
            if card_leg is None:
                unknown.append(disp[nl])
            elif fmt not in card_leg:
                # A Standard card that isn't Alchemy-legal is rebalanced (A- version),
                # not illegal — it's still playable in Alchemy.
                if fmt == "alchemy" and "standard" in card_leg:
                    rebalanced.append(disp[nl])
                else:
                    illegal.append(disp[nl])
        for name in illegal:
            problems.append(f"{name}: not legal in {fmt}")
        if rebalanced:
            notes.append(f"{len(rebalanced)} card(s) are Alchemy-rebalanced — they play as "
                         f"their A- version in Alchemy (still legal): "
                         + ", ".join(rebalanced[:8]) + (" …" if len(rebalanced) > 8 else ""))
    elif fmt and fmt not in POOL_FORMATS:
        notes.append(f"Format '{fmt}' isn't tracked for legality "
                     f"(known: {', '.join(sorted(POOL_FORMATS))}) — checking size/copies only.")
    elif fmt and not leg:
        notes.append("card-pool.csv has no legality data (rebuild with build_pool.py) — "
                     "checking size/copies only.")

    # Commander rules (Brawl / Commander) — needs card types + identities.
    if singleton and fmt in _COMMANDER_FORMATS and carddata is not None:
        cmd_name = (meta.get("commander") or "").strip()
        if not cmd_name:
            problems.append(f"{fmt} needs a `#: commander:` header — a legendary creature "
                            "or planeswalker in the deck (it leads from the command zone)")
        else:
            cnl = cmd_name.lower()
            ccd = carddata.get(cnl) or carddata.get(cnl.split(" // ")[0])
            cident = None
            if ccd is None:
                notes.append(f"commander {cmd_name!r} not in card data — can't verify its "
                             "type/identity (check spelling, or rebuild the pool)")
            else:
                ctype = ccd.get("type", "") or ""
                if not ("Legendary" in ctype and ("Creature" in ctype or "Planeswalker" in ctype)):
                    problems.append(f"commander {cmd_name}: must be a legendary creature or "
                                    f"planeswalker (is {ctype or '?'})")
                cident = card_colors(ccd.get("colors", ""))
                if cnl not in counts:
                    notes.append(f"commander {cmd_name} isn't listed in the deck — add it "
                                 f"(it counts as one of the {min_size})")
            if cident is not None:
                strays = []
                for nl in order:
                    cd2 = carddata.get(nl) or carddata.get(nl.split(" // ")[0])
                    if cd2 and not card_colors(cd2.get("colors", "")) <= cident:
                        strays.append(disp[nl])
                if strays:
                    ident_s = "".join(sorted(cident)) or "C"
                    problems.append(f"outside commander's color identity ({ident_s}): "
                                    + ", ".join(strays[:8]) + (" …" if len(strays) > 8 else ""))

    return {"problems": problems, "unknown": unknown, "notes": notes,
            "total": total, "min_size": min_size, "copy_limit": copy_limit,
            "singleton": singleton}


def cmd_legal(args):
    """Deck-construction legality lint: deck size, copy limits, and per-card format
    legality against the deck's declared `#: format:` (override with --format). Size
    and copy rules are offline; the legality check needs the pool's Legalities
    column (build_pool.py). Basic lands are exempt (unlimited)."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    meta, cards = parse_deck_file(d["path"])
    fmt = (getattr(args, "fmt", None) or meta.get("format") or "").strip().lower()

    rep = legality_report(meta, cards, fmt, load_legalities(), carddata=load_card_data())
    problems, unknown, total, min_size = (rep["problems"], rep["unknown"],
                                          rep["total"], rep["min_size"])

    print(f"Deck {d['id']}: {d['name'] or d['path']} — legality check"
          + (f"  ({fmt})" if fmt else "  (no #: format: declared)"))
    print("-" * 52)

    print(f"Deck size: {total} cards" + (f"  (min {min_size})" if fmt else ""))
    for note in rep["notes"]:
        print(note)

    if problems:
        print(f"\n✗ {len(problems)} construction issue(s):")
        for p in problems:
            print(f"    {p}")
    else:
        print("\n✓ No construction issues"
              + (f" for {fmt}." if fmt else " (size/copy rules only — no format declared)."))

    # PRINTING sanity. Legality is about the card; this is about whether the LINE names
    # a printing that exists — the half nothing checked, so a wrong collector number
    # produced a file that read clean everywhere and would not import (F-01).
    bad_set, unverified = printing_problems(cards)
    if bad_set:
        print(f"\n✗ {len(bad_set)} line(s) name a SET CODE that does not exist:")
        for n, st, cn in bad_set:
            print(f"    {n} — ({st}) {cn}")
    if unverified:
        print(f"\n△ {len(unverified)} unverified printing(s) — the set is real but this "
              "collector number is not one we hold (the pool keys ONE printing per card, "
              "so an alternate art lands here too):")
        for n, st, cn, kn in unverified:
            known = ", ".join(f"({a.upper()}) {b}" for a, b in kn)
            print(f"    {n} — ({st}) {cn}   known: {known}")
    if unknown:
        shown = ", ".join(unknown[:8]) + ("…" if len(unknown) > 8 else "")
        print(f"\n{len(unknown)} card(s) not in the pool — {fmt} legality unverified "
              f"(WIP / older printings): {shown}")
    return 1 if problems else 0


# --- cut candidates: the companion to `suggest` (adds) ---------------------- #
def _protected(meta):
    """Cards a deck's `#: protect:` header marks as signature/spice — the tooling
    must never propose cutting them. Format: `#: protect: Card A; Card B`
    (repeatable across lines; SEMICOLON-separated — card names contain commas, so
    comma can't be the separator). Returns a lowercased set of card names."""
    raw = (meta or {}).get("protect", "") or ""
    return {p.strip().lower() for p in raw.split(";") if p.strip()}


def _uncastable_ok(meta):
    """Cards the deck AUTHOR asserts are intentionally uncastable — a REANIMATOR's
    targets, which you never cast from hand and cheat in from the graveyard instead.
    Format: `#: uncastable-ok: Card A; Card B` (semicolon-separated, like `#: protect:`,
    because card names contain commas). Returns a lowercased set.

    Why this exists: the castability lint and `tier_band` both model "you cannot cast
    this" as a build ERROR, which is right by default and wrong for a whole archetype.
    Measured on deck 52a, a mono-black reanimator: adding ONE five-colour bomb moved
    `preflight` from READY to BLOCKED and the metrics floor from A to C — three bands,
    for a card working exactly as designed. Reanimator is not an exotic case; it is the
    reason `Zombify` and `Rise of the Dark Realms` are in the pool at all.

    Deliberately OPT-IN and per-card. Most uncastable cards really are mistakes, so the
    default stays a hard FAIL; this is the author making a specific claim, the same
    shape as `#: protect:` naming signature cards the tooling must not propose cutting.
    An exempt card is still SHOWN everywhere it was shown before — it moves out of the
    failure list, not out of sight (G-52: a verdict surface must print its evidence)."""
    raw = (meta or {}).get("uncastable-ok", "") or ""
    return {p.strip().lower() for p in raw.split(";") if p.strip()}


def _signature_themes(meta, cards, cardmeta):
    """The themes carried by a deck's `#: protect:` cards — the human-designated
    SPINE. A theme here counts as the deck's signature even when it's otherwise
    'generic' (idf-low): a counters deck that protects two counter-doublers IS a
    counters deck, so a counter card is a KEY fit, not tangential. Corrects the idf
    blind spot where a broadly-common theme (counters/tokens/…) is THIS deck's actual
    plan. Empty when no `#: protect:` header is set (falls back to pure idf)."""
    prot = _protected(meta)
    if not prot:
        return frozenset()
    sig = set()
    for q, n, s, c in cards:
        if n.lower() in prot:
            m = cardmeta.get(n.lower())
            if m:
                sig.update(m["synergies"])
    return frozenset(sig)


def cut_scoring_context(meta, cards, cardmeta, carddata):
    """The deck-level inputs a cut keep-score reads: theme weights, the central
    themes, the `#: protect:` spine, the deck's role tally (for saturation) and its
    creature-subtype counts. Split out so `rank_cut_candidates` and `_weakest_cut`
    build the SAME context from the same cards — see `cut_keep_score`."""
    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = cardmeta.get(n.lower())
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    sub_count = {}
    for q, n, s, c in cards:
        cd = carddata.get(n.lower())
        if cd:
            for st in creature_subtypes(cd["type"]):
                sub_count[st] = sub_count.get(st, 0) + q
    return {
        "cards": cards,
        "carddata": carddata,
        "theme_w": theme_w,
        "central": _central_themes(theme_w),
        # The STRICT spine (a theme carried by >=2 `#: protect:` cards), not the loose
        # union of every protected card's tags. Measured: the loose set fired the +2
        # keep-boost on **86%** of nonland cards across the 22 decks that declare
        # `#: protect:` — 100% in decks 20 and 46 — and a boost applied to every card in
        # a ranking is a constant, carrying no information where it saturates and applied
        # off a 25-theme union where it does not. The strict set fires on 66%.
        #
        # This is `check_suggest` anchor 11b's fix one caller over: that anchor forces
        # `cmd_suggest_homes` to hand `fit_strength` the strict set for the same reason
        # (the loose union gave 99 KEYs where the strict gives 54, every difference a
        # false KEY). The rescue this term exists for survives — deck 30's protected
        # counter-doublers give a strict signature of exactly `{counters}`, so a counters
        # card in a counters deck is still boosted.
        "signature": _strong_signature_themes(meta, cards, cardmeta),
        "deck_tally": role_tally(cards, carddata),
        "sub_count": sub_count,
    }


def cut_keep_score(ctx, tline, text, tags, rarity="", qty=1):
    """THE keep-score for "how cuttable is this card in this deck" — higher = keep.

    ONE definition, because there used to be two. `rank_cut_candidates` (what
    `deck.py cuts` prints, what `tier --to` pairs its adds against, and what the
    recommendation ledger scores a swap by) summed nine terms; `_weakest_cut` — the
    cut hint `suggest-homes` prints on every fit row — summed three of them, and
    matched none of the co-signals added since. They disagreed on **36 of 64 decks**,
    and the disagreements were not cosmetic: `suggest-homes` proposed cutting Bloom
    Tender from deck 17 and Vizier of the Menagerie from decks 34/36 — the roster's
    best fixers, and the exact cards the `_is_color_fixer` work was done to protect.

    This is the F-01 shape one more time, and the reason a pure-function anchor could
    not see it: every co-signal here (`_cuts_power_adj` / `_cuts_uniq_adj` /
    `_cuts_multiplier_adj`) is provably bounded and monotonic, and each is gated by a
    `check_suggest` anchor — but a second caller that never calls them is invisible to
    all of that. `check_agreement.py` now holds the two answers together on the live
    roster, which is the only place the divergence was ever visible.

    Returns (keep, parts) — `parts` carries the display pieces the cut table shows
    (fit, roles, power, uniq, the multiplier axis/support, the cost-as-upside flags)
    so the caller never recomputes one and drifts again."""
    theme_w, central = ctx["theme_w"], ctx["central"]
    fit, hit_central = 0, False
    for t in tags:
        if t in theme_w:
            fit += theme_w[t]
            if t in central:
                hit_central = True
    roles = classify_roles(text)
    subs = set(creature_subtypes(tline))
    tribal = sum(ctx["sub_count"].get(st, 0) for st in subs)
    upside = cost_upside_flags(text, central)
    sig_hit = bool(set(tags) & ctx["signature"])

    # Card-quality co-signal (#3): the wishlist's rarity+role power estimate, so an
    # on-theme-but-WEAK card sorts UP the cut list and an on-theme BOMB is protected —
    # something pure theme-fit can't distinguish (a vanilla and a bomb sharing one tag
    # look equal). Bounded (±_CUTS_POWER_CAP), so it only breaks near-ties (see
    # _cuts_power_adj / check_suggest #7); it never overrides theme fit.
    # NOTE: `rarity` comes from load_rarities() — Arena wildcard LETTERS ("M"/"R"/"U"/
    # "C"), not rarity words. wishlist._norm_rarity accepts both shapes; before it did,
    # every rare/mythic fell through to the default floor and seeded as an uncommon (F-01).
    power = _power_seed({"Rarity": rarity, "Card Text": text, "Type": tline})

    # Ability-distinctiveness co-signal: a generic-ability body (low pool tag-rarity)
    # sorts UP the cut list; a distinctive-mechanic card is mildly protected. Bounded
    # (±_CUTS_UNIQ_CAP) and orthogonal to power (see _cuts_uniq_adj / check_suggest #8).
    uniq = card_distinctiveness(tags, text)

    # Multiplier co-signal: a doubler is worth what it doubles, and neither theme-fit
    # nor role-credit can see that. Routed through the SAME doubler primitives
    # `suggest-homes` uses, so the two models can't disagree (see _cuts_multiplier_adj
    # / check_suggest #16).
    mult_axis = doubler_axis(text)
    mult_support = (doubler_support(mult_axis, ctx["cards"], ctx["carddata"],
                                    doubler_restriction(text))
                    if mult_axis else 0)

    # keep-score: higher = keep; cut candidates sort to the top (lowest keep).
    # Role credit is impact-weighted (see _role_credit) so a strong-but-off-theme
    # card (removal/engine/cost-reducer) isn't mis-ranked as a top cut. Passing the
    # deck's role tally makes that credit SATURATION-aware (#1): a redundant piece
    # (the 8th removal spell) loses most of its bonus and sorts UP the cut list,
    # while the deck's ONLY counterspell keeps full credit and stays protected. A
    # card on the deck's #: protect: signature theme gets a further keep-boost (F#3)
    # so a generic-tagged-but-central theme (e.g. counters) isn't mistaken for filler.
    keep = (fit + _role_credit(roles, ctx["deck_tally"]) + (1 if hit_central else 0)
            + (2 if sig_hit else 0) + min(tribal, 6)
            + _cuts_power_adj(power) + _cuts_uniq_adj(uniq)
            + _cuts_multiplier_adj(mult_support))

    reasons = []
    if tags and not hit_central:
        reasons.append("off the deck's central themes")
    elif not tags:
        reasons.append("no synergy tags")
    if not roles:
        reasons.append("role not auto-detected — read text")
    if subs and tribal <= qty:
        reasons.append("off-tribe")
    if power <= 3.0 and (hit_central or sig_hit):
        reasons.append(f"on-theme but low power (~{power:.1f})")
    if uniq <= 1.5 and not sig_hit:
        reasons.append("generic ability — trips broad synergy checks")

    return keep, {"fit": fit, "roles": roles, "power": power, "uniq": uniq,
                  "upside": upside, "reasons": reasons, "tribal": tribal,
                  "is_int": bool(set(roles) & _INTERACTION_ROLES),
                  "mult": (mult_axis, mult_support)}


def rank_cut_candidates(d):
    """Rank a deck's nonland cards most→least cuttable and return
    (rows_sorted, central, prot_present, deck_int). Each row is
    (keep, name, mv, roles, fit, reasons, ctx, text, is_int, power) — the shared
    ranking behind both `cmd_cuts` (which prints it) and the tier `--to` tune plan
    (which pairs the weakest cuts with the fillers that close a tier gap). Higher
    `keep` = keep; lower sorts to the top of the cut list.

    Scores each card through the shared `cut_keep_score`, which `_weakest_cut` also
    uses — the two answers to "this deck's most-cuttable card" used to be computed by
    separate formulas and disagreed on 36 of 64 decks."""
    meta, cards = parse_deck_file(d["path"])
    protected = _protected(meta)
    cardmeta = load_card_meta()
    carddata = load_card_data()
    mana = load_mana()
    rar = load_rarities()

    sctx = cut_scoring_context(meta, cards, cardmeta, carddata)
    central = sctx["central"]
    deck_int = sctx["deck_tally"]["interaction"]           # for the F#1 interaction guard

    rows, seen, prot_present = [], set(), []
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS or nl in seen:
            continue
        if nl in protected:
            prot_present.append(n)
            seen.add(nl)
            continue
        cd = carddata.get(nl)
        tline = (cd["type"] if cd else "") or ""
        if "Land" in _primary_type(tline):
            continue
        seen.add(nl)
        tags = cardmeta.get(nl, {}).get("synergies", [])
        text = cd["text"] if cd else ""
        cost, mv = (mana.get(nl) or (None, None))
        ctx = context_flags(text, cost)
        keep, p = cut_keep_score(sctx, tline, text, tags, rarity=rar.get(nl, ""), qty=q)
        rows.append((keep, n, mv, sorted(p["roles"]), p["fit"], p["reasons"], ctx, text,
                     p["is_int"], p["power"], p["uniq"], p["upside"], p["mult"]))

    rows.sort(key=lambda r: (r[0], r[1].lower()))
    return rows, central, prot_present, deck_int


def cmd_cuts(args):
    """Rank the deck's nonland cards from most to least cuttable — the counterpart
    to `suggest` (which proposes adds). Heuristic from data the rest of the tooling
    already computes: a card is more cuttable when it sits OFF the deck's central
    themes, fills no functional role, and (in a tribal deck) shares no creature type
    the deck runs in numbers. Transparent by design — it shows the components so you
    judge, and it does NOT know your spice/signature cards, so read it as a
    shortlist, not a verdict."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    rows, central, prot_present, deck_int = rank_cut_candidates(d)
    if not rows:
        print(f"Deck {d['id']}: no nonland cards to evaluate.")
        return 0
    limit = args.limit if getattr(args, "limit", 0) and args.limit > 0 else len(rows)

    print(f"Deck {d['id']}: {d['name'] or d['path']} — cut candidates (weakest fit first)")
    print(f"Central themes: {', '.join(sorted(central)) or '(none)'}")
    if prot_present:
        print(f"Protected (kept OFF the cut list via #: protect:): {'; '.join(prot_present)}")
    print("Heuristic shortlist — read the text; it can't see spice/signature cards "
          "beyond the #: protect: header.\n")
    if deck_int < 5:
        print(f"⚠ deck runs only {deck_int} interaction piece(s) — rows tagged "
              f"⚠interaction are your removal/counters; cutting them lowers resilience.")
    # Zone conflicts (the mirror of ⚡): a card that EMPTIES a graveyard this deck needs
    # populated. Computed once for the deck and looked up by name, so the row tuple stays
    # the shape every other reader expects.
    _zmeta, _zcards = parse_deck_file(d["path"])
    _zconf = {nm: (scope, why, hit) for nm, scope, why, hit
              in zone_conflict_flags(_zcards, load_card_data())}
    if _zconf:
        # NAME them here rather than only tagging the row: `cuts` shows 8 rows by default
        # and a conflicted card can rank anywhere, so a header that just says "1 card"
        # can point below the fold — which is the same "the shortlist saw it but nobody
        # could tell why" failure this flag exists to fix.
        print(f"⛔ {len(_zconf)} card(s) FIGHT this deck's own engine — a good card that "
              f"empties a zone your plan needs FULL:")
        for _zn, (_sc, _why, _hit) in sorted(_zconf.items()):
            print(f"     {_zn} — {_why}")
            print(f"       needs it populated: {', '.join(_hit[:4])}"
                  + (f" … (+{len(_hit) - 4})" if len(_hit) > 4 else ""))
        print()
    # WHICH AXIS IS ACTUALLY SHORT. The `⚠interaction (deck runs N)` note below says a
    # removal card is redundant, and on deck 52a — whose measured weakness is its CURVE
    # (4.22 average, 12 early drops) — that hint put four ONE-MANA removal spells at the
    # top of the cut list. Trimming cheap cards from a deck that is too slow is backwards.
    # `tier --to` and `suggest --needs` both know what a deck is short on; `cuts` did not,
    # so it optimised the axis it could see. Stated rather than scored — the ranking is a
    # shortlist and this is the context that makes it readable.
    _vec = deck_quality_vector(d)
    _short = []
    if _vec["interaction"] < 5:
        _short.append(f"interaction {_vec['interaction']}")
    if _vec["card_advantage"] < 3:
        _short.append(f"card advantage {_vec['card_advantage']}")
    if _vec.get("early_drops", 99) < 18:
        _short.append(f"early drops {_vec['early_drops']} (avg MV {_vec['avg_mv']})")
    if _short:
        print(f"  ⓘ This deck is short on {', '.join(_short)} — weigh a `⚠interaction` note "
              "against that before cutting a cheap card from an axis you are not long on.")
    print(f"  {'Card':30} {'MV':>3}  {'Fit':>4}  {'Pw':>3}  {'Uq':>3}  Roles / why-cuttable")
    print("-" * 82)
    for (keep, n, mv, roles, fit, reasons, ctx, text, is_int, power, uniq, upside,
         mult) in rows[:limit]:
        mvs = str(mv) if mv is not None else "?"
        tail = ", ".join(roles) if roles else ("; ".join(reasons) if reasons else "—")
        low_pow = [r for r in reasons if r.startswith("on-theme but low power")]
        if roles and low_pow:  # a detected-role card can still be a weak body — say so
            tail += "  ·  " + low_pow[0]
        gen = [r for r in reasons if r.startswith("generic ability")]
        if roles and gen:  # a detected-role card can still be generic templating — say so
            tail += "  ·  " + gen[0]
        if ctx:
            tail += f"   ⚠ context: {'/'.join(ctx)}"
        if is_int:
            tail += f"   ⚠interaction (deck runs {deck_int})"
        # A card whose COST this deck turns into an upside is easy to mis-cut: every
        # model here grades it in isolation, where the cost reads as a drawback.
        if upside:
            tail += f"   ⚡cost-as-upside HERE ({upside[0]})"
        # The MIRROR: a card that reads fine alone but works AGAINST this deck's plan.
        if n in _zconf:
            tail += f"   ⛔fights your engine ({_zconf[n][1]})"
        # A MULTIPLIER: its value is in the rest of the deck, which is exactly what the
        # fit and role columns cannot show. Named so a keep-reason is legible, not just
        # baked into the score.
        if mult[0] and mult[1]:
            tail += f"   ✱multiplier — doubles {mult[0]} ({mult[1]} feeder(s) here)"
        # A card whose VALUE is a function of a deck property reads as its FLOOR here, so
        # it sorts up the cut list on a number that is not what you would cast it for:
        # Cat-Gator scores as a 7-mana 3/2 lifelink when its ETB is damage equal to your
        # Swamp count (24 in deck 52a). `suggest --needs` already flags this shape with
        # `⚠ scales w/`; `cuts` had no equivalent, so the same card was graded two ways by
        # two commands. FLAG only — the axis is fuzzy, and a score change on a fuzzy signal
        # is exactly what this file keeps having to undo.
        _ax = _int_scaling(text) or _deck_state_axis(text)
        if _ax:
            tail += f"   ⌁scales w/ {_ax} — graded here at its FLOOR"
        print(f"  {n[:30]:30} {mvs:>3}  {fit:>4}  {power:>3.0f}  {uniq:>3.0f}  {tail}")

    # Surface the actual oracle text so a cut is graded from what the card DOES,
    # never from the label above (the role map is a shortlist, not a verdict).
    import textwrap
    text_n = args.limit if getattr(args, "limit", 0) and args.limit > 0 else min(12, len(rows))
    print(f"\n── Oracle text of the top {min(text_n, len(rows))} cut candidates "
          f"(grade from THIS, not the label) ──")
    for (keep, n, mv, roles, fit, reasons, ctx, text, is_int, power, uniq, upside,
         _mult) in rows[:text_n]:
        warn = f"   ⚠ context: {'/'.join(ctx)} — value depends on this deck" if ctx else ""
        if is_int:
            warn += f"   ⚠interaction — 1 of the deck's {deck_int}"
        for u in upside:
            warn += f"\n    ⚡ cost-as-upside in THIS deck: {u}"
        if n in _zconf:
            _sc, _why, _hit = _zconf[n]
            warn += (f"\n    ⛔ FIGHTS YOUR ENGINE: {_why} — "
                     f"{', '.join(_hit[:4])}{' …' if len(_hit) > 4 else ''}")
        print(f"\n• {n}{warn}")
        for para in (text or "(no oracle text on file)").split("\n"):
            for line in (textwrap.wrap(para, width=86) or [""]):
                print(f"    {line}")
    print(f"\nRead the text above before cutting — the ranking is a shortlist, not a "
          f"verdict, and can't see spice/signature cards. Pair with "
          f"`deck.py suggest {d['id']}` for adds; preview a swap with "
          f"`deck.py swap {d['id']} --cut <weak> --add <pick>` (shows full text of both).")
    return 0


def cmd_verify(args):
    """Compare a pasted/piped Arena export against a stored deck and report either
    'identical' or a +/- differential by card. Case-insensitive, quantity-aware,
    and printing-fungible — a different printing (or basic-land art) of the same
    card counts as a match, since Arena copies are fungible across printings."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    try:
        text = sys.stdin.read() if args.source == "-" else open(args.source, encoding="utf-8").read()
    except OSError as e:
        eprint(f"Could not read {args.source!r}: {e}")
        return 1
    from import_arena import parse as parse_arena
    entries, warnings = parse_arena(text)
    for w in warnings:
        eprint(f"WARN:  {w}")
    if not entries:
        eprint("No card lines found in the pasted export.")
        return 1

    stored_cards = parse_deck_file(d["path"])[1]
    stored = _multiset(stored_cards)
    pasted = _multiset(entries)
    print(f"Deck {d['id']}: {d['name'] or d['id']} — vs pasted export")
    print("-" * 48)
    if "sideboard" in {ln.strip().lower() for ln in text.splitlines()}:
        eprint("Note: the export has a Sideboard section — its cards are included "
               "in this comparison (stored decks are maindeck-only).")
    added = removed = 0
    diffs = []
    for nl in sorted(set(stored) | set(pasted)):
        sd, pd = stored.get(nl, (None, 0)), pasted.get(nl, (None, 0))
        disp = pd[0] or sd[0]
        if pd[1] > sd[1]:
            diffs.append(f"  +{pd[1] - sd[1]}  {disp}")
            added += pd[1] - sd[1]
        elif sd[1] > pd[1]:
            diffs.append(f"  -{sd[1] - pd[1]}  {disp}")
            removed += sd[1] - pd[1]
    if not added and not removed:
        s_total = sum(q for q, *_ in stored_cards)
        print(f"  ✓ identical — the pasted export matches deck {d['id']} ({s_total} cards).")
        return 0
    for ln in diffs:
        print(ln)
    print("-" * 48)
    print(f"  {added} added, {removed} removed vs the stored deck")
    print("  (+ = the paste has more, − = the repo has more; compared by card name/qty "
          "— printings & basic-land art are the same card.)")
    return 1


# --- sync: reconcile stored decks FROM a multi-deck Arena paste -------------- #
# `verify` answers "did deck N drift?" for ONE deck you already identified, and the
# dashboard's stale-check answers it for many — but neither WRITES, so the actual repair
# was always "read a diff, then hand-edit N files". `sync` closes that loop: paste
# everything you exported from Arena, and it matches each block to its stored deck and
# reconciles the files. The matching rule is deliberately identical to the dashboard
# panel's (closest by total drift, with a shared-card floor and a low-confidence flag),
# since the two answer the same question; that JS copy can't share this code, so any
# change here belongs there too (build_dashboard.py, the stale-deck compare block).
_DECK_MARKER_RE = re.compile(r"^deck\s*$", re.I)


def split_paste(text):
    """An Arena paste containing one or MANY decks -> a list of line-blocks. Arena
    exports start each deck with a bare `Deck` line; text before the first one is
    treated as its own block, so a single-deck paste with no marker still works."""
    segs, cur = [], None
    for ln in (text or "").splitlines():
        if _DECK_MARKER_RE.match(ln.strip()):
            cur = []
            segs.append(cur)
            continue
        if cur is None:
            cur = []
            segs.append(cur)
        cur.append(ln)
    return [s for s in segs if any(x.strip() for x in s)]


def _ms_diff(pasted, stored):
    """(added, removed, diffs) between two `_multiset`s — `+` = the paste has more."""
    added = removed = 0
    diffs = []
    for nl in sorted(set(pasted) | set(stored)):
        p = pasted.get(nl, (None, 0))[1]
        s = stored.get(nl, (None, 0))[1]
        disp = pasted.get(nl, (None, 0))[0] or stored.get(nl, (None, 0))[0] or nl
        if p > s:
            added += p - s
            diffs.append(("+", p - s, disp))
        elif s > p:
            removed += s - p
            diffs.append(("-", s - p, disp))
    return added, removed, diffs


def match_paste(pasted, decks):
    """Best stored deck for one pasted block (Arena exports carry no deck name).

    `decks` is [(deck_record, multiset)]. Returns a dict describing the match, or
    ``{'unmatched': True}`` when nothing is close enough. Same rule as the dashboard:
    minimise total drift; require the block to share at least max(3, 30% of its distinct
    cards) with the deck, so an unrelated paste doesn't get force-fitted; flag LOW
    CONFIDENCE when the runner-up is within 2 drift and nearly as many shared cards
    (variants of one core deck look alike, and picking the wrong sibling would rewrite
    the wrong file)."""
    uniq = len(pasted)
    ranked = []
    for d, ms in decks:
        added, removed, diffs = _ms_diff(pasted, ms)
        shared = sum(1 for nl in pasted if nl in ms)
        ranked.append({"deck": d, "drift": added + removed, "shared": shared,
                       "added": added, "removed": removed, "diffs": diffs})
    if not ranked:
        return {"unmatched": True, "uniq": uniq}
    ranked.sort(key=lambda r: (r["drift"], -r["shared"], r["deck"]["id"]))
    best = ranked[0]
    if best["shared"] < max(3, uniq * 0.3):
        return {"unmatched": True, "uniq": uniq}
    runner = ranked[1] if len(ranked) > 1 else None
    best["lowconf"] = bool(runner and runner["drift"] - best["drift"] <= 2
                           and runner["shared"] >= best["shared"] * 0.8)
    best["runner_up"] = runner["deck"] if (runner and best["lowconf"]) else None
    best["sync"] = best["drift"] == 0
    best["uniq"] = uniq
    return best


def reconcile_lines(lines, target, printings):
    """Rewrite a deck file's raw lines so its card list becomes `target` (a `_multiset`).

    Line-level editing, like `_swap_edit_lines`: an existing card line keeps its printing
    and section position and only its QUANTITY changes, a card no longer in the list has
    its line dropped, and genuinely new cards are appended after the last card line — so
    `# Creatures` / `# Lands` comments, the `#:` header and `#~` flex lines all survive.
    A card split across two printing lines has its whole quantity assigned to the first
    and the rest dropped, matching `_multiset`'s printing-fungible view.

    Existing lines are matched on `_ms_key` — the SAME front-face-normalized key
    `_multiset` builds `target` with. Keying the file side on the raw name while the
    target side is normalized would make every `Front // Back` line look absent: its
    line would be dropped and a fresh one appended, silently rewriting the stored
    spelling and moving the card out of its `# section` (broad-scan F-02)."""
    remaining = {nl: q for nl, (_disp, q) in target.items()}
    out, last_card = [], -1
    for ln in lines:
        nm = _card_line_name(ln)
        if nm is None:
            out.append(ln)
            continue
        nl = _ms_key(nm)
        want = remaining.pop(nl, None)
        if not want:
            continue                      # dropped from the deck (or a consumed 2nd line)
        m = LINE_RE.match(ln.split("#", 1)[0].strip())
        indent = ln[:len(ln) - len(ln.lstrip())]
        rebuilt = f"{indent}{want} {m.group(2).strip()}"
        if m.group(3):
            rebuilt += f" ({m.group(3).strip()})" + (f" {m.group(4).strip()}" if m.group(4) else "")
        out.append(rebuilt)
        last_card = len(out) - 1
    new = []
    for nl, q in remaining.items():
        if not q:
            continue
        disp, setc, coll = printings.get(nl, (target[nl][0], "", ""))
        # `printings` is keyed front-face too, and for a DFC the LIBRARY row wins there —
        # and the library stores the front name alone. Writing that bare name back is the
        # P8 failure (parses, passes INV-04 and `legal`, fails an Arena import), so let
        # the fuller of the two spellings decide, exactly as `_multiset` does.
        disp = _ms_display(disp, target[nl][0])
        line = f"{q} {disp}"
        if setc:
            line += f" ({setc})" + (f" {coll}" if coll else "")
        new.append(line)
    at = last_card + 1 if last_card >= 0 else len(out)
    return out[:at] + sorted(new) + out[at:]


def cmd_sync(args):
    """Reconcile stored deck files FROM a pasted Arena export — the write half of
    `verify`. Dry-run by default; `--apply` writes each drifted deck with a `.bak` and
    the INV-04 re-check."""
    try:
        text = sys.stdin.read() if args.source == "-" else open(args.source, encoding="utf-8").read()
    except OSError as e:
        eprint(f"Could not read {args.source!r}: {e}")
        return 1
    from import_arena import parse as parse_arena
    blocks = split_paste(text)
    if not blocks:
        eprint("No deck blocks found in the paste.")
        return 1

    decks = [(d, _multiset(parse_deck_file(d["path"])[1])) for d in discover_decks()]
    printings = _printing_index()
    results, rc = [], 0
    print(f"Sync — {len(blocks)} pasted deck block(s) vs {len(decks)} stored decks\n")
    for i, block in enumerate(blocks, 1):
        entries, warnings = parse_arena("\n".join(block))
        for w in warnings:
            eprint(f"WARN:  block {i}: {w}")
        if not entries:
            continue
        pasted = _multiset(entries)
        m = match_paste(pasted, decks)
        if m.get("unmatched"):
            n = sum(q for q, *_ in entries)
            print(f"  ? block {i}: {n} cards, {m['uniq']} unique — no close stored deck "
                  "(a new deck? add it with /add-deck).")
            rc = 1
            continue
        d = m["deck"]
        label = f"#{d['id']} {d['name'] or d['id']}"
        if m["sync"]:
            print(f"  ✓ {label} — in sync")
            continue
        rc = 1
        conf = (f"   ⚠ low confidence — #{m['runner_up']['id']} is nearly as close"
                if m.get("runner_up") else "")
        print(f"  ⟳ {label} — drifted: {m['added']} added / {m['removed']} removed{conf}")
        for sign, qty, nm in m["diffs"]:
            print(f"        {sign}{qty}  {nm}")
        results.append((d, pasted, m))

    if not results:
        print("\nEvery matched deck is already in sync. ✓")
        return rc
    if not getattr(args, "apply", False):
        print(f"\n(dry run — {len(results)} deck file(s) would be rewritten to match the "
              "paste; pass --apply to write, each with a .bak)")
        return rc
    for d, pasted, m in results:
        if m.get("lowconf") and not getattr(args, "force", False):
            eprint(f"  ✗ #{d['id']}: skipped — low-confidence match (#{m['runner_up']['id']} "
                   "is nearly as close). Re-paste that deck alone, or pass --force.")
            continue
        with open(d["path"], encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        try:
            new_lines = reconcile_lines(lines, pasted, printings)
            bak = _safe_write_lines(d["path"], new_lines,
                                    sum(q for _disp, q in pasted.values()))
        except ValueError as e:
            eprint(f"  ✗ #{d['id']}: not saved — {e}")
            continue
        print(f"  ✓ #{d['id']}: wrote {os.path.relpath(d['path'], REPO_ROOT)} "
              f"(backup: {os.path.basename(bak)})")
    print("\nRe-check with `deck.py check <id>` / `deck.py preflight <id>`.")
    return rc


def _interaction_count(cards, carddata):
    """Copies of nonland spells that do removal / sweeping / countering — the same
    'interaction total' cmd_stats reports and the same number the quality/tier vector
    uses, all via the canonical `role_tally` so the three can't drift."""
    return role_tally(cards, carddata)["interaction"]


AUDIT_ORDER = {"TUNE": 0, "craft": 1, "review": 2, "ok": 3}

# Competitive power tier (from the deck's `#: tier:` header) — a win-capability
# grade separate from the maintenance-health verdict. S strongest → D weakest;
# "" (ungraded) sorts last.
TIER_ORDER = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4, "": 5}


def _deck_tier(meta):
    """The competitive tier LETTER (S/A/B/C/D) from a deck's `#: tier:` header,
    or '' if ungraded. The header is `#: tier: B — one-line rationale`; we keep
    only the leading letter so the audit can column/sort on it."""
    raw = (meta.get("tier") or "").strip()
    m = re.match(r"([SABCD])\b", raw)
    return m.group(1) if m else ""


def audit_deck(d, *, by_name_qty, carddata, mana, leg, cmeta):
    """Score one deck for the roster triage — the structured core shared by
    `cmd_audit` (CLI table) and build_dashboard.py (the roster Audit view), so the
    two can't drift. Pass the big lookups (collection / card data / mana / legalities
    / card meta) in pre-loaded so a whole-roster pass reads each CSV once. Returns a
    dict of raw counts + a verdict (TUNE / craft / review / ok) + human reasons; each
    caller renders its own cells. Offline — no Scryfall."""
    meta, cards = parse_deck_file(d["path"])
    fmt = (meta.get("format") or "").strip().lower()

    # Ownership: unique cards that are missing or short of the deck's need.
    need = {}
    for q, n, s, c in cards:
        need[n.lower()] = need.get(n.lower(), 0) + q
    short = 0
    for nl, req in need.items():
        disp = next(n for q, n, s, c in cards if n.lower() == nl)
        have, found = owned(by_name_qty, disp)
        if not found or have < req:
            short += 1

    rep = legality_report(meta, cards, fmt, leg, carddata=carddata)
    n_illegal = len(rep["problems"])

    declared = _declared_colors(meta)
    # `off_ability` — NOT `off_ident` — drives the verdict. A stray explained by a
    # hybrid pip is a card you pay on-color and never need to look at, and counting
    # those fired `review` on 22 of 63 decks with a 0% actionable rate (F-03).
    uncast, off_ident, off_ability, _intended = _castability(
        cards, declared, mana, carddata, _uncastable_ok(meta))

    interaction = _interaction_count(cards, carddata)

    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = cmeta.get(n.lower())
        if not m:
            continue
        for t in m["synergies"]:
            theme_w[t] = theme_w.get(t, 0) + q
    n_themes = len(_central_themes(theme_w))

    # Verdict: hard problems first (a tune target), then unbuilt, then soft.
    thin = interaction < (5 if rep["min_size"] >= 100 else 3)
    reasons = []
    if n_illegal:
        reasons.append(f"illegal ×{n_illegal}")
    if uncast:
        reasons.append(f"uncastable ×{len(uncast)}")
    if n_illegal or uncast:
        verdict = "TUNE"
    elif short:
        verdict = "craft"
        reasons.append(f"{short} to craft")
    elif off_ability or thin:
        verdict = "review"
        if off_ability:
            reasons.append(f"off-color ability ×{len(off_ability)}")
        if thin:
            reasons.append(f"thin interaction ({interaction})")
    else:
        verdict = "ok"

    return {
        "id": d["id"],
        "name": (d["name"] or os.path.basename(os.path.dirname(d["path"])) or d["id"]),
        "tier": _deck_tier(meta),
        "sz": rep["total"],
        "short": short,
        "illegal": n_illegal,
        "uncast": len(uncast),
        "stray": len(off_ident),
        # The actionable subset of `stray` — the only one that reaches the verdict.
        # `stray` stays the TOTAL so the Cast column keeps agreeing with `deck.py mana`.
        "stray_ability": len(off_ability),
        "int": interaction,
        "thm": n_themes,
        "thin": thin,
        "verdict": verdict,
        "why": ", ".join(reasons),
    }


def audit_roster():
    """Score every deck for the roster triage — loads each reference CSV once, then
    runs audit_deck per deck. Returns the list of row dicts (unsorted, discovery
    order). Shared by the CLI and the dashboard."""
    decks = roster_decks()
    refs = dict(by_name_qty=load_collection()[2], carddata=load_card_data(),
                mana=load_mana(), leg=load_legalities(), cmeta=load_card_meta())
    return [audit_deck(d, **refs) for d in decks]


def cmd_audit(args):
    """Roster-wide triage scorecard — one cheap, OFFLINE line per deck so you can see
    which decks actually need a full (expensive) tune-deck pass instead of re-tuning
    all of them. Reuses the same primitives the single-deck commands do:
      • Own   — ownership drift (missing / short craft targets), like `check`.
      • Legal — size / copy-limit / format-legality construction issues, like `legal`.
      • Cast  — cards that stray outside the deck's declared colors (strict-pip
                uncastable 'u' + softer off-identity 's'), like `check`/`mana`.
      • Int   — interaction count (removal + sweeper + counter), like `stats`.
      • Thm   — number of CENTRAL synergy themes (redundancy / focus signal).
    A deck is flagged TUNE for a hard problem (illegal / uncastable), review for a
    soft one (off-identity strays / thin interaction), craft when it's just unbuilt,
    else ok. No Scryfall calls — everything is read from the already-built CSVs."""
    scored = audit_roster()
    if not scored:
        print("No decks yet. Add one under decks/<NN-name>/deck.txt (see decks/README.md).")
        return 0

    _by_id = lambda ids: sorted(ids, key=lambda i: (len(i), i))
    tune = _by_id([r["id"] for r in scored if r["verdict"] == "TUNE"])
    craft = _by_id([r["id"] for r in scored if r["verdict"] == "craft"])
    review = _by_id([r["id"] for r in scored if r["verdict"] == "review"])

    rows = []
    for r in scored:
        # `Ns` is every identity stray (matching `deck.py mana`); `Na` marks the subset
        # that is an off-color ABILITY rather than a hybrid you pay on-color — the only
        # kind that reaches the verdict, so the column shows why a deck did or didn't.
        cast_cell = "✓" if not (r["uncast"] or r["stray"]) else \
            " ".join(([f"{r['uncast']}u"] if r["uncast"] else [])
                     + ([f"{r['stray']}s"] if r["stray"] else [])
                     + ([f"{r['stray_ability']}a"] if r["stray_ability"] else []))
        rows.append({**r, "own": "✓" if r["short"] == 0 else f"{r['short']}✗",
                     "legal": "✓" if r["illegal"] == 0 else f"{r['illegal']}✗",
                     "cast": cast_cell})

    if args.flagged:
        rows = [r for r in rows if r["verdict"] != "ok"]
    if getattr(args, "by_tier", False):
        # Sort by competitive tier (S→D, ungraded last), then id.
        rows.sort(key=lambda r: (TIER_ORDER.get(r["tier"], 5), len(r["id"]), r["id"]))
    else:
        rows.sort(key=lambda r: (AUDIT_ORDER[r["verdict"]], len(r["id"]), r["id"]))

    print(f"Deck roster audit — {len(scored)} decks "
          f"(offline triage; full-tune only the flagged ones)\n")
    name_w = min(32, max(4, max((len(r["name"]) for r in rows), default=4)))
    hdr = (f"  {'ID':<4}  {'Deck':<{name_w}}  {'Tier':<4}  {'Sz':>3}  {'Own':<4}  {'Legal':<5}  "
           f"{'Cast':<7}  {'Int':>3}  {'Thm':>3}  Action")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for r in rows:
        label = {"TUNE": "★ TUNE", "craft": "craft", "review": "review", "ok": "ok"}[r["verdict"]]
        action = label + (f" — {r['why']}" if r["why"] else "")
        print(f"  {r['id']:<4}  {r['name'][:name_w]:<{name_w}}  {(r['tier'] or '·'):<4}  "
              f"{r['sz']:>3}  {r['own']:<4}  {r['legal']:<5}  {r['cast']:<7}  {r['int']:>3}  "
              f"{r['thm']:>3}  {action}")

    print(f"\nLegend: Tier S→D competitive/win-capability (· = ungraded) · "
          f"Own/Legal ✓ clean · Cast Nu=uncastable Ns=identity stray "
          f"Na=of those, off-color ABILITY (the rest are hybrids you pay on-color) · "
          f"Int=removal+sweeper+counter · Thm=central themes")
    print(f"Summary: {len(tune)} to tune · {len(craft)} to craft · "
          f"{len(review)} to review · {len(scored) - len(tune) - len(craft) - len(review)} ok")
    if tune:
        print(f"\nFull-tune candidates (hard flags): {', '.join(tune)}")
        print("  → run: python3 scripts/deck.py text <id>  then  /tune-deck <id>")
    if review:
        print(f"Worth a look (soft flags): {', '.join(review)}")
    return 0


def _weakest_cut(dmeta, cards, cardmeta, carddata, add_is_fixer=False):
    """The single most-cuttable nonland card in a deck (lowest theme-fit + role
    score), skipping `#: protect:` cards — a hint for suggest-homes. Run
    `deck.py cuts` for the full, oracle-text-graded shortlist.

    `add_is_fixer` is the CARD BEING ADDED, and it is here because this hint used to be
    computed BLIND to it: the caller asked only "what is this deck's weakest card", so
    nothing stopped it proposing a cut that does the very job motivating the add. Mana
    fixing is where that bites, because the keep-score is theme-fit + role credit and
    NEITHER has a fixing term — a rainbow fixer carries almost no synergy tags and no
    classified role, so it sorts to the TOP of the cut list in exactly the multi-colour
    decks that need it. `suggest-homes "Guy in the Chair"` proposed cutting Prismatic
    Undercurrents from deck 13 and Bloom Tender from deck 17 — each strictly better at
    fixing than the card being added. So when the add is a fixer, incumbent fixers are
    not cut candidates: swapping fixing for fixing is a wash at best, and the ranking
    cannot see which one is better.

    Deliberately NOT a general "same role" exclusion. Roles the classifier DOES score
    (removal, card advantage) already reach the keep-score through `_role_credit`, so
    excluding those too would double-count. Fixing is the resource the score is blind
    to, which is precisely why it needs the guard.

    Scored by the SHARED `cut_keep_score` — the same formula `deck.py cuts` prints and
    `tier --to` pairs its adds against. It used to carry its own three-term copy (theme
    fit over central themes + unsaturated role credit) and so inherited none of the
    co-signals: no power, no distinctiveness, no multiplier, no tribal or signature
    term, and a role credit blind to how much of that role the deck already runs. The
    two answers to "this deck's most-cuttable card" disagreed on **36 of 64 decks**.
    Ties break on the card name, matching `rank_cut_candidates`' sort — a min-scan that
    keeps the first-seen winner would otherwise resolve a tie by deck-file order and
    disagree with the printed ranking on exactly the cards that scored equal.
    """
    protected = _protected(dmeta)
    sctx = cut_scoring_context(dmeta, cards, cardmeta, carddata)
    rar = load_rarities()
    best = None
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS or nl in protected:
            continue
        cd = carddata.get(nl)
        tline = (cd["type"] if cd else "") or ""
        if "Land" in _primary_type(tline):
            continue
        tags = cardmeta.get(nl, {}).get("synergies", [])
        ctext = cd["text"] if cd else ""
        if add_is_fixer and _is_color_fixer(tags, ctext):
            continue
        keep, _ = cut_keep_score(sctx, tline, ctext, tags,
                                 rarity=rar.get(nl, ""), qty=q)
        key = (keep, n.lower())
        if best is None or key < best[0]:
            best = (key, n)
    return best[1] if best else None


_FIXER_TAGS = {"ramp", "mana"}
# A fixer is recognised from its TEXT, not from a synergy tag. The tag gate this
# replaced (`ctags & {ramp, mana}` AND a loose cue) depended on `tag_synergies`'
# hand-kept keyword map, so a fixer whose mechanic is UNINDEXED scored as a non-fixer:
# Bloom Tender ("{T}: For each color among permanents you control, add one mana of that
# color") and Prismatic Undercurrents (fetch X basics, X = your colour count) both key
# off **Vivid**, which sits in `keyword_baseline.txt` as acknowledged-but-unmapped, so
# they tag `vivid` — matching nothing — and read is_fixer=False. Meanwhile Guy in the
# Chair ({2}{G}, taps for one any-colour) carried a `mana` tag and read True, took the
# full boost and the automatic KEY, and `suggest-homes` proposed cutting each deck's
# BETTER fixer to make room for it (decks 13 and 17). Reading the text directly makes
# the predicate independent of which keywords happen to be indexed this cycle.
#
# BROAD = fixes several colours at once, or grants colour-agnostic permission. This is
# the Overlord/Bloom Tender/Vizier shape and it is worth full value at any mana cost.
_FIXER_BROAD_RE = re.compile(
    # every/all/each basic land type (Overlord's token, a Triome-maker)
    r"(?:every|all|each) basic land type"
    # colour-agnostic SPENDING permission (Vizier: "spend mana of any type to cast")
    r"|spend .{0,40}?mana (?:of any (?:color|type)|as though it were mana of any)"
    r"|as though it were mana of any (?:color|type)"
    # a MASS grant — every creature/land you control becomes a rainbow source
    # (Enduring Vitality, Great Divide Guide). One card, many sources.
    r"|you control ha(?:ve|s)[^.]{0,80}?add (?:one )?mana of any"
    # production that SCALES with your colour count (Bloom Tender's Vivid)
    r"|for each color among [^.]{0,60}?add (?:one|that much|x)? ?mana"
    r"|add (?:one|two|three|x) mana of each color"
    # a fetch whose count scales with your colour count (Prismatic Undercurrents)
    r"|search .{0,60}?for (?:up to )?x basic land",
    re.I)
# SINGLE = you choose ONE colour per activation (a Command Tower, a rainbow dork, Gilded
# Lotus' three-of-one-colour). Real fixing, but its worth is bounded by what it costs —
# see `_fixer_rate`. `any one color` and Chrome Mox's `any of the exiled card's colors`
# are the same class as `any color`; the first sweep omitted both and dropped 38 genuine
# fixers, which only the roster-wide before/after diff surfaced.
_FIXER_SINGLE_RE = re.compile(
    r"add (?:\w+ )?mana of any(?: one)? (?:color|type)"
    r"|mana of any of [^.]{0,50}?colors",
    re.I)
# Rate floor/ceiling for a SINGLE-source fixer: a 1–2 mana rainbow source is full value,
# and each mana past that discounts it. `Guy in the Chair` at MV 3 lands at 0.67, below
# `_FIXER_KEY_RATE`, so it stays a role-player instead of being auto-promoted to KEY.
_FIXER_SINGLE_PAR = 2.0
_FIXER_RATE_FLOOR = 0.25
# A fixer must be at least this efficient before the colour-count overlay promotes it
# straight to KEY. Broad fixers rate 1.0 and always clear it.
_FIXER_KEY_RATE = 0.7


# DOUBLERS — a card whose value scales with HOW MUCH of a thing the deck already does.
# Theme overlap sees "this card mentions tokens" and stops there, so Exalted Sunborn ("if
# one or more tokens would be created under your control, twice that many are created
# instead") scored deck 45 at fit 52 over Knight's Edge at 46 — when 45 fields SIX
# token-makers and Knight's Edge fields FOURTEEN. The tag model cannot see magnitude, only
# membership, and a doubler is worth exactly the magnitude.
#
# A tag would NOT have fixed this: the card already shared `tokens` with those decks and
# still lost the ranking. What is missing is a deck-side COUNT, so this is a scoring term
# on the same bounded pattern as `_fixer_boost` (whose value likewise scales with a
# deck-side quantity, the colour count).
_DOUBLER_AXES = {
    # axis -> (what the DOUBLER's text looks like, what a deck card that FEEDS it looks like)
    "tokens": (
        re.compile(r"if one or more[^.]{0,80}?tokens? would be created[^.]{0,80}?"
                   r"(?:twice that many|instead)", re.I),
        re.compile(r"creates? (?:a|an|two|three|four|\w+) [^.]{0,60}?token", re.I)),
    "counters": (
        re.compile(r"if one or more[^.]{0,80}?counters? would be put[^.]{0,80}?"
                   r"(?:twice that many|instead)", re.I),
        re.compile(r"put (?:a|an|two|three|\w+) \+1/\+1 counter", re.I)),
    "triggers": (
        re.compile(r"triggers? an additional time|that ability triggers? one more time", re.I),
        re.compile(r"\bwhenever\b|\bwhen .{0,40}?enters\b", re.I)),
    # LIFEGAIN was the missing axis, and The Wind Crystal is why. A card that doubles every
    # lifegain is a multiplier exactly the way a token or counter doubler is, but the axis
    # list stopped at three and so it read `None` — no doubler support, no fit bump, and
    # `cuts` ranked it as an ordinary artifact. Requires the literal "twice that much"
    # rather than reusing the other axes' looser `instead` alternative, because a
    # REPLACEMENT that is not a doubling is templated identically: Angel of Vitality's
    # "you gain that much life plus 1 instead" is +1, not ×2, and would qualify on
    # `instead` alone.
    "lifegain": (
        re.compile(r"if you would gain life[^.]{0,60}?twice that much", re.I),
        re.compile(r"\bgains? \d+ life|\bgain that much life|\blifelink\b", re.I)),
}
_DOUBLER_PER_SOURCE = 1.2   # fit points per feeding card
# Ceiling chosen as a SAFETY rail, not an operating point: real decks feed an axis with
# 4-15 cards, so at 1.2/source the term is effectively linear across that whole range and
# the cap only bites past 15. Capping lower (12) made it saturate at 10 and stop
# distinguishing Knight's Edge's 14 token-makers from Avengers' 10 — which is the exact
# discrimination this term exists to provide. Comparable in size to `_fixer_boost` (max 20).
_DOUBLER_CAP = 18
_DOUBLER_MIN_SOURCES = 5    # below this the deck does not do the thing enough to matter
_DOUBLER_KEY_SOURCES = 10   # at this density the doubler IS a key card (mirrors the
                            # fixer overlay promoting at 4+ colours)


def doubler_axis(text):
    """Which quantity this card DOUBLES ('tokens' / 'counters' / 'triggers'), or None."""
    if not text:
        return None
    for axis, (dbl, _feed) in _DOUBLER_AXES.items():
        if dbl.search(text):
            return axis
    return None


# Some doublers only apply to a SUBSET of the axis — Delney, Streetwise Lookout doubles
# triggers of "creatures you control with power 2 or less". Counting every trigger in the
# deck roughly DOUBLED the real support (deck 24 read 24 sources against a true 4, enough
# to flip it over the KEY threshold on its own), so the restriction is parsed off the
# doubler's own text rather than assumed away.
_DOUBLER_POWER_RE = re.compile(r"power (\d+) or less", re.I)


def doubler_restriction(text):
    """Max creature power a doubler's effect applies to, or None for unrestricted."""
    m = _DOUBLER_POWER_RE.search(text or "")
    return int(m.group(1)) if m else None


def doubler_support(axis, cards, carddata, max_power=None):
    """How many copies in the deck FEED that axis — the magnitude a doubler multiplies.

    `max_power` restricts the count to creatures at or below that printed power, for a
    doubler whose text is scoped that way. Printed power is the correct read (a creature
    that GROWS later still wasn't small when the doubler was evaluated), and
    `lib.card_power` returns None for `*`/`X` rather than inventing a number — those are
    excluded from a restricted count rather than assumed to qualify.
    """
    feed = _DOUBLER_AXES.get(axis, (None, None))[1]
    if not feed:
        return 0
    n = 0
    for q, name, _s, _c in cards:
        nl = name.lower()
        if nl in BASICS:
            continue
        cd = carddata.get(nl) or carddata.get(nl.split(" // ")[0])
        if not cd or not feed.search(cd.get("text") or ""):
            continue
        if max_power is not None:
            if "Creature" not in (cd.get("type") or ""):
                continue
            p = card_power(cd.get("power"))
            if p is None or p > max_power:
                continue
        n += q
    return n


def doubler_boost(support, per=_DOUBLER_PER_SOURCE, cap=_DOUBLER_CAP,
                  floor=_DOUBLER_MIN_SOURCES):
    """Bounded fit bump for a doubler, growing with the deck's density of what it doubles.

    Zero below `floor` (a deck making three tokens does not want a token doubler), linear
    after, hard-capped at `cap` so it can reorder decks that are otherwise close without
    ever overriding a genuine theme match — the same contract as `_fixer_boost`.
    """
    if support < floor:
        return 0.0
    return min(support * per, float(cap))


def _fixer_boost(ncolors, per_color=4, cap=5, rate=1.0):
    """Bounded fit bump for a rainbow fixer in an `ncolors`-color deck — grows with
    the color count (a fixer earns more in a 5-color deck than a 3-color one) but is
    CAPPED (at `cap` colors) so it nudges ordering among fixer-eligible decks without
    ever dwarfing a genuine theme match. Returns 0 below 3 colors (mono/two-color
    decks don't need the fixing).

    `rate` (0..1, from `_fixer_rate`) scales the bump by how much fixing the card
    actually BUYS. Without it the term read only the deck's colour count, so Overlord
    of the Hauntwoods (a permanent land token with every basic land type) and Guy in
    the Chair ({2}{G}, taps for exactly one) collected the identical +16 and the
    identical KEY — the term could not tell a manabase fix from a mediocre dork.
    """
    if ncolors < 3:
        return 0
    return min(ncolors, cap) * per_color * rate


def _fixer_rate(text, mv=None):
    """How much fixing a rainbow fixer actually buys, as a 0..1 multiplier on the
    colour-count boost. BROAD fixers (several colours at once, or colour-agnostic
    spending permission) rate 1.0 at any cost — that value does not decay with mana.
    A SINGLE any-colour source rates by cost: full value at `_FIXER_SINGLE_PAR` mana
    or less, discounted above it, floored at `_FIXER_RATE_FLOOR` so an expensive
    rainbow source is still recognised as fixing rather than dropping to nothing.
    Returns 0.0 for a non-fixer. Unknown MV is treated as par (no penalty), since
    guessing against missing data should not manufacture a demotion.

    Parenthetical REMINDER text is stripped first, and that single line is what keeps
    this from saturating: a Treasure token's reminder is literally `(It's an artifact
    with "{T}, Sacrifice this token: Add one mana of any color.")`, so without the strip
    every Treasure-maker in the pool reads as a rainbow fixer — 150-odd cards, and a
    signal that fires on everything carries nothing. A one-shot sacrificial token is
    ramp, not a manabase. Chromatic Sphere states the same ability as REAL text rather
    than a reminder, so it still qualifies, which is the right split."""
    t = _REMINDER_RE.sub(" ", text or "")
    if _FIXER_BROAD_RE.search(t):
        return 1.0
    if not _FIXER_SINGLE_RE.search(t):
        return 0.0
    if mv is None or mv <= _FIXER_SINGLE_PAR:
        return 1.0
    return max(_FIXER_RATE_FLOOR, _FIXER_SINGLE_PAR / float(mv))


def _is_color_fixer(ctags, text):
    """True when a card's value is multi-color mana FIXING whose worth SCALES with a
    deck's color count — a rainbow fixer (Overlord's every-basic-land-type token,
    Vizier's 'spend mana as though any color', a Triome-maker). A theme-overlap model
    can't see fixing (it isn't a 'theme'), and its value is proportional to how many
    colors the target deck must cast — so `suggest-homes` under-rates it in exactly
    the 3+-color decks that want it most (the Overlord → decks 17/21a miss).

    Read from TEXT alone, in explicit MANA/land-type context. `ctags` is accepted and
    ignored: the previous tag gate (`ramp`/`mana` + a loose "any color" substring) made
    the predicate a hostage of `tag_synergies`' keyword map, and every fixer built on an
    UNINDEXED mechanic read False — see `_FIXER_BROAD_RE`. Requiring mana context is
    what keeps the loose cue honest without the tag: "protection from the color of your
    choice" says "color of your choice" and is not fixing, and a mono-color ramp spell
    ('add {G}{G}') never matches either pattern."""
    return bool(_fixer_rate(text))


def _deck_central_weights(meta, cards, cardmeta):
    """A deck's CENTRAL themes as a {theme: copies} weight vector — the same `_central_themes`
    set the roster tools share, kept weighted so a dominant theme counts for more."""
    tw = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = cardmeta.get(n.lower())
        if m:
            for t in m["synergies"]:
                tw[t] = tw.get(t, 0) + q
    return {t: tw[t] for t in _central_themes(tw)}


_SIM_GENERIC_DAMP = 0.35   # generic themes are shared by nearly every value deck, so they
                           # signal little about IDENTITY overlap — damp them in the cosine.


def _theme_is_generic(t):
    return t.lower() in GENERIC_THEMES or t.lower() in _GENERIC_TRIBES


def _strong_signature_themes(meta, cards, cardmeta, min_cards=2):
    """Signature themes carried by ≥`min_cards` of the deck's `#: protect:` cards — a real
    BUILD-AROUND spine (a counters deck that protects several counter-doublers), NOT a generic
    theme incidental to one protected bomb. Stricter than `_signature_themes` (which unions
    ALL protected cards' tags): used by `similar`'s generic-rescue so a lone protected card's
    card-draw/etb tag can't promote a diffuse value deck's generic overlap into a false
    identity match (a counters spine spans multiple protected cards; Finale's card-draw doesn't).

    A GENERIC theme must additionally clear HALF the protect list, and that proportional bar
    is the whole point of this function rather than a refinement of it. The signature exists
    for one job — rescuing a theme that idf calls generic when it is genuinely the deck's
    spine — so a SPECIFIC theme never needed rescuing and keeps the flat ≥2 bar. But ≥2 was
    tuned against a 3-to-5-card protect list, and it does not survive a longer one: at 7
    protected cards ≥2 is 29% of them, and at 14 it is 14%. Measured on the roster, that let
    26 of 33 decks carry a signature that was ≥50% GENERIC — deck 46 rescued `Human`,
    `combat`, `flying` and five more off 14 protected cards, and deck 51 rescued `card draw`,
    `graveyard`, `mana` and `tokens` off 7. Since `fit_strength` is right to mint KEY from any
    signature theme it is handed (see check_suggest anchor 11b — the strictness must live in
    the caller, not the function), those false spines propagated straight into `screen`'s KEY
    label, which fired on 66% of a 111-card pile and so carried almost no information. The
    proportional bar drops 51 signature themes across 18 decks and leaves every genuine spine
    standing (deck 49 keeps `Dragon`, deck 47 keeps `affinity`/`artifacts`). Same shape as
    G-09: a keep-boost that applies to nearly everything is a constant, not a signal."""
    prot = _protected(meta)
    if not prot:
        return frozenset()
    counts = {}
    for q, n, s, c in cards:
        if n.lower() in prot:
            m = cardmeta.get(n.lower())
            if m:
                for t in set(m["synergies"]):
                    counts[t] = counts.get(t, 0) + 1
    generic_bar = max(min_cards, math.ceil(len(prot) / 2))
    return frozenset(t for t, k in counts.items()
                     if k >= (generic_bar if _theme_is_generic(t) else min_cards))


def _sim_specific(t, keep):
    """Is theme `t` SPECIFIC for a similarity comparison? Non-generic themes always are; a
    generic-by-idf theme counts as specific when it's a deck's `#: protect:` SIGNATURE
    (in `keep`) — so a counters-doubler deck whose spine IS counters reads counters as an
    identity theme, not generic value overlap (the same signature rescue `fit_strength` uses)."""
    return (not _theme_is_generic(t)) or t in keep


def _sim_weights(vec, specific_only=False, keep=frozenset()):
    """Down-weight GENERIC themes/tribes in a central-theme vector for the similarity cosine:
    two decks sharing a SPECIFIC theme (a tribe, a build-around mechanic) are far more alike
    than two that merely both run card-draw/etb — otherwise every diffuse value deck reads as
    a near-duplicate of every other. `keep` (the pair's signature themes) rescues a generic
    theme that IS a deck's spine. `specific_only` DROPS the remaining generics entirely (a
    pure-identity lens), so a diffuse good-stuff deck honestly reads as sharing nothing specific."""
    out = {}
    for t, w in vec.items():
        spec = _sim_specific(t, keep)
        if not spec and specific_only:
            continue
        out[t] = w * (1.0 if spec else _SIM_GENERIC_DAMP)
    return out


def _theme_cosine(a, b, specific_only=False, keep=frozenset()):
    """Cosine similarity of two {theme: weight} vectors (generic-damped via `_sim_weights`,
    or generic-EXCLUDED when specific_only; `keep` = the pair's signature themes). A shared
    SPECIFIC dominant theme drives the score far more than an incidental etb overlap — the
    'do these two decks do the same thing' signal, not 'are they both value decks'."""
    a, b = _sim_weights(a, specific_only, keep), _sim_weights(b, specific_only, keep)
    shared = set(a) & set(b)
    if not shared:
        return 0.0
    dot = sum(a[t] * b[t] for t in shared)
    na = math.sqrt(sum(w * w for w in a.values()))
    nb = math.sqrt(sum(w * w for w in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def cmd_similar(args):
    """Rank the decks most SIMILAR to <id> by shared central-theme overlap — the roster
    'is this deck distinct, or does it duplicate an existing one?' check (the question a
    from-scratch build always raises). Cosine over the central-theme WEIGHT vectors, so a
    shared dominant theme dominates the score; a color-overlap % is shown alongside."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    cardmeta, mana = load_card_meta(), load_mana()
    spec_only = getattr(args, "specific_only", False)
    meta, cards = parse_deck_file(d["path"])
    aw = _deck_central_weights(meta, cards, cardmeta)
    acols = _declared_colors(meta) or _deck_castable_colors(meta, cards, mana)
    if not aw:
        print(f"Deck {d['id']} has no central themes to compare (too few tagged cards).")
        return 0
    sig_a = _strong_signature_themes(meta, cards, cardmeta)   # multi-card spine — rescues a
    a_specific = [t for t in aw if _sim_specific(t, sig_a)]   # generic theme that's the identity
    if spec_only and not a_specific:
        print(f"Deck {d['id']}: {d.get('name') or d['id']} has NO specific central themes — "
              "it's a diffuse good-stuff/value deck, so it's distinct BY IDENTITY from every\n"
              "deck (nothing specific to duplicate). Drop --specific-only for a value-overlap view.")
        return 0
    carddata = load_card_data()
    anames = {n for _q, n, _s, _c in cards if n.lower() not in BASICS
              and "Land" not in _primary_type((carddata.get(n.lower()) or {}).get("type") or "")}
    rows = []
    for dd in discover_decks():
        if dd["id"].lower() == d["id"].lower():
            continue
        m2, c2 = parse_deck_file(dd["path"])
        bw = _deck_central_weights(m2, c2, cardmeta)
        keep = sig_a | _strong_signature_themes(m2, c2, cardmeta)   # EITHER deck's spine counts
        sim = _theme_cosine(aw, bw, spec_only, keep)
        if sim <= 0:
            continue
        bcols = _declared_colors(m2) or _deck_castable_colors(m2, c2, mana)
        colj = len(acols & bcols) / len(acols | bcols) if (acols | bcols) else 0.0
        shared = sorted(set(aw) & set(bw), key=lambda t: -(min(aw[t], bw[t])))
        spec = [t for t in shared if _sim_specific(t, keep)]
        # CARD overlap, the thing the theme cosine cannot see. This model compares
        # {theme: weight} vectors, so two decks can read 84% similar while sharing five
        # card names — four of them lands. Without this column the score reads as "these
        # are the same deck" when it often means "these are both Orzhov value decks".
        # Lands are excluded: a shared manabase is not a shared identity.
        bnames = {n for _q, n, _s, _c in c2 if n.lower() not in BASICS
                  and "Land" not in _primary_type((carddata.get(n.lower()) or {}).get("type") or "")}
        both = anames & bnames
        rows.append((sim, colj, dd["id"], dd.get("name") or dd["id"], shared, spec,
                     len(both), sorted(both)))
    # Theme cosine stays the PRIMARY order — it answers "does this duplicate an
    # identity", which is the question. But it is not the same question as "which deck do
    # I share the most cards with", and the two can rank in opposite orders: deck 52a
    # reads 96% against deck 6 (4 shared cards, 33% colours) and 81% against its own
    # parent 52 (13 shared cards, 100% colours). A reader acts on row order, so the
    # card-overlap answer is stated explicitly below rather than left in a column.
    rows.sort(key=lambda r: (-r[0], -r[1], r[2]))
    limit = getattr(args, "limit", 8) or 8
    lens = "SPECIFIC-theme overlap only" if spec_only else "central-theme overlap"
    print(f"Deck {d['id']}: {d.get('name') or d['id']} — most similar decks ({lens})\n"
          f"Your colors: {'/'.join(sorted(acols)) or '—'}  ·  top themes: "
          f"{', '.join(f'{t}({aw[t]})' for t in sorted(aw, key=lambda t: -aw[t])[:6])}\n")
    print(f"  {'sim':>4} {'col':>4} {'cards':>5}  {'deck':6} shared themes (✦ = a SPECIFIC identity theme)")
    print("  " + "-" * 84)
    for sim, colj, did, name, shared, spec, ncards, cardnames in rows[:limit]:
        # A shared SPECIFIC theme = a real identity match ⇒ ⚠ overlap. High sim on GENERIC
        # themes only = both are value decks, not a duplicate ⇒ the softer '· value overlap'.
        if sim >= 0.60 and spec:
            flag = " ⚠ overlap"
        elif sim >= 0.60:
            flag = " · value overlap"
        elif sim >= 0.30:
            flag = ""
        else:
            flag = " · distinct"
        specset = set(spec)
        disp = ", ".join((("✦" + t) if t in specset else t) for t in shared[:5])
        print(f"  {sim*100:>3.0f}% {colj*100:>3.0f}% {ncards:>5}  {did:6} {disp}{flag}")
    if getattr(args, "full", False):
        print("\n  Shared nonland cards — the concrete evidence the cosine cannot show:")
        for sim, colj, did, name, shared, spec, ncards, cardnames in rows[:limit]:
            print(f"    {did:6} ({ncards}) {', '.join(cardnames) if cardnames else '—'}")
    top = rows[0] if rows else None
    if top and top[0] >= 0.60 and top[5]:
        # Temper the warning with the card count: a high cosine on few shared CARDS is a
        # both-are-value-decks signal, not a duplicate.
        tail = (f" But they share only {top[6]} nonland card(s), so the overlap is in what "
                f"the decks TAG as, not what they play — grade the win-cons from "
                f"`deck.py text`." if top[6] <= 5 else
                f" They also share {top[6]} nonland cards — check that list first.")
        print(f"\n⚠ Closest is #{top[2]} {top[3]} at {top[0]*100:.0f}% and shares a SPECIFIC theme "
              f"({', '.join(top[5][:3])}).{tail}")
    elif top and top[0] >= 0.60:
        print(f"\nClosest is #{top[2]} {top[3]} at {top[0]*100:.0f}%, but only on GENERIC value "
              "themes — a loose 'both value decks' overlap, not a duplicate identity.")
    elif top:
        print(f"\nClosest is #{top[2]} {top[3]} at {top[0]*100:.0f}% — comfortably distinct.")
    # The deck you share the most CARDS with, when the theme ranking does not put it first.
    by_cards = sorted(rows, key=lambda r: (-r[6], -r[1], r[2]))
    if by_cards and by_cards[0][6] and by_cards[0][2] != rows[0][2]:
        top = by_cards[0]
        rank = next(i for i, r in enumerate(rows, 1) if r[2] == top[2])
        print(f"  ▸ Most shared CARDS: deck {top[2]} ({top[6]} nonland card(s), "
              f"{top[1] * 100:.0f}% colours) — it ranks #{rank} by theme. Theme similarity "
              "and card overlap are different questions; some overlap between decks is "
              "fine, so read this as 'where the lists actually meet'.\n")
    print("\n✦ marks a SPECIFIC (identity) theme; plain = generic value overlap. A SHORTLIST — "
          "grade the DOMINANT theme + win-con from `deck.py text`, not the number. "
          "`--specific-only` scores identity themes alone.")
    return 0


_TRAILING_NOTE_RE = re.compile(r"\s*\([^()]*\)\s*$")
_SQUASH_RE = re.compile(r"[^a-z0-9]+")


def _name_query(raw):
    """Normalize a HAND-TYPED candidate name: drop trailing parenthetical notes and collapse
    whitespace. A pile is written by a person, so `Master Pakku (needs Lessons)` and
    `Bruce Banner (mostly for its front face)` name the same cards as the bare strings."""
    q = " ".join(str(raw).split())
    prev = None
    while prev != q:                       # `Foo (a) (b)` — strip every trailing note
        prev = q
        q = _TRAILING_NOTE_RE.sub("", q).strip()
    return q


def _squash(s):
    """Comparison key with every non-alphanumeric character removed, so a hand-typed name
    matches the printed one across the punctuation people drop: `Ramos Dragon Engine` ->
    `Ramos, Dragon Engine`, `Gran Gran` -> `Gran-Gran`, `Flotsam//Jetsam` ->
    `Flotsam // Jetsam`. Deliberately NOT a typo-corrector — `Impostoer Syndrome` still
    fails to resolve, because guessing at a misspelling silently grades the wrong card,
    which is worse than reporting the name back."""
    return _SQUASH_RE.sub("", s.lower())


def _squash_index(table, display):
    """squashed-name -> {key: display}, built ONCE per surface. Screening a 111-card pile
    would otherwise re-scan every pool key per query."""
    out = {}
    for k in table:
        for variant in (k, k.split(" // ")[0]):
            out.setdefault(_squash(variant), {})[k] = display(k)
    return out


def _resolve_card_name(query, table, display, squashed):
    """Resolve a hand-typed card name against `table` (a dict keyed by lowercase name).
    Returns `(key, candidates)` — `key` on a unique match, `candidates` (sorted display
    names) when genuinely ambiguous, `(None, [])` when nothing matched.

    Order: exact -> DFC front -> squashed punctuation -> unique substring.

    THE SQUASH STEP IS THE LOAD-BEARING ONE, and it exists because a real pasted pile
    concentrates its interesting cards in exactly the names it recovers. Screening one
    111-card pile left 22 names unresolved, and they were overwhelmingly `Name, Epithet`
    legendary creatures typed without the comma — so the triage tool silently handed back
    the fifth of the pile that most needed it, and those cards got graded by hand instead.
    Ambiguity is still reported rather than guessed at (G-47: a shortlist that guesses is
    worse than one that admits it doesn't know)."""
    ql = _name_query(query).lower()
    if ql in table:
        return ql, []
    front = ql.split(" // ")[0]
    if front in table:
        return front, []
    hits = squashed.get(_squash(ql)) or {}
    names = set(hits.values())
    if len(names) == 1:
        return sorted(hits, key=len)[0], []
    if len(names) > 1:
        return None, sorted(names)
    subs = sorted((k for k in table if ql in k), key=len)
    names = {display(k) for k in subs}
    if len(names) == 1:
        return subs[0], []
    if len(names) > 1:
        return None, sorted(names)
    return None, []


def _candidate_castability(cost, ident, declared):
    """`(castable, note)` for a CANDIDATE card against a deck's declared colors, read from
    the PRINTED COST rather than from color identity.

    Identity and cost disagree in precisely the cases a pile is full of: `{1}{U/R}` is
    payable with Islands alone, `{6}` is payable anywhere, and BOTH read as off-color in
    the `Color(s)` column. Triaging a 111-card pile on that column mis-sorted nine cards,
    eight of which were castable (G-58, bulk-triage variant). Mirrors `_castability_lint`
    so the two surfaces cannot drift: only a TRUE multicolor hybrid constrains
    castability; a monocolor (`{2/W}`) or Phyrexian (`{W/P}`) hybrid never does."""
    strict, hybrid = parse_pips(cost or "")
    off_strict = sorted(set(strict) - declared)
    bad_hybrid = sorted({x for h in hybrid
                         if len(h) >= 2 and not (h & declared) for x in h})
    if off_strict or bad_hybrid:
        return False, "⚠ NOT castable — needs " + "/".join(sorted(set(off_strict + bad_hybrid)))
    stray = sorted(ident - declared)
    if not stray:
        return True, ""
    if not cost:
        return True, ("identity has " + "/".join(stray)
                      + " (cost unknown — run `deck.py mana` to tell hybrid from ability)")
    hybrid_colors = set().union(*hybrid) if hybrid else set()
    if set(stray) <= hybrid_colors:
        return True, "identity has " + "/".join(stray) + " (hybrid — paid on-color)"
    return True, "identity has " + "/".join(stray) + " (off-color ability — still castable)"


def _printing_index():
    """name_lower (full AND DFC front) -> (display, set_code, collector). The OWNED printing
    (card-library.csv) wins over the pool's representative printing, so a resolved line
    matches what you actually have. Used by `deck.py resolve`."""
    idx = {}
    for path in (POOL_CSV, DEFAULT_CSV):        # library LAST so it overrides the pool
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                disp = (r.get("Card Name") or "").strip()
                nl = disp.lower()
                if not nl:
                    continue
                info = (disp, (r.get("Set Code") or "").strip(), (r.get("Collector #") or "").strip())
                idx[nl] = info
                idx.setdefault(nl.split(" // ")[0], info)   # DFC front fallback (don't clobber a full name)
    return idx


@_file_memo("DEFAULT_CSV", "POOL_CSV")
def known_printings():
    """(by_name, set_codes) — every (set, collector) this repo knows, per card.

      by_name    : name_lower -> {(set_lower, collector_lower), …}
      set_codes  : {set_lower, …} across the whole pool + library

    The deck-line fields `(SET) COLLECTOR#` were validated by NOTHING. `1 Eaten Alive
    (ZZZ) 172` — a set code that does not exist — passed `legal`, passed `check` (which
    reported it as OWNED, since ownership joins on the NAME), passed `preflight` READY
    and passed `check_all` "All invariants hold". INV-04 only asserts a line PARSES, so a
    deck file could be integrity-clean and un-importable at the same time. That is not
    hypothetical: deck 52 was written with `(FDN) 610` for a card whose collector number
    is 172, and nothing complained.

    Front faces are aliased in a SECOND pass so a `Front // Back` row cannot shadow a
    real card named `Front` (G-63) — and only when the front name has no rows of its own.
    """
    by_name, set_codes, real = {}, set(), set()
    for path in (POOL_CSV, DEFAULT_CSV):
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                nl = (r.get("Card Name") or "").strip().lower()
                if not nl:
                    continue
                sc = (r.get("Set Code") or "").strip().lower()
                pr = (sc, (r.get("Collector #") or "").strip().lower())
                by_name.setdefault(nl, set()).add(pr)
                real.add(nl)
                if sc:
                    set_codes.add(sc)
    for nl in list(by_name):
        front = nl.split(" // ")[0]
        if front != nl and front not in real:
            by_name.setdefault(front, set()).update(by_name[nl])
    return by_name, set_codes


def printing_problems(cards):
    """(bad_set, unverified) for a deck's card lines.

      bad_set     : [(name, set, collector)] — the set code appears in NO card anywhere,
                    so the line is certainly wrong. HARD: zero across the whole roster.
      unverified  : [(name, set, collector, known)] — the name and set code are both
                    real, but this exact printing is not one we hold. SOFT, because the
                    pool keys ONE printing per card by construction, so a legitimate
                    alternate printing lands here too.

    BASIC LANDS ARE EXEMPT. Arena prints several arts per set (Swamp MSH 291 and 292 are
    both real) while the pool carries one, so a hard rule would have failed 61 of 78 deck
    files on basics alone — measured before choosing the split. A line with no printing
    stated at all is also skipped: that is a legal, if under-specified, deck line."""
    by_name, set_codes = known_printings()
    bad_set, unverified = [], []
    for _q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS or nl.startswith("snow-covered "):
            continue
        if not s and not c:
            continue
        if s and s.lower() not in set_codes:
            bad_set.append((n, s, c))
            continue
        known = by_name.get(nl) or by_name.get(nl.split(" // ")[0])
        if not known:
            continue                      # unknown card entirely — reported elsewhere
        if (s.lower(), c.lower()) not in known:
            unverified.append((n, s, c, sorted(known)[:3]))
    return bad_set, unverified


def _legality_of(names):
    """name_lower -> set(formats) from the pool, for a legality warning on any surface
    that hands back card names. Empty dict if the pool has no Legalities column."""
    out = {}
    if not os.path.exists(POOL_CSV):
        return out
    want = {n.lower() for n in names} | {n.split(" // ")[0].lower() for n in names}
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            if n in want or n.split(" // ")[0] in want:
                legs = {x.strip() for x in (r.get("Legalities") or "").split(";") if x.strip()}
                out[n] = legs
                out.setdefault(n.split(" // ")[0], legs)
    return out


# A card's value can lie ENTIRELY in its relationship to a list you already have, and
# every scoring model here grades a card on its own text. Two consequences drove this:
#
#  1. A pile graded ONCE against an early plan keeps those verdicts after the plan
#     changes. Deck 46's 76-card pile was screened against a "one enormous body" plan;
#     when the plan became "several growing lifelink bodies", only the cards the user
#     re-raised were re-graded, and the rest carried stale reasoning forward. Shrike
#     Force, Linden, The Wind Crystal and Prayer of Binding all sat in that bucket.
#  2. Nothing asked whether a candidate is a STRICT UPGRADE of a card already in the
#     deck. Prayer of Binding is Liminal Hold plus Flash — identical cost, identical
#     text — and Liminal Hold was in the 60 while Prayer of Binding sat on the excluded
#     list with a note comparing it to a different card entirely.
#
# `screen` answers both by re-scoring a whole candidate list against the deck AS IT IS
# NOW, so the answer cannot be stale, and by naming the incumbents each candidate beats.
_UPGRADE_SELF_RE = re.compile(r"\bthis (?:creature|permanent|enchantment|artifact|land|spell|card)\b", re.I)


def _upgrade_clauses(name, text):
    """A card's text as a set of comparable clauses: reminder text stripped, the card's
    own name normalised to a placeholder (older templating self-references by name, newer
    says "this creature"), split on sentence and line breaks.

    Deliberately a TEXT-CONTAINMENT test with no judgment in it. That makes it blind to
    most real upgrades — but its false-positive rate is near zero, which is the right
    error direction for a flag whose whole claim is "you already run a worse version of
    this card"."""
    t = _REMINDER_RE.sub(" ", (text or "").lower())
    for nm in filter(None, [(name or "").lower(), (name or "").lower().split(" // ")[0],
                            (name or "").lower().split(",")[0]]):
        t = t.replace(nm, "~")
    t = _UPGRADE_SELF_RE.sub("~", t)
    return {c.strip(" .;") for c in re.split(r"[\n.]", t) if c.strip(" .;")}


def strict_upgrades(cand_name, cand_text, cand_mv, cards, carddata, mana):
    """In-deck card names that `cand` STRICTLY upgrades — every clause of the incumbent's
    text is present in the candidate's, at the same or lower mana value, AND the candidate
    does strictly more (an extra clause, or the same text for less mana). Color identity
    is deliberately NOT part of the test — `screen` flags off-color separately, and
    folding it in here would make a text-containment result depend on the deck's colors.
    Two cards with identical text and cost are
    NOT an upgrade of each other — that is redundancy, which is a different (and often
    good) thing."""
    cc = _upgrade_clauses(cand_name, cand_text)
    if not cc:
        return []
    out = []
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS or nl == (cand_name or "").lower():
            continue
        cd = carddata.get(nl) or {}
        if "Land" in _primary_type(cd.get("type") or ""):
            continue
        ic = _upgrade_clauses(n, cd.get("text") or "")
        if not ic or not ic <= cc:
            continue                                   # incumbent says something the candidate doesn't
        imv = (mana.get(nl) or (None, None))[1]
        if cand_mv is not None and imv is not None and cand_mv > imv:
            continue                                   # costs more — not strict
        strictly_more = len(cc) > len(ic) or (
            cand_mv is not None and imv is not None and cand_mv < imv)
        if strictly_more:
            out.append(n)
    return out


def cmd_screen(args):
    """Re-score a list of CANDIDATE cards against a deck as it stands right now — the
    anti-staleness pass for a build that has changed plan since the pile was first graded,
    and the one place that flags a candidate as a STRICT UPGRADE of a card already in the
    60. Reads names from args or stdin (one per line, optional leading quantity, `#`
    comments ignored). Prints full oracle text, because a verdict surface that hides the
    evidence is how a card gets mis-graded twice."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    dmeta, cards = parse_deck_file(d["path"])
    carddata, cardmeta, mana = load_card_data(), load_card_meta(), load_mana()
    legal, rar = load_legalities(), load_rarities()
    _, _, qty = load_collection()
    fmt = (args.format or dmeta.get("format") or "").strip().lower()
    if fmt in ("any", "all"):
        fmt = ""

    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = cardmeta.get(n.lower())
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    central = _central_themes(theme_w)
    d_int, d_ca = deck_role_counts(cards, carddata)
    sig = _strong_signature_themes(dmeta, cards, cardmeta)
    in_deck = {n.lower() for q, n, s, c in cards}
    declared = set(_declared_colors(dmeta) or _deck_castable_colors(dmeta, cards, mana))

    raw = list(args.names or [])
    if not raw or raw == ["-"]:
        raw = sys.stdin.read().splitlines()
    queries = []
    for ln in raw:
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        m = re.match(r"^\s*\d+\s+(.*)$", ln)
        queries.append((m.group(1) if m else ln).strip())

    rows, unresolved, ambiguous = [], [], []
    sqidx = _squash_index(carddata, lambda k: carddata[k].get("name") or k)
    for qname in queries:
        key, cands = _resolve_card_name(
            qname, carddata, lambda k: carddata[k].get("name") or k, sqidx)
        if not key:
            (ambiguous if cands else unresolved).append((qname, cands))
            continue
        cd = carddata[key]
        name = cd.get("name") or qname
        nl = name.lower()
        text = cd.get("text") or ""
        cost, mv = (mana.get(nl) or mana.get(nl.split(" // ")[0]) or (None, None))
        ident = card_colors(cd.get("colors"))
        ctags = set(cardmeta.get(nl, {}).get("synergies", []))
        shared = sorted(ctags & central)
        strength = fit_strength(shared, theme_w, text, d_int, d_ca, sig)
        roles = sorted(classify_roles(text))
        ax = doubler_axis(text)
        sup = doubler_support(ax, cards, carddata, doubler_restriction(text)) if ax else 0
        ups = strict_upgrades(name, text, mv, cards, carddata, mana)
        legs = legal.get(nl) or legal.get(nl.split(" // ")[0]) or set()
        cast_ok, cast_note = _candidate_castability(cost, ident, declared)
        rows.append(dict(name=name, cost=cost, mv=mv, text=text, roles=roles,
                         strength=strength, shared=shared, axis=ax, support=sup,
                         upgrades=ups, ident=ident,
                         owned=owned_qty(qty, name), rar=rar.get(nl, "?"),
                         illegal=bool(fmt and legs and fmt not in legs),
                         castable=cast_ok, cast_note=cast_note,
                         present=nl in in_deck))

    # The header counts RESOLVED candidates, not INPUTS. It used to print len(queries),
    # so `screen 52 "Demon"` announced "screening 1 candidate(s)" and then graded zero —
    # and, worse, a pile passed with broken shell quoting announced "222 candidate(s)"
    # when 83 names were given. The unresolved/ambiguous block moved ABOVE the results
    # for the same reason: it used to print after ~200 lines of output, which is exactly
    # where a reader does not look. (Use `-` and one name per line to avoid the whole
    # class of problem — `screen` reads stdin.)
    print(f"Deck {d['id']}: {d['name'] or d['path']} — screening {len(rows)} candidate(s) "
          f"against the CURRENT list"
          + (f" ({len(queries)} name(s) given)" if len(rows) != len(queries) else ""))
    print(f"Central themes: {', '.join(sorted(central)) or '(none)'}"
          + (f"  ·  format {fmt}" if fmt else ""))
    print("Re-scored now, so nothing here is carried over from an earlier plan.")
    if ambiguous:
        print("\nAmbiguous (be more specific — not guessed at):")
        for q, cands in ambiguous:
            print(f"    {q!r} → {'; '.join(cands[:6])}")
    if unresolved:
        print("\nNot found (fix the name, don't guess): "
              + ", ".join(q for q, _ in unresolved))
    print()

    order = {"KEY": 0, "role-player": 1, "tangential": 2}
    rows.sort(key=lambda r: (bool(r["present"]), r["illegal"], not r["castable"],
                             order.get(r["strength"], 3), -r["support"], r["name"].lower()))
    for r in rows:
        flags = []
        if r["present"]:
            flags.append("already in the deck")
        if r["illegal"]:
            flags.append(f"⚠ NOT legal in {fmt}")
        if r["cast_note"]:
            flags.append(r["cast_note"])
        if r["upgrades"]:
            flags.append("★ STRICT UPGRADE of " + ", ".join(r["upgrades"]))
        if r["axis"] and r["support"]:
            flags.append(f"✱ multiplier — doubles {r['axis']} ({r['support']} feeder(s) here)")
        own = f"×{r['owned']}" if r["owned"] else f"craft {r['rar']}"
        print(f"  {r['strength']:<12} {r['name'][:34]:36} {(r['cost'] or '?'):12} "
              f"{own:9} {', '.join(r['roles']) or '—'}")
        if r["shared"]:
            print(f"       shares: {', '.join(r['shared'])}")
        for f in flags:
            print(f"       {f}")
        if getattr(args, "full", False):
            for line in (r["text"] or "(no text)").split("\n"):
                print(f"         {line}")
        print()
    # SATURATION. KEY means "shares the deck's signature theme", and when that theme is
    # broad the label fires on everything: measured at 51% of 83 candidates on deck 52 and
    # 45% of 119 on 52a, where the strict signature is {graveyard, reanimator} and half the
    # black pool carries `graveyard`. Tightening was TRIED and rejected — requiring a
    # non-generic signature theme dropped deck 30's KEY rate 21%->1% and demoted
    # Innkeeper's Talent, the counter-doubler-in-a-counters-deck rescue the signature
    # branch exists for. So this REPORTS rather than re-scores, like the protection axis
    # and the role-count confidence: a reader who knows the label is saturated can still
    # use the ordering, but will not mistake KEY for a recommendation.
    keys = [r for r in rows if r["strength"] == "KEY"]
    if len(rows) >= 10 and len(keys) / len(rows) >= _SCREEN_KEY_SATURATED:
        by_theme = {}
        for r in keys:
            for t in r["shared"]:
                if t in sig:
                    by_theme[t] = by_theme.get(t, 0) + 1
        top = sorted(by_theme.items(), key=lambda kv: (-kv[1], kv[0]))[:2]
        print(f"⚠ KEY is SATURATED here — {len(keys)} of {len(rows)} candidates "
              f"({len(keys) / len(rows) * 100:.0f}%)"
              + (f", mostly on `{'`, `'.join(t for t, _ in top)}`" if top else "")
              + ". A label that fires on half the pile is not a shortlist. Read the shared"
              " themes and the oracle text, and treat the ORDER as the signal, not the word.")
    print("Trust KEY, judge role-player, read tangential as 'probably not here'. A ★ strict "
          "upgrade is a TEXT-CONTAINMENT test — it is deliberately conservative and misses "
          "most real upgrades, so its silence is not a verdict.")
    return 0


def cmd_resolve(args):
    """Turn card NAMES into ready-to-paste deck lines `<qty> <Name> (<SET>) <#>` with a valid
    printing (exact → DFC front → unique substring; owned printing preferred, else the pool's).
    Reads names from args or stdin (one per line, optional leading quantity). Reports
    unresolved / ambiguous names instead of guessing — the scaffolding step a from-scratch
    build otherwise does by hand."""
    idx = _printing_index()
    if not idx:
        eprint("No card data — build card-pool.csv (build_pool.py) / card-library.csv first.")
        return 1
    raw = list(args.names or [])
    if not raw or raw == ["-"]:
        raw = [ln for ln in sys.stdin.read().splitlines()]
    lines, unresolved, ambiguous = [], [], []
    sqidx = _squash_index(idx, lambda k: idx[k][0])
    for ln in raw:
        ln = ln.strip()
        if not ln or ln.lstrip().startswith("#"):
            continue
        m = re.match(r"^\s*(\d+)\s+(.*)$", ln)          # optional leading quantity
        qty, query = (m.group(1), m.group(2)) if m else ("1", ln)
        # Shared resolver: exact -> DFC front -> squashed punctuation -> unique substring,
        # deduped by DISPLAY name (a DFC's front and full name are two keys but ONE card).
        key, cands = _resolve_card_name(query, idx, lambda k: idx[k][0], sqidx)
        if not key:
            (ambiguous if cands else unresolved).append(
                (query, cands[:6]) if cands else query)
            continue
        disp, setc, coll = idx[key]
        lines.append(f"{qty} {disp} ({setc}) {coll}".rstrip())
    for ln in lines:
        print(ln)
    # LEGALITY WARNING. `resolve` is the scaffolding step for a from-scratch deck, and it
    # used to hand back any card it could find a printing for — which is how Bloodchief
    # Ascension, a TLE supplemental card, reached a finished 60 and was only caught two
    # validation steps later by `deck.py legal`. Surfacing it here means the name list is
    # checked at the moment it becomes deck lines.
    fmt = (getattr(args, "format", None) or "standard").strip().lower()
    if fmt and fmt != "any":
        resolved = [_card_line_name(ln) or "" for ln in lines]
        legal = _legality_of([n for n in resolved if n])
        illegal = [n for n in resolved
                   if n and legal.get(n.lower()) is not None
                   and fmt not in legal.get(n.lower(), set())]
        if illegal:
            eprint(f"\n⚠ NOT legal in {fmt} ({len(illegal)}): {', '.join(illegal)}")
            eprint("   Resolving a printing is not a legality check — pass --format any to "
                   "silence, or pick a different card.")
    if ambiguous:
        eprint("\n⚠ ambiguous (be more specific):")
        for q, opts in ambiguous:
            eprint(f"    {q!r} → {'; '.join(opts)}")
    if unresolved:
        eprint("\n⚠ not found:")
        for q in unresolved:
            eprint(f"    {q!r}")
    return 1 if (unresolved or ambiguous) else 0


def cmd_suggest_homes(args):
    """For a card you own, scan EVERY deck: where is it both castable and on-theme,
    is it already there, and what's the weakest card it could replace? Automates
    the manual 'which of my decks does this new card improve' fit pass."""
    card = args.card
    carddata = load_card_data()
    cardmeta = load_card_meta()
    mana = load_mana()
    cd = carddata.get(card.lower())
    if not cd:
        # Resolve a partial name the way card.py does. Exact + DFC front are already keyed
        # in carddata; this adds UNIQUE-substring matching so 'Ojer Taq' resolves to
        # 'Ojer Taq, Deepest Foundation // …' (a God//Land DFC) instead of "not found".
        ql = card.strip().lower()
        subs = sorted({c0["name"] for k, c0 in carddata.items() if ql in k}, key=len)
        if len(subs) == 1:
            card = subs[0]
            cd = carddata.get(card.lower())
        elif len(subs) > 1:
            eprint(f"{args.card!r} is ambiguous — matches: " + "; ".join(subs[:8])
                   + (" …" if len(subs) > 8 else "") + "\nUse a more specific name.")
            return 1
    if not cd:
        eprint(f"{card!r} not found in card-library.csv or card-pool.csv — check spelling.")
        return 1
    # Format-legality: a card can only be a "home" for a deck it's LEGAL in that deck's
    # format (Triumph of the Hordes is not Standard-legal, so it isn't a Standard home).
    # Reuses the pool's Legalities snapshot; unverified (pool-absent) legalities are
    # treated as legal, matching `suggest`/`legal`. `--any-format` disables the filter.
    any_format = getattr(args, "any_format", False)
    _pool_idx, _ = _pool_rotation_index()
    _cinfo = _pool_idx.get(card.lower()) or _pool_idx.get(card.split(" // ")[0].lower())
    card_legals = _cinfo[1] if _cinfo else None
    ccols = card_colors(cd.get("colors"))
    ctags = set(cardmeta.get(card.lower(), {}).get("synergies", []))
    # Card MV for the curve co-signal (#5): a top-heavy card is a worse home for a
    # low-curve deck than a midrange one — see _home_curve_fit. Also feeds the fixer
    # RATE below, so `is_fixer` is derived after it.
    _cmv = mana.get(card.lower()) or mana.get(card.split(" // ")[0].lower())
    card_mv = _cmv[1] if _cmv and _cmv[1] is not None else None
    fixer_rate = _fixer_rate(cd.get("text") or "", card_mv)
    is_fixer = bool(fixer_rate)

    print(f"Card: {card}  [{'/'.join(sorted(ccols)) or 'Colorless'}]  ({cd['type']})")
    _fixnote = ("   [rainbow fixer — value scales with a deck’s color count"
                + ("" if fixer_rate >= _FIXER_KEY_RATE
                   else f"; single source at MV {card_mv} — discounted") + "]")
    print(f"Themes: {', '.join(sorted(ctags)) or '(none)'}"
          f"{_fixnote if is_fixer else ''}")
    # The VERDICT surfaces are where the misreads clustered this cycle. `cuts` and `swap`
    # print full oracle text and produced the fewest bad calls; suggest-homes hands out
    # KEY / role-player / tangential labels with NO text, which is how Genesis Wave was
    # rated KEY for a deck whose engine it mills away. One card, one text block, always
    # printed: six lines of cost so the label is never the only evidence.
    import textwrap as _tw
    print()
    for _para in (cd.get("text") or "(no oracle text on file)").split("\n"):
        for _ln in (_tw.wrap(_para, width=84) or [""]):
            print(f"    {_ln}")
    print()

    # Which quantity (if any) this card DOUBLES — computed once; the per-deck half is the
    # density of that quantity, which is what the boost scales with.
    _daxis = doubler_axis(cd.get("text") or "")
    _drestrict = doubler_restriction(cd.get("text") or "") if _daxis else None
    results = []
    skipped_illegal = 0
    for dd in discover_decks():
        dmeta, cards = parse_deck_file(dd["path"])
        castable = _deck_castable_colors(dmeta, cards, mana)
        if not ccols.issubset(castable):
            continue
        # Castability above is a SET test (identity ⊆ deck colours) and cannot see pip
        # DEPTH; pip_depth_warning supplies the arithmetic the set test is missing.
        # load_mana values are (cost, mana_value) tuples, not dicts.
        _ce = mana.get(card.lower()) or mana.get(card.split(" // ")[0].lower())
        pipwarn = pip_depth_warning(_ce[0] if _ce else "",
                                    deck_color_sources(cards, cardmeta, carddata))
        # Skip a deck whose format the card isn't legal in (see card_legals above).
        if not any_format and card_legals:
            dfmt = (dmeta.get("format") or "").strip().lower()
            if dfmt and dfmt not in card_legals:
                skipped_illegal += 1
                continue
        theme_w = {}
        d_mvs = []
        for q, n, s, c in cards:
            if n.lower() in BASICS:
                continue
            m = cardmeta.get(n.lower())
            if m:
                for t in m["synergies"]:
                    theme_w[t] = theme_w.get(t, 0) + q
            cdn = carddata.get(n.lower())
            if cdn and "Land" not in _primary_type(cdn.get("type") or ""):
                e = mana.get(n.lower())
                if e and e[1] is not None:
                    d_mvs += [e[1]] * q
        shared = sorted(ctags & _central_themes(theme_w))
        shared = _drop_cost_themes(shared, cards, carddata)
        if not shared:
            continue
        deck_avg_mv = sum(d_mvs) / len(d_mvs) if d_mvs else 0.0
        already = bool({card.lower(), card.split(" // ")[0].lower()}
                       & {n.lower() for _, n, _, _ in cards})
        fit = sum(theme_w.get(t, 0) for t in shared)
        d_int, d_ca = deck_role_counts(cards, carddata)
        # STRICT (>=2 protected cards) — see fit_strength's docstring: the loose
        # union made a generic theme a signature and minted KEY nearly everywhere.
        sig = _strong_signature_themes(dmeta, cards, cardmeta)
        strength = fit_strength(shared, theme_w, cd.get("text") or "", d_int, d_ca, sig)
        # Color-fixer overlay: a rainbow fixer's worth scales with the deck's color
        # count, which theme-overlap can't see. In a 3+-color deck it's at least a
        # role-player manabase upgrade; in a 4+-color deck it's a KEY one (the fixing
        # is doing real work every game). The fit bump is BOUNDED (fixer_boost) so it
        # nudges ordering among fixer-eligible decks without dwarfing a real theme
        # match; the strength promotion never DEMOTES a fit fit_strength already rated
        # KEY. This closes the Overlord → 17/21a miss without touching mono-color decks.
        # The promotion is now rate-gated too: only a fixer that BUYS enough fixing
        # (`_fixer_rate` >= _FIXER_KEY_RATE — broad, or a cheap single source) is worth
        # an automatic KEY. A 3-mana one-mana-any-colour dork gets the role-player step
        # instead, which is what it is. Without this, colour count alone minted KEY and
        # the label sorts ahead of fit, so nothing downstream could correct it.
        if is_fixer and len(castable) >= 3:
            fit += _fixer_boost(len(castable), rate=fixer_rate)
            if len(castable) >= 4 and fixer_rate >= _FIXER_KEY_RATE:
                strength = "KEY"
            elif strength == "tangential":
                strength = "role-player"
        # DOUBLER overlay, same shape as the fixer one: a card that doubles tokens /
        # counters / triggers is worth the deck's DENSITY of that thing, which theme
        # overlap cannot see (it reads membership, not magnitude). Bounded, and it only
        # ever promotes a tangential fit one step — never demotes, never overrides a KEY.
        dsupport = (doubler_support(_daxis, cards, carddata, _drestrict)
                    if _daxis else 0)
        if dsupport:
            _dboost = doubler_boost(dsupport)
            fit += _dboost
            # Mirrors the fixer overlay's promotion rule. A doubler in a deck that really
            # does the thing IS a key card, and the strength label sorts ahead of fit — so
            # without this the boost could not reorder anything: Exalted Sunborn stayed
            # behind every KEY row no matter how many token-makers the deck fielded.
            if dsupport >= _DOUBLER_KEY_SOURCES:
                strength = "KEY"
            elif _dboost and strength == "tangential":
                strength = "role-player"
        # Bounded curve co-signal (#5): gently sort a top-heavy card BELOW efficient fits
        # in an aggressive low-curve deck (never boosts, never relabels — see
        # _home_curve_fit). `top_heavy` flags the row so the clunk is visible, not silent.
        curve_mult = _home_curve_fit(card_mv, deck_avg_mv)
        fit *= curve_mult
        top_heavy = curve_mult < 1.0
        cut = (None if already else
               _weakest_cut(dmeta, cards, cardmeta, carddata, add_is_fixer=is_fixer))
        results.append((fit, dd["id"], already, shared, cut, strength, top_heavy, pipwarn))

    if skipped_illegal:
        print(f"({skipped_illegal} castable deck(s) skipped — the card isn't legal in "
              f"their format; use --any-format to include them.)\n")
    if not results:
        print("No deck is both castable and shares a central theme with this card.\n"
              "(Off-color everywhere, its themes are too generic, or it's format-illegal "
              "everywhere — try `deck.py suggest <id>` from a specific deck instead.)")
        return 0
    # Sort KEY fits first (then role-player, then tangential), then by fit weight —
    # so the decks the card most belongs in lead, differentiating a key from a
    # tangential home (F04).
    _srank = {"KEY": 0, "role-player": 1, "tangential": 2}
    results.sort(key=lambda r: (_srank.get(r[5], 3), -r[0], r[1]))
    print(f"  {'deck':5} {'strength':11} {'fit':>4}  {'in?':3}  shared themes  ·  suggested cut")
    print("  " + "-" * 82)
    for fit, did, already, shared, cut, strength, top_heavy, pipwarn in results:
        tag = "yes" if already else "no"
        hint = "already maindecked" if already else (f"cut ~ {cut}" if cut else "")
        if top_heavy:
            hint = (hint + "  " if hint else "") + "⚠ top-heavy for this curve"
        if pipwarn:
            _col, _pips, _have, _want = pipwarn
            hint = ((hint + "  " if hint else "")
                    + f"⚠⚠ {_pips}x{{{_col}}} vs {_have} sources")
        print(f"  {did:5} {strength:11} {fit:>4.0f}  {tag:3}  {', '.join(shared[:3]):28}  {hint}")
    _pw = [r for r in results if r[7]]
    if _pw:
        _col, _pips, _have, _want = _pw[0][7]
        _need = f"~{_want}" if _want else "more than a 60-card deck can hold"
        print(f"\n⚠⚠ = PIP DEPTH. Castability here is a SET test (the card's colours ⊆ the "
              f"deck's), which cannot see that this card wants {_pips} {{{_col}}} in one cast. "
              f"Those decks hold as few as {_have} {{{_col}}} sources; {_need} is what a 70% "
              "turn-5 cast needs. Identity says yes, the arithmetic says no — verify before "
              "spending a wildcard.")
    if any(r[6] for r in results):
        print(f"\n⚠ = the card (MV {card_mv}) sits well above that deck's average curve — a "
              "win-more/top-heavy add there; grade it from text.")
    strong = [r for r in results if not r[2]]
    if len(strong) >= 2:
        print(f"\nCastable + on-theme in {len(strong)} decks it's not already in — one owned "
              "copy serves every deck in Arena, so slot it into all that earn it.")
    print(f"\nGrade each from full text: `deck.py cuts <id>`, then "
          f'`deck.py swap <id> --cut <weak> --add "{card}"` (shows both cards\' full text).')
    return 0


def deck_quality_vector(d):
    """A deck's measurable QUALITY vector (F10), from the same primitives the CLI
    uses — so a cut/swap can be checked for regression before/after: buildable,
    uncastable strays, interaction + card-advantage role counts, curve (avg nonland
    MV + early-drop count), and central-theme coverage."""
    dmeta, cards = parse_deck_file(d["path"])
    mana, carddata, cardmeta = load_mana(), load_card_data(), load_card_meta()
    _, _, qty = load_collection()
    missing = short = 0
    theme_w, mvs, early = {}, [], 0
    creatures = reach = 0
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS:
            continue
        have, inlib = owned(qty, n)
        if not inlib:
            missing += 1
        elif have < q:
            short += 1
        cd = carddata.get(nl)
        tline = (cd.get("type") if cd else "") or ""
        m = cardmeta.get(nl)
        tags = set(m["synergies"]) if m else set()
        if cd and "Land" not in _primary_type(tline):
            entry = mana.get(nl)
            if entry and entry[1] is not None:
                mvs += [entry[1]] * q
                if entry[1] <= 2:
                    early += q
        if "Creature" in _primary_type(tline):
            creatures += q
        # Reach = ability to CLOSE a game (the aggro axis): burn/drain reach, or an
        # evasive body that keeps connecting. Used only by the archetype-aware floor.
        if ("Burn / drain" in classify_roles((cd.get("text") if cd else "") or "")
                or (tags & _EVASION_TAGS)):
            reach += q
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    declared_hdr = _declared_colors(dmeta)
    declared = declared_hdr or _deck_castable_colors(dmeta, cards, mana)
    uncast, _off, _off_ability, _intended = _castability(
        cards, declared, mana, carddata, _uncastable_ok(dmeta))
    _tally = role_tally(cards, carddata)
    d_int, d_ca = _tally["interaction"], _tally["card_advantage"]
    return {
        "buildable": missing == 0 and short == 0, "missing": missing, "short": short,
        # Whether castability was audited against a DECLARED identity. Without a
        # `#: colors:` header, `declared` is derived from the deck's own cards, so
        # uncastable is 0 by construction (unverified, not a clean bill) — audit F16.
        "colors_declared": bool(declared_hdr),
        "uncastable": len(uncast), "interaction": d_int, "card_advantage": d_ca,
        # Real ward/hexproof/indestructible-class effects. Reported, NOT fed into
        # `tier_band` — the floor's formula is anchored by check_tier.py and a new term
        # would silently re-grade the whole roster. Surfaced so a human sees a zero.
        "protection": _tally["protection"],
        # The counts again, rendered WITH their uncertainty (see count_conf). The bare
        # ints stay for the tier floor and the F10 guard, which need numbers to compare;
        # these are what a human should read.
        "interaction_conf": count_conf(_tally, "interaction"),
        "card_advantage_conf": count_conf(_tally, "card_advantage"),
        "avg_mv": round(sum(mvs) / len(mvs), 2) if mvs else 0.0, "early_drops": early,
        "creatures": creatures, "reach": reach,
        # The deck's game PLAN drives which axes its tier floor weights (#4): an aggro
        # deck is graded on its clock, not an interaction suite it doesn't want.
        "plan": deck_plan(dmeta, avg_mv=(round(sum(mvs) / len(mvs), 2) if mvs else 0.0),
                          interaction=d_int, early=early),
        "central_themes": len(_central_themes(theme_w)),
        "central": sorted(_central_themes(theme_w)),
        # Full per-theme copy counts — lets the F10 guard tell a theme that truly LEFT
        # the deck (0 copies) from one merely demoted below the centrality cutoff (F#2).
        "theme_copies": dict(theme_w),
    }


def _quality_vector_at(d, ref):
    """The quality vector for a deck's list AS OF a git ref — evaluates that past
    version against CURRENT card knowledge (so 'was my old list better?' is a
    like-for-like comparison). Returns (vec, None) or (None, error)."""
    import subprocess
    import tempfile
    rel = os.path.relpath(d["path"], REPO_ROOT)
    r = subprocess.run(["git", "show", f"{ref}:{rel}"], capture_output=True, text=True,
                       cwd=REPO_ROOT)
    if r.returncode != 0:
        return None, (r.stderr.strip() or f"deck not found at {ref}")
    fd, tmp = tempfile.mkstemp(suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(r.stdout)
        return deck_quality_vector({"id": d["id"], "path": tmp, "name": d.get("name")}), None
    finally:
        os.remove(tmp)


def cmd_quality(args):
    """Deck-quality guard (F10): print the quality vector, diff it against a saved
    snapshot (`--vs FILE`) to flag regressions from a cut/swap, and/or check that a
    proposed add isn't a merely-tangential fit (`--add NAME`). `--at REF` compares
    this deck's list at a past git ref against now. Soft by design — it WARNS (some
    regressions are intentional trades); exits 0 unless --strict."""
    import json
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    vec = deck_quality_vector(d)
    if getattr(args, "at", None):
        old, err = _quality_vector_at(d, args.at)
        if old is None:
            eprint(f"could not read deck {d['id']} at {args.at!r}: {err} "
                   f"(renamed? see `deck.py history {d['id']}`)")
            return 1
        print(f"Quality — deck {d['id']} @ {args.at}  →  current:")
        for k in ("buildable", "uncastable", "interaction", "card_advantage",
                  "avg_mv", "early_drops", "central_themes"):
            o, n = old[k], vec[k]
            delta = "" if o == n else f"   ({o} → {n})"
            print(f"  {k:15}: {n}{delta}")
        lost = sorted(set(old["central"]) - set(vec["central"]))
        gained = sorted(set(vec["central"]) - set(old["central"]))
        if lost:
            print(f"  central themes lost since {args.at}: {', '.join(lost)}")
        if gained:
            print(f"  central themes gained: {', '.join(gained)}")
        return 0
    if getattr(args, "json", False):
        print(json.dumps(vec))
        return 0
    print(f"Quality — deck {d['id']}: {d['name'] or d['path']}")
    for k in ("buildable", "uncastable", "interaction", "card_advantage",
              "avg_mv", "early_drops", "central_themes"):
        print(f"  {k:15}: {vec[k]}")

    regressions = []
    if getattr(args, "vs", None):
        try:
            before = json.load(open(args.vs))
        except Exception as e:
            eprint(f"could not read --vs snapshot {args.vs!r}: {e}")
            return 1
        if before.get("buildable") and not vec["buildable"]:
            regressions.append("became UNbuildable")
        if vec["uncastable"] > before.get("uncastable", 0):
            regressions.append(f"castability worse ({before.get('uncastable',0)}→{vec['uncastable']})")
        if vec["interaction"] < before.get("interaction", 0):
            regressions.append(f"interaction dropped ({before['interaction']}→{vec['interaction']})")
        if vec["card_advantage"] < before.get("card_advantage", 0):
            regressions.append(f"card advantage dropped ({before['card_advantage']}→{vec['card_advantage']})")
        # A central theme dropping out of the set is only a REAL regression if the
        # theme's cards actually left the deck (0 copies now). A theme that merely fell
        # below the 25% centrality cutoff because a strongly on-theme add concentrated
        # the top theme is a benign reclassification, not a loss (F#2 — this used to
        # false-alarm, e.g. adding Zimone flagged Druid/mill/selection as "lost" while
        # their cards were still in the deck).
        tc = vec.get("theme_copies", {})
        demoted = set(before.get("central", [])) - set(vec["central"])
        truly_lost = {t for t in demoted if tc.get(t, 0) == 0}
        if truly_lost:
            regressions.append(
                f"lost central theme(s) — 0 copies remain: {', '.join(sorted(truly_lost))}")
        # Guard the direct index: a hand-written / schema-drifted --vs snapshot may lack
        # avg_mv. With .get(...,0) the comparison fires for any real curve, then
        # before['avg_mv'] would KeyError (audit A9). Skip the check when it's absent
        # rather than crash or print a misleading "0→X".
        b_mv = before.get("avg_mv")
        if b_mv is not None and vec["avg_mv"] - b_mv > 0.3:
            regressions.append(f"curve heavier (avg MV {b_mv}→{vec['avg_mv']})")

    weak_add = None
    if getattr(args, "add", None):
        dmeta, cards = parse_deck_file(d["path"])
        carddata, cardmeta = load_card_data(), load_card_meta()
        theme_w = {}
        for q, n, s, c in cards:
            if n.lower() in BASICS:
                continue
            m = cardmeta.get(n.lower())
            if m:
                for t in m["synergies"]:
                    theme_w[t] = theme_w.get(t, 0) + q
        cd = carddata.get(args.add.lower())
        ctags = set(cardmeta.get(args.add.lower(), {}).get("synergies", []))
        shared = sorted(ctags & _central_themes(theme_w))
        d_int, d_ca = deck_role_counts(cards, carddata)
        # STRICT (>=2 protected cards) — see fit_strength's docstring: the loose
        # union made a generic theme a signature and minted KEY nearly everywhere.
        sig = _strong_signature_themes(dmeta, cards, cardmeta)
        strength = fit_strength(shared, theme_w, (cd or {}).get("text") or "", d_int, d_ca, sig)
        if strength == "tangential":
            weak_add = f"add {args.add!r} is only a TANGENTIAL fit (generic themes only)"

    if regressions or weak_add:
        print("\n⚠ QUALITY GUARD:")
        for r in regressions:
            print(f"  - {r}")
        if weak_add:
            print(f"  - {weak_add}")
        print("  (soft — intentional trades are fine; re-grade the cut from full "
              "text via `deck.py cuts`/`card.py` if unsure)")
        if getattr(args, "strict", False):
            return 1
    elif getattr(args, "vs", None) or getattr(args, "add", None):
        print("\n✓ QUALITY GUARD: net improvement / no regressions.")
    return 0


# Competitive-tier robustness (F12). The tier LETTER is a human competitive
# judgment and is NEVER auto-assigned — but it should be DEFENSIBLE against the
# deck's measurable quality vector. `tier_band` maps that vector to the tier FLOOR
# the metrics alone support; it is deliberately blind to raw card power / bombs /
# meta positioning (an idf + role model can't see those), so it systematically
# UNDER-rates. A human letter one band above the floor is fine — that band credits
# the intangibles. A letter TWO-or-more bands above the floor is indefensible or
# stale, and that's the only thing the guard flags.
TIER_RANK = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}


# Evasion tags that let a creature keep connecting — the "reach" the aggro floor credits.
_EVASION_TAGS = {"evasion", "flying", "menace", "trample", "fear", "intimidate",
                 "shadow", "skulk", "horsemanship", "unblockable", "double strike"}
_AGGRO_WORDS = ("aggro", "aggressive", "hyper-aggressive", "burn")


def deck_plan(meta, avg_mv=None, interaction=None, early=None):
    """The deck's game PLAN — 'aggro' | 'control' | 'combo' | 'midrange' — which decides
    the axes its tier floor weights (#4). Source order: an explicit `#: plan:` header,
    then keywords in `#: archetype:`, then a conservative metric inference. Defaults to
    'midrange' (the current interaction+card-advantage floor), so anything not clearly
    aggro/control/combo is graded exactly as before."""
    explicit = (meta.get("plan") or "").strip().lower()
    if explicit in ("aggro", "control", "combo", "midrange"):
        return explicit
    arc = (meta.get("archetype") or "").lower()
    if any(w in arc for w in _AGGRO_WORDS):
        return "aggro"
    if "control" in arc:
        return "control"
    if "combo" in arc:
        return "combo"
    if any(w in arc for w in ("midrange", "ramp", "value", "goodstuff", "tempo")):
        return "midrange"
    # Inference (only when nothing is declared): a clearly fast, cheap, low-interaction
    # deck reads aggro. Deliberately strict so it never surprises a non-aggro deck.
    if (avg_mv is not None and avg_mv <= 2.4 and (interaction or 0) < 4
            and (early or 0) >= 8):
        return "aggro"
    return "midrange"


def _clock_score(vec):
    """Aggressive 'clock' proxy (0–7): a low curve + cheap threats + reach to close.
    Substitutes for interaction in `tier_band` ONLY for an aggro plan — a fast deck's
    resilience is its speed, not its removal count. Bounded so it can't wildly inflate."""
    mv = vec.get("avg_mv") or 99.0
    early = vec.get("early_drops", 0)
    reach = vec.get("reach", 0)
    c = 3 if mv <= 2.2 else 2 if mv <= 2.6 else 1 if mv <= 3.0 else 0
    c += 2 if early >= 12 else 1 if early >= 8 else 0
    c += 2 if reach >= 8 else 1 if reach >= 4 else 0
    return c


# A rationale that grades BELOW the measurable floor and says why is a defensible human
# call — the rubric credits intangibles in the other direction too, and deck 51 set the
# precedent. Flagging it anyway gave decks 51, 52 and 52a a permanent "possibly
# UNDER-graded" nudge for being honest, and a standing warning is one nobody reads.
# Narrow on purpose: the prose must name the floor or the rubric's own language, not just
# be long.
_BELOW_FLOOR_ARGUMENT = re.compile(
    r"(?:below the (?:measurable |metrics )?floor|band BELOW|deliberately (?:one )?band|"
    r"conservative (?:read|grade)|fails? (?:the )?(?:fourth|two|three)|"
    r"at most one clear weakness|PROVISIONAL)", re.I)


def _argues_below_floor(meta):
    """True when `#: tier:` explicitly argues for grading under the metrics floor."""
    return bool(_BELOW_FLOOR_ARGUMENT.search((meta or {}).get("tier", "") or ""))


def _keepable_at(nlands, deck_size, hand=7):
    """P(opening hand holds 2–5 lands) at a hypothetical land count — used to check
    whether the land advisory's suggested direction actually improves anything."""
    if nlands < 0 or nlands > deck_size:
        return None
    from math import comb
    tot = comb(deck_size, hand)
    return sum(comb(nlands, k) * comb(deck_size - nlands, hand - k)
               for k in range(2, 6) if k <= nlands and hand - k <= deck_size - nlands) / tot


# Cards whose value is a COUNT in the deck rather than anything in their own text. The
# `_int_scaling` sibling covers removal; this covers the rest — "equal to the number of
# Swamps you control", "for each creature card in your graveyard", "X is the number of".
# Every scoring model here grades a card in isolation, so these read at their floor.
_DECK_STATE_AXIS_RE = re.compile(
    r"(?:equal to the number of|for each|where X is the number of)\s+"
    r"([\w' -]{3,30}?)\s+(you control|in your graveyard|on the battlefield)", re.I)


def _deck_state_axis(text):
    """The deck property a card's value scales with, or None. Report-only.

    The ZONE is part of the axis: "cards" alone is uninformative, "cards in your
    graveyard" tells you which number to go count."""
    m = _DECK_STATE_AXIS_RE.search(text or "")
    if not m:
        return None
    return f"{m.group(1).strip()} {m.group(2).strip()}"[:40] or None


def tier_band(vec):
    """The tier FLOOR (S/A/B/C/D) a deck's measurable quality vector supports.
    Metrics-only and blind to bombs/meta, so it under-rates by design — used to flag
    a claimed tier sitting ≥2 bands above it, never to assign a tier.

    It rates the LIST's competitive power independent of whether the cards are owned
    — tier is a power judgment, and build-state (ownership) is tracked separately by
    `check`/`audit`, so an aspirational unbuilt list is graded on its merits. A
    castability stray IS a list flaw (a dead card), so it caps the floor."""
    inter, ca = vec["interaction"], vec["card_advantage"]
    # An AGGRO deck closes on a fast clock, not an interaction suite — so for an aggro
    # plan a strong clock (low curve + cheap threats + reach) substitutes for the
    # interaction the resilience floor otherwise demands, and a genuinely fast deck
    # isn't floored at C just for running light removal (#4). Every other plan keeps
    # the exact interaction+card-advantage floor (clock = 0), so nothing else regrades.
    clock = _clock_score(vec) if vec.get("plan") == "aggro" else 0
    ir = inter + clock                    # effective pressure/interaction axis
    resil = inter + ca + clock            # grind / resilience / closing speed
    if ir >= 5 and resil >= 7:
        band = "A"                        # measurable ceiling; S is a human call on top
    elif ir >= 3 and resil >= 4:
        band = "B"
    elif resil >= 2:
        band = "C"
    else:
        band = "D"
    # A castability stray CAPS the floor at C — it does not SET it (broad-scan F-16).
    # The old form returned "C" outright, so a deck whose measurable floor was D got
    # RAISED by having a dead card in it. "Caps" is what the docstring and CLAUDE.md
    # both already said; only the code disagreed. Note the count reaching here excludes
    # cards the deck's `#: uncastable-ok:` header declares intentional (F-02).
    if vec["uncastable"] > 0 and TIER_RANK[band] > TIER_RANK["C"]:
        band = "C"
    return band


# The measurable FLOOR requirement per band: (min interaction, min interaction+ca).
# Kept in lockstep with tier_band above — the single source for both the classifier
# and the gap diagnostic, so they can't disagree about what a band needs.
TIER_FLOOR_REQ = {"S": (5, 7), "A": (5, 7), "B": (3, 4), "C": (0, 2), "D": (0, 0)}


def tier_gap(vec, target):
    """What a deck's measurable vector needs to reach `target` tier's FLOOR (F14):
    the exact axis shortfall — +N interaction, +N card advantage, and any uncastable
    strays to clear (they cap the floor at C). Blind to bombs/meta like tier_band, so
    it reports the measurable floor gap, NOT the intangible A-vs-S judgment. Returns
    None for a bad target; a dict {target, add_interaction, add_card_advantage,
    fix_uncastable, met, summary[]} otherwise."""
    target = (target or "").upper()
    if target not in TIER_FLOOR_REQ:
        return None
    need_i, need_r = TIER_FLOOR_REQ[target]
    inter, ca = vec["interaction"], vec["card_advantage"]
    # For an aggro plan the clock already counts toward the floor (see tier_band), so
    # the interaction the deck still needs is measured against interaction + clock (#4).
    clock = _clock_score(vec) if vec.get("plan") == "aggro" else 0
    inter_eff = inter + clock
    parts = []
    # Any target above C requires 0 castability strays (a stray caps the floor at C).
    fix_unc = vec["uncastable"] if (TIER_RANK[target] > TIER_RANK["C"] and vec["uncastable"]) else 0
    if fix_unc:
        parts.append(f"clear {fix_unc} uncastable stray(s) — they cap the floor at C")
    add_i = max(0, need_i - inter_eff)
    # Interaction adds also raise the resilience sum; only the remainder needs card advantage.
    add_ca = max(0, need_r - (inter_eff + ca + add_i))
    if add_i:
        label = "interaction or clock" if clock or vec.get("plan") == "aggro" else "interaction"
        parts.append(f"+{add_i} {label} ({inter_eff}→{inter_eff + add_i})")
    if add_ca:
        parts.append(f"+{add_ca} card advantage ({ca}→{ca + add_ca})")
    if vec.get("plan") == "aggro" and add_i:
        parts.append("(aggro: raise the clock — lower the curve / add cheap threats / add "
                     "reach — or add interaction)")
    return {"target": target, "add_interaction": add_i, "add_card_advantage": add_ca,
            "fix_uncastable": fix_unc,
            "met": not [p for p in parts if not p.startswith("(aggro:")], "summary": parts}


def owned_role_fillers(d, roles, *, limit=10):
    """Owned, on-color cards NOT already in deck d that fill any role in `roles`
    (e.g. `_INTERACTION_ROLES`, or {"Card advantage"}) — the 0-wildcard fillers that
    can close a tier gap, cheapest first. On-color = the card's identity ⊆ the deck's
    declared/derived colors, so it won't surface an uncastable pick.

    ALSO format-legal, on the same rule as `craft_role_fillers`. This half used to skip
    the check its sibling applied, so `tier <id> --to A` printed the craft list as
    "format-legal" and the owned list unfiltered right above it — and it offered Deadly
    Dispute, an FCA card with no Standard legality, as a filler for Standard deck 42a.
    Being owned is not a licence to play it: the recommendation costs no wildcard but it
    still costs a DECK SLOT, and an illegal maindeck card is a worse outcome than a
    wasted craft. Same failure CLAUDE.md records for `suggest --lands`, one command over.
    A pool-absent / unverified legality is treated as legal, matching `legal`/`suggest`.
    """
    meta, cards = parse_deck_file(d["path"])
    mana, carddata = load_mana(), load_card_data()
    _, _, qty = load_collection()
    legalities = load_legalities()
    fmt = (meta.get("format") or "").strip().lower()
    in_deck = {n.lower() for q, n, s, c in cards}
    declared = set(_declared_colors(meta) or _deck_castable_colors(meta, cards, mana))
    out = []
    for nl, cd in carddata.items():
        if nl in in_deck or nl in BASICS:
            continue
        if "Land" in _primary_type(cd.get("type") or ""):
            continue
        name = cd.get("name") or nl
        have, found = owned(qty, name)
        if not found or have < 1:
            continue
        ident = card_colors(cd.get("colors"))
        if not ident <= declared:
            continue
        legs = legalities.get(nl) or legalities.get(nl.split(" // ")[0]) or set()
        if fmt and legs and fmt not in legs:
            continue
        hit = set(classify_roles(cd.get("text") or "")) & set(roles)
        if not hit:
            continue
        entry = mana.get(nl)
        mv = entry[1] if entry and entry[1] is not None else 99
        out.append((mv, name, "".join(sorted(ident)) or "C", sorted(hit),
                    (cd.get("text") or "").split("\n")[0][:64]))
    # `carddata` keys a DFC under BOTH its full "Front // Back" name and its front face,
    # and both rows carry the same display name — so a double-faced filler was printed
    # twice, wasting a line of a six-line list. Dedupe on the display name, keeping the
    # cheapest entry (the sort below is stable on mv, so first-seen wins after sorting).
    out.sort(key=lambda r: (r[0], r[1]))
    seen, deduped = set(), []
    for row in out:
        if row[1] in seen:
            continue
        seen.add(row[1])
        deduped.append(row)
    return deduped[:limit]


def craft_role_fillers(d, roles, *, limit=8):
    """Unowned pool cards (CRAFT targets) not already in deck d that fill any role in
    `roles`, on-color and legal in the deck's format — the wildcard-spend options to
    close a tier gap when the owned pool is thin (the natural question for an
    aspirational/unbuilt deck). Sorted cheaper-wildcard first, then mana value."""
    if not os.path.exists(POOL_CSV):
        return []
    meta, cards = parse_deck_file(d["path"])
    mana = load_mana()
    _, _, qty = load_collection()
    in_deck = {n.lower() for q, n, s, c in cards}
    declared = set(_declared_colors(meta) or _deck_castable_colors(meta, cards, mana))
    fmt = (meta.get("format") or "").strip().lower()
    RANK = {"Common": 0, "Uncommon": 1, "Rare": 2, "Mythic": 3}
    out, seen = [], set()
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            name = (r.get("Card Name") or "").strip()
            nl = name.lower()
            if not nl or nl in seen or nl in in_deck or nl in BASICS:
                continue
            if "Land" in _primary_type(r.get("Type") or ""):
                continue
            # want CRAFT targets — skip owned. Pool names are the full "Front // Back";
            # owned_qty falls back to the DFC front face so an owned DFC isn't listed as
            # a craft target (audit F6/F19), unlike the local owned() which needs an
            # exact key. Mirrors suggest_scored.
            if owned_qty(qty, name) > 0:
                continue
            ident = card_colors(r.get("Color(s)"))
            if not ident <= declared:
                continue
            legs = {x.strip().lower() for x in (r.get("Legalities") or "").split(";") if x.strip()}
            if fmt and legs and fmt not in legs:
                continue
            if not (set(classify_roles(r.get("Card Text") or "")) & set(roles)):
                continue
            seen.add(nl)
            entry = mana.get(nl)
            mv = entry[1] if entry and entry[1] is not None else 99
            rar = (r.get("Rarity") or "?").strip()
            out.append((RANK.get(rar, 9), mv, name, "".join(sorted(ident)) or "C", rar,
                        (r.get("Card Text") or "").split("\n")[0][:56]))
    out.sort(key=lambda x: (x[0], x[1], x[2]))
    return out[:limit]


# --- redundancy / functional-copies planner ("virtual copies first") ---------- #
# A competitive deck needs to draw its plan reliably. The blunt way is 4-ofs; the
# subtler way is FUNCTIONAL REDUNDANCY — running distinct, similar-but-different cards
# that do the same job ("virtual copies"), which keeps a singleton/highlander feel while
# still drawing the EFFECT every game. This planner encodes the user's preference: when
# firming up a thin effect, try distinct virtual copies FIRST, and fall back to true
# duplicates only when there aren't enough of acceptable quality.
_REDUNDANCY_TARGET = 4          # a plan-critical effect wants ~this many (virtual) copies
_REDUNDANCY_THIN = 2            # depth ≤ this = a consistency risk worth firming up
_REDUNDANCY_QUALITY_TOL = 1.5   # a virtual copy >this far below your best is "much weaker"


def plan_redundancy_fill(depth, best_power, functional_options, *,
                         target=_REDUNDANCY_TARGET, tol=_REDUNDANCY_QUALITY_TOL):
    """Decide how to firm up an effect the deck runs `depth` distinct copies of.

    `functional_options` = [(power, name), …] distinct cards (NOT in the deck) that do the
    same job, best-power first. `best_power` = the deck's strongest existing copy of the
    effect. Prefer functional (virtual) copies as long as they're within `tol` of your
    best — that keeps the deck semi-singleton; only when functional copies run out (or the
    remaining ones are significantly weaker) fall back to running true DUPLICATES of the
    best existing card. Pure/deterministic — unit-tested.

    Returns {need, functional:[(power,name)…], duplicates:int, reason}."""
    need = max(0, target - depth)
    if need == 0:
        return {"need": 0, "functional": [], "duplicates": 0, "reason": "already deep enough"}
    picks = []
    for pw, nm in functional_options:
        if len(picks) >= need:
            break
        if pw >= best_power - tol:            # acceptable quality → prefer the virtual copy
            picks.append((pw, nm))
    dup = max(0, need - len(picks))
    if dup == 0:
        reason = "functional copies cover it — stays singleton"
    elif not picks and not functional_options:
        reason = "no functional copies exist — duplicates are the only option"
    elif dup and picks:
        reason = "functional copies as far as they go, then duplicates for the rest"
    else:
        reason = "remaining functional copies are much weaker — duplicate instead"
    return {"need": need, "functional": picks, "duplicates": dup, "reason": reason}


def _card_power(nl, carddata, rar):
    """Heuristic 0–10 power of a card (by lowercase name) via the shared wishlist seed.

    `rar` is a load_rarities() map — Arena wildcard LETTERS, which the seed normalizes
    (wishlist._norm_rarity); passing a letter used to silently score as an uncommon (F-01)."""
    cd = carddata.get(nl) or {}
    return _power_seed({"Rarity": rar.get(nl, ""), "Card Text": cd.get("text", "") or "",
                        "Type": cd.get("type", "") or ""})


def functional_theme_options(d, theme, *, limit=8):
    """Distinct owned+craft cards (NOT in deck d) that carry synergy `theme`, on-color and
    format-legal — functional (virtual) copies of a THEME effect (e.g. the deck's ping
    payoff via the shared 'burn' tag). Returns [(power, name, owned_bool, mv, rarity)]
    best-power first. The theme analog of owned/craft_role_fillers."""
    meta, cards = parse_deck_file(d["path"])
    cardmeta = load_card_meta()
    carddata = load_card_data()
    mana = load_mana()
    rar = load_rarities()
    leg = load_legalities()
    _, _, qty = load_collection()
    in_deck = {n.lower() for q, n, s, c in cards}
    declared = set(_declared_colors(meta) or _deck_castable_colors(meta, cards, mana))
    fmt = (meta.get("format") or "").strip().lower()
    out, seen = [], set()
    for nl, m in cardmeta.items():
        if nl in seen or nl in in_deck or nl in BASICS:
            continue
        if theme not in m.get("synergies", []):
            continue
        cd = carddata.get(nl)
        if not cd or "Land" in _primary_type(cd.get("type") or ""):
            continue
        name = cd.get("name") or nl
        if not (card_colors(cd.get("colors")) <= declared):
            continue
        legs = leg.get(nl)
        if fmt and legs is not None and fmt not in legs:
            continue
        seen.add(nl)
        entry = mana.get(nl)
        mv = entry[1] if entry and entry[1] is not None else 99
        out.append((_card_power(nl, carddata, rar), name, owned_qty(qty, name) > 0, mv,
                    (rar.get(nl) or "?")))
    out.sort(key=lambda r: (-r[0], r[3], r[1]))
    return out[:limit]


def effect_redundancy(d):
    """Bucket a deck's nonland cards by the EFFECTS they provide — functional roles
    (Removal/Counter/Card advantage/…) and specific (non-generic) synergy themes — and
    return {effect: {"kind": "role"|"theme", "cards": [names], "depth": n}}. Depth is the
    count of DISTINCT cards providing the effect = its virtual-copy count."""
    meta, cards = parse_deck_file(d["path"])
    cardmeta = load_card_meta()
    carddata = load_card_data()
    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        for t in cardmeta.get(n.lower(), {}).get("synergies", []):
            theme_w[t] = theme_w.get(t, 0) + q
    central = _central_themes(theme_w)
    buckets = {}
    seen = set()
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS or nl in seen:
            continue
        cd = carddata.get(nl)
        if cd and "Land" in _primary_type(cd.get("type") or ""):
            continue
        seen.add(nl)
        effects = set()
        for r in classify_roles(cd["text"] if cd else ""):
            if r in IMPACT_ROLES:
                effects.add(("role", r))
        for t in cardmeta.get(nl, {}).get("synergies", []):
            if t in central and t not in GENERIC_THEMES:   # specific, plan-relevant themes
                effects.add(("theme", t))
        for kind, name in effects:
            b = buckets.setdefault(name, {"kind": kind, "cards": []})
            b["cards"].append(n)
    for b in buckets.values():
        b["depth"] = len(b["cards"])
    return buckets


def near_duplicates(cards, carddata, mana=None):
    """[(role_tuple, [card names])] — GROUPS of nonland cards that do the same job in this
    deck: identical non-empty functional-role sets, within a 1-mana band of each other.

    `redundancy` buckets by EFFECT and answers "how many virtual copies of this effect do
    I have"; nothing answered "which of my specific cards are interchangeable". That gap
    produced a real bad recommendation: cutting Chelonian Tackle was proposed without
    noticing Epic Fight already provided the fight mode, so the deck would have kept the
    weaker of two near-identical cards. Reported as GROUPS, not pairs — a 6-card removal
    suite is 15 pairs and one useful fact. Redundancy is often DESIRABLE; this reports,
    it does not judge."""
    buckets = {}
    for q, n, _s, _c in cards:
        if n.lower() in BASICS:
            continue
        cd = carddata.get(n.lower())
        if not cd or "Land" in _primary_type(cd.get("type") or ""):
            continue
        roles = tuple(sorted(classify_roles(cd.get("text") or "")))
        if not roles:
            continue                     # no signal — saying nothing beats guessing
        mv = None
        if mana:
            e = mana.get(n.lower())
            mv = e[1] if e and e[1] is not None else None
        buckets.setdefault(roles, []).append((cd.get("name") or n, mv))
    out = []
    for roles, members in buckets.items():
        if len(members) < 2:
            continue
        # Split a bucket into cost BANDS so a 1-drop and a 6-drop with the same role
        # aren't called interchangeable — cost is most of what makes two answers differ.
        known = sorted((m for m in members if m[1] is not None), key=lambda x: x[1])
        unknown = [m for m in members if m[1] is None]
        bands, cur = [], []
        for name, mv in known:
            if cur and mv - cur[0][1] > 1:
                bands.append(cur)
                cur = []
            cur.append((name, mv))
        if cur:
            bands.append(cur)
        if unknown:
            bands.append(unknown)
        for band in bands:
            if len(band) >= 2:
                out.append((roles, sorted(n for n, _mv in band)))
    out.sort(key=lambda r: (-len(r[1]), r[0]))
    return out


def cmd_shape(args):
    """Report a deck's structural SHAPE — wide/tall, fast/slow — from oracle text."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    meta, cards = parse_deck_file(d["path"])
    carddata, mana = load_card_data(), load_mana()
    sh = deck_shape(cards, carddata, mana)
    print(f"Shape — deck {d['id']}: {d['name'] or d['path']}\n")
    print(f"  axis          : {sh['axis']}")
    print(f"  speed         : {sh['speed']}  (avg nonland MV {sh['avg_mv']})")
    print(f"  wide score    : {sh['wide']:>3}   creature copies {sh['creatures']}, "
          f"evasive {sh['evasive']}")
    print(f"  tall score    : {sh['tall']:>3}")
    if sh["wide_cards"]:
        print(f"\n  WIDE effects ({len(sh['wide_cards'])}): {', '.join(sh['wide_cards'][:10])}"
              + ("…" if len(sh['wide_cards']) > 10 else ""))
    if sh["tall_cards"]:
        print(f"  TALL effects ({len(sh['tall_cards'])}): {', '.join(sh['tall_cards'][:10])}"
              + ("…" if len(sh['tall_cards']) > 10 else ""))
    print("\n  Shape is not quality — a wide deck is not better than a tall one. This "
          "answers the\n  question themes cannot: two decks sharing every tag can be "
          "opposite decks, and a\n  `#: archetype:` header is prose that can go stale. "
          "Read the effect lists, not just\n  the verdict — the scores are a text scan.")
    return 0


def _print_near_duplicates(cards, carddata, mana):
    groups = near_duplicates(cards, carddata, mana)
    if not groups:
        return
    print("\nINTERCHANGEABLE cards (same functional roles, same cost band) — these do the "
          "same job\nin this deck. Often deliberate redundancy; the point is to SEE the "
          "group before cutting\none at random, or before adding an eighth copy of an "
          "effect you are already deep in:")
    for roles, names in groups[:8]:
        print(f"  [{', '.join(roles)}] ×{len(names)}: {', '.join(names)}")
    if len(groups) > 8:
        print(f"  … and {len(groups) - 8} more group(s)")


def cmd_redundancy(args):
    """Competitive-consistency planner (virtual copies first). Shows each plan-effect's
    depth (distinct cards providing it), flags the THIN ones, and for each proposes how to
    firm it up — functional (virtual) copies FIRST so the deck stays semi-singleton, with
    true duplicates only as a fallback when there aren't enough of acceptable quality."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    carddata = load_card_data()
    rar = load_rarities()
    target = getattr(args, "target", None) or _REDUNDANCY_TARGET
    buckets = effect_redundancy(d)
    if not buckets:
        print(f"Deck {d['id']}: no plan-effects to analyze.")
        return 0
    print(f"Redundancy — deck {d['id']}: {d['name'] or d['path']}  "
          f"(competitive consistency; virtual copies first, target {target})")
    print("\nEffect depth (distinct cards = virtual-copy count; higher = drawn more reliably):")
    for name, b in sorted(buckets.items(), key=lambda kv: (-kv[1]["depth"], kv[0])):
        mark = "✓ deep" if b["depth"] >= target else ("~ ok" if b["depth"] > _REDUNDANCY_THIN else "△ THIN")
        print(f"  {name:22} {b['depth']:>2}  {mark}   ({b['kind']})")

    thin = {n: b for n, b in buckets.items() if b["depth"] <= _REDUNDANCY_THIN}
    if not thin:
        print(f"\n✓ every plan-effect runs >{_REDUNDANCY_THIN} virtual copies — already consistent.")
        return 0
    print(f"\nThin effects (≤{_REDUNDANCY_THIN} copies = the real singleton variance) — "
          "firm up FUNCTIONALLY first, duplicate only as fallback:")
    for name, b in sorted(thin.items(), key=lambda kv: kv[1]["depth"]):
        best = max((_card_power(c.lower(), carddata, rar) for c in b["cards"]), default=0.0)
        if b["kind"] == "role":
            owned_f = owned_role_fillers(d, {name}, limit=8)
            craft_f = craft_role_fillers(d, {name}, limit=8)
            opts = [(_card_power(nm.lower(), carddata, rar), nm, True) for _mv, nm, *_ in owned_f]
            opts += [(_card_power(nm.lower(), carddata, rar), nm, False)
                     for _rk, _mv, nm, *_ in craft_f]
            opts.sort(key=lambda r: -r[0])
        else:
            opts = [(pw, nm, own) for pw, nm, own, _mv, _r in functional_theme_options(d, name, limit=10)]
        plan = plan_redundancy_fill(b["depth"], best, [(p, n) for p, n, *_ in opts], target=target)
        own_of = {n: o for p, n, o in opts}
        print(f"\n  {name}  ({b['depth']} now: {', '.join(b['cards'])}):")
        if plan["functional"]:
            print("    ✓ add virtual copies (distinct cards — keeps it singleton):")
            for pw, nm in plan["functional"]:
                tag = "owned" if own_of.get(nm) else "craft"
                print(f"        + {nm[:34]:34} [{tag}]  pw~{pw:.1f}")
        if plan["duplicates"]:
            strongest = max(b["cards"], key=lambda c: _card_power(c.lower(), carddata, rar))
            print(f"    ⚠ then run {plan['duplicates']} true duplicate(s) — {plan['reason']}:")
            print(f"        run {plan['duplicates']}× more {strongest} (pw~{best:.1f})")
        elif not plan["functional"]:
            print(f"    (already at target, or nothing to add)")
        else:
            print(f"    → {plan['reason']}")
    print("\nVirtual copies keep the highlander feel and score the SAME tier floor (the floor "
          "counts effects, not distinct cards); duplicates are the fallback when a specific "
          "effect can't be diversified at comparable power.")
    _meta_r, _cards_r = parse_deck_file(d["path"])
    _print_near_duplicates(_cards_r, carddata, load_mana())
    return 0


def tier_consistency(d):
    """(claimed, implied, mismatch, msg) for a deck's claimed tier vs its metrics
    floor. `mismatch` is True only when a claimed tier sits ≥2 bands ABOVE the floor
    (indefensible / stale) — a soft signal to re-grade, never an auto-assignment.
    An untiered deck returns claimed='' and mismatch False."""
    meta, _cards = parse_deck_file(d["path"])
    claimed = _deck_tier(meta)
    vec = deck_quality_vector(d)
    implied = tier_band(vec)
    if not claimed:
        return "", implied, False, "untiered"
    gap = TIER_RANK.get(claimed, 0) - TIER_RANK.get(implied, 0)
    if gap >= 2:
        why = []
        if vec["uncastable"]:
            why.append(f"{vec['uncastable']} uncastable")
        why.append(f"interaction {vec['interaction']}, card-adv {vec['card_advantage']}")
        if vec.get("plan") == "aggro":
            why.append(f"aggro clock {_clock_score(vec)}/7")
        return claimed, implied, True, (
            f"tier {claimed} sits {gap} bands above the metrics floor (~{implied}): "
            + "; ".join(why))
    return claimed, implied, False, f"tier {claimed}, metrics floor ~{implied}"


def tier_consistency_issues():
    """Roster-wide (id, claimed, implied, msg) for decks whose claimed tier is
    indefensibly high vs its metrics — folded into check_all as a soft warning."""
    out = []
    for d in roster_decks():
        claimed, implied, mismatch, msg = tier_consistency(d)
        if mismatch:
            out.append((d["id"], claimed, implied, msg))
    return out


# A deck's `#: tier:` rationale is prose, so nothing kept it honest as the list changed
# underneath it — and it went stale twice in one session: 40a's rationale still argued
# from Chelonian Tackle and Unforgiving Aim after both were cut, and deck 40's cited a
# 2.26 curve after a swap moved it to 2.32. A *defensible* grade rotting into an
# indefensible one is the exact failure the tier guard exists to prevent, but the guard
# only compares the LETTER to the floor — it never reads the argument. This does.
#
# Figures worth checking are the ones a rationale actually quotes. Each maps to a live
# vector key; a mismatch is reported, never rewritten (the prose is a human argument).
# Between a label and its number the prose often puts a bracket, a qualifier, or both:
# `interaction (3)`, `interaction total (3)`, `card advantage is thinner (3)`, `curve
# (2.81)`. The original patterns demanded whitespace then digits, so EVERY parenthesised
# figure was invisible — eight of them sat on the roster, and deck 23 reported "clean"
# while quoting a curve of 3.6 against a live 3.47. Same silent-false-negative class as
# the bare-`over` and `a 2.44 curve` misses recorded above; a figure the audit cannot see
# is a figure that rots.
#
# The gap is bounded to two intervening lowercase words so a label cannot reach across a
# clause and adopt an unrelated number — "interaction and card advantage 7" stays unmatched
# for `interaction` (three words) and is picked up by the card-advantage pattern instead.
#
# The parenthesised form requires the bracket to close IMMEDIATELY after the digits, and
# that is the load-bearing part. The roster's house style is a number-first claim followed
# by a BREAKDOWN — "7 interaction (5 spot removal + 2 sweepers)", "8 interaction (6 removal
# + 2 sweepers)" — where the parenthetical decomposes the figure instead of restating it.
# A permissive `\((\d+)` read the first sub-count as the claim and reported four decks as
# stale against numbers they never asserted. `\((\d+)\)` keeps the genuine cases
# ("dense interaction (12)", "card advantage is thinner (3)") and drops every breakdown.
_FIG_GAP = r"[  ]+(?:[a-z]+[  ]+){0,2}"
_FIG_PAREN = _FIG_GAP + r"\((\d+)\)"
_RATIONALE_FIGURES = [
    (re.compile(r"interaction[  ]+(\d+)", re.I), "interaction"),
    (re.compile(r"interaction" + _FIG_PAREN, re.I), "interaction"),
    (re.compile(r"card[- ]adv(?:antage)?[  ]+(\d+)", re.I), "card_advantage"),
    (re.compile(r"card[- ]adv(?:antage)?" + _FIG_PAREN, re.I), "card_advantage"),
    # `avg` alone missed the word people actually write. Deck 52a's rationale said
    # "Average nonland MV 4.17" and the audit passed it while the live value was 4.22 —
    # "avg" is not a prefix of "Average", so no pattern here could ever see it. Same
    # class as the number-first miss recorded below: the pattern knew one spelling of a
    # figure the prose writes several ways.
    (re.compile(r"(?:avg|average) (?:nonland )?MV[  ]+(\d+\.\d+)", re.I), "avg_mv"),
    (re.compile(r"curve(?: of)?[  ]+(\d+\.\d+)", re.I), "avg_mv"),
    (re.compile(r"(?:avg|average) (?:nonland )?MV" + _FIG_PAREN.replace(r"(\d+)",
                                                                        r"(\d+\.\d+)"), re.I),
     "avg_mv"),
    (re.compile(r"curve" + _FIG_PAREN.replace(r"(\d+)", r"(\d+\.\d+)"), re.I), "avg_mv"),
    # The roster writes these NUMBER-FIRST far more often than the label-first form the
    # original patterns read — 13 interaction figures, 3 card-advantage, 1 protection,
    # none of them ever audited. Exactly the miss already recorded for avg_mv below,
    # repeated on the three axes the tier FLOOR is actually computed from.
    (re.compile(r"(\d+)[  ]+interaction", re.I), "interaction"),
    (re.compile(r"(\d+)[  ]+card[- ]adv(?:antage)?", re.I), "card_advantage"),
    (re.compile(r"(\d+)[  ]+protection", re.I), "protection"),
    # …and the house phrasing, where the number comes FIRST ("a tight 2.44 curve").
    # The pattern above only reads "curve of 2.44" / "avg MV 2.44", which the rationales
    # essentially never use: roster-wide it matched ONE figure against fourteen written
    # the other way round, so the avg_mv half of this audit was decorative. Six stale
    # curve figures were sitting in the prose, invisible, when this was added.
    (re.compile(r"(\d+\.\d+)[  ]+curve", re.I), "avg_mv"),
    # The reversal above was only ever taught the word "curve". The other house phrasing
    # for the same figure is "3.19 average" — and the FORWARD pattern requires "average"
    # to be followed by MV, so a bare number-then-"average" matched nothing in either
    # direction. Deck 53's prose read "3.19 average" while the live vector said 3.39 and
    # the audit reported the rationale CURRENT. Same shape as the G-26 residual where a
    # copula between a label and its number hides a figure: the audit is only as good as
    # its phrasing coverage, and a miss here is silent by construction.
    (re.compile(r"(\d+\.\d+)[  ]+average", re.I), "avg_mv"),
    (re.compile(r"(\d+)[- ]theme", re.I), "central_themes"),
    (re.compile(r"(\d+) central themes", re.I), "central_themes"),
    (re.compile(r"protection[  ]+(\d+)", re.I), "protection"),
    (re.compile(r"protection" + _FIG_PAREN, re.I), "protection"),
    # EARLY DROPS were in the quality vector but never audited, so a count could go stale
    # in total silence — deck 23 claimed "6 one-two-drops" against a live 11. Both
    # phrasings below are taken from the roster's own prose rather than invented.
    (re.compile(r"(\d+)[  ]+(?:early|cheap) drops?", re.I), "early_drops"),
    (re.compile(r"(\d+)[- ]one[- ]two[- ]drops?", re.I), "early_drops"),
]
# Words that are also real card names ("Negate", "Rest in Peace", …). Requiring a
# multi-word name or a long single word keeps the scan quiet; a citation of a one-word
# card is rare in prose and not worth a false positive on every "Opt" or "Duress".
_RATIONALE_MIN_LEN = 9

# A rationale legitimately names cards that AREN'T in the deck: it documents the swap
# that removed one ("Essence Scatter's creatures-only … became hard counters"), notes a
# land that left, or points at a flex/craft option deliberately held out of the 60
# (Genesis Wave). Flagging those would make the audit noise, and a noisy audit gets
# ignored — which is worse than no audit. So a citation sitting next to change- or
# flex-language is treated as history, not as a live argument. The cost is a real miss
# when someone writes "held from A by <cut card>" right after the word "replaced"; the
# figure check below is the independent backstop for that.
# NOTE what is NOT here: a bare "over". It was, and it silently disabled the FIGURE
# half of this audit across the roster, because "card advantage 9 OVER a 2.86 curve" is
# the house phrasing for a quality vector — so the one cue meant to catch a rationale
# describing a PAST figure was matching the sentence that states the CURRENT one. Deck
# 43 quoted interaction 10 against a live 8 and the audit reported clean. Every other
# cue here is a word that only appears when prose is describing a change; "over" is
# ordinary English and was far too broad to earn a place among them.
# `remov\w*` used to sit here, and it suppressed a card citation by matching the card's
# own ORACLE TEXT. The archetype prose of deck 52a read "Summon: Bahamut is a {9} that
# REMOVES two nonland permanents"; `removes` fell inside the ±140 window, so the audit
# reported "rationale is current" while the header argued from a card two swaps had
# already cut. The same word is already documented four lines down as "the worst of
# them" on the FIGURE path, where it was narrowed because `removal` is the commonest
# noun in a rationale about interaction — but only the figure path was fixed, and the
# CARD path kept the broad form. `removes` is oracle-text vocabulary, not change
# language; a rationale states a change in the past or progressive ("removed it",
# "removing the second wipe"), so those are what the cue needs to match.
_HISTORY_CUES = re.compile(
    r"\b(?:was|were|became|becomes|replac\w*|swap\w*|cut\w*|remov(?:ed|ing)|left|leaves|"
    r"instead|no longer|previously|earlier|former\w*|queued|flex|craft target|"
    r"alternative|revisit|option|skipped|held out)\b", re.I)
_HISTORY_WINDOW = 140
# "<in-deck card> is <other card> that …" — a comparison used to EXPLAIN a card the deck
# runs. Matched immediately before the citation, never as a window cue (see the call site).
_SIMILE_BEFORE = re.compile(r"\b(?:is|are)\s+$", re.I)
# `0→1` / `1->4`: the matched number is the FROM side of a stated change.
_ARROW_AFTER = re.compile(r"\s*(?:→|->|—>|–>)")

# The SECOND way a citation is not a claim about the current list: it is about ANOTHER
# DECK, or about a change you have not made yet. Three real false positives drove this,
# all from rationales written the same week:
#   • "DISTINCTNESS vs deck 8 … that one is built on Bloodthirsty Conqueror" — naming a
#     card in the deck being compared AGAINST.
#   • "PATH TO A: a second copy of the payoff axis (a Drogskol Reaver …)" — naming a
#     card to ADD.
#   • "`similar` reads 91% against 42 Blood Price" — naming another DECK whose name is
#     also a card (Blood Price, ZNR). That one is fixed exactly, by masking roster deck
#     names; these cues cover the other two, which are prose shapes rather than names.
# Kept narrow deliberately: a rationale's own argument is written in the present tense
# about this deck, so comparative and prescriptive language is a reliable signal that
# the sentence has changed subject.
_COMPARISON_CUES = re.compile(
    r"\b(?:path to|vs\.?|versus|unlike|compared|comparison|distinctness|roster'?s|"
    r"another deck|other deck|that deck|that one|elsewhere|would be|would need|"
    r"consider|candidate|upgrade to|next add|instead of)\b", re.I)


def _cites_as_history(prose, pos, length):
    """True when a card citation is NOT an argument that this deck runs the card.

    Two families: change-/flex-language (the card left, or was deliberately held out —
    see _HISTORY_CUES) and comparative/prescriptive language (the sentence is about a
    different deck, or about a card to add — see _COMPARISON_CUES). Window is generous
    on purpose; a noisy audit gets ignored, which is worse than no audit."""
    lo = max(0, pos - _HISTORY_WINDOW)
    hi = min(len(prose), pos + length + _HISTORY_WINDOW)
    window = prose[lo:hi]
    return bool(_HISTORY_CUES.search(window) or _COMPARISON_CUES.search(window))


# A FIGURE is history under much narrower conditions than a CARD citation, and reusing
# the card rule for both is what silently disabled this half of the audit.
#
# `_cites_as_history` sweeps ±140 chars for any change-word, which is right for a card:
# "Essence Scatter … became hard counters" is about a card that left, and the whole
# sentence is history. A FIGURE is different — the number is history only when the
# NUMBER ITSELF is stated as past. A rationale routinely states a CURRENT figure in a
# sentence that also mentions a change, and the domain's ordinary vocabulary collides
# with the cue list head-on:
#
#   deck 41  "The floor reads A on interaction 9 … five surplus REMOVAL spells WERE
#             traded for the card advantage below"      → live interaction 8
#   deck 42  "…interaction 8 … five surplus REMOVAL spells BECAME the pay-life engine"
#                                                        → live interaction 6
#   deck 45a "…interaction 13 … 1. THE PAYOFF IS THE ONE CRAFT TARGET"
#                                                        → live interaction 12
#   deck 42a "\"restore the interaction\" WAS not the whole fix … At interaction 6"
#                                                        → live interaction 5
#
# `remov\w*` is the worst of them: it exists to catch "removed", and it matches
# "removal" — the single most common noun in a rationale that argues about interaction.
# This is the same shape as the bare `over` cue documented above: an ordinary word of
# the domain sitting in a list meant for change-language, silently suppressing the
# sentence it was supposed to check. Four stale interaction figures were hidden by it.
#
# So the figure test looks BACKWARD only, and only for past-tense language directly
# governing this number ("was 4", "up from 2", "it cited a 2.65 curve"). Comparison
# cues still apply — a prescriptive "path to A: +3 interaction" is not a claim — but on
# a tight window, since those shapes sit next to the number too.
_FIGURE_PAST = re.compile(
    r"\b(?:was|were|had|up from|down from|previously|formerly|used to be|"
    r"cited|quoted|read|stated|re-?graded|took it (?:from|to)|moved it (?:from|to))"
    r"\b[^.;]{0,24}$", re.I)
_FIGURE_BACK_WINDOW = 60
_FIGURE_CMP_WINDOW = 60


def _figure_is_history(prose, start, end):
    """True when a quoted figure is presented as a PAST value, not a current claim."""
    if _ARROW_AFTER.match(prose, end):
        return True                       # "0→1" — the match is the FROM side.
    # A figure inside QUOTATION MARKS is a citation of earlier prose, not a live claim:
    # deck 7 writes `The old one-line reason ("fast clock but thin interaction (3)") is no
    # longer true`, which asserts the opposite of what the number says. `_FIGURE_PAST`
    # cannot reach it — its cue must sit within 24 chars and "old" is 47 back — and
    # widening that window to compensate would loosen every other suppression. An odd
    # count of quote marks before the figure means we are inside a quoted span.
    if prose.count('"', 0, start) % 2 == 1:
        return True
    if _FIGURE_PAST.search(prose[max(0, start - _FIGURE_BACK_WINDOW):start]):
        return True
    lo, hi = max(0, start - _FIGURE_CMP_WINDOW), min(len(prose), end + _FIGURE_CMP_WINDOW)
    return bool(_COMPARISON_CUES.search(prose[lo:hi]))


# A replacement claim has TWO sides, and only one of them may name an absent card.
# `_cites_as_history` treats them alike: it sees change-language near the citation and
# stays quiet. That is RIGHT for the DEPARTING card ("Essence Scatter became hard
# counters" — Essence Scatter left, the sentence documents it) and WRONG for the
# ARRIVING one. "Spell Pierce was CUT for Shriek, Treblemaker" names Shriek as the card
# that came IN, so if Shriek is not in the deck the sentence isn't history — it is
# REVERSED, and it asserts a swap that no longer exists.
#
# That is not hypothetical: the Shriek swap was applied and then undone, and the audit
# reported deck 37b clean through both, because "CUT" sat adjacent to the name either
# way. It is the residual left over from the figure fix — the audit could see an absent
# card and a wrong number, but not a claim pointing the wrong way.
#
# The cue lists cover only the directional shapes the roster's prose actually uses
# (surveyed across every `#: tier:` block, not guessed): "cut/traded/swapped/exchanged
# … for X", "became X", "replaced by X", "in place of X", and the "+X" shorthand. A
# DEPARTING marker between the cue and the citation closes the window, because "+A
# (over B)" names both sides in one clause and B is legitimately gone.
# Two of my own bugs, both caught by sweeping the roster rather than by reasoning:
#   * the `+X` shorthand needs a CASE-SENSITIVE capital to mean "a card name", and the
#     `re.I` on this pattern silently defeated it — so the `+` in "hard counters + a
#     mythic finisher" read as a swap marker (deck 12). Hence the `(?-i:[A-Z])`.
#   * "cut for" is not always a replacement: "two heist cards were CUT for cause: Doom
#     Reigns Supreme wants five Villains" means cut for a REASON (deck 45). So the
#     arriving card must sit IMMEDIATELY after the cue — a short gap with no sentence
#     break in it, which "for cause:" fails and "for Shriek, Treblemaker" passes.
_ARRIVING_CUES = re.compile(
    r"\b(?:cut|traded|swapped|exchanged)\s+(?:it\s+)?for\b|\bbecames?\b"
    r"|\breplaced by\b|\bin place of\b|(?<![\w])\+(?=\s?(?-i:[A-Z]))", re.I)
_DEPARTING_CUES = re.compile(
    r"\bover\b|\binstead of\b|\brather than\b|(?<![\w])-(?=\s?(?-i:[A-Z]))", re.I)
_ARRIVING_WINDOW = 70
_ARRIVING_GAP = 25                 # cue → citation; longer means the subject moved on
_ARRIVING_BREAK = re.compile(r"[.;:—]")


def _cites_as_arriving(prose, pos):
    """True when a citation sits on the ARRIVING side of a stated replacement — i.e. the
    prose claims this card came IN, so its absence makes the claim false, not historical.
    """
    back = prose[max(0, pos - _ARRIVING_WINDOW):pos]
    cue = None
    for m in _ARRIVING_CUES.finditer(back):
        cue = m                                  # nearest cue before the citation
    if cue is None:
        return False
    gap = back[cue.end():]
    if len(gap) > _ARRIVING_GAP or _ARRIVING_BREAK.search(gap):
        return False
    return not _DEPARTING_CUES.search(gap)


def _roster_deck_names(_cache={}):
    """Every deck's `#: name:`, longest first — masked out of a rationale before the
    card scan. A deck name that is ALSO a card name ("Blood Price", "Sacrifices") read
    as a stale citation whenever one deck's rationale named another for contrast, which
    is exactly what the distinctness prose is FOR. Exact, not heuristic."""
    if not _cache:
        names = set()
        for rec in discover_decks():
            nm = (rec.get("name") or "").strip()
            # Split a decorated title ("Blood Price — Orzhov Aristocrats") so the core
            # name masks too; drop short fragments that would mask real prose.
            for part in re.split(r"\s+[—–-]\s+", nm):
                part = part.strip()
                if len(part) >= _RATIONALE_MIN_LEN or " " in part:
                    names.add(part)
            if nm:
                names.add(nm)
        _cache["names"] = sorted(names, key=len, reverse=True)
    return _cache["names"]


def rationale_staleness(d, carddata=None):
    """(stale_cards, stale_figures) for a deck's `#: tier:` / `#: notes:` prose.

      stale_cards   — [(name, header)] the rationale names that are NOT in the deck
                      any more (a cut card the argument still leans on),
      stale_figures — [(key, quoted, actual)] a figure the prose quotes that no longer
                      matches `deck_quality_vector`.

    Report-only: the prose is a human argument and this never edits it. Names are
    matched against known cards so ordinary English can't trip it."""
    carddata = carddata if carddata is not None else load_card_data()
    meta, cards = parse_deck_file(d["path"])
    in_deck = {n for _q, n, _s, _c in cards}
    in_deck |= {n.split(" // ")[0] for n in list(in_deck)}
    stale_cards, stale_figures = [], []
    # `#: archetype:` is scanned alongside `#: tier:` because it is equally a CLAIM
    # about the current deck — "these cards push your life total up" is false once those
    # cards are cut, and the header is what a reader trusts first. (Found by this deck's
    # own archetype text surviving three rounds of swaps that removed every card it
    # named.) `#: notes:` stays out: it is a free-form build log where naming an absent
    # card is correct.
    for header in ("tier", "archetype"):
        prose = (meta or {}).get(header, "") or ""
        if not prose:
            continue
        # Mask every card the deck DOES run before scanning, longest name first. Without
        # this, a shorter card name nested inside a longer one reads as a stale citation:
        # "the Ooze Spill / Amazing Acrobatics upgrade" reported the card *The Ooze*.
        masked = prose
        for nm in sorted(in_deck, key=len, reverse=True):
            masked = masked.replace(nm, " " * len(nm))
        # ...and mask roster DECK names, which the distinctness prose names on purpose.
        for nm in _roster_deck_names():
            masked = masked.replace(nm, " " * len(nm))
        for name, row in carddata.items():
            disp = row.get("name") or name
            if len(disp) < _RATIONALE_MIN_LEN and " " not in disp:
                continue
            if disp in in_deck or name in BASICS or disp.split(" // ")[0] in in_deck:
                continue
            # SHORTHAND. A rationale abbreviates a card it runs — deck 33 writes
            # "Heartfire sac-removal" for Heartfire Immolator — and `Heartfire` is
            # itself a real card, so the scan reported a stale citation of a card the
            # prose never meant. Masking cannot help: the full name is not in the text.
            # A citation that is a strict word-prefix of a card the deck DOES run is an
            # abbreviation of that card, not a reference to a different one.
            if any(other.startswith(disp + " ") for other in in_deck):
                continue
            # CASE-SENSITIVE: prose capitalizes a card citation, so this is what keeps
            # ordinary vocabulary out. A lowercase "counterspell"/"food"/"negate" in a
            # sentence is not a reference to the card of that name.
            # Word-boundary match. A bare substring search reported the card
            # *Deliberate* inside the word "Deliberately" — and card names are common
            # enough English that this class of hit is frequent, not exotic.
            pos = -1
            start = 0
            while True:
                i = masked.find(disp, start)
                if i < 0:
                    break
                before_ok = i == 0 or not (masked[i - 1].isalnum() or masked[i - 1] in "'-")
                j = i + len(disp)
                after_ok = j >= len(masked) or not (masked[j].isalnum() or masked[j] in "'-")
                if before_ok and after_ok:
                    pos = i
                    break
                start = i + 1
            if pos < 0:
                continue
            # History suppression, EXCEPT on the arriving side of a stated replacement:
            # a card the prose says came IN is a claim about the current list, and its
            # absence means the sentence points the wrong way (see `_cites_as_arriving`).
            if (_cites_as_history(masked, pos, len(disp))
                    and not _cites_as_arriving(masked, pos)):
                continue
            # SIMILE. "It'll Quench Ya! is Spell Pierce that hits creatures too" explains
            # a card the deck runs BY NAMING a card it does not — the citation is the
            # yardstick, not the claim. This is positional rather than a window cue on
            # purpose: `is`/`are` in the ±140 window would suppress almost everything,
            # but immediately before the name it is reliable, because this scan only ever
            # sees cards the deck does NOT run (a real "the win condition is Krang" names
            # an in-deck card and never reaches here).
            if _SIMILE_BEFORE.search(masked[max(0, pos - 6):pos]):
                continue
            stale_cards.append((disp, header))
    if stale_cards:
        stale_cards = sorted(set(stale_cards))
    vec = deck_quality_vector(d)
    tier_prose = (meta or {}).get("tier", "") or ""
    for rx, key in _RATIONALE_FIGURES:
        for m in rx.finditer(tier_prose):
            quoted, actual = m.group(1), vec.get(key)
            if actual is None:
                continue
            # A rationale legitimately quotes PAST figures when it documents a change
            # ("took interaction 1→4", "it cited a 2.65 curve; the list is now 3.0"), and
            # flagging those makes the check cry wolf, which is how a check gets ignored.
            # Only a figure presented as the CURRENT state is worth reporting. This used
            # to reuse the CARD scan's `_cites_as_history`; see `_figure_is_history` for
            # why that was wrong and what it hid.
            if _figure_is_history(tier_prose, m.start(), m.end()):
                continue
            same = (abs(float(quoted) - float(actual)) < 0.005 if "." in quoted
                    else int(quoted) == int(actual))
            if not same and (key, quoted, actual) not in stale_figures:
                stale_figures.append((key, quoted, actual))
    return stale_cards, stale_figures


_EXCLUSION_CUES = re.compile(
    r"\b(?:NOT included|not included|deliberately not|not run|left out|"
    r"kept out of the (?:list|deck|60)|not in the (?:list|deck|60))\b", re.I)
_EXCLUSION_PAREN = re.compile(r"\([^()]*\)")
# The claim ends at the first clause boundary. Without this, "Craterhoof is deliberately
# NOT here — Summon: Titan's third chapter is this deck's mass pump" reads the REPLACEMENT
# as the excluded card: the excluded name sits BEFORE the cue in that shape, and whatever
# follows is the explanation. Same trap as 52a's own note, which named Quag Feast as the
# card that replaced an excluded one.
_EXCLUSION_STOP = re.compile(r"[;—–.]")
_EXCLUSION_HEAD = 60


def wrong_exclusion_claims(d, carddata=None):
    """[(name, header)] — cards the prose says are NOT in the deck, that the deck RUNS.

    The mirror of `rationale_staleness`, and the case G-27 deliberately leaves out of
    that scan. `#: notes:` is exempted there because it is a build log where naming an
    ABSENT card is correct — but "Deliberately NOT included: Bringer of the Last Gift"
    is not naming an absent card, it is a false claim about the CURRENT list, and it
    survives exactly the edit that makes it false (adding the card). Deck 52a carried
    that sentence for one commit after Bringer was added.

    Scans `notes` as well as `tier`/`archetype`, since the exclusion shape is what makes
    it checkable — an exclusion claim is a claim about the current list wherever it is
    written. Report-only, like the rest of the audit."""
    carddata = carddata if carddata is not None else load_card_data()
    meta, cards = parse_deck_file(d["path"])
    in_deck = {n for _q, n, _s, _c in cards}
    in_deck |= {n.split(" // ")[0] for n in list(in_deck)}
    out = []
    for header in ("notes", "tier", "archetype"):
        prose = (meta or {}).get(header, "") or ""
        # SHAPE, not proximity, and it took three tries to get there — the measurements
        # are the reason this is written the way it is. A plain ±400-char window produced
        # TEN roster hits and every one sampled was noise; splitting the whole post-cue
        # prose on `;` produced THIRTY-SEVEN. What works is reading only the CLAUSE that
        # the cue introduces: parentheticals stripped (the reason text is where innocent
        # names live) and cut at the first boundary (the shape "X is deliberately NOT
        # here — Y does the job" names the replacement after the dash). Roster-wide this
        # form reports zero, and still catches the 52a sentence that motivated the check.
        for m in _EXCLUSION_CUES.finditer(prose):
            seg = _EXCLUSION_PAREN.sub(" ", prose[m.end():m.end() + _EXCLUSION_HEAD])
            stop = _EXCLUSION_STOP.search(seg)
            head = seg[:stop.start()] if stop else seg
            for nm in sorted(in_deck, key=len, reverse=True):
                if len(nm) < _RATIONALE_MIN_LEN and " " not in nm:
                    continue
                if nm in BASICS or nm.lower() in BASICS:
                    continue
                if nm in head:
                    out.append((nm, header))
    return sorted(set(out))


def cmd_tier(args):
    """Tier robustness (F12): show a deck's claimed tier next to the tier FLOOR its
    measurable quality vector supports, and flag an indefensible/stale letter. It
    NEVER writes the tier — grading is a human judgment that credits bombs/meta the
    metrics can't see; this only surfaces a letter ≥2 bands above what the numbers
    support (or, conversely, a deck the metrics say is under-graded)."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    meta, _cards = parse_deck_file(d["path"])
    claimed = _deck_tier(meta)
    vec = deck_quality_vector(d)
    implied = tier_band(vec)
    if getattr(args, "audit_rationale", False):
        cards_stale, figs = rationale_staleness(d)
        wrong_excl = wrong_exclusion_claims(d)
        print(f"Rationale audit — deck {d['id']}: {d['name'] or d['path']}")
        if not cards_stale and not figs and not wrong_excl:
            print("  ✓ rationale is current — every card it cites is still in the deck, "
                  "every figure matches the live vector, and nothing it calls excluded "
                  "is actually in the list.")
            return 0
        for nm, hdr in cards_stale:
            print(f"  ⚠ `#: {hdr}:` argues from {nm}, which is NO LONGER in the deck.")
        for nm, hdr in wrong_excl:
            print(f"  ⚠ `#: {hdr}:` says {nm} is NOT included — but the deck RUNS it.")
        for key, quoted, actual in figs:
            print(f"  ⚠ `#: tier:` quotes {key.replace('_', ' ')} {quoted}, "
                  f"but the live vector says {actual}.")
        print("  Rewrite the prose (or re-grade) — a stale argument is how a defensible "
              "letter turns into an indefensible one. Nothing was changed.")
        return 0
    print(f"Tier — deck {d['id']}: {d['name'] or d['path']}")
    print(f"  claimed tier  : {claimed or '(untiered)'}")
    print(f"  metrics floor : {implied}   (measurable-only — blind to bombs/meta, so it under-rates)")
    print(f"  plan          : {vec.get('plan', 'midrange')}"
          + (f"  ·  clock {_clock_score(vec)}/7 (curve/threats/reach substitutes for interaction)"
             if vec.get('plan') == 'aggro' else "  (floor weights interaction + card advantage)"))
    print(f"  vector        : buildable {vec['buildable']} · uncastable {vec['uncastable']} · "
          f"interaction {vec.get('interaction_conf') or vec['interaction']} · "
          f"card-adv {vec.get('card_advantage_conf') or vec['card_advantage']} · "
          f"protection {vec.get('protection', 0)} · "
          f"avg MV {vec['avg_mv']} · central themes {vec['central_themes']}")
    # An {X} spell is priced at MV 1 (X counts as 0 off the stack), so the avg MV printed
    # just above under-reads a list that runs several. REPORT-only, like protection — a
    # new term in tier_band would silently re-grade the roster.
    _cd = load_card_data()
    _mana = load_mana()
    _xs = x_cost_cards(_cards, _cd, _mana)
    if _xs:
        print(f"  ⚠ avg MV under-reads: {len(_xs)} X-cost card(s) "
              f"({', '.join(n for n, _c in _xs[:3])}{'…' if len(_xs) > 3 else ''}) "
              "book as MV 1 because X counts as 0 — see `deck.py stats` for the list.")
    # Protection is REPORTED, never fed into tier_band (the floor formula is anchored by
    # check_tier.py). A zero here is a judgment prompt, not a band change.
    if not vec.get("protection"):
        sig = _protected(meta)
        print("  ⚠ ZERO protection (no ward/hexproof/indestructible-class effect)"
              + (f" while `#: protect:` names {len(sig)} build-around card(s)" if sig else "")
              + " — weigh this before granting a band the metrics floor allows.")
    # The floor caps at C on any uncastable stray; without a #: colors: header that
    # count is derived from the deck's own cards, so it's 0 by construction — say so
    # rather than imply a verified-clean castability (audit F16).
    if not vec.get("colors_declared"):
        print("  ⚠ castability UNVERIFIED — no `#: colors:` header, so uncastable=0 is "
              "self-derived; add a colors header for the floor's stray-cap to mean anything.")
    # F15: warn if the count may be under-read, since the floor grades on it.
    _meta2, _cards2 = parse_deck_file(d["path"])
    _unc, _under, _nodata = role_coverage_flags(_cards2, load_card_data())
    if _under:
        names = ", ".join(f"{n} ({a})" for n, a in _under[:4])
        print(f"  ⚠ count may under-read {len(_under)} card(s) — verify via `deck.py stats {d['id']}`: {names}"
              + ("…" if len(_under) > 4 else ""))
    if _nodata:
        print(f"  ⚠ {len(_nodata)} card(s) have no oracle text on file — the floor grades on a "
              f"partial count; enrich via build_pool.py ({', '.join(_nodata[:4])}"
              + ("…" if len(_nodata) > 4 else "") + ")")
    if not claimed:
        print("\n  (untiered — add a `#: tier: X — rationale` header; see the tier rubric in CLAUDE.md)")
        return 0
    gap = TIER_RANK.get(claimed, 0) - TIER_RANK.get(implied, 0)
    if gap >= 2:
        print(f"\n⚠ TIER MISMATCH: {claimed} sits {gap} bands above the metrics floor ({implied}).")
        print("  Either the letter is inflated/stale (re-grade from the CLAUDE.md rubric), or it")
        print("  genuinely rests on bombs/meta the metrics can't see — state which in the")
        print("  `#: tier:` rationale so the call is auditable.")
        return 1 if getattr(args, "strict", False) else 0
    if gap <= -1 and _argues_below_floor(meta):
        print(f"\n  ✓ deliberately conservative — {claimed} sits below the {implied} floor and "
              "the rationale argues why. Not flagged.")
    elif gap <= -1:
        print(f"\n  ↑ possibly UNDER-graded: even the (under-rating) metrics floor is {implied}. "
              "Consider re-grading up.")
    elif gap == 1:
        print(f"\n  ✓ defensible — {claimed} is one band above the floor (intangibles credit).")
    else:
        print(f"\n  ✓ consistent — {claimed} matches the metrics floor.")

    # F14 — tier-gap diagnostic: the MEASURABLE work to reach a target band's floor,
    # plus the owned (0-wildcard) on-color cards that fill the short axis. The
    # selection stays a human call (protect signature/spice — that's /tune-deck's job).
    target = getattr(args, "to", None)
    if target:
        gapinfo = tier_gap(vec, target)
        if not gapinfo:
            eprint(f"\n--to: unknown target tier {target!r} (use S/A/B/C/D)")
            return 1
        print(f"\n── Path to the {gapinfo['target']} floor ──")
        if gapinfo["met"]:
            print(f"  ✓ already meets the {gapinfo['target']} floor "
                  f"(interaction {vec['interaction']}, card-adv {vec['card_advantage']}) — "
                  "the letter is a human call from here (bombs/meta).")
            return 0
        print("  measurable gap: " + "; ".join(gapinfo["summary"]))

        # `adds` accumulates the fillers that close the gap, in the order we'll pair
        # them with cuts: owned (0-wildcard) first, then craft targets. Each entry is
        # (axis, kind, mv, name, ident, note).
        adds = []

        def _axis(role_set, add_flag, label):
            if not add_flag:
                return
            owned_f = owned_role_fillers(d, role_set, limit=6)
            craft = craft_role_fillers(d, role_set, limit=6)
            # ONE list, ordered by mana value, with ownership as an ANNOTATION. These used
            # to print as two sections — owned first, then craft — each capped at six, so a
            # better craft filler sat below six owned ones and the assembled plan below
            # reserved owned picks first. That is a build gated on ownership, and ownership
            # here is hand-maintained data that goes stale between updates. Cost still
            # prints on every row; it just no longer decides the order.
            merged = [(mv, name, ident, "owned", "owned", txt)
                      for mv, name, ident, _hit, txt in owned_f]
            merged += [(mv, name, ident, (rar[:1] or "?") + " craft", "craft", txt)
                       for _rk, mv, name, ident, rar, txt in craft]
            merged.sort(key=lambda r: (r[0], r[1].lower()))
            if merged:
                print(f"\n  on-color, format-legal {label} to add "
                      f"(ranked by cost; ownership is a note, not a preference):")
                for mv, name, ident, tag, _kind, txt in merged:
                    print(f"    MV{mv:>2} {name:28} [{ident:4}] {tag:8} {txt}")
            else:
                print(f"\n  (no on-color {label} filler found)")
            adds.extend((label, kind, mv, name, ident,
                         "0 WC" if kind == "owned" else tag)
                        for mv, name, ident, tag, kind, _t in merged[:add_flag])

        _axis(_INTERACTION_ROLES, gapinfo["add_interaction"], "interaction")
        _axis({"Card advantage"}, gapinfo["add_card_advantage"], "card advantage")

        # #4 — assemble the concrete before/after tune package: pair each filler with a
        # weakest-fit cut (from the SAME cut ranking `deck.py cuts` prints, so the two
        # can't disagree), then project the resulting quality vector and floor. It's a
        # STARTING plan, not an auto-apply: the card selection stays a human call
        # (protect signature/spice — that's /tune-deck), so it prints, never writes.
        cut_rows, _c, _pp, _di = rank_cut_candidates(d)
        # Don't propose cutting a card we're also adding (a filler already in the 60
        # would be surfaced as a cut otherwise).
        add_names = {a[3].lower() for a in adds}
        cut_pool = [r for r in cut_rows if r[1].lower() not in add_names]
        pairs = list(zip(adds, cut_pool))
        if pairs:
            print(f"\n── Assembled tune plan → {gapinfo['target']} (starting point; grade & "
                  "protect signature/spice) ──")
            int_gain = ca_gain = 0
            for (axis, kind, mv, name, ident), cut in ((a[:5], c) for a, c in pairs):
                cut_name, cut_mv, cut_roles, cut_text, cut_is_int = (
                    cut[1], cut[2], cut[3], cut[7], cut[8])
                cut_ca = "Card advantage" in cut_roles
                # A mana source: the Ramp/fixing role, OR a dork whose "add one mana"
                # phrasing (a flavor-keyword ability) the role classifier misses.
                cut_ramp = "Ramp / fixing" in cut_roles or _produces_mana(cut_text)
                # Net axis change: +1 for the add's axis, −1 if the cut fed that axis.
                if axis == "interaction":
                    int_gain += 1
                else:
                    ca_gain += 1
                if cut_is_int:
                    int_gain -= 1
                if cut_ca:
                    ca_gain -= 1
                mvs = f"MV{mv:>2}" if isinstance(mv, int) else "MV ?"
                cmvs = f"MV{cut_mv:>2}" if isinstance(cut_mv, int) else "MV ?"
                warn = ""
                if cut_is_int:
                    warn = "  ⚠ cut feeds interaction — pick another cut"
                elif cut_ca:
                    warn = "  ⚠ cut feeds card advantage — pick another cut"
                elif cut_ramp:
                    warn = "  ⚠ cut is a ramp/fixing source — losing it may hurt the manabase"
                print(f"  − {cut_name[:28]:28} {cmvs}   →   + {name[:26]:26} {mvs} "
                      f"[{ident:4}] ({axis}, {kind}){warn}")
            if len(adds) > len(cut_pool):
                print(f"  … {len(adds) - len(cut_pool)} more add(s) needed but the cut list is "
                      "exhausted — the deck may already be tight; loosen a #: protect: card.")
            # Projected floor: apply the net axis changes to the vector, re-band.
            proj = dict(vec)
            proj["interaction"] = max(0, vec["interaction"] + int_gain)
            proj["card_advantage"] = max(0, vec["card_advantage"] + ca_gain)
            proj_band = tier_band(proj)
            print(f"\n  projected: interaction {vec['interaction']}→{proj['interaction']}, "
                  f"card-adv {vec['card_advantage']}→{proj['card_advantage']}  "
                  f"⇒ metrics floor {implied}→{proj_band}"
                  + (f"  ✓ meets {gapinfo['target']} floor" if TIER_RANK.get(proj_band, 0)
                     >= TIER_RANK.get(gapinfo['target'], 9) else
                     f"  (still short of {gapinfo['target']} — more adds or a heavier tune)"))
            print("  Preview any line with `deck.py swap %s --cut <A> --add <B>` "
                  "(shows full text of both)." % d["id"])
        else:
            print("\n  → make room with `deck.py cuts %s` (grade cuts from full text); the card"
                  " SELECTION\n    is a judgment call — protect signature/spice (that's /tune-deck)."
                  % d["id"])
    return 0


def deck_git_history(path, limit=None):
    """[{hash, date, subject}] for a deck file, newest first, from `git log --follow`.
    The commit messages ARE the deck's changelog (they state the thematic + technical
    why). Empty list if git is unavailable / the file is untracked — the CLI and the
    dashboard 'recently edited' panel both read THIS one helper so they can't drift."""
    import subprocess
    rel = os.path.relpath(path, REPO_ROOT)
    args = ["git", "log", "--follow", "--date=short", "--format=%h\t%ad\t%s"]
    if limit:
        args.append(f"-n{int(limit)}")
    args += ["--", rel]
    try:
        r = subprocess.run(args, capture_output=True, text=True, cwd=REPO_ROOT)
    except Exception:
        return []
    if r.returncode != 0:
        return []
    out = []
    for ln in r.stdout.splitlines():
        if not ln.strip():
            continue
        parts = ln.split("\t", 2)
        if len(parts) == 3:
            out.append({"hash": parts[0], "date": parts[1], "subject": parts[2]})
    return out


def deck_recent_card_delta(path):
    """Card-level diff of the MOST RECENT edit to a deck file: {added, removed, prev}
    where added/removed are [(display_name, qty)] between the deck's current list and
    its previous committed version (printing- and case-fungible via `_multiset`). None
    when there's no prior version (a brand-new deck) or git is unavailable — so the
    'recently edited' panel can show WHAT changed, not just when."""
    rel = os.path.relpath(path, REPO_ROOT)
    hashes = _deck_commit_hashes(rel)
    if len(hashes) < 2:
        return None  # no prior committed version to diff against
    prev_ms = _deck_ms_at_ref(rel, hashes[1])
    if prev_ms is None:
        return None
    added, removed = _ms_delta(prev_ms, _multiset(parse_deck_file(path)[1]))
    return {"added": added, "removed": removed, "prev": hashes[1][:9]}


def _deck_commit_hashes(rel, before=None):
    """Full commit hashes touching a deck file, newest first; with `before` (an ISO
    date) only those at/before it. [] on any git failure. Shared by the card-delta
    helpers so the git plumbing lives in one place."""
    import subprocess
    args = ["git", "log", "--follow", "--format=%H"]
    if before:
        args.append(f"--before={before}")
    args += ["--", rel]
    try:
        r = subprocess.run(args, capture_output=True, text=True, cwd=REPO_ROOT)
    except Exception:
        return []
    return [h for h in r.stdout.split() if h] if r.returncode == 0 else []


def _deck_ms_at_ref(rel, ref):
    """The card multiset of a deck file AS OF a git ref, or None on failure."""
    import subprocess
    import tempfile
    r = subprocess.run(["git", "show", f"{ref}:{rel}"], capture_output=True, text=True,
                       cwd=REPO_ROOT)
    if r.returncode != 0:
        return None
    fd, tmp = tempfile.mkstemp(suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(r.stdout)
        return _multiset(parse_deck_file(tmp)[1])
    except Exception:
        return None
    finally:
        os.remove(tmp)


def _ms_delta(prev_ms, cur_ms):
    """(added, removed) as sorted [(display, qty)] between two card multisets."""
    added = sorted((disp, q - prev_ms.get(nl, (disp, 0))[1])
                   for nl, (disp, q) in cur_ms.items() if q > prev_ms.get(nl, (disp, 0))[1])
    removed = sorted((disp, q - cur_ms.get(nl, (disp, 0))[1])
                     for nl, (disp, q) in prev_ms.items() if q > cur_ms.get(nl, (disp, 0))[1])
    return added, removed


def deck_card_delta_since(path, since):
    """Cumulative card-level delta between a deck's current list and its state AS OF an
    ISO date `since` — {added, removed, base, base_date} or None when there's no
    committed version at/before that date or git is unavailable. 'What have I NET-changed
    since date X (and still need to push to Arena)', vs `deck_recent_card_delta`'s single
    most-recent edit. Printing/case-fungible via `_multiset`."""
    import subprocess
    rel = os.path.relpath(path, REPO_ROOT)
    hashes = _deck_commit_hashes(rel, before=since)
    if not hashes:
        return None  # deck had no committed version at/before that date
    base = hashes[0]
    base_ms = _deck_ms_at_ref(rel, base)
    if base_ms is None:
        return None
    added, removed = _ms_delta(base_ms, _multiset(parse_deck_file(path)[1]))
    bd = subprocess.run(["git", "show", "-s", "--format=%ad", "--date=short", base],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    return {"added": added, "removed": removed, "base": base[:9],
            "base_date": bd.stdout.strip() if bd.returncode == 0 else ""}


def cmd_history(args):
    """Show a deck file's git change history — the accurate, complete record of how
    the deck evolved (each commit message states the thematic + technical why). This
    is the deck's changelog; it lives in git rather than in-file so it can't get
    unwieldy or drift. Pair with `deck.py quality <id> --at <hash>` to compare a past
    version's measurable vector (interaction / curve / themes) against now."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    rel = os.path.relpath(d["path"], REPO_ROOT)
    since = getattr(args, "since", None)
    hist = deck_git_history(d["path"])
    if since:
        hist = [h for h in hist if h["date"] >= since]
    scope = f" since {since}" if since else ""
    print(f"History — deck {d['id']}: {d['name'] or rel}{scope}  ({len(hist)} commit(s))")
    for h in hist:
        print(f"  {h['hash']}  {h['date']}  {h['subject']}")
    if since:
        # The cumulative card-level net change since that date — 'what do I still need to
        # push to Arena', printing/case-fungible.
        delta = deck_card_delta_since(d["path"], since)
        if delta and (delta["added"] or delta["removed"]):
            print(f"\n  Net card change since {delta['base_date'] or since} "
                  f"(base {delta['base']}):")
            for nm, q in delta["added"]:
                print(f"    + {q}× {nm}")
            for nm, q in delta["removed"]:
                print(f"    − {q}× {nm}")
        elif delta:
            print(f"\n  No net card change since {delta['base_date'] or since} "
                  "(edits may have cancelled out, or only metadata changed).")
    if hist:
        print(f"\n  full text of any version:   git show <hash>:{rel}"
              f"\n  compare a version's metrics: deck.py quality {d['id']} --at <hash>")
    return 0


def cmd_preflight(args):
    """One-call verification for the skills (F05): construction legality + owned/
    buildable + castability + repo integrity, as a structured PASS/FAIL block.
    Orchestrates the existing checks (legal/check_all) rather than re-implementing
    them. Exits non-zero only on a HARD failure (illegal deck or broken integrity);
    unowned craft targets / hybrid strays are WARN, since WIP decks are legitimate."""
    import io
    import contextlib
    import subprocess
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    dmeta, cards = parse_deck_file(d["path"])

    # Construction legality (size, copies, format) — reuse cmd_legal, captured.
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        legal_rc = cmd_legal(argparse.Namespace(id=args.id, fmt=None))

    # Owned / buildable.
    _, _, qty = load_collection()
    missing = short = 0
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        have, inlib = owned(qty, n)
        if not inlib:
            missing += 1
        elif have < q:
            short += 1

    # Castability.
    mana = load_mana()
    carddata = load_card_data()
    declared = _declared_colors(dmeta) or _deck_castable_colors(dmeta, cards, mana)
    uncast, off_ident, _, intended = _castability(
        cards, declared, mana, carddata, _uncastable_ok(dmeta))

    # Repo integrity — the deterministic gate, run out-of-process for a clean signal.
    integ = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "check_all.py"), "--quiet"],
        capture_output=True, text=True)
    integ_ok = integ.returncode == 0

    def mark(ok):
        return "PASS" if ok else "FAIL"
    legal_ok = legal_rc == 0
    print(f"Preflight — deck {d['id']}: {d['name'] or d['path']}")
    print(f"  legal (construction) : {mark(legal_ok)}")
    print(f"  owned (buildable)    : "
          + ("PASS — fully owned" if missing == 0 and short == 0
             else f"WARN — {missing} craft target(s), {short} short (WIP-ok)"))
    print(f"  castability          : "
          + ("PASS" if not uncast else f"FAIL — {len(uncast)} uncastable")
          + (f" (+{len(intended)} intended, exempt)" if intended else "")
          + (f" (+{len(off_ident)} hybrid stray, ok)" if off_ident else ""))
    print(f"  integrity (check_all): {mark(integ_ok)}")
    hard = (not legal_ok) or bool(uncast) or (not integ_ok)
    print(f"Verdict: {'BLOCKED' if hard else 'READY'}")
    return 1 if hard else 0


              # A gate names a RESOURCE the card needs; the count is how much of it the
              # deck actually holds. Each entry: (regex, label, kind). `kind` selects the
              # counter below — keeping the two apart is what lets a new gate be one line.
_SCREEN_KEY_SATURATED = 0.40   # KEY on this share of a pile carries no information
_TARGET_WORD_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
_TARGET_FAT_MV = 5      # at/above this, reanimating a card gains real mana
_TARGET_GATES = [
    (re.compile(r"mana value (\d+) or less", re.I), "creature MV ≤{0} in the yard", "mv"),
    (re.compile(r"total mana value (\d+) or less", re.I), "cards totalling MV ≤{0}", "mv"),
    (re.compile(r"sacrifice (?:an artifact or creature|a creature or artifact)", re.I),
     "artifacts + creatures to sacrifice", "sac_ac"),
    (re.compile(r"sacrifice (?:a|another) creature", re.I), "creatures to sacrifice", "sac_c"),
    # Lookahead, or this double-fires on "sacrifice an artifact or creature" and reports
    # the artifact-only count next to the correct combined one.
    (re.compile(r"sacrifice an artifact\b(?! or creature)", re.I),
     "artifacts to sacrifice", "sac_a"),
    (re.compile(r"(?:return|put) target creature card", re.I), "creature cards to return", "creat"),
    # WORD-numbers, because Magic writes "eight or more permanent cards", not "8 or more".
    # The digit-only form of this pattern never matched a single card — it was written
    # against Starving Revenant's Descend 8 and could not see it. Nothing noticed because
    # a gate that silently reports nothing looks exactly like a deck with no gates.
    (re.compile(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten) or more "
                r"permanent cards in your graveyard", re.I),
     "permanent cards (needs {0})", "perm"),
    # CARD-TYPE thresholds in the graveyard. Found by running `targets` against deck 54,
    # a Lesson deck built entirely on them, and getting "no gated effects detected" — the
    # table knew MV caps, sacrifice costs and the permanent-count threshold, and nothing
    # about "three or more Lesson cards in your graveyard" or "the number of Lesson cards
    # in your graveyard". Those are the same question (does the list hold the resource?)
    # in the shape a TYPE-matters deck writes it. `permanent` is excluded because the rule
    # above already owns it and would otherwise report the same gate twice.
    (re.compile(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten) or more "
                r"(?!permanent)([A-Za-z]+) cards? in (?:your|all) graveyards?", re.I),
     "{1} cards in the yard (needs {0})", "gy_type"),
    (re.compile(r"number of (?!permanent)([A-Za-z]+) cards? in (?:your|all) graveyards?", re.I),
     "{0} cards in the yard", "gy_type"),
    (re.compile(r"there'?s an? (?!permanent)([A-Za-z]+) card in (?:your|a) graveyard", re.I),
     "{0} cards in the yard (needs 1)", "gy_type"),
    # NO generic "cards to discard" rule. It was written, and it reported 35 for every
    # discard outlet in a 60-card deck — i.e. "you have a hand", which is true of every
    # deck and decides nothing. Same saturation failure this file already documents for
    # `suggest`'s Decks column and `cuts`' protect boost: a signal that fires on
    # everything is not a signal. A gate earns a row only when the resource can be SHORT.
]


def target_counts(cards, carddata, mana):
    """[(card, gate_label, count, need)] — for every card whose text names a GATE, how
    many cards in THIS deck satisfy it.

    The question no command answered. Deck 52's concept pile held 24 ways to return a
    creature against 8 creatures worth returning, and that number came from a
    hand-written script — `engines` grades enabler↔payoff by synergy TAG, which is a
    different question, and every scoring model here reads a card in ISOLATION. G-61
    states the discipline in prose ("state the count, then decide") with an incident list
    of four dismissals that were overturned, precisely because nothing automates it.

    Counts EXCLUDE the card itself (a sacrifice outlet is not its own fodder) and
    exclude lands unless the gate is about lands. `need` is the number the text demands
    when it states one (descend 8), else None. Report-only, and a heuristic on card
    text like every model here — read the list, don't just read the number."""
    pool = []
    for q, n, _s, _c in cards:
        nl = n.lower()
        cd = carddata.get(nl) or carddata.get(nl.split(" // ")[0]) or {}
        entry = mana.get(nl) or mana.get(nl.split(" // ")[0])
        mv = mana_value(front_face_cost(entry[0])) if entry and entry[0] else None
        pool.append({"n": n, "q": q, "type": (cd.get("type") or "").lower(),
                     "text": cd.get("text") or "", "mv": mv})
    out, seen = [], set()
    for c in pool:
        if c["n"] in seen or "land" in c["type"] and "creature" not in c["type"]:
            continue
        seen.add(c["n"])
        for rx, label, kind in _TARGET_GATES:
            m = rx.search(c["text"])
            if not m:
                continue
            groups = [g for g in (m.groups() or ()) if g is not None]
            num = None
            if groups:
                g0 = groups[0].lower()
                num = int(g0) if g0.isdigit() else _TARGET_WORD_NUM.get(g0)
            others = [o for o in pool if o["n"] != c["n"]]
            if kind == "mv":
                hits = [o for o in others if "creature" in o["type"]
                        and o["mv"] is not None and o["mv"] <= num]
            elif kind == "sac_ac":
                hits = [o for o in others
                        if "creature" in o["type"] or "artifact" in o["type"]]
            elif kind == "sac_c":
                hits = [o for o in others if "creature" in o["type"]]
            elif kind == "sac_a":
                hits = [o for o in others if "artifact" in o["type"]]
            elif kind == "creat":
                hits = [o for o in others if "creature" in o["type"]]
                # The count that actually decided something on deck 52: not "how many
                # creatures" (nearly all of them) but how many are BIG enough that
                # cheating them in gains you mana. 24 ways to return against 8 worth
                # returning is the shape of an over-built reanimation package.
                fat = sum(o["q"] for o in hits
                          if o["mv"] is not None and o["mv"] >= _TARGET_FAT_MV)
                out.append((c["n"], f"creature cards to return ({fat} at MV{_TARGET_FAT_MV}+)",
                            sum(o["q"] for o in hits), None))
                continue
            elif kind == "perm":
                hits = [o for o in others if not {"instant", "sorcery"} & set(o["type"].split())]
            elif kind == "gy_type":
                # The captured word is a TYPE or SUBTYPE ("Lesson", "creature", "artifact"),
                # so match the type LINE. Case-insensitive: Magic capitalizes a real subtype
                # but lower-cases the generic nouns, and both spellings appear in gate text.
                want = groups[-1].lower()
                hits = [o for o in others if want in o["type"].lower()]
            else:
                hits = [o for o in others if "land" not in o["type"]]
            # Normalise a word-number in the label ("needs three" -> "needs 3") so the
            # column reads uniformly whichever spelling the card used.
            disp_groups = list(groups)
            if disp_groups and num is not None and not disp_groups[0].isdigit():
                disp_groups[0] = str(num)
            try:
                shown = label.format(*disp_groups) if disp_groups else label
            except (IndexError, KeyError):
                shown = label
            out.append((c["n"], shown, sum(o["q"] for o in hits),
                        num if kind in ("perm", "gy_type") else None))
    return out


def cmd_targets(args):
    """Does this deck contain TARGETS for its own effects? Counts, per gated card, how
    many cards in the list satisfy the gate its text names."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    _meta, cards = parse_deck_file(d["path"])
    rows = target_counts(cards, load_card_data(), load_mana())
    print(f"Deck {d['id']}: {d['name'] or d['path']} — targets for its own effects")
    if not rows:
        print("  No gated effects detected (no MV cap, sacrifice cost or count threshold "
              "in this list's text).")
        return 0
    print(f"  {'Card':32} {'What its text needs':42} {'in deck':>7}")
    print("  " + "-" * 84)
    thin = 0
    for name, label, count, need in sorted(rows, key=lambda r: (r[2], r[0])):
        flag = ""
        if count == 0:
            flag = "  ✗ NOTHING"
            thin += 1
        elif need is not None and count < need:
            flag = f"  ⚠ short of {need}"
            thin += 1
        elif count <= 3:
            flag = "  ⚠ thin"
            thin += 1
        print(f"  {name[:32]:32} {label[:42]:42} {count:>7}{flag}")
    print(f"\n  {len(rows)} gated effect(s); {thin} thin or unmet. A gate with nothing "
          "behind it is a dead card, and a card graded in isolation cannot show you that "
          "(G-61). Counts exclude the card itself; read the list, not just the number.")
    return 0


def cmd_engines(args):
    """Engine analysis: for each two-sided engine theme the deck is built on, show its
    ENABLERS (feed the engine) vs PAYOFFS (reward it) and flag a lopsided engine —
    payoffs with no enablers, or enablers with no reward — the flaw a bag-of-tags model
    can't see. Heuristic + text-based; prints the card lists so you grade the balance."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    meta, cards = parse_deck_file(d["path"])
    cardmeta = load_card_meta()
    carddata = load_card_data()
    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = cardmeta.get(n.lower())
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    central = _central_themes(theme_w)
    signature = _signature_themes(meta, cards, cardmeta)
    bal = engine_balance(cards, carddata, central, signature)

    print(f"Deck {d['id']}: {d['name'] or d['path']} — engine analysis (enabler ↔ payoff)")
    if not bal:
        print("\nNo two-sided engine themes are central to this deck. Engines covered: "
              + ", ".join(sorted(ENGINE_THEMES)) + ".")
        return 0

    def fmt(pairs):
        return ", ".join(f"{n}×{q}" if q > 1 else n for n, q in pairs)

    flagged = 0
    for theme, info in bal.items():
        mark = "⚠ " if info["flag"] else "  "
        print(f"\n{mark}{theme}: {info['verdict']}")
        if info["enablers"]:
            print(f"    enablers ({info['en']}): {fmt(info['enablers'])}")
        if info["payoffs"]:
            print(f"    payoffs  ({info['pay']}): {fmt(info['payoffs'])}")
        if info.get("deaths"):
            print(f"    death-triggers ({info['death']}, combat-fed): {fmt(info['deaths'])}")
        flagged += 1 if info["flag"] else 0

    print("\nHeuristic + text-based — a card can play both sides, and the classifier can "
          "miss an unusual phrasing, so read the lists. Fix a ⚠ by adding the short side "
          "(`deck.py suggest`) or trimming dead payoffs (`deck.py cuts`).")
    return 0


def cmd_rotation(args):
    """Roster-wide Standard-rotation exposure — which of your decks run cards closest to
    rotating, and what rotates next. Offline: reads the pool's Released/Legalities
    snapshot. A card's rotation year is its set's release + `--years` (Standard's ~3y
    window); `--within` sets how far ahead to look (default 2). Scope with --format."""
    fmt = (args.fmt or "standard").strip().lower()
    decks, rollup, meta = rotation_sweep(fmt, years=args.years, within=args.within)
    if not meta["has_released"]:
        eprint("card-pool.csv has no Released column — rebuild it (build_pool.py --all) so "
               "rotation dates are available. Nothing to report until then.")
        return 1
    if meta["stale_days"] is not None and meta["stale_days"] > 120:
        eprint(f"⚠ card-pool.csv is {meta['stale_days']} days old — its legality/rotation "
               "snapshot may lag the current Standard; rebuild with build_pool.py --all.")
    this_year = meta["this_year"]
    total = sum(d["n_slots"] for d in decks)
    print(f"Rotation sweep ({fmt}, ~{args.years}y window, next {args.within}y) — "
          f"{meta['n_decks']} deck(s), {total} rotating card-slot(s).")
    if not total:
        print(f"No cards rotating within {args.within} year(s). ✓ "
              "(widen with --within, or rebuild the pool if it's stale.)")
        return 0

    print("\nRotates by year (deck-slots · distinct cards · decks) — soonest first:")
    for ry in sorted(rollup):
        rr = rollup[ry]
        soon = "  ⚠ SOON" if ry <= this_year + 1 else ""
        past = "  (past-due — pool may be stale)" if ry < this_year else ""
        print(f"  ~{ry:>7}: {rr['slots']:>3} slot(s) · {len(rr['cards']):>3} card(s) · "
              f"{len(rr['decks']):>2} deck(s){soon}{past}")

    print("\nBy deck (most-exposed first):")
    for d in decks:
        if not d["n_slots"]:
            continue
        print(f"\n  deck {d['id']:>4}  {d['name'][:34]:34} {d['n_slots']} rotating")
        for c in d["atrisk"]:
            print(f"       ~{c['rotates']:>4}  {c['qty']}× {c['name']} ({c['set']})")

    if meta["unverified"]:
        print(f"\n({meta['unverified']} card-slot(s) not found in the pool — unverified, "
              "skipped; rebuild the pool if they're recent.)")
    print("\nTiming is a ~%d-year heuristic from set release, not the official schedule, and "
          "the pool keys one printing per card (a reprint can read early) — verify before "
          "disenchanting." % args.years)
    return 0


def cmd_brawl(args):
    """Roster-wide Brawl-readiness — which of your decks are closest to a legal Brawl
    conversion, and the best commander for each. Offline. `distance` = cards to change:
    duplicates to trim to singleton + cards outside the best commander's color identity
    (basics refill the freed slots). A deck at distance 0 with a commander is Brawl-ready
    as-is; pick the commander, add `#: commander:` + `#: format: Brawl`."""
    rows = brawl_readiness(fmt_filter=args.fmt)
    if not rows:
        print(f"No {args.fmt} decks to assess.")
        return 0
    ready = [r for r in rows if not r["no_commander"] and r["distance"] == 0 and not r["converted"]]
    done = [r for r in rows if r["converted"]]
    print(f"Brawl-readiness — {len(rows)} {args.fmt} deck(s), closest to a legal Brawl "
          f"conversion first. distance = duplicates-to-singleton + off-identity cards.")
    if done:
        print(f"Already converted (a *-brawl variant exists): "
              + ", ".join(f"{r['id']}" for r in done))
    print(f"\n  {'dist':>4} {'deck':>5} {'name':24} {'col':5} {'commander (identity)':34} {'dup':>3} {'stray':>5}")
    print("  " + "-" * 92)
    for r in rows:
        if r["no_commander"]:
            continue
        tag = " ✓" if r["converted"] else ""
        cmd = (f"{r['commander'][:26]} ({r['cmd_ident']})") if r["commander"] else "—"
        print(f"  {r['distance']:>4} {r['id']:>5} {r['name'][:24]:24} {r['colors']:5} "
              f"{cmd:34} {r['dup']:>3} {r['stray']:>5}{tag}")
    nocmd = [r for r in rows if r["no_commander"]]
    if nocmd:
        print(f"\n  No in-deck commander (needs a legendary creature/planeswalker added): "
              + ", ".join(f"{r['id']} {r['name'][:18]}" for r in nocmd[:10]))
    print("\nRead it like `rotation`/`audit` — a shortlist. distance 0 (+ commander) = "
          "ready as-is; a few strays = swap those for on-identity cards (deck.py legal "
          "<id> --format brawl names them). Copies are fungible, so a Brawl build costs "
          "no extra owned cards. Grade the commander from full text (deck.py text / card.py).")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Manage decks and variations.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list all decks and variants")
    sub.add_parser("wildcards", help="roster-wide crafting plan (wildcards to finish decks)")
    p = sub.add_parser("audit", help="roster-wide triage scorecard — which decks need a tune (offline)")
    p.add_argument("--flagged", action="store_true",
                   help="show only decks with a flag (hide the 'ok' rows)")
    p.add_argument("--by-tier", action="store_true",
                   help="sort by competitive tier (S→D, ungraded last) instead of by maintenance verdict")
    p = sub.add_parser("check", help="owned vs needed vs your collection")
    p.add_argument("id")
    p = sub.add_parser("diff", help="show what one deck changes vs another")
    p.add_argument("a"); p.add_argument("b")
    p = sub.add_parser("arena", help="emit an Arena-importable decklist")
    p.add_argument("id")
    p = sub.add_parser("stats", help="mana curve, colors, and type breakdown")
    p.add_argument("id")
    p = sub.add_parser("mana", help="hybrid-aware color requirements")
    p.add_argument("id")
    p = sub.add_parser("consistency",
                       # `%%`, not `%`: argparse renders a help string through
                       # `help % params`, so a bare `%` raises ValueError and takes
                       # the WHOLE top-level `--help` down with it (broad-scan F-01).
                       help="manabase + opening-hand probability (keepable %%, land drops, cast-on-curve)")
    p.add_argument("id")
    p.add_argument("--on-draw", action="store_true",
                   help="model on the draw (extra card) instead of on the play")
    p.add_argument("--target", type=float, metavar="P",
                   help="cast-probability target as a fraction (default 0.90)")
    p = sub.add_parser("tribes", help="creature-subtype breakdown + type-matters synergies")
    p.add_argument("id")
    p = sub.add_parser("engines", help="enabler vs payoff balance for the deck's engine themes")
    p.add_argument("id")
    p = sub.add_parser("targets", help="does the deck contain TARGETS for its own gated effects (MV caps, sacrifice costs, count thresholds)")
    p.add_argument("id")
    p = sub.add_parser("brawl", help="roster-wide Brawl-readiness — which decks are closest to a legal Brawl conversion")
    p.add_argument("--format", dest="fmt", default="standard",
                   help="which decks to assess (default: standard)")
    p = sub.add_parser("rotation", help="roster-wide Standard-rotation exposure — which decks run aging-out cards")
    p.add_argument("--format", dest="fmt", default="standard",
                   help="format to check rotation for (default: standard)")
    p.add_argument("--years", type=int, default=3,
                   help="rotation window in years (default: 3, Standard's rough window)")
    p.add_argument("--within", type=int, default=2,
                   help="how many years ahead to surface (default: 2 — what rotates next)")
    p = sub.add_parser("suggest", help="recommend pool cards that fit a deck's colors + themes")
    p.add_argument("id")
    p.add_argument("--limit", type=int, default=20,
                   help="max suggestions (default 20; 0 = unlimited)")
    p.add_argument("--format", dest="fmt", metavar="FMT",
                   help="only suggest cards legal in FMT (default: the deck's "
                        "#: format:). Needs a legality-aware pool (build_pool.py).")
    p.add_argument("--any-format", action="store_true",
                   help="don't filter suggestions by format legality")
    p.add_argument("--full", action="store_true",
                   help="also print full oracle text + keywords/flags of the picks "
                        "(grade adds from text, not the tag-match line)")
    p.add_argument("--lands", action="store_true",
                   help="recommend LANDS for the manabase (fixing value + a bounded "
                        "synergy/shortfall nudge) — the axis theme-based suggest is blind to")
    p.add_argument("--ramp", action="store_true",
                   help="recommend nonland MANA SOURCES (dorks/rocks) — fixing + acceleration "
                        "+ restriction-fit; the structural need theme-suggest can't see")
    p.add_argument("--interaction", action="store_true",
                   help="recommend INTERACTION incl. off-theme removal, with a bounded "
                        "board-scaling boost (fight/'damage = creatures you control'), flagged")
    p.add_argument("--needs", action="store_true",
                   help="unified STRUCTURAL-NEEDS view: fixing · acceleration · interaction")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--unowned", action="store_true", help="only craftable suggestions")
    g.add_argument("--owned", action="store_true",
                   help="only cards you already own (0 wildcards)")
    p = sub.add_parser("legal", help="deck-construction lint: size, copy limits, format legality")
    p.add_argument("id")
    p.add_argument("--format", dest="fmt", metavar="FMT",
                   help="check against FMT instead of the deck's #: format:")
    p = sub.add_parser("preflight", help="one-call verify: legal + owned + castable + integrity (for skills)")
    p.add_argument("id")
    p = sub.add_parser("quality", help="deck-quality vector + regression guard for a cut/swap (for skills)")
    p.add_argument("id")
    p.add_argument("--json", action="store_true", help="print the quality vector as JSON (snapshot before a change)")
    p.add_argument("--vs", metavar="FILE", help="diff against a saved --json snapshot and flag regressions")
    p.add_argument("--add", metavar="NAME", help="warn if adding NAME would be a merely-tangential fit")
    p.add_argument("--at", metavar="REF", help="compare this deck's list at a past git ref against now")
    p.add_argument("--strict", action="store_true", help="exit non-zero on any regression/weak-add (default: warn only)")
    p = sub.add_parser("history", help="show a deck file's git change history (its changelog)")
    p.add_argument("id")
    p.add_argument("--since", metavar="YYYY-MM-DD",
                   help="only commits on/after this date, plus the cumulative card-level "
                        "net change since then (what you still need to push to Arena)")
    p = sub.add_parser("tier", help="check a deck's claimed tier against its measurable quality floor")
    p.add_argument("id")
    p.add_argument("--strict", action="store_true", help="exit non-zero on a tier mismatch (default: warn only)")
    p.add_argument("--to", metavar="TIER", help="show the measurable gap + owned fillers to reach TIER's floor (S/A/B/C/D)")
    p.add_argument("--audit-rationale", action="store_true",
                   help="flag `#: tier:`/`#: notes:` prose that has gone stale — cards it "
                        "cites that are no longer in the deck, and figures that no longer "
                        "match the live quality vector")
    p = sub.add_parser("shape", help="wide vs tall, fast vs slow — the structural read themes can't give")
    p.add_argument("id")
    p = sub.add_parser("redundancy",
                       help="competitive-consistency planner: virtual (functional) copies first, duplicates as fallback")
    p.add_argument("id")
    p.add_argument("--target", type=int, metavar="N",
                   help=f"virtual-copy depth to aim each plan-effect at (default {_REDUNDANCY_TARGET})")
    p = sub.add_parser("cuts", help="rank the deck's weakest-fit cards as cut candidates")
    p.add_argument("id")
    p.add_argument("--limit", type=int, default=8,
                   help="how many cut candidates to show (default 8; 0 = all)")
    p = sub.add_parser("flex", help="show a deck's flex / suggested swaps (#~ lines)")
    p.add_argument("id")
    p = sub.add_parser("swap", help="preview/apply a single -cut/+add swap with deltas")
    p.add_argument("id")
    p.add_argument("--cut", required=True, help="card to remove")
    p.add_argument("--add", required=True, help="card to add")
    p.add_argument("--apply", action="store_true",
                   help="write the change (with a .bak); default is a dry-run preview")
    p = sub.add_parser("feedback",
                       help="how the recommenders scored against the swaps you applied")
    p.add_argument("id", nargs="?", help="limit to one deck (default: the whole roster)")
    p = sub.add_parser("apply-flex", help="promote a flex swap (#~ line) into the maindeck")
    p.add_argument("id")
    p.add_argument("n", type=int, help="which flex swap (1-based; see deck.py flex <id>)")
    p.add_argument("--apply", action="store_true",
                   help="write the change (with a .bak); default is a dry-run preview")
    p = sub.add_parser("verify", help="compare a pasted/piped Arena export against a stored deck")
    p.add_argument("id")
    p.add_argument("source", nargs="?", default="-",
                   help="path to an export file, or '-' / omitted to read stdin")
    p = sub.add_parser("sync", help="reconcile stored deck files FROM a pasted Arena export (many decks at once)")
    p.add_argument("source", nargs="?", default="-",
                   help="path to an export file, or '-' / omitted to read stdin")
    p.add_argument("--apply", action="store_true",
                   help="write the drifted deck files (with .bak); default is a dry run")
    p.add_argument("--force", action="store_true",
                   help="also write decks whose match was low-confidence (a variant sibling "
                        "was nearly as close) — check the diff first")
    p = sub.add_parser("text", help="dump every card's FULL oracle text (read before grading cuts/swaps)")
    p.add_argument("id")
    p = sub.add_parser("suggest-homes",
                       help="find which decks a card fits (castable + shared theme), with a cut")
    p.add_argument("card", help="card name to place across your decks")
    p.add_argument("--any-format", action="store_true",
                   help="don't filter to decks whose format the card is legal in")
    p = sub.add_parser("similar", help="rank the decks most similar to <id> (is it distinct?)")
    p.add_argument("id")
    p.add_argument("--limit", type=int, default=8, help="how many similar decks to show (default 8)")
    p.add_argument("--specific-only", action="store_true",
                   help="score SPECIFIC (identity) themes only — drop generic value overlap")
    p.add_argument("--full", action="store_true",
                   help="list the shared nonland CARD names — the concrete evidence behind "
                        "the theme cosine")
    p = sub.add_parser("resolve",
                       help="turn card names into deck lines `<qty> Name (SET) #` (from args or stdin)")
    p.add_argument("names", nargs="*",
                   help="card names (optional leading qty); omit or '-' to read stdin")
    p.add_argument("--format", default="standard",
                   help="warn about names not legal in this format (default standard; "
                        "'any' disables the check)")
    p = sub.add_parser("screen",
                       help="re-score candidate cards against a deck's CURRENT list; "
                            "flags strict upgrades of cards already in it")
    p.add_argument("id", help="deck id")
    p.add_argument("names", nargs="*",
                   help="card names (optional leading qty); omit or '-' to read stdin")
    p.add_argument("--format", default=None,
                   help="legality format (default: the deck's own; 'any' disables)")
    p.add_argument("--full", action="store_true",
                   help="print each candidate's full oracle text")
    args = ap.parse_args()

    return {
        "list": cmd_list, "wildcards": cmd_wildcards, "audit": cmd_audit, "check": cmd_check,
        "diff": cmd_diff, "arena": cmd_arena, "stats": cmd_stats,
        "mana": cmd_mana, "consistency": cmd_consistency,
        "tribes": cmd_tribes, "engines": cmd_engines, "targets": cmd_targets,
        "suggest": cmd_suggest,
        "rotation": cmd_rotation, "brawl": cmd_brawl,
        "legal": cmd_legal, "cuts": cmd_cuts,
        "shape": cmd_shape,
        "flex": cmd_flex, "swap": cmd_swap, "apply-flex": cmd_apply_flex,
        "verify": cmd_verify, "sync": cmd_sync, "text": cmd_text,
        "suggest-homes": cmd_suggest_homes,
        "similar": cmd_similar, "resolve": cmd_resolve, "screen": cmd_screen,
        "preflight": cmd_preflight, "quality": cmd_quality, "tier": cmd_tier,
        "redundancy": cmd_redundancy, "history": cmd_history,
        "feedback": cmd_feedback,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
