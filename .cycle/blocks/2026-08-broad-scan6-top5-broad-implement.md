---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS6-10 | Four removal templatings scored ZERO interaction — the axis the tier floor grades
- BS6-01 | Ownership joins resolved full→front but never front→full, so 8 full-name library rows read as unowned
- BS6-11 | CLAUDE.md stated the DFC storage convention as a fact that is false for those 8 rows
- BS6-02 | Dashboard mana-colour tokens had no light-mode value on bars whose track flips near-white
- BS6-03 | `attachHover` bound focus/blur to non-focusable spans at 2 of its 3 call sites
- BS6-06 | Deck 73 carried six hand-written collector numbers matching no known printing (G-65)

Files modified: scripts/deck.py, scripts/card.py, scripts/pool.py, scripts/build_dashboard.py,
decks/73-dukes-vigil/deck.txt, CLAUDE.md, tests/test_deck.py, dashboard.html (rebuilt)

CHANGES:

BS6-10 | scripts/deck.py, tests/test_deck.py | Two new `Removal (spot)` patterns.
  (1) COORDINATED QUALIFIER LIST — the existing run allows at most two adjective words, so
  "attacking or blocking" (3), "green or white" (3) and "non-Angel, non-Demon, non-Devil,
  non-Dragon" (4, with commas `[a-z-]+ ` cannot cross) matched nothing. A SEPARATE pattern
  requiring at least three qualifier words, so it is strictly additive and every change is
  attributable to it — raising the shared `{0,2}` run would have re-scored every removal card
  at once, which is what BS2-06 records the cost of. A zone lookahead excludes "exile target
  card … from a graveyard": `land` and `creature` are in `_PERM_TYPE`, so without it Kotose
  (graveyard hate) and Offspring's Revenge (a recursion cost) both read as removal. Measured
  over all 16,067 pool rows: 11 newly classified, 0 false positives.
  (2) REMOVAL AURA — `enchanted creature can't attack or block` (Pacifism) was already in this
  bucket, which settles the design question; its twin, the Aura that SHRINKS the creature, was
  never written, so Dead Weight, Debilitating Injury, Mire's Grasp, Stab Wound and 16 more
  scored zero roles. The non-Aura templating of the same effect (`target creature gets -N/-N`)
  is fully covered — 120 pool cards, no misses — G-67's exact signature. Also a live K-09
  violation, and how it was found: `tag_synergies` tags Dead Weight `removal` while
  `classify_roles` returned nothing. Guarded on `enchant creature you control` (Craving of
  Yeenoghu is a BUFF Aura whose recursion clause perpetually gains "-1/-1" — the one measured
  false positive), and the guard deliberately does not catch Duskmourn's Domination, whose
  "You control enchanted creature" is a Control-Magic steal in the other word order. Measured:
  20 newly classified, 0 false positives.
  K-14 ROSTER DIFF over all 113 decks: **0 decks moved a graded axis, 0 tier floors moved** —
  no deck currently runs one of the 29 cards, so the change is purely to the recommender's
  candidate set. Verified end to end: `deck.py suggest 38 --interaction` reports "SHORT (3 < 5)"
  and now offers Dead Weight (1-mana common, on-colour) where before it offered only mythics
  and rares. 9 tests added, fixtures verbatim from the cards (G-67).

BS6-01 | scripts/deck.py, scripts/card.py, scripts/pool.py, tests/test_deck.py | Front-face
  aliasing added to the three library-side ownership index builders that lacked it
  (`deck.load_collection` for BOTH `by_name` and `by_name_qty`, `pool.owned_counts`,
  `card._owned_index`), routed through `lib.alias_front` in a SECOND pass per G-63.
  `wishlist.owned_index` already had an equivalent pass and was left alone. `lib.owned_qty`
  resolves the full `A // B` name DOWN to a front key — right for the stated convention, and
  the convention is not what the data holds: 8 rows are stored under the FULL name (the DSK
  Rooms + two DFCs), so a query by the FRONT name returned 0 and `deck.owned` answered
  "NOT IN LIBRARY" for an owned card. Neither gate could see it: `check_agreement`'s ownership
  pair got the same wrong 0 from both implementations, and `check_dfc`'s completeness scan only
  walks builders that read card-pool.csv. Verified: all four surfaces now return 1 for
  "Funeral Room", and the shadowing guard holds (a real card named `Life` is not overwritten by
  `Life // Death`). 5 tests added, including one behavioural test across all four builders.

BS6-11 | CLAUDE.md | Corrected "the library stores the front only" to "MOSTLY stores the
  front", with the eight-row exception, the one-way-fallback symptom, why both gates were
  blind, and the fix. README already documented the exception correctly; the file every session
  auto-loads did not. Recorded the transferable lesson: `reconcile_crafts` and
  `import_collection` had each worked around this locally for years, and when two writers route
  around a documented rule, the RULE is the thing that is wrong.

