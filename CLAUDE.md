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
  spare a copy.") Turn this into a *proactive* habit: when a crafted card earns a
  slot in more than one deck, offer to slot it into **all** of them (Elspeth in
  both Knight's Edge and Avengers; Wan Shi Tong in both Bloodbending and Drawn
  Conclusions) rather than asking the user to choose a single home.

## Common Gotchas

- **Inspect one card with `card.py <name>`, never a truncated slice.** `scripts/card.py
  "<name>"` (substring/fuzzy match) prints a card's **complete, untruncated oracle
  text** plus mana cost, **format legality**, owned quantity, rarity/wildcard, and
  which decks run it — all in one place. It exists to stop two recurring mistakes:
  (1) grading a card from a *sliced* read (piping `query.py --full` through `head`
  hid Morningtide's Light's "prevent all damage" clause and mis-graded the cut), and
  (2) recommending a craft without a **legality check** (Champion of Rhonas / Chord
  of Calling read as green cheat enablers but are Historic-only, not Standard;
  Heartfire Hero likewise). Before grading or recommending ANY card in chat, run
  `card.py` — the pool's `Legalities` column is authoritative, so "it's in the pool"
  is NOT "it's Standard-legal." **In code, any card-evaluation path reads the
  COMPLETE text by default** — use `lib.full_card_text(name)` (library→pool,
  never truncated); never slice a card's text to grade/classify/rank it.
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
  **Always grade a cut from full oracle text — the `swap` preview or the text
  block `cuts` now prints — never from a role/fit label or a `Card Text[:N]`
  slice.** **And grade the text against THIS deck's engine, not the card in the
  abstract:** a cost or effect that reads as a downside in isolation is often an
  *upside* in the matching deck — a "sacrifice an artifact / creature" cost is
  cheap and *triggers your payoffs* in a Food/aristocrats deck (Deadly Precision
  in deck 21), "attacks alone" can be a finisher while your other creatures hold
  back to block (Team Avatar), a kicker unlocks a mode the base card hides (Divine
  Resilience → mass indestructible), and a symmetric board wipe is a *reset the
  reanimator rebuilds from* (Villainous Wrath / Rise of Sozin). Ask "what does
  this do *here*" before calling it weak — repeated mis-grades this session traced
  to judging cards in isolation. `--apply` writes with a `.bak` and an INV-04
  re-check; if the add card is already in the deck it bumps that line rather than
  adding a second line for the same card, and it **auto-retires `#~` flex lines
  made stale by the swap** (a line proposing the card you just maindecked, or
  cutting a card you just removed) — replacing the first with an `applied` note.
  `deck.py apply-flex <id> <n>` promotes a `#~` flex line into the 60. Both
  default to a dry run.
