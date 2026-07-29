# Handoff — start the next session here

Written 2026-07-29, for a session with none of this one's context.
Read this before CLAUDE.md's Common Gotchas, not instead of them.

**Read the evidence file when a rule's reasoning matters.** CLAUDE.md carries the RULE and
any live residual; the incident and measurement live under the anchor the rule ends with —
`[G-nn]` / `[K-nn]` in `docs/gotchas.md`, `[C-nn]` in `docs/cycle-config.md`. Nothing was
deleted; open the long form before deciding a rule looks arbitrary. **Keep Cycle Workflow
Config terse** — its shape is specified by `setup-cycle.md` in claude-workflow-tools and
the vendored commands read those fields.

**Also live: `docs/systems-map.md`.** Read it when you need
to know which command answers a question, what a workflow's real command path is, or
why two commands disagree. It replaces re-deriving that from 2,100 lines of prose.

---

## 1. Repo position

- Working branch `claude/project-development-continuation-3hnw5r`, based on `origin/main`
  at the squash-merge of PR #87. If its PR is merged, restart it from `main`
  (`docs/verify-commit-tail.md` §3).
- Gates green at handoff: `check_all` all invariants hold (~11s); **686 pytest**;
  `check_patterns` 145 live; `check_commands` OK (33 subcommands / 34 scripts).
- **CLAUDE.md is 757 lines** (was 2,219). The evidence is in `docs/gotchas.md` (rules)
  and `docs/cycle-config.md` (the Cycle Workflow Config fields), linked by anchor and
  gated in both directions by `scripts/check_docs.py`. The doc split is COMPLETE.
- Collection: 1,853 cards, 64 roster decks. Unchanged this session — no card or deck
  data was touched, only tooling.

## 2. What the last session did

The task was a task-first systems map, then an agreement gate, then fixes prioritized
by the map, holding the subcommand count flat. All four held.

1. **`docs/systems-map.md`** — the four workflows, their real command paths and costs,
   every **reconciliation point** where a human must settle two answers, and an
   overlapping-answer inventory with measured agreement rates.
2. **`scripts/check_agreement.py`** — the twelfth hard gate, and the one that covers
   what the other eleven structurally cannot: two functions that are each correct and
   disagree with each other.
3. **The fix the map surfaced** — `_weakest_cut` (the cut hint on every `suggest-homes`
   row) and `rank_cut_candidates` (what `cuts` prints) both answered "this deck's
   most-cuttable card" and **disagreed on 36 of 64 decks**. One `cut_keep_score` now.
4. **`load_rarities` memoized** — 85% of `deck.py cuts`' runtime, found by profiling.

Subcommand count: **33 → 33.** A duplicate model was deleted, not added.

## 3. The task for the next session

**Pick from §5. There is no single blocking item.** Note §5.5 closed earlier today — the
P/T fix-hypothesis was tested and rejected, so the list is one speculative item shorter
and the remaining work is ordinary. The diagnosis that opened this
cycle — *the models are fine, the composition layer is where the friction is* — is now
one gate and one map better, and the remaining items are ordinary work rather than a
structural gap.

If you want the highest-value one: **`_signature_themes` saturation in `cuts`** (§5.1) —
measured, and needing only the roster-wide diff the standing rule requires before its
one-line caller change can land. The doc split is finished; both phases are done.

## 4. What NOT to do

- **Do not re-weight `cuts`' fit sum.** Simulated across all 64 decks last cycle and
  rejected; also structurally forbidden by `tests/test_recommendations.py`.
  (§5.1 is NOT this — it unifies two definitions of "signature", it does not tune fit.)
- **Do not add a 34th subcommand** without saying what it replaces.
- **Do not trust a gate you have not watched fail.** See §6 — a new gate was vacuous on
  the pair it was written for, twice, and a first run of the creature experiment measured
  a miscalibrated signal rather than the hypothesis.
- **Do not re-propose the P/T creature signal** (§5.5). It was pre-registered, tested and
  rejected; re-running it without new data would just re-find the same null.
- **`docs/tooling-improvement-plan.md` is HISTORICAL** (F01–F15, all landed). Its F01
  instructs adding `lib.full_card_text`, which was later deleted as dead code.

## 5. Open work, in rough value order

