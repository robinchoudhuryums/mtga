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
Updated: 2026-09-20 (manabase recommender + tapland taxonomy + the freshness gate — see Where I left off)

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

- **2026-09-21 — two role-pattern whitelist holes, surfaced by a deck-3 tune.**
  `Team pump / anthem` matched "of the chosen TYPE" and not "of the chosen COLOUR"
  (Heraldic Banner, Caged Sun scored zero roles; 0 decks run either — defensive).
  Card advantage had no topdeck-to-hand pattern, so Sidequest: Catch a Fish scored
  Ramp/fixing alone and **deck 73 sat a tier band low** — a live mis-grade, now
  C→B with its claimed B matching the floor. Roster diff 3 deck files / 1 band.
  Block: `.cycle/blocks/2026-09-topdeck-to-hand-and-chosen-colour-anthem-broad-implement.md`.
  **The first draft of the card-advantage pattern was wrong and the discipline caught
  it**: it used a same-sentence span on the theory that the sentence boundary
  separates card advantage from ramp. It does not — Risen Reef and three others put
  the card in hand only AFTER a battlefield sentence, and a tight span drops ten such
  cards. The discriminator is "reaches your hand at all". A test pinning the wrong
  theory had already been written and was rewritten before landing.
- **2026-09-20 — three tooling fixes surfaced by the deck 16/79 manabase work**
  (`.cycle/blocks/2026-09-manabase-recommender-tapland-taxonomy-broad-implement.md`).
  (1) `suggest_lands` had inherited `suggest` proper's skip-what-you-run filter, so it
  could not propose a SECOND copy of a land — the fix for most manabases. Now only the
  copy limit and basics exclude; an `In` column labels duplicates. **58 of 112 decks' #1
  land pick is now another copy.** (2) `tapland_kind`'s `conditional` bucket held FOUR
  families with opposite timing; `fast` and `check` now earn the untapped premium, `check`
  only when the caller passes a basic count over 12 (roster p25). 35 of 676 pool land rows
  move. (3) `check_all` now reports collection freshness (`collection_freshness_soft`).
  17 new tests, each mutant-verified.
