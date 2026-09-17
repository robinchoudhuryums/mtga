# Deck 45 "The Exiles" — 31-card consideration pile (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the durable findings are folded
into `decks/45-the-exiles/deck.txt`'s `#: notes:`. A scratchpad, not a source of truth.

**Source list:** user-supplied, 2026-09-17. 31 distinct cards, **0 already in deck 45**.
Graded against deck 45 AS OF the 2026-09-17 second tune pass (commit 7b2d020), not the
list it had yesterday.

## 1. The decision framework

**R1 — THE PAYOFF TABLE IS THE WHOLE ANALYSIS, AND "EXILE" IS TWO DIFFERENT EVENTS.**
Deck 45 has four payoffs. Read their triggers exactly:

| payoff | `cast a spell from exile` | `a permanent you control ENTERS from exile` |
|---|---|---|
| Fire Lord Zuko | ✓ | **✓ — the only one** |
| Appa, Steadfast Guardian | ✓ | ✗ |
| Quintorius Kand | ✓ | ✗ |
| Spider-Verse (`from anywhere other than your hand`) | ✓ | ✗ |

So: a **BLINK** (exile and return it immediately) pays **1 of 4**.
A card that **exiles now and lets you CAST it later** (warp, plot, impulse, Appa's
airbend) pays **4 of 4**. The user's thesis on the starred blink cards is *correct but
half-sized* — Zuko fires, the other three do not. Grade every blink card at 1/4, and every
exile-then-cast card at 4/4. Cite this rule by number.

**R2 — EFFECTIVE COST, NOT PRINTED.** 8 of 35 nonland cards are warp/plot cheat costs.
Printed avg MV 3.31; **effective 2.86**. A card whose printed cost looks unplayable may be
fine, and vice versa — read the cost you actually pay first (G-02/G-43/G-60).

**R3 — LIVE VECTOR, 2026-09-17 (every verdict is relative to these).**
interaction 9 (2 unclassified) · card advantage 8 · protection 3 · avg MV 3.31 (eff. 2.86)
· early drops 11 · creatures 21 · central themes 17 · wide score 10 / tall 1.
Sources **W 14 / B 12 / R 16**, 25 lands, **11 unconditional taplands**.
Claimed tier B, metrics floor A.

**R4 — WHAT THE DECK IS NO LONGER SHORT ON.** Protection (3), artifact AND enchantment
answers (Requisition Raid, Cathar Commando, Untimely Malfunction), instant-speed
interaction (5). A pile card that offers *only* these is now redundant, not an upgrade.

**R5 — WHAT IT IS STILL SHORT ON.** Creature count fell 22 → 21 against a wide-score-10
plan. Starfield Shepherd's `creature card with mana value 1 or less` is down to **1**
target. And **BLACK IS TWO CARDS** (Fire Lord Zuko, Black Widow) against 12 sources — a
pile card that is black must justify the splash it is keeping alive.

**R6 — THE TAPLAND TAX IS THE REAL TEMPO CONSTRAINT.** 11 of 25 lands enter tapped
unconditionally. A pile card that wants to be cast on curve at 2 is worth less here than
its text suggests; one with flash, or a cheat cost, is worth more.

**R7 — STRUCTURALLY INVISIBLE.** `airbend`, `warp`, `plot`, `impulse` and `exile cast` are
themes the role classifier does not score; `cuts` and `suggest` will both mis-rank a card
whose whole value is R1. Grade from text, never from the fit number (G-67, K-04).

## 2. Standing error list

- **E1.** Do not read "exiles a permanent" as "triggers the exile payoffs." R1 splits it.
- **E2.** Do not grade a warp/plot card on its printed cost (R2).
- **E3.** Do not count a protection or artifact-answer card as filling a gap — R4 closed
  those on 2026-09-17. This is the freshest way to be wrong about this deck.

## 3. Cross-batch observations

- **AIRBEND IS NOT BLINK, AND THAT IS THE PILE'S BIGGEST SINGLE INSIGHT.** `airbend`
  reads "Exile it. While it's exiled, its owner **may cast it for {2}** rather than its
  mana cost." That is exile-then-CAST, so it pays **4/4** under R1 — where a plain blink
  pays 1/4. Glider Staff, Airbender's Reversal and Airbender Ascension's ETB are all in
  the 4/4 class. The user's instinct that these belong together was right; the ranking
  within the group is what R1 fixes.
