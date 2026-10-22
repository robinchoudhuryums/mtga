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

- `pool.py --legal brawl` is the 60-card format (G-08); every Historic Brawl search here must
  say `--legal "historic brawl"`. The first fetch-land sweep used the wrong one and showed 9
  of the 21 fetches.

## 3. Cross-batch observations

- **B1:** the pile's best cards are the ones that bridge two engines — Killmonger (sacrifice +
  removal), Origin of Black Widow (edict + deathtouch turn + a Saga sacrifice), Vraska,
  Betrayal's Sting (draw + proliferate + removal + finisher). Pure poison cards (Venerated
  Rotpriest, Viral Spawning, Interrogators) grade low under S5.
- **B1:** the pile has almost NO land cards (Mirrex only), yet S2 says lands are the engine.
  The manabase will be built from outside the pile — self-sacrificing lands first.
- **B2:** Long Feng, Jenova and Vorinclex are the Szarel-power layer (S3). With all three, a
  single fetch can put 5+ counters somewhere — the engine is power growth, not trigger count.
- **B2:** the planeswalkers (four Vraskas, two Garruks, Nissa, Tyvar, Lukka) are where the
  pile's removal lives, and Vorinclex doubles their loyalty — a planeswalker sub-package.
- **B3:** the deathtouch-evasion count (S6) inside the pile: Szarel (flying), Kura, Glissa
  Sunslayer (first strike), Rhonas's trample, Hunter's Axe, Vraska Regal Gorgon/Relic Seeker
  menace, Rattleback menace. Enough that Fynn connects, not so many that poison is the main
  clock.
- **B3:** TWO variant-deck signals, neither strong enough to split off: a Jund landfall build
  (Omnath, Phylath, Glacier Godmaw — red-heavy, S8 says no) and a pure poison build (toxic
  creatures from ONE — the pile holds five; the pool holds ~40, below).

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

### Batch 1 — cards 1–33

