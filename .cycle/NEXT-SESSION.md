# Handoff — start the next session here

Written at the end of the 2026-07 cycle, for a session with none of its context.
Read this before CLAUDE.md's Common Gotchas, not instead of them.

**The task for the next session is a SYSTEMS MAP, not a fix.** Details in §3.

---

## 1. Repo position

- `main` is at the squash-merge of PR #86. Everything from the last cycle is IN.
- The working branch `claude/add-cards-ingested-batch-cy2tdb` has been restarted
  from `main` and is clean. If its PR is merged again, restart it the same way
  (`docs/verify-commit-tail.md` §3).
- Gates green as of handoff: `check_all` all invariants hold; 651 pytest;
  `check_patterns` 145 live; `check_commands` OK (33 subcommands / 30 scripts).
- Collection: 1,853 cards, 66 decks. Decks 20, 42a and 46 became fully owned
  this cycle.

## 2. The diagnosis — read this before deciding what to build

**The models are in good shape. The composition layer is where the friction is.**

Current surface: **33 `deck.py` subcommands, 21 skills, 11 correctness gates,
8,748 lines in `deck.py`, 2,096 in CLAUDE.md.** Every model is bounded, anchored
and unit-tested. But **six commands rank cards by fit** — `cuts`, `suggest`,
`suggest-homes`, `screen`, `redundancy`, `tier --to` — each composing the same
theme-fit + role machinery differently, and **nothing checks that they agree**.

That produced one recurring bug class all cycle, always the same shape: **the
model was correct and the CALLER never asked.**

| incident | the model was right | the caller was wrong |
|---|---|---|
| `cuts` multiplier | `doubler_axis`/`doubler_support` scored Delney correctly for `suggest-homes` | `rank_cut_candidates` never called them |
| `owned_role_fillers` | `craft_role_fillers` applied the format filter | its owned sibling did not |
| `doubler_restriction` | power scopes parse correctly | type scopes were never asked about |
| `suggest --lands` | the legality check existed | the lands path never applied it |
| `rationale_staleness` | the per-deck check worked | nothing swept the roster |

Eleven gates verify each model is CORRECT. **None verifies that two models
answering the same question AGREE.** Where that check exists — `check_suggest`
anchor 13 (the two breadth models), `tests/test_verify_ingest.py` (the rebuild
order) — it was added reactively, one pair at a time, after a drift was already
found in production.

Two more, named honestly:

- **The decision surface is too wide.** Placing one card in one deck this cycle
  took `card` → `suggest-homes` → `screen` → `cuts` → `swap` → `quality --vs` →
  `preflight` → `tier --audit-rationale`. Eight commands — and the one that ranks
  cuts is a **45% coin flip on creatures** (§5), the regime where it is used most.
- **CLAUDE.md is doing two jobs.** It is simultaneously the operating manual and
  the incident changelog, and the second has crowded out the first. The operative
  rule ("route every colour parse through `card_colors()`") sits inside the
  narrative of the bug that motivated it. This is why a fresh session must load
  2,000 lines of prose to act safely. Do not "fix" this by deleting history — the
  history is why the rules are trusted — but a separated operating manual is a
  legitimate output of the mapping work.

## 3. The task: a TASK-FIRST systems map

### Why task-first is the whole point

A module map (deck.py / lib.py / wishlist.py / the gates) would teach nothing —
that structure is already legible and is not where the friction is. **Map the four
things the user actually does:**

1. **Ingest new cards** — `/ingest`
2. **Build a new deck** — `/draft-deck`
3. **Refine an existing deck** — `/tune-deck` → `/apply-changes`
4. **Prioritize crafts** — `/add-wishlist`, `wishlist.py --rank/--budget`

For each, record:

- the actual command path, in order, with what each returns
- **every point where a human must reconcile two answers by hand** — this is the
  deliverable, the rest is context
- which commands answer an overlapping question, and whether they agree
- the cost profile (see the `make refresh` note in §6)

### Getting `systems-map`

It is a **Tier-3 command from `claude-workflow-tools` and deliberately NOT
vendored** — CLAUDE.md §"Command provenance" records the reasoning: the ceremony
outweighed the benefit *at this project's size*. That judgement was probably right
when written and is worth re-testing at 33 subcommands.

Two options, in order of preference:

1. **Run the mapping directly** (a scoped `/broad-scan`, or by hand) without
   vendoring anything. The generic command is built for a module map; what is
   needed here is the task-first version above, so the generic one may need
   steering anyway.
2. **Vendor it via `/sync-commands`** if the generic structure turns out to fit.
   If you do, update the Command-provenance paragraph — that section is a
   hand-kept registry and this file's whole thesis is that those rot.

### Then, in order

2. **Add an agreement gate**, generalizing `check_suggest` anchor 13: any two
   functions answering the same question for different inputs — owned vs unowned,
   card vs deck, Python vs JS — must agree on a synthetic fixture. This is the
   gate the project has now built ad-hoc five times.
3. **Fix**, prioritized by the map, not by what is most recently annoying.
4. **Hold the surface**: net subcommand count should go DOWN or stay flat. If a
   fix wants a 34th subcommand, ask what it replaces.

## 4. What NOT to do

