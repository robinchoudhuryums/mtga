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
- **BUILD THE OPTIMAL LIST. Do NOT gate a card on whether it is owned, and do not
  budget the build against the wildcards on hand.** Wildcard balances change constantly
  and the owned/unowned data in this repo is often stale, so "you only have 10 rares" is
  a fact about last week, not about the deck. A card that is objectively better belongs in
  the list whether or not you own it. This was a REAL failure mode, not a hypothetical:
  deck 53 was reported as "over budget — 12 rares against 10 held" as though that were a
  design verdict, and cheaper OWNED removal was picked over better unowned removal in all
  three of decks 52/52a/53. **What stays:** report the craft cost as INFORMATION at the
  end (it is useful for sequencing), keep decks WIP/aspirational so `check` tracks the
  gap, and keep flagging ROTATION — a card leaving Standard is a legality fact about the
  deck's future, not a resource constraint, and those are different questions.

## Key Design Decisions

- **`Color(s)` is color IDENTITY, not mana cost.** For anything mana-related
  (castability, hybrids, pip counts) use `card-mana.csv` / `deck.py mana`
  (hybrid-aware). Never infer mana requirements from `Color(s)`.
- **Parse a `Color(s)` cell with `lib.card_colors()`, never inline.** The naive
  `{ch for ch in s.upper() if ch in "WUBRG"}` reads the literal string `"Colorless"`
  as `{R}` (the word contains an R), so a colorless card was mis-routed as red by
  `suggest`/`suggest-homes`/fingerprints; a `.replace(" ", "")` variant kept the `/`
  and broke gold cards (audit F1/F2). `card_colors()` handles both — route every new
  color-parse site through it, and a `--color`-style FILTER through
  `lib.color_matches()` (set semantics both sides): a substring test is the same trap
  as a filter — `"r" in "colorless"`, so `--color R` matched every Colorless card in
  query/pool/wishlist at once (BS-10). `scripts/check_colors.py` (a hard `check_all`
  gate, like `check_rankings`) locks both in: a colorless card must not read as
  colored, a static AST scan fails the build if any script re-implements the naive
  `{x for x in … if x in "WUBRG"}` idiom — the gap that once let the bug regress into
  `wishlist.py`/`app.py` undetected — and a second scan fails any `in` test whose
  container is a raw `Color(s)` cell, the substring shape the first scan could not see.
- **Write canonical files through `lib.atomic_write()` (+ `lib.backup_path()`).**
  Every mutation of `card-library.csv` / `card-mana.csv` / `card-pool.csv` /
  `card-wishlist.csv` goes temp-file → timestamped `.bak` → atomic `os.replace`, so
  an interrupted or empty-result write can't truncate the source of truth (audit
  F3/F5). `.bak` names come from one collision-free, sort-safe helper so "newest"
  is unambiguous (audit F22); readers that need the latest (e.g. `app.py revert`)
  **must use `lib.latest_backup()`, which selects on the CREATION stamp in the name —
  never on mtime.** Backups are made with `shutil.copy2`, which copies the SOURCE's
  mtime, so a `.bak`'s mtime is when its *contents* were written, not when the backup
  was taken; the two orders diverge as soon as anything restores an old file, and a
  revert→save→revert then restored the state the first revert had discarded
  (broad-scan F-04). Pass `backup=False` only when writing a scratch temp the caller
  promotes itself.
- **`card-library.csv` is the owned inventory** and stays compatible with the
  companion Google Sheet (fixed 8-column header). Derived/reference data lives
  in separate files (`card-mana.csv`, `card-pool.csv`) so the CSV isn't polluted.
- **NEVER point a library writer at a derived CSV.** `lib.write_rows` emits exactly
  the canonical 8 LIBRARY columns, so running `tag_synergies.py` or `enrich.py`
  against `card-pool.csv` (both take a `path` argument, and this file used to tell
  you to re-tag the pool that way) silently rewrote it with the library header —
  destroying `Rarity` / `Legalities` / `Released` and breaking every format filter,
  rotation flag and wildcard price, with `check_all` still green because INV-03 only
  checked that the file EXISTED (audit F-02). Both CLIs now refuse a non-library
  target up front via `lib.csv_schema_error()`, `write_rows` raises `lib.WrongSchema`
  as the backstop, and INV-03 verifies each derived file still carries its own
  columns. **The MIRROR is guarded too**: `build_pool.py` / `build_mana.py` /
  `parse_matches.py` refuse an `--out` that already holds a different schema, before any
  network work — `build_pool.py --out card-library.csv` would otherwise overwrite the
  inventory with the pool header, and the shrink guard reads 15.9k-rows-over-2k as
  GROWTH. `query.py --csv` refuses a derived path for the same reason on the READ side.
  **To refresh a derived file, use its own builder** — `build_pool.py --all`
  re-derives pool `Synergies` through the same `tags_for()`; `build_mana.py` rebuilds
  costs/keywords. A new writer for a differently-shaped CSV needs its own
  `atomic_write` + `DictWriter` on that file's real fieldnames (see
  `reconcile_crafts._bak_write`), never `write_rows`.
- **Deck-dump imports undercount quantities** (each line is a lower bound). True
  up owned counts by reconciling from a built deck: `import_arena.py <deck>
  --skip-basics`. **The authoritative fix is `import_collection.py`** — a tracker's
  full-collection CSV IS the truth, so it sets counts EXACTLY, including DOWN, which no
  other tool here can do (`import_arena` takes `max()` by construction and can never
  learn you own fewer). Five tools write owned-card data and they disagree about what a
  quantity MEANS — lower bound vs authoritative — so route through **`/ingest`** rather
  than picking one by hand; choosing wrong either undercounts the collection or
  overwrites it.
- **Basic lands are not in the collection** (unlimited in Arena). `deck.py`
  treats them as unlimited; imports skip them with `--skip-basics`.
- **Owned copies are fungible across printings.** For buildability, `deck.py`
  and `pool.py` both sum a card's `Quantity Owned` across every printing (a card
  owned 1× in two sets counts as 2) — never count a single printing in isolation.
  The pool-facing ownership joins (`pool.py`, `deck.py suggest`) fall back to a
  DFC's **front** face, since the pool keys the full `Front // Back` name but the
  library stores the front only — else an owned DFC would read as `craft` (audit F6).
  Route every such join through `lib.owned_qty` (front-face aware); `check_dfc.py`
  hard-gates this (behavioral anchor + a static scan for raw lookups that bypass it).
  **`card.py` belongs in that list too, and was the violation**: it read `Quantity Owned`
  off the FIRST matching row, so every card owned in two sets under-reported (Rugged
  Highlands showed 1 against a real 3) — on the surface G-01 makes the mandated
  pre-grading read. The gate could not see it: its scan looks for a lookup on an
  ownership INDEX, and this was a per-row column read, which is a different shape.
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

## Competitive Tiering (the rubric)

The `#: tier:` letter drives a lot of downstream judgment (audit sort, dashboard
pills, which decks get tuned, how I weigh a swap), so it must be **defensible, not
vibes**. Grade against this rubric — bands over the *measurable* quality vector
(`deck.py quality` / `deck_quality_vector`: interaction · card-advantage ·
castability · curve · central-theme density), with the intangibles moving a deck
*within* a band.

- **Tier rates the LIST's competitive power, not whether you own it.** Build-state
  is tracked separately (`check`/`audit`); an aspirational unbuilt list is graded
  on its merits **provided it's legal and a real 60** (that's a purpose of variant
  decks — a fully-owned playable version plus an aspirational variant, each tiered
  on its own list; an incomplete/illegal pile isn't gradeable). **Never auto-write a
  tier letter** — it's a human competitive judgment (design constraint).
- **The measurable FLOOR** (`deck.py tier <id>` → "metrics floor", via
  `tier_band`): interaction + card-advantage = the resilience axis. Roughly:
  **A-floor** interaction ≥5 and (interaction+card-adv) ≥7; **B-floor** interaction
  ≥3 and sum ≥4; **C-floor** sum ≥2; **D** below that; any uncastable stray caps at
  C. The floor is blind to raw card power / bombs / meta (an idf+role model can't
  see those), so it **under-rates by design.** An uncastable stray CAPS the floor at C
  rather than SETTING it, so a dead card can no longer RAISE a D-floor deck, and a card
  the deck's `#: uncastable-ok:` header declares intentional is not counted at all.
