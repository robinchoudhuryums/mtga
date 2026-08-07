---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (Batch C — gate hardening: closing the "a check that cannot fire" holes in the gates themselves):
- BS2-29 | check_all.py had zero tests — the one component exempt from the project's own "a check never watched failing is not a check" rule (BS2-14 was the concrete cost)
- BS2-30 | the CI smoke loop passed vacuously on a glob miss (no count guard, while the same file's subcommand half had one six lines later)
- BS2-31 | check_commands' script coverage accepted a bare prose mention (two of build_pool.py's three "mentions" were warnings NOT to run it), and `deck\.py suggest\b` was satisfied by "suggest-homes"
- BS2-32 | two-thirds of check_agreement's pairs silently switched off when the pool lacked Legalities — a soft data state disabling a hard gate with no message
- BS2-33 | check_suggest's positive wiring anchors were guarded on `ok` truthy, so a total wiring failure (suggest_scored bailing) was the one case they skipped
- BS2-34 | check_engines' fixtures were author-invented paraphrases (the G-67 circularity its own cases warn about) — which is why BS2-13's dead pattern lived
- (small leaks) | check_keywords standalone never ran 2 of its 3 signals (and `stale_registry_entries` was defined BELOW the __main__ guard, so a hand run never defined it); check_rankings anchor 7 silently skipped on a renamed `_seed_power`; check_dfc's editor-payload pin returned clean if the template file moved; check_patterns' `_EXCLUDED` had no in-gate staleness screen (only pytest-layer, which the dependency-free workflow can't run); check_all --quiet collapsed the crashed-radar promotion into the plain soft count on exactly the hook path it was built for

Files modified: tests/test_check_all.py (NEW), tests/test_check_commands.py,
.github/workflows/integrity.yml, scripts/check_commands.py, scripts/check_agreement.py,
scripts/check_suggest.py, scripts/check_engines.py, scripts/check_keywords.py,
scripts/check_rankings.py, scripts/check_dfc.py, scripts/check_patterns.py,
scripts/check_all.py

CHANGES:
BS2-29 | tests/test_check_all.py | 11 mutation tests in tmp worlds: INV-02 (missing mana row named; full coverage quiet; missing file reported), INV-03 (library-header rewrite hard naming the lost columns; optional-columns soft; healthy quiet; missing file hard), INV-04 (malformed line hard naming it — the test that would have caught BS2-14; zero-parseable hard; clean quiet; bad set hard / unheld number soft).
BS2-30 | integrity.yml | the script loop counts what it checked and fails under 25 — same guard, same rationale comment as the subcommand half. A moved scripts/ dir now fails instead of reporting "OK" over nothing.
BS2-31 | check_commands.py, tests | script coverage requires an EXECUTABLE shape — `python3 scripts/<fn>` in a skill or `scripts/<fn>` in the Makefile (make refresh/dashboard ARE the invocation); the subcommand regex uses `(?![\w-])` so `suggest` no longer inherits coverage from `suggest-homes`. The tightened gate immediately caught query.py riding on prose — classified INTERACTIVE_ONLY with an honest reason (ad-hoc search; args come from the conversation; /tune-deck names it) per the deck.py-list precedent. 3 new test pins (script prose ≠ coverage, script invocation = coverage, hyphen non-inheritance).
BS2-32 | check_agreement.py | both legality-dependent pairs WARN "NOT exercised — quiet = unverified" to stderr when the pool lacks Legalities, instead of returning indistinguishably-from-passing. Kept soft (G-21 documents the pool state as legitimate degradation); the disablement is now visible.
BS2-33 | check_suggest.py | `ok` falsy in the synthetic world is itself a hard error naming the bail reason — the positive anchors can no longer evaporate.
BS2-34 | check_engines.py | every invented fixture replaced with a REAL card's printed text, card named beside each (A-Sepulcher Ghoul, Elas il-Kor, Esoteric Duplicator, Kick in the Door, Marketback Walker, Argivian Cavalier, Midnight Tilling, Life // Death, Devil's Play, Drogskol Reaver, Savor, Summon: Anima). All classify correctly on first run — the patterns match real templating; the invented strings were the only thing hiding the one that didn't.
(small leaks) | check_keywords.py (main reports all three signals; __main__ guard moved to EOF), check_rankings.py (missing `_seed_power` = hard error), check_dfc.py (missing template = hard error), check_patterns.py (in-gate _EXCLUDED staleness screen), check_all.py (--quiet appends "⚠ N RADAR(S) DID NOT RUN" when a soft radar crashed).

TEST RESULTS: 1012 passed (998 + 14 new: 11 test_check_all + 3 test_check_commands), 0 failed. check_all full and --quiet green, zero soft warnings; every individually-touched gate run standalone and green (check_patterns 247 live, check_engines, check_suggest, check_rankings, check_dfc, check_keywords, check_commands 34+33 covered / 6 exemptions). Scenario 3's gate half exercised via the full check_all run — PASS; other scenarios N/A (no analysis-model or presentation behavior changed).

REGRESSION RISKS:
- check_commands is STRICTER: a future skill that references a script only in prose will now fail the gate until it carries a real invocation or an exemption — intended (that is G-53's rule).
- check_patterns' _EXCLUDED screen and check_rankings/check_dfc's hard errors turn three silent skips into build failures on refactors — intended forcing functions.
- check_keywords standalone output grew (three signals) — scripted consumers of its stdout (none exist) would see more lines.
- No model, scorer, writer, or data behavior changed anywhere in this batch.

INVARIANTS AT RISK: None — this batch only strengthens the machinery that verifies them.

NET SCORE: 7 − 0 = +7
(Each fix makes a previously-invisible failure visible; BS2-31's tightening caught a live coverage gap (query.py) the moment it landed, which is the pattern working.)

OPERATOR ACTIONS / DEPLOY:
None
Deploy: commit/push is the deploy. integrity.yml's new guard takes effect on the next push.

FOLLOW-ON ITEMS:
- Batches D–H from the priority report, unchanged (Batch D — editor write-safety — is next).
- BS2-07's header-consumer sweep, still the standing Batch A leftover.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md C-01/C-07 gate-and-test inventory: tests/ is now 26 files; worth refreshing the counts in the next /sync-docs pass.
- G-56's "structurally forbids" (test_recommendations one-level depth) remains the one gate-layer finding NOT in this batch — it was listed under Batch G's CLI seams; note kept here so it isn't lost.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
