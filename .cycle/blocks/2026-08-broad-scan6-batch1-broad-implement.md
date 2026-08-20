---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- 2.1 | The NEUTRALIZATION bucket — 124 pool cards that answer a creature by turning it off, scoring zero interaction
- 1.1 | Register the tagger↔classifier disagreement as a standing, baselined sweep
- 1.2 | Widen `check_dfc`'s builder scan to library-shaped name indexes (and fix the 4th BS6-01 instance it found)
- 1.3 | A freshness contract for the committed dashboard

Files modified: scripts/deck.py, scripts/check_roles.py, scripts/check_dfc.py,
scripts/check_all.py, scripts/build_dashboard.py, scripts/verify_ingest.py,
scripts/role_baseline.txt, scripts/tag_role_baseline.txt (new), tests/test_deck.py,
tests/test_gates_fire.py, tests/test_check_dfc.py

CHANGES:

2.1 | scripts/deck.py, tests/test_deck.py, scripts/role_baseline.txt | Four patterns
  closing the third way Magic answers a creature. This bucket read `destroy` and `exile`
  and not `turn it off`, even though Pacifism's `can't attack or block` has been in it all
  along — the repo had already decided a neutralizing effect IS spot removal, and only
  half the templatings were written.
    (1) TAP-DOWN, permanent — 37 cards (Waterknot, Capture Sphere, Frozen in Ice, Dungeon
        Geists, Tidebinder Mage). `its controller's` is load-bearing: the identical clause
        appears as a DRAWBACK on your own card ("Colossus of Sardia doesn't untap during
        YOUR untap step") and 11 such cards would otherwise read as removal.
    (2) ABILITY-STRIP, Aura — 19 cards (Frogify, Kasmina's Transmutation, Witness
        Protection, Ichthyomorphosis). Same `enchant creature you control` guard as the
        BS6-10 Aura pattern.
    (3) ABILITY-STRIP, targeted — 6 cards (Oko, Patriar's Humiliation, Resolute Rejection).
        `except ` excludes Town-Razer Tyrant's "loses all abilities EXCEPT mana abilities",
        which punishes a land rather than answering a threat.
    (4) ABILITY-STRIP, anaphor — exactly ONE card, and it earns its place by closing an
        INCONSISTENCY rather than adding coverage: The Wondrous Wasp strips "for as long
        as this remains on the battlefield" and Ty Lee, Chi Blocker does the identical
        thing one clause over and was already counted by (1).
  **THE LINE IS PERMANENCE, drawn deliberately.** A one-turn effect is TEMPO, not an
  answer, so `NEXT untap step` (Frost Lynx, 35 cards) and `loses all abilities UNTIL end
  of turn / until your next turn` (Merfolk Trickster, Azure Beastbinder) are excluded.
  That is the conservative direction: a tempo card read as removal would inflate the axis
  the tier floor grades on, which is BS2-06's failure.
  **K-14 roster diff over 113 decks: 6 decks moved interaction, ZERO tier floors moved,
  ZERO tier letters need re-grading.** 15 +2; 16, 27, 32, 38a, 38 +1 — exactly the six the
  audit predicted. Deck 38 moves 3→4, off the B floor it was sitting exactly on. All six
  `#: tier:` rationales audited clean afterwards (no figure went stale). `role_baseline.txt`
  lost 2 entries the fix un-zeroed (Frozen in Ice, The Wondrous Wasp) — caught by the
  baseline's own stale-entry sweep, pruned with the delta named per G-69.
  **The payoff is upstream, in what the recommender can see.** Blue's removal is mostly
  neutralization, so it was entirely invisible: `suggest 47 --interaction` now surfaces
  Sleep Magic, Charmed Sleep and Witness Protection — the last of which is already OWNED.
  4 tests added, every fixture verbatim from the card, including four one-turn-tempo
  negatives and the self-referential-drawback negative.

1.1 | scripts/check_roles.py, scripts/check_all.py, scripts/tag_role_baseline.txt,
  tests/test_gates_fire.py | A second sweep in the file that owns "cards the role model
  cannot see": which cards does `tag_synergies` call `removal` from their TEXT while
  `classify_roles` gives them no interaction role? That is K-09's rule, and it is the
  shape that surfaced Dead Weight.
  **I did not build what I proposed in the scan, and the measurement is why.** Stage 3
  suggested a pool-scoped ZERO-ROLE radar; `check_roles._roster_cards` explicitly refuses
  that, and it is right — 5,368 nonland pool cards score no role, 33% of the pool,
  unreadable as a worklist. The DISAGREEMENT set is 143. Build on disagreement, not zero.
  **Scoped by construction, not by an allowlist.** It reads the tagger's own
  `MECHANIC_RULES` predicates rather than a copy, so a third text rule added there is
  swept on arrival and the two cannot drift. The KEYWORD path (`deathtouch` → removal) is
  excluded because it lives in `KEYWORD_THEMES` — that is 250 of the 388 raw
  disagreements, and an allowlist would have had to enumerate them.
  Baselined at 143 with `--tags`, `--update-tag-baseline`, `--max-new` and the G-69 delta
  report; folded into `check_all` as a SOFT warning. **Watched failing**: removing the
  pattern that fixed BS6-10 makes 16 disagreements appear, Dead Weight among them.

1.2 | scripts/check_dfc.py, scripts/verify_ingest.py, tests/test_check_dfc.py | The
  builder scan was POOL-scoped (`DictReader` + a card-pool.csv cue) while every OWNERSHIP
  index reads card-library.csv through `lib.load_rows` — so all four sat outside a scan
  written to find exactly the bug they had. Cue sets widened to cover both files and both
  readers.
  **The widening needed a new discriminator to be readable**: it first reported 8
  unregistered builders, 3 of them printing indexes keyed by `(name, set, collector)`.
  A front-face alias is meaningless for a printing key, so `_tuple_bound_names` rejects
  tuple keys, literal or via a tuple-bound local. That took it to 5, of which 4 register
  and 1 (`reconcile_crafts.reconcile`) is allowlisted with a reason alongside two others.
  **It immediately found a REAL bug**: `verify_ingest.library_index` was the 4th
  library-side ownership index and was still unaliased — so a paste naming a Room card by
  its FRONT face verified as ABSENT, from the tool whose entire job is confirming an
  ingest landed. Fixed.
  **The registry probe was VACUOUS for the new entries and is now not.** The behavioural
  check is `full in idx and front not in idx`, and the pool's first DFC ("Life // Death")
  is not in the collection at all, so `full in idx` was False and every library loader
  passed without being exercised. Added a LIBRARY probe, and a loud "alias NOT exercised"
  line when neither probe reaches a loader — silence was the whole failure. Watched
  failing: stripping `load_collection`'s alias now fires the gate.

1.3 | scripts/build_dashboard.py, scripts/check_all.py, tests/test_gates_fire.py |
  `dashboard_staleness()` compares CONTENT HASHES of the four card CSVs and every deck
  file against the fingerprints the page stored in its own data island when it was
  built; `check_all` reports a mismatch as a soft warning.
  **CORRECTED AFTER THIS BLOCK SHIPPED — the first version compared MTIME** against the
  page's `generated` stamp, which is right in a working tree and wrong everywhere else:
  a fresh clone or CI checkout stamps every file with checkout time, so the sources
  always read newer than the committed page. It reported a permanent, unfixable STALE
  and failed CI on the very PR that added it. That is the F-04 trap — mtime records when
  a file was WRITTEN, not what it CONTAINS — reintroduced one directory over from the
  rule that documents it. Hashing 117 inputs measures at 15ms. INV-03 gives gallery.html a
  content contract and the dashboard had none, so skipping `make postedit` was silent.
  **It watches DATA, not code, and that is deliberate** — a `_ROLE_PATTERNS` edit
  re-scores every deck without touching a watched file, so this stays quiet for that. It
  is the lesson `tagger_fingerprint` paid for twice (BS4-37 hashed deck.py wholesale and
  BS5-06 undid it): a signal that cries wolf every cycle is one an operator waves through.
  A missing or unstamped page is NOT reported as stale — absence is not staleness.

TEST RESULTS: PASSED.
- `python3 scripts/check_all.py` — all invariants hold, ZERO soft warnings.
- `pytest` — 1349 passed, 1 skipped (was 1333 passed, 1 skipped): +16, which is exactly
  the 16 tests added (4 in test_deck.py, 7 in test_gates_fire.py, 5 in test_check_dfc.py).
- Regression Scenario 2 (Analyze a deck) — PASS, walked after the changes.
- Scenarios 5, 6, 7, 8 — NOT RUN: need a person at a browser; none of this touches a
  rendered surface (build_dashboard gained a helper, not a template change).
- Scenarios 1, 3, 9 — NOT APPLICABLE: no ingest, enrich or match path changed, except
  `verify_ingest.library_index`, whose fix is covered by the check_dfc registry.

REGRESSION RISKS:
- The four role patterns can only ADD roles; the roster diff measured 6 decks and 0 tier
  floors, and the tier-mismatch sweep in check_all reports nothing new. Cost measured at
  +0.11s on a whole-pool classify (1.14s → 1.25s).
- `_stores_keyed_by` now rejects tuple keys. Could that hide a real pool builder? A name
  index keyed by a tuple is not a name index, and `test_scan_finds_the_known_builders`
  confirms all five previously-detected pool loaders are still found.
- `verify_ingest.library_index` now returns a front-aliased `qty` and adds front names to
  `names`. A paste naming a front face whose library row is the full name now verifies as
  PRESENT — that is the fix, and it matches `lib.owned_qty`'s resolution order.
- `check_roles.load_baseline` was refactored to delegate to `_load`; behaviour identical,
  and `check_keywords` has its own separate `load_baseline` that is untouched.
- `check_all` now imports `build_dashboard`, which pulls in `wishlist` — both already in
  the process via other gates. check_all remains green and its runtime is unchanged.
- One thing worth recording because it bit me mid-session: my first attempt to
  mutation-test the DFC registry popped keys out of the MEMOIZED `load_collection` dict,
  which then reported a false failure on the clean run. That is G-71 exactly, in test
  code. The committed test copies the dict.

INVARIANTS AT RISK: None.
- INV-01/02: card-library.csv and card-mana.csv were not written.
- INV-03: no derived file rewritten; gallery.html and dashboard.html untouched (1.3 only
  READS the dashboard).
- INV-04: no deck file edited.
- INV-05/06: no colour data, no synergy tags — the tagger was READ, never changed, so no
  re-tag and no pool rebuild is implied.

NET SCORE: 4 production fixes − 0 new failure modes = 4
  a) Fired this month? 2.1 YES — six decks were under-counting interaction, and blue's
     removal was invisible to the recommender that exists to fix an interaction deficit.
     1.2 YES — it found `verify_ingest.library_index` still broken. 1.1 and 1.3 are
     detectors rather than fixes; neither would have "fired" as a bug, and both would have
     caught one that did.
  b) New failure mode? NO for all four. Each new pattern was measured against the whole
     pool with its false-positive class guarded and tested; both new gates were watched
     failing and are soft; the freshness check cannot report a missing page as stale.

