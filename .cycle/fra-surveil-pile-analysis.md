# FRA surveil/scry pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS (2026-10-05).** Goal: a NEW deck built on scry/surveil, primarily blue,
open to mono-U, UW, UB or Esper. Delete once the deck is drafted and the findings are folded
into its `#: notes:`. A scratchpad, not a source of truth — decks/ are.

**Source list:** the owner's 2026-10-05 paste — 65 nonland cards + 21 lands ("lands are a
frame of reference for what I have"). For a NEW deck nothing is "already in" it, so the dedup
removes nothing: copies are shared across decks, and 30 of the 86 lines already sit in some
roster deck (Ral Zarek ×5, Kaito ×2, the shocks/Verges/Hidden Lair widely). Names that needed
their full `Front // Back` form: Diviner of Victory, Variable Chaser, Fatehold Chronologist,
Semester Foreseer, The Legend of Kuruk, Ultimecia, Time Sorceress.

**Related open work:** `fra-bant-pile-analysis.md`'s **deck 2 (UW Jace, draft C)** is still
undrafted, and `fra-rgu-pile-analysis.md` §3 measured the same blue Jace core in mono-U and
in all four pairs (mono-U: 0 cards under 90% on curve, against 12–19 for any pair). This pile
is that deck seen from the surveil side — **the deck drafted from here should BE deck 2**, not
a second Jace deck beside it. Close that question in both docs when this lands.

## 1. The decision framework

1. **The resource is the scry/surveil EVENT, and payoffs read it at two cadences.** Per-event
   payoffs scale with how many separate events you make: Matoya (draw), Proft (pay {2}: draw
   + counter), Denzilore Fatehold (+1/+1 counter on EVERY creature), Diviner of Victory
   (+1/+1). Once-per-turn payoffs need one event a turn and no more: Saheeli, Consul (Thopter),
   Prudent Fateseer (+1/+0 team), Desperate Futurescribe, Surveillance Phantasm (may attack),
   Planetarium (free cast), Proctor's recursion. **So a source is graded on REPEATABLE events
   per turn cycle, not on how many cards it looks at.** Surveil 3 once is worse for this deck
   than surveil 1 three times.
2. **The Jace token IS the repeatable surveil engine.** Every empower card makes (or loads) a
   token with "−1: Surveil 1", activatable once per turn — so empower N ≈ N turns of one
   surveil event each, or N/3 draws. That makes the empower cards SOURCES for rule 1, not just
   loyalty. Jace's Machinations (instant-speed loyalty on ANY player's turn) doubles the rate
   for the turn it is cast. **The role model cannot see any of this** (the token's abilities
   live in reminder text, which `classify_roles` strips — the Bant doc's rule 2), so every
   empower card's card advantage reads zero in `stats`/`tier`.
3. **Other repeatable sources** (once per turn unless noted): Chandra, Chill (+1 surveil 1, and
   it returns a noncreature nonland card it bins), Planetarium ({1},{T}: scry 2), Surveillance
   Phantasm ({3}{U}), Unwelcome Sprite (per spell on THEIR turn), Ral Zarek (+1 surveil 2),
   Kaito (0: surveil 2), Wretched Doll / Joo Dee (black {B},{T}), Fear of Surveillance /
   Redwing (on attack), Compassionate Healer (on tap). One-shots: Opt, the bounce-surveil
   instants, Yuriko, Peer Review, Clone Saga, Kuruk (two chapters), ETB surveil creatures,
   surveil lands.
4. **Castability is the colour question, and the prior measurement already answers most of
   it.** The blue core is a UU deck — Countersculpt, Chandra, Lyra, Seasoned Cryomancer,
   Theorist, Sphinx, Kuruk {2}{U}{U}, Jace RS {3}{U}{U}, Ruric {4}{U}{U}. A second colour costs
   those 15–30 points each on curve (fra-rgu §3). **A second colour must BUY something blue
   cannot:** W buys Denzilore (the best per-event payoff, but {1}{W}{U}{U}), Futurescribe,
   Proctor, Prudent Fateseer, Saheeli, Way of the Healer, Fatehold Charm, Erode; B buys
   Vraska's Final Mercy ({B}{B} — the best removal, 40% on curve in the UB measurement),
   Kaito, Ultimecia, Ral, Garruk, Sanctum Lurker. Measure each against mono-U (§3).
5. **Jace, Reality Sculptor's +1 empowers by ISLAND count**, Theorist's Sanctum is an Island
   that enters untapped if you behold a Jace (the token counts) and sinks {2}{U} into empower
   2, and the Annex lands (Fatehold W/U, Theorix U/B) are untapped with ANY planeswalker out —
   the Jace token included. Mono-U maximises the first two.
6. **Surveil vs scry is not neutral.** Surveil fills the graveyard: Yuriko's −X/−0, Seasoned
   Cryomancer's graveyard draw, Cruel Calculations (counts cards put from YOUR library into
   your graveyard this turn if you target yourself — surveil counts), Chandra's return. Scry
   bottoms. Nothing here mills the deck out; Fblthp's empty-library win is not a plan.
