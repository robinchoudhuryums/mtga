# Handoff — start the next session here

Written 2026-07-31, for a session with none of this one's context.
Read this before CLAUDE.md's Common Gotchas, not instead of them.

**Read the evidence file when a rule's reasoning matters.** CLAUDE.md carries the RULE and
any live residual; the incident and measurement live under the anchor the rule ends with —
`[G-nn]` / `[K-nn]` in `docs/gotchas.md`, `[C-nn]` in `docs/cycle-config.md`. Nothing was
deleted; open the long form before deciding a rule looks arbitrary. **Keep Cycle Workflow
Config terse** — its shape is specified by `setup-cycle.md` in claude-workflow-tools and
the vendored commands read those fields.

**Also live: `docs/systems-map.md`.** Read it when you need to know which command answers a
question, what a workflow's real command path is, or why two commands disagree.

---

## 1. Repo position

- Working branch `claude/project-development-continuation-3hnw5r`, based on `origin/main`
  at the squash-merge of **PR #93**. **If its PR is merged, restart it from `main`**
  (`docs/verify-commit-tail.md` §3) — it has been merged three times this cycle, so assume
  it needs the restart and check.
- Gates green at handoff: `check_all` all invariants hold (**14.8s**); **767 pytest** in 16
  files; `check_patterns` 145 live; `check_commands` OK (33 subcommands / 32 scripts, 5
  exemptions); `check_agreement` OK; `check_docs` OK (87 anchors linked).
- **CLAUDE.md is 868 lines.** The doc split is COMPLETE and gated in both directions.
- Collection: **1,860 cards, 76 deck files.** Both moved this cycle — decks 51 and 51a were
  built, deck 49 refined.

## 2. What the last three sessions did

One theme, found late and named only at the end: **a two-faced card's FRONT face and its
stored metadata disagree**, on every column, and five separate places trusted the metadata.
Each was found by deck work, none by a gate.

1. **P1–P5, the pile-triage path** — a shared name resolver, cost-based castability in
   `screen`, a proportional generic-theme bar, `/add-cards` Stage 0b, and G-58's
   bulk-triage variant. Block: `2026-07-pile-triage-broad-implement.md`.
2. **P6–P8, front-face metadata I** — `suggest` scoped candidates by colour IDENTITY (55
   castable red-pool cards hidden from a mono-red deck); `_primary_type` read the BACK
   face's type (deck 49 reported 26 lands holding 25); `swap --apply` wrote a DFC add as a
   bare unimportable line. Block: `2026-07-front-face-metadata-broad-implement.md`.
3. **FO-1/FO-2, front-face metadata II** — `card-mana.csv` kept only the FRONT cost of a
   MODAL DFC (49 rows; it caused a wrong answer in chat), and `build_gallery.py` had its
   own copy of `_primary_type` with the same bug. `build_mana`'s front-face retry is now
   batched. Block: `2026-07-follow-ons-broad-implement.md`.
4. **G-63** — the class is now a rule, with all four incidents in `docs/gotchas.md`.
5. **Deck work** — 51 Unlock (tier B) and 51a Overdue (tier B, built from scratch) shipped;
   49 Scaleforge refined across four passes; G-62 (blind mill is a CLOCK, not interaction)
   recorded with its permutation proof.

Subcommand count: **33 → 33.**

## 3. The task for the next session

