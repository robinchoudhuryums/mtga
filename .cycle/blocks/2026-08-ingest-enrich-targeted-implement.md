---TARGETED IMPLEMENTATION SUMMARY---
Scope: Ingest & Enrich
Actions completed: A1, A2, A3, A4, A5
Actions not completed: All completed. (A6 stays deferred by the handoff — whether spoiled
cards belong in the pool as planning data is a design call, not a bug fix.)
Files modified: scripts/build_pool.py, scripts/deck.py, scripts/check_all.py,
tests/test_build_pool.py, tests/test_deck.py, card-library.csv, card-pool.csv,
card-pool.build, 28 deck files under decks/, CLAUDE.md, docs/gotchas.md, README.md,
dashboard.html

CHANGES:
A1 | build_pool.py | RELEASED_ONLY/QUERY_ALL/QUERY_STANDARD constants add `date<=now` to
  both default queries. The literal token `now` is load-bearing: the freshness reuse
  compares `stamp_query == query`, so a formatted date would differ daily and force a
  ~4-min refetch every `make refresh`. `--query` is deliberately not rewritten. Rebuilt:
  16,067 -> 15,973 rows, 0 unreleased. | F1
A2 | card-library.csv | Overgrown Tomb TRK 289 -> ECL 266, Watery Grave TRK 306 -> EOE 261,
  written through lib.write_rows (atomic + .bak). These two outlived the pool fix because
  `_printing_index` prefers an owned printing. | F3
A3 | deck.py (`resolve --fix`), 28 deck files | New repair half for `--check`, whose only
  remedy was a hand edit (G-77). Rewrites printing fields only, carrying qty/name/comment
  verbatim; dry-run default; `--apply` goes through `_safe_write_lines`. Keyed on
  (name,set,collector) so a good twin line survives; extended to basics for the SET CODE
  only, since `printing_problems` exempts them and 76 of the 109 lines were basics. 64
  card lines rewritten across the roster; 0 TRK references remain; all 116 decks pass
  strict `resolve --check`. | F1, F4
A4 | deck.py (`unreleased_pool_cards`), check_all.py | Soft sweep reporting pool rows dated
  in the future. POOL-level by design: the exposure is a property of the file, so one
  report covers suggest/--lands/--ramp/--interaction, tier --to and wishlist
  --rank/--budget at once — and being report-only it re-ranks nothing, so no K-12 roster
  diff was required. | F2
A5 | tests/test_build_pool.py, tests/test_deck.py | 13 tests. Test doubles that hardcoded
  the OLD default query were repointed at the constants as part of A1, not reactively.

TEST RESULTS: passed — 1436 passed, 1 skipped (was 1423). check_all green with 1 soft
warning (the 4 accepted dead tutors). check_patterns 268 live, check_commands OK,
check_docs OK, argparse builds.
Four mutants watched failing: reverted query bound; formatted date instead of `now`;
--fix keyed on name only (rewrote a good twin); basics extension removed.

REGRESSION RISKS:
- A1 changed pool CONTENT, which every Analysis surface reads. Verified after rebuild:
  check_all INV-03, full pytest, check_patterns (268 patterns still live against the new
  pool), check_suggest. Shrink guard passed cleanly (94 rows is far under the 50% floor).
- The handoff predicted A1 would turn `resolve --check` red across the roster before A3
  landed. It did — as a HARD INV-04 error, not soft, because A2 had also removed TRK from
  the library. Sequencing A1->A2->A3 in one change is what keeps that window closed;
  splitting them across commits would leave the roster red in between.
- A REAL BUG was found by the new tests, not by review: `_resolve_fix` matched LINE_RE
  against the raw line, and since that pattern anchors on `$`, a trailing `# comment`
  swallowed the printing into the name group and the line silently failed to match. Every
  other line-rewriting site strips the comment first; this one now does too. No roster
  line was affected (0 TRK remain), but the fix would have skipped commented lines.

INVARIANTS AT RISK: None. INV-04 is strengthened — 109 lines that were structurally valid
and un-importable are now both. INV-01 unaffected (A2 changed two cells, no new rows, no
duplicate printing). INV-03 verified post-rebuild.

NET SCORE: 3 production fixes (F1, F2, F3) + 1 latent bug found by the new tests − 0 new
failure modes = 4

INVARIANT CANDIDATES:
- "No deck line may name a set whose release date is in the future." Currently enforced
  indirectly: the pool cannot supply one (A1) and check_all reports it if the pool does
  (A4). A direct INV-04 clause was considered and NOT added — the deck line itself carries
  no date, so the check would have to join through the pool, and it would duplicate A4's
  coverage at a hard-failure severity that a stale pool could trip.

OPERATOR ACTIONS / DEPLOY:
- Paste one previously-affected deck (e.g. 76) into MTG Arena to confirm the repaired
  lines import. This is still the one fact the repo cannot establish, and it is now the
  ONLY open question from the audit. | BLOCKS DEPLOY: N
- A future `build_pool.py --query ...` run bypasses the release bound by design; the
  check_all sweep is what surfaces it. | BLOCKS DEPLOY: N
Deploy: Data + tooling ship by commit/push. Dashboard rebuilt via `make postedit`; Pages
republishes on push to main.

FOLLOW-ON ITEMS:
- deck.py: `Released` is read only for rotation everywhere except the new sweep. A
  per-card "not out yet" flag on the craft surfaces remains unbuilt (deliberately — A4
  covers the exposure without re-ranking anything). Revisit if a custom-query pool becomes
  routine.
- build_gallery.py / build_dashboard.py (Presentation, out of scope): both read the pool
  and were not audited. The next targeted audit in the recommended sequence.
- A6 deferred: whether spoiled-but-unreleased cards should be in the pool as PLANNING data
  behind an explicit marker. A1 drops 94 of them; that is correct for recommending and
  arguably a loss for craft planning ahead of a set.

DOCUMENTATION UPDATES NEEDED:
- Done in this change: G-79 in CLAUDE.md with full evidence in docs/gotchas.md; README
  documents `resolve --fix` and the pool's release bound.
---END TARGETED IMPLEMENTATION SUMMARY---
