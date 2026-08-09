---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
BATCH 1 — live wrong output
- BS4-07 | `#: archetype:` figures were never audited, against G-27's documented scope
- BS4-13 | `/decks` and `check_all`'s info summary computed buildability per LINE, not per summed name
- BS4-14 | Flex panel showed "not owned" for owned DFCs (bypassed `ownedOf`)
- BS4-08 | `wishlist --audit-targets` reported "clean" having checked nothing when deck.py failed to import
- BS4-41 | Dashboard died to a blank page on corrupt sessionStorage, and preferred stale synced data over a fresher local rebuild
BATCH 2 — ingest edges & silent degradation
- BS4-15 | No intra-paste Match ID dedupe — permanently double-counted a match
- BS4-39 | `verify_ingest` swallowed the column diagnostic on the path `import_collection` routes you to
- BS4-17 | Non-numeric `Retry-After` escaped the `ScryfallUnavailable` contract
- BS4-16 | `sheets_sync.push` cleared the remote tab before uploading (no staging)
- BS4-22 | `wishlist --add` tracebacked on a missing file; lost a whole batch if deck.py was broken
- BS4-24 | `parse_matches` report dropped blank-Result rows into an uncounted bucket

Files modified:
- scripts/deck.py
- scripts/app.py
- scripts/check_all.py
- scripts/check_dfc.py
- scripts/check_patterns.py
- scripts/build_dashboard.py
- scripts/wishlist.py
- scripts/parse_matches.py
- scripts/verify_ingest.py
- scripts/scryfall.py
- scripts/sheets_sync.py
- templates/deck.html
- decks/26-iron-forge/26a-virulent.txt
- tests/test_deck.py, tests/test_parse_matches.py, tests/test_scryfall.py,
  tests/test_sheets_sync.py, tests/test_verify_ingest.py, tests/test_wishlist.py

CHANGES:

BS4-07 | scripts/deck.py, decks/26-iron-forge/26a-virulent.txt | The figure loop in
`rationale_staleness` now sweeps `("tier", "archetype")` — the same two headers the CARD
scan has always swept. G-27 documented both, so the rule was true of half the function.
The first roster sweep found 3 hits, of which only ONE was genuine, so the fix needed the
archetype prose to get the same suppression care the tier prose has. Two narrow,
clause-scoped suppressions added: (a) a figure whose clause names ANOTHER ROSTER DECK by
NAME (deck 44a quotes deck 1's "card advantage 0" in its distinctness clause and writes
the name rather than "deck 1", which the id-based `_OTHER_DECK_RE` could not see); (b) a
figure whose subject is the card POPULATION, via `_POPULATION_SUBJECT_RE` (deck 49 argues
"Standard's Dragons average MV 5.30" — true about the format, flagged against the deck's
own 4.03 curve). Possessive form only, so "fine in Standard, avg MV 2.4" still audits.
The deck-name exclusion had to allow names that are part of THIS deck's own name: the
variant convention makes 26a "Iron Forge — Virulent", so its PARENT's name is a substring
of its own, and an exact-match exclusion suppressed the one genuinely stale figure the
whole fix exists to catch. Final state: 1 genuine hit roster-wide, corrected in deck 26a
(avg MV 3.05 → 2.97; its "15 early drops" was re-measured and is still right).

BS4-13 | scripts/deck.py, scripts/app.py, scripts/check_all.py | New `deck_requirements()`
(distinct cards, first-seen order, copies SUMMED across duplicate lines) and
`deck_build_gap()` (the missing/short pair). `cmd_check` now calls the first — its
behaviour is unchanged, the aggregation was extracted, not altered — and `app.py`'s
`_decks_overview` and `check_all`'s info summary call the second instead of carrying
their own per-line loops. `unique` on /decks counted LINES for the same reason and now
counts distinct cards. Verified: /decks agrees with `deck.py check` on all 99 decks.

BS4-14 | templates/deck.html, scripts/check_dfc.py | `renderFlex` routes through
`ownedOf` (full name, then DFC front) instead of a raw `key in OWNED`. The gate could
only see the helper, not its callers — its own docstring stated that residual and
`renderFlex` was already violating it — so `_payload_flags` now scans every USE of the
serialized index and fails any lookup outside `ownedOf` (JS comments excluded, or the
comment explaining the fix would trip it). Mutation-tested: reverting `renderFlex`
makes the gate fire.

BS4-08 | scripts/wishlist.py | `_audit_target_issues` raises a new
`TargetAuditUnavailable` instead of `except Exception: pass`. Every check below was gated
on structures the swallowed load fills, so the function returned `[]` — and
`cmd_audit_targets` printed "Wishlist targets are clean" having checked nothing, while
`check_all`'s soft sweep saw an empty list rather than a skip. `cmd_audit_targets` now
exits 1 with a SKIP message; `check_all` needed no change (its existing handler produces
the " skipped (" sentinel its `--quiet` path already counts as a downed radar).

