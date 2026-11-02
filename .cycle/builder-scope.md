# Builder — implementation plan (2026-11-01)

**Status: batch 1 DONE 2026-11-01; batch 2 + 2a DONE 2026-11-01 (`scripts/builder_template.html`, `builder.py render`, Sultai board republished, `.cycle/board/src/` retired); batch 2b DONE 2026-11-01 (compare view, hidden roles, ownership queue, applied, conflicts, undo, next band, curve); batch 3 DONE 2026-11-02 (`builder.py site`, dashboard link + section, pages.yml build + verify, scenario 25); next 4, then alternate printings.** Grew out of the Sultai pile board
(https://claude.ai/artifact/RfDuwKXX3WmTHYcUrLTgAR, source `.cycle/board/`), which the owner called
"basically what I wanted as a deck building tool for the GitHub Pages deployment". Four
`/broad-implement`-sized batches below. Delete this file, or fold it into `.cycle/blocks/`, once
batch 4 ships.

## What the session board settled (design inputs, all owner-approved)
- **Layout (hybrid of mocks B + C):** one row per card (thumbnail, cost pips, swap seal, role tag,
  in/protected tag per deck, one-line reason, quick per-deck toggles) beside a sticky DETAIL pane
  that shows the FULL card image, the full reason, rules text, pick buttons, add↔cut pairing,
  compare, and an always-open note. Phone: the detail opens as a bottom sheet. Keyboard: j/k or
  arrows, 1..N toggles deck N, b bench, o keep out, n note, / search, z zoom.
- **Polish (mock A, theme-agnostic):** engraved small-cap headings, a reading serif for reasons,
  a condensed UI face with mono numerals, brass hairlines, seal labels, ringed commander portraits.
  Neutral light AND dark palettes. **Each deck's accent comes from its own main colour** (most
  sources), so nothing is tied to one clan; card rows carry a colour-identity stripe.
