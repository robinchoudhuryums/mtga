# Cycle state — 2026-07

> **Starting fresh? Read `.cycle/NEXT-SESSION.md` first.** It carries the current
> diagnosis, the agreed next task, the measurements not to re-derive, and the traps.
> This file is the prose record of what happened; that one is what to do.
> For "which command answers X, and why do two of them disagree", read
> **`docs/systems-map.md`** — that is now a live reference, not a cycle artifact.

## Session — systems map + agreement gate (2026-07-29)

The task-first systems map landed (`docs/systems-map.md`), the agreement gate landed
(`scripts/check_agreement.py`, the twelfth hard gate), and the map's top finding was
fixed: `_weakest_cut` and `rank_cut_candidates` both answered "this deck's most-cuttable
card" and **disagreed on 36 of 64 decks**. Both now score through one `cut_keep_score`.
Subcommand count held flat at 33 — a duplicate model was removed, not added.
Block: `.cycle/blocks/2026-07-systems-map-agreement-gate.md`.

Also: `load_rarities` was the one reference-table loader never memoized, and it was
**85% of `deck.py cuts`' runtime**. Found by profiling the new gate, not by reading.

## Where I left off (previous session)
Feedback segmentation is implemented, mutation-tested, gated and committed on
`claude/add-cards-ingested-batch-cy2tdb`. Nothing is half-done. Block:
`.cycle/blocks/2026-07-feedback-segmentation-broad-implement.md`. Docs for it are
NOT yet written — see DOCUMENTATION UPDATES NEEDED in that block; run /sync-docs.

