---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS8-08 `verify_ingest` red by construction on the tracker-CSV route; false "NO card-mana row" for a front-named Room; Arena's `Name` line reported as never ingested
- BS8-09 `/add-deck` never ran `build_mana` → INV-02 red at its own commit tail
- BS8-19 Editor deck save gated on parse fidelity only (unknown `(SET)` / smuggled line saved green)
- BS8-18 Editor CSV save had no staleness token (stale tab regressed a CLI-raised quantity)
- BS8-34 Library accepted a printing whose set code exists nowhere (no INV-04 twin)
- BS8-35 `import_arena` same-run phantom row (printed line + name-only line in one paste)
- BS8-42 Three app write paths flipped files to 0600
- BS8-07 `PYTEST_NO_SKIPS` blind to a module-level `importorskip` (collection report)
Files modified: scripts/verify_ingest.py, scripts/import_arena.py, scripts/app.py, templates/collection.html, scripts/check_all.py, tests/conftest.py, tests/test_conftest_no_skips.py (new), tests/test_app_editor.py, tests/test_verify_ingest.py, tests/test_ingest.py, tests/test_check_all.py, .claude/commands/add-deck.md, CLAUDE.md, docs/gotchas.md

CHANGES:
BS8-08 | verify_ingest.py | `library_index` no longer aliases `names` (the qty dict stays aliased), so `_library_key`'s front→stored-full step is reachable and the INV-02 half looks up the stored spelling; `_blocking_warning` separates parse/unreadable failures from informational notes (CSV banner, SUMMED) — only the former block ✓; notes print as NOTE:, failures as WARN:.
BS8-08 | import_arena.py `parse` | lines inside the `About` section are skipped (the `Name <deck>` line every modern export carries).
BS8-35 | import_arena.py `merge` | `by_front` is updated when a row is appended, so a name-only line later in the same paste tops up instead of appending a blank-set phantom.
BS8-09 | .claude/commands/add-deck.md | step 3 runs `make refresh` (G-13's one definition) instead of `enrich.py` alone; the separate gallery step is folded in.
BS8-19 | app.py `_write_deck` | runs `deckmod.printing_problems` (bad set → 400) and `deckmod.malformed_deck_lines` (smuggled line → 400) before promote; unverified collector numbers returned as `warnings`.
BS8-18 | app.py `save`, `render_page`, `_lib_token`; templates/collection.html | `/api/save` accepts `{"edits", "lib_token"}` (bare list still works), refuses a stale token with 409, returns the new token; the page carries the token on the `#data` element and updates it after a save.
BS8-42 | app.py `_safe_write`, `_write_deck`, add rollback | `shutil.copymode` before `os.replace` (0644 for a new file).
BS8-34 | check_all.py `check_library_printings` (INV-01b) | HARD: a library Set Code no pool printing carries; exact collector pairing deliberately not checked (the pool keys one printing per card).
BS8-07 | tests/conftest.py | `pytest_make_collect_report` hookwrapper converts a collection-time skip into a collection error under PYTEST_NO_SKIPS (a plain `pytest_collectreport` runs after the terminal count — measured); `tests/test_conftest_no_skips.py` pins it with a subprocess.
Docs | CLAUDE.md G-15 (editor gate = INV-04 + token), C-07 (both stages), INV-01b added, K-09 figure; docs/gotchas.md G-13 (add-deck) and G-15 (editor) long forms.

TEST RESULTS: passed — full suite green with PYTEST_NO_SKIPS=1 (the only failures in the full run were the two docs-cap tests fixed afterwards and re-run green); `check_all` all invariants hold incl. the new INV-01b, only the G-75 soft warning. Mid-batch: the first collection hook (`pytest_collectreport`) did nothing — the terminal reporter had already counted the skip — replaced by the hookwrapper and verified on a synthetic module; the first `_library_key` draft reordered the steps instead of removing the alias at its source, which would have shadowed a real front-named card ("Life" vs "Life // Death") — fixed at the source and pinned.
REGRESSION RISKS:
- A pasted line inside an `About` block is now silently ignored; Arena never puts card lines there.
- `/api/save`'s body shape changed (dict) — the old bare-list form is still accepted; a cached pre-token page saves without a token (same escape hatch the deck save has).
- The deck editor now refuses a `(SET)` that exists nowhere — a deliberately unreleased/custom set code cannot be saved from the editor (the CLI still can, and INV-04 would flag it anyway).
- INV-01b is HARD: a future pool rebuild that drops a set the library holds (a custom `--query`) would fail `check_all` until the pool is rebuilt with `--all`; the message says so.
- `verify_ingest` now prints NOTE: for informational lines — any script grepping for `WARN:` on the CSV banner will no longer match.
INVARIANTS AT RISK: None; INV-01b added and verified clean on the live library.
NET SCORE: 6 − 0 = 6
(BS8-08 YES (every tracker-CSV verify), BS8-09 YES (every add-deck with a new card), BS8-19 YES, BS8-18 YES, BS8-42 YES, BS8-07 YES (every CI run's claimed property); BS8-34/35 latent — counted 6. No new failure mode found.)

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: N/A for the editor (local tool); CI picks up the conftest change on the next push.

FOLLOW-ON ITEMS:
- Write-time twin of INV-01b: `import_arena`/`reconcile_crafts` could refuse a set code the pool has never seen (today the gate catches it after the write).
- `/api/remove` and `/api/add` have no library token (remove has the printing-key 409, which covers most cases).
- `check_docs.figure_drift` is still invoked by `main()` only (BS8-22, batch 7) — it caught the K-09 figure here because I ran it by hand.
- `test_writer_mutations.py` pins copymode on `lib.atomic_write` only; the three app paths are now pinned by `test_the_file_keeps_its_mode_on_save` for the deck save alone.

DOCUMENTATION UPDATES NEEDED:
- README: `/api/save` body shape and the collection page's token; `verify_ingest` NOTE vs WARN; INV-01b in the invariants prose if README lists them.
- docs/cycle-config.md C-01: INV-01b in the gate list; C-07: `test_conftest_no_skips.py`.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
