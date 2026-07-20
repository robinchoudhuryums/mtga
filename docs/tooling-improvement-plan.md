# Tooling Improvement Plan

A structured findings list for `/broad-implement`. Each finding is self-contained:
**why**, **files**, **changes**, and **acceptance**. Implement in the phased order
in **Suggested implementation sequence** at the bottom (not strict ID order) —
later work depends on earlier primitives. Every change must keep
`scripts/check_all.py` green and follow CLAUDE.md's Common Gotchas.

**Design constraints (apply to all findings):**
- Skills **orchestrate the scripts; never reimplement their logic** — the scripts
  stay the single source of truth, so skills can't drift from them.
- Card evaluation reads **complete** oracle text by default (F01). No path may
  truncate a card's text to grade/classify/rank it.
- Do **not** auto-write tier letters — tier is a competitive judgment; prompt a
  human re-grade instead.

---

## F01 — Full-text-by-default in every card-evaluation path

**Why.** Repeated mis-grades came from reading a *sliced* card (a clause hidden by
truncation). `card.py` fixed the chat entry point; this makes full-text the
enforced default everywhere and gives every evaluator one accessor.

**Files.** `scripts/lib.py` (new shared accessor), audit `scripts/deck.py`
(`classify_roles`, `cuts`, `suggest`, `suggest-homes`), `scripts/wishlist.py`
(`_rank_scores`, `_seed_power`, `cmd_suggest_targets`), `scripts/tag_synergies.py`;
`CLAUDE.md`.

**Changes.**
1. Add `lib.full_card_text(name)` → the complete `Card Text` (library then pool),
   never truncated; refactor evaluators to use it.
2. Grep-audit for any text slicing (`Card Text`[:N], `.split(...)[0]` on text,
   `head`-style caps) in evaluation code and remove.
3. `card.py` becomes the mandated pre-grade read; add a one-line CLAUDE.md
   principle: "evaluate a card only from its full text — via `card.py` in chat, via
   `full_card_text()` in code."

**Acceptance.** An audit shows no evaluation path truncates card text; a card whose
key clause is on its *last* line classifies/roles correctly.

---

## F02 — New/unindexed mechanic detector

**Why.** When a set introduces a new keyword/mechanic, it falls through
`tag_synergies.KEYWORD_THEMES` (mis-tagged or missed). Catch it automatically.

**Files.** New `scripts/check_keywords.py`; wire into `scripts/check_all.py` as a
**soft** (non-gating) warning; expose the known-keyword set from
`tag_synergies.py`; `card.py` (surface per-card).

**Changes.**
1. Build the known-keyword set = `KEYWORD_THEMES` keys ∪ `FLAVOR_KEYWORDS`.
2. **Signal A (authoritative):** any keyword in `card-mana.csv`'s Scryfall
   `Keywords` column not in the known set → candidate new mechanic.