7. **Interaction is blue tempo by default** — bounce, counters, taps, auras. Count the answers
   to a resolved noncreature threat (Banishing Betrayal / Unauthorized Exit / Desculpting
   Blast bounce any nonland permanent; Plan for All Outcomes tucks one; counters stop them
   upstream). The A floor needs interaction ≥7 (midrange).
8. **Lyra's token needs THREE draws in one turn** — Matoya, Proft and Theorist (on THEIR draw
   step, so their end step) are what make it real. Count draw sources before grading her.

## 2. Standing error list

- **Matoya, Archon Elder is NOT in the pile** and is the strongest per-event payoff in the
  format for this deck ({2}{U} 1/4, draw on every scry/surveil). Build the optimal list.
- **Fatehold Chronologist and Semester Foreseer are mono-U castable** — the front faces are
  `{1}{W/U}` and `{3}{U}`; only Peer Review (`{2}{W/U}`) carries the hybrid, also castable.
  Their `W/U` identity is NOT a colour commitment (G-58).
- **Refute Destiny only exiles a GREEN or BLUE creature/planeswalker** — a sideboard card.
- **Enlightened Confidant surveils only if you gained life that turn** — no lifegain here.
- **Emrakul, the Exigent Doom** costs {10}; its {3} exile-from-hand mode makes a land tap for
  {C}{C}. A colourless ramp/top-end curiosity, not a surveil card.
- **The Echoverse Fulcrum** is a {2} loot + a {5} wrath — interaction, not surveil.
- **Ruric Thar is a {4}{U}{U} prowess flier** — a spells-deck finisher, not a surveil payoff.
- **Liliana the Repentant MILLS** on each creature/walker entering — that is not surveil and
  triggers no payoff here.
- **Fear of Surveillance, Compassionate Healer** surveil/scry only on attack/tap — once per
  turn, and only on a board that can attack.
- Ownership in this repo reads 0 for every FRA card (the set is not ingested). Irrelevant to
  the build (Player Profile); craft cost is reported at the end as information.

## 3. Cross-batch observations — the colour answer

Measured 2026-10-05 on scratch 60s built from the SAME blue core (both Jaces, Chandra, Theorist's
Proxy ×2, Machinations, both blue Ways, Plan, Protege's Awakening, Countersculpt ×2, Matoya,
Proft, Lyra, Cryomancer, Sphinx ×2, Chronologist ×2, Opt ×2, the two bounce-surveil instants),
24 lands each. "Payoffs" = cards whose text reads a scry/surveil event (rule 1).

| Build | Floor | Int | CA | Board pwr | Payoffs | Sources | Cards < 90% on curve | Worst |
|---|---|---|---|---|---|---|---|---|
| mono-U | A | 12 (+5?) | 9 (+5?) | 30 | **5** | U 24 | **0** | Countersculpt 91% |
| **UW** (light white, 9 W cards) | A | 11 (+6?) | 7 (+6?) | 34 | **8** | U 20 / W 14 | 8 | Countersculpt 82%, Erode 86%, Denzilore 87% |
| UB (Final Mercy ×2, Kaito, Ral, Garruk, Ultimecia, Lurker, Way) | A | 12 (+5?) | 8 (+5?) | 28 | **3** | U 21 / B 12 | 9 | Final Mercy 51%, Ral 58%, Garruk 71% |