| # | Card | Verdict | Note |
|---|------|---------|------|
| 1 | The Serpent Society | ★★ | 3/4 deathtouch for 3; *another deathtouch creature dies → each opponent sacrifices a nontoken creature*. Sacrificing one of our deathtouchers to an outlet on our turn is an edict AND a Szarel trigger. The ward-five-poison is the opponent's cost. |
| 2 | Kraven the Hunter | △ | Draws only when THEIR biggest creature dies; a deathtouch blocker does that, but it is a 4/3 trample with no other link. |
| 3 | Atlas, Sizable Stooge | ✗ | Life on attack per power-4 creature; nothing the engine asks for. |
| 4 | Kraven, Proud Predator | △ | Power = greatest MV we control (~6–7 late); a vigilant beater, no engine link. |
| 5 | Absorbing Man and Titania | △ | Doubles DAMAGE; toxic and Fynn's poison are fixed counts, so it does not double the poison clock. |
| 6 | Killmonger, Scourge of Wakanda | ★★★ | ETB: sacrifice another creature → destroy target nonland permanent. Removal, an S1 trigger (nontoken fodder), and +2/+1 once two creature cards are in the yard. |
| 7 | Titania, Rugged Rumbler | ★ | 5/5 ward for 3. Its additional cost is upside here (G-41): discard a LAND and Szarel replays it from the graveyard. |
| 8 | Rhino, Barreling Brute | ✗ | {3}{R}{R}{G}{G}: double red for a beater in a red-splash deck (S8). |
| 9 | Abomination, Terrifying Titan | △ | A 7-mana fight. Removal of last resort. |
| 10 | Super-Adaptoid | △ | Power = legendary creatures; copies keywords. Cute, no engine. |
| 11 | Mister Hyde, Monster Within | ★ | Upkeep: remove a counter from a creature you control → draw. Szarel hands out counters every turn, so this is a card a turn for a 3-drop. |
| 12 | Undercover Skrull | ★ | {T}: any colour — turn-2 fixing toward {B}{R}{G}; grows with two creature cards in the yard. |
| 13 | Eddie Brock // Venom | ◇ | ETB returns an MV≤1 creature (Elvish Reclaimer, Grist, Emissary); Venom sacrifices a creature on attack (an S1 trigger) to draw X and cheat. The flip costs 6. |
| 14 | Lord Dregg, Insect Invader | ◇ | Disappear fires on ANY permanent leaving — every land sacrifice — so a 1/1 flier each end step; its draw sacrifices TOKENS (no Szarel). |
| 15 | Lukka, Bound to Ruin | ★ | +1 creature mana, −1 a toxic 3/3, −4 damage equal to our greatest power — Szarel's counters make that a board wipe. |
| 16 | Mirrex | ◇ | Toxic Mites for {3}; colourless otherwise. A mana sink, not a clock. |
| 17 | Vraska, Betrayal's Sting | ★★★ | 0: draw + PROLIFERATE (poison AND +1/+1 counters), −2 removal, −9 poison to nine. With Vorinclex it enters at 12 and −9 is 18 poison: the S5 finisher. |
| 18 | Persuasive Interrogators | ◇ | 6-drop: Clue → 2 poison when cracked. Clues are tokens (S1). |
| 19 | Fynn, the Fangbearer | ★★★ | The poison converter (S4): every deathtouch hit is 2 poison. A 2-drop. |
| 20 | Venerated Rotpriest | △ | Poisons when OUR spell targets our creature; the deck has ~3 such spells. |
| 21 | Infectious Bite | ★★ | {1}{G} instant bite — damage equal to power, and Szarel's counters make power large — plus a poison. Cheap interaction. |
| 22 | Viral Spawning | ◇ | A toxic 3/3 with corrupted flashback. Poison-only (S5). |
| 23 | Hapatra, Vizier of Poisons | ◇ | Snakes whenever WE place −1/−1 counters; needs combat damage first. |
| 24 | Necrogen Rotpriest | ◇ | Toxic payoff in a deck with ~4 toxic creatures; its deathtouch grant is the useful half. |
| 25 | Phyrexian Atlas | ◇ | A 3-mana any-colour rock; corrupted drain is a bonus. |
| 26 | White Widow, Yelena Belova | ★ | 2-drop deathtouch; counters on deathtouch hitters. Feeds Fynn. |
| 27 | Ammit Eternal | ✗ | Shrinks every time they cast a spell. |
| 28 | Origin of Black Widow | ★★ | I edict, II team deathtouch (a Fynn turn), III drain — and the Saga's own sacrifice after III is an S1 trigger. |
| 29 | Overkill | ★ | Instant hard removal (−0/−9999), 3 mana. |
| 30 | Ozai's Cruelty | ✗ | 2 damage and a 2-card discard; no engine role. |
| 31 | Rattleback Apothecary | ◇ | Deathtouch; a crime grants MENACE (S6 — evasion for Fynn). Crimes come from targeting their side. |
| 32 | Hidetsugu, Devouring Chaos | ★ | {B}, sacrifice a creature: scry 2 — a 1-mana nontoken outlet (S1); red impulse + damage late. |
| 33 | Pillage the Bog | △ | Selection scaled by lands; we would rather be playing a land. |

### Batch 2 — cards 34–66

