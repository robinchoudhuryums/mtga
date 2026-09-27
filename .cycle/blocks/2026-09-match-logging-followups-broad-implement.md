---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (the six match-logging follow-ups from the first real play-by-play
run, 2026-09-27; implemented in the order 6 → 5 → 1 → 4 → 2 → 3, repo-side first, the
Mac-side function last so it ships in one re-install):
- ML-1 | after an ingest, ask for a one-word reason per NEW loss (0 of 191 rows carried
  any hand column, across 94 losses)
- ML-2 | anonymise the paste — local Arena id → `ME`, every other `"userId"` → `OPP`
  (184 id occurrences / 47 distinct people in one paste)
- ML-3 | automatic date — `mtga-matches` resumes from its previous copy's day, `all`
  copies everything, the date used is printed; every ingest report ends with the next
  command (43 of that paste's 46 matches were already recorded)
- ML-4 | per-deck match history, `parse_matches.py --report --deck <id>`; `/tune-deck`
  shows it as report-only context
- ML-5 | the dry run names new matches that have no play-by-play line
- ML-6 | several same-named Arena decks claiming one repo deck → the newest copy wins
  (owner decision: an edited deck is re-imported as a new Arena deck and the old one
  deleted), instead of a conflict warning on every run (deck 58, three copies)

Files modified: scripts/parse_matches.py, tests/test_parse_matches.py,
.claude/commands/log-matches.md, .claude/commands/tune-deck.md, CLAUDE.md,
docs/gotchas.md, decks/58-treasure-planet/deck.txt (header only), dashboard.html
(rebuilt by `make postedit`)

CHANGES:
ML-6 | scripts/parse_matches.py | `parse_deck_times` reads `LastUpdated`/`LastPlayed` per
  DeckId off the summary lines; `_newest_copy` picks max (LastUpdated, LastPlayed, guid)
  when every claimant's name is typographically identical AND each has a timestamp —
  otherwise None, and the old conflict path runs unchanged. The name key is a
  typography-only key, NOT `_name_key`, which strips a trailing "(...)" gloss and would
  have read "07 Earth's Mightiest (old)" as a copy (the existing conflict test caught it).
  `_arena_header_plan(names, times=None, notes=None)` — new args default, so no caller
  breaks; `map_decks` / `sync_headers` print the choice as a note. Deck 58's header moved
  4f83c097 → e96eca40 via `--map-decks --apply` on the saved paste.
ML-5 | scripts/parse_matches.py | `_print_missing_details` names each new match with no
  `[MTGA-GAME]` line ("a phone game, or a log that rotated"), or says the extractor is not
  installed when the paste has no game lines at all.
ML-1 | scripts/parse_matches.py, .claude/commands/log-matches.md, CLAUDE.md |
  `_print_loss_prompt` runs after the write and prints, per new loss, a commented details
  line (date · deck · play/draw · turns · opponent colours: first cards) and a ready
  `<matchId> why= opp=` line for `--annotate`. New Stage 1d in `/log-matches` asks the
  owner for one word each from the closed vocabulary. "Never fill a reason in yourself" is
  in the skill and in G-74.
ML-4 | scripts/parse_matches.py, .claude/commands/tune-deck.md | `deck_history` — header
  with n and the restraint read, a per-match table (Date, R, On, Turns, Opp, Why, first
  four non-basic opponent cards), loss tallies by opponent colours and by reason as
  COUNTS only, and a closing restraint line. Unknown id → exit 1 with a message.
  `/tune-deck` step 2e runs it as context, never as a reason for a cut/add/tier.
ML-2 | .claude/commands/log-matches.md | an awk stage in `mtga-matches` rewrites the
  `Match to <id>:` header to `Match to ME:` and each `"userId"` to `ME`/`OPP`, BEFORE the
  date filter so the id is known even for a date-cut paste. Both seat readers (parser +
  dashboard paste reader) compare the header id with a seat id, so `ME`/`ME` resolves
  exactly as the real id did — verified by a test running the function under bash.
ML-3 | .claude/commands/log-matches.md | `~/mtga-logs/.last-copy` holds the day of the
  last copy that produced lines; no argument resumes from it (inclusive), `all` copies
  everything, the message names the date and how it was chosen. Stage 1 ends every log
  report with the next command.

TEST RESULTS: passed — full suite 1961 passed on this source (SessionStart run); check_all "All
  invariants hold" with the 3 pre-existing soft warnings (lower-bound counts, deck 28
  `#~ note:`, three dead library searches); `parse_matches.py --help` OK; `--report --deck`
  byte-identical under two PYTHONHASHSEED values. 17 new tests: 5 newest-copy, 5 ingest
  follow-ups (incl. an `--annotate` round-trip), 3 deck history, 4 that run the Mac
  function from the skill doc under bash with a stubbed pbcopy.
REGRESSION RISKS:
- ML-3: the stamp records what was COPIED, not what was INGESTED — a copy never pasted
  makes the next default run skip earlier days. Named in the command's own output
  (`mtga-matches all`), and dedup by matchId keeps an over-paste harmless.
- ML-6: a paste restricted to a period when only an OLD copy was played sees one claimant
  and moves the header back to it. Attribution is unaffected (every copy resolves by
  name); the header self-corrects on the next paste that carries the newer copy.
- ML-2: the anonymiser takes the id from the FIRST `Match to` header in the stream. Logs
  from two Arena accounts merged into one archive would mark the second account `OPP`
  and its matches would be skipped as unresolvable (the parser refuses, never guesses).
  A hand-trimmed paste with NO `Match to` header now marks every seat `OPP`, so the
  `--me` escape hatch cannot rescue it; the function always carries the headers.
INVARIANTS AT RISK: None — INV-04 re-checked after the deck 58 header write (header line
  only, no card line touched); no library/derived CSV writer changed.
NET SCORE: 5 − 2 = 3 (production: ML-1, ML-2, ML-3, ML-5, ML-6 all fired on the first
  real paste; ML-4 is a capability, not a fix. New failure modes: ML-3's
  copied-not-ingested stamp and ML-6's old-period header flip, both documented.)

OPERATOR ACTIONS / DEPLOY:
- Re-install `~/mtga-logs/mtga-matches.zsh` on the Mac from `/log-matches` Stage 0 (one
  paste block; `extract.sh` and `snapshot.sh` are unchanged) | BLOCKS DEPLOY: N — the old
  function keeps working; ML-2 and ML-3 arrive only after the re-install.
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds the dashboard on the next
  push to `main` (the committed dashboard.html changed by one data line).

FOLLOW-ON ITEMS:
- The first automatic run on the Mac has no stamp and copies everything — expected, once.
- Two Arena ids (#103473, #97593) are unresolved by Scryfall's Arena lookup and show as
  placeholders in opponent card lists; misses are not cached, so they retry each run.
- The history view's opponent cards include nonbasic lands (only basics are dropped).
- Best-of-three play-by-play is still unverified on a real log.

DOCUMENTATION UPDATES NEEDED:
- None beyond this change — G-74 (CLAUDE.md sentence + a docs/gotchas.md subsection),
  `/log-matches` Stage 0/1/1d/2/3 and `/tune-deck` 2e were updated in the same commit.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
