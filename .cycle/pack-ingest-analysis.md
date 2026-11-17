# Pack ingest 2026-11-17 — where the new cards fit (TEMPORARY working doc)

**Status: IN PROGRESS — batch 3 of ~5 done.** A running record of the swap suggestions that
surface while the 582 cards from the 2026-11-17 pack ingest are checked against the decks.
Nothing here is applied; the owner picks, then `/apply-changes` writes. Delete this doc once
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
- Decks 91, 92, 94, 96 are not fully owned yet (40-ish cards missing each); a fit there is
  real but waits on the deck being built.

## 3. Suggestions by deck (live — re-sorted each batch)

| Deck | Card | Verdict | Why (from the text) | Suggested cut (unconfirmed) | Batch |
|---|---|---|---|---|---|
| 26 Iron Colossi | Pinnacle Emissary | role-player | A Robot artifact creature that makes a 1/1 flying Drone for every artifact spell you cast; warp {U/R} for an early trigger. | Cosmic Cube | 3 |
| 38 Armory | **Bat'leth** | upgrade | Equipment with removal: on entering, an opponent's creature gets -2/-2; then +2/+0. Orzhov Equipment, Standard-legal. | Shrike Force | 1 |
| 38 Armory | Combadge | role-player | Equipment that copies itself when cast (two for 3); a creature wearing one can't be blocked while another wears the other. Equip {2}. | Shrike Force | 3 |
| 48 Doombots | Pinnacle Emissary | role-player | As in 26: a Robot that turns artifact spells into flying Drones. | Untimely Malfunction | 3 |
| 75 Historic Brawl | Elvish Elegy | role-player | {B/G}: mill three, permanent +1/+1 to graveyard creatures, an Elf or land to hand. | Leyline of Transformation | 1 |
| 75 Historic Brawl | Perennial Gravewarden | role-player | 2-mana Elf that returns from the graveyard on a turn a creature entered and one died. | Leyline of Transformation | 1 |
| 85 Ghost-Spider | Concert Kaboomist | flavour | Damage to an opponent equal to noncreature spells cast since your last turn. | Torbran | 2 |
| 85 Ghost-Spider | Fiery Inscription | flavour | 2 damage to each opponent per instant or sorcery you cast; worth it only with a high spell count. | Torbran | 3 |
| 85 Ghost-Spider | Ghitu Journeymage | role-player | 2 damage to each opponent on entering if you control another Wizard; deck runs 7 Wizards. | Torbran | 1 |
| 85 Ghost-Spider | Soul-Scar Mage | role-player | Prowess; your noncombat damage to their creatures becomes -1/-1 counters. | Torbran | 1 |
| 85 Ghost-Spider | Unstable Amulet | role-player | 1 damage to each opponent whenever you cast a spell from outside your hand, plus energy-fuelled impulse draw; Gwen's exile plays trigger it. | Torbran | 2 |
| 88 Full Throttle | Hydra's Growth | flavour | An Aura that doubles the creature's +1/+1 counters every upkeep; a fast-growing threat for Samut. | Punishing Punch | 3 |
| 91 Scarab's Fist | **Narfi, Betrayer King** | upgrade | Other Zombies get +1/+1, and the deck runs 22 Zombies. (Its snow recursion is dead here.) | Anguished Unmaking — pick another; that one is interaction | 2 |
| 91 Scarab's Fist | **Sidisi, Undead Vizier** | upgrade | A Zombie with deathtouch; exploit (sacrifice a creature, e.g. a token) to tutor any card. | as above | 2 |
| 91 Scarab's Fist | Master of Waves | skip | Its devotion-to-blue tokens are thin in Esper; it is a Merfolk, so deck 94 may want it instead (not matched there). | — | 2 |
| 91 Scarab's Fist | Patchwork Crawler | skip | Exiles creature cards from your graveyard, which fights recursion. | — | 2 |
| 91 Scarab's Fist | Warren Soultrader | flavour | Pay 1 life, sacrifice another creature: a Treasure. A Zombie Wizard sacrifice outlet. | as above | 1 |
| 92 Phoenix King | Emperor of Bones | role-player | Exiles a card from a graveyard each combat; adapt {1}{B} brings an exiled creature back hasty for the turn, and every extra combat is another exile. | Aggravated Assault — the deck's extra-combat engine, pick another | 3 |
| 92 Phoenix King | Witch-king of Angmar | role-player | 5-mana flier; when creatures hit you, the opponent sacrifices one of them; discard a card for indestructible. | as above | 3 |
| 93 Two Heavens | Switchgrass Grazer | role-player | Haste; 1 damage to any target whenever it attacks, which Isshin doubles. | Steal the Show | 2 |
| 94 Paradox Sculptor | **Shapers of Nature** | upgrade | A Merfolk that puts +1/+1 counters ({3}{G}) and turns a counter into a card ({2}{U}); Zimone doubles counters. | Double Major — owner keeps it, pick another | 2 |
| 95 Light of Valinor | Ghost of Illyria | role-player | Flier that blinks your own nonland permanent until end step; a second Galadriel entry. | Panharmonicon | 2 |
| 96 Drowned Library | **Tamiyo, Compleated Sage** | upgrade | −X makes a token copy of a permanent card in your graveyard; +1 locks down a creature. | Lithoform Engine | 1 |
| 96 Drowned Library | Cauldron's Gift | role-player | Mill four, then return a creature from the graveyard with a +1/+1 counter (needs three black mana spent). | Lithoform Engine | 2 |
| 96 Drowned Library | Cemetery Tampering | role-player | Mill three each upkeep; a free hidden card once 20 cards are in your graveyard. | Lithoform Engine | 2 |
| 96 Drowned Library | Mesmeric Orb | flavour | Every untapping permanent mills its controller one; symmetric, so it mills you too. | Lithoform Engine | 3 |
| 96 Drowned Library | Sweet Oblivion | role-player | {1}{U}: a player mills four; escape recasts it from the graveyard. | Lithoform Engine | 3 |
| 96 Drowned Library | Vivien, Monsters' Advocate | role-player | Cast creatures off the top of the library; +1 makes a 3/3 each turn. | Lithoform Engine | 3 |
| 96 Drowned Library | World Shaper | role-player | Mill three on each attack; when it dies, every land in your graveyard returns. | Lithoform Engine | 3 |
| 97 Street Feast | **Feasting Troll King** | upgrade | Three Foods when cast from hand; returns from the graveyard by sacrificing three Foods. {G}{G}{G}{G}. | Mythweaver Poq | 1 |
| 97 Street Feast | Meriadoc Brandybuck | role-player | A Food whenever your Halflings attack; the deck runs 6 Halflings. | Mythweaver Poq | 1 |
| 97 Street Feast | Siege-Gang Commander | role-player | Three Goblin tokens (Peregrin Took adds a Food to each); sacrifice a Goblin for 2 damage. | Mythweaver Poq | 1 |
| 100 Resistance Is Futile | **Assembly Specialist** | upgrade | 2 mana for two Borg artifact creatures, feeding Collation Trimatrix's tap-three draw and Borg Cube's affinity. | Sheoldred's Edict — interaction, pick another | 3 |
| 100 Resistance Is Futile | Free Borg Revolutionaries | role-player | A Borg artifact creature that pumps the team on entering; basic landcycling {2} early. | as above | 3 |
| 100 Resistance Is Futile | Machinist's Dismissal | role-player | Counter a noncreature spell, {1} cheaper per artifact you control or hold; instant-speed interaction the deck lacks. | as above | 3 |
| 100 Resistance Is Futile | Squadron Carrier | role-player | Spacecraft gain "exhaust {W}: conjure a Starfighter Pilot"; stationed 10+, your creatures fly. | Sheoldred's Edict | 2 |

## 4. Skips (graded, no home)

| Card | Deck matched | Why not |
|---|---|---|
| Gilt-Leaf Alchemist | 75 Historic Brawl | Needs two Elf cards already in the graveyard. |
| Val, Marooned Surveyor | 97 | Few scry / investigate effects there. |
| Ominous Seas, Splendor Mare, Zagoth Crystal, Flourishing Fox, Go for Blood, Easy Prey, Raking Claws | 101 | Match on "cycling" only. |
| Dathon, His Heart Open | 101 | Rewards casting enchantments; matched only on the Officer type. |
| Lich's Mastery | 101 | "You can't lose" with a lose-the-game rider; not this deck's plan. |
| Krydle of Baldur's Gate | 75 Historic Brawl, 96 | A 2-mana evasion enabler; lateral at best. |
| Meteoric Mace | 56 Historic Brawl | 6 mana with equip {4}; top-heavy for the deck. |
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
