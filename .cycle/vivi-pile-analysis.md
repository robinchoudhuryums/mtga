# Vivi Ornitier pile — analysis (TEMPORARY working doc)

**Status: FIRST DRAFT WRITTEN (deck 103) — awaiting the owner's decisions in §5.** Building a NEW Izzet (UR) Historic Brawl deck around Vivi
Ornitier from the owner's pile. Delete once the deck is drafted and the findings are folded into
its `#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Source list:** the owner's paste (123 cards: Vivi + 107 distinct nonbasic + 11 basics; the paste
holds 3 Stark Industries and 4 Swiftwater Cliffs, of which Brawl's singleton rule allows one each).
All 107 are Historic Brawl legal and castable in UR. 97 nonland candidates + 9 nonbasic lands.
No dedupe against other decks: cards are shared across decks in Arena (CLAUDE.md), so a card
another deck runs is still a candidate here. Ownership is information only (Player Profile);
40 of the 107 are unowned.

**Builder project:** `builds/vivi` (deck 103), holding the 33 bench cards with reasons.
Board: https://claude.ai/artifact/UAJaJmXDnduGibXkYJLZBd

**Slot budget:** 100 cards = Vivi + 99. At ~35 lands (9 nonbasic + ~26 basics) that leaves ~64
spell slots, so ~33 of the 97 nonland candidates are cut. Lands are revisited once the spell
count settles (Vivi is a mana source, which argues for the low end of the 36–40 Brawl norm).

## 1. The decision framework

Vivi Ornitier {1}{U}{R}, 0/3: "{0}: Add X mana in any combination of {U} and/or {R}, where X is
Vivi's power. Activate only during your turn and only once each turn. / Whenever you cast a
noncreature spell, put a +1/+1 counter on Vivi and it deals 1 damage to each opponent."

- **R1 — The number is NONCREATURE SPELLS CAST.** Each one is +1 power (= +1 mana from Vivi's
  next activation) and 1 damage to the opponent. A creature spell does neither. Grade a creature
  on whether it EARNS the slot a noncreature spell would have filled.
- **R2 — Vivi's mana is ONCE per turn, on YOUR turn, and grows within the turn.** Cast the cheap
  noncreature spells first, then tap Vivi for the big payoff. So: cheap spells (MV ≤ 2) are the
  fuel; X spells and expensive sorceries are the sink, and their printed cost overstates what
  they cost here from mid-game on. Instants held for the opponent's turn cannot use Vivi mana.
- **R3 — CAST vs COPY.** Vivi triggers on CAST. A copy that is merely created (Thousand-Year
  Storm, most "copy target spell") does not trigger her; "cast a copy" (Arcane Bombardment) and
  casting from graveyard/exile (flashback, harmonize, Dreadhorde Arcanist) do. Magecraft ("cast
  or copy") triggers on both. Read each copy card for which it is.
- **R4 — Vivi is the engine and a removal magnet.** Protection for her (counters, hexproof,
  blink) and card flow that keeps the spell count up are worth more than in a generic Izzet pile.
  Commander tax makes a second cast costly.
- **R5 — 1v1 at 25 life.** Vivi's ping plus the burn/noncombat-damage payoffs (Electro, Stormcatch
  Mentor-type prowess, Firebending) are a real clock; count total reach, not just creatures.
- **R6 — The interaction floor at 100 cards** (CLAUDE.md, per-60 scaling): A needs interaction 12
  and interaction + card advantage 19. Counterspells and burn both count; bounce is tempo, not
  interaction (G-25).
- **R7 — A spell that makes OTHER spells (tokens that are spells, Clues, cast-from-exile)** is
  worth more than its face: count what it adds to R1.

## 2. Standing error list
- **Classifier holes found (G-67, fix in one batch later, not now):** Abstract Paintmage (a ritual
  each first main: ramp), As Foretold (a free spell each turn: cost cheat), Sanar, Unfinished
  Genius (prepared tutor), Teferi, Mage of Zhalfir (sorcery-speed lock: protection) all score ZERO
  roles. `make postedit` acknowledged them in role_baseline.txt; Invasion of Kaladesh's zero is
  fair. None of them moves deck 103's floor (it already clears A).

## 3. Cross-batch observations
- **Two-card combo (batch 3):** Niv-Mizzet, Parun + Niv-Mizzet, Visionary loop draw ↔ ping until the
  opponent dies. Vivi's own trigger starts it (her ping is noncombat damage → Visionary draws →
  Parun pings). Tutors that find either half: Sanar (instant/sorcery only — no), so the combo is
  drawn naturally; card flow raises the odds.
- **The pile is creature-heavy.** Of the first 75, roughly 50 are creatures, most of them
  "whenever you cast" payoffs. R1 says creature spells don't grow Vivi, so the build has to choose
  between a spell-dense Vivi deck and a payoff-dense creature deck. Count the noncreature spells
  once all four batches are read.

## 4. Running verdicts
Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

### Batch 1 (cards 0–24 of 97)
| Card | Verdict | Note |
|---|---|---|
| Niv-Mizzet, Visionary | ★★★ | Vivi's ping is noncombat damage to an opponent, so every noncreature spell also DRAWS a card. The single best payoff in the pile. |
| Electro, Assaulting Battery | ★★★ | Every instant/sorcery refunds {R}, and unspent red mana persists (Vivi's red keeps through phases too). Leaves-play X burn is reach (R5). |
| Stormcatch Mentor | ★★★ | 2-drop cost reducer for instants/sorceries: more spells per turn = more Vivi growth (R1/R2). |
| Melek, Reforged Researcher | ★★ | First instant/sorcery each turn costs {3} less; a big body as the yard fills. |
| The Emperor of Palamecia | ★★ | 2-mana dork whose mana is noncreature-only (exactly this deck's spend); transforms off 4+-mana spells, which Vivi mana makes routine. |
| Colorstorm Stallion | ★★ | Ward/haste 3/3; a 5+-mana spell copies it, and Vivi's mana makes 5+ routine mid-game (R2). |
| Spectacular Skywhale | ★★ | +3 power per instant/sorcery on a flier: the biggest damage-per-spell creature here. |
| Ovika, Enigma Goliath | ★★ | 7-drop finisher: each noncreature spell makes MV-many hasty Goblins. |
| Thousand-Year Storm | ★★ | Copies do NOT trigger Vivi (R3), but copied burn/draw late in a Vivi turn is the deck's biggest swing. A 6-MV sink for Vivi mana. |
| Prismari, the Inspiration | ★★ | Storm on every instant/sorcery; 7/7 flier, ward 5 life. Same R3 caveat; a finisher. |
| Abandon Attachments | ★★ | 2-mana instant card flow (discard 1, draw 2): fuel, and a Lesson. |
| Solstice Revelations | ★★ | Free-casts the next nonland card if its MV < Mountains; flashback makes it two casts (R1). Mountain count decides it — revisit with the land plan. |
| The Dawning Archaic | ★★ | Cheapens with the yard; each attack casts an instant/sorcery from the yard free (a CAST, so Vivi triggers — R3). |
| Wiccan, Rising Magician | ★ | Each noncreature spell exiles a blocker until end step. Never target Vivi (she would return without counters). |
| Loki Laufeyson | ★ | Cheap copier of a small instant/sorcery (copy, not cast — R3). |
| Emeritus of Conflict // Lightning Bolt | ★ | 2-drop first strike; after a 3-spell turn, casting its Bolt copy is a CAST (Vivi triggers). |
| Elemental Mascot | ★ | Flier; 5+-mana spells impulse-draw a card. |
| Tolarian Terror | ★ | Cheap 5/5 ward late; the yard fills slower in 100 cards. |
| Dragonfly Swarm | ★ | Flier whose power is the noncreature cards in the yard. |
| Professor Zei, Anthropologist | ★ | Looter that later regrows an instant/sorcery. |
| The Scarlet Witch | ◇ | Discounts MV 4+ instants/sorceries by her power; depends on how many the list keeps. |
| High Fae Trickster | ◇ | Flash for everything — but flashed spells can't use Vivi's mana (R2). A 4/2 flash flier either way. |
| Firebending Student | ◇ | Prowess + attack mana; wants to attack, which the list may not support. |
| Balmor, Battlemage Captain | ◇ | Team pump per spell — a go-wide card in a deck that is not wide. |
| Firebender Ascension | △ | Copies ATTACK triggers; the pile has few. Only its 2/2 token is generic value. |

### Batch 2 (cards 25–49)
| Card | Verdict | Note |
|---|---|---|
| Thunder Magic | ★★★ | 1-mana instant removal that scales with mana: Thundaga (8 damage) is a Vivi-mana sink (R2). |
| Sorcerer Class | ★★★ | Level 3 makes every instant/sorcery deal damage equal to the spells cast that turn — noncombat damage, so Niv-Mizzet draws that many. Level 2 turns every creature into instant/sorcery mana. Level-ups are not spells (no Vivi trigger). |
| Lightning Strike | ★★ | 2-mana instant burn, any target. |
| Vibrant Outburst | ★★ | 2-mana instant: 3 damage plus a tap. |
| Tome Blast | ★★ | 2 damage, then a second CAST from flashback (R1). |
| Iroh's Demonstration | ★★ | 2-mana sweeper of 1-toughness OR 4 to a creature. |
| Nibelheim Aflame | ★★ | Vivi as the chosen creature = a one-sided-ish wipe at her power (it also hits your other creatures). Flashback casts it again and draws four. |
| Artistic Process | ★★ | Modal: 6 to a creature, 2 to each of theirs, or a hasty 3/3 flier. |
| Wisdom of Ages | ★★ | 7-mana sorcery that returns every instant/sorcery: a full refuel and the best late Vivi-mana sink. {U}{U}{U} — check blue sources. |
| Firemind's Research | ★★ | A counter per instant/sorcery; cashes in for cards or 5 damage. |
| Sanar, Unfinished Genius | ★★ | Enters prepared: casting the copy of its tutor sorcery is a CAST (Vivi triggers) and finds any instant/sorcery; Treasures after a spell. |
| Abstract Paintmage | ★★ | {U}{R} every first main for instants/sorceries — a free ritual each turn. |
| Orbital Plunge | ★ | 4-mana 6 damage; excess makes a Lander. |
| Heated Argument | ★ | 5-mana instant 6 damage plus 2 to the face. |
| Enigma Drake | ★ | Flier sized by instants/sorceries in the yard. |
| Malcolm, the Eyes | ★ | Flier/haste; Clue on the second spell each turn. |
| Kaza, Roil Chaser | ★ | Discounts the next instant/sorcery by Wizard count; the pile holds ~8 Wizards (Vivi included). |
| Sprite Dragon | ★ | Grows permanently per noncreature spell. |
| Spider-Man 2099 | ★ | Double strike; end-step burn after a flashback / free-cast / Dawning Archaic cast. |
| Stormchaser Mage | ◇ | 2-drop prowess flier. |
| Arius, Flyby Trawler | ◇ | Attack-driven card selection; the deck has little discard to grow it. |
| Improbable Alliance | △ | Needs a second draw each turn; its loot costs 6. |
| Invasion of Kaladesh | △ | 2-mana noncreature spell (Vivi triggers) for a Thopter; the Vehicle back needs artifacts. |
| Captain Storm, Cosmium Raider | ✗ | Artifact/Pirate payoff; the pile has neither. |
| Jhoira, Ageless Innovator | ✗ | Artifact cheat; the pile has almost none. |

### Batch 3 (cards 50–74)
| Card | Verdict | Note |
|---|---|---|
| Niv-Mizzet, Parun | ★★★ | With Niv-Mizzet, Visionary it is a two-card WIN: each draw pings the opponent (Parun), each ping draws a card (Visionary) — a loop that ends at 25 damage. Alone it draws on every instant/sorcery anyone casts. {U}{U}{U}{R}{R}{R}: needs deep sources of both colours. |
| Baral and Kari Zev | ★★ | The first instant/sorcery each turn casts a cheaper one free from hand — a second CAST (R7) — or makes a hasty Ragavan. |
| Ral, Crackling Wit | ★★ | Grows per noncreature spell; +1 Otters, −3 card flow, −10 storm. Itself a noncreature cast. |
| Resonating Lute | ★★ | Every land taps for TWO instant/sorcery mana; draws at 7+ in hand. Itself a noncreature cast. |
| Gandalf the Grey | ★★ | Per instant/sorcery a fresh mode: 3 damage to each opponent (Niv draws 3), copy the spell, tap/untap. |
| Tellah, Great Sage | ★★ | Hero token per noncreature spell; 4+ mana spent draws two (Vivi mana makes that routine); 8+ burns. |
| Indris, the Hydrostatic Surge | ★★ | Draws on every instant/sorcery and seeds four storm Lightning Bolts. |
| Saheeli, Jewel of Avishkar | ★★ | A hasty flying Thopter per noncreature spell. |
| Rapturous Moment | ★★ | Draw 3, discard 2, add five mana: card flow that refunds itself, and fuel for a big Vivi turn. |
| Paradigm Shifter | ★★ | Conjures a spellbook spell; taps for two instant/sorcery mana. |
| Lilah, Undefeated Slickshot | ★ | Prowess; multicolored instants/sorceries from hand get plotted and recast free (two casts). Count the multicolored spells before keeping. |
| Neera, Wild Mage | ★ | Once a turn trades a cast spell for a free random one (both are casts). |
| Gray and Adira, Forever Joined | ★ | A hasty token copy each combat after a noncreature spell — a copy of Niv-Mizzet, Visionary doubles its draws. Copying Vivi is useless (a copy has no counters). |
| Keranos, God of Storms | ★ | Indestructible enchantment: 3 damage per nonland first draw. |
| Rootha, Mastering the Moment | ★ | X/X hasty flier each combat after an instant/sorcery. |
| Tempest Angler | ★ | Grows permanently per noncreature spell. |
| Galazeth Prismari | ★ | Flier + Treasure; artifacts tap for instant mana (few artifacts here). |
| Role Reversal | ★ | Swap a weak permanent for their best one: interaction with upside. |
| Thundering Djinn | ◇ | Attack damage = cards drawn this turn; good beside Niv, weak alone. |
| Fevered Visions | ◇ | Symmetric draw; the opponent draws too (G-42 shape). |
| Najal, the Storm Runner | ◇ | Sorceries at flash speed lose Vivi mana (R2); attack-gated copy. |
| Spectacle Mage | ◇ | Discounts MV 5+ instants/sorceries by 1. |
| Don & Raph, Hard Science | △ | Affinity for artifacts on attack; the deck has few artifacts. |
| Breeches, the Blastmaker | ✗ | Needs an artifact to sacrifice. |
| Brudiclad, Telchor Engineer | ✗ | Token/artifact deck card. |

### Batch 4 (cards 75–96)
| Card | Verdict | Note |
|---|---|---|
| Arcane Bombardment | ★★★ | Each turn's first instant/sorcery CASTS a growing pile of copies from the yard (casts — Vivi triggers on each, R3). |
| Chandra, Hope's Beacon | ★★★ | Copies one instant/sorcery a turn, +2 mana, impulse-draw, −X burn; itself a noncreature cast. |
| Zaffai and the Tempests | ★★ | A free instant/sorcery from hand every turn (a cast). |
| The Vision and Scarlet Witch | ★★ | Every spell adds {R} and a counter: a ritual on every cast. |
| Wanda's Vision | ★★ | The second spell each turn casts a free card off the top (a cast). |
| As Foretold | ★★ | A growing free spell each turn; itself a cheap noncreature cast. |
| Fiery Inscription | ★★ | 2 damage to each opponent per instant/sorcery — noncombat, so Niv-Mizzet, Visionary draws two. |
| Charred Foyer // Warped Space | ★★ | An extra card every upkeep; Warped Space makes one exiled card free each turn. |
| Tempest Trapper | ★★ | Taps for two instant/sorcery mana; the third spell each turn gives a free random card. |
| Teferi, Mage of Zhalfir | ★★ | Opponents can only act at sorcery speed: no instant removal on Vivi in response to a big turn (R4). {U}{U}{U}. |
| The Locust God | ★ | A hasty flying Insect per card drawn; huge beside Niv-Mizzet. |
| Storm of Saruman | ★ | Copies the second spell each turn (a copy, not a cast — R3). |
| Victor Timely, Wily Tycoon | ★ | Recasts an MV ≤ 4 instant/sorcery from the yard on entry (a cast). |
| Goliath Daydreamer | ★ | Hand-cast instants/sorceries go to exile and are recast free on attack. |
| Dreadhorde Arcanist | ◇ | Attack-recast, capped by its 1 power. |
| Vision, Spectral Synthezoid | ◇ | A free noncreature spell each turn, on an 8-mana body. |
| Enraged Flamecaster | ◇ | 2 damage per MV 4+ spell. |
| Academy Instructor | ◇ | An Officer token per noncreature spell. |
| Jacob Hauken, Inspector | ◇ | Slow card flow; the free-cast back half costs 6 to reach. |
| Kylox, Visionary Inventor | △ | Sacrifices your creatures to free-cast; 7 mana. |
| Glóin, Dwarf Emissary | △ | Historic-spell Treasures; few historic spells. |
| Katara, Waterbending Master | ✗ | Wants spells on the opponent's turn — the turn Vivi's mana can't be used (R2). |

## 5. Consolidated plan (live)

**Measured fact that shapes everything:** the pile holds only **30 noncreature spells** of 97 and
**no counterspells**. A deck built from the pile alone is therefore ~27 noncreature spells and ~37
creatures, while R1 says Vivi grows only on noncreature spells.

**First draft: deck 103, Black Mage — Vivi** (`decks/103-black-mage/deck.txt`), built only from the
pile: 27 noncreature spells (every one above △), 37 creatures (★★★/★★ plus the best ★), 35 lands
(the 9 nonbasics + 13 Island + 13 Mountain). Measured: floor **A** (interaction 15, card advantage
15 against 12 / 19), legal, every printing known. Distinct from decks 25/37/71, which are 60-card
Standard Izzet lists.

**Open decisions for the owner:**
1. **Supplement from outside the pile?** The optimal list wants more cheap noncreature spells
   (cantrips, counterspells) in place of the weakest creatures — a counterspell is also the best
   protection for Vivi (R4). The Player Profile says build the optimal list; the request said "from
   this pile". Owner's call.
2. **Manabase:** 8 of the 9 nonbasic lands enter tapped. Owned untapped duals that fit: Steam
   Vents (×2), Spirebluff Canal, Riverglide Pathway; craft options Fiery Islet, Shivan Reef, Sulfur
   Falls. Each replaces a tapped land or a basic.
3. **Niv-Mizzet, Parun at {U}{U}{U}{R}{R}{R}** casts on turn 5 only 19% of the time with 22 U / 21 R
   sources. It is half the combo, so better lands matter more here than anywhere.

**Protect list** (value the cut ranking can't see): Vivi; both Niv-Mizzets (the combo); Electro (a
refund on every instant/sorcery); Stormcatch Mentor (cost reduction); Arcane Bombardment (the
free-cast engine).

**Bench** (the 33 pile cards not in the draft): kept with reasons on the Builder board.
