---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: feedback segmentation — split `deck.py feedback`'s agreement
rate by creature vs noncreature cut, because the pooled 63% averaged a 90%
(noncreature, n=21) and a 45% (creature, n=31) regime.
Files modified: scripts/deck.py, tests/test_recommendations.py,
decks/41-darkforce-inversion/deck.txt,
decks/42-blood-price/42a-orzhov-aristocrats.txt

CHANGES:
feedback-segmentation | scripts/deck.py | New pure `recommendation_segments(rows,
  is_creature)` returning {segment: (n, agreed, median)} keyed creature /
  noncreature / unknown, plus `cut_creature_classifier(carddata)` (front-face DFC
  aware) and `_print_recommendation_segments`. Each segment is held to the SAME
  `_RECS_MIN_SAMPLE` floor as the pooled rate; a thin segment prints its n and no
  rate. The classifier is INJECTED so the summary stays pure and testable. An
  unclassifiable card is its own `unknown` bucket, never folded into `noncreature`
  — defaulting it would corrupt exactly the segment that reads as calibrated.
feedback-segmentation | tests/test_recommendations.py | New TestSegments (7 tests):
  the split, unknown-is-not-noncreature, unrankable rows excluded, the agreement
  boundary matching recommendation_summary at pct == 0.5, the per-segment sample
  floor, the positive two-segment case, and DFC front-face resolution.
prose (factual) | decks/41 | tier rationale quoted card advantage 5; live is 6.
prose (factual) | decks/42a | tier rationale said "Hero's Downfall and Erode stay";
  Erode was cut for Ruthless Lawbringer this session. Rewritten with the change-cue
  ADJACENT to the name so the audit reads it as history.

TEST RESULTS: passed — 651 pytest (+7), check_all "All invariants hold. ✓",
check_patterns 145 live, check_commands OK (33 subcommands / 30 scripts).
MUTATION-TESTED: four mutations (fold unknown into noncreature; drop the
per-segment floor; move the agreement boundary to `< 0.5`; suppress the
explanatory warning) each fail exactly one test. The floor mutation initially
PASSED — the first draft of that test used fixture names that are not real cards,
so every row bucketed as `unknown`, no split could print, and it passed
vacuously. Fixed by injecting a synthetic card universe via load_card_data.

REGRESSION RISKS: None. `recommendation_summary` is untouched and its callers are
unchanged; the new print sits inside the existing `n >= _RECS_MIN_SAMPLE` branch,
so a small-sample or empty ledger takes the same path as before. `deck.py feedback
<id>` re-verified on a filtered deck.

INVARIANTS AT RISK: None. No CSV writer, no derived file, no deck-file parsing
touched. The two deck edits are `#:` header prose only; INV-04 re-verified via
check_all.

NET SCORE: 1 production fix − 0 new failure modes = 1

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: N/A for the analysis change (local tooling ships by commit). The two deck
files feed the Pages dashboard, which rebuilds automatically on push to main.

FOLLOW-ON ITEMS:
- `tier --audit-rationale` FALSE NEGATIVE, found while answering the tier question
  and NOT fixed (out of scope). Deck 42a's prose asserted "Hero's Downfall and
  Erode stay" after Erode was cut, and the audit reported the deck clean: a
  `_HISTORY_CUES` change-cue about a DIFFERENT card ("Heartless Act was CUT …")
  sat inside the ±140-char window and suppressed the Erode citation one clause
  later. The suppressed clause says the card STAYS — an explicit present-tense
  assertion of current membership. Proposed fix is the mirror of
  `_cites_as_arriving`: un-suppress a citation carrying a STAY marker
  (stays / remains / keeps / is kept), since that is the opposite of a history
  claim. Needs a roster-wide sweep before landing, per the cue-list rule.
- `cuts` ranks creatures at a 45% agreement rate. NOT a re-weighting candidate:
  normalizing the fit sum was simulated across all 64 decks and does not work
  (top-3 themes +0.72 vs +0.73 current, 1% top-5 shortlist churn; mean-of-hits
  +0.60). The effect is that tag count proxies for "described by the tag
  vocabulary at all", which is CLAUDE.md's already-documented raw-power residual.
  Reporting it is the fix; re-weighting off the ledger is also what
  tests/test_recommendations.py structurally forbids.
- correlation(tag count, keep-rank) = +0.73, positive in 64/64 decks — worth
  recording as a measured property of `cuts` if it is not already.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md: the recommendation-ledger paragraph should note the segmented report
  and the measured 90/45 split, and the `cuts` paragraph should record the
  unnormalized-fit-sum property (+0.73) as a known characteristic.
- The `tier --audit-rationale` residual paragraph should gain the STAY-marker case
  alongside the existing `_cites_as_arriving` one.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
