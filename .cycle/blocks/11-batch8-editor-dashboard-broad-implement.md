---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS11-42 — editor `/api/add` stored the Set Code exactly as typed (Arena `DAR`, a typo) and the next check_all failed INV-01b
- BS11-43 — editor Revert restored the newest `.bak` whoever wrote it, with no staleness token (undid a CLI import from a stale tab)
- BS11-44 — Revert restored the library but not the mana row Remove had pruned (INV-02)
- BS11-45 — dashboard toast was not a live region (every result visual-only for 1.7s)
- BS11-46 — `fallbackCopy` ignored `execCommand`'s `false` and toasted "copied" over an empty clipboard
- BS11-47 — `a11y()` keydown fired for bubbled keys (Enter on the nested ↗ link toggled the leverage card)
- BS11-48 — variant-row `<button>` passed to `a11y()` without `native:true` (redundant role + synthetic click)
- BS11-49 — build degradation scan missed the roster craft plan, wishlist and rotation; a failed rotation said "rebuild the pool", a failed wishlist hid its section
- BS11-50 — pages.yml did not surface the build's sub-majority WARN lines or the page's `[analysis error` markers
- BS11-51 — mini curve and roster curve folded MV 0 into the "1" bar (P-10)
- BS11-52 — `COLBG`/`COLFG` hex constants bypassed the light-theme colour tokens on the pie, roster colour bars and filter chips
- BS11-53 — deck-editor Save lacked `aria-disabled`; "show all" was a focusable `<td>` with no role/state; `/api/save` kept a token-less bare-list branch; save/analysis handlers called `res.json()` raw
Files modified: scripts/app.py, templates/collection.html, templates/deck.html, scripts/build_dashboard.py, dashboard.html (rebuilt), .github/workflows/pages.yml, tests/test_app_editor.py, tests/test_templates.py

