# Kellan, the Kid pile — analysis (TEMPORARY working doc)

**Status: DRAFTED as deck 107 (Kid from Anywhere, 2026-11-25); Builder board `builds/kellan`.** Delete once the deck is drafted and the
findings are folded into its `#: notes:` block. A scratchpad, not a source of truth.

**Source list:** the owner's 249-card pile (2026-11-25), commander **Kellan, the Kid**
({G}{W}{U}, 3/3 flying lifelink, owned). Format **Historic Brawl** (every card checked
brawl-legal). Deck 67 (Kid Flash) is the STANDARD Kellan deck (warp + plot); this is a separate
100-card build. No Builder project yet — it is created with the deck at /draft-deck.

## 1. The decision framework

Kellan: *"Whenever you cast a spell from anywhere other than your hand, you may cast a permanent
spell with equal or lesser mana value from your hand without paying its mana cost. If you don't,
you may put a land card from your hand onto the battlefield."*

**K1 — The number that decides a card is how many KELLAN TRIGGERS it makes, and their size.**
Every spell cast from exile, the graveyard, the top of the library (or anywhere not the hand) is a
free permanent from hand. The pile's trigger sources, by family:
- **airbend** (exile a permanent; its owner may recast it for {2}): Aang, Airbending Master;
  Aang, Swift Savior; Appa, Steadfast Guardian (ANY number of your permanents); Appa, Loyal Sky
  Bison (on entering AND attacking); Airbender Ascension; Airbender's Reversal; Glider Staff;
  Monk Gyatso; Avatar's Wrath;
- **plot**: Kellan Joins Up, Make Your Own Luck, Fblthp (plots from the top of the library),
  Railway Brawler, Visage Bandit;
- **warp**: Spirited Simulacrum, Anticausal Vestige;
- **adventure** (creature half cast from exile): Glamdring, Bilbo, Luckwearer; Kellan,
  Inquisitive Prodigy;
- **graveyard casting**: Torrential Gearhulk, Scholar of the Lost Trove, Bilbo, Thief in the
  Night, Valgavoth, Katilda and Lier;
- **library top / discover**: Mm'menon (artifacts), Falco Spara (anything, for a counter),
  Commander Spock, Data, U.S.S. Discovery, The Key to the Vault;
- **exile casting**: Idol of Endurance, Spara's Adjudicators.
Roughly 30 sources. A 100-card list wants ~15+ so Kellan fires most turns.

**K2 — Kellan's free cast is capped by the MANA VALUE of the spell cast from elsewhere, not by
what you paid.** An airbended 6-drop recast for {2} is a free 6-or-less permanent from hand; a
warp {4} Anticausal Vestige recast from exile is an MV 6 trigger. So high-MV cards that you
reliably cast from exile are worth more here than their price, and airbending your OWN
expensive creature is a real play, not a rescue.

**K3 — Airbend beats blink for this commander.** Blink (Don & Leo, Soulherder, Abuelo, Photon,
Wiccan, Silver Surfer, The Mighty Thor) re-triggers enters abilities but is not a cast, so no
Kellan trigger. Airbend exiles and you RECAST: enters ability again, AND a Kellan trigger, AND
the cast-from-exile payoffs (Appa's Ally tokens, Doc Aurlock's discount). Blink is still the
best way to re-use Clue makers and exile removal.

**K4 — Cost engines for the exile/graveyard casts:** Doc Aurlock ({2} less, plotting {2}
less), Bilbo, Thief in the Night ({1} less). With Doc out an airbend recast is FREE.

**K5 — Clues are the card-advantage spine, and token doublers double them.** Clue makers:
Constable Odo, Alquist Proft, Ezrim, Lonis (per creature entering), Tireless Tracker, The
Mechanist, Forensic Gadgeteer, Measure of a Man, Officious Interrogation, Confirm Suspicions,
Tamiyo's Journal, Kellan, Inquisitive Prodigy, Sharp-Eyed Rookie. Doublers: Bard, King of Dale
(tokens AND draws), Mondrak. Payoffs: Fateful Discovery (draw per artifact entering), Forensic
Gadgeteer (Clues cost {1} less), Mutagen Man. **Holo-Engineer is the trap**: it turns every
token into a 3/3 Illusion, so no Clues — out.

