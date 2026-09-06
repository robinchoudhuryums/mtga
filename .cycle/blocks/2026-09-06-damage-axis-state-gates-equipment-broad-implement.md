---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- FO-1 | Damage-doubler AXIS — `_DOUBLER_AXES["damage"]` (Twinflame Tyrant / Collective Inferno / Gratuitous Violence; 17 pool cards), feeder = NONCOMBAT damage text, calibrated (2, 7) from the roster's p50/p75; `suggest-homes` and `cuts` now see the multiplier
- FO-2 | Two state-gate families — HASTE-gated evasion (Speed: proxy = haste sources, band thin ≤1 / free ≥5) and ATTACKS ALONE (proxy = go-wide cues, INVERTED: free ≤3 / CONFLICT ≥9), with a new `conflict` verdict rendered by `targets`
- FO-3 | Granted alt costs substituted — `effective_avg_mv` returns a third figure with every grant's cost applied to the cards in its scope (`_grant_scope_matches`: type + optional colour clauses); `stats` and `tier` print it and the aggro clock it would read
- FO-4 | Equipment bucket — `_ROLE_PATTERNS["Equipment / attach"]`, last in `ROLE_ORDER`; role credit only (not interaction, not in the vector)
- FO-4b | Tap-down / neutralize — NOT implemented: found already CLOSED on 2026-08-19 (docs/gotchas.md "The neutralization bucket, closed") as Removal with a permanence line. The previous block's follow-on note was stale.

Files modified: scripts/deck.py, tests/test_deck.py, tests/test_deck_models.py, scripts/role_baseline.txt (pruned by postedit), dashboard.html, .cycle/STATE.md, this block

CHANGES:
FO-1 | scripts/deck.py | `_DOUBLER_AXES["damage"]` (doubler + feeder regex), `_DOUBLER_CALIB["damage"] = (2, 7)`, `doubler_axis` docstring
FO-2 | scripts/deck.py | two `_STATE_GATES` rows, `_STATE_INVERTED = {"alone"}`, `_STATE_BANDS` haste (1, 5) / alone (3, 9), `_state_axis_counts` gains `haste` and `alone` (go-wide via `_WIDE_CUES`), `state_gate_counts` inverted-band branch, `_STATE_FLAG["conflict"]`, `_print_state_gates` order and struggle count
FO-3 | scripts/deck.py | `_GRANT_COLORS`, `_GRANT_TYPES`, `_grant_scope_matches`; `effective_avg_mv` → (effective, printed, with_grants); `cmd_stats` / `cmd_tier` advisory lines updated (the tier line now prints whenever anything is priced, grant-only included)
FO-4 | scripts/deck.py | `_ROLE_PATTERNS["Equipment / attach"]` (equip / equipped creature / reconfigure / attach … to), `ROLE_ORDER` appended
tests | tests/test_deck.py | `TestDamageDoublerAxis`, `TestHasteAndAttackAloneGates`, `TestEquipmentBucket`
tests | tests/test_deck_models.py | grant-scope tests, 3-tuple `effective_avg_mv`, source pin extended to `_grant_scope_matches`

MEASUREMENTS (all before/after on the 114-deck roster):
- Floors: 0 bands moved; interaction / card advantage / reach / clock: 0 decks changed (`k14-after.json` → `k14-after2.json`).
- Damage axis feeder distribution: noncombat damage min 0 / p25 1 / p50 2 / p75 7 / p90 10; creatures+burn min 11 (rejected — saturates like `triggers`, G-33). 9 roster decks hold a damage doubler.
- `suggest-homes` top-5 for 10 damage doublers: 4 changed (Collective Inferno, Twinflame Tyrant, Lightning Army of One, The Rollercrusher Ride), 2 changed #1 (Lightning, Rollercrusher), all toward burn-dense decks; 6 unchanged.
- Haste gate: 3 pool cards, 1 roster holder (56, count 7 → free); 52 roster decks hold zero haste sources, so the gate can fail. n=1 residual recorded on the row.
- Attacks-alone: 53 pool cards, 13 roster instances in 12 decks; go-wide cues p25 3 / p75 9; decks 3 (17) and 55 (13) read CONFLICT, 5 / 6 / 38 / 56 / 70 read free.
- Equipment: 39 roster cards left the zero-role baseline (every one verified to carry the new role); coverage 71% → 73% (501 zero-role cards remain).
- `check_roles --tags`: no new disagreements. `check_patterns`: 340 patterns live.

TEST RESULTS: check_all — all invariants hold (soft: 39 stale baseline entries, cleared by postedit). Targeted tests: 68 pass. Full suite: all passed (exit 0; no F or E in the dot stream).
REGRESSION RISKS:
- `effective_avg_mv` now returns a 3-tuple (was 2); its only callers are `cmd_stats`, `cmd_tier` and this session's tests, all updated.
- A new doubler axis changes `suggest-homes` fit and `cuts` keep-scores for the 17 damage doublers only (bounded by `_DOUBLER_CAP`).
- `state_gate_counts` gains a `conflict` verdict; `_print_state_gates` is its only consumer and handles it. `targets` output for 12 decks gains a row.
- `ROLE_ORDER` grew by one; consumers (`stats`, dashboard `roles`, `pool.py --role`) iterate it dynamically.
INVARIANTS AT RISK: None — no writer touched; baseline prune is the G-69 last-step path.
NET SCORE: 4 − 0 = 4 (FO-4b is a no-op finding, not a fix)
  FO-1 fired this month: YES (Twinflame ranked 56a KEY off Dragon/evasion alone; the doubler was invisible). New failure mode: NO (bounded, calibrated, measured).
  FO-2 fired this month: YES (Team Avatar's attack-alone conflict in deck 3 unflagged; Speed graded on haste count by hand). New failure mode: NO (report-only; n=1 haste caveat on the row).
  FO-3 fired this month: YES (56b's curve). New failure mode: NO (report-only, pinned out of the vector).
  FO-4 fired this month: YES (Buster Sword / Doc Ock's Tentacles zero-role in 56a/56b `cuts`). New failure mode: NO (credit only, 0 floors).

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Data + tooling ship by commit/push; the dashboard is rebuilt by pages.yml on push to main.

FOLLOW-ON ITEMS:
- The haste gate's band rests on one roster holder; re-measure when a second deck runs Speed / Gingerbrute / Resilient Roadrunner.
- `_grant_scope_matches` knows types and colours only; a grant scoped by subtype ("Goblin cards") or mana value matches nothing (conservative).
- Copy-as-multiplier AXIS (a spell copier's worth is the deck's instant/sorcery density) is the last untaken doubler-shaped axis; Sparks / Return the Favor carry a role since the previous batch.
- 501 zero-role roster cards remain: the long tail, plus the remaining bucket-shaped families (extra combat, taxing, hand attack) that the 2026-08 pass listed.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-33: the damage axis and its feeder definition / calibration.
- CLAUDE.md G-76: the two new families (haste, alone) and the inverted CONFLICT verdict; "only 2 of 6 families shipped" → 4.
- CLAUDE.md G-60: the granted-cost figure.
- CLAUDE.md K-12 or G-67: the Equipment bucket as role credit; and correct the handoff's stale "tap-down taxonomy untaken" note (closed 2026-08-19).
- .cycle/NEXT-SESSION.md §"The open item this created": the neutralize half is closed; Equipment now taken.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
