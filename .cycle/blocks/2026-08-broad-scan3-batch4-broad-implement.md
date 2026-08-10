---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (Batch 4 — structural debt and the latent DFC class):
- BS4-11 | Rotation flags missing from `suggest --lands/--ramp/--interaction` and `tier --to`'s craft fillers
- BS4-12 | `deck_needs`/`suggest_lands` derived an undeclared deck's colours from IDENTITY while `suggest_scored` uses COSTS
- BS4-18 | In-pass `setdefault` front-aliasing in `enrich.index_card`, `build_mana._store`, `deck.fetch_missing_rarities`
- BS4-19 | `lib.owned_qty` conflated an explicit 0 with "absent" via `or`
- BS4-20 | `wishlist.owned_index` front-aliased unconditionally (no real-row-claims-front guard)
- BS4-32 | The banned `card_power(...) or -1` idiom, in the very function G-16 documents
- BS4-33 | `deck_shape` called a creatureless deck TALL, making "no board-growth axis" unreachable
- BS4-34 | Whole-type-line creature scans in `_deck_summary` and `engine_balance` (back-face class)
- BS4-35 | `effect_redundancy` didn't exclude `_GENERIC_TRIBES` from plan-effects
- BS4-36 | Owned-first sort in three recommenders, contradicting `suggest_scored`'s recorded decision
- BS4-37 | The pool freshness fingerprint hashed only `tag_synergies.py`

Files modified:
- scripts/deck.py, scripts/lib.py, scripts/wishlist.py
- scripts/enrich.py, scripts/build_mana.py, scripts/build_pool.py
- tests/test_lib.py, tests/test_deck_models.py, tests/test_ingest.py

CHANGES:

BS4-11 | scripts/deck.py | `craft_rot_note` now feeds `suggest_lands`, `suggest_mana`,
`suggest_interaction` and `craft_role_fillers`; each renderer prints `⚠rot~YYYY` on a
CRAFT row (owned rows are exempt — an owned card costs no wildcard) plus a summary count.
G-30's lesson is that a craft view without the flag buys rotating cards; `check`,
`wildcards` and `wishlist --rank` had it and these five did not, including the one
CLAUDE.md calls a wildcard-spend planner. Live effect: `suggest 52 --lands` flags 4 of 6
picks, `--ramp` 2 of 3, `tier 61 --to A` flags 2 of its top interaction fillers.

BS4-12 | scripts/deck.py | `deck_needs` and `suggest_lands` derive an undeclared deck's
colours via `_deck_castable_colors` (costs), the rule `suggest_scored` states — "never
color identity, so a card's off-color activated abilities don't widen the deck and
surface uncastable picks". Latent (all 99 decks declare `#: colors:`), and exactly the
G-45 two-siblings-different-filters shape on the paths G-38 routes deficits to.

BS4-18 | scripts/enrich.py, scripts/build_mana.py, scripts/deck.py | All three index the
REAL (full) name in-pass and alias fronts in a SECOND pass via `lib.alias_front`.
In-pass `setdefault` on both keys is the order-dependent shadowing the helper's contract
forbids: a `Front // Back` card seen early claims the bare front key, and a distinct card
of that name arriving later can never claim its own. `check_dfc`'s builder scan cannot see
these — it scans functions reading the POOL, and these index Scryfall RESPONSES.

BS4-19 | scripts/lib.py | `owned_qty` tests `nl in index` instead of `or`. A stored count
of a real 0 — which `import_collection --zero-missing` writes and INV-01 permits — is
falsy, so an explicit "you own none" fell through to the front key. `card_power` in the
same file documents this exact trap for a printed 0; quantity had not had it applied.

BS4-20 | scripts/wishlist.py | `owned_index` sums under the stored name, then adds a front
alias only where no real row claims it. The old loop added the count to BOTH keys, so a
distinct card sharing a DFC's front name would have the DFC's copies added to its total.

BS4-32/33/34/35 | scripts/deck.py | `power_threshold_flags` uses a walrus + `is not None`
(a printed 0 is real — every X-creature is 0/0); `deck_shape`'s `creatures <= 14` nudge
only fires when creatures exist, so a 0-creature spells deck no longer reads "TALL … few
bodies, effects that scale one creature UP" with an empty card list; `_deck_summary` and
`engine_balance` count creatures off `_primary_type` (front face) like `quality`/`shape`;
`effect_redundancy` excludes `_GENERIC_TRIBES`, so a central `Human` tag is no longer a
redundancy bucket every other specific-theme test would reject.

BS4-36 | scripts/deck.py | The three needs recommenders drop `owned` from their sort key,
matching `suggest_scored`'s recorded decision (the goal is the best LIST, and the
owned data is hand-maintained — G-10 saw five wrong counts in one session). The
`cmd_suggest_lands` footer asserting "Owned first" was the visible half of the
contradiction and now says ownership is a note, not a ranking term.

BS4-37 | scripts/build_pool.py | `tagger_fingerprint` hashes `deck.py` as well as
`tag_synergies.py`, because `tags_for` reads `deck.ENGINE_THEMES` through
`_engine_keywords` → `is_noise_keyword` — the BS2-23 blind spot one module further out.
deck.py is hashed WHOLE deliberately: a narrower hash would need a hand-kept list of which
attributes the tagger reaches, which is the registry pattern this repo keeps watching rot.
The stated non-goal: card-mana.csv's keyword frequencies also feed the noise floor and are
NOT hashed, because a content hash of a 2k-row derived file would change on every mana
rebuild and make the reuse fire essentially never. `--refetch` remains the escape hatch.

