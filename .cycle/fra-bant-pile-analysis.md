# Reality Fracture Bant pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS (2026-10-03). Deck 1 LANDED as `decks/80-bloom-council` (owner chose option 1: Vivien Reid cut, Garruk kept; Loyal Tutor → Germinate Recruits, Starfield Shepherd back, Astelli Reclaimer cut after the re-read). Deck 2 (UW vs UG Jace, and its six fills) is still the owner's call.** Delete once the deck(s) are drafted and the findings are
folded into their `#: notes:` blocks. A scratchpad, not a source of truth — decks/ are.

**Source list:** 73 cards (mostly FRA), pasted 2026-10-03; the user asked whether to build it as
3-colour, 2-colour or 1-colour. No target deck; this is new-deck material. 9 of the 73 already sit
in roster decks (Ajani ×2, Liliana the Faultless, Deserted Beach, Overgrown Farmland, Exemplar of
Light, Exalted Sunborn, Starfield Shepherd, Michelangelo, Rinoa) — decks share the collection, so
that does not exclude them. **Ownership:** almost none of the FRA cards are in card-library.csv
yet; they need an `/ingest` from an Arena export before `check` / `wildcards` read them as owned.

Scratch drafts measured with the read-only `deck.py` commands (paths, not deck files):
`A` (GW, from the pile), `A2` (GW + owned additions), `B` (Bant 3-colour), `C` (UW Jace, short).

## 1. The decision framework

1. **The deck's real engine is LIFEGAIN ↔ LOYALTY, and it is two-way.** Way of the Mentor and
   Ajani Resolute turn each lifegain event into loyalty; Way of the Paradox turns each loyalty
   activation into 1 life (which Mentor then turns back into loyalty on EVERY planeswalker).
   Liliana the Faultless gains life when a planeswalker enters. The number that decides a card
   is **how many lifegain events or loyalty activations it adds per turn**, not its body.
2. **Empower Jace is card advantage the role model cannot see** (G-67 / K-12 shape). The Jace
   token's "−3: Draw a card" lives in reminder text, which `classify_roles` strips — so
   Way of the Mentor, Repurposed Enforcer, Jace's Machinations and Tam's Resistance score no
   card-advantage role. Treat empower ≥3 as roughly one card. The `N unclassified` remainders
   in every `tier` line here are mostly this.
3. **Castability from the printed cost (G-58), and double pips decide the colour count.** The
   pile's duals are five taplands (two "untapped if you control a planeswalker" Annexes, two
   "untapped with two other lands", one GU Annex). Three colours with UU/WW/GG costs on that
   base is the question; `consistency` answers it (§3).
4. **Legendary "Way of" enchantments are singletons and stack** — each grants all your
   planeswalkers (Jace token included) a new loyalty ability. More Ways = more ways to spend the
   loyalty rule 1 generates.
5. **A token doubler doubles the engine's output** — Elspeth, Storm Slayer and Exalted Sunborn
   double Pridemates, Cadets, Beasts, Kithkin and Germinate's tokens. Whether a doubled
   EMPOWER makes two Jace tokens is unverified (the token is not printed legendary); do not
   argue from it.
6. **Interaction floor:** the measurable A floor needs interaction ≥7 (midrange). The pile alone
   gives GW 5 classified; owned removal-planeswalkers (Elspeth −3, Vivien −3) count twice here.

## 2. Standing error list

- **Vindictive Triumph is `{W}{B}{B}`** — not castable in Bant (identity WB, cost confirms). Out.
- **Tam, the Possibility's activated ability costs `{W}{U}{B}{R}{G}`** — inert in Bant. It is a
  2/4 planeswalker cost reducer only; `card_colors` shows WUBRG identity for that reason.
