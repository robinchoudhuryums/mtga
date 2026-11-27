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
10. **Opponent discard is not our discard.** "Whenever you discard" payoffs (Spider-Man,
   Magmakin, Glint-Horn, Monument, Cool but Rude) and madness trigger only on OUR discards.
   Hand attack (Thoughtseize, Mind Twist, Waste Not, Tinybones, Tourach, Tergrid) is a
   separate engine with its own payoffs; grade it on its own, not as "discard".
9. **Structurally invisible to the tools:** madness and other cast-from-exile mechanics are
   not a role, so `cuts` reads madness cards and impulse engines as low-fit; Zuko's counters
   are not in any score. Grade those by hand.

## 2. Standing error list

(none yet)

## 3. Cross-batch observations

- **Hand-attack cluster (variant signal):** Thoughtseize, Mind Twist, Drill Bit, Waste Not,
  Tinybones x2, Tourach, Tergrid, Heartless Pillage, Ozai's Cruelty, Stinging Vitriol, The
  Eldest Reborn, Armus, Kroxa. A Rakdos "make them discard" deck, not this one.
- **Celes-side cards so far:** Kroxa and Kunoros, Chainer, Kroxa (escape), Ral Zarek's −2,
  Eldest Reborn III, Joshua's Phoenix III, Green Goblin Back for More (mayhem).
- **Noncombat damage package:** Solphim (doubles), Maha (toughness 1), Artist's Talent L3
  (+2): with Spider-Man, Magmakin, Glint-Horn, Bullseye, every discard becomes removal.

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

**Batches 1–2 (cards 1–60):** ★★ Azula, Hostile Investigator, Lorehold, Quintorius History
Chaser, Neriv Heart of the Storm, Lightning Axe, Collective Defiance, Solphim. ★ Tomb Robber,
Dying to Serve, Death of Gwen Stacy, Inevitable Defeat, Merciless Javelineer, Bullseye, Worf,
Green Goblin Back for More, Maha, Witch-king, Gamble, Artist's Talent, Misty Knight, Kirk,
Neheb, Smellerbee, Joshua. Everything else ◇/△ (reasons on the board).

**Batches 3–5 (cards 61–141):** ★★ Phelia, The Mind Stone, Polterheist, Florian, Ob Nixilis
Captive Kingpin. ★ Airbender Ascension, Photon, The Soul Stone, The Neutrinos, Sadistic
Slash, Venat, Black Widow, Taii Wakeen, Luke Cage, Tragic Trajectory, Mishra Tamer of Mak
Fawa, Spider-Gwen, Magda, Sela, Grenzo, Ozai the Phoenix King, Hidetsugu Devouring Chaos,
Kalain, Kaya the Inexorable, Djeru and Hazoret, Quintorius Loremaster.

## 5. Consolidated plan (live)

**2026-11-27 — applied and split.** Deck 108 took the owner's 12 board swaps (Ob Nixilis over
Solphim) and Archfiend of Ifnir for Celes. Celes now commands **deck 109 Returners** (graveyard
casts and reanimation; draft from the board), and `builds/zuko` covers BOTH decks: piles Z (Zuko),
C (Celes), B (either deck), N (neither). Cards were pre-sorted by reason group; every card has a
verdict for each deck. The owner divides the rest between the two decks on the board.

**2026-11-27 — full re-grade for both decks.** Every board card outside a deck, and every
nonland card of each deck, now has a fresh verdict for BOTH decks with a two-part reason
(Zuko / Celes). Findings: (1) Celes has a natural ARISTOCRATS sub-theme: recursive creatures
(Bloodghast, Gixian Recycler, Tenacious Underdog) are free sacrifice fodder, so outlets (Akul,
Ayara, Juri, Stormclaw Rager, Evereth, Kethek, Zhao, Body Dropper) and death payoffs (Vraan,
Massacre Girl, Grand Nagus Zek, Dalkovan Outrider) move up for her. (2) Cards that EXILE your
own discards are anti-synergy for Celes: Containment Construct, Moonstone, Necropotence,
Currency Converter, Hidetsugu Consumes All. (3) Nico and Spider-Verse count graveyard casts
("anywhere other than your hand"), so both are strong for Celes too. (4) Blink, impulse and
heist give Celes nothing.

