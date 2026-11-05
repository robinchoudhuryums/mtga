# Rocco pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** A new Historic Brawl deck (proposed deck 97), commander **Rocco, Street
Chef** (MAT) 44, `{R}{G}{W}`. The owner's brief: Food first, Dog and Cat subthemes, watch for
other synergies. Delete this doc once the deck is drafted and its findings are folded into the
deck file's `#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Source list:** 171 cards (the owner's message, 2026-11-05). 54 already sit in other decks; for
a NEW deck they are still candidates (the collection is shared), so all 171 are graded.
**Builder project:** created once the draft deck file exists (`builder.py new` grades against a
deck; there is none yet).

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

- (none yet)

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

## 5. Consolidated plan (live)

(after the last batch)
