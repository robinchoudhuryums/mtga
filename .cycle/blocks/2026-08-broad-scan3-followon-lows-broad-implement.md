---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (the carried follow-ons + the unbatched Lows):
- G-37 residual | `suggest --lands` offered cards whose LAND is on the BACK face
- BS4-21 | wishlist's Power-provenance comment stated the OPPOSITE of the code
- BS4-23 | `_theme_model`'s 55-70-card window silently excluded any 100-card deck
- BS4-27 | INV-03's gallery leg tested EXISTENCE only
- BS4-38 | reconcile_crafts tracebacked on missing derived files; rewrote the library when only the wishlist changed
- BS4-40 | app.py: unguarded post-write prune, and a Collector # without a Set silently dropped behind a success toast
- BS4-42 | The dashboard's "Wildcards needed" KPI re-parsed a display string
- BS4-44 | `validate.py` accepted Unicode digits its own consumers reject
- follow-on | `recommendation_row`'s `Cut Rank` raw-name join
- follow-on | `BASICS` defined in four modules

Files modified:
- scripts/deck.py, scripts/lib.py, scripts/validate.py, scripts/check_all.py
- scripts/wishlist.py, scripts/reconcile_crafts.py, scripts/app.py
- scripts/build_dashboard.py, scripts/import_arena.py, scripts/import_collection.py
- templates/collection.html
- tests/test_check_all.py

CHANGES:

G-37 residual | scripts/deck.py | `suggest_lands` filters on `_primary_type(...) == "Land"`
(FRONT face) instead of `"land" in type_line.lower()`. The substring scan admitted any
card with `// Land` on its BACK, so three of the four highest-scored picks for deck 52
were Tarrian's Journal (Artifact front), Grasping Shadows (Enchantment front) and Aclazotz
(Creature front) — reached by TRANSFORMING, never by a land drop. Maindeck one and the
deck is a land short with INV-04 seeing nothing wrong, because the line is a valid card
line. **Measured: 81 pool cards were wrongly admitted.** This is the same test
`wishlist._is_land` was fixed to use in BS2-11 — the manabase RECOMMENDER kept the scan
the wishlist was fixed away from. Midgar, City of Mako correctly SURVIVES: its front
really is a land (`Land — Town // Sorcery — Adventure`), the case `lib.primary_type`'s
docstring names.

BS4-44 | scripts/validate.py | Quantity must be ASCII digits. `str.isdigit()` is True for
'²' and '٣', which `int()` then rejects — so such a cell passed INV-01 and crashed every
`int(q) if q.isdigit()` consumer downstream. A gate that admits a value its own consumers
cannot read is worse than no gate: it certifies the row.

BS4-27 | scripts/check_all.py | INV-03's gallery leg checks non-trivial size plus the
`id="data"` island every card is read from. Existence was the whole test, so a zero-byte
or truncated artifact passed exactly as a healthy one did — the exists-but-gutted shape
F-02 hardened the CSVs against, on the third derived file. **Its test fixture wrote
`<html></html>` (13 bytes), which was a test double encoding the old rule; updated as part
of the fix, plus two new tests pinning both failure shapes.**

BS4-42 | scripts/build_dashboard.py | `collect()` emits `wcBy` (structured per-rarity
counts) and the KPI reads it, with the old regex kept only as a fallback for a stale
sessionStorage payload built before the field existed. The panel used to re-parse
`deck._wc_str`'s DISPLAY output with `/(\d+)\s*([MRUC])/g`, so a formatting change there
would silently zero the roster's wildcard needs with everything still green.

BS4-38 | scripts/reconcile_crafts.py | `_read` raises a clean SystemExit naming the file
and the command to run (the tool's own `main()` already did this for the export file, so
the inconsistency was inside one script); and the library is rewritten only when `added or
bumped`, not on any change — a run that merely dropped a wishlist row rewrote an unchanged
600KB inventory and left a `.bak`, the litter import_arena and build_mana were both taught
to avoid.

BS4-40 | scripts/app.py, templates/collection.html | `/api/remove` wraps `_prune_mana`,
which runs AFTER the library write has already landed atomically — an unguarded raise
returned a 500 that the client renders as "Remove failed", telling the user a completed,
non-retryable removal had failed. It now returns ok with a `warning` the client surfaces.
Separately, `_validate_body` REFUSES a collector # with no set code: `_serialize_doc` only
emits the number when a set is present, so the save succeeded, toasted "Saved N card
lines", and the field was gone on reload — a success confirmation for an input the editor
silently dropped (the BS2-28 class, one field over).

BS4-21 | scripts/wishlist.py | The provenance comment said blank is "treated as
hand-graded"; `power_is_seeded` and G-17 both say the opposite, and the comment sat
directly above the constants a future editor reads first.

BS4-23 | scripts/wishlist.py | `_theme_model` accepts 55-70 OR 95-105 cards. The window
silently dropped any 100-card deck from the fingerprint set, so a card targeted at one
would rank "review"/generic while `--audit-targets` still accepted its id — two views
disagreeing about whether a deck exists. **No roster deck is affected today; the handoff
names building a 100-card Historic Brawl deck as a live plan, so this was a trap laid for
the next session rather than a live bug.**

follow-on | scripts/deck.py | `recommendation_row`'s `Cut Rank` lookup joins on `_ms_key`,
matching the `Cut Protected` line beside it. Telemetry only (G-56 keeps the ledger
report-only), but a silently-empty column is what `deck.py feedback` computes agreement
FROM.

