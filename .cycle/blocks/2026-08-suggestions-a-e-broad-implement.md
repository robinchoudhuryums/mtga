---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: suggestions A–E from the tooling-improvements report
- A1 | REFUTED BY MEASUREMENT, deliberately — the third pre-registered `cuts` fix to
  fail. The premise ("roles don't feed the fit term") was FALSE on inspection:
  `cut_keep_score` already carries `_role_credit`, saturation-aware and
  check_suggest-anchored. The candidate reweighting (base 3→6/role) fixed 0 of the 7
  named mis-ranks (the worst offenders are ZERO-role cards — a weight cannot multiply
  zero) while churning 28 of 116 decks' top-3 cut sets. Recorded in CLAUDE.md G-09
  ("Three fixes were pre-registered and REFUTED … don't derive a fourth") and the
  gotchas long form with the full numbers.
- A2 | `feedback` prints the surfaced-rate aggregate: 63/599 chosen adds (11%)
  appeared in suggest's top 20 beforehand — the single recommender health number,
  guarded by the 20-row sample floor, framed as a TREND (the level is dominated by
  structural picks the theme gate excludes by design, G-38).
- B  | `feedback` prints "Most tuned vs. least played" — swaps recorded vs matches
  recorded per deck, plus the ≥5-swaps/0-matches list (31 decks at measurement).
  Framed as a PLAY QUEUE with G-74's caveat built in (a phone game never reaches the
  desktop log, so 0 = unrecorded, not unplayed). Roster-shaped; suppressed under a
  deck filter. Report-only; the scoring-stack ledger ban untouched.
- C  | POLICY, per the owner's direction, not a build: current wildcard balances are
  out of scope for tuning entirely — never asked about, never weighed — factored in
  only when Robin raises them in that conversation. Codified in the Player Profile;
  the balance-stamp proposal recorded there as declined (any recorded balance
  invites the gating the paragraph exists to prevent).
- D  | SessionStart hook now runs `scripts/session_check.sh`: check_all always; full
  pytest only when scripts/tests/Makefile/pytest.ini changed (HEAD tree hashes +
  clean-worktree check) since the last GREEN run, sig stored gitignored at
  .cycle/.tests-green-sig. A dirty tree always reruns; a red run clears the sig. The
  tripwire that caught the DFC regression stays armed; the ~2–4 min per resume on an
  unchanged tree goes away.
- E  | Record-only: the pending operator/user items (stamp seed, ~/.zshrc watermark,
  prune-analysis keep/cut calls, deck 35 letter, Scenarios 5/7/10/11) were already
  named in CLAUDE.md's session-state section and NEXT-SESSION; nothing new to write.

Files modified: scripts/deck.py (cmd_feedback + _print_tuned_vs_played), CLAUDE.md
(Player Profile, G-09), docs/gotchas.md (G-09 long form), scripts/session_check.sh
(new), .claude/settings.json (hook repointed), .gitignore, tests/test_recommendations.py

TEST RESULTS: passed — pytest 1523 / 0 (+4); check_all all invariants hold (1
pre-existing soft warning, G-75); check_commands 35 + 33 reachable (session_check.sh
is .sh, outside the gate's *.py scope by design); check_docs 106 rules, caps clean
(the G-09 addition tripped the 15-line cap once and was compressed — the cap doing
its job).

REGRESSION RISKS:
- Hook: the skip fires only on (clean worktree ∧ unchanged HEAD trees ∧ prior green);
  every other state runs the full suite. Worst case is the old behaviour.
- feedback output grew two sections — report-only, sample-floored.
- None to scoring: A1 changed no production code at all.

INVARIANTS AT RISK: None.

NET SCORE: 3 production improvements + 1 measured refutation that prevents a bad
model change − 0 new failure modes = 4

OPERATOR ACTIONS / DEPLOY:
- Unchanged from before: seed the collection stamp; update ~/.zshrc mtga-matches;
  prune-analysis decisions; browser scenarios | BLOCKS DEPLOY: N
Deploy: N/A.

FOLLOW-ON ITEMS:
- The zero-role structural cards (Delney's evasion grant, Ouroboroid's combat
  counters) remain the one real path to better cut ranks — that is G-67 worklist
  territory and needs its own K-14 diff per family, not a weight.
- Watch the surfaced-rate trend once a few more tuning cycles accrue.

DOCUMENTATION UPDATES NEEDED: None — done in the same commit.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
