# Cycle state — 2026-07

## Where I left off
All three findings from the card-misread reflection are implemented, gated,
documented, committed and pushed on `claude/add-cards-ingested-batch-cy2tdb`.
Nothing is half-done. The block is at
`.cycle/blocks/2026-07-card-misread-causes-broad-implement.md`.

## Completed this session
- Finding 1 — `cuts` multiplier co-signal (`✱`) + a `lifegain` doubler axis.
  Root cause was a CALLER, not a model: `doubler_axis`/`doubler_support` already
  scored Delney correctly for `suggest-homes`; `cuts` never asked.
- Finding 2 — `deck.py screen <id> <names…>`, re-scoring a candidate pile against
  the deck as it currently stands. Wired into /draft-deck and /tune-deck.
- Finding 3 — `strict_upgrades`, surfaced by `screen` as `★ STRICT UPGRADE`.
- Deck 46 (Radiant Ascension) was built and refined across this session and is at
  tier A, floor A, 60 cards, 16 craft targets.

## Decisions made
- The multiplier term only ever RAISES a keep-score. The no-support case is already
  handled by theme-fit; subtracting would punish the same card twice.
- `strict_upgrades` is text-containment with colour identity deliberately EXCLUDED,
  so a containment result never depends on the deck's colours. Conservative by
  design; its silence is explicitly not a verdict.
- The lifegain axis requires the literal "twice that much" — a plus-N replacement
  (Angel of Vitality) is templated identically and must not qualify.
- Anchor 16's WIRING half lives in tests/test_deck_models.py, since a pure-function
  anchor structurally cannot see whether a caller invokes the function.

## Open follow-ons
See FOLLOW-ON ITEMS in the block. Highest value: the reverse flag (a candidate
strictly WORSE than an incumbent), and README coverage for `screen` via /sync-docs.
