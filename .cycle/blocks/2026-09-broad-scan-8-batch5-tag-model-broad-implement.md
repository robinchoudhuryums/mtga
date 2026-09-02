---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS8-31 Tag model: `sacrifice` from Sagas/reminder/quoted text, `ramp` via landfall/convoke, `reanimator` bag-of-words, `removal` cue-less classes, `spellslinger` missing "noncreature spell"
- BS8-33 `tribes` payoffs counted token makers; changelings credited to no tribe; self-count
- BS8-32 `strict_upgrades` blind to power/toughness
- BS8-15 Library-search gate read "two"/"black"/"nonlegendary" as types
Files modified: scripts/tag_synergies.py, scripts/deck.py, scripts/check_patterns.py, card-pool.csv + card-pool.build (re-derived via `build_pool.py --all`, 1,372 rows), card-library.csv (41 rows, `tag_synergies --merge`), tests/test_deck.py, tests/test_ingest.py, decks/40-paradox-drive/deck.txt (one figure), dashboard.html, CLAUDE.md, docs/gotchas.md

CHANGES:
BS8-31 | tag_synergies.py `_clean_text`, MECHANIC_RULES, KEYWORD_THEMES | `sacrifice` and `removal` read reminder- and quote-stripped text; `removal` excludes graveyard hate, self-blink and -N/-0; `reanimator` requires one graveyard→battlefield clause (either templating) and sees unearth/embalm/eternalize/encore/disturb/escape; `spellslinger` adds "whenever you cast a noncreature spell"; `landfall`/`convoke` no longer map to `ramp`. Pool: removal 1689→1578 · sacrifice 2117→1551 · ramp 477→298 · reanimator 543→472 · spellslinger 509→620; 1,286 pool rows change a tag.
BS8-33 | deck.py `cmd_tribes` | a type reference inside a "create … token" clause is not a payoff; changelings qualify for every named type; the payoff is not its own qualifier. Deck 69: The Earth King no longer "rewards Bear".
BS8-32 | deck.py `strict_upgrades(…, cand_pt=)` + the `screen` call site | a smaller body on either axis blocks the ★, a bigger body at equal text and cost earns it; `*`/X neither blocks nor grants. Deck 46: Lifecreed Duo is no longer a ★ STRICT UPGRADE of Dazzling Angel.
BS8-15 | deck.py `_TARGET_GATES` lib_type | lookahead covers `cards?`, the number words, the five colours and legendary/token adjectives.
Derived data | `build_pool.py --all` re-derived the pool through the new `tags_for` (network, 91 pages; the stamp's tagger fingerprint defeated the reuse as G-18 says it must); `tag_synergies.py --merge` re-tagged the library (adds only).

TEST RESULTS: passed — full suite green with PYTEST_NO_SKIPS=1 after the pool re-derive; check_all all invariants hold with the G-75 soft warning only. Mid-batch: the first `-N/-0` removal regex still matched "-2/-0" (fixed and pinned); `check_patterns` wanted `_QUOTED_TEXT_RE` registered; the library re-tag moved deck 40's central-theme count 19→20 (re-grounded).
REGRESSION RISKS:
- `tag_synergies --merge` only ADDS tags, so card-library.csv still carries the false `sacrifice` (Sagas, Treasure makers) and `ramp` (landfall) tags on OWNED cards; deck centrality reads the library, so `similar`/`suggest-homes` still see them (deck 71 still shows `sacrifice` shared). The pool — every craft recommender — is corrected. A prune mode is the follow-on.
- 1,286 pool tag changes shift `suggest`/`cuts` fit terms and `wishlist --rank` fit scores for unowned cards; the top-10 wishlist order was unchanged.
- The pool rebuild also refreshed `Legalities`/`Released` from Scryfall (a normal refresh side-effect); INV-01b held.
- `strict_upgrades` now needs the candidate's P/T; the one caller passes it, tests call it with the default (None, None) which keeps text-only behaviour.
INVARIANTS AT RISK: None (INV-03 pool schema intact; INV-01b clean after the rebuild)
NET SCORE: 4 − 0 = 4
(BS8-31 and BS8-33 fire on every `similar`/`suggest`/`tribes` run; BS8-32 on `screen`; BS8-15 latent — counted 4.)

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — pages.yml republishes the dashboard on push to main.

FOLLOW-ON ITEMS:
- `tag_synergies.py --prune` (remove a library tag the current rules no longer produce, unless hand-added — needs a provenance mark, the G-17 shape) so the library's Synergies can shed false tags without `--force`.
- Tag-side residuals measured in the scan and left: `tokens` noncreature-only (26%), `removal` via the deathtouch keyword map (21%, a design choice), `graveyard` reminder-only (19%), `discard` self-discard enablers untagged.
- `check_roles --tags` worklist shrinks with the removal-tag fix; re-baseline on the next `make postedit`.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md K-10 (the `--merge` cannot-remove caveat is now in K-09's note; K-10 should say so too), G-59 (tribes token-clause rule) — cap-limited, long forms written.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
