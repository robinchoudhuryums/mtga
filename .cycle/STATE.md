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
Cycle: 11 — `/broad-scan` #11 ran 2026-10-01 (81 findings, BS11-01…BS11-81, nine batches).
Phase: implement — **Batches 1 (ingest), 2 (deck legality + parse gates) and 3 (search filters) DONE 2026-10-02**; Batches 4–9 not started.
Scope: broad
Test Command: `python3 scripts/check_all.py`
Subsystem cycles since last Seams audit: 3 (counter adopted 2026-09-08; no Seams audit has run)
Updated: 2026-10-02 (Batch 1 — see Where I left off)

## In progress (facts to carry forward — NOT judgments)
- **Broad scan #10 is fully implemented — nothing outstanding from the scan.** Four
  blocks: `10-batch1-2-ranking-visibility`, `10-batch3-followons-artifacts-tagger`,
  `10-batch4-interaction-taxonomy`.
- **One finding was REFUTED rather than fixed: BS10-02.** The one-turn tap-down exclusion is
  deliberate and documented; widening it would have added 36 cards to the axis `tier_band`
  grades. Recorded at the exclusion itself so a re-file lands on it.
- **Deck 47's tier letter is CLOSED** — re-graded B → A on 2026-09-27 at the owner's call,
  with decks 17 (C → A) and 42a (B → A); all three now match their A floors.
- The cycle's number was `suggest`'s rank median **407**; batch 2 disclosed it and batch 3
  fixed its largest cause (deck 47's own picks: median 310 → 144).

## Completed this cycle

- **2026-10-02 — scan #11 Batch 4: tagger accuracy** (BS11-75–79). Block
  `11-batch4-tagger-accuracy-broad-implement.md`. Net 5 − 0 = 5 | scripts/tag_synergies.py,
  scripts/check_patterns.py, pool rebuild, tests.
- **2026-10-01 — the test suite no longer reverts the real card library (G-88).** An editor
  test POSTed `/api/revert` without its fixture, so every pytest run (including the
  SessionStart hook's) restored the newest `.bak` over `card-library.csv`. Fixed the test,
  added an autouse library sandbox to `test_app_editor.py`, and a `tests/conftest.py`
  session guard over the data files, deck files and `.bak` names (watched it fail on the
  old test). Commit 10e273f.
- **2026-10-01 — three tool gaps from the deck 30 tune closed** (`/broad-implement`).
  G-33 gap 2: `doubler_best` prices a two-axis doubler (Doubling Season) on the axis the
  deck feeds most, and the tagger's `counters` rule reads "one or more counters" (12 pool
  cards). G-38: `deck_needs` reads `deck_color_sources` — 53 of 114 `--needs` headers
  changed, 0 now disagree with `consistency`. K-12: one-sided damage sweeps score Sweeper
  (15 pool cards; decks 30 and 56a +1 interaction). 0 tier floors moved. Block:
  `2026-10-three-tool-gaps-broad-implement.md`. Net 3 − 0 = 3 | scripts/deck.py,
  scripts/tag_synergies.py, pool rebuild, tests, G-33/G-38/K-12
- **2026-09-27 — six match-logging follow-ups from the first real play-by-play run.**
  The ingest now asks for a one-word reason per NEW loss and prints a ready `--annotate`
  line with the game details (0 of 191 rows had any hand column); `mtga-matches`
  anonymises the paste to `ME`/`OPP` and remembers its last copy's date (`all` copies
  everything); `--report --deck <id>` prints one deck's history, shown by `/tune-deck` 2e
  as context only; a new match with no play-by-play is named; and the newest of several
  same-named Arena decks wins the `#: arena:` header instead of warning every run (deck 58
  moved to its newest copy). Block: `2026-09-match-logging-followups-broad-implement.md`.
  Net 5 − 2 = 3 | scripts/parse_matches.py, tests, `/log-matches`, `/tune-deck`, G-74
