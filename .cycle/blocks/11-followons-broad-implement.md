---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: the open follow-ons in .cycle/STATE.md (2026-10-06/07)
- FO-1 suggest-homes KEY-saturation note blamed theme overlap for overlay (doubler / chosen-type) KEYs
- FO-2 consistency's NONLAND disclosure was silent on Vivid (Bloom Tender) and creature-granted mana (Enduring Vitality); three any-colour spellings read as nothing
- FO-3 rationale audit: bare `replace` cue hid stale card citations (deck 42a shape)
- FO-4 rationale audit: comparison-cue window silenced figures inside an explicit `Measured:` / `Live vector:` listing
- FO-5 G-87 recommender half: suggest --lands / _land_value scored a Verge's gated colour as full fixing
- FO-6 tapland_kind's type gate read basics only while G-87's source gate read typed nonbasics too
- FO-7 no surface computed P(tapland in the first three land drops)
- FO-8 sweep for the generalised G-02 shape (a loader's raw value recomputed beside its normalised one)
- FO-9 re-measure unmet_gate at `redundancy` — found the MV-cap gate reading removal as a reanimation gate
- FO-10 a paste of an OLDER Arena copy moved the `#: arena:` header back to it
- FO-11 tier_floor_spread walked the roster twice per check_all
Found already closed (pruned from STATE): structural_overlay_hit power restriction (BS11-16), doubler_axis gap 2 and deck_needs (2026-10-01).
Re-measured, nothing to build: BS10-01 Threaten residual (0 live), wishlist checklands (0 rows).
Not code (left open): Suggested Why column (owner's call), Bo3 play-by-play (needs a real log), browser scenarios, and five standing notes.

Files modified: scripts/deck.py, scripts/lib.py, scripts/wishlist.py, scripts/parse_matches.py, scripts/check_patterns.py, scripts/check_docs.py, tests/test_deck.py, tests/test_deck_models.py, tests/test_lib.py, tests/test_parse_matches.py, tests/test_wishlist.py, decks/24-eternal-flame/deck.txt, decks/78-team-avatar/deck.txt, CLAUDE.md, docs/gotchas.md, dashboard.html, .cycle/STATE.md

CHANGES:
FO-1 | deck.py | suggest-homes records which branch minted each KEY (theme / fixer / doubler (axis) / cost-scale / chosen-type); the saturation note attributes them and, when overlays mint the majority, explains a DENSITY verdict instead of blaming the tags.
FO-2 | lib.py, deck.py, check_patterns.py | `_ANY_COLOR_RE` reads "any combination of colors" / "different colors" / "a chosen color"; new `_CHOOSE_THEN_THAT_COLOR_RE` (per-activation any-colour) and `_BOARD_COLOR_RE` -> new `board` bucket, never `free`. Plaza of Heroes / Mox Amber / The Grey Havens move OUT of `free` (their colour depends on legends you control). `uncounted_mana_sources` labels `board` and `granted` (to creatures; land/Treasure/Cave/artifact grants stay silent) and drops ENTERS-triggered one-shots. Pool: 35 cards gained a reading. Roster: disclosure 79 -> 80 decks; 9 decks' source counts rose via Baxter Building / Three Tree City under the existing `conditional` convention; 0 tier floors.
FO-3 | deck.py | `_HISTORY_CUES`: `replac\w*` -> `replac(?:e[sd]|ing)`. Roster: 0 claims changed.
FO-4 | deck.py, check_patterns.py | `_figure_is_history` skips only the comparison check for a figure inside a `Measured:`/`Live vector:`/`Live:` listing (same sentence). Roster: 1 new hit, 1 real — deck 24 "21 central themes" vs live 20, fixed.
FO-5 | deck.py, wishlist.py | suggest_lands passes `_land_value` a per-colour `gate_credit` from `gated_source_credit` against the deck's own lands; `_land_value` counts a gated colour fractionally (identical at whole numbers; deckless callers unchanged). Roster: 99/117 decks' land scores moved, 57 #1 picks changed (Verge -> ungated untapped dual on what had been a tie).
FO-6 | deck.py | suggest_lands and tapland_profile pass typed nonbasics' types to tapland_kind. Roster: 0 changes (defensive).
FO-7 | deck.py | `tapped_in_first_drops` + a report-only line under consistency's tapland note.
FO-8 | — | Sweep only: every quantity reader sums per name; remaining `mana_value` calls price a single alt-cost face. No live instance.
FO-9 | deck.py | `_TARGET_GATES` mv gate requires "creature (or X) card(s)" or "creatures you control with" before "mana value N or less". Pool 249 -> 89 matches; roster MV-gate rows 83 -> 47; redundancy gate flags 5 -> 2 (both real).
FO-10 | parse_matches.py | `_arena_header_plan` returns `older` (writes nothing) when the header's GUID played strictly later than the claimant (`_guid_last_played`: paste stamps, else matches.csv).
FO-11 | deck.py, check_docs.py | roster `tier_floor_spread()` memoized on deck-file + table stamps (2.5s -> 0.03s on the second call).

TEST RESULTS: check_all green (make postedit). Full pytest suite green on the final tree (a first run passed every test but tripped the G-88 repo-data guard because this session edited deck 78 mid-run; the re-run with no concurrent writes is clean).
REGRESSION RISKS: (a) FO-2 raises sources in 9 decks by counting a {2}/{4} filter land whose output can be zero (Three Tree City without the chosen type) — the existing Capital City convention, now applied to two more lands. (b) FO-5 re-ranks 57 decks' #1 land pick; intended, but a large visible move. (c) FO-4 trusts the writer's `Measured:` label; a historical listing written in that form would now be audited as live.
INVARIANTS AT RISK: None (INV-01..04 untouched; decks 24/78 prose-only edits; check_all green).
NET SCORE: 7 production fixes (FO-1, 2, 3, 4, 5, 9, 10) − 0 new failure modes = 7

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Presentation — pages.yml rebuilds the dashboard on the next push to main.

FOLLOW-ON ITEMS:
- Typed non-creature card MV gate (G-66 residual): "permanent / instant or sorcery / artifact card with mana value N or less" now reports nothing; the old gate counted creatures.
- Three Tree City / Baxter Building now count as filter sources; whether a tribal-count land deserves the conditional credit is unmeasured.

DOCUMENTATION UPDATES NEEDED:
- Done in this change: CLAUDE.md G-26, G-35, G-66, G-87, C-02 figures; docs/gotchas.md G-26, G-33, G-35, G-36, G-66, G-73, G-87.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
