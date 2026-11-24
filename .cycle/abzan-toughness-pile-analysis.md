# Abzan toughness (Hamza) — analysis (TEMPORARY working doc)

**Status: IN PROGRESS — all 163 cards graded (batches 1–4); consolidated plan drafted;
awaiting owner picks before /draft-deck.** Delete once the deck is drafted and the
findings are folded into its `#: notes:` block. A scratchpad, not a source of truth —
decks/ are.

**Source list:** the owner's 163-card pile (2026-11-24), commander **Hamza, Might of the
Yathan** (WBG, 5/6, MV 5, own 0). Format **Historic Brawl** (100-card singleton; every
pile card checked brawl-legal). 58 of the 163 already sit in other decks — still
candidates here, since copies are shared across decks (CLAUDE.md "Decks share the
collection"). No deck exists yet, so there is no Builder project yet: it is created with
`builder.py new <slug> --decks <id>` the moment /draft-deck writes the deck, and the
reasons below are copied into it then.

## 1. The decision framework

Hamza: *"Whenever a creature you control is turned face up, it endures X, where X is that
creature's toughness. / Landfall — Whenever a land you control enters, seek a creature
card and manifest it."*

**F1 — Toughness is the damage stat only while an ENABLER is out.** Enablers in the pile:
global — Felothar the Steadfast, Assault Formation; T>P-gated — Ancient Lumberknot,
Bedrock Tortoise, Tapestry Warden, Ghalta the Immovable, The Kingpin of Crime (on attack,
pay 2 life); pump-by-gap — Doran, Besieged by Time (X = T−P, so an attacker swings for its
toughness AND grows as a blocker); single-creature — Bark of Doran, Gauntlets of Light, Bill
the Pony, Teyo (+1 perpetual base power = toughness). Off-pile: Arcades, Walking Bulwark,
Belligerent Brontodon, Solid Footing, Streetwise Negotiator, Huatli the Sun's Heart. **Target
5–7 enablers** so one is out by turn 4 most games; without one a 0/5 is a wall. A low-power
high-toughness card is graded on its toughness *given that density*.

**F2 — Power-capped clauses are UPSIDE here (the owner's P/T-swap rule).** Our best bodies
have power 0–1 (Felothar 0/5, Doran 0/5, Bedrock 0/6, Walls 0/30, Crystal Barricade 0/4,
Amaranthine Wall 0/6, Lumberknot 1/4, Flatman 1/10, Kingpin 1/5). So:
- recursion capped on POWER returns our best cards: Smile at Death (two power ≤2 a turn),
  Slumbering Walker (power ≤2), Nethroi (total power 10 = five 0-power walls),
  Ruthless Technomancer (power ≤ X artifacts; X=1 returns the 0/30 Walls), Body Launderer
  (≤ its 3);
- "draw if power 2 or less" (Eagle of Deliverance), "power 2 or less enter → draw"
  (Enduring Innocence) are near-unconditional;
- Delney's "power 2 or less can't be blocked by power 3 or greater" makes the toughness
  attackers evasive;
- Destined Confrontation ("keep total power 4 or less") is a ONE-SIDED wrath for us;
- power-based removal aimed at us (Abzan Charm's mode, "power 4 or greater") whiffs.
Conversely, "equal to its POWER" payoffs are weak (Madame Null, Jenova, Golden-Tail
Trainer, Ruthless Technomancer's Treasures, Body Launderer's own cap) and "equal to its
TOUGHNESS" payoffs are strong (Felothar's sac-draw, South Wind Avatar, Stoneglare/Garruk
lifegain, Kin-Tree Invocation, Abzan Monument, Last March).

**F3 — Hamza turns lands into creatures, so landfall COUNT is a payoff multiplier.** Every
land = a 2/2 face-down body plus a creature pulled out of the library. Extra land drops
(Thalia and The Gitrog Monster, Druid Class, Nog, Karametra's fetch, Fecund Greenshell's dig,
Braulios) are each worth an extra 2/2 a turn. Fetchlands count twice. Lands from the
graveyard (Nog, Kagha, Eerie Ultimatum) re-trigger it.

**F4 — Turning face up is NOT entering and NOT casting.** A flipped creature gets no ETB
trigger, no "if you cast it", no kicker, no "enters with" counters, and no cost reduction
(Doran's {1} discount, Ghalta's {X} discount do not apply — you pay the printed cost).
So the ideal flip is a creature whose value is STATIC or P/T, with a low cost relative to its
toughness. Consequences:
- Towering Titan and Darksteel Hydra flip as 0/0 and DIE (endure 0) — hardcast only;
- Slumbering Walker flips as a full 4/7 (no −1/−1 counters) → endure 7;
- Yathan Roadwatcher, Bill the Pony, Severance Priest, Fecund Greenshell's trigger, Glint
  Weaver, Flourishing Hunter lose their ETB when flipped (still fine when cast).
Flip-value table (cost → endure): Crystal Barricade {1}{W} → 4 · Ancient Lumberknot 4 → 4 ·
Flatman 4 → 10 · Amaranthine Wall {4} → 6 · Doran 4 → 5 · Felothar 4 → 5 · Bedrock Tortoise
4 → 6 · Kingpin 3 → 5 · Betor 5 → 7 · Ivorytusk 5 → 7 · Slumbering Walker 5 → 7 · Walls of
Ba Sing Se {8} → 30.

**F5 — Free and cheap flip outlets are worth more than their text reads.** Hauntwoods
Shrieker's `{1}{G}: Reveal target face-down permanent. If it's a creature card, you may turn
it face up` flips a manifested Walls of Ba Sing Se (8 mana) for 2 → endure 30. Harrowing
Swarm cuts every current face-down's flip by {2} and adds a counter. Rok-Tahk turns every
face-down 2/2 into a {G}{G} source to pay flips.

**F6 — Two LOOPS live in this pile; build the manabase for them.**
- **Ashaya, Soul of the Wild + Hamza:** nontoken creatures are Forest lands, so a face-down
  manifest entering IS a land entering → landfall → seek + manifest → … until the library
  has no creature card left. One trigger manifests the whole creature suite. Beorn's
  Hospitality / Claim the Kingdom / Druid Class ride the loop (a counter or a life per
  body).
- **Threats Around Every Corner + Hamza:** face-down enters → basic onto the battlefield →
  landfall → manifest → … until basics or creatures run out. Needs BASICS in the 100.
Both are mandatory but terminate (seek finds nothing when no creature card remains). They
reward a creature-dense list (~35+ creatures) and, for Threats, ~12+ basics.

**F7 — Total and greatest toughness are both trivially high here.** Betor, Kin to All's 10/20/40
thresholds (draw · untap team · opponents lose half) are met by a couple of walls; one Walls
of Ba Sing Se clears 40 alone. "Greatest toughness" scalers (Kin-Tree Invocation, Abzan
Monument, Last March of the Ents, Ghalta's discount, Blighted Nightmare's cap) read 5–7
by default and 30 with the Walls.

**F8 — +1/+1 counters keep the T−P gap; endure Spirits have none.** Counters raise both
stats, so a 0/5 with three counters (3/8) still triggers T>P enablers and Doran's X stays 5.
An endure Spirit token is X/X (P = T) — the T>P enablers ignore it, Felothar/Assault
Formation don't need to. Choose COUNTERS on a cheap flip that already has a gap; choose
the TOKEN for width (Betor totals, Myriarch, convoke).

**F9 — Removal follows the owner's rule: nothing that benefits the opponent.** Severance
Priest (opponent gets an X/X when it leaves) fails it. Cheap instant interaction is short in
Abzan; Kin-Tree Severance, Mythos of Nethroi, Abzan Charm are the core.

**F10 — Blight X assumption.** Blighted Nightmare's "Blight X" is read as the Lorwyn
Eclipsed blight cost (put X −1/−1 counters on a creature you control); the pool carries no
reminder text for it. A high-toughness creature pays it painlessly — a 0/6 eats six.
Verify on the card in Arena before relying on it.

**What no tool scores here** (G-67): toughness-as-damage (the floor counts interaction and
card advantage, not damage), flip value, the two loops, and power-capped upside. `cuts` will
read the walls as low-power filler — every wall goes on the protect list.

## 2. Standing error list
- E1: don't grade a 0-power creature as a vanilla wall when ≥5 enablers are in the list (F1).
- E2: don't credit an ETB to a card's manifest/flip value (F4).
- E3: a power cap on recursion or a draw clause is upside, not a restriction (F2).
- E4: Towering Titan / Darksteel Hydra die if flipped — count them as hardcast-only.

## 3. Cross-batch observations
- **Two shells compete for the same slots**: a *protection-and-pump* shell (the ~30
  indestructible / hexproof / +X/+X cards in batches 3–4) and the *engine* shell (enablers,
  walls, landfall, face-down). The pile has roughly twice the protection a 100-card deck
  wants; keep the protection that also does something else (Akroma's Will double strike,
  Shalai hexproof+counters, Earthshape (power-capped, F2), Hakoda's +0/+5, Heroic
  Intervention).
- **Indestructible "others" pieces** (Walls of Ba Sing Se, Avacyn) turn our own wraths
  (The Last Ronin, Deadly Vanity, Punishment) one-sided. Only the Walls is cheap enough to plan on.
- **Variant signal — none yet.** The Hero/Captain America cluster (Wings of Freedom,
  Skybound, Steve Rogers, Luke Cage, Nick Fury) keeps grading low for the same reason (power
  matters, attack-alone); it belongs to the existing Hero decks, not a variant here.
- **Off-pile candidates surfaced** (pool search, not graded in full yet): Trail of Mystery
  (face-down enters → basic to hand; turned face up → +2/+2), Whisperwood Elemental,
  Unyielding Gatekeeper, Hooded Hydra, Pine Walker, Ethrimik, Master of Pearls, Arcades the
  Strategist, Walking Bulwark, Belligerent Brontodon.

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

### Batch 1 (1–41)
| Card | Verdict | Note |
|---|---|---|
| Darksteel Hydra | △ | flips as 0/0 and dies (E4); hardcast X-cost only |
| Eerie Ultimatum | ★ | returns lands too (landfall, F3); WWBBBGG is a hard 7 |
| Crime // Punishment | ★★ | steal a reanimation target, or an X-sweeper that dodges our MVs |
| Kin-Tree Severance | ★★★ | instant exile MV≥3, hybrid-cheap |
| Perennation | ★★ | any permanent back, hexproof+indestructible |
| Call the Crash | ★ | two 4/5 Rhinos (T>P) and 6 drain |
| Nethroi, Apex of Death | ★★★ | total power 10 = five 0-power walls back (F2) |
| Ivorytusk Fortress | ★★ | every endured creature has counters → attacks AND blocks; flip 5 → 7 |
| Betor, Kin to All | ★★★ | F7 — draws every turn from turn ~4, untaps at 20 |
| Drover of the Swine | ✗ | no Boars |
| Betor, Ancestor's Voice | ★ | lifelink counters, MV≤life-lost recursion |
| Yathan Roadwatcher | ★★ | MV≤3 recursion hits Barricade/Kingpin/Walls-tier cheap enablers; cast only |
| Thalia and The Gitrog Monster | ★★★ | extra land (F3), opponents' creatures enter tapped, attack-draw |
| Felothar the Steadfast | ★★★ | global enabler + defenders attack + sac-draw by toughness |
| Revival of the Ancestors | ★ | trample finisher chapter matters for toughness damage |
| Doran, Besieged by Time | ★★★ | enabler-by-gap + discount on every wall |
| Kethis, the Hidden Hand | ◇ | legendary count to be measured at draft |
| Severance Priest | ✗ | F9 — hands the opponent an X/X |
| Felothar, Dawn of the Abzan | ★ | counters on the team, trample |
| Death's Oasis | ◇ | value on death, lesser-MV return |
| Anafenza, the Foremost | ★ | one-sided graveyard hate, counter on tapped creature |
| Abzan Charm | ★★★ | exile power≥3 / draw two / counters |
| Abzan Ascendancy | ★ | counters on team, spirits on death |
| Abzan Monument | ★★ | basic to hand now, X/X (greatest toughness) later — 30/30 with Walls |
| Kin-Tree Invocation | ★★ | 2 mana, X/X = greatest toughness (F7) |
| Nog, Ambitious Cadet | ★ | 3/4 body, extra land drop + lands from graveyard (F3) |
| Mephidross Slime | ✗ | off-plan |
| Lord of Extinction | ◇ | big, unrelated to the axis |
| Ancient Lumberknot | ★★★ | 4-mana T>P enabler on a 1/4 |
| Vraska's Stoneglare | ◇ | 6-mana sorcery removal |
| Garruk, Apex Predator | ★★ | removal + 3/3 deathtouch each turn, 7 mana |
| Zar Ojanen | ✗ | rewards LOW toughness |
| Hauntwoods Shrieker | ★★★ | F5 — {1}{G} flips anything; manifests on attack |
| Threats Around Every Corner | ★★★ | F6 loop |
| Harrowing Swarm | ★★ | F5 — every face-down {2} cheaper + counter |
| Break Down the Door | ★★ | art/ench exile or manifest dread, instant |
| Guardian of the Forgotten | ★ | manifests top card when a modified creature dies (may be unflippable) |
| Shilgengar | ◇ | BB-heavy, few Blood sources |
| Assault Formation | ★★★ | 2-mana global enabler + defender attack + team +0/+1 |
| Beorn's Hospitality | ★★ | landfall counters, rides both loops |
| Druid Class | ★★ | extra land drop (F3), land creature at 3 |

### Batch 2 (42–82)
| Card | Verdict | Note |
|---|---|---|
| Sharp-Eyed Rookie | ★★ | nearly every creature we play has toughness >2 → clue each |
| Arwen, Weaver of Hope | ★★ | face-down manifests ENTER → +1 counter each |
| Dormant Grove | ★★ | transforms on any 6-toughness → team vigilance (attack and block) |
| Bedrock Tortoise | ★★★ | T>P enabler + team hexproof on our turn |
| Flatman | ★★ | 1/10 for 4; flip 4 → endure 10; don't switch him under an enabler |
| Mythweaver Poq | ★★ | doubles a land drop → two Hamza triggers |
| Sultai Flayer | ◇ | 4 life per T≥4 death |
| Tapestry Warden | ★★★ | T>P enabler, vigilance |
| Ashaya, Soul of the Wild | ★★★ | F6 loop; also every creature counts as a land for Poq/Braulios |
| Braulios of Pheres Band | ★★ | attack-draw + land drop |
| Fecund Greenshell | ★★★ | T>P creature enters → land onto battlefield (F3) or a card; +2/+2 at 10 lands |
| Sauron, Dino Devotee | ◇ | 5/5 rebase shrinks our walls' toughness |
| Flourishing Hunter | ◇ | 6-mana 6/6, lifegain |
| Grunn | ✗ | attack-alone, kicker lost on flip |
| Swampbenders | ◇ | off-plan */* |
| Towering Titan | ★ | hardcast only (E4); X = total toughness → enormous |
| Glint Weaver | ◇ | 7 mana |
| Last March of the Ents | ★★ | draw = greatest toughness, then deploy |
| Bark of Doran | ★★ | +0/+1 makes even a face-down 2/2 a T>P attacker |
| Daxos | ◇ | devotion toughness, thin |
| Tenth District Hero | ✗ | off-plan |
| Captain America, Wings of Freedom | ✗ | Hero-only |
| Gauntlets of Light | ◇ | aura enabler, one creature |
| Rasaad, Monk of Selûne | ★ | 3-mana creature exile (until it leaves) |
| Righteous Valkyrie | ◇ | few Angels/Clerics |
| Bill the Pony | ◇ | single-creature enabler per Food |
| Teyo, Aegis Adept | ★★ | perpetual base power = toughness; defenders attack |
| Loxodon Lifechanter | ◇ | life = total toughness; 6 mana |
| Ghalta the Immovable | ★★ | enabler + defender attack; costs ~4 cast, 9 flipped (F4) |
| The Kingpin of Crime | ★★ | 1/5 for 3, extort, attack-time enabler |
| Tymaret | ✗ | BB devotion |
| Blighted Nightmare | ★★ | repeatable reanimation capped by toughness; blight paid by walls (F10) |
| South Wind Avatar | ★ | life = toughness on deaths, drain |
| Iconic Shield | ◇ | |
| Elspeth Resplendent | ★★ | counters + keyword, dig MV≤3 with shield |
| Captain America's Shield | ★★ | +0/+8 = +8 damage under an enabler; taps a blocker |
| Shalai, Voice of Plenty | ★★ | team hexproof + counters sink |
| Choking Miasma | ★★ | −2/−2 sweep our toughness survives |
| Mythos of Nethroi | ★★★ | instant destroy any nonland permanent (GW spent) |
| Polukranos Reborn | ◇ | GGG |
| Chevill | ★ | 1/3 deathtouch, bounty draws |

### Batch 3 (83–123)
| Card | Verdict | Note |
|---|---|---|
| Cursed Wombat | ★★ | +1 on every endure-counters event |
| Insidious Roots | ◇ | plant per recursion |
| Vraska Joins Up | ★ | deathtouch counters on team |
| Stalwart Successor | ★ | +1 counter on first counters |
| Jenova | ✗ | power-scaled (F2) |
| Kagha | ★ | 1/4, lands/permanents from milled cards |
| Professor Dellian Fel | ★★ | removal + draw walker |
| The Last Ronin | ◇ | kills our walls too unless Walls of Ba Sing Se is out |
| Madame Null | ✗ | power-scaled |
| Jadzia Dax | ★ | ramp |
| Ferrafor | ★ | doubles endure counters; 7 mana |
| Crystal Barricade | ★★★ | 2-mana 0/4, flip 2 → 4, you have hexproof |
| The Walls of Ba Sing Se | ★★★ | 0/30, others indestructible; Betor 40 alone; flip via Shrieker = endure 30 |
| Multiply by Zero | ★ | instant 2-mana shrink-to-0/0 |
| Selfless Glyphweaver // Deadly Vanity | ★ | team indestructible or an 8-mana keep-one wipe |
| General's Enforcer | ◇ | Hamza isn't Human |
| Foot Elite | ◇ | |
| Athreos | ✗ | devotion 7 unreachable |
| Fleecemane Lion | ◇ | |
| Arwen, Mortal Queen | ◇ | |
| Karametra | ★★ | each creature cast fetches a land onto the battlefield (F3) |
| Restoration Magic | ★★ | 1-mana protection, scalable |
| Duty Beyond Death | ◇ | |
| Priest of Possibility | ✗ | |
| Selfless Spirit | ◇ | |
| The Needs of the Many | ◇ | |
| Boromir | ◇ | |
| Basri Ket | ★ | counters + soldiers |
| Earthshape | ★★ | protects every creature with power ≤ 3 = the whole wall team (F2) |
| Gideon of the Trials | ✗ | |
| Gideon Blackblade | ◇ | |
| Akroma's Will | ★★★ | double strike doubles toughness damage; both modes with Hamza out |
| Hakoda | ★★ | +0/+5 team = +5 damage each under an enabler |
| Luke Cage | ◇ | attack-alone |
| Oketra the True | ★ | double strike 3/6 enabler target |
| Captain America, Skybound | ◇ | |
| Captain America, Steve Rogers | ◇ | |
| Moogles' Valor | ★ | 1/2 tokens (T>P) + team indestructible |
| Crested Sunmare | ◇ | |
| Nick Fury | ✗ | attack-alone |
| Eagle of Deliverance | ★★ | indestructible counter + near-certain draw (F2) |

### Batch 4 (124–163)
| Card | Verdict | Note |
|---|---|---|
| Angelic Guardian | ★ | attackers indestructible |
| Avacyn, Angel of Hope | ★ | 8 mana; others indestructible |
| The Soul Stone | ◇ | slow |
| Erebos, God of the Dead | ◇ | devotion 5 |
| Smuggler's Surprise | ★ | mill/deploy; hexproof mode is power≥4 (anti, F2) |
| Biosynthic Burst | ★ | |
| Claim the Kingdom | ★ | landfall counters (rides loops) |
| Gaea's Gift | ★ | |
| Heroic Intervention | ★★ | team hexproof + indestructible |
| Origin of Metalbending | ★ | flex art/ench removal or protection |
| Overprotect | ★ | |
| Song of Freyalise | ★ | mana from face-downs for two turns |
| Efflorescence | ◇ | |
| Strength of Will | ★ | a blocking wall grows by damage dealt |
| Inspiring Call | ★★ | every endured creature has counters → draws |
| Sproutwatch Dryad | ◇ | |
| Colossus | ◇ | |
| Toski | ★ | draw per connecting creature |
| Majestic Myriarch | ★ | twice creature count (manifests go wide) |
| Thrun | ◇ | |
| Zopandrel | ★★ | doubles toughness each combat = doubles damage |
| Rok-Tahk | ★★ | every face-down taps for GG → pays flips (F5) |
| Impervious Greatwurm | ★ | convoke off a wide face-down board |
| Tyvar's Stand | ★ | |
| Darksteel Plate | ◇ | |
| Amaranthine Wall | ★★ | colourless 0/6, flip 4 → 6 |
| The Vision | ◇ | |
| Plaza of Heroes | ★ | land; legendary protection |
| Dark Depths | ◇ | |
| Acrobatic Leap | ◇ | |
| Eladamri, Korvecdal | ★★ | cast creatures from top; free creature drop |
| Veteran Beastrider | ★★ | untap team at end step → attack AND block |
| Delney, Streetwise Lookout | ★★★ | power≤2 attackers unblockable by power≥3 (F2) |
| Enduring Innocence | ★★ | each face-down 2/2 entering draws (once a turn) |
| Destined Confrontation | ★★★ | one-sided wrath for a power-0 board (F2) |
| Slumbering Walker | ★★★ | power≤2 recursion each end step, fuelled by endure counters; flips as 4/7 (F4) |
| Smile at Death | ★★★ | two power≤2 creatures back every upkeep (F2) |
| Body Launderer | ★ | returns power ≤3 on death |
| Ruthless Technomancer | ★ | X=1 returns a 0-power wall per artifact; needs artifacts |
| Golden-Tail Trainer | ✗ | power-scaled |

## 5. Consolidated plan (live) — the core for /draft-deck

Counts: 163 graded → ★★★ 23 · ★★ 42 · ★ 40 · ◇ 42 · △ 1 · ✗ 15. A 100 takes ~37 lands + Hamza
(command zone) → **~62 nonland**, so the ★★★ + ★★ pool (65) is almost exactly a deck. The
work is choosing which ★★ to drop for interaction and the loops' needs.

**Tier 1 — the engine (take all ★★★):** Felothar the Steadfast, Doran, Assault Formation,
Ancient Lumberknot, Bedrock Tortoise, Tapestry Warden (enablers) · Crystal Barricade, The
Walls of Ba Sing Se (walls) · Betor, Kin to All (payoff) · Hauntwoods Shrieker, Threats Around
Every Corner, Ashaya (face-down/loops) · Thalia and The Gitrog Monster, Fecund Greenshell
(landfall) · Nethroi, Smile at Death, Slumbering Walker (power-capped recursion) · Delney,
Destined Confrontation (power-cap upside) · Kin-Tree Severance, Mythos of Nethroi, Abzan
Charm (interaction) · Akroma's Will (finisher).

**Tier 2 — strong, choose ~39 of 42:** enabler/defenders (Kingpin, Ghalta, Teyo, Bark of Doran,
Captain America's Shield, Flatman, Amaranthine Wall); landfall (Druid Class, Poq, Braulios,
Karametra, Beorn's Hospitality); face-down (Harrowing Swarm, Break Down the Door, Rok-Tahk,
Arwen Weaver, Enduring Innocence); payoffs (Kin-Tree Invocation, Abzan Monument, Last March,
Ivorytusk, Dormant Grove, Veteran Beastrider, Zopandrel, Sharp-Eyed Rookie, Inspiring Call,
Cursed Wombat, Eagle of Deliverance, Eladamri); recursion (Yathan Roadwatcher, Blighted
Nightmare, Perennation); interaction (Crime // Punishment, Garruk Apex, Dellian Fel,
Choking Miasma); protection (Shalai, Heroic Intervention, Restoration Magic, Earthshape,
Hakoda, Elspeth).

**Protect list (what `cuts` cannot see):** every wall and 0-power creature (Barricade, Walls,
Amaranthine, Felothar, Doran, Bedrock, Flatman) — `cuts` reads them as no-power filler;
Hauntwoods Shrieker (its flip ability is the Walls' cheap route); Threats Around Every
Corner and Ashaya (loop pieces, no counted role); Smile at Death / Slumbering Walker (their
value is the power cap, F2); Delney and Destined Confrontation (same).

**Open decisions for the owner:**
1. How hard to lean on the loops (F6): Threats wants ~12+ basics; Ashaya wants ~35+
   creatures. Both together pull the list toward creature-dense / basics-heavy.
2. Protection budget: the pile offers ~30 protection cards; plan ~6.
3. Interaction is the thin axis — Abzan in this pile has ~9 real removal pieces; all of
   them likely make the cut, and off-pile removal may be worth a look at draft.
