# Bear-Wolf pile (deck 105) — analysis (TEMPORARY working doc)

**Status: 18 swaps APPLIED 2026-11-23 (§7); two adds held pending two cuts.** 100 new cards the owner added for deck 105 (Den of Bears and Wolves,
Historic Brawl, Sarulf, Realm Eater). Delete once the swaps land and the findings are folded into
deck 105's `#: notes:`. The board is the existing Builder project `builds/bear-wolf`.

**Source list:** `.cycle/bear-wolf-pile.txt` (100 cards; all resolve, all Historic Brawl legal,
all inside Sarulf's black-green identity). `screen`: 16 KEY / 25 role-player / 59 tangential;
two ★ strict upgrades flagged (of Llanowar Elves and of Cultivate).

## 1. The decision framework

Deck 105 live vector (2026-11-22): floor A · interaction 16 · card advantage 14 · protection 7 ·
board power 124 · avg MV 3.45 · 18 Bears · 10 Wolves · WIDE (wide 14 / tall 1).

- **F1 — Bears ENTERING is the first number.** Ayula (in the 99) turns each entering Bear into
  two counters or a fight; Beorn the Fierce pumps Bears and makes a creature a Bear each combat;
  Goreclaw discounts power-4 creatures. Bear TOKENS count.
- **F2 — the POWER-4 GATE.** Garruk's Uprising, Colossal Majesty, Garruk, Curse Breaker, Vaultborn
  Tyrant, Elemental Bond, Rhonas, Fanatic of Rhonas, The Chief Warg, Wilderland Scrounger all read
  "a creature with power 4 or greater". A body that is 4+ power on arrival is worth more than its
  text; a card that only pays once the gate is on is a CONSUMER (deck 69's lesson: don't stack them).
- **F3 — SARULF'S WIPE IS SYMMETRICAL.** Removing its counters exiles EACH OTHER nonland permanent
  with MV ≤ N, yours included. Cheap permanents (1–3 MV) are the ones a wipe takes; 4+ MV threats
  and indestructible / self-returning cards survive. Not a reason to cut every cheap card — the
  wipe is optional — but a tiebreak between two similar cards.
- **F4 — Wolves are the second tribe** (Nightpack Ambusher and Spider-Ham pump them). A Wolf card
  is worth a little more than its text; a Werewolf only counts for Wolf-and-Werewolf cards.
- **F5 — interaction is already 16** (A needs 12 at 100 cards). New removal must beat a current
  piece, not just be removal.
- **F6 — card advantage is 14**; a repeatable draw engine that reads the deck's real state (big
  bodies attacking) is the most valuable new role.
- **F7 — ownership is information only** (Player Profile).

## 2. Standing error list

- **E1 — `screen`'s ★ STRICT UPGRADE is a text-containment test.** It called Argoth a strict
  upgrade of Llanowar Elves (a land is not a dork) and Flare of Cultivation of Cultivate (true
  here: same effect, plus a free alternative cost, at the price of a GG pip).
- **E2 — a creature's death is Sarulf's fuel.** Sarulf counts opposing permanents going to the
  GRAVEYARD. An exile-instead replacement on their creatures (Head of the Hunt, in the deck)
  stops Sarulf's counters from creature kills, and switches Kraven off too. Check any
  exile-on-death card against Sarulf before adding or keeping it.

## 3. Cross-batch observations

- **Counters are the axis this pile adds most to.** Winding Constrictor, Avabruck Caretaker,
  Fight Rigging, Path of Discovery and World War Hulk all put counters on creatures. Each
  counter both opens the power-4 gate (F2) and, through Constrictor, charges Sarulf.
- **Repeatable draw is the other** (F6): Owlbear Shepherd, Toski, Werewolf Pack Leader, Chevill,
  Kraven and Chimil. The deck goes from 14 card advantage to 17 with the tier-1 package.
- **Removal doubles as Sarulf's fuel**, so cutting it has a cost beyond the interaction count.
  The plan takes interaction from 16 to 14, still above the A line of 12; Garruk Relentless
  replaces one spell with a repeatable fight.