| # | Card | Verdict | Note |
|---|------|---------|------|
| 34 | Seedship Broodtender | ★★ | ETB mill 3 (lands milled are playable, S2); sacrifice ITSELF → reanimate a creature: a nontoken self-sacrifice on our turn. |
| 35 | Vraska Joins Up | ★ | Deathtouch counters on the whole board (every attacker carries Fynn's poison) and a draw per legendary hitter — Szarel, Fynn and most of the pile are legendary. |
| 36 | Witherbloom Command | ★ | Two of: mill 3 + return a land, −3/−1, a small artifact/enchantment kill, drain 2. Flexible cheap interaction. |
| 37 | Dina, Essence Brewer | ★★ | Draw on the first creature sacrifice each turn; {2},{T}, sacrifice another creature → life and counters equal to its power. An outlet that pays twice. |
| 38 | Gorma, the Gullet | ◇ | Grows on deaths; nontoken creatures enter with counters per death. Good with an aristocrats turn, quiet otherwise. |
| 39 | Honest Rutstein | ★ | Regrowth on entry; creature spells cost {1} less. |
| 40 | Long Feng, Grand Secretariat | ★★★ | Every land or creature we sacrifice → a +1/+1 counter on any creature we control — **including Szarel** (S3). Order it above her trigger and each fetch grows her power before she resolves. |
| 41 | Pharika, God of Affliction | △ | Exiles creature cards from a graveyard and gives the owner a deathtouch Snake; rarely a creature here. |
| 42 | Sarulf, Realm Eater | △ | The exile wipe is symmetric over nonland permanents of MV ≤ counters (S9): it takes our cheap engine pieces. |
| 43 | Tyvar, Jubilant Brawler | ◇ | Creature abilities ignore summoning sickness (Elvish Reclaimer, Sprouting Goblin, Dina tap the turn they land); −2 reanimates an MV≤2 creature (Fynn, Bushmaster). |
| 44 | Uurg, Spawn of Turg | ★★ | {B}{G}, sacrifice a land: gain 2 — an on-demand land outlet (S2); power = lands in the yard; upkeep surveil fills it. |
| 45 | Vraska, the Cutting Glare | ★★ | 4/4 deathtouch for 3; with six lands, destroy any permanent. Easy to hit in a land deck. |
| 46 | Boneyard Lurker | ◇ | Mutate returns a permanent card (a land, or a dead engine piece) to hand. |
| 47 | Binding the Old Gods | ★★★ | I removal, II a Forest onto the battlefield, III team deathtouch, then the Saga's sacrifice — an S1 trigger. Four jobs. |
| 48 | Culling Ritual | ✗ | S9: destroys every MV ≤2 nonland permanent, ours included — Fynn, Bushmaster, White Widow, Elvish Reclaimer. |
| 49 | Daemogoth Titan | ★ | 11/10 for four hybrid pips; attack or block → sacrifice a creature (a nontoken one is an S1 trigger). |
| 50 | Jenova, Ancient Calamity | ★★★ | Each combat, counters equal to Jenova's power on another creature — Szarel's counters on Jenova raise that, and Jenova can target Szarel back (S3 loop). A Mutant dying on our turn draws its power: sacrificing a pumped Mutant to Dina/Hidetsugu is a big draw. |
| 51 | Nissa of Shadowed Boughs | ★ | Landfall loyalty (a fetch is two), +1 untaps a land, −5 reanimates with counters. |
| 52 | Back for More | ◇ | 6-mana reanimate + fight. |
| 53 | Garruk, Cursed Huntsman | ★★ | Wolves, −3 removal + draw, a +3/+3 trample emblem. |
| 54 | Casualties of War | ★★ | Up to five removal targets for 6. |
| 55 | Izoni, Thousand-Eyed | ◇ | Insects per creature card in the yard; its outlet draws, but its fodder is tokens (no S1). |
| 56 | Vraska, Relic Seeker | ★★ | +2 menace Pirates, −3 removal. |
| 57 | Beledros Witherbloom | ◇ | A Pest every upkeep; untaps lands for 10 life. Slow. |
| 58 | Vraska, Regal Gorgon | ★ | +2 a counter and menace — on Szarel, that grows her (S3) — −3 removal. 7 mana. |
| 59 | Pathbreaker Ibex | ★ | Attack: team +X/+X and trample where X is our greatest power. Szarel's counters make X big; a finisher. |
| 60 | Swampbenders | △ | Makes every land a Swamp; P/T = Swamps. No link to the plan. |
| 61 | Tectonic Split | ★ | Sacrifice half our lands as a COST — that is N Szarel and Long Feng triggers at once — then replay them one per turn while every land taps for three. Hexproof. A combo-ish payoff of S2. |
| 62 | Vorinclex, Monstrous Raider | ★★★ | Doubles every counter we place: Szarel's, Long Feng's, loyalty, poison. Enables the S5 finisher. |
| 63 | Flora Colossus | △ | */* lands, hexproof; a big body only. |
| 64 | Ferrafor, Young Yew | ★ | {T}: double each counter on a creature — on a Szarel-pumped creature that is a lot. 7 mana. |
| 65 | Glacier Godmaw | ◇ | Landfall team pump + haste; its Lander is a token. |
| 66 | Nyxbloom Ancient | △ | Tripled mana; this deck is limited by triggers, not mana. |

### Batch 3 — cards 67–99

| # | Card | Verdict | Note |
|---|------|---------|------|
| 67 | Avatar Kyoshi, Earthbender | ◇ | 8 mana: an 8/8 land-creature every combat that returns if it dies. Strong, slow. |
| 68 | Zopandrel, Hunger Dominus | ★ | Doubles the team's P/T each combat; sacrifice two other creatures for indestructible — two S1 triggers if both are nontoken. |
| 69 | Last March of the Ents | ◇ | 8 mana: draw equal to our greatest toughness and dump creatures. |
| 70 | Baba Lysaga, Night Witch | ★★★ | {T}, sacrifice up to three permanents: with three card types among them, drain 3 and draw 3. A land + a creature + a Saga/artifact is three S1 triggers and three Long Feng counters in one activation. |
| 71 | Bebop & Rocksteady | ★★ | 7/5 for 3; on attack or block sacrifice a permanent — sacrifice a LAND, an S1 trigger, and replay it. A Mutant for Jenova. |
| 72 | Exdeath, Void Warlock | ◇ | Transforms at six permanent cards in the yard (lands count); Neo Exdeath's power is that count. |
| 73 | Roxanne, Starfall Savant | △ | Meteorite tokens; no link. |
| 74 | Phylath, World Sculptor | ◇ | Plants per basic; landfall puts four counters on a Plant — a fetch is two landfall. Red. |
| 75 | Dragonlord Atarka | ★ | 7 mana 8/8 flier, 5 damage divided on entry. |
| 76 | Omnath, Locus of Rage | ★ | A 5/5 per landfall; two per fetch. {R}{R} is the cost (S8). |
| 77 | Slimefoot and Squee | ◇ | Recursion; its Saprolings are tokens (S1). |
| 78 | Noxious Assault | △ | Team +2/+2 and poison per blocker. Poison-only finisher (S5). |
| 79 | Virulent Silencer | ✗ | Needs nontoken ARTIFACT creatures; the pile has one. |
| 80 | Aphelia, Viper Whisperer | ◇ | Deathtouch 2-drop that makes deathtouch Snakes; the half-life ability wants Gorgons/Snakes (Serpent Society, Vraska the Cutting Glare). |
| 81 | Gilt-Leaf Alchemist | △ | Needs two Elf cards in the graveyard. |
| 82 | Grist, Voracious Larva | ◇ | 1-drop deathtouch; flips only when a creature enters from the graveyard (Broodtender, Eddie Brock, Back for More). The walker side is removal and tokens. |
| 83 | Hunter's Axe | ◇ | +2/+0 and trample or deathtouch on attack: a Fynn carrier (S6). Equip 2. |
| 84 | Virulent Emissary | △ | 1-drop deathtouch. Filler. |
| 85 | Bushmaster, Coiled Henchman | ★★★ | Every other creature with a +1/+1 counter has deathtouch. The S4 bridge: Szarel's counters become deathtouch, Fynn turns it into poison. |
| 86 | Kappa Tech-Wrecker | ◇ | Deathtouch counter; on hit, exile an artifact or enchantment. |
| 87 | Noxious Newt | ★ | A deathtouch mana dork for 2. |
| 88 | Serpent-Blade Assailant | ◇ | Backup a counter + deathtouch for a turn. |
| 89 | Rhonas the Indomitable | ★★ | 5/5 deathtouch indestructible for 3 that attacks once we have power 4+ (Szarel's counters make that early); {2}{G} gives +2/+0 and TRAMPLE — a deathtouch trampler deals almost all its damage to the player (S6). |
| 90 | Garruk Relentless | ★★ | 0: 3 damage to a creature; wolves; the flip side sacrifices a creature to TUTOR (an S1 trigger) and makes deathtouch Wolves. |
| 91 | Hit-Monkey | ★ | Hexproof deathtouch haste reach — the safe place to put Szarel's counters. |
| 92 | Tyvar Kell | △ | Elves; the pile has three. |
| 93 | Kura, the Boundless Sky | ★ | Flying deathtouch 4/4 (an evasive Fynn carrier); on death, three lands to hand. |
| 94 | God-Eternal Rhonas | ★ | Deathtouch; doubles the team's power on entry. |
| 95 | Majestic Myriarch | ◇ | */* = 2× creatures; copies keywords. |
| 96 | Glissa Sunslayer | ★★ | First strike + deathtouch; on hit, draw or removal. Hard to block, carries Fynn's poison. |
| 97 | Vraska, Swarm's Eminence | ★ | Counters on deathtouch hitters; −2 deathtouch Assassins. |
| 98 | Glissa, Herald of Predation | ◇ | Incubator counters and Phyrexian deathtouch; slow. |
| 99 | The Gitrog Monster | ★★★ | Upkeep land sacrifice (an S1 trigger, on our turn), an extra land drop (doubles S2 throughput), and a draw each time a land card hits the graveyard. The engine's second half. |

## 5. Consolidated plan (live)

**Scratch draft v1** (scratchpad `d89-v1.txt`, 100 cards, every line from `deck.py resolve`):
44 pile cards + the commander + 17 outside nonland + 38 lands. Measured 2026-10-22: **legal** in Historic
Brawl; floor **A** (interaction 18 +1?, card advantage 11, sum 29 against A's 12 / 19);
protection 6; avg MV 3.53; curve 1/2/13/18/14/5/7/2 (0–7+); 40 creatures; keepable 81.2%
(96.5% within two sevens); sources B 25 / R 19 / G 24, Szarel 84.7% on turn 5. Shape WIDE.
`similar`: closest is deck 8 at 74% on generic themes only; deck 31 (Pox, BG Standard
poison) 73% sharing 3 cards — distinct deck.

### The list, by job

- **Commander:** Szarel, Genesis Shepherd.
- **Land-sacrifice engine (S2), nonland — 12:** The Gitrog Monster, Uurg, Baba Lysaga,
  Elvish Reclaimer*, Sprouting Goblin*, Zuran Orb*, Hearthhull, the Worldseed*, Titania,
  Protector of Argoth*, Azusa*, Crop Rotation*, Squirrel Wrangler*, Tectonic Split.
  (*outside the pile)
- **Szarel's power / counters (S3) — 9:** Long Feng, Jenova, Vorinclex, Bushmaster, Mister
  Hyde, Evolution Sage*, Vraska, Swarm's Eminence, White Widow, Ancient Greenwarden* (doubles
  landfall; a second "lands from graveyard" for when Szarel is in the command zone).
- **Deathtouch → poison (S4–S6) — 11:** Fynn, The Serpent Society, Glissa Sunslayer, Vraska,
  the Cutting Glare, Rhonas the Indomitable, Kura, Hit-Monkey, Vraska Joins Up, Vraska,
  Betrayal's Sting, Bloated Contaminator*, Triumph of the Hordes* (team infect + trample for a
  turn: the poison finisher on a countered board).