BS6-02 | scripts/build_dashboard.py | Added a `[data-theme="light"]` block for the six mana
  tokens (`--W --U --B --R --G --Cc`). They lived in a bare `:root` with no light twin while
  `.hbar .track` (`--fill2`) flips to near-white, so the deck detail's "Color identity" bars
  and "Strict color requirements" pip bars painted cream on white. Same VALUES as
  build_gallery.py's light block, which fixed the identical bug in BS5-10 and wrote the rule
  down; the dashboard sibling was never brought along. The `-f` ink twins deliberately keep one
  value — they are dark inks on a chip that stays coloured in both schemes. Verified: every
  colour token that sits on a flipping surface now has a light value; the only tokens without
  one are the three font stacks and those six inks.

BS6-03 | scripts/build_dashboard.py | `attachHover(node, name, focusHost)` — the focus host is
  now explicit. By default it is the node itself, MADE focusable (tabIndex + an aria-label),
  which is what `craftNameCell`'s bare `.hovname` span needed; the leverage grid passes its
  already-a11y'd `.lev` card instead, so no second tab stop is nested inside a role="button".
  `focus` does not fire on a non-focusable element and does not bubble, so the S-7 guarantee
  ("the preview follows FOCUS") held only at the wishlist call site — and Scenario 7 walks
  exactly that one, so the check passed while two thirds of the feature was inert. Mouse
  behaviour is unchanged at all three sites. G-72's redraw trap does not apply: `craftNameCell`
  is a per-row `node:` factory that `sortableTable.redraw()` re-invokes on every sort.

BS6-06 | decks/73-dukes-vigil/deck.txt | Six land printings corrected to known ones, taken
  from `deck.py resolve`, never typed (G-65). The diagnosis is confirmed by the deck's own
  variant: 73a already carried the correct printings for all six cards, so one file in the
  family was resolved properly and the other hand-typed. Card NAMES and quantities are
  untouched — the diff is six set/collector pairs. `deck.py legal 73` is now clean and
  check_all's soft-warning section is empty for the first time this cycle.

TEST RESULTS: PASSED.
- `python3 scripts/check_all.py` — all invariants hold, **zero soft warnings** (was 1: the
  deck-73 unverified printings, cleared by BS6-06). 59s.
- `pytest` — 1333 passed, 1 skipped (was 1324 passed, 1 skipped; +9 = the 9 tests added here).
- Regression Scenario 2 (Analyze a deck) — PASS. All 13 per-deck subcommands, the roster-wide
  commands, all four `suggest --lands/--ramp/--interaction/--needs` paths, `screen`,
  `suggest-homes`, `pool.py --role`, `card.py`, plus `deck.py --help` and a subcommand help:
  no traceback, no unexpected exit code.
- Regression Scenarios 5, 6, 7, 8 — NOT RUN: all four require a person at a browser. 5 and 7
  are where BS6-02 and BS6-03 land and are listed under OPERATOR ACTIONS below.
- Scenarios 1, 3, 9 — NOT APPLICABLE: no ingest, enrichment or match-log path was touched
  (1 and 3 also need Scryfall).

REGRESSION RISKS:
- `load_collection` now returns front-aliased `by_name` and `by_name_qty`, so both dicts can
  hold up to 8 more keys. Checked every consumer (app.py ×2, build_dashboard, check_agreement
  ×2, check_all, deck.py ×12): all are LOOKUPS — no site iterates, counts or lens either dict.
  The two `for nl, q in qty_by_name.items()` loops in deck.py are DECK-derived, not the
  collection index. Same check for `pool.owned_counts` and `card._owned_index`: lookup-only.
- `alias_front` never overwrites an existing key, so no real card's count can change; pinned by
  a test.
- The two new role patterns can only ADD roles, and the roster diff measured zero movement on
  any graded axis or tier floor, so no deck's grade changed. Marginal cost measured at +0.19s
  on a roster-wide role pass (1.42s → 1.60s); check_all's 59s is pre-existing.
- `attachHover` gained a third parameter with a default, so the two unchanged call sites behave
  as before. The new tab stops on the craft table's card names are the intended cost of the fix
  and match what the wishlist table already does.
- `_ROLE_PATTERNS` is NOT part of `build_pool.tagger_fingerprint()` (it hashes tag_synergies.py
  plus `deck.ENGINE_THEMES`, which is what `tags_for` actually reads), so this change correctly
  does not stale card-pool.csv — verified the stamp still matches, so `make refresh` will not
  trigger a needless 15.9k-card refetch. `scripts/role_baseline.txt` needs no update either:
  it is scoped to owned/roster cards and none of the 29 fixed cards is owned — verified 0 stale
  entries, and `check_roles` reports no new zero-role cards.

INVARIANTS AT RISK: None.
- INV-01/INV-02: card-library.csv and card-mana.csv were not written.
- INV-03: no derived file was rewritten; gallery.html untouched. dashboard.html was rebuilt
  (it is not an INV-03 subject) so the BS6-02/BS6-03 fixes reach the committed artifact.
