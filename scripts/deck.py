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

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint, card_colors, owned_qty
from scryfall import post_collection, ScryfallUnavailable

POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")

DECKS_DIR = os.path.join(REPO_ROOT, "decks")
MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")
BASICS = {"plains", "island", "swamp", "mountain", "forest", "wastes"}

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
META_RE = re.compile(r"^#:\s*([A-Za-z_]+)\s*:\s*(.*)$")

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


# --------------------------------------------------------------------------- #
# Collection lookup
# --------------------------------------------------------------------------- #
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
    if nl not in by_name_qty:
        return 0, False
    return by_name_qty[nl], True


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
            print(f"  [{d['id']:>4}] {tag:12} {label:28} {total:3} cards  {status}")
            ident = _deck_identity(d["meta"])
            if ident:
                print(f"          {ident}")
    return 0


# --- wildcard (crafting) planning ------------------------------------------- #
def load_rarities():
    """name_lower -> wildcard letter (C/U/R/M) from card-pool.csv's Rarity."""
    out = {}
    if not os.path.exists(POOL_CSV):
        return out
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            rar = (r.get("Rarity") or "").strip().lower()
            if n and rar:
                out.setdefault(n, WC_LETTER.get(rar, "?"))
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
    decks = discover_decks()
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


def _castability(cards, declared, mana, carddata):
    """Flag nonland cards whose color needs fall outside `declared` (a WUBRG set).

    Returns (uncastable, off_identity):
      uncastable   – [(name, "needs X")] : a STRICT pip, or a true multicolor
                     hybrid with NO in-declared-color option, in a color the deck
                     can't produce. These genuinely can't be cast off the stated
                     colors. (Needs real mana costs — pass a populated `mana`.)
      off_identity – [(name, "identity has X")] : castable as printed, but the
                     card's color IDENTITY strays outside declared (an off-color
                     ability, or a hybrid you'd pay on-color) — a softer heads-up.

    An empty `declared` disables the lint. With an empty `mana` dict the strict
    check is skipped and only the offline identity check runs (so `check` stays
    network-free)."""
    uncastable, off_ident = [], []
    if not declared:
        return uncastable, off_ident
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
            uncastable.append((n, "needs " + "/".join(sorted(set(off_strict + bad_hybrid)))))
            continue
        ident = card_colors(cd["colors"] if cd else "")
        stray = sorted(ident - declared)
        if stray:
            off_ident.append((n, "identity has " + "/".join(stray)))
    return uncastable, off_ident


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
    _, off_ident = _castability(cards, declared, {}, load_card_data())
    if declared and off_ident:
        cols = "".join(sorted(declared))
        print(f"\n⚠ {len(off_ident)} card(s) stray outside the deck's {cols} colors "
              f"(run `deck.py mana {d['id']}` for castability detail):")
        for n, why in off_ident:
            print(f"    {n} — {why}")
    return 1 if (missing or short) else 0


