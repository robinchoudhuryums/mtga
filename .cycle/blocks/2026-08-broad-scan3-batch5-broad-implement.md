---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (Batch 5 — interface polish, STRUCTURAL half only):
- BS4-43 | Set-dropdown `innerHTML` interpolation unescaped in BOTH grid pages
- S-1 | Deck-editor tab strip lacked the arrow keys its own comment claimed to share
- S-2 | Five dashboard inputs had placeholder-only accessible names
- S-3 | gallery.html had no light palette and no breakpoints
- S-4 | gallery.html's set/sort selects were unlabelled
- S-5 | Dashboard ignored the OS colour scheme on a first visit
- S-6 | Collection save button's disabled state was CSS-only

Files modified:
- scripts/build_gallery.py, scripts/build_dashboard.py
- templates/collection.html, templates/deck.html
- tests/test_templates.py
- gallery.html, dashboard.html (regenerated artifacts)

CHANGES:

BS4-43 | scripts/build_gallery.py, templates/collection.html | `esc()` on both the
attribute and the text of the set `<option>`. `Set Code` is a free-text CSV column that
`/api/add` stores unvalidated, and this was the one interpolation the BS2-17 escaping pass
missed in each file — a code containing `"` breaks out of `value="…"`. Both `esc` are
hoisted function declarations, so calling them above their definition is safe (checked,
not assumed).

S-1 | templates/deck.html | The analysis tab strip handles ArrowLeft/ArrowRight, routed
through `.click()` like its Enter/Space path so one handler stays the definition of what a
tab does. Its own comment claimed the strip "shares one interaction contract" with
`build_dashboard.py`'s `tablist()`, which has installed arrows since S-2 — so the ← / →
Regression Scenario 7 asks for worked on one strip and silently did nothing on the other.

S-2 | scripts/build_dashboard.py | `aria-label` on `#cardfind`, `#staletext`,
`#deckfilter`, `#wlfilter` and the command-palette input. A placeholder is a last-resort
accessible name — many AT configurations demote it, and it disappears once the user types.
The templates/ pages have carried labels since the pass that pinned them; the dashboard's
own five were missed.

S-3 | scripts/build_gallery.py | A `prefers-color-scheme: light` block using the SAME
tokens and values as templates/collection.html (so the two cannot drift), plus a
`--header` token replacing the hardcoded `rgba(15,17,21,.95)` that would have stayed dark
under a light palette; and a 620px breakpoint matching the sibling's. The gallery was the
one page of this tool that stayed dark-only with no toggle. `.pip`'s `color:#1a1a1a` is
deliberately left: the pip backgrounds are light-tinted in both themes, so dark text on
them is correct either way.

S-4 | scripts/build_gallery.py | `aria-label` on the set and sort selects. A `<select>`
takes no accessible name from its options, so the set filter announced unnamed;
collection.html's identical pair has carried labels since its own a11y pass.

S-5 | scripts/build_dashboard.py | `restorePrefs` falls back to
`matchMedia('(prefers-color-scheme: light)')` instead of hardcoding `'dark'`. A stored
choice still wins, so this changes only the FIRST visit — where a light-OS user previously
got dark with no indication a toggle existed, and the two surfaces of one tool disagreed
about the default.

S-6 | templates/collection.html | `aria-disabled` on the save button, set in the markup and
kept in sync wherever the `ready` class is toggled. `aria-disabled` rather than the
`disabled` property ON PURPOSE: a control that drops out of the tab order the moment you
fix your last edit moves focus out from under the user. The cursor and the handler's early
return were both invisible to a screen reader, which announced an ordinary actionable
button ("No changes, button") that then did nothing.

TEST RESULTS: PASSED.
- `python3 scripts/check_all.py` — "All invariants hold. ✓", exit 0, ZERO soft warnings.
- `python3 scripts/check_docs.py` — OK (95 rules linked).
- `python3 -m pytest` — 1,186 tests, all passing, exit 0 (was 1,180; +6).
- CLI smoke: 35 scripts' `--help`, no traceback.
- **The three assertable fixes were mutation-tested** — un-escaping the dropdown, dropping
  `aria-disabled`, and disabling the arrow-key branch are each DETECTED.
- Regression Scenario 1's parity leg: gallery card count 2,133 == library rows 2,133 after
  the rebuild.