- **Nontoken creature outlets (S1) — 8:** Dina, Killmonger, Hidetsugu, Bebop & Rocksteady,
  Daemogoth Titan, Yawgmoth* (also proliferate and draw), Garruk Relentless, Seedship
  Broodtender (sacrifices itself).
- **Ramp — 5:** Undercover Skrull, Noxious Newt, Lotus Cobra*, Tireless Provisioner*,
  Titania, Rugged Rumbler (a 5/5 whose discard cost feeds lands back).
- **Removal — 13:** Infectious Bite, Overkill, Infernal Grasp*, Heartless Act*, Witherbloom
  Command, Origin of Black Widow, Binding the Old Gods, Lukka, Garruk, Cursed Huntsman,
  Casualties of War, Vraska, Relic Seeker, Vraska, Regal Gorgon, Dragonlord Atarka.
- **Value:** Nissa of Shadowed Boughs, Honest Rutstein, Lord Dregg (a flier every turn a land
  is sacrificed).
- **Lands — 38 (21 sacrifice themselves, S2):** fetches Evolving Wilds, Terramorphic Expanse,
  Vibrant Cityscape, Hobbit Hole, Elven Passage, Twisted Landscape, Riveteers Overlook, Escape
  Tunnel (or: a power-≤2 creature is unblockable — Fynn), Promising Vein, Fabled Passage,
  Prismatic Vista, Misty Rainforest, Polluted Delta, Scalding Tarn; repeatable spells Memorial
  to Folly, Memorial to Unity, Hidden Necropolis, Hidden Nursery, Skemfar Elderhall,
  Nurturing Peatland, Ifnir Deadlands; Lotus Field (sacrifices two lands on entry); duals
  Overgrown Tomb, Blood Crypt, Stomping Ground, Command Tower, Ziatora's Proving Ground;
  4 Swamp, 4 Forest, 3 Mountain.

