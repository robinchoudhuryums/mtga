---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- B1 — Steal Auras scored no interaction: "You control enchanted creature/permanent" (Control Magic, Confiscate, Lay Claim, Kitnap, In Bolas's Clutches, Enthralling Hold, Grafted Identity, Coerced to Kill) now `Removal (spot)`.
- B2 — Copy effects scored no role: token copies of a named thing, "enter as a copy of", "becomes a copy of" now `Payoff / engine` (~130 pool cards; self-copy "a copy of it" excluded).
- B3 — Report-only TEMPO line (bounce / stun / one-turn tap on cards with no interaction role) in `role_tally`, the quality vector, `stats`, `tier` and `quality`; never read by `tier_band`.
- B4 — Single-target BOUNCE moved out of `Removal (spot)` (and out of the `_INT_CUES` under-read net) into the tempo line, per the owner's call; mass bounce stays a Sweeper.
Files modified: scripts/deck.py, scripts/check_patterns.py, scripts/check_roles.py, scripts/role_baseline.txt, tests/test_deck.py, CLAUDE.md, docs/gotchas.md, decks/{18,22,32,34,40a,47,48,51,51a,54,65,67,71,79,82} deck files (`#: tier:` prose only), dashboard.html, .cycle/STATE.md

CHANGES:
B1 | scripts/deck.py | Sentence-anchored `you control enchanted (creature|permanent|artifact|planeswalker).` pattern in `Removal (spot)`; 10 pool matches, 0 false positives (Mishra's Domination's conditional buff is the excluded one).
B2 | scripts/deck.py | Three copy-effect patterns in `Payoff / engine`.
B3 | scripts/deck.py | `_TEMPO_PATTERNS`, `tempo_effects`, `_tempo_note`; `role_tally` adds `tempo` + `tempo_kinds` (complement of interaction); vector `tempo`/`tempo_kinds`; printed in stats (beside protection), tier vector line, quality. check_patterns registers the three tempo regexes (norm corpus).
B4 | scripts/deck.py | Bounce pattern removed from `Removal (spot)` (history kept in `_TEMPO_PATTERNS`), bounce cue removed from `_INT_CUES`; `role_coverage_flags` and `check_roles.zero_role_cards` skip a tempo card (seen, not a role).
ALL | decks | 15 decks' `#: tier:` figures re-grounded (interaction counts, floor-band claims); letters untouched — none ends two bands above its floor.
ALL | tests/test_deck.py | Bounce test rewritten (bounce is tempo, not removal); clone-vs-spell-copier test now pins the narrow pattern (a clone is a payoff by the new rule); new TestBatchBRolesAndTempo (steals, the Mishra negative, copies, self-copy negative, tempo kinds + negatives, tally complement, tier_band ignores tempo).
ALL | CLAUDE.md, docs/gotchas.md | G-25 + K-12 rules and long forms; tier-spread figures refreshed (A 68 / B 45 / C 4, top band 58%).

TEST RESULTS: passed — check_all "All invariants hold"; full pytest green; check_patterns, check_docs and check_roles --tags clean. Roster before/after harness asserted 0 errors over 119 decks.
Roster diff: interaction changed in 19 decks (17 down — bounce; 2 up — steal Auras: 32, 71); card advantage 0; payoff counts moved in 44; `cuts` top-3 changed in 10, #1 in 2; **8 tier floors moved down** — 18/40a/47/51 A→B, 22/22-brawl/67/68 B→C (simulation had said 6). Role coverage 1,507 → 1,540 of 1,991; 32 baseline entries pruned, 0 newly acknowledged.
REGRESSION RISKS: The tier floor now under-counts bounce-heavy blue decks by design; a deck tuned for interaction must look at the tempo line too. Kinds are checked bounce → stun → tap and a card counts once, so a bounce-and-tap card reads as bounce. The `tap` kind includes Spider-Woman-style locks that last while the creature stays (arguably permanent) — left as tempo.
INVARIANTS AT RISK: None (no CSV writer touched; INV-04 holds — prose-only deck edits; postedit ran).
NET SCORE: 3 − 0 = 3 (B1, B2, B3+B4 counted as the tempo/bounce fix)

OPERATOR ACTIONS / DEPLOY:
- Owner: re-read the eight decks whose floors moved (18, 40a, 47, 51 now floor B; 22, 22-brawl, 67, 68 now floor C) — letters are a human call | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds and publishes dashboard.html on the next push to `main` (committed copy refreshed by `make postedit`).

(Not complete in production until blocking operator actions are done AND
the deploy step is confirmed.)

FOLLOW-ON ITEMS:
- Mass bounce stays a Sweeper — the owner may want it on the tempo line too (consistency); not done.
- Tagger agreement: steal Auras are not tagged `theft` (that rule reads "gain control of") — K-09 direction, out of scope.
- Deck 82's FRA cards are not in card-library.csv (24 "missing") — the standing FRA-ownership item, pre-existing.
- Batches C (legend-rule advisory) and D (Suggested Why) remain.

DOCUMENTATION UPDATES NEEDED:
None — done in this batch.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
