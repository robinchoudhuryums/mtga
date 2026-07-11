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

### Import — ingest an Arena export

```
python3 scripts/import_arena.py batch.txt          # merge a deck/collection export
python3 scripts/import_arena.py deck.txt --skip-basics   # reconcile owned counts from a built deck
```

Parses MTG Arena's `<qty> <Name> (<SET>) <collector#>` export format and merges
it into `card-library.csv`, keyed by Card Name + Set Code + Collector # (one row
per printing). Re-imports take the **max** quantity seen (decks share one
collection, so counts don't sum); `--skip-basics` ignores basic lands so a deck
list can true up owned counts without polluting the collection. Follow with
`enrich.py` to backfill new cards.

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

Looks cards up on [Scryfall](https://scryfall.com/docs/api) in **batches** (75 per
request via the collection endpoint, so a few hundred cards take seconds) and
fills only **blank** fields — your Synergies and Quantity Owned are never
touched. So you can add rows with just a Card Name (and ideally a Set Code) and
let this backfill the rest. Handles multi-face cards (with a single-card fallback
for `Front // Back` names).

**Set codes & collector numbers:** Type, Card Text, and Color(s) are the same
across every printing, so they're filled from any match. Collector # is
printing-specific, so it's only written when the matched printing's set equals
the row's Set Code (after mapping known Arena→Scryfall differences — e.g. Arena
`DAR` = Scryfall `DOM` for Dominaria). When the sets don't line up, enrich still
fills the shared fields but leaves Collector # as-is, so a wrong number is never
written silently. (Add more mappings in `SET_ALIASES` at the top of
`scripts/enrich.py` as you hit them.)

> Requires outbound access to `api.scryfall.com`. Some managed/CI environments
> block it by policy; if so, run enrich locally. No API key needed.

### Tag synergies — populate deck-building tags

```
python3 scripts/tag_synergies.py --dry-run   # preview
python3 scripts/tag_synergies.py             # fill blank Synergies cells
```

