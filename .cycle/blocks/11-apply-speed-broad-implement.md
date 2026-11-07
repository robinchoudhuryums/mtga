---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- S1 — check_all runs once per apply: `check_all.py --cached` replays the last GREEN run when nothing it reads has changed; `deck.py preflight` and `make postedit` use it; /apply-changes runs postedit before preflight.
- S2 — Dashboard rebuild: card pool read once (memoized), mana-cost parsing and filler castability cached, the per-deck git history fetched on a thread pool. Output byte-identical.
- S3 — `swap --package … --apply` applies the pairs in order through `_do_swap` in one process; single swaps also gain from S2's caches.
Files modified: scripts/check_all.py, scripts/deck.py, scripts/build_dashboard.py, scripts/check_colors.py, Makefile, .gitignore, .claude/commands/apply-changes.md, docs/verify-commit-tail.md, CLAUDE.md, tests/test_check_all.py, tests/test_deck.py

CHANGES:
S1 | scripts/check_all.py | `tree_signature()` = sha256 of HEAD's tree id + `git diff HEAD --binary` + untracked file list and content hashes + today's date + Python version (None without git → never trusted). `--cached` (`run_cached`): a hit replays the stored output; a miss runs the FULL gate in a child (`--summary-to` writes the quiet line), echoes it, and stores it only if exit 0 and the signature is unchanged after the run. One stored run answers both modes. Cache at `.cycle/.check-all-green.json` (gitignored — an untracked cache would change its own key). Cold 41 s, replay 0.15 s.
S1 | scripts/deck.py, Makefile | preflight's integrity subprocess passes `--cached`; postedit's gate is `check_all.py --cached` (postedit's ~2 min note → ~45 s).
S1 | .claude/commands/apply-changes.md, docs/verify-commit-tail.md | Stage 4: `make postedit` first, then preflight (a replay); the tail documents the cache and how to force a fresh run.
S2 | scripts/deck.py | `parse_pips` delegates to `_parse_pips_cached` (lru_cache, immutable result, insertion order kept) and returns fresh containers; `_filler_castable` delegates to `_filler_castable_cached` (frozen inputs); new `load_pool_rows()` (`_file_memo("POOL_CSV")`, `MappingProxyType` rows) replaces `suggest_scored`'s per-call pool read.
S2 | scripts/check_colors.py | `_INLINE_PARSE_ALLOW` names `_parse_pips_cached` (the parse moved there; `parse_pips` no longer parses).
S2 | scripts/build_dashboard.py | `_prefetch_git` runs `_git_info` (the same deck.py history helpers) for every roster deck on an 8-thread pool before the loop; the loop reads the results by path.
S3 | scripts/deck.py | `_package_apply`: the preview first (refuses before any write), then `_do_swap(d, cut, add, True)` per pair in order; stops at the first failure and names what landed. `cmd_swap` accepts `--apply` with `--package` (still refuses `--cut/--add/--undo/--section/--keep-section`); help text updated.
S3 | CLAUDE.md, .claude/commands/apply-changes.md | G-06 and Stage 2 describe the package apply.
Tests | tests/test_check_all.py, tests/test_deck.py | TestGreenRunCache (signature moves on tracked/untracked edits and content, no git → None, a failure is never stored, one green run replays both modes, an edit invalidates); TestSwapPackage: package apply equals the single-swap sequence (file + ledger), a bad pair stops before any write, `--cut` still refused (replaces the old refuses-apply test).

MEASURED (all on the live repo, 2026-11-07):
- Dashboard: 97.6 s → 45.5 s, built back to back; data island byte-identical apart from the `generated` stamp.
- Ledger rows (`recommendation_row`, 5 pairs on deck 97): 14.1 s → 5.5 s; JSON byte-identical old vs new code.
- `swap --apply`: 5 single CLI applies 23.1 s; one `--package --apply` 8.9 s; deck file and the 5 ledger rows byte-identical (repo restored from git afterwards).
- check_all: 41 s cold, 0.15 s replay; in /apply-changes the gate now runs once (postedit) instead of 2–3 times.

TEST RESULTS: Full suite PASSED (exit 0; 2405 tests); check_all OK (all invariants hold).
REGRESSION RISKS: (1) `--cached` trusts that the gate reads only repo files: an input outside the git working tree (a gitignored file, an environment change other than the Python version) would replay a stale green result. Nothing the gate reads is gitignored today (checked `git ls-files -o -i`); the date is in the key for the date-dependent sweeps. (2) `parse_pips` now returns new containers every call — callers that mutated the result were already safe, and the cached core is immutable. (3) `load_pool_rows` rows are read-only `MappingProxyType`; a future caller that writes to one raises rather than silently corrupting the shared table (intended, G-71). (4) The dashboard's git queries run concurrently; each is an independent read-only `git log/show`.
INVARIANTS AT RISK: None — no canonical CSV or deck file written by the new code paths beyond what `_do_swap` already wrote.
NET SCORE: 3 production fixes − 1 new failure mode = 2
(S1 YES: every apply paid 2–3 full gate runs. S2 YES: every postedit paid the rebuild. S3 YES: the 22-swap Route E apply took ~2.5 min in swaps alone. New failure mode: the cache's stale replay if an untracked-by-git input changes — documented.)

OPERATOR ACTIONS / DEPLOY:
- None. | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds the dashboard on the next merge to main (it runs build_dashboard.py, which now uses the thread pool).

FOLLOW-ON ITEMS:
- Pre-existing nondeterminism found while verifying S2: `deck_card_delta_since` passes a bare ISO date to `git log --before=`, which git reads as that date at the CURRENT time of day, so the dashboard's 7-day window base for a deck can change between two builds minutes apart (seen on deck index 130 across 00:05 vs 00:09).
- `builder.py apply` still runs one `deck.py swap` subprocess per pair (scripts/builder.py:1111); it could call `--package --apply` once.
- The SessionStart hook (`scripts/session_check.sh`) runs `check_all --quiet` uncached on every session start; `--cached` would make an unchanged resume ~40 s faster.
- The dashboard's remaining time is mostly `craft_rows` → `suggest_scored` per deck (~25 s) and `cmd_cuts` per deck; not touched.

DOCUMENTATION UPDATES NEEDED:
- None beyond what landed (G-06, apply-changes Stages 2/4, verify-commit-tail §1, Makefile help). docs/systems-map.md §tune+apply quotes per-command costs and may cite the old swap/postedit timings.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
