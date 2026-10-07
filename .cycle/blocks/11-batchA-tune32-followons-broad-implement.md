---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- A1 — G-22 figure_drift re-fired after every tune: ledger-count figures get a ±10% relative tolerance; CLAUDE.md figures refreshed (1112→1135, 375→387).
- A2 — wishlist.py --add with --target on an already-listed card now APPENDS the deck id (never replaces, never touches Note, id validated); plus the pre-existing bug it exposed: a name-only re-add appended a DUPLICATE row because the dedupe key carried the input line's set/collector.
Files modified: scripts/check_docs.py, scripts/wishlist.py, tests/test_check_docs.py, tests/test_wishlist.py, CLAUDE.md, docs/gotchas.md, .claude/commands/add-wishlist.md, README.md, .cycle/STATE.md

CHANGES:
A1 | scripts/check_docs.py | `_DRIFT_TOLERANCE` (label → relative tolerance) + `_within_tolerance`; `figure_drift` skips drift inside it. Keyed by label so `_live_figures`' (label, pattern, fn) triples — unpacked by two tests — keep their shape. Only the two G-22 ledger counts are tolerant; every other figure stays exact.
A1 | CLAUDE.md | G-22 figures refreshed to live (1135 / 387).
A1 | tests/test_check_docs.py | TestLedgerFiguresCarryATolerance: inside-tolerance silent, outside reported, unlisted figure exact, tolerance keyed only to live labels.
A2 | scripts/wishlist.py | `_append_target` (adds missing ids via `_norm_deck_id`, fills blank/`—`, keeps `general`/`concept:`, Note untouched); `cmd_add` matches a name-only line to listed rows by NAME (`by_name`) and appends `--target` to them; prints what it retargeted.
A2 | tests/test_wishlist.py | The old `test_a_re_add_does_not_clobber_a_hand_set_target` encoded skip-on-re-add; rewritten to the append contract ("42" → "42; 6", Note kept). New: no-target re-add leaves Target alone; `06` not appended twice; blank/`—`/`general` cases; name-only line matches the listed printing (no duplicate). 3 of the 5 fail against the old code.
A2 | CLAUDE.md G-82, docs/gotchas.md G-82 + G-19, .claude/commands/add-wishlist.md, README.md | append behaviour and the duplicate-row fix documented.

TEST RESULTS: passed — check_all "All invariants hold", 0 figure-drift warnings (was 2); full pytest suite green; check_docs OK (G-82 bullet under the 300-word cap).
REGRESSION RISKS: A name-only line that shares a name with a listed row is now treated as already listed, so it can no longer add a SECOND printing of the same card by name alone (pass `(SET) #` for that). The live wishlist holds no duplicate names, so no existing data relied on the old behaviour. `write_wishlist` still rewrites on a no-op re-add (pre-existing).
INVARIANTS AT RISK: None (no library/mana/pool/deck writer touched; card-wishlist.csv still written through `write_wishlist`).
NET SCORE: 2 − 0 = 2

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — no Deploy Command configured for the modified subsystems (Analysis / Ingest tooling ship by commit).

(Not complete in production until blocking operator actions are done AND
the deploy step is confirmed.)

FOLLOW-ON ITEMS:
- Batches B, C, D of the 2026-10-07 plan (STATE.md Pending).
- deck 28's `#~ note:` protection figure (1 vs live 2) and the three dead library searches remain soft warnings — pre-existing, out of scope.
- `cmd_add` rewrites the wishlist even when nothing changed (pre-existing, harmless churn).
(or "None")

DOCUMENTATION UPDATES NEEDED:
None — done in this batch.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
