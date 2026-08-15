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

## 5. Consolidated plan (live)

- (builds after batch 1)
