# Loki villains pile (new deck 87) — analysis (TEMPORARY working doc)

**Status: DRAFTED as decks/87-lokis-legion (2026-10-21); keep until the owner signs off on the
list and the tier letter, then fold into its notes and delete.** A scratchpad, not a source of truth — decks/ are.

**Source list:** the owner's 73-card pile (2026-10-21), commander **Loki, the Deceiver**
(MSC 86), Historic Brawl. All 73 are legal in Historic Brawl and inside Loki's {U}{B}{R}
identity. 56 are Villains. 33 already sit in other decks, which does not matter for a new
deck: decks share the collection.

## 1. The decision framework

Loki, the Deceiver — {1}{U}{B}{R} 4/4 Legendary God Sorcerer Villain, no evasion:
"Whenever Loki attacks, create a tapped and attacking token that's a copy of another target
Villain you control, except it isn't legendary and it's an Illusion in addition to its other
types. Sacrifice that token at the beginning of the next end step. / Whenever one or more
Villains you control deal combat damage to a player, draw a card."

- **L1 — WHAT A COPY TOKEN GETS.** The copy ENTERS (its enters triggers fire), it is
  attacking (combat-damage triggers can fire), and it is SACRIFICED at end step (dies /
  leaves / sacrifice triggers fire). It was never DECLARED as an attacker, so its own
  "whenever this attacks" trigger does NOT fire. Grade a copy target by enters + combat
  damage + death value. An attack trigger is worth only what the original does.
- **L2 — THE COPY IS NOT LEGENDARY.** Copying a legendary Villain never hits the legend
  rule, so the best copy target is simply the strongest enters/death Villain on board.
- **L3 — THE DRAW NEEDS A VILLAIN TO CONNECT.** One card per combat damage step, from ANY
  Villain. Evasion (flying, menace, unblockable) and go-wide pressure turn it on; Loki's own
  4/4 body has no evasion.
- **L4 — LOKI MUST ATTACK AND LIVE.** A 4-mana 4/4 attacking every turn needs protection,
  removal for blockers, or a board that makes blocking it bad. Recasting costs {2} more each
  time.
- **L5 — DEATH IS A RESOURCE.** One Villain token dies at every end step Loki attacked.
  Death and sacrifice payoffs ("whenever a creature you control dies", treasure or Blood on
  death) get a free trigger each turn.
- **L6 — DENSITY.** Loki needs ANOTHER Villain on board to copy. Count Villains before
  adding non-Villains: a non-Villain must beat a Villain by enough to cover lost copy
  targets and lost draw triggers.
- **L7 — FORMAT.** 100-card singleton, 25 life, free first mulligan, three colours. The tier
  floor scales ×1.67 (A needs interaction 12 and a sum of 19). Interaction and card
  advantage come from OUTSIDE the pile if the pile is thin on them.
- **L8 — TRIBE DEPTH (G-59, measured 2026-10-21).** In the Historic Brawl-legal U/B/R pool,
  46 cards mention "Villain" in their text and 21 say "Villains you control". The tribe has
  real payoffs; this is not a bodies-only tribe.

## 2. Standing error list
- E1 (rules, L1): a copy token put onto the battlefield attacking was never declared as an
  attacker, so "whenever X attacks" does NOT fire for it. Boomerang, Madame Hydra,
  Reanimated's attack mill and every attack trigger are worth only the original's.
- E2 (rules): a copy token's "when this dies, exile this card" rider fails. The token stops
  existing before the trigger resolves, so there is no card to exile (Doombot Harbinger).
  Its enters half still works.
- E3 (timing): Scorpion's "at the beginning of your end step, if a creature died this turn"
  checks as the end step BEGINS. Loki's copy is sacrificed by a trigger at that same moment,
  so the copy's death does not turn Scorpion on that turn.
- E4 (rules): Thunderbolts Conspiracy cannot return the copy token (a token that died is
  gone). It returns REAL Villains, Loki included, which is its point (L4).
