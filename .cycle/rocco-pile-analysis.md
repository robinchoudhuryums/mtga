# Rocco pile — analysis (TEMPORARY working doc)

**Status: DRAFTED as deck 97 (Street Feast), 2026-11-05; Builder board `builds/rocco` published.** Owner picks pending. A new Historic Brawl deck (proposed deck 97), commander **Rocco, Street
Chef** (MAT) 44, `{R}{G}{W}`. The owner's brief: Food first, Dog and Cat subthemes, watch for
other synergies. Delete this doc once the deck is drafted and its findings are folded into the
deck file's `#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Source list:** 171 cards (the owner's message, 2026-11-05). 54 already sit in other decks; for
a NEW deck they are still candidates (the collection is shared), so all 171 are graded.
**Builder project:** `builds/rocco` (deck 97), board https://claude.ai/artifact/EAzBxG8zy9VCQMuFejDKwH.

## 1. The decision framework

**The commander.** "At the beginning of your end step, each player exiles the top card of their
library. Until your next end step, each player may play the card they exiled this way. Whenever
a player plays a land from exile or casts a spell from exile, you put a +1/+1 counter on target
creature and create a Food token."

- **R1 — Rocco is a symmetric impulse draw that only WE are paid for.** Every player gets one
  extra card a turn; every play from exile, by ANY player, is our +1/+1 counter and our Food.
  So the opponent's extra card is the price, and our edge is (a) using our extra card better and
  (b) cashing the Foods. A card that adds a SECOND play from exile per turn (impulse draw,
  "exile the top card … you may play it") is a multiplier: it is extra card advantage AND an
  extra Rocco trigger. Grade those on plays-from-exile per turn.