- **A no-spell-turn cluster is real but small (batch 4).** Day becomes night when the active
  player casts no spells on their turn, and two spells in a turn flip it back. The deck already
  holds a payoff (Nightpack Ambusher's end-step Wolf) and spell-less actions: three
  planeswalkers, Ranger Class levels, Mother Bear's graveyard ability, flash creatures cast on
  the opponent's turn, and Argoth if added. Howlpack Piper is the piece that resolves the
  tension with Ayula, which wants Bears to ENTER, not to be cast. So take Piper, Edgar and
  Avabruck; leave Weaver of Blossoms, Hound Tamer and Wolfkin Outcast, whose night sides are
  smaller. In one-on-one the opponent controls half the clock, so night is a bonus, never the plan.
- **Proliferate is a second counters axis (batch 4).** Every proliferate grows the
  Ayula-counter Bears AND Sarulf. Note the tools score proliferate as no role (a known
  classifier hole), so `cuts` and the card-advantage figure under-rate these cards.
- **No variant signal.** The rejected cards are mostly landfall and graveyard engines, which
  are already their own decks in the roster.

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

### Batch 1 (cards 1–34)

| # | Card | Verdict | Note |
|---|------|---------|------|
| 1 | Sauron, the Necromancer | ★ | Re-read in batch 4, unchanged. A 5-mana 4/4 menace (F2). Its attack trigger needs a creature card in YOUR graveyard, and that graveyard stays thin here: Sarulf's wipe exiles rather than bins, so only combat trades and the opponent's removal fill it (Mother Bear and Vastlands Scavenger add a few). Read the trigger as a bonus, the body as the card. |
| 2 | Flaxen Intruder // Welcome Home | ★ | Adventure makes three 2/2 Bears = three Ayula triggers (F1); the 1-drop half answers an artifact/enchantment. |
| 3 | Beorn's Hospitality | ◇ | Landfall counters; becomes a land-count Bear for 7. Slow. |
| 4 | Owlbear Shepherd | ★★ | Draws each end step when total power is 8+ — trivial with this board (F6). 3 MV (F3 risk). |
| 5 | Lukamina, Moon Druid | ★ | Re-graded in batch 4. Specialize (six lands, {3}, discard a green card or a Forest) makes Lukamina, Bear Form: a 4/4 trample Bear with 'other creatures you control get +1/+1 and have trample', so every 3-power Bear opens the gate (F2). The entry seek is a free land, and the form returns to base when it dies. Wolf Form needs a red discard, so it is out of reach in BG. Scorpion Form (black discard) is a deathtouch 4/4 that must be blocked. |
| 6 | Ursine Guide | ◇ | Already benched: its Bear Cub engine needs spells not from your starting deck. |
| 7 | Toski, Bearer of Secrets | ★★ | Indestructible; a card whenever any creature connects (F6). Must attack as a 1/1, but indestructible. |
| 8 | Titania's Command | ◇ | Two Bears (two Ayula triggers) plus counters on everything; 6 mana. Benched before. |
| 9 | Copper Host Crusher | ◇ | 8/8 trample hexproof Bear; Goreclaw makes it 6. Top-end only. |
| 10 | Argoth, Sanctum of Nature | ★★ | Untapped with a legendary green creature (Sarulf is one); {2}{G}{G}: a 2/2 Bear — an Ayula trigger mana sink. For a Forest. |
| 11 | Mirkwood | ★ | Tapped black-green dual that sacrifices for two counters on a Bear or Wolf. For a Forest. |
| 12 | Forebear's Blade | ★ | +3/+0 trample turns any 1-2 power body into a gate-opener (F2) and moves when it dies. |
| 13 | Nighthowl Pursuer | ◇ | 1-drop Wolf that is a 3/3 menace attacker once the gate is on (consumer, F2). |
| 14 | Ravening Warg | ◇ | 2-drop deathtouch Wolf; gate consumer. |
| 15 | Rhovanion Rampager | △ | Sacrifices a creature to grow; the deck does not want to sacrifice its bodies. |
| 16 | Vincent Valentine // Galian Beast | ★ | Counters equal to the power of each opposing creature that dies — 16 removal spells feed it; flips to trample lifelink. |
| 17 | Ascendant Packleader | ◇ | 1-drop Wolf that grows on every 4+ MV spell (most of the deck). F3 risk. |
| 18 | Tenacious Pup | △ | Cut once already: a 1/2 and a one-shot boon. |
| 19 | Packsong Pup | △ | Grows by one a turn with another Wolf; small. |
| 20 | Torgal, A Fine Hound | ◇ | Any-colour mana dork that is a Wolf; its Human clause is dead here. |
| 21 | Wargling | ◇ | Gate consumer (deck 69 trimmed it for that reason). |
| 22 | Werewolf Pack Leader | ★★ | 2-mana 3/3 that draws when you attack with total power 6+ (F6). Not a Wolf. |
| 23 | Cemetery Prowler | ★ | 3-mana 3/4 Wolf; graveyard exile on enter/attack and a creature discount. |
| 24 | Hound Tamer // Untamed Pup | ◇ | Counter sink; night side gives Wolves trample. Day/night is fiddly. |
| 25 | Howlpack Resurgence | ◇ | Flash Wolf anthem (+1/+1 trample) with 10 Wolves. |
| 26 | Howling Moon | ◇ | +2/+2 to a Wolf each combat; Wolf tokens on their second spell. |
| 27 | Shrill Howler | △ | Evasion against small blockers; slow to flip. |
| 28 | Varis, Silverymoon Ranger | ◇ | Ventures on creature casts; a dungeon completion makes one Wolf. Slow payoff. |
| 29 | Weaver of Blossoms | △ | 3-mana mana creature; the deck has better ramp. |
| 30 | Garruk Relentless | ★★ | Now legal (black-green): 3 damage to a creature, or a Wolf a turn; flips to deathtouch Wolves and a tutor. |
| 31 | Geistpack Alpha | ★★ | 4-mana 5/4 trample Wolf — a gate-opener on arrival (F2), Goreclaw-discounted; dies into a seek. |
| 32 | Lupine Harbingers | ★ | 4/4 haste trample Wolf; foretold it grows. |
| 33 | Howlpack Piper // Wildsong Howler | ★★ | Re-graded in batch 4. The engine of a no-spell turn: it puts a creature from hand onto the battlefield without casting it, so Bears still trigger Ayula on entry while the turn counts as spell-less. That makes it night, which flips Avabruck Caretaker and the Piper itself (look at six for a creature), and pays Nightpack Ambusher's and Edgar's end-step clauses. Untaps after a Wolf or Werewolf. |
| 34 | Mantle of the Wolf | ◇ | +4/+4 makes a gate-opener; two Wolves when it leaves. An Aura. |

### Batch 2 (cards 35–67)

| # | Card | Deck 105 | Note |
|---|---|---|---|
| 35 | Edgar, Moonlit Sovereign | ★ | Re-graded in batch 4. Flash, so cast it in the opponent's end step and pass your own turn with no spell: Edgar takes two counters, it becomes night, and Nightpack Ambusher (in the deck) makes a Wolf off the same clause. A 4/4 on arrival (F2), and {4}{G} spreads counters, which Constrictor and Hardened Scales add to. |
| 36 | Sage of Ancient Lore | △ | Draws one on entry, and its size is your hand size, so it is small in a deck that empties its hand. Werewolf, not Wolf. |
| 37 | Arlinn, Voice of the Pack | ◇ | Six mana for a Wolf-token walker. Wolves entering with a counter helps the gate, but it is slow and its static does nothing for Bears. |
| 38 | Avabruck Caretaker | ★★ | A hexproof 4/4 that puts two counters on another creature each combat, which turns a 2-power Bear into a gate-opener (F2). Its night side puts two counters on everything and gives the rest of the board hexproof: the deck's best protection card in the pile. MV 6, so it survives most Sarulf wipes (F3). |
| 39 | Flourishing Hunter | △ | A 6/6 Wolf body that gains some life. A Wolf count of one for six mana; the deck has better six-drops. |
| 40 | Wolfkin Outcast | ◇ | Costs four with a Wolf out (the deck has 10). 5/4 for the gate; its night side draws when Wolves die. Werewolf type, so it is not itself a Wolf. |
| 41 | Somberwald Beastmaster | ◇ | Seven mana for four bodies (a Wolf, a 3/3 and a 4/4 among them), and the tokens have deathtouch. Tokens are MV 0, so a Sarulf wipe takes all of them (F3). |
| 42 | Primal Witchstalker | ◇ | A 3-mana BG Wolf with menace that ramps a land back from a mill of four. Cheap Wolf count (F4); the deck already runs Fierce Witchstalker. |
| 43 | Sword of Body and Mind | ★ | +2/+2 turns any 2-power creature into a power-4 gate-opener (F2), protection from green covers the mirror, and a hit makes a Wolf (F4). MV 3, so it is exposed to a big Sarulf wipe. |
| 44 | Fuel Tank Feaster | ◇ | A 2-mana any-colour dork (Alchemy) that discounts your biggest creature each turn. The deck has three dorks already; a fourth is only worth it if the ramp suite is cut back elsewhere. |
| 45 | Fight Rigging | ★ | A counter on a creature every combat (F2 enabler), plus a free hideaway card once you have power 7. Big Bears, Lumra and Vaultborn reach 7. Repeatable and cheap. |
| 46 | Flare of Cultivation | ◇ | Ramp that can be free by sacrificing a nontoken green creature. The deck has 6 ramp spells plus Sarulf to protect; a sacrifice cost on a creature deck is a real cost. |
| 47 | Descendants' Path | ◇ | A free creature each upkeep when the top card shares a type with your board. With 37 creatures, about 37% of draws are creatures, and most share Bear or Wolf. Lands and noncreature spells whiff and go to the bottom. |
| 48 | World War Hulk | ★ | Chapter I makes the next green creature free, chapter II gives three counters (a 1-power Bear becomes a gate-opener, F2), chapter III doubles power with trample. A strong turn-5 play in a creature deck. |
| 49 | Omnipresence | △ | Eight mana. The deck wins by the time this resolves. |
| 50 | Etali, Primal Garden | ◇ | A 7/7 trampler (Alchemy) that casts a random Dinosaur free on entry and attack. Real value, but off-tribe, and actualize barely discounts it here. |
| 51 | Heirloom Epic | △ | Tapping creatures to draw is slow in a deck that wants to attack with them. |
| 52 | Monstrous Vortex | ◇ | Fires on power-5+ creature spells; the deck runs 8 (Beorns, Big Bears, Surrak and Goreclaw, Chief Warg's Company, Vaultborn, Rhonas). A free spell on each, but 8 of 37 creatures is a thin trigger. |
| 53 | Path of Discovery | ★ | Every creature explores: a land in hand or a +1/+1 counter. That counter takes a 3-power Bear to 4 (F2), and with 37 creatures it is repeatable card advantage (F6). |
| 54 | Chimil, the Inner Sun | ★ | A free MV-5-or-less card every end step (F6, repeatable), and your spells can't be countered. MV 6 colourless, so it survives most Sarulf wipes (F3). |
| 55 | Sentinel of the Nameless City | ★ | A 3-mana 3/4 vigilance that makes a Map on entry and every attack. Each Map is an explore, which means a counter or a land. Strong 3-drop, though not a Bear. |
| 56 | Mole Man, Moloid Master | △ | A landfall token maker. The deck has no landfall plan. |
| 57 | Wrenn and Realmbreaker | ◇ | Fixing the deck does not need. The +1 is a 3/3 attacker and the -2 digs for a permanent. Fine, not a fit. |
| 58 | Icetill Explorer | △ | A landfall and graveyard-lands engine; off plan. |
| 59 | Elemental Teachings | △ | Five mana for two tapped lands. |
| 60 | World Shaper | △ | A lands-recursion payoff with no lands plan behind it. |
| 61 | Nissa, Vital Force | ◇ | A 5/5 haste land each turn, which is a gate-opener (F2), and -3 regrows a permanent. A playable five-drop walker. |
| 62 | Ancient Greenwarden | △ | Doubles landfall triggers the deck does not have. A 5/7 reach body is all it gives. |
| 63 | Kamahl's Druidic Vow | ◇ | Sarulf satisfies the legendary-sorcery rule, and the deck has about 15 legendary permanents plus lands. An X spell that puts several onto the battlefield; strong late, weak early. |
| 64 | Nog, Ambitious Cadet | △ | A Ferengi with a land-recursion mode. Off plan. |
| 65 | Nissa of Shadowed Boughs | ◇ | BG walker that grows from land drops; its -5 puts a creature onto the battlefield with two counters. Slow to get there. |
| 66 | Badlands Revival | ◇ | Two-for-one recursion after removal. Sarulf exiles rather than sends to the graveyard, so it does not undo a wipe. |
| 67 | Glacier Godmaw | ◇ | A 6/6 trampler whose landfall pumps the team and gives haste. Seven mana; a finisher the deck does not need. |

### Batch 3 (cards 68–100)

| # | Card | Deck 105 | Note |
|---|---|---|---|
| 68 | Berserk | △ | Doubles a creature's power for one swing, then kills it if it attacked. One big hit for a creature you lose. |
| 69 | Burgeoning | △ | One-opponent Brawl gives about one extra land a turn cycle. Not the deck's problem. |
| 70 | Glimpse of Nature | △ | A burst-draw turn needs a hand of cheap creatures; this deck's creatures cost 3–5. |
| 71 | Hunter's Axe | ◇ | One mana, +2/+0: a 2-power Bear becomes a gate-opener (F2). Equip {2} each time, and the Sword and Forebear's Blade do the same job better. |
| 72 | Vraska, Swarm's Eminence | △ | A deathtouch-token planeswalker. The deck has few deathtouch creatures. |
| 73 | Vraska, Golgari Queen | ◇ | -3 destroys a nonland permanent with MV 3 or less, and +2 trades a spare permanent for a card. A fair replacement removal piece if one is cut (F5). |
| 74 | Tyvar, Jubilant Brawler | ◇ | Dorks and tap abilities work the turn they enter; -2 returns a 2-drop Bear. Modest. |
| 75 | Chevill, Bane of Monsters | ★ | A 2-mana deathtouch body that marks one opposing creature at a time and draws when it dies. With 16 removal spells and Ayula fights it is a repeatable draw (F6). |
| 76 | Fiend Artisan | ◇ | A creature tutor that needs a sacrifice. It can find Ayula or Goreclaw, but its size reads your graveyard and Sarulf exiles rather than bins. |
| 77 | Insidious Roots | △ | Tokens tap for mana and Plants grow when creature cards leave the graveyard. Off plan. |
| 78 | Vraska Joins Up | ◇ | Deathtouch counters on the team on entry, then a card whenever a legendary creature connects. About 14 legendary creatures here; the counters are not +1/+1 and do not open the gate. |
| 79 | Winding Constrictor | ★★ | Every counter you place gets one more. Ayula's two counters become three, Fight Rigging and Avabruck give more, and Sarulf itself gets two per opposing permanent instead of one, so its wipe charges twice as fast. A 2-mana 2/3. |
| 80 | Dina, Essence Brewer | △ | A sacrifice outlet. The deck has no sacrifice plan. |
| 81 | Kraven the Hunter | ★ | A 3-mana 4/3 trampler (power 4 on arrival, F2) that draws and grows whenever the opponent's biggest creature dies. Removal and fights trigger it. Note: Head of the Hunt (in the deck) exiles dying creatures instead, which switches Kraven off. |
| 82 | Sméagol, Helpful Guide | △ | Needs one of your creatures to die each turn. |
| 83 | Beifong's Bounty Hunters | ◇ | A 4/4 for 4 (F2) that turns each dying creature into a land creature with counters equal to its power. A sturdy body. |
| 84 | Culling Ritual | △ | Destroys every nonland permanent with MV 2 or less, including your own dorks, 2-drop Bears and Constrictor. Sarulf already gives the deck a wipe. |
| 85 | Host of the Hereafter | ◇ | A 4/4 for 4 whose counters move to another creature when it dies. Fine, not exciting. |
| 86 | Jenova, Ancient Calamity | △ | Gives counters equal to its own power, which starts at 1. Needs a pump first. |
| 87 | Mortality Spear | ◇ | An instant that destroys any nonland permanent. Four mana here, since the deck rarely gains life. A fair replacement removal piece (F5). |
| 88 | Kagha, Shadow Archdruid | △ | Graveyard casting off a mill of two. Off plan. |
| 89 | Rise of the Witch-king | ◇ | An edict that also costs you a creature, then returns a permanent. Symmetrical in a creature deck. |
| 90 | Deathbloom Ritualist | △ | Its mana scales with creature cards in your graveyard; this deck's graveyard stays small. |
| 91 | Diregraf Rebirth | ◇ | Reanimation with flashback. Undoes removal, but not a Sarulf wipe, which exiles. |
| 92 | Lord of Extinction | △ | Its size reads all graveyards; Sarulf exiles, so graveyards stay small here. |
| 93 | Ygra, Eater of All | ◇ | A 6/6 for 5 (F2) that grows whenever a creature dies. It also gives every opposing creature a 'sacrifice: gain 3 life' ability, which helps the opponent (owner's rule). |
| 94 | Back for More | ◇ | Instant reanimation plus a fight, for six mana. |
| 95 | Mycoid Resurrection | △ | Graveyard reanimation; the graveyard stays thin here. |
| 96 | The Last Ronin | ✗ | Chapter I destroys every creature, and this is a 37-creature deck. |
| 97 | Harness Infinity | ✗ | Swaps hand and graveyard for six mana with a BBB GGG cost. A graveyard deck's card. |
| 98 | Vraska, Regal Gorgon | △ | Seven mana. -3 destroys a creature and +2 opens the gate (F2), but the deck has cheaper removal. |
| 99 | Witherbloom, the Balancer | ★ | Affinity for creatures, so about 3 mana on a normal board, for a 5/5 flying deathtouch. It also gives instants and sorceries affinity, which discounts the removal. MV 8, so a Sarulf wipe never takes it (F3). |
| 100 | Old Stickfingers | △ | An X spell that fills the graveyard; its size reads creature cards there. |

### Batch 4 (owner's extension, 2026-11-22)

| # | Card | Deck 105 | Note |
|---|---|---|---|
| 101 | Cursebound Witch | △ | A 1/2 that drafts a card from its spellbook when it dies (Alchemy). Low impact in a 100-card creature deck. |
| 102 | Dark Ritual | △ | One burst of BBB for a card. Only black spells use it, and the deck's power is green. |
| 103 | Vraska, Betrayal's Sting | ★ | 0: draw a card and proliferate, every turn, which adds a counter to every creature with one, to Sarulf (a bigger wipe) and to Vraska. Repeatable draw (F6). Six mana. Its -2 turns a creature into a Treasure the OPPONENT keeps, which gives them mana, so it clashes with the owner's removal rule; treat it as a draw-and-proliferate walker. |
| 104 | Vat Emergence | ◇ | Reanimate from ANY graveyard, so it can steal the creature your removal just killed, then proliferate. Five mana. |
| 105 | Cankerbloom | ◇ | A 2-mana 3/2 that sacrifices to destroy an artifact or enchantment, or to proliferate. A flexible noncreature answer on a body. |
| 106 | Unnatural Restoration | ◇ | Two mana: regrow a permanent card and proliferate. Fine value, small. |
| 107 | Evolution Sage | ★ | Proliferate on every land drop, twice with Evolving Wilds, Fabled Passage or Prismatic Vista. Grows the Ayula-counter Bears and charges Sarulf each turn. A 3/2 for 3. |
| 108 | Urban Daggertooth | ◇ | A 4/3 vigilance for 4 (F2). Proliferates whenever it is dealt damage, which a fight or a block does. |
| 109 | Hardened Scales | ★ | One mana: each +1/+1 counter placement on a creature gets one more: Ayula's two become three, and Sarulf's counters count. It stacks with Winding Constrictor. MV 1, so every Sarulf wipe takes it (F3). |
| 110 | Mythweaver Poq | ★ | Its size is your land count (power 4+ by turn four, F2), and each turn it conjures a copy of the land you played, so a fetch land is played twice. Ramp on a body, Alchemy. |
| 111 | Stable Wormhole | ◇ | A tapped any-colour land token every time you attack. The deck has enough ramp; this is ramp that needs the attack first. |
| 112 | Innkeeper's Talent | ★★ | Three cards in one, each level an activation rather than a spell (so it works on a no-spell turn). Level 1 is a counter every combat (F2). Level 2 gives ward {1} to every permanent with a counter: the Ayula Bears, Sarulf and the planeswalkers. Level 3 doubles EVERY counter placement, so Sarulf charges twice as fast, walkers enter with double loyalty, and it stacks with Constrictor. Owned. MV 2, so a Sarulf wipe of 2+ takes it (F3). |
| 113 | Advanced Floral Invocations | ◇ | Mills two per land drop, which fills the graveyard Sauron and Mother Bear read. Level 3 casts creatures from the graveyard, so each recast Bear is another Ayula trigger. But reaching level 3 costs eight mana in total, and Sarulf's wipe exiles rather than bins, so the graveyard plan stays a side line. Owned. |

## 5. Consolidated plan (live)

### Tier 1 — the package (previewed with `swap --package`: legal, floor A, interaction 16→14,
card advantage 14→17, protection 7→9, board power 124→129, avg MV unchanged)

| # | Cut | Add | Why |
|---|---|---|---|
| 1 | Casualties of War | Avabruck Caretaker | Six for six. Two counters a combat (F2), and its night side gives the board hexproof. |
| 2 | Head of the Hunt | Winding Constrictor | Head of the Hunt exiles dying opposing creatures, so they never reach the graveyard and Sarulf gets no counter (E2). Constrictor doubles Sarulf's charge rate instead. |
| 3 | Drover Grizzly | Werewolf Pack Leader | Drover's only text is a saddled trample grant. Pack Leader is a 2-mana 3/3 that draws every big attack (F6). Bears 18→17. |
| 4 | Colossal Majesty | Owlbear Shepherd | Two draw-a-turn cards with the same trigger shape. The Shepherd's condition (total power 8) is easier, and it is a body. |
| 5 | Assassin's Trophy | Toski, Bearer of Secrets | Trophy gives the opponent a basic land, which breaks the owner's removal rule. Toski is an indestructible draw engine. |
| 6 | Go for the Throat | Garruk Relentless | Garruk's 3 damage keeps the removal slot, then makes a Wolf every turn (F4). |
| 7 | Wilderland Scrounger | Geistpack Alpha | Wolf for Wolf. Scrounger is a gate consumer (F2); the Alpha is a 5/4 trampler that opens the gate itself. |
| 8 | Forest | Argoth, Sanctum of Nature | Untapped with Sarulf out; a mana sink that makes a 2/2 Bear (an Ayula trigger). |
| 9 | Cultivate | Flare of Cultivation | Same effect, plus a free alternative cost (E1). Owned. |

### Tier 1b — batch 4 adds (previewed on top of tier 1: legal, floor A, interaction 13,
card advantage 17, protection 9, board power 131, avg MV 3.47)

| # | Cut | Add | Why |
|---|---|---|---|
| 10 | Large Bear | Howlpack Piper | Large Bear is a vanilla 5-drop. The Piper puts a Bear in from hand every turn and enables a no-spell turn. Bears 17→16. |
| 11 | Snakeskin Veil | Innkeeper's Talent | Replaces Hardened Scales here (owner's add, 2026-11-22): a counter every combat, ward {1} on everything with a counter, then a doubler at level 3. Protection holds at 9. Owned. Hardened Scales drops to tier 2. |
| 12 | Elemental Bond | Evolution Sage | Bond draws off power-3 creatures entering; the draw engines in tier 1 cover that. The Sage proliferates every land drop. |
| 13 | Heartless Act | Lukamina, Moon Druid | Interaction 14→13, still above the A line of 12. Bear Form is a team anthem plus trample. |

