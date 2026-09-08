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
Phase: implement
Scope: broad
Test Command: `python3 scripts/check_all.py`
Subsystem cycles since last Seams audit: 0 (counter adopted 2026-09-08; no Seams audit has run)
Updated: 2026-09-08

## In progress (facts to carry forward — NOT judgments)
- Broad scan #9 produced 8 findings in 4 batches. **Batch 1 is DONE** (F1, F4, F8) —
  block `.cycle/blocks/09-batch1-broad-implement.md`. Batches 2–4 are not started.
- Deck 71's rebuild has an ordered open list — see §0-current of NEXT-SESSION.md.

## Completed this cycle
- Template sync v1.23.0 → v1.33.0 | `.claude/commands/broad-scan.md`, CLAUDE.md, docs/cycle-config.md
- Tier-3 re-evaluation; state-and-measurement half adopted | `.cycle/`, `.claude/commands/`, CLAUDE.md
- Skill-discoverability fixes | tune-deck Stage 8 handoff, systems-map promoted to intent
  router, three skill descriptions de-truncated
- Broad scan #9 (audit only, no writes) | 8 findings, 4 batches
- **Batch 1** | F1 pool-first synergies + F4/F8 stale figures | scripts/deck.py, CLAUDE.md,
  ROADMAP.md, decks/15, decks/40

## Pending / not yet done
- **Batch 2 — the guards that would have caught Batch 1.** F1b: a cross-file `Synergies`
  agreement check in check_agreement (UNBLOCKED by F1, and it must land AFTER F1 or it goes
  red on arrival). F3: extend `figure_drift` past its 6 hand-kept entries, including the
  tier-floor spread F4 just corrected.
- **Batch 3 — silent degradation and roster scope.** F2: sub-majority `if err_decks:` warning
  in build_dashboard (its craft sibling has one, the detail-panel scan does not, so 1–49% of
  decks can publish `[analysis error]` panels silently); adopt Scenario 19. F5: route
  `wishlist.py:1535/689/813` through `roster_decks()` before the roster prune lands.
- **Batch 4 — the editor's untested boundary.** F6: tests for `_guard_request` (Host +
  Origin) and for `/api/revert`, `/api/remove`, `/api/add`. F7: decide whether to retire the
  absent-token save bypass.
- The unapplied cross-deck homes and earlier proposed swaps — NEXT-SESSION.md §0-current.
- Two G-67 role-pattern holes (Kitnap, Eluge), baselined not fixed.

## Open follow-on items
- `K-09` reads as though "the pool is the corrected store" is a fact about the FILES; it is
  now true of the MODEL too. Record it there — `/sync-docs`.
- `G-30` says "Run it before a tune" of `deck.py rotation`, but its absence from `/tune-deck`
  is DELIBERATE (recommendations ignore rotation so the human decides). A future session will
  try to re-add it; the rule needs the exception written in.
- ROADMAP.md line 12's "of which 51 are PROVISIONAL" was not re-measured.
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
Batch 1 committed and pushed on `claude/sync-commands-mmmsdb`; gate green, 1729 pytest pass,
`make postedit` clean. **Next concrete step: Batch 2**, and F1b specifically — it is the guard
that would have caught F1 the day BS8-31 shipped, and it is only safe to add now that F1 has
landed. Run `/broad-implement Batch 2` or pick another batch from Pending above.
