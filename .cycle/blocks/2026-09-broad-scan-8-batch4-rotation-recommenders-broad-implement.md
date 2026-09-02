---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS8-13 `rotation_year` = release + 3 mis-dated every January–July set by a year
- BS8-12 `⚠rot` printed on owned rows and outside Standard; two rotation predicates with two scopes
- BS8-14 `cross_deck_breadth` (the `Decks` column) tested identity, not printed cost
- BS8-16 The colour-source figure audit could not see the `13/8/10 sources` idiom
- BS8-17 `--target` refused `general` / `concept:` / `21; 6` / `06`; `parse_manual` and `feedback` compared raw ids
- BS8-36 Wishlist `--rank` / `--suggest-targets` castability by identity while `--audit-targets` was pip-aware
- BS8-37 `wishlist._deck_status` ignored zero-quantity rows and short cards
- BS8-38 `--suggest-targets` STRONG ≠ `--rank` STRONG
Files modified: scripts/deck.py, scripts/wishlist.py, scripts/parse_matches.py, scripts/check_patterns.py, tests/test_deck.py, tests/test_wishlist.py, tests/test_parse_matches.py, decks/78-team-avatar/deck.txt (one figure), CLAUDE.md, docs/gotchas.md

CHANGES:
BS8-13 | deck.py `rotation_year` | Standard-year rule: a set released August+ belongs to that year's Standard year, January–July to the previous; rotation = standard year + `years`; `_SET_ROTATION_OVERRIDE` still wins. Checked against DMU…TLA. MKM/OTJ/BIG → 2026 (was 2027), DFT/TDM/FIN → 2027 (was 2028). Wishlist: Railway Brawler and Sword of Wealth and Power now ⚠rot~2026.
BS8-12 | deck.py `rotation_risk(…, legal=None)`, `craft_rot_note`, `suggest_scored` | one predicate: `craft_rot_note` delegates; `suggest` flags only UNOWNED picks, only when the deck's pool key is `standard` (60-card Brawl included — it rotates with Standard; Historic Brawl does not), only for Standard-legal cards. Deck 1 `--owned`: 155 ⚠rot → 0.
BS8-14 | deck.py `cross_deck_breadth(…, cost="")` | castability via `_filler_castable` when a cost is given; `suggest_scored` and `wishlist._breadth_of` pass it. Bullseye synthetic: 1 → 3 of 3 castable decks.
BS8-16 | deck.py `_FIG_SOURCE_SLASH`, `_slash_source_claims` | the slash form checked as a multiset over the deck's `#: colors:` (any-colour lands are sources of every colour, so off-colour counts are out of scope), rendered in the prose's own order by rank; wired into `rationale_staleness` and `note_figure_staleness`; registered with check_patterns. Found deck 78 stale on landing (13/8/10 → 14/9/11, since any-colour lands count now) — re-grounded.
BS8-17 | wishlist.py `cmd_add`, `_status_label`, `_audit_target_issues`; parse_matches.py `_norm_id`/`parse_manual`; deck.py `cmd_feedback`, `recent_ledger_adds` | all normalize through `_norm_deck_id`; `--target` accepts the Target column's vocabulary; `feedback` refuses an unknown deck by name instead of printing "nothing recorded".
BS8-36 | wishlist.py `_mana_costs`, `_castable`, the `_rank_scores` and `cmd_suggest_targets` fit loops | printed-cost castability with the identity fallback (same primitive as deck.py).
BS8-37 | wishlist.py `_deck_status` | `deck.deck_build_gap` (missing + short), keyed on the normalized id.
BS8-38 | wishlist.py `cmd_suggest_targets` | STRONG = specific theme AND score ≥ 1.5 AND a clear lead (was `lead OR score`). `--suggest-targets` STRONG count 64 on the live wishlist.

TEST RESULTS: passed — full suite green with PYTEST_NO_SKIPS=1; check_all all invariants hold. Mid-batch: two old pins on `release + 3` updated; the first slash renderer emitted sorted counts (misleading against a W/U/G claim) and read off-colour any-colour counts (deck 78 "1/1/9/11/14") — both fixed and pinned; two suite failures seen while batch-5 files were being edited mid-run re-ran green on the settled tree; `check_colors` caught my inline `in "WUBRG"` idiom (routed through `card_colors`); `check_patterns` wanted the new regex registered.
REGRESSION RISKS:
- Rotation years moved for every spring set; any prose quoting a rotation year (`⚠rot~2027`) is now a year early in places — the wishlist/check surfaces recompute, prose does not (the audit does not scan rotation figures).
- `suggest` no longer flags rotation for a Historic Brawl deck or an owned pick — both intended; a Standard-Brawl deck still flags.
- `cross_deck_breadth` with a cost admits more decks per hybrid: the `Decks` column and `hi_reuse` rise for hybrids (intended); `check_suggest` anchor 13 (suggest vs wishlist agreement) still passes.
- `_deck_status` now counts SHORT cards as remaining crafts, so the `state` column's remaining figure can be higher than before (it now equals `deck.py check`'s).
- `_slash_source_claims` treats a claim with a different NUMBER of parts than the deck's colours as stale (renders the live counts in header order).
INVARIANTS AT RISK: None
NET SCORE: 7 − 0 = 7
(BS8-13, 12, 14, 16, 17, 36, 38 all fire on live surfaces this month; BS8-37 latent until `--zero-missing` runs — counted 7. No new failure mode found.)

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — pages.yml republishes the dashboard on push to main (snapshot rebuilt).

FOLLOW-ON ITEMS:
- A pre-rotation surface: `rotation` prints ⚠ SOON, but nothing warns that ★ TUNE will flag ~80 decks on the next pool rebuild after the 2026 rotation (A-06's saturation shape).
- Rotation figures in prose (`⚠rot~2027` pasted into a rationale) are outside the audit.
- `_slash_source_claims` does not apply the other-deck / roster-name suppressions the per-colour patterns get; a slash claim about another deck would flag (none on the roster).

DOCUMENTATION UPDATES NEEDED:
- README rotation prose (the ~3-year window wording) and `wishlist --suggest-targets` STRONG description; docs/systems-map.md reconciliation inventory (rotation predicates now one).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
