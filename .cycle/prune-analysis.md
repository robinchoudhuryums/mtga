# Roster prune analysis — Arena's 100-deck cap (TEMPORARY working doc)

**Status: REFRESHED 2026-09-06 against the live roster (118 files); awaiting the user's keep/cut calls.**
Delete once the prune decisions land. A scratchpad, not a
source of truth — decks/ are.

**Why:** MTG Arena caps the app at 100 decks; the repo roster is 118 files (families
counted per file, Brawl twins and the two Example templates included). The deliverable is a CROSS-REFERENCED shortlist:
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

## Refresh 2026-09-06 — what changed since 2026-08-19

- Roster 111 → **118 files**: new are **56b One Fell Swoop — Ball Lightning** (drafted from the
  56 pile), **76 Spirit Call**, **77 Bottomless**, **78 Team Avatar**; the three Brawl twins
  (3-brawl, 22-brawl, 40-brawl) and the two Example templates (0, 0a) now counted explicitly.
- 56, 56a and 56b were rebuilt/tuned 2026-09-05/06 — their overlaps below are post-tune.
- **41 of 118 files carry `#: arena:`** (known in the app) and **30 have a match on record**;
  everything else is roster-relative (G-73).
- A THIRD axis is added this pass: **unique cards** (cards in no other deck). A deck with 0–3
  unique cards is either a variant twin or a deck made of other decks' cards; the twin column
  says which. Roster median unique count is 7.

## Batch 1 — card-name overlap matrix (regenerated)

118 files; pairwise shared DISTINCT nonland, nonbasic names.

### Top CROSS-family pairs (shared ≥ 11)

| shared | % of smaller | pair |
|---|---|---|
| 21 | 57% | 15 Air Nomads × 16 Moon Spirit |
| 15 | 37% | 7 Earth's Mightiest × 63 Heirloom |
| 15 | 33% | **31 Pox × 75 Woodland Realm** (new) |
| 15 | 39% | 50a Hoofprint — Strata × 69a Warg and Woodland — Bear-Wolf |
| 14 | 31% | 8 Sacrifices × 21a Gastromancer — 4-Color |
| 14 | 33% | 26 Iron Forge × 48 Doombots |
| 14 | 33% | 26b Iron Forge — Ancient Decay × 48a Doombots — Motor Pool |
| 14 | 30% | 37a Wizardz — Wiz-Khalifa × 45a The Exiles — Grixis Mayhem |
| 13 | 26% | 28 Triceraton × 29 Enchantress |
| 13 | 30% | 30 Fractalandtastic × 40a Paradox Drive — ParadoXponential |
| 12 | 32% | 8 Sacrifices × 11 Villainous |
| 12 | 30% | 12 Drawn Conclusions × 32 Mimicry |
| 12 | 29% | 24 Eternal Flame × 45 The Exiles |
| 12 | 30% | 26a Iron Forge — Virulent × 48 Doombots |
| 12 | 26% | 28a Triceraton — Owned × 29a Enchantress — Competitive |
| 12 | 25% | 29 / 29a Enchantress × 30 Fractalandtastic |
| 12 | 30% | 41 Darkforce Inversion × 42 Blood Price |
| 12 | 31% | 45 The Exiles × 55b Mardu Airbender |
| 11 | 29% | 5 Coming of Galactus × 6 Dead or Alive |
| 11 | 30% | 10 Mad Villainy × 11 Villainous |
| 11 | 28% | 12 Drawn Conclusions × 22 Bloodbending |
| 11 | 27% | 19b Bird Brain — GW Chocobo × 50a Hoofprint — Strata |
| 11 | 24% | 25 Spellstorm × 54b Grand Lotus — Comet |
| 11 | 23% | 28 Triceraton × 29a; 30 × 54a; 37 / 37b Wizardz × 45a |
| 11 | 25% | 62 Rot and Bloom × 64 Gray Goo |

### Family pairs (share by design — the Arena-cap arithmetic)

22×22-brawl 41 (95%) · 40×40-brawl 40 (100%) · 37×37b 39 (81%) · 36×36a 36 (90%) ·
19×19b 33 (72%) · 37×37a 32 (68%) · 37a×37b 32 (68%) · 29×29a 31 (66%) · 28×28a 30 (64%) ·
38×38a 30 (79%) · 44×44a 30 (68%) · 68×68a 28 (62%) · 24×24b 27 (64%) · 3×3-brawl 26 (72%) ·
21×21a 24 (55%) · 35×35a 24 (53%) · 20a×20b 23 (55%) · 68a×68b 22 (48%) · 73×73a 22 (49%) ·
54a×54b 20 (43%) · 54×54a 18 (38%) · 74×74a 18 (43%). **56×56a 11 · 56×56b 11 · 56a×56b 9** —
the One Fell Swoop family is the least card-overlapping 3-file family in the roster after its
rebuild (each file is a majority of cards nothing else in the family runs).