OPERATOR ACTIONS / DEPLOY:
- None. No visual surface changed, so no operator visual check is added by this batch.
  (The two outstanding checks from the previous batch — Scenario 5's dashboard colour bars
  and Scenario 7's three preview surfaces — are still outstanding and unaffected.)
Deploy: Data + local tooling ship by commit/push. The dashboard is the one deployed
artifact and its TEMPLATE did not change, so nothing needs republishing; pages.yml
rebuilds on push to main as usual.

FOLLOW-ON ITEMS:
- **A NEW hole found while measuring 2.1, deliberately not fixed**: Nameless Inversion
  ("Target creature gets +3/-3 and loses all creature types") scores ZERO roles. A
  toughness-reducing PUMP (`+N/-N`) is removal, and the covered shape requires a leading
  minus (`-N/-N`). It is a different family from the neutralization bucket, so it was out
  of scope — and it is now in `tag_role_baseline.txt`, which means the 1.1 sweep is
  already carrying it as a worklist entry rather than losing it.
- The 143-entry disagreement baseline is a worklist, not a defect count. The legitimate
  classes in it are graveyard hate (the tagger's `"exile target"` substring) and
  self-shrinks (its `gets -N/-N`). Reading it down is the natural next pass.
- `wishlist.owned_index` still carries a hand-rolled copy of the `alias_front` loop
  (behaviour identical; G-63 says aliasing has one home). It is now REGISTERED in
  check_dfc, so a regression in it would at least be caught.
- Batch 4 hygiene items are untouched: `lib.pool_ability_model`'s non-invalidating cache,
  `card.py:_find` dead code, `_clock_score`'s `or 99.0`, `owned()`'s zero-count
  asymmetry, `load_mana`/`fetch_missing_mana`'s unregistered in-pass aliasing, and
  regenerating ROADMAP.md.
- Batch 2.2 (run `import_collection.py` against a tracker export) and 2.3 (the prune
  keep/cut calls) remain blocked on you, and 2.2 is still the highest-value single item.

DOCUMENTATION UPDATES NEEDED:
- G-67's live residual is now WRONG in CLAUDE.md: it says "124 pool cards neutralize
  rather than destroy … six decks under-count today", which this batch fixed. It needs to
  become the closed record plus the new residual (the `+N/-N` pump family).
- K-09 should record that the disagreement sweep is now a standing gate rather than a
  measurement someone ran once.
- G-63 says the check_dfc scan is POOL-scoped and that this is how BS6-01 hid — now
  historical; the scan covers library-shaped indexes.
- C-01 / the Cycle Workflow Config's gate inventory should mention the two new soft
  sweeps (tag/role disagreement, dashboard freshness) and `tag_role_baseline.txt` belongs
  in the Analysis subsystem file list.
- Suggest `/sync-docs`.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
