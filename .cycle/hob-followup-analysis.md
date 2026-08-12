# HOB follow-up pile (27 cards) vs decks 69 / 69a / 69b — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into the
deck files' `#: notes:`. A scratchpad, not a source of truth — decks/ are.

**Source list:** 27 owner-proposed cards. None already in 69 or 69a; Through the Forest
Gate is already in 69b (so evaluated for 69 / 69a only).

## 1. The decision framework

**F1 — CASTABILITY IS NEARLY FREE HERE, WITH ONE EXCEPTION.** 26 of 27 are mono-green,
so they are castable in all three decks. **Tom, Bert, and William is BG → NOT castable in
mono-green 69a** (`screen` confirms). That is the only hard colour gate in the pile.

**F2 — DECK 69 GRADES ON THE GATE: does the card PROVIDE power-4, or WAIT for it?**
This is the Wargling lesson generalised. A provider is worth more than a consumer of
equal rate, and HASTE / FLASH are worth a premium because the gate is checked at ATTACK
time — a hasty power-4 body turns Ferocious on the turn it lands.

**F3 — DECK 69's LOUDEST UNANSWERED WARNING IS "counters: 19 enablers, NO PAYOFF".**
A counter DOUBLER is the payoff, and it multiplies an axis the deck already has more of
than any other. `screen` scores The Earth Crystal and Loading Zone as `✱ multiplier —
doubles counters (17 feeders here)`. This is the single highest-leverage line in the pile.

**F4 — DECK 69a GRADES ON TWO NUMBERS: lands in play, and permanent cards in the
graveyard.** It self-mills hard, so a cost reducer keyed to the graveyard is cheap here
and nowhere else. Its weakest axis is card advantage 2. Curve is already 3.44 — a 7+ drop
must be a finisher, not filler.

**F5 — DECK 69b GRADES ON COLOUR, NOT POWER.** W 11 / B 14 / G 20 sources against
{W}{W} and {B}{B} costs. Anything that makes mana any-colour is worth more than its own
body here, and anything costing {G}{G}{G} is worse than it looks (Overrun).
Weakest axis on the family: card advantage 1.

**F6 — ROTATION.** Only two of the 27 rotate ~2027: **Overlord of the Hauntwoods** and
**Rise of the Varmints**. The rest are 2028-29.

**F7 — WHAT IS STRUCTURALLY INVISIBLE.** `cuts`/`suggest` cannot see a doubler's worth
(G-40 — routed through `suggest-homes`' multiplier primitive only), cannot read a
graveyard-scaled cost reduction, and score every card in isolation (G-61). Every verdict
below that leans on "the rest of the deck" is a human read, not a tool output.

## 2. Standing error list
- Do not grade a doubler by its own text (it does nothing alone) — count its feeders.
- Do not read `screen`'s KEY as a verdict; it saturated at 86% on the last HOB batch.
- Do not dismiss a landfall card from 69 by category — 69 runs Beorn's Hospitality and
  Dancing from Dark to Dawn, so it has real landfall payoffs (the G-42-in-reverse trap).

## 3. Cross-batch observations
- The pile contains **three counter doublers** (Doubling Season, The Earth Crystal,
  Loading Zone). They are not interchangeable: Earth Crystal is cheapest AND cuts {1} off
  ~85%-green deck 69's spells; Doubling Season also doubles TOKENS (which matters in 69b's
  token engine, 10 enablers); Loading Zone has Warp {G} for a turn-1 deploy.
- Deck 69a is the only home for graveyard-scaled costs (Diamond Weapon) and land-sacrifice
  value (Planar Engineering — the sacrificed lands feed Lumra/Titan/Analyst, which is why
  it is better here than in deck 50a, which cut it).
