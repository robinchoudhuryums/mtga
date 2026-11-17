# Pack ingest 2026-11-17 — where the new cards fit (TEMPORARY working doc)

**Status: ALL BATCHES DONE (2026-11-17) — awaiting the owner's picks.** Batch 5 checked the weaker matches into the decks that still have unowned cards, keeping only removal-for-removal and ramp-for-ramp stand-ins. A running record of the swap suggestions that
surface while the 582 cards from the 2026-11-17 pack ingest are checked against the decks.
Nothing here is applied; the owner picks, then `/apply-changes` writes. **Swap page:** `builds/packs/swaps.json`
(claude.ai: https://claude.ai/artifact/MMRD297vEaQmD8FyX3Miyk) — the 29 upgrade / sidegrade / spice pairs only,
each candidate beside the card it would replace (click a card for full size); mark Swap / Maybe / Keep there.
The 18-deck Builder board for `builds/packs` was deleted 2026-11-17 at the owner's request; the swap page
replaces it, and `builds/packs/build.json` stays as its data. Delete this doc once
the picks are applied or dropped. Decks are the source of truth, not this file.

**Source:** the pack-opening CSV (637 lines, 721 cards), ingested in commit 4941a2c
(582 new cards, 8 counts raised, 20 wishlist rows owned; four unmatched names skipped:
"... and Dissident", "Academy on the Bay", "Rampaging Cosmozoan", "Spock, Cross-Time Captain").

## 1. How the shortlist was built

- `deck.py suggest-homes` was run for all 582 new cards (saved in the session scratchpad).
- 240 match no deck. 77 match 6+ decks as KEY, which is a fact about broad tags, not a fit,
  so they are not graded here.
- The rest are ranked by fit score, keeping only KEY matches that share a SPECIFIC theme
  (not Human, card draw, tokens, removal, counters, mana, combat …). That leaves 134 rows over
  109 cards, about five batches.
- Each card is graded from its full text against the deck's own plan, not from the tag.
- Verdicts: **upgrade** (beats a current card), **role-player** (fits, lateral),
  **flavour** (changes how the deck plays), **skip**.
- The suggested cut is `suggest-homes`' weakest-fit guess, never confirmed. Confirm any cut
  with `deck.py cuts <id>` and the full text before swapping, and keep each deck's
  `#: protect:` list and the owner's keeps in its notes.

## 2. Standing notes

- Deck 101 matches many cards on "cycling" alone. Sisko's plan is dilemmas and Officers, not
  cycling, so those rows are skips.
- Owner's removal rule: no removal that benefits the opponent.
- **Unfinished decks (owner's rule, 2026-11-17):** in a deck that still has unowned cards, a newly owned
  card that can stand in for an UNOWNED card is worth logging even as a sidegrade or spice pick: it
  takes the deck one craft closer to buildable. So the cut column prefers an unowned card there, marked
  `UNOWNED:`. Decks affected so far: 48 (5 unowned), 56 Historic Brawl (35), 88 (27), 91 (44), 92 (40),
  93 (24), 94 (30), 96 (39), 100 (38).
- **Deck 96 mills the OPPONENT** (Tutelages, Bruvac, The Water Crystal). Cards that mill YOU work
  against it in a long game, so batch 2-3's self-mill picks for 96 were downgraded to skips.

## 3. Suggestions by deck (live — re-sorted each batch)

| Deck | Card | Verdict | Why (from the text) | Suggested cut (unconfirmed) | Batch |
|---|---|---|---|---|---|
| 26 Iron Colossi | Pinnacle Emissary | role-player | A Robot artifact creature that makes a 1/1 flying Drone for every artifact spell you cast; warp {U/R} for an early trigger. | Cosmic Cube | 3 |
| 38 Armory | **Bat'leth** | upgrade | Equipment with removal: on entering, an opponent's creature gets -2/-2; then +2/+0. Orzhov Equipment, Standard-legal. | Shrike Force | 1 |
| 38 Armory | Combadge | role-player | Equipment that copies itself when cast (two for 3); a creature wearing one can't be blocked while another wears the other. Equip {2}. | Shrike Force | 3 |
| 48 Doombots | Pinnacle Emissary | sidegrade | As in 26: a Robot that turns artifact spells into flying Drones. | UNOWNED: Mm'menon, Uthros Exile (an artifact-enters payoff; Leyline makes either a Robot) | 3 |
| 55 Mardu Waves | L'Rell, Fierce Visionary | role-player | A hasty 2/1 Klingon token at every combat (sacrificed at end step), plus a sacrifice outlet that surveils. | owned deck: confirm with `cuts 55` | 4 |
| 56 Historic Brawl | Craterous Stomp | sidegrade | Instant: 3 damage to an opponent's creature; their other creatures can't block Giants or Warriors that turn. | UNOWNED: Mishra's Command (X-cost modal sorcery) | 5 |
| 56 Historic Brawl | Forging the Tyrite Sword | sidegrade | Two Treasures, then chapter III tutors any Equipment (Embercleave, Kaldra) to hand. | UNOWNED: Stoneforge Mystic (also an Equipment tutor; it also cheats one in) | 4 |
| 56 Historic Brawl | Meteoric Mace | spice | Cascade on cast plus +4/+0 and trample; much weaker than Embercleave, but owned. | UNOWNED: Embercleave (a stand-in until it is crafted) | 3 |
| 56 Historic Brawl | Spectral Steel | role-player | +2/+2 Aura that later returns an Aura or Equipment from the graveyard to hand. | UNOWNED: Shadowspear (a stand-in; much weaker) | 4 |
| 56 Historic Brawl | Storm-Kiln Artist | sidegrade | A Treasure for every instant you cast on your own creature; +1/+0 per artifact. | UNOWNED: Erratic Cyclops (also rewards casting instants) | 4 |
| 56 Historic Brawl | Stormforged Armor | spice | Equip by paying 3 life; the creature conjures an attacking Ball Lightning on every attack. | UNOWNED: Kaldra Compleat (a stand-in until it is crafted) | 4 |
| 74 Iron Hills Forge | Combadge | role-player | Two Equipment for 3 (it copies itself), so two bodies of equip-trigger fodder; equip {2}. | owned deck: confirm with `cuts 74` | 4 |
| 75 Historic Brawl | Elvish Elegy | role-player | {B/G}: mill three, permanent +1/+1 to graveyard creatures, an Elf or land to hand. | Leyline of Transformation | 1 |
| 75 Historic Brawl | Perennial Gravewarden | role-player | 2-mana Elf that returns from the graveyard on a turn a creature entered and one died. | Leyline of Transformation | 1 |
| 85 Ghost-Spider | Concert Kaboomist | flavour | Damage to an opponent equal to noncreature spells cast since your last turn. | Torbran | 2 |
| 85 Ghost-Spider | Fiery Inscription | flavour | 2 damage to each opponent per instant or sorcery you cast; worth it only with a high spell count. | Torbran | 3 |
| 85 Ghost-Spider | Ghitu Journeymage | role-player | 2 damage to each opponent on entering if you control another Wizard; deck runs 7 Wizards. | Torbran | 1 |
| 85 Ghost-Spider | Soul-Scar Mage | role-player | Prowess; your noncombat damage to their creatures becomes -1/-1 counters. | Torbran | 1 |
| 85 Ghost-Spider | Unstable Amulet | role-player | 1 damage to each opponent whenever you cast a spell from outside your hand, plus energy-fuelled impulse draw; Gwen's exile plays trigger it. | Torbran | 2 |
| 88 Full Throttle | **Bouncer's Beatdown** | upgrade | Instant: damage equal to your greatest power (Samut makes that huge) to a creature or planeswalker, exiling it if it would die. | UNOWNED: Hulk's Thunderclap (a sorcery bite) | 5 |
| 88 Full Throttle | Hydra's Growth | flavour | An Aura that doubles the creature's +1/+1 counters every upkeep; a fast-growing threat for Samut. | UNOWNED: Gamma Grotesque (a counters card in a power deck) | 3 |
| 88 Full Throttle | Kami of Whispered Hopes | sidegrade | Taps for mana equal to its power (Samut's +X/+0 counts) and adds an extra counter whenever counters go on. | UNOWNED: Back-Alley Gardener (land ramp off creatures entering) | 5 |
| 91 Scarab's Fist | **Narfi, Betrayer King** | sidegrade | Other Zombies get +1/+1, and the deck runs 22 Zombies. (Its snow recursion is dead here.) | UNOWNED: Eternal Skylord (also a 5-drop; flying for Zombie tokens instead of +1/+1 for all Zombies) | 2 |
| 91 Scarab's Fist | **Sidisi, Undead Vizier** | upgrade | A Zombie with deathtouch; exploit (sacrifice a creature, e.g. a token) to tutor any card. | UNOWNED: Fallen Shinobi (5-drop needing an unblocked attacker) | 2 |
| 91 Scarab's Fist | Master of Waves | skip | Its devotion-to-blue tokens are thin in Esper; it is a Merfolk, so deck 94 may want it instead (not matched there). | — | 2 |
| 91 Scarab's Fist | Patchwork Crawler | skip | Exiles creature cards from your graveyard, which fights recursion. | — | 2 |
| 91 Scarab's Fist | Umbral Juke | sidegrade | Instant: target player sacrifices a creature or planeswalker, or make a 2/1 flier. | UNOWNED: Never // Return (sorcery destroy, Zombie later) | 5 |
| 91 Scarab's Fist | Warren Soultrader | flavour | Pay 1 life, sacrifice another creature: a Treasure. A Zombie Wizard sacrifice outlet. | as above | 1 |
| 92 Phoenix King | **The Wrath of Khan** | upgrade | 3-mana Saga: 4 damage to a creature, then you take control of it for combat; later chapters add value. | UNOWNED: Overwhelming Victory (5-mana instant, 5 damage) | 5 |
| 92 Phoenix King | Emperor of Bones | upgrade | Exiles a card from a graveyard each combat; adapt {1}{B} brings an exiled creature back hasty for the turn, and every extra combat is another exile. | UNOWNED: Archpriest of Shadows (5-mana reanimation that needs combat damage first) | 3 |
| 92 Phoenix King | Witch-king of Angmar | role-player | 5-mana flier; when creatures hit you, the opponent sacrifices one of them; discard a card for indestructible. | UNOWNED: Yathan Tombguard (draws only off creatures with counters, which the deck rarely makes) | 3 |
| 93 Two Heavens | Switchgrass Grazer | role-player | Haste; 1 damage to any target whenever it attacks, which Isshin doubles. | no unowned card it clearly beats (Nadier's Nightblade and Professional Face-Breaker both fit better) | 2 |
| 94 Paradox Sculptor | **Shapers of Nature** | upgrade | A Merfolk that puts +1/+1 counters ({3}{G}) and turns a counter into a card ({2}{U}); Zimone doubles counters. | UNOWNED: Nadir Kraken (not a Merfolk; also its stored printing is flagged unverified) | 2 |
| 94 Paradox Sculptor | Emergent Sequence | sidegrade | Fetch a basic; it becomes a land creature with +1/+1 counters, which Zimone then doubles. | UNOWNED: Song of Freyalise (two turns of creature mana, then a counter each) | 5 |
| 95 Light of Valinor | Ghost of Illyria | role-player | Flier that blinks your own nonland permanent until end step; a second Galadriel entry. | Panharmonicon | 2 |
| 96 Drowned Library | **Tamiyo, Compleated Sage** | sidegrade | +1 locks down a creature; −X copies a permanent card from your graveyard (thin in an opponent-mill deck). A walker to hold the board. | UNOWNED: Nissa, Voice of Zendikar (also a non-mill walker) | 1 |
| 96 Drowned Library | Cauldron's Gift | skip | Mills you four; deck 96 must not deck itself. | — | 2 |
| 96 Drowned Library | Cemetery Tampering | skip | Mills you three every upkeep; the wrong library for this deck. | — | 2 |
| 96 Drowned Library | Garruk, Cursed Huntsman | spice | 6-mana walker: two 2/2 Wolves each turn, or −3 destroy a creature and draw. | UNOWNED: Ob Nixilis Reignited (a stand-in; Ob's +1 draw is a mill under the Tutelages, so Ob stays the better card) | 5 |
| 96 Drowned Library | Mesmeric Orb | flavour | Every untap mills that permanent's controller: the opponent untaps more, but it is symmetric. | Lithoform Engine | 3 |
| 96 Drowned Library | Sweet Oblivion | role-player | {1}{U}: target player (the opponent) mills four; escape recasts it. On plan. | no unowned card it clearly beats (Master's Councillors and Cut Your Losses both mill harder) | 3 |
| 96 Drowned Library | Vivien, Monsters' Advocate | skip | Casting creatures off the top duplicates Glarb, and the deck plays few creatures. | — | 3 |
| 96 Drowned Library | World Shaper | skip | Mills you on each attack. | — | 3 |
| 97 Street Feast | **Feasting Troll King** | upgrade | Three Foods when cast from hand; returns from the graveyard by sacrificing three Foods. {G}{G}{G}{G}. | Mythweaver Poq | 1 |
| 97 Street Feast | Meriadoc Brandybuck | role-player | A Food whenever your Halflings attack; the deck runs 6 Halflings. | Mythweaver Poq | 1 |
| 97 Street Feast | Siege-Gang Commander | role-player | Three Goblin tokens (Peregrin Took adds a Food to each); sacrifice a Goblin for 2 damage. | Mythweaver Poq | 1 |
| 98 Throw Wide the Gates | Dramatic Accusation | sidegrade | 3-mana Aura: tap the creature and keep it tapped; {U}{U} shuffles it away. A noncreature spell for G'raha. | UNOWNED: Lawmage's Binding (flash, also stops activated abilities) | 5 |
| 98 Throw Wide the Gates | Unable to Scream | sidegrade | 1-mana Aura: the creature loses all abilities and becomes a 0/2. A cheap noncreature spell for G'raha. | UNOWNED: Mesmerizing Dose (3 mana; its proliferate also grows Hero tokens) | 5 |
| 100 Resistance Is Futile | **Assembly Specialist** | upgrade | 2 mana for two Borg artifact creatures, feeding Collation Trimatrix's tap-three draw and Borg Cube's affinity. | UNOWNED: Tidus, Blitzball Star (not an artifact creature, so it feeds none of the deck's counts) | 3 |
| 100 Resistance Is Futile | **Bronze Walrus** | upgrade | A 3-mana artifact CREATURE that taps for any colour and scries 2; it counts for Borg Cube and Collation Trimatrix. | UNOWNED: Arcane Signet (a rock that counts for neither) | 5 |
| 100 Resistance Is Futile | Class-F Shuttlecraft | role-player | A 3-mana Spacecraft that taps for any colour; stationed to 6 it is a flying artifact creature. | UNOWNED: Arcane Signet, if Bronze Walrus is not taken | 5 |
| 100 Resistance Is Futile | Free Borg Revolutionaries | role-player | A Borg artifact creature that pumps the team on entering; basic landcycling {2} early. | no unowned card it clearly beats; Winter at most | 3 |
| 100 Resistance Is Futile | Jin-Gitaxias, Progress Tyrant | role-player | 7 mana: copies your first artifact, instant or sorcery each turn, and counters the opponent's first. Top-heavy. | UNOWNED: Kappa Cannoneer (another 6-mana blue artifact payoff) | 4 |
| 100 Resistance Is Futile | Machinist's Dismissal | sidegrade | Counter a noncreature spell, {1} cheaper per artifact you control or hold; instant-speed interaction the deck lacks. | UNOWNED: Haunt the Network (same 5 mana; a sorcery drain where this is instant interaction) | 3 |
| 100 Resistance Is Futile | Squadron Carrier | role-player | Spacecraft gain "exhaust {W}: conjure a Starfighter Pilot"; stationed 10+, your creatures fly. | Sheoldred's Edict | 2 |
| 100 Resistance Is Futile | Umbral Juke | sidegrade | Instant edict (creature or planeswalker), or a 2/1 flier. | UNOWNED: Sheoldred's Edict (2-mana instant edict) | 5 |
| 100 Resistance Is Futile | Vexing Drone | role-player | A 2-mana Borg artifact creature that taps a blocker on entering. | UNOWNED: Winter, Cursed Rider (not an artifact creature) | 4 |

## 4. Skips (graded, no home)

| Card | Deck matched | Why not |
|---|---|---|
| Gilt-Leaf Alchemist | 75 Historic Brawl | Needs two Elf cards already in the graveyard. |
| Val, Marooned Surveyor | 97 | Few scry / investigate effects there. |
| Ominous Seas, Splendor Mare, Zagoth Crystal, Flourishing Fox, Go for Blood, Easy Prey, Raking Claws | 101 | Match on "cycling" only. |
| Dathon, His Heart Open | 101 | Rewards casting enchantments; matched only on the Officer type. |
| Lich's Mastery | 101 | "You can't lose" with a lose-the-game rider; not this deck's plan. |
| Krydle of Baldur's Gate | 75 Historic Brawl, 96 | A 2-mana evasion enabler; lateral at best. |
| Glory-Bound Initiate | 78 Historic Brawl | Matched on Warrior only. |
| Gnawing Vermin | 96 | A 1-mana mill-two; minor. |
| Scourge of Valkas, Goblin Chainwhirler | 85 | {R}{R}{R} in a three-colour deck; few Dragons. |
| Hoshi Sato, Starfleet Academy | 100 | Their Federation count reads only non-Borg creature types, and deck 100 is nearly all Borg. |
| Draugr Necromancer | 91 | Snow-mana payoff with no snow in the deck. |
| Tactical Officer, Captain Jonathan Archer | 101 | Matched on the Officer type; neither cares about dilemmas. |
| Glaring Fleshraker | 97 | Rewards colourless spells, which the deck has few of. |
| Immersturm Skullcairn | 102 | A tapped land; the deck is cutting those. |
| Ravenous Cosmozoan | 56b | Discount needs noncreature cards in the graveyard; off-plan. |
| Leyline Tyrant | 85 | A Dragon payoff in a deck with few Dragons. |
| Mindless Conscription | 93 | Triggers on your third card drawn each turn, which the deck rarely reaches. |
| Raking Claws, Chittering Skullspeaker, Pact Weapon, Free Borg Revolutionaries, Reconnaissance Mission, Resolute Rejection, Shefet Monitor | 101 | Cycling or pay-life matches only. |
| Fangs of Kalonia | 88 | Doubles +1/+1 counters; deck 88 scales on power, not counters. |
| Soul-Scar Mage, Fiery Inscription, Masterpiece Vault | 56 Historic Brawl | Off the one-protected-attacker plan, or random value. |
| Winota, Joiner of Forces; Glory-Bound Initiate; Battershield Warrior; Kargan Warleader; Thunderbond Vanguard | 85 | Matched on Warrior only. |
| Boreal Outrider, Bramblearmor Brawler | 78 Historic Brawl | Matched on Warrior only. |
| Tempest Trapper, Atmosphere Surgeon, Raff Weatherlight Stalwart, Geistchanneler, Merfolk Trickster, Reflective Rimekin, Phyrexian Censor | 91 | Matched on Wizard only; none is a Zombie or a discard card. Phyrexian Censor also locks your own spells. |
| Primary Unimatrix Adjunct, Antagonist Incorporator, Command Subadjunct | 74 | Already in deck 100; Borg artifacts are off-tribe in the Dwarf deck. |
| Sunset Saboteur | 44, 44a | Its attack puts a +1/+1 counter on an OPPONENT's creature (your removal rule). |
| Tetsuko Umezawa, Fugitive | 44 | Needs creatures with power or toughness 1 or less. |
| Year of Hell | 26b, 37a | Symmetric draw and 2 damage to each player. |
| Federation Resupply | 65, 68 | Tutors Auras/Equipment/Spacecraft, which neither deck is built on. |
| Rediscover the Way, Ghost of Illyria, Collation Trimatrix, Machinist's Dismissal, Hologram Janeway, Una Chin-Riley, Pinnacle Emissary | 57, 41, 42, 84, 101, 26a | Low-fit tag matches. |
| Impossible Choice | any | Its removal mode gives the opponent two 1/1 Officers (your removal rule). |
| Fuel Tank Feaster, Bronze Walrus, Kami of Whispered Hopes | 89 | Deck 89's unowned ramp (Azusa, Kodama, Dryad) plays extra lands; a mana creature is not a substitute. |
| Sleep with the Fishes, Stab Wound, Swallow Whole | 98, 100 | Weaker than the paired removal above, or conditional (Swallow Whole needs a tapped target). |
| Card-advantage pairings into 96 and 98 | 96, 98 | Matched on the card-draw role only; none replaces a specific unowned card (planeswalkers, Sphinx's Revelation, the deck's commander-synergy draw). |
