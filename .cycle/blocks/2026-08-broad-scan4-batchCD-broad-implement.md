---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- C1 | A DETERMINISM gate — the property no gate in this project checked
- C2 | NOT IMPLEMENTED — measured as not achievable at useful quality. See below.
- C3 (BS5-07) | `check_colors`' exemption was a substring test a COMMENT could satisfy
- D1 (BS5-08) | `card.py` printed the COMBINED mana value for split / Room cards
- D2 (BS5-06) | The pool's tag fingerprint hashed all of `deck.py`, so it read stale every cycle
- D3 (BS5-09) | `parse_matches.py --report` was silently dropped when a source was given
- D4 | `docs/tooling-improvement-plan.md` retired

Files modified: tests/test_determinism.py (new), scripts/check_colors.py, scripts/card.py,
scripts/build_pool.py, scripts/parse_matches.py, CLAUDE.md, README.md,
docs/tooling-improvement-plan.md (deleted)

CHANGES:

C1 | tests/test_determinism.py (new) | Runs seven read-only commands under two
  PYTHONHASHSEED values in a thread pool and asserts byte-identical stdout: `similar`,
  `stats`, `cuts`, `tier`, `suggest`, `audit`, and `wishlist.py --rank` (one command from
  a different module, so the property is not pinned to deck.py alone). Fourteen gates
  verify each model is CORRECT and one verifies two models AGREE; none could see a command
  that is correct on any single run and answers differently on the next, because they all
  evaluate the code once inside one interpreter where set order is fixed.
  **Placed in pytest, not check_all, deliberately.** The check needs separate interpreters
  with a controlled env, which is the one thing an in-process gate cannot arrange —
  check_all imports `deck` as a module and its whole design (memoized loaders, no
  subprocesses) is what keeps it at ~4s. This follows the precedent G-55 set for the
  argparse tree: a surface check_all structurally cannot reach belongs in the pytest layer
  plus CI. Measured cost: **7.3s** for the module.
  WATCHED FAILING against the real pre-fix code — `git show d017353:scripts/deck.py`
  swapped in, the gate fails on `similar` with the tie reorder visible in the diff
  (`etb(10), burn(10)` vs `burn(10), etb(10)`); deck.py restored byte-exact afterwards.
  It also carries `test_the_check_can_actually_fail`, which proves the seed reaches the
  subprocess so the other seven assertions cannot go vacuous.

C2 | (no change) | NOT IMPLEMENTED — and the measurement is the deliverable.
  Three scan designs were prototyped against the two generated pages:
  * click-binding scan requiring `a11y(` on the target → **14 flags, all false**
    (`const pin = a11y(el(...))` wraps at CREATION, so `a11y(pin` never appears; `$('id')`
    targets that are real `<button>`s; overlay backdrops that are correctly not controls);
  * refined with declaration lookup and native-control detection → **13 flags, all false**
    (JS variable scoping: four different `tb` / `x` / `p` / `s` in different scopes, which
    a regex over a Python string containing JS cannot resolve);
  * markup-level rules (an `<a>` with no href; an element a delegated selector targets
    without tabindex) → flags the two sites that ARE fixed (they are a11y'd at RUNTIME, so
    the markup legitimately lacks the attributes), plus a comment containing "<a>" and two
    `.card` ITERATION selectors.
  The blocker is structural: the a11y happens at runtime through `a11y()`, so a
  markup-level rule flags correctly-fixed code and a JS-level rule cannot scope variables.
  Resolving it needs a JS parser, which breaks the project's zero-dependency constraint.
  A baselined delta-scan (the `check_roles` pattern) would work mechanically but needs ~14
  acknowledged entries and inherits G-69's acknowledge-before-warn muting risk.
  **The coverage that does exist is the right one and is already scheduled**: Regression
  Scenario 7 now walks both repaired controls by keyboard, including the post-sort re-Tab.

