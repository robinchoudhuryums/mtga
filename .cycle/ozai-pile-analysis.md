# Ozai pile — analysis (TEMPORARY working doc)

**Status: CONSOLIDATED, awaiting owner picks.** Delete once the deck is drafted
(`/draft-deck`) and the findings are folded into its `#: notes:` block. A scratchpad, not a
source of truth — decks/ are.

**Source list:** owner's 2026-10-25 paste — 116 distinct cards (deck 1 Black Sun's 33
nonbasic lines plus 83 new), commander **Ozai, the Phoenix King** (TLA) 235, for a new
**Historic Brawl** (100-card) deck. Every card is Historic Brawl-legal and every one is
castable in B/R (G-58 check via `_candidate_castability`). Deck 1 overlap is NOT
deduplicated out: a 60-card Standard list and a 100-card Brawl list grade the same card
differently, so every card was re-read.

Scratch draft (not a deck file): the scratchpad `ozai-draft2.txt`, measured below.

## 1. The decision framework

Ozai, the Phoenix King — {2}{B}{B}{R}{R} 7/7 trample, haste, **firebending 4**; "If you would
lose unspent mana, that mana becomes red instead"; flying + indestructible while you have
**six or more unspent mana**.

- **F1 — Mana never empties while Ozai is out.** Every firebending trigger, Treasure and
  leftover land drop becomes permanent RED mana that carries across steps, phases AND turns.
  A card that ADDS mana is worth its mana every turn after, not just once. Firebending
  creatures are ramp here; the role classifier does not count them as such (§3, T1).
- **F2 — The floating mana is RED.** Red pips and generic costs (X, activations) are what it
  pays. A {B}{B}{B} card gets nothing from it but its generic part. Grade a sink by how
  much of its cost is red/generic.
- **F3 — Six floating = Ozai flies and is indestructible.** Holding mana IS the commander's
  protection. So instant-speed sinks (activated abilities, instants, flash) beat
  sorcery-speed ones: spend down to six on the opponent's end step. It also means a
  "destroy all creatures" wipe (Blasphemous Act, The Rise of Sozin I) is ONE-SIDED with six
  up. "Loses all abilities" (Day of Black Sun) strips the indestructibility — keep X < 6.
- **F4 — Without Ozai, firebending mana dies at end of combat**, so its value without the
  commander is whatever can be cast/activated DURING combat: instants, activated abilities
  (Fire Nation Turret's {R}, Fire Sages, Vindictive Warden, Fire Nation Archers, Loyal Fire
  Sage). A firebending card with an instant-speed sink is live without Ozai; one without
  is a body.
- **F5 — "You don't lose unspent red mana" is redundant with Ozai** (Electro, Ashling, The
  Last Agni Kai, Bloodsky III). Insurance for the turns Ozai is off the table; grade on the
  REST of the text.
- **F6 — Ozai is a 6-drop with a {2} tax.** The deck needs real acceleration to land it
  turn 4–5 and recast it at 8. Rocks and Treasure count; the pile has only four (Rakdos
  Signet, Rakdos Locket, Namazu Trader, The Legend of Roku II).
- **F7 — Deck 1's spine is go-wide sacrifice** (Black Sun: tokens + death triggers +
  reach). Token makers also fuel Slash / Raphael / Warstorm-type "creature enters" payoffs
  and make Sozin's Comet / Avatar Roku / Firebender Ascension huge. A symmetric sweeper
  fights this half (G-42) — count how many the list runs.
- **F8 — Singleton, 100 cards, 1v1 at 25 life.** Burst Lightning ×2 becomes one copy. A
  floor reads ×1.67: A needs interaction 12 and interaction + card advantage 19.

## 2. Standing error list

- (none yet — first pass)

## 3. Cross-batch observations

- **Two engines, one deck.** (a) Firebending / Ozai mana accumulation into red sinks
  (Fire Nation Turret's 50-counter clock, Fated Firepower, Hell to Pay, Frantic
  Confrontation, Avatar Roku's {8} Dragons, Fire Lord Ozai's {6}); (b) deck 1's
  tokens-and-death drain (Slash, Raphael, Perforating Artist, Sawblade, June, Avengers).
  They reinforce: tokens attack for firebending, Sozin's Comet gives EVERY attacker
  firebending 5, Firebender Ascension copies attack triggers.
- **Lesson / Noble subtheme is real but thin.** Lo and Li tutors either; Nobles here: Fire
  Lord Ozai, Azula, three Zukos, two Irohs (Ozai himself is in the command zone). Lessons:
  nine. Lo and Li is a tutor for Fire Lord Ozai or a removal Lesson — worth a slot for that
  alone; the lifelink is a bonus.
