---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch G (2026-10-08 tuning-pass holes) — (1) a fetch with no mana of its own (Hobbit Hole, Evolving Wilds) reads as a tapped land; (2) `consistency`'s cast-on-curve table discloses the board-paid discounts it does not price, reusing `unpriced_discount_cards` (G-85). Fixing (2) exposed and fixed a source-of-truth bug in that helper.
Files modified: scripts/lib.py, scripts/deck.py, scripts/check_patterns.py, CLAUDE.md (G-85 figures), tests/test_lib.py, tests/test_deck.py, .cycle/STATE.md, .cycle/blocks/11-batchG-fetch-taplands-convoke-broad-implement.md

CHANGES:
G-1 | scripts/lib.py | `tapland_kind`: a land matching "search your library for … onto the battlefield tapped" with no mana ability of its own ({T}: Add …) returns "unconditional", or "conditional" when it "untap[s] that land" (Fabled Passage, Elven Passage). The Landscapes, Promising Vein, Shire Terrace and Urza's Cave tap for {C} themselves and stay None. Pool: 11 fetches change (Evolving Wilds, Terramorphic Expanse, Hobbit Hole, the five SNC hideouts, Escape Tunnel, Fabled/Elven Passage). New regexes `_FETCH_TAPPED_RE`, `_OWN_MANA_RE`, `_FETCH_UNTAP_RE`.
  Consumers:
  - `tapland_profile` (consistency's taplands line): 28 of 134 decks now report more tapped lands;
  - `suggest --lands`: Hobbit Hole and Evolving Wilds now print `·tapped`;
  - `wishlist._land_value`: no score change, since it already withheld the untapped premium from any fetch (`if not fetch`).
  The tempo simulation is unchanged: its fetch model checks `fetch_tapped` before `enter`.
  CORRECTION TO THE FILED ITEM: Hobbit Hole's 11.5 in deck 40 was never an untapped-dual score. It is fixing 8.0 + synergy 2.0 (its sacrifice tag) + scarce-colour 1.5, and it is unchanged. The real defect was the missing `·tapped` marker and the tapped-land count.
G-2 | scripts/deck.py | `cmd_consistency` marks a cast-on-curve row ◊ when the card is in `unpriced_discount_cards`, and prints a footnote naming each shown card's discount ("books the PRINTED cost, so the card is often cast earlier than its row says"). Disclosure only; no probability moves. On 10 of 12 sampled decks at least one shown row is marked (deck 47: four).
G-3 | scripts/deck.py | `unpriced_discount_cards` read keywords from `carddata[...]["keywords"]`, a field `load_card_data` never carries. So EVERY keyword-only discount (convoke, affinity, improvise, delve) was invisible to it, while `stats`' ◊ list beside it (which reads `load_keywords()`) named the same cards: the two surfaces its own docstring says "cannot disagree" disagreed. It now reads `load_keywords()` (front-face aliased), and a carddata entry that carries its own keywords still wins (test fixtures). Roster: 31 of 134 decks' unpriced counts rose. The G-85 disclosure in `stats`/`tier` (floor 3) now fires on 27 of the 68 decks that print an effective figure (was 24); p75 is still 3, so the floor stands. CLAUDE.md G-85's two figures updated (max 11 → 12; floor-of-1 rate 83% → 93%; 24 → 27 of 68, 35% → 40%); figure_drift caught it.
G-4 | scripts/check_patterns.py | the three new lib patterns registered with the tapland family (the gate hard-failed them).
G-5 | tests | `test_lib.TestFetchesWithNoManaOfTheirOwnReadTapped` (Evolving Wilds, Hobbit Hole unconditional; Fabled Passage conditional; a Landscape None) and `test_deck.TestConsistencyDisclosesUnpricedDiscounts`. The latter runs the real CLI on a scratch Winnowing deck and asserts the ◊ row and the convoke footnote. It was the test that exposed G-3: the marker could not appear while the helper missed keywords.

TEST RESULTS: full pytest suite passed; check_all OK with 5 soft (the G-85 figure drift resolved by the CLAUDE.md update).
REGRESSION RISKS: `tapland_kind` returns a kind for 11 lands that read None before. Every consumer was checked: the scoring path already excluded fetches, and the tempo simulation checks the fetch first. The G-85 disclosure fires on 3 more decks.
INVARIANTS AT RISK: None.
NET SCORE: 2 production fixes (G-3 was live in `stats`/`tier` on 31 decks; G-1's marker and tapped-land count were wrong on 28 decks) − 0 new failure modes = 2.

OPERATOR ACTIONS / DEPLOY:
None
Deploy: Presentation — the dashboard reads `tapland_profile` and `unpriced_discount_cards` through the deck model, so the next Pages build (on merge to main) picks them up; no separate step.

FOLLOW-ON ITEMS:
- The ◊ footnote prints on most decks with a marked row. It is a per-row fact rather than a deck-level warning, so the G-07 saturation rule was not applied; revisit if it reads as noise.
- G-36 (consistency) and G-37 (suggest --lands) prose does not yet mention fetch lands reading tapped or the ◊ marker.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-35/G-36/G-37: the fetch-tapped reading and the ◊ cast-on-curve marker (word caps permitting); docs/gotchas.md G-85 long form (the keyword-source bug and the re-measure); README consistency paragraph.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
