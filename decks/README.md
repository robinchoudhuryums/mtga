# Decks

Constructed decks and their variations, checkable against your collection with
`scripts/deck.py`.

## Structure

One folder per **core deck**, with **variations** as sibling files:

```
decks/
  01-avatar-tempo/
    deck.txt              # the base deck        -> id "1"
    1a-counter-heavy.txt  # a variation          -> id "1a"
    1b-aggro-splash.txt   # another variation    -> id "1b"
    notes.md              # optional free-form notes
```

- The folder name is `NN-slug` (e.g. `01-avatar-tempo`); its number is the core
  deck's id.
- `deck.txt` is the base build. Variant files are named `<id>-slug.txt` where the
  id is the core number plus a letter (`1a`, `1b`, …).
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
#: notes: removal-heavy base build

# Creatures
4 Katara, Bending Prodigy (TLA) 59
2 Aang, the Last Airbender (TLA) 4

# Lands
9 Plains
9 Island
```

Variations are **full lists too** (not diffs) — so every file is robust,
independently checkable, and can be pasted straight back into Arena. Use
`deck.py diff` to see what a variation changes; git history tracks how each
iteration evolves. (A `#: based-on:` line is just a note for humans.)

Basic lands (Plains/Island/Swamp/Mountain/Forest/Wastes) are treated as
unlimited — they don't count against your collection.

## Commands

```
python3 scripts/deck.py list          # every deck + variant, with buildable status
python3 scripts/deck.py check 1a      # owned vs needed vs your collection
python3 scripts/deck.py diff 1 1a     # what variant 1a changes vs base deck 1
python3 scripts/deck.py arena 1a      # emit an Arena-importable decklist to paste back
python3 scripts/deck.py stats 1a      # mana curve, color balance, type breakdown
```

`stats` fetches mana values from Scryfall once and caches them in
`.mana-cache.json` (gitignored).

## Adding a deck

Paste your Arena deck export into `decks/NN-name/deck.txt`, add a `#: name:`
header, and you're done — or just hand it to Claude Code and it'll place it.
