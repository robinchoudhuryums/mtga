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
import csv
import os
import re
import sys

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, write_rows

MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")

# Keyword -> deck-building themes. Keyword presence comes from Scryfall's
# authoritative per-card `keywords` list (via card-mana.csv), so we don't rely on
# scanning oracle text with a hand-maintained list. Each keyword is tagged
# verbatim AND expanded to the themes it implies, so e.g. Surveil surfaces
# "graveyard" and Convoke surfaces "go-wide".
KEYWORD_THEMES = {
    # Evasion
    "flying": ["evasion"], "menace": ["evasion"], "trample": ["evasion"],
    "fear": ["evasion"], "intimidate": ["evasion"], "shadow": ["evasion"],
    "skulk": ["evasion"], "horsemanship": ["evasion"], "ninjutsu": ["evasion", "tempo"],
    # Combat / resilience
    "first strike": ["combat"], "double strike": ["combat", "aggro"],
    "deathtouch": ["combat", "removal"], "vigilance": ["combat"],
    "reach": ["defense"], "defender": ["defense"], "indestructible": ["resilience"],
    # Aggro / tempo
    "haste": ["aggro"], "flash": ["tempo"], "prowess": ["spellslinger", "tempo"],
    "exalted": ["aggro"], "dash": ["aggro"], "riot": ["aggro"],
    "battle cry": ["go-wide", "aggro"], "training": ["counters", "aggro"],
    # Lifegain / drain
    "lifelink": ["lifegain"], "extort": ["lifegain", "drain"],
    # Graveyard / recursion
    "surveil": ["graveyard"], "mill": ["graveyard", "mill"],
    "delve": ["graveyard", "cost-reduction"], "descend": ["graveyard"],
    "flashback": ["graveyard", "recursion", "spellslinger"],
    "escape": ["graveyard", "recursion"], "disturb": ["graveyard", "recursion"],
    "unearth": ["graveyard", "recursion"], "embalm": ["graveyard", "tokens"],
    "eternalize": ["graveyard", "tokens"], "jump-start": ["graveyard", "spellslinger"],
    "aftermath": ["graveyard", "recursion"], "dredge": ["graveyard", "self-mill"],
    "scavenge": ["graveyard", "counters"], "exploit": ["sacrifice"],
    # Tokens / go-wide / sacrifice
    "convoke": ["go-wide", "ramp"], "amass": ["tokens", "go-wide"],
    "populate": ["tokens", "go-wide"], "fabricate": ["tokens", "counters"],
    "afterlife": ["tokens", "sacrifice"], "devour": ["sacrifice", "tokens"],
    # Counters
    "proliferate": ["counters"], "bolster": ["counters"], "adapt": ["counters"],
    "mentor": ["counters", "aggro"], "outlast": ["counters"], "graft": ["counters"],
    "evolve": ["counters"], "modular": ["counters", "artifacts"],
    # Artifacts / cost
    "affinity": ["artifacts", "cost-reduction"], "improvise": ["artifacts", "ramp"],
    # Card advantage
    "cycling": ["card draw"], "learn": ["card draw"],
    "investigate": ["tokens", "card draw"],
    "connive": ["card draw", "counters", "graveyard"],
    # Protection
    "ward": ["protection"], "hexproof": ["protection"], "shroud": ["protection"],
    "protection": ["protection"],
    # Ramp / lands / spellslinger
    "landfall": ["lands", "ramp"], "domain": ["lands"],
    "cascade": ["value", "spellslinger"], "storm": ["spellslinger"],
    "replicate": ["spellslinger"], "buyback": ["spellslinger", "recursion"],
    "overload": ["spellslinger"],
    # Vehicles / equipment
    "crew": ["vehicles"], "equip": ["equipment"],
}

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


def tags_for(row, keywords=None):
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
    # Mechanic heuristics from oracle text.
    for tag, pred in MECHANIC_RULES:
        try:
            if pred(t_low, x_low) and tag not in tags:
                tags.append(tag)
        except re.error:
            pass
    # Scryfall keyword abilities (authoritative) + the themes they imply.
    for kw in (keywords or []):
        k = kw.strip().lower()
        if not k:
            continue
        if k not in tags:
            tags.append(k)
        for theme in KEYWORD_THEMES.get(k, []):
            if theme not in tags:
                tags.append(theme)
    return tags


def load_keywords(path):
    """name_lower -> [keywords] from card-mana.csv, if it's been built."""
    kw = {}
    if not os.path.exists(path):
        return kw
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            raw = (r.get("Keywords") or "").strip()
            if n:
                kw[n] = [k for k in raw.split(";") if k]
    return kw


def main():
    ap = argparse.ArgumentParser(description="Auto-tag the Synergies column.")
    ap.add_argument("path", nargs="?", default=DEFAULT_CSV)
    ap.add_argument("--force", action="store_true", help="regenerate non-blank cells too")
    ap.add_argument("--dry-run", action="store_true", help="preview a sample, write nothing")
    args = ap.parse_args()

    _, rows = load_rows(args.path)
    kw_map = load_keywords(MANA_CSV)
    if not kw_map:
        print("Note: card-mana.csv not found — tagging without Scryfall keywords. "
              "Run build_mana.py first for keyword-aware tags.")
    changed = 0
    sample = []
    for row in rows:
        name = (row.get("Card Name") or "").strip()
        if not name:
            continue
        if (row.get("Synergies") or "").strip() and not args.force:
            continue
        tags = tags_for(row, kw_map.get(name.lower()))
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
