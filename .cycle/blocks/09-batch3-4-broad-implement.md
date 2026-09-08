---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
  F2 (Medium) — the dashboard's degradation guard was majority-only; no sub-majority voice
  F5 (Medium) — wishlist's roster loops bypassed `roster_decks()`
  F6 (Medium) — app.py's request guard and three destructive endpoints had zero tests
  F7 (Low)    — the absent-token save bypass, retired

Files modified: scripts/build_dashboard.py, scripts/wishlist.py, scripts/app.py,
  tests/test_app_editor.py, CLAUDE.md (Scenario 19)

CHANGES:

F2 | scripts/build_dashboard.py | A sub-majority `if err_decks:` WARN, mirroring the craft
sibling twenty lines down. The existing threshold (`len(err_decks) * 2 >= ndecks`) is the
DEPLOY gate: below half the build returned 0 and printed NOTHING, so 1–49% of the roster —
up to 57 decks — could publish `[analysis error]` panels to Pages under a green build with
silent output. The craft check has had BOTH halves since BS5-05; the detail-panel check had
only the refusal. Two functions answering "did this degrade?" and only one speaking below
the threshold: the G-45 shape. WARN, not fail — a handful of degraded panels is worth
publishing around, and a non-zero exit would block the deploy on one bad card.

  Verified END TO END, not by unit test: the logic is inline in `main()`, and extracting a
  helper would have been a refactor outside this finding. Instead the real build ran with
  `deck_detail` monkeypatched to inject `[analysis error]` into 2 of 113 decks — far below
  the majority threshold. Result: `WARN: deck analysis failed for 2/113 deck(s): 2, 4 …`
  and **rc=0**, i.e. it still publishes, which is the intended posture.

F5 | scripts/wishlist.py | FOUR loops routed from `discover_decks()` to `roster_decks()`:
the `--add --target` validation set (~line 302), `_deck_colors_map` (land manabase
scoring), `_deck_status` (the `--rank` state column) and `_audit_target_issues`' known-deck
set. The audit named three; the fourth — the one with actual teeth — was found while
verifying the fix, because it is the site that decides whether `--target 0` is accepted.

  Before: `--target 0` (the `#: status: example` documentation placeholder) was ACCEPTED,
  while the fingerprint model 1,000 lines up already filtered on `is_roster_deck`. Two
  views of "which decks exist" inside ONE file — `--rank` scored against 113 while
  `--target` validated against 115 — and `_audit_target_issues` (the `check_all` soft
  sweep for target drift) read the permissive set, so it could never flag the result.
  After: `--target 0` → "no deck with id '0'", refused BEFORE any Scryfall work (G-74's
  asymmetry preserved), and zero-padded ids still resolve (G-82). Measured: 0 live
  wishlist rows target a non-roster deck, so this changes nothing today. The teeth are on
  the statuses that do not exist yet — `NONROSTER_STATUSES` has five members and the prune
  in `.cycle/prune-analysis.md` will mark decks `retired`.

F6 | tests/test_app_editor.py | 12 tests across two classes. `TestRequestGuard` covers the
DNS-rebinding Host check and the CSRF Origin check in BOTH directions — a guard that
refuses everything is as broken as one that refuses nothing, and looks identical from a
test that only asserts the refusal — plus the deliberate no-Origin allowance, safe methods,
and the non-local-bind relaxation. `TestDestructiveEndpoints` covers `/api/remove`
(including that a failed remove leaves the row), `/api/revert` (restore-what-remove-took,
and a clean 409 with no backup) and `/api/add`'s INV-02 contract (a new name must gain a
card-mana.csv row in the same request). All use the tmp-path `library` fixture, so no test
touches the real inventory.

  MUTATION-PROVEN: neutering `_guard_request` with an early `return None` fails exactly
  `test_a_cross_origin_post_is_refused` and `test_a_rebinding_host_is_refused`, and
  restoring it makes them pass. Before this, a grep across tests/ for Origin, Host, 403,
  `_same_origin` or `_guard_request` returned NOTHING: the entire security boundary of a
  write-capable server, unpinned, while CI's own comment called app.py "1,035 lines that
  write card-library.csv and deck files".

