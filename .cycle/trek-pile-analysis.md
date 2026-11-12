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

## 6. Deck C — Standard Bant (GWU) "Federation", owner's list (2026-11-12)

Owner's 23: Sarek, Syndicate Liquidators, Holo-Engineer, Rok-Tahk, Jadzia Dax, Replicator, Picard (read as
Captain Jean-Luc Picard — Picard, Steadfast Captain is Historic-only), David and Carol Marcus, Sickbay, MACO
Strike Team, Phlox, Subspace Anomaly, Scotty, Worf (R/W hybrid, paid with W), Neelix, Geordi La Forge,
Seven of Nine (Unassimilated — the UB one is off-colour), The Inner Light, Xindi Surveyors, Dr. Beverly
Crusher, Brad Boimler, Melkotian Adjudicator, Dominion Supervisor. All Standard-legal.

- **Spine: FEDERATION (creature-type diversity).** Sarek draws per five creature types among non-Borg
  creatures; the list's creatures carry ~19 distinct types (Vulcan, Advisor, Orion, Pirate, Human, Artificer,
  Brikar, Scientist, Trill, Officer, Soldier, Denobulan, Doctor, Klingon, Warrior, Talaxian, Xindi,
  Melkotian, Vorta) plus Illusion / Officer tokens. The other Standard Federation cards are all in these
  colours: Captain Jonathan Archer, Hoshi Sato, Saavik (flash removal), Starfleet Academy (land). That spine
  is what keeps it distinct from the roster's five Standard Bant decks (19 tokens, 65 Spiders, 67 cast from
  exile, 68 wide counters, 78 Allies).
- **Second layer: +1/+1 counters → cards**: Phlox, Dominion Supervisor (trample), Jadzia, Xindi, Liquidators,
  Brad, Neelix, Crusher, Sickbay.
- **Weak in THIS list, by count (G-61):** Geordi doubles CHARGE counters and the list has 0 charge-counter
  cards; Scotty gives beam me up to instants/sorceries and the list has 0; Melkotian Adjudicator grows per
  dilemma and the list has 0 modal cards; Seven of Nine Unassimilated wants 5+ differently named lands, few
  in a 60-card deck with basics.
- **Holo-Engineer replaces EVERY token** you would create with a 3/3 Illusion artifact creature: Officers
  (Picard, MACO, Subspace Anomaly) and Neelix's / Replicator's Food become 3/3s (upside), but David and Carol
  Marcus's New Planet LAND token also becomes a 3/3 instead of a land (a real conflict, minor).
- **Interaction gap**: the list has none. In colours: Saavik, Set Phasers to . . ., Malfunctioning Holodeck,
  Consider the Prime Directive, U.S.S. Excelsior, Shields Up! (protection).

## 7. Deck C draft v1 (superseded by v2 in section 8 — kept for the reasoning)

Owner 2026-11-12: Captain Jean-Luc Picard AND Picard, Leading by Example; Seven of Nine, Unassimilated;
then "every nonland card at ONE copy, fill with fits, upgrades and spice". Standard, 60 cards, Bant,
nonland singleton. Name: "Final Frontier" (owner may rename).
Plan: a creature-TYPE toolbox (Federation) that grows with +1/+1 counters and turns them into cards.
Sarek draws per five creature types among non-Borg creatures; Phlox draws when a countered creature
connects; Dominion Supervisor gives countered creatures trample; Dr. M'Benga doubles every counter and
gives countered creatures hexproof. Holo-Engineer turns every token into a 3/3 artifact creature.

Owner's 24 (1 each): Sarek, Federation Ambassador · Syndicate Liquidators · Holo-Engineer · Rok-Tahk,
Budding Scientist · Jadzia Dax, Living Legacy · Replicator · Captain Jean-Luc Picard · Picard, Leading by
Example · David and Carol Marcus, Creators · Sickbay · MACO Strike Team · Phlox, Unorthodox Doctor ·
Scotty, Miracle Worker · Worf, Honor-Bound Warrior · Neelix, Moral Support · Lt. Cmdr. Geordi La Forge ·
Seven of Nine, Unassimilated · The Inner Light · Xindi Surveyors · Dr. Beverly Crusher · Brad Boimler,
Eager Ensign · Melkotian Adjudicator · Dominion Supervisor.
Draft adds (6, from v0): Saavik, Stoic Student · Set Phasers to . . . · Malfunctioning Holodeck ·
Subcommander T'Pol · Captain Jonathan Archer · Deanna Troi, Psychic Counsel.
Fill (8, v1):
- Dr. Joseph M'Benga — UPGRADE: doubles every +1/+1 counter (Deanna, Crusher, Picard LbE, Sickbay, Xindi,
  Liquidators, Brad all double) and gives countered creatures hexproof: the deck's protection.
