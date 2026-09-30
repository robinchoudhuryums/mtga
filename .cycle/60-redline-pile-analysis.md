# Deck 60 (Redline) pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into
`decks/60-redline/deck.txt`'s `#: notes:`. A scratchpad, not a source of truth — decks/ are.

**Source list:** 67 cards from the owner, 2026-09-30 (chat). None are already in deck 60
(Alesha was proposed for it the same day). 11 carry a `*` in the owner's list; the star's
meaning was not stated, so it is recorded per row and does not move a grade.

**Required:** replace one Burnout Bashtronaut and one Far Fortune, End Boss (the owner holds
one of each; the repo still reads 0 — owned counts lag, G-10). Open to upgrading the other
2-ofs. Craft preference this session: owned, or common/uncommon crafts.

## 1. The decision framework (rules cited by number below)

- **F1 — The number that decides a card: does it make an opponent LOSE LIFE ON YOUR TURN,
  early and reliably?** Speed rises once per your turn when an opponent loses life, from any
  source (combat, ping, drain), and max speed (4) needs three ticks. Evasion, haste and
  noncombat pings on turns 2–4 score highest; a ground body with no evasion scores lowest.
- **F2 — Speed only exists once a "Start your engines!" permanent is out.** 33 of the 60
  carry it (incl. 2 Amonkhet Raceway). Trading engine cards for non-engine tickers is fine
  down to ~20, where P(an engine permanent by turn 3) is still ~99%.
- **F3 — Curve.** Aggro, avg MV 2.71, and only FOUR 1-drops. 1–3 drops are the tick layer;
  a 4+ drop must be a payoff or a hasty/evasive threat that ticks the turn it lands.
- **F4 — Castability.** 25 lands, B 13 / R 14 sources. {B}{R} on turn 2 is 78.8%, single
  pips ~86–88%; RR at 4 is 74% (Smaug), RRR and BBRR are real costs.
- **F5 — Legend rule.** A legendary add is a 1-of.
- **F6 — Vehicles are a PACKAGE question.** 23 creature copies, mostly power 1–3; a lone
  Vehicle with crew 2–3 costs an attack to turn on. Grade a Vehicle as part of a Vehicle
  shell, not singly (see §3).
- **F7 — Legality / availability.** Standard only (Chandra, Torch of Defiance is not).
  21 cards are **Reality Fracture (FRA), dated 2026-10-02** — not in `card-pool.csv` by
  design (G-79 `date<=now`), so no tool here scores them: graded from Scryfall text by hand.
  A deck line needs the set in the pool (`make refresh` after 10-02) or the card cataloged.
- **F8 — Noncombat damage is a real axis here.** Deck sources today: Gastal Thrillseeker
  ETB, Far Fortune's attack trigger, Lightning Strike, Outpace Oblivion's sacrifice. FRA adds
  payoffs keyed on "an opponent was dealt noncombat damage this turn" — count sources first.
- **F9 — Slots.** Required: 1 Bashtronaut (a 1-drop slot), 1 Far Fortune (a 4-drop slot).
  Soft: Endrider Catalyzer ×2 (3/1, nothing until max speed), Gastal Raider ×2 (2/1 for 3),
  Goblin/Mutant Surveyor ×4 (ground 3-drops), Streaking Oilgorger ×2 (5-drop). Keep:
  Thrillseeker, Momentum Breaker, Outpace Oblivion, Lightning Strike, Kickoff Celebrations
  (the discard outlet), Hour of Victory (tutors The Speed Demon), Gas Guzzler; `#: protect:`.

## 2. Standing error list
- **The repo's owned count for Burnout Bashtronaut and Far Fortune reads 0**; the owner holds
  one of each. Treat every `own=` column as a lower bound (G-10), never as a reason.
## 3. Cross-batch observations
- **VEHICLE / PILOT CLUSTER (batch 1): 17 cards** — The Last Ride, Tundra Tank, The Fire
  Nation Drill, War Balloon, Apocalypse Runner, Spire Mechcycle, Chandra Spark Hunter,
  Reckless Velocitaur, Deathless Pilot, Dynamite Diver, Calamity, Dracosaur Auxiliary, Push
  the Limit, Road Rage, Rocky Roads, Foul Roads, Adrenaline Jockey (exhaust). Each is weak
  alone in deck 60 for the same reason (F6), which is the variant signal the skill warns about:
  a Rakdos Vehicles build is a different deck, not a pile of cuts. Chandra, Spark Hunter is the
  exception — she brings her own Vehicle and animates it, so she works without the shell.
