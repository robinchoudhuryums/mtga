---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: BS10-04 (Batch 3 — `tags_for` had NO `artifacts` rule at all, so an
artifact deck's payoffs sank in every theme-fit ranking), plus the three follow-on items
from block `10-batch1-2-ranking-visibility`: the dashboard received `back_off`/`candidates`
without rendering either (G-40's shape), four private copies of the reminder-text regex, and
`_UNPRICED_DISCLOSE_FLOOR` unregistered in `check_docs.figure_drift`.

Files modified: scripts/tag_synergies.py, scripts/check_patterns.py, scripts/lib.py,
scripts/deck.py, scripts/build_dashboard.py, scripts/check_docs.py, CLAUDE.md,
docs/gotchas.md, decks/47-affinity/deck.txt, decks/51-unlocked/deck.txt, card-pool.csv,
card-library.csv, card-pool.build, gallery.html, dashboard.html

CHANGES:
BS10-04 | scripts/tag_synergies.py, scripts/check_patterns.py, CLAUDE.md, docs/gotchas.md,
  decks/47, decks/51, card-pool.csv, card-library.csv |
  `MECHANIC_RULES` had **no `artifacts` entry**. Every `artifacts` tag came from the KEYWORD
  map (affinity / improvise / modular / station / prototype / craft / storied), so a card
  whose whole text is "artifacts you control get +1/+1" or "spend this mana only to cast an
  artifact spell" carried no artifact theme — and `suggest` / `cuts` / `suggest-homes` /
  centrality are all theme-fit driven. Deck 47 (mono-blue affinity): of 24 artifact-
  referencing nonland cards the keyword path tagged 5, and **10 artifact-matters cards had no
  tag**, including both artifact-restricted mana sources the deck is built on.
  **Deliberately NOT an `_TYPE_MATTERS` entry**, which is the obvious home and is wrong: that
  table's first pattern is `(a|an|target|…) <TYPE>`, which for artifacts matches **427 pool
  cards** — every "destroy target artifact" printed. That is artifact HATE, and tagging it
  `artifacts` would call a hoser a synergy piece (the G-42 shape). The mechanism is right for
  Equipment and wrong for Artifact because only Artifact has a removal population that large.
  New `_ARTIFACT_MATTERS_RE` matches **273 pool cards, 1.71%** — between `exile cast` (1.68%)
  and `pay life` (2.2%), under the **3.86%** `exile cast` was explicitly capped to avoid as
  "past the point where it still identifies an archetype". Two loosenings measured and
  REJECTED for landing there: without the `an|another|one or more` anchor it also matches
  "when THIS artifact enters", i.e. every artifact with an ETB; and `artifact or creature` is
  **236 cards** of generic either-type text. The `(?<!or )` / `(?! or creature)` guards are
  load-bearing. Read on `_clean_text` (K-09) so affinity's own reminder text — which literally
  reads "for each artifact you control" — cannot mint a hit.
  Registered in `check_patterns._pattern_groups()` as "norm" (it runs on `_clean_text`, already
  lowercased — registering it "raw" beside its `_TYPE_MATTERS_RES` neighbour would be the
  wrong-corpus mistake that file's own docstring warns about). K-10 satisfied via `make
  refresh`: pool `artifacts` **158 → 415**, pool row count unchanged at 15,977 so no population
  confound. New anchor **K-15** in CLAUDE.md + docs/gotchas.md.

FOLLOW-ON 1 | scripts/build_dashboard.py | The craft table is the page's "spend a wildcard
  here" surface and it dropped both new fields. Re-measured AT THAT CALLER first, per G-40's
  rule that reaching a new caller is not free — at the dashboard's exact call shape
  (`unowned=True, limit=15`) `back_off` fires on **7 of 1,680 rendered rows across 7 decks
  (0.42%)**. Wired: the flag renders beside the card name (reusing the existing `.flag` class,
  so no new CSS token), and a `craftTotal` hint says "Top 15 of N ranked candidates" because
  the page can only ship a window and a reader who does not know one exists reads its absence
  as absence. Verified in the built payload: exactly the 7 measured rows ship, `craftTotal` on
  all 112 decks, `tests/test_templates.py` token gate green.

FOLLOW-ON 2 | scripts/lib.py, scripts/deck.py, scripts/tag_synergies.py | Four private copies
  of the reminder-text stripper, and **they were not the same regex**: `deck._REMINDER_RE` read
  `\([^()]*\)`, the other three `\([^)]*\)`, which diverge the moment a reminder contains a
  nested parenthesis. Measured across all 15,977 pool texts they agree on **0 disagreements**,
  so the divergence was LATENT, not live. One canonical `lib.REMINDER_RE` (the stricter
  `[^()]` form — on nested text it declines to span from an outer open paren to an inner close,
  the conservative direction); `lib` is the right home because it imports nothing from the
  project, so there is no cycle. The four original NAMES are kept as ALIASES rather than
  rewritten at their call sites: `check_patterns`' completeness registry is keyed by (module,
  attribute name), so renaming them would silently drop them out of the gate that proves they
  still match. Verified all five names are now one object.

FOLLOW-ON 3 | scripts/check_docs.py, CLAUDE.md, docs/gotchas.md | `figure_drift`'s own rule is
  "a figure a RULE cites as its evidence", so registering `_UNPRICED_DISCLOSE_FLOOR`'s
  calibration required documenting it first. G-60 is already exactly at the 15-line cap, so
  BS10-07's disclosure got its own anchor **G-85** (the doc gap the previous block flagged for
  /sync-docs). Two entries registered, each measured through the SAME predicate rather than a
  second copy: "K-15 artifact-matters pool cards" (273, via `_ARTIFACT_MATTERS_RE` itself) and
  "G-85 unpriced-disclosure fire rate" (14 of 43, via `unpriced_discount_cards` +
  `_UNPRICED_DISCLOSE_FLOOR`; ~1.7s, and lazy — it only runs when CLAUDE.md still makes the
  claim). Both patterns proven to MATCH and to measure correctly, and the gate was
  watched-it-fail on a deliberately wrong number (stated 999 -> reported 273).

TEST RESULTS: passed — `python3 -m pytest` **1796 passed, 0 failed** (243s);
  `python3 scripts/check_all.py` **All invariants hold ✓**; `make refresh` and `make postedit`
  both exit 0. Regression Scenario 2 (Analyze a deck — the subsystem touched) walked: **30 of
  30 commands PASS**. Two apparent failures in the first walk were mine, not the tools':
  `deck.py check 47` exits 1 because deck 47 is a WIP deck with missing cards (G-12) and does
  so identically at HEAD, and `suggest-homes` was my loop dropping the quotes around a
  two-word card name.
  Two gates fired DURING the work and both were the gates working: `check_patterns` hard-failed
  on the new regex being unregistered (fixed by registering it), and the roster figure sweep
  named decks 47 and 51 as citing central-theme counts my change moved (re-grounded 20 -> 10
  and 12 -> 13 — figures only, no tier letter touched, per K-12). The `make refresh` also moved
  K-09's pool-blank figure 343 -> 338, corrected in CLAUDE.md. Remaining soft warnings are the
  three pre-existing dead library searches (decks 20a / 50a / 69a).

REGRESSION RISKS:
  - **A MEASUREMENT OF MINE WAS VACUOUS AND I CAUGHT IT LATE.** The first before/after
    snapshot called `tier_band(vec, cards=…, meta=…)`, which takes only `vec`, so all 112
    decks errored IDENTICALLY on both sides and the diff reported "0 tier floors moved" —
    the answer I expected, from a probe that measured nothing (G-63's vacuous-probe shape).
    The `cuts` half was equally wrong: `rank_cut_candidates` returns a 4-tuple, so I was
    comparing the 2nd cut row and the repr of a SET, whose order is nondeterministic (G-54) —
    that is what the bogus "73 of 112 changed" actually measured. Redone against the real
    signatures, with the snapshot now ASSERTING zero errors so it cannot go vacuous again,
    and the BEFORE side re-taken at HEAD via `git stash`. Every roster figure below is from
    the corrected run.
  - `tags_for` emits a new theme for 273 pool cards; consumers are `cuts`, `suggest`,
    `suggest-homes`, centrality/`similar`, the wishlist target loops and `check_themes`.
    Corrected roster diff: **0 of 112 tier floors moved**, band distribution identical at
    A 67 / B 41 / C 4 (G-80's rule holds — tags feed cuts/suggest, `tier_band` reads TEXT);
    `cuts` top-3 moved on **5** decks (#1 on 3, each toward protecting an artifact card in an
    artifact deck); `suggest` top-20 on **27** decks (#1 on 2); `central_themes` on **6**.
  - Deck 47's central themes 20 -> 10 looks like a loss and is the opposite: `artifacts` went
    from 8 of its cards to **25 of 36 nonland**, so the incidental tail (`Mutant`, `Ninja`,
    `Turtle`, `combat`, `vigilance`) stopped clearing the centrality bar. Checked by reading
    both lists, not inferred from the number.
  - `lib.REMINDER_RE` consolidation changes three call sites from `[^)]` to `[^()]`. Measured
    identical on all 15,977 pool texts today; on a future nested-paren reminder they would
    differ, in the documented conservative direction. `check_patterns` still green at 352
    patterns, and `test_check_patterns`' `id()`-based coverage assertion still holds because
    the aliases ARE the registered object.
  - `craft_rows`' returned dict gained a key and the deck payload gained `craftTotal`; both
    additive, and the two existing `craft_rows` tests (the error paths) pass unchanged.
    `_CRAFT_TOTALS` is module-level mutable state in a one-shot build script, keyed by deck id,
    and is never written on the error paths — so a failed deck yields no hint rather than a
    stale one.
  - `check_all` gains ~1.7s from the G-85 figure entry (lazy: only when the claim is present).
  - Old behaviour better anywhere? No case found. The one measured cost is Three Steps Ahead
    ("a copy of target artifact **or** creature you control"), a genuine false negative bought
    by the 236-card `or creature` guard — and it was equally untagged before this change.

INVARIANTS AT RISK: None. INV-01/01b/02/03 all re-verified by the `make refresh` and `make
  postedit` runs (card-pool.csv and card-library.csv were rewritten by their OWN builders —
  `build_pool.py --all` and `tag_synergies.py --merge` — never by a library writer pointed at
  a derived file, per the standing rule). INV-04: the only deck files touched are 47 and 51,
  and only `#: tier:` prose lines — no card line, no `(SET) COLLECTOR#`, so G-65/G-77 do not
  apply. INV-05/06 untouched; INV-06 is precisely what the refresh satisfied.

NET SCORE: 1 − 0 = 1
  Production fixes (1): **BS10-04**. It fired this month and is the reason this scan exists —
  deck 47's tune produced a ranking in which the deck's own artifact payoffs sat at median
  rank 310, and 10 of its artifact-matters cards were invisible to every theme model.
  Validation on the pre-swap list: **median rank of the 15 cards actually added 310 -> 144,
  best 120 -> 20**, 9 up / 5 down.
  DEFENSIVE, not counted (3): the three follow-ons. Graded by cycle 9's precedent, which
  corrected a self-report for counting defensive work as production fixes. Follow-on 1 extends
  an existing fix to a second surface at a 0.42% rate with no evidence anyone acted on one of
  those 7 rows this month; follow-on 2 is measured at **0 disagreements across 15,977 texts**,
  i.e. it fixed nothing that was firing; follow-on 3 guards against future drift. All three are
  worth having — the consolidation in particular pre-empts this project's dominant bug class —
  but none of them fixed a live wrong answer, and saying so is the point of the bucket.
  New failure modes (0). Two stated residuals, neither new: the `or creature` guard's false
  negatives (untagged before and after), and the `[^()]` form now governing three call sites
  that previously used `[^)]` (identical today, documented direction).

OPERATOR ACTIONS / DEPLOY:
- None.
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds and publishes dashboard.html
  automatically on push to `main`. The committed snapshot was refreshed by `make postedit`.
  Note this push changes what the PUBLISHED page shows (the craft tables gain the back-half
  flag and the window hint), so it is worth a look after Pages runs.

FOLLOW-ON ITEMS:
- **BS10-01 / BS10-02 remain open** — the interaction taxonomy holes, the same class as
  BS10-04 one model over: exchange/gain control **79 of 84 missed (94%)**, tap+stun **33 of 34
  (97%)** against bounce's 1 of 31. Deck 47's own `#: tier:` block argues from the first of
  those figures. Unlike BS10-04 these feed `role_tally`, so they WILL move tier floors —
  budget for a K-14 floor diff and a roster `#: tier:` prose sweep.
- The `or creature` guard costs the genuine either-type cards an artifact deck would copy or
  sacrifice (Three Steps Ahead is the measured instance). Do not relax it without re-measuring
  both sides — it is holding back 236 cards.
- My snapshot scripts are scratch-only. If this kind of roster diff is run again, the lesson
  worth keeping is the ASSERT: a before/after harness that does not fail loudly on a broken
  call will report the expected answer from a probe that ran nothing.

DOCUMENTATION UPDATES NEEDED:
- DONE in this change: **K-15** (the artifacts tagger hole, rule + long form + registered
  figure), **G-85** (BS10-07's unpriced-discount disclosure and its p75 calibration, which
  closes the G-60 doc gap the previous block flagged), and K-09's pool-blank figure 343 -> 338.
- NOT done, still open from the previous block: G-02/G-43/G-58 do not mention BS10-08's
  back-half flag, and G-38/G-22 do not mention BS10-05's ranking-window footer or the
  median-407 measurement — which remains the most decision-relevant number this cycle produced.
  Neither is a contradiction; each is a gotcha that has not caught up. A `/sync-docs` pass.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
