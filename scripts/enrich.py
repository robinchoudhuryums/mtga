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


def _retrying(do_request, retries=6):
    """Run do_request(), retrying 429 and network errors with backoff.

    Non-429 HTTPErrors (e.g. 404) are raised for the caller to handle.
    """
    for attempt in range(retries):
        try:
            return do_request()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                wait = float(e.headers.get("Retry-After", 0) or 0) or 1.0 * (2 ** attempt)
                eprint(f"       rate limited by Scryfall; waiting {wait:.0f}s...")
                time.sleep(wait)
                continue
            raise
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(1.0 * (2 ** attempt))
                continue
            raise


def post_collection(names):
    """Batch-look-up card names via /cards/collection. Returns the parsed JSON."""
    body = json.dumps({"identifiers": [{"name": n} for n in names]}).encode("utf-8")

    def do():
        req = urllib.request.Request(
            COLLECTION_URL,
            data=body,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)

    return _retrying(do)


def get_named(front_name):
    """Single-card lookup by exact (front-face) name; None if not found."""
    def do():
        url = f"{NAMED_URL}?{urllib.parse.urlencode({'exact': front_name})}"
        req = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)

    try:
        return _retrying(do)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


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
        data = post_collection(chunk)
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
        return [c for c in FILLABLE if force or not (r.get(c) or "").strip()]

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
    except urllib.error.HTTPError as e:
        eprint(f"ERROR: Scryfall returned HTTP {e.code}: {e.reason}")
        return 1
    except urllib.error.URLError as e:
        eprint(f"ERROR: could not reach Scryfall: {e}\n"
               f"       This environment may block api.scryfall.com; "
               f"run enrich.py where it is reachable.")
        return 1

    changed = matched = 0
    unresolved = []
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
        # Collector # is printing-specific: only fill it when the matched
        # printing's set equals the row's Set Code (after alias mapping).
        set_code = (row.get("Set Code") or "").strip()
        scry_set = SET_ALIASES.get(set_code.lower(), set_code.lower()) if set_code else ""
        if scry_set and card.get("set", "").lower() == scry_set:
            values["Collector #"] = str(card.get("collector_number", ""))

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
