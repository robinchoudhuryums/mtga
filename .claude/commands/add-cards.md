Find homes across your decks for cards you already own.

Input: card names (or an Arena export) in $ARGUMENTS or the user's latest message.

**If the cards are not catalogued yet, run `/ingest` instead — it does this pass
automatically at the end.** This command used to catalog AND place, duplicating
`/ingest`'s Stage 1 recipe; the two drifted (this file kept its own copy of the
derived-data rebuild chain), and the placing half — the part that actually decides
anything — was the optional one. Cataloging now has a single definition in `/ingest`,
and this is the fit pass on its own, for when you want to re-run placement over cards
you already have:

- after a deck retune changed what that deck wants,
- after `tag_synergies` gained a theme, which can change every fit,
- for a card you have owned for months and never found a slot for,
- for a specific card you are thinking about, without ingesting anything.

For a whole new *deck*, use `/add-deck` (ingest a pasted list) or `/draft-deck`
(build one from scratch).

This skill **orchestrates the existing scripts** — it never re-implements them, so it
cannot drift from their behaviour. Read CLAUDE.md's Common Gotchas first.

## Stage 0 — Confirm the cards are owned

`python3 scripts/card.py "<name>"` reports owned quantity. If a card is not in the
library, stop and route to `/ingest` — placing a card you do not own is a craft
recommendation, which is `/add-wishlist`'s job, not this one.

## Stage 1 — Read each card, then place it (full text, always)

For **every** card, in this order — never grade from a tag or a role label
(CLAUDE.md's recurring mis-grade):

1. `python3 scripts/card.py "<name>"` — the COMPLETE oracle text + mana cost +
   **format legality** + owned qty + which decks already run it. Heed a
   `⚠ unindexed mechanic` line: that keyword is not in the synergy map, so grade its
   effect from the text, not the tags. **A card that isn't Standard-legal is not a
   Standard candidate** — say so and stop suggesting it there (the
   Champion-of-Rhonas / Chord-of-Calling mistake).
2. `python3 scripts/deck.py suggest-homes "<name>"` — every deck the card is
   *castable* in and shares a *central* theme with, each row tagged with a
   **strength** label (**KEY** — fills an interaction/card-advantage gap or shares
   the deck's signature theme; **role-player** — a secondary central theme;
   **tangential** — generic overlap only) and a single weakest-nonland **cut
   candidate**. Rows are sorted strongest-fit first. Costs ~2s per card.
3. For each real fit, grade it from the Stage-1.1 text against **this deck's
   engine** (a "downside" clause is often an upside in the matching deck — see
   CLAUDE.md's swap gotcha) and classify it:
   - **key upgrade** — a KEY fit that beats a current card on a real axis; name
     the cut candidate and confirm it from full text (`deck.py cuts <id>` /
     `card.py` on the cut).
   - **sidegrade** — lateral (~85% of something already run); name it to say
     *skip* unless the user wants it.
   - **different-flavor** — not stronger but changes how the deck plays; offer it
     as a creative option (honor the Player Profile).
4. **Copies are fungible — slot a card into ALL decks it earns, not one.** If a
   card is a key upgrade in three decks, propose it in all three; never tell the
   user to "pick a home" or "split copies" (CLAUDE.md: one owned copy plays in
   every deck at once).

## Stage 2 — Report

- **Per card:** the fit rows as `card → deck (strength) — cut candidate — key
  upgrade / sidegrade / different-flavor`, with the operative oracle clause quoted
  for each recommended swap.
- **No-home cards:** stated plainly (owned but nothing fits yet).
- Do NOT apply the swaps here — this skill *recommends*; applying is
  `/apply-changes` (which the user confirms). Honor the standing "propose, don't
  apply until confirmed" rule.

Nothing is written by this command, so there is no commit step. If the user confirms
a swap, `/apply-changes` performs it and carries the shared verify + commit tail.
