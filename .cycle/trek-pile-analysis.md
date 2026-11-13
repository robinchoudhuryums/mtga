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

**v3 CONFIRMED by the owner (2026-11-12)** — write v2 + the section-9 changes; the section-9 optionals stay
optional unless confirmed. Owner owns Starfleet Academy (information only).

Star Trek land survey (all 17 TRK lands in Bant identity): v3 already runs every one that improves the deck —
Federation Outpost, Ni'Var Science Academy, Q Continuum (modal untapped lands), Risa, Vulcan, Earth Sector 001
(Planets: each ETB gains 1 life, which grows Neelix and Crusher and feeds Sickbay), the three shocks, Starfleet
Academy and Subspace Anomaly. Left out, on purpose: Gaseous Anomaly and Temporal Anomaly (colourless; a THIRD
colourless land in a three-colour deck costs more than their late sacrifice ability buys — Temporal Anomaly is
the better of the two, the swap if Subspace Anomaly is ever cut) and Unexplored Territory (a colourless basic
fetch, worse than any dual here). Edge of Eternities Planets: Evendo (G; station 12 makes G per creature) is
the only one worth a look and enters tapped — bench. NOTE: every Anomaly's New Planet token becomes a 3/3
Illusion while Holo-Engineer is out (a body instead of the land).

**Arena import block for v3 (2026-11-12, before the deck file exists; set codes only where the owner's own Arena export gave them, the rest name-only):**

```
Deck
1 Sarek, Federation Ambassador (TRK) 251
1 Syndicate Liquidators (TRK) 218
1 Holo-Engineer
1 Rok-Tahk, Budding Scientist (TRK) 211
1 Jadzia Dax, Living Legacy (TRK) 204
1 Replicator
1 Captain Jean-Luc Picard (TRK) 7
1 Picard, Leading by Example (TRK) 29
1 David and Carol Marcus, Creators (TRK) 193
1 Sickbay
1 MACO Strike Team
1 Phlox, Unorthodox Doctor (TRK) 250
1 Scotty, Miracle Worker (TRK) 79
1 Worf, Honor-Bound Warrior (TRK) 256
1 Neelix, Moral Support (TRK) 209
1 Lt. Cmdr. Geordi La Forge (TRK) 70
1 Seven of Nine, Unassimilated (TRK) 80
1 The Inner Light (TRK) 241
1 Xindi Surveyors
1 Dr. Beverly Crusher (TRK) 13
1 Brad Boimler, Eager Ensign (TRK) 5
1 Melkotian Adjudicator
1 Dominion Supervisor
1 Malfunctioning Holodeck (TRK) 22
1 Captain Jonathan Archer
1 Deanna Troi, Psychic Counsel
1 Dr. Joseph M'Benga (TRK) 196
1 Captain Kathryn Janeway (TRK) 187
1 Bristly Bill, Spine Sower
1 Support Mission
1 Sylvia Tilly, Joy of Discovery (TRK) 217
1 Shields Up! (TRK) 35
1 Captain Pike, Fullness of Time
1 Amok Time
1 70,000 Light-Years from Home
1 Vigorbloom Charm
1 The Doctor, EMH (TRK) 234
1 Starfleet Academy
1 Subspace Anomaly (TRK) 300
1 Q Continuum (TRK) 290
1 Federation Outpost
1 Ni'Var Science Academy
4 Temple Garden (TRK) 301
2 Hallowed Fountain (TRK) 286
2 Breeding Pool (TRK) 279
1 Risa
1 Vulcan
1 Earth, Sector 001 (TRK) 281
4 Forest
3 Plains
```

## 10. Deck C v4 — STAGED, supersedes v3 (2026-11-12, owner-confirmed)

Owner's screenshot batch graded (Kellan Joins Up, Enterprise-A, Helga, Stable Wormhole, Mr. Spock, Make It
So, Urban Retreat, Aang at the Crossroads, Warp Speed, Final Frontier, Saurian Explorer, Temporal Anomaly,
Jean-Luc Picard Luminary — the last NOT Standard-legal and needs {R}: it belongs to the Sisko Brawl deck).
Applied: +Kellan Joins Up −Bristly Bill (≈22 legendary creatures: nearly every creature spell puts a counter
on the whole team, doubled by M'Benga); +U.S.S. Enterprise-A −Amok Time (three Officers = three 3/3s with
Holo-Engineer; Geordi now doubles its station counters); +Helga, Skittish Seer −Melkotian Adjudicator (owner
agreed; Helga draws off ~8 four-plus creature spells); +Urban Retreat −Risa (all three colours; G/W are the
plentiful colours, so the G/W dual goes).
Owner's MUST-ADD: Stable Wormhole; also wants Warp Speed and Mr. Spock — cut candidates offered in chat
(pending): see the reply of 2026-11-12. Interaction is now thin: 70,000 Light-Years, Vigorbloom Charm,
Malfunctioning Holodeck (+ Shields Up! protection) — do not cut those for the three adds.
The import block lives in this file's section 9 history; the current one is regenerated in chat.

