# Wylie Duke tap-synergy pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the deck(s) are drafted and the findings are folded
into the deck files' `#: notes:` blocks. A scratchpad, not a source of truth — decks/ are.

**Source list:** scratchpad `wylie-pile.txt` — 106 distinct names; 74 not currently in any
deck (`wylie-remaining.txt`), 32 already in decks. **For a NEW-deck pile the 32 stay
candidates** (copies are fungible — CLAUDE.md "decks share the collection"); they get a
compact sweep after the main batches instead of full re-grades.

**Goal:** a NEW deck (likely WGR per the user) around **Wylie Duke, Atiin Hero**
({1}{G}{W} 3/3, Vigilance, "Whenever Wylie Duke becomes tapped, you gain 1 life and draw
a card") — tap OWN creatures as a COST for value; possibly tap-down of opponents as a
second axis. Track variant-deck signals explicitly (user asked).

## 1. The decision framework

- **F1 — The engine is TAP-AS-COST, not attacking.** Wylie has vigilance, so attacking
  never taps him: every card is graded on *how it taps my creatures without combat* —
  crew (Vehicles), saddle (Mounts), station (Spacecraft), teamwork, "tap N untapped
  creatures you control" activation costs, and tap-for-mana/ability (Springleaf Drum
  shape). An enabler's value = taps per turn × what the tap buys. A card that taps
  creatures only by ATTACKING does nothing for Wylie (but see F6).
- **F2 — Count the PAYOFFS (G-59).** Cards that trigger on "becomes tapped" (Wylie is
  one; the pile should be searched for others) are the payoff population. The deck is
  viable in proportion to payoff count, not enabler count — enablers are everywhere.
- **F3 — Vigilance is double-dipping.** A vigilant creature attacks AND is still untapped
  to pay tap costs. Vigilance grants/bodies rate up.
- **F4 — "Untap" effects are extra activations.** Anything that untaps my creatures
  (Rimefur Reindeer shape?) multiplies every tap payoff. Rate untappers as engine
  pieces, not tricks.
- **F5 — Castability WGR (G-58):** read printed COST, not identity; hybrids on-color.
  Non-WGR identity from abilities is fine if the cast cost fits. Check Standard in the
  pull.
- **F6 — The OPPONENT-tap axis is a different engine.** Tap-down control (Thunder Lasso,
  Authority of the Consuls) does not trigger Wylie. It may still belong (control +
  pseudo-removal) or may be a VARIANT signal (F7). Grade it on its own axis and label it.
- **F7 — Variant signals to track per batch:** (a) Mercenary token-makers (OTJ tokens
  tap THEMSELVES to pump — self-tapping bodies), (b) Mounts/saddle, (c) Vehicles/crew,
  (d) Station (EOE), (e) Teamwork, (f) tap-for-mana dorks/fixers, (g) opponent tap-down
  (W control). A cluster repeatedly rejected for the same reason = a deck asking to be
  built; decide at the END.
- **F8 — Cadence (skill rule 4):** "once per turn" vs per-tap changes a payoff's value
  by a factor of 3+ in this deck; quote the cadence in the verdict.

## 2. Standing error list

- (none yet)

## 3. Cross-batch observations

- (running)

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

### Batch 1 (cards 1–25 of the 74)

