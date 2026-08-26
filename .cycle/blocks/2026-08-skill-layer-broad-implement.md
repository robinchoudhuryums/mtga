---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- SK-2 | `/draft-deck` prescribed a hand edit as the remedy for `resolve --check`
  failures — the operation G-65 forbids and G-77 was written about — while
  `resolve --fix … --apply` had shipped this cycle as exactly that remedy and was
  referenced by no skill.
- SK-3 | `/ingest` and `/refresh` write canonical + derived data and had NO commit
  step at all; `/add-deck` carried its own one-line commit instruction instead of
  the shared tail. CLAUDE.md asserted the tail was universal ("edit that one file
  to change the commit discipline for all") while it covered 5 of 12 skills, and
  named `/add-cards` — which writes nothing — as one of its users.
- SK-4 | `/roster-review` step 3 ran `deck.py wildcards` without `--dedup`, the
  cross-deck union its own heading asks for, and its rationale text quoted a deck
  count that had rotted (63 against a live 116).

Files modified:
- .claude/commands/draft-deck.md
- .claude/commands/add-deck.md
- .claude/commands/ingest.md
- .claude/commands/refresh.md
- .claude/commands/roster-review.md
- docs/verify-commit-tail.md
- CLAUDE.md

CHANGES:
SK-2 | .claude/commands/draft-deck.md | Stage 4 step 0 now names `resolve --fix NN`
  (dry run) then `--fix NN --apply` as the repair, states that it preserves qty,
  name and trailing comment verbatim with a `.bak` + INV-04 re-check, and says
  outright never to retype the printing fields by hand. Kept the incident (eleven
  wrong collector numbers across decks 76/77) and added why the old wording was a
  hazard rather than merely incomplete.

SK-3 | .claude/commands/ingest.md | New "Stage 5 — Commit", citing
  docs/verify-commit-tail.md and naming what an ingest actually rewrites
  (card-library.csv, card-mana.csv, card-pool.csv, gallery.html, card-wishlist.csv
  when reconcile_crafts prunes). States explicitly that the Stage 3 fit pass is NOT
  part of it — it proposes and writes no deck file.
SK-3 | .claude/commands/refresh.md | Added a closing bullet: commit what the rebuild
  rewrote, staging only files that actually changed (a reused pool per G-18
  legitimately changes nothing), and say so rather than committing an empty diff.
SK-3 | .claude/commands/add-deck.md | Step 7 replaced its own commit instruction with
  the shared tail, spelling out the four rules it had been missing.
SK-3 | docs/verify-commit-tail.md | Header now enumerates the eight real writing
  skills instead of two, records why the old list hid the gap, and requires a new
  writing skill to be added here AND to cite this file in the same change.
SK-3 | CLAUDE.md | Corrected the "All end with the shared verify+commit tail"
  sentence: measured coverage (5 of 12), the three skills that lacked it, why
  `/add-cards` is a legitimate non-user, and the `.cycle/NEXT-SESSION.md` step that
  the parenthetical had never listed.

SK-4 | .claude/commands/roster-review.md | Step 3 now runs `wildcards --dedup` and
  explains the two columns, which are different questions and were both readable as
  "copies needed": Decks is how many decks one card unblocks (fungible — a Decks 3
  card is ONE craft, per CLAUDE.md's shared-collection rule), Copies is the
  shortfall, i.e. the most any single deck needs minus total owned across printings.
  Verified against the live tool before writing the claim. The stale "across 63
  decks" is now "across the whole roster" — a bare present-tense figure in prose is
  the exact class G-04/G-26 gate for in deck files and nothing gates in skills, so
  the fix is to remove the number, not to bump it to 116 and have it rot again.

TEST RESULTS: passed.
- `python3 scripts/check_all.py` — All invariants hold. ✓ (1 pre-existing soft
  warning: 4 dead library searches, G-75, unrelated)
- `python3 -m pytest -q` — 1493 passed, 0 failed
- `python3 scripts/check_commands.py` — OK, 34 subcommands + 33 scripts reachable
- `python3 scripts/check_docs.py` — structure OK, 105 anchors linked. Two
  PRE-EXISTING figure-drift warnings, neither touched by this work: K-09 pool
  blanks (CLAUDE.md 371 vs live 342) and C-02 matches.csv rows (62 vs live 66).

REGRESSION RISKS: None to code — every file changed is Markdown prose. The one
behavioural consequence is intended and worth naming: `/ingest` and `/refresh` now
END IN A COMMIT where they previously ended in a report, so a session running
either will produce a commit it did not before. That is the fix, but it means a
`/refresh` run purely to inspect derived output will now be asked to commit; the
refresh bullet handles it by requiring `git status` first and saying plainly when
nothing changed rather than committing an empty diff.

None of the 10 VENDORED skills were touched (they must not be edited locally —
only re-synced via `/sync-commands`); all 7 modified files are project-specific or
project docs.

INVARIANTS AT RISK: None. No CSV, deck file, derived artifact or writer was
touched. INV-01…06 are untouched by construction. The `check_commands.py`
coverage gate reads the skill files and stays green — references were added, none
removed.

NET SCORE:
SK-2 — (a) would it have fired this month? YES. Two from-scratch drafts this cycle
  (decks 76/77) shipped eleven wrong collector numbers via exactly this hand-edit
  path, and `/draft-deck` was still prescribing it. (b) new failure mode? NO.
SK-3 — (a) YES, and it did: this session opened on a stop-hook complaint about
  uncommitted changes in the repository. (b) NO.
SK-4 — (a) partially. The stale figure is cosmetic; the missing `--dedup` produces
  a worse craft plan every time step 3 runs, by reporting one card three times
  under three decks with nothing saying it is one craft. (b) NO.
Tally: 3 production fixes − 0 new failure modes = 3

OPERATOR ACTIONS / DEPLOY:
- None. | BLOCKS DEPLOY: N
Deploy: N/A — documentation and skill definitions only; no deployed artifact
changed (the dashboard's data pipeline and template are untouched).

FOLLOW-ON ITEMS:
- SK-1 NOT implemented, deliberately deferred to the user: `parse_matches.py`
  `--sync-names` WRITES with no dry run. The sourceless path
  (`parse_matches.py:1654`) hardcodes `sync_deck_names_from_headers(apply=True)`
  while the function's own `apply=` parameter defaults to False and nothing
  reaches it; the with-source path threads `apply=args.sync_names`, so passing the
  flag writes there too. Every other write in this repo is dry-run-then-`--apply`.
  Observed live 2026-08-25: it adopted 10 renames when 2 had been shown to the
  user. The fix changes the meaning of a flag the user already has muscle memory
  for, so it needs their call on which way to take it.
- `/roster-review` runs no per-deck `tier` pass. Judged NOT a gap — the
  tier-mismatch sweep is a soft `check_all` warning and `audit --by-tier` covers
  the sort — but recorded so the absence is on the record rather than assumed.
- Skills name neither the G-75 dead-tutor sweep nor the G-79 unreleased-pool
  sweep. Also not a gap: both run inside `check_all`, which the skills do invoke.
- Deck 35 may want a tier re-grade — its `#: tier:` argues its B from "scattered
  plan (20 central themes)" and the live figure is 13 after the granted-keyword
  tagger fix. The figure was corrected; the LETTER is a human call.

DOCUMENTATION UPDATES NEEDED:
- Two pre-existing figure drifts for `/sync-docs`: CLAUDE.md K-09 pool blanks
  (371 → 342) and C-02 matches.csv rows (62 → 66).
- No new gotcha anchor was minted for this work. The skill-layer lesson is
  recorded where it acts — in `docs/verify-commit-tail.md`'s header and in
  CLAUDE.md's command-provenance paragraph — rather than as a `[G-nn]`, since it
  governs the skills, not the tooling the anchors index. Worth revisiting if a
  second skill-layer finding lands.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
