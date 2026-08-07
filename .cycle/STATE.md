# Cycle state — 2026-07

> **Starting fresh? Read `.cycle/NEXT-SESSION.md` first.** It carries the current
> diagnosis, the agreed next task, the measurements not to re-derive, and the traps.
> This file is the prose record of what happened; that one is what to do.
> For "which command answers X, and why do two of them disagree", read
> **`docs/systems-map.md`** — that is now a live reference, not a cycle artifact.

## Session — broad scan #2 + top-5 fixes (2026-08-07)

A full `/broad-scan` (three stages, six parallel deep-read passes, every Critical/High
finding hand-verified by reproduction) followed by `/broad-implement top 5 from scan`.
The scan used fresh IDs **BS2-01…BS2-40** (the 2026-08-04 scan owns BS-01…19). Scan
report lives in the session; the implemented slice and its verification are in
`.cycle/blocks/2026-08-broad-scan2-top5-broad-implement.md`.

**Implemented (all reproduced before/after, 14 new tests, 965 passing, zero soft
warnings):** BS2-01 sync --apply truncation guard (a partial paste can no longer
rewrite a deck file; --force overrides). BS2-03/04 import_collection: an unreadable
quantity cell can never be zeroed by --zero-missing, and a no-printing-column export
SUMS repeated names instead of max-collapsing (each loudly warned). BS2-06 the
fixed-damage removal pattern no longer counts player-only burn as interaction — 14
decks re-measured, ZERO tier floors moved, 2 cards baselined, 9 stale `#: tier:`
figures re-grounded in the same commit. BS2-02/25 the ingest DFC loop: front-face
joins in reconcile_crafts/import_arena (no more duplicate front-name rows for the 8
full-name-stored printings) and front→full resolution in verify_ingest (owned Rooms
no longer report "NOT in library"). BS2-08 the needs recommenders normalize --format,
honour --any-format, and warn instead of silently dropping the filter.

**Decisions:** BS2-10 (sync same-deck double-claim) was deliberately left OUT of the
top-5 scope despite being adjacent to BS2-01 — same write loop, queued as the next
sync fix. The no-printing-column SUM trades a warned over-count for a silent
under-count; the per-printing-export premise justifies it.

