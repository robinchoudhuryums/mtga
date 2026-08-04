# 55 Mardu (RWB) Mobilize pile — analysis (TEMPORARY working doc)

**Status: ALL FIVE BATCHES READ (131/131). Consolidated plan below — awaiting user picks.** Delete once the deck(s)
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
   count-reader by WHEN it reads. **AMENDED batch 5: MAIN PHASE 2 sees the full wave's
   WIDTH** — the tokens live until the beginning of the end step, so post-combat
   sorceries count them and post-combat sac outlets can EAT them. Only their DEATHS
   have not happened yet (E-03 unchanged). Main 1 = trough; combat + main 2 = peak.
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
- **E-05 (batch 5): I over-applied the trough rule to Akul.** His sorcery-only sac
  CAN eat the wave — main phase 2 is before the end step, the tokens are alive, and
  three of them pay his cost. Batch 4's parking reason ("the wave can't pay it") was
  wrong; the real constraints are his {B}{B}{R}{R} pips and wanting a bomb in hand.
  Re-graded ◇ → ★★ primary. The framework's rule-1 amendment is the general fix.
- **E-04 (batch 2): airbending/exiling a TOKEN kills it.** Appa's airbend and Avatar's
  Wrath remove tokens permanently (a token in exile ceases to exist) — their recast
  value applies to NONTOKEN permanents only. Blink/exile value must be graded against
  the nontoken board.

## 3. Cross-batch observations

- Axis member counts (FINAL): A=7 B=4 C1=9 C2=12 D=13 E=13 F=13. Mobilize bearers: 6
  in-pile (Stadium 1/1, Shock Brigade 1/3, Zurgo's Vanguard */3, Bone-Cairn 4/4,
  Zurgo 2/4, Reigning Victor 3/3) + Fire Navy Trebuchet off-pile + wave-shaped
  engines (Mardu Siegebreaker, Cruel Administrator, Jolly Balloon Man, Push//Pull's
  back half).
- **Zurgo, Thunder's Decree is the architecture card:** "during your end step, Warrior
  tokens can't be sacrificed" defeats the delayed sac trigger ENTIRELY (it tries once,
  fails, never returns) — with Zurgo out, every wave is PERMANENT width. The deck
  stops being pulse-only; sorcery-speed counts, Akul fodder, and Delney (Zurgo is
  power 2 — doubled Mobilize 2 = 4 tokens/attack) all improve. He is the primary's
  centerpiece.
- **Windcrag Siege (Mardu mode) is Delney-on-an-enchantment** for ATTACK-caused
  triggers of permanents: doubles every Mobilize wave, Wingnut's pump, Cruel Admin's
  Soldier, Siegebreaker's copies. It does NOT double ETB converters (Tremors triggers
  off entering, not attacking).
- **Neriv doubles the wave's DAMAGE** (entered-this-turn creatures deal double) —
  tokens hit for 2 each; stacks under Windcrag/Delney wave doubling.
- **The Siegebreaker package:** exile a nontoken ETB creature (Sonic Shrieker, Jet) →
  a fresh attacking copy EVERY combat (its ETB re-fires; Tremors sees it; Neriv
  doubles it). E-04 respected (never exile a token).
- **Landfall final count (user watch): package did NOT materialize** — 1 payoff
  (Remnant Elemental), 0 true enablers (Mardu Monument fetches to HAND). Remnant
  stays parked; revival number unmet in this pile.
