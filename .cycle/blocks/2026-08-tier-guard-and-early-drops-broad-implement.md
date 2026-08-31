---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: two of the three tooling holes left open by the 2026-08-31 deck-59
session. (A) the tier under-grade suppression nagging 7 of the 10 decks it flagged;
(B) `early_drops` counting a cheap mana source as a cheap threat, in the display a human
reads AND in the aggro `_clock_score` that can float a tier floor.
A third — scanning `#: notes:` for stale live claims — was BUILT, MEASURED and REVERTED;
the measurement is the deliverable and is recorded under [G-27].

Files modified: scripts/deck.py, scripts/check_patterns.py, tests/test_deck.py,
docs/gotchas.md, CLAUDE.md

CHANGES:
(A) | scripts/deck.py | `_BELOW_FLOOR_ARGUMENT` spelled the RUBRIC's vocabulary ("below
the floor", "PROVISIONAL", "≤1 weakness"); the roster writes its own idiom. Measured
across 114 decks: 62 sit below their floor, 52 were suppressed and 10 flagged — and SEVEN
of the ten argue the cap in the held-by family ("Held at B, not A, by the real gap",
"Residual cap: singleton inconsistency", "WHAT CAPS IT IS THE ZERO-PROTECTION FLAG",
"Three weaknesses, where A allows one"). A 70% false-positive rate on a STANDING warning
is the saturation shape G-07 measured on `audit`'s review flag, and the reason nobody
reads it. Widened with that family plus `letter stays/is held` and `capped`.
The OVERRIDE (`_WANTS_UNDER_GRADE_FLAG`) is the load-bearing half and the reason the widen
is safe: the other THREE (7, 19, 23) argue the cap AND defer the call in the same block —
"RE-GRADE CANDIDATE, and the argument for B has now expired", "the letter stays B pending
the human call the flag asks for", "HELD at B pending a human re-grade" — so widening
alone would have silenced precisely the decks asking to be prompted. Checked AFTER the
argument cues, so a deck can hold at B by a stated reason and still be flagged while it
calls that reason provisional. RESULT: 10 flagged → 3, all 7 flips one-directional, no
deck moving the other way. The weakness COUNT cue is band-relational
(`… weaknesses …{0,40}(where|than|past what|allows|tolerat)`) because an existing test
pins that a bare "two weaknesses, both covered by the sideboard" must NOT suppress —
the pattern's own "narrow on purpose" note, enforced.
(B) | scripts/deck.py | `early_drops` is "nonland cards MV ≤ 2, quantity-weighted", so a
turn-two mana dork and a turn-two beater are one number. TWO consumers read it as though
they were the same: the figure a human argues from (deck 59's "nine early drops", four of
which tap for mana — a curve argument I made in chat off the tool's own number and
reversed on a hand recount) and `_clock_score`, the term that lets an AGGRO plan
substitute speed for the interaction the resilience floor demands. A ramp deck declaring
`#: plan: aggro` with twelve cheap mana sources would have collected full clock credit for
a board that does nothing — the deck-56a shape, an input that looks like a description and
behaves like a grade. `_MANA_SOURCE_RE` reads the mana ability off card TEXT with reminder
text stripped (the `granted_keywords` discipline: read what the card does, don't trust a
field). `deck_quality_vector` carries `early_mana`; `_clock_score` subtracts it;
`quality` and the `cuts`/tune short-axis line render `9 (4 mana sources)`.
K-14 DIFF: **0 of 114 decks change tier band.** No deck currently on an aggro plan has a
mana-dense early curve, so the `_clock_score` half buys nothing today and exists so a
future ramp deck cannot buy a band it has not earned. The DISPLAY half changes six decks;
deck 17 reads 12 early drops of which SIX are mana, which is a different deck than "12".
The bare int still feeds `tier_band` and the F10 guard, and the rationale-figure audit
still compares a quoted "N early drops" against the total — that is what the prose means.
(C, REVERTED) | scripts/deck.py | `#: notes:` staleness. Built `_notes_live_claim` (a
citation in a clause that ALSO names a card the deck runs is an enumeration, i.e. a claim
about the current list) and `_notes_list_history` (a list header governs its whole clause,
since `_cites_as_history`'s ±140 window loses a long `OUT: A · B · C …`). Measured 81
roster hits at ~45% precision, 61 after the second gate — and the second gate also drops
REAL hits. What settled it: neither variant catches the motivating case. Reconstructed
deck 59's pre-fix clause — "…The Last Agni Kai and Ancestors' Aid — Rough Rhino Cavalry
and its {8} exhaust were CUT 2026-08-31 for Hugs." — and both return []. The change-cue
for a DIFFERENT card sits ~45 chars away inside the same clause. The suppressions that
make the tier/archetype scan trustworthy are exactly what blind it in a build log, which
is what a build log IS. Reverted rather than shipped behind a flag.
Gates/tests | check_patterns.py, tests/test_deck.py | check_patterns caught BOTH new
regexes unregistered, as designed — `_MANA_SOURCE_RE` registered against the live pool
corpus, `_WANTS_UNDER_GRADE_FLAG` excluded with a reason (it reads tier PROSE, like its
`_BELOW_FLOOR_ARGUMENT` sibling). Nine tests added across two classes; all four behaviours
mutation-checked (clock reading the whole count, the missing override, the missing
held-by cues, the render dropping the split) and each watched to fail.

TEST RESULTS: passed — full pytest suite exit 0; `check_all` all invariants hold (two
pre-existing soft warnings: the stale committed dashboard and the four known dead library
searches); check_patterns 288 live; check_docs OK; `deck.py --help` and a subcommand help
both clean.

REGRESSION RISKS: (A) is a SUPPRESSION widen, so its failure mode is silence — a genuinely
under-graded deck whose prose happens to say "capped" would no longer be nudged. Bounded
by the measurement: all 7 flips were graded by hand against the full `#: tier:` block, and
the deferral override keeps the three decks that want the prompt. (B) touches a
`tier_band` INPUT, which CLAUDE.md is emphatic about — mitigated by the 0/114 diff, by
`.get("early_mana", 0)` so a hand-built or pre-existing vector behaves exactly as before
(pinned by a test), and by leaving the rationale-figure audit reading the total.

INVARIANTS AT RISK: None — no data file is written, no derived file rebuilt, ENGINE_THEMES
untouched so the pool build stamp is unaffected.

NET SCORE: 2 − 0 = 2

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — no Deploy Command configured (tooling ships by commit/push).

FOLLOW-ON ITEMS:
- The `#: notes:` residual STANDS and is now measured rather than assumed: a live claim in
  that header goes stale silently, and the only thing that finds it is reading the header
  after a swap. The numbers in [G-27] are the bar for a future attempt.
- Still open from the prior block: `_TARGET_GATES` is a whitelist of gate SHAPES (G-67 one
  layer over); the teamwork gate family is n=1 in the pool and declined as over-fitting;
  Party Dude's opponent-BOARD condition is outside `target_counts`' model rather than a
  hole in it; `_RATIONALE_MIN_LEN = 9` hides short single-word citations (G-78, measured
  and left); the 445-entry zero-role baseline.
- Decks 7, 19 and 23 remain flagged as possibly under-graded BY THEIR OWN REQUEST. Each
  needs the human call its rationale defers — that is a tiering decision, not a tooling one.

DOCUMENTATION UPDATES NEEDED:
None — done in this batch: new [G-81] section in docs/gotchas.md plus its CLAUDE.md
bullet; the declined `#: notes:` measurement appended under [G-27] with the CLAUDE.md
bullet's two residuals merged into one shape to stay under the 15-line cap; the tiering
rubric's "The guard" bullet re-measured.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
