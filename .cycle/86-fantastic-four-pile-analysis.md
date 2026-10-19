# Fantastic Four Brawl pile (deck 86) — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once deck 86 is drafted and these findings are folded into
its `#: notes:`. A scratchpad, not a source of truth — decks/ are.

**Source list:** the owner's 79-card pile (2026-10-19), commander The Fantastic Four
(MSC 741). 42 of the 79 already sit in other decks; that does not matter for a new deck,
since decks share the collection.

## 1. The decision framework

The Fantastic Four — {R}{G}{W}{U} 4/4 Human Hero: "When The Fantastic Four enter and
whenever you cast a spell with power, toughness, or mana value 4, choose one that hasn't
been chosen this turn: a 0/4 Wall with defender; 3 damage to each opponent; two +1/+1
counters on target creature; draw a card."

- **F1 — THE NUMBER IS 4.** A spell triggers the commander if its printed power OR
  toughness OR mana value is 4, read ON THE STACK: +1/+1 counters do not count, X does
  (Big Bertha cast with X=3 is mana value 4). Up to four triggers a turn, each a different
  mode, so two or three qualifying spells a turn is the target and each one is worth
  roughly an extra card. Every verdict below names which of P/T/MV is 4.
- **F2 — COUNTERS ARE THE SECOND ENGINE.** One mode places two +1/+1 counters, and the pile
  is full of counter multipliers (Doc Samson +1, Shang-Chi, Martial Mentor doubling, Hulk,
  Strongest There Is, Miles Morales's back face, The Thing). Grade a counter card by what
  it does under a doubler, not alone.
- **F3 — NONCREATURE SPELLS BEFORE COMBAT.** Human Torch, Mister Fantastic, Invisible Woman
  and The Thing each check "if you've cast a noncreature spell this turn" at beginning of
  combat. A noncreature spell with mana value 4 is worth double here.
- **F4 — {R}{G}{W}{U} ABILITIES.** Mister Fantastic, Human Torch, Invisible Woman and The
  Thing each have a four-colour activated or attack payment. Shang-Chi, Master of Kung Fu
  pays for creature abilities; the manabase must make all four colours.
- **F5 — POWER 4+ IS COUNTED.** Goliath (draws), Giant-Man (mana) and several others count
  creatures with power 4 or greater; the counter engine pushes bodies over that line.
- **F6 — TRIBES.** Mutant (X-23, Wolverine, Claws Out, Colossus, and every Teenage Mutant
  Ninja Turtle) and Gamma (the Hulks, Doc Samson, She-Hulk). Count before relying on one.
- **F7 — COLOURS.** Four colours, no black. The pile leans hard green; fixing is the cost.

## 2. Standing error list
(none yet)

## 3. Cross-batch observations
- O1: the pile is 79 creatures-and-friends and almost nothing else: 4 noncreature spells
  (Heroic Intervention, Earth's Mightiest Heroes, Ajani, Mentor of Heroes, Zanarkand's
  adventure). F3 needs noncreature spells cast before combat, so they must come from OUTSIDE
  the pile.
- O2: 36 of 79 pile cards hit F1 (P, T or MV 4) — enough for ~25 in the 100 without
  stretching. Big Bertha (X=3) and Mutagen Man (X=2) hit at a chosen X.
- O3: interaction in the pile is thin: Wolverine, Fierce Fighter (fight), Storm, Shaker of
  Skies, Leatherhead, Swamp Stalker (artifact/enchantment on hit), Heroic Intervention and
  Jennifer Walters (protection). The pool holds 212 mana-value-4 noncreature interaction
  spells in these colours (33 owned) — each one triggers the commander AND the members' F3
  checks, the best double-dip available.
- O4 (variant signal): the TMNT / Mutant half (Michelangelos, Raphaels, Mutagen tokens,
  Genghis Frog, Mikey & Don casting Mutants off the top) is a coherent Mutant deck of its
  own, and most of those cards already sit in decks 4, 9, 50, 58 and 69. For deck 86 take
  only the ones that also hit F1/F2.
- O5: counter doublers stack (Doc Samson +1, Michelangelo, Weirdness to 11 +1, Shang-Chi,
  Martial Mentor ×2): the commander's two counters become (2+1+1)×2 = 8 with all three.

## 4. Running verdicts

### Batch 1 (1–30)
| Card | 4? | Verdict | Note |
|---|---|---|---|
| Peter Parker // Amazing Spider-Man | — | ★★ | back face gives legendary spells web-slinging {G}{W}{U}: recast a 4-drop (another trigger) by returning a tapped creature |
| Human Torch | MV | ★★★ | FF member; flying, double strike, haste after a noncreature spell (F3) |
| Mister Fantastic | T | ★★★ | draws after a noncreature spell; {R}{G}{W}{U},{T}: copy a triggered ability twice — the commander's trigger three times means three different modes |
| Invisible Woman | — | ★★ | FF member; Wall after a noncreature spell; attack pump that makes a creature unblockable |
| Bruce Banner // The Incredible Hulk | — | ★★ | {X}{X},{T}: draw X; back face gets extra combats when dealt damage |
| Jennifer Walters // The Sensational She-Hulk | — | ★★ | opponents can't cast spells on your turn (protection); back face redirects damage |
| Heroic Intervention | — | ★★ | instant hexproof + indestructible for the team |
| Goliath, Mass Manipulator | — | ★★ | power-up draws a card per creature with power 4+ (F5) |
| Miles Morales // Ultimate Spider-Man | — | ★★ | two counters on enter; back face doubles counters on every attack |
| Shang-Chi, Master of Kung Fu | — | ★★ | taps for two mana for creature abilities: transforms, power-ups, Mister Fantastic's copy |
| X-23, Deadly Weapon | — | ◇+ | Mutant enters → counters; only as good as the Mutant count (F6) |
| Flatman | MV | ★ | 1/10 wall that swaps to 10/1; a trigger and a blocker |
| Hulk, Brutal Brawler | P,T,MV | ★★★ | triple 4; a counter on every other creature each attack |
| Hulk, Strongest There Is | MV | ★★ | doubles counters on Gamma creatures each upkeep — count Gamma first |
| Wolverine, Claws Out | MV | ★★ | Mutants double their power on attack |
| Colossus, Steel Stalwart | P | ★★ | Mutant lord, indestructible on your turn |
| Giant-Man, Gargantuan Genius | — | ★ | {G} per creature with power 4+ at first main |
| Doc Samson, Super Psychiatrist | — | ★★★ | +1 to every counter placement (the commander's two counters become three); taps for mana equal to power |
| Earth's Mightiest Heroes | — | ★ | 6-mana dig for creatures |
| Shang-Chi, Martial Mentor | P,T | ★★★ | doubles every +1/+1 counter placement |
| The Thing | — | ★★★ | FF member; four counters after a noncreature spell; doubles counters on attack |
| Storm, Shaker of Skies | P | ★★ | enters: destroy an artifact, enchantment or flier — noncreature interaction |
| The Thing, Ben Grimm | — | ★ | 7/7 trample that grows when Heroes connect |
| Zanarkand, Ancient Metropolis | — | ★ | a land that is also a Hero-token spell |
| Big Bertha | MV at X=3 | ★★ | flexible counter body; X=3 is a trigger |
| Scarlet Spider, Ben Reilly | P | ★★ | web-slinging re-buys a tapped creature |
| Wolverine, Best There Is | — | ★ | doubles its own damage; regenerates |
| Wolverine, Fierce Fighter | MV | ★★★ | haste and a fight on entering: removal that triggers the commander |
| Hulk, Gamma Goliath | — | ★★ | power-ups cost {3} less (Goliath, Shang-Chi, Martial Mentor, Hulk) |
| Black Panther, Wakandan King | — | ★ | counters on lands per creature entering; moves them to a creature to draw |

### Batch 2 (31–60)
| Card | 4? | Verdict | Note |
|---|---|---|---|
| Shuri, the Black Panther | — | ◇ | needs three to six artifacts |
| Ms. Marvel, Elastic Ally | — | ★★ | draws when a creature above its base power connects — every countered creature |
| She-Hulk, Attorney-at-Law | — | ★★ | power-up doubles counters on every creature (Hulk, Gamma Goliath cuts it by {3}) |
| T'Challa, the Black Panther | — | ◇ | wants artifact spells of mana value 4+ |
| Black Panther, Vanguard | P,T,MV | ★★★ | triple 4; a token or team pump per nontoken Hero entering |
| Storm, Windrider | P,T,MV | ★★★ | triple 4; fliers can't attack you or block your creatures |
| Silk, Web Weaver | MV | ★★ | a token per creature spell; team pump; web-slinging |
| Ajani, Mentor of Heroes | — | ★★ | noncreature (F3); three counters a turn (doubled) or dig |
| Sigarda, Heron's Grace | P | ★★ | hexproof for you and your Humans (the Fantastic Four are Humans) |
| Spider-Man India | P,T | ★★★ | a counter and flying per creature spell |
| Web-Warriors | P | ★★ | a counter on each other creature |
| Ant-Man, Colony Commander | — | ★ | Insect token once a turn off counters |
| The Astonishing Ant-Man | — | ★ | grows on draws, cashes counters for Insects |
| Ant-Man, Reformed Rogue | — | ◇+ | draws on damage |
| Beast, Erudite Aerialist | MV | ★★ | flies once countered; draws on damage |
| Storm, Force of Nature | T,MV | ★★ | flier; storm on the next instant/sorcery |
| Moon Girl and Devil Dinosaur | — | ◇+ | 6/6 on the second draw |
| Darwin, Adaptive Mutant | — | ★ | evolves; indestructible for two counters |
| Black Tom Cassidy | — | ★ | mana dork |
| Michelangelo, Weirdness to 11 | — | ★★★ | +1 to every counter placement (stacks with Doc Samson) |
| Mona Lisa, Science Geek | — | ★★ | mana equal to her power — big with counters |
| Leatherhead, Swamp Stalker | T,MV | ★★ | hexproof counter; destroys an artifact or enchantment on hit |
| Michelangelo, Improviser | P,T,MV | ★★ | triple 4; puts a creature or land from hand on hit |
| Michelangelo, Mutant BFF | P,T,MV | ★★★ | triple 4; Mutagen tokens; countered creatures can't be double-blocked |
| Venus, Torn Between Worlds | — | ★ | draws when countered creatures connect ({U}) |
| Groundchuck & Dirtbag | — | ★ | doubles land mana; 6 mana |
| Leatherhead, Iron Gator | — | ★ | two counters on everything each attack; 7 mana |
| Mutagen Man, Living Ooze | MV at X=2 | ★★ | X Mutagen tokens; X=2 is a trigger |
| Raph & Mikey, Troublemakers | — | ◇+ | 7-mana creature cheat |
| Mikey & Leo, Chaos & Order | — | ★★ | a card the first time each turn you place a counter |

### Batch 3 (61–79)
| Card | 4? | Verdict | Note |
|---|---|---|---|
| Biomancer's Familiar | — | ★★ | creature abilities cost {2} less (power-ups, transforms; not Mister Fantastic's {R}{G}{W}{U}) |
| Genghis Frog | — | ★ | Mutagen per Mutant entering |
| Mikey & Don, Party Planners | MV | ★★ | cast Mutants and lands off the top; ward {2} |
| Roalesk, Apex Hybrid | P | ★★ | two counters on enter; proliferates twice on death |
| Sally Pride, Lioness Leader | T | ★★ | tokens per nontoken creature; counters on attack |
| Donatello, the Brains | T | ★ | extra Mutagen per token batch |
| Irma, Part-Time Mutant | — | ★★ | becomes a copy of your best creature each combat, plus a counter |
| Mondo Gecko | — | ◇ | |
| Ms. Marvel, Kamala Khan | T | ★★ | draws whenever a spell targets your creature (Mutagen, Miles, Ajani, the commander's counters are abilities — spells only) |
| Namor the Sub-Mariner | T | ◇+ | needs blue noncreature spells |
| Baxter, Fly in the Ointment | MV | ★ | countered creatures fly on enter/attack |
| Namor, Scourge of the Seas | P,T | ★★ | connive every combat |
| Wiccan, Rising Magician | P,T | ★★ | noncreature spell → blink a permanent (re-buy enters triggers) |
| The Scarlet Witch | — | ◇ | discounts mana-value-4+ instants and sorceries |
| Raphael, the Nightwatcher | MV | ★★★ | your attackers have double strike |
| Slash, Reptile Rampager | — | ★★ | 2 damage to each opponent per creature entering |
| Old Hob, Alleycat Blues | P,T | ★ | a temporary token each combat |
| Raphael, the Muscle | P,T | ★★★ | doubles damage from countered creatures |
| Namor, Atlantean King | — | ★ | Merfolk per noncreature spell |

## 5. Consolidated plan (live)

**★★★ core (14):** Human Torch, Mister Fantastic, The Thing, Hulk, Brutal Brawler, Doc
Samson, Shang-Chi, Martial Mentor, Wolverine, Fierce Fighter, Black Panther, Vanguard,
Storm, Windrider, Spider-Man India, Michelangelo, Weirdness to 11, Michelangelo, Mutant BFF,
Raphael, the Nightwatcher, Raphael, the Muscle.

**★★ strong (≈30):** Invisible Woman, Peter Parker, Bruce Banner, Jennifer Walters, Heroic
Intervention, Goliath, Miles Morales, Shang-Chi, Master of Kung Fu, Hulk, Strongest There
Is, Wolverine, Claws Out, Colossus, Storm, Shaker of Skies, Big Bertha, Scarlet Spider, Hulk,
Gamma Goliath, Ms. Marvel, Elastic Ally, She-Hulk, Attorney-at-Law, Silk, Ajani, Sigarda,
Web-Warriors, Beast, Storm, Force of Nature, Mona Lisa, Leatherhead, Swamp Stalker,
Michelangelo, Improviser, Mutagen Man, Mikey & Leo, Biomancer's Familiar, Mikey & Don,
Roalesk, Sally Pride, Irma, Ms. Marvel, Kamala Khan, Namor, Scourge of the Seas, Wiccan,
Rising Magician, Slash.

**★ fillers:** Flatman, Giant-Man, Earth's Mightiest Heroes, The Thing, Ben Grimm,
Zanarkand, Wolverine, Best There Is, Black Panther, Wakandan King, Ant-Man ×2, Darwin,
Black Tom Cassidy, Venus, Groundchuck & Dirtbag, Leatherhead, Iron Gator, Genghis Frog,
Donatello, the Brains, Baxter, Old Hob, Namor, Atlantean King.

**From OUTSIDE the pile (the draft must add):** ~12 noncreature interaction spells, ideally
mana value 4 (F1 + F3), e.g. owned Terrific Team-Up, Polliwallop, Kraven's Last Hunt, Annie
Joins Up, Tractor Beam, Glen Elendra's Answer, Day of Judgment, Chandra, Torch of
Defiance, Armor Wars; ramp and four-colour fixing (36–38 lands).

**PROTECT (the cut ranking cannot see these):** the commander; Doc Samson, Michelangelo,
Weirdness to 11 and Shang-Chi, Martial Mentor (multipliers whose value is in the rest of
the deck); Mister Fantastic (copies the commander's trigger).
