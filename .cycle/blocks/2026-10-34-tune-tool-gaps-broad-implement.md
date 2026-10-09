---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: deck-34-tune tool gaps #2, #4, #5 (2026-10-09)
- #2 Card-advantage pattern holes: typed/compound cast-from-top permission; multi-chapter Saga draw
- #4 Diligent Zookeeper (zero-role engine) protected in deck 34 via `#: protect:`
- #5 Rationale-audit `no longer` consequence-clause suppression — documented, deliberately not fixed
Files modified: scripts/deck.py, tests/test_deck.py, docs/gotchas.md, CLAUDE.md,
decks/{08,16,19,22,34,50a,57,65,69a,70} deck files (re-grounded figures), scripts/role_baseline.txt,
dashboard.html

CHANGES:
#2 | scripts/deck.py | `_ROLE_PATTERNS["Card advantage"]`: cast-from-top word gap {0,3}→{0,5}
     (Traveling Chocobo, Madame Web, Mystic Forge, Sigarda — exactly 4 new pool matches, all real);
     new line-anchored multi-chapter Saga draw pattern excluding single-chapter draws and
     `you may discard` rummage chapters (6 pool matches, 4 real; the 2 loot/rummage ones stay out).
#2 | tests/test_deck.py | two regression tests; both FAIL against the pre-change deck.py (verified).
#2 | decks ×10 | `#: tier:` card-advantage figures re-grounded (16, 19, 22, 34, 50a, 57, 65, 69a,
     70, 8) + deck 19's `#~ note:`; `--audit-rationale` clean on all.
#2 | docs/gotchas.md | K-12 long form records the change and the roster diff.
#4 | decks/34-zoologist/deck.txt | `#: protect: Diligent Zookeeper` (anchored after `#: archetype:`).
#5 | docs/gotchas.md, CLAUDE.md | G-26 long form + STILL LIVE line: a consequence-clause
     `no longer` hid deck 34's stale Patchwork Banner citation; roster sweep with the cue removed
     surfaced 0 other citations, so the cue list is unchanged.

TEST RESULTS: full pytest suite passed; check_all: all invariants hold (soft warnings pre-existing:
deck 28 flex protection figure, 78-historic-brawl printings, dead searches, castability).
Roster before/after (deck_quality_vector, 117 decks): 14 decks card advantage +1/+2, interaction
unchanged, 0 tier-floor band moves.
REGRESSION RISKS: card_advantage feeds tier_band's sum axis — measured 0 band moves today; a future
pattern overlap could double-count a Saga that also draws via another clause (classify_roles is a
set, so no double count within one card).
INVARIANTS AT RISK: None (INV-04 deck parses re-checked by check_all).
NET SCORE: 2 production fixes (#2 patterns, #4 protect) − 0 new failure modes = 2  (#5 doc only)

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Presentation — pages.yml rebuilds dashboard.html on push to main (committed copy refreshed).

FOLLOW-ON ITEMS:
- #1 (not built): named-type payoffs satisfied by changelings are invisible to suggest/screen
  (Beorn, Spider-Ham, Attuma, Imperious Perfect, Champions, Bartz, Chocobo all tangential/role-player
  in deck 34). G-84's NAMED half; needs a roster measurement before building.
- #3 (not built): `early_drops` counts X spells at X=0 — 96 cards in 62 decks; consistency prices
  X=2. Needs a tier-floor diff (aggro clock) before landing.
- Minor: consistency caps cast-on-curve at T5, so a 7-drop (Verdant Kraken) reads 44%.

DOCUMENTATION UPDATES NEEDED:
- None beyond those made (K-12 / G-26 long forms, G-26 STILL LIVE line).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
