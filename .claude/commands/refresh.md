Rebuild the derived data artifacts after card/deck changes, then verify.

**The whole chain is `make refresh`.** Run that rather than the steps below unless you
genuinely need to skip one — the Makefile target is the single executable definition of
the order, which previously lived in four prose copies of which three were wrong (they
put `build_pool.py` after `build_mana.py`, leaving a new set's pool cards with no mana
row until the next cycle). The steps are documented here so you can skip deliberately,
not so you can retype them.

Derived files depend on card-library.csv and can drift after imports or edits.
Rebuild them in dependency order (all require Scryfall egress except the last
two):

1. `python3 scripts/enrich.py` — fill blank Type/Card Text/Color(s)/Collector #
2. `python3 scripts/build_pool.py --all` — refresh the full Arena card pool (drop
   `--all` for a smaller Standard-only pool). Run this BEFORE `build_mana --pool`,
   which reads card-pool.csv — otherwise a just-released set's new pool cards
   wouldn't be covered by card-mana.csv until the next cycle.
3. `python3 scripts/build_mana.py --pool` — refresh card-mana.csv (mana costs +
   keywords). `--pool` keeps costs for the full Arena pool (unowned cards), which
   is slow; omit it for a fast library-only build (but that drops pool coverage)
4. `python3 scripts/tag_synergies.py --merge` — keyword-aware synergy tags
   (reads card-mana.csv's keywords, so it must run after step 3). `--merge` ADDS
   newly-derived tags to existing cells without removing hand-curated ones; use
   `--force` only for a deliberate destructive regenerate (it clobbers hand edits)
5. `python3 scripts/build_gallery.py` — rebuild gallery.html (images). NOTE:
   this does NOT rebuild dashboard.html — nothing in the refresh chain does.
   The deployed dashboard is rebuilt by pages.yml on every push to main; run
   `make dashboard` (~2 min, offline) only if the committed copy should be
   current locally.
6. `python3 scripts/check_all.py` — confirm all invariants hold

Notes:
- Skip step 1 if no new/blank cards were added. Skip step 2 unless card-library
  changed (the full-pool build is the slowest step).
- If Scryfall is unreachable, report which steps were skipped and why; steps 5–6
  still run from cache.
- End by reporting check_all's result. Suggest `/sync-docs` if the code/data
  changes affect the README or CLAUDE.md.
- **Then commit what the rebuild rewrote.** Every derived file here is tracked, so a
  refresh that stops at the report leaves the repo dirty and the next command inherits
  it. Stage only the files that actually changed (`git status` — a reused pool per G-18
  legitimately changes nothing) and follow the shared **verify + commit tail** in
  `docs/verify-commit-tail.md` verbatim: `check_all` gates the commit, the CURRENT
  session's `Co-Authored-By:` / `Claude-Session:` trailer ends the message, the model ID
  never appears in it, and the push goes to the working branch. If nothing changed, say
  that rather than committing an empty diff.
