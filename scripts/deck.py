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
    python3 scripts/deck.py stats 1a            # mana curve, colors, types
    python3 scripts/deck.py mana 1a             # hybrid-aware color requirements
    python3 scripts/deck.py suggest 1a          # pool cards that fit the deck's colors + themes

Mana analysis reads card-mana.csv (real mana costs, built by build_mana.py), so
hybrid {W/U} pips are counted as flexible rather than demanding both colors.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint

POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")

DECKS_DIR = os.path.join(REPO_ROOT, "decks")
MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")
BASICS = {"plains", "island", "swamp", "mountain", "forest", "wastes"}

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


def cmd_check(args):
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    _, _, by_name_qty = load_collection()
    _, cards = parse_deck_file(d["path"])

    print(f"Deck {d['id']}: {d['name'] or d['path']}")
    print(f"{'Have':>4} / {'Need':<4}  Card")
    print("-" * 44)
    missing, short = [], []
    for q, n, s, c in cards:
        have, found = owned(by_name_qty, n)
        flag = ""
        if not found:
            flag, _ = "  <- NOT IN LIBRARY", missing.append(n)
        elif have < q:
            flag = f"  <- short {q - have}"
            short.append(n)
        shown = "unlim" if n.lower() in BASICS else have
        print(f"{str(shown):>4} / {q:<4}  {n} ({s}){flag}")
    print("-" * 44)
    total = sum(q for q, *_ in cards)
    print(f"{len(cards)} unique, {total} total.")
    if missing:
        print(f"{len(missing)} not in library: {', '.join(missing)}")
    if short:
        print(f"{len(short)} short of the deck's requirement.")
    if not missing and not short:
        print("You own everything in this deck. Ready to build.")
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

    _, cards = parse_deck_file(d["path"])
    meta = load_card_meta()

    # Deck fingerprint: color identity + theme weights (copies carrying each tag).
    deck_names = {n.lower() for _, n, _, _ in cards}
    deck_colors, theme_w = set(), {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = meta.get(n.lower())
        if not m:
            continue
        deck_colors |= m["colors"]
        for t in m["synergies"]:
            theme_w[t] = theme_w.get(t, 0) + q
    if not theme_w:
        print(f"Deck {d['id']} has no synergy tags to match against "
              "(run tag_synergies.py). Nothing to suggest.")
        return 0

    # Score every pool card not already in the deck.
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        pool = list(csv.DictReader(fh))
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
    # Rank: strongest theme fit first; owned as a tiebreaker so quick adds float up.
    suggestions.sort(key=lambda x: (-x[0], -min(owned_of(x[1].lower()), 1), x[1].lower()))
    top = suggestions[:args.limit]

    topthemes = sorted(theme_w.items(), key=lambda kv: -kv[1])[:6]
    print(f"Deck {d['id']}: {d['name'] or d['path']} — suggestions from the pool\n")
    print(f"Colors: {'/'.join(sorted(deck_colors)) or 'Colorless'}  ·  "
          f"top themes: {', '.join(f'{t}({w})' for t, w in topthemes)}")
    if not top:
        print("\nNo pool cards matched this deck's colors + themes.")
        return 0
    print(f"\n{'Have':>5}  {'Card':30}  {'Rarity':8}  Matches (deck themes)")
    print("-" * 78)
    craftby = {}
    for score, name, r, shared in top:
        h = owned_of(name.lower())
        have = f"×{h}" if h > 0 else "craft"
        rar = (r.get("Rarity") or "").strip()
        if h == 0:
            craftby[rar] = craftby.get(rar, 0) + 1
        print(f"{have:>5}  {name[:30]:30}  {rar[:8]:8}  {', '.join(shared[:5])}")
    ncraft = sum(craftby.values())
    print("-" * 78)
    print(f"{len(top)} suggestion(s) — {len(top) - ncraft} owned, {ncraft} to craft"
          + (f" ({', '.join(f'{n} {r}' for r, n in sorted(craftby.items()))})"
             if ncraft else ""))
    return 0


def cmd_mana(args):
    """Hybrid-aware color requirements: which colors a deck STRICTLY needs."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}.")
        return 1
    by_key, by_name, _ = load_collection()
    _, cards = parse_deck_file(d["path"])
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
    return 0


def _commitment(n):
    if n <= 3:
        return "<- light splash"
    if n <= 8:
        return "<- secondary color"
    return "<- primary color"


# --- flex / suggested swaps ------------------------------------------------- #
def parse_flex(path):
    """Return the deck's flex suggestions from `#~` lines.

    A flex line is a comment (so it never counts toward the 60 or reaches Arena
    import), machine-readable as:  #~ -Out card | +In card | reason
    Any of the three fields may be omitted; a lone free-text field is a note.
    """
    entries = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            s = raw.strip()
            if not s.startswith("#~"):
                continue
            e = {"out": "", "in": "", "note": ""}
            for col in (c.strip() for c in s[2:].split("|")):
                if col.startswith("-"):
                    e["out"] = col[1:].strip()
                elif col.startswith("+"):
                    e["in"] = col[1:].strip()
                elif col:
                    e["note"] = (e["note"] + "  " + col).strip()
            if e["out"] or e["in"] or e["note"]:
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
    p.add_argument("--limit", type=int, default=20, help="max suggestions (default 20)")
    p.add_argument("--unowned", action="store_true", help="only craftable suggestions")
    p = sub.add_parser("flex", help="show a deck's flex / suggested swaps (#~ lines)")
    p.add_argument("id")
    args = ap.parse_args()

    return {
        "list": cmd_list, "wildcards": cmd_wildcards, "check": cmd_check,
        "diff": cmd_diff, "arena": cmd_arena, "stats": cmd_stats,
        "mana": cmd_mana, "tribes": cmd_tribes, "suggest": cmd_suggest,
        "flex": cmd_flex,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