**Zuko package v4 (proposed 2026-11-27, on the board as suggestions):** -Big Score +Heroes for Hire,
-Laughing Jasper Flint +Impetuous Lootmonger, -Olivia Opulent Outlaw +Goldspan Dragon, -Cool but
Rude +Alpharael, -Vindicate +Collective Defiance, -Nalfeshnee +Ruinous Ultimatum, -Giant Killer
+Phelia, -Stromkirk Occultist +Azula, -Lightning Helix +Lorehold; Plains/Mountain/Swamp ->
Eiganjo/Sokenzan/Takenuma. Preview: floor A, legal; interaction 18 -> 17, card advantage 22,
protection 5 -> 6, board power 107 -> 112, avg MV 3.25 -> 3.40. Keeps Living Laser, Bone Miser,
At Knifepoint, Mog, Rakdos (owner's).

**Celes package v1 (proposed 2026-11-27, on the board as suggestions):** -Spider-Islanders +Nico,
-Raging Goblinoids +Crucias, -Faithless Looting +M.O.D.O.K., -Cathartic Reunion +Bonehoard
Dracosaur, -Misty Knight +Quintorius History Chaser, -Can't Stay Away +Sela, -Sevinne's
Reclamation +Spider-Verse, -Talisman of Conviction +Black Market Connections, -Inevitable Defeat
+Lightning Axe, -Mishra Claimed by Gix +Highway Reaver, -Tomb Robber +Stormclaw Rager, -Smellerbee
+Spider-Man, -Talisman of Hierarchy +Liliana the Faultless, -Spider-Gwen +Boros Charm; Swamp ->
Takenuma, Mountain -> Sokenzan. Preview: floor A, legal; interaction 16 -> 18, card advantage
8 -> 10 (the role model undercounts recursion), protection 1 -> 3, avg MV 3.13 -> 3.22.


**Owner's board round 3 (2026-11-27):** 53 adds marked against 12 cuts, plus notes. Re-graded
on the owner's notes: Alpharael (void is on most turns via Treasures and warp), Dalkovan
Outrider, Hidetsugu Devouring Chaos, Ob Nixilis the Adversary, Ruinous Ultimatum (Treasures pay
WWW), The Balrog (Treasure sacrifices discount it), The Mind Stone, Theater of Horrors.
**Conflict:** Solphim and Ob Nixilis Captive Kingpin are both marked, with Unstable Amulet and
Shadow of the Goblin marked to cut: with those cut, Ob Nixilis loses most of its exactly-1
sources and Solphim turns the rest into 2s, so take Solphim. **Package v3** (21 swaps:
the owner's 12 cuts, 8 more suggested (Laughing Jasper Flint, not Celes, which the owner kept), Plains -> Eiganjo) previewed floor A, legal; interaction
18, card advantage 21, protection 7, board power 118, avg MV 3.44, early drops 14 (heavy:
Treasures are what carry it).

**Commander: keep Fire Lord Zuko (rule 8).** About 32 cards in the current 100 trigger Zuko
(madness, impulse, heist, adventure, foretell, warp, discover, blink). Celes triggers on
creatures entering or cast from a GRAVEYARD, and the current list has essentially none. The
pile's Celes cards (Kroxa and Kunoros, Chainer, Kroxa, Olivia Crimson Bride, The Soul Stone,
Rakdos Joins Up, Eldest Reborn, Kardur's Vicious Return, Orcus, Highway Reaver) top out around
a dozen, mostly ◇, and adding them means cutting exile cards. Zuko also costs 3 to Celes' 4,
and his trigger repeats where Celes' wheel happens once per cast. Celes stays in the 99.

**Package v2 (2026-11-27, owner keeps Living Laser, Bone Miser, At Knifepoint; previewed: floor A,
legal; interaction 20 -> 16, card advantage 20 -> 23, protection 3 -> 4, board power 91 -> 106,
avg MV 3.14 -> 3.27, early drops 18 -> 15):**

| Cut | Add |
|---|---|
| Talisman of Indulgence | Black Market Connections (owned) |
| Light Up the Stage | Heroes for Hire |
| Steal the Show | Ultimate Green Goblin (owned) |
| Kolaghan's Command | Bonehoard Dracosaur |
| Celes, Rune Knight | Ob Nixilis, Captive Kingpin |
| Bloodtithe Harvester | Polterheist |
| Vindicate | Lightning Axe |
| Collective Brutality | Florian, Voldaren Scion |
| Olivia, Opulent Outlaw | Archfiend of Ifnir |
| Cool but Rude | The Legend of Roku (owned) |
| Mountain | Sokenzan (owned) |
| Plains | Eiganjo |
| Swamp | Takenuma |

Keyword sweep (channel, hideaway, craft, saga-transform, connive, jump-start, mayhem,
spectacle, cascade, cycling, Blood) added 20 cards; the best are Archfiend of Ifnir, the
three channel lands, The Legend of Roku, Kumano Faces Kakkazan, Volcanic Torrent,
Necrogoyf, M.O.D.O.K. and Electro's Bolt. **Solphim conflicts with Ob Nixilis**: doubling a
1-damage ping makes it 2, which no longer triggers "exactly 1".

**Tier 2 (next in line; cut candidates Kolaghan's Command, Giant Killer, Bloodtithe
Harvester, Cool but Rude, Olivia Opulent Outlaw):** Phelia (owned, 2-drop blink each attack),
The Mind Stone (owned rock + late blink), Azula, Solphim (owned), Hostile Investigator,
Lorehold (owned), Quintorius History Chaser, Neriv Heart of the Storm (owned), Collective
Defiance, Kalain.

**Spice:** Ozai, the Phoenix King (owned; firebending mana survives combat), Living End
(suspend cast from exile, mass return from exile), Djeru and Hazoret (owned).

**Protect (the cut ranking cannot see exile casts, rule 9):** Teleportation Circle (ranked
#1 cut by `cuts`), Dream Devourer, Tannuk, Charred Foyer, Containment Construct, Moonstone.
