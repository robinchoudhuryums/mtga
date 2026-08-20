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

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, write_rows, csv_schema_error, eprint

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
    # Harmonize ("cast this from your graveyard for its harmonize cost") is graveyard
    # self-recursion like flashback/escape — deck.py's engine classifier already counts
    # it as a graveyard ENABLER. It was wrongly in FLAVOR_KEYWORDS because the collection
    # holds a single Harmonize card, which made the card-uniqueness test read it as a
    # one-off flavor name (broad-scan follow-on).
    "harmonize": ["graveyard", "recursion"],
    "unearth": ["graveyard", "recursion"], "embalm": ["graveyard", "tokens"],
    "eternalize": ["graveyard", "tokens"], "jump-start": ["graveyard", "spellslinger"],
    "aftermath": ["graveyard", "recursion"], "dredge": ["graveyard", "self-mill"],
    "scavenge": ["graveyard", "counters"], "exploit": ["sacrifice"],
    "blight": ["graveyard", "counters"],
    # Forage is a COST — "exile three cards from your graveyard or sacrifice a Food" —
    # so it consumes exactly two resources and a forage deck is built around both.
    # NOT tagged `sacrifice`: 7 of the 9 forage cards already earn that from their own
    # text, and the two that don't (Traverse Valley, a kicked land fetch; Euru) aren't
    # sacrifice cards — the keyword only means they MAY pay with a Food. Note the
    # graveyard side EMPTIES the yard, which the tag can't express in either direction;
    # that asymmetry is the zone-conflict detector's job (_GY_HATE_* / _GY_NEED_*), not
    # the tag model's, which has always read `graveyard` as "interacts with" and left
    # direction to the reader.
    "forage": ["graveyard", "food"],
    # `renew` (Tarkir: Dragonstorm) is a COST + EFFECT like forage, and maps to the two
    # resources it touches: it is activated FROM YOUR GRAVEYARD (exiling the card) and it
    # puts COUNTERS on a creature — "Renew — {1}{G}, Exile this card from your graveyard:
    # Put a +1/+1 counter on target creature." 14 pool cards, every one on that template,
    # so this is a real mechanic rather than flavor: it sat unindexed and warned on every
    # `check_all` run for several cycles, which is the saturation failure the radar exists
    # to avoid. Deliberately NOT `sacrifice` (nothing is sacrificed) and NOT `recursion`
    # (the card never returns — it is exiled to pay for the counters, so a renew card is a
    # graveyard RESOURCE, not a rebuy).
    "renew": ["graveyard", "counters"],
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
    # ── The Universe-Beyond mechanics K-01 carried as "acknowledged but unindexed",
    # triaged PER KEYWORD (never in bulk — that rule exists because `renew` and
    # `triple` came out opposite). Each is a recurring template across 5–17 pool
    # cards, and each maps to the RESOURCE it turns on, per K-02. The measured
    # delta is recorded because it is the only way to see what a mapping buys: most
    # of these cards quote reminder text the TEXT rules already read, so the map
    # earns its keep on the tail that states the keyword BARE.
    #
    # Vivid — "X = the number of colors among permanents you control". The same
    # family as `converge` (colors of mana SPENT), hence the same theme. 17/17 gain
    # both tags: nothing in the text rules reads a colour COUNT, which is why K-04's
    # two best fixers (Bloom Tender keys off Vivid) read as non-fixers for so long.
    "vivid": ["multicolor", "payoff"],
    # Job select — "When this Equipment enters, create a 1/1 Hero token, then attach
    # this to it." Both halves are literal. Only 2 of 16 gain anything: the other 14
    # print the reminder text, which the tokens rule already reads. The two that
    # don't (Ninja's Blades, Summoner's Grimoire) state it bare — exactly K-02's
    # invisible tail.
    "job select": ["equipment", "tokens"],
    # Opus — "Whenever you cast an instant or sorcery spell … if five or more mana
    # was spent". A spellslinger PAYOFF that additionally rewards expensive spells.
    # All 11 already read as spellslinger from text; the mapping's contribution is
    # `payoff`, which is what distinguishes them from the cheap spells they want.
    "opus": ["spellslinger", "payoff"],
    # Increment — "Whenever you cast a spell, if the mana spent is greater than this
    # creature's power or toughness, put a +1/+1 counter on it." 10/10 gain
    # spellslinger; Scalar Scholar states Increment bare and gains `counters` too.
    "increment": ["counters", "spellslinger"],
    # Infusion — "if you gained life this turn". A lifegain payoff, the lifegain
    # analogue of `morbid`. 13/13 gain `payoff`, 5 gain `lifegain`.
    "infusion": ["lifegain", "payoff"],
    # Disappear — "if a permanent left the battlefield under your control this turn".
    # Deliberately given morbid's exact pair: a disappear deck is built with sac
    # outlets and expiring tokens. KNOWN ADJACENCY, not tagged: blink also satisfies
    # it, but several disappear cards accumulate +1/+1 counters, which blink ERASES
    # (G-42) — so `blink` would recommend a package that fights half these cards.
    "disappear": ["sacrifice", "aristocrats"],
    # Paradigm — "exile this spell; after you first resolve a spell with this name,
    # cast a copy from exile for free each first main phase." Casting your OWN
    # exiled cards is exactly K-07's `exile cast`, and a free recurring copy is
    # repeatable card advantage. 5 cards, all on one template.
    "paradigm": ["exile cast", "card advantage"],
    # NOT MAPPED, and the reasons are the point of triaging one at a time:
    #   * `tiered` (6) — a COST SHAPE ("choose one additional cost"), not a resource.
    #     Its six cards span burn / bounce / lifegain / pump / protection and the
    #     text rules already tag each correctly; any single theme would be wrong for
    #     five of them, and a new theme for six cards is the fix K-09 warns off.
    #   * `jump` (13 reported, 2 real) — a SOURCE artifact, and the most interesting
    #     of the three. Scryfall lists "Jump" alongside "Jump-start" on all 11
    #     jump-start cards, so the apparent population is mostly a different, already
    #     mapped keyword. Only Freya Crescent and Kain genuinely have Jump ("during
    #     your turn, this has flying"). Mapping it to `evasion` would put that theme
    #     on 11 unrelated graveyard spells. A keyword's COUNT is not its population.
    #   * `triple` (3) — already triaged out once (K-01). Two damage triplers, which
    #     `doubler_axis` reads structurally, plus a Tiered mode NAME. Tiered cards
    #     also emit "Double", "Final Heaven", "Somersault" as keywords, which is the
    #     same source artifact as `jump`.
}