- **Sweeper count (F7).** One-sided: Massacre Wurm, Iroh's Demonstration (mode 1), Volcanic
  Torrent, Siege Dragon. Symmetric: Blasphemous Act, The Rise of Sozin, Day of Black Sun,
  Black Sun's Zenith, Fiery Confluence mode 1, Avengers: Under Siege II (hits your
  non-Villains). The draft keeps Blasphemous Act (F3 makes it one-sided for Ozai) and Day of
  Black Sun (deck 1's namesake, scalable) and benches Zenith and Rise of Sozin.
- **Allies (Wartime Protestors) and Goblins (Krenko) don't reach density.** Allies: Zuko
  Firebending Master, two Irohs, Loyal Fire Sage (+ its Ally tokens), Freedom Fighter
  Recruit, Longshot, Smellerbee — 7. Goblins: Searslicer, Krenko, Magic Pot, Dragon Fodder,
  Goblin Surprise — 5. Both are side notes, not plans.
- **Hulk, Always Angry fights the deck (G-42):** "destroy all artifacts" kills your own
  Signets, Locket, Turret, Treasures, Clues, Doombots and Noxious Gearhulk.
- **The pile has ten lands and they are weak for a 100-card two-colour deck**: three enter
  tapped unconditionally (two Thriving lands, Valakut). The draft adds six untapped Rakdos
  duals from outside the pile (§5).

### Tooling holes found (record; fix in a batch at the end, Stage 4)
- **T1 — Firebending is not Ramp.** The classifier counts 4 ramp pieces in the draft; with
  Ozai out, Vindictive Warden, Fire Sages, Loyal Fire Sage, Cruel Administrator's tokens,
  Iroh, Ran and Shaw, Avatar Roku and Fire Lord Ozai are all mana. Commander-dependent, so
  probably a disclosure line, not a role.
- **T2 — Scarring Memories reads 0 hand attack** ("Target opponent sacrifices a creature of
  their choice, discards a card, and loses 3 life" — a compound clause).
- **T3 — `suggest --lands` mis-reads two lands** (also seen on deck 91): Duskmantle, House
  of Shadow scores as a U/B producer though it only taps for {C} (`land_production` falls
  back to colour identity, which comes from its {U}{B} activation cost); Demolition Field
  scores as a basic fetch for YOU though the search is the opponent's.
- **T4 — Black Market Connections scores no role** (deck 91): "Buy Information — Draw a
  card" inside a modal bullet at the start of each main phase is repeatable card advantage.

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`. D = draft.

### Batch 1 (deck 1's list)

| Card | Verdict | Note |
|---|---|---|
| Vindictive Warden | ★★ D | firebending 1 + {3}: 1 to each opponent — an instant-speed sink (F3/F4) |
| Cruel Administrator | ★ D | every attack makes a firebending 2/2 |
| Perforating Artist | ★★ D | raid punisher, deathtouch |
| Alesha, Who Laughs at Fate | ★ D | grows each attack; raid reanimation |
| Hazoret, Godseeker | ◇ | needs max speed to attack; drains get there, but a 2-drop that doesn't attack until then |
| Raphael, Tough Turtle | ★ D | 1 damage per creature entering; tokens |
| Searslicer Goblin | ★ D | raid token every end step |
| Doctor Doom | ★★ D | three bodies + a card each end step |
| Slash, Reptile Rampager | ★★★ D | 2 to each opponent per creature entering; attacks make tokens |
| Krenko, Mob Boss | ◇ | five Goblins in the pile — no density |
| Bot Bashing Time | ★ D | 6 damage, exile |
| Raven Eagle | ★ D | flier, Clue, graveyard hate you aim at THEIR yard |
| Gisa, the Hellraiser | ◇ | the lord half is dead (no Zombies); crime tokens only |
| High-Society Hunter | ★ D | flier, draws on nontoken deaths |
| Massacre Wurm | ★★ D | one-sided sweep; {B}{B}{B} gets nothing from F2 — 49% on T5 |
| Namazu Trader | ★ D | Treasure (F1 ramp) + sac-surveil |
| Red Hulk | ◇ | 6-drop with no evasion beyond trample/reach |
| Sawblade Skinripper | ★ D | sac outlet + end-step damage |
| June, Bounty Hunter | ★ D | sac outlet that makes Clues |
| Avengers: Under Siege | ★ D | tokens, 2 to each opponent, Treasures; chapter II hits your non-Villains |
| Blood Spatter Analysis | ★★ D | 3 damage + recursion |
| Hell to Pay | ★★★ D | X removal paid from floating red, Treasures for the excess (F1/F2) |
| Burst Lightning | ★★ D | one copy (F8) |
| Sporogenic Infection | ◇ | edict + conditional kill — bench |
| Robot Domination | ◇ | draws per creature card to graveyard; bench |
| Dragon Fodder | △ | two 1/1s |
| Reckless Ransacking | △ | pump + Treasure |
| Magic Pot | △ | |
| Goblin Surprise | △ | |
| Rat King, Verminister | ◇ | its Rats are only its own tokens |

### Batch 2

| Card | Verdict | Note |
|---|---|---|
| Callous Inspector | △ | |
| Day of Black Sun | ★★ D | X sweeper from floating mana; keep X < 6 (F3) |
| Rakdos Joins Up | ★ D | reanimation + legendary-death damage (many legends) |
| Fire Nation Palace | ★★ D | land that grants firebending 4 |
| Blazemire Verge / Razortrap Gorge / Blood Crypt / Dark Fortress | ★ D | lands |
| Firebender Ascension | ★★ D | firebending token; copies attack triggers, firebending included |
| The Rise of Sozin | ◇ | wrath (one-sided for Ozai with six up) → Fire Lord Sozin; bench vs F7 |
| Fire Sages | ★★ D | firebending + {1}{R}{R} counter sink |
| Firebending Student | ◇ | |
| Azula, Ruthless Firebender | ◇ | |
| Fire Nation Occupation | ★ D | floating mana (F1) makes opponent's-turn casting real |
| Fire Nation Turret | ★★★ D | the red sink: {R} per charge counter, fifty = 50 damage, plus +2/+0 and firebending 2 each combat |
| Zuko, Firebending Master | ◇ | |
| Iroh, Firebending Instructor | ◇ | |
| Loyal Fire Sage | ★★ D | firebending + {5} Ally token sink |
| The Legend of Roku | ★★★ D | impulse 3, mana, then Avatar Roku with an {8} Dragon sink |
| Iroh, Dragon of the West | ★ D | haste, counters → firebending 2 |
| Sozin's Comet | ★★ D | every creature firebending 5 — the big mana turn |
| Avatar Roku, Firebender | ★★★ D | six {R} whenever ANY player attacks — with Ozai, it stays |
| Zuko, Seeking Honor | ◇ | |
| Zuko's Conviction | ★ D | recursion |
| Desperate Plea | ★ D | sac + reanimate and/or destroy |
| Epic Downfall | ★★ D | |
| Ozai's Cruelty | ◇ | |
| Fire Lord Ozai | ★★★ D | sac → {R} equal to power; {6} sink casts their cards |
| Lion Vulture | ★★ D | flier, a card each end step the opponent lost life |
| Scarring Memories | ★★ D | edict + discard + 3, flash with an attacking legend |

### Batch 3

| Card | Verdict | Note |
|---|---|---|
| Fire Nation Salvagers | ◇ | |
| Lo and Li, Twin Tutors | ★★ D | tutor Fire Lord Ozai or a removal Lesson |
| Fire Nation Sentinels | ◇ | |
| Nyla, Shirshu Sleuth | ◇ | |
| Noxious Gearhulk | ★★ D | removal + body |
| Black Sun's Zenith | ◇ | symmetric −1/−1 in a token deck; bench (F7) |
| Realm of Koh | ★ D | land |
| Thriving Moor / Thriving Bluff | ◇ D | tapped; replaceable by duals |
| Firebending Lesson | ★★ D | |
| Redirect Lightning | ★ D | protects Ozai |
| Combustion Technique | ◇ | |
| Fists of Flame | ◇ | |
| Freedom Fighter Recruit | △ | |
| Iroh's Demonstration | ★★ D | one-sided ping sweep or 4 damage |
| Lost in Memories | ◇ | |
| The Last Agni Kai | ◇ | fight; F5 redundant |
| Bolt Bend | ◇ | Redirect Lightning is the better one here |
| Fiery Confluence | ★★ D | 6 to face, a small sweep, or artifacts |
| Fire Nation Archers | ★ D | {5} sink: 2 damage + a token |
| Longshot, Rebel Bowman | ◇ | |
| Smellerbee, Rebel Fighter | ★★ D | haste for tokens (firebending the turn they land) + a refill |
| Wartime Protestors | ◇ | 7 Allies |
| Combustion Man | ★★ D | removal on every attack |
| Fang, Roku's Companion | ★ D | +X/+0 to Ozai on attack; returns once |
| Overwhelming Victory | ★★ D | removal + overrun |
| Mirrorwing Dragon | ◇ | |
| Ran and Shaw | ★ D | flying firebending 2 |
| Storm of Memories | △ | |
| Volcanic Torrent | ◇ | |
| Zuko, Avatar Hunter | ★ D | a token per red spell |

### Batch 4

| Card | Verdict | Note |
|---|---|---|
| Insurrection | ★★ D | a game-ender paid from floating red; sacrifice what you stole |
| Warstorm Surge | ◇ | |
| Blasphemous Act | ★★ D | one-sided for Ozai with six up (F3) |
| Frantic Confrontation | ★ D | X finisher at instant speed |
| Fated Firepower | ★★ D | flash, X fire counters on every source you control |
| Thriving Bluff / Valakut | ◇ D | tapped; Valakut needs five other Mountains |
| White Lotus Hideout | ◇ D | Lesson mana + a filter |
| Rakdos, Patron of Chaos | ★ D | flier, draws two |
| Rakdos, the Muscle | ★★ D | sac outlet that exiles cards to play |
| Rakdos Signet / Rakdos Locket | ★★ D | F6 ramp |
| Electro, Assaulting Battery | ★ D | backup for F1, {R} per spell, X damage when it leaves |
| Ashling, Flame Dancer | ◇ | too few instants/sorceries to chain |
| Pyromancer's Goggles | ◇ | |
| Fury of the Horde | ★★ D | extra combat = a second firebending round |
| Sarkhan, the Dragonspeaker | ★★ D | 4/4 flier or 4 damage |
| The Bloodsky Massacre | ◇ | |
| Hulk, Always Angry | ✗ | destroys your own artifacts (G-42) |
| Improvisation Capstone | ★★ D | free spells, then again each turn |
| Siege Dragon | ◇ | |
| Shivan Branch-Burner | ◇ | |
| Silverclad Ferocidons | ◇ | |
| Explosive Singularity | ◇ | |
| Smaug the Impenetrable | ◇ | |

## 5. Consolidated plan (live)

**Draft (scratch, measured):** commander + 62 nonland + 37 lands = 100.

- Nonland 62: the 61 `D` cards above + **Arcane Signet** (outside the pile; F6).
- Lands 37: the pile's ten + six untapped Rakdos duals from outside the pile (**Mount
  Doom, Blightstep Pathway, Sulfurous Springs, Dragonskull Summit, Smoldering Marsh,
  Blackcleave Cliffs**) + 11 Mountain + 10 Swamp.

Measured (scratch file):
- **Floor A**; interaction 19 (16 spot removal, 5 sweepers; 4 at instant speed, 4 can
  answer a noncreature permanent); card advantage 8; avg MV 3.79; legal in Historic Brawl.
- Sources B 23 / R 25 (lands only). Ozai on T5 63.5% before rocks, Massacre Wurm 49%,
  Avatar Roku / Insurrection / Fated Firepower 55% (all colour-hungry triples).
- Without the six duals: B 20 / R 22, Ozai 52%.

**Bench (graded, not in the draft):** Hazoret, Krenko, Gisa, Red Hulk, Sporogenic Infection,
Robot Domination, Dragon Fodder, Reckless Ransacking, Magic Pot, Goblin Surprise, Rat King,
Callous Inspector, The Rise of Sozin, Firebending Student, Azula, Zuko Firebending Master,
Iroh Firebending Instructor, Zuko Seeking Honor, Ozai's Cruelty, Fire Nation Salvagers, Fire
Nation Sentinels, Nyla, Black Sun's Zenith, Combustion Technique, Fists of Flame, Freedom
Fighter Recruit, Lost in Memories, The Last Agni Kai, Bolt Bend, Longshot, Wartime
Protestors, Mirrorwing Dragon, Storm of Memories, Volcanic Torrent, Warstorm Surge, Ashling,
Pyromancer's Goggles, The Bloodsky Massacre, Siege Dragon, Shivan Branch-Burner, Silverclad
Ferocidons, Explosive Singularity, Smaug; out: Hulk, Always Angry.

**Protect list (what `cuts` cannot see):** Fire Nation Turret, Avatar Roku, Fire Lord Ozai,
The Legend of Roku, Sozin's Comet, Firebender Ascension, Fated Firepower (all valued by
F1/F2 — the floating-mana engine no tag encodes), Slash, Smellerbee.

**Open questions for the owner:**
1. More ramp beyond four rocks (Talisman of Indulgence, Mind Stone)?
2. Keep Massacre Wurm at {B}{B}{B} (49% on T5), or bench it for a red-heavy threat?
3. Take Rise of Sozin over Blasphemous Act / Day of Black Sun?
4. The Thriving lands and Valakut enter tapped — replace with more duals?
