# Deck 78 "Team Avatar" — 72-card pile analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into
`decks/78-team-avatar/deck.txt`'s `#: notes:`. A scratchpad, not a source of truth —
`decks/` is.

**Source list:** 72 names supplied by the user 2026-08-31. **0 are already in deck 78.**
Five needed name repair before they resolved, all `Front // Back` cards (G-63/G-02):
Virtue of Loyalty, both Aangs, Zanarkand and Fuss//Bother. **A name that does not resolve
is a name to fix, not a card to drop.**

**Unexplained marker:** the user starred five entries — Earth King's Lieutenant,
Starry-Eyed Skyrider, Okoye Dora Milaje Leader, Starfield Vocalist, Sandstorm Salvager.
Meaning unknown; check against ownership in batch 1 and ASK if it does not correlate.

## 1. The decision framework

**R1 — THE DECIDING QUESTION IS "DOES A DOUBLER SEE IT?"** This deck's whole thesis is
trigger multiplication. Katara, the Fearless doubles a triggered ability of an **Ally**;
Delney, Streetwise Lookout doubles a triggered ability of a creature with **power 2 or
less**. Neither touches a STATIC ability, an ACTIVATED ability, or a spell's own
resolution. So a card's worth here is `base × (1 + doublers that see it)`, and the same
effect is worth 1×, 2× or 3× depending only on where it is printed. Grade every card
against this first. A big static anthem and a small ETB trigger can swap places.

**R2 — POWER 2 IS A RESOURCE THIS DECK SPENDS ON ITSELF.** 14 of 22 trigger-holding
creature copies are power ≤2, but TEN sit at exactly 2 — one +1/+1 from falling out of
Delney's range. White Lotus Reinforcements, Suki Courageous Rescuer and United Front all
push them out. Any pump/anthem candidate must be priced against that, not just its stats.

**R3 — CASTABILITY IS THE PRINTED COST AGAINST W 13 / U 8 / G 8 on 24 lands.** Measured
cast-on-curve: mono-W 1-pip ~82–89%, `{W}{W}` 56–63%, single U or G ~70–75%, `{G}{W}{U}`
**~51%**. Colorless is free. Four land configurations were tried and Katara moved only
50.5–54.2%, so this is structural — 28 W pips against 10 G and 5 U. **Cite R3 by number
for any cost-based rejection, and never reject on identity alone (G-58).**

**R4 — WHAT THE DECK IS SHORT OF vs LONG ON.** Live vector 2026-08-31 (post-Delney):
interaction **7** (3 unclassified) · card advantage **4** · protection **2** · avg MV
**3.06** · early drops **13 (1 mana source)** · 27 creature copies · WIDE 17 / TALL 2.
SHORT: protection, card advantage, answers to a noncreature permanent (the classifier
says 0; the real figure is 2 — Earth Kingdom Jailer and Aang). LONG: bodies, Ally-token
makers (10), Ally-ETB triggers (19).

**R5 — COUNTS TO HAND, so nothing is dismissed by category (G-61/G-59/K-13).**
26 Ally copies · 24 Human · 19 ETB triggers · 10 Ally-token makers · 4 airbend · 4
earthbend · 9 noncreature spells · 1 Clue source · 1 Equipment · 6 Plains · **0 Lessons**
· **0 artifacts to sacrifice beyond Clues**. Several TLA cards key on Lessons — that
clause is DEAD here and has already fooled `screen` into four KEY labels.

**R6 — THE TOOLS ARE BLIND TO THIS DECK'S BEST CARDS.** A trigger-doubler has no role
bucket, so Katara, Delney, Kyoshi Warriors and Jeong Jeong's Deserters are all baselined
ZERO-ROLE. `screen` saturated at 100% KEY on the last 16-card pile and said so itself.
Read text; treat `cuts`/`screen` order as a hint and their labels as noise.

**R7 — G-42 WATCHLIST for this deck (a good card that fights the engine).**
(a) anthems vs Delney, per R2;
(b) airbending your own Earth Kingdom Jailer or Sheltered by Ghosts RETURNS the
    opponent's exiled permanent — 4 airbend effects make this misplay available;
