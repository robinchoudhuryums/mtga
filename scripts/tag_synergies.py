#!/usr/bin/env python3
"""Populate the Synergies column with baseline deck-building tags.

Tags are derived heuristically from each card's Type line and Card Text:
  * Tribal / type tags   — creature subtypes and key card types (Equipment,
    Saga, Vehicle, Planeswalker, ...), taken from the type line.
  * Mechanic tags        — counters, graveyard, reanimator, lifegain, card
    draw, sacrifice, tokens, removal, burn, mill, ramp, ETB, tokens like Food/
    Treasure, and evergreen keywords (flying, deathtouch, ...).

These are a starting point, not gospel — they make query.py / the gallery
filters immediately useful, and you can hand-edit any Synergies cell afterward.
By default only BLANK Synergies cells are filled (your own tags are preserved);
pass --force to regenerate every row.

Usage:
    python3 scripts/tag_synergies.py --dry-run     # preview a sample
    python3 scripts/tag_synergies.py               # fill blank Synergies
    python3 scripts/tag_synergies.py --force        # regenerate all rows
"""

import argparse
import re
import sys

from lib import DEFAULT_CSV, load_rows, write_rows

# Evergreen / common keyword abilities worth tagging when they appear as words.
KEYWORDS = [
    "flying", "first strike", "double strike", "deathtouch", "trample",
    "vigilance", "menace", "lifelink", "haste", "hexproof", "reach", "defender",
    "ward", "prowess", "flash", "convoke", "cascade", "flashback", "afterlife",
    "exalted", "mentor", "crew", "embalm", "adapt", "escape",
]

# (tag, predicate(type_line_lower, text_lower)) — order defines output order.
MECHANIC_RULES = [
    ("counters", lambda t, x: "+1/+1 counter" in x or "counter on" in x),
    ("counterspell", lambda t, x: "counter target" in x),
    ("reanimator", lambda t, x: "graveyard" in x and "battlefield" in x
        and ("return" in x or "put" in x) and "creature" in x),
    ("graveyard", lambda t, x: "graveyard" in x),
    ("mill", lambda t, x: "mill" in x),
    ("lifegain", lambda t, x: "lifelink" in x or re.search(r"gain \d+ life|gain that much life", x)),
    ("card draw", lambda t, x: "draw a card" in x or "draw two" in x or "draw x" in x),
    ("sacrifice", lambda t, x: "sacrifice" in x),
    ("tokens", lambda t, x: "create" in x and "token" in x),
    ("removal", lambda t, x: "destroy target" in x or "exile target" in x),
    ("burn", lambda t, x: re.search(r"deals? \d+ damage|deals x damage", x) is not None),
    ("ramp", lambda t, x: "search your library for a" in x and "land" in x),
    ("mana", lambda t, x: re.search(r"\{t\}: add", x) is not None),
    ("etb", lambda t, x: re.search(r"when [^.]*enters", x) is not None),
    ("landfall", lambda t, x: "landfall" in x or "whenever a land enters" in x),
    ("scry", lambda t, x: "scry" in x),
    ("explore", lambda t, x: "explore" in x),
    ("energy", lambda t, x: "{e}" in x or "energy counter" in x),
    ("food", lambda t, x: "food" in x),
    ("treasure", lambda t, x: "treasure" in x),
    ("clue", lambda t, x: "clue" in x or "investigate" in x),
    ("equipment", lambda t, x: "equipment" in t or "equip " in x or "equip {" in x),
    ("aura", lambda t, x: "aura" in t or "enchant creature" in x),
    ("vehicle", lambda t, x: "vehicle" in t),
    ("saga", lambda t, x: "saga" in t),
    ("planeswalker", lambda t, x: "planeswalker" in t),
]

# Card types that make useful tags on their own.
TYPE_TAGS = ["Planeswalker", "Battle", "Saga", "Vehicle", "Equipment"]


def type_subtypes(type_line):
    """Return the subtypes (after the em dash) across all faces of a type line."""
    subs = []
    for face in type_line.split("//"):
        if "—" in face:
            subs += face.split("—", 1)[1].split()
    return subs


def tags_for(row):
    type_line = (row.get("Type") or "").strip()
    text = (row.get("Card Text") or "").strip()
    t_low, x_low = type_line.lower(), text.lower()

    tags = []
    # Tribal / subtype tags (Merfolk, Wizard, Ninja, ...).
    for sub in type_subtypes(type_line):
        if sub not in tags:
            tags.append(sub)
    # Notable card types.
    for tt in TYPE_TAGS:
        if tt.lower() in t_low and tt not in tags:
            tags.append(tt)
    # Mechanic heuristics.
    for tag, pred in MECHANIC_RULES:
        try:
            if pred(t_low, x_low) and tag not in tags:
                tags.append(tag)
        except re.error:
            pass
    # Keyword abilities.
    for kw in KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", x_low) and kw not in tags:
            tags.append(kw)
    return tags


def main():
    ap = argparse.ArgumentParser(description="Auto-tag the Synergies column.")
    ap.add_argument("path", nargs="?", default=DEFAULT_CSV)
    ap.add_argument("--force", action="store_true", help="regenerate non-blank cells too")
    ap.add_argument("--dry-run", action="store_true", help="preview a sample, write nothing")
    args = ap.parse_args()

    _, rows = load_rows(args.path)
    changed = 0
    sample = []
    for row in rows:
        if not (row.get("Card Name") or "").strip():
            continue
        if (row.get("Synergies") or "").strip() and not args.force:
            continue
        tags = tags_for(row)
        value = "; ".join(tags)
        if value != (row.get("Synergies") or "").strip():
            if len(sample) < 15:
                sample.append(f"  {row['Card Name']} -> {value}")
            row["Synergies"] = value
            changed += 1

    if args.dry_run:
        print("\n".join(sample))
        print(f"\n[dry-run] {changed} row(s) would be tagged. Nothing written.")
        return 0

    write_rows(rows, args.path)
    print(f"Tagged {changed} row(s). Wrote {args.path}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
