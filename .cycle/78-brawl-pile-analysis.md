# 78-historic-brawl pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into the
deck file's `#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Target:** `decks/78-team-avatar/78-historic-brawl-team-avatar.txt` — Team Avatar — Brawl,
Arena's 100-card Brawl queue (`#: format: Historic Brawl`), commander Katara, the Fearless.

**Source list:** 73 owned cards named by the owner on 2026-09-29, resolved with
`deck.py resolve --format "Historic Brawl"`. All 73 resolve and all are Brawl-legal.
None is already in the target deck. All 73 are inside Katara's G/W/U colour identity.

**Two adaptations of the skill's Stage 0:**

- **The dedupe was against the TARGET deck only**, not every deck, because copies are
  shared across decks (CLAUDE.md, "Decks share the collection").
- **The screen was on colour IDENTITY, not castability.** In Brawl the commander's identity
  is a legality rule, which is the opposite of G-58's castability lesson. Hybrid symbols
  and mana symbols in rules text both count. `deck.py legal` enforces it.

**Ownership gap (G-10):** 53 of the 73 are not in `card-library.csv` at all, although the
owner says all 73 are owned. Ownership never gates a recommendation here. It does mean
`check` will call them craft targets until an ingest records them (`/ingest`).

## 1. The decision framework

Live vector, 2026-09-29, from `deck.py tier/stats/shape/engines/tribes`:

- Interaction 11 (≈6.6 per 60) and card advantage 5 (≈3 per 60). The metrics floor reads A
  on raw counts; the tier is B, held by density.
- Protection 6.
- 46 creatures, 34 Allies, 34 Humans. Shape WIDE (wide 20 / tall 7).
- 38 lands; average nonland MV 3.39.
- Engines: tokens 18 enablers / 13 payoffs; counters 16 / 2; lifegain 9 enablers and
  0 payoffs by the classifier. Belladonna Took is in fact a lifegain payoff, which the
  classifier does not read as one.

The numbered rules:

- **F1 — Value is triggered abilities times the multipliers.** Katara and Roaming Throne
  (naming Ally) each add one extra trigger to every triggered ability of an ALLY. Starfield
  Vocalist, Elesh Norn and Virtue of Knowledge each add one to every ENTERS-caused trigger
  of ANY permanent. An Ally with an enters trigger can fire 4–6 times. A non-Ally permanent
  with an enters trigger fires up to 4 times.
- **F2 — Some cards are graded at face value.** Static abilities, activated abilities,
  instants and sorceries get NO multiplier. Grade those against a generic 100-card deck,
  not against this engine.
- **F3 — Token OUTPUT is multiplied separately.** Doubling Season, Elspeth, Storm Slayer and
  Exalted Sunborn double tokens created, so a token maker is multiplied twice: once by the
  trigger doublers and once by the token doublers.
