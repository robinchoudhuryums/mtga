# Block — task-first systems map + the agreement gate (2026-07-29)

The task set by `.cycle/NEXT-SESSION.md`: map the four things the user does, then add
an agreement gate generalizing `check_suggest` anchor 13, then fix by what the map
surfaces — holding the subcommand count flat.

All three landed. Net subcommand count: **33 → 33** (nothing added; one duplicate
MODEL removed).

## What shipped

### 1. `docs/systems-map.md` — the task-first map

Four workflows (ingest · draft · tune+apply · prioritize crafts), each with its real
command path, what each command returns, and a measured cost. The deliverable is the
**reconciliation points** — every place a human must settle two answers by hand — plus
an overlapping-answer inventory with measured agreement rates.

Deliberately NOT the generic Tier-3 `systems-map` command's module map: the module
structure was never the friction, which is also why vendoring the command stays
declined. CLAUDE.md's Command-provenance paragraph is updated to say so.

### 2. `scripts/check_agreement.py` — the twelfth hard gate

Registers QUESTIONS with two implementations each and fails when they disagree:
most-cuttable card · a card's format legality · copies owned · interaction count ·
power seed · owned-vs-craft role-filler filter parity. Prior art (`check_suggest` #13,
`tests/test_verify_ingest.py`) is left in place — moving it would trade one registry
for two.

Two design rules, written into the module docstring:
- **Prefer the LIVE ROSTER to a synthetic fixture** for a deck-shaped pair. A synthetic
  case only proves the pair agrees on the example its author wrote.
- **A stale entry is a HARD failure** — resolution is by attribute lookup at run time,
  so a rename fails the build instead of silently skipping the pair.

Cost: `check_all` 5.5s → 10.8s.

### 3. The fix the map surfaced — one cut-ranking model, not two

`_weakest_cut` (the cut hint on every `suggest-homes` row) carried a private three-term
formula while `rank_cut_candidates` (what `cuts` prints, what `tier --to` pairs adds
against, what the ledger scores swaps by) summed nine. **They disagreed on 36 of 64
decks.** Not cosmetic: `suggest-homes` proposed cutting Bloom Tender from deck 17 and
Vizier of the Menagerie from decks 34/36 — the roster's best fixers, and the exact cards
the `_is_color_fixer` work protects (the `add_is_fixer` guard only fires when the card
being ADDED is a fixer, so it never covered these).

Both now score through one `cut_keep_score` (+ `cut_scoring_context`). Ties break on the
card name, matching the printed ranking's sort — a min-scan keeping the first-seen winner
would otherwise resolve a tie by deck-file order.

Verified: **`deck.py cuts` output byte-identical across all 64 decks** after the
extraction, then 64/64 agreement after the rewire. `suggest-homes` 0.6s → 3.1s.

### 4. `load_rarities` memoized (found by profiling the new gate)

The one reference-table loader left out of the `_file_memo` sweep, and it hid because it
is read per CARD-SCORING PASS rather than per command. **85% of `deck.py cuts`' runtime**
(0.69s of 0.81s under cProfile). Took the gate's cut-ranking pair 12.0s → 2.3s.

## Measurements (do not re-derive)

| measurement | value |
|---|---|
| `_weakest_cut` vs `rank_cut_candidates` agreement, before | 28 / 64 decks |
| … after | 64 / 64 |
| `_signature_themes` (loose) boost fires on | **86%** of nonland cards across the 22 `#: protect:` decks; **100%** in decks 20 and 46 |
| `_strong_signature_themes` (strict) would fire on | 66% |
| `suggest` picks that also clear `suggest-homes`' central-theme gate | 640 / 640 (**100%**) |
| whole tune-deck gather phase | ~10s |
| `make refresh` | ~10 min |

## The part worth remembering

**The gate's own first two drafts were VACUOUS on the pair it was built for.** The
role-filler check ran green with the format filter deliberately deleted from
`owned_role_fillers` — twice — for two independent reasons:

1. it read the DEFAULT `limit`, so it saw the cheapest ten rows rather than the filtered
   SET, and the illegal card sorted below the cut; and
2. it asked only about the INTERACTION role set, whose one illegal filler (Dovin's Veto)
   is off-color for every deck in the sampled slice — while the card the original bug
   actually offered (**Deadly Dispute**) is a CARD-ADVANTAGE filler.

Both were found by mutating the code and watching the check stay green, never by reading
it. Generalizes to: **a pair is only covered on the axes you ask about, and a truncated
view is not the set.**

A second instance of the same discipline: the first measurement of `suggest` vs
`suggest-homes` reported 100% *disagreement*. It was reading a dict's keys as rows. The
real answer is 100% agreement. Measure, then check the measurement.

## Decisions made

- `_weakest_cut` keeps its `(dmeta, cards, cardmeta, carddata)` signature rather than
  taking a deck dict, so `check_suggest` anchor 15 and the existing unit tests keep
  working against their in-memory fixtures. The shared score is the extraction point.
- The role-filler pair is CAPPED at 3 decks and says so in its output. `craft_role_fillers`
  walks the whole pool per deck, and the property is per-deck filter parity keyed on
  `#: format:`, which is Standard for all 64 decks — so deck 7 tests what deck 40 would.
  Verified the mutation still fires at the cap. Raise it the day the roster spans formats.
- The `_signature_themes` saturation finding was NOT fixed. It changes the cut ranking,
  and the standing rule is that a scoring change needs a roster-wide before/after diff
  first. Recorded in the map's §7 with the numbers.

## Follow-on items

1. **`_signature_themes` saturation in `cuts`** (§7 of the map). Switching to the strict
   set would unify it with the three `fit_strength` callers and de-saturate 86% → 66%.
   The motivating case (deck 30's counter-doublers) survives — its strict signature is
   exactly `{counters}`. Needs the roster diff.
2. **`make refresh` has no incremental path** — still the largest single cost in the repo.
   Any fix must not fork the rebuild order into a second recipe.
3. Carried forward unchanged: the `tier --audit-rationale` STAY-marker false negative,
   and `doubler_restriction` parsing power scopes only.
4. The creature cut-ranking regime (45% agreement) is still open. The map records the
   standing hypothesis — `card-pool.csv` carries `Power`/`Toughness` and nothing in the
   cut ranking reads them — and that it remains untested.

## Verification

- `check_all` — all invariants hold (11.3s).
- `pytest` — 668 passed (was 651; +17 in `tests/test_check_agreement.py`).
- `deck.py cuts` byte-identical on all 64 decks across the extraction.
- Three code mutations and three test mutations, each confirmed to fail.
