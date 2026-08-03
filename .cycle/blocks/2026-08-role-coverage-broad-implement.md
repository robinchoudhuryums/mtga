---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- REC-1 | check_roles.py + role_baseline.txt — a delta radar for cards `classify_roles` scores with NO functional role
- REC-2 | batch the known classifier holes into ONE pass (any-colour ramp, Etali-style impulse, cast-from-top) rather than fixing them one at a time

Files modified:
- scripts/check_roles.py (new)
- scripts/role_baseline.txt (new, 367 acknowledged entries)
- tests/test_check_roles.py (new, 5 tests)
- scripts/deck.py (_ROLE_PATTERNS: Ramp / fixing, Card advantage)
- scripts/check_all.py (soft role-coverage warning)
- scripts/check_suggest.py (anchor 15 baseline updated)
- tests/test_deck.py (2 new tests; 1 anchor test re-premised)
- CLAUDE.md (gate count 13 -> 14; Analysis subsystem file list)
- decks/13-earth-kingdom, 24b-boros-midrange, 34-zoologist, 42-blood-price, 52-void-demons (stale card-advantage figures)

CHANGES:
REC-1 | scripts/check_roles.py, scripts/role_baseline.txt, scripts/check_all.py, tests/test_check_roles.py |
  New gate on the keyword_baseline.txt design. Scope is every nonland, non-blank-text card
  in any decks/*.txt; it reports those `deck.classify_roles()` returns nothing for and that
  are not in the baseline. Wired into check_all as a SOFT warning (a genuinely roleless
  vanilla body is a legitimate zero, and it breaks no invariant). Deck-scoped rather than
  pool-scoped on purpose: a pool-wide scan of ~30k cards would be noise, while a card in a
  deck is one some model has already been asked about. Sorted on a total order (G-54)
  because the output feeds a diffed file. Wired into check_all so check_commands (G-53)
  sees it as reachable.

REC-2 | scripts/deck.py |
  Ramp / fixing — the existing pattern was `\{t\}: add \{`, requiring a literal `{` right
  after "add". That reads "{T}: Add {G}" and misses "{T}: Add one mana of any color", which
  is how Magic templates EVERY rainbow source. Bloom Tender, Great Divide Guide, Springleaf
  Drum and Agatha's Soul Cauldron all scored ZERO roles, in decks whose #1 graded weakness
  is the manabase. Added: any-colour ("add one/two/X mana of any"), the Vivid per-colour
  form ("for each color … add one mana of that color"), spend-as-any-colour, and
  all-basic-land-types.
  Card advantage — added Etali-style impulse off EACH PLAYER'S library (the existing
  patterns were scoped to "your library") and casting off the top of your own library
  (Vizier of the Menagerie, Bolas's Citadel), which scored nothing.

REC-2 | scripts/check_suggest.py, tests/test_deck.py |
  TEST DOUBLE ENCODING OLD BEHAVIOUR, found by check_all rather than reactively. Anchor 15
  and its pytest twin asserted a rainbow fixer ranks MOST-CUTTABLE, on the stated premise
  that it carries "no synergy tags AND no classified role". The ramp fix makes the second
  half false. Both re-premised to assert the fixer no longer tops the cut list, with the
  `add_is_fixer` guard assertion kept — role credit makes a fixer less cuttable, not
  uncuttable.

REC-2 | decks/*.txt (5 files) |
  Roster-wide before/after diff per K-12: 13 decks moved on card advantage, all upward;
  interaction unmoved. Ramp / fixing does NOT feed `deck_quality_vector`, so that half of
  the fix has zero blast radius on the tier floor. Five decks quoted a card-advantage
  figure the live vector no longer supported; corrected in place. Deck 34's prose claimed
  the axis was "genuinely thin rather than mis-counted" — it was mis-counted, twice, and
  now says so.

TEST RESULTS: 861 passed (854 -> 861: +5 check_roles, +2 role patterns; 1 anchor test
re-premised). All fourteen model-sanity gates green. check_all: all invariants hold.
One in-flight failure, caused by this session and fixed: the first draft of the ramp
pattern used a paraphrase ("add one mana of any color") where Bloom Tender's real text is
the Vivid form ("add one mana of THAT color"); the test written from the card's actual
text caught it.

REGRESSION RISKS:
- KNOWN RESIDUAL, recorded in deck.py: the any-colour patterns match the REMINDER TEXT of
  a Treasure token, including where the opponent gets it ("its controller creates a
  Treasure token"). Those pick up a spurious Ramp/fixing role. Left in deliberately —
  Ramp/fixing does not feed the quality vector, so the blast radius is the `stats`
  breakdown and `redundancy`'s depth count, not the tier floor.
- check_roles is deck-scoped, so a classifier hole on a card in NO deck stays invisible.
  Accepted: the gate's job is the cards being graded.
- The baseline is 367 entries and a meaningful fraction is genuinely roleless. The gate
  measures the DELTA, not the absolute; it is not a target to drive to zero.
- No interface, return type or default value changed on any existing export.

INVARIANTS AT RISK: None. No writer touched a canonical CSV; INV-01…04 all verified by
check_all after every step. INV-03 unaffected (role_baseline.txt is a new gate input, not
a derived reference file).

NET SCORE: 2 production fixes − 0 new failure modes = 2
  a) Would these have fired this month? YES for both. The role holes were firing
     continuously — deck 45 measured card advantage 0 while being built entirely on
     cast-from-exile, and four manabase-critical fixers read as roleless in the three
     decks actively being tuned this session.
  b) New failure mode introduced? NO. The Treasure-reminder over-fire is a
     pre-existing-style imprecision on a display-only axis, documented in place.

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push. The dashboard is rebuilt and published by
.github/workflows/pages.yml on push to main; no deck data changed shape, so no rebuild is
required beyond the automatic one.

FOLLOW-ON ITEMS:
- 367 baselined zero-role cards remain. Spot-checking shows real holes still in there —
  token creation has no role bucket at all (a model choice, not a bug), and "as this
  creature enters, choose a creature type" lords (K-13) score nothing. Worth a future pass;
  the gate now makes the population visible.
- The 4 pre-existing stale rationales (deck 40 Doppelgang, deck 49 x2, deck 51a Lost Days)
  are untouched and predate this session.
- 27 unverified printings across 15 decks, pre-existing.
- `rationale_staleness` cannot check a claim about a card's TEXT (only presence and quoted
  figures). Recorded in deck 54's header this session; no fix attempted.

DOCUMENTATION UPDATES NEEDED:
- DONE: CLAUDE.md gate count 13 -> 14, `check_roles` added to the Test Command gate list,
  and scripts/role_baseline.txt added to the Analysis subsystem inventory [C-05].
- Not done, and a judgement call for /sync-docs: whether the whitelist-failure-mode lesson
  deserves its own [G-nn] anchor in CLAUDE.md + docs/gotchas.md. It is currently recorded
  only in check_roles.py's module docstring. K-12 covers "role counts silently under-count"
  but not "the pattern set is a whitelist and its misses are invisible".
---END BROAD SCAN IMPLEMENTATION SUMMARY---
