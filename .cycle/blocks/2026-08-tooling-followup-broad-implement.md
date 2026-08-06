---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: #1 rot-flag on craft views · #2 shorthand-citation detection in the rationale audit · #3 vanilla-vs-data-gap messaging · #4 resolve count summary + --expect · #5 wildcards --dedup cross-deck union · #6 counters-payoff pattern gap · #7 matches.csv (process note, no code) · #8 make postedit
Files modified: scripts/deck.py, scripts/card.py, scripts/check_engines.py, scripts/check_patterns.py, tests/test_deck.py, Makefile, decks/21-gastromancer/deck.txt, dashboard.html, scripts/role_baseline.txt

CHANGES:
#1 | scripts/deck.py | `craft_rot_note()` joins `rotation_year` to the craft-target views: `check` flags each missing/short card rotating this year or next (plus a closing advisory line), `wildcards`' leverage list carries the same flag. Validated live: deck 49 has FIVE 2026-rotating craft targets nothing had flagged.
#2 | scripts/deck.py, tests/test_deck.py | `_shorthand_index` (comma-heads + capitalized word-tails of multi-word names, ambiguity KEPT as a candidate tuple) + `_shorthand_candidates` (prose-driven n-gram lookup) + detection loop in `rationale_staleness` with all existing suppressions. FP classes found by roster sweep and fixed: guild names blocklisted, in-deck gate is plain containment (possessives), `_NEGATION_AFTER` contrast suppressor, `dropp\w*`/`variant` added to cue lists. 7 new unit tests. Sweep result: 1 flag roster-wide, a TRUE positive (deck 21's archetype claimed Ragost while it lives in 21a — prose fixed).
#3 | scripts/card.py, scripts/deck.py | Blank text on a row with a resolved type line now prints "(no rules text — a vanilla creature (K-11), not a data gap)"; only an unresolved card says enrich/build. Ends the Quakestrider-class false errand.
#4 | scripts/deck.py | `resolve` prints "Total: N card(s) across M line(s)" to stderr; `--expect N` exits nonzero on mismatch. The 59-card draft off-by-one happened twice (decks 60, 60a).
#5 | scripts/deck.py | `wildcards --dedup`: union of all craft targets, one row per card — copies short (shared-collection math), rarity, decks served, ⚠rot — sorted by decks-served then rarity. Formalizes the hand-derived craft-efficiency cycles.
#6 | scripts/deck.py, scripts/check_engines.py | counters payoff patterns: active-voice "whenever you put … counter" (Knight of Wundagore's printed text) and "greater than (its|that creature's) base power" (Kutzil/Okinec). K-12 roster diff: 10 decks gain payoffs, 0 removals, all five spot-checked matches genuine. Two new gate anchors pin it.
#7 | (none) | Process finding: matches.csv still empty; ~10 provisional tiers unfalsifiable until /log-matches runs. No code — user action.
#8 | Makefile | `make postedit`: check_roles --update-baseline → build_dashboard → check_all, the after-every-deck-edit tail as one command.

TEST RESULTS: passed — 936 unit tests green; check_all all invariants hold; `make postedit` smoke-tested end-to-end. One intermediate failure (check_patterns: unregistered `_NEGATION_AFTER`) fixed by registering it in the gate's exclusion table — the gate working as designed.
REGRESSION RISKS: `cmd_wildcards` now reads `args.dedup` via getattr — build_dashboard's `SimpleNamespace()` call verified safe. `resolve` totals go to stderr so piped stdout is unchanged. `check` output gains lines only. Shorthand detection can still false-positive on unforeseen prose shapes — by design (G-26: a noisy FP gets noticed; the roster sweep is the check), currently 0 FPs roster-wide.
INVARIANTS AT RISK: None — no canonical-CSV writer touched; deck 21 prose edit re-parses clean (INV-04 in check_all green).
NET SCORE: 5 − 0 = 5  (#1,#2,#3,#4,#6 fixed misses that fired this month; #5/#8 are ergonomics, #7 is process)

OPERATOR ACTIONS / DEPLOY:
- Consider running /log-matches after some Arena sessions — ~10 PROVISIONAL tiers have zero game data (finding #7) | BLOCKS DEPLOY: N
Deploy: dashboard publishes via .github/workflows/pages.yml on push to main (no other deploy step).

FOLLOW-ON ITEMS:
- Deck 49's five ⚠rot~2026 craft targets (surfaced by #1) want the deck-28-style rotation-proofing pass before any crafting.
- Shorthand index caps ambiguity at ≤3 names; a 4+-way fragment is silently dropped — acceptable, noted.
- A failed enrich that populates Type but loses text would now read as "vanilla" — theoretical; enrich fills both together.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-26: "Shorthand … ARE handled" now true in BOTH directions (suppression + detection); the known-residual list shrinks.
- CLAUDE.md G-30/G-19: craft views (`check`, `wildcards`, `--dedup`) now carry ⚠rot — the "wishlist is the only flagged surface" caveat is stale.
- draft-deck skill: "the resolver won't catch an off-by-one" is stale — `resolve` now totals, and `--expect 60` hard-fails.
- K-11: the blank-text message now self-documents; gotcha can note that.
- README/CLAUDE.md command lists: new `wildcards --dedup`, `resolve --expect`, `make postedit`.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
