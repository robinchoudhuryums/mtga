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

## 5. Consolidated plan (live) — rewritten 2026-09-17 after batch 2

**The cut pool changed the shape of this.** The user named 11 cards they are willing to
cut; **10 are live** (Long Goodbye was already swapped out for Boros Charm on 2026-09-16).
With ten slots available the question stops being "what one upgrade" and becomes "what
package", so the plan below is ordered as matched pairs.

### Tier 1 — take, all owned, 0 wildcards
| # | add | cut | why this pair |
|---|---|---|---|
| 1 | **Interdimensional Web Watch** {4} | **Korvold and the Noble Thief** | Both MV 4, both heist-flavoured. Korvold's exile is CHAPTER III — three turns away. The Watch does it on ETB and then taps for mana that can only cast from exile. Colourless, so no strain on W14/B12/R16 |
| 2 | **Anticausal Vestige** {6} / **warp {4}** | **Weftblade Enhancer** | Straight warp-body upgrade at the same printed MV 6. `When this creature LEAVES the battlefield, draw a card, then you may put a permanent card with MV <= lands you control from your hand onto the battlefield` — and warp makes it leave ON PURPOSE, then it recasts from exile for 4/4 (R1). Colourless |
| 3 | **Web-Warriors** {4}{G/W} -> castable {4}{W} | **Stagecoach Security** | The cleanest upgrade in the pile. Stagecoach's anthem is `until end of turn`; Web-Warriors' `+1/+1 counter on each OTHER creature you control` is PERMANENT, on a 4/3 body, across 21 creatures. Owned x2 |
| 4 | **Glider Staff** {2}{W} | **Harnesser of Storms** | airbend = recast for {2} = 4/4 (R1). Harnesser is 9-of-35 fuel once per turn and its `or Otter spell` half is dead text — it is the only Otter |
| 5 | **Airbender's Reversal** {1}{W} | **Plasma Bolt** | modal `destroy target attacking creature` OR airbend your own (4/4). Interaction is already 9, so trading one burn spell for a modal one costs nothing |

### Tier 2 — the one craft worth a wildcard
| # | add | cut | why |
|---|---|---|---|
| 6 | **Charred Foyer // Warped Space** (craft **1 Mythic**) | **Crimson Operative** | Same job, vastly better rate: Crimson Operative impulses ONCE on ETB for MV 4; Charred Foyer does it EVERY upkeep, and the back half (`once each turn, you may pay {0} rather than pay the mana cost for a spell you cast from exile`) is a free 4/4 trigger every turn |

### Tier 3 — real, take if you want that axis
| add | cut | note |
|---|---|---|
| **Ketramose, the New Dawn** | Rayblade Trooper *or* Cruel Alliance | indestructible 4/4 for 3. Keeps the black splash alive (R5) |
| **Goliath Daydreamer** | Erode | fuel counted at **9** instants/sorceries |
| **Hex Magic** / **Aven Interrupter** | Cruel Alliance / Erode | both real, both behind the above |
| **Krang & Shredder** | Virtue of Loyalty | heist + free cast from exile is very on-theme, but `{4}{B}{B}` at MV 6 against **12 black sources** is the heaviest ask in the pile (R5) |

### Batch-2 rejects, with the reason
- **Triple Triad** `{3}{R}{R}{R}` — the effect is the thesis (free cast from exile every
  upkeep), the COST is not castable here. The deck's own `consistency` table already reads
  `{R}{R}` on turn four at **81.7%** against a wanted 20 sources with 16 held; triple-R at
  six is a strictly heavier demand on the same base, with 11 unconditional taplands (R6).
- **Tragic Trajectory** — `{B}` for **-10/-10 with Void** is premium removal and Void is
  reliably on. Held back only by R5 (black is two cards) and it is a craft.
- **Spider-Punk / Spider-Woman** — Spider-Verse's `the legend rule doesn't apply to Spiders
  you control` is currently dead text, and these would switch it on, but the unlock is
  narrow: it only matters for a LEGENDARY Spider you have two of, i.e. one you copied with
  Spider-Verse itself. Spider-Punk's `spells and abilities can't be countered` is the more
  real line. **Web-Warriors is in Tier 1 on its own merits, not as a Spider.**
- **All-Fates Stalker** — `screen` calls it KEY; the text argues down. Its ETB exiles
  `until this creature leaves the battlefield`, and warping it makes it leave at the next
  end step, handing the creature straight back. The two halves fight each other.
- **Hylderblade / Interceptor Mechan** — both black, both marginal; equip {4} and a
  2/2 flier respectively.

### PROTECT — what the ranking structurally cannot see (R7)
- **Spider-Verse, Appa, Fire Lord Zuko, Quintorius Kand, Etali** — `cuts` cannot score
  `exile cast`, so these sort on generic tags only.
- **Every warp/plot card.** Printed cost over-reads them by ~0.45 avg MV (R2).
- **The six newcomers** (Requisition Raid, Cathar Commando, Untimely Malfunction, Valorous
  Stance, Restoration Magic, Boros Charm) — `cuts` flags them `NEWCOMER` precisely because
  tag-fit under-reads them.
- **Virtue of Loyalty is the one Tier-3 cut to think twice about**: its enchantment half is
  a repeatable end-step anthem AND untapper, which is a Fire Lord Zuko effect that repeats
  every turn. It is on the willing-to-cut list, but it is the best card on that list.
