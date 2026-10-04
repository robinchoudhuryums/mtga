---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS11-16 — `structural_overlay_hit` passed on ANY feeder, ignoring each overlay's floor (G-31 KEY saturation through the gate built to stop it)
- BS11-31 — `suggest --lands` labelled shocklands `·tapped?` while scoring them with the untapped premium
- BS11-61 — `cmd_mana` and `build_dashboard` re-implemented the hybrid-binding loop inline (G-70 shape)
- BS11-67 — `pip_depth_warning` picked the colour with the MOST pips (cost-string order on ties), not the one failing worst
- BS11-68 — `consistency`'s "→ want N sources" was per-colour while the probability is the joint product; 136 below-target rows had no note
- BS11-69 — `card_advantage_split` skipped `… // Land` DFCs that `role_tally` counts (split ≠ total in 6 decks)
- BS11-70 — `target_counts` typed each card from BOTH faces
- BS11-71 — `x_cost_cards` scanned the combined split cost; the advisory said X cards "book as MV 1"
- BS11-72 — an avg MV of 0.0 over ZERO priced cards earned full aggro clock credit
- BS11-74 — `consistency` labelled an empty deck "60-card deck"

Files modified: scripts/deck.py, scripts/build_dashboard.py, tests/test_deck_models.py, dashboard.html (rebuilt)

CHANGES:
BS11-16 | deck.py | each overlay branch clears only at its floor: doubler via `doubler_best` + `doubler_calib` floor (so the card's power restriction now applies too), cost-scale at `_COST_SCALE_MIN_SOURCES`, chosen-type at `_TYPE_SCALE_MIN_SOURCES` — that branch tested a TUPLE and was a tautology. Measured over every structural pool card × 114 decks with screen's inputs: 305 of 2,035 KEY verdicts → role-player (doubler 120, cost-scale 132, chosen-type 51, both 2). Deck 46's Elspeth (4 token feeders vs floor 5) is among them. The cost/type branches are the same defect in the same function, fixed together and stated here because the finding named only the doubler.
BS11-31 | deck.py | `·shock` label + legend line (score unchanged).
BS11-61 | deck.py, build_dashboard.py | `hybrid_binding(h, sources)` — the per-symbol rule — used by `binding_pips`, `cmd_mana` and the dashboard. Output unchanged (deck 14 identical).
BS11-67 | deck.py | among colours with ≥2 binding pips, each judged against its own pip-count bar; the worst failing one (lowest P, then more pips, then name — G-54) is returned. `{W}{W}{U}{U}` and `{U}{U}{W}{W}` off W15/U6 now both flag U.
BS11-68 | deck.py | `joint_source_plan` — greedy per-colour increments until the JOINT probability reaches target (reduces to `min_sources_for` for one colour; None past `nlands` → the colour-hungry note). Every below-target row across the roster now carries a note (the 40 un-noted rows are the above-target "Lowest 5" display). Deck 30's Cuboid Colony: "want 18 G (+3), 18 U (+5)".
BS11-69 | deck.py | front-face land skip, matching `role_tally`: repeatable + one-shot now equals the CA total in all 114 decks (deck 3: 3+1 → 4+1 = 5).
BS11-70 | deck.py | `target_counts`' pool `type` is the FRONT face. 67 gate counts moved across 18 decks (the finding measured 51/6 on one effect): adventure creatures count as permanent/creature cards, `Artifact // Land` cards are gate sources again, a flip-Saga is no longer a creature card to return.
BS11-71 | deck.py | X detected on `front_face_cost`; `stats` prints each X card's booked MV, and `stats`/`tier` text says "X counted as 0" instead of "MV 1".
BS11-72 | deck.py | `deck_quality_vector` publishes `avg_mv_n`; `_clock_score` treats n=0 as no data (mv 99). Absent key (hand-built vectors, check_tier) keeps the old reading.
BS11-74 | deck.py | `cmd_consistency` refuses an empty file (exit 1, message), never prints a fake 60.

TEST RESULTS: passed — full pytest suite green; check_all OK (no new soft warning); check_patterns 375 live; 10 new tests (TestScan11Batch5RecommenderMaths), the chosen-type one checked non-vacuous.
ROSTER DIFF (114 decks): tier floors moved 0; `cuts` top-3 changed 0 (cut_keep_score untouched); KEY verdicts 305 fewer for structural cards (screen/suggest-homes/suggest's fit_strength overlay).
REGRESSION RISKS: (1) Fewer KEY labels on structural cards in `suggest-homes`/`screen` — intended, but a deck sitting one feeder under a floor now reads role-player. (2) `consistency` now exits 1 on an empty deck file; no caller depends on 0. (3) The joint source plan can ask for sources in two colours at once — a larger, honest number than the old single-colour one.
INVARIANTS AT RISK: None.
NET SCORE: 9 − 0 = 9 (BS11-61 is a structural consolidation with identical output — defensive, not counted as a production fix)

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — pages.yml rebuilds the dashboard on push to main (committed copy rebuilt).

FOLLOW-ON ITEMS:
- `suggest --lands` has no test pinning the `·shock` label (data-dependent output); the score path is pinned elsewhere.
- G-31's "KEY 18.6% → 10.2%" figure predates this change; the roster KEY rate should be re-measured.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-60: "An {X} SPELL IS PRICED AT MV 1" → priced with X = 0 (MV 1 only for a one-pip X spell).
- CLAUDE.md G-31: `structural_overlay_hit` now clears each overlay only at its floor (BS11-16); re-measure the KEY rate.
- CLAUDE.md G-32 / G-36: `hybrid_binding` is the shared per-symbol rule; `pip_depth_warning` picks the worst-failing colour; `consistency`'s → note is a JOINT plan.
- CLAUDE.md G-37: `·shock` label.
- CLAUDE.md G-66/G-63: `target_counts` front-faces types.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
