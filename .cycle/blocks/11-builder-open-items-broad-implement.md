---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- Verdict staleness — a verdict star is stale only when a card that entered or left its deck since it was given is the card itself or is named in its reason (the item-5 rule, applied to verdicts).
- Item 9 — `builder.py apply` records each unpaired add or cut in recommendations.csv.
- Item 10 — `builder.py publish-plan <out> [--mark]` lists the board's page and image files changed since the last publish.
- Reply race — the board page saves only the fields the owner changed, as an `update`, and never `reply` / `replyTo`; the skills write board records with `update` of Claude's fields only.
- Docs — CLAUDE.md G-89 (296 words) + gotchas.md long form, README Builder section, systems map §5c (steps 7–8, two reconciliation points), scenario 25.
Files modified: scripts/builder.py, scripts/deck.py, scripts/builder_template.html, tests/test_builder.py, tests/test_builder_template.py, .claude/commands/pile-analysis.md, .claude/commands/apply-changes.md, CLAUDE.md, docs/gotchas.md, README.md, docs/systems-map.md, .cycle/board/index.html, .cycle/board/.published.json

CHANGES:
Verdicts | scripts/builder.py | `verdict_stale` (shared with `verdict_status` and derive's `vs`) diffs the graded list against the live one via `_list_changes`; `set_verdict` stores a snapshot and `record_snapshots` keeps verdict hashes. Sultai: 426 → Thranduil 51 / Glarb 180.
9 | scripts/deck.py | `recommendation_row` accepts a blank cut or add (that side's columns stay blank, so a blank add never reads as unsurfaced in `feedback`) and a `cache` dict so several rows against one pre-change deck compute each model once.
9 | scripts/builder.py | `_ledger_rows` scores the plan's unpaired adds/cuts BEFORE the write; `_append_ledger` appends them after it (`Source` = `builder`); any failure records nothing and never blocks the edit.
10 | scripts/builder.py | `site_files` (page, sprites, large images; old-layout leftovers ignored), `publish_plan`, `publish-plan` CLI; `.cycle/board/.published.json` committed.
Race | scripts/builder_template.html | `SERVER` holds each record as last read (filled by the snapshot listener); `changedFields` diffs the page's copy against it; `persist` sends only changed fields as `update`, falls back to a full `set` (without reply fields) only when the record does not exist, and skips a write with nothing changed.
Race | .claude/commands/pile-analysis.md, apply-changes.md | Claude writes `picks` records with `update` of `reply`/`replyTo`, `sug`, or the cleanup fields only; `set` only a new record.
Tests | tests/test_builder.py | verdict test rewritten to the new rule (a basic-count change leaves the verdict fresh; cutting a card its reason names makes it stale); TestPublishPlan; the apply test asserts the two ledger rows; `scratch` repoints `RECS_CSV`.
Tests | tests/test_builder_template.py | TestPersistKeepsReplies runs `persist` under Node against a fake store: the save sends only `picks` + `at`, the reply survives, an unchanged second save writes nothing, a new record is created whole without reply fields.

TEST RESULTS: Full suite PASSED (exit 0); check_all OK. The Node persist test exercises the reply-safe save; the live board was not clicked through (no browser session on claude.ai).
REGRESSION RISKS: The page's save is now `update`-first; a db that rejected `update` for another reason than a missing record surfaces as the usual "could not be saved" banner. Two writers changing the SAME field at once is still last-writer-wins (e.g. owner dismisses a suggestion while Claude rewrites `sug`). `swap --undo` refuses when a deck's last ledger row is a `builder` row (it names the source), which is correct: undo reverses swaps only.
INVARIANTS AT RISK: None — recommendations.csv is written through `append_recommendation` (atomic, backed up, own header); deck writes unchanged.
NET SCORE: 4 production fixes − 0 new failure modes = 4
(Verdicts YES: 426 stale verdicts per deck after the trim. Item 9 NO: no decision was lost this month, only unrecorded. Item 10 YES: 24 cards had no image on the board. Race YES-plausible: the window was live every time Claude replied while the board was open. Docs YES: four surfaces described the pre-apply workflow.)

OPERATOR ACTIONS / DEPLOY:
- None. The claude.ai board was republished (v45, index.html only; the images went out in v44 and `.published.json` is marked). | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds the Builder pages on the next merge to main.

FOLLOW-ON ITEMS:
- The owner's "unprotect Teferi's Tutelage" mark on the board awaits their call.
- Builder tests still read the live deck 96 (broken twice by owner edits).
- check_docs figure drift (tier-floor spread B 41→42, top band 67→66%) — pre-existing, soft.

DOCUMENTATION UPDATES NEEDED:
- None (done in this run).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
