---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: 
- S2-01 | dashboard's "Log a match" panel read three CSS custom properties NO theme defines
- S1-01 | .cycle/NEXT-SESSION.md §0-current declared the CLOSED TRK printing question "UNRESOLVED"
- S2-02 | `make postedit` ran the acknowledge step BEFORE the gate that reads it (G-69's own shape)
- S1-02 | `swap --section` / the G-05 advisory used raw name equality where `_swap_edit_lines` uses `_ms_key`
- S1-04 | the role radar reported a DELTA and never the LEVEL — 26% of the roster is invisible to `classify_roles`
         (report-only half taken; the TAXONOMY half deliberately NOT taken — K-14 diff below)

Files modified: scripts/build_dashboard.py, dashboard.html, scripts/deck.py,
scripts/check_roles.py, Makefile, docs/verify-commit-tail.md, .cycle/NEXT-SESSION.md,
tests/test_templates.py, tests/test_deck.py, tests/test_check_roles.py

CHANGES:
S2-01 | scripts/build_dashboard.py, dashboard.html, tests/test_templates.py |
  Renamed `--acc` -> `--accent`, `--dim` -> `--ink2`, `--fg` -> `--ink` (5+4+3 uses). No
  `:root` block in EITHER theme defined the three names used; both themes define all 27
  of the real ones, so this was never a light/dark gap. Effects, all silent because an
  undefined custom property is invalid at computed-value time rather than a parse error:
  `.segbtn.on` fed `--acc` to `color-mix()`, making the whole `background` an invalid
  VALUE, so the SELECTED W/L/D and Play/Draw button shipped with no fill and no accent
  border; four `outline:2px solid` rules fell back to `currentColor` and, being MORE
  SPECIFIC than the page's global `:focus-visible`, overrode a working rule with a broken
  one (the queue row's ✕ ring rendered red, since the same rule sets `color:var(--bad)`);
  the field labels lost their muted tone. Rebuilt the committed page (2m46s) — the
  artifact now resolves 43/43 tokens.
  NEW GATE: `TestGeneratedPagesDefineEveryTokenTheyUse` asserts used ⊆ defined across the
  generator plus all five shipped pages, with a watched-it-fail case built from the exact
  shape that shipped and a `var(--a, var(--b))` fallback-chain case. This is worth having
  where G-72's a11y gate was measured unbuildable: that one asks a BEHAVIOURAL question a
  file cannot answer, this asks a REFERENTIAL one with no legitimate negative form.
  Caveat, hit during implementation and recorded in the source: the scan reads raw source,
  so PROSE quoting `var(--undefined)` trips it. The incident comment therefore names the
  tokens bare. Fails loud with a naming message; one-word fix.

S1-01 | .cycle/NEXT-SESSION.md, docs/verify-commit-tail.md |
  §0-current's "UNRESOLVED AND RECORDED NOWHERE ELSE: the TRK printing question" (109 deck
  lines, "cheapest next step: paste one affected deck into Arena") was closed by commit
  e269b5e, which landed AFTER 00a6975 wrote the handoff. Verified: 0 `(TRK)` lines under
  decks/ (was 109 across 47 files), 0 TRK rows in card-library.csv (was 2), 0 future-dated
  card-pool.csv rows (was 114). Rewrote the section as CLOSED, keeping the cause and the
  live residual (a custom `--query` is not rewritten with `date<=now`, so a hand-built pool
  re-opens it) and pointing at G-79 for the long form.
  STRUCTURAL HALF: `docs/verify-commit-tail.md` gains step 4 — close what you closed in
  §0-current, in the same commit. That file is the tail every writing skill already runs,
  and nothing gates this (`check_docs` proves anchors resolve, not that a claim is true).

S2-02 | Makefile, scripts/check_roles.py |
  postedit was `--update-baseline` -> dashboard -> check_all. `check_roles.check()` is
  defined as "zero-role cards NOT in the baseline", so rewriting the baseline first made
  it return 0 BY CONSTRUCTION and check_all's soft sweep had nothing to report for the
  cards a tune had just added. Measured: 490 zero-role, 490 baselined, sweep silent.
  Reordered to dashboard -> check_all -> `--update-baseline`. The old order's rationale
  was real and is preserved in the comment (consuming the warning is what the step is FOR);
  what changes is that the gate now runs BEFORE the rewrite, so both halves of G-69 hold.
  Side benefit: a failing check_all now aborts the recipe before the baseline is touched.
  Cost: one TRUE soft warning per run that introduced a roleless card.

S1-02 | scripts/deck.py, tests/test_deck.py |
  `_relocate_card_line` and `_do_swap`'s post-write advisory lookup both used raw
  `.lower()` equality while `_swap_edit_lines`, in the same code path, uses `_ms_key`
  (G-63) — 59 roster deck lines carry a full `Front // Back` name. Reproduced against the
  real deck 53 file: `_relocate_card_line(lines, "Funeral Room", "Lands")` raised
  "appears on 0 card line(s)", and because relocation runs inside `_do_swap`'s write
  `try`, that ABORTED THE WHOLE SWAP; without `--section`, the G-05 advisory was skipped
  without saying so. Both routed through `_ms_key`. Verified end to end: bump onto an
  existing full-name line + advisory + `--section`, all resolving from the front-face
  spelling, with the multiset of lines unchanged (the move stays VERBATIM, so G-65's
  printing fields cannot be retyped).

S1-04 | scripts/check_roles.py, tests/test_check_roles.py | REPORT-ONLY half only.
  Added `role_coverage()` / `_coverage_line()` and printed it on both CLI paths. The radar
  reported only the delta ("No new zero-role cards"), which reads as a clean bill for a
  number nobody had looked at — the audit had to derive 491/1873 (26%) with a throwaway
  script. Now printed as a level beside the delta, and (with S2-02's reorder) it is the
  LAST line `make postedit` emits. Kept OUT of `tier_band` on the same rule as the
  protection axis (G-25) and the X-cost advisory (G-60): a new term there would silently
  re-grade the roster.

TEST RESULTS: PASSED.
  - `python3 scripts/check_all.py` (the Test Command): "All invariants hold. ✓", 1 soft
    warning — the four ACCEPTED dead tutors the handoff documents as expected. Unchanged
    from the pre-change baseline; no new soft warning.
  - `pytest`: 1477 passed, 0 failed, 0 skipped (211s). +15 test instances across three
    files. Pre-change run in the same session was also green.
  - Regression Scenario 2 (Analyze a deck | Deck Tooling Correctness — the scenario whose
    subsystem overlaps deck.py): PASS. 30 invocations, 0 tracebacks — the full per-deck
    command set, `suggest --lands/--ramp/--interaction/--needs`, `screen`, `feedback`,
    roster-wide `audit`/`similar`/`rotation`/`resolve`, `pool.py --role`, and both help
    surfaces.
  - Scenarios 1, 3, 4, 9: NOT APPLICABLE — no ingest writer, no refresh step, no app.py
    and no match parser was touched; 1/3/9 also need a paste, the network, or a real
    Player.log.
  - Scenarios 5, 6, 7, 8: NOT APPLICABLE to automation — all four are explicitly "a person
    at a browser". S2-01 changes what Scenario 5's palette renders as, so it needs a human
    walk; the new Scenario 10 below is the targeted version.

REGRESSION RISKS:
  - deck.py `_relocate_card_line`: `_ms_key` collapses front and full spellings, so two
    lines in ONE deck sharing a front face would now REFUSE ("appears on 2 card line(s)")
    where raw matching moved one. Measured across all 116 decks: 0 such clashes. Refusing
    is the conservative direction and matches the function's existing two-line refusal.
  - Makefile postedit: a run that adds a roleless card now emits a soft warning it did not
    before. Intended — that warning existing is the fix. It is TRUE, not the permanent
    false noise G-78 refuses, and it clears itself on the same run's step 3.
  - build_dashboard.py: template-only, per C-10. The `#data` island and the data pipeline
    were not touched; `collect()` and `deck_detail()` are unmodified.
  - check_roles.py: `check()`, `zero_role_cards()` and `baseline_delta()` are unchanged, so
    check_all's consumption is byte-identical. The two new functions have no callers
    outside the CLI print sites and the tests.
  - No interface, return type or default value changed anywhere.

INVARIANTS AT RISK:
  - INV-03 (derived files exist AND carry usable CONTENT) — the only one touched, because
    dashboard.html was rebuilt. CHECKED and holding: 1,897,955 bytes with the `#data`
    island present, which is both what INV-03 asserts and what pages.yml verifies before
    publishing. gallery.html unchanged and also OK.
  - INV-01, INV-02, INV-04, INV-05, INV-06: not at risk. No CSV and no deck file was
    written this session (`git status` confirms: no `decks/` and no `*.csv` entries); the
    role baseline was re-written once as a verified byte-identical no-op.

NET SCORE: 3 production fixes − 1 new failure mode = 2
  a) Would it have fired in production this month?
     S2-01 YES — live on the deployed page right now. S1-01 YES — any fresh session
     reading the handoff. S2-02 YES — every postedit run after a deck edit.
     S1-02 NO — real, but needs `--section` plus a bumped DFC line under the other
     spelling; no evidence it fired. S1-04 not a bug (a visibility gap).
  b) New failure mode?
     One, documented: the token gate false-positives on PROSE that quotes an undefined
     `var(--x)`. Hit during this implementation, handled by naming tokens bare, and
     recorded in build_dashboard.py's comment. Fails loudly with a message that names the
     token; one-word fix. Counted rather than waved off.

