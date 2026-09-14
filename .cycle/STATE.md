# Cycle State

> **Starting fresh? Read `.cycle/NEXT-SESSION.md` first.** It carries the current
> diagnosis, the agreed next task, the measurements not to re-derive, and the traps.
> This file is the ROLLING machine-readable state for the CURRENT cycle only;
> that one is what to do. Completed-cycle narrative is in `.cycle/HISTORY.md`.
> For "which command answers X, and why do two of them disagree", read
> **`docs/systems-map.md`** — a live reference, not a cycle artifact.
>
> **Keep this file to the seven sections below.** `/cycle-status` and
> `/cycle-resume` read the FIRST match of each heading, so a second
> `## Where I left off` silently shadows the real one. Narrative belongs in
> HISTORY.md; per-run summaries belong in `.cycle/blocks/`.

## Current
Cycle: 10 — a fresh `/broad-scan` ran 2026-09-14 out of the deck 47 tuning post-mortem
("why does the tooling not propose the cards I propose?"). Cycle 9's blocks stay under
their own prefix; cycle 9 is reflected and closed.
Phase: implement (Batches 1 & 2 done — `.cycle/blocks/10-batch1-2-ranking-visibility-*`)
Scope: broad
Test Command: `python3 scripts/check_all.py`
Subsystem cycles since last Seams audit: 2 (counter adopted 2026-09-08; no Seams audit has run)
Updated: 2026-09-14 (broad-implement, batches 1-2)

