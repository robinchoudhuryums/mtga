---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: 1–4, from the post-ingest review of the match-logging workflow
  1 | `parse_matches.py` printed a W/L verdict with none of the evidence behind it
  2 | The `Reason` column stored the field that never varies; the one that does was dropped
  3 | The name-prefix attribution route validates the NUMBER only, then writes a permanent header
  4 | The documented extraction recipe leaves 92%-noise card arrays in the paste
Files modified: scripts/parse_matches.py, tests/test_parse_matches.py,
  .claude/commands/log-matches.md, matches.csv (schema migration + backfill)

CHANGES:
1 | scripts/parse_matches.py | `parse_log` now carries `_my_team` / `_win_team` on each
    row (underscore keys — `write_matches` emits only HEADER, so they never reach the
    CSV), and the dry run prints `[my team 1 · winner 1]` per match plus a one-time note
    on how to read it. G-52: the surface that decides W/L must show what it decided from.
    A single inverted seat read flips every row in a paste the same direction, which
    reads as a losing streak rather than as a bug — the first 15 matches were verified by
    hand-reading the JSON, which is the cost this removes. Evidence keys on the field's
    PRESENCE, not truthiness: a CSV-loaded row prints nothing, but a parsed row whose
    seat has no `teamId` prints `?`, because that is the least trustworthy verdict there
    is and must not share the silent-empty branch.

2 | scripts/parse_matches.py, matches.csv | Added an `Ended By` column carrying the
    match-scope result's own `reason` (Game / Concede). `Reason` is unchanged and keeps
    `matchCompletedReason`, which is `Success` for every match that COMPLETED — all 15
    rows of the record read `Success`, i.e. the stored column carried zero bits, while
    the dropped one distinguished 2 of the 3 matches in the batch that surfaced this. It
    matters most at low n, which is where this record permanently lives: deck 15's 2–0 is
    two opponent CONCEDES, not two games played out.
    Migrated the live matches.csv (15 rows, verified cell-by-cell that nothing outside
    the new column changed) and backfilled `Ended By` on the 6 matches whose logs were
    still on disk, through `parse_log` rather than by hand. 9 rows stay blank — honest,
    those matches were parsed before the field was read.

2b | scripts/parse_matches.py | ENABLING FIX: generalized `_is_own_earlier_schema`. It
    hard-coded the ONE header remembered from the avatar rename, which worked exactly
    once — adding a column makes the CURRENT file an "earlier schema" too, and an exact
    match cannot see that, so the guard would have refused the very write that performs
    the migration. That is the bug the function exists to prevent, reproduced by its own
    narrowness. Now: every column is one of mine, in my order, no duplicates, and the
    core three (Date / Match ID / Result) present. Accepts any past or intermediate shape
    — columns here have been both RENAMED and INSERTED MID-HEADER, so neither a prefix
    nor a subset test would do — while still refusing a foreign CSV.

