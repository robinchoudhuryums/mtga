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

**F9 (added in batch 1, from reading Shrieker in full). A big creature in the LIBRARY is a
dread lottery ticket, not dead weight.** Shrieker ({1}{G}, repeatable) and Bustle both turn
a manifested creature face up without paying its cost. So a 6–8 MV creature is a premium hit
whenever a dread lands on it. With Paranormal Analyst or Under the Skin, a binned fatty is
also not lost. The deciding number is how many **high-MV creatures you would happily flip
for {1}{G}**, set against Shrieker density (2 in the pile). Without Shrieker, F2's
pay-the-cost read applies.

**F8. Structurally invisible to the tools (watch these by hand):**
- *Manifest dread IS tagged* (`manifest dread`), but turn-face-up value (F2) has no tag.
- *"Leaves your graveyard"* triggers have no specific theme; they ride `graveyard`.
- *Mana dorks with any-colour output:* Devotee is tagged `removal` (deathtouch) and
  carries no fixing tag, so `cuts` may undervalue it as fixing (K-03 residual).
- *Selection from dread* (choose 1 of 2) is not card advantage to the role model.

## 2. Standing error list

(Every misreading goes here, so a later batch does not repeat it.)

- **E1 (caught while writing F2): Shrieker's `{1}{G}` flip is FREE.** It reads "Reveal
  target face-down permanent. If it's a creature card, you may turn it face up", with no
  mana-cost payment. F2's "worth paying full cost" therefore does not apply while a Shrieker
  is out. See F9.

## 3. Cross-batch observations

- **(batch 1) The dread core is DEEP.** There are 10 makers in the first 30:
  - repeatable: Shrieker ×2, Oculus, Defiant Survivor;
  - one-shot: Under the Skin, Onslaught, Threats, Weight Room, Dissection Tools,
    Growing Dread, Break Down the Door.

  The payoffs alone (Analyst, Inspector, Bookworm, Growing Dread, Threats) are not enough
  to anchor the deck. **The real anchor is that each dread is a 2-for-1 already**: a body
  plus a binned card plus selection.
- **(batch 1) "Leaves your graveyard" is a live cross-engine.** Kishla Skimmer and Essence
  Anchor read it. Many sources feed it:
  - Oculus's exile cost;
  - Paranormal Analyst (the binned card moves to hand);
  - Under the Skin and Restore with Empathy regrowth;
  - every land played from the yard (Mole Man, Icetill, Glacierwood Sultai, Recon).

  Kishla is the cheapest repeatable draw so far.
- **(batch 1) VARIANT SIGNAL — lands-from-graveyard (F5).** Five cards: Mole Man, Icetill,
  Glacierwood Siege, Undergrowth Recon, Elemental Teachings. Too few on its own. Hold it
  and decide at the end.
- **(batch 1) Counters (F6).** Members: Hollowmurk Siege, Growing Dread, Cryptid Inspector,
  Onslaught, Weight Room, Host, Flytrap. Hollowmurk's Sultai mode needs about one counter
  event per turn. The repeatable sources so far are Inspector (each face-down entry or flip)
  and Flytrap (attacks, when delirium is on). Thin but real.
- **(batch 1) Interaction is SHORT already.** In 30 cards: Break Down the Door (artifact or
  enchantment exile), Devotee deathtouch and Dissection Tools deathtouch. There is no
  creature removal yet. This is the F7 axis to watch.

- **(batch 2) "Cards LEAVE your graveyard during your turn" is TDM-Sultai's own mechanic,
  and the pile carries the full cluster.** Payoffs: Kishla Skimmer (draw), Kheru Goldkeeper
  (Treasure) and Attuned Hunter (+1/+1 counter, which feeds F6). Feeders added in this batch:
  - renew (Champion of Dusan, Goldkeeper itself);
  - Teval's delve on every spell;
  - Auroral Procession, Lie in Wait, True Ancestry, Awaken's chapter III.

  The three payoffs each trigger once per turn, so ONE leave event per turn saturates them,
  and that is easy to reach. **This is the second engine, and it CONSUMES what dread FILLS.**
  The deck's shape is dread → yard → leave-yard payoffs. Delirium and Moon-Vigil are the
  cards that want the yard to STAY full (F3), so they rank below the leave cluster.
