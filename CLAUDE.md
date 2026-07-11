# CLAUDE.md — MTG Arena Card Library

A structured record of Robin's MTG Arena collection plus Python tooling to
enrich, search, analyze, and build decks against it. See `README.md` for user
docs. This file is the source of truth for the workflow commands in
`.claude/commands/`.

## Key Design Decisions

- **`Color(s)` is color IDENTITY, not mana cost.** For anything mana-related
  (castability, hybrids, pip counts) use `card-mana.csv` / `deck.py mana`
  (hybrid-aware). Never infer mana requirements from `Color(s)`.
- **`card-library.csv` is the owned inventory** and stays compatible with the
  companion Google Sheet (fixed 8-column header). Derived/reference data lives
  in separate files (`card-mana.csv`, `card-pool.csv`) so the CSV isn't polluted.
- **Deck-dump imports undercount quantities** (each line is a lower bound). True
  up owned counts by reconciling from a built deck: `import_arena.py <deck>
  --skip-basics`.
- **Basic lands are not in the collection** (unlimited in Arena). `deck.py`
  treats them as unlimited; imports skip them with `--skip-basics`.
- **Owned copies are fungible across printings.** For buildability, `deck.py`
  and `pool.py` both sum a card's `Quantity Owned` across every printing (a card
  owned 1× in two sets counts as 2) — never count a single printing in isolation.

## Common Gotchas

