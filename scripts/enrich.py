#!/usr/bin/env python3
"""Auto-fill card details from the Scryfall API (batched).

For each row this fills any BLANK fields among:
    Type, Card Text, Color(s), Collector #

Fields you have already filled are never overwritten unless you pass --force.
Your own columns (Synergies, Quantity Owned) are never touched.

How it works: cards are looked up in batches of 75 via Scryfall's
/cards/collection endpoint (so a few hundred cards take only a handful of
requests instead of one-per-card), which keeps this well under Scryfall's rate
limits. Double-faced "Front // Back" names that the batch endpoint can't match
fall back to a single-card /cards/named lookup on the front face.

Type / Card Text / Color(s) are identical across every printing, so they're
filled from a name match. Collector # is printing-specific, so it's only written
when the matched printing's set actually equals the row's Set Code (after
mapping known Arena->Scryfall code differences) — otherwise it's left as-is so a
wrong number is never written.

Network requirement:
    Needs outbound HTTPS to https://api.scryfall.com. No API key required.

Usage:
    python3 scripts/enrich.py                # enrich the whole library in place
    python3 scripts/enrich.py --dry-run      # show what would change, write nothing
    python3 scripts/enrich.py --force        # also overwrite non-blank fields
    python3 scripts/enrich.py --only "Llanowar Elves"   # just matching rows
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from lib import DEFAULT_CSV, load_rows, write_rows, eprint
import scryfall
from scryfall import NotFound, ScryfallUnavailable

COLLECTION_URL = "https://api.scryfall.com/cards/collection"
NAMED_URL = "https://api.scryfall.com/cards/named"
USER_AGENT = "mtga-card-library/1.0"
BATCH_SIZE = 75  # Scryfall's max identifiers per /cards/collection request
FILLABLE = ["Type", "Card Text", "Color(s)"]

# MTG Arena uses a few set codes that differ from Scryfall's. Map Arena -> Scryfall
# here so the Collector # set-match check resolves correctly. Unknown codes fall
# through unchanged and are handled safely (Collector # simply isn't filled).
SET_ALIASES = {
    "dar": "dom",  # Dominaria (Arena calls it DAR)
}


def get_named(front_name):
    """Single-card lookup by exact (front-face) name; None if not found. A
    transient outage raises ScryfallUnavailable (see scryfall.py)."""
    try:
        return scryfall.named({"exact": front_name})
    except NotFound:
        return None


def get_named_in_set(front_name, set_code):
    """Look up a card's printing in a SPECIFIC set (exact name + set); None if
    that set has no such printing. The batch /cards/collection endpoint returns
    one representative printing per name (usually the newest), so Collector # —
    which is printing-specific — often can't be filled from it. This targeted
    lookup fetches the row's own set so the collector number actually resolves."""
    try:
        return scryfall.named({"exact": front_name, "set": set_code})
    except NotFound:
        return None


def color_shorthand(card):
    """Derive a Color(s) shorthand from color identity, e.g. 'U', 'B/G', 'Colorless'."""
    ci = card.get("color_identity", [])
    if not ci:
        return "Colorless"
    order = {"W": 0, "U": 1, "B": 2, "R": 3, "G": 4}
    return "/".join(sorted(ci, key=lambda c: order.get(c, 9)))


def oracle_fields(card):
    """Return (type_line, oracle_text), handling multi-face (MDFC/adventure) cards."""
    type_line = card.get("type_line", "")
    text = card.get("oracle_text")
    if not text and "card_faces" in card:
        faces = card["card_faces"]
        text = " // ".join(f.get("oracle_text", "") for f in faces)
        if not type_line:
            type_line = " // ".join(f.get("type_line", "") for f in faces)
    return type_line, (text or "")


def index_card(by_name, card):
    """Index a card under its full and front-face name (lowercased) for matching."""
    full = card.get("name", "").lower()
    by_name.setdefault(full, card)
    by_name.setdefault(full.split(" // ")[0], card)


def resolve_cards(names):
    """Return {name_lower: card} for the given names via batch + named fallback."""
    by_name = {}
    for i in range(0, len(names), BATCH_SIZE):
        chunk = names[i:i + BATCH_SIZE]
        data = scryfall.post_collection(chunk)
        for card in data.get("data", []):
            index_card(by_name, card)
        eprint(f"       looked up {min(i + BATCH_SIZE, len(names))}/{len(names)} names")
        time.sleep(0.1)

    # Fallback for names the batch couldn't match (e.g. "Front // Back" cards).
    unmatched = [n for n in names if n.lower() not in by_name]
    for n in unmatched:
        card = get_named(n.split(" // ")[0])
        if card:
            index_card(by_name, card)
        time.sleep(0.1)
    return by_name


