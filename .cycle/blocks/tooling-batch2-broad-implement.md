---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch 2 of the 2026-10-20 Brawl tooling plan (item 1)
  - Item 1: `swap --apply` never checked commander colour identity. Leonardo, the Balance
    ({W}{U}{B}{R}{G} activation, so B in identity) was written into the G/R/U/W deck 86;
    only `preflight` caught it afterwards. Now: warned in the dry run, REFUSED on --apply
    (owner's decision 2026-10-20: "refused and warned"; no --force).
Files modified: scripts/deck.py, tests/test_deck.py, .cycle/STATE.md,
  .cycle/blocks/tooling-batch2-broad-implement.md

CHANGES:
Item 1 | scripts/deck.py | `_do_swap` keeps the parsed deck meta (`dmeta`) and computes
  `commander_identity_lock(dmeta, carddata)` — the same lock and the same
  `card_colors(colors) <= lock` test `legality_report` applies, so `swap` and `legal` cannot
  disagree. Preview prints `⛔ identity: <add> has colour identity X, outside the
  commander's Y — illegal in this deck; --apply will refuse it.` On --apply it returns 1
  BEFORE the ledger row and before any write (no .bak, no recommendations.csv row). No lock
  (non-commander format, unplaceable commander) or an add the card data cannot place → no
  gate. Covers `apply-flex` too (shared engine).
Item 1 | tests/test_deck.py | `TestSwapIdentityGate` (3): refused apply leaves the file,
  ledger and backups untouched; dry run prints the ⛔ line; an on-identity apply still writes.

TEST RESULTS: passed — full pytest suite exit 0; check_all: all invariants hold.
  Verified live on deck 86: Leonardo → ⛔ + rc=1 with deck file and recommendations.csv
  byte-identical; Domri (on-identity) unaffected; a basic Swamp is caught too.
  Roster measurement before the change: 8 commander-format decks, all 8 locks placeable,
  0 decks holding an off-identity card — the gate cannot trap an existing deck at rest.
REGRESSION RISKS: `apply-flex` shares `_do_swap`, so an off-identity flex line is now refused
  (intended). Non-commander decks: `commander_identity_lock` returns None before any lookup,
  so no new output on 60-card decks. A stale pool `Color(s)` cell could refuse a legal card,
  but `legal` would mis-call the same card, so this adds no new class of error.
INVARIANTS AT RISK: None — the refusal happens before `_safe_write_lines`, so INV-04 is never
  exercised on a refused swap.
NET SCORE: production fixes 1 (fired this month: Leonardo, deck 86, 2026-10-20) − new failure
  modes 0 = net +1

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: N/A — no Deploy Command configured for scripts/deck.py (the dashboard rebuild on push
  is unaffected).

FOLLOW-ON ITEMS:
- Batch 4 (package preview) must print this same ⛔ line per pair (the plan's dependency).
- Item 2 follow-on from Batch 1 still open: suggest/screen/cuts read Legalities directly and
  exclude a blank row silently instead of marking it unverified.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-06 lists what `swap --apply` checks (INV-04, flex retirement, the unmet-gate
  line); it should add that an off-identity add in a commander format is refused. G-09's
  `legal` paragraph could note `swap` now shares its identity test.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