TEST RESULTS: PASSED.
- `python3 scripts/check_all.py` — "All invariants hold. ✓", exit 0, ZERO soft warnings.
- `python3 -m pytest` — 1,180 tests, all passing, exit 0 (was 1,170; +10).
- CLI smoke: 35 scripts' `--help`, no traceback.
- Regression Scenario 2 walked on deck 52 (stats/shape/cuts/tier/redundancy/targets/
  consistency) plus all four `suggest` needs modes.
- **Every new test was mutation-tested**: reverting each of the four pinned fixes
  (`card_power or -1`, the `deck_shape` unconditional nudge, `owned_qty`'s `or`, and the
  in-pass alias in `enrich.index_card`) is DETECTED. The tests fail against the pre-fix
  code rather than merely passing against the fixed code.

REGRESSION RISKS:
- **BS4-36 changes the ORDER of three live recommender outputs.** This is a deliberate
  behaviour change, not a bug fix — it makes three siblings obey a decision the fourth
  already recorded. At equal score an owned card no longer floats above an unowned one;
  ownership is still printed on every row. If the user prefers the old ordering on the
  LANDS view specifically, that is a one-line revert and a judgment call, not a defect.
- **BS4-37 invalidates the existing pool build stamp** (its fingerprint predates hashing
  deck.py), so the NEXT `make refresh` rebuilds the pool once even though nothing about
  the tagger changed. That is the mechanism working — a fingerprint that never changes is
  the bug it fixes — but it costs one full pool fetch. See OPERATOR ACTIONS.
- **BS4-12 changes nothing today** (all 99 decks declare `#: colors:`), and
  `_deck_castable_colors` is the function `suggest_scored` already trusts. A deck with NO
  colors header now gets a narrower, cost-derived colour set — which is the point.
- BS4-18/20 are behaviour-preserving on today's data (zero front-name collisions in the
  Arena pool, verified in the prior scan); they change WHEN the alias is added, not what
  it resolves to.
- BS4-34 could move a creature COUNT on a deck running a DFC with a noncreature front and
  creature back; `check_all` is green and no roster deck's summary changed visibly.
- BS4-19's fallback path is unchanged when the full name is absent, which is every
  current lookup.

INVARIANTS AT RISK: None.
- INV-01…04 untouched; `check_all` green with zero soft warnings.
- G-63 — BS4-18/20 are net closures of the in-pass-aliasing member.
- G-16 — BS4-32 removes a violation of that rule from the function the rule documents.
- G-25/G-60 — no report-only axis was fed into `tier_band`; `deck_shape` and the rotation
  flags are report-only by construction.
- G-30 — extended, not weakened: the flag now reaches every craft surface.

NET SCORE: 11 production fixes − 0 new failure modes = 11
Per-finding: (a) fired this month? (b) new failure mode?
- BS4-11: (a) YES — every craft recommendation this cycle was unflagged. (b) NO.
- BS4-12: (a) NO (latent). (b) NO.
- BS4-18/20: (a) NO (latent, zero collisions). (b) NO.
- BS4-19: (a) NO — no explicit-0 rows exist yet. (b) NO.
- BS4-32: (a) NO — a 0-bar gate is rare. (b) NO.
- BS4-33: (a) YES for any creatureless deck asked for `shape`. (b) NO.
- BS4-34: (a) Marginal. (b) NO.
- BS4-35: (a) YES on any deck with a central background tribe. (b) NO.
- BS4-36: (a) YES — the ordering was live on every needs run. (b) NO, but it is a
  deliberate behaviour change; see REGRESSION RISKS.
- BS4-37: (a) NO — no ENGINE_THEMES edit landed inside a reuse window. (b) NO.

OPERATOR ACTIONS / DEPLOY:
- The next `make refresh` will do ONE full pool rebuild (~5 min, needs Scryfall) because
  BS4-37 changed the fingerprint definition. Expected, one-time. | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push. No presentation artifact changed.

FOLLOW-ON ITEMS:
- **G-37's documented residual is live and visible**: `suggest 52 --lands` still offers
  `Tarrian's Journal // The Tomb`, `Grasping Shadows // Shadows' L` and `Aclazotz …` —
  cards whose LAND is on the BACK face, reached by transforming, never by a land drop.
  Maindeck one and the deck is a land short with INV-04 seeing nothing wrong. Out of Batch
  4's scope (it is a G-37 residual, not a BS4 finding) but it is the most concrete
  remaining defect I saw, and the rotation flags now sit next to it.
- Batch 5 (interface polish) and the six operator visual checks remain.
- `recommendation_row`'s `Cut Rank` raw-name join; `BASICS` in four modules.
- The committed `dashboard.html` snapshot still carries the pre-BS4-41 loader.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-30: the flag now reaches `suggest --lands/--ramp/--interaction` and
  `tier --to`; the rule currently names only `check`/`wildcards`/wishlist.
- CLAUDE.md G-37: its "Owned first" description of `suggest --lands` is now wrong (BS4-36).
- CLAUDE.md G-18/K-10: the freshness fingerprint covers deck.py too, with the stated
  non-goal about card-mana.csv.
- CLAUDE.md G-63: `enrich`/`build_mana`/`fetch_missing_rarities` join the second-pass
  aliasing list; the in-pass member of the class is now closed everywhere.
- CLAUDE.md G-16: the `or -1` violation it warned about is gone from `power_threshold_flags`.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
