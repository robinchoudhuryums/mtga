# Brawl craft triage — unowned mythics and rares (TEMPORARY working doc)

**Status: ALL EIGHT DECKS DONE (2026-11-20). The roster-wide craft order is the Builder board `builds/brawl-crafts`. Awaiting owner picks.**
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

## Deck 56-historic-brawl — One Fell Swoop (Feather, the Redeemed, Boros Voltron) — 7M 17R missing

Engine: Feather returns every instant or sorcery that TARGETS your own creature to hand at end
step, so a self-targeting spell is a spell every turn. Equipment is the second layer, and the
plan is one protected body. **Trap:** Sword of Wealth and Power (owned) gives protection from
instants and sorceries, which blocks your OWN Feather spells on that body — not a replacement here.

### Craft first — no acceptable replacement found

| # | Card | R | Why | Nearest fallback |
|---|------|---|-----|------------------|
| 1 | Feather, the Redeemed | R | The commander. | none |
| 2 | Seize the Day | M | Targets your creature, so Feather returns it: an extra combat EVERY turn. No owned extra-combat spell targets. | Full Throttle (owned R) — one-shot, not returned |
| 3 | Embercleave | M | Protected. Flash, double strike and trample, cheaper while attacking. | Genji Glove (owned R) — double strike plus an extra combat; no flash or trample |
| 4 | Akiri, Fearless Voyager | R | A card every attack with an equipped creature, and {W} indestructible. The deck's repeatable card draw. | Buster Sword (owned M) — a card per hit, needs to connect |
| 5 | Raiyuu, Storm's Edge | R | The Voltron body attacks alone; Raiyuu untaps it and adds a combat. | Genji Glove (owned R), if not used for #3 |
| 6 | Fiery Confluence | R | Sweeps 1/1s, deals 6 to the face, or kills artifacts, in one card. Also wanted by deck 92. | none owned at that flexibility |

### Replaceable — an owned card covers the job

| # | Craft | R | Replacement (owned) | Verdict |
|---|-------|---|---------------------|---------|
| 7 | Stoneforge Mystic | R | **Cloud, Midgar Mercenary** (M) | Tutors any Equipment and doubles the triggers of the equipment on it. Better. |
| 8 | Akroma's Will | M | **Divine Resilience** (U) | Targets your creature, so Feather returns it: repeatable indestructible (kicked = the team). Loses the double-strike mode. Better as repeatable protection. |
| 9 | Sword of Forge and Frontier | M | **Buster Sword** (M) | +3/+2, a card and a free spell per hit. Better or equal. |
| 10 | Kaldra Compleat | M | **Orcrist, Goblin-cleaver** (M) | Kaldra is a 7-mana, 7-equip finisher. Orcrist gives +2/+2 and trample for 3. Reasonable exchange; Meteoric Mace (owned U) is the bigger hit. |
| 11 | Mishra's Command | R | **HULK SMASH!** (C) | Both bite through your own creature, so Feather returns either. Loses X-scaling and the pump mode. Reasonable exchange. |
| 12 | Teyo, Aegis Adept | M | **Nahiri, Heir of the Ancients** (M) | Teyo's main job is Erratic Cyclops (#13). Nahiri makes bodies, attaches equipment, digs for it and removes. Better here. |
| 13 | Erratic Cyclops | R | **Crackling Cyclops** (C) | +3/+0 per noncreature spell instead of +MV. Feather recasts cheap spells, where +3 is more. Equal or better. |
| 14 | Kirk, Enterprising Captain | M | **Chandra, Torch of Defiance** (M) | Impulse every turn, ramp, or 4 to a creature. Better. |
| 15 | Éowyn, Fearless Knight | R | **Stasis Snare** (U) | Flash exile of any creature, not only a bigger one. Loses the haste body. Equal. |
| 16 | Raubahn, Bull of Ala Mhigo | R | **Frodo, Determined Hero** (R) | Attaches a 2–3 MV Equipment on entry and every attack, and takes no damage on your turn. Equal. |
| 17 | Shadowspear | R | **Meteoric Mace** (U) | Trample plus +4/+0, with cascade. Loses the 1-mana lifelink. Reasonable exchange. |
| 18 | Odric, Lunarch Marshal | R | **Captain America, Liberator** (R) | Different job: Odric shares the body's keywords with a team this deck does not build. Captain America fetches and puts an Equipment in. Better here. |
| 19 | Jor Kadeen, First Goldwarden | R | **Firion, Wild Rose Warrior** (R) | Jor Kadeen scales with equipped creatures (one, in a Voltron deck). Firion gives haste to equipped creatures and copies each Equipment. Better here. |
| 20 | Zada, Hedron Grinder | R | **Aziza, Mage Tower Captain** (R) | Zada copies a self-targeting spell per creature, a go-wide read. Aziza copies a spell for three tapped creatures. Both are weak in Voltron; consider cutting the slot entirely. |
| 21 | Krenko, Tin Street Kingpin | R | **Solitary Cell** (R) | No owned card makes tokens on attack in Boros. Krenko is a power-scaling carrier; Solitary Cell is a different job (removal). Weak exchange. |
| 22 | Esper Sentinel | R | **Banishing Light** (U) | A 1-drop tax is low impact in Brawl. A removal slot does more. Better. |
| 23 | Battlefield Forge | R | **Asgardian Citadel** (C) | Same colours, enters tapped. A tempo cost; craft these late, not never. |
| 24 | Needleverge Pathway | R | **Rabanastre, Royal City** (C) | As #23. |