- **The floor is ARCHETYPE-aware** (#4): an aggro deck closes on a fast clock, not an
  interaction suite, so for an **aggro** plan a bounded `_clock_score` (low curve +
  cheap threats + reach, 0–7) SUBSTITUTES for the interaction the resilience floor
  demands — a fast burn deck isn't floored at C for light removal. Every other plan
  (midrange / control / combo) keeps the exact interaction+card-advantage floor
  (clock 0), so nothing else regrades. The plan comes from an explicit **`#: plan:
  aggro|control|combo|midrange`** header, else keywords in `#: archetype:`, else a
  strict metric inference (default midrange). `deck.py tier` prints the plan + clock.
  **`#: plan:` IS A GRADING INPUT, NOT A LABEL, so a wrong one silently BUYS a band.**
  Deck 56a carried `aggro` while its own `#: archetype:` prose called it "slower, bigger,
  board-independent"; the aggro path substituted a clock score (4/7) for the interaction
  it lacked and floated the floor to A. Corrected to `midrange` 2026-08-09 the floor read
  B and the letter followed it down. Nothing flags this — the guard compares the letter
  to the floor, and the floor is what the wrong plan moved. **When the plan header and
  the archetype prose disagree, the prose is usually the honest one**; check them against
  each other whenever a deck's letter looks generous, and re-check after a pivot, since
  a draft-time change of plan does not rewrite the header.
- **The bands (what the letter means):**
  - **S** — measurably A-floor AND a human call that it's top-meta capable: real
    bombs, a protection/interaction suite, proven to close fast. Rare.
  - **A** — A-floor (strong interaction + card advantage), coherent engine, tight
    curve, at most one clear weakness.
  - **B** — B-floor (moderate interaction) OR a single real gap (e.g. thin card
    advantage / reach), coherent but capped.
  - **C** — a hard cap: near-zero interaction, heavy singleton variance, or thin
    themes / castability strays.
  - **D** — incoherent, illegal, or no theme spine.
  A human letter **one band above the floor is fine** — that band credits the
  intangibles the metrics can't see. **Two-or-more bands above is indefensible or
  stale**, and that's the only thing the guard flags.
- **The guard** — `deck.py tier <id>` shows claimed-vs-floor and flags a mismatch
  (≥2 bands over) or a possibly-under-graded deck (claimed *below* the under-rating
  floor) — **unless the `#: tier:` prose argues for grading under it**, which the rubric
  permits and which three decks were being nagged about. A roster pass is a **soft, non-gating** `check_all` warning, so an
  inflated/stale letter can't hide. It never assigns — it says "re-grade this, or
  justify the bombs/meta in the `#: tier:` rationale." **Run it after any deck edit**
  (the `/apply-changes` skill does) so a tune that moves the metrics re-grounds the
  letter. The floor makes the *floor* bulletproof; S-vs-A still needs your judgment.
- **Climbing a tier** — `deck.py tier <id> --to A` prints the exact measurable gap
  to a target band's floor ("+3 interaction"), then the owned (0-wildcard) on-color
  cards **and** the unowned craft targets that fill the short axis, so it doubles as
  a wildcard-spend planner. `/tune-deck` runs it so a tune aims at a concrete tier
  target. The tool does the arithmetic; the card *selection* stays a human call
  (protect signature/spice). Compare a deck's past versions with `deck.py history
  <id>` (its git changelog) + `deck.py quality <id> --at <ref>` (re-scores a past
  list's vector against now) — change history lives in git, not an in-file log.

## Common Gotchas

Each rule below carries an anchor like `[G-nn]`. **The reasoning, the measurements and
the incident that produced it live in `docs/gotchas.md` under that anchor** — nothing was
deleted in the split, and the history is why these rules are trusted. Read the long form
before you decide a rule looks arbitrary and simplify it away, or when you are working
directly on the subsystem it governs. `scripts/check_docs.py` gates the link in both
directions.

- **Inspect one card with `card.py <name>`, never a truncated slice.** It prints the
  complete oracle text plus mana cost, **format legality**, owned quantity and which
  decks run it. Run it before grading or recommending ANY card in chat — "it's in the
  pool" is NOT "it's Standard-legal". **In code, never slice a card's text to grade,
  classify or rank it**; `load_card_data()` is the ONE name→card accessor, and it
  resolves library-first, so a library row with BLANK text would shadow a populated pool
  row. **Its key convention differs from every CSV reader here and fails SILENTLY:
  keys are LOWERCASED and the oracle field is `text`, not `Card Text`.** A sweep written
  as `load_card_data().get(name)["Card Text"]` matches nothing and returns a clean zero
  for every deck — which reads as a finding, not a bug. Cost a wrong "0 scry/surveil
  sources" answer for three decks in one pass. [G-01]
- **A split / Room / Adventure card's stored cost covers BOTH halves — read the FRONT
  face.** Use `lib.front_face_cost()` / `lib.mana_value()`; `parse_pips` and `load_mana`
  already do. A **MODAL DFC** is stored the same way now — either face is castable from
  hand — but its Mana Value is the FRONT face's, so it escapes residual 2 below; a
  TRANSFORM DFC keeps one cost, since its back is reached by transforming, not by paying.
  **Residual 1: a deck that plays a split card mainly for its BACK half reads
  cheaper than it plays — grade that one from the printed card. Residual 2, and it is on
  the surface you are told to trust: `card.py` prints the COMBINED mana value**, so a Room
  reads far MORE expensive than it plays — Mirror Room // Fractured Realm displays MV 10
  when it is a `{2}{U}` three-drop whose back door unlocks separately for `{5}{U}{U}`, and
  you never pay ten. Every analysis path (`stats`, `consistency`, the curve) already uses
  the front face, so the inspection surface and the analysis surface disagree. Read the
  printed cost, not the MV, whenever a name contains `" // "`. [G-02]
- **Don't judge a card by printed mana value or a single subtype.** Read the card TEXT
  (it is in the CSV): `stats` flags ◊/△ cost flexibility and functional roles, `tribes`
  reads oracle text for cross-type synergies. [G-03]
- **A `#~` flex line rots SILENTLY.** `swap --apply` retires only the lines its own swap
  invalidates and `--audit-rationale` never reads the flex block, so a line can sit for
  rounds proposing a cut that already happened. `deck.py flex <id>` and a soft
  `check_all` warning surface it; sometimes the fix is to RETIRE the line, not retarget
  it. Advisory — a flex line is a human note, so nothing edits one. [G-04]
- **A swap inherits the cut card's `# section` comment**, so the file then lies to the
  next reader. `swap --apply` warns via `section_mismatch`, on UNAMBIGUOUS headers only.
  Advisory: moving the line is a human editorial call. [G-05]
- **Preview every swap with `deck.py swap <id> --cut A --add B`** — it prints the FULL
  oracle text of BOTH cards plus the deltas. **Always grade a cut from that text, never
  from a role or fit label, and grade it against THIS deck's engine**: a cost that reads
  as a drawback in isolation is often an upside in the matching deck (a sacrifice cost
  feeds your payoffs, a kicker unlocks a hidden mode, a symmetric wipe is a reset your
  reanimator rebuilds from). `--apply` writes a `.bak`, re-checks INV-04, bumps an
  existing line rather than duplicating it, and auto-retires flex lines the swap made
  stale. [G-06]
- **Triage the roster with `deck.py audit` before full-tuning it** — the cheap, offline
  funnel for "which decks actually need a tune", labelled ★ TUNE / craft / review / ok
  and sortable by `Tier`. It is a SHORTLIST SIGNAL: a flag says "look here", and a
  review/ok label is not a verdict on the deck. `review` counts only an off-color
  ABILITY, never a hybrid you pay on-color — counting every identity stray had saturated
  the flag to a measured 0% actionable rate. A stale `#: colors:` header inflates the
  `Cast` column. [G-07]
- **Stored decks drift from the real Arena decks** — the repo only updates when someone
  writes the file. `deck.py verify <id>` diffs a pasted export; **`deck.py sync` is the
  WRITE half**, matching one or many `Deck` blocks to their closest stored decks and
  rewriting the drifted ones. Dry-run by default; a block matching two variants nearly
  equally is reported LOW CONFIDENCE and skipped, and a paste under 75% of the stored
  deck's total is flagged **TRUNCATED** and skipped too — a partial paste is a strict
  SUBSET, so the shared-card floor alone read it as a full-confidence match and
  `--apply` would have rewritten the 60 down to the fragment (`--force` overrides,
  for a deliberate cut). [G-08]
- **`check` answers "do I own this deck"; `legal <id>` answers "is it a LEGAL deck"** —
  size, copy limit and each nonbasic's legality in the deck's `#: format:`, format-aware
  for Alchemy and Brawl (a Brawl deck also validates `#: commander:` and every card's
  colour identity). A pool-absent card is *unverified*, not illegal. `deck.py brawl` is
  the roster-wide counterpart. **`deck.py cuts <id>` ranks weakest-fit cards and is a
  SHORTLIST, not a GRADE** — it cannot see raw power or spice, and on a creature-heavy
  deck it is a coin flip (50% vs 86% noncreature, replicated at n=31 and n=103). **Two
  fixes were pre-registered and REFUTED**: body quality (2026-07) and tag-count
  normalization (2026-08 — it lifts creatures 53→68% and COLLAPSES noncreature 83→51%,
  so the unnormalized sum is load-bearing). Don't derive a third from the tag-count
  asymmetry. Read the oracle text, preview with `swap`, and hard-protect signature cards
  with a `#: protect:` header — whose keep-boost reads the STRICT spine (≥2 protected
  cards share the theme), like every `fit_strength` caller. `cuts` also prints the axis
  the deck is SHORT on, and flags `⌁scales w/ <axis>` for a card graded at its FLOOR.
  Both REPORT-only. [G-09]
- **"Not in library" for a card you own is the deck-dump undercount symptom.** Fastest
  fix: `reconcile_crafts.py <arena-export>` — it adds the library row, adds a blank
  `card-mana.csv` row so INV-02 always holds, drops the card from the wishlist, and
  stores a DFC under its FRONT name. Dry-run by default. **NEVER USE A CRAFT COST AS A
  REASON IN A CARD-QUALITY ARGUMENT.** Four counts were wrong in ONE 2026-08-09 session
  (Cosmogrand 1→2, Halana 1→2, Ruby absent→2, Castle Doom 2→3), each found only because
  the user noticed, and one of them ("the 3rd Castle Doom is a pending rare craft") had
  been load-bearing in a swap recommendation — the advice survived re-testing on merits,
  but it need not have. Report craft cost as INFORMATION at the end, per the Player
  Profile; when a decision leans on ownership, say so, because that is the premise most
  likely to be false. `import_collection.py` against a tracker export is the only tool
  that sets counts EXACTLY (including down) — run it before a wildcard-spending pass. [G-10]
- **MTG Arena set codes can differ from Scryfall** (`DAR` = `DOM`). `enrich.py` maps the
  known ones in `SET_ALIASES` and leaves Collector # blank rather than writing one from
  an unconfirmed printing. [G-11]
- **WIP decks legitimately show "missing" cards** in `check_all.py` — craft targets not
  yet owned. Not a failure. [G-12]
- **Regenerate derived data with `make refresh` — never by hand.** The order is a real
  dependency graph and the Makefile is the ONE executable definition; it had been written
  out in eleven places, of which only one was right. Use `--merge`, never `--force`
  (which clobbers hand-curated tags). Getting it wrong is QUIET — a new set's pool cards
  rank with no cost and no keyword tags, and no invariant notices.
  `tests/test_verify_ingest.py` fails the build on a new prose copy of the recipe. [G-13]
- **All Scryfall access goes through `scripts/scryfall.py`**, a shared resilient client:
  an outage maps to `ScryfallUnavailable` so the interactive tools DEGRADE instead of
  crashing, and the rebuild scripts fail cleanly rather than writing a partial-blank file
  over good data. A new call that bypasses it will hit the same class of bug — a read
  TIMEOUT is not a `URLError`, `http.client.IncompleteRead` is not a `JSONDecodeError`,
  and `ssl.SSLError` subclasses `OSError` rather than `ConnectionError` (all three now in
  `_TRANSIENT`; the last two were escaping as tracebacks). Needs `api.scryfall.com` +
  `*.scryfall.io` reachable.
  [G-14]
- **The optional editor (`scripts/app.py`) mutates `card-library.csv`** via validated
  writes plus a timestamped `.bak`, appends a `card-mana.csv` row when you add a card
  (INV-02), and edits deck files gated on INV-04. Run `/refresh` after an app session so
  derived data catches up. [G-15]
- **`card-pool.csv` carries printed `Power`/`Toughness` — parse them with
  `lib.card_power()`**, which returns `None` for the `*`/`X` printings instead of
  inventing a number; note `card_power(0)` is a real 0, so the helper can't use `or`.
  `deck.py stats` flags a "power N+" payoff few of the deck's creatures meet, **scoped by
  `_POWER_SCOPE_MINE_RE` to clauses about creatures YOU control**: removal measures the
  opponent's board and "TOTAL power N" is a SUM, and counting your own bodies was wrong
  in 16 of 27 roster flags. The flag reads the gating trigger's TIMING from its own
  ability line (fixed 2026-08-09): an ENTERS gate keeps the "a body that GROWS after it
  enters won't satisfy it" caveat, while an ATTACK-time gate (Scalestorm Summoner, Ruby —
  "whenever this creature attacks … if/while you control") says the printed count is a
  FLOOR, since pumped bodies DO satisfy those. The one-size ENTERS caveat had been copied
  into a `#: tier:` block as a fabricated weakness and retracted the same day. Printed
  stats still under-state any gate a growing deck loosens — read the timing. [G-16]
