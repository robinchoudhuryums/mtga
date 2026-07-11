Run the project integrity check and report the result.

Run: `python3 scripts/check_all.py`

This is the project's Test Command (see CLAUDE.md Cycle Workflow Config). It
verifies the Invariant Library: card-library.csv structure (via validate.py),
card-mana.csv coverage, presence of derived files, that every deck parses, and a
deck buildability summary.

Report:
- The pass/fail result and any HARD FAILURES verbatim.
- If it fails, diagnose the first failure and propose the fix (do not apply it
  unless asked). Common causes: forgot to run build_mana.py after importing new
  cards (INV-02), or a stale/missing derived file (INV-03) — usually fixed by
  `/refresh`.
- Note that WIP decks showing "missing" cards are expected (craft targets), not
  failures.
