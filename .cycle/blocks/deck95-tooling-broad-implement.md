---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- 1: `tier --to` was silently skipped on an untiered deck AND on a ≥2-band mismatch (both branches returned before the gap block)
- 2: rationale audit could not see the short form of a comma-less legend title ("Sakashima" for Sakashima of a Thousand Faces, "Emiel" for Emiel the Blessed)
- 3: three unverified (SET) COLLECTOR# lines in 78-historic-brawl; library rows added by today's two ingests checked for the same defect
Files modified: scripts/deck.py, tests/test_cli.py, tests/test_deck.py, decks/78-team-avatar/78-historic-brawl-team-avatar.txt

CHANGES:
1 | scripts/deck.py (cmd_tier), tests/test_cli.py | The claim verdict now HOLDS its exit code in `rc` instead of returning; the untiered note and the mismatch warning print, then `--to` runs, and the function returns `rc` (so `--strict` on a mismatch still exits 1, after the path). New TestTierToReachesEveryVerdict: untiered scratch deck prints "Path to the S floor"; a roster deck flooring ≤B with a scratch `#: tier: S` prints TIER MISMATCH + the path and exits 1 under --strict (deck CHOSEN, not hardcoded, per BS8-24 — the first draft skipped, which CI's PYTEST_NO_SKIPS fails). The roster-wide TestTunePlanOutputContract now also reaches untiered decks and still passes.
2 | scripts/deck.py (_shorthand_index), tests/test_deck.py | A comma-less "Head of/the …" title contributes its single-word head as a shorthand fragment, scoped to legendary CREATURES and PLANESWALKERS on the FRONT face (G-63 — Throne of the Grim Captain is an artifact on the front; reading the whole DFC type line admitted "Throne"). Same ≥4-char floor, ≤3-name epithet cap and in-deck suppression as the comma-head. Roster sweep before/after of `rationale_staleness` across all 130 decks: 0 findings added, 0 lost. Three tests: the comma-less head flags when absent, stays suppressed when in the deck, and legendary-artifact heads (Mask, Throne) stay out of the index.
3 | decks/78-team-avatar/78-historic-brawl-team-avatar.txt | `resolve --fix 78-historic-brawl --apply`: Command Tower (ELD) 333 → (FRC) 22, Deserted Beach (MID) 260 → (FRA) 176, Overgrown Farmland (MID) 265 → (FRA) 185; `resolve --check` now clean. The library was CHECKED, not changed: all 249 rows added by today's two ingests carry a printing the pool holds (0 defects) — the suspected library-side copy of the bad printings did not happen, because those three cards were already owned under pool printings.

TEST RESULTS: check_all OK (all invariants hold, 17 soft). pytest: 1 FAILED, all others passed — tests/test_gates_fire.py::TestAllSevenAreQuietOnAHealthyRepo::test_soft_gates_are_clean, PRE-EXISTING (fails identically with this batch stashed): `check_keywords.check()` now reports six unindexed keywords (ascend, battalion, conjure, constellation, partner, seek) that entered the OWNED library with today's ingest commits 2dee22a/3cee106. Not caused by fixes 1–3; follow-on below. CI is red on the branch until it is resolved.
REGRESSION RISKS: (1) `tier --to` now prints a plan for untiered and mismatched decks where it printed nothing — longer output, same exit codes for every pre-existing path (no --to: unchanged; --strict mismatch: still 1). (2) The shorthand index is memoized and read only by `rationale_staleness` (one caller), and the roster diff is 0, so no live verdict moved; a FUTURE prose citation of a comma-less legend's first name can now flag — the intended behaviour.
INVARIANTS AT RISK: None — INV-04 strengthened for one deck (three printings now known); no library/pool/mana write.
NET SCORE: 3 production fixes (1: fired on deck 95 this session; 2: fired on deck 95's prose this session; 3: live soft warning on every check_all run) − 0 new failure modes = 3

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation: `.github/workflows/pages.yml` rebuilds the dashboard on push to `main` — not touched by this batch (no presentation file changed).

(Not complete in production until blocking operator actions are done AND
the deploy step is confirmed.)

FOLLOW-ON ITEMS:
- **CI red: six unindexed keywords on owned cards** (ascend, battalion, conjure, constellation, partner, seek) fail `test_soft_gates_are_clean` (a hard pytest, soft in check_all — the G-69 soft/hard split). Needs a per-keyword K-01 decision (theme it, or `check_keywords.py --update-baseline` after the decision). Seek is already read by the role classifier as card advantage; partner and conjure are likely baseline candidates.
- Classifier holes from the same session (record, measure before building): conditional/modal card draw (Galadriel's mode, Glorious Sunrise, Elder Gargaroth, Tidus's Cheer, Ajani Unyielding's +2); Ajani, Strength of the Pride's one-sided 0 not a Sweeper; The Legend of Yangchen's chapter-I exile; proliferate scores no role (Huatli's Raptor, Tidus).
- Pack planning has no booster-availability signal (`wildcards --by-set` groups by the deck line's printing; 39% of the remaining Brawl R/M are commander/bonus-sheet printings no pack holds) — today answered by an ad-hoc Scryfall lookup.
- No "mark deck as fully owned" tool: both ingests today hand-built a shortfall export (cross-deck max, bump an existing printing rather than append) — a candidate `reconcile_crafts.py --from-deck`.
- `check_all` now takes 2–5 minutes; worth profiling.
- CLAUDE.md figure drift (roster 129→130, G-22 median 420→492, tier-floor spread) and the Pinnacle Starcage (EOE) 33 wishlist printing.

DOCUMENTATION UPDATES NEEDED:
- G-26 (CLAUDE.md + docs/gotchas.md long form): the shorthand index now also derives the head of a comma-less legendary creature/planeswalker title ("Sakashima", "Emiel"); front-face typed.
- CLAUDE.md "Climbing a tier" / README `tier --to`: works on untiered and mismatched decks (it silently printed nothing on both until 2026-10-31).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
