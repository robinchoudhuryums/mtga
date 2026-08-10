---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS4-01 | `#: protect:` / `#: uncastable-ok:` consumers joined on raw lowercase names — LIVE-broken on deck 66
- BS4-02 | `make postedit` auto-acknowledged every new zero-role card, muting the check_roles radar
- BS4-03 | `reconcile_crafts.py` had no basic-land guard — a full deck paste wrote basics into the library
- BS4-04 | `import_arena` appended a phantom printing for a `(SET)`-but-no-collector line (silent over-count)
- BS4-05 | `cmd_screen`'s "already in the deck" probe missed every pool-keyed DFC
- BS4-06 | `cmd_suggest_homes`' `already` join was one-sided (deck side un-normalized)

Files modified:
- scripts/deck.py
- scripts/check_roles.py
- scripts/import_arena.py
- scripts/reconcile_crafts.py
- Makefile
- tests/test_deck.py
- tests/test_check_roles.py
- tests/test_ingest.py
- tests/test_reconcile_crafts.py

CHANGES:

BS4-01 | scripts/deck.py | New `_header_card_keys(meta, header)` — the ONE place both header
readers share — returns `_ms_key`-normalized keys (lowercased, front face). `_protected` and
`_uncastable_ok` now delegate to it, and all six consumers key their side too:
`_castability`'s exempt test, `_signature_themes`, `_strong_signature_themes`,
`rank_cut_candidates`, `_weakest_cut`, and `recommendation_row`'s `Cut Protected`.
`_do_swap`'s guard simplified (the header side is normalized at source now).
The fix belongs at the reader, not per call site: the previous state had every consumer
re-deciding raw-vs-`_ms_key`, which is how the class regenerated across three scan cycles.
Note the gate could not catch this — `header_card_staleness` has always joined on `_ms_key`,
so it certified deck 66's header HEALTHY while the consumers could not read it.

BS4-02 | scripts/check_roles.py, Makefile | Added `baseline_delta()` (returns newly-acknowledged
DISPLAY names + pruned entries), plus `--max-new N` and `--show-delta` on `--update-baseline`.
`--update-baseline` now always computes the delta first, NAMES every card it acknowledges, and
REFUSES a jump larger than `--max-new` (exit 1, writes nothing) because a jump that size is a
`_ROLE_PATTERNS` regression rather than a batch of genuinely roleless new cards. `make postedit`
passes `--max-new $(MAXNEW)` with `MAXNEW ?= 8`; a deliberate bulk acknowledge is
`make postedit MAXNEW=40`. The one-command ergonomics are preserved — only the silence is gone.

BS4-03 | scripts/reconcile_crafts.py | Added the `BASICS` set and a hard skip BEFORE any pool
lookup, REPORTED in its own output section (a dropped line the user pasted must be visible).
Hard-skipped rather than opt-in: a basic is never crafted, so this tool has no legitimate reason
to record one. Matches `import_collection`'s posture; `import_arena` keeps `--skip-basics` because
it also ingests genuine collection exports.

BS4-04 | scripts/import_arena.py | The name-level-claim guard changed from
`not set_code and not collector` to `not collector`. `LINE_RE` makes the collector group optional,
so `4 Llanowar Elves (DOM)` keyed as ("llanowar elves","dom","") — matching no real row, because
real rows carry a collector number — and appended a phantom printing beside the owned one; every
consumer sums across printings, so a real 4 read as 8. Note strings now name the actual shape
("(DOM) line with no collector #"). A legitimately blank-collector row (G-11: enrich leaves it
blank rather than guessing) joins the family and is topped up rather than duplicated.

BS4-05 | scripts/deck.py | `cmd_screen`: `present=_ms_key(nl) in in_deck` (was the full display
name against an `_ms_key`-built index).

BS4-06 | scripts/deck.py | `cmd_suggest_homes`: both sides of `already` through `_ms_key`.

TEST RESULTS: PASSED.
- `python3 scripts/check_all.py` — "All invariants hold. ✓", exit 0, ZERO soft warnings.
- `python3 -m pytest` — 1,105 tests, all passing, exit 0 (was 1,087; +18 added here).
- CLI smoke (the CI shape — traceback detection, not exit code): 35 scripts' `--help` and 68
  `deck.py` subcommand helps render with no traceback.
- Regression Scenario 2 (Analyze a deck) walked on deck 66, the one deck whose output changed:
  all 12 subcommands clean, `tier --audit-rationale` reports the rationale current.
- Regression Scenario 1 (Ingest) ingest leg walked non-destructively against a COPY of the
  library: `4 Llanowar Elves (DOM)` topped up the existing printing (row count unchanged at 1)
  and INV-01 passes. Under the old code that line appended a second row.

REGRESSION RISKS: Measured rather than reasoned about. A/B ran the full 97-deck roster through
a pre-fix copy of `scripts/` and the fixed tree, comparing uncastable count, tier floor, protected
list, top cut candidate and cut-list length per deck.
- **Exactly ONE deck changed: 66.** Its protect list gained the title card it was always meant to
  protect (`Eddie Brock // Venom, Lethal Protector`), and its cut list shrank 31 → 30 accordingly.