| Card | Verdict | Why (framework rule) |
|---|---|---|
| Kirol, Attentive First-Year | ★★★ | F1 outlet that taps WYLIE + copies his trigger (tap Wylie+1 → copy the tapped-trigger = 2 life 2 cards). {1}{R/W}{R/W} hybrid, 1/turn (F8). |
| Adagia, Windswept Bastion | ★★★ | A LAND with station: repeatable sorcery-speed "tap another creature you control" — a free Wylie outlet in the manabase. W source. |
| Sunstar Chaplain | ★★ | F2 payoff: "two or more tapped creatures → +1/+1 counter" every end step; its own ability taps for more. |
| Starport Security | ★★ | Repeatable instant-speed "tap another target creature": taps Wylie for value OR their attacker (F6 dual-axis). Owned. |
| Great Train Heist | ★★ | F4 mass-untap = re-tap all outlets in one turn + extra combat; modal. |
| Ertha Jo, Frontier Mentor | ★★ | Copies every activated ability that targets (Mercenary pumps, Starport taps); brings a Mercenary. |
| Hellspur Posse Boss | ★ | 2 Mercenary tokens (self-tapping pump bodies = saddle/crew fuel + Wylie pumps) + outlaw haste. |
| Brimstone Roundup | ★ | Mercenary per 2nd spell; plot. Token stream for tap costs. |
| Alacrian Jaguar | ★ | Vigilant Mount; saddle 1 taps Wylie (F1); self-pump. 5 MV common. |
| Thunder Lasso | ★ | Axis-B (F6): repeatable attack-tap of a defender; cheap. |
| Summon: Primal Garuda | ★ | Axis-B payoff: 4 dmg to a TAPPED creature + evasion sagas. |
| Rootwise Survivor | ★ | F2-adjacent payoff: "if this is tapped at 2nd main → 3 counters on a land"; wants crew/saddle to tap it. |
| Spring-Loaded Sawblades | ★ | Axis-B payoff (5 dmg to tapped) + crew-1 Vehicle back face. |
| Vow to Erebor | ◇ | F4 untap trick + pump; owned. Fine filler, not engine. |
| Vengeful Villagers | ◇ | Axis-B on attack; sac rider is off-plan. Owned. |
| Mouse Trapper | ◇ | Valiant tap-down needs a targeting shell we may not run. |
| Rimefur Reindeer | ◇ | Tap-down per ENCHANTMENT ETB — only with an enchantment sub-build. |
| Wayspeaker Bodyguard | ◇ | Flurry tap-down + small regrowth; cadence 1/turn. |
| Raccoon Rallier | △ | Haste granter; taps itself for marginal value. |
| Stubborn Burrowfiend | △ | Saddle payoff is mill-grow — a different (graveyard) axis. |
| Hedge Whisperer | △ | Land-animation w/ collect evidence; off-plan. |
| Rhys, the Evermore | △ | Persist trick; counter-removal niche. |
| Venat, Heart of Hydaelyn | △ | Legendary-matters engine — good card, wrong deck. |
| Take for a Ride | ✗ | Steal effect; nothing here wants it (F1/F2 zero). |
| Rydia, Summoner of Mist | ✗ | Saga recursion; no saga density planned. |

### Batch 2 (cards 26–50 of the 74)

| Card | Verdict | Why (framework rule) |
|---|---|---|
| Wanderbrine Preacher | ★★★ | PAYOFF #2 (F2): "whenever this becomes tapped, gain 2 life" — a Wylie clone at common. Owned. |
| Selvala, Eager Trailblazer | ★★★ | Vigilance (F3) + Mercenary per creature spell + {T}: huge mana. Engine on one card. |
| Ghired, Mirror of the Wilds | ★★★ | Grants EVERY nontoken creature "{T}: copy a token that entered this turn" — a mass tap outlet (F1) that turns Wylie's tap into a Mercenary copy. |
| Dragonbroods' Relic | ★★★ | G-58 CASE: identity 5c but CAST COST {1}{G} — castable. "{T}, tap an untapped creature you control: any color" = repeatable Wylie tap + fixing. Owned. |
| The Wandering Rescuer | ★★★ | Convoke (casting it taps Wylie = triggers) + "other TAPPED creatures you control have hexproof" — protects the whole tapped board. Flash. |
| Guardian of the Great Door | ★★ | Cast cost taps FOUR untapped permanents incl. lands (F1: 4 triggers in one cast); 4/4 flier for {W}{W}. |
| Encumbered Reejerey | ★★ | Tap-payoff body: 5/4 for 2 that upgrades itself each time it becomes tapped. |
| Split Up | ★★ | Asymmetric BOTH ways here: our board taps down (destroy all untapped hits them), their board taps down via axis B (destroy all tapped). |
| Authority of the Consuls | ★★ | Axis-B keystone: their creatures ENTER tapped → every tapped-punish spell is always live; drips life. |
| Flight-Deck Coordinator | ★ | Payoff #3: 2+ tapped creatures → gain 2 each end step. |
| Glimmer Seeker | ★ | Survival payoff that DRAWS (or makes a body); tap it with crew/saddle/convoke. |
| Veteran Survivor / Savior of the Small | ★ | Survival cluster: graveyard hate / recursion riders on tapped-at-2nd-main. |
| Form a Posse | ★ | X Mercenaries (self-tapping pump bodies, tap-cost fuel). |
| Deadly Riposte / Eriette's Lullaby / Ajani's Response / Fate of the Sun-Cryst / Reroute Systems | ★ | The tapped-punish removal suite (axis B): all cheap or discounted vs tapped targets — always live under Authority. |
| Baseball Bat | ◇ | Attack-tap equipment; axis B, combat-gated. |
| Archangel of Tithes | ◇ | Wants to stay UNTAPPED (tax wall) — fine body, off the tap engine. |
| Settle the Wreckage | ◇ | Generic wrath; fine, no synergy. |
| Helping Hand | △ | Reanimates ETB-tapped — "enters tapped" is NOT "becomes tapped": no triggers. Owned. |
| Tam, Mindful First-Year | ✗ | OFF-color (G/U identity, {G/U} cast — U pip not payable in WGR). |

