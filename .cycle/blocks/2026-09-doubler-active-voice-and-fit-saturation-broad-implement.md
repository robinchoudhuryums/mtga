---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
  BS11-01 | `doubler_axis` missed the ACTIVE voice of the global token/counter replacement — Doubling Season, the card the mechanic is named after, scored None on BOTH its axes
  BS11-02 | `suggest-homes` had no KEY-saturation warning, though `screen` has had one since G-47
  BS11-03 | `/ingest` Stage 3c could not tell a NEW acquisition from an ownership CORRECTION, so it asked "where does this go?" about 75 cards that already had a home

Files modified: scripts/deck.py, scripts/check_suggest.py, tests/test_deck.py, .claude/commands/ingest.md

CHANGES:
BS11-01 | scripts/deck.py (_DOUBLER_AXES tokens + counters) | Added an active-voice branch to
  both patterns. The passive branch ("twice that many of those tokens ARE CREATED instead" —
  Elspeth, Storm Slayer) matched; the active one ("IT CREATES twice that many" — Doubling
  Season) did not. G-67's family-disagreement shape. The new branch requires the LITERAL
  "twice that many" rather than reusing the passive branch's looser `instead`, for the reason
  the lifegain axis already records: a replacement that is not a doubling is templated
  identically — Doc Samson, Super Psychiatrist is "that many PLUS ONE" and must stay out.
  Scoped to "an effect"/"you" and never "an opponent", so Vorinclex's second clause (which
  HALVES an opponent's counters) does not read as your doubler.
  Pool measurement: 71 -> 76 detected doublers, +5, ZERO lost. The five are Doubling Season
  (tokens), Anointed Procession, Parallel Lives, Vorinclex (counters), Innkeeper's Talent.
  Doc Samson was in the candidate set and is a CORRECT miss — reading its text is what kept
  it out; an earlier count of "6 of 6 missed" overstated the hole.
BS11-01 | scripts/check_suggest.py | Extended the doubler probe, which tested only the PASSIVE
  form and therefore could not have caught this. Four new assertions: active token doubler,
  active counter doubler, the plus-N counter replacement stays out, the opponent-scoped
  halving stays out. Watched-it-fail: reverting the regex turns this gate red.
BS11-02 | scripts/deck.py (cmd_suggest_homes + _HOMES_KEY_SATURATED = 0.15) | New roster-wide
  saturation warning, the twin of `_SCREEN_KEY_SATURATED = 0.40`. Threshold DERIVED, not
  chosen: measured on the 75 cards a reconcile ingest surfaced against a 114-deck roster,
  KEY-deck counts run p25 4 / p50 9 (8%) / p75 14 (12%) / max 30 (Patchwork Banner, 26%). At
  0.15 it fires on 14 of 75 (19%) — the `_UNPRICED_DISCLOSE_FLOOR` band, clear of the G-07
  saturation shape. REPORTS, never re-scores (the protection-axis stance). Lower than the pile
  threshold because the denominators differ: a `screen` pile is pre-filtered to one deck's
  plausible adds; a roster is every deck you own.
BS11-03 | .claude/commands/ingest.md | Stage 3c now partitions "new to the LIBRARY" from "new
  to the ROSTER". A card absent from every deck file is a genuine placement; a card already
  maindecked is an ownership CORRECTION whose question is "does it earn a SECOND home",
  graded with the decks it already lives in excluded. Stage 4 now requires saying which
  partition a card came from, and requires reporting a SATURATED fit pass as saturated rather
  than handing over its rows.

TEST RESULTS: passed. Full suite 1809 passed / 0 failed / 0 skipped (exit 0). `check_all.py`
  all invariants hold, with the SAME single pre-existing soft warning (the three accepted dead
  tutors — decks 20a, 50a, 69a). CLI smoke (G-55) green on the top-level and suggest-homes help.
  Both new gates watched-it-fail: reverting the regex reddens `tests/test_deck.py::
  TestDoublerCoSignal::test_active_voice_doublers_are_detected` AND `check_suggest.py`.

ROSTER DIFF (the K-14 / G-40 requirement — measured at each caller, before and after):
  TIER FLOORS moved: 0 of 111. Correct and predicted — G-80: tags and overlays feed
    cuts/suggest/centrality while `tier_band` grades on `role_tally`, which reads TEXT.
  CUTS top-3 changed: 1 of 111 — deck 78, where DOUBLING SEASON moved DOWN the cut list
    (#2 -> #3), now carrying `✱multiplier — doubles tokens (11 feeder(s) here)`. That deck's
    own thesis card had been ranked its second-weakest. This is the intended direction and is
    the same failure shape G-40 records for Delney in deck 46.
  suggest-homes for Doubling Season is now ordered by feeder density (58 with 29 feeders, then
    21 with 19, then 36a with 17) rather than by the bare `tokens` tag.

REGRESSION RISKS:
- `doubler_axis` return type, signature and default are unchanged (axis string or None); the
  three deck.py callers (cut_keep_score's ✱, cmd_screen's ✱, cmd_suggest_homes' overlay) all
  take the same values. Over-match was measured rather than assumed: +5 cards, 0 lost, and the
  two near-miss families (plus-N replacement, opponent-scoped halving) are pinned by tests.
- Was the old behaviour ever correct? No. Doubling Season is unambiguously a doubler on both
  axes; nothing depended on it reading None.
- BS11-02 is display-only and adds one `roster_decks()` call per invocation (memoized loaders).
  It indexes the results tuple positionally (r[3] shared, r[5] strength), matching the
  surrounding code's existing style (r[2], r[6], r[8]) — noted as a fragility, not changed.
- BS11-03 touches no code.

INVARIANTS AT RISK: None. No data file was written; INV-01..06 are untouched and `check_all`
  confirms all hold. `check_patterns`' registry gate (every `_DOUBLER_AXES` pattern must be
  registered) still passes — the patterns were edited in place, not moved out of the dict.

NET SCORE: 2 production fixes − 0 new failure modes = 2
  BS11-01 would have fired this month: it already had, silently — deck 78 runs Doubling Season
  and `cuts` was offering it. BS11-02 fired this month by construction (it is the warning whose
  absence made a 756-row fit pass look like 756 recommendations). BS11-03 fired this month on
  the 75-card reconcile. Counting BS11-02/03 as one "fix" for the tally since they address the
  same saturation; no new failure mode introduced by any of the three.

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: N/A for Analysis — data + local tooling ship by commit/push. The Presentation
  subsystem was not modified, so `.github/workflows/pages.yml` needs no run beyond its
  automatic rebuild on push to main.

FOLLOW-ON ITEMS:
- `doubler_axis` returns the FIRST matching axis only, so Doubling Season reports `tokens` and
  its counters half is invisible. Pre-existing single-axis limitation, out of scope here; it
  matters for a deck that runs it purely for counters.
- The 38 other "twice that many" pool cards are one-shot "double the counters on target
  creature" effects (Tanazir Quandrix, Hulk, Invigorating Surge…). They are deliberately NOT
  doublers — counting them is the BS2-06 over-count — but nothing records that decision where
  the next reader will look.
- `cmd_suggest_homes` indexes its results tuples positionally. A named tuple or dict would make
  BS11-02's r[3]/r[5] safe against a field being inserted.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-33 should record the active-voice branch and that Doubling Season was invisible
  to it, so the next reader does not re-derive the hole.
- CLAUDE.md G-31 should name the new `suggest-homes` saturation warning next to `screen`'s.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
