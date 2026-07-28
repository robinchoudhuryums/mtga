---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: accessibility audit of `templates/deck.html` and `templates/decks.html` (the sibling templates left out of scope by the collection.html pip fix). Four defects found in deck.html, two in decks.html; all fixed.
Files modified: templates/deck.html, templates/decks.html, tests/test_templates.py, CLAUDE.md

CHANGES:
A-01 (deck.html, the headline) | templates/deck.html | The four analysis tabs (Stats / Mana / Tribes / Suggestions) were bare `<span class="tab">`s with a click handler on the container — not focusable, not announced, entirely mouse-only. This is the SAME defect as the collection editor's colour pips, sitting two files over. Each tab now carries `role="tab"`, `tabindex="0"` and `aria-selected`, with a delegated `keydown` handler activating on Enter/Space (preventDefault, since Space scrolls) routed through `.click()` so the click handler stays the single definition of what a tab does. `showKind` now moves `aria-selected` with the `on` class.
A-01b | templates/deck.html | Added the ARIA structure the roles require: `role="tablist"` + `aria-label` on the strip (a `role="tab"` outside a tablist is invalid ARIA) and `role="tabpanel"` + `aria-label` on the output `<pre>`, which is also now `tabindex="0"` because it has `overflow-x:auto` — a scrollable region a keyboard can't focus can't be scrolled without a mouse.
A-02 | templates/deck.html | The toast is the only report that a save succeeded or failed, and it was purely visual (opacity 0 → 1, nothing announced). Now `role="status"` + `aria-live="polite"` — polite because it reports a result rather than interrupting, and `opacity:0` rather than `display:none` keeps it in the a11y tree so the announcement fires.
A-03 | templates/deck.html, templates/decks.html | Both files styled `:hover` on their controls and nothing else, so keyboard users got a weaker signal than mouse users for the same control. Added `:focus-visible` rings (`outline` + `outline-offset`, never the border — `.tab.on` and `.rm:hover` already claim border-color) for `.tool`, `.rm`, `.tab`, `.out` in deck.html and for `a.tool`, `.deck` in decks.html.
A-04 | templates/deck.html, templates/decks.html | Neither page had a `<main>` landmark, so landmark navigation and "skip to content" had nothing to aim at. The existing `.wrap` container became `<main class="wrap">` in both — no CSS or layout change.
A-01…A-04 | tests/test_templates.py | 10 new markup-contract tests (26 total in the file): tabs are focusable/role-bearing/`aria-selected`-initialised, the strip is a tablist, the output is a focusable tabpanel, `aria-selected` moves with the active tab, Enter and Space both activate via `.click()` with preventDefault, the toast is a polite live region, both files carry focus rings for every hover-styled control, and both have a `<main>`.
A-01…A-04 | CLAUDE.md | Regression Scenario 7 extended with the deck-editor walk; the Presentation subsystem records the tabs fix, the tablist/tabpanel structure, and that auditing the SIBLING templates is what found it.

TEST RESULTS: passed — `check_all.py` "All invariants hold. ✓"; pytest 571 passed (was 561, +10). Verified in a real headless Chromium (Playwright in the scratchpad only, NOT added to the repo): 22 checks, all passing — tabs take focus (impossible before), show a 2px ring, Enter and Space both select, Enter actually ran the analysis (1613 chars of output), only the active tab reports `aria-selected="true"` and the previous one is deselected, Space did not scroll, the mouse path still selects and syncs, the output is focusable, both pages have exactly one `<main>`, the toast is a polite live region, and deck/tool links in decks.html show focus rings. Confirmed these checks FIRE: re-run against the stashed pre-fix templates, 19 of 22 failed.
Scenarios walked:
  - Scenario 4 (edit via the app, deck half): PASS — navigated Decks → a deck by clicking the link, changed a quantity, save armed and marked ready, summary recomputed, and the save landed (verified in the file: the quantity went 1 → 2, with a `.bak` written). Deck file reverted afterwards; `decks/` confirmed clean.
  - Scenario 7 (keyboard-only traversal), deck-editor half: PASS — see above.
  - Scenario 8 (editor failure feedback): NOT RE-RUN — walked and passed in the previous batch, and nothing in the fetch/error paths changed here.
  - Scenarios 5 and 6 (dashboard light mode, dashboard at phone width): NOT APPLICABLE — `dashboard.html` untouched.
  - Scenarios 1, 2, 3 (ingest, deck analysis, refresh): NOT APPLICABLE — no Python, data or deck-file code changed.
