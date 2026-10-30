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

- **An ANGEL sub-theme is forming** in the pile: The Book of Exalted Deeds and Speaker of
  the Heavens make Angel tokens off lifegain; Resplendent Angel, Lyra (Archangel of Dawn),
  Serra Paragon, Boon-Bringer Valkyrie are Angels. The deck already runs 4 Angels
  (Restoration Angel, Archangel of Thune, Holy Cow, Lyra-less). Watch the count — an Angel
  payoff is only as good as the Angels it can reach (G-59).
- **"Exile until this leaves" cards** (Prison Realm, Detention Sphere) are fine removal,
  but a blink of them by Silver Surfer or Yorion RETURNS the exiled card before the new
  copy re-exiles (Rule 5). Teleportation Circle cannot target them (creature/artifact only).
- **Protection cluster**: Shalai and Sigarda (hexproof for everything else), Sephara,
  Avacyn — the deck's protection is 6; one hexproof lord is probably enough.
- **Counters payoffs arrive** (R7 gap): Metropolis Angel (draw), Elrond, Master of Healing,
  Metastatic Evangel (proliferate). Metastatic + Flux Channeler are multipliers, not payoffs.
- **Tocasia, Dig Site Mentor turns every creature into a surveil engine** — the single
  biggest scry-sub-theme card in the pile; Denzilore, Matoya, Planetarium and Elrond,
  Master of Healing all pay per surveil.

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

### Batch 1 (cards 1–25)

| # | Card | Own | Verdict | Note (rule) |
|---|---|---|---|---|
| 1 | Ajani, Strength of the Pride | — | ★★ | +1 gains life = creatures + planeswalkers (wide deck, one big gain); −2 Pridemate; 0 at 40 life exiles ALL their creatures and artifacts — pairs with Felidar Sovereign's 40. |
| 2 | The Wandering Emperor | — | ★★★ | Flash; −2 exiles a tapped creature and gains 2; −1 makes a 2/2 that enters (R2). Instant-speed interaction the deck lacks (R7). |
| 3 | Syr Vondam, Sunstar Exemplar | — | ✗ | {W}{B} — off colour. |
| 4 | The Book of Exalted Deeds* | — | ★★ | End step: gained 3+ life → 3/3 Angel; Y'shtola makes it two (R4); tokens enter (R2). {W}{W}{W} is the cost (R6). |
| 5 | Ojutai Exemplars | — | △ | Only blinks ITSELF on a noncreature spell; no enters trigger of its own. |
| 6 | Serra Paragon* | — | ★★ | Once a turn cast a ≤3 MV permanent (or a land) from the graveyard — re-buys Soul Warden, Reflector Mage, Skyclave Apparition; each re-cast enters (R1/R2). Flying Angel. |
| 7 | Prison Realm | — | ★★ | 3-mana creature/planeswalker exile + scry 1 (R7). Caution R5 with Surfer/Yorion. |
| 8 | Lost Isle Calling | — | ★ | Verse counter per scry; 7+ = draw 7 and an extra turn. Scry events are frequent here; spice. |
| 9 | Elrond, Master of Healing | — | ★★ | Every scry puts counters on X creatures (X = cards looked at) — Galadriel's scry 2 = two counters a turn; draws when they're targeted. A counters payoff (R7). |
| 10 | Nissa, Steward of Elements | — | ★★ | +2 scry 2 every turn; 0 puts a land or a creature (MV ≤ loyalty) onto the battlefield — a free enters (R1). |
| 11 | Legolas, Counter of Kills | — | △ | Untap on scry; counters when their creatures die. Little for this deck. |
| 12 | Flickering Hound | — | ★★★ | "Whenever you cast a creature spell, exile up to one other target creature… return it." ~45 creatures: a blink every creature cast (R1). |
| 13 | Photon, Lady of Light | — | ★ | Blink only on ATTACK (R1 grades attack triggers down). |
| 14 | The Legend of Yangchen | own | ★★★ | I: each player picks one of THEIR permanents MV ≥3 to exile — in 1v1 that's two of the opponent's; II: both draw 3; III flips to a flier that airbends on your second spell. Owned interaction + cards; Yorion/Surfer restart the Saga. |
| 15 | Jill, Shiva's Dominant | — | ★ | Enters: return any nonland permanent to hand — tempo, or re-buy your own enters trigger. |
| 16 | Oracle of the Alpha | — | ★★ | Enters: conjure the Power Nine into your library. Every blink adds another nine (Ancestral Recall, Time Walk, Black Lotus, Moxen). Spice with real power. |
| 17 | Wakandan Tusker | — | ◇ | Gain 1 + scry 1 whenever it taps; needs a tap outlet (Tocasia gives one). |
| 18 | Flux Channeler | — | ◇ | Proliferate on noncreature spells — counters, loyalty, verse. A multiplier, not a payoff. |
| 19 | Meandering Towershell | — | ✗ | Attack-exile, no enters value (R1). |
| 20 | Stenn, Paranoid Partisan | — | ★★ | {W}{U} 2-drop; "{1}{W}{U}: Exile Stenn. Return it at the next end step" — a guaranteed creature entering every turn (R2: Galadriel + lifegain triggers) plus a cost reducer. |
| 21 | Detention Sphere | — | ★★ | Exiles any nonland permanent (and all same-named). R5 caution. |
| 22 | Ojutai's Command | — | ★★ | Instant: two of reanimate ≤2 MV / gain 4 / counter a creature spell / draw. Instant interaction (R7). |
| 23 | Tocasia, Dig Site Mentor | — | ★★★ | Creatures have vigilance and "{T}: Surveil 1" — every creature is a surveil engine for Denzilore, Matoya, Planetarium (R9). |
| 24 | Chulane, Teller of Tales | — | ★★★ | Every creature CAST draws a card and puts a land; "{3}, {T}: Return target creature you control to its owner's hand" re-buys an enters trigger. |
| 25 | Speaker of the Heavens | — | ★★ | 1-drop lifelink; at 32+ life taps for a 4/4 Angel each turn (R2). Early play (R6). |

