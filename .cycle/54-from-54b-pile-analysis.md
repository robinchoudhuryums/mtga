# 54b pile → deck 54 (Grand Lotus) — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into deck
54's `#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Source list:** every card named while tuning deck 54b on 2026-10-13/14 (user suggestions,
Claude suggestions, the ~96-card Sneak/flash list, cards added and cut), extracted from the
session transcript and matched against Standard-legal pool names. 404 names →
25 already in deck 54, 30 lands (graded separately, §4 Lands), 30 not castable on G/U/R
(✗ below, black or white pips) → **319 nonland cards to evaluate**, in batches of 30.

## 1. The decision framework

Live vector (2026-10-14, before any swap): interaction 6 (+6 unclassified) · card advantage
**2** · protection 2 · board power 33 over 14 creatures · avg MV 3.29 · TALL (wide score 1) ·
16 Lessons · 17 instants/sorceries · 21 noncreature nonland spells · floor B (midrange plan;
A needs +1 interaction, +2 card advantage).

1. **What a card costs here.** Once Iroh, Grand Lotus is out, a LESSON in the graveyard costs
   `{1}`, every turn, at sorcery or instant speed as printed. Uncle Iroh takes `{1}` off any
   Lesson spell; Doc Aurlock takes `{2}` off any graveyard/exile cast. A NON-Lesson instant or
   sorcery recasts at its FULL mana cost. A permanent pays full price and is never recast.
   ⇒ grade a Lesson on its effect, not its cost; grade everything else on printed cost.
