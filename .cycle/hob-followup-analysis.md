# HOB follow-up pile (27 cards) vs decks 69 / 69a / 69b — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into the
deck files' `#: notes:`. A scratchpad, not a source of truth — decks/ are.

**Source list:** 27 owner-proposed cards. None already in 69 or 69a; Through the Forest
Gate is already in 69b (so evaluated for 69 / 69a only).

## 1. The decision framework

**F1 — CASTABILITY IS NEARLY FREE HERE, WITH ONE EXCEPTION.** 26 of 27 are mono-green,
so they are castable in all three decks. **Tom, Bert, and William is BG → NOT castable in
mono-green 69a** (`screen` confirms). That is the only hard colour gate in the pile.

**F2 — DECK 69 GRADES ON THE GATE: does the card PROVIDE power-4, or WAIT for it?**
This is the Wargling lesson generalised. A provider is worth more than a consumer of
equal rate, and HASTE / FLASH are worth a premium because the gate is checked at ATTACK
time — a hasty power-4 body turns Ferocious on the turn it lands.

**F3 — DECK 69's LOUDEST UNANSWERED WARNING IS "counters: 19 enablers, NO PAYOFF".**
A counter DOUBLER is the payoff, and it multiplies an axis the deck already has more of
than any other. `screen` scores The Earth Crystal and Loading Zone as `✱ multiplier —
doubles counters (17 feeders here)`. This is the single highest-leverage line in the pile.

**F4 — DECK 69a GRADES ON TWO NUMBERS: lands in play, and permanent cards in the
graveyard.** It self-mills hard, so a cost reducer keyed to the graveyard is cheap here
and nowhere else. Its weakest axis is card advantage 2. Curve is already 3.44 — a 7+ drop
must be a finisher, not filler.

**F5 — DECK 69b GRADES ON COLOUR, NOT POWER.** W 11 / B 14 / G 20 sources against
{W}{W} and {B}{B} costs. Anything that makes mana any-colour is worth more than its own
body here, and anything costing {G}{G}{G} is worse than it looks (Overrun).
Weakest axis on the family: card advantage 1.

**F6 — ROTATION.** Only two of the 27 rotate ~2027: **Overlord of the Hauntwoods** and
**Rise of the Varmints**. The rest are 2028-29.

**F7 — WHAT IS STRUCTURALLY INVISIBLE.** `cuts`/`suggest` cannot see a doubler's worth
(G-40 — routed through `suggest-homes`' multiplier primitive only), cannot read a
graveyard-scaled cost reduction, and score every card in isolation (G-61). Every verdict
below that leans on "the rest of the deck" is a human read, not a tool output.

## 2. Standing error list
- Do not grade a doubler by its own text (it does nothing alone) — count its feeders.
- Do not read `screen`'s KEY as a verdict; it saturated at 86% on the last HOB batch.
- Do not dismiss a landfall card from 69 by category — 69 runs Beorn's Hospitality and
  Dancing from Dark to Dawn, so it has real landfall payoffs (the G-42-in-reverse trap).

## 3. Cross-batch observations
- The pile contains **three counter doublers** (Doubling Season, The Earth Crystal,
  Loading Zone). They are not interchangeable: Earth Crystal is cheapest AND cuts {1} off
  ~85%-green deck 69's spells; Doubling Season also doubles TOKENS (which matters in 69b's
  token engine, 10 enablers); Loading Zone has Warp {G} for a turn-1 deploy.
- Deck 69a is the only home for graveyard-scaled costs (Diamond Weapon) and land-sacrifice
  value (Planar Engineering — the sacrificed lands feed Lumra/Titan/Analyst, which is why
  it is better here than in deck 50a, which cut it).
- **Variant signal: none.** Every card slots into an existing family member; no coherent
  cluster is being rejected for the same reason.
