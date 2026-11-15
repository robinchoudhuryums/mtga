# Jodah pile — analysis (TEMPORARY working doc)

**Status: DRAFTED as deck 102 (2026-11-14); board https://claude.ai/artifact/T72nagEionydDJoJJeccw2 (builds/jodah) holds the bench.** Delete once the owner's picks land and the findings are folded into deck 102's `#: notes:`.
A scratchpad, not a source of truth — decks/ are.

**Target:** a NEW Historic Brawl deck (deck 102), commander **Jodah, Archmage Eternal**
(`{1}{U}{R}{W}`, 4/3 flier, identity WUBRG: "You may pay {W}{U}{B}{R}{G} rather than pay the
mana cost for spells you cast"). Owner's concept: cheat powerful cards into play, leaning on the
strong BRU cards, legendary cards and whatever synergies surface.

**Source list:** the owner's 154-line paste (scratchpad `jodah/pile.txt`); all 154 resolve and
all are Historic Brawl legal. Not deduplicated against other decks: this is a new deck, and a
copy in another deck is no reason to skip a card (copies are shared). Ownership is information
only (the library reads 0 for ~100 of these; the paste is the owner's own list).

**Builder project:** builds/jodah (deck key J = 102); every card carries its reason and verdict there.
batch verdicts below become its reasons then.

## 1. The decision framework

- **R1 — Effective cost is min(printed, WUBRG).** Every spell can cost exactly one of each
  colour. A card's value is its power at that price: MV 6+ cards gain the most, MV 5 cards
  gain nothing, cheap cards are cast normally. Cast triggers still fire (it is still cast).
- **R2 — X spells cost X = 0 under the alt cost**, and alternative costs do not stack (bestow,
  warp, evoke cannot be paired with Jodah's). Additional costs (kicker) still add on top.
- **R3 — Five colours every turn is THE constraint.** WUBRG needs one source of each colour, so
  fixing density decides consistency more than any single bomb. A card that makes any land or
  permanent produce every colour (Leyline of the Guildpact, The World Tree, Timeless Lotus,
  Haunted Screen, Oracle's Moxen) is worth more here than in any other deck.
- **R4 — A second cheat layer stacks on the first.** Free casts (Jodah the Unifier, Maelstrom
  Archangel, Omniscience, Invasion of Alara, Golos) and put-onto-battlefield effects (Nissa,
  Leyline Tamer) turn a 5-mana turn into two bombs.
- **R5 — Legendary density feeds Jodah the Unifier and Rona.** The Unifier cascades into a
  legendary nonland of LESSER mana value, so high-MV legends make bigger cascades; count legends.
- **R6 — The commander can die.** Leyline of Mutation and the Bringers keep the alt cost alive
  without him (commander tax is {2} a recast).
- **R7 — Removal rule (owner):** no removal that hands the opponent life or a land.
- **R8 — Cheap support must still pull weight:** fixing, card selection, interaction. A 2-drop
  that only adds to a board is filler here.

## 2. Standing error list

- 2026-11-15: ten of the owner's screenshot cards were dismissed as "off-plan" by category; several make or fix mana (Photon, The Last Agni Kai, Paradigm Shifter, Kalain, Kolvori's Ringhart Crest). Grade each from its text — the rule-6 error this skill warns about.

## 3. Cross-batch observations

- A FREE-CAST CHAIN is surfacing: Kellan, the Kid and Nico Minoru reward casts from anywhere but the hand, which is exactly what the Unifier, Nico, Capstone, Golos and Neera produce.
- Upkeep cheats (The Prismatic Bridge, Bringer of the Green Dawn) multiply with Obeka's extra upkeep steps.
- Batch 1 already shows a double-each-colour subtheme: Door to Nothingness needs
  WWUUBBRRGG, which Ramos (remove five counters) and Esper Terra's chapter IV both make exactly.
  A spice line, not a plan.

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

### Batch 1 (cards 1–30)

| Card | Verdict | Note |
|---|---|---|
| Rona, Herald of Invasion | ★ | 2-mana legendary looter that untaps on each legendary cast (R5, R8) |
| The World Tree | ★★ | at six lands every land taps for any colour (R3); enters tapped |
| Crystal Quarry | ★ | {5}: WUBRG — a guaranteed Jodah cast from six lands (R3); colourless otherwise |
| Meeting of the Five | ◇ | MV 8 for WUBRG, but only casts exactly-three-colour spells; count them first |
| Wizard's Staff | ◇ | doubles Jodah the Unifier's cascade (a Wizard, equip {1}); narrow |
| Flux Channeler | △ | proliferate needs walkers/counters |
| Gogo, Master of Mimicry | ◇ | copies the Unifier's cascade trigger X times; mana-hungry |
| Oracle of the Alpha | ★★ | conjures the Power Nine: five Moxen are fixing, Black Lotus is a Jodah cast (R3) |
| Tazri, Beacon of Unity | △ | party discount, little for this plan |
| Timeless Lotus | ★★★ | taps for exactly WUBRG every turn — one Jodah cast per turn from one card (R1, R3) |
| Ramos, Dragon Engine | ★★ | MV 6 for WUBRG; a five-colour cast adds five counters; ten mana once a turn |
| Providence of Night | ◇ | copies hybrid-cost spells only |
| Omnath, Locus of All | ★★ | card per turn, plus mana from 3+-pip cards, which this pile is full of |
| Maelstrom Archangel | ★★ | flying 5/5; combat damage casts a spell from hand free (R4) |
| Jodah, the Unifier | ★★★ | legendary cascade plus a legend anthem — the second cheat layer (R4, R5) |
| Invasion of Alara | ★★ | free cast of an MV ≤4 card plus one to hand; the back face is a five-mode bomb |
| Infinite Guideline Station | ★ | Robots per multicoloured permanent; station 12 is slow |
| Golos, Tireless Pilgrim | ★★ | fetches any land; late, plays the top three free (R3, R4) |
| Door to Nothingness | ◇ | WWUUBBRRGG: you win; Ramos or Esper Terra make exactly that (spice) |
| Chromanticore | ◇ | 4/4 with five keywords; bestow cannot use the alt cost (R2) |
| Leyline of the Guildpact | ★★★ | every land is every basic type — all lands tap for any colour (R3); free from the opening hand |
| Marshals' Pathcruiser | △ | basic to hand, then a vehicle |
| Haunted Screen | ★★ | 3-mana rock for any colour (R3) |
| Nissa, Leyline Tamer | ★★★ | MV 7 for WUBRG; landfall draws and puts a creature onto the battlefield (R1, R4) |
| Norman Osborn | △ | graveyard casting is off-plan |
| Thanos, the Mad Titan | ★ | 3-mana deathtouch lifelink; power-up is a parity sweeper (hits ours too) |
| Tam, the Possibility | ◇ | needs planeswalkers |
| Terra, Magical Adept | ◇ | chapter IV makes WWUUBBRRGG; slow |
| Bringer of the Green Dawn | ★★ | carries its own WUBRG alt cost (R6); a 3/3 every upkeep |
| Leyline of Mutation | ★★ | the commander's ability on an enchantment (R6); free from the opening hand |

### Batch 2 (cards 31–60)

| Card | Verdict | Note |
|---|---|---|
| Esika, God of the Tree | ★★★ | taps for any colour and gives every other legend that ability (R3, R5); the back face, The Prismatic Bridge, is a WUBRG upkeep cheat that puts a creature or walker onto the battlefield (R4) |
| Widespread Thieving | ★★ | a Treasure per multicoloured spell (R3); pay WUBRG to play the hideaway card free |
| Najeela, the Blade-Blossom | ◇ | WUBRG extra combats; the Warrior half is off-plan |
| Kenrith, the Returned King | ★ | legend with five activations, reanimation {4}{B} and draw {3}{U} among them |
| Leonardo, the Balance | △ | token plan |
| Lone Rider | △ | lifegain transform, off-plan |
| Extricator of Sin | △ | off-plan |
| Eldrazi Displacer | △ | needs {C} specifically |
| Gisela, the Broken Blade | △ | a flying body without Bruna |
| Wharf Infiltrator | △ | discard engine, off-plan |
| Corrupted Shapeshifter | △ | filler |
| Idol of False Gods | △ | Eldrazi tokens, off-plan |
| Glaring Fleshraker | ✗ | needs {C} and colourless spells |
| Anticausal Vestige | ★★ | warp {4}: it is exiled at end step, so it LEAVES — draw, then put a permanent with MV ≤ lands from hand onto the battlefield (R4); recast later |
| Bane of Bala Ged | ★★ | MV 7 for WUBRG (R1); each attack exiles two of their permanents |
| Herigast, Erupting Nullkite | ★★ | MV 9 for WUBRG; cast trigger refills the hand; every creature gets emerge |
| Ulamog, the Defiler | ★★★ | MV 10 for WUBRG; cast trigger exiles half their library, then enters huge with annihilator (R1) |
| Emrakul, the World Anew | ★★★ | MV 12 for WUBRG; cast trigger steals every creature they have (R1). Leaving sacrifices our creatures: protect it |
| Wizard Class | ★ | 1-mana enchantment that draws two at level 2 (R8) |
| Goro-Goro and Satoru | ★ | {1}{R}: haste for the cheated bombs; Dragons when new creatures connect |
| Maestros Diabolist | △ | small attacker |
| Marchesa, Dealer of Death | △ | crime card selection |
| Spelldrain Assassin | ◇ | casualty for an instant or sorcery |
| Cormela, Glamour Thief | △ | spell-only mana |
| Fire Lord Azula | ◇ | copies spells cast while she attacks (instant speed only) |
| Doctor Doom, King of Latveria | △ | Villain connive |
| Mai and Zuko | ◇ | flash for artifacts and Allies |
| Nicol Bolas, the Ravager | ★★ | 4-mana flier with discard; the walker side removes and reanimates (BRU legend) |
| Obeka, Splitter of Seconds | ★ | extra upkeeps replay upkeep cheats (Prismatic Bridge, Bringer of the Green Dawn) — spice |
| Saruman, the White Hand | ★ | amass equal to a noncreature spell's printed MV: a cheated big spell makes a big Army |

### Batch 3 (cards 61–92)

| Card | Verdict | Note |
|---|---|---|
| Evelyn, the Covetous | △ | Vampire engine |
| Inalla, Archmage Ritualist | ◇ | Wizard copies; Jodah, the Unifier and Rona are Wizards, but the payoff wants five |
| Kefka, Court Mage | ★ | legend; ETB/attack discard into draws |
| Nicol Bolas, Dragon-God | ★★ | walker with draw and −3 removal (BRU) |
| Glamorous Outlaw | ★ | MV 6 for WUBRG; can sit exiled as a UBR land fixer |
| Sauron, the Dark Lord | ★ | MV 6 7/6, ward that costs them a legend |
| Lord Xander, the Collector | ★★ | MV 7 for WUBRG; discard half, mill half, and sacrifice half when it dies (R1) |
| Cruel Ultimatum | ★★★ | {U}{U}{B}{B}{B}{R}{R} becomes WUBRG — the alt cost turns an uncastable card into a 5-mana blowout (R1) |
| Nicol Bolas, God-Pharaoh | ★★★ | MV 7 walker for WUBRG; +2 casts their card free, −4 deals 7 (R1, R4) |
| Sauron, Lord of the Rings | ★★★ | MV 8 for WUBRG; the cast trigger amasses 5 and reanimates a creature (R1, R4) |
| Pensive Professor | ★ | every WUBRG cast spends 5, so it grows and draws (increment) |
| Crypt of the Eternals | ◇ | UBR filter land, colourless otherwise |
| Breya, Etherium Shaper | ★ | 4-colour legend, two fliers, removal modes |
| Relic of Sauron | ◇ | UBR rock |
| Jace, Multiverse Architect | ★★ | +1 draw two; −3 puts a creature or walker onto the battlefield (R4) |
| Bringer of the Black Dawn | ★★ | own WUBRG alt cost (R6); upkeep tutor to the top |
| Iridescent Tiger | ★★ | when cast, adds WUBRG — cast it, then cast a Jodah spell with the refund (R3) |
| Karolina Dean, Runaway | ★ | WUBRG every first main phase, not for spells from hand: recasts the commander, pays activations (Golos, Kenrith) |
| Tome of the Infinite | ◇ | random conjures |
| Prismatic Omen | ★★★ | 2 mana: every land is every basic type, so all lands tap for any colour (R3) |
| Prismatic Undercurrents | ★ | basics to hand plus an extra land drop |
| Vona de Iedo, the Antifex | ★★ | ETB destroys a nonland permanent (R7 clean) |
| Change the Narrative | ◇ | random walkers |
| The Bloodbile Swarm | △ | off-plan |
| Dáin, Lord of the Iron Hills | △ | small |
| Ashe, Princess of Dalmasca | △ | artifact dig |
| Rosa, Resolute White Mage | △ | small |
| Princess Yue | △ | scry body |
| Elrond, Moon-Reader | ◇ | ability draws |
| Grand Nagus Zek | ◇ | Treasures need deaths |
| Lo and Li, Twin Tutors | △ | Noble/Lesson tutor |
| Loot, Exuberant Explorer | ★ | extra land drop; puts a creature with MV ≤ lands onto the battlefield |

### Batch 4 (cards 93–124)

| Card | Verdict | Note |
|---|---|---|
| Baron Bertram Graywater | △ | token plan |
| Indulging Patrician | △ | lifegain plan |
| Bard, King of Dale | ★ | MV 6 for WUBRG; doubles extra draws and tokens |
| Falkenrath Aristocrat | △ | aggro body |
| Raphael, Fiendish Savior | △ | Devil tribal |
| Olivia, Crimson Bride | ★★ | MV 6 for WUBRG; each attack reanimates a creature, kept while Olivia (a legendary Vampire) stays (R4) |
| Buxton, Decorated Host | ◇ | needs tapped creatures |
| The Key to the Vault | ★ | combat damage digs and casts a card free (R4) |
| Jacob Hauken, Inspector | ★★ | looter now; transformed, casts a card from its exile free each turn (R4) |
| Malcolm, Alluring Scoundrel | △ | slow free cast |
| Tempest Trapper | △ | spell-only mana |
| Reenact the Crime | ◇ | narrow |
| The Conundrum of Bowls | ◇ | slow |
| Yue, the Moon Spirit | ★ | waterbend {5}: cast a noncreature spell from hand free — creatures and artifacts help pay |
| Jin-Gitaxias | ★★ | draws on noncreature MV 3+; the Saga's chapter III casts any number of spells free (R4) |
| Omnispell Adept | ◇ | instants and sorceries only |
| Omniscience | ★★★ | MV 10 for WUBRG, then every spell from hand is free (R1, R4) |
| Brazen Bluff | ◇ | conditional |
| Nico Minoru, Runaway | ★★ | {2}{R}, discard: cast the top nonland card free, repeatable; pings on every non-hand cast (R4) |
| Improvisation Capstone | ★★★ | MV 7 for WUBRG; free casts from the top, and paradigm repeats it free every first main phase (R1, R4) |
| Descendants' Path | ◇ | needs shared creature types |
| Fight Rigging | ◇ | hideaway released by a power-7 creature (the Eldrazi qualify) |
| World War Hulk | ◇ | one free red/green creature |
| Omnipresence | ◇ | MV 8 for WUBRG; free casts capped by creature count |
| Kaya the Inexorable | ★★ | −3 exiles a nonland permanent (R7 clean); the emblem casts legends free |
| Neera, Wild Mage | ★★ | once a turn, swap a cast for a free cast off the top (R4) |
| Bre of Clan Stoutarm | ◇ | needs lifegain |
| Djeru and Hazoret | ★ | attacks cast a legendary creature from the top six free (R4, R5) |
| Kasmina, Enigma Sage | ◇ | walker support |
| Unexpected Results | ★ | free cast of the top card; in a deck of bombs the hit rate is high |
| Kellan, the Kid | ★★ | every non-hand cast (Unifier, Nico, Capstone, Golos) also casts a permanent from hand free (R4) |
| Tamiyo, Field Researcher | ◇ | the −7 emblem is a long way off |

### Batch 5 (cards 125–154)

| Card | Verdict | Note |
|---|---|---|
| Gandalf, Party Guest | ◇ | free instants/sorceries, scaled by legendary Wizards |
| Narset, Enlightened Exile | ◇ | graveyard spell copies |
| Commander Spock | ★★ | ETB and attack cast the top card free if its MV ≤ differently named lands — a singleton manabase makes that high (R4) |
| Narset, Enlightened Master | ★★ | MV 6 for WUBRG; each attack casts noncreature spells from the top four free |
| Buster Sword | ★ | damage-scaled free cast |
| Glamdring | ◇ | instants/sorceries only |
| Cosmic Cube | ★★ | each attack casts from the top six, capped by the biggest attacker's power — the Eldrazi make that 7+ |
| Planetarium of Wan Shi Tong | ★★ | MV 6 for WUBRG; scry casts the top card free once a turn |
| Teyo, Aegis Adept | △ | off-plan |
| Lukka, Coppercoat Outcast | ★★ | −2 turns a creature into a bigger one from the library (R4) |
| Ashiok, Sculptor of Fears | ★ | MV 6 for WUBRG; −5 reanimates |
| Akul the Unrepentant | ◇ | needs three sacrifices |
| Nissa of Shadowed Boughs | ★ | −5 puts a creature with MV ≤ lands onto the battlefield |
| Raph & Mikey, Troublemakers | ★★ | MV 7 for WUBRG; each attack puts a creature from the library onto the battlefield attacking |
| Kinnan, Bonder Prodigy | ★★ | doubles rock and dork mana (Timeless Lotus makes six); {5}{G}{U} puts a non-Human creature onto the battlefield |
| Nissa, Steward of Elements | ◇ | X walker, X = 0 under the alt cost (R2) |
| Rocco, Cabaretti Caterer | ◇ | X = 0 under the alt cost (R2); fine cast normally |
| Aang, at the Crossroads | ★ | puts an MV ≤4 creature from the top five onto the battlefield |
| Stable Wormhole | ★ | an any-colour Planet per attack (R3) |
| Artificial Anomaly | ◇ | colourless land until sacrificed |
| Robber of the Rich | △ | small |
| Chandra, Hope's Beacon | ★ | MV 6 for WUBRG; +2 adds two mana of any colours, −X is removal |
| Goldspan Dragon | ★★ | Treasures make two mana of one colour (R3) |
| Rogue Class | ◇ | slow |
| King Narfi's Betrayal | ◇ | slow |
| Galazeth Prismari | ◇ | instant/sorcery mana |
| Insidious Roots | △ | off-plan |
| Helga, Skittish Seer | ★ | draws on every MV 4+ creature |
| Vraska, Soul of Stone | ★ | a Treasure per noncreature spell (R3) |
| Great Divide Guide | ★★★ | 2 mana: every land and Ally taps for any colour (R3) |

### Round 2 (owner's notes, 2026-11-14) — re-grades and outside-pile finds

Re-graded on the owner's notes:
- **The Key to the Vault ◇→★★, Buster Sword ★→★★:** an equipped flier (Jodah himself is a 4/3 flier)
  connects most turns; Buster Sword on Jodah is 7 damage, so a free spell of MV ≤ 7 plus a draw (R4).
- **Yue, the Moon Spirit ★→★★:** waterbend {5} is GENERIC and creatures/artifacts help pay, so it is a
  repeatable free noncreature cast that does not need five colours (R3, R4).
- **Stable Wormhole ★→★★:** an any-colour land every attack, and the deck now has an attack package.
- **Door to Nothingness ◇→★★:** WWUUBBRRGG is reachable from ten any-colour lands (Prismatic Omen,
  Leyline of the Guildpact, Great Divide Guide), Timeless Lotus plus five, Ramos alone, or anything
  with Chromatic Orrery. No card in the pool reduces a COLOURED activation cost (Zirda and Training
  Grounds reduce generic only), so the route is making the colours, not discounting them.

Outside the pile (pool, Historic Brawl legal):
- **Sunbird's Invocation ★★★** — every spell cast from hand reveals cards equal to its PRINTED mana
  value and casts one free: Ulamog for WUBRG reveals ten.
- **Chromatic Orrery ★★★** — "spend mana as though it were mana of any color": WUBRG and Door's
  WWUUBBRRGG become payable with any mana; taps for five; draws per colour.
- **One with the Multiverse ★★★** — MV 8 for WUBRG; play from the top and one free spell a turn.
- **Etali, Primal Conqueror ★★** — MV 7 for WUBRG; ETB casts a free spell from each library.
- **Leyline of Anticipation ★★** — flash on everything, so every alt-cost bomb is instant speed.
- **Lithoform Engine ★, Roaming Throne ★ (Wizard), Echoes of Eternity ◇, Bring to Light ◇** — trigger
  copiers and a converge tutor; bench.
- **Fires of Invention ✗** — it caps us at two spells a turn and only on our turn, which breaks the
  free-cast chains (the G-42 shape: a cheat card that fights the engine).
- **Instant interaction:** Sublime Epiphany ★★★ (MV 6 for WUBRG, counters spells and abilities),
  Jeskai Revelation ★★ (MV 7 for WUBRG), Cryptic Command ★★, Hero's Downfall ★★, Anguished Unmaking
  ★★, Teferi, Time Raveler ★★ (opponents only at sorcery speed, which protects our big turns);
  bench: Glen Elendra's Answer, The End, Infernal Grasp, Kolaghan's Command, Gale's Redirection.
- **Rejected on the removal rule (R7):** An Offer You Can't Refuse (gives Treasures), Assassin's Trophy
  (gives a land).

**Draft v2 (scratch):** +16 (the five above from the pile, Sunbird's Invocation, Chromatic Orrery, One
with the Multiverse, Etali Primal Conqueror, Leyline of Anticipation, and the six interaction cards),
−16 (Djeru and Hazoret, Sauron the Dark Lord, Unexpected Results, Goro-Goro and Satoru, Kenrith,
Breya, Vraska Soul of Stone, Karolina Dean, Wizard Class, Kefka, Chandra Hope's Beacon, Thanos, Bane
of Bala Ged, Bringer of the Black Dawn, Nicol Bolas the Ravager, Herigast). Legal; floor A;
interaction 13 (5 instant, 8 can hit a noncreature permanent); card advantage 14.

### Round 3 (2026-11-15) — the slow start

Owner's games: the plan is strong once it runs but slow to start. Measured with a draw simulation
(37 lands of 99, on the play): five mana by turn 4 ~4%, by turn 5 ~42%, because the only early
mana source is Esika. Adding Chromatic Lantern, Arcane Signet, Birds of Paradise, Paradise Druid and
Farseek raises that to ~25% by turn 4 and ~56% by turn 5 (three of them: ~17% / ~50%). The fix is
cheap mana that also fixes; the dorks double as early blockers. Proposed cuts: Rona, Jin-Gitaxias,
Commander Spock, Narset Enlightened Master, Bringer of the Green Dawn. The consistency model does not
count nonland mana sources, so its on-curve figure cannot show this.

## 5. Consolidated plan (live)

**Draft 100 (proposed, not yet a deck file):** 62 nonland + 37 lands + Jodah. Scratch-measured:
legal for Historic Brawl, floor A (interaction 12 against the 100-card bar of 12, card advantage
17), 41 legends of 62 nonland, 22 cards at MV 6+, keepable 79.9% (95.9% with the free mulligan),
sources W19 U19 B19 R20 G22.

- **Fixing (14):** Timeless Lotus, Great Divide Guide, Prismatic Omen, Leyline of the Guildpact,
  Haunted Screen, Esika, Oracle of the Alpha, Iridescent Tiger, Goldspan Dragon, Kinnan,
  Widespread Thieving, Golos, Omnath, Karolina Dean.
- **Alt-cost redundancy (3):** Leyline of Mutation, Bringer of the Green Dawn, Bringer of the Black Dawn.
- **Bombs for WUBRG (12):** Ulamog, Emrakul, Omniscience, Improvisation Capstone, Cruel Ultimatum,
  Nicol Bolas God-Pharaoh, Sauron Lord of the Rings, Nissa Leyline Tamer, Lord Xander, Herigast,
  Bane of Bala Ged, Ramos.
- **Free-cast engines (14):** Jodah the Unifier, Maelstrom Archangel, Invasion of Alara, Anticausal
  Vestige, Jace Multiverse Architect, Jacob Hauken, Jin-Gitaxias, Nico Minoru, Neera, Kellan,
  Commander Spock, Narset Enlightened Master, Planetarium of Wan Shi Tong, Cosmic Cube.
- **Into play (3):** Lukka, Raph & Mikey, Olivia.
- **Interaction (6):** Kaya the Inexorable, Vona de Iedo, Nicol Bolas Dragon-God, Nicol Bolas the
  Ravager, Thanos, Breya.
- **Flow and glue (10):** Rona, Wizard Class, Kefka, Goro-Goro and Satoru, Kenrith, Chandra Hope's
  Beacon, Unexpected Results, Djeru and Hazoret, Sauron the Dark Lord, Vraska Soul of Stone.
- **Lands (37):** deck 101's owned-heavy five-colour manabase with The World Tree, Crystal Quarry
  and Artificial Anomaly in for Q Continuum, Ni'Var Science Academy and Subspace Anomaly.

**Known gaps:** all 12 interaction pieces are sorcery-speed (0 instant); the pile has no counter or
instant removal. The modelled cast-on-curve (33.9%) prices PRINTED costs and cannot see the alt
cost (R1) — not a meaningful figure for this deck.

**Bench (★ not in the 62):** Crystal Quarry and The World Tree are in as lands; Pensive Professor,
Glamorous Outlaw, Bard, The Key to the Vault, Yue, Buster Sword, Ashiok, Nissa of Shadowed Boughs,
Aang, Stable Wormhole, Helga, Obeka, Saruman, Loot, Prismatic Undercurrents, Thanos alternatives.