**For the next session:** the scan's unimplemented findings are queued in the block's
FOLLOW-ON ITEMS (highest value next: BS2-10, BS2-05 verify-for-collection-CSVs,
BS2-11/12 wishlist land mis-rank + card.py deck join, BS2-16/17 a11y + gallery XSS,
BS2-13/14 gate holes, BS2-18 interaction_profile divergence). Doc updates for
/sync-docs are listed in the block (G-67 incident, README import_collection semantics,
G-63 write-side membership, K-12's still-contradicted claim).

**Second pass, same session:** `/sync-docs` applied (G-63/G-67/G-08 + README ingest/sync
semantics, K-12 left un-annotated on purpose), then `/broad-implement` of ALL TEN follow-on
items — BS2-05, 10, 11, 12, 13, 14, 16, 17, 18, 24. Block:
`.cycle/blocks/2026-08-broad-scan2-followon-broad-implement.md`. 983 tests (18 more new),
zero soft warnings, dashboard.html + gallery.html rebuilt. K-12's canonical-counter claim
is TRUE again (BS2-18); check_patterns now sees 247 patterns at any nesting depth and the
dead engine pattern is gone; INV-04 gained the malformed-line channel.

**Third pass, same session — Batch A** (verdict-surface joins & determinism): BS2-19, 20,
21, 22, 35, 36 all implemented. Block:
`.cycle/blocks/2026-08-broad-scan2-batchA-broad-implement.md`. 992 tests (9 more new).
Deliberately NOT done: BS2-07's full header-consumer sweep (only the swap-side protect
guard was in Batch A's scope) — it is the named follow-on.

**Fourth pass, same session — Batch B** (wishlist & recommender honesty): BS2-37, 38, 39,
40 + the grouped power-model fixes (conditional-power mana join, front-face seed) all
implemented; 8 stale seed-provenance Power cells re-seeded in the same commit. Block:
`.cycle/blocks/2026-08-broad-scan2-batchB-broad-implement.md`. 998 tests (6 more new).
The five BS2-39 rows verified rescued live (Splash Portal → blink et al.).

**Fifth pass, same session — Batch C** (gate hardening): BS2-29..34 + five small gate
leaks all implemented. tests/test_check_all.py is NEW (the runner's first mutation
layer — 11 tests, including the one that would have caught BS2-14). The tightened
check_commands immediately caught query.py riding on prose mentions (exempted with an
honest reason). Block: `.cycle/blocks/2026-08-broad-scan2-batchC-broad-implement.md`.
1012 tests (14 more new).

**Sixth pass, same session — Batch D** (editor write-safety): BS2-26 (deck-save
staleness 409 via content-hash token), BS2-27 (atomic rollback), BS2-28 (metadata-key
validation) + the html-shadow minor. ONE RETRACTION: the dirty-key join('') "collision"
is a non-finding — the file already delimits with an invisible \x01 that the scan's
reader (and a verifying grep) rendered as empty; no change made. Block:
`.cycle/blocks/2026-08-broad-scan2-batchD-broad-implement.md`. 1018 tests (6 more new,
in the new importorskip'd tests/test_app_editor.py).

**Seventh pass, same session — Batch E + sync-docs** (interface access): S-2 tablist
completer (both dashboard strips, arrow keys, live aria-selected), S-4 collection toast
live region, S-5 <main> landmark + test scope, S-6 focus restoration on remove, S-7
keyboard/focus preview parity, S-10 disclosure state + per-card remove names, S-11
/decks empty state. dashboard.html rebuilt; the accumulated doc notes from Batches A–D
applied (README ×3, CLAUDE.md C-07 + Scenario 4, gotchas G-08/G-63) and check_docs green.
Block: `.cycle/blocks/2026-08-broad-scan2-batchE-broad-implement.md`. 1022 tests.

**Eighth pass, same session — Batch F** (editor theming + phone width, the last
interface batch): S-9 dashboard status fills/borders via color-mix (completing I-03's
half-done fix), S-8 one --ok/--warn/--bad vocabulary + a light palette across all three
templates + five hardcoded hexes tokenized (with --on-solid flipping per theme and
--pip-ink/--scrim held invariant on purpose), S-3 a phone breakpoint per template.
Light-mode contrast measured: every pair clears WCAG AA. Deliberate decision recorded:
NO in-page theme toggle (the dashboard's is a different origin; three copies would rot).
Block: `.cycle/blocks/2026-08-broad-scan2-batchF-broad-implement.md`. 1029 tests (7 new,
verified non-vacuous after a lowercase-only regex was found skipping the pip tokens).
Batches E+F close every STRUCTURAL Stage-3 interface finding.

**Ninth pass — /sync-docs** after Batch F. Eight drift points found and applied across
the four checks: Regression Scenarios 5 (S-9 moved fills+borders onto the tokens, so the
"hardcoded until I-03" note was false), 6 (extended dashboard-only → dashboard AND
editor, absorbing what the scan proposed as a new Scenario 9) and 7 (arrow-key tablists,
focus-follows-preview, focus-after-remove, and a leg in each OS colour scheme); C-01's
gate enumeration, which omitted three soft roster sweeps check_all really runs; G-53
(both coverage paths now enforce the real-call rule); **G-56's overstated "structurally
forbids"** — the test is one call level deep and does not cover `cut_keep_score`, now
stated as a live residual rather than fixed (that is Batch G); integrity.yml's rotted
"31 subparsers" comment (real: 34) replaced with a no-count floor; C-10's browser
baseline (color-mix ⇒ 2023+); and README's two operator-visible editor behaviours (the
save-refused-on-concurrent-change toast, and following the OS colour scheme with the
different-origin reason there is no toggle). C-11's Scenario 7 long form extended to match.

**Tenth pass — Batch G** (refresh, resilience, CLI polish — the scan's whole Low tail):
BS2-23 pool re-tag staleness via a tag-CONTENT fingerprint in the build stamp (not mtime:
a fresh clone would otherwise force a 5-min rebuild every time), scryfall's two missing
body-read exceptions, sheets_sync's file mode, the F-02 MIRROR guards on `--out` (plus a
direction-neutral rewrite of csv_schema_error's message, which read backwards for the new
direction), import_arena/import_collection polish, nine deck.py CLI seams, card.py's
legality token test, query.py's --csv guard, two model fixes, and the G-56 depth close.
1031 tests. TWO self-inflicted breaks caught by the gates and fixed pre-commit — an
indentation loss that made card.py unparseable (check_all's AST scans caught it) and four
read_stamp test doubles I should have scanned for first.
Block: `.cycle/blocks/2026-08-broad-scan2-batchG-broad-implement.md`.

**Where I left off:** top-5 + docs + follow-ons + Batches A–G implemented, tested, committed and
pushed on `claude/broad-scan-v74wau`; no PR opened (not requested). The remaining scan
items are batched/prioritized in the session's closing report (batches A–H: verdict-surface
joins, wishlist honesty, gate hardening, editor safety, interface access, editor theming,
CLI polish, strategic).

## Session — broad scan + top-5 fixes (2026-08-04)

A full `/broad-scan` (three stages, seven parallel deep-read passes, top findings
hand-verified) followed by `/broad-implement BS-01, BS-02, BS-05 - BS-07`. The scan's
full report lives in the session; the implemented slice and its verification are in
`.cycle/blocks/2026-08-broad-scan-top5-broad-implement.md`.

**Implemented (scripts/deck.py, scripts/card.py):** BS-01 the needs recommenders
(`suggest --ramp/--interaction`) now filter by PRINTED COST via `_candidate_castability`
like `suggest_scored` — the G-58 bug had been re-introduced on the exact path G-38
routes deficits to (34 interaction cards + 25 mana sources were hidden from mono-color
decks). BS-02 `card.py` exactness now outranks source (`card.py "Mimic"` no longer
shows Gogo) — including a second shadow inside field resolution. BS-05/BS-06 the
swap bump-match, self-swap guard, and `legality_report` copy/commander counting all
key on `_ms_key` (front face), closing the seam where a DFC swap could split a card
across two spellings and the copy limit couldn't sum them. BS-07 `sync` now strips
Sideboard/Maybeboard per pasted block (with a visible note) instead of writing board
cards into the maindeck.

**Verification:** check_all green (same 2 pre-existing soft warnings), 861/861 pytest,
Scenario 2 walked on the modified surfaces. Net score +3 − 0.

**Decisions / for the next session:** the scan's unimplemented findings are queued in
the block's FOLLOW-ON ITEMS (highest value next: BS-10 `--color` substring filter,
BS-09 XSS one-liner, BS-08 deck-editor JS front-face buildability, BS-03 sheets_sync
shrink guard, BS-04 check_patterns perimeter). The scan DISCONFIRMED the pool-DFC
Power/Toughness suspicion (NEXT-SESSION §5.4 / ROADMAP Tier 2.1 shrinks: 0 of 698 DFC
rows merged). The /broad-implement scope string ended in a truncated "BS-" — if a
sixth finding was meant, it was not implemented.

**Where I left off:** all five findings implemented, tested, and committed on
`claude/broad-scan-hekdj0`; docs updates (G-38/G-58/G-63 long forms) flagged for
/sync-docs, not yet written.

## Session — broad-implement Batches 1 & 2 (2026-08-04, same session, second pass)

Eleven more scan findings landed on `claude/broad-scan-hekdj0`. Block:
`.cycle/blocks/2026-08-batch1-2-broad-implement.md`.

**Batch 1 (trust the surfaces):** BS-10+18 — `--color` now set-matches via new
`lib.color_matches` in query/pool/wishlist (546→442 on `--color R`; the 104 Colorless
under `--color colorless`), and check_colors gained a membership-scan that was watched
to fail on the old shape, plus behavioral anchors and 5 unit tests. BS-11 — tribes
payoff scan sees plurals (deck 49/48 payoff lists now show their lords). BS-12 —
`load_keywords` front-face aliased (Cecil's keywords back). BS-13 — live-fetched
split costs book front-face MV. BS-14 — suggest-homes/similar/sync scope to
`roster_decks()`. BS-09 — 404 XSS escaped.

**Batch 2 (data safety):** BS-03 — `sheets_sync pull` is dry-run by default with
`--apply` + a 50% shrink guard (fake-worksheet tested: header-only and tiny sheets
refused). BS-15 — `import_collection` is finish-aware (foil+non-foil SUM; same-finish
repeats still MAX; 3 new tests). BS-16 — `reconcile_crafts` pool index front-face
aliased, dead fallback deleted (front-name paste of a DFC now reconciles). BS-17 —
outage-era wishlist Power seeds recompute on re-enrich (2.0→6.5 in the verified case;
hand grades untouched). Rider — `build_mana`'s front-face loop propagates outages to
the clean-abort path instead of writing blanks over ~700 good rows under --refetch.

**Verification:** check_all green (same 2 pre-existing soft warnings), 869/869 pytest
(8 new), scenario walks clean. Net +4 − 0.

**Where I left off:** Batches 1–2 committed and pushed. Remaining backlog: Batch 3
(interface parity), Batch 4 (gate hardening — the sibling-filter diff gate and
lib.alias_front are the two that prevent recurrence), Batch 5 (low tail), Batch 6
(tests for the 7 uncovered scripts). /sync-docs still owed for BOTH blocks' doc items
(--color semantics, sheets_sync contract, G-38/G-58/G-63 long forms).

## Session — /sync-docs + Batches 3 & 5 (2026-08-04, same session, third pass)

**Docs are synced** (README --color set semantics + sheets_sync pull contract +
import_collection finish column; CLAUDE.md check_colors both-scans bullet, G-38
needs-model note, G-63 rewritten with the five 2026-08 members; gotchas.md addenda
under G-58/G-63/G-38/G-59/G-17; app.py's mtime docstring corrected; test_cli's
stale counts made count-free). check_docs green, 91 anchors linked.

**Batch 3 (interface parity)** and **Batch 5 (correctness tail)** are implemented —
21 items; block: `.cycle/blocks/2026-08-batch3-5-broad-implement.md`. Headlines:
the deck editor's JS ownership lookup now mirrors lib.owned_qty (BS-08, the last
open G-63 member); gallery + dashboard keyboard access completed; `make dashboard`
target (deliberately outside refresh — measured 1m44s vs 13s) with the /refresh doc
claim corrected; consistency's → note targets the BINDING color; import_arena sums
Deck+Sideboard within a block and maxes across blocks; wishlist rank/budget is
name-unique (live dups Drakuseth/Sally Pride collapsed); atomic_write is actually
durable and permission-preserving; snow basics exempt from the copy limit (rules
side only — they stay real collection cards).

**Verification:** check_all green (same 2 pre-existing soft warnings), 872/872
pytest (4 new), scenario walks clean, wishlist --rank diffed against pre-change
code via git stash.

**New follow-ons found:** Pensive Professor / Riverchurn Monument carry Power cells
of 78.0 / 74.0 (pre-existing data typos, scale is 0–10 — reproduced on old code);
a Power>10 range flag in _rank_scores would catch the class. Committed
dashboard.html/gallery.html still carry pre-batch markup until `make dashboard` /
`make refresh` regenerate them (pages.yml covers the deployed dashboard).

**Where I left off:** everything above committed and pushed on
`claude/broad-scan-hekdj0`. Remaining scan backlog: Batch 4 (gate hardening: the
sibling-filter diff gate, lib.alias_front + check_dfc index/payload scan, BS-04
check_patterns perimeter, BS-19 role_baseline pruning, gate tail) and Batch 6
(behavioral tests for the 7 uncovered scripts, + the F20 re-seed path).

## Session — Batch 4, gate hardening (2026-08-04, same session, fourth pass)

The recurrence-prevention batch. Block: `.cycle/blocks/2026-08-batch4-broad-implement.md`.
Every new guard was WATCHED TO FAIL on its target regression before being trusted.

- **check_suggest anchor 13d** — sibling-castability parity: four synthetic cards whose
  identity and printed cost DISAGREE run through suggest_scored/suggest_mana/
  suggest_interaction end-to-end; a revert to an identity filter in any sibling fails
  the build. This is the gate BS-01 lacked.
- **lib.alias_front** — G-63's index rule in one home (six loader copies unified;
  known_printings keeps its provenance-aware variant), plus check_dfc's new
  index-alias REGISTRY (seven loaders behaviorally verified against a live DFC) and a
  payload pin on deck.html's `ownedOf` (the JS channel no Python scan reaches).