- **(batch 2) Interaction is SOLVED in this batch.** Eight cards: Kin-Tree Severance,
  Lie in Wait, Fangkeeper's Familiar, Awaken the Honored Dead, Felling Blow, Dragonclaw
  Strike, Budding Insurgent, plus Break Down the Door from batch 1. An A floor (7) is
  reachable without strain.
- **(batch 2) Fixing (F4).** Enduring Vitality makes every creature tap for any colour, and
  that includes face-down 2/2s, so it is fixing on a body. Other sources: Opulent Palace ×2,
  Ancient Cornucopia, Devotee ×4. The {2/B}{2/G}{2/U} hybrids (Gurmag Nightwatch, Rakshasa's
  Bargain, Kin-Tree, Dragonclaw) cost 3 with all colours and are castable with ANY, so they
  are never a mana failure, only a tempo tax.
- **(batch 2) Tokens are thin.** Quina doubles tokens, and the token makers so far are
  Monument, Essence Anchor and Goldkeeper Treasure. Face-down dread creatures are NOT
  tokens.

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

### Batch 1 (cards 1–30)

| Card | Verdict | Note |
|---|---|---|
| Hauntwoods Shrieker ×2 | ★★★ | Anchor. Repeatable dread on attack, and `{1}{G}` is a FREE flip (F9). |
| Abhorrent Oculus | ★★ | 3-MV 5/5 flier with a dread every opponent upkeep. Its 6-card exile fights delirium and Moon-Vigil, but feeds Kishla (F3). |
| Growing Dread | ★★ | 2-mana flash dread; puts a counter on each flip (F6). |
| Paranormal Analyst | ★★ | Every dread becomes +1 card in hand. Also a "leaves yard" trigger. Pulls against delirium (F3). |
| Valgavoth's Onslaught | ★★ | X=2 at 5 mana gives two 3/3s, 2 binned cards and selection. Scales late. |
| Under the Skin | ★★ | Dread plus regrowth of a permanent card (lands included). A 3-mana 3-for-1. |
| Sultai Devotee ×4 | ★★ | The deck's fixing (F4) on a deathtouch 2-drop. U and B come from the ability only. |
| Kishla Skimmer | ★★ | GU 2/2 flier. Draws once per turn when a card leaves the yard, and many sources feed it. |
| Hollowmurk Siege | ★★ | Sultai mode draws once a turn per counter. Abzan mode makes counters itself (attack: +1 counter and menace). Pick the mode per game. |
| Break Down the Door | ★ | Instant modal: artifact or enchantment exile, OR dread. Interaction (F7). |
| Moon-Vigil Adherents | ★ | Face-down 2/2s count as creatures, and dread bins creature cards. Often 6/6+ trample. |
| Omnivorous Flytrap | ★ | Delirium counters on ETB and attack. Dread bins varied types (F3). |
| Cryptid Inspector | ★ | Grows on each face-down entry and flip. Repeatable counters for Hollowmurk. |
| Oblivious Bookworm | ★ | End-step draw that skips the discard on any dread or flip turn. |
| Moldering Gym // Weight Room | ★ | 3-MV ramp front; 6-MV back gives a dread with 3 counters (a 5/5). |
| Threats Around Every Corner | ◇ | A dread plus a land per face-down entry. Ramp needs a sink. |
| Defiant Survivor | ◇ | A dread when it attacks, but a 3/2 attacker for 3 dies early. |
| Dissection Tools | ◇ | 5 colourless for a 4/4 deathtouch lifelink face-down. Equip costs a creature. |
| Hustle // Bustle | ◇ | The Bustle half is a G-castable overrun plus a free flip. Hustle is {U/R}, castable with U. |
| Riddles in the Dark | ◇ | Instant pile split: +2 cards and 2 binned. |
| Essence Anchor | ◇ | Upkeep surveil plus Zombies on any turn a card left the yard. |
| Spineseeker Centipede | ◇ | Basic land to hand; delirium makes it a 3/3 vigilance. |
| Sultai Monument | ◇ | Fetches a basic for 2; late, two Zombies. |
| Glacierwood Siege | ◇ | F5 card (Sultai mode); Temur mode self-mills 4 per spell. |
| Mole Man, Moloid Master | ◇ | F5. Lands from the yard plus landfall Moloids. |
| Icetill Explorer | ◇ | F5. Extra land, lands from the yard, landfall mill. |
| Undergrowth Recon | ◇ | F5. Needs lands in the yard, which dread supplies. |
| Restore with Empathy | △ | 3-mana instant regrowth +4 life. Under the Skin does more. |
| Elemental Teachings | △ | 5-MV ramp. Only interesting under F5. |