# Scryfall records Universe-Beyond *flavor* ability names in each card's
# `keywords` list — Final Fantasy spells/commands (Firaga, Blue Magic, Item, …),
# Marvel/Avatar signature moves (Wave Cannon, Angelo Cannon, Particle Beam, …),
# and one-off named actions (Take the Elevator, The Allagan Eye, …). These are
# card-unique flavor, not deck-building mechanics, so they're dropped from tags
# rather than polluting the Synergies vocabulary. Recurring UB *mechanics* are
# intentionally kept — seven of them (Vivid, Opus, Job select, Infusion, Paradigm,
# Increment, Disappear) are now THEMED in KEYWORD_THEMES above, and Tiered is
# deliberately left unthemed with its reason recorded there — as are
# genuine keywords that merely look unusual (Eerie, Survival). This is a
# denylist so new *real* keywords still tag automatically; extend it as new
# flavor-heavy sets land. Compare against the keyword lowercased.
#
# The Marvel (MSH) block below was the second lapse of exactly this kind (audit
# F-05): the set shipped and its signature moves went unindexed, so check_all
# emitted 27 soft warnings on EVERY run — burying the one signal the radar
# exists to raise — and 11 of them leaked into the Synergies vocabulary as
# one-card tags, which the pool tag-rarity model then scored as near-maximally
# distinctive. Each entry below was verified to sit on exactly ONE owned card;
# `check_keywords.flavor_overreach()` guards the reverse mistake, flagging any
# denylisted word that later turns up on >=3 owned cards (a real mechanic).
FLAVOR_KEYWORDS = {
    "ability", "angelo cannon", "animal may-ham", "attack", "blue magic", "bring down",
    "death gigas", "dinosaur formula", "double overdrive", "dragonfire dive",
    "echo of the lost", "find new host", "fira", "firaga", "fire", "fire cross",
    "galian beast", "heal", "hellmasker", "item", "look around",
    "magic", "murasame", "particle beam", "rat tail", "stagger", "starfall", "super nova",
    "take 59 flights of stairs", "take the elevator", "the allagan eye",
    "trance", "wave cannon",
    # Final Fantasy — a remaining card-unique weapon name. ("Jump" is deliberately NOT
    # here: Scryfall lists it as a keyword on one card, but it's a real recurring FF
    # ability — Kain and Freya both read "Jump — During your turn, ~ has flying" — so it
    # belongs in keyword_baseline.txt as an unindexed MECHANIC to theme, not suppressed.)
    "gae bolg",
    # Marvel (MSH) signature moves — each on a single card (Hawkeye's four arrow
    # types, The Vision's three abilities, Reptil's two dino forms, …).
    "avian telepathy", "boomerang", "brontosaurus", "cosmic awareness",
    "cybernetic senses", "density control", "embiggen fist", "explosive",
    "i love squirrels!", "intangibility", "legal justice", "mental organism",
    "net", "no one dies!", "photographic reflexes", "radar sense",
    "seismic takedown", "solar beam", "sonic attack", "street justice",
    "technopathy", "trick arrows", "tyrannosaurus rex", "unbreakable skin",
    "wasp's sting",
}

