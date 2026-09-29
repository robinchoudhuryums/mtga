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

(none yet)

## 3. Cross-batch observations

(none yet)

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`

## 5. Consolidated plan (live)

(after batch 1)