CHANGES:
BS11-42 | scripts/app.py | `add()` maps the set through `enrich.SET_ALIASES`, stores it UPPERCASE (the library's convention) and refuses (400, nothing written) a set no card-pool.csv printing carries — new `_pool_set_codes()`, INV-01b's own reference set; an absent pool disables the check.
BS11-43 | scripts/app.py, templates/collection.html | `revert()` requires the page's `lib_token` (absent → 409, stale → 409 "CHANGED since this page loaded it"), the `/api/save` contract. The page sends `#data`'s token; the confirm now says it restores the newest backup "whichever tool wrote it".
BS11-44 | scripts/app.py | new `_restore_mana_rows(rows)` appends a blank card-mana.csv row for every restored library name without one; `revert()` reports `mana_restored` (a failure there returns ok + `warning`, which the page flashes).
BS11-45 | scripts/build_dashboard.py, tests/test_templates.py | toast is `<div class="toast" id="toast" role="status" aria-live="polite">`; pinned at the generator source (the template pin reads templates/ only).
BS11-46 | scripts/build_dashboard.py | `fallbackCopy` calls `done()` only on a true `execCommand` return; otherwise "Copy failed — this browser blocked clipboard access here".
BS11-47 | scripts/build_dashboard.py | `a11y()` keydown returns unless `e.target === node`.
BS11-48 | scripts/build_dashboard.py | variant row: `type="button"`, `a11y(..., {role:null, native:true})`.
BS11-49 | scripts/build_dashboard.py | payload carries `wishlist_error`; the page renders a rotation `R.error` and a wishlist error as an explicit "failed to build — run <cmd>" note instead of the pool hint / a hidden section; `main()` WARNs for a `[analysis error` roster plan, a wishlist error and a rotation error (warn-and-publish, like the sub-majority case). Verified with a forced `rotation_sweep` failure: WARN printed, rc 0.
BS11-50 | .github/workflows/pages.yml | the build step tees stderr, turns every `WARN` line into a `::warning title=Dashboard build::` annotation and preserves the exit status; the verify step annotates the count of `[analysis error` markers in the page.
BS11-51 | scripts/build_dashboard.py | shared `curveBuckets()`: MV 0 gets its own "0" bucket, shown only when non-empty; mini and roster curves both use it. Node-run test.
BS11-52 | scripts/build_dashboard.py | `COLBG`/`COLFG` are `var(--W…--Cc)` / `var(--Wf…--Ccf)`; the colourless pie fallback too. All tokens already defined (the token gate passes).
BS11-53 | templates/deck.html, scripts/build_dashboard.py, scripts/app.py, templates/collection.html, tests/test_app_editor.py | Save sets `aria-disabled` when there is nothing to save; "show all" is a `<button aria-expanded>` inside the cell (focus restored after redraw); `/api/save` refuses a bare-list body with 409 (the old `test_a_bare_list_body_still_saves` pin reversed); a `jsonOf()` guard (deck.html) and an inline guard (collection.html save) report "non-JSON response (HTTP n)".

TEST RESULTS: passed — full suite green; `check_all --quiet` integrity OK, 4 soft (unchanged); `make postedit` all invariants hold, no new zero-role cards. New tests: revert restores the pruned mana row, stale-token and no-token revert refused, add stores DOM for `dar`, add refuses an unknown set; dashboard toast live region, a11y e.target guard, native variant row, show-all button state, execCommand return, token colours, curve buckets (source + Node run), roster-panel error rendering, pages.yml annotations.
REGRESSION RISKS: (1) `/api/revert` and `/api/save` now refuse a token-less request — a curl/script client that relied on the bare endpoints gets 409 (deliberate; matches the deck-save contract). (2) The add-time set check reads the pool on every add (16k rows, ~tens of ms) and refuses any set the pool lacks — a brand-new set before `make refresh` is refused until the pool carries it (leave the set blank or refresh). (3) Mini curves gain a seventh bar only for decks with an MV-0 nonland; 0 decks today. (4) `var(--…)` inside `conic-gradient` / `box-shadow` inline styles needs the 2023-browser floor the page already assumes.
INVARIANTS AT RISK: None — INV-01b and INV-02 are each newly PROTECTED on the editor paths (add, revert).
NET SCORE: 2 − 0 = 2  (production this month: BS11-45 — every dashboard toast was unannounced to assistive tech; BS11-52 — light mode painted the dark pastels on every render of the pie, roster bars and "on" chips. Latent: BS11-42/43/44 (no editor add/revert across a CLI write recorded), 46 (Pages is https; the fallback runs on file:// only), 47/48, 49/50 (no roster-panel failure or WARN this month), 51 (0 decks have an MV-0 nonland), 53.)

OPERATOR ACTIONS / DEPLOY:
- Walk the new scenarios on a real browser: light-mode JS colours (pie, roster colour bars, an "on" colour chip) and keyboard on a leverage card's ↗ link | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds and publishes the dashboard on the next push to `main` (the committed dashboard.html is rebuilt).

FOLLOW-ON ITEMS:
- The dashboard toast still clears after 1.7s; a live region announces it, but a sighted keyboard user reading slowly may miss it (the editor pages use 4s).
- `_lib_token()` hashes the whole library per call; revert/save now call it twice per request (once to compare, once to return). Cheap at 2.8k rows.
- The scan's two operator scenarios (20: JS colours in light mode; 21: leverage card + nested link by keyboard) are not yet in CLAUDE.md's Regression Scenarios.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-15 (editor): Revert now carries `lib_token` like Save and re-adds pruned mana rows; Add aliases + validates the set against the pool (INV-01b); the bare-list save is refused.
- CLAUDE.md Regression Scenarios: scenario 4 (Revert across a CLI write → 409), scenario 17 (P-10 now fixed — the 0 bucket), and add scenarios 20/21 from the scan.
- CLAUDE.md G-72 / scenario 5: JS-painted colours now use the tokens.
- docs/cycle-config.md C-10 / README (Pages): the workflow annotates build WARNs and degraded panels.
- README editor section: Add refuses an unknown set; Revert refuses a page that is out of date.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
