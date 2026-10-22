# Szarel pile (deck 89) — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once deck 89 is drafted and the findings are folded into
its `#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Source list:** the owner's 100-line pile (commander Szarel, Genesis Shepherd + 99), saved
at the session scratchpad as `szarel-pile.txt`, full text pulled to `szarel-full.txt`.
Every one of the 99 is inside Szarel's B/R/G identity and Historic Brawl legal. 29 already
sit in other decks (31, 87, 88 and others), which does not matter for a new deck: decks
share the collection.

**Brief from the owner:** "inspired by poison-counters and the Toxic ability and other
things that will surface when analyzing the pile."

## 1. The decision framework

Szarel, Genesis Shepherd — {2}{B}{R}{G} 2/5 flyer: *You may play lands from your
graveyard. Whenever you sacrifice another nontoken permanent during your turn, put a number
of +1/+1 counters equal to Szarel's power on up to one other target creature.*

- **S1 — The trigger reads four words, and each one prunes cards.** *Sacrifice*: an opponent's
  edict does not count, you must be the one sacrificing. *Another nontoken permanent*: a
  Treasure, Clue, Food, Lander, Saproling or Wolf token feeds a cost but fires nothing; a
  land, a creature card, a Saga or an artifact card does. *During your turn*: upkeep
  (Gitrog) and the post-draw Saga sacrifice count, an instant-speed outlet on their turn does
  not. So a card is graded on **how many nontoken sacrifices per turn it adds**, not on
  whether it says "sacrifice".
- **S2 — Lands are the renewable fuel, and that is the deck.** Because Szarel replays lands
  from the graveyard, a land that sacrifices ITSELF is a spell you cast every turn, not a
  one-shot. A fetch is one trigger plus two landfall per land drop; a Memorial is a
  regrowth every turn; a Hidden cave is a Discover 4 every turn; Riveteers Overlook
  sacrifices itself on entry. **The deciding number is self-sacrificing lands plus
  land-sacrifice outlets** — it sets how often Szarel fires without spending a card.
  Extra land drops (Gitrog, Azusa) multiply it.
- **S3 — Szarel's POWER is the second number.** Her trigger gives counters equal to her power
  (2 printed), checked on resolution, and she cannot target herself. What grows her:
  Long Feng (a counter on any creature each time a land or creature hits the graveyard from
  the battlefield — order it above Szarel's trigger and she counts it), Jenova (counters
  equal to Jenova's power, which Szarel's own counters raise — a mutual loop), Vraska, Regal
  Gorgon +2, Ferrafor and Vorinclex doubling. A card that grows Szarel is worth more than one
  that grows itself.
- **S4 — Poison is a real SECOND clock, not the primary plan, and the reason is counted.** The
  pile's poison sources: Fynn (deathtouch combat damage → 2), Necrogen Rotpriest, Venerated
  Rotpriest, Persuasive Interrogators (Clues are TOKENS, so no Szarel trigger), Vraska,
  Betrayal's Sting (proliferate; −9), Infectious Bite, Viral Spawning, Lukka's Beast, Mirrex's
  Mites, Noxious Assault, Virulent Silencer — five cards that poison more than once. Szarel
  never poisons on her own. **What makes poison live here is a bridge, not a poison count**:
  Szarel's counters + Bushmaster (every countered creature has deathtouch) + Fynn (every
  deathtouch hit is 2 poison) turns the counters engine into a poison engine, and Vorinclex
  doubles poison (4 per Fynn hit). In Brawl the opponent has 25 life and still dies at 10
  poison, so the poison clock is relatively faster than in 60-card play.
- **S5 — A poison card must do a second job to make the 100.** Proliferate also grows +1/+1
  counters and loyalty (counts as counters-engine); a deathtouch body also blocks and carries
  Fynn's poison. A card whose only output is a poison counter is △ unless it is a finisher.
  **The finisher found while reading: Vorinclex + Vraska, Betrayal's Sting** — Vraska enters
  with 12 loyalty under Vorinclex, −9 immediately, and the 9 poison is doubled to 18. A
  one-turn win from zero poison with two cards that are each good alone.
- **S6 — Deathtouch needs a way through.** ~25 pile cards have or grant deathtouch; a blocked
  deathtoucher kills a creature but deals no player damage. Evasion and trample sources
  (Szarel's flying, Kura, Rhonas's pump, Hunter's Axe, Vraska, Regal Gorgon's menace,
  Rattleback's menace, Escape Tunnel's unblockable) decide how many hits Fynn converts.
- **S7 — Format.** Historic Brawl: 100 singleton, BRG identity, 25 life, free first mulligan,
  36–40 lands. The tier floor scales ×1.67: A needs interaction 12 and interaction + card
  advantage 19.
- **S8 — Red is a splash for the commander.** Of the 99 only Kraven Proud Predator, Absorbing
  Man and Titania, Rhino, Abomination, Lukka, Roxanne, Phylath, Atarka, Omnath, Slimefoot and
  Squee and Hidetsugu's ability need red. The deck is Golgari with Szarel's {R}; the manabase
  must still hit R on turn 5, which fetches (S2) do for free.
- **S9 — G-42 conflicts to check on every card.** This deck NEEDS land cards in its own
  graveyard. Graveyard exile is a conflict only if it can hit ours; symmetric small-permanent
  wipes (Culling Ritual) kill our own Fynn and Bushmaster; Sarulf's exile wipe hits our own
  countered creatures.
- **S10 — Structurally invisible here (G-67/G-76).** No tool counts nontoken sacrifices per
  turn, lands-from-graveyard recursion, or Szarel's power; `targets` sees sacrifice-cost gates
  but not a commander's trigger. Proliferate is not a role. These are hand counts in this doc.

## 2. Standing error list

- (none yet)

## 3. Cross-batch observations

- (filled per batch)

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

## 5. Consolidated plan (live)

- (after batch 3)
