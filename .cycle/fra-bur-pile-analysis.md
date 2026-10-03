# FRA BUR pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the deck(s) land and the findings are folded into the
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