- **2026-09-27 — the match digest (PR #196).** `scripts/mtga_extract.sh` reduces each
  game's play-by-play to one `[MTGA-GAME]` line; the parser fills On Play (blank cells
  only), mulligans, Turns and opponent colours/cards, naming cards via Scryfall's Arena-id
  lookup cached in `arena-cards.csv`. Seat read confirmed by the owner on nine real games.
  `.cycle/match-digest-plan.md` deleted as its header asked.
- **2026-09-27 — decks 17, 42a and 47 re-graded to A at the owner's call.** Each `#: tier:`
  block rewritten to argue the A (the old blocks argued a cap below the floor) and to carry
  the real risks as caveats; `tier` reads "consistent" and `--audit-rationale` is current on
  all three. Stale facts corrected in the same pass: 42a and 47 were called unplayed (3-3
  each, n=6), 47 "unbuilt with ten craft targets" (fully owned), 42a cited Hero's Downfall
  as staying (cut) and a 2.91 curve (live 3.14) | decks/17, decks/42a, decks/47
- **2026-09-26/27 — decks 17 and 30 tuned; three tooling holes documented.** Deck 17's
  manabase rebuilt from owned fixing plus several swaps (Oltec Matterweaver the one craft,
  also slotted into 21, 74a, 42a). Deck 30: fifteen owned swaps across six commits, green
  sources 12 → 15, cards under 90% on curve 33 → 21, floor held A at interaction 7 / card
  advantage 7. The tune surfaced three holes, written up under G-33, G-38 and K-12 by the
  `/sync-docs` pass rather than fixed — see Open follow-on.

- **2026-09-26 — G-87: a colour gated on a land TYPE was counted as a full source.**
  The Verge cycle ("Activate only if you control a Mountain or a Plains") and the MSH
  basic cycle ("…or if you control a basic land") read as FREE in `lib.land_production`,
  so `mana` / `consistency` / `pip_depth_warning` / the rationale audit all treated them as
  always on. Now `land_production` reports `gated` (subset of `free`), and
  `deck_source_profile` credits each by `lib.gated_source_credit` (P one of the two other
  lands on turn three carries a named type — the `_CHECKLAND_BASIC_FLOOR` framing), rounded
  per colour. Validated against a gate-honouring Monte Carlo on nine decks: tool Δ tracks
  sim Δ within ~1.1 points mean, against a 4.6-point bias removed. Roster: 93/114 decks
  run a gated land, 42 changed source counts (all down), **0 tier floors moved**. Three
  stale source figures re-grounded (decks 78, 68a) and deck 17's tier block rewritten.
  `_LAND_GATE_RE` registered in `check_patterns`; tests watched to fail with the pattern
  dead. Residuals (recommender half, `tapland_kind` basics-only twin, Leyline of the
  Guildpact, unaudited per-card %) are in the G-87 long form and under Open follow-on.

- **2026-09-23 — F-LAND-01/02/03: the checkland gate read the basic COUNT, never the
  basic TYPE, and `/tune-deck` was not running the land recommender at all.** Both
  shipped. `_TAPLAND_CHECK_RE` matches the generic "a basic land" AND the type-named
  cycle ("a Plains or an Island"); both collapsed to kind `check`, so a land gated on
  basics the deck does not run took the untapped premium — **81 (deck, land) pairs across
  54 of 114 decks**. New `lib.tapland_check_types`; `tapland_kind` takes `basic_types` and
  returns `unconditional` for an unmeetable gate. Roster diff: **79 scores moved, 91 rider
  labels corrected, 63 decks changed a row, 6 decks' #1 pick changed**, every one off a
  land it can never untap. `/tune-deck` step 5c now runs `suggest --lands` EVERY run.
  Three land swaps applied (deck 2 +2nd Fire Nation Palace; deck 1 +2nd Blazemire Verge
  and +2nd Blood Crypt for its two unconditional taplands). Block at
  `.cycle/blocks/2026-09-checkland-types-and-tune-deck-land-gate-broad-implement.md`.