- **BS-04** — check_patterns scans wishlist (175 patterns live); **BS-19** —
  role_baseline has its pruning half, wired into check_all.
- **Gate tail** — flavor_overreach reports its skip; check_docs survives G-100;
  crash-skipped radars promoted with a "N RADAR(S) DID NOT RUN" count; the
  printings warning names cards.
- **Perf**: the batch-1 check_colors membership scan was costing +28s of check_all
  (unconditional ast.get_source_segment); a subtree pre-filter restored 67s → 42s
  (~39s baseline + ~3s of new gates).

**Verification:** 872/872 pytest, check_all green, every touched gate green
standalone. Net score 0 − 0 by "fired this month" — deliberately: this batch buys
recurrence-prevention, not live fixes.

**Where I left off:** Batch 4 committed and pushed. Only Batch 6 remains from the
scan backlog (tests for the 7 uncovered scripts, F20 re-seed path, Power>10 range
flag) plus the owner data-hygiene items (27 printings, 4 stale rationales,
Pensive Professor/Riverchurn Power-cell typos) and the strategic items
(matches.csv, deck lifecycle).

## Session — Batch 6, the coverage batch (2026-08-04, same session, fifth pass)

**The 2026-08 broad-scan backlog is CLOSED** — top-5 + Batches 1–6 all implemented
in one session. Block: `.cycle/blocks/2026-08-batch6-broad-implement.md`.

