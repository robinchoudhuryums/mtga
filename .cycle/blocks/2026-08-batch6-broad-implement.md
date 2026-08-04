---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (Batch 6 — the coverage batch, closing the scan backlog):
- BS-20 — behavioral tests for six of the seven uncovered scripts: reconcile_crafts and sheets_sync (canonical-file writers) first, then validate, query, pool, scryfall, enrich. The seventh, pool.py, is covered in the shared query/pool file.
- F20/BS-17 — the wishlist outage→re-enrich→re-seed path tested end to end (the enrich seam faked, which is why nobody had tested it), including the hand-grade-survives control.
- Power range flag — a finite out-of-range Power (>10 or <0) now flags `bad_power` and scores 0.0 instead of pinning the craft ranking.

Files modified: scripts/wishlist.py, tests/test_reconcile_crafts.py (new), tests/test_sheets_sync.py (new), tests/test_validate.py (new), tests/test_query_pool.py (new), tests/test_scryfall.py (new), tests/test_enrich.py (new), tests/test_wishlist.py

CHANGES:
BS-20 | tests/test_reconcile_crafts.py | 8 tests on a tmp four-CSV world with repointed module paths: dry-run writes nothing, --apply lands library row + BLANK mana row (INV-02) + wishlist removal + .bak files, existing counts bump on max (a lower line can't drop a count), a front-name DFC paste with an unheld printing resolves via the aliased pool index (the BS-16 pin), unparseable/pool-absent lines report loudly.
BS-20 | tests/test_sheets_sync.py | 7 tests with a fake worksheet: header-only sheet refused (THE BS-03 case — passes validate() with zero rows), >50% shrink refused, --allow-shrink escape hatch, dry-run default writes nothing, wrong header refused, invalid rows leave the CSV untouched (write-to-temp→validate→promote), and a full-size --apply overwrites + backs up + repairs INV-02 (the F-05 pin).
BS-20 | tests/test_validate.py | 9 tests pinning INV-01's letter: dup printings, negative/non-numeric quantities, header mismatch, missing file; plus a CHARACTERIZATION test that a header-only zero-row library PASSES by design — with the comment naming the shrink guards that exist because of it, so a future change to either side updates both together.
BS-20 | tests/test_query_pool.py | 9 tests: the BS-10 color-set pins on both CLIs' matches() (Colorless excluded from --color R, gold matches either color, colorless needle exact), AND-ed filters, min-owned, rarity/legalities cells, and --role classifying through the batch-5 lazy deck proxy.
BS-20 | tests/test_scryfall.py | 7 tests with scripted urlopen + stubbed sleep: 404→NotFound immediately (a miss is not an outage), 400 NOT retried (the batch-5 pin — one call, "client error" in the message), 429 honors retry, 5xx retries then ScryfallUnavailable, timeout is transient (G-14's founding incident), recovery after a blip.
BS-20 | tests/test_enrich.py | 6 tests: the F-02 schema guard refuses a derived file before any traffic, blanks fill from the resolver, the F-11 vanilla rule (enriched blank-text rows are never requeued — resolver not even called), hand-curated Synergies survive, ScryfallUnavailable aborts cleanly with the file untouched, dry-run writes nothing.
F20/BS-17 | tests/test_wishlist.py | TestOutageReseed: outage add seeds 2.0 from blank data; the re-add backfills fields AND recomputes the seed upward; a hand grade (Power Source=hand) survives re-enrich untouched (G-17).
range flag | scripts/wishlist.py, tests/test_wishlist.py | `_rank_scores` treats a finite Power outside 0–10 like the NaN/non-numeric cases (flag + 0.0); the ⚠ report says "NON-NUMERIC or OUT-OF-RANGE". TestPowerRangeFlag pins 78→flagged, 0 and 10→in range.

TEST RESULTS: passed — 922/922 (872 prior + 50 new across 6 new files + 2 new test_wishlist classes); check_all all invariants hold (same 2 pre-existing soft warnings).

REGRESSION RISKS:
- The range flag changed LIVE ranking output: 15 wishlist cells carry 0–100-style grades ('84','78','74','66','60','52'…) and were silently DRIVING the top of `--rank`/`--budget` (Pensive Professor sat at #1 with combined 42.3 on a 0–10 scale; now #106 at pow 0.0! with the ⚠ naming all 15). The flag is the fix for the ranking; the cells themselves are hand-grade data (G-17) and are NOT auto-rewritten — see operator actions.
- New tests monkeypatch module path constants; they never touch the repo's real CSVs (verified: dry-run/untouched assertions read the tmp copies).

INVARIANTS AT RISK: None — the only script change is the wishlist range flag (read path); INV-01…06 verified via check_all.

NET SCORE: 1 − 0 = +1 (the range flag fired THIS month: the wildcard-spend ranking was being led by mis-scaled cells on every `--rank`/`--budget` run; the 50 tests are recurrence-prevention for the map where this scan found its bugs — three of the seven uncovered scripts carried BS-10, a fourth carried BS-16).

OPERATOR ACTIONS / DEPLOY:
- Re-grade the 15 out-of-range wishlist Power cells to the 0–10 scale (they look like 0–100-style grades: Ojer Axonil '84', Pensive Professor '78', Riverchurn Monument '74', Eddymurk Crab '66', Transit Mage '60', Keys to the House '52', + 9 more — `wishlist.py --rank` lists them). Until then they rank at 0.0 with a visible flag, which under-ranks them exactly as loudly as they were over-ranked silently. | BLOCKS DEPLOY: N
Deploy: N/A — tests + one read-path flag; ships by commit/push.

FOLLOW-ON ITEMS:
- The scan backlog is now CLOSED (top-5, Batches 1–6 all implemented). Remaining from the scan's strategic section, all owner-paced: log the first matches (matches.csv still empty — the roadmap's standing bet), deck lifecycle status, rotation planning, keyword theming Tier 1.
- Standing data hygiene: the 15 Power cells above; 27 unverified printings; 4 stale tier rationales (decks 40/49).
- app.py's Flask routes and build_gallery's output remain the two untested surfaces noted by the scan (templates and the _primary_type seam ARE pinned); both need a Flask test client / HTML assertions — a different harness class than this batch's.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md [C-07]: "tests/ (18 files …)" → 24 files; the layer list gains "ingest-writer, sync-guard, resilience-layer and CLI-filter" coverage.
- CLAUDE.md G-19's long form could note the Power scale is now range-enforced at rank time (0–10, out-of-range flags pow!).
- Carry-over from Batch 4's block: G-63's "index rule now has an enforcer" clause and docs/cycle-config.md's [C-01] sub-check inventory.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