- Captain Kathryn Janeway — FIT: every creature that enters explores (a counter or a land), plus an extra
  land drop that feeds Xindi and Liquidators' landfall. Human Officer.
- Bristly Bill, Spine Sower — FIT: landfall counters, and {3}{G}{G} doubles every counter on the team.
- The Doctor, EMH — FIT: a counter, then another on each countered creature; adds Illusion to the types.
- Command Decision — interaction: kills a 4+ power creature or draws; modal, so it feeds Melkotian.
- Constable Odo — interaction: two stun counters or two Clues; modal; adds Shapeshifter and Detective.
- Hoshi Sato, Exolinguist — Federation payoff: digs as many cards as you have creature types.
- Test of Conviction — a counter on every creature or draw two; modal.
Lands (23): 1 Starfleet Academy · 1 Subspace Anomaly · 4 Temple Garden · 2 Hallowed Fountain · 2 Breeding
Pool · 1 Risa · 1 Vulcan · 1 Earth, Sector 001 · 5 Forest · 4 Plains · 1 Island. (Re-check with
`consistency` once written: the fill raised green — M'Benga GG, Bristly — and white.)
Total 37 nonland + 23 lands = 60.

Flags to carry into the file's notes (owner's cards kept, not dropped):
- Geordi: no charge counters in the list (doubles nothing) — a 3/2 Human Artificer for the type count.
- Scotty: {1}{U}{U} on ~7 blue sources; beam me up works on instants/sorceries (Set Phasers, Command
  Decision, Test of Conviction — three).
- Melkotian Adjudicator: dilemma support — Set Phasers, Command Decision, Test of Conviction, T'Pol, Odo.
- Two colourless lands (Starfleet Academy, Subspace Anomaly) in a three-colour deck: watch `consistency`.
- Holo-Engineer turns David and Carol Marcus's New Planet land token into a 3/3 instead of a land.
- Curve: seven 5-drops plus Rok-Tahk; ramp is Jadzia, David and Carol Marcus, Janeway, Rok-Tahk.
Bench (screen after the refresh): Support Mission (a second Deanna Troi), Emergency Medical Hologram,
Wesley Crusher, Dr. Leonard "Bones" McCoy, Culber and Stamets, Cold-Blooded Crew, Dr. McCoy Surly Surgeon,
Sylvia Tilly, Captain Pike (few land names at 60), Shields Up!, Pure Energy, Type-2 Phaser, I'm a Doctor.
SPICE, offered with a warning: Kobayashi Maru Scenario — three good upkeeps (bounce, draw two, two
Officers), then the fourth mode is "you lose the game"; nothing in the list removes your own enchantment.

## 8. Deck C draft v2 — STAGED, the list to write as deck 99 after the 2026-11-13 refresh

Owner 2026-11-12: Support Mission for sure; likely Sylvia Tilly, Shields Up!, Captain Pike; maybe Wesley
Crusher; asked about 70,000 Light-Years from Home, Antagonist Incorporator, Dr. McCoy Surly Surgeon, Q
Continuum, Captain Jonathan Archer, Hologram Janeway, Amok Time, Forever Joined, Warp Core, Captain
Kathryn Janeway, Common Goal.