3. **Signal B (text-structure heuristic, for keywords Scryfall hasn't tagged):**
   flag ability lines matching a keyword-ability shape — a capitalized word/phrase
   at line start followed by `" — "`, or parenthetical reminder text `"(As this …"`
   — whose lead word isn't a known keyword or English stop-word.
4. Report distinct unknown mechanics with an example card each; soft-warn in
   `check_all`; add a `⚠ unindexed mechanic: <kw>` line to `card.py` output.

**Acceptance.** A synthetic card with a made-up keyword is flagged by both the
standalone check and `check_all`'s soft warning; known keywords produce no
false positives; `check_all` still exits 0 (soft only).

---

## F03 — Land-aware wishlist rating axis

**Why.** The ranking is *theme-fit + power*; lands have no synergy themes, so they
score ~0 fit and rank on an ambiguous "power." Lands need a manabase-value axis.

**Files.** `scripts/wishlist.py` (`_rank_scores`); reuse `deck.py` mana-source
logic.

**Changes.** When a wishlist card is a land, replace the theme-fit axis with a
**manabase-value** score for its target deck: (a) do the colors it produces match
the deck's colors (a WB dual in mono-W is half-dead)? (b) does the deck *need* that
fixing — cross-reference `deck.py mana` source counts vs pip demand (short on a
color the land makes → high)? (c) untapped/fixing quality (untapped > tapland >
gainland-tapland). Blend with `Power` as today; keep the `combined` scale so
`--budget` and the ranking gate stay valid.

**Acceptance.** A dual in a matching 2-color deck short on one of its colors ranks
high; the same dual targeted at a mono-color deck ranks low; `check_rankings.py`
still passes.

---

## F04 — Fit-strength labels (KEY / role-player / tangential)

**Why.** When a card lists multiple deck fits, nothing differentiates a *key* fit
from a *tangential* one.

**Files.** `scripts/deck.py` (`suggest-homes`, `suggest`); `scripts/wishlist.py`
(reuse in `--rank`/`--suggest-targets` output where a home is shown).

**Changes.** For each card→deck fit, classify strength: **KEY** (shares the deck's
*most-central* theme, or fills a named gap the deck is short on — interaction /
card advantage), **role-player** (a central but secondary theme), **tangential**
(only generic / one-off overlap). Surface the label in the per-deck fit rows.

**Acceptance.** A food card → Gastromancer = KEY; a removal spell → an
interaction-light deck = KEY; a generic-etb card → a broad deck = tangential.

---

## F05 — Shared `preflight` verification primitive

**Why.** Every change ends with the same checks; the skills need one call.

**Files.** `scripts/deck.py` (new `preflight <id>` subcommand — distinct from the
existing Arena-drift `verify`).

**Changes.** `deck.py preflight <id>` runs legal + owned/buildable + castability +
a `check_all` pass and returns a compact structured PASS/FAIL block the skills can
parse.

**Acceptance.** `deck.py preflight 19` reports legal/owned/castable/integrity in
one structured block; non-zero exit on any hard failure.

---

## F06 — Skill: `add-cards` (systematic owned-card intake)

**Why.** Codifies the reconcile-and-fit-check loop repeated ~10× per session.

**Files.** `.claude/commands/add-cards.md`.

**Changes.** Pipeline: parse an Arena export of newly-owned cards →
`reconcile_crafts.py --apply` → `build_gallery.py` → prune reconciled rows from the
wishlist + re-home drift (`wishlist.py --audit-targets`) → **per card:** `card.py`
(full text + legality; heed F02 unindexed-mechanic flags) + `deck.py suggest-homes`
with F04 strength labels → classify each real fit as **key upgrade / sidegrade /
different-flavor** with a cut candidate → `deck.py preflight` on touched decks →
**structured report** (cataloged N; per-card fits: card→deck (strength) + cut
candidate) → standardized commit (F08). Orchestrates scripts only.

**Acceptance.** Pasting an owned-cards export runs the whole pipeline and emits the
structured report; no logic duplicated from the scripts.

---

## F07 — Skill: `apply-changes` (systematic swap application)

**Why.** Codifies the swap→flex→wishlist→verify→commit loop repeated ~15× per session.

**Files.** `.claude/commands/apply-changes.md`.

**Changes.** Pipeline: parse swaps (from a `/tune-deck` result block or chat as
`−cut / +add`) → per swap `deck.py swap --apply` (auto-retires stale flex lines;
INV-04 recheck) → if an *add* is unowned: wishlist it (Target = this deck, F03/F04
aware) or flag craft; if a *cut* frees a card used nowhere else, note it → reconcile
any now-owned adds and prune them from the wishlist → `deck.py preflight` →
**structured report** (swaps, wildcard cost, interaction/curve deltas, wishlist
changes, tier-before/after with a *prompt* to re-grade, verification) →
standardized commit (F08). Orchestrates scripts only.

**Acceptance (live test case).** Validate against the **Bird Brain (deck 19)
B-tier package** held over from this session: `+Crib Swap / +Stroke of Midnight /
+Dazzling Denial / +Bushwhack`, cutting `Season of Gathering / The Legend of
Kyoshi / Rydia's Return / Cat-Owl`. The skill must: apply all four swaps, keep flex
+ wishlist in sync, run the F10 quality guard (which should CONFIRM the change is a
net improvement — interaction 1→~5, curve smoothed, no central theme lost, still
legal/owned), emit the structured report, prompt a tier re-grade (C→B), and commit
per F08. Do NOT apply this package by hand beforehand — it is the acceptance run.

---

## F08 — Standardized verify+commit tail (shared by F06/F07)

**Why.** The avoidable mistakes live here (model-ID in a commit, skipped
`check_all`, stale flex note).

**Files.** A shared snippet/section referenced by `add-cards.md` and
`apply-changes.md`.

**Changes.** Encode the tail once: `check_all` must pass first; commit message ends
with the Co-Authored-By + Claude-Session lines and **never** contains the model ID;
push to the working branch; if the branch's PR is already merged, restart from
`main` per CLAUDE.md.

**Acceptance.** Both skills reference the same tail; a dry-run shows the exact
commit discipline.

---

## F09 — Docs sync

**Why.** Keep CLAUDE.md/README from drifting from the new tools/skills.

**Files.** `CLAUDE.md`, `README.md`.

**Changes.** Document: the full-text-by-default principle (F01), the
unindexed-mechanic detector (F02), the land rating (F03) and fit-strength labels
(F04), `deck.py preflight` (F05), and the two skills (F06/F07). Add `card.py`,
`check_keywords.py` to the Subsystems lists. Note `check_all`'s new soft warning.

**Acceptance.** `sync-docs` finds no remaining drift for these features.

---

## F10 — Deck-quality regression guard (self-check on cuts/swaps)

**Why.** A suggested cut/swap may not be the best option — or may *worsen* the
deck. The skills (and `/tune-deck`) should self-catch a net-negative change instead
of trusting the suggestion blindly.

**Files.** `scripts/deck.py` (new `quality <id>` snapshot + a before/after diff
mode, reusing `audit_deck` / `stats` / `mana` / `cuts` primitives); consumed by
F07 `apply-changes` and F06 `add-cards`, and referenced by `/tune-deck`.

**Changes.** Compute a **deck-quality vector** from existing primitives — buildable
(owned+legal), castability strays, interaction count, curve health (avg MV +
early-drop count), central-theme coverage, and the functional-role vector
(removal / card advantage / ramp / payoff …). Snapshot it before a change and again
after, then **flag regressions**:
1. **Axis regression** — any key axis got worse past a threshold (interaction
   dropped, castability broke, a central theme lost its last copy, curve worsened)
   with no compensating gain → warn with the specific axis.
2. **Wrong-cut check** — re-run `cuts` on the pre-change deck; if a swap removed a
   card that ranks *above* cards it kept (you cut something better than what
   remains), warn.
3. **Weak-add check** — the added card's F04 fit-strength must be ≥ role-player;
   an added **tangential**/off-theme card warns.
It is a **soft guard** — it flags, it does not block (some regressions are
intentional trades). Output a compact "quality delta" block the skills surface.

**Acceptance.** A swap that drops interaction with no offsetting gain, cuts a
higher-ranked card than it keeps, or adds a tangential card → the guard warns with
the specific reason; a genuine upgrade (e.g. the Bird Brain package) → "net
improvement, no regressions."

---

## F11 — Optimize unowned-card search (date-aware legality + pre-filter)

**Why.** Scanning the ~15.8k-card pool for build/tune targets is heavy, and the
pool's `Legalities` is a **build-time snapshot** — Standard rotates on a schedule,
so stale entries waste the search and risk recommending a rotated-out card.

**Files.** `scripts/build_pool.py` (capture set release/rotation info), a small
set→rotation table (or derive from Scryfall via `scripts/scryfall.py`),
`scripts/deck.py` (`suggest`), `scripts/pool.py`. Python may read the real date
(`datetime.date.today()`).

**Changes.**
1. **Date-aware Standard legality.** Layer a rotation check over the pool's static
   `Legalities`: given today's date and a set→in-Standard-until table, treat a card
   as Standard only if its set is *currently* in Standard; **flag** cards whose set
   has rotated (or rotates within ~3 months) even if the stale pool still marks them
   `standard`. `suggest`/`pool --legal standard` default to currently-legal.
2. **Pre-filter the search space.** Before the expensive text/theme scoring, prune
   the pool to candidates that pass color (identity ⊆ deck colors) + format +
   date-legality — so scoring runs on a small set, not all ~15.8k. Optionally cache
   a pre-indexed pool (by color/format/theme) for repeated queries.

**Acceptance.** `suggest` on a deck never recommends a rotated-out card and flags
rotates-soon; the candidate set is pruned by color+format+date before theme
scoring (measurably fewer cards scored); results match the old scoring on the
surviving candidates.

---

## F12 — Tier robustness (ground + verify the competitive tier)

**Why.** The `#: tier:` letter drives a lot of downstream judgment (audit sort,
dashboard, which decks get tuned, how a swap is weighed), yet it was the one
most-trusted signal with **no verifier** — free text nothing checks, graded from
prose rationales rather than a rubric, and silently stale after a tune. The risk
the user named: "so many decisions are made according to your evaluation of decks
and the tiering system."

**Files.** `CLAUDE.md` (a documented tier **rubric**); `scripts/deck.py` (`tier_band`
/ `tier_consistency` / `tier_consistency_issues` + a `tier <id>` subcommand);
`scripts/check_all.py` (soft, non-gating roster warning); `README.md`.

**Changes.**
1. **Rubric (A).** Define S/A/B/C/D as bands over the measurable quality vector
   (`deck_quality_vector`) — interaction + card-advantage (resilience axis),
   castability, curve, theme density — with the intangibles (bombs, protection,
   proven closing speed, meta) moving a deck *within* a band. Tier rates the LIST's
   power, **independent of ownership** (build-state is tracked by `check`/`audit`);
   never auto-assigned.
2. **Guard (B).** `tier_band(vec)` → the tier FLOOR the metrics support (blind to
   bombs/meta, so it under-rates by design). `deck.py tier <id>` shows claimed-vs-
   floor and flags a **mismatch** when the letter is ≥2 bands above the floor
   (indefensible/stale) or possibly under-graded (claimed below the under-rating
   floor). A one-band-over letter is fine (intangibles credit). Never writes the
   letter.
3. **Roster check (C).** `tier_consistency_issues()` folds into `check_all` as a
   soft, non-gating warning, so an inflated/stale tier can't hide. The
   `/apply-changes` skill runs `tier` after an edit so a tune re-grounds the letter.

**Acceptance.** The guard is quiet across a well-tiered roster (0 false positives),
fires when a letter is set ≥2 bands above its metrics floor, treats an aspirational
unbuilt list on its power (not its ownership), and `check_all` stays green (soft
only). *(Implemented and calibrated against the live 44-deck roster: 0 mismatches
today; fires on a simulated inflation.)*

## F13 — Unify the interaction / card-advantage counters (found via F12)

**Why.** Running the F12 tier pass across the roster exposed that **three separate
implementations counted "interaction"** and disagreed by ±1 on several decks:
`deck_role_counts` (quality/tier vector — line-count, skipped only basics),
`_interaction_count` (audit — quantity-weighted, skipped nonbasic lands), and
`cmd_stats`' "interaction total" (quantity-weighted *sum of buckets*, double-counting
a modal removal+counter card). At a band boundary the tier floor could hinge on a
number the user couldn't reproduce in `stats` — undermining F12's premise. Deck 30
was mis-served: a nonbasic **land that pings** was counted as removal, inflating its
interaction to 3 (the human's own rationale said "only 2"), which hid that its A
claim sits 2 bands above the true floor.

**Files.** `scripts/deck.py` (`role_tally`, `deck_role_counts`, `_interaction_count`,
`cmd_stats`).

**Changes.** One canonical `role_tally(cards, carddata)` all three route through —
quantity-weighted, a card counted ONCE toward interaction regardless of how many
interaction roles it fills, basics **and** nonbasic lands skipped. `cmd_stats` shows
the once-per-card "interaction total (distinct removal/sweeper/counter cards)".

**Acceptance.** All three counters agree on every deck (verified: 0 drift across 44
decks); `stats`' interaction total equals the audit `Int` column equals the tier/
quality vector; `check_all` green. *(Implemented; the unification also resolved false
"under-graded" flags on decks 22 and 28a whose counts now match their rationales.)*

## F14 — Tier-gap diagnostic (the mechanical half of "get to the next tier")

**Why.** "What would it take to move deck N up a tier" was a hands-on synthesis
(done for deck 30). The *diagnostic* half is deterministic and should be codified;
the *selection* half (which cards preserve the engine/identity, is the trade worth
it) stays a `/tune-deck` judgment call — automating it would reintroduce the
graded-from-a-label failure mode.

**Files.** `scripts/deck.py` (`tier_gap`, `owned_role_fillers`, `tier <id> --to
TIER`); `.claude/commands/tune-deck.md` (consume it); `README.md`.

**Changes.**
1. `tier_gap(vec, target)` — the exact axis shortfall to reach a target band's
   FLOOR (from the same `tier_band` thresholds): `+N interaction`, `+N card
   advantage`, and any uncastable strays to clear. Blind to bombs/meta, so it
   reports the measurable floor gap, not the A-vs-S judgment.
2. `owned_role_fillers(d, roles, …)` — owned, on-color cards NOT already in the
   deck that fill the short axis (interaction / card advantage), cheapest first —
   the 0-wildcard fillers that close the gap. Pairs with `cuts` for room.
3. `deck.py tier <id> --to A` prints the gap + the fillers + weakest cut
   candidates. `/tune-deck` runs it so a tune aims at a concrete tier target
   ("close +3 interaction") instead of generic improvement.

**Acceptance.** `deck.py tier 30 --to A` reports "+3 interaction" and surfaces
owned GUR removal/counters; the numbers match the tier_band thresholds; the
selection stays a human call. `check_all` green.

## F15 — Classifier coverage self-audit (surface silent under-counts)

**Why.** The role classifier (`classify_roles`) is precise regexes, so it inevitably
misses phrasings and silently UNDER-counts — the recurring failure that only a
hands-on read caught (a creature-ETB kill, an edict, a `-X/-X`, a bounce, "exile up
to one target"). The count then feeds `stats` / `audit` / `quality` / `tier`, so a
miss quietly drags a grade down.

**Files.** `scripts/deck.py` (`role_coverage_flags`, broadened `_ROLE_PATTERNS`,
`cmd_stats` / `cmd_tier` surfacing); `README.md`, `CLAUDE.md`.

**Changes (two parts, same philosophy as F02/the tier guard — keep the precise thing
precise, make the blind spot visible).**
1. **Visibility:** `role_coverage_flags(cards, carddata)` — broad, high-recall
   lexical cues (`_INT_CUES` / `_CA_CUES`) for "this text interacts / draws cards";
   when a cue fires but the precise classifier tagged NO matching role, flag the card
   for a human verify (never silently change a count). Surfaced in `deck.py stats`
   (a "⚠ Possible UNDER-COUNT" list + the count of unclassified noncreature spells)
   and `deck.py tier` (a compact pointer, since the floor grades on the count).
2. **Fix the common misses the flag surfaced:** broadened `_ROLE_PATTERNS` for the
   unambiguous high-frequency templates — any `fight`, `destroy/exile up to N target`,
   `-N/-N` / `-X/-X` shrink, and one-sided minus-wraths ("creatures your opponents
   control get -2/-2"). Cut the flag volume ~in half (84→42 residual, genuinely-
   ambiguous cards left for review) and correctly counts cards like Massacre Wurm,
   Mutant Chain Reaction, She-Hulk, Cloud of Darkness.

**Acceptance.** The previously-missed cards now classify as interaction; `stats`/`tier`
print a verify list for the residual ambiguous cards; no new tier mismatch and
`check_all` green. *(Side effect: the more-accurate counts raised interaction on ~12
decks, several now measuring a band higher — re-grade candidates, not auto-applied.)*

## Suggested implementation sequence

Phased, so each wave builds on stable primitives and can be validated before the
next. `/broad-implement` one phase at a time.

**Phase 1 — principles & standalone tooling (low-risk, no dependencies).**
`F01` (full-text default) → `F02` (unindexed-mechanic detector) → `F11` (search
optimization: date-legality + pre-filter). All are self-contained script changes
that also make later work cheaper and safer.

**Phase 2 — rating & verification primitives (the shared building blocks).**
`F03` (land-aware rating) → `F04` (fit-strength labels) → `F05` (`preflight`) →
`F10` (quality-regression guard). These are the primitives the skills call; land
them and their gates (`check_rankings`) before building on top.

**Phase 3 — the skills (orchestration only).**
`F06` (`add-cards`) → `F07` (`apply-changes`). Build `add-cards` first (highest-
frequency loop; exercises F04/F11), then `apply-changes`. **Validate `F07` with the
Bird Brain B-tier package** as its live acceptance run (see F07), confirming the
F10 guard reports a net improvement and the tier re-grade prompt fires (C→B).

**Phase 4 — glue & docs.**
`F08` (verify+commit tail, folded into the skills) → `F09` (docs sync). Do F09 last
so it documents the final shape of everything above.
