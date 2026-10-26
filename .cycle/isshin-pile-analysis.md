# Isshin pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the deck is drafted and the findings are folded into
the deck file's `#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Source list:** the owner's 116-line pile, pasted 2026-10-26 (130 cards: 106 distinct
nonland, 10 distinct lands incl. 14 Swamp). Aimed at a NEW **Historic Brawl** deck (100
cards, singleton) with commander **Isshin, Two Heavens as One** ({R}{W}{B}, 3/4), "based on
deck 55a" (Mardu Waves — Imperial Storm, the roster's Standard Mardu spells deck). 52 of the
106 nonland cards already sit in other decks; they stay ELIGIBLE — copies are shared.
Scratch copy: `pile.txt` / `nonland.txt` in the session scratchpad.

Isshin: "If a creature attacking causes a triggered ability of a permanent you control to
trigger, that ability triggers an additional time."

## 1. The decision framework

- **R1 — The currency is ATTACK TRIGGERS.** Isshin doubles every trigger caused by a creature
  attacking — "whenever ~ attacks", "whenever a creature you control attacks", "whenever you
  attack" — on any permanent you control (creatures, enchantments, equipment, artifacts).
  Grade an attack-trigger card at TWICE its printed trigger. A card with no attack trigger is
  graded on its own merits only; it gets nothing from the commander.
- **R2 — Read the CADENCE.** "Whenever ~ attacks" = once per combat for that one creature.
  "Whenever a creature you control attacks" = once PER ATTACKER, so it scales with board
  width and Isshin doubles each one. "Whenever you attack" = once per combat. Per-attacker
  triggers on a wide board are the highest ceiling in the deck.
- **R3 — What Isshin does NOT double.** Combat-DAMAGE triggers ("deals combat damage to a
  player"), enters-the-battlefield triggers (including tokens created "tapped and attacking"
  — they never attacked), cast triggers, raid checks ("if you attacked this turn") and
  opponents' permanents. Exert, saddle and crew are costs, not triggers. A combat-damage card
  is graded as a normal card (Ninja/Rogue damage payoffs are fine, not doubled).
- **R4 — Extra combats multiply everything.** Every additional combat re-fires every attack
  trigger, doubled. An extra-combat card is graded on the trigger density it multiplies.
- **R5 — Attackers must be able to attack.** Triggers resolve on declaration, before blocks,
  so a small body attacking into a bigger board still pays — but only if it survives to
  attack next turn, or if the deck accepts trading it. Haste, evasion, menace and
  "can't block" effects are what keep the triggers firing on curve. Isshin himself is a 3/4
  and does NOT need to attack; he is the engine, so protecting him matters (Brawl commander
  tax {2} per recast).
- **R6 — Three colours, and the pile's manabase is two.** The pile's 23 lands (14 Swamp,
  Blood Crypt, Blazemire Verge, Dark Fortress, Razortrap Gorge, Temple of Malice, two
  Bloodfell Caves, two Boiling Rock Prison, Rakdos Guildgate) make NO white. Isshin needs
  {R}{W}{B}. Owned white duals in Historic Brawl: Nomad Outpost (RWB tri), Godless Shrine,
  Sacred Foundry, Scoured Barrens, Shattered Sanctum, Temple of Silence, Temple of Triumph,
  Bleachbone Verge, Sunbillow Verge, Insomnia Crown City, Misty Palms Oasis, Raucous Carnival,
  Sun-Blessed Peak, Abraded Bluffs, Wind-Scarred Crag, Dedicated Commons, Iron Hills,
  Rabanastre, Asgardian Citadel, Boros Guildgate, plus five-colour Starting Town / Mirage Mesa
  / Uncharted Haven / Crossroads Village. The manabase is a measured `consistency` question
  at draft time, not a pile verdict.
- **R7 — Colour identity is a HARD gate in Brawl.** Anything blue (Crucias, Tamiyo?) or
  green is illegal however payable. Check identity in the pull, not later.
