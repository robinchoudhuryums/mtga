---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch A of .cycle/builder-picks-plan.md — choosing cuts
- A1: cut picker with card previews in the pane (replaces the native <select>)
- A2: Compare inspect slot — a deck card opens in a second pane slot; the selected pile card stays selected
- A3: package view — Compare pile option "My adds for <deck> with no cut yet" + a swap-package tray
- A4: "needs a cut" chip on rows and in the pane; "N need a cut" in the deck strip
Files modified: scripts/builder_template.html, tests/test_builder_template.py, README.md, .cycle/builder-picks-plan.md, .cycle/board/index.html

CHANGES:
A1 | scripts/builder_template.html | `cutPickerHTML` replaces `pairSelects`: per deck the card is added to, the current cut (thumbnail, rank, verdict, ✕ clear, Compare) or a "needs a cut" chip, and a "Choose a cut" toggle opening the deck's nonland list in cuts order (protected last) — thumbnail, rank, name + pips, roles, the deck's verdict, "already the cut for X". Hovering or focusing an option fills a FIXED-HEIGHT preview (image, type, rank, verdict, rules text with symbols, reason, Compare side by side); clicking sets the pair (`setPair`, one undo step, toast); a search box filters in place; ↑/↓ move through the list, Esc closes it — handled before the dialog guard so it works in the phone sheet too. The `select.pair` change handler and `compareBtns` are gone (the picker carries both).
A2 | scripts/builder_template.html | `INSPECT` state: in Compare, clicking a deck-column row (or j/k while in that column) calls `inspect()` — SEL stays the pile card, the pane appends `inspectHTML` (image, rank, verdicts, rules, reason, "⇄ <pile card> replaces this", Compare side by side, − Cut) and scrolls to it; ✕ closes it. The deck row highlights from INSPECT, the pile row from SEL. On a phone the sheet opens on the deck card without moving SEL (`SHEETID`). render() no longer moves SEL onto a deck card when the pile list is empty-filtered; INSPECT clears on deck change.
A3 | scripts/builder_template.html | `packageOf(k)` (paired / unpaired / cuts with no add, pending only, applied excluded) feeds a "Swap package" tray atop the deck column (add → cut with Compare, "needs a cut", lone cuts) — names jump to the pile card or open the deck card in the inspect slot — and the new pile option filtering to adds with no cut.
A4 | scripts/builder_template.html | `needsCut(id,k)` drives a "needs a cut · T" row chip; the deck strip's summary and key figures show "N need a cut".

TEST RESULTS: full pytest suite passed (rc=0), incl. a new Node test of packageOf/needsCut (paired, unpaired, lone cut, an applied add excluded). check_all OK, 5 soft. Browser walks: desktop — add with no cut shows the chip, the list opens, hover previews, search narrows 12, a click pairs (toast, strip count), Compare "no cut yet" filter, deck-column click keeps Kishla selected while inspecting Infernal Grasp, j moves the inspected card; phone 390 px — the sheet's cut list, ↑/↓ focus with the preview following, no sideways scroll. Two bugs found and fixed in the walk: the preview grew per card and moved the list under the pointer (hover jitter → fixed height), and arrows did nothing in the phone sheet (the dialog guard ran first).
REGRESSION RISKS: (1) Clicking a deck-column card in Compare no longer selects it — the pane keeps the pile card and shows the deck card below; keyboard number keys still act on the pile card. (2) Removing the <select> removes its native keyboard semantics; the list's buttons are Tab/arrow reachable instead.
INVARIANTS AT RISK: None — page-only; no data or deck file is written.
NET SCORE: 0 production fixes − 0 new failure modes = 0 (new capability; two bugs caught before shipping).

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation: `.github/workflows/pages.yml` publishes on the next merge to main; the claude.ai board is republished (artifact v24).

(Not complete in production until blocking operator actions are done AND
the deploy step is confirmed.)

FOLLOW-ON ITEMS:
- Scenario 25 could gain the cut-list and inspect steps when docs are next synced.
- Ulamog, the Ceaseless Hunger is in Glarb's list at ◇ (from the re-grade) — a cut to consider.
- Next plan batch: B (undecided filter, bulk marks, one-step undo for b/o, move-to-pile request, bench → #~ flex lines).

DOCUMENTATION UPDATES NEEDED:
- README Builder paragraph updated; regression scenario 25 steps could name the cut list (sync-docs).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