Interaction 13 is one above the A line; take all four only if you are happy at that margin.
Swap 13 is the one to drop first.

### Tier 2 — strong alternatives (swap in for a tier-1 add, or for a cut below)

- **Kraven the Hunter** (owned): a 4/3 trampler that draws when their biggest creature dies.
  Swap 2 removes the Head of the Hunt conflict that would otherwise switch it off.
- **Chevill, Bane of Monsters** (owned): 2 mana, repeatable draw off removal.
- **Witherbloom, the Balancer** (owned): about 3 mana for a 5/5 flying deathtouch, and it
  discounts the removal.
- **Fight Rigging · Path of Discovery · World War Hulk** (Hulk owned): counter engines (F2).
- **Chimil, the Inner Sun · Sentinel of the Nameless City · Vincent Valentine** (Vincent owned).
- **Sword of Body and Mind · Forebear's Blade**: equipment that opens the gate.
- **Hardened Scales · Advanced Floral Invocations** (Floral owned).
- **Edgar, Moonlit Sovereign · Vraska, Betrayal's Sting · Mythweaver Poq** (Poq owned).
- **Flaxen Intruder** (three Bears, three Ayula triggers) · **Mirkwood** (owned, for a Forest).

Next cut candidates if more tier-2 cards go in: Large Bear (a vanilla 5-drop), Heartless Act and
Infernal Grasp (spot removal; keep interaction at 12 or more), Elemental Bond (overlaps the
draw engines above), Snakeskin Veil.