- **`card-wishlist.csv` records Power PROVENANCE** in a `Power Source` column
  (`seed` / `hand` / `unknown`). `wishlist.power_is_seeded()` treats seed, unknown and
  blank as untrusted; set `hand` when you grade one. [G-17]
- **`build_pool.py --all` and `build_mana.py --pool` are the FULL-coverage scopes.** Both
  DEFAULT to something smaller, so a plain rebuild silently shrinks coverage back; both
  now refuse a >50% shrink (`--allow-shrink` to force). `build_mana.py` is also
  INCREMENTAL — it reuses already-resolved rows and re-fetches only new or unresolved
  names, and `build_pool.py` REUSES a pool built within the last week for the same query
  (99% of the old refresh cost was its 91 paginated pages). Skipping the pool is correct,
  not just fast: it is the whole Arena pool and independent of what you OWN, so an ingest
  cannot change it — what goes stale is `Legalities` and a new set's arrival, hence a
  window. **But a TAG-PATTERN edit also stales it**, which the reuse could not see: the
  stamp records a content hash of `tag_synergies.py` and a mismatch defeats the reuse
  (BS2-23). An ABSENT hash means UNKNOWN and rebuilds ONCE — the reuse path returns
  before writing a stamp, so "unknown = reuse" meant the hatch could never arm (BS3-02).
  `--refetch` (`make refresh REFETCH=1`) forces both. [G-18]
- **`card-wishlist.csv` is UNOWNED craft targets**, with DFCs under their full
  `Front // Back` name. `--rank` blends a hand-graded Power 50/50 with theme fit plus a
  bounded cross-deck breadth bonus; **lands rank on manabase value instead**, since theme
  fit would sink them. `--budget` turns a wildcard budget into a craft plan and must show
  every check `--rank` runs — it once dropped the rotation flag and planned two rotating
  cards into a 3-slot budget. The filter flags apply to `--rank`/`--budget`/`--by-set`,
  and a filtered view is normalized against the WHOLE wishlist. `pow~` marks a
  CONDITIONAL power a rarity+role seed structurally cannot price. **The Power scale is
  0–10 and range-ENFORCED at rank time**: a finite out-of-range cell flags `pow!` and
  scores 0 — 15 live cells carried 0–100-style grades ('84', '78'…) and were silently
  LEADING `--rank`/`--budget` until the flag landed (batch 6). [G-19]
- **Auto-targeting a wishlist batch: trust STRONG, judge `review`.**
  `wishlist.py --suggest-targets` scores fit by theme rarity (idf) so broad decks stop
  acting as catch-alls — only a *specific* theme is a confident match. Workflow: `--add`
  → `--suggest-targets --write` → text-review the `review` cards, which the tag heuristic
  genuinely cannot place. [G-20]
- **`card-pool.csv` carries a `Legalities` column**, so `deck.py suggest` filters craft
  picks to the deck's `#: format:` by default (`--format` overrides, `--any-format`
  disables). A pool built before the column lacks it — `suggest` warns and shows all
  until you rebuild. [G-21]
- **`deck.py suggest` scopes by CASTABLE COLORS, not identity**, so an off-color
  activated ability doesn't surface uncastable picks. Run it both ways every time:
  `--owned --limit 0` for 0-wildcard upgrades you already own, `--unowned` for craft
  targets. Picks are ranked by theme fit plus impact-role credit, with three BOUNDED
  modifiers — saturation-discounted role credit, a curve factor, and a power co-signal
  that only re-ranks WITHIN the on-theme set. [G-22]
- **`deck.py engines <id>` grades a deck's two-sided ENGINES** (enabler ↔ payoff): a
  synergy tag says "sacrifice" is present, not which cards FEED the engine and which PAY
  IT OFF. The ⚠ fires only off the trustworthy PAYOFF side, since enabler cues are broad.
  A shortlist that prints the card lists — read them. [G-23]
- **`deck.py stats` prints an INTERACTION PROFILE** — the raw count treats all removal
  alike, so it splits by SPEED and by whether anything answers a NONCREATURE permanent,
  flagging "all sorcery-speed" or "no noncreature answer". [G-24]
- **`stats` / `tier` measure a PROTECTION axis** — "can this deck protect the permanent
  it wins with?" Narrower than the "Protection / trick" role on purpose (a combat pump is
  not an answer to removal), and `regenerate` is excluded because "can't be regenerated"
  is boilerplate on removal. A ZERO is flagged in both views. It is REPORTED, never fed
  into `tier_band` — a new term there would silently re-grade the roster. [G-25]
- **`tier --audit-rationale`'s SUPPRESSION RULES are the delicate part** — a citation is
  often legitimately not a claim about the current list. Keep the cue lists NARROW and
  **let a roster-wide sweep be the check**: a false positive is noisy and gets noticed, a
  false negative is silent, and three separate sweeps each found figures the audit had
  reported clean. A CARD citation and a FIGURE go stale differently and must not share a
  predicate — and the CARD path kept a broad `remov\w*` for a year after the FIGURE path
  was narrowed for exactly that word, so a card whose own text says "removes" suppressed
  its own staleness report. The 2026-08-09 rework (five live misses in one day, each now
  a fixture in `test_deck.py`) clause-scoped both cue families — cross-sentence
  suppression, a cue inside the card's OWN name ("Crib **Swap**"), possessives, short
  comma-heads and cross-deck figures are all fixed, and its first roster sweep found six
  real stale rationales a clean-reporting scan had been passing. **STILL LIVE:** a copula
  hides a figure ("protection is 1"); "the swap removes X" about a CUT card reads as
  live; a fragment shared by 4+ cards drops as an epithet; a card absent from the POOL
  is invisible entirely (the scan matches known names only). [G-26]
- **Run `tier <id> --audit-rationale` after ANY deck edit.** The tier guard checks the
  LETTER; this checks the ARGUMENT — cards the prose cites that the deck no longer runs,
  and figures the live quality vector contradicts. A swap moves those numbers by
  construction. Scoped to `#: tier:` AND `#: archetype:` — the archetype block is equally a
  claim about the CURRENT list, and it is the header a reader trusts first, so it is the
  one that goes stale unnoticed. `#: notes:` stays out of the STALENESS scan — a build log
  may name an absent card — but an EXCLUSION claim in it ("deliberately NOT included: X")
  is checked, because that is a claim about the current list in the opposite direction.
  Report-only. A rationale that legitimately names a card it cut must put the change-cue
  ADJACENT to the name — adjacent means the SAME clause; "X came out for Y" split across
  a wrapped `#:` line still read stale, "X was CUT for Y" passed. **Residual: the
  EXCLUSION check has a proximity window and misses a name several lines into a wrapped
  list** — deck 52 named Zemo under "Deliberately NOT included" while running him, and
  `wrong_exclusion_claims` returned empty. [G-27]
- **`suggest`'s `Decks` column is cross-deck BREADTH, not curated fit** — castable and
  sharing a *central* theme that is also SPECIFIC, with variants collapsed to their core
  deck. Both gates are load-bearing: centrality alone left the column saturated at 99%,
  i.e. carrying no information. Read it as rough "value per wildcard". [G-28]
- **Flex-block craftables are format-scoped** — when a deck's `#: format:` changes,
  re-check its `#~` craft suggestions, because a craftable legal under the old format may
  have rotated. [G-29]
- **The pool's `Legalities` is a build-time SNAPSHOT — Standard rotates.** `suggest`
  marks an aging pick `⚠rot` from the `Released` date, `deck.py rotation` is the
  roster-wide view, and `wishlist --rank` flags a craft target rotating this year or
  next. Since 2026-08 the CRAFT views carry the same flag: `deck.py check` marks each
  missing/short card `⚠rot~YEAR` inline, and `wildcards` (incl. `--dedup`, the
  cross-deck union ranked by decks-served per copy) flags its leverage list — deck 28's
  plan bought four rotating cards past unflagged views, and deck 49 held five more.
  `rotation_risk` is calendar-YEAR based, since rotation happens annually.
  **Reprint caveat, partly encoded:** the pool keys ONE printing, so a card reprinted
  into a long-legality set inherited the wrong date — `_SET_ROTATION_OVERRIDE` fixes the
  announced ones, and the residual is real: verify against the official schedule. [G-30]
- **`deck.py suggest-homes <card>` is the cross-deck fit pass** — every deck where the
  card is castable, format-legal and shares a *central* theme, labelled KEY /
  role-player / tangential, strongest first, with the card's oracle text and a cut hint
  from the same ranking `cuts` prints. Trust KEY, judge role-player, read tangential as
  "probably not for this deck". Overlays it applies that theme overlap cannot see: a
  rainbow FIXER is promoted by the deck's colour count, a DOUBLER by the deck's magnitude
  on its axis, and cost-shaped themes (graveyard/mill/discard) count only when the deck
  fields payoffs — filling your graveyard is value in a reanimator deck and damage in a
  control deck. It is a SHORTLIST: grade from full text, preview with `swap`.
  **TWO RESIDUALS, both measured on one card (2026-08-07).** A ZERO-ROW result is a THEME
  miss, not a colour-identity fact — reporting the second produced a written "you have no
  Abzan deck" claim against FOUR WBG decks. And KEY scores THEME OVERLAP ALONE, so for a
  structurally-valued card it says little: Chandra rated KEY in 14 of 42 decks, nearly all
  on the generic red trio, while the counts that decided placement were unseen. [G-31]
- **`suggest-homes` reads castability as an identity SUBSET, which says nothing about
  whether you can pay the PIPS.** A `{W}{W}{W}{W}{W}` card was rated KEY for decks with
  10–11 white sources, roughly a 1% chance on turn five. `pip_depth_warning` prints
  `⚠⚠ 5x{W} vs 10 sources` from the same hypergeometric model `consistency` uses. It is a
  FLAG, never a score change. [G-32]
