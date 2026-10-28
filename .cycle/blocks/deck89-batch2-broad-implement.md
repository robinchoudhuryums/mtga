---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: B2-1 typed basic fetches count only the basics they can find; B2-2 consistency
discloses basic fetches >= basics (and the cards that replay lands); B2-3 consistency's basic-rebalance hint
(plan: .cycle/deck89-tooling-plan.md Batch 2)
Files modified: scripts/lib.py, scripts/deck.py, scripts/wishlist.py, scripts/check_patterns.py,
tests/test_deck_models.py, decks/89-genesis-cycle/deck.txt (a notes figure this batch made stale),
dashboard.html (rebuild)

CHANGES:
B2-1 | scripts/lib.py | `land_production` returns `fetch_types`: None for an untyped basic fetch ("a basic land
  card"), else the WUBRG letters of the basic types it names (`_FETCH_TYPES_RE`; any "land" in the list means any
  basic). Pool: 146 untyped, 45 typed, 0 misread.
B2-1 | scripts/deck.py, scripts/wishlist.py | the three consumers — `deck_source_profile`, `suggest_lands`,
  `wishlist._land_value` — credit a typed fetch only with the deck's colours it names. Source-kind label and
  docstring updated.
B2-2 | scripts/deck.py | `fetch_pool_pressure()` + a `consistency` ⓘ line: basic fetches >= basics, naming the
  cards (commander included) that "play lands from your graveyard" (`_LAND_REPLAY_RE`). Fires on 1 of 124 decks
  (89: 11 fetches vs 10 basics, Szarel + Ancient Greenwarden); next closest 69b at 6 vs 8.
B2-3 | scripts/deck.py | `basic_rebalance_hint()` + a `consistency` ⓘ line: for each pair of basic types the deck
  runs (from-colour holding >= 2 basics), move one source and re-price every card through `cast_on_curve_rows`;
  report the best swap whose summed shortfall gain clears `_REBALANCE_MIN_GAIN = 16.0`, with its 3 biggest gains
  and 3 biggest costs. Calibrated: 69 of 124 decks show some gain, nonzero p25 4.6 / p50 8.6 / p75 16.0 / p90 25.3 /
  max 45.8; at p75 (the G-85 rule) it fires on 17 of 124.
B2 | scripts/check_patterns.py | `lib._FETCH_TYPES_RE` and `deck._LAND_REPLAY_RE` registered live-corpus (390 live).
B2 | decks/89-genesis-cycle/deck.txt | the LANDS note's "G 25" annotated: 24 once typed fetches read correctly.

TEST RESULTS: passed — pytest 2205 passed (8 new: TestTypedBasicFetches ×3, TestFetchPoolPressure ×2,
  TestBasicRebalanceHint ×2, plus the lib parse case inside the first); check_all "All invariants hold", soft lines
  unchanged; check_patterns 390 live. `consistency` smoke-run on 89, 86, 45a, 3, 52.
ROSTER DIFF (before/after, all 124 decks): source counts changed in 1 deck (89: G 25 → 24, Maestros Theater);
  `suggest --lands` #1 pick changed in 1 deck (89: Brokers Hideout → Demolition Field). Tier floors: 0 moved (the
  floor reads no sources). Rationale sweep: no new stale figure.
REGRESSION RISKS: (1) the rebalance hint sums shortfall over every card equally, so a key card in the losing colour
  weighs no more than filler — the line prints the costs beside the gains for that reason. (2) It moves a SOURCE, not
  a land TYPE (checklands, Verges, typed fetches are not re-priced) and never proposes a colour with no basic yet —
  both disclosed in the output. (3) Any caller reading `land_production` without `fetch_types` keeps the old
  full credit (consumers use `.get`).
INVARIANTS AT RISK: None (INV-01…04 untouched; the deck-89 edit is a `#: notes:` prose line, INV-04 passes).
NET SCORE: 3 − 0 = 3  (B2-1 fired on deck 89's count and its land recommender this month; B2-2 describes deck 89's
  real situation; B2-3 would have found the Forest-for-Mountain swap that was hand-built on 2026-10-23)

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — dashboard.html rebuilt by `make postedit`; publishes via .github/workflows/pages.yml on the
  next push to main.

FOLLOW-ON ITEMS:
- NONBASIC typed fetches (Misty Rainforest / Polluted Delta / Scalding Tarn: "a Forest or Island card") read as NO
  source at all — `_FETCH_BASIC_RE` requires "basic". Their real reach is the deck's basics AND typed duals of those
  types. Only deck 89 runs them today (3 cards). Separate, measured change.
- `suggest --lands 89`'s new top three (Demolition Field, Promising Vein, Shire Terrace) are {1}-to-sacrifice
  untyped fetches priced as BRG at 8.8 — the existing fetch model; whether a {1}-activation fetch deserves a
  tempo discount is unexamined.
- `pytest -q` doubles pytest.ini's `-q` and suppresses the summary line; use plain `python3 -m pytest` to see counts.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-35 ("a basic fetch counts for each colour the deck runs a basic of") → only the types it names.
- CLAUDE.md G-36 (consistency): the two new ⓘ lines (fetch pressure, basic rebalance).
- CLAUDE.md G-37 (suggest --lands): typed fetches priced on the colours they reach.
- docs/gotchas.md G-35/G-36 long forms: the deck-89 incident and the rebalance calibration.
- README consistency section, if it enumerates the disclosures.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
