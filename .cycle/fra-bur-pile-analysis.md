# FRA BUR pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS — the black-red build (deck 81 Detention Hall) was SUPERSEDED 2026-10-03: the owner reworked the pile into red-green, and deck 81 is now Heartwood Foundry (see fra-rgu-pile-analysis.md). The black-red list is in git history; the blue-black Theorist variant is still open.** Delete once the deck(s) land and the findings are folded into the
deck files' `#: notes:` blocks. A scratchpad, not a source of truth — decks/ are.

**Source list:** 44-card Reality Fracture (FRA) pile in blue/black/red, pasted 2026-10-03
(+ Ral Zarek, SOS). Aimed at a NEW deck (owner open to 1/2/3 colours and variants), so the
7 cards already in decks — Tinybones, Massacre Girl, Samut, Chandra Torch (60 Redline),
Ajani Unrelenting, Ingris (55 Mardu Waves), Ral Zarek (five decks) — stay ELIGIBLE: copies
are shared across decks. Ownership: the FRA set is not ingested, so the library reads most
of these as 0 — treat the pile as owned (owner's statement).

Colour split of the pile: U 8 · B 16 · R 15 · UB 2 · UR 1 · BR 2.

## 1. The decision framework

Measured context: Standard. Black-red dual depth is good (owned: 4 Dark Fortress, Blood Crypt,
Blazemire Verge, Temple of Malice, Razortrap Gorge, Rakdos Guildgate; FRA's Stingerquill
Annex). Owned black-red-castable walkers beyond the pile: Liliana, Dreadhorde General; Chandra,
Flameshaper; Chandra, Spark Hunter; plus colourless Tezzeret, Cruel Captain / The Aetherspark
/ Ugin. Owned death payoffs: Meathook Massacre II, Midnight Reaper, Funeral Room, Sothera,
Agent Venom, Buzzard-Wasp Colony, South Wind Avatar.

- **R1 — The engine's currency is LOYALTY ACTIVATIONS and CREATURE DEATHS.** Grade a card by
  how many engine events it produces or consumes, not by its printed body.
  Producers: every walker + the Jace token the Ways make; Way of the Deathbringer's −2
  (sacrifice → a death). Converters: Ajani Unrelenting (activation → Cadet), Way of the
  Necromancer (death → +1 loyalty on EVERY walker), Massacre Girl (death → drain 1),
  Liliana Dreadhorde (death → draw), Way of the Pyromancer (+1 → {R}),
  Way of the Mind Sculptor (an activation removing 2+ → draw).
- **R2 — The loop is Deathbringer + Necromancer.** A walker's −2 sacrifices a token for a 4/4
  Beast; the death puts +1 on every walker (Necromancer), so the activating walker nets −1
  while every OTHER walker gains one. That is the deck's spine. Count fodder for it (R6).
- **R3 — A death counts; an EXILE does not (G-42).** Overwrite the Multiverse and Identity Echo
  exile, so they fire no death payoff. Garruk, Veiled Butcher's exile clause is opponent-only
  and harmless. Tokens never reach the graveyard: Winter's +1/+0 and Loot's threshold count
  CARDS only.
- **R4 — Noncombat damage is a second, smaller resource.** Command the Stage returns to hand
  each upkeep if an opponent was dealt noncombat damage last turn; Massacre Girl grows on it.
  Sources: Massacre Girl drains, Ingris attack pings, Gideon the Oathless, Extended Absence,
  Chandra Torch +1, Warlord's −4, Tinybones, Stingerquill Charm.
- **R5 — Cadet (Wizard Soldier) tokens are a micro-theme.** Ajani Unrelenting, Stingerquill
  Charm, Ingris, Command the Stage and Semester Foreseer make them; Command the Stage grows
  every other Wizard token. They are also the cheapest sacrifice fodder for R2.
- **R6 — Count fodder before trusting the loop (G-61).** Sacrifice outlets: Deathbringer −2 (on
  every walker), Winter ETB, Loot (only at 7+ graveyard cards), Garruk −2 (each player).
  Fodder: Cadets, Jace's Illusions (blue only), Kiora's body, Phoenix, Sphinx of False
  Conclusions (returns as a token copy once).
- **R7 — Three colours must clear a MEASURED bar.** The previous FRA pile rejected Bant on mana
  (33 of 36 spells under 90% on curve). The blue cards that pull hardest are UU (Chandra Chill,
  Theorist Jace) — a third colour needs a scratch-draft `consistency` run, not a hope.
- **R8 — Walkers need protection from the board.** Ways give every walker an ability, but a
  walker deck with too few blockers dies to attackers. Count bodies that can block.

## 2. Standing error list

- (none yet)

## 3. Cross-batch observations

- **Black-red superfriends-aristocrats is the strongest cluster** (R1/R2): 4 Ways
  (Necromancer, Deathbringer, Pyromancer, Warlord) + 4 pile walkers (Chandra Torch, Garruk
  VB, Ral Zarek, Ajani Unrelenting) + death payoffs (Massacre Girl, Darklight Phoenix,
  Winter, Liliana the Repentant) + 5 removal spells. Distinct from 60 Redline (black-red max-speed
  aggro) — check with `deck.py similar`.
- **Mono-black is a real variant**: Necromancer + Deathbringer, Garruk, Ral, + owned Liliana
  Dreadhorde; the creature/removal core is all black. Thinner on walkers (3 + Jace token).
- **Blue offers two signals**: (a) a UB "Theorist" build — Theorist Jace, Chandra Chill, Way of
  the Mind Sculptor (draws off every −2), Uldaros Theorix, Theorix Charm, Sphinx of False
  Conclusions; (b) a UR **Saheeli + Draconic Visitor** combo — every noncreature spell makes a
  Thopter, and Visitor turns each artifact token into a 5/5 flying Dragon. Neither is decided
  mid-batch (rule 7).
- Deck 2 (UW/UG Jace, previous pile) is still the owner's open call; Theorist Jace, Chandra
  Chill and Mind Sculptor were graded there too. Copies are shared, so no conflict.

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out. Columns:
BR (black-red) / UB / UR. "—" = off-colour for that build.

### Batch 1 (cards 1–22)

| Card | BR | UB | UR | Note |
|---|---|---|---|---|
| Fblthp, Impossibly Lost | — | ◇ | ◇ | draw 2 on combat damage; a 1/1 in a walker deck rarely connects |
| Chandra, Chill of Compliance | — | ★★ | ★★ | UU 3 walker; +1 surveil-and-regrow noncreature; −X stun |
| Traxos, Academy Guardian | — | △ | ◇ | prowess flier; needs a spell-dense list |
| Semester Foreseer | — | △ | △ | 4-mana 3/4 + prepared Cadet; filler |
| Sphinx of False Conclusions | — | ★ | ★ | flash flier, loots on attack, returns once as a token on death (R6 fodder twice) |
| The Theorist, Jace Beleren | — | ★★★ | ★★ | draws every opponent draw step; +1 Illusions = R2 fodder; −2 mass bounce |
| Ruric Thar, Biomagus | — | △ | △ | 6-mana UU; no engine role |
| Way of the Mind Sculptor | — | ★★ | ★ | draws on every activation removing 2+ (Deathbringer −2, Warlord −4, Jace −3, Garruk −2/−3, Ral −2) |
| Liliana the Repentant | ★★ | ★★ | — | 2-drop; mills 2 per creature/walker entering (feeds Winter, Loot, Rewrite Regrets, Ral −2); exhaust reanimates a creature OR walker |
| Way of the Necromancer | ★★★ | ★★ | — | R2 core: every death → +1 loyalty on every walker; empower 2 for 2 mana |
| Break Under Pressure | ★★ | ★★ | — | instant edict on their BIGGEST creature/walker + 2 life |
| Danitha, Spear of Agony | △ | △ | — | first strike 3-drop; grows only off targeted spells |
| Loot, the Anomaly | ★ | ★ | — | sac outlet at threshold 7; each sac makes his power MORE negative, which he assigns as positive — a growing attacker. Needs Liliana/Ral filling the yard |
| Gideon the Oathless | ★ | ★ | — | 3-mana 3/3, ward–discard; pings when their creatures enter or they activate loyalty (R4) |
| Tinybones, Pocket Nuisance | ◇ | ◇ | — | ETB discard + discard pings; only Ral −1 / Garruk −3 make more discards |
| Way of the Deathbringer | ★★★ | ★★ | — | R2 core: every walker gains −2: sac a creature → 4/4 trample Beast; empower 5 |
| Winter, Tormented Loner | ★★ | ★★ | — | ETB: sac a token → each opponent sacrifices; grows with creature/walker CARDS in yard (R3) |
| Darklight Phoenix | ★★ | ★ | — | 4-mana hasty flier; returns at combat if two creatures died this turn — Deathbringer + Winter / Garruk −2 do it |
| Rewrite Regrets | ★★ | ★★ | — | reanimates a creature OR WALKER ≤6, + empower 2 |
| Extended Absence | ★★ | ★★ | — | instant exile creature/walker + 1 noncombat damage (R4) |
| Garruk, Veiled Butcher | ★★★ | ★★★ | — | +2 shrink, −2 edict-and-Beast (a death on your side too, R2), −3 discard/draw |
| Massacre Girl, Most Wanted | ★★ | ★★ | — | R1 converter: each death of yours drains 1; grows on noncombat damage |

### Batch 2 (cards 23–44)

| Card | BR | UB | UR | Note |
|---|---|---|---|---|
| Overwrite the Multiverse | ★ | ★ | — | the walker deck's natural wrath (walkers survive, empower X) — but EXILE fires no death payoff (R3); 1-of at most |
| Gallia, the Merrymaker | △ | — | △ | haste only for creatures with counters; the deck makes few |
| Samut, Hazoret's Champion | ★ | — | ★ | team haste: Beasts, Cadets, Zombies and Kiora's Dragon attack at once |
| Stingcaster Mage | ★ | — | ★ | hasty 2-drop that flashes back Rewrite Regrets / Break / Absence / Forte / a charm; fodder after |
| Chandra's Emberling | ◇ | — | ★ | grows per noncreature spell; Ways, walkers and removal all count, but a 2/2 body |
| Way of the Pyromancer | ★★ | — | ★ | walkers gain +1: add {R} (ramp + loyalty); under Ajani Unrelenting every +1 is also a Cadet |
| Command the Stage | ★★ | — | ◇ | Cadet + grows other Wizard tokens; returns to hand every upkeep after noncombat damage (R4) — repeatable fodder (R6) |
| Fulminous Forte | ★★ | — | ★★ | instant: 1 to each of their creatures/walkers, or 5 to one |
| Identity Echo | ◇ | — | ◇ | exiles your own creature/walker for the next one off the top (R3 — an exile, not a death); 4 mana per sorcery-speed use |
| Pyre Rhymer | △ | — | ◇ | prowess 3/3; prepared ritual needs Mountains |
| Way of the Warlord | ★★ | — | ★★ | every walker gains −4: 2 to a creature/walker + 2 to a player (R4); the Jace token it makes can use it at once |
| Arni, Renowned Champion | △ | — | △ | trample; pumps off entering power |
| Chandra, Torch of Defiance | ★★★ | — | ★★★ | card/damage +1, ramp +1, −3 removal |
| Ajani Unrelenting | ★★★ | — | ★★ | EVERY loyalty activation (any walker, the Jace token included) makes a Cadet — the fodder engine for R2; −3 sweeps all but your tokens |
| Kiora of Fire and Ashes | ★ | — | ★ | 6-mana top end: 2/2 + 5/5 flying Dragon; the 2/2 is fodder |
| Theorix Charm | — | ★ | — | counter-tax / −2/−2 / mill-3-draw |
| Uldaros Theorix | — | ★★ | — | cast copies of a yard Way, walker and removal spell (total MV ≤6) for free |
| Saheeli, Jewel of Avishkar | — | — | ★★ | noncreature spell → hasty Thopter; with Draconic Visitor each Thopter is a 5/5 flying Dragon |
| Stingerquill Charm | ★★ | — | — | 3 damage any target / deathtouch trick / hasty Cadet |
| Ingris Stingerquill | ★★ | — | — | flier; every attacker pings each opponent (R4); {4}: Cadet + team haste |
| Draconic Visitor | ◇ | — | ★★ | 5/5 flier; artifact tokens become 5/5 Dragons. In black-red only Chandra, Spark Hunter's 0 (a Vehicle token) feeds it |
| Ral Zarek, Guest Lecturer | ★★ | ★★ | — | +1 surveil 2 fills the yard; −2 reanimates a ≤3 (Liliana R, Winter, Gideon, Ingris, Stingcaster) |

Owned non-pile support graded for the black-red build (read in full 2026-10-03):

| Card | BR | Note |
|---|---|---|
| Liliana, Dreadhorde General | ★★★ | death → draw; +1 Zombie = fodder; −4 each player sacrifices two |
| Sothera, the Supervoid | ★★★ | each of YOUR creature deaths → each opponent exiles a creature: Deathbringer's −2 becomes a repeatable edict |
| Funeral Room | ★ | death → drain 1 (the Massacre Girl effect on an enchantment) |
| Midnight Reaper | ◇ | draws on NONTOKEN deaths only — the fodder here is tokens |
| Meathook Massacre II | ◇ | {B}{B}{B}{B} — mono-black only |
| Chandra, Spark Hunter | ◇ | 0: a Vehicle token each turn (Draconic Visitor food); +2 rummage |
| Chandra, Flameshaper / Ugin / Tezzeret / The Aetherspark | △ | 7-mana or artifact-themed; off-engine |

## 5. Consolidated plan (live)

**Recommended: a black-red planeswalker-aristocrats deck.** The engine (R1/R2):
- walkers activate;
- Ajani makes a Cadet on every activation;
- Deathbringer's −2 sacrifices it for a 4/4 Beast;
- Necromancer puts +1 on every walker;
- Liliana Dreadhorde draws, Massacre Girl drains and Sothera makes them exile a creature.

Black-red mana is two double-pip colours (RR: Chandra, Ajani, Kiora, Ingris; BB: Garruk, Ral,
Liliana DG, Sothera) on deep dual support.

Core (~30 of 36 nonland):
- Walkers (5–6): Chandra Torch, Garruk VB, Ral Zarek, Ajani Unrelenting, Liliana DG
  (+ Chandra Spark Hunter optional).
- Ways (4): Necromancer, Deathbringer, Pyromancer, Warlord.
- Creatures (~10): Liliana the Repentant, Winter, Gideon the Oathless, Ingris, Darklight Phoenix,
  Massacre Girl, Samut, Stingcaster Mage, Loot, Kiora.
- Enchantment: Sothera.
- Spells (~7): Break Under Pressure, Extended Absence, Fulminous Forte, Stingerquill Charm,
  Rewrite Regrets, Command the Stage, Overwrite the Multiverse.

Fodder count (R6): Ajani (per activation), Liliana DG +1, Command the Stage (recurring),
Stingerquill Charm, Ingris {4}, Garruk −2 Beast, Kiora's 2/2 — seven sources before any body.

Variants the pile surfaced (decide after the main build):
- **UB "Theorist"** — swaps red for Theorist Jace, Chandra Chill, Mind Sculptor, Uldaros,
  Theorix Charm, Sphinx of False Conclusions on the same black core. Best as a variant of the
  black-red deck (shared core = near-duplicate as a separate deck).
- **Mono-black** — Necromancer/Deathbringer/Garruk/Ral/Liliana DG + Sothera, Meathook II; walker
  count thin (3 + Jace token).
- **UR Saheeli + Draconic Visitor** — a real combo but this pile supplies only ~6 of its cards; a
  collection-driven build, out of this pile's scope.
- **Grixis** — rejected on R7: UU (Theorist, Chill) + BB + RR across three colours.

PROTECT (once built): Way of the Necromancer, Way of the Deathbringer, Ajani Unrelenting,
Sothera — their value is in the rest of the deck, which `cuts` cannot see.

## 6. Build log

- **2026-10-03 — deck 81 Detention Hall drafted** from §5's core. Additions beyond the pile,
  from the owned pool: Sanctum Lurker (walkers survive at 0 loyalty; +2 drain on every walker —
  makes the big minuses free), The Aetherspark and Chandra, Spark Hunter (cheap walkers = Way
  carriers), Liliana Dreadhorde, Sothera, Funeral Room, Phyrexian Arena, Umbral Collar Zealot
  (free sac outlet), Hellish Sideswipe, Fell, Nocturnal Hunger. Re-screen swaps: Nocturnal
  Hunger > Murder (strict upgrade), Aetherspark > Tezzeret. Floor A (interaction 15, card adv 6),
  sources B 19 / R 17, lowest on-curve Ingris 78%. Closest deck by theme is 1 Black Sun (0 shared
  cards); by cards, 60 Redline (4).
