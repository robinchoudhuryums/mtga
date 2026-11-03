---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- Item 4 — cleared vs undone: settled marks move to a per-record `done` history (page's Clear applied marks and `apply`'s cleanup alike); each `apply --apply` writes a log entry the page shows.
- Item 5 — stale reasons: a reason is stale only when a card that entered or left its deck since it was written is its own card or is named in its text.
- Item 6 — note replies on the board: `reply` / `replyTo` on the card's record, shown under the note in the pane and in Your picks; `apply` lists only unanswered (or since-edited) notes.
- Item 7 — cards still to cut: the deck panel and its summary line show "109 / 100 · 9 cuts to go" (exact for Brawl, a minimum otherwise), counted after the owner's picks too.
- Item 8 — Claude's suggestions: `sug: [{v, why}]` on a record is drawn as a dashed button and a "✦ suggested" row tag, listed with Accept / Dismiss in the pane and Your picks; it counts for nothing until accepted.
Files modified: scripts/builder.py, scripts/builder_template.html, tests/test_builder.py, tests/test_builder_template.py, .claude/commands/pile-analysis.md, .claude/commands/apply-changes.md

CHANGES:
4 | scripts/builder.py | `cleanup_ops` appends each settled mark to `done` as {v, at} and never deletes a record; new `apply_log_entry` (what landed per deck, failures); `apply --apply` writes `cleanup.json` as {picks: [...], log: {...}}.
4 | scripts/builder_template.html | records load and save `done`; `clearApplied` moves applied marks to `done`; a record with history is kept; Your picks gains "History — applied and cleared" and "What Claude applied" (the `log` collection, read live).
5 | scripts/builder.py | `record_snapshots` stores each deck's card names per graded hash in build.json (pruned to hashes a reason refers to); `_history_names` finds an older list in the deck file's git history for reasons written before snapshots; `reason_changes` + `mentioned` (full name, split-card front, legend short name ≥4 letters, whole word) decide staleness; `check_build` messages name the card; `stale_summary` text updated. Sultai: 426 → 231 stale entries, every one naming a card the Glarb trim moved; 0 lists missing from history.
6 | scripts/builder.py, scripts/builder_template.html | `picks_from_db` lists a note only when `replyTo` differs from it; `replyHTML` under the note (pane + Your picks), marked when it answers an earlier version; `persist` keeps the reply while the note stands.
7 | scripts/builder.py, scripts/builder_template.html | `deck_live` adds `target` (100 for BIG_DECK_FORMATS, else 60) and `exact` (singleton format); `sizeHTML`/`sizeNote` in the deck panel and summary line, from `project`'s size0/size1.
8 | scripts/builder_template.html | `sugOf`/`sugA`/`openSugs`/`sugHTML`, dashed `data-sug` buttons, row tag, Accept = the ordinary pick button (marking a suggested pick removes the suggestion in `togglePick`), Dismiss = `dismissSug` (undoable); not counted in pending, copy text or projections.
Skills | .claude/commands/pile-analysis.md, apply-changes.md | write cleanup's `done` + `log`; reply via `reply`/`replyTo`; propose cuts as `sug`.
Tests | tests/test_builder.py, tests/test_builder_template.py | cleanup history test replaces the deletion test; log entry, unanswered notes, four stale-reason tests, deck target test; two TestCheck tests rewritten to the new rule (they asserted any change marks a reason stale); the Node quick() harnesses extract sugOf/sugA.

TEST RESULTS: builder test files pass (82); full suite and check_all: see the commit adding this block. Browser walk (Playwright, Pages render, seeded storage): dashed suggested button and two row tags, "109 / 100 · 9 cuts to go" / "100 / 100 on size", Notes with reply, Suggestions and History sections; Accept turned the suggestion into a cut mark, Dismiss removed it; no console errors.
REGRESSION RISKS: `cleanup.json` changed shape (list → {picks, log}); its only reader is Claude via the two skills, both updated. `persist` now writes five more fields; a record Claude writes a reply to while the page holds an older copy could be overwritten by the page's next save of that card (the live snapshot listener narrows this to a race). Verdict staleness (`vs`) is unchanged and still flags all 426 verdicts after the trim.
INVARIANTS AT RISK: None — no deck or CSV writer changed; build.json gains a `snapshots` key, read only by builder.py.
NET SCORE: 5 production fixes − 1 new failure modes = 4
(4 YES: round two found eight bench lines "unbenched" when four had been cleared. 5 YES: 426 stale flags after one round. 6 YES: replies lived only in chat. 7 YES: both decks sat over size all session with no count on the page. 8 YES: round one proposed unasked cuts. New failure mode: the reply race above.)

OPERATOR ACTIONS / DEPLOY:
- Re-render and republish the claude.ai Sultai board so the new page is live. | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds the Builder pages on the next merge to main.

FOLLOW-ON ITEMS:
- Verdict staleness uses the old any-change rule (426 per deck after the trim); the same snapshot diff could narrow it.
- Item 9 (unpaired picks in recommendations.csv) and item 10 (render lists changed image files for republishing) remain.
- The reply race: persist could skip writing reply fields it did not change (a field-level update instead of set).
- Builder tests still read the live deck 96 (twice broken today by owner edits).

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-89 + gotchas.md long form: done history and log, narrowed stale reasons, replies, size line, suggestions (300-word cap).
- README Builder section; docs/systems-map.md §5c; scenario 25 (C-?): Accept/Dismiss a suggestion, reply under a note, size line.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