- **Do not open by writing code.** The tempting failure is to fix the creature
  cut-ranking, add a subcommand, and leave cohesion one command worse.
- **Do not re-weight `cuts`.** See §5 — it was simulated across all 64 decks and
  does not work. Re-weighting off the ledger is also structurally forbidden by
  `tests/test_recommendations.py`.
- **Do not audit `/roster-review`, `/log-matches` or the wishlist tooling
  speculatively.** They were barely exercised; there is no evidence of friction.
- **Do not touch the model internals.** They are the part that works.
- **`docs/tooling-improvement-plan.md` is HISTORICAL** (F01–F15, all landed, cycle
  closed) and is referenced from nowhere. Its F01 instructs adding
  `lib.full_card_text`, which was later **deleted** as dead code. A status header
  has been added; do not follow it as a plan.

## 5. Measurements — do not re-derive these

All measured this cycle. Re-deriving costs a roster sweep each.

**The recommendation ledger, at 52 scored swaps:**

| segment | agreement | median toward "keep" | n |
|---|---|---|---|
| noncreature cuts | 90% | 10% | 21 |
| creature cuts | **45%** | 56% | 31 |
| *pooled (what it used to print)* | *63%* | *28%* | *52* |

**Why:** `rank_cut_candidates` computes `fit` as an **unnormalized sum** —
`for t in tags: fit += theme_w[t]` — so tag count drives the keep-score, and every
co-signal (`_cuts_power_adj` / `_cuts_uniq_adj` / `_cuts_multiplier_adj`) is
bounded to ±3 and cannot reach a term spanning that range. Roster-wide,
**correlation(tag count, keep-rank) = +0.73, positive in 64 of 64 decks**.
Creatures carry ~5.7 tags against ~3.0 for noncreature spells.

**Normalization was simulated across all 64 decks and rejected:**

| fit variant | corr(tag count, keep-rank) |
|---|---|
| current (sum all) | +0.73 |
| top-3 themes | +0.72 |
| top-4 themes | +0.73 |
| mean of hits | +0.60 |

Top-3 changes **1% of top-5 shortlist slots**. The effect is not double-counting
within a card — tag count proxies for "is this card described by the tag
vocabulary at all", and a card matching zero themes gets fit 0 and sorts to the
top regardless of quality.

**So the real fix is probably a DIFFERENT SIGNAL for creatures, not a tuned
version of this one.** Bodies compete on stats, evasion and curve slot; theme-fit
structurally cannot see any of that. `card-pool.csv` already carries
`Power`/`Toughness` (read via `lib.card_power`) and nothing in the cut ranking
uses them. That is the most promising unexplored direction, and it is a
**hypothesis, not a conclusion** — nothing has tested it.

## 6. Open follow-ons

**Live and user-facing:**

- **`tier --audit-rationale` STAY-marker false negative.** A `_HISTORY_CUES`
  change-cue about ONE card suppresses a citation of ANOTHER card in the same
  ±140-char window, even when the clause says the card **stays**. Deck 42a
  asserted "Erode stay[s]" after Erode was cut and the audit reported the deck
  clean. Proposed fix is the mirror of `_cites_as_arriving`: un-suppress a
  citation carrying `stay`/`stays`/`remains`/`is kept`. **Needs a roster-wide
  sweep before landing**, per the cue-list rule. Until then a "X stays" claim is
  not covered — check by hand after a swap.
- **`doubler_restriction` parses power scopes only.** A type-scoped doubler
  (Splinter, Radical Rat's Ninja clause) is counted against the whole deck — 27
  feeders in deck 20 against a correct 12. The `✱ multiplier` figure on a tribal
  doubler is an upper bound. Fix is a second scope pattern feeding the same
  filter, not a second model.

**Cost / quality-of-life:**

- **`make refresh` costs the same for a 4-card ingest as for a full rebuild**
  (~10 min, re-pricing ~15.9k cards through Scryfall's rate limit). Nothing about
  the ingest loop needs that. An incremental path is likely the cheapest real
  quality-of-life win in the repo — but note the rebuild ORDER is load-bearing and
  pinned by `tests/test_verify_ingest.py`; any incremental path must not fork it
  into a second recipe (that exact drift is documented in CLAUDE.md, and the
  Makefile is deliberately the ONE executable definition).

**Smaller, from earlier blocks:**

- The reverse `screen` flag — a candidate strictly WORSE than an incumbent.
- ROADMAP Tier 1: theme the remaining UB flavor mechanics.

## 7. Where things are

- Per-cycle implementation blocks: `.cycle/blocks/*.md` — the newest is
  `2026-07-feedback-segmentation-broad-implement.md`.
- Prose state / decisions: `.cycle/STATE.md`.
- Commit discipline (shared by every writing skill):
  `docs/verify-commit-tail.md`.
- Long-range ideas: `ROADMAP.md` (regenerate with `/roadmap`).
- **Historical, do not follow:** `docs/tooling-improvement-plan.md`.

## 8. One thing to preserve

The habit that found nearly every real bug this cycle was **measuring before
believing** — the roster-wide before/after diff, the mutation test, the 64-deck
simulation that killed a fix that looked obviously right. Two of this cycle's
findings were bugs in my own new tests, caught only by mutating the code and
watching the test stay green. Whatever the next session builds, keep that.
