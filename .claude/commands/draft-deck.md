Build a NEW deck FROM SCRATCH around a concept, from your owned pool + craft
targets — the create-a-list counterpart to `/add-deck` (which ingests a pasted
list). Orchestrates the existing scripts; it never re-implements their logic, so
it can't drift from them.

Input: a concept in $ARGUMENTS or the user's latest message — colors and an
archetype/idea (e.g. "Simic ramp-control around Paradox Surveyor",
"mono-red aggro", "Orzhov aristocrats"), optionally a format (default Standard)
and any must-include cards.

Read CLAUDE.md's Common Gotchas first (especially the build-from-scratch helpers
`deck.py similar` / `deck.py resolve` and `pool.py --role`, and the Competitive
Tiering rubric — never auto-write an inflated tier).

## Stage 1 — Survey the pool by what cards DO (not just tags)
For the concept's colors + format, list the owned (and craftable) options by
FUNCTIONAL role, so the skeleton is built from real cards:
`python3 scripts/pool.py --owned --within <COLORS> --legal <fmt> --role <ramp|draw|removal|counter|sweeper|payoff|cheat>`
(`--within` is the SUBSET filter — identity fits a deck of those colors, colorless
included — the castable-in-my-deck question; `--color` is the superset filter and
returns five-color cards for a three-color query)
(repeat per role; add `--unowned` for craft targets, `--synergy <theme>` for the
concept's signature theme, `--full` to read a card's text before including it).
`deck.py suggest --lands --owned <existing-deck-in-colors>` is a quick owned-manabase
scan if a same-color deck exists to borrow the land read from.

## Stage 2 — Draft the ~60 and scaffold the lines
Pick a coherent 60 (≈24–26 lands + ramp + card advantage + interaction + payoffs/
finishers), leaning on owned cards, marking craft targets. Then turn the names into
valid deck lines instead of hand-looking-up printings:
`python3 scripts/deck.py resolve <names…>`  (or pipe a name list on stdin; optional
leading quantity per line). It reports unresolved/ambiguous names — fix those, don't
guess. Pass `--expect 60`: the resolver prints a total-count line and hard-fails a
miscount (the 59-card off-by-one shipped twice before that flag existed).

## Stage 3 — Create the deck file
Next deck number + a short slug → `decks/NN-slug/deck.txt`. Paste the resolved lines
(group nonland / lands cosmetically) under a `#:` header: `name`, `format`, `colors`,
`archetype` (state the PLAN and the intended DISTINCTIVENESS), `protect` (the
signature cards the tooling must never propose cutting). **Leave `#: tier:` until
Stage 5** — grade it from the floor, don't guess.

## Stage 4 — Read it, then validate
0. `python3 scripts/deck.py resolve --check NN` — verify every `(SET) COLLECTOR#`
   in the file you just wrote against known printings, STRICTLY. This exists
   because eleven hand-written collector numbers shipped wrong across two
   consecutive drafts (decks 76/77) — real sets, wrong numbers, the class
   `check_all` keeps soft — and only a hand-run diff caught them. Do not proceed
   on a non-zero exit.

   **Repair it with `python3 scripts/deck.py resolve --fix NN` (dry run), then
   `--fix NN --apply`** — it rewrites each bad `(SET) COLLECTOR#` to the
   resolver's printing in place, preserving the quantity, name and any trailing
   comment verbatim, with a `.bak` and an INV-04 re-check. **Never retype the
   fields by hand.** That is the operation G-65 forbids and G-77 was written
   about: relocating four lines by hand in one session invented two collector
   numbers, which is the same failure this step is here to catch. Until
   `--fix` existed this step's only remedy WAS the hand edit — an advisory you
   can only act on by a forbidden edit is a hazard, not a warning.
1. `python3 scripts/deck.py text NN` — read the FULL oracle text of the whole deck
   once now (cheapest time): catches mistyped/mismatched names (a wrong printing
   reads blank/wrong), off-color cards, and hidden `⚠` effects.
2. `python3 scripts/deck.py legal NN` — size (60) + copy limit + format legality
   (a craft target reads as `not in library`, not illegal — that's fine for a WIP).
3. `python3 scripts/deck.py preflight NN` — legal + owned/buildable + castability +
   integrity in one block; resolve any hard FAIL (illegal / uncastable / broken).
4. `python3 scripts/deck.py mana NN` and `python3 scripts/deck.py consistency NN` —
   confirm the manabase supports the colored/double-pip and X-cost costs.
5. `python3 scripts/deck.py targets NN` — does the list contain TARGETS for its own
   gated effects? A card whose text names a resource (an MV cap on what it can
   reanimate, a sacrifice cost, a count threshold) is only as good as the number of
   cards in THIS deck that satisfy it, and every other model here grades a card in
   isolation. A `✗ NOTHING` row is a dead card; a `⚠ thin` row is the shape that made
   deck 52's first draft hold 24 ways to return a creature against 8 worth returning.

## Stage 5 — Tune for DISTINCTIVENESS + quality
1. **`python3 scripts/deck.py similar NN`** — the whole point of a from-scratch deck:
   is it distinct, or a near-duplicate of an existing one? Read the ✦ SPECIFIC-theme
   overlaps and the `⚠ overlap` vs `· value overlap` labels; `--specific-only` for a
   pure-identity lens. If it duplicates a deck's *identity* (shared dominant specific
   theme + colors + win-con), pivot the plan (a different payoff/axis) before tuning
   further — that's how deck 40 avoided being "deck 30 minus red".
2. **`python3 scripts/deck.py screen NN <the cards you did NOT use>`** — re-score the
   REJECTED pile against the deck as it now stands. This is not optional bookkeeping:
   a pile graded against the first draft's plan keeps those verdicts after the plan
   changes, and re-reading only the cards the user re-raises leaves the rest stale
   (deck 46 lost Shrike Force, Linden and The Wind Crystal that way, and kept an
   exclusion note for Prayer of Binding that compared it to the wrong card). Run it
   again after ANY change of plan, not just once. It also flags a candidate that is a
   ★ STRICT UPGRADE of a card already in the 60, and a ✱ multiplier whose value is in
   the rest of the deck rather than its own text.
3. `deck.py cuts NN` (weakest-fit, full text) + `deck.py suggest NN --owned` /
   `--needs` — trim off-plan filler and slot owned upgrades. Honor the Player Profile
   (protect signature/spice, keep it flavorful). Preview any swap with `deck.py swap`.
4. `python3 scripts/deck.py tier NN` — read the metrics floor and set `#: tier:` to a
   letter you can DEFEND (at most one band above the floor; never auto-inflate — it's
   a human competitive judgment). Add a rationale; mark PROVISIONAL if it's a WIP brew.

## Stage 6 — Verify & commit
Ownership intent: a from-scratch deck is normally ASPIRATIONAL — leave it a WIP so
`check` shows the craft targets; do NOT reconcile the catalog from it (that's for a
deck you've actually built and own). If the library didn't change, no gallery rebuild
is needed. Rebuild the dashboard so the new deck appears
(`python3 scripts/build_dashboard.py`). Then follow the shared **verify + commit tail**
in `docs/verify-commit-tail.md` verbatim (check_all first; the `Co-Authored-By:` /
`Claude-Session:` trailer, no model ID; restart the branch from `main` first if its PR
is already merged). Report the roster with `deck.py list` and the Arena import block
(`deck.py arena NN`).
