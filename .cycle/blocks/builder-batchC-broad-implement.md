---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch C of .cycle/builder-picks-plan.md — more than two decks, and one
- C1: deck-less pile labels follow the deck count (new builds and add-deck)
- C2: row buttons and chips name a deck by its unique KEY, not its label's first letter
- C3: distinct deck accents when two decks share a colour identity
- C4: past three decks, Bench / Keep out fold into a per-row "⋯" menu
- C5: tests for 1- and 3-deck builds (labels, add-deck transitions, render) and the row buttons / accents under Node
Files modified: scripts/builder.py, scripts/builder_template.html, tests/test_builder.py, tests/test_builder_template.py, .cycle/board/index.html; .cycle/builder-picks-plan.md deleted (all batches landed)

CHANGES:
C1 | scripts/builder.py | `shared_pile_labels(n)`: 1 deck → no shared pile, "Doesn't fit"; 2 → "Either deck", "Fits neither"; 3+ → "More than one deck", "Fits none". `new_build` uses it; `add_deck` moves a label still at the OLD count's default to the new one (a renamed label is kept) and adds the shared pile when a one-deck build gets its second deck. Stored builds are untouched until a deck is added.
C2 | scripts/builder_template.html | `DECKS[k].label[0]` → the deck key `k` in the +/− toggles, the Bench/Keep out buttons, the verdict chip and the "needs a cut" chip (three Glarb decks read +G +G2 +G3, not +G +G +G). The two Sultai keys are T and G, so that board reads the same.
C3 | scripts/builder_template.html | `colourRank` (a deck's colours, most-produced first) and `assignColours` (in build order, each deck takes its best colour no earlier deck took; its own top when all are taken) replace the per-deck `mainColour` accent. Sultai unchanged (G, U).
C4 | scripts/builder_template.html | With more than three decks the deck toggles sit two to a row and Bench / Keep out live in a `<details class="qmore">` menu ("⋯ N" counts the set marks); the row click handler ignores the menu so opening it does not open the note.
C5 | tests/test_builder.py, tests/test_builder_template.py | TestDeckCount: labels for 1/2/3 decks, three copies of one deck get three keys, add-deck 1→2→3 with a renamed label kept, 1- and 3-deck pages render with the right decks and piles. TestManyDecks (Node): quick() for 3 and 5 decks — key letters, Bench/Keep out per deck on a shared pile, the menu past three — and assignColours. TestAddDeck updated: 1→2 decks now adds the shared pile (it encoded the old behaviour).

TEST RESULTS: full pytest suite passed (rc=0). check_all OK, 5 soft. Browser: a 3-deck scratch build (Glarb, Thranduil, Szarel) shows +G +T +S over two rows of per-deck Bench/Keep out; a 5-deck build shows the toggles two to a row and the ⋯ menu, whose Bench marks a deck and reads "⋯ 1"; no page errors. The walk found the row handler eating the menu click (it opened the note) — fixed.
REGRESSION RISKS: (1) A build with three decks of near-identical colours now gets accents that are not each deck's top colour. (2) add-deck now inserts a shared pile when a one-deck build gets a second deck — a pile the owner may not have expected, though it is empty.
INVARIANTS AT RISK: None — builds/ and the page only.
NET SCORE: 0 production fixes − 0 new failure modes = 0 (multi-deck capability; the Sultai board is unchanged).

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation: `.github/workflows/pages.yml` publishes on the next merge to main; the claude.ai board is republished (artifact v26).

(Not complete in production until blocking operator actions are done AND
the deploy step is confirmed.)

FOLLOW-ON ITEMS:
- PRE-EXISTING, found while testing C: `new_build` gives a deck whose label starts with B the key "B", the same key as the shared pile — two piles keyed "B". A deck-key/pile-key collision guard (or reserved keys B/N) belongs in new_build; add_deck already refuses a key a pile uses.
- Scenario 25 could name the Decision filter, bulk mark, move request, cut list and inspect slot (sync-docs).
- CLAUDE.md G-04 could name `deck.py flex --add` as the writer for a flex line (sync-docs).

DOCUMENTATION UPDATES NEEDED:
- None beyond the sync-docs items above.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
