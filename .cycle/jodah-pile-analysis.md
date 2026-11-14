# Jodah pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the deck is drafted and the findings are folded into its
`#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Target:** a NEW Historic Brawl deck (deck 102), commander **Jodah, Archmage Eternal**
(`{1}{U}{R}{W}`, 4/3 flier, identity WUBRG: "You may pay {W}{U}{B}{R}{G} rather than pay the
mana cost for spells you cast"). Owner's concept: cheat powerful cards into play, leaning on the
strong BRU cards, legendary cards and whatever synergies surface.

**Source list:** the owner's 154-line paste (scratchpad `jodah/pile.txt`); all 154 resolve and
all are Historic Brawl legal. Not deduplicated against other decks: this is a new deck, and a
copy in another deck is no reason to skip a card (copies are shared). Ownership is information
only (the library reads 0 for ~100 of these; the paste is the owner's own list).

**Builder project:** deferred until deck 102 exists (`builder.py new` needs a deck file); the
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

- (none yet)

## 3. Cross-batch observations

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

## 5. Consolidated plan (live)

(after the last batch)