BS4-41 | scripts/build_dashboard.py | The loader takes the embedded snapshot as a FLOOR:
a corrupt `mtga-live` is caught, cleared and logged instead of throwing at the top of the
script and leaving dead chrome for the tab session; and the stored payload is preferred
only when its `generated` stamp is genuinely NEWER, so a locally rebuilt dashboard no
longer shows older synced data. Behaviour verified by executing the extracted loader
under node across five cases (no live / corrupt / older / newer / undated).

BS4-15 | scripts/parse_matches.py | Dedupe extracted to `fresh_rows(rows, existing)` and
extended to dedupe WITHIN the paste, not just against the CSV. Two copies of one
`finalMatchResult` in one paste — what concatenating overlapping log extracts produces —
were both written, double-counting that match in `--report` permanently, while the
docstring and the truncation warning both told the user re-pasting was safe. Id-less rows
stay exempt: "" is not an identity.

BS4-24 | scripts/parse_matches.py | `report()` counts only W/L/D (case/whitespace
tolerant) and reports anything else in a named block. `b[r.get("Result","L")]` only
defaulted when the KEY was absent, so `Result=""` incremented a `b[""]` bucket printed in
no column and excluded from n=W+L — header count and per-deck totals silently disagreed.

BS4-39 | scripts/verify_ingest.py | The CSV-fallback `except Exception` keeps the
diagnostic as a warning instead of discarding it. `import_collection.parse_export` raises
a ValueError naming the columns it saw and the `--map` remedy; swallowing it sent the
operator to the generic "Expected Arena export lines" — the wrong FORMAT — on the exact
path `import_collection`'s post-apply message recommends.

BS4-17 | scripts/scryfall.py | New `_retry_after_seconds()`. RFC 7231 allows Retry-After
as an HTTP-DATE as well as delay-seconds, and the bare `float()` raised ValueError INSIDE
the HTTPError handler, escaping both `_TRANSIENT` and `ScryfallUnavailable` and breaking
the module's premise that every transport failure degrades to one exception type. The
date form is now parsed and capped at 60s so a far-future date can't park a rebuild.

BS4-16 | scripts/sheets_sync.py | Push writes over the tab and then trims the leftover
tail, instead of `clear()` then a separate `update()`. A failure between the two left the
Sheet EMPTY — and the Sheet is the one REMOTE copy the shrink guard above it exists to
protect. A failed trim warns but does not report the push as failed (the data is already
correct; reporting failure would invite a re-push of a correct Sheet).

BS4-22 | scripts/wishlist.py | `cmd_add` gives a clean error on an unreadable file (and
closes the handle), and Power seeding goes through `_try_seed_power`, which warns ONCE
and returns None. `_seed_power` does `import deck`, and it ran in a bare loop after the
Scryfall fetches and before `write_wishlist`, so a broken deck.py discarded an entire
enriched batch over a cosmetic estimate. A blank Power is a state the tool already models.

TEST RESULTS: PASSED.
- `python3 scripts/check_all.py` — "All invariants hold. ✓", exit 0, ZERO soft warnings.
- `python3 -m pytest` — 1,146 tests, all passing, exit 0 (was 1,105; +41 added here).
- CLI smoke (CI shape, traceback detection): 35 scripts and 68 `deck.py` subcommand helps
  render clean.
- ONE test failure occurred during the run and was CAUSED BY THIS SESSION:
  `test_verify_ingest.py::test_an_unparseable_line_is_a_warning_not_a_silent_drop`
  asserted `len(warns) == 1`, a count that encoded the pre-BS4-39 warning set. The test's
  INTENT (an unparseable line must not be swallowed) still holds and now asserts that
  directly; a second test pins the new diagnostic including the `--map` remedy. Fixed, not
  worked around.
- Regression Scenario 2 (Analyze a deck) walked on deck 26a — all 12 subcommands clean,
  `tier --audit-rationale` reports the rationale current; roster-wide `audit`/`rotation`/
  `brawl` clean.
- Regression Scenario 1 (Ingest) — `verify_ingest` walked; reconcile/import dry runs clean.
- Regression Scenario 4 (Editor) — `_decks_overview` cross-checked against
  `deck.deck_build_gap` for all 99 decks: NO disagreements.

REGRESSION RISKS:
- **BS4-07 is the one with real re-grade potential, and it was measured.** Widening the
  figure scan can only ADD reports; the two suppressions can only REMOVE them, so the risk
  is a false negative. Roster sweep before suppressions: 3 hits (1 genuine, 2 false).
  After: exactly the 1 genuine hit, corrected. A behavioural anchor test asserts the roster
  figure sweep stays clean, so a future stale figure fails a test rather than going quiet.
- **BS4-13 changed no numbers on the canonical surface.** `cmd_check`'s aggregation was
  extracted verbatim; the two drifted surfaces now match it. No deck on the roster
  currently lists a card on two lines, so no displayed count changed today — the fix is
  against the case, not a current symptom.
