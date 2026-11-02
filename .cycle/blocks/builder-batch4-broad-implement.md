---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Builder batch 4 (.cycle/builder-scope.md) — workflow wiring
- B4-1: /pile-analysis keeps every pile as a Builder project from Stage 0 (new + add), records each batch's placements and reasons in it (Stage 3), separates what the doc holds from what the project holds (Stage 5), and closes with publishing, reading picks and processing Add-cards requests (Stage 6 steps 4–6)
- B4-2: /draft-deck Stage 6 adds the new deck to the pile's project (`builder.py add-deck`) or keeps the bench as a new project
- B4-3: /apply-changes Stage 0 accepts a pasted Builder picks block (or the board's picks collection) through `builder.py picks`, routes protect lines to a header edit, ownership to /ingest and hidden roles to `builder.py hidden`, and re-renders the board after the commit
- B4-4: `builder.py add-deck <slug> ID [--key K] [--label L]` — the tool B4-2 needed, so no skill hand-edits build.json
- B4-5: CLAUDE.md Common Gotchas G-89 (PAGE = TEMPLATE + DATA; the reason is the only thing stored; reasons graded against a deck version; theme fit not a verdict; picks are requests; hidden roles stay out of the floor; the 511-file ceiling) with its long form in docs/gotchas.md; Presentation subsystem lists the Builder files
Files modified: scripts/builder.py, tests/test_builder.py, .claude/commands/pile-analysis.md, .claude/commands/draft-deck.md, .claude/commands/apply-changes.md, CLAUDE.md, docs/gotchas.md

CHANGES:
B4-1 | .claude/commands/pile-analysis.md | Stage 0 starts the project beside the working doc; Stage 3 adds per-batch `place` + `reason` in the same commit; Stage 5 says the doc and the project each have one job; Stage 6 replaces "keep the pile as a project" with: check → render + publish (artifact limits spelled out) or Pages on merge → read picks (ArtifactData `picks` fields, or Copy as text) → `builder.py picks` → /apply-changes; request processing (add with --pile / grade-and-place for auto / propose a swap for add<KEY>; reason; re-render; republish; mark done with a reply).
B4-2 | .claude/commands/draft-deck.md | Stage 6 opening paragraph.
B4-3 | .claude/commands/apply-changes.md | New Stage 0.
B4-4 | scripts/builder.py, tests/test_builder.py | add_deck inserts the deck's pile before the shared piles (B/N); refuses a deck already in the build and a key already used by a deck or pile; does not re-stamp existing reasons' graded_at (a reason must not claim a list it predates). Test covers order, refusal, and the unchanged stamps.
B4-5 | CLAUDE.md, docs/gotchas.md | Rule within check_docs' 300-word cap; long form records the stale-figure board, the field-identical migration and its one diff, the 640-entry refusal, and the tests that hold it.

TEST RESULTS: Full pytest suite passed; check_all OK (13 soft); check_docs OK (two pre-existing soft figure drifts in G-35, 97→99 and 130→132, not from this batch); check_commands OK.
REGRESSION RISKS: (1) /pile-analysis now asks for per-batch Builder writes — more steps per batch, by design (the reasons were being written anyway). (2) The Sultai board stays at .cycle/board (its doc says so); new projects use .cycle/board-<slug>.
INVARIANTS AT RISK: None — skills and docs only, plus a builder subcommand that writes builds/ through atomic_write.
NET SCORE: 0 production fixes − 0 new failure modes = 0. Workflow wiring.

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation: `.github/workflows/pages.yml` — unchanged this batch.

(Not complete in production until blocking operator actions are done AND
the deploy step is confirmed.)

FOLLOW-ON ITEMS:
- figure drift (soft, pre-existing): G-35 cites 97 decks with an uncounted nonland source (live 99) and a 130-deck walk (live 132) — /sync-docs.
- Remaining approved Builder item: view-only alternate Arena printings (excluding the borderless semi-transparent-textbox variant).
- .cycle/builder-scope.md stays until that item ships, then is deleted (its own header says so).

DOCUMENTATION UPDATES NEEDED:
- None beyond this batch's; /sync-docs for the two G-35 figures.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
