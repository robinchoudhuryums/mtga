# Hashaton pile (from deck 53) — analysis (TEMPORARY working doc)

**Status: PLAN REVISED (§5a), awaiting owner picks** (started 2026-10-25; all 118 graded). Delete once the new deck is drafted and the
findings are folded into its `#: notes:` block. A scratchpad, not a source of truth —
decks/ are.

**Target:** a NEW 100-card Historic Brawl deck (Arena's "Brawl" queue), commander
**Hashaton, Scarab's Fist** (DRC) 1 — `{W}{B}`, identity W/U/B. Working deck id **91**.
**Source list:** the owner's 118-card pile, built out of deck 53 (Sibsig Choir, mono-B
Standard zombies). 37 of the 118 are deck 53's own cards; that is intended (a new deck in a
new format), so the pile is NOT deduplicated against the roster. All 118 are Historic Brawl
legal. 73 are creatures, 43 Zombie-typed. Five names were DFCs stored under the full
`Front // Back` name and were corrected (Sidequest: Hunt the Mark, Liliana Heretical Healer,
Ludevic, Invasion of Amonkhet, Ultimecia).

**The cut is large:** 118 candidates for ~62 nonland slots (99 + commander, ~37 lands).
Roughly half the pile does not make it.

## 1. The decision framework

Hashaton: *"Whenever you discard a creature card, you may pay {2}{U}. If you do, create a
tapped token that's a copy of that card, except it's a 4/4 black Zombie."*

- **R1 — A discarded creature costs {2}{U}, not its printed cost.** The copy keeps every
  ability, so it fires the card's enters trigger and keeps its static and activated text, on
  a 4/4 body. Grade a creature on its TEXT as a 4/4 Zombie. A 7-drop with a huge enters
  trigger (Massacre Wurm) is a 3-mana spell here; a small creature whose value is its body
  is worth about a 4/4 for 3. Printed cost still matters for the copies you CAST.
- **R2 — The engine is DISCARD OUTLETS.** Hashaton does nothing without them. Looting,
  rummaging, cycling, discard as a cost, "each player discards" — count them every batch.
  An outlet that discards a creature on our own terms is worth more than one that makes us
  discard at random or only at end of turn.
- **R3 — Discarding fills the graveyard, so graveyard recursion double-dips.** The card
  is copied by Hashaton AND sits in the yard for embalm / eternalize / reanimation (Scarab
  God, God-Pharaoh's Gift, Liliana's Mastery, Dread Summons…). Embalm and eternalize are
  themselves "a token copy that's a Zombie", so they stack with the same lords.
- **R4 — The copies are ZOMBIES, and ONLY Zombies.** "Except it's a 4/4 black Zombie"
  replaces the card's types, so every Hashaton token counts for Zombie lords and Zombie
  payoffs, whatever the original was, and loses its own tribe. Zombie lords and "Zombies
  you control" effects scale with the engine.
- **R5 — The copy enters TAPPED.** No surprise blocker the turn you make it; haste or
  attack triggers on the copy are a turn late.
- **R6 — Colours are not "white splash".** Hashaton costs `{W}{B}` every time it is cast
  or recast, and EVERY copy costs `{2}{U}`. So: B main, U the repeated activation colour,
  W light but required for the commander. White CARDS can be few; white SOURCES cannot
  be near zero. Decide W on source count, not on card count.
- **R7 — Brawl facts.** Singleton, 100 cards, 1v1 at 25 life, free first mulligan. The
  tier floor is scaled ×1.67: A needs interaction 12 and interaction + card advantage 19.
- **R8 — Legend rule.** A token copy of a legendary creature is legendary. Singleton means
  the original is rarely also out, but a reanimated original plus its Hashaton copy is a
  conflict.
- **R9 — The value of a creature card in this deck has TWO uses**: cast it, or discard it
  for a copy. A creature whose text works poorly as a copy (it wants to be cast — cast
  triggers, "when you cast", flash ambushes, X spells) loses half its value here.

## 2. Standing error list

