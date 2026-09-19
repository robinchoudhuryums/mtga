# Roster prune analysis — Arena's 100-deck cap (TEMPORARY working doc)

**Status: REGENERATED 2026-09-18 against the live roster (114 files).** Supersedes the
2026-09-06 pass wholesale — every row of that table had moved (see §5). Delete once the
prune decisions land. A scratchpad, not a source of truth — decks/ are.

> **⚠ PARTLY STALE, 2026-09-19 — re-run before acting on any row involving deck 15 or 16.**
> Deck 16 was rebuilt and tuned by eleven cards the day after this was generated (the
> waterbend split from 15 Air Nomads, then nine swaps and a land). Its overlap figures here
> predate all of it. The 15 × 16 pair is the one this actually decides: the split was made
> precisely to separate them, and the shared-card count was expected to fall from 19 to
> around 12, with a further drop to ~6 available if deck 15 also sheds its six waterbend
> cards — a call deliberately left until deck 15 has been played in its current form
> (3-0 at n=3). Every other row is as generated.

**Why:** MTG Arena caps the app at 100 decks. Pruning means REMOVING FROM ARENA — the repo
file can stay, since a repo deck costs nothing against the cap.

---

## 1. THE HEADLINE: there is probably no cap pressure, and that inverts the old premise

| | |
|---|---|
| repo files | **114** |
| carry an `#: arena:` header (known to be IN Arena) | **48** |
| no header — not in Arena, or in Arena and never reconciled | **66** |

The 2026-09-06 pass opened "118 files vs a 100-deck cap → 18 slots to find". **That is the
wrong denominator.** The cap counts decks in the CLIENT, and the repo can only prove 48 of
them. If 48 is close to right there are ~52 free slots and nothing needs pruning at all.

**RECONCILIATION POINT — only the user can settle this.** Count the decks in the Arena
client, or paste a `Player.log` through `parse_matches.py --apply`, which harvests deck
summaries and writes the `#: arena:` headers it learns (`/log-matches` Stage 1). Every
number below is conditional on the answer.

**And the Arena filter is the load-bearing one.** A prune only frees a slot if BOTH halves
of the pair are in Arena. Of the ten dual-overlap pairs in §3, six qualify; of the ten
biggest FAMILY twins in §4, **zero** do.

## 2. Method

Two independent axes, both computed from the live files; a prune candidate needs BOTH.

- **CARD axis** — pairwise shared DISTINCT nonland, nonbasic card names. Percentages are
  of the smaller deck's spell count.
- **THEME axis** — `deck._theme_cosine` over central-theme weight vectors, the same model
  `deck.py similar` prints (G-47).

Family pairs (same directory: parent/variant, sharing by design) are reported separately
from CROSS-family pairs, which are the surprising ones. 6,441 pairs scored.

**Read the two axes as different questions (G-47).** A high cosine with few shared cards is
a TAG match, not a deck match — two decks can share every tag and be opposite decks.

## 3. Cross-family pairs that overlap on BOTH axes

Threshold: theme cosine ≥ 80% AND ≥ 8 shared spells. Ten pairs clear it out of 2,009.

| shared | % | cosine | pair | both in Arena? | already argued? |
|---|---|---|---|---|---|
| **19** | 54% | **90%** | **15 Air Nomads × 16 Moon Spirit** | **YES** | **NEITHER** |
| 12 | 34% | 93% | 63 Heirloom × 7 Earth's Mightiest | YES | 63 → 7 only |
| 10 | 29% | 90% | 43 Uatu The Watcher × 79 Second Draw | YES | 79 → 43 only |
| 10 | 29% | 88% | 29 Enchantress × 30 Fractalandtastic | no | both ways |
| 9 | 26% | 96% | 38 Armory × 39 Starforge | no | 39 → 38 only |
| 9 | 25% | 87% | 26 Iron Forge × 48 Doombots | YES | 48 → 26 only |
| 9 | 26% | 86% | 47 Grid Overload × 48 Doombots | YES | 48 → 47 only |
| 9 | 25% | 83% | 26a Iron Forge — Virulent × 48 Doombots | no | NEITHER |
| 8 | 23% | 85% | 26 Iron Forge × 47 Grid Overload | YES | 47 → 26 only |
| 8 | 24% | 84% | 30 Fractalandtastic × 40a Paradox Drive — ParadoX | no | 40a → 30 only |

