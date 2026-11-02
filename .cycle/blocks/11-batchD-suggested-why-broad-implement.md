---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch D (match-digest decision 2) — a `Suggested Why` column filled by the three pre-registered rules (keep / screw / flood), printed with evidence, never confirmed without the owner; `--review` and `--accept` (through the `--annotate` writer); agreement measured with a 20-loss floor. The extractor was extended so screw/flood are computable (owner's choice, 2026-11-02, after the stop-and-ask below).
Files modified: scripts/mtga_extract.sh, scripts/parse_matches.py, .claude/commands/log-matches.md, tests/test_parse_matches.py, .cycle/STATE.md, .cycle/blocks/11-batchD-suggested-why-broad-implement.md

STOP-AND-ASK: the plan assumed per-turn land counts the game lines did not carry. "cards" keeps one entry per grpId, so four Islands read as one, and there was no per-turn count. Only `keep` was computable. On the 34 recorded losses with game facts, no mulligans were recorded, so `keep` would have suggested nothing. The owner chose to extend the extractor.

CHANGES:
D-1 | scripts/mtga_extract.sh | Tracks zones (`zoneId`, `type`, `objectInstanceIds` — the full list of each changed zone) and every card object (controller : owner : is-land). On each new turn it snapshots each seat's lands on the battlefield. Each game line gains:
  - "lands": per seat, the land count at the end of every turn, comma-separated, blank where unknown;
  - "seen": per seat, "lands/cards" across hand, battlefield, graveyard and exile at game end.
  It counts zone MEMBERSHIP, so each physical card is counted once. It stores nothing when no battlefield zone was ever seen, so a parse failure reads blank, not 0 (a 0 would make every loss read as screw). Only POSIX awk constructs are used (index/substr/split, local arrays, split("", a)).
D-2 | scripts/parse_matches.py | Changes:
  - "Suggested Why" appended to HEADER; earlier files migrate through `_is_own_earlier_schema`, unchanged.
  - The rules are module constants with their 2026-09-25 registration date: keep = mulliganed to ≤5; screw = ≤2 lands at the end of my 4th turn (global turn 7 on the play, 8 on the draw, only if the game reached it); flood = lands ≥60% of cards seen over ≥7 of my turns.
  - `suggest_loss_reason` picks the first rule that fires in the first lost game (Bo3 aware). It writes "none (no rule fired)", or "none (… not readable — the game line predates the 2026-11-02 extractor)" when the line lacks the fields.
  - `apply_game_details` fills the cell once, into a blank cell, on losses only, and never touches Loss Reason.
  - `_print_loss_prompt` shows the suggestion.
D-3 | scripts/parse_matches.py | `--review` lists every loss without a confirmed reason, numbered, with its suggestion or why it has none, then the agreement block. For each rule it shows fired / agreed / named-but-silent, with rates only from 20 confirmed losses. `--accept [id …]` confirms the suggested word through `annotate()` (dry run unless --apply, prefix ids, a "none" is never accepted).
D-4 | .claude/commands/log-matches.md | The extractor's embedded copy is re-synced (the test pins it byte-for-byte). Stage 1d gains the suggestion step, the rule that an unread suggestion must never be accepted (it inflates the agreement figure), and the re-install note.
D-5 | tests/test_parse_matches.py | 15 new tests:
  - the extractor counts lands by zone (four copies count as four) on a fixture with real zone shapes;
  - each rule at, under and over its threshold, on the play and on the draw, and a game that ended before my turn 4;
  - wins are never suggested; an old line says what it could not read;
  - the column is written but Loss Reason is untouched, and a hand-set cell is kept;
  - --accept dry run, then apply, and "none" is never accepted;
  - agreement counting;
  - schema migration;
  - a log without zones records blanks, not zeroes.

TEST RESULTS: full pytest suite passed (run before the D-1 blank-not-zero guard; test_parse_matches.py and check_all re-run green after it). check_all OK with 5 soft.
REGRESSION RISKS: The matches.csv header gains a column on the next write (migration path tested). Game lines grow by two small fields. Older parsers ignore unknown keys, and parse_game_facts reads json.
INVARIANTS AT RISK: None (matches.csv is written only through write_matches + atomic_write).
NET SCORE: 1 production fix (the loss-reason column is still nearly empty: 2 of 122 losses; this gives every new desktop loss a starting point) − 0 new failure modes = 1. Residual risk is recorded below instead of being counted.

OPERATOR ACTIONS / DEPLOY:
- Re-run /log-matches Stage 0's install block on the Mac so ~/mtga-logs/extract.sh carries the land counts. Until then, new games read `keep` only. | BLOCKS DEPLOY: N
- After the first paste with the new extractor, check one suggestion against memory. The zone field names come from fixtures modelled on 17Lands' parser, not from a real log. | BLOCKS DEPLOY: N
Deploy: N/A — nothing on Pages reads the new column.

FOLLOW-ON ITEMS:
- BSD awk (the Mac's) is untested here: the container has only mawk. Constructs were kept POSIX. The first real run on the Mac is the test.
- The 32 already-recorded losses with game facts carry no suggestion. Their facts were never stored raw, so only `keep` could be backfilled, and every one recorded 0 mulligans.
- `--report` does not yet show the play/draw, mulligan and colours-faced pooled sections from the match-digest plan (out of Batch D's scope).

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-74 (Suggested Why, --review/--accept, the 20-loss floor), docs/gotchas.md G-74 long form (rules, extractor zone counting, the stop-and-ask), README parse_matches lines, C-02 data note, scenario 9 (check a suggestion on the first real paste), docs/systems-map.md §5b.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
