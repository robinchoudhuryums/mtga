Add unowned craft targets to the main wishlist, with home + cross-deck targeting.

Input: an MTG Arena export of cards you do NOT own but want to craft, in
$ARGUMENTS or the user's latest message (`<qty> <Name> (<SET>) <collector#>`
lines), OR a phrasing like "the craft targets of deck 36" (then pull deck 36's
unowned nonland cards with `deck.py check 36`). This is the UNOWNED craft-target
intake loop — for cards you now OWN use `/add-cards`, for a whole new deck use
`/add-deck`.

This skill **orchestrates the existing scripts** — it never re-implements their
logic, so it can't drift from them. Read CLAUDE.md's `card-wishlist.csv` gotchas
first (Target/Power are hand-annotated; DFCs are stored under the full `Front //
Back` name; the ranking model — not the CSV — is what `check_all` gates).

Most of the *checks* here are already automated — `--add` auto-seeds a heuristic
Power, `--rank`'s `use` column auto-computes cross-deck breadth, and
`--audit-targets` is folded into `check_all`. The skill exists to guarantee the
two HUMAN-JUDGMENT steps that are easy to skip: setting the **Target** and the
**cross-deck fit review**.

## Stage 1 — Add + enrich

1. **Add the batch:** `python3 scripts/wishlist.py --add <export>` (file or `-`
   for stdin). It enriches each card (Type/Color/text/Synergies) from
   `card-pool.csv` with a Scryfall fallback, stores DFCs under their full name,
   and **auto-seeds a heuristic Power**. Re-running `--add` on a batch re-enriches
   rows added name-only during an earlier Scryfall outage.
2. **Don't trust the Power seed on bombs.** The classifier undersells format-
   warping cards. Skim the seeded values (`--rank` shows them) and hand-raise the
   obvious bombs in `card-wishlist.csv` (it's a plain CSV) — a sunk Power ranks a
   real craft target far too low.

## Stage 2 — Set the Target (home deck)

`--add` leaves Target blank. Set it to the deck the card is a craft target *for*:

- **If the cards came from specific decks** (e.g. "the craft targets of deck 36"),
  set Target to that deck id directly — a core deck for cards shared by its
  variants (`36`), the variant id for a variant-only card (`36a`). Edit the CSV
  directly or script it; it's the authoritative "which deck is this for" field.
- **If it's a loose batch** with no obvious home, run
  `python3 scripts/wishlist.py --suggest-targets` (idf-weighted theme fit; add
  `--write` to fill blank Targets with its STRONG/ok picks) and text-review the
  `review` cards — the tag heuristic genuinely can't place generic/multi-home/
  new-concept cards.

## Stage 3 — Cross-deck fit review (the step that's easy to forget)

A craft target often earns a slot in MORE than its home deck, and a multi-home
craft is worth more per wildcard. Two layers, both now reliable:

1. **Breadth is already auto-scored.** `python3 scripts/wishlist.py --rank` shows
   a **`use`** column (how many of your decks the card is castable + central-theme
   in, ★ at ≥3) that feeds the ranking — so a broadly-useful staple (removal,
   card advantage) is already credited for its reach. You do NOT hand-stuff every
   fit into the Target; that's what `use` is for.
2. **Record only a GENUINE specific second home.** For each added card run
   `python3 scripts/deck.py suggest-homes "<card>"` and look at the `KEY` /
   `role-player` rows for decks OTHER than its home. Trust these now: the
   classifier is specific-theme-gated (a generically-good card no longer reads KEY
   in every low-interaction deck — see `fit_strength`), so a KEY/role-player fit
   means a real shared SPECIFIC theme (a tribe like Wizard/Bird, a real archetype),
   not generic etb/tokens overlap. When one is genuine, add that deck to the Target
   with the multi-target format: `Target = "37a; 19"`. Ignore tangential rows.

## Stage 4 — Audit + verify + commit

1. **Audit the targets:** `python3 scripts/wishlist.py --audit-targets` — flags any
   card whose target deck can't cast it (hybrid-aware) or has blank Power. Re-home
   or grade until clean.
2. Then the **shared verify + commit tail** in `docs/verify-commit-tail.md`
   (check_all-first, the Co-Authored-By / Claude-Session trailer, no model id,
   branch-restart on a merged PR). `card-wishlist.csv` isn't gated by `check_all`,
   but run it anyway to catch the soft target-drift warning and any ranking-model
   regression.
