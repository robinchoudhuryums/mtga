# Decks

Constructed decks and their variations, checkable against your collection with
`scripts/deck.py` — `deck.py check <id>` for ownership, `deck.py legal <id>` for
construction legality (size, copy limits, format).

## Structure

One folder per **core deck**, with **variations** as sibling files:

```
decks/
  01-avatar-tempo/
    deck.txt               # the base deck (Standard) -> id "1"
    1a-counter-heavy.txt   # a Standard variation     -> id "1a"
    1b-aggro-splash.txt    # another Standard variation-> id "1b"
    1-brawl-avatar.txt     # a Brawl adaptation        -> id "1-brawl"
    1-alchemy-avatar.txt   # an Alchemy adaptation      -> id "1-alchemy"
    notes.md               # optional free-form notes
```

- The folder name is `NN-slug` (e.g. `01-avatar-tempo`); its number is the core
  deck's id.
- `deck.txt` is the base build. **Standard sub-variants** are named `<id>-slug.txt`
  where the id is the core number plus a letter (`1a`, `1b`, …).
- **Game-type (format) variants** — an Alchemy or Brawl adaptation of a core deck is
  named `<core>-<format>[-slug].txt` and gets the id `<core>-<format>` (e.g.
  `3-brawl-knights-edge.txt` → id `3-brawl`), so it reads as *that deck's* Brawl/Alchemy
  version, **not** as another Standard sub-variant like `3a`. Recognized format tokens:
  `alchemy`, `brawl`, `historic-brawl`, `timeless`, `explorer`, `pioneer`, `modern`,
  `pauper`, `historic`. The token is only for the id — the deck's `#: format:` header
  is the authoritative format the tooling checks. A **Brawl** deck adds a
  `#: commander:` header (a legendary creature/planeswalker); `deck.py legal` then
  enforces singleton (1-of) **and** that every card sits within the commander's color
  identity. (Alchemy needs no separate file unless you want to tune it apart — a
  Standard deck is already Alchemy-legal; `deck.py legal <id> --format alchemy` confirms
  it and notes any Alchemy-rebalanced cards, which play as their `A-` version.)
- Loose `decks/<name>.txt` files (no folder) also work, using the filename as id.

## Deck file format

A full, self-contained list in **Arena export format** — the same
`<qty> <Name> (<SET>) <collector#>` you paste from the game — optionally preceded
by a metadata header. Lines starting with `#:` are metadata; plain `#` lines are
comments; blank lines are ignored.

```
#: name: Avatar Tempo
#: format: Standard
#: colors: WU
#: archetype: Azorius (W/U) fliers / tempo — one-line "meant-for" summary.
#: notes: removal-heavy base build

# Creatures
4 Katara, Bending Prodigy (TLA) 59
2 Aang, the Last Airbender (TLA) 4

# Lands
9 Plains
9 Island
```

`#: archetype:` is a one-line identity (colors + core plan; for a variant, how it
differs from its core) that `deck.py list` prints under each deck — a quick guard
against homogenizing a deck when scanning the roster for swaps. `#: notes:` is
free-form and **may span several lines** (repeat `#: notes:`); the tooling now
concatenates them in order, so the full note survives rather than only the last
line. If a deck has no `#: archetype:`, `list` falls back to the first sentence of
its notes.

`#: plan:` (optional — `aggro` | `control` | `combo` | `midrange`) declares the deck's
game plan so `deck.py tier` weights the right axes: an **aggro** deck is graded on its
clock (curve + cheap threats + reach) instead of the interaction suite it doesn't want.
Without it the plan is read from `#: archetype:` keywords, else inferred, else midrange
(the default interaction+card-advantage floor).

Variations are **full lists too** (not diffs) — so every file is robust and
independently checkable. Use `deck.py diff` to see what a variation changes; git
history tracks how each iteration evolves. (A `#: based-on:` line is just a note
for humans.)

**Importing into MTG Arena:** don't paste the raw file — its `# Creatures` /
`# Lands` section headers and `#:` metadata are for humans and Arena's importer
rejects them. Run `python3 scripts/deck.py arena <id>` and paste *that* — it emits
the clean, `Deck`-prefixed `<qty> <Name> (<SET>) <#>` list Arena accepts (comments
and metadata stripped).

Basic lands (Plains/Island/Swamp/Mountain/Forest/Wastes) are treated as
unlimited — they don't count against your collection.

### Flex section (suggested swaps)

A deck file may end with a **flex block** recording swaps you're considering but
haven't committed. These are plain comments — lines starting with `#~` — so they
never count toward the 60, never affect buildability, and are stripped from the
Arena export. Format each as pipe-separated columns; a `-` prefix is the card
coming out, `+` the card going in, and any other column is a free-form note:

```
# Flex — suggested swaps (comments; not part of the 60). See: deck.py flex 19a
#~ -Earthbender Ascension | +Bushwhack | fight OR fetch a basic; also feeds landfall
#~ -Rabaroo Troop | +Harsh Annotation | clean hard removal — the deck runs almost none
#~ note: all three swaps are OWNED (0 wildcards)
```

`deck.py flex <id>` prints the block and enriches each `+In` card with its mana
cost, rarity, and owned count. The editing app also surfaces the block in a
read-only "Suggested swaps" panel. `/tune-deck` can append a flex block when it
builds or audits a deck.

## Commands

```
python3 scripts/deck.py list          # every deck + variant, with buildable status
python3 scripts/deck.py check 1a      # owned vs needed + castability lint (off-color cards)
python3 scripts/deck.py diff 1 1a     # what variant 1a changes vs base deck 1
python3 scripts/deck.py arena 1a      # emit an Arena-importable decklist to paste back
python3 scripts/deck.py stats 1a      # curve, colors, type breakdown, functional roles
python3 scripts/deck.py mana 1a       # hybrid-aware color requirements + castability lint
python3 scripts/deck.py suggest 1a --owned   # owned pool cards that fit (0 wildcards; --limit 0 = all)
                                             #   (filters to the deck's #: format: by default; --format / --any-format to change)
python3 scripts/deck.py flex 1a       # suggested swaps recorded in the file (#~ lines)
python3 scripts/deck.py swap 1a --cut A --add B   # preview a swap's deltas; --apply writes (.bak)
python3 scripts/deck.py apply-flex 1a 2      # promote flex swap #2 into the 60 (--apply writes)
pbpaste | python3 scripts/deck.py verify 1a  # diff a pasted Arena export against the stored deck (identical / +−)
```

`stats` also reports **functional roles** — a heuristic read of card text that
counts removal / counters / card advantage / ramp / anthems, so "light on
interaction" is measured, not eyeballed. `check` and `mana` run a **castability
lint** against the deck's declared `#: colors:` header: a strict off-color pip is
uncastable, an off-color identity (a hybrid you'd pay on-color, or an off-color
ability) is a softer heads-up. `swap` and `apply-flex` default to a **dry-run**
(before/after deltas: card count, creatures, avg MV, color identity) and only
write with `--apply`, always leaving a timestamped `.bak` and re-checking that the
file re-parses at the same card total (INV-04).

`stats` fetches mana values from Scryfall once and caches them in
`.mana-cache.json` (gitignored).

## Adding a deck

Paste your Arena deck export into `decks/NN-name/deck.txt`, add a `#: name:`
header, and you're done — or just hand it to Claude Code and it'll place it.