**v4 + owner's swaps (2026-11-12):** +Stable Wormhole −Replicator, +Warp Speed −Neelix, +Mr. Spock −Scotty.
Current staged import block: regenerated in chat (and in the scratch file deck99-import.txt).

### Blink / beam me up survey (owner asked: the deck has many ETBs)
What a re-entry re-triggers here: Kellan Joins Up (legendary enters → a counter on every creature), Support
Mission and Deanna Troi (enters with a counter), Janeway (explores), M'Benga doubles all of it — plus the
card's own ETB (The Doctor, Holo-Engineer, Rok-Tahk/Murf, Archer/Porthos, Tilly, David and Carol Marcus,
Enterprise-A's three Officers, Malfunctioning Holodeck re-targets). Beam me up (return your creature to hand
as a cost) ALSO re-triggers the CAST payoffs: Captain Picard (an Officer per creature spell) and Helga (a card
per 4+ creature). CAUTION (G-42): a blink resets the blinked creature's +1/+1 counters — blink a fresh ETB
creature, not the grown threat; Deanna/Support Mission/Kellan give some back on re-entry.
| Card | Cost | Read |
|---|---|---|
| Abuelo, Ancestral Echo | {1}{W}{U} | ★★★ repeatable blink of a creature OR ARTIFACT (Enterprise-A = three more Officers); flying, ward 2 |
| Ghost of Illyria (TRK) | {3}{W} | ★★ flier; ETB blinks any nonland permanent (Enterprise-A, Holodeck, even Kellan Joins Up) |
| Test of Priorities (TRK) | {1}{U} instant | ★★ modal: surveil 2 + draw, or blink your creature — also dodges removal |
| Don & Leo, Problem Solvers | {3}{W/U}{W/U} (owned) | ★★ free blink of an artifact AND a creature every end step |
| Miles O'Brien (TRK) | {2}{W} | ★★ returns your creature/artifact to hand, then draws at end step whenever a permanent came back to hand that turn — the beam-me-up engine |
| Energize (TRK) | {1}{U} | ★ bounces THEIR creature (interaction), beam me up {3}{U} |
| Pure Energy / Open Communications / There's Coffee in that Nebula / Final Frontier / Adversary by Algorithm (TRK) | 1-3 | ◇ beam me up spells; each recast returns your creature for a re-cast |
| Ennis, Debate Moderator | {1}{W} (owned) | ★ 2-drop blink on ETB |
| Charming Prince | {1}{W} | ★ modal ETB: blink / scry 2 / 3 life |
| Salvation Swan | {3}{W} (owned) | ◇ flash blink (+ flying counter), Birds only repeat it |
| Kykar, Elrond | — | ◇ |
Note: Scotty (cut today) gives EVERY instant/sorcery in the graveyard beam me up — only worth bringing back
if the beam-me-up route is taken.

### Owner's next batch (2026-11-12) — graded against the current staged list
| Card | Verdict | Read |
|---|---|---|
| Jett Reno, Problem Solver {1}{U} | ★★ | with Deanna + Support Mission + M'Benga she enters a 5/6, so every tap draws a card — and taps come from attacking, stationing Enterprise-A, Worf's tap-two, D'Vana's untap |
| Test of Conviction {1}{W} | ★★ | a counter on every creature (doubled) or draw two (four with Mr. Spock); modal |
| D'Vana Tendi {1}{G/U}{G/U} | ★★ | {T}: untap another permanent — Helga taps for X mana twice, Rok-Tahk's creatures, Starfleet Academy, or Jett Reno for another card; a 2/4 for 3 |
| Dominion Saboteur {4}{U} | ★★ | clones a creature OR artifact and copies its COUNTERS: your biggest creature, or Enterprise-A (three more Officers, charge counters kept); not legendary, so no Kellan trigger |
| Jake Sisko {1}{G} | ★ | landfall life (Crusher, Sickbay) and a Clue on the second land a turn — Janeway, Pike and Stable Wormhole make that reachable |
| The Traveler {G}{U} | ★ | a 2-mana Captain Pike without the land-from-top; reach, vigilance |
| Gaseous Anomaly | ◇ | a THIRD colourless land; only as a swap for Subspace Anomaly (draw two vs two Officers) |