# ── One-card keyword suppression (replaces hand-maintaining the denylist) ───────
# FLAVOR_KEYWORDS above is a hand-kept list, and it went stale twice: once when Final
# Fantasy landed, again when Marvel shipped 27 signature moves that spent a cycle
# polluting the tag vocabulary and drowning the keyword radar (audit F-05). Derive the
# rule instead — but state it accurately, because the obvious phrasing is subtly wrong.
#
# The tempting rule is "a keyword on exactly one card is a FLAVOR name". Measured against
# the pool that mostly holds (every Marvel signature move sits at 1; Flashback 110,
# Escape 26, Vivid 17, Jump 13, Harmonize 11), but it also catches `forestwalk`,
# `sunburst`, `melee`, `eminence` — real MTG mechanics that simply appear on one Arena
# card each. So the rule is NOT about flavor. It is:
#
#     a keyword carried by exactly ONE card in the corpus cannot match any other card,
#     so as a tag it carries no cross-card synergy signal — and it actively HURTS,
#     because lib.pool_ability_model scores tag rarity, where a 1-card tag reads as a
#     near-maximally distinctive mechanic and inflates that card's `Uq`.
#
# On that basis suppressing `forestwalk` is as correct as suppressing `Trick Arrows`:
# neither can ever pair with another card. A keyword that DOES carry signal is protected
# by the guards below, since a mapped keyword contributes its THEMES (flashback ->
# graveyard; recursion) even when the verbatim tag would be lonely.
#
# Guards, because suppressing a real mechanic is the expensive mistake:
#   * a keyword mapped in KEYWORD_THEMES is a declared mechanic — never suppressed;
#   * a keyword deck.py names in ENGINE_THEMES is one another subsystem already treats
#     as real (exactly how `harmonize` got mis-filed) — never suppressed;
#   * the heuristic engages only when the corpus is big enough to mean anything.
#     card-mana.csv defaults to LIBRARY-ONLY scope, where a pool-wide mechanic can sit
#     on one owned card — `harmonize` did. Below the floor we fall back to the explicit
#     list, so a small corpus degrades to today's behaviour, never a confident wrong one.
# The explicit list stays as an override for anything the corpus can't settle.
_NOISE_MAX_CARDS = 1         # on exactly one card => no cross-card signal
_NOISE_MIN_CORPUS = 5000     # trust the count only when card-mana.csv covers the pool
_freq_cache = {}