def _multiset(cards):
    """{name_lower: (display_name, total_qty)} — keyed case-insensitively (like
    every other command) so the SAME card spelled with different casing across two
    files isn't reported as a spurious −N / +N change (audit F4). The first-seen
    spelling is kept for display."""
    m = {}
    for q, n, s, c in cards:
        nl = n.lower()
        disp, cur = m.get(nl, (n, 0))
        m[nl] = (disp, cur + q)
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
            mv = (r.get("Mana Value") or "").strip()
            out[n] = (r.get("Mana Cost") or "", int(mv) if mv.isdigit() else None)
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
    """
    strict, hybrid = {}, []
    for sym in SYMBOL_RE.findall(cost or ""):
        colors = set(ch for ch in sym.upper() if ch in "WUBRG")
        if "/" in sym:
            if colors:
                hybrid.append(frozenset(colors))
        elif len(colors) == 1:
            (c,) = colors
            strict[c] = strict.get(c, 0) + 1
    return strict, hybrid


def _primary_type(type_line):
    order = ["Land", "Creature", "Planeswalker", "Battle", "Artifact",
             "Enchantment", "Instant", "Sorcery"]
    for t in order:
        if t.lower() in type_line.lower():
            return t
    return "Other"


# --- card data (type + text) for synergy / cost analysis -------------------- #
def load_card_data():
    """name_lower -> {'type', 'text'} from card-library.csv then card-pool.csv.

    The pool fills in oracle text/type for unowned WIP cards so analysis works on
    decks that aren't fully owned yet.
    """
    data = {}
    for path in (DEFAULT_CSV, POOL_CSV):
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                n = (r.get("Card Name") or "").strip().lower()
                if n and n not in data:
                    data[n] = {"name": (r.get("Card Name") or "").strip(),
                               "type": r.get("Type") or "", "text": r.get("Card Text") or "",
                               "colors": r.get("Color(s)") or ""}
                    data.setdefault(n.split(" // ")[0], data[n])
    return data


def creature_subtypes(type_line):
    """Creature subtypes (after the em dash) across all faces of a type line."""
    subs = []
    for face in type_line.split("//"):
        if "creature" in face.lower() and "—" in face:
            subs += face.split("—", 1)[1].split()
    return subs


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
_ROLE_PATTERNS = {
    "Removal (spot)": [
        r"destroy target (?:creature|permanent|nonland permanent|artifact or creature|"
        r"tapped creature|attacking creature|creature or planeswalker|creature with)",
        r"exile target (?:creature|permanent|nonland permanent|attacking|tapped)",
        # "destroy/exile up to one/two target ..." — the fixed "target" patterns above
        # miss the up-to-N wording (She-Hulk's power-up, Mutant Chain Reaction).
        r"(?:destroy|exile) up to \w+ target (?:creature|permanent|nonland permanent|"
        r"artifact|enchantment|planeswalker|artifact or|artifact, enchantment)",
        r"deals? \d+ damage to (?:target|any target|another target)",
        r"deals? \d+ damage to up to \w+ target",
        # any "fight" is removal (Novel Nunchaku "fights up to one target", Longstalk
        # Brawl "fight each other") — the old pattern only caught "fights target".
        r"\bfights?\b|creatures? fight",
        r"deals damage equal to (?:twice )?.{0,20}?power to target (?:creature|creature or planeswalker|attacking)",
        # -N/-N or -X/-X shrink on a targeted creature (incl. "creature an opponent
        # controls gets -X/-X" — Cloud of Darkness, Wick's Patrol).
        r"target creature (?:an opponent controls )?gets -[0-9x]",
        r"creature an opponent controls gets -[0-9x]",
        r"return target creature.{0,40}?(?:owner|their) hand",
        r"enchanted creature can't attack or block",
    ],
    "Sweeper": [r"destroy all", r"exile all", r"all creatures get -",
                r"each (?:other )?creature (?:gets|deals|is|you don't control)",
                # one-sided / opponent-only wraths ("creatures your opponents control
                # get -2/-2" — Massacre Wurm) the "all creatures" pattern misses.
                r"creatures (?:you don't control|your opponents control|target player controls) get -",
                # scalable / conditional wipes the fixed patterns above miss
                r"creature with mana value.{0,20}?or less.{0,40}?destroy",
                r"destroy those creatures",
                r"deals? \d+ damage to each (?:other )?creature"],
    "Counter": [r"counter target"],
    "Card advantage": [r"draws? (?:two|three|four|x|that many) cards?",
                       r"draw a card for each", r"draws? cards? equal to",
                       r"\binvestigate\b"],
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
        r"loses life equal to",
    ],
    "Lifegain": [r"\blifelink\b", r"you gain \d+ life", r"gain \d+ life"],
    # Cost reducers / free-cast enablers — the value that makes a nominally
    # expensive card cheap (Diamond Weapon, affinity/convoke, cascade cheats).
    "Cost reduction / cheat": [
        r"costs? \{[0-9x]+\} less",
        r"costs? \{1\} less for each",
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
        missed = []
        if _INT_CUES.search(text) and not (roles & _INTERACTION_ROLES):
            missed.append("interaction")
        if _CA_CUES.search(text) and "Card advantage" not in roles:
            missed.append("card advantage")
        if missed:
            under_read.append((n, "/".join(missed)))
        elif not roles and "Creature" not in (cd.get("type") or ""):
            unclassified.append(n)
    return unclassified, under_read, no_data


def classify_roles(text):
    """Return the set of functional-role labels a card's oracle text matches."""
    t = (text or "").lower().replace("−", "-")  # normalize unicode minus
    return {label for label, pats in _ROLE_COMPILED if any(p.search(t) for p in pats)}


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
        print(f"  {'interaction total':20} {role_counts['interaction']:3}  "
              "(distinct removal/sweeper/counter cards)")

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


def _central_themes(theme_w, frac=0.25):
    """The themes that are actually CENTRAL to a deck: those carried by at least a
    quarter of the deck's most-common theme's copies (floor of 2 copies). Filters
    out one-off tag overlaps so a generic sac/tokens card doesn't read as fitting a
    deck it only grazes."""
    if not theme_w:
        return set()
    cutoff = max(2, frac * max(theme_w.values()))
    return {t for t, w in theme_w.items() if w >= cutoff}


