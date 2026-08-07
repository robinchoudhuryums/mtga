---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS2-01 | sync --apply could rewrite a deck file to a TRUNCATED paste (data loss)
- BS2-03 | import_collection --zero-missing zeroed a card whose quantity cell it could not read
- BS2-04 | exports with no set/collector column collapsed distinct printings to max(), silently LOWERING counts
- BS2-06 | "deals N damage to target player/opponent" classified as spot removal, inflating the interaction axis the tier floor grades on (14 decks)
- BS2-02 | reconcile_crafts / import_arena re-added an owned full-name-stored DFC printing as a duplicate front-name row, splitting the owned count
- BS2-25 | verify_ingest had no front→full name fallback, reporting owned cards "NOT in library" — composing with BS2-02 into a loop that manufactured the split
- BS2-08 | suggest --ramp/--interaction/--needs silently dropped the format filter on a cased --format and ignored --any-format entirely

Files modified: scripts/deck.py, scripts/import_arena.py, scripts/import_collection.py,
scripts/reconcile_crafts.py, scripts/verify_ingest.py, scripts/role_baseline.txt,
tests/test_deck.py, tests/test_ingest.py, tests/test_reconcile_crafts.py,
tests/test_verify_ingest.py, decks/01,09,10,26b,33,35,44,45a,48 (stale #: tier: figures)

CHANGES:
BS2-01 | scripts/deck.py, tests/test_deck.py | match_paste now returns paste_total/deck_total/truncated (paste < 75% of the stored deck = fragment, not an edit — an Arena export is always the whole deck; the largest legitimate shrink is a 64→60 trim ≈ 0.94). cmd_sync reports "⚠ TRUNCATED?" in dry-run and refuses the write without --force, same handling as a low-confidence match. Reproduced before/after: the first 8 lines of deck 52 dry-ran as a full-confidence rewrite; now flagged + skipped. 3 new tests.
BS2-03 | scripts/import_collection.py, tests/test_ingest.py | parse_export returns a third element `unreadable` (names whose quantity cell isn't a non-negative integer); plan(unreadable=…) marks their library rows SEEN so --zero-missing can never zero them (full-name or front-face resolution). main() warns prominently under --zero-missing. Warning text now says "row left unchanged", not "skipped". 2 new tests; 9 existing call sites updated to the 3-tuple.
BS2-04 | scripts/import_collection.py, tests/test_ingest.py | when the export has NO set/collector column, repeated-name rows are distinct printings and SUM (per finish) instead of max-collapsing — with a per-card "SUMMED to N" warning. The max-on-repeat rule stays wherever a real printing key exists. 2 new tests.
BS2-06 | scripts/deck.py, scripts/role_baseline.txt, decks/* | the fixed-damage removal pattern gained the (?!(?:player|opponent)\b(?! or planeswalker)) guard its scaling-damage sibling documents as load-bearing; "player/opponent or planeswalker" (42 pool cards, can hit a planeswalker) stays counted. Measured roster-wide per K-12/K-14: 14 decks' interaction drops (deck 10: 15→12), ZERO tier floors moved. 2 newly-roleless cards (Hawkeye Master Marksman — player-only burn mode; Ozai's Cruelty) read from full text and baselined. 9 stale #: tier: interaction figures re-grounded in this same change (decks 1, 9, 10, 26b, 33, 35, 44, 45a, 48); rationale audit reports 0 stale figures after.
BS2-02 | scripts/reconcile_crafts.py, scripts/import_arena.py, tests | the library-row join now matches on FRONT faces both sides ((set, collector) keeps it unambiguous — a collector number is unique within a set): import_arena.key() is front-face-named; reconcile's `existing` lookup front-matches, and its mana-row check keys on the LIBRARY row's actual spelling (lib_name), so no spurious front-named mana row is appended for a full-name-stored card. 2 new tests (one end-to-end through --apply in the tmp world).
BS2-25 | scripts/verify_ingest.py, tests/test_verify_ingest.py | _library_key resolves front→full to the STORED spelling (third step, O(n) on miss only), keeping the quantity and mana checks on the same row; verify() reads the owned count off the resolved key instead of owned_qty (which only resolves full→front). Front-name paste of an owned Room now verifies clean end to end. 1 new test.
BS2-08 | scripts/deck.py, tests/test_deck.py | new shared _needs_fmt(): normalizes --format case, honours --any-format, falls back to the deck's #: format:, and prints the same "not tracked — not filtering" / "no legality data" notices cmd_suggest prints — a dropped filter is never silent. cmd_suggest_needs forwards any_format to suggest_lands explicitly (fmt="" would re-enable the deck-format fallback). Workers untouched (check_suggest anchors call them directly). Reproduced: `suggest 52 --ramp --format Standard` now returns the Standard-filtered picks (Mox Jasper/Cryptex), not Pillar of Origins/Adherent's Heirloom. 4 new tests.

TEST RESULTS: 965 passed (951 pre-existing + 14 new), 0 failed. check_all: "All invariants hold. ✓" with ZERO soft warnings (the 2 new zero-role cards baselined; 9 stale rationale figures fixed in the same change; roster tier guard clean). Regression scenarios: Scenario 2 walked on every modified surface (sync dry+apply-refusal, verify, suggest --ramp/--interaction/--needs with all three warning paths, stats/tier on re-grounded decks, --help + subcommand help) — PASS. Scenario 1 partially walked (reconcile/import_arena/verify_ingest dry-runs against live data + end-to-end --apply in the tests' tmp world) — PASS on exercised surfaces; make refresh NOT APPLICABLE (no data mutated, nothing to rebuild). Scenarios 3–8 NOT APPLICABLE (no refresh inputs changed; no app/presentation files touched).

REGRESSION RISKS:
- match_paste's dict gained three keys (additive); the dashboard JS stale-check mirror is report-only and pins the tie-break rule, which is unchanged. A deliberate >25% deck cut via sync now needs --force (message says so).
- import_collection with NO printing columns: a tracker emitting true duplicate rows now over-counts where it used to under-count — mitigated by a per-card "SUMMED to N" warning naming the card; the per-printing-export premise (already load-bearing for the summing rule) makes SUM the correct default.
- BS2-06 lowers interaction on 14 decks — audit verdicts and deck_needs.int_short shift accordingly on those decks; that is the correction, and zero tier floors moved (measured).
- import_arena.key() front-face keys mean two spellings of one printing in ONE paste now fold together (correct — same physical printing).

INVARIANTS AT RISK: None. INV-01 (front-face join *prevents* duplicate-printing rows), INV-02 (mana rows now keyed to the library row's actual spelling — strictly more correct), INV-04 (deck edits are `#:` comment lines only; check_all green). check_patterns green (the edited pattern still matches live pool cards).

NET SCORE: 5 − 0 = +5
(All five fired in production terms: BS2-06 was continuously mis-grading 14 decks; BS2-02/25's loop reproduced against the live library's 8 full-name rows; BS2-08 fired on the natural `--format Standard` spelling; BS2-01 on any partial paste; BS2-04 on any name-only export. No new silent failure modes introduced; the two behavior changes that could surprise are both loudly reported.)

OPERATOR ACTIONS / DEPLOY:
None
Deploy: commit/push is the deploy (Data + local tooling, per CLAUDE.md). pages.yml auto-rebuilds the dashboard on merge to main — no manual step.

FOLLOW-ON ITEMS (from the same scan, deliberately out of this scope):
- BS2-10: sync can match two pasted blocks to the SAME deck and write it twice — same write loop as BS2-01, next highest-value sync fix.
- BS2-05: verify_ingest cannot parse a collection CSV at all (the authoritative route's mandated check) — teach it import_collection.parse_export's shape.
- BS2-24: import_arena still accepts set-less lines and appends a phantom ("name","","") printing (over-count path, adjacent to the key() change).
- BS2-11/12: wishlist _is_land back-face mis-ranking (live budget error) and card.py "in decks: (none)" DFC join miss.
- BS2-16/17: dashboard a11y role="button" regression; gallery.html unescaped set/cn/img interpolations.
- BS2-13/14: check_patterns one-level container walk (dead engine pattern `whenever[^.]*is sacrificed` found); INV-04 has no malformed-line channel.
- BS2-18: interaction_profile counts lands role_tally excludes (13 decks print two contradicting figures in one stats run) — K-12's canonical-counter claim stays contradicted until fixed.

DOCUMENTATION UPDATES NEEDED (for /sync-docs):
- docs/gotchas.md G-67: record the BS2-06 incident — "never an over-count" was false for the pattern set's life until this fix; the guard and the 42-card "or planeswalker" retention belong in the long form.
- README import_collection section: the sum-on-no-printing-columns rule and the unreadable-quantity protection (both change documented semantics).
- docs/gotchas.md G-63: the ingest WRITE side is a new class member (BS2-02) — the "key every name JOIN on _ms_key" rule now demonstrably covers writers, not just loaders.
- G-08/sync prose: mention the truncation guard (a partial paste is flagged, --force overrides).
- K-12's "role_tally is the ONE canonical counter" remains contradicted by BS2-18 (unfixed) — either fix or annotate.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
