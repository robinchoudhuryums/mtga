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
    "web-slinging": ["evasion", "tempo"],
    # Combat / resilience
    "first strike": ["combat"], "double strike": ["combat", "aggro"],
    "deathtouch": ["combat", "removal"], "vigilance": ["combat"],
    "reach": ["defense"], "defender": ["defense"], "indestructible": ["resilience"],
    "enrage": ["combat"], "fight": ["removal", "combat"], "valiant": ["combat", "counters"],
    "immune": ["protection"], "wither": ["combat", "counters"],
    # Aggro / tempo
    "haste": ["aggro"], "flash": ["tempo"], "prowess": ["spellslinger", "tempo"],
    "exalted": ["aggro"], "dash": ["aggro"], "riot": ["aggro"], "raid": ["aggro"],
    "battle cry": ["go-wide", "aggro"], "training": ["counters", "aggro"],
    "mobilize": ["go-wide", "aggro"], "alliance": ["aggro", "value"],
    # Speed (Aetherdrift)
    "start your engines!": ["speed"], "max speed": ["speed", "aggro"],
    "mayhem": ["graveyard", "aggro"],
    # Lifegain / drain
    "lifelink": ["lifegain"], "extort": ["lifegain", "drain"],
    # Graveyard / recursion
    "surveil": ["graveyard"], "mill": ["graveyard", "mill"],
    "delve": ["graveyard", "cost-reduction"], "descend": ["graveyard"],
    "fathomless descent": ["graveyard"], "threshold": ["graveyard"],
    "delirium": ["graveyard"], "morbid": ["sacrifice", "aristocrats"],
    "collect evidence": ["graveyard"], "void": ["graveyard", "payoff"],
    "flashback": ["graveyard", "recursion", "spellslinger"],
    "escape": ["graveyard", "recursion"], "disturb": ["graveyard", "recursion"],
    "unearth": ["graveyard", "recursion"], "embalm": ["graveyard", "tokens"],
    "eternalize": ["graveyard", "tokens"], "jump-start": ["graveyard", "spellslinger"],
    "aftermath": ["graveyard", "recursion"], "dredge": ["graveyard", "self-mill"],
    "scavenge": ["graveyard", "counters"], "exploit": ["sacrifice"],
    "blight": ["graveyard", "counters"],
    # Tokens / go-wide / sacrifice
    "convoke": ["go-wide", "ramp"], "amass": ["tokens", "go-wide"],
    "populate": ["tokens", "go-wide"], "fabricate": ["tokens", "counters"],
    "afterlife": ["tokens", "sacrifice"], "devour": ["sacrifice", "tokens"],
    "offspring": ["tokens", "go-wide"], "role token": ["tokens", "auras"],
    "manifest": ["tokens"], "manifest dread": ["tokens", "graveyard"],
    "teamwork": ["go-wide", "combat"], "saddle": ["go-wide", "combat"],
    # Counters
    "proliferate": ["counters"], "bolster": ["counters"], "adapt": ["counters"],
    "mentor": ["counters", "aggro"], "outlast": ["counters"], "graft": ["counters"],
    "evolve": ["counters"], "modular": ["counters", "artifacts"],
    "endure": ["counters", "tokens"], "power-up": ["counters", "payoff"],
    # Artifacts / cost
    "affinity": ["artifacts", "cost-reduction"], "improvise": ["artifacts", "ramp"],
    "station": ["counters", "artifacts"], "prototype": ["artifacts"],
    "craft": ["artifacts", "graveyard"], "reconfigure": ["equipment"],
    # Card advantage / selection
    "cycling": ["card draw"], "learn": ["card draw"], "channel": ["card advantage"],
    "investigate": ["tokens", "card draw"], "scry": ["selection"],
    "connive": ["card draw", "counters", "graveyard"], "discover": ["value", "spellslinger"],
    "landcycling": ["card draw", "lands"], "typecycling": ["card draw"],
    "basic landcycling": ["card draw", "lands"], "plainscycling": ["card draw", "lands"],
    "islandcycling": ["card draw", "lands"], "swampcycling": ["card draw", "lands"],
    "mountaincycling": ["card draw", "lands"], "forestcycling": ["card draw", "lands"],
    "behold": ["dragons"], "explore": ["counters", "selection"],
    # Protection
    "ward": ["protection"], "hexproof": ["protection"], "shroud": ["protection"],
    "protection": ["protection"], "changeling": ["tribal"],
    # Ramp / lands / spellslinger / modal
    "landfall": ["lands", "ramp"], "domain": ["lands"], "converge": ["multicolor"],
    "cascade": ["value", "spellslinger"], "storm": ["spellslinger"],
    "replicate": ["spellslinger"], "buyback": ["spellslinger", "recursion"],
    "overload": ["spellslinger"], "flurry": ["spellslinger"], "prepared": ["spellslinger", "tempo"],
    "repartee": ["spellslinger"], "magecraft": ["spellslinger"],
    # Alternative / additional cost & tempo
    "warp": ["tempo", "cost-reduction"], "sneak": ["tempo", "cost-reduction"],
    "plot": ["tempo", "cost-reduction"], "evoke": ["value", "sacrifice"],
    # Impending (Duskmourn): cast for a cheaper impending cost, enters with time
    # counters and isn't a creature until the last is removed — a discounted early
    # drop with a delay, like warp/sneak/plot.
    "impending": ["tempo", "cost-reduction"],
    "kicker": ["value"], "multikicker": ["value"], "bargain": ["sacrifice", "value"],
    "gift": ["value"], "spree": ["value"], "disguise": ["tempo"], "boast": ["payoff"],
    "exhaust": ["payoff"], "suspect": ["aristocrats"], "gates": ["lands"],
    # Universe-of-Beyond flavor mechanics
    "waterbend": ["bending"], "earthbend": ["bending"], "airbend": ["bending"],
    "firebending": ["bending"],
    # Vehicles / equipment
    "crew": ["vehicles"], "equip": ["equipment"],
}

