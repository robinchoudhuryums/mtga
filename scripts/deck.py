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
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint
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
    return {ch for ch in (meta.get("colors") or "").upper() if ch in "WUBRG"}


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
            cols |= set(strict) | {x for h in hybrid for x in h}
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
        colstr = ((cd["colors"] if cd else "") or "").strip()
        ident = set() if colstr.lower() == "colorless" else \
            {ch for ch in colstr.upper() if ch in "WUBRG"}
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
                    data[n] = {"type": r.get("Type") or "", "text": r.get("Card Text") or "",
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
        r"deals? \d+ damage to (?:target|any target|another target)",
        r"deals? \d+ damage to up to \w+ target",
        r"fights? (?:target|another target)",
        r"deals damage equal to (?:twice )?.{0,20}?power to target (?:creature|creature or planeswalker|attacking)",
        r"target creature gets -\d",
        r"return target creature.{0,40}?(?:owner|their) hand",
        r"enchanted creature can't attack or block",
    ],
    "Sweeper": [r"destroy all", r"exile all", r"all creatures get -",
                r"each (?:other )?creature (?:gets|deals|is|you don't control)",
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


def _role_credit(roles):
    """Keep-score credit for a card's functional roles: base 3 each, +6 more for each
    IMPACT role, so a card that does a high-value job clears the no-role 'filler' band
    (theme-fit only, ~0–8) and doesn't rank as a top cut. It can't fully offset a large
    theme-fit gap — an off-theme power card (Cosmic Cube, The Ten Rings) still sorts
    low in a tuned deck, which is inherent to a synergy model and exactly why `cuts`
    prints full oracle text and wishlist ranking pairs fit with a hand-graded Power."""
    return 3 * len(roles) + 6 * len(set(roles) & IMPACT_ROLES)


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
    _, cards = parse_deck_file(d["path"])

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
    role_counts = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        d2 = carddata.get(n.lower())
        if not d2 or "Land" in _primary_type(d2["type"]):
            continue
        for label in classify_roles(d2["text"]):
            role_counts[label] = role_counts.get(label, 0) + q
    if role_counts:
        print("\nFunctional roles (heuristic from card text; a card can fill several):")
        for label in ROLE_ORDER:
            cnt = role_counts.get(label, 0)
            if cnt:
                print(f"  {label:20} {cnt:3}  {'#' * cnt}")
        interaction = sum(role_counts.get(k, 0)
                          for k in ("Removal (spot)", "Sweeper", "Counter"))
        print(f"  {'interaction total':20} {interaction:3}  "
              "(removal + sweeper + counter)")
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
                cols = {ch for ch in (r.get("Color(s)") or "").upper() if ch in "WUBRG"}
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


def deck_role_counts(cards, carddata):
    """(interaction, card_advantage) role counts for a deck — used to tell whether
    a candidate card FILLS A GAP (interaction / card advantage the deck is short on),
    which makes an otherwise-secondary fit a KEY one."""
    inter = ca = 0
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        cd = carddata.get(n.lower())
        roles = set(classify_roles(cd["text"] if cd else ""))
        if roles & _INTERACTION_ROLES:
            inter += 1
        if "Card advantage" in roles:
            ca += 1
    return inter, ca


def fit_strength(shared, theme_w, card_text, deck_int, deck_ca):
    """Classify a card→deck fit as KEY / role-player / tangential (F04).

      KEY          – shares the deck's SIGNATURE (top central theme) on a specific
                     theme, OR fills a role the deck is short on (interaction < 5 /
                     card advantage < 3).
      tangential   – shares only GENERIC themes (etb/tokens/…): low real signal.
      role-player  – shares a specific central theme, but not the signature.
    """
    specific = [t for t in shared if t.lower() not in GENERIC_THEMES]
    roles = set(classify_roles(card_text or ""))
    gap = (bool(roles & _INTERACTION_ROLES) and deck_int < 5) or \
          ("Card advantage" in roles and deck_ca < 3)
    if gap:
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
    deck_names = {n.lower() for _, n, _, _ in cards}
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

    # Deck colors = the colors the deck can actually CAST. Prefer the declared
    # `#: colors:`; else derive from mana COSTS — never color identity, so a card's
    # off-color activated abilities don't widen the deck and surface uncastable picks.
    deck_colors = _declared_colors(dmeta)
    if not deck_colors:
        dm = load_mana()
        for q, n, s, c in cards:
            if n.lower() in BASICS:
                continue
            entry = dm.get(n.lower())
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
        if not name or nl in deck_names or nl in BASICS:
            continue
        ccolors = {ch for ch in (r.get("Color(s)") or "").upper() if ch in "WUBRG"}
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
        # Theme fit + impact-role credit: among on-theme picks, a card that also fills
        # a high-value functional role (removal / card advantage / ramp / cost-reduction
        # / a payoff engine) outranks a same-theme vanilla body — the mirror of the
        # `cuts` fix, so a strong-but-thinly-tagged upgrade isn't buried. Reads the
        # pool's Card Text; a text-less row just gets no bonus.
        score = sum(theme_w[t] for t in shared) + _role_credit(classify_roles(r.get("Card Text") or ""))
        suggestions.append((score, name, r, shared))

    owned_of = lambda nl: by_name_qty.get(nl, 0)
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
        card_cols = {ch for ch in (r.get("Color(s)") or "").upper() if ch in "WUBRG"}
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
            for col in {ch for ch in (colid or "").upper() if ch in "WUBRG"}:
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


def legality_report(meta, cards, fmt, leg):
    """Pure legality computation shared by `legal` (verbose, one deck) and `audit`
    (one line per deck) so both apply IDENTICAL size/copy/format rules. Returns a
    dict: problems (list of strings), unknown (pool-absent card names), notes
    (informational lines about untracked formats / missing legality data), plus
    total / min_size / copy_limit / singleton for the caller to render. Offline —
    `leg` is a pre-loaded load_legalities() map (pass {} to skip the format check)."""
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
        illegal = []
        for nl in order:
            card_leg = leg.get(nl)
            if card_leg is None:
                unknown.append(disp[nl])
            elif fmt not in card_leg:
                illegal.append(disp[nl])
        for name in illegal:
            problems.append(f"{name}: not legal in {fmt}")
    elif fmt and fmt not in POOL_FORMATS:
        notes.append(f"Format '{fmt}' isn't tracked for legality "
                     f"(known: {', '.join(sorted(POOL_FORMATS))}) — checking size/copies only.")
    elif fmt and not leg:
        notes.append("card-pool.csv has no legality data (rebuild with build_pool.py) — "
                     "checking size/copies only.")

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

    rep = legality_report(meta, cards, fmt, load_legalities())
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
    meta, cards = parse_deck_file(d["path"])
    protected = _protected(meta)
    cardmeta = load_card_meta()
    carddata = load_card_data()
    mana = load_mana()

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

        # keep-score: higher = keep; cut candidates sort to the top (lowest keep).
        # Role credit is impact-weighted (see _role_credit) so a strong-but-off-theme
        # card (removal/engine/cost-reducer) isn't mis-ranked as a top cut.
        keep = fit + _role_credit(roles) + (1 if hit_central else 0) + min(tribal, 6)
        reasons = []
        if tags and not hit_central:
            reasons.append("off the deck's central themes")
        elif not tags:
            reasons.append("no synergy tags")
        if not roles:
            reasons.append("role not auto-detected — read text")
        if subs and tribal <= q:
            reasons.append("off-tribe")
        rows.append((keep, n, mv, sorted(roles), fit, reasons, ctx, text))

    if not rows:
        print(f"Deck {d['id']}: no nonland cards to evaluate.")
        return 0
    rows.sort(key=lambda r: (r[0], r[1].lower()))
    limit = args.limit if getattr(args, "limit", 0) and args.limit > 0 else len(rows)

    print(f"Deck {d['id']}: {d['name'] or d['path']} — cut candidates (weakest fit first)")
    print(f"Central themes: {', '.join(sorted(central)) or '(none)'}")
    if prot_present:
        print(f"Protected (kept OFF the cut list via #: protect:): {'; '.join(prot_present)}")
    print("Heuristic shortlist — read the text; it can't see spice/signature cards "
          "beyond the #: protect: header.\n")
    print(f"  {'Card':30} {'MV':>3}  {'Fit':>4}  Roles / why-cuttable")
    print("-" * 74)
    for keep, n, mv, roles, fit, reasons, ctx, text in rows[:limit]:
        mvs = str(mv) if mv is not None else "?"
        tail = ", ".join(roles) if roles else ("; ".join(reasons) if reasons else "—")
        if ctx:
            tail += f"   ⚠ context: {'/'.join(ctx)}"
        print(f"  {n[:30]:30} {mvs:>3}  {fit:>4}  {tail}")

    # Surface the actual oracle text so a cut is graded from what the card DOES,
    # never from the label above (the role map is a shortlist, not a verdict).
    import textwrap
    text_n = args.limit if getattr(args, "limit", 0) and args.limit > 0 else min(12, len(rows))
    print(f"\n── Oracle text of the top {min(text_n, len(rows))} cut candidates "
          f"(grade from THIS, not the label) ──")
    for keep, n, mv, roles, fit, reasons, ctx, text in rows[:text_n]:
        warn = f"   ⚠ context: {'/'.join(ctx)} — value depends on this deck" if ctx else ""
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
    'interaction total' cmd_stats reports, computed offline from oracle text so the
    roster audit can rank thin-interaction decks without a per-deck stats run."""
    n = 0
    for q, name, s, c in cards:
        if name.lower() in BASICS:
            continue
        cd = carddata.get(name.lower())
        if not cd or "Land" in _primary_type(cd["type"]):
            continue
        roles = classify_roles(cd["text"])
        if roles & {"Removal (spot)", "Sweeper", "Counter"}:
            n += q
    return n


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

    rep = legality_report(meta, cards, fmt, leg)
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
    ccols = {ch for ch in (cd.get("colors") or "").upper() if ch in "WUBRG"}
    ctags = set(cardmeta.get(card.lower(), {}).get("synergies", []))

    print(f"Card: {card}  [{'/'.join(sorted(ccols)) or 'Colorless'}]  ({cd['type']})")
    print(f"Themes: {', '.join(sorted(ctags)) or '(none)'}\n")

    results = []
    for dd in discover_decks():
        dmeta, cards = parse_deck_file(dd["path"])
        if not ccols.issubset(_deck_castable_colors(dmeta, cards, mana)):
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
        strength = fit_strength(shared, theme_w, cd.get("text") or "", d_int, d_ca)
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
        if cd and "Land" not in _primary_type(cd.get("type") or ""):
            entry = mana.get(nl)
            if entry and entry[1] is not None:
                mvs += [entry[1]] * q
                if entry[1] <= 2:
                    early += q
        m = cardmeta.get(nl)
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    declared = _declared_colors(dmeta) or _deck_castable_colors(dmeta, cards, mana)
    uncast, _off = _castability(cards, declared, mana, carddata)
    d_int, d_ca = deck_role_counts(cards, carddata)
    return {
        "buildable": missing == 0 and short == 0, "missing": missing, "short": short,
        "uncastable": len(uncast), "interaction": d_int, "card_advantage": d_ca,
        "avg_mv": round(sum(mvs) / len(mvs), 2) if mvs else 0.0, "early_drops": early,
        "central_themes": len(_central_themes(theme_w)),
        "central": sorted(_central_themes(theme_w)),
    }


def cmd_quality(args):
    """Deck-quality guard (F10): print the quality vector, diff it against a saved
    snapshot (`--vs FILE`) to flag regressions from a cut/swap, and/or check that a
    proposed add isn't a merely-tangential fit (`--add NAME`). Soft by design — it
    WARNS (some regressions are intentional trades); exits 0 unless --strict."""
    import json
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    vec = deck_quality_vector(d)
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
        if vec["central_themes"] < before.get("central_themes", 0):
            lost = set(before.get("central", [])) - set(vec["central"])
            regressions.append(f"lost central theme(s): {', '.join(sorted(lost)) or '?'}")
        if vec["avg_mv"] - before.get("avg_mv", 0) > 0.3:
            regressions.append(f"curve heavier (avg MV {before['avg_mv']}→{vec['avg_mv']})")

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
        strength = fit_strength(shared, theme_w, (cd or {}).get("text") or "", d_int, d_ca)
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
    resil = inter + ca                    # interaction + card advantage = grind / resilience
    if inter >= 5 and resil >= 7:
        return "A"                        # measurable ceiling; S is a human call on top
    if inter >= 3 and resil >= 4:
        return "B"
    if resil >= 2:
        return "C"
    return "D"


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
    print(f"  vector        : buildable {vec['buildable']} · uncastable {vec['uncastable']} · "
          f"interaction {vec['interaction']} · card-adv {vec['card_advantage']} · "
          f"avg MV {vec['avg_mv']} · central themes {vec['central_themes']}")
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
    p = sub.add_parser("tribes", help="creature-subtype breakdown + type-matters synergies")
    p.add_argument("id")
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
    p.add_argument("--strict", action="store_true", help="exit non-zero on any regression/weak-add (default: warn only)")
    p = sub.add_parser("tier", help="check a deck's claimed tier against its measurable quality floor")
    p.add_argument("id")
    p.add_argument("--strict", action="store_true", help="exit non-zero on a tier mismatch (default: warn only)")
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
        "mana": cmd_mana, "tribes": cmd_tribes, "suggest": cmd_suggest,
        "legal": cmd_legal, "cuts": cmd_cuts,
        "flex": cmd_flex, "swap": cmd_swap, "apply-flex": cmd_apply_flex,
        "verify": cmd_verify, "text": cmd_text, "suggest-homes": cmd_suggest_homes,
        "preflight": cmd_preflight, "quality": cmd_quality, "tier": cmd_tier,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
