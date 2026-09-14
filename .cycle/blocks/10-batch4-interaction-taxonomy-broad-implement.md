---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: BS10-01 (permanent steal / exchange scored no interaction role —
FIXED). BS10-02 (one-turn tap-down scored no interaction role — **REFUTED**: it is a
documented deliberate exclusion, not a hole, and the exclusion stands).

Files modified: scripts/deck.py, decks/47-affinity/deck.txt, decks/43-overdraft/deck.txt,
CLAUDE.md, docs/gotchas.md, scripts/role_baseline.txt, dashboard.html

CHANGES:
BS10-01 | scripts/deck.py (`_ROLE_PATTERNS["Removal (spot)"]`) |
  Permanent steal and exchange — `gain control of target …`, `exchange control of …` —
  scored no interaction role on **91 of 98** pool cards, against the bounce sibling's 4%.
  Taking their creature answers it AND keeps it, and this module already treats the effect
  as an answer: the shrink-Aura guard upstream calls Duskmourn's Domination's "You control
  enchanted creature" a Control-Magic steal and a real answer. Only the `gain control of
  target` templating had no pattern.
  **Half the family is not an answer, and it is the larger half.** A THREATEN ("gain control
  of target creature UNTIL END OF TURN. Untap it. It gains haste") hands the creature back —
  an alpha-strike or sacrifice-outlet enabler. **48 of the 103 steal cards are that shape**
  and stay OUT; counting them would inflate exactly the decks that run them. That is the
  PERMANENCE line the neutralization block already draws, and the call G-62 makes about
  blind mill.
  CLAUSE-SCOPED, not a proximity window: the duration cue sits in the same sentence but on
  EITHER side of the phrase (Grishnákh reads "until end of turn, gain control of…"), which
  is G-67's rule to fix the CLAUSE rather than widen the window. **The trailing temper must
  be anchored on `(?:\.|$)`** — a bare `{0,N}` with nothing after it matches zero characters
  and excludes nothing, which is how my first draft let Act of Treason and Captivating Crew
  through while reporting a plausible count.
  Three exclusions, each earned by reading a card in full: an OPPONENT gaining control is a
  DONATION (Harmless Offering, Discerning Financier); "gain control of target OPPONENT" is a
  player, not a permanent (Emrakul, the Promised End); "until the end of your next turn" is a
  second Threaten templating (Evil's Thrall). Validated against a hand-graded list of 10 that
  must stay out and 10 that must come in: **20 of 20**. 43 matches, 38 newly scoring a role.

BS10-02 | scripts/deck.py (comment only — NO pattern change) | **REFUTED.** The scan measured
  the one-turn tap-down family ("doesn't untap during its controller's NEXT untap step") as
  33 of 34 scoring no interaction role. The two templatings are genuinely disjoint — 37
  permanent / 39 one-turn, **zero overlap** — which reads exactly like G-67's
  family-disagreement signature. It is not one. The block's own comment had already drawn the
  line: *a one-turn effect is TEMPO, not an answer*, and *a tempo card read as removal would
  inflate the axis the tier floor grades on, which is the BS2-06 failure*. Widening it would
  have added 36 cards to that axis, in the direction the paragraph exists to prevent.
  I nearly shipped it: the diagnosis "one word — the pattern says `controller's untap step`
  and every card says `controller's NEXT untap step`" was written before I read the comment
  four lines above the pattern. **A measurement counts the EFFECT and cannot see the
  DECISION.** The refutation is now recorded AT the exclusion, where someone re-filing it
  will land, and the cited figure was re-grounded 35 → 39 while I was there. The two outcomes
  are consistent rather than merely coexisting: the same permanence line that keeps one-turn
  tap-down out is what makes the steal pattern exclude Threatens.

