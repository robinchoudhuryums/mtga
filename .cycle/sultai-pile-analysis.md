# Sultai Manifest Dread pile — analysis (TEMPORARY working doc)

**Status: DRAFTED as deck 83 (`decks/83-grave-dread/`) on 2026-10-11; the owner is still
refining it.** The durable findings are already in deck 83's `#: notes:`. Delete this file
when refinement ends; until then, its per-card verdicts are the bench. It is a scratchpad, not a source of truth;
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
- **E2 (batch 4): turning a card face up is NOT entering the battlefield.** ETB triggers
  and "enters with" riders never fire on a flipped dread creature. That makes these WORSE
  lottery hits: Omega's Wave Cannon, Hapatra's −1/−1 counters, Zegana's draw, Lotuslight
  Dancers' tutor, Fangkeeper's Familiar's mode, Leatherhead's hexproof counter and Lasyd
  Prowler's mill. Good hits are STATIC or ATTACK/DAMAGE-triggered: Koma, Muldrotha, Teval,
  Sin (the attack trigger works), Quandrix (a 6/6 flying trample body; the cascade is lost
  because it is a cast trigger), and Witherbloom the Balancer.
- **E3 (batch 4): a face-down creature has mana value 0.** Vicious Rivalry kills your own
  manifests even at X=0. This is the G-42 shape: a fine card that fights the engine.

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

- **(batch 3) A dread creature is a NONTOKEN creature entering.** So Warden of the Grove
  endures X on every dread. That makes it a repeatable counter source that scales with
  dread density. It also feeds Hollowmurk (draw) and Stalwart Successor (+1). Bogwater
  Lumaret and Quina's frogs do not care about this, but Warden does.
- **(batch 3) Jenova ↔ Shrieker.** Shrieker is printed a Beast **Mutant**. Jenova puts
  counters every combat (a Hollowmurk trigger) and draws on a Mutant dying on your turn.
  It is a small synergy, not a reason to build.
- **(batch 3) The graveyard splits into two clusters. Count both before choosing.**
  - **STAY-FULL:** Exdeath (needs 6 permanent cards), Moon-Vigil, Tarmogoyf, Avatar Destiny,
    Flytrap and Spineseeker (delirium), Drag to the Roots (delirium discount), and Kraven's
    Last Hunt (reads the greatest power in the yard).
  - **LEAVE:** Kishla, Goldkeeper, Attuned Hunter, Cosmogoyf (counts exile), Teval,
    Oculus, renew.

  Delirium survives the leave engine because it counts TYPES, not cards. Exdeath's
  6 permanents and Oculus's 6 cards compete directly.
- **(batch 3) F5's lands-from-yard signal is GROWING.** New this batch: Primal Witchstalker
  (mill 4 and put a land back), Lasyd Prowler (renew scales with lands in the yard),
  Lluwen, Imperfect Naturalist (Worms per land), Traveling Chocobo. That is about 10 cards.
  Still a sub-theme; it may become a variant.
- **(batch 3) Interaction is now ABUNDANT, so be picky about quality.** New: Drag to the
  Roots, Kraven's Last Hunt, Deadly Brew, Witherbloom Charm, Professor Dellian Fel. That is
  13 candidates so far. Prefer instant speed, cheap costs, and cards that also fill or
  leave the yard.

- **(batch 4) Muldrotha and Glarb are the two engines that make the leave cluster
  REPEATABLE.**
  - Muldrotha plays a land and casts one permanent of each type from the yard every turn.
    Each one is a leave event (Kishla, Goldkeeper, Attuned Hunter) and also F5's land
    replay.
  - Glarb surveils 2 every turn, which fills the yard, and casts MV ≥4 spells off the top.
- **(batch 4) VARIANT SIGNAL 2: a Temur-less "big lottery" ramp shell.** Koma, Quandrix,
  Omega, Zegana, Bonny Pall, Sin and Witherbloom the Balancer, with Shrieker flipping them
  for {1}{G}. Only Shrieker ×2 and Bustle flip for free, so this is too thin to build
  around. Run 2–3 of them as top-end that is ALSO a dread hit, not more.
- **(batch 4) The F5 lands sub-engine reached about 14 cards.** Additions: Bonny Pall,
  Silvan Reveler, Tam Observant Sequencer, Thranduil Sindarin Liege, Muldrotha.

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

### Batch 3 (cards 61–90)

