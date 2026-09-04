# Six holes surfaced by the deck-57 tune — 2026-09-04

**Trigger.** A long `/tune-deck 57` session (six passes, 20 card changes plus a rebuilt
manabase) kept running into places where the tooling answered a question wrongly, or could
not answer it at all. The user asked for the discrepancies listed and prioritised. Four of
the six are verified down to the line of code; two are observations.

---

## P1 — `_land_value` is blind to colour breadth past two  [FIXING]

`deck_source_profile` counts a basic fetch as a source of EVERY colour the deck runs a
basic of (G-35). `wishlist._land_value`, the model `suggest --lands` ranks on, does not:

    multi = 1.0 if len(used) >= 2 else 0.5 if len(used) == 1 else 0.0
    base  = 3.5 + 4.5 * match * multi

`multi` CAPS AT TWO COLOURS, so a WUR fetch and a UR tapped dual both compute
`match 1.0 · multi 1.0` -> base **8.0, identical**. The untapped premium is then withheld
from fetches (correct — a fetch yields a tapped basic), and fetches carry no synergy tags,
so they lose the tiebreak. Measured on deck 57's full 216-row ranking: Fabled Passage /
Escape Tunnel / Vibrant Cityscape sit at **rank 45-47, score 9.5, behind 29 cards tied at
exactly 10.5**.

**What it cost.** Three basic fetches were the single largest manabase upgrade available
to this deck — they moved every worst cast-on-curve row 5-8 points and fixed the `{U}{U}`
that the deck's own flex block had recorded as unfixable. The land recommender never
surfaced them. The fix came from the user asking "would land-fetching cards be a
solution?".

**NOT a bug, checked:** Evolving Wilds and Terramorphic Expanse being absent from the
ranking is correct — `suggest_lands` filters lands already in the deck.

**Fix.** Scale `multi` with breadth against the deck's own colour count rather than
flooring at 2. Re-derive from the roster distribution and diff before shipping (the
`_DOUBLER_CALIB` / `TIER_FLOOR_REQ` lesson). A gate belongs in `check_agreement.py`, which
exists for this "two implementations of one question" shape and does not reach the land
models today.

---

## P2 — `tapland_profile` files shocklands as UNCONDITIONAL taplands  [FIXING]

    _TAPLAND_COND_RE = re.compile(r"enters(?: the battlefield)? tapped[^.\n]*\b(unless|if )", re.I)

The conditional cue must appear AFTER "enters tapped". A shockland reads "As this land
enters, you may pay 2 life. **If you don't**, it enters tapped." — the `If` comes first, so
the card falls through to `_TAPLAND_RE` and is reported unconditional.

**What it cost.** Hallowed Fountain is listed among "unconditional taplands" on
`consistency`'s tempo line — the one figure a human reads to judge whether a manabase is
too slow. The deck-57 flex block had to caveat it in three separate notes. Ten shocklands
are Standard-legal.

**Fix.** Match a `you may pay \d+ life` clause in the same sentence, or allow the cue on
either side. Report-only surface, so no re-grading risk. Pin with a real shockland.

---

## P3 — role counts count CARDS, not repeatability  [OPEN — design decided, not built]

`role_tally` returned **6** for a card-advantage set holding one repeating engine (Charred
Foyer), one net-+1 planeswalker activation (Ral) and four one-shots. The USER caught this;
no tool did. `count_conf` (G-48) annotates CLASSIFICATION uncertainty (`3 +2?`), never
quality dispersion inside the count.

**A 1-3 "limited / versatile" scale for the role buckets was proposed and DECLINED.**
Four reasons, in order of weight:

1. **It changes the UNITS of the only two terms `tier_band` reads.** Not a new term — the
   existing ones re-scaled. `TIER_FLOOR_REQ` would need re-deriving (it already was, on
   2026-09-02, BS8-06), and **110 of 117 deck files cite interaction or card-advantage
   figures in `#: tier:` prose** — every one goes stale in a single commit.
2. **The classifier is the weak link, not the granularity.** `check_roles` reports **560 of
   1882 roster cards (30%) score ZERO roles**. A precision axis on top of a base that
   misses 30% of cards grades confidence that is not there (K-12, G-67).
3. **"Versatile / strong" is exactly the fuzzy judgment this repo refuses to score.**
   G-09's `⚠ scales w/`, G-25's protection axis and G-41's cost-as-upside are all
   deliberately FLAGS, never score changes — "the honest stance for a fuzzy signal".
4. **The real failure was ONE structural distinction, not a missing scale.**
   Repeatable-vs-one-shot is binary, syntactic and text-detectable (a trigger or activated
   ability vs a one-shot ETB/cast — the same argument K-14 already rests on).

**Build instead: an orthogonal REPORT-ONLY split, the G-81 pattern.** Render
`card advantage 6 (1 repeatable, 5 one-shot)` while the bare int still feeds `tier_band`.
Precedent, three times over: `count_conf` renders `8 +4? (3 unclassified)`; `early_drops`
renders `9 (4 mana sources)` because a mana dork is not a clock (G-81); the interaction
profile splits by SPEED and by noncreature-answer (G-24). Pick the structural distinction
that matters per axis and split on it.

**Related, unreported anywhere:** two of deck 57's three best card-advantage sources are
UNOWNED crafts, so the owned figure is 3 against a printed 6. No surface separates owned
from aspirational inside a role count.

---

## P4 — the rationale audit cannot see a prose claim about the POOL  [OPEN]

Deck 57's `#: tier:` block asserted "no untapped dual exists owned or craftable". False —
two owned, four craftable — and it was the stated reason two earlier decisions went the way
they did. The audit prices FIGURES and IN-DECK CARD citations; an existential claim about
the pool is invisible by construction. Same shape as the "near-zero protection" retraction
of 2026-09-03.

**Fix.** A narrow scan for existential shapes (`no \w+ exists`, `nothing in the pool`,
`there is no`) that FLAGS for human re-check rather than trying to verify. Keep the cue
list narrow and sweep the roster before shipping (G-26).

---

## P5 — `#~` swap-line rationale sits outside the figure sweep  [OPEN]

`note_figure_staleness` reads `#~ note:` prose only. Two `#~ -X | +Y | ...` rationale
blocks in deck 57 carried `card advantage 5 -> 6` figures that went stale within the
session and were corrected BY HAND; nothing would have caught them.

**Fix.** Widen the line filter to the rationale text of `#~ -/+` lines — same predicate.
Measure the roster hit rate first; keep it soft if noisy.

---

## P6 — `cuts` disagreed with both real cuts  [NO ACTION, recorded]

`cuts` ranked Crackling Cyclops **15/32** and Equilibrium Adept **25/32** — both in the
bottom half — while putting the deck's removal suite at the top of the cut list. That is
G-09 behaving as documented (a coin flip on creature-heavy decks; three fixes
pre-registered and REFUTED). The right action is to let `recommendations.csv` keep
accumulating the disagreements — this session added six rows — and **not** to derive a
fourth fix.

---

## Status

P1 and P2 implemented in the `/broad-implement` run that follows this block.
P3 (as the split, not the scale), P4 and P5 remain open.
