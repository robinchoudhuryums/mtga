---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- T-1 | Per-deck rotation view — `deck.py rotation <id>` (owned cards INCLUDED, by year, SOON flag) and a `check` footer naming OWNED cards that rotate this year or next; `_deck_atrisk` factored out so the roster sweep and the single-deck view share one routine
- T-2 | Cheat-cost advisory — `cheat_cost_cards` (Warp / Plot / Foretell / Evoke / Emerge / Spectacle / Surge / Miracle / Sneak priced below the printed cost); a ⌁ list in `stats`, a one-line "avg MV over-reads" note in `tier`; report-only, the X-cost under-read (G-60) in reverse
- T-3 | `suggest --lands` rider tie-break — `_land_utility` (creature / draw / scry / surveil / sink / ping / life, bounded 0–0.4) as a SORT-KEY tie-break only, never a score term; a `Rider` column
- T-4 | Scratch measurement by path — `find_deck(id, allow_path=True)` accepts an existing `.txt` for the 21 READ-ONLY commands; writers (`swap`, `move`, `apply-flex`) and roster-reasoning commands (`preflight`, `history`) keep the id-only form; a roster file's path resolves to its roster id

Files modified: scripts/deck.py, scripts/check_patterns.py, tests/test_deck_models.py, tests/test_deck.py, tests/test_cli.py

CHANGES:
T-1 | scripts/deck.py | `_deck_atrisk` (per-deck half of `rotation_sweep`), `deck_rotation(d, fmt=None, …)` (fmt=None reads the deck's own `#: format:`), `_cmd_rotation_deck`, `rotation` gains an optional `id` positional and `--format` defaults to None (roster sweep still assumes standard); `cmd_check` prints "ⓘ N OWNED card(s) rotate out this year or next (~YYYY: …) — `deck.py rotation <id>`" after the craft-target ⚠rot line, same within=1 window as `craft_rot_note`
T-2 | scripts/deck.py | `_ALT_COST_RE` (lookbehinds skip a GRANT — Tannuk's "have warp {2}{R}"), `cheat_cost_cards` mirroring `x_cost_cards`; `cmd_stats` CHEAT-COST block after the X-COST block; `cmd_tier` advisory line after the X-cost one
T-3 | scripts/deck.py | `_LAND_UTILITY_CUES`, `_land_utility`; `suggest_lands` picks carry `util`/`util_label`, sort key `(-score, -util, name)`; `cmd_suggest_lands` prints a `Rider` column and a legend sentence
T-4 | scripts/deck.py | `find_deck(deck_id, allow_path=False)`; 21 read-only `cmd_*` call sites pass `allow_path=True` (check, diff, arena, text, stats, tribes, suggest, mana, consistency, flex, legal, cuts, verify, similar, screen, quality, shape, redundancy, tier, targets, engines)
gate | scripts/check_patterns.py | `_ALT_COST_RE` and each `_LAND_UTILITY_CUES` entry registered in `_pattern_groups()` ("norm" corpus) — the completeness check failed the build on them, as designed
tests | tests/test_deck_models.py | `TestCheatCostCards` (real Bygone Colossus / Stingerback / Tannuk text; not in `deck_quality_vector`/`tier_band`/`_clock_score` source), `TestLandUtilityTieBreak` (each cue on real land text, bounded, reminder ignored, tie order, live 56 score untouched)
tests | tests/test_deck.py | `TestScratchPathResolution` (refused by default, resolves with allow_path, roster path → roster id, writers never pass allow_path), `TestDeckRotation` (single-deck view == sweep entry by construction; owned cards included; deck's own format)
tests | tests/test_cli.py | `TestRotationTakesADeckId` (`rotation <id>` prints one deck; a scratch path works for `stats` and is refused by `swap`)

TEST RESULTS: check_all — all invariants hold (after registering the two pattern sets with check_patterns: 322 patterns live). pytest — the 17 new tests pass; full suite: all passed (exit 0). Determinism spot-check: `suggest 56 --lands` byte-identical under PYTHONHASHSEED 0/1.
REGRESSION RISKS:
- `rotation --format` default changed from "standard" to None; `cmd_rotation` still resolves None → "standard" for the roster sweep, so the sweep output is unchanged. Only the per-deck view reads the deck's own format.
- `suggest --lands` ORDER changes only among equal-score lands (tie-break); every score is unchanged and pinned by a test. The `Rider` column widens the table by ~10 chars.
- `check` gains one footer line when a deck holds owned rotating cards — parsers of `check` output (none known; the dashboard reads `deck_build_gap`, not stdout) unaffected.
- `find_deck` with a path: a scratch record has `variant=True`, `core=<basename>`; `similar`/`tier --audit-rationale` treat it as a non-roster id — cross-deck citation masks resolve against the roster and will not mask the scratch's own name, which is expected for a scratch copy.
INVARIANTS AT RISK: None — no writer touched; INV-04 unaffected (scratch files live outside decks/ by design, which is the point of T-4).
NET SCORE: 4 − 0 = 4
  T-1 fired this month: YES (56a's Commercial District/Ridgeline found by hand 2026-09-06). New failure mode: NO.
  T-2 fired this month: YES (Colossus moved 56b's floor A→B, pile §5.7 item 6). New failure mode: NO (report-only, pinned).
  T-3 fired this month: YES (four-way 10.9 tie on 56, 2026-09-06). New failure mode: NO (tie-break only, pinned).
  T-4 fired this month: YES (every scratch measurement 2026-09-05/06 needed a temp variant in decks/). New failure mode: NO (writers refuse a path, pinned).

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Data + local tooling ship by commit/push; the dashboard is rebuilt by pages.yml on push to main (unchanged by this batch — no template edits).

FOLLOW-ON ITEMS:
- T-2 sees CARD-level alt costs only. A DECK-level grant (Tannuk giving warp {2}{R} to every red creature in hand) is a different question and is not priced — 56b's real curve is cheaper still.
- `_clock_score` still reads the printed avg MV; the aggro floor of a cheat-cost deck (56b) stays B until a human letter argues it, per the G-60 discipline. A measured "effective MV" term was NOT added (it would re-grade the roster).
- T-3's `sink` cue matched Iron Hills' Dwarf-only pump; the label is right (it IS an activated sink) but a type-restricted sink is worth less than an unrestricted one. Not split — the value is a tie-break.
- Pile §5.7 items 1/2/5/6 (role-pattern holes, damage-doubler axis, state gates) and the taxonomy decisions remain as listed in the 2026-09-06 chat assessment; items 5–6 of that list need a K-14 floor diff.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-30: `deck.py rotation <id>` is the per-deck view (owned included) and `check` now names owned rotating cards in a footer.
- CLAUDE.md G-60: add the cheat-cost twin (`cheat_cost_cards`, ⌁ in `stats`, "over-reads" in `tier`), same report-only rule.
- CLAUDE.md G-37/G-42: `suggest --lands` breaks ties by rider (`Rider` column); still never a score term.
- CLAUDE.md G-56: a scratch copy can now live OUTSIDE decks/ and be measured by path; writers refuse a path.
- docs/gotchas.md long form for each; `.claude/commands/tune-deck.md` could cite `rotation <id>` (check_commands is satisfied today via the bare `rotation` call).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