## In progress (facts to carry forward — NOT judgments)
- **Broad scan #10 ran 2026-09-14; Batches 1 & 2 are implemented, Batches 3 & 4 are NOT.**
  The user selected batches 1-2 only. Outstanding: **BS10-04** (`tags_for` misses 112 of
  150 artifact-count cards) and **BS10-01 / BS10-02** (interaction taxonomy: exchange/gain
  control 79 of 84 missed, tap+stun 33 of 34 missed against bounce's 1 of 31).
- **The number this cycle produced is `suggest`'s rank median: 407.** Over 783 applied
  swaps that recorded a rank for the ADD, the median rank of the card actually chosen is
  407 and only 10% fell inside the default top-20 window. That is the measured answer to
  "why does the tooling not suggest my cards": it is not REACH, it is RANKING. BS10-05
  discloses it; **BS10-04 is the finding that would move it.**
- Cycle 9's work is fully landed; nothing from scan #9 is outstanding.
- Deck 71's rebuild has an ordered open list — see §0-current of NEXT-SESSION.md.

## Completed this cycle
- Template sync v1.23.0 → v1.33.0 | `.claude/commands/broad-scan.md`, CLAUDE.md, docs/cycle-config.md
- Tier-3 re-evaluation; state-and-measurement half adopted | `.cycle/`, `.claude/commands/`, CLAUDE.md
- Skill-discoverability fixes | tune-deck Stage 8 handoff, systems-map promoted to intent
  router, three skill descriptions de-truncated
- Broad scan #9 (audit only, no writes) | 8 findings, 4 batches
- **Batch 1** | F1 pool-first synergies + F4/F8 stale figures | scripts/deck.py, CLAUDE.md,
  ROADMAP.md, decks/15, decks/40
- **Batch 2 + follow-ons** | F1b model-vs-store agreement pair (mutation-proven), F3 four
  roster-shape figures, K-09/G-30 amended, ROADMAP PROVISIONAL 51→55 | check_agreement.py,
  check_docs.py, test_gates_fire.py, CLAUDE.md, docs/gotchas.md, ROADMAP.md
- **Batches 3 + 4** | F2 sub-majority dashboard warning + Scenario 19, F5 four wishlist
  roster loops, F6 twelve editor guard/endpoint tests (mutation-proven), F7 absent-token
  bypass retired | build_dashboard.py, wishlist.py, app.py, test_app_editor.py, CLAUDE.md
- **Post-mortem fixes 1-3** | `swap` now reports an unmet gate on the ADD (probe built
  POST-CUT, so a cut that removes the gate's only enabler shows); a CHOSEN-TYPE payoff
  overlay (`type_scale_*`, floor 7 / key 13 / cap 12 calibrated from the roster's
  p25/p75/p90) wired into `suggest-homes` and `cut_keep_score`; the self-consuming-resource
  flag measured and DECLINED | scripts/deck.py, scripts/check_patterns.py, tests/test_deck.py
- **Follow-ons + /sync-docs** | `unmet_gate` wired into BOTH recommenders, which exposed and
  fixed three defects in the primitive (self-supply, reminder text, G-66's token residual):
  82 dead-gate hits over 4,520 craft picks -> 12, all 12 genuine. Three other follow-ons
  measured and declined. New anchor G-84; G-66/G-06/G-40/K-09/G-42/K-13 updated; G-84's pool
  count registered in `figure_drift` | scripts/deck.py, scripts/check_docs.py,
  scripts/check_patterns.py, tests/test_deck.py, CLAUDE.md, docs/gotchas.md
- **Scan #10 Batches 1 + 2** | BS10-03 card-advantage hole ("put the rest into your hand",
  4 pool cards wholly missed; 0 tier floors moved, deck 67 prose re-grounded 4->5), BS10-05
  `suggest`'s ranking window + `feedback`'s rank distribution (median 407), BS10-06
  `pool.py --regex` (K-13's effect-shape search, which had a rule and no tool), BS10-07 the
  ◊ discounts `effective_avg_mv` does not price (14 of 43 decks), BS10-08 a split card's
  BACK half needing a colour the deck lacks (0.46% roster-wide, transform DFCs correctly
  excluded) | scripts/deck.py, scripts/pool.py, CLAUDE.md, decks/67-warpwright/deck.txt

## Pending / not yet done
- **Scan #10 Batches 3 & 4** — BS10-04 (tagger artifact-count hole) and BS10-01 / BS10-02
  (interaction taxonomy holes). BS10-04 is the highest-leverage item outstanding: it is the
  measured cause of the median-407 ranking BS10-05 only discloses.
- A `/sync-docs` pass for the three gotchas BS10-07 / BS10-08 / BS10-05 outran — see the
  block's DOCUMENTATION UPDATES NEEDED.

- The unapplied cross-deck homes and earlier proposed swaps — NEXT-SESSION.md §0-current.
- Two G-67 role-pattern holes (Kitnap, Eluge), baselined not fixed.

## Open follow-on items
- The dashboard's craft table shares `suggest_scored` and now RECEIVES `back_off` and
  `candidates` without rendering either — the G-40 shape (a primitive that works and one
  caller that never asks). Re-measure the rate AT that caller before wiring; do not inherit
  the 0.46% measured on the CLI.
- Four private copies of the `\([^)]*\)` reminder regex remain across deck.py, lib.py (x2)
  and tag_synergies.py. BS10-06 added a CALLER of deck.py's, not a fifth copy.
- `_UNPRICED_DISCLOSE_FLOOR = 3` carries the `TIER_FLOOR_REQ` hazard (calibrated from
  today's 43-deck population) and is NOT registered in `check_docs.figure_drift`.

- `unmet_gate` has three callers now, and `redundancy` is the one never re-measured AT its
  own surface — the exact lesson the second wiring taught. Small list, so the rate is
  probably fine; "probably" is what that pass spent the day disproving.
- G-84's DFC front-face question is closed as "all-faces is the better approximation", NOT as
  correct. A per-face availability read (transform vs modal vs saga-back) would settle it;
  G-63's column list still does not name TYPE on this path.
- `figure_drift` now covers 10 of CLAUDE.md's ~1,100 numeric claims. The rule for what earns
  an entry is written down; the registry is still hand-kept and its misses still invisible.
- `tier_floor_spread()` is called twice per `check_all` (the BS8-06 sweep and figure_drift)
  and is not memoized — ~2s of duplicated roster walk, a one-liner nobody has needed yet.
- `synergies` LIST ORDER now comes from the pool (258 pure re-orderings). Nothing measured
  moved; any surface showing "the first N themes" shows the pool's order.
- Regression scenarios 5–8 and 10–19 need a person at a browser; several never walked.

## Decisions made (so the next session doesn't re-litigate)
- **BS10-08 DECLINES the ambiguous middle rather than guessing.** There is no `layout`
  column, so a transform DFC and a modal one are indistinguishable by cost alone — and
  Norman Osborn / Bruce Banner are the two cards G-58 already cites as this exact mis-bin.
  Only an Adventure/Room back or instant-or-sorcery-on-both-faces qualifies (213 of 308);
  the 157 creature/land-faced DFCs stay unflagged. A modal DFC with a creature back is a
  KNOWN, ACCEPTED false negative — G-76's scope line, report nothing over reporting a guess.
- **BS10-07 and BS10-08 are DISCLOSURE, pinned out of every score** (G-25 / G-60's rule:
  a score change on a fuzzy signal is what this file keeps having to undo). Do not
  "finish" either by feeding it into `tier_band`.
- **`_UNPRICED_DISCLOSE_FLOOR` is p75 of its own axis, not 1.** At >=1 the note fires on
  83% of the decks that can see it — the G-07 saturation shape. 32% at the chosen floor.
- **BS10-06 does not add a fifth reminder-regex copy.** `pool.strip_reminder` lazily proxies
  `deck._REMINDER_RE` for the same reason `pool.classify_roles` proxies its model: `--regex`
  must answer the same question about a card that `classify_roles` does (K-09).

- `load_card_meta` is POOL-first for Synergies and LIBRARY-first for colours. Colours were
  deliberately left alone — the finding was about tags, and re-sourcing identity is a
  separate, wider change.
- A BLANK pool cell never overrides a library tag set (0 such cards today; the guard is for
  the next pool rebuild).
- The two tags the override drops (`fear` on Wraith, `undying` on Shadow of the Goblin) are
  Scryfall ability-NAME artefacts, the K-01 shape — dropping them is a correction.
- Tier-3 `/audit`, `/plan`, `/implement`, `/systems-map`, `/setup-cycle` stay UNVENDORED.
- PROJECT_HEALTH.md deliberately NOT created (no vendored writer for it).
- **The self-consuming-resource flag (G-42's mirror) is DECLINED, measured.** 44 (card, deck)
  pairs fire on the roster and **23 read BACKWARDS** — 12 fetchlands (they REPLACE what they
  sacrifice) and 11 sacrifice outlets in decks whose plan is sacrificing, which is G-41's
  cost-as-upside saying the opposite thing. At best 3-6 of the rest are real: <=14% precision,
  against the ~45% at which G-27 declined the `#: notes:` scan. The narrow non-optional form
  has **0 live instances**. Structural reason: a sacrifice is a CHOICE, and the same text is
  upside in one deck and conflict in another - separated by the deck's PLAN, which no text
  model here holds.
- The BLANKET converters (Arcane Adaptation, Leyline of Transformation) are EXCLUDED from the
  chosen-type family rather than counted: they INVERT the term. The pattern is ANCHORED at the
  clause start — unanchored it also swallowed Lifecraft Engine, a genuine member.
- **FRONT-ONLY subtype counting is DECLINED, measured**: of 35 roster DFCs whose faces differ,
  25 are creature->creature transforms (all-faces over-counts) but 10 have a NON-creature
  front where front-only counts a hard ZERO. It trades 25 over-counts for 10 silent zeroes.
- **The NAMED-type overlay half is DECLINED, measured**: 124 pool cards, but `tribal` already
  serves the 92 where the card IS that type, and the noun extraction misfires on the rest.
- **Caching `type_scale_support` is DECLINED**: 1.3% of `suggest-homes`, and a cache keyed on
  an unhashable list is the G-71 hazard.
- Gate patterns read reminder-STRIPPED text EXCEPT the library-search family — a fetch rider
  lives only in its reminder, and a global strip deletes G-75's worked example silently.
- The full history of what was decided against lives in `.cycle/HISTORY.md`.

## Where I left off
**Broad scan #10, Batches 1 & 2 are implemented, verified and committed** — block
`.cycle/blocks/10-batch1-2-ranking-visibility-broad-implement.md`. Five findings:
BS10-03 / BS10-05 / BS10-06 / BS10-07 / BS10-08. **1796 tests pass, `check_all` exit 0,
`make postedit` clean. NET SCORE 4 − 0 = 4** (BS10-06 graded a new capability, not a
production fix, per cycle 9's precedent).

**The thing to carry into the next session is BS10-04.** This cycle measured why the
tooling's recommendations and the user's picks diverge — the median rank of an actually
chosen add is **407 of ~950 candidates, 10% inside the top 20** — and then fixed only the
DISCLOSURE of it. The cause is upstream: `tags_for` misses 112 of 150 artifact-count cards
(74%), so theme-fit-driven `base` sinks mechanically perfect picks. BS10-05 makes the
problem visible at the surface; BS10-04 is what makes the ranking usable. Batches 3 & 4
were not selected, not blocked.

One caution for whoever runs BS10-04: it is a TAGGER change, which per G-67's triage line
is a TAXONOMY widening, not a pattern hole — it re-scores the roster. K-10 requires BOTH
derived tag stores rebuilt (`tag_synergies.py --merge` AND `build_pool.py --all`), and
K-12 requires the before/after roster diff plus the `#: tier:` prose sweep. Budget for
that, and expect the full pytest suite (not just `check_all`) to be the gate that catches
stale prose — it is what caught deck 67 in this batch.