# Themes carried by nearly every deck — low signal for how KEY a fit is (mirrors
# wishlist.NON_SIGNAL_TAGS's intent, kept local so deck.py has no wishlist import).
GENERIC_THEMES = {
    "etb", "tokens", "counters", "lifegain", "sacrifice", "card draw", "graveyard",
    "mana", "ramp", "combat", "aggro", "tempo", "pump", "removal", "evasion",
    "flying", "trample", "menace", "deathtouch", "lifelink", "vigilance",
}
_INTERACTION_ROLES = {"Removal (spot)", "Sweeper", "Counter"}


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
    union of Removal/Sweeper/Counter) and 'card_advantage'."""
    per_role = {}
    interaction = ca = 0
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
    per_role["interaction"] = interaction
    per_role["card_advantage"] = ca
    return per_role


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

      KEY          – shares the deck's SIGNATURE (top central theme, OR a theme
                     carried by the deck's `#: protect:` cards) on a specific theme,
                     OR fills a role the deck is short on (interaction < 5 /
                     card advantage < 3).
      tangential   – shares only GENERIC themes (etb/tokens/…): low real signal.
      role-player  – shares a specific central theme, but not the signature.

    `signature` (from `_signature_themes`) corrects the idf blind spot: a theme in
    GENERIC_THEMES is still SPECIFIC-for-this-deck if the deck protects cards built
    on it — so a counter-doubler in a counters deck reads KEY, not tangential.
    """
    specific = [t for t in shared if t.lower() not in GENERIC_THEMES or t in signature]
    roles = set(classify_roles(card_text or ""))
    gap = (bool(roles & _INTERACTION_ROLES) and deck_int < 5) or \
          ("Card advantage" in roles and deck_ca < 3)
    if gap:
        return "KEY"
    if signature and any(t in signature for t in shared):
        return "KEY"
    if not specific:
        return "tangential"
    top = max(theme_w.values()) if theme_w else 0
    if top and any(theme_w.get(t, 0) >= top for t in specific):
        return "KEY"
    return "role-player"


def _deck_fingerprints(meta, exclude_id=None):
    """[(id, colors:set, central_themes:set), ...] for every deck — used to score a
    craft target's cross-deck reuse (a card that fits several of your decks is worth
    more per wildcard). Colors are the deck's declared `#: colors:` (else the union
    of its cards' identities); themes are the deck's CENTRAL synergy tags (weighted
    by copies, then thresholded via _central_themes) rather than every tag that
    appears once — so reuse counts a deck only when the card is genuinely on-theme
    for it, not merely sharing an incidental keyword.

    `exclude_id` drops one deck from the roster (the deck being analyzed), so a
    suggestion's reuse count is 'how many OTHER decks it fits' — otherwise the
    current deck always counts itself and inflates every score by one."""
    fps = []
    for dd in discover_decks():
        if exclude_id is not None and dd["id"].lower() == exclude_id.lower():
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
        fps.append((dd["id"], colors or ident, _central_themes(theme_w)))
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


def rotation_risk(released, years=3):
    """True if a set released more than ~`years` ago — Standard's rough rotation
    window — so a still-`standard`-marked pick may have rotated (stale pool) or
    rotates soon. Empty/absent `released` → False (graceful before a pool rebuild
    captures the Released column)."""
    if not released:
        return False
    try:
        import datetime
        rel = datetime.date.fromisoformat(released[:10])
        return (datetime.date.today() - rel).days > 365 * years
    except Exception:
        return False


def rotation_year(released, years=3):
    """The year a set rotates out of Standard — its release year + `years` (Standard's
    ~3-year window) — or None if the date is blank/unparseable. The single primitive
    behind both `rotation_sweep` and the wishlist ⚠rot flag, so 'when does this rotate'
    is computed one way everywhere."""
    try:
        return int((released or "")[:4]) + years
    except (ValueError, TypeError):
        return None


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
    for d in discover_decks():
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
            rotates = rotation_year(released, years)
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
    converted = {d["core"] for d in discover_decks()
                 if str(d["id"]).endswith("-brawl")}
    fmt_filter = (fmt_filter or "").strip().lower()
    rows = []
    for d in discover_decks():
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
        ccolors = card_colors(r.get("Color(s)"))
        if not ccolors.issubset(deck_colors):
            continue  # off-color for this deck
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
    # Rank: strongest theme fit first; owned as a tiebreaker so quick adds float up.
    suggestions.sort(key=lambda x: (-x[0], -min(owned_of(x[1].lower()), 1), x[1].lower()))
    top = suggestions if limit == 0 else suggestions[:limit]

    fps = _deck_fingerprints(meta, exclude_id=d["id"])
    picks, hi_reuse = [], []
    for score, name, r, shared in top:
        h = owned_of(name.lower())
        card_cols = card_colors(r.get("Color(s)"))
        card_themes = {t.strip() for t in (r.get("Synergies") or "").split(";") if t.strip()}
        fits = sum(1 for _id, dc, dt in fps if card_cols <= dc and (card_themes & dt))
        if h == 0 and fits >= 3:
            hi_reuse.append((name, fits))
        picks.append({"name": name, "rarity": (r.get("Rarity") or "").strip(),
                      "owned": h, "decks": fits, "score": score, "matches": shared,
                      "rotates": rotation_risk(r.get("Released") or "")})

    res.update(ok=True, colors=deck_colors,
               themes=sorted(theme_w.items(), key=lambda kv: -kv[1])[:6],
               fmt=fmt, apply_fmt=apply_fmt, has_leg=has_leg,
               picks=picks, total=len(top), hi_reuse=hi_reuse)
    return res


