# Star Trek pile (2026-11-12) — analysis (TEMPORARY working doc)

**Status: IN PROGRESS — graded, awaiting the owner's pick of directions.** Delete once the decks it
seeds are drafted and the findings are folded into their `#: notes:`. A scratchpad, not a source of
truth — decks/ are.

**Source list:** `.cycle/trek-pile.txt` (169 distinct cards). Not aimed at an existing deck, so cards
other decks already run were KEPT (25 of them; copies are shared across decks). Oracle text was pulled
from Scryfall directly: the TRK/TRC/SDS printings are not in card-pool.csv until the 2026-11-13 refresh
(G-79), so `screen`, `resolve` and the Builder cannot read them yet. **The Builder project waits for the
refresh and a drafted deck id** (builder.py needs both).

## 1. The decision framework

Two directions from the owner, plus whatever surfaces. Column A = WUB Borg artifact creatures,
column R = five-colour (rainbow).

1. **Format split decides the shape.** Every TRC / SDS / older-set card in the pile is Historic Brawl
   only (not Standard, not Standard Brawl). That includes FIVE of the Borg deck's fifteen payoffs:
   Locutus of Borg, The Borg Queen, Borg Queen Perfection Manifest, Bio-Asset Allocator and Battle of
   Wolf 359. So the Borg deck is a **Historic Brawl** deck; a Standard / Standard Brawl version loses its
   best cards. The rainbow deck's commander, Captain Benjamin Sisko, IS Standard-legal, but Sisay,
   Kenrith, Golos, Karn's support and Jhoira are Historic-only, so it is also strongest as Historic Brawl.
