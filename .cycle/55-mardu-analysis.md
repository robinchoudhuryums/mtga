# 55 Mardu (RWB) Mobilize pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS — batch 4 of 5 done (104/131).** Delete once the deck(s)
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

- **E-01 (batch 1, AMENDED batch 2 by user):** Aven Interrupter's "exile target spell"
  has NO opponent restriction — two modes: (i) opponent-facing tempo + recursion tax,
  and (ii) SELF-TARGET: respond to your own spell, it becomes plotted, and YOUR later
  free cast is a genuine cast-from-exile (triggers Appa's Ally-maker and Antiquities'
  not-from-hand clause). Mode (ii) makes it a real C-axis enabler at the price of
  delaying your own spell a turn. Original one-mode read was the error.
- **E-02 (batch 1): "tap creatures" costs fight the engine (rule 6).** Group Project's
  flashback taps three UNTAPPED creatures — Mobilize width enters tapped-and-attacking
  and is gone by end step, so the cost is payable only by holding back the permanent
  board. Any tap-as-cost card must be graded against rule 6 explicitly. (Batch 2:
  Wild Ride's harmonize discount is the same shape, though optional.)
- **E-03 (batch 2, REFINED batch 3 after user challenge via Fire Navy Trebuchet):**
  whether the end-step sacrifice wave is visible depends on the SHAPE of the reader:
  (i) "whenever a creature dies" triggers on permanents → YES, they fire when the sac
  resolves; (ii) an INSTANT cast in the end step after the sac → YES; (iii) a
  sorcery-speed "per creature that died this turn" count (Callous Sell-Sword) → NO,
  there is no main phase after your end step; (iv) "at the beginning of your end step,
  if a creature died this turn" → NO, the intervening-if is checked when triggers go
  on the stack, before the simultaneous sac trigger resolves (CR 603.4). The original
  E-03 was shape (iii) only and over-generalized.
- **E-04 (batch 2): airbending/exiling a TOKEN kills it.** Appa's airbend and Avatar's
  Wrath remove tokens permanently (a token in exile ceases to exist) — their recast
  value applies to NONTOKEN permanents only. Blink/exile value must be graded against
  the nontoken board.

## 3. Cross-batch observations

- Axis member counts (running, after batch 4): A=5 B=4 C=17 D=12 E=11 F=12.
- **Batch 4 held the primary's SPINE:** Zurgo's Vanguard (self-scaling bearer),
  EPF Point Squad (the wave feeds him PERMANENTLY — counters outlive the tokens),
  Frontline Rush (instant-speed +X at the pulse peak), Raph & Leo (extra combat =
  a SECOND wave per turn, untapping the bearers), Jolly Balloon Man (a nightly
  Balloon copy of Vanguard/Stadium — the copy keeps their count-scaling abilities).
- **Delney tally, near-final:** bearers Stadium ✓ (1/1), Shock Brigade ✓ (1/3);
  Zurgo's Vanguard ✗ (power = creature count, usually >2 at trigger time — Delney
  checks power WHEN the trigger triggers). But the doubling roster widened: Wingnut ✓,
  EPF ✓ (double counters per wave), Raph & Leo ✓ (up to FOUR untaps), Suki ✓ (two
  Allies/turn). Delney graduates to ★★★ for the primary.
- **C splits into two flavors** (affects variant condensation): C1 = exile-cast
  (Appa, Knight Luminary warp, Aven self-plot, Longhorn plot, Demonic Ruckus plot);
  C2 = graveyard/discard (Kirol + Spirit Mascot leave-the-yard growers, Ultimate
  Green Goblin's discard+Treasure engine, Cruelclaw's discard-cast, Electro's Bolt
  mayhem, the flashback suite, Pursue the Past). C2 overlaps discard outlets and
  Treasures with D — C2+D+E looks like ONE deck; C1 rides with the primary's white
  half (Appa/Knight/Ally).
- **Landfall watch (user):** none in batch 4, but Terrapact's Landers FETCH basics
  (a land ETB on crack) — if batch 5 shows landfall payoffs, the Landers count
  toward the revival number for Remnant Elemental.
- **Mobilize bearer P/T tally (for Delney):** Stadium Headliner 1/1 (power ≤2 ✓). One
  bearer seen, one qualifies. Also tally WARRIOR payoffs — the tokens are Warriors and
  Suki is one; search plural effect-shapes at close-out (K-13).
- **Team Avatar + Mobilize stack ruling (batch 2):** "attacks alone" checks DECLARED
  attackers, and Mobilize tokens are created attacking, never declared — so a solo
  Mobilize bearer still triggers it; both triggers go on the stack together and
  resolving Mobilize FIRST means the +X/+X pump counts the fresh wave. The engine's
  wide pulse and the F-axis tall payoff are the SAME attack. This is the F-axis's
  best trick and it is entirely a timing read.
