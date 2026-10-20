---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch 5 of the 2026-10-20 Brawl tooling plan (items 7 and 9), plus a
  regression from Batch 1 that this batch exposed.
  - Item 7: pack planning across several decks had no tool; a hand script joined ownership on
    the wrong key. Now `deck.py wildcards --by-set [--decks ID …]`.
    DEVIATION FROM THE PLAN (measured, not preferred): the plan said `wishlist --by-set --decks`,
    but the wishlist held only 35 of the 96 cards decks 84–86 were missing, so a wishlist view
    would have omitted 61. The decks are the source of truth for what a deck needs, and
    `wildcards` already computed the shared-collection shortfall from them.
  - Item 9: `suggest --lands` led with craft targets, so owned lands sat below the window
    unseen (deck 85: 50 owned options, 0 shown at the default limit). Now a footer says so.
  - Batch 1 regression: `lib.normalize_card_name` collapsed EVERY `//`, so the real card
    "SP//dr, Piloted by Peni" (decks 65 and 84) keyed as "sp" in `_ms_key` and lost its printing
    in `_printing_of`. Found because `--by-set` (joins through `owned()`) disagreed with a direct
    `_ms_key` count by exactly that one card.
Files modified: scripts/deck.py, scripts/lib.py, tests/test_deck.py, .cycle/STATE.md,
  .cycle/blocks/tooling-batch5-broad-implement.md, .cycle/blocks/tooling-batch1-broad-implement.md

CHANGES:
Item 7 | scripts/deck.py | `wildcards`: new `--decks ID …` (resolved through `find_deck`, unknown
  id refused, scopes all three views) and `--by-set` (the `--dedup` shortfall — a card short in
  several decks counts once, at the most any deck needs — grouped by the (SET) its first deck
  line names; sets ordered mythic+rare first; per card rarity, copies, rotation note, decks;
  the existing collection-freshness note prints first; a closing line says a card printed in
  several sets may come from another set's packs and that supplemental-set pack availability is
  a store question). The per-card set is recorded in the existing requirements loop (`set_of`).
Item 9 | scripts/deck.py | `suggest_lands` counts owned picks BEFORE the `--limit` cut and returns
  `owned_info` (total, candidates, best owned name/score/rank); `cmd_suggest_lands` prints
  "ⓘ N owned land(s) qualify, M shown here; the best owned is X (score, #rank of T)" on the
  default view only, and only when the window hid some.
Regression | scripts/lib.py | `normalize_card_name` now collapses only a run of THREE+ slashes, or
  a `//` already touching whitespace; a bare `//` inside a word is part of the name.
Tests | tests/test_deck.py | `TestWildcardsBySet` (3), `TestLandsOwnedFooter` (2), and two
  normaliser cases (SP//dr survives; `Fire //Ice` is tidied).

TEST RESULTS: passed — full pytest suite exit 0; check_all: all invariants hold.
  Live: `wildcards --by-set --decks 84 85 86` → 95 distinct cards across 25 sets (MSC 55: 14 M /
  23 R / 17 U / 1 C; MAR 7 M; …), equal to a direct count once the regression was fixed (the
  "96" of the morning was itself inflated by the bug). `suggest --lands 85` footer: 50 owned
  qualify, 0 shown, best Airship Engine Room #28 of 247; silent with `--owned`.
REGRESSION RISKS: `--decks` and `--by-set` are additive; the default `wildcards` output is
  unchanged. `suggest_lands` only GAINED a return key (`owned_info`). The normaliser change only
  narrows what is rewritten: every spaced `A // B` and every 3+-slash run still normalise.
INVARIANTS AT RISK: None — nothing here writes. (The regression could have mis-keyed SP//dr in
  INV-04's copy counting and `verify`/`sync`; fixed before any deck write used it.)
NET SCORE: production fixes 3 (item 7 and item 9 both fired this month on decks 84–86; the
  SP//dr key regression was live in decks 65 and 84 since Batch 1's commit) − new failure modes
  0 = net +3. Batch 1's block is amended: its normaliser introduced the regression, so its net
  is 2 − 1 = 1.

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: N/A — no Deploy Command configured for scripts/deck.py or scripts/lib.py.

FOLLOW-ON ITEMS:
- `--by-set` attributes a card to the set its DECK LINE names; a card reprinted in a main set
  could be opened from that set's packs too. Listing every set that prints a card needs a
  per-printing table the pool does not hold (it keys one printing per card).
- The `wishlist --by-set` view remains (it answers "my wishlist by set"); its docs should say it
  covers wishlisted cards only.

DOCUMENTATION UPDATES NEEDED:
- README: `deck.py wildcards --by-set --decks 84 85 86` beside the other craft-planning lines.
- CLAUDE.md G-19 (wishlist `--by-set` is wishlist-only; the deck view is `wildcards --by-set`),
  G-37 (the owned-options footer), G-63 long form (a bare `//` inside a name survives).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
