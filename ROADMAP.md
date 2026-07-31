# Roadmap — MTG Arena Card Library

Regenerated 2026-07-31 with `/roadmap`. Grounded in measured state, not wishes.
Effort: S ≈ <2h, M ≈ ½–2 days, L ≈ 3+ days (one dev + Claude Code).

State at regeneration: 1,860 cards · 76 deck files · 33 `deck.py` subcommands ·
767 tests in 16 files · 13 model-sanity gates · `check_all` 14.8s.

## What the last roadmap proposed, and where it went

Stated because a roadmap that never records its own outcomes is a wishlist.

- **Mono-U/colorless affinity deck — BUILT** as deck 47, Grid Overload. The measured
  case (16 artifact-count payoffs, 7 affinity/improvise, Chrome Dome as a real lord) held
  up; the deck exists and is distinct from 26 in the resource it spends.
- **Full-collection import — SHIPPED** as `import_collection.py`. It is the only tool here
  that can set an owned count DOWN, which is why `/ingest` routes by provenance.
- **Match / win-rate tracking — the CODE shipped**, `parse_matches.py` plus `--report`
  with the G-57 restraint. **The data did not**: `matches.csv` does not exist. See Tier 1.
- **Theme the remaining flavor keywords — still open.** Ten in
  `scripts/keyword_baseline.txt`. Carried to Tier 1 again, unchanged.
- **Google Sheets round-trip — still unwired.** The script is complete; what is missing is
  a one-time service-account setup, which is an operator action, not development.

## Tier 1 — Short-term (days–weeks)

1. **Run the pre-registered creature-cut re-test. The threshold is MET.** The handoff said
   "a pre-registered re-test at ~100 swaps is the honest step"; `recommendations.csv` now
   holds exactly **100 swaps, 96 with a usable ranking**. The split replicates at nearly
   double the sample: creature cuts **20/48 (42%)**, noncreature **40/48 (83%)** — against
   45% (n=31) and 90% (n=21) at the last reading. This is no longer a small-sample story,
   and it is the only claim in the repo that has been tested twice. Decide what it means
   before adding anything to the ranking. **(M, ~1 day)**
2. **Fix `tier --audit-rationale`'s two false negatives.** (a) A change-cue about one card
   suppresses a citation of ANOTHER card in the same window even when the clause says that
   card stays. (b) A figure joined to its label by a copula is invisible — which fired
   again this cycle: deck 51 claimed "protection reads 3" against a live 4 and the audit
   reported the deck clean. Needs a roster sweep before landing, per the cue-list rule.
   **(M, ~1 day)**
3. **Log the first real matches.** `matches.csv` does not exist, so the Outcomes subsystem
   — described in the Cycle Workflow Config as one of the only two that has seen reality —
   has seen none. The data is free and already in `Player.log`, the parser is written and
   tested, and until it runs, every tier letter on the roster is graded against internal
   consistency alone. **(S, <2h, and most of it is playing.)**
4. **Theme the remaining unindexed keywords** (Vivid, Job select, Opus, Increment,
   Infusion, Paradigm, Disappear, Tiered, Jump, triple). K-01's rule stands: triage PER
   KEYWORD, never in bulk — `renew` and `triple` went opposite ways. Each unindexed keyword
   is a hole every tag-gated predicate inherits. **(S, ~2h)**
5. **Give `doubler_restriction` a TYPE scope.** It parses a POWER scope and nothing else,
   so a type-scoped doubler is counted against the whole deck — 27 feeders in deck 20
   against a correct 12. A second pattern feeding the same filter, not a second model.
   **(S, ~2h)**

## Tier 2 — Medium-term (weeks–months)

1. **Finish the G-63 sweep across every merged two-faced field.** Cost, colour, type and
   name are each fixed and each was found by accident. `card-pool.csv`'s `Power`/
   `Toughness` for a two-faced card is stored the same merged way costs were before FO-1,
   and nothing has looked. The class is now understood well enough to audit the remaining
   columns deliberately instead of waiting for the next deck to trip over one. **(M)**
2. **Walk the interface regression scenarios with a human at a browser.** Scenarios 5–8
   (light-mode status colours, phone-width layout, keyboard-only traversal, editor failure
   feedback) are the perceptual checks a code read structurally cannot make, and they have
   not been walked in three sessions of heavy tooling change. `tests/test_templates.py`
   pins the markup half; nothing pins the rest. **(M)**