- Both artifacts regenerated and verified to carry the changes (`gallery.html` has the
  light block and the breakpoint; `dashboard.html` has the labels and the BS4-41 loader).

REGRESSION RISKS:
- **These are markup/CSS changes to two generated artifacts and two templates; none of
  them touches a model, a score or a write path.** The riskiest is S-3, which introduces a
  whole colour scheme the gallery has never rendered — and its correctness is exactly the
  half a file cannot prove. See OPERATOR VISUAL CHECKS: it needs eyes before it is
  trusted.
- S-5 changes the dashboard's default for anyone who has never set a theme. Users with a
  stored preference see no change. Reverting is one expression.
- BS4-43's `esc()` calls sit above the `esc` definition in both files; both are hoisted
  function declarations (verified). Had either been a `const` arrow, this would have been
  a TDZ crash on page load rather than a fix.
- `dashboard.html` and `gallery.html` are committed artifacts, so this commit's diff is
  large and mostly generated. The data pipeline feeding the `#data` island was NOT
  touched, per the Deploy Command's restyle rule.

INVARIANTS AT RISK: None. INV-03 requires gallery.html to exist and it was regenerated
(card count verified against the library); no CSV writer, deck file or model was touched.

NET SCORE: 7 production fixes − 0 new failure modes = 7
Per-finding: (a) fired this month? (b) new failure mode?
- BS4-43: (a) NO — needs a quote in a set code, which no real Arena set has. (b) NO.
- S-1: (a) YES for a keyboard user on the deck editor. (b) NO.
- S-2/S-4: (a) YES for an assistive-tech user. (b) NO.
- S-3: (a) YES for a light-OS user, on every visit. (b) NO, but unverified perceptually.
- S-5: (a) YES for a light-OS user's first visit. (b) NO.
- S-6: (a) YES for a screen-reader user. (b) NO.
**Honest framing: six of the seven are accessibility and theming defects that a sighted
mouse user would never encounter.** They are real for the people they affect and invisible
to everyone else, which is precisely why they survived five interface passes.

OPERATOR ACTIONS / DEPLOY:
- **The gallery's new light palette needs a browser check** — a whole scheme that has
  never been rendered. | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push. `.github/workflows/pages.yml` republishes
the dashboard from source on push to `main`; the committed `dashboard.html` and
`gallery.html` snapshots were both regenerated here, so the repo copy and the deployed copy
now agree.

OPERATOR VISUAL CHECKS (the perceptual half these changes cannot assert):
- **Gallery in light mode** — open `gallery.html` on a light-OS machine (or flip the OS
  setting). Correct = header, panels, card frames and muted text all read as a coherent
  light page, with the colour pips still legible (their dark text is deliberate).
- **Gallery at 390px** — scroll top to bottom. Correct = the body never scrolls sideways,
  the search field spans the row, the grid is 2 columns not 1.
- **Dashboard first visit on a light OS** — clear `localStorage` for the page, reload.
  Correct = it opens in light mode; pressing `t` still toggles and persists.
- **Deck editor tab strip** — focus a tab, press ← and →. Correct = focus moves along the
  strip and the panel follows, matching the dashboard's strip.
- **Collection save button with a screen reader** — with no edits pending, Tab to it.
  Correct = announced as dimmed/unavailable, still reachable by Tab.

FOLLOW-ON ITEMS:
- **G-37's live residual is still the most concrete open defect**: `suggest --lands` offers
  cards whose LAND is on the BACK face (Tarrian's Journal, Grasping Shadows, Aclazotz for
  deck 52), reached by transforming and never by a land drop. Out of every batch's scope so
  far because it is a G-37 residual rather than a BS4 finding — it should be picked up
  explicitly.
- `recommendation_row`'s `Cut Rank` raw-name join; `BASICS` defined in four modules.
- The remaining unimplemented scan findings are the Lows not assigned to a batch
  (BS4-21/23/27/38/40/42/44/45).
- The six operator visual checks above, plus Regression Scenarios 5-8's perceptual halves.

DOCUMENTATION UPDATES NEEDED:
- Regression Scenario 5 (light-mode status colours) should gain the gallery, which now has
  a light mode to check; Scenario 6 (phone width) likewise, since the gallery now has a
  breakpoint. Both currently name only the dashboard and the editor pages.
- CLAUDE.md's Presentation health dimension describes the interface layer `/broad-scan`
  Stage 3 grades; no rule statement changed, so no gotcha edit is implied.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
