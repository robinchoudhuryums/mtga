# Feather pile (2026-11-11) — analysis (TEMPORARY working doc)

**Status: ROUND 2 APPLIED 2026-11-11** (15 swaps). Open: Raiyuu and Lightning await owner
picks for their alternate cuts; step 2 (Star Trek) waits on the 2026-11-13 pool refresh. Delete once the swaps land and the findings are folded into deck
56-historic-brawl's `#: notes:`. A scratchpad, not a source of truth — decks/ are.

**Source list:** the owner's 107-line pile (2026-11-11). 4 lands already in the deck; Picard,
Leading by Example and Kirk, Enterprising Captain are Star Trek cards not yet in the repo pool
(same 2026-11-13 refresh as the queued step-2 cards). 101 graded on the Builder project
`builds/feather` (pile F), board https://claude.ai/artifact/1UBYAUTmsCBW4TrGtcsK3Q.

## 1. The decision framework

Live vector (2026-11-11, after Builder round 1): floor B · interaction 12 (+2 unread) ·
card advantage 6 · protection 17 · board power 74 · avg MV 2.92 · 37 lands (W 26 / R 23).
Step 2 (queued for 11-13): +Pah-Wraith −Collective Inferno, +La'An −Iron Fist, +Exploratory
Mission −Valorous Stance, +Worf −Titan's Strength, +Combadge −Delney.

1. **Feather's recursion is the axis.** An instant or sorcery that targets a creature YOU control
   returns to hand each end step, so its real cost is "once per turn, forever". Grade such a card
   as a permanent, not a one-shot. A spell that targets only the opponent's creature, or no
   creature, is a one-shot (no return).
2. **One protected body wins.** Value per card is measured on ONE big creature: power doubling,
   double strike, trample, evasion, protection. Go-wide payoffs only count if they also make the
   lone attacker bigger (Team Avatar, Zada copies).
3. **Card advantage is the short axis (6).** A repeatable draw / impulse source earns a slot over a
   comparable non-draw card. Interaction is at the A line (12); don't spend it.
4. **Opponent-benefit removal is out by owner's rule** (Swords to Plowshares, Path to Exile —
   life or a land). Bites and fights that scale with the body are preferred (they also return).