3 | scripts/parse_matches.py | REVISED FROM WHAT WAS SPECIFIED, on measurement. The
    finding asked for a name-AGREEMENT gate: cross-check the Arena name's remainder
    against the repo `#: name:` and refuse a mismatch. Measured over the 22 `#: arena:`
    headers on the roster — every one a CORRECT mapping — 8 DISAGREE under a containment
    test ("49 Big Draco" is Scaleforge, "58 Treasure Planet" is Gold Standard, "45 The
    Exiles" is Exile Dividend). The Arena names are flavour names, not repo names, so the
    gate would have blocked a correct attribution 36% of the time — the saturation that
    made the `review` flag 0% actionable in G-07. Implemented as DISCLOSURE instead: the
    attribution block prints the repo deck's own name next to a `name prefix` route plus
    a warning that --apply turns the guess into a permanent header. G-38's stance for a
    fuzzy signal — flag, don't score. New `deck_names()` helper, wired at the ONE caller
    that matters and tested through `main()`, because G-40 is the recurring failure here.

4 | scripts/parse_matches.py (docstring), .claude/commands/log-matches.md | Folded a
    `sed` stage into both documented extraction recipes, dropping EventSetDeckV3's
    MainDeck/Sideboard card arrays — which nothing reads (attribution uses only Name,
    DeckId, LastPlayed off the same line). Measured: a real 52-card selection line is
    1919 bytes and slims to 152, a 92% cut, once per event join. Verified the slimmed log
    parses byte-identically. Documented to slim at PASTE time, never at capture time:
    slimming inside `snapshot.sh` would put two forms of the same line in the archive and
    defeat its own `awk '!seen[$0]++'` dedupe. Also made the module docstring RAW — the
    shell regex it now contains (`\[`, `\\"`) is an invalid escape sequence in a normal
    string: a DeprecationWarning today, a SyntaxError on a future Python, from a comment.

TEST RESULTS: passed — 1299 passed, 1 skipped (was 1285 + 1; +14 new tests).
  `check_all.py`: all invariants hold. `check_commands.py`: OK, 34 subcommands / 33
  scripts reachable. `parse_matches.py --help` builds (G-55).
  Regression Scenario 9 (Log a session of matches) walked against the REAL log:
    - dry run → --apply → --report: PASS (attribution block names every route)
    - idempotent re-ingest: PASS (3 found, 0 new, nothing written)
    - paste stripped of `Match to` headers: PASS (skips all 3 with a warning, never guesses)
    - the slimmed extraction from finding 4, end to end: PASS (identical attribution)
    - deck-rename leg: NOT APPLICABLE — needs the Arena client, which this session lacks
  Scenarios 1–8: NOT APPLICABLE (no ingest/deck/presentation file touched).

REGRESSION RISKS:
- `_is_own_earlier_schema` is deliberately WIDER than before. A foreign CSV would now
  have to be built from this module's own column names in its own order to slip through;
  pinned by three tests (reorder refused, missing-core refused, genuinely-foreign
  refused). This is the one change that trades strictness for future migrations working.
- The `_my_team` / `_win_team` row keys are not columns. `write_matches` filters to
  HEADER explicitly, and a test asserts no HEADER entry starts with `_`, but any future
  code that iterates a row's keys expecting columns would see them.
- `matches.csv` gained a column. Verified the consumers: `deck.py audit`'s `Pld` column
  (reads 3/3/2/2/4 correctly), `deck.py feedback` / `swap_outcomes`, and `report` all
  work unchanged — they select columns by name.
- Old behaviour better anywhere? No. `Reason` is untouched, so nothing that read it
  changed meaning; `Ended By` is additive and blank where unknown rather than guessed.

INVARIANTS AT RISK: None.
  INV-01…04 unaffected (no library, derived-file or deck-line change). The deck-file
  write path is untouched — `_write_arena_header` still routes through
  `deck._safe_write_lines`. matches.csv is not an INV-03 derived file, and its write
  still goes through `atomic_write` + the F-02 mirror guard, which was strengthened
  against genuinely-foreign files while being loosened for this module's own history.

NET SCORE: 2 production fixes − 0 new failure modes = 2
  Honest split: only finding 2 describes information the record was ACTIVELY losing this
  month (6 matches' end conditions, incl. deck 15's 2–0 being two concedes), and 2b would
  have fired the moment 2 was written. Findings 1, 3 and 4 are verification-cost and
  robustness improvements — no wrong data was produced by any of them this month.

OPERATOR ACTIONS / DEPLOY:
- Re-copy the extraction recipe on the Arena machine to pick up the `sed` stage (the
  per-session paste command in log-matches.md). The old recipe still works — it just
  produces a paste ~92% larger on its EventSetDeckV3 lines. | BLOCKS DEPLOY: N
- `snapshot.sh` needs NO change and must not be given the sed (see finding 4). | BLOCKS DEPLOY: N
Deploy: N/A — no Deploy Command covers Outcomes/Analysis; data and tooling ship by
commit/push. The dashboard is unaffected (it does not render matches.csv columns).

FOLLOW-ON ITEMS:
- 9 of 15 matches have a blank `Ended By` — their logs predate the retained archive and
  are unrecoverable. Not a defect; noted so a future reader does not read blank as "Game".
- The `--report` per-deck split cannot reach n=20 in any realistic timeframe at the
  current rate (best row is n=4 across 106 decks). The tool's refusal to print a
  percentage is correct; what is missing is an AGGREGATE read, which would reach the
  floor far sooner. Out of scope here, worth a finding of its own.
- Checked and REJECTED, recorded so it is not re-proposed: cross-checking Arena's
  `Format` attribute against the deck's `#: format:`. Deck 15 reports Alchemy in Arena
  against Standard in the repo, which looks like drift and is not — `deck.py legal 15`
  passes clean, the deck simply sits in the client's Alchemy slot and Standard is a
  subset. A check here fires on every such deck.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-57 and docs/gotchas.md [G-57] describe the match record's columns and name
  `My Avatar` / `Opponent Avatar` explicitly. They should mention `Ended By` and why
  `Reason` is kept despite never varying — otherwise the next reader repeats the audit
  that produced this batch.
- docs/cycle-config.md [C-12] DONE in this batch — it carried its own copy of the paste
  command, which is finding 4's scope (the G-13 "written out in eleven places, one of
  them right" trap), so it gained the `sed` stage plus the new expected-output lines for
  findings 1 and 3.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
