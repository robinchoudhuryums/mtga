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
`build_mana.py` runs.

```
make refresh
```

That is the whole tail, in the one place the order is defined. **Do not hand-run the
steps** — the order is a real dependency graph (`build_mana --pool` READS
`card-pool.csv`; `tag_synergies` reads `card-mana.csv`), it used to be written out in
four places, and three of them — including this one — had `build_pool.py` in the wrong
position. Getting it wrong is quiet: a newly released set's pool cards end up with no
mana row until the next cycle, so they rank with no cost and no keyword tags. The
Makefile target announces each step, so a failure is still attributable.

It needs Scryfall and is slow (`build_mana --pool` prices ~15.9k cards against a rate
limit). If Scryfall is unreachable, say which steps were skipped and that INV-02 stays
red until they run.

## Stage 3b — Verify the ingest actually landed

```
python3 scripts/verify_ingest.py <the same export>          # or --exact
```

Every failure mode in this subsystem is a SILENT UNDERCOUNT, and `check_all` cannot see
one: a card that never arrived breaks no invariant, so the gate stays green. This reads
the paste back against the library and reports, per card, whether it is present, at the
expected count, and covered by `card-mana.csv`.

Pass `--exact` **only** for the authoritative `import_collection.py` route — it requires
`owned == pasted`, which is right for a full-collection export and wrong for every other
route, where a line is a lower bound. A non-zero exit means the ingest is not finished:
re-run it for the named cards, or run `make refresh` if the gap is the mana rows.

## Stage 4 — Report

- What was ingested, by which route, and what changed (added / bumped / zeroed).
- Anything the tool refused or flagged, verbatim — an unparseable line or an ambiguous
  name-only row is a card that did NOT get counted.
- The `verify_ingest.py` verdict — say plainly whether every pasted card landed, and name
  any that did not. This is the answer to "did my ingest work", so do not bury it.
- The `check_all` result.
- Then suggest the natural follow-up: `/add-cards` finishes with a cross-deck fit pass
  (`deck.py suggest-homes <card>`) for anything newly owned, and `/roster-review` if a
  lot changed. Because owned copies are fungible across decks, a newly-owned card can go
  into **every** deck that earns it — never ask the user to pick one home.
