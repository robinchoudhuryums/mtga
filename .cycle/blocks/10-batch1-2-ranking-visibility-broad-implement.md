---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: BS10-03 (card-advantage role hole: "put the rest into your hand"),
BS10-05 (the `suggest` ranking window is invisible — the footer counts the TRUNCATION, not
the ranking), BS10-06 (no tool performs K-13's effect-shape search; every sweep was a
hand-written throwaway script), BS10-07 ("effective avg MV" does not price affinity /
improvise / cost-reduction discounts and never said so), BS10-08 (a split / Adventure /
Room card's BACK half can need a colour the deck lacks, disclosed by no surface)

Files modified: scripts/deck.py, scripts/pool.py, CLAUDE.md,
decks/67-warpwright/deck.txt, scripts/role_baseline.txt, dashboard.html

CHANGES:
BS10-03 | scripts/deck.py, decks/67-warpwright/deck.txt, scripts/role_baseline.txt |
  Added `r"put the rest into your hand"` to `_ROLE_PATTERNS["Card advantage"]`. The family
  is a multi-card draw whose word for drawing is "put", so every pattern in the bucket
  missed it: 4 pool cards, 4 scoring ZERO card advantage (Make Your Own Luck, Allure of the
  Unknown, Threats Undetected, Deliver Unto Evil). Every member delivers two or more cards
  — the "rest" of a revealed or searched set is plural by construction — so there is no
  cantrip exclusion to make, which is why the bare phrase is safe where a bare "draw a
  card" would not be. K-14 roster diff: **1 deck moved (67, card_advantage 4 -> 5), 0 tier
  floors moved**, band distribution unchanged at 67 A / 42 B / 5 C. Per K-12/G-67 the
  roster figure sweep then named deck 67's `#: tier:` prose as stale — corrected 4 -> 5 in
  the same change, along with the adjacent claim the same read showed false ("Fblthp scores
  ZERO roles" -> "scores no CARD-ADVANTAGE role"; it scores Protection/trick off Ward {2},
  and the under-read argument the clause makes is unaffected). No tier LETTER touched.
  `role_baseline.txt` pruned by 1 via `make postedit` (make your own luck acknowledged as
  zero-role, no longer is).

BS10-05 | scripts/deck.py | Two disclosures, no model change. (a) `suggest_scored` now
  returns `candidates=len(suggestions)` — the PRE-truncation count — and `cmd_suggest`
  prints "Showing the top N of M ranked candidate(s)". The footer previously read "20
  suggestion(s)" whether the ranking held 20 candidates or 958, and a reader who does not
  know a window exists reads its absence as absence. (b) `cmd_feedback` now reports where
  the adds actually ranked, from `Add Rank`, which the ledger has stored all along and
  nothing read as a distribution: **over 783 rows, median 407 · p25 94 · p75 976 · worst
  3663; 83 (10%) ranked inside the default top 20.** `Add Surfaced` collapsed exactly this
  to a yes/no at the window, which answers "was it on the page" and hides "how far down",
  and the second is the number that says whether the ranking is usable. A median in the
  hundreds is a different problem from the theme gate G-38 describes and wants a different
  fix. Gated at `_RECS_MIN_SAMPLE`.

BS10-06 | scripts/pool.py, CLAUDE.md | `pool.py --regex RE` (+ `--regex-raw`): match Card
  Text as a case-insensitive regex with reminder text stripped by default, the same way
  `tags_for` / `classify_roles` / `target_counts` read a card (K-09), so "(You may cast…)"
  boilerplate cannot mint a hit; `--regex-raw` keeps it for the library-search family whose
  riders live there (G-75). K-13's rule is that a literal search cannot see a generically
  worded effect, and its remedy — search the EFFECT SHAPE — had no tool: every such sweep
  in recent tuning passes was a hand-written script over card-pool.csv, rewritten from
  scratch each session. The G-53 shape one step earlier: not a capability nothing reaches,
  but one never built. Reminder stripping routes through `deck._REMINDER_RE` via the same
  lazy-proxy pattern `classify_roles` uses (a caller, not a fifth private copy), so
  `--regex` and `classify_roles` cannot answer different questions about the same card. An
  invalid pattern and a bare `--regex-raw` both exit 2 with a named reason. Cross-checked
  against the ad-hoc sweep it replaces: `--regex 'exchange control of|gain control of
  target'` returns 84, exactly the hand-written count. K-13 rewritten to name the tool.

BS10-07 | scripts/deck.py | New `unpriced_discount_cards()` + `_UNPRICED_DISCLOSE_FLOOR`,
  wired into `cmd_stats` and `cmd_tier`. `effective_avg_mv` substitutes the PRINTED
  alternative costs `_ALT_COST_RE` finds (Warp / Plot / Foretell) and nothing else, while
  `classify_cost` flags a wider ◊ set — affinity, improvise, convoke, delve, evoke, "costs
  {N} less" — that it never prices, because what those shrink by is a board state the curve
  does not have. So a deck whose whole premise is a discount printed "effective avg MV 3.51
  against 3.54 printed" and meant the printed curve: deck 47 (mono-blue affinity) carried
  SEVEN such cards and the correction moved 0.03, on a list that routinely casts a {6} for
  {U}{U} — and that figure was read during a live tune. Derived from the same two
  primitives the ◊ list and the effective figure already use (`cheat_cost_cards` +
  `classify_cost`), so the three surfaces cannot disagree (G-40). DISCLOSURE, never
  pricing, for the reason G-25 and G-60 both give. Floor calibrated from the only
  population that can see the line — the 43 decks printing an effective figure, where the
  unpriced count runs p25 1 / p50 2 / p75 3 / p90 5 / max 11: at >=1 it fires on 83% (the
  G-07 saturation shape), so the floor is that axis's own p75 and it fires on **14 of 43
  (32%)**.

BS10-08 | scripts/deck.py | New `split_back_offcolor()` + `_back_half_is_cast_from_hand()`,
  wired into `cmd_screen` and `suggest_scored`/`cmd_suggest`. `_candidate_castability` and
  `parse_pips` read the FRONT face, which is correct (G-02) — but every recommender prints
  the whole `Front // Back` name, and 102 of the pool's 308 split / Adventure / Room cards
  (33%) have a back half needing a colour the front does not. So a mono-U deck was shown
  "Failure // Comply" ({1}{U} // {W}) with nothing indicating half the card is uncastable
  in it, against G-43's rule to grade by the FACE YOU CAST, on surfaces G-52 says must
  print their evidence. Found while sweeping Adventure removal for deck 67, where four hits
  were this shape. **Scoped to faces you CAST**: a TRANSFORM DFC reaches its back by
  transforming, not by paying, so Norman Osborn ({1}{U} // {1}{U}{B}{R} — a transform cost)
  and Bruce Banner, the two cards G-58 cites as exactly this mis-bin, must not flag. There
  is no `layout` column, so `_back_half_is_cast_from_hand` reads the only unambiguous
  evidence the type line carries (Adventure / Room back, or instant-or-sorcery on both
  faces) and DECLINES the ambiguous middle — 213 of 308 qualify; the 157 creature/land-
  faced DFCs stay out rather than be answered wrongly (the G-76 scope line). `type_line` is
  a REQUIRED parameter so a forgetful caller fails loudly rather than silently returning "".
  In `screen` it is suppressed when the FRONT is uncastable, or it would contradict the
  `⚠ NOT castable` flag printed above it. Measured AT the caller per G-40: **1,036 of
  223,155 candidate rows roster-wide (0.46%)**; in the default top-20 window, 4 rows across
  4 decks — one of them deck 49's Decadent Dragon // Expensive Taste, which is G-43's own
  worked case. Disclosure only: it never filters a pick or moves a score.

TEST RESULTS: passed — `python3 -m pytest` **1796 passed, 0 failed** (235s);
  `python3 scripts/check_all.py` **All invariants hold ✓** (exit 0); `make postedit` clean.
  ONE failure was caused by this session and fixed: `test_deck.py::
  TestArchetypeFiguresAreAudited::test_the_roster_figure_sweep_is_clean` went red on
  `('67', ('card_advantage', '4', 5))` — exactly the K-12/G-67 discipline ("run the SUITE
  after a role-pattern change, not just check_all: the roster figure sweep names every deck
  whose `#: tier:` prose still cites the old number"). This is the gate working, not a
  defect: the fix is the deck-67 prose correction recorded under BS10-03. A
  DeprecationWarning from an unescaped `\(` in the new pool.py docstring was also mine and
  is fixed (raw string). Soft warnings after the run are the three pre-existing dead
  library searches (decks 20a / 50a / 69a).

REGRESSION RISKS:
  - `suggest_scored`'s return dict gained `candidates`, and each pick gained `back_off`.
    Both are ADDITIVE; every consumer reads named keys. Consumers checked and exercised:
    `build_dashboard.py` (which shares the function verbatim — rebuilt clean by
    `make postedit`), `check_suggest.py`, `tests/test_recommendations.py`,
    `tests/test_deck.py`, `tests/test_check_dfc.py`. `back_off` is computed INSIDE
    `suggest_scored` rather than in the CLI precisely so the two surfaces cannot disagree
    (G-40); the dashboard does not yet RENDER it — follow-on below, not a regression.
  - `pool.matches()` gained a `--regex` branch read via `getattr(args, "regex", None)`, so
    the existing `tests/test_query_pool.py` callers that build a partial namespace are
    unaffected (verified: those 9 assertions pass).
  - `unpriced_discount_cards` takes the memoized `carddata`/`mana` tables. G-71 checked
    explicitly: deep-compared before/after, **neither table mutated**; 8 ms per call, two
    single-deck CLI callers only, never in `check_all`.
  - Old behaviour better anywhere? No case found. All four non-pattern changes are
    additive disclosure that cannot filter, score, or grade; BS10-03 is a one-direction
    widening measured at 0 tier floors.

INVARIANTS AT RISK: None. INV-01/01b/02/03 untouched (no CSV writer changed). INV-04: the
  only deck file edited is decks/67-warpwright/deck.txt, and only `#:` prose lines — no
  card line, no `(SET) COLLECTOR#`, so G-65/G-77 do not apply; re-parses clean (check_all
  exit 0). INV-05/06 untouched. The two model-shape gates that could have caught a bad
  pattern — `check_patterns` and `check_roles` — both pass.

NET SCORE: 4 − 0 = 4
  Production fixes (4): BS10-03 (a live deck file's grading argument carried a wrong figure;
  4 pool cards scored zero on an axis they belong to), BS10-05 (the misread this fix
  prevents demonstrably occurred this month — the "why doesn't the tooling suggest my cards"
  question was unanswerable without the rank distribution, and the answer turned out to be
  median 407), BS10-07 (a figure that advertises itself as corrected was read during a live
  tune while describing the printed curve), BS10-08 (half-uncastable cards were surfaced
  with no disclosure during deck 67's sweep this month).
  NOT counted as a production fix (1): BS10-06 is a NEW CAPABILITY — nothing was wrong, a
  tool did not exist. Graded per cycle 9's precedent, which corrected a self-report for
  counting defensive work as production fixes.
  New failure modes (0). Two STATED residuals, neither new: BS10-08 declines the ambiguous
  middle, so a modal DFC with a creature back needing an off-colour is still unflagged —
  narrower blindness than the total silence it replaces, not a new one; and BS10-07 says
  nothing below 3 unpriced cards, the deliberate anti-saturation calibration.

OPERATOR ACTIONS / DEPLOY:
- None.
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds and publishes dashboard.html
  automatically on push to `main`. The committed snapshot was refreshed by `make postedit`
  in this session; no manual step.

FOLLOW-ON ITEMS:
- The dashboard's craft table shares `suggest_scored` and now receives `back_off` and
  `candidates` without rendering either. The CLI is the surface the scan named, so wiring
  the page is out of this scope — but it is the G-40 shape exactly (a primitive that works
  and one caller that never asks), and a fix should re-measure the rate at THAT caller
  rather than inherit the 0.46% measured here.
- Four private copies of the `\([^)]*\)` reminder regex exist across scripts/ — deck.py,
  lib.py (x2), tag_synergies.py. BS10-06 added a CALLER of deck.py's, not a fifth copy;
  consolidating the four is a separate job.
- Batches 3 and 4 of broad scan #10 are unimplemented by choice (BS10-04, the tagger's
  artifact-count hole — `tags_for` misses 112 of 150 artifact-count cards, which is the
  measured root cause of BS10-05's median-407 ranking; and BS10-01 / BS10-02, the
  interaction taxonomy holes — exchange/gain control 79 of 84 missed (94%), tap+stun 33 of
  34 missed (97%) against bounce's 1 of 31). BS10-04 is the one that would move the number
  BS10-05 only discloses.
- `_UNPRICED_DISCLOSE_FLOOR` is calibrated from today's 43-deck population; it carries the
  `TIER_FLOOR_REQ` hazard — re-derive if that distribution moves. It is not registered in
  `check_docs.figure_drift`.

DOCUMENTATION UPDATES NEEDED:
- DONE in this change: K-13 rewritten to name `pool.py --regex '<shape>'` as the tool for
  effect-shape search (it previously stated the rule with no implementation), compressed to
  stay inside `check_docs.py`'s 15-line-per-bullet cap.
- NOT done, and worth a `/sync-docs` pass: G-60 (the curve-distortion anchor) does not
  mention that the ◊ discount family is unpriced by `effective_avg_mv` — BS10-07's
  disclosure now says so at two surfaces while the gotcha does not. G-02/G-43/G-58 do not
  mention BS10-08's back-half flag. G-38/G-22 do not mention the ranking-window footer or
  the median-407 measurement, which is the most decision-relevant number this batch
  produced. None of these is a contradiction — each is a gotcha that has not caught up.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
