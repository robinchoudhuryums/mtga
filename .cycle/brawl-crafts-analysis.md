# Brawl craft triage — unowned mythics and rares (TEMPORARY working doc)

**Status: IN PROGRESS — deck 93 done; 88, 56-historic-brawl, 96, 92, 91, 98, 89 to go.**
Delete once every deck is done and the owner's picks have landed (as swaps, or as notes in each
deck's `#: notes:`). A scratchpad, not a source of truth — decks/ are.

## Method (the same for every deck)

- **Scope:** the Brawl decks that are not fully owned (`deck.py wildcards`, 2026-11-20):
  93 (9M 12R), 88 (13M 9R), 56-historic-brawl (7M 17R), 96 (18M 10R), 92 (16M 18R),
  91 (18M 15R), 98 (15M 15R), 89 (21M 12R). Smallest gap first.
- **What counts as a replacement:** an OWNED card of any rarity, or an UNOWNED card of a LOWER
  rarity than the craft it replaces (a rare for a mythic; an uncommon or common for a rare).
  It must fit the commander's colour identity and be legal in the deck's format. It must also
  do the same JOB in this deck (same trigger shape, same engine), not merely share a theme.
- **Ranking:** craft first what has NO acceptable replacement and carries the deck's engine.
  Craft last (or never) what an owned card covers as well or better.
- **Search:** `cands.py` effect-shape sweeps (pool regex, identity- and format-filtered, owned
  first), then `deck.py screen <id>` on the chosen replacements. Ownership counts are lower
  bounds (G-10); a card listed as unowned may be owned.
- Proposals only. Swaps go through `/apply-changes` once the owner picks.

## Deck 93 — Two Heavens (Isshin, Mardu attack triggers) — 9M 12R missing

Engine: Isshin doubles attack-caused triggers. Mobilize/attack tokens die every end step,
feeding death payoffs. A discard sub-engine (Smellerbee, Living Laser, Crucias, Celes).
34 legendary creatures (Djeru and Hazoret's hit rate). 14 outlaws, but 6 of those are
unowned crafts below, so the outlaw sub-theme shrinks if they are replaced.

### Craft first — no acceptable replacement found

| # | Card | R | Why it cannot be replaced | Nearest fallback |
|---|------|---|---------------------------|------------------|
| 1 | Mishra, Claimed by Gix | M | "Whenever you attack, drain X = attackers", doubled by Isshin: the deck's biggest win condition in a go-wide board. Nothing owned or cheaper scales with attacker count. | none (Marshal of the Lost U pumps one creature) |
| 2 | Hellrider | R | 1 damage per attacking creature, each trigger doubled. No owned or uncommon card pings per attacker. | none |
| 3 | Dictate of Erebos | R | Every end-step mobilize sacrifice becomes an opponent edict. No owned or cheaper "each opponent sacrifices" death trigger exists in the pool. | none |
| 4 | Smellerbee, Rebel Fighter | R | The haste half is replaceable; the attack-scaled hand refill (doubled) is not. | Samut, Hazoret's Champion (owned R) — haste only |
| 5 | Djeru and Hazoret | R | Attack trigger casts a free legendary; 34 legends make the hit rate high. | Cosmic Cube (owned M) — whenever you attack, free spell from top six; see #13 |
| 6 | Raiyuu, Storm's Edge | R | Protected signature: a repeatable extra combat (two under Isshin). | Full Throttle (owned R) — two extra combats, but one-shot |
| 7 | Far Fortune, End Boss | R | Whenever-you-attack ping (doubled) plus max-speed +1 damage. | Screeching Soulbreaker (owned C) — much weaker |

### Replaceable — an owned card covers the job

| # | Craft | R | Replacement (owned) | Verdict |
|---|-------|---|---------------------|---------|
| 8 | Zurgo Stormrender | M | **Venerated Stormsinger** (U) | Same shape, mobilize plus a death payoff. Stormsinger drains on EVERY creature death, which pays more in this deck. Better or equal. |
| 9 | Vraan, Executioner Thane | R | **Funeral Room // Awakening Hall** (M) | Vraan drains 2 once a turn; Funeral Room drains 1 per death, so 3+ deaths a turn beats it. The back half is a mass reanimation. Better. |
| 10 | Outlaws' Merriment | M | **Warren Warleader** (M) | Merriment's upkeep token is not doubled; Warleader's whenever-you-attack token or pump is. Better here. |
| 11 | Mardu Thunderkite | M | **Dragonback Lancer** (C) | Flying mobilize body; loses the perpetual keyword grant. Reasonable exchange. |
| 12 | Professional Face-Breaker | R | **Captain Lannery Storm** (R) | Treasure on attack (doubled) instead of on combat damage; haste. Loses the impulse draw. Reasonable exchange. |
| 13 | Phyrexian Dragon Engine | R | **Cosmic Cube** (M) | The card it replaced in the 2026-10-26 package; attack trigger doubled. The Mishra meld is optional (notes say so). Better as card advantage. |
| 14 | Celes, Rune Knight | M | **Captain James T. Kirk** (M) | Enters-or-attacks loot, token or pump, doubled on attack. Celes' counters half rarely fires (few graveyard entries). Better here. |
| 15 | Crucias, Titan of the Waves | M | **Cool but Rude** (R) | Attack-triggered loot (doubled); level 2 adds 2 damage per discard. Feeds the discard engine harder than Crucias. Better. |
| 16 | Living Laser | R | **Monument to Endurance** (R) | Discard payoff that draws, makes Treasure or drains 3. Loses the copy-attackers burst. Reasonable exchange; Magmakin Artillerist (owned C) is a second option. |
| 17 | Rakdos, the Muscle | M | **Garna, Bloodfist of Keld** (U) | Rakdos exiles cards equal to the sacrificed creature's MV, so mobilize tokens (MV 0) exile nothing. Garna draws or pings on every death. Better in this deck; loses the 6/5 flier. |
| 18 | Olivia, Opulent Outlaw | M | **Olivia, Crimson Bride** (M) | Flying, haste, reanimates tapped and attacking on attack (doubled = two returns). Better. |
| 19 | Zagras, Thief of Heartbeats | R | **Drakuseth, Maw of Flames** (R) | Zagras gives team deathtouch; Drakuseth's attack trigger is 10 damage split, doubled. Different job (removal and reach instead of combat deterrent). Reasonable exchange. |
| 20 | Laughing Jasper Flint | R | **Daredevil, Man Without Fear** (R) | Jasper scales with outlaws, and outlaws fall if #17–19 are taken. Daredevil's whenever-you-attack impulse is doubled. Reasonable exchange. |
| 21 | Angrath, the Flame-Chained | M | **Involuntary Employment** (C) | Keeps the threaten-and-sacrifice line (Akul, sac outlets); loses the +1 discard-and-drain. Weakest exchange in the list; nothing owned matches a planeswalker here. |

**If every replacement is taken:** 1 mythic and 6 rares left to craft (Mishra plus #2–7), down
from 9M 12R. Without the fallbacks for #4–7, it is 1M 3R (Mishra, Hellrider, Dictate of Erebos).

`deck.py screen 93` on the replacement set: KEY for Dragonback Lancer, Venerated Stormsinger and
Warren Warleader; role-player for the rest except Captain James T. Kirk and Cosmic Cube
(tangential — their value is the doubled attack trigger, which theme overlap cannot see).
