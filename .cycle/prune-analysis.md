# Roster prune analysis — Arena's 100-deck cap (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the prune decisions land. A scratchpad, not a
source of truth — decks/ are.

**Why:** MTG Arena caps the app at 100 decks; the repo roster is ~113 lists (families
counted per file, Brawl included). The deliverable is a CROSS-REFERENCED shortlist:
pairs/families that overlap on BOTH card names and playstyle are prune candidates;
pruning means REMOVING FROM ARENA — the repo file can stay (a repo deck costs nothing
against the cap, and `#: arena:` headers mark which decks are known-in-Arena).

## The plan

1. **Batch 1 (mechanical, whole roster in one pass): the CARD-overlap matrix.**
   Pairwise shared nonland, nonbasic card names across every deck file. Family pairs
   (same directory — parent/variant, sharing by design) reported separately from
   CROSS-family pairs, which are the surprising ones.
2. **Batches 2+ (playstyle): `deck.py similar` per deck** — the theme-overlap tool
   built for exactly this question (G-47), ~15 decks per batch, recording each deck's
   top ⚠-overlap neighbours + the ✦ specific-theme collisions + shared-card counts.
   Committed per batch so the analysis survives context loss.
3. **Final: cross-reference.** High on BOTH axes → prune candidate. High cards only →
   shared staples (fine — copies are fungible). High theme only → different builds of
   one idea (usually the variant convention working as intended). The shortlist
   carries tier letters and `Pld` (matches played, report-only per G-57) so the
   keep/cut call has the context it needs.

**Caveats recorded up front:** `similar`'s number is a TAG read — G-47 says grade the
✦ SPECIFIC overlaps and the shared-CARD line, not the percentage; theme similarity and
card overlap are different questions and SOME overlap is fine. The map of what is
actually IN Arena is incomplete (G-73: only reconciled decks carry `#: arena:`), so
the final list is roster-relative and the user maps it onto the app.

## Batch 1 — card-name overlap matrix

111 deck files parsed; pairwise shared DISTINCT nonland, nonbasic names.

### Top CROSS-family pairs (the surprising axis)

| shared | % of smaller | pair |
|---|---|---|
| 21 | 57% | 15 Air Nomads × 16 Water Spirit |
| 15 | 37% | 07 Earth's Mightiest × 63 Heirloom |
| 15 | 36% | 26 Iron Forge × 48 Doombots |
| 14 | 32% | 08 Sacrifices × 21a Gastromancer 4C |
| 13 | 26% | 28 Triceraton × 29 Enchantress |
| 12 | 35% | 56a Executioner's Song × 59 Stampede |
| 12 | 32% | 50a Hoofprint Strata × 69a Warg Beorn |
| 12 | 32% | 08 Sacrifices × 11 Villainous |
| 12 | 31% | 45 The Exiles × 55b Mardu Airbender |
| 12 | 30% | 41 Darkforce Inversion × 42 Blood Price |
| 12 | 30% | 30 Fractalandtastic × 40a Exponential Drive |
| 12 | 30% | 12 Drawn Conclusions × 32 Mimicry |
| 12 | 29% | 26b Ancient Decay × 48a Motor Pool |
| 12 | 29% | 24 Eternal Flame × 45 The Exiles |
| ~12 | ~26% | 29/29a Enchantress × 30 Fractalandtastic; 28a × 29a |
| 11 | 30% | 10 Mad Villainy × 11 Villainous |
| 11 | 29% | 05 Coming of Galactus × 06 Dead or Alive |
| 11 | 28% | 12 Drawn Conclusions × 22 Bloodbending |
| 11 | 25% | 62 Rot and Bloom × 64 Gray Goo |
| 11 | 25% | 25 Spellstorm × 54b Grand Lotus Comet |
| 11 | 24% | 37a Wizardz Storm × 45a Grixis Mayhem |
| 10 | 29% | 44 Grand Larceny × 70 Empty Threats |
| 10 | 28% | 03 Knight's Edge × 23 Avengers |
| 10 | 26% | 38 Armory × 39 Starforge |
| 10 | 25% | 19b GW Chocobo × 36/36a Panthera |

### Family pairs (variants — share by design; the Arena-cap arithmetic)

37×37b 39 shared (85%) · 36×36a 36 (90%) · 37×37a 35 (78%) · 29×29a 31 (66%) ·
38×38a 30 (79%) · 19×19b 30 (75%) · 44×44a 30 (68%) · 28×28a 30 (64%) ·
68×68a 29 (64%) · 24×24b 27 (64%) · 03×3-brawl 26 (72%) · 68a×68b 24 (59%) ·
21×21a 24 (55%) · 35×35a 24 (53%).

