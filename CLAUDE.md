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
  deck's future, not a resource constraint, and those are different questions. **And the
  2026-08-27 sharpening: current WILDCARD BALANCES are out of scope for tuning entirely —
  never ask about them, never weigh them, never build a stamp for them; factor them in
  ONLY when Robin raises them in that conversation.** (A balance-stamp tool was proposed
  and declined for exactly this reason: any recorded balance invites the gating this
  paragraph exists to prevent.)

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
  library MOSTLY stores the front — else an owned DFC would read as `craft` (audit F6).
  Route every such join through `lib.owned_qty` (front-face aware); `check_dfc.py`
  hard-gates this (behavioral anchor + a static scan for raw lookups that bypass it).
  **"MOSTLY" is load-bearing — the library holds BOTH spellings, and this file claimed
  otherwise (BS6-01).** Eight rows are stored under the full name (the DSK Rooms + two
  DFCs), so the fallback only ran one way: `owned_qty` resolves full → front, nothing
  resolved front → full, and `deck.owned` answered **"NOT IN LIBRARY" for an owned
  card** — the exact string G-10 sends you to `reconcile_crafts.py` about. Both gates
  were blind: `check_agreement`'s ownership pair got the same wrong 0 from both sides,
  and `check_dfc`'s completeness scan walks only **card-pool.csv** builders while every
  ownership index reads card-library.csv. **All four library-side builders now alias
  through `lib.alias_front`** (`deck.load_collection`, `pool.owned_counts`,
  `card._owned_index`, `wishlist.owned_index`). `reconcile_crafts` and
  `import_collection` had each worked around this locally for years: when two writers
  route around a documented rule, the RULE is the thing that is wrong.
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
  sources" answer for three decks in one pass. **Piping `card.py` through `head`/`sed`
  re-creates the partial read from the inside** — it happened while grading (2026-08);
  the closing `━━ end · <name> ━━` bar is the tell that you saw the whole card. [G-01]
- **A split / Room / Adventure card's stored cost covers BOTH halves — read the FRONT
  face.** Use `lib.front_face_cost()` / `lib.mana_value()`; `parse_pips` and `load_mana`
  already do. A **MODAL DFC** is stored the same way now — either face is castable from
  hand — but its Mana Value is the FRONT face's, so it escapes residual 2 below; a
  TRANSFORM DFC keeps one cost, since its back is reached by transforming, not by paying.
  **The one live residual: a deck that plays a split card mainly for its BACK half reads
  cheaper than it plays** — grade that one from the printed card. (The second residual —
  `card.py` printing the COMBINED mana value, so Mirror Room // Fractured Realm displayed
  MV 10 for a `{2}{U}` three-drop — is CLOSED as of 2026-08-12: it recomputes from the
  front face like `load_mana` always did, and names which half the number describes. It
  had put the inspection surface G-01 mandates in direct contradiction with every analysis
  surface for a year, which is the shape to watch for: the fix landed in the ANALYSIS path
  and the READING path was never brought along.) [G-02]
- **Don't judge a card by printed mana value or a single subtype.** Read the card TEXT
  (it is in the CSV): `stats` flags ◊/△ cost flexibility and functional roles, `tribes`
  reads oracle text for cross-type synergies. [G-03]
- **A `#~` flex line rots SILENTLY, and BOTH HALVES of it rot.** `swap --apply` retires
  only the lines its own swap invalidates and `--audit-rationale` never reads the flex
  block. **The `+In` half was unchecked until 2026-08-11** — deck 28 proposed adding a
  card it already ran, and `flex_staleness`' own docstring had encoded that gap as a rule.
  First sweep: **7 real, 1 false** — BASICS are exempt, being unlimited in Arena, so
  `+Island` proposes a 25th land rather than a duplicate. **FIGURES in `#~ note:` prose
  are swept too** (`note_figure_staleness`), and ONLY figures: a card name in a build log
  is legitimate (252 citations across 51 decks), while a bare present-tense number is a
  claim about the CURRENT list — deck 50 argued from "a 3.11 curve with 21 early drops"
  against a live 3.31/16. `deck.py flex <id>` and two soft `check_all` warnings surface
  all of it; sometimes the fix is to RETIRE the line, not retarget it. Advisory — a flex
  line is a human note, so nothing edits one. [G-04]
- **A swap inherits the cut card's `# section` comment**, so the file then lies to the
  next reader. `swap --apply` warns via `section_mismatch`, on UNAMBIGUOUS headers only.
  The WARNING is advisory (where a line belongs is editorial) but the REMEDY is
  mechanical since G-77: pass **`--section "<header>"`** in the same command and never
  hand-move a card line, which retypes the printing fields G-65 governs. [G-05]
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
  `Cast` column. **`Pld` (matches played, from matches.csv) is REPORT-ONLY and stays so** —
  a COUNT, never a win rate, answering only "which decks are still untested"; it never
  reaches the verdict, and an all-`·` column says whether the RECORD is empty rather than
  letting that read as 99 untested decks. [G-07]
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
  colour identity). **ARENA'S BRAWL LABELS ARE INVERTED HERE**: Arena's "Brawl" is
  100-card = `#: format: Historic Brawl`; Arena's "Standard Brawl" is 60-card =
  `#: format: Brawl` (`normalize_format` aliases the spellings — `historic-brawl` once
  matched NEITHER set). A pool-absent card is *unverified*, not illegal. `deck.py brawl` is
  the roster-wide counterpart. **`deck.py cuts <id>` ranks weakest-fit cards and is a
  SHORTLIST, not a GRADE** — it cannot see raw power or spice, and on a creature-heavy
  deck it is a coin flip (50% vs 86% noncreature, at n=31 and n=103). **Three fixes were
  pre-registered and REFUTED** (body quality, tag-count normalization, role-credit
  reweighting — 0 of 7 mis-ranks fixed, 28 of 116 top-3 sets churned; the worst offenders
  are ZERO-role cards a weight cannot help) — don't derive a fourth. Read the oracle
  text, preview with `swap`, and hard-protect signature cards via `#: protect:`. `cuts`
  prints the axis the deck is SHORT on and flags `⌁scales w/ <axis>`. REPORT-only. [G-09]
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
  that sets counts EXACTLY (including down) — run it before a wildcard-spending pass.
  **A script that WRITES and NARRATES must write first**: reporting before writing let
  `--apply | head -6` die on BrokenPipeError having printed success and written nothing
  (two batches lost 2026-08-18, invisible to `check_all`). Fixed and pinned. [G-10]
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
  inventing a number; note `card_power(0)` is a real 0, so neither the helper NOR ITS
  CALLERS can use `or` — `power_threshold_flags` carried `card_power(...) or -1` for a
  year inside the very function this rule documents, until BS4-32 (every X-creature is
  printed 0/0, so `or` silently unknowns the commonest real zero there is).
  `deck.py stats` flags a "power N+" payoff few of the deck's creatures meet, **scoped by
  `_POWER_SCOPE_MINE_RE` to clauses about creatures YOU control**: removal measures the
  opponent's board and "TOTAL power N" is a SUM, and counting your own bodies was wrong
  in 16 of 27 roster flags. The flag reads the gating trigger's TIMING from its own
  ability line: an ENTERS gate keeps the "a body that GROWS after it enters won't satisfy
  it" caveat, while an ATTACK-time gate says the printed count is a FLOOR, since pumped
  bodies DO satisfy those. The one-size caveat had been copied into a `#: tier:` block as
  a fabricated weakness and retracted the same day. Printed
  stats still under-state any gate a growing deck loosens — read the timing. [G-16]
