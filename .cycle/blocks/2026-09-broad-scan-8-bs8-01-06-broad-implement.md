---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS8-01 Any-colour lands counted as ZERO colour sources (identity-only) in all three source counts
- BS8-02 `suggest --lands` / `wishlist._land_value` blind to any-colour lands and basic fetches
- BS8-03 Match-ingest watermark advanced by hand-logged (`manual-`) rows → `--since-last` dropped un-ingested log lines
- BS8-04 60-card `#: format: Brawl` legality/recommendations keyed to Scryfall's `brawl` (Historic Brawl)
- BS8-05 `tier --to` / `redundancy` fillers gated castability on colour identity, not printed cost (G-58 holdouts)
- BS8-06 Tier floor saturated (A for 104/117 decks); thresholds re-derived, one table, roster-spread soft warning
Files modified: scripts/lib.py, scripts/deck.py, scripts/wishlist.py, scripts/parse_matches.py, scripts/check_all.py, scripts/check_tier.py, scripts/check_patterns.py, tests/test_lib.py, tests/test_deck.py, tests/test_parse_matches.py, CLAUDE.md, docs/gotchas.md, dashboard.html (rebuilt), decks/20-honor-among-thieves/20b-abzan-toughness-ramp.txt, decks/40-paradox-drive/40a-paradoxponential.txt, decks/68-frog-sage/68b-warren.txt, decks/78-team-avatar/deck.txt (prose figures re-grounded)

