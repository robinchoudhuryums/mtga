# Bear-Wolf pile (deck 105) — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** 100 new cards the owner added for deck 105 (Den of Bears and Wolves,
Historic Brawl, Sarulf, Realm Eater). Delete once the swaps land and the findings are folded into
deck 105's `#: notes:`. The board is the existing Builder project `builds/bear-wolf`.

**Source list:** `.cycle/bear-wolf-pile.txt` (100 cards; all resolve, all Historic Brawl legal,
all inside Sarulf's black-green identity). `screen`: 16 KEY / 25 role-player / 59 tangential;
two ★ strict upgrades flagged (of Llanowar Elves and of Cultivate).

## 1. The decision framework

Deck 105 live vector (2026-11-22): floor A · interaction 16 · card advantage 14 · protection 7 ·
board power 124 · avg MV 3.45 · 18 Bears · 10 Wolves · WIDE (wide 14 / tall 1).

- **F1 — Bears ENTERING is the first number.** Ayula (in the 99) turns each entering Bear into
  two counters or a fight; Beorn the Fierce pumps Bears and makes a creature a Bear each combat;
  Goreclaw discounts power-4 creatures. Bear TOKENS count.
- **F2 — the POWER-4 GATE.** Garruk's Uprising, Colossal Majesty, Garruk, Curse Breaker, Vaultborn
  Tyrant, Elemental Bond, Rhonas, Fanatic of Rhonas, The Chief Warg, Wilderland Scrounger all read
  "a creature with power 4 or greater". A body that is 4+ power on arrival is worth more than its
  text; a card that only pays once the gate is on is a CONSUMER (deck 69's lesson: don't stack them).
- **F3 — SARULF'S WIPE IS SYMMETRICAL.** Removing its counters exiles EACH OTHER nonland permanent
  with MV ≤ N, yours included. Cheap permanents (1–3 MV) are the ones a wipe takes; 4+ MV threats
  and indestructible / self-returning cards survive. Not a reason to cut every cheap card — the
  wipe is optional — but a tiebreak between two similar cards.
- **F4 — Wolves are the second tribe** (Nightpack Ambusher and Spider-Ham pump them). A Wolf card
  is worth a little more than its text; a Werewolf only counts for Wolf-and-Werewolf cards.
- **F5 — interaction is already 16** (A needs 12 at 100 cards). New removal must beat a current
  piece, not just be removal.
- **F6 — card advantage is 14**; a repeatable draw engine that reads the deck's real state (big
  bodies attacking) is the most valuable new role.
- **F7 — ownership is information only** (Player Profile).

## 2. Standing error list

(none yet)

## 3. Cross-batch observations

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

### Batch 1 (cards 1–34)

| # | Card | Verdict | Note |
|---|------|---------|------|
| 1 | Sauron, the Necromancer | ★ | 5-mana 4/4 menace (F2 body); attacks reanimate a graveyard creature as a temporary 3/3. Graveyard fill is incidental here. |
| 2 | Flaxen Intruder // Welcome Home | ★ | Adventure makes three 2/2 Bears = three Ayula triggers (F1); the 1-drop half answers an artifact/enchantment. |
| 3 | Beorn's Hospitality | ◇ | Landfall counters; becomes a land-count Bear for 7. Slow. |
| 4 | Owlbear Shepherd | ★★ | Draws each end step when total power is 8+ — trivial with this board (F6). 3 MV (F3 risk). |
| 5 | Lukamina, Moon Druid | △ | Seeks a land; specialize needs six lands. Little here. |
| 6 | Ursine Guide | ◇ | Already benched: its Bear Cub engine needs spells not from your starting deck. |
| 7 | Toski, Bearer of Secrets | ★★ | Indestructible; a card whenever any creature connects (F6). Must attack as a 1/1, but indestructible. |
| 8 | Titania's Command | ◇ | Two Bears (two Ayula triggers) plus counters on everything; 6 mana. Benched before. |
| 9 | Copper Host Crusher | ◇ | 8/8 trample hexproof Bear; Goreclaw makes it 6. Top-end only. |
| 10 | Argoth, Sanctum of Nature | ★★ | Untapped with a legendary green creature (Sarulf is one); {2}{G}{G}: a 2/2 Bear — an Ayula trigger mana sink. For a Forest. |
| 11 | Mirkwood | ★ | Tapped black-green dual that sacrifices for two counters on a Bear or Wolf. For a Forest. |
| 12 | Forebear's Blade | ★ | +3/+0 trample turns any 1-2 power body into a gate-opener (F2) and moves when it dies. |
| 13 | Nighthowl Pursuer | ◇ | 1-drop Wolf that is a 3/3 menace attacker once the gate is on (consumer, F2). |
| 14 | Ravening Warg | ◇ | 2-drop deathtouch Wolf; gate consumer. |
| 15 | Rhovanion Rampager | △ | Sacrifices a creature to grow; the deck does not want to sacrifice its bodies. |
| 16 | Vincent Valentine // Galian Beast | ★ | Counters equal to the power of each opposing creature that dies — 16 removal spells feed it; flips to trample lifelink. |
| 17 | Ascendant Packleader | ◇ | 1-drop Wolf that grows on every 4+ MV spell (most of the deck). F3 risk. |
| 18 | Tenacious Pup | △ | Cut once already: a 1/2 and a one-shot boon. |
| 19 | Packsong Pup | △ | Grows by one a turn with another Wolf; small. |
| 20 | Torgal, A Fine Hound | ◇ | Any-colour mana dork that is a Wolf; its Human clause is dead here. |
| 21 | Wargling | ◇ | Gate consumer (deck 69 trimmed it for that reason). |
| 22 | Werewolf Pack Leader | ★★ | 2-mana 3/3 that draws when you attack with total power 6+ (F6). Not a Wolf. |
| 23 | Cemetery Prowler | ★ | 3-mana 3/4 Wolf; graveyard exile on enter/attack and a creature discount. |
| 24 | Hound Tamer // Untamed Pup | ◇ | Counter sink; night side gives Wolves trample. Day/night is fiddly. |
| 25 | Howlpack Resurgence | ◇ | Flash Wolf anthem (+1/+1 trample) with 10 Wolves. |
| 26 | Howling Moon | ◇ | +2/+2 to a Wolf each combat; Wolf tokens on their second spell. |
| 27 | Shrill Howler | △ | Evasion against small blockers; slow to flip. |
| 28 | Varis, Silverymoon Ranger | ◇ | Ventures on creature casts; a dungeon completion makes one Wolf. Slow payoff. |
| 29 | Weaver of Blossoms | △ | 3-mana mana creature; the deck has better ramp. |
| 30 | Garruk Relentless | ★★ | Now legal (black-green): 3 damage to a creature, or a Wolf a turn; flips to deathtouch Wolves and a tutor. |
| 31 | Geistpack Alpha | ★★ | 4-mana 5/4 trample Wolf — a gate-opener on arrival (F2), Goreclaw-discounted; dies into a seek. |
| 32 | Lupine Harbingers | ★ | 4/4 haste trample Wolf; foretold it grows. |
| 33 | Howlpack Piper // Wildsong Howler | ★ | Puts a creature from hand onto the battlefield each turn (Bears → Ayula), untaps for Wolves. |
| 34 | Mantle of the Wolf | ◇ | +4/+4 makes a gate-opener; two Wolves when it leaves. An Aura. |

## 5. Consolidated plan (live)

(after the last batch)
