---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- A-5 | Burn/reach and multiplier pattern holes — "any OTHER target" / "that much damage to …" reach templatings, and three multiplier shapes (trigger doubler, damage doubler, spell copier) as Payoff / engine
- A-6 | Lock-as-protection and redirect — "opponents can't cast spells" and "change the target of target spell" join Protection / trick (role credit only; the G-25 protection AXIS and `_INTERACTION_ROLES` unchanged)
- F-1 | Deck-level alt-cost GRANTS named — `cheat_cost_grants` (Tannuk's "have warp {2}{R}") printed under the CHEAT-COST block in `stats`
- F-2 | Effective-curve advisory — `effective_avg_mv` (alt costs substituted, quantity-weighted) in `stats`, and in `tier` the aggro clock it WOULD read beside the clock it does; report-only, the floor keeps the printed curve
- F-3 | Type-restricted sink label — `suggest --lands` prints `sink~` for a sink that feeds one creature type (Iron Hills), same tie-break value

Files modified: scripts/deck.py, scripts/check_patterns.py, tests/test_deck.py, tests/test_deck_models.py, scripts/role_baseline.txt (pruned by postedit), .cycle/STATE.md, this block

CHANGES:
A-5 | scripts/deck.py | `_ROLE_PATTERNS["Burn / drain"]`: `any (?:other )?target` in the damage-equal-to pattern, plus `deals x damage to any (other) target` and `deals that much damage to (each opponent|any (other) target|target player)`; `_ROLE_PATTERNS["Payoff / engine"]`: `triggers an additional time`, `deals double that damage`, `double all damage that sources you control`, `copy target (instant|sorcery|creature)…spell`
A-6 | scripts/deck.py | `_ROLE_PATTERNS["Protection / trick"]`: `opponents can't cast spells`, `change the target of target spell`
F-1 | scripts/deck.py | `_ALT_COST_GRANT_RE`, `cheat_cost_grants`; `cmd_stats` prints "⌁ grant: <card> gives <kw> <cost> to <scope>"
F-2 | scripts/deck.py | `effective_avg_mv`; `cmd_stats` prints "effective avg MV X against Y printed"; `cmd_tier` prints "ⓘ effective avg MV … the aggro clock would read N/7 against M/7 — ADVISORY"
F-3 | scripts/deck.py | `_LAND_SINK_TYPED_RE`; `_land_utility` relabels `sink` → `sink~`; legend updated
gate | scripts/check_patterns.py | `_ALT_COST_GRANT_RE` (norm) and `_LAND_SINK_TYPED_RE` (raw — creature types are capitalized) registered; role patterns are registered automatically via `_ROLE_COMPILED_MAP`
tests | tests/test_deck.py | `TestRolePatternHoles20260906` — real text for Self-Destruct, Pain for All, Red Hulk, Delney, Twinflame, Collective Inferno, Sparks, Return the Favor, Abolisher, Voice of Victory; negatives for a fight and a clone; pins `_INTERACTION_ROLES` and that the lock is not on the protection axis
tests | tests/test_deck_models.py | `TestCheatCostGrantsAndEffectiveCurve` (grant named with scope; own-warp is not a grant; quantity-weighted substitution; None without a priced card; neither reaches the vector/floor/clock), `TestTypedSinkLabel`

K-14 MEASUREMENT (before/after snapshot of all 114 roster decks, `k14-before.json` / `k14-after.json` in the session scratchpad):
- Floor bands moved: 0 (A 62 / B 44 / C 8 both sides). interaction: 0 decks changed. card advantage: 0. clock: 0.
- reach: 8 decks changed — 2 (8→9), 9 (8→9), 29 (9→10), 33 (10→11), 56 (12→16), 56a (11→15), 56b (8→11), 58 (7→8). No clock crossed a band edge.
- 22 roster cards left the zero-role baseline (562 → 540); all 13 that the named cards did not account for were read and are true positives: Avatar's Wrath and Kutzil (lock), Bolt Bend and Redirect Lightning (redirect), Callous Sell-Sword and Sawblade Skinripper (reach), Cloud / Katara the Fearless / Mirror Room / Splinter / Starfield Vocalist / Traveling Chocobo (trigger doubler), Kitsa (spell copier).
- `check_roles --tags`: no new tagger-vs-classifier disagreements. `check_patterns`: 332 patterns live.

TEST RESULTS: check_all — all invariants hold (one soft warning: 22 stale baseline entries, cleared by `make postedit`). New tests: 22 pass. Full suite: all passed (exit 0; the dot stream holds no F or E).
REGRESSION RISKS:
- `role_tally` output changes for the 22 cards (stats role counts, `cuts` role credit, `count_conf` remainders). Tier floors are unchanged by measurement; a future aggro deck built on the reach family gains clock credit it previously lacked, which is the intended direction.
- `copy target … spell` is scoped to spell copies; a clone ("enter as a copy of") is pinned NOT to match.
- `opponents can't cast spells` also matches a combat-only lock (Kutzil) — still a lock, accepted.
- `stats`/`tier` gain up to three advisory lines on cheat-cost decks; nothing parses them.
INVARIANTS AT RISK: None — no writer touched; the baseline prune is the documented `--update-baseline` path (G-69 order: it runs LAST in postedit).
NET SCORE: 5 − 0 = 5
  A-5 fired this month: YES (56's reach read 12 for a deck built on Pain for All / Self-Destruct; 56a's Delney offered as a cut). New failure mode: NO (measured, 0 floors).
  A-6 fired this month: YES (Abolisher/Return the Favor on 56's `cuts` weakest list, O45). New failure mode: NO (role credit only; axis and floor pinned).
  F-1 fired this month: YES (56b's curve argued from printed costs in chat). New failure mode: NO.
  F-2 fired this month: YES (56b's floor discussion). New failure mode: NO (report-only, pinned).
  F-3 fired this month: YES (Iron Hills ranked above a scry land on `sink`). New failure mode: NO.

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Data + tooling ship by commit/push; the dashboard is rebuilt by pages.yml on push to main (no template edit).

FOLLOW-ON ITEMS:
- The damage-doubler AXIS in `doubler_support` (so `suggest-homes` promotes Twinflame Tyrant by the deck's damage-source count) is still the deliberately untaken taxonomy item; this batch gives those cards a ROLE, not an axis.
- Haste-gated evasion and attack-alone state gates (pile §5.7 item 5) remain open at n=1–2.
- `effective_avg_mv` prices CARD-level alt costs only; a granted warp is named (F-1) but not substituted, since which cards it reaches is a deck-level question.
- `check_roles` role coverage is now 71% (was 70%); the 540 remaining zero-role cards are the long tail plus the Equipment / tap-down / neutralize taxonomy decision.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-67: add the 2026-09-06 family — "any OTHER target" (3 reach patterns), multipliers as payoffs, lock/redirect as protection-class; the 0-floors / 8-reach / 22-cards measurement.
- CLAUDE.md G-60: the effective-curve advisory and the grant line beside the cheat-cost twin.
- CLAUDE.md G-37: `sink~` legend.
- docs/gotchas.md long form; `role_baseline.txt` prune is recorded by postedit.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