1. **`_signature_themes` saturates in `cuts`.** `rank_cut_candidates` gives a +2
   keep-boost off the LOOSE signature set (the union of every `#: protect:` card's tags);
   all three `fit_strength` callers use the STRICT set (a theme carried by ≥2 protected
   cards) precisely because the loose one saturated there (`check_suggest` anchor 11b).

   | | fires on |
   |---|---|
   | loose (what `cuts` uses) | **86%** of nonland cards across the 22 `#: protect:` decks; **100%** in decks 20 and 46 |
   | strict (what `fit_strength` uses) | 66% |

   A boost applying to every card in a ranking is a constant. The motivating case
   (deck 30's counter-doublers) survives the strict set — its strict signature is
   exactly `{counters}`. **Needs a roster-wide before/after `cuts` diff before landing**;
   the harness for that is in the block, and it is the same one that proved the
   `cut_keep_score` extraction byte-identical. Details: `docs/systems-map.md` §7.

2. **An incremental `make refresh`.** Still ~10 min for a 4-card ingest, re-pricing
   ~15.9k cards through Scryfall's rate limit. The largest single cost in the repo and
   the clearest quality-of-life win. **The rebuild ORDER is load-bearing and pinned by
   `tests/test_verify_ingest.py` — an incremental path must not fork it into a second
   recipe.** The Makefile is deliberately the one executable definition.

3. **`tier --audit-rationale` STAY-marker false negative.** A `_HISTORY_CUES` change-cue
   about one card suppresses a citation of ANOTHER card in the same ±140-char window,
   even when the clause says the card **stays**. Deck 42a asserted "Erode stay[s]" after
   Erode was cut and the audit reported clean. Fix is the mirror of `_cites_as_arriving`.
   **Needs a roster sweep before landing**, per the cue-list rule. Until then a "X stays"
   claim is not covered — check by hand after a swap.

4. **`doubler_restriction` parses POWER scopes only.** A type-scoped doubler (Splinter,
   Radical Rat's Ninja clause) is counted against the whole deck — 27 feeders in deck 20
   against a correct 12. The `✱ multiplier` figure on a tribal doubler is an upper bound.
   Fix is a second scope pattern feeding the same filter, not a second model.

5. **The creature cut-ranking regime — the P/T hypothesis is TESTED and REJECTED.**
   Do not re-propose it. Pre-registered, scored against all 31 creature cuts on
   git-reconstructed pre-swap snapshots: as a bounded ±3 co-signal it changed nothing
   (4 up / 5 down, p=1.00, agreement 48% → 48%), which was *predicted* — `fit` has a
   roster median of 44 (IQR 31–59), so a ±3 term cannot reorder anything. Scaled to span
   that IQR it made agreement slightly worse (48% → 45%). Decisive: a cut creature's body
   quality (mean 4.83) is indistinguishable from the median body of the creatures that
   STAYED (5.00), and the cut card was the worse body only 17/31 times — chance, p=0.72.

   **What replaced it:** the 45% is not a property of creatures. Per deck it runs 0/6,
   1/6, 3/6, 2/4, 4/4 — 0% to 100% — so it is largely a statement about which decks were
   edited. `deck.py feedback` now discloses that breakdown (`segment_concentration`).
   The build-vs-tune story fits deck 46 (rebuilt mid-window, 0/6) but not deck 3 (1/6, an
   ordinary tune). **The next move is MORE LEDGER DATA, not another signal** — every
   subgroup here is 4–6 rows. A pre-registered re-test at ~100 swaps is the honest step.
   Full method and numbers: `.cycle/blocks/2026-07-creature-cut-hypothesis-test.md`.

6. Smaller: the reverse `screen` flag (a candidate strictly WORSE than an incumbent);
   ROADMAP Tier 1 (theme the remaining UB flavor mechanics).

## 6. Measurements — do not re-derive

Each costs a roster sweep. All still current.

**Cut-ranking agreement** (this session): `_weakest_cut` vs `rank_cut_candidates`
**28/64 before → 64/64 after**.

**Signature-boost saturation** (this session): 86% loose / 66% strict — table in §5.1.

**`suggest` vs `suggest-homes`** (this session): they use different theme gates
(`suggest` admits any theme the deck carries, `suggest-homes` requires a CENTRAL one),
which looked like a guaranteed divergence. Across 640 picks on 64 decks they agree
**100%** — `suggest` sorts by theme weight and central themes are the heaviest, so its
top always clears the stricter gate. A consequence of the ranking, not a property.

**The recommendation ledger** at 52 scored swaps (last cycle):

| segment | agreement | median toward "keep" | n |
|---|---|---|---|
| noncreature cuts | 90% | 10% | 21 |
| creature cuts | **45%** | 56% | 31 |
| *pooled* | *63%* | *28%* | *52* |

`fit` is an **unnormalized sum**, so tag count drives the keep-score; creatures carry
~5.7 tags against ~3.0 for spells. Correlation(tag count, keep-rank) = **+0.73, positive
in 64 of 64 decks**. Normalization was simulated and rejected (top-3 themes moves it to
+0.72 and changes 1% of top-5 shortlist slots).

**Costs:** whole tune-deck gather phase ~10s · `preflight` 6.4s (it runs `check_all`) ·
`suggest-homes` 3.1s per card · `make refresh` ~10 min · `check_all` 11.3s.

## 7. Where things are

- **`docs/systems-map.md`** — the live task-first map. Start here for "which command".
- Per-cycle blocks: `.cycle/blocks/*.md`; newest
  `2026-07-systems-map-agreement-gate.md`.
- Prose state / decisions incl. what was decided AGAINST: `.cycle/STATE.md`.
- Commit discipline: `docs/verify-commit-tail.md`.
- Long-range ideas: `ROADMAP.md` (regenerate with `/roadmap`).
- **Historical, do not follow:** `docs/tooling-improvement-plan.md`.

## 8. One thing to preserve

**Measure before believing, then check the measurement.** It found every real thing this
session:

- The cut-model divergence was invisible to eleven gates and obvious in one roster sweep.
- `load_rarities` reads as fine in any single command's wall clock; cProfile said 85%.
- The new gate's role-filler pair ran GREEN with the bug it names deliberately
  reintroduced — **twice**, for two independent reasons (it read a truncated view of the
  filtered set, and it asked about only one of the two role axes). Both were found by
  mutating the code and watching the check stay green.
- The first `suggest`-vs-`suggest-homes` measurement said 100% disagreement. It was
  reading a dict's keys as rows. The real answer is 100% agreement.

A check you have not watched fail is not a check, and a number you have not sanity-tested
is not a measurement.