5. **Equipment is the second engine** (Embercleave, 3 Swords, Shadowspear, Maul, War-Whip, Kaldra,
   Boots; Bruenor, Reyav, Akiri, Danitha, Stoneforge, Sigarda's Aid). An Equipment or an
   equipment payoff is judged against that package, not alone.
6. **Curve is already heavy (2.92).** A 5+ drop has to beat Kaldra / Pah-Wraith / Chandra's
   Ignition for a top-end slot.
7. **Kept on the owner's call** (not cut candidates): Pain for All, Mabel, Stingerback Terror, The
   Sentry, Luke Cage, Team Avatar, The Fire Crystal, Kaldra Compleat, Swiftblade Vindicator.
8. **Already decided** this week, no re-grade unless the text says otherwise: Swords to
   Plowshares (out, rule 4), Team Tactics (cut, double strike redundant), Two-Handed Axe (bench).

Structurally invisible to the tools: rule 1 (no model knows Feather returns spells), lifegain
on the body, and "attacks alone" vs go-wide polarity.

## 2. Standing error list

1. A spell that targets ANY creature (not "you control") still returns with Feather when you
   aim it at your own creature: Seize the Day ("untap target creature"), Legion Leadership,
   Onward. Read the target clause, not the wording "you control".
2. A modal spell returns if the mode you chose targets your creature (Mishra's Command with the
   pump mode, Giantfall's bite). Go Ninja Go returns only on its blink mode, which resets the body.
3. Extra-combat cards that don't target (Savage Beating, Great Train Heist, Resurgence) are
   one-shots; the repeatable ones are Seize the Day (Feather) and the creatures (Raph & Leo,
   Aurelia the Warleader, Raiyuu, Desert Were-Worm).

## 3. Cross-batch observations

- **Extra combats are a real sub-theme in this pile** (Seize the Day, Raph & Leo, Aurelia the
  Warleader, Raiyuu, Great Train Heist, Savage Beating, Response // Resurgence, Desert Were-Worm,
  Moraug, Godo). Each extra combat re-triggers the three Swords, Akiri, Pain for All, Laelia and
  Jor Kadeen, so it multiplies the Equipment engine rather than competing with it. Not a variant
  signal: it slots into this deck.
- **Lifegain becomes card advantage** through Bre of Clan Stoutarm (free spell up to the life
  gained) — the deck already has lifelink on the body (Elspeth counters, Shadowspear, Lightning).
- Oil / Phyrexian cards (ONE block) and Dog / token packages are a different deck; all ✗/△.
- Star Trek: Kirk ★★ (impulse draw on attack at 8+ power) and Picard ◇ queue with step 2.

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

Per-card reasons and stars live on the Builder project (pile F). Summary of 101 graded:
- ★★★ (8): Seize the Day, Raph & Leo (owned), Aurelia the Warleader (owned), Bre of Clan
  Stoutarm (owned), Thorin Mountain-king (owned), Furious Rise, Bionic Blow, Legion Leadership.
- ★★ (22): Éowyn, Mishra's Command, Great Train Heist (owned), Jor Kadeen, Lightning (owned),
  Fang, Heartfire Hero (owned), Chainsaw (owned), Desert Were-Worm (owned), Origin of Thor
  (owned), Frontline Rush (owned), Lunar Frenzy, Raubahn, Savage Beating, Response // Resurgence,
  Raiyuu, The Akroan War, Huatli, Onward // Victory; queued: Kirk.
- The rest ★ / ◇ / △ / ✗ (oil, Dogs, go-wide, opponent-benefit removal, 7-drops).

## 5. Consolidated plan (live)

Tier 1 package (measured: floor B → A, interaction 12 → 13, card advantage 6 → 7, protection
17 → 15, board power 74 → 77, avg MV 2.92 → 3.03, legal):

| Add | Cut | Why the cut |
|---|---|---|
| Seize the Day | Red Hulk | 6-mana body; an extra combat every turn beats a sixth big body |
| Raph & Leo (owned) | Boros Reckoner | the Self-Destruct double is a narrow line |
| Aurelia, the Warleader (owned) | Monastery Mentor | Akroma's Will kept (owner); Monks are a go-wide side line |
| Bre of Clan Stoutarm (owned) | Sigarda's Aid | low-power enabler; Bre is card advantage |
| Furious Rise | Defiant Strike | a card every turn vs. one cantrip |
| Bionic Blow | Lightning Helix | a returned, scalable bite vs. a one-shot 3 |
| Thorin, Mountain-king (owned) | Restoration Magic | protection is the deepest axis (17) |
| Legion Leadership | a Mountain | a land drop that is also a returned power doubler |

Package 2 (owner's list; measured with tier 1: floor A, interaction 13, card advantage 7,
protection 15, board power 76, avg MV 3.03): +Raiyuu −Seedglaive Mentor, +Great Train Heist
−Enter the Avatar State, +Response // Resurgence −Fiery Confluence, +Lightning −Agrus Kos,
+Sif's Spearmaster −Champion of the Flame; after the 11-13 refresh: +Kirk −Spinerock Tyrant,
+Picard −Boros Charm (Picard ◇; the weakest of the group).

Owner's board round 2 (2026-11-11): cuts Chandra's Ignition, Grand Abolisher, Maul of the Skyclaves,
Giver of Runes, Delney (plus Red Hulk, Boros Reckoner, Monastery Mentor, Titan's Strength, matching
the plan); Fiery Confluence kept. Paired: +Response // Resurgence −Chandra's Ignition, +Mishra's
Command −Grand Abolisher, +Éowyn −Delney, +Jor Kadeen −Giver of Runes, +Chainsaw −Maul. Full set
measured: floor A, interaction 16, card advantage 8, protection 15, board power 76, avg MV 3.02.
Combadge (step 2) loses Delney as its cut; Titan's Strength goes to Worf as planned.

Team Tactics re-read: its trample half was not weighed the first time. Still backup (★): it is
a second Temur Battle Rage under Feather, and both halves are covered.

Tier 2 options (◇ cut candidates: Seedglaive Mentor, Spinerock Tyrant, Monastery Mentor,
Enter the Avatar State, Fiery Confluence, Champion of the Flame): Éowyn, Mishra's Command,
Great Train Heist, Jor Kadeen, Lightning, Heartfire Hero, Chainsaw, Desert Were-Worm, Raiyuu,
Response // Resurgence. Queued for the 11-13 refresh with step 2: Kirk.

PROTECT (the ranking can't see their value): Seize the Day and Bionic Blow (Feather returns
them, rule 1), Bre (free spells from lifegain), the step-1 keeps (rule 7).

## 6. Round 2 applied (2026-11-11)

15 swaps landed: +Seize the Day −Red Hulk, +Raph & Leo −Boros Reckoner, +Aurelia the Warleader
−Monastery Mentor, +Bre −Sigarda's Aid, +Furious Rise −Defiant Strike, +Bionic Blow −Lightning
Helix, +Thorin −Restoration Magic, +Legion Leadership −Mountain, +Great Train Heist −Enter the
Avatar State, +Sif's Spearmaster −Champion of the Flame, +Response // Resurgence −Chandra's
Ignition, +Mishra's Command −Grand Abolisher, +Éowyn −Delney, +Jor Kadeen −Giver of Runes,
+Chainsaw −Maul of the Skyclaves. Live: floor A (tier unset), interaction 16 (+2 unread), card
advantage 8, protection 15, board power 75, avg MV 3.02, 36 lands (Legion Leadership MDFC),
keepable 78.4%. Preflight READY.

Owner kept Seedglaive Mentor, Agrus Kos and Iron Fist (their planned cuts). Alternate cuts,
each pair measured together (floor A, interaction 16 throughout):

| Spot | Primary | Alternates |
|---|---|---|
| Raiyuu | Danitha Capashen, Paragon (card adv 8, prot 15, BP 77, MV 3.02) | Mother of Runes (with Blazing Crescendo: CA 7, prot 14, BP 80, MV 3.08); a tapland (Sun-Blessed Peak) |
| Lightning | Aurelia, Exemplar of Justice | Blazing Crescendo; a tapland (Abraded Bluffs) |
| La'An (step 2) | Mother of Runes (if not used above) | Crystal Barricade; a tapland |

Tapland option: lands already 36 incl. the MDFC, so two land cuts leave 34 + MDFC — not advised.

## 7. Owner's board notes, round 3 (2026-11-11) — re-grades

The owner's carrier argument (a card is better when IT is the built-up body) moved ten verdicts:
Odric ★→★★, Krenko ◇→★★, Two-Handed Axe ★→★★ (extra combats double the doubled power),
Erratic Cyclops ◇→★, Loxodon Lifechanter △→★ (+25/+25 at 25 life), Voldaren Thrillseeker ◇→★
(backup grants the sac-for-power ability to the BODY), Phalanx Leader ◇→★, Balduvian Berserker
△→◇, Dragonborn Immolator △→◇ (notes only its OWN power), Thunderous Orator △→◇. Held: Fling ◇
(Self-Destruct returns, Fling doesn't), Esper Sentinel ◇ (only permanent power taxes), Concerted
Effort ◇ (Odric does it better), Forgehammer △ (needs other things dying), Teyo ◇ (lock-vs-track
question untested in Arena). Proposed: +Two-Handed Axe −Titan's Strength (owner's marks), which
moves Worf's step-2 cut elsewhere.

Error added: **the carrier frame.** A body graded in isolation ("a 1/2 for 3") misses that its
text scales with whatever the deck builds onto it. Grade a creature as the carrier too.

## 8. Carrier pass over the whole bench (2026-11-11)

Three lenses applied to every card not in the deck: (a) the CARRIER frame — text that scales with
the card's own power/toughness is graded as if it is the built-up body; (b) DEATH VALUE — a body
whose death deals its power (Berserker, Heartfire Hero) or banks it (Immolator) doubles with
Self-Destruct / Fling / Kazuul's Fury; (c) TEYO LOCK (owner's read, untested in Arena): +1 locks
toughness as base power, so pump toughness first. Moves: Teyo ◇→★, Erratic Cyclops ★→★★,
Combustion Man ★→★★, Esper Sentinel / Dragonborn Immolator / Balduvian Berserker / Fling ◇→★,
Kazuul's Fury, Guardian Scalelord, Regal Bunnicorn, Orcish Siegemaster, Cosmic Sovereign,
Molten-Core Maestro, Firebending Student ◇→★; Thunderbond Vanguard and Devilish Valet △→◇ (Krenko
combos). Corrected: Desert Were-Worm's own power is low (~10 Mountain-typed lands of 36, 2-3 in play
mid-game) — still ★★ because the carrier alone meets its 12-power extra-combat trigger; Sardian
Cliffstomper stays △ for the same Mountain count.

