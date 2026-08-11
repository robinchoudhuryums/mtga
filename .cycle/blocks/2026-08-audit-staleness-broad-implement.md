---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: 
  Fix 1 — rationale audit: a fragment inside a longer ABSENT card name resolves to a different card
  Fix 2 — flex_staleness checked only the -Out half of a two-sided line
  Fix 3 — _ROLE_PATTERNS whitelist hole: variable damage in TARGET-FIRST word order
  Fix 4 — `#~ note:` prose outside every staleness scan — MEASURED AND NOT BUILT (see below)
Files modified: scripts/deck.py, scripts/check_all.py, scripts/role_baseline.txt,
                tests/test_deck.py, decks/28-dinosaurs/deck.txt

CHANGES:
Fix 1 | scripts/deck.py (rationale_staleness) | The shorthand pass now scans a string with every
  OCCURRING full card name blanked, not `masked` (which hides only cards the deck RUNS). An absent
  card's full name stayed in the text, so a fragment of it resolved to whatever OTHER card
  abbreviates to that fragment — live on deck 28, where prose citing "Savage Land Dinosaur"
  produced a false second report of "Ka-Zar of the Savage Land". Suppressed names are blanked too:
  otherwise the fragment path smuggles back a citation the full-name scan deliberately let go
  (history / simile / negation). Length-preserving mask, so `pos` stays comparable. +2 tests.

Fix 2 | scripts/deck.py (flex_staleness, cmd_flex), scripts/check_all.py | The `+In` half is now
  checked: a line proposing an add the deck already runs is stale. Deck 28 carried
  `-Triumphant Chomp | +Bushwhack` with Bushwhack maindecked. BASICS are exempt (unlimited in
  Arena, so "+Island" is a 25th-land proposal, not a duplicate) — that was the single false
  positive in the first roster sweep, 7 of 8 hits being real. Both consumers reworded off the
  `why` field instead of hard-coding "the card they propose cutting". +4 tests.

Fix 3 | scripts/deck.py (_ROLE_PATTERNS), scripts/role_baseline.txt | Added the TARGET-FIRST
  variable-damage shape; both pre-existing patterns assume "equal to X" precedes "to target".
  Triumphant Chomp — a {R} sorcery that kills anything up to a 12/12 — scored ZERO roles, which is
  why `cuts` ranked it deck 28's weakest card. Guard extends BS2-06: player-only burn stays out,
  and "target spell's controller" (Refuse) is a player too — the only false positive when measured
  against the whole pool. Fixtures are the cards' REAL text (G-67). Stale baseline entry for
  Triumphant Chomp pruned as part of the fix, not reactively. +3 tests.

Fix 4 | NOT BUILT | Measured first, and both implementable forms fail this repo's own standard.
  Extending the CARD scan to `#~` notes fires on 252 citations across 51 decks of 537 note lines —
  a flex note's job is to discuss cards NOT in the deck. Extending the FIGURE half fires 47 times,
  28 of them arrow/delta form (history by construction). The narrow variant (bare present-tense
  figures only) yields 16 hits, 12 contradicting the live vector — but at least two are cue-gaps,
  not staleness ("+1 early drop" is a DELTA; "it READ avg MV 4.18" is history), so shipping it
  needs a suppression-iteration pass against 537 lines. Decisive: the failure that motivated the
  finding — a note asserting "the deck has FOUR cyclers" — is neither a card name nor a tracked
  vector key, so NO version of this check would have caught it. Precedent followed:
  check_commands' executable-shape rule was measured and rejected the same way.

TEST RESULTS: passed — 1253 tests (was 1244; +9). `check_all` all invariants hold. Each new test
  was watched failing against the unfixed code first, except
  `test_a_suppressed_full_name_is_not_re_flagged_via_its_fragment`, which passed pre-fix and is a
  regression pin rather than a reproduction — stated so it is not read as evidence it did not give.
REGRESSION RISKS: 
  - flex_staleness return shape unchanged (3-tuple); both consumers updated, no other callers.
  - rationale_staleness return shape unchanged; check_all and header_card_staleness unaffected.
  - Fix 3 moved role counts on exactly 2 decks (28: interaction 6→7; 28a: 3→4) and ZERO tier
    floors, verified by a captured before/after roster snapshot. Deck 28's `#~ note:` figures,
    invalidated by my own change, were re-grounded in the same commit.
  - check_agreement and check_roles re-run green; `deck.py --help` and `flex --help` smoke-tested
    (G-55: no gate builds an argparse tree).
INVARIANTS AT RISK: None. No canonical CSV writer, deck-file parser, or schema was touched.
  role_baseline.txt is an acknowledgement list, not an invariant; its one pruned entry is the
  intended consequence of Fix 3.
NET SCORE: 3 production fixes − 0 new failure modes = 3

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push (no build/release step). The dashboard is the one
  deployed artifact and rebuilds itself from source via .github/workflows/pages.yml on push to
  main; no deck data changed shape, so no manual rebuild is required.

FOLLOW-ON ITEMS:
- 7 genuine stale flex lines the new +In check surfaced, now a soft warning: decks 8, 14, 26,
  26a (x3, including a duplicated Invasion Submersible line), 50. NOT edited here — G-04 makes a
  flex line a human editorial note, and the scope was tooling.
- 12 bare figures in `#~ note:` prose that contradict the live vector (decks 26, 26b, 28, 31, 41,
  42, 49, 50, 50a). Surfaced by the Fix 4 measurement; deck 28's were fixed because Fix 3 caused
  them. The rest are the raw material if Fix 4 is ever revisited with a suppression pass.
- Fix 4 itself, if wanted: it needs a delta-form suppression ("+1 early drop") and additional
  history verbs ("read", "measured at"), iterated against 537 note lines.

DOCUMENTATION UPDATES NEEDED:
- G-04 in CLAUDE.md + docs/gotchas.md: now covers BOTH halves of a flex line, not just the stale cut.
- G-26 in CLAUDE.md + docs/gotchas.md: the prefix-collision residual is closed; record it and the
  "blank suppressed names too" reasoning.
- G-67 in CLAUDE.md + docs/gotchas.md: add the target-first variable-damage hole to the list of
  whitelist misses found by a human reading a card.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