- **ZERO tier floors moved** (distribution unchanged: 87 A / 10 B) and **zero uncastable counts
  changed** (all 97 decks read 0). The `uncastable-ok` half of BS4-01 is the dangerous one — it
  can raise a floor by exempting a card — and it had no live instance today, so nothing re-graded.
- The `_signature_themes` / `_strong_signature_themes` change feeds KEY promotion in
  `fit_strength` / `screen` / `similar`; it is reachable only through a protected DFC, of which
  deck 66's is the only one on the roster, and that deck's top cut candidate did not move.
- `check_roles.check()` (what `check_all` calls) is untouched; only `main()`'s `--update-baseline`
  path gained behavior. New flags default to off (`--max-new 0` = no limit), so a bare
  `--update-baseline` behaves exactly as before apart from now naming what it acknowledged.
- Old behavior was never correct in any of these cases: each fix makes a join agree with the
  index it queries, or makes a skip visible.

INVARIANTS AT RISK: None.
- INV-01 — BS4-03 and BS4-04 both strictly REDUCE row creation (a basics row, a phantom
  printing), and BS4-04 removes a latent delayed INV-01 break (enrich backfilling the phantom
  collector into an exact-duplicate printing). Verified: `validate.py` exit 0 on a real
  end-to-end import.
- INV-02 — BS4-03 skips basics before the mana-row append, so no library name is left without a
  mana row; unit-pinned.
- INV-03/INV-04 — untouched; `check_all` green.
- G-63 (front-face joins) — this change is a net closure of that class, not a risk to it.
- G-56 (recommendations ledger is report-only) — `recommendation_row` still only WRITES; no
  scoring function reads the ledger. `tests/test_recommendations.py` structural scan passes.
- G-25/G-60 (report-only axes stay out of `tier_band`) — no new term added; floors verifiably
  unmoved across the roster.

NET SCORE: 6 production fixes − 0 new failure modes = 6
Per-finding: (a) would it have fired this month? (b) new failure mode introduced?
- BS4-01: (a) YES — already firing on deck 66 since 2026-08-08. (b) NO.
- BS4-02: (a) YES — `make postedit` is the standard post-edit command. (b) NO. `--max-new`
  can refuse a legitimate bulk acknowledge, but it exits 1 with the names and the exact
  remedy printed, so it fails loud and forward rather than silently.
- BS4-03: (a) YES on any full-deck paste; the tool is the documented fastest reconcile path. (b) NO.
- BS4-04: (a) Conditional — needs a set-stamped, collector-less list; silent over-count when it
  happens. (b) NO.
- BS4-05: (a) YES — six live deck/card combos (decks 6, 11, 31, 40a ×2, 42a). (b) NO.
- BS4-06: (a) YES — same six combos, inverse surface. (b) NO.

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push (no build/release step). The dashboard is
republished automatically by `.github/workflows/pages.yml` on push to `main`; no dashboard
template or `#data` pipeline code was touched, so no manual dashboard rebuild is required.

FOLLOW-ON ITEMS:
- `recommendation_row`'s `Cut Rank` lookup (scripts/deck.py, next to the `Cut Protected` line
  fixed here) still joins on a raw lowercase name, so a front/full spelling difference blanks the
  rank. Telemetry only, never blocks a swap (G-56) — deliberately left out of scope.
- `BASICS` is now defined in FOUR modules (deck.py, import_arena.py, import_collection.py,
  reconcile_crafts.py). Consolidating into `lib` would touch three files outside this scope.
- The remaining audit findings BS4-07 … BS4-45 are unimplemented, including the two other
  Mediums with live output impact: BS4-07 (`#: archetype:` figures are never audited, against
  G-27's documented scope — deck 26a quotes avg MV 3.05 vs a live 2.97) and BS4-13 (`/decks`
  and `check_all`'s info summary compute buildability per-line, not per summed name).
- `docs/gotchas.md:3080` and `.cycle/NEXT-SESSION.md` §6 still describe BS2-07 as the open
  member of the G-63 class "measured at zero live instances". That is now both closed and
  factually stale — see DOCUMENTATION UPDATES.

DOCUMENTATION UPDATES NEEDED:
- `docs/gotchas.md` G-63 section (~line 3080): BS2-07 is CLOSED. Replace the "one member remains
  open … measured at zero live instances" paragraph with the closure, and record why the
  measurement expired (deck 66, drafted after it was taken) — the lesson is that a
  zero-instances measurement is a fact about a moment, not a property of the code.
- `.cycle/NEXT-SESSION.md` §6 ("The one open item from the cycle's own findings"): now closed.
- `CLAUDE.md` G-63: add that the header consumers are closed, and that `_header_card_keys` is the
  single normalization home for `#:` headers naming cards (the `alias_front` of the header side).
- `CLAUDE.md` — new gotcha candidate: "a baseline updated BEFORE the gate that reads it is a muted
  gate" (BS4-02), and the `make postedit MAXNEW=` escape hatch.
- `README.md` reconcile-crafts section: note that basic lands are skipped and reported.
- `README.md` / import_arena docs: a collector-less line is a NAME-level claim whether or not it
  carries a set code.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