(c) tapping creatures for mana (Great Divide Guide, convoke, waterbend) competes with
    attacking — only the 4 vigilance bodies do both.

## 2a. TOOLING HOLE FOUND WHILE GRADING (Stage 4) — not fixed here
**`_ROLE_PATTERNS["Removal (spot)"]` misses a PLURAL-SUBJECT fight effect.** All three
damage-equal-to-power patterns are written `deals damage` (singular). **Allies at Last**
reads *"Up to two target creatures you control each **deal** damage equal to their power
to target creature an opponent controls"* and scores `['Cost reduction / cheat']` — the
affinity clause matches, the removal does not. Verified: Rabid Bite classifies fine, and
an "its power / you don't control" rewrite of Allies at Last still fails, so the plural
VERB is the break, not the targeting language. Consequence: **every interaction figure in
the plan below reads one LOWER than the truth.** Left unfixed on purpose — a pattern widen
costs a roster-wide `#: tier:` prose sweep (K-12), so batch it with any others.

## 2b. CORRECTIONS — six verdicts overturned on a user-prompted re-read (2026-09-01)
1. **Jet, Freedom Fighter — I made the exact error G-58 documents.** Cost is
   `{2}{R/W}{R/W}{R/W}`, payable as `{2}{W}{W}{W}`. I printed that cost in my own batch-1
   pull and binned the card anyway off the `Color(s)` identity column. `deck.py screen`
   says it outright: *"identity has R (hybrid — paid on-color)"*. **Never bin on identity;
   R3 says read the printed cost.** Re-graded ★★★ — an Ally whose ETB deals damage equal
   to your creature count, DOUBLED by Katara.
2. **Pinnacle Starcage — overstated.** I called it actively harmful without reading the
   second ability. It exiles only **6 nontoken cards** here, all MV 2, and NONE of the
   three doublers (MV 3/3/4); and `{6}{W}{W}` turns every exiled CARD — theirs included —
   into a 2/2 Robot under YOUR control. The real objection is narrower: your TOKENS are
   MV 0, cease to exist on exile, and yield no Robot. ✗ → ◇.
3. **The Eagles Are Coming! — the miss that matters.** A token returned to hand ceases to
   exist but still counts as "returned to your hand this way", so **each of your 1/1 Ally
   tokens becomes a 4/4 flier**, and nontoken creatures return to be recast (re-triggering
   ETBs). 10 token makers in the deck. The 4/4s also satisfy The Earth King. ◇ → ★★★.
4. **Sheriff of Safe Passage — Plot is the point.** Casting from exile triggers **Appa,
   Steadfast Guardian** (a 1/1 Ally token), and FOUR cards here care about exile-casting.
   Plot for `{1}{W}` on turn 2, cast free later as a 9/9. ★ → ★★★.
5. **Shang-Chi — the Great Divide Guide line.** Guide gives every land AND Ally
   `{T}: Add one mana of any color`; Shang-Chi removes summoning sickness from those
   abilities, so every Ally taps the turn it lands. ★ → ★★.
6. **The Queen of Dale / Ant-Man / Oko — all under-read.** Queen is power 2, so Delney
   doubles it: two recruits per opponent turn, feeding Belladonna Took. Ant-Man's "once
   each turn" cap is on the TOKEN half only; Delney doubles the attack trigger. Oko was
   dismissed BY CATEGORY (rule 6 of this skill, violated): his −5 copies every other
   nonland permanent, which on this board wins.

## 2. Standing error list
- (seed) Do NOT grade a TLA card's Lesson clause as live. Zero Lessons in the deck. R5.
- (seed) Do NOT read `Color(s)` as castability. G-58. Use the printed cost, R3.
- (seed) Do NOT trust a zero-result literal type search. Search the effect shape. K-13 —
  it already turned up 18 choose-a-creature-type lords invisible to an "Ally" search.

