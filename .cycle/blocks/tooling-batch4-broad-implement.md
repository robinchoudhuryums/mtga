---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch 4 of the 2026-10-20 Brawl tooling plan (item 5)
  - Item 5: there was no way to preview several swaps as one change. Every package in the
    decks 84–86 builds went through a hand-rolled scratch simulator (write a temp deck, run
    `tier` on it), which crashed with a bare IndexError on a misspelled cut name. Now
    `swap <id> --package "cut=add" …` prints the combined result and writes nothing.
Files modified: scripts/deck.py, tests/test_deck.py, .cycle/STATE.md,
  .cycle/blocks/tooling-batch4-broad-implement.md

CHANGES:
Item 5 | scripts/deck.py | new `_package_preview(d, raw_pairs)`: parses `cut=add` pairs
  (names through `lib.normalize_card_name`, adds through `_printing_of`), applies them IN
  ORDER with `_swap_edit_lines` on the raw lines, and per pair prints the identity verdict
  `--apply` would give (Batch 2's lock and test), an unknown-card warning, and the
  `section_mismatch` advisory. A cut not in the deck (after the earlier pairs) is named and
  the preview exits 1. Then: `deck_quality_vector` on the current deck and on a temp copy
  of the result (the `_quality_vector_at` pattern; temp file outside the repo, removed),
  printed as tier floor + interaction / card advantage / protection / board power / early
  drops / central themes / uncastable / avg MV with before → after; one `legality_report`
  on the resulting list; a closing ⛔ count. No write, no .bak, no ledger row.
Item 5 | scripts/deck.py | `swap` argparse: `--package CUT=ADD [CUT=ADD …]`; cmd_swap routes it
  first and refuses it with --cut/--add/--undo/--section/--apply (preview only).
Item 5 | tests/test_deck.py | `TestSwapPackage` (6): writes nothing (file, ledger, backups);
  the printed combined figures EQUAL the quality vector after actually applying the same
  pairs; a missing cut exits 1 and names it; a pair without `=` and `--apply` are refused;
  the per-pair ⛔ identity line appears in a Brawl deck.

TEST RESULTS: passed — full pytest suite exit 0; check_all: all invariants hold.
  Live on deck 86 (Domri for Storm, Windrider; Leonardo for Storm, Force of Nature; Shuri for
  Jennifer Walters): the preview printed floor A, interaction 14, card advantage 12,
  protection 8, board power 137, avg MV 3.76, central themes 14 — identical to the scratch
  simulator — flagged Leonardo per pair and in the legality check, and left deck 86 and
  recommendations.csv byte-identical.
REGRESSION RISKS: additive — a new flag and a new function; existing `swap` paths unchanged
  (`getattr(args, "package", None)` keeps programmatic callers without the field working).
  The preview computes the quality vector twice, so it costs a few seconds more than a
  single swap preview.
INVARIANTS AT RISK: None — nothing is written; the temp copy lives outside decks/, so INV-04
  and the roster never see it.
NET SCORE: production fixes 1 (fired this month: every 84–86 package went through the
  crash-prone scratch simulator) − new failure modes 0 = net +1

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: N/A — no Deploy Command configured for scripts/deck.py.

FOLLOW-ON ITEMS:
- `/tune-deck` and `/apply-changes` could run `swap --package` on a proposed set before asking
  for confirmation (the skills still describe one-pair previews).
- The preview reports protection/board power but not the X-cost or cheat-cost advisories
  `tier` prints; add them only if a package decision ever turns on them.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-06: name `swap --package` as the way to preview a multi-swap package.
- README: a `swap 20a --package "A=B" "C=D"` example beside the other swap lines.
- /tune-deck, /apply-changes: use `--package` for a proposed set.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
