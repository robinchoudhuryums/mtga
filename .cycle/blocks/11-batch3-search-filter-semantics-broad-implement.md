---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS11-39 pool.py / query.py `--type` was a substring match ("orc" in Sorcery, "ant" in Instant)
- BS11-34 wishlist `--target` / `--set` were substring matches that scoped --rank/--budget to the wrong decks
- BS11-41 card.py and the gallery read the stale LIBRARY Synergies first; plus an agreement leg — which found the same bug inside the model (load_card_meta) for front-named DFC rows, fixed here
- BS11-54 gallery "Top synergies" chips ran a free-text search, so a chip's count and the cards shown disagreed
Files modified: scripts/lib.py, scripts/pool.py, scripts/query.py, scripts/wishlist.py, scripts/card.py, scripts/build_gallery.py, scripts/deck.py, scripts/check_agreement.py, scripts/check_dfc.py, gallery.html, dashboard.html, tests/test_query_pool.py, tests/test_wishlist.py, tests/test_templates.py, tests/test_deck_models.py

CHANGES:
BS11-39 | lib.py, pool.py, query.py | new lib.type_matches(type_line, needle): whole-word / whole-phrase, case-insensitive; both `--type` filters use it. Live: `pool.py --type Orc --count` 1,938 → 73; `--type Ant` 3,845 → 0. +3 tests.
BS11-34 | wishlist.py | `--target` is a token match on deck ids (split on `;`/`,`, zero-padded ids normalised like deck._norm_deck_id); `--set` is exact; `--type` uses lib.type_matches. `--note` stays a substring search on purpose (free text). Live: `--target 6` 20 → 7 rows. +3 tests.
BS11-41 | card.py, build_gallery.py, check_agreement.py, check_dfc.py, deck.py | card.synergy_cell(): pool first, library on a blank pool cell (load_card_meta's rule); build_gallery.load_pool_tags() feeds build_cards the same way (registered in check_dfc's _ALIASED_LOADERS). New agreement pair `_agree_card_synergies` (card.py display vs the model) — on its first run it found the MODEL wrong too: load_card_meta's pool-first pass matched exact names only, so 10 owned cards stored under a DFC/split FRONT name (Oko, Norman Osborn, Push, The Rise of Sozin…) kept stale library tags, plus 18 order-only differences. A front-face fallback (exact name wins, G-63) fixes it; 8 roster decks run one of the corrected cards (14, 34, 45, 51, 52, 54, 55, 62). +3 tests.
BS11-54 | build_gallery.py | a chip writes `tag:<name>`, and the search treats `tag:` as an EXACT tag-token filter (the thing the chip's count counts); free text is unchanged; the placeholder documents it. +1 Node-run test.

TEST RESULTS: passed — `check_all` all invariants hold (model agreement now 10 questions, OK); full pytest suite exit 0 after registering the new gallery loader with check_dfc (its completeness scan caught it, as designed). Gallery and dashboard rebuilt.
REGRESSION RISKS:
- `--type` no longer matches word fragments: `--type Elf` still matches "Elf", but `--type El` no longer matches "Elf" — prefix searching via --type is gone (use --text or --regex).
- `wishlist --set M2` no longer matches M21; `--target` no longer matches a fragment of a label ("concept" no longer matches "concept: Mardu" — pass the whole label).
- The model's tags changed for 10 owned cards, so suggest / cuts / centrality can shift slightly in the 8 decks that run them (the direction is the K-09 correction).
INVARIANTS AT RISK: None.
NET SCORE: 1 − 0 = 1 (BS11-41 fired: card.py is the mandated pre-grading read and showed stale tags on 216 owned cards, and the model scored 10 cards in 8 decks on stale tags; BS11-39/34/54 not known to have fired this month)

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Presentation — pages.yml rebuilds the dashboard on the next push to main (committed dashboard.html and gallery.html rebuilt here).

FOLLOW-ON ITEMS:
- query.py `--set` and `--name`/`--text` remain substring matches (names and text are reasonable as substring; `--set` is not — same shape as BS11-34, not in this batch's list).
- Gallery chips are still split by tag CASE (`Equipment` vs `equipment`) — BS11-78, Batch 4.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md Key Design Decisions (Color(s) parsing bullet): `--type` filters route through lib.type_matches, the type-axis twin of color_matches.
- CLAUDE.md K-09: card.py and the gallery read pool-first too; load_card_meta's correction now also reaches front-named DFC rows; check_agreement holds card.py to the model (10 questions).
- README: pool.py/query.py `--type` is whole-word; wishlist `--target` is exact per deck id and `--set` exact; gallery `tag:` search.
- CLAUDE.md C-01/check_agreement mentions of "nine" questions, if any, now ten.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