- **Fblthp, Knows the Way** has domain power — 2 in a GW deck. It is a basic-land tutor, not a body.
- **Roiling Canopy** needs five OTHER Forests for its trigger and enters tapped — not in a two-colour 9-Forest deck.
- **Hexhaven Invigorator is `{G}{G}{G}{G}`** — uncastable on curve outside mono-G.
- **Return to the Light Realms** is 9 mana; no ramp in this pile reaches it.
- **Countersculpt costs `{U}{U}` plus behold-a-Jace or {1}** — a counterspell, but a UU 2-drop.
- **Germinate Recruits counts life gained THIS turn** — needs a same-turn lifegain burst; it is an instant, so it can wait for one.

## 3. Cross-batch observations — the colour answer

| Draft | Colours | Floor | Interaction | Card-adv | Cards < 90% on curve | Notes |
|---|---|---|---|---|---|---|
| A  | GW (pile only) | B | 5 (+6?) | 3 (+6?) | 20 | WW 3-drops at 63% on 13 W |
| A2 | GW + owned PWs/removal | **A** | 9 (+5?) | 3 (+5?) | 23 (most 80–89%) | 15 W / 11 G; GG 5-drops at 64% |
| B  | WUG Bant | A | 7 (+6?) | 6 (+6?) | **33** | UU/WW/GG on 9–11 sources, 5 taplands |
| C  | WU Jace (54 cards) | A | 8 (+5?) | 6 (+5?) | 15 | short 6 spells; low board power 29 |

- **3-colour (Bant): no.** Every card is fine; the MANA is not. 33 of 36 spells are under 90%,
  the double-pip planeswalkers land at 41–53%, and the five duals all enter tapped. It would need
  ~10 more untapped duals (crafts) and to shed the double-pip cards, which are the best ones.
- **1-colour: no.** Mono-W has 23 castable cards in the pile (+3 G/W hybrids) — short ~10, and it
  loses Way of the Paradox (the other half of rule 1) and every green payoff.
- **2-colour: yes — and the pile is TWO decks.** The white/green cards and the blue cards each
  form a complete two-colour deck on their own engine, sharing the white empower cards (the
  collection is shared, so the same copies can sit in both).
  - **GW Lifegain Superfriends** (A2) — rule 1's loop.
  - **UW Jace** (C) — empower Jace toward Jace, Reality Sculptor's 25-loyalty mill-out, with
    Denzilore Fatehold turning every Jace-token surveil into +1/+1 counters.
- `deck.py similar`: A shares ≤3 nonland cards with any roster deck (closest by theme is deck 46
  Lightwing at 85%, 1 shared card) — a new deck, not a duplicate.

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out. Columns: GW deck / UW deck.

### Batch 1 (cards 1–25)

| Card | GW | UW | Note |
|---|---|---|---|
| Ajani Resolute | ★★★ | ★ | rule 1 core: lifegain → loyalty; 2-mana walker |
| Repurposed Enforcer | ★ | ★★ | empower X on attack; better where the Jace token is the plan |
| Loyal Tutor | ★ | ★ | 1-mana walker tutor (to top) |
| Liliana the Faultless | ★★ | ★ | PW/creature enters → life; hexproof outlet |
| Ajani, Caller of the Pride | ★★ | ◇ | WW 3; +1 counters, −3 double strike |
| Ajani, Outland Chaperone | ★★ | ◇ | WW 3; Kithkin tokens (doubled by Elspeth), −2 removal |
| Way of the Mentor | ★★★ | ★★ | rule 1 core: lifegain → loyalty on EVERY walker; empower 5 |
| Way of the Healer | ★★ | ★★ | every walker gains −2: Cadet + surveil |
| Vindictive Triumph | ✗ | ✗ | {W}{B}{B} — off-colour |
| Your Fate Ends Here | ★ | ★ | MV≥3 removal + surveil |
| Gideon's Memorial | ★ | ★ | tokens +1/+0 vigilance; walker mana; 4-dmg discard mode |
| Chandra, Chill of Compliance | — | ★★ | UU 3; card selection + stun removal |
| Jace's Machinations | — | ★★★ | empower 8 at instant speed |
| Way of the Cryomancer | — | ★ | walkers copy an instant/sorcery |
| The Theorist, Jace Beleren | — | ★★★ | draws every opponent draw step |
| Jace, Reality Sculptor | — | ★★ | the 25-loyalty win condition; +1 scales with Islands |
| Fblthp, Impossibly Lost | — | ◇ | draw 2 on combat damage; low-board deck |
| Countersculpt | — | ★ | UU counter + empower 1 |
| Perfected Theory | — | ◇ | combat trick |
| Guiding Hydra | ★★ | — | X-flexible counter spreader; with Yoshimaru/Michelangelo every counter is +1 |
| Return to the Light Realms | ✗ | ✗ | 9 mana |
| Blossom-Blessed Angel | ★ | — | flier + prepared Seed Suture (life + counter) |
| Yuriko, Blade of the Mighty | △ | — | attack-alone double strike; this deck goes wide |
| Koth of the Homestead | ★ | — | landfall lifegain every turn |
| Germinate Recruits | ◇ | — | needs same-turn lifegain |

