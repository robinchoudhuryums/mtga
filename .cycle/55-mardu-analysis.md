# 55 Mardu (RWB) Mobilize pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS — batch 1 of 5 done (26/131).** Delete once the deck(s)
are drafted and findings folded into their `#: notes:` blocks. A scratchpad, not a
source of truth — decks/ are.

**Source list:** the 131-card RWB pile in
`scratchpad/mardu-pile.txt` (regenerate from the chat dump if lost). **Dedupe note —
deliberate adaptation:** 49 of the 131 already sit in other decks, but this pile aims at
a NEW deck and decks share the collection (a copy is never consumed), so they stay in
scope as candidates; the dedupe pass instead produced the where-they-live map (in git
history of this file's first commit). All 131 get full-text reads, in pile order,
5 batches of ~26.

**Concept (user's brief):** primary deck around **Mobilize** and related wave-token
attack mechanics; 2–3 variants expected. User-spotted clusters: (a) creature-count
ETB/damage payoffs, (b) pingers per creature/spell, (c) cast from exile/graveyard,
(d) multi-spell-per-turn boosts, (e) instant/sorcery focus, (f) wide-for-tall feeders.

## 1. The decision framework

The number that decides a card here is **what it does DURING the combat pulse**, not on
an empty board. Mobilize's shape: *"Whenever this creature attacks, create N tapped and
attacking 1/1 red Warrior tokens. Sacrifice them at the beginning of the next end
step."* Everything follows from that clock:

1. **The board WIDTH is a pulse, not a state.** Creature count peaks between the attack
   trigger and the end step. A payoff that reads count at COMBAT time (attack triggers,
   "deals damage equal to creatures you control" on an attack, Tremors-style ETB pings)
   gets the peak number; a sorcery-speed count effect you cast MAIN PHASE 1 sees the
   trough (yesterday's tokens are gone, this turn's not yet made). Grade every
   count-reader by WHEN it reads.
2. **Every combat is an ETB WAVE.** N tokens enter attacking → "whenever a creature
   enters" triggers fire N times per combat, every combat. This is the engine's real
   output; Impact Tremors-class cards are converters from width-pulse to damage.
3. **Every end step is a DEATH wave.** The tokens sacrifice themselves → "dies" /
   sacrifice-fodder payoffs are fed for free. But a SACRIFICE OUTLET is only value if
   its price beats "they die anyway" — an outlet that costs mana per token competes
   with casting spells.
4. **CADENCE IS THE CARD.** "Whenever ~ attacks" (once/combat) ≠ "whenever a creature
   you control attacks" (N+1 times) ≠ "once per turn". The Mobilize tokens themselves
   ATTACK as they enter, so per-attacker triggers see them; "at the beginning of
   combat" effects do NOT (tokens don't exist yet). Read the exact window.
5. **PRINTED COST IS WHAT WE PAY.** No cheat/recursion engine in the primary — this is
   an attacking deck; curve and Mardu castability decide. Identity ≠ castability
   (G-58): read the printed cost; hybrids and off-color activations are fine. Mardu is
   THREE colors — every 1-drop with double pips is a real cost; note pip demands.
6. **Tokens enter TAPPED AND ATTACKING.** They never block, never convoke/tap-pay
   before combat, and are gone by your next main phase. Anything that wants to TAP
   tokens for value, equip them at sorcery speed, or block with them is misreading the
   engine. (Exception: effects that sacrifice them at instant speed during combat
   beat the end-step clock.)
7. **VARIANT AXES to track, decided at the END, not mid-batch:** (A) count-payoff wide
   [primary], (B) noncombat-damage pingers [primary or its own — Judith wants SPELLS
   too], (C) exile/graveyard-cast spells-matter, (D) multi-spell velocity, (E)
   instant/sorcery focus, (F) wide-feeds-tall. Expect C+D+E to be ONE spells deck and
   F to fold into primary or ride with A; keep counting members per axis.
8. **Tooling notes:** `mobilize` IS keyword-indexed (→ go-wide/aggro) and its reminder
   text classifies as Payoff/engine — the tag layer can see this deck. Warrior-tribal
   references ("Warriors you control") must be searched PLURAL and by effect shape
   (K-13). Next deck id: **55**.

## 2. Standing error list

- **E-01 (batch 1): Aven Interrupter is NOT a C-axis engine piece.** It plots the
  OPPONENT'S spell — the free later cast belongs to the spell's owner, not us. It is
  opponent-facing tempo plus a recursion tax. Grade it as interaction, never as an
  exile-cast enabler.
- **E-02 (batch 1): "tap creatures" costs fight the engine (rule 6).** Group Project's
  flashback taps three UNTAPPED creatures — Mobilize width enters tapped-and-attacking
  and is gone by end step, so the cost is payable only by holding back the permanent
  board. Any tap-as-cost card must be graded against rule 6 explicitly.

## 3. Cross-batch observations

- Axis member counts (running, after batch 1): A=1 B=0 C=3 D=3 E=4 F=2.
- The primary's best batch-1 cards split into two machine parts: COMBAT-TIME READERS
  (Stormbeacon Blade, Auron's Inspiration, Practiced Offense, Snow Villiers) and
  WAVE-ETB ENGINES (Enduring Innocence, Spiritcall Enthusiast). Both scale with N
  tokens per combat — the deck wants its Mobilize count high, not its body count.
- **Delney question (rule G-61 — count before deciding):** Delney doubles triggered
  abilities of your power≤2 creatures. If the Mobilize BEARERS are mostly power≤2,
  Delney doubles every wave. Tally bearer power as they appear in later batches.
- Spells-matter cluster (C/D/E) is already co-occurring on the same cards (Practiced
  Offense flashback + targets; Inkwright wants targeting spells; Sage/Cosmogrand want
  velocity) — first sign C+D+E condense into ONE variant.

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`, per
AXIS (primary = the Mobilize wave deck; letters = variant axes above).

### Batch 1 (26 — the white cluster)

| Card | Primary | Axis | Note |
|---|---|---|---|
| Mardu Devotee | ★★ | infra | RWB fixer on a scrying 1-drop; rule 5 manabase glue for every build |
| Descendant of Storms | △ | F | pay-per-attack growth competes with casting (rule 3's price test) |
| Restoration Magic | ★ | E | {0}-tier instant protection for the engine piece; scales late |
| Duty Beyond Death | ★★★ | — | sac cost paid by a token that dies anyway; counters persist on the real board; instant-speed wrath insurance |
| Group Project | △ | C | E-02: flashback tap-cost fights tapped-attacking width |
| Heartflame Duelist | ★ | E | adventure removal early; lifelink-on-spells is variant E's card |
| Twinmaw Stormbrood | ◇ | — | grade the face you cast (G-43): {1}{R} omen removal early, 6-drop later; off-curve for primary |
| Informed Inkwright | ★ | E | per-spell Inkling on TARGETING spells (removal counts); E engine |
| Leader's Talent | ★ | F | L1 once/attack (rule 4); L3 turns every spell into an anthem |
| Sheltered by Ghosts | ★ | — | exile removal on a stick; interaction axis any build |
| Stormbeacon Blade | ★★★ | — | "3+ attacking" read at combat time = always true here (rule 1); repeatable draw |
| Antiquities on the Loose | ★★ | C | persistent width + flashback upgrade; the C-axis token card |
| Auron's Inspiration | ★★ | C | +2/+0 to N attackers at the pulse peak, twice via flashback |
| Aven Interrupter | ★ | — | E-01: interaction/tax, not a C engine |
| Cosmogrand Zenith | ★★ | D | second-spell → width or counters; D exemplar, feeds primary |
| Delney, Streetwise Lookout | ★★? | — | doubles power≤2 creature triggers — verdict waits on the bearer-power count (obs. above) |
| Dual-Sun Adepts | ◇ | — | fine body, {5} anthem is late-game width conversion |
| Enduring Innocence | ★★★ | — | draws EVERY combat off the wave (once/turn ✓), recurs through wraths |
| Make a Stand | ◇ | — | wrath insurance; Duty Beyond Death usually better here (free fodder) |
| Monica Rambeau | ★ | D/E | transformed = per-spell team counters; steep transform cost |
| Practiced Offense | ★★ | C | counter wave AT COMBAT TIME + cheap {1}{W} flashback recast |
| Quake, Agent of S.H.I.E.L.D. | ◇ | E | per-spell Falter; only with real spell density |
| Sage of the Skies | ★ | D | self-copying second-spell body; two lifelink flyers |
| Scout for Survivors | ◇ | C | mass-reanimate ≤3 total MV — only the cheap engines qualify; count later |
| Snow Villiers | ★★★ | A/F | power recalculates mid-combat: tokens enter attacking BEFORE damage, so he counts the full pulse |
| Spiritcall Enthusiast | ★★ | — | re-prepares every combat off the wave; repeatable pump that is also an extra CAST (feeds D) |

## 5. Consolidated plan (live)

(built after batch 1; re-ranked every batch)
