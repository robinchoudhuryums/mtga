# Roadmap — MTG Arena Card Library

Regenerated 2026-08-11 with `/roadmap`. Grounded in measured state, not wishes.
Effort: S ≈ <2h, M ≈ ½–2 days, L ≈ 3+ days (one dev + Claude Code).

State at regeneration: **2,186 library printings** · 16,071 pool rows · **103 deck files**
(numbered through 68) · 34 `deck.py` subcommands · 14 model-sanity gates · **1,253 tests in
29 files** · `check_all` green with 1 soft warning.

Two figures do most of the work below:

- **Tier spread: A 38 / B 56 / C 3 / ungraded 3 — of which 41 are PROVISIONAL.** Every one
  says the same thing in its file: unplayed.
- **`matches.csv` holds 9 matches, 8 attributed to a deck.** `--report` refuses a
  percentage under 20.
- Buildability: 68 decks fully owned, 35 craft-gated. Rotation exposure: **157**
  card-instances ~2026, 596 ~2027, 1,608 ~2028.

---

## What the last roadmap proposed, and where it went

Stated because a roadmap that never records its own outcomes is a wishlist.

- **Match / win-rate tracking — the DATA now exists.** The previous entry read "the CODE
  shipped, the data did not; `matches.csv` does not exist." It exists: 9 matches, 8
  attributed, the pipeline run end to end against a real `Player.log`. Two things it
  settled the hard way — `courseId` is the AVATAR cosmetic, not the deck (nine rows were
  recorded against it before anyone read the values), and the real deck is in
  `EventSetDeckV3`. Still far under the read floor; see Tier 2.
- **Google Sheets round-trip — unchanged.** The dev half is done (`sheets_sync.py check`
  names every missing part and writes nothing). The one-time service-account setup is an
  operator action and has not been taken.
- **The creature cut-ranking hypothesis — TESTED, REJECTED**, and the negative result is
  kept in `docs/systems-map.md` §7 with its sign test. Two pre-registered fixes for `cuts`
  have now been refuted; G-09 says do not derive a third from the tag-count asymmetry.
- **Deck 49 Big Draco rotation-proofing — measured, NOT applied.** Queued at the user's
  request, not rejected. Do not re-derive it; the five swaps are in `.cycle/NEXT-SESSION.md`.
- **This file's own staleness header — resolved by this regeneration.** It had been a
  2026-07-31 snapshot through two full scan cycles.

---

## Tier 1 — Short-term (days–weeks)

1. **Sync G-04 / G-26 / G-67 to the docs.** The 2026-08-11 broad-implement changed what
   three rules claim: G-04 now covers BOTH halves of a flex line, G-26's prefix-collision
   residual is closed, G-67 gained the target-first variable-damage hole. CLAUDE.md and
   `docs/gotchas.md` still describe pre-fix behaviour, and `check_docs.py` gates the anchor
   link, not the prose. — **S, ~1h**
2. **Clear the 7 stale flex lines and 12 stale note figures.** Both sets were surfaced by
   the same session and sit as a soft warning; deck 26a has a literally duplicated line.
   Editorial rather than tooling — G-04 makes retiring a flex line a human call. — **S, ~1h**
3. **Run `import_collection.py` against a full tracker export.** Top of the handoff for two
   cycles. Five ownership counts were wrong on 2026-08-09, each caught only because the
   user said "I actually have N", one of them load-bearing in a recommendation. Nothing in
   the toolchain detects this, and it should precede any wildcard spend (G-10). — **S,
   ~30m + operator**
4. **Install the launchd log archive.** The one item with a DEADLINE: `Player.log` is
   overwritten on every Arena launch, so every unextracted session is lost permanently —
   the 2026-07-27 match already is, and no tooling can recover its deck. Written but
   unverified on the user's machine (this container is Linux; `launchctl` is untestable
   from it). Verify with `~/mtga-logs/snapshot.sh && wc -l ~/mtga-logs/arena.log`. — **S,
   ~30m, operator-only**
5. **Re-grade the decks the tier guard flags as under-graded.** Deck 19 is the named case —
   metrics floor A, letter B, both sides recorded in the file. Letters are never
   auto-written (design constraint), so this is a bounded human pass. — **S, ~1h**

## Tier 2 — Medium-term (weeks–months)

1. **A "both sides" meta-gate.** 2026-08-11 produced two bugs of one shape in one session:
   `rationale_staleness` masked only the cards the deck RUNS (so an absent card's fragment
   resolved to a different card), and `flex_staleness` checked only the `-Out` half of a
   two-sided line. G-27 (read `#: tier:` but not `#: archetype:`), BS4-07 and G-63's header
   consumers are the same class. A gate asserting that symmetric structures are checked
   symmetrically would catch the next one — and `check_dfc`'s lesson applies: find them in
   the AST, not in a hand-maintained registry, because a registry cannot see what nobody
   added to it. — **M, 3–5d**