- E5 (rules): Minotaur, Roxxon CEO counts NONTOKEN deaths, so the copy token does not feed
  it. Thanos, Death's Consort counts any creature, so it does.
- E6 (rules): a copy of Mysterio, Master of Illusion counts NONTOKEN Villains and its 3/3s are
  exiled when the copy is sacrificed — a temporary blocker wall, not lasting value. A copy of
  Morlun enters with X = 0. Grade both on the original.
- E8 (re-grade, owner's pushback 2026-10-21): Villainous Wrath is NOT a symmetric wipe here.
  With Thunderbolts Conspiracy out, every real Villain you lose comes back (finality
  counter), so it is one-sided against a Villain board. ◇ → ★★.
- E9 (re-grade): the deathtouch cards are a PACKAGE, not singles. Black Widow, Deadly Hunter
  draws whenever a deathtouch creature connects, and the pile holds seven (Undead Hand Ninja,
  White Widow, Crossbones, Scorpion, Radioactive Man, Gwenom, Black Widow, Deadly Hunter),
  plus any Loki copy of one. The Heroes were graded as off-tribe singles; as a group they are
  the deck's second draw engine.
- E7: Chameleon, Master of Disguise and Superior Spider-Man copy a creature WHOLESALE (only
  the name is kept), so a copy of a Villain IS a Villain — they are not off-tribe.

## 3. Cross-batch observations
- O1: the copy token is a VILLAIN ENTERING every attack, so every "whenever a Villain enters"
  card gets a free trigger each turn: Doom Reigns Supreme (drain + plan counter), Baron
  Strucker (connive), Crossbones (2 damage + counter). It is also a VILLAIN DYING every turn:
  Criminal Enterprise (drain) and Kingpin, Wilson Fisk (two Treasures).
- O2: the best COPY TARGETS so far are enters-value Villains: Tombstone (regrow a Villain
  card every attack), Doombot Harbinger (mill 4), Madame Hydra, Reanimated (mill 2).
- O3: an ATTACKS-ALONE package (Bob, Viper) fights Loki, which always attacks with a token
  beside it. Out, not graded down for power.
- O4: black is the pile's core (24 of the first 25 are black). Blue/red come from Loki and
  later batches; check the pip balance at consolidation.
- O5: a DEATHTOUCH cluster (Undead Hand Ninja, White Widow, Crossbones, Scorpion) makes Loki
  attacks hard to block profitably (L4).
- O6 (the strongest pattern): the turn's normal draw is the first card, so Loki's
  combat-damage draw is the SECOND card every turn a Villain connects. That turns on the
  whole "whenever you draw your second card each turn" family each turn: Construct a Cosmic
  Cube (menace Villain), M.O.D.O.K., Evil Intellect (opponent sacrifices a nontoken
  creature — repeatable removal), Madame Masque (menace Villain), Kang, Temporal Tyrant
  (drain). Connive engines (Prowler, Baron Strucker, Tiger Shark) add more draws.
- O7: colour balance — black is the core. Blue: Norman, Prowler, Kang, Morbius, Taskmaster,
  Tiger Shark, Doctor Octopus, Loki, God of Mischief. Red: Avengers: Under Siege, Madame
  Hydra; Bullseye is {B/R} hybrid. Red is a light third colour so far.
- O8: anthems for the Villain team: The Masters of Evil (+2/+1, or tutor a Plan),
  Doctor Octopus (+2/+2 and refill to eight).
- O9: the pile's last seven (Black Widow ×3, Agent Venom, Gwenom, Symbiote Spider-Man,
  Superior Spider-Man) are HEROES, not Villains: no copy target, no draw trigger (L6). Only
  Gwenom earns a look on raw power; Superior Spider-Man becomes a Villain if it copies one
  (E7).
- O10: CONNIVE is a second engine. Eleven pile cards connive (Norman, Baron Strucker, Baron
  Helmut Zemo, Valentina, Scorpion, M.O.D.O.K., Madame Masque, Prowler, Kang, Temporal
  Tyrant, Tiger Shark, Leader). Leader, Super-Genius adds a card to EVERY connive, and its
  beginning-of-combat connive makes the second draw happen BEFORE combat, so the O6 family
  fires even when no Villain connects. Connive's DISCARDS also feed Mysterio's Mirage (a 3/3
  Villain), Chameleon's mayhem and Living Laser.
