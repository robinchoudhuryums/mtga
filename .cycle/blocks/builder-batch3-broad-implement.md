---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Builder batch 3 (.cycle/builder-scope.md) — Pages integration
- B3-1: `builder.py site --out DIR` — every build rendered for GitHub Pages, offline: DIR/builds/<slug>.html (self-contained, data inline, Scryfall hot-linked images), DIR/builds/index.json (the project list), DIR/builder.html (the picker)
- B3-2: Dashboard — a ⚒ header link to builder.html and a "Builder" section (collapsible, in the section nav) listing each project's title, decks and counts, linking to its page
- B3-3: pages.yml — a Builder build step (failures annotated, never blocking the dashboard) and a verify step that refuses a missing picker or a listed project page with no data island
- B3-4: Regression scenario 25 (Builder walk), a README section, a docs/systems-map.md §5c entry; CLAUDE.md C-07 test-file count 33 → 35
Files modified: scripts/builder.py, scripts/builder_template.html, scripts/build_dashboard.py, dashboard.html, .github/workflows/pages.yml, tests/test_builder.py, CLAUDE.md, README.md, docs/systems-map.md

CHANGES:
B3-1 | scripts/builder.py, scripts/builder_template.html | `render` gains `page_name`, `fetch` (image lookup off for the Pages job — the committed images.json cache is the source) and `home` (the page's ← Dashboard link, shown only when set). `site` neutralises deck.py's live-Scryfall fallbacks like build_dashboard's `_no_network`, renders each project, and leaves a failing one out of the index with a `WARN:` line (exit 1). `summaries()` gives the dashboard light per-project facts without deriving anything. Deviation from the plan's wording: one self-contained HTML per project instead of a shared builder.html that fetches builds/<slug>.json — same lazy loading (a project's data loads only when its page opens) with no change to the template's synchronous boot, and the picker still lists every project.
B3-2 | scripts/build_dashboard.py, dashboard.html | payload `builds` (error-tolerant), section `sec-builder` registered in SECTIONS (open by default), `renderBuilder()`; a copy opened from disk links to the live site (SITE_BASE = LIVE_URL under file:).
B3-3 | .github/workflows/pages.yml | Build step: `builder.py site --out _site`, every `WARN` → annotation, exit status swallowed so a broken project cannot block the dashboard. Verify step: builder.html must exist (the dashboard links to it); each project in index.json must be >1 KB with its `#data` island; a builds/ dir with projects but none rendered → warning annotation.
B3-4 | CLAUDE.md, README.md, docs/systems-map.md | Scenario 25 (perceptual walk: links, theme, pane, Compare pairing, ownership, hidden role, undo, copy-out round trip, phone width, keyboard). README "Builder" section with the commands. Systems map §5c with three reconciliation points (a pick is a request; a reason is graded against a deck version; an ownership correction is an /ingest batch).

TEST RESULTS: check_all OK (13 soft). check_commands OK. Full pytest suite passed (rc=0). New tests: site writes picker + index + one page per build with the home link; one broken build is reported and the others still render; summaries; the dashboard template carries the link, section, registry entry and renderer; the workflow builds and verifies the Builder. Local dry run: build_dashboard + builder site into a scratch _site, then the workflow's verify script executed verbatim → OK. Chromium walk: header link and section card → picker → project page (116 rows, Scryfall large image URL, Pages banner) → ← Dashboard, no script errors.
REGRESSION RISKS: (1) The Pages job now runs `deck.py consistency --tempo` per build deck (~5 s per project). (2) A new project whose images.json lacks URLs publishes without images and a WARN annotation — run `builder.py render <slug> --target pages` online once to fill the cache. (3) The dashboard section is open by default; collapse state is remembered per browser as for other sections.
INVARIANTS AT RISK: INV-03 (dashboard.html content) — rebuilt and checked; the data island and size are intact.
NET SCORE: 0 production fixes − 0 new failure modes = 0. New capability.

OPERATOR ACTIONS / DEPLOY:
- Merge to main for the Pages job to publish builder.html and builds/sultai.html | BLOCKS DEPLOY: N
Deploy: Presentation: `.github/workflows/pages.yml` — runs on push to main (now also builds the Builder pages).

(Not complete in production until blocking operator actions are done AND
the deploy step is confirmed.)

FOLLOW-ON ITEMS:
- figure drift (soft): G-35 cites 130 decks walked; live is 132 (decks added this session). Left for /sync-docs.
- Batch 4: skills wiring (/pile-analysis Stage 5, /draft-deck, /apply-changes reading a picks block), request processing for the claude.ai board, the CLAUDE.md Common Gotchas entry. Then view-only alternate printings.
- The claude.ai board was not republished: the only template change this batch is the Pages-only ← Dashboard link, hidden on the artifact.

DOCUMENTATION UPDATES NEEDED:
- None beyond what this batch made; the CLAUDE.md Gotchas entry stays in batch 4.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