- **KEY saturation in `fit_strength` — the earned generic signature (post-scan, user-requested)** | The filed control-flow defect: the signature branch is the function's FIRST statement and excluded `_GENERIC_TRIBES` but not `GENERIC_THEMES`, so it minted **97.3% of every KEY verdict** roster-wide while `role-gap` (1.5%) and `top-theme` (1.2%) were dead. A generic signature theme must now EARN its KEY via `structural_overlay_hit`; a specific one still mints alone; an unearned generic one FALLS THROUGH rather than being forced down. KEY 18.6% → 10.2%, p50 KEY decks per card **8 → 4**, and `top-theme` → **63.8%** / `role-gap` → **8.8%**. **A REJECTION was pinned in the tests and had to be cleared first** — an earlier tightening dropped deck 30 21% → 1% and demoted Innkeeper's Talent; that rejection stands and this is a different change, evidenced on the same deck: **deck 30's KEY rate does not move at all (27.7% → 27.7%)** and Innkeeper's Talent survives via the overlay. Measured LIVE at all THREE callers per G-40, with `tangential` invariant at every one — the first `screen` sample showed zero change and would have been a VACUOUS pass, so the population was measured (42 of 112 decks) and re-run where the path bites (5 of 8 moved) | scripts/deck.py, scripts/check_suggest.py, tests/test_deck.py
- **F2/F4 — the nonland mana-source disclosure, and a MEASURED DECLINE of the pay-life flag (post-scan, user-requested)** | F2: `consistency` prices every figure off the LAND count (G-35) while `suggest --ramp` recommends the nonland sources it cannot see — two surfaces disagreeing by construction, neither saying so, and **decks 23 and 41 had each independently hand-written the workaround into their own `#: notes:`**, which by this repo's rule means the RULE was wrong. New `uncounted_mana_sources`, printed by `consistency`, REPORT-ONLY (no figure moves — a rock is not a land drop, and that exclusion was never the bug; its SILENCE was). Rules reused from `lib.land_production` so the disclosure and the land count cannot drift, which buys the spend-only / granted-ability exclusions free. **75 of 112 decks, 76 cards, hand-checked 74/76.** The first two measurements were WRONG — a hand-rolled regex said 40 decks, and `_MANA_SOURCE_RE` (the existing primitive, one caller) said 89 at far worse precision: G-40 fired exactly as written. F4: **DECLINED after measurement, not built.** Bar pre-registered at ~50%; the broad form scores **22%** (46% shocklands/equip costs, 26% cheap-not-upside, **6% BACKWARDS** — "ward—pay 5 life" is the OPPONENT's cost, G-42's own signature), and the narrow form fires on **1 of 112 decks** off 7 pool cards — **not deck 41**, the deck that motivated it. The shape was wrong: every `_COST_UPSIDE` rule encodes a cost that FEEDS something, and paying life feeds nothing | scripts/deck.py, tests/test_deck_models.py
- **F1/F3 — the board-presence axis and the rationale audit's self-disclosure (post-scan, user-requested)** | Came out of the deck 41 tune: the deck read WEAK while clearing an A floor, and **no tool measured board presence at all** — `grep board_power scripts/` returned nothing and the sum was hand-rolled six-plus times in one session. New `board_power` (quantity-weighted printed power over FRONT-face creatures), report-only in `stats` and `tier`, never in `tier_band` — pinned by a test that two decks differing only in creature SIZE land in the same band. It is a SEPARATE axis, measured: **r = −0.147 against a ±0.188 noise band at n=112**, distribution min 23 / p10 37 / p50 54 / p90 73 / max 120. Three limits disclosed rather than guessed: unknown `*`/X power (**70 of 112 decks**, 124 copies — a bare sum would under-report on 62% of the roster), tokens (read ZERO), and Vehicles (counted apart, 10 decks). `deck_quality_vector` had a SECOND in-loop creature tally beside it — removed, 0 diffs across 112 decks. F3's half: deck 41's board-power figure **went stale twice in one session while `--audit-rationale` reported it CURRENT**, because an unregistered figure is unauditable; registered now, with `_FIG_RANGE_AFTER` (the WORDED form of `_ARROW_AFTER` — the roster writes "went 41 to 57") so the delta's FROM side is not flagged, and `audited_figure_keys()` derived from the pattern table so the audit PRINTS what it can price | scripts/deck.py, scripts/check_patterns.py, tests/test_deck_models.py, tests/test_deck.py
- **BS14-01/02/03 + doc sync — the hybrid blind spot's remaining surfaces (post-scan, user-requested)** | BS13 fixed the probability model; `deck.py mana` and the DASHBOARD still repeated the blanket "castable with any of their colors", which is the sentence that made deck 14 look fine. Both are source-aware now via the same `binding_pips`, printing `⚠ BINDS as {X}` — **34 hybrid entries flagged roster-wide**; `cmd_mana` had been computing its source profile AFTER the report it needed to inform. KEEPABLE joined `_figure_lookup` (11 roster claims, 0 wrong, but it drifts on every manabase change), with its own past-tense guard because the shared history cue reaches neither a cue INSIDE the match nor one AFTER it. **The WORD-SPELLED figure was measured and DECLINED** — ~10–20% precision, since "one" and "two" are ordinary prose (the G-78 bar). Doc sync closed all three BS13 items: the "hybrids are strictly easier" premise was stated in FOUR places | scripts/deck.py, scripts/build_dashboard.py, CLAUDE.md, docs/gotchas.md
- **BS13-01/02 — the hybrid zero-source blind spot and copula figures (post-scan, user-requested)** | **A hybrid pip with ZERO sources of one half was priced as NO constraint**: every probability surface dropped the hybrid half on the premise that a hybrid is strictly easier, which is true everywhere except at zero, where `{B/G}` IS `{B}`. **41 cards across 24 decks**, all of them SKIPPED ENTIRELY by the cast-on-curve table rather than shown wrong; 27 overstated by 5+ points; worst deck 14's Long Feng at **100% against a true 52.5%**, invisible while its strictly easier `{B}{B}` twin off the same 11 sources was flagged at 65.1%. New `binding_pips` wired into both probability surfaces; **0 of 111 tier floors moved** (verified against a stashed baseline). And the audit's figure patterns require the number ADJACENT, so a copula was invisible — G-26 had recorded that residual for a year unmeasured: **23 roster claims, 6 wrong**, all five live ones corrected (deck 27's cap rested on a false figure and is now a RE-GRADE CANDIDATE with the letter untouched). One exclusion earned by the sweep: a number re-qualified by a SPEED word is a profile sub-count, not the axis total | scripts/deck.py, tests/test_deck.py, 5 deck files
- **BS12-01/02 — the prose budget and the figure registry (post-scan, user-requested)** | Asked whether the project carries too much text. Measured: the always-on budget is CLAUDE.md's 24k words, not the 177k total — `docs/gotchas.md` is opt-in and `HISTORY.md`/blocks are read by workflow commands — and of ~1,179 numeric tokens only **~40 are LIVE claims**; the rest are dated history that cannot rot. Four rules trimmed (G-27 648→266, G-84 551→276, G-33 384→226, G-09 367→286, **−896 words**), narrative MOVED to gotchas.md (**+1229**), so the project gained prose while the session budget shrank. **The 15-LINE cap that should have prevented this measured the FORMATTING**: two of the four sat on a SINGLE line and all four passed it, and wrapping a trimmed rule turned a passing 1-line bullet into a failing 21-line one. Now `WORD_CAP = 300`, derived from p90 (224). `figure_drift` 14 → 21 registered figures, each through the real predicate; **five of the seven were already stale**, plus a sixth in the same sentence — all re-grounded | CLAUDE.md, docs/gotchas.md, scripts/check_docs.py, tests/test_check_docs.py
- **BS11-01/02/03 — the doubler active voice and fit-pass saturation (post-scan, user-requested)** | `doubler_axis` matched only the PASSIVE voice of the global replacement, so **Doubling Season — the card the mechanic is named after — scored None on BOTH its axes** and `cuts` ranked it deck 78's 2nd-weakest card while that deck's rubric entry names it as the thesis. Active branch added to the tokens and counters patterns, requiring the literal "twice that many" so Doc Samson's plus-N stays out and scoped away from Vorinclex's opponent-halving clause. Pool 71 → 76 doublers, **0 lost**; roster diff **0 of 111 tier floors, 1 of 111 cuts top-3** (deck 78, Doubling Season moving DOWN — the intended direction). `suggest-homes` gained a roster-wide KEY-saturation warning (`_HOMES_KEY_SATURATED = 0.15`, derived from p75 of a measured 75-card distribution), the twin of `screen`'s pile-wide 0.40. `/ingest` Stage 3c now splits new-to-the-LIBRARY from new-to-the-ROSTER. **check_suggest's doubler probe tested only the passive form and so could not have caught this** — extended, watched-it-fail | scripts/deck.py, scripts/check_suggest.py, tests/test_deck.py, .claude/commands/ingest.md
- **G-02 recompute fix (post-scan, user-requested)** | `effective_avg_mv` and `cheat_cost_cards` recomputed mana value from the RAW `A // B` cost instead of `load_mana`'s front-faced `entry[1]`; the printed avg MV `stats`/`tier` render disagreed with the vector's on **27 of 112 decks, up to +0.45** (0 after). `cheat_cost_cards` was latent (0 of 616 `//` rows carry an alt cost). Report-only, so **no floor moved and nothing flagged** — gated now by `check_agreement`'s ninth pair `_agree_avg_mv` (roster sweep + synthetic split-cost control, watched-it-fail both halves) | scripts/deck.py, scripts/check_agreement.py, tests/test_deck_models.py, CLAUDE.md, docs/gotchas.md
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
- **No surface computes P(a tapped land in your first N land drops).** Hand-rolled six
  times on 2026-09-20 and it decided both manabases. The G-86 `board_power` shape. MUST
  stay report-only — `tapland_profile`'s docstring already commits to never feeding a
  score, and G-25/G-60/G-86 say why.
- **`wishlist --rank` could pass its Target deck's basics to `_land_value`** and price
  checklands properly. NOT built: the wishlist holds zero checkland rows today, so the
  change is unmeasurable and this project measures. Revisit when one is wishlisted.
- `_central_themes`' relative cutoff moved deck 79's reported count 11 → 8 with no deck
  change (two new tagged lands raised the top weight). Report-only; documented in the
  deck's notes rather than filed as a defect.
- CLOSED 2026-09-15: `_ALT_COST_RE` now covers `impending`. It was not the count of cards
  that mattered — `effective_avg_mv` returns None when nothing is priced, so **7 of the 9
  decks holding an impending card printed NO advisory at all**, a failure that presented as
  silence. The cost is substituted (right for what the deck PAYS) and the body delay is
  DISCLOSED by `impending_delay_note` rather than gated, because a gate on the "this
  permanent" wording would pass all six cards and assert nothing. 7 decks gained a figure,
  2 moved, **0 of 112 tier floors**. Ride-alongs: `check_patterns` refused the build until
  `_IMPENDING_RE` was registered; `cmd_tier`'s "Warp/Plot/Foretell" prose named three of
  nine keywords and now names the shape; G-85's effective-figure POPULATION moved 43 → 50
  and was only ever hardcoded inside the fire-rate entry's own regex, so it is registered in
  `figure_drift` as its own figure now. Residual: no impending GRANT form exists, so
  `_ALT_COST_GRANT_RE` was left alone.
- **The generalised form of the G-02 fix, unswept:** `load_mana` normalises a value and hands back `(raw, normalised)`; two callers recomputed from `raw` and drifted. No sweep has asked whether any OTHER `load_*` table has the same shape — a loader that fixes something up, and a caller that re-derives it from the untouched input beside it.
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
- `figure_drift` now covers 13 of CLAUDE.md's ~1,100 numeric claims (K-15 and G-85 joined
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
**2026-09-20 — deck 16/79 manabases, then the three tooling fixes they surfaced.**
PR #187 merged (four deck-79 swaps, the library reconcile, both manabases rebuilt, the
dashboard). Then `/broad-implement 1-3` on branch `claude/sync-commands-mmmsdb`, restarted
from `main` after the merge. `check_all` green, `check_docs` 114 rules, `check_commands`
OK, both `--help` levels OK.

