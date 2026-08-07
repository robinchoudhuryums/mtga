---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (Batch G — refresh, resilience, CLI polish: the scan's Low tail):
- BS2-23 | `make refresh` silently no-op'd the pool re-tag K-10 mandates after a tag-pattern edit — the freshness reuse skipped it for up to a week while step 2/6 announced itself as run
- scryfall | `_TRANSIENT` missed two real body-read failures (`http.client.IncompleteRead`, `ssl.SSLError` — the latter subclasses OSError, not ConnectionError), so they escaped as tracebacks past the clean-abort contract
- sheets_sync | `pull` promoted its own 0600 mkstemp file, re-introducing the 644→600 regression `atomic_write` documents fixing
- `--out` guards | the UNGUARDED MIRROR of F-02: `build_pool.py --out card-library.csv` (and build_mana / parse_matches) would overwrite the inventory with a derived header, and the shrink guard reads 15.9k-over-2k as GROWTH
- import_arena | a bad path was a raw traceback; a zero-change re-import rewrote the 614KB library and dropped a `.bak`
- import_collection | the dry-run report — the ONLY review surface before an authoritative rewrite — truncated every section at 20, including "Set to 0", with no way to see the rest
- deck.py CLI seams | `cuts --limit 0` capped the oracle block at 12 while the table printed all and the header claimed 12; `quality --at` and `tier --audit-rationale` silently discarded their sibling flags; `history --since 2026-8-1` lexicographically matched nothing while the same string parsed fine in the delta half; `verify` merged a multi-deck paste into one list; `consistency --target 0` meant 0.90 and `--target 90` was accepted
- recommendations | `append_recommendation` rewrote the whole ledger with `backup=False` (a Data-subsystem file, not a scratch temp) and its caller caught only OSError, so a corrupt ledger tracebacked AFTER the deck write — against G-56's "recording never blocks a swap"
- name joins | `screen` / `redundancy` / `similar` still used exact-name sets (the last G-63 stragglers; `similar`'s is the "▸ Most shared CARDS" figure G-47 says to trust over the cosine)
- card.py / query.py | legality was a substring test (`standardbrawl` contains `standard`); `--csv` on a derived path silently emitted the library's 8 columns
- models | `role_coverage_flags` read the merged type line (back-face Creature dropped from the uncertainty channel); `pip_depth_warning` hardcoded N=60 in three places while its stated twin `consistency` reads the real total
- G-56 | `tests/test_recommendations.py`'s "structurally forbids" was one call level deep — it never inspected `cut_keep_score`, the delegate BOTH cut rankings read

Files modified: scripts/deck.py, scripts/lib.py, scripts/scryfall.py, scripts/sheets_sync.py,
scripts/build_pool.py, scripts/build_mana.py, scripts/parse_matches.py, scripts/import_arena.py,
scripts/import_collection.py, scripts/card.py, scripts/query.py,
tests/test_build_pool.py, tests/test_recommendations.py

CHANGES:
BS2-23 | build_pool.py, tests | the build stamp gains a THIRD line: `tagger_fingerprint()`, a
content hash of tag_synergies.py. A mismatch defeats the freshness reuse and says why. Content,
NOT mtime — a fresh clone stamps every file at checkout time in arbitrary order, so an mtime
comparison would force a ~5-minute rebuild after every clone; this repo already learned
content-not-mtime at F-04. A pre-BS2-23 two-line stamp reads as None = "cannot tell", which never
forces a rebuild. 2 new tests (three-line stamp, fingerprint stability).
scryfall | `_TRANSIENT` += IncompleteRead, ssl.SSLError; verified by issubclass (both were False).
sheets_sync | `shutil.copymode(target, tmp)` before the promote, else 0644 for a new file.
--out guards | csv_schema_error(args.out, <own header>) at the TOP of main() in build_pool and
build_mana, and inside write_matches — refusing BEFORE any Scryfall traffic, the way enrich.py does
(tests/test_enrich.py pins that ordering for F-02 itself). Verified end to end: both refuse
instantly and leave the target byte-identical. ALSO: csv_schema_error's message was worded only for
F-02's original direction and read backwards for the mirror — it called card-library.csv "not the
card library" and advised rebuilding it with a derived builder. Now direction-neutral, naming the
tool that OWNS each file. No test pinned the text.
import_arena | try/except OSError on the read (matching its three siblings); a zero-change import
prints "nothing to change" and skips the write entirely.
import_collection | `--full` lists every row; the default cap now says "(--full to list them)".
deck.py | cuts: `text_n` uses the same expression as the table, so `--limit 0` prints all 30 with
text and says 30. quality/tier: the early-return branches now NAME the flags they cannot combine
with instead of dropping them. history: `--since` requires zero-padded ISO and says so. verify:
warns when the paste holds >1 `Deck` block and points at `sync`. consistency: `--target` must be a
fraction in (0,1). recommendations: `atomic_write(path, _w)` (backup ON) and the caller catches
Exception. screen/redundancy: `_ms_key` in_deck. similar: keyed intersection with a key→display map,
so the count is right AND the printed names keep the deck's own spelling.
card.py/query.py | legality splits on ";" into a set; `--csv` refuses a non-library path.
models | role_coverage_flags uses `_primary_type`; pip_depth_warning takes `total=` (14 sources /
3 pips / turn 5 = 50.2% at 60 vs 18.2% at 100 — the flag was suppressed exactly where colour depth
is hardest), with cmd_suggest_homes passing the real deck size.
G-56 | the forbid-scan covers 7 functions (added cut_keep_score and _weakest_cut), verified
non-vacuous by re-running the scan directly.

TEST RESULTS: 1031 passed (1029 + 2 new), 0 failed. check_all "All invariants hold. ✓" with zero
soft warnings; check_docs / check_commands / check_patterns / check_dfc green standalone.
TWO SELF-INFLICTED BREAKS, both caught by the gates and fixed before commit: (1) a comment
insertion lost its indentation and made card.py unparseable — check_all's AST scans reported it as
three hard failures, which is the gate doing exactly its job; (2) read_stamp's 2→3-tuple broke four
test doubles in tests/test_build_pool.py that I should have found by scanning for them BEFORE the
edit, per this command's own rule — updated as part of the fix, not reactively.
Scenario 2 walked on the modified surfaces (cuts --limit 0, consistency --target both bad shapes,
history --since, tier --audit-rationale --to, quality --at --json, verify, similar, screen, card.py,
query.py --csv) — PASS. Scenario 1 partially walked (import_arena no-op + bad path, import_collection
--full, the two --out refusals) — PASS. Scenario 3 NOT fully walked: `make refresh` needs Scryfall,
and the BS2-23 path was verified by unit-testing the fingerprint logic instead.

REGRESSION RISKS:
- read_stamp returns a 3-TUPLE; the only caller is in build_pool and the four test doubles are updated.
- The first `make refresh` after this lands WILL rebuild the pool once (the committed stamp has no
  fingerprint → None → no rebuild; but the next build writes one). Cost: one ~5-minute rebuild, once.
- `--target` and `--since` now REJECT inputs they previously accepted-and-misinterpreted (exit 2).
- `query.py --csv` refuses derived paths it used to silently mangle; `card.py`'s legality is stricter
  only in the direction of correctness.
- pip_depth_warning's signature gained an optional `total=`; the one caller passes it, and the
  default preserves the old N=60 behaviour for any other caller.
- `similar`'s shared-card COUNT can now be higher than before (cross-spelled cards finally count) —
  that is the correction; the printed names are unchanged in form.
- append_recommendation now writes a `.bak` per swap. Deliberate: it is a Data subsystem file.

INVARIANTS AT RISK: None. The --out guards strictly PROTECT INV-01/INV-03; nothing else writes a
canonical file differently.

NET SCORE: 12 − 0 = +12
(Counting the grouped items as one each. Most were latent-but-reachable; the ones that fire on
ordinary use are cuts --limit 0, the silently-dropped flags, history --since, and import_arena's
backup litter. No new failure modes — the three stricter inputs all report what they want.)

OPERATOR ACTIONS / DEPLOY:
- The next `make refresh` will rebuild the pool once as the fingerprint is first written | BLOCKS DEPLOY: N
Deploy: commit/push is the deploy.

FOLLOW-ON ITEMS:
- Batch H (strategic) is all that remains of the priority report: log ten real matches, decide the
  twice-replicated creature-cut finding, the writer mutation-test layer, the G-63 AST scan, deck 49's
  Route A, the ten unindexed keywords, and the Sheets round-trip.
- BS2-07's header-consumer sweep is STILL the standing leftover — Batch A fixed the swap-side protect
  guard only, and `rank_cut_candidates` / `_castability` / `_weakest_cut` still compare raw names
  against `#: protect:` / `#: uncastable-ok:` while the G-68 gate joins on `_ms_key`. Zero live
  instances measured, but it is the one member of the G-63 class this session did not close.

DOCUMENTATION UPDATES NEEDED:
- G-56's CLAUDE.md bullet says the forbid-test is "one call level deep … does NOT cover
  cut_keep_score" — that residual is now CLOSED and the sentence should be re-tightened.
- G-18's freshness-reuse rule should mention the tag-fingerprint escape (BS2-23), and K-10's
  "skip the pool rebuild and unowned craft candidates rank on stale tags" is now enforced, not advisory.
- README's build_pool section could note the third stamp line.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