OPERATOR ACTIONS / DEPLOY:
- Walk NEW Regression Scenario 10 (below) in a browser — the S2-01 palette has never been
  rendered by a person with the tokens correct, and the fill/ring/label distinctions are
  perceptual by nature | BLOCKS DEPLOY: N
- Decide the S1-04 taxonomy question (see FOLLOW-ON) — a human call per the tier rubric,
  since it moves tier FLOORS | BLOCKS DEPLOY: N
Deploy: Presentation subsystem [C-10] — no command to run. `.github/workflows/pages.yml`
rebuilds build_dashboard.py offline and republishes to GitHub Pages automatically on push
to `main`; its pre-publish check (non-trivial size + `#data` island) was verified locally
against the rebuilt page and passes. Data + local tooling ship by commit/push, no build step.

FOLLOW-ON ITEMS:
- S1-04 TAXONOMY HALF — NOT TAKEN, DELIBERATELY, and here is the K-14 diff it needs.
  CLAUDE.md is explicit that adding a role bucket "re-scores every deck running the type,
  so take it deliberately with a K-14 diff, not as a pattern slip-in", and the rubric says
  never auto-write a tier letter. Measurements, all read-only:
    · The 491 zero-role roster cards are NOT one bucket. 400 are a long tail (291 creature,
      109 noncreature) with no shared shape. The named blocks are small: Equipment 31,
      hand-attack 31, Aura 9, tap-down 8, ability-strip 6, extra-combat 5, vanilla 1.
    · NEUTRALIZATION IS ALREADY CLOSED. Decks that would gain interaction from a
      "doesn't untap / loses all abilities" bucket: ZERO. §0-latest's open item ("Six decks
      under-count interaction: 15 by 2; 16, 27, 32, 38a, 38 by 1") appears to have been
      resolved by the G-67 patterns landing — worth confirming and closing there. That is
      the S1-01 shape again, one file over.
    · The one RISKY candidate is hand-attack. If bucketed as interaction: 27 decks
      re-scored and 3 tier FLOORS move — deck 22 (4->5, B->A), 22-brawl (4->5, B->A),
      deck 73 (5->6, B->A). That is a human re-grade, not a pattern fix.
    · Equipment (31) maps to neither graded axis, so it moves no floor. It is the
      lowest-risk bucket if one is wanted.