- O11: interaction in the pile is THIN: The Spot's Portal, M.O.D.O.K., Evil Intellect,
  Avengers: Under Siege, Bullseye, Shocker, M.O.D.O.K.'s −1/−1, Villainous Wrath (symmetric).
  At 100 cards the A floor wants interaction 12, so most removal must come from OUTSIDE the
  pile (L7).
- O12 (outside the pile, the biggest find): VILLAINS WITH ENTERS-REMOVAL are the best copy
  targets in the format, because Loki copies their enters trigger on EVERY attack.
  Ultimo, Civilization's End (each opponent sacrifices a creature), Elektra, Daughter of the
  Hand (destroy power 3 or less, owned), Shocker (2 to a creature and its controller) — a
  removal spell every turn from one card. Liliana, Dreadhorde General (owned) draws off the
  copy's death every turn (L5).
- O13 (G-67 holes, record only — fix in a later batch): Leader, Super-Genius and Black Cat,
  Cunning Thief score NO role, though both are card advantage; connive engines read only as
  "Payoff / engine". The proposal's card-advantage 8 under-counts the real card flow.
- O15 (G-67, record only): Avengers: Under Siege scores no interaction role, though chapter II
  is a one-sided sweep (2 damage to each non-Villain creature and each opponent).
  Duskmantle, House of Shadow showed as a U/B producer in `suggest --lands` but makes only {C}.
- O14: distinct from deck 11 (Villainous — a 60-card mono-black Standard deck). Twelve
  shared cards; different format, colours and engine (G-47: some overlap is fine).

## 4. Running verdicts
Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

### Batch 1 (1–25)
| # | Card | Verdict | Note |
|---|---|---|---|
| 1 | Boomerang, Blade Flinger | △ | 2-drop ping; attack trigger is the original's only (E1) |
| 2 | Bob, Reluctant HYDRA Agent | ✗ | attacks ALONE — Loki never attacks alone (O3) |
| 3 | Norman Osborn // Green Goblin | ★★★ | unblockable Villain = Loki's draw every turn (L3) plus connive; flips to a flying menace engine |
| 4 | Decoy Ploy | ◇ | 2-mana instant regrowth of a Villain |
| 5 | Doom Reigns Supreme | ★★ | copy token triggers it every attack (O1): drain 1 + counter; 5th counter casts two of their cards free |
| 6 | Hammerhead, Maggia Boss | ★ | free sac outlet for the doomed copy token after damage (L5) |
| 7 | Viper, Cruel Conspirator | ✗ | attacking-alone pump (O3) |
| 8 | Undead Hand Ninja | ◇ | deathtouch 2-drop; drain needs graveyard recursion |
| 9 | Villainous Syndication | △ | taps Villains that should be attacking |
| 10 | White Widow, Yelena Belova | ◇ | deathtouch package only (O5) |
| 11 | Baron Strucker, HYDRA Overlord | ★★★ | Villain cost −1 AND connive on a Villain entering (copy token each turn, O1) |
| 12 | Baron Helmut Zemo | ★ | connive per black spell from hand; {B}{B}{B}; boast needs 15 black pips in the yard |
| 13 | Construct a Cosmic Cube | ★★ | second draw each turn → 2/1 menace Villain; Loki's draw + connives reach it |
| 14 | Citizen V, Helmut Zemo | ★★ | every lifegain → +1/+1 on each Villain; the drain cards feed it |
| 15 | Criminal Enterprise | ★★ | menace Villain token + drain on each Villain death (the copy, every turn) |
| 16 | Crimson Cowl, Master of Evil | ★★★ | a 2/1 menace Villain every attack: copy fodder and draw trigger |
| 17 | Doombot Harbinger | ★★ | flying Villain (draw); copy target for mill 4; recursion on the original only (E2) |
| 18 | Valentina Allegra de Fontaine | ★ | tap: a Villain connives (they are Heroes too); taps an attacker |
| 19 | The Spot's Portal | ★★★ | 3-mana instant removal, no life cost with a Villain |
| 20 | Tombstone, Career Criminal | ★★★ | Villain cost −1; BEST copy target — regrow a Villain card every attack (O2) |
| 21 | Crossbones, Malicious Mercenary | ★★ | deathtouch; copy token entering = 2 damage + counter each turn |
| 22 | Doctor Doom, Unrivaled | ★★★ | 4/4 lifelink that taps to draw — a card engine |
| 23 | Kingpin, Wilson Fisk | ★★★ | copy token sacrificed each turn → 2 Treasures (O1); menace 3/6 |
| 24 | Madame Hydra, Reanimated | ★ | menace grower; copy target for mill 2 |
| 25 | Scorpion, Seething Striker | ◇ | deathtouch; its connive does not see the copy's death (E3) |