3. **Close the outcome loop once `matches.csv` has rows.** Per-deck win rate against the
   `#: tier:` letter, under the G-57 restraint: no percentage under 20 matches, a Wilson
   interval above it, and a small-sample rate never written into a tier block. This is the
   first thing that could confirm or refute a tier grade from outside the model. **(M)**
4. **Two measured deck builds are queued.** Deck **52**, the unblockable-tempo deck from
   deck 51's ~20-card overflow (its own number, not `51b`). And the **Dinosaur** question —
   per G-59's table it is the only tribe besides Dragon with a real payoff count (52
   bodies / 11 payoffs, against Vampire 69/3 and Mutant 79/2), so it is the one remaining
   tribal archetype that is not body-count theatre. **(M each)**
5. **Wire the Google Sheets round-trip.** The code is done; what remains is a service
   account, the Sheets API, and two environment variables. Listed here rather than dropped
   because a complete script nobody has ever run is indistinguishable from a broken one.
   **(S dev + operator setup)**

## Tier 3 — Long-term (months+)

1. **A grading loop that closes on outcomes, not on itself.** Today `tier` grades a list
   against a metric floor, `cuts` ranks against theme fit, and both are validated by other
   models in the same repo. The ledger showed what external feedback buys: it is the only
   reason anyone knows the cut ranking is a coin flip on creatures. Match data plus the
   ledger together could make the tier rubric's "intangibles" band measurable rather than a
   human override. **(L)**
2. **A deck lifecycle.** 76 deck files and rising, with no retire/archive path — `audit`
   triages which decks need a tune but nothing says which decks are done, dead, or
   superseded by a variant. Rotation makes this worse on a schedule, not gradually. **(M–L)**
3. **Reduce the reconciliation points.** `docs/systems-map.md`'s real deliverable is the
   list of places a human must settle two answers by hand. Each one removed is a class of
   mistake removed — the cut-model unification took one from 28/64 agreement to 64/64.
   Work the list rather than waiting for the next disagreement to surface as a bug. **(L)**

## Tier 4 — Future possibilities (exploratory)

**Field-aware grading.** Every judgement here is internal: does this deck hold together,
can it cast its spells, does it answer things in the abstract. A deck is actually good or
bad against *a field*. Pulling archetype and meta data — even coarsely, "what are the five
decks you will actually face" — would turn the interaction count from a number into a
question with an answer: interaction against *what*. It would also give the tier rubric's
S band, currently defined as "a human call that it is top-meta capable", something to point
at. The risk is obvious and worth naming: meta data ages faster than anything else here,
and a stale meta read is more confidently wrong than no meta read.

**Play telemetry as model validation.** `Player.log` carries far more than match results.
Mulligans taken, the turn each card was first cast, what sat in hand unplayed — all of it
is already on disk. `consistency` predicts keepable 84.4% and a 63.2% chance of four lands
on turn four; nobody has ever checked those predictions against a real game. A telemetry
pass would make the hypergeometric model falsifiable, which is a different and better thing
than making it more sophisticated. It is also the only path that could measure whether the
cost-reduction cards this roster leans on actually reduce the effective curve.

**Rotation as a standing plan rather than an annual surprise.** `rotation_risk` flags a
card, `deck.py rotation` flags a roster, and both answer "what is at risk". Neither answers
"what does this collection look like after rotation, and which decks survive it". A
standing model — decks scored on post-rotation survivability, wildcards steered toward
cards with runway, the wishlist reordered by remaining legal life — would turn the single
most predictable disruption in the format into a planning input. It suits this project
specifically, because the wishlist and budget tooling already exist and only lack a time
axis.

## The strategic bet

**Get real outcome data in, starting with `matches.csv`.**

Everything in this repo is graded against other things in this repo. Tier floors read the
quality vector, the quality vector reads the role classifier, the role classifier reads the
tags, and thirteen gates check that they all agree with each other — which is genuinely
valuable and is exactly why it can be wrong in a way no gate can see.

The one place external feedback exists is `recommendations.csv`, and look what it bought:
at 100 swaps it says the cut ranking sits at **42% on creature cuts**, near a coin flip,
with the mechanism identified (an unnormalized tag-count sum) and the obvious fix already
simulated and rejected. No internal check produced that. A ledger of what a human actually
decided did.

`matches.csv` is the same lever, cheaper, and empty. The data is free — it is already
written to `Player.log`, the parser exists, it is tested, and G-57 already specifies the
restraint for reading a small sample. The gap is that nobody has run it.

Until it has rows, "deck 51 is a B" is a statement about a metric floor and a human
argument, and there is no way to be surprised by it. The whole point of building fifty-one
decks is to play them.