**K6 — Removal rule (owner): nothing that benefits the opponent.** Out on that: Soul of
Emancipation (3/3 fliers each), Rampage of the Clans (3/3s), The Sentry (gives them a 5/5),
Unyielding Gatekeeper's mode on THEIR permanent. The pile's exile removal (Seal from Existence,
Malfunctioning Holodeck, Sheltered by Ghosts, Detention Sphere, Aang's Iceberg, Assimilation
Aegis, Lagrella) is the clean core — and blinking an O-ring re-targets it.

**K7 — What no tool scores:** the Kellan trigger count (no role or tag for "cast from elsewhere"),
airbend recasts, and the free-cast size. `cuts` will under-read every airbend/plot card.

## 2. Standing error list
- E1: don't grade blink as a Kellan enabler — only CASTS from elsewhere trigger him (K3).
- E2: a spell cast "without paying its mana cost" FROM HAND (Lady Octopus, Vision, Yue,
  Conspiracy Unraveler) is still from hand — no trigger.
- E3: Derevi's command-zone ability is a put-onto-battlefield, not a cast, and works only as a
  commander.

## 3. Cross-batch observations
- **Core engine is clear**: airbend (9 cards) + plot (5) + graveyard casting (5) + library-top
  (6), with Doc Aurlock / Bilbo as cost reducers. That alone is ~27 cards.
