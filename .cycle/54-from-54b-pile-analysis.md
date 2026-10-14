# 54b pile → deck 54 (Grand Lotus) — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into deck
54's `#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Source list:** every card named while tuning deck 54b on 2026-10-13/14 (user suggestions,
Claude suggestions, the ~96-card Sneak/flash list, cards added and cut), extracted from the
session transcript and matched against Standard-legal pool names. 404 names →
25 already in deck 54, 30 lands (graded separately, §4 Lands), 30 not castable on G/U/R
(✗ below, black or white pips) → **319 nonland cards to evaluate**, in batches of 30.

## 1. The decision framework

Live vector (2026-10-14, before any swap): interaction 6 (+6 unclassified) · card advantage
**2** · protection 2 · board power 33 over 14 creatures · avg MV 3.29 · TALL (wide score 1) ·
16 Lessons · 17 instants/sorceries · 21 noncreature nonland spells · floor B (midrange plan;
A needs +1 interaction, +2 card advantage).

1. **What a card costs here.** Once Iroh, Grand Lotus is out, a LESSON in the graveyard costs
   `{1}`, every turn, at sorcery or instant speed as printed. Uncle Iroh takes `{1}` off any
   Lesson spell; Doc Aurlock takes `{2}` off any graveyard/exile cast. A NON-Lesson instant or
   sorcery recasts at its FULL mana cost. A permanent pays full price and is never recast.
   ⇒ grade a Lesson on its effect, not its cost; grade everything else on printed cost.
