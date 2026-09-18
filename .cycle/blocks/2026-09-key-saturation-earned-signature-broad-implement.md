---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- KEY saturation in `fit_strength` (filed 2026-09-17 in `.cycle/NEXT-SESSION.md` as a
  CONTROL-FLOW defect, not a data gap). The signature branch is the function's FIRST
  statement and excluded `_GENERIC_TRIBES` but not `GENERIC_THEMES`, so any theme carried
  by >=2 of a deck's `#: protect:` cards minted KEY for every card sharing it.

Files modified: scripts/deck.py, scripts/check_suggest.py, tests/test_deck.py

CHANGES:
| scripts/deck.py | New `structural_overlay_hit(card_text, cards, carddata)` — one shared
  predicate (G-70) routing through the doubler / cost-scale / type-scale primitives
  `suggest-homes` and `cut_keep_score` already use, never a second copy of any of them.
| scripts/deck.py | `fit_strength` gains an optional zero-arg `overlay` predicate and the
  signature branch splits in two: a SPECIFIC signature theme still mints KEY on its own; a
  GENERIC one mints only when the card clears a structural overlay, and otherwise FALLS
  THROUGH to the branches below rather than being forced down. The function stays pure —
  the overlay is supplied by the caller.
| scripts/deck.py | All THREE callers wired in the same change (`cmd_screen`,
  `cmd_suggest_homes`, `cmd_quality`), per G-40: a pure-function anchor cannot see whether
  a caller asks, and that is this repo's recurring failure shape.
| scripts/check_suggest.py | Anchor 11b's RATIONALE corrected (see below) and anchor 11c
  added — both halves of the branch, pinned: a generic non-spine signature must not mint,
  and an overlay must earn it back. Watched-it-fail against a regressed implementation.
| tests/test_deck.py | `test_the_signature_rescue_is_preserved`'s docstring re-grounded,
  plus 5 new pins (generic-non-spine, overlay-earns-it-back, specific-still-mints,
  overlay-optional).

THE REJECTED-FIX CHECK, which is why this took measuring rather than typing:
`tests/test_deck.py` pinned a REJECTION — "a tightening was TRIED and rejected: requiring
a non-generic signature theme dropped deck 30's KEY rate 21% -> 1% and demoted Innkeeper's
Talent". Found by scanning test doubles before editing, as the skill instructs. That
rejection STILL STANDS and the pin is kept; this is a different change:
  - the rejected one REMOVED the branch's effect; this one makes it CONDITIONAL, and when
    the condition fails the card falls through to branches that can still return KEY.
  - Re-measured on the deck the rejection was taken on: **deck 30's KEY rate does not move
    at all — 27.7% before and after.**
  - The named casualty SURVIVES: Innkeeper's Talent and Branching Evolution keep KEY
    through the overlay; Kami of Whispered Hopes / Conclave Mentor / Ozolith keep it
    through `top-theme`, because where `counters` really is the spine it is also the top
    theme. `check_suggest`'s old 11b comment ("the strictness cannot live in the function")
    was measured wrong — even with the STRICT signature the branch minted 97.3% of every
    KEY — and its warning about asserting `signature={"etb"}` == tangential confused this
    with the rejected tightening; nobody makes that assertion.

MEASUREMENT — aggregate, via a mirror validated to reproduce the filed baseline exactly
(p50 8; signature 97.3% against the filed 97.2%), 400-card sample x 112 decks:
  KEY 18.6% -> 10.2%; KEY decks per card p50 **8 -> 4**, p90 17 -> 10, max 35 -> 26.
  The dead branches come ALIVE: `top-theme` 1.2% -> **63.8%**, `role-gap` 1.5% -> **8.8%**.