### Batch 2 (26–49)
| # | Card | Verdict | Note |
|---|---|---|---|
| 26 | Thanos, Death's Consort | ★ | lifelink grower; the copy's death feeds it every turn (E5) |
| 27 | Thunderbolts Conspiracy | ★★ | flash; every real Villain — Loki too — comes back once (E4, L4) |
| 28 | Titanium Man | ◇ | attack trigger is the original's only (E1) |
| 29 | Black Cat, Cunning Thief | ★★★ | copy target: two of their top nine, castable, EVERY attack (O2) |
| 30 | M.O.D.O.K. | ★★★ | flying lifelink; −1/−1 to their creatures stacks with a copy during combat; connive for life |
| 31 | M.O.D.O.K., Evil Intellect | ★★★ | flying; the second draw each turn makes them sacrifice a nontoken creature (O6) |
| 32 | Madame Masque | ★★ | enters connive (copy target) + a menace Villain on the second draw (O6) |
| 33 | Radioactive Man | ★★ | deathtouch 3/5; a connecting hit halves their life; a copy can do it too |
| 34 | Villainous Wrath | ◇ | symmetric wipe — emergency only, kills your Villains |
| 35 | Doctor Doom | ★★★ | two 3/3 Doombot Villains on entry (a copy makes two more each attack); draws each end step |
| 36 | Minotaur, Roxxon CEO | ◇ | nontoken deaths only — the copy never feeds it (E5) |
| 37 | The Masters of Evil | ★★ | Villains +2/+1, or {1}{B} discard: tutor a Plan |
| 38 | Count Nefaria | ◇ | 6/6 flier, {3} cheaper after a sacrifice (Kingpin, Hammerhead) |
| 39 | Prowler, Clawed Thief | ★★★ | menace; connives on EVERY Villain entering, no once-per-turn cap |
| 40 | Kang, Temporal Tyrant | ★★ | attack connive + drain on the second draw (O6) |
| 41 | Morbius the Living Vampire | ★★ | flying vigilance lifelink Villain — a reliable draw trigger (L3) |
| 42 | Taskmaster, Mercenary Mimic | ★ | copies the best creature each turn |
| 43 | Vulture, Scheming Scavenger | ★★ | when it attacks, every other Villain — the copy too — gains flying (L3) |
| 44 | Tiger Shark, Abyssal Hunter | ★★ | connives on entry (copy target) and attack; {4}{U/B} unblockable |
| 45 | Doctor Octopus, Master Planner | ★★★ | Villains +2/+2, refill to eight at end step — the top end |
| 46 | Avengers: Under Siege | ★★★ | two menace Villains, a one-sided sweep of non-Villains + 2 to each opponent, Treasures per Villain |
| 47 | Bullseye, Death Dealer | ★★ | enters: 2 damage (pay with a Treasure); a copy target for repeat shots |
| 48 | Madame Hydra | ★★ | every Villain spell cast makes a menace Villain token |
| 49 | Loki, God of Mischief | ★★ | Loki's attack trigger TARGETS — draws a card every turn |