## Playstyle sweep — `deck.py similar`, all 118 files (regenerated)

Read per G-47: the % is a TAG read; grade the ✦ SPECIFIC themes and the shared-CARDS count.

### High on BOTH axes, cross-family (theme ≥ 75% AND ≥ 8 shared cards)

| pair | theme | shared | tiers | Pld | ✦ specific |
|---|---|---|---|---|---|
| 15 Air Nomads × 16 Moon Spirit | 89% | 19–21 | B × A | 3 / 1 | Ally, bending, airbend |
| 7 Earth's Mightiest × 63 Heirloom | 92% | 12–15 | B × B | 3 / 1 | counters, Human |
| **15 Air Nomads × 78 Team Avatar** (new) | 82% | 8–9 | B × B | 3 / **7** | Ally, Human |
| 38 Armory × 39 Starforge | 91% | 10 | B × A | · | Equipment, etb, equip |
| 38a Armory — Cloud × 39 Starforge | 98% | 9 | B × A | · | Equipment, pump, equip |
| 50a Hoofprint — Strata × 69a Warg — Bear-Wolf | 80% | 12–15 | B × B | 1 / 1 | counters (ramp, sacrifice) |
| 26b Iron Forge — Ancient Decay × 48a Doombots — Motor Pool | 79% | 10–14 | B × B | · | tokens, card draw, burn |
| 26a Iron Forge — Virulent × 48 Doombots | 78% | 9–12 | · × B | · | Robot |
| 40a Paradox Drive — ParadoXponential × 30 Fractalandtastic | 84% | 8–13 | A × A | 4 / · | counters |
| **64 Gray Goo × 77 Bottomless** (new) | 88% | 9–10 | B × **C** | · | graveyard, mill |

### Theme-only clusters (≥ 85%, < 8 shared — the belts; NOT prune candidates on this evidence)

Reanimator/graveyard 5 · 6 · 52a · 62 · 64 · 77 (6×52a 97%+5, 5×62 95%+4, 51a×77 92%+2) ·
Counters 4 · 7 · 9 · 30 · 63 · 69 (4×63 93%+3, 30×63 94%+3, 9×30 88%+3) · Aristocrats/lifegain
21 · 21a · 42a · 1 · 58 · 9 (21×42a 89%+3, 1×58 85%+1) · Spellslinger 25 · 37a · 55a (89%+3,
87%+3) · Evasion-aggro 35 · 35a · 59 (89–90% + **0** shared — pure tag) · Treasure 48a × 58
87%+4 · Card draw 12 × 43 85%+2 · 24b × 55 86%+4.

### Distinct decks (top match < 66% or 0 shared with it — the safe list)

61 Pony Express (51%) · 70 Empty Threats (56%) · 75 Woodland Realm (57% — but 15 shared
cards with 31 Pox on the CARD axis, see below) · 18 Atlantis Attacks (61%) · 65 Web of Life
(64%) · 72 Goblin Kamikaze (65%, 0) · 69b Warg — Crooked Way (68%, 0) · 53 Sibsig Choir (73%,
0) · 54a Grand Lotus — Encore (84%, 0) · 68b Frog Sage — Warren (82%, 0) · 35 / 35a / 59
(89–90%, 0 shared — a tag match, not a deck match).

## Uniqueness — the third axis (new this pass)

Cards in NO other deck, basics excluded. ≤ 3 unique, with the deck each shares most with:

| deck | unique | twin (shared) | tier | Pld | in Arena |
|---|---|---|---|---|---|
| 22 Bloodbending | 0 | 22-brawl (41) | B | 1 | Y |
| 22-brawl | 0 | 22 (41) | · | · | · |
| 40 Paradox Drive | 0 | 40-brawl (40) | A | · | · |
| 40-brawl | 0 | 40 (40) | · | · | · |
| 37 Wizardz | 0 | 37b (39) | B | · | · |
| 3-brawl Knight's Edge — Brawl | 0 | 3 (26) | · | · | · |
| 0 / 0a Example Avatar WU | 0 | each other (7) | · | · | · |
| 19b Bird Brain — GW Chocobo | 1 | 19 (33) | A | · | · |
| 3 Knight's Edge | 1 | 3-brawl (26) | A | · | · |
| 35a Hack n Slash — Ninja Avatar | 1 | 35 (24) | B | 3 | Y |
| 36 Panthera | 2 | 36a (36) | B | · | Y |
| 36a Panthera — Competitive | 2 | 36 (36) | A | · | · |
| 38a Armory — Cloud Value-Combo | 2 | 38 (30) | B | · | · |
| 68a Frog Sage — Seer | 2 | 68 (28) | B | 4 | Y |
| 21a Gastromancer — 4-Color | 2 | 21 (24) | B | · | · |
| 7 Earth's Mightiest | 2 | 63 (15) | B | 3 | Y |
| 29 Enchantress | 3 | 29a (31) | A | · | · |
| 74a Iron Hills Forge — Smaug's Vault | 3 | 74 (18) | B | 4 | Y |
| 63 Heirloom | 3 | 7 (15) | B | 1 | Y |
| 10 Mad Villainy | 3 | 11 (11) | A | · | · |
| 56a / 56b One Fell Swoop variants | 3 | 56 (11) | B | 1 / · | Y / · |
| 9 Hulk Smash | 3 | 29 (8) | A | · | · |

