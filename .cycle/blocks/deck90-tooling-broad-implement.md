---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- T1: X-scaled drain/lifegain ("each opponent loses X life and you gain X life") scored no role (Sanctum of Stone Fangs)
- T2: "Lands you control are every basic land type" fixer scored no role (Leyline of the Guildpact); new every-land-a-five-colour-source disclosure in `consistency`
- T3: hand attack (opponent discards / exiles from hand) added as a REPORT-ONLY line (stats, tier, quality) — never a tier_band term
- T4: Seek (Alchemy) counted as card advantage; a seek that puts the card onto the battlefield routed to Ramp / fixing instead
Files modified: scripts/deck.py, scripts/check_patterns.py, tests/test_deck.py, decks/88-full-throttle/deck.txt, decks/90-spirit-world/deck.txt, scripts/role_baseline.txt, dashboard.html

CHANGES:
T1 | scripts/deck.py | Burn/drain `loses (?:\d|x life)`; Lifegain `you gain x life`. The hole was the X, not the trigger wording first suspected (Northern Air Temple only matched through its second "loses 1 life" clause).
T2 | scripts/deck.py | Ramp/fixing `(?:lands? you control|enchanted land) (?:are|is) every basic land type` (the "gain/have all basic land types" twin never matched "are every"); `_LAND_RAINBOW_RE` + `land_rainbow_enablers()` + an ⓘ line in `consistency` naming the nonland permanents (instants/sorceries excluded) that make every land any colour. Disclosure only — no figure moves.
T3 | scripts/deck.py, scripts/check_patterns.py | `_HAND_ATTACK_RE` + `hand_attack_effects()`; `role_tally` "hand_attack"; `deck_quality_vector` "hand_attack"; printed in `stats`, `quality` and the `tier` vector line. Both new regexes registered in check_patterns (norm corpus).
T4 | scripts/deck.py | Card advantage `\bseeks? (?:a|an|one|…)\b(?![^.]{0,60}?onto the battlefield)`; Ramp/fixing `seeks? an? (?:basic )?land card[^.]{0,40}?onto the battlefield`.
(prose) | decks/88-full-throttle/deck.txt | tier rationale card advantage 8 -> 9 (Emperor Apatzec's seek now counts); decks/90-spirit-world/deck.txt notes re-grounded and a stale `#: protect:` entry (Crescent Island Temple) pruned.

ROSTER MEASUREMENT (before/after, 125 decks, 16,078 pool cards):
pool roles gained: Card advantage 94, Lifegain 42, Burn/drain 22, Ramp/fixing 11; lost: none.
interaction changed in 0 decks; card advantage in 2 (88: 8->9, 90: 11->12); tier floors moved: 0.
hand attack: 14 of 127 decks >0 (p50 0, p90 1, max 19 = deck 70); 236 pool cards, 15-card sample hand-checked all genuine.

TEST RESULTS: passed — 2217 passed (full suite); check_all exit 0, all invariants hold; check_patterns 400 patterns live.
REGRESSION RISKS: Seek is new to card advantage, which feeds tier_band — measured: 0 floors moved. Hand attack and the rainbow line are new keys/lines only; tier_band ignores them (pinned by a test).
INVARIANTS AT RISK: None
NET SCORE: 4 production fixes − 0 new failure modes = 4

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — pages.yml rebuilds dashboard.html on push to main (dashboard rebuilt and committed here).

FOLLOW-ON ITEMS:
- Hand attack stays report-only; whether discard should count as interaction is an owner call after a roster measurement (14 decks carry any).
- Empowered Jace tokens' "−3: Draw a card" lives in reminder text, which the role reader strips by design — still uncounted.
- `suggest --lands` scores Plaza of Harmony (Gate-only), Mirrodin's Core and Aether Hub (counter/energy-gated) as full five-colour lands.
- card.py raises BrokenPipeError when piped into `grep -m1` (read-only, harmless).
- deck 89's notes still call Izoni and Zopandrel token-only sacrificers (open since 2026-10-23).
- check_all figure drift: tier-floor spread / roster-walked counts moved with deck 90's addition (A 81->82, top band 65->66%, G-86/G-35 roster 124->125, G-35 nonland-source decks 85->86).

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md K-12 (the three pattern fixes and seek), G-25 (hand attack as the tempo line's sibling), G-35 (the every-land-a-five-colour-source disclosure), G-67 (hand attack moved from a silent taxonomy hole to a reported line), plus the figure-drift numbers above; docs/gotchas.md long forms to match.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