### Batch 2 (cards 31–60)

| Card | Verdict | Note |
|---|---|---|
| Kin-Tree Severance | ★★ | Instant exile of any permanent with MV ≥3. {2/W}{2/B}{2/G}, so 4 mana in BG. |
| Lie in Wait | ★★ | Regrow a creature, then bite for its power. Removal plus card advantage plus a leave event. A BGU 3-drop, so it needs fixing on curve. |
| Fangkeeper's Familiar | ★★ | Flash 3/3 with three modes: surveil 3 and 3 life, enchantment kill, or counter a creature spell. |
| Awaken the Honored Dead | ★★ | Saga: I kills a nonland permanent, II mills 3, III regrows a creature or land. |
| Teval, Arbiter of Virtue | ★★ | 5-MV 6/6 flying lifelink that gives delve to everything. Delve is a leave engine (F3 tension with delirium). |
| Enduring Vitality | ★★ | Every creature taps for any colour, face-down ones included. Fixing (F4) on a recursive body. |
| Opulent Palace ×2 | ★★ | Tapped tri-land. Take both. |
| Kheru Goldkeeper | ★ | 4-MV 3/3 flier; Treasure on leave events; renew grants 2 counters and flying. |
| Attuned Hunter | ★ | 3/3 trample that gains a counter on leave events. Bridges the leave and counters engines. |
| Champion of Dusan | ★ | 4/2 trample for 3. Renew from the yard gives a counter and trample. Dread bins it, so it is value either way. |
| Stalwart Successor | ★ | 3/2 menace. Adds +1 counter to each creature's first counter of the turn. |
| Auroral Procession | ★ | 2-mana instant regrowth of ANY card. A leave event on your turn. |
| Rakshasa's Bargain | ★ | Instant: dig 4, keep 2, bin 2. Fills and draws. |
| Tarmogoyf | ★ | 2-drop that reads every graveyard. Dread plus mill makes it 4/5+. |
| Something Worth Saving | ★ | 2-mana mill 4, keep a permanent. Delirium fuel. |
| Felling Blow | ★ | Counter plus bite (sorcery). Interaction and F6. |
| Dragonclaw Strike | ◇ | Double P/T, then fight. 4 mana in GU. Interaction, but sorcery and creature-dependent. |
| Gurmag Nightwatch ×2 | ◇ | 3/3 that mills 2 or 3 with selection. Filler fuel. |
| Lotuslight Dancers | ◇ | 5-MV 3/6 lifelink that entombs a B, a G and a U card. Feeds Lie in Wait and delirium. |
| True Ancestry | ◇ | Regrow a permanent plus a Clue. |
| Kotis, the Fangkeeper | ◇ | Indestructible 2/1. Its free-cast trigger needs connected damage. |
| Budding Insurgent | ◇ | 3/3 vigilance; sacrifice it to kill an artifact or enchantment. |
| Ancient Cornucopia | ◇ | Mana rock plus life. Vitality does the fixing better. |
| Emil, Vastlands Roamer | ◇ | Trample for creatures with counters; a Fractal maker as a mana sink. |
| Inspiring Call | ◇ | Draws per creature with a counter. Needs Onslaught-level density. |
| Cycle of Renewal | △ | Land-swap ramp. Only interesting under F5. |
| Michelangelo, Game Master | △ | Disappear counter. Few leave-battlefield events here. |
| Gardenize | △ | Mana from creature deaths. Not this deck's axis. |
| Quina, Qu Gourmet | △ | Token doubler with almost no tokens (face-down creatures are not tokens). |
| Death Begets Life | △ | 8-MV wrath in a creature deck. It already lives in deck 62. |

## 5. Consolidated plan (live)
