# Samut Brawl pile (deck 88) — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once deck 88 is drafted, the owner signs off, and these
findings are folded into its `#: notes:`. A scratchpad, not a source of truth — decks/ are.

**Source list:** the owner's 104-card pile (2026-10-21), commander Samut, the Driving Force
(DFT 222). Every card is inside the W/R/G identity and Historic Brawl-legal (checked in the
pull). 58 of the 104 read unowned, and owned counts are lower bounds (G-10). Cards already
in other decks do not matter for a new deck: decks share the collection.

## 1. The decision framework

Samut, the Driving Force — {3}{R}{G}{W} 4/5 first strike, vigilance, haste. Start your
engines! Other creatures you control get +X/+0 and noncreature spells cost {X} less, where X
is your speed (max 4).

- **S1 — Speed starts only when a Start-your-engines permanent arrives.** Speed goes up once
  on each of YOUR turns when an opponent loses life. If Samut is the only engine card, she
  lands at speed 1, hits for 2 (haste), and reaches max speed two turns later. Every card
  that STARTS the engines earlier is worth more than its printed text, because it lets Samut
  land already at speed 3–4. The pile has none besides Samut, so the starters come from
  outside: Point the Way (G, owned), Hazoret, Godseeker (R, owned), Loxodon Surveyor (G,
  owned), and the Raceway lands (Amonkhet U / Avishkar C / Muraganda R — a land slot that
  costs no spell slot).
- **S2 — The discount is generic-only and arrives with Samut.** At speed X, a noncreature
  spell costs X less GENERIC (coloured pips stay). So Earth's Mightiest Heroes {4}{G}{G}
  becomes {G}{G}, Garruk {2}{G}{G} becomes {G}{G}, Unnatural Growth {1}{G}{G}{G}{G} becomes
  {G}{G}{G}{G}. Tiered costs count, so Tifa's Limit Break's Meteor Strikes tier becomes
  free. Power-up and other ACTIVATED costs are not spells and are NOT discounted. Grade on
  the printed cost first: the deck must function before Samut lands.
