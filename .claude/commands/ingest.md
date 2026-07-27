Route incoming card data to the right ingest tool, then rebuild what depends on it.

There are five ways card data enters this repo and they are NOT interchangeable — they
disagree about what a quantity MEANS. Picking the wrong one either undercounts your
collection or silently overwrites it. This command is the front door: it identifies what
you actually have, hands off to the right tool, and then runs the shared tail that every
ingest needs and that is easy to forget.

It **orchestrates the existing scripts and never re-implements them**, so it cannot drift
from their behaviour. Read CLAUDE.md's Common Gotchas first — especially the deck-dump
undercount and the DFC front-vs-full-name convention.

## Stage 1 — Identify what you have

Ask, or infer from `$ARGUMENTS` / the user's last message. **The deciding question is
whether the quantities are LOWER BOUNDS or AUTHORITATIVE.**

| What you have | Route | What a quantity means |
|---|---|---|
| Arena export of cards you just **crafted or opened** | `/add-cards` → `reconcile_crafts.py` | lower bound; takes `max(existing, line)` |
| A **deck list** you built in Arena, to true up counts | `import_arena.py <file> --skip-basics` | lower bound — each line is what that deck plays, not what you own |
| A **tracker's full-collection CSV/TSV** | `import_collection.py` | **authoritative** — sets exact counts, including DOWN |
| The companion **Google Sheet** | `sheets_sync.py pull` | authoritative; needs credentials (ROADMAP Tier 3, not wired up) |
| A **new deck** to store in the repo | `/add-deck` | not an ownership change at all |
| One card to fix by hand | `make app` (the Flask editor) | interactive |

Signatures to tell them apart:
- Lines like `1 Doctor Doom (MSH) 95`, often under a `Deck` header → an **Arena export**.
  If the user says they *crafted/opened* these, it is the crafted-cards route; if it is a
  list they *built*, it is the deck-dump route.
- A header row with comma/tab-separated columns (`Card Name,Set,Quantity` or similar) →
  a **tracker collection export**.
- If it is ambiguous, ASK. Guessing between "lower bound" and "authoritative" is the one
  mistake here that loses data.

## Stage 2 — Dry-run, always

Every tool here defaults to a dry run. Show the user what would change before writing:

- `python3 scripts/reconcile_crafts.py <export>` — adds to the library, appends the
  `card-mana.csv` row, drops the card from `card-wishlist.csv`
- `python3 scripts/import_arena.py <file> --skip-basics --dry-run`
- `python3 scripts/import_collection.py <file>` — also reports cards owned here but
  ABSENT from the export; those are left alone unless you pass `--zero-missing`
- `python3 scripts/sheets_sync.py pull --dry-run`

Report the counts and anything flagged (unparseable lines, ambiguous name-only rows,
cards about to be zeroed), then **ask before applying**. Only `import_collection.py` can
lower a count, so give its output the closest read.

Apply with `--apply` (or, for `import_arena.py`, by dropping `--dry-run`).

## Stage 3 — The shared tail

**This is the part that gets skipped, and skipping it leaves the integrity gate red with
no hint why.** A newly added card has no `card-mana.csv` row, so INV-02 fails until
`build_mana.py` runs. Run in this order — the dependencies are real:

1. `python3 scripts/enrich.py` — fill Type / Card Text / Color(s) / Collector #
2. `python3 scripts/build_mana.py --pool` — cost + keywords **← INV-02 depends on this**
3. `python3 scripts/tag_synergies.py --merge` — keyword-aware tags (needs step 2's data;
   `--merge` adds without clobbering hand-curated cells)
4. `python3 scripts/build_pool.py --all` — re-derive pool tags through the same `tags_for`
5. `python3 scripts/build_gallery.py` — art for the new cards
6. `python3 scripts/check_all.py` — confirm every invariant holds

`/refresh` runs exactly this chain; prefer it unless you need to skip steps. Steps 1–4
need Scryfall; if it is unreachable, say which steps were skipped and that INV-02 will
stay red until they run.

## Stage 4 — Report

- What was ingested, by which route, and what changed (added / bumped / zeroed).
- Anything the tool refused or flagged, verbatim — an unparseable line or an ambiguous
  name-only row is a card that did NOT get counted.
- The `check_all` result.
- Then suggest the natural follow-up: `/add-cards` finishes with a cross-deck fit pass
  (`deck.py suggest-homes <card>`) for anything newly owned, and `/roster-review` if a
  lot changed. Because owned copies are fungible across decks, a newly-owned card can go
  into **every** deck that earns it — never ask the user to pick one home.
