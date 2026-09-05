# Tier-rubric investigation + the floor-band claim gate — 2026-09-03

**Trigger.** Deck 78 "Team Avatar" has played well (5-2) against a claimed B, and the user
asked what the tier floors are based on and whether the rubric needs adjusting, correctly
noting it is the yardstick every deck is compared against.

## Answer: the rubric is not changing, and three independent measurements say so

**What the floor actually grades.** `tier_band` reads TWO of the eleven terms
`deck_quality_vector` produces — interaction and card advantage (plus `_clock_score`,
only on an `#: plan: aggro` deck; 78 is midrange). Protection, curve, X-cost, early-mana
split and central-theme density are all deliberately report-only (G-25/G-48/G-60/G-81).

**Deck 78 is invisible to it by construction, and so is the roster.** 10 of its 36
nonland cards score NO role at all — Doubling Season, Starfield Vocalist and Katara among
them, i.e. the entire trigger-doubling thesis — and another 11 are Payoff/engine, a
bucket the floor does not read. 21 of 36 contribute nothing. But that is not special:
the roster's MEDIAN deck has **71%** of its nonland cards invisible to the floor; 78 is
**75%, rank 42 of 115**.

**A payoff-density term was simulated and DECLINED.** +1 per 4 payoff cards, capped +3,
added to the resilience sum: **16 of 115 decks change band** (B→A ×8, C→B ×8), the C band
collapses 9→1 and A reaches 62% — re-starting exactly the saturation BS8-06 fixed — **and
deck 78 stays at B**. The term the deck's own thesis argues for does not move the deck
that prompted it.

**The record cannot arbitrate.** 30 decks with a record, 79 attributed matches, pooled
43-36 (54%). Match-weighted correlation with winning: interaction −0.004, card advantage
−0.036, protection −0.070, **int+ca (the floor itself) −0.031**. The ±0.22 band is the
null at n=79, so nothing clears it (`central_themes` at +0.237 is the only axis that
does, at 8 comparisons, and is not actionable). This is not evidence the floor is wrong;
it is evidence the sample sees nothing. Deck 78's 5-2 is P=23% at a coin flip and one win
above the pooled baseline, at n=7 against `_MIN_SAMPLE = 20`.

**Threshold spread is healthy**: A 63 / B 43 / C 9, top band 55% against the 85%
`tier_floor_spread` alarm. **Re-derive the table when that warning fires, never because a
deck outperformed its letter.** The remedy the rubric already provides is the human
letter, which may sit ONE band above the floor — deck 78's own `#: tier:` block calls
itself a RE-GRADE CANDIDATE and defers the call, which is the correct posture.

## What the investigation found instead: 15 stale floor-band claims, invisible to the audit

Every `--audit-rationale` figure family resolves through `_figure_lookup`, and everything
it holds is a NUMBER. The commonest structural assertion a `#: tier:` block makes is a
LETTER ("the metrics floor is A", "one band UNDER its A metrics floor") — unverifiable by
construction. Re-deriving `TIER_FLOOR_REQ` last cycle then left **36 floor-band claims on
the roster, 15 of them false the same day**, every one reported CURRENT.

- `_FIG_FLOOR_BAND` + `_floor_band_claims` price a claim against `tier_band`. Roster:
  **36 raw → 15 reported → 15 real, 0 false**. Registered in `check_patterns`, seven unit
  tests in `tests/test_deck.py::TestFloorBandClaimsAreAudited`.
- **Deliberate divergence:** a band claim is NOT suppressed by the shared
  `_figure_is_history`. A change narrative names where a NUMBER came FROM but where a
  BAND LANDED; the shared rule dropped 3 real hits (decks 12/23/69a). Tense of the
  captured verb (`floor READ A` vs `READS A`) plus a narrow explicit cue does the work.
  An earlier cue list carried `had` and deck 23's "(it had zero)" muted a real claim.
- **One false positive, guarded:** deck 75's "held ONE band under the floor **at B**"
  names the LETTER. Only the bare-`at` form is guarded, and only after a band-relative
  preposition — its sibling "put the metrics floor at A" is a real claim and needs `at`.
- **A rule's explanation lives in the corpus the rule scans.** Re-grounding fifteen blocks
  meant writing "moved the A bar to interaction 7", which `interaction\s+(\d+)` reads as a
  claim about the citing deck: the sweep went 0 → 8 hits on text written to fix it.
  Reworded to "raised the A floor's interaction requirement to 7".

**14 deck files re-grounded** (7, 12, 19, 23, 35a, 36, 37a, 39, 42, 56a, 65, 66, 69a, 78),
and **no tier letter was touched** — correcting the floor a block cites is a different act
from re-grading the deck that cites it. Most had simply stopped being "one band under an A
floor" and become "at a B floor" with the list unchanged. Two decks moved further than
that: 23 now floors C (the 2026-09-01 blink fix took its interaction 7 → 5) and 56a floors
C, both now graded one band ABOVE their floor, which the rubric allows.

**Gates:** `check_all` all invariants hold, one expected G-75 soft warning; full pytest
suite green with `PYTEST_NO_SKIPS=1`; roster stale-figure sweep back to **0**.

## Carried forward

- Deck 78's B→A re-grade is still a HUMAN call. The evidence now runs both ways: the play
  record argues up, the metrics do not move, and the axes it wins on are ones the floor
  cannot see. `tier 78 --to A` prices the measurable gap at +1 interaction, +1 card adv.
- The new games the user mentions are **not in `matches.csv`** — it still holds 7 rows for
  deck 78 (5-2). Run `/log-matches` before reading the record again.
