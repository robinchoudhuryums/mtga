# Hashaton pile (from deck 53) — analysis (TEMPORARY working doc)

**Status: IN PROGRESS** (started 2026-10-25). Delete once the new deck is drafted and the
findings are folded into its `#: notes:` block. A scratchpad, not a source of truth —
decks/ are.

**Target:** a NEW 100-card Historic Brawl deck (Arena's "Brawl" queue), commander
**Hashaton, Scarab's Fist** (DRC) 1 — `{W}{B}`, identity W/U/B. Working deck id **91**.
**Source list:** the owner's 118-card pile, built out of deck 53 (Sibsig Choir, mono-B
Standard zombies). 37 of the 118 are deck 53's own cards; that is intended (a new deck in a
new format), so the pile is NOT deduplicated against the roster. All 118 are Historic Brawl
legal. 73 are creatures, 43 Zombie-typed. Five names were DFCs stored under the full
`Front // Back` name and were corrected (Sidequest: Hunt the Mark, Liliana Heretical Healer,
Ludevic, Invasion of Amonkhet, Ultimecia).

**The cut is large:** 118 candidates for ~62 nonland slots (99 + commander, ~37 lands).
Roughly half the pile does not make it.

## 1. The decision framework

Hashaton: *"Whenever you discard a creature card, you may pay {2}{U}. If you do, create a
tapped token that's a copy of that card, except it's a 4/4 black Zombie."*

- **R1 — A discarded creature costs {2}{U}, not its printed cost.** The copy keeps every
  ability, so it fires the card's enters trigger and keeps its static and activated text, on
  a 4/4 body. Grade a creature on its TEXT as a 4/4 Zombie. A 7-drop with a huge enters
  trigger (Massacre Wurm) is a 3-mana spell here; a small creature whose value is its body
  is worth about a 4/4 for 3. Printed cost still matters for the copies you CAST.
- **R2 — The engine is DISCARD OUTLETS.** Hashaton does nothing without them. Looting,
  rummaging, cycling, discard as a cost, "each player discards" — count them every batch.
  An outlet that discards a creature on our own terms is worth more than one that makes us
  discard at random or only at end of turn.
- **R3 — Discarding fills the graveyard, so graveyard recursion double-dips.** The card
  is copied by Hashaton AND sits in the yard for embalm / eternalize / reanimation (Scarab
  God, God-Pharaoh's Gift, Liliana's Mastery, Dread Summons…). Embalm and eternalize are
  themselves "a token copy that's a Zombie", so they stack with the same lords.
- **R4 — The copies are ZOMBIES, and ONLY Zombies.** "Except it's a 4/4 black Zombie"
  replaces the card's types, so every Hashaton token counts for Zombie lords and Zombie
  payoffs, whatever the original was, and loses its own tribe. Zombie lords and "Zombies
  you control" effects scale with the engine.
- **R5 — The copy enters TAPPED.** No surprise blocker the turn you make it; haste or
  attack triggers on the copy are a turn late.
- **R6 — Colours are not "white splash".** Hashaton costs `{W}{B}` every time it is cast
  or recast, and EVERY copy costs `{2}{U}`. So: B main, U the repeated activation colour,
  W light but required for the commander. White CARDS can be few; white SOURCES cannot
  be near zero. Decide W on source count, not on card count.
- **R7 — Brawl facts.** Singleton, 100 cards, 1v1 at 25 life, free first mulligan. The
  tier floor is scaled ×1.67: A needs interaction 12 and interaction + card advantage 19.
- **R8 — Legend rule.** A token copy of a legendary creature is legendary. Singleton means
  the original is rarely also out, but a reanimated original plus its Hashaton copy is a
  conflict.
- **R9 — The value of a creature card in this deck has TWO uses**: cast it, or discard it
  for a copy. A creature whose text works poorly as a copy (it wants to be cast — cast
  triggers, "when you cast", flash ambushes, X spells) loses half its value here.

## 2. Standing error list

(none yet)

## 3. Cross-batch observations

(none yet)

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

## 5. Consolidated plan (live)

(after the last batch)
