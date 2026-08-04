---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (Batch 4 — gate hardening: make the found bug classes impossible):
- Sibling-castability parity gate — check_suggest anchor 13d: the BS-01 class (a castability fix landing in one suggest sibling and not the others) now fails the build
- lib.alias_front — G-63's index rule given ONE home; six per-loader copies unified, and check_dfc gained an INDEX-ALIAS registry + a serialized-payload pin
- BS-04 — check_patterns' perimeter now covers wishlist.py's oracle-text classifiers
- BS-19 — role_baseline.txt gained its pruning half (stale_baseline_entries), wired into check_all
- Gate tail — flavor_overreach reports its own skip; check_docs' anchor regex survives G-100; crash-skipped radars are promoted with their own count in check_all's soft section; the unverified-printings warning names cards instead of a delta-blind count

Files modified: scripts/check_suggest.py, scripts/lib.py, scripts/deck.py, scripts/reconcile_crafts.py, scripts/check_dfc.py, scripts/check_patterns.py, scripts/check_roles.py, scripts/check_all.py, scripts/check_docs.py, scripts/check_keywords.py, scripts/check_colors.py

CHANGES:
13d | check_suggest.py | The synthetic world's cards gained per-card colors/costs plus four discriminators where identity and printed cost DISAGREE (a mono-U-castable {1}{U/R} hybrid removal spell, a {3} rock with 5-color identity — the Haunted Screen case, a hybrid on-theme creature for suggest_scored, and a genuinely uncastable {W}{W} control). Anchor 13d runs suggest_interaction / suggest_mana / suggest_scored end-to-end and fails if any sibling's discriminating pick vanishes or the uncastable control appears. WATCHED IT FAIL: simulated both regressions (hybrid hidden from interaction; rock hidden from mana) — detected both; clean after restore. The fixture routes Color(s) parsing through lib.card_colors (an earlier draft re-implemented the F1 idiom in the fixture itself).
alias_front | lib.py, deck.py, reconcile_crafts.py | New `lib.alias_front(index)` — the order-independent second-pass front-face alias with the real-row-wins guarantee. Replaces five per-loader copies (load_keywords, load_legalities, load_rarities, load_card_data, _pool_rotation_index) and reconcile_crafts' copy; known_printings keeps its own alias (different semantics — it tracks real-row provenance for printing merges).
check_dfc | check_dfc.py | (3) `_ALIASED_LOADERS` registry: seven loaders behaviorally verified to resolve a live DFC's front key (getattr at run time, so a rename is a hard error — the stale-registry rule); WATCHED IT FAIL on a de-aliased load_keywords. (4) `_payload_flags`: pins templates/deck.html's `ownedOf` helper and its front-split — the serialized-index consumer no Python scan can reach (BS-08's channel). Residual stated in the docstring: a NEW raw lookup elsewhere in the template wouldn't fire it.
BS-04 | check_patterns.py | wishlist added to _SCANNED_MODULES; `_FLEX_REMOVAL_RE` + `_CONDITIONAL_POWER_RE` registered on the norm corpus, LINE_RE excluded with reason. WATCHED IT FAIL: adding the module before registering produced exactly the three completeness errors. 175 patterns now live.
BS-19 | check_roles.py, check_all.py | `stale_baseline_entries()`: flags a baseline entry whose card now classifies (masking a future re-zeroing regression forever) or left every deck (roster-scoped, acknowledges nothing). Wired into check_roles' CLI and check_all's soft block. WATCHED IT FAIL on an injected entry; clean baseline reports empty.
tail | check_keywords.py, check_docs.py, check_all.py | flavor_overreach's `except: pass` now eprints a skip naming what's degraded (WATCHED IT FAIL by breaking ENGINE_THEMES' shape); ANCHOR_RE/HEADING_RE accept 3-digit anchors; check_all partitions crash-skipped radars above ordinary soft warnings with a "N RADAR(S) DID NOT RUN" count (stateless by design — no cross-run counter, just impossible to read as health); the printings warning shows the first three offending lines.
perf | check_colors.py | The batch-1 membership scan called ast.get_source_segment (O(file)) on EVERY `in` node — measured +28s of check_all runtime. Now a cheap subtree walk for the "Color(s)" constant gates the expensive call (plus a whole-file substring pre-filter). Sensitivity re-verified: still flags the old buggy shape, still exempts card_colors/color_matches. check_all 67s → 42s (~39s pre-batch baseline; the ~3s left is the new gates).

TEST RESULTS: passed — full pytest 872/872; check_all all invariants hold (same 2 pre-existing soft warnings, now with named printings); every touched gate run standalone and green (check_agreement, check_suggest, check_dfc, check_patterns, check_roles, check_docs, check_colors); every NEW guard watched to fail on its target regression before being trusted.

REGRESSION RISKS:
- The index-alias registry runs seven loaders inside check_dfc (~1.1s, memoized loaders shared with the rest of the run); a future loader rename fails the gate until the registry entry is updated — intended (stale-registry rule).
- `_SYN_CARDS`' tuple shape changed (5 → 7 fields); it is private to check_suggest and all uses were updated in the same edit.
- alias_front unification: behavior verified identical on live data for all six converted sites (front keys resolve; real cards never shadowed). known_printings deliberately not converted.
- The radar-down partition keys on the literal " skipped (" in warning text — a new soft check that words its degradation differently would land in the ordinary section (cosmetic, not silent).

INVARIANTS AT RISK: None — no data writers touched; INV-01…06 verified via check_all post-change.

NET SCORE: 0 − 0 = +0 by the "fired this month" measure — and that is the point of this batch: nothing here fixes a live bug; it makes the two bug classes that produced most of this scan's findings (sibling filter drift, un-aliased front-face indexes) fail the build at introduction, and stops the soft-radar channel from decaying silently. The scan's own evidence says both classes recur (G-58 re-introduced once, G-63 seven times).

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — gates are local tooling; ships by commit/push.

FOLLOW-ON ITEMS:
- Batch 6 remains: behavioral tests for the 7 uncovered scripts (reconcile_crafts and sheets_sync first — canonical-file writers), the F20 re-seed path, and a Power>10 range flag in wishlist._rank_scores (the Pensive Professor 78.0 data typo found in batch 3/5; the cells themselves still need hand-fixing).
- The two standing data-hygiene soft warnings (27 unverified printings, 4 stale tier rationales in decks 40/49) are owner deck-file edits, now with named examples in the warning.
- check_dfc's payload pin covers deck.html's helper only; if more templates ever consume the ownership map, register them.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md's G-63 bullet could note the index rule now has an enforcer (`lib.alias_front` + check_dfc's registry) — one clause, next /sync-docs pass.
- CLAUDE.md's Cycle Workflow Config gate description ([C-01]) still says "thirteen check_*.py gates" wording variants — unchanged counts, but the new sub-checks (13d, index-alias registry, role-baseline pruning) belong in docs/cycle-config.md's long form.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
