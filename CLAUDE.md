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
- **Parse a `Color(s)` cell with `lib.card_colors()`, never inline.** The naive
  `{ch for ch in s.upper() if ch in "WUBRG"}` reads the literal string `"Colorless"`
  as `{R}` (the word contains an R), so a colorless card was mis-routed as red by
  `suggest`/`suggest-homes`/fingerprints; a `.replace(" ", "")` variant kept the `/`
  and broke gold cards (audit F1/F2). `card_colors()` handles both — route every new
  color-parse site through it. `scripts/check_colors.py` (a hard `check_all` gate,
  like `check_rankings`) locks this in: a colorless card must not read as colored,
  AND a static AST scan fails the build if any script re-implements the naive
  `{x for x in … if x in "WUBRG"}` idiom instead of `card_colors()` — the coverage
  gap that once let the bug regress into `wishlist.py`/`app.py` undetected.
- **Write canonical files through `lib.atomic_write()` (+ `lib.backup_path()`).**
  Every mutation of `card-library.csv` / `card-mana.csv` / `card-pool.csv` /
  `card-wishlist.csv` goes temp-file → timestamped `.bak` → atomic `os.replace`, so
  an interrupted or empty-result write can't truncate the source of truth (audit
  F3/F5). `.bak` names come from one collision-free, sort-safe helper so "newest"
  is unambiguous (audit F22); readers that need the latest (e.g. `app.py revert`)
  select by mtime. Pass `backup=False` only when writing a scratch temp the caller
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
  columns. **To refresh a derived file, use its own builder** — `build_pool.py --all`
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
  see those), so it **under-rates by design.**
- **The floor is ARCHETYPE-aware** (#4): an aggro deck closes on a fast clock, not an
  interaction suite, so for an **aggro** plan a bounded `_clock_score` (low curve +
  cheap threats + reach, 0–7) SUBSTITUTES for the interaction the resilience floor
  demands — a fast burn deck isn't floored at C for light removal. Every other plan
  (midrange / control / combo) keeps the exact interaction+card-advantage floor
  (clock 0), so nothing else regrades. The plan comes from an explicit **`#: plan:
  aggro|control|combo|midrange`** header, else keywords in `#: archetype:`, else a
  strict metric inference (default midrange). `deck.py tier` prints the plan + clock.
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
  floor). A roster pass is a **soft, non-gating** `check_all` warning, so an
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
  is NOT "it's Standard-legal." **In code, never slice a card's text to
  grade/classify/rank it** — the rule holds today because every evaluator reads a
  whole `Card Text` cell off `load_card_data()` (library→pool) or a pool row, and
  truncation appears only in DISPLAY (a first-line preview in a filler list).
  `load_card_data()` is the ONE name→card accessor; a `lib.full_card_text()` was once
  added as a dedicated funnel but never acquired a caller (every evaluator already
  holds a carddata dict, and a second cache of the same column is worse than one), so
  it was removed rather than left as dead code the docs pointed at (broad-scan F-07).
  Note `load_card_data` resolves library-first, so a library row with BLANK text would
  shadow a populated pool row — harmless today (all 6 blank-text rows are genuinely
  vanilla in both files) but the thing to check if an evaluator ever reads a card as
  text-less.
- **A split / Room / Adventure card's stored cost covers BOTH halves — read the FRONT
  face.** Scryfall joins them with `" // "` (Funeral Room is `{2}{B} // {6}{B}{B}`), and
  you never pay both, so reading the merged string over-counts pips for all 292 such
  cards in the pool and 15 across the roster. Worse, a split/Room card's *rules* mana
  value is the COMBINED total — which is correct and useless: Funeral Room came through
  at **MV 11**, inflating deck 42a's curve and making `consistency` read it as a
  `{B}{B}{B}` turn-5 play when the door that deck casts is `{2}{B}`, one black pip on
  turn 3. **`lib.front_face_cost()`** takes the castable half and **`lib.mana_value()`**
  computes MV from one face; `parse_pips` reads the front face and `load_mana`
  recomputes MV whenever the cost contains `" // "`. FRONT is the convention, matching
  `owned_qty`'s DFC rule — the creature on an Adventure card, the cheap door on a Room —
  and Adventure cards already stored the front-face value, so recomputing AGREES with
  them and only corrects the split/Room shape. Roster diff when this landed: 18 of 59
  decks changed, **every one downward**. Residual: a deck that plays a split card mainly
  for its BACK half reads cheaper than it plays; grade that from the printed card.
- **Don't judge a card by printed mana value or a single subtype.** `deck.py
  stats` flags cost flexibility (`◊` cheaper / `△` added cost), buckets spells
  into functional roles (removal / card advantage / ramp / …, heuristic from
  oracle text), and `deck.py tribes` reads oracle text for cross-type synergies
  (e.g. a Serpent feeding a Leviathan payoff). `deck.py mana` / `check` also run
  a castability lint against the deck's declared `#: colors:`. Read the card text
  (stored in the CSV) for real evaluation.
- **A `#~` flex line rots SILENTLY — `deck.flex_staleness()` is the check.**
  `swap --apply` retires only the lines invalidated by the swap it is PERFORMING, and
  `--audit-rationale` reads `#: tier:` / `#: archetype:` prose and never the flex block,
  so a line can sit for rounds proposing a cut that already happened. Surfaced by
  `deck.py flex <id>` and as a soft `check_all` warning; it found FIVE on its first run
  (decks 6, 7, 9 and 38a ×2). Note two of those were **obsolete rather than mis-aimed** —
  38a's "add a 2nd protection piece" was written when protection was thin and `stats` now
  counts six — so the fix is sometimes to RETIRE the line, not retarget it. Advisory: a
  flex line is a human note, so this never edits one.