- **The owned pool already covers both required slots**, and several 2-drop/3-drop tickers
  (Hawkeye, Speed, Black Widow, Cruelclaw, Alesha) beat the soft 2-ofs on F1 outright.
- **FRA is a NONCOMBAT PING package, and that is deck 60's own axis (F1, F8).** Voxmancer
  (every upkeep), Koth (every land), Screeching Soulbreaker (every attack), Tinybones (ETB),
  Stingerquill Charm and Cast Away Doubt all make an opponent lose life without connecting in
  combat — the one failure mode an aggro speed deck has (a stalled board). Unlike the Vehicle
  cluster, these fold straight into deck 60 rather than asking for a variant.
- **Availability gate (F7):** the FRA picks cannot be written to the deck file until FRA is in
  the pool (after 2026-10-02, `make refresh`) or the cards are cataloged as owned. The owned
  plan in §5 stands on its own today; the FRA picks are a second wave.

## 4. Running verdicts

### Batch 1 — the 46 cards the pool holds (read in full, 2026-09-30)

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out. `own` = repo count.

| Card | Cost | own | Verdict | Grounds (operative clause, framework rule) |
|---|---|---|---|---|
| Hawkeye, Master Marksman | {1}{R} | 1 | ★★★ | "Whenever Hawkeye becomes tapped, you may pay {1}… Explosive — deals 2 damage to target player": attacking IS the tick, blocked or not (F1). 2-drop, legend (F5). |
| The Infamous Cruelclaw | {1}{B}{R} | 1 | ★★★ | 3/3 menace; combat damage → cast the next nonland card free by discarding. Evasive 3-drop that snowballs (F1, F3). |
| Speed, Young Avenger | {1}{R} | 1 | ★★ | "Haste" 2-drop ticks the turn it lands; noncreature spell + {1}: a haste creature can't be blocked except by haste. Deck casts 12 noncreature spells. |
| Alesha, Who Laughs at Fate | {1}{B}{R} | 1 | ★★ | First strike, grows each attack, "return target creature card with MV ≤ Alesha's power" every end step you attacked — rebuys Thrillseeker's ping. |
| Black Widow, Super Spy | {1}{B} | 1 | ★★ | 2/1 menace 2-drop; combat damage → free card or +1/+1. Evasive and value (F1). Mythic, owned. |
| The Ruinous Wrecking Crew | {X}{B}{R} | 1 | ★★ | X=1: 3/3 + "target opponent loses 2 life" (a tick); X=2 adds an edict. Scales into a 4-drop slot (F9). |
| Chandra, Spark Hunter | {3}{R} | 1 | ★★ | "0: Create a 3/2 … Vehicle token", then "at the beginning of combat… it becomes an artifact creature and gains haste" — a 3-power hasty attacker the turn she lands, every turn; +2 loots. Single R (F4). Far Fortune slot. |
| Ninja Teen | {2}{B} | 1 | ★★ | "Whenever a creature you control leaves the battlefield, each opponent loses 1 life" (tick on trades/sacs); Level 2 "+1/+0 and menace" to the team. Slow (5 mana to level 2). |
| Realm of Koh | land | 1 | ★★ | A Swamp that is untapped with a basic out, plus "{3}{B}, {T}: 1/1 Spirit… can't block or be blocked by non-Spirit" — an evasive ticker from a land slot. |
| Lightning, Security Sergeant | {2}{R} | 1 | ★ | 2/3 menace; combat damage → impulse card. Evasive 3-drop with card flow. |
| Vindictive Warden | {2}{B/R} | 1 | ★ | Hybrid 2/3 menace, firebending 1, "{3}: 1 damage to each opponent" — a guaranteed tick sink late (F1, F8). |
| Shriek, Treblemaker | {2}{B/R} | 1 | ★ | Discard → "target creature can't block"; opponent creature dies → 1 damage (tick with removal). Discard feeds nothing else here. |
| Jet's Brainwashing | {R} | 1 | ★ | "Target creature can't block" + a Clue for 1 mana; kicked, a threaten. Makes an attack connect (F1). |
| Road Rage `*` | {R} | 1 | ★ | 1-mana instant, "2 plus the number of Mounts and Vehicles" damage. Cheap removal at 2; better in a Vehicle shell (F6). |
| The Fire Nation Drill `*` | {2}{B}{B} | 0 | ★ | Enters → tap it → "destroy target creature with power 4 or less"; then a 6/3 trample Vehicle (crew 2). BB at 4 and a rare craft. |
| My Precious | {3} | 1 | ◇ | "hexproof and can't be blocked" on a creature — the deck's only protection answer (protection 1) — but 3 + equip {2} and 2 life is slow for aggro. |
| Underfoot Underdogs | {2}{R} | 0 | ◇ | 1/2 + a 1/1 Goblin; "{1}, {T}: power ≤2 creature can't be blocked". Enabler, weak bodies; common craft. |
| Apocalypse Runner | {2}{B}{R} | 0 | ◇ | "{T}: power ≤2 creature … can't be blocked" works uncrewed — an unblockable engine for Bashtronaut/Guzzler. Crew 3 for the 6/5 is hard (F6). |
| The Last Ride | {B} | 1 | ◇ | Repeatable "{2}{B}, Pay 2 life: Draw a card". Card flow, but the body is dead above 12 life in aggro. |
| Tundra Tank | {2}{B} | 1 | ◇ | 4/4 Vehicle, crew 1, ETB indestructible trick. Ground body, no tick of its own (F6). |
| War Balloon `*` | {2}{R} | 1 | ◇ | 4/3 flier but crew 3, or three {1} fire counters to become a creature. Slow (F6). |
| Dynamite Diver | {R} | 0 | ◇ | 1-drop; "when this creature dies, it deals 1 damage to any target". A tick on a trade; pilot text is Vehicle-only. Common craft. |
| Brambleback Brute | {2}{R} | 1 | ◇ | 2/3 that grows; "target creature can't block" as a sorcery. Enabler, not a ticker. |
| Goblin Negotiation | {X}{R}{R} | 1 | ◇ | Scaling removal + Goblins from excess; RR (F4). |
| Adrenaline Jockey `*` | {2}{R} | 0 | ◇ | 3/3; punishes off-turn spells for 4. Meta-dependent. |
| Garrison Excavator | {3}{R} | 1 | ◇ | 3/4 menace; cards leaving your graveyard → 2/2 Spirit. The Surveyors exile themselves — synergy, but a 4-drop. |
| Arnim Zola, Bio-Fanatic | {2}{B} | 1 | △ | Token maker needs two creature cards in the yard and {3} a turn. Slow. |
| Reno and Rude | {1}{B} | 0 | ◇ | 2/1 menace, card theft on hit. Black Widow does this job, owned. |
| Fated Firepower | {X}{R}{R}{R} | 1 | △ | +X to every source — but RRR on 14 red sources (F4). |
| Coalstoke Gearhulk `*` | {1}{B}{B}{R}{R} | 1 | △ | 5/4 menace deathtouch + reanimate MV ≤4. BBRR (F4). |
| Dracosaur Auxiliary `*` | {4}{R}{R} | 1 | △ | 6-drop flier; saddle 3 for the ping. Above the curve (F3). |
| Calamity, Galloping Inferno | {4}{R}{R} | 1 | △ | 6-drop Mount. (F3, F6) |
| Fear of Burning Alive | {4}{R}{R} | 0 | △ | "deals 4 damage to each opponent" on ETB — reach, but a 6-drop (F3). |
| Spider-Man Noir | {4}{B} | 1 | △ | Rewards attacking ALONE — the deck goes wide (shape: WIDE). |
| June, Bounty Hunter | {1}{B} | 1 | △ | Unblockable only after drawing two in a turn — rare before max speed. |
| Hog-Monkey | {2}{B} | 1 | △ | Menace for a creature with a +1/+1 counter; few counters here. |
| Alien Symbiosis | {1}{B} | 1 | △ | Aura +1/+1 menace; card disadvantage into removal. |
| Along the Crooked Way | {2}{B} | 1 | △ | Regrowth + amass Goblins; no tick. |
| Yathan Tombguard | {2}{B} | 0 | △ | Draw needs creatures with counters (few). |
| Deathless Pilot | {1}{B} | 1 | △ | Recursive 2/2; crew text is Vehicle-only (F6). |
| Reckless Velocitaur | {3}{R} | 1 | △ | Only does anything crewing (F6). |
| Spire Mechcycle | {4}{R} | 0 | △ | Vehicle payoff (F6). |
| Rocky Roads / Foul Roads | lands | 2 / 0 | △ | Untapped only with a Vehicle or Mount out (F6). |
| Push the Limit | {5}{R}{R} | 1 | ✗ | 7 mana (F3). |
| Chandra, Torch of Defiance | {2}{R}{R} | 0 | ✗ | Not Standard-legal (F7). |
### Batch 2 — the 21 Reality Fracture (FRA) cards, from Scryfall text (F7)

