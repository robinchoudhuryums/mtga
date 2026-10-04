---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS11-06 — rotation views compared the raw `#: format:` string: all four 60-card Brawl decks fell out of the roster rotation view, `Standard Brawl` read "0 rotating", and the raw `brawl` was used as a pool key (the G-08 inversion)
- BS11-13 — `suggest --lands --format X` replaced the deck's construction format, offering a singleton deck second copies
- BS11-14 — `--any-format` set the format to "", and `format_rotates("")` is True → ⚠rot on a non-rotating Historic Brawl deck in --lands/--ramp/--interaction/--needs
- BS11-15 — only the needs model scaled for 100-card decks; `cuts`' short-axis note, `fit_strength`'s role-gap KEY test, `audit`'s thin check and `mana`'s pip check did not
- BS11-17 — `lib.land_production` read "commander's color identity" (Command Tower, Arcane Signet) as all five colours
- BS11-18 — an unplaceable commander silently dropped every recommender's colour lock; `resolve --format <unknown>` skipped legality without a word
- BS11-40 — `pool.py --legal` bypassed `pool_format_key`: "historic brawl" → 0, a typo → silent 0, `brawl` silently meant Historic Brawl

Files modified: scripts/deck.py, scripts/lib.py, scripts/pool.py, scripts/build_dashboard.py, scripts/check_patterns.py, tests/test_deck_models.py, tests/test_query_pool.py, dashboard.html (rebuilt)

CHANGES:
BS11-06 | deck.py | `rotation_sweep` selects decks by POOL KEY (`pool_format_key(header or "standard")`), and `_deck_atrisk` tests legality against the pool key; `deck_rotation` keeps `fmt` a normalised format NAME (callers pass it to `format_rotates`) and hands the key to `_deck_atrisk`; `_deck_format_class` normalises. Roster view 109 → 113 decks (only the non-rotating Historic Brawl deck is out).
BS11-13 | deck.py | `suggest_lands`' copy limit reads the deck's own `#: format:`; `--format` only picks the legality pool.
BS11-14 | deck.py | the ⚠rot flag in `suggest_lands`, `suggest_mana` and `suggest_interaction` falls back to the deck's own format when the filter format is "" (--any-format). 78-historic-brawl: 0 rot flags on all four surfaces.
BS11-15 | deck.py | `deck_floor_scale(meta, cards)`; `fit_strength(scale=)` (its three callers pass it), `cuts`' interaction warning and short-axis note (int 5 / CA 3 / early 18), `audit`'s thin check (was a hand-written `5 if min_size >= 100 else 3`), and `mana`'s 9/4-source pip check all go through `_scale_count`. A no-op at 60 cards (scale 1.0).
BS11-17 | lib.py, deck.py, build_dashboard.py | `land_production(commander=)`: a "commander's color identity" clause adds the commander's colours (empty set = no commander = nothing; None = unknown = the old all-five). `deck_commander_colors(deck_meta)`; `deck_source_profile(deck_meta=)` and `uncounted_mana_sources(deck_meta=)`, passed by `mana`, `consistency` and the dashboard. `_COMMANDER_IDENTITY_RE` registered in check_patterns. Deck 78: Command Tower is G/W/U only (the residual B 1 / R 1 is Starting Town, a real any-colour land).
BS11-18 | deck.py | `commander_identity_lock` warns once per unplaceable commander that the lock is OFF; `resolve --format <untracked>` warns that legality was NOT checked.
BS11-40 | pool.py | `--legal` resolves through `deck.pool_format_key` (stored as `args._legal_key`), refuses an unknown format (exit 2, lists the formats), and notes when the repo name maps to a different pool key (`brawl` → `standard`, `historic brawl` → `brawl`).

TEST RESULTS: passed — full pytest suite green; check_all OK (no new soft warning); check_patterns 376 live; 8 new tests (TestScan11Batch6FormatDrift, the pool --legal refusal); one old pool fixture updated (it encoded `--legal brawl` = Historic Brawl).
ROSTER DIFF (114 decks): tier floors 0, cuts top-3 0, central themes 0.
REGRESSION RISKS: (1) `pool.py --legal brawl` now means 60-card Standard Brawl (the repo's convention) — anyone who used it for Historic Brawl gets a one-line notice and must type `historic brawl`. (2) `deck_color_sources` (the path `pip_depth_warning` and the `suggest` recommenders read) still takes no deck header, so those surfaces read Command Tower as five colours — the fix reached `mana`, `consistency` and the dashboard only. (3) A non-commander deck that somehow runs Command Tower now reads it as producing nothing, which is the rules-correct answer.
INVARIANTS AT RISK: None.
NET SCORE: 7 − 0 = 7

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — pages.yml rebuilds the dashboard on push to main (committed copy rebuilt).

FOLLOW-ON ITEMS:
- `deck_color_sources` / `pip_depth_warning` / `suggest --lands`' `_land_value` do not see the commander lock (residual of BS11-17).
- `consistency`'s splash line lists colours the deck has sources for but no DEMAND for (deck 78: B 1, R 1 from Starting Town).
- `suggest_scored` (plain `suggest`) still suppresses ⚠rot entirely under --any-format rather than following the deck's format — consistent before, now the one surface that differs from its siblings.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-08 / G-30: rotation views select by pool key; `--any-format` keeps the deck's rotation; `pool.py --legal` uses `pool_format_key`.
- CLAUDE.md G-35 / G-87: "commander's color identity" production is the commander's colours (`land_production(commander=)`), on mana/consistency/dashboard.
- CLAUDE.md "100-CARD BRAWL DECK IS GRADED PER 60": the scaling now also covers cuts / fit_strength / audit / mana (`deck_floor_scale`).
- README: `pool.py --legal` format names.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