### Batch 2 (cards 26–50)

| Card | GW | UW | Note |
|---|---|---|---|
| Rescue Girl, First Responder | ◇ | ★ | re-buys a Way (another empower 5) or resets a walker |
| Yoshimaru, Beloved Companion | ★★ | — | +1 counter on every counter placement |
| Unflinching Hortimancer | ★ | ◇ | 2-drop lifegain payoff with ward |
| Inspired Tethermage | ★★ | — | loyalty counters → +1/+1; empower outlet |
| Compel Brutality | ★ | — | instant; walker-loyalty fight mode |
| Garruk, Curse Breaker | ★★ | — | GG 5; Beasts + draw on power-4 entries |
| Way of the Wildspeaker | ★★ | — | walkers get −4: 4/4 Beast; empower 7 |
| Avatar of Burgeoning Echoes | — | ◇ | GU — only in a UG build |
| Kiora of Salt and Sand | — | ◇ | GU — only in a UG build |
| Mind Meanderer | — | ◇ | {3}{G}{U}{U} — UG only |
| Way of the Paradox | ★★★ | — | rule 1 core: loyalty → life; extra land |
| Samut, Tyrant of Naktamun | — | ◇ | split second on your spells |
| Lyra, Tolarian Archangel | — | ★ | Angels on 3+ draw turns |
| Plan for All Outcomes | — | ★★ | removal + empower each turn |
| Sphinx of False Conclusions | — | ★ | flash flier that returns as a copy |
| Traxos, Academy Guardian | — | ◇ | cheap flier after a noncreature spell |
| Way of the Mind Sculptor | — | ★★ | draw on every −2+ activation |
| Ruric Thar, Biomagus | — | ◇ | 6-drop |
| Greenhouse Propagator | ★★ | — | lifegain per creature + mana |
| Loot, the Nexus | △ | — | needs varied powers |
| Hexhaven Invigorator | ✗ | — | GGGG |
| Titanbones, Towering Heart | ★ | — | +2 counters per lifegain |
| Jiang Yanggu, Never Alone | △ | — | |
| Edgar, Moonlit Sovereign | △ | — | anti-synergy: wants you to cast nothing |
| Fblthp, Knows the Way | ✗ | — | domain 2 in GW |

### Batch 3 (cards 51–73)

| Card | GW | UW | Note |
|---|---|---|---|
| Roiling Canopy | ✗ | — | needs 5 other Forests |
| Denzilore Fatehold | — | ★★★ | every Jace-token surveil = counters on the team |
| Deserted Beach | — | ★★ | WU dual |
| Fatehold Annex | — | ★★ | WU, untapped with a walker |
| Solarium Sentry | ◇ | — | lifegain depends on the opponent |
| Emergency Phytomedic | ★★ | — | 1-drop, two Seed Sutures (2 lifegain + 2 counters) |
| Vigorbloom Charm | ★★ | — | protection / draw+3 life / fight |
| Vigorbloom Vanguard | ★ | — | prepared Seed Suture; vigilance |
| Kwia Vigorbloom | ★★ | — | lifelink flier; Lotus per lifegain turn |
| Bloombrute | ★★ | — | draw per lifegain turn |
| Overgrown Farmland | ★★ | — | GW dual |
| Vigorbloom Annex | ★★ | — | GW, untapped with a walker |
| Tam, the Possibility | — | — | GU; ability inert in Bant (error list) |
| Transformative Commons | — | — | GU land |
| Lyra, Archangel of Dawn | ★ | — | angel lord on lifegain |
| Exemplar of Light | ★★ | — | grows + draws on lifegain |
| Astelli Reclaimer | ★ | — | returns a dead walker/Way (warp → MV ≤3) |
| Exalted Sunborn | ★★ | ★ | token doubler, warp 2 |
| Starfield Shepherd | ◇ | — | tutors a 1-drop |
| Michelangelo, Weirdness to 11 | ★★ | — | counter doubler |
| Rinoa Heartilly | △ | — | 5-drop |
| Fatehold Charm | — | ★★ | modal; draw + empower 2 |
| Tam's Resistance | ★ | ★ | {1}{G/U}: counter + empower 4 |

