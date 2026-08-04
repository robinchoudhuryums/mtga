# 55 Mardu (RWB) Mobilize pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS — framework written, batch 1 of 5 next.** Delete once the deck(s)
are drafted and findings folded into their `#: notes:` blocks. A scratchpad, not a
source of truth — decks/ are.

**Source list:** the 131-card RWB pile in
`scratchpad/mardu-pile.txt` (regenerate from the chat dump if lost). **Dedupe note —
deliberate adaptation:** 49 of the 131 already sit in other decks, but this pile aims at
a NEW deck and decks share the collection (a copy is never consumed), so they stay in
scope as candidates; the dedupe pass instead produced the where-they-live map (in git
history of this file's first commit). All 131 get full-text reads, in pile order,
5 batches of ~26.

**Concept (user's brief):** primary deck around **Mobilize** and related wave-token
attack mechanics; 2–3 variants expected. User-spotted clusters: (a) creature-count
ETB/damage payoffs, (b) pingers per creature/spell, (c) cast from exile/graveyard,
(d) multi-spell-per-turn boosts, (e) instant/sorcery focus, (f) wide-for-tall feeders.

## 1. The decision framework

The number that decides a card here is **what it does DURING the combat pulse**, not on
an empty board. Mobilize's shape: *"Whenever this creature attacks, create N tapped and
attacking 1/1 red Warrior tokens. Sacrifice them at the beginning of the next end
step."* Everything follows from that clock:

1. **The board WIDTH is a pulse, not a state.** Creature count peaks between the attack
   trigger and the end step. A payoff that reads count at COMBAT time (attack triggers,
   "deals damage equal to creatures you control" on an attack, Tremors-style ETB pings)
   gets the peak number; a sorcery-speed count effect you cast MAIN PHASE 1 sees the
   trough (yesterday's tokens are gone, this turn's not yet made). Grade every
   count-reader by WHEN it reads.
2. **Every combat is an ETB WAVE.** N tokens enter attacking → "whenever a creature
   enters" triggers fire N times per combat, every combat. This is the engine's real
   output; Impact Tremors-class cards are converters from width-pulse to damage.
3. **Every end step is a DEATH wave.** The tokens sacrifice themselves → "dies" /
   sacrifice-fodder payoffs are fed for free. But a SACRIFICE OUTLET is only value if
   its price beats "they die anyway" — an outlet that costs mana per token competes
   with casting spells.
4. **CADENCE IS THE CARD.** "Whenever ~ attacks" (once/combat) ≠ "whenever a creature
   you control attacks" (N+1 times) ≠ "once per turn". The Mobilize tokens themselves
   ATTACK as they enter, so per-attacker triggers see them; "at the beginning of
   combat" effects do NOT (tokens don't exist yet). Read the exact window.
5. **PRINTED COST IS WHAT WE PAY.** No cheat/recursion engine in the primary — this is
   an attacking deck; curve and Mardu castability decide. Identity ≠ castability
   (G-58): read the printed cost; hybrids and off-color activations are fine. Mardu is
   THREE colors — every 1-drop with double pips is a real cost; note pip demands.
6. **Tokens enter TAPPED AND ATTACKING.** They never block, never convoke/tap-pay
   before combat, and are gone by your next main phase. Anything that wants to TAP
   tokens for value, equip them at sorcery speed, or block with them is misreading the
   engine. (Exception: effects that sacrifice them at instant speed during combat
   beat the end-step clock.)
7. **VARIANT AXES to track, decided at the END, not mid-batch:** (A) count-payoff wide
   [primary], (B) noncombat-damage pingers [primary or its own — Judith wants SPELLS
   too], (C) exile/graveyard-cast spells-matter, (D) multi-spell velocity, (E)
   instant/sorcery focus, (F) wide-feeds-tall. Expect C+D+E to be ONE spells deck and
   F to fold into primary or ride with A; keep counting members per axis.
8. **Tooling notes:** `mobilize` IS keyword-indexed (→ go-wide/aggro) and its reminder
   text classifies as Payoff/engine — the tag layer can see this deck. Warrior-tribal
   references ("Warriors you control") must be searched PLURAL and by effect shape
   (K-13). Next deck id: **55**.

## 2. Standing error list

(nothing yet — populated as misreadings surface)

## 3. Cross-batch observations

- Axis member counts (running): A=0 B=0 C=0 D=0 E=0 F=0 (tallied per batch).

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`, per
AXIS (primary = the Mobilize wave deck; letters = variant axes above).

(batch tables land here)

## 5. Consolidated plan (live)

(built after batch 1; re-ranked every batch)