C3 | scripts/check_colors.py | `_guards_colorless(node)` replaces
  `"colorless" in ast.get_source_segment(...).lower()`. The old test was satisfied by a
  COMMENT — the same substring-standing-in-for-a-comparison shape this file exists to
  catch. The new one walks the function's AST for an actual comparison against the literal,
  or a call to `card_colors` / `color_matches` (a function that delegates to the safe
  primitive has handled the trap rather than guarding it inline). All four currently
  exempted sites still pass; verified directly that a comment-only mention now returns
  False where it used to return True.

D1 | scripts/card.py | Recomputes Mana Value from the FRONT face when the cost contains
  `" // "`, matching what `deck.load_mana` has done for a year. Mirror Room // Fractured
  Realm displayed **MV 10** and now displays **MV 3**, which is what every analysis surface
  (stats, the curve, consistency) already used — so the inspection surface G-01 mandates
  for pre-grading reads no longer contradicts them. The full two-half cost is still shown
  (it is the printed card), with a line naming which half the MV describes, because an
  unqualified number beside a two-half cost invites the same misreading in a human that
  the raw column caused in the code.

D2 | scripts/build_pool.py | `tagger_fingerprint()` now hashes `tag_synergies.py`'s bytes
  plus a canonical `json.dumps(deck.ENGINE_THEMES, sort_keys=True)` — the VALUE the tagger
  consumes — instead of all of deck.py. BS4-37 widened it to the whole file to avoid a
  hand-kept attribute list and described the cost as "an occasional unnecessary rebuild";
  it was every cycle, because deck.py changes every cycle. The pool was reading stale on
  2026-08-12 purely because unrelated `similar` and buildability edits had landed, forcing
  a ~4-minute refetch of 15.9k cards for a reason that was almost never real. Verified:
  an unrelated deck.py change no longer stales the pool, an ENGINE_THEMES change still
  does, and the fingerprint is identical across three PYTHONHASHSEED values (`sort_keys`
  is load-bearing — a future set leaf would otherwise make the change-detector itself
  order-dependent, the G-54 shape inside the mechanism meant to detect change).

D3 | scripts/parse_matches.py | `--report` composes with a source on every SUCCESS path —
  the normal ingest, the summaries-only path, and `--map-decks`. The gate was
  `if args.report and not args.source`, so `parse_matches.py session.log --apply --report`
  did the ingest and printed nothing. Error paths are deliberately excluded: a report after
  a failed read would read as reassurance. It re-reads matches.csv rather than reporting
  `existing + fresh` in memory, so a dry run describes the record as it STANDS.
  (First attempt fixed only the last return and still dropped the report on the
  summaries-only path — caught by running all three paths rather than the obvious one.)

D4 | docs/tooling-improvement-plan.md (deleted), CLAUDE.md, README.md | Removed, with both
  references updated. The CLAUDE.md entry now records WHY: a "historical, do not follow"
  status header was tried first and is not enough, because the file still reads like a plan
  to anything that greps it, which is how a fresh session finds things. A completed plan is
  not a record — `.cycle/blocks/` is, and git holds the file.

TEST RESULTS: passed. **1278 tests collected, full suite green** (+8: the seven determinism
commands plus the can-it-fail pin). `check_all.py`: all invariants hold, **ZERO soft
warnings**. `check_docs.py` OK. `check_commands.py` OK — 34 subcommands and 33 scripts all
reachable, unaffected by the deleted doc and the new test file.

REGRESSION RISKS:
- **D2 changes the fingerprint ALGORITHM, so every existing stamp mismatches and the next
  `build_pool.py` run rebuilds once.** That is the designed behaviour for an unknown stamp
  and it is a one-time ~4-minute cost, but it will happen on the next `make refresh` and
  should not be mistaken for the bug it fixes.
- D1 changes `card.py`'s displayed MV for the 292 pool cards with a two-half cost. This is
  the fix, but any note or rationale quoting a combined MV from this surface is now
  contradicted by it — which is the correct direction, and the rationale audit does not
  read `card.py` output.
