---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- P1 | `wishlist._land_value`'s `multi` saturates at two colours, so a source fixing all
  three of a three-colour deck's colours scored identically to a two-colour dual and
  could never rise in `suggest --lands`.
- P2 | `deck._TAPLAND_COND_RE` requires the conditional cue AFTER "enters tapped", so all
  ten Standard shocklands were reported as UNCONDITIONAL taplands.

Files modified: scripts/wishlist.py, scripts/deck.py, tests/test_wishlist.py,
tests/test_deck.py, .cycle/blocks/2026-09-04-deck-57-tune-findings.md (new)

CHANGES:
P1 | scripts/wishlist.py | Added `_LAND_BREADTH_PER_COLOR` (0.75) / `_LAND_BREADTH_CAP`
     (1.5) and an additive credit in `_land_value` for each of the deck's colours a
     source fixes beyond two. ADDITIVE and one-directional UP by choice: the
     multiplicative alternative (dividing by the deck's colour count) would have LOWERED
     every two-colour dual in every three-colour deck, re-ranking the roster to fix an
     ordering at the top. Nothing below three colours moves, so no existing
     recommendation is withdrawn.
P2 | scripts/deck.py | `_TAPLAND_COND_RE` gains a `you may pay \d+ life … enters tapped`
     alternative (bounded, so it cannot cross an unrelated paragraph). Verified against
     real text: Hallowed Fountain and Multiversal Passage now read conditional; Mystic
     Monastery and Temple of Epiphany still read unconditional.
P2 | scripts/deck.py | `suggest_lands`' `cond_tapped` was a SECOND, narrower
     implementation of the same question in the same file (`tapped and "unless" in low`),
     which missed every shockland. Routed through `_TAPLAND_COND_RE` so the two surfaces
     cannot disagree — fixing the classifier alone would have left the sibling wrong.
P1/P2 | tests/ | `TestLandBreadthAboveTwo` (4 tests) and
     `test_a_shockland_is_conditional_not_unconditional`, plus two shockland fixtures in
     `TestTaplandProfile.DATA`.

TEST RESULTS: passed. Full pytest suite exit 0; `check_all.py` "All invariants hold ✓";
`check_rankings` OK; `check_suggest` OK; `check_patterns` green (both tapland regexes are
registered there and still match real oracle text).

REGRESSION RISKS:
- P1 re-ranks the #1 land pick in 22 of 115 decks (measured; 21 at 0.5, 25 at 1.0 — the
  choice of constant is not what drives it). The flip is fetch-over-untapped-dual, and it
  happens because the pre-existing gap was only 0.2 (untapped dual 11.7 vs fetch 11.5 in
  deck 8) — fetches already carried a +1.3 synergy-tag advantage that was just barely
  insufficient. ANY positive breadth credit tips it. Judged defensible: in a three-colour
  deck a basic fetch genuinely is the better FIXER, which is the axis this model scores,
  and the tempo cost is reported separately by the `·tapped` marker and by
  `consistency`'s tapland line — which P2 has just made trustworthy. Reversible via one
  constant.
- The top of a three-colour deck's list is now an 8-way tie at 12.3 among seven basic
  fetches plus Demolition Field. Judged HONEST rather than saturated: those cards have
  the same effect, and the `Have` column (×2 owned vs craft) does the disambiguating.
  Worth re-checking if a tiebreak is ever added.
- `_land_value` has a second consumer, `wishlist.py:1019` (the `--rank` land path, G-19).
  Same direction of change; no interface, return type or range changed (still 0–10, still
  clamped by `min(10.0, base)`).

INVARIANTS AT RISK: None. No CSV writer, schema, deck file or derived artefact was
touched; both changes are read-side scoring/reporting. INV-01…04 unaffected — `check_all`
confirms.

NET SCORE: 2 production fixes − 0 new failure modes = 2
  P1: would it have fired this month? YES — it did, on deck 57 this session.
  P2: YES — it mis-reported deck 57's tempo through six tuning passes.
  New failure modes: none introduced. The 22-deck re-rank is a deliberate, measured
  behaviour change, not a defect, and it is pinned by tests in both directions.

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push. The dashboard is rebuilt and published
by `.github/workflows/pages.yml` on push to `main`; this branch does not touch it.

FOLLOW-ON ITEMS:
- `_land_value`'s `match` term penalises an ANY-COLOUR land for producing colours the
  deck does not use: "{T}: Add one mana of any color" scores 8.4 in a three-colour deck,
  BELOW a basic fetch's 8.8, because match = 3/5. Producing more colours than you need is
  not a drawback. Pre-existing, out of scope for P1, and the fix is not obvious (the same
  `match` term is what correctly devalues a WB dual in mono-W).
- P3 (repeatable-vs-one-shot split on role counts), P4 (existential prose claims about the
  pool) and P5 (`#~` swap-line figures outside the staleness sweep) remain open — see
  `.cycle/blocks/2026-09-04-deck-57-tune-findings.md`.

DOCUMENTATION UPDATES NEEDED:
- G-35 should record that `_land_value` now credits breadth above two colours, and why the
  additive form was chosen over rescaling `multi`.
- G-37 (the `suggest --lands` gotcha) should note the fetch-over-untapped-dual re-rank and
  name `_LAND_BREADTH_PER_COLOR` as the constant to revisit.
- The tapland residual described under G-35/G-37 ("`consistency` miscounts a shockland")
  is now CLOSED and the deck-57 flex notes that caveat it three times are stale.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