| Card | Verdict | Note |
|---|---|---|
| Drag to the Roots | ★★ | Instant: destroy a nonland permanent. 2 mana with delirium. |
| Kraven's Last Hunt | ★★ | Saga: I mills 5 and deals damage equal to the yard's best power (removal); II pumps +2/+2; III regrows a creature. |
| Warden of the Grove | ★★ | Grows each end step; every dread (a nontoken creature) endures X. A counters engine. |
| Witherbloom Charm | ★ | Instant modes: sacrifice and draw 2, 5 life, or kill a nonland permanent with MV ≤2. |
| Deadly Brew | ★ | 2-mana edict. Sacrifice a dud face-down 2/2, then regrow a permanent. |
| Professor Dellian Fel | ★ | 4-MV walker: −3 kills a creature; 0 draws. |
| Exdeath ×2 | ★ | 3-MV 3/3 that gains 3 life and flips at 6 permanent cards in the yard. Stay-full cluster. |
| Lasyd Prowler | ★ | 5/5 for 4 that mills (one per land you control). Renew counters scale with yard lands. |
| Primal Witchstalker | ★ | 3-MV menace that mills 4 and puts a land back (ramp). F5. |
| Seedship Broodtender | ★ | 2-MV 2/3 that mills 3; late, a sorcery-speed reanimation. |
| Jenova, Ancient Calamity | ★ | Counters every combat; draws when a Mutant dies (Shrieker is one). |
| Leatherhead, Swamp Stalker | ★ | 5/4 trample hexproof for 4. Spend a counter to kill an artifact or enchantment. |
| Cosmogoyf | ◇ | Power equals cards you own in exile. Big only with Oculus, Teval or renew. |
| Avatar Destiny | ◇ | +1/+1 per creature card in the yard; reanimates on death. |
| Kona, Rescue Beastie | ◇ | 4/3. When it attacks, cheat a permanent from hand. |
| Lluwen, Imperfect Naturalist | ◇ | 2-MV mill 4 with setup. Worms per land is F5. |
| Lluwen, Exchange Student | ◇ | 3/4. Exiles a creature card (a leave event) to re-prepare a Pest. |
| Rite of Renewal | ◇ | Regrows two permanents. Sorcery, and exiles itself. |
| Essenceknit Scholar | ◇ | Draws if a creature died. Sacrifice outlets are thin here. |
| Long Feng, Grand Secretariat | ◇ | A counter when a creature or land hits the yard from play. |
| Beifong's Bounty Hunters | ◇ | 4/4. Earthbends on creature death. |
| The Chief Warg | ◇ | Menace; draws on attack with power ≥4 (Moon-Vigil, Lasyd, Leatherhead). |
| Traveling Chocobo | ◇ | Lands from the top. F5 only. |
| Zanarkand // Lasting Fayth | ◇ | Tapped G land with a late Hero token. |
| Bogwater Lumaret | △ | Lifegain on creature entry. No lifegain payoff here. |
| Old-Growth Educator | △ | Infusion 4/4 reach. Lifegain is thin. |
| Blech, Loafing Pest | △ | Counts only Snake, Insect and Pest bodies plus lifegain. |
| Chief Warg's Company | △ | Wolf gate. |
| Way of the Paradox | △ | Jace token plus an extra land. Off-plan. |
| Skystinger | △ | Reach hoser. |

### Batch 4 (cards 91–118)

