---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- FO-1 | `card-mana.csv` stored only the FRONT cost of a MODAL double-faced card, so the
  back face — a face you may cast from hand — was invisible everywhere
- FO-2 | `build_gallery.py` carried its own `_primary_type` with the identical back-face
  bug P7 fixed in `deck.py`
- FO-3 | (NOT implemented — deck construction, needs the owner) whether decks 51 / 51a add
  a 25th land now that keepable reads 84.4%

Files modified:
- scripts/build_mana.py
- scripts/lib.py
- scripts/deck.py
- scripts/build_gallery.py
- tests/test_build_mana.py
- tests/test_lib.py
- card-mana.csv (49 rows re-priced)
- gallery.html, image-manifest.json (rebuilt)

CHANGES:
FO-1 | scripts/build_mana.py, card-mana.csv | `_front_mana` became `_castable_cost` and
   now keeps EVERY face you may cast, in Scryfall's own `A // B` convention. Scryfall
   gives a split / Room / Adventure card both halves in the top-level `mana_cost`, but
   leaves a modal DFC's top-level cost empty with a real cost on both faces — so face 0
   was all that survived. Bruce Banner read as a plain `{U}` one-drop with nothing
   recording that `{2}{R}{R}{G}{G}` The Incredible Hulk is castable from the same card.
   The test is the SHAPE of the faces, not a layout string: a card with a real cost on
   more than one face is one you may cast either way. A TRANSFORM DFC is the control and
   still keeps ONE cost — Scryfall writes its back face's `mana_cost` as `""`.
   Re-priced via `build_mana.py --pool --refetch`: 49 rows changed, 0 added, 0 removed,
   and EVERY change is the same class (gained a back-face cost). No Mana Value or
   Keywords moved, so no curve, pip count or castability read changed — `front_face_cost`
   takes the head of the string exactly as before. What changed is that `card.py` now
   prints `{U} // {2}{R}{R}{G}{G} (MV 1)` instead of `{U} (MV 1)`.
FO-1b | scripts/build_mana.py | the front-face retry (for names `/cards/collection` will
   not match by FULL name) is now BATCHED through that same endpoint, which resolves a
   two-faced card by its front name just as `/cards/named` does. It was one GET per name;
   on the ~700 two-faced names that trips Scryfall's rate limiter and the client's own
   backoff — measured: 432 such lookups did not finish in ten minutes, while the same set
   batched is nine requests. This is what made the `--refetch` migration affordable. The
   strict "the resolved card must BE the one asked for" check is preserved verbatim — a
   bare front name can name a DIFFERENT card ("Life" is also a card).
FO-2 | scripts/lib.py, scripts/deck.py, scripts/build_gallery.py | `_primary_type` moved
   to `lib.primary_type`; deck.py binds `_primary_type = primary_type` (~35 call sites,
   plus build_dashboard.py and the tests, reach for the private name) and build_gallery.py
   imports it under the same alias, deleting its copy. The gallery's committed type
   breakdown was wrong: Creature 1071 → 1063, Enchantment 137 → 146, Sorcery 196 → 198,
   Artifact 110 → 112, Land 108 → 106. The Enchantment shift is the transforming Sagas
   (`Enchantment — Saga // Enchantment Creature`), which the whole-string scan called
   creatures.
FO-3 | not implemented | Measured instead: at 60 cards, keepable is 82.5% at 23 lands,
   84.4% at 24, 86.0% at 25, 87.4% at 26; the 25th land buys +1.6pp keepable and −2.1pp
   screw for +0.4pp flood. Recommendation is to take it in deck 51 (avg MV 4.03, real top
   end) and leave 51a at 24 (avg MV 3.14). NOT APPLIED: a deck edit is the owner's call
   under the standing "propose, don't apply until confirmed" rule.

TEST RESULTS: 767 passed (was 755; +12 across TestModalDfcKeepsBothCosts,
TestFrontFaceRetryIsBatched and TestPrimaryTypeHasOneDefinition). `check_all.py` — all
invariants hold. All ten gates OK (check_patterns, check_commands, check_agreement,
check_docs, check_colors, check_dfc, check_suggest, check_rankings, check_tier,
check_engines). `deck.py --help` and `build_mana.py --help` clean (G-55).
Regression scenarios walked: #3 refresh derived data — PASS (`make refresh` end-to-end,
all invariants hold). #2 analyze a deck — PASS (17 commands on deck 51; `deck.py check`
exits 1 on 19 unowned cards, which is the documented WIP-deck signal, G-12, not a
failure). #1 ingest a batch — NOT APPLICABLE, nothing was ingested. #4–#8 NOT APPLICABLE,
they need a browser and no template or app.py code was touched.

REGRESSION RISKS:
- FO-1's joined string makes a modal DFC indistinguishable from a SPLIT card in
  `card-mana.csv`. That is deliberate — both mean "choose a face as you cast it", and
  every reader takes the front — but it means the file can now tell transform from modal
  and cannot tell modal from split. No reader asks that question today.
- FO-1 does NOT change G-02's residual: a deck that plays a two-half card mainly for its
  BACK half still reads cheaper than it plays. Valki read MV 2 before this change and
  reads MV 2 after; the Mana Value column was untouched.
- FO-1b widens a Scryfall failure from one name to a 75-name chunk. The chunk still ends
  in the existing blank-row-plus-WARN path, and `ScryfallUnavailable` still leaves the
  file unchanged (pinned by `test_a_scryfall_outage_leaves_the_file_unchanged`).
- FO-2 changes no behaviour in deck.py — it is the same function object under the same
  name. build_gallery.py's answer changes, which is the fix.
- The four `card-mana.csv` writers that hardcode the 4-column header (sheets_sync.py,
  import_collection.py, reconcile_crafts.py, app.py) were checked: no schema change was
  made, so none needed touching. `reconcile_crafts.py` copies a pool row's Mana Cost to
  the library's front-name row, which now propagates the two-face cost correctly.

INVARIANTS AT RISK: None. INV-02 and INV-03 both re-verified by `check_all` after the
re-price; card-mana.csv kept its exact 4 columns and its exact 15,970 rows.

NET SCORE: 2 production fixes − 0 new failure modes = 2
(a) Fired this month? FO-1 YES — it is why both faces of Bruce Banner and Norman Osborn
    were called permanently unreachable in chat, an answer the owner corrected.
    FO-2 YES — the committed gallery.html has shipped a wrong type breakdown for as long
    as the second copy existed. (b) New failure modes: none. The modal-vs-split ambiguity
    above is a legibility limit of the encoding, not a wrong answer at any call site.

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push. gallery.html is committed and was
rebuilt here; dashboard.html is rebuilt by `.github/workflows/pages.yml` on push to main.

FOLLOW-ON ITEMS:
- FO-3 above is still open and is a deck decision, not a code one.
- `build_dashboard.py` reaches into `deckmod._primary_type` (a private name in another
  module) rather than importing `lib.primary_type`. Harmless today, and out of scope.
- The pool's `Power`/`Toughness` for a two-faced card is stored the same merged way costs
  were. Not investigated; noted because it is the same shape as this whole class.

DOCUMENTATION UPDATES NEEDED:
- The front-face-vs-metadata class now has FIVE members across two sessions — COST (G-02,
  plus this session's modal-DFC half), COLOR (G-58/P6), TYPE (P7 + FO-2), NAME (P8). Only
  COST and COLOR are written up. A combined gotcha is overdue; `/sync-docs` is next.
- `card-mana.csv`'s documented meaning changes with FO-1: the Mana Cost cell is now
  "every castable face", not "the front face". CLAUDE.md and README describe this file.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