**THE THREE FIXES ARE IN THE BLOCK FILE** — read it rather than re-deriving:
`.cycle/blocks/2026-09-manabase-recommender-tapland-taxonomy-broad-implement.md`.

**Two of the three findings were not what I filed, and the corrections matter more than
the fixes.** Finding 2 was filed as "checkland vs board-state" and MEASURED as four
families with opposite early-game timing (fast / check / slowland / board state) — the
measurement widened the fix. Finding 3 claimed `collection_stamp_note` could not tell
"never" from "30 days ago"; it ALREADY could, and the only real gap was that `check_all`
never called it. State a finding from the code, not from the symptom that surfaced it.

**A PROCESS FAILURE TO NOT REPEAT:** a background full-suite run reported five failures
that were artifacts of my own concurrent edits to scripts/ while it was reading them. All
five passed on the settled tree. The clean re-run is now guarded by a before/after md5 of
scripts/ — never edit source while a suite is running, and never report such a run red.

**2026-09-19 — deck work, two classifier holes, and the handoff caught up.** Working tree
clean, full pytest exit 0, `make postedit` green, `check_docs` resolves 114 rules. Branch
`claude/sync-commands-mmmsdb`; PRs #183/#184/#185 merged.

**Deck 16 is a different deck** — rebuilt as the roster's waterbend deck, tuned nine swaps
to the A metrics floor, then one land (Plains → Gleaming Bastion). Its `#: notes:` carries
the negative results so they are not re-derived. **`prune-analysis.md`'s overlap numbers
predate it.**