2. **The graveyard counts are resources.** Lessons in yard (Combustion Technique, Bumi,
   Accumulate Wisdom's 3-gate), noncreature nonland cards (Dragonfly Swarm), instants and
   sorceries (The Dawning Archaic's discount). A non-Lesson replacing a Lesson costs a point.
3. **The deck is TALL and rarely attacks.** 14 creatures, printed power 33. Attack and
   combat-damage triggers (firebending, Sneak, Seifer, Bilbo, Newt, Raphael) are weak unless
   the body is evasive or the trigger is on ATTACK rather than damage. Firebending mana
   (red, expires at end of combat) has little to buy: most Lessons are sorceries.
4. **Mana is main-phase and three-colour.** G16 U14 R14 lands, 8 enter-tapped, double pips
   at 79.5% on curve. Colourless and hybrid costs are a bonus; triple pips are a cost.
5. **Needs, in order:** card advantage (2, Weak) > protection for Iroh (2) > interaction (6)
   > a second engine so Iroh is not the only recast source. A card that does two wins.
6. **"Mana SPENT" gates read LOW here; "mana VALUE" gates read HIGH.** A `{1}` Iroh flashback
   spends 1 (Uncover the Moon-Letters, Shantotto, Emperor of Palamecia barely fire); Thor deals
   the spell's mana VALUE, so a flashed-back Capstone is 7 damage for `{1}`.
7. **Per-cast triggers scale with Iroh.** Every `{1}` recast is a cast: "whenever you cast a
   noncreature spell" (Mechanist, Thor, Death to Our Enemies, Kraum's second spell) fire
   several times a turn.
8. **Engine conflicts (G-42).** Anything that exiles your own graveyard, or makes it exile,
   fights the deck (Festival of Embers, Emeritus of Ideation's attack, Abhorrent Oculus).
9. **Rotation.** Wizards skipped the 2026 rotation; WOE/LCI/MKM/OTJ/BLB/DSK leave Standard in
   early 2027 (Jan–Feb; exact day unconfirmed). `deck.py rotation` still says "~2026" for
   WOE–OTJ — treat those as early 2027. Flag a card from those sets; do not gate on it.

## 2. Standing error list

1. Rotation: the repo's `rotation_year` still models a fall-2026 rotation; the real one is early 2027 and takes BLB/DSK too, while DFT/TDM/FIN stay to early 2028 (2025 sets). Do not trust a `~2026` flag literally (R9).

## 3. Cross-batch observations

- **Batch 1: R1 sinks most of 54b's red burn here.** A non-Lesson removal spell recasts at full price; a Lesson one at `{1}`. Lesson removal in the owned pool (Firebending Lesson, Lost Days, Zuko's Exile) beats every Burst Lightning / Bombard in this pile.
- **Iroh insurance is a real category:** Auroral Procession and True Ancestry return a dead Iroh; Bilbo and The Dawning Archaic are second recast sources.
- **Batch 2: the counters axis has enablers and no payoff** (`engines`: 10 enablers, 0 payoffs). Doc Samson is the first real payoff seen. Watch for more.
- **A copy that renames itself dodges the legend rule** (Chameleon) — a second Iroh or Uncle Iroh is possible.
- **Batch 3: a red-mana REFUND is the 54b idea that transfers best.** Electro adds `{R}` per instant/sorcery cast and keeps it; with `{1}` Lesson recasts that is a near-free chain. Emeritus of Conflict (third spell → Lightning Bolt) is the same "many cheap casts" payoff in interaction form.
- **Second-Iroh paths so far:** Chameleon (renamed copy), Ember Island Production (non-legendary token), plus the recast sources Bilbo / The Dawning Archaic.
- **Batch 4: "cards leave your graveyard" is an unmodelled payoff axis.** Garrison Excavator turns every Iroh recast into a 2/2; no tool counts this. Two anti-synergy cards so far (Festival of Embers, Goliath Daydreamer) both REDIRECT cards away from the yard.

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

### Not castable on G/U/R (✗, 30)
Armaggon, Azula Cunning Usurper, Barbed Bloodletter, Boros Charm, Bre of Clan Stoutarm, Cori
Mountain Stalwart, Cruel Administrator, Emet-Selch, Fire Lord Azula, Fire Lord Zuko, Great
Ugly-Looking Goblin, Heartflame Duelist, Lake-town Toymaker, Lightning Helix, Liminal Hold,
M.O.D.O.K., Nowhere to Run, Oltec Matterweaver, Poised Practitioner, Prayer of Binding,
Pursue the Past, Restoration Magic, Sage of the Skies, Sheltered by Ghosts, Sun Warriors, The
Legend of Yangchen, Uldaros Theorix, Wayspeaker Bodyguard, Winter Misanthropic Guide, Xande.

### Batch 1 (1–30)

| Card | 54 | Note (rule) |
|---|---|---|
| Aang's Journey | △ | Lesson `{2}`: basic to HAND, +2 life. With Iroh a `{1}` land each turn; +1 Lesson (R2). Shared Roots already does the job better (to battlefield). |
| Abstract Paintmage (craft U) | ◇ | Adds `{U}{R}` each first main, instants/sorceries only — flashback casts count. Ramp for the hard-cast turns. |
| Ancestors' Aid | ✗ | Combat trick (R3). |
| Anzrag, the Quake-Mole (craft M) | ✗ | Extra combat on block (R3). |
| Aquitect's Defenses | ◇ | Flash aura: hexproof until end of turn + `+1/+2`. One-shot cover for Iroh (R5 protection). |
| Archmage's Newt | △ | Needs combat damage (R3); OTJ, rotates early 2027 (R9). |
| Asinine Antics (craft M) | △ | Every opposing creature becomes 1/1 — real mass answer, but a mythic craft from WOE, gone early 2027 (R9), non-Lesson (R1). |
| Auroral Procession | ★ | `{G}{U}` instant: "Return target card from your graveyard to your hand." Returns a DEAD IROH (R5 single engine) or any Lesson. Card-neutral. |
| Balmor, Battlemage Captain | ✗ | Team pump on spell cast — attack payoff (R3). |
| Balthier and Fran (craft R) | ✗ | Vehicles. |
| Bear Trap (craft C) | △ | Colourless flash artifact, `{3}`, sac: 3 damage to a creature. Works; DSK (R9). |
| Beast, Erudite Aerialist | △ | Draws on combat damage only (R3). |
| **Bilbo, Thief in the Night** | ★★ | "Spells you cast from anywhere other than your hand cost {1} less" — Iroh's `{1}` Lesson flashback becomes **free**, and it stacks with Doc Aurlock. Attack trigger casts an instant/sorcery from the yard — a second recast source (R5) that only needs to ATTACK (R3). The Doc Aurlock replacement when OTJ rotates. |
| Bitter Work | ◇ | Draws when a power-4+ creature attacks: Iroh 5/5, Thor 5/5 flier, Bumi, earthbent lands. Rarely attacks (R3). Exhaust earthbend 4 is real. |
| Blazing Crescendo | ✗ | Trick (R3). |
| Blazing Firesinger // Seething Song | ◇ | Enters prepared: a free copy of "Add {R}{R}{R}{R}{R}" — one big hard-cast turn (Capstone from hand turn 5). One-shot. |
| Blooming Blast (craft U) | △ | 2 damage, non-Lesson (R1). Firebending Lesson does it as a Lesson. |
| Bombard | △ | 4 damage instant `{2}{R}`, non-Lesson (R1). Best non-Lesson burn here if wanted. |
| Brazen Collector | ✗ | Attack mana (R3). |
| Breaching Dragonstorm | ★ | 5-mana enchantment: free-cast the first nonland card off the top if MV ≤ 8. Hits here: Capstone (7, starts its Paradigm), Symposium, Germination, Iroh, Bumi, Thor. Noncreature cast (R7). |
| Brineborn Cutthroat | ✗ | Opponent's-turn casting. |
| **Bruce Banner // The Incredible Hulk** | ★★ | `{U}` 1/1: "{X}{X}, {T}: Draw X cards" — a mana sink that turns the deck's ramp into cards (R5, CA). Flips for `{2}{R}{R}{G}{G}`, exactly Temur, into a reach/trample Hulk. |
| Bulk Up | ✗ | Trick. |
| Bumi, Unleashed | ◇ | 5/4 trample, earthbend 4 on entry; the land-only extra combat needs damage (R3). |
| Burner Rocket | ✗ | Vehicle trick. |
| Burrog Befuddler (craft C) | ✗ | Flash -1/-0. |
| Burst Lightning | △ | 2/4 damage any target, non-Lesson (R1). |
| Buster Sword | ✗ | Combat damage (R3). |
| Captain Howler, Sea Scourge | △ | Discard payoff; only Sokka discards here. |
| Caught in the Crossfire | △ | 2 to each non-outlaw creature — a sweeper, non-Lesson, OTJ (R9). Iroh's Demonstration already pings. |

### Batch 2 (31–60)

| Card | 54 | Note (rule) |
|---|---|---|
| **Chameleon, Master of Disguise** | ★ | Enters as a copy of a creature you control "except his name is Chameleon" — so NO legend rule. A second Iroh (insurance, R5), a second Uncle Iroh (Lessons `{2}` cheaper), or a re-run of Bumi's / Guru Pathik's / Toph's enter trigger. |
| Channeled Dragonfire (craft U) | △ | 2 damage sorcery, non-Lesson (R1). |
| Charred Foyer // Warped Space | ★ | Upkeep: exile the top card, play it this turn — repeatable card advantage (R5). Doc Aurlock makes those casts `{2}` cheaper; Warped Space casts one free. |
| Choreographed Sparks | ◇ | `{R}{R}` instant: copy an instant/sorcery you control — a second Capstone or Germination off one `{1}` flashback. Non-Lesson. |
| Coati Scavenger (craft U) | △ | Descend 4 counts PERMANENT cards; Lessons are instants/sorceries (R2), so it rarely turns on. |
| Colorstorm Stallion | △ | Opus needs 5+ mana SPENT (R6). |
| Colossal Rattlewurm (craft R) | ✗ | Desert deck card. |
| Conduct Electricity | △ | 6 damage, 5 mana, non-Lesson (R1). |
| Coral Sword | ✗ | Equipment trick. |
| Cosmic Cube | △ | Free cast on ATTACK up to the greatest attacking power — Thor/Iroh 5 — but the deck rarely attacks (R3). |
| Crash and Burn | △ | 6 damage `{3}{R}` instant, non-Lesson (R1). |
| Cuboid Colony | △ | Increment reads mana SPENT (R6). |
| Cunning Maneuver | ✗ | Trick. |
| Curious Forager (craft U) | △ | Forage exiles three yard cards to return a permanent — eats Lessons (R8). |
| Daring Waverider | △ | One free MV≤4 instant/sorcery from the yard on entry; Iroh already does that for `{1}`. |
| Decadent Dragon (craft R) | △ | Front `{2}{R}{R}` flier castable; back `{2}{B}` is not (⚠back:B). Attack trigger (R3). |
| Desert Were-Worm | ✗ | Mountain-count beater. |
| Devoted Duelist | △ | 1 damage on second spell; tiny. |
| Disruptor of Currents (craft R) | △ | Flash convoke bounce body. |
| Divergent Equation | △ | Returns X instants/sorceries to HAND — with Iroh they are better left in the yard at `{1}`. |
| Divining Duelist (craft C) | △ | Flash body, loot or tap. |
| Doc Ock's Henchmen | △ | Connives on attack (R3). |
| **Doc Samson, Super Psychiatrist** | ★ | "Put that many plus one" counters — `engines` reads 10 counter enablers and NO payoff; this is the payoff (Bumi, Earthbending Lesson, Rockalanche, Germination, Leaves II, Guru, Toph). Also "{T}: Add X mana of any one color, X = power" — a 3+ mana rock. |
| Don & Raph, Hard Science | ✗ | Attack-gated affinity, almost no artifacts here (R3). |
| Donatello's Technique (craft U) | ◇ | Draw two for `{2}{U}`; non-Lesson so Iroh recasts it at full cost (R1). Sneak is combat (R3). |
| Donatello, Gadget Master | ✗ | Sneak/combat artifact copy. |
| Dracosaur Auxiliary | ✗ | Saddle attacker. |
| **Dragonback Assault** (craft M) | ★ | `{3}{G}{U}{R}`: 3 to each creature and planeswalker, then "Landfall — create a 4/4 flying Dragon." Elemental Teachings for `{1}` puts TWO lands in a turn → two Dragons. Kills our own 2-drops; Iroh/Thor/Bumi survive. |
| Dragonclaw Strike | △ | Double P/T + fight, 6 mana non-Lesson. |
| Dundoolin Weaver (craft U) | △ | Needs three creatures; 14 here. |

### Batch 3 (61–90)

| Card | 54 | Note (rule) |
|---|---|---|
| **Earth's Mightiest Heroes** | ★ | Top eight: put a creature onto the battlefield (all of them with teamwork 5), "Put the rest into your graveyard" — mills ~7, i.e. Lessons into the yard (R2), and finds Iroh/Bumi/Thor. Non-Lesson, so a full-cost recast (R1). |
| Echo, Perceptive Prodigy | ◇ | `{1}`, T: copy a triggered ability from a creature — a second Bumi / Guru Pathik / Toph enter trigger. |
| **Eddymurk Crab** | ★ | Flash 5/5, "{1} less for each instant and sorcery card in your graveyard" (17 in the list, R2) — often 2–4 mana; taps two creatures on entry. A body for a deck with 33 power (R3). BLB, early 2027 (R9). |
| **Electro, Assaulting Battery** | ★★ | "Whenever you cast an instant or sorcery spell, add {R}" and red mana never empties — each `{1}` Lesson flashback refunds itself (R7). With Iroh the recast chain is close to free. 2/3 flier; leaves → X damage. |
| Electroduplicate (craft R) | ◇ | Hasty token copy of your creature for a turn — a second Bumi enter trigger; flashback. |
| Elementalist Adept | △ | Flash prowess body. |
| Ember Island Production | ◇ | 5-mana sorcery: a token copy "except it's not legendary" — a permanent SECOND IROH (R5). Non-Lesson. |
| **Emeritus of Conflict // Lightning Bolt** | ★ | Third spell each turn → prepared → cast a copy of Lightning Bolt. Iroh makes three spells a turn routine: a repeatable 3-damage instant (interaction). |
| Emeritus of Ideation // Ancestral Recall | ★ | Enters prepared: Ancestral Recall, draw three. 5/5 flier, ward 2. Its re-prepare EXILES eight yard cards — optional, and it fights the engine (R8); do not use it. |
| Enduring Curiosity | △ | Combat-damage draw (R3). |
| **Energybending** | ★ | Lesson `{2}` instant: "Draw a card"; lands gain all basic types this turn. With Iroh a `{1}` cantrip every turn; same turn, Rockalanche earthbends for EVERY land and Solstice Revelations' Mountain count is your land count. |
| Eshki Dragonclaw (craft R) | ◇ | Creature + noncreature same turn → draw and two counters. 14 creatures here; real but conditional. |
| Essence Burn (craft U) | △ | Black/green targets only. |
| Explosive Derailment | △ | 4 damage or kill an artifact; non-Lesson; OTJ. |
| Extravagant Replication | △ | Upkeep token copy; Iroh copies die to the legend rule. |
| Fated Firepower | △ | Damage amplifier; only Thor and Death to Our Enemies ping. |
| Fear of Impostors (craft U) | ◇ | Flash counterspell on a 3/2. DSK. |
| Fear of Missing Out (craft R) | ✗ | Attack/delirium combat. |
| Festival of Embers | ✗ | Exiles everything bound for your graveyard (R8). |
| Fiery Annihilation | △ | 5 damage, non-Lesson. |
| Fire Magic | △ | Tiered sweeper, non-Lesson. |
| Fire Sages | ✗ | Firebending attacker (R3). |
| Fire-Rim Form | ✗ | Aura trick. |
| Firebender Ascension | ✗ | Attack triggers (R3). |
| **Firebending Lesson** | ★★ | Lesson `{R}` instant: 2 damage, kicked 5. Flashback `{1}` (+`{4}` to kick). Removal on the deck's own terms (R1). Owned ×2. |
| Firebending Student | ✗ | Attack mana (R3). |
| Flame Lash (craft C) | △ | 4 damage, 4 mana. |
| Flashback (craft R) | ✗ | Iroh already grants flashback to everything. |
| Floodpits Drowner | ◇ | Flash: tap + stun, then `{1}{U}`, T shuffles the stunned creature away — real removal on a 2-drop. DSK. |
| Frantic Firebolt | ◇ | X = 2 + instants/sorceries in your yard — often 7+ here (R2). Non-Lesson; WOE, early 2027. Owned ×2. |

### Batch 4 (91–120)

| Card | 54 | Note (rule) |
|---|---|---|
| Fuel the Flames | △ | 2 to each creature (ours too), cycling; non-Lesson. |
| Full Throttle | ✗ | Extra combats (R3). |
| Fulminous Forte (craft U) | ◇ | 1 to each opposing creature, or 5 to one. Flexible, non-Lesson (R1). |
| Galuf's Final Act | ✗ | Combat trick. |
| Galvanize | △ | 3 damage, 5 if you drew two this turn; non-Lesson; MKM (R9). |
| **Garrison Excavator** | ★ | "Whenever one or more cards leave your graveyard, create a 2/2" — every Iroh recast is a card leaving the yard (R7): a token per flashback. Board for a 33-power deck (R3). 3/4 menace. |
| Genji Glove | ✗ | Combat equipment. |
| Giant-Sized Flying Ant | △ | Flash flier, tap/untap. |
| Giantfall | ◇ | Your creature deals its power to theirs (Iroh/Thor 5), or kill an artifact; non-Lesson. |
| Glacial Dragonhunt (craft U) | ◇ | Loot, and discarding a NONLAND card deals 3 — discard a fat Lesson straight into the yard (R2). Sorcery, non-Lesson. |
| Glamer Gifter | △ | Flash flier trick. |
| Glamermite | △ | Flash flier tap/untap. |
| Gleaming Geardrake | △ | One Clue on a 1/1 flier. |
| Glen Elendra Guardian | ◇ | Flash 2/3 flier that counters one noncreature spell (`{1}{U}`, remove its counter) and becomes a 3/4. |
| Goblin Firebomb (craft C) | △ | `{7}`: destroy any permanent; colourless. |
| Gogo, Master of Mimicry | ◇ | Copies Bumi/Guru/Toph triggers X times; slow. |
| Goldvein Hydra | △ | X-sized hasty trampler; mana sink. OTJ. |
| Goliath Daydreamer | ✗ | Instants/sorceries cast from hand are EXILED instead of hitting the yard — starves Iroh (R8). |
| Great Train Heist | ✗ | Combat spree. |
| Guttersnipe (craft U) | ◇ | 2 to each opponent per instant/sorcery — with `{1}` recasts that is a real clock (R7). |
| Gwen Stacy // Ghost-Spider | ◇ | Enters, exiles the top card, playable while she stays — +1 card; flip needs white. |
| Harbinger of the Tides | △ | UU bounce of a tapped creature. |
| Hazoret, Godseeker | ✗ | Speed deck card. |
| Heated Argument | △ | 6 damage; its bonus exiles a yard card (R8, optional). |
| Herd Heirloom | △ | Creature-only mana. |
| Hidetsugu's Second Rite | ✗ | Exact-10-life kill. |
| High Fae Trickster | △ | Flash for sorceries — but Iroh's grant is "during your turn" only, so it doesn't extend the recasts. |
| Hire a Crew | ✗ | Combat token trick. |
| How to Start a Riot | △ | Lesson (+1 count, R2) with a combat effect (R3). Filler only. |
| Humbling Elder | △ | Flash -2/-0. |

## 5. Consolidated plan (live)

(after batch 1)
