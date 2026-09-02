---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- H1 | `granted_keywords` covered only the 12 EVERGREENS, so a card that GRANTS any other
       keyword was untagged while a card that HAS it was tagged (G-80's own asymmetry,
       one keyword over)
- H2 | `--audit-rationale` could not see COLOUR-SOURCE claims at all — no figure family
       resolves against the manabase, so such a claim could rot indefinitely (G-27)

Files modified:
  scripts/tag_synergies.py, scripts/deck.py, scripts/check_patterns.py,
  tests/test_ingest.py, tests/test_deck.py,
  CLAUDE.md, docs/gotchas.md,
  decks/26-iron-forge/deck.txt, decks/40-paradox-drive/40a-exponential-drive.txt,
  decks/68-frog-sage/68b-warren.txt,
  card-library.csv, card-pool.csv, card-pool.build, card-mana.csv, gallery.html,
  image-manifest.json, dashboard.html

CHANGES:

H1 | scripts/tag_synergies.py | `_GRANTED_KEYWORDS` extended by five: ward, convoke,
  affinity, prowess, flash. Chosen on TWO measured tests rather than by sweeping in every
  keyword Scryfall names — each is (a) already a live pool tag, so no new theme is
  introduced and the grant resolves through the same `KEYWORD_THEMES` table as a native
  keyword, and (b) has real granted instances in the pool. `cascade` passed (a), failed
  (b) with zero granting cards, and was deliberately LEFT OUT: an unexercised whitelist
  entry is one nobody can check.
  FOUND the ordinary way — `check_themes` flagged Dazzling Theater ("Creature spells you
  cast have convoke") and `tags_for` returned only ['Room'].
  MEASURED: 55 pool cards newly tagged (ward 34, convoke 8, affinity 5, flash 5,
  prowess 3). Every one read back; all genuine grants. Exactly ONE is the *cares-about*
  rather than *grants* shape (Joyful Stormsculptor's "a spell that has convoke"), which
  is a property of the pre-existing `(gains?|have|has|gets?)` reader, not of the widening,
  and tagging a convoke payoff `convoke` is the call K-03 makes elsewhere.
  K-14 DIFF: **0 decks moved a role count, 0 moved a central-theme count, 0 tier floors
  moved** — as predicted, since `role_tally` reads TEXT and only cuts/suggest/centrality
  consume tags. Tags regenerated through `make refresh` and VERIFIED in both stores per
  K-10 (library AND pool now read `Room; convoke; go-wide; ramp`).

H2 | scripts/deck.py | `_RATIONALE_FIGURES` gains one pattern per colour keyed
  `sources_W`…`sources_G`, and a new `_figure_lookup(vec, cards, carddata)` returns the
  quality vector PLUS those counts. Widening the LOOKUP rather than adding a parallel scan
  is the load-bearing choice: every suppression the figure loop already applies
  (other-deck id, roster deck name, population subject, history, percent/draw misreads) is
  reused instead of reimplemented. Wired into BOTH figure loops — `rationale_staleness`
  and `note_figure_staleness` — so the `#: tier:` and `#~ note:` scans cannot drift.
  Two guards, measured on the roster rather than invented: DELTAS ("wanting roughly +8
  white sources", deck 19) and WANTS (`deck.py consistency` prints "want 13 G sources
  (have 8, +5)" and that line gets pasted in verbatim).
H2 | scripts/deck.py | `_OTHER_DECK_POSS_RE` + `_other_deck_ids()`. The sweep surfaced a
  false positive the existing suppressions structurally could not see: `_OTHER_DECK_RE`
  requires the literal word *deck* before an id, but the prose's commoner idiom is the
  POSSESSIVE — `42's`, `68a's` — at **35 roster occurrences** against a handful of the
  explicit form. Deck 68b's archetype reads "{1}{G}{G}{G} on 68a's 12 green sources", a
  claim about ANOTHER deck, and it flagged against 68b's own 17. The possessive is gated
  on the id being a REAL roster id so it cannot eat ordinary prose.
  ROSTER DIFF: 4 flags → 3, the suppressed one being exactly that false positive and
  nothing else moving. The 3 survivors were all genuinely stale and were re-grounded:
  deck 26 (`#~ note:` 13 red sources / 69.6% against a live 15 / 78.1% — recomputed, not
  guessed), deck 40a (16 → 14 G), deck 68b (15 → 17 W).
H2 | scripts/check_patterns.py | Both new prose patterns registered in `_EXCLUDED` with
  reasons. The gate HARD-FAILED the build until they were, which is it working as designed
  (G-53).

TEST RESULTS: full pytest suite green (exit 0). `check_all` all invariants hold;
`check_patterns` 293 patterns live; `check_commands` OK; `check_docs` OK; `check_roles`
no new zero-role cards.
  12 new tests, ALL mutation-checked (reverted each fix, watched them fail, restored):
    tests/test_ingest.py  : 4 in TestGrantedKeywordsAreTagged — the granted non-evergreen,
                            the "already a live tag" invariant, the cascade decision, and
                            the opponent/negation guards still holding for the new five
    tests/test_deck.py    : 5 in TestColourSourceFiguresAreAudited, 3 in
                            TestPossessiveDeckCitationSuppression
  TWO PROCESS FAILURES WORTH RECORDING, both caught before they shipped:
  1. H1's first mutation run SURVIVED — the existing `-k grant` tests are shape/order
     tests that pass with the evergreen-only list. The fix was unpinned until the four
     new tests were written. A passing suite is not evidence a new behaviour is covered.
  2. Inserting the H2 test classes mid-file RE-PARENTED the remainder of
     `TestClassifyRoles` into the new class (16 methods silently moved). Caught by
     diffing the class map, fixed by re-homing the block at EOF. Insert test classes at a
     class boundary, never before an arbitrary method.

REGRESSION RISKS:
- `_other_deck_ids` LOOSENS a suppression, so in principle it could hide real staleness.
  Measured against a full before/after roster capture: exactly one flag disappeared, and
  it was the known false positive. Residual, small and honest: a possessive of a
  single-digit number that happens to be a deck id ("the 4's slot") would suppress —
  measured at ONE roster occurrence, itself a genuine deck reference.
- H1 widens a whitelist, whose default failure is over-counting (BS2-06). All 55 newly
  tagged cards were read back individually; no false positive on the grants axis.
- `_figure_lookup` swallows any exception from `deck_color_sources` and returns the plain
  vector, so a deck whose sources cannot be priced skips the check rather than guessing.

INVARIANTS AT RISK: None. No writer, schema or derived-file path changed. The derived
stores were rebuilt through `make refresh` (the Makefile, per G-13) rather than by hand,
and INV-03's per-file schemas are untouched.

NET SCORE: 2 production fixes − 0 new failure modes = 2
  (a) H1 fired this month — it is why Dazzling Theater carried no convoke tag on the day
      it was crafted. H2 fired this session: I made a stale colour-source claim in deck
      78's tier block and the guard passed it.
  (b) Neither introduces a new failure mode; the one loosening is bounded, measured, and
      its residual is recorded above.

OPERATOR ACTIONS / DEPLOY:
- None.
Deploy: dashboard is the one deployed artifact — `.github/workflows/pages.yml` rebuilds
and publishes it on push to `main`. The committed snapshot was refreshed.

FOLLOW-ON ITEMS:
- The colour-source computation exists THREE times: inline in `cmd_mana`, inline in
  `cmd_consistency`, and as `deck_color_sources`. They agree today (verified: all three
  give deck 78 W13/U8/G10) and nothing checks that they keep agreeing — the shape
  `check_agreement` exists to catch. Out of scope here.
- H3 from the same scan, measured and NOT treated as a defect: 272 distinct craft targets
  in deck files are absent from the 186-row wishlist, so `--rank`/`--budget` plan against
  a subset. The wishlist is a CURATED list and deck files include aspirational builds, so
  these are two systems with different purposes. The narrow finding is that
  `--audit-targets` checks wishlist→deck and nothing checks deck→wishlist; whether that
  view should exist is a design call for the user.

DOCUMENTATION UPDATES NEEDED:
- DONE in this change: G-80 extended (CLAUDE.md bullet + docs/gotchas.md long form) with
  the widening, its two selection criteria, the cascade decision and the 0-floor diff;
  G-27 extended with the manabase axis, the two guards and the possessive-citation fix.
- DONE: K-09's quoted pool-blank figure corrected 342 → 340, which H1 moved by tagging two
  previously-blank cards. `check_docs` caught this — the figure-drift check earning itself.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
