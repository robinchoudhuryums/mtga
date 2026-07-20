Catalog newly-owned cards and find their homes across your decks.

Input: an MTG Arena export of cards you now OWN (crafted or opened) in
$ARGUMENTS or the user's latest message — `<qty> <Name> (<SET>) <collector#>`
lines. This is the owned-card intake loop; for a whole new *deck*, use
`/add-deck` instead.

This skill **orchestrates the existing scripts** — it never re-implements their
logic, so it can't drift from them. Read CLAUDE.md's Common Gotchas first
(especially the deck-dump undercount and the DFC front-vs-full-name handling —
`reconcile_crafts.py` is the tool that gets both right).

## Stage 1 — Catalog the cards (own them in the data)

1. **Dry-run the reconcile** so you see exactly what will change:
   `python3 scripts/reconcile_crafts.py <export>` (reads a file or `-` for
   stdin). It reports which cards it will add to `card-library.csv` (DFCs stored
   under their **front** name), which `card-mana.csv` rows it will append (keeps
   INV-02), and which `card-wishlist.csv` rows it will drop (a craft target you
   just fulfilled).
2. **Apply it:** `python3 scripts/reconcile_crafts.py <export> --apply` — writes
   with `.bak`s. This is the correct fix for the "not in library / undercounted"
   symptom; do NOT hand-edit the CSVs.
3. **Rebuild derived data** so costs/tags/art catch up:
   `python3 scripts/build_gallery.py`, then — if any card was genuinely new to
   the library (not just a quantity bump) — `/refresh` (enrich → build_pool →
   build_mana → tag_synergies → build_gallery) so the new rows get real
   cost/keywords/synergies rather than fallbacks. A pure quantity bump needs only
   the gallery rebuild.
4. **Prune the wishlist & catch drift:** `reconcile_crafts.py` already drops the
   fulfilled rows; confirm with `python3 scripts/wishlist.py --owned` (lists any
   wishlist card you now own — should be empty for the batch). Then
   `python3 scripts/wishlist.py --audit-targets` to re-home any card whose target
   deck drifted color/theme (a soft signal, also folded into `check_all`).

## Stage 2 — Read each card, then place it (full text, always)

For **every** newly-owned card, in this order — never grade from a tag or role
label (CLAUDE.md's recurring mis-grade):

1. `python3 scripts/card.py "<name>"` — the COMPLETE oracle text + mana cost +
   **format legality** + owned qty + which decks already run it. Heed a
   `⚠ unindexed mechanic` line (F02): that keyword isn't in the synergy map, so
   grade its effect from the text, not the tags. **A card that isn't
   Standard-legal is not a Standard craft** — say so and stop suggesting it there
   (the Champion-of-Rhonas / Chord-of-Calling mistake).
2. `python3 scripts/deck.py suggest-homes "<name>"` — every deck the card is
   *castable* in and shares a *central* theme with, each row tagged with an F04
   **strength** label (**KEY** — fills an interaction/card-advantage gap or shares
   the deck's signature theme; **role-player** — a secondary central theme;
   **tangential** — generic overlap only) and a single weakest-nonland **cut
   candidate**. Rows are sorted strongest-fit first.
3. For each real fit, grade it from the Stage-2.1 text against **this deck's
   engine** (a "downside" clause is often an upside in the matching deck — see
   CLAUDE.md's swap gotcha) and classify it:
   - **key upgrade** — a KEY fit that beats a current card on a real axis; name
     the cut candidate and confirm it from full text (`deck.py cuts <id>` /
     `card.py` on the cut).
   - **sidegrade** — lateral (~85% of something already run); name it to say
     *skip* unless the user wants it.
   - **different-flavor** — not stronger but changes how the deck plays; offer it
     as a creative option (honor the Player Profile).
4. **Copies are fungible — slot a card into ALL decks it earns, not one.** If a
   card is a key upgrade in three decks, propose it in all three; never tell the
   user to "pick a home" or "split copies" (CLAUDE.md: one owned copy plays in
   every deck at once).

## Stage 3 — Verify & report

5. **Preflight every touched deck:** `python3 scripts/deck.py preflight <id>` —
   one block confirming legal + owned/buildable + castable + integrity. Resolve
   any hard FAIL before reporting.
6. **Structured report:**
   - **Cataloged:** N cards added / M quantities bumped; any wishlist rows pruned.
   - **Per card:** `card` → the fit rows as `card → deck (strength) — cut
     candidate — key upgrade / sidegrade / different-flavor`, with the operative
     oracle clause quoted for each recommended swap.
   - **No-home cards:** stated plainly (owned but nothing fits yet).
   - Do NOT apply the swaps here — this skill catalogs and *recommends*; applying
     is `/apply-changes` (which the user confirms). Honor the standing "propose,
     don't apply until confirmed" rule.

## Stage 4 — Commit (standardized tail)

Only the **catalog** changes (library / mana / wishlist / gallery) are committed
by this skill — the swaps are not applied yet. Follow the shared commit
discipline:

- `python3 scripts/check_all.py` must pass first (all invariants hold).
- Commit the changed data files with a clear message; end it with the
  `Co-Authored-By:` and `Claude-Session:` lines and **never** put the model ID in
  the message, code, or any pushed artifact.
- Push to the working branch with `git push -u origin <branch>` (retry with
  backoff on network errors). If that branch's PR is already merged, restart the
  branch from `main` per CLAUDE.md before pushing the follow-up.
