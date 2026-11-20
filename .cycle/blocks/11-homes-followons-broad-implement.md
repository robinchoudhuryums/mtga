---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- H1 — Rainbow-fixer overlay priced New Planet token makers (Gaseous Anomaly) as if the land tapped for any colour.
- H2 — Type-scoped doublers (Harmonic Prodigy, Splinter, Katara…) counted against the whole deck (G-33 known gap).
- H3 — 21 Star Trek subtypes missing from the tagger vocabulary (the K-17 radar's whole list).
- H4 — Unheld printings: deck 96 Thryx, deck 98 Danitha, 7 wishlist rows.
- H5 — Stale `#~ note:` figures in decks 24, 28, 50.
- H6 — STATE.md listed items the 2026-11-05 batch had already closed.
Files modified: scripts/deck.py, scripts/tag_synergies.py, scripts/check_patterns.py, tests/test_deck_models.py, decks/24,28,50,96,98, card-wishlist.csv, card-pool.csv/.build, card-mana.csv, gallery.html, dashboard.html, CLAUDE.md, docs/gotchas.md, .cycle/STATE.md

CHANGES:
H1 | scripts/deck.py | `_fixer_rate` takes the larger of card MV and the activation cost on the line that delivers the any-colour mana (`_fixer_activation_mv`; a quoted grant has no cost of its own). Pool diff: exactly 6 cards moved, all New Planet makers. Gaseous Anomaly KEY homes 10 → 2 (both theme matches).
H2 | scripts/deck.py | `doubler_type_scope` (two templatings, every word a real subtype or no scope); `doubler_support(types=)` filters to the tribe plus changelings; `doubler_best` passes it. 7 pool doublers scoped. KEY: Harmonic Prodigy 11 → 2, Katara 8 → 3, Twinflame 9 → 0, Splinter 2 → 1 — every remaining KEY already runs the card. Deck 20 Splinter support 26 → 12 (G-33's figure). `cuts` in 20/24/46/78/103 byte-identical.
H3 | scripts/tag_synergies.py | 20 creature types + Communicator; Ferengi/Hirogen/Aenar invariant plurals. Radar empty; Sela gains `Romulan`. Pool re-derived by `make refresh` (the refetch also pulled SDS: +10 cards, 4 newest-printing moves).
H4 | decks 96/98 via `resolve --fix --apply`; wishlist via `write_wishlist` | J25 printings (Pinnacle Starcage EOE 33 → 27 was a real typo). Both soft sweeps now empty.
H5 | decks 24/28/50 comments | 24: 16 → 17 R sources; 28 and 50: past-tense cue on figures that were true when written. Sweep empty.
H6 | .cycle/STATE.md | six bullets marked closed with the block that closed them; this batch's open items added.

TEST RESULTS: pytest full suite passed; check_all all invariants hold; check_patterns 441 live; check_docs OK.
REGRESSION RISKS: scoped doublers now read 12–19 against the `triggers` floor of 20 (calibrated on unscoped counts), so their doubler lane no longer clears the floor in their own decks; `cuts` unchanged, suggest-homes KEY for them now rests on theme.
INVARIANTS AT RISK: None (INV-04 re-checked by resolve --fix; INV-03 pool schema unchanged).
NET SCORE: 3 − 1 = 2

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — pages.yml rebuilds dashboard.html on merge to main.

FOLLOW-ON ITEMS:
- Re-derive the `triggers` doubler floor for TYPE-scoped doublers if a tribal doubler's home reads wrong.
- Needs lane ranks by NEED only (Sheoldred's Edict → 98/87/92) — owner call.
- Blink value of enters-with feeders is unread (Deanna/Mikaeus → 95) — owner call.
- Builder staleness: sultai 394, trek-borg 70 reasons; Sultai board at the 511-file cap.
- The SDS refetch moved Captain Sisay / Mogis / Prosper / Stella Lee's newest printing; no deck line is affected today (no unverified-printing warning).

DOCUMENTATION UPDATES NEEDED:
- None beyond what landed (G-33 rule + long form, G-31 long-form residual closed).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
