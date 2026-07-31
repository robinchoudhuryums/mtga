---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- F-01 — `import_collection.plan()` collapsed several export printings onto one library row (last write won, order-dependent silent undercount); plus its read half, `verify_ingest --exact`, which compared a summed owned count against ONE line's quantity.
- F-02 — `deck._multiset` was not DFC front-face aware, so `verify` reported phantom drift on an identical deck and `sync --apply` would have rewritten a stored `Front // Back` name to the bare, un-importable front face.
- F-03 — `card.py` reported owned quantity from a SINGLE printing, contradicting the fungible-across-printings rule on the surface G-01 mandates for pre-grading inspection.
- F-04 — `app.py revert` selected the newest `.bak` by mtime, but `shutil.copy2` preserves the SOURCE's mtime, so revert→save→revert restored the state the first revert had already discarded.
- F-14 — `load_rarities` was the only pool loader without a DFC front-face alias; 47 roster card names resolved to `""`, so `_power_seed` fell to its default floor and every mythic/rare DFC sorted UP the cut list.

Files modified:
- scripts/import_collection.py, scripts/verify_ingest.py (F-01)
- scripts/deck.py (F-02, F-14), scripts/build_dashboard.py (F-02, client-side half)
- scripts/card.py (F-03)
- scripts/lib.py, scripts/app.py (F-04), CLAUDE.md (F-04 rule, corrected in place)
- scripts/check_patterns.py (registry entry for the new `_BAK_STAMP_RE`)
- tests/test_ingest.py, tests/test_verify_ingest.py, tests/test_deck.py, tests/test_lib.py, tests/test_card.py (new)