2. **The graveyard counts are resources.** Lessons in yard (Combustion Technique, Bumi,
   Accumulate Wisdom's 3-gate), noncreature nonland cards (Dragonfly Swarm), instants and
   sorceries (The Dawning Archaic's discount). A non-Lesson replacing a Lesson costs a point.
3. **The deck is TALL and rarely attacks.** 14 creatures, printed power 33. Attack and
   combat-damage triggers (firebending, Sneak, Seifer, Bilbo, Newt, Raphael) are weak unless
   the body is evasive or the trigger is on ATTACK rather than damage. Firebending mana
   (red, expires at end of combat) has little to buy: most Lessons are sorceries.
4. **Mana is main-phase and three-colour.** G16 U14 R14 lands, 8 enter-tapped, double pips
   at 79.5% on curve. Colourless and hybrid costs are a bonus; triple pips are a cost.
5. **Needs, in order:** card advantage (2, Weak) > protection for Iroh (2) > interaction (6)
   > a second engine so Iroh is not the only recast source. A card that does two wins.
6. **"Mana SPENT" gates read LOW here; "mana VALUE" gates read HIGH.** A `{1}` Iroh flashback
   spends 1 (Uncover the Moon-Letters, Shantotto, Emperor of Palamecia barely fire); Thor deals
   the spell's mana VALUE, so a flashed-back Capstone is 7 damage for `{1}`.
7. **Per-cast triggers scale with Iroh.** Every `{1}` recast is a cast: "whenever you cast a
   noncreature spell" (Mechanist, Thor, Death to Our Enemies, Kraum's second spell) fire
   several times a turn.
8. **Engine conflicts (G-42).** Anything that exiles your own graveyard, or makes it exile,
   fights the deck (Festival of Embers, Emeritus of Ideation's attack, Abhorrent Oculus).
9. **Rotation.** Wizards skipped the 2026 rotation; WOE/LCI/MKM/OTJ/BLB/DSK leave Standard in
   early 2027 (Jan–Feb; exact day unconfirmed). `deck.py rotation` still says "~2026" for
   WOE–OTJ — treat those as early 2027. Flag a card from those sets; do not gate on it.

## 2. Standing error list

(none yet)

## 3. Cross-batch observations

- **Batch 1: R1 sinks most of 54b's red burn here.** A non-Lesson removal spell recasts at full price; a Lesson one at `{1}`. Lesson removal in the owned pool (Firebending Lesson, Lost Days, Zuko's Exile) beats every Burst Lightning / Bombard in this pile.
- **Iroh insurance is a real category:** Auroral Procession and True Ancestry return a dead Iroh; Bilbo and The Dawning Archaic are second recast sources.

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

### Not castable on G/U/R (✗, 30)
Armaggon, Azula Cunning Usurper, Barbed Bloodletter, Boros Charm, Bre of Clan Stoutarm, Cori
Mountain Stalwart, Cruel Administrator, Emet-Selch, Fire Lord Azula, Fire Lord Zuko, Great
Ugly-Looking Goblin, Heartflame Duelist, Lake-town Toymaker, Lightning Helix, Liminal Hold,
M.O.D.O.K., Nowhere to Run, Oltec Matterweaver, Poised Practitioner, Prayer of Binding,
Pursue the Past, Restoration Magic, Sage of the Skies, Sheltered by Ghosts, Sun Warriors, The
Legend of Yangchen, Uldaros Theorix, Wayspeaker Bodyguard, Winter Misanthropic Guide, Xande.

### Batch 1 (1–30)

| Card | 54 | Note (rule) |
|---|---|---|
| Aang's Journey | △ | Lesson `{2}`: basic to HAND, +2 life. With Iroh a `{1}` land each turn; +1 Lesson (R2). Shared Roots already does the job better (to battlefield). |
| Abstract Paintmage (craft U) | ◇ | Adds `{U}{R}` each first main, instants/sorceries only — flashback casts count. Ramp for the hard-cast turns. |
| Ancestors' Aid | ✗ | Combat trick (R3). |
| Anzrag, the Quake-Mole (craft M) | ✗ | Extra combat on block (R3). |
| Aquitect's Defenses | ◇ | Flash aura: hexproof until end of turn + `+1/+2`. One-shot cover for Iroh (R5 protection). |
| Archmage's Newt | △ | Needs combat damage (R3); OTJ, rotates early 2027 (R9). |
| Asinine Antics (craft M) | △ | Every opposing creature becomes 1/1 — real mass answer, but a mythic craft from WOE, gone early 2027 (R9), non-Lesson (R1). |
| Auroral Procession | ★ | `{G}{U}` instant: "Return target card from your graveyard to your hand." Returns a DEAD IROH (R5 single engine) or any Lesson. Card-neutral. |
| Balmor, Battlemage Captain | ✗ | Team pump on spell cast — attack payoff (R3). |
| Balthier and Fran (craft R) | ✗ | Vehicles. |
| Bear Trap (craft C) | △ | Colourless flash artifact, `{3}`, sac: 3 damage to a creature. Works; DSK (R9). |
| Beast, Erudite Aerialist | △ | Draws on combat damage only (R3). |
| **Bilbo, Thief in the Night** | ★★ | "Spells you cast from anywhere other than your hand cost {1} less" — Iroh's `{1}` Lesson flashback becomes **free**, and it stacks with Doc Aurlock. Attack trigger casts an instant/sorcery from the yard — a second recast source (R5) that only needs to ATTACK (R3). The Doc Aurlock replacement when OTJ rotates. |
| Bitter Work | ◇ | Draws when a power-4+ creature attacks: Iroh 5/5, Thor 5/5 flier, Bumi, earthbent lands. Rarely attacks (R3). Exhaust earthbend 4 is real. |
| Blazing Crescendo | ✗ | Trick (R3). |
| Blazing Firesinger // Seething Song | ◇ | Enters prepared: a free copy of "Add {R}{R}{R}{R}{R}" — one big hard-cast turn (Capstone from hand turn 5). One-shot. |
| Blooming Blast (craft U) | △ | 2 damage, non-Lesson (R1). Firebending Lesson does it as a Lesson. |
| Bombard | △ | 4 damage instant `{2}{R}`, non-Lesson (R1). Best non-Lesson burn here if wanted. |
| Brazen Collector | ✗ | Attack mana (R3). |
| Breaching Dragonstorm | ★ | 5-mana enchantment: free-cast the first nonland card off the top if MV ≤ 8. Hits here: Capstone (7, starts its Paradigm), Symposium, Germination, Iroh, Bumi, Thor. Noncreature cast (R7). |
| Brineborn Cutthroat | ✗ | Opponent's-turn casting. |
| **Bruce Banner // The Incredible Hulk** | ★★ | `{U}` 1/1: "{X}{X}, {T}: Draw X cards" — a mana sink that turns the deck's ramp into cards (R5, CA). Flips for `{2}{R}{R}{G}{G}`, exactly Temur, into a reach/trample Hulk. |
| Bulk Up | ✗ | Trick. |
| Bumi, Unleashed | ◇ | 5/4 trample, earthbend 4 on entry; the land-only extra combat needs damage (R3). |
| Burner Rocket | ✗ | Vehicle trick. |
| Burrog Befuddler (craft C) | ✗ | Flash -1/-0. |
| Burst Lightning | △ | 2/4 damage any target, non-Lesson (R1). |
| Buster Sword | ✗ | Combat damage (R3). |
| Captain Howler, Sea Scourge | △ | Discard payoff; only Sokka discards here. |
| Caught in the Crossfire | △ | 2 to each non-outlaw creature — a sweeper, non-Lesson, OTJ (R9). Iroh's Demonstration already pings. |

## 5. Consolidated plan (live)

(after batch 1)
