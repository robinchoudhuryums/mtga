---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- F1 — BOARD PRESENCE was not a metric anywhere. No `board_power` existed in scripts/;
  the axis was hand-rolled six-plus times in one session because deck 41 read "weak" while
  clearing an A floor, and no tool could say why.
- F3 — a figure invented in `#: tier:` prose is UNGUARDED unless a pattern prices it.
  Deck 41's board-power figure went stale twice on 2026-09-18 (41→56 after one swap, →57
  after three more) and `--audit-rationale` reported the block CURRENT both times.

Files modified: scripts/deck.py, scripts/check_patterns.py, tests/test_deck_models.py,
tests/test_deck.py

CHANGES:
F1 | scripts/deck.py | New `board_power(cards, carddata)` — quantity-weighted printed
   power over cards whose FRONT face is a creature (`primary_type`, G-63). Returns
   power / creatures / unknown / vehicles / vehicle_power. `board_power_note()` is the
   shared human rendering so `stats` and `tier` cannot drift (G-70). Three things it
   refuses to guess at, disclosed instead: UNKNOWN power (`card_power` returns None for a
   printed */X and is never coerced — G-16/BS4-32, and this is not a corner case: 70 of
   112 roster decks hold at least one such creature, 124 copies, so a bare sum would
   under-report on 62% of the roster); TOKENS and created bodies, which read ZERO because
   they are not printed on a card in the list; and VEHICLES, counted apart because they
   are not creatures until crewed (10 decks, 16 copies, 63 power).
F1 | scripts/deck.py | `deck_quality_vector` publishes `board_power` / `board_unknown`
   and now takes `creatures` from the SAME helper. It had been running a second in-loop
   `"Creature" in _primary_type(...)` tally beside board_power's — two answers to one
   question, this repo's dominant bug class. Verified a no-op: 0 creature-count diffs
   across all 112 roster decks against a pre-change snapshot.
F1 | scripts/deck.py | `stats` prints the axis beside the role counts it is blind to, with
   the "printed power only — read it as a FLOOR" caveat; `tier` puts it on the vector line
   and adds a ⓘ line when there is an unknown or a Vehicle. REPORT-ONLY on both: nothing
   reaches `tier_band`, the same stance as protection (G-25), the X-cost advisory (G-60)
   and the unpriced-discount disclosure (G-85), and for the same reason — a new floor term
   silently re-grades the roster, which is what the payoff-density simulation showed on
   2026-09-03 before it was declined.
F3 | scripts/deck.py | Four `_RATIONALE_FIGURES` patterns registering `board_power`, in
   the same change that added the metric. Deliberately NOT `_FIG_GAP`: the roster's only
   live board-power claim is a worded DELTA ("Board power went 41 to 57"), and a gap of up
   to two lowercase words would read `went 41` as a claim of 41 — flagging the FROM side of
   the very change the prose documents. Adjacent forms plus one explicit TO-side pattern.
F3 | scripts/deck.py | `_FIG_RANGE_AFTER`, the WORDED form of `_ARROW_AFTER`, added to
   `_figure_is_history`: a figure followed by "to <digit>" is the FROM side of a change.
   `_ARROW_AFTER` only ever knew the arrow spelling. Two live instances on the roster
   (deck 41's board power, deck 47's "the axis went 6 to 7"); requires a DIGIT so
   "interaction 7 to answer a wrath" stays a live claim.
F3 | scripts/deck.py | `audited_figure_keys()` — DERIVED from the pattern table, never
   hand-listed — and `--audit-rationale` now prints "figures checked: …" on both the clean
   and the stale path, with an explicit note that a number not on the list is unguarded.
   A clean bill said "every figure matches the live vector" and MEANT "every figure I have
   a pattern for matches"; the gap between those was invisible, which is exactly how deck
   41's number rotted twice in plain sight.
F3 | scripts/check_patterns.py | `_FIG_RANGE_AFTER` registered in `_EXCLUDED` with its
   reason. The gate caught the unregistered pattern on the first run — working as designed.

TEST RESULTS: passed.
- `python3 scripts/check_all.py` — "All invariants hold. ✓", exit 0. Soft warnings
  IDENTICAL to the pre-change baseline (deck 28's `#~ note:` protection figure; 3 dead
  library searches). No new warning.
- Full `pytest` suite — exit 0, no failures, no skips.
- WATCHED-IT-FAIL on the new patterns: a scratch copy of deck 41 with the figure mutated
  to 99 is flagged in all three prose forms (worded delta, adjacent, number-first); the
  correct value reads clean; and the verbless delta "board power 41 to 57" does NOT flag
  its FROM side.
