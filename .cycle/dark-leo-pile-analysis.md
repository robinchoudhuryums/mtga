# Dark Leo & Shredder pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS — batch 1 of 6 graded.** For a NEW Orzhov Historic Brawl deck. Delete once the
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

## 5. Consolidated plan (live)

(after batch 6)