- **2026-09-22 — F-CUTS-01 (plan-aware `cuts`) BUILT, MEASURED and DECLINED.** No
  production code changed. 40 hits over 205 cards in the only **8 of 114 decks (7%)** it
  could fire on; **25 clearly false, precision <= 37.5%**, against G-41's 22% and G-42's
  <=14%, both declined. It flags aggro FINISHERS as off-plan (Aurelia in two decks),
  re-opens G-60/G-83 on cost-reduced cards, fires backwards on deck 73a's own tap engine,
  and `_MANA_SOURCE_RE` matched a FIGHT spell. Decisive: it **could not fire on deck 1**,
  the case that produced it. Numbers in `.cycle/HISTORY.md`; block at
  `.cycle/blocks/2026-09-f-cuts-01-plan-aware-cuts-broad-implement.md`. Two zero-code
  residuals survive and are NEXT-SESSION item 0.
- **2026-09-22 — deck 1 tuned (six applied swaps).** Manabase rebuilt from 4 owned-but-
  unplayed Dark Fortress + Blood Crypt (B 13->17, cards below 90% on curve **15 -> 7**,
  Massacre Wurm 44.3% -> 66.4%), then Sawblade Skinripper, June, Slash, Rat King, Gisa and
  Doctor Doom in for Tome Blast, Diamond Pick-Axe, Kav Landseeker, Prickly Pair, Wick's
  Patrol and Fire Nation Raider. Protection **1 -> 3**, card advantage 6 -> 7, floor holds
  A. Two rare crafts outstanding (Slash, Rat King).

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
- The unapplied cross-deck homes and earlier proposed swaps — NEXT-SESSION.md §0-current.
- Three G-67 role-pattern holes, baselined not fixed: Kitnap, Eluge and Cheering Crowd
  (conditional mana) — K-12's long form has the probe. (Soul Immolation closed 2026-10-01.)

## Open follow-on items
- **suggest-homes' KEY-saturation warning misattributes a doubler-density KEY** to theme
  overlap ("KEY scores THEME OVERLAP ALONE") — the whole counter-doubler family now trips
  it at ~23–28% of the roster, which the counters key-at-p75 calibration predicts.
- **`structural_overlay_hit` ignores a doubler's power restriction** while `doubler_best`
  applies it (G-70 shape, pre-existing).
- **The match digest plan's decision 2 is unbuilt: a `Suggested Why` column** the owner
  confirms in one reply (owner, 2026-09-25). What shipped asks for the word with the game
  details beside it and suggests nothing. Build it only if the owner still wants a
  suggestion; it would slot into `parse_matches._print_loss_prompt`.
- **Best-of-three play-by-play is unverified** — `mtga_extract.sh` assumes game N is the
  Nth `MatchScope_Game` result; no Bo3 log has been read.
- **A paste covering only an OLD Arena copy's period moves the `#: arena:` header back to
  that copy** (one claimant, so nothing to compare). Attribution is unaffected; the next
  paste carrying the newer copy moves it forward again.
- **`consistency`'s NONLAND disclosure (G-35) is silent on two real mana engines (found
  2026-09-27, deck 21).** `lib.land_production` reads Bloom Tender's Vivid clause ("For each
  color among permanents you control, add one mana of that color") as producing NOTHING, so
  `uncounted_mana_sources` omits it and the page prints no `ⓘ NONLAND` line at all; Enduring
  Vitality ("Creatures you control have '{T}: Add one mana of any color'") is a GRANTED
  ability, excluded by G-35's design. Deck 21 now runs both, so its cast-on-curve figures are
  floors with nothing saying so. The Vivid pattern is a G-67 pattern hole (measure the pool
  before widening); the granted case is a disclosure question, not a counting one.
