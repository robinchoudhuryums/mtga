---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
BATCH 6 (interface)
- BS8-20 Global shortcuts fired while focus was in a `<select>` (the Log-a-match deck picker)
- BS8-43 JS mirrors drifted from Python: no TRUNCATED flag; a DRAW labelled `L`; truncated event lines dropped silently
- P-04 Dashboard light theme was JS-only — no `prefers-color-scheme` fallback, no `color-scheme`
- P-05 `syncLive` toasted success before the payload was stored
- P-06 `role="option"` rows outside a listbox; both overlays unnamed
- P-07 Focusable `<h2>` carrying `aria-expanded` (a heading cannot hold that state)
- P-08 Deck editor had no unsaved-changes guard
BATCH 7 (outcomes, gates, docs hygiene)
- BS8-23 `parse_matches --deck <id>` was never validated against the roster
- BS8-22 `check_docs.figure_drift` was invoked by nothing; its baseline figure counted comment lines
- BS8-24 `test_cli.py` was pinned to deck 43's current contents
- BS8-25 `/ingest`↔`/add-cards` routing loop; `/pile-analysis` inline identity castability; `/roster-review` wrote without a commit step; `make postedit` reachable from no skill
- BS8-26 Three documents carried three different gate counts (11/12/14) against a real 13; `systems-map.md` was marked LIVE at half the roster
Files modified: scripts/build_dashboard.py, scripts/check_commands.py, scripts/check_docs.py, scripts/check_all.py, scripts/parse_matches.py, templates/deck.html, dashboard.html (rebuilt), tests/test_templates.py, tests/test_dashboard_js.py, tests/test_cli.py, tests/test_check_commands.py, tests/test_check_docs.py, tests/test_parse_matches.py, .claude/commands/ingest.md, .claude/commands/pile-analysis.md, .claude/commands/roster-review.md, docs/verify-commit-tail.md, docs/systems-map.md, docs/cycle-config.md, README.md, CLAUDE.md