def keyword_frequencies(path=None):
    """{keyword_lower: number of distinct cards carrying it} from card-mana.csv's
    Keywords column, plus the corpus size. Cached; returns ({}, 0) if unavailable."""
    path = path or MANA_CSV
    if path in _freq_cache:
        return _freq_cache[path]
    # Count DISTINCT CARDS, which for a DFC means collapsing its two rows. card-mana.csv
    # keys a double-faced card BOTH ways — under the front name and under the full
    # `Front // Back` name — so a tally by row reads a card-UNIQUE keyword on a DFC as
    # frequency 2 and it escapes the `<= _NOISE_MAX_CARDS` (1) noise filter. That is
    # exactly how "Goblin Formula" (on Norman Osborn alone) reached the check_keywords
    # radar as an unindexed mechanic: the docstring already said "distinct cards", the
    # implementation counted rows, and only a DFC could show the difference.
    freq, seen, n = {}, {}, 0
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                name = (r.get("Card Name") or "").strip()
                if not name:
                    continue
                card = name.split(" // ")[0].lower()
                if card not in seen:
                    seen[card] = True
                    n += 1
                for k in (r.get("Keywords") or "").split(";"):
                    k = k.strip().lower()
                    if k:
                        freq.setdefault(k, set()).add(card)
    freq = {k: len(v) for k, v in freq.items()}
    _freq_cache[path] = (freq, n)
    return freq, n


def _engine_keywords():
    """Keywords deck.py's ENGINE_THEMES patterns name as real engine mechanics."""
    if "engine" not in _freq_cache:
        words = set()
        try:
            import deck as _dk
            for _t, sides in getattr(_dk, "ENGINE_THEMES", {}).items():
                for _role, pats in sides.items():
                    for p in pats:
                        words |= {m.lower() for m in re.findall(r"\\b([a-z][a-z'\- ]+)\\b", p)}
        except Exception:
            words = set()
        _freq_cache["engine"] = words
    return _freq_cache["engine"]


