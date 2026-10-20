---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Brawl tooling plan Batch 6. Profile `consistency`, `swap --apply` and
`make postedit`. Measurement only: no code changed. The deliverable is this profile, and any
speed-up is a separate follow-up batch.
Files modified: .cycle/blocks/tooling-batch6-broad-implement.md, .cycle/STATE.md (no code, no data)

CHANGES:
Batch 6 | (none) | All runs pointed at scratch copies or used `--out`.
  `git status` was clean before and after every run.

WALL-CLOCK (2026-10-20, 121 decks, pool about 16k rows):

  | Command | Time |
  |---|---|
  | consistency 85 / 86 | 0.5s / 0.6s (not a problem) |
  | swap dry run | 0.8s |
  | tier 85 | 0.9s |
  | check_roles --all | 1.3s |
  | swap --apply (scratch DECKS_DIR + RECS_CSV) | 6.9s |
  | check_all | 77.4s |
  | build_dashboard --out <scratch> | 227s (414s under cProfile) |

The reported ">120s per swap" is not `swap`. It is the tail around it:

  | Step | Time |
  |---|---|
  | preflight (runs a full check_all) | ~80s |
  | make postedit (dashboard + check_all + check_roles) | ~305s |

A three-swap apply therefore costs about 21s of swapping and about 6.5 minutes of verification.

PROFILE 1 — swap --apply (6.9s):
  - `recommendation_row` takes 5.8s. Of that, `suggest_scored` takes 4.9s, re-ranking the
    whole pool to record where the add would have ranked.
  - `classify_roles` takes 3.86s over 16,653 calls, all regex search.
  - The edit itself and the INV-04 re-parse take under 1s.

PROFILE 2 — check_all (233s profiled, 77s wall):
  - `rationale_staleness` takes 142.8s over 121 decks.
    - The cost is the genexpr at deck.py:15206, `any(other.startswith(disp + " ") for other
      in in_deck)`: 188M generator steps and 184M `str.startswith` calls.
    - That shorthand guard runs for every pool name in every deck, before the much
      cheaper word-bounded text search that rejects almost all of them.
    - Two fixes are possible: reorder so the text search runs first, or precompute
      a set of word-prefixes of `in_deck` and do an O(1) lookup.
    - Either fix gives identical output, because both are pure filters.
  - `check_agreement.check` takes 41s, including:

    | Function | Time |
    |---|---|
    | `_agree_weakest_cut` | 14s |
    | `_agree_role_fillers` | 13.5s |
    | `craft_role_fillers` | 7.5s |

  - `classify_roles` takes 33.4s over 128,256 calls.
  - `role_tally` takes 29s.
  - `deck_quality_vector` takes 23s over 548 calls (about 4.5 per deck, recomputed per gate).
  - Other costs:

    | Function | Time |
    |---|---|
    | `role_coverage_flags` | 17s |
    | `figure_drift` | 13.5s |
    | `_find_word_bounded` | 7s |
    | `check_dfc` | 6.2s |
    | `note_figure_staleness` | 6s |
    | `parse_deck_file` (7,190 calls) | 5.9s |

PROFILE 3 — build_dashboard (414s profiled):
  - `craft_rows` takes 264s, all of it in `suggest_scored`, called once per deck (121 calls).
    - Inside that, `classify_roles` takes 151s over 620,483 calls. The pool is about 16k
      cards, so each card's text is classified about 39 times. Regex search alone accounts
      for 109s.
    - `_power_seed` → `wishlist._seed_power` takes 73s over 283k calls. This is also per
      card and per deck, and the result does not depend on the deck.
    - `_candidate_castability` takes 21s over 2.0M calls.
  - `deck_detail`, via `_capture` of `cmd_*`, takes 101s.
    - `cmd_legal` takes 59s. `load_legalities` is not memoized and re-reads card-pool.csv
      122 times, for 45.5s.
    - `cmd_cuts` takes 30s.
    - `cmd_arena` takes 13s.
  - `discover_decks` takes 63s over 611 calls. It is not memoized and re-parses every deck
    file each time: 87k `parse_deck_file` calls, 70s.
    - It is reached through `find_deck` (363 calls) and `roster_decks` (247 calls).
  - `_deck_commit_hashes` / `deck_card_delta_since` spend about 32s in git subprocesses
    (1,061 runs).

FOLLOW-UP FIX CANDIDATES (ranked by seconds saved per byte of risk; none applied):
  1. Memoize `classify_roles` on its text argument. It is a pure function of `text`, so an
     `lru_cache` keyed on the string should work.
     - Saves about 140s on the dashboard, 25–30s on check_all and about 3s on a swap.
     - It returns a mutable set, so the cache must hand back a frozenset or a copy. G-71 is
       exactly this trap: a memoized table mutated by a caller.
  2. Fix the `rationale_staleness` shorthand guard: reorder it or build a prefix set.
     - Saves about 135s profiled, roughly 40–45s wall, on every check_all, preflight and
       postedit.
     - The output must be byte-identical. Pin it with a roster before/after diff of
       `rationale_staleness`.
  3. Memoize `load_legalities` (through `_file_memo`, like the other loaders) and
     `discover_decks`, keyed on the directory listing plus mtimes.
     - Saves about 45s and about 60s on the dashboard.
     - The `discover_decks` cache must invalidate on a deck write within one process,
       because `app.py` is long-lived (G-71).
  4. Hoist the deck-independent work out of `suggest_scored`'s per-deck loop. `_power_seed`
     depends only on the card, so cache it per name.
     - Saves about 70s on the dashboard.
  5. `recommendation_row` re-ranks the whole pool for one lookup. It could score only the
     add, but the rank needs the full ordering, so this is LOW value once (1) lands.
  6. Do not change the order of `make postedit`. G-69's acknowledge-last order is
     load-bearing. Speed comes from (1) to (4), not from skipping steps.

TEST RESULTS: No code changed, so the suite was not re-run for this batch. The SessionStart hook
reported 2173 passed; check_all was OK with 5 soft warnings on the unchanged tree.
REGRESSION RISKS: None, because no code changed.
INVARIANTS AT RISK: None.
NET SCORE: 0 − 0 = 0 (measurement batch: no production fix, no new failure mode).

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — no presentation change.

FOLLOW-ON ITEMS:
- A speed-up batch built from candidates 1 to 4 above. Each needs a byte-identical
  before/after diff of the outputs it touches: check_all soft output, the dashboard's
  `#data` island, and `suggest` rankings.
- `make postedit` rebuilds the full dashboard after every deck edit (227s). A per-deck
  incremental rebuild would be a larger design change and is not proposed here.

DOCUMENTATION UPDATES NEEDED:
None. The timings are recorded here. CLAUDE.md does not cite run times.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