Six new test files (50 tests → **922 total in 24 files**) cover the previously
untested scripts, writers first: reconcile_crafts (tmp four-CSV world; the BS-16
DFC pin), sheets_sync (fake worksheet; the BS-03 header-only/shrink/dry-run
contract), validate (INV-01's letter + a characterization pin on the zero-row
pass), query+pool (the BS-10 color-set pins), scryfall (scripted urlopen; the
404/400/429/timeout classification incl. batch-5's no-retry-on-400), enrich (the
F-02 schema guard, F-11 vanilla rule, clean outage abort). The F20 outage→
re-enrich→re-seed path is tested end to end with a hand-grade-survives control.

**The Power range flag found a real mess:** 15 wishlist Power cells carry
0–100-style grades ('84','78','74','66','60','52'…) and were silently LEADING the
craft ranking — Pensive Professor sat at #1 with combined 42.3 on a 0–10 scale.
They now flag pow! and score 0.0 (loud under-rank replacing silent over-rank).
**Owner action: re-grade those 15 cells** (`wishlist.py --rank` names them); they
are hand-grade data per G-17 and were deliberately not auto-rewritten.

**Verification:** 922/922 pytest, check_all green.

**Where I left off:** everything committed and pushed on `claude/broad-scan-hekdj0`.
Nothing from the scan remains unimplemented. Open items are owner-paced: the 15
Power cells, 27 unverified printings, 4 stale tier rationales; then the strategic
bets (log the first matches — matches.csv is still empty — deck lifecycle,
rotation planning, keyword theming). Doc touch-ups queued for /sync-docs: the
[C-07] test count (18→24), G-19's range-enforcement note, Batch 4's carry-overs.
## Session — data-hygiene sweep (2026-08-04, sixth pass, post-#100)

The three standing warnings are CLEARED (commit `1899be3`, branch restarted from
the merged main): the 15 mis-scaled Power cells rescaled ÷10 (one batch graded
0–100; relative judgment and `hand` provenance preserved), all 27 unverified
printings repointed to held printings via `_printing_of` + `_safe_write_lines`,
and the four stale rationale claims rewritten from the current lists with every
new citation verified against oracle text (decks 40, 49, 51a — all three audit
"rationale is current"). **check_all is fully quiet: zero soft warnings**, for
the first time. 922/922 pytest. Remaining open items are purely strategic:
log the first matches, deck lifecycle, rotation planning, keyword theming.

**Update, same day: that /sync-docs pass has RUN** (commit `354b4ed`) — all of the
above landed (C-07 24 files + the six new layers described in cycle-config, G-19
range enforcement in bullet + long form, G-63's enforcer clause, C-01's Batch-4
addendum). Nothing from the 2026-08 broad scan remains queued, in code or in docs.

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

## Session 2026-07-31 — front-face-vs-metadata fixes (P6–P8)

Three fixes, all the SAME SHAPE and all found by deck work rather than by a scan: a
two-faced card's FRONT face and the metadata row disagree. Full block:
`.cycle/blocks/2026-07-front-face-metadata-broad-implement.md`.

- **P6 (COLOR)** `suggest_scored` scoped candidates by `Color(s)` — color IDENTITY — while
  the surrounding code derived the DECK's colours from printed COSTS. So `suggest` could
  never surface a hybrid or a colorless-cost card. 55 Standard red-pool cards were hidden
  from a mono-red deck. Now reads `_candidate_castability` (shared with `_castability_lint`).
  Verified live: `suggest 49 --unowned` now shows Decadent Dragon and Ramos, Dragon Engine.
- **P7 (TYPE)** `_primary_type` substring-scanned the whole `Front // Back` type line, so
  ANY DFC with a land back read as a Land — out of the curve, uncounted as a creature, and
  added to the land total. ~35 call sites inherited it. Land counts corrected: deck 49
  26→25, deck 51 25→24, deck 51a 25→24.
- **P8 (NAME)** `_printing_of` matched names exactly, so `swap --apply` wrote a DFC add as
  a bare `1 Runescale Stormbrood` — parses, passes INV-04, passes `legal`, fails an Arena
  import. It now matches a DFC front and returns the CANONICAL display name.

**755 tests pass** (+11). `check_all` green; the soft stale-rationale warning P7 raised is
clear on all five affected decks.

The class has four members — COST (G-02), COLOUR (G-58), TYPE and NAME — and it is now
written up as **G-63**, with the four incidents and their measurements in
`docs/gotchas.md`. Done in the same cycle by `/sync-docs`; nothing outstanding here.