follow-on | scripts/lib.py + 4 modules | `BASICS` has one definition in `lib.py`; deck,
import_arena, import_collection and reconcile_crafts import it. Four identical literals
could not drift without someone noticing — but a FIFTH writer forgetting the set entirely
is exactly what happened in BS4-03, and a name you have to import is one you notice you
need.

TEST RESULTS: PASSED.
- `python3 scripts/check_all.py` — "All invariants hold. ✓", exit 0, ZERO soft warnings.
- `python3 scripts/check_docs.py` — OK (95 rules linked).
- `python3 -m pytest` — 1,188 tests, all passing, exit 0 (was 1,186; +2 net after the
  fixture repair).
- CLI smoke: 35 scripts' `--help`, no traceback.
- Regression Scenario 2 walked on deck 52 (11 subcommands); Scenario 1's ingest leg walked
  via reconcile/verify dry runs.
- TWO test failures occurred and were CAUSED BY THIS SESSION: `test_check_all.py`'s INV-03
  fixture wrote a 13-byte gallery stub, which BS4-27 correctly began rejecting. That
  fixture encoded the behaviour being fixed, so it was updated as part of the fix (the
  documented "scan for test doubles first" rule — I found these by running, not by
  scanning, which is the miss worth recording).
- The gallery-content check was mutation-tested end to end: emptying the real gallery.html
  makes `check_all` report it, and the file was restored and re-verified.

REGRESSION RISKS:
- **The G-37 fix removes 81 pool cards from land candidacy.** That is the point, and the
  survivors were spot-checked (Midgar keeps its place because its front IS a land). If a
  deck genuinely wants a transforming back-face land, it is still craftable by name — it
  just is not a MANABASE recommendation, which is the honest reading.
- **BS4-40's collector-without-set rule makes a previously-accepted save FAIL.** A user
  mid-edit with a number and no set now gets a blocking error instead of a silent drop.
  That is strictly better than the toast that lied, but it IS a new refusal.
- BS4-27 makes INV-03 stricter: a repo whose gallery was never built now fails a gate that
  used to pass on a stub. The message names `build_gallery.py`.
- BS4-42 adds a field to the `#data` island. CLAUDE.md's Deploy Command reserves the island
  as the source of truth against RESTYLES; this is a data-correctness fix, and the old
  parse is retained as a fallback so a stale synced payload still renders.
- BS4-23 widens a filter, so a 100-card deck now ENTERS the theme model and shifts idf
  weights slightly. No roster deck is in that band, so nothing changed today.
- The `BASICS` consolidation is a pure re-point (verified: all four modules resolve to the
  same six names). `lib.BASICS` is a frozenset where the locals were sets; nothing mutates
  it (checked).

INVARIANTS AT RISK: None, and two are strengthened.
- INV-01 — BS4-44 closes a hole where a row could pass validate and crash its consumers.
- INV-03 — BS4-27 upgrades the gallery leg from existence to content.
- INV-02/INV-04 — untouched; `check_all` green with zero soft warnings.
- G-56 — the ledger stays report-only; the `Cut Rank` fix is a join, not a read by a
  scoring function, and `test_recommendations.py`'s structural scan still passes.
- G-63 — the G-37 fix is another closure of the TYPE-column member.

NET SCORE: 10 production fixes − 0 new failure modes = 10
Per-finding: (a) fired this month? (b) new failure mode?
- G-37 residual: (a) YES — visible in `suggest 52 --lands` every run. (b) NO.
- BS4-21: (a) N/A, a comment. (b) NO.
- BS4-23: (a) NO — latent, and aimed at the next session. (b) NO.
- BS4-27: (a) NO. (b) NO.
- BS4-38: (a) NO for the traceback; YES for the needless rewrite on any wishlist-only run.
- BS4-40: (a) YES for the collector-without-set drop; NO for the prune (it has not failed).
  (b) NO, though the new refusal is a behaviour change.
- BS4-42: (a) NO — `_wc_str` has not changed format. (b) NO.
- BS4-44: (a) NO — no such cell exists. (b) NO.
- Cut Rank: (a) YES for any DFC swap. (b) NO.
- BASICS: (a) N/A, structural. (b) NO.

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push. `build_dashboard.py` changed (BS4-42), so
the published page picks it up on the next push to `main`; the committed `dashboard.html`
snapshot was NOT regenerated this session (it is a ~2 min step and the change is a KPI
data path, not a visual one) — run `make dashboard` when convenient.

FOLLOW-ON ITEMS:
- **G-37's TWO remaining scoring residuals are untouched** and still documented: a "spend
  this mana only to cast a creature spell" land scores top, and a conditionally-tapped land
  scores as sometimes-untapped on a condition mono-black cannot meet. Only the
  not-a-playable-land half was in scope here.
- `dashboard.html` snapshot is one `make dashboard` behind (BS4-42).
- The six operator visual checks from Batch 5, incl. the gallery's never-rendered light
  palette.
- Still owner-paced: `matches.csv` is empty, so 34 provisional tier letters rest on
  internal consistency alone.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-37: its "LIVE RESIDUAL, at the TOP of the list" paragraph describes the
  back-face-land bug in the present tense — that half is now FIXED, and the two scoring
  misses are what remain. This is the most misleading stale text in the file right now.
- CLAUDE.md G-63: the TYPE-column member gains `suggest_lands`, and it is worth recording
  that `wishlist._is_land` was fixed in BS2-11 while its sibling recommender was not — the
  same one-place-not-another shape.
- CLAUDE.md INV-01 / INV-03 wording: quantity is ASCII-digits-or-blank, and the gallery leg
  now checks content rather than existence.
- CLAUDE.md G-17 could note that the wishlist comment contradicting it is fixed.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
