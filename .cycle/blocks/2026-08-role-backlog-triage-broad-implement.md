---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: follow-on items from the per-turn-engines block — (1) the
whenever catch-all's counter-quantity gap; (2) the zero-role baseline worklist,
triaged as families per the 2026-08-19 precedent.

Files modified: scripts/deck.py, scripts/role_baseline.txt, tests/test_deck.py,
docs/gotchas.md, CLAUDE.md

CHANGES:
Item 1 (counter quantities) | scripts/deck.py | The Payoff / engine whenever
catch-all read the literal `put a +1/+1 counter`; "put two / X / that many +1/+1
counters" is how every scaling counter payoff is templated (Serra Redeemer,
Woodland Champion). The quantity alternation the per-turn pattern shipped with now
sits in the catch-all too — a strict superset of the old pattern (no trailing
" on", preserving parity). Measured BEFORE shipping: 34 pool cards (12-card sample
all genuine engines; one matches via endure's reminder text, and endure is itself a
repeatable attack trigger), 25 roster decks' Payoff counts up, graded axes 0,
floors 0, vectors 0. Two stale comments from the previous batch ("the catch-all
still misses…") updated in the same change — test doubles encoding old behavior.
Item 2a (ward — SHIPPED from the triage) | scripts/deck.py | The one PATTERN hole
the family triage surfaced: Protection / trick counted bare hexproof/indestructible
but not ward, their modern replacement, while _PROTECTION_RE (the G-25 axis) always
counted it — K-09's two-models shape on the same text. 259 pool cards gained the
role, 131 otherwise ZERO-role (largest family since the lord anthem's 146).
Measured: 58 decks' Protection / trick counts up; the protection AXIS unchanged
everywhere; interaction / card-advantage / floors 0 / 0 / 0 (the role is in neither
_INTERACTION_ROLES nor IMPACT_ROLES — the diff confirms the wiring). Negative
fixture: the devotion reminder's "counts toward your devotion" (embedded 'ward'
the word boundary must exclude, live on 30+ pool cards).
Item 2b (family triage — the rest DECLINED with reasons) | docs/gotchas.md [G-67] |
The 463-entry baseline grouped by effect shape (K-13): equip/attach 38 (taxonomy,
parked), one-shot ETB tokens 29 (correct zero — not repeatable), scry/surveil/
explore 28 (taxonomy — a Selection bucket is a new axis), sac outlets 15 (taxonomy
— enablers belong to engine_roles), opponent discards 15 (taxonomy — adding hand
attack to _INTERACTION_ROLES would re-grade the roster), tap-downs 7 (correct zero
— the neutralization permanence line working), blind mill 6 (correct zero BY
POLICY, G-62), treasure/food one-shots 5 (correct zero). Organizing distinction
recorded: a PATTERN hole is fixed and measured; a TAXONOMY hole is a design
decision that re-scores the roster.
Baselines | scripts/role_baseline.txt | 6 entries pruned by item 1, 18 by item 2a
(463 → 445). Tag-disagreement baseline (138) untouched by both.
Fixtures | tests/test_deck.py | Scaling-whenever positives (Serra Redeemer,
Woodland Champion); ward positives (Skyward Spider keyword form, A-Armory
Veteran cost form) + the devotion-reminder negative. All verbatim card text.
Docs | CLAUDE.md, docs/gotchas.md | New [G-67] section "the backlog triaged as
FAMILIES" with both measurements and the full triage table; CLAUDE.md G-67 bullet
21→23 holes + the pattern-vs-taxonomy triage line, re-compressed under the 15-line
cap (fired twice, evidence moved out — as designed).

TEST RESULTS: passed — full pytest suite exit 0 (5 new fixtures included);
check_all all invariants hold (pre-existing G-75 soft warning only); check_docs OK;
check_roles clean in both directions after baseline updates.

REGRESSION RISKS: cuts/suggest keep-scores shift where the newly-roled cards sit
(59 pool ward cards + 34 scaling-counter cards now earn base role credit) — the
intended direction, protecting warded bodies and scaling engines from the cut
list. Protection / trick is not an impact role, so the credit is the small base
tier. No graded axis or floor moved (measured, both changes).

INVARIANTS AT RISK: None — role patterns feed no invariant; both K-14 diffs
confirm floors unmoved.

NET SCORE: 2 − 0 = 2

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — no Deploy Command configured (data + tooling ship by commit/push).

FOLLOW-ON ITEMS:
- The four taxonomy families (Equipment 38, selection 28, sac outlets 15, hand
  attack 15) are recorded design questions, not fixes — each would re-score the
  roster and needs its own decision + K-14 diff if ever taken up.
- role_baseline.txt at 445: the residual is now mostly taxonomy or correct zeros
  by count; per-card triage of the remainder is low-yield.

DOCUMENTATION UPDATES NEEDED:
None — done in this batch.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
