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

## 5. Consolidated plan (live)

After batch 1, before cuts are chosen:

- **Tier 1 adds:** Inspiring Commander, An Unexpected Party, Leyline Binding.
- **Tier 2 adds:** Cyclonic Rift, Leonin Warleader, Virtue of Loyalty, Echo, The Falcon.
- **Tier 3 (fun budget / if slots allow):** Suki, Shi'ar Soldier.

Cuts come after batch 3, from `deck.py cuts` plus a text read.
