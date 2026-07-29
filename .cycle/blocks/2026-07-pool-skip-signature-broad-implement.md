---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- **build_pool freshness skip + `--refetch`** — `build_pool.py --all` was the remaining
  bulk of `make refresh`, and the last piece of the incremental-rebuild work.
- **`_signature_themes` saturation in `cuts`** — the `#: protect:` keep-boost fired on
  87% of nonland cards, so a term meant to protect a deck's spine was a near-constant.

Files modified: scripts/build_pool.py, scripts/deck.py, Makefile,
tests/test_build_pool.py (new), CLAUDE.md, docs/gotchas.md, docs/systems-map.md,
.cycle/NEXT-SESSION.md, .cycle/STATE.md

CHANGES:
pool-skip | scripts/build_pool.py | Added `read_stamp()`, `stamp_age_days()`, `--refetch`
  and `--max-age DAYS` (default 7). A pool built within the window FOR THE SAME QUERY is
  reused and the fetch is skipped entirely. **Measured first, not assumed:** `fetch_all` is
  222.5s of a 224.3s run (**99%**), 91 paginated pages at ~2.4s each, against 1.8s to derive
  every row — so the only lever is not fetching. Skipping is CORRECT, not merely fast:
  card-pool.csv is the whole Arena pool and is INDEPENDENT of what you own, so the
  motivating case (`make refresh` after an ingest, which changes the LIBRARY) cannot change
  it. What genuinely goes stale is `Legalities` (rotation, bans, rebalances) and a new set's
  arrival — hence a time WINDOW rather than blanket reuse.
pool-skip | scripts/build_pool.py | The sidecar now records the QUERY on a second line.
  `--all` and the Standard-only default produce different files, and reusing a
  Standard-scoped pool for an `--all` request would freeze the wrong scope — the shrink
  guard catches a shrink but cannot see that the file answers a different question. The
  DATE stays on line 1 because `deck.pool_staleness_days` reads `stamp[:10]`; that is a
  cross-module contract and it is now pinned by a test that consumes the real producer's
  output.
pool-skip | Makefile | `REFETCH=1` now propagates to `build_pool.py` as well as
  `build_mana.py`. Still a FLAG on the one target, not a second recipe.
signature-saturation | scripts/deck.py | `cut_scoring_context` reads
  `_strong_signature_themes` (a theme carried by ≥2 `#: protect:` cards) instead of the
  loose union of every protected card's tags. This is `check_suggest` anchor 11b's fix one
  caller over — that anchor already forces the strict set on `cmd_suggest_homes` for the
  same reason.
signature-saturation | tests + docs | Measurement and roster diff recorded in [G-09]'s
  rule and evidence, docs/systems-map.md §7, and the handoff.

TEST RESULTS: passed. `python3 scripts/check_all.py` — all invariants hold.
`pytest` — **721 passed** (was 706; +15). `check_docs` and `check_agreement` OK.
Regression Scenarios walked (Subsystem overlap: Ingest & Enrich, Deck Tooling Correctness):
  - Scenario 3 (Refresh derived data) — **PASS**, run twice. A legacy date-only stamp
    correctly forced a full rebuild (**5m3s**); the next consecutive run skipped both
    fetches at **12.7s**, of which ~11s is the final `check_all`. Invariants held both times.
  - Scenario 2 (Analyze a deck) — **PASS**. `cuts` exercised on all 64 decks for the
    before/after diff; no traceback.
  - Scenario 1 (Ingest a batch) — **PARTIAL**: the `make refresh` half was exercised; the
    `import_arena.py` half was not (needs a real paste and would mutate the collection). No
    ingest code touched.
  - Scenarios 4–8 — NOT APPLICABLE (browser/editor surfaces; no modified file belongs to
    those subsystems).