One assertion failed on the first Scenario-4 run ("save succeeded", toast empty). Investigated before changing anything: the save had in fact succeeded, and `location.reload()` fires immediately after `toast(...)`, destroying the message. Pre-existing, not caused by this change, and confirmed by re-running against the stashed original template. Recorded as a follow-on, not fixed — see below.

REGRESSION RISKS:
- The four tabs and the output `<pre>` now sit in the tab order, so reaching anything after the Analysis section takes five more Tab presses. That is the intended cost of making them reachable.
- `role="tab"` with all tabs at `tabindex="0"` matches the dashboard's existing tabs rather than the roving-tabindex + arrow-key pattern ARIA recommends. Chose consistency with the sibling surface over strict conformance; arrow keys would be purely additive and are listed as a follow-on.
- `<main>` replaced a `<div class="wrap">` in both files. The class and all CSS are unchanged, and `main` is `display:block` like `div`, so there is no layout effect — confirmed by rendering both pages.
- `aria-live="polite"` on the toast means every toast is now announced. That is the point, but it does mean a rapid sequence of toasts would queue announcements. The toast has a single 4s timer and is replaced rather than stacked, so this is bounded.
- No interface changed: `showKind`, the click handler, `cardStatus`, `refresh`, the save fetch and the flex renderer are all behaviourally untouched; the key path routes through the existing click handler rather than around it.

INVARIANTS AT RISK: None. INV-01…06 cover CSV structure, derived-file schema and deck-file parsing; these are presentation-layer changes to Jinja templates with no data path. Notably the deck SAVE path was exercised end-to-end and `check_all` (INV-04 included) passed afterwards, before the test edit was reverted.

NET SCORE: 1 production fix − 0 new failure modes = 1
  a) Would this have fired in production this month? YES — the deck editor is a documented workflow (Regression Scenario 4) and its entire analysis panel was unusable without a mouse, with no gate able to see that.
  b) New failure mode introduced? NO — the three candidates (longer tab order, the simplified tabs pattern, live-region announcements) are intended behaviour, a documented consistency trade-off, and bounded respectively.

OPERATOR ACTIONS / DEPLOY:
- None.
Deploy: N/A for this change — the only Deploy Command in CLAUDE.md is the GitHub Pages dashboard rebuild, unaffected (`build_dashboard.py` / `dashboard.html` untouched). The editor runs locally via `make app`.

FOLLOW-ON ITEMS:
- **The deck editor's success toast is never readable.** `location.reload()` fires immediately after `toast('Saved N card lines …')`, so the confirmation is destroyed before anyone can read it — and it now also truncates the live-region announcement this batch added. Failure toasts are unaffected (they don't reload). Pre-existing; the fix is a behaviour change to the save flow (delay or drop the reload), not a markup change, so it was left out of an accessibility audit.
- **Saving a deck through the editor REORDERS its `#:` metadata.** The Scenario-4 walk moved `#: based-on: deck.txt` from the header block to after `#: notes:` and inserted a blank line, on a save that only changed a quantity. Verified pre-existing (reproduced with the original template). INV-04 passes because every card line survives, so no gate catches it — but deck files are read far more than they are parsed, and a save silently rewriting the header is a data-fidelity issue worth its own look.
- The dashboard's own tabs (`build_dashboard.py`, two sites) use `role="tab"` without an enclosing `role="tablist"` and without a tabpanel — the invalid-ARIA half of what was fixed here. Out of scope (different file, not named in the finding).
- Arrow-key navigation for the tabs (with roving tabindex) would complete the ARIA tabs pattern on both surfaces; deliberately skipped to avoid diverging from the dashboard.
- A permanent Playwright layer would automate Regression Scenarios 5-8. Still a deliberate decision rather than a side effect: `check_all` is zero-dependency by design.
- The recommendation ledger's complementary signal (a card `cuts` keeps ranking weakest that survives round after round) — carried forward, still open.

DOCUMENTATION UPDATES NEEDED:
- Done in this session: CLAUDE.md (Regression Scenario 7 extended with the deck-editor walk; Presentation subsystem records the tabs fix and the sibling-audit lesson). No README change — the editor's internal controls are not described there at that level.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