## 5. Consolidated plan (live)

### Deck 1 — GW Lifegain Superfriends — LANDED as deck 80 (draft A2 was 61 cards; the final list is A3)

**Re-read finding (2026-10-03):** Liliana the Faultless and Greenhouse Propagator gain life for EACH creature or token that enters, so every token is two life gains, which Way of the Mentor turns into two loyalty on every walker. That raised Germinate Recruits, Starfield Shepherd (a warp-cost tutor for Liliana) and the token makers. `screen` afterwards rated Solarium Sentry KEY; it went in for Tam's Resistance on 2026-10-03 (owner's call).

**Adds from outside the pile (all OWNED):** Elspeth, Storm Slayer (token doubler + walker +
removal), Vivien Reid (selection + removal), Erode, Bite Down. **From the pile, cut from draft A:**
Rinoa, Solarium Sentry, Germinate Recruits, Starfield Shepherd.

Mana: 13 Plains, 9 Forest, Overgrown Farmland, Vigorbloom Annex (W 15 / G 11).
**Open tuning call:** Garruk and Vivien are GG 5-drops at 64% on 11 G sources, while the WW
3-drop Ajanis read 71% on 15 W. Going 12/10 trades one for the other; cutting one GG walker
is the cleaner fix.

**PROTECT** (ranked low by `cuts` for reasons it cannot see): Way of the Mentor and Way of the
Paradox (the two halves of rule 1 — neither scores a role worth its slot), Ajani Resolute,
Yoshimaru and Michelangelo (doublers: their value is the rest of the deck), and Liliana the Faultless.

### Deck 2 — UW Jace (draft C: floor A at 54 cards)

Core from the pile: both Jaces, Chandra, Jace's Machinations, Way of the Cryomancer, Way of the
Mind Sculptor, Plan for All Outcomes, Countersculpt, Fatehold Charm, Denzilore Fatehold, Lyra,
Tolarian Archangel, Sphinx of False Conclusions, Repurposed Enforcer, Rescue Girl, plus the shared
white empower cards and Elspeth/Erode. **Six slots to fill**, best from the Standard empower pool
outside the pile: Theorist's Proxy, Mindseeker Oculus, Protege's Awakening, Campus Crier,
Academic Ascent, and Theorist's Sanctum lands. UU costs on 13 U sources (Countersculpt 63%,
Chandra 70%) argue for more Islands than Plains.

**2026-10-03 cross-pile measurement (fra-rgu-pile-analysis.md §3):** mono-U beat every pair on the same blue core (0 cards under 90% on curve against 12–19 for UR/UG/UW/UB, all floor A), so deck 2 may be better as mono-blue than UW or UG.

### Not used in either deck

Vindictive Triumph, Return to the Light Realms, Hexhaven Invigorator, Roiling Canopy, Fblthp
Knows the Way, Edgar, Jiang Yanggu, Loot, Yuriko (rule-specific reasons in §2/§4). The GU cards
(Avatar, Kiora, Mind Meanderer, Tam, Transformative Commons) want a UG Jace-landfall build — a
third option only if the user prefers green-blue to white-blue for deck 2.