2. **Get 3–4 decks past 20 matches.** This is the only work that converts the roster from
   internally-consistent to *validated*, and it is what unblocks most of Tier 3. The
   pipeline runs end to end, deck attribution resolves through `EventSetDeckV3`, and
   `--report` is built and waiting behind its restraint threshold. — **M, owner-paced**
3. **The October rotation pass.** 157 card-instances rotate ~2026 across 20+ decks. Deck
   28's flex block is the worked pattern (successors pre-named for its six owned rotating
   cards); deck 28a has never had the pass; deck 36 loses Kutzil with no safe replacement
   for his "opponents can't cast spells during your turn" half. — **M, 3–5d**
4. **Finish Fix 4 — `#~ note:` staleness — properly.** Measured and deliberately declined
   on 2026-08-11: a card scan fires on 252 citations across 51 decks of 537 note lines (a
   flex note's job is to discuss cards NOT in the deck), and a figure scan fires 47 times,
   28 of them arrow/delta form. The narrow variant yields 16 hits, 12 contradicting the
   live vector, but at least two are cue-gaps rather than staleness. The terrain is mapped;
   what it needs is a delta-form suppression and additional history verbs, iterated against
   537 lines. **Note the honest limit: the failure that motivated the finding — a note
   asserting "the deck has FOUR cyclers" — is neither a card name nor a tracked vector key,
   so no version of this check catches it.** — **M, 2–3d**
5. **Regenerate `docs/systems-map.md`.** Measured 2026-07-29 against 64 decks and 1,853
   cards; the roster is now 103 and 2,186, and five subcommands have landed since. Its
   reconciliation-point inventory — every place a human must settle two answers by hand —
   is the most load-bearing doc in the repo, and it is aging on stale figures. — **S/M, 1–2d**

## Tier 3 — Long-term (months+)

1. **Outcome-driven tiering.** The floor today is `interaction + card-advantage` from a
   heuristic classifier that is measurably blind: Triumphant Chomp, a `{R}` sorcery that
   kills anything up to a 12/12, scored ZERO roles until 2026-08-11. Once match volume
   exists, a Wilson-interval win rate becomes a SECOND axis the floor can be validated
   against, and the 41-deck PROVISIONAL backlog resolves as a consequence rather than as a
   grading chore. — **L, 2–3mo, gated on Tier 2.2**
2. **Roster consolidation.** 103 files, and `similar` already names the closest pairs
   (68a/68b at 84% theme overlap, 26b/48a at 89%). Every roster-wide sweep, rotation pass
   and doc regeneration scales with this number, so a deliberate merge/retire pass buys
   time back on all of them. Deck 68b's file already records that it is the family's
   closest pair and the first place to look. — **L, 2–4wk**
3. **A rotation-aware deck lifecycle.** Rotation is currently a flag on craft views plus
   hand-written flex successors. With 596 card-instances rotating ~2027, the natural step
   is a first-class "deck after the next rotation" view — computed rather than annotated —
   so a deck's remaining Standard life is a property you can sort on. — **L, 3–4wk**
4. **Close the heuristic-classifier gap structurally.** `_ROLE_PATTERNS` is a whitelist
   whose misses are silent by construction, and `check_roles` baselines the population but
   reads as a DELTA, not a target. **432 acknowledged zero-role cards** is a large blind
   spot to carry indefinitely, and every one of the eight holes found in 2026-08 was found
   by a human reading a card. — **L, 1–2mo**

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
data across 16,071 rows and the collection is 2,186 printings. A genuinely format-neutral
layer — "what is the best Historic deck in this collection that I have not built" — asks a
different question than any current command, and the data to answer it is already on disk.
The 100-card Historic Brawl build already queued (seed 35a with Terra as commander, who
casts for `{1}{R}{G}` while carrying a five-colour identity) is the smallest version of this.

---

## The strategic bet

**Get match volume on a handful of decks (Tier 2.2).**

This project has built an unusually rigorous internal-consistency machine: 14 gates, 1,253
tests, agreement checks between duplicate implementations of the same question, mutation
testing that proves a gate would fail if its model broke, and a documented incident behind
nearly every rule. That machinery is genuinely excellent — and it validates the tooling
against *itself*.

What it cannot do is tell you whether an A is an A. **41 of 103 decks carry PROVISIONAL
tiers**, and each file gives the same reason: unplayed. Every item in Tier 3 —
outcome-driven tiering, lifecycle modelling, closing the classifier gap — is gated on having
outcomes to check against.

The 2026-08-11 session is the argument in miniature. A one-mana sorcery that kills almost
anything scored zero functional roles, `cuts` therefore ranked it its deck's *weakest* card,
and the error surfaced only because a human playing the deck said so. No gate could have
caught it: every gate verifies that the models agree with each other, and they did.

The cost is low and falling. The pipeline runs end to end, deck attribution resolves,
`--report` is built and waiting behind its own restraint threshold. The blocker is 30
minutes of operator setup (Tier 1.4, which is also the one item with a deadline attached)
and then games. That is the cheapest available conversion of "well-engineered" into "known
correct."