### Protect list (what the cut ranking cannot see)

- **Exuberant Wolfbear**: a Wolf AND a Bear, so it counts for both tribes. `cuts` rates it low power.
- **Little Bear, Mother Bear**: Ayula triggers. Little Bear's flash untap puts a counter on a
  Bear; Mother Bear makes two Bear tokens.
- **Nature's Lore**: finds any Forest card, Overgrown Tomb included, untapped. `cuts` shows no tags.
- **The removal suite generally**: each kill is a Sarulf counter (E2), so interaction is
  worth more here than its count says.

### Ownership (information only, F7)

Tier 1 crafts: 2 mythic (Avabruck Caretaker, Garruk Relentless), 4 rare (Werewolf Pack Leader,
Toski, Geistpack Alpha, Argoth), 2 uncommon (Winding Constrictor, Owlbear Shepherd). Flare of
Cultivation is owned. Tier 1b: 1 mythic (Lukamina), 1 rare (Howlpack Piper); Evolution Sage and
Innkeeper's Talent are owned.

## 6. Owner's board marks — review (2026-11-23)

Marks read from the board: **37 adds, 15 cuts, 44 bench** (and one note, on Wicked Wolf). As
marked, the deck is **122 cards**, 22 over. Measured as a scratch copy (`consistency`/`tier` take
a path):