**Two classifier holes closed, both 0 tier floors moved:** mass bounce now scores as a
Sweeper, and **K-16** — `tribes` no longer reads a card's own NAME as a tribe (367 → 336
payoff rows, 0 newly admitted). K-16's lesson is about REUSE: `_upgrade_clauses` lowercases
and `_tribe_ref_re` is case-SENSITIVE, so the obvious routing would have emptied the payoff
list while looking like a fix.

**CLOSED from the entry below:** G-31 now documents `structural_overlay_hit`, not just the
saturation warning. **Also closed:** the live analysis-doc list in CLAUDE.md said THREE and
named the wrong set (`uw-equipment-analysis.md` was live and unlisted); corrected to FOUR,
and `56-tall-pile-analysis.md` deleted — finished since 2026-09-06.

**Open, numbers already taken (do not re-derive):** BS8-33 discards a whole clause, so a
lord that references a type AND creates a token of it in one sentence is under-counted;
the create-span fix admits 17 more at 12 real / 5 false. See `docs/gotchas.md` `[K-16]`.

**Still open from before:** G-22's RELATIONAL gap (card × card, the bigger half of the
median-rank finding) remains the obvious next batch — untouched by any of the above.

Earlier in the same cycle:

**KEY saturation fixed (2026-09-18).** Full pytest exit 0, `check_all` exit 0 with soft warnings identical to baseline, `check_suggest` OK, anchor 11c watched-it-fail against a regressed implementation, output deterministic across three hash seeds. Block: `.cycle/blocks/2026-09-key-saturation-earned-signature-broad-implement.md`. NET SCORE 1 − 0 = 1. The finding in `.cycle/NEXT-SESSION.md` is marked CLOSED with its result.

