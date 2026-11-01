---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Builder batch 2b (.cycle/builder-scope.md) — compare and review aids
- B2b-1: Compare view — a pile (or all piles) beside one deck's current list; same rows, thumbnails, roles, cut rank (#n / P), shared card pane; ⇄ on a deck row pairs it with the selected pile card; the selected card and its chosen cut are highlighted; phone shows Pile | Deck tabs
- B2b-2: Hidden-role markers — suspected (dotted "Int?/CA?", from deck.role_coverage_flags) and confirmed ("· hidden", from build.json `hidden` or a page mark); projection and deck strip show "incl. hidden" figures; the floor letter never uses them
- B2b-3: Ownership — owned/craft tag on every row; "I own exactly" in the pane queues a correction; Copy as text emits an /ingest block (reconcile_crafts --set-exact lines with the printing)
- B2b-4: Applied state — a pick the deck files already show is marked "Applied ✓", folds away under "Hide applied" (default on), is left out of Copy as text and the projection, and can be cleared in one click
- B2b-5: Conflict warnings — one cut chosen for several adds, a cut that is protected, a cut no longer in the deck; shown in the pane, deck strip, Compare summary, Your picks and Copy as text
- B2b-6: Undo — header button and `u`; every pick, pairing, ownership and hidden-role change is undoable (50 deep)
- B2b-7: Next band — "To reach a B floor: +1 interaction, +1 more interaction or card advantage" under each projection
- B2b-8: Mana curve now vs after (8 buckets, 0–7+) in the Compare view, with legend, per-bar titles and a text caption listing every count and change
Files modified: scripts/builder.py, scripts/builder_template.html, scripts/check_dfc.py, tests/test_builder.py, tests/test_builder_template.py, .cycle/board/index.html

CHANGES:
B2b-1 | scripts/builder_template.html, scripts/builder.py | Rows are found by data attributes (`.rw[data-w][data-col]`) instead of ids, because a card can sit in both columns; rerow/select/note/peek/refocus all follow. derive() now emits a record (pile None) for every deck-list card not on a pile, so the deck column, pane and zoom work for any build. `pairWith` adds the add pick and the pairing in one undoable step. Repainting a column keeps its scroll position.
B2b-2 | scripts/builder.py, template | `builder.py hidden <slug> <card> --role interaction|card-advantage [--remove]` (build.json `hidden`); derive fields `hr` (suspected) and `hc` (confirmed). A hidden role adds 1 only when the classifier counted 0 on that axis. Report-only, like every axis kept out of tier_band.
B2b-3 | scripts/builder.py, template | derive field `pr` (printing: library row if owned, else pool). `builder.py picks` turns the Ownership block into reconcile_crafts lines and the Counts-as blocks into `builder.py hidden` commands.
B2b-4 | template | isApplied: add → card now in the deck; cut → card now out; protect/unprotect → header now matches. project() also ignores a pairing whose cut has left the deck.
B2b-5 | template | conflicts() per deck. Picking a card for BOTH decks is deliberately NOT a conflict — decks share copies (CLAUDE.md, "Decks share the collection").
B2b-6 | template | snapshot() before each change; undo restores and persists (a restored empty pick deletes the doc).
B2b-7, B2b-8 | template | nextBand() reads the same scaled `req` table the floor uses.
G-63 | scripts/builder.py, scripts/check_dfc.py | check_all's DFC gate rejected the new printings index (front aliased in-pass with setdefault — the documented trap). Now aliased in a second pass with lib.alias_front and registered in check_dfc._ALIASED_LOADERS.

TEST RESULTS: check_all OK. Builder/template/CLI/templates tests: all passed. Full suite: see commit (re-run after the G-63 fix). New tests: hidden-role record/validate/remove; derive adds deck-only cards with the 2b fields; Ownership and Counts-as blocks round-trip through `picks`; a Node test runs the page's isApplied/conflicts/nextBand on a synthetic deck; the existing projection-vs-model Node test now loads the hidden-role helpers. Headless-Chromium walk: undo, ownership tag, hidden tag, Compare pairing, conflict, curve, copy text, applied section, phone tabs at 390 px with no sideways scroll, no script errors.
REGRESSION RISKS: (1) Picks docs gain `own` and `hid`; older docs without them load as before. (2) A row click on the already-selected card in the OTHER Compare column selects it there instead of opening the note — intended. (3) Size projection can exceed the deck size when two adds share one cut; the conflict box says so.
INVARIANTS AT RISK: None — no canonical CSV or deck file is written; ownership corrections only become an /ingest batch the owner runs.
NET SCORE: 0 production fixes − 0 new failure modes = 0. New capability; the one defect (in-pass aliasing) was caught by the G-63 gate before commit.

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation: `.github/workflows/pages.yml` — not touched (the Pages target is wired in batch 3).

(Not complete in production until blocking operator actions are done AND
the deploy step is confirmed.)

FOLLOW-ON ITEMS:
- "Your picks" links use the browser's default link colour (pre-existing since the first board).
- Batch 3 (Pages integration) and batch 4 (skills wiring, CLAUDE.md entry) remain; then view-only alternate printings.

DOCUMENTATION UPDATES NEEDED:
- None this batch; the CLAUDE.md entry stays scheduled for batch 4.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
