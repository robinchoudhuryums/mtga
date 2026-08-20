# Roadmap — MTG Arena Card Library

Regenerated 2026-08-19 with `/roadmap`. Grounded in measured state, not wishes.
Effort: S ≈ <2h, M ≈ ½–2 days, L ≈ 3+ days (one dev + Claude Code).

State at regeneration: **2,368 library printings** · 16,067 pool rows · **113 deck files**
(111 roster-counted, numbered through 74) · 34 `deck.py` subcommands · 14 model-sanity
gates · **1,3xx tests in 30 files** · `check_all` green with ZERO soft warnings.

Two figures do most of the work below:

- **Tier spread: A 39 / B 65 / C 3 / ungraded 3 — of which 51 are PROVISIONAL.** Every one
  says the same thing in its file: unplayed. That count has GROWN (41 → 51) since the last
  roadmap, because decks are being added faster than they are being played.
- **`matches.csv` holds 15 matches**, 14 attributed to a deck; `--report` refuses a
  percentage under 20. The best per-deck row is n=4 against a floor of 20.
- Buildability: 66 decks fully owned, 45 craft-gated. Rotation exposure: **171**
  card-instances ~2026, 693 ~2027, 1,715 ~2028.

---

## What the last roadmap proposed, and where it went

Stated because a roadmap that never records its own outcomes is a wishlist.

- **Tier 1.1 — sync G-04/G-26/G-67 to the docs — DONE**, and then done twice more. Three
  `/sync-docs` passes have landed since; G-67 in particular has been re-grounded three
  times as its residual moved from "nine holes" to "the taxonomy question" to "closed, and
  here is the new one".
- **Tier 1.2 — the 7 stale flex lines and 12 stale note figures — DONE.** `check_all` now
  reports ZERO soft warnings, which is the first time that has been true across a full
  cycle.
- **Tier 1.3 — `import_collection.py` against a tracker export — STILL NOT DONE**, and it
  has now been top of the handoff for FOUR cycles. This is the honest failure of the last
  roadmap: it is 30 minutes of work, it is the premise under every craft recommendation,
  and it is blocked on an export only the owner can produce. Re-listed below, unchanged.
- **Tier 1.4 — the launchd log archive — STILL NOT DONE**, same reason, and it is still the
  one item with a real deadline: `Player.log` is overwritten on every Arena launch.
- **Tier 1.5 — re-grade the flagged decks — DONE.** The tier guard reports nothing today.
- **Tier 2.5 — regenerate `docs/systems-map.md` — NOT DONE**, and it has aged further: it
  is measured against 64 decks and 1,853 cards against a live 111 and 2,368.
- **Tier 3.4 — close the classifier gap — SUBSTANTIALLY ADVANCED, by a route this file did
  not predict.** It estimated "L, 1–2mo" for a structural fix. What actually worked was
  cheaper and different: nineteen whitelist holes closed across 2026-08, the last four by
  reading the POOL corpus-wide rather than waiting for a human to notice a card, plus a
  standing disagreement gate (`check_roles --tags`) that watches the two models for
  divergence. The blind spot is now 474 baselined zero-role cards and a 138-entry
  disagreement worklist — bigger numbers, but both are now *instrumented* rather than
  unknown, and the last three holes were found by a sweep rather than by accident.

## Tier 1 — Short-term (days–weeks)

1. **Run `import_collection.py` against a full tracker export.** Top of the handoff for
   FOUR cycles now, and re-listed unchanged because nothing about it has been invalidated —
   only deferred. Ownership counts were wrong five times on 2026-08-09 and roughly ten more
   times across 2026-08-16..19, every one caught because the owner said "I actually have
   N", never by a gate. It is the premise under every craft recommendation and it should
   precede any wildcard spend (G-10). **The reason it keeps slipping is worth naming: it is
   the only Tier 1 item that cannot be done by the tooling at all.** — **S, ~30m +
   operator export**
2. **Install the launchd log archive.** The one item with a DEADLINE: `Player.log` is
   overwritten on every Arena launch, so every unextracted session is lost permanently —
   the 2026-07-27 match already is. Written but unverified on the owner's machine (this
   container is Linux; `launchctl` is untestable from it). Verify with
   `~/mtga-logs/snapshot.sh && wc -l ~/mtga-logs/arena.log`. — **S, ~30m, operator-only**
3. **Make the keep/cut calls in `.cycle/prune-analysis.md`.** The roster is 111 decks
   against Arena's 100-deck cap, so some decks in this repo cannot exist in the client at
   all. The analysis is finished and committed — card-overlap matrix, `similar` sweep,
   three-tier candidate list — and blocked on judgment, not work. — **S, ~2h once decided**