- **S3 — Power is the deciding number, toughness is not.** +X/+0 meets every "power 4 or
  greater" / "power 7 or greater" gate and scales every power-READING effect: fight and bite
  (Punishing Punch deals twice power), Selvala's and Doc Samson's mana, Giant-Man's mana,
  Master's Guidance's draw, Emperor Apatzec's haste, Tifa, Martial Artist's extra combat.
  Toughness is not boosted, so a FIGHT (two-way) still risks the creature; a BITE
  (one-way — Punishing Punch, Hulk's Thunderclap) does not. Prefer bites.
- **S4 — Speed needs life loss every one of your turns.** Haste (Samut, Hazoret's Champion
  gives it to the whole team; earthbent lands have haste), a guaranteed attacker (Alien
  Invasion), pings (Roxanne's Meteorites) and trample/evasion keep speed rising. A turn
  without opponent life loss is a turn the commander does not scale.
- **S5 — Format: Historic Brawl, 100 cards singleton, 25 life, 1v1, free first mulligan.**
  The tier floor scales ×1.67: A needs interaction 12 and interaction + card advantage 19.
  Green is the main colour, red second, white lightest (only the G/W and Naya gold cards).
  Green's interaction is fight/bite, and this pile is rich in it.
- **S6 — Cards that fight our own board (G-42).** Hulk, Always Angry destroys ALL artifacts
  (our Twitching Doll, Thunderous Velocipede, Sledge-Class Seedship, Roxanne's Meteorites);
  Incandescent Aria hits our nontoken creatures (dorks die, big bodies survive); Tangle
  also prevents OUR combat damage if cast on our turn (only an opponent's-turn fog).
- **S7 — Pick a spine; the pile holds about seven mini-themes.** Gamma/Hulk, landfall +
  earthbend, +1/+1 counters, power-up, Bears, mana creatures, Naya legends. The deck holds
  ~63 nonland cards. Themes that SCALE with Samut's +X power (power payoffs, bites, power
  mana, double/triple power) beat themes that merely coexist with her (Bears, lifegain).
- **S8 — Mana creatures double as attackers.** A dork with +4 power is a real threat, and the
  power-to-mana cards turn Samut into a mana engine. Ramp is how a 6-drop commander lands on
  turn 4–5; it is also what pays for Zacama, Hugs X, Rocco X, Minsc X and the power-ups.

## 2. Standing error list

- E1: Ownership is not grading (Player Profile). 58 cards read unowned, including the
  commander; craft cost is reported at the end only.
- E2: Do not credit Samut's discount to an activated ability (power-up, Zacama's abilities,
  Beorn's Hospitality's animation, Minsc's X): only SPELLS are discounted (S2).
- E3: Ayula "fights" only when another BEAR enters. Beorn the Fierce turns a creature into a
  Bear at combat, which is not an enter, so Ayula needs actual Bear cards or tokens (only
  Dancing from Dark to Dawn's landfall makes them).

## 3. Cross-batch observations

- O1: No speed starter in the pile besides Samut (S1). This is the single biggest structural
  gap, and it costs no wildcards: Point the Way, Hazoret, Godseeker and Loxodon Surveyor
  are owned.
- O2: Bites outnumber fights: Punishing Punch, Hulk's Thunderclap, Ravenous Tyrannosaurus's
  attack trigger, Cabaretti Charm, Annie Joins Up. With Samut's +X power each is one-sided
  removal that toughness cannot answer (S3).
- O3: The pile's "power reads" cluster is the real engine: Selvala, Doc Samson, Giant-Man
  (mana); Master's Guidance, Emperor Apatzec Intli IV (cards); Warden of the Chained, Tifa,
  Martial Artist (gates); Unnatural Growth, Tifa's Limit Break, Mightform Harmonizer,
  Absorbing Man and Titania (multipliers). All of them read +X power.
- O4: Bears (Ayula, Beorn's Hospitality, Dancing's tokens) and lifegain (Eumidian
  Terrabotanist, Titanbones, Dina, Greenhouse Propagator's life) do not reach a payoff
  density; they are the first cuts (S7).

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

### Batch 1 (cards 1–35)

| Card | Verdict | Note |
|---|---|---|
| Samut, the Driving Force | commander | The payoff (S1–S3). |
| Samut, Vizier of Naktamun | ★★ | 3-mana first strike/haste attacker; draws whenever a creature that entered THIS turn connects. With team haste (Hazoret's Champion) every new creature draws on contact (S4). |
| Samut, the Tested | ★★ | +1 double strike on a +X creature; −2 is 2 damage split (removal). Noncreature, so discounted to {R}{G} (S2). |
| Samut, Hazoret's Champion | ★★★ | {1}{R}: creatures you control have haste. Every creature hits the turn it lands, which is what keeps speed rising (S4) and turns on Vizier's draw. |
| Jennifer Walters | ★★ | 2-drop that stops opponents casting on your turn — protects the alpha strike and the fights. Late transform to a damage-redirect She-Hulk. |
| Tifa's Limit Break | ★★ | {G} instant: +2/+2, or double, or triple power. Tiered cost is discounted (S2), so doubling is free at speed 2+. A finisher on a +4 creature. |
| Badgermole Cub | ★★ | Earthbend 1 (a hasty land creature) and +{G} whenever you tap a creature for mana — doubles every dork (S8). |
| Ayula, Queen Among Bears | ✗ | Needs Bears ENTERING (E3). Two real Bear sources in the pile. |
| Beast Mode | △ | +2/+2 trample pump; filler next to the better pumps. |
| Beorn's Hospitality | ◇ | Landfall counters; only if landfall becomes the spine. |
| Eumidian Terrabotanist | ✗ | Landfall life gain, no payoff (O4). |
| Feral Ferocity | △ | +4/+4 for {G} after the discount; a combat trick, not removal. |
| Great Divide Guide | ★★ | Lands and Allies tap for any colour — fixing in three colours; Toph ×3 and Bumi are Allies. |
| Tangle | △ | A fog; only on an opponent's turn (S6). |
| Tifa Lockhart | ◇ | Landfall doubles power; strong only in a landfall build. |
| Torgal, A Fine Hound | ★ | Any-colour dork; the Human bonus is small (one Dog/Wolf). |
| Twitching Doll | ★ | Any-colour dork that becomes Spiders late. An artifact (S6 vs Hulk, Always Angry). |
| Advancing the Spirit | ◇ | Cantrip + one free power-up per turn; only four power-up cards in the pile. |
| Beastmaster Ascension | ★ | Seven attacks → +5/+5 team. Easy in a hasty attacking deck; a second finisher. |
| Blanchwood Armor | △ | Counts Forests only; a three-colour manabase holds maybe 8–10. |
| Epic Fight | ★★ | Double and/or fight; at {G} after the discount, removal plus a finisher mode (S3: a fight, not a bite). |
| Enduring Vitality | ★★★ | Every creature taps for any colour, and it comes back as an enchantment. The fixing engine of a three-colour creature deck (S8). |
| Greenhouse Propagator | ★ | {G} dork; the life gain is incidental (O4). |
| Jiang Yanggu, Wildcrafter | ◇ | Countered creatures tap for any colour; only with a counters spine. |
| Master's Guidance | ★★★ | End step: draw if you control a creature with power 4+ — every turn once Samut lands (S3), and the 4-power bodies do it alone. Two legends attacking adds counters. Card advantage the deck otherwise lacks. |
| Mole Man, Moloid Master | ◇ | Landfall tokens, lands from the graveyard; landfall build only. |
| Nissa, Voice of Zendikar | ★ | +1 chump Plant, −2 counter on each creature; {G}{G} after the discount. |
| Origin of the Hulk | △ | A token, two counters, a pump; slow. |
| Punishing Punch | ★★★ | Instant bite for twice power (one-sided, S3). {G} with two creature cards in the graveyard. The best removal in the pile. |
| Selvala, Heart of the Wilds | ★★ | {G},{T}: X mana where X = greatest power. With Samut out, X is 8+ (S8). The draw is symmetric but rarely the opponent's. |
| Sledge-Class Seedship | ◇ | Stations off a creature's power (+X fast); at 7 a 4/5 flier that cheats creatures in. A slow artifact (S6). |
| Thunderous Velocipede | ★ | Every creature enters with +1 or +3 counters; a 5/5 trample vehicle. |
| Traveling Chocobo | ◇ | Lands from the top and doubled land triggers; card advantage in a landfall build. |
| Way of the Paradox | ✗ | A blue Jace token and an extra land drop; off plan. |
| Worldweave | ★★ | Every creature spell puts a land onto the battlefield (ramp + landfall), Alchemy, Brawl-legal. |