- **Variant signal: none.** Every card slots into an existing family member; no coherent
  cluster is being rejected for the same reason.

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`

| Card | 69 Ferocious | 69a Lands | 69b Convergence | Note |
|---|---|---|---|---|
| The Earth Crystal | ★★★ | ★★ | ★ | F3. 17 feeders in 69 + {1} off ~85%-green spells. Best doubler for 69. |
| Germination Practicum | ★★★ | ★ | ★★ | Two counters on EACH of 27 creatures, Paradigm = free recast every turn. The counters PAYOFF. |
| Selfless Safewright | ★★★ | ◇ | ★ | F2 provider at FLASH speed + names Wolf (15 bodies) for hexproof/indestructible vs a wipe. Convoke is cheap in a wide deck. |
| Leatherhead, Swamp Stalker | ★★★ | ★ | ★ | 5/4 provider, hexproof counter (protection 2), and 69's SECOND noncreature answer. |
| Vizier of the Menagerie | ★ | ★ | ★★★ | F5. "Spend mana of any type to cast creature spells" fixes every creature in 3-colour 69b; top-of-library feeds card-adv 1. |
| Doubling Season | ★★ | △ | ★★★ | 69b: 10 token + 9 counter enablers — doubles Suki's Allies, Torgal's counters, Crooked Way's amass. |
| Diamond Weapon | ✗ | ★★★ | ✗ | F4. {1} less per permanent in graveyard; 69a mills 4–7 at a time. 8/8 reach, immune to combat damage. Only 69a can cast it cheap. |
| Harmonious Grovestrider | ★ | ★★★ | ◇ | 26 lands → 6/6+ with ward 2. Natural 69a body. |
| Mightform Harmonizer | ★ | ★★★ | ◇ | 4/4 + landfall power-doubling; Traveling Chocobo doubles the trigger. |
| Groundchuck & Dirtbag | ★★ | ★★★ | ◇ | 8/8 trample; land-tap doubler against 26 lands and ~1 creature mana source. |
| Overlord of the Hauntwoods | ★★ | ★★ | ★★★ | Land token is EVERY BASIC TYPE = 69b fixing, on enter AND attack. **⚠rot~2027.** |
| Galion, Elvenking's Butler | ★★ | ★ | ★ | 4/4 provider that also makes a 2/2 Wargling a 4/4 — double gate provision. |
| Moon-Vigil Adherents | ★★ | ★★ | ★★ | +1/+1 per creature AND per creature card in graveyard. Base 0/0 is the risk. |
| Troll Negotiations | ★★ | ★ | ★ | Counters + fight: removal that feeds the central theme. |
| Radagast of Rhosgobel | ★★ | ★ | ★★ | First creature each turn {2} cheaper + flash. 27 creatures in 69. |
| Gigantic Big Bear | ★★ | ★ | ◇ | Bear (Beorn +2/+2), HASTE = same-turn gate, hexproof dodges 69's stated failure mode. 7 MV. |
| Overrun | ★★ | ◇ | ★ | WIDE finisher (69 wide score 9). {G}{G}{G} is fine at G 20 in 69, tense in 3-colour 69b. |
| Loading Zone | ★★ | △ | ★ | Third doubler; Warp {G} deploys turn 1. 17 feeders in 69. |
| Seedship Agrarian | △ | ★★ | ◇ | Landfall counter + Lander on tap. |
| Planar Engineering | ✗ | ★★ | ✗ | Sacrificed lands go to the GRAVEYARD, which Lumra/Titan/Analyst return — better here than in 50a, which cut it. |
| Rise of the Varmints | ◇ | ★★ | ◇ | X 2/1s = creature cards in yard. **⚠rot~2027.** |
| Tom, Bert, and William | ★ | ✗ **uncastable** | ★★ | F1. BG. In 69b its death-return is a creature card LEAVING the graveyard → Crooked Way amass. |
| Through the Forest Gate | ✗ | ★★ | (in deck) | 8 MV against 69's 2.97 curve is a non-starter; in 69a every land is a landfall trigger, doubled by Chocobo. |
| Flopsie, Bumi's Buddy | ★ | ◇ | ★ | ETB counter on each creature + power-4 evasion. 6 MV. |
| Michelangelo's Technique | ★ | ◇ | ★ | Dig 8, two creatures totalling MV ≤6 — 69's cheap creatures fit that cap; 69a's do not. |
| Glacier Godmaw | ◇ | ★ | ◇ | Landfall team pump. 7 MV. |
| Primeval Bounty | △ | ◇ | △ | 6 MV, no immediate board. Too slow for every curve in the family. |

## 5. Consolidated plan (live) — PROPOSED, not applied

### Deck 69 — answer the "no counters payoff" warning
1. **The Earth Crystal** (owned) ← Bite Down  · doubles 17 feeders + {1} off green
2. **Germination Practicum** (owned) ← Drover Grizzly  · repeatable mass counters
3. **Selfless Safewright** (craft R) ← Unforgiving Aim  · flash provider + anti-wipe
4. **Leatherhead** (owned) ← Felling Blow  · provider + 2nd noncreature answer
Cut pool is thin on interaction (5) — take 1–2, not all four, or replace the removal elsewhere.

### Deck 69a — the owner's seven, ranked, with cuts
1. **Diamond Weapon** (owned) ← Part in Friendship (`cuts` 1/28)
2. **Harmonious Grovestrider** (owned) ← Mirkwood Pathmaker (`cuts` 3/28, and Grovestrider is the same body with ward 2)
3. **Groundchuck & Dirtbag** (craft R) ← Grow from the Ashes (`cuts` 7/28)
4. **Mightform Harmonizer** (owned) ← Drover Grizzly (`cuts` 8/28)
Of the seven proposed: Earth Crystal ★★ and Seedship Agrarian ★★ are next in line;
**Primeval Bounty is the one to skip** (6 MV, no board impact, on a 3.44 curve).

### Deck 69b — fix the colour, then the card advantage
1. **Vizier of the Menagerie** (owned) — the best card in the pile for this deck
2. **Doubling Season** (owned)
3. **Overlord of the Hauntwoods** (owned) — but ⚠rot~2027
4. **Tom, Bert, and William** (craft R) — card advantage 1 is the family's weakest axis

### PROTECT — what the ranking structurally cannot see
- **Loot, Exuberant Explorer** and **Part in Friendship** both sort high on 69a's cut list
  and both carry `⌁scales w/ lands — graded at its FLOOR`. Part in Friendship is listed as
  a cut above only because Diamond Weapon does its job better at the same slot; Loot is
  NOT cuttable (it was restored on the owner's challenge last cycle for exactly this).
- **Garruk's Uprising** sorts 4th on 69's cut list and is the deck's card-advantage engine.
- **Beorn's Hospitality** sorts 6th on 69's list with the same floor flag.