| Card | Verdict | Note |
|---|---|---|
| Muldrotha, the Gravetide | ★★ | A permanent of each type plus a land from the yard every turn. The leave engine's best card. Also a good dread hit (static). |
| Glarb, Calamity's Augur | ★★ | BGU 3-drop with deathtouch. Surveil 2 each turn fills the yard; casts MV ≥4 off the top. |
| Quandrix, the Proof | ★ | 6/6 flying trample with cascade. A good dread hit (the body survives a flip). |
| Koma, World-Eater | ★ | Hard to cast (31%→61% on curve), but the best Shrieker flip in the pile. |
| Sin, Spira's Punishment | ★ | 7/7 flier. Enter/attack copies a yard permanent (a leave event). The attack trigger survives a flip. |
| Hapatra, the Desert Fang | ★ | ETB −1/−1 counters equal to the yard's best MV. BB, and a bad flip (E2). |
| The Coming of Galactus | ★ | 5-MV saga: kill, drain 4, then a 16/16. BB. |
| Witherbloom, the Balancer | ★ | Affinity for creatures, and face-down 2/2s count. A cheap 5/5 flying deathtouch on a wide board. |
| Tom, Bert, and William | ◇ | Sacrifice outlet: a dud noncreature manifest becomes a 2-card loot. |
| Bonny Pall, Clearcutter | ◇ | Draw and a land from the yard on every attack. GUU at 6. F5 card. |
| Mimeoplasm, Revered One | ◇ | A big leave event (exiles X creature cards). |
| Berta, Wise Extrapolator | ◇ | Counters into mana. |
| Absorbing Man | ◇ | 4/4 vigilance for 3 that copies a land, artifact or enchantment. |
| Mind into Matter | ◇ | Draw X and put a permanent down. |
| Wardens of the Cycle | ◇ | Morbid draw. |
| Root Manipulation | ◇ | One-turn overrun. |
| Aatchik, Emerald Radian | ◇ | Insects per artifact or creature card in the yard. BB at 6. |
| Silvan Reveler · Tam, Observant Sequencer · Thranduil, Sindarin Liege | ◇ | F5 landfall cards. |
| Prime Speaker Zegana | ◇ | GGUU at 6, and its ETB draw is lost on a flip (E2). |
| Omega, Heartless Evolution | ◇ | Its ETB is lost on a flip (E2); 7 MV to cast. |
| Vicious Rivalry | ✗ | Kills your own face-down creatures (E3). |
| Tam, Mindful First-Year | △ | Hexproof from each of a creature's colours, and face-down creatures are colourless. |
| Kiora of Salt and Sand · Maralen · Thranduil, the Elvenking | △ | Planeswalker, Faerie and Elf shells. |
| Codie, Ravenous Codex | ✗ | Prepare plus WUBRG activation. |

## 5. Consolidated plan (live)

**Thesis:** Sultai dread midrange. Every dread is a body plus a binned card. The leave-the-
graveyard cluster (Kishla, Goldkeeper, Attuned Hunter, Teval, Muldrotha) converts the
binned cards into draws, Treasure and counters. Hollowmurk and Warden convert counters
into cards. Interaction comes from the Sultai removal suite. Measured on a scratch list
(`scratchpad/sultai-draft2.txt`):
- metrics floor **A**: interaction 9, card advantage 4 (+2 unclassified);
- avg MV 3.42, board power 77;
- keepable 84%.

**Distinct:** no deck shares more than 3 nonland cards with it (deck 21). The theme
neighbours (64, 62) share 1–2 cards.

**Proposed 60** (36 spells, 24 lands):
- **Dread core (8):** Shrieker ×2, Abhorrent Oculus, Growing Dread, Under the Skin,
  Break Down the Door, Valgavoth's Onslaught, Paranormal Analyst.
- **Leave + counters engine (9):** Kishla Skimmer, Kheru Goldkeeper, Attuned Hunter,
  Champion of Dusan, Hollowmurk Siege, Warden of the Grove, Cryptid Inspector, Glarb,
  Tarmogoyf.
- **Fixing (5):** Sultai Devotee ×4, Enduring Vitality.
- **Interaction (8):** Kin-Tree Severance, Lie in Wait, Fangkeeper's Familiar, Awaken the
  Honored Dead, Drag to the Roots, Kraven's Last Hunt, Witherbloom Charm, Professor
  Dellian Fel.
- **Card flow (1):** Rakshasa's Bargain.
- **Top end, all good dread hits (5):** Teval, Muldrotha, Quandrix, Sin, Koma.
- **Lands (24):**
  - Opulent Palace ×2, Overgrown Tomb ×3, Breeding Pool ×3, Watery Grave ×2;
  - Wastewood, Willowrush and Gloomlake Verge;
  - 6 Forest, 3 Island, 2 Swamp.

  This gives sources U 12 / B 11 / G 16. The three-pip 3-drops (Glarb, Lie in Wait,
  Awaken) cast on curve 73% of the time; Devotee and Vitality make that a floor.

**Bench, in order:** Moon-Vigil Adherents, Stalwart Successor, Witherbloom the Balancer,
Jenova, The Coming of Galactus, Hapatra, Omnivorous Flytrap, Oblivious Bookworm, Exdeath,
Lasyd Prowler, Deadly Brew, Weight Room.

**Protect list (what `cuts` cannot see):**
- Sultai Devotee is FIXING; it is tagged only removal (F8).
- Paranormal Analyst's value is the dread count.
- Koma and Quandrix are valued as Shrieker flips (F9).
- Kishla and Goldkeeper: their trigger sources are the whole yard-leave cluster.

