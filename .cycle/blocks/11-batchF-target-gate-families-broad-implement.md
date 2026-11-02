---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch F (2026-10-08 tuning-pass holes) — three gate families `deck.py targets` could not see: mana spent ("if at least N mana was spent to cast it"), type presence ("if you control a <creature type>"), and not-cast ("if none of them were cast" / "enters … if it wasn't cast"). Report-only, G-66/G-76 shape, measured on the roster and at `suggest`.
Files modified: scripts/deck.py, scripts/check_patterns.py, tests/test_deck.py, .cycle/STATE.md, .cycle/blocks/11-batchF-target-gate-families-broad-implement.md

CHANGES:
F-1 | scripts/deck.py | `spent` gate: captures the trigger's scope (noncreature / creature / any spell) and N. It counts the other non-land cards of that scope at front-face MV ≥ N, and discloses X spells beside the count ("(+1 X spell)") because X counts as 0. Pool: 7 cards. Roster: 5 rows (Emperor of Palamecia in 25/37/37a, Prima Vista and Prompto in 48a). Deck 18's cut Ultros/Sahagin, re-probed against the current list: 3 qualifying spells.
F-2 | scripts/deck.py | `control` gate: "if you control a/an/another/two or more/three or more <word>". It counts only when the word is a creature subtype in the tagger's own vocabulary (`tag_synergies._CREATURE_TYPES`, so the two cannot disagree on what a tribe is, K-17); Human is skipped. The raw shape matched 292 pool cards, nearly all noise (Verges, "a creature", "two or more other lands"). Creatures of the subtype plus changelings are counted, with the stated need. Roster: 24 rows, all real gates on spot-read; Psychic Whorl's Rat rider reads 0 in decks 44 and 44a; Beorn holds 1 of 3 Bears in deck 88.
F-3 | scripts/deck.py | `notcast` gate: "if (none of them were | it wasn't) cast", excluding "…cast this way" (Beseech the Mirror's leftover clause). Enablers via `_brings_in_uncast` / `_UNCAST_RE`: put/return a creature card onto the battlefield, exile-then-return blink, "without paying its mana cost", plot. A card whose OWN text is an enabler counts itself (Freestrider's plot). Pool: 3 cards; 0 roster rows today (Satoru was cut from deck 12 after its tune); the re-probe there reads 1 enabler (Uldaros Theorix). `_UNCAST_RE` matches 398 pool cards; a 30-card sample read about 3 in 4 genuine (misses: noncreature free casts, a Saga returning itself).
F-4 | scripts/deck.py | MEASURED AT THE CALLER (G-40): `unmet_gate` feeds `swap`/`suggest`/`screen`/`redundancy`. With the `control` family included, `suggest --unowned` "needs" rows on ten decks went 67 → 132, mostly riders and cost reductions ("costs {1} less if you control a Wizard"). So `unmet_gate` skips that family (`_CONTROL_LABEL_MARK`); it stays in `targets`, where the card is read beside the count. `spent` and `notcast` still reach the recommenders (deck 86 back to its 23-row baseline).
F-5 | scripts/deck.py | `target_counts`' pool entries carry the front-face `cost` for the X-spell disclosure.
F-6 | scripts/check_patterns.py | `_UNCAST_RE` registered (the gate hard-fails an unregistered pattern; the three gate regexes register themselves through `_TARGET_GATES`).
F-7 | tests/test_deck.py | `TestBatchFGateFamilies`, 5 tests on real oracle texts:
  - spent: scope and threshold; the creature is excluded and the X spell disclosed;
  - control: subtype plus changeling counting, zero, the stated "three or more", a Verge not reported, and kept off `unmet_gate`;
  - notcast: blink and a card's own plot count; Beseech is not a gate.

TEST RESULTS: full pytest suite passed; check_all OK with 5 soft.
REGRESSION RISKS: `target_counts` returns more rows, so `targets` prints more. `check_all`'s dead-library-search sweep filters on "in the deck" labels and is unaffected. `unmet_gate`'s output is unchanged for the control family by design, and new for spent/notcast, both narrow (7 + 3 pool cards).
INVARIANTS AT RISK: None (read-only report).
NET SCORE: 1 production fix (Psychic Whorl's dead rider in 44/44a and Beorn's 1-of-3 in 88 are live; the two cut cards that motivated the batch were found by hand) − 0 new failure modes = 1. `_UNCAST_RE` is a ~75%-precision proxy, recorded rather than counted as a new failure mode, since the report prints the count for a human to read.

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — the dashboard does not render `targets`.

FOLLOW-ON ITEMS:
- `targets` prints a gate's COUNT but not the cards behind it. For the heuristic families (notcast especially) a "which cards" list would let a human audit the proxy. Not built here.
- Ultros's second clause ("at least eight mana") is not reported; only the first match per gate is read (a pre-existing property of `target_counts`).
- The footer "a gate with nothing behind it is a dead card" overstates a rider (Psychic Whorl still discards). Wording, pre-existing.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-66 is at the word cap: one clause on the three families, and that type presence stays off the recommenders. The detail goes in the docs/gotchas.md G-66 long form.
- README `targets` paragraph.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
