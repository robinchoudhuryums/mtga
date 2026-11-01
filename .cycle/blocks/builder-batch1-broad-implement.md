---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Builder batch 1 (.cycle/builder-scope.md) — data model, derivation and CLI, no UI
- B1a: `scripts/builder.py` — build files in `builds/<slug>/build.json` with `new / add / place / reason / check / picks / derive`
- B1b: derivation moved out of the session board's `refresh.py` into `builder.derive` / `builder.deck_live`, calling the deck model
- B1c: Sultai project migrated to `builds/sultai/build.json` (426 cards, 292 reasons, each stamped `graded_at` both decks' current list hash)
- B1d: tests (`tests/test_builder.py`, a `builder.py` subcommand-help test in `tests/test_cli.py`) and `check_commands` reachability (a real `python3 scripts/builder.py` call in `/pile-analysis` Stage 6)
- B1e: `check_all` soft sweep `builder_soft()` — a project whose reasons were written against an older deck list
- B1f: font decision recorded — pairing 1 (Marcellus SC / Spectral / IBM Plex Sans Condensed / IBM Plex Mono)
Files modified: scripts/builder.py (new), builds/sultai/build.json (new), tests/test_builder.py (new), tests/test_cli.py, scripts/check_all.py, .claude/commands/pile-analysis.md, .cycle/board/src/refresh.py, .cycle/board/src/data.json, .cycle/board/index.html, .cycle/builder-scope.md

CHANGES:
B1a | scripts/builder.py | A build stores only hand-made content (decks with keys, piles, card placements, reasons). Names resolve through deck._resolve_card_name; a name not on Arena (pool + library) or ambiguous is refused BEFORE anything is written, so a typo never leaves half a batch. A reason records `graded_at` = a 12-char hash of each deck's card multiset (quantity + `_ms_key`), so a swap marks it stale and a `#: notes:` edit does not. `check` reports stale / unknown / unplaced / reasonless / orphan; `--strict` exits 1 on stale or unknown. `picks` reads the board's "Copy as text" block and re-emits only the `swap --package` pairs whose cut is in the deck and whose add is not, explaining the rest. Writes go through lib.atomic_write.
B1b | scripts/builder.py, .cycle/board/src/refresh.py | `deck_live` (floor, interaction, card advantage, sources, tapped-land cost via `consistency --tempo`, crafts, avg MV, protect list, nonland list with `cuts` ranks, scaled floor thresholds) and `derive` (per-card facts, roles, ri/rc, in-list and protected flags, reason) now live in builder.py; refresh.py is a 30-line wrapper that derives from builds/sultai and renders template + data. Verified field-by-field against the previous data.json: every card field identical across 426 cards; both decks' live figures identical except the sources line, which `deck_color_sources` had padded with "W1 · R1" (a commander-identity land read as five colours) — the line is now limited to the deck's declared colours.
B1c | builds/sultai/build.json | Migrated from the board's data.json and template (pile labels and intros, group letters); `builder.py check sultai` → clean.
B1d | tests/test_builder.py, tests/test_cli.py, .claude/commands/pile-analysis.md | 14 tests on a scratch builds/ dir and a scratch COPY of deck 96 (G-88): default piles, distinct keys, refusal of unknown names without partial writes, input validation, stale-after-swap, not-stale-after-notes-edit, soft summary text, picks parse and validation, derive fields (incl. declared-colour sources), repo builds well-formed (structure only), CLI exit codes. test_cli reads the subcommand list from the parser and checks each one's help. `/pile-analysis` Stage 6 step 4 keeps a finished pile as a Builder project — the real invocation check_commands requires.
B1e | scripts/check_all.py | `builder_soft()` emits one soft line per project with stale reasons or unresolved names (reasonless/unplaced cards are work in progress, not decay); never gates; exceptions become a "skipped" line.
B1f | .cycle/builder-scope.md | Status line and font decision recorded.

TEST RESULTS: check_all OK (all invariants hold; no new soft lines). pytest: full suite passed (rc=0), including tests/test_builder.py (14 passed) and the test_cli builder subcommand-help test.
REGRESSION RISKS: (1) refresh.py's derived data gains meta.title/decks/piles and a per-card `src`; the board template ignores unknown keys, and the rendered figures were compared before and after. (2) check_all imports builder.py inside a try; a malformed build file yields a "skipped" soft line rather than a failure. (3) The sources string drops colours a deck does not declare — only the board reads it.
INVARIANTS AT RISK: None — no canonical CSV or deck file is written; builds/ is new and written only through atomic_write.
NET SCORE: 1 production fix (the phantom "W1 · R1" on the board's sources line, live on the published board) − 0 new failure modes = 1. The rest is new capability (the stale-reason check is defensive: 0 stale reasons today).

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation: `.github/workflows/pages.yml` — not touched by this batch (no dashboard change).

(Not complete in production until blocking operator actions are done AND
the deploy step is confirmed.)

FOLLOW-ON ITEMS:
- `deck_color_sources` counts a commander-identity land (Command Tower) as five colours — the G-37/BS11-17 residual CLAUDE.md already names; builder works around it for display only.
- Builder batch 2: generic template (N decks, piles from data), `builder.py render --target pages|artifact`, retire `.cycle/board/src/`.
- `/draft-deck` and `/apply-changes` wiring stays in batch 4 (only `/pile-analysis` was touched, for reachability).

DOCUMENTATION UPDATES NEEDED:
- None this batch; the CLAUDE.md entry is scheduled for batch 4 (one Common Gotchas rule: PAGE = TEMPLATE + DATA, reasons graded against a deck version, the theme-fit grade is not a verdict).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
