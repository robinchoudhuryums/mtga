---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
  F-CUTS-01 — plan-aware `cuts` flag. PROTOTYPED, MEASURED and **DECLINED**.
  No change to scripts/deck.py.

Files modified: .cycle/HISTORY.md, .cycle/NEXT-SESSION.md,
.cycle/findings-cuts-plan-awareness.md (DELETED), .cycle/STATE.md

CHANGES:
F-CUTS-01 | (no production code) | The flag was built as a throwaway measurement
   script, run against the live roster, and declined on the acceptance bar the
   finding itself set. The decline and its numbers are recorded in
   `.cycle/HISTORY.md`; the finding file is deleted per its own header, and
   `.cycle/NEXT-SESSION.md` item 0 now points at the record and carries the two
   live residuals.

WHAT THE MEASUREMENT FOUND — three independent reasons, increasing in force:

1. COVERAGE. Constraint 2 restricted the flag to an EXPLICIT `#: plan:` header.
   Only **8 of 114 decks (7%)** carry `#: plan: aggro`, the one plan where
   "MV>=5 / mana-only early drop" is a defensible off-plan claim. **Deck 1 — the
   deck that produced the finding — is not one of them**; its plan is inferred
   from the word "aggro" in its `#: archetype:` prose. The finding's own safety
   constraint excluded its own motivating case.

2. PRECISION. **40 hits over 205 nonland cards; 25 clearly FALSE (62.5%), so
   precision <= 37.5%.** G-41 measured 22% and G-42 <= 14%; both were declined.
   The failures are structural, not threshold-tunable:
   - The MV>=5 branch flags aggro FINISHERS — backwards, since an aggro deck's
     top end IS its plan. Aurelia, the Warleader ("untap all creatures you
     control. After this phase, there is an additional combat phase") was
     flagged in TWO of the eight decks; so were Full Throttle, Sozin's Comet,
     Twinflame Tyrant, Nova Hellkite, Streaking Oilgorger, Thor Odinson, Samut,
     Combustion Man, Spinerock Tyrant.
   - It re-opens G-60/G-83. Printed MV lies hardest on exactly what it flags:
     The Dawning Archaic (MV 10, costs {1} less per instant/sorcery in yard),
     Valkyrie Aerial Unit (MV 7, Affinity for artifacts), Savage Ventmaw (MV 6,
     refunds {R}{R}{R}{G}{G}{G} on attack), Fate of the Sun-Cryst (MV 5, costs
     {2} less targeting a TAPPED creature — in deck 73a, the tap deck).
   - The mana branch fires BACKWARDS on the deck whose thesis it is: 73a is the
     tap-for-value build and Springleaf Drum, Dragonbroods' Relic, Hardbristle
     Bandit and Spider Manifestation are its ENGINE. All four flagged. G-42's
     signature.
   - `_MANA_SOURCE_RE` misfires at this caller exactly as its own docstring
     warns (deck.py L6681-6686, 89 decks against a hand-rolled 40). The Last
     Agni Kai — a {1}{R} FIGHT spell — matched on "add that much {R}" in its
     excess-damage rider; Mardu Devotee read "mana-only" while its text is
     "when this creature enters, scry 2".

3. REDUNDANCY. Strip the 25 false positives and the ~15 survivors all say "this
   card is expensive" — which the `cuts` table's **MV column already prints
   beside every row**.

WHAT IS CONFIRMED AND NOT DECLINED: `cut_keep_score` genuinely reads no mana
value and no plan. That half of F-CUTS-01 stands. The two remedies are cheaper
than the flag and need no code: `#: protect:` (deck 1 had none, which is why its
namesake ranked #1 cut), and the SEVEN decks whose inferred plan contradicts
their own curve — a live defect in `tier`, where the plan is a grading input.

TEST RESULTS: `python3 scripts/check_all.py` — "All invariants hold. ✓".
No production code was changed, so no new test was owed and none was written.

REGRESSION RISKS: None — `scripts/` is untouched.
INVARIANTS AT RISK: None. No CSV, deck file, schema or printing touched.

NET SCORE: 0 production fixes − 0 new failure modes = **0**
  A declined finding scores zero by construction. The value delivered is the
  measurement: this family (G-41, G-42, now F-CUTS-01) costs a roster sweep each
  time it is re-proposed, and the record now says not to.

OPERATOR ACTIONS / DEPLOY: None. | BLOCKS DEPLOY: N
Deploy: N/A — no production code changed.

FOLLOW-ON ITEMS:
- SEVEN decks carry an inferred plan contradicting their own curve: 39-starforge
  (3.40), 35-hack-n-slash (3.36), 20-honor-among-thieves (3.33), 36-panthera
  (3.31), 02-thundergod (3.28), 37-wizardz (3.11), 01-black-sun (3.03). The plan
  is a `tier_band` input, so this is a live grading defect, not a label problem.
  Editorial work on deck files; no code. Carried as NEXT-SESSION item 0(b).
- `#: protect:` adoption is uneven across the roster. Carried as item 0(a).
- 54 of 114 decks have no explicit `#: plan:` header at all. The seven above are
  the subset where the inference is measurably wrong; the rest are unverified.

DOCUMENTATION UPDATES NEEDED:
- G-09 currently reads "Three fixes were pre-registered and REFUTED … don't
  derive a fourth." A fourth has now been derived, measured and refuted. Worth a
  clause naming it so the next reader sees four rather than re-running this.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