- **A DOUBLER is worth what it doubles, so `doubler_support` counts the deck's feeders**
  on that axis (tokens / counters / triggers / lifegain), bounded and promoting to KEY
  only at real density. `doubler_restriction` reads the doubler's OWN scope so a
  restricted one isn't counted against the whole deck. **KNOWN GAP: it parses a POWER
  scope and nothing else**, so a TYPE-scoped doubler (Splinter's Ninja clause) is counted
  against the whole deck — 27 feeders in deck 20 against a correct 12. Read a
  `✱ multiplier` figure on a tribal doubler as an upper bound until that is fixed. [G-33]
- **Before committing a deck edit run `deck.py preflight <id>`, and grade a cut/swap with
  `deck.py quality`.** `preflight` folds legal + owned + castable + a full `check_all`
  into one READY/BLOCKED verdict. `quality --json` before, `--vs FILE` after, flags
  regressions so a swap that worsens the deck self-catches — a SOFT guard, since an
  intentional trade is fine. [G-34]
- **`deck.py mana` also lints color SOURCES, not just pip demand** — it flags cards whose
  strict pips look thin against the deck's actual sources (`△ Pip-intensive`), catching
  the "wants UU but this is really a U-splash" problem the identity-subset castability
  check cannot see. A review signal; it doesn't gate `check_all`. [G-35]
- **`deck.py consistency <id>` is the PROBABILITY layer `mana` lacks** — keepable %,
  screw/flood, land-drop consistency and per-card P(cast on curve), with a Karsten-style
  source recommendation. Run it whenever a splash, a double pip or a top-end bomb is in
  question; it is what settles "is this actually castable" instead of hand-waving from a
  source count. A thin (≤3-source) splash is reframed "cast late or cut" rather than
  printing an impractical land count. The land-count advisory checks the neighbour before
  prescribing a direction: on a low curve BOTH directions used to trip ("consider fewer"
  at 24 lands, "consider more" at 23, where keepable was worse), so when neither helps it
  now says the threshold is unreachable and points at cast-on-curve — which is the number
  that settles the question anyway. A planning aid, not a guarantee. [G-36]
- **`deck.py suggest --lands <id>` is the manabase RECOMMENDER** — plain `suggest` is
  structurally blind to lands, because it filters to cards sharing a synergy theme.
  Scored on FIXING value plus two bounded nudges (a land's own synergy text, and the
  deck's scarcest colour). It defaults to the deck's own `#: format:`, as the card-facing
  `suggest` always did — it once offered two non-Standard duals as craft targets, and on
  a wildcard-spend recommender an unfiltered pick costs real resources. **LIVE RESIDUAL,
  at the TOP of the list: three of its four highest-scored picks for deck 52 were NOT
  PLAYABLE LANDS** — a land on the BACK face, a spell on the front, so it is reached by
  transforming and never by a land drop. Maindeck one and the deck is a land short with
  INV-04 seeing nothing wrong. Same class as G-63. Two scoring misses ride along: a
  "spend this mana only to cast a creature spell" land scored top, and a
  conditionally-tapped land scored as sometimes-untapped on a condition mono-black cannot
  meet. **Read the type line of every pick before crafting.** [G-37]
- **`suggest --ramp / --interaction / --needs` are the NEEDS model** — the structural
  axes theme-`suggest` is blind to (fixing, acceleration, interaction). **If the scorecard
  says the deficit is interaction or mana, the fix comes from here, not from plain
  `suggest`.** Never weaken the gated theme filter to surface them; add a parallel path.
  Board-dependent removal is FLAGGED `⚠ scales w/ <axis>` rather than silently boosted —
  the honest stance for a fuzzy signal. Their castability filter reads the PRINTED COST
  via `_candidate_castability`, same as `suggest` proper — they were the two siblings the
  G-58 fix missed, hiding 34 castable interaction cards and 25 mana sources from
  mono-color decks on exactly the paths this rule routes deficits to (BS-01). [G-38]
- **`cuts` folds a card-QUALITY (power) co-signal**, so an on-theme-but-weak card sorts
  UP the cut list and an on-theme bomb is protected. Bounded and neutral-centred, so it
  only breaks near-ties; a `Pw` column shows it. Still grade from the oracle text, not
  the number. [G-39]
- **`cuts` folds a MULTIPLIER co-signal (`✱`), and the bug it fixed was a CALLER, not a
  model.** A doubler's worth lives in the rest of the deck, and both halves of the cut
  score are blind to that — so Delney, which doubles the trigger of every small creature
  in deck 46's engine layer, ranked as that deck's WEAKEST card while `suggest-homes`
  scored it correctly off the same primitive. Routed through those same primitives so the
  two cannot disagree; bounded, zero below a feeder floor, and it only ever RAISES a
  keep-score. **A pure-function anchor cannot see whether a caller asks — that is the
  recurring failure shape here.** [G-40]
- **`cuts` flags COST-AS-UPSIDE (`⚡`)** — a cost that is a benefit in THIS deck (a
  landfall kicker returning a land, Warp in a counters deck, a sacrifice feeding an
  outlet, a discard filling a reanimator's yard). Every model grades a card in isolation,
  where an additional cost reads as a drawback. A FLAG for a human read, never a score
  change. [G-41]
- **The MIRROR of cost-as-upside has no flag: a fine card that fights your own engine.**
  Graveyard hate in a graveyard deck, hand attack against a deck you want holding cards.
  Two such cards shipped into finished decks. **When a deck DEPENDS on a zone being
  populated, audit every card that empties it** — grading a card in isolation cannot see
  this. **Same shape one resource over: BLINK ERASES +1/+1 COUNTERS** (the creature
  returns as a new object), so a flicker package in a counters deck resets the
  investment it is meant to protect — the question was asked of deck 63 and the answer
  came from measuring ETB density (7 of 35 nonland cards) against the erasure, not from
  the cards' own text. Before adding blink, count what the blink would DISCARD. [G-42]
- **Grade a modal / split / adventure card by the FACE YOU CAST, not the half you want.**
  Decadent Dragon was drafted for its `{2}{B}` adventure half and cut once `consistency`
  priced its `{2}{R}{R}` FRONT face at 53% on turn four. [G-43]
- **`cuts` folds an ability-DISTINCTIVENESS co-signal (`Uq`)** — the card-level analog of
  the deck-idf theme model, so a generic-ability filler sorts UP the cut list and a
  distinctive card is mildly protected. It takes the MAX of tag-rarity and a
  structural-TEXT signal, so the text half can only ever RESCUE a mis-tagged card, never
  inflate a genuinely generic one. **Residual: a distinctive card with neither a rare tag
  nor an unusual text shape still reads generic — `Uq` is a shortlist signal, not a
  verdict.** [G-44]
- **`deck.py tier <id> --to <TIER>` assembles a concrete CUT→ADD tune package** — the
  measurable gap, the owned (0-wildcard) and craft fillers that close it, each paired
  with a weakest-fit cut from the SAME ranking `cuts` prints, and a projection of the
  resulting floor. It flags a cut that itself feeds interaction/card-advantage or is a
  mana source. It PRINTS, never writes: card selection stays a human call. **Both filler
  halves apply the deck's format filter** — the owned half once skipped the check its
  craft sibling applied and offered non-Standard cards; when two functions answer the
  same question for owned vs unowned, diff their filters. [G-45]
- **`deck.py redundancy <id>` plans consistency the "virtual copies first" way** —
  distinct, similar-but-different cards that do the same job, keeping the singleton feel,
  with true 4-of duplicates only as a fallback when nothing of comparable quality exists.
  This is why a functionally-dense singleton can defensibly grade A: the tier floor counts
  EFFECTS, not distinct cards. [G-46]
- **Building a deck FROM SCRATCH has four helpers**: `deck.py similar <id>` (is it
  distinct or a near-duplicate — read the ✦ SPECIFIC overlaps, not the number),
  `deck.py resolve <names…>` (names → valid deck lines, reporting ambiguity instead of
  guessing), `pool.py --role` (survey owned cards by what they DO), and
  **`deck.py screen <id> <names…>`** — re-score a candidate pile against the deck AS IT
  IS NOW. **Re-run `screen` after ANY change of plan, not once**: a pile graded against
  the first draft's plan keeps those verdicts, which is how four cards were excluded for
  reasons that had expired. Its `★ STRICT UPGRADE` test is deliberately conservative, so
  its silence is not a verdict — and when KEY fires on ≥40% of a pile `screen` SAYS SO:
  measured at 45–51% on the two mono-black decks, where the signature theme sits on half
  the colour's pool. Read the ORDER, not the word. `similar` likewise prints `▸ Most
  shared CARDS` when its theme ranking disagrees with actual card overlap — deck 52a
  reads 96% against deck 6 (4 shared cards) and 81% against its own parent (14). Theme
  similarity and card overlap are different questions, and SOME OVERLAP IS FINE. [G-47]
- **Every role COUNT carries its own uncertainty** (`deck.count_conf`), because a
  heuristic classifier reports a false negative as a FACT. `stats`/`tier` render `7`,
  `3 +2?`, or `8 +4? (3 unclassified)`. The remainders are QUANTITY-WEIGHTED like the
  counts they annotate. The bare ints still feed `tier_band`; the annotated string is
  what a human reads. [G-48]
- **`deck.py shape <id>` answers WIDE vs TALL** — the structural question themes
  structurally cannot, since `counters` is the same tag whether they all go on one
  creature or spread across twelve. Reading `#: archetype:` prose instead produced the
  worst misread of the cycle; the header is the older claim, and the measurement wins.
  [G-49]
- **`deck.py resolve --format` warns on cards not legal in the format.** Resolving a
  printing is not a legality check, and that gap let a supplemental card reach a finished
  60-card deck file. [G-50]
- **`deck.py redundancy` also lists INTERCHANGEABLE cards** — groups of nonland cards
  with identical role sets inside a 1-mana band. Reported as GROUPS, not pairs, and cards
  with NO detected role are never grouped: no signal beats a guess. [G-51]
- **A VERDICT surface must print its evidence.** `cuts` and `swap` print full oracle text
  and produced the fewest bad calls; `suggest-homes` handed out KEY/role-player labels
  with no text at all, which is how a card was rated KEY for a deck whose engine it mills
  away. Keep it that way. [G-52]
- **A CAPABILITY THAT WORKS AND IS NEVER REACHED is invisible to every correctness
  gate.** Every gate verifies a model is right; none can see a command nothing runs.
  `check_commands.py` closes it — every subcommand and script must be invoked by a skill,
  called by another module, or exempted WITH A REASON, and a stale exemption is itself a
  failure. Coverage requires a REAL call, not a prose mention — on BOTH paths: the
  script half accepted any filename mention until 2026-08 (two of `build_pool.py`'s three
  were warnings NOT to run it), and now wants `python3 scripts/<fn>` in a skill or
  `scripts/<fn>` in the Makefile. [G-53]
- **A SET plus a sort key that can TIE is a nondeterministic output.** Tied themes left
  in set-iteration order made an unchanged build produce different output every run.
  **Before sorting anything derived from a set, ask what happens when the key ties** —
  make the key a total order. [G-54]
- **NO GATE BUILT AN ARGPARSE TREE, so a broken `--help` was invisible** for four days
  with three green workflows. `check_all` imports `deck` as a MODULE and calls `cmd_*`
  directly, so the CLI surface is covered separately by `tests/test_cli.py` and a CI
  smoke step. Note argparse renders help through `help % params`, so **a bare `%` in a
  help string raises — write `%%`** — and the top-level help expands every subaction, so
  one bad string takes the whole `--help` down. [G-55]
- **`swap --apply` records the decision to `recommendations.csv`** — where `cuts` ranked
  the card you cut and whether `suggest` surfaced the add, captured against the PRE-swap
  deck. `deck.py feedback` reads it back and **leads with the DISAGREEMENTS**, because an
  agreement is contaminated by the shortlist's own influence. It is REPORT-ONLY and must
  stay so: `tests/test_recommendations.py` structurally forbids a scoring function
  reading the ledger — including `cut_keep_score` and `_weakest_cut`, the DELEGATES the
  scan missed while claiming to be structural (a ledger read placed in the shared
  delegate satisfied every assertion; 7 functions are scanned now, not 5). Recording
  never blocks a swap — the caller catches any exception, not just `OSError`, so a
  corrupted ledger can't traceback AFTER the deck file is written.
  **A swap applied only to MEASURE something still leaves a row** — prefer a dry run or a
  scratch copy, since a fabricated row is worse than a missing one. [G-56]
- **Match results are FREE from `Player.log`, and the header line is the load-bearing
  half** — the `finalMatchResult` JSON carries the outcome and both seats but NOT which
  seat is yours; that appears only in the `Match to <userId>:` prefix. A paste of the JSON
  alone is unparseable, so the parser SKIPS with a warning rather than guessing: a
  50%-accurate record is worse than an empty one because it looks like data. **Read the
  record with restraint** — under 20 matches `--report` refuses to print a percentage,
  above it prints a Wilson interval, and a small-sample win rate never belongs in
  `#: tier:`. [G-57]
- **NEVER widen `#: colors:` for a HYBRID card, and never reject a card for a widening you
  do not need.** Both halves were violated in one cycle: 26b's header was widened to UBR
  for `{B/R}` Bullseye, and Don & Raph was kept OUT of mono-blue 47 because its R identity
  "would widen `#: colors:`". `deck.py mana` already prints "identity has R (hybrid — paid
  on-color)" and `preflight` reads "castability PASS (+1 hybrid stray, ok)". Widening is
  WORSE than unnecessary: a wider baseline stops flagging a genuinely off-colour card added
  later. **The distinction is HYBRID vs GOLD and only the printed COST shows it** —
  `Color(s)` is identity and reads the same for both. Read the cost from `card-mana.csv` /
  `deck.py mana`, never from identity. **BULK-TRIAGE VARIANT, the costly one: never sort a
  PILE on the `Color(s)` column.** Hand-filtering 111 cards that way binned nine as
  off-colour of which EIGHT were castable — five hybrids, plus `{6}` Ramos (identity from a
  MANA ABILITY) and `{U}` Bruce Banner / `{1}{U}` Norman Osborn (identity from a TRANSFORM
  cost); only Iroh was truly gold. The one-card rule is easy to hold and a 111-row filter is
  where it breaks. **`deck.py screen <id> <pile>` is the tool** — it prints the cost and
  reads castability from it; `/add-cards` now requires it for a pile over ~10. [G-58]
- **A TRIBE'S VIABILITY IS ITS PAYOFF COUNT, NOT ITS BODY COUNT, and changelings cannot fix
  the missing half.** Measured across eight tribes: Dragon 71 bodies / 20 payoffs (built as
  deck 49), Dinosaur 52/11, Vampire 69/3, Mutant 79/**2**, Demon 28/1, Plant 27/1, God 21/**0**,
  Leviathan 5/0. Mutant has the MOST bodies of any tribe considered and is unbuildable —
  body count is the number that is easy to measure and the one that does not decide anything.
  A changeling is every creature type, so it RECEIVES tribal effects and never provides one:
  ten changelings in a Demon deck give you eleven Demons and still exactly ONE card that
  cares. Count the payoffs first (search the effect shape per K-13 — "Xs you control", "for
  each X", "X spells you cast"), and only then ask whether the bodies exist. The inverse
  reading — that a deep tribe must be supportable — is what makes a shallow archetype look
  buildable right up until the deck has no reason to share a type. [G-59]
- **An `{X}` SPELL IS PRICED AT MV 1, so a curve reading UNDER-reads any deck running
  several — and the distortion runs BOTH ways.** `mana_value` counts X as 0 because that
  is what the rules say off the stack, which is right for castability and for
  cast-on-curve probability (you really can cast Wildwood Scourge for `{G}`) and wrong as
  a CURVE reading: a card you realistically cast for four books as a one-drop and as an
  early drop. Deck 50a was misread twice in one cycle — adding two `{X}` spells made avg
  MV appear to fall 3.85 → 3.70, and removing one made it appear to rise 3.55 → 3.76,
  while the real curve barely moved either time. `deck.py stats` now lists them under
  `✕ X-COST cards` and `deck.py tier` prints a one-line "avg MV under-reads" advisory.
  Both are REPORT-ONLY and must stay so — a new term in `tier_band` would silently
  re-grade the roster, exactly as the protection axis is kept out. [G-60]
- **BEFORE DISMISSING A CARD, COUNT THE DECK PROPERTY ITS VALUE DEPENDS ON.** Four
  dismissals were overturned in one cycle, all the same shape — a card judged on its own
  text when the decision belonged to a number in the LIST. Michelangelo was called
  "circular, it needs combat damage" in the same commit that added Rogue's Passage to
  force damage through (the deck had SIX enablers); the power-as-mana dorks were called
  circular because "only Craterhoof pumps", in a deck running Colossification (+20/+20,
  not a win condition); Groundchuck & Dirtbag was cut as "a six-drop worth less than a
  two-drop" from the deck with 27 LANDS AND ONE CREATURE MANA SOURCE, which is precisely
  what its land-doubling reads; Agatha's Soul Cauldron was called "too narrow, needs
  exiled creatures" in the deck that SELF-MILLS four different ways. The control case is
  The Earth Crystal — rejected twice, correct the third time, with the card unchanged and
  the deck different. **State the count, then decide** (lands vs creature mana sources,
  trample grants, mill effects, counter sources), and when a card is parked say WHICH
  number would have to move for it to come back. [G-61]
- **BLIND MILL IS A CLOCK, NOT INTERACTION, and that is provable, not a matter of taste.**
  Milling M cards makes the opponent draw library positions M+1..M+D instead of 1..D, and
  in a random permutation any fixed set of D positions has the same distribution — so
  `P(they draw one of their k answers)` is IDENTICAL either way. Mill changes neither
  threat density nor access; it changes exactly one thing, the turn the library empties.
  Its payoff is binary, so it belongs next to the deck's other CLOCKS (turns-to-kill),
  never in its removal count. It is most tempting when you are behind on board, which is
  exactly when milling six does nothing about the threat killing you. **Three exceptions,
  all needing the mill to stop being blind:** SELECTIVE mill ("look at top X, bin one") IS
  interaction; mill + graveyard EXILE answers recursion (blue/colorless Standard: Ghost
  Vacuum, Soul-Guide Lantern, Wreck Remover, Mechanical Mobster); and a library already
  short. **The inverse is the G-42 shape** — blind mill FEEDS a graveyard deck. If the
  scorecard really says interaction, the fix is `suggest --needs` per G-38, not a mill
  card. Deck 51 is the worked case: its mill package is a second win condition. [G-62]
- **THE FRONT FACE AND THE STORED METADATA DISAGREE — ON EVERY COLUMN, AND IN EVERY
  INDEX.** G-02 is one member of a class that has produced SIX bugs across five columns —
  **COST** (a modal DFC stored only the front), **COLOR** (identity hid 55 castable
  red-pool cards — G-58), **TYPE** (a whole-line scan read the BACK face's; deck 49
  reported 26 lands holding 25), **NAME twice** (a bare front name written by
  `swap --apply`, then read back as DRIFT), **RARITY** (47 roster names priced blank) —
  plus FIVE more from the 2026-08 scan (two indexes, two exact-name JOINS, the editor's
  JS payload) and the ingest WRITE side, where reconcile/import_arena APPENDED a
  duplicate front-name row and split the owned count (BS2-02). **Ask which face a column describes; alias
  via `lib.alias_front` (the ONE second-pass home, ENFORCED by `check_dfc`'s registry +
  the editor-payload pin); key every name JOIN — a writer's too — on `_ms_key`.** The
  registry is now itself gated by an AST scan for pool-shaped name-index BUILDERS: it
  only ever checked loaders someone listed, and every bug in this class was a loader on
  no list (2026-08; it found `deck._legality_of` on its first run). [G-63]

- **A reanimator's uncastable bombs need `#: uncastable-ok:`, and everything else's do
  not.** The castability lint and `tier_band` both model "you cannot cast this" as a build
  ERROR, which is right by default and wrong for a whole archetype: one five-colour bomb in
  mono-black 52a moved `preflight` READY→BLOCKED and the floor A→C, for a card working as
  designed. The header is OPT-IN and PER-CARD (`#: uncastable-ok: A; B`, semicolons, like
  `#: protect:`) — most uncastable cards really are mistakes, so the default stays a hard
  FAIL. An exempt card is still PRINTED by `mana` and counted in `preflight` as
  "(+N intended, exempt)"; it leaves the failure list, not the page. [G-64]
- **Never hand-write a deck line's `(SET) COLLECTOR#` — get it from `deck.py resolve`.**
  Those fields were validated by NOTHING: `1 Eaten Alive (ZZZ) 172` passed `legal`, passed
  `check` (which reported it OWNED, because ownership joins on the NAME), passed
  `preflight` READY and passed `check_all`. A deck file could be integrity-clean and
  un-importable at once, and deck 52 was written with `(FDN) 610` against a real 172. Now:
  a set code that exists nowhere is a HARD INV-04 failure; an unheld collector number in a
  real set is a SOFT warning, since the pool keys ONE printing per card. Basics are exempt
  — Arena prints several arts per set. `deck.py legal <id>` lists both. [G-65]
- **`deck.py targets <id>` answers whether the deck holds TARGETS for its own gated
  effects** — MV caps ("reanimate a creature MV 4 or less"), sacrifice costs, count
  thresholds. Every other model here grades a card in ISOLATION, so a gate with nothing
  behind it is invisible: deck 52's concept pile held 24 ways to return a creature against
  8 worth returning, a number that had to be derived by hand. This is the automated half of
  G-61's "state the count, then decide". `✗ NOTHING` is a dead card; `⚠ thin` (≤3) is the
  shape to read. Counts exclude the card itself. Heuristic and report-only — read the list,
  not just the number. **Residual: it counts CARDS, so a TOKEN economy reads false-thin** —
  deck 58's artifact-sac gates reported "1 artifact" against 14 token producers; a deck
  whose resource is tokens must say so in its `#: notes:` or the flag invites a bad cut. [G-66]

- **A PATTERN SET IS A WHITELIST, AND A WHITELIST'S MISSES ARE INVISIBLE.** `_ROLE_PATTERNS`
  matches PHRASINGS, and Magic templates one effect several ways — so a card worded a way no
  pattern anticipates scores ZERO roles, and the tier floor, `cuts`, the quality guard and
  `check_all` all inherit that as fact. Never an error; the DEFAULT failure is a silent
  UNDER-count — but a too-broad pattern OVER-counts just as silently, and one did for its
  whole life (player-only burn counted as spot removal; 14 decks over-read the interaction
  axis — BS2-06, guard now in the pattern). Eight under-count holes surfaced in one
  2026-08 session, every one found by a HUMAN reading a card.
  **`check_roles.py` + `role_baseline.txt` make the population visible** (soft, deck-scoped,
  baselined); read it as a DELTA, not a target. Two habits follow: write a pattern's
  fixture from the CARD'S REAL TEXT, never a paraphrase — that is how you write a pattern
  for a card that does not exist — and check for a TEST DOUBLE encoding the old behaviour,
  since `check_suggest` anchor 15 asserted a fixer ranks most-cuttable PRECISELY BECAUSE it
  had no role. [G-67]

- **A `#:` HEADER THAT LISTS CARD NAMES GOES STALE, AND UNTIL 2026-08-07 NOTHING CHECKED
  ONE.** `#: protect:` and `#: uncastable-ok:` are read by the tooling as INSTRUCTIONS, so
  an entry naming a card the deck no longer runs is a silent no-op — `cuts` excludes
  protected cards BY NAME, so a name matching nothing drops out of the mechanism it was
  written for. Worse, `protect` also feeds a figure a HUMAN reads: the zero-protection flag
  prints "names N build-around card(s)", and deck 26b reported FIVE against a real four in
  the very sentence arguing its tier cap. `#: uncastable-ok:` is the more dangerous half —
  it SUPPRESSES a castability failure, so a stale entry is a disabled check. No gate could
  see the class: INV-04 validates deck LINES, the rationale audit reads `#: tier:` /
  `#: archetype:` PROSE, and a card-name list in a third header was checked by nothing.
  `deck.header_card_staleness` now sweeps the roster inside `check_all` (soft — pruning is
  editorial) and found two more the moment it ran: deck 56's Boros header protected two
  GREEN cards that live only in its Gruul variant 56a. Joined on `_ms_key` per G-63, so a
  DFC named by its front face does not read as stale. [G-68]

## Known Issues

Same convention as above — `[K-nn]` resolves in `docs/gotchas.md`.

- **An unindexed keyword is a HOLE every tag-gated predicate inherits**, not an inert
  gap. The acknowledged-but-unindexed list is `scripts/keyword_baseline.txt`. Triage a
  new set's keywords PER KEYWORD, not in bulk — of the ten this rule used to list,
  SEVEN were themed in 2026-08 (vivid→multicolor·payoff, job select→equipment·tokens,
  opus→spellslinger·payoff, increment→counters·spellslinger, infusion→lifegain·payoff,
  disappear→sacrifice·aristocrats, paradigm→exile cast·card advantage) and THREE were
  deliberately left, for three different reasons. **A keyword's reported COUNT is not
  its population**: Scryfall lists `Jump` on all 11 `Jump-start` cards, so mapping it
  would have put `evasion` on 11 graveyard spells for the sake of 2 real ones — the same
  source artifact that emits `Triple`/`Double`/`Somersault` off Tiered's mode names —
  and `undying`, added 2026-08-09, is the same shape: it reports 2 cards, of which the
  new one (Shadow of the Goblin) merely has an ABILITY NAMED "Undying Vengeance" and no
  Undying mechanic at all. Baselined, not themed.
  `tiered` is a COST SHAPE, not a resource, and its six cards' effects already tag
  correctly from text. A standing warning is a decision nobody has made yet. [K-01]
- **A keyword maps to the resources it COSTS** — `forage` → `["graveyard", "food"]`, not
  `sacrifice`. Mapping it changed only 2 of 9 cards because the rest quote reminder text
  the TEXT rules already read; the keyword map exists for the cards that state a keyword
  bare, and that tail is invisible unless you check them. [K-02]
- **`tag_synergies.py` text-tags fixing + topdeck-value engines** so they stop hiding
  under `selection`/`tokens` (cast-from-top → `card advantage`; spend-as-any-color and
  `land token` → `ramp`; all-basic-land-types → `mana`). **Residual: a fixer whose value
  scales with colour count but whose text carries no explicit any-colour / basic-land-type
  cue is still invisible — grade those from full text. Same shape one theme over: a card
  whose text names a CARD TYPE it never casts or equips (Gilgamesh digs for "Equipment
  cards") carries no tag for that type, so `suggest-homes` never surfaced his real home,
  the roster's 13-Equipment deck. A "what does this card look for" read beats the tags.** [K-03]
- **Never gate a predicate on a derived TAG — it inherits every hole in the tagger.**
  `_is_color_fixer` did, so the roster's two best fixers (keying off unindexed Vivid) read
  as non-fixers and `suggest-homes` proposed cutting the BETTER fixer. Read TEXT, in
  mana/land-type context, and exclude reminder text. When a gate blocks a fix, check
  whether it encodes the intent or merely the old implementation. (Vivid has since been
  themed — which does not retire the rule, it demonstrates it: reading TEXT is what made
  the fixer overlay survive the keyword being unindexed, and will again.) [K-04]
- **`pay life` is a tagged theme** (351 pool cards, 2.2% — specific enough to build
  around): YOU losing life as a cost, plus the cards that only CARE. "Each opponent loses
  2 life" is a DRAIN effect — the opposite card, deliberately not tagged. [K-05]
- **CHECK `MECHANIC_RULES` FOR THE NAME BEFORE ADDING A THEME.** `heist` (cast a card
  that was THEIRS) was first drafted as `theft`, a name already taken by the
  "gain control of" rule — reusing it silently UNIONED two mechanically unrelated effects
  and destroyed the specificity that makes an idf theme useful, **with `check_all` green
  throughout, because a tag collision breaks no invariant.** [K-06]
- **`exile cast` is the SIBLING of `heist` and stays separate** — casting your OWN exiled
  cards (impulse / Warp / Plot / Foretell / Adventure, 266 pool cards). The two only look
  alike; a deck built on one gets nothing from the other. [K-07]
- **`keyword_frequencies()` counts DISTINCT CARDS, not rows** — the mana file keys a DFC
  under its full `Front // Back` name, so a two-faced card could contribute two rows and
  clear the one-card noise floor without a second card existing. [K-08]
- **`tags_for` and `classify_roles` must agree on the same text.** Three phrases
  disagreed, each leaving a card with a blank Synergies cell and therefore invisible to
  every tag-based recommendation. **Residual: ~384 pool blanks remain — a genuine long
  tail of un-themeable effects, and a new theme for four cards is not the fix.** [K-09]
- **After editing a tag pattern, regenerate BOTH derived tag stores** —
  `tag_synergies.py --merge` for the LIBRARY and **`build_pool.py --all` for the pool**,
  which re-derives every pool row's `Synergies` through the same `tags_for()`. Skipping
  the pool rebuild used to leave unowned craft candidates ranking on stale tags SILENTLY;
  since BS2-23 the pool's build stamp carries the tagger's content hash, so an edit here
  defeats the freshness reuse and `make refresh` really does re-derive them. **That
  sentence was false for a year of stamps** — a pre-BS2-23 stamp had no hash and the reuse
  path never wrote one, so the check could not arm (BS3-02, G-18). VERIFY the pool
  actually changed after a tag edit; do not trust the step announcing itself. Never point
  `tag_synergies.py` or `enrich.py` at `card-pool.csv` — both write the library's 8
  columns and would destroy the pool's own. [K-10]
- **A few genuinely text-less vanilla creatures trip validate's blank-Card-Text
  warning** — expected, not an error. `card.py` / `deck.py text` label a resolved row
  with blank text "(no rules text — a vanilla creature (K-11), not a data gap)" since
  2026-08, so the blank no longer reads as an enrichment failure; only an UNRESOLVED
  card still says enrich/build. [K-11]
- **The functional-role breakdown and the castability lint are HEURISTIC, and they
  silently UNDER-count.** So every count carries its own uncertainty: `stats`/`tier`
  print `7`, `3 +2?`, or `8 +4? (3 unclassified)` plus a "⚠ Possible UNDER-COUNT" list.
  **Read the uncertainty, not just the number** — deck 40a was once graded on interaction
  3 against a hand count of 7. `role_tally` is the ONE canonical counter, so the number
  `stats` shows is the number the tier floor grades on. **When editing a role pattern,
  run a roster-wide before/after diff**: three sweeps found large silent under-counts,
  and a card sorted into the WRONG bucket is harder to detect than one in no bucket at
  all. The castability lint reads the deck's `#: colors:` header, so a stale header
  manufactures phantom strays — a flag is a review signal, not a hard failure.
  **CONNIVE is an unread keyword here**: Baron Helmut Zemo connives on every black spell
  and classifies as Payoff/Recursion, so deck 52's card advantage stayed at 3 across a
  ten-swap pass that genuinely moved the axis. A FLAT metric after a tune is not proof
  the tune failed. [K-12]
- **A LITERAL TYPE-NAME SEARCH CANNOT SEE THE CHOOSE-A-TYPE CATEGORY, and a false negative
  there reads as a finished answer.** A pool sweep for "Robots you control get" / "for each
  Robot" returned zero, and an entire archetype was declined in writing as "bodies without
  a payoff". There are FOURTEEN such cards in those colours and five are genuine lords —
  they say "as this enters, choose a creature type", so the category NEVER contains the
  type name. Deck 48 exists only because a later card pile surfaced one by accident. This
  is K-04 one layer earlier: that rule says do not gate a PREDICATE on a derived tag, this
  one says do not gate a SEARCH on a literal name when the effect is expressed generically.
  **Search the EFFECT SHAPE, not the noun** — "choose a creature type", "creatures you
  control get +1/+1", "of the chosen type" — and treat a zero-result sweep as an unverified
  search, not a fact about the format. Same shape as the changeling / kindred cards, and as
  any "permanents of that type" wording. [K-13]
- **A DRAW REACHED BY PAYING A COST IS A DRAW — FIXED 2026-08-07, and the fix's SHAPE is
  the rule.** Every Card-advantage pattern was TRIGGER-shaped, so `+1: Draw a card`,
  `{3},{T}: Draw a card` and every planeswalker's draw ability scored ZERO (187 pool cards,
  24 of them planeswalkers). An activated ability is repeatable BY CONSTRUCTION, which is
  the same argument the `whenever` pattern already rested on. **What made it safe to widen
  was three exclusions taken from rules this module already stated, not invented:** a
  `(?m)^` LINE anchor (an ability owns its line, so a cost quoted inside REMINDER text —
  every Clue and Blood maker — stays out); `discard` in the cost span (rummaging is
  card-neutral, the same rule `_LOOT_RE` implements one clause over); and `sacrifice this`
  (consuming the source makes it a ONE-SHOT cantrip, which the cantrip rule already
  excluded — keeping those took the change from 24 decks to 58 and re-graded the roster off
  a flood-insurance land). `_LOOT_RE` also gained the SINGULAR pair, which had been excluded
  only by accident. Result: 18 decks up, 12 down, **interaction unchanged and ZERO tier
  floors moved**. Prefer that shape — measure the floors before widening a role bucket. [K-14]

## Cycle Workflow Config

The canonical shape of this section is defined by `setup-cycle.md` in
[claude-workflow-tools](https://github.com/robinchoudhuryums/claude-workflow-tools) — the
command that writes it. Keep the fields TERSE and in that shape: the vendored workflow
commands read them, so the field structure is load-bearing. Detail belongs in
`docs/cycle-config.md` under the `[C-nn]` anchor a field carries.

**Test Command:** `python3 scripts/check_all.py` — the deterministic integrity gate; it
exits non-zero on any hard invariant break. INV-01…04 plus **fourteen model-sanity
gates** (`check_rankings`, `check_colors`, `check_dfc`, `check_suggest`, `check_engines`,
`check_tier`, `check_patterns`, `check_commands`, `check_agreement`, `check_docs`, and the
soft `check_keywords` / `check_roles` / `check_themes` / rationale-and-flex sweeps) — plus
three further SOFT roster sweeps this list used to omit: wishlist target drift, the G-68
card-name-header staleness pass, and the tier-mismatch pass. Two things to know
before touching it: it imports `deck` as a MODULE and calls `cmd_*` directly, so it never
builds an argparse tree — the CLI surface is covered by `tests/test_cli.py` and a CI smoke
step — and the reference-table loaders are memoized, which is what makes a roster-wide
sweep affordable enough to run automatically. What each gate guards, and the bug that
earned it: [C-01]

**Health Dimensions:**
- Data Integrity — CSV structure, no drift between library and derived files
- Enrichment & Tagging Accuracy — Scryfall-sourced fields and synergy tags
- Deck Tooling Correctness — deck.py / query.py / pool.py behavior
- Deck-Building Insight — mana (hybrid-aware), tribes, cost-nature, pool value
- Presentation & Interface — gallery/dashboard correctness and freshness, plus the
  interface layer `/broad-scan` Stage 3 grades structurally (keyboard/assistive access,
  empty-loading-error states, responsive posture, theme-token completeness, feedback on
  failure) across dashboard.html, gallery.html, templates/ and app.py
- Documentation Currency — README / CLAUDE.md / docs match the code and data

**Subsystems:**
- Data: card-library.csv, card-pool.csv, card-mana.csv, card-wishlist.csv, matches.csv
  (absent until the first `/log-matches`), recommendations.csv [C-02]
- Outcomes: scripts/parse_matches.py, recommendations.csv + `deck.py feedback` — the only
  subsystems that have seen a real game or a real decision [C-03]
- Ingest & Enrich: scripts/import_arena.py, scripts/import_collection.py,
  scripts/verify_ingest.py, scripts/enrich.py, scripts/tag_synergies.py,
  scripts/build_pool.py, scripts/build_mana.py, scripts/reconcile_crafts.py,
  scripts/sheets_sync.py, scripts/scryfall.py, scripts/lib.py [C-04]
- Analysis: scripts/deck.py, scripts/query.py, scripts/card.py, scripts/pool.py,
  scripts/wishlist.py, scripts/validate.py, scripts/check_all.py + the thirteen
  `check_*.py` gates, scripts/keyword_baseline.txt, scripts/role_baseline.txt [C-05]
- Presentation: scripts/build_gallery.py, gallery.html, image-manifest.json,
  scripts/build_dashboard.py, dashboard.html, .github/workflows/pages.yml,
  scripts/app.py, templates/, Makefile [C-06]
- Testing: tests/ (29 files: the markup-contract, CLI-entry-point, analysis-model,
  gate-pinning, shared-primitive and ingest layers, the 2026-08 ingest-writer /
  sync-guard / resilience-layer / CLI-filter coverage of the formerly untested
  scripts, plus the broad-scan-2 additions — test_check_all.py, the gate runner's
  own mutation layer; test_app_editor.py, the editor's write-safety pins
  (importorskip'd on Flask); test_check_dfc.py, which pins the G-63 builder SCAN
  rather than the registry it feeds; and test_writer_mutations.py, which runs each
  write-safety property against a mutant writer so the property is proven to be
  load-bearing), requirements-dev.txt, pytest.ini,
  .github/workflows/tests.yml [C-07]
- Decks: decks/

**Invariant Library:**
- INV-01 | card-library.csv has the canonical 8-column header, every row has 8 fields, no duplicate (Card Name, Set Code, Collector #) printing, and Quantity Owned is blank or a non-negative integer | Subsystem: Data | Verify: scripts/check_all.py (via validate.py)
- INV-02 | Every Card Name in card-library.csv has a row in card-mana.csv | Subsystem: Data | Verify: scripts/check_all.py
- INV-03 | Derived reference files exist AND keep their own schema: card-mana.csv (Card Name/Mana Cost/Mana Value/Keywords), card-pool.csv (…/Rarity; Legalities+Released+Power+Toughness warn if absent), gallery.html | Subsystem: Data/Presentation | Verify: scripts/check_all.py
- INV-04 | Every deck file under decks/ parses with no malformed card lines, AND every line's `(SET)` code exists in the pool or library (an unheld COLLECTOR # within a real set is a soft warning, since the pool keys one printing per card) | Subsystem: Decks | Verify: scripts/check_all.py
- INV-05 | Color(s) stores color identity; actual mana cost lives only in card-mana.csv | Subsystem: Data | Verify: design/manual
- INV-06 | Synergy tags are keyword-aware — regenerate via build_mana.py then tag_synergies.py --merge after imports (--merge preserves hand-curated tags; --force replaces them) | Subsystem: Ingest | Verify: manual

**Policy Configuration:** threshold 6/10; 2 consecutive cycles below triggers a policy
response.

**Regression Scenarios** (manual walks; the Test Command above is the primary gate).
Scenarios 5–8 need **a person at a browser** — they are the perceptual and interaction
checks a code read structurally cannot make. `/broad-scan` Stage 3 emits new ones in this
format.

1. Ingest a batch | Subsystem: Ingest & Enrich
   Steps: `import_arena.py <file>` → `make refresh` → `verify_ingest.py <file>`
   Expected: check_all clean, gallery card count == library row count, and every pasted
   card present at the expected count. `verify_ingest.py` is the step nothing else
   covers — check_all proves the library is self-consistent, not that it contains what
   you pasted. [C-08]
2. Analyze a deck | Subsystem: Deck Tooling Correctness
   Steps: `deck.py check|mana|consistency|tribes|stats|shape|legal|cuts|tier|tier
   --audit-rationale|redundancy|targets|text|verify <id>`, plus `feedback`, `suggest <id>
   --lands|--ramp|--interaction|--needs`, `screen <id> <names>`, and roster-wide `audit`
   / `suggest-homes` / `similar` / `resolve` / `rotation` / `pool.py --role`. Also
   `deck.py --help` and one subcommand help.
   Expected: no traceback; each command reports the axis it owns. [C-09]
3. Refresh derived data | Subsystem: Ingest & Enrich
   Steps: `make refresh` (never the steps by hand — the Makefile is the one executable
   definition of the order)
   Expected: check_all reports all invariants hold.
4. Edit via the app | Subsystem: Presentation & Interface
   Steps: start `scripts/app.py`, change a quantity and Save, add a card, open a deck (Decks →),
   change a card's quantity and Save; run `check_all.py`
   Expected: CSV + deck file updated, `.bak`s written, all invariants hold (INV-02 since
   an add appends a card-mana.csv row; INV-04 since a deck save re-parses cleanly). A
   deck save against a file changed underneath (e.g. a CLI `swap --apply` while the tab
   was open) is refused with a 409 "reload the page" toast, never silently overwritten.
5. Light-mode status colors | Subsystem: Presentation & Interface
   Steps:
     - Open `dashboard.html`, press `t` (or click the theme toggle) for light mode
     - Look at the roster-triage Action pills (TUNE / craft / review / ok)
     - Look at a deck card's build badge (buildable / N missing / N short)
     - Expand "Recently edited" — the +added / −removed delta lines
     - Paste any deck into the stale-deck panel — the in-sync / drifted text
   Expected: green/amber/red read clearly against the LIGHT panel background, are
   distinguishable from each other and from body text, AND each pill still reads as a
   bounded CHIP — a visible fill and border, not a loose coloured word. The TEXT moved
   onto `var(--ok)` / `var(--warn)` / `var(--bad)` at I-03; the FILLS and BORDERS
   followed at S-9, via `color-mix` off the same tokens (they had been dark-tuned
   literals whose ~1.3:1 edge disappeared over a white panel). A washed-out pill means
   one regressed back off the tokens.
6. Phone width — dashboard AND editor | Subsystem: Presentation & Interface
   Steps:
     - Open `dashboard.html` at 390×844 (or a real phone); scroll top to bottom
     - Open the roster-triage table and the wishlist table
     - Open a deck modal from the section-nav and switch tabs
     - Then `make app` at the same width: the collection grid, `/decks`, and a DECK
       editor page — scroll each, and edit a card line's quantity
   Expected: the page body NEVER scrolls sideways; the wide tables scroll inside their
   own boxes; the section-nav strip scrolls horizontally; every grid is one column. In
   the deck editor each card line WRAPS — the name on its own row above the
   qty/set/№/status fields — and a long `#` comment line scrolls inside its own row.
   The editor leg is new: `templates/` had no breakpoints at all until S-3, when a card
   row needed 472px inside the 350px a 390px viewport leaves.
7. Keyboard-only traversal | Subsystem: Presentation & Interface
   Steps: in `dashboard.html`, using Tab / Shift-Tab only, reach a colour filter chip, a
   quick-filter pill, a roster-table sort header, a section header (collapse it with
   Enter or Space) and a deck's ⤢ opener; open the modal, Tab through it, press Escape.
   On a deck card's tab strip try ← / →, and focus a wishlist card NAME to check the
   card image appears. Then the EDITOR (`make app`, `templates/collection.html`) colour
   pips, and the DECK editor's (`templates/deck.html`) Analysis tab strip; remove a card
   line with its ✕ and watch where focus lands.
   Expected: every control reachable with a VISIBLE focus ring; Enter and Space both
   activate; ← / → move along a tab strip (S-2 made them real tablists); the card
   preview follows FOCUS, not just the mouse (S-7); removing a row leaves focus on the
   next row's ✕, never on `<body>` (S-6); Tab inside the modal never reaches the page
   behind; Escape returns focus to the ⤢ that opened it. **Walk it once in each OS
   colour scheme** — the editor pages follow `prefers-color-scheme` since S-8 and no
   longer snap to forced dark mid-walk. The MARKUP half is pinned by
   `tests/test_templates.py`; what needs a person is the perceptual part. Full step list,
   the I-01/I-04 acceptance criteria, and the known SUCCESS-toast-cut-short-by-reload
   caveat: [C-11]
8. Editor failure feedback | Subsystem: Presentation & Interface
   Steps:
     - `make app`, open the editor, then STOP the server (Ctrl-C)
     - In the still-open page: edit a quantity and Save; click a card's ✕ and confirm;
       click Revert and confirm
   Expected: all three show a toast naming the failure. Remove and Revert used to do
   nothing at all — the rejected fetch died as an unhandled rejection right after a
   destructive confirm (F-02). This is that fix's acceptance test.

**Frozen Subsystems:** none.

**Deploy Command:** Data + local tooling ship by commit/push (no build/release step). The
one deployed artifact is the roster **dashboard**: `.github/workflows/pages.yml` rebuilds
`build_dashboard.py` offline and publishes it to GitHub Pages on every push to `main`.
`build_dashboard.py` restyles are **template-only** — the data pipeline feeding the
`#data` island is the source of truth and must stay untouched by any restyle. The
published page assumes a **2023-or-later browser**: it has long used `backdrop-filter`
and `aspect-ratio`, and S-9 added `color-mix` (Chrome 111 / Safari 16.2 / Firefox 113)
so the status pills' fills derive from the same token as their text. [C-10]

## Command provenance

`broad-scan`, `broad-implement`, `test-sync`, `sync-docs`, `health-pulse`,
`roadmap`, `sync-commands`, `targeted-audit`, `targeted-implement`, and
`pr-review` in `.claude/commands/` are copied **verbatim** from
[claude-workflow-tools](https://github.com/robinchoudhuryums/claude-workflow-tools)
— currently synced to template **v1.23.0**;
they stay project-agnostic and read everything from the Cycle Workflow Config
above. To update them, run **`/sync-commands`** with a path/URL to that repo (it
reports the template VERSION + CHANGELOG and diffs each file) and re-copy any it
flags OUTDATED — don't edit them here. They span the **Tier-1 loop** the project
runs (`broad-scan` → `broad-implement` → `test-sync` → `sync-docs`) plus **Tier-2
depth** (`targeted-audit`/`targeted-implement` for a single subsystem, `pr-review`
for per-change health) and the meta commands (`health-pulse`, `roadmap`,
`sync-commands`). The **Tier-3 full-cycle** commands (`audit`, `plan`, `implement`,
`regression`, `reflect`, `systems-map`, `cycle-*`, `setup-cycle`) are deliberately
NOT vendored — that two-axis-scoring ceremony outweighs its benefit at this project's
size; adopt them only if you later want benchmarkable scoring. **Two corrections to
that sentence, because it has aged.** The `.cycle/` state dir is NOT part of what was
declined — this project uses one (see "Session state" below), and reading the
un-vendoring as covering it would hide the handoff a fresh session is supposed to
start from. And **`systems-map` was re-tested, and the vendoring stays declined** — but
the MAP itself landed: **`docs/systems-map.md`** is a hand-written, TASK-first map (the
four things the user does: ingest · draft · tune+apply · prioritize crafts), not the
module map the generic Tier-3 command produces. That distinction is why the command was
still not worth vendoring: the module structure was never the friction. The map's
deliverable is the list of **reconciliation points** — every place a human must resolve
two answers by hand — plus the overlapping-answer inventory with MEASURED agreement
rates. Regenerate it by hand when a cycle adds a subcommand or a skill stage.
`check`, `refresh`, `add-deck`, `draft-deck`, `tune-deck`, `add-cards`,
`add-wishlist`, `roster-review`, `ingest`, `log-matches`, `pile-analysis`, and
`apply-changes` are project-specific. **A skill drifts behind the
tooling silently** — `/tune-deck` was still built around the command set it shipped with
and had no step for `consistency` (the probability layer), `engines`, `shape`, `cuts`,
`flex`, the protection axis, the role counts' own uncertainty, or the post-edit rationale
re-grounding. The load-bearing omission was the needs-aware `suggest
--needs/--interaction/--ramp/--lands`: plain `suggest` filters candidates to cards sharing
a synergy THEME and so structurally CANNOT surface removal or a land, i.e. the one
recommender a tune-for-interaction would reach for is blind to the fix. Re-read a skill
against the tool list whenever a cycle adds a command. `draft-deck` (BUILD a new
deck from scratch around a concept — survey the owned pool by role via `pool.py --role`,
scaffold the lines with `deck.py resolve`, then validate + tune for distinctiveness via
`deck.py similar`; the create-a-list counterpart to `/add-deck`, which INGESTS a pasted
list), `add-cards` (the cross-deck FIT PASS for cards you already own — it used to
catalog AND place, duplicating `/ingest`'s reconcile recipe and carrying its own copy of
the rebuild chain; cataloging now has one definition in `/ingest`, which runs the fit
pass itself whenever an ingest added NEW cards, so the half that actually decides
something stopped being the optional half), `add-wishlist` (intake UNOWNED craft targets to the wishlist —
add+enrich+Power-seed, set the home Target, do the cross-deck fit review via the
specific-theme-gated `suggest-homes`, audit), `log-matches` (record played matches from
Arena's `Player.log` into `matches.csv` via `parse_matches.py`, then read the record with
the restraint it needs — see the match-record gotcha below), and `apply-changes` (apply confirmed
swaps, run the F10 quality guard, re-ground the `#: tier:` prose via
`--audit-rationale`, verify + commit) **orchestrate the scripts, never
re-implement them** — the scripts stay the single source of truth so the skills
can't drift. `add-cards` is the OWNED-card counterpart to `add-wishlist`'s unowned
craft-target intake. All end with the shared verify+commit tail in
`docs/verify-commit-tail.md` (check_all-first, the Co-Authored-By/Claude-Session
trailer, no model ID, branch-restart on a merged PR) — edit that one file to change
the commit discipline for all.

## Session state — where to look when resuming

A fresh session loads THIS file automatically and nothing else, so anything a
resuming session needs has to be named here or it is not found. That is not
hypothetical: this file's own recurring lesson is that a capability nothing reaches
is invisible, and a handoff nobody is told to read is the same failure one layer up.

- **`.cycle/NEXT-SESSION.md` — read this FIRST when starting fresh.** The current
  cycle's diagnosis, the agreed next task, the measurements not worth re-deriving,
  and the traps. It is written for a session with no context and supersedes the
  older blocks where they disagree.
- **`.cycle/*-analysis.md`** — a LIVE `/pile-analysis` working doc, if one exists.
  Carries that pile's decision framework, its standing error list and the
  consolidated swap plan; it is TEMPORARY and says so, and it is deleted once the
  swaps land. Named here because a fresh session loads nothing else, and the whole
  point of committing it per batch is that it outlives one context window.
  **None currently live** — the 54-family doc was deleted when its swaps landed
  (2026-08-05), which is the contract working as intended.
- **`.cycle/STATE.md`** — prose record: what was completed, decisions made, what was
  decided AGAINST (worth reading before re-proposing a rejected fix), and where the
  last session left off.
- **`.cycle/blocks/*.md`** — one verbatim implementation summary per
  `/broad-implement` run. `/broad-scan` and `/roadmap` consume these in a FRESH
  session, which is why they live on disk rather than only in chat.
- **`docs/verify-commit-tail.md`** — the commit discipline every writing skill ends
  with. Live.
- **`docs/cycle-config.md`** — the long form of the Cycle Workflow Config fields (what
  each gate guards and the bug that earned it, the full subsystem file inventories, the
  full regression-scenario steps), keyed by the `[C-nn]` anchor. Its canonical shape
  comes from `setup-cycle.md` in claude-workflow-tools — keep the fields terse. Live.
- **`docs/gotchas.md`** — the long form of every Common Gotchas / Known Issues rule:
  the incident, the measurement and the reasoning behind each, keyed by the `[G-nn]` /
  `[K-nn]` anchor the rule carries. CLAUDE.md holds the rule and any live residual so a
  session can act safely without opening this; open it to find out WHY. Live.
- **`docs/systems-map.md`** — the TASK-first map: the four workflows with their real
  command paths and costs, every **reconciliation point** where a human must settle two
  answers, and the overlapping-answer inventory with measured agreement. Read it when
  you need to know which command answers a question, or why two of them disagree. Live.
- **`ROADMAP.md`** — long-range ideas; regenerate with `/roadmap`. Live.
- **`docs/tooling-improvement-plan.md`** — **HISTORICAL, do not follow.** Findings
  F01–F15 all landed cycles ago and it is referenced from nowhere, but it reads like
  a live plan and one of its instructions is now WRONG (F01 specifies adding
  `lib.full_card_text()`, which was added, never acquired a caller, and was deleted
  as dead code). It carries a status header saying so.
