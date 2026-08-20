---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- FOLLOW-ON | The `+N/-M` LETHAL-SHRINK removal hole (found while measuring the neutralization batch)
- FOLLOW-ON | `wishlist.owned_index`'s hand-rolled copy of the alias loop
- BS6-08 | `lib.pool_ability_model` memoized on a bare `if _cache:` — first call won permanently
- BS6-05 | `card.py:_find` dead code whose docstring read as live guidance
- BS6-12 | `_clock_score`'s `vec.get("avg_mv") or 99.0` falsy-zero
- BS6-07 | `owned()` returned "not in library" for a stored count of a real 0
- BS6-09 | `load_mana` / `fetch_missing_mana` aliased in-pass with `setdefault`, unregistered
- ROADMAP | Regenerated against live state (was 8 days and two cycles stale)

Files modified: scripts/deck.py, scripts/lib.py, scripts/card.py, scripts/wishlist.py,
scripts/check_dfc.py, ROADMAP.md, tests/test_deck.py, tests/test_lib.py

CHANGES:

FOLLOW-ON (+N/-M) | scripts/deck.py, tests/test_deck.py | `target creature gets -N/-N` was
  covered (120 cards) and its twin `gets +N/-N` was not, so Auger Spree, Nameless Inversion,
  Lash of Malice, Flowstone Infusion and Desperate Measures scored zero roles.
  **The permanence rule from the neutralization batch does NOT transfer, and that is the
  whole reason this is written separately.** A `-4/-4 until end of turn` still KILLS, and a
  dead creature does not return at cleanup — so unlike an ability-strip, the temporary
  version does permanent work. Auger Spree is a removal spell in a way Merfolk Trickster is
  not, despite both saying "until end of turn". This family is graded on LETHALITY.
  Scoped to the TARGETED spell: 29 pool cards carry a `+N/-M` clause and 23 are
  firebreathing-style self-pumps on your own body, the same drawback-vs-answer split
  `its controller's` handles for tap-down. `target … creature` plus a `you control` guard
  isolates the 5 real ones, zero false positives. The AURA form is deliberately left out —
  Immolation reads as removal and Mogis's Favor (+2/-1) reads as a pump, two cards a shape
  test genuinely cannot separate. **K-14: 0 decks moved, 0 tier floors.**

FOLLOW-ON (wishlist) | scripts/wishlist.py | Replaced the fourth private copy of the alias
  loop with `lib.alias_front`. Behaviourally identical, which is exactly why it was worth
  removing: G-63 gives aliasing ONE home so a future correction reaches every caller, and a
  loop that merely happens to agree today is the drift shape this repo keeps paying for.
  Its three siblings were routed through the helper in BS6-01; this was the hold-out.

BS6-08 | scripts/lib.py, tests/test_lib.py | `pool_ability_model` now memoizes on the pool
  file's (mtime_ns, size) like every other reference-table loader, and exposes
  `cache_clear()`. It used `if _cache:`, so the FIRST call won for the life of the process:
  a `build_pool.py` run inside `app.py` served the old model afterwards, and a first call
  made before the pool existed pinned the EMPTY model — which is the silent case, because
  `card_distinctiveness` then falls back to the structural term alone and `cuts`' `Uq`
  co-signal flattens with nothing printed. Verified: repointing `_POOL_CSV` at a missing
  file now returns n=0 where it previously returned the stale 16,067.

BS6-05 | scripts/card.py | Deleted `_find` (zero references across scripts/ and tests/,
  confirmed by AST). Left a NOTE in its place rather than a clean deletion: its docstring
  ended with a warning not to chain two of them with `or`, i.e. it survived as a documented
  invitation to re-introduce the BS-02 shadowing bug, and a silent deletion invites the next
  person to write it again. The note says why `_resolve` exists — exactness has to outrank
  SOURCE, which a per-source helper structurally cannot express.

BS6-12 | scripts/deck.py, tests/test_deck.py | `_clock_score` reads `vec.get("avg_mv")` and
  substitutes 99.0 only for `None`. `0.0 or 99.0` is 99.0 — the falsy-zero trap `card_power`
  and `owned_qty` each carry a paragraph about, sitting in the one function that can RAISE a
  tier band. The effect was conservative (no clock credit) so nothing was mis-graded; the
  shape is what mattered.

BS6-07 | scripts/deck.py, tests/test_deck.py | `owned()` ended `return (qty, True) if qty
  else (0, False)` — truthiness, not membership — so a stored count of a real 0 read as NOT
  IN LIBRARY, the exact string G-10 sends you to `reconcile_crafts.py` about, pointing at a
  row already there. Now membership-tested on both the full and front keys.
  **My first attempt at this was wrong and is worth recording**: I inlined the front-face
  split, which re-implements `lib.owned_qty` and is precisely the A3/A4/F6 bypass
  `check_dfc` statically bans. Corrected to keep the COUNT coming from the shared helper
  and compute only the membership flag locally.

