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

(none yet)

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

### Not castable on G/U/R (✗, 30)
Armaggon, Azula Cunning Usurper, Barbed Bloodletter, Boros Charm, Bre of Clan Stoutarm, Cori
Mountain Stalwart, Cruel Administrator, Emet-Selch, Fire Lord Azula, Fire Lord Zuko, Great
Ugly-Looking Goblin, Heartflame Duelist, Lake-town Toymaker, Lightning Helix, Liminal Hold,
M.O.D.O.K., Nowhere to Run, Oltec Matterweaver, Poised Practitioner, Prayer of Binding,
Pursue the Past, Restoration Magic, Sage of the Skies, Sheltered by Ghosts, Sun Warriors, The
Legend of Yangchen, Uldaros Theorix, Wayspeaker Bodyguard, Winter Misanthropic Guide, Xande.

## 5. Consolidated plan (live)

(after batch 1)
