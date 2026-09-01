---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- T-01 | `_ROLE_PATTERNS` missed the PLURAL verb and the "to ANOTHER target" templating in the
        three damage-equal-to removal patterns (G-67 whitelist hole)
- T-02 | `wishlist.py --add` silently accepted `--target` / `--note` and wrote BLANK cells —
        a documented /add-wishlist step with no tool behind it (G-53 shape)
- T-03 | Ten deck directories are zero-padded ON DISK and no by-id command accepted the
        padded id (`deck.py stats 06` failed while `6` worked)

Files modified:
  scripts/deck.py, scripts/wishlist.py, scripts/check_all.py,
  tests/test_deck.py, tests/test_wishlist.py, tests/test_check_all.py,
  decks/28-triceraton/deck.txt, decks/28-triceraton/28a-owned.txt,
  decks/72-goblin-town/deck.txt, decks/78-team-avatar/deck.txt,
  scripts/role_baseline.txt, dashboard.html

CHANGES:

T-01 | scripts/deck.py | Widened four patterns in the damage-equal-to family. `deals damage`
  -> `deals? damage` on all four (three removal + the Burn/drain sibling, kept consistent),
  and `to (?:any target|target …)` -> `to (?:any target|(?:another )?target …)` on the two
  scaling-removal patterns plus the up-to-N twin.
  WHY BOTH HALVES: the plural verb was the reported bug (Allies at Last says "each DEAL
  damage equal to their power" and scored zero interaction), but measuring it surfaced the
  bigger half — "to ANOTHER target creature" is the commonest bite/fight templating, and the
  TARGET-FIRST sibling pattern had carried `(?:another )?` since it was written while these
  two never got it. Verb alone: 5 pool cards. Both: 15.
  MEASURED, full pool, zero false positives (each of the 15 points power-scaled damage at a
  target creature; the `(?!player|opponent)` guard is retained and tested):
    verb-only  : Coordinated Clobbering, Friendly Rivalry, Terrific Team-Up, Allies at Last,
                 Graceful Takedown
    +another   : Bolg of the North, Itzquinth Firstborn of Gishath, Breaking of the
                 Fellowship, Garruk Savage Herald, Cosmic Hunger, Tandem Takedown,
                 Fall of the Hammer, Mutiny, Markov Retribution, Band Together
  K-12 ROSTER DIFF: 4 decks moved interaction (28a 5->6, 28 7->8, 72 7->8, 78 8->9),
  **0 tier floors moved**. Prose re-grounded in the same change (below).

T-02 | scripts/wishlist.py | `cmd_add(path)` -> `cmd_add(path, target=None, note=None)`;
  stamps `Target` / `Note` onto the rows THIS RUN added (never a re-add, so a hand-set
  Target survives), reports what it set, and REFUSES an unknown deck id BEFORE any Scryfall
  work rather than writing a dangling Target — the asymmetric validation parse_matches uses
  (G-74) and the refuse-before-network shape the builders' `--out` guards use.

T-03 | scripts/deck.py | New `_norm_deck_id()` strips a zero-padded numeric prefix; both
  sides of `find_deck`'s comparison go through it. The variant branch of `discover_decks`
  now normalizes its digits with `int()` like the core branch, closing a LATENT asymmetry
  (a file named `06a-….txt` would have carried id `06a` against a core of `6`; no such file
  exists, which is why nothing caught it).
     | scripts/check_all.py | INV-04's duplicate-id gate re-keyed on `_norm_deck_id`, so it
  sees exactly the collisions the resolver can now suffer. Keying it on the raw id would
  have left the padding collision invisible to the check built to catch it.

PROSE RE-GROUNDING (same change, mandatory — a model change stales a rationale by
construction, exactly like a swap):
  deck 28a `#: tier:` interaction 5 -> 6; deck 72 `#: tier:` 7 -> 8; deck 78 `#: tier:` 8 -> 9;
  deck 28 `#~ note:` "interaction 7 + card advantage 4 = 11" -> "8 + 4 = 12".
  Deck 78's tier block ARGUED THE HOLE THIS CHANGE CLOSED ("Allies at Last is removal the
  classifier cannot see") — rewritten to record it as history with the fix date, since the
  sentence described a bug that no longer exists.
  `role_baseline.txt`: 2 stale entries pruned (Bolg, Itzquinth now classify) by
  `make postedit`, which per G-69 warns first and acknowledges last.

TEST RESULTS: full suite green (`pytest tests/` exit 0); `check_all.py` all invariants hold;
`check_patterns.py` 288 patterns live; `check_commands.py` OK; `test_determinism.py` green;
`deck.py --help` + six subcommand helps build (G-55 CLI smoke).
  9 new tests, ALL mutation-checked (reverted the fix, watched them fail, restored):
    test_deck.py            : plural-verb removal, another-target removal, another-target
                              PLAYER guard, + TestDeckIdNormalization (5)
    test_wishlist.py        : TestAddStampsTargetAndNote (4)
    test_check_all.py       : padding-collision duplicate id (1)
  ONE MUTANT SURVIVED FIRST TIME and is worth recording: reverting the STORED-id half of
  `find_deck` left the roster tests green, because `discover_decks` already canonicalizes
  core ids — that half only matters for the top-level `<name>.txt` branch, which takes its
  id raw. Added `test_a_non_canonical_stored_id_is_still_resolvable` (monkeypatched
  discovery) so the line is actually exercised rather than shipped untested.

REGRESSION RISKS:
- `find_deck` accepts more inputs than before. `_norm_deck_id` touches the NUMERIC prefix
  only and is pinned against `52a`, `3-brawl`, `0a`, `0` — a variant suffix and a game-type
  id survive intact. Verified every deck id referenced in matches.csv and
  recommendations.csv still resolves (0 unresolvable).
- `cmd_add`'s new params are keyword-defaulted, so the existing positional callers in
  tests/test_wishlist.py are unaffected.
- The widened role patterns feed `tier_band`, `cuts`, the F10 quality guard and `check_all`.
  The K-12 diff above is the guard: interaction only ever ROSE, and no tier floor moved.

INVARIANTS AT RISK: None. INV-04's id gate was STRENGTHENED (re-keyed to the resolver's own
normalization). INV-01/02/03/05/06 untouched — no writer, schema or derived-file path changed.