def is_noise_keyword(kw, freq=None, corpus=None):
    """Should `kw` be dropped as a tag that carries no cross-card synergy signal? See the
    block above — this is one-card suppression, NOT flavor detection, and it deliberately
    catches genuinely rare real mechanics too. Pass `freq`/`corpus` to score against a
    specific corpus (the tests and the keyword radar do); both default to card-mana.csv."""
    k = (kw or "").strip().lower()
    if not k:
        return False
    if k in {x.lower() for x in FLAVOR_KEYWORDS}:
        return True                                   # explicit override
    if k in {x.lower() for x in KEYWORD_THEMES} or k in _engine_keywords():
        return False                                  # a declared/real mechanic
    if freq is None or corpus is None:
        freq, corpus = keyword_frequencies()
    if corpus < _NOISE_MIN_CORPUS:
        return False                                  # corpus too small to judge
    return 0 < freq.get(k, 0) <= _NOISE_MAX_CARDS


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
        # `gain life equal to ...` (Exsanguinate) is lifegain by any reading, but the
        # fixed-number alternation missed it and the card carried NO tags at all.
        r"gains? life equal to|"
        r"gain \d+ life|gain x life|gain that much life|"
        # also the PAYOFF side — cards that care about lifegain without gaining it
        # themselves (Ajani's Pridemate, Starscape Cleric) belong to the theme too.
        r"whenever you gain life|(amount of )?life you gained|if you('ve| have)? gained", x)),
    # LIFE AS A COST — the resource axis a whole deck can be built on, and the tag model
    # was blind to it. 351 pool cards (2.2%) spend YOUR life for an effect and none
    # carried a tag for it, so Dark Confidant — the single most on-thesis card for an
    # Orzhov life-as-currency deck — read `tangential / Human` in `suggest-homes`, its
    # only shared theme being a creature type. Deliberately scoped to YOU losing life:
    # "each opponent loses 2 life" is a DRAIN effect, which is the opposite card and
    # already covered by `drain`. The last three alternatives are the PAYOFF side, the
    # same way `lifegain` also tags cards that only CARE about life being gained.
    # COST REDUCTION without a named keyword. `cost-reduction` already exists as a tag
    # (167 pool cards) but only ever arrived via the KEYWORD map (affinity, delve, warp,
    # sneak, plot, impending, …), so a card that plainly says it costs less — Hour of
    # Revelation, Stratadon's domain clause — carried no tag at all. `classify_roles`
    # already read these as "Cost reduction / cheat"; this is the tag model catching up so
    # the two agree on the phrase, the same alignment the `draw cards equal to` and
    # `gain life equal to` fixes made.
    ("cost-reduction", lambda t, x: re.search(
        r"costs? \{[0-9x]+\} less|costs? \{[0-9x]+\} less to cast"
        r"|costs? up to \{[0-9x]+\} less", x) is not None),
    ("pay life", lambda t, x: re.search(
        r"(?:^|[,.:;(]\s*|\byou (?:may )?)pay (?:\d+|x) life"
        r"|\bpay life equal to"
        r"|you lose (?:\d+|x) life|you lose life equal to|you lose that much life"
        r"|\byou [^.]{0,60}?\band lose (?:\d+|x) life"
        r"|whenever you lose life|if you(?:'ve| have) lost life|life you(?:'ve| have) lost",
        x) is not None),
    # EXILE CAST — the card is cast FROM EXILE (warp / plot / foretell / Adventure), or it
    # pays off casting from outside your hand. See `is_exile_cast_text` for why the
    # graveyard half is deliberately excluded.
    ("exile cast", lambda t, x: is_exile_cast_text(t, x)),
    # HEIST — cast an opponent's card yourself (distinct from `theft` = gain control).
    # See `is_heist_text` for the scoping
    # rationale and why the match needs a proximity window rather than one regex.
    ("heist", lambda t, x: is_heist_text(x)),
    # `draw cards equal to ...` is the one phrase where this model and deck.py's
    # `classify_roles` disagreed: the role classifier already read it as Card advantage,
    # the tag model did not, so The Ten Rings ("draw cards equal to the difference") sat
    # in the deck with a COMPLETELY BLANK Synergies cell — invisible to every tag-based
    # recommendation. Eight more pool cards had the same hole.
    ("card draw", lambda t, x: re.search(
        r"draw (a|two|three|four|five|six|seven|x|that many|\d+) cards?"
        r"|draws? cards? equal to", x) is not None),
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
    # --- Mechanical-synergy PAYOFFS the tag model missed (tagging-misreads fix) ---
    # Toughness-matters (Doran-style): a card that assigns/deals combat damage by
    # TOUGHNESS instead of power — the payoff a "toughness swap" deck is built on
    # (Kingpin of Crime, Bark of Doran). Tagged so it shares a theme with those decks
    # instead of reading as a bare equipment/pump body (Bark → 20a/20b was invisible).
    ("toughness matters", lambda t, x: re.search(
        r"damage equal to its toughness|toughness rather than (its )?power|"
        r"assigns? combat damage equal to (its|their) toughness", x) is not None),
    # Noncombat-damage payoff/amplifier + repeatable PINGERS. The literal phrase catches
    # the amplifiers (Hawkeye, Ojer Axonil) and the "whenever a source you control deals
    # noncombat damage" draw engine. The second clause tags a repeatable pinger — a
    # PERMANENT (not a one-shot instant/sorcery burn spell) whose ability deals damage to a
    # player / any target / each opponent — so a ping-ENGINE deck reaches critical mass on
    # the theme and its amplifiers read KEY, WITHOUT a couple of burn SPELLS faking the
    # theme into any aggressive deck. Combat-damage triggers ("deals combat damage to a
    # player") don't match: "a player" isn't one of the targeted phrases.
    ("noncombat damage", lambda t, x: "noncombat damage" in x or (
        "instant" not in t and "sorcery" not in t and re.search(
            r"deals?\b[^.]{0,40}\bdamage to (any target|each opponent|target player|"
            r"target opponent|that player|each of (your opponents|them))", x) is not None)),
    # Spell-copy: a mana source / effect that copies an instant or sorcery — a
    # spellslinger payoff (Pyromancer's Goggles) that carried only a "mana" tag before.
    ("spell copy", lambda t, x: "copy that spell" in x
        or re.search(r"copy target (instant|sorcery|instant or sorcery)", x) is not None),
]

