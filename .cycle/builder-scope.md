# Builder tab — scope (2026-11-01, not started)

**Status: PROPOSED, awaiting the owner's go.** Grew out of the Sultai pile board
(https://claude.ai/artifact/RfDuwKXX3WmTHYcUrLTgAR, source `.cycle/board/`), which the owner
called "basically what I wanted as a deck building tool for the GitHub Pages deployment".
Delete or fold into `.cycle/blocks/` once it ships.

## What the board taught us (keep these)
- One page holding BOTH decks and every pile beat chat lists: card art, oracle text, the reason,
  and a per-card pick, with filters for "in neither list" / reason group / swap candidates first.
- The REASON is the valuable part and the expensive part — it is written by Claude from full text
  against the deck as it stands. Everything else is derivable.
- The theme-fit grade misleads in exactly the documented ways (G-42 polarity: Glarb's mill fills
  THEIR yard, so own-graveyard recursion read KEY there; removal reads tangential everywhere). It
  was dropped from the page; it should not come back as a verdict.
- Placement goes stale when a deck's plan changes: three "fits neither" cards (Tyvar Kell, Kinnan,
  Pol Jamaar) were graded for a plan Thranduil's deck no longer had. A reason needs to know which
  version of the deck it was written against.

## What is wrong with the session board today
1. Built from session scratch files; only `.cycle/board/src/` keeps the inputs. Not reproducible
   by a command.
2. Deck stats in the header are HARD-CODED strings (floor, interaction, sources, tapped cost) —
   they are already stale the moment a swap lands.
3. Picks are per card with no pairing: "add Krang" says nothing about what it replaces, which is
   the decision `/apply-changes` actually needs.
4. Neither deck's current list is on the page, so a cut cannot be chosen there.
5. No filters by role (interaction / card advantage / ramp), cost, rarity or owned.
6. Reasons carry no "graded against" marker, so nothing flags a reason a later swap invalidated.
7. 17 MB of images had to be uploaded as artifact files (the artifact sandbox blocks remote images).

## Proposed shape
### Data (in the repo, reviewed like any other file)
`builds/<slug>/build.json` — one per deck-building project:
```
{ "title": "Sultai pile", "decks": ["75-historic-brawl", "96"],
  "cards": [{"name": ..., "pile": "T|G|B|N", "src": "pile|search"}],
  "reasons": {"<card>": {"group": ..., "75-historic-brawl": "...", "96": "...",
                         "graded_at": {"75-historic-brawl": "<deck file sha>", "96": "<sha>"}}},
  "pile_labels": {"T": "Thranduil", "G": "Glarb", "B": "Either", "N": "Fits neither"} }
```
Everything else (cost, type, text, rarity, owned, in-list, image URL) is derived at build time from
card-pool / card-library / the deck files, so it never goes stale in the file.

### CLI (`scripts/build.py`, name TBD — must not collide with the Makefile/`build_*` scripts)
`new <slug> --decks A B`, `add <slug> <names…|file>`, `place <slug> <card> <pile>`,
`reason <slug> <card> --deck <id> "<text>"`, `check <slug>` (lists reasons whose deck changed
since `graded_at`, and cards now in a list that the build still calls "not in"),
`picks <slug> <pasted block>` → prints a `deck.py swap <id> --package "A=B" …` preview line per deck.
Migration: the Sultai doc §8–9 becomes `builds/sultai/build.json` (the data already exists in
`.cycle/board/index.html`'s data island and `.cycle/board/src/`).

### Dashboard section `sec-build` ("Builder")
- Loaded lazily from a sidecar `_site/builder.json` (same pattern as `collection.json`, so the
  3.5 MB dashboard does not grow), written by `build_dashboard.py --builder-out`; `pages.yml`
  publishes it and its deploy check reads it like it reads `collection.json`.
- Project picker → deck strip with LIVE stats from the model functions (`tier_band` floor,
  interaction / card advantage, `deck_source_profile`, crafts) — never typed in.
- Pile tabs + filters (search, in-which-list, reason group, role, cost, owned/craft, rarity),
  swap candidates first. "Graded against an older list" badge from `graded_at`.
- Card art hot-linked from Scryfall (Pages has no image CSP): `image-manifest.json` for owned
  cards, Scryfall's `cards/named?format=image` redirect for the rest; lazy-loaded.
- Each deck's current list in a side panel with its `cuts` rank, so an add is PAIRED with a cut
  on the page. Picks queue in `localStorage` (like Log-a-match) and "Copy picks" emits the
  `--package` lines `/apply-changes` previews. Nothing is written to the repo from the page.

### Gates it must pass (project rules)
- G-72: every control through `a11y()`; tablist arrows; focus after re-render; token gate
  (every `var(--x)` defined) — `tests/test_templates.py`.
- G-53: the new CLI reached by a skill (`/pile-analysis` and `/draft-deck` should end by writing
  a build file) or exempted with a reason — `check_commands.py`.
- G-55: CLI covered in `tests/test_cli.py`; any JS logic shared with Python pinned under Node
  like `test_dashboard_js.py`.
- G-88: tests use scratch build files, never `builds/` itself.
- A regression scenario (phone width, both themes, keyboard) added to the Cycle Workflow Config.

## Phases (one `/broad-implement` each)
1. Data format + CLI (`new/add/place/reason/check/picks`) + migrate the Sultai build + tests.
2. `build_dashboard.py --builder-out` + read-only `sec-build` (piles, filters, art, live stats) +
   `pages.yml` + template/token tests.
3. Cut pairing panel + picks queue + "Copy picks" → `--package` lines; `/pile-analysis` and
   `/draft-deck` write a build file; scenario walk.

## The claude.ai board meanwhile
Keep it for THIS project (it is the only version whose picks Claude can read directly). Cheap
improvements worth doing now, before the Pages version exists: derived deck stats (2), both decks'
current lists with cut ranks (3–4), add↔cut pairing on picks (3), role/cost/owned filters (5).
Once phase 2 ships, the board can be regenerated from `builds/sultai/build.json` by the same code.