### Hand counts the tools cannot make (S10)

- **Nontoken sacrifice sources:** 21 self-sacrificing lands + Lotus Field, 12 land outlets,
  8 creature outlets, 2 Sagas. Szarel fires on most turns from a land drop alone.
- **Basics are a finite fetch pool:** 11 basics against 11 basic-fetchers that REPLAY. A long
  game empties the basics; after that a fetch still sacrifices (a failed search is legal), so
  Szarel still fires — only the ramp stops.
- **Things that grow Szarel:** Long Feng (per land/creature to the graveyard), Jenova (each
  combat), Vraska, Regal Gorgon +2, Vorinclex (doubles all of it).

### Protect list — what `cuts` cannot see

`cuts` ranked Azusa and Lotus Cobra as the two weakest cards (fit 14 and 11). Both are S2
multipliers. Protect: **Azusa, Zuran Orb, Long Feng, Gitrog, Bushmaster, Fynn, Vorinclex,
Jenova, Lotus Field, Tectonic Split, Elvish Reclaimer** — each one's value is in the rest of
the deck (land-drop count, counter count, deathtouch count), which no ranking term reads.
`engines` also reports "counters: no payoff" — Bushmaster, Vorinclex and Rhonas are the
payoffs it does not recognise.

### Open decisions for the owner