| | Deck now | As marked (122) | Proposed (100) |
|---|---|---|---|
| Interaction | 16 | 16 | 15 |
| Card advantage | 14 | 17 | 12 |
| Protection | 7 | 11 | 9 |
| Board power | 124 | 166 | 133 |
| Avg MV | 3.45 | 3.72 | 3.73 |
| Bears / Wolves (creature cards) | 18 / 11 | 15 / 13 | 15 / 10 |
| Removal at MV 2 or less | 8 | 4 | 5 |
| Keepable 7 (first hand) | 78.4% | 66.4% | 78.4% |

### What the marks do together (the interactions, not the single cards)

- **I1 — the counter engine is the strongest cluster you marked.** Innkeeper's Talent (level 3
  doubles), Winding Constrictor (+1), Evolution Sage (proliferate per land), Fight Rigging, The
  Great Henge, Titania's Command and Avabruck all multiply each other. With Innkeeper level 3 and
  Constrictor out, Ayula's two counters become five or six, and every opposing permanent that dies
  puts four counters on Sarulf instead of one.
- **I2 — that same engine makes Sarulf's wipe a trap if used blindly.** Four counters from one kill
  means a wipe that exiles everything you control at MV 4 or less: Innkeeper (2), Constrictor (2),
  Fight Rigging (3), Evolution Sage (3), Lukamina (3). The wipe is optional; take it only when the
  opponent's board is worth more than your engine. Kogla (6), Avabruck (6), Tovolar (6) and The
  Great Henge (9) survive it.