### Batch 2 (cards 26–50)

| # | Card | Own | Verdict | Note (rule) |
|---|---|---|---|---|
| 26 | Metastatic Evangel | — | ★★ | {1}{W}: every nontoken creature entering proliferates — Galadriel/Archangel/Heliod counters, planeswalker loyalty, verse counters. Blink feeds it each time (R1, R7). |
| 27 | Angelheart Protector | — | ◇ | Enters: one creature indestructible this turn — a blink in response is a save. |
| 28 | Metropolis Reformer | — | ★ | 3-mana Angel flier; "You have hexproof"; damage dealt to it gains life. |
| 29 | Righteous Valkyrie | — | ★★ | Angel or Cleric entering gains life = its toughness (blink repeats it); at 32+ life every creature gets +2/+2. |
| 30 | Valgavoth, the Lifeline | — | ★★ | 3-mana Angel; each gain grows creature cards in hand and yard perpetually; having gained life lets you CAST creatures from the graveyard — recursion every turn the lifegain engine runs. |
| 31 | Archangel of Tithes | own | ★ | {1}{W}{W}{W}; attackers cost {1} each — a defensive tax. Owned. |
| 32 | Champions of Tyr | — | ◇ | Boon: next creature cast enters with a keyword counter. Small. |
| 33 | Serra the Benevolent | — | ◇ | −3: a 4/4 Angel; +2 pumps fliers. |
| 34 | Shalai, Voice of Plenty | — | ★★ | You, your planeswalkers and other creatures have hexproof (protection, R7); {4}{G}{G}: a counter on each creature. |
| 35 | Angel of Destiny | — | ◇ | Alt-win at 40 needs combat damage and symmetric gains. Felidar does it without combat. |
| 36 | Angel of Sanctions | — | ★★ | Enters: exile a nonland permanent until it leaves — a blink re-targets (R5 is harmless here); embalm gives a second copy. |
| 37 | Elspeth Resplendent | — | ★★ | +1 counter and keyword; −3 puts a ≤3 MV permanent from the top 7 onto the battlefield (a free enters, R1); −7 five Angels. |
| 38 | Divine Visitation | — | ◇ | Creature tokens become 4/4 flying Angels. ~7 token makers today (count before adding, G-61). |
| 39 | Herald of War | — | △ | Attack-only value (R1). |
| 40 | Light of the Legion | — | △ | 6 MV; mentor/death counters. |
| 41 | Valkyrie Harbinger | — | ★ | 6-mana lifelink Angel; each end step with 4+ life gained makes a 4/4 Angel (doubled, R4). Resplendent Angel does it for 3. |
| 42 | Ob Nixilis, the Ascended | — | ★★ | 7-mana Angel: enters destroying all their TAPPED creatures (blink after they attack = another wipe); end step Angel if you gained life (R4). |
| 43 | Sephara, Sky's Blade | — | ★ | Your other fliers are indestructible; alt cost tap four fliers + {W}. ~19 evasive bodies. |
| 44 | Avacyn, Angel of Hope | — | ★ | 8 MV; everything you control indestructible. Late protection. |
| 45 | Parhelion II | — | ◇ | 8-mana vehicle, crew 4, attacking Angels. |
| 46 | Orvar, the All-Form | — | ◇ | Instant/sorcery targeting your permanent → token copy. Ephemerate is the only targeted blink spell left. |
| 47 | Seraphic Steed | — | ◇ | {G}{W} lifelink first striker; saddled attack → Angel. Early drop. |
| 48 | Metropolis Angel | — | ★★ | Attack with any creature with counters → draw. A counters PAYOFF (R7) on a flier. |
| 49 | Torens, Fist of the Angels | — | ★★ | Every creature cast makes a 1/1 token that enters (R2). |
| 50 | Sigarda, Font of Blessings | — | ★★★ | Other permanents hexproof (protection), and cast Angels and Humans from the top of your library (Humans 14 + the Angel sub-theme) — card advantage every turn. |

## 5. Consolidated plan (live)

(after the last batch)