- **`card-wishlist.csv` records Power PROVENANCE** in a `Power Source` column
  (`seed` / `hand` / `unknown`). `wishlist.power_is_seeded()` treats seed, unknown and
  blank as untrusted; set `hand` when you grade one. [G-17]
- **`build_pool.py --all` and `build_mana.py --pool` are the FULL-coverage scopes.** Both
  DEFAULT to something smaller, so a plain rebuild silently shrinks coverage back; both
  now refuse a >50% shrink (`--allow-shrink` to force). `build_mana.py` is also
  INCREMENTAL — it reuses already-resolved rows — and `build_pool.py` REUSES a pool built
  within the last week for the same query (99% of the old refresh cost was its 91
  paginated pages). Skipping it is correct, not just fast: the pool is independent of what
  you OWN, so an ingest cannot change it; what goes stale is `Legalities` and a new set. **But a TAG-PATTERN edit also stales it**, which the reuse could not see: the
  stamp records a content hash of what `tags_for` depends on — `tag_synergies.py`'s BYTES
  plus the VALUE of `deck.ENGINE_THEMES` (BS2-23; BS4-37 hashed all of deck.py, BS5-06
  narrowed it back because that staled the pool every cycle) — and a mismatch defeats it. An ABSENT hash means UNKNOWN and rebuilds ONCE (the
  reuse path returned before writing a stamp, so "unknown = reuse" could never arm —
  BS3-02). **Stated non-goal:** card-mana.csv's keyword frequencies also feed the noise
  floor and are NOT hashed, because a derived file's hash would change on every mana
  rebuild and the reuse would never fire. `--refetch` (`make refresh REFETCH=1`). [G-18]
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
  A shortlist that prints the card lists — read them. **A GRAVEYARD ENGINE HAS TWO
  OWNERS**: the enabler cues are ownership-blind (opponent-discard/mill match) and the
  payoff cues were own-scoped, so a deck that fills THEIR yard and casts from it read
  "N enablers, no payoff" — decks 44/44a, four real payoffs each. `_GY_CONSUME_OPP_RE`
  (consumes their yard) is now separate from `_GY_NEED_OPP_RE` (merely wants it full —
  an opponent-MILL card is an ENABLER), and reminder text is stripped before either:
  "cards in their graveyards is a crime" made every crime card read as yard-dependent.
  **Nothing gate-checked a PROPOSED add either** — `unmet_gate_note` runs `targets`
  against a recommendation now (partial: an opponent-BOARD condition is outside that
  model). [G-23]
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
  false negative is silent, and three sweeps each found figures the audit had reported
  clean. A CARD citation and a FIGURE go stale differently and must not share a predicate —
  the CARD path kept a broad `remov\w*` for a year, so a card saying "removes" suppressed
  its own report. The 2026-08-09 rework clause-scoped both cue families and found six real
  stale rationales. **The sweep is least optional when you WIDEN the scan**: extending it
  to archetype figures (G-27) returned 3 hits of which 2 were FALSE, and their suppressions
  muted the 1 real one until the parent-name case was handled. **CLOSED 2026-08-11: a
  PREFIX COLLISION** — only IN-DECK names were masked, so a fragment of an ABSENT card's
  name resolved to a DIFFERENT card. **STILL LIVE:** a copula hides a figure ("protection
  is 1"); "the swap removes X" about a CUT card reads as live; a 4+-card fragment drops as
  an epithet; a card absent from the POOL is invisible; and a figure needs its cue ADJACENT
  ("the fastest curve here at 2.44" is missed, deck 26b). [G-26]
- **Run `tier <id> --audit-rationale` after ANY deck edit.** The tier guard checks the
  LETTER; this checks the ARGUMENT — cards the prose cites that the deck no longer runs,
  and figures the live quality vector contradicts. A swap moves those numbers by
  construction. Scoped to `#: tier:` AND `#: archetype:` — for CARDS since it was written,
  and for FIGURES only since 2026-08-09: this rule claimed both for a year while the figure
  loop read `tier` alone, so an archetype figure could contradict the vector indefinitely.
  Widening it needed two clause-scoped suppressions — a figure about another deck named by
  NAME, and one whose subject is the card POPULATION ("Standard's Dragons average MV 5.30")
  — plus the rule that a name forming part of THIS deck's own name is not another deck,
  since the variant convention makes 26a "Iron Forge — Virulent". `#: notes:` stays out of
  the STALENESS scan — a build log may name an absent card — but an EXCLUSION claim in it
  is checked. Same split for `#~ note:` prose since 2026-08-11 (G-04). Report-only. A rationale naming a card it cut must put the change-cue in the
  SAME clause. **Residual: the EXCLUSION check has a proximity window and misses a name
  several lines into a wrapped list** — deck 52 named Zemo under "Deliberately NOT
  included" while running him, and `wrong_exclusion_claims` returned empty. [G-27]
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
  next. **EVERY craft view carries the flag** — `check` inline per missing/short card,
  `wildcards` (incl. `--dedup`), `suggest --lands/--ramp/--interaction`, `tier --to`'s
  fillers. Owned rows are exempt: an owned card costs no wildcard. **The windows must
  MATCH and did not**: `rotation_risk` read `<= year` until 2026-08-28, one year
  stricter than every sibling, while a docstring asserted they "cannot disagree" —
  `suggest --unowned` was its last caller, so the craft recommender under-flagged by a
  full rotation. **A claim that two implementations agree is not agreement.** Plain
  `suggest` also excludes LANDS now: a land has no cost, so the printed-cost castability
  gate (G-58) passed an off-colour one unconditionally.
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
- **Castability reads the PRINTED COST (`suggest-homes`, the last identity-subset holdout,
  converted 2026-08-20 — G-58) and says nothing about PIPS.** A `{W}{W}{W}{W}{W}` was KEY for
  decks with 10–11 white sources, roughly a 1% chance on turn five. `pip_depth_warning`
  prints `⚠⚠ 5x{W} vs 10 sources` from the same hypergeometric model `consistency` uses.
  It is a FLAG, never a score change. **Two 2026-08-13 fixes, and both are the G-40 shape
  — a working primitive nothing asked.** It had ONE caller, `suggest-homes`, so the
  DECK-level recommender that surfaces craft targets never ran it; `cmd_suggest` calls it
  now. And the floor was 3 pips, so `{2}{B}{B}` Elegy Acolyte was recommended into a deck
  holding EIGHT black sources — 45% on curve — and the helper returned None. The bar is
  pip-count aware now (`_PIP_DEPTH_TARGET_BY_PIPS`): 3+ pips grade at 0.70 UNCHANGED, 2
  pips at 0.55. Read the bands as different claims — 3+ says "you cannot cast this", 2
  says "you will cast this late". 0.55 was measured, not chosen: at 0.70 the 2-pip band
  fires on 109 maindecked cards against 25 today and most are ordinary 10–11-source
  cards, which trains you to ignore it; at 0.55 it fires on 43 and isolates 3–9
  sources. [G-32]
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
  structurally blind to lands (it filters to cards sharing a synergy theme). Scored on
  FIXING value plus bounded synergy/scarce-colour nudges, and it applies the deck's
  `#: format:`. **Both 2026-08-09 fixes were about admitting or pricing the wrong card:**
  the candidate filter scanned a whole type line, so 81 pool cards with `// Land` on the
  BACK qualified — three of deck 52's four top picks were unplayable as lands — now fixed
  to front-face `_primary_type`, the same fix `wishlist._is_land` got in BS2-11 and this
  sibling did not; and RESTRICTED mana ("spend this only to cast a creature spell", which
  had ranked #1) now has its fixing premium halved and prints `·restricted`. **The
  conditionally-tapped miss this rule used to claim was NOT REAL** — the 5.8-vs-4.6 gap
  cited was mono-colour vs DUAL, not tap handling. The real limitation is the opposite and
  conservative: a conditional land never gets the untapped premium even when the deck
  meets the condition, so it prints `·tapped?` for a human read. [G-37]
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
  failure. Coverage requires a REAL call, not a prose mention — on ALL THREE paths: the
  script half accepted any filename mention until 2026-08 (two of `build_pool.py`'s three
  were warnings NOT to run it) and wants `python3 scripts/<fn>`; the Makefile half matched
  COMMENTS until BS4-25; and the SUBCOMMAND half counted a caution ("never run `deck.py
  sync` blindly") until BS4-09. **That last one is where the obvious fix was wrong**:
  demanding the executable shape there would have failed 27 of 34 live subcommands, since
  the skills write 30 of their references bare and only 3 sit in fenced code blocks — so a
  caution CLAUSE is suppressed instead, which measured as costing zero coverage. [G-53]
- **A SET plus a sort key that can TIE is a nondeterministic output.** Tied themes left
  in set-iteration order made an unchanged build produce different output every run.
  **Before sorting anything derived from a set, ask what happens when the key ties** —
  make the key a total order. **First LIVE violation, 2026-08-12: `deck.py similar`
  answered differently on every run** (five `PYTHONHASHSEED` values, five outputs) —
  `_deck_central_weights` built its weight vector by iterating `_central_themes()`, a
  SET, and the display truncates to `shared[:5]`, so WHICH themes you were shown changed
  run to run on the exact ✦ SPECIFIC overlaps G-47 says to grade from. **The fix is the
  KEY, not the return type**: two callers do `ctags & _central_themes(...)`, so making it
  a tuple is a TypeError. Fix the ORDER where order is consumed, and remember a float SUM
  over a set is the same bug wearing arithmetic. **ENFORCED since 2026-08-12 by
  `tests/test_determinism.py`** (7 commands × 2 `PYTHONHASHSEED` values, byte-compared).
  It sits in PYTEST, not `check_all`, for G-55's reason — it needs separate interpreters —
  so `make check` alone misses this class and `make verify` catches it. [G-54]
- **NO GATE BUILT AN ARGPARSE TREE, so a broken `--help` was invisible** for four days
  with three green workflows. `check_all` imports `deck` as a MODULE and calls its MODEL
  functions — 16 of them, and **zero `cmd_*`**, which this rule claimed for a year: the
  untested surface is therefore the whole COMMAND layer, not just the argparse tree.
  `tier --to` pairing a filler with a cut that undid its own gap (2026-08-24) lived
  exactly there. The CLI is covered by `tests/test_cli.py` and a CI smoke step. Note argparse renders help through `help % params`, so **a bare `%` in a
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
  scratch copy. **`swap_outcomes` joins the ledger to `matches.csv`** — the one signal
  these models cannot influence — banned from those same seven functions for a STRONGER
  reason (a win rate looks like ground truth), split per DECK not per swap, and refusing
  to read under 20, which is where it sits. G-57 governs it. [G-56]
- **Match results are FREE from `Player.log`, and the two lines AROUND the result JSON are
  the load-bearing halves.** `finalMatchResult` carries the outcome and both seats but NOT
  which seat is yours; that is only in the `Match to <userId>:` prefix, so a paste of the
  JSON alone is unparseable and the parser SKIPS rather than guessing — a 50%-accurate
  record is worse than an empty one. **`courseId` is NOT a deck, it is the AVATAR
  cosmetic**; the columns are `My Avatar` / `Opponent Avatar`. The deck you played is in
  **`EventSetDeckV3`**, joined on TIMESTAMP and resolved `--deck` → `#: arena:` header →
  the name's leading NUMBER, with the run PRINTING the route AND the two integers behind
  each W/L (G-52). **Two reason fields and only one carries information**: `Reason`
  (`matchCompletedReason`) is `Success` for every match that COMPLETED — 58 of 58 — while
  `Ended By` (Game vs Concede) varies and is most of the signal at low n. **Read with
  restraint** — under 20 matches `--report` refuses a percentage. The per-deck split
  CANNOT reach that floor at 111 decks (best row n=8), so it also POOLS, which answers a
  different question: whether YOU are winning, never whether a deck is good. [G-57]
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
  INDEX.** G-02 is one member of a class that has produced bugs on five COLUMNS — cost,
  colour (identity hid 55 castable red cards — G-58), TYPE (deck 49 read 26 lands holding
  25; `suggest --lands` offered 81 back-face lands, G-37), name twice, rarity — plus the
  **Ask which face a column describes; alias an INDEX via `lib.alias_front` in a SECOND
  pass — NEVER in-pass with `setdefault`, which lets a DFC seen early claim the bare front
  key a distinct card owns (BS4-18 closed the last four, three of them indexing Scryfall
  RESPONSES and so invisible to the pool-reading scan) — key every name JOIN, a writer's
  too, on `_ms_key`, and read a `#:` header's card names through
  `deck._header_card_keys`.** Gated by `check_dfc`'s registry, its AST scan for name-index
  BUILDERS and its editor-payload scan. That scan was POOL-scoped — hiding FOUR
  library-side indexes from a gate built for its own bug class (BS6-01) — and now covers
  both files; **a gate whose scope excludes the file the bug lives in is absent, not
  narrow.** It also needs a probe the index can HOLD: a pool-only probe passed VACUOUSLY. [G-63]

- **A reanimator's uncastable bombs need `#: uncastable-ok:`, and everything else's do
  not.** The castability lint and `tier_band` both model "you cannot cast this" as a build
  ERROR, which is right by default and wrong for a whole archetype: one five-colour bomb in
  mono-black 52a moved `preflight` READY→BLOCKED and the floor A→C, for a card working as
  designed. The header is OPT-IN and PER-CARD (`#: uncastable-ok: A; B`, semicolons, like
  `#: protect:`) — most uncastable cards really are mistakes, so the default stays a hard
  FAIL. An exempt card is still PRINTED by `mana` and counted in `preflight` as
  "(+N intended, exempt)"; it leaves the failure list, not the page. [G-64]
- **Never hand-write a deck line's `(SET) COLLECTOR#` — get it from `deck.py resolve`,
  and verify a freshly WRITTEN file with `deck.py resolve --check <id>`** (strict: an
  unheld printing FAILS there, where check_all keeps it soft — eleven hand-written
  numbers shipped wrong across the two 2026-08-21 drafts and only a hand-run diff
  caught them; /draft-deck Stage 4 now runs it).
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

- **A GATE THE DECK MEETS FOR FREE IS NOT A COST, AND EVERY MODEL HERE READ IT AS ONE.**
  G-66's `targets` asks only "does the deck CONTAIN N cards of shape X" — all 13
  `_TARGET_GATES` count cards in the list — so a card gated on a GAME STATE was invisible
  in **both directions**, and one 2026-08-24 session hit each end: Ketramose needs seven
  cards in exile against **three** sources, and Lake-town Toymaker needs "drawn two or more
  cards this turn" in the deck whose second engine draws one **every turn**, so its pump is
  UNCONDITIONAL — it was one confirmation from being cut as a conditional one, having scored
  fit 17 / power 2 / uniqueness 0 / **no detected role**. `deck.py targets` now prints a
  STATE GATES section reporting both ends (`CANNOT turn on` / `thin` / `free`), with
  proxies from `role_tally` so a gate and `stats` cannot answer one question differently.
  **Only 2 of 6 families shipped**: a roster sweep found lifegain, artifacts and drain
  structurally always satisfied, and delirium MIS-PROXIED — it asks about the GRAVEYARD,
  and counting types in the DECK is a bound any 60-card list clears. **Residual: the two
  live families are n=4 and n=1 on the roster** — read a band as provisional. [G-76]
- **A PREVIEWED SET IS IN SCRYFALL MONTHS BEFORE YOU CAN PLAY IT, and the pool took its
  printings.** Scryfall indexes spoiled cards immediately and `unique=cards` returns the
  NEWEST printing, so a reprint in an unreleased set became the ONLY printing the pool
  held — and `deck.py resolve`, the MANDATED source of deck-line printings (G-65), emitted
  it. Measured 2026-08-24: 114 pool rows dated in the future, **109 deck lines across 47
  files**, and two round-tripped through an Arena export into `card-library.csv`, so
  OWNERSHIP recorded an unreleased printing too. `build_pool`'s defaults now carry
  **`date<=now`** — the literal token `now` is load-bearing, since the freshness reuse
  compares `stamp_query == query` and a formatted date would refetch daily. A custom
  `--query` is NOT rewritten. **`resolve --fix <deck> --apply` is the repair half**
  (G-77: `--check`'s only remedy was a hand edit). Backstop: a `check_all` soft sweep on
  the POOL, since one report covers every craft recommender at once. **Residual:
  `Released` is still read only for rotation elsewhere — no per-card surface asks "is this
  out yet", so a stale or custom-query pool re-opens it.** [G-79]

- **A CARD THAT GRANTS A KEYWORD IS A CARD ABOUT THAT KEYWORD, and the tagger only read
  what a card HAS.** Keyword tags came from Scryfall's `keywords` field, so a lord handing
  the team deathtouch carried no `deathtouch` tag and looked like a card with nothing to do
  with the deck built on it. **1,941 pool cards grant one of the twelve evergreens**, and
  for FOUR the granted case is the MAJORITY (indestructible 224 vs 83 native, hexproof 151
  vs 56, first strike 172 vs 145, double strike 112 vs 75), so the tag tracked the
  exception. `tags_for` reads grants from TEXT now (`granted_keywords`, reminder text
  stripped, opponent- and loss-scoped clauses excluded). **What it moved and what it did
  NOT is the useful half:** tags feed `cuts` / `suggest` / centrality, so deck 31's Venom
  Connoisseur went fit 17 → 68 and stopped being offered as a cut (a real, user-caught
  mis-suggestion), while `tier_band` grades on `role_tally`, which reads TEXT — K-14 diff
  **0 decks, 0 tier floors, 0 role counts**. One SIDE EFFECT needed a human: more tags
  raised the dominant theme's count and with it the 25% centrality floor, so four decks'
  quoted central-theme figures went stale, one load-bearing in a `#: tier:`. [G-80]

- **AN ADVISORY YOU CAN ONLY ACT ON BY A FORBIDDEN EDIT IS A HAZARD, NOT A WARNING.**
  G-05's `section_mismatch` correctly flags an add that inherited the cut card's
  `# section`, but the only way to act on it was to hand-edit the deck file — and G-65
  forbids exactly that. Relocating four lines by hand in one 2026-08-24 session invented
  two collector numbers (`(HOB) 26` for a real 24, `(HOB) 21` for a real 19), caught only
  because `resolve --check` happened to be run after. **`swap --section "<header
  substring>"`** now moves the line VERBATIM as part of the same write, so the printing
  fields cannot be retyped; it refuses an absent or ambiguous header BEFORE writing, and
  the warning now names it. **`deck.py move <id> "<card>" --section` (2026-08-27) is the
  standalone form** — relocating an ALREADY-written line used to take a swap-out/swap-in
  pair, which polluted recommendations.csv with rows that were relocations, not decisions.
  **When a warning's only remedy is a manual edit of a file the rules say never to edit
  manually, the tool owes you the mechanical form of that edit.** [G-77]

- **A SHARING CLAIM IS NOT A COMPARISON, and the citation audit suppressed it as one.**
  `_cites_as_history` treats any clause naming another deck as comparison context, which
  is right for "where deck 42 spends its splash on X" and WRONG for "only FIVE nonland
  cards are shared (X, …)" — the second asserts X is in THIS deck. Deck 43's tier block
  named a card it had not run in months. Narrow `_SHARING_CUES` carve-out; roster sweep
  returned 0 new hits. **The residual is bigger than the fix and is MEASURED, not
  guessed: `_RATIONALE_MIN_LEN = 9` hides every single-word card name shorter than that**,
  which is what actually hid `Erode` — lowering it to 5 surfaces 7 roster hits of which
  only 3 are real (43 Wolfbat, 42a Ahriman ×2 — all three fixed on discovery), and to 7
  gives 3 real against 2 false. Both rates would put permanent false warnings in
  `check_all`, which trains you to ignore the sweep, so **the floor stays at 9 and short
  single-word citations remain invisible**. Re-measure before changing it. [G-78]

- **A TUTOR IS WORTH THE NUMBER OF THINGS IT CAN FIND IN *THIS* DECK, and that number was
  checked by nothing.** Deck 76 ran ZERO basics while TWO cards searched for them
  (Bloomvine Regent's Omen half, Encroaching Dragonstorm) — found by the USER IN PLAY, by
  no gate, and the second had been ADDED the day before *on the fetched basics as its
  stated rationale*. `deck.py targets` now counts library searches and `check_all` sweeps
  the ZERO case. **Three build-earned constraints, all still live:** the gate is
  ZERO-ONLY (a thin count is editorial, an empty one is dead text); it SKIPS the
  saturating searches — an unconditional "search your library for a card" is always
  satisfiable, as are the creature/land/artifact type-wide ones; and it must NOT skip
  LANDS, which is where fetches live (its own test caught that omission, and the fix
  immediately found two more). **Read a hit as a claim about the SEARCH, never the CARD:**
  Hobbit Hole's basic fetch works in the decks where only its Halflingcycling rider
  whiffs, and The Masters of Evil is still a Villain anthem. [G-75]
- **A PATTERN SET IS A WHITELIST, AND A WHITELIST'S MISSES ARE INVISIBLE.** `_ROLE_PATTERNS`
  matches PHRASINGS, and Magic templates one effect several ways — so a card worded a way no
  pattern anticipates scores ZERO roles, and the tier floor, `cuts`, the quality guard and
  `check_all` inherit that as fact. Never an error; the DEFAULT failure is a silent
  UNDER-count — but a too-broad pattern OVER-counts just as silently (BS2-06). 23 holes
  closed in 2026-08 — NEUTRALIZATION (**ask which rule a family takes before reusing
  one**), PER-TURN ENGINES (K-14's shape one bucket over), WARD (K-09's two-models shape
  vs the G-25 axis) among them. **A PATTERN hole is fixed and measured; a TAXONOMY hole
  (Equipment, selection, hand attack — no bucket exists) is a design decision that
  re-scores the roster — triage the backlog by that line.** **`check_roles.py` makes the
  population visible** — `role_baseline.txt` for zero-role ROSTER cards, `--tags` for
  POOL cards the two models disagree about. Read both as a DELTA. **Live residual: the
  138-entry worklist + the AURA `+N/-M`** (a curse and a pump one shape cannot
  separate). Fixtures from REAL TEXT; check for a TEST DOUBLE. [G-67]

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

- **A BASELINE UPDATED BEFORE THE GATE THAT READS IT IS A MUTED GATE.** `make postedit`
  ran `check_roles.py --update-baseline` unconditionally and FIRST, so every new zero-role
  card was acknowledged before `check_all` could warn about it — on the exact workflow
  (after every deck edit) the radar was built for. **FIXED broad-scan-7: the acknowledge
  step now runs LAST** (dashboard → `check_all` → `--update-baseline`), so the warning
  fires on the run that earns it and step 3 clears it. `--update-baseline` rewrites the
  file from the CURRENT set, so it cannot tell one genuinely roleless new card from a
  `_ROLE_PATTERNS` edit that just re-zeroed fifty; it therefore NAMES every card it
  acknowledges and REFUSES a jump over `--max-new` (postedit passes `MAXNEW`, default 8 —
  `make postedit MAXNEW=40` for a deliberate bulk pass). `check_keywords.py
  --update-baseline` got the same delta report and `--max-new` (BS4-10); it has no
  automated caller, so it was never MUTED. **The shape generalizes: when an acknowledge
  step and a warn step run in one command, the ORDER decides whether the warning exists at
  all** — and the convenience of automating the pair is what hides it. [G-69]

- **BUILDABILITY IS PER CARD NAME, NEVER PER LINE — one definition, `deck_requirements` /
  `deck_build_gap`.** A deck may list the same card on two lines, and owned counts are
  per-name (copies are fungible across printings), so "do I own this deck" must compare
  TOTAL need against TOTAL owned. `cmd_check` always did and said so in a comment — and a
  comment is not a mechanism: `app.py`'s `/decks` overview and `check_all`'s info summary
  each re-derived the question per LINE, so a deck listing 2+2 of a card owned 3 read
  "buildable" on those two surfaces while `deck.py check`, the dashboard and the deck
  editor called it short. Three implementations of one question, and the two that drifted
  were the two that copied the loop instead of calling it — the shape `check_agreement.py`
  exists to catch, in a spot it does not reach. `/decks` also counted LINES as `unique`.
  **When you find yourself writing a second loop over `cards` that compares against owned,
  call the helper instead.** [G-70]

- **A MEMOIZED TABLE IS SHARED STATE, and a helper that mutates its ARGUMENT will mutate
  it.** `_file_memo` hands every caller the same dict, and its docstring rested the whole
  memo on "every caller treats these tables as READ-ONLY — verified by scanning all of
  scripts/". Five sites in that same file were mutating them: `fetch_missing_mana` /
  `fetch_missing_rarities` write into the dict they are GIVEN, and `cmd_stats`, `cmd_mana`,
  `cmd_consistency`, `_do_swap` and `cmd_wildcards` were handing them the cached object.
  Invisible on a one-shot CLI run; in the Flask editor — one process, many decks — deck B's
  Stats tab computed its curve from costs deck A's Mana tab had live-fetched, so the editor
  disagreed with a fresh `deck.py stats B` depending on click order. **Pass
  `dict(load_*())` whenever a fetcher will touch it.** The transferable half: *a claim
  about all callers is only as good as the last person who added one* — the property is
  pinned behaviourally now (`TestMemoizedTablesAreNotMutated`), because a source scan is
  what failed. [G-71]
- **A CONTROL BUILT IN JAVASCRIPT IS A CONTROL ONLY IF IT GOES THROUGH `a11y()`.** Four
  times a click handler has been bound to a non-interactive node (collection pips I-01,
  editor tabs S-2, the triage Deck cell and card-finder chips in 2026-08). **All of them
  were in the GENERATED pages**, because `tests/test_templates.py` pins `templates/` plus a
  few NAMED dashboard controls and cannot see a new one. When a11y-ing a node inside a table,
  apply it in `sortableTable`'s `onRowExtra` — `redraw()` rebuilds `<tbody>` on every sort,
  discarding attributes set once. The same files hide hardcoded colours (`gallery.html`'s
  literal `#0f1115` track; the dashboard's mana tokens had no light value at all, BS6-02).
  **AN A11Y'D NODE IS NOT A11Y'D BEHAVIOUR**: `attachHover`'s focus listeners sat on bare
  spans at 2 of 3 call sites, and `focus` neither fires on a non-focusable node nor bubbles,
  so the preview followed focus at ONE site for months — and Scenario 7 named that site, so
  the walk passed over an inert feature (BS6-03). **Write a scenario step from the FEATURE,
  not from the fix.** **A STATIC A11Y GATE WAS MEASURED UNBUILDABLE — do not restart it**
  (three designs, every flag FALSE). The COLOUR half IS gated since 2026-08-26: a page must
  define every `var(--x)` it emits. Scenario 7 stays the a11y half's only coverage. [G-72]
- **A DECK'S REPO NAME AND ITS ARENA NAME ARE DIFFERENT STRINGS, and NEITHER is
  authoritative — so never gate anything on their agreeing.** Of 22 CORRECT `#: arena:`
  mappings, **8 DISAGREED** ("49 Big Draco" was repo deck 49 "Scaleforge"): the Arena names
  are FLAVOUR names, so a name-agreement check on the attribution path would block a
  correct attribution 36% of the time (the G-07 saturation shape). The leading NUMBER stays
  the only match key; the repo name is merely DISCLOSED beside a guess. `--sync-names
  --apply` is the RECONCILE half (adopted 12 on 2026-08-14) and is a **DRY RUN without
  `--apply`** (it wrote on its own until 2026-08-26). Four earned rules: identity is the
  **DeckId GUID**, never a card list (it changes the moment you tune); **typography is not
  a rename**; a variant keeps its `<parent> — <variant>` prefix, and renaming a PARENT
  orphans its variants — flagged, never cascaded; a rename **strands prose citations** (50
  of 106 decks are named in another's prose). **The divergence REGROWS** from client-side
  renaming, so today's agreement is a snapshot, not a reason to add the gate — docs cite it
  with examples that now read as agreements *because* the sync ran. Re-measure first. [G-73]

- **THE LOG CANNOT SEE WHAT YOU FACED, WHETHER YOU WERE ON THE PLAY, OR WHY YOU LOST — and
  a PHONE GAME never reaches the desktop log at all** (`Player.log` is written by the
  install that played the match). Four hand-only columns fill that gap. **Which writer
  depends on whether Arena logged the match**: `--add` (`<deck> <W|L|D>` + `opp= why=
  play= note=`) for one it never saw; **`--annotate` (`<matchId> …`) for one it DID** —
  it joins on Arena's id and UPDATES, where `--add` would append a SECOND row, because a
  hand row has no matchId to dedupe on. `deck`/`result`/`date` are refused by `--annotate`;
  the log owns them. The **loss vocabulary is CLOSED so it can be COUNTED** (`flood screw
  slow answer removed keep misplay outclassed`) — free text cannot answer "which decks
  flood out". Validation is asymmetric: an unknown DECK or matchId is REFUSED (it would
  invent or silently skip a row), an unknown `why` is warned about and RECORDED. The
  dashboard's **"Log a match"** panel does both from a phone — the page is STATIC, so it
  queues in `localStorage` and hands back lines; it parses a pasted log only to LABEL
  rows, and emits only the id, so a misparse there cannot corrupt a stored W/L. [G-74]

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
  cue is still invisible — grade those from full text. The type-naming half is CLOSED
  (2026-08-20): a card whose text names a CARD TYPE it interacts with but never is —
  Gilgamesh digging for "Equipment cards" — now carries that tag via
  `_TYPE_MATTERS_RES`, 196 tags across 180 pool cards, nothing lost. A "what does this
  card look for" read still beats the tags for the fixer half.** [K-03]
- **Never gate a predicate on a derived TAG — it inherits every hole in the tagger.**
  `_is_color_fixer` did, so the roster's two best fixers (keying off unindexed Vivid) read
  as non-fixers and `suggest-homes` proposed cutting the BETTER fixer. Read TEXT, in
  mana/land-type context, and exclude reminder text. When a gate blocks a fix, check
  whether it encodes the intent or merely the old implementation. (Vivid has since been
  themed — which does not retire the rule, it demonstrates it: reading TEXT is what made
  the fixer overlay survive the keyword being unindexed, and will again.) **G-80 is this
  rule one layer over and the costliest instance:** `cuts`' fit term is gated on derived
  tags, so when the tagger read only the keywords a card HAS, a deck-31 engine piece
  scored fit 17 and was offered as a cut. The user caught it; no gate could. [K-04]
- **`pay life` is a tagged theme** (357 pool cards, 2.2% — specific enough to build
  around): YOU losing life as a cost, plus the cards that only CARE. "Each opponent loses
  2 life" is a DRAIN effect — the opposite card, deliberately not tagged. [K-05]
- **CHECK `MECHANIC_RULES` FOR THE NAME BEFORE ADDING A THEME.** `heist` (cast a card
  that was THEIRS) was first drafted as `theft`, a name already taken by the
  "gain control of" rule — reusing it silently UNIONED two mechanically unrelated effects
  and destroyed the specificity that makes an idf theme useful, **with `check_all` green
  throughout, because a tag collision breaks no invariant.** [K-06]
- **`exile cast` is the SIBLING of `heist` and stays separate** — casting your OWN exiled
  cards (impulse / Warp / Plot / Foretell / Adventure, 291 pool cards). The two only look
  alike; a deck built on one gets nothing from the other. [K-07]
- **`keyword_frequencies()` counts DISTINCT CARDS, not rows** — the mana file keys a DFC
  under its full `Front // Back` name, so a two-faced card could contribute two rows and
  clear the one-card noise floor without a second card existing. [K-08]
- **`tags_for` and `classify_roles` must agree on the same text.** Three phrases
  disagreed, each leaving a card with a blank Synergies cell and therefore invisible to
  every tag-based recommendation. **The 2026-08-19 instance runs the OTHER way and is
  worse, because nothing is blank**: Dead Weight is tagged `removal` by the tagger and
  scored ZERO roles by the classifier, so it was a removal card to one model and roleless
  to the other — and it is the ROLE model that feeds `tier_band` (BS6-10). Comparing the
  two is cheap, and is a GATE now, not a one-off: `check_roles.py --tags` sweeps the pool
  for it, baselined at 153 and soft in `check_all`. It reads the tagger's own
  `MECHANIC_RULES` live (never a copy) and excludes the deathtouch KEYWORD path by
  construction — 250 of the 388 raw hits, which an allowlist would have had to enumerate.
  A worklist, not a defect count. **Residual: 342 pool blanks —
  a long tail of un-themeable effects, and a new theme for four cards is not the fix.** [K-09]
- **After editing a tag pattern, regenerate BOTH derived tag stores** —
  `tag_synergies.py --merge` for the LIBRARY and **`build_pool.py --all` for the pool**,
  which re-derives every pool row's `Synergies` through the same `tags_for()`. Skipping
  the pool rebuild used to leave unowned craft candidates ranking on stale tags SILENTLY;
  since BS2-23 the pool's build stamp carries a content hash of the tagger AND (since
  BS4-37, narrowed by BS5-06) of `deck.ENGINE_THEMES`, which the tagger reads, so an edit to either
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
EIGHT further SOFT roster sweeps this list used to omit: wishlist target drift, the G-68
card-name-header staleness pass, the tier-mismatch pass, (2026-08-11) the `#~ note:`
figure sweep, (2026-08-19) the tag/role disagreement sweep (`check_roles --tags`) and
the committed-dashboard freshness check, and (2026-08-24) TWO more — the G-75
dead-library-search sweep (a tutor whose named resource the deck holds ZERO of) and the
G-79 unreleased-pool sweep (a card-pool row from a set that is not out yet, which every
craft recommender would price a wildcard for). Two things to know
before touching it: it imports `deck` as a MODULE and calls its MODEL functions (no
`cmd_*` at all), so it never
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
  (LIVE since 2026-08-10 — 72 matches, 69 attributed across 29 decks, pooled 37-35; the
  best per-deck row is n=8 against the 20-match floor, which is why `--report` also POOLS,
  and why the four HAND columns exist at all — G-74), recommendations.csv,
  collection-stamp.json (written only by `import_collection.py --apply` — the date owned
  counts were last EXACT; absent until the first run, and the craft surfaces say so) [C-02]
- Outcomes: scripts/parse_matches.py, recommendations.csv + `deck.py feedback` — the only
  subsystems that have seen a real game or a real decision [C-03]
- Ingest & Enrich: scripts/import_arena.py, scripts/import_collection.py,
  scripts/verify_ingest.py, scripts/enrich.py, scripts/tag_synergies.py,
  scripts/build_pool.py, scripts/build_mana.py, scripts/reconcile_crafts.py,
  scripts/sheets_sync.py, scripts/scryfall.py, scripts/lib.py [C-04]
- Analysis: scripts/deck.py, scripts/query.py, scripts/card.py, scripts/pool.py,
  scripts/wishlist.py, scripts/validate.py, scripts/check_all.py + the thirteen
  `check_*.py` gates, scripts/keyword_baseline.txt, scripts/role_baseline.txt,
  scripts/tag_role_baseline.txt, **.github/workflows/integrity.yml** — the zero-dependency
  CI half: `check_all.py` plus the `--help` CLI smoke step that exists because check_all
  builds no argparse tree (G-55). Named here since 2026-08-26; it had lived only in
  `docs/cycle-config.md` prose, so the file list said CI ran pytest and nothing else [C-05]
- Presentation: scripts/build_gallery.py, gallery.html, image-manifest.json,
  scripts/build_dashboard.py, dashboard.html, .github/workflows/pages.yml,
  scripts/app.py, templates/, Makefile [C-06]
- Testing: tests/ (31 test files + conftest: the markup-contract, CLI-entry-point and
  command-output, analysis-model, gate-pinning, shared-primitive and ingest layers, the
  2026-08 ingest-writer / sync-guard / resilience-layer / CLI-filter coverage of the
  formerly untested scripts, plus test_check_all.py, the gate runner's own mutation layer;
  test_app_editor.py, the editor's write-safety pins (importorskip'd on Flask);
  test_check_dfc.py, which pins the G-63 builder SCAN rather than the registry it
  feeds; test_writer_mutations.py, which runs each write-safety property against a
  mutant writer so the property is proven load-bearing; and test_gates_fire.py, the
  watched-it-fail layer for the seven gates that had none — so all fourteen now have
  one; and test_dashboard_js.py, the CROSS-LANGUAGE layer running the dashboard's JS
  matcher under Node against `match_paste`), requirements-dev.txt + requirements-app.txt
  (CI installs BOTH, and sets PYTEST_NO_SKIPS so a skip FAILS — installing only -dev
  silently skipped the editor's six write-safety pins on every run),
  pytest.ini, .github/workflows/tests.yml, + test_templates.py's TOKEN gate (a GENERATED
  page must define every `var(--x)` it emits — G-72 one file over) [C-07]
- Decks: decks/

**Invariant Library:**
- INV-01 | card-library.csv has the canonical 8-column header, every row has 8 fields, no duplicate (Card Name, Set Code, Collector #) printing, and Quantity Owned is blank or a non-negative integer | Subsystem: Data | Verify: scripts/check_all.py (via validate.py)
- INV-02 | Every Card Name in card-library.csv has a row in card-mana.csv | Subsystem: Data | Verify: scripts/check_all.py
- INV-03 | Derived reference files exist AND keep their own schema: card-mana.csv (Card Name/Mana Cost/Mana Value/Keywords), card-pool.csv (…/Rarity; Legalities+Released+Power+Toughness warn if absent), gallery.html AND dashboard.html (each has usable CONTENT — non-trivial size + the `#data` island — since existence alone passed a truncated build) | Subsystem: Data/Presentation | Verify: scripts/check_all.py
- INV-04 | Every deck file under decks/ parses with no malformed card lines, AND every line's `(SET)` code exists in the pool or library (an unheld COLLECTOR # within a real set is a soft warning, since the pool keys one printing per card), AND the roster's ids are unambiguous — no two files claim one deck id, and no top-level decks/ directory is variant-shaped (`73a-…`), both of which let a by-id command silently validate one file while editing another | Subsystem: Decks | Verify: scripts/check_all.py
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
     - Still in light mode, open a two-or-three-colour DECK: the Stats tab's "Color
       identity" bars and the Mana tab's "Strict color requirements" pip bars
     - Then `gallery.html` in a LIGHT OS scheme (it has no toggle — it follows the OS):
       the "Collection overview" bar tracks, each colour bar, and a card's ×N badge /
       set-code label
   Expected: green/amber/red read clearly against the LIGHT panel background, are
   distinguishable from each other and from body text, AND each pill still reads as a
   bounded CHIP — a visible fill and border, not a loose coloured word. The TEXT moved
   onto `var(--ok)` / `var(--warn)` / `var(--bad)` at I-03; the FILLS and BORDERS
   followed at S-9, via `color-mix` off the same tokens (they had been dark-tuned
   literals whose ~1.3:1 edge disappeared over a white panel). A washed-out pill means
   one regressed back off the tokens. **The gallery leg is NEW and its palette has never
   been rendered by anyone**: the bar tracks must read as a light neutral (`--track`, not
   the `#0f1115` literal they carried until BS5-10), every colour bar must be visible
   against that track (`--W…--C` are mid-tone in light mode — the dark pastels vanish on
   it), and the ×N / set-code plates stay deliberately DARK because they sit on card ART,
   so check their ink is still light-on-dark rather than dark-on-dark. **The DECK-tab leg
   is the same bug one file over** (BS6-02): the dashboard's `--W…--Cc` had no light value
   at all while their bar track flips near-white, so those two panels painted cream on
   white. Both pages now use the SAME mid-tone values — if one looks right and the other
   does not, one of them drifted off the shared set.
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
   quick-filter pill, a roster-table sort header, **a Triage row's DECK NAME and a Card
   finder CHIP** (both mouse-only until BS5-02/03), a section header (collapse it with
   Enter or Space) and a deck's ⤢ opener; open the modal, Tab through it, press Escape.
   On a deck card's tab strip try ← / →, then check the card image appears on focus at
   **ALL THREE** preview surfaces — a wishlist card NAME, a card name in the roster
   CRAFT-PLAN table, and a card in the IMPACT grid ("cards that advance the most decks");
   re-Tab to the craft table after clicking a sort header. Then the EDITOR (`make app`, `templates/collection.html`) colour
   pips, and the DECK editor's (`templates/deck.html`) Analysis tab strip; remove a card
   line with its ✕ and watch where focus lands.
   Expected: every control reachable with a VISIBLE focus ring; Enter and Space both
   activate; ← / → move along a tab strip (S-2 made them real tablists); the card
   preview follows FOCUS, not just the mouse, **at all three surfaces — this step used to
   name only the wishlist one, which is the single site where it worked, so the walk passed
   over a feature inert at the other two for months (S-7, fixed BS6-03)**; removing a row leaves focus on the
   next row's ✕, never on `<body>` (S-6); Tab inside the modal never reaches the page
   behind; Escape returns focus to the ⤢ that opened it. The Triage deck name and the
   Card finder chip must BOTH filter the deck list on Enter AND on Space, and the Triage
   one must survive a SORT click (its a11y is applied per-redraw, so sorting and re-Tabbing
   is the real test). **Walk it once in each OS
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
9. Log a session of matches | Subsystem: Outcomes
   Needs **a person with a real `Player.log`** — check_all never touches
   `parse_matches.py`, and its pytest layer runs against synthetic fixtures, so the
   end-to-end path is covered by nobody else.
   Steps: paste (or `cat`) an archive → `parse_matches.py <file>` (dry run) →
   `--apply` → `--report`; then rename a deck in the Arena client, play once, and
   re-run. Then the HAND path, which no log can exercise: `make log-match DECK=<id>
   R=L WHY=flood` (dry run, then `APPLY=1`), and the dashboard's "Log a match" panel
   on a PHONE — queue two matches, reload the page, confirm the queue survived, copy
   the block and feed it to `--add`.
   Expected: the dry run prints a `Deck attribution` block naming every Arena deck and
   the ROUTE that resolved it; re-running is idempotent (dedup by matchId); the rename
   re-maps in the SAME run, because header sync precedes the mapping. A match whose
   deck selection is missing stays blank rather than borrowing a neighbour's, and
   `--report` refuses a percentage under 20 matches. Full steps + the launchd archive
   setup: `.claude/commands/log-matches.md`. [C-12]
10. Log-a-match panel — selected state and focus ring | Subsystem: Presentation & Interface
    Steps: open `dashboard.html`, expand "Log a match" (starts collapsed); click W, L, D
    and then Play / Draw; Tab into the Deck select, the Opponent input, each segment
    button and a queued row's ✕; repeat in the other theme (press `t`).
    Expected: the selected segment has a visible tinted FILL and an accent border, clearly
    distinct from its neighbours — not just a colour change in the label. Field labels
    (DECK, RESULT, ON THE, …) read as muted against the value. Every focus ring is the
    accent purple used elsewhere, and the ✕ ring is accent, **NOT red**. A fill-less "on"
    segment or a red ring means the panel regressed off the shared tokens. **This palette
    has never been rendered by a person with the tokens correct** — the panel was built
    against token names that did not exist (`--acc`, `--dim`, `--fg` for `--accent`,
    `--ink2`, `--ink`), so every one of them silently fell back to the browser default;
    `tests/test_templates.py` now fails the build on an undefined token, but what the
    corrected palette LOOKS like is perceptual and unverified.
11. Log-a-match end to end on a phone | Subsystem: Presentation & Interface / Outcomes
    Steps: at 390×844 queue two matches with different decks, a `why` and a note; RELOAD;
    confirm the queue survived; Copy all; feed the block to `parse_matches.py --add`
    (dry run, then `APPLY=1`); then `--report`.
    Expected: no sideways body scroll, one column, the queue survives the reload; Copy all
    either copies or focuses-and-selects the textarea with the "Select-and-copy the box
    below" toast (a `file://` open is not a secure context, so the fallback is the
    EXPECTED path, not a failure); `--report`'s manual-axis section shows a non-empty Loss
    Reason tally for the first time. The four hand-only columns (G-74) are empty in all 66
    rows today, so this scenario is the only thing that can prove the loop closes at all.

**Frozen Subsystems:** none.

**Deploy Command:** Data + local tooling ship by commit/push (no build/release step). The
one deployed artifact is the roster **dashboard**, and since 2026-08-24 the workflow
INSPECTS the page it is about to publish (non-trivial size + the `#data` island, the same
two facts INV-03 checks on the committed copy) — nothing looked at it before:
`.github/workflows/pages.yml` rebuilds
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
Arena's `Player.log` into `matches.csv` via `parse_matches.py`, reconcile deck names with
`--sync-names`, then read the record with the restraint it needs — see G-57/G-73 below), and `apply-changes` (apply confirmed
swaps, run the F10 quality guard, re-ground the `#: tier:` prose via
`--audit-rationale`, verify + commit) **orchestrate the scripts, never
re-implement them** — the scripts stay the single source of truth so the skills
can't drift. `add-cards` is the OWNED-card counterpart to `add-wishlist`'s unowned
craft-target intake. **Every skill that WRITES ends with the shared verify+commit tail
in `docs/verify-commit-tail.md`** (check_all-first, the Co-Authored-By/Claude-Session
trailer, no model ID, branch-restart on a merged PR, and closing what it closed in
`.cycle/NEXT-SESSION.md`) — edit that one file to change the commit discipline for all.
**That sentence said "All" for a year and it covered 5 of 12** (2026-08-25 skill sweep):
`/ingest` and `/refresh` rewrite `card-library.csv` and every derived file and had NO
commit step at all — an ingest simply ended at its report and left the repo dirty —
while `/add-deck` carried its own one-line commit instruction and so inherited none of
the four rules. All three cite the tail now. `/add-cards` is the one that legitimately
does not: it writes nothing (it proposes; `/apply-changes` applies), and naming it here
as a tail-user was the claim that made the real gaps invisible. The tail's own header
lists the current writers — **add a new writing skill to that list and cite the file
from the skill in the same change**, since a skill only follows it if it SAYS so.

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
  **THREE are live as of 2026-08-19** — read them before re-deriving their findings:
  `prune-analysis.md` (the roster-wide prune shortlist for Arena's 100-deck cap:
  card-overlap matrix + `similar` sweep + a three-tier candidate list, awaiting the
  user's keep/cut calls); `wylie-tap-analysis.md` (Variant B, the mono-W tap-down
  control build, still specced-but-undrafted; Variant C parked); and
  `hob-followup-analysis.md`. Each is deleted when its work lands — the 54-family doc
  went on 2026-08-05, which is the contract working as intended.
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
- **`docs/tooling-improvement-plan.md` — DELETED 2026-08-12**, and the reasoning is
  worth keeping for the next document like it. Findings F01–F15 had all landed cycles
  earlier, nothing referenced it, and one instruction had gone WRONG (F01 specified
  adding `lib.full_card_text()`, which was added, never acquired a caller, and was
  deleted as dead code). A status header saying "historical, do not follow" was tried
  first and is not enough: the file still read like a plan to anything that grepped it,
  which is exactly how a fresh session finds things. **A completed plan is not a
  record** — the record is `.cycle/blocks/`, which is per-run, dated and consumed by
  the workflow commands. Git holds the file if it is ever wanted.