- **THE PILE SPLITS ~11 / ~10 / ~10 on R1** (exile-then-cast / blink-only / neither), and
  the 4/4 group is where every top verdict landed. That is not a coincidence — it is R1.
- **TWO CARDS ARE STRAIGHTFORWARDLY DEAD AND BOTH LOOK ON-THEME**, which is the G-61 trap:
  Tinybones wants `whenever an OPPONENT discards` (deck 45 has **0** such sources) and
  Moonstone wants `whenever YOU discard` (**0** outlets). Counted, not assumed.
- **VARIANT SIGNAL (rule 7):** the discard-shaped rejects (Tinybones, Moonstone, The
  Infamous Cruelclaw's discard-to-cast) all point at **deck 70 Empty Threats**, not at a
  new deck. Tinybones is already deck 70's craft target. No variant is asking to be built.
- **THE BLACK QUESTION KEEPS RECURRING.** Ketramose ({1}{W}{B}), Syr Vondam ({W}{B}),
  Cruelclaw ({1}{B}{R}) and Huskburster ({7}{B}) are all real cards whose only problem is
  R5 — black is down to two cards against 12 sources. Taking any of them is a decision to
  KEEP the splash, not just to add a card.

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`

| card | cost | own | R1 class | verdict | why |
|---|---|---|---|---|---|
| Charred Foyer // Warped Space | {3}{R} front | craft M | 4/4 | **★★★** | back half: `once each turn, you may pay {0} rather than pay the mana cost for a spell you cast from exile` — a FREE 4/4 trigger every turn. Front is a repeatable upkeep impulse. Grade the front at MV 4, not the combined 10 (G-02) |
| Interdimensional Web Watch | {4} | ×1 | 4/4 | **★★★** | `{T}: Add two mana in any combination of colors. Spend this mana only to cast spells from exile` — a rock that powers only the thesis, and COLORLESS, so zero strain on W14/B12/R16 (R3) |
| Glider Staff | {2}{W} | ×1 | 4/4 | **★★** | airbend = recast for {2}; rebuys Etali (MV 6) for two mana. +1/+1 and flying as a rider |
| Goliath Daydreamer | {2}{R}{R} 4/4 | ×1 | 4/4 | **★★** | dream-counters every instant/sorcery you cast, then attacks to cast one FREE. Fuel counted: **9**, not the ~12 first assumed |
| Airbender's Reversal | {1}{W} | ×1 | 4/4 | **★★** | modal `destroy target attacking creature` OR airbend your own — never dead, instant speed |
| Ketramose, the New Dawn | {1}{W}{B} 4/4 | ×1 | — | **★★** | menace/lifelink/**indestructible** 4/4 for 3. Draw clause fires on exile from GRAVEYARD or BATTLEFIELD (warp/airbend/blink), **not** on impulse from library. R5 applies |
| Hex Magic | {2}{R} | ×1 | 4/4 | **★** | exiles your hand and redraws that many, all playable from exile — a refill where every card triggers |
| Aven Interrupter | {1}{W}{W} 2/2 | ×1 | 4/4 | **★** | the line is targeting YOUR OWN spell: it becomes plotted, you cast it later from exile. Taxes their graveyard/exile decks {2} as a rider |
| Solstice Revelations | {2}{R} | ×1 | 4/4 | **★** | free cast capped at MV < **4 Mountains**, i.e. MV ≤3. Flashback for the late game |
| Syr Vondam, Sunstar Exemplar | {W}{B} 2/2 | craft R | — | **★** | `whenever another creature you control dies OR IS PUT INTO EXILE` — grows on every warp/airbend/blink. R5 applies |
| Roving Actuator | {3}{R} 3/4 | craft U | 4/4 | **★** | Void is reliably on; copies an instant/sorcery MV≤2 from your yard (**8** targets) and casts the copy free |
| Bre of Clan Stoutarm | {2}{R}{W} 4/4 | ×1 | 4/4 | **★** | end-step free cast gated on lifegain; deck has lifelink + three life-gain lands |
| Airbender Ascension | {1}{W} | ×1 | 4/4 ETB, then 1/4 | **◇** | the ETB airbend is the good half; the quest-counter blink is slow and only 1/4 |
| Mardu Siegebreaker | {1}{R}{W}{B} 4/4 | ×1 | — | **◇** | deathtouch+haste 4/4 is a real body, but the exile is "until this leaves", not a recast. Four-colour-pip cost on a 3-colour mana base |
| The Neutrinos | {2}{R}{W} 2/4 | ×1 | 1/4 | **◇** | returns a creature **tapped and attacking** — tempo, but one payoff |
| Improvisation Capstone | {5}{R}{R} | ×1 | 4/4 | **◇** | enormous, and Paradigm recasts it free each turn — but MV 7 on an 11-tapland mana base (R6) |
| Chandra, Flameshaper | {5}{R}{R} | ×1 | 4/4 | **◇** | MV 7, same objection |
| Static Snare | {4}{W} | ×1 | — | **◇** | cheap with attackers, but R4 — answers are covered now |
| Salvation Swan / Ennis / Daydream / Go Ninja Go / Koya | 1–4 | ×1 | 1/4 | **△** | all blink. One payoff each. Daydream is the cheapest at {W}; Go Ninja Go the most flexible |
| The Mind Stone | {1}{W} | ×1 | 1/4 | **△** | a {W} source that is eventually a repeatable blink, but {5}{W} to harness |
| Joshua, Phoenix's Dominant | {1}{R}{W} | craft R | 1/4 | **△** | the exile-return costs {3}{R}{W} + tap. Saga side is fine, the trigger is not why |
| The Infamous Cruelclaw | {1}{B}{R} 3/3 | ×1 | 4/4 | **△** | free cast costs a DISCARD, and R5 |
| Huskburster Swarm | {7}{B} 6/6 | craft U | — | **△** | cost scales with creatures in exile/yard, so it gets cheap — but black, unowned, no payoff link |
| Alchemist's Assistant | {1}{B} 2/1 | ×1 | — | **△** | marginal body, black |
| Nexus of Becoming | {6} | ×1 | **0/4** | **✗** | exiles from HAND and creates a TOKEN — a token is neither cast-from-exile nor returned-from-exile. Triggers **nothing**. 6 mana |
| Tinybones, Bauble Burglar | {1}{B} | craft R | — | **✗** | `whenever an OPPONENT discards` — deck 45 has **0**. Dead. It is already deck 70's craft target, where it works |
| Moonstone, Harsh Mistress | {3}{B} | ×1 | — | **✗** | `whenever YOU discard` — **0** outlets in deck 45 |

## 5. Consolidated plan (live)

### Tier 1 — take these
1. **Interdimensional Web Watch** (owned, 0 wildcards) — cut **Heroes' Hangout**
   (`exile the top two… choose ONE of them`, the weakest of the impulse enablers, fit 19 / power 2).
2. **Glider Staff** (owned) — cut **Harnesser of Storms** (3 MV; its `or Otter spell` half is
   dead text, it is the only Otter, so it is 9-of-35 once per turn).
3. **Airbender's Reversal** (owned) — cut **Plasma Bolt** *only if* you want more airbend;
   otherwise hold, since interaction is already 9 and Plasma Bolt is an early drop (R6).

### Tier 2 — the one craft worth a wildcard
4. **Charred Foyer // Warped Space** (craft **1 Mythic**) — the best card in the pile, and
   the only craft that clears the bar. Nothing owned does what Warped Space does.

### Tier 3 — take if you want the body, not the trigger
5. **Ketramose, the New Dawn** (owned) — a 3-mana indestructible 4/4. Keeps black alive (R5).
6. **Goliath Daydreamer** (owned) — best if the instant/sorcery count grows past 9.

### PROTECT — what the ranking structurally cannot see (R7)
- **Spider-Verse, Appa, Fire Lord Zuko, Quintorius Kand, Etali** — the four payoffs plus
  the copy engine. `cuts` cannot score `exile cast`, so these sort on generic tags only.
- **Every warp/plot card.** Their printed cost over-reads them by ~0.45 avg MV (R2).
- **Requisition Raid / Cathar Commando / Untimely Malfunction / Valorous Stance /
  Restoration Magic / Boros Charm** — all newcomers, all flagged `✚ NEWCOMER` by `cuts`
  precisely because tag-fit under-reads them. Not cut candidates.
