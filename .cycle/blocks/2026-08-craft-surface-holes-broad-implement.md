---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: four tooling holes surfaced while tuning decks 6, 53 and 44a.
(1) rotation flag window mismatch between craft surfaces; (4) plain `suggest` offering
off-colour LANDS; (2) `engines` misreading an opponent-graveyard engine as payoff-less;
(3) `redundancy` proposing virtual copies whose gate the deck cannot satisfy.
Three of the four are one shape: a correct primitive one caller does not reach (G-40).

Files modified: scripts/deck.py, scripts/check_patterns.py, tests/test_deck.py,
docs/gotchas.md, CLAUDE.md

CHANGES:
(1) | scripts/deck.py | `rotation_risk` tested `yr <= today.year`; `craft_rot_note`
(check, wildcards, tier --to) and wishlist --rank/--budget tested `yr <= today.year + 1`.
`craft_rot_note`'s docstring asserted the two "cannot disagree" — a claim, not a
mechanism, and false. `cmd_suggest` was the last `rotation_risk` caller, so the format's
craft recommender under-flagged by a full rotation: deck 44a's tune was offered Valgavoth
(DSK, ~2027) with no ⚠rot in the same session `check` warned about OTJ/BLB/MKM cards in
that same wave. Widened at the primitive so future callers inherit it. MEASURED:
Standard-legal pool flag rate 11% → 34% — not inflation, the share of Standard rotating
within ~15 months and the rate four other surfaces already showed. Both existing test
boundaries unaffected (3y-ago still flags, 1y-ago still doesn't); only the 2y-ago band
moved, which is the gap.
(4) | scripts/deck.py | Castability reads the PRINTED COST (G-58) and a land has no cost,
so `_candidate_castability("")` passes every land — a U/G Town (Balamb Garden) reached
Rakdos deck 44a. `suggest-homes` had an identity fallback and `functional_theme_options`
an outright exclusion; `suggest_scored` had neither. Plain suggest is the THEME path and
cannot grade a manabase (`suggest --lands` is the recommender, G-37), so it excludes
lands, front-face typed per G-63.
(2) | scripts/deck.py | ENGINE_THEMES' graveyard ENABLER cues are ownership-blind
(`mill`, `discard[^.]*card` match opponent-directed effects); its PAYOFF cues are
own-scoped. A deck filling THEIR yard and casting from it counted every enabler and no
payoff — decks 44 and 44a both read "12 enablers, no payoff — your engine has no reward"
with four working payoffs each. Fixed at the `engine_balance` caller, NOT in
ENGINE_THEMES, whose VALUE is hashed into the pool build stamp (G-18/K-10) — editing it
would force a full pool refetch for a reporting bug. Two corrections the first version
needed, both from measuring: (a) the CRIME REMINDER TEXT was matching ("cards in their
graveyards is a crime" contains the phrase the third branch seeks), so every crime card
read as yard-dependent — four measured; `_REMINDER_RE` already existed and is now applied,
which also drops one spurious zone-conflict ⛔ roster-wide (3 → 2); (b) "needs their yard
populated" ≠ "consumes their yard", and only the second is a payoff — Riverchurn Monument
scales off their yard while FILLING yards, an enabler; hence the split into
`_GY_CONSUME_OPP_RE` beside the broad `_GY_NEED_OPP_RE`, which the zone-conflict flag
correctly keeps. ROSTER DIFF: 10 verdicts move, all graveyard, all upward, two heist
decks flipping off the false verdict. Report-only (G-23), so no graded axis moves.
(3) | scripts/deck.py | `target_counts` (G-66) answers "does this deck hold what this
card asks for" only for cards already in the list; nothing ran it on a RECOMMENDED card,
so `redundancy` proposed Party Dude (draws when an OPPONENT's artifact dies) and Agent
Maria Hill (needs a teamwork cost the deck lacks) as card-advantage copies for deck 6.
New `unmet_gate_note` wires it in. PARTIAL, stated honestly: neither motivating card is
caught — "pay a teamwork cost" triggers are n=1 in the whole pool (a gate family for one
card is the over-fitting the 2026-08-19 triage declined), and Party Dude's condition is
about the OPPONENT'S BOARD, outside `target_counts`' model rather than a hole in it.
Verified live rather than left dead (G-53): reports Hobbit Hole's Halfling gate as 0
against deck 6.
Gates/tests | check_patterns.py, tests/test_deck.py | check_patterns caught
`_GY_CONSUME_OPP_RE` unregistered — registered as "norm". Nine tests added, every one
mutation-checked.

TEST RESULTS: passed — full suite exit 0; check_all all invariants hold (only the
pre-existing G-75 dead-search soft warning); check_patterns 287 live; check_engines,
check_agreement, check_rankings, check_suggest, check_docs all OK.

REGRESSION RISKS: `suggest --unowned` now flags ~3× as many picks ⚠rot. That is the
correct rate and matches four sibling surfaces, but it is a visible change and worth
watching for flag fatigue (G-07's saturation lesson) — the flag carries the YEAR, so it
informs rather than nags. `engines` verdicts change on 10 roster rows, all upward and all
report-only. No tier floor, role count or interaction figure moves anywhere.

INVARIANTS AT RISK: None — all four surfaces are report-only; ENGINE_THEMES deliberately
untouched so the pool build stamp is unaffected.

NET SCORE: 4 − 0 = 4

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — no Deploy Command configured (tooling ships by commit/push).

FOLLOW-ON ITEMS:
- Two test-authoring mistakes worth remembering, both caught by mutation: an AST test
  that passed with the guard deleted (the function already called `_primary_type`
  elsewhere), and a caller test written against deck 44a, which scores identically under
  both predicates and could not discriminate — deck 51a can. Pick the fixture that can
  tell the two answers apart.
- A dropped `class` line during an edit silently absorbed `TestStateGateCounts`'s methods
  into the preceding class. Tests still passed, so nothing caught it; restored by hand.
- The fifth hole from the same session is NOT implemented: the tier under-grade
  suppression fires for decks 53 and 44a but not deck 6, whose prose also argues the cap.
  Cue-list narrowness; failure mode is a spurious nag, the cheap direction. Measure
  roster-wide before touching (G-26).
- `_TARGET_GATES` remains a whitelist of gate SHAPES — the G-67 lesson one layer over.

DOCUMENTATION UPDATES NEEDED:
None — done in this batch (gotchas.md [G-23] and [G-30] sections, both CLAUDE.md bullets,
the G-30 one re-compressed under the 15-line cap).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