**Rotation (a legality fact):** 27 of the 36 spell lines are DSK/TDM/BLB and leave Standard
around 2027. The deck has roughly one rotation of life.

**Tool holes seen (G-67, batch-fix later, not now):** Rakshasa's Bargain ("put two into
your hand") reads as no role, so card advantage is under-counted. The deck's real card
advantage (dread selection, Analyst, Kishla, Hollowmurk) is mostly invisible to the floor.

**REVISION 1 (owner, 2026-10-11): one Sultai Devotee instead of four.**
- Changes: −3 Devotee and −Cryptid Inspector; +Jenova, +The Coming of Galactus,
  +Stalwart Successor, +Exdeath.
- Manabase rebalanced toward black: Overgrown Tomb 3→4, Breeding Pool 3, Watery Grave 2,
  Forest 6→4, Island 3, Swamp 2→3. Sources are now U 12 / B 13 / G 15.
- On-curve changes, measured on the same 60 spells under the old and new manabase:
  - Galactus 64→73%;
  - Glarb, Lie in Wait and Awaken 73→76%;
  - Hollowmurk and Witherbloom Charm 77→80%;
  - Exdeath and Stalwart 82→85%;
  - Shrieker and Vitality 76→72% (one fewer G source).
- The Devotees were never counted in those figures, since dorks are not land drops (G-35).
  Their loss is real fixing the model does not price. Vitality is now the only creature
  fixing.
- Floor still A: interaction 10, card advantage 5, avg MV 3.58.
- Cryptid Inspector was the 4th cut; alternatives are Tarmogoyf and Rakshasa's Bargain.
- Exdeath (6 permanent cards in the yard) sits in the stay-full cluster against the
  leave engine (F3). Muldrotha and Oculus drain the same yard it counts.

**Variant signals:**
1. Lands-from-graveyard Simic/Sultai (F5, about 14 cards).
2. "Big lottery" top end. Too thin to build around; noted only.


## 6. Refinement round 1 (owner pushback on 16 cards + new search), 2026-10-11

**Upgraded after a full re-read:**
- *Seedship Broodtender* ★★ — a 2-drop that mills 3. Its reanimation is a REAL enter
  (ETB fires, unlike a flip), with 5 MV5+ targets, and it is a creature-card leave event.
- *Bonny Pall* ★★ — every attack draws and puts a land from the yard into play, which is
  a leave event. A flip loses only Beau.
- *Tam, Mindful First-Year* ★ — its tap makes a creature all colours, so the static gives
  it hexproof from all colours, at instant speed. Protection 1→2.
- *Absorbing Man* ★ — 4/4 vigilance for 3. Copying Opulent Palace makes a BGU mana source.
  It cannot usefully copy a Siege, because the mode is chosen as the card enters and a copy
  never enters.
- *Beifong's Bounty Hunters* ★ — the earthbend puts counters on a land creature, which is a
  Hollowmurk and Stalwart trigger.
- *Threats Around Every Corner* ★ — with Devotee ×1, its per-face-down basic fetch is the
  fixing that left with the other three.
- *Kotis* ★ spice — Kheru renew (2 counters plus flying) or Jenova counters make it connect.

**Held:**
- *Gardenize* ✗ — it adds only {G}, so it is not fixing.
- *Cosmogoyf* ◇ — about 0–3 power until Oculus's one-time 6.
- *Mind into Matter*, *Essence Anchor*, *Defiant Survivor* (only the one Vitality tap),
  *Zegana*, *Wardens*, *Lotuslight Dancers*, *Chief Warg's Company*: all ◇.

**New (pool regex: face-down / leave-your-graveyard / renew):**
- Etrata, Deadly Fugitive ★★★ (a noncreature manifest is exiled and cast free);
- Fang, Fearless l'Cie ★★;
- Insidious Roots ★★;
- Overgrown Zealot ★★;
- Vannifar ★;
- Soul Enervation ★;
- Defiled Crypt ★;
- Qarsi Revenant ★;
- Sage of the Fang ★;
- Agent of Kotis ★;
- Manifest Dread ★;
- Cryptic Coat ◇.

**ROTATION (a legality fact):** MKM and OTJ leave Standard in 2026. That covers Etrata,
Insidious Roots, Vannifar, Soul Enervation, Cryptic Coat and Bonny Pall.

**Measured package** (−Bargain +Etrata, −Sin +Bonny, −Champion +Broodtender,
−Witherbloom Charm +Tam): interaction 10→9, protection 1→2, avg MV 3.61→3.47.
