---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch 3 of the 2026-10-20 Brawl tooling plan (item 4)
  - Item 4: there was no way to reverse a swap without leaving its ledger row behind. The
    Leonardo round trip in deck 86 (swap in, swap back out) left two recommendations.csv
    rows that had to be pruned by hand. Now `swap <id> --undo` reverses the deck's most
    recent swap and removes its row — ONE step, per the owner's decision (2026-10-20).
Files modified: scripts/deck.py, tests/test_deck.py, .cycle/STATE.md,
  .cycle/blocks/tooling-batch3-broad-implement.md

CHANGES:
Item 4 | scripts/deck.py | new `drop_recommendation(index)` — removes one ledger row through
  the same atomic, backed-up DictWriter rewrite as `append_recommendation`.
Item 4 | scripts/deck.py | new `_deck_backups_newest_first` (orders a deck's `.bak`s by the
  CREATION stamp via `lib.backup_stamp`, never mtime) and `_undo_last_swap`: finds the deck's
  last ledger row; refuses a non-`swap` source (apply-flex); re-applies that cut/add to the
  newest backup with `_swap_edit_lines` and requires the result to equal the CURRENT file as a
  multiset of lines (so `--section` and a `move` of the added card are tolerated); restores
  the backup through `_safe_write_lines` (INV-04 parse + copy-count check, new .bak of the
  swapped file) — byte-identical to the pre-swap file — then drops the ledger row. Refuses
  when anything else changed since the swap (a header/notes edit, another card, or a `move`
  of an UNRELATED card, which restoring would silently revert). Dry run unless --apply.
Item 4 | scripts/deck.py | `swap` argparse: `--cut`/`--add` no longer argparse-required (cmd_swap
  validates them unless `--undo`); new `--undo` flag; `--undo` rejects `--cut/--add/--section`.
Item 4 | tests/test_deck.py | `TestSwapUndo` (8): byte-identical restore + row dropped; dry run
  writes nothing; survives a `move` of the added card; refuses after an unrelated `move`;
  refuses after a later edit (and keeps the row); refuses with no recorded swap; refuses a
  flex row; rejects `--undo` with `--cut`.

TEST RESULTS: passed — full pytest suite exit 0; check_all: all invariants hold.
  Read-only check on deck 85 (its notes were edited after the last swap): undo refuses with
  the "changed since its last swap" message; deck file and ledger byte-identical.
REGRESSION RISKS: `--cut`/`--add` moved from argparse-required to a runtime check in cmd_swap —
  every existing caller passes both, and a missing one still exits 1 with a message. The
  ledger removal is a full rewrite like `append_recommendation` (atomic, with .bak); it is
  not a scoring function, so `test_recommendations`' ledger-isolation rule is unaffected.
  The common workflow (swap, then edit notes) makes undo REFUSE — by design, since restoring
  would discard the notes; the message says to reverse with an ordinary swap.
INVARIANTS AT RISK: INV-04 — the restore writes through `_safe_write_lines`, so the parse and
  copy-count checks run on it. None violated.
NET SCORE: production fixes 1 (fired this month: the deck 86 Leonardo round trip needed two
  ledger rows pruned by hand) − new failure modes 0 = net +1. (A reorder-past-an-unrelated-
  move failure mode was found in review and closed before commit, with a test.)

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: N/A — no Deploy Command configured for scripts/deck.py.

FOLLOW-ON ITEMS:
- `apply-flex` rows cannot be undone (the consumed flex line is not reproducible from the
  ledger); refused with a message. Revisit only if it is ever needed.
- Undo cannot reach past a notes edit; storing a post-swap hash per row would allow a
  targeted inverse, but it changes the ledger schema — not worth it for one-step undo.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-06 (swap --apply) and G-56 (the ledger) should mention `swap --undo`: one step,
  removes its own ledger row, refuses if the file changed since beyond that swap.
- /apply-changes skill could name `swap --undo` as the remedy for a swap applied in error.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
