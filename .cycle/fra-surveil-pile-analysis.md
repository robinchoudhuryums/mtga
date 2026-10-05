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

(pending — drafts measured below)

## 4. Running verdicts

(pending)

## 5. Consolidated plan (live)

(pending)