### Swap package proposed 2026-11-12 (owner offered cuts: Captain Pike, Sylvia Tilly, Geordi, MACO, Archer)
Core (5 for 5): +Jett Reno −MACO Strike Team · +D'Vana Tendi −Sylvia Tilly · +Abuelo, Ancestral Echo −Captain
Jonathan Archer · +Dominion Saboteur −Lt. Cmdr. Geordi La Forge · +Test of Conviction −Captain Pike.
Maybes (each needs a cut beyond the offered five): +Test of Priorities −Seven of Nine, Unassimilated ·
+Don & Leo, Problem Solvers −Sickbay · +Jake Sisko −David and Carol Marcus.
Watch: removal stays at three (70,000 Light-Years, Vigorbloom, Holodeck); blue demand rises (Jett, Abuelo,
Saboteur, Spock UU, Test of Priorities) — check blue sources in consistency, a Forest→Island may be needed.

## 11. Deck 99 WRITTEN 2026-11-12 (owner's override) — Builder board live

Owner authorised a one-day override of the release-date bound: `build_pool.py --query "game:arena (date<=now or
set:trk or set:trc or set:sds)"`, then build_mana.py --pool and tag_synergies.py --merge. The 2026-11-13
`make refresh REFETCH=1` restores the standard query. Deck 99 = the staged list + the five swaps (+Jett Reno
−MACO, +D'Vana −Tilly, +Abuelo −Archer, +Dominion Saboteur −Geordi, +Test of Conviction −Pike). Preflight READY,
legal, every printing known. Measured: interaction 3, card advantage 8, protection 7, board power 52, avg MV
3.27, keepable 82.5% (low for 23 lands), W 14 / U 10 / G 15 sources; tier floor C (interaction 3; one more
removal → B). similar: 0 shared cards with any deck (overlap is the generic counters theme; Federation has no tag).
Builder project builds/trek-bant, board https://claude.ai/artifact/1eekQNYt2Jxtb3fh4wRSVu (pile F = 32 bench
cards with reasons/verdicts). Owner keeps Seven of Nine and Sickbay, maybe David and Carol Marcus; the three
maybes are on the board as suggestions: Test of Priorities −Brad Boimler, Don & Leo −The Inner Light, Jake Sisko
−Xindi Surveyors.
2026-11-12: +Don & Leo −Xindi Surveyors applied. A-floor package proposed (on the board as suggestions), measured:
+Spectacular Tactics −Brad Boimler, +Common Goal −Worf, +Coordinated Maneuver −David and Carol Marcus, +Saavik
−The Inner Light → interaction 3→7, card advantage 8→7, floor C→A, legal. The first two alone reach B (int 5).
Test of Priorities and Jake Sisko set aside: their slots are better spent on interaction.

