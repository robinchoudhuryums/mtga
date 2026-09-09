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
Cycle: 9 — a fresh `/broad-scan` ran 2026-09-08 after cycle 8's work merged, which is what
increments the number. Cycle 8's blocks stay under their own prefix.
Phase: implement (a second implement pass on cycle 9, from a deck-session post-mortem
rather than from the scan's finding list)
Scope: broad
Test Command: `python3 scripts/check_all.py`
Subsystem cycles since last Seams audit: 0 (counter adopted 2026-09-08; no Seams audit has run)
Updated: 2026-09-09 (second pass)

## In progress (facts to carry forward — NOT judgments)
- **Broad scan #9 is FULLY IMPLEMENTED** — all 8 findings, 4 batches, blocks `09-batch1-*`,
  `09-batch2-and-followons-*`, `09-batch3-4-*`. Nothing from the scan is outstanding.
- A FIFTH implement block landed 2026-09-09 from a different source: a post-mortem of the
  deck 39/58/74 tuning session, which asked what caused the card misreads. Three tooling
  fixes came out of it; two built, one measured and declined. Block
  `09-swap-gate-and-type-scale-broad-implement.md`, and a SIXTH closing that block's own
  follow-on list plus a `/sync-docs` pass — `09-followons-and-syncdocs-broad-implement.md`.
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

## Pending / not yet done
- The unapplied cross-deck homes and earlier proposed swaps — NEXT-SESSION.md §0-current.
- Two G-67 role-pattern holes (Kitnap, Eluge), baselined not fixed.

## Open follow-on items
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
The previous pass's follow-on list is CLOSED — one done, three measured and declined — and
`/sync-docs` has run and applied. Gate green, **1783 pytest passed / 0 skipped**, Scenario 2
walked, docs synced with a new G-84 anchor in both files.
**The finding worth carrying forward is not any single fix**: wiring `unmet_gate` to a
40-row craft table proved a primitive that had been correct enough for `swap` and
`redundancy` was **85% wrong there** (82 hits, 12 real), and `figure_drift` then caught a
real bug in that same pass's own CLAUDE.md text within minutes of the entry being added.
Both say the same thing — a measurement is only as good as the surface it was taken at.
Next step is unchanged and now cheaper: (a) `/reflect` on cycle 9, which has six implement
blocks and has still never run, and this pass gives it a clean `2 - 0 = 2` beside the
previous one's `1 - 1 = 0, defensive 1`; or (b) the DECK work in Pending, the only thing
here a player would notice.
