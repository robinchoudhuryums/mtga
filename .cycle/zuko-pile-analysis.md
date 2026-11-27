# Zuko pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into deck
108's `#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Source list:** the owner's 2026-11-27 paste (209 distinct cards); 68 are already in deck
108 or on the `builds/zuko` board, so **141 to evaluate**. Board:
https://claude.ai/artifact/LqgRVwYXwUiHyvSA5cGTCa (project `builds/zuko`, pile Z).

**Open question the owner raised:** Fire Lord Zuko vs Celes, Rune Knight as commander.
Decide at the end of the pile, from counts (rule 8), not mid-batch.

## 1. The decision framework

Live vector of deck 108 at the start (2026-11-27, after the owner's board picks):
interaction 20 (+1?), card advantage 20, protection 3, ramp 3, board power 91, avg MV
3.14, tier floor A (100-card thresholds A = interaction 12 / sum 19). Talisman of
Indulgence is a placeholder slot marked to cut for a Treasure maker.

1. **Zuko counts two things: a spell CAST FROM EXILE, and a permanent you control that
   ENTERS FROM EXILE.** Madness, impulse/heist, adventure, foretell, plot, warp, discover,
   cascade, rebound and airbend recasts all count. Blink counts (it returns from exile).
   Flashback, escape, unearth, mayhem, disturb and "cast from your graveyard" do NOT count
   for Zuko: they are graveyard zones. A card that only fills the graveyard is a Celes
   card, not a Zuko card.
2. **Celes counts the opposite zone**: another creature entering FROM A GRAVEYARD or CAST
   FROM a graveyard (each time: +1/+1 counter on every creature). Its own entering
   discard-and-draw is one-shot per cast. As the commander it is recast for +{2} each time.
3. **Discard is the input, so a discard outlet is graded by repeatability.** Once per turn
   or better (attack trigger, upkeep, activated) beats a one-shot. A discard that EXILES the
   card for later play is worth more than one that only bins it (it is also a Zuko cast).
4. **Printed cost is what we pay for most cards**; the exceptions are madness (pay the
   madness cost), warp (Tannuk gives red creatures warp {2}{R}), foretell (Dream Devourer
   gives every card foretell at −2) and free casts (discover, cascade, Charred Foyer).
5. **Interaction is NOT the shortage (20 against a 12 floor). Protection (3), ramp (3, with
   the Treasure subtheme replacing the Talismans) and cheap plays are.** An answer has to be
   a better answer, or an answer that is also an engine piece, to earn a slot.
6. **Treasure is the ramp now** (owner, 2026-11-27): makers already in: Crucias, Prosper,
   Face-Breaker, Ragavan, Olivia, Big Score, Fable's Goblin. Spenders: Face-Breaker,
   Prosper, Olivia.
7. **Outlaws are a light third axis** (about 11 outlaws, payoffs Olivia, At Knifepoint).
   An outlaw payoff needs the count to matter.
8. **Commander decision rule:** count the deck's cards that trigger each candidate
   (rule 1 vs rule 2), plus what the pile could add to each. Zuko wins by default unless the
   Celes count could reach a comparable density without gutting the exile engine.
9. **Structurally invisible to the tools:** madness and other cast-from-exile mechanics are
   not a role, so `cuts` reads madness cards and impulse engines as low-fit; Zuko's counters
   are not in any score. Grade those by hand.

## 2. Standing error list

(none yet)

## 3. Cross-batch observations

(none yet)

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

## 5. Consolidated plan (live)

(after the last batch)
