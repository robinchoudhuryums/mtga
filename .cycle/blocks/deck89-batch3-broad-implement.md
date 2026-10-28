---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: B3-1 extra land drops → Ramp / fixing; B3-2 replacement multipliers → Payoff / engine;
B3-3 "X damage divided" → Removal (spot); B3-4 `engines` counters payoff cues (plan: .cycle/deck89-tooling-plan.md
Batch 3)
Files modified: scripts/deck.py, tests/test_deck_models.py, scripts/role_baseline.txt (13 pruned),
decks/76-spirit-call/deck.txt (a `#: tier:` figure this batch moved), dashboard.html (rebuild)

CHANGES:
B3-1 | scripts/deck.py `_ROLE_PATTERNS["Ramp / fixing"]` | `play (an|one|two|three|up to N|x) additional lands?` —
  32 pool cards (Azusa, Dryad, Exploration, Oracle of Mul Daya, The Gitrog Monster…), all extra land drops.
B3-2 | scripts/deck.py `_ROLE_PATTERNS["Payoff / engine"]` | `(twice that many|that many plus N)…instead` —
  32 pool cards, all counter/token/mill multipliers (Doubling Season, Hardened Scales, Vorinclex, Parallel Lives,
  Anointed Procession, Ozolith…); an opponent HALVING clause ("half that many") does not match (negative test).
B3-3 | scripts/deck.py Removal (spot) divided-damage clause | `deals? (\d+|x) damage divided as you choose among` —
  the clause fixed, not the window (G-67). +10 pool cards, all removal (Lukka −4, Fire Covenant, Avacyn's Judgment,
  Huatli, Ureni, Polukranos World Eater…).
B3-4 | scripts/deck.py `ENGINE_THEMES["counters"]["payoff"]` | + `creatures? you control with (a|one or more) +1/+1
  counters?` (Bushmaster's shape) and `twice that many of (those|each of those kinds of) counters` (Doubling Season,
  Vorinclex). Deck 89: counters 15 enabler / 1 payoff → 15 / 4.
B3 | decks/76-spirit-call/deck.txt | `#: tier:` "interaction 8" → 9, citing the card that moved it (Ureni).

TEST RESULTS: passed — pytest 2210 passed (5 new in TestDeck89RolePatternHoles, incl. a NEGATIVE halving-clause
  assertion); check_all "All invariants hold"; check_patterns 394 live; role baseline 480 → 467 (0 newly
  acknowledged, 13 stale pruned).
ROSTER DIFF (before/after, all 124 decks, K-12): Ramp / fixing up in 17 decks; Payoff / engine up in 31;
  Removal / interaction +1 in 2 (76: 8→9, 89: 15→16); card advantage 0; TIER FLOORS 0 moved; `cuts` top-3 changed in
  1 deck (89: #1 Dryad of the Ilysian Grove → Overkill); `engines` counters payoff counts up in 25 decks, 0 flags
  changed. Rationale sweep: 1 stale figure (deck 76), fixed in this change.
REGRESSION RISKS: (1) the multiplier pattern also admits mill doublers (Bruvac) and symmetric ones (Primal Vigor) as
  payoffs — consistent with the trigger-doubler argument, and Payoff is not a `tier_band` term. (2) The new
  ENGINE_THEMES strings change the pool build stamp's content hash, so the next `make refresh` rebuilds the pool once
  (G-18 by design); the tagger's keyword extraction reads only `\b`-wrapped literals, none of which were added, so no
  pool TAG changes.
INVARIANTS AT RISK: None (INV-01…04 untouched; the deck-76 edit is `#: tier:` prose, INV-04 passes).
NET SCORE: 4 − 0 = 4  (each hole fired on deck 89 this month: Dryad as #1 cut, Hardened Scales / Doubling Season
  roleless, Lukka's −4 uncounted, engines 15/1; B3-3 also under-counted deck 76)

OPERATOR ACTIONS / DEPLOY:
- The next `make refresh` rebuilds card-pool.csv once (ENGINE_THEMES hash changed) — expect the full fetch, not the
  week-long reuse | BLOCKS DEPLOY: N
Deploy: Presentation — dashboard.html rebuilt by `make postedit`; publishes via .github/workflows/pages.yml on the
  next push to main.

FOLLOW-ON ITEMS:
- Bushmaster still scores NO functional role (a deathtouch lord) — `engines` now sees it; the role taxonomy does
  not (a TAXONOMY question per G-67, not a pattern hole).
- Lukka's +1 is creature-only mana and its −1 a token maker; neither is classified, only the −4.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md K-12: the 2026-10-23 additions (extra land drops → Ramp, replacement multipliers → Payoff, X-divided
  damage → Removal) with the roster diff.
- CLAUDE.md G-23 (engines): counters payoff now reads creatures-with-counters and counter doublers.
- docs/gotchas.md K-12 / G-23 long forms.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
