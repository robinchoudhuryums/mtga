# Deck 60 (Redline) pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into
`decks/60-redline/deck.txt`'s `#: notes:`. A scratchpad, not a source of truth — decks/ are.

**Source list:** 67 cards from the owner, 2026-09-30 (chat). None are already in deck 60
(Alesha was proposed for it the same day). 11 carry a `*`: the owner's mark for "especially worth consideration, or re-read if
dismissed" (clarified 2026-09-30) — re-read in §4b.

**Required:** replace one Burnout Bashtronaut and one Far Fortune, End Boss (the owner holds
one of each; the repo still reads 0 — owned counts lag, G-10). Open to upgrading ONE copy of
each other 2-of (clarified), plus any swap the pile justifies. Craft preference: owned, or
common/uncommon crafts. **The 21 Reality Fracture cards are OWNED and playable on Arena now**
(owner, 2026-09-30) — Arena released the set before Scryfall's 2026-10-02 date.

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

### 4b. Re-read of the starred cards (owner's `*`)

| Card | Was | Now | What changed on the re-read (a count, per G-61) |
|---|---|---|---|
| Koth, the Geomancer | ★★★ | ★★★ | Unchanged: 25 lands, a tick per land drop from turn 3. |
| The Fire Nation Drill | ★ | ★★ | Chandra, Spark Hunter animates "one target Vehicle you control… gains haste" each combat, so with her the Drill needs no crew; alone it is still a 4-mana kill spell (power ≤4) that leaves a 6/3 trampler. The Far Fortune slot's removal option. Rare, repo reads unowned. |
| War Balloon | ◇ | ★ | "{1}: Put a fire counter" is instant-speed and permanent: cast turn 3, pay {3} on turn 4 and it is a 4/3 flier that never needs crew — 4 flying power a turn earlier than Streaking Oilgorger's 3. Owned. |
| Adrenaline Jockey | ◇ | ★ | "Whenever a player casts a spell, if it's not their turn, deals 4 damage to them" — an opponent's removal in YOUR combat costs them 4, on your turn: a tick and a tax. A 3/3 for 3 over a Surveyor. It hits you too, so cast your instants on your own turn. |
| Tomik, Izzet Sparkmage | ◇ | ★ | With the ping package in, "noncombat damage… plus 1" upgrades Voxmancer, Koth, Soulbreaker, Thrillseeker, Hawkeye, Lightning Strike and Outpace Oblivion — Far Fortune's max-speed amp for pings, online from turn 2. Payoff only; 1/2 body. |
| Tinybones, Pocket Nuisance | ★ | ★ | Discard sources counted: Kickoff Celebrations ×2, Bitter Triumph, Hawkeye's Boomerang, its own ETB. Real, 2/1 body. |
| Road Rage | ★ | ★ | 1-mana removal at 2; with Chandra's token or a Drill out, 3–4. |
| Dracosaur Auxiliary | △ | ◇ | A hasty 4/4 flier is a tick on arrival and saddle 3 adds a 2-damage ping; the problem is only the 6th mana — Whiplash Wordsmith does the job at 4. |
| Coalstoke Gearhulk | △ | ◇ | Its ETB reanimates a MV ≤4 creature from ANY graveyard with haste — a tick the turn it lands, and a second Thrillseeker ping. Held back by {B}{B}{R}{R} on 13 B / 14 R. |
| Massacre Girl, Most Wanted | △ | ◇ | Every trade pings, and every ping grows her; a 5-drop with no evasion. |
| Tetsuko Umezawa, Pursuer | ◇ | ◇ | A 2/4 double striker with no evasion; its ping needs THEIR small blockers. |

## 5. Consolidated plan (live) — REVISED 2026-09-30: one copy per 2-of, FRA owned

| # | Out (1 copy) | In | Grounds |
|---|---|---|---|
| 1 | Burnout Bashtronaut (required) | Stingerquill Voxmancer | A tick every turn for {B/R}; hybrid 1-drop Goblin (F1, F3). |
| 2 | Far Fortune (required) | Chandra, Spark Hunter | A hasty 3-power attacker every turn she is out; single R. Alt: The Fire Nation Drill `*` (removal + trampler; rare, repo reads unowned). |
| 3 | Endrider Catalyzer | Hawkeye, Master Marksman | 2 damage to a player every attack, blocked or not. |
| 4 | Gastal Raider | The Infamous Cruelclaw | Menace 3/3, free spells on hit. |
| 5 | Goblin Surveyor | Koth, the Geomancer `*` | A tick per land drop. |
| 6 | Mutant Surveyor | Screeching Soulbreaker | Flier; pings on every attack. |
| 7 | Streaking Oilgorger | Whiplash Wordsmith | Enters prepared, so its own Verse turns on flying + haste: a 3/3 hasty flier for 4 (+1). Alt: War Balloon `*` (owned). |
| 8 | Swamp | Realm of Koh | Same source; evasive token sink. |
| opt | Lightning Strike | Stingerquill Charm | Same 3 damage + two modes; {B}{R} on turn 2 is 78.8% vs Strike's ~90% — a castability cost. |
| opt | Hour of Victory | Samut, Hazoret's Champion | Team haste; keeps the other Hour as The Speed Demon's tutor. |
| opt | Kickoff Celebrations | Tomik, Izzet Sparkmage `*` | Ping amplifier once 1–7 are in; the other Kickoff stays as the discard outlet. |

