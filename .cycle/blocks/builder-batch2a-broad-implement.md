---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Builder batch 2 + 2a (.cycle/builder-scope.md) — generic template, renderer, and the owner's board notes
- B2a: `scripts/builder_template.html` — the board template generalised: decks (1–4) and piles come from the build's data, pick verbs, keys 1..N, colours and labels per deck; no Sultai-specific text left in the template
- B2b: `builder.py render <slug> --target pages|artifact --out DIR` — PAGE = TEMPLATE + derived data; pages hot-links Scryfall (normal/large) and is a whole document; artifact writes img/lg/ (672 px) plus one thumbnail sprite
- B2c: theme toggle (header button + `t`), first-paint from the stored choice, written into the dashboard's shared `mtga-prefs` by merge
- B2d: row quick-picks as a 2×2 block — deck toggles on top, Bench / Keep out (icons, labelled) below
- B2e: clicking an already-selected row opens an inline comment row (the same note as the pane; Esc closes); collapsible detail pane (button + `p`, remembered); hover/focus card preview while the pane is collapsed
- B2f: Protect / Unprotect requests on deck-list rows, emitted in Copy as text; `builder.py picks` checks them against the deck's `#: protect:` header
- B2g: sharper images — detail pane and zoom use 672 px images; rows use a sprite sheet on the artifact
- B2h: Sultai board regenerated from builds/sultai and republished to the same URL (versions 14–17); `.cycle/board/src/` and `fetch_images.py` retired
- B2i: plan updated with the owner-approved 2b items and view-only alternate printings
Files modified: scripts/builder_template.html (new), scripts/builder.py, builds/sultai/images.json (new), tests/test_builder.py, tests/test_builder_template.py (new), .cycle/board/index.html, .cycle/board/src/* (deleted), .cycle/board/fetch_images.py (deleted), .cycle/builder-scope.md, .cycle/sultai-pile-analysis.md

CHANGES:
B2a | scripts/builder_template.html | Decks from meta.decks (label from build.json, accent from the deck's main colour); piles from meta.piles (tone from the pile's deck, muted for N); the In-list filter, Add-cards destinations, PICKLAB and pick order are built per deck; keys 1..N; picks validated per deck key on load. Storage keys are per build slug.
B2b | scripts/builder.py | `render` + `image_urls` (build cache `builds/<slug>/images.json` → image-manifest.json → Scryfall; an outage degrades to missing images, never a failed render; cache committed so an offline Pages build in batch 3 has URLs) + `_fetch_image` + `_sprite`. Title HTML-escaped; `</` escaped in the data island.
B2c | template | `toggleTheme` reads mtga-prefs, sets `theme`, writes it back (the dashboard keeps six other prefs in that object). Head script applies a stored theme before first paint.
B2d | template | `.q` grid with `--qn` = max(2, decks); Bench/Keep out are SVG icons with aria-labels and tooltips.
B2e | template | Rows are wrapped (`.rw`, the listitem) so the inline note sits under its row; note edits sync across every textarea for the card and update only the ✎ dot (no row re-render while typing). Pane state in `builder-prefs`; peek shows the 672 px image beside the list (or over its right side when there is no room) only while the pane is collapsed and not on phones.
B2f | template, scripts/builder.py | `prot<KEY>` / `unprot<KEY>` picks (cards on the deck list need not be on the board — names come from the lists); Copy as text adds `protect:` / `unprotect:` lines per deck; parse_picks reads them; picks_report validates against `deck._protected(meta)` and the deck's cards, naming stale requests.
B2g | scripts/builder.py, template | An artifact version holds at most 511 files (the first publish was refused at 640): small + large per card stops fitting at ~250 cards. Rows now draw from one sprite (68×94 cells, 2x) and the pane/zoom/peek/portraits use img/lg; ~500 cards fit.
B2h | .cycle/board/ | Rendered data verified field-identical to the batch-1 data.json on all 426 cards before the old sources were deleted. Republished in four steps (page + sprite with 240 removals; 186 removals; 213 + 213 large images).

TEST RESULTS: check_all OK (no new soft lines). pytest full suite rc=0 (run before the sprite change); tests/test_builder.py, tests/test_builder_template.py and tests/test_cli.py re-run after it: 50 passed. New: render (pages document, artifact local images, unknown target), protect parse + header validation, template token gate (consumed tokens defined; both dark blocks define the same tokens), no inline handlers, typed buttons, mtga-prefs merge, keys ignored while typing, and a Node test running the page's own `project()` and `parseNames()` against the deck model (a real swap on a scratch copy: interaction, card advantage, tier floor) and the CLI's name reader. A headless-Chromium walk confirmed theme toggle, inline note sync, Esc, pane collapse, peek, bench, protect/unprotect copy text and no sideways scroll at 390 px.
REGRESSION RISKS: (1) Existing claude.ai picks keep working: pick values and db fields are unchanged for keys T/G; only the browser-only fallback storage key changed (`builder-sultai-picks`), which held nothing on claude.ai. (2) The artifact now needs img/lg and img/thumbs.jpg; a card added later needs a re-render and those two files republished. (3) Clicking the already-selected row now opens the note instead of doing nothing.
INVARIANTS AT RISK: None — no canonical CSV or deck file is written; render writes only its out dir and builds/<slug>/images.json, through atomic_write.
NET SCORE: 0 production fixes − 0 new failure modes = 0. New capability; the 511-file ceiling was found and designed around before it shipped.

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation: `.github/workflows/pages.yml` — not touched (the Pages target is wired in batch 3).

(Not complete in production until blocking operator actions are done AND
the deploy step is confirmed.)

FOLLOW-ON ITEMS:
- The artifact holds at most ~500 cards (511 files per version). If a build grows past that, move large images to the artifact asset store.
- Batch 2b (approved): compare view, hidden-role markers, ownership controls + ingest queue, applied state, conflict warnings, undo, floor letter in the projection, curve before/after. Compare view will need deck-list card images too.
- Perceptual walk (both themes, phone width, keyboard-only) belongs in regression scenario 25, scheduled for batch 3.

DOCUMENTATION UPDATES NEEDED:
- None this batch; the CLAUDE.md entry stays scheduled for batch 4.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