NET SCORE: 3 production fixes − 0 new failure modes = 3
  (a) T-01 fired every time deck 78's interaction was quoted this session — it read one low
      throughout. T-02 silently dropped data an hour before it was found. T-03 cost a turn.
  (b) No new failure mode: each change is a widening or a normalization with its guard
      retained and tested, and the one under-tested line was caught by mutation and covered.

OPERATOR ACTIONS / DEPLOY:
- None.
Deploy: dashboard is the one deployed artifact — `.github/workflows/pages.yml` rebuilds and
publishes it on push to `main`. The committed snapshot was refreshed by `make postedit`.

FOLLOW-ON ITEMS:
- `suggest-homes` rated FOURTEEN decks KEY for Pinnacle Starcage — the G-31 saturation shape
  for a STRUCTURALLY-valued card, since it scores theme overlap alone. Not fixed here: it is
  a documented residual, and narrowing it is a scoring change that re-ranks every card.
- `card-pool.csv` has no Mana Cost column by design (INV-05), so an MV question about a pool
  card needs a join to card-mana.csv. A sweep written without it returns a clean ZERO, which
  reads as a finding rather than a bug — the G-01 shape one file over. No helper exists; a
  `lib.pool_mana_value(name)` would remove the trap.

DOCUMENTATION UPDATES NEEDED:
- G-67 gains the plural-verb + another-target instance (docs/gotchas.md) with the 15-card
  measurement and the 0-floors K-12 diff.
- A new gotcha for T-02/T-03: a flag that is a FILTER in one mode and silently a no-op in
  another, and an id whose on-disk form the resolver rejects.
- CLAUDE.md Cycle Workflow Config: no field changes.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
