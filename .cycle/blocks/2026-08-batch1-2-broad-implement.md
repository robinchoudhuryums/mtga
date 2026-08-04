---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS-10 — `--color R` matched every Colorless card in query.py / pool.py / wishlist.py (substring `in`, the F1 trap as a filter)
- BS-18 — check_colors' AST scan could not see the substring re-implementation shape (only the comprehension idiom)
- BS-11 — `cmd_tribes`' type-matters payoff scan was plural-blind (`\bNinja\b` misses "Ninjas"), under-reporting the count G-59 says decides tribal viability
- BS-12 — `load_keywords` had no DFC front-face alias (the sixth unaliased G-63 index); front-named DFC lines read as "no keywords"
- BS-13 — `fetch_missing_mana` stored a split/Room card's COMBINED mana value, skipping the front-face correction `load_mana` applies
- BS-14 — `suggest-homes` / `similar` / `sync` iterated `discover_decks()`, so an example/retired deck could be rated a KEY home or rewritten by a sync match
- BS-09 — reflected XSS in the deck-editor 404 (`app.py` echoed the path segment unescaped)
- BS-03 — `sheets_sync pull` was the one authoritative overwrite path with no shrink guard, writing by default
- BS-15 — `import_collection` collapsed foil/non-foil rows sharing (name, set, collector) with max, halving those holdings on the one tool that can LOWER a count
- BS-16 — `reconcile_crafts`' pool name index was not front-face aliased and its DFC fallback was dead code (live G-63 violation)
- BS-17 — a wishlist row Power-seeded during a Scryfall outage (flat 2.0 from blank data) was never re-seeded when its data arrived
- (Batch-2 rider) — `build_mana`'s front-face retry loop caught ScryfallUnavailable and kept writing, so a mid-`--refetch` outage committed blanks over ~700 previously-good split/Room/DFC costs

Files modified: scripts/lib.py, scripts/query.py, scripts/pool.py, scripts/wishlist.py, scripts/check_colors.py, scripts/deck.py, scripts/app.py, scripts/sheets_sync.py, scripts/import_collection.py, scripts/reconcile_crafts.py, scripts/build_mana.py, tests/test_lib.py, tests/test_ingest.py

CHANGES:
BS-10 | scripts/lib.py, query.py, pool.py, wishlist.py | New `lib.color_matches(cell, needle)` — SET semantics through `card_colors` on both sides (WUBRG needle ⊆ identity; letterless needle like "colorless"/"c" matches only colorless; None/blank = no filter). All three CLIs route --color through it. Verified: `query --color R` 546 → 442 rows (the 104 Colorless now under `--color colorless`).
BS-18 | scripts/check_colors.py | New `_scan_color_cell_membership()` — flags any `in`/`not in` whose CONTAINER source mentions `Color(s)` without routing through card_colors/color_matches (left-operand header checks pass untouched). Watched it fail: flags the old buggy line, ignores the two legitimate shapes. Plus four behavioral anchors on `color_matches` itself, and 5 unit tests in tests/test_lib.py.
BS-11 | scripts/deck.py | New `_tribe_ref_re(t)`: singular OR plural type references (-y→-ies, -f→-ves, sibilants→-es, +s, Mouse/Ox irregulars). Verified: deck 49 payoff list now shows Lathliss/Firespitter Whelp/Dragonlord's Servant etc.; deck 48 shows Ultron/Ravenous Robots/Mouser Foundry — all plural-templated lords previously invisible.
BS-12 | scripts/deck.py | `load_keywords` aliases fronts in a SECOND pass (order-independent, real rows never shadowed — the load_rarities pattern). Verified: Cecil, Dark Knight's ⌘ keywords line restored in `text 42`.
BS-13 | scripts/deck.py | `fetch_missing_mana` recomputes `mv = mana_value(front_face_cost(cost))` when the fetched cost contains " // " — the identical correction load_mana applies to stored rows.
BS-14 | scripts/deck.py | The three sites now iterate `roster_decks()` (with comments); `find_deck`, `cmd_list` and the rationale name-mask deliberately stay on `discover_decks()` (direct addressing / full inventory / wider masking is safer).
BS-09 | scripts/app.py | `html.escape(deck_id)` in the 404 body (+ `import html`). The sibling 404 at /api/deck is JSON (jsonify) — no escape needed.
BS-03 | scripts/sheets_sync.py | `pull` is now DRY-RUN by default (`--apply` writes) and refuses a >50% row-count shrink without `--allow-shrink` (same `_SHRINK_FLOOR = 0.5` as import_collection) — a header-only sheet passes validate() with zero rows, so the guard is the only protection for that case. Tested with a fake worksheet: header-only → refused; 10-row sheet vs 1,899 local → refused; full-size dry-run → reports, writes nothing. push unchanged.
BS-15 | scripts/import_collection.py | `parse_export` gains an optional `finish` column role and pre-collapses per (front, set, collector): repeats within one finish take MAX (one holding stated twice), DISTINCT finishes SUM. With no finish column the old max semantics hold unchanged, and plan()'s own collapse stays as the backstop for direct callers. 3 new tests pin all three behaviors.
BS-16 | scripts/reconcile_crafts.py | Pool name index aliases fronts in a second pass; the dead third fallback deleted. Verified: a front-name paste with an unheld (SET) # now resolves to "Bruce Banner (ZZZ) 999 [DFC front of Bruce Banner // The Incredible Hulk]" instead of NOT FOUND (dry run).
BS-17 | scripts/wishlist.py | The F20 re-enrich branch recomputes `_seed_power` when `power_is_seeded(prev)` (seed/unknown/blank per G-17); hand grades never touched. Verified: blank-data seed 2.0 → 6.5 once Type/Text/Rarity arrive.
build_mana | scripts/build_mana.py | The front-face retry loop no longer catches ScryfallUnavailable — it propagates to main()'s existing clean-abort handler, leaving card-mana.csv untouched (G-14's rule). Incremental mode now aborts too instead of keeping partial progress; strictly the safer direction.