Earlier in the cycle: the three card-misread findings, and the 42a / 46 / 20
ingests (PR #85, merged). Prior block:
`.cycle/blocks/2026-07-card-misread-causes-broad-implement.md`.

## Completed this session
- Finding 1 — `cuts` multiplier co-signal (`✱`) + a `lifegain` doubler axis.
  Root cause was a CALLER, not a model: `doubler_axis`/`doubler_support` already
  scored Delney correctly for `suggest-homes`; `cuts` never asked.
- Finding 2 — `deck.py screen <id> <names…>`, re-scoring a candidate pile against
  the deck as it currently stands. Wired into /draft-deck and /tune-deck.
- Finding 3 — `strict_upgrades`, surfaced by `screen` as `★ STRICT UPGRADE`.
- Deck 46 (Radiant Ascension) was built and refined across this session and is at
  tier A, floor A, 60 cards, 16 craft targets.

## Decisions made
- The multiplier term only ever RAISES a keep-score. The no-support case is already
  handled by theme-fit; subtracting would punish the same card twice.
- `strict_upgrades` is text-containment with colour identity deliberately EXCLUDED,
  so a containment result never depends on the deck's colours. Conservative by
  design; its silence is explicitly not a verdict.
- The lifegain axis requires the literal "twice that much" — a plus-N replacement
  (Angel of Vitality) is templated identically and must not qualify.
- Anchor 16's WIRING half lives in tests/test_deck_models.py, since a pure-function
  anchor structurally cannot see whether a caller invokes the function.

## Session — creature cut-ranking hypothesis (2026-07-29, later)

Tested the standing P/T hypothesis and **rejected it**. Pre-registered, one evaluation,
scored on git-reconstructed pre-swap snapshots across all 31 creature cuts. A bounded
±3 body term changed nothing (predicted: `fit` median 44 vs a ±3 term); scaled to the fit
IQR it made agreement slightly worse; and cut creatures are indistinguishable from kept
creatures on body quality (17/31, p=0.72). Nothing shipped from the hypothesis.

What did ship: `segment_concentration` + a per-deck breakdown in `deck.py feedback`,
because the test found the creature rate running 0%–100% per deck — the 45% is largely a
statement about which decks were edited. Block:
`.cycle/blocks/2026-07-creature-cut-hypothesis-test.md`.

## Session — CLAUDE.md split (2026-07-29, later still)

**CLAUDE.md 2,219 → 956 lines, nothing deleted.** Each operative rule (plus any live
residual) stays in the auto-loaded file with an anchor; the incident, measurement and
reasoning moved VERBATIM to `docs/gotchas.md`. Gated by `scripts/check_docs.py`
(anchor round-trip both ways, vendored section names, per-bullet line cap).
Conservation proved 69/69 byte-identical and mutation-tested. Cycle Workflow Config
deliberately deferred to a follow-up pass, agreed with the user.
Block: `.cycle/blocks/2026-07-claude-md-split.md`.

## Session — Cycle Workflow Config, phase 2 of the split (2026-07-29, last)

**CLAUDE.md 956 → 757 lines** (2,219 at the start of the day). The user supplied
`setup-cycle.md`, the command that WRITES that section, which turned the work into
restoring a specified format: Test Command is a single line (ours was 208), a Subsystem is
a comma-separated file list (ours held 13.6k chars of prose), a Regression Scenario is
Steps + Expected. Eleven `[C-nn]` blocks moved verbatim, 11/11 conserved.

Two real findings: my compressed scenario 7 dropped a LIVE caveat (the editor's success
toast is cut short by the `location.reload()` after it) — caught by a shingle check over
the retyped half, and recovered as its own block; and Regression Scenario 3 carried the
rebuild chain in the WRONG order, invisible because `_restates_chain` scanned
`scripts/*.py` and `.claude/commands/*.md` but never CLAUDE.md. Both fixed and
mutation-tested. Block: `.cycle/blocks/2026-07-cycle-config-split.md`.

## Session — incremental `make refresh` (/broad-implement)

`build_mana.py` was the only non-incremental step of the rebuild and re-priced all ~15.9k
pool cards every run. It now reuses already-resolved rows and fetches only new/unresolved
names; `make refresh REFETCH=1` forces the full re-price, as a FLAG on the one target
rather than a second recipe. Live `make refresh`: **3m40s vs ~10 min**, the mana step
**1.2s**, and the run modified 0 existing rows / lost 0 Mana Values while adding 94 real
new cards. Fixed a latent write bug on the way: Mana Value arrives as a float when fetched
and a string when reused, and the old `isinstance` check would have blanked every reused
row — the whole file on the first incremental run.
Block: `.cycle/blocks/2026-07-incremental-refresh-broad-implement.md`.

**Where I left off:** committed and pushed; nothing half-done. The one loose end is
DELIBERATE — the live refresh produced real derived-data drift (card-pool.csv +389 lines,
card-mana.csv +94 rows) which I reverted to keep the commit scoped. Run `/refresh` and
commit it deliberately; it will need deck 43's tier rationale re-grounded
(`card_advantage 11 vs live 12`, `avg_mv 2.91 vs live 3.0`).

## Session — pool freshness skip + cuts signature de-saturation (/broad-implement)

Two findings. **`build_pool.py --all` was 99% of `make refresh`** (222.5s of 224.3s, 91
paginated pages at ~2.4s each, vs 1.8s to derive every row — measured, not assumed). It now
reuses a pool built within 7 days FOR THE SAME QUERY; the sidecar records the query on a
second line, with the date still on line 1 because `deck.pool_staleness_days` reads
`stamp[:10]`. Skipping is correct, not just fast: the pool is the whole Arena pool and is
independent of what you own, so an ingest cannot change it. `REFETCH=1` now propagates to
both build steps. No-change refresh: **12.7s** (≈11s of it `check_all`) vs 5m3s full.

**`cut_scoring_context` now reads the STRICT `#: protect:` spine.** The loose union fired
the +2 keep-boost on 87% of nonland cards across the 22 protect-declaring decks (100% in
decks 20 and 46) — a constant, not a signal. Strict fires on 66%. Roster diff: 14/64 decks
re-scored, 4 top-cut candidates moved, deck 30's motivating case intact (`{counters}`).
Block: `.cycle/blocks/2026-07-pool-skip-signature-broad-implement.md`.

**Where I left off:** committed and pushed, nothing half-done. The derived-data drift is
now CLEARED (see follow-on 5). One standing hazard to know: a stale `__pycache__` can
silently defeat a same-size mutation test — `rm -rf scripts/__pycache__` between runs.

**Notable from the refresh:** 7 cards the decks play were previously absent from
card-pool.csv altogether (Grimoire, Moonshaker Cavalry, Moonstone, Vampire Nighthawk,
Vampire Gourmand, Tragedy Feaster, Hakoda), so those decks' metrics were computed with
them partly invisible. Only deck 43 cited an affected figure in prose, and it is fixed;
other decks' numbers moved without any written claim depending on them.

## Open follow-ons
See FOLLOW-ON ITEMS in each block. Highest value now:
1. ~~**`_signature_themes` saturates in `cuts`**~~ — DONE this session (87% → 66%).
   Superseded item, kept for the record: **`_signature_themes`** — the +2 keep-boost fires on 86% of
   nonland cards across the 22 `#: protect:` decks (100% in decks 20 and 46), because
   `cuts` reads the LOOSE signature set while all three `fit_strength` callers read the
   STRICT one. Switching would unify them and de-saturate to 66%; the motivating case
   (deck 30's counter-doublers) survives. Needs a roster-wide before/after diff first.
   Measured in `docs/systems-map.md` §7.
2. `tier --audit-rationale` false negative — a `_HISTORY_CUES` cue about one card
   suppresses a citation of ANOTHER card in the same window, even when that
   clause says the card STAYS. Deck 42a asserted "Erode stay[s]" after Erode was
   cut and the audit reported clean. Fix is the mirror of `_cites_as_arriving`;
   needs a roster sweep before landing.
3. ~~An incremental `make refresh`~~ — DONE: `build_mana.py` reuses already-resolved rows,
   so a no-change refresh is ~1s and offline. `make refresh REFETCH=1` forces a re-price.
4. The reverse `screen` flag (a candidate strictly WORSE than an incumbent).
5. ~~**Commit the derived-data drift**~~ — DONE via `/refresh`: pool 15,796 → 15,899
   unique names (103 added, 0 removed), card-mana +94 rows, 0 legality changes, nothing a
   deck plays left the pool. Deck 43's rationale re-grounded (card advantage 11 → 12,
   curve 2.91 → 3.0) — both figures were understated because **Marina Vendrell's
   Grimoire**, the deck's named engine, had been missing from card-pool.csv entirely and
   so counted as free in the curve with no `card draw` role.
6. ~~`build_pool.py --all` incremental~~ — DONE this session (freshness skip + `--refetch`).
7. The 7-day pool window is a guess, not a measurement — no data informs the exact number.

## Decided AGAINST (2026-07-29, the split)
- Reorganising CLAUDE.md by topic. The vendored workflow commands name its sections
  verbatim and cannot be edited here, so a rename breaks a command with no local fix.
- Deduping the gotchas against README (26 of 57 are about a subcommand README already
  documents). That needs a second judgement per rule and a wrong call loses information
  silently; one destination, one judgement.
- Rewriting the evidence while moving it. Verbatim movement is what makes the
  conservation check an exact-equality proof instead of a fuzzy overlap.

## Session 2026-07-31 — pile-triage fixes (P1–P5)

Five fixes to the candidate-pile path, all found by finally running
`deck.py screen 51 <the 111-card pile>` AFTER a hand-triage had already mis-classified
nine cards. Full block: `.cycle/blocks/2026-07-pile-triage-broad-implement.md`.

- **P1** `_resolve_card_name` — one shared resolver for `resolve` and `screen`, matching
  across dropped punctuation and stripping a trailing `(note)`. Unresolved on the real
  pile 22 -> 2. Still refuses to correct typos.
- **P2** `_candidate_castability` — `screen` reads castability from the PRINTED COST, not
  from `Color(s)`. False off-colour flags 5 -> 1 (the one is genuinely gold).
- **P3** `_strong_signature_themes` — a GENERIC theme now needs HALF the `#: protect:`
  list; SPECIFIC keeps `>=2`. **This closes the deferral recorded below on 2026-07-29**
  ("Fixing the `_signature_themes` saturation in the same session it was measured…
  needs a roster-wide diff first"). The diff was run: 4,440 (deck, card) judgements,
  KEY 13% -> 8%, 223 labels changed, ALL of them KEY -> weaker. Nothing gained a KEY.
- **P4** `/add-cards` Stage 0b now REQUIRES `screen` for a pile over ~10 cards.
- **P5** G-58 gained its BULK-TRIAGE variant, with the nine-card table.

744 tests pass (+19). `check_all` green.

**Where I left off.** Two things are open and neither is started:
1. **A `card-mana.csv` data gap, found by checking a rules question against Scryfall.**
   Modal DFCs store only the FRONT cost — Bruce Banner reads `{U}`, but its layout is
   `modal_dfc` and BOTH faces have a real `mana_cost`, so either is castable from hand.
   Rooms/splits correctly store two. 432 two-faced rows hold one cost and need splitting
   into transform (correct) vs modal (data loss). `build_mana.py` is the fix site. This
   caused a WRONG ANSWER in chat, so it is not cosmetic.
2. **Deck work agreed but NOT applied**, pending the owner picking cuts: deck 51's
   engine/top-end group (Lady Octopus, Walls of Ba Sing Se, Ramos, Kitsa, Norman Osborn,
   Ghostly Keybearer ← Into the Flood Maw, 2nd Tolarian Terror freed), deck 51a's mill
   group (Kitsune's Technique, Jidoor ← an Island, Tale of Tamiyo, Cephalid Inkmage), and
   a NEW third variant for the ~20-card unblockable-tempo overflow. Measurements are in
   chat; nothing was written. The owner has asked twice for no changes without approval.

## Decided AGAINST (2026-07-29, later)
- Shipping any body-quality term in the cut ranking. It failed its pre-registered test;
  a term that fails and ships anyway is worse than no term.
- Tuning the concentration report's share threshold until deck 46 appeared. The first
  draft used >20% and deck 46 sits at 19.4%; the threshold was REMOVED rather than
  lowered, because a cutoff tuned until the expected finding shows up is that finding
  smuggled into a constant.
- Recording BUILD-vs-TUNE context at `swap --apply`. It would separate the populations
  properly, but it needs every skill to pass it — another hand-kept thing that rots — and
  the split has not survived a large enough sample to earn that.

## Decided AGAINST (2026-07-29)
- Vendoring the Tier-3 `systems-map` command. It produces a MODULE map, and the module
  structure was never the friction — the map that was needed is task-first and
  hand-written. CLAUDE.md's Command-provenance paragraph now records this.
- Fixing the `_signature_themes` saturation in the same session it was measured. It
  changes the cut ranking, and the standing rule is that a scoring change needs a
  roster-wide diff first. Recorded with numbers instead of landed blind.
- Moving `check_suggest` #13 and the `test_verify_ingest` rebuild-order check into the
  new agreement gate. That would trade one registry for two.

## Decided AGAINST (previous session)
- Re-weighting `cuts` to normalize its fit sum. Simulated across all 64 decks:
  top-3 themes moves correlation(tag count, keep-rank) +0.73 -> +0.72 and changes
  1% of top-5 shortlist slots; mean-of-hits reaches +0.60 and over-rewards narrow
  cards. The effect is not double-counting within a card — tag count proxies for
  "described by the tag vocabulary at all". Reporting the split is the fix.
- Promoting decks 41 or 42a to tier A. Both sit one band below an A floor by a
  written, still-true argument; the guard permits that and does not nag.