- **Leyline of the Guildpact is genuinely uncastable in Mardu** — {G/U} demands G or
  U mana, neither exists here. ✗ (not parked; a 4c/5c deck's card).
- **Thanos, graded as what's reachable:** the power-up needs literal {C}{W}{U}{B}{R}{G}
  — dead in Mardu — but the front is a castable {R}{W}{B} 4/4 deathtouch lifelink,
  a fair body on rate. ★ as a body, ability written off (contrast Eddie Brock, whose
  PAYOFF was the unreachable half).
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

### Batch 5 (27 — top end and lands)

| Card | Primary | Axis | Note |
|---|---|---|---|
| Mabel, Heir to Cragflame | ★ | — | free Cragflame (haste+vigilance) on a bearer; Mouse count too low for the anthem |
| Windcrag Siege | ★★★ | — | Mardu mode doubles ATTACK-caused triggers of permanents — every wave, Wingnut, Cruel Admin, Siegebreaker; not Tremors (ETB≠attack) |
| Bre of Clan Stoutarm | ★★ | C1 ★★ | taps HERSELF (rule 6 clean); lifelink the bearer → free-cast MV≤life at end step |
| Ertha Jo, Frontier Mentor | ★★ | — | copies targeted ACTIVATIONS: Stadium's count-damage, Balloon Man's copy, Mercenary pumps |
| Sami, Ship's Engineer | ★★ | — | "2+ tapped" post-attack = always (rule 6 as upside); free 2/2 per turn |
| Sun Warriors | ★★★ | A | firebending X = count AFTER the wave resolves first — width into mana, mid-combat; {5} sink included |
| Veteran Guardmouse | ★ | F/E | Valiant + scry rider |
| Jet, Freedom Fighter | ★★ | A | rule-1 AMENDMENT case: cast MAIN 2 → counts the still-living wave |
| Lorehold, the Historian | ◇ | E ★★ | hand-miracle {2} makes the big-spell tilt real; enables Scarlet Witch's gate |
| Thor Odinson | ◇ | D/E ★★ | double prowess, vigilance |
| Aurelia, the Warleader | ★★★ | — | untap ALL + extra combat = full second wave |
| Molten Note | ◇ | E ★ | "mana SPENT" not MV (framework Stage-1 distinction); untap-all rider |
| Form a Posse | ★ | F | X persistent Mercenaries; Akul/Ertha fodder |
| Mardu Monument | ★ | infra | fetch-to-HAND (no landfall); late 3-Warrior sac |
| Fire Lord Zuko | ★ | C1 ★★★ | the exile variant's payoff: counters per exile-cast; firebending scales with his own growth |
| Push // Pull | ★★ | C2 ★★ | G-02: front is {1}{W/B} removal, not MV 8; back is a wave-shaped reanimation |
| Bone-Cairn Butcher | ★★★ | A | Mobilize 2 + the WAVE GAINS DEATHTOUCH — attacking into it loses material every turn |
| Zurgo, Thunder's Decree | ★★★ | A | the architecture card: end-step sac PREVENTED once = prevented forever; waves become permanent; power 2 → Delney doubles him |
| Thanos, the Mad Titan | ★ | — | power-up needs literal WUBRG+C — dead; the {R}{W}{B} 4/4 deathtouch lifelink body is still fair |
| Mardu Siegebreaker | ★★★ | A | attacking COPY of your best ETB creature every combat; sac-at-end-step (wave-shaped); pair with Sonic Shrieker/Jet |
| All-Out Assault | ★★ | — | anthem + deathtouch + a third extra-combat effect |
| Neriv, Heart of the Storm | ★★★ | A | entered-this-turn creatures deal DOUBLE — tokens hit for 2; stacks with wave-count doublers |
| Sonic Shrieker | ★ | — | ★★ as the Siegebreaker exile target (ETB re-fires per copy) |
| Defibrillating Current | ★ | — | {2/R}{2/W}{2/B}: MV prints 6, casts for 3 colored pips (rule 5) |
| Nomad Outpost | ★ | infra | the Mardu tapland |
| Reigning Victor | ★ | A | bearer #6; flexible hybrid cost |
| Leyline of the Guildpact | ✗ | — | {G/U} demands G or U mana — uncastable in strict Mardu |

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

**VARIANT VERDICT (all 131 read): three decks, matching the user's 2–3 guess.**
A and B fold into the primary (the pingers ARE its damage converters); F folds in as
a sub-package; C1 and C2+D+E each stand alone.

### 55 PRIMARY — "Mardu Waves" (Mobilize pulse-to-permanence)
- **Engine (bearers + wave-shaped):** Zurgo, Thunder's Decree ★★★ (centerpiece —
  makes waves permanent) · Zurgo's Vanguard ★★★ · Stadium Headliner ★★★ · Bone-Cairn
  Butcher ★★★ (wave gains deathtouch) · Shock Brigade ★★ · Reigning Victor ★ ·
  Fire Navy Trebuchet (off-pile, owned) · Mardu Siegebreaker ★★★ + Sonic Shrieker/Jet
  as its exile targets · Cruel Administrator ★★ · The Jolly Balloon Man ★★
