# Sultai legends pile (250 cards) — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the deck(s) are drafted and the findings are folded into
their `#: notes:` blocks. A scratchpad, not a source of truth — decks/ are.

**Source list:** `.cycle/sultai-pile-source.txt` (250 names; all resolve, all castable in UBG,
all Historic Brawl legal; 57 owned). No dedupe against existing decks: this pile builds NEW
decks, and a card already in another deck is still a candidate (copies are shared).

**Goal (owner):** the best 1–2 distinct Historic Brawl decks (possibly parent + variant) out of
a Sultai pile whose synergies include exile-to-win (Ashiok), self-mill + opponent mill, library
interaction (scry, enter/leave-library triggers, cast from opponents' library), reanimation,
cast from graveyard/exile, draw triggers, hand size, Elf tribal, land fetch, Mutate, Wizard
tribal, Descend, discard. Tentative commander: Thranduil, the Elvenking.

## 1. The decision framework

1. **The commander decides the deck.** Each candidate rewards ONE number, and every other card
   is graded against that number:
   - *Thranduil, the Elvenking* — ELF cards with activated abilities in the GRAVEYARD (he gains
     them) + LEGENDARY Elves entering (draw 2, discard 1). Wants self-mill/discard of Elves.
   - *Maralen, Fae Ascendant* — Elves/Faeries ENTERING (exile two of an opponent's library each)
     and the COUNT of Elves+Faeries (the free-cast MV cap). Cast-from-opponent's-library + Elves.
   - *Glarb, Calamity's Augur* — TOP of library (play lands, cast MV ≥ 4 from the top; tap to
     surveil 2). Library manipulation; MV ≥ 4 is an UPSIDE here, not a cost.
   - *Muldrotha* / *Kotis, Sibsig Champion* / *Teval* / *Sidisi* / *Mimeoplasm* / *Sin* —
     GRAVEYARD as a hand (cast permanents back, reanimate, token-on-leave). Self-mill is fuel.
   - *Gonti, Canny Acquisitor* / *Kotis, the Fangkeeper* — cast cards you DON'T own (combat
     damage → steal from their library).
   - *Yarok* (enters-trigger doubler), *Brokkos* (mutate), *Nashi, Moon's Legacy* (legendary
     recursion), *Leovold* (stax/draw lock) — narrower.
2. **Two-deck hypothesis to test, not assume:** (A) a GRAVEYARD deck — self-mill → recast /
   reanimate / descend, discard as enabler; (B) a LIBRARY/EXILE deck — opponent's library
   (exile-to-win, cast their cards, opponent mill only as fuel), top-of-library and scry
   triggers, draw triggers, hand size. Elves attach to whichever commander rewards them.
3. **Tribe viability is the PAYOFF count (G-59), measured on the pile:** Elf 22 bodies / ~10
   payoff texts → a sub-theme under an Elf commander only. Wizard 20 bodies / 2 payoffs → NOT a
   theme. Mutate 1 card → NOT a theme (Brokkos is a recursive threat, nothing more).
4. **What the deck PAYS vs what is printed:** in a graveyard deck a permanent's real cost is its
   recast-from-graveyard route (Muldrotha: one of each permanent type per turn); grade big
   permanents on effect. Under Glarb, MV ≥ 4 casts from the top for free card advantage.
5. **Mill polarity (G-62/G-42):** self-mill FEEDS deck A and is neutral-to-bad in deck B; blind
   opponent mill is a CLOCK, not interaction — it only scores in deck B where exiled/milled
   opponent cards are a resource (cast them, or count them for an exile win).
6. **Graveyard hate fights deck A (G-42):** anything exiling YOUR graveyard is a cost there; an
   exile-their-graveyard effect is fine in both.
7. **Legends are free:** 236 of 250 are legendary, so "legendary matters" (≈25 payoff texts:
   Thranduil, Nashi, Tamiyo, Price of Fame, the copy/clone family) needs no build-around.
8. **The pile is SHORT on interaction:** 23 counted interaction pieces in 250 cards, 56 card
   advantage. A 100-card deck needs 12 interaction for the A floor (scaled), so each deck's
   removal will mostly come from OUTSIDE the pile (`suggest --needs` at draft time). A pile card
   that IS interaction gets a bonus; do not cut one for a marginal engine card.
9. **Lands and ramp come from outside the pile** (it holds two MDFC lands). The deliverable is
   the ~55–63 nonland CORE of each deck; the draft fills the rest.
10. **Ownership is information, never a gate** (Player Profile): 57 owned.

## 2. Standing error list

(empty — filled as batches find misreadings)

## 3. Cross-batch observations

(empty)

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.
Columns: deck A = graveyard, deck B = library/exile; `Elf` marks a legendary Elf body.

## 5. Consolidated plan (live)

(after the batches)
