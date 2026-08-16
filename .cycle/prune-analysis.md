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


## Playstyle batches

(pending)

## Cross-referenced shortlist (final)

(pending)
