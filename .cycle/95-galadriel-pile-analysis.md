# Deck 95 Light of Valinor pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into deck
95's `#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Source list:** owner's pile part 1 (85 names) + the earlier consideration list (16),
resolved to 100 cards after removing three deck 95 already runs (Denzilore Fatehold,
Thassa, Deep-Dwelling, Soulherder). Part 2 of the pile is still to come. "Arwen" expanded
to the four Arwen cards; "Ob Nixilis" read as Ob Nixilis, the Ascended (the white one);
"Tocasia" as Tocasia, Dig Site Mentor. Daxos of Meletis is not on Arena (not in the pool).

## 1. The decision framework

Live vector (2026-10-30, after the lifegain package): floor B; interaction 9 (A needs 12
at 100 cards); card advantage 6 (+3 unread); protection 6; board power 145; avg MV 3.75;
shape WIDE; Humans 14, Angels 4; sources W 21 / U 21 / G 20; tempo-sim on-curve 51.3%.
Engines: lifegain 16 enablers / 10 payoffs; counters 9 enablers, NO payoff flagged;
tokens 7 / 7.

1. **The deck pays a creature's printed cost once and its enters trigger many times.**
   ~15 blink effects (Y'shtola, Thassa, Don & Leo, Teleportation Circle, Silver Surfer,
   Yorion, Soulherder, Abuelo, Oji, Restoration Angel, Salvation Swan, Lilysplash Mentor,
   Ephemerate, Morningtide's Light, Another Round) plus Elesh Norn and Panharmonicon.
   Value ON ENTERING is multiplied; value on attacking, on dying or from a static ability
   is not. Grade enters triggers up, attack triggers down.
2. **Every creature entering is also a Galadriel trigger** (three modes a turn: {G}{G}{G},
   a counter on each creature, scry 2 and draw) and a lifegain event for Soul Warden,
   Ajani's Welcome, Distinguished Conjurer. Tokens count. More bodies entering = more of
   everything.
3. **Lifegain payoffs scale per EVENT, not per point**, and "first time each turn" caps
   (Vanguard Seraph, Bloombrute) do not. A payoff that reads "whenever you gain life" is
   worth a trigger per creature entering.
4. **Y'shtola's extra end step doubles "at the beginning of (your / each) end step"**
   (Crested Sunmare, Lathiel, Aerith, Enlightened Confidant, Thassa, Don & Leo,
   Teleportation Circle, Palantír). End-step payoffs grade up.
5. **Blink RESETS a permanent**: counters, X values (a blinked X creature returns with
   X = 0), "until this leaves" exiles (the exiled card comes back — the G-42 shape for
   O-ring creatures), transformed DFCs (return front face). Grade those down.
6. **Mana**: W 21 / U 21 / G 20, 37 lands. {W}{W} on turn 2–3 casts ~55–63% on curve.
   The deck is already heavy (avg MV 3.75, 11 early drops); the deck 85 slow-start lesson
   says favour ≤3 MV unless the card is a top-end engine.
7. **Gaps worth filling**: interaction (9, no sweeper, few instants); a counters PAYOFF
   (Galadriel, Archangel of Thune and Heliod make counters and nothing spends them);
   cheap early plays.
8. **Format**: Historic Brawl, singleton, commander identity GWU. Not-brawl-legal = out.
9. **Structurally invisible to the tools**: enters-trigger multiplication (every model
   counts a trigger once), lifegain event counts, end-step doubling, Galadriel's mode
   choice. Grade those by hand from text.

## 2. Standing error list

(none yet)

## 3. Cross-batch observations

(none yet)

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

## 5. Consolidated plan (live)

(after the last batch)