- **Fonts: DECIDED 2026-11-01 — pairing 1 ("Current")**: Marcellus SC (headings) · Spectral
  (reading) · IBM Plex Sans Condensed (interface) · IBM Plex Mono (numbers), chosen from the
  specimen sheet (https://claude.ai/artifact/XHSGYFVeu2bWT5gHr6jJg7). The template keeps them as
  four tokens (`--display --read --ui --mono`).
- **Features that must carry over:** picks + per-deck pairing ("this replaces"), notes on any card,
  review progress per pile + hide-marked, swap-candidates filter, role/MV/owned/rarity filters,
  before→after projection (interaction and card advantage are additive per card in `role_tally`,
  so the page's arithmetic is exact), compare add-vs-cut, zoom with prev/next, Deck lists with
  `cuts` ranks and protected group, Add-cards request queue, "Copy as text" ending in
  `deck.py swap <id> --package "CUT=ADD" …` lines.
- **PAGE = TEMPLATE + DATA** (already true of the board): styling never touches card data.

## Lessons the plan must respect
- The REASON is the only expensive, hand-written part. Everything else is derived at build time.
- The theme-fit grade misleads in documented ways (G-42 polarity; removal reads tangential) — it is
  NOT shown as a verdict.
- Placement goes stale when a deck changes plan (three "fits neither" cards were graded for an old
  plan). A reason records which deck version it was written against, and a check flags drift.
- Stats typed into a page go stale at the first swap: derive them.

## Architecture
- **Delivery:** a separate page `builder.html` on the Pages site, linked from the dashboard header
  and a small "Builder" section listing projects. Not a section INSIDE the 3.5 MB dashboard: the
  console needs the full width and a sticky pane, its keyboard map would collide with the
  dashboard's (`t`, `g`, `/`), and a separate page keeps the dashboard's tests untouched. It reads
  the dashboard's stored theme preference (`mtga-prefs`) so the two pages agree on light/dark.
- **Two targets, one template:** (1) Pages — picks and requests live in the browser with
  copy-out, images hot-linked from Scryfall (no CSP on Pages); (2) a claude.ai artifact per project
  — picks/notes/requests in the artifact's store so Claude reads them directly, images uploaded as
  artifact files. The template already branches on `window.claude`.
- **Data:** `builds/<slug>/build.json`, curated and reviewed like any repo file:
  `title`, `decks` (ids, in display order), `piles` (key, label, intro, which deck it favours),
  `cards` [{name, pile, src}], `reasons` {card: {group, text | per-deck texts, graded_at: {deck: sha}}}.
  Derived at render: oracle text, cost, type, rarity, owned, roles, ri/rc/mf/land, in-list and
  protected flags, live deck stats, nonland lists with `cuts` rank, floor thresholds
  (`floor_requirements`), image URL.

## Batches

### Batch 1 — Data model, derivation and CLI (no UI)
- `scripts/builder.py` (name checked against the Makefile and `build_*` scripts):
  `new <slug> --decks A B`, `add <slug> <names|file> [--pile P]` (resolves against card-pool,
  refuses names not on Arena), `place`, `reason <slug> <card> [--deck id] --group G "text"`,
  `check <slug>` (reasons whose deck file changed since `graded_at`; cards the build calls
  "not in" that a deck now runs; cards on no pile), `picks <slug> <pasted block>` (parses the
  page's copy-out → per-deck `swap --package` preview command), `derive <slug> --json`.
- Move the derivation now in `.cycle/board/src/refresh.py` (live stats, lists, cut ranks, roles,
  ri/rc/mf, protect, req) into `builder.py` as functions that call the model, never re-implement it.
- Migrate the Sultai project: `.cycle/board/src/data.json` + §8–9 → `builds/sultai/build.json`.
- Tests: `tests/test_builder.py` (derive on a scratch build, check catches a changed deck, picks
  parser round-trips the copy-out format, unknown names refused) — scratch dirs only (G-88);
  `tests/test_cli.py` entries; `check_commands.py` reachability.
- `check_all`: a SOFT sweep over `builds/*` reporting stale reasons (drift), not a gate.

### Batch 2 — Generic template and renderer
- `scripts/builder_template.html`, generalised from `.cycle/board/src/template.html`: N decks
  (1–4) with keys from `build.json`, piles from data, pick verbs and pairing per deck, keyboard
  1..N, font tokens set to the owner's chosen pairing, deck accent from main colour.
- `builder.py render <slug> --target pages|artifact --out DIR` — Pages: Scryfall image URLs;
  artifact: downloads and resizes images (the current `fetch_images.py`) into `DIR/img/`.
- Regenerate the Sultai board from `builds/sultai/` and republish it to the SAME artifact URL;
  retire `.cycle/board/src/`.
- Tests: template token gate and a11y markup pins in `tests/test_templates.py` (every control a
  real button/select, focus ring, `var(--x)` defined in both themes); the page's projection and
  name parser run under Node against Python's numbers, like `test_dashboard_js.py`.

### Batch 2a — owner notes folded in (approved 2026-11-01)
Goes with batch 2, since that batch rebuilds the page anyway:
- Theme toggle (header button + `t`), remembered; on Pages it shares the dashboard's `mtga-prefs`.
- Row buttons as a 2×2 block: deck toggles on top, Bench / Keep out (icons + tooltips) below.
- Clicking an already-selected row opens a one-line comment row under it — the SAME note as
  the pane's; `n` opens it. The detail pane is collapsible (open by default, remembered), and
  while it is collapsed the full card appears beside a row on hover or focus.
- Deck-list rows: Protect / Unprotect REQUESTS (not edits), emitted in "Copy as text"; Claude
  applies them as a `#: protect:` header edit.
- Sharper images: small row thumbnails stay; detail pane and zoom use 672 px (Scryfall
  `large`). Pages hot-links Scryfall; the artifact uploads both sizes.

### Batch 2b — Compare and review aids (approved 2026-11-01)
- **Compare view**: pile on the left, the chosen deck's current list on the right (same rows,
  thumbnails, roles, cut rank, same detail pane). A selected pile card highlights the deck card
  it replaces; clicking a pile card then a deck card sets the pairing. Phone: two tabs.
- **Hidden-role markers**: dotted "Interaction?" / "Card advantage?" tags from
  `role_coverage_flags` (suspected), plus hand-confirmed hidden roles stored with the reason;
  the projection shows counted and with-hidden figures. Confirmed tags are G-67 pattern leads.
- **Ownership**: owned/craft on the row; an "I own this many" control in the pane that queues
  corrections; the queue copies out as an `/ingest` batch (reconcile_crafts `--set-exact`).
  Ownership stays information only.
- **Applied state**: cards whose swap landed show "applied ✓" and fold away.
- **Conflict warnings**: one deck card chosen as the cut for two adds; a card picked for both
  decks when that is not intended.
- **Undo** the last pick (`u`).
- **Floor letter in the projection** (before → after), not only the counts.
- **Mana curve before/after** in the Compare view.

### Later — alternate printings, view only (approved 2026-11-01)
- List each card's other Arena printings (art, set, rarity — rarity can differ between
  printings) from Scryfall, view only; the owner picks the art in Arena. Exclude the generic
  borderless "semi-transparent text box" variant most cards have. No deck-file change: the
  project keys one printing per card and an unknown set code is a hard INV-04 failure.
  Artifact target: limit images to cards marked to add or in a deck.

### Batch 3 — Pages integration
- `build_dashboard.py` (or a sibling call in `pages.yml`) renders every `builds/*` project to
  `_site/builder.html` + `_site/builds/<slug>.json` (lazy-loaded per project; a project picker
  when there are several).
- Dashboard: a header link and a "Builder" section listing projects (title, decks, card count).
- `pages.yml` deploy check reads the builder page like it reads `collection.json` (non-trivial
  size, data present) and annotates failures.
- Regression scenario 25 (Builder walk: phone width, both themes, keyboard, copy-out, Scryfall
  images load) in the Cycle Workflow Config; README section; `docs/systems-map.md` entry.

### Batch 4 — Workflow wiring
- `/pile-analysis` Stage 5 and `/draft-deck` Stage 6 write or update `builds/<slug>/build.json`
  (so every future pile ends up as a board), and say how to render/publish it.
- `/apply-changes` accepts a pasted Builder picks block: `builder.py picks` prints the `--package`
  preview, then the normal swap/quality/preflight flow runs.
- Request processing for the claude.ai target documented as a skill step: read `requests` from
  the artifact store, `builder.py add` + reasons, re-render, republish, mark done.
- CLAUDE.md: one Common Gotchas entry (PAGE = TEMPLATE + DATA; reasons are graded against a deck
  version; the theme-fit grade is not a verdict), word-capped per `check_docs.WORD_CAP`.

## Open decisions for the owner
1. (decided) Font pairing 1.
2. Should the Pages builder show picks from the claude.ai board? (It cannot read the artifact
   store; the answer today is copy-out → paste. Keep it that way unless asked.)
