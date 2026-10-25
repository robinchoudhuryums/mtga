---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: the four tooling holes recorded in `.cycle/ozai-pile-analysis.md` §3 and deck 91's notes
- T3a — `lib.land_production` read colour IDENTITY as production even when the text printed a mana ability (Duskmantle, House of Shadow scored as an untapped U/B dual)
- T2 — hand attack missed the COMPOUND clause ("Target opponent sacrifices …, discards a card, and loses 3 life")
- T4 — a draw offered as a MODE of a recurring phase trigger scored no card advantage (Black Market Connections)
- T1 — firebending's mana lives in stripped reminder text, so a deck of firebenders disclosed no nonland mana
- (T3b, Demolition Field as a basic fetch, was a MISREAD — its full text does let you search; dropped)
Files modified: scripts/lib.py, scripts/deck.py, scripts/check_patterns.py, tests/test_deck_models.py, tests/test_deck.py, CLAUDE.md, docs/gotchas.md, decks/04-quantum-realm/deck.txt, decks/07-earths-mightiest/deck.txt, decks/87-lokis-legion/deck.txt, decks/91-scarab-fist/deck.txt, scripts/role_baseline.txt, dashboard.html, .cycle/ozai-pile-analysis.md

CHANGES:
T3a | scripts/lib.py | identity folds into `free` only when the reminder-stripped text prints NO mana ability (`saw_mana_ability`); a chosen-colour line keeps its printed symbols out of `chosen` (`printed`), the job identity used to do for the Thriving lands. Pool: 87 rows changed (26 lands, 61 nonland), all identity-from-cost corrections; roster source counts moved in 2 of 126 decks (89 B 24→23; 90 −1 B/R/U/W, The World Tree now a G land); 0 tier floors.
T2 | scripts/deck.py | `_HAND_ATTACK_RE` gains `(target|each) (opponent|player)s? [^.;]{0,60}?, (and )?discards?`. Pool +4 (Scarring Memories, Cruel Ultimatum, Dusk Mangler, Smallpox), all true; report-only.
T4 | scripts/deck.py | new Card-advantage pattern: phase trigger → `choose` (not "hasn't been chosen") → a `•` mode that draws; the three phase alternations also accept `first main phase`. Pool +3 (Black Market Connections, Wardens of the Cycle, Mister Hyde); roster card advantage up in 5 decks (4, 7, 69, 87, 91), 0 tier floors moved; 4 decks' prose re-grounded.
T1 | scripts/deck.py, scripts/check_patterns.py | `_FIREBENDING_RE` → `uncounted_mana_sources` row labelled `combat-only` (`_NONLAND_COND_LABEL`); registered in check_patterns. 21 roster decks now disclose it; no count moves.
docs | CLAUDE.md, docs/gotchas.md | G-35 / K-12 short form + long form; figure drift corrected (G-35 87→93 of 126; tier spread A 82 / B 41 / top band 65%, which deck 91's earlier B had moved).

TEST RESULTS: check_all OK (8 soft, none new); full pytest suite passed (-x, 0 failures); 4 new tests.
REGRESSION RISKS: `land_production` is shared by every source count and the nonland disclosure — a land whose real colours were reachable ONLY through identity while its text also has an Add clause would now under-read; the pool-wide diff found none (every changed row was a correction). The Thriving `chosen` guard is pinned by a test.
INVARIANTS AT RISK: None (INV-04 — prose-only deck edits; check_all green).
NET SCORE: 4 production fixes − 0 new failure modes = 4

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds the dashboard on the next push to main (dashboard.html regenerated here by `make postedit`).

FOLLOW-ON ITEMS:
- Firebending is still not RAMP for a deck whose commander keeps unspent mana (Ozai): a commander-aware reading is a taxonomy change, not attempted.
- The figure_drift tier-spread entries moved because deck 91 dropped to B, not because of this batch.

DOCUMENTATION UPDATES NEEDED:
- None beyond what landed (G-35, K-12, long forms).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