CHANGES:
BS8-01 | scripts/lib.py, scripts/deck.py | New `lib.land_production(text, colors)` reads a land's production from oracle text (free / restricted "spend only" / conditional extra-mana-cost / any-colour / basic-fetch; reminder text stripped; per-line cost and rider). New `deck.deck_source_profile` is THE colour-source count (basics by name; free + extra-cost production counted; fetch counted per basic colour present; spend-only listed, not counted) returning (sources, nlands, total, notes); `_deck_source_counts` and `deck_color_sources` delegate to it; `cmd_mana`'s inline copy removed; `mana` and `consistency` print `format_source_notes` (what the count is made of). Deck 21a: B 5 → 12. 29 roster decks' counts changed (one DOWN: deck 34's Lilypad Village is spend-only). Registered the four new regexes with `check_patterns` (raw corpus form; `_EXTRA_MANA_COST_RE` excluded with a reason).
BS8-02 | scripts/deck.py (suggest_lands), scripts/wishlist.py (_land_value) | Candidate production via `land_production` (any-colour → all five; fetch → the deck's colours; restricted/extra-cost admitted and discounted); `suggest_lands`' own source loop replaced by `deck_color_sources`; `_land_value` treats fetch as never-untapped and extra-cost any-colour like restricted (half premium). Deck 17 `--lands` now lists Branch of Vitu-Ghazi / Forgotten Monument at the top.
BS8-03 | scripts/parse_matches.py, tests/test_parse_matches.py | `MANUAL_ID_PREFIX` + `is_manual_id`; `ingest_watermark` skips hand rows by prefix (the blank-id guard never matched a real row); `parse_manual` stamps through the constant; fixture now uses the writer's real id shape plus a test pinning the fixture to the writer.
BS8-04 | scripts/deck.py | `_POOL_FORMAT_KEY` + `pool_format_key(fmt)` (`brawl`→`standard`, `historic brawl`→`brawl`, untracked→""); applied in `legality_report`, `brawl_readiness`, `suggest_scored`, `suggest_lands`, `suggest_mana`, `suggest_interaction`, `_needs_fmt`, `cmd_suggest`, `screen`, `suggest-homes`, and the three fillers. Manamorphose now fails `legal` in 3-brawl.
BS8-05 | scripts/deck.py | `_filler_castable(cost, ident, declared)` → `_candidate_castability` on the printed cost (identity only when no cost is on file); used by `owned_role_fillers`, `craft_role_fillers`, `functional_theme_options`. 52a's owned interaction fillers now include Bullseye (108 rows).
BS8-06 | scripts/deck.py, scripts/check_all.py, scripts/check_tier.py, CLAUDE.md | `tier_band` reads `TIER_FLOOR_REQ` (was duplicated literals); table re-derived from the roster distribution: A (7, 11), B (4, 7), C (0, 2). Floor spread 104 A / 13 B → 64 A / 43 B / 8 C, zero ≥2-band mismatches, 34 claimed-below-floor nudge candidates (prose suppression applies). New `tier_floor_spread` + `TIER_SPREAD_MAX_SHARE` (0.85) with a `check_all` soft warning when one band holds >85% of the roster. `check_tier._pure_floor` reads the same table (it carried its own literals). Rubric numbers in CLAUDE.md updated with the reasoning.

TEST RESULTS: passed — full pytest suite green with PYTEST_NO_SKIPS=1 (two runs; the first surfaced three failures all caused by this session and fixed: unregistered lib regexes in check_patterns, two CLAUDE.md bullets over the 15-line cap, and the roster figure sweep catching four prose figures computed under the old count — re-grounded in the deck files). `check_all`: all invariants hold, soft warnings = the expected G-75 dead-tutor sweep only after `make dashboard`.

REGRESSION RISKS:
- Source counts now CREDIT an extra-cost any-colour land ("{1}, {T}: Add one mana of any color") as a full source; on-curve castability for that colour is optimistic by one turn for such lands. Labelled in `mana`/`consistency` output so a reader can discount; the previous behaviour (zero) was the larger error.
- Spend-only lands (Village cycle, Castle Doom) are now NOT counted where identity used to count them: deck 34 lost one U source, 68b one W. Correct, but a prose figure that quoted the identity count goes stale (the audit caught all four on the roster; none remain).
- `deck_color_sources` feeds the rationale audit's `sources_*` figures; future prose must quote the text-derived count.
- `TIER_FLOOR_REQ` change re-grades the floor for ~half the roster: `tier --to A` now shows a real gap for 43 decks that used to read "already meets"; the under-grade nudge fires on claimed-B decks whose prose does not argue the cap. Dashboard tier-floor pills change accordingly (rebuilt).
- Any external caller of `_deck_source_counts` keeps its 3-tuple; `deck_color_sources` keeps its signature (`meta` is now a fallback only).
- `pool_format_key` returns "" for untracked formats; every site previously tested `fmt in POOL_FORMATS`, so behaviour is unchanged for Standard/Alchemy/etc.

INVARIANTS AT RISK: None — INV-01..03 untouched (no CSV writes); INV-04 verified (`check_all` green after the four prose-only deck edits).

NET SCORE: 5 − 1 = 4
(BS8-01 YES, BS8-02 YES, BS8-05 YES, BS8-06 YES fire this month; BS8-03 NO (no `--add` rows exist yet), BS8-04 NO (latent: no Historic-only card in a Brawl deck today) — counted 4 production + 1 for BS8-04's recommender side which was live (2,238 illegal picks); new failure mode: the extra-cost source over-credit, documented.)

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — the dashboard is rebuilt and published by `.github/workflows/pages.yml` on push to `main` (committed `dashboard.html` refreshed with `make dashboard` here).

FOLLOW-ON ITEMS:
- The old "7 unconditional any-colour lands in 21a" figure from the scan was wrong: six are extra-cost; the counting policy for extra-cost lands is the judgment call to revisit if `consistency` reads optimistic in play.
- `check_agreement` has no colour-source pair; with one implementation it would be tautological — the pair to add is `cmd_mana`'s printed line vs `deck_source_profile` (output-level), if wanted.
- Stage 2 R-14 (`classify_roles` does not strip reminder text) and BS8-27 (blink as removal) move the interaction axis and therefore the floor; re-run `tier_floor_spread` after those land.
- BS8-24: `test_cli.py` pins deck 43's tier gap to live data; it survived this change but remains a pin on roster state.
- `Historic Brawl` decks now get a legality check against Scryfall's `brawl`; none exist on the roster today.

DOCUMENTATION UPDATES NEEDED:
- README: `deck.py mana`/`consistency` now print the source composition lines; `suggest --lands` admits any-colour and fetch lands; tier rubric numbers (README's copy, if any); `pool_format_key` for Brawl.
- docs/gotchas.md: G-35/G-36 long form for BS8-01/02 and the extra-cost counting policy; G-08 long form for the pool-key mapping; the tiering section for the re-derived thresholds and `tier_floor_spread` (CLAUDE.md carries the rule; G-57/G-58 long forms were added here).
- docs/systems-map.md / cycle-config C-01: `check_all` gained the tier-floor-spread soft sweep.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