def cmd_suggest(args):
    """Recommend pool cards that fit a deck's color identity and synergy themes.

    Scores each candidate by how strongly its tags overlap the deck's themes
    (weighted by how central each theme is to the deck), filters to the deck's
    colors, and flags owned vs. craftable with wildcard rarity. Composes
    card-pool.csv + the synergy tags + tribes-style theme matching. Rendering only —
    the scoring lives in suggest_scored() so the dashboard shares it verbatim.
    """
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    if not os.path.exists(POOL_CSV):
        eprint("No card-pool.csv. Build it: python3 scripts/build_pool.py")
        return 1

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
          "CENTRAL theme with (higher = more value per wildcard).")
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
        uncastable, off_ident = _castability(cards, declared, mana, load_card_data())
        cols = "".join(sorted(declared))
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
        want = "more" if nlands < N * 0.40 else "fewer"
        print(f"  △ keepable {100*ls['keepable']:.0f}% is low — consider {want} lands "
              f"(most 60-card decks run 23–26).")

    # Color sources.
    active = [c for c in "WUBRG" if sources[c]]
    if active:
        print("\nColor sources (lands producing each color):")
        print("  " + "   ".join(f"{c} {sources[c]}" for c in active))

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
            flag = ""
            if p < target and need > sources.get(worst_col, 0):
                flag = (f"   → want {need} {worst_col} sources "
                        f"(have {sources.get(worst_col, 0)}, +{need - sources.get(worst_col, 0)})")
            print(f"  {100*p:5.1f}%  T{turn}  {pipstr:10} {n[:30]:30}{flag}")
        if below:
            print(f"\n  {len(below)} card(s) below {100*target:.0f}% on curve — the "
                  "→ note is the Karsten source count to reach target for the tight color.")
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
    return 0