### Spacecraft batch (owner's screenshot + three asks, 2026-11-12), graded for deck 99
Station taps another creature for counters equal to its power: this deck's countered creatures fill a station in one
or two taps, Jett Reno draws whenever she is tapped at 4+ power (station taps her), Brad Boimler adds one to the
charge counters, D'Vana untaps a creature to station again, Holo-Engineer's 3/3s station too. Cost: a station tap
is a creature not attacking. Spacecraft carry no creature types (nothing for Sarek).
| Card | Verdict | Read |
|---|---|---|
| Dawnsire, Sunstar Dreadnought {5} | ★★★ | counts as REMOVAL: at 10+ counters every attack deals 100 to a creature or planeswalker; colourless |
| The Seriema {1}{W}{W} | ★★ | tutors a legendary creature (M'Benga, Sarek, Helga, Jett...); tapped legends are indestructible; 5/5 flier at 7 |
| U.S.S. Enterprise-D {3} | ★★ | counts as CARD ADVANTAGE: a card to play every turn you charge it; 4/5 flier at 7 |
| Class-F Shuttlecraft {3} | ★ | any-colour rock (helps Spock's UU) and a 2/4 flier at 6 |
| Sledge-Class Seedship {2}{G} | ◇ | puts a creature from hand onto the battlefield on attack, once it flies at 7 |
| U.S.S. Cerritos {5} | ◇ | two Officers; Enterprise-A does it better |
| The Eternity Elevator {5} | ◇ | three colourless mana; 20 counters is a lot even here |
| Wurmwall Sweeper {2} | ◇ | surveil 2, a 2/2 flier at 4 |
| Deep Space 9 {9} | ◇ spice | free permanents every upkeep and +3/+3 at 9 counters, at 9 mana |
A-floor package v2 measured: +Spectacular Tactics −Worf, +Saavik −The Inner Light, +Dawnsire −David and Carol Marcus,
+Coordinated Maneuver −Brad Boimler → interaction 7, card advantage 7, floor A, avg MV 3.38, legal.
Deep Space 9 in place of Coordinated Maneuver (measured): interaction 6, floor B (one short of A), avg MV 3.57.
To keep A AND take Deep Space 9: keep Coordinated Maneuver and give DS9 its own slot (−Dominion Saboteur, the
weakest-ranked card in `cuts`, measured separately). Alternate cuts offered: Spectacular Tactics → Picard Leading by
Example / Shields Up! / Jadzia Dax; Saavik → Syndicate Liquidators / Dr. Beverly Crusher; Dawnsire → Dominion
Saboteur / Dominion Supervisor.
2026-11-12: +Spectacular Tactics −Shields Up! applied (owner).
Board marks 2026-11-12 (owner): +Dawnsire, +Saavik, +Deep Space 9; −David and Carol Marcus, −The Inner Light, −Helga;
bench Felidar Retreat, Replicator, Test of Priorities, Enterprise-D. Measured: floor B, interaction 6, card adv 6,
avg MV 3.54. Adding Coordinated Maneuver −Brad Boimler → A (int 7, card adv 6). Alternative keeping Helga: DS9 −Brad,
Coordinated Maneuver −Picard LbE → A (int 7, card adv 7, avg MV 3.57). Replies posted on the board (Saboteur copies
Spacecraft with counters; Replicator copies New Planets, but Holo-Engineer turns copies into 3/3s).
Interaction search 2026-11-12 (better than Coordinated Maneuver, all OWNED): Bite Down ({1}{G} instant bite, creature
or planeswalker), Stasis Snare ({1}{W}{W} flash exile), Sheltered by Ghosts ({1}{W} Aura: exile ANY nonland
permanent + lifelink/ward on yours), Felling Blow ({2}{G} counter + bite). Excluded by the owner's rule: Prophesied End
(they draw unless it was attacking), Stroke of Midnight / Crib Swap (they get a 1/1). Owner's marks now cut D'Vana and
Picard LbE too. Measured: +Dawnsire −D&C Marcus, +Saavik −Inner Light, +Bite Down −D'Vana, +DS9 −Picard LbE → A
(int 7, card adv 7, Helga kept); with Helga ALSO cut for Stasis Snare → see chat.
2026-11-12: applied +Dawnsire −D&C Marcus, +Saavik −Inner Light, +Sheltered by Ghosts −D'Vana, +DS9 −Picard LbE (Helga kept); lands −2 Forest −1 Plains +2 Breeding Pool +1 Hallowed Fountain (U 10→13). Floor A.
2026-11-12: +Overgrown Farmland −1 Temple Garden (owner owns one Farmland, was a Temple Garden short).
2026-11-12: +Replicator −Worf (owner). David and Carol Marcus re-add measured: for Brad / Syndicate Liquidators / Dominion Supervisor all keep A.
2026-11-12: Kwia Vigorbloom graded ★★ (owned). Owner keeps Liquidators/Brad/Dominion Supervisor; D&C alternates offered: Jadzia Dax, Dr. Beverly Crusher, Dominion Saboteur. Measured +D&C −Jadzia, +Kwia −Crusher: A, int 7, card adv 7, avg MV 3.65.
2026-11-12: Crusher payoffs graded (Exemplar of Light, Bloombrute, Heroic Feast, Aerith, Drogskol Reaver). Test of Conviction for Kwia or D&C: A holds, card adv 7→6.

### Full re-read of deck 99 + candidates (2026-11-12) — what changed
1. Sickbay gains 1 life for EVERY creature entering (tokens too): it is the lifegain engine, so Crusher's payoffs
   (Heroic Feast, Bloombrute, Aerith, Kwia) trigger far more often than "11 lifegain sources" implied.
2. Holo-Engineer replaces EVERY token: Replicator's Food, Heroic Feast's Food and Kwia's Lotus become 3/3 Illusions
   while it is out (each then enters → Sickbay life, Support Mission/Deanna counters, Janeway explore).
3. Test of Conviction's draw mode gives the OPPONENT a card (target opponent draws one, you draw two) — earlier
   described as just "draw two".
4. Seven of Nine is better than flagged: 14 differently named lands in the deck (plus New Planet), so her discard
   stops applying by mid-game.
5. Dawnsire's 100-damage trigger needs 10 counters; it only becomes a creature at 20. Saavik hits only an attacking
   or blocking creature. Abuelo / Don & Leo blinking a legendary creature re-triggers Kellan.
Proposed: +Kwia −Rok-Tahk, +Bloombrute −Helga, +Heroic Feast −Jadzia Dax, +Aerith −Test of Conviction, +D&C −Dominion
Saboteur → A, interaction 7, card advantage 6, avg MV 3.57, early drops 9, legal.
2026-11-12: owner wants ONE swap for Test of Conviction. Ranked: 1 Bloombrute (keeps card adv 7, avg MV 3.59), 2 Aerith (card adv 6, 3.57), 3 Heroic Feast (6, 3.57), 4 Kwia (6, 3.65, WW 6-drop, Lotus blank while Holo-Engineer is out). All keep A.
2026-11-12: Tribbles vs Aerith for Test of Conviction — Aerith alone; both: Aerith −Test, Tribbles −Dominion Saboteur (A, card adv 6, avg MV 3.51) / −Jadzia (early drops 9) / −Helga (card adv 5).
2026-11-12: +Aerith −Test of Conviction applied (A, card adv 6). Tribbles for Jett Reno advised against (Jett is an uncounted draw engine; early drops 10→9).
2026-11-12: +Troubling Tribbles −Abuelo applied. Lands unchanged (W14/U13/G15; Spock 70%). Interaction 7: 3 instant-speed, 2 answer noncreature permanents; fliers answered by removal only — no flying/reach blockers. Proposed: +Pawpatch Formation −Dominion Saboteur, +The Traveler −Jadzia (interaction 8, early drops 11, avg MV 3.49).
2026-11-12: bench re-graded against the current list — up: Bloombrute, Exemplar of Light, Pawpatch Formation, Coordinated Maneuver (★★★); Heroic Feast, The Traveler, David and Carol Marcus, Make It So (★★); Neelix (★). Drivers: Sickbay lifegain per creature, Tribbles, card advantage at 6, the flier gap, two noncreature answers.
2026-11-12: all-three packages measured (Bloombrute, Heroic Feast, D&C): C = +Bloombrute −Saboteur, +Feast −Jadzia, +D&C −Rok-Tahk → card adv 7, early 9, avg MV 3.49; A = +Bloombrute −Helga, +Feast −Jadzia, +D&C −Saboteur → 6 / 9 / 3.57; D = +Bloombrute −Saboteur, +Feast −Warp Speed, +D&C −Rok-Tahk → 6 / 10 / 3.46. All A, legal.

- 2026-11-12: **Deck 100 drafted** — `decks/100-resistance-is-futile/deck.txt`, "Resistance Is Futile — Borg",
  Historic Brawl, commander Locutus of Borg (WUB), 100 cards (34 creatures, 8 Spacecraft, 19 spells and
  artifacts, 38 lands). Checks: resolve --check OK, legal OK, preflight READY, metrics floor A (interaction 15,
  card advantage 6, board power 86, average MV 3.52), keepable 81.2% (96.5% counting the free mulligan),
  sources W 21 / U 21 / B 22, shares at most 1 card with any other deck. Weak spot: the WW cards (Tempered
  Steel, The Seriema) cast on turn 3 only 60% of the time. Tier letter left for the owner. Bench of 26 graded cards in
  Builder `builds/trek-borg`, board https://claude.ai/artifact/SEWP7enbuaTvr3nBk4mDDy. Empress Galina is
  not on Arena (not in the pool), so it was skipped. Arcane Sanctum is not on Arena either; Obscura Storefront
  replaces it. The Sisko Brawl deck is still to do (after the 11-13 refresh).
- 2026-11-12 classifier gaps (G-67, recorded only): Battle of Wolf 359 ("All nonartifact creatures get -X/-X
  … X is the number of artifact creatures you control") scores no Sweeper role, and Collation Trimatrix ("Tap
  three untapped artifact creatures you control: You draw a card") scores no card advantage, because the cost is a tap of
  other creatures, not {T}. Both would raise deck 100's figures, which already clear A. Also: the pool override
  added a card named "Seven of Nine", so decks 45a / 48 / 54b now flag their prose "Seven of Nine" as a
  stale card citation. That is noise, and it should clear when the 11-13 refresh restores the standard pool (re-check then).
- 2026-11-12: **Deck 101 drafted** — `decks/101-the-emissary/deck.txt`, "The Emissary — Sisko", Historic Brawl, commander
  Captain Benjamin Sisko (WUBRG): dilemmas and Officers. Repeating mode engines (Felidar Retreat, Glorious Sunrise, Black Market
  Connections, Dreamshackle Geist, Kirk, Tal Shiar Operative, Elder Gargaroth, Hullbreaker Horror, Galadriel, Fantastic Four,
  Gala Greeters, Territorial Kavu, Warren Warleader, Cosmogrand Zenith) plus modal interaction (charms, commands, Spree,
  Sublime Epiphany, Casualties of War). preflight READY, floor A (interaction 24, card advantage 17, per 60: 14.4 / 10.2),
  keepable 79.9% (95.9% with the free mulligan), sources W 18 / U 19 / B 18 / R 19 / G 21. Draft swaps for five-colour
  castability: Gala Greeters for Silverback Elder (GGG 42% T5), Deadly Plot for Vraska's Final Mercy (BB 47% T2), Territorial
  Kavu for Tectonic Giant (RR); four pathways replaced three KTK tri-lands + The World Tree (tempo sim: 42.4% vs 41.2% average
  on-curve, tapland cost 6.0 → 4.1 points a card). Spells shared with deck 100: only Seven of Nine and Enterprise-A. The
  trek-borg Builder now holds BOTH decks (L = 100, S = 101) with piles L / S / Either / Neither so the owner can split cards for
  variety; board https://claude.ai/artifact/SEWP7enbuaTvr3nBk4mDDy (v2). Tier letter left for the owner.
- 2026-11-12 full re-read of the 132 cards left out of decks 100/101 (whole pile + board bench). Changed grades:
  Sisko UP — Scotty (◇→★★: recast a graveyard charm by bouncing an Officer token, a fresh dilemma each time), Isshin (◇→★★:
  doubles five modal attack triggers), Rimefire Torque naming Officer (◇→★), Anthropological Mission (◇→★), Sarek (△→★: the
  earlier "Officers are one type" read was WRONG, it counts types across all non-Borg creatures), Suus Mahna (★, a {U} tapper
  with 30+ land names), Sarcophagus (◇→★, +1/+0 to Officers), Mikaeus (◇→★), Voyager / David and Carol (★, Felidar triggers),
  Jhoira (★). Borg UP — Rimefire Torque naming Borg (◇→★), Scotty (★), Romulan Bird-of-Prey (◇→★), Brad Boimler (◇→★: +1
  charge counter when tapped to station), Suus Mahna (★). Unchanged: Kobayashi Maru / Demonic Pact (lose-the-game mode),
  Impossible Choice (removal rule), Expropriate (a vote is not a mode). Hull Breach and All Good Things . . . are not in the
  Arena pool. Board v3 carries the new reasons.
- 2026-11-13 deck 100 fits/upgrades pass (proposed, NOT applied): owned Iron Man −Free Borg Revolutionaries, Doctor Doom
  −Badgey, Chrome Dome −Data New Life; crafts Arcbound Condor −Make Disappear, Kappa Cannoneer −Lita, Thought Monitor −Mind
  Stone. Package preview: floor A, interaction 15 (held), card advantage 6→9, protection 6→8, avg MV 3.52→3.69. Spice:
  Krang Utrom Warlord (owned), Virulent Silencer (owned), Karn's Bastion (costs ~1.4 on-curve points as a land), Alela,
  Monoist Circuit-Feeder. All on the trek-borg board (v4).
