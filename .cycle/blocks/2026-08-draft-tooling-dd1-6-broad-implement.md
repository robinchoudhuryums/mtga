---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: DD-1 (resolve printing preference), DD-2 (resolve --check strict
printing verifier), DD-3 (targets copula gate hole), DD-4 (pool.py --within subset
filter), DD-5 (similar headline names the card-overlap neighbour), DD-6 (duplicate
deck-id + variant-shaped-directory hard checks)
Files modified: scripts/deck.py, scripts/pool.py, scripts/lib.py, scripts/check_all.py,
.claude/commands/draft-deck.md, CLAUDE.md, tests/test_deck.py, tests/test_lib.py,
tests/test_check_all.py, tests/test_query_pool.py

CHANGES:
DD-1 | scripts/deck.py | _printing_index prefers owned∩pool > owned > pool (was: last
      library row wins). Front-face aliasing moved to a SECOND pass (G-63). Changes the
      resolved printing for 3 live cards (Lightning Strike, Scout the City, Spider-Rex).
      NOTE: the recorded Llanowar incident was a FALSE PREMISE — the FDN printing is not
      owned, so the old M19 answer was defensible; the multi-printing arbitrariness was
      the real flaw and is what this fixes.
DD-2 | scripts/deck.py, .claude/commands/draft-deck.md, CLAUDE.md | `resolve --check
      <deck-id-or-path>`: strict verification of a deck file's (SET) COLLECTOR# fields
      against known printings — unheld printing FAILS (G-65 keeps it soft in check_all;
      a drafted file's lines should come from resolve). Prints the resolver's preferred
      printing beside each ✗. draft-deck Stage 4 step 0 now mandates it; G-65's rule
      text points at it.
DD-3 | scripts/deck.py | gy_type gate regex reads both copula spellings — "there's" AND
      "there is" — so Dawnhand Eulogist's dead Elf rider in deck 77 now reports
      "✗ NOTHING" (was invisible; Dragonfly Swarm's contraction form was always seen).
DD-4 | scripts/lib.py, scripts/pool.py, .claude/commands/draft-deck.md | lib.color_within
      (SUBSET semantics, colorless passes) + pool.py --within — the castable-in-my-deck
      survey filter both 2026-08-21 drafts hand-scripted. --owned --within WRG --legal
      standard: 1320 cards vs --color WRG's 16. draft-deck Stage 1 teaches it.
DD-5 | scripts/deck.py | similar's ⚠-Closest headline, when the closest-by-theme deck
      shares ≤5 cards and another deck shares more, names that card-neighbour inline
      (deck 77's headline now points at 64; deck 31's at 75). by_cards computed once.
DD-6 | scripts/check_all.py | check_decks: duplicate deck ids are a HARD error naming
      both paths; a variant-shaped top-level directory (decks/NNa-*/) is a HARD error —
      the 73a near-duplicate shape, which the id check alone cannot see.

TEST RESULTS: full suite passed (exit 0) after one test-double fix — test_query_pool's
_pargs namespace lacked the new `within` attr (3 failures on first run; fixture updated,
matches() also hardened with getattr). New tests: TestColorWithin (6),
TestPrintingIndexPreference (4), TestResolveCheck (3), copula gate fixture (1),
--within behaviour (1), duplicate-id + variant-dir (2). check_all: all invariants hold.
deck.py --help builds (G-55).

REGRESSION RISKS: _printing_index return content changes for 3 multi-printing cards
(strictly toward the pool-canonical owned printing); its consumers are cmd_resolve and
cmd_sync (display only). similar's headline gains a sentence — test_determinism's
similar leg is seed-comparison, keys are total-order, safe. matches() gains one filter,
default None = no-op.

INVARIANTS AT RISK: None — INV-04 is TIGHTENED (two new hard error classes), verified
green on the live roster before landing.

NET SCORE: 4 production fixes (DD-2, DD-3, DD-4, DD-6 all fired or were needed live
this month) − 0 new failure modes = +4  (DD-1 half-overturned premise, DD-5 polish)

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: N/A for code (data + local tooling ship by commit/push); dashboard pipeline
untouched.

FOLLOW-ON ITEMS:
- query.py and wishlist.py still expose only --color; a --within there is the same
  one-line wiring if wanted.
- DD-1 residual: when owned∩pool is empty, resolve still returns the owned printing —
  correct for "matches what you have", but a --prefer-pool flag could serve pasting
  into a fresh Arena import.
- The variant-shaped-directory rule assumes the decks/NN-parent/NNa-*.txt convention;
  if a future reorganisation moves variants top-level, the check must move with it.

DOCUMENTATION UPDATES NEEDED:
- Done in this pass: CLAUDE.md G-65 (resolve --check), draft-deck.md Stages 1 and 4.
- docs/gotchas.md G-65 long form could mirror the --check sentence (not blocking).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