- **Three stale `#: tier:` claims passed `--audit-rationale` on deck 42a (found 2026-09-27
  while re-grading it).** (1) "…what the uncounted pieces cannot replace is a cheap
  unconditional answer on demand, which is why Hero's Downfall stays" — Hero's Downfall had
  been cut, and the citation was suppressed by `_HISTORY_CUES` matching the ORDINARY verb
  "replace" in the same clause (probed: removing the sentence's "CUT" changes nothing). The
  `remov\w*` / `over` / `rather than` shape again, one word over. (2) "the reported 2.91 is the real
  number" against a live avg MV 3.14: no curve cue adjacent to the figure (G-26's
  adjacency residual). (3) "PROVISIONAL (unplayed brew)" with six logged matches: the
  audit reads no match record, by design. Deck 47 carried (3) too, plus "ten craft
  targets" on a fully owned list. All corrected by hand. For (1), measure what a narrower
  `replac\w*` cue (e.g. requiring "replaced"/"replacing"/"replaced by") would surface on the
  roster before changing it — G-26: keep the cue lists narrow, let a sweep be the check.
- **`doubler_axis` returns ONE axis (G-33 KNOWN GAP 2).** Doubling Season is priced as a
  tokens-only doubler everywhere (`✱`, `screen`, `suggest-homes`, `cuts`), and a doubler
  that says bare "counters" gets no `counters` tag (Doubling Season, Loading Zone, Doc
  Samson). Fix shape: multi-axis return taking the best-supported axis + a `counters` tag
  for the generic replacement — measure roster-wide first (G-40).
- **`deck_needs` counts land sources from colour IDENTITY (G-38).** The one surface not on
  `deck_source_profile`; it also chooses the "scarcest" colour the fixing list is nudged
  toward. Route it through the profile and re-measure the fixing picks.
- **G-87 recommender half** — `suggest --lands` and `wishlist._land_value` still score a
  Verge's gated colour as full fixing (they read `free`). Pricing the gate there is a
  separate measurement (G-40). Also: `tapland_kind`'s checkland type gate counts basics
  only while G-87's source gate counts typed nonbasics — two answers to one question.
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
- **Same-named Arena decks: the NEWEST wins (owner, 2026-09-27).** An edited deck is
  re-imported as a new Arena deck and the old one deleted, so copies are expected and the
  latest `LastUpdated` is correct. Two DIFFERENTLY named claimants are still a conflict,
  and the comparison is typography-only — never `_name_key`, whose gloss strip reads
  "X (old)" as a copy of "X".
- **Never fill a loss reason in yourself.** `/log-matches` Stage 1d asks the owner; the
  game details say what happened, not what decided it.
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
**2026-10-02 (latest) — scan #11 Batch 4 implemented** (block
`11-batch4-tagger-accuracy-broad-implement.md`): BS11-75/76/77/78/79. Tribal tags resolve
against the real type list; blink/graveyard/burn false positives closed; one spelling per
theme. Pool rebuilt with the stamped query (16,047 rows); 0 tier floors moved, cuts top-3
changed in 10 of 114 decks. Full suite and `check_all` green. **Next:** `/sync-docs` for
Batch 4 (K-09 figure 348→350 is the one soft drift), then Batch 5 (recommender maths:
BS11-16/31/61/67–72/74).

**2026-10-02 (latest) — scan #11 Batch 3 implemented** (block
`11-batch3-search-filter-semantics-broad-implement.md`): BS11-39/34/41/54. The new card.py
agreement pair found load_card_meta's pool-first tag correction missing front-named DFC rows;
fixed in the same batch (10 cards, 8 decks). Full suite and `check_all` green; gallery and
dashboard rebuilt. **Next:** `/sync-docs` for Batch 3, then Batch 4 (tagger: BS11-75–79 —
needs `make refresh` (network) and a roster diff).

