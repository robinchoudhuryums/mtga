---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (Batch E — interface access, the structural Stage-3 findings):
- S-2 | dashboard tab strips carried role="tab" with no tablist/tabpanel/aria-controls — the exact invalid-ARIA shape test_templates pins the EDITOR against, on the side with no test
- S-4 | the collection editor's toast — the sole reporting channel for five actions, two destructive — was not a live region; failures announced nothing
- S-5 | collection.html had no <main> landmark, and the landmark test explicitly excluded it (the one failing page)
- S-6 | removing a deck row / metadata field rebuilt the container and threw keyboard focus to <body> — four cuts = four full page re-traversals
- S-7 | the card-image hover preview (the EVIDENCE for a craft decision — G-52 in interface form) was mouse-only on keyboard-focusable controls
- S-10 | the ＋ Add card disclosure exposed no expanded state; ~2k remove buttons announced identically with nothing naming the card
- S-11 | /decks rendered a blank page on an empty decks/ — no explanation, no pointer at the ＋ New deck button

Files modified: scripts/build_dashboard.py, dashboard.html (rebuilt), templates/collection.html,
templates/deck.html, templates/decks.html, tests/test_templates.py

CHANGES:
S-2 | build_dashboard.py | new `tablist(strip, panel, label, pid)` completer: container role="tablist" + aria-label, panel role="tabpanel" with an id, aria-controls on every tab, Left/Right arrow navigation, and aria-selected kept live across clicks (the strips don't rebuild on switch). Wired at BOTH strips (deck-card detail, modal). Source-pinned by 2 new tests.
S-4 | collection.html, tests | toast gains role="status" aria-live="polite" with the same rationale comment deck.html has carried since I-04; the live-region test now covers BOTH files.
S-5 | collection.html, tests | the grid div is a <main>; the landmark test includes collection.html (the pin's hole was shaped exactly like the failing file).
S-6 | deck.html | both remove handlers restore focus after the rebuild — the same-index ✕ (the next line slides up), else the last, else the Add button — the pattern addRow already used on the constructive path.
S-7 | build_dashboard.py | attachHover mirrors mouseenter/mouseleave with focus/blur, positioned from getBoundingClientRect (no cursor on a keyboard).
S-10 | collection.html, tests | addToggle carries aria-expanded (kept live) + aria-controls; every ✕ is aria-label'd "Remove <name> (<set>) from the collection" (built in the JS literal, so the pin is a source assertion). 2 new tests.
S-11 | decks.html | zero decks renders an .empty explainer pointing at ＋ New deck, matching collection.html/gallery's idiom.

Then, per the same instruction, the accumulated /sync-docs pass (committed separately):
README (verify_ingest reads collection CSVs; query --min-owned sums / --count counts distinct cards; --budget shows the same ⚠rot + pow flags as --rank), CLAUDE.md (C-07 test inventory → 27 files naming the two new layers; Scenario 4 gains the 409-on-concurrent-change expectation), docs/gotchas.md (G-08 + the BS2-10 same-deck claim guard; G-63 + the Batch A/B member closures and the alias-registry completion).

TEST RESULTS: 1022 passed (1018 + 4 new template/source pins), 0 failed. check_all + check_docs green, zero soft warnings. dashboard.html rebuilt with the tablist/preview changes. Scenario 7's MARKUP half re-pinned and green; its perceptual half (visible focus ring on the new focus targets, arrow-key feel, screen-reader announcements) remains the operator's browser walk — the walk got shorter, not longer.

REGRESSION RISKS:
- tablist() adds arrow-key handling to strips whose tabs are already Tab-reachable — Left/Right now also switches tabs (activation-on-focus, the simpler of the two canonical tab patterns).
- The focus-restoration targets on remove are best-effort queries; if the row classes are renamed the focus falls back to the Add button rather than <body>.
- decks.html's `if (!decks.length) … else` guards only the empty branch; the populated path is byte-identical.
- No Python behavior changed anywhere in this batch (build_dashboard edits are inside the JS template string).

INVARIANTS AT RISK: None. INV-03's artifacts rebuilt through their builders.

NET SCORE: 7 − 0 = +7
(All seven were live for any assistive-tech or keyboard user on every page load; S-2/S-4/S-5 additionally repair pins whose holes matched the failing surfaces.)

OPERATOR ACTIONS / DEPLOY:
- Walk the perceptual halves of Scenarios 5–8 (plus the new arrow-key tab feel and the focus-restoration path) at a browser | BLOCKS DEPLOY: N
Deploy: commit/push is the deploy; pages.yml republishes the rebuilt dashboard on merge to main.

FOLLOW-ON ITEMS:
- Batch F (editor theming + phone width) is the remaining interface batch — S-3/S-8/S-9.
- Batches G–H unchanged; BS2-07 header-consumer sweep still standing.

DOCUMENTATION UPDATES NEEDED:
None — the accumulated notes were applied in this same pass (see above); nothing new accrued.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