- **A swap inherits the cut card's `# section` comment.** The add takes the cut's line
  slot, so it lands under whatever header preceded it — which is how a counter battery
  (Broodguard Elite) ended up filed under `# Card advantage`, the section Kiora had
  occupied. Harmless to the tooling, but the file then lies to the next reader, and these
  files are read far more often than they're parsed. `swap --apply` now warns via
  `section_mismatch`. Only UNAMBIGUOUS headers are checked — "Counter DOUBLERS" means
  +1/+1 counters, not counterspells, and "Threats"/"Payoff"/"Creatures" are too broad to
  contradict — and a card the classifier gave NO role gets softer "verify" wording rather
  than a mismatch claim, since a no-role read usually means a lexicon gap, not a weak card.
  Advisory: it never moves the line, because that's a human editorial call.
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
  illegal / uncastable), **craft** (unbuilt), **review** (soft: an off-color ABILITY
  or thin interaction), or **ok**. `--flagged` drops the ok rows. Each deck also
  carries a competitive **`Tier`** (S/A/B/C/D win-capability) read from its `#:
  tier:` header — shown as a column and sortable with `deck.py audit --by-tier`
  (and a color-coded pill on the dashboard). The dashboard opens
  with the same scorecard as a sortable **Roster-triage** table (both render from a
  shared `audit_deck()` scorer, so CLI and page can't drift). It's a SHORTLIST
  SIGNAL like `suggest`/`cuts`: a flag says "look here," then grade the flagged deck
  from `deck.py text` + `/tune-deck` — a review/ok label is not a verdict on the
  deck. (A stale `#: colors:` header inflates the `Cast` column — a deck whose header is
  narrower than the colors it actually casts shows spurious "uncastable" rows; fixing the
  header to the deck's real castable colors clears it, same as it does for `mana`/`check`.)
  **The `review` verdict counts only an off-color ABILITY, never a hybrid you pay
  on-color** — `_castability` returns `off_ability` as a subset of `off_identity`, and
  `audit_deck` reads the subset. Counting every identity stray had saturated the flag:
  it fired on 22 of 63 decks, and on ALL 26 flagged decks every flagged card's strict
  pips were inside the declared colors, i.e. a measured 0% actionable rate (broad-scan
  F-03). Knight's Edge is mono-W and runs two R/W hybrids that are simply white cards
  there; Super-Skrull casts for `{1}{B}{B}{B}` but its `{4}{R}` ability is dead in a
  deck with no red, and only the second is worth a look. Roster impact: review 22 → 6,
  ok 22 → 38. Nothing became invisible — the `Cast` column still shows every stray as
  `Ns` (matching `deck.py mana`) and marks the actionable subset `Na`, so the column
  says WHY a deck did or didn't reach the verdict. Same saturation shape as audit F-04's
  `Decks` column: a flag that always fires reads as working.
- **Stored decks drift from the real Arena decks.** The user edits decks in the Arena
  app; the repo only updates when someone writes the deck file, so the two silently
  diverge (hit this session: deck `12` had been changed to 2× Super Intelligence / −Futurist
  Forge in Arena while the repo still showed the old list). Catch it with **`deck.py verify
  <id>`** (pipe/paste an Arena export — reports *identical* or a `+/−` diff, printing- and
  basic-fungible) or the dashboard's **"Check for stale decks"** panel (paste one or many
  `Deck` blocks; it auto-matches each to its closest stored deck — variants included — and
  flags the drifted ones). **Then repair it with `deck.py sync`** — the WRITE half of
  `verify`: pipe or pass an export containing ONE OR MANY `Deck` blocks and it matches each
  to its closest stored deck (same rule as the dashboard panel) and rewrites the drifted
  files to match. That "same rule" is now PINNED by tests rather than asserted in a
  docstring: the JS copy had drifted on the TIE-BREAK, comparing drift alone with a strict
  `<` so an equal-drift tie went to whichever deck came first in iteration order, while
  Python preferred more shared cards then the lower id — same paste, two answers, in
  exactly the sibling-variant case the low-confidence flag exists for (broad-scan F-08).
  Both now sort by `(drift asc, shared desc, id asc)`, and the JS uses `<`/`>` on the id
  rather than `localeCompare`, because Python compares CODEPOINTS and locale collation can
  ignore the hyphen in an id like `3-brawl`. Dry-run by default; `--apply` writes each with a `.bak` and the INV-04
  re-check. Line-level editing, so an existing card keeps its printing and section position
  and only its QUANTITY changes, dropped cards lose their line, new cards are appended after
  the last card line, and the `#:` header / `# Creatures` comments / `#~` flex lines all
  survive. A block matching two variants nearly equally is reported LOW CONFIDENCE and
  SKIPPED on `--apply` (rewriting the wrong sibling is the one expensive mistake here) —
  re-paste that deck alone, or pass `--force`. Previously the only repair was reading a diff
  and hand-editing each file.
- **Legality lint and cut candidates are separate from ownership.** `deck.py check`
  answers "do I own this deck"; `deck.py legal <id>` answers "is it a *legal* deck"
  — size vs the format minimum, the copy limit (4, or 1 in singleton formats), and
  each nonbasic's legality in the deck's `#: format:` (from the pool's `Legalities`
  column; `--format` overrides). It exits non-zero on a real violation but treats a
  pool-absent card as *unverified*, not illegal (so WIP/older-print decks aren't
  false-flagged). It's **format-aware for Alchemy and Brawl**: a Standard card that
  isn't Alchemy-legal is *rebalanced* (plays as its `A-` version), so `--format alchemy`
  notes it rather than flagging it illegal; and a **Brawl/Commander** deck (a singleton
  format) enforces the 1-of limit AND validates the `#: commander:` header — it must be
  a legendary creature/planeswalker in the deck, and every card's **color identity** must
  sit within the commander's (Brawl's defining rule, which is stricter than Standard's
  castability check — a `W/R`-identity card is fine in a mono-W Standard deck but illegal
  under a mono-W commander). Game-type variants are organized as `<core>-<format>` decks
  (e.g. `3-brawl`) — see `decks/README.md`. **`deck.py brawl`** is the roster-wide
  counterpart: it ranks every deck by *distance to a legal Brawl conversion* (duplicates
  to trim to singleton + cards outside the best in-deck commander's color identity) and
  names that commander, so you can see which decks convert cleanest — a shortlist like
  `audit`/`rotation`, marking cores that already have a `*-brawl` variant. `deck.py cuts <id>` is the counterpart to `suggest` (adds): it
  ranks nonland cards weakest-fit first (central-theme fit + **impact-weighted**
  functional role + tribal contribution) **and prints the full oracle text of the top
  candidates plus a `⚠ context` flag on deck-dependent mechanics (converge / devotion /
  affinity / X-cost) and a `⚠interaction` tag on removal/counter/sweeper rows showing
  the deck's interaction count (with a header warning when the deck runs <5)** — so the
  shortlist never silently lists the interaction you deliberately tuned in as
  "weakest" (a recurring mis-read: Shock / Spell Pierce sorting to the top of a
  freshly-firmed removal suite). A card on the deck's `#: protect:` **signature theme
  also gets a keep-boost**, so a generic-tagged-but-central theme (e.g. counters in a
  deck that protects counter-doublers) isn't mistaken for filler. This is because the
  role/fit line is a SHORTLIST SIGNAL, NOT A GRADE: its classifier can miss what a
  card does and can't see spice/signature cards. (Role credit is now impact-weighted — removal / card advantage / ramp /
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
  stored under its **front** name), adds the matching `card-mana.csv` row — a
  **blank** one when the card has no source mana row yet, so INV-02 always holds
  and `build_mana.py`/`/refresh` fills the cost later (audit F8) — drops it
  from `card-wishlist.csv`, and lists the decks to re-check. For a card already in
  the library it takes `max(existing, line)` so a deck-dump slice can't drop a real
  count (`--set-exact` forces the exact/lower value, audit F17); unparseable lines
  are reported, not skipped silently. Dry-run by default; `--apply` writes with
  `.bak`s; then run `build_gallery.py` + `check_all.py` (or `/refresh`). (The DFC front-vs-full name handling — pool/mana key `A // B`, the
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
- **Regenerate derived data with `make refresh` — never by hand.** The order is a real
  dependency graph (`build_pool.py` is independent, taking keywords straight off the
  Scryfall response; `build_mana.py --pool` READS `card-pool.csv`; `tag_synergies.py`
  reads `card-mana.csv`'s keywords; `build_gallery.py` last), and it had been written out
  in **eleven** places — this line, Regression Scenario 1, `/refresh`, `/ingest`,
  `/add-cards`, and printed or docstring'd copies inside `import_arena.py` (×2),
  `import_collection.py` (×2) and `reconcile_crafts.py` — of which only `/refresh` had it
  right. The rest put `build_pool.py` AFTER `build_mana.py`, `/ingest` claimed it matched
  `/refresh` while contradicting it, and `import_arena.py`'s docstring asserted "IN THIS
  ORDER" over the wrong one. The first sweep found four and fixed five; the copies inside
  SCRIPTS survived it, which is the worse half — a stale doc misleads a reader, a printed
  recipe is an instruction someone follows. `tests/test_verify_ingest.py` now fails the
  build on any new copy (`_restates_chain`, which distinguishes a RECIPE — both builders
  as adjacent invocations or an arrow chain — from the many legitimate one-tool mentions
  like "built by build_mana.py", because a check that flagged those would be deleted). Getting
  it wrong is QUIET: a newly released set's pool cards get no `card-mana.csv` row until
  the next cycle, so they rank with no cost and no keyword tags, and no invariant notices
  (INV-02 covers the LIBRARY, not the pool). The Makefile target is now the one
  executable definition; the correct order is `enrich` → `build_pool --all` →
  `build_mana --pool` → `tag_synergies --merge` → `build_gallery` → `check_all`. Use **`--merge`** (adds
  newly-derived tags without removing existing/hand-curated ones), not `--force`,
  which REPLACES every cell and clobbers hand edits (audit F10). `tag_synergies`
  also warns when `card-mana.csv` is older than the library — rebuild it first or
  new cards get keyword-less tags (audit F21).
- **Scryfall egress**: needs `api.scryfall.com` + `*.scryfall.io` allowed; some
  managed environments block it. Enrichment/pool/mana builds require it. All
  Scryfall access now goes through **`scripts/scryfall.py`** (a shared, resilient
  client): a slow/flaky Scryfall — read-timeout, 5xx, or a truncated body, none of
  which are `URLError` subclasses — maps to `ScryfallUnavailable` (transient) and a
  real 404 to `NotFound`, so the **interactive tools degrade instead of crashing**:
  `deck.py mana/stats/wildcards/swap` show `?`/unknown, `build_gallery.py` flags
  missing art and exits non-zero (instead of reporting an imageless gallery as
  success), `wishlist.py --add` marks rows added name-only-due-to-outage
  distinctly from a genuine no-match, and the editor's `/api/add` returns an
  `enrich_status` of `ok`/`miss`/`offline` instead of 500-ing — it used to hand-roll
  its own urllib call catching only `URLError`, so a READ timeout (a `TimeoutError`,
  which is NOT a URLError subclass) escaped and crashed the request (audit F-09).
  **Every** Scryfall call goes through the shared client; a new one that doesn't will
  hit this same class of bug. The rebuild scripts (`enrich.py` /
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
- **`card-pool.csv` carries printed `Power` / `Toughness`** (front face for a DFC), so
  "power N or greater" conditions are gradeable at last. Nothing stored P/T before, which
  left a whole class of card unanswerable by ANY tool — Garruk's Uprising's "whenever a
  creature you control with power 4 or greater enters", Doran-style toughness-matters
  payoffs, every "power 4+" condition — and it produced a real mis-read: **Mossborn Hydra
  looks like a big body but is printed 0/0** and enters with a single counter, so it does
  NOT trigger Garruk on entry. Values are stored RAW and parsed by **`lib.card_power()`**,
  which returns `None` for the 91 pool cards printed `*` / `1+*` / `X` rather than
  inventing a number — never `int()` the column yourself, and note `card_power(0)` is a
  real 0 (every X-creature is 0/0), which is why the helper can't use `value or ""`.
  `load_card_data()` exposes `power`/`toughness` and **backfills them from the pool onto
  library rows**, since the library CSV has no such columns and is read first — without
  that, exactly the cards you OWN would read as unknown. `deck.py stats` uses it for a
  **power-threshold check**: a payoff keying on "power N+" is flagged when few of the
  deck's creatures meet the bar on PRINTED stats (40a: Garruk's Uprising sees 2 of 23).
  A creature that GROWS after it enters still won't satisfy an ENTERS trigger, so printed
  stats are the correct and conservative read. Rebuild via `build_pool.py --all`; INV-03
  treats the columns as OPTIONAL so a pool built before them still passes.
  **The flag is SCOPED, because counting your own creatures is only the right question for
  some "power N+" clauses — 16 of the roster's 27 flags (59%) were false in two shapes.**
  (1) REMOVAL / opponent-facing (83 pool cards): "Destroy target creature with power 4 or
  greater" (Sandbenders' Storm, Battle Menu, Valorous Stance) measures the WRONG BOARD —
  the card wants THEIR creatures big — and for a sweeper like Dusk, few of your own
  qualifying is the entire point, so the warning inverted the card. (2) **"TOTAL power N
  or greater"** (153 pool cards, the bigger cause and one nobody reported): teamwork's
  "tap any number of creatures you control with total power 4 or more" and Betor's "if
  creatures you control have total toughness 10 or greater" are SUMS — three 2/2s satisfy
  "total power 4" — so counting bodies at printed power ≥4 is the wrong ARITHMETIC, not a
  conservative read of the right one. Deck 34 was told 0 of its 19 creatures could pay a
  cost it pays trivially. `_POWER_SCOPE_MINE_RE` opts IN on "you control" rather than
  blacklisting the bad shapes, because Magic's templating puts "you control" directly
  before "with power N" and an affirmative test can't be widened by a phrasing nobody has
  written yet; the cost is losing a scope spelled another way (Gwenna's "whenever you cast
  a creature spell with power 5 or greater"), which is the right direction to err on a
  list that exists to be read card-by-card. Found by asking why deck 13's earthbend deck
  was flagged for a removal spell — then the pool survey turned up the larger `total`
  family that the single reported case never hinted at.
- **`card-wishlist.csv` records Power PROVENANCE** in a `Power Source` column
  (`seed` / `hand` / `unknown`). `--add` and `--seed-power` both write a heuristic
  estimate into the same cell a hand grade goes in, so nothing could tell an auto-seed
  from a human judgment — which forced "verify this number" onto every row including the
  graded ones. `wishlist.power_is_seeded()` treats `seed`, `unknown` and blank as
  untrusted. **`unknown` is a deliberate third value:** rows predating the column were
  mostly auto-seeds but some were hand-graded, so defaulting either way would be wrong in
  one direction. Set `Power Source=hand` when you grade one.
- **`card-pool.csv` now holds the full Arena pool** (`build_pool.py --all`,
  ~15.8k cards) and **`card-mana.csv` covers it** (`build_mana.py --pool`), so
  unowned cards have real costs/tags. Both tools DEFAULT to the smaller scope
  (Standard pool / library-only mana), so a plain rebuild would SHRINK coverage back —
  pass `--all` / `--pool` (as `/refresh` does) to keep full coverage. **Both now REFUSE
  a >50% shrink** (`--allow-shrink` to force): `build_pool.py` always did, and
  `build_mana.py` gained the same guard after the file was found at 1,695 rows against a
  15,850-card pool — this exact mistake, which had also silently disabled the one-card
  keyword heuristic that needs a pool-sized corpus. The full-pool mana build is slow
  (Scryfall rate limits ~15.9k cards, plus a front-face pass); the pool build itself is
  fast (paginated search, ~90 requests). `build_mana.py` falls back to a **front-face
  `/cards/named` lookup** for names the batch endpoint won't match — SPLIT and room cards
  (`Life // Death`), ~630 of them — and accepts the result only when the resolved card IS
  the one asked for, since a bare front name can be a different card and a wrong cost is
  worse than a blank one.
- **`card-wishlist.csv` is UNOWNED craft targets**, separate from the owned library
  and the full pool. `wishlist.py --add <arena-export>` appends a batch, enriching
  each card (Rarity/Color/Type/text/Synergies) from `card-pool.csv` with a Scryfall
  fallback — double-faced cards are stored under their **full `Front // Back` name**
  (matching the pool) so joins work, unlike the library's front-name convention.
  `--by-set` is the pack/gem-optimization view (wishlist cards per set by rarity);
  `--budget "9M 10R 38U 48C"` turns a wildcard budget into an optimal craft plan
  (top `combined` per rarity cap + alternates + an import block — optimal because Arena
  wildcards are strictly per-rarity, so the problem separates and top-K per rarity IS
  the answer). **`--budget` is the SPEND view, so every check `--rank` runs has to
  appear here too** — it was computing each pick's `rot` flag in `_rank_scores` and then
  discarding it at print time, so a 3-slot uncommon budget came back with TWO cards
  leaving Standard and no warning. Same shape as the `suggest --lands` legality bug: the
  recommender that actually costs you resources was the one missing the check.
  **The filter flags (`--set`/`--rarity`/`--color`/…) now apply to `--rank`/`--budget`/
  `--by-set`**, which previously dropped them silently — `--budget "3R" --set TMT`
  planned against the whole wishlist and returned FIN cards. The maintenance commands
  (`--suggest-targets`/`--audit-targets`/`--seed-power`) deliberately keep the FULL list,
  since auditing a filtered subset would report "clean" while leaving the rest unchecked.
  A filtered view is **normalized against the whole wishlist** (`_rank_scores(rows,
  keep=…)` scores everything, then filters): `fitN` is `pri` scaled to the max in the
  scored set while `power` is not rescaled, so scoring only the subset inflates fit
  relative to power and can genuinely reorder the picks — the normalization denominator
  is a property of the CORPUS, not of the view. `--seed-power`
  first-passes BLANK `Power` cells with a heuristic estimate (rarity floor + roles;
  review it — the classifier undersells bombs); `--owned` flags cards you've since
  crafted so you can prune them (or feed them to `reconcile_crafts.py`). `--add`
  marks a **CONDITIONAL power** as `pow~` in `--rank`: a rarity+role seed grades a card in
  ISOLATION and structurally cannot price one that scales with YOUR deck (X-cost, kicker,
  exhaust, warp, landfall, "equal to …", "for each … you control"). Every Power that needed
  hand-correcting in practice was this class — Repulsive Mutation seeded near-zero though
  its counter is unconditional once the threat is big, Mona Lisa at 2.5 though she's a
  3-mana rock that taps for 3, Procrastinate at 1.0 though twice-X stun counters lock a
  creature for four untaps. The flag fires **even when Power is filled**, because the CSV
  records no PROVENANCE — a value may be a `--add` auto-seed rather than a hand grade. It
  says "verify from text", not "wrong". `--add`
  **auto-seeds a heuristic `Power`** on the newly-appended rows (so a fresh card
  never ranks at a 0.0 blank — the Elf engine and the Dino/Enchantress batches each
  sank until graded; review the estimate and hand-adjust the bombs). `--audit-targets`
  flags any card whose **Target deck can no longer cast it** (color/theme drift after
  a retune — e.g. Neriv orphaned when deck 14 went Mardu→Rakdos) or has blank Power;
  it's also folded into `check_all` as a **soft, non-gating warning**. The castability
  check is **hybrid-aware** (`_pips_castable`, unit-tested): it reads the card's mana
  cost and treats a hybrid pip as payable by either color, so a `{W/U}` card (Sun-Spider)
  isn't false-flagged as off-color in a W/B deck — matching deck.py's own castability
  lint rather than the raw color-identity subset. `--rank` shows
  a **`state`** column (target deck's tier·remaining-crafts, ★ = this card helps
  *finish* a near-complete deck) so "upgrade a BUILT deck" reads apart from "build an
  UNBUILT one" — the strategic overlay the raw score can't show. `--rank` and
  `--budget` **exclude cards you already own** (DFC front-name aware) so a craft plan
  never tells you to craft what you have (audit F19); a **non-numeric or non-finite**
  (`nan`/`inf`) `Power` is flagged `pow!` (scored 0.0 but surfaced, not silently sunk —
  audit F9/A10); and
  re-running `--add` on a batch **re-enriches** rows that were added name-only during
  an earlier Scryfall outage instead of skipping them as dupes (audit F20).
  `Target`/`Note`/`Power` are hand-annotated: `Target` is a
  deck id / `general` / `concept: …`; **`Power` is a 1–10 hand-graded constructed-
  power score** that `--rank` blends 50/50 with theme fit — plus a **bounded
  cross-deck reuse (breadth) bonus** (the `use` column, ★ at ≥3; guarded as
  bounded/capped by `check_rankings` anchor 5) so a multi-home craft outranks an equal
  fit+power one-deck sidegrade — into a `combined` score
  (an idf theme model can't see raw power, so bombs like Doctor Doom get buried
  without it — the Power column is the fix; the artifact exposes a live fit↔power
  slider). **Lands rank on a different axis:** a land has no synergy themes, so
  theme fit would sink it — `--rank` instead rates a land on **manabase value** for
  its target deck (how much of the deck's colors it produces, +untapped bonus, on
  the same 0–10 scale) and blends *that* with `Power`, tagging it `manabase (land)`.
  So a dual/verge that fixes a two-color deck ranks as the upgrade it is instead of
  bottoming out under spells; the same dual pointed at a mono-color deck stays low.
  The wishlist CSV itself isn't gated by check_all, but the **ranking
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
  That ranking is now **needs-aware**: the role credit is **saturation-discounted** (the
  8th removal spell is worth far less than the 1st, so `suggest` stops recommending an
  effect the deck is already deep in and `cuts` ranks a redundant piece as more cuttable
  while protecting a scarce one — #1); the score is nudged by a bounded (±15%) **curve
  factor** that gently favors filling a thin CHEAP slot and penalizes an over-full one
  (#2); and a modest **power co-signal** (the wishlist's rarity+role seed) surfaces an
  owned/craftable BOMB with only modest theme overlap without pulling in off-theme junk
  (it only re-ranks WITHIN the on-theme set — #6). All three are BOUNDED modifiers on the
  dominant theme-fit signal, gated by `check_suggest.py` so they can't silently reorder a
  tuned deck.
- **`deck.py engines <id>` grades a deck's two-sided ENGINES** (enabler ↔ payoff, #3).
  A synergy tag says "sacrifice" is in the deck; it can't say which cards FEED the engine
  (outlets/fodder) vs PAY IT OFF (death triggers). `engines` classifies each card's text
  as enabler and/or payoff for the engine themes (sacrifice, counters, tokens, graveyard,
  lifegain, food) and flags a lopsided engine — the ⚠ fires only off the trustworthy
  PAYOFF side ("payoffs but NO enablers" = dead payoffs; "payoff-heavy" = under-enabled),
  since enabler cues are broad; `deck.py stats` surfaces the flag inline. It's a shortlist
  that prints the card lists — read them, the classifier is heuristic. **Two combat-/self-
  fed false-positive classes are now discriminated (guarded by `check_engines.py`):** a
  **`sacrifice` "whenever ~ dies" DEATH trigger** is split from an outlet-dependent "whenever
  you sacrifice" payoff and is COMBAT-FED — exempt from the dead-payoff ⚠ once the deck fields
  ≥`_COMBAT_FED_MIN` (6) creatures (so a go-wide/deathtouch deck that trades constantly no
  longer reads as "payoffs sit dead" — the deck-31 misfire); and **`graveyard` self-recursion**
  (flashback / escape / disturb / unearth / harmonize / jump-start / retrace / aftermath /
  "cast from graveyard") counts as its OWN enabler, so a flashback-heavy yard isn't flagged
  "payoff-heavy" (the deck-9 misfire). The fix is SURGICAL: a genuine thin-enabler signal —
  e.g. many "N cards in your graveyard" *value* payoffs with few active fillers — still flags,
  because combat fills the yard only slowly there (unlike an immediate death trigger).
- **`deck.py stats` also prints an INTERACTION PROFILE** (#5): the raw interaction count
  treats all removal alike, so `stats` breaks it down by SPEED (instant vs sorcery) and by
  whether it can answer a NONCREATURE permanent (planeswalker / enchantment / artifact),
  flagging "all sorcery-speed" or "no noncreature answer" — measured, not eyeballed.
- **`deck.py stats` / `tier` measure a PROTECTION axis** — "can this deck protect the
  permanent it wins with?" Nothing asked that before: `stats`, `quality` and `tier` all
  counted interaction and card advantage, so an all-in single-threat deck with ZERO
  ward / hexproof / indestructible in 60 cards looked healthy, and the gap had to be
  found by hand-grepping the deck list. `role_tally` now returns **`protection`** via
  `protection_effects()` — deliberately NARROWER than the "Protection / trick" role,
  which lumps a combat pump ("gets +2/+2 until end of turn") in with a real answer to
  removal. `regenerate` is excluded on purpose: "It can't be regenerated" is boilerplate
  on removal spells, so keying on the word would score half the format's removal as
  protection. A **zero** is flagged in both views, naming the `#: protect:` build-arounds
  at risk. It is REPORTED, never fed into `tier_band` — that formula is anchored by
  `check_tier.py`, and a new term would silently re-grade the roster. It found 5
  zero-protection decks on first run (2, 37/37a/37b, 40), three of them with `#: protect:`
  headers.
- **`deck.py tier <id> --audit-rationale` catches a STALE tier argument** — and its
  SUPPRESSION RULES are the delicate part, because a citation is often legitimately not
  a claim about the current list. Two families, both windowed ±140 chars:
  `_HISTORY_CUES` (the card left / was held out) and **`_COMPARISON_CUES`** (the sentence
  changed subject — `path to`, `vs`, `unlike`, `distinctness`, `consider`), plus an exact
  mask of every **roster DECK name**, since a deck name that is also a card name
  ("Blood Price", "Sacrifices") read as a stale citation whenever one deck's prose named
  another for contrast — which is what the distinctness prose is FOR. Getting these wrong
  is asymmetric: a false positive is noisy and gets noticed, a **false negative is
  silent**. One did hide for a while — a bare `over` in `_HISTORY_CUES`, which matched
  "card advantage 9 **over** a 2.86 curve", the house phrasing for a quality vector, so
  the cue meant to catch a PAST figure was suppressing the sentence that states the
  CURRENT one. Deck 43 quoted interaction 10 against a live 8 and the audit said clean.
  Removing `over` then exposed the case it had been covering by luck — a figure written
  as a TRANSITION (`card advantage 0→1` states the OLD value first), now handled
  explicitly by **`_ARROW_AFTER`**. Keep these cue lists NARROW and let the roster-wide
  sweep be the check.
  **A SECOND, larger false negative had the same shape, and the root cause was reusing
  ONE rule for two different questions.** A CARD citation and a FIGURE go stale
  differently: a card is history when the SENTENCE is about a change ("Essence Scatter
  became hard counters"), which is why its ±140-char sweep for any change-word is right;
  a figure is history only when **the NUMBER ITSELF is stated as past**. Running the
  card rule over figures meant ordinary domain vocabulary suppressed live claims — and
  `remov\w*` (in the list to catch "removed") matches **"removal"**, the commonest noun
  in a rationale arguing about interaction. `"The floor reads A on interaction 9 … five
  surplus REMOVAL spells were traded"` was silenced by its own subject matter. So were
  `"…interaction 13 … THE PAYOFF IS THE ONE CRAFT TARGET"` and `"\"restore the
  interaction\" WAS not the whole fix … At interaction 6"`. Figures now go through
  **`_figure_is_history`**: BACKWARD-looking only, ~24 chars, for past-tense language
  directly governing that number (`was`, `up from`, `it cited a 2.65 curve`), plus the
  arrow and a tightened comparison window. Separately the avg_mv pattern read only
  `curve of 2.44` / `avg MV 2.44` while the rationales write **`a tight 2.44 curve`** —
  14 uses against 1 roster-wide, so that half of the audit was decorative. Both fixed
  together surfaced **13 stale figures across 10 decks** where the audit had reported
  clean, with **zero** false positives on the roster sweep. The lesson generalizes past
  this file: when one predicate serves two callers, check that the QUESTION is the same,
  not just the shape of the data.
  **The residual that fix left was a REVERSED claim, now closed by `_cites_as_arriving`.**
  A replacement names TWO cards and only one of them may legitimately be absent:
  "Essence Scatter became hard counters" documents a card that LEFT, but `"Spell Pierce
  was CUT for Shriek, Treblemaker"` names Shriek as the card that came IN — so when that
  swap was reverted the sentence asserted a swap that no longer existed, and the audit
  reported the deck clean through both directions because "CUT" sat adjacent either way.
  The check now un-suppresses a citation on the ARRIVING side of a directional cue
  (`cut/traded/swapped/exchanged … for X`, `became X`, `replaced by X`, `+X`), closed by a
  DEPARTING marker (`over Y`, `instead of Y`, `-Y`) since "+A (over B)" names both sides.
  **A THIRD sweep found the audit had been reporting the whole roster clean while TWELVE
  figures were stale — and this time the misses were in the PATTERNS, not the cues.**
  Three independent holes, all the same shape. (1) **Parenthesised figures.** The prose
  writes `interaction (3)`, `interaction total (3)`, `card advantage is thinner (3)`,
  `curve (2.81)`; the patterns demanded whitespace then digits, so every one was invisible
  — eight sat on the roster and deck 23 reported clean while quoting a 3.6 curve against a
  live 3.47. (2) **Number-first figures.** The roster writes `7 interaction` far more often
  than `interaction 7` — 13 interaction figures, 3 card-advantage, 1 protection, none ever
  read. This is EXACTLY the avg_mv miss already recorded two paragraphs up ("14 uses
  against 1 roster-wide"), repeated on the three axes the tier floor is actually computed
  from, which is the argument for fixing a class rather than an instance. (3) **`early_drops`
  was in the quality vector with NO pattern at all**, so that count could rot in total
  silence; deck 23 claimed "6 one-two-drops" against a live 11.
  Two false-positive classes came out of the same sweep and shaped the fix. The house style
  is a number-first claim followed by a **BREAKDOWN** — "7 interaction (5 spot removal + 2
  sweepers)" — so a permissive `\((\d+)` read the first SUB-COUNT as the claim and reported
  four decks stale against numbers they never asserted; requiring the bracket to close on
  the digits (`\((\d+)\)`) keeps the genuine cases and drops every breakdown. And a figure
  inside **quotation marks** cites earlier prose rather than claiming it (deck 7's `The old
  one-line reason ("thin interaction (3)") is no longer true`) — `_figure_is_history` cannot
  reach that with a 24-char window and widening it would loosen every other suppression, so
  it now treats an ODD count of preceding quote marks as a quoted span. All twelve findings
  were UNDER-statements (live exceeded quoted in 11 of 12), so no tier letter was at risk —
  but that is luck, not a property of the bug.
  **The KNOWN RESIDUAL is the label side, and it is live:** the figure patterns read
  `protection N` and `curve of N` / `a N curve`, so **"protection is 1"** and **"the
  reported 2.57"** both sailed through on deck 42a while the real values were 3 and 2.91.
  A copula or a participle between the label and the number still hides a figure. Widen it
  only with a roster sweep — the gap is deliberately bounded to two intervening lowercase
  words so a label cannot reach across a clause and adopt an unrelated number.
  Two of MY OWN cue bugs surfaced on the roster sweep, not from reasoning: `re.I` silently
  defeated the case-SENSITIVE capital that makes `+X` a card name, so the `+` in "hard
  counters + a mythic finisher" read as a swap marker; and "cut for" is not always a
  replacement — "two heist cards were CUT for **cause**: Doom Reigns Supreme wants five
  Villains" means cut for a REASON, so the arriving card must sit immediately after the
  cue (short gap, no `.;:—` in it). Both directions are unit-tested, and the roster sweep
  is the check that found them — run it on any cue-list change.
- **`deck.py tier <id> --audit-rationale` catches a STALE tier argument.** The `#: tier:`
  rationale is prose, so nothing kept it honest as the list changed underneath it — and it
  went stale twice in one session (40a's argued from Chelonian Tackle and Unforgiving Aim
  after both were cut; deck 40's cited a 2.26 curve after a swap moved it to 2.32). The
  tier guard only compares the LETTER to the floor; it never reads the argument. This does:
  it flags cards the rationale cites that are no longer in the deck, and figures that
  contradict the live quality vector. Card matching is CASE-SENSITIVE against known card
  names (prose capitalizes a citation, so a lowercase "counterspell" isn't one), masks the
  cards the deck DOES run first (else "the Ooze Spill" reported the card *The Ooze*), and
  suppresses citations sitting next to change/flex language — a rationale legitimately
  documents what it cut. Scoped to `#: tier:`; `#: notes:` is a free-form build log where
  naming an absent card is CORRECT. Report-only; it never edits the prose. Note the practical
  consequence of the suppression window: a rationale that legitimately NAMES a card it cut
  must put the change-cue ADJACENT to the name ("X and Y were CUT because…"), not a sentence
  later — three separate rewrites this cycle were needed for exactly that. **Run it after
  any deck edit** — a defensible grade rotting into an indefensible one is the exact
  failure the tier guard exists to prevent.
- **`deck.py suggest` shows a cross-deck reuse count (`Decks` column).** For each
  pick it counts how many of your OTHER decks (the deck being analyzed is excluded,
  so it can't inflate its own picks) the card is *castable* (its identity ⊆ the
  deck's declared/derived colors) **and** shares ≥1 *central* theme with (a theme
  carried by ≥25% of that deck's most-common theme's copies, floor 2) that is also
  **SPECIFIC** — a generic theme (etb/tokens/counters/lifegain/…) or a broad
  background tribe doesn't count, unless it's that deck's `#: protect:` build-around
  spine (≥2 protected cards). That gate is load-bearing: centrality alone left the
  count saturated — nearly every deck is central on the same handful of generic
  themes, so 99% of a deck's picks scored ≥3 and the median pick "fit" 31 of 56 other
  decks, i.e. the column carried no information (audit F-04). **VARIANTS are collapsed to
  their core deck** and `#: status:` placeholders are excluded — 19/19b/19c are one
  archetype's worth of value, not three homes (the second inflation source). Median reuse
  is now ~1–2 of 41 core decks, spread 0–19. Both models route the counting rule through
  **`deck.cross_deck_breadth`**, each supplying its own notion of a "specific" theme
  (deck.py's denylist vs the wishlist's idf cutoff — a deliberate difference), so the RULE
  can't drift apart again the way it did; `check_suggest` anchor 13 asserts the two agree
  on a synthetic card. Read it as a rough "value per wildcard": a craft that fits several
  decks outranks a one-deck sidegrade — still breadth, not curated fit. A "High
  cross-deck reuse" line summarizes the top fits≥3. Factor it into a craft's ★/~/·
  weight in a flex block.
- **Flex-block craftables are format-scoped.** When a deck's `#: format:` changes,
  re-check its `#~` craft suggestions — a craftable legal under the old format may
  have rotated (hit moving decks 1/2 Historic→Standard). `deck.py flex <id>` plus
  the pool's `Legalities` column confirm.
- **The pool's `Legalities` is a build-time SNAPSHOT — Standard rotates.** So a
  card the pool still marks `standard` may have aged out since the last
  `build_pool.py`. `deck.py suggest` guards against this with a **date-aware
  rotation check**: `build_pool.py` now writes a `Released` date per card and a
  `card-pool.build` date sidecar, and `suggest` marks a pick **`⚠rot`** when its
  set is >~3 years old (rotated / rotates soon) and warns when the pool stamp
  itself is stale. Treat `⚠rot` as "verify before crafting" and rebuild the pool
  (`build_pool.py --all`, per `/refresh`) to refresh both the legality snapshot and
  the date stamp. `rotation_risk()` returns False on a blank `Released` (graceful
  before a pool rebuild adds the column), so the flag only fires once the data
  supports it. The **roster-wide counterpart is `deck.py rotation`**: for each
  Standard deck it lists the cards past the ~3-year window (same `rotation_risk`
  primitive), a rollup by rotation year (soonest first, `⚠ SOON` for this/next year),
  and the most-exposed decks — *what rotates next and which decks it hits*. It reads
  the pool's `Released` column (rebuild `build_pool.py --all`, else it prints a
  rebuild prompt) and scopes with `--format` / `--years` / `--within` (how many years
  ahead to surface — since a freshly-built pool holds only currently-legal cards, it
  ranks by each card's rotation YEAR rather than a strict >years boolean). It's also a
  **dashboard panel** (Standard rotation), and `wishlist.py --rank` flags a craft target
  whose Standard-legal set rotates this year/next as **`⚠rot~YEAR`** (don't spend a
  wildcard on a card about to leave the format). **Reprint caveat, now partly encoded:**
  the pool keys ONE printing per card, so a card reprinted into a set with an announced
  non-standard legality window inherited the wrong date — Genesis Wave read `⚠rot~2027`
  off its Foundations printing when FDN is Standard-legal through **2029**, i.e. it was
  flagged "about to leave the format" with four years left (it ranked 27th; it now ranks
  4th). `deck.rotation_year(released, years, set_code)` consults
  **`_SET_ROTATION_OVERRIDE`** (add a row per announced long-legality set), and
  `rotation_risk` routes through it so the two primitives can't disagree. `rotation_risk`
  is calendar-YEAR based, not days-since-release, because rotation happens at an annual
  fall rotation: a 2023 set rotates during 2026 and is at risk for all of 2026, not only
  after its third birthday. The RESIDUAL is still real — a card whose newest printing the
  pool didn't capture can read early; verify against the official schedule.
- **`deck.py suggest-homes <card>` automates the "which of my decks does this new
  card improve" fit pass** (the manual dance repeated every craft this session —
  Doctor Doom, Elspeth, Wan Shi Tong, Shark Shredder). It scans EVERY deck and
  lists the ones where the card is both *castable* (its identity ⊆ the deck's
  declared/derived colors), **legal in that deck's `#: format:`** (the pool's
  `Legalities` snapshot, so a non-Standard card like Triumph of the Hordes isn't
  offered as a Standard home — `--any-format` disables; unverified/pool-absent =
  legal, like `suggest`/`legal`), **and** shares ≥1 *central* theme — with
  **cost-shaped themes gated** (`_drop_cost_themes`): filling your graveyard is VALUE in a
  reanimator deck and DAMAGE in a control deck that needs its counterspells in the library,
  but theme overlap sees one tag either way. Genesis Wave read **KEY for a Simic control
  deck purely on a `graveyard` match** — i.e. it scored highly BECAUSE it mills you.
  `graveyard`/`mill`/`discard` now count as a fit only when the deck fields ≥2 cards that
  PAY THEM OFF, reusing `engine_roles` rather than adding a model; it drops the theme for
  20 of 56 decks and keeps it for the real graveyard decks. (Note the motivating case is
  NOT filtered — that deck does field 3 graveyard payoffs, so the KEY is defensible on that
  axis; the objection to Genesis Wave there rests on its `GGG` cost against 15 green
  sources and on binning 15 of 34 nonlands.) Same 25%-centrality test as `suggest`'s reuse
  count (same
  25%-centrality test as `suggest`'s reuse count), ranked by theme-fit, marking where
  it's already maindecked and naming the single weakest nonland cut candidate per deck
  (`#: protect:` cards excluded). The card name is resolved like `card.py` (exact →
  DFC front → unique substring), so a partial name (`Ojer Taq`) or a God//Land DFC
  resolves instead of "not found". It's a SHORTLIST, not a verdict — the cut is one
  heuristic pick, so still grade from full oracle text via `deck.py cuts <id>` and
  preview with `deck.py swap` before applying. Because copies are fungible, it
  reminds you to slot a card into *all* decks that earn it, not pick one home. A
  **bounded curve co-signal** (`_home_curve_fit`, capped at `_HOME_CURVE_CAP`) gently sorts
  a top-heavy / win-more card (an ~11-mana Aettir and Priwen, MV well above a deck's average
  nonland MV) BELOW efficient fits in a low-curve deck and flags the row `⚠ top-heavy for
  this curve` — a one-sided nudge that never boosts, never relabels the KEY/role-player/
  tangential verdict, and only reorders same-strength fits (finding #5; anchor 12). Each
  fit row now carries a **strength label** (`KEY` / `role-player` / `tangential`):
  KEY = it shares the deck's *signature* theme (the top central theme, **or any theme
  carried by the deck's `#: protect:` cards** — so a counter-doubler reads KEY in a
  counters deck even though "counters" is idf-generic, correcting a blind spot where the
  deck's actual spine looked tangential), OR it shares a **specific** (non-generic) theme
  AND fills an interaction/card-advantage gap the deck is short on; role-player = a
  secondary specific central theme; tangential = generic overlap only
  (etb/tokens/lifegain/…). **The role-gap KEY is gated on a specific-theme match**
  (`fit_strength` checks generic-only → tangential BEFORE the gap branch): otherwise a
  generically-good removal / card-advantage card read KEY in *every* low-interaction deck
  it merely shared an etb/tokens tag with (Get Lost "KEY" in 15 decks). Its broad utility
  is real, but it belongs to the cross-deck **breadth** signal (wishlist `--rank` `use`
  column), not a specific home — so `suggest-homes` no longer inflates it. `GENERIC_THEMES`
  (the low-signal denylist behind "specific") covers the broad matters-generics PLUS
  card-selection/value and the evergreen combat keywords (flying/ward/first strike/…), so
  a keyword-only overlap never fakes a specific fit. **Broad background creature TRIBES
  get the same treatment** via `_GENERIC_TRIBES` (Human/Hero/Villain — so common in a
  superhero/anime multiverse they carry no home signal): a bare shared tribe can't mint
  KEY even as the deck's top theme OR via a `#: protect:` signature (the Hawkeye-"KEY"-in-
  every-Hero/Human-deck over-assignment, tagging-misreads #4). Narrow build-around tribes
  (Ninja/Cat/Dinosaur/Wizard/Merfolk/…) stay SPECIFIC — a real tribal payoff still reads
  KEY (guarded by `check_suggest` anchor 11). Rows sort strongest-first — trust KEY,
  judge role-player, and read a tangential fit as "probably not for this deck" (fit_strength
  is unit-tested). The same classifier flags a merely-tangential add in `deck.py quality --add`. **A rainbow fixer gets a
  color-count-aware overlay** on top of `fit_strength`: a card whose value is
  multi-color fixing (`_is_color_fixer`, read from oracle TEXT in explicit mana /
  basic-land-type context) is promoted to **KEY in a 4+-color deck / role-player in a
  3-color one** (and gets a bounded fit bump, `_fixer_boost`), because fixing value
  scales with the deck's color count — something a theme-overlap model can't see. It
  never demotes a fit `fit_strength` already rated KEY, and does nothing below 3 colors
  (mono/two-color decks don't want the fixing). This closed the Overlord → decks 17/21a
  miss. **The promotion is RATE-GATED and the cut side is add-AWARE — both because the
  overlay shipped a backwards recommendation.** See the fixer-overlay gotcha below.
- **`suggest-homes` reads CASTABILITY as an identity SUBSET — which says nothing about
  whether you can pay the pips.** A card is "castable" here when its color identity ⊆ the
  deck's colors, so **Anti-Venom (`{W}{W}{W}{W}{W}`) was rated KEY for decks 29/29a**, where
  10–11 white sources put it at roughly a **1%** chance of being castable on turn five. The
  identity test is right for *routing* and structurally blind to *depth*. `deck.py
  pip_depth_warning(cost, sources)` closes it with the same hypergeometric model
  `consistency` uses: a cost demanding ≥`_PIP_DEPTH_MIN` (3) strict pips of one color is
  priced against the deck's real sources (`deck_color_sources`) at turn `_PIP_DEPTH_TURN`
  (5), and anything under `_PIP_DEPTH_TARGET` (70%) prints `⚠⚠ 5x{W} vs 10 sources` on the
  fit row plus the source count that would clear the bar. It's a FLAG, never a score change
  — a deck can legitimately want a color-hungry bomb and fix for it — but the number is now
  on screen instead of implied by a subset test that can't see it.
- **`suggest-homes` also weighs a DOUBLER against the deck's magnitude on its axis.** A
  doubler (Exalted Sunborn, Delney, Anointed Procession, a counters doubler) is worth
  roughly what it doubles, and theme overlap cannot see that: Exalted Sunborn shares
  `tokens` with a deck that makes 14 tokens and with one that makes 6, and scored them the
  same — which is how it read `role-player` for Knight's Edge (deck 3) while ranking a
  6-token deck above it. `doubler_axis(text)` classifies the card on one of
  `_DOUBLER_AXES` (tokens / counters / triggers), `doubler_support()` COUNTS the deck's
  cards that feed that axis, and `doubler_boost()` turns the count into a bounded fit bump
  (`_DOUBLER_PER_SOURCE` 1.2 per feeder, capped at `_DOUBLER_CAP` 18, zero below
  `_DOUBLER_MIN_SOURCES` 5), promoting to **KEY** at `_DOUBLER_KEY_SOURCES` (10) the way
  the fixer overlay promotes at 4 colors — necessary because the strength label sorts ahead
  of raw fit. `doubler_restriction()` reads the doubler's OWN scope off its text
  (`_DOUBLER_POWER_RE`, e.g. Delney's "power 2 or less") and filters the feeder count to
  match; without it Delney's support in deck 24 read 24 instead of 4 — enough to flip it
  over the KEY threshold, i.e. the restriction is load-bearing, not a nicety. The cap is set
  at 18 rather than 12 so the term stays linear across the realistic 4–15 feeder range
  instead of saturating at 10 and calling a 14-token deck the same as a 10-token one.
  Bounded and gated by `check_suggest` anchor 14. Exalted Sunborn → deck 3 moves
  role-player/51 → KEY/69; Delney goes tangential (a bare `Human` overlap) → KEY for the
  decks it actually doubles.
- **Before committing a deck edit, run `deck.py preflight <id>` — and grade a
  cut/swap with `deck.py quality`.** `preflight` is the one-call gate the editing
  skills use: it folds `legal` + owned/buildable + castability + a full `check_all`
  pass into one PASS/FAIL block with a READY/BLOCKED verdict (hard-fails only on an
  illegal deck or broken integrity; WIP craft targets are WARN). `quality <id>`
  computes a deck-quality vector (buildable · uncastable · interaction/
  card-advantage · curve · central themes); snapshot it with `--json` **before** a
  change, then `--vs FILE` **after** to flag regressions (interaction dropped,
  castability broke, a central theme lost its last copy, curve heavier) so a swap
  that *worsens* the deck self-catches. It's a SOFT guard — an intentional trade
  (e.g. dropping card advantage for interaction in an aggressive deck) is fine and
  it only warns; grade the flagged axis from full text before accepting or
  reverting. This is what the `/apply-changes` skill runs around every swap.
- **`deck.py mana` also lints color SOURCES, not just pip demand.** After the pip
  breakdown it prints "Color sources (lands producing each color)" (basics by
  name, nonbasics by color identity — mana dorks aren't counted) and flags cards
  whose strict colored pips look thin against those sources (`△ Pip-intensive`:
  wants CC with <9 sources, or C with <4). This catches the "wants UU but this is
  really a U-splash" problem the castability lint (which only checks identity ⊆
  declared colors) can't see — e.g. a 3-source green splash flagging GG cards. A
  heuristic review signal, not a hard fail; it doesn't gate `check_all.py`.
- **`deck.py consistency <id>` is the PROBABILITY layer `mana` lacks.** `mana` diagnoses
  ("wants UU, only 6 U sources — thin"); `consistency` puts numbers on it via an exact
  hypergeometric model: opening-hand **keepable %** (2–5 lands in 7), **screw/flood %**,
  **land-drop consistency** (P of ≥N lands by turn N), and — per colored card — **P(casting
  on curve)** at turn = its mana value (capped at 5), with a **Karsten-style source
  recommendation** for the ones that come up short ("62% on T3 → want +2 R sources"). This
  is what caught deck 8's 1-red-source splash reading 12% on turn 2 (The Ruinous Wrecking
  Crew) — the "is this splash even castable" question the source-count lint only hand-waves.
  The fix note is source-count-aware: a **thin (≤3-source) splash** color is reframed as
  "cast late or cut, don't chase it on curve" rather than printing an impractical land
  count (15 R sources), and an **early double pip in a MAIN color** ({B}{B} on T2) reads
  "color-hungry — expect it a turn or two later" instead of being mislabeled a splash.
  Strict pips only (hybrids are strictly easier — excluded, same rule `mana` uses);
  multi-color costs use per-color independence (a mild over-estimate). `--on-draw` models
  the extra card; `--target P` sets the cast-probability bar (default 0.90). A planning
  aid, not a guarantee (mulligans/scry/draw shift the real numbers) — it doesn't gate
  `check_all.py`. Pure math helpers (`hypergeom_at_least`, `cards_seen`, `cast_probability`,
  `min_sources_for`, `opening_land_stats`) are unit-tested in `tests/test_deck.py`.
- **`deck.py suggest --lands <id>` is the manabase RECOMMENDER `consistency` was missing.**
  `consistency` DIAGNOSES a color-source shortfall ("want 18 R, have 12") but nothing turned
  that into a list of lands — and plain `suggest` is structurally BLIND to lands (it filters
  candidates to cards sharing a synergy THEME, and lands rarely do, so a manabase fix never
  surfaces; this is why a batch of hand-picked land/fixer suggestions once had to be found by
  a manual CSV query). `--lands` scores each on-color land by **FIXING value** (`wishlist.
  _land_value` — produces the deck's colors, untapped premium; the DOMINANT 0–10 axis) plus
  two BOUNDED nudges: **synergy** (`_land_synergy_bonus` — a land whose ability plays a deck
  theme, e.g. Abandoned Air Temple's team-pump in a go-wide deck: *lands sometimes have
  relevant text*) and **shortfall** (`_land_shortfall_bonus` — favor the color the deck is
  scarcest on, from strict pip-demand vs current sources). Both caps ≤2 so fixing decides and
  the nudges only break near-ties (gated by `check_suggest` anchor 9). `--owned` scours the
  collection for 0-wildcard fixers (usually the answer — it surfaced deck 39's owned Boros
  duals); `--unowned` ranks craft targets (untapped premium duals first); `--full` prints the
  land's oracle text so you grade the ability, not just the fixing. It excludes lands already
  in the deck and off-color/colorless-only lands (they don't fix THIS deck).
  **It now defaults to the deck's own `#: format:`, as the card-facing `suggest` always did.**
  It previously filtered only when someone passed `--format` explicitly, so a plain
  `suggest --lands <id>` on a Standard deck offered Underground River and Duskmantle, House of
  Shadow as craft targets — neither Standard-legal. On a WILDCARD-SPEND recommender an
  unfiltered pick costs real resources, and it is the "recommending a craft without a legality
  check" failure this file warns about elsewhere. Found by USING the tool to build a deck, not
  by a test. `--any-format` still shows everything.

- **`deck.py suggest --ramp / --interaction / --needs` are the NEEDS model — the structural
  axes theme-`suggest` is blind to.** The theme model answers "what SYNERGIZES"; a mana dork,
  a fixer, or a board-dependent removal spell fills a STRUCTURAL need (fixing / acceleration /
  interaction) it can't see — so these opt-in modes score against a shared **`deck_needs(d)`**
  profile (per-color source deficit, curve top-heaviness → accel-want, interaction count vs
  target) instead of themes. Never weaken the gated theme filter to surface them (the idf model
  was BUILT to reject catch-alls); add a parallel path. **`--ramp`** ranks repeatable mana
  sources (dorks/rocks; instants/sorceries excluded as one-shot rituals) by CHEAPNESS × the
  deck's accel-want (a cheap dork ramps a top-heavy deck; a 2-color deck's fixing is nearly
  solved, so fixing is only the bounded scarce-color bonus) + **restriction-fit** (a restricted
  dork — "add R only for Equipment spells" — is boosted in a matching deck, penalized in a
  mismatched one; `_ramp_restriction_fit`) + a power tiebreak — surfaces Purple Dragon Punks
  atop deck 39. **`--interaction`** surfaces removal INCLUDING off-theme (the fix — theme-suggest
  filters it out), ranked by power + a bounded **scaling boost** for a board-dependent spell the
  deck supports (`_int_scaling` detects fight / "damage = N you control" / X-cost; `_scaling_
  metric` reads the deck's strength on that axis) and FLAGS it `⚠ scales w/ <axis>` for a human
  read — never a silent boost (the honest stance for a fuzzy signal). **`--needs`** is the
  one-stop view composing all three (fixing · acceleration · interaction). All nudges bounded,
  gated by `check_suggest` anchor 10.
- **`deck.py cuts` folds a card-QUALITY (power) co-signal into the ranking (#3).** Theme
  fit alone can't tell a vanilla body from a bomb that share one tag, so cuts blends the
  wishlist's rarity+role **Power** estimate into the keep-score: an on-theme-but-WEAK card
  sorts UP the cut list (flagged "on-theme but low power") and an on-theme BOMB is
  protected. It's a **bounded** nudge (`_cuts_power_adj`, ±`_CUTS_POWER_CAP`, neutral at
  power 5) — it only breaks near-ties, never overrides theme fit — and is gated by
  `check_suggest.py` anchor 7 (mirrors the suggest power co-signal, anchor 5). A `Pw`
  column shows each card's power; still grade from the printed oracle text, not the number.
- **`deck.py cuts` folds a MULTIPLIER co-signal (`✱`) — and the bug it fixes is a caller,
  not a model.** A doubler's worth lives in the REST of the deck, and BOTH halves of the
  cut score are structurally blind to that: theme-fit sees a card with few tags, and
  `_role_credit` sees no functional role, because "doubles a trigger" is not a role. So
  **Delney, Streetwise Lookout — which doubles the triggered ability of every creature in
  deck 46's small-body engine layer (10 feeders) — ranked as that deck's WEAKEST card**,
  with Valkyrie's Call just behind it. The information was already in the codebase:
  `doubler_axis` / `doubler_support` were built for `suggest-homes` and score Delney
  correctly, *including* its "power 2 or less" restriction. `cuts` simply never asked.
  `_cuts_multiplier_adj` routes the SAME primitives into the keep-score — not a second
  model, so the two cannot disagree about what a doubler is worth — bounded to
  0…`_CUTS_MULT_CAP` and **ZERO below `_CUTS_MULT_MIN_SOURCES`**, because a doubler in a
  deck that does not feed its axis genuinely is cuttable. It only ever RAISES a
  keep-score: the no-support case is already handled by theme-fit, and subtracting there
  would punish the same card twice. Gated by `check_suggest` anchor 16, which pins the
  bounds AND (in `tests/test_deck_models.py`) the WIRING — a pure-function anchor cannot
  see whether a caller asks, which is exactly the F-01/F-18 failure shape and exactly what
  went wrong here. Roster impact: 15 multipliers across 11 decks re-scored; every
  non-doubler unchanged.
  **A LIFEGAIN axis was added to `_DOUBLER_AXES` at the same time**, because The Wind
  Crystal ("if you would gain life, you gain twice that much life instead") read as no
  doubler at all — the axis list stopped at tokens/counters/triggers. It requires the
  literal `twice that much` rather than reusing the other axes' looser `instead`
  alternative, because a replacement that is NOT a doubling is templated identically:
  Angel of Vitality's "you gain that much life plus 1 instead" is +1, not ×2, and would
  have qualified. Pool diff: 53 → 57 doublers, the four new ones all genuine.
- **`deck.py cuts` flags COST-AS-UPSIDE (`⚡`) — a cost that is a BENEFIT in this deck.**
  Every scoring model here grades a card in ISOLATION, where an additional cost reads as a
  drawback; in the matching deck the same clause is an engine trigger. CLAUDE.md warned
  humans about this in prose ("ask what does this do *here*") but nothing detected it, so a
  card whose cost is secretly an upside sorted like one with a real drawback.
  `cost_upside_flags(text, deck_themes)` pairs a cost pattern with the themes that invert
  it: a **kicker returning a land** in a LANDFALL deck re-triggers every landfall payoff
  (Chocobo Kick); **Warp / "when this leaves the battlefield"** in a COUNTERS deck is what
  moves the counters onto your threat (Broodguard Elite); a **sacrifice** cost feeds a sac
  outlet; a **discard** cost fills a reanimator's yard. Shown in the cut table and again in
  the oracle-text block. It is a FLAG for a human read, never a score change — the same
  posture as `⚠ scales w/`, because the signal is real but too fuzzy to move a ranking.
- **The MIRROR of cost-as-upside: a fine card that fights your own engine.** The `⚡` flag
  catches a drawback that is secretly an upside here; nothing catches an UPSIDE that is
  secretly a drawback here, and that shape shipped into two finished decks. Strategic Betrayal
  and Pit of Offerings both read as perfectly good cards — and both EXILE an opponent's
  graveyard, while four heist cards in each deck (Tinybones the Pickpocket, Shark Shredder,
  Hama, Azula/Rakdos) need that graveyard FULL. `deck.py cuts` did rank Strategic Betrayal
  second-weakest, so the shortlist saw it; only the full-text read explained WHY. The general
  rule: when a deck DEPENDS on a zone being populated, audit every card that empties it —
  graveyard hate in a graveyard deck, hand attack in a deck that wants them holding cards.
  Grading a card in isolation cannot see this, which is the same blind spot `⚡` exists for.
- **Grade a modal / split / adventure card by the FACE YOU CAST, not the half you want.**
  Decadent Dragon was drafted into a Rakdos deck for its `{2}{B}` adventure half (a two-card
  heist) and cut once `deck.py consistency` priced its `{2}{R}{R}` FRONT face at 53% on turn
  four. The rationalization — "the half this deck actually wants is castable" — is exactly what
  the front-face costing convention exists to prevent, and `consistency` is the tool that
  settles it.

- **`deck.py cuts` also folds an ability-DISTINCTIVENESS co-signal — the card-level analog
  of the deck-idf theme model.** The deck theme model weights how rare a theme is across
  *decks*; nothing measured how generic a *card's own abilities* are, so a body carrying
  five common tags (`etb; tokens; sacrifice; lifegain; pump`) tripped broad synergy-overlap
  everywhere, indistinguishable from a distinctive-mechanic card. `lib.card_distinctiveness`
  scores that from **pool tag-rarity**: a card's ability tags mapped to pool-idf, evergreen
  keywords and bare creature TRIBES excluded (identity, not ability — a niche tribe isn't a
  distinctive *mechanic*; noncreature subtypes like Equipment/Aura/Case are kept), scored on
  its *rarest* couple of tags (top-2 mean, so a standout ability isn't diluted by also
  carrying etb) normalized to 0–10. A vanilla card reads ~0; a rare mechanic reads high.
  cuts shows a **`Uq`** column and blends it as a **bounded, orthogonal-to-power** keep nudge
  (`_cuts_uniq_adj`, ±`_CUTS_UNIQ_CAP`, neutral at 4) — a generic-ability filler sorts UP the
  cut list (flagged "generic ability — trips broad synergy checks"), a distinctive card is
  mildly protected; gated by `check_suggest.py` anchor 8. It's **orthogonal to power** on
  purpose (a vanilla 6/6 is high power, low distinctiveness), so it earns its own small term.
  Tags are a lossy projection, so a **second, complementary signal** closes the residual:
  `lib.structural_distinctiveness` reads the oracle TEXT's SHAPE — an unusual (non-ETB)
  trigger, a non-mana activated ability, rule-bending / replacement language, modality,
  clause depth — to catch "this card does something the tags didn't capture," with NO
  corpus / build artifact / normalization pipeline (the cheap alternative to a text
  TF-IDF model; option 2 of the two follow-ups). `card_distinctiveness(tags, text)` returns
  the **MAX** of the tag-rarity and structural signals, so the structural term only ever
  RAISES a score — it RESCUES a mis-tagged distinctive card (Ragnarok's dies-trigger 2.1→7.5,
  Thousand-Year Storm's copy engine 3.6→7.5) but can never inflate a truly generic one
  (vanilla / plain-ETB / bare-mana all stay low; the mana-dork activated ability is excluded).
  Both callers pass the card's text; omitting it is tag-only (backward-compatible). The
  RESIDUAL caveat is now small but real: a distinctive card with *neither* a rare tag *nor*
  an unusual text shape still reads generic — so `Uq` remains a shortlist signal, not a
  verdict (a full oracle-TEXT-rarity model is the heavier follow-up if this ever misfires).
  `wishlist.py --rank` shows the metric as a **`uq` diagnostic column** (display-only there —
  it does NOT feed `combined`): a low `uq` on a `review` card confirms filler, a high `uq`
  says the tags under-read it — grade from text.
- **`deck.py tier <id> --to <TIER>` now assembles a concrete CUT→ADD tune package (#4).**
  Past the measurable gap + owned/craft fillers, it pairs each filler that closes the gap
  with a weakest-fit cut from the SAME ranking `deck.py cuts` prints (so the two can't
  disagree), then **projects the resulting quality vector and floor** ("interaction 2→5 ⇒
  floor C→A ✓"). It flags a cut that itself feeds interaction/card-advantage ("⚠ pick
  another cut") **or is a mana source** (a dork/rock/ramp spell — "⚠ losing it may hurt
  the manabase", caught via `_produces_mana` so an "add one mana" dork the role classifier
  misses still flags) and notes when the cut list is exhausted before the gap closes. It's a
  STARTING plan that PRINTS, never writes — the card selection stays a human call (protect
  signature/spice — that's `/tune-deck`); preview any line with `deck.py swap`.
  **Its OWNED filler list used to skip the legality check its CRAFT sibling applied** —
  so `--to A` printed one list headed "format-legal" and an unfiltered one directly above
  it, and offered **Deadly Dispute** and **Dovin's Veto**, neither Standard-legal, to
  Standard decks. Owning a card is not a licence to play it: the pick costs no wildcard
  but it still costs a DECK SLOT, and an illegal maindeck card is a worse outcome than a
  wasted craft. `owned_role_fillers` now filters on the deck's `#: format:` exactly as
  `craft_role_fillers` does (pool-absent/unverified legality = legal, matching
  `legal`/`suggest`). Same shape as the `suggest --lands` bug one command over, and the
  same lesson: **when two functions answer the same question for owned vs unowned cards,
  diff their filters** — one of them will be missing a check. Fixing it exposed a second,
  older bug underneath: `load_card_data` keys a DFC under BOTH `Front // Back` and its
  front face, and both rows carry the same display name, so a double-faced filler printed
  **twice**, wasting a line of a six-line list. Deduped on the display name. Both are
  pinned in `tests/test_deck_models.py` (verified to fail on the un-fixed code).
- **`deck.py redundancy <id>` plans competitive CONSISTENCY the "virtual copies first" way.**
  A singleton/highlander deck draws a random slice of its plan; the fix for competitive
  quality is redundancy — but the *first* lever is **functional redundancy** (distinct,
  similar-but-different cards that do the same job — "virtual copies"), which raises
  consistency while keeping the singleton feel, and only THEN true 4-of duplicates. The
  command buckets the deck's cards by EFFECT (functional roles + specific non-generic
  synergy themes), prints each effect's **depth** (distinct cards providing it = its
  virtual-copy count), flags the **thin** ones (≤`_REDUNDANCY_THIN`), and for each proposes
  how to firm it to `--target` (default `_REDUNDANCY_TARGET`=4): **functional copies FIRST**
  (owned/craft distinct cards via `owned/craft_role_fillers` for a role, `functional_theme_
  options` for a theme), with **true duplicates only as a FALLBACK** when there aren't enough
  of acceptable quality. The decision is the pure, unit-tested `plan_redundancy_fill` — it
  prefers a virtual copy unless it's >`_REDUNDANCY_QUALITY_TOL` (1.5 on the 0–10 power scale)
  below your best existing copy, else recommends duplicating the strongest existing card.
  This is why a functionally-dense singleton (e.g. Wizardz 37b's ping win-con as a virtual
  ~10-of: Coruscation Mage + Firebrand Archer + Thunderdrum Soloist + Black Waltz + the token
  makers) can defensibly grade A: **the tier floor counts effects, not distinct cards**, so
  virtual copies score the same floor while dodging singleton variance — a notch below a
  true-4-of build (the copies aren't identical — a quality tax — and can't STACK a keystone),
  but a real A when the plan hinges on no single card. `/tune-deck` runs it in the competitive
  flow (semi-singleton first, duplicates as fallback). It PRINTS a shortlist — grade the
  virtual copies from full text like any other add.
- **Building a deck FROM SCRATCH (not a pasted list) has four helpers** — the tooling is
  strong at ANALYZING/tuning a list but these close the gap at CREATING one. **`deck.py
  similar <id>`** ranks the decks most alike by central-theme overlap (cosine over the
  weight vectors, GENERIC themes/tribes DAMPED via `_SIM_GENERIC_DAMP` so a shared SPECIFIC
  theme drives the score, not "we both draw cards") + a color-overlap %. It marks each shared
  theme `✦` when SPECIFIC (an identity theme) and splits the verdict: a `⚠ overlap` (≥60% AND
  shares a specific theme — a real duplicate-identity signal) from a softer `· value overlap`
  (high sim on generic value themes only — both are value decks, not the same deck), so a
  diffuse good-stuff deck doesn't false-alarm as a duplicate. A generic-by-idf theme is
  RESCUED to specific (✦) when it's a deck's real BUILD-AROUND spine — carried by ≥2 of its
  `#: protect:` cards (`_strong_signature_themes`), so a counters-doubler deck reads counters
  as its identity (30↔04 flags ⚠), while a lone protected bomb's incidental card-draw/etb tag
  can't promote a diffuse deck's generic overlap into a false match. `--specific-only` scores
  identity themes alone (a diffuse deck then honestly reads as sharing nothing specific). The roster "is
  this deck distinct or a duplicate?" check (answers the question a from-scratch build always
  raises; it's a SHORTLIST — grade the DOMINANT theme + win-con from `deck.py text`, not the
  number — a shared tribe can be incidental, e.g. Druid mana dorks). **`deck.py resolve <names…>`** turns card names into
  ready-to-paste deck lines `<qty> Name (SET) #` with a valid printing (exact → DFC front →
  unique-substring, OWNED printing preferred; reads args or stdin, optional leading qty),
  reporting unresolved/ambiguous names instead of guessing — removes the hand printing-lookup
  (and the off-by-one that shipped a 59-card draft). **`pool.py --role <removal|sweeper|
  counter|draw|ramp|cheat|payoff>`** filters the collection by FUNCTIONAL role (via
  `classify_roles`, aliased to friendly names), so you survey owned cards by what they DO,
  not just their synergy tags — the deckbuild axis `--synergy` couldn't reach.
  **`deck.py screen <id> <names…>`** is the fourth, and it exists for a failure the other
  three cannot touch: a candidate pile graded ONCE keeps those verdicts after the plan
  changes. Deck 46's 76-card pile was screened against a "one enormous body" plan; when
  the plan became "several growing lifelink bodies with an Angel sub-theme and recursion",
  only the cards the user re-raised got re-graded and the rest carried stale reasoning
  forward — Shrike Force, Linden, The Wind Crystal and Prayer of Binding all sat in that
  bucket, each excluded for a reason that had expired. `screen` re-scores a whole list
  against the deck AS IT IS NOW (fit strength, roles, shared central themes, legality,
  owned-vs-craft), so an answer cannot be stale by construction. **Re-run it after any
  change of plan, not once.** It carries two flags nothing else does: **`✱ multiplier`**
  (as `cuts` now does), and **`★ STRICT UPGRADE`** — in-deck cards the candidate strictly
  beats. That second one is the bug it was built for: **Prayer of Binding is Liminal Hold
  with FLASH** — identical `{3}{W}`, identical text — and Liminal Hold sat in the 60 while
  Prayer of Binding sat on the excluded list under a note comparing it to a different card
  entirely. `strict_upgrades` is a deliberately conservative TEXT-CONTAINMENT test
  (reminder text stripped, self-references normalised via `_UPGRADE_SELF_RE` so modern
  "this creature" templating matches older "<Name>" templating): every clause of the
  incumbent must appear in the candidate, at the same or lower mana value, and the
  candidate must do strictly MORE. Identical text at identical cost is **redundancy, not
  an upgrade** — often a good thing (virtual copies), and flagging it would fire on every
  deck's own redundancy. Color identity is deliberately NOT in the test (`screen` flags
  off-color separately) so a text-containment result never depends on the deck's colors.
  It misses most real upgrades by design; **its silence is not a verdict**. Driven by
  `/draft-deck` Stage 5 and `/tune-deck` step 6a.

- **Every role COUNT now carries its own uncertainty** (`lib`-free `deck.count_conf`).
  A heuristic classifier reports a false negative as a FACT: a card it can't parse
  contributes 0, and `0` reads as "none" rather than "not detected". That is the single
  most damaging failure this toolkit has had — deck 40a was graded on interaction 3
  against a hand count of 7. `role_tally` now also returns `interaction_unread` /
  `card_advantage_unread` (a broad cue fired but no role matched), **`unclassified`** (a
  noncreature spell that matched NO role and tripped NO cue — the Broken Wings /
  Repulsive Mutation case, the worst kind, so it is reported even though it can't be
  attributed to one axis) and `unreadable` (no oracle text on file). `stats` and `tier`
  render `7`, `3 +2?`, or `8 +4? (3 unclassified)`. 54 of 59 decks show uncertainty
  inline — mostly the `unclassified` channel, which is exactly the queue the second
  under-count sweep was mined out of. The bare ints are unchanged for `tier_band` and the F10 guard, which compare
  numbers; the annotated string is what a human reads.
  **The remainders are QUANTITY-WEIGHTED, like the counts they annotate.** They used to be
  card counts, so `8 +4?` compared a weighted base against an unweighted remainder and a
  deck running 4× of a card with no oracle text on file reported `+1?` for four unread
  copies (broad-scan F-09) — understating uncertainty, which is the wrong direction for a
  signal whose entire job is to stop a heuristic count reading as fact. They are deduped by
  NAME first, because `role_coverage_flags` emits one entry per LINE and a card split
  across two printing lines would otherwise be weighted twice. Only the annotation moved:
  the bare ints feeding `tier_band` were verified unchanged on all 63 decks.
- **`deck.py shape <id>` answers WIDE vs TALL, FAST vs SLOW** — the structural question
  themes structurally cannot: `counters` is the same tag whether they all go on one
  creature or spread across twelve. Reading `#: archetype:` prose instead produced the
  worst misread of the cycle (deck 30 was called a wide deck from its header while the
  open question was whether a TALL counters plan duplicated it). Scores WIDE cues (token
  creation, anthems, count-scaling) against TALL cues — deliberately only AMPLIFIERS
  (doubling, equipment/aura pump, "where X is its power"), because the first draft keyed
  on "put a +1/+1 counter on target creature" and read a 27-creature WIDE board as tall;
  a single counter is wide glue too. Creature DENSITY is folded in (≥22 copies pushes
  wide, ≤14 pushes tall) since a text scan can't see it. Prints the effect lists, not
  just the verdict. Note it reads deck 30 as BALANCED against its own "go wide" header —
  14 creatures plus counter-doublers genuinely is both, and the header is the older claim.
- **`deck.py resolve --format` warns on cards not legal in the format** (default
  standard; `any` disables). Resolving a printing is not a legality check, and that gap
  let Bloodchief Ascension — a TLE supplemental card — reach a finished 60-card deck
  file, caught only two validation steps later by `deck.py legal`.
- **`deck.py redundancy` also lists INTERCHANGEABLE cards** (`near_duplicates`): groups
  of nonland cards with identical non-empty role sets inside a 1-mana band. `redundancy`
  buckets by EFFECT ("how many virtual copies do I have"); nothing answered "which of my
  specific cards are the same card here", and that gap produced a real bad
  recommendation — cutting Chelonian Tackle was proposed without noticing Epic Fight
  already provided the fight mode. Reported as GROUPS, not pairs (a 6-card removal suite
  is 15 pairs and one useful fact), split into cost bands so a 1-drop and a 6-drop aren't
  called interchangeable, and cards with NO detected role are never grouped — no signal
  beats a guess.
- **The VERDICT surfaces now print evidence.** `cuts` and `swap` print full oracle text
  and produced the fewest bad calls all cycle; `suggest-homes` handed out KEY /
  role-player / tangential labels with no text at all, which is how Genesis Wave was
  rated KEY for a deck whose engine it mills away. `suggest-homes` now always prints the
  card's oracle text, and `deck.py similar --full` lists the shared nonland CARD names —
  the concrete evidence behind a theme cosine that can read 84% on five shared cards,
  four of them lands.
- **A CAPABILITY THAT WORKS AND IS NEVER REACHED is invisible to every correctness
  gate.** Eleven gates verify that each model is right; not one can see a command nothing
  runs. That is not hypothetical — it is written a few paragraphs down in this file:
  `/tune-deck` sat on the command set it shipped with while `consistency`, `engines`,
  `shape`, `cuts`, `flex` and the needs-aware `suggest --needs/--interaction/--ramp/
  --lands` were built around it, and *"the one recommender a tune-for-interaction would
  reach for is blind to the fix."* Every one of those was correct, gated, documented —
  and unused. The SKILLS are the composition layer, and they were the last hand-kept
  registry with no gate, exactly like `check_patterns`' coverage list (13 patterns
  behind), `_INLINE_PARSE_ALLOW` (could name deleted code) and the argparse tree (no gate
  ever built one). **`check_commands.py` closes it as a hard `check_all` gate**: every
  `deck.py` subcommand and every runnable script must be invoked by a skill, called
  programmatically by another module, or listed in `INTERACTIVE_ONLY` **with a reason** —
  and a stale exemption naming a command that no longer exists is itself a failure.
  Two design points worth keeping. Coverage requires a REAL call (`cmd_*`) or a skill
  invocation, **not a prose mention**: the first draft matched the string `deck.py <name>`
  anywhere under `scripts/`, and since every docstring here cross-references commands, it
  passed five genuinely unreachable ones — a check that cannot fire, in the check written
  to stop checks that cannot fire. And the first honest run flagged `audit`, `brawl`,
  `rotation`, `sync`, `verify` — **all roster-level**, which is the actual finding: the
  per-deck loop had `/tune-deck` and `/apply-changes`, and the roster loop had no workflow
  at all. **`/roster-review`** is what closed it (triage → rotation → craft plan → Brawl
  → Arena drift), so those five are now driven rather than remembered.
- **A SET plus a sort key that can TIE is a nondeterministic output.** `wishlist`'s
  displayed `sig` changed between runs of unchanged code: `shared = ctags & central` is a
  SET, and `sorted(..., key=lambda t: -idf[t])` left tied themes in set-iteration order.
  `Aura`, `aura` and `enchant` all score idf 3.1135, so the signal flipped among them on
  every build — and `PYTHONHASHSEED` changed it too. Nothing was WRONG in any single run,
  which is why it survived: the cost was that `dashboard.html`'s `#data` island churned on
  every rebuild (every Pages deploy republished a payload differing from the last for no
  real reason) and the live ⟳ sync could show different signals from the local snapshot.
  The fix is to make the key a TOTAL order — `(-idf[t], t)` — so ties break alphabetically
  and stably; the same bug sat at two sites (`_rank_scores` and `cmd_suggest_targets`).
  **Before sorting anything derived from a set, ask what happens when the key ties.** This
  was found by CHECKING the "restyle is template-only" claim (rebuild twice, diff the
  payload) rather than asserting it — worth keeping as a habit for any dashboard change,
  since a build-to-build diff is the only thing that makes this class visible.
- **NO GATE BUILT AN ARGPARSE TREE, so a broken `--help` was invisible.** `check_all.py`
  imports `deck` as a MODULE and calls `cmd_*` functions directly; `main()` and the
  parser only exist under `__main__`, and nothing in `tests/` constructed an
  `ArgumentParser`. So `deck.py --help` crashed for four days with three green workflows
  (broad-scan F-01/F-12). The cause is a rule worth knowing before you touch any help
  string: **argparse renders help through `help % params`, so a bare `%` raises
  `ValueError: unsupported format character` — write `%%`.** Worse, the top-level help
  EXPANDS EVERY SUBACTION, so one bad string among 33 subparsers takes the whole
  `--help` down, i.e. the discovery surface for the project's main tool — the very
  "tool list" CLAUDE.md tells you to re-read a skill against. Now covered twice:
  `tests/test_cli.py` runs `--help` on every script in `scripts/` (32 today; the test
  lists the directory rather than a fixed set, so the COUNT can't go stale even when this
  sentence does) plus each deck.py subcommand in a
  thread pool (~2s, asserting no traceback and that argparse scripts exit 0 with usage —
  argparse use is detected from SOURCE, not a hardcoded list, so it can't go stale), and
  a dependency-free shell mirror in `.github/workflows/integrity.yml`, which runs on
  EVERY push rather than just main + PRs. Both were verified to fail on a reintroduced
  bug. One trap found while writing the CI half: the first shell extraction of the
  subcommand list silently yielded ZERO subcommands and still passed, because it guarded
  on `[ -z "$subs" ]` and a whitespace-only capture is not empty — a check that covers
  nothing while reporting success, which is the exact failure this whole family is about.
  It now guards on the COUNT (`-lt 25`).
- **`swap --apply` is the only moment a real add/cut DECISION is observable — it now
  records one.** Every ranking model here (`cuts`, `suggest`, the bounded co-signals, the
  whole gated stack) had been graded on argument and anchor tests and never against a
  decision anyone actually made. That is the same gap CLAUDE.md records for the `Decks`
  column: it read as working right up until someone MEASURED it and found a 0% actionable
  rate. `deck.py swap --apply` / `apply-flex --apply` now append a row to
  **`recommendations.csv`** — where `cuts` ranked the card you cut (rank/total, plus
  whether it was `#: protect:`ed) and whether `suggest` surfaced the card you added in its
  default top 20. Ranks are captured against the PRE-swap deck, because that is the list
  the decision was made against; re-deriving one later would score against a deck the swap
  already changed. `deck.py feedback [<id>]` reads it back.
  **The report LEADS WITH DISAGREEMENTS, and that ordering is the whole design.** An
  agreement is contaminated: you read `cuts` before deciding, so a high agreement rate
  partly measures the shortlist's INFLUENCE rather than its accuracy — a metric that
  cannot distinguish "the model is right" from "the model was persuasive" is the
  saturation failure again. A DISAGREEMENT (you cut a card the model put in its keep half)
  is a case the model got wrong whichever way the decision was reached, so it is the
  informative direction. Below `_RECS_MIN_SAMPLE` (20) the report refuses to compute a
  rate at all, the same restraint `parse_matches --report` and `count_conf` show.
  **"Add not surfaced" is EXPECTED and is not on its own a model miss** — `suggest` filters
  to cards sharing a synergy THEME and is structurally blind to lands and off-theme
  removal (that is what `--lands`/`--interaction`/`--ramp` exist for), so read that count
  as "which fills the theme model can't reach."
  **It is REPORT-ONLY and must stay that way.** The scoring terms are bounded and anchored
  by `check_suggest` precisely so they cannot silently reorder a tuned deck; a feedback
  loop that quietly re-weighted them would defeat that by construction *and do it
  invisibly*, since every pure-function anchor would still pass. `tests/test_recommendations.py`
  pins this structurally — no function in the scoring stack may reference the ledger — so
  wiring feedback into a score requires deleting a test, which is the point: it makes the
  decision visible instead of incidental. Recording is also **never fatal to a swap**: each
  model call sits in its own guard, a swap whose telemetry fails is still saved, and a row
  is written only AFTER the edit lands (so a rejected write leaves no phantom row).
- **Match results are FREE from `Player.log` — the header line is the load-bearing half.**
  Arena's "Detailed Logs (Plugin Support)" setting writes match events locally; that is the
  same feed every third-party tracker reads, and their subscriptions buy cloud analytics,
  not log access. (COLLECTION data was locked down years ago, which is why ingestion has to
  undercount — see the deck-dump gotcha. MATCH results were not.) `scripts/parse_matches.py`
  (`/log-matches`) turns a paste into `matches.csv`. Two line shapes are needed and **both
  are required**: the `finalMatchResult` JSON carries the outcome and both players' seats
  but **NOT which seat is yours** — the local userId appears only in the `Match to <userId>:`
  header prefix. A paste of the JSON alone is unparseable, so the parser SKIPS with an
  actionable warning rather than guessing; a 50%-accurate record would be worse than an
  empty one because it looks like data. (`--me <userId>` is the escape hatch.) Three more
  things the real log settled, none of them guessable from the JSON alone: the log line's
  LOCAL timestamp must beat the JSON's UTC epoch (an evening session otherwise files a day
  late — the sample's own header said 7/27 while its epoch resolved to 7/28), the epoch is
  still the right FALLBACK when no header date exists (a blank Date sorts to the top and
  can't be scoped in time), and `courseId` is Arena's own deck identifier with **no
  derivable relationship to a repo deck id** — so the mapping is LEARNED from a `#: arena:
  <courseId>` deck header, and an unmapped match is kept and surfaced, never dropped.
  Deliberately stores no userId and no playerName: neither is needed for a win rate, and a
  match log is not a place to accumulate identity (opponent *deck* is kept — an archetype,
  not a person). The scan keys on the EVENT rather than on `"finalMatchResult"`, because a
  truncated paste is the expected failure and that marker sits LATE in the line, after both
  seats — so any realistic width cap removed it and the match was dropped in **silence**
  while the run reported success. Found by a test, and it is this project's signature bug
  class one more time: the check keyed on the thing the failure destroys.
  **Read the record with restraint.** Below `_MIN_SAMPLE` (20) matches `--report` refuses
  to print a percentage at all, and above it prints a 95% **Wilson** interval (the naive
  normal approximation is wrong at exactly these sample sizes). A win rate separates a
  BROKEN deck from a fine one; it will not separate a 55% deck from a 45% one without
  hundreds of games. Never write one into `#: tier:` — tier grades the LIST against the
  rubric, and a small-sample rate is not evidence at that resolution, so citing one would
  be precisely the stale-rationale failure `--audit-rationale` exists to catch. Same
  restraint `count_conf` shows for role counts: a number that looks certain when it isn't
  is the expensive kind of wrong.

## Known Issues

- A handful of recurring Universe-Beyond flavor *mechanics* (Vivid, Job select,
  Opus, Increment, Infusion, Paradigm, Disappear, Tiered, **Jump**) aren't in
  `tag_synergies.py`'s keyword→theme map, so they're tagged verbatim. They live in
  `scripts/keyword_baseline.txt` — the acknowledged-but-unindexed list — so the radar
  stays quiet about them; theming them is ROADMAP Tier 1.
  **Vivid is the cautionary one on this list:** an unindexed keyword is not inert, it is a
  hole every tag-gated predicate inherits — `_is_color_fixer` gated on a `ramp`/`mana` tag
  and so read the roster's two best fixers as non-fixers (see the fixer-overlay gotcha).
  **`renew` and `triple` were the standing pair, and they triaged in OPPOSITE
  directions** — which is the argument for doing this per-keyword rather than in bulk.
  `renew` (Tarkir: Dragonstorm, 14 pool cards, every one on the same template) is a real
  mechanic of exactly the `forage` shape — a COST plus an EFFECT — so it maps to the two
  resources it touches: **`["graveyard", "counters"]`**, since it is activated FROM your
  graveyard and puts counters on a creature. Deliberately NOT `sacrifice` (nothing is
  sacrificed) and NOT `recursion`: the card is EXILED to pay for the counters and never
  comes back, so a renew card in the yard is a resource to spend, not a rebuy, and tagging
  it recursion would point reanimator decks at cards that do not recur.
  **The mapping changed ZERO stored tags, and that is the forage lesson at full strength.**
  All 14 cards state the template without reminder text ("Exile this card from your
  graveyard: Put a +1/+1 counter …"), so the TEXT rules already earned both tags —
  `tag_synergies --merge` tagged 0 rows and no pool row would change. The mapping's real
  job is to DECLARE the mechanic: that silences the radar, and it permanently exempts the
  keyword from `is_noise_keyword`, which matters the day a set ships with only one renew
  card. Note a mapped keyword KEEPS its literal tag (`forage` does too) — mapping adds the
  themes, it does not replace the name.
  **`triple` is not a mechanic at all** and must not be themed: Scryfall is surfacing the
  ordinary WORD from "deals triple that damage" (Fiery Emancipation, City on Fire) and
  "Triple target creature's power" (Tifa's Limit Break). Three unrelated cards, no shared
  template. Its sibling **`double` appears on the very same card and was already in
  `keyword_baseline.txt`**, so `triple` goes there beside it — following the precedent
  rather than inventing a theme. It is baselined rather than denylisted because
  FLAVOR_KEYWORDS is for card-UNIQUE flavor ability names, which a common English word is
  not.
  The lesson worth keeping: **a standing warning is a decision nobody has made yet.** These
  two fired on every `check_all` run for several cycles, which is the saturation failure
  this file documents elsewhere — a channel that always fires reads as working, and a
  genuinely new mechanic arriving beside them would have been invisible.
- **`forage` was THEMED rather than baselined, and the 7-of-9 split is the lesson.**
  It is a COST — "exile three cards from your graveyard or sacrifice a Food" — so it maps
  to `["graveyard", "food"]`, the two resources it consumes. Deliberately NOT `sacrifice`:
  the keyword only means the card MAY pay with a Food, and the cards that really do
  sacrifice earn that tag from their own text. **Mapping it changed only 2 of the 9
  forage cards**, because the other 7 quote the reminder text — which contains the words
  "graveyard", "sacrifice" and "Food" — and so already earned the tags from the TEXT
  rules. The two that changed (Traverse Valley, whose entire text is "Kicker—Forage.",
  and Euru, Acorn Scrounger) carry the keyword with no reminder, and were tagged neither.
  So a text-only tag model looks like it works on this mechanic right up until it meets a
  card that states the keyword bare — the keyword map is what covers that tail, and the
  gap is invisible unless you check the cards whose text OMITS the reminder. Note the
  graveyard side EMPTIES the yard; the tag can't express direction, and that asymmetry is
  the zone-conflict detector's job (`_GY_HATE_*` / `_GY_NEED_*`), not the tag model's. Card-*unique* flavor ability
  names (Firaga, Wave Cannon, Murasame, and the Marvel signature moves — Trick Arrows,
  Radar Sense, Technopathy, …), which Scryfall also reports as keywords, are dropped
  via the `FLAVOR_KEYWORDS` denylist so they don't pollute the tags.
  **Triage a new set's keywords promptly, and triage on the right axis.** When MSH
  shipped, its 27 signature moves went unindexed: `check_all` emitted 27 soft warnings
  on EVERY run — saturating the one channel the radar exists to use — and 11 leaked
  into the Synergies vocabulary, where `lib.pool_ability_model`'s tag-idf scored a
  one-card tag as near-maximally distinctive and inflated those cards' `Uq`. The test
  is **card-uniqueness across the POOL, not the collection**: `jump` reads as one
  *owned* card but Kain and Freya both carry "Jump — During your turn, ~ has flying",
  so it is a real mechanic and belongs in the baseline, NOT the denylist. Both
  directions are guarded — `check_keywords.check()` flags an unindexed keyword,
  `check_keywords.flavor_overreach()` flags a denylisted word that turns up on ≥3
  owned cards, is ALSO mapped in `KEYWORD_THEMES`, or is named in `deck.ENGINE_THEMES`
  as a real engine mechanic. That last cross-check exists because `harmonize` — a
  graveyard self-recursion keyword deck.py counts as a graveyard ENABLER — sat
  denylisted for a full cycle: the collection holds exactly ONE Harmonize card, so the
  owned-count signal could never reach the threshold. **Card-uniqueness is judged across
  the POOL, and a keyword another subsystem already treats as a mechanic is never flavor.**
  That rule is now MECHANICAL rather than hand-kept: `tag_synergies.is_noise_keyword`
  drops a keyword carried by exactly ONE card in the corpus, so a new set's signature moves
  are suppressed with no code change. It engages only when `card-mana.csv` is POOL-scoped
  (`build_mana.py --pool`) — at library scope a pool-wide mechanic can sit on one owned
  card (harmonize did), so below the corpus floor it falls back to the explicit list rather
  than guess. A keyword in `KEYWORD_THEMES` or named in `deck.ENGINE_THEMES` is never
  suppressed. `FLAVOR_KEYWORDS` remains an override for what the corpus can't settle, and
  `check_keywords.known_keywords()` counts the heuristic's drops as known so the radar
  doesn't re-report them as new mechanics.
- **`tag_synergies.py` text-tags fixing + topdeck-value engines** so they stop
  hiding under `selection`/`tokens`: "cast/play … from the top of your library" →
  `card advantage` (Vizier of the Menagerie, Realmwalker, Bolas's Citadel); "spend
  mana of any type / as though it were any color" → `ramp` (Vizier, Fist of Suns);
  a card that makes a **`land token`** → `ramp` (the regex requires the phrase *land
  token* directly, so a creature token whose ability merely mentions "land" — Gysahl
  Greens, Fat Chocobo — isn't mis-tagged); and a card that turns lands into **"every/
  all/each basic land type"** → `mana` (rainbow fixing: Overlord of the Hauntwoods'
  Everywhere token, Energybending) — so these surface on ramp/value in `suggest` /
  `suggest-homes` / `cuts` instead of hiding under `tokens`. **The residual is now
  mostly closed for detectable fixers:** a card whose fixing value SCALES with the
  target deck's color count used to mis-grade as *role-player* when it was really
  KEY, so `suggest-homes` now applies a **color-count-aware fixer overlay**
  (`_is_color_fixer` + `_fixer_rate` + `_fixer_boost`, guarded by `check_suggest`
  anchors 6 and 15) — a rainbow fixer reads **KEY in a 4+-color deck / role-player in a
  3-color one** (Overlord → decks 17/21a, previously role-player/tangential). The
  remaining residual is only a fixer whose value scales with color count but whose text
  lacks an explicit any-color / basic-land-type cue (so `_is_color_fixer` can't see it)
  — grade those from full text (why the shortlists print "grade from text").
- **The fixer overlay recommended cutting the BETTER fixer, and it took three separate
  blind spots to do it.** `suggest-homes "Guy in the Chair"` ({2}{G}, `{T}: Add one mana
  of any color`) rated it **KEY at fit 70 for deck 13** and proposed cutting **Prismatic
  Undercurrents**; for deck 17 it proposed cutting **Bloom Tender**. Both incumbents are
  strictly better fixing than the card being added. Every gate was green throughout,
  because each piece was individually correct.
  (1) **A TAG GATE made the predicate a hostage of the keyword map.** `_is_color_fixer`
  required `ctags & {ramp, mana}`. Bloom Tender (`{T}: For each color among permanents
  you control, add one mana of that color`) and Prismatic Undercurrents (fetch X basics,
  X = your colour count) both key off **Vivid** — which sits in `keyword_baseline.txt` as
  acknowledged-but-unindexed and therefore tags `vivid`, matching nothing. So the two
  best fixers on the roster read `is_fixer=False` while a mediocre dork read True. The
  fix reads TEXT ONLY; the strictness the tag was standing in for now lives in requiring
  **mana / land-type context**, so "protection from the color of your choice" still fails.
  The general lesson: *a predicate gated on a derived tag inherits every hole in the
  tagger* — and `keyword_baseline.txt` is a list of known holes.
  (2) **The boost read only the deck's colour count, never what the fixer BUYS.**
  Overlord of the Hauntwoods (a permanent land token with every basic land type) and Guy
  in the Chair collected the identical +16 and the identical automatic KEY. `_fixer_rate`
  splits **BROAD** (several colours at once, a mass grant, or colour-agnostic spending
  permission — full value at any cost) from a **SINGLE** any-colour source (discounted by
  mana cost, floored, never zero), and the KEY promotion is gated on `_FIXER_KEY_RATE`.
  Guy in the Chair drops to role-player; Bloom Tender / Prismatic Undercurrents / Vizier /
  Enduring Vitality all rate 1.0 and read KEY.
  (3) **`_weakest_cut` was computed BLIND to the card being added** — the caller asked
  only "what is this deck's weakest card". The keep-score is theme-fit + role credit and
  NEITHER has a fixing term, so a fixer (few tags, no classified role) sorts to the TOP
  of the cut list in exactly the multi-colour decks that need it. It now takes
  `add_is_fixer` and excludes incumbent fixers when the add is one: swapping fixing for
  fixing is a wash, and the ranking cannot see which is better. Deliberately NOT a
  general same-role exclusion — removal and card advantage already reach the keep-score
  through `_role_credit`, so excluding those would double-count. Fixing is the resource
  the score is blind to, which is why it needs the guard.
  **Two process notes worth keeping.** The roster-wide before/after diff (CLAUDE.md's
  own rule for pattern edits) was load-bearing *twice*: the first sweep silently dropped
  **38 real fixers** by omitting `any one color` / `any of the exiled card's colors`, and
  it added **190** by counting a **Treasure token's parenthetical REMINDER text** ("It's
  an artifact with `{T}, Sacrifice this token: Add one mana of any color.`") — which would
  have made ~150 pool cards read as manabase fixers, the saturation failure again. Reusing
  `_REMINDER_RE` fixes the second; Chromatic Sphere states the same ability as REAL text
  and correctly survives. Net after both corrections: 304 → 377 recognised fixers, and
  `check_all` output is byte-identical (the overlay is scoped to `suggest-homes`). And
  **anchor 6 had to be rewritten, not extended** — it asserted that rainbow text with no
  fixing tag must NOT qualify, using *Overlord's own ability* as the negative example. The
  anchor was pinning the bug. When a gate blocks a fix, check whether it encodes the
  intent or merely the old implementation.
- **`tag_synergies.py` text-tags LIFE AS A COST (`pay life`) — an entire archetype the
  tag model could not see.** 351 pool cards (2.2%) spend YOUR life for an effect and none
  carried a tag for it, so deck 42's whole thesis was invisible: Dark Confidant, the most
  on-thesis card available for an Orzhov life-as-currency deck, read `tangential` in
  `suggest-homes` on a shared creature type. Scoped to YOU losing life — "each opponent
  loses 2 life" is a DRAIN effect, the opposite card — with a payoff side ("whenever you
  lose life", "if you've lost life") the way `lifegain` also tags cards that only CARE.
  At 2.2% it reads as a SPECIFIC theme, which is the point: deck 42 now reads KEY.
- **`tag_synergies.py` text-tags HEIST (`heist`) — casting cards you don't own.** 82 pool
  cards (0.52%), so it reads as maximally SPECIFIC to the idf model: right for a build-around
  and well clear of the 4-card floor that got a `clone` tag rejected. Before it existed, the
  spine of a theft deck was invisible — Dream Harvest, Outrageous Robbery, Kotis, Laughing
  Jasper Flint and Rakdos, the Muscle all carried a blank or near-blank Synergies cell.
  **CHECK `MECHANIC_RULES` FOR THE NAME BEFORE ADDING A THEME.** The first draft was called
  `theft` — which was already taken by the "gain control of" rule (Act of Treason, Agent of
  Treachery, stealing a permanent already on the battlefield). Reusing the name silently
  UNIONED the two: 93 gain-control cards merged in, taking the theme from 81 to 174 cards and
  destroying exactly the specificity that makes an idf theme useful — **and `check_all` stayed
  green throughout, because a tag collision breaks no invariant.** The two effects are
  mechanically different and a deck built on one is not helped by the other, so they stay
  separate tags (`heist` = cast their card, `theft` = gain control of their permanent).
  Matching needs TWO parts with a BACKWARD PROXIMITY window, because the cast clause and the
  opponent's zone usually sit in DIFFERENT SENTENCES ("…exiles the top card of their library.
  You may cast it") — a same-sentence regex structurally cannot see the commonest templating.
  Both halves are required so the large self-exile families (impulse, foretell, adventure,
  plot) stay out. Four pattern bugs surfaced while building it, every one found by reading
  real cards rather than testing the regex against strings written to match it: `(?:cast|play)`
  without `\b` matched the `play` inside "each PLAYer … from their graveyard" (13 graveyard-HATE
  cards tagged as heists); `(?:an?|each|that )?` carried a trailing space on `that ` but not
  `each`, so "from EACH opponent's graveyard" never matched; the zone pattern assumed one word
  order and missed "from THE TOP OF target player's library"; and the opponent-subject branch
  let its gap cross a comma, so "if an opponent lost life this turn, exile the top two cards of
  YOUR library" read as a heist. All three patterns are registered with `check_patterns.py`.
- **`tag_synergies.py` text-tags SELF-EXILE CASTING (`exile cast`) — the sibling theme to
  `heist`.** `heist` is deliberately narrow (cast a card that was THEIRS), and that
  narrowness left a real archetype untagged: the impulse / Warp / Plot / Foretell / Adventure
  family casts from exile too, and the payoffs ("whenever you cast a spell from exile",
  "spells you cast from exile cost {1} less", "cast a spell from anywhere other than your
  hand") reward BOTH halves. 266 pool cards, 1.68% — specific by the idf model, and it is
  what makes decks 45/45a gradeable as a single archetype rather than a pile of unrelated
  exile cards. `is_exile_cast_text(type_line, text)` treats an **Adventure type line** as an
  automatic enabler (the mechanic IS cast-from-exile, and no oracle phrasing states it), then
  matches `_EXILE_CAST_ENABLE` (the keyword family) or `_EXILE_CAST_PAYOFF`. Kept SEPARATE
  from `heist` on purpose — the two only look alike; a deck built on casting your own exiled
  cards gets nothing from an opponent's graveyard, which is exactly the mistake the
  `theft`/`heist` collision taught.
- **`keyword_frequencies()` counts DISTINCT CARDS, not rows.** It backs
  `is_noise_keyword`'s one-card-in-the-corpus test, and the mana file stores a DFC under its
  full `Front // Back` name while other tables key the front — so a two-faced card could
  contribute two rows and clear the "carried by exactly one card" floor without a second
  card existing. "Goblin Formula", a genuinely card-unique flavor keyword, escaped the noise
  filter that way. Front-names are collapsed into a set before counting.

- **Three phrases where `tags_for` and `classify_roles` disagreed on the SAME text**, each
  leaving a card with a completely blank Synergies cell and therefore invisible to every
  tag-based recommendation. All three are ALIGNMENT fixes, not new concepts: `draw cards
  equal to` → `card draw` (The Ten Rings sat in a deck untagged), `gain(s) life equal to`
  → `lifegain` **and** the Lifegain ROLE (Exsanguinate read no roles at all; 68 pool
  cards), and `costs {N} less` → `cost-reduction`, which already existed on 167 pool cards
  but only ever arrived via the KEYWORD map (affinity/delve/warp/sneak/plot), so a card
  that plainly SAYS it costs less had nothing. Pool blanks 417 → 384. **Deliberately NOT
  fixed:** a `clone` tag for the four remaining "becomes a copy of" cards — that would be
  a new theme for four cards rather than an alignment. The residual 384 is a long tail of
  genuinely un-themeable effects (Oust, Exploration, Wish).
- **`tag_synergies.py` also text-tags MECHANICAL-SYNERGY payoffs the keyword map missed
  (tagging-misreads fix)** — the class of fit the tag model was blind to because it saw a
  card's own keywords/subtypes but not what its TEXT rewards: **`toughness matters`**
  ("assigns/deals combat damage equal to its toughness", Doran-style — Bark of Doran +
  Kingpin, so a toughness-swap payoff isn't a bare `equipment/pump` body); **`noncombat
  damage`** (the literal phrase — Hawkeye/Ojer Axonil amplifiers + the "whenever a source
  deals noncombat damage" draw engine — PLUS a repeatable **pinger**: a PERMANENT, not a
  one-shot instant/sorcery burn spell, whose ability deals damage to a player / any target
  / each opponent, so a ping-ENGINE deck reaches critical mass on the theme while a couple
  of burn SPELLS can't fake it into any aggressive deck; combat-damage triggers excluded);
  **`spell copy`** (Pyromancer's Goggles); and a
  **tribal-matters PAYOFF** tag — a lord/tutor gets the creature TYPE it rewards even when
  it isn't that type itself ("Dinosaurs you control" / "search for a Dinosaur card" →
  `Dinosaur`, so Huatli reads KEY in a Dino deck, not role-player). The tribal scan runs on
  ORIGINAL-case text (MTG capitalizes real tribes but lower-cases generic "creatures/lands",
  a strong natural filter) with a `_NON_TRIBE_WORDS` denylist for sentence-initial capitals.
  **These sub-themes surface even as a SECONDARY payoff:** they'd otherwise sit below the
  25%-of-top-theme centrality cutoff in a deck with a dominant theme (toughness-swap with
  only Kingpin+Bark; noncombat-damage with 2 cards under a heavy Wizard theme), so
  `_central_themes` admits the curated `_MECHANIC_SUBTHEMES` set (`toughness matters` /
  `noncombat damage` / `spell copy`) at a **flat floor of 2** — the specific-effect analog
  of the `#: protect:` signature rescue (a real 2-card payoff sub-synergy reads central,
  while a GENERIC theme at the same low weight STAYS gated behind the 25% cutoff, so the
  relaxation can't fake a generic overlap into a home; guarded by `check_suggest` anchor 12).
  So Bark → 20a/20b and Hawkeye → the ping decks now auto-surface. A tribal payoff clears
  the plain cutoff easily (a Dino deck runs ~19 Dinosaurs). After editing these
  patterns, regenerate BOTH derived tag stores: `tag_synergies.py --merge` for the
  LIBRARY, and **`build_pool.py --all` for the pool** — which re-derives every pool row's
  `Synergies` through the same `tags_for()`. Do NOT point `tag_synergies.py` (or
  `enrich.py`) at `card-pool.csv`: both write through `lib.write_rows`, which emits only
  the canonical 8 LIBRARY columns, so it silently dropped the pool's `Rarity` /
  `Legalities` / `Released` and broke every format filter, rotation flag and wildcard
  price (audit F-02). Both now refuse a non-library target up front
  (`lib.csv_schema_error`), and `check_all` fails if a derived file loses its own
  columns. Skip the pool rebuild and UNOWNED craft candidates read stale pool tags.
- A few genuinely text-less vanilla creatures trip validate's blank-Card-Text
  warning (expected, not an error).
- The **functional-role** breakdown (`deck.py stats`) and **castability lint**
  (`deck.py mana` / `check`) are heuristic. Roles are matched from oracle text, so
  modal cards land in several buckets and single-draw cantrips are deliberately
  *not* counted as card advantage. Because regex matching inevitably misses
  phrasings and silently *under*-counts, `stats` and `tier` run a **coverage
  self-audit** (`role_coverage_flags`, F15): a broad lexical net flags any card
  whose text reads like interaction / card advantage the classifier *didn't* tag,
  printing a "⚠ Possible UNDER-COUNT — verify" list so a miss is explicit, never
  silent. It only prompts a human read; it never changes a count. **That net is now
  built as a strict SUPERSET of the precise patterns** (`_INT_CUE_PATS` /
  `_CA_CUE_PATS` union the compiled role regexes in), because a phrasing used to be
  missable by BOTH — Repulsive Mutation's "counter up to one target spell unless…"
  was too narrow for the Counter pattern *and* absent from the net, so the
  under-read was invisible to the audit that exists to catch under-reads.
  **A hands-on session found the under-count was much larger than "a residual":**
  three cards that unambiguously interact scored ZERO roles, and one deck read
  interaction 3 against a hand count of 7. All are fixed and unit-tested — removal
  now matches a permanent-type LIST (`destroy target artifact or enchantment`,
  `destroy target artifact, enchantment, or creature with flying` — previously
  unmatched by the hand-kept alternation), a counter accepts `up to N target`,
  library-TUCK removal counts (`shuffle … target creature … into their owners'
  libraries` — Floodpits Drowner leaves the battlefield, so it IS an answer), and
  card advantage covers `five` / `half X`. Conversely a **LOOT** (`draw N, then
  discard N`) is no longer card advantage: it's card-neutral, the same reason a
  single-draw cantrip is excluded. Roster impact when this landed: 26 of 56 decks
  gained interaction, 2 lost card advantage (both Kiora), 6 metrics floors moved
  B→A. **When editing these patterns, run a roster-wide before/after diff** — a
  bare `{0,2}` inside an `rf"…"` regex silently compiles to the literal `(0, 2)`,
  and only that diff caught it (46 decks had lost all "destroy target creature").
  **`check_patterns.py` now catches this class mechanically** (a hard `check_all` gate):
  every card-text pattern must match ≥1 pool card, and no pattern source may hold a
  tuple repr. Run the diff anyway for anything that changes a COUNT — the gate proves a
  pattern is alive, not that it matches the right cards.
  **A SECOND sweep, driven by reading the audit's own output, was larger still** —
  proof the coverage list is worth actually working through rather than glancing at.
  The big one: the bounce pattern spelled `(?:owner|their) hand`, which requires the
  literal text "owner hand", while MTG writes "to its **owner's** hand" — so EVERY
  unconditional bounce spell in the collection scored zero roles for the entire life
  of the pattern (note `owner'?s?`; this is the same class of typo as the `{0,2}`
  one). Six more templatings were missing: EDICT (`target opponent sacrifices a
  creature of their choice` — it answers hexproof), X-damage removal (the fixed
  patterns all demand a DIGIT), the Aura form of the library tuck, mass edict (`each
  player sacrifices all other creatures`) → Sweeper, a REPEATABLE upkeep draw →
  Card advantage (the cantrip exclusion is about ONE-SHOT single draws; Phyrexian
  Arena accrues every turn), and fixed damage to each opponent → Burn/drain. Roster
  impact: 34 of 58 decks moved, all upward — interaction 415→464, card advantage
  104→112, unclassified 174→157, under-read 48→10. Deck 22 re-graded C→B on it, and
  ten more decks had stale figures in their `#: tier:` prose corrected.
  **A THIRD under-count sat in the CARD-ADVANTAGE half, and it is the one case so far
  that NO uncertainty channel could reach.** The repeatable-draw rule above was added as
  a single pattern keyed on the literal word **`upkeep`** — but repeatability comes in
  two templatings, and that pattern read only one. A **PHASE** trigger recurs every turn
  and Magic writes it on the end step, the draw step and combat as readily as the upkeep
  (Haliya, Guided by Light draws at the beginning of your END STEP); and a **`WHENEVER`**
  trigger recurs by construction (Exemplar of Light draws every turn it gets a counter).
  Neither matched the precise pattern NOR the broad `_CA_CUES` net — the "missable by
  BOTH" failure the superset property exists to prevent — so deck 46 reported card
  advantage 1 against a real 3. **The reason it was invisible is worth keeping:** both
  cards DID match a role (Payoff, Lifegain), so `unclassified` — which by definition only
  names cards matching NOTHING — could never reach them, and `under_read` fires per-axis
  but is driven by the same cue net that missed them. A card sorted into the *wrong*
  bucket is therefore harder to detect than one sorted into no bucket at all. Found by
  hand-counting a deck's draws while drafting it, not by any gate.
  **The fix is a DISCRIMINATION problem, not a widening one, and the roster diff is what
  proved it.** A naive `whenever .* draw a card` took the pool from 777 card-advantage
  cards to 1200 — and **45 of those were the exact inverse of the role**: `Whenever you
  draw a card, <effect>` (Chasm Skulker, Orcish Bowmasters, Queza) puts the draw in the
  CONDITION, so the card CARES about drawing and does not draw. Scoring a draw-PAYOFF as
  a draw is backwards, and it is the same shape as the `theft`/`heist` tag collision.
  Magic templates a trigger as `Whenever <condition>, <effect>`, so requiring the draw to
  fall AFTER the comma separates them; final count 1163. **`When` vs `Whenever` is the
  other load-bearing distinction** — "When this creature enters, draw a card" is a
  one-shot ETB cantrip (Inspiring Overseer) and stays excluded, which is the cantrip rule
  this pattern implements rather than an oversight. Roster impact: 38 of 64 decks moved,
  **all upward**, median card advantage 1→2.5 (not saturated — 5 decks still read 0 and
  the max is 12); three metrics floors moved (38 and 38a C→B, 42a B→A); no deck landed
  ≥2 bands off its claimed letter; and **15 decks had a stale card-advantage figure in
  `#: tier:` prose**, every one an under-statement. Note 42a now sits one band BELOW its
  floor by deliberate choice, which the guard permits and does not nag about.
  The coverage net also **strips parenthetical REMINDER text** before matching, because
  Ward's reminder ends "…counter it unless that player pays {2}" and was reporting every
  warded creature as a missed interaction piece. A FALSE cue is the expensive kind of
  error here — the list exists to be read card-by-card — and the strip cannot create a
  blind spot, since the net contains the precise patterns and the flag only fires when
  NO role was tagged.
  The interaction / card-advantage counts are computed by ONE canonical
  `role_tally` (F13) — quantity-weighted, a card counted once per axis, basics and
  nonbasic lands skipped — that `stats`, `audit`, and the `quality`/`tier` vectors
  all route through, so the number you eyeball in `stats` is the number the tier
  floor grades on (three separate counters used to disagree by ±1). It also returns
  **`protection`** (see below). The lint reads the deck's `#: colors:` header,
  so a stale or intentionally-narrow header flags cards as off-color — a header
  narrower than the deck's real card pool reads as multicolor strays. Fixing a stale
  header to the deck's real castable colors clears the false positives (e.g. deck
  `13` was corrected `GR`→`GWBR`). Treat a flag as signal to review, not a hard
  failure — it doesn't gate `check_all.py`.
  An identity stray now says WHICH KIND it is, in three cases: `(hybrid — paid
  on-color)`, `(off-color ability)`, or `(cost unknown — run deck.py mana …)`. The third
  exists because **`check` deliberately passes an EMPTY mana dict to stay offline**, and
  with no cost to read nothing can be shown to be hybrid-explained — so `check` would
  otherwise assert "off-color ability" for a card it cannot classify (false for deck 3's
  two R/W hybrids). It still COUNTS an unknown as actionable, so the offline path
  over-reports rather than silently clearing a deck; only the claim is softened to match
  the evidence. Run `deck.py mana` (which loads real costs) for the definitive read.

## Cycle Workflow Config

**Test Command:** `python3 scripts/check_all.py`
(deterministic integrity gate; exits non-zero on any hard invariant break —
NOTE it imports `deck` as a MODULE and calls `cmd_*` directly, so it never builds an
argparse tree — the CLI surface is covered separately by `tests/test_cli.py` and a
dependency-free smoke step in `.github/workflows/integrity.yml`; see the CLI gotcha
above —
INV-01…04 plus a **ranking-model sanity check** (`check_rankings.py`) that guards
the Doctor-Doom-class regression: a scoring change that silently reclassifies a
real tribal theme as "generic". The ranking check is distribution-based, so it
survives cards being crafted off the wishlist; it also carries a **wiring** anchor
asserting `_seed_power` reads an Arena wildcard LETTER and the matching rarity WORD
identically — deck.py's `cuts`/`redundancy` pass letters, and a mismatch silently
seeded every rare and mythic as an uncommon (audit F-01). Note INV-03 is now
existence **and schema**: a derived file that loses its own columns (a pool without
`Rarity`, a mana file without `Mana Cost`) is a HARD failure, since the old
existence-only check let a library-header rewrite pass green. Five more model-sanity checks are
also hard-gated: **color-parsing** (`check_colors.py`) locks in the F1/F2 fix (a
colorless card must not read as red; a slash-gold must pass the subset test) and a
static scan bans the naive inline `if ch in "WUBRG"` parse outside `lib.py` — in
**BOTH** its shapes, the comprehension AND the equivalent `for` STATEMENT, since the
scan originally tested only the comprehension node types and the same bug written as a
loop passed green (broad-scan F-07). It also rejects a **stale `_INLINE_PARSE_ALLOW`
entry** naming a file or function that no longer exists: an exemption for code that is
gone reads as a considered decision while covering nothing, and silently pre-grants a
pass to any future function that reuses the name — the same hand-kept-registry rot the
`check_patterns` completeness check exists for;
**DFC ownership-join** (`check_dfc.py`) guards the front/full-name convention — a
behavioral anchor that `lib.owned_qty` and its wrappers (`wishlist._owned_of`,
`pool.owned_of`) resolve an owned double-faced card by its front face, plus a static
scan that flags a raw ownership lookup bypassing `owned_qty` (the A3/A4/F6 class);
**suggest scoring** (`check_suggest.py`) keeps the needs-aware suggest/cuts terms
BOUNDED — the diminishing-returns role credit and the curve-gap factor can't
silently reorder a tuned deck (#1/#2), the suggest power co-signal never overrides
theme fit (#6), the `suggest-homes` rainbow-fixer boost stays bounded/capped
and zero below 3 colors while `_is_color_fixer` reads TEXT in mana/land-type context
(so an UNINDEXED mechanic like Vivid can't hide a real fixer, and a Treasure's reminder
text can't fake one) and `_fixer_rate` keeps a single any-color source discounted below
the KEY bar (anchor 6) — with anchor 15 pinning the WIRING half, that `_weakest_cut`
never proposes cutting a fixer to make room for a fixer, the CUTS power co-signal stays bounded/neutral-centered/
monotonic so it only breaks near-ties in the cut ranking (anchor 7), and the CUTS
ability-distinctiveness co-signal stays bounded/neutral-centered/monotonic (anchor 8,
which also proves the tag-rarity metric reads a vanilla card as ~0 and a rare mechanic
above a generic one, AND that the structural-text signal reads vanilla/plain-ETB/bare-mana
low while rescuing an unusual trigger, `card_distinctiveness` taking the max so structural
only ever raises), and the `suggest --lands` synergy + shortfall nudges stay bounded/
non-negative and fixing-dominant, favoring the deck's top theme / scarcest color (anchor 9),
and the NEEDS-model nudges (`--ramp` accel-want / restriction-fit, `--interaction` scaling
boost) stay bounded/rising-with-support (anchor 10), and `fit_strength` never credits a
bare BROAD-TRIBE overlap (`_GENERIC_TRIBES`: Human/Hero/Villain) as a KEY home — not as the
top theme nor via a `#: protect:` signature — while a narrow tribe and a specific theme
still read KEY (anchor 11, the Hawkeye-"KEY"-in-every-Hero-deck fix), and **anchor 11b
asserts the WIRING of that same demotion one category over** — `fit_strength` must be handed
the STRICT `_strong_signature_themes` (a theme carried by ≥2 `#: protect:` cards), never the
loose `_signature_themes` that unions every protected card's tags. With the loose set deck
37's signature held 25 themes (etb, removal, sacrifice, combat, tempo…), so Azula, Cunning
Usurper — a Human Noble Rogue — read KEY for three WIZARD-tribal decks on `Human, etb` alone;
roster-wide the loose set gave 99 KEYs where the strict set gives 54, and all 45 differences
were KEY→tangential. It HAS to be a wiring anchor: `fit_strength` is RIGHT to mint KEY from
any signature it is handed, because the rescue's whole point is that a generic theme IS a
signature when it is genuinely the spine (`counters` is in GENERIC_THEMES, and deck 30's
strict signature is exactly `{counters}`), so asserting the pure function returns
`tangential` for a generic signature would CONTRADICT the rescue — the strictness lives in
the CALLER and only reading the call site catches it. And the suggest-homes
curve co-signal (`_home_curve_fit`) stays a bounded/never-boosting SORT nudge while
`_central_themes` admits a curated mechanical sub-theme at floor 2 yet still gates a generic
theme (anchor 12, finding #5 + the secondary-payoff centrality fix), and — unlike every other
check in this suite — **anchor 13 runs the real ENTRY POINTS end-to-end** over a synthetic
deck+pool and asserts the OUTPUT ORDER (a mythic and a common differing ONLY in rarity must
not score the same power; an off-theme card must not be suggested; both breadth models must
agree). Pure-function anchors cannot see WIRING — F-01 shipped past eleven green gates
because `_cuts_power_adj` was provably bounded/monotonic while its CALLER handed the seed the
wrong rarity shape, so a model correct in every part was still wired up wrong (F-18). And
**anchor 14** keeps the suggest-homes DOUBLER term bounded — zero below
`_DOUBLER_MIN_SOURCES`, never above `_DOUBLER_CAP`, monotonic in feeder count — and pins the
two halves the term is worthless without: `doubler_axis` classifying tokens/counters/triggers,
and `doubler_restriction` reading a doubler's own "power N or less" scope (unrestricted
support over-counted Delney 6× and would have minted a false KEY); and **anchor 16** does
the same for the CUTS side of that signal — `_cuts_multiplier_adj` bounded, zero below
`_CUTS_MULT_MIN_SOURCES`, never negative, rising with support, plus the new LIFEGAIN axis
and its discriminator (a `plus 1 instead` replacement must NOT read as a doubler). Its
WIRING half lives in `tests/test_deck_models.py`, because the pure function was already
correct here — the bug was that `rank_cut_candidates` never called it;
**engine classifier** (`check_engines.py`) anchors the enabler/
payoff detection on canonical cards (#3); **tier floor** (`check_tier.py`) proves
the archetype-aware floor grades non-aggro decks identically to before and only
ever raises an aggro band (#4); and **dead patterns** (`check_patterns.py`) — THREE
checks over 145 registered patterns: every card-text classifier regex must match ≥1 card
in the ~15.8k-card pool, no pattern source may contain a Python tuple repr like `(0, 2)`,
and **every module-level compiled pattern in `deck`/`lib`/`tag_synergies` must be either
REGISTERED or explicitly EXCLUDED with a reason** (the COMPLETENESS check). This is the
gate for THIS PROJECT'S SIGNATURE BUG: a regex that compiles fine and can never fire. Both historical
instances shipped past every other gate — the f-string `{0,2}` that became the literal
`(0, 2)` (46 decks lost their interaction count) and `(?:owner|their) hand`, which
demands the text "owner hand" while Magic writes "owner's hand" (every bounce spell
scored zero roles). Unit tests structurally cannot catch these, because each pattern was
tested against a string its author wrote to match it; only a roster-wide diff did, and
only when someone remembered to run one. It found a THIRD on its first run — `costs {1}
less for each`, where Magic writes "costs {1} less TO CAST for each" — which was invisible
even to a diff, since a general pattern already covered those cards so no count ever
moved. Note the check must feed each pattern the text form it really runs against
(`norm` / `raw` / `window`): the case-sensitive tribal-payoff scan reads ORIGINAL-case
text and reads as dead against a lowercased corpus, while a **`window`** pattern is
`$`-anchored and run against a SHORT SLICE (`_POWER_SCOPE_*` read
`text[m.start()-25:m.start()]`), so it matches 0 of 15.8k WHOLE texts by construction —
registering those two naively would have failed the build on two healthy regexes. They
keep the corpus-free format-leak check and skip the live-corpus one.
**The COMPLETENESS check exists because the coverage list was hand-kept and had fallen
13 patterns behind the code** (broad-scan F-04): all five of `lib.structural_
distinctiveness`, every `_DOUBLER_AXES` matcher, `_DOUBLER_POWER_RE` and `_REMINDER_RE`
were uncovered. The structural-distinctiveness hole was the dangerous one —
`card_distinctiveness` returns `max(tag_score, structural)`, so a dead pattern there
silently collapses the structural signal to 0 and the `max()` HIDES it: no error, no
visible count change, `cuts`' `Uq` column quietly reverting to tag-only. Anything
deliberately left out is enumerated with a justification in `_EXCLUDED` (deck-file /
mana-symbol SYNTAX, and the tier-RATIONALE prose patterns, which read a human argument
rather than card text and are unit-tested in `tests/test_deck.py` instead). A new
pattern now fails the build until someone says what corpus it runs against — the same
lesson as the checks that could never fire: a hand-kept registry grows holes.
It also emits **soft, non-gating warnings**:
wishlist target drift — a card whose Target deck can no longer cast it
after a retune — via `wishlist.py --audit-targets`; and **new unindexed mechanics**
— `check_keywords.py` flags a keyword on an owned card that isn't in
`tag_synergies.py`'s map yet (a new set's mechanic), baselined in
`keyword_baseline.txt` so it stays quiet until something genuinely new appears
(`check_keywords.py --update-baseline` to acknowledge one); **FLAVOR_KEYWORDS
registry staleness** — `check_keywords.stale_registry_entries()` flags a
`FLAVOR_KEYWORDS` or `keyword_baseline.txt` entry matching NO card in the corpus (a
suppression with nothing behind it; both lists only ever grow, and nothing pruned them
when a set left the pool). Soft on purpose — it breaks no invariant — and skipped below
the corpus floor, where a pool-wide mechanic can legitimately sit on zero owned cards
(the `harmonize` case). A stale `_INLINE_PARSE_ALLOW` entry is HARD by contrast, because
it sits inside a hard gate; and **FLAVOR_KEYWORDS
overreach** — `check_keywords.flavor_overreach()` flags a denylisted "flavor" word
that's also theme-mapped, or one shared by several owned cards (likely a real
mechanic being suppressed, audit F24); **theme coverage** — `check_themes.py` flags
an owned card whose oracle text clearly plays a high-confidence theme (food, landfall,
proliferate, convoke, graveyard, lifegain, counters) it ISN'T tagged with (the theme
analog of `role_coverage_flags`; a stale/removed tag distorts every tag-based
recommendation), summarized to one line (#7); and **tier mismatch**
— `deck.py tier_consistency_issues()` flags a deck whose claimed `#: tier:` sits ≥2
bands above the tier its measurable quality vector supports (an inflated/stale
letter — see the Competitive Tiering rubric); and **stale flex lines** —
`deck.flex_staleness()` flags a `#~ -Out | +In` line whose cut card already left the deck,
which nothing else covered; and **stale tier rationales** — `deck.rationale_staleness()`
roster-wide. That last one is the lesson: the check EXISTED for a long time and nothing ran
it. `deck.py tier <id> --audit-rationale` could always find these, but only for one deck, on
demand, and the instruction to run it after every deck edit lived in CLAUDE.md prose that no
skill executed — so its two siblings swept the roster every run while it waited to be
remembered, and **13 stale figures across 10 decks accumulated with every gate green**. Same
shape as the dead-regex bugs: a check that cannot fire is not a check. It is now automatic
(and `/apply-changes` + `/tune-deck` run the per-deck form at the moment of the edit, where a
human is present to fix the prose). Soft warnings never fail the build.)

**The reference-table loaders are memoized** (`deck._file_memo`, keyed on each source
file's `(mtime_ns, size)`). `load_mana` / `load_card_data` / `load_card_meta` /
`load_collection` / `load_keywords` re-parsed their CSVs on EVERY call, and a roster pass
calls them once per deck — 65 × ~0.31s ≈ 21s of `check_all`'s runtime, and the reason a
roster-wide rationale sweep looked too expensive to run automatically, which is precisely
how the check above never got wired in. **check_all went 23s → ~5s including the new
sweep.** Two design points worth keeping: the decorator takes the module-global NAMES of
its files and resolves them per call, because `check_suggest`'s wiring anchor repoints
`deck.POOL_CSV` at a synthetic pool and a path captured at decoration time would key the
cache on the REAL file while the loader body read the synthetic one — a stale-cache bug in
the one check whose job is catching wiring mistakes; and the tables are now SHARED, so a
caller that needs to mutate one must copy it first (no caller does today — verified by
scanning `scripts/` for external mutation).

A **pytest unit layer** (`tests/`, run with `pytest` or `make test-units`, deps in
`requirements-dev.txt`) COMPLEMENTS this gate — fast, isolated tests that pin the
edge-case behaviour of the pure helper functions. It is NOT part of the Test Command
above (check_all stays zero-dependency); both run in CI via `.github/workflows/tests.yml`.

**Health Dimensions:**
- Data Integrity — CSV structure, no drift between library and derived files
- Enrichment & Tagging Accuracy — Scryfall-sourced fields and synergy tags
- Deck Tooling Correctness — deck.py / query.py / pool.py behavior
- Deck-Building Insight — mana (hybrid-aware), tribes, cost-nature, pool value
- Presentation & Interface — gallery/dashboard correctness and freshness, plus the
  interface layer `/broad-scan` Stage 3 grades structurally (keyboard/assistive
  access, empty-loading-error states, responsive posture, theme-token completeness,
  feedback on failure) across dashboard.html, gallery.html, templates/ and app.py
- Documentation Currency — README / CLAUDE.md match the code and data

**Subsystems:**
- Data: card-library.csv, card-pool.csv (+ Power/Toughness), card-mana.csv, card-wishlist.csv (+ Power Source provenance), matches.csv (played-match record; created on first `/log-matches`, absent until then — deliberately NOT an invariant, since a repo with no logged games is healthy), recommendations.csv (recommendation-outcome ledger; same treatment — accrues from `swap --apply`, absent until the first swap)
- Outcomes: scripts/parse_matches.py (Arena `Player.log` → matches.csv, `/log-matches`) — the ONLY subsystem that has seen a game; recommendations.csv + `deck.py feedback` (the recommendation ledger — how `cuts`/`suggest` scored against the swaps you actually applied; written by `swap --apply`, report-only, never fed back into a score). Every other model grades a deck on its LIST; `#: tier:` is a human competitive judgment with no outcome data behind it, which is why the rubric leans on measurable proxies.
- Ingest & Enrich: scripts/import_arena.py, scripts/import_collection.py (authoritative full-collection tracker import — sets exact counts including DOWN), scripts/verify_ingest.py (reads a paste BACK against the library — present? at the expected count? covered by card-mana.csv? — because every failure mode here is a silent undercount and `check_all` structurally cannot see one: a card that never arrived breaks no invariant), scripts/enrich.py, scripts/tag_synergies.py, scripts/build_pool.py, scripts/build_mana.py, scripts/reconcile_crafts.py, scripts/sheets_sync.py, scripts/scryfall.py (shared resilient Scryfall client), scripts/lib.py
- Analysis: scripts/deck.py, scripts/query.py, scripts/card.py, scripts/pool.py, scripts/wishlist.py, scripts/validate.py, scripts/check_all.py, scripts/check_rankings.py, scripts/check_keywords.py, scripts/check_colors.py, scripts/check_dfc.py, scripts/check_suggest.py, scripts/check_engines.py, scripts/check_tier.py, scripts/check_themes.py, scripts/check_patterns.py, scripts/check_commands.py, scripts/keyword_baseline.txt (acknowledged-but-unindexed mechanics, read by check_keywords.py)
- Presentation: scripts/build_gallery.py, gallery.html, image-manifest.json, scripts/build_dashboard.py, dashboard.html, .github/workflows/pages.yml (Pages deploy), scripts/app.py (optional Flask editor), templates/, Makefile (`make app` launcher / `make check` / `make refresh` — the ONE executable definition of the derived-data rebuild order). The dashboard now also renders a **Recently edited** panel (repo→Arena sync: last-edit date + commit changelog + card-level delta, with a last-edit / net·7d / net·30d "since" toggle — from git, needs `pages.yml` fetch-depth: 0) and a **Standard rotation** panel. The deck grid groups into per-format shelves (Standard / Brawl / Alchemy / …) when the roster spans more than one format, and **nests variant decks under their core** — a core deck's same-format variants render as an always-visible `↳ Variants (N)` strip inside its card (id + name + build-status per row, click opens the variant's modal), so they're clearly grouped yet never hidden; searching a variant still surfaces it as its own card, and a cross-format variant (e.g. `3-brawl`) stays standalone in its own format shelf (families are built per shelf). The page is **mobile-responsive** (single-column grids, wide data tables scroll in-box, a horizontally-scrollable section-nav) and uses **progressive disclosure**: every section collapses — the utility ones (card finder / stale-check / recently-edited / rotation) default CLOSED — a sticky **section-nav strip** jumps to and auto-expands a section with a scroll-spy highlight, and the long lists (wishlist tiers, crafting leverage) cap at ~12 rows with a *show all* toggle while the roster-triage table defaults to the ACTIONABLE decks (the page analog of `deck.py audit --flagged`). The **wishlist** filters by free text (card/target/signal) AND by **wildcard rarity** (M/R/U/C chips, multi-select, mirroring `wishlist.py --rarity`). All of this is template-only (the `#data` island is untouched) and persists in `localStorage`.
  The EDITOR's colour filter (`templates/collection.html`) follows the dashboard's chip
  contract verbatim — `role="button"` + `tabindex` + `aria-pressed` + Enter/Space, per
  `build_dashboard.py`'s `a11y()`. It is the same control, so a second interaction
  contract would be a drift bug, not a style choice; the key handler routes through
  `.click()` rather than re-implementing the toggle, for the same reason. Its focus ring
  is an `outline`, never the border — `.pip.on` already uses border-color for the ACTIVE
  state, so sharing it would make focused and selected the same pixel. Pinned by
  `tests/test_templates.py`.
  The DECK editor's analysis tabs (`templates/deck.html`) had the identical defect and
  the identical fix — bare `<span class="tab">`s with a container click handler, so all
  four were mouse-only — plus the ARIA structure the dashboard's own tabs still lack:
  `role="tablist"` on the strip and `role="tabpanel"` on the output (a `role="tab"`
  outside a tablist is invalid ARIA). The output `<pre>` is focusable because it
  scrolls. Both editor pages carry a `<main>` landmark and a `:focus-visible` rule
  wherever they style `:hover`. **Auditing the SIBLING templates is what found this** —
  the pip fix named one file, and the same bug was sitting two files over.
- Testing: tests/ (pytest unit layer over the pure helpers — tests/test_templates.py is the MARKUP-CONTRACT layer over `templates/`, stdlib-`html.parser` only and deliberately NOT a browser test: what a file CAN prove is whether a control is a control at all — role, tabindex, an accessible name, a key handler, `aria-pressed` kept in sync, and a focus ring that uses `outline` rather than the border `.pip.on` already claims. A `<div>` with a click handler and none of those is invisible to a keyboard and to assistive tech, which is how the editor's six colour pips stayed mouse-only through six deferrals of the I-01 fix with every gate green; the perceptual half stays a human walk (Regression Scenario 7); tests/test_cli.py is the CLI ENTRY-POINT layer, the one surface no other gate touches: `--help` on every script in `scripts/` (32 today, listed dynamically) plus every deck.py subcommand, asserting no traceback and that argparse scripts exit 0 with usage (F-01/F-12); tests/test_check_commands.py pins the workflow-coverage gate (an unreachable subcommand is reported; a prose mention does NOT count as coverage; a stale or unexplained INTERACTIVE_ONLY entry fails; /roster-review drives the five roster commands and /ingest routes all four ownership writers); tests/test_deck_models.py is the ANALYSIS-MODEL layer — deck_quality_vector (the F10 guard's core, which had no direct test at all), tier_gap, legality_report, interaction_profile, effect_redundancy, deck_needs, deck_role_counts, the pure helpers, and the eight POOL-backed models (owned/craft_role_fillers, functional_theme_options, suggest_lands/mana/interaction, audit_roster, brawl_readiness) — all against a SYNTHETIC card universe and a synthetic pool, so they assert the model's contract rather than the current roster's numbers. Its pool carries a deliberately NON-Standard card and a DFC, because the two `owned_role_fillers` bugs need exactly those: the missing format filter (the owned half of `tier --to` skipping the check its craft sibling applied) and the double-faced row printed twice (`load_card_data` keys a DFC under both its full name and its front face, same display name on both). It also holds the cuts MULTIPLIER wiring anchor — `_cuts_multiplier_adj` being bounded and monotonic says nothing about whether `rank_cut_candidates` calls it, and it did not; the test compares the SAME doubler's keep-score across two decks (with and without feeders) so every other component is held constant. That closes the layer: 21 analysis functions had no direct test, now 0; tests/test_check_patterns.py pins the dead-pattern gate on both historical bug shapes, plus the COMPLETENESS check (an unregistered pattern is reported; structural_distinctiveness and the doubler axes are covered; every `_EXCLUDED` entry names a real attribute) and the `window` corpus form (a `$`-anchored slice pattern matches 0 whole texts and must be exempt); tests/test_deck.py is the DECK-ANALYSIS helper layer (the biggest file, and the default home for a `deck.py` pure function) — front_face_cost / mana_value (split-Room-Adventure front-face costs), flex_staleness, the rationale figure audit (the bare-`over` false negative, `_ARROW_AFTER` transition notation, `_figure_is_history` — the `removal`/`craft target` domain-vocabulary suppressions plus the `a 2.44 curve` house phrasing — and the third sweep's three pattern holes: parenthesised figures, number-first figures, `early_drops` with no pattern at all, plus both false-positive classes the sweep produced, the `(N)`-must-close breakdown rule and the quoted-span suppression), the tag/role alignments (`draw cards equal to`, `gain life equal to`, `costs {N} less`, `pay life` scoping); tests/test_lib.py is the SHARED-PRIMITIVE layer over `lib.py` — the accessors every other model routes through, so a regression here is roster-wide: card_colors (the F1/F2 colourless-reads-as-red parse), card_power, owned_qty (the DFC front-face ownership join), distinctiveness_score (tag-rarity, tribe/evergreen-excluded), structural_distinctiveness (oracle-text-shape rescue), card_distinctiveness (max-combine) and _creature_subtypes; back in test_deck.py, parse_pips, role_tally, tier_band, engine_roles, rotation math, _reuse_bonus, hypergeometric consistency math, _cuts_power_adj, _cuts_uniq_adj, _land_synergy_bonus / _land_shortfall_bonus (bounded manabase-recommender nudges), _accel_want / _ramp_restriction_fit / _int_scaling / _int_scaling_boost (needs-model signals), _produces_mana, plan_redundancy_fill (virtual-copies-first), _pips_castable (hybrid-aware target audit), fit_strength (specific-theme-gated KEY + broad-tribe demotion), _home_curve_fit (bounded suggest-homes curve nudge), the color-fixer overlay (_is_color_fixer reading TEXT not tags so an unindexed mechanic can't hide a fixer, the Treasure-reminder exclusion, _fixer_rate's broad-vs-single cost discount, and _weakest_cut refusing to cut a fixer for a fixer), pip_depth_warning / deck_color_sources (the colored-pip DEPTH flag the identity-subset castability test can't see), doubler_axis / doubler_restriction / doubler_support / doubler_boost (the bounded deck-magnitude co-signal for doublers, incl. the LIFEGAIN axis and the plus-N-is-not-a-doubling discriminator), _cuts_multiplier_adj (the cuts-side multiplier term: bounded, zero below the floor, never negative), strict_upgrades (`screen`'s text-containment upgrade test — the extra clause, the non-symmetry, identical-text-is-redundancy, the empty-clause guard against a vanilla incumbent, and the cost ceiling), _central_themes (mechanical sub-theme floor-2 admission), _theme_cosine (generic-damped deck-similarity), the role-classifier under-count fixes (permanent-type-list removal, `counter up to N target`, library-tuck removal, the draw-N/discard-N LOOT exclusion, `half X` draw, the second sweep — bounce to `owner's` hand, edict, X-damage, Aura tuck, mass-edict sweeper, repeatable-upkeep-draw card advantage, damage to each opponent — and the THIRD sweep's card-advantage half: a repeatable draw on any PHASE not just the upkeep, a `whenever`-triggered draw, and the draw-PAYOFF false positive the trigger-comma discriminates against, plus that the under-read channel no longer flags what it now counts) plus a structural assertion that the coverage net is a SUPERSET of the precise patterns and that stripping reminder text kills the Ward false cue without hiding a real miss, protection_effects (real ward/hexproof/indestructible vs a combat pump), rotation_year/rotation_risk (`_SET_ROTATION_OVERRIDE`, calendar-year risk), cost_upside_flags, _drop_cost_themes, section_mismatch, power_threshold_flags (incl. the SCOPE fix: removal/opponent-facing and `total power` sums must not flag), _cites_as_arriving (the reversed-replacement claim, plus the `re.I`-defeated `+X` capital and the "cut for cause" idiom), count_conf (role counts carry their own uncertainty, quantity-weighted), match_paste's TIE-BREAK (drift, then more shared, then lower id — order-independent; the rule the dashboard's JS copy mirrors), _file_memo (reference-table cache: a same-size rewrite and a REPOINTED path both invalidate), deck_shape (wide/tall from text, amplifiers-only), near_duplicates (interchangeable-card groups); tests/test_wishlist.py is the WISHLIST-model layer — wishlist.is_conditional_power, wishlist.power_is_seeded, wishlist._parse_budget / _rank_scores(keep=…) (the budget planner: spec parsing, and that a FILTERED view scores identically to the full one — the subset must exclude the corpus max or the test passes vacuously); tests/test_ingest.py is the INGEST + TAGGING layer over `import_arena.py` / `tag_synergies.py` — import_arena, is_heist_text (TestHeistTheme: cross-sentence matching, the impulse/graveyard-hate exclusions, and the `theft`/`heist` name-collision regression), is_exile_cast_text (TestExileCastTheme: the Adventure type-line enabler, the Warp/Plot/Foretell keyword family, and the cast-from-exile payoffs), keyword_frequencies (distinct cards, not rows — the DFC double-count that let a card-unique flavor keyword escape the noise filter), tags_for (incl. the toughness-matters / noncombat-damage / spell-copy / tribal-payoff mechanical-synergy tags); tests/test_parse_matches.py pins the match parser against the REAL log shape (the seat-derived W/L (and its mirror, so the outcome isn't hardcoded), the skip-and-warn when the `Match to` header is missing, the local-date-beats-UTC-epoch rule, dedup by matchId, `_wilson`'s bounds, the `_MIN_SAMPLE` refusal to print a percentage, and that no userId/playerName ever reaches a row); tests/test_verify_ingest.py pins the ingest verifier (lower-bound vs `--exact` authoritative quantities, the DFC front-face key shared by the quantity and INV-02 checks, basics skipped by design, an absent card-mana.csv not blamed on the ingest) AND the rebuild ORDER in the Makefile — asserting `build_pool` precedes `build_mana --pool`, `build_mana` precedes `tag_synergies`, the full-scope flags survive, `--merge` not `--force`, and that the three dependency CLAIMS the order rests on are still true in the code, so a future change fails the test instead of silently invalidating the order; tests/test_recommendations.py pins the recommendation ledger — the cut-percentile math, disagreements-worst-first, that an unrankable row is excluded from n rather than counted as agreement, the call-time path resolution, that a broken model loses its column and not the swap, and the STRUCTURAL guarantee that no scoring function reads the ledger (wiring feedback into a score has to delete a test); tests/conftest.py holds the shared fixtures and path setup every one of these imports through), requirements-dev.txt (pytest, dev-only), pytest.ini, .github/workflows/tests.yml (runs pytest + check_all on push/PR), Makefile (`make test-units`). COMPLEMENTS check_all.py — it stays the pure-stdlib gate; pytest is never required to run the core tooling.
- Decks: decks/

**Invariant Library:**
- INV-01 | card-library.csv has the canonical 8-column header, every row has 8 fields, no duplicate (Card Name, Set Code, Collector #) printing, and Quantity Owned is blank or a non-negative integer | Subsystem: Data | Verify: scripts/check_all.py (via validate.py)
- INV-02 | Every Card Name in card-library.csv has a row in card-mana.csv | Subsystem: Data | Verify: scripts/check_all.py
- INV-03 | Derived reference files exist AND keep their own schema: card-mana.csv (Card Name/Mana Cost/Mana Value/Keywords), card-pool.csv (…/Rarity; Legalities+Released+Power+Toughness warn if absent), gallery.html | Subsystem: Data/Presentation | Verify: scripts/check_all.py
- INV-04 | Every deck file under decks/ parses with no malformed card lines | Subsystem: Decks | Verify: scripts/check_all.py
- INV-05 | Color(s) stores color identity; actual mana cost lives only in card-mana.csv | Subsystem: Data | Verify: design/manual
- INV-06 | Synergy tags are keyword-aware — regenerate via build_mana.py then tag_synergies.py --merge after imports (--merge preserves hand-curated tags; --force replaces them) | Subsystem: Ingest | Verify: manual

**Policy Configuration:** threshold 6/10; 2 consecutive cycles below triggers a policy response.

**Regression Scenarios** (manual walks; the Test Command above is the primary gate):
1. Ingest a batch — `import_arena.py <file>` → **`make refresh`** → `verify_ingest.py <file>`. Expect: check_all clean, gallery card count == library row count, and verify_ingest reporting every pasted card present at the expected count. **`build_mana.py` is not optional when the batch introduced a NEW card** — it has no `card-mana.csv` row until then, so INV-02 fails; this scenario used to omit it (and so did `import_arena.py`'s own "Next:" line), which left the gate red with no hint why (broad-scan F-06). It then carried the steps in the WRONG ORDER for a further cycle (`build_pool.py` after `build_mana.py`), which is why the chain now lives in the Makefile instead of in four disagreeing prose copies. **`verify_ingest.py` is the step nothing else covers:** check_all proves the library is self-consistent, not that it contains what you pasted — a card that never arrived breaks no invariant.
2. Analyze a deck — `deck.py check|mana|consistency|tribes|stats|shape|legal|cuts|tier|tier --audit-rationale|redundancy|text|verify <id>`, plus `deck.py feedback` (the recommendation ledger; empty until a swap has been applied, and a dry-run `swap` must leave it untouched), the needs-aware recommenders `deck.py suggest <id> --lands|--ramp|--interaction|--needs`, `deck.py screen <id> <names>` (re-scores candidates against the CURRENT list; ★ strict upgrade + ✱ multiplier flags), and roster-wide `deck.py audit` / `deck.py suggest-homes <card>` / `deck.py similar <id>` / `deck.py resolve <names>` / `deck.py rotation` (+ `pool.py --role`). Expect: no traceback; mana is hybrid-aware; consistency reports keepable %/land-drops/cast-on-curve (with the splash / color-hungry fix notes); tribes surfaces type-matters payoffs; legal flags size/copy/format violations; cuts/text print full oracle text; tier shows claimed-vs-floor (and `--audit-rationale` flags a tier rationale citing cut
   cards or stale figures); stats reports the protection axis and flags a ZERO; redundancy buckets effects by virtual-copy depth and proposes functional copies first, duplicates as fallback; suggest `--lands`/`--needs` surface the STRUCTURAL fills (fixing · acceleration · interaction, with board-scalers flagged) the theme model can't; audit scores every deck TUNE/craft/review/ok, with `review` reserved for an off-color ABILITY or thin interaction (a hybrid you pay on-color shows as `Ns` in the Cast column but never reaches the verdict); verify diffs a pasted Arena export against the stored deck. Also `python3 scripts/deck.py --help` and one subcommand help — the CLI surface check_all cannot reach.
3. Refresh derived data — `build_mana.py` → `tag_synergies.py --merge` → `build_pool.py` → `build_gallery.py` → `check_all.py`. Expect: check_all reports all invariants hold.
4. Edit via the app — start `scripts/app.py`, change a quantity and Save, add a card, then open a deck (Decks →), change a card's quantity and Save; run `check_all.py`. Expect: CSV + deck file updated, `.bak`s written, and all invariants hold (INV-02 since add appends a card-mana.csv row; INV-04 since deck save re-parses cleanly).

The next four need **a person at a browser** — they are the PERCEPTUAL and interaction
checks a code read structurally cannot make, which is exactly why they are written down
rather than assumed. `/broad-scan` Stage 3 emits new ones in this format.

5. Light-mode status colors | Subsystem: Presentation & Interface
   Steps:
     - Open `dashboard.html`, press `t` (or click the theme toggle) for light mode
     - Look at the roster-triage Action pills (TUNE / craft / review / ok)
     - Look at a deck card's build badge (buildable / N missing / N short)
     - Expand "Recently edited" — the +added / −removed delta lines
     - Paste any deck into the stale-deck panel — the in-sync / drifted text
   Expected: green/amber/red read clearly against the LIGHT panel background and are
   distinguishable from each other and from body text. All 16 of these sites were
   hardcoded to the DARK-mode hexes until I-03; a washed-out or muddy pill means one
   regressed back off `var(--ok)` / `var(--warn)` / `var(--bad)`.
6. Dashboard at phone width | Subsystem: Presentation & Interface
   Steps:
     - Open `dashboard.html` at 390×844 (or a real phone); scroll top to bottom
     - Open the roster-triage table and the wishlist table
     - Open a deck modal from the section-nav and switch tabs
   Expected: the page body NEVER scrolls sideways; the wide tables scroll inside their
   own boxes; the section-nav strip scrolls horizontally; every grid is one column.
7. Keyboard-only traversal | Subsystem: Presentation & Interface
   Steps:
     - In `dashboard.html`, using Tab / Shift-Tab only, reach in order: a color filter
       chip, a quick-filter pill, a roster-table sort header, a section header (collapse
       it with Enter or Space), and a deck's ⤢ detail opener
     - Open the modal, Tab through it, press Escape
   Expected: every one is reachable with a VISIBLE focus ring; Enter and Space both
   activate; Tab inside the modal cycles within it and never reaches the page behind;
   Escape closes it and returns focus to the ⤢ that opened it. This is the acceptance
   test for I-01/I-04 — before those, nothing in that list was reachable at all.
   Then the EDITOR's half of the same fix (`make app`, `templates/collection.html`):
     - Focus the search box, then Tab — the six colour pips must come next, in W U B R
       G C order, each with a visible ring; Enter and Space both toggle one, Space must
       not scroll the page; the card grid re-filters
   Then the DECK editor (`/deck/<id>`, `templates/deck.html`):
     - Tab to the Analysis strip — each of Stats / Mana / Tribes / Suggestions must take
       focus with a visible ring; Enter and Space both run one; the output `<pre>` is
       itself focusable, since it scrolls
   Expected: the selected tab is the only one reporting `aria-selected="true"`, and a
   save toast is announced (it is a `role="status"` live region). Note the SUCCESS toast
   is cut short by the `location.reload()` that follows it — see the follow-on below;
   the failure toasts are the readable ones.
   Expected: identical behaviour to the dashboard's colour chips, because they are the
   same control — `role="button"` + `aria-pressed`, per `build_dashboard.py`'s `a11y()`.
   The pips were bare `<div>`s until this landed, so the editor's whole colour filter
   was mouse-only. The MARKUP half of this is now pinned automatically by
   `tests/test_templates.py` (attributes, key handler, `aria-pressed` sync, focus ring);
   what still needs a person is the perceptual part — that the ring is actually visible
   and the order actually matches what you see.
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
one deployed artifact is the **roster dashboard**: `.github/workflows/pages.yml` rebuilds
`build_dashboard.py` offline and publishes it to **GitHub Pages on every push to `main`**
(no manual step). Everything else is read/run locally. The generated page is a themed
(dark/light) self-contained view: the BUILD stays offline (embedded data, system fonts,
no CDN), and the page's only online touches are optional/non-blocking — Scryfall hover
images and a ⟳ live re-sync from the Pages URL — always falling back to the embedded
snapshot. `build_dashboard.py` restyles are **template-only**: the data pipeline
(`collect`/`deck_viz`/`craft_rows` → the `#data` island) is the source of truth and must
stay untouched by any restyle (the payload shape is what `deck.py`/`wishlist.py` produce).

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
NOT vendored — that ceremony (two-axis scoring + a `.cycle/` state dir) outweighs
its benefit at this project's size; adopt them only if you later want benchmarkable
scoring. `check`, `refresh`, `add-deck`, `draft-deck`, `tune-deck`, `add-cards`,
`add-wishlist`, `roster-review`, `ingest`, `log-matches`, and `apply-changes` are project-specific. **A skill drifts behind the
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
