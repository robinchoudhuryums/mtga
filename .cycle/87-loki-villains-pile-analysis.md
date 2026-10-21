# Loki villains pile (new deck 87) — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once deck 87 is drafted and these findings are folded into its
`#: notes:`. A scratchpad, not a source of truth — decks/ are.

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

## 5. Consolidated plan (live)
(after batch 3)