### Batch 3 (cards 51–74) — highlights

| Card | Verdict | Why |
|---|---|---|
| Annie Joins Up | ★★★ | DOUBLES legendary creatures' triggered abilities — Wylie taps for 2 life + 2 cards. Naya gold. |
| A Realm Reborn | ★★★ | Every permanent gains "{T}: any color" — mass outlet + complete WGR fixing. Owned. |
| Hawkeye's Bow | ★★★ | Equipment PAYOFF: "whenever equipped creature becomes tapped, 1 dmg each opponent" — staple it to Wylie. {R}, owned. |
| Springleaf Drum / Gene Pollinator | ★★ | 1-mana tap-a-creature fixers: a Wylie trigger every turn that also fixes 3 colors. |
| Baylen, the Haymaker | ★★★ | Taps TOKENS for mana/draw/counters — the Mercenary stream becomes an engine. |
| Command Bridge | ★★ | Land that taps a permanent on ETB (a trigger from the manabase) + any color. |
| Traveling Botanist | ★★ | Payoff: becomes tapped → land selection. |
| Agent Maria Hill | ★★ | Teamwork-tap payoff: +1/+1 counter AND draw. Owned. |
| Helicarrier Strike | ★★ | Teamwork removal — the cost taps Wylie = trigger + 4 dmg. Owned. |
| Samut, the Driving Force | ★★ | Vigilant Naya anthem + cost reduction; curve top. |
| Redshift, Rocketeer Chief | ★★ | Vigilant; {T}: X mana for ABILITIES — pays crew/saddle/equip/station costs. |
| Frontline War-Rager | ★ | 2+ tapped → grows. Owned. |
| Hardbristle Bandit | ★ | Any-color dork; axis-B targeting is a crime → untaps → extra activation. Owned. |
| Bender's Waterskin / Dependable Quinjet | ★ | Any-color rocks; Quinjet is also a crew-4 outlet. Owned. |
| Bridled Bighorn / Gilded Ghoda | ★/◇ | Saddle outlets (Bighorn vigilant per F3). |
| Foggy Swamp Vinebender | ◇ | Waterbend = tap-to-pay outlet, but slow. Owned. |
| Shimmerwilds Growth / Ishgard / Crowd-Control Warden / Old Hob | ◇/△ | Fine cards, off the engine. |

### In-deck 32 sweep (fungible — all still candidates)

**Payoffs already owned:** Compassionate Healer (tapped → life+scry — a third Wylie),
Spider-Gwen (tapped → loot), Hawkeye, Master Marksman (tapped → modal arrows),
Seedship Agrarian (tapped → Lander), Dawnstrike Vanguard (2+ tapped → mass counters),
Roxanne (artifact-token tap payoff). **Outlets/engines owned:** Enduring Vitality
(creatures gain "{T}: any color" — vigilant + recursive), Aziza (tap 3 → copy spell),
Wanderbrine Trapper (tap own → tap theirs, both axes), Aurelia (untap all + extra
combat), Unswerving Sloth (attack → untap ALL), The Eternity Elevator + Adagia
(station), Wrench, Frog Butler, Surveillance Room, teamwork suite (Go Nuts!,
HULK SMASH!, Team Tactics). **Axis-B owned:** Solitary Sanctuary, Spider-Woman
({3}{W/U} hybrid — castable in W per G-58), Push // Pull (front face), Zidane/Neutrinos
(off-plan steal/blink — skip).

## 3b. Cross-batch observations (final)

