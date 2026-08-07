---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (Batch B — wishlist & recommender honesty):
- BS2-37 | `--budget` showed only 1 of the 4 checks `--rank` runs — the Power-provenance flags (pow?/pow!/pow~) were computed and discarded on the one view that spends wildcards
- BS2-38 | rotation flagging degraded silently: bare `except: pass` disabled the ⚠rot axis, and `_pool_rotation_index`'s `has_released` flag — whose documented purpose is "callers then warn" — was bound to an underscore and discarded
- BS2-39 | the specific-theme confidence was read off the single highest-SCORING deck, so a card whose real specific home scored below a pile of floored generics read `review`/"generic" and `--suggest-targets` pointed at the WRONG deck (5 of 206 live rows)
- BS2-40 | the last two in-pass DFC aliasing sites (`deck.load_card_meta`, with the row-dropping `continue`; `wishlist.load_pool_index`) converted to second-pass `lib.alias_front` and REGISTERED in `check_dfc._ALIASED_LOADERS`
- (grouped) | `is_conditional_power` read a `Mana Cost` key wishlist rows never carry — the `{x}` half of the detector was dead for its whole life (Genesis Wave, named in the block's own comment, unflagged); `_seed_power`'s type reads scanned BOTH faces (back-face Instant suppressed the permanent-value bump; three live seeded cells wrong by −1.0)

Files modified: scripts/wishlist.py, scripts/deck.py, scripts/check_dfc.py,
card-wishlist.csv (8 seed-provenance Power cells re-seeded), tests/test_wishlist.py

CHANGES:
BS2-37 | wishlist.py | cmd_budget prints the pow?/pow!/pow~ marker inline on every pick and alt, plus a trailing "UNTRUSTED Power" block naming the flagged picks with the fix for each shape — mirroring cmd_rank per G-19's "must show every check --rank runs". Latent today (0 flagged cells in live data); the wiring is what the finding was.
BS2-38 | wishlist.py | the rotation-index load WARNs on failure (matching its two sibling loaders' audit-A14 discipline) and WARNs + disables cleanly when the pool lacks the Released column — "⚠rot flags are OFF, not clear", never silence that reads as "nothing is rotating".
BS2-39 | wishlist.py | _rank_scores tracks the best SPECIFIC-theme deck separately; when the top-scoring deck has only generic overlap but a specific home exists, conf is rescued to `ok` (never STRONG — it was not the top score) and the sig carries the specific themes. cmd_suggest_targets proposes the specific deck, labeled "(specific home; generic-top <id>)". Verified live: all five measured rows (Splash Portal → blink, Dubious Delicacy → flash, Aloe Alchemist → Plant/cost-reduction, Rise of the Varmints → cost-reduction, Rooftop Assassin → flash) now read `ok` with their real homes; roster totals moved 11→16 ok, review shrank accordingly. 2 behavioral tests on a synthetic theme model.
BS2-40 | deck.py, wishlist.py, check_dfc.py | both loaders insert real rows only, then `lib.alias_front` as a second pass (the documented contract; load_card_meta's `continue` had made the order-dependence into row loss); both registered in _ALIASED_LOADERS so the behavioral anchor exercises them. check_dfc green; front keys verified to resolve in both.
(grouped) | wishlist.py, card-wishlist.csv | is_conditional_power joins the cost from card-mana.csv (full-pool scope per G-18; cached once, degrades to text-only if absent — the old behavior) — the four live X-spells now flag; _seed_power reads the FRONT face of the type line. The 8 stale `Power Source: seed` cells the fixed models change were re-seeded in the same commit (3 DFC face fixes incl. Decadent Dragon 4.5→5.5; 5 catching up with this session's role-pattern corrections — seeds are machine estimates by contract, hand grades untouched). 4 tests.

TEST RESULTS: 998 passed (992 + 6 new), 0 failed. check_all: "All invariants hold. ✓", zero soft warnings; check_dfc green with the two new registry entries. Scenario 2 walked on the modified surfaces (--rank header/totals, --budget with the new provenance block, --suggest-targets live rescue rows) — PASS. Others N/A.

REGRESSION RISKS:
- BS2-39 moves 5 live rows review→ok and their proposed Target from "<generic>?" to the specific deck — the correction, and `--write` fills only blank Targets so no stored value changes without the flag.
- The re-seeded cells change 8 stored Power numbers (all seed-provenance; the contract says these track the machine).
- alias_front conversion changes which row wins ONLY in the front-name-collision case (0 in today's pool, and the new winner is the correct one by the documented contract).
- is_conditional_power now flags 4 more live cards `pow~`-eligible; all are Power Source: hand today, so cond_power stays suppressed for them (the flag fires only on seed/blank provenance — by design).

INVARIANTS AT RISK: None. The wishlist write went through write_wishlist (atomic + .bak); INV-01..04 untouched; check_all green.

NET SCORE: 6 − 0 = +6
(BS2-39 was mislabeling live rows and mispointing targets; BS2-38's silence and BS2-37's missing markers fire exactly when the data degrades — the honest-reporting half of G-19/G-30; BS2-40 and the power-model fixes were latent-to-live with three wrong stored numbers.)

OPERATOR ACTIONS / DEPLOY:
None
Deploy: commit/push is the deploy; the dashboard's wishlist tiers pick up the corrected _rank_scores on the next pages.yml rebuild (merge to main).

FOLLOW-ON ITEMS:
- Batches C–H from the priority report, unchanged (Batch C — gate hardening — is next in order).
- BS2-07's header-consumer sweep, still the named leftover from Batch A.

DOCUMENTATION UPDATES NEEDED:
- README wishlist section: one line that --budget now prints the same provenance flags as --rank (fits the next /sync-docs).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