- §0-latest's "six decks under-count interaction" item is likely stale (see above).
- CLAUDE.md's Subsystems inventory omits `.github/workflows/integrity.yml` — the workflow
  with the broadest trigger (every push) and the home of the CLI smoke step G-55 cites.
  Reported as S1-05; out of scope for this pass.
- CLAUDE.md [C-02]'s match figures read "pooled 28-30" against an actual 31-31 (and 59
  attributed across 24 decks, not "55+ / 23+"). Reported as S1-06; out of scope.
- matches.csv's four hand-only columns are empty in all 62 rows (S1-03). The S2-01 fix is
  a precondition for that panel being usable; whether the loop closes is unknown until a
  person walks Scenario 11.

NEW REGRESSION SCENARIOS (adopt into CLAUDE.md):
10. Log-a-match panel — selected state and focus ring | Subsystem: Presentation & Interface
    Steps: open dashboard.html, expand "Log a match" (starts collapsed); click W, L, D and
    then Play / Draw; Tab into the Deck select, the Opponent input, each segment button and
    a queued row's ✕; repeat in the other theme (press `t`).
    Expected: the selected segment has a visible tinted FILL and an accent border, clearly
    distinct from its neighbours — not just a colour change in the label. Field labels
    (DECK, RESULT, ON THE, …) read as muted against the value. Every focus ring is the
    accent purple used elsewhere, and the ✕ ring is accent, NOT red. A fill-less "on"
    segment or a red ring means the panel regressed off the shared tokens (S2-01). This
    palette has never been rendered by anyone with the tokens correct.
11. Log-a-match end to end on a phone | Subsystem: Presentation & Interface / Outcomes
    Steps: at 390×844 queue two matches with different decks, a `why` and a note; RELOAD;
    confirm the queue survived; Copy all; feed the block to `parse_matches.py --add`
    (dry run, then APPLY=1); `--report`.
    Expected: no sideways body scroll, one column, queue survives reload; Copy all either
    copies or focuses-and-selects the textarea with the "Select-and-copy the box below"
    toast (a file:// open is not a secure context, so the fallback is the EXPECTED path);
    `--report`'s manual-axis section shows a non-empty Loss Reason tally for the first
    time. This is the acceptance test for S1-03.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-69 still describes the pre-S2-02 order as current ("`make postedit` ran
  `check_roles.py --update-baseline` unconditionally and FIRST"). The incident is history
  and stays; the sentence needs a "fixed in broad-scan-7: acknowledge runs LAST" clause.
- docs/gotchas.md [G-69] (around line 4277) needs the same clause plus the S2-02
  measurement (490/490 baselined, sweep silent).
- README.md ~line 1305 lists postedit's steps in the OLD order ("re-baseline roles, …").
- CLAUDE.md G-72 / Regression Scenario 5 should mention the new token gate, and the
  Presentation subsystem [C-06] / Testing [C-07] inventories should name it.
- CLAUDE.md's Regression Scenarios need the two new scenarios above.
- A new gotcha is earned by S1-01 and is not yet written: a handoff that IS read and is
  wrong is worse than one that is not read. `docs/verify-commit-tail.md` step 4 carries the
  rule; CLAUDE.md's "Session state" section should point at it.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
