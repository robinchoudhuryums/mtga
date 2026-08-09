---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (Batch 3 — gate credibility):
- BS4-09 | check_commands' skill-side subcommand match counted a prose mention (a caution NOT to run a command granted it coverage)
- BS4-10 | `--update-baseline` was all-or-nothing on BOTH baselines, with no delta reported
- BS4-25 | check_commands' Makefile-coverage regex matched COMMENT lines
- BS4-26 | check_keywords' ENGINE_THEMES cross-check died silently on an attribute rename
- BS4-28 | check_agreement's `_agree_owned` skipped silently on an empty collection
- BS4-29 | check_themes reported its 40-row CAP as the count
- BS4-30 | Seven gates had no "watched-it-fail" layer, contradicting test_check_all's own docstring
- BS4-31 | check_commands' standalone `main()` tracebacked where `check()` degrades cleanly

Files modified:
- scripts/check_commands.py
- scripts/check_keywords.py
- scripts/check_agreement.py
- scripts/check_themes.py
- scripts/check_all.py
- tests/test_gates_fire.py (NEW)
- tests/test_check_all.py

CHANGES:

BS4-09 | scripts/check_commands.py | New `_cited_as_usage(text, pattern)`: a match counts
as coverage only if at least one occurrence sits OUTSIDE a caution clause
(`_CAUTION_CUES`, clause-scoped via `_CLAUSE_EDGE`). The script half has required an
executable shape since BS2-31 — two of build_pool.py's three skill mentions were warnings
NOT to run it — and the subcommand half kept a plain text match, so the same hole was open
one column over. **The obvious fix was measured and REJECTED**: requiring
`python3 scripts/deck.py <name>` would have failed 27 of 34 live subcommands, because the
skills legitimately write 30 of their references in the bare `deck.py <name>` form and only
3 subcommands appear inside fenced code blocks. Suppressing the caution CLAUSE costs
nothing today — measured: zero subcommands lose coverage — while closing the hole.

BS4-25 | scripts/check_commands.py | `_strip_make_comments()` removes `#` lines before the
Makefile coverage match. Makefile line 3 mentions `scripts/app.py` in a comment, so the
"do NOT run scripts/foo.py here" shape would have granted coverage to a script nothing runs.

BS4-31 | scripts/check_commands.py | `main()` wraps its re-derivation of
`deck_subcommands()`/`runnable_scripts()`; an unparseable deck.py now prints a clean FAIL
instead of raising the RuntimeError `check()` had just handled — the standalone run is
exactly the one you reach for when the gate is unhappy.

BS4-10 | scripts/check_keywords.py | `baseline_delta()` (the sibling of check_roles', added
in the previous batch) plus `--max-new` and `--show-delta` on `--update-baseline`. It now
names every keyword it acknowledges and refuses a regression-sized jump. K-01 is why this
matters more than the count suggests: a keyword's reported COUNT is not its population
(`jump` reports 13 cards of which 11 are `Jump-start`), so entries must be READ one at a
time, not tallied.

BS4-26 | scripts/check_keywords.py | `getattr(_dk, "ENGINE_THEMES", {})` replaced with an
explicit `hasattr` check that raises. The default made a RENAME take the silent path: the
loop produced no engine words, the `-2` overreach signal evaporated, and the `except`
written precisely so this could not die quietly never fired, because nothing raised. A
structural error was loud while the likeliest refactor was silent.

BS4-28 | scripts/check_agreement.py | `_agree_owned` appends a loud WARN instead of a bare
`return` on an empty collection, matching the BS2-32 discipline its two siblings already
follow. "No disagreement found" and "nothing was compared" were the same output.

BS4-29 | scripts/check_themes.py, scripts/check_all.py | The scan is now one generator
(`_iter_flags`) that `flags()` caps and `flags(count_only=True)` counts in full; check_all
reports the TOTAL and shows the capped list as examples. `len(tflags)` counted a 40-row
cap, so 400 mis-tags reported as "40" — a number that cannot move, which reads as a stable
known quantity rather than a growing one (the delta-blind shape K-01 documents).

