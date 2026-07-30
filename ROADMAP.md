# Roadmap — MTG Arena Card Library

Grounded in the project's current state and deferred ideas. Regenerate with
`/roadmap`. Effort: S ≈ <2h, M ≈ ½–2 days, L ≈ 3+ days (one dev + Claude Code).

## Deck ideas (measured, not speculative)

- **Mono-U/colorless AFFINITY — the one third-variant shape that has a payoff.** Two
  other candidates were swept and rejected first, both recorded in
  `decks/26-iron-forge/26a-virulent.txt`'s flex block: an artifact-TOKEN deck (120
  makers but the sacrifice-drain win-con is ONE card, which triggers off the
  opponent) and ROBOT tribal (53 Robots, 27 owned, but ZERO Robot-count payoffs in
  all of Standard, any colour — there is no Robot lord). Affinity is different
  because the payoff genuinely exists:
  - **16 cards scale with artifact COUNT** and **7 carry affinity/improvise**, so
    the board itself pays for the spells. Key pieces: Krang Master Mind {6}{U}{U}
    (R, affinity, draws you to four, +1/+0 per artifact), Gearseeker Serpent
    {5}{U}{U} (**Common**), Valkyrie Aerial Unit, Memory Guardian, Cerebral
    Download, Edgar King of Figaro, Braided Net (**owned**), Simulacrum Synthesizer,
    plus the owned improvise cards Ironheart and Arc Reactor.
  - **Chrome Dome {2} (R) is a real artifact-creature LORD** ("other artifact
    creatures you control get +1/+0") — one of only three such cards, alongside
    Krang and Iron Spider.
  - **49 owned artifacts at MV<=2 in mono-U/colorless** to turn affinity on.
  - **It is distinct from deck 26 in the resource it spends.** 26 ramps with MANA
    (lands, Arc Reactor, Tony Stark's free drop, Tannuk's warp) to hard-cast bombs;
    affinity ramps with PERMANENTS already on board. And it is mono-U/colorless, so
    it pays none of the two-colour manabase tax both existing decks carry (26 has
    six tapped lands and an {R}{R} card at 69.6%).
  - **The honest structural limit:** a search for "whenever an artifact creature
    enters / attacks / dies" returns ZERO cards in these colours, so there is no
    aristocrats or value-loop engine. The deck wins by combat with oversized cheap
    bodies, nothing subtler.
  - Minimum viable craft bill: Gearseeker Serpent (C), Memory Guardian (U), Valkyrie
    Aerial Unit (U), Cerebral Download (U), then Chrome Dome (R) and Krang Master
    Mind (R) as the two Rares that make it a deck rather than a pile. (M)

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