- **R2 — Food is the currency, and a Food costs `{2}` to cash.** A producer is worth what the
  payoffs do with it. Payoffs that do NOT need the `{2}` (sacrifice a Food as a cost, "Foods you
  control" counts, Food-as-artifact counts) beat payoffs that need a crack per use. Sam, Loyal
  Attendant's `{1}` discount changes this rule for the whole deck.
- **R3 — Lifegain is the second currency.** Each crack is 3 life; realistic crack rate is 1–2 a
  turn on mana. "Whenever you gain life" payoffs fire about once a turn unless something gains
  life for free (lifelink, Ragost's untap loop). Count free lifegain before grading a payoff that
  wants several gains a turn.
- **R4 — Counters arrive for free.** Every Rocco trigger is a +1/+1 counter; counter payoffs and
  counter doublers are live from turn 4.
- **R5 — Tribe viability is the PAYOFF count (G-59).** In the Naya-identity Historic Brawl pool:
  **Cat payoffs 23** (152 Cat creatures) — a real subtheme; **Dog payoffs 9** (69 Dog creatures) —
  flavour unless the pile itself carries the payoffs. Grade a Dog card on its own text.
- **R6 — Historic Brawl, 100 cards, singleton, 25 life, 1v1, free first mulligan.** The A floor
  at 100 cards is interaction 12 with interaction + card advantage 19 (G-08 per-60 scaling).
  Interaction is the axis to watch: Food decks tend to be all engine.
- **R7 — Colour identity is WRG and it is a LEGALITY rule** (Brawl): a card outside it is
  illegal however payable. The pull marks identity; castability reads the printed cost.
- **R8 — Ownership is information only** (Player Profile).
- **R9 — The G-42 mirror here is "players can't gain life" / lifegain denial.** A card that
  stops lifegain turns every Food into a `{2}` do-nothing.

**Structurally invisible:** `Food` is flagged an unindexed mechanic on Rocco's own card; the
`food` synergy tag exists. "Play from exile" value (R1) is invisible to every model — `suggest`
cannot price a second Rocco trigger. Alchemy "perpetually"/"conjure" cards are legal here.

## 2. Standing error list

- Pool-absent cards read "!!NOT-HISTORIC-BRAWL" in the pull; unverified, not illegal (`legal` passed the list).

## 3. Cross-batch observations

- **Halfling cluster (LTR)**: Samwise, Sam, Rosie Cotton, Meriadoc already in batch 1 — Food
  makers that care about Halflings and Foods. Watch for Peregrin, Bilbo, Elanor, Belladonna,
  The Shire.
- **Token-plus-Food replacements stack**: Peregrin Took and Tippy-Toe each add a Food to EVERY
  token creation, so one Food becomes three with both out; Bilbo adds a Treasure per Food. With
  Rosie Cotton every token is a counter. This is the deck's engine core, not Rocco.
- **Lifegain → draw** (Tippy-Toe) and **Food → draw** (Peregrin) give a Naya deck real card
  advantage; Night of the Sweets' Revenge makes every Food a mana rock.
- **Free Food cracks**: Sam, Loyal Attendant (`{1}` less) + Mutagen Man (artifact tokens `{1}`
  less) make a Food crack cost `{0}` — free lifegain on demand, which turns Tippy-Toe's draw,
  Heroic Feast, Cat Collector and Ragost's untap into engines (R2, R3).
- **Foods are ARTIFACT tokens**: metalcraft (Galvanic Blast, Mox Opal), affinity (Sami),
  "three or more artifacts" (Shuri) all read them. Cards that need NONTOKEN artifacts (Meria)
  do not.
- **Second exile payoff**: Pia Nalaar, Consul of Revival makes a Thopter per play from exile —
  Rocco's own trigger, twice.
- **Artifact-sacrifice payoffs read every Food crack**: Biotech Specialist (2 damage), Krenko
  (a Goblin), Dragonspark Reactor (counter on entry). With free cracks (Sam + Mutagen Man) each
  Food is 3 life + 2 damage + a token. **Artifact ENTERING payoffs** (Haliya, Teething Wurmlet)
  make each Food a lifegain event, so lifegain payoffs fire several times a turn (revises R3).
- **Dogs earn slots through counters, not tribe** (R5 held): Yoshimaru, Generous Pup and
  Ainok Bond-Kin are COUNTER payoffs — Rocco supplies a counter every turn. The Dog/Cat tribal
  payoffs are Rin and Seri, Spider-Ham, Lucky and Jinnie Fay (which converts any token, Foods
  included, into Cats or Dogs).
- **Lifegain → Cat tokens** (Cat Collector) links the Food and Cat halves (R3, R5).
- **Pool-absent cards** read "!!NOT-HISTORIC-BRAWL" in the pull with rarity `?`: that is
  UNVERIFIED (no pool row), not illegal. Sidequest: Catch a Fish runs in deck 3-brawl.

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

### Batch 1 (cards 0–29)

| Card | R | Note |
|---|---|---|
| Ragost, Deft Gastronaut | ★★★ | Every artifact is a Food; `{1}`, sac a Food: 3 to each opponent, untaps when we gained life — the Food → damage engine (R2). |
| Wish Good Luck | ★ | Food + Treasure + 3/2 Vehicle for 2: three artifacts (Ragost reads each as a Food). |
| Hurska Sweet-Tooth | ★ | Attack → Food; lifegain → pay `{G/W}` pump. Fine, not an engine. |
| Resourceful Collector | ★ | Alchemy: each end step a graveyard permanent becomes a playable Food. Recursion, but from the graveyard, not exile (no Rocco trigger). |
| Iroh, Tea Master | ◇ | Donate a permanent each combat for a growing Ally; donating a spent Food is cheap. Spicy, slow. |
| Samwise Gamgee | ★★ | Food per nontoken creature entering; three Foods → historic card back. |
| Sam, Loyal Attendant | ★★★ | Food every combat and every Food ability costs `{1}` less: halves the crack cost (R2). |
| Rosie Cotton of South Lane | ★★ | Every token we create → +1/+1 counter; each Rocco trigger is a Food, so each is a counter too. |
| Lita, Little Orphan Amphibian | ★ | Alliance Food / counter / scry per creature entering. |
| Krovod Haunch | ★ | A Food card (Courier tutors it), +2/+0 equip, two Dogs when it dies. |
| Momo, Playful Pet | ◇ | 1-drop flier; leaves → Food or counter. |
| Hobbit's Sting | ★★ | Instant removal, X = creatures + Foods — real interaction at `{1}{W}` (R6). |
| Cat Collector | ★★ | Food on entry; first lifegain each of our turns → a Cat token (R3, R5). |
| Sidequest: Catch a Fish | ◇ | Upkeep card selection that flips to a land; pool-absent (unverified). |
| The Battle of Bywater | △ | Kills power 3+ — ours too, once Rocco's counters land. |
| Food Coma | ★★ | O-ring a creature plus a Food — interaction (R6). |
| Bill the Pony | ◇ | Two Foods; the toughness-damage trick is narrow. |
| Late to Dinner | ◇ | Reanimate one creature + Food. |
| Overcooked | ✗ | "Players can't gain life" — switches off every Food (R9). |
| Gilded Goose | ★★ | Ramp that makes and spends Food on turn 1. |
| Many Partings | ◇ | Basic land + Food for `{G}`. |
| Pippin's Bravery | △ | Pump. |
| Bumi's Feast Lecture | ★ | Food, then earthbend twice the Foods — a large hasty land by mid-game. |
| Courier of Comestibles | ★ | Tutors a Food CARD (Krovod Haunch, Ancient Cornucopia…) or makes a Food. |
| Intrepid Trufflesnout | △ | Attacks alone → Food; pool-absent. |
| Lucky the Pizza Dog | ★ | Cat / Dog / Hero spell → Food; lifegain → counter. Value tracks the Cat+Dog count (R5). |
| Meriadoc Brandybuck | ◇ | Halflings attack → Food; depends on the Halfling count. |
| Michelangelo, the Heart | ★ | Attack → counter + Food each turn. |
| Pawpatch Formation | ★★ | Modal instant: flier or enchantment removal, or draw + Food (R6). |
| Revive the Shire | ◇ | Permanent card back + Food. |

### Batch 2 (cards 30–59)

| Card | R | Note |
|---|---|---|
| Spider-Ham, Peter Porker | ★★ | Food on entry and +1/+1 to other Cats, Dogs, Bears, Birds, Boars, Squirrels… — the one lord covering both tribes (R5). |
| Tough Cookie | ◇ | Food, then `{2}{G}`: animate a noncreature artifact (a Food) as a 4/4. |
| Unlucky Cabbage Merchant | ◇ | One-shot: a Food sacrifice fetches a basic, then it goes to the library bottom. |
| Welcome to Sweettooth | ★ | Saga: 1/1, Food, then counters = 1 + Foods. |
| Bilbo, Fellow Conspirator | ★★ | Each Food we create also makes a Treasure: ramp that scales with every producer. |
| Creeping Crystal Coating | ◇ | Flash aura: +0/+3 and Food on attack. |
| Eager Trufflesnout | △ | Combat-damage Food. |
| Elephant-Mandrill | △ | Gives the opponent a Food too; grows off THEIR artifacts. |
| Food Chain | △ | Exile a creature for creature-only mana; not a Food card despite the name. |
| Giant Opportunity | ★ | Three Foods, or two Foods into a 7/7. |
| Heroic Feast | ★★ | Every lifegain puts a counter on that many creatures: one crack = three counters (R3, R4). |
| Hinterland Chef | ◇ | Alchemy draft; the drafted card becomes a Food. |
| Honored Dreyleader | ★ | Grows with every Food entering. |
| Peregrin Took | ★★★ | Every token creation adds a Food, and three Foods: draw a card — card advantage from the currency (R2). |
| Stew the Coneys | ★★ | Instant bite removal + Food (R6). |
| Spider Food | ★ | Artifact / enchantment / flier removal + Food. |
| The Cabbage Merchant | ★ | Their noncreature spells give us Food; two Foods tap for any colour. |
| Tireless Provisioner | ★★ | Landfall Food or Treasure; Rocco's exiled lands count (R1). |
| Bristlebud Farmer | ★ | Two Foods; attack: sac a Food to dig three for a permanent. |
| Elanor Gardner | ◇ | Food, and a basic each end step we sacrificed a Food. |
| Night of the Sweets' Revenge | ★★ | Foods tap for `{G}` — every Food is a mana rock — plus an overrun finisher. |
| Provisions Merchant | ◇ | Food; attack: sac a Food for team +1/+1 and trample. |
| Wicked Wolf | ★★ | ETB fight (interaction) and a Food sink for counters + indestructible. |
| Tippy-Toe, Terrific Partner | ★★★ | Every token creation adds a Food, and a lifegain turn draws a card (R3) — the card-advantage engine. |
| Bosco, Just a Bear | ◇ | Food per legendary creature; Food sink for counters. |
| Galadriel, Gift-Giver | ★ | ETB/attack: counter, Food or Treasure. |
| Feasting Troll King | ◇ | Three Foods cast from hand; returns for three Foods. `{G}{G}{G}{G}` in three colours. |
| The Shire | ★ | Legendary land that makes Food; untapped with a legendary creature (Rocco). |
| Ajani, Nacatl Pariah | ★★ | 2/1 Cat + transform; the walker makes Cats and pings (red permanent: Rocco). Pool-absent. |
| Big Spender | ◇ | Alchemy; Treasure on blocks, spellbook for two artifacts. |

### Batch 3 (cards 60–89)

| Card | R | Note |
|---|---|---|
| Legion Extruder | ★★ | ETB 2 to any target (interaction); `{2}`, sac a Food: 3/3 Golem. |
| Improvised Arsenal | ◇ | +1/+0 per artifact (Foods count). |
| Urabrask's Forge | ★ | A token every combat — each is an extra Food under Peregrin / Tippy-Toe and a counter under Rosie. |
| Mutagen Man, Living Ooze | ★★ | Artifact-token abilities cost `{1}` less: with Sam, a Food crack is FREE (R2, R3). |
| Tenured Tethermage | ◇ | Tap two artifacts: two counters. |
| Svella, Ice Shaper | ◇ | Mana rock maker; the `{8}` free cast is slow. |
| Aerid Konstrari | ◇ | Heartwood tokens; flier. |
| Roxanne, Starfall Savant | ★★ | A Cat; Meteorite pings 2 on ETB/attack; doubles artifact-TOKEN mana — Foods under Night of the Sweets' Revenge tap twice. |
| Pia Nalaar, Consul of Revival | ★★★ | Every play from exile is a hasty 1/1 flier — a second Rocco payoff (R1), and each token is a Food under Peregrin / Tippy-Toe. |
| Mabel, Heir to Cragflame | ◇ | Mouse lord; the equipment is the value here. |
| Hook Swords | ◇ | 1/1 Ally + first-strike equipment. |
| Thorin, King of Durin's Folk | △ | Dwarf payoffs; no Dwarves. |
| T'Challa, the Black Panther | ◇ | Vibranium tokens; counters on big artifact spells. |
| Dyadrine, Synthesis Amalgam | ★ | Removes Rocco's counters for a draw + Robot each attack (R4). |
| Toph, the First Metalbender | ◇ | Earthbend 2 each end step; artifacts-as-lands is incidental. |
| Sami, Wildcat Captain | ★★ | Every spell has affinity for artifacts — Foods make the deck cheap. Double strike body. |
| Mondrak, Glory Dominus | ★★★ | Doubles every token: Foods, Thopters, Cats. |
| Dockside Extortionist | ◇ | Treasure per opposing artifact/enchantment; 1v1-variable. |
| Craterclaw Colossus | ◇ | `{R}{R}{R}` finisher scaling with artifacts. |
| Indomitable Creativity | △ | `{R}{R}{R}` polymorph; destroys our own Foods for random permanents. |
| Shuri, the Black Panther | ★★ | Lifelink 2-drop; attack draws with three artifacts (Foods) (R3). |
| Iron Spider, Stark Upgrade | ◇ | Counters on artifact creatures; few here. |
| Karn, the Great Creator | △ | Its −2 wants a sideboard Brawl does not have. |
| Karn, Legacy Reforged | ◇ | Upkeep mana per artifact, artifact spells only. |
| Radiant Lotus | ★ | Sac Foods for three mana each — a burst. |
| Ori, Plate Stacker | ◇ | One-sided artifact/enchantment wipe at 7. |
| Galvanic Blast | ★★ | `{R}`, 4 damage with three artifacts (Foods) — cheap interaction (R6). |
| Heliod's Intervention | ★★ | Instant artifact/enchantment removal, or gain twice X (a lifegain trigger) (R6). |
| Meria, Scholar of Antiquity | △ | Taps NONTOKEN artifacts — Foods are tokens. |
| Mox Opal | ★ | Metalcraft from Foods. |

### Batch 4 (cards 90–119)

| Card | R | Note |
|---|---|---|
| Motivated Muralist | ◇ | Alchemy; conjures Inspiring Statuary. |
| Arc Reactor | ◇ | Improvise rock; Foods tap to pay. |
| Hungering Puppetbeast | ◇ | Food sink for counters and keywords. |
| Woodwork Prodigy | ★ | A Cat that makes a Heartwood every turn it re-prepares. Pool-absent. |
| Dragonspark Reactor | ★★ | A charge counter per artifact entering — every Food — then burns a player AND a creature (R6). |
| Tempestra, Dame of Games | ◇ | Sac a Food to copy a creature for a turn. |
| Shrapnel Blast | ★★ | Sac a Food: 5 to any target at instant speed (R6). |
| Vision of Love | ★★ | Sac a Food: draw two at instant speed. |
| Sokenzan Smelter | ★ | Each combat a Food becomes a hasty 3/1. |
| Glittering Stockpile | ◇ | Treasure that grows. |
| Krenko, Baron of Tin Street | ★★ | Every artifact to the graveyard — every Food crack — is a `{R}` hasty Goblin, itself a token (Peregrin / Tippy-Toe Food). |
| Lithobraking | ◇ | 2 to each creature — our 1/1 tokens too. |
| Momo's Heist | △ | Threaten an artifact. |
| Goldspan Dragon | ★★ | Treasures make two mana; Bilbo turns every Food into a Treasure too. |
| Purphoros, Bronze-Blooded | ◇ | Haste for the team; cheat ability narrow. |
| Rootwire Amalgam | ◇ | Prototype body. |
| Biotech Specialist | ★★★ | Every artifact sacrificed — every Food crack — deals 2 to the opponent (R2). |
| Variable Solutions | ◇ | Alchemy modal. |
| Rootha, Ardent Artisan | ◇ | Alchemy; pool-absent. |
| Pep, Raucous Raider | ★★ | Combat damage exiles their top card for us to play — a cast from exile (R1) — and sac an artifact for three mana. |
| Kwia Vigorbloom | ★★ | Lifelink flier; first lifegain each turn makes a Lotus (three mana). |
| Mindslaver | △ | 10 mana total. |
| Castle Doom | ★ | Utility land: sac a Food for a 3/3. |
| Haliya, Guided by Light | ★★★ | 1 life per creature or artifact entering — every Food — and a draw at 3+ life; Warp is a cast from exile (R1, R3). |
| Elesh Norn | ◇ | Punisher + transform; pool-absent. |
| Wedding Ring | ◇ | Symmetric in 1v1. |
| Teething Wurmlet | ★★ | Every artifact entering is 1 life: each Food becomes a lifegain trigger (R3). |
| Ancient Cornucopia | ★ | Any-colour rock + once-a-turn lifegain. Not a Food card (Courier misses it). |
| Arabella, Abandoned Doll | ★ | Drain per small creature on attack. |
| Excalibur II | ★ | Grows with every lifegain. |

### Batch 5 (cards 120–145)

| Card | R | Note |
|---|---|---|
| Sword of Light and Shadow | ★ | Protection, 3 life and a creature back on each hit. |
| Aetherflux Reservoir | ◇ | Lifegain per spell; the 50-life shot is a reach at 25 life. |
| Well of Lost Dreams | ★★ | Every lifegain: pay X to draw X — Food cracks become draws (R3). |
| Belladonna Took | ★★★ | Tokens entering: first gives life, second draws, third puts a counter on the team — Foods, Thopters and Cats all count. |
| Ajani Resolute | ★★ | Lifegain adds loyalty; −4 is a Pridemate Cat; −10 a team anthem. |
| West Wind Avatar | ◇ | A 7-mana Cat: sac a Food for 3 life, then draws (disappear). |
| Shortcut to Mushrooms | ★ | A Food sacrificed (a permanent left) is a counter at end step. |
| Michelangelo, Game Master | ◇ | Disappear counters on itself. |
| Tarkir Duneshaper | △ | A Dog 1-drop; pool-absent. |
| Ainok Bond-Kin | ★ | Every countered creature has first strike — Rocco counters (R4). Dog. |
| Generous Pup | ★★ | A counter on the Pup spreads to every creature — one Rocco trigger, team counters (R4). Dog. |
| Yoshimaru, Beloved Companion | ★★ | Every counter placement is one more (R4). Dog. |
| Flickering Hound | ◇ | Blink on creature cast — resets Rocco's counters (G-42). Dog. |
| Release the Dogs | ★ | Four Dogs: two extra Foods under Peregrin + Tippy-Toe, eight Dogs under Mondrak. |
| Enduring Courage | ◇ | Haste for tokens; a Dog. |
| District Mascot | ◇ | Dog; counters remove an artifact. |
| Torgal, A Fine Hound | ◇ | Any-colour dork; Human-spell counters. |
| Jiang Yanggu, Never Alone | ★ | Mowu (a Dog token) and untaps all tokens at end step. |
| Mowu, Loyal Companion | ◇ | Dog; counters +1 on itself. |
| Jinnie Fay, Jetmir's Second | ★★ | MAY turn any token creation into 2/2 haste Cats or 3/1 Dogs — Foods become bodies when the board needs them, and it feeds both tribes. |
| Rin and Seri, Inseparable | ★★ | Dog spell → Cat, Cat spell → Dog; `{R}{G}{W}`: damage = Dogs, life = Cats. The tribal payoff (R5). |
| Basri, Tomorrow's Champion | ★ | `{W}` lifelink Cat each turn. |
| Gloryheath Lynx | ◇ | Lifelink Cat; Plains on saddle. |
| Leonin Sanctifier | ◇ | Lifelink Cat; Alchemy grant. |
| Lion Sash | ★ | A Cat that eats graveyards and grows. |
| Adeline, Resplendent Cathar | ★★ | A Human token every attack — tokens feed Peregrin, Tippy-Toe, Belladonna, Rosie. |

### Batch 6 (cards 146–170)

| Card | R | Note |
|---|---|---|
| Brimaz, King of Oreskos | ★★ | A Cat token on every attack and block. |
| Ajani, Caller of the Pride | ★ | +1 counter; −8 makes Cats equal to our life total — large in a Food deck. |
| Ajani, Strength of the Pride | ★★ | +1 gains life per creature; −2 Pridemate Cat; 0 at 40 life exiles their artifacts and creatures (one-sided wipe) (R6). |
| Felidar Retreat | ★★ | Landfall: a 2/2 Cat or team counters; Rocco's exiled lands are landfall. |
| Leonin Warleader | ★★ | Two lifelink Cats attacking each swing — tokens and lifegain both. |
| Qala, Ajani's Pridemate | ★ | Cat that grows on lifegain and pumps the attack. |
| Angel of Invention | ★★ | Lifelink flier, team anthem, two Servos (artifact tokens). |
| Sally Pride, Lioness Leader | ★ | Cat; Mutants per nontoken creature, team counters on attack. |
| Old Hob, Alleycat Blues | ◇ | Cat; a temporary token every combat (a Food under Peregrin / Tippy-Toe). |
| Undergrowth Leopard | ★ | Cat 2-drop that trades for an artifact or enchantment (R6). |
| Greenhouse Propagator | ★ | Cat mana dork; 1 life per creature entering (R3). |
| Mythweaver Poq | ◇ | Alchemy: duplicates each land drop; a Cat. |
| Keeper of Fables | ★ | Cat; non-Human combat damage draws. |
| Ka-Zar of the Savage Land | ★ | Lands off the top, and Zabu, a Cat token that grows on landfall. |
| Swiftblade Vindicator | ◇ | Double strike body for Rocco's counters. |
| Arcbound Shikari | ◇ | Artifact-creature Cat; few artifact creatures here. |
| Dedicated Commons | △ | R/W dual tapped unless we control a planeswalker. |
| Solarium Sentry | ◇ | Cat; life when they cast cheap spells. |
| Kutzil, Malamet Exemplar | ★★ | Opponents can't cast spells on our turn; a countered creature connecting draws — Rocco's counters make every creature qualify (R4). Cat. |
| Drizzt Do'Urden | ★ | Guenhwyvar is a Cat token; double strike body. |
| Sovereign Okinec Ahau | ★★ | Each attack doubles the counters a creature carries above base — Rocco's counters compound (R4). Cat. |
| Zar Ojanen, Scion of Efrava | ◇ | Domain counters; three basic types at most. |
| Scattered Groves | ◇ | Tapped G/W dual with cycling. |
| Jetmir, Nexus of Revels | ★★ | Go-wide anthem (3 / 6 / 9 creatures) — tokens make it live. Cat. |
| Rocco, Cabaretti Caterer | ★ | X-tutor a creature onto the battlefield; the other Rocco. |

## 5. Consolidated plan (live)

**Measured on a scratch list** (`deck.py tier/stats/legal` on a file outside decks/, 62 nonland
cards below + The Shire, Castle Doom, Scattered Groves, Command Tower and 33 basics as a
placeholder manabase): legal at 100; **floor A** — interaction 15 (+2 unclassified) and card
advantage 6 (+2 unclassified) against an A line of 12 and 19; protection 4; board power 113;
printed avg MV 3.02. 42 of the 70 distinct cards are not in the library (information only, R8).

### Core (62 nonland) — the proposed list

- **Engine (9):** Ragost, Sam Loyal Attendant, Peregrin Took, Tippy-Toe, Pia Nalaar Consul of
  Revival, Mondrak, Biotech Specialist, Haliya, Belladonna Took.
- **Food makers / payoffs (13):** Samwise, Rosie Cotton, Cat Collector, Gilded Goose, Spider-Ham,
  Bilbo Fellow Conspirator, Heroic Feast, Tireless Provisioner, Night of the Sweets' Revenge,
  Mutagen Man, Teething Wurmlet, Lita, Lucky the Pizza Dog.
- **Artifact / mana (6):** Roxanne, Sami, Shuri, Krenko Baron of Tin Street, Goldspan Dragon, Pep.
- **Lifegain → cards (4):** Kwia Vigorbloom, Well of Lost Dreams, Vision of Love, Ajani Resolute.
- **Counters (4):** Generous Pup, Yoshimaru, Sovereign Okinec Ahau, Kutzil.
- **Cats / Dogs / go-wide (13):** Jinnie Fay, Rin and Seri, Adeline, Brimaz, Ajani Strength of the
  Pride, Felidar Retreat, Leonin Warleader, Angel of Invention, Jetmir, Ajani Nacatl Pariah,
  Greenhouse Propagator, Release the Dogs, Ka-Zar.
- **Interaction (12):** Hobbit's Sting, Food Coma, Pawpatch Formation, Stew the Coneys, Wicked Wolf,
  Legion Extruder, Dragonspark Reactor, Shrapnel Blast, Galvanic Blast, Heliod's Intervention,
  Spider Food, Undergrowth Leopard.
- **Tutor (1):** Rocco, Cabaretti Caterer.

### Bench (★, for the owner's swaps)

Wish Good Luck, Hurska, Resourceful Collector, Krovod Haunch, Bumi's Feast Lecture, Courier of
Comestibles, Michelangelo the Heart, Welcome to Sweettooth, Giant Opportunity, Honored Dreyleader,
The Cabbage Merchant, Bristlebud Farmer, Galadriel Gift-Giver, Urabrask's Forge, Dyadrine, Radiant
Lotus, Mox Opal, Woodwork Prodigy, Sokenzan Smelter, Ancient Cornucopia, Arabella, Excalibur II,
Sword of Light and Shadow, Shortcut to Mushrooms, Ainok Bond-Kin, Jiang Yanggu, Basri, Lion Sash,
Ajani Caller of the Pride, Qala, Sally Pride, Keeper of Fables, Drizzt.

### Out, with the reason

Overcooked (stops all lifegain, R9); The Battle of Bywater and Lithobraking (kill our own
countered creatures / tokens); Flickering Hound (blink resets Rocco's counters, G-42); Meria
(nontoken artifacts only); Karn, the Great Creator (no sideboard in Brawl); Elephant-Mandrill (feeds
the opponent); Indomitable Creativity (`{R}{R}{R}`, eats our Foods); Thorin (no Dwarves).

### Protect (what `cuts` cannot see)

Sam, Loyal Attendant + Mutagen Man (each `{1}` off a Food crack — together free), Peregrin Took and
Tippy-Toe (token-creation replacements, value is the rest of the deck), Mondrak (doubler), Pia
Nalaar (second Rocco payoff), Haliya and Teething Wurmlet (each Food is a lifegain trigger),
Biotech Specialist (each crack is damage).

### Tooling holes recorded (G-67, fix after the pile)

- `engines`' Food PAYOFF side misses "Sacrifice three Foods" (Peregrin Took, Samwise) and every
  "sacrifice an artifact" payoff that eats Foods (Biotech, Krenko, Shrapnel Blast, Vision of Love):
  it reads 6 Food payoffs on a list holding about 15.
- Heliod's Intervention ("Destroy X target artifacts and/or enchantments") scores no role: the
  X-count target is outside the Removal patterns.

### Open questions for the owner

1. Dogs: the list carries six Dog cards (Generous Pup, Yoshimaru, Lucky, Rin and Seri, Release the
   Dogs, Jinnie Fay's Dog mode); the pool's Dog payoffs are thin (R5). More Dogs means trading
   Cats or engine pieces.
2. Manabase: 37 lands with Gilded Goose, Bilbo's Treasures and Night of the Sweets' Revenge, or
   trim to 36? Picked at draft time from `suggest --lands`.

## 6. Pool sweep for deck 97 (2026-11-05, after the draft)

`suggest --limit 0`, `--interaction` and `pool.py --regex` effect-shape sweeps (exile-cast payoffs,
token replacements, Food / artifact-sacrifice / token-entering payoffs, lifegain → draw, Cat/Dog
lords, repeatable impulse draw), full text read on 58 finalists; 30 added to `builds/rocco` with a
reason and verdict each (board v2).

**Owned package, previewed with `swap 97 --package` (nothing written):** −Rocco, Cabaretti Caterer
+Doubling Season · −Ka-Zar +Parallel Lives · −Sami +Exalted Sunborn · −Spider Food +Elspeth, Storm
Slayer · −Pep +Quintorius Kand · −Greenhouse Propagator +Arahbo · −Goldspan Dragon +Valakut
Exploration · −Vision of Love +Bloombrute. Result: legal, floor A, interaction 15 (unchanged),
card advantage 6 → 7, board power 111 → 102 (tokens read zero), avg MV 3.03 → 3.08.

**Crafts worth it:** Caretaker's Talent (a draw every turn Foods enter), Ocelot Pride (copies the
turn's tokens with the city's blessing), Trail of Crumbs, Dawn of Hope; Anointed Procession only if
fewer doublers land. **Spice (owned):** Scalesoul Gnome — each play from exile conjures a duplicate.
**Declined:** Weapons Manufacturing and Junkyard Scrapper (NONTOKEN artifacts only), Case of the
Pilfered Proof (Detectives), Elspeth, Sun's Champion (−3 kills our countered creatures).