4. **Read down the 138-entry disagreement worklist.** New this cycle: `check_roles --tags`
   now lists every pool card the tagger calls `removal` while the classifier scores no
   interaction role. The known-legitimate classes are graveyard hate (the tagger's
   `"exile target"` substring) and self-shrinks. What is left is the next batch of
   whitelist holes, pre-sorted — the first one found after the gate was built (the `+N/-M`
   lethal-shrink family) came straight off it. — **S/M, 2–4h**
5. **Two outstanding operator VISUAL checks.** Regression Scenario 5's light-mode leg for
   the dashboard's deck-tab colour bars and the gallery palette (which no person has ever
   rendered), and Scenario 7's keyboard walk across all three card-preview surfaces. Both
   guard fixes that shipped un-eyeballed. — **S, ~30m, operator-only**

## Tier 2 — Medium-term (weeks–months)

1. **Get 3–4 decks past 20 matches.** Unchanged from the last roadmap and still the item
   everything in Tier 3 is gated on. It has moved backwards in relative terms: matches went
   9 → 15 while PROVISIONAL decks went 41 → 51, so the roster is outrunning the record.
   **The arithmetic will not resolve itself** — at 111 decks a per-deck read of 20 is
   unreachable by play volume alone, which is why item 2 below now sits beside it rather
   than waiting behind it. — **M, owner-paced**
2. **Aggregate outcomes at a unit the sample can support.** New this cycle, and the honest
   response to item 1's arithmetic. Per-deck at n=4 will not become readable; per COLOUR
   PAIR, per `#: plan:` or per swap-batch would put a dozen matches behind each row instead
   of two. The restraint machinery already exists — `_MIN_SAMPLE`, Wilson intervals, and a
   pooled read that names the different question it answers — so this is a grouping key,
   not new statistics. — **M, 2–3d**
3. **The October rotation pass.** 171 card-instances rotate ~2026 across 83 decks. Deck 28's
   flex block is the worked pattern (successors pre-named for its owned rotating cards);
   deck 28a has never had the pass. — **M, 3–5d**
4. **An ownership FRESHNESS signal.** New this cycle, and the structural half of Tier 1.1:
   a stamp recording when `import_collection.py` last ran, surfaced as an age warning on
   the three surfaces that spend wildcards (`wildcards`, `wishlist --budget`, `tier --to`).
   It cannot make the data correct, but it makes the premise VISIBLE — the same move
   `card-pool.build` already makes for pool staleness, and the reason a four-cycle-old
   deferral is currently invisible at the point of decision. — **S/M, 1d**
5. **Regenerate `docs/systems-map.md`.** Measured 2026-07-29 against 64 decks and 1,853
   cards; the roster is now 111 and 2,368. Its reconciliation-point inventory — every place
   a human must settle two answers by hand — is the most load-bearing doc in the repo and
   is aging on stale figures. Its measured agreement RATES are the part most at risk: this
   repo's own G-07/G-31 lessons are that those saturate as the roster grows. — **S/M, 1–2d**
6. **A "both sides" meta-gate.** Carried forward. Two 2026-08-11 bugs shared one shape (a
   check that read only one half of a symmetric structure), and BS6-03 was a third: focus
   listeners on 2 of 3 call sites. A gate asserting symmetric structures are checked
   symmetrically would catch the next one — found in the AST, not in a hand-kept registry,
   because a registry cannot see what nobody added to it. — **M, 3–5d**

## Tier 3 — Long-term (months+)

1. **Outcome-driven tiering.** The floor is `interaction + card-advantage` from a heuristic
   classifier that is measurably blind — nineteen holes closed in 2026-08 alone, the last
   being blue's entire neutralization suite. Once volume exists, a Wilson-interval win rate
   becomes a SECOND axis the floor can be validated against, and the 51-deck PROVISIONAL
   backlog resolves as a consequence rather than as a grading chore. — **L, 2–3mo, gated
   on Tier 2.1/2.2**
2. **Roster consolidation.** 111 files against Arena's 100-deck cap, and `similar` already
   names the closest pairs. Every roster-wide sweep, rotation pass and doc regeneration
   scales with this number, so a merge/retire pass buys time back on all of them. Note this
   is the LONG-TERM version of Tier 1.3: the immediate cap problem needs a decision, the
   structural version needs a policy for what earns a deck file. — **L, 2–4wk**