# Capitalized nouns that show up in the tribal-payoff templates below but are NOT
# creature types — kept out of the tribal tag so a sentence-initial "Creatures you
# control get…" or "search for a Basic land card" can't mint a bogus tribe tag. (Oracle
# text lower-cases generic "creatures/lands/tokens" mid-sentence, so the Title-case
# requirement already filters most of these; this backstops sentence-initial capitals.)
_NON_TRIBE_WORDS = {
    "Creature", "Creatures", "Land", "Lands", "Card", "Cards", "Basic", "Artifact",
    "Artifacts", "Enchantment", "Enchantments", "Instant", "Sorcery", "Planeswalker",
    "Permanent", "Permanents", "Token", "Tokens", "Spell", "Spells", "Aura", "Auras",
    "Equipment", "Vehicle", "Saga", "Legendary", "Snow", "Attacking", "Blocking",
    "Tapped", "Untapped", "Target", "Nonland", "Colored", "Colorless", "Opponent",
    "Opponents", "Player", "Players", "Modified", "Another", "Other",
    # NOT basic land types. Excluding them was tried and MEASURED WRONG: the widening
    # below mints exactly ZERO new basic-type tags (checked across all 16,067 pool
    # rows), while the exclusion silently dropped the tag from 28 real land-matters
    # payoffs — Corrupt, Tendrils of Corruption, Spitting Earth, Gates Ablaze, Eluge.
    # The reasoning that motivated it ("every landcycling reminder would mint a
    # Mountain theme") was plausible and false; the count is what settled it.
}

# Card TYPES a deck genuinely builds around, tagged when the card's TEXT names one it
# interacts with. `_NON_TRIBE_WORDS` deliberately excludes these from the tribal path
# (they are types, not tribes) and `TYPE_TAGS` reads only the TYPE LINE — so a card that
# CARES about a type carried no tag for it. That is K-03's stated residual ("Gilgamesh
# digs for Equipment cards" and so never surfaced in the roster's 13-Equipment deck),
# and it is why `deck.py suggest-homes Canyon Vaulter` returned NO DECK AT ALL: its only
# themes were its own subtypes (Kor, Pilot), while "saddles a Mount or crews a Vehicle"
# — the entire card — was invisible. A Mount/Vehicle deck shares no theme with a card
# whose text is exclusively about Mounts and Vehicles.
#
# Scoped to an INTERACTION clause, not a bare mention, so a Vehicle's own crew reminder
# text doesn't retag every Vehicle with what it already is.
_TYPE_MATTERS = ("Mount", "Vehicle", "Equipment", "Saga", "Battle", "Planeswalker")
_TYPE_MATTERS_RES = [
    re.compile(r"\b(?:a|an|target|another|each|any) (%s)\b" % "|".join(_TYPE_MATTERS)),
    re.compile(r"\b(%s)s? you control\b" % "|".join(_TYPE_MATTERS)),
    re.compile(r"\b(%s) cards?\b" % "|".join(_TYPE_MATTERS)),
]
# Templates where a SPECIFIC creature type is a payoff subject the card may not itself be
# — a tribal lord / tutor (Huatli searching for and pumping Dinosaurs). Capturing the
# type lets a tribal PAYOFF share its tribe's theme, so it reads KEY in that tribal deck
# instead of merely role-player (Huatli → 28/28a was under-read). Matched on ORIGINAL-case
# text: MTG oracle text capitalizes real tribes ("Dinosaurs you control") but lower-cases
# the generic "creatures you control", so `[A-Z][a-z]+` is itself a strong tribe filter.
_TRIBAL_PAYOFF_RES = [
    re.compile(r"\b([A-Z][a-z]+)s you control\b"),
    # "search your HAND AND/OR library for a Dragon card" (Last Light of Durin's Day)
    # matched nothing while the pattern demanded "search your library for" verbatim —
    # so a Dragon TUTOR carried no Dragon theme and `suggest-homes` never offered it to
    # the roster's 23-Mountain, 18-Dragon deck. One template, one word, one silent miss.
    re.compile(r"\bsearch [^.]{0,40}?\bfor (?:a|an) ([A-Z][a-z]+) card\b"),
    re.compile(r"\bother ([A-Z][a-z]+)s?\b"),
    re.compile(r"\b([A-Z][a-z]+) creatures you control\b"),
]