- **Doublers:** Windcrag Siege ★★★ (attack-triggers) · Delney ★★★ (power≤2 triggers)
  · Neriv ★★★ (damage) · Raph & Leo ★★★ / Aurelia ★★★ / All-Out Assault ★★ (extra
  combats = extra waves)
- **Converters (the wave becomes cards/damage/mana):** Impact Tremors ★★★ · Shocking
  Sharpshooter ★★★ · EPF Point Squad ★★★ (permanent counters) · Enduring Innocence
  ★★★ (draw/combat) · Spider-UK ★★ · Stormbeacon Blade ★★★ · Sun Warriors ★★★
  (width → {R} mana mid-combat) · Suki ★★★ (wave-death → permanent Ally) · Sami ★★
- **Pulse spells:** Frontline Rush ★★★ · Duty Beyond Death ★★★ · Auron's Inspiration
  ★★ · Practiced Offense ★★ · Boros Charm ★★
- **Big sink (revived):** Akul ★★ (E-05 — main-2 sac of three live tokens)
- **Interaction:** Lightning Helix ★★ · Lorehold Charm ★★ · Stand Up for Yourself ★ ·
  Ajani's Response ★ · Sheltered by Ghosts/Prayer of Binding ★ · Defibrillating
  Current ★ · Push // Pull ★★ (2-mana front; wave-shaped back)
- **Infra:** Mardu Devotee ★★ · Terrapact ★ · Nomad Outpost + fixers · Mabel ★
  (Cragflame on a bearer)
- **F sub-package (trim to taste):** Snow Villiers ★★★ · Team Avatar ★★ (stack
  ruling) · Bulk Up · Go Ninja Go · Rabid Gnaw · Swiftblade · Seedglaive
- **PROTECT (what `cuts` can't see):** Zurgo (rules-layer sac prevention), Windcrag
  Siege (trigger doubling reads as blank text to role patterns), Delney (G-40's
  documented shape), Suki (leave-trigger cadence), Siegebreaker's exile targets
  (their value is the copies, not their bodies).

### 55a — "Mardu Spellstorm" (C2 + D + E merged)
Payoffs: Judith ★★★ · Cori Mountain Stalwart ★★ · Thor ★★ · Monica ★★ · Heartflame
Duelist ★★. Mana engine: Electro ★★★ · Blazing Firesinger ★★ · Brazen Collector ★★ ·
Tablet of Discovery ★★ · Death to Our Enemies ★★ (+ Crime Novelist on its Treasures).
Velocity: Cosmogrand ★★★ · Sage ★★ · Sunstar ★★ · Rally ★★ · Pigment Wrangler ★★.
Graveyard half: Kirol ★★★ + Spirit Mascot + the flashback suite (Pursue ★★,
Antiquities, Auron's, Practiced) + discard outlets (UGG ★★★, Flamecache, Cruelclaw)
+ mayhem (Electro's Bolt ★★). Removal that scales: Thunder Salvo ★★ · Frantic
Firebolt ★★. Big-spell tilt (optional): Lorehold the Historian ★★ miracle + Scarlet
Witch (parked gate). Targeting riders: Inkwright ★ · Scornmage ★ · Seedglaive ★.
Aziza rides ONLY with the vigilance package (parked note).

### 55b — "Mardu Airbender" (C1 exile-cast, white-heavy)
Fire Lord Zuko ★★★ (counters per exile-cast + firebending) · Appa ★★★ (flash save +
Ally per exile-cast) · Bre of Clan Stoutarm ★★ (lifegain → free cast) · Knight
Luminary ★★ (warp) · Aven Interrupter ★★ (self-plot, E-01) · Antiquities on the
Loose ★★ · Longhorn Sharpshooter ★ · Demonic Ruckus ★ (plot) · Avatar's Wrath ◇ ·
plus white token base (Suki, Frontline Rush, Cosmogrand) and Mardu interaction.
Thinnest of the three — a 60 exists, but it borrows the primary's white half; build
THIRD, after the first two prove which cards they actually keep.

### Next steps (Stage 6)
1. User picks the build order (recommendation: 55 primary via /draft-deck, then 55a;
   55b after both settle).
2. /draft-deck per deck; this doc's PROTECT list goes into `#: protect:` headers.
3. Fold durable findings (E-01..E-05, the stack rulings, Zurgo architecture note)
   into the deck files' `#: notes:`, then DELETE this doc.
