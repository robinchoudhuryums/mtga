---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch E (tuning-pass holes, decks 12/18/40, 2026-10-08) —
  E1 maindeck castability sweep (soft check_all + audit `Crv` column);
  E2 {X} spells priced at X=2 in the cast-on-curve table instead of X=0.
Files modified: scripts/deck.py, scripts/check_all.py, tests/test_deck.py,
  tests/test_deck_models.py, .cycle/STATE.md

CHANGES:
E2 | scripts/deck.py | New module constants CAST_CAP / SPLASH_MAX (were locals of cmd_consistency) and X_ASSUMED = 2; new `cast_turn(cost, mv)` (front-face {X} count, +2 per X, capped) and `cast_on_curve_rows(...)` — the per-card table extracted from cmd_consistency so it has ONE implementation; cmd_consistency now calls it, marks X-priced rows `T4ˣ` and prints a one-line note. Fblthp 65% "T2" → 78% T4; Wan Shi Tong / Mind Spring / Finale 69% T2 → 82% T4.
E1 | scripts/deck.py | New `castability_shortfalls(meta, cards, …)`: maindecked cards casting on curve below CURVE_SWEEP_FLOOR (0.50) by turn CURVE_SWEEP_MAX_TURN (4), off a non-splash colour (> SPLASH_MAX sources), excluding `#: uncastable-ok:` cards; offline. `audit_deck` returns a report-only `crv` count; `deck.py audit` prints a `Crv` column + legend. Never reaches `verdict` or `tier_band`.
E1 | scripts/check_all.py | Soft sweep "castability: N maindecked card(s) in M deck(s) …" naming the worst three, pointing at `audit` Crv and `consistency <id>`.
tests | tests/test_deck.py, tests/test_deck_models.py | TestCastabilitySweep (11 cases: X pricing incl. back-face-only X, thin-colour row, X moves turn not pips, splash exclusion, uncastable-ok exclusion, late/healthy cards ignored, report-only source scan) + audit row carries `crv`.

Calibration (roster, 117 decks, after the X fix): floor 0.40 → 9 cards / 8 decks (7%); 0.45 → 13 / 12 (10%); **0.50 → 30 / 19 (16%)**; 0.55 → 48 / 25; 0.60 → 76 / 35. Before the X fix, 22 decks had a sub-50% T1–4 card and 7 of those were X spells at X=0. Deck 18 (the motivating case) no longer appears — its 2026-10-08 land fix took the W lords to 70%.

TEST RESULTS: passed — full pytest suite green; check_all "All invariants hold" (one new soft warning, the sweep itself: 30 cards in 19 decks).
REGRESSION RISKS: `consistency` output changed (T-cell gains a `ˣ`/space column; X spells now judged 2 turns later, raising their %). The editor's Analysis tab prints the same text. Row sort gained a name tiebreak (G-54). check_all runtime +~10s for the per-deck source profile.
INVARIANTS AT RISK: None (report-only; no data or deck file written).
NET SCORE: 2 production fixes (deck 18's 44% lords shipped unflagged; X spells mispriced on every deck running one) − 0 new failure modes = 2

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — pages.yml rebuilds the dashboard on push to main (no dashboard change in this batch).

FOLLOW-ON ITEMS:
- `pip_depth_warning` (recommendation surfaces) still prices an {X} card at its X=0 turn via `_PIP_DEPTH_TURN`; whether it should share `cast_turn` is a separate, measured question.
- The 19 flagged decks are owner reads, not defects: several are double pips a turn late (accepted trades) — 45a Zemo 16%, 80 Hexhaven Invigorator 21%, 17/10 Super-Skrull, 08 Perforating Artist on 4 R.
- Batch F (targets gate families) and Batch G (Hobbit Hole tapped + consistency convoke disclosure) remain.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md: Test Command's soft-sweep list (a twelfth sweep); G-07 (audit `Crv` column, report-only); G-36 (consistency prices {X} at X=2, marked ˣ); G-60 (X-cost advisory now reaches the cast-on-curve table).
- docs/gotchas.md long forms for G-07/G-36/G-60; README consistency/audit lines.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