1. **How much poison?** v1 runs poison as the second clock: Fynn + Bushmaster + deathtouch,
   proliferate (Vraska, Evolution Sage, Bloated Contaminator, Yawgmoth), two finishers
   (Triumph; Vraska −9, 18 poison with Vorinclex). A poison-FORWARD swap set is available:
   Necrogen Rotpriest, Venerated Rotpriest, Persuasive Interrogators, Venomous Brutalizer
   (toxic 3 + proliferate), Skithiryx (flying infect) for Daemogoth Titan, Squirrel Wrangler,
   Dragonlord Atarka, Lord Dregg, Honest Rutstein.
2. **Rare fetches.** Fabled Passage, Prismatic Vista, Misty Rainforest, Polluted Delta and
   Scalding Tarn are the untapped fetches; commons (Promising Vein, Shire Terrace) do the
   same job a turn slower.

### Pile cards left out (55), by reason

- **Red-heavy (S8):** Rhino, Omnath, Phylath, Roxanne, Kraven Proud Predator, Absorbing Man
  and Titania, Abomination.
- **Poison-only, below S5:** Venerated Rotpriest, Viral Spawning, Necrogen Rotpriest,
  Persuasive Interrogators, Mirrex, Noxious Assault, Virulent Silencer, Phyrexian Atlas,
  Hapatra. (Option 1 above brings some back.)
- **G-42 conflicts (S9):** Culling Ritual, Sarulf, Pharika.
- **Tokens, not nontoken sacrifices (S1):** Izoni, Slimefoot and Squee, Beledros.
- **7–8 mana, outclassed by the kept top end:** Ferrafor, Zopandrel, Avatar Kyoshi, Last
  March, Flora Colossus, Nyxbloom, Glacier Godmaw, Pathbreaker Ibex (cut for Greenwarden).
- **Filler deathtouch the list has enough of:** Aphelia, Virulent Emissary, Grist, Kappa
  Tech-Wrecker, Serpent-Blade Assailant, Gilt-Leaf Alchemist, God-Eternal Rhonas, Hunter's
  Axe, Rattleback Apothecary.
- **No engine link:** Kraven the Hunter, Atlas, Super-Adaptoid, Eddie Brock, Ammit Eternal,
  Ozai's Cruelty, Pillage the Bog, Gorma, Tyvar Jubilant Brawler, Boneyard Lurker, Back for
  More, Swampbenders, Exdeath, Majestic Myriarch, Glissa Herald, Tyvar Kell.

### Tool holes found (record only, G-67)

- Azusa and Lukka score no role (extra land drops; Lukka's −4 is removal).
- `engines` does not read Bushmaster / Vorinclex / Rhonas as counters payoffs.
- No surface counts nontoken sacrifices or a commander's trigger (S10).

### Craft cost (information only)

67 of the 100 read unowned (owned counts are stale lower bounds): 20 mythic, 25 rare,
15 uncommon, 7 common.
