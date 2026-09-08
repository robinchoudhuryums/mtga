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
Cycle: 8 — broad scan #8, merged as PR #169/#170 plus the cross-deck pass; numbering
adopted 2026-09-08 from the scan number the blocks and CLAUDE.md's BS8-nn anchors
already use. Increments only when a NEW audit cycle begins.
Phase: idle
Scope: broad
Test Command: `python3 scripts/check_all.py`
Subsystem cycles since last Seams audit: 0 (counter adopted 2026-09-08; no Seams audit has run)
Updated: 2026-09-08

## In progress (facts to carry forward — NOT judgments)
- Tier-3 adoption, this session: STATE.md split from HISTORY.md; `/cycle-init`,
  `/regression`, `/reflect`, `/cycle-status`, `/cycle-resume` vendored from template
  v1.33.0; `metrics.csv` backfilled from the blocks that already carry a net score.
- Deck 71's rebuild is landed but has an ordered open list — see §0-current of
  NEXT-SESSION.md (Melek rotates ~2026 and is a protected engine piece; Rapturous
  Moment is the craft to drop now the Lute is in; spell count 15 v 16 creatures).

## Completed this cycle
- Broad scan #8, seven implementation batches + a deck re-grade pass + two doc syncs |
  merged PR #163, then #169/#170 | blocks `2026-09-broad-scan-8-*`, `2026-09-04-*`, `2026-09-06-*`
- Template sync v1.23.0 → v1.33.0 | `.claude/commands/broad-scan.md`, CLAUDE.md, docs/cycle-config.md
- Tier-3 re-evaluation and partial adoption | `.cycle/`, `.claude/commands/`, CLAUDE.md

## Pending / not yet done
- The cross-deck homes from the 2026-09-08 pass, NOT applied: Whirlwing Stormbrood → 67,
  Death to Our Enemies → 72, Gandalf → 55a, Swallowed by Leviathan → 62,
  Pensive Professor → 37/37a (craft), Eject → 43 for Lake-town Toymaker.
- The earlier proposed swaps never applied (55, 39, 75, 46, 55b, 13, 37a, 69, 77, 31, 42a, 38)
  — listed in full in NEXT-SESSION.md §0-current.
- Two G-67 role-pattern holes surfaced by the deck-71 swaps, baselined not fixed: Kitnap's
  Aura-steal wording scores no Removal role; Eluge's "costs {U} (or {1}) less" scores no
  Cost-reduction role. Fix each with a K-14 roster floor diff, then prune from `role_baseline.txt`.
- Mabel, Heir to Cragflame is owned but absent from `card-pool.csv` — close on the next
  `make refresh REFETCH=1`.
- Unresolved card name "Fear of Immortality" (DSK has Fear of Immobility / Fear of Infinity).

## Open follow-on items
- `scripts/deck.py: _ROLE_PATTERNS` — the two holes above; measure floors before widening (K-14).
- `card-library.csv` — stale `sacrifice`/`ramp` tags survive because `--merge` cannot remove
  one; the pool is the corrected store (K-09).
- Regression scenarios 5–8 and 10–18 need a person at a browser and several have never
  been walked; scenario 11 is still the only thing that can prove the match-logging loop closes.

## Decisions made (so the next session doesn't re-litigate)
- Tier-3 `/audit`, `/plan`, `/implement`, `/systems-map`, `/setup-cycle` stay UNVENDORED —
  they duplicate the Tier-1/Tier-2 loop this project runs. Re-evaluated 2026-09-08 with the
  measurements in CLAUDE.md's Command provenance; only the state-and-measurement half was adopted.
- PROJECT_HEALTH.md deliberately NOT created: the Health Synthesis (§6a) is a console prompt,
  not a vendored command, and `/health-pulse` is read-only — the file would sit empty while
  reading as a live status board.
- The full history of what was decided against lives in `.cycle/HISTORY.md`; read it before
  re-proposing a rejected fix.

## Where I left off
Tier-3 partial adoption committed and pushed on `claude/sync-commands-mmmsdb`. Next
concrete step is the user's call between the deck work in Pending above (the unapplied
cross-deck homes, and deck 71's Melek/Rapturous Moment decisions) and the two G-67
role-pattern holes. Run `/cycle-status` first — it now reads this file.
