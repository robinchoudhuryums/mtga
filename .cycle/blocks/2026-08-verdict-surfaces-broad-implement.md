---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: #1–7 from the deck-68b/49 tuning retrospective
- #1 | `deck.py move <id> "<card>" --section` — standalone verbatim relocation
  (dry-run default, .bak + total-preserving guard, NO recommendations row), plus the
  4 mechanical relocation rows pruned from recommendations.csv (603 → 599, .bak kept).
  The refused-"Ramp" attempt was verified to have left NO phantom row first.
- #2 | Verdict surfaces print their evidence by default: `screen`'s oracle text was
  already implemented but sat behind an opt-in `--full` that no skill and no session
  ever passed (the G-40 shape on a G-52 surface) — now default-on with `--no-text`
  opt-out; `card.py` ends every printout with `━━ end · <name> ━━` so a truncated
  pipe is visible (the 2026-08 sessions piped it through `sed -n '1,14p'` while
  grading — the partial-text read came from the INSIDE).
- #3 | `cuts` annotates `✚ NEWCOMER` on any card added to that deck by a ledger swap
  in the last 14 days — display-only via `recent_ledger_adds`, never inside the
  ranking (test_recommendations' structural scan untouched; the helper's docstring
  says why it must never be called from the scoring stack).
- #4 | Collection-freshness stamp: `lib.write_collection_stamp` (written ONLY by
  import_collection.py --apply, including the nothing-to-write branch — a verified
  match is a reconcile too) + `lib.collection_stamp_note` read by `deck.py check`
  (when craft targets print), `deck.py wildcards`, and `card.py`. Until the first
  exact reconcile it says plainly: owned counts are LOWER BOUNDS.
- #5 | `tapland_profile` + a report-only ⓘ line in `consistency`: N of M nonbasics
  enter tapped (unconditional vs conditional split), with the caveat that every
  figure above prices color ACCESS, not tempo. Registered both regexes in
  check_patterns (the completeness gate caught them unregistered — working as built).
- #6 | CLOSED AS NOT-A-HOLE, by measurement: token MAKERS (Hop to It, Head of the
  Homestead, Rapacious Dragon) are uniformly zero-role while Lathliss/Sally Pride
  score for their triggers on OTHER events — token creation is a tag, not a role,
  and the taxonomy is consistent. Desert Were-Worm / Dragonmaster Outcast stay
  baselined as deliberate zeros. Recorded under [G-67] in docs/gotchas.md.
- #7 | CLOSED AS NOT-A-BUG, against Scryfall live: Carnelian Orb of Dragonkind is
  genuinely `historic: not_legal`, and all 5 standard-but-not-historic pool rows are
  real Historic/Alchemy bans (Geological Appraiser, Leyline of Resonance…). The pool
  was right; the flag was wrong.

Files modified: scripts/deck.py, scripts/lib.py, scripts/card.py,
scripts/import_collection.py, scripts/check_patterns.py, recommendations.csv (−4 rows,
.bak), .claude/commands/apply-changes.md, CLAUDE.md (G-01, G-77, C-02 figure),
docs/gotchas.md (G-01, G-67, G-77 evidence), tests/test_deck.py, tests/test_lib.py,
tests/test_cli.py

TEST RESULTS: passed — pytest 1519 / 0 failed (+18); check_all all invariants hold
(1 pre-existing soft warning, G-75); check_patterns 284 live; check_commands 35
subcommands + 33 scripts reachable (`move` covered via apply-changes.md);
check_docs 106 rules, zero figure drift, caps clean. Mutation checks: stubbing
`recent_ledger_adds` to empty fails the cmd_cuts wiring test; screen asserted in
both directions (default prints text, --no-text suppresses).

REGRESSION RISKS:
- `screen` output is much longer by default — intended; `--no-text` restores the
  old shape, `--full` kept as a compat no-op.
- `check`/`wildcards`/`card.py` now print a standing ⓘ lower-bounds line until the
  first import_collection run — true and actionable, so not the G-78 class, and it
  self-clears on the run that fixes it.
- New `move` subcommand: dispatch + argparse only; no existing interface changed.
- cmd_cuts reads the ledger for DISPLAY — outside the seven scanned scoring
  functions by construction; the helper documents the boundary.

INVARIANTS AT RISK: None (no canonical CSV schema touched; recommendations.csv
edit was a row deletion through atomic_write with a .bak).

NET SCORE: 5 production fixes (+2 measured negative results that prevent future
false work) − 0 new failure modes = 5

OPERATOR ACTIONS / DEPLOY:
- Run `import_collection.py <tracker-export> --apply` once to seed the freshness
  stamp — until then the ⓘ lower-bounds note stands (deliberately) | BLOCKS DEPLOY: N
Deploy: N/A — no deployed artifact changed.

FOLLOW-ON ITEMS:
- The #3 model change proper (functional roles feeding the fit term so structural
  cards stop topping `cuts`) — needs a roster-wide K-14 diff; the annotation is the
  safe half only.
- The diagnosis question's standing answer: evidence opt-OUT on every future verdict
  surface; `screen` was the second G-52 regression of this class.

DOCUMENTATION UPDATES NEEDED: None — G-01/G-77/G-67 updated in both files this
commit; C-02 figure refreshed (72 matches).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
