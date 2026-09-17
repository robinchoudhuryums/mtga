---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
  BS12-01 | Move the measurement narrative out of the four CLAUDE.md rules that had outgrown the always-on budget (G-27, G-84, G-33, G-09), keeping the rule and every live residual
  BS12-02 | Extend `check_docs.figure_drift` from 14 registered figures toward the ~40 live claims, so a stale number is reported rather than noticed

Files modified: CLAUDE.md, docs/gotchas.md, scripts/check_docs.py, tests/test_check_docs.py

CHANGES:
BS12-01 | CLAUDE.md, docs/gotchas.md | Four rules trimmed, narrative moved to their `[G-nn]`
  sections. G-27 648 -> 266, G-84 551 -> 276, G-33 384 -> 226, G-09 367 -> 286; total
  1950 -> 1054 (-896 words). docs/gotchas.md +1229 words, so this is a MOVE, not a delete —
  and net the project gained prose. What that buys is the ALWAYS-ON budget: CLAUDE.md loads
  every session (24,377 -> 23,506 words), gotchas.md is opt-in. G-84's long form was an
  11-word STUB and G-27's was HALF its CLAUDE.md copy, so two of the four had to be written
  rather than relocated; checking that first is what stopped this being a lossy delete.
  Kept in every case: the rule, the live residuals (G-33's POWER-scope KNOWN GAP, G-09's
  Lunar Insight and the report-only stance, G-27's exclusion-window residual and the
  twice-DECLINED `#: notes:` scan, G-84's front-only rejection and unbuilt NAMED-type half)
  and every decision a reader could otherwise re-propose.
BS12-01 | scripts/check_docs.py, tests/test_check_docs.py | THE CAP THAT SHOULD HAVE
  PREVENTED THIS MEASURED THE WRONG QUANTITY. A 15-LINE cap on split-section bullets has
  existed for cycles, with the exactly right message ("that length means the evidence has
  moved back in"). Line count is a property of the FORMATTING: a bullet evades it by not
  wrapping. Measured — all four of the longest rules PASSED it, and two (G-84 at 551 words,
  G-83 at 269) sat on a SINGLE line. Worse, it punished the fix: wrapping the trimmed G-84
  to a readable width turned a passing 1-line rule into a FAILING 21-line one, which is how
  the defect was found. Now WORD_CAP = 300, derived from the distribution (p90 is 224, so
  300 targets outliers, not ordinary rules) and firing on exactly the four rules this
  finding names. Test doubles updated in the same change, plus a new case pinning that the
  same text fails whether wrapped or not.
BS12-02 | scripts/check_docs.py | Registry 14 -> 21 figures. Added: G-83 cost-scale pool
  cards, G-80 granted-evergreen pool cards, K-03 type-matters tags AND cards, G-22 applied
  swaps with a rank AND median add rank, C-07 test files. Each routes through the REAL
  predicate (`cost_scale_resource`, `granted_keywords`, `_TYPE_MATTERS_RES`,
  `deck.load_recommendations`), never a second copy — the registry's own standing rule.
  Three earned a note: G-80 is scoped to the TWELVE evergreens the prose names, because
  `_GRANTED_KEYWORDS` has held SEVENTEEN since 2026-09-02 and counting the list would
  silently answer a different question (2000 vs 1,942); K-03's patterns are CASE-SENSITIVE
  and read `_clean_text` un-lowered, since lowercasing first returns a clean ZERO, the shape
  that reads as a finding rather than a bug; and the G-22 pair is read through the ledger's
  real accessor and is a DOC gate, so it sits outside the G-56 ban that
  `tests/test_recommendations.py` enforces on scoring functions.
BS12-02 | CLAUDE.md | FIVE of the seven new figures were ALREADY STALE when registered, plus
  a sixth in the same sentence: G-80 1,941 -> 1,942; K-03 196 -> 277 tags and 180 -> 193
  cards; G-22 783 -> 816 swaps, median 407 -> 420 and the top-20 share 10% -> 11%. All six
  re-grounded. That five of seven had rotted unnoticed is the argument for the registry
  rather than against it.

TEST RESULTS: passed. Full suite 1810 passed / 0 failed / 0 skipped (exit 0) — one more than
  the previous run, the new no-evasion cap test. `check_all.py` all invariants hold with the
  SAME single pre-existing soft warning (three accepted dead tutors). `check_docs.py`: doc
  structure OK, 112 rules linked, and ZERO figure drift across all 21 registered figures.

REGRESSION RISKS:
- The cap changed quantity (lines -> words), so a bullet that passed before can fail now.
  That is the intent, and it was measured: after the four trims NO rule exceeds 300 words
  (longest remaining G-42 at 298). `LINE_CAP` is gone; the one test double referencing it
  was updated in the same change rather than reactively.
- BS12-01 is prose only and cannot affect a model. The risk is INFORMATION LOSS, which was
  managed by reading each long-form section first: two of the four were thinner than their
  CLAUDE.md copy and were written up rather than assumed to exist.
- figure_drift is SOFT and non-gating by design, so a newly registered figure can never
  break a build; the worst case is a warning. New helpers are cached and share one pool
  read; the ledger walk is O(rows).
- No scoring path reads any of this. `check_docs` imports `deck` and `tag_synergies` at
  measure time only.

INVARIANTS AT RISK: None. No data file written. INV-01..06 untouched; `check_all` confirms.

NET SCORE: 2 production fixes − 0 new failure modes = 2
  BS12-01's cap defect had fired this month by construction (four rules had grown past it
  unchallenged). BS12-02 caught six stale figures live. No new failure mode: the cap is
  stricter but measured to fit, and figure_drift stays soft.

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: N/A — Documentation and Analysis ship by commit/push; Presentation untouched.

FOLLOW-ON ITEMS:
- G-43's "102 of the pool's 308 split / Adventure / Room cards" was NOT registered. Measured
  live through `split_back_offcolor` it reads 63 of 213, because 308 counts the family
  BEFORE the cast-from-hand gate while 213 counts it after — two populations in one
  sentence. Registering a number that does not mean what the prose means is worse than
  leaving it, so this needs the original derivation before it can be gated.
- ~19 live claims remain unregistered (the rot surface was ~40, of which 21 are now covered).
  The remaining ones mostly need a roster walk or a predicate that does not exist yet.
- K-15's "427 pool cards" describes a REJECTED design (what `_TYPE_MATTERS` would have
  matched for artifacts), so there is no live predicate to route it through. Unregisterable
  as written.
- CLAUDE.md's "~1,179 numeric tokens" are mostly dated history and cannot rot; only the
  ~40 live-shaped claims matter. Worth stating in the file so no future pass tries to gate
  all of them.

DOCUMENTATION UPDATES NEEDED:
- STILL OUTSTANDING from the previous block, deliberately NOT done here to respect scope:
  G-33 should record the doubler active-voice branch, and G-31 should name the new
  `suggest-homes` KEY-saturation warning. G-33 was rewritten by THIS change without adding
  them, which is a scope call, not an oversight.
- The WORD_CAP switch is worth a line wherever the CLAUDE.md/gotchas.md split is described,
  so the next writer knows the budget is 300 words and why it is not lines.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