# Scryfall records Universe-Beyond *flavor* ability names in each card's
# `keywords` list — Final Fantasy spells/commands (Firaga, Blue Magic, Item, …),
# Marvel/Avatar signature moves (Wave Cannon, Angelo Cannon, Particle Beam, …),
# and one-off named actions (Take the Elevator, The Allagan Eye, …). These are
# card-unique flavor, not deck-building mechanics, so they're dropped from tags
# rather than polluting the Synergies vocabulary. Recurring UB *mechanics*
# (Vivid, Opus, Job select, Infusion, Paradigm, Increment, Disappear, Tiered)
# are intentionally kept — theming those is a separate roadmap item — as are
# genuine keywords that merely look unusual (Eerie, Survival). This is a
# denylist so new *real* keywords still tag automatically; extend it as new
# flavor-heavy sets land. Compare against the keyword lowercased.
FLAVOR_KEYWORDS = {
    "ability", "angelo cannon", "animal may-ham", "attack", "blue magic", "bring down",
    "death gigas", "dinosaur formula", "double overdrive", "dragonfire dive",
    "echo of the lost", "find new host", "fira", "firaga", "fire", "fire cross",
    "galian beast", "harmonize", "heal", "hellmasker", "item", "look around",
    "magic", "murasame", "particle beam", "rat tail", "stagger", "starfall", "super nova",
    "take 59 flights of stairs", "take the elevator", "the allagan eye",
    "trance", "wave cannon",
}

