---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (Batch 3 — interface parity):
- BS-08 — deck editor's client-side buildability had no DFC front-face fallback (deck 43 read "1 missing" while /decks and `deck.py check` said buildable)
- Analysis-tab errors were cached until reload — a transient failure could never be retried
- BS-21a — five dashboard controls (viewGrid/viewCompact/copyall/exportwl/palettehint) missed the a11y() keyboard wrap
- S3 — `aria-sort` set only at construction; stale after any sort click
- BS-21b — the gallery filter bar was mouse-only (pips/chips no role/tabindex/key handler, no :focus-visible anywhere, unlabeled search)
- S4 — collection editor: add/remove/revert reloads silently discarded other staged edits; no beforeunload guard
- S5 — /decks conflated missing (red everywhere else) and short into one amber badge
- Refresh gap — nothing rebuilds the committed dashboard.html and `/refresh`'s doc claimed step 5 did

Findings implemented (Batch 5 — low-severity correctness tail):
- `consistency`'s per-card → note targeted the max-pip color, not the BINDING (lowest per-color probability) color
- `legal` exited 0 despite a hard ✗ bad-set failure (G-65); preflight inherited via cmd_legal's rc
- `sync --apply` exited 1 after a fully successful repair
- Snow-covered basics tripped the 4-copy limit (rules-basics per CR 205.4c; deliberately NOT added to the ownership-side BASICS set — they are craftable in Arena)
- `flex_staleness` compared names exact-case (permanent false STALE on a case mismatch)
- `cmd_list` checked ownership per LINE, not per aggregated name (disagreed with `check` on split lines)
- `load_card_data` / `load_legalities` / `_pool_rotation_index` used the in-loop front-face alias that lets a full-name row shadow a real card named `Front` (now the load_rarities second-pass pattern)
- Inline `# comments` on card lines were dropped by `_swap_edit_lines` / `reconcile_lines` rebuilds (new `_line_comment` helper re-attaches them)
- wishlist: duplicate (name, set) rows ranked twice and `--budget` could spend two slots on one card (rank output now name-unique, best combined kept — live dups Drakuseth/Sally Pride, Tier A 133→131); `pw = power or land_val` collapsed a hand-graded 0 (now keyed on blank-ness); `_land_value` counted a `{W}` ACTIVATION COST as color production (now Add-clause-scoped)
- `lib.mana_value` counted `{2/G}` as 1 (CR 202.3f: larger half — Wildgrowth Archaic {2/G}{2/G} is MV 4); 13 pool cards
- `lib.atomic_write`: fsync file before replace + directory after (the docstring's "durably" is now true), target permissions preserved (writes flipped CSVs 644→600), `*.tmp` gitignored
- `scryfall._run` retried non-retryable 4xx for ~63s before misreporting an outage (now raises immediately, naming it a client error)
- `import_arena.parse` is section- and block-aware: Deck+Sideboard copies within one block SUM (they draw from the collection simultaneously — 2+2 Duress proves 4, max() recorded 2), same-section repeats and separate Deck blocks take MAX, Companion folds into Sideboard
- `parse_matches`: blank matchIds no longer dedupe against each other (id-less matches were silently dropped as "already recorded"); `_ME_RE` accepts lowercase userIds (truncation made every match skip while blaming a missing header)
- `card.py`'s K-01 unindexed-mechanic check reports its own failure to stderr instead of `except: pass`
- `pool.py` imports `deck.classify_roles` lazily on first --role use instead of at module load

Files modified: templates/deck.html, templates/collection.html, templates/decks.html, scripts/build_dashboard.py, scripts/build_gallery.py, scripts/deck.py, scripts/wishlist.py, scripts/lib.py, scripts/scryfall.py, scripts/import_arena.py, scripts/parse_matches.py, scripts/card.py, scripts/pool.py, Makefile, .claude/commands/refresh.md, .gitignore, tests/test_ingest.py, tests/test_deck.py

CHANGES (highlights; one line each, full detail in the diffs):
BS-08 | templates/deck.html | New `ownedOf()` mirrors lib.owned_qty's full-then-front resolution at the JS lookup (covers names typed after render, which a server-aliased map cannot)
Refresh gap | Makefile, refresh.md | New `make dashboard` target (~1m44s measured — deliberately OUTSIDE refresh, which is ~13s no-change; pages.yml rebuilds on deploy anyway); refresh prints a NOTE; refresh.md step 5's false "(images + dashboard)" claim corrected
consistency | scripts/deck.py | `worst_col` = argmin of per-color hypergeometric term (tiebreak pips desc, then name — total order per G-54)
import_arena | scripts/import_arena.py | Per-block accumulation with section sets; `_fold_block` takes cross-block max; 3 new tests pin sum/max/companion semantics

TEST RESULTS: passed — check_all all invariants hold (same 2 pre-existing soft warnings); full pytest 872/872 (3 new import_arena pins + 1 mana_value hybrid line); scenario walks clean on pool/card/consistency/legal/list/flex/wishlist-rank/parse_matches/sheets surfaces; templates markup-contract tests green; wishlist --rank output diffed against pre-change code via git stash (only intended changes: dedupe 133→131; the "pow 78.0" anomaly reproduces on OLD code — pre-existing data typo, see follow-ons)

REGRESSION RISKS:
- `import_arena.parse` now returns one aggregated entry per printing instead of raw lines — verify/sync/verify_ingest consumers are quantity-equivalent (they summed per name anyway; tests green); a caller wanting raw lines would need the text itself.
- `legal`/`preflight` now BLOCK on a nonexistent set code (G-65's stated semantics); any deck that trips it would already hard-fail check_all's INV-04, so no current deck changes verdict.
- `sync --apply` rc semantics: non-zero now means unmatched/skipped/failed, not "drift was found and repaired"; dry-run rc unchanged.
- `_rank_scores` returns fewer rows when the wishlist holds duplicate names (by design; per-set views like --by-set are unaffected — they don't rank).
- beforeunload prompts on tab-close with unsaved edits (intended; suppressed for the guarded actions' own reloads).
- atomic_write adds one fsync per write (negligible at this scale) and sets 0644 on newly created files.

INVARIANTS AT RISK: None — no CSV schema or writer changes; INV-01…06 verified via check_all post-change.

NET SCORE: 4 − 0 = +4 (BS-08 visibly wrong today; the wishlist double-spend has live duplicate rows; the consistency advisory misfires on any splash deck; the /refresh doc claim actively misled sessions. The rest is latent hardening.)

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — ships by commit/push; dashboard.html + gallery.html regenerate from the modified builders on the next `make dashboard` / `make refresh` (deployed dashboard rebuilds via pages.yml on merge to main regardless)

FOLLOW-ON ITEMS:
- Committed dashboard.html/gallery.html still carry the OLD markup until regenerated — run `make dashboard` and `make refresh` (or let pages.yml cover the deployed dashboard). Deliberately not regenerated here to keep the diff reviewable.
- Wishlist data typo: Pensive Professor's Power cell reads 78.0 (scale is 0–10) and Riverchurn Monument 74.0 — pre-existing, reproduced on pre-change code; the NaN/inf guard doesn't catch large finite values. A range check in `_rank_scores` (flag Power > 10) is a small Batch-4-adjacent add; the cells need hand-fixing either way.
- Batch 4 (gate hardening) remains: sibling-filter diff gate, lib.alias_front + check_dfc index/payload scan, BS-04 check_patterns perimeter, BS-19 role_baseline pruning, gate tail (flavor_overreach swallow, check_docs anchor cap, soft-skip escalation, delta-blind printings count). Batch 6 (tests for 7 uncovered scripts) remains.
- The source-count sites that guard on `nl in BASICS` still never reach the new snow-covered BASIC_COLOR aliases (noted in-code; matters only if a snow basic ever enters a deck — none are Standard-legal today).

DOCUMENTATION UPDATES NEEDED:
None — this batch landed alongside the /sync-docs pass that already updated README (--color semantics, sheets_sync contract, import_collection finish column), CLAUDE.md (check_colors both scans, G-38 needs-model, G-63 five new members incl. the JS payload fix), docs/gotchas.md (G-58/G-63/G-38/G-59/G-17 addenda), the app.py mtime docstring, and test_cli's stale counts.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
