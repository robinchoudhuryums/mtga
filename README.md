# MTG Arena Card Library

A structured record of Robin's MTG Arena collection, used as a reference during
deck-building sessions. The collection lives in a single CSV file at the repo
root; a small set of standard-library Python scripts help validate, enrich,
search, and build decks against it.

## The data: `card-library.csv`

One row per unique card **printing** (the same card in two sets = two rows).

| Column           | Notes |
|------------------|-------|
| Card Name        | Full printed name. For MDFC/Adventure cards, front-face name only (unless the back matters for search, e.g. `Cheerful Osteomancer // Raise Dead`). |
| Type             | Full type line, e.g. `Legendary Creature — Merfolk`. |
| Card Text        | Oracle text, verbatim where wording affects rulings. |
| Color(s)         | Color/mana shorthand, e.g. `U`, `B/G`, `Colorless`. |
| Synergies        | Free-text deck-building tags, separated by semicolons. |
| Set Code         | Three/four-letter set code. |
| Collector #      | Collector number within that set printing. |
| Quantity Owned   | Integer count owned. Left **blank** (not `0`) when ownership is unconfirmed. |

Fields containing commas are quoted per standard CSV escaping (the scripts
handle this automatically).

## Tooling

All scripts live in `scripts/` and run on Python 3 with no dependencies, except
`sheets_sync.py` (see below). Run them from the repo root.

### Validate — catch problems early

```
python3 scripts/validate.py
```

Checks the header, that every row has all 8 columns, that Card Name is present,
that Quantity Owned is blank or a non-negative integer, and that there are no
duplicate printings. Warns about rows still missing Type/Card Text. Exits
non-zero on errors, so it doubles as a pre-commit / CI check.

### Enrich — auto-fill from Scryfall

```
python3 scripts/enrich.py --dry-run     # preview
python3 scripts/enrich.py               # fill blank Type / Card Text / Color(s) / Collector #
```

Looks each card up on [Scryfall](https://scryfall.com/docs/api) (by name, and by
set code when present) and fills only **blank** fields — your Synergies and
Quantity Owned are never touched. So you can add rows with just a Card Name (and
ideally a Set Code) and let this backfill the rest. Handles multi-face cards.

**Set codes & collector numbers:** Type, Card Text, and Color(s) are the same
across every printing, so they're filled from any match. Collector # is
printing-specific, so it's only written when the Set Code resolves to a real
Scryfall printing. A few MTG Arena set codes differ from Scryfall's (e.g. Arena
`DAR` = Scryfall `DOM` for Dominaria) — known ones are mapped automatically. If a
set code isn't recognized, enrich still fills the shared fields but leaves
Collector # blank and warns, so a wrong number is never written silently. (Add
more mappings in `SET_ALIASES` at the top of `scripts/enrich.py` as you hit them.)

> Requires outbound access to `api.scryfall.com`. Some managed/CI environments
> block it by policy; if so, run enrich locally. No API key needed.

### Query — search the collection

```
python3 scripts/query.py --color U --type Merfolk      # blue Merfolk
python3 scripts/query.py --synergy counters            # counters-matter cards
python3 scripts/query.py --set MSH --text "draw a card"
python3 scripts/query.py --min-owned 1 --count         # how many distinct cards you own
python3 scripts/query.py --color G --csv               # emit CSV to pipe elsewhere
```

Case-insensitive substring filters, AND-ed together. Table output by default.

### Deck — check a deck against your collection

```
python3 scripts/deck.py decks/example-merfolk.txt
```

Reports owned-vs-needed per card and flags shortfalls or cards missing from the
library. Deck file format is documented in [`decks/README.md`](decks/README.md).

### Sheets sync — round-trip with Google Sheets (optional)

```
pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export MTGA_SHEET_ID=<sheet id from its URL>
python3 scripts/sheets_sync.py push    # local CSV  -> Google Sheet
python3 scripts/sheets_sync.py pull    # Google Sheet -> local CSV
```

Keeps the CSV and the companion Google Sheet in sync. Setup details are in the
docstring at the top of `scripts/sheets_sync.py`. (Since the CSV is the
interchange format, you can also import/export manually in Sheets without this.)

## Typical workflow

1. Add rows to `card-library.csv` (Card Name + Set Code + Quantity is enough).
2. `python3 scripts/enrich.py` to backfill card details from Scryfall.
3. `python3 scripts/validate.py` to confirm the file is clean.
4. `python3 scripts/query.py …` while brewing; `python3 scripts/deck.py …` to
   check buildability.
