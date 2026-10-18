# Marvel equipment pile → deck 84 — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into the
deck files' `#: notes:` blocks. A scratchpad, not a source of truth — decks/ are.

**Source list:** the owner's 249-card Marvel / equipment pile (2026-10-18, chat). Minus the
38 cards vetted in the first pile and the 10 more already in deck 84 → **201 to evaluate**,
every one inside the Jeskai (W/U/R) identity and Historic Brawl legal. Scratch list:
`pile2-rem.txt` in the session scratchpad (order = the owner's paste order).

**Target:** deck 84 Avengers Initiative (Historic Brawl, commander Director Nick Fury),
with the owner's new direction: lean into EQUIPMENT and ARTIFACTS.

## 1. The decision framework

Live vector of deck 84 (2026-10-18): interaction 19, card advantage 7, protection 11,
board power 124, avg MV 3.75, floor A (A at 100 cards = interaction 12, sum 19).
39 Heroes, 13 artifacts, 2 Equipment (Mjölnir, Swiftfoot Boots).

- **F1 — The commander rewards HEROES, not equipment.** Director Nick Fury: "Hero spells you
  cast cost {1} less" and "whenever you attack, look at the top four … reveal a Hero card".
  An Equipment is not a Hero card, so every non-Hero slot dilutes both halves. Measured:
  P(top four holds a Hero) is 88% at 40 Heroes, 83% at 35, 77% at 30, 69% at 25. **An
  equipment pivot that drops the deck below ~30 Heroes is paying for itself out of the
  commander.** Hero-TYPED artifacts (Iron Man, Vision, Robot Hero token makers) are the
  overlap that keeps both.
- **F2 — An Equipment costs its cast PLUS its equip.** Grade the sum, and grade the equip
  discounts (Bruenor's free first equip, an "equip {1}" for a type, auto-attach on entry)
  as cost reducers. An Equipment that attaches itself on entry is worth a mana or more.
- **F3 — Artifact COUNT is a resource.** It feeds Iron Man, Master of Machines (+1/+0 per
  other artifact), Ironheart's improvise, Iron Man, Titan of Innovation's MV+1 artifact
  chain, Tony Stark's dig, metalcraft and affinity. Count Equipment, rocks, artifact
  creatures and artifact TOKENS (Treasure, Clue, Robot).
- **F4 — Attack triggers are this deck's currency.** Nick Fury, Captain America, Skybound,
  Falcon and the Photons trigger on attack; an Equipment that grants evasion or protection
  makes the attack happen. Grade equipment by what it does to ATTACKING.
- **F5 — Brawl is 1v1 at 25 life, with sweepers and spot removal.** A voltron plan (one
  creature carrying everything) dies to one removal spell; Equipment that STAYS when the
  carrier dies is the anti-fragile half (that is the point of Equipment over Auras). Protection
  for the carrier (Swiftfoot Boots, ward, hexproof) is worth more here.
- **F6 — Variant signal: an equipment-first COMMANDER exists in the same colours.**
  Captain America, First Avenger (R/W/U): "at the beginning of combat on your turn, attach up
  to one target Equipment you control to Captain America" (a free equip every turn) and
  "{3}, unattach an Equipment from Captain America: he deals damage equal to that
  Equipment's mana value divided as you choose among one, two, or three targets". That is
  a different deck: Equipment as removal ammunition. Track every card that is better under
  him than under Nick Fury; decide at the end whether it is a variant (84a) or a pivot.
- **F7 — Structurally invisible here:** equip discounts and auto-attach are not a role; Hero
  density is not scored; `cuts` cannot see a card's value to Nick Fury's dig.

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

## 2. Standing error list

(none yet)

## 3. Cross-batch observations

- **O1 — Equipment TUTORS are Heroes** (Captain America, Liberator; Bucky; Tony Stark's dig),
  which is how an equipment package stays inside F1. Count them; a tutor in a 6-Equipment
  deck is worse than in a 15-Equipment deck.
- **O2 — A VOLTRON cluster is forming** (Zarda's exalted, Luke Cage and Black Panther, Claws
  of Bast's attacks-alone, Mockingbird's double strike). It pulls against the go-wide Hero
  plan (Falcon, Skybound battalion, Trick Shot). Variant signal for F6 — keep counting.
- **O3 — Hero TOKEN makers** (Aerith Rescue Mission, The Crystal's Chosen) feed every
  "Hero enters" payoff but are not Hero CARDS for Nick Fury's dig. Batch 2 adds two
  repeatable makers: Iron Man, Tony Stark (red spell → Robot Hero token) and Tellah
  (noncreature spell → Hero token).
- **O4 — An Equipment is a NONCREATURE SPELL.** Wiccan, Tellah, Iron Lad, Ironheart and the
  prowess Heroes all read "noncreature spell", so the equipment package powers them for free.
- **O5 — The artifact-creature Iron Men form their own sub-engine** (Master of Machines,
  Modern Marvel, Bleeding Edge, Tony Stark, Iron Lad, Ironheart, Repulsor Bots — all Heroes,
  all artifacts). That is the F1/F3 overlap: an "Iron Legion" package costs no Hero density.
- **O6 — The EQUIPMENT ENGINE is mostly NOT Heroes.** The pieces that make equipment cheap
  or free — Kíli (free first equip), Danitha Capashen (cost reducer), Danitha, Sword of Hope
  (draw), Sokka, Swordmaster (free attach), Weapons Vendor, Halvar (double strike + move),
  Super-Soldier Serum — are a Dwarf, two Knights, an Ally, an Artificer, a God and an Aura.
  Under Nick Fury each costs Hero density (F1). Under Captain America, First Avenger
  (F6), who does not care about Heroes, they are the core. **Variant signal is now strong:**
  an equipment deck led by Captain America, First Avenger, distinct from the Hero-tribal 84.

## 4. Running verdicts

### Batch 1 (cards 1–30)

| Card | Verdict | Note (from full text) |
|---|---|---|
| Bucky Barnes, Eager Ally | ★ | 2-drop Hero; dies → look at four, take an Equipment, Hero or Soldier. Serves both plans |
| Donald Blake, Guise of Thor | △ | a Human Doctor (NOT a Hero) until a {4}{W}{W} power-up (F1) |
| Patriot, Shield Wielder | ★ | 2-drop Hero; "{2},{T}: another target creature gets +2/+0 and gains hexproof" — protects the carrier (F5) |
| Aerith Rescue Mission | ★★ | three 1/1 colorless HERO tokens: three Hawkeye, Trick Shot triggers, three Team Leader counters; or tap three + stun |
| The Wasp, Janet Van Dyne | ◇ | 1/1 flier, enters: 4 to a TAPPED creature — conditional removal |
| Silver Sable, Mercenary Leader | ◇ | enters: a counter; attacks: a modified creature (Equipment counts) gains lifelink |
| Venat, Heart of Hydaelyn | ★★ | not a Hero, but "whenever you cast a legendary spell, draw a card" (once a turn) in a deck of ~40 legends is a card every turn; flips to an indestructible-granter that draws on legends |
| Hawkeye, Clint Barton | ✗ | a vanilla 3/5 vigilance for 4 |
| Luke Cage, Power Man | ◇ | attacks ALONE: +2/+0, indestructible — the voltron cluster (see §3) |
| Mockingbird, Ace Agent | ★ | double strike — the best possible Equipment carrier; counters only from targeting SPELLS (equip is an ability) |
| The Sentry, Golden Guardian | ✗ | gives the opponent a 5/5 flying INDESTRUCTIBLE Villain — a threat handed over (G-42 shape) |
| Spider-UK | ◇ | end step: draw + 2 life if two creatures entered |
| Okoye, Dora Milaje Leader | ◇ | two Soldier tokens, tokens get first strike attacking |
| Zarda, the Power Princess | ◇/★ | "other Heroes you control have exalted": strong for ONE big attacker (voltron), weak for go-wide |
| Anti-Venom, Horrifying Healer | ◇ | {W}{W}{W}{W}{W} reanimation; 22 W sources make it a late card |
| Captain Marvel, Earth's Protector | ★ | flash 5/4 flying lifelink |
| Captain America, Liberator | ★★★ | enters: search for an Equipment of MV ≤3 and put it ONTO THE BATTLEFIELD; attacks: a Soldier token per Equipment attached. The equipment pivot's best Hero |
| Captain Mar-Vell, Space-Born | ◇ | 4/4 flier for 5, conditional flash |
| Invisible Woman, Sue Storm | ◇ | Walls when Heroes get counters |
| Doctor Strange, Surgeon | ◇ | lifegain doubler — no lifegain engine here |
| The Falcon, Sam Wilson | ★ | flier; enters: a counter on each other creature (Captain Marvel, Apex Avenger copies counters) |
| The Crystal's Chosen | ◇+ | 7 mana: four Hero tokens then a counter on everything — four scaling Trick Shot hits |
| Secret Identity | ★ | {U} instant: hexproof (or becomes a 3/4 flying Hero) — cheap carrier protection |
| Kid Loki | ◇ | needs counters-and-draw-two |
| Tony Stark // The Invincible Iron Man | ★★★ | "{1},{T}: look at four, take an artifact" is the equipment deck's card advantage; the back face puts an artifact from hand onto the battlefield each combat and AUTO-ATTACHES an Equipment (F2) |
| Virtual Assistant | ✗ | needs teamwork; the deck has none |
| Wasp, Shrinking Savior | ◇ | its draw needs creatures with NEGATIVE power |
| Mister Fantastic, Reed Richards | ◇+ | draws when tokens enter — Hero tokens, Treasure, Robots |
| Immortus, Master of Eternity | ◇ | a mana engine for noncreature spells, wheel power-up |
| Iron Man, Modern Marvel | ★★ | Hero-TYPED artifact lord: other artifact creatures +1/+1, draws on attack with another artifact creature (the F1/F3 overlap) |

### Batch 2 (cards 31–60)

| Card | Verdict | Note (from full text) |
|---|---|---|
| Ironheart, Clever Champion | ★★ | artifact Hero flier; "noncreature spells you cast have improvise" — every Equipment is a noncreature spell (O4) |
| Iron Man, Bleeding Edge | ★★★ | "whenever you cast an artifact spell, you may copy it, except the copy isn't legendary" once a turn — a second copy of every Equipment |
| Reed Richards, Smartest Man | ★ | 6 mana; the first extra draw each turn becomes FOUR — pairs with Venat, Daredevil, Tony Stark |
| Repulsor Bots | ★ | Robot Hero artifact flier; enters: return up to two artifacts/creatures (theirs, or your own enters-trigger Heroes) |
| Heartfire Hero | ◇/★ | NOT a Hero (Mouse Soldier). Valiant: an EQUIP targets it, so it grows each equip; dies → damage equal to its power to each opponent. A classic carrier, but F1 |
| Gwen Stacy // Ghost-Spider | ◇+ | 2-drop Hero that exiles a card to play; {2}{U}{R}{W} flips to a flying haste grower |
| Hawkeye, Master Marksman | ★ | 2-drop; when tapped (attacking) pay {1} up to three times: can't block / 2 damage / loot |
| Iron Fist, Hero for Hire | ◇ | 2-drop trample prowess; the power-up is 8 mana |
| Iron Fist, Living Weapon | ◇ | needs SPELLS that target your creature (equip is not a spell) |
| The Scarlet Witch | ✗ | discounts instants/sorceries of MV ≥4 — the deck runs few |
| Nico Minoru, Runaway | ◇ | needs casting from outside the hand |
| Photon, Mighty Marvel | ◇ | flier; combat damage → that much mana |
| The Whizzer, Classic Speedster | △ | vanilla 3/3 first strike haste — a carrier at best |
| Wiccan, Young Avenger | ★ | "whenever you cast a noncreature spell, exile the top card … you may play that card" — Equipment fire it (O4) |
| Iron Man, Tony Stark | ★★ | artifact Hero flier; attacking creatures +1/+0; every RED spell makes a 2/1 flying Robot HERO artifact token (O3, F3) |
| Wonder Man, Hollywood Hero | ◇ | power-ups twice; the deck has few power-ups |
| Captain America, Living Legend | ★ | untaps each creature the first time it taps on your turn: Tony Stark's dig and Hawkeye's arrows twice, attackers stay back as blockers |
| King T'Challa // Black Panther, Hope Enduring | ◇+ | flash; draws when anyone draws a second card; back: double strike, damage prevented |
| Cid, Timeless Artificer | ★ | NOT a Hero, but "artifact creatures AND Heroes get +1/+1 for each Artificer you control and in your graveyard" — and "a deck can have any number of cards named Cid", so Brawl's singleton rule does not bind it (spice) |
| Spider-Man 2099 | ◇+ | {U}{R} double strike vigilance (castable turn 4+) — a carrier |
| Iron Lad, Young Avenger | ★★ | artifact Hero flier; "noncreature spells you cast cost {1} less" — Equipment included |
| Speedball, New Warrior | ◇ | needs spells that target it |
| Iron Man, Master of Machines | ★★ | +1/+0 per other artifact; draws on attack if an artifact entered this turn (F3) |
| Teferi, Hero of Dominaria | ★★ | +1 draw and untap two lands; −3 tucks any nonland permanent — card advantage AND interaction (mythic craft) |
| Tellah, Great Sage | ★ | NOT a Hero, but every noncreature spell makes a 1/1 Hero TOKEN; four+ mana spent draws two (O3, O4) |
| Marvel Boy, Noh-Varr | ◇ | grows on creatures entering |
| Mabel, Valley Hero | ◇ | not a Hero (Mouse Soldier); counters on entering creatures |
| Patriot, Young Avenger | ★ | prowess; "as long as Patriot is equipped, other creatures you control get +1/+0" |
| Daredevil, Man Without Fear | ★★ | haste, vigilance; whenever you attack, exile the top card — a Hero gives +2/+1 — and you may play it: a second Nick Fury dig |
| The Super Hero Civil War | ★★ | Saga: steal up to two creatures (total MV ≤6), team pump, then a fight — interaction |

### Batch 3 (cards 61–90)

| Card | Verdict | Note (from full text) |
|---|---|---|
| Thor Odinson | ★ | flying vigilance, prowess twice — every Equipment cast is +2/+2 (O4) |
| Captain America, First Avenger | ★★ / commander | free attach every combat ("Catch") and "{3}, unattach: damage equal to that Equipment's MV divided among up to three targets" (F6). In the 99 a strong card; as COMMANDER, a different deck |
| Iron Man Armor | ★★ | attaches itself on entry (F2), +2/+1 flying; {2} turns it into a Construct HERO that grows with your artifact count |
| Team Transmitter | ★ | a 3-mana any-colour rock that gains 1 per Hero entering |
| Viv Vision, Teen Synthezoid | ★ | 3-mana artifact Robot Hero flier; draws on attack at power 4+ (one Equipment gets there) |
| Iron Spider, Stark Upgrade | ★ | {T}: a counter on each artifact creature; {2}, remove two counters: draw (O5) |
| The Vision | ★★ | 4-mana artifact Hero flier; each noncreature spell: double strike / indestructible / draw (O4) |
| Silver Surfer, Galactus's Herald | △ | a 5-mana 4/5 flier whose value is tutoring a 10-drop |
| Galactus, Devourer of Worlds | △ | {10}; not a Hero; spice only |
| Crystal Fragments // Summon: Alexander | ◇+ | {W}, equip {1}, +1/+1; at seven mana flips to a Saga that fogs twice and taps their team |
| Iconic Shield | ◇ | +1/+2, gives another attacker indestructible; equip {3} |
| Quintessential Katana | ◇ | untap + 2 life on combat damage; its free attach is for Ninjas |
| S.H.I.E.L.D. Spy Kit | ◇ | equip {1}; attacks ALONE: untap and scry (O2) |
| Ancestral Katana | △ | Samurai/Warrior attacking alone only |
| Bark of Doran | △ | toughness-as-damage; only a few high-toughness Heroes |
| Kíli the Resourceful | ★★★ | not a Hero (Dwarf), but storied is trivial here (three artifacts/LEGENDARIES) → "pay {0} rather than the equip cost of the first equip ability you activate each turn", and draws when an Equipment enters (once a turn) — the equipment engine (O6) |
| Rune of Sustenance | ◇ | Aura that draws; can enchant an Equipment to grant lifelink |
| Spectral Steel | ◇ | +2/+2 Aura that later rebuys an Equipment |
| Super-Soldier Serum | ★★ | Aura: +2/+2, first strike, vigilance; "whenever enchanted creature attacks or blocks, attach ANY NUMBER of Equipment you control to it" — free mass equip, but an Aura dies with its creature (F5) |
| Danitha Capashen, Paragon | ★★ | not a Hero; Aura and Equipment SPELLS cost {1} less; first strike, vigilance, lifelink body (O6) |
| Danitha, Sword of Hope | ★★ | not a Hero; draws when you cast an Equipment (or target your creature), once a turn (O6) |
| Godsend | ★ | mythic; +3/+3, exiles a blocker/blocked creature; equip {3} |
| Infinity Formula | ◇ | self-attaching +1/+2 and 2 life per attack |
| One Last Job | ★ | spree: reanimate a creature AND return an Equipment attached to it |
| Plate Armor | ★★ | +3/+3 and ward {1}; equip {3} minus {1} per other Equipment |
| Sokka, Swordmaster | ★ | an Ally, not a Hero; attaches an Equipment to himself every combat for free (the Ally discount is idle here) |
| Halvar, God of Battle // Sword of the Realms | ★★★ | "creatures you control that are enchanted or equipped have DOUBLE STRIKE" and moves an Equipment each combat; back face is itself an Equipment (mythic) |
| With Great Power . . . | ◇+ | +2/+2 per Aura/Equipment on it, and redirects damage you'd take onto it |
| Weapons Vendor | ★ | an Artificer, not a Hero; draws on entry, pays {1} to attach each combat |
| Machinist's Arsenal | ★★ | makes a 1/1 Hero TOKEN and attaches to it; +2/+2 per artifact you control; makes it an Artificer (Cid) |

## 5. Consolidated plan (live)

(after the last batch)
