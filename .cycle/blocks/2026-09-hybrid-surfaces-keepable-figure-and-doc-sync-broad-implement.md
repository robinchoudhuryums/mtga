---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (BS13's follow-on items, minus the tier letters, which are human calls):
  BS14-01 | `deck.py mana` told you a zero-source hybrid was "castable with any of their colors" — the sentence that made the deck-14 case look fine
  BS14-02 | `build_dashboard.py` split strict/hybrid itself, so the published page repeated the same blanket claim and became the only surface disagreeing with the model
  BS14-03 | The two G-26 residuals: KEEPABLE registered in `_figure_lookup`; the WORD-SPELLED figure measured and DECLINED

Files modified: scripts/deck.py, scripts/build_dashboard.py, CLAUDE.md, docs/gotchas.md,
  dashboard.html (rebuilt by `make postedit`)

CHANGES:
BS14-01 | scripts/deck.py (cmd_mana) | The hybrid report is source-aware. `deck_source_profile`
  was computed AFTER the report and is now computed before it, which is why the report could
  only ever speak in the abstract. Each hybrid row that binds prints
  `⚠ BINDS as {X} — no sources for Y`, the section header no longer promises "payable with
  EITHER color" unconditionally, and the hybrid-only count says how many of its symbols bind
  and points at `consistency`. Uses `binding_pips`, the same primitive the probability
  surfaces use, so `mana` and `consistency` cannot disagree. Deck 14 now flags all four.
BS14-02 | scripts/build_dashboard.py | Same rule on the published page: the per-deck source
  profile is computed, each hybrid entry carries `binds`, and the Mana panel renders
  `⚠ binds as {X}`. 34 hybrid entries flagged roster-wide. This follows the note already
  sitting three lines below the change, which records the identical failure for
  `#: uncastable-ok:` — "otherwise a deck reads BLOCKED here and READY there".
BS14-03 | scripts/deck.py | KEEPABLE joins `_figure_lookup` and gets two patterns. Nine
  percentage claims were in the roster's prose and NONE was verifiable, because every figure
  resolves through a lookup holding the quality vector, which has no probability term.
  `_keepable_at` is pure arithmetic over the land count, so this costs no per-card work, and
  the figure WILL drift — any manabase change moves it. Routed through `opening_land_stats`,
  the helper `consistency` prints from, so the two cannot disagree (G-70).
  BOTH patterns carry their own past-tense guard. The shared `_figure_is_history` reaches
  neither shape: it looks only BEFORE the match and only within 24 chars, while deck 35a
  writes "keepable was 80%" (cue INSIDE the match) and deck 51 writes "86.0% keepable; that
  figure was wrong" (cue AFTER it). Both were real false positives — 2 of 13 — and two
  permanent false warnings is the rate G-78 refused. After the guards: 11 matches, 0 false.
BS14-03 | DECLINED, with the measurement | The WORD-SPELLED figure ("six of it") is not built.
  A broad pattern returns 44 roster candidates at roughly 10–20% precision, because "one" and
  "two" are ordinary English ("Protection was the ONE", "the ONE weakness"). Narrowed to the
  unambiguous `<word> <axis>` form it gives 10 matches whose apparent failures are history
  ("it SCORED zero interaction UNTIL"), a hyphenate the regex split ("NEAR-zero"), and a
  claim about a different list that sits in `#: notes:` and is outside the scan by design.
  Also DECLINED: a per-card "N% on turn 5", which names one card in passing and so has no
  deck-level value to look up — guessing which card is meant is the guess this module refuses.
SYNC-DOCS | scripts/deck.py, docs/gotchas.md, CLAUDE.md | The premise "hybrids are excluded
  (strictly easier)" was stated in FOUR places and is now true only while both halves are
  live: `pip_depth_warning`'s docstring, the G-36 long form, CLAUDE.md G-32 (with the 41/27
  measurement) and G-36. G-26 records the copula and keepable as CLOSED, names the
  speed-qualifier exclusion, and states why the word-spelled half stays unbuilt.
  Writing G-26 pushed it to 347 words and the WORD_CAP added last cycle REFUSED it — the
  second time in two cycles that cap has caught its own author — so its narrative moved to
  `docs/gotchas.md` and the rule came back at 278.

TEST RESULTS: passed. Full suite **1813 passed / 0 failed / 0 skipped** (exit 0).
  `check_all.py` all invariants hold with the same single pre-existing soft warning; the
  rationale sweep stays clean and `check_docs` reports zero figure drift across 21 figures.
  `make postedit` exit 0, role baseline unchanged, dashboard rebuilt with the new flag.

REGRESSION RISKS:
- `cmd_mana` now calls `deck_source_profile` before printing rather than after. Same call,
  same arguments, one position earlier; nothing between the two points consumed its result.
- `build_dashboard` adds one `deck_source_profile` call per deck to a ~2-minute build. It
  completed in the usual time and the data island is unchanged apart from the new `binds`
  key, which is additive — an older cached page simply renders no flag.
- The keepable patterns can only ADD matches, and both carry a guard measured against the
  roster rather than assumed.
- A NOTE ON AN EARLIER MEASUREMENT: my BS13 sweep passed `load_collection()`'s indexes to
  `deck_source_profile` in the wrong order (it returns by_key, by_name). Checked rather than
  assumed — the profile falls back to `carddata`, which is name-keyed and complete, so the
  results are byte-identical either way and BS13's 41/27 figures stand. The correct order is
  used here.

INVARIANTS AT RISK: None. No data file written; no deck file touched this round. INV-03's
  dashboard content check passes on the rebuilt page.

NET SCORE: 2 production fixes − 0 new failure modes = 2
  BS14-01/02 are one bug on two surfaces and it fired this month: "castable with any of their
  colors" is the line that made deck 14 look fine while Long Feng sat at a true 52.5%.
  BS14-03's keepable half found 0 defects today but closes a class that drifts on every
  manabase change; counted as defensive, not as a fix. No new failure mode.

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — `.github/workflows/pages.yml` republishes `dashboard.html` on push to
  main, which is what carries the new hybrid flag to the published page.

FOLLOW-ON ITEMS:
- `deck.py mana`'s `△ Pip-intensive` lint still reads `parse_pips` strict pips directly, so a
  binding hybrid does not raise it. Out of scope here (that lint is a source-adequacy review
  signal, not a probability), but it is the last reader of the old split inside cmd_mana.
- G-43's 102/308-vs-63/213 population mismatch, `doubler_axis`'s single-axis return, and
  `cmd_suggest_homes`' positional tuple indexing remain open from earlier blocks.
- Open human calls: deck 27 (new RE-GRADE CANDIDATE), 45 and 47 tier letters.

DOCUMENTATION UPDATES NEEDED:
- None. The three items BS13 raised are done in this change.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
