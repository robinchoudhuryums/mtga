# Brawl craft triage — unowned mythics and rares (TEMPORARY working doc)

**Status: IN PROGRESS — decks 93 and 88 done; 56-historic-brawl, 96, 92, 91, 98, 89 to go.**
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

## Deck 88 — Full Throttle (Samut, the Driving Force, Naya power ramp) — 13M 9R missing

Engine: Samut gives other creatures +X/+0 and discounts noncreature spells by X (speed, max 4),
so power gates (4+, 7+) are easier than printed power suggests. Twelve mana creatures and land
ramp, a landfall layer, and a Gamma counters layer (8 Gamma). Thin sub-themes: earthbend (4
cards, two of them the unowned Tophs), Elves 4, Wolves 2, Bears 2, one noncreature artifact.
`screen` grades most replacements "tangential" here; that is the theme model, not a verdict:
their value is the power-4+ and landfall reads it does not score.

### Craft first — no acceptable replacement found

| # | Card | R | Why | Nearest fallback |
|---|------|---|-----|------------------|
| 1 | Samut, the Driving Force | R | The commander. Replacing it is a different deck. | none |
| 2 | Unnatural Growth | R | Protected. Doubles the whole team's power and toughness every combat; stacks with Samut's +X. Nothing owned or cheaper is team-wide and permanent. | Mightform Harmonizer (owned R) — one creature per landfall |
| 3 | Tifa, Martial Artist | M | Protected. Untap and an extra combat whenever a 7-power creature connects, which Samut makes routine. | Full Throttle (owned R) — two extra combats, one-shot |
| 4 | Worldweave | M | A 3-mana engine: a land onto the battlefield for every creature cast, feeding ramp and the landfall layer. | Earthbender Ascension (owned R) — one land plus landfall counters |
| 5 | Emperor Apatzec Intli IV | M | Protected. Every big creature gets haste, life and a seeked creature. | Hit It! (owned R) — team haste and a land; loses the life and the card |
| 6 | Ravenous Tyrannosaurus | M | A repeatable bite on every attack, at Samut-boosted power, with excess to the face. | Hunter's Talent (owned U) — one bite on entry |

### Replaceable — an owned card covers the job

| # | Craft | R | Replacement (owned) | Verdict |
|---|-------|---|---------------------|---------|
| 7 | Nylea, God of the Hunt | M | **Garruk's Uprising** (U) | Team trample, plus a card on entry. Nylea is rarely a creature here. Better or equal. |
| 8 | Zacama, Primal Calamity | M | **Craterhoof Behemoth** (M) | A 9-drop removal engine for an 8-drop that ends the game. Better as a finisher; loses repeatable removal. |
| 9 | Nyxbloom Ancient | M | **Caged Sun** (M) | Doubles green mana from lands and pumps green creatures. Nyxbloom triples the dorks too, so it is a reasonable exchange, not an upgrade. |
| 10 | Voja, Jaws of the Conclave | M | **Vaultborn Tyrant** (M) | Voja reads 4 Elves and 2 Wolves. Vaultborn draws and gains 3 for every power-4 creature entering, which Samut makes most of them. Better here. |
| 11 | Samut, the Tested | M | **Vivien, Arkbow Ranger** (M) | Counters plus trample, a bite (−3), and a creature tutor. Better here. |
| 12 | Arlinn Kord | M | **Garruk, Curse Breaker** (M) | Draws on every power-4 creature entering, makes 4/4s, untaps lands. Better here. |
| 13 | Omnath, Locus of Rage | M | **Rampaging Baloths** (R) | Landfall 4/4s for 6 instead of 5/5s for 7. Loses the Elemental death burn. Reasonable exchange. |
| 14 | Rhys the Redeemed | M | **Mole Man, Moloid Master** (R) | Rhys's Elf half feeds Voja (#10); its copy ability costs 6 a turn. Mole Man makes a token per landfall and replays lands from the graveyard. Reasonable exchange. |
| 15 | Back-Alley Gardener | M | **Tireless Provisioner** (U) | Gardener puts a land in once a turn when creatures enter; Provisioner makes Treasure on landfall. Weaker ramp. Primeval Herald (unowned U) is closer: a land on entry and on attack. |
| 16 | Toph, Greatest Earthbender | R | **Bumi, Unleashed** (M) | Toph's double strike reads land creatures, and only 4 cards earthbend. Bumi earthbends 4 and takes an extra combat. Better. |
| 17 | Toph, the First Metalbender | R | **Earthbender Ascension** (R) | The artifacts-are-lands clause has one artifact to read. Ascension earthbends 2, fetches a land, and grows a creature on landfall. Better. |
| 18 | Hulk, Strongest There Is | R | **Branching Evolution** (R) | Hulk doubles Gamma counters only; Branching doubles every +1/+1 counter the team gets. Better, but the Gamma layer loses a body. |
| 19 | Gamma Grotesque | R | **Outcaster Trailblazer** (R) | Grotesque draws per countered creature after a 6-mana power-up. Trailblazer draws per power-4 creature entering and taps for mana. Reasonable exchange. |
| 20 | Abomination, Irradiated Brute | R | **Bristly Bill, Spine Sower** (M) | Landfall counters plus a counter doubler, on the axis the deck actually feeds. Better. |
| 21 | Ayula, Queen Among Bears | R | **Felling Blow** (U) | Two Bears in the deck. Felling Blow is a counter plus a bite. Better. |
| 22 | Master's Guidance | R | **Bitter Work** (U) | PROTECTED, so the owner's call. Bitter Work draws when a power-4 creature attacks, and earthbends 4 once. Colossal Majesty (unowned U) is the closest copy: an upkeep draw at power 4. |

**If every replacement is taken:** 4 mythics and 2 rares to craft (#1–6), down from 13M 9R.
With the fallbacks for #3–6, only Samut and Unnatural Growth remain (2 rares).