3. **A rotation-aware deck lifecycle.** Rotation is a flag on craft views plus hand-written
   flex successors. With 693 card-instances rotating ~2027, the natural step is a
   first-class "deck after the next rotation" view — computed rather than annotated — so a
   deck's remaining Standard life is a property you can sort on. — **L, 3–4wk**
4. **Close the classifier gap structurally.** Downgraded in urgency, and the reason is a
   result rather than a decision: the cheap route worked. Nineteen holes closed by reading
   corpora, plus a standing disagreement gate, moved this from "unknown blind spot" to
   "474 baselined zero-role cards and a 138-entry worklist, both instrumented". The
   structural version — a classifier that is not a phrase whitelist — is still the only
   thing that RETIRES the problem, but it is no longer the only thing that shrinks it.
   — **L, 1–2mo**

## Tier 4 — Future possibilities (exploratory)

**Play-log-driven deck evolution.** The match parser already recovers which deck was played
and when. With volume, the interesting object stops being a win rate and becomes the *diff
between what a deck is and what it does*: which cards sat in hand at concession, which never
got cast, which decks lose to a specific matchup rather than to variance. That reframes the
whole toolchain from "is this list coherent" — which every model here currently
approximates — to "which card in this list is dead weight in practice." It is the only
direction that could retire a heuristic rather than adding another.

**A judgment ledger.** `recommendations.csv` already records where `cuts` ranked each card
cut and whether `suggest` surfaced the add, captured against the pre-swap deck, and
`deck.py feedback` leads with the DISAGREEMENTS because agreements are contaminated by the
shortlist's own influence. Extended over a few hundred more decisions, that is a calibration
dataset for the heuristics themselves: which flags get overruled, and how often the tool was
right when it was. The repo already treats a refuted hypothesis as a result worth committing
(two `cuts` fixes pre-registered and rejected); this would make that systematic instead of
incidental.

**Format-agnostic collection reasoning.** Everything is Standard-shaped today, with Brawl
bolted on through `normalize_format` and its inverted labels. The pool carries full legality
data across 16,067 rows and the collection is 2,368 printings. A genuinely format-neutral
layer — "what is the best Historic deck in this collection that I have not built" — asks a
different question than any current command, and the data to answer it is already on disk.
The 100-card Historic Brawl build already queued (seed 35a with Terra as commander, who
casts for `{1}{R}{G}` while carrying a five-colour identity) is the smallest version of this.

---

## The strategic bet

**Get match volume on a handful of decks (Tier 2.2).**

This project has built an unusually rigorous internal-consistency machine: 14 gates, 1,362
tests, agreement checks between duplicate implementations of the same question, mutation
testing that proves a gate would fail if its model broke, and a documented incident behind
nearly every rule. That machinery is genuinely excellent — and it validates the tooling
against *itself*.

What it cannot do is tell you whether an A is an A. **51 of 111 decks carry PROVISIONAL
tiers**, and each file gives the same reason: unplayed. Every item in Tier 3 —
outcome-driven tiering, lifecycle modelling, closing the classifier gap — is gated on having
outcomes to check against.

The 2026-08-11 session is the argument in miniature. A one-mana sorcery that kills almost
anything scored zero functional roles, `cuts` therefore ranked it its deck's *weakest* card,
and the error surfaced only because a human playing the deck said so. No gate could have
caught it: every gate verifies that the models agree with each other, and they did.

The cost is low and falling. The pipeline runs end to end, deck attribution resolves,
`--report` is built and waiting behind its own restraint threshold. The blocker is 30
minutes of operator setup (Tier 1.2, the one item with a deadline attached) and then games.
That is the cheapest available conversion of "well-engineered" into "known correct."

**One thing has changed since the last roadmap made this same bet, and it sharpens it.**
Matches went 9 → 15 while PROVISIONAL decks went 41 → 51. Play volume is not merely low, it
is losing ground to deck creation — so "get 3–4 decks past 20" is no longer a matter of
waiting. At 111 decks the per-deck denominator is unreachable by play alone, which is why
Tier 2.2 (aggregate at a coarser unit) is now listed BESIDE the bet rather than behind it:
it is the version of this bet that the available sample can actually pay off.

**And the cycle produced a second-order argument for it.** Nineteen classifier holes were
closed in 2026-08, several of them cards the models had graded confidently and wrongly for
months. Every one was found by reading — a human reading a card, or a sweep reading a
corpus — and none by a gate, because the gates verify that the models agree with each
other and they did agree. Outcomes are the only input this project does not already
generate for itself.
