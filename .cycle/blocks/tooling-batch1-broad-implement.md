---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch 1 of the 2026-10-20 tooling plan (items 2 and 3)
  - Item 2: a blank Legalities cell read as "illegal in every format"; `legal` reported
    Searing Soloist "not legal in historic brawl" while Scryfall had it legal. Blank is now
    UNVERIFIED. Stale rows refreshed by rebuilding the pool.
  - Item 3: `Insult /// Injury` (three slashes) matched no printing and no front-face key.

Files modified: scripts/lib.py, scripts/deck.py, scripts/check_all.py, card-pool.csv,
  card-pool.build, dashboard.html, tests/test_deck.py, tests/test_check_all.py,
  .cycle/blocks/tooling-batch1-broad-implement.md

CHANGES:
Item 3 | scripts/lib.py | new `normalize_card_name()`: collapses `///`/extra spaces to ` // `
Item 3 | scripts/deck.py | `_ms_key`, `_printing_of`, `_resolve_card_name`, and `_do_swap`'s cut/add
  route through the normaliser
Item 2 | scripts/deck.py | `load_legalities` keeps a blank cell as an empty set; `legality_report`
  treats a falsy legality entry as unknown (unverified), not illegal; roster brawl count
  (cmd_brawl) reads a falsy entry as unknown too
Item 2 | card-pool.csv | rebuilt with `build_pool.py --all --refetch`: 31 blank rows now carry
  Brawl legality (all 31 legal on Scryfall); 18 other rows changed upstream (17 oracle text,
  13 synergy tags, 1 release date) — 49 rows total
Item 2 | scripts/check_all.py | new soft `pool_legality_soft`: counts blank Legalities rows and
  names the remedy (silent when zero)

TEST RESULTS: passed — full pytest suite green (exit 0); check_all: all invariants hold;
  make postedit exit 0. New tests: TestBatch1NameAndLegality (5), TestPoolLegalitySoft (2).
REGRESSION RISKS:
  - load_legalities callers (build_dashboard x2, check_agreement x2, deck.py x2) reviewed.
    A first version stored None; check_agreement iterates each value and would have
    crashed, so it was reverted to empty sets before commit. Storage is unchanged.
  - Other suggest/screen/cuts paths read the pool's Legalities directly and still treat a
    blank cell as "not in the format" (excluded). Unchanged in this batch; see follow-on.
INVARIANTS AT RISK: INV-03 (pool still carries its own columns — verified by check_all);
  INV-01b/INV-04 unaffected. None violated.
NET SCORE: production fixes 2 (Searing Soloist false FAIL in `legal`/preflight; `///` lookups) −
  new failure modes 0 = net +2. (A None-storage regression was caught in review, before commit.)

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: N/A — no Deploy Command configured for these subsystems beyond the dashboard
  rebuild that runs on push.

FOLLOW-ON ITEMS:
- suggest / screen / cuts read Legalities directly and exclude a blank row silently (they never
  say "unverified"). Route them through the same unknown rule in a later batch (item 2 scope).
- The pool rebuild changed 18 rows' oracle text and tags from upstream: worth a `tag_synergies`
  sanity pass? (Only the 13 synergy changes are tag-derived; they follow from the new text.)
- Pre-existing soft warnings at check_all (not from this batch): stale #~ figures in decks 24,
  28, 50; dead library searches in 20a, 50a, 69a; 29 off-splash castability lines.

DOCUMENTATION UPDATES NEEDED:
- None for CLAUDE.md. Gotchas text on blank legality may be added to docs/gotchas.md later.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