- E1: The Sibsig Ceremony destroys every creature we CAST — grade it against the cast half of R9, not against deck 53.
- E3: A discard PAYOFF (Bone Miser, Chariot, Chancellor) is not an OUTLET; count the two separately (O1).
- E4–E7: see §5a (speed, Sibsig, copy-makers, token-count payoffs).
- E2: "Whenever another NONTOKEN creature dies" (Agent Venom) misses the engine: Hashaton's copies are tokens.

## 3. Cross-batch observations

- O1 (after batch 2): **discard OUTLETS are the scarce resource.** In 60 cards only three are
  true outlets (Cryptbreaker, Collector's Vault, Ral −1), against ~35 creatures worth
  copying. R2 says Hashaton does nothing without them, so expect to fetch outlets from
  OUTSIDE the pile (UB looters/rummagers, cycling, discard-as-cost) — run
  `pool.py --regex` for the discard shape before the final plan.
- O2: **Zombie lords are plentiful** (Death Baron, Gisa, Lifecraft Engine, Cursecloth,
  Chronicle, Eternal Skylord's flying grant). Pick the 4–5 best, not all.
- O4 (after batch 4): the pile holds only 7 outlets; the outside search adds the four best
  (Psychic Frog, Selhoff Entomber, Dreadwing Scavenger, Key to the City) plus cycling
  creatures, which are outlet and discard target in one card.
- O3: **two cards want the same graveyard creature**: Abyssal Harvester (this turn), Patchwork
  Crawler and Havengul Runebinder (exile it) compete with R3 recursion. Fine in moderation.

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

### Batch 1 (cards 1–30)

| # | Card | Verdict | Note |
|---|---|---|---|
| 1 | Sothera, the Supervoid | ★ | Every creature of ours that dies = each opponent exiles one of theirs. A repeatable edict, but only with deaths; the deck is not a sacrifice deck by default. |
| 2 | Death Baron | ★★★ | R4: every Hashaton copy gets +1/+1 and deathtouch. As a discarded copy the lord still works (it pumps OTHER Zombies). |
| 3 | Hour of Victory | △ | 2/2 now; the tutor needs max speed (an opponent losing life on four of our turns). |
| 4 | The Sibsig Ceremony | ✗ | G-42: destroys every creature we CAST, including the lords we want to keep. Deck 53's engine, not this one's. Copies are not cast, so it does not kill them, but the cast half of R9 dies. |
| 5 | Cryptcaller Chariot | ★★★ | R2 payoff: each discard makes that many 2/2 Zombies, on top of Hashaton's copy. Crewed by any 4/4 copy. |
| 6 | Lifecraft Engine | ★ | A 3-mana colourless Zombie lord (+1/+1) that is itself a Zombie when crewed. |
| 7 | Dread Summons | ★ | Mill both players for X, a 2/2 per creature milled; fills our yard for R3. |
| 8 | Gisa, the Hellraiser | ★★ | Zombie lord (+1/+1, menace) plus two 2/2s on any crime each turn — targeting an opponent with removal or Ral is a crime. |
| 9 | Unstoppable Slasher | ★★ | Deathtouch Zombie; combat damage halves their life; returns once. A 4/4 copy of it is a real clock. |
| 10 | Soul-Shackled Zombie | ★ | R1: {2}{U} for a 4/4 that exiles two cards from a graveyard and drains 2. Graveyard hate that points at THEIR yard (G-42 check: choose their yard, not ours). |
| 11 | Cursecloth Wrappings | ★★ | Zombie anthem plus a per-turn embalm grant at the card's mana cost — R3 recursion for everything discarded. |
| 12 | Risen Necroregent | △ | 5/4 for five; the token needs max speed. |
| 13 | Avenger of the Fallen | ◇ | Mobilize X = creature cards in our yard, which discarding grows. Not a Zombie (its copy is). |
| 14 | Deathless Pilot | ★ | R2 loop: discard it (copy), return it to hand for {3}{B}, discard again — a creature card that comes back to feed every outlet. |
| 15 | Zul Ashur, Lich Lord | ★★ | {T}: cast a Zombie creature card from the graveyard. R3 for every discarded Zombie. |
| 16 | Ninja Teen | ◇ | Drain on leave; level 3 lets graveyard creatures be cast with sneak. Slow. |
| 17 | Agent Venom | △ | Draws only on NONTOKEN deaths, and the engine's bodies are tokens. |
| 18 | Doctor Doom | ★★ | R1: for {2}{U}, a 4/4 plus two 3/3 Doombots, indestructible while they live, and a draw every end step. A top discard target. |
| 19 | Chronicle of Victory | ★ | Zombies +2/+2, first strike, trample for six; the draw-on-cast half misses copies (R9). |
| 20 | Winter, Tormented Loner | ★ | R1: an edict on entry for {2}{U}, sacrificing a token. |
| 21 | Collector's Vault | ★★ | R2 outlet: {2},{T} loot plus a Treasure, every turn. |
| 22 | Bitterbloom Bearer | ◇ | Upkeep 1/1 fliers for 1 life; not a Zombie. |
| 23 | Ral Zarek, Guest Lecturer | ★★ | R2: −1 lets US discard (and the opponent); −2 reanimates MV 3 or less; +1 surveil. |
| 24 | Deadly Precision | ★ | One-mana kill spell, a token pays the cost. |
| 25 | Eaten Alive | ★ | One-mana exile for a creature or planeswalker. |
| 26 | Robot Domination | ★★ | Draws whenever a creature card hits our graveyard from ANYWHERE — every discard of a creature refills the hand. |
| 27 | Funeral Room // Awakening Hall | ★ | Drain per death; the back door returns every creature card in the yard. A finisher after a long discard game. |
| 28 | Sidequest: Hunt the Mark | ★ | Removal on entry; the Treasures and transform are a bonus. |
| 29 | Withering Torment | ★ | Instant removal for a creature or enchantment. |
| 30 | The Cloning of Shredder | ◇ | Six mana for three copies of one graveyard creature, over three turns. |

Outlets this batch (R2): Collector's Vault, Ral Zarek. Discard payoffs: Cryptcaller Chariot,
Robot Domination. Zombie lords: Death Baron, Gisa, Lifecraft Engine, Cursecloth Wrappings,
Chronicle of Victory. Recursion: Zul Ashur, Cursecloth, Ral −2, Funeral Room, Deathless Pilot.

### Batch 2 (cards 31–60)

| # | Card | Verdict | Note |
|---|---|---|---|
| 31 | The Final Days | ★ | Two 2/2 Horrors now; flashback makes one per creature card in our yard, which discarding grows (R3). |
| 32 | Liliana, Dreadhorde General | ★★★ | Draws on ANY creature death (tokens count); +1 Zombie; −4 double edict. |
| 33 | Massacre Wurm | ★★★ | R1 headline: {2}{U} for −2/−2 on their whole board plus 2 life per creature of theirs that dies. |
| 34 | Blasphemous Edict | △ | Symmetric 13-creature sacrifice; it wipes the token army this deck builds. |
| 35 | Midnight Reaper | △ | E2: nontoken deaths only. |
| 36 | Abyssal Harvester | ★★ | Exiles a creature card put in a graveyard THIS turn for a token copy: a discarded creature becomes TWO copies (Hashaton's and this). Competes with yard recursion for the same card. |
| 37 | Realm of Koh | ★ | Land: untapped B with a basic, a late token sink. |
| 38 | Binding Mummy | ★ | Every other Zombie entering taps an artifact or creature — every Hashaton copy is a tap-down. White 2-drop. |
| 39 | Pride of the Road | △ | Speed-gated double strike. |
| 40 | God-Eternal Oketra | ★ | Double strike; every creature we CAST makes a 4/4 Zombie. {3}{W}{W} is heavy for light white (R6); as a discarded copy it keeps the cast trigger. |
| 41 | Patchwork Crawler | ◇ | Eats graveyard creatures for their activated abilities; competes with R3 recursion. |
| 42 | Oglor, Devoted Assistant | ★★ | Upkeep self-mill; every creature card put in our yard from HAND or library perpetually gains "leaves the graveyard: a 2/2 Zombie" — every discard plus every later recursion is a token. |
| 43 | Aven Eternal | △ | Amass 1 flier. |
| 44 | Essence Anchor | ◇ | Upkeep surveil; a 2/2 on a turn a card left our yard — real only with embalm/recursion density. |
| 45 | Eternal of Harsh Truths | △ | Afflict/unblocked draw on a 1/3. |
| 46 | Geralf, the Fleshwright | ★ | Zombies entering grow per other Zombie that entered this turn (a Hashaton copy plus Chariot tokens); second spell each turn makes a 2/2. |
| 47 | Crush Dissent | ◇ | Soft counter plus amass 2. |
| 48 | Havengul Runebinder | ★ | Exile a graveyard creature: a 2/2 and +1/+1 on EVERY Zombie. Its {2}{U} competes with Hashaton's {2}{U} each turn. |
| 49 | God-Eternal Kefnet | ★ | 4/5 flier that copies a drawn instant or sorcery; fine as a 4/4 flying copy. |
| 50 | Necroduality | ◇ | Copies NONTOKEN Zombies entering, so it misses every Hashaton copy (E2's shape); only cast or recast Zombies. |
| 51 | Outlaw Stitcher | △ | A 2/2 Zombie plus counters only on multi-spell turns. |
| 52 | Eternal Skylord | ★★ | "Zombie tokens you control have flying" — every Hashaton copy is a Zombie token (R4), so the whole army flies. |
| 53 | Commence the Endgame | ◇ | Six-mana instant: draw two, amass hand size. |
| 54 | Assemble from Parts | ★ | One mana: a graveyard creature gets a perpetual "make a 4/4 Zombie copy of me" — Hashaton's effect from the yard. |
| 55 | Dreadmalkin | △ | A sacrifice outlet that grows itself. |
| 56 | Dread Wanderer | ◇ | Returns itself from the yard with ≤1 card in hand; discard fodder that comes back, but hand-size-gated. |
| 57 | Cryptbreaker | ★★★ | R2: {1}{B},{T}, discard a card: a 2/2 Zombie — a ONE-mana repeatable outlet. Tapping three Zombies draws a card. |
| 58 | Aphemia, the Cacophony | △ | Needs enchantment cards in the yard. |
| 59 | Cemetery Recruitment | ★ | Return a creature card (draw if Zombie) — the discarded card comes back to be discarded again. |
| 60 | Dreadhorde Invasion | ★ | Upkeep amass 1; power-6 Zombie tokens gain lifelink (the 4/4 copies reach 6 with two lords). |

### Batch 3 (cards 61–90)

| # | Card | Verdict | Note |
|---|---|---|---|
| 61 | Undead Hand Ninja | ★ | Deathtouch 2-drop Zombie; drains on every creature card leaving our yard (embalm, Zul Ashur, recursion). |
| 62 | Waste Not | △ | Triggers on OPPONENT discards only; the pile has three such effects (Ral −1, Liliana +2, Invasion of Amonkhet). |
| 63 | Wight | ◇ | Tapped 3/2; tokens off creatures it damaged and killed. |
| 64 | Ammit Eternal | ◇ | 5/5 for three that shrinks per opponent spell. |
| 65 | Headless Rider | △ | E2: nontoken Zombie deaths only. |
| 66 | Grim Reaper's Scythe | ★ | A 2/2 whenever creature cards leave our yard; sorcery reanimation for two creatures. |
| 67 | Liliana, Heretical Healer | ★ | Flips on a nontoken death; the walker's +2 makes EACH player discard — an R2 outlet — and −X reanimates. |
| 68 | Liliana, the Last Hope | ★★ | +1 shrinks a creature; −2 mills two and regrows a creature; the emblem is a Zombie army. |
| 69 | Never // Return | ★★ | Three-mana creature/planeswalker kill; the aftermath half casts from the yard for a 2/2 and graveyard hate. |
| 70 | Vizier of the Scorpion | ★ | Zombie tokens have deathtouch (every copy); overlaps Death Baron. |
| 71 | Boneyard Desecrator | △ | A sacrifice outlet on a 3/4 menace. |
| 72 | Kalitas, Traitor of Ghet | ★★ | Their dying nontoken creatures become OUR 2/2 Zombies; lifelink. Not a Zombie itself. |
| 73 | Bone Miser | ★★★ | R2 payoff: discard a creature → 2/2, a land → {B}{B}, anything else → draw. Every outlet use pays twice with Hashaton. |
| 74 | Ghoulcaller Gisa | ★ | {B}, sacrifice a 4/4 copy → four 2/2s. A token multiplier and a sacrifice outlet. |
| 75 | Liliana, Death's Majesty | ★★ | +1 a 2/2 and mill two; −3 reanimates as a Zombie; −7 destroys all non-Zombies. |
| 76 | Liliana's Mastery | ★ | Anthem plus two 2/2s. |
| 77 | Army of the Damned | ◇ | Eight mana for thirteen 2/2s, with flashback. The top-end finisher if any. |
| 78 | Blessed Ghoul | ★ | One-drop that returns to hand for {2}{W/B} (hybrid, payable with B) — Deathless Pilot's loop at half the price. |
| 79 | Wayward Servant | ★ | Drain 1 per other Zombie entering — every copy and token. |
| 80 | Zahur, Glory's Past | ◇ | Once-a-turn sacrifice-to-surveil; the token half needs max speed. |
| 81 | Embalmed Ascendant | ◇ | 1/2 plus a 2/2; drain at max speed. |
| 82 | Lazotep Chancellor | ★★ | R2 payoff: pay {1} per discard to amass 2. Two-mana Zombie. |
| 83 | Ludevic, Necrogenius | ◇ | Self-mill on entry and attack; the transform is a big late sink. |
| 84 | Soul Diviner | ◇ | Draws by removing counters (the amass Army carries many). |
| 85 | Skull Skaab | △ | Exploit payoff off nontoken creatures. |
| 86 | Venser, Corpse Puppet | ✗ | Needs proliferate; the pile has none. |
| 87 | Diregraf Captain | ★★ | Lord (+1/+1), deathtouch, and a drain per Zombie death. |
| 88 | Gleaming Overseer | ★★ | Zombie tokens have hexproof AND menace — protects every Hashaton copy. |
| 89 | Invasion of Amonkhet // Lazotep Convert | ★ | Mill three each, they discard, we draw; flips into a 4/4 Zombie copy of any graveyard creature. |
| 90 | Tomebound Lich | ★★★ | R2 OUTLET on a body: loot on entry and on each hit; deathtouch, lifelink. Its copy loots again. |

Outlets running count: Cryptbreaker, Collector's Vault, Ral −1, Tomebound Lich, Liliana
(flipped) +2 = 5. Discard payoffs: Cryptcaller Chariot, Robot Domination, Bone Miser,
Lazotep Chancellor, Oglor.

### Batch 4 (cards 91–118)

| # | Card | Verdict | Note |
|---|---|---|---|
| 91 | Gisa and Geralf | ★★ | Mills four on entry; once each turn cast a Zombie creature from the yard — R3 for everything discarded. |
| 92 | Enter the God-Eternals | ★★ | 4 damage, gain 4, mill four, amass 4 — removal that builds a Zombie. {U}{U} heavy. |
| 93 | Fallen Shinobi | ◇ | Ninjutsu value; its copy enters tapped (R5), so the hit is a turn late. |
| 94 | Grimgrin, Corpse-Born | ★ | Each attack destroys a creature; untaps by sacrificing a token. Its copy is already tapped, as the card wants. |
| 95 | Havengul Lich | ★ | {1}: cast a creature card from ANY graveyard this turn. |
| 96 | The Scarab God | ★★★ | Upkeep drain and scry per Zombie; {2}{U}{B} makes 4/4 Zombie copies from any yard; returns to hand when it dies. Hashaton's ability on a second body. |
| 97 | Temmet, Naktamun's Will | ★★★ | R2 OUTLET every attack (loot), and every draw pumps all Zombies. W/U/B — it needs the white. |
| 98 | God-Pharaoh's Gift | ★★ | Each combat, a hasty 4/4 Zombie copy from our yard; the haste fixes R5 for its own copies. |
| 99 | Visage Bandit | ◇ | Clones our best creature. |
| 100 | Zephyr Singer | △ | Convoke flier. |
| 101 | Advanced Stitchwing | ★★ | R2 OUTLET: {2}{U}, discard TWO cards to return it — two creature discards are two Hashaton triggers. Flying Zombie. |
| 102 | Defiler of Dreams | ◇ | Draws on blue permanents; most of the engine is black. |
| 103 | Desertion | ◇ | Five-mana counter that steals a creature. |
| 104 | Fear of Failed Tests | ◇ | Draws on damage from a 2/7. |
| 105 | Inniaz, the Gale Force | ◇ | Flier swap engine; Eternal Skylord makes the Zombie tokens fly, which reaches its three-flier trigger. |
| 106 | Inexorable Tide | △ | Proliferate on each spell: Army counters and loyalty, but no counter theme. |
| 107 | Kindred Discovery | ★★ | Name Zombie: every Hashaton copy, token and Zombie entering or attacking draws a card. |
| 108 | Lier, Disciple of the Drowned | ◇ | Flashback for instants and sorceries; the deck is creature-led. |
| 109 | Ojutai's Summons | △ | A 2/2 flier twice for five. |
| 110 | Clone Legion | ◇ | Nine mana. |
| 111 | Aven Wind Guide | ◇ | Token flying/vigilance overlaps Eternal Skylord at more colours. |
| 112 | Denzilore Fatehold | ◇ | Scry/surveil counters; {W}{U}{U}. |
| 113 | Genku, Future Shaper | ◇ | Nontoken leaves → small tokens. |
| 114 | Ephara, God of the Polis | ◇ | Draws on each upkeep after a creature entered — tokens count — but {2}{W}{U} on light white. |
| 115 | Ultimecia, Time Sorceress | ★ | Surveil 2 on entry and attack; a late extra turn. |
| 116 | Zareth San, the Trickster | ◇ | Rogue ninjutsu; few Rogues. |
| 117 | Ashiok, Sculptor of Fears | ★ | +2 draw and mill both; −5 steals a creature from any yard. |
| 118 | Uldaros Theorix | ◇ | R9: "if you cast him" — its copy does nothing on entry. A six-drop to cast. |

Outlets in the pile, final count (O1): **7** — Cryptbreaker, Collector's Vault, Ral −1,
Tomebound Lich, Liliana (flipped) +2, Temmet, Advanced Stitchwing.

### Outside the pile — outlets and self-discarding creatures (O1's search)

`pool.py --regex` over WUB, Historic Brawl, permanents with a discard cost or a recurring
loot trigger found 73; the best, all read in full:

| Card | Verdict | Why |
|---|---|---|
| Psychic Frog | ★★★ | "Discard a card: +1/+1 counter" — a FREE, instant-speed, repeatable outlet; draws on hits. {U}{B}. |
| Selhoff Entomber | ★★★ | Zombie: {T}, discard a CREATURE card: draw. Card-neutral, exactly R2. |
| Dreadwing Scavenger | ★★ | Loots on entry and attack; flier; deathtouch at threshold. |
| Key to the City | ★★ | {T}, discard: a creature is unblockable; pay {2} on untap to draw. |
| Overlord of the Floodpits (owned) | ★★ | Draw two, discard one on entry and attack; impending lets it arrive for {1}{U}{U}. |
| Emet-Selch, Unsundered (owned) | ◇ | Loots on entry/attack; the flip EXILES what would hit our yard (G-42) — keep it unflipped. |
| Locke Cole (owned) | ◇ | Loots on combat damage; deathtouch, lifelink. |

Creatures with CYCLING discard themselves — a self-contained Hashaton trigger:

| Card | Verdict | Why |
|---|---|---|
| Archfiend of Ifnir | ★★★ | Every cycle or discard puts −1/−1 on each opposing creature; cycles itself, and its copy keeps the ability. |
| Alabaster Host Intercessor | ★★ | Plainscycling {2} (finds a W source, R6) and its copy exiles a creature on entry. |
| Malboro (owned) | ★ | Swampcycling; its copy makes them discard, lose 2 and exile three. |
| Angel of the Ruins | ◇ | Plainscycling; the copy exiles two artifacts/enchantments. |
| Timeless Dragon | ◇ | Plainscycling plus eternalize (a second Zombie copy). |

## 5a. Revision pass (2026-10-25, owner pushback on the left-out cards)

All 64 left-out cards re-read in full. Four first-pass errors, now on the standing list:

- **E4 — Speed is nearly automatic here.** "Start your engines" rises once on each of OUR
  turns when an opponent loses life, and ANY combat damage is life loss — plus Wayward
  Servant, Diregraf Captain, Undead Hand Ninja, The Scarab God's upkeep and Massacre Wurm
  all drain. Max speed is a few attacking turns away, so every speed card was under-graded:
  Hour of Victory (a max-speed TUTOR for any card) △→★, Risen Necroregent △→◇, Pride of
  the Road △→◇, Embalmed Ascendant and Zahur ◇ (live).
- **E5 — The Sibsig Ceremony was graded against the wrong half.** It destroys a creature
  we CAST, after its enters trigger, and the card lands in the graveyard. With Zul Ashur /
  Gisa and Geralf / Havengul Lich (all CAST from the yard, at {2} less) that is a loop:
  recast, enters trigger, die, a 2/2, back in the yard, again next turn — and every death
  feeds Robot Domination, Liliana Dreadhorde General, and the NONTOKEN-death cards E2 had
  ruled out (Midnight Reaper, Agent Venom, Headless Rider, Liliana Heretical Healer's flip).
  Hashaton's copies are never cast, so they stay. The cost is real: a lord we hard-cast
  dies — so lords go in through Hashaton, not the stack. ✗→★ as a SECOND ENGINE; an owner
  decision, because it pulls the list toward cast-and-die.
- **E6 — A copy-maker multiplies R1.** The Cloning of Shredder makes THREE non-legendary
  copies of one graveyard creature (three Massacre Wurm sweeps, six Doombots, three Scarab
  Gods) for six mana. ◇→★★.
- **E7 — Token-count payoffs were read in isolation.** Army of the Damned is thirteen
  Zombies ENTERING: with Kindred Discovery that is thirteen cards, with Wayward Servant
  thirteen drain, with Binding Mummy thirteen tap-downs. ◇→★★. Dreadhorde Invasion's
  lifelink line reads 6 power, which a 4/4 copy reaches with two lords ◇→★.
- Also up: **God-Eternal Oketra** ★→★★ (discarding it dodges its {W}{W} — R1 beats R6 — and
  every Zombie we recast from the yard makes a 4/4); **Liliana, Heretical Healer** ★→★★ once
  flipped her +2 is a per-turn R2 OUTLET, the scarce resource; **Ninja Teen** ◇→★ (level 2
  is a team menace anthem, level 3 casts graveyard creatures); **Vizier of the Scorpion** ★
  (redundant deathtouch in a singleton deck is the point, G-46); **Avenger of the Fallen**,
  **Essence Anchor**, **Inniaz** (Eternal Skylord's flying Zombie tokens reach its
  three-flier steal), **Denzilore Fatehold** (Scarab God's upkeep scry), **Soul Diviner**
  (Army and loyalty counters), **Necroduality** (nontoken Zombies we recast) ◇→★.

**Revised core: 8 swaps** — in The Cloning of Shredder, Army of the Damned, God-Eternal
Oketra, Hour of Victory, Liliana Heretical Healer, Ninja Teen, Vizier of the Scorpion,
Dreadhorde Invasion; out Chronicle of Victory, Liliana's Mastery, Dread Summons, Ghoulcaller
Gisa, Grim Reaper's Scythe, Assemble from Parts, Havengul Runebinder, Geralf. Scratch
measurement: interaction 14, card advantage 9 → 8, floor A. The Sibsig engine is a further
decision, not in this count.

## 5. Consolidated plan (live — after batch 4)

**Measured on a scratch build** of the 62 below plus a placeholder manabase (94 cards):
interaction **14**, card advantage **9**, protection 5, hand attack 2 — floor **A** (at
100 cards A needs interaction 12 and a sum of 19; this is 14 + 9 = 23). 36 of the 62 are
creature cards, 19 Zombie-typed. Untiered; the letter is the owner's.

### Core 62 (proposed)

- **Outlets (11)** — R2, the scarce half: Cryptbreaker, Psychic Frog*, Selhoff Entomber*,
  Tomebound Lich, Temmet, Collector's Vault, Dreadwing Scavenger*, Advanced Stitchwing,
  Ral Zarek, Key to the City*, Overlord of the Floodpits* (owned).
- **Self-discarding creatures (3)**: Archfiend of Ifnir*, Alabaster Host Intercessor*,
  Malboro* (owned).
- **Discard payoffs (5)**: Bone Miser, Cryptcaller Chariot, Lazotep Chancellor, Robot
  Domination, Oglor.
- **Discard targets — R1 (7)**: Massacre Wurm, Doctor Doom, Kalitas, Winter, Soul-Shackled
  Zombie, The Scarab God, Gisa and Geralf.
- **Zombie lords and tribal (9)**: Death Baron, Diregraf Captain, Gisa the Hellraiser,
  Eternal Skylord, Gleaming Overseer, Cursecloth Wrappings, Kindred Discovery, Unstoppable
  Slasher, Wayward Servant.
- **Recursion (8)**: Zul Ashur, God-Pharaoh's Gift, Liliana Death's Majesty, Liliana the
  Last Hope, Cemetery Recruitment, Abyssal Harvester, Assemble from Parts, Blessed Ghoul.
- **Interaction (10)**: Never // Return, Withering Torment, Deadly Precision, Eaten Alive,
  Sidequest: Hunt the Mark, Enter the God-Eternals, Liliana Dreadhorde General, Sothera,
  Grimgrin, Invasion of Amonkhet.
- **Value / flex (9)**: Undead Hand Ninja, Grim Reaper's Scythe, Funeral Room, Dread
  Summons, Liliana's Mastery, Ghoulcaller Gisa, Geralf, Havengul Runebinder, Chronicle of
  Victory.

\* = from outside the pile.

### Bench (from the pile, left out — in rough order of what comes back first)

Deathless Pilot (a second discard loop), Vizier of the Scorpion, Ashiok, Ultimecia, Havengul
Lich, God-Eternal Oketra, God-Eternal Kefnet, Binding Mummy, Dreadhorde Invasion, The Final
Days, Lifecraft Engine, Avenger of the Fallen, Army of the Damned, Ephara, Liliana Heretical
Healer, Patchwork Crawler, Essence Anchor, Dread Wanderer, Ninja Teen, Cloning of Shredder,
Fallen Shinobi, Uldaros Theorix. Out: The Sibsig Ceremony (E1), Venser (no proliferate),
Blasphemous Edict, Agent Venom / Midnight Reaper / Headless Rider (E2), Waste Not, and the
low-impact remainder (△).

### Protect list — what `cuts` cannot see

- The OUTLETS (Cryptbreaker, Psychic Frog, Selhoff Entomber, Collector's Vault, Key to the
  City): their worth is Hashaton's trigger, which no role pattern credits.
- Discard targets bought for their ENTERS text as a 4/4 (Massacre Wurm, Doctor Doom, Winter,
  Soul-Shackled Zombie): `cuts` grades their printed cost, R1 says that cost is {2}{U}.
- Eternal Skylord and Gleaming Overseer: their text affects Zombie TOKENS, the engine's
  output, so tag fit under-reads them.

### Open questions for the owner

1. **White (R6).** Only Hashaton, Temmet, Wayward Servant and Alabaster Host need {W}; the
   commander needs it EVERY recast. Proposal: ~9–10 W sources through duals/tri-lands and
   Plainscycling, not Plains-heavy basics.
2. **Creature density.** 36 creature cards is enough to feed Hashaton most turns; swapping
   flex noncreatures (Chronicle, Liliana's Mastery, Dread Summons) for bench creatures
   raises it if games stall with outlets and nothing to discard.
3. **Craft information** (owned counts are stale): of the 62, 44 read unowned — 11
   mythic, 18 rare, 10 uncommon, 5 common.
