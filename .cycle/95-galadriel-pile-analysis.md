# Deck 95 Light of Valinor pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into deck
95's `#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Source list:** owner's pile part 1 (85 names) + the earlier consideration list (16),
resolved to 100 cards after removing three deck 95 already runs (Denzilore Fatehold,
Thassa, Deep-Dwelling, Soulherder). Part 2 of the pile is still to come. "Arwen" expanded
to the four Arwen cards; "Ob Nixilis" read as Ob Nixilis, the Ascended (the white one);
"Tocasia" as Tocasia, Dig Site Mentor. Daxos of Meletis is not on Arena (not in the pool).

## 1. The decision framework

Live vector (2026-10-30, after the lifegain package): floor B; interaction 9 (A needs 12
at 100 cards); card advantage 6 (+3 unread); protection 6; board power 145; avg MV 3.75;
shape WIDE; Humans 14, Angels 4; sources W 21 / U 21 / G 20; tempo-sim on-curve 51.3%.
Engines: lifegain 16 enablers / 10 payoffs; counters 9 enablers, NO payoff flagged;
tokens 7 / 7.

1. **The deck pays a creature's printed cost once and its enters trigger many times.**
   ~15 blink effects (Y'shtola, Thassa, Don & Leo, Teleportation Circle, Silver Surfer,
   Yorion, Soulherder, Abuelo, Oji, Restoration Angel, Salvation Swan, Lilysplash Mentor,
   Ephemerate, Morningtide's Light, Another Round) plus Elesh Norn and Panharmonicon.
   Value ON ENTERING is multiplied; value on attacking, on dying or from a static ability
   is not. Grade enters triggers up, attack triggers down.
2. **Every creature entering is also a Galadriel trigger** (three modes a turn: {G}{G}{G},
   a counter on each creature, scry 2 and draw) and a lifegain event for Soul Warden,
   Ajani's Welcome, Distinguished Conjurer. Tokens count. More bodies entering = more of
   everything.
3. **Lifegain payoffs scale per EVENT, not per point**, and "first time each turn" caps
   (Vanguard Seraph, Bloombrute) do not. A payoff that reads "whenever you gain life" is
   worth a trigger per creature entering.
4. **Y'shtola's extra end step doubles "at the beginning of (your / each) end step"**
   (Crested Sunmare, Lathiel, Aerith, Enlightened Confidant, Thassa, Don & Leo,
   Teleportation Circle, Palantír). End-step payoffs grade up.
5. **Blink RESETS a permanent**: counters, X values (a blinked X creature returns with
   X = 0), "until this leaves" exiles (the exiled card comes back — the G-42 shape for
   O-ring creatures), transformed DFCs (return front face). Grade those down.
6. **Mana**: W 21 / U 21 / G 20, 37 lands. {W}{W} on turn 2–3 casts ~55–63% on curve.
   The deck is already heavy (avg MV 3.75, 11 early drops); the deck 85 slow-start lesson
   says favour ≤3 MV unless the card is a top-end engine.
7. **Gaps worth filling**: interaction (9, no sweeper, few instants); a counters PAYOFF
   (Galadriel, Archangel of Thune and Heliod make counters and nothing spends them);
   cheap early plays.
8. **Format**: Historic Brawl, singleton, commander identity GWU. Not-brawl-legal = out.
9. **Structurally invisible to the tools**: enters-trigger multiplication (every model
   counts a trigger once), lifegain event counts, end-step doubling, Galadriel's mode
   choice. Grade those by hand from text.

## 2. Standing error list

- **Role classifier holes (G-67), recorded, not fixed**: The Legend of Yangchen's chapter I
  ("each player chooses… Exile those permanents") and Aang, Swift Savior's airbend of a
  creature or spell score as no interaction, so the package preview under-reads
  interaction by about 2. Grade them by hand.

## 3. Cross-batch observations

- **An ANGEL sub-theme is forming** in the pile: The Book of Exalted Deeds and Speaker of
  the Heavens make Angel tokens off lifegain; Resplendent Angel, Lyra (Archangel of Dawn),
  Serra Paragon, Boon-Bringer Valkyrie are Angels. The deck already runs 4 Angels
  (Restoration Angel, Archangel of Thune, Holy Cow, Lyra-less). Watch the count — an Angel
  payoff is only as good as the Angels it can reach (G-59).
- **"Exile until this leaves" cards** (Prison Realm, Detention Sphere) are fine removal,
  but a blink of them by Silver Surfer or Yorion RETURNS the exiled card before the new
  copy re-exiles (Rule 5). Teleportation Circle cannot target them (creature/artifact only).
- **Protection cluster**: Shalai and Sigarda (hexproof for everything else), Sephara,
  Avacyn — the deck's protection is 6; one hexproof lord is probably enough.
- **Counters payoffs arrive** (R7 gap): Metropolis Angel (draw), Elrond, Master of Healing,
  Metastatic Evangel (proliferate). Metastatic + Flux Channeler are multipliers, not payoffs.
- **A CLERIC sub-theme is mostly incidental**: many pile cards are Clerics (Minwu, Righteous
  Valkyrie, Cleric Class) but the deck runs ~4 Clerics; treat Cleric payoffs as filler unless
  several land together (G-59).
- **Counter multipliers** (Conclave Mentor, Metastatic Evangel, Cleric Class level 2) pair
  with the counters engine; a payoff (Metropolis Angel, Elrond) is still the missing half.
- **VARIANT SIGNAL (part 2): a PROLIFERATE cluster** — Huatli's Raptor, Bloom Hulk, Gitaxian
  Anatomist, Tainted Observer, Contagion Dispenser, Ezuri, Tekuthal, Inexorable Tide,
  Quintorius (Fate Splitter), Roalesk. Coherent, but a fourth theme on top of blink, scry and
  lifegain would thin all three. Left out of the package; a counters/proliferate deck is a
  candidate for its own build.
- **Tocasia, Dig Site Mentor turns every creature into a surveil engine** — the single
  biggest scry-sub-theme card in the pile; Denzilore, Matoya, Planetarium and Elrond,
  Master of Healing all pay per surveil.

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

### Batch 1 (cards 1–25)

| # | Card | Own | Verdict | Note (rule) |
|---|---|---|---|---|
| 1 | Ajani, Strength of the Pride | — | ★★ | +1 gains life = creatures + planeswalkers (wide deck, one big gain); −2 Pridemate; 0 at 40 life exiles ALL their creatures and artifacts — pairs with Felidar Sovereign's 40. |
| 2 | The Wandering Emperor | — | ★★★ | Flash; −2 exiles a tapped creature and gains 2; −1 makes a 2/2 that enters (R2). Instant-speed interaction the deck lacks (R7). |
| 3 | Syr Vondam, Sunstar Exemplar | — | ✗ | {W}{B} — off colour. |
| 4 | The Book of Exalted Deeds* | — | ★★ | End step: gained 3+ life → 3/3 Angel; Y'shtola makes it two (R4); tokens enter (R2). {W}{W}{W} is the cost (R6). |
| 5 | Ojutai Exemplars | — | △ | Only blinks ITSELF on a noncreature spell; no enters trigger of its own. |
| 6 | Serra Paragon* | — | ★★ | Once a turn cast a ≤3 MV permanent (or a land) from the graveyard — re-buys Soul Warden, Reflector Mage, Skyclave Apparition; each re-cast enters (R1/R2). Flying Angel. |
| 7 | Prison Realm | — | ★★ | 3-mana creature/planeswalker exile + scry 1 (R7). Caution R5 with Surfer/Yorion. |
| 8 | Lost Isle Calling | — | ★ | Verse counter per scry; 7+ = draw 7 and an extra turn. Scry events are frequent here; spice. |
| 9 | Elrond, Master of Healing | — | ★★ | Every scry puts counters on X creatures (X = cards looked at) — Galadriel's scry 2 = two counters a turn; draws when they're targeted. A counters payoff (R7). |
| 10 | Nissa, Steward of Elements | — | ★★ | +2 scry 2 every turn; 0 puts a land or a creature (MV ≤ loyalty) onto the battlefield — a free enters (R1). |
| 11 | Legolas, Counter of Kills | — | △ | Untap on scry; counters when their creatures die. Little for this deck. |
| 12 | Flickering Hound | — | ★★★ | "Whenever you cast a creature spell, exile up to one other target creature… return it." ~45 creatures: a blink every creature cast (R1). |
| 13 | Photon, Lady of Light | — | ★ | Blink only on ATTACK (R1 grades attack triggers down). |
| 14 | The Legend of Yangchen | own | ★★★ | I: each player picks one of THEIR permanents MV ≥3 to exile — in 1v1 that's two of the opponent's; II: both draw 3; III flips to a flier that airbends on your second spell. Owned interaction + cards; Yorion/Surfer restart the Saga. |
| 15 | Jill, Shiva's Dominant | — | ★ | Enters: return any nonland permanent to hand — tempo, or re-buy your own enters trigger. |
| 16 | Oracle of the Alpha | — | ★★ | Enters: conjure the Power Nine into your library. Every blink adds another nine (Ancestral Recall, Time Walk, Black Lotus, Moxen). Spice with real power. |
| 17 | Wakandan Tusker | — | ◇ | Gain 1 + scry 1 whenever it taps; needs a tap outlet (Tocasia gives one). |
| 18 | Flux Channeler | — | ◇ | Proliferate on noncreature spells — counters, loyalty, verse. A multiplier, not a payoff. |
| 19 | Meandering Towershell | — | ✗ | Attack-exile, no enters value (R1). |
| 20 | Stenn, Paranoid Partisan | — | ★★ | {W}{U} 2-drop; "{1}{W}{U}: Exile Stenn. Return it at the next end step" — a guaranteed creature entering every turn (R2: Galadriel + lifegain triggers) plus a cost reducer. |
| 21 | Detention Sphere | — | ★★ | Exiles any nonland permanent (and all same-named). R5 caution. |
| 22 | Ojutai's Command | — | ★★ | Instant: two of reanimate ≤2 MV / gain 4 / counter a creature spell / draw. Instant interaction (R7). |
| 23 | Tocasia, Dig Site Mentor | — | ★★★ | Creatures have vigilance and "{T}: Surveil 1" — every creature is a surveil engine for Denzilore, Matoya, Planetarium (R9). |
| 24 | Chulane, Teller of Tales | — | ★★★ | Every creature CAST draws a card and puts a land; "{3}, {T}: Return target creature you control to its owner's hand" re-buys an enters trigger. |
| 25 | Speaker of the Heavens | — | ★★ | 1-drop lifelink; at 32+ life taps for a 4/4 Angel each turn (R2). Early play (R6). |

### Batch 2 (cards 26–50)

| # | Card | Own | Verdict | Note (rule) |
|---|---|---|---|---|
| 26 | Metastatic Evangel | — | ★★ | {1}{W}: every nontoken creature entering proliferates — Galadriel/Archangel/Heliod counters, planeswalker loyalty, verse counters. Blink feeds it each time (R1, R7). |
| 27 | Angelheart Protector | — | ◇ | Enters: one creature indestructible this turn — a blink in response is a save. |
| 28 | Metropolis Reformer | — | ★ | 3-mana Angel flier; "You have hexproof"; damage dealt to it gains life. |
| 29 | Righteous Valkyrie | — | ★★ | Angel or Cleric entering gains life = its toughness (blink repeats it); at 32+ life every creature gets +2/+2. |
| 30 | Valgavoth, the Lifeline | — | ★★ | 3-mana Angel; each gain grows creature cards in hand and yard perpetually; having gained life lets you CAST creatures from the graveyard — recursion every turn the lifegain engine runs. |
| 31 | Archangel of Tithes | own | ★ | {1}{W}{W}{W}; attackers cost {1} each — a defensive tax. Owned. |
| 32 | Champions of Tyr | — | ◇ | Boon: next creature cast enters with a keyword counter. Small. |
| 33 | Serra the Benevolent | — | ◇ | −3: a 4/4 Angel; +2 pumps fliers. |
| 34 | Shalai, Voice of Plenty | — | ★★ | You, your planeswalkers and other creatures have hexproof (protection, R7); {4}{G}{G}: a counter on each creature. |
| 35 | Angel of Destiny | — | ◇ | Alt-win at 40 needs combat damage and symmetric gains. Felidar does it without combat. |
| 36 | Angel of Sanctions | — | ★★ | Enters: exile a nonland permanent until it leaves — a blink re-targets (R5 is harmless here); embalm gives a second copy. |
| 37 | Elspeth Resplendent | — | ★★ | +1 counter and keyword; −3 puts a ≤3 MV permanent from the top 7 onto the battlefield (a free enters, R1); −7 five Angels. |
| 38 | Divine Visitation | — | ◇ | Creature tokens become 4/4 flying Angels. ~7 token makers today (count before adding, G-61). |
| 39 | Herald of War | — | △ | Attack-only value (R1). |
| 40 | Light of the Legion | — | △ | 6 MV; mentor/death counters. |
| 41 | Valkyrie Harbinger | — | ★ | 6-mana lifelink Angel; each end step with 4+ life gained makes a 4/4 Angel (doubled, R4). Resplendent Angel does it for 3. |
| 42 | Ob Nixilis, the Ascended | — | ★★ | 7-mana Angel: enters destroying all their TAPPED creatures (blink after they attack = another wipe); end step Angel if you gained life (R4). |
| 43 | Sephara, Sky's Blade | — | ★ | Your other fliers are indestructible; alt cost tap four fliers + {W}. ~19 evasive bodies. |
| 44 | Avacyn, Angel of Hope | — | ★ | 8 MV; everything you control indestructible. Late protection. |
| 45 | Parhelion II | — | ◇ | 8-mana vehicle, crew 4, attacking Angels. |
| 46 | Orvar, the All-Form | — | ◇ | Instant/sorcery targeting your permanent → token copy. Ephemerate is the only targeted blink spell left. |
| 47 | Seraphic Steed | — | ◇ | {G}{W} lifelink first striker; saddled attack → Angel. Early drop. |
| 48 | Metropolis Angel | — | ★★ | Attack with any creature with counters → draw. A counters PAYOFF (R7) on a flier. |
| 49 | Torens, Fist of the Angels | — | ★★ | Every creature cast makes a 1/1 token that enters (R2). |
| 50 | Sigarda, Font of Blessings | — | ★★★ | Other permanents hexproof (protection), and cast Angels and Humans from the top of your library (Humans 14 + the Angel sub-theme) — card advantage every turn. |

### Batch 3 (cards 51–75)

| # | Card | Own | Verdict | Note (rule) |
|---|---|---|---|---|
| 51 | Soul of Emancipation | — | ★★ | 7 MV Bant: enters destroying up to three nonland permanents (their owners get 3/3 Angels). A blink repeats a three-for-one (R1, R7). |
| 52 | Cleric Class | — | ★★★ | {W}: every gain is +1; level 2: every gain puts a +1/+1 counter on a creature; level 3 reanimates. Turns each per-entry gain into a counter (R3) and gives the counters theme a source. |
| 53 | Essence Channeler | — | ★ | 2-drop that grows per gain; passes counters on death. Redundant with Voice of the Blessed. |
| 54 | Priest of Possibility | — | △ | Perpetual keywords from the top 7; small. |
| 55 | Prophet of the Planeswalker | — | △ | Needs planeswalkers to behold (deck runs 0 today). |
| 56 | Unflinching Hortimancer | own | ◇ | 2-drop gain → counter, ward 1. Filler-tier payoff. |
| 57 | Voice of the Blessed | — | ★★ | {W}{W} 2-drop: a counter per gain — with per-entry gains it flies by turn 4–5, indestructible at 10. |
| 58 | Aerith Gainsborough | own | ★ | Owned 3-drop lifelink that grows per gain; death spreads counters to legends. |
| 59 | Rescue Girl, First Responder | — | ★★ | Flier; "{T}: Return another target permanent you control to its owner's hand" every turn — re-buys an enters trigger (or saves a creature). |
| 60 | Hallowed Haunting | — | △ | Enchantment-cast payoff; ~6 enchantments. |
| 61 | Rosa, Resolute White Mage | own | ◇ | Combat-step counter + lifelink. Owned. |
| 62 | Teshar, Ancestor's Apostle | — | ★★ | Every historic spell (legendaries are ~20 of the deck, plus Panharmonicon, Sagas) reanimates a ≤3 MV creature — Soul Warden, Reflector Mage, Skyclave come back and re-trigger. |
| 63 | Bishop of Rebirth | — | ◇ | Same recursion on ATTACK only (R1). |
| 64 | Minwu, White Mage | — | ◇ | Counters on Clerics per gain; ~4 Clerics in the deck. |
| 65 | Victory's Envoy | — | ★ | Upkeep: a counter on each other creature. 5 MV. |
| 66 | Saint Elenda | — | ★★ | 7 MV lifelink; enters: conjure and cast free from its spellbook (a blink repeats it); end step: an X/X where X = life gained this turn — doubled by Y'shtola (R4). |
| 67 | Mikaeus, the Lunarch | — | ◇ | X counters; a blink returns it at X = 0 (R5). |
| 68 | Quicksilver Servitor | — | ◇ | Proliferate on cards drawn this turn. |
| 69 | Arcus Acolyte | — | △ | Outlast counters; sorcery-speed taps. |
| 70 | Conclave Guildmage | — | △ | Late token sink. |
| 71 | Conclave Mentor | — | ★★ | {G}{W}: every counter placement gets +1 — Galadriel's counter mode, Archangel, Heliod, Cleric Class. |
| 72 | Dina, Flesh Sower | — | ◇ | Lifelink 2-drop that grows perpetually. |
| 73 | Emmara, Soul of the Accord | — | ◇ | Lifelink token when tapped (needs a tap outlet — Tocasia). |
| 74 | Emmara, Voice of the Conclave | — | ★ | Enters: draft a card from its spellbook — a blink drafts another. Convoke. |
| 75 | Yuna, Grand Summoner | — | ★ | Mana creature (any colour) that adds counters to the next creature. |

### Batch 4 (cards 76–100, incl. the earlier consideration list)

| # | Card | Own | Verdict | Note (rule) |
|---|---|---|---|---|
| 76 | Queen Allenal of Ruadach | — | ★ | P/T = your creature count (wide deck); every token batch adds a 1/1. |
| 77 | Arwen's Gift | — | ★ | Scry 2 + draw 2 for {2}{U} with two legends (the deck runs ~20). |
| 78 | Arwen, Mortal Queen | — | ★★ | Indestructible counter she can hand out with +1/+1 and a LIFELINK counter (a permanent lifelinker); a blink refreshes her indestructible counter (R5 as an upside). |
| 79 | Arwen, Weaver of Hope | — | ★★★ | "Each other creature you control enters with additional +1/+1 counters equal to Arwen's toughness" — every blink returns a creature with 3+ counters (R1), and counters on Arwen raise the number. |
| 80 | Arwen Undómiel | — | ★★ | {G}{U}: every scry puts a counter on a creature; a cheap scry payoff (R7). |
| 81 | Selfless Samurai | — | △ | Sacrifice to protect; Samurai/Warrior clause is dead here. |
| 82 | Virulent Emissary | own | ★★ | {G} 1-drop deathtouch; gains 1 per creature entering (R2/R3). Owned. |
| 83 | Evolution Sage | — | ◇ | Landfall proliferate. |
| 84 | Accomplished Alchemist | — | ★★ | Taps for X of one colour, X = life gained this turn — the lifegain engine becomes ramp. |
| 85 | Felidar Sovereign | — | ★★ | Alt-win at 40 life in your upkeep. |
| 86 | Sakashima of a Thousand Faces | — | ★★★ | Copy your best creature, legend rule off — a second Y'shtola, Soul Warden, Archangel. |
| 87 | Resplendent Angel | own | ★★★ | 4/4 Angel each end step with 5+ gained; two with Y'shtola (R4). |
| 88 | Aang, Swift Savior | own | ★★★ | Flash; airbend a creature OR SPELL — protection and interaction in one. |
| 89 | Wan Shi Tong, Librarian | own | ◇ | A blink returns it with X = 0 (R5). |
| 90 | Greenhouse Propagator | own | ★★ | Gain 1 per creature entering + {T}: Add {G}. |
| 91 | Daxos, Blessed by the Sun | — | ★★ | Gain on enter AND die; {W}{W}. |
| 92 | Ojer Taq, Deepest Foundation | — | ◇ | Triples creature tokens; ~7 token makers. |
| 93 | Anointed Procession | — | ◇ | Doubles all tokens (incl. Kwia's Lotus). |
| 94 | Emiel the Blessed | — | ★★★ | "{3}: blink another creature" repeatable + counters on entry. |
| 95 | Drogskol Reaver | — | ★★★ | "Whenever you gain life, draw a card" — one card per creature entering with Soul Warden effects out (R3). |
| 96 | Smothering Tithe | — | ◇ | Treasure off their draws; off-theme ramp. |
| 97 | Boon-Bringer Valkyrie | — | ★ | Backup grants lifelink/flying/first strike and a counter. |
| 98 | King T'Challa | own | ★★ | Flash; draws whenever a player draws their second card each turn. |
| 99 | Black Panther, Claws of Bast | — | ✗ | Attacks-alone payoff. |
| 100 | Lyra, Archangel of Dawn | — | ★ | Counters on every Angel per gain; good only with 8+ Angels. |

### Batch 5 — pile part 2 (37 cards)

| Card | Own | Verdict | Note (rule) |
|---|---|---|---|
| Dwynen, Gilt-Leaf Daen | own | △ | Elf lord; ~1 Elf in the deck. |
| Disciple of Freyalise // Garden of Freyalise | — | ★★ | Modal DFC: a land slot (untapped for 3 life) or a 6-drop that sacrifices a creature to gain X and draw X. |
| Ledev Champion | — | △ | Attack-only. |
| Tolsimir, Friend to Wolves | — | ★★★ | Enters → Voja (3/3 Wolf) → "gain 3 life and that creature fights up to one target creature you don't control." Every blink: removal + 3 life + a token entering (R1/R2/R7). |
| Tolsimir, Midnight's Light | own | ★★ | Enters → a 5/5 trample Wolf token; lifelink. Owned. |
| Ezuri, Stalker of Spheres | — | ★ | Draw per proliferate; only with a proliferate package. |
| Elven Passage | own | ◇ | Tapped basic fetch (no Elves to untap it). |
| Song of Freyalise | — | ◇ | Saga ramp then a counter on everything. |
| Freyalise, Skyshroud Partisan | — | △ | Elf walker. |
| Grateful Apparition / Guildpact Informant | — | △ | Combat proliferate. |
| Dreamtide Whale | — | ◇ | Vanishing; proliferate on the second spell. |
| Lulu, Stern Guardian | — | ★ | Stuns an attacker every attack; {3}{U} proliferate. Defensive. |
| Ichormoon Gauntlet | — | ◇ | Needs planeswalkers. |
| Mesmerizing Dose | — | ★ | Lock-down Aura + proliferate. |
| Gitaxian Anatomist / Bloom Hulk | — | ★ | Proliferate on entering — blinkable, but only with counters worth growing. |
| Tezzeret's Gambit | — | ★ | Draw 2 + proliferate. |
| Tekuthal, Inquiry Dominus | — | ◇ | Proliferate doubler; needs density. |
| Inexorable Tide | — | ★ | Every spell proliferates. 5 MV. |
| Unnatural Restoration / Planewide Celebration | — | ◇ | Recursion + proliferate. |
| Expand the Sphere | — | ★ | Two lands or proliferate. |
| Venomous Brutalizer | — | △ | Toxic. |
| Huatli's Raptor | — | ★★ | {G}{W} 2-drop: proliferate on entering (R1). |
| Quintorius, Fate Splitter | — | ★★ | 0: proliferate + gain 3 every turn; −3 token + a counter on each creature. |
| Tainted Observer | — | ★★ | Flier; pay {2} on each creature entering to proliferate (R2). |
| Merfolk Skydiver | — | ★ | Enters with a counter on a creature; late proliferate. |
| Contagion Dispenser | — | ★★ | Proliferating on your turn drafts a card. |
| Tidus, Yuna's Guardian | — | ★ | Combat-only payoff. |
| Roalesk, Apex Hybrid | — | ★★ | Enters: two counters on another creature (R1); dies: proliferate twice. |
| Roalesk, Prime Specimen | — | △ | Disguise/cloak; little here. |
| Staff of Compleation | — | ★ | Life into cards ("Pay 4 life: Draw a card"), mana, proliferate. |
| Karn's Bastion | — | ◇ | Colourless proliferate land; the deck needs coloured sources. |
| Sword of Truth and Justice | — | ◇ | Combat-gated. |
| Huatli, Radiant Champion | — | ★★★ | +1 = a loyalty per creature (wide deck, R2); −8 emblem: "Whenever a creature you control enters, you may draw a card." Every blink after that draws. |
| Huatli, the Sun's Heart | — | △ | Toughness damage. |

### Batch 6 — pile part 3 (11 cards; "Elesh Norn" read as all three)

| Card | Own | Verdict | Note (rule) |
|---|---|---|---|
| Flare of Fortitude | — | ★★ | Free (sacrifice a nontoken white creature): your life can't change, your permanents gain hexproof and indestructible — a sweeper answer (R7). |
| Elesh Norn // The Argent Etchings | — | ◇ | Punisher; its Saga destroys your own non-Phyrexian board. |
| Elesh Norn, Grand Cenobite | — | ★★ | 7 MV: your creatures +2/+2, theirs −2/−2 — a one-sided wipe of small creatures. |
| Elesh Norn, Mother of Machines | — | (in deck) | |
| Defiler of Dreams | — | ★ | Draw on every blue permanent cast (~15 blue permanents). |
| Sylvan Library | — | ★★ | {1}{G}: see two extra cards a turn; pay 4 life each to keep them — the lifegain engine turns into cards (R3). |
| Hurska Sweet-Tooth | — | ◇ | Per-gain pump for {G/W}. |
| Tranquil Frillback | — | ★★ | Enters: pay {G} up to three times for artifact/enchantment removal, graveyard exile, 4 life — a blink repeats it (R1, R7). |
| Defiler of Vigor | — | ★ | A counter on every creature per green permanent cast (~12 green permanents). |
| Azor, the Lawbringer | — | ★ | 6 MV; attack to gain X and draw X. |
| Kellan, the Kid | own | ★★ | Flying lifelink 3-drop; a spell cast from anywhere but your hand (Serra Paragon, Sigarda) casts a permanent from hand free. Owned. |
| Shanna, Purifying Blade | — | ★★★ | {G}{W}{U} lifelink: "At the beginning of your end step, you may pay {X}. If you do, draw X cards. X can't be greater than the amount of life you gained this turn." Y'shtola's extra end step = a second draw (R3, R4). |

## 5. Consolidated plan (live)

**FINAL PROPOSAL (2026-10-30, revised after part 3)** — 19 swaps, chosen for how the cards work together.
Preview: legal; floor B; card advantage 6 → 9; interaction 9 (reads 9 but is ~11 by hand —
Yangchen and Aang are classifier holes); avg MV 3.75 → 3.84; tempo-sim on-curve 49.9%
with one Forest → Plains.

| Out | In | Why together |
|---|---|---|
| Spark Double | Sakashima of a Thousand Faces | Same copy job + legend rule off (double Y'shtola / Soul Warden / Archangel). |
| Getaway Glamer | Flickering Hound | A blink on every creature cast. |
| Rumor Gatherer | Tocasia, Dig Site Mentor | Every creature surveils → Denzilore, Matoya, Planetarium. |
| Political Triumph | Cleric Class | Every gain +1; level 2 a counter per gain. |
| Eternal Witness | Serra Paragon (owner *) | Recasts a ≤3 MV permanent from the yard each turn. |
| Ephara, God of the Polis | Huatli, Radiant Champion | Ultimate in ~2 turns on a wide board → draw on every creature entering. |
| Curator of Destinies | Drogskol Reaver | A card per gain = per creature entering. |
| Venser, Shaper Savant | The Wandering Emperor | Instant-speed exile + tokens. |
| Sundering Archaic | The Legend of Yangchen (own) | Exiles two of their permanents; draws 3. |
| Another Round | Emiel the Blessed | Repeatable "{3}: blink". |
| Palantír of Orthanc | Detention Sphere | Removal for any nonland permanent. |
| Vanguard Seraph | Sigarda, Font of Blessings | Hexproof for the board; Angels/Humans from the top. |
| Holy Cow | Resplendent Angel (own) | 4/4 Angel per end step, two with Y'shtola. |
| Bloombrute | Chulane, Teller of Tales | A card + a land per creature cast; re-buy ability. |
| Salvation Swan | Aang, Swift Savior (own) | Flash protection/interaction. |
| Ignis Scientia | Arwen, Weaver of Hope | Every blinked creature returns with 3+ counters. |
| Aang, at the Crossroads | Tolsimir, Friend to Wolves | Blink = fight removal + 3 life + a token. |
| Wood Elves | The Book of Exalted Deeds (owner *) | Angel each end step with 3+ gained; two with Y'shtola. |
| Enlightened Confidant | Shanna, Purifying Blade | Same end-step lifegain hook, but draws X cards (twice with Y'shtola). |

Kept on purpose: Lilysplash Mentor and Saheeli (owner keeps), every multiplier (protect list).
Next in line (★★ not taken): Sylvan Library, Tranquil Frillback, Flare of Fortitude, Kellan (the Kid, own), Elesh Norn (Grand Cenobite), Ajani (Strength of the Pride), Prison Realm, Elrond (Master of
Healing), Nissa (Steward of Elements), Oracle of the Alpha, Stenn, Ojutai's Command, Speaker
of the Heavens, Metastatic Evangel, Righteous Valkyrie, Valgavoth, Shalai, Angel of
Sanctions, Elspeth Resplendent, Ob Nixilis, Metropolis Angel, Torens, Soul of Emancipation,
Voice of the Blessed, Rescue Girl, Teshar, Saint Elenda, Conclave Mentor, Arwen (Mortal
Queen), Arwen Undómiel, Virulent Emissary (own), Accomplished Alchemist, Felidar Sovereign,
Greenhouse Propagator (own), Daxos, King T'Challa (own), Tolsimir (Midnight's Light, own),
Disciple of Freyalise, Huatli's Raptor, Quintorius (Fate Splitter), Tainted Observer,
Contagion Dispenser, Roalesk (Apex Hybrid).

**Protect (the ranking cannot see their value):** Y'shtola, Silver Surfer, Thassa, Don &
Leo, Teleportation Circle, Elesh Norn, Panharmonicon — every enters/end-step multiplier.