- **Clue shell**: ~14 makers + Bard, King of Dale / Mondrak doublers + Fateful Discovery.
- **Variant signals** (clusters that keep grading ◇ for the same reason): a **Bant +1/+1
  counters** cluster (M'Benga, Brokers Ascendancy, Web-Warriors, Katara, Falcon, McCoy, Doctor,
  Wakka, Yotian Dissident, Thunderous Velocipede, Hamza, Guardian of Arashin), a **TMNT/Detective
  tribal** cluster (Donatellos, April O'Neil, Private Eye), an **attack-alone Hero** cluster
  (Nick Fury, Agent 13, Peggy Carter). None belongs in a Kellan cast-from-exile list.
- **Artifacts/improvise** (Ironheart, Kappa Cannoneer, Metallic Rebuke, Reverse Engineer,
  Mm'menon, Iron Man) overlaps the Clue shell: Clues are artifacts, so improvise is real here.

## 4. Running verdicts
Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

### Batch 1 (1–62)
| Card | Verdict | Note |
|---|---|---|
| Constable Odo | ★★ | ETB stun or two Clues; a blink target either way |
| Alquist Proft, Master Sleuth | ★★ | Clue on entering, and a Clue sink that draws X and gains X |
| Officious Interrogation | ★ | Clues equal to creatures; scales with the opponent's board |
| Bard the Bowman | ◇ | second-draw counters; Clues make the second draw easy, but the payoff is small |
| Private Eye | ◇ | Detective tribal; few Detectives |
| King T'Challa // Black Panther, Hope Enduring | ★★ | draws whenever any player draws their second card; Clues and Bard make that every turn |
| Hylda of the Icy Crown | ◇ | needs tapping opposing creatures (Tidus, Odo) |
| Ephara, God of the Polis | ★★ | upkeep draw if a creature entered last turn — blink makes that automatic |
| Bard, King of Dale | ★★★ | doubles tokens (Clues) AND turns every non-first draw into two — Clue cracks draw two |
| Live Long and Prosper | ◇ | 7-mana life and cards |
| Brokers' Safeguard | ★ | 2-mana instant blink with a shield counter |
| Gold-Forged Thopteryx | ★ | ward {2} on legends, incl. Kellan |
| Mendicant Core, Guidelight | ◇ | speed-gated artifact copy |
| Abuelo, Ancestral Echo | ★★ | repeatable blink of a creature or artifact, returning at end step |
| Scour the Scene | ◇ | pays off sacrificed Clues, but small |
| Spider-Woman, Stunning Savior | ◇ | opponents' creatures enter tapped |
| Assimilation Aegis | ★★ | exile removal, then the equipped creature copies it |
| Richlau, Headmaster | ◇ | artifact recursion, slow |
| Tidus, Blitzball Star | ★ | counter per artifact (each Clue) and taps a blocker |
| The Mighty Thor, Jane Foster | ★★ | on attack, blinks your own creature/artifact (an ETB again) or resets an opposing token |
| Cephalopod Sentry | ★ | power = artifacts (Clues) |
| Don & Leo, Problem Solvers | ★★★ | blinks an artifact AND a creature every end step |
| Ghalma the Shaper | ◇ | artifact tokens, off-plan |
| Urza, Prince of Kroog | ★ | copies an artifact for 6 |
| Teferi, Who Slows the Sunset | ★★ | untap, dig three, protection-ish |
| Riptide Gearhulk | ★★ | ETB tuck a permanent per opponent — a blink target |
| Tenth District Hero | ◇ | collect evidence; off-plan |
| Unyielding Gatekeeper | ◇ | flip blinks your own permanent; on theirs it gives them a 2/2 (removal rule) |
| April O'Neil, Live on the Scene | ◇ | Clue per Mutant/Ninja/Turtle; depends on the TMNT count |
| Excogitator Sphinx | ★ | Clues on combat damage; Clue → seek an instant/sorcery |
| Wraith, Vicious Vigilante | ◇ | unblockable double strike 1/1 |
| Conspiracy Unraveler | ◇ | collect evidence 10 instead of mana — cast from hand, so no Kellan trigger |
| Forensic Gadgeteer | ★★ | Clue per artifact spell; Clue and artifact abilities cost {1} less |
| Agent 13, Sharon Carter | ◇ | attack-alone Clues |
| The Measure of a Man | ★★ | exile your creature, investigate, return it — a delayed blink, or a temporary removal |
| Curious Inquiry | ◇ | aura Clues on damage |
| Confirm Suspicions | ★ | counterspell plus three Clues, at 5 |
| Tamiyo's Journal | ★ | Clue every upkeep plus a tutor; 5 mana |
| Knowledge Seeker | ◇ | second-draw counters |
| The Mechanist, Aerial Artisan | ★★ | a Clue per noncreature spell; animates Clues |
| Scene of the Crime | ★ | land that is also a Clue (and an artifact) |
| Aang, Air Nomad | ◇ | vigilance anthem |
| Aang, Airbending Master | ★★★ | airbend your own creature → recast it from exile for {2} (a Kellan trigger); experience tokens |
| Aang, Swift Savior // Aang and La, Ocean's Fury | ★★★ | flash airbend of a creature or SPELL; recast from exile for {2} triggers Kellan |
| Teferi's Protection | ★★ | the best protection effect in the format |
| Aang's Iceberg | ★★ | flash exile removal; waterbend sac to scry |
| Imperial Cosmographer | ★ | grows when creatures leave without dying (blink) |
| Dour Port-Mage | ★★ | draws when creatures leave without dying; bounces your own creature |
| Kami of Transmutation | ◇ | perpetual type change; niche |
| Klement, Novice Acolyte | ◇ | perpetual +1/+1 |
| Leader's Talent | ◇ | counters; off-plan |
| Shire Shirriff | ★ | sacrifice a Clue to exile a creature (until it leaves) |
| Sheltered by Ghosts | ★★ | 2-mana exile removal on an aura |
| Idol of Endurance | ★★ | casts MV≤3 creatures from exile for free — each one triggers Kellan |
| In the Trenches | ★ | anthem plus one exile |
| Malfunctioning Holodeck | ★★ | 3-mana warded exile removal |
| Nine Lives | ◇ | damage shield with a lose-the-game risk |
| Rasaad, Monk of Selûne | ★ | exile a creature until it leaves; a blink target |
| Seal from Existence | ★★ | warded exile removal |
| Suki, Courageous Rescuer | ★ | token whenever a permanent leaves on your turn (Clue sacrifices count) |
| Aurelia's Vindicator | ★ | disguise exile of X creatures |
| Celebrate the Mountain-king | ★ | exile one permanent per opponent and recruit |

### Batch 2 (63–124)
| Card | Verdict | Note |
|---|---|---|
| White Auracite | ★ | 4-mana exile removal that taps for W |
| Static Snare | ★ | flash exile of an artifact/creature; cheaper with attackers |
| Detention Sphere | ★★ | 3-mana exile of a permanent and all copies |
| Dr. Joseph M'Benga | ◇ | counters doubler; counters are not this deck's axis |
| Spirited Simulacrum | ★★ | warp it (cast later from exile = a Kellan trigger); land on enter, card on leaving — blink fodder |
| Anticausal Vestige | ★★ | warp {4}, leaves → draw and put a permanent onto the battlefield; recast from exile triggers Kellan |
| Priest of Possibility | ◇ | keyword lottery |
| Odric, Lunarch Marshal | ◇ | keyword sharing |
| Valkyrie Harbinger | ◇ | lifegain angels |
| Super-Adaptoid | ◇ | legendary count; keyword copy |
| Katara, Waterbending Master | ★ | experience from flash spells; loot on attack |
| Lyra, Tolarian Archangel | ★ | angel when you drew three; Clues help |
| Data, Exploring Humanity | ★★ | second draw each turn → discover 4 — a free cast from exile, which triggers Kellan |
| Krang, the All-Powerful | ★ | doubles draw-caused triggers (T'Challa, Data, Bard the Bowman) |
| Teferi, Temporal Pilgrim | ★ | draw engine walker |
| Pol Jamaar, Illusionist | ◇ | tribal draw; no tribe |
| Fateful Discovery | ★★ | draw a card whenever an artifact enters — every Clue (two with Bard, King of Dale) |
| Kindred Discovery | ◇ | needs a creature type |
| Donatello, Gadget Master | ◇ | copies an artifact on damage |
| Donatello, the Brains | ★ | extra Mutagen token whenever you make tokens (Clues) |
| Donatello, Way with Machines | ◇ | grows off artifacts |
| Irma, Part-Time Mutant | ★ | copies your best ETB creature each combat — copy, not ETB, though |
| Donatello, Mutant Mechanic | ◇ | animates artifacts |
| Skatewing Spy | ◇ | counters → flying |
| Wiccan, Rising Magician | ★★ | noncreature spell → blink a nontoken permanent (yours for an ETB, or theirs to reset) |
| Namor, Atlantean King | ★ | token per noncreature spell |
| Medomai the Ageless | ◇ | extra turn on damage, 6 mana |
| Matoya, Archon Elder | ★ | draw on scry/surveil |
| Land Tax | ★★ | thins basics and fixes; in Brawl you are often behind on lands early |
| Ashe, Princess of Dalmasca | ◇ | digs for artifacts on attack |
| Valgavoth, the Lifeline | ★★ | cast creatures from your GRAVEYARD after lifegain (Kellan has lifelink) — each one triggers Kellan |
| Does Machines | ◇ | loot then artifact recursion |
| Glamdring, Foe-hammer // Gleam of Death | ★★ | adventure: cast the sorcery, then the artifact from exile (a Kellan trigger) |
| Enter the Infinite | ◇ | 14 mana |
| Blind Obedience | ★ | opponents' creatures enter tapped; extort |
| Mondrak, Glory Dominus | ★★ | doubles tokens (Clues), 4 mana |
| Katara's Reversal | ★ | counter up to four spells/abilities |
| One with the Machine | ◇ | draw = biggest artifact MV |
| Tekuthal, Inquiry Dominus | ◇ | proliferate doubler |
| Mm'menon, the Right Hand | ★★★ | cast artifacts from the top of your library (each a Kellan trigger), and artifacts tap for mana for exactly those casts |
| Repulsor Bots | ★ | bounce two of your ETB creatures to recast |
| Valkyrie Aerial Unit | ★ | affinity flier; Clues pay for it |
| Krang, Master Mind | ★ | affinity refill to four cards |
| Cerebral Download | ★ | surveil X + draw three |
| Airbender Ascension | ★★ | airbend on entering (a recast from exile triggers Kellan), then a blink every end step |
| Appa, Steadfast Guardian | ★★★ | flash airbend of ANY number of your permanents (each recast from exile triggers Kellan), and an Ally token per spell cast from exile |
| Avatar's Wrath | ★★ | one-sided sweep: airbend everything else, and opponents can't cast from exile until your turn |
| Monk Gyatso | ★ | airbends your targeted creature — protection that recasts from exile |
| Airbender's Reversal | ★★ | removal, or airbend your own creature (protection plus a Kellan recast) |
| Glider Staff | ★★ | airbend on entering; flying equipment |
| The Key to the Vault | ★ | free cast from exile on combat damage |
| The Caretaker | ◇ | needs modal spells |
| Soulherder | ★★ | blinks a creature every end step |
| Metastatic Evangel | ◇ | proliferate |
| Urdnan, Dromoka Warrior | ◇ | counters |
| Extricator of Sin // Extricator of Flesh | ◇ | sacrifice → 3/2 |
| Koth of the Homestead | ◇ | landfall life |
| Rosie Cotton of South Lane | ★ | counter per token (each Clue) |
| Rumor Gatherer | ★ | scry or draw as creatures enter — blink feeds it |
| Dr. McCoy, Surly Surgeon | ◇ | counters |
| Felidar Retreat | ★ | landfall tokens/counters |
| The Sentry, Golden Guardian | ✗ | gives the opponent a 5/5 indestructible flier (removal rule spirit) |

### Batch 3 (125–186)
| Card | Verdict | Note |
|---|---|---|
| Anti-Venom, Horrifying Healer | ◇ | WWWWW; reanimate only when cast |
| Katara, Heroic Healer | ◇ | counters on the team |
| Nick Fury, Spymaster | ◇ | attack-alone |
| The Falcon, Sam Wilson | ◇ | counters on the team |
| Appa, Loyal Sky Bison | ★★ | airbends one of your permanents on entering AND on every attack — repeatable Kellan triggers |
| Captain Marvel, Shooting Star | ★ | 7-mana exile on entering/attack; opponent gains life |
| Saint Elenda | ◇ | WWW 7-drop |
| Ironheart, Clever Champion | ★ | improvise for noncreature spells (Clues pay) |
| Origin of Iron Man | ★ | tap-down, draw two, cheat an artifact |
| Iron Man, Futurist Paragon | ◇ | 6-mana animate |
| Stark's Ingenuity | ◇ | pay X draw X |
| Kappa Cannoneer | ★ | improvise; grows unblockable per artifact (Clues) |
| Metallic Rebuke | ★ | improvise soft counter, often free with Clues |
| Reverse Engineer | ★ | improvise draw three |
| Archway of Innovation | ◇ | improvise land |
| Lady Octopus, Inspired Inventor | ★ | free artifact casts — from hand, so no Kellan trigger |
| Malcolm, Alluring Scoundrel | ◇ | flash looter |
| Yue, the Moon Spirit | ★ | free noncreature spell from hand (waterbend pays with Clues) |
| Torrential Gearhulk | ★★ | flash; casts an instant from your graveyard — a Kellan trigger at instant speed |
| Vision, Spectral Synthezoid | ◇ | free casts from hand; 8 mana |
| Scholar of the Lost Trove | ★★ | casts an instant/sorcery/artifact from your graveyard (a Kellan trigger); blink target |
| Eagle of Deliverance | ★ | indestructible counter + draw |
| Ezrim, Agency Chief | ★★ | two Clues on entering (blink it) and sacrifices artifacts for keywords |
| Brokers Ascendancy | ★ | counters each end step |
| Peter Parker // Amazing Spider-Man | ★ | web-slinging returns a creature to recast (ETB again) |
| Derevi, Empyrial Tactician | ★ | can be put onto the battlefield from the command zone — but only as a commander |
| Disciplined Duelist | ◇ | shield double striker |
| Helga, Skittish Seer | ★ | draws on 4+ MV creatures; mana for big creatures |
| Gorion, Wise Mentor | ★ | copies Adventure spells (several here) |
| Katilda and Lier | ★ | flashback for instants/sorceries per Human spell — casting from the graveyard triggers Kellan |
| Kellan Joins Up | ★★★ | plots a card (a later free cast from exile = a Kellan trigger) and counters per legend |
| Lagrella, the Magpie | ★★ | exile removal on entering — a blink target |
| Rigo, Streetwise Mentor | ◇ | small-attacker draws |
| Spara's Bodyguard | ◇ | shield counters |
| Shanna, Purifying Blade | ★ | draw for lifegain (Kellan has lifelink) |
| Falco Spara, Pactweaver | ★★ | cast spells from the top of your library — every one a Kellan trigger; costs counters (shield, Clues are not counters) |
| Choco, Seeker of Paradise | ◇ | Bird attack digging |
| Sarek, Federation Ambassador | ◇ | creature-type draws |
| Tamiyo, Field Researcher | ★ | draws on damage, taps two |
| Yuna, Grand Summoner | ★ | any-colour mana |
| Aang, at the Crossroads // Aang, Destined Savior | ★★ | puts a creature from the top five onto the battlefield; transforms when a creature leaves (blink) |
| Tocasia, Dig Site Mentor | ◇ | surveil, artifact mass recursion |
| Commander Spock | ★★ | casts the top card free on entering/attack — from the library, a Kellan trigger; blink it |
| Spara's Adjudicators | ★ | exile from hand to fix a land, then cast it from exile later (a Kellan trigger) |
| Aang and Katara | ★ | Ally tokens per tapped artifact/creature |
| Soul of Emancipation | ★★ | OWNER RE-GRADE: target your own Clues for 3/3 fliers, or their best permanents |
| Urban Retreat | ★ | tri-land |
| Brigid, Clachan's Heart // Brigid, Doun's Mind | ◇ | Kithkin tokens / mana |
| Jake Sisko, War Correspondent | ◇ | landfall Clue on the second land |
| Sharp-Eyed Rookie | ★ | Clue when a bigger creature enters |
| Tireless Tracker | ★★ | a Clue on every land drop |
| Weirding Wood | ★ | ramp aura + Clue |
| Briarbridge Patrol | ◇ | Clues on creature damage |
| Ulvenwald Mysteries | ★ | Clue on death, token per Clue sacrificed |
| Lonis, Cryptozoologist | ★★ | Clue per nontoken creature entering (blink!) and a Clue sink that steals from their library |
| Undercover Crocodelf | ◇ | disguise Clue beater |
| Kellan, Inquisitive Prodigy // Tail the Suspect | ★★ | adventure: Clue + extra land, then cast the creature from exile (a Kellan trigger) |
| Path of Discovery | ★ | explore per creature entering |
| U.S.S. Discovery, at Black Alert | ★★ | discover 5 on entering/attack — a free cast from exile (Kellan trigger) |
| Monstrous Vortex | ◇ | needs power-5 creatures |
| Jadelight Ranger | ★ | double explore |
| Captain Kathryn Janeway | ★ | extra land + explore per creature entering |

### Batch 4 (187–249)
| Card | Verdict | Note |
|---|---|---|
| Auspicious Starrix | ◇ | mutate cheats permanents from exile (not cast) |
| Doc Aurlock, Grizzled Genius | ★★★ | spells cast from exile or graveyard cost {2} less, and plotting costs {2} less — the cost engine for every Kellan trigger |
| Make Your Own Luck | ★★ | plots a card from the top three (a free cast from exile later) and keeps the rest |
| Bilbo, Luckwearer // Burglar's Plot | ★★ | adventure: steal-swap a permanent, then cast Bilbo from exile (a Kellan trigger) |
| Railway Brawler | ★★ | plot it (free cast from exile = Kellan trigger); every creature entering gets counters equal to its power |
| Bilbo, Thief in the Night | ★★★ | spells cast from anywhere but your hand cost {1} less, and on attack you cast an artifact/instant/sorcery from your graveyard (a Kellan trigger) |
| Teething Wurmlet | ◇ | artifact lifegain |
| Legion of Clay | ◇ | trample anthem |
| Rampage of the Clans | ★ | OWNER RE-GRADE: destroy your own Clues for 3/3s; it also destroys our own exile-removal permanents |
| Pest Infestation | ★ | artifact/enchantment removal that makes your own tokens |
| Shuri, the Black Panther | ★ | draws on attack with 3+ artifacts (Clues) |
| Black Panther, Most Dangerous | ◇ | damage redirect |
| Black Panther, Wakandan King | ★ | counters on lands per creature entering; cashes in for a draw |
| T'Challa, the Black Panther | ◇ | Vibranium artifacts |
| Shuri, Vibranium Technologist | ★ | ETB token or draw — a blink target |
| Party Dude | ◇ | Food and artifact draw |
| Belt of Giant Strength | ◇ | off-plan |
| Elvish Archivist | ◇ | artifact counters, enchantment draws |
| Vivien's Arkbow | ◇ | creature cheat |
| Genesis Device | ◇ | land fetch |
| Reclamation Sage | ★★ | ETB artifact/enchantment removal — blink it for repeated answers |
| Sandstorm Salvager | ★ | ETB Golem — blink target |
| Sledge-Class Seedship | ◇ | spacecraft cheat |
| Thunderous Velocipede | ◇ | counters |
| Holo-Engineer | ✗ | turns every token (Clues!) into a 3/3 Illusion — kills the Clue plan |
| Summoner's Grimoire | ◇ | creature cheat on attack |
| U.S.S. Voyager, Lone Wanderer | ★ | ramp two lands |
| Silverback Elder | ★ | removal/land/life per creature spell |
| Storm, Shaker of Skies | ★ | ETB removal of artifact/enchantment/flier |
| Titan of Industry | ★ | ETB modes |
| Mutagen Man, Living Ooze | ◇ | Mutagen tokens; artifact token abilities cost {1} less (Clues!) |
| Baseball Bat | ◇ | tapper equipment |
| Sundering Growth | ★ | 2-mana instant artifact/enchantment removal |
| Yotian Dissident | ◇ | counters per artifact |
| Serah Farron // Crystallized Serah | ★ | legendary creature discount |
| Wakka, Devoted Guardian | ◇ | counters |
| The Doctor, EMH | ◇ | counters |
| Kwia Vigorbloom | ★ | Lotus per lifegain (Kellan lifelink) |
| Absorbing Man | ◇ | copies an artifact |
| Omega, Heartless Evolution | ◇ | stun on entering, 7 mana |
| Matt Murdock, Justice Seeker | ◇ | counters ward |
| Peggy Carter, Secret Agent | ◇ | attack-alone |
| Captain America, Super-Soldier | ◇ | Hero hexproof |
| Mockingbird, Ace Agent | ◇ | double strike, targeted spells |
| Photon, Lady of Light | ★★ | blinks your creature on every attack |
| Iron Man, Bleeding Edge | ★ | copies an artifact spell each turn |
| Silver Surfer, Cosmic Voyager | ★★ | flash mass blink of your permanents (ETBs again, and a wrath dodge) |
| Earth's Mightiest Heroes | ★ | cheat creatures from the top eight |
| Captain America, Living Legend | ◇ | untap on first tap |
| Ms. Marvel, Elastic Ally | ◇ | pump draws |
| Wylie Duke, Atiin Hero | ★ | draw whenever it becomes tapped |
| Web-Warriors | ◇ | counters on the team |
| Fblthp, Lost on the Range | ★★★ | plot cards from the top of your library — each later free cast from exile is a Kellan trigger |
| Visage Bandit | ★★ | plot it (free cast from exile) as a copy of your best ETB creature |
| Hamza, Guardian of Arashin | ◇ | counters discount |
| Delighted Halfling | ★★ | 1-drop, any colour for legendary spells |
| The Notary Hobbits | ◇ | colourless mana; few Halflings here |
| Pippin, Guard of the Citadel | ★ | protection from a card type |
| Gretchen Titchwillow | ★ | draw and put a land in (Kellan's land half) |
| Prosperous Innkeeper | ★ | Treasure + lifegain per creature entering |
| Belladonna Took | ★ | token triggers (Clues) |
| The Gaffer | ◇ | draw on 3+ lifegain |
| McCoy, Not a Bricklayer | ◇ | counters, Doctors |

## 5. Consolidated plan (live)

Counts: 249 graded → ★★★ 10 · ★★ 54 · ★ 84 · ◇ 97 · ✗ 4. ~37 lands + Kellan → ~62 nonland, so
the ★★★ + ★★ set (64) is about a deck; the open question is the mix.

**Tier 1 (★★★):** Bard, King of Dale; Don & Leo; Aang, Airbending Master; Aang, Swift Savior;
Mm'menon; Appa, Steadfast Guardian; Kellan Joins Up; Doc Aurlock; Bilbo, Thief in the Night;
Fblthp.

**Protect list:** every airbend and plot card, Doc Aurlock, Bilbo, Thief in the Night, Fblthp,
Mm'menon — `cuts` cannot see the Kellan trigger (K7).