Changes from v1 (nonland stays singleton, 37 + 23 lands):
| In | Out | Why |
|---|---|---|
| Support Mission | Hoshi Sato | owner's pick; every creature enters with a counter (two with M'Benga), an enchantment that survives creature removal; Hoshi was a 5-drop |
| Sylvia Tilly | Test of Conviction | a counter EVERY combat for {1} (repeatable) over a one-shot |
| Shields Up! | Constable Odo | 2-mana hexproof + indestructible + a counter, protects Sarek / M'Benga; Odo was a 5-drop |
| Captain Pike | The Doctor, EMH | 3-mana body sized by land names (~4-5 mid-game, Q Continuum adds one) that plays lands off the top: card advantage; The Doctor was a 5-drop |
| Amok Time | Saavik | a fight that SCALES with counters, then 3 life, then a creature back; Saavik needed an attacking/blocking target |
| Common Goal | Set Phasers to . . . | 2 mana: one or two of your creatures deal their power to a creature; counters make it a kill spell |
| Q Continuum | 1 Forest | free upgrade: untapped with two lands, a pump or surveil, and another land name |
Curve fix: the four 5-drops cut (Hoshi, Odo, The Doctor, Saavik) leave Liquidators, Sickbay, The Inner Light and
Rok-Tahk as the top end.

Final staged v2 nonland (37, one each): Sarek, Federation Ambassador · Syndicate Liquidators · Holo-Engineer ·
Rok-Tahk, Budding Scientist · Jadzia Dax, Living Legacy · Replicator · Captain Jean-Luc Picard · Picard, Leading
by Example · David and Carol Marcus, Creators · Sickbay · MACO Strike Team · Phlox, Unorthodox Doctor · Scotty,
Miracle Worker · Worf, Honor-Bound Warrior · Neelix, Moral Support · Lt. Cmdr. Geordi La Forge · Seven of Nine,
Unassimilated · The Inner Light · Xindi Surveyors · Dr. Beverly Crusher · Brad Boimler, Eager Ensign · Melkotian
Adjudicator · Dominion Supervisor · Malfunctioning Holodeck · Subcommander T'Pol · Captain Jonathan Archer ·
Deanna Troi, Psychic Counsel · Dr. Joseph M'Benga · Captain Kathryn Janeway · Bristly Bill, Spine Sower ·
Command Decision · Support Mission · Sylvia Tilly, Joy of Discovery · Shields Up! · Captain Pike, Fullness of
Time · Amok Time · Common Goal.
Lands (23): Starfleet Academy · Subspace Anomaly · Q Continuum · 4 Temple Garden · 2 Hallowed Fountain · 2 Breeding
Pool · Risa · Vulcan · Earth, Sector 001 · 4 Forest · 4 Plains · 1 Island.
Interaction (6): Malfunctioning Holodeck, T'Pol, Command Decision, Amok Time, Common Goal, Shields Up! (protection).

Verdicts on the owner's questions (deck C):
| Card | Verdict | Read |
|---|---|---|
| 70,000 Light-Years from Home | ✗ by the owner's rule | exile, but its controller searches a basic land into hand: the Path to Exile pattern the owner ruled out. Owner's call if a land to HAND is acceptable |
| Antagonist Incorporator | ◇ | it is a Borg, so it adds nothing to the Federation count, and only artifact creatures get its token ability (Holo-Engineer's 3/3s, Seven of Nine, Replicator copies) |
| Dr. McCoy, Surly Surgeon | ★ bench | a counter, then countered creatures shrug off destroy (lose the counters instead); 4 mana WW |
| Q Continuum | ★★ in | see above |
| Captain Jonathan Archer | ★★ already in | {G},{T}: +X/+X where X is your creature types — a repeatable pump that grows with the deck |
| Hologram Janeway | ◇ bench | a counter per attack at 8+ total power; an artifact Illusion Officer |
| Amok Time | ★★ in | see above |
| Forever Joined | UNREAD | not in the card database or the saved TRK data, and Scryfall was down (503); grade after the refresh |
| Warp Core | ✗ | its charge counters go on Spacecraft, and the deck has none; otherwise a 2-mana basic-land tutor |
| Captain Kathryn Janeway | ★★ already in | explores on every creature; extra land drop |
| Common Goal | ★★ in | see above |
| Wesley Crusher | ★ bench (maybe) | flash, choose two (counter a noncreature spell, bounce a 2-drop, unblockable, loot); the natural swap is for T'Pol |

Flags carried to the file's notes: Geordi (no charge counters); Scotty ({1}{U}{U} on ~7 blue sources; two
sorceries to beam up: Command Decision, Common Goal); Melkotian (dilemmas: Command Decision, T'Pol, Q Continuum's
untapped entry, Culber-style ETBs — thin); three colourless/utility lands; Holo-Engineer vs David and Carol
Marcus's land token.
Bench to screen after the refresh: Wesley Crusher, Dr. McCoy Surly Surgeon, Hologram Janeway, Emergency Medical
Hologram, Dr. Leonard "Bones" McCoy, Culber and Stamets, Cold-Blooded Crew, Hoshi Sato, Constable Odo, Saavik,
The Doctor EMH, Test of Conviction, Set Phasers to . . ., Antagonist Incorporator, Forever Joined (unread).

