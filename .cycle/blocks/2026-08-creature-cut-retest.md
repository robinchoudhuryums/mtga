# Block — the creature-cut re-test at n=103 (2026-08-07)

**PRE-REGISTRATION. Everything above the RESULTS heading was written before any
outcome number was computed.** The 2026-07 test earned that discipline: its first run
was invalid and had to be thrown out, and the rule that saved it was one evaluation,
criteria fixed in advance.

## Why this is being re-opened, and why that is not p-hacking

The 2026-07 test rejected a SPECIFIC hypothesis — that creature body quality (P/T per
mana, evasion, curve redundancy) was the missing signal — and rejected it decisively:
the creatures the user cut were not the worse bodies (17/31, p=0.72). Its own follow-on
was "more ledger data, not another signal", with a pre-registered re-test at ~100 swaps
named as the honest next step.

The ledger has since reached that size, and the gap did not close:

| | 2026-07 (n=31 creature / 52 total) | 2026-08 (n=103 creature / 251 total) |
|---|---|---|
| creature agreement | 48% | **50%** |
| noncreature agreement | 90% | **86%** |

Twice replicated, at 3.3× the sample, with the per-deck concentration disclosure now
running and no single deck able to explain it (worst deck is 6% of the segment). This
is a stable property of the model, not a small-sample artifact.

**The hypothesis under test is NOT the one that was rejected.** It is the mechanism the
`feedback` warning already names in prose, which has never been measured:

> `cuts` scores a card by SUMMING theme weights over its tags with no normalization for
> tag count, and creatures carry roughly twice as many tags as noncreature spells, so
> they are systematically protected.

## The premise, measured first (a fact about the corpus, not an outcome)

Mean synergy tags per pool card, by primary type:

| type | n | mean tags | median |
|---|---|---|---|
| creature | 9081 | **5.31** | 5 |
| noncreature | 6197 | **3.15** | 3 |
| land | 736 | 2.99 | 3 |

Ratio 1.69×, so the prose figure "roughly twice" is a little generous and should be
tightened to 1.7× whatever this test concludes. The premise holds: `fit` is a SUM over
a set whose size differs systematically by card type, so creatures start ahead.

Note what the premise does NOT establish. A larger tag count only inflates `fit` for
tags that are in the deck's `theme_w`, and a creature's excess is substantially
CREATURE-SUBTYPE tags (Elf, Wizard, Druid). Those are already credited separately by
`cut_keep_score`'s `min(tribal, 6)` term — so the excess may be double counting rather
than mere noise, which is a different bug with a different fix. Both are tested.

## Models

* **M0** — the live `cut_keep_score`. Baseline.
* **M1 — normalize.** Replace `fit = Σ theme_w[t]` with the MEAN over the card's tags,
  rescaled to M0's corpus mean so the other terms keep their relative weight. Tests the
  warning's stated mechanism directly.
* **M2 — de-duplicate.** Leave `fit` a sum, but exclude creature-subtype tags from it,
  since `min(tribal, 6)` already pays for them. Tests the narrower "the excess is double
  counted" reading. Touches creature scores only, by construction.

## Method (identical to the 2026-07 test, so the two are comparable)

* Ground truth: the creature cuts in `recommendations.csv`.
* Snapshot: for each ledger row, the newest committed version of that deck file that
  still CONTAINS the cut card — the state the decision was actually made against —
  via `git log --follow` + `git show <ref>:<path>`.
* Paired: all three models score the SAME snapshot. The rank stored in the ledger is
  deliberately NOT reused (it was computed against the exact pre-swap state; mixing the
  two is apples-to-oranges).
* Reconstruction is validated by reproducing the M0 baseline to within the
  commit-boundary approximation the earlier test measured at ~1 row in 31.

## Success criteria, fixed in advance

A model SHIPS only if **all three** hold:

1. creature agreement improves by **≥8 percentage points** (50% → ≥58%);
2. noncreature agreement falls by **no more than 2 points** (86% → ≥84%);
3. the paired movement is not chance — sign test **p < 0.05**.

Threshold 1 is set at 8 points because the segment is 103 rows: a 1-sigma swing on a
50% rate at n=103 is ~4.9 points, so anything under ~8 is inside the noise the sample
can produce on its own.

**Stopping rule: ONE evaluation.** If neither model clears the bar, the finding is
recorded as a property of the model, the prose is corrected to the measured 1.7×, and
this question is CLOSED — no third signal, no threshold adjusted after seeing a number.
The failure mode being guarded against is the one `segment_concentration` was written
about: a constant tuned until the finding you already believe appears.

## What "closed" would mean

