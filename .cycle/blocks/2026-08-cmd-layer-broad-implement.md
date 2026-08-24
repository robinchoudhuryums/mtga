---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: the Analysis-audit follow-on — the `cmd_*` COMMAND layer is
exercised by `tests/test_cli.py` (help only) and a CI smoke step, nothing more. F3
measured the gap (`check_all` reaches ZERO `cmd_*`) and B1's bug demonstrated it.
Files modified: tests/test_cli.py, docs/cycle-config.md, CLAUDE.md

CHANGES:
cmd-layer | tests/test_cli.py | New `TestSubcommandsActuallyRun`: every deck.py
  subcommand RUN for real against a live deck, asserting it raises nothing, exits
  cleanly, and PRODUCES OUTPUT. The output contract is the one no other gate checks — a
  command that silently prints nothing is indistinguishable from a healthy one
  everywhere else in this repo. `_ARGS` is exhaustive by construction: a subcommand
  missing from it FAILS rather than being skipped, the same discipline check_commands
  applies to workflow reachability where a stale exemption is itself a failure (G-53).
cmd-layer | tests/test_cli.py | New `TestTunePlanOutputContract`: the specific
  render-time layer B1's bug lived in — a plan must not pair an add with a cut feeding
  the axis it is adding, and deck 43's plan must reach the floor it claims. This catches
  B1 at the CLI level, where nothing would have.
cmd-layer | tests/test_cli.py | `_run` gained a `stdin` parameter so `sync` is fed a real
  `deck.py arena` export rather than an empty pipe, exercising its matching path instead
  of its empty-input guard.
cmd-layer | tests/test_cli.py docstring | Corrected the same stale claim B3 fixed in
  CLAUDE.md: the file asserted `check_all` "calls cmd_* directly". It calls 16 model
  functions and no cmd_* at all. A test double encoding the OLD understanding of the very
  gap it exists to cover.
cmd-layer | docs/cycle-config.md [C-07], CLAUDE.md | The C-07 inventory described
  test_cli.py as a help-only entry-point layer. Updated to name the command-output layer,
  the exhaustive-_ARGS rule and the reports-findings exit-code ledger.

TEST RESULTS: passed — 1449 passed, 1 skipped (was 1443). check_all green with 1 soft
warning (the 4 accepted dead tutors). check_docs OK, check_commands OK.
Three mutants watched failing: a command stubbed to print nothing (caught by the output
contract), the positional zip restored (caught by BOTH tune-plan contract tests), and a
new unclassified subcommand (caught by the exhaustiveness test).

REGRESSION RISKS: None to production code — this change is tests plus documentation. Two
risks in the TESTS themselves, both handled:
- The suite now runs 33 extra subprocesses. Reused the existing module-scoped fixture and
  thread pool, so the whole file still completes in ~30s; total suite went 139s vs 138s.
- `_ARGS` hardcodes deck ids (43, 20/20a). If those decks are deleted the tests fail
  loudly rather than silently skipping, which is the intended direction — but it is a
  real coupling to roster data and is noted below.

INVARIANTS AT RISK: None. No production code path changed; the write-capable commands
(swap, apply-flex, sync, resolve --fix) are all dry-run until `--apply`, verified before
being invoked, and a before/after md5 confirmed `apply-flex` writes nothing.

NET SCORE: 0 production fixes − 0 new failure modes = 0
This is coverage for a gap that produced a real bug, not a bug fix. The honest score is
zero; its value is that the next B1-class defect fails a test instead of reaching a deck.

OPERATOR ACTIONS / DEPLOY:
- None.
Deploy: Data + tooling ship by commit/push. No dashboard-affecting change.

FOLLOW-ON ITEMS:
- tests/test_cli.py: `_ARGS` couples to specific roster deck ids (43, 20/20a). A fixture
  that picks the first deck with a variant would decouple it; deliberately not done here
  to keep the change to the scoped follow-on.
- The output contract asserts len > 20 chars. That catches a silent command but not a
  TRUNCATED one. A per-command expected-substring table would be stronger and is the
  natural next increment.
- Presentation remains the last unaudited subsystem, and still holds the biggest untested
  surface: app.py's Flask tests skip in this environment, build_dashboard.py (2,685
  lines) has no dedicated test file.

DOCUMENTATION UPDATES NEEDED:
- Done in this change: docs/cycle-config.md [C-07] and CLAUDE.md's Testing subsystem line.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
