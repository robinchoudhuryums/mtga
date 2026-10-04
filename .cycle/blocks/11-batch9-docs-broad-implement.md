---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS11-55 — the SessionStart hook's `check_all --quiet 2>/dev/null` hid a check_all crash completely (no integrity line at all)
- BS11-56 — `validate.py --help` read "--help" as a file path; the eleven argument-less check_*.py gates ignored `--help` and ran in full (so CI's smoke step ran every gate)
- BS11-57 — `/refresh` said "drop `--all` for a smaller pool" (now refused by the shrink guard) and "skip step 2 unless card-library changed" (the opposite of G-18)
- BS11-58 — ROADMAP.md (2026-08-19) pointed at the deleted prune analysis, listed done items as open, and carried figures from 34/113/58 days
- BS11-59 — `figure_drift` hard-coded "of 112 decks" in G-86's and G-35's patterns while the roster is 114
- BS11-60 — regression scenario 11 said the hand columns are empty in "all 66 rows" (213 live)
- BS11-62 — CLAUDE.md said systems-map has four sections (five, with §5b Log matches); the map's header figures were stale
- BS11-63 — `query.py --color`/`--type` help said "substring"; query/pool module docstrings said every filter is a substring match; `build_pool.tagger_fingerprint` described the retired card-mana noise-floor dependency
- BS11-64 — INV-06's recipe (build_mana then tag_synergies) omitted build_pool and contradicted G-13; the no-prose-recipe test could not see a PARTIAL chain
- BS11-65 — NEXT-SESSION §0 was headed "2026-08-24" while holding stamps to 10-01, said "Step 0 still waiting", and called three deleted working docs live
- BS11-66 — count drift: G-55 "16 model functions" (18), C-07 "all fourteen" (thirteen), G-33 "all four" axes (five), integrity.yml "calls cmd_* directly" (none)
Files modified: scripts/session_check.sh, scripts/validate.py, scripts/check_{agreement,colors,commands,dfc,docs,engines,patterns,rankings,suggest,themes,tier}.py, scripts/query.py, scripts/pool.py, scripts/build_pool.py, scripts/verify_ingest.py, .claude/commands/refresh.md, ROADMAP.md, CLAUDE.md, docs/systems-map.md, .cycle/NEXT-SESSION.md, .github/workflows/integrity.yml, tests/test_cli.py, tests/test_check_docs.py, tests/test_verify_ingest.py

CHANGES:
BS11-55 | scripts/session_check.sh | check_all's stdout is captured with its exit code and stderr goes to a temp file; when it exits non-zero WITHOUT printing its `[card-library]` line, the hook prints "check_all CRASHED (exit N)" plus the traceback's last 3 lines. A normal run's banner is unchanged. Verified against a fake crashing and a fake clean check_all.
BS11-56 | scripts/validate.py, scripts/check_*.py (11) | `-h`/`--help` prints the module docstring and exits 0 before any work. Test: every non-argparse gate and validate.py answers help (rc 0, no "file not found", no FAIL verdict).
BS11-57 | .claude/commands/refresh.md | step 2 says keep `--all` (the shrink guard refuses a Standard-only pool over the full one), that the build reuses a fresh pool, and `--refetch`; the notes say the pool does not depend on ownership (G-18), what DOES stale it, and to check the pool count on a release day (G-79).
BS11-58 | ROADMAP.md | a dated CURRENCY PASS, not a full regeneration: live state figures (2,832 printings, 16,047 pool, 116 files / 114 roster, 35 subcommands, 13 gates, 213 matches, claimed spread A 44 / B 64 / C 2 / ungraded 4 with 53 provisional, rotation 390/1,290/2,369), a status paragraph, and in-place DONE / CLOSED marks on the launchd archive, freshness signal, systems-map and prune items; the deleted-file reference now says deleted. Ordering and reasoning unchanged — a full `/roadmap` run is still the way to re-prioritise.
BS11-59 | scripts/check_docs.py, CLAUDE.md, tests/test_check_docs.py | the two numerator patterns take a wildcard denominator and the denominators are registered as their own figures ("G-86/G-35 roster walked", from the same roster walk). The gate then reported 112 vs 114 on both; CLAUDE.md now reads 72 of 114 / 77 of 114 and figure_drift is empty.
BS11-60 | CLAUDE.md | scenario 11 no longer hard-codes a row count (points at C-02's live figure).
BS11-62 | CLAUDE.md, docs/systems-map.md | "five task sections … *Log matches* (§5b)" in both CLAUDE.md mentions; the map's header re-taken 2026-10-03 (116 files, 2,832 printings, 16,047 pool, 35 subcommands, 213 matches), with the §6 agreement rates explicitly dated 2026-09-03.
BS11-63 | scripts/query.py, scripts/pool.py, scripts/build_pool.py | query/pool docstrings name the non-substring filters (whole-word `--type`, set-semantics `--color`/`--within`, `--regex`); query's `--type`/`--color` help corrected; `tagger_fingerprint` says card-mana.csv is no longer a dependency (G-18, 2026-09-09).
BS11-64 | CLAUDE.md, tests/test_verify_ingest.py, scripts/verify_ingest.py | INV-06 points at `make refresh` and restates no chain. `_restates_chain` now flags any line joining two rebuild steps as a sequence (`->`, `→`, `then`) — the old line test needed BOTH build_mana and build_pool, so a partial chain was invisible. Its first run found a LIVE instance: verify_ingest.py printed "(or at minimum build_mana.py --pool, then tag_synergies.py --merge)"; it now says `make refresh` only.
BS11-65 | .cycle/NEXT-SESSION.md | §0 retitled "STATE STAMPS, 2026-08-24 → 2026-10-03" with an explainer; a new 2026-10-03 stamp (scan #11 fully implemented, what stays the owner's, the new browser scenarios, the one live pile doc); the "Step 0 still waiting" line marked superseded; the three deleted working docs marked deleted.
BS11-66 | CLAUDE.md, .github/workflows/integrity.yml | 18 model functions (re-counted), "all thirteen model-sanity gates", "all five" axes, and the integrity.yml comment says check_all calls no cmd_*.

TEST RESULTS: passed — full suite green; `check_all --quiet` integrity OK, 4 soft (unchanged); `figure_drift` empty after the CLAUDE.md denominators were corrected. New tests: gates/validate answer `--help` (test_cli), no hard-coded roster size in the G-86/G-35 numerator patterns and both denominators registered (test_check_docs); the widened `_restates_chain` is exercised by the existing three scans (scripts / CLAUDE.md / skills), which it now passes after the verify_ingest fix.
REGRESSION RISKS: (1) A gate invoked as `check_x.py --help` no longer runs — any script that relied on `--help` being ignored would now skip the gate (none found; check_all calls `check()` in-process). (2) The widened recipe detector flags ANY line joining two rebuild steps with "then"/an arrow; a future legitimate sentence of that shape (e.g. explaining G-13's order) must live in docs/gotchas.md, which the scan deliberately skips. (3) The hook now spawns `mktemp`; on a system without it the fallback path is /tmp/check_all.$$.err.
INVARIANTS AT RISK: None — no data file, deck or derived artifact changed.
NET SCORE: 1 − 0 = 1  (production this month: BS11-59 — CLAUDE.md shipped two evidence figures over a stale 112-deck roster that the drift gate could not see. The rest are doc/help drift that misinformed nobody on record this month: no check_all crash at session start, no one followed refresh.md's wrong advice, the partial recipe printed only when a mana row is missing.)

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: N/A — no Presentation file changed (the Pages workflow is untouched; integrity.yml changed a comment only).

FOLLOW-ON ITEMS:
- ROADMAP.md is current but not RE-PRIORITISED — run `/roadmap` for a full regeneration when the next cycle starts.
- docs/systems-map.md §6's agreement rates are dated 2026-09-03; re-measuring them is its own task.
- G-55's "18 model functions" is a literal count again; registering it in `figure_drift` (a grep of `deckmod.<fn>(` in check_all.py) would stop the next drift.

DOCUMENTATION UPDATES NEEDED:
- None beyond what this batch made — it is the docs batch. (README does not describe the hook's banner or the gates' `--help`.)
---END BROAD SCAN IMPLEMENTATION SUMMARY---