- **F3b — Bard, King of Dale is a FOURTH token doubler and a DRAW doubler** ("if you
  would draw a card except the first one you draw in each of your draw steps, draw two
  cards instead"). F3 missed him until the cut read (E6). Every draw engine the pile adds
  is doubled again while Bard is out.
- **F4 — The thin axis is card advantage.** It is 5 cards, about 3 per 60. Repeatable draw
  that fires off creatures entering or attacking is the highest-priority add. Interaction is
  close to the A density already, so a new removal spell must beat an existing one, not
  just exist. Protection is 6.
- **F5 — The deck is WIDE**, 46 creatures. A team-wide effect scales with the board, and a
  single huge body is off-plan unless it does something the board uses.
- **F6 — The printed cost is roughly what the deck pays.** There is no general cost
  reducer. Dazzling Theater gives creature spells convoke, which in a 46-creature deck is a
  real discount on creatures only. Allies at Last has affinity for Allies. Grade the
  curve at printed cost otherwise.
- **F7 — This is 1v1 Brawl at 25 life on the Historic pool.** Opposing sweepers and cheap
  removal are common, so recovery and protection for Katara are worth more than in
  Standard. A commander can be recast, but each recast costs {2} more.
- **F8 — Lifegain has 9 enablers and one real payoff (Belladonna Took).** A second
  lifegain payoff converts cards that are already in the deck.
- **F9 — The tools cannot see some things.** Trigger doublers score ZERO roles, so `cuts`
  cannot see this deck's thesis. `cuts` ranked Path to Exile as the weakest card on
  2026-09-29, which is a shortlist artefact, not a grade (G-09). Grade every cut from its
  text.
- **F10 — The question to ask of every card, in order:**
  1. Is it a triggered ability on an Ally?
  2. Is it an enters trigger on any permanent?
  3. Does it fill card advantage?
  4. Does it protect the engine?
  5. Otherwise, grade it at face value against the curve.

## 2. Standing error list

- **E1 — `screen` KEY on an "attacks alone" card.** Black Panther, Claws of Bast screened
  KEY. Its only trigger is "whenever a creature you control attacks alone", which this
  46-creature deck almost never does. That is G-76's inverted state gate, and it is not
  in `screen`. Grade those cards from text.
- **E2 — `screen` cannot see the enters-doublers.** Inspiring Commander screened
  tangential. Starfield Vocalist, Elesh Norn and Virtue of Knowledge each make its draw
  trigger fire an extra time, so one small creature entering is 2–4 cards (F1, F9).
- **E3 — Deck-property counts behind batch 1**, taken 2026-09-29:
  - 23 nonland creatures with printed power ≤2, and 11 cards that make small creature
    tokens.
  - 1 Hero (The Astonishing Ant-Man), 5 Soldiers, 0 first strikers.
  - 1 creature that taps opposing creatures (Ty Lee).
  - The lands carry all three of Forest, Island and Plains.
- **E4 — `screen` repeated E2 in batch 2.** The Great Henge and Tribute to the World Tree
  screened tangential. Both draw from an enters trigger on a permanent, which the
  enters-doublers multiply.
- **E5 — Deck-property counts behind batch 2**, taken 2026-09-29:
  - 16 noncreature nonland spells, for The Mechanist's Clues.
  - 21 creatures with power ≥3, for Tribute to the World Tree's draw half.
  - Largest power 4–6 (The Earth King's 4/4 Bears, Exalted Sunborn, Overlord of the
    Mistmoors 6), so The Great Henge costs about {3}{G}{G}–{5}{G}{G}.
  - Great Divide Guide gives "each land and Ally you control" a mana ability. Badgermole
    Cub adds {G} "whenever you tap a creature for mana", so with Guide out every Ally is a
    two-mana creature. Without Guide, only Hermitic Herbalist and earthbent lands count.
- **E6 — The framework under-counted the doublers.** F3 listed three token doublers and
  missed Bard, King of Dale, who doubles tokens AND non-draw-step draws. Found on the cut
  read; now F3b.
- **E7 — Counts behind batch 3:** 25 legendary creatures, for Kellan Joins Up.
- **E8 — Castability of the package** (scratch copy, `consistency`, 2026-09-29):
  - Tribute to the World Tree ({G}{G}{G}) is 26% on turn 3 against 20 green sources, so it
    is a turn-5-or-later card here.
  - The Great Henge's {G}{G} is 69% by turn 5.
  - Kellan Joins Up is 68% on turn 3; Inspiring Commander ({W}{W}) is 78% on turn 5.

## 3. Cross-batch observations

- **O1 — Anthems are the deck's missing half.** Team pump reads 2, on a 46-creature wide
  deck. An Unexpected Party (+2/+2 to a chosen type, naming Ally), Virtue of Loyalty and
  Suki are all real anthems. Two of the three are also token or counter engines.
- **O2 — Card advantage that fires off entering creatures is the priority (F4).** Inspiring
  Commander is the best one so far.
- **O3 — The owner holds several of the pile's Marvel commander-set cards** (Heroes and
  Soldiers). This deck has 1 Hero and 5 Soldiers, so the Hero payoffs (Wondrous Revival,
  Captain America, Unbowed) are dead here. That is a variant signal only if more Hero
  payoffs turn up in batches 2–3.
- **O4 — Batch 2 answers F4 three times over.** The Great Henge, Tribute to the World Tree
  and Reed Richards are each a repeatable draw engine. The first two are enters triggers,
  so they are doubled. Card advantage is the thin axis, so these outrank everything else.
- **O5 — The Hero cluster grew and still has no home here.** Five Iron Man / Vision /
  Goliath / Giant-Man / Blue Marvel cards key on artifacts or power ≥4, which this deck
  does not build around. Together with batch 1's Hero payoffs, they look like a separate
  Marvel Heroes deck, not a 78 variant. Decide at the end (skill rule 7).
