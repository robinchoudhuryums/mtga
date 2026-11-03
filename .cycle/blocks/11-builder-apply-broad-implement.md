---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- Builder item 1 — `builder.py apply <slug>`: the board's picks become deck-file edits in one checked run (dry run by default, `--apply` writes).
- Builder item 2 — bench reconcile: board bench marks vs the deck's builder-tagged `#~` lines (add missing, retire lines for cards now in the deck, list the rest; `--retire-bench` removes them).
- Builder item 3 — picks read from the board's database dump (`--db`, the folder ArtifactData `list` + `out_dir` writes), plus a cleanup file that clears settled marks from the board; the Pages banner says its picks are separate.
Files modified: scripts/builder.py, scripts/builder_template.html, tests/test_builder.py, .claude/commands/pile-analysis.md, .claude/commands/apply-changes.md

CHANGES:
Item 1 | scripts/builder.py | `plan_apply` checks every pick against the live deck file: pairs (cut must be in, add must be out, add inside the commander's identity), unpaired adds and cuts, protect/unprotect, bench, keep out; a pick the deck already shows is skipped as applied, so a rerun changes nothing; a cut card leaves the `#: protect:` line (G-68). `execute_apply` runs swaps through `deck.py swap --apply` (section placement, flex retirement, identity refusal, ledger row, .bak), then one `_safe_write_lines` INV-04 write for unpaired cuts/adds (resolver printings, G-65), protect edits and bench retirements, then `deck.py`'s `_flex_add` for new bench lines; a failed swap stops that deck and settles nothing. `_post_checks` prints legal size/issues, `resolve --check` and the rationale audit. New `apply` subparser (`file` or `--db`, `--apply`, `--retire-bench`, `--cleanup`).
Item 2 | scripts/builder.py | `_builder_bench_lines` reads only `BENCH (builder <slug>)` lines; a hand-written bench line is never touched. Missing bench lines are planned; a builder line for a card the deck now runs is always retired (G-04 +In rot); one the board merely no longer marks is listed as `bench_stale` unless `--retire-bench` — bench marks set on the Pages copy never reach the board's database.
Item 3 | scripts/builder.py, scripts/builder_template.html | `read_db_dump` (dump folder, its `picks/` folder, a list file, or wrapped {id,version,data} records) and `picks_from_db` (same shape as `parse_picks`; legacy deck-less bench/out). Every planned or already-applied pick goes into `consume`; `cleanup_ops` turns it into per-record writes (picks/pair after, delete when empty; bench and keep-out never consumed), written to `<dump>/cleanup.json` for Claude to write back with ArtifactData. Pages banner: "Picks are saved in this browser only, apart from the claude.ai board's … after Claude applies them, press Clear applied marks."
Skills | .claude/commands/pile-analysis.md, apply-changes.md | Stage 6 step 5 / Stage 0: `apply --db` is the standard path (dump → dry run → owner confirms → `--apply` → write cleanup.json to the board); read the add list against the conversation; `--retire-bench` only for a one-surface round; `builder.py picks` kept as the read-only form.

TEST RESULTS: Full suite PASSED (exit 0, ~2371 tests incl. 9 new TestApply); check_all OK (10 soft, unchanged).
REGRESSION RISKS: None to existing callers — every change is a new function or subcommand; `parse_picks`/`picks_report` are untouched. The Pages banner is copy text only. `apply --apply` writes deck files, but only through deck.py's own writers (swap, `_safe_write_lines`, `_flex_add`), each with a .bak and an INV-04 re-parse.
INVARIANTS AT RISK: INV-04 (deck files parse; printings known) — guarded by `_safe_write_lines`' copy-count check and resolver printings, and `_post_checks` runs `resolve --check`. None otherwise.
NET SCORE: 3 production fixes − 0 new failure modes = 3
(Item 1 YES: two hand-applied rounds this month each needed ad-hoc scripts, and one shipped a duplicate Jin-Gitaxias line. Item 2 YES: round two found all 8 round-one bench lines stale by hand. Item 3 YES: today's picks came from the Pages copy and diverged from the database. New failure mode: a stale add mark would still be re-applied if the owner confirms a plan without reading it — mitigated by the dry run and the skill's instruction, not eliminated.)

OPERATOR ACTIONS / DEPLOY:
- One-time board cleanup on the Sultai board: the live `picks` collection still carries add marks for ~25 cards cut in chat since (Chalk Outline, Visions of Beyond, Wizard's Retort…), from rounds applied by hand before cleanup existed. The owner confirms they are stale; Claude clears them with ArtifactData. | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds the Builder pages (with the new banner) on the next merge to main.

FOLLOW-ON ITEMS:
- Unpaired adds/cuts still reach no `recommendations.csv` row (original item 9); `apply` could record them.
- Original items 4–8 and 10 (cleared-vs-undone history, narrower stale-reason flag, note replies on the board, cuts-to-go in the deck panel, suggestion marks, republish file list) remain open.
- Builder tests use the live deck 96 and broke twice today on the owner's edits (Counterspell, Island count); a frozen fixture deck would end that.
- `builder.py check sultai` reports 426 stale reasons since the Glarb trim.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-89 (and its gotchas.md long form): `builder.py apply` + cleanup + `--retire-bench`; `picks` is now the read-only form. Mind the 300-word cap.
- README Builder section and docs/systems-map.md §5c (row 3: `apply`), scenario 25 / C-?? Copy-as-text step.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
