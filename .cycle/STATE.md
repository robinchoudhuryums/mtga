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
Phase: verify
Scope: broad
Test Command: `python3 scripts/check_all.py`
Subsystem cycles since last Seams audit: 0 (counter adopted 2026-09-08; no Seams audit has run)
Updated: 2026-09-08

## In progress (facts to carry forward — NOT judgments)
- **Broad scan #9 is FULLY IMPLEMENTED** — all 8 findings, 4 batches, blocks `09-batch1-*`,
  `09-batch2-and-followons-*`, `09-batch3-4-*`. Phase is now verify/reflect, not implement.
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

## Pending / not yet done
- The unapplied cross-deck homes and earlier proposed swaps — NEXT-SESSION.md §0-current.
- Two G-67 role-pattern holes (Kitnap, Eluge), baselined not fixed.

## Open follow-on items
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
- The full history of what was decided against lives in `.cycle/HISTORY.md`.

## Where I left off
All four batches of broad scan #9 committed and pushed on `claude/sync-commands-mmmsdb`; gate
green, **1761 pytest passed / 0 skipped**. The scan is closed — nothing from it is outstanding.
**Next concrete step is a choice, not a queue:** (a) `/reflect` on cycle 9, which has never run
and is the whole reason `defensive_count` was adopted — 9 of the 10 items across batches 2–4
were defensive, and the metrics row would say so for the first time; (b) `/sync-docs` for the
one G-15 clause the last block names; or (c) the DECK work in Pending above, which is the only
thing here a player would notice.
