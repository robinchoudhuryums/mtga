# FINDING — `cuts` is blind to the deck's PLAN and to mana value

**Status: OPEN, not started.** A `/broad-scan`-format finding, written 2026-09-22 out of the
deck-1 tune. Hand it to `/broad-implement` when it is picked up, or fold it into the next
`/broad-scan`'s batch plan. Delete this file once it lands or is declined with its reasons
recorded in `.cycle/HISTORY.md`.

---

## F-CUTS-01 | `cut_keep_score` reads neither mana value nor `#: plan:`

**File / area:** `scripts/deck.py` — `cut_keep_score` (~L8791) and `rank_cut_candidates`
(~L8941).

**Severity:** Medium
**Confidence:** High (read the function; did not infer it from behaviour)
**Class:** feature-effectiveness gap — NOT a production bug. `cuts` is documented
REPORT-ONLY and SHORTLIST-ONLY (G-08/G-09), and it is behaving as written.

### The issue

`cut_keep_score` sums nine terms: theme fit (idf-weighted tags), role credit, tribal count,
cost-as-upside flags, a signature-theme hit, the wishlist power seed, ability
distinctiveness, multiplier support and cost-scale support. **None of them is mana value,
and none of them is the deck's plan.** `rank_cut_candidates` carries `mv` in its row tuple
purely so the table can print a column, and its sort key is `(keep, name.lower())`.

So a 4-mana ramp body and a 2-mana threat carrying the same tags score identically, and an
aggro-plan deck and a control-plan deck get the same ranking over the same 60 cards.

### Motivating evidence — deck 1, Black Sun (2026-09-22)

Four swaps were applied to deck 1 in one session. `recommendations.csv` recorded the
model's rank for each cut card (of 33 ranked):

| cut | `cuts` rank | why it was cut anyway |
|---|---|---|
| Kav Landseeker | **28 / 33** (strong keep) | 4-mana body whose payoff — a Lander that fetches a basic — arrives on turn 5 |
| Diamond Pick-Axe | 18 / 33 | 3 mana total to buff ONE creature in a go-wide deck; rotates ~2026 |
| Prickly Pair | 14 / 33 | two bodies for 3 where the deck wanted a 2-drop |
| Tome Blast | 7 / 33 (agreement) | strictly worse than the Burst Lightning already in the list |

Three of four disagreements, and all three are the same shape: the model liked the TAGS and
could not see the CURVE. Kav Landseeker is the clean case — it scores well on
tokens/mana/etb and is a ramp creature in a deck that wants to be attacking on turn four.

Separately, `cuts` ranked **Day of Black Sun #1** — the card the deck is NAMED after.

**The strongest data point arrived last, 2026-09-22:** `cuts` ranked **Fire Nation Raider
33 / 33** — its single strongest KEEP in the deck — for a four-mana 4/2 whose entire text is
*"Raid — When this creature enters, if you attacked this turn, create a Clue token."* Cast
precombat it does nothing, and a 4/2 trades down against everything. It ranks last on the
cut list because `tokens` / `etb` / `raid` / `clue` are four of the deck's central themes
and the card hits all four. The tags are right; the card is a 4/2 that sometimes cantrips.
This is the cleanest available illustration that theme fit alone is not a grade.

### Three things to settle before building anything

**1. The `#: protect:` header already solves the loudest half, and deck 1 was not using it.**
`cuts` hard-excludes protected cards by name. Deck 1 had no `#: protect:` line at all, which
is the entire reason its namesake sorted first. That is a zero-code fix available today and
it should be applied and MEASURED before a code change is designed — it may absorb most of
the complaint.

**2. A plan-aware `cuts` would read the WRONG PLAN on at least 7 decks today.**
Measured 2026-09-22 across all 114 deck files:

- **60 of 114 (53%)** carry an explicit `#: plan:` header. **54 (47%) do not** — their plan
  is inferred from `#: archetype:` keywords, else from metrics.
- **7 decks read inferred `aggro` while their avg MV is >= 2.9**: 39-starforge (3.40),
  35-hack-n-slash (3.36), 20-honor-among-thieves (3.33), 36-panthera (3.31),
  02-thundergod (3.28), 37-wizardz (3.11), 01-black-sun (3.03).

Deck 1 is the LEAST extreme of the seven. Its `#: archetype:` prose says "aggro-sacrifice"
while `deck.py shape` measures a MIDRANGE curve; the inference took the prose. A plan-aware
flag shipped today would flag confidently in the wrong direction on all seven. **Fix the
headers first** — this is the deck-56a lesson (`#: plan:` is a grading input, not a label)
arriving one tool over.

**3. It must be a FLAG, not a score term.** Two independent reasons from the record:

- **G-09 states three `cuts` re-weightings were pre-registered and REFUTED** (body quality,
  tag-count normalization, role-credit reweighting) and ends "don't derive a fourth". A plan
  or curve term would be the fourth.
- The standing pattern here is that a fuzzy signal gets a flag and never a score change:
  the protection axis (G-25), board power (G-86), the X-cost advisory (G-60), `cuts`' own
  `⌁ scales w/` and `⚡` (G-41) are all report-only, and `_land_utility` (G-37) is explicitly
  a tie-break rider forbidden from becoming a score term.

### Proposed shape (for the implementer to measure, not to assume)

A display-only **`⚠ off-plan`** rider on the `cuts` row, gated on an EXPLICIT `#: plan:`
header only — never on an inferred plan, per constraint 2.

The primitive already exists: **`_MANA_SOURCE_RE`** (G-81) separates a mana-producing early
drop from a real threat, which is exactly the Kav Landseeker discrimination. An `aggro`-plan
deck flags its mana bodies and its MV 5+ cards; a `control`-plan deck flags neither.

**Acceptance bar, set by the record rather than by taste:** G-41's pay-life flag scored 22%
precision over 91 roster pairs and was DECLINED; G-42's engine-conflict flag scored <=14% over
44 hits and was DECLINED. So this needs a measured roster-wide precision rate BEFORE it
ships, in the same form. A hand-check of the flagged rows against the deck's own plan is the
measurement; if it lands where those two landed, decline it and record that in HISTORY.md.

### Effort

S for the flag itself (one predicate + a column, reusing `_MANA_SOURCE_RE`).
M once the mandated roster measurement and the `check_suggest` anchor are included.
The header backfill in constraint 2 is separate editorial work on 54 deck files and should
NOT be bundled into the same batch.

### Out of scope, deliberately

Re-weighting the keep score. Adding an MV term. Making `cuts` a grade rather than a
shortlist. All three are the thing G-08/G-09 spent three refuted experiments learning not
to do.
