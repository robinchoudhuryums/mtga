# Dark Leo & Shredder pile — analysis (TEMPORARY working doc)

**Status: DRAFTED as deck 104 (Way of the Foot), 2026-11-21; board round 2 APPLIED (14 swaps, §6b) the same day. The bench is the Builder board `builds/dark-leo` (https://claude.ai/artifact/NczS8xwUj3r6qX63Y6esve); delete this doc once the owner's board picks land and the findings are folded into deck 104's `#: notes:`.** For a NEW Orzhov Historic Brawl deck. Delete once the
deck is drafted and these findings are folded into its `#: notes:` block. A scratchpad, not a
source of truth — decks/ are.

**Source list:** `.cycle/dark-leo-pile.txt` — 172 cards + the commander. Not deduplicated against
other decks: this pile is for a new deck, and a card can sit in any number of decks at once.
All 172 resolve, are Brawl-legal and fit the W/B identity (four are two-faced cards stored under
`Front // Back`). Ownership (information only): 75 owned, 97 not (22 mythic, 36 rare, 32
uncommon, 7 common). The Builder board comes after the draft, as for decks 97 and 103 — a board
needs a deck file to grade against.

**Commander:** Dark Leo & Shredder {W}{B} — Sneak {W}{B}; attacking Ninjas have deathtouch;
combat damage to a player makes a 1/1 Ninja token, then if you control FIVE or more Ninjas that
player loses half their life.

## 1. The decision framework

- **F1 — the deciding number is NINJAS IN PLAY.** Five Ninjas when the commander connects is half
  the opponent's life (13 of 25). Tokens count; the commander makes one per hit. The pile holds 17
  Ninja cards, and a 100-card list that wants five on the battlefield needs most of them plus
  token makers. A Ninja card is worth more than its text; a non-Ninja creature must earn its slot.
- **F2 — what the deck pays is the SNEAK cost, not the printed one.** Sneak (and ninjutsu) casts
  happen in the declare-blockers step and return an unblocked attacker. So: (a) grade sneak cards
  at their sneak cost; (b) the deck needs cheap EVASIVE attackers (flying, menace, can't be
  blocked) to stay unblocked; (c) returning a creature with an enters trigger re-buys it
  (Ruthless Lawbringer, Turncoat Kunoichi, Vona de Iedo).
- **F3 — the payoff family is COMBAT DAMAGE TO A PLAYER.** The commander, Karai and the other
  Ninjas trigger on it. Deathtouch on attacking Ninjas makes every block a trade the opponent loses.
- **F4 — Brawl facts.** 100-card singleton, 1v1 at 25 life, free first mulligan. The commander
  recast tax applies to its sneak cost too ({W}{B} + {2} per recast), so sneaking the commander in
  is cheap even after a death.
- **F5 — one secondary engine, not four.** The pile also holds a lifegain cluster (Leonardo,
  Cutting Edge; Archangel of Thune; Ajani's Welcome; Elenda), an aristocrats cluster (Teysa,
  Elas il-Kor, Pitiless Plunderer, Blood Money) and a Treasure cluster (Smothering Tithe, Revel in
  Riches). Pick the one that overlaps the Ninja plan most; decide at the end, from the counts.
- **F6 — interaction.** Prefer instant speed and exile. Owner's rule: no removal that benefits the
  opponent. A sneak spell that is also removal (Karai's Technique) counts twice: interaction and
  an attacker re-buy.
- **F7 — ownership is information only** (Player Profile). Reported at the end, never a reason.

## 2. Standing error list

- Batch 3 note claimed deck 104 would be the roster's only Orzhov Ninja deck; deck 20 (Standard) is one. Caught by `deck.py similar` at draft; the header now says so.
- Classifier holes (G-67, record only): Biting-Palm Ninja, Black Widow, Double Agent, Ink-Eyes, Nashi and Swarm Saboteur score NO role — their value is a combat-damage trigger (hand exile, reanimation, impulse, conjure) or a lone-attacker grant. Acknowledged in role_baseline.txt by `make postedit`; fix in a classifier batch, with the K-12 roster diff.

## 3. Cross-batch observations

- Batch 2: the Ninja core is deep and CHEAP — six sneak/ninjutsu costs of 1–2 mana (Leonardo,
  Cutting Edge {W}; Splinter, Hamato Yoshi {B}; Swarm Saboteur {B}; Dokuchi Silencer {1}{B}; Last
  Ronin's Technique {1}{W}; Karai's Technique {W}{B}). Menace is the main evasion (Splinter ×2,
  Super Shredder, Killian, Syr Vondam, Ninja Teen level 2). Two half-life sources (commander at 5
  Ninjas; Shredder, Shadow Master alone).
- Batch 3: the commander's DEATHTOUCH grant is a second key — White Widow and Black Widow, Deadly
  Hunter read "a creature you control with deathtouch deals combat damage", which every attacking
  Ninja does. The lone-attacker cards (Black Widow, Double Agent; Squall) fit the one-attacker
  sneak setup. Lifegain keeps appearing as a secondary (Wispdrinker, Niv-Mizzet, Sorin ×2).
- Batch 4 is almost all LIFEGAIN payoffs (14 of 30). Variant signal (rule 7): they are rejected
  for the same reason every time — none of them makes a Ninja or reads combat damage. A lifegain
  deck is a different deck; in this one, lifegain stays incidental (lifelink bodies, Katana).
- Batch 6: the Treasure cluster splits — Rev and Grim Hireling read combat damage (in); the rest
  feed on sacrifices or their draws (out). Exalted Sunborn (batch 5) doubles the commander's
  Ninja tokens: the strongest single non-Ninja for F1.

- Batch 1: the lifegain variant signal is already visible (Leonardo, Cutting Edge; Ayli; Elenda,
  Saint of Dusk; Vona, Butcher of Magan all read "your life total"). Watch whether it overlaps
  the Ninja plan or competes with it (F5).

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

### Batch 1 (cards 1–30)

| # | Card | Verdict | Note |
|---|------|---------|------|
| 1 | Eirdu, Carrier of Dawn // Isilu | ◇ | Flying lifelink 5/5; convoke for creatures; back face gives persist. Good card, off-plan (F1). |
| 2 | Shaile, Dean of Radiance // Embrose | ★ | A 2-mana FLYING attacker (F2b) — an unblocked enabler; the back half is repeatable ping removal. |
| 3 | Ayli, Eternal Pilgrim | △ | Deathtouch 2-drop and a sac outlet; the exile needs +10 life. ★ only in a lifegain build (F5). |
| 4 | Cleric of Life's Bond | △ | Cleric lifegain; few Clerics here. |
| 5 | Despark | ★★ | Instant exile of anything MV 4+ (F6). |
| 6 | Feast of the Victorious Dead | △ | Aristocrats payoff; competes with F1 (sacrificing Ninjas lowers the count). |
| 7 | Elas il-Kor, Sadistic Pilgrim | ◇ | Deathtouch 2-drop; life on every creature entering (Ninja tokens, sneak re-entries). |
| 8 | Hardened Tactician | △ | Sacrifices tokens for cards — the commander's Ninja tokens are F1's count. |
| 9 | Karai's Technique | ★★ | Sneak {W}{B}: ±3/±3, either or both, and it returns an unblocked attacker (F2c, F6). |
| 10 | Karai, Future of the Foot | ★★★ | Ninja; combat damage returns a creature card — to the battlefield when sneaked (F1, F3). |
| 11 | Kaya, Geist Hunter | ◇ | Team deathtouch (attacking Ninjas already have it), doubled tokens once. |
| 12 | Lurrus of the Dream-Den | ★ | Recasts a ≤2 MV permanent from the graveyard each turn: the cheap Ninjas and enablers come back. |
| 13 | Mortify | ★★ | Instant: creature or enchantment (F6). |
| 14 | Oath of Kaya | ★ | 3 damage and 3 life on entry; punishes attacks on planeswalkers. |
| 15 | Ruthless Lawbringer | ★★ | Enters → sacrifice a creature, destroy any nonland permanent; sneak returns re-buy it (F2c). |
| 16 | The Kingpin of Crime | ◇ | Extort and toughness damage; off-plan. |
| 17 | Baron Bertram Graywater | ◇ | A lifelink Vampire when tokens enter, sac-draw; not Ninjas. |
| 18 | Elenda, the Dusk Rose | ◇ | Aristocrats/lifegain body (F5). |
| 19 | Elenda, Saint of Dusk | ◇ | Lifegain payoff; ★ in a lifegain build. |
| 20 | Kaya the Inexorable | ★ | −3 exiles any nonland permanent; +1 protects a key creature. |
| 21 | Starseer Mentor | ◇ | Flying vigilance 5-drop with an end-step punisher. |
| 22 | Spirit-Sister's Call | △ | Slow recursion engine. |
| 23 | Vona, Butcher of Magan | ★ | Repeatable removal for 7 life; better with lifegain (F5). |
| 24 | Vona de Iedo, the Antifex | ★★ | Enters → destroy a nonland, nontoken permanent; menace (F2b); sneak re-buys it. |
| 25 | Mister Negative | ◇ | 7-drop life swap and cards; situational at 25 life. |
| 26 | Moment of Reckoning | ★ | 7 mana, four modes of destroy or return. |
| 27 | Primevals' Glorious Rebirth | △ | Mass legend reanimation; slow. |
| 28 | Ashen Rider | △ | 8 mana. |
| 29 | Turncoat Kunoichi | ★★★ | Ninja; sneak 4 exiles a creature for good (F1, F2, F6). |
| 30 | Leonardo, Cutting Edge | ★★ | Ninja with Sneak {W}: the cheapest sneak in the pile; lifelink, grows on lifegain. |

### Batch 2 (cards 31–60)

| # | Card | Verdict | Note |
|---|------|---------|------|
| 31 | Quintessential Katana | ★ | Attaches itself to every Ninja that enters (sneaks included); untap plus 2 life per hit. |
| 32 | Lita, Little Orphan Amphibian | ★★ | A 2-mana Ninja (F1) that grows, makes Food or scries on every creature entering. |
| 33 | Leonardo, Sewer Samurai | ★★★ | Ninja; double strike (two combat-damage triggers, F3); recasts power-1 creatures from the yard on your turn — Splinter, Hamato Yoshi, Super Shredder, Leonardo, Cutting Edge. |
| 34 | The Last Ronin's Technique | ★★★ | Sneak {1}{W}, instant: three Ninja Turtle Spirit tokens tapped and ATTACKING — three Ninjas at once (F1). |
| 35 | Dokuchi Silencer | ★★ | Ninjutsu {1}{B}; a hit discards a creature card (recursion fodder) to destroy a creature or planeswalker. |
| 36 | Splinter, Hamato Yoshi | ★★★ | Ninja lord (+1/+1), menace, Sneak {B}. |
| 37 | Splinter, the Mentor | ★★ | Menace Ninja 2-drop; a Mutagen token whenever a nontoken creature leaves — every sneak return counts. |
| 38 | Super Shredder | ★★ | Menace Ninja that grows whenever ANY permanent leaves (sneak returns, deaths, removal). |
| 39 | Undead Hand Ninja | ★★ | Deathtouch Ninja 2-drop; drains whenever creature cards leave your yard (Karai, Lurrus, Leonardo). |
| 40 | Swarm Saboteur | ★★ | Ninjutsu {B}, deathtouch; a hit conjures Virus Beetle (more hand attack). |
| 41 | Biting-Palm Ninja | ★★ | Ninjutsu {2}{B}, menace; a hit exiles their best nonland card. |
| 42 | Ninja's Blades | ★★ | Job select makes a Hero token and makes it a NINJA (F1); loot plus life loss per hit. |
| 43 | Ninja Teen | ★★★ | Drain whenever a creature leaves (every sneak return); level 2 gives the team MENACE (F2b); level 3 sneaks creatures from the yard. |
| 44 | Nashi, Moon Sage's Scion | ★ | Ninjutsu {3}{B}; impulse paid with life. |
| 45 | Shark Shredder, Killer Clone | ★★ | Ninja; first strike; a hit steals a creature from their yard, attacking. |
| 46 | Shredder, Unrelenting | ★★ | 6/4 deathtouch Ninja for Sneak {3}{B}; lends deathtouch. |
| 47 | Shredder, Shadow Master | ★★★ | Ninja; its OWN hit takes half their life — a second half-life source that needs no Ninja count (the copy clause is blank in 1v1). |
| 48 | Ink-Eyes, Servant of Oni | ★★ | Ninjutsu 5; reanimates their creature; regenerates. |
| 49 | Fracture | ★ | Instant: artifact, enchantment or planeswalker. |
| 50 | Fleshtaker | △ | Aristocrats; fights F1. |
| 51 | Frodo, Adventurous Hobbit | △ | Needs 3 life gained a turn. |
| 52 | Golden Sidekick | ★ | 2-mana flying lifelink attacker (F2b). |
| 53 | Head of the Class | ◇ | Discount for creature-targeting spells. |
| 54 | Humiliate | ◇ | Hand attack plus a counter. |
| 55 | Killian, Ink Duelist | ★★ | Menace lifelink 2-drop (F2b); creature-targeting spells cost {2} less (Karai's Technique, removal, pumps). |
| 56 | Syr Vondam, Sunstar Exemplar | ★ | Menace vigilance 2-drop; grows on deaths and exiles (not on sneak returns). |
| 57 | Athreos, God of Passage | ◇ | Recursion tax on deaths. |
| 58 | Black Widow, Double Agent | ★ | A lone attacker gets first strike and menace — the one-attacker sneak setup (F2b); deathtouch. |
| 59 | Cloak and Dagger, Entwined | ★★ | Deathtouch lifelink; enters → exile a card from hand or a creature; sneak returns re-buy it (F2c). |
| 60 | Indulging Patrician | ◇ | Flying lifelink 1/4; ★ in a lifegain build. |

### Batch 3 (cards 61–90)

| # | Card | Verdict | Note |
|---|------|---------|------|
| 61 | Kambal, Profiteering Mayor | ◇ | Drains 1 when your tokens enter (commander Ninjas, Last Ronin's Technique); copies their tokens. |
| 62 | Kambal, Consul of Allocation | ◇ | Taxes their noncreature spells; a hate card. |
| 63 | Tymna the Weaver | ★ | A card a turn after combat damage (F3); in 1v1 that is pay 1, draw 1. |
| 64 | Basilica Bell-Haunt | △ | {W}{W}{B}{B} for a discard and 3 life. |
| 65 | Kaya's Wrath | △ | A sweeper in an attacking deck; emergency only. |
| 66 | Render Speechless | △ | Sorcery hand attack plus counters. |
| 67 | Sorin, Solemn Visitor | ◇ | Team +1/+0 lifelink, or a 2/2 flier (an enabler). |
| 68 | Silverquill, the Disputant | ◇ | Flying 4/4; casualty copies Karai's Technique and the removal — but the sacrifice costs a Ninja (F1). |
| 69 | Sorin, Vengeful Bloodlord | ◇ | Lifelink on your turn; −X reanimates. |
| 70 | Squall, SeeD Mercenary | ★ | A lone attacker gets double strike (two hits, F3); a hit returns a ≤3 MV permanent. |
| 71 | Teysa Karlov | ◇ | Doubles death triggers; aristocrats (F5). |
| 72 | Vito, Fanatic of Aclazotz | △ | Sacrifice payoff; fights F1. |
| 73 | Wispdrinker Vampire | ★ | Flier; drains on every small creature entering — most Ninjas, every sneak re-entry, every token. |
| 74 | Arvad the Cursed | ★ | Legends +2/+2: 12 of the 17 Ninjas are legendary, plus the commander. |
| 75 | Closing Statement | ★★ | Instant creature/planeswalker kill, cheaper at your end step (F6). |
| 76 | Syr Vondam, the Lucent | ◇ | Team deathtouch and +1/+0 on entry and attack; attacking Ninjas already have deathtouch. |
| 77 | Athreos, Shroud-Veiled | ◇ | Slow coin-counter recursion. |
| 78 | Niv-Mizzet, Ghost Counsel | ◇ | Lifegain draw engine (F5). |
| 79 | Blot Out the Sky | ★★ | X flying 2/1s: a wave of evasive attackers for sneaks (F2b); X ≥ 6 is a one-sided noncreature wipe. |
| 80 | Bleachbone Verge | ★★ | Untapped dual (gated W). |
| 81 | Cardassia Prime | ◇ | Tapland, 1 life. |
| 82 | Foot Headquarters | ◇ | Tapland, 1 life. |
| 83 | Fisk Tower | ◇ | Tapland, 1 life. |
| 84 | Godless Shrine | ★★★ | Untapped dual. |
| 85 | Great Hall of Starnheim | △ | Tapped, mono-B, sacrifice for an Angel. |
| 86 | Meticulous Commons | ◇ | Untapped only with a planeswalker out. |
| 87 | Shattered Sanctum | ★★ | Untapped from turn 3. |
| 88 | Temple of Silence | ★ | Tapped, scry 1. |
| 89 | White Widow, Yelena Belova | ★★ | Every deathtouch creature that connects grows — and attacking Ninjas all have deathtouch. |
| 90 | Black Widow, Deadly Hunter | ★★★ | A card per deathtouch creature that connects: under the commander, every Ninja hit draws (F3). |

### Batch 4 (cards 91–120)

| # | Card | Verdict | Note |
|---|------|---------|------|
| 91 | Vincent Valentine // Galian Beast | ◇ | Grows on their creatures dying (deathtouch blocks kill them); comes back once. |
| 92 | Massacre Girl, Most Wanted | △ | Aristocrats drain; fights F1. |
| 93 | The Cloning of Shredder | ★★ | Three non-legendary token copies of one creature card from your yard — of a Ninja, that is three Ninjas (F1). |
| 94 | Sally Pride, Lioness Leader | ◇ | Mutant tokens per nontoken creature; not Ninjas. |
| 95 | Ajani's Welcome | △ | Lifegain only (F5). |
| 96 | Speaker of the Heavens | △ | Needs +7 life. |
| 97 | Belladonna Took | ◇ | Pays off tokens entering (commander's Ninjas, Last Ronin). |
| 98 | Donald Blake, Guise of Thor | △ | Expensive power-up. |
| 99 | Grateful Apparition | ★ | 2-mana flier (F2b); proliferate on hit. |
| 100 | Griffin Aerie | △ | Lifegain only. |
| 101 | Leader's Talent | ◇ | A counter on an attacker each attack. |
| 102 | Selfless Samurai | △ | One-shot protection. |
| 103 | Sheltered by Ghosts | ★★ | 2-mana exile of any nonland permanent, plus lifelink and ward on your creature (F6). |
| 104 | Black Panther, Claws of Bast | ◇ | Counters on a lone attacker. |
| 105 | Dr. Beverly Crusher | △ | Lifegain doubler (F5). |
| 106 | Envoy of the Ancestors | △ | Lifelink for modified creatures. |
| 107 | Enduring Innocence | ★★ | A card a turn when small creatures enter — Ninjas, tokens and every sneak re-entry; returns once as an enchantment. |
| 108 | Ethereal Escort | △ | Lifelink spread. |
| 109 | Falcon, Joaquin Torres | ★ | 3-mana flying lifelink attacker (F2b). |
| 110 | Gideon Blackblade | ◇ | A 4/4 attacker on your turn; grants a keyword. |
| 111 | Light of Promise | △ | Lifegain Aura. |
| 112 | Metropolis Reformer | ◇ | Flier; you have hexproof. |
| 113 | MJ, Rising Star | △ | Lifegain payoff. |
| 114 | Practiced Offense | ◇ | Team counters plus double strike; flashback. |
| 115 | Teferi's Protection | ◇ | Protection from a board wipe. |
| 116 | Way of the Mentor | △ | Planeswalker loyalty from lifegain. |
| 117 | Exemplar of Light | ◇ | Flier; lifegain → counters → a card. ★ in a lifegain build. |
| 118 | Rosa, Resolute White Mage | ◇ | A counter and lifelink each combat. |
| 119 | Sigiled Contender | ✗ | Vanilla 4-drop. |
| 120 | The Wind Crystal | △ | Lifegain doubler. |

### Batch 5 (cards 121–150)

| # | Card | Verdict | Note |
|---|------|---------|------|
| 121 | Teyo, Aegis Adept | △ | Off-plan walker. |
| 122 | The Wandering Emperor | ★★ | Flash; −2 exiles a tapped creature, +1 a counter and first strike, −1 a token (F6). |
| 123 | Archangel of Thune | ◇ | Lifegain engine; ★ in a lifegain build (F5). |
| 124 | Bond of Discipline | ★ | Taps their whole board: every attacker unblocked, so every sneak is live — the five-Ninja finishing turn. |
| 125 | Captain America, Steve Rogers | ◇ | Counter and indestructible on an attacker. |
| 126 | Boon-Bringer Valkyrie | ◇ | Flier; backup hands a Ninja flying for the turn. |
| 127 | Doctor Strange, Surgeon | △ | Lifegain doubler. |
| 128 | Exalted Sunborn | ★★ | Token DOUBLER: two Ninjas per commander hit, six from Last Ronin's Technique (F1); Warp {1}{W} for the big turn. |
| 129 | Moogles' Valor | ◇ | Lifelink tokens plus team indestructible. |
| 130 | Shepherd of Heroes | △ | Party lifegain. |
| 131 | Tale of Tinúviel | ◇ | Protection then reanimation. |
| 132 | Inspiring Commander | ★ | A card for every small creature entering (tokens, sneak re-entries), no once-a-turn cap; 6 mana. |
| 133 | Loxodon Lifechanter | △ | Life-total reset. |
| 134 | Righteous Fury | ◇ | Kills tapped creatures — theirs after they attack. |
| 135 | Federation Outpost | ◇ | Mono-W land. |
| 136 | Toxin Analysis | ◇ | Cheap trick plus a Clue. |
| 137 | Tymaret, Chosen from Death | △ | Graveyard hate; fights Karai and Leonardo's recursion (G-42). |
| 138 | Black Market Connections | ★★ | Card, Treasure or a CHANGELING token each turn — a changeling is a Ninja (F1). |
| 139 | Madame Null, Power Broker | ◇ | Counters for life on each creature entering. |
| 140 | My Precious // Allure of Power | ★★ | Equip → hexproof and CAN'T BE BLOCKED: a guaranteed unblocked attacker for sneak every turn (F2b), or a protected commander. |
| 141 | Nadier's Nightblade | ◇ | Drain when tokens leave. |
| 142 | Origin of Black Widow | ★ | Edict, team deathtouch, drain. |
| 143 | Sanctum Lurker | △ | Planeswalker support. |
| 144 | Yathan Tombguard | ◇ | Menace; a card when a countered creature connects. |
| 145 | Withering Curse | ✗ | −2/−2 to all kills most of this deck's own Ninjas. |
| 146 | Barbed Servitor | ★ | Indestructible menace attacker that draws on a hit (F2b, F3). |
| 147 | Doctor Doom, Unrivaled | ★ | A card a turn on a 4/4 lifelinker. |
| 148 | Enduring Tenacity | ◇ | Lifegain drain (F5). |
| 149 | Eradicator Valkyrie | ★ | Flying lifelink 4/3; boast edict (sacrifice a token, not a Ninja card). |
| 150 | Erebos, Bleak-Hearted | ◇ | Cards on deaths; aristocrats. |

### Batch 6 (cards 151–172)

| # | Card | Verdict | Note |
|---|------|---------|------|
| 151 | Daxos, Blessed by the Sun | △ | Lifegain on enter/die. |
| 152 | Surgical Precision | ◇ | Sorcery: kill toughness 4+, or a card. |
| 153 | Bill the Pony | △ | Food and toughness damage. |
| 154 | Ghalta the Immovable | △ | Toughness-matters; off-plan. |
| 155 | Scourge of the Skyclaves | ◇ | Kicked, both players lose half their life. |
| 156 | Vincent's Limit Break | ◇ | Cheap protection trick. |
| 157 | Finale of Eternity | ★ | X removal for up to three creatures (F6). |
| 158 | Zero Point Ballad | △ | Sweeper that kills the small Ninjas first. |
| 159 | Veko, Death's Doorkeeper | ◇ | Recursion for a sacrifice. |
| 160 | Kingpin, Wilson Fisk | ◇ | Menace 3/6; Treasure on a sacrifice. |
| 161 | Tataru Taru | ◇ | A card, and a Treasure engine on their off-turn draws. |
| 162 | Smothering Tithe | ◇ | Treasure off their draws; slow in 1v1. |
| 163 | Deadly Dispute | ◇ | Sacrifice a token for two cards. |
| 164 | Grim Hireling | ★ | Two Treasures per connecting combat (F3); Treasures become removal. |
| 165 | Pitiless Plunderer | △ | Aristocrats Treasure. |
| 166 | Rev, Tithe Extractor | ★★ | Deathtouch on attack; every connecting combat makes a Treasure and steals a card (F3). |
| 167 | Ruthless Technomancer | △ | Sacrifice for Treasure; reanimation. |
| 168 | Blood Money | △ | A sweeper. |
| 169 | Revel in Riches | ◇ | Treasure on their deaths; slow alternate win. |
| 170 | Vraska, Betrayal's Sting | ◇ | Draw and proliferate; −2 neutralises a creature. |
| 171 | Lotho, Corrupt Shirriff | △ | Second-spell Treasure. |
| 172 | Vraska, Scheming Gorgon | ★ | −3 destroys a creature; +2 team pump. |

## 5. Consolidated plan (live)

**The deck: Orzhov Ninjas.** Win by connecting with Ninjas — the commander at five Ninjas takes
half their life, Shredder, Shadow Master does it alone — and draw off every connection (Black
Widow, Deadly Hunter reads the commander's deathtouch). Lifegain stays incidental (F5): the
pile's lifegain, aristocrats and Treasure clusters are each rejected for the same reason, none of
them makes a Ninja or reads combat damage, so they are a different deck (see Variant signals).

**Proposed core, 63 nonland cards + the commander** (printed avg MV 3.29; sneak lowers the real
cost — six sneak/ninjutsu costs are 1–2 mana):

- **Ninjas, all 17 (F1):** Karai; Turncoat Kunoichi; Leonardo, Cutting Edge; Lita; Leonardo,
  Sewer Samurai; Dokuchi Silencer; Splinter, Hamato Yoshi; Splinter, the Mentor; Super Shredder;
  Undead Hand Ninja; Swarm Saboteur; Biting-Palm Ninja; Nashi; Shark Shredder; Shredder,
  Unrelenting; Shredder, Shadow Master; Ink-Eyes.
- **Ninja makers (5):** The Last Ronin's Technique (three, attacking); Ninja's Blades (a Ninja
  Hero token); The Cloning of Shredder (three copies of a Ninja card); Black Market Connections
  (a changeling a turn); Exalted Sunborn (doubles every token).
- **Evasive enablers (12, F2b):** Shaile; Golden Sidekick; Killian, Ink Duelist; Syr Vondam,
  Sunstar Exemplar; Grateful Apparition; Falcon; Black Widow, Double Agent; Barbed Servitor;
  Wispdrinker Vampire; My Precious; Ninja Teen; Blot Out the Sky.
- **Combat-damage payoffs and engines (13, F3):** Black Widow, Deadly Hunter; White Widow;
  Enduring Innocence; Tymna; Rev, Tithe Extractor; Grim Hireling; Squall; Lurrus; Quintessential
  Katana; Arvad the Cursed; Doctor Doom, Unrivaled; Inspiring Commander; Eradicator Valkyrie.
- **Interaction (16, F6):** Despark; Mortify; Karai's Technique; Closing Statement; Sheltered by
  Ghosts; The Wandering Emperor; Ruthless Lawbringer; Vona de Iedo; Cloak and Dagger; Fracture;
  Kaya the Inexorable; Oath of Kaya; Finale of Eternity; Vraska, Scheming Gorgon; Origin of
  Black Widow; and Bond of Discipline as the finishing-turn enabler.
- **Lands (36):** the pile's Godless Shrine, Bleachbone Verge, Shattered Sanctum, Temple of
  Silence, Cardassia Prime, Foot Headquarters, Fisk Tower and Meticulous Commons, plus 28 more —
  basics and untapped duals chosen with `suggest --lands` once the list exists.

**Closest cuts if the owner wants other pile cards in** (each is the weakest of its group):
Inspiring Commander (6 mana), Nashi (impulse paid in life), Arvad, Grateful Apparition, Oath of
Kaya, Fracture, Origin of Black Widow.

**Strongest pile cards left out**, for the owner to argue back in: Archangel of Thune, Elenda,
Saint of Dusk, Vona, Butcher of Magan (lifegain); Teysa Karlov, Elas il-Kor (aristocrats);
Moment of Reckoning, Ashen Rider, Kaya's Wrath (top-end interaction); Sally Pride; Silverquill.

**Protect list** (value the ranking cannot see): Black Widow, Deadly Hunter and White Widow (they
read the commander's deathtouch grant); Ninja Teen (menace for the team, drain on every sneak
return); Exalted Sunborn and Black Market Connections (Ninja count, F1); My Precious (a guaranteed
unblocked attacker); Splinter, Hamato Yoshi (the lord).

**Variant signals (rule 7):** an Orzhov LIFEGAIN deck (Archangel of Thune, Elenda, Saint of Dusk,
Vona, Exemplar of Light, Enduring Tenacity, Ajani's Welcome, Dr. Crusher, Doctor Strange, The Wind
Crystal, Niv-Mizzet, Leonardo, Cutting Edge) and an ARISTOCRATS deck (Teysa, Elas il-Kor, Elenda,
the Dusk Rose, Massacre Girl, Pitiless Plunderer, Blood Money, Vito) are each coherent; neither is
this deck.

**Draft changes from this plan:** the land section became 14 nonbasics + 10 Plains + 12 Swamp — Silent Clearing, Brightclimb Pathway, Caves of Koilos, Concealed Courtyard, Isolated Chapel and Prismatic Vista (owned) in for six basics (`suggest --lands`; sources W 24 / B 26; tapped lands cost 2.0 points a card on `consistency --tempo`, under the roster median 2.7).

**Ownership (information only, F7):** of the 63 nonland cards and 8 pile lands, 35 are unowned —
5 mythic, 13 rare, 13 uncommon, 4 common.


## 6. Hybrid evaluation — board round 1 (2026-11-21)

The owner's first board marks (10 adds, 5 cuts, 29 bench) asked whether deck 104 can keep the
Ninja plan and mix in lifegain, aristocrats/sacrifice and Treasure. Three scratch copies were
measured against the drafted list (not deck files; `deck.py tier/quality/engines/consistency` on
a path):

| Version | Floor | Interaction | Card adv | Ninjas (tribes) | Lifegain payoffs | Board power | Tempo cost |
|---|---|---|---|---|---|---|---|
| Drafted 104 | A | 20 | 9 | 18 | 2 (25 sources) | 109 | 2.0 |
| A: marks as given | A | 18 | 7 | 16 | 7 | 107 | 2.1 |
| C: refined hybrid | A | 16 | 9 | 17 | 9 (31 sources) | 111 | 2.1 |

- **The lifegain half already existed.** The draft runs 25 lifegain sources (lifelink on Golden
  Sidekick, Killian, Falcon, Lurrus, Exalted Sunborn, Eradicator Valkyrie, Cloak and Dagger,
  Tymna, Katana's gain 2…) and 2 payoffs. A lifegain secondary is mostly adding PAYOFFS, which is
  why it costs the Ninja plan little.
- **Bridge cards** (help both plans): Sorin, Vengeful Bloodlord (all your creatures have lifelink
  on your turn, so every attacking Ninja gains life); Teysa Karlov (Ninja/Turtle/Inkling tokens
  get lifelink and vigilance); Indulging Patrician and Starseer Mentor (fliers, so also sneak
  enablers per F2b, plus a drain); Rosa and Leader's Talent (a counter and lifelink each combat);
  Elas il-Kor (every sneak entry and token gains 1 life).
- **Aristocrats and Treasure fight F1.** Sacrificing Ninjas lowers the count the commander reads,
  and sneak returns attackers to HAND, so death triggers are rare here. Treasure has no payoff in
  the list. Teysa and Elas are the light touch; Kingpin Fisk, Deadly Dispute, Baron Bertram,
  Ayli and Smothering Tithe stay on the bench.
- **Counters vs sneak (G-42):** a returned creature loses its counters and its Aura. Rosa and
  Leader's Talent are fine if the counter goes on the creature that stays in play; Light of
  Promise is not (the Aura falls off on the return).
- **Disagreements with the marks:** keep Cloak and Dagger (deathtouch + lifelink, and every sneak
  return re-buys its exile), Dokuchi Silencer (a Ninja and one of six 1–2-mana sneak costs) and
  Tymna (lifelink + draw; version A drops card advantage 9→7 mostly through Tymna and Doctor
  Doom). Agree on Biting-Palm Ninja and Doctor Doom.
- Niv-Mizzet, Ghost Counsel is {2}{W}{W}{B}{B}: 67% on turn 5 — a late-game card, not a curve play.

### 6b. Round 2 — owner's answers and the regrade (2026-11-21)

Owner: keep Squall, Grim Hireling and Black Widow, Double Agent; cut Dokuchi Silencer (needs a hit
AND a creature discard) and Tymna (card advantage capped at 1); Envoy belongs (its lifelink is
permanent, and Equipment counts as a modification). All three accepted. Squall and Black Widow, Double Agent still show
`targets` ⚠ CONFLICT against 9 go-wide cards; they stay for the lone-attacker turns.

**New criteria for the bench** (added to F1–F7): H1 lifegain SOURCES are plentiful (29), so a new
card earns a slot as a PAYOFF or as an evasive body that gains life; H2 +1/+1 counters are now a
third layer (Rosa, Leader's Talent, Archangel → Envoy lifelink, Yathan Tombguard draws) — mind
that sneak strips counters and Auras; H3 a sacrifice or Treasure card must not eat Ninjas and needs
a payoff — Treasure has none here; H4 card advantage must replace Tymna/Doom with repeatable draw.

**Version E (the plan, measured on a scratch copy):** floor A · interaction 15 (A needs 12 at 100)
· card advantage 9 (8 repeatable) · Ninjas 16 · lifegain 29 sources / 8 payoffs · counters 16 / 2
payoffs · board power 121 (was 109) · avg MV 3.34 (3.27) · early drops 18 (19) · tapped-land cost 1.9.
- ADD (16): Sorin, Vengeful Bloodlord; Archangel of Thune; Yathan Tombguard (new find — menace,
  draws off every countered attacker); Teysa Karlov; Indulging Patrician; Starseer Mentor; Rosa;
  Dr. Beverly Crusher; Niv-Mizzet, Ghost Counsel; The Wind Crystal; Leader's Talent; Elas il-Kor;
  Exemplar of Light; Envoy of the Ancestors; Vona, Butcher of Magan; Federation Outpost (for a Plains).
- CUT (16): Biting-Palm Ninja, Doctor Doom, Dokuchi Silencer, Tymna, Bond of Discipline, Inspiring
  Commander, Fracture, Blot Out the Sky, Origin of Black Widow, Arvad the Cursed, Vraska, Scheming
  Gorgon, Finale of Eternity, Oath of Kaya, Wispdrinker Vampire, Golden Sidekick, 1 Plains.
  Mortify and Kaya the Inexorable were kept: cutting them too put interaction at 13.
- Version D (Mortify + Kaya cut instead of Wispdrinker + Golden Sidekick) read interaction 13; rejected.

All 101 pile cards outside the deck were re-graded on the board under the new criteria
(groups: Hybrid plan: add · Bench: lifegain/counters · Bench: aristocrats/Treasure · Off-plan).
- **Applied 2026-11-21** with two changes from the plan above: Oath of Kaya and Golden Sidekick were
  KEPT (owner), so Vona, Butcher of Magan and Starseer Mentor went to the bench instead of in. Live:
  floor A · interaction 15 · card advantage 9 · board power 115 · avg MV 3.27 · early drops 19.
  Light of Promise (not added) and Cloak and Dagger (kept) were settled in chat and cleared on the board.

### 6c. Board round 3 — owner marks, feedback only (2026-11-21)

Marks: +Baron Bertram Graywater, +Starseer Mentor; −Enduring Innocence, −Falcon, −Ink-Eyes,
−Oath of Kaya, −Quintessential Katana, −The Cloning of Shredder (net −4); notes on Kingpin Fisk,
Primevals' Glorious Rebirth and Veko (answered on the board). Measured on scratch copies:
F (marks + Veko, Kingpin, Vona Butcher, Ethereal Escort): floor A · int 15 · CA 9 · Ninjas 15 ·
board power 123. G (keep Katana and Enduring Innocence; + Baron, Starseer, Vona, Veko): floor A ·
int 15 · CA 10 · Ninjas 15 · board power 119 · avg MV 3.23 · early drops 20. Recommended G:
Katana is the Envoy lifelink enabler and survives every sneak return; Enduring Innocence draws
off nearly every token and sneak entry. Baron is the first real Treasure payoff (sac Treasure: draw).
- **Round 4 applied 2026-11-21:** −Enduring Innocence +Baron, −Katana +Veko, −Falcon +Starseer,
  −Oath of Kaya +Enduring Tenacity, −The Cloning of Shredder +Elenda, the Dusk Rose (owner's reasons:
  Innocence caps at one draw, Baron replaces it; counters already feed Envoy; use slots on doubler
  payoffs). Massacre Girl declined; Ink-Eyes stays until its replacement is chosen — Vito first,
  Pitiless Plunderer second, Ruthless Technomancer third (replies on the board). Live: floor A ·
  int 14 · CA 9 · board power 123. Tooling gap: `swap --apply` did not retire the builder BENCH
  flex lines for the four adds (deck.py flex listed them as STALE); retired by hand.
- **Round 5 applied 2026-11-21:** −Ink-Eyes +Vito, Thorn of the Dusk Rose; −Lurrus +Replicator. Floor A ·
  int 14 · CA 9 · early drops 20. Land check (scratch copies, `consistency --tempo`): every W/B dual left
  in the pool enters tapped, so adding duals raises colour access (87.9% → 89–90%) but the as-built
  figure stays flat (58.7% now; 58.0–58.5% with 2–4 more duals, inside the ±0.8 noise). No fix needed;
  optional: −2 Swamp +Restless Fortress +Shambling Vent (creature lands, W 24 → 26, tempo-neutral).
- **Land swap applied 2026-11-21:** −1 Swamp +Shambling Vent (W 25 / B 26; as-built 58.7%, unchanged); Restless Fortress parked as a `#~` flex line.

### 6d. Final pass — fits, upgrades and spice from the WHOLE pool (2026-11-21)

Searched beyond the pile (`suggest --limit 0`, `pool.py --regex` for "opponent loses life, you gain",
"triggers an additional time", "twice that many", "whenever you gain life", sneak/ninjutsu).
Recommended 5 (scratch copy Q: floor A · int 14 · CA 9 · protection 4 · Ninjas 15 · board power 122 ·
quality guard clean): −Mortify +Shredder's Technique (strict upgrade); −Nashi +Elektra; −Grateful
Apparition +Delney (Dark Leo is a 1/3, so its trigger fires twice); −Closing Statement +Bloodthirsty
Conqueror (infinite drain with Vito, Thorn or Enduring Tenacity); −Kaya the Inexorable +Elspeth, Storm
Slayer. A first draft also cut Barbed Servitor and Eradicator Valkyrie — protection fell 4 → 2 and CA
9 → 8, so rejected. Spice with no slot: Elesh Norn, Mother of Machines; Oroku Saki; Exquisite Blood;
Splinter's Technique; Mondrak; Marauding Blight-Priest. All on the board under "Final pass".