BS4-30 | tests/test_gates_fire.py (NEW, 24 tests) | The watched-it-fail layer for
check_colors, check_rankings, check_suggest, check_engines, check_tier, check_themes and
check_keywords. Each test breaks the model a gate guards and asserts the gate reports it,
with a baseline class asserting all seven are quiet on the real repo first (so a firing is
attributable to the mutation). Two mutations had to be rewritten after measurement rather
than guessed: an EMPTY theme model makes check_rankings return early ("too few decks to
assert a distribution"), which proves nothing — the real model is kept and only the cutoff
is moved, in both directions; and `engine_roles` returns `{theme: {roles}}`, so the
"sees everything" mutant maps every ENGINE_THEME to both sides.
tests/test_check_all.py's docstring, which asserted this coverage while it was false of
seven gates, now says so.

TEST RESULTS: PASSED.
- `python3 scripts/check_all.py` — "All invariants hold. ✓", exit 0, ZERO soft warnings.
- `python3 scripts/check_docs.py` — OK (95 rules linked).
- `python3 scripts/check_commands.py` — OK, 34 subcommands / 33 scripts, 6 exemptions.
- `python3 -m pytest` — 1,170 tests, all passing, exit 0 (was 1,146; +24).
- CLI smoke: 35 scripts' `--help` render with no traceback.
- **The new tests were themselves mutation-tested**: making each of the five hard gates'
  `check()` return `[]` unconditionally (the vacuous-gate shape) was DETECTED in all five
  cases. The tests catch a dead gate, not merely a broken model — which is the property
  BS4-30 is about.

REGRESSION RISKS:
- **BS4-09 is the one that could remove real coverage**, since it makes a passing gate
  stricter. Measured before landing: zero subcommands lose coverage today, and the
  gate still reports OK on all 34. The cue list is deliberately narrow (nine words) and
  clause-scoped, per G-26's rule that a broad suppression silently drops real signal.
- BS4-25 could in principle un-cover a script whose ONLY Makefile reference is in a
  comment; `check_commands` still reports OK for all 33, so none was.
- BS4-29 changes `check_themes.flags()`'s signature (new `count_only` kwarg, default
  False) — additive, and the only other caller (`check_all`) was updated in the same
  commit. `flags()`'s capped behaviour is unchanged.
- BS4-26 converts a silent default into a raised AttributeError that the existing handler
  catches and prints; the gate's other two signals continue to run, as before.
- BS4-10's `--max-new` defaults to 0 (no limit), so a bare `--update-baseline` behaves as
  it did apart from now naming what it acknowledged. Nothing automated passes `--max-new`
  for keywords yet — `make postedit` only re-baselines ROLES.
- No scoring model, tier floor or recommendation output was touched by this batch; it is
  entirely gate-layer.

INVARIANTS AT RISK: None. This batch changes only the gates and their tests; INV-01…04 are
untouched and `check_all` is green with zero soft warnings. The one contract worth naming:
`check_themes.flags()` keeps its default cap, so no consumer sees more rows than before.

NET SCORE: 8 production fixes − 0 new failure modes = 8
Per-finding: (a) would it have fired this month? (b) new failure mode introduced?
- BS4-09: (a) NO — zero live instances measured. (b) NO; measured as costing no coverage.
- BS4-10: (a) NO — no keyword bulk-acknowledge happened. (b) NO (opt-in flag).
- BS4-25: (a) NO. (b) NO.
- BS4-26: (a) NO — ENGINE_THEMES exists. (b) NO.
- BS4-28: (a) NO — the collection loads. (b) NO.
- BS4-29: (a) YES if the theme radar ever exceeds 40 — it reports 0 today, so the wrong
  number was latent rather than displayed. (b) NO.
- BS4-30: (a) N/A — a test-coverage gap, not a runtime bug; its cost is invisibility.
- BS4-31: (a) NO. (b) NO.
**Read this tally honestly: this batch fixed almost nothing that was actively misbehaving
today.** It is insurance on the layer everything else is trusted through, which is why it
ranked third rather than first.

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push. No presentation artifact changed, so no
dashboard rebuild is implied by this batch.

FOLLOW-ON ITEMS:
- `make postedit` passes `--max-new` to check_roles only; check_keywords' new `--max-new`
  has no automated caller. Deliberate — nothing bulk-acknowledges keywords today, and
  wiring a flag with no caller is the "capability nothing reaches" shape G-53 warns about.
- Batch 4 (structural/latent DFC: BS4-18/20 in-pass aliasing, BS4-12 identity-vs-cost
  colours, BS4-11 rotation flags, BS4-19/32/34/35/36/33/37) and Batch 5 (interface polish)
  remain, plus the six operator visual checks.
- The committed `dashboard.html` snapshot still carries the pre-BS4-41 loader.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-53: the "REAL call, not a prose mention — on BOTH paths" claim is now true of
  all three paths (skill subcommand, skill script, Makefile); record that the
  executable-shape rule was measured and rejected for subcommands, and why.
- CLAUDE.md G-69: the all-or-nothing rewrite it names as "still sitting under
  `check_keywords.py --update-baseline`" is now fixed — that sentence is stale.
- CLAUDE.md C-01 / docs/cycle-config.md: the Testing subsystem inventory says "29 files";
  it is 30 with test_gates_fire.py, and the gate list can note that all fourteen now have
  a watched-it-fail layer.
- K-01 could record that the keyword baseline now names what it acknowledges, since that
  rule is the reason keywords must be read individually.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