**Early observations:** (1) The single biggest cross-family collision is
15 Air Nomads × 16 Water Spirit — 57% of the smaller list is identical. (2) The
families are where the cap arithmetic lives: 3-deck families (19, 26, 28?, 35?, 37,
54, 55, 60?, 68, 69, 73, 74…) each cost 3 Arena slots. (3) Clusters visible even
before the theme pass: the Sacrifices/Villainous/Gastromancer aristocrats belt
(08/10/11/21a), the copy/fractal belt (12/22/32, 29/30/40a), the artifact belt
(26/48 both flavors), the exile belt (24/45/44a/55b).


## Playstyle batches — `deck.py similar` sweep, all 111 decks

Read per G-47: the % is a TAG read; the ✦ SPECIFIC themes and the shared-CARDS count
are what to grade from. Numbers below are "theme% + shared nonland cards".

### The belts (theme clusters, cross-family)

- **Reanimator/graveyard** — 5, 6, 52, 52a, 62, 64, with 54a/45a/51/51a on the mill
  edge. Tightest: 62×52a 97%+10 · 6×52a 96% · 5×52a 94% · 6×62 95%+7 · 5×62 93%+5 ·
  5×64 89%+7 · 51a×64 85% · 54a×6 88%+0. Six decks share ✦graveyard/✦reanimator as
  their SPECIFIC theme; card overlap stays moderate (5–10) because colors differ.
- **Counters** — 4, 7, 9, 29/29a, 30, 63, 69. Tightest: 30×63 94% · 4×63 93% ·
  **7×63 92%+12** (the one pair high on BOTH axes) · 4×30 91%+4 · 9×30 89% · 69×4 85%.
- **Aristocrats/sacrifice** — 1, 8, 10, 11, 21/21a, 42a, 55, 58. Tightest: 21×42a
  90%+3 · 21a×42a 90%+1 · 1×58 86%+1 · 8×58 84%+3 · 11×52a 84%+6 (bridges into the
  graveyard belt) · 10×55 79%. Card overlap is LOW throughout — same idea, different
  colors/cards. Theme-only cluster.
- **Treasure** — 26b, 48a, 58, 74a, plus 1/49 on the edge. Tightest: 48a×58 91%+4 ·
  74a×58 87%+3 · 26b×48a 85%+8 · 74a×48a 86%+7 · 49×74a 66%+7. Identity arguments
  already written into 74a's header (58 = sacrifice, 48a = Izzet cheat, 74a = Dwarf
  hoard); the belt is real but each deck's payoff half is disjoint.
- **Equipment** — 38, 38a, 39, 74. **38×39 98%+10 and 38a×39 98%+9 — the highest
  cross-family theme number in the roster.** 74 sits at 74%+2–4 (the tribal-trigger
  identity holds on the card axis).
- **Bending** — 14, 15, 16, 22, 54b. **15×16 89%+19 — the top BOTH-axes pair in the
  roster** (✦Ally ✦bending ✦airbend, 100% colours). 16×22 73%+4 · 14×54b 73%+6.
- **Exile-cast** — 45, 55b, 67: 45×55b 81%+6 · 55b×67 82%+5 · 45×67 78%+8.
- **Spellslinger/burn** — 2, 25, 37-family, 55a, 71: 25×55a 85%+3 · 2×10 75%+7 ·
  25×37a 75%+5.
- **Robot/artifact** — 26, 26a, 47, 48: 26×48 71%+10 · 26a×48 74%+8 · 47×26 71%+3.
- **Landfall/ramp** — 30, 40a, 50a, 69a: **50a×69a 81%+12 (100% colours)** ·
  40a×50a 82%+5.
- **Card-draw engines** — 12, 32, 41, 43: 12×32 66%+9 · 32×43 79%+4 · 43×41 79%+5.
- **Lifegain** — 20/20a/20b, 31, 42/42a, 46: 20b×46 83%+2 · 46×20a 80%+4 · 42×20a 68%+4.
- **Pump/aggro** — 24b, 33, 35, 56/56a, 57, 59: 57×33 75%+1 · 56×24b 75%+2 · 59×56a
  (12 shared per card matrix).

### Distinct decks (low overlap on both axes — the safe list)

70 Empty Threats (top match 48%) · 60/60a Redline (✦speed, nothing else within 50%) ·
44/44a Grand Larceny (✦heist; best external 51%) · 61 Pony Express (66%, 1 shared) ·
34 Zoologist (63%) · 53 Sibsig Choir (75% but 0 shared) · 65 Web of Life (65%) ·
17 Spectrum (62%) · 18 Atlantis Attacks (62%) · 72 Goblin-town (66%, 0 shared) ·
73/73a Duke's Vigil (78%/76% generic-tag matches, 0 shared cards) · 66 Lethal
Protector (69%) · 14 Dragon King Roku (73%).