Derives tags for the Synergies column from each card's type line (tribal
subtypes, key card types), oracle text heuristics (counters, graveyard,
reanimator, lifegain, removal, burn, ramp, tokens, …), and — when `card-mana.csv`
has been built — **Scryfall's authoritative keyword list** mapped to
deck-building themes (Surveil → `surveil; graveyard`, Convoke → `convoke;
go-wide; ramp`, Escape → `graveyard; recursion`, …). Using Scryfall's per-card
keywords means real-keyword coverage is complete and maintained, not a hand-kept
list; a small `FLAVOR_KEYWORDS` denylist drops Universe-Beyond flavor ability
names (Firaga, Wave Cannon, …) that Scryfall also reports as keywords, so they
don't pollute the tags. Fills only blank cells by default (`--force` regenerates). These make `query.py
--synergy` / `pool.py --synergy` and the gallery filters useful; tags are
hand-editable. Rerun `build_mana.py` then `tag_synergies.py --force` after
importing new cards to refresh keyword-aware tags.

### Query — search the collection

```
python3 scripts/query.py --color U --type Merfolk      # blue Merfolk
python3 scripts/query.py --synergy counters            # counters-matter cards
python3 scripts/query.py --set MSH --text "draw a card"
python3 scripts/query.py --min-owned 1 --count         # how many distinct cards you own
python3 scripts/query.py --color G --csv               # emit CSV to pipe elsewhere
```

Case-insensitive substring filters, AND-ed together. Table output by default.
`query.py` searches only cards you **own** (`card-library.csv`); to search the
full set of cards you *could* play, use `pool.py` below.

### Card pool — reference cards you don't own yet

For deck-building you often want to see options beyond your collection. The pool
is a separate reference of Arena-playable cards (built from Scryfall), kept apart
from your owned inventory. `card-library.csv` stays exactly your collection.

```
python3 scripts/build_pool.py            # (re)build card-pool.csv — Standard-legal Arena cards
python3 scripts/build_pool.py --all      # every Arena-craftable card (~15.8k) instead
```

`card-pool.csv` carries a **Rarity** column (= Arena wildcard cost). Search it
with `pool.py`, which joins against what you own so each result is flagged owned
or craftable:

```
python3 scripts/pool.py --color U --text "counter target"    # all blue counters, owned or not
python3 scripts/pool.py --color G --synergy ramp --unowned   # green ramp you'd need to craft
python3 scripts/pool.py --synergy removal --rarity rare,mythic --unowned
python3 scripts/pool.py --type Merfolk --count               # how many exist vs. how many you own
```

Each row shows `×N` (copies owned) or `craft`, plus rarity; the summary totals
the wildcard cost of the craftable results. Rebuild the pool after a new set
releases. For formats outside the stored pool (e.g. a one-off Historic card),
just ask Claude Code — it can query Scryfall live and cross-check your library.

### Deck — manage decks and variations

```
python3 scripts/deck.py list          # every deck + variant, with buildable status
python3 scripts/deck.py check 1a      # owned vs needed vs your collection
python3 scripts/deck.py diff 1 1a     # what variant 1a changes vs base deck 1
python3 scripts/deck.py arena 1a      # emit an Arena-importable decklist to paste back
python3 scripts/deck.py stats 1a      # mana curve, color balance, type breakdown
python3 scripts/deck.py mana 1a       # hybrid-aware color requirements
python3 scripts/deck.py tribes 1a     # creature-subtype breakdown + type-matters synergies
```

`stats` also flags **cost flexibility** (`◊` — cards whose text reduces their
cost or grants flash, e.g. convoke/delve/"costs {1} less", so the printed mana
value doesn't mislead). `tribes` reads oracle text to surface **type-matters
payoffs** — e.g. a Saga that rewards Krakens/Leviathans/Merfolk/Octopuses/
Serpents will list those types and how many of your creatures qualify — so
cross-type tribal synergies aren't missed.

Decks live under `decks/` as one folder per core deck, with variations as sibling
files (`deck.txt` → id `1`, `1a-*.txt` → id `1a`). Basics are treated as
unlimited. Full format + structure docs are in [`decks/README.md`](decks/README.md).

**Mana analysis (`stats` curve and `mana`) reads `card-mana.csv`** — real mana
costs captured from Scryfall by `build_mana.py`. This matters because the CSV's
Color(s) column stores color *identity*, which can't tell a hybrid `{W/U}`
(payable with either color) from a strict `{W}{U}` (needs both). `deck.py mana`
counts hybrids as flexible, so "how much white do I really need?" gets an honest
answer. Rebuild the data after importing new cards:

```
python3 scripts/build_mana.py          # refresh card-mana.csv from card-library.csv
python3 scripts/build_mana.py --pool   # also cover card-pool.csv names
```

### Gallery — a visual, filterable view of the collection

```
python3 scripts/build_gallery.py     # resolve card images + build gallery.html
open gallery.html                    # (macOS) view it in your browser
```

Generates a self-contained `gallery.html`: a **collection dashboard** (totals,
color/type/set breakdowns, and clickable top-synergy chips) above a filterable
grid of your cards with real card art, quantity badges, and set/collector labels.
Search by name/type/text/synergy, filter by color (WUBRG/Colorless) or set, and
sort by name/set/quantity — all in the browser, no server. Card data is embedded
in the file; images are hotlinked from Scryfall's CDN (so you need internet to see
the art, but the file stays tiny and portable).

Image URLs are resolved via Scryfall's batch endpoint (≈4 requests for a few
hundred cards) and cached in `.image-cache.json` (gitignored) so rebuilds are
instant and the canonical CSV is never modified. Use `--no-fetch` to rebuild
from cache without touching the network. Rerun after importing new cards.

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

## Integrity check & workflow commands

`python3 scripts/check_all.py` is the project's integrity gate — it verifies the
invariants in [`CLAUDE.md`](CLAUDE.md) (CSV structure, `card-mana.csv` coverage,
derived files present, decks parse) and exits non-zero on any hard break. A
SessionStart hook runs it (quiet) so drift surfaces immediately.

Claude Code slash commands live in `.claude/commands/`:

- **Project:** `/check` (integrity), `/refresh` (rebuild derived data),
  `/add-deck` (ingest a pasted deck), `/tune-deck` (deck-building analysis).
- **Audit (from claude-workflow-tools):** `/broad-scan`, `/broad-implement`,
  `/sync-docs`, `/health-pulse` (quick directional read), `/roadmap` —
  project-agnostic; they read the **Cycle Workflow Config** in `CLAUDE.md` (Test
  Command = `check_all.py`, Health Dimensions, Subsystems, Invariant Library) for
  all project specifics. See also [`ROADMAP.md`](ROADMAP.md).
