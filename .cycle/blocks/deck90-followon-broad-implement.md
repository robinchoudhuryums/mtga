---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (the FOLLOW-ON ITEMS of deck90-tooling-broad-implement.md):
- F1: hand attack as interaction — MEASURED, not changed (owner's call)
- F2: empowered Jace tokens' "−3: Draw a card" (reminder text) now card advantage when the empower is 3+ or repeatable
- F3: `suggest --lands` read Plaza of Harmony (Gate-bounded), Mirrodin's Core (charge counter) and Aether Hub (energy) as free five-colour lands
- F4: card.py printed a BrokenPipeError traceback when its reader closed the pipe
- F5: deck 89's notes called Izoni and Zopandrel token-only sacrificers
- F6: CLAUDE.md figure drift from deck 90's addition
Files modified: scripts/deck.py, scripts/lib.py, scripts/card.py, scripts/check_patterns.py, tests/test_deck.py, tests/test_lib.py, tests/test_card.py, CLAUDE.md, decks/22-bloodbending/deck.txt, decks/24-eternal-flame/deck.txt, decks/51-unlocked/deck.txt, decks/70-empty-threats/deck.txt, decks/78-team-avatar/78-historic-brawl-team-avatar.txt, decks/82-fatehold-foresight/deck.txt, decks/89-genesis-cycle/deck.txt, decks/90-spirit-world/deck.txt, scripts/role_baseline.txt, dashboard.html

CHANGES:
F1 | (measurement only) | Counting a hand-attack card with no interaction role as interaction would raise interaction in 9 of 125 decks and move 0 tier floors. Left report-only.
F2 | scripts/deck.py | Card advantage: `empower jace (?:[3-9]|\d{2})`, `(?:whenever|landfall)…empower jace`, and an activated-ability line (`^…:…empower jace`). A one-off empower 1–2 stays uncounted. +22 pool cards; card advantage up in 9 decks (22 7→8, 24 12→14, 51 10→11, 70 6→7, 78-historic-brawl 6→7, 80 3→7, 82 12→15, 89 12→13, 90 12→16); 0 tier floors moved. Six decks' prose re-grounded to the live figure.
F3 | scripts/lib.py, scripts/check_patterns.py | `_EXTRA_RESOURCE_COST_RE` ({E}, "remove a … counter from") makes the colour `conditional`; `_GATE_ONLY_RE` ("a Gate you control could produce") files it under `board`. Reflecting Pool and pay-life lands unchanged. 0 roster decks' colour sources moved (none runs these lands); the three drop out of deck 90's top `suggest --lands` picks.
F4 | scripts/card.py, tests/test_card.py | BrokenPipeError in `__main__` exits quietly (stdout to devnull first). The new test fails without the fix and passes with it.
F5 | decks/89-genesis-cycle/deck.txt | Only Persuasive Interrogators (Clues) and Slimefoot and Squee (Saprolings) sacrifice tokens alone; Izoni and Zopandrel sacrifice nontoken creatures, so each is a Szarel trigger.
F6 | CLAUDE.md | tier-floor spread A 81→82 and top band 65→66%; G-35 86 of 125 decks; G-86 n=125, 74 of 125. check_all figure drift now clean.

TEST RESULTS: passed — 2222 passed (full suite); check_all exit 0, all invariants hold, no figure drift; check_patterns live.
REGRESSION RISKS: F2 widens card advantage, a tier_band input — measured 0 floors moved. F3 narrows land_production, which feeds every source count — measured 0 decks moved.
INVARIANTS AT RISK: None
NET SCORE: 5 production fixes − 0 new failure modes = 5 (F1 was a measurement)

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — pages.yml rebuilds dashboard.html on push to main (rebuilt and committed here).

FOLLOW-ON ITEMS:
- Mirrex (entered-this-turn), Spire of Industry (needs an artifact) and Gemstone Caverns (luck counter) still score as free rainbow lands: the board-state gates G-87 already lists as unmodelled.
- Hand attack: the measurement is in; whether it should count toward the floor remains the owner's decision.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md K-12 (empower Jace, plus the earlier tooling batch's X-drain / every-basic-type / seek), G-25 and G-67 (hand-attack line and its measurement: 9 decks, 0 floors), G-35/G-37 (energy, counter and Gate-bounded lands; the every-land disclosure); docs/gotchas.md long forms to match.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
