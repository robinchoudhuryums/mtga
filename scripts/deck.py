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
    python3 scripts/deck.py check 1a            # owned vs needed vs your collection
    python3 scripts/deck.py diff 1 1a           # what the variant changes
    python3 scripts/deck.py arena 1a            # emit an Arena-importable list
    python3 scripts/deck.py stats 1a            # mana curve, colors, types
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint

DECKS_DIR = os.path.join(REPO_ROOT, "decks")
MANA_CACHE = os.path.join(REPO_ROOT, ".mana-cache.json")
BASICS = {"plains", "island", "swamp", "mountain", "forest", "wastes"}

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
    _, rows = load_rows(DEFAULT_CSV)
    by_key, by_name = {}, {}
    for r in rows:
        name = (r.get("Card Name") or "").strip()
        if not name:
            continue
        key = (name.lower(), (r.get("Set Code") or "").strip().lower(),
               (r.get("Collector #") or "").strip().lower())
        by_key[key] = r
        by_name.setdefault(name.lower(), r)
    return by_key, by_name


def owned(by_key, by_name, name, set_code, collector):
    """(count_owned, in_library) for a deck card. Basics count as unlimited."""
    if name.lower() in BASICS:
        return 99, True
    key = (name.lower(), set_code.lower(), collector.lower())
    row = by_key.get(key) or by_name.get(name.lower())
    if not row:
        return 0, False
    q = (row.get("Quantity Owned") or "").strip()
    return (int(q) if q.isdigit() else 0), True


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def cmd_list(_args):
    decks = discover_decks()
    if not decks:
        print("No decks yet. Add one under decks/<NN-name>/deck.txt "
              "(see decks/README.md).")
        return 0
    by_key, by_name = load_collection()
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
                have, found = owned(by_key, by_name, n, s, c)
                if not found or have < q:
                    short += 1
            status = "OK " if short == 0 else f"{short} short"
            label = d["name"] or os.path.basename(os.path.dirname(d["path"])) or d["id"]
            tag = "  └─ variant" if d["variant"] else "CORE"
            print(f"  [{d['id']:>4}] {tag:12} {label:28} {total:3} cards  {status}")
    return 0


def cmd_check(args):
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    by_key, by_name = load_collection()
    _, cards = parse_deck_file(d["path"])

    print(f"Deck {d['id']}: {d['name'] or d['path']}")
    print(f"{'Have':>4} / {'Need':<4}  Card")
    print("-" * 44)
    missing, short = [], []
    for q, n, s, c in cards:
        have, found = owned(by_key, by_name, n, s, c)
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


# --- stats (needs mana value; fetched from Scryfall and cached) ------------- #
def _load_mana_cache():
    if os.path.exists(MANA_CACHE):
        with open(MANA_CACHE, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def _fetch_cmc(names, cache):
    """Fill cache[name_lower] = mana value for missing names via Scryfall batch."""
    todo = [n for n in names if n.lower() not in cache]
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
        except urllib.error.URLError:
            break
        for card in data.get("data", []):
            full = card.get("name", "").lower()
            cmc = card.get("cmc", card.get("mana_value", 0))
            cache[full] = cmc
            cache[full.split(" // ")[0]] = cmc
        time.sleep(0.1)
    with open(MANA_CACHE, "w", encoding="utf-8") as fh:
        json.dump(cache, fh)
    return cache


def _primary_type(type_line):
    order = ["Land", "Creature", "Planeswalker", "Battle", "Artifact",
             "Enchantment", "Instant", "Sorcery"]
    for t in order:
        if t.lower() in type_line.lower():
            return t
    return "Other"


def cmd_stats(args):
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}.")
        return 1
    by_key, by_name = load_collection()
    _, cards = parse_deck_file(d["path"])

    colors, types, total = {}, {}, 0
    nonland_names = []
    for q, n, s, c in cards:
        total += q
        row = by_key.get((n.lower(), s.lower(), c.lower())) or by_name.get(n.lower())
        tline = (row.get("Type") if row else "") or ""
        ptype = "Land" if n.lower() in BASICS else _primary_type(tline)
        types[ptype] = types.get(ptype, 0) + q
        if ptype != "Land":
            nonland_names.append(n)
        col = (row.get("Color(s)") if row else "") or ""
        for ch in (col.upper() if col else ""):
            if ch in "WUBRG":
                colors[ch] = colors.get(ch, 0) + q
        if col.lower() == "colorless":
            colors["C"] = colors.get("C", 0) + q

    print(f"Deck {d['id']}: {d['name'] or d['path']}  ({total} cards)")
    print("\nTypes:")
    for t, n in sorted(types.items(), key=lambda kv: -kv[1]):
        print(f"  {t:13} {n:3}  {'#' * n}")
    print("\nColors (by mana symbol in identity):")
    for ch in "WUBRGC":
        if colors.get(ch):
            print(f"  {ch}  {colors[ch]:3}  {'#' * colors[ch]}")

    # Mana curve (fetched + cached).
    cache = _fetch_cmc(sorted(set(nonland_names)), _load_mana_cache())
    curve = {}
    have_cmc = True
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        row = by_key.get((n.lower(), s.lower(), c.lower())) or by_name.get(n.lower())
        if row and "Land" in _primary_type((row.get("Type") or "")):
            continue
        cmc = cache.get(n.lower())
        if cmc is None:
            have_cmc = False
            continue
        bucket = int(cmc) if cmc < 7 else 7
        curve[bucket] = curve.get(bucket, 0) + q
    print("\nMana curve (nonland):" + ("" if have_cmc else "  [partial — some CMC unavailable]"))
    for b in range(0, 8):
        if curve.get(b):
            label = f"{b}+" if b == 7 else str(b)
            print(f"  {label:>2} MV  {curve[b]:3}  {'#' * curve[b]}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Manage decks and variations.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list all decks and variants")
    p = sub.add_parser("check", help="owned vs needed vs your collection")
    p.add_argument("id")
    p = sub.add_parser("diff", help="show what one deck changes vs another")
    p.add_argument("a"); p.add_argument("b")
    p = sub.add_parser("arena", help="emit an Arena-importable decklist")
    p.add_argument("id")
    p = sub.add_parser("stats", help="mana curve, colors, and type breakdown")
    p.add_argument("id")
    args = ap.parse_args()

    return {
        "list": cmd_list, "check": cmd_check, "diff": cmd_diff,
        "arena": cmd_arena, "stats": cmd_stats,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
