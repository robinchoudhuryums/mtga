---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- SK-1 | `parse_matches.py --sync-names` WROTE with no dry run. `main()` passed
  `apply=args.sync_names` on the paste path — the only writer in the file ignoring
  `--apply` — and a hardcoded `apply=True` on the sourceless path, which could
  therefore not be previewed at all. It adopted ten `#: name:` headers unannounced
  in one 2026-08-25 session when two had been shown to the user.
- FOLLOW-ON (deck 35 tier) | RESOLVED, and NOT by a re-grade. Deck 35's `#: tier:`
  already argues its below-floor B in the rubric's own language; the suppression
  pattern `_BELOW_FLOOR_ARGUMENT` only matched the LONG form of the A-band clause,
  so the deck was permanently nagged "possibly UNDER-graded" for being honest —
  exactly the failure the pattern's own comment says it exists to prevent.
- FOLLOW-ON (roster-review `tier`; skills not naming the G-75/G-79 sweeps) | Both
  were checked and closed as NOT gaps in the previous block. No code change; noted
  here so a fresh session does not re-raise them.

Files modified:
- scripts/parse_matches.py
- scripts/deck.py
- tests/test_parse_matches.py
- tests/test_deck.py
- .claude/commands/log-matches.md
- README.md
- CLAUDE.md
- docs/gotchas.md
- docs/systems-map.md

CHANGES:
SK-1 | scripts/parse_matches.py | `--sync-names` now SELECTS the reconcile and
  `--apply` WRITES it, matching `sync_headers` / `map_decks` / `add_manual` on the
  lines around it. Sourceless path takes `apply=args.apply`; both paste-path call
  sites take `apply=(args.sync_names and args.apply)`. The conjunction has a second
  effect worth naming: a routine `session.log --apply` ingest can no longer rename a
  deck as a side effect of recording a match. Help text for BOTH flags rewritten
  (`--apply` never said it gated anything but matches.csv, though it has gated the
  header sync all along), plus the dry-run hint, which now names the full invocation
  because that one line prints in two different situations.

SK-1 | tests/test_parse_matches.py | New `TestSyncNamesIsADryRunWithoutApply`, five
  tests, ALL driving `main()` rather than the helper. That is the point: the helper
  `sync_deck_names(text, apply=…)` has taken the parameter since it was written and
  had tests on both sides of it — what was wrong was what the CALLER passed. A
  parameterized primitive says nothing about whether anything asks (G-40, one layer
  up). Mutation-tested in both directions: reverting the code fails exactly the two
  dry-run tests, and writing the conjunction as `or` instead of `and` fails the
  routine-ingest test, so no test in the class is vacuous. Also tightened the
  existing hint assertion from `--sync-names` to `--sync-names --apply`.

