---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Builder one-deck item 5: on a one-deck build, Compare's candidate column is grouped into verdict sections, best first, with ✗ collapsed at the bottom
Files modified: scripts/builder_template.html, tests/test_builder_template.py

CHANGES:
5 | scripts/builder_template.html | Items 1–4 already put the piles in a Pile menu, so item 5 groups the candidate column instead of merging tabs.
  - `verdictSections(xs, k)` groups cards by this deck's verdict: ★★★ ★★ ★ ◇ △, then "No verdict yet" (no mark, another deck's mark, or an unknown mark), then ✗. Empty sections are dropped, and the toolbar's sort order is kept inside each section.
  - `cmpLists` returns the sections. COLIDS.L, which j/k, the count and bulk marks read, leaves out the cards in collapsed sections.
  - `vsecHTML` draws each header as a button with aria-expanded, a caret, the label and a count. The header stays pinned while its cards scroll (desktop).
  - `VCOLL` holds the collapsed sections. It starts as {✗} and is remembered in `builder-prefs` (`savePrefs` now writes `vcoll`).
  - The count line reads "N shown (+M collapsed) · d/m decided".
  - `revealCand()` opens a card's section before a jump lands on it (Your picks → card, the swap-package add link).
  - Sort loses its "Verdict" option on one deck, since the sections now order by verdict. A build where every card is ungraded shows one plain list with no header.
  - All of it is gated on `ONE`. Two-deck pages are unchanged: no sections, and Sort keeps "Verdict — Thranduil/Glarb".
tests | tests/test_builder_template.py | New: TestVerdictSections (Node: section order, ungraded before ✗, sort order kept inside a section, another deck's verdict counts as ungraded) and TestVerdictSectionMarkup (✗ starts collapsed and the choice is remembered; collapsed cards are left out of what j/k and bulk marks read; jumps open the section).

TEST RESULTS: passed. Full pytest suite green; check_all OK, 5 soft (unchanged).

Browser walk on a scratch Glarb-only copy of the Sultai build (deleted afterwards):
- Opens with six sections (★★★ 1, ★★ 23, ★ 73, ◇ 81, △ 104, ✗ 58 collapsed) and "282 shown (+58 collapsed)".
- Opening ✗ shows all 340 and keeps focus on the header.
- Collapsing ★★★ survives a reload.
- j from the last shown card wraps to the first and never lands in a collapsed section.
- Opening a ✗ card from Your picks expands ✗ and selects it.
- With the Pile set to Fits neither, it shows 5 sections and 245 cards.
- Two-deck Sultai: no sections, Sort options unchanged.
- No page errors.
REGRESSION RISKS: On one deck, the "Hide marked" filter and the sections compose: marking a card in a section removes it from that section, as before. A card selected in the pane and then collapsed away stays in the pane until the next render. Two-deck code paths take the `secs` = undefined branch and render exactly as before.
INVARIANTS AT RISK: None (template only).
NET SCORE: 0 production fixes − 0 new failure modes = 0 (a UX change; Defensive)

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds the Builder pages on push to main

FOLLOW-ON ITEMS:
- The phone deck-panel collapse on re-render, and "Your marks" not counting paired cuts (both carried from the items 1–4 block)

DOCUMENTATION UPDATES NEEDED:
- Together with items 1–4: CLAUDE.md G-89 and docs/gotchas.md G-89, README Builder section, docs/systems-map.md §5c, and regression scenario 25 (a one-deck walk: Compare home, the Pile menu, the header curve, verdict sections with ✗ collapsed)
---END BROAD SCAN IMPLEMENTATION SUMMARY---
