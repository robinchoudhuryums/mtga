Analyze a deck and propose improvements — with owned cards and craftable upgrades.

Input: a deck id in $ARGUMENTS (e.g. `18` or `18a`).

Gather the full picture BEFORE recommending anything (read the actual card text
— don't judge by mana value or a single subtype):
1. `python3 scripts/deck.py check <id>` — owned vs. craft targets.
2. `python3 scripts/deck.py stats <id>` — types, curve, and the ◊ (cheaper) /
   △ (added-cost) flags. Treat printed MV skeptically for flagged cards.
3. `python3 scripts/deck.py mana <id>` — hybrid-aware color requirements. This,
   not stats' rough color identity, is the truth about how many sources each
   color needs. Hybrids don't demand their off-color.
4. `python3 scripts/deck.py tribes <id>` — creature subtypes and type-matters
   payoffs (which payoff cards reward which types, and how many creatures
   qualify). Catches cross-type synergies.
5. For any card you'd cut or keep, read its Card Text from card-library.csv /
   card-pool.csv. Verify synergies and effective cost before judging.

Then find improvements:
- Owned upgrades: `python3 scripts/query.py --type <tribe>/--synergy <theme>`
  for on-theme cards the user already owns but didn't include (free — check they
  fit the mana with `deck.py mana`).
- Craftable upgrades: `python3 scripts/pool.py --synergy/--type ... --unowned`
  (and `--rarity`) for cards worth wildcards. Report wildcard cost by rarity.

Deliver:
- The deck's real color requirements and any mana-base tension.
- Concrete swaps (out → in) with rationale, noting the effect on white/off-color
  demand and on wildcard cost (prefer swaps that improve BOTH).
- If asked to build it, create a variant `<id>a`/`<id>b` (full list), then show
  `deck.py diff <id> <ida>` and `deck.py mana <ida>`, and provide the Arena
  import block via `deck.py arena <ida>` plus the wildcard tally.

Be honest when the tools contradict a first-glance judgment — the data wins.