FOLLOW-ON | scripts/deck.py | `_BELOW_FLOOR_ARGUMENT` matched only "at most one
  clear weakness"; decks quote the rubric in shorthand — deck 35 writes `More than
  the "≤1 weakness" an A allows` and deck 17 `not a coherent engine with one
  weakness`. Widened to `(?:≤\s*1|at most one|one) (?:clear )?weakness`.
  MEASURED FIRST, per K-14: of the 62 decks sitting below their floor, 12 were
  flagged; the widen suppresses exactly 2 and both were read by hand and are true
  positives; 10 remain flagged. Not a topic match — `tests/test_deck.py` adds a
  negative control that bare "weakness" in a rationale does NOT suppress.

SK-1 | docs | `.claude/commands/log-matches.md` now shows the three-form invocation
  and requires showing the user the plan before `--apply` — the preview is the only
  place the stranded-citation and orphaned-variant ⚠ flags appear before the write.
  README, CLAUDE.md (G-73), docs/gotchas.md (G-73 long form) and docs/systems-map.md
  updated to the two-flag semantics; the incident and the G-40 reading live in
  gotchas.md, with CLAUDE.md carrying only the rule.

TEST RESULTS: passed.
- `python3 scripts/check_all.py` — All invariants hold. ✓ (1 pre-existing soft
  warning: 4 dead library searches, G-75, unrelated)
- `python3 -m pytest` — **1500 passed**, 0 failed (+7)
- `check_patterns` 282 patterns live · `check_tier` OK · `check_docs` structure OK
- Regression Scenario 9 (Outcomes) walked on the leg that needs no person, against
  the REAL repo: a divergence was created on deck 16, `--sync-names` reported the
  plan and left the file and its backups untouched, `--sync-names --apply` adopted
  the name and wrote a `.bak`, and the deck was restored. This is the bug reproduced
  and the fix confirmed on real data, not fixtures.

  `check_docs` FAILED once mid-session — the G-73 bullet hit 16 lines against its
  15-line cap because the incident narrative had been written into CLAUDE.md instead
  of gotchas.md. That gate did its job; the evidence was moved and the rule trimmed.

REGRESSION RISKS: One real behaviour change, intended and user-facing:
`parse_matches.py --sync-names` no longer writes. Anyone (or any script) invoking it
expecting the old semantics now gets a preview and must add `--apply`. That is the
fix, and the operator-facing docs all changed with it, but it is a CLI contract
change rather than a pure bug fix. No return type, signature or default changed —
`sync_deck_names` / `sync_deck_names_from_headers` already defaulted to `apply=False`
and every existing caller is unaffected.

The old behaviour was never correct: every other writer in this file, and every
writer in the repo, is dry-run-then-`--apply`.

INVARIANTS AT RISK: None. INV-04 is the only one in reach (a deck-name rewrite must
re-parse) and it is untouched — `_write_deck_name` is unchanged, and the change only
ever makes it run LESS often. check_all is green on the real roster.

NET SCORE:
SK-1 — (a) fired this month? YES, observed directly: it adopted 10 renames in this
  session when 2 had been shown. (b) new failure mode? NO — a preview cannot damage
  anything, and the conjunction closes an adjacent one (a routine ingest renaming a
  deck as a side effect).
FOLLOW-ON deck 35 — (a) YES, continuously: two decks carried a permanent false
  "re-grade this" nudge, and a standing warning is one nobody reads, which degrades
  the ten real ones next to it. (b) NO — measured, and the negative control pins that
  the widen stays a rubric-language match.
Tally: 2 production fixes − 0 new failure modes = 2

OPERATOR ACTIONS / DEPLOY:
- Nothing blocking. If you have `--sync-names` in a shell alias or muscle memory on
  the Arena machine, it is now a preview; add `--apply` to write. | BLOCKS DEPLOY: N
Deploy: N/A — no deployed artifact changed (the dashboard's data pipeline and
template are untouched).

FOLLOW-ON ITEMS:
- **I deleted a `.bak` that was not mine.** Cleaning up after the Scenario 9 walk,
  `rm -f decks/16-water-spirit/*.bak` removed both my test backup AND a pre-existing
  one from this morning's rename run. Its content is `#: name: Water Spirit` and is
  recoverable from `4e94a2b^` (verified). Nothing was lost, and the other 14 `.bak`
  files in the repo are untouched — but a glob delete in a directory I did not
  inventory first is the mistake, and it is recorded rather than passed over.
- `_BELOW_FLOOR_ARGUMENT` matches 61 of 116 decks' `#: tier:` prose in the
  POPULATION, which looks like the G-07 saturation shape. It is not, today: the
  pattern is only consulted when a deck sits BELOW its floor, where it suppresses 52
  of 62. Worth a look if the suppression is ever reused somewhere less gated.
- Deck 35's tier LETTER is still a human call and was NOT changed (design
  constraint: never auto-write a tier letter). The deck's own prose says the scatter
  argument is weaker at 13 central themes than at the 20 it was written against, and
  invites a re-grade look. Nothing is broken if it stays B.

DOCUMENTATION UPDATES NEEDED:
- Unchanged from the previous block and deliberately NOT done here, since they were
  listed as doc updates rather than follow-on items and `/sync-docs` does a proper
  roster-wide pass: CLAUDE.md K-09 pool blanks (says 371, live 342) and C-02
  matches.csv rows (says 62, live 66). `check_docs` reports both on every run.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
