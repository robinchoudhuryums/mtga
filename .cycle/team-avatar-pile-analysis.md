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

## 5. Consolidated plan (live)
_(populated from batch 1 onward)_

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`
