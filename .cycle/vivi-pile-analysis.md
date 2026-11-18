# Vivi Ornitier pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS (2026-11-18).** Building a NEW Izzet (UR) Historic Brawl deck around Vivi
Ornitier from the owner's pile. Delete once the deck is drafted and the findings are folded into
its `#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Source list:** the owner's paste (123 cards: Vivi + 107 distinct nonbasic + 11 basics; the paste
holds 3 Stark Industries and 4 Swiftwater Cliffs, of which Brawl's singleton rule allows one each).
All 107 are Historic Brawl legal and castable in UR. 97 nonland candidates + 9 nonbasic lands.
No dedupe against other decks: cards are shared across decks in Arena (CLAUDE.md), so a card
another deck runs is still a candidate here. Ownership is information only (Player Profile);
40 of the 107 are unowned.

**Builder project:** deferred until a first draft deck file exists (`builder.py new` needs a deck);
then `builder.py new vivi --decks <id>` per `/draft-deck` Stage 6.

**Slot budget:** 100 cards = Vivi + 99. At ~35 lands (9 nonbasic + ~26 basics) that leaves ~64
spell slots, so ~33 of the 97 nonland candidates are cut. Lands are revisited once the spell
count settles (Vivi is a mana source, which argues for the low end of the 36–40 Brawl norm).

## 1. The decision framework

Vivi Ornitier {1}{U}{R}, 0/3: "{0}: Add X mana in any combination of {U} and/or {R}, where X is
Vivi's power. Activate only during your turn and only once each turn. / Whenever you cast a
noncreature spell, put a +1/+1 counter on Vivi and it deals 1 damage to each opponent."

- **R1 — The number is NONCREATURE SPELLS CAST.** Each one is +1 power (= +1 mana from Vivi's
  next activation) and 1 damage to the opponent. A creature spell does neither. Grade a creature
  on whether it EARNS the slot a noncreature spell would have filled.
- **R2 — Vivi's mana is ONCE per turn, on YOUR turn, and grows within the turn.** Cast the cheap
  noncreature spells first, then tap Vivi for the big payoff. So: cheap spells (MV ≤ 2) are the
  fuel; X spells and expensive sorceries are the sink, and their printed cost overstates what
  they cost here from mid-game on. Instants held for the opponent's turn cannot use Vivi mana.
- **R3 — CAST vs COPY.** Vivi triggers on CAST. A copy that is merely created (Thousand-Year
  Storm, most "copy target spell") does not trigger her; "cast a copy" (Arcane Bombardment) and
  casting from graveyard/exile (flashback, harmonize, Dreadhorde Arcanist) do. Magecraft ("cast
  or copy") triggers on both. Read each copy card for which it is.
- **R4 — Vivi is the engine and a removal magnet.** Protection for her (counters, hexproof,
  blink) and card flow that keeps the spell count up are worth more than in a generic Izzet pile.
  Commander tax makes a second cast costly.
- **R5 — 1v1 at 25 life.** Vivi's ping plus the burn/noncombat-damage payoffs (Electro, Stormcatch
  Mentor-type prowess, Firebending) are a real clock; count total reach, not just creatures.
- **R6 — The interaction floor at 100 cards** (CLAUDE.md, per-60 scaling): A needs interaction 12
  and interaction + card advantage 19. Counterspells and burn both count; bounce is tempo, not
  interaction (G-25).
- **R7 — A spell that makes OTHER spells (tokens that are spells, Clues, cast-from-exile)** is
  worth more than its face: count what it adds to R1.

## 2. Standing error list
(none yet)

## 3. Cross-batch observations
(none yet)

## 4. Running verdicts
Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

## 5. Consolidated plan (live)
(after batch 1)
