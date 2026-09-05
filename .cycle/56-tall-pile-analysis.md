# Deck 56 tall pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into the
deck files' `#: notes:` blocks. A scratchpad, not a source of truth — decks/ are.

**Source list:** user-supplied in batches of ~10–20 (scratchpad `pile-56-batch*.txt`).
Batch 1: 20 cards, 0 already in 56/56a (13 sit in OTHER decks — irrelevant, decks share
the collection). Per the user: ignore rotation and craft cost for this pass; evaluate as a
continuous whole; group into plans / flag a variant if one surfaces; note 56a fits.

**Primary deck:** 56 One Fell Swoop (RW, aggro, ultra-tall one-swing).
**Secondary:** 56a Executioner's Song (RG, midrange, permanent-counter tall).

**Pending from the pre-pile `/tune-deck 56`** (NOT applied — the user wants the pile read
first): cut 2 Twin Blades / 1 Reckless Ransacking / 1 Rabid Gnaw → add Enter the Avatar
State, Restoration Magic, Spectacular Tactics, Valorous Stance. Measured protection 3→7,
interaction 7→8, floor A→A. Re-rank against the pile in §5.

## 1. The decision framework

Live vector, 56 (2026-09-05): interaction 7 · card-adv 2 (0 repeatable) · protection 3 ·
avg MV 2.42 · clock 6/7 · floor A · shape TALL 8 / wide 1 · 15 creature copies, 24 lands ·
W 11 sources / R 18 · strict pips W 8 / R 35 · `double strike` tag on 8 copies (+ Mai = 9
sources) · `hexproof` 1 · `haste` 7 · `evasion` 7 · `trample` 5.
Live vector, 56a: interaction 4 · card-adv 2 · floor C (letter B) · avg MV 2.86 ·
TALL 11 · 21 creature copies · counters 10 enablers / 0 payoff.

Rules — cite by number in every verdict:

- **F1. The deciding number is DAMAGE THAT CONNECTS in one combat**, not power on the
  board. Delivered = boost × multiplier × (gets through?). Grade each card by which factor
  it moves. A linear pump (+3) is the weakest factor; a multiplier (Bulk Up doubles) is
  the strongest; EVASION is the one the deck is thinnest on — its "evasive 10" is mostly
  conditional trample, and the only unblockable grant is Speed's haste rider.
- **F2. Double strike DOES NOT STACK and the deck already has 9 sources.** A new
  double-strike grant is worth ~0 in 56 (the Vindicators carry it printed). Flying /
  can't-be-blocked / menace / trample are the multipliers that still have headroom.
- **F3. Kill turn is T4–T5 (curve 2.42, aggro plan).** A card at MV 4+ must BE the kill
  turn (haste + evasion + size on one card) or it is a turn the deck does not have. A
  card at MV ≤2 that is a spell also feeds F4.
- **F4. Every noncreature spell is +3/+0 on Crackling Cyclops, +1/+1 on Mai, and a
  valiant counter on Seedglaive Mentor if it targets him.** 21 of 36 nonland cards are
  noncreature now. A creature ADD dilutes this; a cheap instant feeds it. Count the
  noncreature ratio after any package.
