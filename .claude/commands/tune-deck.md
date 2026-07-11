Analyze a deck and propose improvements — with owned cards and craftable upgrades.

Input: a deck id in $ARGUMENTS (e.g. `18` or `18a`).

## Stage 0 — Read the play-style profile

Check CLAUDE.md's **Player Profile** for the default deck-building style on the
creative ↔ competitive dial, and honor any per-run override in $ARGUMENTS
(e.g. `19 competitive`, `19 creative`). The style changes how you weight cuts and
swaps (see "Play-style weighting" below) — not the data-gathering.

## Stage 1 — Gather the full picture (before recommending anything)

Read the actual card text — never judge by mana value or a single subtype:
1. `python3 scripts/deck.py check <id>` — owned vs. craft targets.
2. `python3 scripts/deck.py stats <id>` — types, curve, and the ◊ (cheaper) /
   △ (added-cost) flags. Treat printed MV skeptically for flagged cards.
3. `python3 scripts/deck.py mana <id>` — hybrid-aware color requirements. This,
   not stats' rough color identity, is the truth about how many sources each
   color needs. Hybrids don't demand their off-color.
4. `python3 scripts/deck.py tribes <id>` — creature subtypes and type-matters
   payoffs (which payoff cards reward which types, how many creatures qualify).
5. `python3 scripts/deck.py suggest <id>` — on-color, on-theme pool cards, owned
   vs. craftable with rarity.
6. For every card you'd cut OR keep, read its Card Text from card-library.csv /
   card-pool.csv. A card's real value is in its text (tap engines, alt costs,
   token generation) — the tribes/curve tools miss cross-mechanic synergies.

## Stage 2 — Deliver a STRUCTURED report

Use these sections and headings, in order. Keep it scannable: severity- and
wildcard-tagged, with discrete swaps the user can accept or reject individually.

**1. Snapshot** — archetype · format · colors · card/land count · buildability
(owned N / craft M, with the wildcard breakdown by rarity). One status line.

**2. Health scorecard** — rate each dimension **Strong / OK / Weak** + one line:
mana base (sources vs. strict requirements) · curve fit (for this archetype's
speed; credit ◊ cost-reducers) · synergy density (theme/tribal count,
payoff-to-enabler ratio) · interaction (amount AND type: removal/counter/tempo) ·
card advantage / reach · consistency (redundancy vs. singleton context).

**3. Keep — validated strengths + signature/spice** — engines/cards that are
working; say *explicitly* not to cut them (guardrail against over-tuning). Split
out a **Signature & spice** line: the cards that give the deck its identity / fun
factor. At a creative-leaning style these are *protected* — never cut them for a
generic upgrade unless they're actively non-functional.

**4. Findings** — tagged **Critical / Moderate / Minor**, each grounded in card
text; separate problems from opportunities.

**5. Recommended changes** — ranked; each a discrete swap:
`− Out / + In` | wildcard cost (rarity + owned/craft) | impact deltas (creatures /
tribe / curve / color) | **two-axis verdict: power (helps/neutral/hurts) + fit/fun
(on-identity/neutral/off-identity)** | confidence. Rating both axes keeps the
power-vs-flavor trade visible instead of collapsing it into one "worth it."

**6. Craft priority** — for WIP decks: tiered list by impact-per-wildcard.

**7. Routes / branches** — when directions genuinely diverge (e.g. more tempo vs.
more midrange), present as forks with trade-offs, not one linear answer.

**8. Decisions for you** — judgment calls that hinge on preference/meta; surface
them, don't decide unilaterally.

**9. Bottom line** — the single highest-value move + the net wildcard spend.

## Criteria (rules the report must honor)

- **Ground every call in card text.** When the tools contradict a first-glance
  judgment, the data wins — say so.
- **Wildcard-aware always.** Tag every craft with rarity + a worth-it verdict;
  prefer owned or lower-rarity alternatives (an uncommon that does ~90% of a
  rare's job usually wins).
- **Judge against the deck's own intent/archetype**, not a generic ideal.
- **Discrete, individually-acceptable swaps** — never a monolithic "new list."
- **Show before/after deltas** for each change.
- **Respect singleton-vs-playset context** — tuning a 60-card highlander differs
  from a 4-of Standard list.

## Play-style weighting (creative ↔ competitive)

Apply the profile from Stage 0. The dial changes *recommendations*, never the
honesty of the data (always still report the by-the-numbers pick).

- **Creative-leaning** (default for this repo — see CLAUDE.md): optimize for
  interesting/entertaining play, not raw win-rate.
  - **Protect signature/spice cards** — don't cut a functional-but-quirky card
    just because a generic "better" option exists.
  - **Power-gap threshold for homogenizing swaps** — only suggest replacing a
    flavorful card with a staple when the power gap is *large*; otherwise keep
    the flavorful card and merely *note* the option.
  - **Reserve a fun budget** — leave ~15–20% of flex slots for pure-flavor picks
    even if suboptimal; call them out as intentional.
  - Frame trade-offs as choices ("the netdeck pick is X; your Y does ~85% and is
    more your style"), and lead with fit/fun in the two-axis verdict.
- **Competitive-leaning**: flip it — prioritize power, recommend the staples,
  minimal fun budget, lead with the power axis.
- **Balanced**: in between — surface both the staple and the spicy option and let
  the user pick.

## If asked to build it

Create a variant `<id>a`/`<id>b` (a full list — variants are self-contained), or
overwrite the base if the user wants it promoted to primary. Then show
`deck.py diff <base> <new>`, `deck.py mana <new>`, the Arena import block via
`deck.py arena <new>`, and the wildcard tally. Deck files save with a `.bak` and
must re-parse cleanly (INV-04).

## Recording flex swaps

When the report surfaces discrete swaps the user might want later (Section 5),
you can persist them as a **flex block** at the end of the deck file so they
travel with the deck instead of living only in chat. These are `#~` comment lines
— ignored by the parser, absent from the Arena export — so they're safe to append
to any list (see `decks/README.md` → *Flex section*):

```
# Flex — suggested swaps (comments; not part of the 60). See: deck.py flex <id>
#~ -Card Out | +Card In | one-line reason grounded in card text
```

Read them back with `deck.py flex <id>` (enriches each `+In` with cost, rarity,
owned count); the editing app shows them in a read-only panel.
