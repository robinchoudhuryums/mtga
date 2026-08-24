---TARGETED IMPLEMENTATION SUMMARY---
Scope: Analysis
Actions completed: B1, B4, B3, B2
Actions not completed: All completed. (B5/B6 remain deferred by the handoff — determinism
coverage beyond the pinned 6 of 34 subcommands, and the documented model residuals G-33 /
G-66 / K-09, each of which needs its own K-12 roster diff and decision.)
Files modified: scripts/deck.py, scripts/check_docs.py, tests/test_deck.py, CLAUDE.md,
docs/cycle-config.md, dashboard.html

CHANGES:
B1 | deck.py (`pair_adds_with_cuts`, `_cut_feeds_axis`, cmd_tier ~11186) | The tune plan
  paired fillers with cuts by positional `zip`, blind to what the cut DOES — so a plan
  closing an interaction gap could propose cutting an interaction card, netting zero and
  reporting "still short" while telling the reader to pick another cut. Replaced with a
  pairing that skips a cut feeding the add's own axis, consuming each cut once, and falls
  back to the weakest remaining cut (keeping the existing ⚠) when nothing neutral is
  left. Roster effect: self-defeating pairs 3 -> 2, and plans REACHING the A floor went
  from 8 to 10 of 11. | F1
B4 | tests/test_deck.py | 7 tests on the pairing, incl. the fallback, cut consumption,
  order preservation and the deliberate cross-axis allowance. Watched failing against a
  mutant that restores the positional zip — exactly the two tests naming the bug fail. | F1
B3 | CLAUDE.md [C-01]/[G-55], docs/cycle-config.md | `check_all` calls NO `cmd_*` — 16
  model functions and zero command functions — which both docs claimed otherwise for a
  year. Corrected, and the consequence stated: the untested surface is the whole COMMAND
  layer, not just the argparse tree. B1's bug lived exactly there, which is cited. | F3
B2 | check_docs.py (`_live_figures`, `figure_drift`), CLAUDE.md | New SOFT check
  verifying CLAUDE.md's mechanically-derivable figures against live data, plus the six
  stale figures corrected (K-09 138->153, K-07 266->291, K-05 351->357, K-09 blanks
  380->371, C-02 58->62; G-69's 425 re-dated rather than bumped, since it describes a
  past incident). A regex that stops matching is itself reported — a silently-dead
  figure check reads exactly like a clean one. | F2

TEST RESULTS: passed — 1443 passed, 1 skipped (was 1436). check_all green with 1 soft
warning (the 4 accepted dead tutors). check_patterns 268 live, check_commands OK,
check_tier OK, check_rankings OK, check_docs OK with zero figure drift, argparse builds.
Three mutants watched failing: positional-zip restored (B1), a re-staled figure (B2), and
a figure regex that matches nothing (B2).

REGRESSION RISKS:
- B1 changes what `tier --to` PRINTS, not what any model SCORES. `tier_band`, `role_tally`
  and `cut_keep_score` are untouched, so no roster re-grade and no K-12 diff was required;
  check_tier and check_rankings confirm.
- B1's fallback preserves the old behaviour exactly when no axis-neutral cut exists, so a
  deck whose entire cut pool feeds the axis gets the same plan and the same warning it did
  before — the change can only improve a pairing, never remove one.
- The 2 remaining ⚠ lines (decks 22, 61) were verified CORRECT rather than residual: they
  are CROSS-axis trades (interaction up, card advantage down where the sum has slack), and
  deck 22's plan still reaches the A floor. Only the axis being RAISED is protected, which
  is the documented intent.
- B2 is soft and prints regardless of the structural result, so it cannot turn check_docs
  red. Landing it hard was considered and rejected: these figures are partly historical
  statements, so a hard gate would break the build on an ordinary tagger edit — the way a
  gate gets routed around.

INVARIANTS AT RISK: None. No invariant reads the tune plan (it prints, never writes), and
B2/B3 touch documentation only.

NET SCORE: 2 production fixes (F1 degraded a planning tool and was hit live; F2
misinformed any reader) + 1 documentation correctness fix (F3) − 0 new failure modes = 3

INVARIANT CANDIDATES:
- "A tune plan must never pair an add with a cut that feeds the axis being raised."
  Pinned behaviourally by B4 rather than added to the invariant library: it is a property
  of one command's output, not a repo-wide data invariant, and check_all does not reach
  the command layer at all (F3).

OPERATOR ACTIONS / DEPLOY:
- None.
Deploy: Data + tooling ship by commit/push. Dashboard rebuilt via `make postedit`; Pages
republishes on push to main.

FOLLOW-ON ITEMS:
- deck.py: the COMMAND layer (`cmd_*`) is exercised by `tests/test_cli.py` and a smoke
  step only. F3 makes the size of that gap explicit and B1's bug demonstrates it; a
  broader `cmd_*` output-contract layer is the natural next investment.
- check_docs.py: `_live_figures` covers 5 claims. Extending it is cheap and each entry
  pays for itself, but a pattern must be specific enough not to match a neighbouring
  sentence — the PATTERN MATCHED NOTHING report exists for the other failure direction.
- Presentation subsystem remains unaudited and holds the biggest untested surface:
  app.py's Flask tests skip in this environment, build_dashboard.py (2,685 lines) has no
  dedicated test file.

DOCUMENTATION UPDATES NEEDED:
- Done in this change: C-01, G-55 and docs/cycle-config.md corrected; six figures updated.
---END TARGETED IMPLEMENTATION SUMMARY---