**THE REJECTED TIGHTENING STILL STANDS — do not confuse the two.** `tests/test_deck.py::test_the_signature_rescue_is_preserved` pins it and its docstring now spells out the difference: the rejected fix REMOVED the branch's effect (deck 30 21% → 1%, Innkeeper's Talent demoted); this one makes it CONDITIONAL and lets an unearned generic signature fall through to branches that can still return KEY (deck 30 27.7% → 27.7%, Innkeeper's Talent kept).

**Docs outstanding — `/sync-docs` next:** G-31 still describes the saturation WARNING as the remedy and should record that a generic signature now has to earn its KEY; the NEXT-SESSION closure is written but CLAUDE.md is not; any figure cited in a rule needs a `figure_drift` entry.

**The bigger half of G-22's median-424 is UNTOUCHED and is the obvious next batch:** the RELATIONAL gap. Card × card relations that no per-card category encodes — Seek the Heart ranked 645 for deck 41 because "tutors a legendary creature" plus "this deck's payoff IS a legendary creature" is a relation between two cards, not a property of either. `deck.py targets` is already the primitive for that shape; G-40 governs wiring it into a ranking, and this batch is a worked example of why (the first `screen` measurement was vacuous until the population was checked).

Earlier in the same cycle:

**F2 implemented and F4 declined (2026-09-18).** Full pytest exit 0, `check_all` exit 0 with soft warnings identical to baseline, Scenario 2 PASS, determinism byte-identical. Block: `.cycle/blocks/2026-09-nonland-sources-and-paylife-decline-broad-implement.md`. NET SCORE 1 − 0 = 1 — **F4 is deliberately NOT counted as a fix**; a measured decline is the defensive bucket, and counting a decision as a fix is the self-report inflation cycle 9's `/reflect` had to correct.

**DO NOT RE-PROPOSE THE PAY-LIFE ⚡ RULE.** The full measurement lives at `_COST_UPSIDE` in `scripts/deck.py`, in the shape G-42 uses. The one-line reason: the flag asserts "this cost FEEDS something", and paying life feeds nothing unless the deck holds a lose-life payoff — 1 of 112 decks does, and it is not deck 41. What deck 41 needed was the weaker claim "this cost is CHEAP here", which no model holds and which its own `#: notes:` now carries.

**Docs are DONE for both batches (`/sync-docs`, 2026-09-18).** New rule **G-86** (board-presence axis) with its `docs/gotchas.md` long form; **G-35** records the nonland disclosure and **G-41** the pay-life decline, both with long forms; **G-27** records board power as an audited family. All four bullets are under `WORD_CAP` (289 / 269 / 201 / 265). README gained the board-power and nonland-source paragraphs. **Three figures registered in `check_docs.figure_drift`** — the roster median board power, the unknown-power deck count and the nonland-source deck count — from ONE shared cached roster walk, routed through `board_power` and `uncounted_mana_sources` themselves rather than a second copy of either predicate. **Watched-it-fail**: corrupting all three in place made the sweep report all three with the correct live values (54 / 70 / 75), so the patterns are live rather than silently dead. `check_docs` reports 113 rules linked; test files 32 and gates 13 still match C-07/C-01.

**New follow-ons:** `_GRANTED_ABILITY_RE` does not phrase-match "Enchanted land has …", so one land-upgrading aura reads as a nonland source (a `lib` fix, which the land count would inherit). Deck 23's `#: notes:` workaround is now superseded by the tool and could be retired — a deck edit, out of scope. `_MANA_SOURCE_RE` remains correct for its one `early_mana` caller and measurably wrong for any second.

Earlier in the same cycle:

**F1 + F3 implemented (2026-09-18).** Full pytest suite exit 0, `check_all` exit 0 with soft warnings IDENTICAL to the pre-change baseline, Regression Scenarios 2 and 19 PASS, determinism byte-identical across three hash seeds. Block: `.cycle/blocks/2026-09-board-power-axis-and-figure-disclosure-broad-implement.md`. NET SCORE 2 − 1 = 1.

**FOUR documentation items are outstanding and they are the next step** — `/sync-docs`: a CLAUDE.md Common Gotchas rule for the board-power axis (every sibling report-only metric has one: G-25, G-60, G-85 — without it a future session neither knows the axis exists nor that report-only is deliberate); the `docs/gotchas.md` long form with the measurements; `check_docs.figure_drift` registration for whichever figures land in CLAUDE.md; and G-27 recording board power as an audited family plus the new disclosure line.

**Two findings from the same triage are NOT implemented and are the obvious next batch.** F2: `consistency` reads LAND text only (G-35) so it cannot price a rock or a dork, while `suggest --ramp` recommends them and prints "acceleration want: HIGH" — **40 of 112 decks run at least one invisible nonland source**, 6 run three or more, and TWO decks (41 and 23) have independently hand-written the workaround into their `#: notes:`, which by this project's own rule means the RULE is what is wrong. The fix is a disclosure line on `consistency`, NOT widening `deck_source_profile` — a rock is not a land drop and that count sits behind six surfaces. F4: `_COST_UPSIDE` has no pay-life rule, which is why three cards were graded down for costing life in a deck whose thesis is spending life for cards; **do the G-42-style precision measurement BEFORE writing any rule** — that flag was built, measured at ≤14% precision with 23 of 44 hits backwards, and declined.

**New follow-on found while reading prose for F3:** the `keepable` figure patterns require a `%` sign, so deck 41's "keepable 84.4 to 86.0" is registered-but-unreachable.

Earlier in the same cycle:

**BS14 + the doc sync are implemented and committed (2026-09-17).** 1813 tests pass, `check_all` exit 0, `check_docs` zero drift, `make postedit` exit 0. Block: `.cycle/blocks/2026-09-hybrid-surfaces-keepable-figure-and-doc-sync-broad-implement.md`. NET SCORE 2 − 0 = 2. **No documentation items are outstanding** — the three BS13 raised are done.

**The WORD_CAP caught its own author for the second cycle running**: writing the G-26 update pushed that rule to 347 words and the gate refused it, which is the mechanism working rather than a defect.

**Still open:** `deck.py mana`'s `△ Pip-intensive` lint is the last reader of the raw strict/hybrid split inside `cmd_mana`, so a binding hybrid does not raise it; G-43's 102/308-vs-63/213 population mismatch; `doubler_axis`'s single-axis return; `cmd_suggest_homes`' positional tuple indexing. **Human calls: deck 27 (new RE-GRADE CANDIDATE), 45 and 47 tier letters.**

Earlier in the same cycle:

**BS13-01/02 implemented and committed (2026-09-17).** 1813 tests pass, `check_all` exit 0 with the rationale sweep now CLEAN where five decks had been silently arguing from wrong numbers, `make postedit` exit 0. Block: `.cycle/blocks/2026-09-hybrid-binding-pips-and-copula-figures-broad-implement.md`. NET SCORE 2 − 0 = 2.

**Three doc updates are outstanding** (all named in that block): G-32 and G-36 plus the `cast_probability` docstring still state "hybrids excluded (strictly easier)", now true only while BOTH halves are live; and G-26 should record the copula residual as closed for the three axes while the word-spelled and PERCENTAGE residuals remain open. **`deck.py mana` and `build_dashboard.py` still treat a zero-source hybrid as unconstrained** — deliberately out of BS13's scope (neither is a probability surface), but they are now the only surfaces that disagree with the model. **Open human calls: deck 27 (new), 45 and 47 tier letters.**

Earlier in the same cycle:

**BS12-01/02 are implemented and committed (2026-09-17).** 1810 tests pass, `check_all` exit 0, `check_docs` reports ZERO drift across 21 registered figures. Block: `.cycle/blocks/2026-09-prose-budget-and-figure-registry-broad-implement.md`. NET SCORE 2 − 0 = 2.

**Two doc updates are STILL outstanding** and were deliberately left out of BS12 to respect its scope: G-33 should record the doubler active-voice branch and G-31 should name the `suggest-homes` KEY-saturation warning (both from the BS11 block). `/sync-docs` is the way in. **One follow-on needs a decision**: G-43's "102 of the pool's 308" could not be registered because 308 and 213 count two different populations in one sentence — it needs the original derivation before it can be gated.

Earlier in the same cycle:

**BS11-01/02/03 are implemented and committed (2026-09-17), on top of a match ingest and a roster-wide ownership reconcile.** 1809 tests pass, `check_all` exit 0 with the same single pre-existing soft warning. Block: `.cycle/blocks/2026-09-doubler-active-voice-and-fit-saturation-broad-implement.md`. NET SCORE 2 − 0 = 2. **Two CLAUDE.md doc updates are outstanding and named in that block** (G-33 should record the active-voice branch; G-31 should name the new saturation warning) — `/sync-docs` is the way in.

Earlier in the same cycle:

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