# HEIST — casting cards you don't own. A whole archetype (exile an opponent's card, then
# cast or play it yourself) had NO tag: Dream Harvest, Outrageous Robbery, Kotis, Laughing
# Jasper Flint and Rakdos, the Muscle carried a BLANK or near-blank Synergies cell, so the
# spine of a heist deck was invisible to `suggest` / `suggest-homes` / `cuts`. 81 pool cards
# (0.51%), which reads as maximally SPECIFIC to the idf model — correct for a build-around,
# and well clear of the 4-card floor that got a `clone` tag rejected as not-a-theme.
#
# NAMED `heist`, NOT `theft`, because **`theft` was already taken** — see the "gain control
# of" rule in MECHANIC_RULES, which covers stealing a permanent already on the battlefield
# (Act of Treason, Agent of Treachery, Mind Control). Reusing the name silently UNIONED the
# two: 93 gain-control cards merged into this theme, taking it from 81 cards to 174 and
# destroying exactly the specificity that makes an idf theme useful — while `check_all`
# stayed green, because a tag collision breaks no invariant. The two effects are
# mechanically different and a deck built on one is not automatically helped by the other,
# so they stay separate tags. Check MECHANIC_RULES for the name before adding a theme.
#
# Two-part match, because the cast clause and the opponent's zone usually sit in DIFFERENT
# SENTENCES ("…exiles the top card of their library. You may cast it"), so a same-sentence
# test structurally cannot see the most common templating. The loose form therefore gets a
# BACKWARD PROXIMITY window, the technique deck.py's rationale audit already uses. Both
# halves are required so the large self-exile families — impulse draw ("exile the top card
# of YOUR library, you may play it"), foretell, adventure — stay out.
_HEIST_WINDOW = 240
_HEIST_CAST_LOOSE = re.compile(
    r"you may (?:\w+ ){0,3}?\b(?:cast|play)\b "
    r"(?:it|that|those|them|the exiled|spells?|cards?|up to \w+|any number of)", re.I)
_HEIST_CAST_STRICT = re.compile(
    r"you may (?:\w+ ){0,3}?\b(?:cast|play)\b[^.]{0,90}?exiled"
    # \b is load-bearing: without it the `play` inside "each PLAYer … from their graveyard"
    # matched 13 graveyard-HATE cards (Relic of Progenitus, Endurance, Gaea's Blessing) —
    # this project's signature bug, a pattern firing on text nobody meant it to read.
    r"|\b(?:cast|play)\b[^.]{0,70}?from (?:\w+ ){0,2}?(?:opponent|player|their)(?:'s)? graveyard"
    r"|from among (?:them|those cards|cards exiled|the exiled cards)[^.]{0,60}?without paying"
    # reanimating out of THEIR graveyard is theft too (Scion of Darkness, Zareth San)
    r"|(?:card|permanent)[^.]{0,60}?from that player's graveyard onto the battlefield under your control"
    r"|exiled with (?:it|\w+)[^.]{0,60}?onto the battlefield under your control", re.I)
_HEIST_OPP_ZONE = re.compile(
    r"opponent(?:s)?(?:'s)? (?:library|hand|graveyard)"
    # The opponent must be the SUBJECT of the exile ("each opponent chooses a creature they
    # control and exiles it"). Commas are excluded from the gap because a comma means a new
    # clause and the subject has changed: Fireglass Mentor's "if an opponent lost life this
    # turn, exile the top two cards of YOUR library" is self-impulse, and a gap that crossed
    # the comma read it as a heist.
    r"|opponent(?:s)? [^.,]{0,45}?\b(?:exiles?|mills?|reveals?)\b"
    # both word orders: "the top X CARDS OF target opponent's library" (Black Cat) and
    # "cards … from THE TOP OF target player's library" (Rakdos, the Muscle).
    r"|top (?:\w+ |\{?[Xx]\}? )?cards? of (?:the )?(?:their|that|target|an|each) ?(?:player's|opponent's)? ?library"
    r"|top of (?:their|that player's|target player's|target opponent's|an opponent's) library"
    r"|(?:their|that player's|target player's) (?:library|hand|graveyard)"
    r"|put into an opponent's graveyard|defending player", re.I)


