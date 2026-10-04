---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS11-75 — tribal payoff tags invented types (Elve, Heroe, Allie, Werewolve, Dwarve) and junk capitals (Equipped, Nontoken, Then); real tribes went untagged on their payoffs
- BS11-76 — `blink` fired on transform returns and earthbend reminder text (~37% false)
- BS11-77 — `graveyard` was minted by incidental reminders (crime, Role tokens, madness)
- BS11-78 — case-duplicate tags (Equipment/equipment ×8 themes) double-counted theme weight; library and pool disagreed on case
- BS11-79 — `burn` tagged cards whose only damage is to their own controller (Talismans, painlands, Ancient Tomb)

Files modified: scripts/tag_synergies.py, scripts/check_patterns.py, tests/test_ingest.py,
tests/test_deck_models.py, card-pool.csv + card-pool.build (rebuilt), card-library.csv
(--merge + junk-tag cleanup), card-mana.csv (row reorder only), gallery.html, dashboard.html,
decks/50-hoofprint/50a-strata.txt (one stale figure)

CHANGES:
BS11-75 | tag_synergies.py | `_CREATURE_TYPES` / `_OTHER_SUBTYPES` (Scryfall catalogs, single-word, fetched 2026-10-02) + `_resolve_tribe`, which tries the word then singular candidates (ies→y, ves→f/fe, es, s) against the real list. `_TRIBAL_PAYOFF_RES` now capture the whole word. Pool: Elve 19→0, Werewolve 8→0, Heroe 8→0, Allie 6→0, Dwarve 4→0, Equipped/Nontoken/Then →0; Elf +3, Ally +3, Werewolf +3, Hero +2. 20 library rows had the junk tags removed explicitly, since --merge cannot remove a tag.
BS11-76 | tag_synergies.py | `_blink`: reminder-stripped (quotes kept), and a return "to the battlefield transformed" does not count. Pool blink 189→130; gains real flashback blinks (Momentary Blink, Daydream).
BS11-77 | tag_synergies.py | `graveyard` reads text with the INCIDENTAL reminders removed (`_GY_INCIDENTAL_REMINDER_RE`: crime, "another Role on it", madness cost). A blanket reminder strip was measured and rejected: it dropped 116 cards, ~40 real (descend, retrace, explore, collect evidence). Pool graveyard 2946→2880.
BS11-78 | tag_synergies.py | `canonical_tags` — one spelling per theme (the lowercase theme vocabulary wins over a Title-case type tag), case-insensitive dedupe, applied at the end of `tags_for` and to `--merge`'s kept tags so library and pool agree. Pool: Equipment 464→0 / equipment 395→477 (and Aura, Saga, Vehicle, Planeswalker, Food, Clue, Treasure the same way).
BS11-79 | tag_synergies.py | `_burn`: "deals N damage to you" is not burn outside quotes; inside quotes "you" is the recipient of a granted ability (Relic Robber), so it still counts. Pool burn 1151→1115.
(gate) | check_patterns.py | five new patterns registered (four "norm", the reminder filter "raw" since norm strips reminders); `_BURN_QUOTE_RE` excluded as a quote splitter.

TEST RESULTS: passed — full pytest suite green; check_all OK (6 soft, none new except K-09's pool-blank figure 348→350 and the dashboard staleness, both cleared/expected); check_patterns 375 live; 7 new tests in TestScan11TaggerFixes; one old assertion updated (`Vehicle`→`vehicle`).
ROSTER DIFF (114 decks): tier floors moved 0; cuts top-3 changed in 10; cut #1 changed in 1 (deck 37: Bitter Triumph → Super Intelligence); central-theme sets changed in 18; pool tag cells changed 1,773 of 16,047. Deck 50a's `#: tier:` quoted 34 central themes against a live 33 — re-grounded.
REGRESSION RISKS: (1) a tribe not in the embedded catalog gets no payoff tag until the list is updated (silent but honest direction). (2) Lowercasing the type tags changes any HAND-written capitalised tag in the library to the canonical spelling on the next --merge. (3) The graveyard filter is a deny-list of three reminder families; a new incidental reminder will mint the theme again.
INVARIANTS AT RISK: None — INV-03 (pool schema) verified by check_all after the rebuild; pool row count unchanged at 16,047.
NET SCORE: 5 − 0 = 5

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — pages.yml rebuilds the dashboard on push to main (committed dashboard.html already rebuilt).

FOLLOW-ON ITEMS:
- The tribal payoff regexes still require an `s` plural for "X you control", so "Merfolk you control" (irregular plural) is not captured by that template.
- `tag_synergies --merge` still cannot REMOVE a stale library tag in general (K-09); this batch removed only the known invented tribes by hand.
- K-09's pool-blank figure moved 348 → 350 (figure drift, soft).

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md K-09: pool blanks 350; note canonical tag case (BS11-78).
- CLAUDE.md / docs/gotchas.md: a rule entry for the tagger fixes (invented tribes resolved against the real type list; blink/graveyard/burn guards; one spelling per theme) — likely under K-09/K-10 or G-83's sibling note.
- README: gallery `tag:` chips now lowercase for equipment/aura/saga/vehicle/planeswalker.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