- **Don't judge a card by printed mana value or a single subtype.** `deck.py
  stats` flags cost flexibility (`◊` cheaper / `△` added cost) and `deck.py
  tribes` reads oracle text for cross-type synergies (e.g. a Serpent feeding a
  Leviathan payoff). Read the card text (stored in the CSV) for real evaluation.
- **MTG Arena set codes can differ from Scryfall** (e.g. Arena `DAR` = Scryfall
  `DOM`). `enrich.py` maps known ones (`SET_ALIASES`) and never writes a
  collector # for an unconfirmed printing.
- **WIP decks legitimately show "missing" cards** in `check_all.py` — those are
  craft targets not yet owned (e.g. Atlantis Attacks 18/18a). Not a failure.
- **Regenerate derived data after imports**, in order: `enrich.py` →
  `tag_synergies.py --force` (needs `build_mana.py` first for keyword tags) →
  `build_pool.py` → `build_gallery.py`. Or run `/refresh`.
- **Scryfall egress**: needs `api.scryfall.com` + `*.scryfall.io` allowed; some
  managed environments block it. Enrichment/pool/mana builds require it.
- **The optional editing app (`scripts/app.py`) mutates `card-library.csv`** via
  validated writes + a timestamped `.bak`, appends a `card-mana.csv` row when you
  add a card (to keep INV-02), and also edits deck files under `decks/` (gated on
  INV-04 — the file must re-parse with every card line intact — `.bak`'d, with
  section comments preserved). After an app-editing session, run `/refresh` so
  derived data catches up — an added card needs `build_mana.py` for its real
  cost/keywords, `tag_synergies.py` for keyword tags, and `build_gallery.py` for
  its art (until then it shows a fallback tile).
- **`card-pool.csv` is Standard-legal Arena by default**; rebuild with `--all`
  for the full Arena pool. For cards outside the stored pool, query Scryfall live.

## Known Issues

- A handful of recurring Universe-Beyond flavor *mechanics* (Vivid, Job select,
  Opus, …) aren't in `tag_synergies.py`'s keyword→theme map, so they're tagged
  verbatim. Card-*unique* flavor ability names (Firaga, Wave Cannon, …), which
  Scryfall also reports as keywords, are dropped via the `FLAVOR_KEYWORDS`
  denylist so they don't pollute the tags.
- A few genuinely text-less vanilla creatures trip validate's blank-Card-Text
  warning (expected, not an error).

## Cycle Workflow Config

**Test Command:** `python3 scripts/check_all.py`
(deterministic integrity gate; exits non-zero on any hard invariant break)

**Health Dimensions:**
- Data Integrity — CSV structure, no drift between library and derived files
- Enrichment & Tagging Accuracy — Scryfall-sourced fields and synergy tags
- Deck Tooling Correctness — deck.py / query.py / pool.py behavior
- Deck-Building Insight — mana (hybrid-aware), tribes, cost-nature, pool value
- Presentation — gallery correctness and freshness
- Documentation Currency — README / CLAUDE.md match the code and data

**Subsystems:**
- Data: card-library.csv, card-pool.csv, card-mana.csv
- Ingest & Enrich: scripts/import_arena.py, scripts/enrich.py, scripts/tag_synergies.py, scripts/build_pool.py, scripts/build_mana.py, scripts/sheets_sync.py, scripts/lib.py
- Analysis: scripts/deck.py, scripts/query.py, scripts/pool.py, scripts/validate.py, scripts/check_all.py
- Presentation: scripts/build_gallery.py, gallery.html, image-manifest.json, scripts/app.py (optional Flask editor), templates/, Makefile (`make app` launcher / `make check`)
- Decks: decks/

**Invariant Library:**
- INV-01 | card-library.csv has the canonical 8-column header, every row has 8 fields, no duplicate (Card Name, Set Code, Collector #) printing, and Quantity Owned is blank or a non-negative integer | Subsystem: Data | Verify: scripts/check_all.py (via validate.py)
- INV-02 | Every Card Name in card-library.csv has a row in card-mana.csv | Subsystem: Data | Verify: scripts/check_all.py
- INV-03 | Derived reference files exist: card-mana.csv, card-pool.csv, gallery.html | Subsystem: Data/Presentation | Verify: scripts/check_all.py
- INV-04 | Every deck file under decks/ parses with no malformed card lines | Subsystem: Decks | Verify: scripts/check_all.py
- INV-05 | Color(s) stores color identity; actual mana cost lives only in card-mana.csv | Subsystem: Data | Verify: design/manual
- INV-06 | Synergy tags are keyword-aware — regenerate via build_mana.py then tag_synergies.py --force after imports | Subsystem: Ingest | Verify: manual

**Policy Configuration:** threshold 6/10; 2 consecutive cycles below triggers a policy response.

**Regression Scenarios** (manual walks; the Test Command above is the primary gate):
1. Ingest a batch — `import_arena.py <file>` → `enrich.py` → `validate.py` → `build_gallery.py`. Expect: validate clean, gallery card count == library row count.
2. Analyze a deck — `deck.py check|mana|tribes|stats <id>`. Expect: no traceback; mana is hybrid-aware; tribes surfaces type-matters payoffs.
3. Refresh derived data — `build_mana.py` → `tag_synergies.py --force` → `build_pool.py` → `build_gallery.py` → `check_all.py`. Expect: check_all reports all invariants hold.
4. Edit via the app — start `scripts/app.py`, change a quantity and Save, add a card, then open a deck (Decks →), change a card's quantity and Save; run `check_all.py`. Expect: CSV + deck file updated, `.bak`s written, and all invariants hold (INV-02 since add appends a card-mana.csv row; INV-04 since deck save re-parses cleanly).

**Frozen Subsystems:** none.

**Deploy Command:** N/A — this project has no deploy step (data + local tooling; changes ship by commit/push).

## Command provenance

`broad-scan`, `broad-implement`, `sync-docs`, `health-pulse`, and `roadmap` in
`.claude/commands/` are copied **verbatim** from
[claude-workflow-tools](https://github.com/robinchoudhuryums/claude-workflow-tools);
they stay project-agnostic and read everything from the Cycle Workflow Config
above. To update them, re-copy the files when that repo bumps them — don't edit
them here. `check`, `refresh`, `add-deck`, and `tune-deck` are project-specific.