- ROSTER SWEEP (G-26's mandate for any widening): 0 stale figures reported across 112
  decks, unchanged from before — no new false positives.
- DETERMINISM (G-54, since `audited_figure_keys` derives from a SET): byte-identical
  output across PYTHONHASHSEED 0/1/12345 for both changed commands.
- Regression Scenario 2 (Analyze a deck) — PASS. 20 per-deck commands plus the roster-wide
  half (`suggest --lands/--ramp/--interaction/--needs`, `screen`, `audit`, `similar`,
  `suggest-homes`, `pool.py --role`, `--help`, one subcommand help): no traceback.
- Regression Scenario 19 (Degraded analysis panels) — PASS. `build_dashboard.py --out`
  exits 0, stderr carries no `deck analysis failed for N/113`, built page has 0
  `[analysis error`.
- Scenarios 4, 5, 6, 7, 8, 10–18 — NOT APPLICABLE: they need a person at a browser and
  this change touches no template, no generated page and no theme token.
- Scenarios 1, 3, 9, 11 — NOT APPLICABLE: ingest / refresh / match-log paths untouched.

REGRESSION RISKS:
- `deck_quality_vector` gained two keys. Every consumer was checked: `quality` and
  `quality --vs` iterate a FIXED key tuple (unaffected), `tier_band` reads named keys
  (pinned by a new test that two decks differing only in creature SIZE land in the same
  band), `check_agreement` does not read `creatures`, `build_dashboard.py` does not read
  the vector at all. No caller compares the key SET.
- `cmd_stats`' printed output is captured by `app.py`'s editor Stats tab, so the new lines
  appear there too. Intended, and test_cli.py's output assertions still pass.
- The one real risk is `_FIG_RANGE_AFTER`: it is a new SUPPRESSION, so it can only ever
  hide a report, never invent one. Counted honestly as a new failure mode below.

INVARIANTS AT RISK: None. No CSV and no deck file is written by any of this; INV-01,
INV-01b, INV-02, INV-03 and INV-04 are untouched, and `check_all` confirms.

NET SCORE: 2 − 1 = 1
- F1 would have fired this month — it DID, six times in one session.
- F3 would have fired this month — it DID, twice on 2026-09-18, on the same deck.
- New failure mode (1): `_FIG_RANGE_AFTER` adds a false-NEGATIVE surface. A figure written
  "N to M" where N is a live claim rather than a delta is now silently skipped. Measured at
  0 live instances (all 10 roster matches of that shape are genuine deltas or ranges), and
  the direction is the safe one per G-26 — but a false negative is the SILENT direction, so
  it is counted rather than waved off.

OPERATOR ACTIONS / DEPLOY:
- None.
Deploy: Presentation — `.github/workflows/pages.yml` republishes `dashboard.html` on push
to `main`. The committed dashboard is unchanged by this work (build_dashboard does not read
the quality vector), so no deploy is required for it; the push will rebuild it regardless.

FOLLOW-ON ITEMS:
- The `keepable` figure patterns REQUIRE a `%` sign, so deck 41's "keepable 84.4 to 86.0,
  screw 14.3 to 12.2" is matched by nothing. A real registered-but-unreachable figure,
  found while reading prose for this fix; out of scope here.
- TOKENS and other created bodies still read ZERO in `board_power`. This is the M-sized
  half of F1 and was deliberately deferred: `_makes_token` knows a card creates a token but
  not how big it is, and parsing token sizes is a new pattern set with a whitelist's blind
  spots (G-67). The output discloses the limitation rather than hiding it.
- `quality --vs` does not surface board power — the value is in `--json` but the printed
  tuple is unchanged, so a swap that halves the deck's board does not self-flag. Left
  deliberately: changing the F10 guard's reported set is a wider blast radius than this
  finding asked for, and it is a decision rather than an oversight.
- Findings 2 (`consistency` cannot price a rock or dork while `suggest --ramp` recommends
  them — 40 of 112 decks affected, and TWO decks have hand-written the workaround into
  their `#: notes:`) and 4 (`_COST_UPSIDE` has no pay-life rule; needs a G-42-style
  precision measurement BEFORE any rule is written) are untouched and still open.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md needs a new Common Gotchas rule for the board-power axis: what it measures,
  that it is report-only by design, and the three things it cannot see. Every sibling
  report-only metric has one (G-25, G-60, G-85), and without it a future session neither
  knows the axis exists nor knows the report-only stance is deliberate.
- `docs/gotchas.md` needs the long form under that anchor: the distribution (min 23 / p10
  37 / p50 54 / p90 73 / max 120, mean 56.2), the independence measurement (r = −0.147
  against a ±0.188 noise band at n=112), the 70-of-112 unknown-power population, and the
  deck-41 incident that produced it.
- Any of those figures written into CLAUDE.md must be registered in
  `check_docs.figure_drift`, or the rule's own evidence becomes the next stale number.
- G-27's list of audited figure families should record board power, and that
  `--audit-rationale` now discloses its covered list.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
