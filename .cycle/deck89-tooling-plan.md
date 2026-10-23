# Deck-89 tooling holes — batch plan (TEMPORARY working doc)

**Status: IN PROGRESS.** Written 2026-10-23 from the holes the deck 89 (Szarel) build surfaced.
Each batch is one `/broad-implement` run. Delete this file once Batch 4 lands; the record is
`.cycle/blocks/`.

| Batch | State |
|---|---|
| 1 — ingest/CLI correctness (B1-1, B1-2) | DONE 2026-10-23 (block `deck89-batch1-broad-implement.md`; B1-2's `--within` half not applicable — it takes colours) |
| 2 — manabase sources (B2-1..3) | DONE 2026-10-23 (block `deck89-batch2-broad-implement.md`) |
| 3 — role + engine patterns (B3-1..4) | open |
| 4 — measure-first (B4-1, B4-2) | open |

Two corrections were made while scoping: Rhonas the Indomitable is NOT a counters payoff (its
gate is power 4), and #7 is deck-specific — deck 89's chosen adds ranked median 1678 in
`suggest` against a roster median of 420 (Polukranos, Unchained: 382 theme / 128
`--interaction` before the swap).

## Batch 1 — ingest/CLI correctness (no roster score should move)

- **B1-1** `wishlist.py --add` trusts the pasted `(SET) COLLECTOR#`: a hand-typed
  `(THB) 226` was stored for Polukranos, Unchained (real 224). When the name resolves and the
  pair matches no pool printing, store the pool's printing and print the correction; refuse a
  set code no printing carries (the INV-01b shape). Plus a SOFT `check_all` sweep for wishlist
  rows whose set or collector the pool does not hold. Keep CRLF (G-19).
- **B1-2** `pool.py --legal brawl` is the 60-card format (G-08) and the deck 89 pile sweep used
  it by mistake. Print a one-line note when `--legal brawl` is given; with `--within <deck>`
  and no `--legal`, default to that deck's format.

## Batch 2 — manabase sources (one count, every surface: G-35/G-87)

- **B2-1** `lib.land_production` records `fetch: True` with no named types, so a TYPED basic
  fetch (SNC hideouts, Maestros Theater, the Landscapes: "a basic Forest, Plains, or Island")
  is counted for every colour the deck runs a basic of. Deck 89's G read one high via Maestros
  Theater; `suggest --lands 89` ranked Brokers Hideout / Cabaretti Courtyard / Obscura
  Storefront as `Prod BRG` (12.3) above every untapped dual. 9 such cards in 6 roster decks.
  Record `fetch_types`; count the intersection in `deck_source_profile` and `_land_value`.
  Leave NONBASIC typed fetches (Misty Rainforest) alone unless handled deliberately — they reach
  typed duals.
- **B2-2** `consistency` disclosure when basic fetchers outnumber basics (deck 89: 10 basics vs
  11 replayable fetchers). A failed search still sacrifices. Disclosure only.
- **B2-3** Basic-rebalance hint: a colour with many sources per strict-pip card next to one
  with few (deck 89: R 18 sources / 6 cards, G 23 / 47) → "move a basic R → G". No tool proposed
  the Forest-for-Mountain swap. Threshold from the roster distribution (G-07).
- Measure: per-deck source diff, `suggest --lands` #1-pick diff, tier floors (expect 0), the
  rationale sweep; update G-35/G-87.

## Batch 3 — role + engine patterns (K-12 diff, full suite — G-67)

- **B3-1** Extra land drops ("play an additional land", 31 historic-brawl pool cards) → Ramp.
  Azusa and Dryad score no role; Dryad is deck 89's #1 `cuts` candidate.
- **B3-2** Counter replacement (Hardened Scales, Doubling Season, Vorinclex; ~6 pool cards) →
  Payoff / engine.
- **B3-3** Lukka, Bound to Ruin's −4 ("deals X damage divided as you choose among any number of
  target creatures and/or planeswalkers") scores no Removal. Fix the clause, not the window.
  Interaction moves → floors may move.
- **B3-4** `engines` counters payoff cues: "creatures you control with a +1/+1 counter" (47 pool
  cards, Bushmaster's shape) and the counter-replacement effects. Deck 89 reads
  "15 enabler / 1 payoff".
- Measure: roster role diff, tier floors, `cuts` top-3, `engines` verdicts, prose sweep,
  `make postedit MAXNEW=<n>`; update K-12/G-48.

## Batch 4 — measure first, may end as a recorded decline

- **B4-1** Token vs NONTOKEN sacrifice: count decks with a nontoken-gated payoff (Szarel's
  "another nontoken permanent") and how many KEY verdicts there come from token-only sacrifice
  cards (Izoni, Zopandrel, Slimefoot and Squee rated KEY for deck 89). Build a narrow flag only
  if precise; else record the decline with numbers (the G-41/G-42 shape).
- **B4-2** Why deck 89's adds rank ~4× worse than the roster median. Hypothesis: 14 central
  themes, mostly generic, dilute fit. Correlate central-theme count with chosen-add rank over
  `recommendations.csv`. Report; no ranking change without `check_suggest` anchors.
