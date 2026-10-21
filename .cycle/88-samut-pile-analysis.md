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
