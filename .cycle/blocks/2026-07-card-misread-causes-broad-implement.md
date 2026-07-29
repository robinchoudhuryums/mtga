---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
  1 — `cuts` is blind to MULTIPLIERS: a doubler's value is in the rest of the deck, and both halves of the cut score can't see it (Delney ranked as deck 46's weakest card). Includes a missing LIFEGAIN doubler axis.
  2 — A candidate pile graded ONCE keeps stale verdicts after the plan changes (deck 46's 76-card pile was screened against an abandoned plan; only re-raised cards got re-graded).
  3 — Nothing asked whether a candidate is a STRICT UPGRADE of a card already in the deck (Prayer of Binding is Liminal Hold + Flash; Liminal Hold was in the 60).

Files modified: scripts/deck.py, scripts/check_suggest.py, scripts/check_patterns.py,
tests/test_deck.py, tests/test_deck_models.py, .claude/commands/draft-deck.md,
.claude/commands/tune-deck.md, CLAUDE.md, dashboard.html

CHANGES:
1 | scripts/deck.py | Added `_CUTS_MULT_CAP` / `_CUTS_MULT_MIN_SOURCES` / `_cuts_multiplier_adj`, wired into `rank_cut_candidates`'s keep-score and rendered as a `✱multiplier` flag in `cmd_cuts`. Routes the EXISTING `doubler_axis`/`doubler_support`/`doubler_restriction` primitives (built for suggest-homes) rather than adding a second model. Added a `lifegain` axis to `_DOUBLER_AXES`, requiring the literal "twice that much" so a plus-N replacement (Angel of Vitality) is not read as a doubling.
1 | scripts/check_suggest.py | Anchor 16: `_cuts_multiplier_adj` bounded / zero below floor / never negative / rising with support, plus lifegain-axis detection and its plus-N discriminator.
1 | tests/test_deck.py | `TestCutsMultiplierCoSignal` (3 tests); lifegain-axis + plus-N tests added to `TestDoublerCoSignal`.
1 | tests/test_deck_models.py | WIRING anchor: two POOL_CARDS entries (a doubler + a feeder) and two tests comparing one doubler's keep-score across decks with and without feeders, holding every other term constant. Verified to FAIL when the term is unwired.
2,3 | scripts/deck.py | New `deck.py screen <id> <names…>` subcommand + `_upgrade_clauses` / `_UPGRADE_SELF_RE` / `strict_upgrades`. Re-scores a candidate list against the CURRENT deck (fit strength, roles, shared themes, legality, owned/craft), flagging `★ STRICT UPGRADE` and `✱ multiplier`. `--full` prints oracle text.
2,3 | .claude/commands/draft-deck.md, tune-deck.md | `screen` wired into /draft-deck Stage 5.2 and /tune-deck 6a with the re-run-after-any-plan-change instruction (required by the check_commands gate).
3 | scripts/check_patterns.py | Registered `deck._UPGRADE_SELF_RE` (the completeness gate flagged it unregistered on first run).
— | CLAUDE.md | Documented all three under Common Gotchas, plus anchor 16, the test-file attribution, and Regression Scenario 2.

TEST RESULTS: passed. check_all clean (2 pre-existing soft warnings: unindexed
mechanics `renew`, `triple`). All 9 model gates green — check_patterns 145 live,
check_suggest OK, check_commands OK (33 subcommands reachable), check_rankings,
check_tier, check_engines, check_colors, check_dfc, check_themes all OK. pytest
645 passed. `deck.py --help` and `screen --help` OK.
Regression Scenario 2 walked in full (21 commands): all PASS after one fix — see
below. `check 46` exits 1 by design (WIP craft targets), confirmed against a
buildable deck.

REGRESSION RISKS:
- **One real regression was introduced and caught by the Scenario 2 walk**, not by
  the test suite: `rank_cut_candidates`'s row tuple grew a field, and `cmd_cuts`
  unpacks it positionally in TWO places. I updated the table loop and missed the
  oracle-text loop, so `deck.py cuts` crashed on every deck. Fixed; both loops now
  unpack 13 fields. My earlier smoke test piped through `sed` and truncated the
  traceback away — the scenario walk is what exposed it.
- Other `rank_cut_candidates` consumers (`deck.py` swap-telemetry at ~4665,
  `tier --to` at ~7827, check_suggest 13a, tests/test_recommendations.py) read only
  `r[0]`/`r[1]` or unpack with `*_`, so appending a field is safe for them. Verified
  by grep and by the passing suite.
- `cuts` keep-scores changed for 15 cards across 11 of 64 decks (all genuine
  doublers with ≥4 feeders). Every non-doubler is unchanged — the term is exactly 0
  otherwise. `recommendations.csv` rows are captured at swap time, so history is
  unaffected.
- `doubler_axis` gained a 4th return value (`"lifegain"`). Callers switch on the
  axis via `_DOUBLER_AXES` lookup, so the new value flows through; pool detections
  went 53 → 57.

INVARIANTS AT RISK: None. No canonical CSV was written; no derived file rebuilt
except dashboard.html (regenerated, as its Deploy Command requires). INV-01…04 all
verified green by check_all after every step.

NET SCORE: 3 production fixes − 0 new failure modes = 3
  (a) Would each have fired this month? 1 YES — it fired repeatedly this session.
      2 YES — it fired on the deck-46 pile. 3 YES — Prayer of Binding.
  (b) New failure mode introduced? The cuts unpack crash was introduced AND fixed
      within this session before commit, so it reached neither main nor the user;
      counted as caught, not shipped.

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push (done). Dashboard: rebuilt via
`python3 scripts/build_dashboard.py`; `.github/workflows/pages.yml` republishes it
on push to `main`.

FOLLOW-ON ITEMS:
- `strict_upgrades` is text-containment only, so it misses semantic upgrades (a
  strictly better body at the same cost, a mode that dominates another). Widening it
  needs a card-comparison model, which is a much larger piece — its silence is
  documented as not-a-verdict rather than papered over.
- `deck.py screen` does not yet flag the MIRROR of a strict upgrade: a candidate
  strictly WORSE than something already in the deck. Cheap to add on the same
  primitive if it proves useful.
- Cause (1) from the reflection — anchoring on a card's first ability when its
  abilities point in different strategic directions — is only partly addressed. The
  `✱` flag catches the multiplier subclass; a general "this card's abilities disagree
  with each other" detector was scoped out as speculative.
- Two pre-existing soft warnings remain: unindexed mechanics `renew` and `triple`.
  Out of scope here; triage per the keyword gotcha (card-uniqueness across the POOL).

DOCUMENTATION UPDATES NEEDED:
- None outstanding — CLAUDE.md was updated in this session (Common Gotchas ×2,
  check_all gate list for anchor 16, Testing subsystem attribution, Regression
  Scenario 2). README was not touched: `screen` is a build/tune workflow command and
  README's deck-tooling section describes the analysis surface, so /sync-docs may
  want to add it there.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
