---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- F2 — `consistency` prices every figure off the LAND count (G-35) while `suggest --ramp`
  recommends the nonland sources it cannot see. Two surfaces disagreeing by construction,
  with neither saying so. FIXED as a disclosure.
- F4 — `_COST_UPSIDE` has no pay-life rule, so three cards were graded down in chat for
  costing life in the deck that refunds it. MEASURED AND DECLINED; the measurement is
  recorded at the table so a re-proposal lands on it.

Files modified: scripts/deck.py, tests/test_deck_models.py

CHANGES:
F2 | scripts/deck.py | New `uncounted_mana_sources(cards, carddata)` -> [(qty, name,
   colours, conditional)], printed by `consistency` under the "lands producing each
   color" heading it qualifies. REPORT-ONLY: it changes no figure, because a rock is not
   a land drop and must not inflate a land count — that exclusion is correct and was
   never the bug. The bug was its SILENCE.
   The production rules are `lib.land_production`'s, run on a nonland card's text, so the
   disclosure and the land count cannot drift apart (G-70) — which is the entire point,
   since the finding IS two surfaces disagreeing. That reuse buys three exclusions free,
   each matching what the land count already does: SPEND-ONLY mana excluded (G-35 says so
   for lands; counting it here would have made the disclosure contradict the rule it
   complements — 8 roster cards), GRANTED abilities excluded (so "Lands you control have
   '{T}: Add …'" reads as the land upgrade it is), extra-cost sources counted but
   LABELLED. The PERMANENT filter is this function's own: a land's Add clause is
   repeatable by tapping, a sorcery's is a one-shot ritual.
F4 | scripts/deck.py | A ~35-line measured DECLINE recorded at `_COST_UPSIDE`, in the
   shape G-42 uses for its own declined flag.

MEASUREMENT — F2, and the first one was WRONG in a way worth keeping:
- A hand-rolled regex (written in the triage that produced this finding) reported 40 of
  112 decks. `_MANA_SOURCE_RE` — the EXISTING primitive, which has exactly one caller —
  reported 89 decks / 97 cards at much worse precision, matching rituals, spend-restricted
  mana and granted abilities alike. G-40's rule fired exactly as written: reaching a new
  caller is not free, so re-measure the primitive AT that caller. Neither number survived.
- Through `land_production` instead: **75 of 112 decks, 76 distinct cards**, hand-checked
  at 74 of 76. The two residuals are an aura that upgrades a LAND ("Enchanted land has
  '{T}: Add two mana…'", New Horizons — `_GRANTED_ABILITY_RE` does not phrase-match it)
  and one "target player adds" that could name the opponent (Radiant Lotus).
- ACCEPTANCE: deck 23's `#: notes:` says White Auracite is "a 23rd white source that
  `consistency` does NOT count". The disclosure now surfaces White Auracite on deck 23 —
  and White Lotus Tile, which the hand-written note had missed.

MEASUREMENT — F4, which is why it was declined:
- Bar pre-registered BEFORE looking: ship only above ~50% precision. G-42's flag was
  declined at <=14%.
- BROAD form (gate: CENTRAL themes include lifegain / pay life / drain / lifelink — 50 of
  112 decks) fires on 91 (deck, card) pairs at **22% precision**, and that figure is
  GENEROUS because the bucket counting it was gated on a regex that conflates "whenever
  you GAIN life" with "whenever you LOSE life". Failure split: **46% NOT REWARDED**
  (shocklands, equip costs, a land's own "{T}, pay 1 life: add" — you pay those FOR
  something), **26% CHEAP-but-not-upside**, **6% BACKWARDS** ("ward—pay 5 life" is the
  OPPONENT's cost read as yours — literally G-42's signature).
- NARROW form (gate: the deck fields a payoff that TRIGGERS on losing life, the only
  shape that makes the cost feed something) is unbuildable: **1 of 112 decks** holds one,
  off **7 pool cards** total — and it is NOT deck 41, the deck that motivated the finding.
  Deck 41's refund is Mister Negative's life SWAP, which no text model here holds.
- THE SHAPE WAS WRONG, and that is the transferable part: every existing `_COST_UPSIDE`
  rule encodes a cost that FEEDS something. Paying life feeds nothing. Deck 41 needed the
  weaker claim "this cost is CHEAP here", and the ⚡ flag asserts the stronger one.

TEST RESULTS: passed.
- `python3 scripts/check_all.py` — "All invariants hold. ✓", exit 0, soft warnings
  IDENTICAL to the pre-change baseline.
- Full `pytest` — exit 0, no failures, no skips. 7 new tests pin F2's exclusions.
- `_COST_UPSIDE` verified unchanged in behaviour after the comment edit: 5 rules, still
  deck-gated (a discard cost flags in a reanimator deck and not in a control deck).
- DETERMINISM (G-54): `consistency` byte-identical across PYTHONHASHSEED 0/1/12345.
- Regression Scenario 2 (Analyze a deck) — PASS: `consistency` across 7 decks spanning
  the mana-source distribution, no traceback.
- Scenarios 1, 3, 4, 5–19 — NOT APPLICABLE: no template, generated page, theme token,
  ingest path, deck file or CSV is touched.

REGRESSION RISKS:
- `uncounted_mana_sources` is new and additive with one caller; no interface, return type
  or default changed anywhere.
- `cmd_consistency` gained an output line, which `app.py`'s editor tab also renders.
  Intended.
- The `_COST_UPSIDE` edit is comment-only, verified behaviourally rather than by reading.
- Is there a case where the OLD behaviour was right? For F2, no: the silence was the bug
  and the counts are untouched. For F4, the old behaviour (no rule) is what the
  measurement endorses.

INVARIANTS AT RISK: None. No CSV and no deck file is written; INV-01, INV-01b, INV-02,
INV-03 and INV-04 untouched, confirmed by `check_all`.

NET SCORE: 1 − 0 = 1
- F2 would have fired this month — it DID: two decks (23 and 41) had each independently
  hand-written the workaround into their own `#: notes:` prose, and this session asked
  "are there mana-fixers that could help castability?" and had to answer it by hand.
- F4 is NOT counted as a production fix. It is a measured DECLINE — the defensive bucket
  `/reflect` tracks — and counting a decision as a fix is the self-report inflation the
  cycle-9 reflect had to correct.
- No new failure mode: F2 is report-only with hand-checked 74/76 precision, and F4 changed
  no behaviour at all.

OPERATOR ACTIONS / DEPLOY:
- None.
Deploy: Presentation — `.github/workflows/pages.yml` republishes `dashboard.html` on push
to `main`. `build_dashboard.py` does not call `consistency`, so the published page is
unchanged; the push rebuilds it regardless.

FOLLOW-ON ITEMS:
- Deck 23's `#: notes:` carries a hand-written workaround for F2 that the tool now
  supersedes ("a 23rd white source that `consistency` does NOT count"). Deck 41's carries
  the F4 one ("the cost-as-upside flag has five rules and none of them is pay-life") —
  that one is still TRUE and should stay. Retiring the first is a deck edit, out of scope
  here.
- `_GRANTED_ABILITY_RE` does not phrase-match "Enchanted land has …", so a land-upgrading
  aura reads as a nonland source. One card roster-wide; a fix belongs in `lib`, where the
  land count would inherit it too.
- `_MANA_SOURCE_RE` still has exactly one caller and is now measurably the wrong primitive
  for any second one. Left alone deliberately — its `early_mana` caller is correct.

DOCUMENTATION UPDATES NEEDED:
- G-35 should record that `consistency` now discloses the nonland sources it excludes, and
  why the exclusion itself is still right.
- G-41 should record the pay-life decline the way G-42 records its own, so it is not
  re-proposed from CLAUDE.md alone without opening the code.
- Both need `docs/gotchas.md` long forms under their anchors, and any figure cited as
  evidence needs a `check_docs.figure_drift` entry.
- Still outstanding from the PREVIOUS batch: the board-power axis has no CLAUDE.md rule.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