## 9. In-deck carrier pass + round 3 package (2026-11-11, PROPOSED)

In-deck re-grades: Sif's Spearmaster ◇→★ (tap for its power; untaps repeat it), Kaldra ★→★★
(permanent +5/+5 feeds Sentinel/Immolator/Teyo; Stoneforge and Thorin cheat it), Reyav and
Bladehold War-Whip ★★→★ (double strike now covered seven ways plus Odric). Unrated originals
that the frame confirms: Iron Fist (a carrier that taps for its power after every Feather spell,
again after each untap), Agrus Kos (extra combats turn suspect into exile in one turn),
Swiftblade (double strike + trample built in). Crystal Barricade conflicts with Pain for All
(it prevents the Self-Destruct damage Pain needs).

Package (12, measured together): +Two-Handed Axe −Titan's Strength, +Raiyuu −Danitha, +Lightning
−Aurelia Exemplar, +Teyo −Crystal Barricade, +Raubahn −Reyav, +Odric −Bladehold War-Whip,
+Krenko −Sword of Truth and Justice, +Combustion Man −Spinerock Tyrant, +Erratic Cyclops
−Collective Inferno, +Esper Sentinel −Boros Charm, +Balduvian Berserker −Mother of Runes
(optional), +Kazuul's Fury −Mountain (optional). Result: floor A, interaction 16→18, card adv
8→9, protection 15→13, board power 75→80, avg MV 3.02→3.09, early drops 24→21, legal. Kazuul's
for a Mountain: keepable 78.4→76.9% (the tool counts it as a spell; true cost is smaller).
Maybes benched: Siegemaster (best of them, Krenko combo), Maestro, Scalelord, Cosmic Sovereign.
Step 2 consequence: Spinerock, Inferno, Boros Charm, Titan's Strength and Mother of Runes were
Kirk / Pah-Wraith / Picard / Worf / La'An's cuts; only Exploratory Mission (−Valorous Stance)
keeps its cut.

