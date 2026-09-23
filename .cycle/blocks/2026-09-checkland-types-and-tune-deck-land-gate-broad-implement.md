---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
  F-LAND-01 — `check` tapland premium read the deck's basic COUNT, never the basic TYPE
  F-LAND-02 — `/tune-deck` gated `suggest --lands` on a scorecard mana deficit
  F-LAND-03 — apply the three land swaps the two findings surfaced (decks 1 and 2)

Files modified: scripts/lib.py, scripts/deck.py, scripts/wishlist.py,
tests/test_lib.py, .claude/commands/tune-deck.md, CLAUDE.md, docs/gotchas.md,
decks/01-black-sun/deck.txt, decks/02-thundergod/deck.txt, dashboard.html,
recommendations.csv

CHANGES:
F-LAND-01 | scripts/lib.py | `_TAPLAND_CHECK_RE` matches BOTH the generic "unless you
   control a basic land" and the TYPE-NAMED cycle ("a Plains or an Island"). Both
   collapsed to kind `check`, and the only thing any consumer knew was the deck's TOTAL
   basic count against `_CHECKLAND_BASIC_FLOOR = 12` — so a land gated on basics the deck
   does not run took the untapped premium. New `tapland_check_types(text)` returns the
   gate's basics as WUBRG letters (None = not a checkland, EMPTY = generic form, non-empty
   = named cycle), read off NAMED CAPTURE GROUPS added to the existing pattern rather than
   a second regex — a parallel pattern for "which types" is the drift shape this project
   keeps paying for. `tapland_kind(text, basic_types=None)` returns `unconditional` for a
   named gate the deck cannot meet, which is the literal truth there and keeps it out of
   `TAPLAND_CONDITIONAL_KINDS` so no consumer special-cases it. `_BASIC_TYPE_COLOR` became
   public `BASIC_TYPE_COLORS` because deck.py needs the same map.

F-LAND-01 | scripts/wishlist.py | `_land_value` gained `basic_types=None` and passes it
   to `tapland_kind`. Default omitted = pre-fix behaviour, which `wishlist --rank` needs
   (it has no deck).

F-LAND-01 | scripts/deck.py | Three call sites opted in. `suggest_lands` collects
   `deck_basic_types` beside the existing `deck_basics` count and passes it to
   `_land_value` (the premium) and to both `tapland_kind` reads (the `·check` rider, which
   was making the same wrong claim to the reader). `tapland_profile` — the `consistency`
   tempo line — walks a deck's own lands and so always had the answer; it passes them too.
   Fixed in the PREDICATE, not per caller, because G-35's whole point is that there is one
   of it.

F-LAND-02 | .claude/commands/tune-deck.md | New step 5c runs `suggest <id> --lands` EVERY
   run. 5b's "if the scorecard says the deficit is interaction or mana" is right for
   `--ramp`/`--interaction` and became wrong for `--lands` when G-37 (2026-09-20) made a
   land already in the deck a pick: the recommender's commonest output is now advice for a
   manabase that is NOT deficient, i.e. exactly the deck the gate skipped. The step also
   says to read the TEMPO line rather than the colour counts, because an unconditional
   tapland swapped for an untapped dual of the same colours moves no probability figure at
   all.

F-LAND-03 | decks/02-thundergod/deck.txt | −1 Mountain / +1 Fire Nation Palace (2nd copy).
   R 24 → 24, keepable 84.4% → 84.4%; the gain is a firebending mana sink in a deck with
   no other flood outlet. Gate is "a basic land" against 22 remaining basics.
F-LAND-03 | decks/01-black-sun/deck.txt | −Bloodfell Caves / +Blazemire Verge (2nd) and
   −Temple of Malice / +Blood Crypt (2nd). All four are BR duals: B 17 → 17, R 16 → 16,
   every cast-on-curve figure identical. Taplands 5 → 4 and both UNCONDITIONAL ones gone.

F-LAND-01/02 | CLAUDE.md, docs/gotchas.md | G-35 carries the deck-aware clause, G-37 the
   every-run fact; both were at 297/286 of the 300-word cap, so three pieces of incident
   evidence were moved out — each VERIFIED to survive verbatim in the long form first
   (the 81 back-face lands, the ten any-colour lands, decks 23/41's `#: notes:`
   workaround). Two new dated sections in docs/gotchas.md carry the measurements.

