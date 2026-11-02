---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch B of .cycle/builder-picks-plan.md
- B1: "Undecided for <deck>" filter; pile tabs and the count show decided/total
- B2: bulk mark every shown, undecided card (Bench in / Keep out of a deck) behind an inline confirm
- B3: one undo step per gesture (b/o on a shared pile, bulk marks)
- B4: "Move to pile" request from the card pane, processed by /pile-analysis Stage 6
- B5: `deck.py flex <id> --add "+Card | note" [--apply]` writer; `builder.py picks` emits one per benched card; /apply-changes Stage 0 runs them
Files modified: scripts/deck.py, scripts/builder.py, scripts/builder_template.html, tests/test_deck.py, tests/test_builder.py, tests/test_builder_template.py, .claude/commands/apply-changes.md, .claude/commands/pile-analysis.md, README.md, .cycle/builder-picks-plan.md, .cycle/board/index.html

CHANGES:
B1 | scripts/builder_template.html | `decided(c,k)` = in the deck, or Add/Cut/Bench/Keep out for it; `decidedInPile` = decided for every deck the pile speaks for (its own deck, or all when shared). A toolbar "Decision" select (Undecided for <deck> / for any deck); the pile tab counts and the "N shown · d/t decided" line read it (they counted any mark before, so a Thranduil-only mark finished a shared-pile card).
B2 | scripts/builder_template.html | "Mark every shown, undecided card" select (Bench in / Keep out of the pile's decks) + Mark… → an inline "Keep out of Glarb for 35 cards? Yes / Cancel" (no window.confirm — an artifact iframe may block it). It touches only shown cards not in that deck and undecided for it, so it never overrides an existing Add or Bench.
B3 | scripts/builder_template.html | Undo entries hold `items` (several cards); `gesture(label, fn)` collects every snapshot inside it into one entry; `toggleScoped` (b/o) and the bulk mark run inside one; undo restores every item and says how many. The clearing toast is muted inside a gesture.
B4 | scripts/builder_template.html, .claude/commands/pile-analysis.md | A "Pile" select in the pane (pile cards only) queues `{dest: "move:<pile>"}` in the requests collection (or this browser's), shown as "queued for Claude" and counted on the Add cards tab; DESTS labels the move; the Add-cards form omits move destinations. Stage 6 step 6: `builder.py place`, then re-read the reason and verdicts.
B5 | scripts/deck.py, scripts/builder.py, .claude/commands/apply-changes.md | `_flex_add`: parses the line, resolves the +In name through the shared resolver (canonical spelling), refuses a card the deck runs or another `#~` line names, inserts after the last `#~` line (else at the end) through `_safe_write_lines` (INV-04 re-parse, copy-count guard, .bak); dry run without --apply; a writer never takes a path. `picks_report` prints one `deck.py flex <id> --add "+Card | BENCH (builder <slug>): benched on the board"` per benched card (dry form; /apply-changes adds --apply).

TEST RESULTS: full pytest suite passed (rc=0) — new: TestFlexAdd (dry run, apply with resolved spelling and .bak, three refusals) on a scratch decks/ dir (G-88), the picks bench → flex command, and a Node test of decided/decidedInPile + one undo entry for b on a shared pile. The Batch 2b Bench test's harness gained a `gesture` stub (toggleScoped now calls it). check_all OK, 5 soft. Browser walk: b marks both decks, one u clears both; the Decision filter narrows Either deck to 39; bulk asks "Keep out of Glarb for 35 cards?", marks 35, one u reverts all 35; a move request shows "queued for Claude" and the Add tab counts it; no page errors. The walk found a name clash (a new `GROUP` beside the existing reason-group `GROUP`) — renamed `GESTURE`.
REGRESSION RISKS: (1) Tab progress now means "decided", not "marked": a shared-pile card with one deck's mark no longer counts as done. (2) `flex` gains --add/--apply; the read form is unchanged. (3) Undo entries changed shape ({label, items}); only this page reads them.
INVARIANTS AT RISK: INV-04 — the flex writer edits deck files; it goes through `_safe_write_lines` (parse + copy-count check + .bak), refuses on a mismatch, and a comment line cannot change the count.
NET SCORE: 0 production fixes − 0 new failure modes = 0 (new capability).

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation: `.github/workflows/pages.yml` publishes on the next merge to main; the claude.ai board is republished (artifact v25).

(Not complete in production until blocking operator actions are done AND
the deploy step is confirmed.)

FOLLOW-ON ITEMS:
- Regression scenario 25 could gain the Decision filter, bulk mark and move-request steps (sync-docs).
- Next plan batch: C (multi-deck polish: pile labels by deck count, unique button letters, distinct deck colours, 4+ decks, 1/3-deck render tests).

DOCUMENTATION UPDATES NEEDED:
- README updated; CLAUDE.md G-04 could name `flex --add` as the writer for a flex line (sync-docs).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