F7 | scripts/app.py, tests/test_app_editor.py | The absent-token bypass is RETIRED on both
dict-shaped saves. `sent and sent != token` meant an ABSENT token skipped the staleness
check entirely — a standing hole kept for "a cached pre-token page", and PINNED by two
tests named `test_an_absent_token_keeps_the_old_contract`.

  The decision rested on evidence, not preference: both templates send the field
  unconditionally (`lib_token: dataEl.dataset.libToken || ''`), the page is served by the
  same process that validates it, a successful save reloads, and — checked in
  `templates/deck.html`, not assumed — the NEW-deck page posts to `/api/deck/new`, which
  has no token gate, so deck creation cannot break. What the hole re-admitted is the exact
  failure BS2-26/BS8-18 exist to stop: an open tab silently reverting a CLI `swap --apply`.
  The CSV endpoint's BARE-LIST body is unambiguously the pre-token page and cannot carry a
  token, so it keeps the old contract; a DICT body is the current wire format and must.
  Both pins re-encoded to assert the 409, with the reversal and the one-line revert
  recorded in their docstrings.

Scenario 19 | CLAUDE.md | "Degraded analysis panels on the published page" — the operator
walk F2's sub-majority band needs, since a page already published carries no stderr.

TEST RESULTS: passed. `check_all.py` — All invariants hold, unchanged single soft warning
(4 dead library searches, G-75, accepted). pytest **1761 passed, 0 skipped**, from
1734 passed / 1 skipped. Two causes, worth separating: 12 new tests, and the disappearance
of the skip because Flask was installed into THIS environment so `test_app_editor.py` runs
locally instead of importorskipping. That is an environment change, not a repo change — CI
already installed requirements-app.txt and already ran these.

REGRESSION RISKS: Two identified and both MEASURED to zero rather than reasoned about.
(1) F5 could newly flag a live wishlist row whose Target names a non-roster deck — there
are **0**. (2) F7 could break new-deck creation if that page saved through the gated
endpoint — it posts to `/api/deck/new`, verified in the template. One BEHAVIOR CHANGE is
real and deliberate: a non-browser client POSTing a dict body to `/api/save` or
`/api/deck/save` without a token now gets a 409 where it previously succeeded unchecked.
That is louder and recoverable where the old path was silent and destructive, and the
bare-list body remains an escape hatch. F2 changes no return code and no output on a
healthy build.

INVARIANTS AT RISK: None. No CSV, deck file or derived artifact was written by this batch.
INV-02 is now COVERED by a test for the first time (`/api/add`'s mana-row contract), where
before it was only asserted by `check_all` after the fact.

NET SCORE: 0 production fixes − 0 new failure modes = 0
  Four DEFENSIVE/STRUCTURAL items. None of the four fixes a bug that fired this month: F2's
  window was real but measured empty (0 of 115 decks raise), F5's required someone to type
  `--target 0` and 0 live rows did, F6 changes no behavior at all, and F7 needed a stale
  tab. Recorded as 0 for the second batch running — under the old habit this would have
  read "4 − 0 = 4". Batches 2 and 3-4 together are 9 items and ZERO production fixes, which
  is the shape `defensive_count` exists to make visible.

OPERATOR ACTIONS / DEPLOY:
- None.
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds and publishes on push to
`main`. `build_dashboard.py` changed, so the next deploy carries the new WARN; the
committed `dashboard.html` is unchanged and still current (no deck file moved).

FOLLOW-ON ITEMS:
- Broad scan #9 is now FULLY IMPLEMENTED: all 8 findings across 4 batches.
- F2's sub-majority branch is verified end-to-end but has no unit test, because the logic
  is inline in `main()`. Extracting `_report_degradation(payload)` would make both it and
  the majority branch testable — a small, contained refactor, deliberately not done here.
- `tier_floor_spread()` still runs twice per `check_all` and is unmemoized (~2s), carried
  over from Batch 2.
- `figure_drift` covers 10 of ~1,100 numeric claims; the registry is still hand-kept.
- Scenarios 5–8 and 10–19 need a person at a browser; several have never been walked.

DOCUMENTATION UPDATES NEEDED:
- G-15 describes the editor's save gates and now under-describes them: it says the CSV save
  "carries a content-hash `lib_token` … a stale tab is refused with a 409", which is still
  true, but does not say that an ABSENT token is refused too (BS9-06). One clause. Also
  worth a line that the request guard is now pinned, since G-15 is where a reader looks for
  what the editor is trusted to do. -> /sync-docs
---END BROAD SCAN IMPLEMENTATION SUMMARY---