- **Brazen Collector funds the spell decks:** attack → {R} that persists through
  phases = combat-time ramp that pays for D-axis second spells or instant tricks.
  A bridge card between primary and the spells variant. (Batch 3 adds Electro,
  Assaulting Battery and Blazing Firesinger's Seething Song copy to the same
  mana-engine family — the spells variant has real fuel.)
- **OFF-PILE CANDIDATE (user, batch 3): Fire Navy Trebuchet** — {2}{B} Wall, owned 1,
  Standard-legal: "whenever you attack, create a 2/1 flying Boulder tapped and
  attacking, sac at next end step." A SECOND Mobilize-shaped wave engine on a
  defensive body; every combat's wave grows by a 2/1 flier. Strong primary include.
- **Mobilize bearer P/T tally (Delney):** Stadium Headliner 1/1 ✓, Shock Brigade 1/3 ✓
  — 2 of 2 bearers so far are power ≤2. Wingnut (1/2) also doubles its Alliance
  trigger under Delney. Delney trending toward ★★★.
- **Micro-cluster: TREASURE/ARTIFACT SAC** (batch 3): Death to Our Enemies (Treasure
  per noncreature spell) + Crime Novelist (sac artifact → counter + {R}) + Terrapact's
  Landers + Machinesmith Automaton (artifact ETB counters) — a self-contained loop
  that lives naturally INSIDE the spells variant (spells → Treasures → mana + bodies).
- **Micro-cluster: DISCARD OUTLETS feed C:** Flamecache Gecko's rummage + Team
  Avatar's discard mode enable Electro's Bolt mayhem — the C variant wants 2-3 cheap
  discard outlets to turn dead cards into graveyard casts.
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

## 3b. Parked, not dead (user rule, batch 4)

- **The Scarlet Witch** — discount gates on MV≥4 instants/sorceries; revives at ~6+
  big spells in the final E list (current pile count is low; tally at close-out).
- **Akul the Unrepentant** — the sac is SORCERY-only, so the Mobilize wave can't pay
  it (rule 1 trough + rule 6); revives at ~8+ PERSISTENT token producers (Suki,
  Antiquities, Cruel Administrator, Prickly Pair, Frontline Rush mode 1…) — that
  count is actually climbing.
- **Aziza, Mage Tower Captain** — E-02's tap-three cost; revives with a vigilance/
  stay-home width package (Swiftblade, Seedglaive, Snow, Prickly's Mercenary) in
  the copy build.

A ✗/△ is a claim about a COUNT (G-61), and later batches can move it. Each parked
card names its revival number:

- **Remnant Elemental** — revives if the pile's LANDFALL package (user: small but
  present, later batches) reaches ~6+ land-drop synergies. Watch batch 4/5.
- **Tiger-Dillo** — revives at ~8+ power-4+ bodies (F-axis tall build).
- **Scalestorm Summoner** (◇→★★) — same power-4 count as Tiger-Dillo.
- **Southern Air Temple** — revives only if a second Shrine appears (count: 1).
- **Eddie Brock** — stays out for MARDU (transform needs literal {G}); revives only
  in a 4-color/green variant, which is out of scope.
- **Crime Novelist / Machinesmith Automaton** — revive at ~8+ artifact-producers
  (Treasure/Lander cluster tally).