# (tag, predicate(type_line_lower, text_lower)) — order defines output order.
MECHANIC_RULES = [
    ("counters", lambda t, x: "+1/+1 counter" in x or "-1/-1 counter" in x
        or "counter on" in x or "stun counter" in x),
    ("counterspell", lambda t, x: "counter target" in x),
    ("reanimator", lambda t, x: "graveyard" in x and "battlefield" in x
        and ("return" in x or "put" in x) and "creature" in x),
    ("graveyard", lambda t, x: "graveyard" in x),
    ("mill", lambda t, x: "mill" in x),
    ("lifegain", lambda t, x: "lifelink" in x or re.search(
        r"gain \d+ life|gain x life|gain that much life|"
        # also the PAYOFF side — cards that care about lifegain without gaining it
        # themselves (Ajani's Pridemate, Starscape Cleric) belong to the theme too.
        r"whenever you gain life|(amount of )?life you gained|if you('ve| have)? gained", x)),
    ("card draw", lambda t, x: re.search(
        r"draw (a|two|three|four|five|six|seven|x|that many|\d+) cards?", x) is not None),
    # Repeatable topdeck advantage — casting/playing off the top of your library is
    # continuous extra cards, a value engine the earlier "selection" ("look at the top")
    # rule alone under-read (Vizier of the Menagerie, Realmwalker, Bolas's Citadel,
    # Oracle of Mul Daya, Future Sight).
    ("card advantage", lambda t, x: "from the top of your library" in x
        and ("cast" in x or "play" in x)),
    ("sacrifice", lambda t, x: "sacrifice" in x),
    ("tokens", lambda t, x: "create" in x and "token" in x),
    ("removal", lambda t, x: "destroy target" in x or "exile target" in x),
    ("burn", lambda t, x: re.search(r"deals? \d+ damage|deals x damage", x) is not None),
    ("ramp", lambda t, x: "search your library for a" in x and "land" in x),
    # Color fixing — "spend mana of any type / as though it were any color" lets a deck
    # cast off-color cards, a ramp-adjacent value that scales with a deck's color count
    # (Vizier of the Menagerie, Fist of Suns, Jodah). Untagged before, so fixing engines
    # read as pure "selection" and hid from ramp/multicolor decks in suggest/suggest-homes.
    ("ramp", lambda t, x: "spend mana of any type" in x
        or "as though it were mana of any color" in x),
    ("mana", lambda t, x: re.search(r"\{t\}: add", x) is not None),
    # Land-token ramp + rainbow fixing — a card that makes a LAND token, or turns lands
    # into "every/all basic land type(s)", is ramp AND color fixing whose value scales with
    # a deck's color count (Overlord of the Hauntwoods' Everywhere token, Energybending).
    # The theme model missed these (tagged only tokens/etb), so rainbow fixers hid from
    # multicolor decks in suggest/suggest-homes/cuts, same blind spot as the Vizier case.
    ("ramp", lambda t, x: re.search(r"create[s]?\b[^.]*\bland tokens?\b", x) is not None),
    ("mana", lambda t, x: re.search(r"(every|all|each) basic land type", x) is not None),
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
    # Common spell/enchantment effects that otherwise left many
    # instants/sorceries/enchantments untagged: combat tricks & anthems, shrink-
    # based removal / bite, bounce, hand disruption, card selection, impulse
    # draw, theft, blink, and instant/sorcery-matters.
    ("pump", lambda t, x: re.search(r"gets? \+[\dx]+/[+-][\dx]+", x) is not None),
    ("removal", lambda t, x: re.search(r"gets [+-]?[\dx]+/-[\dx]+|gets -[\dx]+/", x) is not None
        or "deals damage equal to its power to target creature" in x),
    ("bounce", lambda t, x: re.search(r"return .*to (its|their) owner", x) is not None
        and "hand" in x),
    ("discard", lambda t, x: re.search(
        r"target (player|opponent)[^.]*discard|discards (a|that|two|their|down)"
        r"|unless (they|that player) discard", x) is not None),
    ("selection", lambda t, x: "look at the top" in x),
    ("impulse", lambda t, x: "exile the top" in x and "may play" in x),
    ("theft", lambda t, x: "gain control of" in x),
    ("blink", lambda t, x: "exile" in x and "return" in x
        and "to the battlefield" in x and "graveyard" not in x),
    ("spellslinger", lambda t, x: "whenever you cast an instant or sorcery" in x
        or "instant and sorcery spell" in x),
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
    # Skip Universe-Beyond flavor ability names (see FLAVOR_KEYWORDS).
    for kw in (keywords or []):
        k = kw.strip().lower()
        if not k or k in FLAVOR_KEYWORDS:
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
    ap.add_argument("--force", action="store_true",
                    help="REPLACE non-blank cells too (destructive — clobbers hand edits)")
    ap.add_argument("--merge", action="store_true",
                    help="add newly-derived tags to non-blank cells WITHOUT removing "
                         "existing/hand-curated ones — the safe refresh mode (audit F10)")
    ap.add_argument("--dry-run", action="store_true", help="preview a sample, write nothing")
    args = ap.parse_args()

    _, rows = load_rows(args.path)
    kw_map = load_keywords(MANA_CSV)
    if not kw_map:
        print("Note: card-mana.csv not found — tagging without Scryfall keywords. "
              "Run build_mana.py first for keyword-aware tags.")
    elif os.path.exists(args.path) and os.path.getmtime(MANA_CSV) < os.path.getmtime(args.path):
        # A present-but-STALE mana file gives newly-imported cards no keyword tags with
        # no warning (audit F21) — flag it so the operator rebuilds before tagging.
        print("Note: card-mana.csv is OLDER than the library — newly-added cards may lack "
              "keyword-aware tags. Run build_mana.py (--pool) first, then re-tag.")
    changed = 0
    sample = []
    for row in rows:
        name = (row.get("Card Name") or "").strip()
        if not name:
            continue
        existing = (row.get("Synergies") or "").strip()
        if existing and not (args.force or args.merge):
            continue
        derived = tags_for(row, kw_map.get(name.lower()))
        if args.merge and existing:
            # Union: keep every existing tag (incl. hand-curated), append new ones.
            have = [t.strip() for t in existing.split(";") if t.strip()]
            haveset = {t.lower() for t in have}
            merged = have + [t for t in derived if t.lower() not in haveset]
            value = "; ".join(merged)
        else:
            value = "; ".join(derived)
        if value != existing:
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