- **O6 — Batch 3 closes the variant question.** No Hero payoff in batch 3 fits this deck.
  The Hero / artifact cluster runs to about a dozen cards: the Iron Men, Vision, Ultron,
  Goliath, Giant-Man, Blue Marvel, both Captain Americas, Wondrous Revival, Hawkeye,
  Kwende. That is a real "Marvel Heroes" shell for `/draft-deck`, not a home in deck 78.

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`

### Batch 1 (cards 1–30)

| Card | Verdict | Operative text → reason |
|---|---|---|
| An Unexpected Party // At the Door | ★★★ | "creatures you control of the chosen type get +2/+2": name Ally → 34 Allies plus every Ally token (O1). The adventure half makes X 2/2 tokens, which the token doublers multiply (F3) |
| Inspiring Commander | ★★★ | "whenever another creature you control with power 2 or less enters, you gain 1 life and draw a card": 23 small creatures plus 11 small-token makers; the enters-doublers make each entry 2–4 cards (F1, F4, E2); the life feeds Belladonna Took (F8). {4}{W}{W}, but convoke from Dazzling Theater helps |
| Leyline Binding | ★★★ | flash; "exile target nonland permanent an opponent controls"; domain → {2}{W} once all three basic land types are out (E3). Its enters trigger is doubled by the enters-doublers, so it can exile TWO (F1). Beats Prayer of Binding ({3}{W}) on cost and reach; Prayer keeps its 2 life |
| Cyclonic Rift | ★★ | instant bounce for {1}{U}; overload {6}{U} bounces every nonland permanent the opponent controls. Face value (F2): answers anything, and with a wide board the overload is a win |
| Leonin Warleader | ★★ | "whenever this creature attacks, create two 1/1 white Cat creature tokens with lifelink that are tapped and attacking": 2 tokens, 4–8 with token doublers (F3); lifelink feeds F8. Not an Ally, so Katara does not double it |
| The Falcon, Sam Wilson | ★★ | ETB "+1/+1 counter on each other creature": enters-doublers plus Doubling Season. It is the second copy of Katara, Heroic Healer's effect, and hers is also doubled by Katara, so this is redundancy, not a new axis |
| Virtue of Loyalty // Ardenvale Fealty | ★★ | end step: "+1/+1 counter on each creature you control. Untap those creatures". A wide-deck anthem engine at face value, with counters doubled by Doubling Season. Instant half: a 2/2 Knight |
| Echo, Perceptive Prodigy | ★★ | "{1}, {T}: Copy target activated or triggered ability you control from a creature source": a repeatable extra copy of Earth Kingdom Jailer's or The Earth King's enters trigger. Its own ability is activated, so no multiplier (F2) |
| Suki, Courageous Rescuer | ★ | "Other creatures you control get +1/+0" on 45 bodies. Her token trigger "triggers only once each turn", the cap deck 78's notes cite for cutting her. The anthem alone earns a 100-card slot |
| Shi'ar Soldier | ★ | "{U}, {T}: Return another target permanent you control to its owner's hand": re-buys an Ally's enters trigger each turn, but costs a recast, and bounce erases +1/+1 counters (16 counter enablers — the G-42 shape) |
| Spaceshift | ◇ | instant flicker of a creature: re-fires its enters trigger (doubled) and dodges removal; the flicker resets any counters |
| Spider-Sense | ◇ | counters an instant, sorcery or triggered ability; web-slinging returns a tapped creature, which re-buys an enters trigger |
| Archangel of Tithes | ◇ | attack tax while untapped; block tax while attacking. Face value, WWW |
| Eagle of the Great Shelf | ◇ | attacks for +1/+1 per other creature: a big flier in a 46-creature deck; face value |
| Tetsuko Umezawa, Fugitive | ◇ | "power or toughness 1 or less can't be blocked": 1/1 Ally tokens swing freely, but every anthem above pushes them past 1 |
| The Wasp, Janet Van Dyne | ◇ | ETB 4 damage to a TAPPED creature, doubled by the enters-doublers; the deck has one tapper (E3) |
| Captain America, Steve Rogers | ◇ | attack: +1/+1 counter and indestructible on another creature; 4/4 lifelink for 5 |
| Angelic Guardian | ◇ | "whenever one or more creatures you control attack, they gain indestructible": sweeper-proof alpha strikes; 6 mana |
| Bond of Discipline | ◇ | tap all their creatures, lifelink for yours: a one-shot alpha strike |
| Black Widow, Intel Expert | △ | combat damage: "you and that player each draw two cards" — symmetric |
| Ponder | △ | selection, not card advantage (F4) |
| It'll Quench Ya! | △ | counter unless they pay {2}; the deck taps out |
| Captain America, Unbowed | △ | ETB indestructible for "Soldiers and Heroes" only: 5 Soldiers and 1 Hero (E3) |
| Vengeful Townsfolk | △ | counters when your creatures die; face value 3/3 |
| Imperial Cosmographer | △ | counters when creatures leave "without dying": only airbend and blink do that here |
| Wild Pack Squad | △ | first strike and vigilance to one creature a turn |
| Black Panther, Claws of Bast | ✗ | "attacks alone" in a go-wide deck (E1) |
| Kwende, Pride of Femeref | ✗ | double strike for first strikers; the deck has 0 (E3) |
| Hawkeye, Clint Barton | ✗ | 3/5 vigilance, no other text |
| Wondrous Revival | ✗ | returns Hero cards; 1 Hero in the deck (E3) |

### Batch 2 (cards 31–60)

| Card | Verdict | Operative text → reason |
|---|---|---|
| The Great Henge | ★★★ | "whenever a nontoken creature you control enters, put a +1/+1 counter on it and draw a card": an enters trigger, doubled by the enters-doublers (F1, O4). "{T}: Add {G}{G}. You gain 2 life" feeds F8. Costs about {3}{G}{G}–{5}{G}{G} here (E5) |
| Tribute to the World Tree | ★★★ | "whenever a creature you control enters, draw a card if its power is 3 or greater. Otherwise, put two +1/+1 counters on it": tokens included, doubled (F1, F3). 21 bodies draw (E5). GGG against 20 green sources is a turn-4-plus cast |
| Reed Richards, Smartest Man | ★★ | "the first time you would draw a card each turn except the first card you draw during each of your draw steps, you draw four instead": every turn's first extra draw, yours and theirs, becomes four (F4). Static, so face value (F2). A 6-mana 2/4 that removal ends |
| Silver Surfer, Cosmic Voyager | ★★ | flash; ETB "exile any number of other target permanents you control. Return those cards … at the beginning of the next end step": a mass re-buy of every enters trigger on the board, and an instant-speed sweeper dodge. TOKENS exiled this way are gone, and counters reset (the G-42 shape) |
| Black Panther, Wakandan King | ★★ | "whenever Black Panther or another creature you control enters, put a +1/+1 counter on target land you control" (enters-doubled, tokens included); "{3}: Move all +1/+1 counters from target land … If one or more … are moved this way, you gain that much life and draw a card". A 2-drop that is card advantage plus F8 |
| Triumph of the Hordes | ★★ | "creatures you control get +1/+1 and gain trample and infect": with a wide board, ten poison in one swing. Face value (F2); a finisher, not an engine |
| Fractured Identity | ★★ | "exile target nonland permanent. Each player other than its controller creates a token that's a copy of it": in 1v1 a removal spell that also steals. The copy is a token, so the token doublers make TWO copies |
| The Mechanist, Aerial Artisan | ★ | an Ally: "whenever you cast a noncreature spell, create a Clue token", doubled by Katara and Roaming Throne (F1, F3). 16 noncreature spells (E5), so about one Clue batch every few turns. `screen` KEY |
| Badgermole Cub | ★ | "whenever you tap a creature for mana, add an additional {G}": with Great Divide Guide out, every Ally makes two mana (E5). ETB earthbend is doubled. Banned in Standard, legal here. Conditional on one card (Guide) |
| Bloom Tender | ★ | "for each color among permanents you control, add one mana of that color": three mana from a 2-drop in G/W/U. Ramp, which the deck has 4 of |
| Hindering Light | ★ | {W}{U}: "counter target spell that targets you or a permanent you control. Draw a card": protects Katara and replaces itself (F7) |
| Stark's Ingenuity | ◇ | ETB "you may pay {X}. If you do, draw X cards", doubled by the enters-doublers (pay twice). An Aura, so it dies with its creature |
| Hulk, Brutal Brawler | ◇ | "whenever Hulk attacks, put a +1/+1 counter on each other creature you control" (Doubling Season doubles); must attack each combat |
| Gamma Grotesque | ◇ | power-up {4}{G}{G}: "draw a card for each creature you control with a counter on it". One-shot; big in a counters-heavy board |
| Ms. Marvel, Elastic Ally | ◇ | draws once a turn when a pumped creature connects; anthems and counters make that routine. Hybrid {G/W} |
| Iron Man, Futurist Paragon | ◇ | combat: target creature "becomes an artifact creature with base power and toughness 5/5 and gains flying" — a 1/1 token becomes a 5/5 flier. 6 mana |
| Blue Marvel, Adam Brashear | ◇ | 3/5 flier with ward {2}; grows on a second draw each turn. Face value |
| War Machine, James Rhodes | ◇ | attack: "tap up to one target creature"; a second tapper for The Wasp and Momo-style cards |
| Cytoplast Manipulator | ◇ | steals a creature "with a +1/+1 counter on it" for {U},{T}; graft can move a counter onto an opposing creature as it enters. Clunky |
| Algorithmic Ferocity | ◇ | 1-mana fight plus indestructible; needs a big creature |
| Unstoppable Plan | △ | untaps your nonland permanents at your end step — pseudo-vigilance after convoke or waterbend |
| Fantastic Bounce | △ | sorcery bounce plus a card; Cyclonic Rift does the job at instant speed |
| Goliath, Mass Manipulator | △ | power-up draws per power-≥4 creature; few of those |
| Giant-Man, Gargantuan Genius | △ | mana per power-≥4 creature; few of those |
| Nature's Will | △ | combat damage taps their lands and untaps yours |
| Flora Colossus | △ | 7-mana hexproof */* equal to your lands |
| Vision, Spectral Synthezoid | △ | 8 mana; one free noncreature spell a turn |
| Iron Man, Modern Marvel | ✗ | pumps and draws off ARTIFACT creatures; the deck runs 1 (Roaming Throne) |
| Iron Man, Bleeding Edge | ✗ | copies artifact spells; the deck runs 2 artifacts |
| Through the Forest Gate | ✗ | 8-mana land ramp; the deck does not need lands late |

### Batch 3 (cards 61–73)

| Card | Verdict | Operative text → reason |
|---|---|---|
| Kellan Joins Up | ★★★ | "whenever a legendary creature you control enters, put a +1/+1 counter on each creature you control": 25 legendary creatures (E7). An enters trigger, so doubled; counters doubled again by Doubling Season. Its enters trigger plots a card of MV 3 or less |
| Buried in the Garden | ★★★ | Aura on a land; ETB "exile target nonland permanent you don't control until this Aura leaves", doubled by the enters-doublers, so it can exile TWO. The enchanted land makes an extra mana of any colour. Removal plus ramp for {2}{G}{W} |
| Silk, Web Weaver | ★★★ | "whenever you cast a creature spell, create a 1/1 green and white Human Citizen creature token": a token per creature spell, and 41–46 creatures, multiplied by four token doublers (F3, F3b). Every token is power 1, so it feeds Inspiring Commander and Tribute. "{3}{G}{W}: Creatures you control get +2/+2 and gain vigilance" is a repeatable anthem |
| Contagion Engine | ★★ | ETB "put a -1/-1 counter on each creature target player controls", doubled, so -2/-2 to their whole board. "{4}, {T}: Proliferate twice" on your own +1/+1 counters. A one-sided sweeper that becomes a counter engine |
| Kellan, the Kid | ★ | "whenever you cast a spell from anywhere other than your hand, you may cast a permanent spell with equal or lesser mana value from your hand without paying its mana cost": Katara from the command zone qualifies, as do the three adventure cards cast from exile. 3/3 flier with lifelink (F8) |
| Akroma's Memorial | ★ | "creatures you control have flying, first strike, vigilance, trample, haste": a finisher on a 41–46 creature board. 7 mana; face value |
| Storm, Windrider | ◇ | 4/4 flier; opposing fliers "can't attack you or block creatures you control". Face value |
| Decisive Denial | ◇ | fight, or counter a noncreature spell unless they pay {3} |
| Planetarium of Wan Shi Tong | ◇ | a free cast off each scry, once a turn; the deck's scry sources are few (Galadriel, Niko's Shards) |
| Rumble Arena | ◇ | untapped land, ETB scry 1 (doubled). Colourless unless you pay {1}, so it costs fixing in a three-colour deck. Only as a swap for an unconditional tapland |
| Ant-Man, Reformed Rogue | △ | draws on combat damage; needs green/blue spells to enable |
| Mindslaver | △ | 10 mana total to take one turn |
| Ultron, Machine Overlord | ✗ | pumps Robots and Constructs; the deck has none |

### Batch 4 — the owner's 37-card craft list (2026-09-29)

All 37 resolve and are Historic Brawl legal. **Mister Fantastic is out: its `{R}{G}{W}{U}`
ability puts R in its identity, illegal under Katara.** Before this batch no recommender and
not `screen` checked identity (now fixed: `commander_identity_lock`). Water Whip, raised by
the owner as not legal on Arena, is `brawl: legal` / `standardbrawl: not_legal` on Scryfall
(Arena id 98189), the same status as the five TLE cards already in the list.

Gap to A (per 60, scaled): interaction 11 -> 12 AND interaction + card advantage 17 -> 19.
Measured on scratch copies (cuts: Earth Kingdom Protectors + Aang, Airbending Master):

| Adds | Floor | Note |
|---|---|---|
| Vault Guardsman + Inspiring Call (owned) | **A** | protection stays 6; both castable ≥88% |
| Vault Guardsman + Coastal Piracy / Whirlwind Technique / Elemental Bond | A | UU cards 57-63% on curve |
| Raise the Palisade / Counterspell / Righteous Fury + Coastal Piracy | A | |
| Wan Shi Tong / Fiend Hunter + Coastal Piracy | A | read B until the 2026-09-29 classifier fix (G-67) |
| Vault Guardsman + Dawn of a New Age | A | read B until the 2026-09-29 classifier fix (G-67) |

Second wave, measured on top of the core pair (still A, protection 6): +Wan Shi Tong
−The Eagles Are Coming!, +Flowering of the White Tree −Duty Beyond Death, +Multiversal
Recruitment −Starry-Eyed Skyrider (interaction 13 now that Wan Shi Tong's tuck counts).
Every remaining unprotected UNOWNED card is an engine
or interaction piece, so a second wave has to cut owned cards.

| Card | Verdict | Why, from text |
|---|---|---|
| Vault Guardsman | ★★★ | convoke; "exile target artifact or creature an opponent controls until this creature leaves", copied by all three enters-doublers |
| Inspiring Call (owned) | ★★★ | instant; draws per creature with a +1/+1 counter, and they gain indestructible |
| Wan Shi Tong, All-Knowing | ★★★ | enters: tuck a nonland permanent (copied ×3), each tuck makes two Spirits (doubled). UU 63% T5; counted as removal since the classifier fix |
| Multiversal Recruitment | ★★ | non-legendary token copy of Elesh Norn or Starfield Vocalist = another multiplier; flashback |
| Flowering of the White Tree | ★★ | legends +2/+1 and ward {1}, the rest +1/+1; ward covers Katara |
| Coastal Piracy | ★★ | draw per creature connecting; UU 57% T4 |
| Whirlwind Technique | ★★ | draw 2 discard 1 + airbend two (own: re-buy enters triggers, feeds Appa, Steadfast Guardian) |
| Black Panther, Wakandan King | ★★ | 2-drop legend; counters on lands per creature entering (Toph's power), copied by the doublers |
| Beastmaster Ascension | ★★ | go-wide finisher, one wide attack turns it on |
| Andúril, Narsil Reforged | ★★ | counters on every creature per attack, two with the city's blessing |
| Raise the Palisade | ★ | mass bounce of every type but one (name Ally); returns your non-Allies too |
| Righteous Fury | ★ | destroy all tapped creatures, pre-combat that is their attackers |
| Counterspell | ★ | UU 44% T2 |
| Captain Marvel, Shooting Star | ★ | seven mana; enters/attacks exile |
| Dawn of a New Age | ★ | draws each end step, one per creature on entry; counted as draw since the fix |
| Fiend Hunter | ★ | exile until it leaves, copied ×3 but all return together |
| Katara, Waterbending Master | ◇ | needs spells on the opponent's turn |
| Ephemerate | ◇ | re-buys enters triggers, but blink erases +1/+1 counters (G-42) |
| Return to the Ranks, Match the Odds, Elemental Bond, Loki, Commander's Plate, Rivendell | ◇ | situational or overlapping |
| Empty City Ruse, Tangle, Comeuppance | ◇ | fogs; not interaction |
| Air Nomad Student, Concerted Effort, Dramatic Reversal, Mystic Remora, Training Grounds, Thriving Isle, Ant-Man, Reformed Rogue | △ | little for this engine |
| Don't Move | ✗ | "whenever a creature becomes tapped, destroy it" kills your own attackers and convoke |
| Mister Fantastic | ✗ | illegal: R in identity |

### Batch 4 — applied, and the cut candidates for the rest (2026-09-29)

**Applied:** Vault Guardsman −Earth Kingdom Protectors, Flowering of the White Tree −Duty
Beyond Death, Multiversal Recruitment −Starry-Eyed Skyrider. Now interaction 12 (clears the
scaled A line), card advantage 6 (sum 18 against 19): **one more counted draw reaches A.**
Protection 6 -> 5 (both cuts granted indestructible; Flowering's ward replaces one).

Cut candidates, measured one pair at a time on scratch copies. Primaries are DISTINCT so all
nine could land together; protected cards are never offered.

| Add | Primary cut | Floor | Alternates (floor) |
|---|---|---|---|
| Wan Shi Tong, All-Knowing | Katara, Water Tribe's Hope | A | Aang, Airbending Master (A); Aang, the Last Airbender (A) |
| Inspiring Call | The Eagles Are Coming! | A | Hermitic Herbalist (A); White Lotus Reinforcements (A) |
| Dawn of a New Age | Arcane Signet | A | The Millennium Calendar (A, spice); Belladonna Took (A) |
| Coastal Piracy | Dazzling Theater // Prop Room | A | Niko, Light of Hope (A); Sokka, Lateral Strategist (B) |
| Whirlwind Technique | Aang, Airbending Master | A | Aang, the Last Airbender (A); The Earth King (A) |
| Black Panther, Wakandan King | Hermitic Herbalist | B | The Astonishing Ant-Man (B); Arcane Signet (B) |
| Beastmaster Ascension | White Lotus Reinforcements | B | The Millennium Calendar (B); An Unexpected Party (B) |
| Fiend Hunter | Aang, the Last Airbender | A | Allies at Last (B); Ty Lee, Chi Blocker (B) |
| Andúril, Narsil Reforged | The Astonishing Ant-Man | B | Belladonna Took (B); White Lotus Reinforcements (B) |

Cautions: Dawn's and Black Panther's primaries are two of the three nonland mana sources, so
take an alternate for one if both go in. Swapping like for like on the counted axis (Coastal
for Sokka, Fiend Hunter for Allies at Last or Ty Lee) cannot move the floor. Ty Lee is an Ally,
so its "tap up to one target creature" is copied by Katara, Roaming Throne and the three
enters-doublers — it may be the stronger card here. Black Panther's "{3}: Move … and draw a
card" is real card advantage the classifier does not count.

## 5. Consolidated plan (live)

**Measured on a scratch copy (Tier 1 package, 2026-09-29):**

| | Now | With the 8 swaps |
|---|---|---|
| Card advantage | 5 | 8 (repeatable 2 → 4) |
| Interaction | 11 | 12 |
| Anthems | 2 | 4 |
| Creatures | 46 | 41 |
| Average MV | 3.39 | 3.55 |

Per 60 cards, interaction ≈7.2 and interaction + card advantage ≈12, which is A density.
It is 100 cards and legal. Tier stays a human call.

### Tier 1 — the package, REVISED 2026-09-29 on the owner's decision

**Owner decision:** do NOT cut Appa, Loyal Sky Bison, Earth Kingdom General, Toph, the
Blind Bandit or Earth King's Lieutenant. Cut unowned craft targets in the list instead,
rares first. The owner raised wildcards in this conversation, so the Player Profile lets
them weigh. Each pair below is still like-for-like, graded from text, and the
by-the-numbers cost of each is stated.

| # | Add (owned) | Cut | Cut's craft | Trade, from text |
|---|---|---|---|---|
| 1 | The Great Henge | Kyoshi Warriors | owned C | a 4-mana 3/3 plus one Ally token, for a draw engine |
| 2 | Tribute to the World Tree | Relief Captain | U | a one-shot support 3, for counters on every small creature and draws off every big one |
| 3 | Inspiring Commander | The Blue Spirit | R | draw for draw. Blue Spirit draws only when a NONTOKEN creature enters DURING COMBAT, but it also gives a creature a turn flash. Commander draws on every power-≤2 creature, tokens included. Costs: the Jet, Rebel Leader pairing loses its half, and the deck loses the flash |
| 4 | An Unexpected Party | Rumor Gatherer | U | Gatherer draws at most once a turn ("if this is the second time this ability has resolved this turn, draw a card instead"). With Henge, Tribute and Commander in, a +2/+2 Ally anthem is worth more |
| 5 | Leyline Binding | Skyclave Apparition | R | Skyclave hits "nontoken permanent … mana value 4 or less" and leaves a body; Leyline hits ANY nonland permanent, at instant speed, for about {2}{W}. Both are doubled. Prayer of Binding (owned) STAYS |
| 6 | Buried in the Garden | Get Lost | R | by the numbers Get Lost is the more efficient answer ({1}{W}, instant). Buried is 4 mana, sorcery speed and an Aura, but it hits any nonland permanent, is doubled, and ramps |
| 7 | Silk, Web Weaver | Invasion Reinforcements | owned U | one token once, for a token per creature spell |
| 8 | Kellan Joins Up | Katara, Heroic Healer | U | the same effect: a +1/+1 counter on each other creature. Healer does it once, as an Ally, so Katara and Throne double it, on a lifelink body. Kellan Joins Up repeats it on each of 25 legends entering |

**Measured on a scratch copy:**

| | Now | Revised package |
|---|---|---|
| Card advantage | 5 | 7 |
| Interaction | 11 | 11 |
| Anthems | 2 | 4 |
| Average MV | 3.39 | 3.58 |

The deck is legal. Per 60 cards, interaction + card advantage ≈10.8, just under the A line
of 11; the first package reached it, mainly by cutting Rumor Gatherer's draw less often.

**Crafting this removes** from the deck's own list: 3 rares (The Blue Spirit, Skyclave
Apparition, Get Lost) and 3 uncommons (Relief Captain, Rumor Gatherer, Katara, Heroic
Healer). The 8 adds are owned per the owner. The library does not record 6 of them yet
(G-10), so `check` still lists them until an ingest.

**If the owner prefers unowned cuts for rows 1 and 7 too:** Earth Kingdom Protectors (U)
and Knight of Autumn (R) are the remaining unowned candidates, read from text:
- Protectors: a 1-drop that sacrifices itself for one Ally's indestructibility.
- Knight of Autumn: modal ETB (counters, artifact/enchantment removal, or 4 life).

The multipliers are unowned too (Elesh Norn, Roaming Throne, Virtue of Knowledge). They
are the thesis, so they are NOT offered.

**Header change to carry with the swaps:** add the four owner-kept cards to
`#: protect:`, so `cuts` and future tunes stop proposing them.

