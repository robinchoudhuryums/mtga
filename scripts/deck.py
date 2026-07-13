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
    #: notes: removal-heavy base build

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
    """Return (meta_dict, [(qty, name, set, collector), ...])."""
    meta, cards = {}, []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            m = META_RE.match(raw.strip())
            if m:
                meta[m.group(1).lower()] = m.group(2).strip()
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
        body = json.dumps({"identifiers": [{"name": n} for n in chunk]}).encode()
        req = urllib.request.Request(
            "https://api.scryfall.com/cards/collection", data=body,
            headers={"User-Agent": "mtga-card-library/1.0",
                     "Accept": "application/json", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
        except urllib.error.URLError as e:
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
    m = {}
    for q, n, s, c in cards:
        m[n] = m.get(n, 0) + q
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
    for n in names:
        da, db = ma.get(n, 0), mb.get(n, 0)
        if db > da:
            print(f"  +{db - da}  {n}")
            added += db - da
        elif da > db:
            print(f"  -{da - db}  {n}")
            removed += da - db
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
        body = json.dumps({"identifiers": [{"name": n} for n in chunk]}).encode()
        req = urllib.request.Request(
            "https://api.scryfall.com/cards/collection", data=body,
            headers={"User-Agent": "mtga-card-library/1.0",
                     "Accept": "application/json", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
        except urllib.error.URLError as e:
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
              "Ramp / fixing", "Team pump / anthem", "Protection / trick",
              "Recursion"]
_ROLE_PATTERNS = {
    "Removal (spot)": [
        r"destroy target (?:creature|permanent|nonland permanent|artifact or creature|"
        r"tapped creature|attacking creature|creature or planeswalker|creature with)",
        r"exile target (?:creature|permanent|nonland permanent|attacking|tapped)",
        r"deals? \d+ damage to (?:target|any target|another target)",
        r"fights? (?:target|another target)",
        r"deals damage equal to its power to target (?:creature|creature or planeswalker)",
        r"target creature gets -\d",
        r"return target creature.{0,40}?(?:owner|their) hand",
        r"enchanted creature can't attack or block",
    ],
    "Sweeper": [r"destroy all", r"exile all", r"all creatures get -",
                r"each (?:other )?creature (?:gets|deals|is|you don't control)"],
    "Counter": [r"counter target"],
    "Card advantage": [r"draws? (?:two|three|four|x|that many) cards?",
                       r"draw a card for each", r"draws? cards? equal to",
                       r"\binvestigate\b"],
    "Ramp / fixing": [r"search your library for .{0,30}?\bland",
                      r"\{t\}: add \{",
                      r"put (?:a|that|those|up to \w+).{0,40}?land.{0,40}?onto the battlefield"],
    "Team pump / anthem": [r"(?:other )?creatures you control get \+"],
    "Protection / trick": [r"\bhexproof\b", r"\bindestructible\b", r"protection from",
                           r"gets \+\d+/\+\d+ until end of turn"],
    "Recursion": [r"from your graveyard"],
}
_ROLE_COMPILED = [(label, [re.compile(p) for p in _ROLE_PATTERNS[label]])
                  for label in ROLE_ORDER]


def classify_roles(text):
    """Return the set of functional-role labels a card's oracle text matches."""
    t = (text or "").lower().replace("−", "-")  # normalize unicode minus
    return {label for label, pats in _ROLE_COMPILED if any(p.search(t) for p in pats)}


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


def cmd_suggest(args):
    """Recommend pool cards that fit a deck's color identity and synergy themes.

    Scores each candidate by how strongly its tags overlap the deck's themes
    (weighted by how central each theme is to the deck), filters to the deck's
    colors, and flags owned vs. craftable with wildcard rarity. Composes
    card-pool.csv + the synergy tags + tribes-style theme matching.
    """
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    if not os.path.exists(POOL_CSV):
        eprint("No card-pool.csv. Build it: python3 scripts/build_pool.py")
        return 1

    dmeta, cards = parse_deck_file(d["path"])
    meta = load_card_meta()

    # Format filter: default to the deck's own `#: format:` so craft suggestions
    # are legal to play (and acquire) in that format. --format overrides,
    # --any-format disables. Only applies when card-pool.csv carries legality data
    # (build_pool.py) and the format is one we track.
    fmt = "" if getattr(args, "any_format", False) else \
        (getattr(args, "fmt", None) or dmeta.get("format") or "").strip().lower()

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
        print(f"Deck {d['id']} has no synergy tags to match against "
              "(run tag_synergies.py). Nothing to suggest.")
        return 0

    # Deck colors = the colors the deck can actually CAST, so suggestions are
    # castable. Prefer the declared `#: colors:`; else derive from mana COSTS —
    # never color identity, since a card's off-color activated abilities (e.g.
    # Super-Skrull's {4}{R}) must not widen the deck's colors or we'd suggest
    # cards you can't cast.
    deck_colors = _declared_colors(dmeta)
    if not deck_colors:
        dm = load_mana()
        for q, n, s, c in cards:
            if n.lower() in BASICS:
                continue
            entry = dm.get(n.lower())
            if entry and entry[0]:
                strict, hybrid = parse_pips(entry[0])
                deck_colors |= set(strict) | {x for h in hybrid for x in h}

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
        score = sum(theme_w[t] for t in shared)
        suggestions.append((score, name, r, shared))

    owned_of = lambda nl: by_name_qty.get(nl, 0)
    if args.unowned:
        suggestions = [x for x in suggestions if owned_of(x[1].lower()) == 0]
    if getattr(args, "owned", False):
        suggestions = [x for x in suggestions if owned_of(x[1].lower()) > 0]
    # Rank: strongest theme fit first; owned as a tiebreaker so quick adds float up.
    suggestions.sort(key=lambda x: (-x[0], -min(owned_of(x[1].lower()), 1), x[1].lower()))
    top = suggestions if args.limit == 0 else suggestions[:args.limit]

    topthemes = sorted(theme_w.items(), key=lambda kv: -kv[1])[:6]
    print(f"Deck {d['id']}: {d['name'] or d['path']} — suggestions from the pool\n")
    print(f"Colors: {'/'.join(sorted(deck_colors)) or 'Colorless'}  ·  "
          f"top themes: {', '.join(f'{t}({w})' for t, w in topthemes)}")
    if apply_fmt:
        print(f"Format: {fmt}-legal only  (override with --format <fmt> / --any-format)")
    elif fmt and not has_leg:
        print(f"Format: '{fmt}' filter requested but card-pool.csv has no legality "
              "data — rebuild with build_pool.py. Showing all.")
    elif fmt and fmt not in POOL_FORMATS:
        print(f"Format: '{fmt}' not tracked — not filtering. "
              f"(known: {', '.join(sorted(POOL_FORMATS))})")
    if not top:
        print("\nNo pool cards matched this deck's colors + themes.")
        return 0
    fps = _deck_fingerprints(meta, exclude_id=d["id"])
    print(f"\n{'Have':>5}  {'Card':28}  {'Rarity':8}  {'Decks':>5}  Matches (deck themes)")
    print("-" * 82)
    craftby = {}
    hi_reuse = []
    for score, name, r, shared in top:
        h = owned_of(name.lower())
        have = f"×{h}" if h > 0 else "craft"
        rar = (r.get("Rarity") or "").strip()
        if h == 0:
            craftby[rar] = craftby.get(rar, 0) + 1
        card_cols = {ch for ch in (r.get("Color(s)") or "").upper() if ch in "WUBRG"}
        card_themes = {t.strip() for t in (r.get("Synergies") or "").split(";") if t.strip()}
        fits = sum(1 for _id, dc, dt in fps if card_cols <= dc and (card_themes & dt))
        if h == 0 and fits >= 3:
            hi_reuse.append((name, fits))
        print(f"{have:>5}  {name[:28]:28}  {rar[:8]:8}  {fits:>5}  {', '.join(shared[:5])}")
    ncraft = sum(craftby.values())
    print("-" * 82)
    print(f"{len(top)} suggestion(s) — {len(top) - ncraft} owned, {ncraft} to craft"
          + (f" ({', '.join(f'{n} {r}' for r, n in sorted(craftby.items()))})"
             if ncraft else ""))
    print("Decks = how many of your OTHER decks the card is castable in + shares a "
          "CENTRAL theme with (higher = more value per wildcard).")
    if hi_reuse:
        print("High cross-deck reuse: "
              + ", ".join(f"{n} ({k})" for n, k in sorted(hi_reuse, key=lambda x: -x[1])[:6]))
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
    return out


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
    carddata = load_card_data()
    mana = load_mana()
    _, cards = parse_deck_file(d["path"])
    add_pr = _printing_of(add)
    after = _cards_after_swap(cards, cut, add, add_pr)
    if after is None:
        eprint(f"{cut!r} is not in deck {d['id']}. Nothing swapped.")
        return 1

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

    # Aggregate copies per card name (a card may span lines / printings); basics
    # are unlimited so they only count toward deck size, never the copy limit.
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

    print(f"Deck {d['id']}: {d['name'] or d['path']} — legality check"
          + (f"  ({fmt})" if fmt else "  (no #: format: declared)"))
    print("-" * 52)
    problems = []

    print(f"Deck size: {total} cards" + (f"  (min {min_size})" if fmt else ""))
    if fmt and total < min_size:
        problems.append(f"deck has {total} cards — {fmt} minimum is {min_size}")

    over = [(disp[nl], counts[nl]) for nl in order if counts[nl] > copy_limit]
    for name, cnt in over:
        problems.append(f"{name}: {cnt} copies (max {copy_limit}"
                        + (", singleton format" if singleton else "") + ")")

    unknown = []
    leg = load_legalities()
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
        print(f"Format '{fmt}' isn't tracked for legality "
              f"(known: {', '.join(sorted(POOL_FORMATS))}) — checking size/copies only.")
    elif fmt and not leg:
        print("card-pool.csv has no legality data (rebuild with build_pool.py) — "
              "checking size/copies only.")

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

    rows, seen = [], set()
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS or nl in seen:
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
        roles = classify_roles(cd["text"]) if cd else set()
        subs = set(creature_subtypes(tline))
        tribal = sum(sub_count.get(st, 0) for st in subs)  # includes own copies
        mv = (mana.get(nl) or (None, None))[1]

        # keep-score: higher = keep; cut candidates sort to the top (lowest keep).
        keep = fit + 3 * len(roles) + (1 if hit_central else 0) + min(tribal, 6)
        reasons = []
        if tags and not hit_central:
            reasons.append("off the deck's central themes")
        elif not tags:
            reasons.append("no synergy tags")
        if not roles:
            reasons.append("no functional role")
        if subs and tribal <= q:
            reasons.append("off-tribe")
        rows.append((keep, n, mv, sorted(roles), fit, reasons))

    if not rows:
        print(f"Deck {d['id']}: no nonland cards to evaluate.")
        return 0
    rows.sort(key=lambda r: (r[0], r[1].lower()))
    limit = args.limit if getattr(args, "limit", 0) and args.limit > 0 else len(rows)

    print(f"Deck {d['id']}: {d['name'] or d['path']} — cut candidates (weakest fit first)")
    print(f"Central themes: {', '.join(sorted(central)) or '(none)'}")
    print("Heuristic shortlist — spice/signature cards aren't known here.\n")
    print(f"  {'Card':30} {'MV':>3}  {'Fit':>4}  Roles / why-cuttable")
    print("-" * 74)
    for keep, n, mv, roles, fit, reasons in rows[:limit]:
        mvs = str(mv) if mv is not None else "?"
        tail = ", ".join(roles) if roles else ("; ".join(reasons) if reasons else "—")
        print(f"  {n[:30]:30} {mvs:>3}  {fit:>4}  {tail}")
    print(f"\nPair with `deck.py suggest {d['id']}` for adds; preview a swap with "
          f"`deck.py swap {d['id']} --cut <weak> --add <pick>`.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Manage decks and variations.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list all decks and variants")
    sub.add_parser("wildcards", help="roster-wide crafting plan (wildcards to finish decks)")
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
    g = p.add_mutually_exclusive_group()
    g.add_argument("--unowned", action="store_true", help="only craftable suggestions")
    g.add_argument("--owned", action="store_true",
                   help="only cards you already own (0 wildcards)")
    p = sub.add_parser("legal", help="deck-construction lint: size, copy limits, format legality")
    p.add_argument("id")
    p.add_argument("--format", dest="fmt", metavar="FMT",
                   help="check against FMT instead of the deck's #: format:")
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
    args = ap.parse_args()

    return {
        "list": cmd_list, "wildcards": cmd_wildcards, "check": cmd_check,
        "diff": cmd_diff, "arena": cmd_arena, "stats": cmd_stats,
        "mana": cmd_mana, "tribes": cmd_tribes, "suggest": cmd_suggest,
        "legal": cmd_legal, "cuts": cmd_cuts,
        "flex": cmd_flex, "swap": cmd_swap, "apply-flex": cmd_apply_flex,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
