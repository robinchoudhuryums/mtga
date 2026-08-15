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

## 5. Consolidated plan (live)

- (builds after batch 1)
