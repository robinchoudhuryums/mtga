---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
  F1b (Batch 2) — a cross-file agreement pair: the theme MODEL vs the corrected tag STORE
  F3  (Batch 2) — `figure_drift` extended past its 6 hand-kept entries with roster-shape figures
  Follow-ons    — K-09 and G-30 amended; ROADMAP's PROVISIONAL count re-measured

Files modified: scripts/check_agreement.py, scripts/check_docs.py,
  tests/test_gates_fire.py, CLAUDE.md, docs/gotchas.md, ROADMAP.md

CHANGES:

F1b | scripts/check_agreement.py | New pair `_agree_synergy_store` (pair 8), plus a
`("deck", "load_card_meta")` entry in REQUIRED so a rename fails the build rather than
silently skipping it. QUESTION: what themes does this card have? A =
`load_card_meta()[name]["synergies"]`, what every theme surface reads. B = `card-pool.csv`'s
own `Synergies` cell, the corrected store K-09 names. It deliberately does NOT compare the
two FILES — the library legitimately keeps stale tags (it is the inventory, not the tag
store), so a file-vs-file check would fail forever. A blank pool cell is skipped, matching
the loader. An empty model or a zero-comparison run is reported LOUDLY, per the discipline
`_agree_owned` records: a quiet pass is indistinguishable from a pair that never ran.

  This is the pair that would have caught BS9-01 the day BS8-31 shipped, and it belongs in
  THIS module specifically because no per-model gate could: `check_roles --tags` sweeps the
  POOL (comparing the corrected store with itself), `check_themes` is MISSING-only so an
  EXTRA stale tag is invisible by construction, and this module's own `_agree_weakest_cut`
  takes `load_card_meta()` as its shared INPUT, so both of its implementations inherited
  the same wrong tags and agreed perfectly.

  MUTATION-PROVEN, not assumed. Reverting `load_card_meta` to the pre-BS9-01 library-first
  loader makes the pair report 479 of 15,633 pool-tagged cards disagreeing; the current
  loader is clean. Four cases in `tests/test_gates_fire.py::TestCheckAgreementSynergyStore
  Fires`: quiet on the real repo, fires on library-first precedence, never counts a blank
  pool cell as a disagreement, and reports an empty model loudly rather than passing.

F3 | scripts/check_docs.py | Four roster-SHAPE figures added to `_live_figures` (6 -> 10):
the tier-floor spread's A / B / C counts and its top-band percentage. The six pre-existing
entries were all file-and-column counts, and the figure that actually went stale (F4, last
batch) was the sentence CLAIMED AS THE EVIDENCE for leaving `TIER_FLOOR_REQ` alone. Rule
adopted for what earns an entry: a figure a RULE cites as its evidence, and that a function
here can measure. Each regex is anchored on the words AROUND its own number and never on its
neighbours' values — otherwise correcting A silently kills B's and C's patterns, and a dead
pattern is reported while a wrong-but-live one is not. `tier_floor_spread()` is a ~2s
roster walk and is NOT memoized, so the four entries share ONE lazy call behind a closure;
`live_fn` only runs on a regex match, so a CLAUDE.md that stops making the claim pays zero.

  Mutation-proven: restoring the old numbers makes all four fire with the right
  stated-vs-live pairs (63/62, 43/45, 9/6, 61/55).

FOLLOW-ONS | CLAUDE.md, docs/gotchas.md, ROADMAP.md |
  * K-09 now records that "the pool is the corrected store" was true of the FILE and false
    of the MODEL until BS9-01, names the measurement (219 of 2,576; 105 of 113 decks) and
    the guard that holds it. The long form — including why no existing gate could see it,
    and that the fix was precedence rather than the prune mode the section predicted —
    is appended under `[K-09]` in docs/gotchas.md.
  * G-30 now records that `/tune-deck` deliberately does NOT run `deck.py rotation`: the
    recommendations ignore rotation so the human decides whether to run a card anyway. The
    rule's own "run it before a tune" is what would make a future session "fix" that back;
    a 2026-09-08 review read it as drift and was corrected by the owner. Long form under
    `[G-30]`.
  * ROADMAP's "of which 51 are PROVISIONAL" re-measured to **55**, and its trend line
    "(41 -> 51)" to "(41 -> 55)".

  BOTH CLAUDE.md BULLETS WERE ALREADY AT `check_docs`' 15-LINE CAP, so the amendments are
  net-zero rewrites: prose was tightened to make room and the detail moved to the evidence
  file, which is exactly the split the two files are for.

TEST RESULTS: passed. `python3 scripts/check_all.py` — All invariants hold, back to the one
pre-existing soft warning (4 dead library searches, G-75, accepted). pytest **1734 passed /
1 skipped**, up 5 from 1729: the four new mutation cases plus the PAIRS-parametrized test
picking up pair 8 automatically. The skip is test_app_editor.py's Flask importorskip.

  TWO SELF-INFLICTED BREAKS, both caught by the gates I was editing rather than by me:
  the new pair first errored on a missing `csv` import (caught by `check_agreement`'s own
  per-pair exception handler), and condensing K-09 broke `figure_drift`'s
  `baselined at (\d+) and soft in` pattern — twice, the second time because the phrase
  straddled a line break. `figure_drift` reported "PATTERN MATCHED NOTHING" both times,
  which is the self-report its docstring promises and a working demonstration of F3's
  premise.

REGRESSION RISKS: Runtime, measured. The additions cost +0.11s (the agreement pair, warm)
and +2.3s (figure_drift's roster walk) on a `check_all --quiet` that now runs 53.8s — ~4%,
paid on every SessionStart. `check_docs` now imports `deck`, but lazily inside the closure,
so no import-time cycle with check_all. No interface, return type or default changed;
`PAIRS` and `_live_figures` both grew by append, and the parametrized test over `PAIRS`
covers the new pair automatically.

INVARIANTS AT RISK: None. No CSV, deck file or derived artifact was written. `check_docs`'
own structural gate (required sections, anchor round-trip, per-bullet line cap) passes, and
the two amended bullets are back at exactly 15 lines.

NET SCORE: 0 production fixes − 0 new failure modes = 0
  Two DEFENSIVE/STRUCTURAL items (F1b, F3) and three DOCUMENTATION corrections. Neither
  guard fixes a firing bug — F1 fixed the bug last batch; these stop it returning and stop
  the next stale-evidence figure hiding. Recorded as 0 deliberately: under the old
  summary-block habit this batch would have read "5 − 0 = 5", and the gap between those two
  numbers is exactly the `defensive_count` bucket /reflect adds and this project has never
  tracked. First batch where that bucket is the whole story.

OPERATOR ACTIONS / DEPLOY:
- None.
Deploy: N/A for this batch — no Presentation-subsystem file changed (dashboard.html
untouched; the Pages workflow rebuilds on push to `main` regardless).

FOLLOW-ON ITEMS:
- Batch 3 (F2 sub-majority dashboard warning + Scenario 19; F5 wishlist roster_decks) and
  Batch 4 (F6 editor guard tests; F7 absent-token bypass) are untouched.
- `figure_drift` is 10 of ~1,100 numeric claims. The rule for what earns an entry is now
  written down; the registry is still hand-kept and its misses are still invisible.
- `tier_floor_spread()` is called twice per `check_all` run (the BS8-06 sweep and now
  figure_drift) and is not memoized. ~2s of duplicated roster walk; memoizing it would
  return that, and is a one-liner nobody has needed until now.

DOCUMENTATION UPDATES NEEDED:
- None outstanding — the three follow-ons in this batch WERE the documentation updates the
  Batch 1 block asked for.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