CHANGES:
F-01 | scripts/import_collection.py | `plan()` now resolves entries in two passes: identical export keys `(front-name, set, collector)` collapse on `max` FIRST — a tracker emitting one printing twice states one holding twice, not two — then the distinct printings that remain SUM onto their library row, which is written once. `added` is keyed and summed the same way, so two lines naming one new printing can no longer append a duplicate `(Card Name, Set Code, Collector #)` row (an INV-01 break written by the importer itself). Verified in both export orders: 1 → 3, not the old order-dependent 1 or 2.
F-01 | scripts/verify_ingest.py | `verify()` sums the paste per LIBRARY ROW before comparing, and results gained a `pasted` field (`qty` still carries the line's own quantity). Owned is summed across printings while a tracker exports one line per printing, so the old per-line compare made `--exact` structurally unable to pass a correct multi-printing import — and, in default lower-bound mode, hid a real shortfall (owned 2 against lines of 2 and 1 passed both `>=` tests while the paste claimed 3). `report()` dedupes the shortfall list by library row and says "summed over N pasted printings".
F-02 | scripts/deck.py | Added `_ms_key` (lowercased, front-face) and `_ms_display` (first-seen wins, except the full `Front // Back` form beats a bare front — that is the spelling a deck file must carry, per P8). `_multiset` uses both. `reconcile_lines` matches existing file lines on `_ms_key` too, and picks the fuller display when appending, so `sync --apply` neither drops a DFC line nor writes a bare front name.
F-02 | scripts/build_dashboard.py | The client-side `parseLine` now front-face normalizes its key, matching `deck._ms_key`. The stored side of that compare is `deck._multiset` serialized into `d.cards`, so the browser's stale-check would otherwise keep the phantom drift the CLI no longer reports.
F-03 | scripts/card.py | Added `_owned_index` (summed by name, the same view `deck.load_collection` / `pool.owned_counts` / `wishlist` build) and `_owned_printings`. The OWNED line now goes through `lib.owned_qty` and shows its working when the total spans several printings (`OWNED: 3  [2 printings: FDN×1, M21×2]`). Rugged Highlands 1 → 3, Lightning Strike 1 → 2, Scout the City 1 → 2, Spider-Rex 1 → 2; `card.py` and `deck.py` now agree.
F-04 | scripts/lib.py | Added `backup_stamp` and `latest_backup` next to `backup_path` — the two halves of one scheme. Selection is on the microsecond creation stamp in the NAME, falling back to mtime only when no name carries one (the legacy case F22's mtime selection was reaching for). `backup_path`'s docstring no longer recommends mtime.
F-04 | scripts/app.py | `revert()` selects via `lib.latest_backup`. Verified headless with Flask's test client: save→save→revert→save→revert now lands on the pre-save state, not the discarded one.
F-04 | CLAUDE.md | The atomic-write/backup rule said readers "select by mtime" — the opposite of the shipped behaviour after this fix, and the third place that wrong advice appeared. Corrected in place with the reason.
F-14 | scripts/deck.py | `load_rarities` aliases a DFC's front face in a SECOND pass, after every real pool row is indexed — so a `Front // Back` row cannot shadow a distinct card named `Front` (`Life` is a card as well as the front of `Life // Death`), and the result is order-independent. Roster names without a rarity: 47 → 0. Ojer Axonil's `_cuts_power_adj` goes −0.70 → +0.17, i.e. the nudge changed sign; Avatar Aang / Bruce Banner / Clive each gain 2.5 power. Side effect: `fetch_missing_rarities` no longer makes a Scryfall round-trip for those 47 names.
— | scripts/check_patterns.py | `_BAK_STAMP_RE` registered in `_EXCLUDED` with a reason (a `.bak` FILENAME pattern, not card text). The completeness gate caught it on the first run — working as designed.

TEST RESULTS: PASSED. `python3 scripts/check_all.py` — all invariants hold, zero soft warnings, exit 0. `pytest` — **802 passed** (was 767; +35 new anchors, 0 pre-existing failures). All twelve gates green standalone, including `check_patterns` (145 live), `check_dfc`, `check_agreement`, `check_docs` (87 anchors). One failure occurred mid-session — `check_patterns` rejecting the unregistered `_BAK_STAMP_RE` — caused by this session's changes and fixed here.

Regression Scenarios walked (Subsystems overlapping modified files):
- Scenario 1 (Ingest a batch) — **PASS**, on scratch copies. `import_arena` → `verify_ingest` reports clean on the lower-bound route; `--exact` correctly rejects a deck-dump paste. `make refresh` step NOT RUN (needs Scryfall egress and would rewrite derived data unrelated to this diff).
- Scenario 2 (Analyze a deck) — **PASS**. 41 command invocations plus every script's `--help` and one subcommand help: no traceback.
- Scenario 3 (Refresh derived data) — **NOT APPLICABLE**. No derived-data builder was modified, and `atomic_write`/`backup_path` behaviour is unchanged (new functions only, plus a docstring).
- Scenario 4 (Edit via the app) — **PASS**, headless via Flask's test client on a scratch CSV: save, save, revert, save, revert (F-04's acceptance path), remove, index and /decks all correct; the cross-origin and non-loopback-Host guards still return 403.
- Scenarios 5–8 — **NOT APPLICABLE to programmatic verification**; they are the perceptual/browser checks. Nothing in this diff touches the status-colour tokens, the responsive layer, or the editor's failure-toast paths.

REGRESSION RISKS:
- `_multiset`'s key change reaches `diff`, `verify`, `sync`, `match_paste`, `_ms_delta` (git history) and the dashboard Finder. All compare multiset-to-multiset or were repointed at `_ms_key`; verified no roster deck contains two genuinely different cards that front-key to the same value, and an `arena` → `verify` round-trip across all 74 roster decks reports 0 drifted. The Finder searches on the display name, so front-keying only MERGES a card previously split across two spellings.
- `load_rarities` returning more keys changes `fetch_missing_rarities`' "todo" set — strictly fewer network calls for names now resolvable offline. No caller uses rarity-key ABSENCE as a semantic signal.
- `verify_ingest.verify()` result dicts gained a key (additive) and `enough` is now per-card rather than per-line. Only `report()` and the tests consume them.
- Residual, unchanged by this work: front-face keying would merge a `Front // Back` card with a distinct card literally named `Front`. Zero such collisions exist in the current pool or on the roster; both new code paths (`load_rarities`' second pass, `_ms_key`) are written so a real row always wins.

INVARIANTS AT RISK: None — re-verified directly. INV-01 `validate` rc 0; INV-02 zero library names missing a mana row; INV-03 derived files keep their own headers (`check_all` clean); INV-04 zero decks with unparseable cards. INV-01 is now *better* protected: `import_collection` can no longer append a duplicate printing row.

NET SCORE: 5 production fixes − 0 new failure modes = **5**
(Per-fix: would it have fired this month? F-02 YES — 14 deck files carry a `Front // Back` line and decks 49/51/51a were built or tuned this cycle; F-03 YES — 4 cards currently mis-report and `card.py` is the mandated pre-grading read; F-14 YES — 47 roster cards, and `cuts` ran this cycle per the ledger's 2026-07-31 rows; F-01 NO — no collection import is recorded this cycle; F-04 NO — needs a revert→save→revert in the optional editor. New failure modes: none. The one this fix nearly introduced — accumulation double-counting a repeated export printing, where the old last-wins was right — was closed by collapsing identical export keys on `max` before summing, and pinned by a test.)

OPERATOR ACTIONS / DEPLOY:
- None. | BLOCKS DEPLOY: N
Deploy: Presentation subsystem — `.github/workflows/pages.yml` rebuilds `build_dashboard.py` and publishes to GitHub Pages automatically on push to `main`; the F-02 client-side fix reaches the published dashboard on that rebuild. Data + local tooling ship by commit/push (no build step). NOTE: the committed `dashboard.html` still carries the OLD client-side key until someone regenerates it — deliberately not rebuilt here, since it would add ~1.2 MB of unrelated data churn to this diff.

FOLLOW-ON ITEMS:
- **F-05 confirmed live, out of scope.** Walking Scenario 1 reproduced it: `card-library.csv` holds Llanowar Elves only under `(M19) 314` ×1, and importing `2 Llanowar Elves (DOM) 168` from a deck dump took the summed owned count to 3. `import_arena`'s `max()` is per-PRINTING while ownership sums across printings, so re-importing the same physical playset under a different printing inflates the count — the opposite of the guarantee its docstring states.
- F-15 (`reconcile_crafts`' front-name pool fallback is a byte-identical no-op of the lookup above it), F-16 (`tier_band` SETS the floor to C on an uncastable stray instead of capping it, so a stray raises a D-floor deck — latent, no roster deck in range), F-17 (`load_keywords` has the same missing front-face alias as F-14, but measured at 1 card and 0 behavioural difference), F-06, F-07, F-08, F-09, F-10, F-11, F-12, F-13, F-18…F-23 — all unimplemented, per scope.
- The `.bak` selection rule now has one definition (`lib.latest_backup`) and exactly one caller. Any future `.bak` reader must use it rather than re-deriving mtime order.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md line 683: `tests/ (16 files: …)` → **17 files** (added `tests/test_card.py`).
- CLAUDE.md **G-63**: the class now has a fifth member on the NAME column — `_multiset`, fixed here — and F-14 is a sixth incident on a new column (RARITY, via a pool-only loader with no front alias). The rule's closing instruction ("when a name contains `" // "`, ask which face the column describes") held; what it did not say is that a *loader over a pool-keyed file* is the shape that keeps re-introducing it. Worth naming the five loaders that alias and the two that did not.
- CLAUDE.md Key Design Decisions, "Owned copies are fungible across printings": the enforcement list names `deck.py`, `pool.py` and `lib.owned_qty` — `card.py` now belongs in it (it was the violation).
- README `import_collection.py` section: state that several export printings of one card SUM onto the library row it resolves to, and that a repeated printing does not.
- README `verify_ingest` / `--exact` description: the comparison is now per CARD (summed across pasted printings), not per line.
- `docs/systems-map.md` §7 and README's ledger figures still quote n=52 (63% / 90% / 45%); the live ledger is n=100 at 62% / 83% / 42% (broad-scan F-23, not implemented).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