- **BS4-16 changes the ORDER of remote API calls.** `delete_rows` is a new gspread call
  this code did not previously make; if a worksheet object lacks it the trim warns and the
  push still reports success (pinned by a test). The shrink guard still runs first, so the
  destructive-overwrite floor is unchanged.
- **BS4-08 changes a return contract to an exception.** Both callers were updated in the
  same commit and there are only two (`cmd_audit_targets`, `check_all`). `check_all`
  needed no edit because its existing handler already produces the downed-radar sentinel.
- **BS4-24 changes report() output shape** (a new warning block). Nothing parses that
  output; `matches.csv` is empty today, so no live record is affected.
- **BS4-41 is template-only** — no change to `build_dashboard`'s `#data` pipeline, which
  CLAUDE.md's Deploy Command marks as the source of truth a restyle must not touch.
- Old behaviour was not correct in any of these cases; each fix makes a surface agree with
  the thing it summarises, or makes a swallowed failure visible.

INVARIANTS AT RISK: None.
- INV-01…INV-04 — untouched; `check_all` green with zero soft warnings.
- G-63 (front-face joins) — BS4-14 is a net closure, and its gate now covers every
  consumer rather than the helper alone.
- G-25/G-60 (report-only axes stay out of `tier_band`) — no scoring term added; BS4-07 is
  report-only by construction.
- G-26 (keep rationale-audit cue lists NARROW) — the two new suppressions are the reason
  this finding took the longest: both are clause-scoped and possessive/name-specific, and
  the roster sweep is the check, exactly as that rule prescribes.
- check_patterns' registry — `_POPULATION_SUBJECT_RE` is registered in `_EXCLUDED` with a
  reason and unit tests, per that gate's contract.

NET SCORE: 11 production fixes − 0 new failure modes = 11
Per-finding: (a) would it have fired this month? (b) new failure mode introduced?
- BS4-07: (a) YES — live on deck 26a. (b) NO. The suppressions can under-report; that risk
  is measured (roster sweep) and anchored by a test.
- BS4-13: (a) NO — no roster deck currently splits a card across lines. (b) NO.
- BS4-14: (a) YES — any flex line naming a DFC by full name. (b) NO.
- BS4-08: (a) NO — deck.py imports fine today. (b) NO. It can now exit 1 where it silently
  exited 0, which is the point.
- BS4-41: (a) YES for the freshness half (any tab that has ever synced). (b) NO.
- BS4-15: (a) Conditional — needs a concatenated paste; `matches.csv` is empty. (b) NO.
- BS4-24: (a) NO — no records exist yet. (b) NO.
- BS4-39: (a) YES if a tracker export is verified. (b) NO.
- BS4-17: (a) Conditional on a 429 with a date header. (b) NO.
- BS4-16: (a) Conditional on a mid-push failure; the Sheets round-trip is not yet set up.
  (b) NO.
- BS4-22: (a) YES for the missing-file traceback. (b) NO.

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push (no build/release step). The dashboard is
republished by `.github/workflows/pages.yml` on push to `main`. BS4-41 edits
`build_dashboard.py`'s TEMPLATE, so the published page picks the fix up on that rebuild;
the committed `dashboard.html` snapshot is regenerated by `make dashboard` / `make
postedit` and was NOT rebuilt here (it is a convenience snapshot, and rebuilding it is a
~2 min step unrelated to these findings).

FOLLOW-ON ITEMS:
- `dashboard.html` (the committed snapshot) still carries the pre-BS4-41 loader. Run
  `make dashboard` when convenient; the deployed Pages copy is rebuilt from source.
- `deck_requirements` keys on `n.lower()`, matching `cmd_check`'s long-standing behaviour.
  Two lines spelling the SAME DFC differently would still be two entries — a G-63 sibling,
  deliberately not changed here because it would alter `cmd_check`'s canonical output.
- `recommendation_row`'s `Cut Rank` raw-name join (noted last session, still open).
- `BASICS` is defined in four modules.
- Remaining scan findings: Batch 3 (gate credibility), Batch 4 (structural/latent DFC),
  Batch 5 (interface polish), plus the six operator visual checks.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-27: the audit now genuinely covers `#: archetype:` figures — the rule text
  can drop the implicit "cards only" reading, and should record the two suppressions
  (other-deck-by-NAME, population subject) as the live residual shape.
- CLAUDE.md G-26: add the BS4-07 measurement — widening a scan without the matching
  suppressions produced 2 false positives in 3 hits, and the roster sweep is what caught it.
- CLAUDE.md / docs: a new gotcha candidate — "buildability is per NAME, not per LINE", now
  with one definition (`deck_requirements` / `deck_build_gap`) after three implementations.
- G-63 / docs/gotchas.md: `check_dfc._payload_flags` now scans every consumer, not just the
  helper; the stated residual in its docstring is closed.
- README: `wishlist.py --audit-targets` can now exit non-zero (audit skipped ≠ clean).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