BS6-09 | scripts/deck.py, scripts/check_dfc.py | `load_mana` and `fetch_missing_mana` now
  alias through `lib.alias_front` in a second pass instead of `setdefault` in-pass, and
  `deck.load_mana` is registered in the DFC behavioural registry. The in-pass form was SAFE
  — a real card's own row is a direct assignment and always wins over a DFC's `setdefault`
  whatever the file order — but "safe by accident of assignment order" is a property nobody
  verified and nothing gated: these read card-mana.csv, which even the widened builder scan
  does not reach. In `fetch_missing_mana` the alias deliberately runs after the whole batch,
  because aliasing mid-batch could let an early DFC claim a key a later real card owns.

ROADMAP | ROADMAP.md | Regenerated. It was measured against 2,186 printings / 103 decks /
  1,253 tests / 9 matches against a live 2,368 / 111 / 1,362 / 15. Records outcomes honestly,
  including the two items that did NOT move: `import_collection.py` has been top of the
  handoff for four cycles, and the launchd archive still has a real deadline. Tier 3.4
  (close the classifier gap) is marked SUBSTANTIALLY ADVANCED **by a route the file did not
  predict** — it estimated L/1–2mo for a structural fix, and what worked was cheaper and
  different. The strategic bet is unchanged but sharpened: matches went 9 → 15 while
  PROVISIONAL decks went 41 → 51, so play volume is LOSING GROUND to deck creation, which is
  why coarser outcome aggregation now sits beside the bet rather than behind it.

TEST RESULTS: PASSED.
- `python3 scripts/check_all.py` — all invariants hold, ZERO soft warnings.
- `pytest` — 1362 collected, all passing (was 1349): +13, exactly the tests added.
- `check_docs.py` — OK.
- Regression Scenario 2 (Analyze a deck) — PASS.
- Scenarios 5, 6, 7, 8 — NOT RUN: need a person at a browser; no rendered surface changed.
- Scenarios 1, 3, 9 — NOT APPLICABLE: no ingest, enrich or match path touched.

REGRESSION RISKS:
- The `+N/-M` pattern can only ADD roles and moved no deck. The self-pump exclusion is
  pinned by three negative fixtures.
- `owned()`'s return CONTRACT is unchanged ((count, in_library)); only the in_library flag
  for a zero-count row changes, False → True. Consumers: `cmd_check` (prints "NOT IN
  LIBRARY" vs "short"), `deck_build_gap` (missing vs short). A zero-count row now counts as
  SHORT rather than MISSING — which is the intent, and no library row carries 0 today, so
  the live output is byte-identical.
- `lib.pool_ability_model` gained a stat() per call. Negligible, and it is what every other
  loader here already pays.
- `load_mana` returns the same mapping; only the aliasing pass moved. `check_dfc` now
  exercises it behaviourally.
- `card.py:_find` had zero callers — verified by AST across scripts/ and tests/, not by grep.
- ROADMAP.md is prose; nothing reads it programmatically.

INVARIANTS AT RISK: None. No canonical CSV, deck file, colour data or synergy tag was
written. The tagger was not touched, so no re-tag and no pool rebuild is implied.

NET SCORE: 7 production fixes − 0 new failure modes = 7
  a) Fired this month? The `+N/-M` hole YES in principle (the recommender could not offer
     those 5 cards) though no deck runs one. BS6-08 YES in `app.py`'s long-lived process.
     The rest are latent-by-construction (BS6-07 needs a zero row, BS6-12 needs a zero
     curve, BS6-09 was safe by ordering) or hygiene (BS6-05, wishlist, ROADMAP) — fixed
     because the SHAPES are ones this repo has been burned by repeatedly, not because they
     were firing.
  b) New failure mode? NO for all seven. One near-miss, recorded above: my first BS6-07 fix
     re-implemented `owned_qty` inline and was corrected before it landed.

OPERATOR ACTIONS / DEPLOY:
- None new. The two visual checks from earlier batches remain outstanding, and ROADMAP Tier
  1 now lists them explicitly alongside the two operator-only items that have been deferred
  for four cycles.
Deploy: data + local tooling ship by commit/push. No rendered artifact changed.

FOLLOW-ON ITEMS:
- The 143-entry disagreement worklist is now ROADMAP Tier 1.4 rather than an unowned note.
  Its known-legitimate classes are graveyard hate and self-shrinks; what is left is the next
  batch of whitelist holes, pre-sorted.
- The AURA form of `+N/-M` (Immolation vs Mogis's Favor) is deliberately unclassified — a
  shape test cannot separate a curse from a pump there, and both are single cards.
- `docs/systems-map.md` is still measured against 64 decks / 1,853 cards (ROADMAP Tier 2.5).
- Everything else from Batch 5 (sideboard model, coarser match aggregation, ownership
  freshness stamp) is now carried in the regenerated ROADMAP rather than only in a block.

DOCUMENTATION UPDATES NEEDED:
- G-67's live residual names `target creature gets +N/-N` as the open hole; it is now
  CLOSED, and the remaining residual is the AURA form plus the disagreement worklist.
- K-09 / G-63 are current as of the last `/sync-docs` and unaffected by this batch.
- Suggest `/sync-docs` for the G-67 residual only — it is one bullet.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
