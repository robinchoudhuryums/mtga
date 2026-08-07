---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (Batch A — verdict-surface joins & determinism):
- BS2-20 | `engines` output order was nondeterministic (set iteration; G-54 violation, reproduced across runs)
- BS2-21 | `swap`/`apply-flex` CUT side was exact-name: front-name cuts refused, the protect ⚠ bypassed for the other spelling, flex auto-retire missed cross-spelled lines
- BS2-19 | `owned_role_fillers`/`craft_role_fillers` offered a deck its own maindecked DFC (25 rows roster-wide at full limit; reaches `tier --to` and `redundancy`)
- BS2-22 | `preflight` + `deck_quality_vector` compared ownership per LINE — a card split across two printing lines could read buildable while `check` said short
- BS2-35 | `pool.py --role recursion` returned a silent 0 (case-sensitive fallback, unknown roles never rejected) on the survey /draft-deck builds from
- BS2-36 | `query.py --min-owned` read one printing instead of the fungible sum; `--count` counted rows, not cards

Files modified: scripts/deck.py, scripts/pool.py, scripts/query.py,
tests/test_deck.py, tests/test_deck_models.py, tests/test_query_pool.py

CHANGES:
BS2-20 | deck.py | engine_balance gains a `weights` kwarg and sorts central engines by (-theme weight, name) — the centrality order its docstring already promised, now a TOTAL order; both callers (cmd_engines, cmd_stats) pass theme_w. Verified: five consecutive `engines 46` runs produce identical output (was 2 orderings in 5).
BS2-21 | deck.py, tests/test_deck.py | `_cards_after_swap` and `_swap_edit_lines` match the CUT on `_ms_key` (the add side already did, BS-05); `_do_swap`'s protect guard compares `_ms_key`s; the flex auto-retire block keys add/cut/maindeck on `_ms_key`. Verified live: `swap 51 --cut "Mirror Room"` now previews AND fires the protect ⚠ (both halves in one dry run). 4 tests.
BS2-19 | deck.py, tests/test_deck_models.py | both fillers build `in_deck` from `_ms_key` and probe with `_ms_key(nl)`, so a DFC keyed under either spelling is suppressed. Roster-wide verification: 0 self-offers remaining (owned and craft, full limit). 2 tests in the synthetic world (Pool Door // Pool Attic).
BS2-22 | deck.py, tests/test_deck_models.py | both sites aggregate need per NAME before comparing against owned (cmd_check's rule); missing/short now count cards, not lines. 2 tests (3+2 lines vs 4 owned flips buildable to False).
BS2-35 | pool.py, tests/test_query_pool.py | --role names resolve case-insensitively against deck.ROLE_ORDER + the aliases in main(), and an unresolvable name is a hard ERROR listing every valid role and alias — a zero now always means "no cards". Verified: `--role recursion` 0 → 1,459; `--role bogusrole` errors with the list.
BS2-36 | query.py, tests/test_query_pool.py | --min-owned filters on a per-name summed totals index built once in main() (Rugged Highlands 1+2 now passes --min-owned 3); --count prints distinct card names (2081, matching the usage line's "distinct cards you own"), not rows (2085). Test doubles updated to the new arg shape + a summed-printings pin.

TEST RESULTS: 992 passed (983 + 9 new), 0 failed. check_all: "All invariants hold. ✓", zero soft warnings. Scenario 2 walked on the modified surfaces: `engines` (determinism), `swap` dry-run (front-name cut + protect ⚠), `preflight 63` (READY, "fully owned"), `quality 52`, `pool.py --role` (all three shapes), `query.py --min-owned/--count` — PASS. Other scenarios NOT APPLICABLE (no ingest/presentation files touched).

REGRESSION RISKS:
- engine_balance's new kwarg is optional; check_engines fixtures pass lists without weights and get stable alphabetical order (their assertions key by theme, not position).
- A swap cut naming EITHER face now matches — if someone deliberately kept two same-front spellings as separate lines (never true in this repo; _multiset forbids the reading), the first line wins.
- pool.py --role now REJECTS unknown names (exit 2) where it silently returned 0 — scripted callers relying on the silent-zero behavior (none exist in-repo) would see the error.
- query.py --count semantic change: distinct cards, not rows — matches the documented usage; anyone wanting the row count loses it (README documents the card reading).
- args._owned_totals/_roles are internal Namespace fields built in main(); direct matches() callers must supply them (both test files updated; no other callers exist).

INVARIANTS AT RISK: None. No writer paths changed except swap's line editing, which is exercised by its INV-04 re-check tests; check_all green.

NET SCORE: 6 − 0 = +6
(BS2-20 fired on every engines run under hash randomization; BS2-35/36 on routine survey commands; BS2-21 on any DFC swap; BS2-19 reached tier --to/redundancy output; BS2-22 latent-but-adjacent. No new failure modes; the two behavior changes are documented semantics corrections.)

OPERATOR ACTIONS / DEPLOY:
None
Deploy: commit/push is the deploy (Data + local tooling); no dashboard-affecting changes (engines order feeds captured CLI text — pages.yml rebuilds on merge regardless).

FOLLOW-ON ITEMS:
- BS2-07's full sweep (rank_cut_candidates/_castability/_weakest_cut header joins vs the G-68 gate's `_ms_key`) — Batch A fixed only the swap-side protect guard; the header-consumer normalization is the remaining latent half.
- Batches B–H from the session's priority report, unchanged.

DOCUMENTATION UPDATES NEEDED:
- README query.py section: `--count` now counts distinct cards (one line).
- G-63 long form: BS2-19/21 close two more members — worth a line in the next /sync-docs pass, not urgent.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