## 10. Round 3 revised + Star Trek re-scope (2026-11-11, PROPOSED)

Owner keeps Danitha and Mother of Runes. Correction: Crystal Barricade is protected for a reason
(prevents noncombat damage to your other creatures: one-sided Self-Destruct and Fiery Confluence),
so it stays too. Revised: +Raiyuu −Great Train Heist, +Berserker −Fall of the Hammer, +Teyo
−Chainsaw; the other nine pairs unchanged. Measured: floor A, interaction 16, card adv 9,
protection 15, board power 83, avg MV 3.11, early drops 20, legal.

Star Trek (after the 11-13 refresh), carrier frame: Worf, Honor-Bound Warrior ★★★ (2-drop that
doubles its power on every attack at 8+ total power, free counters by tapping Equipment) −Sif's
Spearmaster; Exploratory Mission ★★ −Valorous Stance; Kirk ★★ (impulse on every attack) −Blazing
Crescendo; Combadge ★★ (two Communicators for 3 = an unblockable carrier) −Zada (alt Tenth District
Legionnaire); Pah-Wraith ★ (7 mana, team +X per differently named land each combat) −Response //
Resurgence, optional for the curve (~3.2 avg MV with all five). Skipped: La'An (Combadge does
evasion better), Picard (weakest). Estimated after all: interaction ~14, card adv ~11, floor A.

## 11. Round 3 final proposal (2026-11-11)

Owner keeps Great Train Heist, Sif's Spearmaster, Zada; takes Teyo for Crystal Barricade
(Barricade to flex; drop it from `#: protect:` when applying). Round 3: Axe −Titan's Strength,
Raiyuu −Response // Resurgence, Lightning −Aurelia Exemplar, Teyo −Crystal Barricade, Raubahn
−Reyav, Odric −War-Whip, Krenko −Sword of Truth and Justice, Combustion Man −Spinerock, Cyclops
−Collective Inferno, Esper Sentinel −Boros Charm, Berserker −Fall of the Hammer, Kazuul's Fury
−Mountain. Measured: floor A, interaction 16, card adv 9, protection 14, board power 83, avg MV
3.09, early drops 20, legal. Star Trek: Worf −Tenth District Legionnaire, Exploratory Mission
−Valorous Stance, Kirk −Blazing Crescendo, Combadge −Chainsaw, Pah-Wraith (optional) −Giantfall
(interaction ~13 if taken, ~14 without).