## 4. Running verdicts (batch 4 table below batch 3)

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`, per
AXIS (primary = the Mobilize wave deck; letters = variant axes above).

### Batch 1 (26 — the white cluster)
*(Aven Interrupter re-graded C ★★ after the E-01 amendment.)*

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

### Batch 4 (26 — the multicolor heart)

| Card | Primary | Axis | Note |
|---|---|---|---|
| The Scarlet Witch | ◇ | E (parked) | MV≥4 gate — see parked list |
| War Balloon | △ | — | crew fights rule 6; fire-counter route slow |
| Zurgo's Vanguard | ★★★ | A | bearer #3; power recalcs continuously — counts his own wave mid-combat |
| Combustion Man | ★★ | — | punisher removal EVERY attack (rule 4 cadence: once/combat is enough at power 4+) |
| Pigment Wrangler | ◇ | E ★★ | {R} copy-next-spell sorcery rides the prepared body |
| The Infamous Cruelclaw | ◇ | C2 ★★ | combat damage → free cast via discard; feeds mayhem |
| Ultimate Green Goblin | ◇ | C2 ★★★ | the discard engine: upkeep rummage + Treasure; mayhem loop on himself |
| Akul the Unrepentant | ◇ | F (parked) | sorcery-only sac CANNOT eat the wave — parked on persistent-token count |
| Cruel Administrator | ★★ | A | the wave that STAYS: persistent firebending Soldiers per attack |
| Judith, Carnage Connoisseur | ◇ | B/E ★★★ | deathtouch+lifelink on damage spells (Thunder Salvo kills anything) or death-ping Imps; the spells variant's namesake payoff |
| Aziza, Mage Tower Captain | ◇ | E (parked) | E-02 tap-three; revives with vigilance width |
| Boros Charm | ★★ | E | modal: reach/indestructible (nontoken board)/double strike |
| Frontline Rush | ★★★ | F | instant: 2 PERSISTENT Goblins or +X at the pulse peak — the F-axis modal card |
| Go Ninja Go | ★★ | F | blink re-buys ETBs; damage = greatest power scales with the tall body |
| Kirol, History Buff | ◇ | C2 ★★★ | every card LEAVING the yard re-prepares a {1}{R}{W} pump — the flashback suite's engine |
| Lorehold Charm | ★★ | C2 | 3 live modes; reanimates MV≤2 engines; team trample at the peak |
| Lightning Helix | ★★ | — | premium interaction any build |
| Pursue the Past | ★ | C2/D ★★ | discard outlet + draw 2 + flashback |
| Spirit Mascot | △ | C2 ★ | Kirol's little brother |
| Swiftblade Vindicator | ★ | F ★★ | vigilance dodges rule 6 (untapped for Aziza; pump magnet) |
| EPF Point Squad | ★★★ | A | wave counters PERSIST after tokens die; hybrid cost; Delney doubles |
| Cori Mountain Stalwart | ★ | D ★★ | Flurry ping+life; the velocity build's Tremors |
| Iroh, Tea Master | △ | — | donate gimmick; slow in 1v1 |
| Seedglaive Mentor | ★ | F/E ★★ | Valiant + vigilance + haste; grows off every targeting trick |
| Raph & Leo, Sibling Rivals | ★★★ | A | EXTRA COMBAT = second Mobilize wave; untaps the bearers; Delney doubles the untap |
| The Jolly Balloon Man | ★★ | — | nightly Balloon copy KEEPS count-scaling abilities (copy Vanguard → power = creature count, flying haste) |

### Batch 3 (26 — the red core: pingers, Mobilize bearers, spell fuel)

| Card | Primary | Axis | Note |
|---|---|---|---|
| Demonic Ruckus | ★ | C ★ | menace+trample on a bearer; replaces itself; plot cast is a real exile-cast |
| Flamecache Gecko | ◇ | D ★ | post-combat ETB refunds {B}{R} (opponent lost life ✓); rummage enables mayhem |
| Impact Tremors | ★★★ | B | rule 2 made card: N damage per combat, every combat |
| Jeskai Devotee | ★ | infra/D | G-58 poster child: identity has U from a MANA ABILITY; printed {1}{R} castable; a fixer that attacks |
| Rabid Gnaw | ★ | F ★★ | one-sided fight scaling with the tall body |
| Remnant Elemental | ✗ | — | landfall deck's card, not ours |
| Red Mage's Rapier | ◇ | E ★ | per-spell +2/+0 engine; equip {3} steep |
| Shocking Sharpshooter | ★★★ | B | 1 damage per OTHER creature entering — the wave, aimed at a player; reach body |
| Shock Brigade | ★★ | A | Mobilize bearer #2, MENACE gets the bearer through; power 1 (Delney ✓) |
| Terrapact Intimidator | ★ | infra | either mode fine: Landers fix RWB (and feed Crime Novelist) or 4/1-equivalent |
| Tiger-Dillo | △ | F ◇ | needs the power-4 count (G-61) — pending F-axis density |
| Thunder Salvo | ★ | D ★★ | X=2+spells this turn; the velocity build's cheap removal |
| Wingnut, Bat on the Belfry | ★★★ | — | Alliance picks evasion MID-combat off the wave (tokens enter before blocks); attack pump resolves after Mobilize → counts the wave; Delney doubles it |
| Adrenaline Jockey | ◇ | — | meta punisher; exhaust half is dead here |
| Blazing Firesinger | ★ | D ★★ | prepared Seething Song copy = +2 mana burst AND an extra cast |
| Crime Novelist | ◇ | D ★ | real only with the Treasure/Lander cluster — count at draft |
| Death to Our Enemies | ★ | D/E ★★ | 4 spells → 7 damage + 4 Treasures that fund the next 4 |
| Electro, Assaulting Battery | ◇ | D/E ★★★ | the spells variant's mana engine: rebate per spell, mana persists, X-damage exit |
| Electro's Bolt | ★ | C ★★ | mayhem off the discard outlets; clean 4-damage otherwise |
| Frantic Firebolt | ◇ | E ★★ | scales with the spells graveyard, not this board |
| Machinesmith Automaton | ◇ | — | artifact-cluster only; Treasures do trigger it |
| Longhorn Sharpshooter | ◇ | C ★ | plot ping + a later exile-cast; slow for primary |
| Molecular Modifier | ◇ | — | rule 4: beginning-of-combat fires BEFORE the wave — bearer-only pump, works but small |
| Prickly Pair | ★ | — | two persistent bodies; the Mercenary's sorcery-tap dodges rule 6 by staying home |
| Scalestorm Summoner | ◇ | F ★★ | with a power-4 body: a PERSISTENT 3/1 per attack (not sacrificed) |
| Tablet of Discovery | ◇ | E ★★ | spells-only RR mode; impulse ETB; the spells variant's rock |

### Batch 2 (26 — rest of white, into the red cluster)

| Card | Primary | Axis | Note |
|---|---|---|---|
| Stand Up for Yourself | ★ | — | clean power-3+ removal |
| Suki, Courageous Rescuer | ★★★ | F | anthem + converts one wave-death per turn into a PERSISTENT Ally (end step is "during your turn" ✓); a Warrior herself |
| Team Avatar | ★★ | F ★★★ | the stack ruling above: solo bearer + wave = counted pump; discard mode reads count at combat (rule 1) |
| Appa, Steadfast Guardian | ★★ | C ★★★ | flash wrath-dodge for the NONTOKEN board (E-04); Ally per exile-cast pairs with warp/plot/flashback |
| Avatar's Wrath | ◇ | C | reset-when-behind; our cheap engine rebuilds at {2} each, tokens lost (E-04); briefly shuts THEIR recursion |
| Exemplar of Light | ◇ | E | verdict waits on the LIFEGAIN COUNT (G-61) — with Heartflame Duelist every spell draws |
| Knight Luminary | ★ | C ★★ | warp = two ETBs + a real exile-cast; feeds Appa |
| Prayer of Binding | ★ | — | flash exile removal, any build |
| Rally the Monastery | ★ | D ★★ | {1}{W} after your second spell; three relevant modes |
| Southern Air Temple | △ | — | Shrine count in pile = 1 (G-61: counted, dismissed) |
| Spider-UK | ★★ | — | "2+ entered this turn" = every Mobilize combat → draw+2 life; web-slinging RE-BUYS a tapped post-combat ETB creature (rule 6 turned into upside) |
| Sunstar Lightsmith | ★ | D ★★ | second spell → counter + draw |
| Wayspeaker Bodyguard | ★ | C/D | recurs MV≤2 engines; Flurry taps a blocker |
| White Auracite | ★ | infra | removal that fixes ({T}: add W) |
| Ajani's Response | ★ | — | {1}{W} destroy vs a tapped creature — attackers and post-Flurry targets |
| Primary Research | ◇ | C ★★ | reanimate + draw-per-turn once the graveyard moves; spells-variant engine |
| Lecturing Scornmage | △ | E ★ | grows per targeting spell; small |
| Masterful Flourish | ◇ | — | 1-mana protection; competes with Restoration Magic's {0} tier |
| Callous Sell-Sword | ★ | F ★★ | E-03: counts combat deaths, NOT the end-step wave; Burn Together is the F-axis fling finisher |
| Eddie Brock // Venom | ✗ | — | transform costs literal {G} — uncastable in Mardu; the front alone is filler (G-58 read correctly: castable front, unreachable payoff) |
| Stadium Headliner | ★★★ | A | Mobilize-1 one-drop whose sac reads creature count DURING combat (rule 1); bearer power 1 (Delney ✓) |
| Violent Urge | △ | — | delirium wants a graveyard this build doesn't fill deliberately |
| Wild Ride | ◇ | C | E-02-shaped harmonize discount; the front is a fine haste trick |
| Become Brutes | ◇ | — | haste + Roles; unexciting here |
| Brazen Collector | ★★ | D | attack → persistent {R}: combat-time ramp that funds second spells (see observation) |
| Bulk Up | ◇ | F ★★ | double Snow Villiers = double the count; flashback for two uses |

## 5. Consolidated plan (live)

(first draft lands after batch 3 — the Mobilize core itself (Zurgo, Siegebreaker,
Bone-Cairn, Frontline Rush, Warriors) is still unread in batches 4-5; ranking the
shell before reading the engine would be premature)