# --- swap preview / apply (and flex promotion) ------------------------------ #
def _printing_of(name):
    """Best-known (set, collector#) for a card name: an owned library printing
    first (so the added line matches something you have), else any known
    printing. ('', '') if unknown — a bare '1 Name' line still parses/checks."""
    nl = name.strip().lower()
    best = ("", "")
    for path, owned_pref in ((DEFAULT_CSV, True), (POOL_CSV, False)):
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if (r.get("Card Name") or "").strip().lower() != nl:
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
                        return (setc, cn)      # an owned printing wins outright
                if best == ("", ""):
                    best = (setc, cn)
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
    expected) -> timestamped .bak -> atomic replace. Returns the .bak path."""
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
        bak = f"{target}.{time.strftime('%Y%m%d-%H%M%S')}.bak"
        shutil.copy2(target, bak)
        os.replace(tmp, target)
        tmp = None
        return bak
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


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
    add_pr = _printing_of(add)
    after = _cards_after_swap(cards, cut, add, add_pr)
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

    with open(d["path"], encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    try:
        new_lines = _swap_edit_lines(lines, cut, add, add_pr, drop_flex=flex_entry)
        bak = _safe_write_lines(d["path"], new_lines, before_s["total"])
    except ValueError as e:
        eprint(f"Not saved: {e}")
        return 1
    print(f"\nApplied. Wrote {os.path.relpath(d['path'], REPO_ROOT)} "
          f"(backup: {os.path.basename(bak)}).")
    if flex_entry is not None:
        print("Removed the consumed flex line.")
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


def rank_cut_candidates(d):
    """Rank a deck's nonland cards most→least cuttable and return
    (rows_sorted, central, prot_present, deck_int). Each row is
    (keep, name, mv, roles, fit, reasons, ctx, text, is_int, power) — the shared
    ranking behind both `cmd_cuts` (which prints it) and the tier `--to` tune plan
    (which pairs the weakest cuts with the fillers that close a tier gap). Higher
    `keep` = keep; lower sorts to the top of the cut list."""
    meta, cards = parse_deck_file(d["path"])
    protected = _protected(meta)
    cardmeta = load_card_meta()
    carddata = load_card_data()
    mana = load_mana()
    rar = load_rarities()

    # Deck theme weights (by copies) — the same fingerprint `suggest` uses.
    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = cardmeta.get(n.lower())
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    central = _central_themes(theme_w)
    signature = _signature_themes(meta, cards, cardmeta)   # #: protect: spine (F#3)
    deck_tally = role_tally(cards, carddata)               # role → copies the deck runs
    deck_int = deck_tally["interaction"]                   # for the F#1 interaction guard

    # Deck creature subtypes (for the tribal-contribution signal).
    sub_count = {}
    for q, n, s, c in cards:
        cd = carddata.get(n.lower())
        if cd:
            for st in creature_subtypes(cd["type"]):
                sub_count[st] = sub_count.get(st, 0) + q

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
        fit, hit_central = 0, False
        for t in tags:
            if t in theme_w:
                fit += theme_w[t]
                if t in central:
                    hit_central = True
        text = cd["text"] if cd else ""
        roles = classify_roles(text)
        subs = set(creature_subtypes(tline))
        tribal = sum(sub_count.get(st, 0) for st in subs)  # includes own copies
        cost, mv = (mana.get(nl) or (None, None))
        ctx = context_flags(text, cost)
        sig_hit = bool(set(tags) & signature)          # shares the deck's protected spine
        is_int = bool(set(roles) & _INTERACTION_ROLES)  # removal / sweeper / counter

        # Card-quality co-signal (#3): the wishlist's rarity+role power estimate, so an
        # on-theme-but-WEAK card sorts UP the cut list and an on-theme BOMB is protected —
        # something pure theme-fit can't distinguish (a vanilla and a bomb sharing one tag
        # look equal). Bounded (±_CUTS_POWER_CAP), so it only breaks near-ties (see
        # _cuts_power_adj / check_suggest #7); it never overrides theme fit.
        power = _power_seed({"Rarity": rar.get(nl, ""), "Card Text": text, "Type": tline})
        pow_adj = _cuts_power_adj(power)

        # keep-score: higher = keep; cut candidates sort to the top (lowest keep).
        # Role credit is impact-weighted (see _role_credit) so a strong-but-off-theme
        # card (removal/engine/cost-reducer) isn't mis-ranked as a top cut. Passing the
        # deck's role tally makes that credit SATURATION-aware (#1): a redundant piece
        # (the 8th removal spell) loses most of its bonus and sorts UP the cut list,
        # while the deck's ONLY counterspell keeps full credit and stays protected. A
        # card on the deck's #: protect: signature theme gets a further keep-boost (F#3)
        # so a generic-tagged-but-central theme (e.g. counters) isn't mistaken for filler.
        keep = (fit + _role_credit(roles, deck_tally) + (1 if hit_central else 0)
                + (2 if sig_hit else 0) + min(tribal, 6) + pow_adj)
        reasons = []
        if tags and not hit_central:
            reasons.append("off the deck's central themes")
        elif not tags:
            reasons.append("no synergy tags")
        if not roles:
            reasons.append("role not auto-detected — read text")
        if subs and tribal <= q:
            reasons.append("off-tribe")
        if power <= 3.0 and (hit_central or sig_hit):
            reasons.append(f"on-theme but low power (~{power:.1f})")
        rows.append((keep, n, mv, sorted(roles), fit, reasons, ctx, text, is_int, power))

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
    print(f"  {'Card':30} {'MV':>3}  {'Fit':>4}  {'Pw':>3}  Roles / why-cuttable")
    print("-" * 78)
    for keep, n, mv, roles, fit, reasons, ctx, text, is_int, power in rows[:limit]:
        mvs = str(mv) if mv is not None else "?"
        tail = ", ".join(roles) if roles else ("; ".join(reasons) if reasons else "—")
        low_pow = [r for r in reasons if r.startswith("on-theme but low power")]
        if roles and low_pow:  # a detected-role card can still be a weak body — say so
            tail += "  ·  " + low_pow[0]
        if ctx:
            tail += f"   ⚠ context: {'/'.join(ctx)}"
        if is_int:
            tail += f"   ⚠interaction (deck runs {deck_int})"
        print(f"  {n[:30]:30} {mvs:>3}  {fit:>4}  {power:>3.0f}  {tail}")

    # Surface the actual oracle text so a cut is graded from what the card DOES,
    # never from the label above (the role map is a shortlist, not a verdict).
    import textwrap
    text_n = args.limit if getattr(args, "limit", 0) and args.limit > 0 else min(12, len(rows))
    print(f"\n── Oracle text of the top {min(text_n, len(rows))} cut candidates "
          f"(grade from THIS, not the label) ──")
    for keep, n, mv, roles, fit, reasons, ctx, text, is_int, power in rows[:text_n]:
        warn = f"   ⚠ context: {'/'.join(ctx)} — value depends on this deck" if ctx else ""
        if is_int:
            warn += f"   ⚠interaction — 1 of the deck's {deck_int}"
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
    uncast, off_ident = _castability(cards, declared, mana, carddata)

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
    elif off_ident or thin:
        verdict = "review"
        if off_ident:
            reasons.append(f"off-color ×{len(off_ident)}")
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
    decks = discover_decks()
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
        cast_cell = "✓" if not (r["uncast"] or r["stray"]) else \
            " ".join(([f"{r['uncast']}u"] if r["uncast"] else [])
                     + ([f"{r['stray']}s"] if r["stray"] else []))
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
          f"Own/Legal ✓ clean · Cast Nu=uncastable Ns=off-identity stray · "
          f"Int=removal+sweeper+counter · Thm=central themes")
    print(f"Summary: {len(tune)} to tune · {len(craft)} to craft · "
          f"{len(review)} to review · {len(scored) - len(tune) - len(craft) - len(review)} ok")
    if tune:
        print(f"\nFull-tune candidates (hard flags): {', '.join(tune)}")
        print("  → run: python3 scripts/deck.py text <id>  then  /tune-deck <id>")
    if review:
        print(f"Worth a look (soft flags): {', '.join(review)}")
    return 0


def _weakest_cut(dmeta, cards, cardmeta, carddata):
    """The single most-cuttable nonland card in a deck (lowest theme-fit + role
    score), skipping `#: protect:` cards — a hint for suggest-homes. Run
    `deck.py cuts` for the full, oracle-text-graded shortlist."""
    protected = _protected(dmeta)
    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = cardmeta.get(n.lower())
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    central = _central_themes(theme_w)
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
        fit = sum(theme_w.get(t, 0) for t in tags if t in central)
        keep = fit + _role_credit(classify_roles(cd["text"] if cd else ""))
        if best is None or keep < best[0]:
            best = (keep, n)
    return best[1] if best else None


_FIXER_TAGS = {"ramp", "mana"}
_FIXER_CUES = (
    "any color", "any type", "every basic land type", "all basic land types",
    "each basic land type", "mana of any", "as though it were mana of any color",
    "spend mana of any type",
)


def _fixer_boost(ncolors, per_color=4, cap=5):
    """Bounded fit bump for a rainbow fixer in an `ncolors`-color deck — grows with
    the color count (a fixer earns more in a 5-color deck than a 3-color one) but is
    CAPPED (at `cap` colors) so it nudges ordering among fixer-eligible decks without
    ever dwarfing a genuine theme match. Returns 0 below 3 colors (mono/two-color
    decks don't need the fixing)."""
    if ncolors < 3:
        return 0
    return min(ncolors, cap) * per_color


def _is_color_fixer(ctags, text):
    """True when a card's value is multi-color mana FIXING whose worth SCALES with a
    deck's color count — a rainbow fixer (Overlord's every-basic-land-type token,
    Vizier's 'spend mana as though any color', a Triome-maker). A theme-overlap model
    can't see fixing (it isn't a 'theme'), and its value is proportional to how many
    colors the target deck must cast — so `suggest-homes` under-rates it in exactly
    the 3+-color decks that want it most (the Overlord → decks 17/21a miss). Gated on
    BOTH a fixing tag (ramp/mana) AND explicit rainbow text, so a mono-color ramp
    spell ('add {G}{G}') never qualifies."""
    if not ({t.lower() for t in ctags} & _FIXER_TAGS):
        return False
    t = (text or "").lower()
    return any(cue in t for cue in _FIXER_CUES)


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
        eprint(f"{card!r} not found in card-library.csv or card-pool.csv — check spelling.")
        return 1
    ccols = card_colors(cd.get("colors"))
    ctags = set(cardmeta.get(card.lower(), {}).get("synergies", []))
    is_fixer = _is_color_fixer(ctags, cd.get("text") or "")

    print(f"Card: {card}  [{'/'.join(sorted(ccols)) or 'Colorless'}]  ({cd['type']})")
    print(f"Themes: {', '.join(sorted(ctags)) or '(none)'}"
          f"{'   [rainbow fixer — value scales with a deck’s color count]' if is_fixer else ''}\n")

    results = []
    for dd in discover_decks():
        dmeta, cards = parse_deck_file(dd["path"])
        castable = _deck_castable_colors(dmeta, cards, mana)
        if not ccols.issubset(castable):
            continue
        theme_w = {}
        for q, n, s, c in cards:
            if n.lower() in BASICS:
                continue
            m = cardmeta.get(n.lower())
            if m:
                for t in m["synergies"]:
                    theme_w[t] = theme_w.get(t, 0) + q
        shared = sorted(ctags & _central_themes(theme_w))
        if not shared:
            continue
        already = card.lower() in {n.lower() for _, n, _, _ in cards}
        fit = sum(theme_w.get(t, 0) for t in shared)
        d_int, d_ca = deck_role_counts(cards, carddata)
        sig = _signature_themes(dmeta, cards, cardmeta)
        strength = fit_strength(shared, theme_w, cd.get("text") or "", d_int, d_ca, sig)
        # Color-fixer overlay: a rainbow fixer's worth scales with the deck's color
        # count, which theme-overlap can't see. In a 3+-color deck it's at least a
        # role-player manabase upgrade; in a 4+-color deck it's a KEY one (the fixing
        # is doing real work every game). The fit bump is BOUNDED (fixer_boost) so it
        # nudges ordering among fixer-eligible decks without dwarfing a real theme
        # match; the strength promotion never DEMOTES a fit fit_strength already rated
        # KEY. This closes the Overlord → 17/21a miss without touching mono-color decks.
        if is_fixer and len(castable) >= 3:
            fit += _fixer_boost(len(castable))
            if len(castable) >= 4:
                strength = "KEY"
            elif strength == "tangential":
                strength = "role-player"
        cut = None if already else _weakest_cut(dmeta, cards, cardmeta, carddata)
        results.append((fit, dd["id"], already, shared, cut, strength))

    if not results:
        print("No deck is both castable and shares a central theme with this card.\n"
              "(Off-color everywhere, or its themes are too generic — try "
              "`deck.py suggest <id>` from a specific deck instead.)")
        return 0
    # Sort KEY fits first (then role-player, then tangential), then by fit weight —
    # so the decks the card most belongs in lead, differentiating a key from a
    # tangential home (F04).
    _srank = {"KEY": 0, "role-player": 1, "tangential": 2}
    results.sort(key=lambda r: (_srank.get(r[5], 3), -r[0], r[1]))
    print(f"  {'deck':5} {'strength':11} {'fit':>4}  {'in?':3}  shared themes  ·  suggested cut")
    print("  " + "-" * 82)
    for fit, did, already, shared, cut, strength in results:
        tag = "yes" if already else "no"
        hint = "already maindecked" if already else (f"cut ~ {cut}" if cut else "")
        print(f"  {did:5} {strength:11} {fit:>4}  {tag:3}  {', '.join(shared[:3]):28}  {hint}")
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
    uncast, _off = _castability(cards, declared, mana, carddata)
    d_int, d_ca = deck_role_counts(cards, carddata)
    return {
        "buildable": missing == 0 and short == 0, "missing": missing, "short": short,
        # Whether castability was audited against a DECLARED identity. Without a
        # `#: colors:` header, `declared` is derived from the deck's own cards, so
        # uncastable is 0 by construction (unverified, not a clean bill) — audit F16.
        "colors_declared": bool(declared_hdr),
        "uncastable": len(uncast), "interaction": d_int, "card_advantage": d_ca,
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
        sig = _signature_themes(dmeta, cards, cardmeta)
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


def tier_band(vec):
    """The tier FLOOR (S/A/B/C/D) a deck's measurable quality vector supports.
    Metrics-only and blind to bombs/meta, so it under-rates by design — used to flag
    a claimed tier sitting ≥2 bands above it, never to assign a tier.

    It rates the LIST's competitive power independent of whether the cards are owned
    — tier is a power judgment, and build-state (ownership) is tracked separately by
    `check`/`audit`, so an aspirational unbuilt list is graded on its merits. A
    castability stray IS a list flaw (a dead card), so it caps the floor."""
    if vec["uncastable"] > 0:
        return "C"                        # castability strays cap the floor
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
        return "A"                        # measurable ceiling; S is a human call on top
    if ir >= 3 and resil >= 4:
        return "B"
    if resil >= 2:
        return "C"
    return "D"


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
    declared/derived colors, so it won't surface an uncastable pick."""
    meta, cards = parse_deck_file(d["path"])
    mana, carddata = load_mana(), load_card_data()
    _, _, qty = load_collection()
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
        hit = set(classify_roles(cd.get("text") or "")) & set(roles)
        if not hit:
            continue
        entry = mana.get(nl)
        mv = entry[1] if entry and entry[1] is not None else 99
        out.append((mv, name, "".join(sorted(ident)) or "C", sorted(hit),
                    (cd.get("text") or "").split("\n")[0][:64]))
    out.sort(key=lambda r: (r[0], r[1]))
    return out[:limit]


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
    for d in discover_decks():
        claimed, implied, mismatch, msg = tier_consistency(d)
        if mismatch:
            out.append((d["id"], claimed, implied, msg))
    return out


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
    print(f"Tier — deck {d['id']}: {d['name'] or d['path']}")
    print(f"  claimed tier  : {claimed or '(untiered)'}")
    print(f"  metrics floor : {implied}   (measurable-only — blind to bombs/meta, so it under-rates)")
    print(f"  plan          : {vec.get('plan', 'midrange')}"
          + (f"  ·  clock {_clock_score(vec)}/7 (curve/threats/reach substitutes for interaction)"
             if vec.get('plan') == 'aggro' else "  (floor weights interaction + card advantage)"))
    print(f"  vector        : buildable {vec['buildable']} · uncastable {vec['uncastable']} · "
          f"interaction {vec['interaction']} · card-adv {vec['card_advantage']} · "
          f"avg MV {vec['avg_mv']} · central themes {vec['central_themes']}")
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
    if gap <= -1:
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
            if owned_f:
                print(f"\n  owned on-color {label} to add (0 wildcards, {len(owned_f)} shown):")
                for mv, name, ident, hit, txt in owned_f:
                    print(f"    MV{mv:>2} {name:30} [{ident:4}] {','.join(hit):18} {txt}")
            else:
                print(f"\n  (no owned on-color {label} found)")
            # Craft targets — the wildcard-spend options, cheaper rarity first.
            craft = craft_role_fillers(d, role_set, limit=6)
            if craft:
                print(f"  craft targets ({label}, format-legal, cheaper wildcard first):")
                for rk, mv, name, ident, rar, txt in craft:
                    print(f"    {rar[:1] or '?'} MV{mv:>2} {name:28} [{ident:4}] {txt}")
            # Reserve `add_flag` fillers for the assembled plan — owned before craft.
            picks = [(label, "owned", mv, name, ident, "0 WC") for mv, name, ident, _h, _t in owned_f]
            picks += [(label, "craft", mv, name, ident, f"{rar[:1] or '?'} craft")
                      for _rk, mv, name, ident, rar, _t in craft]
            adds.extend(picks[:add_flag])

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
                cut_name, cut_mv, cut_roles, cut_is_int = cut[1], cut[2], cut[3], cut[8]
                cut_ca = "Card advantage" in cut_roles
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
                    warn = "  ⚠ cut feeds card advantage"
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
    uncast, off_ident = _castability(cards, declared, mana, carddata)

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
          + (f" (+{len(off_ident)} hybrid stray, ok)" if off_ident else ""))
    print(f"  integrity (check_all): {mark(integ_ok)}")
    hard = (not legal_ok) or bool(uncast) or (not integ_ok)
    print(f"Verdict: {'BLOCKED' if hard else 'READY'}")
    return 1 if hard else 0


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
                       help="manabase + opening-hand probability (keepable %, land drops, cast-on-curve)")
    p.add_argument("id")
    p.add_argument("--on-draw", action="store_true",
                   help="model on the draw (extra card) instead of on the play")
    p.add_argument("--target", type=float, metavar="P",
                   help="cast-probability target as a fraction (default 0.90)")
    p = sub.add_parser("tribes", help="creature-subtype breakdown + type-matters synergies")
    p.add_argument("id")
    p = sub.add_parser("engines", help="enabler vs payoff balance for the deck's engine themes")
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
    p = sub.add_parser("apply-flex", help="promote a flex swap (#~ line) into the maindeck")
    p.add_argument("id")
    p.add_argument("n", type=int, help="which flex swap (1-based; see deck.py flex <id>)")
    p.add_argument("--apply", action="store_true",
                   help="write the change (with a .bak); default is a dry-run preview")
    p = sub.add_parser("verify", help="compare a pasted/piped Arena export against a stored deck")
    p.add_argument("id")
    p.add_argument("source", nargs="?", default="-",
                   help="path to an export file, or '-' / omitted to read stdin")
    p = sub.add_parser("text", help="dump every card's FULL oracle text (read before grading cuts/swaps)")
    p.add_argument("id")
    p = sub.add_parser("suggest-homes",
                       help="find which decks a card fits (castable + shared theme), with a cut")
    p.add_argument("card", help="card name to place across your decks")
    args = ap.parse_args()

    return {
        "list": cmd_list, "wildcards": cmd_wildcards, "audit": cmd_audit, "check": cmd_check,
        "diff": cmd_diff, "arena": cmd_arena, "stats": cmd_stats,
        "mana": cmd_mana, "consistency": cmd_consistency,
        "tribes": cmd_tribes, "engines": cmd_engines, "suggest": cmd_suggest,
        "rotation": cmd_rotation, "brawl": cmd_brawl,
        "legal": cmd_legal, "cuts": cmd_cuts,
        "flex": cmd_flex, "swap": cmd_swap, "apply-flex": cmd_apply_flex,
        "verify": cmd_verify, "text": cmd_text, "suggest-homes": cmd_suggest_homes,
        "preflight": cmd_preflight, "quality": cmd_quality, "tier": cmd_tier,
        "history": cmd_history,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