- INV-04: deck 73 was edited; check_all re-parses every deck file and every `(SET)` code, and
  passes — the previously-soft unverified-printing warning is now gone.
- INV-05/INV-06: no colour data and no synergy tags were touched.

NET SCORE: 6 production fixes − 0 new failure modes = 6
  a) Would it have fired in production this month? BS6-10 YES (the interaction recommender was
     already giving deck 38 a mythic-only answer to a deficit a 1-mana common fixes, and 6 decks
     under-count interaction via the neighbouring taxonomy class). BS6-01 NO — latent: no deck
     line currently names one of the 8 by its front face, though `card.py` would have under-
     reported one on any pre-grading read. BS6-11 YES (it is the false premise BS6-01 rested on
     and the file every session loads). BS6-02 YES for anyone using light mode. BS6-03 YES for
     any keyboard user. BS6-06 YES — the deck may not import into Arena.
  b) New failure mode introduced? NO for all six. The two role patterns were measured against
     the whole pool with the false-positive classes guarded and tested; the aliasing cannot
     overwrite a real key; the theme block only adds values; `attachHover`'s new parameter is
     defaulted; the deck edit changed no card names.

OPERATOR ACTIONS / DEPLOY:
- Regression Scenario 5 (light-mode colour), extended leg: open dashboard.html, press `t`, open
  a two-or-three-colour deck, and look at the Stats tab's "Color identity" bars and the Mana
  tab's "Strict color requirements" pip bars. Correct = every fill clearly visible against its
  track and the six colours distinguishable, in BOTH modes. | BLOCKS DEPLOY: N
- Regression Scenario 7 (keyboard traversal), extended leg: in dashboard.html, Tab to a card
  name in the roster CRAFT-PLAN table and to a card in the IMPACT grid — the card image must
  appear on focus, as it already does for a wishlist name. Re-check the craft table after
  clicking a sort header. | BLOCKS DEPLOY: N
- Deck 73's six corrected land printings are worth confirming with one real Arena import.
  | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push (no build step). The dashboard is the one
deployed artifact: `.github/workflows/pages.yml` rebuilds it and publishes to GitHub Pages on
every push to main, so BS6-02/BS6-03 reach the published page on merge. The committed
dashboard.html was rebuilt here (`make dashboard`) so the local copy matches.

FOLLOW-ON ITEMS:
- The TAXONOMY half of BS6-10, deliberately not touched: 128 pool cards whose effect is
  neutralization rather than destruction — 83 "doesn't untap during its controller's untap
  step" (tap-down) and 45 "loses all abilities" — carry no interaction role. SIX DECKS ARE
  LIVE-AFFECTED and under-count today (15 by 2; 16, 27, 32, 38a, 38 by 1). I checked each:
  none crosses a band right now, but deck 38 sits at interaction 3, exactly the B floor. This
  is the same open question as the Equipment bucket already on the handoff list — adding a
  bucket re-scores every deck running the type, so it is a decision to take deliberately.
- `check_dfc`'s registry-completeness scan only walks builders that read card-pool.csv, which
  is why BS6-01 was invisible to it. Widening the file predicate to library-shaped name indexes
  would make the gate cover the class rather than one instance. (Audit strategic suggestion 5.)
- `wishlist.owned_index` still carries a hand-rolled copy of the `alias_front` loop. Behaviour
  is identical, so it was left alone as out-of-scope refactoring — but G-63's rule is that
  aliasing has ONE home.
- `deck.py _clock_score` reads `vec.get("avg_mv") or 99.0` — the falsy-zero shape the repo bans
  elsewhere. Conservative in effect (no clock credit) and I could not construct a live case
  (BS6-12), so it was left alone.
- `card.py:_find` is dead code (zero references in scripts/ and tests/) whose docstring reads as
  live guidance about the shadowing bug BS-02 fixed (BS6-05).
- The committed dashboard.html has no freshness contract — nothing detects it going stale
  against the deck files (BS6-04). It happened to be three days stale at audit time and is
  current again now, but only because this session rebuilt it.
- `docs/systems-map.md` is marked LIVE with agreement rates measured 2026-07-29 against 64
  decks / 1,853 cards; the roster is now 111 decks / 2,368 printings.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md was updated in-session for BS6-11 (the "front only" claim). No other doc change is
  required: the four fixed patterns and the aliasing are described where the code lives, and
  `check_docs` passes.
- Two Regression Scenarios would be more honest with the extended legs written into CLAUDE.md
  rather than living only in this block: Scenario 5 needs the dashboard's mana bars added
  beside the gallery's (its current text covers only gallery colour bars), and Scenario 7 needs
  the craft-table and impact-grid card names added beside the wishlist name it already walks —
  that gap is precisely why BS6-03 stayed invisible. Suggest `/sync-docs`.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