# EXILE CAST — the card is cast from EXILE rather than from hand, or it PAYS OFF doing so.
# 266 pool cards (1.68%), in the same band as `pay life` (2.2%).
#
# The gap this closes: warp / plot / foretell / Adventure all put the card in EXILE and cast
# it from there on a later turn, but the keyword map sent them to `tempo` / `cost-reduction`
# — which describe the DISCOUNT and say nothing about the ZONE. So the axis three decks are
# built on (24 Eternal Flame, 45 Exile Dividend, 45a) had no tag, and three cards in a row
# failed to surface for them: Spider-Verse ("whenever you cast a spell from anywhere other
# than your hand, copy it") returned NO fits at all because its only tag was `Spider`;
# Virtue of Loyalty pointed at counters decks instead of 45, whose payoffs its Adventure
# half would trigger; and Norman Osborn read as a generic graveyard card.
#
# ENABLER and PAYOFF share one tag, the way `lifegain` tags both the card that gains life
# and the card that merely cares — a deck wants both halves and the idf model wants them on
# the same axis.
#
# SCOPED TO EXILE. The graveyard half (flashback / escape / disturb / unearth / mayhem …)
# is deliberately NOT included: the keyword map already routes those to `recursion` +
# `graveyard`, so they are covered, and folding them in would take the theme to 613 cards
# (3.86%) — past the point where it still identifies an archetype. `impulse` likewise stays
# separate: that tags exiling from your own library to PLAY the exiled card (Light Up the
# Stage), which is a different action from the card itself being cast out of exile.
_EXILE_CAST_ENABLE = re.compile(r"\bWarp\b|\bPlot\b|\bForetell\b", re.I)
_EXILE_CAST_PAYOFF = re.compile(
    r"whenever you cast[^.]{0,80}?from (?:exile|your graveyard|anywhere other than your hand)"
    r"|spells? you cast from (?:exile|your graveyard)[^.]{0,40}?cost"
    r"|permanent[^.]{0,40}?enters from exile"
    r"|cast a spell from anywhere other than your hand", re.I)


def is_exile_cast_text(type_line, x):
    """True when the card is cast FROM EXILE, or rewards casting from outside your hand."""
    if "adventure" in (type_line or "").lower():
        return True          # the Adventure half exiles, then you cast the creature from exile
    if not x:
        return False
    return bool(_EXILE_CAST_ENABLE.search(x) or _EXILE_CAST_PAYOFF.search(x))


def is_heist_text(x):
    """True when the card lets YOU cast/play a card out of an OPPONENT's zone."""
    if not x:
        return False
    if _HEIST_CAST_STRICT.search(x) and _HEIST_OPP_ZONE.search(x):
        return True
    return any(_HEIST_OPP_ZONE.search(x[max(0, m.start() - _HEIST_WINDOW):m.start()])
               for m in _HEIST_CAST_LOOSE.finditer(x))


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
    # Tribal-matters PAYOFF: add the creature type a lord/tutor REWARDS (which it may not
    # itself be) so it shares that tribe's theme — see _TRIBAL_PAYOFF_RES. Scanned on the
    # original-case text (Title-case = a real tribe); _NON_TRIBE_WORDS drops false hits.
    for rx in _TRIBAL_PAYOFF_RES:
        for m in rx.finditer(text):
            typ = m.group(1)
            if typ and typ not in _NON_TRIBE_WORDS and typ not in tags:
                tags.append(typ)
    # Card types the card's TEXT builds around (see _TYPE_MATTERS_RES).
    for rx in _TYPE_MATTERS_RES:
        for m in rx.finditer(text):
            tt = m.group(1)
            if tt not in tags:
                tags.append(tt)
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
        if not k or is_noise_keyword(k):
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

    # This writer emits ONLY the canonical library columns, so it must never be pointed
    # at a derived file (card-pool.csv / card-mana.csv) — that would drop Rarity /
    # Legalities / Released and break every format, rotation and wildcard lookup
    # (audit F-02). Refuse up front, before any work.
    problem = csv_schema_error(args.path)
    if problem:
        eprint(f"ERROR: {problem}\n"
               "       To refresh a DERIVED file's synergy tags, rebuild it with its own "
               "builder (build_pool.py), which re-derives tags via tags_for().")
        return 1

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
