# Dark Leo & Shredder pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS — batches 1–2 of 6 graded.** For a NEW Orzhov Historic Brawl deck. Delete once the
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

(none yet)

## 3. Cross-batch observations

- Batch 2: the Ninja core is deep and CHEAP — six sneak/ninjutsu costs of 1–2 mana (Leonardo,
  Cutting Edge {W}; Splinter, Hamato Yoshi {B}; Swarm Saboteur {B}; Dokuchi Silencer {1}{B}; Last
  Ronin's Technique {1}{W}; Karai's Technique {W}{B}). Menace is the main evasion (Splinter ×2,
  Super Shredder, Killian, Syr Vondam, Ninja Teen level 2). Two half-life sources (commander at 5
  Ninjas; Shredder, Shadow Master alone).

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

## 5. Consolidated plan (live)

(after batch 6)