### Tier 1 status and the two open rows (2026-09-29, after the tooling change)

**Applied (commit 9b575b0):** rows 1, 2, 4, 5, 6 and 7. **Owner decision:** keep The Blue
Spirit and Katara, Heroic Healer (both now in `#: protect:`), so rows 3 and 8 need other
cuts. The adds stay: Inspiring Commander and Kellan Joins Up.

**The floor changed under this analysis (commit 6a7e53e).** A 100-card deck is now graded
per 60 cards, so the deck reads B, not A: at 100 cards, A needs interaction 12 and a sum of
19, and the deck has 11 and 7. That makes INTERACTION the axis to protect in the two open
cuts: every package that cuts an interaction piece widens the gap to A.

Measured on scratch copies (interaction · card advantage · protection):

| Pkg | Commander's cut | Kellan's cut | Int | CA | Prot | Gap to A |
|---|---|---|---|---|---|---|
| a | Earth Kingdom Protectors (U) | Knight of Autumn (R) | 10 | 8 | 5 | +2 int |
| b | Forecasting Fortune Teller (owned) | Duty Beyond Death (owned) | 11 | 7 | 5 | +1 int, +1 sum |
| c | Katara, Water Tribe's Hope (owned) | Allies at Last (owned) | 10 | 8 | 6 | +2 int |
| d | Earth Kingdom Protectors (U) | Arcane Signet (C) | 11 | 8 | 5 | +1 int |
| e | Earth Kingdom Protectors (U) | Aang and Katara (R) | 11 | 8 | 5 | +1 int |
| f | Earth Kingdom Protectors (U) | Jet, Rebel Leader (R) | 11 | 8 | 5 | +1 int |
| h | Earth Kingdom Protectors (U) | Aang, Airbending Master (M) | 11 | 8 | 5 | +1 int |

