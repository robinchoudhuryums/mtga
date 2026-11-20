# Brawl craft triage — unowned mythics and rares (TEMPORARY working doc)

**Status: IN PROGRESS — decks 93, 88, 56-historic-brawl and 96 done; 92, 91, 98, 89 to go.**
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
