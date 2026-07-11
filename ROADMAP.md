# Roadmap — MTG Arena Card Library

Grounded in the project's current state and deferred ideas. Regenerate with
`/roadmap`. Effort: S ≈ <2h, M ≈ ½–2 days, L ≈ 3+ days (one dev + Claude Code).

## Tier 1 — Short-term (days–weeks)

- **Lock Atlantis Attacks 18a as the primary build** once crafted — retire or
  rename base `18` so the roster reflects the intended list. (S)
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

- **Local editing app** — a small Flask/FastAPI UI for in-browser collection and
  deck editing that writes back to the CSVs (Tier 2 of the original UI plan). (L)
- **Google Sheets round-trip in practice** — wire up `sheets_sync.py` against the
  companion sheet so the CSV and Sheet stay in sync automatically. (M)

## Tier 4 — Future possibilities (exploratory)

- **Deck suggestions from the collection** — given owned cards + synergy tags,
  propose brews or upgrades automatically (extends `pool.py` + `tribes`).
- **Wildcard optimization across the roster** — plan crafting to maximize decks
  unlocked per wildcard, using `card-pool.csv` rarity + deck craft lists.
- **Meta integration** — pull archetype/meta data to score decks against the
  current field, not just internal consistency.

## The strategic bet

The recurring bottleneck is **data entry** — keeping owned quantities accurate is
manual because Arena no longer logs the collection. The highest-leverage move is
whichever path restores a reliable full-collection import (tracker export or a
future log format). Match tracking is the most exciting *capability* add, but it
only pays off once the collection stays current with low effort.