## 9. Deck C draft v3 — STAGED, supersedes v2 (2026-11-12)

Owner: The Doctor, EMH back in; Set Phasers and Saavik are maybes; 70,000 Light-Years from Home is OK (a
land to HAND is better for us than Path's land to battlefield — the owner's rule is satisfied). Gray and
Adira, Forever Joined read: {2}{U/R}{U/R} Trill Human Officer 2/3 — at the beginning of combat, if you cast a
noncreature spell this turn, copy a creature you control (not legendary, haste, sacrificed at end step).
◇ here: blue-heavy hybrid on ~7 sources, ~12 noncreature spells, and Holo-Engineer REPLACES the copy with a
plain 3/3 Illusion. Bench.

Modal search (owner: "best modal cards, in or out of the Star Trek set"), Standard, Bant — 115 in the pool,
26 in TRK. A modal PERMANENT is worth more here than a modal spell: every trigger is another dilemma for
Melkotian Adjudicator. Best fits, ranked:
| Card | Cost | Read |
|---|---|---|
| Vigorbloom Charm | {G}{W} instant | protect a permanent / draw + 3 life / a counter then fight — every mode is live |
| Felidar Retreat | {3}{W} | every land: a 2/2 (a 3/3 with Holo-Engineer) or a counter on every creature; Janeway and Pike add lands |
| Federation Outpost | land (W) | untapped with two lands; 2 life or surveil — a modal land, another land name |
| Ni'Var Science Academy | land (U) | the same, flying or surveil |
| Spectacular Tactics | {1}{W} instant (owned) | a counter + hexproof, or destroy a power-4+ creature |
| Pawpatch Formation | {1}{G} instant (owned) | kill a flier / an enchantment / draw + Food (a 3/3 with Holo-Engineer) |
| Sylvan Scavenging | {1}{G}{G} (owned) | every end step a counter or a 3/3 |
| Trash the Town | {G} spree (owned) | two counters, trample, draw two on damage |
| Cosmogrand Zenith | {2}{W} (owned ×2) | second spell each turn: two 1/1s or a counter on every creature |
| Consider the Prime Directive | {2}{U} instant | counter unless they pay 3, or stun + draw |
| Archdruid's Charm | {G}{G}{G} | tutor a creature/land, or a counter + bite; GGG is hard in three colours |

v3 changes from v2:
| In | Out | Why |
|---|---|---|
| 70,000 Light-Years from Home | Command Decision | exiles ANY creature or Spacecraft for 2, against Command Decision's power-4+ limit |
| Vigorbloom Charm | Common Goal | an instant with three live modes (protection, cards, a counter + fight) over a sorcery bite |
| The Doctor, EMH | Subcommander T'Pol | owner's call; T'Pol's stun is the weakest interaction left |
| Federation Outpost | 1 Plains | free: a modal land, another name for Pike and Seven of Nine |
| Ni'Var Science Academy | 1 Island | the same, blue |
OPTIONAL (owner's maybes), each needs a cut: Felidar Retreat (strongest modal fit — for Sylvia Tilly or Bristly
Bill), Spectacular Tactics (better than Set Phasers — for Amok Time), Saavik (for Shields Up! or Amok Time).
Interaction in v3: 70,000 Light-Years, Vigorbloom Charm, Malfunctioning Holodeck, Amok Time, Shields Up!
(protection). Melkotian's dilemmas: Vigorbloom, Q Continuum, Federation Outpost, Ni'Var (untapped entries),
plus Felidar Retreat if taken.
Lands (23): Starfleet Academy · Subspace Anomaly · Q Continuum · Federation Outpost · Ni'Var Science Academy ·
4 Temple Garden · 2 Hallowed Fountain · 2 Breeding Pool · Risa · Vulcan · Earth, Sector 001 · 4 Forest · 3 Plains.