**Deck work completed this session** (closing the P1–P5 block's open item 2): deck 51
tuned to tier **B** across four passes; deck **51a Overdue** built from scratch and graded
**B**; deck 49 (Scaleforge) refined across four passes. PR #91 created and squash-merged.
G-62 (blind mill is a CLOCK, not interaction) was added with its permutation proof.

**Where I left off.** Committed and pushed; nothing half-done. Open, all needing an owner
decision rather than work:
1. The `card-mana.csv` modal-DFC gap is STILL unfixed (carried from the P1–P5 block): 432
   two-faced rows hold one cost and need splitting into transform (correct) vs modal (data
   loss). `build_mana.py` is the fix site. It caused a wrong answer in chat.
2. `build_gallery.py` has its own `_primary_type` at line 217 with the identical P7 bug.
   Gallery type-breakdown only; no analysis path reads it.
3. Decks 51 / 51a read keepable **84.4%** on 24 lands, which `consistency` flags low. A
   25th land is a real open question in both — re-opened BY this fix, since the reading
   that closed it was the P7 artifact.
4. Whether to add Ramos, Dragon Engine to deck 49. Recommendation: skip — every available
   cut worsens the curve. If taken, cut Spinerock Tyrant or Rapacious Dragon.
5. Whether to build the third unblockable-tempo deck from deck 51's ~20-card overflow.
   Recommended as its own number **52**, not `51b`.

## Session 2026-07-31 — the two code follow-ons (FO-1, FO-2)

Both open code follow-ons from the P6–P8 block are now closed. Full block:
`.cycle/blocks/2026-07-follow-ons-broad-implement.md`.

- **FO-1** `card-mana.csv` kept only the FRONT cost of a MODAL double-faced card.
  `build_mana._castable_cost` now keeps every face you may cast, in Scryfall's own
  `A // B` convention — the shape of the faces decides, not a layout string, so a
  TRANSFORM DFC still keeps one cost. Re-priced with `--refetch`: **49 rows changed, all
  the same class**, 0 added/removed, no Mana Value or Keyword moved. Nothing downstream
  changed except `card.py`, which now prints `{U} // {2}{R}{R}{G}{G} (MV 1)`.
- **FO-1b** The front-face retry is now BATCHED (one `/cards/collection` call per 75
  names, resolving a DFC by its front name). Per-card it tripped Scryfall's rate limiter —
  432 lookups did not finish in ten minutes; batched, the same set is nine requests. This
  is what made the migration affordable.
- **FO-2** `_primary_type` now lives in `lib.primary_type`; `build_gallery.py`'s private
  copy carried the identical back-face bug and is deleted. The committed gallery's type
  breakdown was wrong: Creature 1071→1063, Enchantment 137→146, Land 108→106. The
  Enchantment shift is the transforming Sagas, which the whole-string scan called
  creatures.

**767 tests pass** (+12). `check_all` green, all ten gates OK. Regression scenarios 2 and
3 walked and PASS.

## Session 2026-07-31 — ownership counting + name keys (/broad-implement)

Five findings from a `/broad-scan`, implemented and gated. Full block:
`.cycle/blocks/2026-07-ownership-and-name-keys-broad-implement.md`.

One theme, and it is G-63's, one layer down: **the front-face rule is applied per call
site, so every new index that keys off a pool-shaped file re-introduces it.** Three of
the five were that shape.

- **F-14** `load_rarities` was the ONLY reference-table loader without a DFC front-face
  alias (the other five have it), because it reads the pool, which keys only the full
  `Front // Back` name. 47 roster names resolved to `""`, `_power_seed` fell to its
  default floor, and every mythic/rare DFC sorted UP the cut list — Ojer Axonil's
  `_cuts_power_adj` went −0.70 where the real mythic gives +0.17, so the nudge changed
  SIGN. Aliased in a second pass so a real card named `Front` can never be shadowed.
- **F-02** `_multiset` was not front-face aware, so `verify` reported phantom drift on an
  identical deck and `sync --apply` would have rewritten a stored `Front // Back` name to
  the bare front — P8's un-importable line, re-introduced from the other side, past a
  green INV-04 check. New `_ms_key` / `_ms_display`; `reconcile_lines` and the dashboard's
  client-side `parseLine` repointed at the same key.
- **F-03** `card.py` read owned quantity off ONE printing — on the surface G-01 makes the
  mandated pre-grading read. Rugged Highlands showed 1 against a real 3.
- **F-01** `import_collection.plan()` assigned rather than accumulated, so several export
  printings of one card collapsed onto one row and the last one won, order-dependently.
  Its verifier (`verify_ingest --exact`) had the mirror bug and now sums per card. Both
  halves had to move or the authoritative route has no working check.
- **F-04** `revert` picked the newest `.bak` by mtime, but `copy2` copies the SOURCE's
  mtime — so after one revert the ordering inverts and the next revert restored the state
  already discarded. `lib.latest_backup` selects on the creation stamp in the name.

**802 tests pass** (+35), `check_all` green, all twelve gates OK. Regression scenarios 1,
2 and 4 walked and PASS (4 headless via Flask's test client — it is F-04's acceptance
path); 3 not applicable, 5–8 are the browser/perceptual checks.

**Where I left off.** Committed and pushed; nothing half-done. Open:
1. **F-05 is confirmed live and was left out of scope** — `import_arena`'s `max()` is
   per-PRINTING while ownership sums across printings, so re-importing the same physical
   playset under a different printing inflates the count. Reproduced while walking
   Scenario 1. Its docstring promises the opposite.
2. Documentation updates the block lists — the tests file count (16 → 17), G-63 gaining
   its fifth and sixth members, `card.py` joining the fungibility rule's enforcement list,
   and the README's `import_collection` / `verify_ingest` semantics. Run `/sync-docs`.
3. The committed `dashboard.html` still carries the OLD client-side key; Pages rebuilds it
   on push to `main`. Not regenerated here to keep the diff free of ~1.2 MB of data churn.
4. Everything else from the scan (F-06…F-13, F-15…F-23) is unimplemented by scope. The
   highest-value remaining are F-15 (a dead no-op fallback in `reconcile_crafts`) and
   F-23 (the ledger has reached the pre-registered n=100 re-test threshold and four docs
   still quote the n=52 figures).

## Decided AGAINST (2026-07-31)
- Adding a `Layout` column to `card-mana.csv` to mark modal-vs-transform. It would have
  let `load_existing` re-fetch exactly the stale rows, but the 4-column header is
  hardcoded in four writers plus INV-03, and the same correction was reachable with a
  one-time `--refetch` that the tool itself produces. No bespoke migration script either
  (G-53: a capability nothing reaches).
- Applying FO-3 (a 25th land in decks 51 / 51a). Measured — keepable 82.5/84.4/86.0/87.4%
  at 23/24/25/26 lands, so the 25th buys +1.6pp keepable and −2.1pp screw for +0.4pp
  flood; take it in 51 (avg MV 4.03), leave 51a at 24 (avg MV 3.14). A deck edit is the
  owner's call under the standing "propose, don't apply until confirmed" rule.

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

## 2026-08 — deck-build tooling scan + implement (session: Void Demons)

Built decks **52 Void Demons** (mono-black Void aristocrats) and **52a Void Demons —
Dark Realms** (mono-black true reanimator) from a ~116-card concept pile, then used what
the build exposed as a scan.

**Findings recorded**: `.cycle/blocks/2026-08-deck-build-tooling-scan.md` — 10 findings,
each with a repro command. Provenance matters: none were caught by a gate. check_all was
green, preflight said READY and 804 tests passed through all ten.

**Implemented** (block: `2026-08-deck-build-tooling-broad-implement.md`): F-01 (deck-line
set/collector validated for the first time — `(ZZZ) 172` used to pass every gate), F-02
(`#: uncastable-ok:` header, so a reanimator's intentionally-uncastable bomb stops reading
as a build error), F-16 (an uncastable stray now CAPS the tier floor instead of SETTING
it), F-04 (new `deck.py targets` — does the deck contain targets for its own gated
effects), F-03 (three separate rationale-audit misses).

**Decided AGAINST / corrected in flight:**
- A generic "cards to discard" gate in `targets` — written, measured at 35-for-everything,
  removed. Same saturation class as `suggest`'s Decks column. Pinned by a test.
- A distance-window `wrong_exclusion_claims` — 10 roster false positives at ±400 chars,
  37 when split on `;`. Rewritten around clause SHAPE; now 0.
- Over-weighting `similar`. The user's standing position, recorded in F-06: **some card
  overlap between decks is acceptable.** Two good cards (Bringer of the Last Gift, Forum
  Necroscribe) were cut from 52a purely to lower a similarity number and were reinstated
  on merits. `similar` is a shortlist for "is this a new deck", not a constraint.

**All ten findings are now implemented** (second block:
`2026-08-deck-build-tooling-remaining-broad-implement.md` covers F-05…F-10). One fix was
designed, measured and REJECTED: tightening `fit_strength`'s signature branch fixed
`screen`'s KEY saturation on deck 52a (51%→11%) but broke deck 30's documented
counter-doubler rescue (21%→1%), so the saturation is REPORTED instead and the real fix
is left open as a follow-on.

**Still open**: 27 unverified printings and 4 stale
rationale citations are now VISIBLE on the roster and unfixed — both were invisible before
this session. The user plans 1–2 gold bombs in 52a, which is what F-02 unblocks.

**Where I left off**: all four findings implemented, 826 tests green, check_all clean with
2 new (intended) soft warnings. Documentation updates are listed at the end of the
implement block and NOT yet applied — run `/sync-docs`.

---

## Session 2026-08 (later) — role-coverage gate + batched classifier fixes

**Context.** A long deck-building session on the Grand Lotus family (decks 54 / 54a / 54b)
kept turning up holes in `deck._ROLE_PATTERNS` — eight of them, every single one found by a
human reading a card rather than by any gate. `/broad-implement` was run on the two
recommendations that came out of asking what the common thread was.

**The thread, which is the finding worth remembering:** `_ROLE_PATTERNS` is a WHITELIST of
phrasings, and Magic templates the same effect several ways. A card templated a way no
pattern anticipates scores ZERO roles, and the tier floor, the `cuts` ranking, the quality
guard and check_all's own reporting all inherit that as fact. The failure is never an
error and never an over-count — always a silent under-count.

**Completed:**
- **REC-1** — `scripts/check_roles.py` + `scripts/role_baseline.txt`, on the
  `keyword_baseline.txt` design. Soft, non-gating warning in check_all. Baseline is 367.
- **REC-2** — three classifier holes fixed in ONE pass (deliberately batched: each fix
  costs a roster-wide prose sweep, and three were already done this session):
  any-colour ramp, Etali-style impulse, casting off the top of the library.

**The ramp hole was the biggest single one found all session.** The pattern required a
literal `{` after "add", so `{T}: Add one mana of any color` — the templating of EVERY
rainbow source — matched nothing. Bloom Tender, Great Divide Guide, Springleaf Drum and
Agatha's Soul Cauldron all read as having no functional role, in three decks whose #1
graded weakness is the manabase.

**Decisions made:**
- check_roles is DECK-scoped, not pool-scoped. A pool-wide scan of ~30k cards is noise; a
  card in a deck is one some model has already been asked about.
- The gate is SOFT. A genuinely roleless card (a vanilla body, a pure combat trick) is a
  legitimate zero and breaks no invariant.
- The baseline is read as a DELTA, not a target. 367 is not a backlog to drive to zero.
- The Treasure-reminder-text over-fire on the ramp patterns was left in, documented in
  place, because Ramp / fixing does not feed `deck_quality_vector`.

**Corrected in flight:** the first draft of the ramp pattern used a paraphrase where Bloom
Tender's real text is the Vivid form ("add one mana of THAT color"). The test written from
the card's ACTUAL text caught it — paraphrasing a card into a fixture is how a pattern gets
written for a card that does not exist.

**Test double found and updated, not reactively:** `check_suggest.py` anchor 15 and its
pytest twin asserted a rainbow fixer ranks most-cuttable on the premise that it has "no
classified role". The ramp fix falsifies that premise; both were re-premised rather than
deleted, keeping the `add_is_fixer` guard assertion.

**Where I left off**: 861 tests green, all fourteen gates green, check_all clean with the
4 pre-existing stale rationales unchanged. CLAUDE.md gate count and subsystem inventory
updated. One documentation judgement left for `/sync-docs`: whether the whitelist-failure
lesson deserves its own `[G-nn]` anchor — it currently lives only in check_roles.py's
docstring, and K-12 covers "counts under-count" but not "the pattern set is a whitelist".
Also still open and unrelated: the queued swap plans for decks 54 / 54a / 54b in
`.cycle/54-pile-reanalysis.md` §5 and §5b.

---

## Session 2026-08-04 (continued): the three Mardu decks drafted, pile doc closed out

**Completed:** /draft-deck for all three decks the 131-card pile analysis produced —
55 Mardu Waves (Mobilize pulse; A PROVISIONAL at the floor), 55a Mardu Spellstorm
(cast-cadence; A PROVISIONAL), 55b Mardu Airbender (exile-cast; B PROVISIONAL, argued
under the A floor). Full draft-deck pipeline each: text read, legal, preflight READY,
mana + consistency (manabases rebalanced from the cast-on-curve table: 55 traded 2
Swamps to Plains for the WW three-drops, 55a traded 4, 55b dropped Swamps entirely for
its 2-pip B splash), targets, similar, screen of the rejected/parked pile, cuts,
tier + audit-rationale, dashboard rebuild, verify-commit tail. Commits a6f6caa /
2b6774f / 7d43477 on claude/broad-scan-hekdj0.

**Decisions made:**
- 55b graded UNDER its metrics floor (B vs A) — payoff concentration + protection 2 +
  card-adv 0; the rubric permits it and the header argues it.
- Quintorius Kand swapped in over Stand Up for Yourself in 55b after screening KEY —
  Discover fills the measured zero card-advantage axis; same copy sits in 45/24/24b
  (decks share the collection).
- Six roleless cards baselined rather than pattern-edited (Delney precedent; a role
  pattern edit needs a roster-wide diff per K-12 and is cycle work, not draft work).
- The pile doc's "flashback pairs with Zuko/Appa" claim was WRONG (they trigger on
  exile-casts only; flashback casts from the graveyard) — corrected in 55b's notes.
