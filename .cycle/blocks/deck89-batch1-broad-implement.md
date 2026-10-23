---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: B1-1 wishlist --add validates the pasted printing + soft check_all sweep;
B1-2 pool.py --legal brawl names the 60-card/100-card distinction (plan: .cycle/deck89-tooling-plan.md Batch 1)
Files modified: scripts/wishlist.py, scripts/check_all.py, scripts/pool.py, tests/test_wishlist.py,
tests/test_query_pool.py

CHANGES:
B1-1 | scripts/wishlist.py | `_corrected_printing` (+ `_held_printings`, `_printing_held`): on a POOL-enriched add, a
  pasted (SET) COLLECTOR# that neither card-pool.csv nor card-library.csv holds for that card is replaced by the
  pool's printing (what `deck.py resolve` emits) and the correction is printed AFTER the write (G-10). Validation
  reuses `deck.known_printings` — the index INV-04's printing check reads — so a deck line and a wishlist row
  cannot disagree. A library-held alternate art is kept; a name-only line stays blank; a card the pool does not
  know is left alone. `printing_issues()` is the read-side sweep.
B1-1 | scripts/check_all.py | new SOFT line "wishlist printing(s): N row(s) name a (SET) COLLECTOR# this repo does
  not hold — <first 3>". Live: 1 row (Pinnacle Starcage (EOE) 33; resolve prints (EOE) 27).
B1-2 | scripts/pool.py | `--legal brawl` (any spelling normalising to `brawl`) now also prints "`brawl` is the
  60-card format — Arena's "Standard Brawl". For a 100-card deck use --legal "historic brawl"." The existing note
  named only the pool KEY ('standard'), and the deck-89 pile sweep ran the wrong format with it on screen.
B1-2 (half NOT APPLICABLE) | — | the plan's "`--within <deck>` defaults --legal to that deck's format" rests on a
  misreading: `--within` takes COLOUR letters (identity subset), not a deck id. Nothing built.

TEST RESULTS: passed — full pytest suite exit 0 (6 new tests: 5 in TestAddValidatesThePrinting, 1 in
  test_query_pool); check_all "All invariants hold", the new soft line fires on the one live row.
REGRESSION RISKS: (1) a re-add of a line carrying the SAME wrong printing as an already-stored stale row now
  dedupes against the CORRECTED key, so it appends a correct row beside the stale one (the new sweep flags the
  stale one). (2) An alternate-art printing the library does not hold is rewritten to the pool's printing —
  harmless for a craft target, and printed. Tests that fake `enrich` with status "scryfall" are unaffected (the
  check runs only on pool-enriched rows).
INVARIANTS AT RISK: None (INV-01/01b/04 untouched; the wishlist is not an invariant file; writes still go through
  write_wishlist, CRLF kept).
NET SCORE: 3 − 1 = 2  (B1-1 add fired 2026-10-23 [Polukranos (THB) 226]; B1-1 sweep fires on a live row;
  B1-2 fired in the deck-89 pile sweep; −1 for regression risk (1), a narrow duplicate-row edge)

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: N/A — no Presentation file changed (dashboard untouched)

FOLLOW-ON ITEMS:
- card-wishlist.csv: Pinnacle Starcage (EOE) 33 — `deck.py resolve` prints (EOE) 27. One-cell data fix, owner's
  call (could be an intended alt art).
- Re-add dedupe against a stale wrong-printing row (regression risk 1) — could match on name when the corrected
  pair differs; not built (narrow).
- `pkill -f <pattern>` from a Bash call matches its own shell (exit 144) — process note, not code.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-19 (wishlist): `--add` now corrects an unheld printing to the pool's; one clause.
- CLAUDE.md G-08: `pool.py --legal brawl` prints the 60-card note.
- CLAUDE.md Cycle Workflow Config Test Command list: a THIRTEENTH soft sweep (wishlist printings).
- docs/cycle-config.md [C-01]: same sweep.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