### Format twins & family arithmetic (the cap math)

- Brawl twins: **40×40-brawl 100%+34 · 22×22-brawl 99%+34 · 3×3-brawl (26 shared)** —
  same list re-shaped; prunable only if the Brawl queue isn't being played.
- Tightest family pairs: 44×44a 99%+30 · 38×38a 99%+26 · 37×37b 99%+29 · 36×36a
  98%+31 · 19×19b 98%+25 · 21×21a 97%+20 · 28×28a 95%+19 · 37×37a 94%+25 · 60×60a
  94%+9 · 68×68a 92%+25 (68b +18/+11) · 52×52a 81%+13 · 29×29a 79%+21 · 35×35a
  73%+20 · 73×73a 70%+13 · 24×24b 65%+20 · 74×74a (14 shared).
- 3-file families (3 Arena slots each): 19, 20, 26, 28?, 35?, 37, 54, 55, 60?, 68,
  69, 73?, 74? — 68 and 69 are the only THREE-variant families where all three sit in
  one belt (Frog counters / Warg graveyard-ramp).

## Cross-referenced shortlist (final)

High on BOTH axes = prune candidate; tier letters + Pld attached (Pld report-only).
111 repo decks vs a 100-deck Arena cap → ~11 slots to find IF everything is in Arena
(the `#: arena:` map is incomplete — user maps this list onto the app).

**Tier 1 — high both axes, cross-family (the real candidates):**

| pair | theme | shared | tiers | Pld | read |
|---|---|---|---|---|---|
| 15 Air Nomads × 16 Water Spirit | 89% | 19–21 (57%) | B × A | 15:2 | Clearest merge in the roster: same ✦Ally/✦bending core, 100% colours. 16 is the stronger letter. |
| 07 Earth's Mightiest × 63 Heirloom | 92% | 12–15 (37%) | B × B | 7:3 | Both counters-goodstuff; 63's theme count is 5 (thinnest in roster) — 63 is the weaker identity. |
| 38 Armory × 39 Starforge | 98% | 9–10 (26%) | B × A | · | Highest cross-family theme %. 38's own variant 38a also reads 98% vs 39. One equipment-voltron identity spread over three files + 74's tribal take. |
| 50a Hoofprint-Strata × 69a Warg-Beorn | 81% | 12 (32%) | B × B | · | Same landfall/counters engine, 100% colours. Each is someone's variant — the parents (50, 69) differ more than the variants do. |
| 26/26a Iron Forge × 48 Doombots | 71–74% | 8–15 (36%) | A/· × B | · | Robot tribal twice; 26a (ungraded, 8 to craft) is the redundant file. |
| 26b Ancient Decay × 48a Motor Pool | 85% | 8–12 (29%) | B × B | · | Treasure-artifact twice, as each family's variant. |
| 12 Drawn Conclusions × 32 Mimicry | 66% | 9–12 (30%) | A × A | · | Both A — overlap is real (9 shared, 100% colours) but both earn their slot; lowest-priority in this tier. |
| 45 The Exiles × 55b Mardu Airbender | 81% | 6–12 (31%) | B × B | 45:4 | Exile-cast twice; 45 is the played one. 67 Warpwright borders both (78–82%). |

**Tier 2 — theme-only or cards-only (NOT prune candidates on this evidence):**
aristocrats belt (8/10/11/21a — high theme, low shared cards: different builds of one
macro-idea); reanimator belt (5/6/52a/62/64 — 97% numbers but distinct colors/payoffs);
08×21a 14 shared but theme outside top-3 (shared staples); 28×29 13 shared (staples);
24×45 12 shared (staples).

**Tier 3 — the family/Brawl arithmetic (biggest slot savings, pure preference):**
- Brawl twins 3/22/40 — 3 slots if the Brawl queue is idle.
- Near-duplicate variants (98%+ / 25+ shared): 37b (vs 37: 99%+29), 36a (98%+31),
  19b (98%+25), 44a (99%+30), 38a (99%+26), 28a (95%+19), 21a (97%+20), 68's third
  file 68b. Each variant pair where the user only ever plays one is a free slot.

**Suggested reading order for the user:** Tier 3 is where the easy slots are (a
variant you never play costs a slot and adds nothing); Tier 1 is where two decks are
genuinely the same deck in different files (15×16 first); Tier 2 is listed so the
raw numbers don't get re-litigated later — those overlaps were examined and are fine.