MEASUREMENT — LIVE AT EACH OF THE THREE CALLERS (G-40's rule), against a harness running
the pre-change `deck.py` from HEAD with `lib` resolved from the real repo:
  - CALLER 1 `suggest-homes`, 12 cards: KEY **93 -> 73**, role-player 100 -> 120,
    tangential **289 -> 289, IDENTICAL**. Nothing is demoted to "not for this deck"; the
    change only distinguishes KEY from role-player. Innkeeper's Talent 24 -> 24 and
    Doubling Season 22 -> 22 (the doublers are untouched); Inspiring Overseer 14 -> 7,
    Treasure Dredger 13 -> 6, Phyrexian Arena 7 -> 4.
  - CALLER 2 `screen`: the first sample (decks 30/41/20) showed ZERO change, which would
    have been a VACUOUS pass — the G-63 lesson about a probe the index cannot hold. So the
    population was measured: **42 of 112 decks** carry a generic signature theme that is
    not their top theme, which is where the path bites. Re-run on 8 of those, **5 moved**
    (deck 37 KEY 5 -> 0, deck 39 4 -> 0, deck 29 4 -> 1, 42a 4 -> 3, 36 3 -> 2), tangential
    invariant in every one.
  - CALLER 3 `quality --add`: its warning fires on TANGENTIAL, which is invariant, so it is
    **unchanged** — verified on three (deck, card) pairs rather than argued.

SPOT-CHECK that the demotions are right, not just fewer: deck 37's spine is `spellslinger`
and its signature also holds `card draw`/`evasion`/`flying`. After the change its real
payoffs (Sprite Dragon, Third Path Iconoclast, Young Pyromancer) still read KEY while
Deep-Cavern Bat — a generically-good lifegain flier — drops to role-player. That row is
the saturation in one line.

TEST RESULTS: passed.
- `python3 scripts/check_all.py` — "All invariants hold. ✓", exit 0, soft warnings
  IDENTICAL to the pre-change baseline.
- Full `pytest` — exit 0, no failures, no skips.
- `check_suggest.py` — OK, including the pre-existing anchors 11 and 11b.
- WATCHED-IT-FAIL: a deliberately regressed `fit_strength` (mint on any signature hit)
  makes anchor 11c fire and the gate exit 1.
- DETERMINISM (G-54): `suggest-homes` byte-identical across PYTHONHASHSEED 0/1/12345.

REGRESSION RISKS:
- `fit_strength` gained a keyword-only-in-practice 7th parameter with a default, so every
  existing call remains valid; the three in-repo callers are all wired.
- An UNWIRED future caller gets the conservative fall-through (no mint) rather than a KEY
  nothing checked. That is a deliberate default and is pinned.
- Is there a case where the old behaviour was right? Yes, exactly one — the G-33 rescue —
  and it is preserved, measured on the deck the earlier rejection was taken on.
- `_HOMES_KEY_SATURATED` / `_SCREEN_KEY_SATURATED` still exist and still warn. They were
  shipped INSTEAD of a re-score; they are now a backstop behind one.

INVARIANTS AT RISK: None. No CSV, no deck file and no derived artifact is written.
INV-01, INV-01b, INV-02, INV-03 and INV-04 are untouched; `check_all` confirms.

NET SCORE: 1 − 0 = 1
- Would it have fired this month? YES. It fired in this session's own deck-41 work: the
  user asked whether more granular card data would make fits more discriminating, and the
  answer was that the bottleneck is here, not in the data.
- New failure mode: NO. Tangential is invariant at every caller, so no card becomes
  "probably not for this deck"; the change only separates KEY from role-player. The one
  new surface — an unwired caller — defaults conservative and is pinned.

OPERATOR ACTIONS / DEPLOY:
- None.
Deploy: Presentation — `.github/workflows/pages.yml` republishes `dashboard.html` on push
to `main`. `build_dashboard.py` does not call `fit_strength`, so the published page is
unchanged; the push rebuilds it regardless.

FOLLOW-ON ITEMS:
- The saturation WARNINGS now sit behind a fix rather than in place of one. Whether
  `_HOMES_KEY_SATURATED = 0.15` is still the right threshold against the new distribution
  (p90 dropped 17 -> 10) is a re-derivation nobody has done — the `TIER_FLOOR_REQ` hazard.
- The relational gap filed alongside this one is UNTOUCHED and is the bigger half of G-22's
  median-424: card x card relations no per-card category encodes (Seek the Heart ranked 645
  for deck 41 because "tutors a legendary creature" plus "this deck's payoff IS a legendary
  creature" is a relation between two cards). `deck.py targets` is the primitive; G-40
  governs any wiring of it into a ranking.
- `structural_overlay_hit` swallows exceptions from each primitive so one bad card cannot
  break a whole roster pass. That is deliberate but it does mean a primitive that starts
  raising would degrade silently to "no overlay".

DOCUMENTATION UPDATES NEEDED:
- G-31 (suggest-homes) should record that a generic signature theme must now earn its KEY,
  and what that did to the distribution — its current text describes the saturation WARNING
  as the remedy.
- `.cycle/NEXT-SESSION.md`'s open finding is now CLOSED and must say so, with the result,
  or a fresh session will re-derive it — the file is declared authoritative over everything
  below it.
- The measured figures cited in any CLAUDE.md rule need `check_docs.figure_drift` entries.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