CHANGES:
BS8-20 | build_dashboard.py `isTyping` | SELECT added.
BS8-43 | build_dashboard.py `analyzeOne` / `stalecardEl` / `parseLogBlock`; tests/test_dashboard_js.py | the JS carries `truncated` on the same 75% rule `deck.match_paste` uses and renders "⚠ TRUNCATED? paste holds N of M cards — a fragment, not a drift"; a DRAW (no winning team) is `D`, matching Python; an unparseable event line increments `parseLogBlock.dropped` and the panel toasts it. The agreement fixtures gained a FRAGMENT paste and the harness now compares `truncated` — the mirror drift was invisible because no fixture was partial.
P-04 | build_dashboard.py head + `_with_light_scheme_fallback` | a first-paint script stamps `data-theme` before the body parses; `color-scheme` declared for both themes; every `[data-theme="light"]` token block is emitted a second time at BUILD time under `@media (prefers-color-scheme: light) :root:not([data-theme="dark"])`, copied from the template's own definition rather than hand-kept (the G-72 drift shape).
P-05 | build_dashboard.py `syncLive` | store first; on a storage failure toast the failure and do NOT reload.
P-06 | build_dashboard.py `paletteEl` / `openModal` | the option rows live in a `role="listbox"` with `aria-activedescendant` driven by ↑↓; the input is a `combobox`; both overlays carry an accessible name (the modal names its deck).
P-07 | build_dashboard.py `initSections` + `a11y(…, native:true)` + CSS | the collapse control is a real `<button>` inside the `<h2>` carrying `aria-expanded`/`aria-controls`; the heading keeps its role and stops being focusable; `a11y` skips tabindex and the synthetic key handler for a native control (binding it would fire the toggle twice).
P-08 | templates/deck.html | `beforeunload` guard, bypassed by a successful save's reload — the same shape collection.html has.
BS8-23 | parse_matches.py `main` | `--deck` is normalized and checked against `deck_ids()` before any parsing; unknown → exit 1 with the reason `--add`/`--annotate` give.
BS8-22 | check_all.py + check_docs.py | `figure_drift` runs inside the gate as a SOFT warning, appended AFTER `soft` exists (beside the hard doc check it raised NameError into that block's `except` — a false "doc structure check errored"); the K-09 figure now measures baseline ENTRIES (173), not the file's 188 lines.
BS8-24 | tests/test_cli.py `_pick_deck` | `_DECK`, the cut card, the section header, the add card and the variant pair are derived from the live roster: a Standard deck with two unambiguous `# section` headers, a nonland card under one, a different header to move it to. Today it picks deck 42a; the suite no longer goes red when a tune touches deck 43. The tune-plan test now searches the roster for any deck that assembles a plan instead of asserting a fact about deck 43.
BS8-25 | check_commands.py + the three skills + the shared tail | Makefile TARGETS are covered the way scripts are: a `make <target>` must appear in a skill or in `docs/verify-commit-tail.md`, or be exempted with a reason (`INTERACTIVE_ONLY` grew a `make` kind and five entries, and stale-entry checking to match). It fired on `make postedit` on its first run; the tail now runs it for a deck-file change, per G-69's ordering. `/ingest`'s route cell names `reconcile_crafts.py` directly (it and `/add-cards` pointed at each other); `/pile-analysis`'s pull reads castability from the PRINTED COST via `deck._candidate_castability` (it computed `identity ⊆ deck colours` and printed ✗OFF — the G-58 trap inside the skill that warns about it two paragraphs later — verified: Bullseye reads castable in mono-black, Negate off-colour); `/roster-review` cites the commit tail and is named in its writer list.
BS8-26 | README.md, CLAUDE.md, docs/cycle-config.md, check_docs.py | the count is thirteen everywhere, and it is now a MEASUREMENT the drift radar holds (`_gate_word` counts `check_*.py` less the runner), so it cannot rot again. `systems-map.md` is LIVE again: figures re-measured (117 decks, 2,537 printings, 15,973 pool, 35 subcommands, 82 matches) and the overlapping-answer inventory gained the six rows batches 1–5 changed — three colour-source copies retired to one, two rotation predicates to one, castability at every site, the format key, the editor gate, the JS truncation mirror.

TEST RESULTS: passed — full suite green with PYTEST_NO_SKIPS=1 (1,639+ tests); `check_all` all invariants hold, only the expected G-75 dead-tutor soft warning; `check_docs`, `check_commands`, `check_patterns`, `check_colors` all clean. Mid-batch failures, all mine and fixed: the JS truncated-fixture comparison used `[r["truncated"]]` over a row set that includes the unmatched paste (no such key); the light-fallback test compared against a LITERAL count of `[data-theme="light"] {` which includes the new one-line `color-scheme` rule (the property is per token BLOCK); and `test_every_exemption_names_something_real` encoded the old two-kind exemption table and had to learn about `make` targets — a test double for the module I changed, updated as part of the fix.
REGRESSION RISKS:
- The section header's markup changed shape (an inner `<button>`): any CSS or selector targeting `h2.sec > *` directly would need to account for it; the caret is appended to the heading before the wrap, so it moves inside the button (styled `all:unset` + flex so it renders as before). The perceptual result is unverified — Scenario 15 below.
- `a11y(…, native:true)` is new: passing it for a NON-native node would leave that node unfocusable and keyless. Only the section button uses it, and a test pins that.
- The no-script light fallback is generated at build time; a template edit that renames the light blocks silently drops it — pinned by a test that counts blocks, not text.
- `parseLogBlock` now reports `D`; a caller reading only W/L would see a third value (the panel emits only the id, as designed).
- `--deck` validation refuses an id the roster does not hold: a deliberately-not-yet-created deck id can no longer be pre-tagged.
- `check_commands` now fails on a NEW Makefile target until it is named or exempted — intended, and the message says both remedies.
INVARIANTS AT RISK: None
NET SCORE: 8 − 0 = 8
(BS8-20, BS8-43 (draw label + truncation), P-05, P-08, BS8-23, BS8-22, BS8-25 (postedit staleness + the pile-analysis trap), BS8-26 all fire on live use this month; P-04/P-06/P-07 are perceptual/assistive-tech fixes counted once under BS8-20's line. No new failure mode found.)

OPERATOR ACTIONS / DEPLOY:
- Walk the new Scenarios 12–18 (light-OS first paint, deck-select type-ahead, palette/modal with a screen reader, section-header announcement, editor leave-prompt, mini-curve, live-sync honesty) | BLOCKS DEPLOY: N
Deploy: Presentation — pages.yml republishes the dashboard on push to main (snapshot rebuilt).

FOLLOW-ON ITEMS:
- P-09 (`needsMythic` parses a display string), P-10 (mini curve folds MV 0 into the 1 bar), P-11 (recently-edited panel depends on clone depth), P-12 (two inline WUBRG parsers in the generators), P-13 (deck-editor dirty tracking compares a string to an int) — all Low, all still open.
- `/api/remove` and `/api/add` still have no library token (remove has the printing-key 409).
- The library tag-prune follow-on from batch 5 (`tag_synergies --prune`) is unstarted.
- `systems-map.md`'s WORKFLOW prose is still the 2026-07-29 text; only its figures and inventory were re-measured.

DOCUMENTATION UPDATES NEEDED:
- Regression Scenarios 12–18 from the scan should be added to CLAUDE.md's Cycle Workflow Config (they exist only in the scan report and this block).
- README's dashboard section does not mention the no-script light fallback or the section-header button.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