K-12 CONSEQUENCES (mandated by the role-pattern change, not separate findings):
  - **decks/47-affinity** — its `#: tier:` block had argued "THE INTERACTION FIGURE
    UNDER-READS … Trade the Helm … is an answer, and 79 of 84 such pool cards score no
    interaction role at all. Counted by hand the suite is one piece larger than the vector
    says." That argument is now obsolete in the best way: the pattern was added, Trade the
    Helm scores, interaction went 6 → 7 and the floor B → A. Block rewritten to say so.
  - **decks/43-overdraft** — its `#~ note:` current-state figure re-grounded 5 → 6 (Bilbo,
    Luckwearer's "exchange control of two target nonland permanents" Adventure half).
  - **CLAUDE.md** — the tier-floor spread the rubric cites as its evidence, A 67 / B 41 /
    C 4 top band 60% → **A 68 / B 40 / C 4, top band 61%**. Caught by `figure_drift`.
  - `role_baseline.txt` pruned by 1 (trade the helm) via `make postedit`.

TEST RESULTS: passed — `python3 -m pytest` **1796 passed, 0 failed** (257s); `check_all`
  **All invariants hold ✓**; `make postedit` exit 0; `check_patterns` 354 patterns all live.
  Regression Scenario 2 (Analyze a deck) walked: **29 of 29 PASS**.
  Remaining soft warnings are the three pre-existing dead library searches (20a / 50a / 69a).
  **A SUPPRESSION HID A REAL STALE FIGURE AND THE SUITE STAYED GREEN** — see REGRESSION RISKS.

REGRESSION RISKS:
  - **The roster figure sweep did NOT catch deck 47, and that is the finding of this batch.**
    After the change, deck 47's prose said "interaction 6" against a live 7 and both
    `tier --audit-rationale` and the pytest roster sweep reported CURRENT. Traced:
    `_figure_is_history` suppresses any figure with a `_COMPARISON_CUES` hit within ±60
    chars, and the phrase **"rather than"** — which I wrote into that block myself in the
    previous batch, 46 characters before the number — silenced the entire live-vector
    listing (interaction, card advantage, protection, avg MV, central themes, all five).
    G-26 says a false positive is noisy and gets noticed while a false NEGATIVE is silent;
    this is that, and it means the K-12 discipline "the suite will name every stale deck"
    is only as good as the prose's wording. Rewritten to move the listing out of the
    comparison window, then **watched it fail**: planting "interaction 9" now flags, which
    it did not before. Logged as a follow-on — the general defect is not fixed here.
  - `classify_roles` feeds `role_tally`, which `tier_band` grades on, so this change can
    move tier floors by construction. Measured with an ASSERTING harness (the batch-3
    lesson): **1 of 112 floors moved** (deck 47 B → A), interaction up on exactly 2 decks
    (43: 5→6, 47: 6→7), `cuts` top-3 on 1, bands 67/41/4 → 68/40/4. Both changed cards were
    identified by diffing `classify_roles` against the pre-change module rather than guessed.
  - Deck 47 is now claimed B against an A floor, so `deck.py tier` prints the
    possibly-under-graded nudge. That is correct behaviour for a rationale that DEFERS the
    call (the rubric's documented shape), and the letter is a **human judgment** — not
    written here. It is the one thing this batch leaves for the user.
  - Old behaviour better anywhere? For BS10-02, yes — which is why it was not changed. For
    BS10-01 the risk is over-counting Threatens, which the permanence line and the 20-of-20
    validation address directly.

INVARIANTS AT RISK: None. No CSV writer touched; card-pool.csv / card-library.csv unchanged
  (this batch changes a classifier, not stored data). INV-04: the only deck files edited are
  43 and 47, and only `#: tier:` / `#~ note:` prose lines — no card line, no
  `(SET) COLLECTOR#`, so G-65/G-77 do not apply; both re-parse clean. INV-01/01b/02/03/05/06
  untouched.

NET SCORE: 1 − 0 = 1
  Production fixes (1): **BS10-01**. It fired this month and was found from the inside —
  deck 47's own tier block had been arguing, in writing, that its interaction figure was one
  low because of this exact hole, and the hand count it relied on is now what the model says.
  NOT counted: BS10-02 is a REFUTATION, not a fix. It changed no behaviour. Recording it is
  worth more than a change would have been, because the next scan will re-raise it.
  New failure modes (0). One residual, stated not introduced: the steal pattern is
  clause-scoped, so a Threaten whose duration cue sits in a DIFFERENT sentence from the
  gain-control phrase would be counted. Zero pool instances today; the templating is
  consistently single-sentence.

OPERATOR ACTIONS / DEPLOY:
- **A tier-letter decision is open for the user**: deck 47 claims B and its metrics floor is
  now A. The rubric permits one band under when the prose argues it (this one names three
  risks: the deck is unbuilt with 10 craft targets, protection is thin, the curve climbed).
  Re-grade or leave — never auto-written. | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds and publishes dashboard.html
  on push to `main`. The committed snapshot was refreshed by `make postedit`.

FOLLOW-ON ITEMS:
- **The comparison-cue suppression is a live blind spot in the audit K-12 depends on.**
  `_figure_is_history` silences every figure within ±60 chars of a `_COMPARISON_CUES` word,
  and the roster's prose puts "rather than" / "instead of" / "variant" next to live-vector
  listings routinely. Deck 47 hid five figures behind one such word for a full cycle. A
  plausible fix is to stop suppressing when the figure sits in an explicit live-state
  listing ("Live vector:", "vector:"), but that needs the roster-wide precision sweep G-26
  demands before it is trustworthy — not done here.
- BS10-01's own residual: a Threaten whose duration cue is in a different sentence would be
  counted. Zero instances today; re-check after a pool rebuild.
- Still open from earlier blocks: a `/sync-docs` pass for G-02/G-43/G-58 (BS10-08's
  back-half flag) and G-38/G-22 (the ranking-window footer and the median-407 measurement).

DOCUMENTATION UPDATES NEEDED:
- DONE: `docs/gotchas.md` G-67 gained a section carrying BOTH outcomes and the transferable
  rule — **before widening a role bucket, read the comment at the exclusion; a measured gap
  is evidence that a pattern does not match something, not that it should.** CLAUDE.md's
  G-67 bullet is at its 15-line cap, so the evidence went to the long form, which is what a
  session doing a role-pattern change is told to read. Tier-floor spread figures re-grounded.
- None outstanding for this batch.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