- Deck 45 overlap surfaced by `similar` and stated honestly in 55b's archetype rather
  than pivoting the build: different enabler suite (own-board exile vs library
  impulse/heist), different win-con (wide vs drain), 3 shared nonland cards.

**Decided against:** churning the three 60s toward the screen's KEY bench (Cruel
Administrator, Shock Brigade, Reigning Victor…) — the consolidated plan already ranked
them below the ★★★ picks and nothing expired; they are recorded as the bench in 55's
notes. Also against hand-writing rotation years — deck.py rotation is the source.

**Where this leaves off:** `.cycle/55-mardu-analysis.md` deleted (findings folded into
the three deck headers). check_all clean, zero soft warnings, 922 tests green. Open:
the 54-family swap plans in `.cycle/54-pile-reanalysis.md` (§5/§5b) remain unapplied;
no PR open for the current branch (user has not asked).

## Session — the Mardu pile family: seven decks, an addendum, and the follow-on tunes (2026-08-04/05)

The 131-card Mardu pile (five batches, analyzed prior session) was drafted into decks
55 / 55a / 55b; the user then extended the pile with a 59-card addendum carrying three
new concepts, of which two survived contact with the counts: T (ultra-tall) became deck
56 + variant 56a after a full drafted A/B (white beat green on every measured axis;
green revived as 56a WITH the protection suite the A/B never tested), and J (Jeskai)
became deck 57 (prowess tempo; the pile holds zero mono-U spells — recorded as the
first tuning axis). Concept G (RGB) was rejected BY COUNT (zero G/B cards; deck 8
already owns BRG sacrifice) — then resurrected on the user's sharper idea (Treasure
economy) once a whole-pool payoff sweep (108 payoffs / 75 producers) showed the token
economy identity unclaimed: deck 58 Gold Standard, around Roxanne's token-mana
doubling. Follow-on tunes landed via screened + quality-guarded swaps (55a ×2, 55 ×2,
58 ×1, 55b flex line); a ten-card revival pass produced seven pending placements the
user is still weighing (list + cut candidates in NEXT-SESSION §3.2), and a
craft-priority read (Castle Doom/Electro/Appa/Cosmogrand as direct crafts; FDN > TDM >
OTJ packs; avoid rotating LCI/WOE). Decided AGAINST: a generic RGB goodstuff deck (no
identity left), Voja (0 Elves), Charging Strifeknight to 55a (outlet recount: Pursue
already covers it), Speedball (its rider theme was cut from 55a's final), Taii into 55
initially — reversed later by the user reading the amplifier correctly (every
noncombat-damage instance that turn). Doc residuals G-66 (token false-thin) and K-03
(type-keying tag invisibility, Gilgamesh/deck 39) recorded in CLAUDE.md + gotchas.

## 2026-08-05 (later) — /broad-implement #1-8 (session tooling findings)

Implemented all eight findings from the post-work tooling assessment (summary block:
`.cycle/blocks/2026-08-tooling-followup-broad-implement.md`):
rot flags on `check`/`wildcards` (#1), shorthand-citation DETECTION in the rationale
audit with roster-sweep-verified FP fixes (#2 — found one true positive, deck 21's
archetype header, fixed), vanilla-vs-gap messaging (#3), `resolve` totals + `--expect`
(#4), `wildcards --dedup` (#5), counters-payoff patterns from Wundagore/Kutzil printed
text (#6 — 10 decks gained payoffs, 0 lost), matches.csv noted as process debt (#7),
`make postedit` (#8). 936 tests green, check_all green.

Decided AGAINST: encoding vanilla-ness in the pool CSV (message-level fix suffices;
a data-format change would touch every reader for marginal gain).

Where I left off: /sync-docs is owed (G-26/G-30 claims, draft-deck skill line, new
command mentions). NEW actionable from #1: deck 49 has five ⚠rot~2026 craft targets —
wants the deck-28-style rotation-proofing pass before any wildcard goes there.
October rotation pass (28 flex block, 28a, 36 Kutzil successor) still pending.

## 2026-08-06 — decks 59-63, tooling batch, ingests, doc sync

Completed: decks 59/60/60a/61/62/63 (four built entirely from owned cards); the
eight-finding tooling batch (rot-flagged craft views, shorthand staleness DETECTION,
`wildcards --dedup`, `resolve --expect`, vanilla messaging, counters-payoff patterns,
`make postedit`); three ingests (14 crafted + 2 crafted + 16-card TDM pack) with all
placement swaps applied; rotation-proofing of decks 28 and 36; tunes of 9, 29, 36, 37b,
25 (reported, not applied); a plural-passive counters-payoff pattern fix; and a
date-adjacency FALSE POSITIVE fix in the rationale figure matcher.

Decided AGAINST (do not re-propose without new information):
- **Blink in deck 63.** Measured 7/35 ETB density, and blink ERASES +1/+1 counters, so
  it fights the engine (now recorded under G-42). Daydream is benched as PROTECTION only.
- **A new Abzan deck was NOT needed for Armament Dragon** — four WBG decks already exist
  (6, 13, 21, 20b). What was missing was the counters ANGLE, which became deck 63.
- **Deck 49 Route A** — proposed, measured, and deferred by the user ("hold off for now").
  Queued, not rejected; see NEXT-SESSION §3.

Where I left off: doc sync applied (CLAUDE.md stale `.cycle/54-pile-reanalysis.md`
pointer removed — the file was deleted when its swaps landed; test count 24→25; G-42
extended with the blink/counters finding), then PR opened and merged.

## Session — six ingest batches, ~35 placements, and Chandra into five decks (2026-08-07)

**No code changed.** Every commit after `0c47ab4` is data, decks or docs; `scripts/` is
untouched apart from `role_baseline.txt` moving with the roster. So a resuming session can
trust the 08-05/06 notes above as a description of current tooling behaviour.

**Ingests (six batches, ~97 cards, plus Chandra).** Batches 8–13, each run through
`/ingest` and confirmed by `verify_ingest` rather than by `check_all` alone — check_all
proves the library is self-consistent, not that it contains what was pasted. Three things
worth carrying forward: batch 9 needed comma restoration on five names (Arena export
strips them); batches 11–13 contained cards that are **not Standard-legal**, called out in
their commits instead of quietly kept; and batch 11's Progenitus lands plus batch 12's
speed/Mount cards closed most of decks 60/60a/61's gap. Deck 35a is now **one card
(Omniscience) from buildable**.

**Placements (~35 swaps).** Applied through the standard chain — `quality --json` before,
`swap --apply`, `quality --vs`, `preflight`, `tier --audit-rationale`, stale prose fixed in
the SAME commit. The audit earned its keep repeatedly: seven stale figures and one
cut-card citation in a single batch, three more figures and two prose claims in the Chandra
pass. G-05 section-comment relocations were needed on roughly ten swaps, which is close to
every swap that crossed a section boundary — the warning is doing its job and the fix
stays manual by design.

### Chandra, Spark Hunter — the placement pass worth not re-deriving

Crafted mid-session, then placed in **26b, 48, 58, 10 and 45a**, with **48a** already
maindecking her as a craft target (she simply became owned, so that deck's plan dropped by
one). One owned copy plays in all six simultaneously.

The selection is the cleanest worked example of G-61 so far. `suggest-homes` rated her KEY
in **14 of 42** decks, nearly all on the generic red trio `burn, card draw, noncombat
damage`; nine of those fourteen run zero artifacts, where she is a four-mana looter. The
five real homes were found by hand-counting the resources her text names — artifact cards,
token producers, Vehicles, Mayhem cards — and two of the five break the obvious pattern:
deck 58 holds **zero artifact CARDS** and is among the best homes (its resource is tokens,
the G-66 residual its own notes already flag), while 45a holds two and is a good home for a
reason unrelated to artifacts (five Mayhem cards want a free repeating discard). **The
table is in `docs/gotchas.md` under `[G-31]`; do not re-measure it.**

### Two findings recorded as rules

- **`[K-14]` — a draw clause behind an ACTIVATION cost is invisible to `role_tally`.** All
  Card-advantage patterns are trigger-shaped, so `+1: Draw a card` / `{2}{U},{T}: Draw a
  card` / `{1}, Sacrifice this artifact: Draw a card` all score zero. Measured: 187 pool
  cards (24 planeswalkers), ≥12 on the roster. It surfaced because deck 58's quality guard
  reported `card advantage 4→3` on a swap that RAISED real card advantage — Elvish
  Archivist's draw keys off enchantments entering and the deck runs two, while Chandra
  draws every turn from a loyalty ability nothing parses. The mirror image rode along:
  interaction read 8→9 (58) and 14→15 (10) because her `−7` emblem parses as removal.
  **This is the highest-value small pattern job available** — the measurement is done.
- **`[G-31]` gained two residuals.** A zero-row `suggest-homes` result is a THEME miss, not
  a colour-identity fact — that misread was written up this cycle as "you have no Abzan
  deck" against four existing WBG decks, and it is K-13's shape one layer up: the sweep did
  not fail, it answered a narrower question than the one reported. And KEY scores theme
  overlap alone, which is why the count-first habit above was needed at all.

**Also found, unfixed and cheap to check elsewhere:** deck 26b's `#: protect:` header named
**Summon: Bahamut**, a card the deck has never run (it went to 48a in the pivot its own
notes record). A protect entry for an absent card shields nothing and inflates the
build-around count the zero-protection flag is read against, and **no gate catches it**.
Worth a roster-wide sweep next time someone is in the tooling.

Where I left off: five Chandra placements committed and pushed, `/sync-docs` applied
(K-14 added, G-31 extended, NEXT-SESSION and STATE refreshed). No PR opened yet for the
work after `0c47ab4`.

### Tail of the same day: K-14 fixed, then the two cheap tooling jobs

**K-14 shipped** (PR #107). The role tally now counts a draw reached by PAYING a cost. The
part worth keeping is the METHOD, not the patterns: the first draft counted
`Sacrifice this land: Draw a card`, which would have swept in a whole common tapland cycle
and taken the change from 24 decks to 58. Measuring the roster BEFORE landing it caught
that, and what shipped moved 18 decks up, 12 down, interaction unchanged, and **zero tier
floors**. Sixteen decks were left with a stale `#: tier:` figure and were re-grounded in
the same commit; deck 21a's 3 → 5 is flagged in-file for a HUMAN re-grade.

**Then the two jobs this file had been listing as cheap and un-owned:**

1. `Rogue's Passage (FDN) 264` → `(HOC) 212` in decks 26a and 50, from `deck.py resolve`
   rather than by hand (G-65). Oldest standing soft warning, now gone.
2. **G-68**, and it is the more interesting of the two. `#: protect:` and
   `#: uncastable-ok:` are card-name lists the tooling reads as INSTRUCTIONS, and nothing
   validated that a name matches a card in the deck. A stale `protect` entry protects
   nothing (`cuts` excludes by name) AND inflates the build-around count the
   zero-protection flag prints — deck 26b reported five against a real four inside the
   sentence arguing its own tier cap. `deck.header_card_staleness` now sweeps the roster
   in `check_all`, joined on `_ms_key` so a front-face DFC name does not read as stale.
   **It found two more on its first run**: deck 56's Boros header protected Ashroot Animist
   and Halana and Alena — both R/G, both living only in variant 56a. A variant split left
   the parent's header behind, which is presumably how 26b's happened too.

**`check_all` now reports ZERO soft warnings**, the first time this cycle. 951 tests.

The pattern across both fixes, worth stating once: "no gate checks this" was true twice in
one day, on the same shape — a role bucket nothing exercised, and a header nothing
validated. Both had been live for months behind fully green gates, and both were cheap to
fix once someone said the sentence out loud.
