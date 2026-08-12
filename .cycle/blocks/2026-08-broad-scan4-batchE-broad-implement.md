---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- E2 | BUILT — join `recommendations.csv` to `matches.csv`: the only signal these models cannot influence
- E1 | NOT IMPLEMENTABLE — owner-paced (needs games played). Pipeline is armed; A1 is now installed.
- E3 | NOT IMPLEMENTABLE — operator (Google service-account credentials).
- E4 | NOT BUILT — measurement produced instead; the card/commander choices are taste.
- E5 | NOT WRITABLE BY DESIGN — evidence produced; `#: tier:` letters are never auto-written.

Files modified: scripts/deck.py, tests/test_recommendations.py

CHANGES:

E2 | scripts/deck.py, tests/test_recommendations.py | `swap_outcomes(rows, matches)` joins
  the two ledgers, and `_print_swap_outcomes` adds an Outcomes section to `deck.py
  feedback`. Both ledgers have existed for a cycle with nothing connecting them, so every
  ranking model here is graded on its own argument plus an agreement rate CLAUDE.md itself
  calls contaminated (the human reads the shortlist before deciding). An outcome is the one
  signal the models cannot influence.

  THE SPLIT IS DELIBERATELY COARSE — per DECK, at its FIRST recorded swap. A per-swap
  before/after is the interesting analysis and is not honest at any volume this record will
  reach soon: a deck accumulates many swaps whose windows overlap almost completely, and
  attributing a result to one of four changes made the same week is a story, not a
  measurement. Draws and unreadable Result cells decide nothing but still count as games
  played; an unattributed match (blank Deck — the parser refusing to guess a seat) joins to
  nothing rather than being borrowed.

  IT REFUSES TO READ, which is the honest output today and the reason to build it now
  rather than later. Live: 365 swaps, 9 matches, 8 attributed, 3 decks with both, largest
  post-swap sample n=4 against a threshold of 20. The section prints the coverage so the
  distance from signal is visible, and says explicitly that no outcome is reported and none
  should be inferred. When volume arrives the analysis is already in place.

  REPORT-ONLY, STRUCTURALLY. `tests/test_recommendations.py`'s existing scan of the seven
  scoring functions was extended from `load_recommendations`/`RECS_CSV` to also ban
  `swap_outcomes`, `MATCHES_CSV` and `load_match_counts`. An outcome is the most tempting
  thing in the project to feed back into a ranking — it looks like ground truth — and doing
  so would both destroy the bounded-and-anchored property `check_suggest` holds AND make
  the models chase an 8-match sample. 5 new behavioural tests.

E1 | (no change) | Owner-paced. The pipeline now runs end to end and A1 (the launchd
  rolling archive) is installed as of this session, so the only missing input is games.
  This is the project's real bottleneck and E2 exists to be ready for it.

E3 | (no change) | Needs a Google service-account key, a sheet id, and the sheet shared
  with that account — none creatable from here. `python3 scripts/sheets_sync.py check`
  names every missing part and writes nothing.

E4 | (no change) | MEASURED, not built, and the measurement changes the estimate: all three
  planned conversions are at **distance 0** on `deck.py brawl` — already singleton and
  on-identity — so each is a `#: format: Brawl` + `#: commander:` header plus the commander
  card, not the ~20-card singleton rebuild the "M each" estimate assumed.

      dist  deck                     commander the tool picks
         0     4 Quantum Realm       Ant-Man, Colony Commander (GU)
         0    46 Lightwing           Aerith Gainsborough (W)
         0    11 Villainous          Bullseye, Death Dealer (BR)

  NOT BUILT because the remaining decisions are exactly the taste ones. The tool picks
  Aerith for 46 where NEXT-SESSION §4b records the user wanting **Delney**; the user has
  already flagged that Bullseye's **BR identity sits against a mono-B deck** and that a
  mono-B legend would be tighter; and each conversion needs one card cut to make room for
  the commander. The Player Profile is creative-leaning and this repo records two swaps
  applied and then reverted on the user's challenge. `/draft-deck` or `/add-deck` with the
  user in the loop is the right vehicle; 40-brawl is the worked example.