**If every replacement is taken:** 2 mythics and 4 rares to craft (#1–6), down from 7M 17R.
With the fallbacks for #3–5, 1 mythic and 2 rares (Feather, Seize the Day, Fiery Confluence).

## Deck 96 — Drowned Library (Glarb, Calamity's Augur, Sultai draw-to-mill) — 18M 10R missing

Engine: every card drawn mills the opponent (two Sphinx's Tutelages, owned), multiplied by
Bruvac and The Water Crystal and repeated by Fraying Sanity; Glarb casts MV 4+ cards off the
top. 29 creatures (Phenax's count). The owned pool has many planeswalkers but almost no MILL
multipliers — that is where the crafts concentrate.

### Craft first — no acceptable replacement found

| # | Card | R | Why | Nearest fallback |
|---|------|---|-----|------------------|
| 1 | Bruvac the Grandiloquent | M | Protected. Doubles every mill; the deck's clock is built on it. | none |
| 2 | The Water Crystal | R | +4 on every mill instance, and blue spells cost 1 less. | none |
| 3 | Fraying Sanity | R | Repeats each turn's total at end step: a second doubler. | none |
| 4 | Jace, Memory Adept | M | Protected. Mills 10 a turn, or draws and mills. | none |
| 5 | Ashiok, Nightmare Muse | M | Protected. A token per turn that exiles two from their library on every attack or block. | none |
| 6 | Phenax, God of Deception | M | Every creature taps to mill its toughness; with 29 creatures (and Bruvac's 4 toughness) this is a mill engine on its own. | none |
| 7 | Terisian Mindbreaker | R | Half their library on attack, and Glarb casts it off the top (MV 7). | Kitsune's Technique (owned R), but see #8 |

**Craft later — unique but optional:** Villainous Wealth (R; an X finisher that casts their cards,
nothing owned does it) and Jace, Wielder of Mysteries (R; mill 2 + draw each turn, AND it wins if
YOU are the one who decks out — insurance in a deck that draws this much).

### Replaceable — an owned card covers the job

| # | Craft | R | Replacement (owned) | Verdict |
|---|-------|---|---------------------|---------|
| 8 | Cut Your Losses | R | **Kitsune's Technique** (R) | Mills half their library, rounded UP, at instant speed. Loses the casualty copy. Equal. |
| 9 | Altar of Dementia | M | **Exhibition Tidecaller** (R) | Mill 3 per instant or sorcery, 10 if 5+ mana was spent; no creature to sacrifice. Reasonable exchange. |
| 10 | Lithoform Engine | M | **Gogo, Master of Mimicry** (M) | Copies an activated or triggered ability X times, loyalty abilities included. Loses copying spells. Better for the planeswalker plan. |
| 11 | Ob Nixilis Reignited | M | **Garruk, Cursed Huntsman** (M) | −3 destroys a creature AND draws, plus two Wolves a turn. Better. |
| 12 | Ashiok, Sculptor of Fears | M | **Professor Dellian Fel** (M) | 0: draw, −3: destroy a creature, +2: 3 life. Loses each-player mill 2. Reasonable exchange. |
| 13 | Ashiok, Nightmare Weaver | M | **Ral Zarek, Guest Lecturer** (M) | Surveil 2 each turn feeds Matoya and Glarb. Loses exile 3. Reasonable exchange. |
| 14 | Kasmina, Enigma Sage | M | **Chandra, Chill of Compliance** (M) | Surveil plus card advantage for 3. Loses sharing Kasmina's abilities with the other walkers. Reasonable exchange. |
| 15 | Vraska, Betrayal's Sting | M | **Vivien Reid** (M) | Card selection every turn and flier/artifact removal. Loses the proliferate. Reasonable exchange. |
| 16 | Nissa, Voice of Zendikar | M | **Wrenn and Seven** (M) | Lands to hand, ramp, a huge reach token. Better. |
| 17 | Tezzeret the Schemer | M | **Kiora, the Crashing Wave** (M) | Draw plus an extra land drop, a Fog on their best threat, a Kraken emblem. Better. |
| 18 | Jace, the Perfected Mind | M | **Jace, Reality Sculptor** (R) | Weakest exchange: JPM's −X is a mill finisher, and nothing owned matches it. Keep it on the craft list if the mill clock feels slow. |
| 19 | Erebos, God of the Dead | M | **Phyrexian Arena** (R) | A card every upkeep. Loses "opponents can't gain life". Equal. |
| 20 | Malcolm, Alluring Scoundrel | R | **Seven of Nine, Unassimilated** (M) | A card every main phase, no combat needed. Better. |
| 21 | Thryx, the Sudden Storm | R | **Thunderous Snapper** (U) | Draws on every 5+ MV spell instead of discounting it. Equal. |
| 22 | Defiler of Dreams | R | **Tanufel Rimespeaker** (U) | Draws on every MV 4+ spell — exactly what Glarb casts off the top. Equal or better. |
| 23 | Lord of the Forsaken | M | **Hama, the Bloodbender** (U) | Mill 3 on entry plus graveyard exile. Loses the 6/6 flier and repeatable mill. Weak exchange. |
| 24 | One Ring to Rule Them All | R | **Villainous Wrath** (R) | A full sweeper with a drain. The Ring spares legends (this deck has many); Wrath does not. Reasonable exchange. |
| 25 | The Mycotyrant | M | **Archmage of Runes** (R) | Different job: the Fungus count is only what Mycotyrant itself makes. Archmage draws per instant or sorcery. Reasonable. |
| 26 | Immortus, Master of Eternity | M | **Aether Syphon** (U) | A draw engine that mills 2 per draw at max speed. Speed needs life loss (Master of Lake-town helps). Weaker. |

**If every replacement is taken:** 4 mythics and 3 rares to craft (#1–7), plus the two optional
rares — down from 18M 10R.

## Deck 92 — Phoenix King (Ozai, the Phoenix King, Rakdos firebending) — 16M 18R missing

Engine: under Ozai, unspent mana becomes red instead of emptying, so firebending, Treasure and
spare mana accumulate; at six unspent Ozai has flying and indestructible. Extra combats re-fire
firebending and combat-damage payoffs; red sinks spend the pile. The owned Rakdos pool is deep
in firebending bodies, Treasure makers and X-damage sinks, so most crafts here are replaceable.
**Shared with earlier decks** (count once): Smellerbee (93), Professional Face-Breaker (93),
Embercleave and Fiery Confluence (56-historic-brawl), Rakdos, the Muscle (93).

### Craft first — no acceptable replacement found

| # | Card | R | Why | Nearest fallback |
|---|------|---|-----|------------------|
| 1 | Avatar Roku, Firebender | M | Protected. Six red on ANY player's attack, which Ozai keeps. No owned card comes close. | none |
| 2 | Fire Nation Turret | R | Protected. Firebending 2 every combat and the 50-counter sink that turns stored mana into a kill. | none |
| 3 | Fire Lord Ozai | M | Protected. Sacrifice for red on attack, and a {6} impulse sink every turn. | none |
| 4 | Aggravated Assault | R | A REPEATABLE extra combat for {3}{R}{R}: with Ozai's stored mana it is several combats a turn, each re-firing firebending. | Genji Glove (owned R) — one extra combat |
| 5 | Smellerbee, Rebel Fighter | R | Protected. Haste plus an attack-scaled hand refill. Also craft-first in deck 93. | Samut, Hazoret's Champion is not in Rakdos identity; none |
| 6 | Embercleave | M | Flash it in mid-combat with stored mana. Also craft-first in deck 56-historic-brawl. | Genji Glove (owned R), if not used for #4 |
| 7 | Moraug, Fury of Akoum | M | An extra combat on every main-phase land drop. | Full Throttle (owned R) — two combats, one-shot |
| 8 | Fiery Confluence | R | Also craft-first in deck 56-historic-brawl. | none as flexible |

### Replaceable — an owned card covers the job

| # | Craft | R | Replacement (owned) | Verdict |
|---|-------|---|---------------------|---------|
| 9 | Goldspan Dragon | M | **Smaug the Magnificent** (M) | Flying haste, a Treasure every upkeep, and damage per Treasure on attack. Loses Treasures that tap for two. Equal. |
| 10 | Ancient Copper Dragon | M | **Grim Hireling** (R) | Two Treasures every combat that connects, and Treasures become removal. Loses the 6/5 flier and the d20. Reasonable exchange. |
| 11 | Professional Face-Breaker | R | **Captain Lannery Storm** (R) | As in deck 93. |
| 12 | Savage Beating | M | **Full Throttle** (R) | Two extra combats for one. Loses instant speed and the double-strike mode. Equal, if #7 is crafted. |
| 13 | Zuko, Firebending Master | M | **Zuko, Exiled Prince** (U) | Firebending 3 from the start (no experience needed) and a {3} impulse sink. Better here. |
| 14 | Iroh, Dragon of the West | R | **Zhao, Ruthless Admiral** (U) | Firebending 2 and a team pump per sacrifice. Loses giving the whole team firebending. Reasonable exchange. |
| 15 | Neheb, Dreadhorde Champion | R | **Chandra, Dressed to Kill** (M) | Red mana plus a ping, or impulse draw, every turn. Loses the rummage-for-mana burst. Reasonable exchange. |
| 16 | Explosive Singularity | M | **Draconic Debut** (U) | X damage to any target from stored red; scales past 10. Better as a sink. |
| 17 | Overwhelming Victory | R | **Fear, Fire, Foes!** (U) | X damage removal from stored red, plus 1 to their other creatures. Loses the team trample pump. Equal. |
| 18 | Fire Nation Archers | R | **Torch Breath** (U) | Archers is a REPEATABLE {5} sink (2 to each opponent and a token); Torch Breath is one X shot. Weaker; keep Archers on the list if the sinks feel thin. |
| 19 | Insurrection | M | **Emrakul, the World Anew** (M) | Steals their whole board on cast; 12 colourless, but Ozai stores mana, and it stays as a 12/12. Reasonable exchange. |
| 20 | Sarkhan, the Dragonspeaker | M | **Chandra, Torch of Defiance** (M) | Impulse or 2 to each opponent, ramp, or 4 to a creature. Better. |
| 21 | Smaug the Impenetrable | R | **Chandra, Flameshaper** (M) | Seven mana for RRR plus impulse, haste copies, or 8 split damage. Different job (a value engine, not a body). Reasonable exchange. |
| 22 | Rakdos, the Muscle | M | **Garna, Bloodfist of Keld** (U) | As in deck 93. |
| 23 | Rakdos, Patron of Chaos | M | **Ran and Shaw** (R) | A flying firebender with a Dragon pump sink. Loses the end-step tax or two cards. Reasonable exchange. |
| 24 | Fang, Roku's Companion | R | **Nova Hellkite** (R) | Flying haste body with a ping; Warp for {2}{R}. Loses the legend pump and the return. Reasonable exchange. |
| 25 | Archpriest of Shadows | R | **Olivia, Crimson Bride** (M) | Reanimates on every ATTACK, not only on damage, tapped and attacking. Better. |
| 26 | Noxious Gearhulk | M | **Anchovy & Banana Pizza** (C) | Destroy target creature on entry. Loses the 5/4 menace body. Reasonable exchange. |
| 27 | Efreet Flamepainter | R | **Sword of Fire and Ice** (M) | A card and 2 damage per hit, protection. Loses the spell recursion. Equal or better. |
| 28 | Drana, Liberator of Malakir | M | **Black Widow, Deadly Hunter** (R) | Different job: card draw on deathtouch damage instead of team counters. Reasonable exchange. |
| 29 | Lion Vulture | R | **Buster Sword** (M) | A card per hit plus a free spell. Equal. |
| 30 | Barbed Servitor | R | **Ninja's Blades** (R) | Equipment that draws on combat damage. Equal. |
| 31 | Zuko, Avatar Hunter | R | **Academy Instructor** (U) | A token per noncreature spell (Zuko counts every red spell). Weaker; Death to Our Enemies (owned U) is the Treasure version. |
| 32 | Fire Nation Occupation | R | **Death to Our Enemies** (U) | A Treasure per noncreature spell, which Ozai keeps. Different trigger; reasonable exchange. |
| 33 | Valakut, the Molten Pinnacle | M | **Mountain** | Valakut needs five other Mountains and enters tapped. A basic is better in this manabase. |

**If every replacement is taken:** 4 mythics and 4 rares (#1–8), of which Smellerbee, Embercleave
and Fiery Confluence are already on earlier decks' lists — so 3 mythics and 2 rares NEW to deck 92.
With the fallbacks for #4 and #7 (Genji Glove can cover #4 or #6, not both): 3 mythics and 3
rares, of which 2M 1R are new (Avatar Roku, Fire Lord Ozai, Fire Nation Turret).

## Deck 91 — Scarab's Fist (Hashaton, Scarab's Fist, Esper discard Zombies) — 18M 15R missing

Engine: every creature card discarded becomes a 4/4 Zombie copy for {2}{U}; Zombie payoffs read
the copies; The Sibsig Ceremony and Necroduality are a second engine. **The owned Esper pool has
plenty of discard outlets and removal but almost NO Zombie support** — two owned cards make a
Zombie (Draugr's Helm, Essence Anchor) and none pumps one. So this deck keeps more of its crafts
than any so far: the Zombie half of the plan has nothing owned to stand in.

### Craft first — no acceptable replacement found

| # | Card | R | Why | Nearest fallback |
|---|------|---|-----|------------------|
| 1 | Hashaton, Scarab's Fist | M | The commander. | none |
| 2 | Necroduality | M | Protected. Copies every nontoken Zombie entering. | none |
| 3 | The Sibsig Ceremony | R | Protected. The second engine (cost reduction, enters trigger, a 2/2, a card back in the yard). | none |
| 4 | Waste Not | M | Protected. Pays off the each-player discard cards. | none |
| 5 | The Scarab God | M | Upkeep drain per Zombie, and 4/4 Zombie copies from any graveyard. | none |
| 6 | Cursecloth Wrappings | R | The only Zombie anthem in reach, plus embalm. | none owned |
| 7 | Gisa and Geralf | M | Cast a Zombie from your graveyard every turn: the discarded Zombies come back. | Zombify (owned U) — one-shot |
| 8 | Liliana, Death's Majesty | M | A Zombie every turn, reanimation, and a one-sided wipe of non-Zombies. | Coiling Rebirth (owned R) — reanimation only |
| 9 | Kalitas, Traitor of Ghet | M | Their dying creatures become your Zombies. Nothing owned does this. | none |
| 10 | God-Eternal Oketra | M | A 4/4 Zombie per creature cast. Nothing owned does this in Esper. | none |
| 11 | Cryptcaller Chariot | R | A Zombie per card discarded. | Scrounging Skyray (owned U) — counters only, weak |
| 12 | Liliana of the Veil | M | Protected. Each player discards (fires Waste Not), and an edict. | Fanatic of the Harrowing (owned C) — one discard on entry |
| 13 | Bone Miser | M | Protected. A Zombie, mana or a card per discard. | Monument to Endurance (owned R) — draw, Treasure or drain 3 per turn |

**Craft later — unique, no owned replacement, lower impact:** Ghoulcaller Gisa (M; a 4/4 Hashaton
copy sacrificed is four Zombies), Havengul Runebinder (R; Zombies plus a team counter per exiled
creature card), Army of the Damned (M; thirteen Zombies — a finisher nothing owned matches).

### Replaceable — an owned card covers the job

| # | Craft | R | Replacement (owned) | Verdict |
|---|-------|---|---------------------|---------|
| 14 | Psychic Frog | R | **Compulsion** (U) | PROTECTED, so the owner's call. A repeatable discard outlet that draws. Loses the growing flier. Reasonable exchange. |
| 15 | Liliana, Waker of the Dead | M | **Ral Zarek, Guest Lecturer** (M) | −1: each player discards; surveil 2; reanimate MV 3 or less. Loses the −X removal. Reasonable exchange. |
| 16 | Temmet, Naktamun's Will | M | **Sphinx of False Conclusions** (R) | Flash flier that loots on every attack and copies itself when it dies. Loses the Zombie pump. Reasonable exchange. |
| 17 | Oglor, Devoted Assistant | M | **Essence Anchor** (U) | Upkeep surveil plus a Zombie on turns a card left your graveyard. Equal. |
| 18 | Grimgrin, Corpse-Born | M | **Yawgmoth, Thran Physician** (M) | Sacrifice for removal and a card; discard to proliferate. Equal or better. |
| 19 | Unstoppable Slasher | R | **Draugr's Helm** (U) | A Zombie body with +2/+2 and menace. Reasonable exchange. |
| 20 | Dreadhorde Invasion | R | **Emet-Selch, Unsundered** (M) | Different job: loots on entry and attack (feeds Hashaton) and flips to replay the graveyard. Reasonable exchange. |
| 21 | Liliana, Heretical Healer | M | **Kaya the Inexorable** (M) | Exile any nonland permanent; ghostform protection. Better. |
| 22 | Zahur, Glory's Past | R | **Liliana the Faultless** (R) | A 1-drop discard outlet. Zahur's Zombie half needs max speed. Equal. |
| 23 | Liliana, the Last Hope | M | **Coiling Rebirth** (R) | Reanimation. Loses the repeatable −2/−1. Reasonable exchange (if #8 keeps Coiling Rebirth free). |
| 24 | Assemble from Parts | R | **Zombify** (U) | Reanimate instead of a 4/4 copy. Equal (if #7 keeps Zombify free). |
| 25 | Grim Reaper's Scythe | R | **Grim Reaper, Lethal Legionnaire** (U) | Reanimates tapped and attacking on every attack. Loses the Zombie per card leaving the yard. Reasonable exchange. |
| 26 | Never // Return | R | **Bake into a Pie** (C) | Instant-speed kill. Loses the Return half. Equal. |
| 27 | Enter the God-Eternals | R | **Consuming Ashes** (C) | Instant exile. Loses the amass and mill. Reasonable exchange. |
| 28 | Soul Diviner | R | **Collector's Vault** (U) | PROTECTED. A loot plus a Treasure each turn. Different job. Reasonable exchange. |
| 29 | Commence the Endgame | R | **Seasoned Cryomancer** (M) | Draw two, discard two (two Hashaton triggers). Better here. |
| 30 | Fallen Shinobi | R | **Locke Cole** (U) | A loot on combat damage, deathtouch and lifelink. Much weaker; skip the slot if nothing better turns up. |

**If every replacement is taken:** 10 mythics and 3 rares (#1–13), down from 18M 15R. With the
fallbacks for #12–13: 8 mythics and 3 rares. The three craft-later cards add 2M 1R.

## Deck 98 — Throw Wide the Gates (G'raha Tia, Esper spells-and-Heroes + Auras) — 15M 15R missing

Engine: every noncreature spell (once a turn, on either player's turn) becomes a Hero token with
X counters for X life; lifegain refuels it. Second engine: 13 Auras with draw-per-Aura payoffs.
The owned pool covers the SPELLS half well (flash enablers, proliferate, X draw spells, lifegain
payoffs) and the AURA half poorly — there is no owned Sram, Kor Spiritdancer or Pearl-Ear
equivalent, so the Aura-draw crafts are where the priority sits.

### Craft first — no acceptable replacement found

| # | Card | R | Why | Nearest fallback |
|---|------|---|-----|------------------|
| 1 | G'raha Tia, Scion Reborn | M | The commander. | none |
| 2 | Y'shtola, Night's Blessed | M | Protected. 2 to each opponent and 2 life per MV 3+ noncreature spell, and a card at end step. | Enduring Tenacity (owned R) — drains on lifegain |
| 3 | Ephara, God of the Polis | M | Protected. A card on BOTH upkeeps, since a Hero enters every turn. | none |
| 4 | Sram, Senior Edificer | R | The cheapest card-per-Aura engine; nothing owned draws on Aura casts. | none |
| 5 | Eriette of the Charmed Apple | M | Drains per Aura every end step, and enchanted creatures cannot attack you. | none |
| 6 | Sigil of the Empty Throne | R | A 4/4 flying Angel per enchantment cast. | none owned |
| 7 | Killian, Decisive Mentor | M | Goad per enchantment entering, a card when enchanted creatures attack. | none |

**Craft later — the same jobs as #4 and #6, a second copy of the engine:** Kor Spiritdancer (R),
Pearl-Ear, Imperial Advisor (R), Hallowed Haunting (M), Halvar, God of Battle (M; double strike
for every enchanted creature, nothing owned does it).

### Replaceable — an owned card covers the job

| # | Craft | R | Replacement (owned) | Verdict |
|---|-------|---|---------------------|---------|
| 8 | Leyline of Anticipation | R | **Valley Floodcaller** (R) | PROTECTED. Noncreature spells with flash — exactly the half G'raha needs — on a flash body. Loses the free turn-0 start. High Fae Trickster (owned R) does all spells. Equal. |
| 9 | Light-Paws, Emperor's Voice | R | **Sun-Spider, Nimble Webber** (U) | An Aura tutor on entry. Light-Paws chains Auras onto the battlefield every cast. Weaker; Federation Resupply (owned R) is a second tutor. |
| 10 | Entity Tracker | R | **Uncover the Moon-Letters** (R) | Draws X per noncreature spell (discard two). Different trigger, more cards. Reasonable exchange. |
| 11 | Archnemesis | R | **Curiosity** (U) | Still an Aura (keeps the Aura count), draws on damage. Loses the drain. Reasonable exchange. |
| 12 | Archon of the Wild Rose | R | **Heliod, Sun-Crowned** (M) | Different job: every life gained puts a counter on a Hero, and grants lifelink. Reasonable exchange. |
| 13 | Barrensteppe Siege | R | **Inexorable Tide** (R) | Proliferate on every spell grows every Hero. Better here. |
| 14 | Teferi, Hero of Dominaria | M | **Kaya the Inexorable** (M) | Exile any nonland permanent; protection for a Hero. Loses Teferi's draw and untap. Reasonable exchange. |
| 15 | Kaya, Geist Hunter | M | **Elspeth Resplendent** (M) | Counters plus flying or lifelink on a Hero each turn, and a free permanent. Better. |
| 16 | Invasion of New Phyrexia | M | **Finale of Revelation** (M) | An X noncreature spell: G'raha makes an X-counter Hero and you draw X. Equal or better. |
| 17 | Sphinx's Revelation | M | **Mind Spring** (R) | Draw X. Loses instant speed and the life. Reasonable exchange. |
| 18 | Ojutai's Command | R | **Reject Imperfection** (U) | Counterspell that proliferates. Loses the modes. Equal. |
| 19 | Sorin of House Markov | M | **Enduring Tenacity** (R) | Lifegain becomes a drain. Better, if not used for #2. |
| 20 | Doctor Strange, Surgeon | R | **The Wind Crystal** (R) | Doubles lifegain and discounts white spells. Better. |
| 21 | Rodolf Duskbringer | R | **Exemplar of Light** (R) | A flier that grows on lifegain and draws. Loses the reanimation. Equal. |
| 22 | Drana and Linvala | R | **Archangel of Thune** (M) | Flying lifelink; every lifegain grows the team. Better here. |
| 23 | Scriv, the Obligator | M | **Dawn of Hope** (R) | A card per lifegain, and lifelink tokens. Loses the Contract Auras. Reasonable exchange. |
| 24 | Eriette, the Beguiler | R | **Imprisoned in the Moon** (U) | Eriette steals with Auras; the owned Aura answers them instead (and counts as an Aura). Reasonable exchange. |
| 25 | The Circle of Loyalty | M | **Bard's Company** (R) | A team anthem with conditional flash. Loses the Knight per legendary spell. Reasonable exchange. |
| 26 | Staff of Compleation | M | **Karn's Bastion** (R) | Proliferate from a land slot. Loses the draw and mana modes. Reasonable exchange. |

**If every replacement is taken:** 5 mythics and 2 rares to craft (#1–7), down from 15M 15R. The
craft-later list adds 2M 2R. With Enduring Tenacity standing in for #2: 4M 2R.

## Deck 89 — Genesis Cycle (Szarel, Genesis Shepherd, Jund land sacrifice + poison) — 21M 12R missing

Engine: Szarel replays lands from the graveyard and grows a creature on every nontoken sacrifice
on your turn, so self-sacrificing lands are spells every turn. Poison is the second clock
(Bushmaster, Fynn, Vorinclex with Vraska's −9). The owned Jund pool is rich in extra land drops,
graveyard-land recursion and counter doublers, so most crafts here have owned stand-ins.
**Shared with an earlier deck:** Vraska, Betrayal's Sting (96 — replaceable there, a combo piece here).

### Craft first — no acceptable replacement found

| # | Card | R | Why | Nearest fallback |
|---|------|---|-----|------------------|
| 1 | Szarel, Genesis Shepherd | M | The commander. | none |
| 2 | The Gitrog Monster | M | Protected. A card per land to the graveyard, an extra land drop, an upkeep land sacrifice that triggers Szarel. | none |
| 3 | Vorinclex, Monstrous Raider | M | Protected. Doubles every counter AND poison; halves theirs. | Doubling Season (owned M) — counters only, no poison |
| 4 | Titania, Protector of Argoth | M | A 5/3 for every land sacrificed. The land engine's biggest payoff. | none |
| 5 | Korvold, Fae-Cursed King | M | A card and a counter per sacrifice. | none at that rate |
| 6 | Vraska, Betrayal's Sting | M | With Vorinclex, −9 is 18 poison: the deck's combo finish. Also wanted by deck 96 (replaceable there). | none |
| 7 | Azusa, Lost but Seeking | R | Protected. Two extra land drops a turn. | Icetill Explorer (owned R) — one extra, plus lands from the graveyard |

**Craft later — unique, but secondary:** Zopandrel (M; doubles the team every combat), Bloated
Contaminator (R; toxic plus proliferate on a 3-drop), Triumph of the Hordes (M; the infect finisher),
Tectonic Split (R; sacrificing half your lands is a Szarel trigger per land, then triple mana),
Lotus Field (R; sacrifices two lands on entry — two Szarel triggers).

### Replaceable — an owned card covers the job

| # | Craft | R | Replacement (owned) | Verdict |
|---|-------|---|---------------------|---------|
| 8 | Hardened Scales | R | **Branching Evolution** (R) | Doubles +1/+1 counters instead of +1. Better. |
| 9 | Fanatic of Rhonas | R | **Kami of Whispered Hopes** (U) | Taps for mana equal to its power and adds a counter to every counter placement. Better. |
| 10 | Dryad of the Ilysian Grove | R | **Captain Kathryn Janeway** (M) | An extra land drop on a body. Loses the every-basic-type fixing. Equal. |
| 11 | Kodama of the West Tree | M | **Loot, Exuberant Explorer** (R) | An extra land drop and a creature dig. Loses trample for modified creatures. Reasonable exchange. |
| 12 | Grist, Voracious Larva | M | **Undergrowth Recon** (M) | Different job: a land from the graveyard every upkeep, which Szarel turns into a sacrifice loop. Better here. |
| 13 | Kura, the Boundless Sky | M | **World Shaper** (R) | Returns ALL land cards from the graveyard when it dies. Equal. |
| 14 | Hornet Queen | M | **Rampaging Baloths** (R) | A 4/4 on every land drop, and the deck replays lands every turn. Reasonable exchange. |
| 15 | Tyrranax Rex | M | **Etali, Primal Conqueror** (R) | A 7-drop that casts their cards and transforms. Loses toxic 4 and ward. Reasonable exchange. |
| 16 | Rhonas the Indomitable | M | **Lumra, Bellow of the Woods** (M) | A huge body that grows with lands. Loses indestructible deathtouch. Reasonable exchange. |
| 17 | Daemogoth Titan | R | **Summon: Titan** (R) | A big body that also mills and returns lands. Equal. |
| 18 | Polukranos, Unchained | M | **Vivien, Arkbow Ranger** (M) | Counters, trample and a bite every other turn. Equal. |
| 19 | Garruk Relentless | M | **Garruk, Cursed Huntsman** (M) | Two Wolves a turn, removal plus a card. Better. |
| 20 | Lukka, Bound to Ruin | M | **Wrenn and Seven** (M) | Lands to hand, ramp, a huge Treefolk. Better here. |
| 21 | Nissa of Shadowed Boughs | M | **Vivien Reid** (M) | Card selection and removal. Loses the land animation and reanimation. Reasonable exchange. |
| 22 | Tyvar, Jubilant Brawler | R | **Professor Dellian Fel** (M) | Draw, life, removal. Loses haste-activation and recursion. Reasonable exchange. |
| 23 | Dina, Essence Brewer | M | **The Sackville-Bagginses** (R) | Sacrifice for a card and a Treasure. Equal. |
| 24 | Hidetsugu, Devouring Chaos | R | **Yawgmoth, Thran Physician** (M) | Sacrifice outlet that draws and kills, and proliferates (poison). Better. |
| 25 | Bontu the Glorified | M | **Juri, Master of the Revue** (U) | Grows per sacrifice and burns when it dies. Reasonable exchange. |
| 26 | Hearthhull, the Worldseed | M | **Redrock Sentinel** (U) | Sacrifice a land: a card and a Treasure. Equal as an outlet. |
| 27 | Genesis Device | R | **Cycle of Renewal** (C) | Sacrifice a land for two basics (a Szarel trigger). Equal. |
| 28 | Vraska Joins Up | R | **Venom Connoisseur** (U) | Deathtouch on entries. Loses the team deathtouch counters and the draw. Weak exchange. |

**If every replacement is taken:** 6 mythics and 1 rare (#1–7), down from 21M 12R; Vraska is
already counted for deck 96 only if crafted there. With Icetill Explorer for Azusa: 6M 0R.
