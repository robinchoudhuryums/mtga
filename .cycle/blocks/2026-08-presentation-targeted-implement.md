---TARGETED IMPLEMENTATION SUMMARY---
Scope: Presentation & Interface
Actions completed: C1, C2, C3, C4, C5
Actions not completed: All completed. (C6 — a broader build_dashboard.py test module —
stays deferred by the handoff; C5 covers the genuinely un-mirrored logic, which was the
JS.)
Files modified: .github/workflows/tests.yml, .github/workflows/pages.yml,
tests/conftest.py, tests/test_check_all.py, tests/test_dashboard_js.py (new),
scripts/check_all.py, CLAUDE.md

CHANGES:
C1 | tests.yml, tests/conftest.py | CI installs requirements-app.txt as well as -dev, so
  test_app_editor.py's SIX write-safety pins on app.py (1,035 lines that write
  card-library.csv and deck files) actually run — they had skipped on every push and PR
  since they were written, visible only as an unremarkable "1 skipped". Verified they
  PASS with Flask present before changing CI, so this could not turn the build red.
  Then the CLASS: PYTEST_NO_SKIPS=1, set by the workflow, makes any skip a FAILURE via a
  conftest report hook. Local runs are untouched — skipping without the editor's optional
  dependency is the same split `make app` draws. | F1
C2 | check_all.py | Added dashboard.html to INV-03's derived-file list. BS4-27 hardened
  the gallery leg against an exists-but-gutted build and wrote the fix generically
  (`endswith(".html")`), but the second generated page was never added — so a truncated,
  committed dashboard.html passed every gate. Its only other check asks whether the page
  is CURRENT, never whether it is INTACT. | F2
C3 | tests/test_check_all.py | Three mutation tests beside the existing gutted-gallery
  pair (empty file, missing data island, absent file), all watched failing with
  dashboard.html removed from the list again. | F2
C4 | pages.yml | The built page is inspected before upload: non-trivial size plus the
  `#data` island, the same two facts INV-03 checks on the committed copy. | F4
C5 | tests/test_dashboard_js.py (new) | Cross-language agreement: the JS matcher is
  extracted brace-balanced from build_dashboard.py's SHIPPED source and executed under
  Node against the same fixtures `deck.match_paste` gets. "Mirrors deck.match_paste
  exactly; change both or neither" was a comment, and it had already broken once (F-08:
  strict `<` on drift vs Python's more-shared-then-lower-id, so browser and CLI named
  different decks for one paste). Skips without Node, which C1's guard converts to a CI
  failure — the same mechanism, not a second blind spot. | F3

TEST RESULTS: passed — 1462 passed, ZERO skipped under CI conditions (PYTEST_NO_SKIPS=1);
was 1449 passed / 1 skipped. check_all green with 1 soft warning (the 4 accepted dead
tutors). check_docs, check_commands, check_patterns all OK.
Mutants watched failing: a simulated optional-dependency skip (C1's guard), dashboard.html
removed from INV-03 (all three C3 tests), the F-08 localeCompare divergence (three C5
tests), and a renamed JS function (C5's extraction guard).

REGRESSION RISKS:
- A REAL BUG WAS CAUGHT BY TESTING THE DEPLOY STEP, not by review: C4's first version put
  a backslash inside an f-string EXPRESSION, a SyntaxError before Python 3.12. It would
  have failed EVERY deploy. Fail-closed, so nothing bad would have shipped — but nothing
  at all would have. Found by extracting the step's `run:` from the YAML and executing it
  against a real page, a gutted page and an island-less page.
- C1 changes what CI installs. Flask is pure-Python with no compiled extensions; the core
  tooling's zero-dependency guarantee is unaffected and check_all.py was re-verified
  running standalone.
- C1's no-skips rule will fail on ANY future permanently-skipped test. That is the intent;
  the full suite was run under PYTEST_NO_SKIPS=1 and reports zero skips today.
- C2 makes check_all HARD-fail on a gutted dashboard.html. Verified green against the real
  committed page before landing.
- C5 introduces the repo's first JS execution, in the pytest layer ONLY. check_all.py
  stays pure-stdlib and offline, as its contract requires.

INVARIANTS AT RISK: None. INV-03 is strengthened (a second generated artifact now checked
for content, not just existence). No production code path changed — the only scripts/ edit
is check_all.py's own list.

NET SCORE: 3 production fixes (F1 was live and skipping on every CI run; F2 and F4 were
latent gates that could not fire) + 1 bug caught in my own new code − 0 new failure
modes = 4

INVARIANT CANDIDATES:
- "CI must not silently skip a test." Implemented as a mechanism (PYTEST_NO_SKIPS) rather
  than added to the invariant library: it is a property of the test RUN, not of the repo's
  data, and check_all.py — where the invariant library lives — never runs pytest.

OPERATOR ACTIONS / DEPLOY:
- None. Both changes are workflow files; no runner, secret or environment change.
Deploy: the dashboard redeploys via pages.yml on push to main, now with the pre-publish
verification in front of it.

FOLLOW-ON ITEMS:
- check_docs.py `_live_figures` covers 5 claims and does NOT cover the test-file count,
  which this change moved 30 -> 31 and I updated by hand. Adding it is a natural entry.
- tests/test_dashboard_js.py extracts 7 JS functions by name; the panel's rendering half
  (stalecardEl and the click handler) is still unpinned. The MATCHING logic is what could
  silently disagree with Python, so it was taken first.
- C6 remains open: build_dashboard.py is 2,685 lines with no dedicated test module. Its
  data pipeline routes through shared primitives covered elsewhere, so the marginal value
  is lower than it looks — scope it against what C5 leaves uncovered.

DOCUMENTATION UPDATES NEEDED:
- Done in this change: CLAUDE.md's Testing subsystem line (31 files, the new
  cross-language layer, and the CI install/no-skips rule).
---END TARGETED IMPLEMENTATION SUMMARY---
