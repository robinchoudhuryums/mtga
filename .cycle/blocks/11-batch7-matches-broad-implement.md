---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS11-32 — `void=no` restored a result GUESSED from the game score (and a void on a live row was silently accepted)
- BS11-33 — a zero-padded deck id (`06`) was accepted by `--add` / `--deck` / `wishlist --add --target` and then STORED padded
- BS11-35 — the `--annotate` loss prompt said a blank value records nothing; the documented, tested contract is that it CLEARS
- BS11-36 — voided matches leaked into `report` (0-0-0 rows), the loss-reason tally, and `feedback`'s swap_outcomes game count
- BS11-37 — `--sync-names` could not see an Arena rename that changed only a trailing "(...)"
- BS11-38 — `_adopted_name` stripped a parent that prefixed a WORD ("Dino" + "Dinosaur Party" → "Dino — saur Party")
Files modified: scripts/parse_matches.py, scripts/deck.py, scripts/wishlist.py, tests/test_parse_matches.py, tests/test_wishlist.py

CHANGES:
BS11-32 | scripts/parse_matches.py | `_void_fields` now records the prior result in the note (`void (was L): <why>`, `_VOID_NOTE_RE`), restores exactly that result, keeps the ORIGINAL result on a re-void, and returns None (refuse) for `void=no` on a row that is not voided or for a legacy `void: ` note whose game score is tied. `annotate()` warns on a refusal and still applies the row's other fields. The one live voided row (deck 17, legacy `void: stepped-away`) still restores from its game score, as before.
BS11-33 | scripts/parse_matches.py, scripts/wishlist.py | `parse_manual` and `main()`'s `--deck` map the accepted id to its canonical roster spelling (`_norm_id` → roster id) before writing; `wishlist.cmd_add` rewrites `--target` tokens to canonical ids joined with "; ". Updated the BS8-17 test that pinned the padded STORAGE (it encoded the bug) — acceptance is still pinned.
BS11-35 | scripts/parse_matches.py | `_print_loss_prompt` wording now says a blank value CLEARS the field (already empty on these new rows). Behaviour kept: log-matches.md, README and `test_an_empty_value_clears_the_field` all define clearing; the finding's suggested behaviour change would have contradicted them.
BS11-36 | scripts/parse_matches.py, scripts/deck.py | `report()` skips VOID before creating the per-deck bucket; the loss-reason tally counts a reason only on Result == "L"; `deck.swap_outcomes` excludes VOID (lazy import of `parse_matches.VOID`, "X" fallback), so `feedback` and `audit`'s Pld agree.
BS11-37 | scripts/parse_matches.py | new `_rename_key(name, current)` strips only the CURRENT name's own gloss before keying; `deck_name_plan` compares with it, so an Arena-side "(old)"→"(new)" is a rename while the repo's premise gloss still is not.
BS11-38 | scripts/parse_matches.py | `_adopted_name` treats a parent prefix as repeated only when the cut falls on a word boundary (alnum on both sides of the cut → not a repeat).

TEST RESULTS: passed — full suite `python3 -m pytest -q tests/` green (one pre-existing test, `test_a_zero_padded_id_is_accepted`, asserted the padded storage BS11-33 removes; split into an acceptance assertion + a new canonical-storage test). `python3 scripts/check_all.py --quiet`: integrity OK, 4 soft (unchanged). New tests: void round-trip with a blank game score, refusal on a live row, refusal of a tied legacy void, canonical storage (parse_matches + wishlist), voided-only deck has no report row, voided loss not tallied, swap_outcomes excludes VOID, Arena parenthetical rename seen, repo gloss still ignored, word-boundary parent, real repeated parents still stripped (dash and colon).
REGRESSION RISKS: (1) The void note format changed from `void: <why>` to `void (was X): <why>`; `_VOID_NOTE_RE` accepts both, so legacy rows still restore (from the game score, as before) — any external reader grepping `^void: ` would miss new rows (none in the repo; `report` prints the note verbatim). (2) A padded id is now rewritten on write — callers comparing the stored value against the user's raw typing would differ; none do (every reader normalizes or uses roster ids). (3) `_rename_key` is used only by `deck_name_plan`; the rename WARNINGS path still uses `_name_key` (unchanged, by scope).
INVARIANTS AT RISK: None — no canonical CSV schema changed; matches.csv/card-wishlist.csv are written through their existing writers.
NET SCORE: 1 − 0 = 1  (production this month: BS11-36 — deck 17's voided match made `feedback` count 3 games against `audit`'s 2. Latent, not fired: BS11-32 (only void on record is a legacy note), BS11-33 (0 padded ids in matches.csv or wishlist Targets), BS11-35 (wording), BS11-37/38 (no such names live). No new failure modes: the tied-legacy refusal is a deliberate "do not guess", reported with a WARN.)

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: N/A — no modified subsystem has a Deploy Command (Presentation's Pages build is untouched).

FOLLOW-ON ITEMS:
- The rename-WARNING path (`TestRenameWarningsSeeThroughGlossCaseAndCards` territory) still keys on `_name_key`, which drops any trailing "(...)" — an Arena-only parenthetical change is invisible to the warning as it was to the plan. Out of scope (BS11-37 named the plan).
- Deck 17's legacy void row cannot carry a recorded result retroactively; it restores from the game score, which is fine unless that score is tied.

DOCUMENTATION UPDATES NEEDED:
- G-74 / README `--annotate` section: the void note now reads `void (was <W|L|D>): <why>`; `void=no` restores the RECORDED result and refuses on a live row.
- G-82 (or G-74): a padded deck id is accepted AND stored canonical — by `--add`, `--deck` and `wishlist --add --target`.
- `/log-matches` skill and README: the post-ingest prompt wording ("a blank value clears").
- G-73: `--sync-names` sees an Arena-side parenthetical rename; a parent repeated only as a word prefix is not stripped.
- (Carried from Batch 6, still unsynced: G-08/G-30, G-35/G-87, the 100-card section, README `pool.py --legal`.)
---END BROAD SCAN IMPLEMENTATION SUMMARY---
