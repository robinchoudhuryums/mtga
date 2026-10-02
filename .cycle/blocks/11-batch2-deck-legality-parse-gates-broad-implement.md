---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS11-01 legal ignored a card's own copy-limit text ("any number of cards named", "up to N cards named")
- BS11-02 legal checked Brawl/Commander size as a minimum, not an exact size
- BS11-03 legal's commander colour-identity check skipped basic lands
- BS11-12 a leading Companion block was merged into the maindeck (sync would write a 61st card)
- BS11-05 a Sideboard/Maybeboard/Companion block in a deck file was parsed as maindeck with INV-04 green
- BS11-04 printing_problems exempted basics from the bad-set check (resolve --fix disagreed)
- BS11-73 a quantity-0 deck line passed INV-04
- BS11-07 deck_requirements keyed on the raw name; audit_deck re-implemented the loop
- BS11-08 verify kept sideboard lines while sync dropped them
- BS11-10 sync had no oversize-paste guard (two decks run together matched one)
- BS11-09 a flex reason starting with +/- overwrote the card columns
- BS11-11 resolve --fix rebuilt the whole line (name case, indent, comment spacing) and applied to any path
Files modified: scripts/deck.py, scripts/check_patterns.py, scripts/build_dashboard.py, dashboard.html, tests/test_deck.py, tests/test_deck_models.py, tests/test_dashboard_js.py

CHANGES:
BS11-01 | deck.py, check_patterns.py | new card_copy_limit() reads `_ANY_NUMBER_NAMED_RE` / `_UP_TO_N_NAMED_RE` from the card's text (None = unlimited, N for "up to N"); legality_report applies it in place of the format limit, singleton formats included. Both patterns registered in check_patterns. +3 tests.
BS11-02 | deck.py | a singleton-format deck over its size is a problem ("exactly 60/100"). +2 tests.
BS11-03 | deck.py | basics are collected separately (still copy-exempt) and run through the commander identity check. +1 test.
BS11-12 | deck.py, build_dashboard.py | strip_boards and the JS splitDecks treat `Companion` as a board (dropped like Sideboard/Maybeboard). +1 test.
BS11-05 | deck.py | parse_deck_file stops counting card lines under a Sideboard/Maybeboard/Companion heading; malformed_deck_lines reports them (INV-04 hard). +1 test; one old test that tolerated a sideboard CARD now tolerates only the marker.
BS11-73 | deck.py | malformed_deck_lines reports a quantity-0 card line. +1 test.
BS11-04 | deck.py | printing_problems applies the set-code check to basics and snow basics (collector number stays exempt); _resolve_fix's own basics loop removed as redundant. +1 test; two resolve-fix tests now run the real check instead of a stub.
BS11-07 | deck.py | deck_requirements keys on _ms_key; audit_deck calls deck_build_gap instead of its own loop. +1 test.
BS11-08 | deck.py | cmd_verify runs strip_boards before parsing and notes how many board cards it ignored. +1 test.
BS11-10 | deck.py, build_dashboard.py, tests/test_dashboard_js.py | match_paste sets `oversized` (> 125% of the stored total); cmd_sync labels it and --apply skips it unless --force; the dashboard matcher mirrors the flag and labels it (the "change both or neither" rule). +2 tests (one cross-language).
BS11-09 | deck.py | only the first `-` and first `+` columns are card fields; later signed columns are note text. Roster: 0 of 971 flex lines change.
BS11-11 | deck.py | _resolve_fix replaces only the `(SET) #` span in place (name, indent, spacing and comment verbatim) and refuses --apply on a path that is not a roster deck. +2 tests; the existing tests resolve tmp paths as roster decks via a fixture.

TEST RESULTS: passed — `python3 scripts/check_all.py` all invariants hold (soft warnings unchanged); full pytest suite exit 0 after updating one test that encoded the old sideboard tolerance. A roster sweep of legality_report over every deck file found 0 problems after BS11-01/02/03. Regression scenario 2 (analyze a deck) exercised by the CLI suite; scenarios needing a browser not walked.
REGRESSION RISKS:
- `resolve --fix <path> --apply` is now refused unless the target resolves as a roster deck id; pass the id.
- A deck file with a sideboard block now fails INV-04 (0 live files have one).
- A pasted Companion is no longer counted by sync/verify/the dashboard panel; a Companion is not part of the maindeck in Arena, so this matches the rules.
INVARIANTS AT RISK: INV-04 is stricter (board card lines and quantity-0 lines, basics' set codes) — 0 live violations, gate green.
NET SCORE: 0 − 0 = 0 (defensive batch: none of the twelve fired on the live roster this month — no Slime-style deck over 4, no off-size Brawl deck, no sideboard/companion pastes or files, no qty-0 lines, 0 affected flex lines)

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds the dashboard on the next push to main (the committed dashboard.html was rebuilt here).

FOLLOW-ON ITEMS:
- The dashboard JS `deckFormatClass` reads the raw format string (the BS11-06 alias issue, Batch 6).
- A `#~ note: applied — Kinscaer Sentry in for Captain America's Shield.` history line in deck 23 now reads oddly since the Shield is back in (editorial).

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-09 (`legal`): a card's own copy-limit text is honoured; Brawl/Commander size is exact; basics are identity-checked.
- CLAUDE.md G-08 (`sync`): an OVERSIZED paste is flagged and skipped like a TRUNCATED one; Companion blocks are boards.
- CLAUDE.md G-65 / INV-04: basics' set codes are checked; card lines under a board heading and quantity-0 lines fail INV-04; `resolve --fix --apply` takes a roster id only and replaces only the printing span.
- README `legal` / `sync` / `verify` / `resolve --fix` sections, to match.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