Read from text:
- **Protectors is the Commander cut in every good package.** It is a 1-drop whose only
  job is "Sacrifice this creature: Another target Ally you control gains indestructible";
  it has no enters trigger, so none of the five multipliers touch it. Heroic Intervention
  stays as the anti-sweeper answer.
- **Knight of Autumn is no longer a good cut.** It is interaction AND one of the deck's
  noncreature answers ("Destroy target artifact or enchantment"). Package a was the
  recommendation before the floor scaled; it is the worst unowned option now.
- **Kellan's slot, by the owner's unowned-first rule:** Aang, Airbending Master (mythic,
  the biggest saving) or Arcane Signet (common, the smallest). Airbending Master's tokens
  come "at the beginning of your upkeep … for each experience counter", and a counter
  only when creatures "leave the battlefield without dying"; the deck's other exits of
  that kind are the two Appas and Niko, so it builds slowly. Signet is one of three
  nonland mana sources beside 38 lands.
- **Not recommended:** Jet (f) is The Blue Spirit's other half, which the owner kept, and
  Aang and Katara (e) makes "X 1/1 white Ally creature tokens, where X is the number of
  tapped artifacts and/or creatures you control" on enter AND attack, which Katara,
  Throne and all four token doublers multiply.

**Owner's pick, same day:** Kellan Joins Up in for Forecasting Fortune Teller (applied);
Inspiring Commander parked in the flex block against Earth Kingdom Protectors. Fortune
Teller's Clue was a counted draw, so card advantage fell 7 to 6, and the A gap is now one
answer AND one draw. Measured on scratch copies, cutting Aang, Airbending Master: any plain
answer reaches interaction 12 but a sum of 18 (still B). Water Whip (TLE) or Origin of Iron
Man (MSC) reach A alone, because each also draws two. Any answer plus the flexed Inspiring
Commander also reaches A.

