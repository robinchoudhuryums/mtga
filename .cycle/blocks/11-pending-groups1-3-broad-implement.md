---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- G1a — Builder publish manifest: `render` writes `.manifest.json` (the files the page uses); `publish-plan` lists unused published files as removals.
- G1b — Pruning rule / cap: `publish-plan` reports the board against the 511-file artifact cap (warns at 95%, exits 2 over), naming pile cards settled out of every deck (`prunable_cards`) as the prune candidates.
- G1c — 255 stale Sultai reasons re-read against the live lists: 210 corrected, 45 unchanged; all re-stamped.
- G1d — Builder tests read a frozen fixture deck (`tests/fixtures/builder-glarb.txt`), not live deck 96.
- G2a — Sidisi (KTK) 199y: verified as the Arena-only printing; no change.
- G2b — CLAUDE.md G-85 figures (26 of 67 / 67 decks) and the tier-floor spread (A 86 / B 43 / C 3, top band 65%).
- G2c — `deck.py check` reads castability from local costs, so a hybrid is labelled hybrid, not an off-colour stray.
- G2d — A power-only shrink (Oko's −2/−0) no longer scores Removal (spot).
- G3a — Six role-pattern holes: non-X damage sweeps (Avengers: Under Siege), self-exile one-sided wipes (Ajani, Strength of the Pride's 0), chosen-opposing-permanent exile (Yangchen ch. I), "up to one other target" power damage (Ravenous Tyrannosaurus), coloured-pip cost reduction (Eluge), triggered scaling mana (Cheering Crowd).
- G3b — Proliferate → Payoff / engine.
- G3c — `targets` reads the typed non-creature MV gate ("nonland permanent / artifact card with mana value N or less").
- G3d — `early_drops` excludes {X} spells.
- G3 measured, not built: blank Legalities, changeling named-type payoffs, wildcards --by-set pack availability, reconcile_crafts --from-deck, check_all runtime, Bo3 play-by-play (see FOLLOW-ON).
Files modified: scripts/builder.py, scripts/deck.py, scripts/role_baseline.txt, tests/test_builder.py, tests/test_builder_template.py, tests/test_deck.py, tests/fixtures/builder-glarb.txt (new), builds/sultai/build.json, .cycle/board/index.html, .cycle/board/.manifest.json (new), .cycle/board/.published.json, CLAUDE.md, dashboard.html, decks/{01,10,15,26a,30,33,45a,49,50,52a,53,79,87,88,95} deck files (prose figures only), decks/34-zoologist/deck.txt and decks/95-light-of-valinor/deck.txt (tier rationale, earlier commit), .cycle/STATE.md

CHANGES:
G1a | scripts/builder.py | `write_manifest` (index.html, sprite, art sheets, each card's large image and shipped back face); `site_files` reads only manifest files when one exists (older renders fall back to the layout scan); the published record now drops 5-style stale cache files as removals.
G1b | scripts/builder.py | `ARTIFACT_FILE_CAP = 511`, `PUBLISH_BATCH = 255`, `board_capacity`, `prunable_cards` (pile card, run by no deck, ✗ in every deck); the CLI prints "holds N of 511", warns ≥95%, exits 2 over the cap, and notes a >255-file change needs several publishes. Live board: 511/511, 8 prunable cards.
G1c | builds/sultai/build.json | per-reason minimal substitutions (cut/added cards, Glarb's removed control core — Psychic Corrosion, Proft, Princess Yue, Dictate, Counterspell, Traumatize, Damnation, Doctor Doom — the Thranduil 2026-11-05 package and its owned land stand-ins), each validated to match exactly once, then `set_reason` re-stamps. `builder.py check sultai`: 0 stale reasons.
G1d | tests/test_builder.py, tests/test_builder_template.py | `scratch` and the Node projection test copy the fixture (deck 96 with the premise applied, trimmed to a legal 100).
G2b–d | CLAUDE.md, scripts/deck.py, tests/test_deck.py | (commit 26dbddf) `cmd_check` uses `_castability` with local costs; Removal (spot) shrink patterns require a toughness reduction; TestCheckLintReadsLocalCosts, TestPowerOnlyShrinkIsNotRemoval.
G3a | scripts/deck.py | Sweeper: `damage to each (?:non-?<type> )?creature` and `(destroy|exile) … and each … your opponents control`; Removal: chosen-opposing-permanents exile, `(?:an)?(?:other )?target`; Cost reduction: `{[wubrgc]}\s+(?:(or {1})\s+)?less` (reminder stripping leaves a double space); Ramp: `adds? {C} for each`. Pool: 34 cards gain a role, 0 lose one; roster: interaction +1 in 9 decks, 0 tier floors moved; `cuts` top-3 changed in 1 of 134 deck files.
G3b | scripts/deck.py | `\bproliferate\b` in Payoff / engine beside the replacement multipliers. 70 pool cards, 31 of them roleless before; `cuts` top-3 changed in 1 deck file, no #1 changed; not read by `tier_band`.
G3c | scripts/deck.py | `type_mv` gate in `_TARGET_GATES` with `(?<!or )(?<!and )(?<!aura )` and `(?<!total )` guards; 36 pool cards. Reaches `unmet_gate`: 437 unmet of 4,958 roster probes, every one a true zero (an artifact tutor in a deck with no cheap artifacts); the first draft's 106 false flags from Shadows' Verdict were removed by the `and` guard before shipping.
G3d | scripts/deck.py | front-face cost with `{x}` is not an early drop. 66 decks' early_drops fell, 0 tier floors moved.
Prose | 15 deck files | 16 `#: tier:` / `#: archetype:` / `#~ note:` figures made stale by G3a/G2d/G3d re-grounded (factual corrections, no letters changed).
Tests | tests/test_deck.py, tests/test_builder.py | TestRoleHoles20261105 (positive + negative per hole), TestTypedMvGate, TestXSpellIsNotAnEarlyDrop, three TestPublishPlan cases (manifest removals, prunable rule, CLI cap refusal).

TEST RESULTS: Full suite PASSED — 2397 passed in 205 s (exit 0); check_all OK (all invariants hold); `make postedit` ran (dashboard rebuilt, role baseline pruned 12 stale entries, 0 new). Board republished (v51, index.html) and marked.
REGRESSION RISKS: (1) `early_drops` is lower on 66 decks, so a `quality --json` snapshot taken before this change will show an early-drop "regression" on its next `--vs` — transient, one comparison. (2) The typed MV gate now prints `⚠ gate` on swap previews and `needs` rows for artifact/planeswalker tutors in decks without targets — intended, measured true. (3) `site_files` trusts the manifest: a `render --no-images` keeps the previous manifest, which still names the previous image set (correct, since no images were rewritten). (4) The fixture deck is frozen: if a card in it leaves the pool, builder tests fail rather than drift — the intended trade.
INVARIANTS AT RISK: None — no canonical CSV written; deck edits are `#` prose lines only (INV-04 re-checked by check_all).
NET SCORE: 11 production fixes − 0 new failure modes = 11
(G1a YES: five stale images caused today's 512 refusal. G1b YES: the publish was refused today. G1c YES: 310 stale lines on the board the owner reads. G1d YES: owner edits broke the suite twice. G2b YES: figure drift in a rule loaded every session. G2c YES: 53 hybrids mislabelled. G2d YES: two tier floors were inflated. G3a YES: 9 decks under-counted interaction. G3b YES: 31 roleless proliferate cards ranked as filler in `cuts`. G3c YES: 7 roster cards' gates unread. G3d YES: 66 decks over-read their early game. G2a NO: the printing was already correct.)

OPERATOR ACTIONS / DEPLOY:
- None. | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds the dashboard and Builder pages on the next merge to main.

FOLLOW-ON ITEMS:
- Owner: the Sultai board is at 511/511 files. The prune rule names 8 pile cards settled out of both decks (Chulane, Jyoti, Kogla and Yidaro, Marit Lage's Slumber, Mystic Reflection, Naban, Niv-Mizzet Visionary, Tawnos); removing them frees ~8–10 files. The structural fix is packing large images into sheets (a template refactor of ~8 `imgSrc` call sites); not built.
- Sultai verdict stars: Thranduil 108 / Glarb 129 graded before the list changed, plus 37 Glarb ungraded — a re-grade pass, out of this scope.
- Pre-existing stale `#~ note:` figures: deck 24 sources_R 16→17, deck 28 protection 1→2, deck 50 avg MV 3.31→3.64 / early drops 16→12.
- Measured, not built: blank Legalities — the format filter drops a blank cell silently, but 0 of 16,089 pool rows are blank and `pool_legality_soft` already flags the stale pool that would create them. Changeling named-type payoffs — 34 changelings in the pool, 2 deck files run one (34 ×4, 18 ×1); G-84 records the named half as deliberately unbuilt. `reconcile_crafts --from-deck` — a deck PATH already parses (dry run lists deck 95's 40 adds); an id alias would make reconciling from an aspirational deck easier, which /draft-deck forbids. check_all runtime — 38 s in a fresh process (twice); the 2–5 min figure was not reproduced (the SessionStart hook's suite is ~3.5 min). Bo3 play-by-play — needs a real best-of-three Player.log. Pack availability for `wildcards --by-set` — needs a data source (Scryfall's per-printing `booster` flag via build_pool is the candidate; a pool schema change + refetch).
- Builder tests still copy live deck 75-historic-brawl for the two-deck case (`test_two_decks_get_an_either_pile…`, `add_deck` test) — same exposure as deck 96 had, lower risk (they only need it to parse).

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-89: publish-plan now reports the 511-file cap and the prune candidates; the "republish … page AND its changed images" sentence could mention removals. K-12 / G-67: the 2026-11-05 role holes. G-81: `early_drops` excludes X spells. README Builder section and docs/systems-map.md §5c for the cap.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