None is in the repo yet, so `own` is unknown and no tool has scored them.

| Card | Cost | Verdict | Grounds |
|---|---|---|---|
| Stingerquill Voxmancer // Vicious Verse | {B/R} // {B/R} | ★★★ | Hybrid 1-drop Goblin; "at the beginning of your upkeep, if this creature isn't prepared, it becomes prepared" and Verse "deals 1 damage to target opponent" — a guaranteed tick EVERY turn from turn 2 for {B/R}, blockers irrelevant (F1). The Bashtronaut slot's natural heir (F9). Noncombat, so it also switches on the F8 payoffs. |
| Koth, the Geomancer | {2}{R} | ★★★ | "Landfall — whenever a land you control enters, Koth deals 1 damage to each opponent" — every land drop from turn 3 is a tick; "if that land is a Mountain, add {R}" (10 Mountains). Legend (F5). |
| Samut, Hazoret's Champion | {1}{R} | ★★ | "Creatures you control have haste" — every later creature ticks the turn it lands (F1). Gas Guzzler still enters tapped. Legend, rare. |
| Screeching Soulbreaker | {2}{B} | ★★ | 1/4 flier; "whenever this creature attacks, it deals 1 damage to each opponent and you gain 1 life" — the tick fires on the ATTACK, blocked or not. Common. A Surveyor's slot. |
| Stingerquill Charm | {B}{R} | ★★ | "3 damage to any target" / first strike + deathtouch / a 2/2 hasty Cadet. Lightning Strike with two more modes; {B}{R} on turn 2 is 78.8% (F4). |
| Tinybones, Pocket Nuisance | {2}{B} | ★ | ETB "each opponent discards a card", and "whenever a player discards… 1 damage to each opponent" — so the ETB itself ticks; Kickoff Celebrations and Bitter Triumph discard for more. 2/1 body. Legend. |
| Gallia, the Merrymaker | {1}{R} | ★ | Haste 2/1 2-drop (a tick the turn it lands); counter-haste is narrow here. Legend. |
| Cast Away Doubt | {2}{B} | ★ | "Draw two cards… deals 2 damage to each player" — card advantage (deck reads 4) plus a tick. Common. |
| Whiplash Wordsmith // Vicious Verse | {3}{B/R} | ★ | "Enters prepared", and "as long as an opponent was dealt noncombat damage this turn, this creature has flying and haste": with any ping that turn it is a hasty 3/3 flier for 4. Beats Streaking Oilgorger (5 MV 3/3 flying haste). Common. |
| Extended Absence | {3}{B} | ◇ | Instant exile + 1 damage. Good removal at 4 MV; the deck's removal sits at 2–3. |
| Tomik, Izzet Sparkmage | {1}{R} | ◇ | "Noncombat damage… plus 1" — Far Fortune's amp for pings only. A payoff that needs the ping package first (F8). |
| Grim Repriser | {B}{R} | ◇ | 2/2 prowess that returns for {B}{R} if an opponent took noncombat damage this turn (F8). |
| Gideon the Oathless | {2}{B} | ◇ | 3/3, "Ward—Discard a card"; its pings trigger on THEIR creatures entering — mostly the opponent's turn, which does not tick (F1). |
| Tetsuko Umezawa, Pursuer | {3}{R} | ◇ | 2/4 double strike, prowess. A 4-drop with no evasion. |
| Winter, Tormented Loner | {2}{B} | ◇ | Sacrifice → edict; 0/3 that grows with your yard. |
| Garruk, Veiled Butcher | {3}{B}{B} | ◇ | Strong planeswalker (−4/−1, edict + 4/4, discard two) but BB at 5, above the curve (F3, F4). |
| Massacre Girl, Most Wanted | {4}{B} | △ | 5-drop drain/counters payoff (F3). |
| Liliana the Repentant | {1}{B} | △ | Mills you on creatures entering; exhaust reanimation at {5}{B}. No tick. |
| Danitha, Spear of Agony | {2}{B} | △ | Counters when you target their stuff; 2/2 first strike. |
| Jiang Yanggu, Alone | {4}{R} | △ | Rewards attacking alone in a wide deck. |
| Pyre Rhymer // Molten Tide | {1}{R}{R} | △ | RR 3-drop ramp (F4). |

## 5. Consolidated plan (live)