**The `_signature_themes` roster diff** (the standing rule for any scoring change):
  - boost fires on **87% → 66%** of nonland cards across the 22 `#: protect:` decks.
  - **14 of 64** decks re-scored; only the 22 protect-declaring decks can change.
  - **4 of 64** top-cut candidates moved (a 5th diff was whitespace only). Deck 36a's moved
    OFF **Vizier of the Menagerie** — one of the two fixers CLAUDE.md says the tooling is
    meant to protect — though only by one rank (8 → 9), so this de-saturates rather than
    fixing the fixer problem.
  - The motivating case survives: deck 30 protects counter-doublers and its strict
    signature is exactly `{counters}`.

REGRESSION RISKS:
  - **`build_pool.py` has no programmatic consumers** (verified by scanning `scripts/` and
    `tests/`); the interface change is two new opt-in flags plus the default.
  - **The default behaviour changed**: a pool younger than 7 days for the same query is not
    rebuilt. The case where the old behaviour was strictly better is a new SET released
    within the window, or a legality change (ban/rebalance) inside it. Mitigated by
    `--refetch` / `REFETCH=1` / `--max-age`, and `suggest` already warns on a stale pool
    stamp. Accepted, documented in [G-18] and the Makefile.
  - **The sidecar format changed** (one line → two). `deck.pool_staleness_days` reads
    `stamp[:10]`, so a two-line stamp still parses, and a legacy one-line stamp still works
    — it simply never satisfies the skip, which is the safe direction. Both pinned.
  - `cuts` re-scores 14 decks. That is the intended effect of the finding, and it only ever
    REMOVES a boost, so no card became less cuttable by gaining an unearned bonus.
  - The two remaining loose `_signature_themes` callers (`cmd_stats`, `cmd_engines`) feed
    `engine_balance`, a different question, and were deliberately left alone.

INVARIANTS AT RISK: None.
  - INV-03 (derived files keep their own schema) — POOL_HEADER is unchanged; the skip path
    writes nothing at all.
  - INV-02/INV-06 — untouched; card-mana.csv and the tag pipeline are unaffected by the
    pool skip beyond seeing the same pool.

NET SCORE: 2 production fixes (a ~5-minute rebuild on every refresh; a keep-boost that had
degenerated into a constant) − 0 new failure modes (both behaviour changes are documented,
flagged and have an escape hatch) = **+2**

OPERATOR ACTIONS / DEPLOY:
- None. | BLOCKS DEPLOY: N
Deploy: N/A for this change — the only configured Deploy Command is the dashboard
(`.github/workflows/pages.yml` on push to `main`), and no Presentation data-pipeline file
was modified.

FOLLOW-ON ITEMS:
- **Derived-data drift is now deferred for the SECOND session running, and that is worth
  escalating.** The live refreshes produced real upstream changes (`card-pool.csv` ~±190
  lines, +95 new cards; `card-mana.csv` +94 rows). I reverted them again to keep the commit
  scoped to tooling. It needs a deliberate `/refresh` commit, and it will need deck 43's
  tier rationale re-grounded (`card_advantage 11 vs live 12`, and an `avg_mv` claim moved
  too). Each deferral makes the eventual diff larger.
- A **stale `__pycache__` silently defeated a mutation test.** Restoring a file whose edit
  was a pure two-line swap left the byte SIZE identical and the mtime within the same
  second, so CPython's mtime+size `.pyc` validity check passed and kept executing the
  MUTATED bytecode — I nearly concluded a correct new test was broken. Worth knowing that
  `deck._file_memo` is immune because it keys on `mtime_ns`, while CPython uses whole
  seconds. Not fixed here (it is a workflow hazard, not a repo defect); the mitigation is
  `rm -rf scripts/__pycache__` between mutation runs.
- `build_pool.py`'s 7-day window is a guess, not a measurement. A set releases roughly
  quarterly, so it is comfortably safe for new sets, but no data informs the exact number.
- `.claude/commands/refresh.md` documents the individual steps as the one deliberate
  exemption and still does not mention `--refetch` / `--max-age`.

DOCUMENTATION UPDATES NEEDED:
- None outstanding. [G-18] and [G-09] (rule + evidence), docs/systems-map.md §2/§7/§8, the
  Makefile comments and the handoff were all updated in this change, including correcting
  a "~1s no-change refresh" claim I had written before measuring it (the real figure is
  12.7s, nearly all of it `check_all`).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