**2026-10-02 (latest) — scan #11 Batch 2 implemented** (block
`11-batch2-deck-legality-parse-gates-broad-implement.md`): BS11-01/02/03/04/05/07/08/09/10/11/12/73.
Full suite and `check_all` green; dashboard rebuilt (its paste matcher gained the OVERSIZED flag).
**Next:** Batch 3 (search filters: BS11-39/34/41/54), then 4–9 as listed below. Docs for Batch 2
need a `/sync-docs` pass (the block lists them). Also today: deck 23 swapped Origin of the
Avengers for Captain America's Shield (owner's swap).

**2026-10-02 (latest) — scan #11 Batch 1 implemented** (block
`11-batch1-ingest-correctness-broad-implement.md`): BS11-19/20/21/22/23/24/25/26/27/28/29/30.
Full suite and `check_all` green. The pool fingerprint value changed, so the next `make refresh`
rebuilds the pool once. **Next:** Batch 2 (deck legality + parse gates: BS11-01/02/03/04/05/07/
08/09/10/11/12/73). The scan's batch plan is in the 2026-10-01 chat only — Batches 2–9 list:
2 legality/parse, 3 search filters (BS11-39/34/41/54), 4 tagger (75–79, needs network + roster
diff), 5 recommender math (16/31/61/67–72/74), 6 format drift (06/13/14/15/17/18/40), 7 matches
(32/33/35–38), 8 editor/dashboard (42–53), 9 docs (55–60, 62–66). Deferred: BS11-80, BS11-81.
Same day, earlier: Reality Fracture refreshed into the pool; decks 55 and 60 FRA swaps applied.

**2026-10-01 (latest) — G-88 fixed, docs synced, PR opened.** The revert-test leak is closed
(10e273f) and `/sync-docs` landed G-88, the README doubler/`--needs` lines, the systems-map
inventory rows and the cycle-config C-07 note. **Trap for every later session: never edit a
data or deck file while a suite runs — the new conftest guard fails the run.**

**2026-10-01 (later) — deck 55 shocklands, then the three tool gaps.** Deck 55 swapped
Scoured Barrens and Sun-Blessed Peak for second copies of Godless Shrine and Sacred Foundry
(commit fde63e2). Then `/broad-implement` closed G-33 gap 2, G-38 and K-12 (block
`2026-10-three-tool-gaps-broad-implement.md`); full suite and `check_all` green. The pool
rebuild also pulled 9 Reality Fracture reprints into Standard legality. **Next:** unchanged
— after 2026-10-02, `make refresh REFETCH=1` and apply the 13 queued FRA swaps; loss
reasons for three losses and tier letters for 55/60/78 are with the owner.

**2026-10-01 — `/sync-docs` over the 47 commits since PR #197**, then a PR. README now
describes the play-by-play columns, `void=`, `--report --deck`, the Brawl commander export
and per-60 Brawl grading; CLAUDE.md lists the two live pile docs and G-79 carries the
early-release inverse (Reality Fracture). **Next:** after 2026-10-02, `make refresh
REFETCH=1` and apply the 13 queued FRA swaps (decks 55 and 60) — NEXT-SESSION.md has the
list. Loss reasons for three new losses are still with the owner.

**2026-09-27 — six match-logging follow-ups implemented** (`/broad-implement 1-6`) on
`claude/sync-commands-mmmsdb`, restarted from main after PR #196 (the match digest)
merged. Full suite and `check_all` green. Deck 58's `#: arena:` header now names its
newest copy (e96eca40). **The owner still has to re-install `mtga-matches` on the Mac** —
the anonymising and the date memory live only in that function; the first run after the
re-install has no stamp and copies everything, once.

**Still open from earlier today:** the three tooling holes the deck 30 tune documented
(G-33 KNOWN GAP 2, the G-38 `--needs` holdout, the K-12 sweeper) — each needs its roster
measurement first (G-40, G-67).

**THE 2026-09-20 PROCESS RULE STILL HOLDS:** never edit source while a suite is running,
and never report such a run red.