def enrich(path, dry_run=False, force=False, only=None):
    _, rows = load_rows(path)

    def needs(r):
        cols = [c for c in FILLABLE if force or not (r.get(c) or "").strip()]
        # Collector # is filled separately (only when the printing's set matches),
        # so also queue a row whose Collector # is blank but that carries a Set
        # Code to resolve against — otherwise a lone-missing Collector # would
        # never be backfilled once the shared fields are already present.
        if (r.get("Set Code") or "").strip() and (
                force or not (r.get("Collector #") or "").strip()):
            cols.append("Collector #")
        return cols

    todo = [
        r for r in rows
        if (r.get("Card Name") or "").strip()
        and (not only or only.lower() in (r.get("Card Name") or "").lower())
        and needs(r)
    ]
    if not todo:
        print("Nothing to enrich (all matching rows already filled).")
        return 0

    names = sorted({(r.get("Card Name") or "").strip() for r in todo})
    try:
        by_name = resolve_cards(names)
    except ScryfallUnavailable as e:
        eprint(f"ERROR: could not reach Scryfall: {e}\n"
               f"       A slow/blocked Scryfall (timeout, 5xx, or a bad response) "
               f"stopped enrichment; nothing was written. This environment may "
               f"block api.scryfall.com — run enrich.py where it is reachable.")
        return 1

    changed = matched = 0
    unresolved = []
    coll_cache = {}  # (name_lower, scry_set) -> collector # for set-scoped lookups
    set_lookup_down = False  # trips on a mid-run outage so we stop retrying per-row
    unresolved_coll = {}  # set_code -> example name: collector # couldn't be resolved
    for row in todo:
        name = (row.get("Card Name") or "").strip()
        card = by_name.get(name.lower())
        if not card:
            unresolved.append(name)
            continue
        matched += 1

        type_line, text = oracle_fields(card)
        values = {
            "Type": type_line,
            "Card Text": text,
            "Color(s)": color_shorthand(card),
        }
        # Collector # is printing-specific. Fill it from the batched printing when
        # its set matches the row's Set Code; otherwise (the common case — the
        # batch endpoint returns one representative printing per name, rarely the
        # row's set) do a targeted set-scoped lookup so the number still resolves.
        set_code = (row.get("Set Code") or "").strip()
        scry_set = SET_ALIASES.get(set_code.lower(), set_code.lower()) if set_code else ""
        if scry_set and card.get("set", "").lower() == scry_set:
            values["Collector #"] = str(card.get("collector_number", ""))
        elif scry_set and (force or not (row.get("Collector #") or "").strip()):
            ck = (name.lower(), scry_set)
            if ck not in coll_cache:
                if set_lookup_down:
                    coll_cache[ck] = ""  # outage already seen; don't hammer Scryfall
                else:
                    try:
                        printing = get_named_in_set(name, scry_set)
                    except ScryfallUnavailable as e:
                        # The batch resolve succeeded but Scryfall went flaky during
                        # the per-row collector-# lookups — degrade (leave the rest
                        # as-is) instead of crashing, and stop retrying.
                        eprint(f"WARN:  Scryfall outage during collector-# lookups "
                               f"({e}); leaving remaining collector numbers as-is.")
                        set_lookup_down, printing = True, None
                    coll_cache[ck] = (str(printing.get("collector_number", ""))
                                      if printing and printing.get("set", "").lower() == scry_set
                                      else "")
                    time.sleep(0.1)
            if coll_cache[ck]:
                values["Collector #"] = coll_cache[ck]
            elif not set_lookup_down and not (row.get("Collector #") or "").strip():
                # The set-scoped lookup didn't confirm a printing in this set, so the
                # Collector # stays blank. Record the set so the miss isn't silent
                # (audit F26): if it's an Arena-specific code, add it to SET_ALIASES.
                unresolved_coll.setdefault(set_code.upper(), name)

        row_changed = False
        for col in ["Type", "Card Text", "Color(s)", "Collector #"]:
            new = values.get(col, "")
            if not new:
                continue
            current = (row.get(col) or "").strip()
            if (force or not current) and current != new:
                if dry_run:
                    print(f"  {name} :: {col}: {current!r} -> {new!r}")
                row[col] = new
                row_changed = True
        if row_changed:
            changed += 1

    for n in unresolved:
        eprint(f"WARN:  no Scryfall match for {n!r}")
    if unresolved_coll:
        pairs = ", ".join(f"{s} (e.g. {ex})" for s, ex in sorted(unresolved_coll.items()))
        eprint(f"NOTE:  Collector # left blank for {len(unresolved_coll)} set code(s) that "
               f"didn't resolve on Scryfall: {pairs}. If a code is Arena-specific (like "
               f"DAR→DOM), add it to SET_ALIASES in enrich.py so its numbers fill in.")

    if dry_run:
        print(f"\n[dry-run] {matched} card(s) matched, {changed} row(s) would change. "
              f"Nothing written.")
        return 0

    write_rows(rows, path)
    print(f"Enriched {changed} row(s) from {matched} Scryfall match(es)"
          + (f", {len(unresolved)} unmatched" if unresolved else "")
          + f". Wrote {path}.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fill blank card fields from Scryfall (batched).")
    ap.add_argument("path", nargs="?", default=DEFAULT_CSV, help="CSV path")
    ap.add_argument("--dry-run", action="store_true", help="preview only, write nothing")
    ap.add_argument("--force", action="store_true", help="overwrite non-blank fields too")
    ap.add_argument("--only", metavar="SUBSTR", help="only rows whose name contains SUBSTR")
    args = ap.parse_args()
    sys.exit(enrich(args.path, dry_run=args.dry_run, force=args.force, only=args.only))