**Measured in a sandbox copy with the FRA cards injected from Scryfall (rows 1–8):** floor
A → A; interaction 8 → 9; card advantage 4 → 5; avg MV 2.71 → 2.69; curve 4/13/11/4/3; B 13 /
R 14 and keepable 86.0% unchanged; every FRA add ≥90% on curve, Cruelclaw 84.0%, Hawkeye
89.8%. Engine cards 33 → 26 (F2). **With both optional Charm and Samut:** avg MV 2.66, board
power 61, Charm 78.8% on turn 2.

**Wave-1 alternates superseded:** Gingerbrute (Voxmancer does the job), Speed / Alesha /
Black Widow (still ★★, but the one-copy rule leaves no slot without cutting a 1-of — they
are the first reserves if a cut above disappoints).


### Status 2026-09-30 (owner's picks)

- **APPLIED (part A, commit c45187e):** Chandra for a Far Fortune, Hawkeye for an Endrider
  Catalyzer, Cruelclaw for a Gastal Raider, Realm of Koh for a Swamp.
- **PENDING (part B, after FRA reaches the pool):** Voxmancer for a Bashtronaut, Koth for a
  Goblin Surveyor, Soulbreaker for a Mutant Surveyor, Wordsmith for an Oilgorger, Samut for an
  Hour of Victory. Recorded in the deck's `#: notes:` too. The owner plays the full list on
  Arena now (import block built in the sandbox).
- **APPLIED (round 2):** The Fire Nation Drill for Endrider Spikespitter, Road Rage for a
  Kickoff Celebrations, Adrenaline Jockey for a Gastal Thrillseeker, Dracosaur Auxiliary for
  an Outpace Oblivion. Quality guard: card advantage 5 to 3 (soft; accepted by the owner's
  pick). Floor still A, aggro clock 5/7. Jockey added to the wishlist (Target 60); the Drill
  was already there (Target 14).
- **PENDING (part B, extended):** Massacre Girl, Most Wanted for the second Mutant Surveyor,
  Tetsuko Umezawa, Pursuer for the second Goblin Surveyor, Tomik, Izzet Sparkmage for the last
  Endrider Catalyzer, Tinybones, Pocket Nuisance for a Gas Guzzler. All FRA; they join the
  five above.
- **Not taken:** War Balloon, Coalstoke Gearhulk.

### Cut candidates for the ten (against the full part-A+B list; measured in the sandbox)

The full list holds 25 engine cards; nearly every cut candidate is one (F2). Taking all ten
on their primary cuts leaves 15 — P(an engine permanent by turn 3) 99.5% → 94.0%.

**Top-end reading:** the list already runs 7 cards at 4+ (Far Fortune, Chandra, Spikespitter,
Wordsmith; The Speed Demon, Necroregent, Oilgorger). Three of those — Spikespitter,
Necroregent, Oilgorger — do little before max speed, so the fix is to UPGRADE those slots,
not add more: Drill / Gearhulk / Dracosaur on them keeps the curve (avg MV 2.66 → 2.69),
interaction 9 → 11, protection 1 → 2 (the Drill strips hexproof/indestructible), engine
cards 25 → 22. Costs: Drill {B}{B} 69.6% on turn 4, Gearhulk {B}{B}{R}{R} 59.8% on turn 5,
Dracosaur {R}{R} 79.5% by turn 5 (13 B / 14 R sources).

| Add | Cut candidates (primary first) |
|---|---|
| The Fire Nation Drill | Endrider Spikespitter · Momentum Breaker (1) · Bitter Triumph |
| Coalstoke Gearhulk | Risen Necroregent · Streaking Oilgorger (last) |
| Dracosaur Auxiliary | Streaking Oilgorger (last) · Risen Necroregent · Endrider Spikespitter |
| Massacre Girl, Most Wanted | Risen Necroregent · Mutant Surveyor (last) · Streaking Oilgorger (last) |
| Tetsuko Umezawa, Pursuer | Endrider Spikespitter · Goblin Surveyor (last) · Howlsquad Heavy |
| Tinybones, Pocket Nuisance | Gastal Raider (last) · Mutant Surveyor (last) · Goblin Surveyor (last) |
| Tomik, Izzet Sparkmage | Endrider Catalyzer (last) · Kickoff Celebrations (1) |
| Road Rage | Momentum Breaker (1) · Bitter Triumph · Heartless Act |
| Adrenaline Jockey | Goblin Surveyor (last) · Mutant Surveyor (last) · Gastal Raider (last) |
| War Balloon | Streaking Oilgorger (last) · Kickoff Celebrations (1) · Mutant Surveyor (last) |

### Repo availability (F7)

FRA is on Arena now but not in `card-pool.csv` (Scryfall dates it 2026-10-02; the pool's
`date<=now` gate). Cataloging it as owned before the pool holds it would fail INV-01b, and a
deck line would fail INV-04. After 2026-10-02: `make refresh REFETCH=1` (the pool is reused
for 7 days otherwise), then catalog the owned FRA cards (`/ingest`), then apply rows 1, 5–7.
Rows 2–4 and 8 can land today. **Tooling notes for that ingest:** `prepared` is a new keyword
the tagger does not index (Voxmancer and Wordsmith screen as "tangential" because their
Verse half reads as no role), and the `date<=now` gate lags Arena's early digital release —
both worth a triage pass when FRA lands.

### Protect — what the ranking cannot see

`cuts` ranks the removal as weakest fit (theme term), so it must not drive these cuts. Keep:
Gas Guzzler, Hazoret, the remaining Far Fortune, The Speed Demon (header); Kickoff
Celebrations (discard outlet); Hour of Victory (tutors The Speed Demon); Gastal Thrillseeker.

### Variant parked

A Rakdos Vehicles build (§3); War Balloon and The Fire Nation Drill would anchor it.
