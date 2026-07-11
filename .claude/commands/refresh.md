Rebuild the derived data artifacts after card/deck changes, then verify.

Derived files depend on card-library.csv and can drift after imports or edits.
Rebuild them in dependency order (all require Scryfall egress except the last
two):

1. `python3 scripts/enrich.py` — fill blank Type/Card Text/Color(s)/Collector #
2. `python3 scripts/build_mana.py --pool` — refresh card-mana.csv (mana costs +
   keywords). `--pool` keeps costs for the full Arena pool (unowned cards), which
   is slow; omit it for a fast library-only build (but that drops pool coverage)
3. `python3 scripts/tag_synergies.py --force` — keyword-aware synergy tags
4. `python3 scripts/build_pool.py --all` — refresh the full Arena card pool (drop `--all` for a smaller Standard-only pool)
5. `python3 scripts/build_gallery.py` — rebuild gallery.html (images + dashboard)
6. `python3 scripts/check_all.py` — confirm all invariants hold

Notes:
- Skip step 1 if no new/blank cards were added. Skip step 4 unless card-library
  changed (it's the slowest).
- If Scryfall is unreachable, report which steps were skipped and why; steps 5–6
  still run from cache.
- End by reporting check_all's result. Suggest `/sync-docs` if the code/data
  changes affect the README or CLAUDE.md.