2. **A (Borg): the number is ARTIFACT CREATURES.** Affinity (Borg Cube), the anthems (The Borg Queen,
   Perfection Manifest), the evasion (Organic Avulsion Unit, Cube's 12+ flying), the double strike
   (Primary Unimatrix Adjunct), the card draw (Hive Mind Coprocessor, Collation Trimatrix) and the
   one-sided sweepers (Battle of Wolf 359, Crystalline Entity) all count artifact CREATURES. A plain
   artifact counts only for Conquest Mission. Grade each card by what it ADDS to that count (tokens
   included: Borg tokens, Robots, Synthesizer Labship's animation) or what it PAYS per artifact creature.
3. **A Spacecraft is an artifact creature only after station.** Station taps another creature at
   sorcery speed for counters equal to its power, so it competes with attacking. Cheap stations
   (Synthesizer Labship 9, Oberth 6, Enterprise-A 6) are creatures in a turn or two; 12-20 is a late
   game. Geordi La Forge doubles counters, Zefram Cochrane adds two, Warp Core adds two a turn, Brad
   Boimler adds one per tap. Assimilate (Borg Cube, both Borg Queens, Death Is Irrelevant) turns any
   creature into a Borg artifact creature — that is how the deck steals threats.
4. **R (rainbow): Sisko's numbers are DILEMMAS and OFFICERS.** You face a dilemma whenever you choose
   modes for a spell OR ability (Choose one, Spree, Tal Shiar Operative's attack). Sisko makes an Officer
   per dilemma at your end step, and his {2}{W}{U}{B}{R}{G} activation casts free spells with MV up to
   your Officer count. Payoffs that also read dilemmas: Jett Reno, Seven of Nine (UB), The Caretaker.
   The pile has only ~12 modal cards, so a Sisko deck must draw most of its modal spells from the pool.
5. **Strange new worlds counts DIFFERENTLY NAMED lands.** A 100-card singleton deck with the ten shocks,
   the Planets and the Anomaly lands naturally has 10+ names; a 60-card deck with basics has few. This
   favours the rainbow Brawl build (Excalbian Gamemaster, Seven of Nine Unassimilated, Suus Mahna,
   Ensign Chekov, Species 8472).
6. **Owner's removal rule:** no removal that benefits the opponent. Malfunctioning Holodeck (O-ring),
   Excelsior, Dirgecraft and In the Pale Moonlight are fine; The Measure of a Man returns the card, so it
   is a tempo play or a blink for your own ETB.
7. **Brawl colour identity**: a WUBRG-identity card (Karn, Golos, Haunted Screen, Bringer, Chamber Sentry,
   Engineered Explosives is colourless) cannot go in the WUB deck however castable it is.

## 2. Standing error list

1. Do not count a Spacecraft as a creature before its station number (rule 3).
2. Officer TOKENS are red; an Officer creature card of any colour counts for Sisko too (Janeway, Kirk,
   Picards, Operations Officer, Cetacean Ops, Tal Shiar Operative, Seven of Nine Unassimilated, Worf).
3. Badgey, Hemmer, Jett Reno and Brad Boimler trigger on BECOMING TAPPED — station taps them, so in a
   Spacecraft deck they fire every turn without attacking.

## 3. Cross-batch observations

- **The Borg deck is the strongest, most coherent direction in the pile**: 18 WUB artifact creatures,
  15 Spacecraft, 15 payoffs, two one-sided sweepers, and three commander candidates.
- **Spacecraft/station is not a separate deck**: the W/U/B Spacecraft and the station support (Geordi,
  Zefram, Warp Core, Labship, Enterprise-D, Rutherford, Hemmer) fold into the Borg deck, since a stationed
  Spacecraft is an artifact creature.
- **Rainbow = Sisko Officers + dilemmas + strange new worlds.** Distinct from the roster's 5c decks
  (17 Spectrum good-stuff, 35 five-colour ninjas, 76 Dragons, 90 Spirit World shrines) because its engine
  is modal spells and Officer tokens, not bombs or tribes.
- **Variant signals (not asked for):** GW counters (Dr. M'Benga doubles counters, Phlox, The Doctor,
  Bristly Bill, Rishkar, Mikaeus, McCoy, Picard Steadfast, Test of Conviction, Pure Energy) and green
  landfall (Loot, Janeway, Tatyova, Cleveland Booker, Jake Sisko, Syndicate Liquidators, Exploratory
  Mission, Hit It!). Both overlap existing roster themes; neither is pursued unless the owner asks.

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out (– = wrong colour identity).
[H] = Historic Brawl only.

### Batch 1 (1-30)
| Card | A Borg | R Rainbow | Note |
|---|---|---|---|
| Captain Benjamin Sisko | – | ★★★ cmdr | Officers per dilemma; free spells with MV up to Officers |
| Borg Cube | ★★★ anchor | ◇ | affinity for artifact creatures; assimilates what it exiles; 12+ team flying |
| The Eternity Elevator | ★ | ★ | 3 colourless mana; 20+ station is late |
| Weather Maker | ◇ | ★ | any-colour rock, landfall burn |
| Warp Core | ★ | ★ | land fetch + 2 charge a turn |
| U.S.S. Enterprise-D | ★★ | ★ | play the top card each turn counters land; creature at 7 |
| Zefram Cochrane | ★★ | – | cast artifacts off the top; Spacecraft +2 counters |
| Geordi La Forge | ★★ | – | doubles charge counters (halves every station) |
| Captain Jean-Luc Picard | ★★ | ★★ | anthem + an Officer per creature/Spacecraft spell; 7 Officers fetch a Spacecraft |
| Romulan Bird-of-Prey | ★ | – | 2-mana hexproof ship, 8 to animate |
| Drill Too Deep | – | ★ | modal; 5 charge or artifact removal |
| Systems Override | – | ◇ | threaten |
| Sarcophagus | – | ◇ | red ship |
| Gardenize | – | △ | |
| Excalibur II | ◇ | △ | needs lifegain (Locutus, Noctis, Bio-Asset) |
| Engineered Explosives | ◇ | ★ | sunburst sweeper, symmetric |
| Lost Jitte | ★ | ★ | equip 1; modal counter use |
| Rimefire Torque | ◇ | ◇ | name Borg: copies a spell every third Borg |
| In the Pale Moonlight | ★★ | ★ | edict + Clue + two Romulans |
| Artificial Anomaly | ★ | ★ | utility land, New Planet any colour |
| Spatial Anomaly | – | ★ | red identity |
| Oberth-Class Starship | ★ | – | Plains fetch; creature at 6 |
| The Seriema | ★★ | ★ | tutors a legendary creature; indestructible tapped legends |
| U.S.S. Enterprise-A | ★★ | ★★ | three Officers, ward 2, lifelink flier at 6 |
| U.S.S. Excelsior | ★★ | ★ | ETB destroys a tapped creature |
| Adagia | ★ | ◇ | W Planet, copies an artifact at 12 |
| Synthesizer Labship | ★★ | – | 1 mana; at 2+ animates an artifact each combat |
| H.M.S. Bounty | ◇ | – | Whale tutor (Cetacean Ops), extra turn |
| Uthros | ★ | – | U Planet; U per artifact at 12 |
| Susur Secundi | ◇ | ◇ | B Planet |

### Batch 2 (31-60)
| Card | A Borg | R Rainbow | Note |
|---|---|---|---|
| Entropic Battlecruiser | ★ | ◇ | discard drain, 3/10 |
| Susurian Dirgecraft | ★★ | ★ | ETB edict, flier at 7 |
| Sledge-Class Seedship | – | ◇ | green |
| U.S.S. Voyager | – | ★ | two lands |
| Larval Scoutlander | – | ◇ | |
| Evendo | – | ◇ | |
| Infinite Guideline Station | – | ★★★ | Robots per multicoloured permanent; draws on attack |
| Dawnsire | ★ | ★ | 100 damage per attack at 10+ |
| Deep Space 9 | ◇ | ◇ | 9 mana |
| Command Subadjunct | ★★ | – | 1-drop Borg; artifact creatures have vigilance |
| Set Phasers to . . . | ★ | ★★ | modal stun / 3 to an attacker |
| Antagonist Incorporator | ★★★ | – | artifact creatures make Borg tokens on damage |
| Sisay [H] | – | ★★ | legendary toolbox, grows per colour |
| Brad Boimler | ★ | ◇ | +1 counter on station taps; lifelink |
| Picard, Leading by Example | ◇ | ◇ | |
| Pure Energy | ◇ | ◇ | |
| Shields Up! | ★★ | ★ | hexproof + indestructible on an artifact or creature |
| Tactical Officer | ◇ | ◇ | |
| Test of Conviction | ★ | ★★ | modal: team counters or draw two |
| Dr. Beverly Crusher | ◇ | ◇ | lifegain counters (GW signal) |
| Conquest Mission | ★★★ | – | a Borg token per nontoken artifact |
| Hologram Janeway | ★ | ★ | artifact creature Officer |
| Malfunctioning Holodeck | ★★ | ★★ | ward 2 O-ring |
| Rutherford | ★★ | ★ | digs an artifact; counters per Spacecraft cast |
| The Measure of a Man | ★ | ★ | temporary exile + Clue, or blink your own |
| Federation Field Medic | ◇ | ★ | modal ETB |
| Dr. McCoy | ◇ | ◇ | counters (GW signal) |
| Peace in Our Time | ◇ | ◇ | alt-win, symmetric draw |
| Primary Unimatrix Adjunct | ★★★ | – | artifact creatures have double strike |
| Shuttle Ace | △ | △ | |

### Batch 3 (61-90)
| Card | A Borg | R Rainbow | Note |
|---|---|---|---|
| Una Chin-Riley | ◇ | ◇ | |
| Excalbian Gamemaster | ◇ | ★★ | Officers per land name; death counters |
| Subspace Anomaly | ★ | ★ | two Officers + New Planet |
| Data, New Life | ★ | – | 2-mana artifact creature, grows per draw |
| Seven of Nine, Unassimilated | ★ | ★★ | artifact creature; land-name payoff |
| Jett Reno | ★ | ★★ | dilemma counters; draws when tapped at 4+ |
| Test of Priorities | ★ | ★★ | modal draw / blink |
| Anthropological Mission | ◇ | ◇ | |
| Consider the Prime Directive | ★ | ★★ | modal counter / stun + draw |
| Lieutenant Commander Data | ★★ | ★ | artifact creature grows; counters into cards |
| Scotty | ◇ | ◇ | |
| Suus Mahna Practitioner | ◇ | ★ | cheap tapper with many land names |
| Cetacean Ops | ◇ | ◇ | Whale for Bounty |
| Flare of Fortitude [H] | ★ | ★ | free hexproof + indestructible turn |
| Operations Officer [H] | ◇ | ★ | Officer, draws |
| Kenrith [H] | – | ★★ | 5c ability engine |
| Picard, Steadfast Captain [H] | ◇ | ◇ | |
| Mikaeus [H] | ◇ | ◇ | GW signal |
| Ensign Pavel Chekov | ◇ | ★ | land-name theft |
| Make It So | ◇ | ★ | modal; Officer + draw two |
| Mr. Spock, Science Officer | ★★ | ★★ | draws two instead of one |
| Dominion Saboteur | ★ | ★ | clone |
| Empress Galina [H] | ◇ | ◇ | |
| Spock, Logical Choice [H] | ★★ | ★★ | {T}: draw |
| The Caretaker | ◇ | ★★ | dilemma turns into a free spell each end step |
| Gaseous Anomaly | ★ | ★ | land, draw two + New Planet |
| Collation Trimatrix | ★★ | – | tap three artifact creatures: draw |
| Tal Shiar Operative | ◇ | ★ | modal attack trigger |
| Grand Nagus Zek | ◇ | ◇ | |
| Overflow Submatrix | ★★★ | – | an artifact creature from the graveyard every turn |

### Batch 4 (91-120)
| Card | A Borg | R Rainbow | Note |
|---|---|---|---|
| Organic Avulsion Unit | ★★ | – | team menace |
| Badgey [H] | ★★ | ★ | drain when tapped — station taps it every turn |
| Blastoneuron | ◇ | ◇ | |
| Sela | ◇ | ◇ | |
| Sheoldred, the Apocalypse [H] | ★★ | ★★ | |
| U.S.S. Reliant | ★★ | ★ | reanimates MV 4 or less on ETB and hit |
| Bio-Asset Allocator [H] | ★★ | – | artifact creatures drain on attack |
| Battle of Wolf 359 [H] | ★★★ | – | one-sided sweeper |
| Drivnod [H] | ◇ | ◇ | |
| Hive Mind Coprocessor | ★★ | – | artifact creatures draw on damage |
| Georgiou | ◇ | ◇ | |
| Borg Queen, Perfection Manifest [H] | ★★ | – | +2/+0; assimilates from their yard |
| Gul Dukat | ◇ | ◇ | |
| Death Is Irrelevant | ★★ | – | team indestructible + an assimilation each turn; 8 mana |
| The Unicomplex | ★★ | ★ | B land, surveil or top-deck a creature |
| Brazen Bluff | – | ◇ | |
| Savvy Profiteer | – | ◇ | |
| The Wrath of Khan | – | ★ | |
| Exploratory Mission | – | ★ | landfall card flow |
| Kirk [H] | – | ★ | Officer, impulse |
| La'An | – | ◇ | |
| Grilka [H] | – | ◇ | |
| Infinite Diversity | – | ◇ | 9 mana |
| Bristly Bill | – | ◇ | GW signal |
| Jadzia Dax | – | ◇ | |
| Jake Sisko | – | ◇ | |
| Neelix | – | ◇ | |
| David and Carol Marcus | – | ★ | body + any-colour Planet |
| Loot | – | ★ | extra land |
| Rishkar [H] | – | ◇ | |

### Batch 5 (121-150)
| Card | A Borg | R Rainbow | Note |
|---|---|---|---|
| Captain Kathryn Janeway | – | ★★ | Officer; extra land; every creature explores |
| Sylvia Tilly | – | ◇ | |
| Dr. Joseph M'Benga | – | ◇ | counters doubler (GW signal) |
| Syndicate Liquidators | – | ◇ | |
| Species 8472 | – | ★ | land names; unblockable by artifacts |
| Rok-Tahk | – | ★★ | every creature taps for GG |
| Q Continuum | – | ★ | another land name |
| Hemmer | ★ | ★ | Spacecraft hexproof on your turn; loots when tapped |
| Live Long and Prosper | ◇ | ◇ | |
| Hallowed Fountain | ★★ | ★★ | |
| Godless Shrine | ★★ | ★★ | |
| Mirror Universe Intrusion | ★ | ★ | copies their creature |
| Seven of Nine | ★★ | ★★ | artifact creature; draws per dilemma |
| Jhoira [H] | – | ★ | historic draw |
| Steam Vents | – | ★★ | |
| Gowron | – | ◇ | |
| Prosper [H] | – | ◇ | |
| Blood Crypt | – | ★★ | |
| Qo'noS | – | ★ | |
| Vash | – | ◇ | |
| Ferenginar | – | ★ | |
| Hull Breach [H] | – | ★ | modal artifact/enchantment removal |
| Overgrown Tomb | – | ★★ | |
| Hit It! | – | ◇ | |
| Orion | – | ★ | |
| Stomping Ground | – | ★★ | |
| Cleveland Booker | – | ◇ | landfall signal |
| Worf, Honor-Bound Warrior | – | ◇ | (queued for deck 56-historic-brawl) |
| Phlox | – | ◇ | GW signal |
| The Doctor, EMH | – | ◇ | GW signal |

### Batch 6 (151-169)
| Card | A Borg | R Rainbow | Note |
|---|---|---|---|
| The Inner Light | – | ◇ | |
| Temple Garden | – | ★★ | |
| Tatyova | – | ◇ | |
| All Good Things . . . | – | ◇ | |
| Breeding Pool | – | ★★ | |
| Earth, Sector 001 | – | ★ | |
| Locutus of Borg [H] | ★★★ cmdr | – | 4 mana; every artifact creature that connects makes a Borg |
| The Borg Queen [H] | ★★★ | – | +2/+2 to artifact creatures; assimilates on ETB and attack |
| Isshin [H] | – | ◇ | |
| Sarek | – | ★ | creature-type draw |
| Riku of Many Paths | – | ★★ | modal-spell payoff |
| Jean-Luc Picard, Luminary [H] | – | ★★ | historic draw; Spacecraft counters |
| Crystalline Entity | ★★★ | ★ | 8-mana flier; destroys all NONartifact creatures |
| Bringer of the White Dawn [H] | – | ★ | WUBRG alt cost |
| Noctis | ★★★ (Std cmdr) | – | casts artifacts from the graveyard; Standard-legal |
| Chamber Sentry [H] | – | ★ | |
| Karn, Gilded Guardian | – | ★★ | draws per artifact colour |
| Haunted Screen | – | ★ | fixer |
| Golos [H] | – | ★★ | land fetch + free-cast activation |

## 5. Consolidated plan (live)

**Deck A — "Resistance Is Futile", WUB Borg artifact creatures, Historic Brawl (RECOMMENDED FIRST).**
Commander: **Locutus of Borg** (4 mana, lifelink; every artifact creature that connects makes a Borg
token, so the engine runs from the command zone). The Borg Queen goes in the 99 as the top-end anthem.
Alternatives: The Borg Queen as commander (7 mana, slower but an anthem every game), or Noctis for a
Standard Brawl build (loses the five Historic-only payoffs).
Core from the pile: Borg Cube, The Borg Queen, Antagonist Incorporator, Conquest Mission, Primary
Unimatrix Adjunct, Overflow Submatrix, Battle of Wolf 359, Crystalline Entity, Command Subadjunct,
Collation Trimatrix, Organic Avulsion Unit, Hive Mind Coprocessor, Bio-Asset Allocator, Perfection
Manifest, Synthesizer Labship, Enterprise-A, Excelsior, Dirgecraft, Seriema, Reliant, Rutherford,
Geordi, Zefram, Lieutenant Commander Data, Seven of Nine, Badgey, Mr. Spock, Spock Logical Choice,
Shields Up!, Malfunctioning Holodeck, In the Pale Moonlight, Death Is Irrelevant, Hallowed Fountain,
Godless Shrine, The Unicomplex. About 35 cards; the draft fills the rest from the pool (Esper artifact
creatures, removal, lands).

**Deck R — Sisko Officers & dilemmas, five-colour, Historic Brawl.** Commander: **Captain Benjamin
Sisko**. Core: Infinite Guideline Station, Captain Jean-Luc Picard, Enterprise-A, Excalbian Gamemaster,
Janeway, Seven of Nine, Jett Reno, The Caretaker, Riku, Rok-Tahk, Golos, Karn, Kenrith, Sisay, JL Picard
Luminary, the modal cards (Set Phasers, Test of Conviction / Priorities, Consider the Prime Directive,
Make It So, Drill Too Deep, Hull Breach, Federation Field Medic), the ten shocks and the Planets.
The pile holds only ~12 modal cards, but MEASURED 2026-11-12: the pool already has 533 Historic-Brawl-legal
modal cards (choose one/two/three, choose one or more, Spree), 135 of them owned — Sisko's dilemma supply is not
the constraint. (For deck A: 96 WUB artifact-creature cards in the pool beyond this pile, 15 owned.)

PROTECT (what `cuts` cannot see): Borg Cube's affinity counts artifact CREATURES (a stationed
Spacecraft counts, an unstationed one does not); Battle of Wolf 359 and Crystalline Entity are
one-sided only while the board is artifact creatures; Badgey / Hemmer / Jett Reno fire on station taps.
