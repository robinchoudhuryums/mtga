---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (the top-5 block's FOLLOW-ON ITEMS, all ten):
- BS2-10 | sync could match two pasted blocks to the SAME stored deck and write the file twice
- BS2-05 | verify_ingest could not read a collection CSV — the authoritative route's mandated check — and printed a false "never ingested" claim
- BS2-24 | import_arena appended a phantom blank-set printing for a set-less line (the subsystem's one over-count path)
- BS2-11 | wishlist._is_land scanned the whole type line, so back-face-land DFCs were ranked (and bought) as manabase
- BS2-12 | card.py reported "in decks: (none)" for owned cards the roster plays (deck-line join never front-face normalized)
- BS2-13 | check_patterns' walker stopped one container level deep — 68 oracle-text classifiers invisible, one dead engine pattern live
- BS2-14 | INV-04 had no malformed-line channel — a broken card line was silently deleted from every analysis
- BS2-16 | dashboard a11y() forced role="button" onto <h2> headings and <th> columnheaders, erasing heading/table semantics
- BS2-17 | gallery.html interpolated Set Code / Collector # / qty / image URL unescaped (stored-XSS path via the editor)
- BS2-18 | interaction_profile skipped role_tally's nonbasic-land filter — 13 decks printed two contradicting figures in one stats run

Files modified: scripts/deck.py, scripts/card.py, scripts/wishlist.py, scripts/import_arena.py,
scripts/verify_ingest.py, scripts/check_all.py, scripts/check_patterns.py,
scripts/build_dashboard.py, scripts/build_gallery.py, dashboard.html + gallery.html (rebuilt
artifacts), tests/test_deck.py, tests/test_card.py, tests/test_wishlist.py,
tests/test_ingest.py, tests/test_verify_ingest.py, tests/test_templates.py

CHANGES:
BS2-10 | deck.py | cmd_sync tracks claimed deck ids; a later block matching an already-claimed deck is reported ("ALSO matched #N, already claimed by block M") and skipped — first claim wins, exit non-zero. Reproduced live (two blocks → one claim). 1 test (monkeypatched roster, dry-run).
BS2-05 | verify_ingest.py | when ZERO Arena lines parse, the text is retried through import_collection.parse_export (CSV/TSV), with a "read as a collection CSV/TSV export" banner; the "never ingested by ANY tool" hint is scoped to actual could-not-parse warnings so it can no longer make a false claim about a just-applied import. Reproduced live (2-row tracker CSV verifies clean, --exact works). 2 tests.
BS2-24 | import_arena.py | merge() returns (added, updated, notes); a set-less line is a NAME-level claim: for an owned card it compares against the summed total (tops up the first printing only if the line exceeds it; sums onto it under --sum), never appends a phantom row; an unknown card is still added but loudly ("BLANK set code — prefer a printed export"). 3 tests; 3 call sites updated.
BS2-11 | wishlist.py | _is_land routes through lib.primary_type (front face). Live re-rank matches the scan's corrected measurements exactly: Ojer Axonil combined 6.37→4.54 (no longer bought at --budget pick #6 as "manabase"), Matzalantli re-tiered. 3 tests.
BS2-12 | card.py | _decks_using joins on front faces BOTH sides; "Cecil, Dark Knight" ↔ "…// Cecil, Redeemed Paladin" resolve each other (5 affected cards verified live). 2 tests (tmp deck dir).
BS2-13 | check_patterns.py + deck.py | recursive _walk_patterns (any depth, cycle-capped); _ENGINE_COMPILED (63) + _COST_UPSIDE (5) registered against the norm corpus; _RATIONALE_FIGURES/_SECTION_EXPECTATIONS declared in _EXCLUDED with reasons; the dead sacrifice-payoff pattern `whenever[^.]*is sacrificed` (0 of ~15.9k pool texts) REMOVED — 247 patterns now all live-corpus verified. check_engines still green; active-voice sacrifice payoffs still detected.
BS2-14 | deck.py + check_all.py | new deck.malformed_deck_lines(path): non-blank, non-comment lines that are neither a `#:` header, a card line, nor a tolerated Arena marker (Deck/Sideboard/…) are a HARD INV-04 failure naming the line. Roster surveyed first: zero flags (the 12 stray `Deck` markers are tolerated by design). 4 tests incl. the quantity-less line and BOM cases.
BS2-16 | build_dashboard.py + dashboard.html | a11y() gains role:null = keep the native role; the nine <h2> section headers, the sort <th>s (aria-sort now valid on columnheader) and the progressive-disclosure <td> use it. Source-pinned by 3 new tests in test_templates.py (the markup is JS-built, so the pin is on the builder). Artifact rebuilt.
BS2-17 | build_gallery.py + gallery.html | esc() on the four unescaped interpolations (set, cn, qty, img src), matching collection.html's discipline for the same data. Artifact rebuilt (2085 cards).
BS2-18 | deck.py | interaction_profile applies role_tally's nonbasic-land filter; all 93 roster decks now report ONE interaction figure (verified roster-wide: zero disagreements). Deck 44/48 prose parentheticals re-checked against the corrected profile — both already accurate; rationale audit reports 0 stale figures. K-12's "one canonical counter" claim is TRUE again.

TEST RESULTS: 983 passed (965 + 18 new), 0 failed. check_all: "All invariants hold. ✓", zero soft warnings. Scenario 2 walked on touched surfaces (card.py both spellings, sync double-claim, verify_ingest CSV + Arena routes, stats/engines, --help) — PASS. Scenario 1's verify step now covers the collection-CSV route it previously couldn't — PASS on exercised surfaces. Scenarios 5–7 remain the operator's browser walk; the BS2-16/17 halves verifiable from code are pinned by tests.

REGRESSION RISKS:
- import_arena.merge returns a 3-tuple (callers updated; external callers would break loudly, and none exist).
- A set-less line for an owned card no longer creates a row — a user who WANTED a new blank-set printing row for an owned card loses that (never a sane outcome; notes say what happened).
- check_patterns now covers 68 more patterns: a future dead engine/cost-upside pattern FAILS the build (intended forcing function; may surprise the next pattern author).
- a11y role:null sites keep tabIndex+keydown, so keyboard operation is unchanged; screen-reader announcement of th/h2 changes from "button" to native semantics (the correction).
- verify_ingest CSV fallback triggers only when zero Arena lines parse — a mixed paste still reads as Arena.

INVARIANTS AT RISK: None. INV-04 is STRENGTHENED (malformed-line channel); INV-01 further protected (no phantom printings); artifacts (INV-03's gallery.html) rebuilt through their own builders.

NET SCORE: 10 − 0 = +10
(BS2-18/16/17/13 were live continuously; BS2-11 was mis-spending a live budget ranking; BS2-12 mis-reported five owned cards; BS2-05/10/14/24 fired on routine-shaped inputs. No new silent failure modes; all behavior changes are loudly reported.)

OPERATOR ACTIONS / DEPLOY:
None
Deploy: commit/push is the deploy; pages.yml rebuilds the dashboard on merge to main (the committed dashboard.html/gallery.html are already rebuilt in this commit).

FOLLOW-ON ITEMS: the remaining scan findings are grouped, prioritized and effort-estimated in the session's closing report (batches A–H); .cycle/STATE.md points here.

DOCUMENTATION UPDATES NEEDED:
- K-12's "role_tally is the ONE canonical counter" is TRUE again (BS2-18) — no annotation needed; G-08's long form could add the same-deck claim guard (BS2-10) next /sync-docs.
- README verify_ingest section: it now reads collection CSVs (the import_collection handoff is real).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
