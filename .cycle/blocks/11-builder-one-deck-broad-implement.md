---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Builder one-deck items 1-4 (from the 2026-11-02 single-deck review)
  1. Compare is the home view of a one-deck build; the pile tabs become a Pile menu in the toolbar; the deck picker and "Search both" are gone
  2. The deck panel is live: the mana curve (now vs after picks) and the distance to the next tier sit beside the figures and the mark counts
  3. No deck letter on any control: + Add / Bench / Keep out / − Cut, verdict tags without the key, a one-row pick block in the pane, plain labels everywhere they show
  4. Fewer filters: Verdict and Decision lose their per-deck options, Sort reads "Verdict", the "In list" filter is dropped (see CHANGES)
Files modified: scripts/builder_template.html, tests/test_builder_template.py

CHANGES:
1 | scripts/builder_template.html | `ONE = DK.length===1`. PILES leaves out the pile tabs, so Compare is PILES[0] and loads first. On one deck the toolbar shows on Compare, and `toolbarFilter()` (split out of `filtered()`) filters and sorts the candidate column, so the verdict, role, reason, mana-value, owned and rarity filters and the bulk mark all work there. Search covers both columns. The Pile menu sits in the toolbar after Search and stays visible on a phone (`label.keep`); each option shows its pile's decided count, refreshed by `updateTabCounts`. The count line reads "N shown · d/m decided". An old `#pile-x` link opens Compare with that pile chosen. A "Your picks" link selects the card on the left, or inspects it on the right when it is in the deck. Bulk marks target the candidate column. `/` focuses the toolbar search.
2 | scripts/builder_template.html | On one deck `renderDecks` puts the figures, the next-band line and the protected list beside a compact `curveHTML(k)` (`.onegrid`, stacked below 760px). The panel re-renders on every pick, as it already did. Compare's right column keeps only the swap package and conflicts, since the curve and figures moved up.
3 | scripts/builder_template.html | `quick()` has a one-deck branch: "+ Add" on top, then Bench and Keep out (icon plus word; icon only under 520px), or "− Cut" for a card in the list. Tags read "In the deck" / "Protected", with verdicts without the key and "needs a cut" without the key. The pane's pick block drops the deck label, the hint lines drop the per-deck wording, and inspect reads "− Cut". `PICKLAB` (the shown labels) leaves the deck out on one deck. The new `FULLLAB` keeps the deck-named labels, and Copy as text uses FULLLAB, so the copied block and `builder.py picks` are unchanged.
4 | scripts/builder_template.html | The Verdict options read "★★ or better" and so on with no optgroup; Decision is Any / Undecided; Sort reads "Verdict". The "In list" filter is HIDDEN on one deck rather than reduced to In deck / Not in deck: once Compare is home, the left column already excludes the deck's cards and the right column is the deck, so that filter would change nothing (a deviation from the item's wording, noted here).
tests | tests/test_builder_template.py | `_HARNESS_QUICK` defines `ONE`/`K1`, since `quick()` now reads them. New: TestOneDeck (Node: the row buttons' words, values and aria-labels on one deck) and TestOneDeckMarkup (copy uses FULLLAB, PILES drops the pile tabs, old pile links, the curve moved to the deck panel).

TEST RESULTS: passed. Full pytest suite green; check_all OK, 5 soft (unchanged). Browser walk on a scratch one-deck copy of the Sultai build (Glarb only, deleted afterwards):
- Compare loads first, with 4 tabs, the Pile menu showing per-pile progress and no deck picker.
- After an add, the header reads card adv. 17 → 18 and the curve "+1 at 3"; pairing it with ⇄ cuts Dictate (the curve goes back to unchanged, crafts 66 → 65).
- The verdict filter gives 24 shown, and the search covers both columns.
- `#pile-n` opens Compare on Fits neither.
- Copy as text still writes "Add to Glarb:" and the swap --package line.
- 390px: no sideways scroll, and the Pile menu is visible with the filters folded.
- Sultai (two decks) unchanged: pile tabs, +T/+G, verdict optgroups, Compare with its deck picker and curve, no curve in the header.
- No page errors on either page.
Scenario 25 is perceptual and still needs a person.
REGRESSION RISKS: The multi-deck code paths are gated on `!ONE` and were walked unchanged. On one deck a toolbar change re-renders the whole Compare view, so its columns scroll back to the top, as a pile view's list already did. The one-deck "Your marks" count does not include cuts chosen by pairing, which is pre-existing on two-deck boards too.
INVARIANTS AT RISK: None. Template only; no data, deck or CSV writer touched.
NET SCORE: 0 production fixes − 0 new failure modes = 0 (a UX change for a build shape that has not shipped yet; Defensive)

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds the Builder pages on push to main (the Sultai board is two-deck, so its page is unchanged)

FOLLOW-ON ITEMS:
- Item 5 (group the pile by verdict instead of separate pile tabs/menu) — the user asked for it as the next batch
- On a phone, a re-render after a pick collapses an opened deck panel (`renderDecks` re-renders it collapsed when narrow). It is pre-existing, but more noticeable now that the panel holds the curve.
- "Your marks +a / −c" counts only explicit Cut marks, not cuts chosen by pairing (pre-existing, both modes)

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-89 and docs/gotchas.md G-89: a one-deck build opens on Compare with the piles as a filter
- README Builder section and docs/systems-map.md §5c: the one-deck layout
- Regression scenario 25: a one-deck walk (Compare home, Pile menu, header curve)
---END BROAD SCAN IMPLEMENTATION SUMMARY---
