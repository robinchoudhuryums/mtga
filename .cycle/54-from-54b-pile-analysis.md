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
- **Batch 5: the card-advantage gap has an owned, cheap answer that reads THIS deck's engine.** Kishla Skimmer draws whenever a card leaves the yard on your turn — which is every Iroh recast. With Garrison Excavator (batch 4), 'leaves the graveyard' is now two payoffs deep.
- **Card-advantage candidates are now plentiful** (Kishla, Kraum, Mechanist, Loot, Marang River Regent, Mind into Matter, Inspiring Call, Bruce Banner, Charred Foyer, Energybending). The constraint is SLOTS, not options.
- **Batch 6: R6 makes MANA-VALUE payoffs the deck's finishers.** Thor (already in), Ovika and Niv-Mizzet all scale with the RECAST spell's mana value, so a `{1}` Capstone is worth 7. Prismari (storm) and Planetarium (free top card) are the same 'many cheap casts' idea. A spicy top-end package exists; it competes for the 5–7 slot with Bumi/Iroh/Thor.
- **Protection for Iroh found:** My Precious (permanent hexproof, colourless) is the first answer that does not expire.
- **Batch 7: owned Lesson protection exists.** Redirect Lightning is a Lesson, so it is a `{1}`+`{2}` answer to removal on Iroh EVERY turn from the yard — the strongest R1+R5 overlap in the pile.
- **Batch 8: COPY engines keyed on 'cast from anywhere other than your hand' or 'single target' are R7 in its purest form** (Spider-Verse, Spinerock Tyrant, Spider-Man 2099's end-step shot). They make each `{1}` recast worth two. A 'copy' route is a real variant direction — see §5 Routes.
- **Batch 9: a 'make the recast free' cluster** — Bilbo (−1 non-hand), Temur Battlecrier (−1 per power-4 creature), The Scarlet Witch (−2 on MV 4+), The Fire Crystal (−1 red). Iroh's `{1}` is already cheap, so these only matter at volume; one is plenty.
- **Guru Pathik turns every Lesson cast into a counter** — which is what makes Terrasymbiosis a reliable card a turn here (the counters axis finally has a payoff, with Doc Samson from batch 2).
- **Batch 10: cheap non-Lesson DRAW spells are the exception to R1.** Twinned Vision (draws two when not cast from hand) and Vision of Love (discard a fat Lesson, draw two) are cheap enough that Iroh's full-price recast is still a card-advantage engine every turn — and the discard half FEEDS the yard.

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

### Batch 5 (121–150)

| Card | 54 | Note (rule) |
|---|---|---|
| Identity Echo (craft R) | △ | Polymorph a creature into the next creature off the top. |
| Idol of the Deep King | △ | Flash, 2 damage on entry. |
| Illusion Spinners | △ | 5-mana flier, hexproof while untapped. |
| Impossible Inferno (craft C) | △ | 6 damage, non-Lesson. |
| Impostor Syndrome | ✗ | Combat damage (R3). |
| **Inspiring Call** | ★ | "Draw a card for each creature you control with a +1/+1 counter" + indestructible to them. Counters here: Bumi, Germination (two on EACH creature), Leaves II, Guru, Sokka, and every earthbent land is a creature with counters. CA + protection (R5). |
| Inti, Seneschal of the Sun | △ | Attack-triggered discard (R3). |
| Iron Fist, Living Weapon | △ | Needs spells targeting your own creature. |
| Iron Spider, Stark Upgrade | △ | Artifact-creature counters; none here. |
| **Jeong Jeong, the Deserter** | ★ | Exhaust `{3}`: "When you next cast a Lesson spell this turn, copy it." One copied Capstone / Symposium / Germination from a `{1}` flashback. Once per game, but huge. |
| Judgment Bolt (craft R) | △ | 5 damage, Equipment rider dead here. |
| Kindle the Inner Flame | △ | Hasty copy for a turn; flashback needs Elementals. |
| Kirol, Attentive First-Year | ◇ | Tap two creatures: copy a triggered ability (Bumi/Guru/Toph). R/W hybrid, castable on R. |
| **Kishla Skimmer** | ★★ | `{G}{U}` 2/2 flier: "Whenever a card leaves your graveyard during your turn, draw a card" (once a turn). Every Iroh recast is a card leaving the yard → a card every turn for two mana (R5, R7). |
| Kitnap | ◇ | Steal a creature (stun if no gift). Interaction since 2026-10-07 steal-aura fix. |
| Kraum, Violent Cacophony | ★ | Second spell each turn: counter + draw (R7). |
| **Leyline of the Guildpact** | ★ | Perfect fixing; makes Rockalanche earthbend for EVERY land and Solstice's Mountain count your land count; Bloom Tender taps for five. Free from the opening hand. |
| Light of Judgment (craft C) | △ | 6 damage, non-Lesson. |
| Lithobraking (craft U) | △ | Sweeper needing an artifact. |
| Loki Laufeyson | ◇ | Copy the next instant/sorcery with MV ≤ his power (2, or 4 powered up): a second Combustion Technique / Iroh's Demonstration. |
| Long River Lurker | △ | Combat blink (R3). |
| Long-Bodied Grey Dog (craft C) | △ | Flash reach + Treasure. |
| **Loot, the Pathfinder** | ★ | `{2}{G}{U}{R}` double strike, vigilance, haste; three once-each exhausts: add three mana, **draw three**, deal 3. CA + ramp + removal on one Temur card (R5). |
| Maelstrom Artisan (craft R) | ✗ | Land destruction. |
| Mai, Jaded Edge | ✗ | Combat (R3). |
| **Marang River Regent // Coil and Catch** | ★ | Omen instant `{3}{U}`: "Draw three cards, then discard a card" — discard a fat Lesson into the yard (R2); or a 6/7 flier that bounces two. Non-Lesson. |
| Meltstrider Eulogist | △ | Draws when a creature with a counter dies. |
| Might of the Meek | △ | `{R}` cantrip. |
| **Mind into Matter** | ★ | `{X}{G}{U}`: draw X, then put a permanent with MV ≤ X from hand onto the battlefield — X=6 is draw six and a free Iroh/Bumi. Scales with the deck's ramp. |
| Mirror Room // Fractured Realm | ◇ | Fractured Realm (7): every triggered ability triggers twice — Bumi, Thor, Death to Our Enemies. Expensive. |

### Batch 6 (151–180)

| Card | 54 | Note (rule) |
|---|---|---|
| Mister Fantastic, Reed Richards | ◇ | Draws when tokens enter — Death to Our Enemies makes a Treasure per noncreature spell (R7), plus Clues/Food. |
| Mockingbird | △ | Copy keeps the name — an Iroh copy dies to the legend rule. |
| Monastery Messenger | △ | Puts a yard card back on top — worse than leaving it for Iroh. |
| Mondo Gecko | △ | Combat-damage draw (R3). |
| Mouth of the Storm | △ | 7-mana flier. |
| **My Precious // Allure of Power** | ★ | `{3}` Equipment: "Equipped creature has hexproof and can't be blocked." Equip `{2}` + 2 life onto Iroh = permanent protection for the engine (R5). Colourless. The Adventure needs black — ignore it. |
| Naga Fleshcrafter | △ | Copy keeps the name (legend rule). |
| Nature's Rhythm (craft R) | ◇ | `{X}{G}{G}`: tutor a creature MV ≤ X onto the battlefield — X=6 is Iroh. Harmonize recast. |
| Nebula Dragon | △ | 7-mana flier, 3 damage. |
| New Generation's Technique | △ | Two basics for 4; non-Lesson. Elemental Teachings does this better at `{1}`. |
| **Niv-Mizzet, Visionary** | ★ | "Whenever a source you control deals noncombat damage to an opponent, you draw that many cards." Thor deals each spell's MANA VALUE (R6): a `{1}` Capstone flashback = 7 to face, draw 7. Death to Our Enemies' 7 too. Spice finisher. |
| Norman Osborn // Green Goblin | △ | Flip needs black. |
| North Wind Avatar | ✗ | "From outside the game" — nothing to fetch in Bo1. |
| Nova Hellkite | △ | Flier, ping. |
| **Oko, the Ringleader** | ★ | +1: draw two, discard one or two — discard the fat Lessons into the yard (R2). −1 Elks. CA (R5). |
| Old Fat Spider | △ | 6/7 reach; draws only when targeted. |
| Old Fat Spider Can't See Me | ★ | Hexproof on Iroh for the Saga's life, neutralise one creature, draw two (R5). Saga → Guru Pathik finds it. |
| Omni-Changeling | △ | Copy keeps the name. |
| Opera Love Song (craft U) | ◇ | Exile two, play them — +2 cards at instant speed. Non-Lesson. |
| Outlaws' Fury | ✗ | Combat pump. |
| Overprotect | ◇ | One-shot hexproof + indestructible for Iroh. BLB. |
| **Ovika, Enigma Goliath** | ★ | "Create X 1/1 Goblins, X = the mana VALUE" (R6): a `{1}` Capstone recast is seven hasty Goblins. 7 mana. Spice finisher. |
| Peerless Recycling (craft U) | ◇ | Return one or two permanent cards — a dead Iroh. |
| Pigment Wrangler (craft U) | △ | Prepared: copy your next instant/sorcery. |
| Pitiless Fists (craft U) | ◇ | Fight aura +2/+2 — Iroh fights at 7. |
| **Planetarium of Wan Shi Tong** | ★ | `{1}`, T: scry 2, and "whenever you scry or surveil, look at the top card… you may cast that card without paying its mana cost" (once a turn). A free spell every turn; Bumi's scry mode and Surveillance Room also trigger it. 6 mana, colourless. Spice. |
| Plumecreed Escort (craft U) | △ | Flash 2/1 flier, hexproof for a turn. |
| Price of Freedom | ◇ | LESSON: destroy an artifact (or land) + "Draw a card" — a `{1}` cantrip answer every turn. |
| **Prismari, the Inspiration** | ★ | "Instant and sorcery spells you cast have storm." Iroh chains three or four Lessons a turn → each copied once per earlier spell. 7/7 flier, ward–5 life. The spiciest finisher in the pile. |
| Prompto Argentum | ✗ | Needs 4 mana SPENT (R6). |

### Batch 7 (181–210)

| Card | 54 | Note (rule) |
|---|---|---|
| Pull Through the Weft | ◇ | Two nonland permanents back to hand (a dead Iroh) and two lands back to play — earthbent lands that died. 5 mana, GG. |
| Pym Particles | △ | Unblockable cantrip (R3). |
| Pyre Rhymer // Molten Tide | △ | Prepared ritual: Mountains add an extra `{R}` this turn; only 2 Mountains here. |
| Pyromancer's Goggles | ◇ | Its `{R}` spent on a red instant/sorcery copies it — a `{1}` Capstone flashback paid with Goggles mana is copied. 5-mana artifact. Spice. |
| Quistis Trepe | ◇ | Enters: cast an instant/sorcery from ANY graveyard, any mana. One-shot. |
| Radagast of Rhosgobel | △ | Creature discount + flash; 14 creatures. |
| Raiding Schemes (craft R) | ◇ | Noncreature spells gain conspire: tap two creatures sharing its colour → copy it. A copied Capstone each turn, if the board has two creatures. |
| Rapacious Dragon | △ | Flier + two Treasures. |
| Raph & Leo, Sibling Rivals | ✗ | Extra combat (R3). |
| Raphael, Ninja Destroyer | ✗ | Enrage mana (R3). |
| Raphael, the Nightwatcher | ✗ | Double strike / Sneak (R3). |
| Reckless Ransacking | ✗ | Trick. |
| Red Hulk | △ | 6/7 enrage pinger. |
| **Redirect Lightning** | ★ | LESSON: "Change the target of target spell or ability with a single target" (+ `{2}` or 5 life). Protection for Iroh at `{1}`+`{2}` from the yard, every turn (R1, R5). |
| Renet, Temporal Apprentice | ◇ | Flash: bounce every nonland permanent that entered this turn — an opponent's whole turn of plays. |
| Restore with Empathy (craft U) | ◇ | A dead Iroh back to hand, +4 life. |
| Return the Favor | ◇ | `{R}{R}`+`{1}`: copy an instant/sorcery (a recast Capstone) or redirect. Non-Lesson. |
| Riku of Many Paths (craft R) | △ | Modal spells — only Iroh's Demonstration and Origin of Metalbending are modal here. |
| Rimefire Torque | △ | Choose Human (9 here); three counters → copy an instant/sorcery. Slow. |
| Rite of Replication (craft R) | ◇ | Kicked: five token Bumis — five enter triggers (the legend rule then trims them). |
| Roamer's Routine | △ | Basic land ramp, non-Lesson. |
| Roar of Endless Song (craft R) | ◇ | Two 5/5 Elephants, then double the team. A Saga (Guru Pathik). Board for a tall deck. |
| Roving Actuator (craft U) | △ | Void-gated free cast. |
| Runaway Boulder (craft C) | △ | Flash 6 damage, colourless, LCI (R9). |
| Rydia's Return | ◇ | Two permanent cards back (Iroh), or +3/+3 team. |
| Rydia, Summoner of Mist (craft U) | ◇ | Landfall rummage — discard fat Lessons on every Elemental Teachings / Shared Roots land (R2); Summon replays Leaves from the Vine / Old Fat Spider Can't See Me. |
| **Sab-Sunen, Luxa Embodied** | ★ | Indestructible 6/6; "if it has an odd number of counters on it, draw two cards" — two cards every other turn (R5). Owned ×2. |
| Saheeli, Jewel of Avishkar (craft U) | ◇ | A flying Thopter per noncreature spell (R7) — board, no cards. |
| **Sanar, Unfinished Genius // Wild Idea** (craft U) | ★ | `{U}{R}` 0/4 that enters prepared: cast Wild Idea — "Search your library for an instant or sorcery card" — a tutor for Capstone / Combustion / Germination. Treasures on spell turns. |
| Savage Ventmaw | ◇ | Attacks → six mana that lasts the turn: a post-combat hard-cast of a fat Lesson. Rarely attacks (R3). |

### Batch 8 (211–240)

| Card | 54 | Note (rule) |
|---|---|---|
| Saved by the Shell (craft U) | ◇ | One-shot hexproof + indestructible; no Turtles here for the discount. |
| Scorching Dragonfire (craft C) | △ | 3 damage, exile; non-Lesson. |
| Season of Gathering | ◇ | Modes: counters, destroy all artifacts or enchantments, or draw = greatest power (Iroh/Thor 5, a pumped Bumi more). 6 mana, non-Lesson. |
| Seifer Almasy | △ | Free MV≤3 recast only on combat DAMAGE (R3); Iroh already makes those `{1}`. |
| Seize Opportunity (craft C) | ◇ | Instant: exile two, play them — +2 cards. |
| Self-Destruct | △ | Your creature deals its power to a target and itself. |
| Self-Reflection | △ | Token copy keeps the name (legend rule). |
| Serpent of the Pass | ◇ | `{1}` less per noncreature, nonland card in the yard (R2), flash with three Lessons — a cheap 6/5. Cut from 54 once already for engine slots. |
| Shantotto, Tactician Magician | ✗ | Reads mana SPENT (R6). |
| Slickshot Lockpicker | △ | One flashback grant; Iroh makes it redundant. OTJ. |
| Smuggler's Surprise (craft R) | ◇ | Mill four (Lessons into the yard, R2) and take two creatures/lands; `{1}` mode: hexproof + indestructible to power-4+ creatures (Iroh, Thor). Instant. OTJ, gone early 2027 (R9). |
| Songcrafter Mage (craft R) | △ | One harmonize grant; redundant with Iroh. |
| Sorceress's Schemes | △ | Returns an instant/sorcery to HAND — worse than Iroh's `{1}`. |
| Sozin's Comet | ✗ | Firebending (R3). |
| **Spectral Sailor** | ★ | `{U}` flash flier; "{3}{U}: Draw a card" — a repeatable mana sink for a ramp deck (R5). |
| Sphinx of False Conclusions (craft R) | △ | Loots on attack (R3). |
| Sphinx of Forgotten Lore | △ | Flashback at FULL cost on attack; Iroh's `{1}` is strictly better for Lessons (R1). |
| Spider Manifestation | ◇ | R/G mana dork that untaps on a MV 4+ spell — a `{1}` Capstone recast is MV 7. |
| **Spider-Man 2099** (craft R) | ★ | End step: if you cast a spell from anywhere other than your hand, deal damage equal to his power — every Iroh turn. Double strike makes it 2 per turn as written (power 2). Interaction (R5). |
| Spider-Punk | △ | Uncounterable spells; Spider tribal. |
| **Spider-Verse** | ★ | "Whenever you cast a spell from anywhere other than your hand, you may copy it" (once a turn) — every Iroh turn copies the best recast: a second Capstone / Germination / Combustion. 5 mana. Spice engine. |
| **Spinerock Tyrant** | ★ | 6/6 flier: "Whenever you cast an instant or sorcery spell with a single target, you may copy it" — Combustion Technique, Firebending Lesson, Iroh's Demonstration (4-damage mode), True Ancestry. Repeat removal (R5). |
| Spinneret and Spiderling | ✗ | Spider attacks. |
| Starfield Vocalist | ◇ | ETB triggers fire twice — Bumi, Guru Pathik, Toph. |
| **Steal the Show** | ★ | Mode 2: damage = instants/sorceries in YOUR yard (R2, often 5–8); mode 1: discard any number and redraw — dump fat Lessons into the yard. Interaction + enabler. |
| Stingcaster Mage (craft M) | △ | One flashback grant on a hasty 2/1. |
| Stingerquill Voxmancer // Vicious Verse | △ | 1 damage each upkeep (B/R hybrid, castable). |
| Stoic Sphinx (craft R) | △ | Flash flier, conditional hexproof. |
| Stormscale Scion | ◇ | Storm on a 4/4 flying Dragon — Iroh turns cast several spells first. |
| Stormsplitter | △ | Hasty copies per instant/sorcery (R3). |

### Batch 9 (241–270)

| Card | 54 | Note (rule) |
|---|---|---|
| Strife Scholar // Awaken the Ages | △ | Prepared: two 2/2 Spirits for 6. |
| Summon: Leviathan | ✗ | Chapter I bounces OUR non-sea creatures too — Iroh included. |
| **Summon: Titan** | ★ | Saga 7/7: I "Mill five" (Lessons into the yard, R2); II "Return all land cards from your graveyard to the battlefield" — Elemental Teachings sends two lands to the yard every cast. A Saga (Guru Pathik finds it). |
| Super Speed | ✗ | Aura trick. |
| Super Strength | △ | +4/+4, trample, ward 1 on Iroh — thin protection. |
| **Survey Mechan** (craft U) | ★ | Hexproof flier; `{10}` sac costs `{X}` less per DIFFERENTLY NAMED land — this manabase runs ~16 names, so it is close to free: 3 damage, draw three, +3 life. CA + interaction, colourless. |
| Sword of Wealth and Power | ◇ | Equipped creature has protection from instants AND sorceries — most removal — so Iroh is safe. The copy half needs combat damage (R3). BIG, early 2027 (R9). |
| Sygg (craft R) | △ | Transform needs white. |
| Synchronized Charge | △ | Two counters + harmonize. |
| Tam, Mindful First-Year | ◇ | Iroh (G/U/R) gets hexproof from green, blue and red; with Leyline, from every colour. Tam itself is exposed. |
| Teach by Example (craft U) | ◇ | Copy your next instant/sorcery — a second Capstone. |
| Technodrome | △ | Artifact sac engine; few artifacts. |
| **Temur Battlecrier** (craft R) | ★ | "During your turn, spells you cast cost {1} less for each creature you control with power 4 or greater" — it is 4/3 itself; Iroh, Thor, Bumi and every earthbent 4/4 land count. Every `{1}` Lesson recast goes FREE, and hard-cast Lessons shrink. |
| Temur Tawnyback | △ | 6-mana loot body. |
| Terrapact Intimidator | △ | Landers or counters. |
| **Terrasymbiosis** | ★ | "Whenever you put one or more +1/+1 counters on a creature you control, you may draw that many cards" (once a turn). Guru Pathik puts a counter on every Lesson cast — a card per turn; Germination draws two. CA (R5). |
| Terror of the Peaks | △ | Pings on creatures entering; earthbend does not make a land ENTER. |
| Tetsuko Umezawa, Pursuer | ✗ | Combat (R3). |
| **The Arkenstone // Seek the Heart** | ★ | `{5}` colourless: "Creatures you control get +1/+1" and "At the beginning of your end step, draw a card" — repeatable CA. The Adventure needs white. |
| The Dawning Archaic | ★★ | Already in the tune plan (second recast engine). |
| The Earth King | ◇ | 4/4 Bear on entry; land ramp on power-4 attacks (R3). |
| The Emperor of Palamecia | △ | Flip needs 4 mana SPENT (R6); its mana is noncreature-only ramp. |
| The Fire Crystal | ◇ | Red spells `{1}` less — red Lesson recasts (Combustion, Capstone, Firebending Lesson, Demonstration, Solstice) go free. |
| The Last Agni Kai | △ | Fight, non-Lesson. |
| The Legend of Kyoshi // Avatar Kyoshi | ◇ | I: draw = greatest power (Iroh 5); III flips into a mana Avatar. 6 mana, GG. A Saga (Guru). |
| **The Legend of Roku // Avatar Roku** | ★ | I: exile three, play them — +3 cards (R5); II: a mana; III: a firebending 4 Avatar. A Saga (Guru). |
| The Lord of the Eagles | △ | Flier-cost discount; few fliers. |
| **The Mechanist, Aerial Artisan** | ★ | A Clue per noncreature spell (R7) — 21 here plus every recast. |
| The Scarlet Witch | ◇ | Instants/sorceries MV 4+ cost `{X}` less (X = her power, 2) — a recast Capstone/Symposium/Germination is FREE (`{1}` − 2); hard-casts shrink too. |
| The Unagi of Kyoshi Island | △ | Draws only when the OPPONENT draws two. |

### Batch 10 (271–300)

| Card | 54 | Note (rule) |
|---|---|---|
| **The Vision** | ★ | Colourless 2/5 flier: per noncreature spell, one unused mode a turn — "Draw a card", indestructible, double strike. A card a turn plus self-protection (R5, R7). |
| The Wondrous Wasp | ◇ | Flash: tap a creature, it loses all abilities while Wasp stays — soft removal on a 2-drop. |
| Theorist's Proxy (craft R) | ◇ | Flash 0/3; a Jace token that surveils/draws. |
| Thief's Knife | △ | Combat-damage draw (R3). |
| Thrill of Possibility (craft C) | ◇ | Discard (a fat Lesson, R2), draw two. Instant. |
| Thunder Magic | ◇ | 2 / 4 / 8 damage by tier; non-Lesson, so its `{R}`+tier recasts at full price (R1). |
| Thunderdrum Soloist | ◇ | 1 damage to each opponent per instant/sorcery — a `{1}` recast pings. |
| Tishana's Tidebinder | ◇ | Flash: counter an activated/triggered ability and blank the source. LCI (R9). |
| Trade the Helm | △ | Exchange control; cycling. |
| Traxos, Academy Guardian (craft U) | △ | Cheap flier after a noncreature spell. |
| Truck Toss | △ | 4 damage, no Vehicles. |
| Tweeze | ◇ | 3 damage any target, then rummage — discard a fat Lesson. Non-Lesson. |
| Twin Blades | ✗ | Combat equipment. |
| Twin Bolt (craft C) | △ | 2 damage split. |
| Twinflame Tyrant | ◇ | Doubles our damage to them: Thor's MV pings, Death to Our Enemies' 7 becomes 14. 5-mana flier. Spice. |
| **Twinned Vision** (craft C) | ★ | "Draw a card. If this spell wasn't cast from your hand, draw two cards instead." Iroh recasts it (non-Lesson, `{1}{U/R}`) → TWO cards every turn; it also has its own flashback. A common (R5). |
| Ty Lee, Chi Blocker | ◇ | Flash: lock a creature down while Ty Lee stays. |
| **Ugin, Eye of the Storms** | ★ | `{7}` colourless: on cast, exile a coloured permanent; +2: gain 3, draw a card. Removal + CA in one finisher. Spice. |
| Unending Whisper (craft C) | △ | `{U}` cantrip sorcery, non-Lesson. |
| Unstoppable Plan (craft R) | △ | Untap nonland permanents each end step — mana creatures twice. |
| Unsubtle Mockery | ◇ | 4 damage + surveil 1 (surveil feeds Planetarium); non-Lesson. |
| Ureni's Rebuff (craft U) | △ | Bounce sorcery. |
| Ureni, the Song Unending | ◇ | 8-mana 10/10 flier: enters, deal damage = lands you control, divided among their creatures — a one-sided sweep. Spice top end. |
| Valley Floodcaller | △ | Flash for sorceries; Iroh's grant is your turn only. |
| Vanille, Cheerful l'Cie | ◇ | Enters: mill two, return a permanent card — a dead Iroh. |
| Venus, Torn Between Worlds | △ | Combat draw (R3). |
| Vibrant Outburst | ◇ | 3 damage any target + tap; non-Lesson (full `{U}{R}` recast). |
| Violent Urge (craft U) | ✗ | Trick. |
| Visage Bandit | △ | Copy keeps the name. |
| **Vision of Love** | ★ | "Sacrifice an artifact or discard a card. If you do, draw two" — discard a fat Lesson into the yard (R2) and draw two. Instant `{1}{R}`; Iroh recasts it every turn at full price (`{1}{R}`): loot-two each turn. Owned. |

## 5. Consolidated plan (live)

(after batch 1)
