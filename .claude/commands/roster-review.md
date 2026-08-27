Survey the whole collection — what to tune, what rotates, what drifted, what to craft.

This is the ROSTER loop. `/tune-deck` and `/apply-changes` cover one deck deeply;
nothing covered the question "across the whole roster, what should I work on?", so five
genuinely useful commands (`audit`, `rotation`, `brawl`, `verify`, `sync`) existed
and were only ever run when someone remembered them. `check_commands.py` now fails
the build if that happens again.

Everything here is READ-ONLY and offline except the optional repair in step 5.
Nothing is written without asking first.

## 1. Triage — which decks need attention

`python3 scripts/deck.py audit --flagged`

One line per deck: ownership drift, legality, castability, interaction count,
central themes, and a verdict of **★ TUNE** / **craft** / **review** / **ok**.

Read the verdicts as a SHORTLIST, not a grade:
- **★ TUNE** — a hard problem (illegal or genuinely uncastable card). Fix these.
- **craft** — the list is fine, you just don't own it all yet. Not a defect.
- **review** — a soft flag: an off-color ABILITY (`Na` in the Cast column) or thin
  interaction. Worth a look, not a verdict. A hybrid you pay on-color shows as `Ns`
  and deliberately never reaches this bucket.
- Add `--by-tier` to sort by competitive tier instead of verdict.

## 2. Rotation exposure — what leaves Standard next

`python3 scripts/deck.py rotation`

Cards past the ~3-year window, rolled up by rotation year (soonest first), plus the
most-exposed decks. Use it to decide what NOT to craft. If it prints a rebuild
prompt, the pool predates the `Released` column — run `/refresh` first.

## 3. Craft plan — where the wildcards go

`python3 scripts/deck.py wildcards --dedup`
`python3 scripts/wishlist.py --rank`

`wildcards` is the roster-wide "what finishes a deck" view. Run it **`--dedup`**
here: plain `wildcards` reports per deck, so a card three decks are short of
appears three times and nothing tells you that. `--dedup` is the cross-deck UNION
ranked by decks-served per copy, which is the question this section's heading
actually asks. Read the two columns as different things: **Decks** is how many
decks that one card unblocks (copies are fungible — a `Decks 3` card is one
craft serving all three simultaneously, never three crafts), while **Copies** is
what you must still craft — the most any *single* deck needs, minus what you
already own across every printing. Drop `--dedup` only when you want the per-deck
breakdown of a specific deck's gap.
Both views carry the `⚠rot` flag.

`--rank` is the value-per-wildcard ranking. If you have a specific budget, prefer
`wishlist.py --budget "9M 10R 38U 48C"`, which is the SPEND view and is the only
one that shows every check — including the `⚠rot` flag on a card about to rotate.

## 4. Brawl conversions — cheap format wins

`python3 scripts/deck.py brawl`

Ranks every deck by distance to a legal Brawl conversion (duplicates to trim to
singleton, plus cards outside the best in-deck commander's color identity) and
names that commander. Decks that already have a `*-brawl` variant are marked.
Only worth acting on if you actually play Brawl — otherwise read and move on.

## 5. Arena drift — has the repo fallen behind?

The repo only updates when someone writes a deck file, so decks edited in the Arena
client silently diverge. Ask the user to paste an Arena export (one or many `Deck`
blocks), then:

`python3 scripts/deck.py verify <id>` — for a single deck you already identified
`python3 scripts/deck.py sync -` — for a multi-deck paste; auto-matches each block

`sync` is DRY-RUN by default. Report the diff and **ask before running `--apply`**,
which rewrites deck files (with a `.bak` and an INV-04 re-check). A block matching
two variants nearly equally is reported LOW CONFIDENCE and skipped — re-paste that
deck alone rather than forcing it, since rewriting the wrong sibling is the one
expensive mistake here.

If the user has no export handy, say so and skip this step rather than guessing.

## Report

Finish with a short prioritized summary — the point of this command is to end with
a decision, not five tables:

1. **Act now** — any ★ TUNE deck, and any deck that drifted from Arena.
2. **Spend on** — the top few craft targets, with anything `⚠rot` called out as a
   wildcard that won't last.
3. **Watch** — decks with heavy rotation exposure this year or next.
4. **Ignore** — say plainly what came up clean, so the absence of a flag is on the
   record rather than assumed.

Then suggest the natural next step: `/tune-deck <id>` for the worst offender, or
`/add-wishlist` if the craft plan turned up gaps. Do not start tuning inside this
command — the roster pass picks the target, the deck pass does the work.