### Tier 2 — a second wave, if play shows the need

Adds, in order:
1. Reed Richards
2. Silver Surfer
3. Cyclonic Rift
4. Fractured Identity
5. Black Panther, Wakandan King
6. Contagion Engine
7. Virtue of Loyalty
8. Echo
9. Triumph of the Hordes
10. Leonin Warleader
11. The Falcon

Cut candidates for this wave, weakest first, each read from text:
- Katara, Water Tribe's Hope: 60% castable on turn 5.
- Allies at Last: creature-only removal.
- Forecasting Fortune Teller: a single Clue.
- Hermitic Herbalist: a mana dork; it only earns its slot beside Badgermole Cub.
- Duty Beyond Death.
- Earth Kingdom Protectors.

The Millennium Calendar is fun-budget: keep it unless a slot is truly needed.

### Tier 3 — fun budget / situational

The Mechanist, Badgermole Cub, Bloom Tender, Hindering Light, Suki, Shi'ar Soldier,
Kellan, the Kid, Akroma's Memorial, Storm, Rumble Arena.

### Protect list (what `cuts` cannot see — F9)

`cuts` ranks these near the top of its weakest-fit list, and they are not weak:
- **Path to Exile and Swords to Plowshares** — ranked #1 and #7, a shortlist artefact.
- **Dazzling Theater** — ranked #2; convoke across 41–46 creatures.
- **Virtue of Knowledge** — ranked #3; an enters-doubler.
- **Heroic Intervention** — the sweeper answer (F7).
- **Starfield Vocalist, Elesh Norn, Roaming Throne, Doubling Season** — multipliers.
- **Bard, King of Dale** — the draw and token doubler (F3b).

### Not for this deck

**The Marvel Heroes cluster (O6)** is about a dozen cards and a `/draft-deck` candidate.