- **The floor does not decide this — every version is A.** The question is the THEME versus
  the MANA, and they point in different directions.
- **The theme lives in white-blue.** Of the nine Standard cards that read a scry/surveil event
  (`pool.py --regex 'whenever you (scry|surveil)|scry or surveil'`), FIVE are W/U or W:
  Denzilore Fatehold, Proctor of Potential, Desperate Futurescribe, Prudent Fateseer, Saheeli.
  Mono-U has Matoya, Proft and Diviner, plus Surveillance Phantasm. **G-59: an archetype's
  viability is its payoff count**, and UW has 60% more payoffs than mono-U (8 against 5).
- **UW's mana cost is real but smaller than the earlier UW measurement**, because this pile's
  white is a light touch (no WW card is kept; Saheeli, the only WW payoff, is left out). 8
  cards under 90% at a worst of 82%, against 17 under at 65% in fra-rgu §3's UW (which carried
  Elspeth and the Bant white). Floodfarm Verge ×2 and Gleaming Bastion ×2 beat a second Beach
  and both Theorist's Sanctums (W 12→14 for U 21→20).
- **UB is rejected on mana and on the theme**: the black cards are removal and walkers, not
  payoffs (3 payoffs, the fewest), and the BB cards — the reason to be black — sit at 51–71%.
- **Esper** was not built: it would add a third double-pip colour to a deck whose problem is
  already double pips.
- **Jace, Reality Sculptor's alt-win is slower in UW** (14 Islands counting Fountain and the
  Sanctum, against 23 in mono-U). In UW he is a +X loyalty battery and a −3 Fog, not a win.
- **Board power is low in every version (28–34, roster p10 37)**, but the real board is
  bigger than it reads — Cadets, Illusions and the Jace token are tokens (G-86 reads them as
  zero), and Denzilore puts a counter on EVERY creature per event. Zero protection everywhere.
- **`similar`: ≤2 shared nonland cards with any roster deck** — distinct.
- **This pile IS the Bant doc's deck 2** (UW Jace). The UW build here is that deck with the
  surveil payoffs it lacked; do not draft both.

### Tooling holes (Stage 4 — recorded, not fixed)

- **`engines` has no scry/surveil engine.** It reports graveyard/tokens/counters for the UW
  draft and nothing about the deck's actual enabler ↔ payoff loop (15 sources, 8 payoffs). Nine
  Standard payoffs exist; a `surveil` pair would be one cue on each side.
