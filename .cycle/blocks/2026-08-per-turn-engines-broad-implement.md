---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: follow-on from the suggestions A–E block — the zero-role
structural cards (Ouroboroid's combat-trigger counters, Delney's evasion grant) as
G-67 per-family classifier work, each with its own K-14 diff.

Files modified: scripts/deck.py, scripts/role_baseline.txt, tests/test_deck.py,
docs/gotchas.md, CLAUDE.md

CHANGES:
Family A (per-turn engines) | scripts/deck.py | Every `Payoff / engine` pattern was
`whenever`-shaped — K-14's exact failure one bucket over — so the same payoff on a
beginning-of-phase clock scored ZERO roles (Ouroboroid, Dragonmaster Outcast, Virtue
of Loyalty). Added one pattern scoped to YOUR phases (combat on your turn / your
upkeep / your end step / each of your turns) with the catch-all's payoff alternation
plus the non-"a" counter quantities (X / two / that many). Measured BEFORE shipping:
+187 pool cards (14-card random sample read end to end, all genuine engines); 47
roster cards, 19 previously ZERO-role; 60 of 114 decks' Payoff counts up (deck 60:
0→2); interaction 0 moved, card advantage 0 moved, tier floors 0 moved; only vector
changes were 15 decks' "unclassified" uncertainty lists shrinking. Negative classes
measured and excluded by the scope alternation: symmetric each-player gifts (Howling
Mine) and opponent-scoped clauses (Urabrask, Heretic Praetor).
Family A baselines | scripts/role_baseline.txt | 21 stale zero-role entries pruned
via --update-baseline (0 newly acknowledged). Tag-disagreement baseline (138)
untouched — none of the acknowledged disagreements involved this family.
Family A fixtures | tests/test_deck.py | TestClassifyRoles: 3 positive fixtures from
verbatim card text (Ouroboroid, Dragonmaster Outcast, Bitterbloom Bearer) + 2
negatives (Howling Mine symmetric, Urabrask opponent-scoped — whose "draw a card"
sits in a denial clause and whose own-upkeep payoff is a sentence away, outside the
[^.] window).
Family B (evasion grants) | docs/gotchas.md [G-67] | Measured and DECLINED. 47
zero-role roster cards mention unblockable/menace but nearly all are native-evasion
BODIES; evasion is already counted where it decides something (quality-vector reach
via _EVASION_TAGS; granted keywords land in the tag/fit model since G-80; Delney's
own mis-rank was fixed by the G-40 multiplier co-signal). A new Evasion role would
be a TAXONOMY change (ROLE_ORDER + IMPACT_ROLES + displays) that double-counts reach
and fixes no live mis-rank — the same taxonomy-vs-pattern line the 2026-08-19 pass
drew for Equipment.
Docs | docs/gotchas.md, CLAUDE.md | New [G-67] section "the per-turn engine family"
with the full measurements and the Family B decline; CLAUDE.md G-67 bullet updated
(20→21 holes, per-turn engines named) and re-compressed under the 15-line cap
(check_docs fired twice during editing — working as designed).

TEST RESULTS: passed — full pytest suite exit 0 (4 new fixtures included);
check_all all invariants hold (one pre-existing soft warning: G-75 dead library
searches, unrelated); check_patterns 285 patterns live; check_docs OK;
check_roles reports no new zero-role cards and no new tag disagreements.

REGRESSION RISKS: cuts/suggest rankings shift in the 60 affected decks (newly
Payoff-roled cards gain role credit) — that is the intended fix, the direction that
protects engines from the cut list. No graded axis moved, so no tier letter or
audit verdict changes from this alone. The pattern cannot over-count symmetric or
opponent-scoped triggers (measured; pinned by the two negative fixtures).

INVARIANTS AT RISK: None — role patterns feed no invariant; the K-14 diff confirms
tier floors unmoved.

NET SCORE: 1 − 0 = 1

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — no Deploy Command configured (data + tooling ship by commit/push).

FOLLOW-ON ITEMS:
- The whenever catch-all still misses non-"a" counter quantities ("put X/two +1/+1
  counters on" in whenever form) — the per-turn pattern handles them but its
  whenever sibling does not; same one-line widening + diff when it next surfaces.
- role_baseline.txt still holds 469 acknowledged zero-role roster cards — a
  worklist, per the 2026-08-19 precedent (most are legitimately roleless or
  taxonomy questions like Equipment).

DOCUMENTATION UPDATES NEEDED:
None — done in this batch (gotchas.md [G-67] section, CLAUDE.md G-67 bullet).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
