# CLAUDE.md — MTG Arena Card Library

A structured record of Robin's MTG Arena collection plus Python tooling to
enrich, search, analyze, and build decks against it. See `README.md` for user
docs. This file is the source of truth for the workflow commands in
`.claude/commands/`.

## Player Profile

- **Deck-building style: creative-leaning.** Robin values inventive / entertaining
  / flavorful play over squeezing out the last few points of win-rate — happy to
  run a functional-but-spicy card over a "correct" staple. `/tune-deck` reads this
  by default (protect signature/spice cards, reserve a fun budget, keep flavorful
  picks unless the power gap is large); override per run with `competitive` /
  `balanced` in the args. Still always report the by-the-numbers pick — the
  preference shifts recommendations, not honesty.

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
- **Decks share the collection — a card is NOT consumed by a deck.** In MTG Arena
  the whole collection is available to every deck at once, so one owned copy can
  sit in any number of decks *simultaneously*; owning N copies lets each deck run
  up to N (and up to the format limit) with no competition between decks. The
  buildability check already models this correctly — it compares *each* deck's
  required quantity against total owned, independently, so a card in 5 decks
  never needs 5× copies. When recommending swaps, therefore, never frame decks as
  competing for a card, tell the user to "pick" one home, or "split" copies across
  decks: the same copy can go everywhere it fits. (Recurring misread in past
  sessions — the only real question per deck is "do I want it here," not "can I
  spare a copy.")

## Common Gotchas

- **Don't judge a card by printed mana value or a single subtype.** `deck.py
  stats` flags cost flexibility (`◊` cheaper / `△` added cost), buckets spells
  into functional roles (removal / card advantage / ramp / …, heuristic from
  oracle text), and `deck.py tribes` reads oracle text for cross-type synergies
  (e.g. a Serpent feeding a Leviathan payoff). `deck.py mana` / `check` also run
  a castability lint against the deck's declared `#: colors:`. Read the card text
  (stored in the CSV) for real evaluation.
- **Previewing and applying swaps.** `deck.py swap <id> --cut A --add B` shows a
  swap's before/after deltas plus the **full oracle text of BOTH the cut and add
  cards** (not just the type line) — so a later ability can't hide behind a
  truncated read (this is how M.O.D.O.K.'s board-wide −1/−1 and Momo's modal
  leaves-play trigger got missed when grading cuts from a sliced text field).
  **Always grade a cut from this full-text preview, never from a `Card Text[:N]`
  slice.** `--apply` writes with a `.bak` and an INV-04 re-check; if the add card
  is already in the deck it bumps that line rather than adding a second line for
  the same card. `deck.py apply-flex <id> <n>` promotes a `#~` flex line into the
  60. Both default to a dry run.
- **Legality lint and cut candidates are separate from ownership.** `deck.py check`
  answers "do I own this deck"; `deck.py legal <id>` answers "is it a *legal* deck"
  — size vs the format minimum, the copy limit (4, or 1 in singleton formats), and
  each nonbasic's legality in the deck's `#: format:` (from the pool's `Legalities`
  column; `--format` overrides). It exits non-zero on a real violation but treats a
  pool-absent card as *unverified*, not illegal (so WIP/older-print decks aren't
  false-flagged). `deck.py cuts <id>` is the counterpart to `suggest` (adds): it
  ranks nonland cards weakest-fit first (central-theme fit + functional role +
  tribal contribution), but it's a heuristic shortlist that can't see spice/
  signature cards — grade its picks, then preview with `swap`.
- **"Not in library" for a card you own is the deck-dump undercount symptom.**
  `import_arena.py` takes a lower bound per line, so a card can end up
  *undercounted or entirely absent* from `card-library.csv` — then `deck.py
  check` reports it as a craft target even though you own it. Reconcile via
  `import_arena.py <deck> --skip-basics` (trues up from a built deck), or append
  the row from `card-pool.csv` at the right `Quantity Owned` and rebuild the
  gallery. Hit repeatedly in practice (Primeval Bounty, Cat Collector, Inspiration
  from Beyond, Dion, …).
- **MTG Arena set codes can differ from Scryfall** (e.g. Arena `DAR` = Scryfall
  `DOM`). `enrich.py` maps known ones (`SET_ALIASES`). It fills a row's Collector #
  from the batch match when that printing's set lines up, else via a targeted
  `/cards/named?exact=&set=` lookup of the row's own set (the batch endpoint
  returns one representative printing per name, rarely the row's set) — and still
  never writes a number from an unconfirmed printing: a set it can't resolve
  leaves Collector # blank.
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
- **`card-pool.csv` now holds the full Arena pool** (`build_pool.py --all`,
  ~15.8k cards) and **`card-mana.csv` covers it** (`build_mana.py --pool`), so
  unowned cards have real costs/tags. Both tools DEFAULT to the smaller scope
  (Standard pool / library-only mana), so a plain rebuild SHRINKS coverage back —
  pass `--all` / `--pool` (as `/refresh` now does) to keep full coverage. The
  full-pool mana build is slow (Scryfall rate limits ~15.8k cards); the pool
  build itself is fast (paginated search, ~90 requests).
- **`card-wishlist.csv` is UNOWNED craft targets**, separate from the owned library
  and the full pool. `wishlist.py --add <arena-export>` appends a batch, enriching
  each card (Rarity/Color/Type/text/Synergies) from `card-pool.csv` with a Scryfall
  fallback — double-faced cards are stored under their **full `Front // Back` name**
  (matching the pool) so joins work, unlike the library's front-name convention.
  `--by-set` is the pack/gem-optimization view (wishlist cards per set by rarity);
  `--owned` flags cards you've since crafted so you can prune them. `Target`/`Note`
  are hand-annotated (deck id / `general` / `concept: …`). Not gated by check_all.
- **Auto-targeting a wishlist batch: trust STRONG, judge `review`.** `wishlist.py
  --suggest-targets` scores each card's deck fit by **theme rarity (idf)** so broad
  decks stop acting as catch-alls: naive theme-overlap over-assigns to 5-color
  decks (17) and many-themed decks (21 Gastromancer) because *generic* themes
  (etb/counters/tokens/lifegain/sacrifice) are central to nearly every deck and
  carry ~no signal — only a *specific* theme (food, earthbend, firebending, Ninja
  `sneak`, reanimator, Merfolk, …) is a confident match. Evergreen keywords
  (trample/deathtouch) are excluded from the signal (they'd else fake a match).
  Workflow for a new batch: `--add` → `--suggest-targets --write` (fills only
  blank Targets with STRONG/ok picks) → text-review the `review` cards (generic/
  multi-home/new-concept — the tag heuristic genuinely can't place these). This is
  why the first batch's 21/17 buckets needed a manual text pass and were trimmed.
- **`card-pool.csv` carries a `Legalities` column** (`;`-joined formats a card is
  legal in) so `deck.py suggest` filters craft picks to the deck's `#: format:`
  by default (override `--format` / disable `--any-format`). It's captured free
  during `build_pool.py`, but a pool built before the column exists lacks it —
  `suggest` then warns and shows all until you rebuild. `pool.py --legal <fmt>`
  uses the same data.
- **`deck.py suggest` scopes by castable colors, not identity.** It builds the
  deck's colors from the declared `#: colors:` (else mana costs), so a card's
  off-color *activated abilities* (e.g. Super-Skrull's `{4}{R}`) don't surface
  uncastable picks. Run it both ways: `--owned --limit 0` scours the collection
  for 0-wildcard upgrades already owned; `--unowned` lists craft targets.
- **`deck.py suggest` shows a cross-deck reuse count (`Decks` column).** For each
  pick it counts how many of your OTHER decks (the deck being analyzed is excluded,
  so it can't inflate its own picks) the card is *castable* (its identity ⊆ the
  deck's declared/derived colors) **and** shares ≥1 *central* theme with (a theme
  carried by ≥25% of that deck's most-common theme's copies, floor 2) — a rough
  "value per wildcard" signal, so a craft that fits several decks outranks a
  one-deck sidegrade. It weights by theme centrality rather than any single-tag
  overlap, so a card that only grazes a deck on one incidental tag no longer
  counts — but it's still broad (a generic sac/tokens card that's genuinely
  central to many decks scores high), so read it as breadth, not curated fit. A
  "High cross-deck reuse" line summarizes the top fits≥3. Factor it into a craft's
  ★/~/· weight in a flex block.
- **Flex-block craftables are format-scoped.** When a deck's `#: format:` changes,
  re-check its `#~` craft suggestions — a craftable legal under the old format may
  have rotated (hit moving decks 1/2 Historic→Standard). `deck.py flex <id>` plus
  the pool's `Legalities` column confirm.

## Known Issues

- A handful of recurring Universe-Beyond flavor *mechanics* (Vivid, Job select,
  Opus, …) aren't in `tag_synergies.py`'s keyword→theme map, so they're tagged
  verbatim. Card-*unique* flavor ability names (Firaga, Wave Cannon, …), which
  Scryfall also reports as keywords, are dropped via the `FLAVOR_KEYWORDS`
  denylist so they don't pollute the tags.
- A few genuinely text-less vanilla creatures trip validate's blank-Card-Text
  warning (expected, not an error).
- The **functional-role** breakdown (`deck.py stats`) and **castability lint**
  (`deck.py mana` / `check`) are heuristic. Roles are matched from oracle text, so
  modal cards land in several buckets and single-draw cantrips are deliberately
  *not* counted as card advantage. The lint reads the deck's `#: colors:` header,
  so a stale or intentionally-narrow header flags cards as off-color — e.g. the
  raw 83-card `19` pile is headed `WU` but is really multicolor. Fixing a stale
  header to the deck's real castable colors clears the false positives (e.g. deck
  `13` was corrected `GR`→`GWBR`). Treat a flag as signal to review, not a hard
  failure — it doesn't gate `check_all.py`.

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
- Data: card-library.csv, card-pool.csv, card-mana.csv, card-wishlist.csv
- Ingest & Enrich: scripts/import_arena.py, scripts/enrich.py, scripts/tag_synergies.py, scripts/build_pool.py, scripts/build_mana.py, scripts/sheets_sync.py, scripts/lib.py
- Analysis: scripts/deck.py, scripts/query.py, scripts/pool.py, scripts/wishlist.py, scripts/validate.py, scripts/check_all.py
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
2. Analyze a deck — `deck.py check|mana|tribes|stats|legal|cuts <id>`. Expect: no traceback; mana is hybrid-aware; tribes surfaces type-matters payoffs; legal flags size/copy/format violations; cuts ranks weakest-fit cards.
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