TEST RESULTS: passed — check_all all invariants hold (same 2 pre-existing soft warnings: 27 unverified printings, 4 stale tier rationales in decks 40/49); full pytest 869/869 (861 prior + 5 new color_matches + 3 new finish-dedupe) in 67s; scenario walks clean across deck.py (help/tribes/ramp/homes/similar), query/pool/wishlist --color, card.py, and all four ingest-cluster --help surfaces.

REGRESSION RISKS:
- `--color` semantics deliberately changed from substring to set: a multi-letter needle is now an AND over identity letters regardless of stored order; garbage needles match colorless instead of nothing. CLI-only surface, no programmatic caller.
- `sheets_sync pull` now requires `--apply` — an operator following the old README-style usage gets a dry-run report telling them so (visible, not silent). Never run in production to date.
- `import_collection` totals can now be HIGHER than before for finish-split exports (that is the fix); exports without a finish column are bit-identical in behavior.
- `build_mana` incremental runs that hit an outage mid-front-face now abort entirely (rerun needed) rather than keeping partial batch progress — trades convenience for never writing blanks.
- `check_colors`' new membership scan could flag legitimate future code that tests membership against an expression mentioning Color(s); the failure is loud at the gate and the message names both escape hatches.
- `_tribe_ref_re` pluralization could over-match an unrelated word equal to a tribe's plural; bounded by the deck's own subtypes, and a false payoff listing is a visible report line, not a score.

INVARIANTS AT RISK: None — INV-01 preserved (import_collection still emits one entry per printing; sheets pull still validates before write and now also shrink-guards); INV-02 untouched (`_ensure_mana_rows` runs after an applied pull exactly as before); INV-03/04 untouched. check_all green post-change.

NET SCORE: 4 − 0 = +4 (BS-10, BS-11, BS-12, BS-16 all fire in a normal month of roster work; BS-09/03/13/14/15/17/build_mana are hardening of reachable-but-unobserved paths)

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — data + local tooling ship by commit/push; the dashboard redeploys via pages.yml on merge to main (no modified file feeds its build differently).

FOLLOW-ON ITEMS:
- Remaining scan backlog by batch (from the session's priority list): Batch 3 interface parity (BS-08 deck-editor JS front-face buildability, BS-21a/b dashboard+gallery keyboard access, aria-sort, beforeunload, decks badge, analysis-tab retry, refresh-dashboard step); Batch 4 gate hardening (sibling-filter diff gate, lib.alias_front + check_dfc index/payload scan, BS-04 check_patterns perimeter, BS-19 role_baseline pruning, gate tail); Batch 5 low-severity correctness tail; Batch 6 tests for the 7 uncovered scripts + doc rot.
- The F20 re-enrich + re-seed path (BS-17) still has no test — cmd_add needs a Scryfall mock harness; belongs in Batch 6 with the other wishlist coverage.
- `deck_needs` derives an undeclared deck's colors from identity (noted last session, still open, moot while every roster deck declares `#: colors:`).

DOCUMENTATION UPDATES NEEDED:
- README/CLAUDE.md: `--color` filter semantics (set-based, `--color colorless` now the way to list colorless cards) and `sheets_sync pull`'s new dry-run/--apply/--allow-shrink contract (README documents the old usage).
- CLAUDE.md's check_colors description can now claim the substring shape is gated (it previously overpromised); G-63's long form gains BS-12/BS-16 as members; G-58's gains the needs-model re-introduction (from the previous block, still unwritten).
- Previous block's doc items (G-38/G-22 needs-model note) remain queued — run /sync-docs once for both blocks.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
