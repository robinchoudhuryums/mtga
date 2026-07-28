---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: I-01 (residual) — the six `.pip` colour-filter divs in `templates/collection.html` had no `role`, no `tabindex` and no key handler, so the editor's entire colour filter was mouse-only and unannounced. Deferred six times across prior batches.
Files modified: templates/collection.html, tests/test_templates.py (new), CLAUDE.md

CHANGES:
I-01 | templates/collection.html | Each pip gets `role="button"`, `tabindex="0"`, `aria-pressed="false"` and an `aria-label` ("Filter by White", …); the `#pips` container gets `role="group"` + `aria-label`. Mirrors `build_dashboard.py`'s `a11y()` contract verbatim, because the dashboard's colour chips are the same control and a second interaction contract would be a drift bug.
I-01 | templates/collection.html | New `.pip:focus-visible` rule using `outline` + `outline-offset` + `opacity: 1`. Deliberately not the border: `.pip.on` already signals the ACTIVE state with border-color, so sharing it would make focused and selected the same pixel; `opacity: 1` stops a focused pip reading as dimmed at its base `.45`.
I-01 | templates/collection.html | The click handler now syncs `aria-pressed`; a delegated `keydown` handler activates on Enter/Space with `preventDefault` (Space scrolls by default) and routes through `pip.click()` rather than duplicating the toggle logic — two definitions of what a pip does is how a keyboard path and a mouse path drift apart.
I-01 | tests/test_templates.py | New markup-contract layer (16 tests, stdlib `html.parser` only, no new dependency): the six pips exist in order, each is focusable, role-bearing, unpressed at render and has a real accessible name; the group is named; the keydown handler exists and covers both keys, preventDefaults, and routes via `.click()`; `aria-pressed` is synced on toggle; the focus ring exists, uses outline not border, and isn't left dimmed. Plus a guard that no `<input>`/`<select>` in the template loses its label.
I-01 | CLAUDE.md | Regression Scenario 7 extended with the editor's half of the keyboard walk (it only covered `dashboard.html`); the Presentation subsystem records the shared chip contract and the outline-not-border rule; the Testing subsystem describes the new markup-contract layer and why it is not a browser test.

TEST RESULTS: passed — `check_all.py` "All invariants hold. ✓"; pytest 561 passed (was 545, +16). Scenarios walked, all driven in a real headless Chromium rather than asserted by inspection (Playwright installed to the scratchpad only, NOT added to the repo):
  - Scenario 7 (keyboard-only traversal), editor half: PASS — 14 checks. Tab order from the search box is `pip:W → pip:U → pip:B → pip:R → pip:G → pip:C → set → sort → addToggle`, matching visual order; 2px focus ring present in the accent colour; Enter and Space both toggle; Space does not scroll; the grid actually re-filtered (1762 → 422 cards); `aria-pressed` syncs on both the key and mouse paths; a mouse click leaves no ring (`:focus-visible` working); multi-select still works. Verified these checks FIRE: re-run against the stashed pre-fix template, 10 of them failed.
  - Scenario 4 (edit via the app): PASS — grid renders, save button starts idle, arms on an edit, and the edited card marks dirty. No data written; `card-library.csv` and `decks/` confirmed clean after the walk.
  - Scenario 8 (editor failure feedback): PASS — with the server stopped, Save / Remove / Revert each show a toast naming the failure ("… failed (is the server running?): Failed to fetch") and zero unhandled promise rejections.
  - Scenarios 5 and 6 (light-mode status colours, dashboard at phone width): NOT APPLICABLE — both are `dashboard.html`, which this change does not touch.
  - Scenarios 1, 2, 3 (ingest, deck analysis, refresh): NOT APPLICABLE — no Python, data or deck code changed.
One assertion failed on the first browser run ("focused pip is not dimmed", opacity 0.45). Investigated before changing anything: `.pip` carries a 120ms opacity transition and the probe sampled at t=0. Confirmed by timing the transition (0.45 → 0.54 → 0.92 → 1.0 across 200ms). The CSS was correct; the test was wrong, and the test was fixed.

REGRESSION RISKS:
- The pips are now in the tab order, so keyboard users reach `set`/`sort` six Tab presses later than before. That is the intended cost of making a control reachable, and the order matches the visual order.
- `role="button"` on a multi-select filter is a defensible-but-not-unique choice; `role="checkbox"` + `aria-checked` would also be correct. Chose `button` + `aria-pressed` solely to match the dashboard's existing chips — consistency between two copies of the same control beats a marginally better label on one of them.
- `:focus-visible` is unsupported in pre-2021 browsers, where the pips would show no ring. The rest of the page already assumes a modern engine (`aspect-ratio`, `backdrop-filter`), so this adds no new floor.
- No interface changed: the click handler's behaviour, the `activeColors` set, `matches()` and `render()` are all untouched, and the key path routes through the existing click handler rather than around it. Verified the mouse path still toggles and filters identically.

INVARIANTS AT RISK: None. INV-01…06 all cover CSV structure, derived-file schema and deck parsing; this change is presentation markup in a Jinja template with no data path. `card-library.csv` and `decks/` were confirmed unmodified after the app walk.

NET SCORE: 1 production fix − 0 new failure modes = 1
  a) Would this have fired in production this month? YES — the collection editor is a documented workflow (`make app`, Regression Scenario 4) and its colour filter was entirely unusable without a mouse, with no way to discover that from any gate.
  b) New failure mode introduced? NO — the two candidates (a longer tab order, `:focus-visible` support) are intended behaviour and an existing baseline respectively; both are documented above.

OPERATOR ACTIONS / DEPLOY:
- None.
Deploy: N/A for this change — the only Deploy Command in CLAUDE.md is the GitHub Pages dashboard rebuild, which is unaffected (`build_dashboard.py` / `dashboard.html` untouched). The editor is run locally via `make app`.

FOLLOW-ON ITEMS:
- `templates/deck.html` (292 lines) and `templates/decks.html` (67) were not audited for the same class of issue; the finding named `collection.html` only, so they stayed out of scope. Worth a look, and `tests/test_templates.py` is now the place to pin whatever it finds.
- The browser-driven walk above was disposable (scratchpad only). A permanent Playwright layer would automate Regression Scenarios 5-8, which are currently manual by design — but it adds a heavy dependency to a project whose gate is deliberately zero-dependency, so it is a decision to make deliberately rather than a side effect of this fix.
- The recommendation ledger's complementary signal (a card `cuts` keeps ranking weakest that survives round after round) — carried forward from the previous batch, still open.

DOCUMENTATION UPDATES NEEDED:
- Done in this session: CLAUDE.md (Regression Scenario 7 extended to the editor, Presentation subsystem, Testing subsystem). No README change — the editor's colour filter is not described there at the control level.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
