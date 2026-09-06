# Deck 56 tall pile — analysis (TEMPORARY working doc)

**Status: PILE COMPLETE (201 cards, 10 batches) — awaiting the user's picks.** Delete once the swaps land and the findings are folded into the
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
- **E10 (user correction, half-taken).** Stone-Giant of High Pass was filed ✗ on MV alone.
  Its Walls are ARTIFACT creature tokens, so they chump the Void and feed "{2}{R},
  sacrifice an artifact: 4 damage to ANY target" — reach, and the tokens outlive a warped
  Giant. Revised to ★ in 56b (Tannuk warps it for `{2}{R}`). In 56 it stays ✗ on a
  NUMBER, not a category: P(7 lands by T7) is 20% at 24 lands, so the hardcast mode is
  a one-in-five card. State the probability, not the mana value.
- **E11 (correcting the user's note).** Old Hob's `{1}{W}` indestructible targets an
  attacking creature TOKEN only — it cannot protect the tall body unless the body is a
  token. The haste-token half of the note is right.
- **E12 (user correction).** Steal the Show's modes resolve in printed order, and the
  first targets a PLAYER — so "choose both" on yourself is: discard the hand (instants
  and sorceries land in the graveyard, Bulk Up's flashback among them), draw that many,
  THEN mode two counts the newly filled graveyard. A wheel plus scaled removal, not a
  loot. Graded it as a loot with a rider. △ → ★.
- **E13 (rules answer for Lotus Ring).** Indestructible stops "destroy" and lethal damage
  only; SACRIFICE is neither, so an indestructible creature can still be sacrificed (and
  the Ring's sac cost is the CREATURE, not the Ring — the Ring stays, unattached). The
  fallback is therefore "turn your body into three mana", which is only upside on a body
  that is leaving anyway (a warped Colossus at end of combat). △ → ◇, for that line.
- **E14 (user correction).** Sami's affinity is on EVERY spell you cast, not on herself —
  with four artifacts out (Boots, Shield, Key, Pick-Axe, Treasures) Bulk Up and
  Self-Destruct cost {0} and the kill turn casts the whole hand, which is also F4 (Cyclops)
  and Stingerback's penalty running to zero. Graded her on MV 6 alone (F3). She is ◇ in 56
  (the artifact count is the number — 3 today, ~4 after the equipment adds) and ★★★ in an
  artifact-tilted variant. The MV-6 cost stands: she sets up NEXT turn's kill, not this
  one, and 24 lands reach six by T6 ~35% of the time.
- **E15.** "Tali Wakeen" resolved to nothing in the pool OR on Scryfall; the card is
  **Taii Wakeen, Perfect Shot** (OTJ). A name that fails twice is still a name to fix,
  not a card to drop (Stage 2). Graded under the corrected name.
- **E16.** "Bardmage's Rescue" is **Shardmage's Rescue** (DSK) — a second name that failed
  the pool and needed Scryfall's fuzzy match (E15's shape). Graded under the real name.

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

- **O20. THE FIREBALL SUB-PLAN IS NOW A REAL SECOND WIN CONDITION.** "Deal the tall body's
  power to any target" has FOUR engines across the pile: Self-Destruct (in deck), Pain for
  All (b3, doubles it), Iron Fist (b5 — every creature-targeting spell gives him a TAP
  for his power, repeatable each turn), Infernal Phantom (b5 — dies → power to any
  target, so Self-Destruct on him is 2X). Add the survivors (Sentry / Luke Cage take
  Self-Destruct and live, O16) and the small reach (Helix, Hawkeye's Explosive, Longhorn's
  plot, Stone-Giant's sac). A chump-block board stops mattering when the power goes
  face. `stats` counts one of these as reach (Self-Destruct is `burn`; Iron Fist and
  Phantom score no role at all — G-67, same hole as O4). The user's Iron Fist and Phantom
  stars both read the card right.
- **O21. Stingerback Terror's hand-size penalty runs the RIGHT way here.** -1/-1 per card
  in hand, in a deck that CASTS its hand on the kill turn: every trick cast is +1/+1 to
  the Terror AND its own effect, and Plot `{2}{R}` puts it in exile to come down free with
  an empty hand. A 7/7 flying trample for three-then-zero. The user's read is right; the
  extra point is that F4's spell density is the same number that shrinks the penalty.
- **O22. "Becomes tapped" and "attacks alone" are TRIGGER CONDITIONS the deck's own cards
  satisfy or violate.** Hawkeye triggers off Team Tactics' teamwork tap (a cost-as-upside,
  G-41) without attacking. Luke Cage wants to attack ALONE — which is the tall pattern —
  but every second attacker the pile adds (Hawkeye, Ty Lee, Brute, Scalestorm) turns him
  off. Count attackers before pairing them.
- **O23. Equipment that is INDESTRUCTIBLE is a permanent investment removal cannot undo**
  (Boots is not; Shield, Pick-Axe, Lotus Ring are) — but none of them protects the BODY
  from destroy. Captain America's Shield's +0/+8 answers burn and fights, its attack-tap
  answers a blocker, and vigilance lets Iron Fist swing AND tap. It is the one equipment
  in five batches that adds to the deck's protection AND evasion at once.

- **O24. THE THIRD KIND OF PROTECTION: LOCK THE KILL TURN.** Grand Abolisher, Jennifer
  Walters and Voice of Victory all say "your opponents can't cast spells during your turn"
  (Abolisher also stops artifact/creature/enchantment abilities). For a one-swing deck
  that is not protection ON the body, it is the removal of every instant-speed answer on
  the turn that matters — Bulk Up cannot be answered in response. Paired with Boots
  (hexproof on THEIR turn) the coverage is complete. Three virtual copies of the effect
  at two mana (G-46). Cost is white: Abolisher is `{W}{W}` — 45% on T2, 59% on T4, 71% on
  T6 with 11 W sources — where Walters and Voice are a single W.
- **O25. Avatar's Wrath is the one card that answers CHUMP BLOCKS and SWEEPERS at once**:
  keep the tall body, airbend everything else (theirs AND yours), and they cannot recast
  from exile until your next turn. It costs your own support board (Cyclops, Speed,
  Seedglaive — recastable for `{2}`, G-42 half-cost) and WW at sorcery speed.
- **O26. Super-Soldier Serum makes the body a LEGENDARY Soldier** — so a non-Villain R/W
  body it enchants becomes Mjölnir-worthy (Stingerback, Cyclops, Luke Cage; Molten Man
  and Red Hulk stay Villains), and it auto-attaches every Equipment on attack. The
  equipment count decides it (G-61): 3 today counting Twin Blades, which are cut; Boots +
  Shield + Celestial Armor restores 3.
- **O27. Daredevil is the deck's first REPEATABLE card advantage.** "Whenever you attack,
  exile the top card; you may play it this turn" fires every attack, Hero or not — the
  +2/+1 is the rider, the impulse is the card. 56 has 0 repeatable CA (F6d); the user's
  "minor" undersells it. Haste + vigilance also turns Speed on (O2).

- **O28. THE PILE'S SECOND THEME AFTER PROTECTION IS COST CHEATING, and it is ~14 cards
  deep now.** F10 called "what the deck pays vs what is printed" structurally invisible;
  the pile has answered it from every direction: Tannuk (red creatures + artifacts warp
  `{2}{R}`), the native warps (Colossus `{3}`, Vestige `{4}`, Nova Hellkite, Mechan, Ball
  Lightning's premise), the Plots (Stingerback, Demonic Ruckus `{R}`, Longhorn), Warped
  Space (`{0}` from exile once a turn — which also makes Hex Magic's exiled hand one free
  card a turn), Sami (affinity on every spell), Kíli (first equip free), Serum and
  Blacksmith's Talent L2 (free attach), Lorehold (miracle `{2}` on every instant and
  sorcery in hand), Nexus of Becoming (a 3/3 Golem copy of anything in hand each combat),
  Anticausal Vestige (cheat a permanent onto the battlefield on leaving, twice). **56b is
  not "Ball Lightning"; it is CHEAT-TALL** — every body and every spell arrives for less
  than printed, and Self-Destruct is free on the ones that leave. Rename the working id's
  thesis; decide at the end as planned.
- **O29. Energybending is a hidden Molten Man pump.** "Lands you control gain all basic
  land types" makes every land a MOUNTAIN until end of turn, so Molten Man gets +1/+1 per
  non-Mountain land you control — at instant speed, for `{2}`, colourless, and it draws a
  card. It also fixes WW for Abolisher / Wrath on the turn it matters (F7). Nothing tags
  "gain all basic land types" as a pump, and no model here counts Mountains as a
  resource (F8 is a hand rule).
- **O30. Aura risk has an insurance shape.** Demonic Ruckus draws a card when it leaves
  the battlefield, so removal on the enchanted body is a 2-for-1 that refunds one. Pain
  for All has no such clause — its insurance is that the ETB already fired.
- **O31. Nexus of Becoming's "except it's a 3/3" REPLACES base P/T and keeps everything
  else** — a Molten Man copy is 3/3 + Mountains (legend rule with the real one), a Sentry
  copy is a 3/3 flying vigilance indestructible that hands them a SECOND Void, a Sire copy
  is a 3/3 with six keywords and ward 7, a Stingerback copy is a 3/3 that shrinks per card
  in hand (bad). Read what the copy KEEPS before cheating it.

- **O32. MENACE is the third evasion sub-cluster after flying and unblockable**, and batch 8
  is where it arrives: Ferocification (menace + haste EVERY combat), Daily Bugle Building
  (a land that gives a legendary menace), How to Start a Riot, J. Jonah Jameson and Caught
  Red-Handed (suspect: menace AND can't block), Lightning, Raphael, Zhao, Item Shopkeep,
  Quilled Charger, plus Agrus Kos (b6) and Demonic Ruckus (b7). Against a one-blocker
  board menace is unblockable; against two it is a chump-block tax. Nothing in 56 grants
  it today.
- **O33. CRYSTAL BARRICADE MAKES SELF-DESTRUCT FREE WITHOUT AN INDESTRUCTIBLE BODY.**
  "Prevent all noncombat damage that would be dealt to other creatures you control" —
  Self-Destruct's X to itself is noncombat damage to a creature you control, so it is
  prevented; so is Rabid Gnaw's and Agni Kai's fight-back, and Wisecrack's. A `{1}{W}` 0/4
  defender that also chumps the Void and gives YOU hexproof. Two costs, both G-42-shaped:
  prevented damage is not DEALT, so Pain for All's reflect does not fire off the
  self-damage (the ETB and blocker damage still do), and Red Hulk's enrage never triggers.
  O16 (Sentry) and O33 are the two routes to a repeatable Self-Destruct; they do not stack
  in value, they are virtual copies.
- **O34. Zhao's counter is the only PERMANENT Mountain-count booster in the pile**, and it
  costs `{7}`: every nonbasic becomes a Mountain, so Molten Man gains +1/+1 per nonbasic YOU
  control — five in 56 today. Energybending does the same for `{2}` at instant speed for a
  turn and draws (O29). The user's read is right on the mechanism; the number is +5 for 7
  mana, 20% castable by T7. Zhao's static also taps YOUR nonbasics on entry.
- **O35. Firebending / mana-on-attack is the kill turn's fourth resource.** Sozin's Comet
  (foretell `{2}{R}`, then RRRRR on the swing for every attacker), Firebending Student (b1),
  The Last Agni Kai's overflow, Maximum Carnage's chapter II. The one-swing deck's binding
  constraint on the kill turn is MANA for the tricks in hand, not the tricks — F4 and
  Stingerback both want the whole hand cast. This is O28 by another mechanism.
- **O36. Collective Inferno is Mjölnir without the worthy gate**: double all damage from
  sources of a chosen TYPE, convoke to cast on T3–4. HUMAN covers Sentry, Iron Fist, Luke
  Cage, Hawkeye, Mai, War Machine, Swiftblade, Scalestorm — 56's central theme (5 copies
  today, far more with the pile's Marvel bodies). Molten Man (Elemental) and Stingerback
  (Scorpion Dragon) are outside it; choose the type for the body you are building.

- **O37. STATION IS A SECOND USE OF THE TALL BODY'S POWER (user's Dawnsire insight, checked
  against the pool).** Station taps another creature at sorcery speed for charge counters
  equal to its POWER — so one Bulk-Upped body stations a Spacecraft to its top tier in one
  tap, at the cost of that body's attack that turn. Pool sweep: 14 Station cards castable in
  RW, of which the fits are **Dawnsire** (`{5}`: 10+ = 100 damage to a creature on attack,
  20+ = a 20/20 flier — one 10-power tap turns it on, one 20-power tap makes it the body),
  **Lumen-Class Frigate** (`{1}{W}` 3/5: 2+ = other creatures +1/+1, 12+ = flying lifelink —
  the cheap one), **The Seriema** (`{1}{W}{W}` 5/5: ETB tutors a legendary creature — Sentry
  — 7+ flies, and *tapped* legendary creatures you control are INDESTRUCTIBLE, which the
  station tap itself provides), **Warmaker Gunship** (`{2}{R}`, ETB damage = artifacts),
  **Wurmwall Sweeper** (`{2}`, 4+ flies). Galvanizing Sawship / Pinnacle Kill-Ship /
  Extinguisher Battleship are MV 6–8 (F3; Battleship is Tannuk-warpable for its ETB).
  Station does not stack with the Self-Destruct plan on the same turn — the body taps for
  one or attacks for the other.
- **O38. SPINEROCK TYRANT COPIES EVERY TRICK IN THE DECK.** "Whenever you cast an instant
  or sorcery with a single target, copy it": Bulk Up ×4, Self-Destruct 2X, Haste Magic,
  Team Tactics, Avatar State, Restoration Magic — every pump and every finisher is
  single-target. It is Return the Favor's copy mode on a 6/6 FLYING body, for every spell,
  free. Twinflame Tyrant (same cost) doubles the DAMAGE instead, to opponents only — so it
  doubles Self-Destruct's face half and NOT its self-damage. Both are `{3}{R}{R}` with no
  haste; the deck holds one MV-5 body, not two (F3). Spinerock for A1, Twinflame for A2.
- **O39. DELNEY IS AN ENGINE HERE, not a 46-only card.** Power ≤2 creatures' triggers fire
  twice: Crackling Cyclops is a printed 0/4 (O14), so each noncreature spell is +6/+0, not
  +3; War Machine's combat trigger gives +2X/+0; Speed's rider, Hawkeye's Trick Arrows (six
  payments), Iron Fist, Mai's prowess all double. And "power ≤2 can't be blocked by power
  ≥3" is evasion for the body BEFORE the pump: attack as a 2-power, pump after blocks. G-40's
  own worked example, one deck over.
- **O40. TEAM AVATAR is the attack-alone payoff (O22's other side).** +X/+X where X = creatures
  you control, every attack, for the creature attacking ALONE — the more bodies stay home,
  the taller the one that goes. It rewards exactly what Luke Cage wants and Hawkeye / Ty Lee
  / Brute violate. A1's repeatable pump.

- **O41. SWORD OF WEALTH AND POWER'S PROTECTION IS PROTECTION FROM YOUR OWN TRICKS.**
  "Protection from instants and sorceries" stops targeting by ANY player's instants —
  Bulk Up, Self-Destruct, Haste Magic, Team Tactics, Avatar State, Restoration Magic all
  fail to target the equipped body. Sixteen of 56's 36 nonland cards are instants. It is
  the strongest-looking protection card in the pile and a G-42 card here; it only works
  on a body the deck pumps by ABILITY (Mercenaries, Patriot, Team Avatar, Ferocification)
  or Aura (Pain for All, Ruckus). Graded ◇ with the warning, not ★★★.
- **O42. THE MERCENARY SUB-THEME IS REAL AND SORCERY-SPEED (user's Ertha Jo note).**
  Brimstone Roundup (a Mercenary per second spell — 56 casts two most turns), Hellspur
  Posse Boss (two), Form a Posse (X), Ertha Jo and Prosperity Tycoon (one each), Rodeo
  Pyromancers (is one). Each token is "{T}: +1/+0, sorcery speed" — so four of them are +4
  BEFORE Bulk Up, +8 after, but only in main phase 1, so the pump is visible to blockers.
  Ertha Jo copies every ACTIVATED ability that targets — the Mercenary taps (+2 each), but
  also Iron Fist's tap (2X to the face), Patriot's hexproof, Key's unblockable, Bre's
  flying. The user's read is right; the sorcery-speed limit is the caveat, and the tokens
  are Terror-of-the-Peaks / Self-Destruct / Void-chump fodder either way.
- **O43. THE FIRE CRYSTAL IS THREE OF THE PILE'S AXES ON ONE CARD**: red spells cost `{1}`
  less (O28 — Bulk Up, Self-Destruct, Haste Magic, Team Tactics all `{R}`), creatures have
  haste (O2/O10 — Speed is always on, Colossus / Sentry / Stingerback swing the turn they
  land), and a `{4}{R}{R}` hasty token copy of a creature. `{2}{R}{R}` on 18 R sources.
- **O44. COPY EFFECTS are the pile's fourth cluster, and they price the same** — Return
  the Favor (`{R}{R}`+`{1}`), Choreographed Sparks (`{R}{R}`, both modes), Spinerock
  (free, on a body), Peter Parker's Camera (abilities, 3 charges), Ertha Jo (activated
  abilities), Mica (sac an artifact), Sword of W&P and Buster Sword (on damage),
  Pyromancer's Goggles, Spider-Verse, Pigment Wrangler. On a Bulk Up every one is ×4.
  A deck holds two or three; Sparks + Spinerock is the cheapest pair.
- **O45. Screen (39 candidates): all castable, all Standard-legal; 36 of 39 read
  "tangential"** — the theme model cannot see structural value (G-31 residual), which is
  the whole pile. Read the order, not the word. Zero-role cards among the ★★★s: Pain for
  All, Return the Favor, Choreographed Sparks, Stingerback, Twinflame, Grand Abolisher,
  Delney — the batch-fix list (Stage 4) is below.

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
| Stone-Giant of High Pass | ✗ | ✗ | Revised (E10): the Walls are artifact tokens — chump the Void, then `{2}{R}` sac for 4 to ANY target. ★ in 56b (warp `{2}{R}`, and the Wall stays). ✗ in 56 on the number: 20% to hardcast on T7. |
| Aurelia, the Warleader | ✗ | ✗ | `{2}{R}{R}{W}{W}` — WW on 11 sources at MV 6 (F3 + F7). A premium card the manabase cannot cast. |
| Boldwyr Aggressor | ✗ | ✗ | Double strike + a Giant DS lord: 0 Giants in 56 (G-61) and DS = 0 (F2). |
| Earth Kingdom Protectors | ✗ | ✗ | Sac: an ALLY gains indestructible — 56 runs 0 Allies (G-61). |

### Batch 5 (20 cards)

| Card | 56 | 56a | Note (framework rule) |
|---|---|---|---|
| Stingerback Terror | ★★★ | ★★ | `{2}{R}{R}` 7/7 FLYING TRAMPLE, -1/-1 per card in hand; Plot `{2}{R}` to cast free later. The biggest evasive base body in the pile (F1), and the penalty shrinks with every trick you cast (O21). Bulk Up → 14 flying trample. RR on 18 sources is fine. The user's plot line is the right sequencing. |
| Iron Fist, Living Weapon | ★★ | ★★ | `{2}{R}` 2/3: every spell that targets YOUR creature gives him "{T}: his power to any other target" this turn. Twenty-plus of the deck's spells qualify. Pump HIM and he is a repeatable Self-Destruct with no self-damage (O20); Mjölnir-worthy (Human Warrior Hero, red) for ×2. Needs to be untapped — Shield's vigilance lets him attack and tap. The user's read is exact. |
| Hawkeye, Master Marksman | ★★ | ★★ | `{1}{R}` 2/2 reach first strike; whenever TAPPED, `{1}` up to three times: a blocker can't block / 2 face / loot. Attacks beside the tall body as a blocker-remover + reach + the deck's only repeatable draw (F6d). Also fires off teamwork (O22). |
| Captain America's Shield | ★★ | ★★ | `{2}` equip `{2}`, indestructible: +0/+8, vigilance, attack → TAP a defender's creature. Repeatable blocker removal (F6b) plus an 8-toughness answer to burn/fights (F6a half), and vigilance for Iron Fist (O23). Not hexproof; does nothing against destroy or exile. |
| Luke Cage, Power Man | ★★ | ✗ | `{3}{W}` 2/5; attacks ALONE → +2/+0 and indestructible. Self-protecting on exactly the tall attack pattern, survives its own Self-Destruct (O16) with no Void. No evasion, and no protection on THEIR turn. Sentry beats it on evasion; Luke beats it on drawback. Every second attacker turns him off (O22). |
| Infernal Phantom | ★ | ★ | `{3}{R}` 2/3; dies → its power to any target. Self-Destruct on a pumped Phantom is 2X (O20) — the user is right. MV 4 for a 2/3 (F3) and eerie is dead without enchantments; Pain for All doubles on the body you already have, which is why this is ★ not ★★. |
| Diamond Pick-Axe | ★ | ★ | `{R}` equip `{2}`, indestructible: +1/+1 and a Treasure ON ATTACK — mana that arrives DURING combat for an extra trick, and W fixing (F7). Cheap and permanent. |
| The Lonely Mountain | ★ | ★ | A Land — MOUNTAIN (Molten Man +1, F8) with a Dwarf-token sink; enters tapped unless you control an Equipment. Replaces a basic at no cost to F8 once Boots/Shield are in. |
| Lightning Helix | ★ | ✗ | `{R}{W}` 3 to any target + 3 life. Flexible reach/removal at instant speed. Generic; the deck's interaction is 7 already. |
| Mouse Trapper | ★ | ✗ | `{2}{W}` FLASH 3/2 valiant → tap an opponent's creature. A blocker-tap off a spell you cast anyway — but the spell has to target TRAPPER, not the tall body, so each tap costs a pump. The user's read is right on the mechanic; the cost is the split target. |
| Monica Rambeau | ★ | ✗ | Front face `{2}{W}` 3/3 flying prowess — an evasive bearer (F1 + F4). The `{2}{R}{W}{W}` transform is WW on 11 sources (F7), so grade the front only (G-43). |
| Stone by Sunlight | ★ | ✗ | `{1}{W}` destroy power ≥4 OR indestructible. Same tier and same axis as Valorous Stance — out on O17. |
| Longhorn Sharpshooter | ◇ | ◇ | Plot `{3}{R}`: 2 to any target now, a free 3/3 reach body later with the turn's mana open. The user's sequencing is right; it is tempo-neutral rather than an axis. |
| Old Hob, Alleycat Blues | ◇ | ◇ | MV 5 (F3): a 2/2 haste token each combat (Self-Destruct fodder — the token dies anyway, G-41; Terror of the Peaks 2 a turn). The `{1}{W}` indestructible is TOKEN-only (E11). |
| Tenth District Hero | ◇ | ✗ | Six mana and six MV of graveyard across three steps to a 5/5 that gives OTHER creatures indestructible permanently. Collect evidence exiles Bulk Up from the yard (G-42, flashback). |
| Prosperity Tycoon | △ | ✗ | 4/2 + a Mercenary that taps for +1/+0 (sorcery); its indestructible taps ITSELF — defensive, not for an attacker. |
| Joshua, Phoenix's Dominant | △ | ✗ | `{1}{R}{W}` 3/4 loot-two; the Phoenix transform is 5 mana and grindy. No tall relevance. |
| Steal the Show | ★ | ★ | Revised (E12): choose both on yourself — discard the hand (tricks + Bulk Up to the yard), draw that many, then damage = the now-fuller graveyard to a creature. A wheel + scaled removal for `{2}{R}` at sorcery speed. Creature-only (E1). |
| Lotus Ring | ◇ | ◇ | Six mana total for +3/+3 vigilance, indestructible Equipment. The sac-for-three is of the CREATURE and indestructible does not stop it (E13) — upside only on a body that is leaving anyway (warp). |
| Boilerbilges Ripper | △ | △ | MV 5, sac another creature → 2 damage; with Phantom that is the Phantom's death trigger + 2. Two slow cards to make one line. |

### Batch 6 (14 cards)

| Card | 56 | 56a | Note (framework rule) |
|---|---|---|---|
| Grand Abolisher | ★★★ | ✗ | `{W}{W}` 2/2: on your turn they cannot cast spells OR activate artifact/creature/enchantment abilities. The kill turn becomes uninteractable (O24). The `{W}{W}` is the whole cost: 59% by T4 on 11 sources (F7); if the manabase moves to 13 W it is a different card. |
| Jennifer Walters | ★★ | ✗ | `{1}{W}` 2/3: opponents can't cast spells during your turn — the single-W Abolisher (89% by T4) without the ability lock. Transform is off-colour and dead (G-58: still castable). |
| Voice of Victory | ★★ | ✗ | `{1}{W}` 1/3, same lock as Walters, plus Mobilize 2 (two 1/1 attackers each swing — Terror of the Peaks / Scalestorm fodder, otherwise irrelevant to tall). Third virtual copy of O24. |
| Agrus Kos, Spirit of Justice | ★★ | ✗ | `{2}{R}{W}` 2/4 DS vigilance; ETB AND attack: suspect a creature (menace, CAN'T BLOCK), exile it if already suspected. Repeatable blocker removal that graduates to exile; or suspect your own body for menace. Works the turn it lands. |
| Daredevil, Man Without Fear | ★★ | ✗ | `{2}{R}{W}` 3/4 vigilance haste; every attack impulses the top card (O27). Repeatable card advantage the deck has none of, on a hasty body. |
| Avatar's Wrath | ★★ | ✗ | `{2}{W}{W}` sorcery: keep one creature, exile every other one; they can't recast from exile until your next turn. Chump blocks and sweepers answered in one card (O25); costs your own support board and WW at sorcery speed. |
| Super-Soldier Serum | ★ | ✗ | `{1}{W}` Aura: +2/+2 first strike vigilance, legendary Soldier (Mjölnir-worthy, O26), free-attach every Equipment on attack. Aura 2-for-1 risk; ★★ once the deck holds 3+ Equipment. |
| The Super Hero Civil War | ★ | ✗ | MV 5 saga: steal two blockers (MV ≤6 total) for two turns, team +1/+1 vigilance, then a fight. Self-Destruct on a stolen body is removal + reach (O9). The user's read is right; MV 5 at sorcery speed is F3's cost and the steal is temporary. |
| Zog, Triceraton Castaway | ◇ | ◇ | MV 5 5/4 reach trample + ETB can't-block, or Mountaincycling `{2}` (F8). Hill Gigas with a blocker-answer instead of haste; 56b via Tannuk ★. |
| Veteran Guardmouse | △ | △ | MV 4 valiant: +1/+0 first strike + scry when targeted. A Seedglaive at twice the cost. |
| Brightspear Zealot | △ | ✗ | 2/4 vigilance, +2/+0 with two spells. A small spellslinger body. |
| Sami, Wildcat Captain | ◇ | ✗ | Revised (E14): affinity on EVERY spell — four artifacts out and the kill turn casts the hand for free (F4 / Stingerback run to the max). MV 6 sets up next turn's kill, not this one (F3, ~35% to six lands by T6). ★★★ in an artifact-tilted variant. |
| Pride of the Road | ✗ | ✗ | Max-speed double strike (F2 = 0, and T5+). |
| Aurelia, the Law Above | ✗ | ✗ | Triggers need three / five ATTACKERS — the opposite of attacking alone (G-42 for Luke Cage). |

### Batch 7 (21 cards)

| Card | 56 | 56a | Note (framework rule) |
|---|---|---|---|
| Energybending | ★★ | ★★ | `{2}` instant, colourless: every land is a Mountain until end of turn (+1/+1 per non-Mountain on Molten Man, O29), fixes WW for the turn, draws a card. Three axes on a cantrip. |
| Demonic Ruckus | ★★ | ★★ | `{1}{R}` Aura: +1/+1 MENACE + TRAMPLE (F1 evasion), draws when it leaves (O30), Plot `{R}` to cast free later. The cheapest evasion in the pile with its 2-for-1 insured. |
| Hex Magic | ★★ | ★★ | `{2}{R}` sorcery: exile the hand, draw that many, and you may STILL play the exiled cards until the end of next turn — a "draw N" that keeps the old N. On a kill turn with four cards it is eight cards of tricks (F6d). Sorcery at 3 is the cost. Warped Space makes one exiled card a turn free (O28). |
| Lorehold, the Historian | ★★ | ✗ | `{3}{R}{W}` 5/5 FLYING HASTE — a T5 body that is itself the kill-turn swing (F3 ✓, Speed's rider on) and gives every instant/sorcery in hand miracle `{2}` (Return the Favor, Avatar's Wrath for two). Single pips. The top end 56 could take. |
| The Arkenstone // Seek the Heart | ★★ | ★ | Adventure `{2}{W}`: TUTOR a legendary creature (Sentry, Iron Fist, Luke Cage, Agrus, Daredevil, Molten Man, Red Hulk…) — finds the tall body on demand. Then the `{5}` artifact: +1/+1 anthem and draw a card every end step (repeatable CA). Tannuk-warpable as an artifact. |
| Buster Sword | ★★ | ★★ | `{3}` equip `{2}`: +3/+2; combat damage to a player → draw + free-cast a spell with MV ≤ that damage. On a double-striker the first-strike hit casts Self-Destruct free before regular damage. CA that scales with the swing. |
| Kíli the Resourceful | ★ | ✗ | `{1}{W}` 1/2: storied is on for free here (five legendaries); first equip each turn costs `{0}`, draw when an Equipment enters. The user's read is right; the equipment COUNT decides it (3 today, Twin Blades cut) — ★★★ in the equipment plan, in 74 already. |
| Taii Wakeen, Perfect Shot | ★ | ✗ | `{R}{W}` 2/2 (E15): `{X},{T}` adds X to every noncombat damage this turn — Self-Destruct, Pain for All, Iron Fist, Gnaw (A2 amplifier, ★★ there); draws when your noncombat damage exactly equals a creature's toughness (fiddly). |
| Anticausal Vestige | ★ | ★ | Warp `{4}` 7/5; on LEAVING: draw + put a permanent with MV ≤ your lands onto the battlefield tapped — then recast from exile and do it again. The user's "2-time cheat" is right. Needs haste to swing on the warp turn and a target in hand; ★★★ in 56b (O28). |
| Nexus of Becoming | ★ | ★ | `{6}`: each combat draw + exile a creature/artifact from hand → a 3/3 Golem copy with its abilities (O31). Repeatable cheat + card a turn; MV 6 (F3). ★★ in the cheat plan. |
| Diary of Dreams | ★ | ★ | `{2}`: a page counter per instant/sorcery; `{5}`-minus-counters, `{T}`: draw. Four spells in and it is `{1}`: draw, repeatably. An artifact for Sami's count. |
| Thrór's Map | ★ | ★ | `{2}`: tutor a basic to hand (a Plains for WW, or a Mountain for F8) + `{2},{T}` loot. Legendary (Kíli's storied, Key's draw mode). |
| Ragged Short Spear | ★ | ★ | `{1}{R}` Equipment: ETB discard one, draw TWO; +2/+0. The ETB is the card; equip `{3}` is bad alone and free under Kíli/Serum. |
| Charging Strifeknight | ★ | ★ | `{2}{R}` 3/3 HASTE + `{T}`, discard: draw. A hasty 3-power bearer that loots when not attacking. |
| Yuyan Archers | △ | △ | `{1}{R}` 3/1 reach + ETB loot. 3 base power is a better Bulk Up base than Vindicator's 1 (user's point); 1 toughness dies to everything. |
| Bandit's Haul | ◇ | ◇ | `{3}` rock: any-colour mana (WW fixing) + crime-fed draw. A rock in a 2.4-curve deck is F3's cost. |
| Sire of Seven Deaths | △ | △ | `{7}` 7/7 with six keywords + ward 7 life. NOT Tannuk-warpable (colourless, not an artifact); 20% to hardcast on T7. A payload for Vestige / Nexus only (O31). |
| Flick a Coin | △ | △ | 3 mana: 1 damage + Treasure + draw. F4 but too expensive for the effect. |
| Borrowed Knowledge | △ | ✗ | `{2}{R}{W}` wheel. Hex Magic does it for 3 and KEEPS the hand. |
| Hedron Archive | △ | △ | `{4}` ramp rock, sac for two. Wrong curve. |
| Racers' Scoreboard | △ | △ | `{4}`: loot-two ETB, a late `{1}` discount at max speed. |

### Batch 8 (24 cards)

| Card | 56 | 56a | Note (framework rule) |
|---|---|---|---|
| Crystal Barricade | ★★★ | ✗ | `{1}{W}` 0/4 defender: prevents all noncombat damage to your OTHER creatures — Self-Destruct's self-damage, fight-back, Wisecrack — so the finisher is free every turn on any body (O33); you have hexproof; it chumps the Void. Costs Pain for All's reflect off the self-damage and Red Hulk's enrage (G-42). The A2 fireball plan's other enabler (O16 is the first). |
| Ferocification | ★★ | ★★ | `{2}{R}` enchantment: EVERY combat, menace + haste OR +2/+0 on your creature. Repeatable evasion (O32) that turns Speed's rider on every turn (O2). One card, on the table, for the rest of the game. |
| Collective Inferno | ★★ | ★★ | `{3}{R}{R}` convoke: double all damage from sources of a chosen type (O36). A permanent damage-doubler (F1's third axis) with no equip gate; convoke lets the small bodies pay for it. Choose Human for the Marvel bodies, or the tall body's own type. |
| Patriot, Shield Wielder | ★★ | ✗ | `{1}{W}` 2/2: `{2},{T}`: another creature +2/+0 and HEXPROOF until end of turn — repeatable instant-speed hexproof (F6a), the activated-ability copy of Restoration Magic. Worse than Boots (mana each turn), a second copy of the effect (G-46). |
| Shardmage's Rescue | ★★ | ✗ | `{W}` FLASH Aura (E16): hexproof the turn it enters, +1/+1 permanently. One-mana instant-speed protection that leaves a stat behind; targets your creature (Iron Fist, valiant). Avatar State gives flying instead of the counter — take both, they are the same slot. |
| Daily Bugle Building | ★★ | ★★ | A LAND: `{1},{T}` any colour (WW fixing, F7) and `{1},{T}` a LEGENDARY creature gains menace (sorcery) — Molten Man, Sentry (redundant with flying), Iron Fist, Luke Cage, Agrus, Daredevil, Mai, Speed. Evasion from a land slot; takes a tapland's slot, never a Mountain (F8). |
| Sozin's Comet | ★★ | ★★ | Foretell `{2}{R}` on T3, cast for three on the kill turn: every attacker adds RRRRR on attack (O35). The hand gets cast in combat. A sorcery that IS the kill turn's mana. |
| Soul Immolation | ★★ | ★★ | `{3}{R}{R}`: blight X (X ≤ your greatest toughness; -1/-1 counters on one of your creatures) → X to each opponent AND each of their creatures. Reach + a ONE-SIDED sweeper at X = Stingerback's 7 / Sentry's 5 / a doubled body's toughness. The counters can go on a Wall token — or on Brambleback Brute, giving him X can't-block charges (E7). |
| Maximum Carnage | ★ | ★ | MV 5 saga: I — until your next turn every creature must attack a player other than its controller: THEIR board attacks you and is TAPPED on your next turn (no blockers); II — RRR; III — 5 face. A three-turn plan that also forces YOUR creatures to attack on cast (G-42 half). |
| How to Start a Riot | ★ | ★ | `{2}{R}` instant: menace + your team +2/+0. Three mana for what Demonic Ruckus does permanently for two (O32). |
| J. Jonah Jameson | ★ | ★ | `{2}{R}` 2/2: ETB suspect (their blocker can't block, or your body gets menace); a Treasure per menace attacker (fixing). |
| Lightning, Security Sergeant | ★ | ★ | `{2}{R}` 2/3 MENACE; connect → impulse a card while you control her. A menace bearer with CA. |
| Veteran Survivor | ★ | ✗ | `{W}` 2/1; exiles a graveyard card each second main if it attacked; at three, a 5/4 HEXPROOF. A one-drop that grows into a self-protecting body by T5 — and exiles their recursion (or your Bulk Up, G-42). |
| Zhao, the Moon Slayer | ◇ | ◇ | `{1}{R}` 2/2 menace; `{7}` for the conqueror counter → nonbasics are Mountains, Molten Man +5 permanently (O34). Taps your own duals on entry. |
| Caught Red-Handed | ◇ | ◇ | MV 5 INSTANT Threaten + suspect: steal a blocker into your attack with haste, Self-Destruct it (O9), hand it back unable to block ever again. Five mana (F3). |
| Raphael, Most Attitude | ◇ | ◇ | MV 4 4/3 menace; impulse on other creatures entering, play them on attack. CA on a menace body; few creatures enter here. |
| Pigment Wrangler // Striking Palette | ◇ | ◇ | MV 5 4/4 flier that enters prepared: cast `{R}` copy-your-next-spell once. A flying bearer with a one-shot Return the Favor. F3. |
| Daring Discovery | ◇ | ◇ | MV 5 sorcery: three creatures can't block + discover 4 (a free MV ≤4 card). Blocker removal with a free spell, two turns late. |
| Narset's Rebuke | ◇ | ◇ | MV 5 instant: 5 damage, exile; refunds URW (the U is dead). Net-two-mana removal with two usable mana back. |
| Pyromancer's Goggles | ◇ | ◇ | `{5}`: `{T}` for R that copies the red instant/sorcery it pays for — Bulk Up ×4, Self-Destruct 2X, every turn. F3; a cheat-plan card. |
| Item Shopkeep | △ | △ | Menace on an EQUIPPED attacker each attack — needs the equipment plan. |
| Wingnut, Bat on the Belfry | △ | △ | Alliance keywords need creatures entering; +1/+0 to OTHER attackers is go-wide. |
| Quilled Charger | △ | △ | Saddle 2 taps another body for menace on ITSELF. |
| Misty Mountains Raider | △ | △ | Amass 2 on attack — an Army token deck. |

### Batch 9 (20 cards)

| Card | 56 | 56a | Note (framework rule) |
|---|---|---|---|
| Spinerock Tyrant | ★★★ | ★★★ | `{3}{R}{R}` 6/6 FLYING; copies every single-target instant/sorcery you cast (O38). A tall flying body that doubles its own pumps and finishers. MV 5, no haste (F3): the one top-end slot, and the best claim on it. |
| Delney, Streetwise Lookout | ★★★ | ✗ | `{2}{W}` 2/2: power ≤2 triggers fire twice (Cyclops +6 per spell, War Machine, Speed, Hawkeye, Iron Fist, Mai) and power ≤2 attackers can't be blocked by power ≥3 (O39). An engine on the deck's existing pieces plus pre-pump evasion. |
| Twinflame Tyrant | ★★★ | ★★★ | `{3}{R}{R}` 3/5 flier: double all damage to opponents and their permanents — combat, Self-Destruct's face half (not its self-half), Pain for All's reflect, Iron Fist, Gnaw. The least-gated doubler in the pile; the user's "generous" is right. Competes with Spinerock for the MV-5 slot (O38). |
| Team Avatar | ★★ | ✗ | `{2}{W}` enchantment: the creature attacking ALONE gets +X/+X, X = your creatures — a repeatable pump keyed on the tall pattern (O40); discard mode is X damage to a creature. |
| Cosmic Cube | ★★ | ★★ | `{5}` ward 2: every attack, look at six and cast one with MV ≤ your greatest attacking power FREE. With a 10-power attacker that is any card in the top six, every turn — CA and cheat (O28) scaling with the body. Colourless; MV 5 (F3). |
| Dawnsire, Sunstar Dreadnought | ★★ | ★★ | `{5}`: one 10-power station tap = 100 damage to a creature on every attack; one 20-power tap = a 20/20 flier (O37). The user's insight is right and it costs the body's attack that turn. Colourless. |
| Cloud, Midgar Mercenary | ★ | ✗ | `{W}{W}` 2/1: ETB tutor an Equipment (Boots, Shield); equipped, his and his Equipment's triggers double. WW at two is 45% (F7). ★★★ in the equipment plan. |
| Catharsis | ★ | ★ | Evoke `{R/W}{R/W}` with RR: creatures +1/+1 and HASTE, then sacrificed — a two-mana team haste grant (Speed on, a warped Colossus swings). The user's read is right; it is a creature spell, so Cyclops does not trigger (F4). Hardcast 6 is F3. |
| Windcrag Siege | ★ | ✗ | Mardu: attack triggers of your permanents fire twice — Cosmic Cube, Dawnsire, Daredevil, Hawkeye, Sozin's firebending (RRRRR ×2). ★★ once the deck holds three of those; today it doubles Scalestorm alone. |
| Aettir and Priwen | ◇ | ◇ | `{6}` equip `{5}`: base P/T = your life total. 11 mana honestly, or `{6}` + Kíli / Serum / Blacksmith L2. The user's condition is right — equipment-plan only. |
| Spider-Verse | ◇ | ◇ | Copy a spell cast from anywhere but hand, once a turn: Bulk Up's flashback, every Plot and warp recast, Hex Magic's exile, Cosmic Cube's cast. The CHEAT plan's copy engine (★★ in 56b); one flashback in 56. |
| Zidane, Tantalus Thief | ◇ | ✗ | MV 5 ETB Threaten with lifelink + haste; Self-Destruct the stolen body (O9). |
| Fire-Rim Form | ◇ | ◇ | `{1}{R}` flash Aura: +2/+0 permanent, first strike the turn it lands. A Ransacking that stays. |
| Chimil, the Inner Sun | ◇ | ◇ | `{6}`: uncounterable + a free ≤5 card every end step. Cheat-plan CA (★★ there). |
| Extinguisher Battleship | ◇ | ◇ | `{8}`: ETB destroy a noncreature permanent + 4 to EACH creature (one-sided under Crystal Barricade, O33). Tannuk warps it for `{2}{R}` as a 3-mana Vindicate-sweeper (★★ in 56b). |
| Bifur, Melodic Rider | △ | △ | MV 6 counter-on-enter/attack; Dwarf doubling with no Dwarves. |
| Firebender Ascension | △ | △ | Copies an attacking creature's own trigger after four — 56 has one such trigger (Scalestorm). |
| Thunderhead Gunner | △ | △ | MV 5 body with a sorcery-speed loot. |
| Ultima Weapon | △ | △ | `{7}` equip `{7}`: +7/+7 and destroy a creature on attack. Fourteen mana; equipment-plan only. |
| Meteor Sword | △ | △ | `{7}` Vindicate on a +3/+3 stick. Tannuk-warpable for the ETB. |

### Batch 10 (21 cards — FINAL)

| Card | 56 | 56a | Note (framework rule) |
|---|---|---|---|
| Choreographed Sparks | ★★★ | ★★★ | `{R}{R}` instant, one OR BOTH: copy your instant/sorcery (Bulk Up ×4, Self-Destruct 2X) / copy your creature SPELL as a hasty token (a second Stingerback that swings now and dies at end step — Self-Destruct it free, O3). Return the Favor's copy half, cheaper, plus a body mode. Can't be copied itself. |
| The Fire Crystal | ★★★ | ★★★ | `{2}{R}{R}`: red spells cost `{1}` less, creatures have HASTE, and a hasty copy on tap (O43). The T4 play that makes the T5 kill cast the whole hand. |
| Frontline Rush | ★★ | ✗ | `{R}{W}` instant: +X/+X where X = your creatures (or two Goblins). Reckless Ransacking's slot, better at three or more bodies, single-target (Spinerock copies it). Owned ×2. |
| Peter Parker's Camera | ★★ | ★★ | `{1}`, three charges: `{2},{T}` copy an activated OR triggered ability — Iron Fist's tap (2X), Dawnsire's 100, Hawkeye, Bre, Molten Man's ETB (a second Mountain), Seedglaive's counter. Ertha Jo for one mana, any ability, three times. |
| Ertha Jo, Frontier Mentor | ★★ | ✗ | `{2}{R}{W}` 2/4 + a Mercenary; copies every activated ability that targets (O42): Mercenary taps, Iron Fist, Patriot, Key, Bre. The user's sub-theme read is right; MV 4 (F3) and sorcery-speed tokens. |
| Dalkovan Encampment | ★★ | ✗ | LAND: `{W}`, enters UNTAPPED if you control a Mountain (13 here) — the W source the manabase wants without a tapland (F7); `{2}{W},{T}` two attacking 1/1s (Team Avatar's enemy, Terror's fodder). |
| Seifer Almasy | ★ | ★ | `{3}{R}` 3/4: the creature attacking ALONE gains double strike (F2 = 0 today; the one-card replacement for the four DS grants being cut); Fire Cross recasts a ≤3 spell from the yard when HE connects. ★★ in the post-cut list. |
| Rodeo Pyromancers | ★ | ★ | `{3}{R}` 3/4 Mercenary: first spell each turn → RR (O35). The kill turn's mana on a body; MV 4. |
| Brimstone Roundup | ★ | ★ | `{1}{R}` (plot `{2}{R}`): a Mercenary per second spell each turn. The sub-theme's cheapest engine (O42). |
| Hell to Pay | ★ | ★ | `{X}{R}` sorcery: X to a creature, Treasures for the excess (W fixing). Creature-only. |
| Improvised Arsenal | ★ | ★ | `{1}{R}` equip `{R}`: +1/+0 per artifact you control — 3–4 in the tuned list (G-83: the count decides); copies itself for `{4}{R}`. |
| Mica, Reader of Ruins | ★ | ★ | `{3}{R}` 4/4 ward-3-life; sac an artifact to copy each instant/sorcery — Treasures and Walls are the fuel. |
| Devastating Onslaught | ★ | ★ | `{X}{X}{R}`: X hasty token copies of your creature, gone at end step. Copies keep copiable values only (no pumps, no counters): Stingerback ×2 for five mana, Cyclops copies that each grow per spell. Self-Destruct on a token is free. Legend rule kills Molten Man / Sentry copies. |
| Sword of Wealth and Power | ◇ | ◇ | +2/+2, PROTECTION FROM INSTANTS AND SORCERIES, Treasure + copy-next-spell on damage. Reads like the pile's best protection and is a G-42 card (O41): Bulk Up cannot target the equipped body. Only for an ability-pumped body. |
| Form a Posse | ◇ | ✗ | `{X}{R}{W}` X Mercenaries (O42). Sorcery, go-wide. |
| Hellspur Posse Boss | ◇ | ◇ | Two Mercenaries + outlaw haste, `{2}{R}{R}` 2/4. |
| Adagia, Windswept Bastion | ◇ | ◇ | Tapped W land; station 12+ → copy Pain for All / Ferocification / Boots as legendary. A fifth tapland. |
| Calamity, Galloping Inferno | ◇ | ◇ | MV 6: saddle with Stingerback, attack with two attacking token Stingerbacks. F3. |
| Hellspur Brute | △ | △ | 5/4 trample for five minus outlaws. |
| An Unexpected Party | ✗ | ✗ | `{2}{W}{W}` type anthem (F7) / X Dwarves. Go-wide. |
| Chandra, Flameshaper | ✗ | ✗ | MV 7 (20% on T7). Her +1 is a hasty body copy each turn — for a deck two turns slower than this one. |

## 5. Consolidated plan (FINAL — 201 cards read; propose, do not apply)

### 5.0 The decisions the plan hangs on (answer these first)

1. **Sentry or Crystal Barricade** for the free Self-Destruct (O16 / O33): Sentry is an
   evasive body that also wins; Barricade is a 2-mana wall that also blocks the Void and
   costs Pain for All's reflect. Both is fine; neither is not.
2. **Spinerock or Twinflame** for the ONE MV-5 slot (O38): Spinerock for combat-tall (A1),
   Twinflame for fireball-tall (A2). The deck cannot hold both at 24 lands.
3. **White sources: 11 or 13.** Sacred Foundry is a Mountain-Plains, so `−2 Mountain +2
   Sacred Foundry` adds two W sources at ZERO Molten Man cost (F8) and enters untapped. At
   13 W, Grand Abolisher and Avatar's Wrath are real cards (WW 71% by T6 → ~80%); at 11
   they are not. Dalkovan Encampment (untapped W beside a Mountain) is the third W source
   if wanted, in Abraded Bluffs' slot.
4. **A1 or A2 tilt** — decides the last four slots (§5.2).

### 5.1 The core package — 10 cuts, 10 adds, both tilts share it

| # | CUT | why cuttable | ADD | why |
|---|---|---|---|---|
| 1 | Twin Blades | DS #5–6 of 9, 3 MV artifact (F2) | **Pain for All** | reach engine; Self-Destruct 2X (O12) |
| 2 | Twin Blades | " | **Stingerback Terror** | 7/7 flying trample, grows as you cast (O21) |
| 3 | Reckless Ransacking | Pw 1.5, +3/+2 is small here | **Frontline Rush** | +X/+X instant for 2, single-target |
| 4 | Reckless Ransacking | " | **Delney** | Cyclops +6/spell, Speed / Hawkeye / Iron Fist ×2; pre-pump evasion (O39) |
| 5 | Team Tactics (1 of 2) | DS #3–4; keep one for the trample rider | **Choreographed Sparks** | Bulk Up ×4 or a hasty second body (O44) |
| 6 | Rabid Gnaw (1 of 2) | keep one; Giantfall is the virtual copy | **Swiftfoot Boots** | permanent hexproof + haste (F6a, O2) |
| 7 | Tiger-Dillo | `cuts` #1: a body gated on power 4 that adds nothing to F1 | **Enter the Avatar State** | `{W}` hexproof + flying |
| 8 | Go Ninja Go | `cuts` #2; blink RESETS pumps and counters (G-42), damage half is creature-only | **The Sentry** *or* **Crystal Barricade** | free Self-Destruct (decision 1) |
| 9 | Scalestorm Summoner | power-4 gate; tokens are off-plan for attack-alone | **The Fire Crystal** | red spells −1, team haste, a copy (O43) |
| 10 | Haste Magic (1 of 2) | Fire Crystal + Boots + Ferocification carry haste now | **Spinerock** *or* **Twinflame Tyrant** | the MV-5 slot (decision 2) |

Measured effect of the core (scratch copy, `quality --vs`): to be run on the user's picks —
the pre-pile 4-swap package measured protection 3 → 7, interaction 7 → 8, avg MV 2.42 →
2.31, floor A → A with the guard clean; this package moves more and should be re-measured
before applying, per G-34.

**Duplicates after the core:** 2-ofs drop from 14 cards to 9 (Molten Man, Cyclops,
Vindicator, Seedglaive, Speed, Boros Charm, Bulk Up, Self-Destruct, Agni Kai) — the
user's original ask — and every remaining pair is either a body the deck wants to see
early or a card the deck wants twice (Bulk Up, Self-Destruct).

### 5.2 The tilt slots — four more, by plan

**A1 COMBAT-tall** (one connected swing): −Boros Charm ×1, −Vindicator ×1, −Mai,
−Celestial Armor → **Ferocification** (menace + haste every combat), **Team Avatar**
(+X/+X attacking alone), **Grand Abolisher** (the kill-turn lock — needs decision 3),
**Energybending** (Molten Man pump + WW fix + draw). Return the Favor if a fifth opens.

**A2 FIREBALL-tall** (the power goes face): same four cuts → **Iron Fist** (repeatable
power-to-face), **Peter Parker's Camera** (copy Iron Fist's tap, 3×), **Twinflame** if not
already taken (else **Collective Inferno** on Human), **Restoration Magic** (instant
indestructible for the sweeper case Barricade does not cover). Ertha Jo if a fifth opens.

### 5.3 Manabase (no spell slots)

- `−2 Mountain +2 Sacred Foundry` — W 11 → 13, R 18 → 18, Molten Man unchanged (Foundry
  is a Mountain), untapped for 2 life. **Do this regardless of tilt.**
- `−1 Abraded Bluffs +1 Rogue's Passage` — unblockable from a land; costs one W and one R
  source, so only after the Foundries.
- `−1 Temple of Triumph +1 Daily Bugle Building` — menace for a legendary + any-colour
  filter; or Dalkovan Encampment here for a fourth untapped W.
- The Lonely Mountain replaces a basic Mountain at zero F8 cost once Boots/Shield are in.

### 5.4 PROTECT — what `cuts` will rank wrongly after the swaps

- **Self-Destruct ×2** — `burn`, reach, the win condition (E1).
- **Bulk Up ×2** — the multiplier; every copy effect keys on it.
- **Molten Man ×2** — Mountain-scaled; a printed 0/0 that `cuts` cannot size.
- **Crackling Cyclops ×2** — a printed 0/4; with Delney +6 per spell (O14, O39). `cuts`
  calls it "low power".
- **Speed ×2** — the only unblockable GRANT; haste-gated and now always on (O2).
- **Seedglaive Mentor ×2** — valiant is fed by every targeted add.
- **War Machine** — Delney doubles his combat trigger.
- **Pain for All / Delney / Fire Crystal / Barricade / Boots** — every one scores ZERO
  roles (O45) and will sit at the top of the next `cuts` run.
Write these into `#: protect:` with the apply.

### 5.5 Plan B — 56b CHEAT-TALL: DECISION

**DRAFTED 2026-09-05 as `decks/56-boros-tall/56b-ball-lightning.txt` (mono-R, 37+23,
tier B PROVISIONAL, preflight READY, `similar`: closest by cards is 26 at 5 shared).** The
re-screen of the rejected pile against the drafted list moved Goliath Daydreamer IN over
Memorial Team Leader (KEY: every instant cast from hand recurs free on his attack; Spider-Verse
copies it). Still homed in 56, not here, by choice: Crackling Cyclops (KEY on screen — it
wants 56's 14 instants), Pain for All / Iron Fist (56c's), Spinerock (56's MV-5 slot).

The original decision text: **Draft it.** The pile holds a complete, DISTINCT deck: engine (Tannuk, Warped Space,
Fire Crystal, Sami, Kíli), bodies that arrive for less than printed (Bygone Colossus,
Anticausal Vestige, Nova Hellkite, Ball Lightning, Red Tiger Mechan, Hill Gigas / Zog /
Lorecaster / Stone-Giant via Tannuk, Stingerback and Ruckus via Plot, Extinguisher
Battleship's ETB), payoffs (Terror of the Peaks, Doc Ock's Tentacles, Cosmic Cube,
Nexus, Spider-Verse, Chimil, Sire as a Vestige/Nexus target), free finishers
(Self-Destruct on a leaving body, Twinflame), Hex Magic + Warped Space for gas. It shares
Molten Man / Cyclops / Speed / Bulk Up / Self-Destruct with 56 and nothing with 38 / 74
(those are equipment decks; this is a WARP deck). Distinctness check before drafting:
`deck.py similar` against 56, 26 (Iron Forge runs Vestige / Nexus / Colossus) and 45.
Protection is the open question — Boots for the swing turn, Abolisher if white, otherwise
the plan IS the protection (bodies leave before a sorcery-speed answer). `/draft-deck`.

**Not drafting:** an Equipment-tall 56c (O8 — borrow Boots / Shield / Mjölnir into 56 and
56a instead; 38 and 74 own that space) and a Mercenary 56d (O42 — a sub-theme, four cards,
not a deck).

### 5.6 56a — Executioner's Song (RG) picks

**APPLIED 2026-09-05 via /tune-deck 56a → /apply-changes (user-confirmed):** −Twin Blades
+Boots · −Molten Man ×2 +Pain for All +Mjölnir · −Ransacking +Demonic Ruckus · −Gnaw
+Giantfall · −Crackling Cyclops +Spinerock Tyrant (user chose Cyclops over Red Hulk as the
cut). Measured: interaction 4→5, protection 4→5, floor C→B, guard clean, rationale
re-grounded. Open: Stomping Ground ×2 (craft) for the eight taplands; Railway Brawler's
library undercount (G-10).


★★★: Pain for All, Mjölnir (8 worthy carriers), Spinerock Tyrant, Twinflame Tyrant,
Choreographed Sparks, Fire Crystal, Swiftfoot Boots. ★★: Stingerback, Dragonclaw Strike
(4 mana in RG), Bulwark Ox, Brambleback Brute (Halana reloads it), Ferocification,
Energybending, Demonic Ruckus, Iron Fist, Cosmic Cube / Dawnsire, Sozin's Comet, Soul
Immolation, Hex Magic. 56a's stated gap is counters PAYOFF (10 enablers, 0 payoffs) — the
pile holds none; its interaction is 4 at a C floor, so Giantfall / Wisecrack / Dragonclaw
Strike's fight are the honest interaction adds. A separate `/tune-deck 56a` pass with this
list as input.

### 5.7 Tooling holes found by the read (Stage 4 — fix as ONE batch, roster-diffed, K-12)

1. `classify_roles` → no role: **Return the Favor** ("change the target of target spell"
   = redirect / protection-class; "copy target instant" = multiplier), **Choreographed
   Sparks** (copy), **Pain for All** (reach), **Iron Fist** (reach on an activated grant),
   **Infernal Phantom** (reach on death), **Twinflame Tyrant** / **Collective Inferno** /
   **Mjölnir** (damage doublers — `doubler_support` has no DAMAGE axis), **Grand Abolisher**
   / **Jennifer Walters** / **Voice of Victory** (a lock is protection-class), **Delney**
   (a trigger doubler that `suggest-homes` already sees — `✱ multiplier, 7 feeders` — but
   `classify_roles` does not).
2. `stats` reach count: Self-Destruct is the only `burn`-tagged reach; the "power to any
   target" family (Pain for All, Iron Fist, Phantom, Red Hulk's enrage, Stone-Giant's sac)
   is unindexed — O20.
3. No model reads a MOUNTAIN COUNT as a resource (Molten Man, Energybending, Zhao, Sacred
   Foundry's typing) — F8 is a hand rule; G-83's cost-scale family is the nearest shape.
4. `screen` labels: 36 of 39 structurally-valued cards read "tangential" (O45) — G-31's
   residual, re-measured on this pile.
6. WARP / PLOT / FORETELL alternative costs are invisible to `avg_mv` and `_clock_score`
   — Bygone Colossus (warp `{3}`) prices at 9 and moved the aggro floor A → B on its own
   (§5.9 review). The G-60 X-spell under-read, in reverse: an OVER-read of a cheat-cost
   body. Report-only fix, same discipline (a new term in `tier_band` re-grades the roster).
5. Haste-GATED evasion (Speed) and attack-ALONE conditions (Luke Cage, Team Avatar, Seifer)
   are invisible to `count_conf` / `targets` — the G-76 state-gate family, two new members.

### 5.9 THE MEASURED REBUILD (user widened the cut budget 2026-09-05: any 2-of, Cyclops, Tiger-Dillo, Become Brutes, Gnaw, clear upgrades)

20 cuts / 20 adds + 3 land swaps, built on a scratch copy and measured. Combat-tall tilt
with Sentry AND Barricade, Spinerock in the MV-5 slot, 13 W sources.

**CUTS (20):** Twin Blades ×2, Reckless Ransacking ×2, Rabid Gnaw ×2, Crackling Cyclops ×1,
Swiftblade Vindicator ×1, Seedglaive Mentor ×1, Speed ×1, Boros Charm ×1, Team Tactics ×1,
Haste Magic ×1, The Last Agni Kai ×1, Tiger-Dillo, Scalestorm Summoner, Go Ninja Go,
Become Brutes, Celestial Armor, Mai. **Kept at 2:** Molten Man (legend-rule redundancy on
the signature body), Bulk Up, Self-Destruct.

**ADDS (20):** Pain for All, Stingerback Terror, The Sentry, Spinerock Tyrant, Delney,
Iron Fist, Grand Abolisher, Crystal Barricade, Swiftfoot Boots, Enter the Avatar State,
Restoration Magic, Ferocification, Demonic Ruckus, Giantfall, Frontline Rush, Team Avatar,
Choreographed Sparks, Return the Favor, Energybending, The Fire Crystal.

**LANDS:** −2 Mountain +2 Sacred Foundry; −1 Temple of Triumph +1 Dalkovan Encampment.
W 11 → 13, R 18 → 17, Mountains for Molten Man 13 → 13 (Foundry is typed), basic
Mountains for his fetch 13 → 11.

**Measured (scratch, `quality --vs` the pre-pile baseline):**

```
interaction     7 → 4  (+1?)   ← Gnaw ×2, Go Ninja Go, Agni Kai ×1 out; Giantfall in
card advantage  2 → 1          ← Key's draw mode was the 2nd; Energybending/Ruckus cantrip
protection      3 → 6
avg MV       2.42 → 2.58       (1 five-drop, 1 six-drop)
tier floor      A → A          (aggro clock 6/7 substitutes; guard: SOFT, intentional)
shape        TALL 8 → TALL 7, evasive 10 → 13
2-ofs      14 cards → 3 (Molten Man, Bulk Up, Self-Destruct)
legal ✓ · resolve --check ✓ · castability ✓ · Molten Man fetch: 11 basics
```

The interaction drop is the honest cost: four creature-only removal spells left and the
deck now answers a board by going over or through it (Pain for All / Iron Fist /
Self-Destruct are reach the counter cannot see, O20). Giantfall restores one instant
answer AND the first noncreature-permanent answer. If that reads too thin, the next
interaction adds are Wisecrack and the second Agni Kai back in for Key-class cards.

**Castability flags (13 W / 17 R):** Grand Abolisher WW 56% on T2 / ~65% on T4 — the one
real cost; Jennifer Walters (`{1}{W}`, 89%) is the swap if it bites. Sparks / Return the
Favor RR 73% on T2, fine by T4.

**`cuts` on the rebuilt list ranks Return the Favor, Giantfall, Abolisher, Frontline Rush,
Delney, Team Avatar and Pain for All as its seven weakest** — every one a zero-role engine
card (O45). The `#: protect:` line for the apply must carry them.

**The proposed file (nonland + lands):**
```
# Tall bodies
2 Molten Man, Inferno Incarnate (SPM) 84
1 Crackling Cyclops (FDN) 83
1 Red Hulk (MSH) 149
1 Stingerback Terror (OTJ) 147
1 The Sentry, Golden Guardian (MSH) 35
1 Spinerock Tyrant (ECL) 159

# Bearers / engines
1 Swiftblade Vindicator (FDN) 246
1 Seedglaive Mentor (BLB) 231
1 War Machine, Legacy of Iron (MSH) 238
1 Speed, Young Avenger (MSH) 152
1 Delney, Streetwise Lookout (MKM) 12
1 Iron Fist, Living Weapon (MSH) 138
1 Grand Abolisher (BIG) 2
1 Crystal Barricade (FDN) 7

# Evasion / protection
1 Boros Charm (FDN) 721
1 Swiftfoot Boots (BRR) 58
1 Enter the Avatar State (TLA) 18
1 Restoration Magic (FIN) 30
1 Ferocification (OTJ) 123
1 Demonic Ruckus (OTJ) 120
1 Giantfall (ECL) 141

# Multipliers and tricks
2 Bulk Up (SOA) 40
1 Team Tactics (MSH) 155
1 Haste Magic (FIN) 140
1 Frontline Rush (TDM) 186
1 Team Avatar (TLA) 38
1 Choreographed Sparks (SOS) 111
1 Return the Favor (SOA) 47
1 Energybending (TLA) 2
1 The Fire Crystal (FIN) 135

# Finisher / removal (power-scaled)
2 Self-Destruct (FIN) 157
1 The Last Agni Kai (TLA) 144
1 Pain for All (EOE) 151

# Lands
1 Sunbillow Verge (DFT) 264
1 Abraded Bluffs (OTJ) 251
1 Inspiring Vantage (OTJ) 269
1 Elegant Parlor (MKM) 260
2 Sacred Foundry (EOE) 256
1 Dalkovan Encampment (TDM) 253
11 Mountain (MSH) 293
6 Plains (MSH) 287
```

**User review of §5.9 (2026-09-05) — three points, answered:**
1. *Vindicator and Speed.* The rebuild cut ONE copy of each, not both (both stay at 1). Both
   second copies are fine keeps — Vindicator is the deck's best delivery bearer (E6: DS +
   trample is near-unblockable ×2, and Delney makes a 1-power attacker unblockable by ≥3) and
   nonlegendary; Speed is the unblockable GRANT, legendary (two on the table is a legend-rule
   choice, two in the deck is finding it earlier). If both return, the two weakest adds go:
   Giantfall (the interaction restore the user may not weigh) and Frontline Rush (the +X/+X
   trick; Team Avatar does it repeatably). Recommended: keep 2 Vindicator, 1 Speed.
2. *Were cuts made with a variant in mind?* **No.** Every cut was graded on 56's list
   alone. No cut was needed to free a card for 56b — decks share the collection (a card is
   never consumed by a deck), so a Cyclops in 56 is also a Cyclops in 56b. The user's point
   stands anyway: building the variant FIRST shows which cards are better HOMED there
   (Cyclops, Tannuk's warp bodies, Ball Lightning), and that clarifies what 56 keeps. **Order
   of work: `/draft-deck 56b` → `/tune-deck 56a` with §5.6 → finalize 56.** §5.9 is a
   proposal that waits.
3. *Cut both Molten Man.* Agreed on the merits: a 3-drop that is ~4/4 on T3 and grows one a
   turn, dies to everything, and SACRIFICES A LAND on leaving — behind Stingerback (7/7
   flying trample for 4, or 3 via Plot) and Sentry as the deck's tall body. Cutting him
   RETIRES F8 (the Mountain-count rule): Rogue's Passage / Daily Bugle can now replace
   Mountains freely, Energybending loses its pump mode (still a colourless cantrip that fixes
   WW), Zhao / Lonely Mountain / the basic-fetch target gate become irrelevant.
   **The two cards in — two options, measured:**
   - **A: Bygone Colossus + Luke Cage** (two BODIES, keeps 15 creatures). Colossus: with
     The Fire Crystal on the table it is a 9/9 HASTE for `{3}` on T4, and Barricade /
     Self-Destruct make it a free 9 to the face when it leaves. Luke Cage: indestructible
     when attacking ALONE — the pattern Team Avatar pays, the body Self-Destruct spares, no
     Void. Measured: protection 6 → 7, interaction 4, avg MV 2.58 → **2.78 and the floor
     A → B** — an ARTIFACT of Colossus's printed MV 9 (the clock score reads printed cost;
     warp `{3}` is invisible to it — O28 / G-60's shape in reverse). The deck did not get
     slower; the number did. Tooling item 6 for §5.7.
   - **B: Luke Cage + Hawkeye** (or Daredevil): no MV distortion; Hawkeye is blocker
     removal + reach + the deck's only repeatable loot, Delney-doubled (six payments), but
     he ATTACKS — Team Avatar / Luke Cage want him home (O22). Daredevil is the attack-alone
     -compatible CA (his trigger is "whenever you attack", he can stay home… no — he must
     be the attacker; same conflict, milder: vigilance haste 3/4).
   **Recommended: A**, with the floor reading disclosed. **User leans A (2026-09-05).**

### 5.10 Variant inventory — every cluster the pile surfaced, with its roster home

Decision rule: a cluster is a NEW deck only if it has an engine AND payoffs the pile
supplies (G-59: payoff count, not body count) AND no roster deck already owns the space.
Cards are never consumed by a deck, so "home" means where the cluster's IDENTITY lives, not
where its cards may be played.

| # | Cluster | Pile depth | Roster home today | Verdict |
|---|---|---|---|---|
| 1 | **WARP / cheat-tall** (O3, O11, O19, O28) — Tannuk, Warped Space, Fire Crystal, Sami, Kíli; Colossus, Vestige, Hellkite, Ball Lightning, Mechan, Gigas/Zog/Lorecaster/Stone-Giant via Tannuk; Terror, Tentacles, Cube, Nexus, Chimil, Spider-Verse; Self-Destruct free | ~25 | **none** — 26 Iron Forge (UR artifact RAMP into big hitters; runs Vestige/Nexus/Colossus/Tannuk) and 45 The Exiles (WBR cast-from-exile PAYOFF) are the neighbours; 56b's thesis is the BODY is temporary, not the cast is rewarded | **NEW DECK — 56b.** `similar` against 26 and 45 before drafting. |
| 2 | **FIREBALL-tall** (O20, O16, O33) — Pain for All, Iron Fist, Phantom, Self-Destruct, Sentry / Barricade / Luke Cage as survivors, Twinflame, Collective Inferno, Mjölnir, Taii, Camera, Ertha Jo, Wisecrack, Soul Immolation, Red Hulk, Stone-Giant's sac | ~16 | **none** — 49 Big Draco runs Twinflame/Inferno as Dragon burn; nothing wins by pointing a creature's power at the face | **NEW DECK candidate — 56c** ("the body never attacks"). Distinct from 56 by win condition, shares its pump suite. Second priority after 56b. |
| 3 | **EQUIPMENT-tall** (O6, O8, O26) — Boots, Shield, Mjölnir, Katana, Genji Glove, Blacksmith's Talent, Kíli, Serum, Cloud, Aettir, Ultima, Buster Sword, Sword of W&P, Arsenal, Thorin, Stalwart, Gilgamesh, Item Shopkeep | ~19 | **taken three times**: 38 Armory (WB voltron), 74 Iron Hills Forge (WR Dwarf/Equipment triggers), 39 Starforge (runs Katana, Gilgamesh, Genji Glove, Buster Sword, Mjölnir, Cloud, Sami) | **Borrow, don't build.** Boots / Shield / Mjölnir into 56 and 56a; the rest are 38/39/74 adds. |
| 4 | **MERCENARY** (O42) — Ertha Jo, Posse Boss, Form a Posse, Brimstone Roundup, Tycoon, Rodeo Pyromancers, Hellspur Brute, Old Hob | ~8 | **73a Duke's Vigil — Hired Guns IS the Mercenary-token deck** (it already runs Ertha Jo, Posse Boss, Form a Posse, Roundup, Adagia, Old Hob) | **Exists.** These are 73a adds; in 56 a sorcery-speed sub-theme of 2–3 cards at most. |
| 5 | **COPY / spellslinger-tall** (O44) — Sparks, Return the Favor, Spinerock, Camera, Mica, Goggles, Spider-Verse, Wrangler, Sword of W&P, Buster Sword + the prowess bodies (Student, Immolator, Ty Lee, Thor, Monica, Cyclops, Mai) | ~17 | 57 Tempest (RWU prowess tempo), 33 Fighting Spirit (UR haste/DS/pump), 25 Spellstorm | **Taken.** The copy engines are 56 adds (Sparks, Return the Favor, Spinerock in the rebuild); the prowess bodies are 57/33's. |
| 6 | **STATION** (O37) — Dawnsire, Frigate, Seriema, Gunship, Sweeper, Sawship, Kill-Ship, Battleship, Adagia | ~9 | none, and it cannot stand alone: it needs a tall body as the station source | **Sub-plan** of 56 or 56c (Dawnsire + Frigate, two slots), not a deck. |
| 7 | **CAST-FROM-EXILE** — the Plots (Stingerback, Ruckus, Longhorn, Roundup), foretell (Comet), Hex Magic, Daydreamer, Warped Space, Charred Foyer, Lightning / Raphael impulse, Spider-Verse | ~12 | **45 The Exiles** (WBR — gets PAID for casting from exile) | **Exists** for the payoff half; the temporary-BODY half is cluster 1. |
| 8 | **GIANTS** — Stoneback, Walker, Curious Colossus, Brute, Hurler, Bre, Cindermaw, Daydreamer, Iron Giant, Bygone Colossus, Lorecaster, Hill Gigas, Pulverizer, Stone-Giant, Boldwyr | 15 bodies | none | **Not a deck (G-59): ONE payoff** (Boldwyr Aggressor, a DS lord — and DS is worth 0 here). Fifteen bodies with one card that cares is the Mutant shape. |
| 9 | **MENACE / evasion** (O32); **KILL-TURN LOCK** (O24); **ATTACK-ALONE** (O22, O40); **HASTE-as-enabler** (O2, O10); **REPEATABLE unblockable** (Key, Passage, Bugle) | 3–12 each | — | **Sub-clusters of 56 itself** — they are what the rebuild is made of. |

**Overlaps that matter:** 1 ∩ 3 (Sami's affinity, Kíli, Tannuk warps artifacts — an
ARTIFACT-warp 56b is one build of cluster 1); 1 ∩ 2 (Self-Destruct free on a leaving body
is both); 2 ∩ 6 (a fireball body that never attacks is the ideal station source); 4 ∩ 2
(Ertha Jo copies Iron Fist). **The roster is at 117 files against Arena's 100-deck cap**
(`.cycle/prune-analysis.md` is live) — each new deck is a prune somewhere else, which is
one more reason clusters 3–5 and 7 stay as adds to the decks that own them.

**So: two new decks (56b warp, 56c fireball), one retune (56a), four "these are adds to
an existing deck" lists (38/39/74, 73a, 57/33, 45), one refusal (Giants).** Recommended
order: `/draft-deck 56b` → `/draft-deck 56c` (or fold 56c's core into 56 as tilt A2 and
skip it) → `/tune-deck 56a` → finalize 56.

### 5.11 56c as a FILE vs 56's A2 TILT — measured (2026-09-05)

**56c sketch (RW, 36 + 24 on the rebuilt 56 manabase, plan midrange):** survivors Sentry /
Luke Cage / Hazoret / Crystal Barricade / Red Hulk / Iron Fist / Infernal Phantom / Grand
Abolisher / Ertha Jo; pumps Bulk Up ×2, Frontline Rush, Haste Magic, Full Bore, Lightfoot,
Shardmage's Rescue; reach Self-Destruct ×2, Pain for All, Wisecrack, Gnaw, Agni Kai,
Giantfall; doublers Twinflame, Collective Inferno, Mjölnir; amplifiers Camera, Taii, Return
the Favor, Sparks; protection Boots, Restoration Magic, Avatar State; CA Hex Magic,
Energybending, Ransacking. Measured: legal ✓, interaction 5 (2 answer noncreature
permanents), protection 9, avg MV 2.53, floor B on midrange, shape TALL 8, 11 creatures.
Closest by cards: 56a at 7 shared; against the REBUILT 56 it would share ~17.

**What each is:**
- **A2 tilt** = four slots in 56 (Iron Fist, Camera, Twinflame-or-Inferno, Restoration
  Magic) at the cost of Ferocification / Team Avatar / Abolisher / Energybending. It gives
  56 a fallback when the swing is blocked; it does NOT give it a second win condition — the
  body still has to live AND attack, so Luke Cage / Hazoret (can't attack) and the
  never-attack doublers are wasted there. Four slots buy a hedge.
- **56c file** = the fireball as the PLAN: the body never attacks, so "attacks alone" /
  "can't attack" / summoning sickness stop mattering, Barricade's prevention and Sentry's
  indestructible make Self-Destruct free every turn, Iron Fist's tap is the repeatable
  finisher, and Twinflame / Inferno / Mjölnir / Camera / Ertha Jo / Taii multiply it.
  Chump blockers, first strike, flash blockers, fog effects are all irrelevant. Its honest
  weaknesses: interaction 5 (creature-only bar Giantfall / Boots-class answers to its own
  engine), a B floor on midrange, and it is ~17 cards away from the rebuilt 56 — distinct
  by WIN CONDITION, not by list, which is the same relation 56a has to 56.

**Recommendation:** skip the A2 tilt (a four-card hedge is the worst of both); keep 56
combat-tall with Pain for All + Self-Destruct as its natural reach (already in the
rebuild); build 56c as a file ONLY if the fireball plan is one you want to PLAY — it costs
a slot against the 100-deck cap and half its list is 56's.

### 5.12 56b — pile cards NOT in the drafted list that fit it (sweep 2026-09-06)

Method: all 201 pile names − 56b's 37, kept mono-R-castable and Standard-legal (118), screened
against 56b, then graded from the per-batch text and O3 / O11 / O19 / O28 / O37 / O44.
**The recurring caveat is Tannuk-dependence**: one Tannuk is in hand by T4 17% of the time,
two copies 31% — so every "warps under Tannuk" body below is a bet on him unless it has its
own cheat cost.

**★★★ (would go in today):**
- **Cosmic Cube** — every attack, cast a card from the top six with MV ≤ your greatest
  attacking power free: a warped 9/9 Colossus swinging = any card. The cheat plan's CA.
- **Twinflame Tyrant** — doubles every damage source to the opponent (Terror's throws,
  Weftstalker's pings, Self-Destruct's face half, combat). Competes with Terror / Spider-Verse
  for the MV-5 slots.
- **Devastating Onslaught** — `{X}{X}{R}`: X hasty token copies of a creature, gone at end
  step. On a warped Colossus that is X extra 9/9 haste bodies AND X free Self-Destruct targets.
- **Hazoret, Godseeker** — 5/3 INDESTRUCTIBLE haste for two that "can't attack or block
  unless you have max speed": as a body that never needs to attack, she survives her own
  Self-Destruct every turn (O16), and max speed arrives fast in a deck pinging each turn.

**★★ (in with a Tannuk or a slot):**
- **Combustion Man** — Tannuk warps a 4/6 for `{2}{R}`; attacks with haste; "destroy target
  permanent unless its controller has him deal damage to them equal to his power".
- **Zealous Lorecaster** — Tannuk warp: 4/4 haste that regrowths Bulk Up / Self-Destruct, and
  re-exiles to do it again. **Extinguisher Battleship** — Tannuk warp as an ARTIFACT:
  Vindicate + 4 to each creature; the Spacecraft is not a creature and survives its own ETB
  (Hellkite / Ardent / Mechan do not — G-42 half). **Zog** — Tannuk warp 5/4 + ETB can't-block.
  **Stone-Giant** — Tannuk warp 7/7 + a Wall + `{2}{R}` sac-an-artifact for 4.
- **Chimil, the Inner Sun** — discover 5 every end step: a warp body discovered is cast for
  free and STAYS. MV 6. **Sozin's Comet** (KEY) — RRRRR per attacker for the combat's tricks.
  **Spinerock Tyrant** — copies Bulk Up / Self-Destruct / Full Bore / Haste Magic; MV-5 slot.
  **Dawnsire** (O37) — station with a warped 9/9 on the turn it would otherwise attack.
  **Pigment Wrangler** (KEY) — Tannuk warps a 4/4 flier that arrives with a copy spell.

**★ (real, slot-dependent):** Pain for All (a 3-mana "9 to the face" on a leaving Colossus;
the Aura's second clause is lost), Nexus of Becoming (a Terror copy is a 3/3 flier WITH the
trigger; a Colossus copy is a vanilla 3/3), Pyromancer's Goggles, Firebending Student /
Ty Lee (KEY — evasion and mana bodies), Diary of Dreams (KEY), Wisecrack / Hell to Pay
(interaction beyond burn), Maximum Carnage, The Arkenstone's `{5}` half (the Adventure is
`{2}{W}` — off-colour; only the artifact casts here), Iron Fist, Ferocification.

**Not for 56b despite the pile:** Crystal Barricade / Sentry / Abolisher / Delney (white),
Mjölnir (three worthy carriers here), Energybending (nothing to fix, no Molten Man),
Gingerbrute / Key / Passage (Speed's rider already covers evasion), Brimstone Roundup /
Hellspur Brute / Racers' Scoreboard (KEY on screen for tag reasons — read as tangential).

**56b's weakest slots, for the swaps:** Longhorn Sharpshooter, Red Tiger Mechan, Lightning
Strike, Impolite Entrance, Hill Gigas (when Tannuk is not the plan), one Hellkite.

### 5.8 Craft cost — INFORMATION, per the Player Profile (not a constraint)

Unowned in the §5.9 rebuild: Stingerback Terror (R), The Fire Crystal (R), Sacred Foundry
×2 (R) — **4 rares**; every other add is owned ×1+. Tilt/extended unowned: Impolite
Entrance (U), Shardmage's Rescue (U), Lightfoot Technique (C), Agrus Kos (M), Ertha Jo (U),
Peter Parker's Camera (R), Sword of W&P (M). Everything else in §5.1–5.2 is owned ×1+
(Pain for All, Delney, Sentry, Barricade, Boots, both Tyrants, Abolisher, Return the Favor,
Avatar State, Sparks, Team Avatar, Ferocification, Collective Inferno, Energybending,
Iron Fist, Restoration Magic, Frontline Rush ×2).
Rotation: nothing in the core is older than 2024-09 (BLB's Gnaw is a CUT); no ⚠rot.
