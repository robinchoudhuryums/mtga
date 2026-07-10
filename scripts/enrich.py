#!/usr/bin/env python3
"""Auto-fill card details from the Scryfall API.

For each row, this looks the card up on Scryfall (by Card Name, and by Set Code
when one is present) and fills in any BLANK fields among:
    Type, Card Text, Color(s), Collector #

Fields you have already filled are never overwritten unless you pass --force.
Your own columns (Synergies, Quantity Owned) are never touched.

Network requirement:
    This needs outbound HTTPS access to https://api.scryfall.com. Some managed
    environments block it by egress policy; if so, run this where Scryfall is
    reachable (e.g. your local machine). No API key is required.

Usage:
    python3 scripts/enrich.py                # enrich the whole library in place
    python3 scripts/enrich.py --dry-run      # show what would change, write nothing
    python3 scripts/enrich.py --force        # also overwrite non-blank fields
    python3 scripts/enrich.py --only "Llanowar Elves"   # just matching rows

Scryfall asks callers to rate-limit; this sleeps 100ms between requests.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from lib import DEFAULT_CSV, load_rows, write_rows, eprint

SCRYFALL = "https://api.scryfall.com/cards/named"
USER_AGENT = "mtga-card-library/1.0"
# Type/Card Text/Color(s) are identical across every printing of a card, so they
# are safe to fill from any match. Collector # is printing-specific and is
# handled separately — only written when we are sure of the printing.
FILLABLE = ["Type", "Card Text", "Color(s)"]

# MTG Arena uses a few set codes that differ from Scryfall's. Map Arena -> Scryfall
# here so a set-constrained lookup resolves to the right printing. Unknown codes
# fall through unchanged and are caught safely by the mismatch guard below.
SET_ALIASES = {
    "dar": "dom",  # Dominaria (Arena calls it DAR)
}


def _request_json(params):
    url = f"{SCRYFALL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_card(name, set_code):
    """Look up an exact card name, optionally constrained to a set.

    Returns (card_json_or_None, set_matched). set_matched is True only when a
    set code was requested AND the returned card is actually from that set — so
    the caller knows whether the printing-specific Collector # can be trusted.

    Raises on network/policy errors so the caller stops rather than silently
    producing an empty library.
    """
    scry_set = SET_ALIASES.get(set_code.lower(), set_code.lower()) if set_code else None
    try:
        params = {"exact": name}
        if scry_set:
            params["set"] = scry_set
        card = _request_json(params)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        # Set+name not found. Retry by name alone so we can still fill the
        # printing-invariant fields, but report the printing as unmatched.
        if scry_set:
            try:
                return _request_json({"exact": name}), False
            except urllib.error.HTTPError as e2:
                if e2.code == 404:
                    return None, False
                raise
        return None, False

    # Confirm the returned printing really is the requested set.
    matched = bool(scry_set) and card.get("set", "").lower() == scry_set
    return card, matched


def color_shorthand(card):
    """Derive a Color(s) shorthand from color identity, matching the sheet's style.

    Examples: 'U', 'B/G', 'Colorless'. Uses color identity (not mana cost) so
    lands and hybrid cards resolve to the colors they actually belong to.
    """
    ci = card.get("color_identity", [])
    if not ci:
        return "Colorless"
    # Preserve WUBRG order for readability.
    order = {"W": 0, "U": 1, "B": 2, "R": 3, "G": 4}
    return "/".join(sorted(ci, key=lambda c: order.get(c, 9)))


def oracle_fields(card):
    """Return (type_line, oracle_text) handling multi-face (MDFC/adventure) cards."""
    type_line = card.get("type_line", "")
    text = card.get("oracle_text")
    if not text and "card_faces" in card:
        # Join faces with the standard '//' separator used on the card itself.
        faces = card["card_faces"]
        text = " // ".join(f.get("oracle_text", "") for f in faces)
        if not type_line:
            type_line = " // ".join(f.get("type_line", "") for f in faces)
    return type_line, (text or "")


def enrich(path, dry_run=False, force=False, only=None):
    header, rows = load_rows(path)
    changed = 0
    matched = 0

    for row in rows:
        name = (row.get("Card Name") or "").strip()
        if not name:
            continue
        if only and only.lower() not in name.lower():
            continue

        # Skip the network call if nothing is fillable and we're not forcing.
        needs = [c for c in FILLABLE if force or not (row.get(c) or "").strip()]
        if not needs:
            continue

        set_code = (row.get("Set Code") or "").strip()
        try:
            card, set_matched = fetch_card(name, set_code)
        except urllib.error.URLError as e:
            eprint(
                f"ERROR: could not reach Scryfall for {name!r}: {e}\n"
                f"       This environment may block api.scryfall.com; "
                f"run enrich.py where it is reachable."
            )
            return 1
        time.sleep(0.1)  # be polite to the API

        if card is None:
            eprint(f"WARN:  no Scryfall match for {name!r}"
                   + (f" in set {set_code}" if set_code else ""))
            continue
        matched += 1

        type_line, text = oracle_fields(card)
        values = {
            "Type": type_line,
            "Card Text": text,
            "Color(s)": color_shorthand(card),
        }
        # Collector # is printing-specific, so only fill it when we are certain
        # of the printing (set code was given and Scryfall returned that set).
        # Otherwise we'd write a number from an arbitrary reprint — the DAR->DOM
        # class of bug. Warn so the user knows to check the set code.
        if set_matched:
            values["Collector #"] = str(card.get("collector_number", ""))
        elif set_code:
            eprint(
                f"WARN:  {name!r}: Scryfall has no printing in set {set_code!r} "
                f"(mapped to {SET_ALIASES.get(set_code.lower(), set_code.lower())!r}). "
                f"Filled shared fields; left Collector # for you to confirm."
            )

        row_changed = False
        for col in ["Type", "Card Text", "Color(s)", "Collector #"]:
            new = values.get(col, "")
            if not new:
                continue
            current = (row.get(col) or "").strip()
            if force or not current:
                if current != new:
                    if dry_run:
                        print(f"  {name} :: {col}: {current!r} -> {new!r}")
                    row[col] = new
                    row_changed = True
        if row_changed:
            changed += 1

    if dry_run:
        print(f"\n[dry-run] {matched} card(s) matched, {changed} row(s) would change. "
              f"Nothing written.")
        return 0

    write_rows(rows, path)
    print(f"Enriched {changed} row(s) from {matched} Scryfall match(es). Wrote {path}.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fill blank card fields from Scryfall.")
    ap.add_argument("path", nargs="?", default=DEFAULT_CSV, help="CSV path")
    ap.add_argument("--dry-run", action="store_true", help="preview only, write nothing")
    ap.add_argument("--force", action="store_true", help="overwrite non-blank fields too")
    ap.add_argument("--only", metavar="SUBSTR", help="only rows whose name contains SUBSTR")
    args = ap.parse_args()
    sys.exit(enrich(args.path, dry_run=args.dry_run, force=args.force, only=args.only))
