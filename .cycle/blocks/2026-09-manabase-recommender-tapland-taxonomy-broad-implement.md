---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
  1 — `suggest_lands` structurally could not propose a second copy of a land already in the deck
  2 — `lib.tapland_kind`'s `conditional` bucket merged clauses with opposite early-game timing
  3 — `lib.collection_stamp_note` had three consumers and the integrity gate was not one

Files modified: scripts/deck.py, scripts/lib.py, scripts/wishlist.py, scripts/check_all.py,
scripts/check_patterns.py, tests/test_deck_models.py, tests/test_lib.py,
tests/test_wishlist.py, tests/test_check_all.py, CLAUDE.md, docs/gotchas.md, README.md

CHANGES:
1 | scripts/deck.py | `suggest_lands` dropped the `nl in deck_names` skip it had inherited
verbatim from `suggest` proper (right there — proposing a card you already run is G-04's
`+In` bug; wrong for a manabase, where 2-4 of a dual is ordinary). Only the format copy
limit and basics exclude now. An `In` column carries the copies already in the deck so a
duplicate cannot read as a new card, and `suggest --needs` — which renders the SAME picks —
got an inline `(+1, you run N)` marker for the same reason. Roster: 58 of 112 decks' #1
land pick is now another copy, all singleton untapped duals; a duplicate appears in the top
five for 96 of 112.

2 | scripts/lib.py, scripts/wishlist.py, scripts/deck.py, scripts/check_patterns.py |
WIDER THAN FILED. The finding said "checkland vs board-state"; measuring the pool's 87
conditional lands found FOUR families with opposite timing — `fast` ("two or FEWER other
lands", 11 cards, untapped turns 1-3), `check` (a basic-land gate, 35), slowland ("two or
MORE", 10) and board state ("13 or less life", 10). `_TAPLAND_FAST_RE` / `_TAPLAND_CHECK_RE`
split them; `tapland_kind` returns the new kinds; `TAPLAND_CONDITIONAL_KINDS` lets consumers
test membership instead of string-matching. `_land_value` grants the untapped premium to
`fast` outright and to `check` only when the CALLER passes a basic count clearing
`_CHECKLAND_BASIC_FLOOR` = 12 (roster p25 of 114 decks; conservative turn-three model reads
76% there, real play higher because you sequence). `basics=None` means unknown and stays
conservative, so every non-opting caller is byte-identical. `suggest_lands` passes the
deck's basics and prints `·fast` / `·check` instead of one flat `·tapped?`. Both new
patterns registered in check_patterns (its gate caught them unregistered — working as
designed). Impact: 35 of 676 pool land rows move once basics are known; 11 fastlands gain
it unconditionally.

3 | scripts/check_all.py | NARROWER THAN FILED, and the finding was partly wrong: the note
ALREADY distinguished never / stale-with-age / fresh. The real gap was only that `check_all`
never called it. Added as one soft warning via `collection_freshness_soft()`, a module-level
function rather than an inline block in `main()` so it can be watched failing (this file's
own standing rule, BS2-29).

TEST RESULTS: 17 new tests in 5 classes, each verified to FAIL against a mutant (fast
premium dropped; basics floor ignored; old blanket exclusion restored; copy-limit guard
removed). Every affected file passes: test_lib, test_wishlist, test_deck_models,
test_check_all, test_check_patterns, test_deck, test_cli, plus files 1-11 in collection
order. check_all green; check_docs 114 rules both directions; check_commands OK; both
--help levels OK. Regression scenario 2 walked on deck 16 — all commands PASS (`check`
exits 1 on any deck with craft targets, which is G-12 documented behaviour, identical on
the pre-change tree and on untouched deck 70).
  ONE PROCESS FAILURE WORTH RECORDING: a first full-suite run reported five failures, all
  artifacts of MY OWN concurrent edits — scripts/deck.py and scripts/wishlist.py were
  modified while that background run was reading them. All five pass on the settled tree.
  The clean re-run is guarded by a before/after md5 of scripts/ so a polluted run cannot
  be mistaken for a red one again.

REGRESSION RISKS:
- `wishlist --rank` REORDERS: the fastland premium moves Blooming Marsh 23 -> 8 and
  Concealed Courtyard 24 -> 9, pushing 15 cards down one place (36 changed lines).
  INTENDED — they were scored as though they always entered tapped, the same defect the
  2026-09-04 shockland fix closed — but it is visible. Both keep their ⚠rot~2026 flag.
- `tapland_kind` returns two new strings. All four call sites were found and updated;
  `TAPLAND_CONDITIONAL_KINDS` exists so a future caller cannot silently mean something
  narrower by testing `== "conditional"`.
- `_land_value` gained an optional `basics=None`. Default reproduces the old score exactly.

INVARIANTS AT RISK: None. No data file is written by any of this; INV-01..04 untouched.

NET SCORE: 3 production fixes − 0 new failure modes = 3
  1: YES, would have fired this month — it did, on decks 16 and 79 the same week.
  2: YES — it mis-scored Agna Qel'a and Abandoned Air Temple in this cycle's own work.
  3: YES — five stale counts priced two decks at nine rare wildcards against a real zero.

OPERATOR ACTIONS / DEPLOY:
- Run `import_collection.py` with a tracker export to clear the new freshness warning and
  make every craft figure trustworthy | BLOCKS DEPLOY: N
Deploy: Presentation subsystem untouched by this change; the dashboard rebuilds from source
on push to main via .github/workflows/pages.yml as usual.

FOLLOW-ON ITEMS:
- `wishlist --rank` calls `_land_value(r, dcols)` where `dcols` comes from the row's Target
  deck, so it COULD pass that deck's basics and price checklands properly. Not built: the
  wishlist holds ZERO checkland rows today, so the change would be unmeasurable, and this
  project's rule is to measure. Revisit when a checkland is wishlisted.
- No surface computes P(a tapped land among your first N land drops). Hand-rolled six times
  in one session (38/31/24/16/8/0%) and it was the number that decided both manabases. The
  board_power (G-86) shape. Must stay REPORT-ONLY — `tapland_profile`'s docstring already
  commits to never feeding a score, and G-25/G-60/G-86 say why.
- `_central_themes` uses a relative cutoff, so adding two tagged lands moved deck 79's
  reported count 11 -> 8 with no deck change. Report-only, arguably working as designed;
  documented in the deck's notes rather than filed.

DOCUMENTATION UPDATES NEEDED: Done in this change — G-37 (duplicates + the `In` column),
G-35 (the four-way split, the floor, TAPLAND_CONDITIONAL_KINDS), G-10 (the gate now reports
freshness), the Cycle Workflow Config's soft-sweep list (an ELEVENTH), README's
`suggest --lands` line, and three new evidence sections in docs/gotchas.md. All three rules
verified under the 300-word cap.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