## 4. The one real candidate: 15 Air Nomads × 16 Moon Spirit

It is the only pair that is top of BOTH axes, in Arena on both sides, and argued by
neither file. 19 of ~35 spells shared, and the shared set is the whole Team Avatar core:

> Aang's Iceberg · Aang, Swift Savior · Aang, the Last Airbender · Airbender Ascension ·
> Airbender's Reversal · Airbending Lesson · Appa, Steadfast Guardian · Avatar's Wrath ·
> Compassionate Healer · Crashing Wave · Earth Kingdom Jailer · Gather the White Lotus ·
> Hakoda, Selfless Commander · Katara, Water Tribe's Hope · Path to Redemption · Sokka,
> Lateral Strategist · The Legend of Yangchen · Ty Lee, Chi Blocker · Water Tribe Rallier

Both are WU. What separates them is one sub-theme each — 15 keeps the FLIERS (Momo ×2,
Glider Kids, Glider Staff, Teo, Suki, Air Nomad Legacy, Appa Loyal Sky Bison, Wan Shi
Tong); 16 keeps the WATER TRIBE (Yue, Waterbender Ascension, Waterbending Lesson, South
Pole Voyager, North Pole Patrol, Giant Koi, Flexible Waterbender, East Wind Avatar).

**The tell is in deck 15's own archetype line**, which reads "Air Nomads fliers / airbend
+ **waterbend** tempo" — it already claims the axis deck 16 exists for.

Three ways to resolve it, in ascending cost. **All three are the user's call.**

1. **Keep both, argue the split.** Write the distinctness paragraph into both files and
   push the sub-themes apart — cut 15's waterbend claim, cut 16's remaining airbend cards.
   Costs no Arena slot and makes the pair defensible.
2. **Merge into a parent + variant** (`15` + `15a`), which is what the roster does
   everywhere else for two takes on one shell. Frees one Arena slot.
3. **Cut one from Arena.** Frees one slot outright. Only worth doing if the cap binds.

**26a × 48 is the other mutually-silent pair and is NOT a candidate**: 9 shared against 27
and 27 cards unique to each, and 26a is not in Arena. The 83% cosine is a tag match on
UR-artifacts, exactly the shape §2 warns about.

## 5. What changed since 2026-09-06 — the roster is de-duplicating itself

Every row of the old table was re-measured. **23 of 23 moved DOWN; none was unchanged and
none rose.** Mean drop 4.5 shared cards.

| pair | 2026-09-06 | live | | pair | 2026-09-06 | live |
|---|---|---|---|---|---|---|
| 28 × 29 | 13 | **0** | | 41 × 42 | 12 | 6 |
| 28a × 29a | 12 | **1** | | 8 × 21a | 14 | 8 |
| 62 × 64 | 11 | 4 | | 26 × 48 | 14 | 9 |
| 19b × 50a | 11 | 6 | | 15 × 16 | 21 | **19** |

That is tuning working: the decks have been pulled apart by ordinary swaps, not by a prune.
It is also why a single-row patch was refused — the table was stale roster-wide, and fixing
one row would have made the rest look current.

## 6. Family twins — the cheapest slots, and they are all free already

| pair | shared | % | both in Arena? |
|---|---|---|---|
| 40 × 40-brawl | 34 | 100% | no |
| 22 × 22-brawl | 33 | 94% | no (22 only) |
| 36 × 36a | 31 | 89% | no (36 only) |
| 44 × 44a | 30 | 83% | no |
| 19 × 19b | 26 | 74% | no (19 only) |
| 3 × 3-brawl | 25 | 71% | no |

**Not one of the ten biggest family twins has both halves in Arena**, so the Brawl-twin and
variant slots the old pass pointed at cannot free anything. 28 families hold 63 of the 114
files; the other 51 are standalone.

## 7. Decisions for the user

1. **How many decks are actually in your Arena client?** Everything here is conditional on
   it. If the answer is near 48, close this doc — there is nothing to prune.
2. **15 × 16** — keep both and argue the split, merge to parent+variant, or cut one.
3. Six more pairs share both axes but are each argued by at least one file already (§3).
   None needs action unless the cap binds; if it does, they are the next place to look.
