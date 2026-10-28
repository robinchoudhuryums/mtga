---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: B4-1 token-vs-nontoken sacrifice flag — MEASURED AND DECLINED (recorded); B4-2 deck 89's
"4× worse" add ranks — MEASURED, premise refuted, raw-rank disclosure added to `feedback`
(plan: deck89-tooling-plan.md Batch 4 — the plan doc is deleted with this batch)
Files modified: scripts/deck.py, tests/test_recommendations.py, docs/gotchas.md (G-42 long form), CLAUDE.md
(session-state line), .cycle/deck89-tooling-plan.md (deleted)

CHANGES:
B4-1 | docs/gotchas.md G-42 | decline recorded with numbers: 66 pool cards carry a nontoken-gated payoff; 17 roster
  decks run one, but in 16 it is ONE incidental card (8 also run token-inclusive payoffs, 8 have no sacrifice
  engine) — only deck 89 has the gate as its always-on engine (3 gated payoffs incl. the commander). Over 129
  Historic-Brawl-legal token-only sacrificers, `suggest-homes` gave 20 KEY verdicts in those 17 decks; 19 are KEY for
  a Food/Treasure/tokens theme unrelated to the gated card, 1 (Peregrin Took, deck 89) is the targeted case — ~5%
  precision. Same verdict as G-42's 2026-09-09 decline: whether a sacrifice counts is the deck's PLAN. No code built.
B4-1 (finding) | — | the motivating read was itself wrong: of the three cards excluded from deck 89's pile as
  "token-only", Izoni, Thousand-Eyed ("Sacrifice another creature") and Zopandrel ("Sacrifice two other creatures")
  are outlets that sacrifice NONTOKEN creatures and DO trigger Szarel; only Slimefoot and Squee was right.
B4-2 | scripts/deck.py `add_rank_stats` + `_median_add_pct` + `cmd_feedback` | a `median_pct` key (median of Add Rank /
  Add Of over rows carrying both) and a feedback line printing it beside the raw median. Measured over 1,656 ranked
  ledger rows: deck 89 median rank 1678 of a median 8,146 candidates = 0.206; roster median rank 433 of 1,972 = 0.208
  — the SAME. Raw rank tracks candidate-pool size (r = 0.585 over 79 decks with n ≥ 8); the hypothesis that many
  generic central themes dilute fit is refuted (r = 0.136 against a ±0.225 noise band). Existing keys unchanged, so
  check_docs' G-22 figure gate is untouched.
B4 | CLAUDE.md, .cycle/ | session-state line: the plan doc is completed and deleted; its record is the four blocks.

TEST RESULTS: passed — pytest 2211 passed (1 new: test_median_pct_normalises_by_the_candidate_pool); check_all "All
  invariants hold"; check_docs OK.
REGRESSION RISKS: `add_rank_stats` gained a key — every consumer reads keys by name (feedback, check_docs), none
  iterates the dict. The ledger stays report-only (test_recommendations' scoring-function ban is untouched; the new
  helper is called only from `add_rank_stats`).
INVARIANTS AT RISK: None.
NET SCORE: 1 − 0 = 1  (B4-2's raw-rank misread fired in THIS session's planning; B4-1 is a DEFENSIVE measured
  decline — it ships nothing, and its value is the recorded numbers plus the overturned Izoni/Zopandrel read)

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: N/A — no Presentation file changed

FOLLOW-ON ITEMS:
- decks/89-genesis-cycle/deck.txt `#: notes:` still says Izoni and Zopandrel "were left out because their sacrifices
  are of TOKENS" — false for both (they are nontoken-capable outlets). Owner's call whether to reconsider them; the
  note needs correcting either way.
- G-22 in CLAUDE.md cites the RAW median rank (420); the percentile is the cross-deck-comparable figure.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-42: one clause pointing at the 2026-10-23 decline.
- CLAUDE.md G-22: `feedback` now prints the percentile; raw rank tracks pool size.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
