# Roadmap — MTG Arena Card Library

Grounded in the project's current state and deferred ideas. Regenerate with
`/roadmap`. Effort: S ≈ <2h, M ≈ ½–2 days, L ≈ 3+ days (one dev + Claude Code).

## Tier 1 — Short-term (days–weeks)

- **Theme the remaining UB flavor mechanics** (Vivid, Job select, Opus, Infusion,
  Paradigm, Increment, Disappear) in `tag_synergies.py`'s keyword→theme map, or
  decide they stay verbatim. (S)

## Tier 2 — Medium-term (weeks–months)

- **Full-collection import** — revisit if Wizards re-exposes the collection in the
  log, or ingest a third-party tracker's CSV export, to replace deck-dump ingestion
  and get true owned quantities. (M)
- **Match / deck win-rate tracking** — a local `parse_matches.py` that reads
  `Player.log` after sessions into `matches.csv`, plus win-rate analytics linked to
  `decks/`. Batch first; a live daemon later. (M–L)
- **Pool scope** — rebuild `card-pool.csv --all` (full Arena) if deck-building
  regularly reaches beyond Standard; today live Scryfall covers the tail. (S)

## Tier 3 — Long-term (months+)

- **Google Sheets round-trip in practice** — wire up `sheets_sync.py` against the
  companion sheet so the CSV and Sheet stay in sync automatically. (M)

## Tier 4 — Future possibilities (exploratory)

- **Meta integration** — pull archetype/meta data to score decks against the
  current field, not just internal consistency.

## The strategic bet

The recurring bottleneck is **data entry** — keeping owned quantities accurate is
manual because Arena no longer logs the collection. The highest-leverage move is
whichever path restores a reliable full-collection import (tracker export or a
future log format). Match tracking is the most exciting *capability* add, but it
only pays off once the collection stays current with low effort.
