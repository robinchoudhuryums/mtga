---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: recommendation feedback loop — `swap --apply` already knows when a proposed swap was accepted, but nothing recorded it, so every ranking model in the repo was graded on argument and anchor tests rather than against a decision anyone actually made.
Files modified: scripts/deck.py, tests/test_recommendations.py (new), .claude/commands/apply-changes.md, CLAUDE.md, README.md

CHANGES:
recommendation-feedback | scripts/deck.py | New ledger: `RECS_CSV` (`recommendations.csv`), `recommendation_row()` (scores an accepted swap against `rank_cut_candidates` and `suggest_scored` at the pre-swap state), `load_recommendations()` / `append_recommendation()` (own DictWriter on own fieldnames via `lib.atomic_write`, never `lib.write_rows`), `_rec_percentile()`, `recommendation_summary()`, `cmd_feedback()` + the `feedback` subparser and dispatch entry. `_do_swap` computes the row before the edit and appends it only after the edit lands, both guarded so telemetry can never fail a swap.
recommendation-feedback | .claude/commands/apply-changes.md | Stage 2 step 3 documents the ledger row and points at `deck.py feedback` (also satisfies the `check_commands.py` coverage gate, which hard-failed on the new subcommand until a skill drove it).
recommendation-feedback | tests/test_recommendations.py | 33 tests: percentile math, disagreements-worst-first, unrankable rows excluded from n rather than counted as agreement, CSV roundtrip incl. comma-bearing card names, call-time path resolution, real-deck wiring, per-model failure isolation, report output, and a structural assertion that no scoring function reads the ledger.
recommendation-feedback | CLAUDE.md, README.md | Documented the design and — more importantly — how to read it: why the report leads with disagreements, why an agreement rate is contaminated by the shortlist's own influence, why "add not surfaced" is expected, and that it is report-only by design.

TEST RESULTS: passed — `check_all.py` "All invariants hold. ✓"; pytest 545 passed (was 512, +33). Regression Scenario 2 walked in full (15 deck.py subcommands + `tier --audit-rationale` + all four needs recommenders): no traceback, all exit 0. Scenario 1/3 (ingest, refresh) NOT APPLICABLE — no ingest or derived-data code touched. Scenario 4 (app editing) NOT APPLICABLE — app.py untouched. Scenarios 5–8 NOT APPLICABLE — perceptual/browser checks over dashboard/templates, none of which changed. Additionally verified end-to-end on a real deck: applied a live swap, confirmed the ledger row and the `feedback` report, then reverted the deck file and removed the ledger.

REGRESSION RISKS:
- `_do_swap` now costs ~1.1s more per `--apply` (a `rank_cut_candidates` pass plus a full `suggest_scored` pool scan). Loaders are memoized so a multi-swap `/apply-changes` run pays the pool read once, but a bulk apply is measurably slower. Dry runs are unaffected — verified they write nothing.
- `recommendation_row` catches bare `Exception` around each model call. That is deliberate (a swap must not fail because telemetry did) but it will also swallow a genuine bug in either ranking model at this call site. Mitigated by the column going blank rather than the row being fabricated, and by both failure paths being tested; the models remain covered by their own gates elsewhere.
- `apply-flex` shares `_do_swap`, so it records too (source `flex`). Intended, and tested.
- No interface changed: `_do_swap`'s signature, `rank_cut_candidates`' return shape and `suggest_scored`'s dict are all read-only here.

INVARIANTS AT RISK: None. `recommendations.csv` is a new standalone file with its own header, written through `lib.atomic_write` with its own `csv.DictWriter` — deliberately NOT through `lib.write_rows`, which emits the canonical 8 LIBRARY columns (audit F-02). It is not a derived reference file, so INV-03 does not cover it, and like `matches.csv` its absence is healthy rather than a violation. INV-04 is untouched: the ledger write happens after `_safe_write_lines`' parse-and-copy-count re-check, and no deck-file line handling changed.

NET SCORE: 1 production fix − 0 new failure modes = 1
  a) Would this have fired in production this month? YES — swaps are applied routinely via `/apply-changes`, and every one of them was discarding the only ground truth this toolkit can observe.
  b) New failure mode introduced? NO — the two candidates (a slower `--apply`, a broad `except`) are bounded, tested and documented; neither can corrupt a deck file or block a swap.

OPERATOR ACTIONS / DEPLOY:
- None.
Deploy: N/A for this change — the only Deploy Command in CLAUDE.md is the GitHub Pages dashboard rebuild, which fires automatically on push to `main` and is unaffected (no `build_dashboard.py` / template change).

FOLLOW-ON ITEMS:
- The ledger records ACCEPTED swaps only. The complementary signal — a card `cuts` keeps ranking weakest that survives round after round ("the model proposes this and you keep declining") — needs no new capture, only a report over deck history, but is out of scope here.
- `templates/collection.html`'s six `.pip` filter divs still lack `role`/`tabindex` (I-01 class, deferred; S ≈ 30 min).
- A dashboard panel over `recommendations.csv` would surface disagreements without a CLI run; not built, and worth waiting for real rows first.

DOCUMENTATION UPDATES NEEDED:
- Done in this session: CLAUDE.md (Common Gotchas entry, Data + Outcomes subsystems, Testing layer, Regression Scenario 2) and README.md (command list + a `feedback` prose section).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
