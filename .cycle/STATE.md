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
("why does the tooling not propose the cards I propose?"). Cycle 9 is reflected and closed.
Phase: implement — **scan #10 is FULLY IMPLEMENTED**. All four batches plus every follow-on.
Scope: broad
Test Command: `python3 scripts/check_all.py`
Subsystem cycles since last Seams audit: 2 (counter adopted 2026-09-08; no Seams audit has run)
Updated: 2026-09-14 (broad-implement, batch 4)

## In progress (facts to carry forward — NOT judgments)
- **Broad scan #10 is fully implemented — nothing outstanding from the scan.** Four
  blocks: `10-batch1-2-ranking-visibility`, `10-batch3-followons-artifacts-tagger`,
  `10-batch4-interaction-taxonomy`.
- **One finding was REFUTED rather than fixed: BS10-02.** The one-turn tap-down exclusion is
  deliberate and documented; widening it would have added 36 cards to the axis `tier_band`
  grades. Recorded at the exclusion itself so a re-file lands on it.
- **ONE OPEN HUMAN DECISION: deck 47's tier letter.** It claims B and its metrics floor is
  now A (BS10-01 gave Trade the Helm a removal role). The rubric permits one band under when
  the prose argues it, and this block names three risks — but the deck also prints the
  possibly-under-graded nudge. Never auto-written.
- The cycle's number was `suggest`'s rank median **407**; batch 2 disclosed it and batch 3
  fixed its largest cause (deck 47's own picks: median 310 → 144).

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
- **Scan #10 Batch 3 + follow-ons** | BS10-04 the `artifacts` tagger hole (273 pool cards,
  1.71%; pool tag 158 -> 415; 0 tier floors, `cuts` top-3 on 5 decks, `suggest` top-20 on 27;
  deck 47/51 `#: tier:` figures re-grounded per K-12), the dashboard craft table wired for
  `back_off` + `craftTotal` (re-measured at that caller: 0.42%), the four reminder-regex
  copies consolidated into one `lib.REMINDER_RE` (0 disagreements across 15,977 texts), and
  two `figure_drift` registrations (K-15's 273, G-85's 14-of-43) | scripts/tag_synergies.py,
  scripts/check_patterns.py, scripts/lib.py, scripts/deck.py, scripts/build_dashboard.py,
  scripts/check_docs.py, CLAUDE.md (new K-15 + G-85), docs/gotchas.md, decks/47, decks/51

- **Scan #10 Batch 4** | BS10-01 permanent steal/exchange added to `Removal (spot)` (91 of
  98 pool cards had scored nothing; 48 Threatens deliberately excluded on the permanence
  line; 20-of-20 hand validation) — **1 of 112 tier floors moved**, deck 47 B → A. BS10-02
  REFUTED and its exclusion re-affirmed in place. K-12 consequences: deck 47's tier block
  rewritten, deck 43's `#~ note:` re-grounded 5 → 6, CLAUDE.md's tier-floor spread
  67/41/60% → 68/40/61% | scripts/deck.py, decks/47, decks/43, CLAUDE.md, docs/gotchas.md

## Pending / not yet done
- **Deck 47's tier LETTER** — claimed B, floor now A. A human call; see above.
- A `/sync-docs` pass: G-02/G-43/G-58 do not mention BS10-08's back-half flag, and G-38/G-22
  do not mention the ranking-window footer or the median-407 measurement.
- The unapplied cross-deck homes and earlier proposed swaps — NEXT-SESSION.md §0-current.
- Two G-67 role-pattern holes (Kitnap, Eluge), baselined not fixed.

## Open follow-on items
- **THE COMPARISON-CUE SUPPRESSION IS A LIVE BLIND SPOT in the audit K-12 depends on.**
  `_figure_is_history` silences every figure within ±60 chars of a `_COMPARISON_CUES` word.
  Deck 47's block hid FIVE figures behind one "rather than" for a full cycle, and both the
  CLI audit and the pytest roster sweep reported it CURRENT while its interaction figure was
  wrong. A plausible fix is to stop suppressing inside an explicit live-state listing
  ("Live vector:"), but that needs G-26's roster-wide precision sweep first.
- BS10-01 residual: a Threaten whose duration cue sits in a DIFFERENT sentence from the
  gain-control phrase would be counted. Zero pool instances today; re-check after a rebuild.

- The `or creature` guard in `_ARTIFACT_MATTERS_RE` costs the genuine either-type cards an
  artifact deck would copy or sacrifice (Three Steps Ahead is the measured instance). It is
  holding back 236 cards — do not relax it without re-measuring BOTH sides.
