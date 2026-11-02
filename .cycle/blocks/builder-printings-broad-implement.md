---BUILDER IMPLEMENTATION SUMMARY---
Item implemented: view-only alternate Arena printings (the last approved Builder item, .cycle/builder-scope.md — now deleted)
Files modified: scripts/builder.py, scripts/builder_template.html, builds/sultai/printings.json (new), tests/test_builder.py, CLAUDE.md (G-89), docs/gotchas.md, README.md, .cycle/board/index.html, .cycle/builder-scope.md (deleted)

CHANGES:
- builder.printing_arts(slug, names, fetch): oracle ids via post_collection (front-face aliased in a second pass, G-63), then `game:arena unique:art (oracleid:… or …)` searches in batches of 12 (30 overflowed the URL, HTTP 400). One entry per illustration, oldest first, with set, number, set name, rarity, year, artist, art-crop and normal URLs, and visual treatments (showcase, borderless, full art, extended art, etched). Cached in builds/<slug>/printings.json; a one-art card is cached as [] and never returned; an outage leaves the cache as it was.
- render attaches `al` to cards with ≥2 artworks (fetch=False reads the cache only, so the offline Pages job works). Artifact: `_art_sprites` packs every art into sheets of 60 cells (366×267) — 5 files for Sultai, ~7 MB — keeping the board at 434 of 511 files.
- Template: an "Arena printings · N artworks" section in the card pane (thumbnails with set #, rarity, year, treatments); click enlarges — Pages opens the full card in the zoom dialog, the artifact shows the art cell in its own dialog; a ⧉N tag on rows that have alternates. View-only: no pick, no deck-line change (the pool keys one printing per card; unknown set codes are a hard INV-04 failure).
- The owner's exclusion (the borderless "see-through text box" treatment of the same art) is satisfied by `unique:art`: same illustration collapses to one entry. Checked on the Sultai pile: every remaining borderless print is a different illustration by a different artist.

MEASURED: 111 of 426 Sultai cards have alternate artworks; 261 artworks in all; max 6 for one card. Fetch ~20 s once, then cached.
TEST RESULTS: builder tests pass (new: fetched once and cached, one-art cards dropped, treatments filtered, unique:art in the query; offline render reads the cache and attaches `al` without network); check_all OK; check_docs OK; full pytest suite passed (rc=0). Chromium walk: ⧉3 row tag, 3 thumbnails, enlarge dialog with caption, Escape closes, no script errors.
REGRESSION RISKS: a new set adds artworks the cache does not know until the next online render (`builder.py render <slug> --target pages|artifact` without --no-images) refreshes missing names; existing names are not re-queried — delete printings.json to force a full refresh.
NET SCORE: 0 − 0 = 0 (new capability).
DEPLOY: claude.ai board republished (v19). Pages picks it up on the next merge to main.
---END---