## 3. Cross-batch observations
- (open) Two latent sub-engines are underbuilt and could absorb adds: **airbend/recast**
  (4 sources, 19 ETBs) and **earthbend/land-creatures** (4 sources; feeds Toph, The Earth
  King's power-4 gate, and Delney's evasion band).

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`

### Batch 1 (1–24)
| card | v | note (R# = framework rule) |
|---|---|---|
| Aang, at the Crossroads // Destined Savior | ★★★ | OWNED. Ally, so Katara doubles the ETB: **two** free creatures MV≤4 off the top 5. Back face is the earthbend axis (earthbend 2 every combat + vigilance for land creatures). Cost {2}{G}{W}{U} is R3's worst band. |
| Bard, King of Dale | ★★★ | OWNED. **Token doubler + extra-draw doubler** in one card — a replacement effect, so it stacks with the trigger doublers rather than competing. 10 token makers, and it doubles South Pole Voyager's draws. MV 6 is the cost. |
| Belladonna Took | ★★★ | OWNED. South Pole Voyager's shape for TOKENS and it escalates to three (life → draw → counters on each creature). Power 2, so **Delney doubles it**; Katara does not (not an Ally). |
| Sally Pride, Lioness Leader | ★★★ | OWNED. ETB X 2/2s where X = nontoken creatures; attacks → counter on each creature. **Power 2, so Delney doubles BOTH triggers.** |
| Earth King's Lieutenant | ★★★ | craft R. Power 1 + Ally = the only card in the pile **both** doublers see on **both** triggers. Caveat R2: its counters push the team out of Delney's range. |
| Captain America, Living Legend | ★★ | OWNED. Untaps each creature the first time it taps each turn = board-wide pseudo-vigilance, and with Great Divide Guide every Ally taps for mana **twice**. No doubler sees it (Hero, power 3). |
| Rally the Monastery | ★★ | OWNED ×2. The third mode **destroys a creature with power 4+** — R4 says interaction is the short axis. Costs {2} less after a first spell. |
| Moogles' Valor | ★★ | craft R. Instant: a 1/2 lifelink token per creature, then indestructible. Mass token + anti-sweeper in one. |
| Virtue of Loyalty // Ardenvale Fealty | ★★ | OWNED. Adventure token first, enchantment later: counters on each creature **and untaps them** each end step. R2 tension. |
| Felidar Retreat | ★★ | craft R. Landfall, and **earthbent lands returning ("when it dies or is exiled, return it") are land drops** — a connection neither card advertises. |
| Antiquities on the Loose | ★ | OWNED. Two 2/2s with flashback. Plain but recurring. |
| The Eagles Are Coming! | ◇ | OWNED. Bounces your own creatures (re-triggers ETBs, feeds Suki's leaves-play) then 4/4 fliers that satisfy The Earth King's power-4 gate. Clunky. |
| Alquist Proft, Master Sleuth | ◇ | craft M. ETB Clue + big X draw. **No doubler sees it** (Detective, power 3) — R1. |
| Earth Kingdom Protectors | ◇ | craft U. Cheap Ally body, but the sac is ACTIVATED so no doubler (R1); saves one Ally once. |
| Ant-Man, Colony Commander | ◇ | OWNED. Power 2 → Delney sees the attack trigger, but the token half is capped "only once each turn" and the {G}{U} cost is R3-awkward. |
| Niko, Light of Hope | ◇ | craft M. Shards + a copy engine; no doubler, and the copy ability is activated. |
| Oko, the Ringleader | △ | OWNED. Planeswalker, {G}{U}, Elk tokens. Off-plan. |
| Katara, Bending Prodigy | △ | OWNED. Both doublers see the end-step counter, but that is one counter a turn; waterbend {6} draw is unpayable early. |
| Hermitic Herbalist | △ | OWNED. Already cut from the 60: the second ability is **Lesson-gated and dead here** (R5), and {G}{U} to cast a fixer is circular. |
| Katara, Water Tribe's Hope | ◇ | OWNED. Real card, blocked by R3 — {U}{U} on 8 blue sources would be the worst row in the deck. |
| **Pinnacle Starcage** | **✗** | craft R. **Exiles ALL artifacts and creatures with MV 2 or less — including yours.** Ally tokens are MV 0 and 13 of the deck's early drops are MV ≤2. Textbook G-42 / R7. |
| Tolls of War | ✗ | OWNED but **off-colour (BW)** — R3. Makes Ally tokens on sacrifice; note it if a B/W Ally build ever happens. |
| Jet, Freedom Fighter | ✗ | **off-colour (RW)** — R3. |
| The Mechanist, Aerial Artisan | ★ | OWNED. Graded last turn: 9 noncreature spells is thin, but Delney AND Katara both see it (Ally, power 1) so it is 2–3 Clues per trigger. |

### Batch 2 (25–48)
| card | v | note |
|---|---|---|
| Starry-Eyed Skyrider | ★★★ | craft U. **"Attacking tokens you control have flying"** — evasion for the entire token swarm, which is how this deck actually closes. Power 1 → Delney doubles the attack trigger too. |
| Voice of Victory | ★★★ | craft R. Mobilize 2, power 1 → **Delney makes it four attacking tokens per combat**; they die at end step, feeding Suki. Plus opponents can't cast spells during your turn. |
| Oltec Matterweaver | ★★★ | craft M. Triggers on **casting a creature spell — 27 of them** — and power 2, so Delney doubles it. Second mode copies an artifact token (Clues). |
| Cosmogrand Zenith | ★★ | OWNED ×2. Second spell each turn → two tokens or a counter on each creature. Power 2 → Delney doubles. Already in deck 28a; copies are fungible. |
| Okoye, Dora Milaje Leader | ★★ | OWNED. ETB two tokens, and **attacking creature tokens have first strike** — real for a 1/1 swarm. No doubler (Hero, power 3). |
| Grand Abolisher | ★★ | OWNED M. Opponents can't interact on your turn — protects the doubler you spent three mana on. Static, so no doubler (R1). |
| Friendly Neighborhood | ★★ | OWNED. Three tokens on ETB plus a land that pumps by creature count. |
| Silk, Web Weaver | ★★ | craft R. A token per creature spell (27 of them) + a team pump. Power 3, not an Ally → no doubler. |
| Bard's Company | ★★ | craft R. Recruit on ETB **and** attack, power 2 → Delney doubles both. Anthem half is R2 tension. |
| Aerith Gainsborough | ★★ | OWNED. Counters whenever you gain life, and the deck gains life on Voyager/Compassionate Healer/E.K. General. Power 2 → Delney. |
| Sheriff of Safe Passage | ★ | OWNED. Enters as a big body scaled to your board; plot. No trigger for the doublers. |
| Snow Villiers | ★ | OWNED. Power = creature count, vigilance — a cheaper Suki, Kyoshi Warrior. |
| Silver Sable, Mercenary Leader | ★ | OWNED. Power 2 → Delney doubles the ETB counter. Modified-creature lifelink is live (counters everywhere). |
| Spider-UK | ★★ | craft U. "Two or more creatures entered this turn → draw and gain 2" is near-unconditional here. No doubler. |
| The Queen of Dale | ◇ | OWNED. Keys on the OPPONENT's spells — a different deck's card. |
| Great Gilded Boat | ◇ | OWNED. Crew taps your creatures (R7c). |
| Sage of the Skies | ◇ | OWNED. Copies itself on a second spell. Fine, unexciting. |
| Descendant of Storms | ◇ | craft U. Delney doubles endure, but it costs {1}{W} per attack. |
| Linden, the Steadfast Queen | △ | OWNED. **{W}{W}{W} against 13 white sources** — R3 puts this below the Katara band. |
| Sound the Trumpets | △ | craft U. {1}{U}{U} on 8 blue sources (R3), and a counterspell is off-plan. |
| Informed Inkwright | △ | craft R. Wants instants/sorceries targeting creatures; the deck has ~3. |
| Orphans of the Wheat | △ | craft U. Taps your own untapped creatures to pump one — fights the go-wide attack. |
| Vengeful Townsfolk | △ | OWNED. Needs your creatures to die; nothing here sacrifices. |
| Wild Pack Squad | △ | craft C. One creature gains first strike/vigilance. Filler. |

### Batch 3 (49–72)
| card | v | note |
|---|---|---|
| **Starfield Vocalist** | **★★★★** | OWNED. *"If a permanent entering the battlefield causes a triggered ability of a permanent you control to trigger, that ability triggers an additional time."* **A THIRD DOUBLER, and the broadest one** — no Ally restriction, no power restriction. It doubles all 19 ETB triggers AND Voyager/Enthusiasts/Haru. Warp {1}{U} deploys it for two mana. **The best card in the pile.** |
| Mister Fantastic, Reed Richards | ★★★ | OWNED. "Whenever one or more tokens you control enter, you may draw a card" against 10 token makers — and power 2, so **Delney doubles it**. Card advantage is the short axis (R4). |
| Echo, Perceptive Prodigy | ★★★ | OWNED. `{1},{T}: copy a triggered or activated ability you control from a creature` — a repeatable manual doubler, power 1 so Delney doubles nothing here (it is activated) but it copies whatever matters that turn. |
| Sandstorm Salvager | ★★ | craft M. ETB 3/3 Golem (doubled = two), and `{2},{T}` puts a counter on **each creature token** with trample — a mass pump aimed at exactly this board. Power 1 → Delney sees the ETB. |
| The Wandering Rescuer | ★★ | craft M. Flash + **convoke** (answers R7c directly), double strike, and **other tapped creatures have hexproof** — protection for a board tapped for mana. R4 says protection is 2. |
| Aang, Swift Savior // Aang and La | ★★ | OWNED. Flash flier; ETB airbends a creature **or a spell** (a soft counterspell). Ally at power 2 → **both doublers**. |
| For the Common Good | ★★ | OWNED. X copies of a token + indestructible + life. Books as MV 1 (G-60) — read the real cost. |
| Shang-Chi, Master of Kung Fu | ★ | OWNED M. Haste for activated abilities + two mana for creature abilities — turns on waterbend and the Great Divide Guide plan. |
| Raucous Audience | ★ | OWNED. Taps for {G}, or {G}{G} with a power-4 creature — earthbent lands turn that on. |
| Mirrormind Crown | ★ | OWNED. Your first token wave each turn becomes copies of the equipped creature. Spicy; fragile, and legend-rule awkward on Katara. |
| Orcrist, Goblin-cleaver | ◇ | OWNED. Choose-a-type Treasure per creature of that type on combat damage — a K-13 card. Needs the equipped creature to connect. |
| Syr Alin, the Lion's Claw | ◇ | craft U. Attack anthem at MV 5; R2 tension. |
| Esgaroth Garrison | ◇ | craft C. Power = creature count at MV 5, ETB recruit. |
| Dawnstrike Vanguard | ◇ | OWNED. MV 6; counters on everything if two creatures are tapped. Curve cost is real. |
| Homunculus Horde | ◇ | craft R. Copies itself on your second draw each turn — the deck draws, but not reliably twice. |
| Bard the Bowman | ◇ | craft U. Same second-draw gate, smaller payoff. |
| Chameleon, Master of Disguise | ◇ | OWNED. Enters as a copy of your best creature; mayhem needs a discard the deck does not have. |
| Wingblade Disciple | ◇ | OWNED. Flurry Bird token on a second spell. Fine, small. |
| The Notary Hobbits | ◇ | OWNED. Makes two copies of itself — three bodies for 5 — but the mana ability counts **Halflings**, of which the deck has 0 (R5). |
| Season of Weaving | △ | craft M. {4}{U}{U} on 8 blue sources (R3). |
| Sapling Nursery | △ | OWNED. MV 8 with affinity for Forests; the deck runs 3. |
| Zanarkand // Lasting Fayth | △ | OWNED. Adventure makes one Hero token scaled to lands; the land half enters tapped. |
| Torgal, A Fine Hound | △ | craft U. Counters scale with **Dogs and Wolves** — the deck has 0 (R5). One of only two Human payoffs in Bant, and it still does not work here. |
| Fuss // Bother | ✗ | **off-colour (RUW)** — R3. |

### Batch 4 (five late additions)
| card | v | note |
|---|---|---|
| Leader's Talent | ★★ | OWNED. Level 3 is *"whenever you cast a spell, put a +1/+1 counter on each creature you control"* — enormous on a wide board. No doubler sees it (enchantment, and the trigger is a cast, not a permanent entering). Maximum R2 tension. |
| Duty Beyond Death | ★★ | OWNED. Team indestructible + counters at instant speed for a creature — protection is the short axis (R4 says 2), and the sacrifice feeds Suki's leaves-play trigger. |
| Kykar, Zephyr Awakener | ★★ | craft R. The blink mode re-triggers an ETB and feeds Suki; the Spirit mode is a flier. Gated on **9 noncreature spells** (R5). **G-42 warning: blinking your own creature ERASES its +1/+1 counters** — bad on Avatar Enthusiasts, which is the deck's counter sink. |
| Group Project | ★ | craft U. Two 2/2s across a game, and the flashback cost is **tap three creatures** — the convoke-shaped cost you asked about, on a card cheap enough to want it. |
| Anafenza, Unyielding Lineage | ◇ | OWNED. Delney doubles endure, but it needs your NONTOKEN creatures to die and nothing here sacrifices them (Duty Beyond Death would). |

### Batch 5 (seven late additions — the convoke follow-up)
| card | v | note |
|---|---|---|
| **Winnowing** | **★★★★** | craft R, convoke. *"For each player, you choose a creature that player controls. Then each player sacrifices all other creatures they control that don't share a creature type with the chosen creature."* **A ONE-SIDED SWEEPER IN THIS DECK SPECIFICALLY.** 26 of 27 creature copies are Allies and 24 are Human, so naming a Human Ally keeps ~24 and leaves the opponent whatever shares a type with the one creature you pick for them. R4 says the deck has no sweeper at all. |
| **Allies at Last** | **★★★** | OWNED. **Affinity for Allies** — {1} less per Ally, so it is free at five Allies — and it is REMOVAL: two of your creatures each deal damage equal to power to one of theirs. Interaction is the short axis (R4: 7). Unlike convoke it taps NOTHING, so it dodges R7c entirely. |
| **Enter the Avatar State** | **★★★** | OWNED. `{W}` instant: flying, first strike, lifelink **and hexproof**. A one-mana answer to the deck's stated single point of failure — a removal spell aimed at Katara or Delney. Protection measures 2 (R4). Also a **Lesson**, which turns on Aang's currently-dead Lesson clause (R5). |
| **Dazzling Theater // Prop Room** | **★★★** | craft R. G-02: MV reads 7 as the COMBINED cost — the front face is `{3}{W}`. Front gives **all 27 creature spells convoke**; back **untaps your team during each opponent's untap step**, which is pseudo-vigilance AND keeps Great Divide Guide's mana available on their turn. Both halves are on-plan. |
| Protective Response | ★★ | craft U. Convoke instant, destroys an attacking or blocking creature. Conditional but nearly free on a wide board. |
| Web of Life and Destiny | ★★ | OWNED (in 50a, 59 — fungible). Convoke, and a free creature onto the battlefield every combat = a free ETB every turn for the doublers. MV 8 base and `{G}{G}` against 8 green sources (R3); convoke's coloured-mana clause helps, but tapping fights attacking (R7c). |
| Crystal Fragments // Summon: Alexander | △ | craft U. Equip +1/+1 (R2 tension), and `{5}{W}{W}` to transform is far too slow for this curve. |

**Cross-batch note added here:** this batch answers the earlier convoke question properly.
The best "tap-cost" card in the whole pile is **Allies at Last**, which is not convoke at
all — **affinity for Allies** reduces the cost without tapping anything, so it is strictly
better than convoke in a deck that wants to attack (R7c). Search the effect shape, not the
keyword (K-13): a cost reducer that counts your board is what this deck wanted, and
"convoke" was the wrong noun for it.

## 5. Consolidated plan (live)

### THE FORK THIS PILE EXPOSED — decide before picking adds
A third of the pile pumps the team with +1/+1 counters (Leader's Talent, Virtue of
Loyalty, Sally Pride, Earth King's Lieutenant, United Front, Cosmogrand Zenith, Duty
Beyond Death…). **Every one of them turns Delney off** as it resolves: ten of the
fourteen Delney-eligible copies sit at exactly power 2 (R2). The deck can be

- **A. SMALL AND EVASIVE** — keep the team at power ≤2, add Delney-doubled triggers and
  evasion (Starry-Eyed Skyrider, Voice of Victory, Mister Fantastic, Belladonna Took).
  Delney's first line then makes the whole board unblockable by anything real.
- **B. WIDE AND PUMPED** — accept Delney as a fair 3-drop that sometimes doubles, and
  take the counter payoffs. Katara and Starfield Vocalist still work; Delney degrades.

They are not equally supported: **A is what the current 60 already is**, and B needs the
anthems the deck runs to be joined by four or five more. Pick A unless the user wants the
rebuild. Everything below is ranked for A, with B-only cards marked.

### ✅ THE RECOMMENDED 8 SWAPS (all owned · 0 wildcards · measured)

Four are SPELL-FOR-SPELL and cost the engine nothing. Four are creature upgrades and each
costs one Ally body — that is the real price and it is stated below.

| out | in | why |
|---|---|---|
| Into the Flood Maw `{U}` | **Enter the Avatar State** `{W}` | a bounce for a **one-mana hexproof** on the doubler the deck dies without. Also drops a blue pip (R3). |
| Crib Swap `{2}{W}` | **Allies at Last** `{2}{G}` | 3-mana exile that gifts them a body → **often-free** double-fight removal. Affinity for Allies WANTS the board this deck builds, and taps nothing (R7c). |
| Path to Redemption `{1}{W}` | **Rally the Monastery** `{3}{W}` | an aura that stops one attacker → instant removal, `{2}` cheaper after a first spell. |
| Kyoshi Battle Fan `{2}` | **Duty Beyond Death** `{1}{W}` | a 1/1 and an equip → team indestructible + counters at instant speed. |
| Forecasting Fortune Teller `{1}{U}` | **Starfield Vocalist** `{3}{U}` | **the third doubler.** |
| Compassionate Healer `{1}{W}` | **Belladonna Took** `{1}{W}` | tap-to-scry → a token engine that escalates to three, Delney-doubled. |
| Glider Kids `{2}{W}` | **Mister Fantastic** `{3}{U}` | ETB scry 1 → a card per token wave, Delney-doubled. |
| 1× Appa, Steadfast Guardian | **Echo, Perceptive Prodigy** `{2}{U}` | the 2nd Appa → a repeatable manual doubler. Airbend goes 4 → 3. |

**MEASURED (deck.py quality):** interaction 7 → 6 *(really 7 — see §2a)* · card advantage
4 → 4 *(under-read: Vocalist and Echo score zero roles, R6)* · **protection 2 → 4** ·
avg MV 3.06 → 3.17 · early drops 13 → 11 · **tier floor stays A**.

**THE COST, STATED PLAINLY: Ally copies 26 → 22.** Six of the eight cuts are Allies and
none of the adds is one, so Katara, South Pole Voyager, Avatar Enthusiasts and Haru all
get ~15% less fuel. What pays for it: **Starfield Vocalist does not read the Ally type at
all**, so the deck shifts from "many Ally triggers" to "fewer triggers, each worth more,
and a doubler that no longer depends on the tribe." That is a more robust engine, not just
a stronger one — but it IS a change of plan, so say no to the creature half if you want to
keep the tribal density.

**NOT taken, and why:** Bard, King of Dale (MV 6 on a 3.06 curve) · Captain America
(a fifth blue-ish card against 8 U sources, R3) · Sally Pride / Earth King's Lieutenant /
Leader's Talent / Virtue of Loyalty (all Fork B — their counters switch Delney off, R2).
**Aang, the Last Airbender and both Earth Kingdom Generals are deliberately KEPT** even
though you offered them: they are the airbend and earthbend sub-engines (3 and 4 sources
after this plan), which nothing else in the pile replaces.

### CRAFT UPGRADES, as information (Player Profile: reported, not budgeted)
- **Winnowing** `{4}{W}{W}` R — the deck's only possible sweeper, and one-sided here.
- **Dazzling Theater // Prop Room** `{3}{W}` R — convoke on all 27 creature spells, then
  a team untap on their turn.
- **Starry-Eyed Skyrider** `{2}{W}` U — attacking tokens gain flying; the actual closer.

### TIER 1 — take, all OWNED, no wildcards
1. **Starfield Vocalist** `{3}{U}` — third doubler, broadest of the three, warp {1}{U}.
2. **Allies at Last** `{2}{G}` — affinity for Allies; free removal at five Allies, taps nothing.
3. **Enter the Avatar State** `{W}` — one mana of hexproof for the doubler that wins the game.
4. **Mister Fantastic, Reed Richards** `{3}{U}` — a card per token wave, Delney-doubled.
5. **Belladonna Took** `{1}{W}` — the token analogue of South Pole Voyager, escalating.
6. **Sally Pride, Lioness Leader** `{3}{W}{W}` — Delney doubles both halves. (Half B.)
7. **Echo, Perceptive Prodigy** `{2}{U}` — copy the best trigger each turn, repeatably.

### TIER 2 — owned, strong, situational on the fork
6. **Bard, King of Dale** `{4}{W}{U}` — doubles tokens AND extra draws. MV 6.
7. **Aang, at the Crossroads** `{2}{G}{W}{U}` — Katara doubles the tutor; back face is the
   earthbend engine. R3's worst cost band.
8. **Captain America, Living Legend** `{1}{W}{U}` — board-wide untap; doubles Great Divide
   Guide's mana and gives the team pseudo-vigilance.
9. **Rally the Monastery** `{3}{W}` ×2 — the only removal in the pile for the short axis.
10. **Duty Beyond Death** / **Grand Abolisher** — protection, the other short axis.

### TIER 3 — the crafts worth the wildcards
- **Winnowing** `{4}{W}{W}` R — a one-sided wipe here, and the deck's only sweeper.
- **Dazzling Theater // Prop Room** `{3}{W}` R — convoke for every creature, then a team untap.
- **Starry-Eyed Skyrider** `{2}{W}` U — attacking tokens have flying. The closer.
- **Voice of Victory** `{1}{W}` R — Delney makes mobilize 2 into four attacking tokens.
- **Oltec Matterweaver** `{2}{W}` M — triggers on 27 creature spells, Delney-doubled.
- **Earth King's Lieutenant** `{G}{W}` R — the only both-doublers-both-triggers card. (B.)
- **The Wandering Rescuer** `{3}{W}{W}` M — flash convoke, hexproof for tapped creatures.

### CUT CANDIDATES (from `deck.py cuts`, re-read against this pile)
Gather the White Lotus (spell-effect tokens no doubler sees; 6 Plains) · Into the Flood
Maw · Crib Swap · Path to Redemption · Kyoshi Battle Fan · United Front (B-only) ·
Invasion Tactics (its draw trigger is on an enchantment — no doubler).

### PROTECT — what `cuts` structurally cannot see
**Katara, the Fearless · Delney, Streetwise Lookout · South Pole Voyager · Avatar
Enthusiasts · Haru, Hidden Talent · Suki, Kyoshi Warrior.** The first three score ZERO
detected roles (R6) — a trigger-doubler has no bucket — so the ranking puts the deck's
engine at the top of its own cut list.

### HARD NO
**Pinnacle Starcage** — exiles your own board (R7). **Tolls of War, Jet, Fuss // Bother**
— off-colour (R3).

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`
