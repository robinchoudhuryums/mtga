# Builder — picks workflow plan (TEMPORARY working doc)

**Status: Batches 0, A and B DONE (2026-11-02); C open.** Delete once the batches land (the record is
`.cycle/blocks/`). Written 2026-11-02 after per-deck Bench / Keep out landed (commit 179b244).

The owner's workflow, in their words: mark adds or bench, go to the deck's list and mark cuts,
go back and forth until a swap package feels right. Today the cut step is a native `<select>`
(no card text, no image), and in Compare, clicking a deck card to read it replaces the selected
pile card, so reading a cut and pairing it fight each other. Batch A fixes that first.

## Batch 0 — per-deck verdict stars (added 2026-11-02, before A)

The pile-analysis legend (`★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal ·
✗ out`) exists per card per deck in `.cycle/sultai-pile-analysis.md` §4 for the 250 original
pile cards (column A → Thranduil, B → Glarb) — it is what placed them in piles — but the board
never received it. The board's reasons carry a verdict only as loose prose ("**Strong add.**",
a trailing ◇) in ~15 of 292. The 176 outside-the-pile cards have no star at all.

- **0a Data.** A per-deck verdict on each reason in build.json (`v: {T: "★★", G: "◇"}`, hand
  content, stamped like the reason). `builder.py verdict <slug> <card> <deck> <mark>` sets one;
  `check` reports a card with a reason but no verdict.
- **0b Import.** The 250 from §4, recorded as graded before the decks were drafted (column A was
  graded against the graveyard shell, before Thranduil's "a non-Elf has to beat an Elf" rule),
  so the page marks them "pre-draft".
- **0c Grade the rest.** Full-text grades for the 176 unstarred cards against the current
  lists, and a re-grade of every Thranduil grade whose reason leaned on Elf-ness — under the
  owner's synergy-first rule (sultai-pile-analysis §10, 2026-11-02): synergies first, Elf as a
  tiebreaker. Runs AFTER the owner settles the §10 list changes, so grades read the new list.
- **0d Page.** A star badge beside each deck's button on the row and in the pane (with the
  legend); filter "verdict for <deck> at least …"; sort by verdict; the loose prose verdicts
  stay in the reason text.

## Batch A — choosing cuts (the back-and-forth)

- **A1 Cut picker with card previews.** Replace the pane's "this replaces" `<select>` with a
  panel: the deck's nonland cards in `cuts` order, each row with thumbnail, rank, roles and the
  first line of its reason. Hover or keyboard focus shows the full card (the existing peek,
  allowed while the pane is open); Enter or click sets the pair; a Compare button opens the
  side-by-side dialog. Protected cards stay listed last. A search box filters the list.
- **A2 Inspect without losing the selection (Compare tab).** Clicking a deck-column card shows
  it in a second "Cut candidate" slot in the pane under the selected pile card, instead of
  replacing it, so ⇄ stays live. Esc clears the slot.
- **A3 Package view (Compare tab).** A pile option "My adds for <deck> with no cut yet", and a
  tray above the deck column listing this deck's package: paired add → cut, unpaired adds
  marked "needs a cut", cuts with no add. Clicking a tray entry selects it.
- **A4 Say when an add has no cut.** A "needs a cut" chip on the row and in the pane, and
  "N adds need a cut" in the deck strip. The projected size already shows the overflow
  (e.g. 100 → 103); the chip says why.

## Batch B — the five approved improvements

- **B1 "Undecided for <deck>" filter.** A card is decided for a deck when it carries Add, Cut,
  Bench or Keep out for that deck. Filter option per deck; each pile tab shows decided/total for
  the pile's own deck (a shared pile counts a card decided only when every deck is decided).
- **B2 Bulk mark the shown list.** "Mark all shown: Bench in / Keep out of <deck>" under the
  toolbar, with a confirm naming the count, skipping cards already in that deck, one undo step.
- **B3 One undo step per gesture.** `b` / `o` on a shared pile and bulk marks snapshot once
  (an undo entry holds several cards).
- **B4 "Move to pile …" request.** A pane control queues a request (the existing `requests`
  collection, dest `move:<pile>`); `/pile-analysis` Stage 6 processes it with
  `builder.py place` and re-checks the card's reason. Shown in Add cards → Requests.
- **B5 Bench lists persist in the deck file.** New writer `deck.py flex <id> --add "+Card |
  BENCH (builder <slug>): <note>" [--apply]` — dry run by default, `.bak`, INV-04 re-check,
  refuses a card already in the deck or already on a `#~` line. `builder.py picks` emits these
  lines for each deck's bench list, and `/apply-changes` Stage 0 applies them with the swaps.
  `flex_staleness` already retires a `+In` line once the card is maindecked (G-04).

## Batch C — more than two decks, and one

Measured 2026-11-02 on scratch 1-deck and 3-deck builds: both render with no errors, piles,
buttons, pane and Compare work. Gaps:

- **C1 Pile labels by deck count.** "Either deck" → "More than one deck" at 3+; "Fits neither"
  → "Doesn't fit" (1 deck) / "Fits none" (3+). Set at `new_build` / `add_deck`, existing
  builds keep their stored labels.
- **C2 Unique button letters.** Row buttons show the label's first letter, so two decks with
  the same initial (two Thranduil variants) read "+T +T". Use the deck KEY, which is unique.
- **C3 Distinct deck colours.** Two decks with the same colour identity get the same accent;
  assign from a palette when identities collide.
- **C4 Four or more decks.** The row grid widens past the name on a phone; above three decks,
  collapse Bench / Keep out into a per-row menu and keep the deck toggles.
- **C5 Tests.** Render smoke for 1- and 3-deck builds (no JS errors, expected piles and
  buttons) in `tests/test_builder_template.py`.

## Order and size

0 (verdict stars — the owner is mid-review of the piles) → A (cut choosing, the daily friction) → B → C. Each batch: tests, browser walk, render and
republish the board, block in `.cycle/blocks/`, commit.
