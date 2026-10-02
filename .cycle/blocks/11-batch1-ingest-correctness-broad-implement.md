---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS11-19 import_collection: a printed export row for an unheld printing of a card held in 2+ printings was filed "ambiguous" and its copies dropped
- BS11-20 import_collection --library still wrote the REPO's collection-stamp.json and card-mana.csv
- BS11-22 import_arena LINE_RE matched a tab, so a quantity-first TSV parsed as junk Arena lines (verify_ingest never tried the CSV/TSV reading)
- BS11-21 lib.csv_schema_error refused a builder rebuilding an OLDER prefix of its own schema
- BS11-23 import_arena.merge over-counted when a set-less line preceded the printed line
- BS11-24 reconcile_crafts took max() across Deck/Sideboard and reported "Sideboard" as unparseable
- BS11-25 scryfall._TRANSIENT missed UnicodeDecodeError and http.client.HTTPException
- BS11-26 build_pool fingerprint missed lib.REMINDER_RE / POOL_FORMATS; a blank fingerprint read as "unchanged"
- BS11-27 INV-01 missed a front-name / full-name duplicate of one printing
- BS11-28 import_arena imported basic lands unless --skip-basics was passed
- BS11-30 collection_stamp_note crashed on a non-object stamp; a future date read fresh forever
- BS11-29 enrich.py / tag_synergies.py rewrote the library and made a .bak on a 0-change run
Files modified: scripts/import_collection.py, scripts/import_arena.py, scripts/reconcile_crafts.py, scripts/lib.py, scripts/scryfall.py, scripts/build_pool.py, scripts/validate.py, scripts/enrich.py, scripts/tag_synergies.py, README.md, tests/test_ingest.py, tests/test_verify_ingest.py, tests/test_lib.py, tests/test_reconcile_crafts.py, tests/test_scryfall.py, tests/test_build_pool.py, tests/test_validate.py, tests/test_enrich.py

CHANGES:
BS11-19 | import_collection.py | plan(): a printed entry (set or collector present) whose exact printing is absent, for a card held in 2+ printings, folds onto an existing printing (same-set row preferred, else the first) like the single-printing branch; only name-only rows stay AMBIGUOUS. +2 tests.
BS11-20 | import_collection.py | new _sibling_paths(library): mana rows and the freshness stamp are written beside --library; _ensure_mana_rows takes a path. Default library = repo files (unchanged). +2 tests.
BS11-22 | import_arena.py | LINE_RE name group excludes tabs (and the set group too); a TSV row no longer matches, so verify_ingest falls through to parse_export. +1 test.
BS11-21 | lib.py | csv_schema_error returns None when the existing header is a PREFIX of the one being written and holds at least half its columns (library vs pool, a 1-column stub, still refused). +1 test.
BS11-23 | import_arena.py | merge() stable-sorts printed lines before set-less ones, so line order cannot change the result. +1 test.
BS11-24 | reconcile_crafts.py | quantities come from import_arena.parse (section-aware: Deck+Sideboard sum, same-section repeat max, Companion folded); section headers and the About block are not reported as unparseable. +1 test.
BS11-25 | scryfall.py | _TRANSIENT gains UnicodeDecodeError and http.client.HTTPException. +1 test.
BS11-26 | build_pool.py | fingerprint also hashes lib.REMINDER_RE.pattern and POOL_FORMATS; read_stamp treats a blank third line as unknown; an uncomputable current fingerprint counts as changed. +3 tests.
BS11-27 | validate.py | duplicate-printing key uses the FRONT face. +1 test.
BS11-28 | import_arena.py, README.md | basics skipped by default; --include-basics opts in; --skip-basics kept as an accepted no-op. +3 tests.
BS11-30 | lib.py | collection_stamp_note treats a non-object stamp and a future date as "never reconciled". +2 tests.
BS11-29 | enrich.py, tag_synergies.py | a 0-change run prints "left untouched" and writes nothing. +2 tests.

TEST RESULTS: passed — `python3 scripts/check_all.py` all invariants hold (soft warnings unchanged from before the batch); full pytest suite exit 0. Regression scenarios 1 and 3 (ingest/refresh) need network + a real export and were not walked; their code paths are covered by the new unit tests.
REGRESSION RISKS:
- BS11-26 changes the fingerprint VALUE, so the next `make refresh` rebuilds the pool once (~4 min). Expected and one-time.
- BS11-28 flips import_arena's default: a caller that wanted basics now needs --include-basics. No skill or script relies on importing basics (all pass --skip-basics).
- BS11-19 records the folded copies on an existing printing rather than the exported one — the same documented trade-off the single-printing branch already makes; the TOTAL is now right.
- BS11-21 now lets a builder overwrite an older prefix of its own schema; a different schema is still refused.
INVARIANTS AT RISK: None — INV-01 is stricter (BS11-27; live library still clean, 0 errors), INV-02/INV-01b paths unchanged in default use.
NET SCORE: 1 − 0 = 1 (BS11-29 fired this session — the 2026-10-02 refresh's "Tagged 0 row(s). Wrote card-library.csv" made a byte-identical .bak; the other eleven would not have fired this month: import_collection has never been run, and no TSV / Sideboard export / reminder-regex edit / bad stamp occurred)

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: N/A — the Deploy Command covers the dashboard only (pages.yml); no presentation file changed.

FOLLOW-ON ITEMS:
- build_pool.tagger_fingerprint's docstring still describes the card-mana.csv noise-floor dependency G-18 says is gone (BS11-63, Batch 9).
- The release-day Cloudflare cache trap on the canonical `game:arena date<=now` URL (recorded in NEXT-SESSION 2026-10-02) has no tooling fix; a cache-busting parameter or a post-fetch "newest Released vs today" check in build_pool would close it.
- With exactly ONE library printing, import_collection still folds a new printing onto it rather than adding it (documented README behaviour; unchanged).

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md "Basic lands are not in the collection … imports skip them with `--skip-basics`" and the Deck-dump bullet: skipping is now the default (`--include-basics` opts in).
- README's import_collection section: a printed row for a printing the library lacks now folds onto an existing printing even when several are held.
- CLAUDE.md G-14: UnicodeDecodeError / HTTPException joined `_TRANSIENT`; G-18: the fingerprint also covers lib.REMINDER_RE and POOL_FORMATS, and a blank fingerprint is unknown.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