- **I3 — Kogla bounces HUMANS, and four of your adds are Humans.** {1}{G} returns Tovolar's
  Huntmaster (replay = two more Wolves), Lukamina (replay = seek a land), Howlpack Piper or
  Avabruck Caretaker to hand, and makes Kogla indestructible for the turn. Kogla also fights on
  entry (a removal piece that feeds Sarulf).
- **I4 — The Great Henge's discount reads your biggest creature.** Kogla (7), Tovolar (6) or a
  counter-loaded Bear make it cost two or three. Its GG-and-2-life tap also turns on Mortality
  Spear's discount (Spear costs {B}{G} after a life gain).
- **I5 — Titania's Command is three cluster cards in one.** Two Bear tokens (two Ayula triggers),
  two counters on each creature (multiplied by I1), or two lands (two landfall triggers for
  Evolution Sage and Beorn's Hospitality).
- **I6 — the landfall / lands-from-graveyard half is only half built.** Mole Man, Ancient
  Greenwarden, Kagha, Nog and Wrenn all replay lands from the graveyard, but the deck has three
  lands that put themselves there (Evolving Wilds, Fabled Passage, Prismatic Vista) and little
  mill. Glacier Godmaw and Nissa of Shadowed Boughs pay off land drops the deck makes about once a
  turn. Keep the cheap landfall pieces that also do something else (Evolution Sage, Beorn's
  Hospitality, Mythweaver Poq); bench the recursion five.
- **I7 — cutting Nature's Lore works against your own landfall adds.** It puts a land onto the
  battlefield (a landfall trigger) and can fetch Overgrown Tomb untapped. Flare of Cultivation
  for Cultivate is fine; cutting both search spells and both dorks (Llanowar, Paradise Druid)
  while the curve rises from 3.45 to 3.7 is the mana risk in the marks.
- **I8 — the cheap removal went out, the expensive removal came in.** Cut: Abrupt Decay, Go for
  the Throat, Infernal Grasp (all 2 MV), Assassin's Trophy and Beast Within (both rightly — each
  hands the opponent something). Added: Mortality Spear (4), Garruk Relentless (4), Kogla (6),
  Tovolar's fight (6 + 4 per use), Vraska, Regal Gorgon (7), Rise of the Witch-king (4,
  symmetrical). The total holds; the speed does not. Keep Abrupt Decay as the one cheap instant.
- **I9 — Head of the Hunt still fights the commander (E2).** It is not marked; it should go.
- **I10 — Ygra and Wicked Wolf would answer your Food note.** Ygra makes every other creature a
  Food, so Wicked Wolf can sacrifice any creature for its indestructible counter, and Kogla's
  attack trigger (destroy an artifact) hits a creature every turn. But Ygra also gives every
  opposing creature a 'sacrifice: gain 3 life' ability, which benefits the opponent. Bench it.
- **I11 — the Wolf adds are weaker than the Wolves you cut.** Packsong Pup, Tenacious Pup and
  Rhovanion Rampager (a sacrifice outlet with nothing to feed) for Fierce Witchstalker (a 4/4
  trampler for 4, a gate-opener) and Wicked Wolf (a fight on entry). Keep the two you cut; keep
  Ravening Warg as the cheap one.

### Proposed 100 (built and checked as a scratch copy: legal, floor A)

- **Keep 19 of your adds:** Avabruck Caretaker, Winding Constrictor, Innkeeper's Talent, Garruk
  Relentless, Howlpack Piper, Toski, Tovolar's Huntmaster, Kogla, The Great Henge, Evolution
  Sage, Fight Rigging, Flare of Cultivation, Titania's Command, Mortality Spear, Lukamina,
  Mythweaver Poq, Beorn's Hospitality, Fuel Tank Feaster, Ravening Warg.
- **Bench 18 of your adds:** Ancient Greenwarden, Mole Man, Kagha, Nog, Wrenn and Realmbreaker
  (I6); Glacier Godmaw, Nissa of Shadowed Boughs (I6); Insidious Roots, Jenova, Fiend Artisan,
  Descendants' Path, Hound Tamer (curve); Rise of the Witch-king, Vraska, Regal Gorgon (I8);
  Ygra (I10); Packsong Pup, Tenacious Pup, Rhovanion Rampager (I11).
- **Un-cut 5 of your cuts:** Nature's Lore (I7), Abrupt Decay (I8), Fierce Witchstalker and
  Wicked Wolf (I11), Mother Bear (two Bear tokens late; Bear count).
