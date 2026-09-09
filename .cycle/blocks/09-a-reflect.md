---CYCLE SUMMARY BLOCK---
Scope: broad | Cycle: 9 / 2026-09-09
Production fixes: 3 — severity: 1 Critical (F1 stale synergies, 105 of 113 decks), 2 Medium (chosen-type overlay mis-ranking; G-66 token residual misreporting deck 58 as 1 vs 17)
New capabilities/features: 1 (the proposed-add gate now runs on swap + suggest + suggest-homes; no recommendation surface checked this at cycle start)
Defensive/structural: 13
New failure modes: 1 — severity: 1 Low (the ✦ best-type count inherits creature_subtypes' all-faces DFC read; bounded, report-only, documented, and measured as the better of two approximations)
Net score: 3 − 1 = 2
Invariant candidates:
  INV-07 | load_card_meta()[name]["synergies"] == card-pool.csv's Synergies cell wherever non-blank | Analysis / model-vs-store seam | Verify: check_agreement._agree_synergy_store (mutation-proven in test_gates_fire.py)
  INV-08 | a _TARGET_GATES pattern matches reminder-STRIPPED text unless its kind is in _TARGET_KEEP_REM; the library-search family must still see a fetch quoted in a reminder | Analysis / gate text corpus | Verify: TestUnmetGateReachesTheRecommenders (Bargain silent, Hobbit Hole's rider still 0)
  INV-09 | every calibrated bounded term spans its range on the live roster — not all decks below the floor, <30% pinning the cap | Analysis / overlay calibrations | Verify: TestChosenTypePayoff::test_the_term_spans_its_range_on_the_LIVE_roster. NOT enforced for doubler/cost_scale — that is the gap
  INV-10 | a CLAUDE.md figure cited as a rule's evidence and mechanically derivable is registered in figure_drift | Documentation Currency | Verify: check_docs.figure_drift — partial by construction (11 of ~1,100 claims, hand-kept, misses invisible)
  INV-11 | a primitive reaching a new caller is re-measured AT that caller before the wiring ships | Analysis / G-40 seam | Verify: NONE — process rule, not machine-checkable. The cycle's central lesson and the one with no gate
Most structurally significant change: load_card_meta was library-first for OWNED cards, so the theme model feeding cuts/suggest/centrality was silently wrong on 105 of 113 decks.
Should-have-been-deferred: the swap gate wiring — measured 0 of 805 ledger rows, and everything it was meant to catch was caught a day later at the recommender surfaces, where the same primitive proved 85% wrong; doing the recommenders first would have surfaced all three primitive defects before the gate shipped anywhere.
---END CYCLE SUMMARY BLOCK---
