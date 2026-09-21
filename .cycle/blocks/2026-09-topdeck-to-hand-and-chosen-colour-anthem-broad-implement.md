---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
  F1 — `Team pump / anthem` matched "of the chosen TYPE" but not "of the chosen COLOUR"
  F2 — Card advantage had no pattern for the topdeck-to-hand family

Files modified: scripts/deck.py, tests/test_deck.py, scripts/role_baseline.txt,
decks/03-knights-edge/deck.txt, decks/73-dukes-vigil/deck.txt

CHANGES:
F1 | scripts/deck.py | Third anthem pattern's alternation widened from
   `of the chosen type ` to `of the chosen (?:type|colou?r) `. Heraldic Banner and
   Caged Sun scored ZERO roles; both now score Team pump / anthem. The
   family-disagreement shape G-67 says to check first — the author anticipated
   chosen-type and missed chosen-colour. 2 pool cards, 0 decks run either:
   purely DEFENSIVE.

F2 | scripts/deck.py | New Card-advantage pattern
   `look at the top card of your library\..{0,220}?put (?:it|that card) into your hand`.
   25 pool cards. Sidequest: Catch a Fish had scored Ramp/fixing ALONE.

F2 | decks/73-dukes-vigil/deck.txt | Stale `card advantage 1` -> 2, and a
   PRE-EXISTING false claim that the list "meets the A metrics floor exactly"
   corrected (the floor read C before this change, B after). No audit pattern
   prices a floor stated that way, which is why it survived.

F2 | decks/03-knights-edge/deck.txt | Trued up the card-advantage figure in prose
   written earlier the same day (4 -> 5).

THE CORRECTION THAT MATTERS, because the first draft of F2 was WRONG and the
discipline is what caught it: the pattern was first written with a same-sentence
`[^.]{0,80}` span, on the stated theory that the sentence boundary separates card
advantage from ramp. It does not. Risen Reef, Fecund Greenshell, Wickerfolk
Thresher and Parcelbeast all read "if it's a land, put it onto the battlefield.
OTHERWISE / IF YOU DON'T, put it into your hand" — you get the card either way, so
they ARE card advantage, and the tight span silently dropped ten such cards. The
real discriminator is whether the card REACHES YOUR HAND AT ALL; the 8 genuine
negatives (Lantern of Revealing, Raiders' Karve, Mobile Homestead...) never say
"into your hand" anywhere, so the destination clause excludes them with no help
from the span. A regression test asserting the tight theory had already been
written and would have pinned the wrong behaviour permanently. It was rewritten.

ROSTER DIFF (K-12, before/after over all 114 deck files):
  card advantage moved on 3 deck files — 03-knights-edge 1->2 (brawl twin),
  03-knights-edge 4->5, 73-dukes-vigil 1->2
  TIER FLOOR moved on 1 — 73-dukes-vigil C -> B
  Deck 73's claimed B now MATCHES its floor; it had been a live mis-grade.
  Deck 61 was predicted to move and did NOT: `role_tally` skips LANDS by design
  and Bucolic Ranch is a Land. The pre-fix estimate was made by adding +1 to a
  vector rather than asking whether the card is counted at all.
  check_roles baseline: 0 newly acknowledged, 1 stale entry pruned;
  role coverage 1405 -> 1406 of 1884.

TEST RESULTS: check_all "All invariants hold. ✓". Full pytest suite exit 0,
1898 collected (1894 baseline + 4 new). Four new tests in TestClassifyRoles, each
proven load-bearing against a targeted mutant:
  - tightening the span back to `[^.]{0,80}` FAILS the intervening-sentence test
  - widening the destination to "onto the battlefield" FAILS the negative test
(G-67: truncating a regex makes it BROADER, so a positive-only test passes
vacuously — the negative half is the one that constrains.)

REGRESSION RISKS: `classify_roles` feeds `role_tally`, which feeds `tier_band`,
`cuts`, the F10 quality guard and check_all. The roster diff above IS the
blast-radius measurement: 3 deck files, 1 band. Both patterns only ADD roles, so
no card can lose one. The widened `.{0,220}` span is the only place a false
positive could enter; every one of the 25 matches was read individually and all
reach hand. Reminder text is stripped upstream by `_clean_text`, which is why
Search for Azcanta's surveil reminder ("put that card into your graveyard") does
not match.

INVARIANTS AT RISK: None. No CSV writer, schema, deck line or printing touched.
INV-01..04 unaffected; check_all green.

NET SCORE: 2 production fixes − 0 new failure modes = 2
  F1: would it have fired this month? NO — 0 decks run either card. DEFENSIVE.
  F2: YES — deck 73 was graded a band low today.

OPERATOR ACTIONS / DEPLOY: None. | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds the dashboard on
push to main; deck 73's tier pill will move C->B there. No other subsystem has a
Deploy Command.

FOLLOW-ON ITEMS:
- Deck 73's `#: archetype:` carries an unverified "no tap-engine deck exists in
  the roster" claim that the audit flags with `?`. Pre-existing, out of scope.
- `_land_utility` (G-37's sort-key rider) has no category for a land that puts
  counters on the team, so `suggest --needs` ranked Abandoned Air Temple top on
  FIXING value alone while its real value here is a repeatable mass-counter
  ability. Sort-key only — G-37 is explicit it must never become a score term.
- The 8 battlefield-only topdeck cards are ramp and score no Ramp/fixing role
  from this family. Not examined; separate axis.

DOCUMENTATION UPDATES NEEDED:
- G-67 in CLAUDE.md could cite the "fix the CLAUSE, not the window" lesson with
  this case, which is a second instance of it in the opposite direction: here the
  WINDOW was wrongly blamed and the CLAUSE (destination) was doing the work.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