- **Keep your other 10 cuts:** Assassin's Trophy, Beast Within, Go for the Throat, Infernal
  Grasp, Cultivate, Llanowar Elves, Paradise Druid, Little Bear, Owlbear, Guardian Project.
- **Cut 9 more:** Head of the Hunt (I9), Casualties of War, Colossal Majesty, Elemental Bond,
  Master's Guidance, Snakeskin Veil, Herd Heirloom, Drover Grizzly, Wilderland Scrounger.
- **The trade:** card advantage falls 14→12 (four draw enchantments out, Toski and the Henge in).
  If that is too low, keep Elemental Bond and bench Beorn's Hospitality.

### Bench marks (44)

Each benched card becomes a `#~` flex line in the deck file on apply. 44 lines is a block that
rots (G-04). The bench calls themselves are sound — Kraven, Chevill, Witherbloom, Sword, Path,
Sentinel, Hardened Scales and Vraska, Betrayal's Sting are all ★ in §4, and benching them is a
fair choice of the ones above. Suggest trimming the bench to the cards that would come in for a
named reason (about 12); the rest stay on the board with their reasons.

Unmarked from the tier-1 plan: Werewolf Pack Leader, Geistpack Alpha, Argoth (no mark at all).

## 7. Applied 2026-11-23

Owner kept Wilderland Scrounger (not cut) and kept Rise of the Witch-king (sacrifice a weak token
for the best permanent in the graveyard). Applied 18 paired swaps through `builder.py apply`, plus 12
bench lines (`#~`): Kraven, Hardened Scales, Chevill, Witherbloom, Path of Discovery, Sword of Body
and Mind, Sentinel, Edgar, Vraska Betrayal's Sting, World War Hulk, Owlbear Shepherd, Ygra. Live:
floor A, interaction 16, card advantage 12, avg MV 3.81, preflight READY.

**Held (still marked add on the board):** Beorn's Hospitality, Ravening Warg. With Scrounger kept
and Rise added, the plan is two cards over 100. Cut candidates written to the board as suggestions:
Large Bear, Heartless Act, Grizzly Ghoul.

## 8. Second board review (2026-11-23)

Marks: 21 adds (2 of them lands: Argoth, Mirkwood), 8 cuts (Abrupt Decay, Heartless Act,
Fierce Witchstalker, Large Bear, Mother Bear, Nature's Lore, Outcaster Trailblazer, Vaultborn
Tyrant). That is 13 over. Measured as scratch copies (land swaps: Argoth for a Forest, Mirkwood
for Temple of Malady):

| | Deck now | A: tribal core | B: every add |
|---|---|---|---|
| Interaction | 16 | 14 | 13 |
| Card advantage | 12 | 12 | 12 |
| Avg MV | 3.81 | 3.95 | 3.88 |
| Nonland cards at MV 2 or less | 17 | 11 | 12 |
| Bears / Wolves | 15 / 10 | 12 / 10 | 8 / 8 |

- **A** takes the 11 nonland adds outside the lands package, benches the lands package (Floral,
  Nog, Nissa of Shadowed Boughs, Kamahl's Druidic Vow, Burgeoning, Beorn's Hospitality) plus
  Copper Host Crusher and Ravening Warg, and cuts Fuel Tank Feaster, Heroic Intervention and
  Grizzly Ghoul.