Not that the model is fine. It means the 50% is understood and disclosed rather than
fixed: `cuts` stays a shortlist on creatures, the printed warning stays, and the
remaining lever is more ledger data — the honest reading being that a THEME-fit model
cannot rank bodies, which is what the 2026-07 test found from the other direction.

---

## RESULTS

**Verdict: M1 REFUTED, decisively and informatively. M2 not adopted, underpowered.
The question is closed; one prose fix shipped from it.**

### Two invalid runs were discarded before any outcome existed

Both were harness defects that produced ZERO scored rows, so neither could have been a
peek at a result:

1. `deck_paths()` was hand-rolled as `filename.split("-")[0]`, but decks live in
   DIRECTORIES and variant ids carry a letter (`40a`) — every one of the 266 rows
   reported `no-deck`. Replaced with `deck.discover_decks()`, the real API.
2. `discover_decks` returns ABSOLUTE paths. `git log -- <abs>` accepts one and
   `git show <ref>:<abs>` rejects it ("exists on disk, but not in <ref>"), so the two
   halves of the snapshot lookup disagreed silently and all 266 rows became
   `no-snapshot`. Fixed with `os.path.relpath`.

Then ONE evaluation, as pre-registered.

### The numbers

| model | creature n=38 | noncreature n=78 | paired creature (toward-cut / away / tied) |
|---|---|---|---|
| **M0** baseline | 20/38 (**52.6%**) | 65/78 (**83.3%**) | — |
| **M1** normalize | 26/38 (**68.4%**) | 40/78 (**51.3%**) | 24 / 9 / 5 |
| **M2** de-duplicate | 22/38 (**57.9%**) | 63/78 (**80.8%**) | 20 / 9 / 9 |

M0 reproduces the live ledger (50% / 86%) to 2.6 and 2.9 points, which is the
commit-boundary approximation the 2026-07 test measured at ~1 row in 31. The
reconstruction is sound.

### M1 — refuted, and the refutation is the useful part

M1 clears criterion 1 easily (+15.8 points, well past the +8 bar). It fails criterion 2
by **32 points**: noncreature agreement collapses 83.3% → 51.3%, i.e. normalizing turns
the segment that works into a coin flip too. That is not a near miss and no sample-size
caveat touches it — it is measured on the LARGER segment (n=78) and it is an order of
magnitude past the tolerance.

**What that means is more interesting than the rejection.** The warning printed by
`deck.py feedback` asserted that the unnormalized sum was the *cause* of the creature
problem. It is not: the sum is carrying real signal for noncreature cards, and removing
it costs more than it buys. The two segments want different treatments, which is a
statement about a single-number model, not about a bug in one term. **The tool was
telling its reader to go fix something that would have made it worse**, so the prose was
corrected in the same commit — `_print_recommendation_segments` and
`recommendation_segments`' docstring now state the measured asymmetry as an observation
and name both rejected hypotheses instead of asserting a mechanism.

### M2 — not adopted, and honestly underpowered

+5.3 points creature (bar: +8) and −2.5 points noncreature (bar: −2). It misses both
criteria, so under the stopping rule it does not ship.

**The caveat is stated rather than argued away.** The pre-registration anticipated
n=103 creature rows and set the +8 threshold from that; the harness resolved only 38.
At n=38 one sigma is ~8.1 points, so M2's +5.3 is comfortably inside noise and this is
NOT a clean rejection of the double-counting reading — it is an inconclusive result
being recorded as inconclusive. The attrition is a known harness defect and is written
down below so a future re-test starts ahead.

**No third run was made to chase a better n.** Re-running after seeing the numbers is
precisely the discipline the stopping rule exists to enforce, and it is the failure
`segment_concentration` was written about one level down.

### The harness defect a future re-test should fix first

Of 266 ledger rows, 103 are creature cuts and 163 noncreature; the harness scored 38 and
78. Attrition is 26 `no-snapshot` plus ~124 rows where the cut card resolved to a
snapshot but was absent from the ranking. The likely cause is the snapshot test itself:
`cardname.lower() in body.lower()` matches a name appearing in a `#:` header or comment,
so it can select a version in which the card is discussed but not played. A future
re-test should match against PARSED card lines (`parse_deck_file`), not raw text — the
2026-07 run resolved 50 of 53 with a smaller, less variant-heavy corpus and did not hit
this.

### The decision

1. **M1 is closed permanently.** Tested, refuted, and the refutation is recorded in the
   code so nobody re-derives it from the tag-count asymmetry, which is real and
   misleading.
2. **M2 is parked, not rejected** — with the exact defect that must be fixed before it
   is asked again, and the sample size it needs.
3. **The standing guidance does not change**: `cuts` is a shortlist on creatures. G-09
   already says so and remains correct.
4. **The remaining lever is still more ledger data.** That has not changed since
   2026-07, and it is now backed by two rejected mechanisms rather than one.