### Batch 3 (50–73)
| # | Card | Verdict | Note |
|---|---|---|---|
| 50 | Graviton, Fundamental Force | ★★ | second draw → flying for an attacker, or tap a blocker (O6) |
| 51 | Mysterio's Mirage | ★★ | a 3/3 Illusion Villain any turn you discarded — every connive turn (O10) |
| 52 | Chameleon, Master of Disguise | ★★ | enters as a copy of your best creature (a Villain copy stays a Villain, E7); mayhem off a connive discard |
| 53 | Immortus, Master of Eternity | ◇ | mana for noncreature spells only; a 7-mana wheel |
| 54 | Leader, Super-Genius | ★★★ | +1 card on EVERY connive, and a connive each combat (O10) |
| 55 | Kang the Conqueror | ★★★ | 4-mana 4/5 FLYING Villain (L3); late power-up is an extra turn |
| 56 | Mysterio, Master of Illusion | ★★ | a 3/3 Villain per nontoken Villain on entry (original only — E6) |
| 57 | Vulture, Feathered Fiend | ★★ | flying; fliers connecting draw a card and grow — stacks with Loki's draw |
| 58 | Victor Timely, Wily Tycoon | ★★ | copy target: recast a removal spell from the yard free each attack (needs ≥4 such spells) |
| 59 | Loki Laufeyson | ◇ | copies cheap instants/sorceries; the pile has few |
| 60 | Electro, Assaulting Battery | ★ | 3-mana flying red Villain (L3); the rest needs spells |
| 61 | Loki, God of Lies | ◇ | needs single-target creature SPELLS; Loki's trigger is an ability |
| 62 | Living Laser | ◇ | copies per card discarded this turn — real only with Leader |
| 63 | Red Hulk | ★ | 6/7 reach trample, enrage pings — red top end |
| 64 | Shocker, Unshakable | ★★ | enters: 2 to a creature and its controller — a copy target that is REMOVAL every attack |
| 65 | Scientist Supreme of A.I.M. | ★ | copies an artifact source's trigger — M.O.D.O.K., Evil Intellect's sacrifice, a Doombot |
| 66 | Black Widow, Super Spy | ◇ | Hero (O9) |
| 67 | Black Widow, Deadly Hunter | ◇ | Hero; deathtouch draw (O9) |
| 68 | Agent Venom | ◇ | Hero; flash menace, draws on nontoken deaths (O9) |
| 69 | Black Widow, Daring Operative | ◇ | Hero (O9) |
| 70 | Gwenom, Remorseless | ★ | Hero, but deathtouch lifelink + play from the top on attack — raw power (O9) |
| 71 | Symbiote Spider-Man | ◇ | Hero (O9) |
| 72 | Superior Spider-Man | ★ | copies a creature card in ANY graveyard; a Villain copy counts (E7) |
| 73 | Morlun, Devourer of Spiders | ★ | X-burn lifelink Villain, scales late (copy is X=0, E6) |

## 5. Consolidated plan (live)

Measured on a scratch 100 (`deck.py tier/legal/consistency` on a path; placeholder basics
for the 37 lands): **Historic Brawl-legal, floor A — interaction 17, card advantage 8 (an
under-count, O13), sum 25 against an A line of 12 and 19.** Avg MV 3.7.

### Core — the 40 ★★/★★★ pile cards
★★★: Norman Osborn; Baron Strucker; Crimson Cowl; The Spot's Portal; Tombstone; Doctor Doom,
Unrivaled; Kingpin, Wilson Fisk; Black Cat; M.O.D.O.K.; M.O.D.O.K., Evil Intellect; Doctor
Doom; Prowler; Doctor Octopus; Avengers: Under Siege; Leader, Super-Genius; Kang the
Conqueror.
★★: Doom Reigns Supreme; Construct a Cosmic Cube; Citizen V; Criminal Enterprise; Doombot
Harbinger; Crossbones; Thunderbolts Conspiracy; Madame Masque; Radioactive Man; The Masters of
Evil; Kang, Temporal Tyrant; Morbius; Vulture, Scheming Scavenger; Tiger Shark; Bullseye;
Madame Hydra; Loki, God of Mischief; Graviton; Mysterio's Mirage; Chameleon; Mysterio, Master
of Illusion; Vulture, Feathered Fiend; Victor Timely; Shocker.

