---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (Batch F — editor theming + phone width, the last interface batch):
- S-3 | templates/ had NO breakpoints at all: deck.html's card rows needed a 472px minimum inside the 350px a 390px viewport leaves, so the page BODY scrolled sideways — the failure Regression Scenario 6 declares unacceptable, on the surface you type into
- S-8 | three sibling pages of one app carried three incompatible status vocabularies (--ok/--short/--missing · none at all · --ok/--warn/--bad), no light mode on any of them, and five hardcoded hexes bypassing the tokens that did exist
- S-9 | the dashboard's status pills themed only their TEXT: ~14 dark-tuned literal rgba fills/borders whose .28–.3 borders fell to roughly 1.3:1 over light mode's white panel, so the pills lost their chip shape and read as loose coloured words

Files modified: scripts/build_dashboard.py, dashboard.html (rebuilt), templates/collection.html,
templates/deck.html, templates/decks.html, tests/test_templates.py

CHANGES:
S-9 | build_dashboard.py, dashboard.html | 10 rules / 14 fills + 3 borders converted to
`color-mix(in srgb, var(--ok|--warn|--bad|--accent) N%, transparent)` — the status token
already flips per theme, so both themes now come from ONE declaration instead of a
dark-only literal (.b-ok/.b-missing/.b-short, .stalechip, .v-tune/.v-craft/.v-ok,
.t-s/.t-a/.t-b/.t-c, .radd/.rrem). I-03 had moved only the `color:` half; this is its
residual. Artifact rebuilt (18 color-mix sites live in dashboard.html).
S-8 | all three templates | ONE vocabulary: deck.html's --short/--missing renamed to
--warn/--bad (CLASS names .stat.short / .summary b.missing stay page-local and the JS
that emits them is untouched — verified), collection.html gains --ok/--warn/--bad it
never had, decks.html already matched. Five literals replaced by tokens: two
`#save.ready { color:#0c130e }`, `.tool.go { color:#1a1a1a }`, `.pip { color:#1a1a1a }`,
`.rm:hover { #e39a8a }`, plus the three `rgba(15,17,21,.96)` headers and collection's two
`rgba(10,11,14,.8)` art scrims. New tokens encode a real distinction the old literals
blurred: `--on-solid` FLIPS with its fill (dark ink on a light green button, light ink on
a dark one), while `--pip-ink` / `--scrim` / `--scrim-ink` are theme-INVARIANT because
they sit on card-identity swatches and card ART. Light palette added to all three via
`prefers-color-scheme`; every light pair clears WCAG AA at body-text level (measured:
accent 4.68, ok 5.33, warn 5.75, bad 5.70, muted 6.00, text 15.0+).
S-3 | all three templates | a `max-width: 620px` breakpoint each. deck.html's card row
wraps with `.name` taking its own full-width line (order:-1 puts it first, where it
reads) and the fixed fields sharing the second — 52+64+56+24 + gaps = 228px, leaving the
status column ~120px inside 350px; `white-space:pre` comment rows scroll inside
themselves rather than pushing the body. decks.html gives the deck NAME its own line
(it had ~54px at 390px). collection.html, which survived by luck via auto-fill/minmax,
just stops wasting a third of the screen on fixed padding and a 240px search min-width.

TEST RESULTS: 1029 passed (1022 + 7 new), 0 failed. check_all green with zero soft
warnings; check_docs green. The 7 new pins are in tests/test_templates.py and were
verified NON-VACUOUS by printing the extracted token sets (22/13/11 tokens per page) —
the first draft's lowercase-only regex silently skipped the uppercase pip tokens, which
would also have left 6 dead entries in the _THEME_INVARIANT allowlist, the
"registry that looks considered while covering nothing" shape check_patterns gates
against; fixed to a case-insensitive class, and all 9 allowlist entries are now
load-bearing. Scenarios 5/6/7's MARKUP halves are pinned and green (one vocabulary, no
mode inheriting gaps, every consumed token defined, a breakpoint per page); their
PERCEPTUAL halves stay the operator's browser walk — and both got materially shorter.
NOT APPLICABLE: Scenarios 1-4, 8 (no ingest, analysis, or write-path files touched).

REGRESSION RISKS:
- `color-mix` needs Chrome 111 / Safari 16.2 / Firefox 113 (all 2023). The dashboard
  already requires backdrop-filter, aspect-ratio and inset, so this does not move the
  floor much — but it IS a newer baseline, and on an older browser the affected pills
  lose their fill (text and border colour still read). Noted rather than hedged with a
  literal fallback, which would reintroduce exactly the dark-tuned constant being removed.
- The editor pages now follow the OS colour scheme. A user on a LIGHT OS gets a light
  editor where they previously got dark — intended, and the fix Scenario 7 asked for.
- Deliberately NO in-page theme toggle: the dashboard's lives on a different ORIGIN
  (file:// or Pages vs 127.0.0.1), so its stored choice cannot reach the editor, and
  three hand-copied toggles is duplication that rots. A [data-theme] hook goes in when a
  toggle does — one block, not two, until there is something to switch.
- Breakpoints apply only ≤620px; desktop layout is unchanged.
- No Python behaviour changed (the build_dashboard edits are inside its CSS string).

INVARIANTS AT RISK: None. INV-03's dashboard.html rebuilt through its own builder.

NET SCORE: 3 − 0 = +3
(All three were live on every page load for anyone on a phone or a light-mode OS; S-9
additionally completes a fix — I-03 — that had shipped half-done.)

OPERATOR ACTIONS / DEPLOY:
- Walk Scenario 5 (light-mode pills now have real fills), Scenario 6 extended to the
  EDITOR at 390x844, and Scenario 7's editor leg in light mode | BLOCKS DEPLOY: N
Deploy: commit/push is the deploy; pages.yml republishes the rebuilt dashboard on merge
to main. The editor is local — `make app` picks the templates up on next launch.

FOLLOW-ON ITEMS:
- Batches G (CLI/resilience polish) and H (strategic) remain; BS2-07's header-consumer
  sweep is still the standing Batch A leftover.
- The three interface batches (E, F) close every STRUCTURAL Stage-3 finding. What is
  left on that axis is perceptual and needs a person at a browser.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md Regression Scenario 5: its "All 16 of these sites were hardcoded to the
  DARK-mode hexes until I-03" note is now out of date — the FILLS and BORDERS derive too
  (S-9), so the check becomes "does each pill still read as a bounded chip".
- CLAUDE.md Regression Scenario 6: extend from dashboard-only to the editor pages, which
  now have breakpoints (this was the proposed new Scenario 9 in the scan's operator list;
  folding it into 6 is tidier than a new scenario).
- CLAUDE.md Regression Scenario 7: the editor leg no longer snaps to forced dark, so the
  walk should be done once in each OS colour scheme.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