- **Triage the roster before full-tuning it.** `deck.py audit` is the cheap,
  offline funnel that answers "which decks actually need a tune" so you don't run
  the expensive `/tune-deck` text-read on all 30+ decks. One line per deck reusing
  the same primitives the single-deck commands do — ownership drift (`check`),
  construction legality (`legal`), color strays (`mana`/`check` castability),
  interaction count and central-theme count (`stats`) — labelled **★ TUNE** (hard:
  illegal / uncastable), **craft** (unbuilt), **review** (soft: off-color strays or
  thin interaction), or **ok**. `--flagged` drops the ok rows. Each deck also
  carries a competitive **`Tier`** (S/A/B/C/D win-capability) read from its `#:
  tier:` header — shown as a column and sortable with `deck.py audit --by-tier`
  (and a color-coded pill on the dashboard). The dashboard opens
  with the same scorecard as a sortable **Roster-triage** table (both render from a
  shared `audit_deck()` scorer, so CLI and page can't drift). It's a SHORTLIST
  SIGNAL like `suggest`/`cuts`: a flag says "look here," then grade the flagged deck
  from `deck.py text` + `/tune-deck` — a review/ok label is not a verdict on the
  deck. (A stale `#: colors:` header inflates the `Cast` column — e.g. the archived
  raw 83-card `19c` pile headed `WU` shows dozens of "uncastable"; fixing the header to
  the deck's real castable colors clears it, same as it does for `mana`/`check`.)
- **Stored decks drift from the real Arena decks.** The user edits decks in the Arena
  app; the repo only updates when someone writes the deck file, so the two silently
  diverge (hit this session: deck `12` had been changed to 2× Super Intelligence / −Futurist
  Forge in Arena while the repo still showed the old list). Catch it with **`deck.py verify
  <id>`** (pipe/paste an Arena export — reports *identical* or a `+/−` diff, printing- and
  basic-fungible) or the dashboard's **"Check for stale decks"** panel (paste one or many
  `Deck` blocks; it auto-matches each to its closest stored deck — variants included — and
  flags the drifted ones). When a drift is confirmed, reconcile the deck file to match Arena
  (a `swap --apply` or a hand-edit) so the repo is the source of truth again.
- **Legality lint and cut candidates are separate from ownership.** `deck.py check`
  answers "do I own this deck"; `deck.py legal <id>` answers "is it a *legal* deck"
  — size vs the format minimum, the copy limit (4, or 1 in singleton formats), and
  each nonbasic's legality in the deck's `#: format:` (from the pool's `Legalities`
  column; `--format` overrides). It exits non-zero on a real violation but treats a
  pool-absent card as *unverified*, not illegal (so WIP/older-print decks aren't
  false-flagged). `deck.py cuts <id>` is the counterpart to `suggest` (adds): it
  ranks nonland cards weakest-fit first (central-theme fit + **impact-weighted**
  functional role + tribal contribution) **and prints the full oracle text of the top
  candidates plus a `⚠ context` flag on deck-dependent mechanics (converge / devotion /
  affinity / X-cost)** — because the role/fit line is a SHORTLIST SIGNAL, NOT A
  GRADE: its classifier can miss what a card does and can't see spice/signature
  cards. (Role credit is now impact-weighted — removal / card advantage / ramp /
  cost-reduction / payoff engines get a bonus via `_role_credit`, so a strong card no
  longer floats to the top of the cut list just for being off-theme; two detection
  bugs that hid Shuri's cost-reduction and Mjölnir's removal are fixed too. The
  residual is inherent: an off-theme power card with **zero** matching themes still
  sorts low in a tuned deck — a synergy model can't see raw power, which is why the
  oracle text is printed and why wishlist ranking pairs fit with a hand-graded Power.) **Read the printed oracle text (and check any `⚠ context` mechanic
  against the deck's actual colors/board), then preview the swap with `swap`
  (which re-shows both cards' full text) before recommending or applying a cut.**
  Repeated cut mis-grades in past sessions traced to trusting the label instead
  of the text — don't. For a holistic add/cut pass, prefer the `/tune-deck`
  skill, which protects signature/spice cards and reserves a fun budget. To
  hard-protect a deck's signature/spice cards, add a **`#: protect: Card A; Card
  B`** header (semicolon-separated — card names contain commas): `cuts` then keeps
  them off the cut list and `swap --cut`-ing one warns. Set these for cards a deck
  is built around so the tooling never proposes cutting them.
- **"Not in library" for a card you own is the deck-dump undercount symptom.**
  `import_arena.py` takes a lower bound per line, so a card can end up
  *undercounted or entirely absent* from `card-library.csv` — then `deck.py
  check` reports it as a craft target even though you own it. Fastest fix:
  `reconcile_crafts.py <arena-export>` — paste the crafted/owned cards as an Arena
  export ("1 Doctor Doom (MSH) 95"), and it adds each to `card-library.csv` (DFC
  stored under its **front** name), adds the matching `card-mana.csv` row, drops it
  from `card-wishlist.csv`, and lists the decks to re-check. Dry-run by default;
  `--apply` writes with `.bak`s; then run `build_gallery.py` + `check_all.py` (or
  `/refresh`). (The DFC front-vs-full name handling — pool/mana key `A // B`, the
  library keys `A` — was the most error-prone part when done by hand.) Alternatives:
  `import_arena.py <deck> --skip-basics` (trues up from a built deck), or append the
  `card-pool.csv` row manually. Hit repeatedly in practice (Primeval Bounty, Cat
  Collector, Inspiration from Beyond, Dion, Atlantis Attacks, the deck 20–22 FDN
  cards, The Everflowing Well, …).
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
  managed environments block it. Enrichment/pool/mana builds require it. All
  Scryfall access now goes through **`scripts/scryfall.py`** (a shared, resilient
  client): a slow/flaky Scryfall — read-timeout, 5xx, or a truncated body, none of
  which are `URLError` subclasses — maps to `ScryfallUnavailable` (transient) and a
  real 404 to `NotFound`, so the **interactive tools degrade instead of crashing**:
  `deck.py mana/stats/wildcards/swap` show `?`/unknown, `build_gallery.py` flags
  missing art and exits non-zero (instead of reporting an imageless gallery as
  success), and `wishlist.py --add` marks rows added name-only-due-to-outage
  distinctly from a genuine no-match. The rebuild scripts (`enrich.py` /
  `build_mana.py` / `build_pool.py`) also fail cleanly on an outage — a clear error
  and a non-zero exit that leaves the existing derived file unchanged, rather than
  crashing or writing a partial-blank file over good data.
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
  `--budget "9M 10R 38U 48C"` turns a wildcard budget into an optimal craft plan
  (top `combined` per rarity cap + alternates + an import block); `--seed-power`
  first-passes BLANK `Power` cells with a heuristic estimate (rarity floor + roles;
  review it — the classifier undersells bombs); `--owned` flags cards you've since
  crafted so you can prune them (or feed them to `reconcile_crafts.py`). `--add`
  now **auto-seeds a heuristic `Power`** on the newly-appended rows (so a fresh card
  never ranks at a 0.0 blank — the Elf engine and the Dino/Enchantress batches each
  sank until graded; review the estimate and hand-adjust the bombs). `--audit-targets`
  flags any card whose **Target deck can no longer cast it** (color/theme drift after
  a retune — e.g. Neriv orphaned when deck 14 went Mardu→Rakdos) or has blank Power;
  it's also folded into `check_all` as a **soft, non-gating warning**. `--rank` shows
  a **`state`** column (target deck's tier·remaining-crafts, ★ = this card helps
  *finish* a near-complete deck) so "upgrade a BUILT deck" reads apart from "build an
  UNBUILT one" — the strategic overlay the raw score can't show.
  `Target`/`Note`/`Power` are hand-annotated: `Target` is a
  deck id / `general` / `concept: …`; **`Power` is a 1–10 hand-graded constructed-
  power score** that `--rank` blends 50/50 with theme fit into a `combined` score
  (an idf theme model can't see raw power, so bombs like Doctor Doom get buried
  without it — the Power column is the fix; the artifact exposes a live fit↔power
  slider). The wishlist CSV itself isn't gated by check_all, but the **ranking
  model is** — `check_rankings.py` (run inside check_all) guards the specific-theme
  cutoff so a scoring change can't silently reclassify a real tribe as "generic".
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
  for 0-wildcard upgrades already owned; `--unowned` lists craft targets. Picks are
  ranked by theme fit **plus the same impact-role credit `cuts` uses** (`_role_credit`),
  so among on-theme options a removal / card-advantage / ramp / cost-reduction / payoff
  card outranks a same-theme vanilla body instead of being buried by tag overlap alone.
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
- **`deck.py suggest-homes <card>` automates the "which of my decks does this new
  card improve" fit pass** (the manual dance repeated every craft this session —
  Doctor Doom, Elspeth, Wan Shi Tong, Shark Shredder). It scans EVERY deck and
  lists the ones where the card is both *castable* (its identity ⊆ the deck's
  declared/derived colors) **and** shares ≥1 *central* theme (same 25%-centrality
  test as `suggest`'s reuse count), ranked by theme-fit, marking where it's
  already maindecked and naming the single weakest nonland cut candidate per deck
  (`#: protect:` cards excluded). It's a SHORTLIST, not a verdict — the cut is one
  heuristic pick, so still grade from full oracle text via `deck.py cuts <id>` and
  preview with `deck.py swap` before applying. Because copies are fungible, it
  reminds you to slot a card into *all* decks that earn it, not pick one home.
- **`deck.py mana` also lints color SOURCES, not just pip demand.** After the pip
  breakdown it prints "Color sources (lands producing each color)" (basics by
  name, nonbasics by color identity — mana dorks aren't counted) and flags cards
  whose strict colored pips look thin against those sources (`△ Pip-intensive`:
  wants CC with <9 sources, or C with <4). This catches the "wants UU but this is
  really a U-splash" problem the castability lint (which only checks identity ⊆
  declared colors) can't see — e.g. a 3-source green splash flagging GG cards. A
  heuristic review signal, not a hard fail; it doesn't gate `check_all.py`.

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
  archived raw 83-card `19c` pile is headed `WU` but is really multicolor. Fixing a stale
  header to the deck's real castable colors clears the false positives (e.g. deck
  `13` was corrected `GR`→`GWBR`). Treat a flag as signal to review, not a hard
  failure — it doesn't gate `check_all.py`.

## Cycle Workflow Config

**Test Command:** `python3 scripts/check_all.py`
(deterministic integrity gate; exits non-zero on any hard invariant break —
INV-01…04 plus a **ranking-model sanity check** (`check_rankings.py`) that guards
the Doctor-Doom-class regression: a scoring change that silently reclassifies a
real tribal theme as "generic". The ranking check is distribution-based, so it
survives cards being crafted off the wishlist. It also emits a **soft, non-gating
warning** for wishlist target drift — a card whose Target deck can no longer cast it
after a retune — via `wishlist.py --audit-targets`; soft warnings never fail the build.)

**Health Dimensions:**
- Data Integrity — CSV structure, no drift between library and derived files
- Enrichment & Tagging Accuracy — Scryfall-sourced fields and synergy tags
- Deck Tooling Correctness — deck.py / query.py / pool.py behavior
- Deck-Building Insight — mana (hybrid-aware), tribes, cost-nature, pool value
- Presentation — gallery correctness and freshness
- Documentation Currency — README / CLAUDE.md match the code and data

**Subsystems:**
- Data: card-library.csv, card-pool.csv, card-mana.csv, card-wishlist.csv
- Ingest & Enrich: scripts/import_arena.py, scripts/enrich.py, scripts/tag_synergies.py, scripts/build_pool.py, scripts/build_mana.py, scripts/reconcile_crafts.py, scripts/sheets_sync.py, scripts/scryfall.py (shared resilient Scryfall client), scripts/lib.py
- Analysis: scripts/deck.py, scripts/query.py, scripts/card.py, scripts/pool.py, scripts/wishlist.py, scripts/validate.py, scripts/check_all.py, scripts/check_rankings.py
- Presentation: scripts/build_gallery.py, gallery.html, image-manifest.json, scripts/build_dashboard.py, dashboard.html, .github/workflows/pages.yml (Pages deploy), scripts/app.py (optional Flask editor), templates/, Makefile (`make app` launcher / `make check`)
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
2. Analyze a deck — `deck.py check|mana|tribes|stats|legal|cuts|text|verify <id>` and roster-wide `deck.py audit` / `deck.py suggest-homes <card>`. Expect: no traceback; mana is hybrid-aware; tribes surfaces type-matters payoffs; legal flags size/copy/format violations; cuts/text print full oracle text; audit scores every deck TUNE/craft/review/ok; verify diffs a pasted Arena export against the stored deck.
3. Refresh derived data — `build_mana.py` → `tag_synergies.py --force` → `build_pool.py` → `build_gallery.py` → `check_all.py`. Expect: check_all reports all invariants hold.
4. Edit via the app — start `scripts/app.py`, change a quantity and Save, add a card, then open a deck (Decks →), change a card's quantity and Save; run `check_all.py`. Expect: CSV + deck file updated, `.bak`s written, and all invariants hold (INV-02 since add appends a card-mana.csv row; INV-04 since deck save re-parses cleanly).

**Frozen Subsystems:** none.

**Deploy Command:** Data + local tooling ship by commit/push (no build/release step). The
one deployed artifact is the **roster dashboard**: `.github/workflows/pages.yml` rebuilds
`build_dashboard.py` offline and publishes it to **GitHub Pages on every push to `main`**
(no manual step). Everything else is read/run locally.

## Command provenance

`broad-scan`, `broad-implement`, `sync-docs`, `health-pulse`, and `roadmap` in
`.claude/commands/` are copied **verbatim** from
[claude-workflow-tools](https://github.com/robinchoudhuryums/claude-workflow-tools);
they stay project-agnostic and read everything from the Cycle Workflow Config
above. To update them, re-copy the files when that repo bumps them — don't edit
them here. `check`, `refresh`, `add-deck`, and `tune-deck` are project-specific.