- **F5. Power on the board is ALSO reach and removal** — Self-Destruct ("any other
  target"), Rabid Gnaw, The Last Agni Kai, Go Ninja Go, War Machine all read the tall
  body's power. So a pump is worth more than its printed number: it is face damage at
  instant speed through Self-Destruct. READ THE TARGET LINE of every damage effect —
  "any target" is reach, "target creature" is removal, and they are different cards
  (standing error E1).
- **F6. The threat is ONE body, so grade a card against the four ways the deck loses:**
  (a) targeted removal on the body → hexproof > indestructible (exile/bounce/−X/−X);
  (b) chump block → evasion or Self-Destruct; (c) sweeper/edict → indestructible /
  blink / a second body held back; (d) a whiffed swing → card advantage, which is 2
  with 0 repeatable. Protection is 3 today (7 under the pending tune).
- **F7. Castability from the PRINTED cost (G-58).** RW, W secondary: `{R}{W}` is 78%
  on T2, `{W}{W}` is not a cost this manabase pays on curve. Green-identity cards route
  to 56a only; white to 56 only; red to both.
- **F8. Molten Man = +1/+1 per MOUNTAIN (13 basics + his own fetch).** Any land package
  that swaps basics for nonbasics shrinks the protected signature body; anything that
  adds Mountain-typed lands or fetches grows him. State the Mountain count before any
  manabase verdict.
- **F9. 56a pays differently** — midrange curve, RG, green COMPOUNDS permanent counters
  on big bodies and protects with hexproof. A one-turn multiplier or a haste enabler is
  a 56 card; a permanent grower, a counters payoff (56a has 10 enablers / 0 payoff) or a
  green-identity card is a 56a card. Its interaction is 4, floor C — an RG interaction
  piece is worth more there than in 56.
- **F10. Structurally invisible to every tool here:** can't-be-blocked and menace
  grants (no tag), double-strike non-stacking, the ANY-target/creature-only split, the
  Mountain count, exhaust/once-per-game cadence, "Ball Lightning" hasty self-sacrifice
  bodies (a body that dies at end of turn is a SPELL here — grade it as one under F4/F5).

## 2. Standing error list

- **E1.** Self-Destruct grouped with Rabid Gnaw / Agni Kai as "power-as-removal". It
  targets "any OTHER target" — the player — so it is REACH and a win condition in a tall
  deck. Read the target line, every time.
- **E2.** Double-strike grants graded as if they stack. They do not (F2).
- **E3.** The Vision's / Cloud's indestructible read as protection for the tall body;
  each protects only ITSELF.
- **E4.** Aziza rejected for "competing with Yue for untapped creatures"; redundancy
  argument wins (P(both) ≈ 4% vs P(either) ≈ 36%). Do not reject a second copy of an
  effect on the grounds that the first copy exists.
- **E5.** A type-line scan for `Legendary Creature` missed War Machine (`Legendary
  ARTIFACT Creature`), under-counting Mjölnir's worthy carriers 3 → 4. Substring tests on
  a type line need the word order checked (G-63's column-vs-face shape one field over).
- **E6.** Gingerbrute was graded above Swiftblade Vindicator as a bearer on "unblockable
  beats double strike". Both are 1/1s, and Vindicator's double strike + TRAMPLE together
  is near-unblockable ×2 (first-strike damage kills the chump, everything else tramples,
  then the regular hit is all excess). F2 says a NEW double-strike grant is worth 0; it
  does not say the printed pair on a bearer is. Gingerbrute drops to ◇.
- **E7 (user correction).** Brambleback Brute's "remove a counter" is ANY counter, so a
  +1/+1 counter reloads the can't-block charge and leaves a 4/5. Graded it as two charges
  without counting the deck's counter sources ONTO OTHER creatures: 56 has none today
  (Seedglaive / Red Hulk / Mai all self-counter), 56a has Halana and Alena every combat.
  State the count, then decide (G-61) — the count differs between the two decks.
- **E8 (user correction).** Terror of the Peaks was graded on "56's bodies enter at 0–3":
  Molten Man's static applies the moment he is on the battlefield, so he ENTERS as N/N
  for N Mountains; Scalestorm's 3/1 tokens are a repeatable enter; Red Hulk enters at 6;
  Go Ninja Go re-enters the body. A printed P/T is not what a creature enters as.
- **E9.** Batch 3 filed Fleeting Flight / Lightfoot Technique's +1/+1 counter as a minor
  rider. In this deck a counter is ALSO a Brute reload (E7) and a Bulwark Ox key
  ("creatures with counters gain hexproof and indestructible") — a counter is a resource
  two other cards spend, not a stat.

## 3. Cross-batch observations

- **O1. Batch 1 is two piles wearing one list.** Nine of 20 cards are the EVASION axis
  F1 names as thinnest (Rogue's Passage, Secret Tunnel, Key to the Side-Door, Ty Lee,
  Hazoret, Gingerbrute, Roadrunner, X-ATM092, Speed's rider via haste), and eight are a
  **WARP / Ball Lightning temporary-body plan** (Ball Lightning, Nova Hellkite, Red Tiger
  Mechan, Memorial Team Leader, Tannuk, Full Bore's rider, Charred Foyer // Warped Space).
  The first pile tunes 56 in place. The second is a DIFFERENT deck — see O3.
- **O2. Speed's rider is HASTE-gated** ("target creature WITH HASTE can't be blocked
  except by creatures with haste"). 56's haste sources today: Speed, Seedglaive Mentor,
  Haste Magic ×2. Tannuk ("other creatures you control have haste") or a natively hasty
  bearer turns the rider on for every body — the one card in the deck that grants
  unblockable is half-off until the deck is hasty. Nothing tags this (F10).
- **O3. VARIANT SIGNAL — "Ball Lightning" Boros/mono-R burst (working id 56b).** The
  warp cluster answers F6(c) STRUCTURALLY: a body that leaves at the end step cannot be
  swept or edicted on their turn, and Self-Destruct's "X damage to itself" is FREE on a
  body that is exiling itself anyway (G-41 cost-as-upside — the deck's own notes call
  that self-damage the card's drawback). Tannuk gives Molten Man / Cyclops / Red Hulk
  warp; Warped Space recasts any warp body from exile for {0} once a turn; Charred Foyer
  is repeatable card advantage (56 has 0 repeatable). The cost: warp Molten Man
  sacrifices a LAND on leaving (G-42 — his leave trigger), and the plan trades 56's
  protection layer for tempo. Decide at the end, not now; keep tallying which batch-N
  cards join it.
- **O4. Tooling hole (Stage 4, batch-fix at the end):** `classify_roles` returns
  NO role for Return the Favor — "change the target of target spell" is a redirect
  (protection-class, F6a) and "copy target instant" is a multiplier. G-67 whitelist
  miss; record, keep reading.
- **O5. Firebending X on a pumped body is a mid-combat mana engine** ("whenever this
  creature attacks, add X {R}" where X = its power): pump Student before attackers, get
  X red mana, cast the rest of the hand on the same swing. Pairs with The Last Agni Kai's
  persisting red mana. No tool scores mana-from-power.

- **O6. Batch 2 is an EQUIPMENT pile, and 9 of its 20 cards grant double strike** (Hard-Won
  Jitte, Fireshrieker, Rover Blades, Genji Glove, Leyline Axe, Dáin, Iron Hills Blacksmith,
  Blacksmith's Talent L3, Practiced Offense from batch 1). F2 prices every one at ~0 for 56.
  What survives is the cards that do something ELSE: Mjölnir (doubles DAMAGE — a third
  multiplier axis distinct from Bulk Up's power-doubling and DS's two-hit), Genji Glove
  (an extra COMBAT), Swiftfoot Boots (permanent hexproof + haste), Blacksmith's Talent L2
  (free attach every combat — the equip-cost answer the user's Katana note points at).
- **O7. Mjölnir has NO generic equip** — only "Equip worthy {1}", legendary non-Villain
  R/W. In 56 the worthy bodies are Mai, Speed ×2 and War Machine (4 copies — the first
  scan matched `Legendary Creature` and missed War Machine's `Legendary Artifact
  Creature` line, E5); Molten Man and Red Hulk are VILLAINS and can never carry it (G-61: the count decides, and the two signature
  bodies are outside it). In 56a worthy = 8 copies (Wolverine, Scarlet Spider, Mai,
  Halana and Alena, Ruby ×2, Speed ×2) — Mjölnir is a 56a card first.
- **O8. An "Equipment-tall" plan is real but would collide with deck 38 Armory (voltron)
  and 74 Iron Hills Forge (Boros Dwarf/Equipment triggers, which already runs Thorin,
  Orcrist, Leyline Axe, Stalwart, Blacksmith)** — run `similar` against both before any
  56c is drafted. The better use is to BORROW the two pieces that are not double strike
  (Swiftfoot Boots, and Mjölnir if the worthy count is accepted) into 56 rather than
  build a third equipment deck.
- **O9. Self-Destruct on a STOLEN creature** (Unexpected Request's Threaten): their
  creature deals its power to their face and the reflected damage kills it. A removal +
  reach line the deck's own notes never list. Sorcery-speed setup, but it is a G-41 shape
  in reverse — the self-damage is upside when the body is theirs.
- **O10. Haste keeps turning up as the hidden enabler** (O2): Impolite Entrance,
  Swiftfoot Boots, Samurai's Katana, Blacksmith's Talent L3, Quaketusk Boar all grant or
  carry it, and every one of them turns Speed's unblockable rider on. The deck's four
  haste sources are the count that decides whether Speed is a 2/2 or an evasion engine.

- **O11. Batch 3 is the 56b PAYLOAD, and the variant is now a real deck.** Batch 1 gave
  the engine (Tannuk, Warped Space, Speed's rider, Self-Destruct-for-free); batch 3 gives
  the bodies: Bygone Colossus (WARP {3}: a 9/9 for three mana), Doc Ock's Tentacles
  (auto-attaches +4/+4 to any MV ≥5 creature that ENTERS — a warped Colossus is MV 9, a
  warped Nova Hellkite MV 5), Terror of the Peaks (each entering body deals its power to
  any target — a warped Colossus is 9 to the face on entry), and Iron Giant ({7} 6/6
  trample) which Tannuk warps for {2}{R} with haste. Five warp/hasty bodies + two
  recasts + three payoffs across three batches. Decide at the end as planned, but the
  count now clears "enough bodies for a 60" (O3's open question).
- **O12. Pain for All is the reach engine the tall body was missing.** ETB: enchanted
  creature deals its power to ANY OTHER TARGET (E1 ✓ reach); then every point of damage
  dealt TO it hits each opponent. Self-Destruct on the enchanted body = X face + X self →
  X face again: 2X for `{1}{R}`. Chump-blocking stops saving them (the blocker's damage
  goes face). An Aura on the one body is the 2-for-1 risk, but the ETB has paid before
  removal resolves. The user's star is right.
- **O13. `lose all abilities` is a G-42 card here.** Final Showdown's first mode and
  Curious Colossus strip YOUR body's granted keywords and Molten Man's Mountain scaling
  (he is a printed 0/0) — in a deck whose entire plan is granted abilities, the symmetric
  mode is a self-wipe. Grade only the indestructible mode.
- **O14. Crackling Cyclops is a printed 0/4** — F4 is not an overlay on him, it is the
  whole card: three spells make him a 9/4. Every creature ADD that displaces a spell
  shrinks the Cyclops; every cantrip (Impolite Entrance, Haste Magic's impulse) is +3.
- **O15. Repeatable flying — Bre of Clan Stoutarm.** `{1}{W},{T}`: ANOTHER creature gains
  flying + lifelink each turn, and a lifelinked tall swing (gain 20) free-casts the next
  nonland card off the top at end step. The one MV-4 creature across three batches whose
  turn pays for itself (F3): T5 activate + Bulk Up is four mana for a doubled evasive
  lifelink swing. Nothing in 56 grants flying repeatably; Key to the Side-Door is the
  unblockable equivalent at a better rate but with no draw.

- **O16. AN INDESTRUCTIBLE BODY MAKES SELF-DESTRUCT REPEATABLE.** Self-Destruct deals X
  to the body too; an indestructible one (The Sentry, Hazoret) survives it, so the deck's
  finisher stops costing the body — and with Pain for All on that body the reflected X is
  a second X to the face. The Sentry is therefore F5 + F6(a/c) in one card: 5/5 flying
  vigilance indestructible for `{3}{W}`, and the deck's reach spells stop being one-shots.
  Its cost is the Void: a 5/5 flying indestructible token that attacks YOU every combat
  (vigilance lets Sentry block it and still swing, but that is the whole tall body on
  defence). Say the 5-a-turn out loud before taking it.
- **O17. Batch 4 is the PROTECTION pile — ten cards on F6 — and they split by which
  half of F6 they answer.** Hexproof (targeted removal): Restoration Magic, Bofur's
  Concerted Care, Spider-Man's sac, Bulwark Ox's sac. Indestructible only (destroy /
  damage, sweepers): Lightfoot Technique, Reroute Systems, Divine Resilience, Zack Fair,
  Crumb and Get It, Earth Kingdom Protectors. With The Sentry as the body the FIRST half
  is what the deck needs (the body already survives the second), which re-orders the
  list: Boots, Avatar State, Restoration Magic/Bofur, Spider-Man; the indestructible-only
  cards fall out. Without Sentry, Lightfoot Technique is the best of the second half
  (flying + a counter, E9).
- **O18. Crumb and Get It's indestructible is bought by GIVING THEM 3 LIFE** (the Food).
  In a deck that computes exact lethal, that is a G-42 cost on a protection spell.
- **O19. 56b keeps growing from the Giants via Tannuk's warp** (`{2}{R}` for any red
  creature card in hand): Hill Gigas 5/4 trample haste, Zealous Lorecaster 4/4 + regrowth
  Bulk Up (and it re-exiles, so it can be recast from exile to regrowth AGAIN), Stone-Giant
  7/7 + a Wall token to sacrifice for 4 damage. Tannuk is the card that turns the Giants
  pile from ✗ into a plan.

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

### Batch 1 (20 cards)

| Card | 56 | 56a | Note (framework rule) |
|---|---|---|---|
| Return the Favor | ★★★ | ★★ | `{R}{R}`+`{1}`/mode. Copy Bulk Up = ×4 power (F1 multiplier); REDIRECT their removal onto their own creature = protection that also kills (F6a). Instant, feeds F4. Best card in the batch. `{R}{R}` is fine on 18 R. Roleless to the classifier (O4). |
| Nova Hellkite | ★★ | ★ | Warp `{2}{R}`: 4/5 **flying haste** on T3 — the only FLYING bearer in the batch (F1 evasion) and it is on curve (F3). Recast from exile later. Self-Destruct on it is free the turn it warps (O3). Hardcast 5 is the fallback, not the plan. |
| Gingerbrute | ★★ | ★ | `{1}` haste; `{1}`: can't be blocked except by haste. The cheapest UNBLOCKABLE bearer that exists (F1). 1/1 base is the cost — Bulk Up doubles power, so the base matters; Celestial Armor / Twin Blades / Reckless Ransacking make the base first. A bearer, not a threat. |
| Key to the Side-Door | ★★ | ★★ | `{1}` artifact, `{2},{T}`: target creature can't be blocked — REPEATABLE, half the price of Rogue's Passage, and a noncreature spell (F4). Draw-two mode is live off a duplicate Molten Man / Speed (2 each) — minor. The user's ⭐ note is right. |
| Rogue's Passage | ★★ | ★★ | A LAND that grants unblockable for `{4}` — zero spell slots. Costs a colour source (`{C}`) in a 24-land deck with W at 11 (F7) and is NOT a Mountain (F8: −1/−1 on Molten Man if it replaces one). Replace a tapland, not a basic. |
| Firebending Student | ★ | ★ | Prowess + Firebending X (O5). A 2-drop bearer that pays for the kill turn's tricks. 1/2 base is small; the mana is the card. |
| Ty Lee, Artful Acrobat | ★ | ★ | Prowess 3/2; attack + `{1}`: target creature can't block. Against ONE blocker this is unblockable for a tall body — but it only fires when TY LEE attacks, so she is a second attacker beside the tall one. Real, not key. |
| Tannuk, Steadfast Second | ◇ | ◇ | In 56 as-is: MV 4, 3/5, no haste itself (F3) — but "other creatures have haste" turns Speed's rider on (O2) and warp on red creatures. In 56b it is the ENGINE (★★★ there). Warp Molten Man = sacrifice a land on exile (G-42). |
| Full Bore | ◇ | ◇ | `{R}` +3/+2 instant — Reckless Ransacking minus the Treasure, one mana cheaper (F4). Its trample+haste rider needs a WARP-cast creature: dead in 56 today, ★★ in 56b. |
| Hazoret, Godseeker | ◇ | ◇ | 5/3 indestructible haste for 2 is a tall body on its own, but it can't ATTACK before max speed (opponent loses life on 4 of your turns → T5 earliest), and its unblockable tap targets power ≤2 — useless on the tall body (F1). A T5 threat in a T4–5 deck. |
| Ball Lightning | ◇ | △ | `{R}{R}{R}` 6/1 trample haste, dies at end step. On its own: a 6-damage Lava Axe at sorcery speed. With Bulk Up + Self-Destruct: 12 trample + 12 face at instant speed, and the sacrifice was free (O3). The user is right that it is the PREMISE — it is the premise of 56b, not a slot in 56 (triple-R on T3 is 78%-ish and it dilutes F4). |
| Heartfire Immolator | ◇ | ◇ | Prowess 2/2; `{R}`, sac: damage equal to power to target CREATURE OR PLANESWALKER — not a player (E1 check: this is removal, not reach). A worse Rabid Gnaw that costs the body. |
| Charred Foyer // Warped Space | ◇ | △ | Front `{3}{R}` (G-02): upkeep impulse = the deck's only REPEATABLE card advantage (F6d). Back `{4}{R}{R}`: free cast-from-exile once a turn. MV 4 sorcery-speed enchantment on the kill turn (F3) — too slow for 56; the engine of 56b. |
| Thor Odinson | △ | ✗ | `{3}{R}{W}` 4/4 flying vigilance DOUBLE prowess — with two spells an 8/8 flier. But MV 5 in a T4–5 deck with 11 W (F3, F7), and it is a creature (F4). If the deck went up the curve this is the top-end; it hasn't. |
| Practiced Offense | △ | ✗ | Sorcery, white, +1/+1 counter per creature (one or two here) and double strike OR lifelink — DS is worth 0 in 56 (F2). Flashback is the only reason it is not ✗. |
| Red Tiger Mechan | △ | △ | Warp `{1}{R}` 3/3 haste — a vanilla Ball Lightning-lite for 56b; nothing for 56. |
| Resilient Roadrunner | △ | △ | Gingerbrute at three times the activation cost with a 2/2 body. Gingerbrute dominates it for this job. |
| Secret Tunnel | △ | △ | `{4},{T}`: TWO target creatures sharing a type can't be blocked — a tall deck attacks with ONE (F1) and the second target is a requirement, not a bonus. Rogue's Passage dominates it. |
| Memorial Team Leader | ✗ | ✗ | Anthem (+1/+0 to OTHERS, your turn only) is a go-wide card; warp 4/3 is the only tall use and Red Tiger Mechan does that cheaper. |
| Relentless X-ATM092 | ✗ | ✗ | MV 6 colourless, no haste (F3). "Can't be blocked except by three or more" is real evasion two turns too late. |

### Batch 2 (20 cards)

| Card | 56 | 56a | Note (framework rule) |
|---|---|---|---|
| Swiftfoot Boots | ★★★ | ★★★ | `{2}`, equip `{1}`: PERMANENT hexproof + haste. Answers F6(a) without holding mana up, turns Speed's rider on (O2/O10), and is a noncreature spell (F4). Complements Restoration Magic (which adds indestructible at instant speed for the sweeper case, F6c) rather than competing with it. Best protection card in the pile so far. |
| Impolite Entrance | ★★ | ★★ | `{R}` sorcery: trample + haste + DRAW. A cantrip that converts the tall body into an unblockable one via Speed (O2) and gives trample if not. One-shot CA on a deck at 2 (F6d). Sorcery is fine — it is a precombat card. |
| Mjölnir, Hammer of Thor | ★ | ★★★ | "Double all damage equipped creature would deal" — a THIRD multiplier axis (F1): Bulk Up ×2 power → DS ×2 hits → Mjölnir ×2 damage, and it doubles Self-Destruct's / Rabid Gnaw's / Agni Kai's damage too. ETB 4 to a creature clears a blocker. But equip WORTHY only (O7): 3 carriers in 56, none of them the big bodies; 8 in 56a including Halana and Alena. MV 4 (F3). |
| Unexpected Request | ★ | ★ | Threaten + attach an Equipment: removes their best blocker AND adds an attacker on the kill turn (F6b); Self-Destruct on the stolen body is removal + reach (O9). Sorcery, 3 mana. |
| Dragonclaw Strike | ★ | ★★ | Hybrid `{2/G}{2/U}{2/R}`: FIVE mana in RW, FOUR in RG (G-58 — the tool's "MV 6" is the printed maximum). Double P/T then fight = Bulk Up + Agni Kai in one sorcery. 56a's midrange curve and its Bulk Up #3 slot want it; 56's T4–5 clock does not pay five for a sorcery (F3). The user's 56a flag is right. |
| Quaketusk Boar | ◇ | ◇ | `{3}{R}{R}` 5/5 reach trample haste — a kill-turn body (F3) that hardcasts as a permanent. Nova Hellkite (warp `{2}{R}`, flying) does the job two mana cheaper and in the air. |
| Samurai's Katana | ◇ | ◇ | `{2}{R}`: a 3/3 trample haste body that moves onto the tall one for `{5}` — or FREE via Blacksmith's Talent L2 / Thorin / Unexpected Request. +2/+2 trample haste on the tall body is F1 + O10. The `{5}` is the whole problem in 56 as-is; the user's note is the equipment-plan case (O8). |
| Blacksmith's Talent | ◇ | ◇ | L2 (`{2}{R}`) attaches an Equipment free every combat — the engine that makes Katana / Genji Glove / Celestial Armor's equips cost 0. L1 alone is a `{R}` +1/+1 Sword; L3 is DS + haste. 8 mana across three levels: the spine of an equipment plan, a slow enchantment in 56 (F3). |
| Thorin, Mountain-king | ◇ | ◇ | ETB: attach ANY number of Equipment free, then the creature deals its power to a creature (F5 removal). MV 4 3/4 trample. Needs Equipment on the field to be more than a body; 56 has 3 and is cutting 2. |
| Genji Glove | ◇ | △ | `{5}` equip `{3}`: DS (0) + an EXTRA COMBAT PHASE — a ×2 that stacks with all three others (F1). 8 mana total, 5 with Talent L2. The equipment plan's top end; nothing for 56 at its clock (F3). |
| Super-Adaptoid | △ | △ | Power = legendaries you control (usually 1–2 here); copies keywords onto ITSELF, not the tall body. A second body, not a taller one (F1). |
| Orcrist, Goblin-cleaver | △ | △ | +2/+2 trample, Treasures on damage. Equip `{3}` — a slow Twin Blades. |
| Leyline Axe | △ | △ | +1/+1 DS trample; free-start only in the opener (~12% at one copy). DS = 0 (F2). |
| Dáin Ironfoot | △ | △ | Axe token + attack-trigger DS for equipped attackers (F2). |
| Iron Hills Stalwart | △ | △ | Thorin's common cousin at MV 5 with one attach. Thorin dominates. |
| Gilgamesh, Master-at-Arms | △ | △ | MV 6, no haste (F3); digs six for Equipment and attaches to a SAMURAI (Katana makes one). Equipment-plan top end only. |
| Iron Hills Blacksmith | △ | ✗ | `{1}{W}` 1/1 DS + Axe token. DS = 0. |
| Hard-Won Jitte | ✗ | ✗ | Pure DS equipment (F2). |
| Fireshrieker | ✗ | ✗ | Pure DS equipment (F2). |
| Rover Blades | ✗ | ✗ | DS equipment that is also a 2/2 DS vehicle; equip `{4}` (F2). |

### Batch 3 (21 cards)

| Card | 56 | 56a | Note (framework rule) |
|---|---|---|---|
| Pain for All | ★★★ | ★★★ | `{2}{R}` Aura: ETB power-to-any-target (reach), then all damage dealt to the body hits each opponent. Self-Destruct becomes 2X face (O12). Turns blockers, fights (Agni Kai), Wisecrack and Red Hulk's enrage into face damage. Sorcery-speed setup; the 2-for-1 risk is real but the ETB pays first. |
| Bygone Colossus | ★★ | ★ | WARP `{3}`: a 9/9 for three, gone at end step. No haste of its own — the count that decides it is 56's HASTE GRANTS: Haste Magic ×2 (+3/+1 → 12), Swiftfoot Boots (equip `{1}`, so T4 = warp + equip = a 9/9 hexproof haste swing), Impolite Entrance. Self-Destruct on it is a free 9 (O3); with Pain for All 18. The user's read is right, and the enabler count is what makes it ★★ rather than ★★★ in 56. ★★★ in 56b. |
| Bre of Clan Stoutarm | ★★ | ✗ | Repeatable flying + lifelink on the tall body, and a free cast off the top after a lifelink swing (O15). MV 4, `{R}{W}` (F7: 78%). The only creature in three batches that earns a turn-4 slot. |
| Enter the Avatar State | ★★★ | ✗ | Confirmed from the pre-pile pass: `{W}` hexproof + flying + first strike + lifelink. Plan A #3. |
| Giantfall | ★ | ★ | `{1}{R}` instant: your creature deals its power to theirs (Rabid Gnaw without the +1/+0 or the fight-back) OR destroy target ARTIFACT — the deck's first noncreature answer. The de-dup swap for Gnaw #2: same effect, second mode (G-46 virtual copy). |
| Wisecrack | ★ | ★ | `{2}{R}` instant: target creature deals its power to ITSELF (+2 to its controller if attacking). Removal that scales with THEIR body — kills any big blocker. On your own Pain-for-All body it is X to face. Interaction 7 → 8. |
| Brambleback Brute | ★ | ★★ | `{2}{R}` enters 2/3; `{1}{R}`, remove ANY counter: target creature can't block (sorcery). Two charges in 56 as-is, RELOADED by every +1/+1 counter put on it (E7: Lightfoot Technique, Bulwark Ox, Fleeting Flight are the adds that do); in 56a Halana and Alena reloads it every combat, and it ends as a 4/5. Revised up on the user's read. |
| Fleeting Flight | ★ | ✗ | `{W}`: permanent +1/+1 counter, flying, prevent all combat damage to it. Avatar State dominates it on the same mana except for the counter. |
| Final Showdown | ★ | ✗ | Only the `{W}`+`{1}` indestructible mode is live (O13: mode 1 strips your own body; the `{3}{W}{W}` wipe is WWW on 11 sources, F7). At 2 mana instant indestructible it ties Valorous Stance and loses to Restoration Magic. |
| Goliath Daydreamer | ★ | ◇ | `{2}{R}{R}` 4/4: your instants/sorceries exile with dream counters; on attack, cast one FREE. Bulk Up cast on T3 comes back free on every Daydreamer attack — but HE must attack, beside the tall body. RR at MV 4. Already 57's card. |
| Doc Ock's Tentacles | △ | △ | `{1}`, equip `{5}`: +4/+4, auto-attaches when a MV ≥5 creature ENTERS. In 56 that is Red Hulk alone (Nova Hellkite if added). ★★ in 56b, where a warped Colossus enters at MV 9 (O11). |
| Terror of the Peaks | ★ | ★ | MV 5 5/4 flier, targeting tax (soft protection); each entering creature deals ITS power to any target. Revised up (E8): Molten Man ENTERS as N/N for N Mountains, Scalestorm's 3/1 tokens are 3 a turn, Red Hulk enters at 6, Go Ninja Go re-enters the body. A 56b payoff too (Colossus: 9). MV 5 with no haste is still F3's cost. |
| Combustion Man | ◇ | ◇ | MV 5; on attack, destroy target PERMANENT unless they take his power — the deck's only noncreature-permanent answer, and it scales with pumps. His attack, not the tall body's; F3. |
| Fated Firepower | ◇ | ◇ | `{X}{R}{R}{R}` flash: every damage source you control deals +X. Triple R (F7) and X=2 costs five for +2 per hit. A wide-burn card. |
| Burdened Stoneback | ◇ | ✗ | `{1}{W}` enters 2/2; two SORCERY-speed uses of indestructible for `{1}{W}`. Pre-combat protection only — cannot answer removal in response. |
| Hovel Hurler | ◇ | ◇ | MV 5, two uses of +1/+0 flying (sorcery). Bre does it repeatably at MV 4. |
| Giant Cindermaw | △ | △ | 4/3 trample for 3; "players can't gain life" fights Bre / Avatar State lifelink (G-42). |
| Giant's Boulder | △ | △ | Scry 2 + a `{1}`-to-use any-colour rock; `{7}` destroy a permanent. Fixing for W at a cost. |
| Slumbering Walker | ✗ | ✗ | MV 5 WW reanimating power ≤2 — a different deck. |
| Curious Colossus | ✗ | ✗ | MV 7 WW (F3/F7); one-sided shrink. |
| Iron Giant | ✗ | ✗ | `{7}` 6/6 with no haste — ✗ in 56; ◇ in 56b where Tannuk warps it for `{2}{R}` (O11). |

### Batch 4 (20 cards)

| Card | 56 | 56a | Note (framework rule) |
|---|---|---|---|
| The Sentry, Golden Guardian | ★★★ | ✗ | `{3}{W}` 5/5 flying vigilance INDESTRUCTIBLE. An evasive tall body that survives its own Self-Destruct (O16) and every destroy/damage answer; with Pain for All every Self-Destruct is 2X. The Void (a 5/5 flying indestructible attacker for THEM, every combat) is a real 5-a-turn tax that vigilance only half-cancels. Single W at MV 4: 86% on curve. The user's star is right, with the Void named. |
| Lightfoot Technique | ★★ | ✗ | `{1}{W}` instant: permanent +1/+1 counter, flying, indestructible. Evasion + protection + a counter that reloads Brute / keys Bulwark Ox (E9). The best indestructible-half card (O17) and the only one that also gives flying. |
| Spectacular Spider-Man | ★★ | ✗ | `{1}{W}` FLASH 3/2; `{1}`, sac: ALL your creatures gain hexproof + indestructible. A protection spell held up like an instant that is a body when not needed (G-46 virtual copy of Restoration Magic with a 3/2 attached). Answers a sweeper too. |
| Bofur, Reliable Guardian // Concerted Care | ★★ | ✗ | Adventure `{1}{W}`: hexproof + indestructible (Restoration Magic at +1 mana), then a 1/1 lifelink body from exile later. Two virtual copies of the deck's best protection effect. |
| Restoration Magic | ★★ | ✗ | Confirmed from the pre-pile pass: `{W}` Cure = hexproof + indestructible; Curaga = the team. Plan A #6. |
| Bulwark Ox | ★ | ★★ | `{1}{W}` 2/2 Mount: attacks while saddled → +1/+1 counter on target creature (a repeatable counter source: Brute reload, Seedglaive stacking); sac: creatures WITH COUNTERS gain hexproof + indestructible. Saddle taps another power-1 body. In 56a every body carries counters, so the sac is a team Restoration Magic. |
| Hill Gigas | ◇ | ◇ | MV 6 5/4 trample haste OR Mountaincycling `{2}` — a land-drop that GROWS Molten Man (F8). Late, a hasty body. In 56b Tannuk warps it for `{2}{R}` (O19). |
| Zack Fair | ★ | ✗ | `{W}` 0/1 + counter; `{1}`, sac: target creature indestructible, moves its counters and its Equipment. A stored protection spell for one mana that also re-homes Boots. Indestructible only. |
| Reroute Systems | ★ | ✗ | `{W}` indestructible OR 2 to a tapped creature. Indestructible-half only (O17). |
| Divine Resilience | ★ | ✗ | `{W}` indestructible, kicker for all. Restoration Magic dominates it at the same mana. |
| Zealous Lorecaster | △ | △ | MV 6 4/4 regrowth an instant (Bulk Up back). F3 in 56; a repeatable-regrowth engine in 56b via Tannuk (O19). |
| Monastery Messenger | △ | △ | Hybrid → `{2}{R}{W}` in RW (G-58): 2/3 flier, puts a noncreature card from graveyard on TOP (Bulk Up again next draw). MV 4 for a small body. |
| Iron-Fist Pulverizer | △ | △ | MV 5 4/5 reach; second spell each turn → 2 face + scry. A spellslinger payoff two turns late. |
| Colossus of the Blood Age | △ | ✗ | MV 6 6/6, ETB 3 to each opponent; dies → filter-draw. F3. |
| The Misty Mountains Cold | △ | △ | Saga: a Treasure a turn, a 6/6 flying Dragon on chapter IV if four Treasures are held. Four turns to a body; the Treasures fix W (F7). |
| Crumb and Get It | ◇ | ✗ | `{W}` +2/+2, indestructible only if you gift them a Food = 3 life (O18, G-42). |
| Stone-Giant of High Pass | ✗ | ✗ | MV 7 (F3). ◇ in 56b via Tannuk (O19). |
| Aurelia, the Warleader | ✗ | ✗ | `{2}{R}{R}{W}{W}` — WW on 11 sources at MV 6 (F3 + F7). A premium card the manabase cannot cast. |
| Boldwyr Aggressor | ✗ | ✗ | Double strike + a Giant DS lord: 0 Giants in 56 (G-61) and DS = 0 (F2). |
| Earth Kingdom Protectors | ✗ | ✗ | Sac: an ALLY gains indestructible — 56 runs 0 Allies (G-61). |

## 5. Consolidated plan (live)

Re-ranked after batch 1. Nothing applied.

### Plan A — tune 56 in place (protection + evasion)

**ADDS, tiered (after batch 4):**
1. **Pain for All** (★★★, b3) — the reach engine.
2. **The Sentry, Golden Guardian** (★★★, b4) — an indestructible evasive body that makes
   Self-Destruct repeatable (O16). The Void is the named cost.
3. **Swiftfoot Boots** (★★★, b2) — permanent hexproof + haste.
4. **Return the Favor** (★★★, b1) — multiplier + redirect.
5. **Enter the Avatar State** (★★★, pre-pile) — hexproof + flying for `{W}`.
6. **Bygone Colossus** (★★, b3) — the 9/9 for three, on the haste-grant count.
7. **Restoration Magic** (★★) / **Bofur // Concerted Care** (★★, b4) — the hexproof
   instants; one or both, they are virtual copies of each other.
8. **Lightfoot Technique** (★★, b4) — flying + indestructible + a counter; the pick if
   Sentry is NOT taken (O17).
9. **Spectacular Spider-Man** (★★, b4) — flash protection with a body.
10. **Impolite Entrance** (★★, b2) / **Bre** (★★, b3) / **Key** / **Nova Hellkite** /
    **Rogue's Passage** (★★, b1).
11. Giantfall (★) as the Gnaw #2 replacement; Terror of the Peaks (★, revised E8);
    Brambleback Brute (★, reloads only with a counter add); Mjölnir (★); Wisecrack (★);
    Bulwark Ox / Zack Fair / Reroute Systems (★).
12. Out: Spectacular Tactics, Valorous Stance, Final Showdown, Fleeting Flight, Divine
    Resilience, Crumb and Get It, Aurelia (WW), Boldwyr, Protectors.

**Slot pressure:** eleven ★★★/★★ spell adds against 4–7 cuts. The white count is the
binding constraint now — Sentry, Avatar State, Restoration Magic, Bofur, Lightfoot,
Spider-Man are all W, against 11 W sources and 8 strict W pips today (F7). A final list
takes 3–4 of the white cards, not all six, and the manabase question (the pre-pile
note: +2 W sources without cutting a Mountain, F8) is now load-bearing.

**CUTS, in order (double-strike de-dup first, per the pre-pile finding):**
0. NOTE: with Boots + Return the Favor + Avatar State + Restoration Magic + Impolite
   Entrance + Key + Hellkite + Passage there are 7 spell adds against 4 cuts below —
   later batches decide which five make it. The 5th–7th cuts would come from: Team
   Tactics ×1 (DS #3–4 of 9, keep one for the trample rider), Go Ninja Go (`cuts` #2),
   Haste Magic ×1 (if Boots/Entrance/Hellkite carry the haste count).
1. Twin Blades ×2 — DS source #5–6 of 9, 3 MV, artifact (F2).
2. Reckless Ransacking ×1 — weakest trick (Pw 1.5).
3. Rabid Gnaw ×1 — keeps power-as-removal at 3 copies.
4. (if a 5th slot is needed) Tiger-Dillo — `cuts` #1, a body gated on power 4 that only
   attacks or blocks beside the tall one; contributes nothing to F1.

**PROTECT (the ranking cannot see these):** Self-Destruct (reach — E1), Bulk Up (the
multiplier), Molten Man (Mountain-scaled), Speed (the only unblockable GRANT — its
rider looks conditional and IS, on haste; O2), Seedglaive Mentor (valiant is fed by
every targeted add), Crackling Cyclops (F4 payoff — `cuts` calls it low power).

### Plan B — 56b "Ball Lightning" burst variant (VARIANT SIGNAL, not yet decided)

**After batch 4 (O19): Tannuk's warp also admits Hill Gigas, Zealous Lorecaster (a
repeatable Bulk Up regrowth) and Stone-Giant.** After batch 3 the body count clears a 60 (O11). Bodies: Ball Lightning, Nova Hellkite,
Red Tiger Mechan, Bygone Colossus, Iron Giant (via Tannuk), Molten Man / Cyclops / Red Hulk
(via Tannuk — Molten Man sacrifices a land on leaving, G-42). Payoffs: Terror of the Peaks,
Doc Ock's Tentacles, Pain for All, Self-Destruct ×2. Recast: Warped Space, Charred Foyer.
Evasion: Speed ×2 (always on), Full Bore. Still open: the protection layer (Boots is the
one candidate that helps a body that is leaving anyway — hexproof for the swing turn).

Core from batch 1: Ball Lightning, Nova Hellkite, Red Tiger Mechan, Tannuk, Full Bore,
Charred Foyer // Warped Space, + 56's Self-Destruct ×2 / Bulk Up ×2 / Speed ×2 / Haste
Magic ×2 / Crackling Cyclops. Thesis: every body is a spell (F10); Speed's rider is
always on (O2); Self-Destruct's self-damage is free (O3); sweepers and edicts miss.
Open questions for later batches: does the pile hold enough warp bodies for a 60, and
what is the protection layer when there are no permanents to protect? `/draft-deck` if it
survives the pile.

### 56a notes
**Batch 4:** Bulwark Ox ★★ (every 56a body carries counters — the sac is a team
hexproof+indestructible, and the saddle-attack counter feeds Halana's compounding);
Brambleback Brute revised to ★★ (Halana and Alena reloads it every combat, E7). The
white protection cluster is off-colour there; 56a's own is Overprotect / Snakeskin Veil.
**Batch 3:** Pain for All ★★★ (RG-castable; on Halana and Alena's compounding body every
point of damage dealt to it is face damage), Giantfall / Wisecrack ★ (interaction for its
4 → 5–6 at a C floor, F9), Bygone Colossus ★ (56a has fewer haste grants — count them
before adding).
**Batch 2:** Swiftfoot Boots ★★★ (hexproof + haste on a permanent-counter body is
exactly F9's protection axis), Mjölnir ★★★ (8 worthy carriers incl. Halana and Alena —
doubling damage on a body that compounds counters), Dragonclaw Strike ★★ (4 mana in RG,
Bulk Up #3 + a fight for its interaction-4 gap), Impolite Entrance ★★.
Return the Favor and Key to the Side-Door are ★★ there too (RG-castable, and 56a's
interaction is 4 at a C floor — a redirect is interaction it lacks, F9). Nothing in batch 1
is a counters PAYOFF, which is 56a's stated 10-enabler / 0-payoff gap.