TEST RESULTS: passed. Full pytest 1904 passed (1898 baseline + 6 new), exit 0.
`check_all.py` "All invariants hold. ✓". Six new tests in
`TestTaplandKindSplitsByWhenTheConditionIsMet`, each proven load-bearing against a
targeted mutant — reverting the downgrade kills the cannot-meet test; downgrading EVERY
named gate kills the CAN-meet test (the negative half, without which the over-applying
fix also passes); conflating the empty frozenset with None kills the generic-gate test.
Regression scenario 2 (Analyze a deck) walked: 18 subcommands on deck 1 plus
`tier --audit-rationale`, all four `suggest` needs modes, `audit`/`similar`/`rotation`/
`suggest-homes`/`screen`, `--help` and one subcommand help, `pool.py --role`,
`wishlist.py --rank` — no traceback. Scenario 19's mechanical half: `dashboard.html`
contains zero `[analysis error` and the build printed no `deck analysis failed` line.
Scenarios 1/3 NOT APPLICABLE — lib.py is an Ingest subsystem file but the tapland
predicate is read by no ingest step. Scenarios 4–8, 10–18 NOT APPLICABLE — perceptual,
need a person at a browser, and no generated-page template changed.

REGRESSION RISKS: The `tapland_kind` signature gained an optional parameter; a test pins
that omitting it reproduces every pre-fix answer, so `wishlist --rank` (the one deckless
caller) is unchanged. `_TAPLAND_CHECK_RE` gained named capture groups, which no consumer
sees — every other use is a `.search()` truthiness test — and `check_patterns` still pins
it live-corpus. The old behaviour was never correct for a named gate, so there is no case
where this makes things worse; the risk is the opposite direction, over-applying to a
generic gate, which is what the two negative tests exist to catch. Roster diff measured by
running `suggest_lands` over all 112 decks twice with the predicate monkeypatched back:
79 scores moved, 91 rider labels corrected, 63 decks changed a row, 6 decks' #1 pick
changed — all six off a land the deck can never untap, each verified by hand against that
deck's basics.

INVARIANTS AT RISK: None. No CSV writer, schema or printing field touched. INV-04 was
re-checked by `swap --apply` on every land swap and `preflight` reads READY for both
decks; check_all green.

NET SCORE: 2 production fixes − 0 new failure modes = 2
  F-LAND-01: would it have fired this month? YES — it was firing, on 81 (deck, land)
    pairs across 54 of 114 decks, and it put Cori Mountain Monastery at #2 in deck 2's
    own land list while the session was reading that list.
  F-LAND-02: YES — a `/tune-deck 2` run would not have opened the land list at all, and
    the second Fire Nation Palace was free and sitting in it.
  F-LAND-03 is the application of those two, not a third fix, and is not scored.

OPERATOR ACTIONS / DEPLOY: None.
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds the dashboard on push to
main. Decks 1 and 2's land rows change there. No other subsystem has a Deploy Command.

FOLLOW-ON ITEMS:
- Deck 1's land swap has a small ROTATION cost, reported rather than buried: Temple of
  Malice (FDN) was legal to ~2029 and the two adds run to ~2027 (Blazemire Verge, DSK)
  and ~2028 (Blood Crypt, ECL). The user instructed the swap; this is information.
- `wishlist.py --rank` still scores every named-gate checkland conservatively because it
  has no deck to read. Correct, but it means a craft target gated on a basic type is
  under-valued for the deck that WOULD run it. Not in scope; `--rank` is deckless by
  construction.
- `Hobbit Hole` and the other basic-FETCH lands still score high on G-35 fixing breadth in
  a MONO-colour deck, where fetching a tapped basic is strictly worse than playing the
  basic. Noticed while reading deck 2's list; separate from this finding.
- Deck 2's `·check` on Fire Nation Palace is now correct, but nothing checks the
  interaction between a checkland's gate and a deck that might LOSE its basics to a later
  land swap. No instance today.

DOCUMENTATION UPDATES NEEDED: Done in this change — G-35 and G-37 in CLAUDE.md (both kept
under the 300-word cap by moving already-duplicated evidence out), plus two new dated
sections in docs/gotchas.md carrying the full measurements.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