- **Empower card advantage stays invisible** (rule 2; the Bant doc's rule 2) — 14–17 empower
  cards per build, each a Jace token whose surveil/draw lives in reminder text.
- **`screen` rated no card KEY**, Denzilore and Matoya included — the deck's central themes are
  generic tags (card draw, graveyard, tokens), and `surveil` is one of 15.

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`. Rules cited by §1 number.

### Batch 1 — the blue and gold FRA cards (plus the outside-pile Jace/surveil cards)

| Card | Verdict | Note |
|---|---|---|
| Matoya, Archon Elder (FIN, outside pile) | ★★★ | per-event DRAW (r1); with the Jace token every turn is a free card |
| Denzilore Fatehold | ★★★ (UW) | per-event counter on EVERY creature (r1); flash flier |
| Proft, Consulting Detective | ★★★ | per-event draw + counter for {2}; a mana sink that grows |
| Proctor of Potential | ★★★ (UW) | a SOURCE on every creature/token entering (Cadets, Illusions, Thopters) and recursion gated on the theme |
| The Theorist, Jace Beleren | ★★★ | draws on THEIR draw step (r8), +1 Illusions feed Proctor; real Jace for Countersculpt/Sanctum |
| Chandra, Chill of Compliance | ★★★ | repeatable surveil that returns spells (r3) |
| Jace's Machinations (outside pile) | ★★ | empower 8 + a second activation on their turn (r2) |
| Theorist's Proxy (outside pile) | ★★ | 2-mana flash empower 3 |
| Diviner of Victory | ★★ | 1-drop that grows per event + a bounce/surveil spell |
| Fatehold Chronologist | ★★ | mono-U castable (error list); 2 bodies + surveil |
| Desperate Futurescribe | ★★ (UW) | 3/4 flier, a counter a turn once you surveil |
| Seasoned Cryomancer | ★★ | loot 2 + stun, and draws again from the yard |
| Sphinx of False Conclusions | ★★ | flash 4/2 flier, loots on attack, returns as a token |
| Lyra, Tolarian Archangel | ★★ | 3/3 flier for 3; Angels once Matoya/Proft/Theorist reach 3 draws (r8) |
| Countersculpt | ★★ | UU counter + empower 1; the worst-cast card in UW (82%) |
| Way of the Cryomancer | ★★ | empower 5 + every walker copies a spell |
| Way of the Mind Sculptor | ★★ | empower 5 + the token's −3 draws 2 |
| Plan for All Outcomes | ★★ | answers ANY nonland permanent (r7) + empower per turn |
| Jace, Reality Sculptor | ★★ mono-U / ★ UW | Island-scaled (r5) |
| Fatehold Charm (outside pile) | ★★ (UW) | counter-a-creature / bounce / empower+draw |
| Opt | ★★ | the cheapest event |
| Protege's Awakening | ★ | empower 6 + a card at 4 mana |
| Way of the Healer | ★ (UW) | empower 5; every walker −2: Cadet + surveil (feeds Proctor) |
| Prudent Fateseer (outside pile) | ★ (UW) | once-per-turn team +1/+0; hybrid, mono-U castable |
| Mindseeker Oculus (outside pile) | ★ | empower 4 on a 2/1 |
| Icy Reception | ★ | soft counter or −5/−0 |
| Infinite Coursework | ★ | aura removal for a creature |
| Yuriko, Hope from the Shadows | ★ | flash 1-drop: surveil 2 or −X/−0 |
| Semester Foreseer | ★ | 3/4 + surveil + a prepared Cadet; mono-U castable |
| The Legend of Kuruk | ★ | scry 2 + draw ×2, then a token maker |
| Surveillance Phantasm | ◇ | a payoff that only lets itself attack; {3}{U} surveil |
| Unwelcome Sprite | ◇ | repeatable on their turn — real only with many flash cards |
| The Clone Saga | ◇ | surveil 3 once, then a creature copy |
| Planetarium of Wan Shi Tong | ◇ | 6-mana free cast a turn; strong late, nothing the turn it lands |
| Saheeli, Consul of Oversight | ◇ | a once-a-turn Thopter, but {3}{W}{W} at 14 W sources |
| Ruric Thar, Biomagus | ◇ | a prowess finisher, not a theme card |
| Variable Chaser | ◇ | the Wheel is symmetric |
| Geist of Saint Thalia | △ | ~16 noncreature spells; a 1/2 flier |
| Tetsuko Umezawa | △ | few 1-power bodies |
| Cruel Calculations | △ | counts only same-turn library→yard; surveil 1–2 → draw 1–2 for 3 |
| Fblthp, Impossibly Lost | △ | needs combat damage; the empty-library win is not a plan (r6) |
| Perfected Theory, Traxos | △ | off-theme |
| The Echoverse Fulcrum | ◇ | a colourless wrath — fights your own board |
| Emrakul, the Exigent Doom | ✗ | {10} |
| Refute Destiny | ◇ | green/blue only — sideboard |
| Enlightened Confidant | ✗ | needs lifegain (error list) |

### Batch 2 — the older-set and black cards

| Card | Verdict | Note |
|---|---|---|
| Banishing Betrayal / Unauthorized Exit | ★★ | identical: bounce any nonland permanent + surveil 1 (r7) |
| Erode | ★★ (UW) | 1-mana removal for a creature or walker |
| Falcon, Winged Wonder | ◇ | 5 mana; Redwing surveils on attack |
| Fear of Surveillance, Compassionate Healer | △ | once-a-turn, attack/tap only |
| Simulacrum Synthesizer, Cerebral Download, Valkyrie Aerial Unit | ✗ | artifact-count cards; ~0 artifacts here |
| Vraska's Final Mercy | ★★★ card / ✗ here | best removal in the pile, 51% on curve at {B}{B} |
| Kaito, Bane of Nightmares | ★★ (UB) | 0: surveil 2 + draw; hexproof creature on your turn |
| Ral Zarek, Guest Lecturer | ★ (UB) | +1 surveil 2, but BB at 58% |
| Garruk, Ultimecia, Sanctum Lurker | ◇ | UB-only, off-theme or BB |
| Rewrite Regrets, Way of the Necromancer, Twilight Diviner, Winter | ◇ | black graveyard/walker cards |
| Wretched Doll, Joo Dee, Umbral Collar Zealot, Namazu Trader, Spider-Man Noir | △ | repeatable surveil, but black and sacrifice-gated |
| Liliana the Repentant | ✗ | MILLS, which is not surveil (error list) |
| Massacre Girl | ✗ | drain on deaths; no engine for it here |

### Lands (frame of reference — UW)

Take: **Hallowed Fountain ×4, Floodfarm Verge ×2, Gleaming Bastion ×2, Fatehold Annex ×2**
(untapped once the Jace token is out — r5), **Deserted Beach**, **Theorist's Sanctum** (an
Island that empowers). Optional: Temple of Enlightenment (a scry EVENT on entry, but tapped).
Out: Surveillance Room ({C} in a UU deck), Hall of Echoes, Hexhaven Dueling Arena / Skycoach
Waypoint (only 4–5 prepare creatures), every B land.

## 5. Consolidated plan (live)

**Recommendation: UW, blue-heavy (U 20 / W 14), 24 lands.** The white cards ARE the theme's
payoffs (§3), they cost ~5–10 points of cast-on-curve, and no white card has WW. **Fallback:
mono-U** — every card ≥91% on curve and the faster Jace RS alt-win, but 5 payoffs instead of 8.
Both are floor A. Drafting is `/draft-deck`; this file is retired when that lands, and the Bant
doc's deck 2 closes with it.

**UW draft (60) — scratch-measured, floor A, 8 payoffs:**
- Creatures (17): Diviner of Victory, Theorist's Proxy ×2, Proft, Fatehold Chronologist ×2,
  Proctor of Potential ×2, Matoya, Lyra, Mindseeker Oculus, Seasoned Cryomancer, Prudent
  Fateseer, Sphinx of False Conclusions ×2, Desperate Futurescribe, Denzilore Fatehold
- Walkers (3): Chandra, Chill of Compliance; The Theorist; Jace, Reality Sculptor
- Spells/enchantments (16): Opt ×2, Erode, Countersculpt ×2, Banishing Betrayal, Unauthorized
  Exit, Fatehold Charm, Icy Reception, Jace's Machinations, Infinite Coursework, Way of the
  Cryomancer, Plan for All Outcomes, Protege's Awakening, Way of the Healer, Way of the Mind
  Sculptor
- Lands (24): Hallowed Fountain ×4, Floodfarm Verge ×2, Gleaming Bastion ×2, Fatehold Annex ×2,
  Deserted Beach, Theorist's Sanctum, 9 Island, 3 Plains

**Weakest slots (first to trade):** Icy Reception, Infinite Coursework, Mindseeker Oculus,
Protege's Awakening, Prudent Fateseer. **Bench, if a slot opens:** Yuriko, Semester Foreseer,
The Legend of Kuruk, Planetarium, Unwelcome Sprite.

**PROTECT (what `cuts` cannot see):** every empower card (their card advantage is reminder text,
r2); Matoya, Proft, Denzilore, Proctor (value is per EVENT, and `engines` has no surveil
engine); Jace's Machinations (it doubles the token's rate).

**Craft cost (information only):** 0 of the FRA cards read as owned because the set is not
ingested (run `/ingest` with a collection export first). Outside FRA the draft uses Matoya (FIN),
Opt, Erode, Banishing Betrayal, Unauthorized Exit and the lands.
