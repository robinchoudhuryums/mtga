# Roster prune analysis — Arena's 100-deck cap (TEMPORARY working doc)

**Status: REGENERATED 2026-09-21 against the live roster (114 files).** Supersedes the
2026-09-18 pass wholesale — see §5 for every row re-measured. Delete once the prune
decisions land. A scratchpad, not a source of truth — decks/ are.

> **The 2026-09-19 staleness warning on the previous version is now DISCHARGED.** It said
> to re-run before acting on any row involving deck 15 or 16, because deck 16 had been
> rebuilt the day after generation. That re-run is this document, and the pair moved
> exactly as predicted: **19 shared → 11**, against a forecast of "around 12".

**Why:** MTG Arena caps the app at 100 decks. Pruning means REMOVING FROM ARENA — the repo
file can stay, since a repo deck costs nothing against the cap.

---

## 1. THE HEADLINE: there is still probably no cap pressure

| | 2026-09-18 | live |
|---|---|---|
| repo files | 114 | **114** |
| carry an `#: arena:` header (known to be IN Arena) | 48 | **48** |
| no header — not in Arena, or in Arena and never reconciled | 66 | **66** |

Unchanged. The cap counts decks in the CLIENT, and the repo can only prove 48 of them. If
48 is close to right there are ~52 free slots and nothing needs pruning at all.

**RECONCILIATION POINT — only the user can settle this.** Count the decks in the Arena
client, or paste a `Player.log` through `parse_matches.py --apply`, which harvests deck
summaries and writes the `#: arena:` headers it learns (`/log-matches` Stage 1). Every
number below is conditional on the answer.

**And the Arena filter is the load-bearing one.** A prune only frees a slot if BOTH halves
of the pair are in Arena. Of the six dual-overlap pairs in §3, four qualify; of the eight
biggest FAMILY twins in §6, **zero** do — unchanged from the last two passes.

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

**NEW THIS PASS — the two axes do not age the same way, and §5 is the evidence.** Of the
four pairs that dropped out of §3, **all four kept their card count exactly and fell only
on the theme axis**, by 15 to 30 points. The mechanism is in CLAUDE.md: `_central_themes`
uses a RELATIVE cutoff (`max(2, 0.25 × max weight)`), so changing one card can drop an
unrelated theme out of a deck's central set and swing the cosine hard. Every one of the
four had a side edited on or after 2026-09-18, so this is real tuning rather than model
drift — but the lesson stands: **the CARD axis is stable and the THEME axis is volatile.**
Treat a cosine as a snapshot, and when the two disagree, trust the shared-card count.

## 3. Cross-family pairs that overlap on BOTH axes

Threshold: theme cosine ≥ 80% AND ≥ 8 shared spells. **Six pairs clear it out of 6,399,
down from ten.**

| shared | % | cosine | pair | both in Arena? | already argued? |
|---|---|---|---|---|---|
| **11** | 31% | 80% | **15 Air Nomads × 16 Moon Spirit** | **YES** | see §4 |
| 9 | 26% | 96% | 38 Armory × 39 Starforge | no | 39 → 38 only |
| 9 | 26% | **90%** | 47 Grid Overload × 48 Doombots | **YES** | 48 → 47 only |
| 9 | 25% | 87% | 26 Iron Forge × 48 Doombots | **YES** | 48 → 26 only |
| 9 | 25% | 82% | 26a Iron Forge — Virulent × 48 Doombots | no | NEITHER |
| 8 | 23% | 85% | 26 Iron Forge × 47 Grid Overload | **YES** | 47 → 26 only |

**The artifact knot is now the story.** Five of the six rows are the same three decks —
**26 Iron Forge, 47 Grid Overload, 48 Doombots** (plus variant 26a) — and it is the only
cluster that did not decay this cycle: 47 × 48 actually ROSE, 86% → 90%. Three of its pairs
have both halves in Arena. If the cap ever binds, this is where the slots are, not 15 × 16.

Each of those pairs is already argued by at least one of the files, so none needs action
today. What no file argues is the cluster as a THREE-deck question rather than three
pairwise ones.

## 4. 15 × 16 — largely resolved by the rebuild, one residual

The previous pass called this "the one real candidate": 19 of ~35 spells shared, the whole
Team Avatar core, top of both axes, in Arena on both sides, argued by neither file. The
2026-09-19 rebuild of deck 16 (the waterbend split from 15, then nine swaps and a land)
addressed it without a prune.

**Live: 11 shared of 36 and 36 spells, cosine 80%** — the pair now sits exactly ON the §3
threshold rather than far above it. What is left:

> Aang's Iceberg · Aang, Swift Savior · Captain America, Living Legend · Compassionate
> Healer · Crashing Wave · Earth Kingdom Jailer · Hakoda, Selfless Commander · Katara,
> Water Tribe's Hope · Sokka, Lateral Strategist · Ty Lee, Chi Blocker · Watery Grasp

Note the set SHIFTED as well as shrank — Captain America and Watery Grasp are shared now
and were not before, so this is not the old list minus eight.

**THE RESIDUAL IS THE ONE THE OLD DOC NAMED, AND IT IS STILL LIVE.** Deck 15's archetype
header still reads:

> "Azorius (W/U) Air Nomads fliers / airbend + **waterbend** tempo"

It still claims the axis deck 16 exists for. The card lists have been pulled apart; the
PROSE has not. That is a one-line edit to deck 15's `#: archetype:`, not a prune, and it is
the cheapest remaining action in this document.

The old three-way choice (keep both and argue the split / merge to parent+variant / cut one
from Arena) is **resolved in favour of option 1** by events — the split happened. All that
is outstanding is writing it down.

## 5. What changed since 2026-09-18 — the de-duplication continued

Every row of the previous §3 table re-measured:

| pair | was | live | what moved |
|---|---|---|---|
| 15 × 16 | 19 / 90% | **11 / 80%** | BOTH axes — the rebuild |
| 63 × 7 | 12 / 93% | 12 / **64%** | theme only — **dropped off** |
| 43 × 79 | 10 / 90% | 10 / **75%** | theme only — **dropped off** |
| 29 × 30 | 10 / 88% | 10 / **64%** | theme only — **dropped off** |
| 30 × 40a | 8 / 84% | 8 / **57%** | theme only — **dropped off** |
| 38 × 39 | 9 / 96% | 9 / 96% | unchanged |
| 26 × 48 | 9 / 87% | 9 / 87% | unchanged |
| 47 × 48 | 9 / 86% | 9 / **90%** | theme ROSE |
| 26a × 48 | 9 / 83% | 9 / 82% | ~unchanged |
| 26 × 47 | 8 / 85% | 8 / 85% | unchanged |

**Only one pair moved on the card axis, and it is the one that was deliberately worked on.**
The four drop-offs are all theme-axis moves at a constant shared-card count — see the §2
note on why that is expected and what it means for reading the table.

The previous pass's finding still holds over the longer window: the roster de-duplicates
itself through ordinary tuning, not through pruning.

## 6. Family twins — the cheapest slots, and they are all free already

| pair | shared | % | both in Arena? |
|---|---|---|---|
| 22 × 22-brawl | 34 | 94% | no (22 only) |
| 40 × 40-brawl | 34 | 100% | no |
| 36 × 36a | 31 | 89% | no (36 only) |
| 44 × 44a | 30 | 83% | no |
| 19 × 19b | 26 | 74% | no (19 only) |
| 3 × 3-brawl | 26 | 72% | no |
| 29 × 29a | 21 | 58% | no |
| 20a × 20b | 20 | 56% | no |

**Not one of the eight biggest family twins has both halves in Arena**, so the Brawl-twin
and variant slots cannot free anything. Unchanged across three passes now; stop re-checking
it unless the Arena headers change.

## 7. Noted non-candidates (asked and answered — do not re-derive)

- **10 Mad Villainy × 11 Villainous** (asked 2026-09-21). 10 shared spells, 30% of the
  smaller list, 23 and 26 cards unique. They are each other's MOST-SHARED-CARDS partner
  while ranking **#20 and #35** respectively by theme — the G-47 split in its purest form.
  BR artifacts midrange (14 early drops, avg MV 3.08, card advantage 3) against mono-B
  control (6 early drops, avg MV 3.94, card advantage 6). The shared ten are Villain typal
  staples, which two Villain decks are supposed to share. **NEITHER carries an `#: arena:`
  header**, so a prune here frees nothing. Not a candidate on any axis.
- **26a × 48** remains the other mutually-silent pair and is still NOT a candidate: 9
  shared against 27 unique to each, and 26a is not in Arena. The 82% cosine is a tag match
  on UR-artifacts, exactly the shape §2 warns about.

## 8. Decisions for the user

1. **How many decks are actually in your Arena client?** Everything here is conditional on
   it. If the answer is near 48, close this doc — there is nothing to prune.
2. **15 × 16 — write the split down.** Deck 15's `#: archetype:` still claims the waterbend
   axis deck 16 owns. One line, no prune, and it closes the document's original candidate.
3. **The 26 / 47 / 48 artifact cluster** is the densest remaining knot and the only one
   that did not decay. Worth one three-way read — not three pairwise ones — if the cap
   turns out to bind. Nothing to do if it does not.