- C1 asserts on the STDOUT of seven commands, so a deliberate output change to any of them
  makes the module fail until re-run. That is a maintenance cost, not a defect: it fails
  loudly and the fix is to re-run, unlike a golden-file test it does not store expected text.
- C3 could in principle exempt a function that calls `card_colors` for an unrelated reason
  while ALSO doing a naive inline parse. Strictly narrower than the substring test it
  replaces, so no site loses coverage.

INVARIANTS AT RISK: None. No CSV or deck file written — `git status decks/` clean
throughout. INV-03 re-verified (check_all green). `card-pool.csv` was NOT rebuilt: D2
changes only how staleness is DETECTED, and rebuilding needs Scryfall egress; the pool's
content is unchanged and the next refresh will re-derive it through the same `tags_for`.

NET SCORE: 5 production fixes − 0 new failure modes = 5
(C1 and C3 are gates rather than bug fixes, so they are counted as fixes to the DETECTION
gap each names. Would they have fired this month: D2 YES — the pool has been reading stale
since 2026-08-11 and would have cost a needless refetch on the next refresh; D3 YES for
anyone typing the natural post-ingest invocation; D1 YES on any split/Room card inspected
before grading, which G-01 mandates. C1 would have caught BS5-01. C2 is not counted — it
was not built.)

OPERATOR ACTIONS / DEPLOY:
- **A2 — run `import_collection.py` against a full tracker export** (still outstanding from
  Batch A; A1 is now done). Five ownership counts were wrong on 2026-08-09, one
  load-bearing in a recommendation, and nothing in the toolchain can detect it. Should
  precede any wildcard spend. | BLOCKS DEPLOY: N
- **A3 — the two visual checks** in Regression Scenarios 5 and 7 (gallery light mode;
  keyboard walk of the two repaired dashboard controls). Scenario 7 is now the ONLY
  coverage for the C2 class, which raises its value. | BLOCKS DEPLOY: N
- **Expect one full pool rebuild** on the next `make refresh`, from D2's fingerprint
  change. Normal, one-time. | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds and publishes on push to
main. Data + local tooling ship by commit/push. Nothing in this batch changes the
dashboard or gallery output, so no snapshot rebuild was needed.

FOLLOW-ON ITEMS:
- **C2 remains open** and now has a measurement attached. If it is ever revisited, the
  baselined delta-scan is the only design that survived scrutiny; weigh it against G-69's
  muting risk. The honest alternative is to keep the coverage human (Scenario 7).
- `cmd_check` joins card names with `", "` while card names contain commas, so "12 not in
  library: …" reads as 16 names; the repo already uses `;` for `#: protect:` for this
  reason. Carried over from the Batch A&B block, still unfixed.
- `launchctl load` in log-matches.md Stage 0 is deprecated on macOS 11+ in favour of
  `launchctl bootstrap gui/$(id -u)`. Works today; worth modernising when that file is next
  touched. (A1 is installed, so this is cosmetic now.)
- Batch E (strategic: match volume, the recommendations↔matches join, sheets_sync setup,
  the Brawl conversions, decks 19/21a tier re-grades) is untouched.

DOCUMENTATION UPDATES NEEDED:
- G-54 should gain a line pointing at `tests/test_determinism.py` as its enforcement, and
  say WHY the gate is in pytest rather than check_all (separate interpreters).
- G-72's closing line says the perceptual halves "live in Regression Scenarios 5 and 7".
  That is now the ONLY coverage for the JS-control class — worth stating explicitly, with
  the C2 measurement, so a later cycle does not re-attempt the scan from scratch.
- G-18 / K-10 describe the pool freshness fingerprint as hashing deck.py; both should say
  ENGINE_THEMES' value instead, and record why the coarser hash was reverted.
- G-02's "residual 2" (card.py prints the combined MV) is now CLOSED and should be struck
  from the residual list.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