- **R8 — The floor is scaled ×1.67 (100 cards).** A needs interaction 12 and interaction +
  card advantage 19; B needs 7 / 12. Card advantage that RIDES attack triggers ("whenever ~
  attacks, draw/impulse/treasure") counts twice as much in practice; grade it high.
- **R9 — Theft (the pile's second theme).** Tinybones, Black Cat, Ragavan, Vaan, Locke, Cruelclaw,
  Laughing Jasper Flint, Outrageous Robbery cast or exile opponents' cards. That is a
  card-advantage axis, not a separate engine — grade by how often it fires (an attack
  trigger that steals is doubled; a combat-damage one is not, R3).

## 2. Standing error list

- **E1 — "Deals combat damage" is not "attacks" (R3).** Most of the pile's black creatures
  (Tinybones, Black Widow, Reno and Rude, Cruelclaw, Shark Shredder, Jecht) pay on combat
  DAMAGE. Isshin does not double those. Grade them as ordinary evasive creatures.
- **E2 — A U/B HYBRID has blue identity.** Hama and Dream Harvest are payable with black
  mana but are ILLEGAL under an R/W/B commander (R7). Hybrid castability (G-58) is a 60-card
  rule; in Brawl, identity wins.
- **E3 — A doubled trigger is only worth twice when its effect STACKS.** Silver Sable's
  "gains lifelink" twice is lifelink once; Terra's trance is "at the beginning of combat",
  not an attack trigger. Count what the second resolution adds.
- **E4 — Keyword attack triggers live in REMINDER text.** Firebending ("whenever this creature
  attacks, add {R}"), exalted, battle cry, mobilize, melee, myriad, mentor, training are all
  attack triggers Isshin doubles, and a reminder-stripped sweep misses them (it missed Loyal
  Fire Sage). Sweep with `--regex-raw` or name the keywords. Corrected counts: pile **12**,
  owned Mardu Historic-Brawl pool **166**.

## 3. Cross-batch observations

- **O1 — The pile is not an Isshin pile yet (measured before batch 1).** A text sweep of all
  106 nonland cards finds **11** (12 after E4) that Isshin doubles (Raven Eagle, Djeru and Hazoret, Locke,
  Silver Sable, Far Fortune, Combustion Man, Stormforged Armor, Toralf's Disciple,
  Scalestorm Summoner, Imperial Blademaster, Raiyuu). Most of the rest is a black THEFT /
  HAND-ATTACK / outlaw shell. But the owned pool holds **137** Mardu Historic-Brawl cards with
  an attack trigger (`pool.py --regex 'whenever [^.]*attacks?|whenever you attack' --within
  RWB --legal "historic brawl" --owned`), so the commander's engine is buildable — the plan
  must pull those in from outside the pile, as the Ozai draft did with its duals.
- **O3 — Djeru and Hazoret wants LEGENDS.** Doubled, its attack looks at twelve cards and casts
  up to two legendary creatures free. The pile is legend-dense (Tinybones ×2, Black Widow,
  Reno and Rude, Cruelclaw, Jasper Flint, Shark Shredder, Jecht, Black Cat, Rakdos, Celes,
  Terra, Rankle, Akul, Locke, Zagras, Silver Sable…). Count legendary creatures at draft; at
  ~25 of 99 a twelve-card look finds ~3.
- **O2 — Hand attack is a real sub-theme** (Virus Beetle, Corrupt Court Official, Psychic
  Whorl, Ozai's Cruelty, Auntie's Sentence, Cruelclaw's Heist, Jecht's saga, Ninja of the
  Hand), and Tinybones, Bauble Burglar is its payoff. Report-only in the floor (G-25).

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

### Batch 1 (27)

| Card | Verdict | Note |
|---|---|---|
| Isshin | commander | — |
| Tinybones, the Pickpocket | ◇ | 1-drop deathtouch; combat-damage recast (E1) |
| Black Widow, Super Spy | ★ | menace 2-drop; combat-damage card advantage, not doubled |
| Reno and Rude | ◇ | menace 2-drop; damage impulse needs a sacrifice |
| Tinybones, Bauble Burglar | ◇ | payoff for the hand-attack sub-theme (O2) only |
| Deep-Cavern Bat | ★ | evasive lifelink 2-drop + hand disruption |
| Virus Beetle | △ | ETB discard body |
| Corrupt Court Official | △ | ETB discard body |
| Umbral Collar Zealot | △ | sac outlet, surveil |
| Sawblade Skinripper | △ | sacrifice deck card |
| Raven Eagle | ★★ | flier; ATTACK trigger doubled — two graveyard exiles, two Clues off creatures |
| Ninja of the Hand | △ | deathtouch 3-drop, late discard |
| The Infamous Cruelclaw | ★ | menace; free cast on damage (not doubled) — strong anyway |
| Laughing Jasper Flint | ★ | upkeep impulse X = outlaws; count outlaws at draft |
| Shark Shredder | ★ | first strike 4/4; reanimates on damage (enters attacking — no trigger) |
| Jecht // Braska's Final Aeon | ★ | menace 4/3; flips to a discard+draw ×2 / double-edict saga |
| Sothera, the Supervoid | ◇ | each of YOUR creatures dying = an edict; needs sac outlets |
| Black Cat, Cunning Thief | ★ | ETB: two cards from their top nine — card advantage 2 |
| Rakdos, the Muscle | ★★ | 6/5 flying trample for 5; sac → impulse; self-indestructible |
| Hama, the Bloodbender | ✗ | U/B hybrid — blue identity (E2) |
| Cruelclaw's Heist | ◇ | hand attack + steal; gift costs a card |
| Outrageous Robbery | ★ | instant X impulse from their library |
| Dream Harvest | ✗ | U/B hybrid — blue identity (E2) |
| Korvold and the Noble Thief | ◇ | two Treasures then impulse 3 |
| Auntie's Sentence | ◇ | cheap modal discard / -2/-2 |
| Psychic Whorl | △ | discard two; no Rats |
| Ozai's Cruelty | △ | discard two + 2 damage |

### Batch 2 (27)

| Card | Verdict | Note |
|---|---|---|
| Death in the Family | ★ | 2-mana instant exile, MV ≤3 |
| Epic Downfall | ★ | 2-mana exile, MV ≥3 (sorcery) |
| Long Goodbye | ★ | 2-mana instant, uncounterable, MV ≤3, hits walkers |
| Bitter Triumph | ★★ | 2-mana instant, unconditional creature/walker |
| Feed the Swarm | ★ | creature OR enchantment answer |
| Hero's Downfall | ★★ | 3-mana instant, unconditional creature/walker |
| Cruel Alliance | ◇ | teamwork taps your own attackers — fights the plan |
| Nowhere to Run | ★ | flash -3/-3; strips hexproof/ward |
| Phyrexian Arena | ★★ | a card every upkeep |
| Interdimensional Web Watch | ◇ | 2 impulse + exile-only mana |
| Celes, Rune Knight | ★★ | Mardu 4/4; ETB rummage-plus-one; team counters on graveyard entries |
| Terra, Herald of Hope | ★ | Mardu 3/3; flies each combat; reanimates on damage (beginning-of-combat, not doubled) |
| Djeru and Hazoret | ★★★ | ATTACK trigger doubled: two looks at six, up to two free legendary creatures (O3) |
| Hazoret's Monument | ◇ | red creature reducer + loot per creature cast |
| Hazoret the Fervent | ◇ | hellbent gate; discard ping |
| Hazoret, Godseeker | ◇ | makes a power-2 attacker unblockable; max-speed gate |
| Archon's Glory | △ | pump |
| Mabel, Valley Hero | ◇ | ETB counters |
| Panicked Bystander | △ | death lifegain |
| Oona's Blackguard | ◇ | Rogue counters + damage discard |
| Morbid Opportunist | ★ | draw on a death each turn |
| Rankle, Pitiless Trickster | ◇ | symmetric discard + edict ETB |
| Akul the Unrepentant | ★ | 5/5 flying trample for 4 |
| Locke, Treasure Hunter | ★★ | ATTACK trigger doubled: four mills, Treasures off lands, cast up to two spells |
| Zagras, Thief of Heartbeats | ◇ | 6-mana team deathtouch |
| Annex Sentry | ★ | removal on a body (W) |
| Silver Sable | ◇ | attack trigger doubles to nothing (E3) |

### Batch 3 (27)

| Card | Verdict | Note |
|---|---|---|
| Omenport Vigilante | ◇ | double strike after a crime (any targeted attack trigger counts) |
| Wild Pack Squad | △ | beginning-of-combat, not doubled |
| Boneyard Desecrator | △ | sac outlet body |
| Brimstone Roundup | △ | second-spell tokens — a spells-deck card |
| At Knifepoint | ◇ | outlaw first strike + a token per crime turn |
| Vial Smasher | ◇ | outlaw-ETB pings |
| Ertha Jo | △ | copies ACTIVATED abilities, not triggers |
| Far Fortune, End Boss | ★★ | "whenever you attack" doubled: 2 damage a combat, fills speed; max speed +1 to every hit |
| Form a Posse | ★ | X tokens = width for per-attacker triggers (R2) |
| All-Fates Stalker | ★ | O-ring on a body; warp |
| Olivia, Opulent Outlaw | ★★ | Mardu flying lifelink; Treasures on outlaw damage; team counters |
| Murderous Redcap | ★ | ETB 2 damage, persists for another |
| Combustion Man | ★★ | ATTACK trigger doubled: two "destroy a permanent or take 4" |
| Shoot the Sheriff | ◇ | 2-mana instant, non-outlaws only |
| Caught in the Crossfire | ◇ | modal sweeper; the outlaw half hits your own |
| Hellspur Posse Boss | ★ | outlaws gain haste; two tokens |
| Hellspur Brute | ◇ | outlaw affinity trampler |
| Outlaws' Merriment | ★ | a hasty attacker every upkeep (WW) |
| Ahn-Crop Invader | △ | |
| Chandra's Spitfire | △ | |
| Longhorn Sharpshooter | ◇ | plot for 2 damage |
| Loyal Fire Sage | ★ | firebending doubled = {R}{R} per attack (E4) |
| Molecular Modifier | △ | beginning-of-combat |
| Nahiri's Wrath | ◇ | discard-cost removal |
| Professional Face-Breaker | ★ | Treasures on damage + impulse sink |
| Pyre-Sledge Arsonist | △ | |
| Repercussion | ◇ | combo-ish damage redirect |

## 5. Consolidated plan (live)

- (after batch 4)