- **Payoff population (F2): ~15** "becomes tapped"/tapped-state cards across pile +
  collection — comfortably viable by the G-59 test. The engine's best turn: tap Wylie
  to Springleaf/Relic/Vitality mana or Ghired/Aziza/convoke, with Annie doubling and
  Kirol copying the triggers, under Wandering Rescuer's tapped-hexproof umbrella.
- **The mana problem solves itself**: the tap-fixers (Drum, Pollinator, Relic, Vitality,
  Realm Reborn, Selvala, Surveillance Room) ARE engine pieces — a WGR base with
  any-color access that triggers Wylie to fix.
- **VARIANT A — RW/Naya Mercenary-outlaw tokens** (viable): Form a Posse, Hellspur
  Posse Boss, Brimstone Roundup, Ertha Jo, Great Train Heist, War Effort, Old Hob +
  Baylen as the token-tap engine. Self-tapping Mercenaries + haste lord + ability
  copying. Distinct plan (aggro swarm) from the value engine.
- **VARIANT B — W(±u splash-free) tap-down control** (viable): Authority of the Consuls
  (they ENTER tapped) + Spider-Woman/Solitary Sanctuary/Thunder Lasso/Mouse
  Trapper/Rimefur locks + the tapped-punish suite (Deadly Riposte, Eriette's Lullaby,
  Ajani's Response, Fate of the Sun-Cryst, Reroute Systems, Sawblades, Garuda,
  Split Up, Push front face) + Archangel of Tithes/Settle the Wreckage. No such deck
  in the roster. Wanderbrine Trapper bridges A-axis and B-axis.
- **NOT variants, just packages:** teamwork/MSH cluster (1 payoff — Maria Hill) and the
  DSK survival cluster (tapped-at-2nd-main) both fold into the main deck.

## 5. Consolidated plan (live)

**MAIN DECK — "Wylie tap-value" (WGR, Standard).** Draft via /draft-deck from this
shortlist (~44 nonland candidates for ~35 slots; cut at draft time):

- **Core engine (protect):** Wylie Duke (craft R — THE seed), Wanderbrine Preacher,
  Compassionate Healer, Annie Joins Up (craft R), Kirol (craft R), The Wandering
  Rescuer (craft M), Hawkeye's Bow, A Realm Reborn, Enduring Vitality.
- **Payoff bodies:** Spider-Gwen, Hawkeye Master Marksman, Traveling Botanist (craft U),
  Seedship Agrarian, Encumbered Reejerey, Sunstar Chaplain (craft R), Flight-Deck
  Coordinator (craft C), Frontline War-Rager, Dawnstrike Vanguard, Agent Maria Hill,
  Rootwise Survivor (craft U), Glimmer Seeker (craft U).
- **Outlets/fixing:** Springleaf Drum (craft U), Gene Pollinator (craft C),
  Dragonbroods' Relic, Aziza, Selvala (craft M), Ghired (craft M), Baylen (craft R),
  Redshift (craft R), Guardian of the Great Door (craft U), Group Project (craft U),
  Dependable Quinjet, Wanderbrine Trapper.
- **Re-tap/protection:** Aurelia, Unswerving Sloth, Great Train Heist (craft R),
  Biosynthic Burst, Vow to Erebor.
- **Interaction:** Helicarrier Strike, HULK SMASH!, Split Up (craft R), Deadly Riposte
  (craft C), Fate of the Sun-Cryst.
- **Lands of note:** Adagia (craft M), Command Bridge (craft C), The Eternity Elevator
  (artifact), Surveillance Room, Abandoned Air Temple, Fire Nation Palace + owned
  Naya duals.
- **PROTECT list (what `cuts` cannot see):** Dragonbroods' Relic and Springleaf Drum
  (fixers whose value is the TRIGGER, not the mana), Hawkeye's Bow (payoff lives on
  the equipped creature), Annie Joins Up (doubler — value in the rest of the deck),
  A Realm Reborn / Enduring Vitality (mass outlets that read as mana filler).

**VARIANT A (later, /draft-deck):** RW/Naya Mercenary tokens — Baylen + Form a Posse +
Hellspur + Brimstone + Ertha Jo + Great Train Heist + War Effort + Old Hob.
**VARIANT B (later, /draft-deck):** Mono-W tap-down control — Authority + stun/lock
bodies + the tapped-punish removal suite + Archangel of Tithes.