- **B** takes every add and has to find nine more cuts inside the tribal core.
- Both share the curve problem: the four cheap cuts (Abrupt Decay, Heartless Act, Mother Bear,
  Nature's Lore) leave 11–12 nonland cards at MV 2 or less, against 21 at the draft.

Owner notes conceded: Descendants' Path is pure upside (misses cost no draw); Floral + Argoth +
Mirkwood answer §6 I6 (now about eight ways for a land to reach the graveyard); Beifong's earthbend
counters are multiplied and its land returns; Jenova's 1 becomes 4 with the multipliers.

## 9. Plan A applied, bench re-graded (2026-11-23)

Applied 12 of plan A's 13 swaps; Fuel Tank Feaster stays and Sentinel of the Nameless City is held
pending a cut (suggestions on the board: Mythweaver Poq, Exuberant Wolfbear, Bosco). Live: floor A,
interaction 14, card advantage 12, avg MV 3.94, 11 nonland cards at MV 2 or less, 9 Humans.
All 125 off-deck board cards re-graded against this list (builder reasons and verdicts). What moved
most: cheap cards and card draw rose (Werewolf Pack Leader and Return of the Wildspeaker ★★; Abrupt
Decay ★★; Infernal Grasp, Go for the Throat, Heartless Act, Torgal, Goliath, Mayor of Avabruck,
Chevill, Cankerbloom, Striped Bears ★), because those are the two thin axes now.

## 10. Fits, upgrades and spice search (2026-11-23)

Searched the pool by effect (cheap removal, counter payoffs, draw, Bears/Wolves) beyond the board;
added 16 to the builder. Previewed package (−Mortality Spear +Fatal Push, −Mythweaver Poq +Inspiring
Call, −Exuberant Wolfbear +Sarulf's Packmate, −Studious First-Year +Incubation Druid): legal, floor
A, interaction 14, card advantage 12→13, avg MV 3.94→3.89. `suggest --lands` offered only tapped BG
duals, none better than the current manabase.

## 11. Third board pass (2026-11-23)

Applied: Studious First-Year → Incubation Druid. Owner's new cuts: Bosco, Rhonas, Turntimber
Symbiosis, Wicked Wolf. Owner's point taken: Bear/Wolf TOKENS are the real tribe count. 11 cards
make them (5 repeatably: Dancing from Dark to Dawn, Garruk Cursed Huntsman, Garruk Relentless,
Nightpack Ambusher, Argoth), and tokens count for Ayula, Torgal, Moonlight Hunt and Nightpack.
Trade-off: every Sarulf wipe exiles all tokens (MV 0). Proposed 4-pair package (Wicked Wolf→Ram
Through, Bosco→Branching Evolution, Rhonas→Sentinel, Turntimber→Moonlight Hunt): legal, floor A,
interaction 14 (Moonlight Hunt reads as no role, a classifier hole), protection 9→7, avg MV 3.81.

## 12. Fourth pass (2026-11-23)

Applied: Wicked Wolf→Ram Through, Bosco→Branching Evolution, Rhonas→Sentinel, Turntimber
Symbiosis→Shang-Chi (owner's change from Moonlight Hunt). The deck now runs FOUR counter
multipliers (Winding Constrictor +1, Branching Evolution ×2, Shang-Chi ×2, Innkeeper level 3 ×2):
one counter can become 16. Scoped 8 pairs for the owner's adds (suggestions on the board): Primal
Might→Moonlight Hunt, Exuberant Wolfbear→Torgal, Gigantic Big Bear→Ygra, Edgar→Vincent Valentine,
Lukamina→Elemental Bond, Bejeweled Warg→Nog, Wilson→Beorn's Hospitality, Fanatic of Rhonas→Floral.
All 8 previewed: legal, floor A, interaction 13 (Moonlight Hunt unclassified, so really 14),
protection 6, avg MV 3.78. Mortality Spear DESTROYS (not exiles); its discount sources are Spider-Ham,
The Great Henge, Titania's Command.

## 13. Re-scoped cuts (2026-11-23)

Owner keeps Exuberant Wolfbear (and maybe Gigantic Big Bear, Edgar, Lukamina). Re-scoped as board
suggestions: Kraven→Elemental Bond (alt The Chief Warg; Bond triggers on 25 power-3+ creatures vs
18 power-4+ for Garruk's Uprising), Flare→Burgeoning (Flare is the only lands-only card),
Beorn Reluctant Host→Ygra (alts Gigantic Big Bear, Garruk Curse Breaker), Bejeweled Warg→Torgal,
Wilson→Nog, Fanatic→Beorn's Hospitality, Edgar→Vincent (if one of the maybes goes), Primal
Might→Moonlight Hunt. Full 8-pair preview: legal, floor A, avg MV 3.83, interaction 13 (14 real).
Floral Invocations has no cut left.

## 14. Torgal in; Head of the Hunt reconsidered (2026-11-23)

Applied Bejeweled Warg→Torgal. Owner's new board cuts: Primal Might, Hunter's Talent, Rise of the
Witch-king, Sword of Body and Mind. Measured: all four cut with Floral, Moonlight Hunt, Head of the
Hunt and Elemental Bond in = interaction 11, floor A→B. Keeping Rise (Kraven→Head instead) = 12,
floor A. Head of the Hunt: owner's case accepted with conditions — the more tokens the deck makes,
the more a Sarulf wipe costs (it exiles every token), so Sarulf's counters matter less; but Head
also switches off Kraven, Vincent Valentine's counters and Ygra's growth from opposing deaths.

## 15. Head of the Hunt and Floral in; protection for Sarulf (2026-11-23)

Applied Kraven→Head of the Hunt, Primal Might→Advanced Floral Invocations; prose updated (Head is
now in by choice). Live gaps: interaction 13 but only 2 instant-speed; card advantage 11; protection
7, but only three can protect SARULF (Sword of Body and Mind, Innkeeper's ward {1}, Avabruck's night
side) — the rest protect themselves. Protection that also adds a +1/+1 counter doubles as wipe fuel
for Sarulf. Added 10 candidates to the board (Gaea's Gift, Warg Tactics, Oblivion's Hunger,
Silkguard, Swiftfoot Boots, Plaza of Heroes, Commander's Plate, Revitalizing Repast, Sword of Truth
and Justice, Tyvar's Stand) plus Snakeskin Veil re-graded. Preview: Wilson→Ygra, Fanatic→Nog,
Lukamina→Snakeskin Veil, Edgar→Warg Tactics, Gigantic Big Bear→Gaea's Gift = legal, floor A,
interaction 14, protection 9, avg MV 3.77, card advantage 10.
Tooling note: the rationale audit missed "Rhonas" (cut) in the archetype prose — G-78's short-name
floor; fixed by hand.

## 16. Ygra and Nog in; equipment and auras for Sarulf (2026-11-23)

Applied Wilson→Ygra, Fanatic of Rhonas→Nog. Owner shortlist: Inspiring Call, Gaea's Gift, Plaza of
Heroes, Overprotect. Added 9 aura/equipment/protection cards to the board (Champion's Helm, Mithril
Coat, Sword of Wealth and Power, Dragonfire Blade, Sword of Fire and Ice, Leyline Immersion,
Darksteel Plate, Alpha Authority, Overprotect). Caveat for all of them: Sarulf's wipe exiles your
own equipment and auras at MV ≤ N too (they are MV 1–4).

## 17. Protection creatures (2026-11-23)

Searched BG Historic Brawl creatures and planeswalkers that protect OTHER creatures. No planeswalker
does. Added 6 to the board: Dr. Joseph M'Benga ★★ (countered creatures hexproof + a fifth counter
doubler), Saryth ★★ (untapped creatures hexproof), Selfless Safewright ★ (flash Wolf-wide hexproof
+ indestructible, convoke), Guildpact Greenwalker ★ (multicoloured creatures ward {2}), The Walls of
Ba Sing Se ◇ (owned, MV 8), Bedrock Tortoise ◇.

## 18. M'Benga and Saryth in (2026-11-23)

Applied Sword of Body and Mind→Dr. Joseph M'Benga, Hunter's Talent→Saryth. Live: floor A,
interaction 12 (exactly the A line), card advantage 10, protection 8, avg MV 3.97. Rise of the
Witch-king is still marked cut on the board but should stay while interaction sits at 12.
Correction: Saryth is MV 3 ({2}{G}), not 4 as first reported.

## 19. Multi-role search: interaction + card advantage (+ protection, mill/recursion) (2026-11-23)

Swept BG Historic Brawl for cards with two or more of interaction / card advantage / protection /
mill-recursion (299 hits), curated 12 onto the board. Strongest are OWNED: Professor Dellian Fel,
Fall of Gil-galad, Liliana Dreadhorde General (★★); Witherbloom Charm, Pawpatch Formation, Glissa
Sunslayer, Kraven's Last Hunt (★, owned). Preview Lukamina→Dellian Fel, Cemetery Prowler→Fall of
Gil-galad, Gigantic Big Bear→Liliana: legal, floor A, interaction 12→15, card advantage 10→12,
protection 8→7 (Gigantic Big Bear's own hexproof), avg MV 3.95.