### From outside the pile (12)
- Engine (O12): Ultimo, Civilization's End; Elektra, Daughter of the Hand (owned); Liliana,
  Dreadhorde General (owned).
- Removal, all mana value ≤4 so Victor Timely can recast them: Infernal Grasp, Go for the
  Throat, Heartless Act (owned), Hero's Downfall (owned), Bitter Triumph (owned), Feed the
  Swarm (owned), Kolaghan's Command.
- Rocks: Arcane Signet, Talisman of Dominance, Talisman of Indulgence.

### The ★ fill (8 of 13)
Hammerhead (sac outlet), Madame Hydra, Reanimated, Thanos, Taskmaster, Scientist Supreme of
A.I.M., Superior Spider-Man, Morlun, Valentina Allegra de Fontaine.
**Left out on castability:** Baron Helmut Zemo ({B}{B}{B}, 13% on turn 3), Electro ({R}{R},
26% turn 3), Red Hulk ({R}{R}, 35% turn 5) — red is a light third colour (O7). Shocker is
also {R}{R} but kept: as a copy target it is removal every attack.
**Out:** Bob, Viper (attack alone, O3); the Heroes except Superior Spider-Man (O9);
Villainous Syndication, Villainous Wrath, Minotaur, Count Nefaria, Titanium Man, Boomerang,
Immortus, Loki Laufeyson, Loki, God of Lies, Living Laser, Decoy Ploy, Undead Hand Ninja,
White Widow, Scorpion, Gwenom, Electro, Red Hulk, Baron Helmut Zemo.

### Lands (37, decided in /draft-deck with `suggest --lands`)
Black is the main colour (most double pips); blue second; red light. Owned fixing to
start from: Watery Grave, Blood Crypt, Steam Vents, Villainous Hideout, Castle Doom. Crafts to
weigh: Command Tower, Xander's Lounge (the U/B/R triome), Sulfurous Springs.

### REVISED 2026-10-21 — pile-first (owner: every pile card was added for a reason)
The arithmetic: 99 slots, 36 lands, so 63 nonland, and the pile alone is 73. Measured on a
scratch 100: **58 pile cards + Ultimo, Elektra, Liliana + Infernal Grasp, Heartless Act =
63 nonland, 36 lands — Historic Brawl-legal, floor A at exactly interaction 12** (card
advantage 11, an under-count). With 60 pile cards and no removal spells the floor reads B
(interaction 10). No rocks; Kingpin and Avengers: Under Siege make Treasures.
**The 15 pile cards that do not fit**, weakest first, each returnable at the cost of a kept
card: Bob, Viper (attack alone — Loki never does), Boomerang, Villainous Syndication, Titanium
Man, Minotaur, Count Nefaria, Immortus, Loki, God of Lies, Living Laser, Electro, Red Hulk,
Baron Helmut Zemo (colour-hungry), Symbiote Spider-Man, Loki Laufeyson.
Kept from the original "out" list: all four Black Widow/Agent Venom Heroes, Gwenom, Superior
Spider-Man, Villainous Wrath (E8), Decoy Ploy, Undead Hand Ninja, White Widow, Scorpion (E9).
The five other outside removal spells and the three rocks are dropped to make room.

### Protect list (what `cuts` cannot see)
Tombstone, Black Cat, Elektra, Ultimo, Shocker, Doombot Harbinger, Madame Masque, Tiger
Shark — their value is the COPY of their enters trigger every attack (L1/O2/O12), which no
ranking models. Kingpin, Criminal Enterprise, Liliana, Thanos — they cash the copy's death
every turn (L5). Leader, Super-Genius and Black Cat score no role at all (O13).
