# Zimone pile — analysis (TEMPORARY working doc)

**Status: DRAFTED as deck 94 (Paradox Sculptor) 2026-10-27; owner is choosing add-backs and the fits sweep below.** Delete once the deck is drafted and the findings are folded into
the deck file's `#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Source list:** the owner's 141-card pile, pasted 2026-10-27, aimed at a NEW **Historic
Brawl** deck (100 cards, singleton), commander **Zimone, Paradox Sculptor** ({2}{G}{U}, 1/4).
Owner's themes: exponential counters, Merfolk, Elves, "other synergies that surface". 140
distinct nonland cards, no lands; every card resolves, is Historic-Brawl legal and inside
G/U identity. Cards already in other decks stay ELIGIBLE (copies are shared). Scratch copy:
`zimone/pile.txt` in the session scratchpad.

Zimone: "At the beginning of combat on your turn, put a +1/+1 counter on each of up to two
target creatures you control. {G}{U}, {T}: Double the number of each kind of counter on up to
two target creatures and/or artifacts you control."

## 1. The decision framework

- **R1 — The currency is COUNTERS on creatures and artifacts.** Zimone adds two +1/+1
  counters every combat and, once she can tap, doubles EVERY kind of counter on two targets
  each turn. Grade a card by how many counters it puts out (X-cost Hydras and Fractals,
  "enters with N counters", counter-placing triggers) and by whether it PAYS for a big pile
  (power-matters, "for each counter", trample/evasion to cash it in).
- **R2 — "Each kind" includes non-+1/+1 counters, but only on creatures and artifacts.**
  Charge/oil/other counters on artifacts double; loyalty on planeswalkers and lore on Sagas
  do NOT (not a creature or artifact). Planeswalkers gain only from proliferate.
- **R3 — Doublers stack multiplicatively.** A "twice that many counters" replacement
  (Branching Evolution and kin) doubles every counter PLACED; Zimone doubles what is already
  there. Grade replacement doublers as engine pieces, not filler.
- **R4 — Zimone needs a turn and a tap.** The doubling is a {T} ability, so she cannot use it
  the turn she enters, and she is a 1/4 — protect her (Brawl tax {2} per recast). The combat
  counters arrive at the beginning of combat even if she does not attack.
- **R5 — Tribes are judged by PAYOFF count, not body count (G-59).** Merfolk (Lord of
  Atlantis, Svyelun, Kumena, Tishana, Deeproot…) and Elves (Imperious Perfect, Dionus,
  Eladamri, Thranduil…) are both present; count the payoffs per tribe at the end. Zimone
  is a Human Wizard — neither tribe.
- **R6 — Brawl floor is scaled ×1.67.** A needs interaction 12 and interaction + card
  advantage 19. Simic interaction is thin: counterspells, fight/bite, and -X effects count;
  single-target BOUNCE is report-only tempo since 2026-10-07 (G-25), not interaction. Count
  real interaction carefully.
- **R7 — Two colours: mana is easy, but X-cost cards want MANA.** Ramp and mana creatures
  (Elves) have real value here because the counter cards scale with X.

## 2. Standing error list

- **E1 — A token COPY of an X-counter creature enters with no counters.** Hydras and Fractals
  are 0/0 bodies that ENTER with X counters; Echocasting Symposium, Irma, Undercover Operative
  and other copy effects copy the card, not the counters, so a copied Hydra dies on entry.
  Copy the creature that carries static value, never the X-body.
- **E2 — Doubling a BAD counter is bad.** Zimone doubles every kind of counter, so stun
  counters (The Watcher in the Water) and -1/-1 counters on your own creatures double too.

## 3. Cross-batch observations