Read it as four kinds: templates (0, 0a), format twins (3-brawl, 22-brawl, 40-brawl),
parent/variant pairs where BOTH score low (37/37b, 36/36a, 19/19b, 38/38a, 68/68a, 21/21a,
29/29a, 35/35a), and the one standalone deck made of other decks' cards (**7 Earth's
Mightiest**, twin 63 at only 15). 56a/56b score 3 because the family shares its eight-card
core, not because either duplicates 56 (11 shared of ~35).

## Cross-referenced shortlist (refreshed)

118 files vs a 100-deck cap → **18 slots to find IF everything is in Arena**; 41 files are
known-in-Arena, so the real gap is unknown and the user maps this onto the app.

**Tier 1 — high on both axes, cross-family (the real merge candidates):**

| pair | read | suggested cut |
|---|---|---|
| 15 Air Nomads × 16 Moon Spirit | 89% / 21 shared / same colours — still the clearest merge in the roster. 16 holds A. | **15** — unless its 3 matches say otherwise |
| 15 Air Nomads × 78 Team Avatar | new: 78 is the roster's most-played deck (7) and shares the ✦Ally core. 15 is now squeezed from two sides. | reinforces cutting **15** |
| 7 Earth's Mightiest × 63 Heirloom | 92% / 15 shared / both B; 7 has 2 unique cards, 63 has 3. Two counters-goodstuff decks. | **63** (thinner theme count) or merge into one |
| 38 Armory × 39 Starforge (+ 38a) | 98% is the highest theme number in the roster; one equipment identity across three files plus 74's tribal take. 39 holds A. | **38a** first (2 unique), then decide 38 vs 39 |
| 50a Hoofprint — Strata × 69a Warg — Bear-Wolf | 80% / 15 shared / same colours. Each is someone's variant; the parents differ more than the variants do. | one of the two variants |
| 26/26a/26b Iron Forge × 48/48a Doombots | Robot tribal and Treasure-artifact, each twice. 26a is ungraded with 8 to craft. | **26a**, then 26b vs 48a |
| 64 Gray Goo × 77 Bottomless | new: 88% / 10 shared; 77 is the roster's one **C**. | **77** |
| 40a × 30 | both A, 4 matches on 40a — real overlap, both earn their slot. | none (listed so it is not re-litigated) |
| 31 Pox × 75 Woodland Realm | 15 shared on cards but theme match only 57% — read as shared staples between two distinct plans. | none |

**Tier 2 — theme-only or cards-only (examined, fine):** the reanimator, counters, aristocrats,
spellslinger and treasure belts above; 8×21a / 28×29 / 24×45 / 12×32 (staples); 35/35a/59
(tag match, 0 shared cards).

**Tier 3 — family / format arithmetic (biggest savings, pure preference):**
- **Brawl twins: 22-brawl (41 shared, 95%), 40-brawl (40, 100%), 3-brawl (26)** — 3 slots if
  the Brawl queue is idle. None has a match on record.
- **Templates: 0, 0a** — 2 slots if they are in Arena at all.
- **Variant pairs where one file has ≤ 3 unique cards:** 37 vs 37b (39 shared — the PARENT is
  the redundant one), 36 vs 36a (36 — parent again; 36a holds A), 19b (33), 29 vs 29a (31),
  38a (30), 44a (30), 28a (30), 68a (28 — but 68a has 4 matches), 24b (27), 21a (24), 35a (24
  — 3 matches, in Arena), 20a/20b (23), 68b (22), 73a (22), 74a (18 — 4 matches). Each pair
  where only one is played is a free slot; **Pld and `#: arena:` say which one is played.**

**Combined signal, ranked (unique ≤ 3, twin ≥ 20 shared, no matches, not known-in-Arena):**
0 · 0a · 3-brawl · 22-brawl · 40-brawl · 37 · 19b · 36 (in Arena, no matches) · 38a · 21a · 29
· 36a. That is **12 slots** with no recorded play behind any of them; the eighteen-slot gap
closes with Tier 1's 15, 63, 77, 26a and two of the variant pairs above.

**Suggested reading order (unchanged):** Tier 3 first (a variant or twin you never play costs
a slot and adds nothing), Tier 1 second (two decks that are one deck — 15×16 first), Tier 2
listed so the raw numbers are not re-litigated.
