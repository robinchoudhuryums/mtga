---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- SHOCKLAND RESIDUAL | `_land_value` withheld the untapped premium from a shockland — the
  third and last surface of the 2026-09-04 tapland defect.
- P3 | `role_tally` counts CARDS, not repeatability; a 1-3 quality SCALE was proposed,
  measured against its consequences, and DECLINED in favour of a report-only split.
- P4 | The rationale audit cannot see an EXISTENTIAL claim about the POOL.

Files modified: scripts/lib.py, scripts/deck.py, scripts/wishlist.py,
scripts/check_patterns.py, tests/test_deck.py, tests/test_wishlist.py, CLAUDE.md,
docs/gotchas.md, dashboard.html (regenerated)

CHANGES:
SHOCKLAND | scripts/lib.py, deck.py, wishlist.py | New `lib.tapland_kind(text)` returning
  None / "shock" / "conditional" / "unconditional". The two regexes MOVED from deck.py to
  lib.py because wishlist cannot import deck (deck imports wishlist), and a third local
  copy is what caused this in the first place — there were THREE implementations of "is
  the tapping conditional?", each missing shocklands differently. "shock" is separated from
  "conditional" because the conditions differ in KIND: a shockland's is payable AT WILL, so
  it earns the untapped premium (the same reasoning already applied to Mana Confluence's
  pay-life cost); a board-state condition may not be met and stays conservative. Hallowed
  Fountain 8.0 -> 9.5, equal to a genuinely untapped dual; Sundown Pass stays 8.0.
P3 | scripts/deck.py | `card_advantage_split()` + a `(N repeatable, M one-shot)` suffix on
  `stats`' card-advantage line. Repeatable = a permanent supplying it through a recurring
  trigger or an activated ability (K-14's own argument); one-shot = an instant/sorcery or a
  single ETB. REPORT-ONLY — `tier_band` still grades the bare int.
P4 | scripts/deck.py | `existential_pool_claims()` + a `?` line in `tier
  --audit-rationale`. Flags sentences asserting something does NOT EXIST in the pool.
  Never auto-verified: the output is "re-check this", not "this is wrong".
GATES | scripts/check_patterns.py | `_CA_ETB_RE` / `_CA_REPEATABLE_RE` registered (raw
  corpus — they read card text); the three P4 prose patterns and the moved tapland trio
  filed with reasons. The gate caught all six, which is it working.

TEST RESULTS: passed. pytest 0 FAILED; `check_all.py` "All invariants hold ✓";
`check_patterns.py` "314 card-text pattern(s) all live ✓"; `check_docs.py` OK;
`make postedit` clean.

REGRESSION RISKS:
- `tapland_kind` moved modules. deck.py's three call sites and check_patterns' registration
  were updated together; no test imported the regexes directly (they call
  `tapland_profile`). `tapland_profile` and `·tapped?` behaviour is unchanged — only
  `_land_value` gains the premium, which is the fix.
- P3 and P4 are additive report surfaces; no scoring path reads either.
- `stats` card-advantage line is now longer. `tests/test_cli.py` covers the command; suite
  green.

INVARIANTS AT RISK: None. No CSV, schema or deck line touched.

NET SCORE: 3 production fixes − 0 new failure modes = 3
  SHOCKLAND: would it have fired this month? YES — it mis-valued every shockland while the
  reporting surfaces said the opposite, which is worse than either being wrong alone.
  P3: YES — two deck-57 decisions leaned on the flat integer this session.
  P4: YES — the false "no untapped dual exists" claim drove two decisions.

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: commit/push; pages.yml republishes the dashboard from `main`.

FOLLOW-ON ITEMS:
- **P4 is deliberately NOT in `check_all`.** The roster sweep measured 7 hits, tightened to
  5, of which 4 are genuine — a standing warning at 80% precision that fires on 5 decks
  every run is the G-07 shape that trains you to ignore it. It lives in
  `tier --audit-rationale`, where a human is already reading the argument. Revisit only
  with a measurement, not a hunch.
- **The automated P3 split is MORE generous than a hand read.** On deck 57 it calls Ral and
  Ghost-Spider repeatable (loyalty abilities and a counter-sink genuinely are, in
  principle) where a human counting "engines" would say only Charred Foyer. That is the
  structural distinction working as specified, and it is recorded in gotchas so the
  difference is not mistaken for a bug.
- **The `match` follow-on remains blocked** on the entry-condition gap (Command Bridge).
- P5 (`#~` swap-line figures outside `note_figure_staleness`) remains open.

DOCUMENTATION UPDATES NEEDED: None outstanding. G-35 names `lib.tapland_kind` as the one
predicate; K-12 carries the split and the declined scale, with the evidence (including the
CONNIVE example the 15-line cap pushed out) in docs/gotchas.md.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