- **O1 — Xolatoyac untaps every permanent with a counter at YOUR end step.** Give Zimone one
  of her own combat counters and she doubles twice per turn cycle (main phase, then again
  after the end-step untap, on the opponent's turn). Jace, Ingenious Mind-Mage's +1 (untap
  all creatures) does the same. Untap effects are an engine axis here.
- **O2 — A blue DRAW → COUNTERS sub-theme:** Pensive Professor (counters → draw), Baxter and
  Stark's Ingenuity (draw → counters), Tui and La, Krang (draw triggers twice), Teferi.
- **O3 — A PROLIFERATE sub-theme:** Inexorable Tide (proliferate per spell), Tekuthal
  (proliferate twice), Ichormoon Gauntlet (walkers proliferate; extra counter per
  noncreature spell). Proliferate is the only thing that grows planeswalker loyalty (R2).
- **O4 — Counter REPLACEMENT doublers are deep in green.** Branching Evolution, The Earth
  Crystal, Shang-Chi, Innkeeper's Talent (level 3, ALL counter kinds), plus Michelangelo
  (+1 per placement) and Bristly Bill / Seismic Tutelage (double existing). Order matters:
  apply +1 replacements before doublers when you choose the order (you do, as the
  affected creature's controller). Five-plus doublers is a real engine, not filler.
- **O5 — Applied Geometry copies a NONCREATURE permanent as a 6-counter Fractal.** Copy a
  doubler (Branching Evolution, The Earth Crystal, Innkeeper's Talent) and you have a second
  doubler that is also a creature Zimone can target. Highest-ceiling card in the pile.
- **O6 — Simic Ascendancy is an alternate win.** Growth counters equal to every +1/+1 counter
  placed on your creatures; with two doublers, twenty arrives in a few turns. Note Zimone does
  NOT double the growth counters (it is an enchantment, R2) — the doublers do the work.
- **O7 — Card draw from counters is plentiful:** Prime Speaker Zegana, Take (Give // Take),
  Pensive Professor, Hydroid Krasis, Sab-Sunen (draw 2 on odd, Zimone's doubling makes it
  even again so it can attack).
- **O8 — Merfolk is dense enough to be its own deck (variant signal, decide at the end).**
  Batch 4 alone has ~20 Merfolk cards, many of them small tribal payoffs (Lord of Atlantis,
  Vodalian Hexcatcher, Deeproot Pilgrimage/Waters, Daughter of the Deep, Tunnel-Guide) that
  do little for COUNTERS. The counter-relevant Merfolk are the bridge: Deeproot Elite, Combine
  Guildmage, Merfolk Skydiver, Mindspring Merfolk, Svyelun, Namor, Scourge.
- **O9 — Copying a SPELL keeps X (unlike E1).** Double Major copies a creature spell on the
  stack, so a copied Hydra or Krasis keeps its X — the reverse of a token copy of a permanent.
- **O10 — Elves are thin on PAYOFFS (G-59).** Elf bodies are plentiful but the tribal payoffs
  are Imperious Perfect, Thranduil, Dionus and Thranduil's Company (needs another Elf). The
  Elves that matter here are MANA (Selvala, Topiary Lecturer) and counter cards that happen
  to be Elves (Arwen, Fractal Tender, Elrond, Ezuri ×2, Evolution Sage) — play them for their
  text, not their type.
- **O11 — Interaction lives OUTSIDE the pile.** In-pile answers: Sublime Epiphany, Repulsive
  Mutation, Inscription of Abundance, Commit // Memory, Voracious Hydra, Chandra's −X. Owned
  Simic answers that scale with big creatures: Felling Blow, Bite Down, Rabid Bite, Hunter's
  Talent; counterspells Essence Capture (+1 counter), Quandrix Charm, Three Steps Ahead, Mana
  Sculpt (Zimone is a Wizard — the mana refund turns on); Season of Gathering, Pawpatch
  Formation, Glen Elendra's Answer, Vivien Reid.

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

### Batch 1 (28, blue)

| Card | Verdict | Note |
|---|---|---|
| Xolatoyac, the Smiling Flood | ★★★ | end-step untap of everything with a counter = Zimone doubles twice a cycle (O1) |
| Eluge, the Shoreless Sea | △ | UUU; Island-count body; flood counters sit on LANDS (R2) |
| Ichormoon Gauntlet | ★ | +1 counter per noncreature spell; walkers proliferate (O3) |
| Irma, Part-Time Mutant | ◇ | copies a creature each combat + a counter (E1: never a Hydra) |
| Namor the Sub-Mariner | ◇ | Merfolk payoff; tokens off blue noncreature spells |
| Pensive Professor | ★★ | every counter placement draws; Zimone feeds it each combat (O2) |
| Stark's Ingenuity | ★ | draw X, then a counter per draw |
| Commit // Memory | ★ | instant answer to a spell or permanent (interaction) |
| Baxter, Fly in the Ointment | ★ | grows on draws; team with counters flies on enter/attack |
| Orvar, the All-Form | △ | needs targeted instants/sorceries on your own permanents |
| Tekuthal, Inquiry Dominus | ★ | proliferate twice; 3/5 flier |
| Tui and La, Moon and Ocean | ★ | draw when tapped, counter when untapped — pairs with O1 untaps |
| Undercover Operative | ★ | clone; its shield counter doubles under Zimone |
| Vesuvan Duplimancy | △ | needs single-target spells on your own creatures |
| Vulture, Feathered Fiend | ◇ | flying-damage draw |
| Yue, the Moon Spirit | ◇ | free noncreature spell from hand |
| Bribery | ◇ | steal their best creature; off-theme |
| Inexorable Tide | ★★ | proliferate on every spell (O3) |
| Krang, the All-Powerful | ◇ | doubles draw triggers (O2) |
| Mesmerizing Benthid | ◇ | defensive hexproof body |
| Namor, Scourge of the Seas | ★ | connive each combat; Merfolk with counters fly |
| Teferi, Temporal Pilgrim | ◇ | loyalty per draw; walkers get nothing from Zimone (R2) |
| Thryx, the Sudden Storm | ◇ | flash flier; MV 5+ discount |
| The Watcher in the Water | ✗ | stun counters (E2) |
| Echocasting Symposium | ◇ | free copy every main phase; copy a static creature, not a Hydra (E1) |
| Jace, Ingenious Mind-Mage | ★ | +1 untaps all creatures — a second Zimone activation (O1) |
| Sublime Epiphany | ★★ | modal counter / bounce / copy / draw — real interaction |
| One with the Multiverse | ◇ | 8 mana |

### Batch 2 (28, green + blue)

| Card | Verdict | Note |
|---|---|---|
| Mockingbird | ◇ | X clone with flying |
| Ambitious Augmenter | ★ | 1-drop increment; dies into a Fractal carrying its counters |
| Burgeoning | ◇ | ramp in 1v1, one extra land per opposing land |
| Smuggler's Surprise | ★ | modal: dig, cheat two creatures, or hexproof+indestructible for power 4+ |
| Bristly Bill, Spine Sower | ★★★ | landfall counters; {3}{G}{G} doubles every creature's +1/+1 counters |
| Fractal Anomaly | ◇ | instant Fractal = cards drawn this turn |
| As Foretold | ◇ | free spells as time counters build |
| Chandra, Chill of Compliance | ◇ | −X stun is real interaction; walker gets nothing from Zimone |
| Imperial Cosmographer | △ | needs blink/bounce of your own creatures |
| Jadzi // Oracle's Gift | ★ | loot 2 on entry; prepared copy makes X Fractals with X counters EACH |
| Herald of Secret Streams | ★★ | every creature with a +1/+1 counter is unblockable — the finisher |
| Serpentine Curve | △ | few instants/sorceries to scale it |
| The Theorist, Jace Beleren | ★ | draw on their draw step; −2 bounces (tempo) |
| Innkeeper's Talent | ★★★ | combat counter; ward 1 on countered permanents; L3 doubles ALL counter kinds |
| Inscription of Abundance | ★★ | instant fight + counters (interaction) |
| Michelangelo, Weirdness to 11 | ★★ | +1 on every counter placement (O4) |
| Arwen, Weaver of Hope | ★ | Elf; others enter with counters = her toughness, which grows |
| Branching Evolution | ★★★ | doubler (O4) |
| Seismic Tutelage | ★ | doubles counters on each attack |
| The Earth Crystal | ★★★ | doubler + green discount |
| Germination Practicum | ★★ | +2 to the team, and free again every first main phase (paradigm) |
| Herd Baloth | ★★ | a 4/4 every time counters land on it — Zimone's combat counter included |
| Nissa, Who Shakes the World | ★ | Forest mana doubling; animated lands carry counters |
| Railway Brawler | ★★ | others enter with counters = their power |
| Shang-Chi, Martial Mentor | ★★ | doubler on a 4/4 body |
| Ancient Bronze Dragon | ◇ | 7-mana flier, random d20 counters |
| Feral Hydra | ◇ | plain X Hydra |
| Goldvein Hydra | ★ | X Hydra with haste and trample; Treasures on death |

### Batch 3 (28, green-blue)

| Card | Verdict | Note |
|---|---|---|
| Ivy Elemental | ◇ | plain X body |
| Mistcutter Hydra | ★ | uncounterable, haste, protection from blue |
| Hungering Hydra | ★ | grows from damage; one blocker max |
| Voracious Hydra | ★★ | X body that fights (interaction) or doubles itself |
| Biomancer's Familiar | ◇ | cuts generic costs only — Zimone's {G}{U} gets nothing; Bristly Bill, Ant-Man do |
| Growth Curve | ★ | 2 mana: +1 then double |
| Simic Ascendancy | ★★ | alternate win (O6) |
| Sita Varma, Masked Racer | ◇ | one-shot X counters + team base P/T |
| The Astonishing Ant-Man | ★ | grows on draws; cashes counters into Insects |
| Give // Take | ★ | Take draws a card per counter removed — card advantage after a doubling |
| Hadana's Climb | ★★ | combat counter; flips into a land that doubles a creature's power and gives flying |
| Zimone, Infinite Analyst | ★ | X-spell discount per counter on her; grows on the first X spell |
| Applied Geometry | ★★★ | copy a doubler as a 6-counter Fractal (O5) |
| Arixmethes, Slumbering Isle | ★ | ramp land that wakes into a 12/12 |
| Berta, Wise Extrapolator | ★★ | mana on every counter placement; X Fractal maker |
| Ezuri, Claw of Progress | ★ | Elf; experience-scaled combat counters |
| Manifestation Sage | ◇ | Fractal = hand size |
| Thranduil's Company | ★ | Elf; extra land with another Elf; landfall +2 counters |
| Fractal Tender | ★★ | ward 2; a 3-counter Fractal every end step it grew |
| Roalesk, Apex Hybrid | ★ | flier; +2 on entry; proliferate twice on death |
| Sab-Sunen, Luxa Embodied | ★ | indestructible 6/6; draws 2 on odd counts, Zimone evens it (O7) |
| Tanazir Quandrix | ★★ | doubles counters on entry; team base P/T on attack |
| Body of Research | ◇ | GGGUUU spice: a Fractal the size of your library |
| Prime Speaker Zegana | ★★ | draws cards equal to its power (O7) |
| Oko, the Trickster | ★ | +2 counters per turn; −7 makes the team 10/10 |
| Hydroid Krasis | ★★ | X flier that draws and gains on cast |
| Repulsive Mutation | ★★ | instant counters + soft counterspell (interaction) |
| Nissa, Steward of Elements | ◇ | X walker; free lands/creatures off the top |

### Batch 4 (28, mostly Merfolk)

| Card | Verdict | Note |
|---|---|---|
| Primo, the Unbounded | ★★ | twice-X counters, trample; base-0 Fractals that connect make more Fractals |
| Wolverine, Claws Out | △ | Mutant power doubling; few Mutants |
| God-Eternal Rhonas | ★ | doubles the team's power for a turn — a finisher |
| Majestic Myriarch | ◇ | creature-count body |
| The Skullspore Nexus | ◇ | death-to-token; power doubler |
| Double Major | ★★ | copies a creature SPELL, X kept (O9) |
| Exponential Growth | ★ | one-shot finisher |
| Additive Evolution | ★ | 3-counter Fractal + a combat counter every turn |
| Preponderant Pearl | △ | Merfolk cantrip |
| Mindspring Merfolk | ★ | draw X + a counter on each Merfolk, once |
| Deeproot Pilgrimage | ◇ | Merfolk tokens when Merfolk tap |
| Daughter of the Deep | ◇ | Merfolk token on second draw; unblockable Merfolk |
| Lord of Atlantis | ◇ | Merfolk lord |
| Skyclave Aerialist | ◇ | 2-drop flier |
| Thassa's Oracle | ◇ | devotion dig |
| Vodalian Hexcatcher | ◇ | Merfolk lord; sac-a-Merfolk soft counterspell |
| Atlantean Cavalry | △ | second-draw counter |
| Deeproot Waters | ◇ | Merfolk spell → hexproof token |
| Svyelun of Sea and Sky | ★ | Merfolk ward; draws on attack |
| Umara Wizard // Umara Skyfalls | △ | MDFC land |
| Deeproot Elite | ★ | Merfolk enter → a counter |
| World Shaper | ◇ | lands back on death |
| Combine Guildmage | ★ | team enters with +1; moves counters |
| Merfolk Skydiver | ★ | flier; +1 counter; proliferate sink |
| Merfolk Tunnel-Guide | ◇ | explore boon |
| Nicanzil, Current Conductor | ◇ | explore payoff |
| Thrasios, Triton Hero | ★ | mana sink: land or card |
| Kiora of Salt and Sand | ◇ | walker support |

### Batch 5 (28, Merfolk + Elves)

| Card | Verdict | Note |
|---|---|---|
| Quandrix Pledgemage | △ | magecraft counters |
| Kumena, Tyrant of Orazca | ◇ | Merfolk tap engine |
| Adrix and Nev, Twincasters | ★★ | token doubler — every Fractal maker makes two |
| Vodalian Tide Mage | ◇ | conjures duplicates on damage |
| Zegana, Utopian Speaker | ★★ | draw on entry; every countered creature has trample |
| Tatyova, Benthic Druid | ★ | landfall draw |
| Kiora, Sovereign of the Deep | ◇ | sea-monster cascade |
| Tishana, Voice of Thunder | ★ | 7 mana: draw per creature |
| Kiora, the Tide's Fury | ◇ | untap / prevent; walker |
| Nadir Kraken | ★ | every draw buys a counter and a Tentacle |
| Reef Worm | △ | |
| Verdant Kraken | ◇ | 7 mana; land creatures every upkeep |
| Kiora, the Crashing Wave | ◇ | |
| Pelt Collector | ◇ | 1-drop grower |
| Virulent Emissary | △ | |
| Aftermath Analyst | ◇ | |
| Eladamri, Korvecdal | ★ | cast creatures off the top |
| Elvish Hydromancer | ◇ | kicked copy (E1) |
| Evolution Sage | ★★ | landfall proliferate |
| Imperious Perfect | ◇ | Elf lord (O10) |
| Nissa, Vastwood Seer | ◇ | fetches a Forest; flips late |
| Selvala, Heart of the Wilds | ★★ | {G},{T}: mana equal to your greatest power — explosive here |
| Topiary Lecturer | ★★ | taps for {G} equal to its power; increment grows it |
| Dionus, Elvish Archdruid | ◇ | Elf untap + counters |
| Elrond, Master of Healing | ★ | scry → counters; draws when countered creatures are targeted |
| Ezuri, Stalker of Spheres | ★ | proliferate twice on entry; draw per proliferate |
| Legolas, Counter of Kills | ◇ | |
| Thranduil, Sindarin Liege | ◇ | Elf lord + landfall Elves |

## 5. Consolidated plan (live)

**Recommended plan: COUNTER ENGINE.** Zimone + replacement doublers + X-bodies, cashed in
through unblockability (Herald), trample (Zegana), an alternate win (Simic Ascendancy) and
mana that scales with power (Selvala, Topiary Lecturer). Merfolk and Elves are played for
their TEXT; the tribal shells are benched (O8, O10). Draft target: 36 lands + 63 nonland +
Zimone. P = from the pile, O = owned outside it.

- Engine (9): Branching Evolution, The Earth Crystal, Innkeeper's Talent, Shang-Chi,
  Michelangelo, Bristly Bill, Applied Geometry, Xolatoyac, Tanazir Quandrix (all P)
- Payoffs (7): Inexorable Tide, Evolution Sage, Simic Ascendancy, Herald of Secret Streams,
  Zegana Utopian Speaker, Herd Baloth, Primo (P)
- X bodies (7): Hydroid Krasis, Voracious Hydra, Goldvein Hydra, Mistcutter Hydra, Hungering
  Hydra, Double Major, Zimone Infinite Analyst (P)
- Counter makers (8): Fractal Tender, Jadzi, Berta, Additive Evolution, Hadana's Climb,
  Railway Brawler, Arwen, Germination Practicum (P)
- Cheap counter support (4): Growth Curve, Merfolk Skydiver, Ambitious Augmenter, Combine
  Guildmage (P)
- Card advantage (8): Pensive Professor, Prime Speaker Zegana, Sab-Sunen, Give // Take, The
  Astonishing Ant-Man, Ezuri Stalker of Spheres, Tatyova, Thrasios (P)
- Ramp (4): Topiary Lecturer, Selvala, Arixmethes, Thranduil's Company (P)
- Untap / protection (3): Jace Ingenious Mind-Mage, Smuggler's Surprise, Oko the Trickster (P)
- Interaction (13): Sublime Epiphany, Repulsive Mutation, Inscription of Abundance, Commit //
  Memory (P); Felling Blow, Bite Down, Hunter's Talent, Essence Capture, Quandrix Charm, Three
  Steps Ahead, Mana Sculpt, Season of Gathering, Pawpatch Formation (O)

**Protect:** Zimone, Branching Evolution, The Earth Crystal, Innkeeper's Talent, Applied
Geometry, Xolatoyac, Simic Ascendancy, Herald of Secret Streams — their value is in the rest
of the deck.

**Variant signal:** a MERFOLK Brawl deck (O8) — Lord of Atlantis, Vodalian Hexcatcher,
Svyelun, both Namors, Kumena, Deeproot Elite/Pilgrimage/Waters, Daughter of the Deep,
Mindspring Merfolk, Tunnel-Guide, Nicanzil, Tishana, Kiora of Salt and Sand. Not built here.

**Bench (pile, not in the core):** the Merfolk shell above; Elf lords (O10); clone/copy cards
(Irma, Undercover Operative, Mockingbird, Echocasting Symposium, Elvish Hydromancer — E1);
Watcher in the Water (E2); spells-matter (Eluge, Orvar, Vesuvan Duplimancy, Serpentine Curve,
Quandrix Pledgemage, Umara Wizard); 7–8 drops (One with the Multiverse, Verdant Kraken,
Ancient Bronze Dragon, Body of Research, Tishana); walkers Zimone cannot grow (Teferi,
Chandra, Kiora ×3, Nissa ×2, The Theorist); draw-trigger extras (Krang, Baxter, Stark's
Ingenuity, Tui and La, Nadir Kraken, Atlantean Cavalry, Vulture); and the remaining
situational cards. Next in line: Adrix and Nev, Tekuthal, Elrond, Eladamri, Seismic
Tutelage, Ichormoon Gauntlet, Baxter, Nadir Kraken, Tishana, God-Eternal Rhonas, Exponential
Growth.

## 6. Fits / upgrades / spice sweep for deck 94 (2026-10-27; full text read)

Regex sweeps over the Simic Historic-Brawl pool for doublers, proliferate, counter payoffs,
untap effects and team protection.
- **Owned upgrades:** Swiftfoot Boots (haste lets Zimone tap the turn she lands; hexproof),
  Doubling Season (tokens AND counters), Loading Zone (all counter kinds on creatures; warp {G}),
  Doc Samson (+1 of every counter kind; taps for mana = power), Inspiring Call (instant draw per
  countered creature + indestructible), Sazh Katzroy (attack: +1 then double), Mossborn Hydra
  (landfall doubles), Tezzeret, Cruel Captain (0: untap a creature — a second Zimone activation).
- **Craft upgrades:** Vorinclex (doubles ALL counters, loyalty included), Unstoppable Plan
  (end-step untap of all nonland permanents — Zimone twice a turn cycle, like Xolatoyac),
  Hardened Scales, Katara's Reversal (counter four things + untap four), Heroic Intervention,
  Simic Charm.
- **Fits:** Thunderous Velocipede, Biogenic Upgrade, Marketback Walker (an artifact — Zimone
  doubles it; draws a card per counter on death), Armorcraft Judge, Bred for the Hunt, Benthic
  Biomancer, Dramatic Reversal, the +1 replacements (Ozolith, Kami of Whispered Hopes, Solid
  Ground).
- **Spice:** Cytoplast Manipulator (steal a creature with a counter), Contagion Engine,
  Paradox Engine, Intruder Alarm.