E5 | (no change) | Evidence produced; the letter is a human competitive judgment CLAUDE.md
  says is NEVER auto-written (design constraint).
  * **Deck 19 Bird Brain** — claimed B, metrics floor **A**, interaction 5 / card-adv 2,
    0 uncastable. `tier` reports "possibly UNDER-graded: even the (under-rating) metrics
    floor is A. Consider re-grading up." This is the one genuinely awaiting a call.
  * **Deck 21a Gastromancer** — claimed B, floor **A**, interaction 10 / card-adv 5. The
    guard does NOT flag it: "deliberately conservative — B sits below the A floor and the
    rationale argues why." So the K-14 card-advantage move (3→5) that NEXT-SESSION cites as
    the reason to re-grade has already been absorbed by the written rationale. Nothing is
    wrong here; re-grading is optional rather than owed.

TEST RESULTS: passed. Full suite green; `check_all.py` all invariants hold with **ZERO soft
warnings**; docs, commands and agreement gates all OK (agreement still 7 questions).

REGRESSION RISKS:
- `cmd_feedback` gained a section, so its output is longer. `tests/test_recommendations.py`
  asserts on substrings rather than whole output, and the small-sample test still passes;
  nothing parses `feedback`.
- `_print_swap_outcomes` reads matches.csv through `parse_matches.load_matches` inside a
  try/except that degrades to "no matches.csv yet". matches.csv is deliberately NOT an
  invariant (a repo with no logged games is healthy), and this must not become the first
  thing to require one — the swallow is intentional and mirrors `load_match_counts`.
- The new structural assertions could fail a FUTURE legitimate refactor that moves a
  scoring function's body somewhere that mentions these names. That is the intended cost:
  the test has to be deleted deliberately, which makes the decision visible.

INVARIANTS AT RISK: None. No CSV, deck file or derived artifact was written — `git status`
shows only the two source files. matches.csv and recommendations.csv are read, never
written. No new script or subcommand, so `check_commands` coverage is unchanged.

NET SCORE: 1 production fix − 0 new failure modes = 1
(E2 is capability rather than a bug fix, and would not have "fired" this month — it reports
that there is nothing to report. Counting it as 1 is generous in kind and honest in number;
the other four items were not implementable by me and are not counted either way.)

OPERATOR ACTIONS / DEPLOY:
- **E1 — play games.** The single highest-value input to the project. 8 attributed matches
  against a 20-per-deck read floor; 34 decks carry provisional tiers graded on internal
  consistency alone. A1 is installed, so nothing is being lost any more. | BLOCKS DEPLOY: N
- **A2 — `import_collection.py` against a full tracker export.** Still outstanding, still
  precedes any wildcard spend. | BLOCKS DEPLOY: N
- **A3 — the two visual checks** (gallery light mode; keyboard walk of the two repaired
  dashboard controls, which is the only coverage for the C2 class). | BLOCKS DEPLOY: N
- **E3 — `sheets_sync.py check`**, then the credential setup it names. | BLOCKS DEPLOY: N
- **E4 — decide the three commanders** (Delney vs Aerith for 46; a mono-B legend vs
  Bullseye for 11; Ant-Man for 4), then run `/draft-deck`. | BLOCKS DEPLOY: N
- **E5 — deck 19's tier letter.** Floor A, claimed B, flagged. | BLOCKS DEPLOY: N
- Still pending from Batch C/D: **one full pool rebuild** on the next `make refresh`.
Deploy: N/A for this batch — nothing here changes the dashboard, gallery or any published
artifact. Data + local tooling ship by commit/push.

FOLLOW-ON ITEMS:
- E4's real remaining cost is one decision per deck, not a rebuild. Worth re-estimating
  from M each to S each once the commanders are chosen.
- `cmd_check` joins comma-containing card names with `", "` (carried from Batch A&B).
- `launchctl load` deprecated on macOS 11+ (cosmetic; A1 is installed).
- C2 (a11y scan over the generated pages) remains open with its measurement attached.

DOCUMENTATION UPDATES NEEDED:
- README's `feedback` section describes the ledger and the agreement rate; it should
  describe the Outcomes section and, more importantly, WHY the split is per-deck and why
  the read is refused.
- CLAUDE.md G-56 says the ledger "is REPORT-ONLY and must stay so" and lists the scanned
  functions; it should record that outcomes are now in that ban and why they are the most
  dangerous member of it.
- G-57's "read the record with restraint" is the governing rule for the new section and
  should point at it.
- Carried from Batch C&D and still unapplied: G-54's enforcement pointer, G-72's C2
  measurement, G-18/K-10's fingerprint description, and striking G-02's residual 2.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
