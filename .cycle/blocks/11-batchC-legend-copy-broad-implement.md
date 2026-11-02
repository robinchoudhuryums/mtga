---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch C (deck-32 tooling follow-ons, planned 2026-10-07) — a legend-rule advisory in `deck.py targets`: copy effects that KEEP legendary status, measured against how much of what they could copy is legendary. Report-only, calibrated on the roster.
Files modified: scripts/deck.py, scripts/check_patterns.py, tests/test_deck.py, .cycle/STATE.md, .cycle/blocks/11-batchC-legend-copy-broad-implement.md

CHANGES:
C-1 | scripts/deck.py | The three copy templatings the `Payoff / engine` role reads moved into one named tuple, `_COPY_EFFECT_PATTERNS` (+ compiled `_COPY_EFFECT_RES`). The role table spreads it, so the advisory and the classifier read the SAME predicate (G-40). Role output unchanged (same strings; check_roles baseline green).
C-2 | scripts/deck.py | `_copy_effect_kind(text)` sorts one card's copy clause into keeps / strips (except it isn't legendary, or except its/his/her name is …) / nonlegendary (target nonlegendary, or "if … isn't legendary") / self-safe (legend rule off for its own copy) / card (copies a card off the battlefield) / token (copies tokens, including "for each … token" anaphors) / opponent. It also reads which permanent types the clause can copy. `legend_copy_conflicts(cards, carddata)` counts, per copy effect, the OTHER cards of those types in the list and how many are legendary (quantity-weighted, front face). It flags a "keeps" row when the share is at least `_LEGEND_COPY_FLAG_SHARE` (0.67) and no card turns the legend rule off deck-wide (Sakashima).
C-3 | scripts/deck.py | `cmd_targets` prints a third section via `_print_legend_copies`: keeps rows with "L of N (share)", a `⚠ legend rule` flag, a "Not counted:" line explaining each other kind, and a legend-rule-OFF note. It is also printed on the "no gated effects" early-return path, which the first wiring missed (deck 32 printed nothing).
C-4 | scripts/check_patterns.py | Registered `_LEGEND_RULE_OFF_RE`, `_LEGEND_RULE_ANY_OFF_RE` and `_COPY_STRIPS_RE` in the norm corpus. The gate hard-fails any unregistered compiled pattern.
C-5 | tests/test_deck.py | Added `TestLegendCopyConflicts` (5 tests, real oracle texts):
  - pins the shared predicate inside the role table;
  - pins every kind, including the four first-run misreads (Chameleon's "except HIS name is", Mirrormind Crown's "copies of", Ghired's and Rhys's token copies);
  - a heavy pool flags and a light one does not; the card itself is excluded from its own pool;
  - Sakashima silences the flag;
  - non-keeps rows never flag.

CALIBRATION (2026-11-02, 134 deck files): 37 decks run a keep-legendary copy effect (68 rows). Legendary share of the copyable pool: p25 0.35 / p50 0.51 / p75 0.59. At 0.67 the flag fires on 8 of the 37 (22%), below the top quartile (G-07):
  - 12: Silent Hallcreeper, 18 of 22
  - 22-brawl: The Everflowing Well
  - 38: Mirrormind Crown, 10 of 13
  - 54: Ashling's Command / Echocasting Symposium / Applied Geometry
  - 71: Ashling's Command / Self-Reflection
  - 78-historic-brawl: Mirror Room
  - 84: Three Steps Ahead, 45 of 55
  - 94: Three Steps Ahead
Deck 32, which motivated this (17 of 24 legends then), now reads 12 of 22 (55%) after its tune and is not flagged.
The first run had flagged 10 decks. Two were false: Chameleon in 87 and Ghired in 88. Both were fixed (C-2) before the threshold was set.

TEST RESULTS: full pytest suite passed (0 failures). `check_all` OK with 5 soft. The first `check_all` run failed 3 hard (unregistered patterns), fixed by C-4.
REGRESSION RISKS: The role table now spreads a tuple instead of literal strings; the compiled role patterns are identical (verified by a printed list and a green check_roles baseline). The `targets` output gains a section at its end; no consumer parses it (test_cli / determinism green).
INVARIANTS AT RISK: None (read-only report; no data or deck writes).
NET SCORE: 1 production fix (8 roster decks carry the shape today, none of them reported before) − 0 new failure modes = 1. Residuals are documented in the code and below: the classification is per FIRST copy clause, and a card with two copy clauses of different kinds reads as its first.

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — the dashboard does not render `targets`; no Pages rebuild needed.

FOLLOW-ON ITEMS:
- A card with TWO copy clauses (e.g. a mode that strips and a mode that keeps) is classified by its first; none on the roster today.
- The "Copies" type read defaults to creature when a clause names a subtype only (Brigid's Command → Kithkin). Reading the subtype against the list would be sharper; not built.
- The 8 flagged decks are a read for their owners, not a cut list: Three Steps Ahead in 84/94 is a modal spell whose copy is one of three modes.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-66 (or G-76): one sentence that `targets` now also prints the legend-rule copy advisory, report-only, threshold 0.67 (p75 0.59).
- docs/gotchas.md G-66 long form: the calibration and the four first-run misreads.
- README `targets` line; /tune-deck Stage 2c-bis could name the third section.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
