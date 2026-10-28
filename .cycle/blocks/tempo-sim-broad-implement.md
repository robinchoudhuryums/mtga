---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: TEMPO-1 — simulate one land a turn and tapped lands (`consistency --tempo`); validated on decks 87, 92, 93 (Dragonskull Summit placement)
Files modified: scripts/deck.py, scripts/check_patterns.py, tests/test_tempo_sim.py (new)

CHANGES:
TEMPO-1 | scripts/deck.py | sim_land_model (land enter kind + production from lib.tapland_kind / land_production: untapped, tapped, shock, fast, slow, early (Starting Town), check (type- or basic-gated), reveal (snarl), board; Verge gates; fetches), _sim_enters_untapped, _sim_mana_masks, _sim_payable (Hall's condition — one land makes one mana), simulate_tempo (paired: each shuffle played honouring enter clauses and with every land untapped; each target turn played toward that turn), tempo_cast_rows, _print_tempo_section; `consistency --tempo [--games N]`. Report-only.
TEMPO-1 | scripts/check_patterns.py | registered the five new land-text regexes in the live-corpus check (the gate refused them unregistered).
TEMPO-1 | tests/test_tempo_sim.py | 13 tests on real oracle text: enter kinds, Verge gating, fetch, checkland/fast/slow/snarl conditions, Hall payability, all-untapped deck costs nothing, taplands cost tempo, untapped land drops match the closed form within 3 points, determinism.

VALIDATION: untapped-mode "T lands by turn T" matches the closed form (deck 94: 85.5/69.1/49.5 vs 85.6/69.6/51.7 for T2–T4; the T4 gap is fetch thinning). Decks 87/92/93: tapped lands cost 3.8 / 3.7 / 3.0 points of on-curve chance per card. Dragonskull Summit moves any of the three by ≤0.4 points: replacing a basic gains colour access but loses ~0.5 points of T2 mana (it can enter tapped before a Swamp/Mountain is out); replacing a tapland gains ~0.3 points of untapped mana on T2–T5. Best by mean on-curve: 92 −Swamp (48.2 vs 47.8), 93 −Swamp/−Mountain (49.4 vs 49.0), 87 −Temple of Malice (49.1 vs 48.9).

TEST RESULTS: check_all — all invariants hold (after registering the regexes; first run failed check_patterns' completeness gate, caused by this change, fixed). Full pytest suite passed.
REGRESSION RISKS: None for existing output — `consistency` without --tempo is unchanged; the new code is reached only through the flag. Runtime ~2 s per deck at 4000 games.
INVARIANTS AT RISK: None (read-only; no data or deck file written).
NET SCORE: 1 − 0 = 1 (production: the Summit decision this month could not be measured at all; no new failure mode found)

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — not part of the published dashboard

FOLLOW-ON ITEMS:
- Swap preview: print a before/after tempo line for a land swap (`swap --tempo`), so the comparison needs no scratch copy.
- Mulligans and card draw are not modelled (same as the hypergeometric table); a shockland's life cost is not tracked; board-state enter conditions (13 life, planeswalker, Equipment) are scored tapped.
- Colours behind an extra mana cost ("{1},{T}: any colour") are excluded on curve; Thriving lands' chosen colour is read as any of the allowed ones.
- The commander stays in the simulated library, matching the hypergeometric table's N.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-36 (consistency): mention `--tempo` and that it is report-only (word cap is tight — may need the long form in docs/gotchas.md).
- docs/systems-map.md: the land-swap reconciliation point now has a measuring tool.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