- A roster before/after harness must ASSERT zero errors. Mine called `tier_band(vec, cards=…)`,
  which takes only `vec`, so 112 decks errored identically on both sides and the diff reported
  the answer I expected from a probe that ran nothing (G-63's vacuous shape). The `cuts` half
  compared a set's repr, whose order is nondeterministic (G-54).
- CLOSED 2026-09-14 (batch 3): the dashboard now renders `back_off` + `craftTotal`; the four
  reminder-regex copies are one `lib.REMINDER_RE`; `_UNPRICED_DISCLOSE_FLOOR`'s calibration is
  registered in `figure_drift` as G-85. Nothing left from the batch-1-2 block.
- `unmet_gate` has three callers now, and `redundancy` is the one never re-measured AT its
  own surface — the exact lesson the second wiring taught. Small list, so the rate is
  probably fine; "probably" is what that pass spent the day disproving.
- G-84's DFC front-face question is closed as "all-faces is the better approximation", NOT as
  correct. A per-face availability read (transform vs modal vs saga-back) would settle it;
  G-63's column list still does not name TYPE on this path.
- `figure_drift` now covers 12 of CLAUDE.md's ~1,100 numeric claims (K-15 and G-85 joined
  2026-09-14). The rule for what earns an entry is written down; the registry is still
  hand-kept and its misses still invisible.
- `tier_floor_spread()` is called twice per `check_all` (the BS8-06 sweep and figure_drift)
  and is not memoized — ~2s of duplicated roster walk, a one-liner nobody has needed yet.
  G-85's entry adds a further ~1.7s roster walk, lazily.
- `synergies` LIST ORDER now comes from the pool (258 pure re-orderings). Nothing measured
  moved; any surface showing "the first N themes" shows the pool's order.
- Regression scenarios 5–8 and 10–19 need a person at a browser; several never walked.

## Decisions made (so the next session doesn't re-litigate)
- **BS10-02 IS REFUTED, NOT DEFERRED. Do not re-file it.** The one-turn tap-down family
  (39 cards, disjoint from the 37 permanent ones) is excluded because a one-turn effect is
  TEMPO, not an answer — widening it adds 36 cards to the axis the tier floor grades on,
  which is the BS2-06 failure. The same permanence line makes BS10-01 exclude Threatens, so
  the two decisions agree rather than merely coexist.
- **Before widening a role bucket, read the comment AT the exclusion.** A measured gap is
  evidence that a pattern does not match something; it is not evidence that it should.

- **`artifacts` is NOT an `_TYPE_MATTERS` entry, deliberately.** That table's first pattern
  matches 427 pool cards for artifacts — every "destroy target artifact", i.e. artifact HATE
  tagged as synergy. The mechanism is right for Equipment and wrong for Artifact.
- **BEING an artifact is deliberately untagged** (~19% of the pool would destroy the theme).
  G-83's `cost_scale_resource` already answers "how many artifacts does this deck field" from
  the TYPE LINE.
- **`lib.REMINDER_RE` takes the stricter `[^()]` form** for all five call sites. Measured
  identical on 15,977 texts; the four original NAMES stay as aliases because
  `check_patterns`' registry is keyed by (module, attribute name).

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
**Broad scan #10 is COMPLETE** — four batches, every follow-on, three implementation
blocks in `.cycle/blocks/10-*`. **1796 tests pass, `check_all` exit 0, `make postedit`
exit 0, Regression Scenario 2 walked 29/29. Batch 4 NET SCORE 1 − 0 = 1.**

**One decision is waiting for the user: deck 47's tier letter.** BS10-01 gave Trade the Helm
— the exact card that deck's own tier block had been arguing was uncounted — a removal role,
so interaction went 6 → 7 and the metrics floor B → A. The claimed letter is still B. The
rubric allows one band under when the prose argues it, and the block names three risks (the
deck is unbuilt with 10 craft targets, protection is thin, the curve climbed), but the tier
command prints the possibly-under-graded nudge and the letter is a human judgment.

**The lesson from this batch is that a measured gap is not a mandate.** Two findings arrived
looking identical — same measurement shape, same disjoint-templating signature. One was a
real hole; the other was a decision with its reasoning written four lines above the pattern,
and I had drafted the fix before reading it. A measurement counts the EFFECT and cannot see
the DECISION.

**And the audit that K-12 depends on hid a real stale figure.** After the change deck 47's
prose said interaction 6 against a live 7, and both the CLI audit and the pytest roster sweep
said CURRENT — because "rather than", a phrase I wrote into that block last cycle, sat 46
characters before the number and tripped the comparison-cue suppression, silencing all five
of its live-vector figures. Found by hand, fixed by rewording, and then watched-it-fail to
prove the sweep can see it now. The general defect is logged under Open follow-on items.