**Pick from §5. There is no blocking item and nothing is half-done.** The highest-value
one is §5.1 (`tier --audit-rationale`'s stay-marker false negative) — it is the oldest open
item, it is measured, and it fired again this cycle in a new way: deck 51's tier block said
"protection reads 3" against a live 4 and the audit reported the deck **clean**, because a
copula between a label and its number hides the figure from the sweep. That is the same
residual from the other side, and it is now costing real accuracy in the decks being built.

## 4. What NOT to do

- **Do not re-weight `cuts`' fit sum.** Simulated across all 64 decks and rejected; also
  structurally forbidden by `tests/test_recommendations.py`.
- **Do not re-propose the P/T creature signal.** Pre-registered, tested, rejected.
- **Do not add a 34th subcommand** without saying what it replaces.
- **Do not trust a gate you have not watched fail** (§8).
- **Do not hand-triage a card pile on the `Color(s)` column.** G-58's bulk-triage variant:
  it mis-binned nine of 111 cards, eight of which were castable. `deck.py screen` is the
  tool and `/add-cards` Stage 0b now requires it above ~10 cards.
- **Do not apply a deck edit without the owner confirming it.** Standing rule, restated
  several times this cycle. Propose with numbers; they decide.
- **`docs/tooling-improvement-plan.md` is HISTORICAL.** Its F01 instructs adding
  `lib.full_card_text`, which was later deleted as dead code.

## 5. Open work, in rough value order

1. **`tier --audit-rationale` false negatives, now two shapes.** (a) The STAY-marker one: a
   `_HISTORY_CUES` change-cue about one card suppresses a citation of ANOTHER card in the
   same ±140-char window even when the clause says that card **stays** (deck 42a asserted
   "Erode stay[s]" after Erode was cut, reported clean). (b) The COPULA one, hit again in
   deck 51 this cycle: a figure joined to its label by a copula or participle ("protection
   reads 3", "the reported 2.57") is invisible to the figure sweep. **Both need a roster
   sweep before landing**, per the cue-list rule — a false positive is noisy and gets
   noticed, a false negative is silent.
2. **`card-mana.csv` cannot distinguish a MODAL DFC from a SPLIT card.** FO-1 made it able
   to tell transform from modal (a transform DFC keeps one cost), but both split and modal
   now render `A // B`. No reader asks the question today; if one ever needs to, the fix is
   a `Layout` column — and note the 4-column header is hardcoded in four writers plus
   INV-03, which is exactly why it was NOT added this cycle.
3. **`doubler_restriction` parses POWER scopes only.** A type-scoped doubler (Splinter's
   Ninja clause) is counted against the whole deck — 27 feeders in deck 20 against a
   correct 12. Read a `✱ multiplier` figure on a tribal doubler as an upper bound. Fix is a
   second scope pattern feeding the same filter, not a second model.
4. **The pool's `Power`/`Toughness` for a two-faced card** is stored the same merged way
   costs were before FO-1. Not investigated — flagged because it is the same shape as the
   whole G-63 class and nothing has looked.
5. **`build_dashboard.py` reaches into `deckmod._primary_type`**, a private name in another
   module, instead of `lib.primary_type`. Harmless today; the reason it is listed is that a
   private cross-module reference is how the duplicate copy survived in the first place.
6. **More ledger data, not another cut signal.** Every subgroup in the recommendation
   ledger is 4–6 rows. A pre-registered re-test at ~100 swaps is the honest next step.
7. Smaller: the reverse `screen` flag (a candidate strictly WORSE than an incumbent);
   ROADMAP Tier 1 (theme the remaining UB flavor mechanics, `scripts/keyword_baseline.txt`).

## 6. Open DECK decisions (the owner's, not yours)

Measured, recorded, and deliberately not applied. Do not act on these unsolicited.

- **Deck 51, the 25th land.** Recorded as a `#~` flex line in the deck file with the full
  measurement. The list stands as is by the owner's call.
- **Deck 51a, the 25th land.** Recommended AGAINST (avg MV 3.14; it wants the spell).
- **Deck 49, Ramos, Dragon Engine.** Recommended against — every available cut worsens the
  curve. If taken: Spinerock Tyrant or Rapacious Dragon.
- **A third unblockable-tempo deck** from deck 51's ~20-card overflow. Recommended as its
  own number **52**, not `51b`.

## 7. Measurements — do not re-derive

Each costs a roster sweep. All current.

- **Cut-ranking agreement**: `_weakest_cut` vs `rank_cut_candidates` **28/64 → 64/64**.
- **Signature-boost saturation**: 87% loose / 66% strict; the generic-theme bar (P3) moved
  4,440 (deck, card) judgements, KEY 13% → 8%, and **every one of the 223 changed labels
  went KEY → weaker**. Nothing gained a KEY.
- **`suggest` vs `suggest-homes`**: 640 picks on 64 decks, **100% agreement** — a
  consequence of the ranking, not a property of the gates.
- **Colour-identity vs printed cost** (G-58/P6): 55 Standard cards in the red pool that an
  identity filter hides from a mono-red deck; 9 of 111 pile cards mis-binned by hand, 8 of
  them castable.
- **Back-face type** (P7): 81 pool cards have a type line whose back face outranks the
  front; 4 decks were live.
- **Modal DFC costs** (FO-1): 100 Arena modal DFCs, 40 with a real cost on both faces, 49
  `card-mana.csv` rows corrected (the extra 9 are library front-name rows).
- **Land math for a 60-card deck**: keepable 82.5 / 84.4 / 86.0 / 87.4% at 23 / 24 / 25 / 26
  lands; at 24, land-drop probability is T3 78.9%, T4 63.2%, T5 46.7%.
- **Costs**: `check_all` 14.8s · full pytest ~36s · `preflight` ~6s · `suggest-homes` ~3s
  per card · no-change `make refresh` ~13s · full `make refresh REFETCH=1` ~5 min (the mana
  re-price is now batched end to end).

## 8. One thing to preserve

**Measure before believing, then check the measurement** — and this cycle adds a second
half: **a fix applied to one definition does not reach a copy of it.**

- Three of the four G-63 bugs were found by building a deck, not by any gate. Eleven gates
  were green throughout.
- `build_gallery.py` kept mis-typing its own breakdown after `deck.py` was fixed, because
  it had its own `_primary_type`. The test now asserts both callers resolve to the **same
  object**, not that they agree today — a same-answer test passes against two copies.
- The "Ojer −Hoarding Dragon → avg MV 4.15" reading that shaped a deck-49 decision was an
  artifact of the type bug. A measurement taken through a broken primitive is not a
  measurement.
- A `--refetch` that "took too long" was not slow: it was rate-limited by doing 700
  single-card GETs. The fix was one batch call, and it was invisible until timed.
