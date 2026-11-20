---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: M1 needs lane (removal/ramp/fixing reach the decks that want the job); M2 artifact lanes (artifact payoff ↔ artifact count by type line; artifact ↔ artifact payoffs); M3 multiplier lane (counters/tokens feeder ↔ the deck's multipliers, plus-one replacements included); M4 KEY saturation (fit_strength's top-theme branch asks the overlay for a generic theme)
Files modified: scripts/deck.py, scripts/check_patterns.py, scripts/check_suggest.py, tests/test_deck.py, tests/test_deck_models.py, CLAUDE.md, docs/gotchas.md

CHANGES:
M1 | scripts/deck.py | needs_axis() + _needs_lane_rows(): a card whose role is interaction / ramp / fixing is ranked into the ≤5 castable, legal decks that most want the job (interaction by distance to the A line, excluding decks >2 above it; ramp by _accel_want ≥ 0.6; fixing by colours covered ≥ 2), upgrading a tangential row or adding one. KEY only below the needs minimum.
M2 | scripts/deck.py | resource_lane_hits(): "artifact count" (artifact_payoff via K-15's _ARTIFACT_MATTERS_RE, imported; floor 10 / key 20 artifacts by type line) and "artifact payoffs" (card IS an artifact; floor 5 / key 10 payoff cards). Calibrated at the roster's p90 (140 decks).
M3 | scripts/deck.py | multiplier_axes() / feeder_axes(): a counters/tokens feeder meets the deck's multipliers (doublers + plus-one replacements; floor 2 / key 3); a plus-one multiplier is priced by its feeders through doubler_calib. Feeder patterns are _DOUBLER_AXES' own plus an enters-with counter pattern.
M1-M3 | scripts/deck.py | cmd_suggest_homes checks the lanes BEFORE `if not shared: continue` (a theme-less deck could previously reach no row); lane-only rows are role-player, KEY only at an artifact lane's key level; lanes boost theme rows (bounded, promote tangential → role-player). structural_overlay_hit reads the lanes and takes card_type, passed at all three callers (screen, suggest-homes, quality --add).
M4 | scripts/deck.py, tests/test_deck.py, scripts/check_suggest.py | fit_strength's top-theme branch now requires the overlay for a GENERIC theme, as the signature branch already did; the two pinned contract tests and the (11b) gate updated to the new contract, with the measured rescue recorded.
tests | tests/test_deck_models.py | TestHomesLanes: 11 tests (multiplier/feeder/payoff predicates, each lane at its floor, overlay wiring, bounded boost, needs_axis, needs-lane bound + headroom, top-theme overlay condition).
gates | scripts/check_patterns.py | _PLUS_ONE_COUNTER_RE / _PLUS_TOKEN_RE / _COUNTER_FEED_EXTRA_RE registered on the raw corpus.
docs | CLAUDE.md, docs/gotchas.md | G-31 rule rewritten within the 300-word cap; long form with the measurements and residuals added under [G-31].

MEASURED (101 ingested cards × 140-deck roster, new-home rows): KEY 218 → 158; known homes found 4 → 11 of 16; KEY decks per card p90 6 → 4, max 15 → 13; total rows 1539 → 1561; role-player 343 → 569 (133 tangential → role-player, 97 KEY → role-player). Deck 30 rescue cards (Innkeeper's Talent, Branching Evolution, Hardened Scales, Kami of Whispered Hopes, Conclave Mentor, The Ozolith, Deanna Troi) and deck 86 (Deanna, Mikaeus, Hardened Scales, Gaseous Anomaly): `screen` verdicts identical before and after. suggest-homes runtime on the set 63 s → 68 s.

TEST RESULTS: passed — full suite 2395 passed, 1 skipped (2384 + 11 new); check_all integrity OK, 50 soft (unchanged; all pre-existing figure drift).
REGRESSION RISKS: M4 changes verdicts on all three fit_strength callers (screen, suggest-homes, quality --add): a card whose fit to a generic spine is real but not structural (no doubler/multiplier/resource lane) now reads role-player instead of KEY — the deck-30 rescue set was checked and is unaffected. structural_overlay_hit is broader, so a generic SIGNATURE theme now earns KEY for lane hits too (e.g. Gaseous Anomaly in deck 98 via its token in a 2-multiplier deck).
INVARIANTS AT RISK: None (no data file is written; INV-01..06 untouched).
NET SCORE: 4 − 1 = 3

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — no Deploy Command configured for the Analysis subsystem (Presentation's pages.yml rebuilds the dashboard on merge; the dashboard does not render suggest-homes).

(Not complete in production until blocking operator actions are done AND
the deploy step is confirmed.)

FOLLOW-ON ITEMS:
- The rainbow-fixer overlay promotes Gaseous Anomaly (a colourless land whose Planet token taps for any colour) to KEY in 4- and 5-colour decks — the fixer rate reads the token's text as the land's.
- Harmonic Prodigy reads as a trigger doubler for every deck (KEY in ~10): `doubler_restriction` parses only a POWER scope, not its "Shaman or another Wizard" type scope — G-33's documented KNOWN GAP.
- Needs lane ranks by NEED only; a premium answer that is an upgrade over a deck's weakest removal (Sheoldred's Edict → 98/87/92) is a power read this lane does not make.
- Deck 95 (blink): an enters-with feeder's value under flicker is invisible to every lane.
- CLAUDE.md figure drift (16 soft warnings, pre-existing): K-05, K-09, K-15 (280 → 301), G-85, G-86, G-35, G-80, K-03, G-22.

DOCUMENTATION UPDATES NEEDED:
- None beyond what landed (G-31 rule + long form). /sync-docs could refresh the pre-existing figure drift.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
