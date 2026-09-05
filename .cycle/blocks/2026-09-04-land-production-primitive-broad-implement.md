---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- PRIMITIVE | `lib.land_production`'s `free` set meant FOUR different things, so ten
  Standard lands that produce little or nothing read as five-colour free sources.

Files modified: scripts/lib.py, scripts/wishlist.py, scripts/check_patterns.py,
tests/test_lib.py, CLAUDE.md, docs/gotchas.md, dashboard.html (regenerated)

CHANGES:
PRIMITIVE | scripts/lib.py | Four shapes separated, each with its own registered pattern:
  * CHOOSE-ONCE-ON-ENTRY -> new `chosen` key. Kept INSIDE `free` so ACCESS counting is
    unchanged (the same generosity a fetch already gets), but reported separately so a
    breadth-aware score declines to credit colours it can never supply at once. Seven
    lands: Uncharted Haven, Night Market, Valgavoth's Lair, Crossroads Village, Mirage
    Mesa, Edgewall Inn, Tarnation Vista.
  * TRANSFORM-GATED (`_TRANSFORM_GATED_RE`) -> excluded. Branch of Vitu-Ghazi taps for
    `{C}`; its "add two mana of any one color" fires only when turned face up via
    Disguise. It scored 10.0, the maximum, and was #1 in dozens of decks.
  * GRANTED TO OTHERS (`_GRANTED_ABILITY_RE`) -> excluded. FOUND DURING THIS FIX, not in
    the original finding: Forgotten Monument gives "{T}, Pay 1 life:
    Add one mana of any color" to OTHER Caves and taps for `{C}` itself.
  * EXTRA NON-MANA TAP COST (`_EXTRA_TAP_COST_RE`) -> `conditional`, not `free`. Scene of
    the Crime costs "Tap an untapped creature you control".
PRIMITIVE | scripts/wishlist.py | `_land_value`'s breadth credit now counts only colours
  the land supplies SIMULTANEOUSLY (`used - chosen`).
PRIMITIVE | scripts/check_patterns.py | All four new patterns registered in the same group
  as the rest of `land_production`'s readers, with the note that each going dead returns a
  land to being a rainbow source silently.
TESTS | tests/test_lib.py | `TestLandProductionExclusions` — one test per shape, one for a
  true any-colour land (must NOT be marked chosen), one guard-rail for tri-land/dual/fetch.

TEST RESULTS: passed. Full pytest suite clean (no F/E markers); `check_all.py` "All
invariants hold ✓"; `check_patterns.py` "311 card-text pattern(s) all live against the
pool ✓"; `check_docs.py` OK; `make postedit` clean.

REGRESSION RISKS:
- Colour SOURCE counts (`deck_source_profile`, and through it `mana`, `consistency`,
  `pip_depth_warning`, `suggest --lands` and the rationale audit's colour figures) are
  UNCHANGED on the live roster: measured, **no deck runs any of the ten affected lands**.
  A future deck adding one now gets the correct count rather than an inflated one.
- `suggest --lands`: the #1 pick moves in 8 of 115 decks, top-5 in 24 — every #1 change is
  a land that fixes nothing leaving the top (Branch of Vitu-Ghazi in all 8).
- Return-shape change: `land_production` gained a `chosen` key. Additive; all three
  consumers (`deck_source_profile`, `suggest_lands`, `_land_value`) read by key.

INVARIANTS AT RISK: None. Read-side scoring only; no CSV, schema or deck line touched.

NET SCORE: 1 production fix − 0 new failure modes = 1
  Would it have fired this month? YES — it did, twice: it put Branch of Vitu-Ghazi at the
  top of deck 57's land list this session, and it is why the `match` follow-on could not
  ship. New failure modes: none; each exclusion is pinned by a test and a live-corpus gate.

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: commit/push; pages.yml republishes the dashboard from `main`.

FOLLOW-ON ITEMS:
- **The `match` follow-on is STILL not safe and stays reverted.** Re-tested on the
  corrected primitive: **88 of 115** decks still change their #1 pick. The remaining cause
  is different and newly identified — the model cannot see an ENTRY CONDITION, so Command
  Bridge ("sacrifice it unless you tap an untapped permanent you control") reads as a
  clean untapped any-colour land. Solve that before re-applying.
- **`_land_value` still withholds the untapped premium from a SHOCKLAND** — the third
  surface of the P2 defect. `tapland_profile` and `suggest_lands`' `cond_tapped` were
  fixed; the FIXING score was not, so Hallowed Fountain scores 8.0 in a WUR deck as though
  it always entered tapped. Recorded in G-35 as a live residual.
- P3, P4, P5 remain open — see `.cycle/blocks/2026-09-04-deck-57-tune-findings.md`.

DOCUMENTATION UPDATES NEEDED: None outstanding — G-35 carries the four-shapes fix and the
shockland residual; docs/gotchas.md carries the measurements and the still-blocked `match`
follow-on with its new cause.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
