---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: incremental `make refresh` — the rebuild re-priced all ~15.9k pool
cards against Scryfall's rate limit on every run, costing ~10 minutes for a four-card
ingest as much as for a full rebuild. It was the largest single cost in the repo.

Files modified: scripts/build_mana.py, Makefile, tests/test_build_mana.py (new),
CLAUDE.md, docs/gotchas.md, docs/systems-map.md, .claude/commands/ingest.md,
.cycle/STATE.md, .cycle/NEXT-SESSION.md

CHANGES:
incremental-refresh | scripts/build_mana.py | Added `load_existing()` and `--refetch`.
  The build now REUSES rows already resolved in the output file and fetches only names
  that are new or still unresolved; `--refetch` restores the full re-price. A row counts
  as resolved when its **Mana Value** is non-blank — the load-bearing predicate, because
  673 pool LANDS legitimately carry a blank Mana Cost with a real Mana Value of 0, so
  keying off the cost would re-fetch every land forever and let a genuinely unresolved
  row look settled. Reuse is keyed by the row's EXACT Card Name only, deliberately not
  also under the DFC front face the way `_store` indexes a fetched card: reuse must never
  answer for a name it was not written for. Nothing to fetch now means no Scryfall call at
  all, so a no-change refresh completes offline.
incremental-refresh | scripts/build_mana.py | Fixed a latent write bug the reuse path
  exposed: Mana Value arrives as a FLOAT from Scryfall's `cmc` but as a STRING from a
  reused row, and the existing `int(mv) if isinstance(mv, (int, float)) else ""` blanked
  anything non-numeric. Left alone it would have wiped the Mana Value of every reused row
  — the whole file on the first incremental run. `_mv_out()` renders both shapes and keeps
  a blank blank.
incremental-refresh | scripts/build_mana.py | An unchanged refresh is now a no-op instead
  of a rewrite. `atomic_write` takes a timestamped `.bak` every time, and now that a
  refresh is cheap enough to run often that would litter backups of a file that never
  changed.
incremental-refresh | Makefile | `make refresh REFETCH=1` forces the full re-price, as a
  FLAG on the one target rather than a second "quick refresh" recipe — the rebuild ORDER
  is the thing that must have a single definition, and a parallel recipe is exactly how it
  drifts (CLAUDE.md [G-13]). Updated the stale "SLOW … prices ~15.9k cards every run"
  comment and the `make help` line.
incremental-refresh | tests/test_build_mana.py | 16 tests over the paths a live run cannot
  reach: the resolved/unresolved predicate (land-with-blank-cost is resolved; all-blank is
  retried; exact-name keying only), incremental scoping (first run fetches all, second
  fetches nothing, only a NEW name is fetched, an unresolved row is retried, `--refetch`
  rebuilds everything), Mana Value rendering in both shapes, the no-op write, and that the
  shrink guard and the Scryfall-outage path still leave the file unchanged.
incremental-refresh | docs + skill | Corrected the now-false ~10-minute cost claims in
  docs/systems-map.md (§2 table, §2 reconciliation point, §8), the [G-18] rule in
  CLAUDE.md and its evidence in docs/gotchas.md, and `/ingest` Stage 3.

TEST RESULTS: passed. `python3 scripts/check_all.py` — all invariants hold.
`pytest` — 706 passed (was 690; +16). `check_docs` OK.
Regression Scenarios walked (Subsystem overlap: Ingest & Enrich, Presentation/Makefile):
  - Scenario 3 (Refresh derived data) — **PASS**. Ran the real `make refresh`:
    **3m40s against ~10 min**, all invariants hold. The mana step alone is **1.2s**. The
    run added 94 genuinely new pool cards and **modified 0 existing rows and lost 0 Mana
    Values** (15,876 → 15,970), which is the strongest available evidence that reuse is
    faithful.
  - Scenario 1 (Ingest a batch) — **PARTIAL**. The `make refresh` and `verify_ingest`
    halves were exercised; the `import_arena.py` half was NOT, because it needs a real
    Arena paste and would mutate the collection. No ingest code was touched.
  - Scenarios 2, 4–8 — NOT APPLICABLE. Deck-tooling and browser/editor surfaces; no
    modified file belongs to those subsystems.

REGRESSION RISKS:
  - **`build_mana.py` has no programmatic consumers** — verified by scanning `scripts/`
    and `tests/`; every other mention is prose. The only interface change is the CLI (one
    new opt-in flag) and the default behaviour.
  - **The default behaviour DID change**: a plain run no longer re-fetches. The case where
    the old behaviour was strictly better is a row that is present but WRONG — a Scryfall
    errata or an Alchemy rebalance changing a cost or keyword list. Incremental will never
    correct that on its own. Mitigated by `--refetch` / `REFETCH=1`, documented in the
    Makefile, [G-18] and the `--help` text. This is a real, accepted trade.
  - The shrink guard is untouched: `names` is still the full name set, so the >50%-shrink
    refusal computes exactly as before. Pinned by a test.
  - The no-op write means `card-mana.csv`'s mtime no longer changes on every refresh.
    `deck._file_memo` keys on `(mtime_ns, size)`, so a cache holding an unchanged file
    stays valid — which is correct, not stale.

INVARIANTS AT RISK: None.
  - INV-02 (every library card has a card-mana.csv row) — the writer still emits one row
    per collected name; only the SOURCE of a row's values changed. Held green through the
    live refresh.
  - INV-03 (card-mana.csv keeps its own columns) — the header is written unchanged.
  - INV-06 (tags are keyword-aware) — reuse preserves the Keywords column verbatim, so
    the pool-sized corpus `tag_synergies.is_noise_keyword` needs is intact.

NET SCORE: 2 production fixes (the ~10-minute rebuild cost; the float-vs-string Mana Value
blanking, which would have fired on the first incremental run) − 0 new failure modes
(the stale-row trade is a documented, flagged behaviour with an escape hatch, not an
undocumented failure) = **+2**

OPERATOR ACTIONS / DEPLOY:
- None. | BLOCKS DEPLOY: N
Deploy: N/A for this change — the only configured Deploy Command is the dashboard
(`.github/workflows/pages.yml` on push to `main`), and no Presentation data-pipeline file
was modified.

FOLLOW-ON ITEMS:
- **Derived-data drift is real and uncommitted.** The live `make refresh` produced
  `card-pool.csv` +389 lines and `card-mana.csv` +94 rows (94 new pool cards, 0 modified).
  I reverted both to keep this commit scoped to tooling. Someone should run `/refresh` and
  commit that deliberately — and it will need the deck 43 tier rationale re-grounded, which
  the refresh surfaced as a new soft warning (`card_advantage 11 vs live 12`,
  `avg_mv 2.91 vs live 3.0`).
- `make refresh` is 3m40s, not seconds, because `build_pool.py --all` (~90 paginated
  requests), `enrich.py` and `build_gallery.py` still run every time. `build_pool.py` is
  the remaining bulk and could take the same treatment (it rewrites the whole pool from a
  full search); not touched here, out of scope.
- `.claude/commands/refresh.md` documents the individual steps as the one deliberate
  exemption. It does not yet mention `--refetch`; worth a line next time that skill is
  edited.

DOCUMENTATION UPDATES NEEDED:
- None outstanding — the cost claims in CLAUDE.md [G-18], docs/gotchas.md,
  docs/systems-map.md and `/ingest` were corrected as part of this change, since leaving a
  "~10 min" claim would itself be a stale-doc defect.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
