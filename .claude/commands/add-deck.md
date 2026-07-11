Ingest a constructed deck the user pasted (an MTG Arena export) into the repo.

Input: an Arena deck export in $ARGUMENTS or the user's latest message
(`<qty> <Name> (<SET>) <collector#>` lines, optional `Deck`/section headers).

Steps:
1. Pick the next deck number and a short slug; create `decks/NN-slug/deck.txt`.
   Add a `#:` metadata header (name, format, colors, notes) and the card list
   (group nonland / lands for readability — grouping is cosmetic).
2. `python3 scripts/deck.py check NN` — see what's owned vs. flagged.
3. **Determine ownership intent.** If this is a deck the user has BUILT and
   owns, reconcile the catalog from it (a built deck is ownership evidence):
   `python3 scripts/import_arena.py decks/NN-slug/deck.txt --skip-basics`
   then `python3 scripts/enrich.py`. This adds owned-but-uncatalogued cards and
   raises undercounted quantities. If the deck is ASPIRATIONAL / not fully owned
   (a build target), do NOT reconcile — leave it as a WIP so `check` shows the
   craft targets.
4. Confirm colors from `python3 scripts/deck.py stats NN` and fix the `#: colors`
   label if the guess was wrong. Note any off-color splash.
5. If the library changed, `python3 scripts/build_gallery.py` (quantity badges).
6. `python3 scripts/validate.py` (or `/check`) to confirm clean.
7. Commit and push: the deck file, and card-library.csv / gallery.html if
   reconciled. Report the roster with `python3 scripts/deck.py list`.

Watch for: cards that are a DIFFERENT printing of one already catalogued (new
row, per one-row-per-printing); `//` double-faced names; the `--skip-basics`
flag so basic lands don't pollute the collection.
