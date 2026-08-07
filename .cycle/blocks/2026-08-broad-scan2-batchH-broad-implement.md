---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch H (strategic) — the last batch of the broad-scan-2 priority report.
  H-2 | Decide the twice-replicated creature-cut finding — pre-registered re-test, ONE evaluation
  H-3 | Writer mutation-test layer — prove the write-safety tests fail on a broken writer
  H-4 | G-63 AST scan at the primitive — the alias registry is hand-kept and could not see an
        unregistered loader; scan for them instead
  H-6 | Triage the ten unindexed keywords (K-01), per keyword, with measured deltas
  H-7 | Wire the Sheets round-trip — reachable but unusable; setup preflight, push guard, coverage
  BS3-02 | (found by H-6) the BS2-23 tag fingerprint could never arm itself
  BS3-03 | (found by H-7) push had no shrink guard and no tests; pull created worksheets on READ
  BS3-04 | (H-2's shipped output) the feedback warning asserted a CAUSE that measurement refutes
  H-1 / H-5 | NOT done — see OPERATOR ACTIONS and FOLLOW-ON ITEMS; both are the user's call

Files modified: scripts/check_dfc.py, scripts/tag_synergies.py, scripts/build_pool.py,
scripts/sheets_sync.py, scripts/deck.py, scripts/keyword_baseline.txt, tests/test_check_dfc.py (new),
tests/test_writer_mutations.py (new), tests/test_build_pool.py, tests/test_sheets_sync.py,
tests/test_recommendations.py, CLAUDE.md, README.md, docs/gotchas.md, .claude/commands/ingest.md,
.cycle/blocks/2026-08-creature-cut-retest.md (new), decks/17-spectrum/deck.txt,
decks/40-paradox-drive/deck.txt, card-pool.csv, card-mana.csv, card-library.csv, card-pool.build,
gallery.html

CHANGES:
H-4 | scripts/check_dfc.py, tests/test_check_dfc.py | New guard (4), REGISTRY COMPLETENESS. Guard (3)
  behaviorally verifies every loader in `_ALIASED_LOADERS`; it is blind to a loader nobody listed, and
  every G-63 index bug so far (load_keywords/BS-12, reconcile's pool map/BS-16) was exactly that. An AST
  scan now finds pool-shaped name-index builders structurally — a function that names the pool, reads it
  with a DictReader, and stores into a dict under a key derived from `Card Name` — and each must be
  registered or allowlisted WITH A REASON. Measured at introduction: 9 builders, 0 false positives, 1
  unregistered (`deck._legality_of`, a fourth private copy of the alias loop that nothing verified; now
  registered via a new optional args_factory, since it is the only non-zero-arg loader). The key-derived
  clause is what keeps it honest: `suggest_scored`/`suggest_lands` iterate the same rows building
  `theme_w`/`deck_curve` and must NOT be flagged. Also: `_seg()` slices pre-split lines instead of calling
  `ast.get_source_segment` per function — the first version took 39s on a gate check_all runs every time;
  it is now 0.22s. 17 tests, including the mutation pair (drop a registry entry → the gate fires).
H-3 | tests/test_writer_mutations.py | 15 mutation tests over lib.atomic_write / backup_path /
  latest_backup / write_rows. test_lib.py already asserts what the writer DOES; nothing asserted those
  assertions would FAIL if it stopped. Each property runs against the real writer (must pass) and a mutant
  with one safety step removed (must fail): no temp file, backup-after-replace, no copymode, no cleanup on
  failure, a fixed backup name, mtime-based backup selection, and the F-02 schema guard disabled. Every
  mutant is a bug this writer actually had, cited in lib.py's own comments. fsync-before-replace is pinned
  as a call-ORDER assertion with that weakness stated in the docstring — a power cut is not simulable.
H-6 | scripts/tag_synergies.py, scripts/keyword_baseline.txt, CLAUDE.md, docs/gotchas.md | Seven of the
  ten K-01 keywords themed, three deliberately left, each decided on its own evidence. vivid→multicolor,
  payoff (17/17 gain; the same family as `converge`, and the reason K-04's fixer overlay was blind to Bloom
  Tender); job select→equipment, tokens (only 2/16 gain — K-02's tail at full strength); opus→spellslinger,
  payoff; increment→counters, spellslinger; infusion→lifegain, payoff; disappear→sacrifice, aristocrats
  (morbid's exact pair; blink adjacency deliberately NOT tagged, since blink erases the +1/+1 counters half
  these cards accumulate — G-42); paradigm→exile cast, card advantage (K-07 by definition). LEFT: `jump`,
  because Scryfall lists it on all 11 Jump-start cards and only 2 cards genuinely have it — a keyword's
  reported COUNT is not its population; `tiered`, a cost SHAPE whose six cards span burn/bounce/lifegain/
  pump and already tag correctly from text; `triple`, unchanged. Baseline regenerated (23 → 13 entries).
BS3-02 | scripts/build_pool.py, tests/test_build_pool.py | An ABSENT tag fingerprint now rebuilds ONCE
  instead of reusing. BS2-23 added the fingerprint so a tag edit defeats the freshness reuse, and gave a
  legacy two-line stamp a grace clause: unknown → don't force a rebuild. But the reuse path returns BEFORE
  writing a stamp, so the stamp could never ACQUIRE a fingerprint and the escape hatch was permanently
  disarmed. Found the only way it could be: H-6's seven mappings were added, `make refresh` ran, step 2/6
  announced build_pool, check_all went green — and card-pool.csv came back byte-identical. That is BS2-23's
  own bug, inside its fix. 4 new tests, including the pair that makes "once" mean once.
BS3-03 | scripts/sheets_sync.py, tests/test_sheets_sync.py, README.md, .claude/commands/ingest.md | H-7.
  (a) `pull` no longer creates the worksheet it fails to find — a typo'd `--worksheet` added an empty tab
  to the operator's spreadsheet and then reported it empty, i.e. a READ mutating the remote document; the
  blanket `except Exception` also turned auth failures into add_worksheet attempts. It now lists the tabs
  that do exist. (b) `push` gained pull's shrink guard: it CLEARS the tab, so a short local CSV would
  destroy the copy you would recover FROM. (c) New `sheets_sync.py check` — reports all four setup parts
  plus the share, and writes nothing. This is why the round-trip was reachable but unused: every failure
  looked the same from outside. (d) `push` had ZERO tests, including none over the RAW value_input_option
  that keeps a `=`-leading cell from running as a live formula (audit F10). 12 new tests.
BS3-04 | scripts/deck.py, tests/test_recommendations.py, .cycle/blocks/2026-08-creature-cut-retest.md |
  H-2. Pre-registered, one evaluation. M1 (normalize `fit` by tag count — the mechanism the tool's own
  warning ASSERTED) is REFUTED: creature agreement 52.6→68.4%, noncreature 83.3→**51.3%**. The
  unnormalized sum is load-bearing for the segment that works. M2 (exclude creature-subtype tags, already
  paid for by `min(tribal,6)`) misses both criteria (+5.3 vs +8; −2.5 vs −2) and is recorded as
  UNDERPOWERED, not rejected — the harness resolved 38 creature rows against the 103 planned. The warning
  text and `recommendation_segments`' docstring now state the measured asymmetry as an observation and
  name both rejected hypotheses, instead of pointing the reader at a change that would make the tool worse.
G-27 | decks/17-spectrum/deck.txt, decks/40-paradox-drive/deck.txt | The H-6 retag moved two central-theme
  counts; both `#: tier:` figures re-grounded (19→21, 18→19) in the same commit that moved them.

TEST RESULTS: passed — 1078 (was 1031, +47). `check_all` "All invariants hold. ✓" with ZERO soft
warnings. `check_docs` OK. `check_dfc` OK. `check_commands` OK (34 subcommands, 33 scripts). The 7
blank-Card-Text validate warnings are K-11 vanilla creatures, expected and pre-existing.
Two test failures were caused by this session and fixed as part of it, both test doubles encoding OLD
behaviour — `test_build_pool._stamp` wrote a pre-BS2-23 two-line stamp by default, and
`test_recommendations` pinned the exact wording of the warning BS3-04 refuted.

REGRESSION RISKS:
- `check_dfc._worksheet`-style signature change: `sheets_sync._worksheet` gained a `create` kwarg. The one
  in-repo double was updated; no other caller exists.
- `_ALIASED_LOADERS` entries may now be 3- or 4-tuples. The single consumer unpacks `entry[:3]` with an
  optional 4th; `tests/test_check_dfc` pins both shapes.
- `build_pool` behaviour change: anyone with a pre-BS2-23 stamp pays ONE full pool rebuild (~5 min +
  Scryfall). Intended, announced in the printed message, and it happened here.
- The seven keyword mappings re-tagged ~85 pool cards, which moves theme weights roster-wide. Measured
  effect on the roster: two stale tier figures, both re-grounded. No tier floor moved, no deck re-graded.
- `push`'s shrink guard adds one `get_all_values()` call before clearing. On an empty/unreadable tab it
  falls back to "no guard needed" rather than blocking a legitimate first push.

INVARIANTS AT RISK: None. INV-01/02/03 verified after the pool + mana rebuild; INV-04 re-verified after
the two deck-file edits. The writer mutation layer only ADDS assertions over the paths INV-01/03 rest on.

NET SCORE: 8 − 0 = +8
(H-2 counts as one — it shipped a prose correction, not a model change. BS3-02 and BS3-03(a) are the two
that would certainly have fired in ordinary use this month: the first DID fire, silently, during this very
batch; the second fires on any typo'd `--worksheet`. No new failure modes — the three behaviour changes
(rebuild-once, push floor, read-never-creates) all report what they want and carry an escape hatch.)

OPERATOR ACTIONS / DEPLOY:
- H-1: log ten real matches. `matches.csv` is still absent and 34 decks carry unfalsifiable provisional
  tiers. This is the one Batch H item no amount of code can do — it needs games played and a `Player.log`.
  Route: `/log-matches`. | BLOCKS DEPLOY: N
- H-7 setup: `pip install -r requirements.txt`, a service-account key, `MTGA_SHEET_ID`, and sharing the
  sheet with the key's `client_email`. Verify with `python3 scripts/sheets_sync.py check` — it now names
  each missing part. | BLOCKS DEPLOY: N
- Perceptual halves of Regression Scenarios 5–8 still need a person at a browser. | BLOCKS DEPLOY: N
Deploy: commit/push is the deploy. The dashboard rebuilds from pages.yml on push to main; `card-pool.csv`
and `card-mana.csv` moved, so the published dashboard will pick the new tags up on that rebuild.

FOLLOW-ON ITEMS:
- H-5 (deck 49 Route A rotation-proofing) NOT done — the user said to hold off, and nothing in this batch
  changes that. Still measured and queued.
- The H-2 harness defect, written down so a re-test starts ahead: the snapshot selector matches
  `cardname in body`, which hits a `#:` comment, so it can pick a version where the card is discussed but
  not played. ~124 of 266 rows dropped that way. Match PARSED lines (`parse_deck_file`) instead. M2
  deserves a rerun at full n; M1 does not.
- BS2-07's header-consumer sweep remains the standing G-63 leftover: `rank_cut_candidates` /
  `_castability` / `_weakest_cut` still compare raw lowercase names against `#: protect:` /
  `#: uncastable-ok:` while `header_card_staleness` joins on `_ms_key`. Zero live instances.
- `deck._printing_index` and `deck._legality_of` alias front faces IN-PASS, which `lib.alias_front`'s
  docstring warns against. Both are correct today only because the real row's assignment is a direct
  `idx[k] =` that overwrites the alias; a refactor to `setdefault` would break them silently. Now at least
  both are behaviorally covered by the registry. Not converted here — out of scope, and the conversion has
  a real semantic wrinkle (`known_printings` shares a set object where the hand-rolled version unions).
- `check_dfc`'s builder scan skips `check_*.py`, on the reasoning that a gate's scratch index is not a
  consumer surface. Stated in the code as a residual rather than left implicit.

DOCUMENTATION UPDATES NEEDED:
- Applied in this commit, not deferred: K-01 rewritten (the ten-keyword list was the rule's whole content
  and is now false), G-18 given the BS3-02 clause, G-09 given the two refuted hypotheses, G-63 given the
  new scan. docs/gotchas.md long forms for all four. README's Sheets section. ingest.md's Sheets row.
- Three CLAUDE.md bullets breached check_docs' 15-line cap while doing it; each was compressed by moving
  EVIDENCE to docs/gotchas.md, and the `cuts` annotation evidence (the four one-mana spells, Cat-Gator)
  was written into G-09's long form rather than deleted.
- Not needed: ROADMAP still lists "theme the unindexed keywords" as Tier 1; seven of ten are done and the
  remaining three are decided-against, so that entry should be closed on the next /roadmap.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
