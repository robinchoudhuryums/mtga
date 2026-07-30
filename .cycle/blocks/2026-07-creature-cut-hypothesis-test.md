# Block — testing the creature cut-ranking hypothesis (2026-07-29)

**Result: the hypothesis is FALSE. Nothing shipped from it.** One reporting change did
ship, from a confound the test surfaced.

## The hypothesis on file

From `.cycle/NEXT-SESSION.md` §5, carried for two cycles as "the most promising
unexplored direction":

> Bodies compete on stats, evasion and curve slot; theme-fit structurally cannot see any
> of that. `card-pool.csv` already carries `Power`/`Toughness` (read via `lib.card_power`)
> and nothing in the cut ranking uses them.

## Method

Pre-registered before any result was computed (the signal, the three models, the success
criteria, and a one-evaluation stopping rule). n=31 is small enough that iterating a
signal against it until the number improves is fitting noise — and
`tests/test_recommendations.py` structurally forbids a scoring function reading the
ledger, so tuning one by hand would defeat that gate manually.

**Signal**, defined from Magic first principles: stats-per-mana against a vanilla
benchmark, plus evasion (flying/menace/trample/…, capped), minus curve-slot redundancy.
0–10, centred at 5.

**Ground truth**: the 31 creature cuts in `recommendations.csv`.

**Snapshots**: for each ledger row, the newest committed version of that deck file that
still CONTAINS the cut card — the state the decision was made against — found by walking
`git log --follow` (which handles deck 46's rename) and reading each version with
`git show <ref>:<path>`. 50 of 53 rows resolved; 3 skipped (two cards added and cut
inside one uncommitted session, one unrankable). **Both models are scored on the same
snapshot**, so the comparison is paired; the rank stored in the ledger is deliberately
NOT reused, since it was computed against the exact pre-swap state and mixing the two
would be apples-to-oranges. Reconstruction validated by reproducing the known baseline
(15/31 here vs the ledger's 14/31 — the small gap is the commit-boundary approximation).

**Models**: M0 = current `cut_keep_score`; M1 = M0 + body quality as a bounded ±3
co-signal; M2 = M0 + body quality scaled to span the creature `fit` IQR.

## The first run was invalid, and was thrown out

Mean body quality came out at 2.22 on a scale specified as centred at 5, with 14% of
creatures clamped at 0. Diagnosis: the hand-guessed benchmark `P+T ≈ 2·MV+1` is 2 points
too generous on this corpus (mean rate excess −2.20), and the raw curve-redundancy count
(mean 3.44, max 11) punished every creature in a 24-creature deck — it was measuring deck
size, not the body. **That run tested a broken implementation, not the hypothesis.**

Recalibrated against the CORPUS — pool median P+T per MV, redundancy as a SHARE of the
deck's creatures — which re-centred it at mean 5.21 / median 5.00, 0% clamped. Corpus
calibration is not outcome tuning: nothing in it has seen a swap decision. Then ONE run.

## Results

| model | paired (up / down / tied) | sign test | creature agreement | median toward 'keep' |
|---|---|---|---|---|
| M1 bounded ±3 | 4 / 5 / 22 | p=1.00 | 48% → 48% | 53% → 53% |
| M2 fit-range | 11 / 16 / 4 | p=0.44 | 48% → **45%** | 53% → **56%** |

Guard: noncreature scores unchanged (0) under both, as a creature-only term requires.
(My first guard was mis-specified — it compared noncreature *ranks*, which necessarily
shift when creatures reorder around them.)

M1's null result was **predicted in the pre-registration**: `fit` has a roster median of
44 and an IQR of 31–59, so a ±3 term cannot reorder anything. That is a finding about the
architecture — the hypothesis cannot be delivered as a bounded co-signal at all.

**The decisive measurement is the separation check.** If body quality discriminated these
decisions at all, cut creatures would score below the creatures that stayed:

- cut creature body quality: mean **4.83**
- creatures that stayed, deck median: mean **5.00**
- cut card was the worse body: **17 / 31** — chance, p=0.72

The creatures the user cut are not the worse bodies. P/T is not the missing signal.

## What the test DID find

The creature agreement rate is **not a property of creatures**. Per deck: 0/6, 1/6, 3/6,
2/4, 4/4 — **0% to 100%**. The 45% figure says more about which decks happened to be
edited in the ledger window than about how `cuts` grades bodies.

The tempting explanation — deck 46 was rebuilt from scratch during the window, and a cut
during a BUILD means "this didn't make the 60", not the question `cuts` ranks — fits deck
46 (0/6) but **not deck 3 at 1/6**, an ordinary tune. Excluding deck 46 moves the segment
only 45% → 56%, still under the noncreature 90%. All 4–6-row subgroups with enormous
overlapping intervals: exploratory, not a conclusion.

## What shipped

`deck.segment_concentration` + a per-deck breakdown printed by `deck.py feedback` under
the weak segment. Same principle as the segmentation itself, one level down: a segment
rate dominated by one deck is that deck's rate wearing the segment's name.

**It has no share threshold, and that is the point.** The first draft disclosed a deck
holding >20% of the segment — and deck 46, the case that motivated the function, sits at
6/31 = **19.4%** and did not print. The fix was not a lower cutoff: a threshold tuned
until the finding you already believe appears is the finding smuggled into a constant.
Every deck with ≥3 rows gets a line and the reader sees the concentration whatever it is.
Pinned by `TestSegmentConcentration`, including that regression; both the threshold and
the sort order were mutation-tested.

## Follow-on

**More ledger data, not another signal.** Every subgroup here is 4–6 rows. The instrument
now discloses its own concentration, so the next N swaps will be readable in a way these
52 were not. A pre-registered re-test at ~100 swaps is the honest next step.

Also worth considering, and NOT done here: recording whether a swap was a BUILD or a TUNE
at `swap --apply` time. It would separate the two populations properly rather than
inferring from per-deck variance — but it needs the skills to pass it, which is another
hand-kept thing that can rot, so it should only be added if the build/tune split survives
a larger sample.

## Verification

- `check_all` — all invariants hold. `pytest` — 673 passed (was 668; +5).
- Two code mutations on `segment_concentration` (threshold reintroduced; sort reversed),
  each confirmed to fail the new tests.
