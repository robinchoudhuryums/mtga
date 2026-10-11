# Sultai Manifest Dread pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete this file once the deck is drafted (`/draft-deck`) and the
findings are folded into its `#: notes:` block. It is a scratchpad, not a source of truth;
decks/ are.

**Source list:** Robin's pile, 2026-10-11. It has 118 distinct names (≈126 copies) and
targets a NEW deck. The working copy is the scratchpad `sultai-pile.txt`. Copies are shared
across decks, so the 62 names already in other decks stay as candidates.
**Anchors (owner):** the strong Sultai Tarkir (TDM) cards, plus Hauntwoods Shrieker.
**Pile profile:** 42 G, 30 BG, 19 BGU, 18 GU, 4 U, plus 5 others by identity. Pips are
G 114 / B 45 / U 37. That means green is the base and U and B are both secondary. 74 of the
118 are creatures.
**Neighbours to stay distinct from:** 62 (UBG wrath-reanimator, which already runs
Shrieker and Undergrowth Recon), 31 (BG elves/poison) and 82 (UW surveil; it once ran
Oculus). Run `similar` at the end.

## 1. The decision framework

**F1. The dread EVENT is the resource.** One `manifest dread` produces three things:
- a 2/2 body;
- one card in your graveyard;
- a choice of 2 cards (selection).

So a card's value is how many dread events it makes, or how much it pays per event:
- *Makers:* Shrieker (on attack), Under the Skin, Valgavoth's Onslaught, Threats Around
  Every Corner, Moldering Gym's Weight Room, Dissection Tools, Growing Dread, Break Down
  the Door, Defiant Survivor, Oculus (each opponent upkeep).
- *Per-event payoffs:* Paranormal Analyst (the binned card goes to hand instead of the
  graveyard), Threats (a land per face-down entry), Cryptid Inspector, Growing Dread
  (counter on turn-up), Oblivious Bookworm.

The deciding number is **dread events per game**. Count makers before grading a payoff (G-61).

**F2. A manifested NONCREATURE stays a vanilla 2/2 forever.** Only a creature card can be
turned face up. Two numbers therefore decide the "turn face up" payoffs (Growing Dread,
Cryptid Inspector, Bookworm, Hustle // Bustle):
- **library creature density**;
- whether a creature's face-up text is **worth paying its full cost for at instant speed**.

Turning a card face up is not casting it. Cast triggers do not fire, but "enters" does
NOT fire either. Grade every ETB creature as a weaker dread hit.

**F3. Dread is also self-mill: one card per event.** Graveyard payoffs read four different
numbers. Do not conflate them (the "value vs spent" lesson):
- **card types** (delirium, 4 or 6): Spineseeker, Flytrap;
- **card count**: Oculus exiles 6, which is a COST that empties the yard;
- **"leaves your graveyard"**: Kishla Skimmer, Essence Anchor. Renew, escape, land-from-yard
  and Oculus's cost all FEED these;
- **creature cards in the graveyard**: Moon-Vigil Adherents.

Oculus is the G-42 shape: it eats the yard that delirium and Moon-Vigil count, while it
feeds the "leaves" triggers. **Exile and delirium in the same list must be counted against
each other.**

**F4. Mana: green base, with U and B as a two-colour splash pair.** Fixing in the pile:
- 4× Sultai Devotee ({1}: B, G or U, once per turn);
- 2× Opulent Palace;
- Sultai Monument, which fetches a basic;
- basic fetchers: Threats, Moldering Gym, Spineseeker.

Deciding numbers:
- **double-B / double-U pips** on non-green cards;
- **three-colour gold cards** at 3 MV or less. These want sources ON CURVE, and a dork
  that taps once per turn fixes only one pip.

Grade with `consistency` on a scratch list, never by hand.

**F5. Lands-from-graveyard is a parallel sub-engine. It surfaced in batch 1 and is a
VARIANT SIGNAL.** Members so far:
- Mole Man (landfall Moloid);
- Icetill Explorer (extra land, landfall mill);
- Glacierwood Siege (Sultai mode);
- Undergrowth Recon;
- Elemental Teachings.

Dread bins a land roughly 40% of the time, so the two engines share the graveyard. The
question is DENSITY: about 5 cards is a sub-theme, not a deck. Track it in §3.

**F6. +1/+1 counters are the third axis.** It is the Tarkir-Sultai payoff Hollowmurk Siege
reads (a counter means a draw, once per turn). Members: Growing Dread, Cryptid Inspector,
Valgavoth's Onslaught, Weight Room, Host of the Hereafter, Flytrap. The question is whether
it shows up as a COUNT or only as incidental riders.

**F7. Format is Standard, 60 cards.** The tier floor wants interaction ≥4 for B and ≥7 for
A (`TIER_FLOOR_REQ`). The pile is creature-heavy green, so interaction is the axis most
likely to be short. Count it per batch.

**F8. Structurally invisible to the tools (watch these by hand):**
- *Manifest dread IS tagged* (`manifest dread`), but turn-face-up value (F2) has no tag.
- *"Leaves your graveyard"* triggers have no specific theme; they ride `graveyard`.
- *Mana dorks with any-colour output:* Devotee is tagged `removal` (deathtouch) and
  carries no fixing tag, so `cuts` may undervalue it as fixing (K-03 residual).
- *Selection from dread* (choose 1 of 2) is not card advantage to the role model.

## 2. Standing error list

(Every misreading goes here, so a later batch does not repeat it.)

## 3. Cross-batch observations

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

## 5. Consolidated plan (live)
