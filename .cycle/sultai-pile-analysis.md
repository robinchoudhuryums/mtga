# Sultai legends pile (250 cards) — analysis (TEMPORARY working doc)

**Status: CONSOLIDATED — awaiting the owner's pick of shells/commanders.** Delete once the deck(s) are drafted and the findings are folded into
their `#: notes:` blocks. A scratchpad, not a source of truth — decks/ are.

**Source list:** `.cycle/sultai-pile-source.txt` (250 names; all resolve, all castable in UBG,
all Historic Brawl legal; 57 owned). No dedupe against existing decks: this pile builds NEW
decks, and a card already in another deck is still a candidate (copies are shared).

**Goal (owner):** the best 1–2 distinct Historic Brawl decks (possibly parent + variant) out of
a Sultai pile whose synergies include exile-to-win (Ashiok), self-mill + opponent mill, library
interaction (scry, enter/leave-library triggers, cast from opponents' library), reanimation,
cast from graveyard/exile, draw triggers, hand size, Elf tribal, land fetch, Mutate, Wizard
tribal, Descend, discard. Tentative commander: Thranduil, the Elvenking.

## 1. The decision framework

1. **The commander decides the deck.** Each candidate rewards ONE number, and every other card
   is graded against that number:
   - *Thranduil, the Elvenking* — ELF cards with activated abilities in the GRAVEYARD (he gains
     them) + LEGENDARY Elves entering (draw 2, discard 1). Wants self-mill/discard of Elves.
   - *Maralen, Fae Ascendant* — Elves/Faeries ENTERING (exile two of an opponent's library each)
     and the COUNT of Elves+Faeries (the free-cast MV cap). Cast-from-opponent's-library + Elves.
   - *Glarb, Calamity's Augur* — TOP of library (play lands, cast MV ≥ 4 from the top; tap to
     surveil 2). Library manipulation; MV ≥ 4 is an UPSIDE here, not a cost.
   - *Muldrotha* / *Kotis, Sibsig Champion* / *Teval* / *Sidisi* / *Mimeoplasm* / *Sin* —
     GRAVEYARD as a hand (cast permanents back, reanimate, token-on-leave). Self-mill is fuel.
   - *Gonti, Canny Acquisitor* / *Kotis, the Fangkeeper* — cast cards you DON'T own (combat
     damage → steal from their library).
   - *Yarok* (enters-trigger doubler), *Brokkos* (mutate), *Nashi, Moon's Legacy* (legendary
     recursion), *Leovold* (stax/draw lock) — narrower.
2. **Two-deck hypothesis to test, not assume:** (A) a GRAVEYARD deck — self-mill → recast /
   reanimate / descend, discard as enabler; (B) a LIBRARY/EXILE deck — opponent's library
   (exile-to-win, cast their cards, opponent mill only as fuel), top-of-library and scry
   triggers, draw triggers, hand size. Elves attach to whichever commander rewards them.
3. **Tribe viability is the PAYOFF count (G-59), measured on the pile:** Elf 22 bodies / ~10
   payoff texts → a sub-theme under an Elf commander only. Wizard 20 bodies / 2 payoffs → NOT a
   theme. Mutate 1 card → NOT a theme (Brokkos is a recursive threat, nothing more).
4. **What the deck PAYS vs what is printed:** in a graveyard deck a permanent's real cost is its
   recast-from-graveyard route (Muldrotha: one of each permanent type per turn); grade big
   permanents on effect. Under Glarb, MV ≥ 4 casts from the top for free card advantage.
5. **Mill polarity (G-62/G-42):** self-mill FEEDS deck A and is neutral-to-bad in deck B; blind
   opponent mill is a CLOCK, not interaction — it only scores in deck B where exiled/milled
   opponent cards are a resource (cast them, or count them for an exile win).
6. **Graveyard hate fights deck A (G-42):** anything exiling YOUR graveyard is a cost there; an
   exile-their-graveyard effect is fine in both.
7. **Legends are free:** 236 of 250 are legendary, so "legendary matters" (≈25 payoff texts:
   Thranduil, Nashi, Tamiyo, Price of Fame, the copy/clone family) needs no build-around.
8. **The pile is SHORT on interaction:** 23 counted interaction pieces in 250 cards, 56 card
   advantage. A 100-card deck needs 12 interaction for the A floor (scaled), so each deck's
   removal will mostly come from OUTSIDE the pile (`suggest --needs` at draft time). A pile card
   that IS interaction gets a bonus; do not cut one for a marginal engine card.
9. **Lands and ramp come from outside the pile** (it holds two MDFC lands). The deliverable is
   the ~55–63 nonland CORE of each deck; the draft fills the rest.
10. **Ownership is information, never a gate** (Player Profile): 57 owned.

## 2. Standing error list

- **Thranduil's graveyard half is nearly blank in this pile.** Of 22 legendary Elves only four
  have an activated ability he could borrow (Elrond, Moon-Reader; Lathril; High Perfect Morcant;
  Furgul). Tyvar Kell is a planeswalker and grants nothing from the graveyard. His loot on a
  legendary Elf entering is the real card.
- **Drana returns only NONlegendary creatures** — near-dead in a 94%-legendary pile (rule 7).
- **"Exile to win" is not a win condition here:** no pile card wins on an exile count. Ashiok,
  Nightmare Muse's −7 and Krang & Shredder CAST the exiled cards — it is a theft plan.
- **Own-graveyard exile (rule 6):** Kotis (Sibsig), Mimeoplasm, Sin, Tamiyo −X, Sauron, The
  Cloning of Shredder, Lazav (both), Nashi (Moon's Legacy), Rona (Disciple), Ultimecia's
  transform, Pharika, Lich's Mastery, Ashiok (Wicked Manipulator). Teval (token whenever cards
  leave your graveyard), Oasis of Renewal (seek on leave) and Syr Konrad turn that cost into value
  in deck A — keep them with the exilers.
- **Classifier holes noted (record only, G-67):** Davriel's −3 (removal, no role); Leader,
  Super-Genius (card advantage, no role); High Perfect Morcant (repeatable blight, no role); Gisa,
  Glorious Resurrector (steal, no role); Kamahl's Druidic Vow / Invasion of Ikoria (cheat, no role);
  Glarb and Fblthp, Lost on the Range (cast from top, no card advantage); Mu Yanling's −2/−0 and
  Morlun read as removal (false positives); Kira's counter is self-protection.

## 3. Cross-batch observations

- **The pile splits cleanly in two** (rule 2 confirmed): 55 cards grade ★★+ for the graveyard
  deck, 46 for the library deck, and only 14 are ★★+ in both — and 11 of those 14 are removal or
  card advantage that a removal-short pile wants in every deck (Price of Fame, Yawgmoth's Vile
  Offering, Garruk Veiled Butcher, Ob Nixilis Reignited, Vraska ×2, Dragonlord Silumgar, Sheoldred
  // The True Scriptures, Sheoldred the Apocalypse, Ashiok Sculptor of Fears, Doctor Doom
  Unrivaled). Copies are shared, so they go in BOTH.
- **Deck A's commander is Muldrotha** (one permanent of each type from the graveyard per turn).
  Teval and Sidisi are the alternates; both are better in the 99 beside Muldrotha.
- **Deck B's commander is Glarb**: surveil 2 every turn turns Matoya, Proft and the scry Elves
  into engines, and casting mana value 4+ from the top makes the pile's expensive blue legends
  (Jin-Gitaxias ×2, Reed Richards, Kitsune, Iymrith, Dragonlord Silumgar) free card advantage.
- **Variant signal: Maralen, Fae Ascendant + Elves + theft.** Every Elf entering exiles two of an
  opponent's library; the free cast is capped by the Elf count. The 22 legendary Elves, Thranduil's
  loot, and the theft cluster (Ashiok Nightmare Muse, Krang & Shredder, Xanathar, Gix, Rev, Gonti,
  Kotis the Fangkeeper, Sméagol) all point at it, and the scry Elves (Elronds, Galadriel, Arwen,
  Legolas, Rashmi) are shared with Glarb — a natural variant of deck B.
- **Not themes (rule 3):** Mutate (1 card), Wizard tribal (2 payoffs), instant/sorcery payoffs
  (God-Eternal Kefnet, Jadzi, Gale, Magic Mirror, Victor Timely, Yue — the pile has almost no
  instants), clones (only Yarok would make them a deck), hand size (Tishana, Jin-Gitaxias, Reed
  Richards — a sub-theme of deck B, not a deck).
- **34 cards are △/✗ in both decks** (snow, Beast/Bird, nonlegendary-only, artifact, Food,
  lifegain, Islands-matter, counters shells absent) — they leave the pile.
- **Interaction is the pile's constraint (rule 8):** about 15 real pieces in 250, almost all black,
  so both decks share them and still need 2–4 more from outside the pile.

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.
Columns: deck A = graveyard, deck B = library/exile; `Elf` marks a legendary Elf body.

# Batch 1 — pile entries 0–62

| Card | Cost | A: graveyard | B: library/exile | Best fit | Elf? | Roles | Operative clause | Note |
|---|---|---|---|---|---|---|---|---|
| Thranduil, the Elvenking | 2BGU | ★★★ | ★★ | Thranduil | L-Elf | CA | "Whenever another legendary Elf you control enters, draw two cards, then discard" | Commander; loot fills yard. Gy-ability half is thin (see obs). |
| Legolas, Counter of Kills | 2GU | ◇ | ★ | Glarb | L-Elf | — | "Whenever you scry, if Legolas is tapped, you may untap it" | Scry payoff; small body; legendary-Elf trigger for Thranduil. |
| Tam, Observant Sequencer | 2GU | △ | ★ | Glarb | — | CA | "Landfall — … Tam becomes prepared" (Deep Sight: draw, gain 1) | Lands from top under Glarb re-prepare it. |
| Thranduil, Sindarin Liege | 2{G/U}{G/U} | ★★ | ★ | Thranduil | L-Elf | anthem | "Mill four cards, then put up to two land cards … into your hand" | Adventure is self-mill + lands (rule 5); Elf lord. |
| Elrond, Master of Healing | 2GU | ◇ | ★★ | Glarb | L-Elf | protection/CA | "Whenever you scry, put a +1/+1 counter on each of up to X" | Scry engine payoff; draws when targeted. |
| Ezuri, Stalker of Spheres | 2GU | ◇ | ◇ | Thranduil | L-Elf | CA | "you may pay {3}. If you do, proliferate twice" | Two cards for 7 mana; legendary-Elf body. |
| Jyoti, Moag Ancient | 2GU | ✗ | ✗ | none | — | — | "create … token for each time you've cast your commander" | Needs commander recasts; land-creature anthem irrelevant. |
| Kiora, the Crashing Wave | 2GU | ★ | ★ | Teval/Glarb | — | CA, ramp, protection | "−1: Draw a card. You may play an additional land" | +1 neuters a threat each turn (tempo). |
| Nael, Avizoa Aeronaut | 2GU | ✗ | △ | none | L-Elf | — | "if there are five basic land types … draw a card" | Sultai holds 3 types: draw never fires. Elf body only. |
| Rashmi, Eternities Crafter | 2GU | ◇ | ★★ | Glarb | L-Elf | CA | "reveal the top card … cast it without paying … lesser mana value" | Top-of-library cheat; Glarb shows the top. |
| Imoti, Celebrant of Bounty | 3GU | ◇ | ★ | Glarb | — | CA | "Spells you cast with mana value 6 or greater have cascade" | Few 6+ in pile; ◇ unless big-spell skew. |
| Kruphix, God of Horizons | 3GU | △ | ◇ | other | — | — | "You have no maximum hand size" | Hand-size enabler only; rarely a creature. |
| Roalesk, Apex Hybrid | 2GGU | ◇ | ◇ | other | — | counters | "When Roalesk dies, proliferate, then proliferate again" | Counters deck card; deck 94 territory. |
| Tamiyo, Compleated Sage | 2G{G/U/P}U | ★★ | ★ | Muldrotha | — | tempo, recursion | "−X: Exile target nonland permanent card … from your graveyard. Create a token" | Copies a gy legend; +1 locks a threat (tempo). |
| Tawnos, the Toymaker | 3GU | ✗ | ✗ | none | — | — | "Whenever you cast a Beast or Bird creature spell, you may copy it" | No Beast/Bird count. |
| Oko, the Trickster | 4GU | ◇ | ◇ | other | — | counters | "+1: Put two +1/+1 counters on up to one target creature" | Six mana for counters; weak here. |
| Bonny Pall, Clearcutter | 3GUU | ★★ | ★ | Teval/Muldrotha | — | CA, ramp | "draw a card, then you may put a land card from your hand or graveyard onto the battlefield" | Attack engine; lands out of yard. |
| Omega, Heartless Evolution | 5GU | ◇ | ◇ | Glarb | — | tempo | "Put X stun counters … X is the number of nonbasic lands" | Tempo, not removal; MV7 castable from top. |
| Tishana, Voice of Thunder | 5GU | ★ | ★★ | Glarb | — | CA | "draw a card for each creature you control" | Hand-size body; MV7 from Glarb's top. |
| Glarb, Calamity's Augur | BGU | ★★ | ★★★ | Glarb | — | CA(missed) | "cast spells with mana value 4 or greater from the top" | Commander candidate; {T}: Surveil 2 also fuels A. |
| Kotis, Sibsig Champion | BGU | ★★★ | ✗ | Kotis-S | — | recursion | "cast a creature spell from your graveyard by exiling three other cards" | Eats own yard as cost (rule 6). |
| Leovold, Emissary of Trest | BGU | ★ | ★★ | Maralen/Thranduil | L-Elf | CA, stax | "Each opponent can't draw more than one card each turn" | 1v1 stax; draws when targeted. |
| Nashi, Moon's Legacy | BGU | ★★★ | ◇ | Nashi/Muldrotha | — | recursion | "exile up to one target legendary … card from your graveyard and copy it" | Rule 7: every pile card is legendary → recasts anything. |
| Nashi, Illusion Gadgeteer | 1BGU | ★★ | ◇ | Muldrotha | — | CA | "conjure a duplicate of it into your hand … perpetually gains flash" | Gy card → hand copy. |
| Kotis, the Fangkeeper | 1BGU | ◇ | ★★ | Gonti/Kotis-F | — | CA | "exile the top X cards of their library … cast … without paying" | Indestructible attacker; cast-their-cards axis. |
| Sidisi, Brood Tyrant | 1BGU | ★★★ | ✗ | Sidisi | — | tokens | "Whenever Sidisi enters or attacks, mill three cards" | Self-mill → Zombies (rule 5: anti-B). |
| Teval, the Balanced Scale | 1BGU | ★★★ | ◇ | Teval | — | tokens, ramp | "Whenever one or more cards leave your graveyard, create a 2/2" | Turns Kotis/Nashi/Tamiyo exile into tokens. |
| Gonti, Canny Acquisitor | 2BGU | ◇ | ★★ | Gonti | — | CA | "look at the top card of that player's library, then exile it face down" | Combat-gated theft commander. |
| Brokkos, Apex of Forever | 2BGU | ★ | ◇ | Muldrotha | — | recursion | "You may cast this card from your graveyard using its mutate ability" | Rule 3: mutate not a theme; recursive threat. |
| Oasis of Renewal | BGU | ★★ | ◇ | Muldrotha/Teval | — | CA | "whenever a nonland card leaves your graveyard, seek a nonland card" | Once/turn each; pays off gy recasting. |
| Maralen, Fae Ascendant | 2BGU | ◇ | ★★★ | Maralen | L-Elf | CA(theft) | "cast a spell with mana value ≤ the number of Elves and Faeries" | Commander candidate; Elf density drives it. |
| Yarok, the Desecrated | 2BGU | ★ | ★ | Maralen/Sidisi | — | doubler | "that ability triggers an additional time" | Doubles Maralen exile, Sidisi mill, Tishana draw. |
| Sin, Spira's Punishment | 4BGU | ★★ | ◇ | Muldrotha | — | recursion | "exile a permanent card from your graveyard at random, then create a … copy" | Random; eats yard (rule 6). |
| Muldrotha, the Gravetide | 3BGU | ★★★ | ✗ | Muldrotha | — | recursion | "cast a permanent spell of each permanent type from your graveyard" | Best A commander candidate (rule 4). |
| Mimeoplasm, Revered One | XBGU | ★★ | ✗ | Mimeoplasm | — | recursion | "exile up to X creature cards from your graveyard" | Consumes fuel (rule 6); late-game finisher. |
| Glamdring, Foe-hammer | 2 // 3U | ◇ | △ | Muldrotha | — | — | "Mill six cards, then put all instant and sorcery cards … into your hand" | Pile is permanents: Gleam ≈ mill 6. |
| Fblthp, Impossibly Lost | 1U | ★ | ◇ | Sidisi | — | CA | "If your library has no cards in it, you win the game" | Self-mill alt-win; combat draw 2. |
| Goldberry, River-Daughter | 1U | △ | △ | none | — | — | "Move one or more counters … draw a card" | Counter shuffler; no home. |
| Jace Reawakened | UU | ◇ | ★ | Glarb | — | CA | "+1: Draw a card, then discard a card" | Can't cast turns 1–3; loot/plot. |
| Katara, Waterbending Master | 1U | △ | △ | none | — | — | "Whenever you cast a spell during an opponent's turn" | Pile has almost no instants. |
| Marit Lage's Slumber | 1U | ✗ | ✗ | none | — | — | "if you control ten or more snow permanents" | No snow. |
| Mystic Reflection | 1U | ✗ | ✗ | none | — | — | "Choose target nonlegendary creature" | Pile is 94% legendary. |
| Malcolm, Alluring Scoundrel | 1U | ★ | ◇ | Muldrotha | — | CA | "Draw a card, then discard a card" | Flash flier looter; discard fuels A. |
| Naban, Dean of Iteration | 1U | △ | △ | none | — | — | "If a Wizard you control entering causes a triggered ability" | Rule 3: Wizard not a theme. |
| Proft, Consulting Detective | 1U | ★ | ★★ | Glarb | — | CA | "Whenever you scry or surveil, you may pay {2} … draw a card" | Glarb's surveil every turn → card. |
| Proft's Eidetic Memory | 1U | △ | ★ | Glarb | — | CA | "You have no maximum hand size" | Draw-two-a-turn payoff; hand-size. |
| Rona, Herald of Invasion | 1U | ★★ | ★ | Muldrotha | — | CA | "Whenever you cast a legendary spell, untap Rona" | Rule 7: repeat loots; discard fuels A. |
| The Key to the Vault | 1U | ◇ | ★ | Gonti | — | CA | "You may cast the exiled card without paying its mana cost" | Combat-gated. |
| Vnwxt, Verbose Host | 1U | △ | ◇ | other | — | CA | "Max speed — If you would draw a card, draw two cards instead" | Speed needs opponent life loss; slow here. |
| Arni, Humble Scribe | 2U | ★★ | ★ | Muldrotha/Thranduil | — | CA | "Whenever another nontoken creature you control enters, untap Arni" | Repeatable loot; creature-heavy pile. |
| Chandra, Chill of Compliance | 1UU | ★ | ★★ | Glarb | — | CA, tempo | "+1: Surveil 1. If … noncreature, nonland card … into your hand" | −X stun = tempo, not removal. |
| Callaphe, Beloved of the Sea | 1UU | △ | △ | none | — | protection | "Spells your opponents cast that target this permanent cost {1} more" | Mild ward tax. |
| Elrond, Lord of Rivendell | 2U | ◇ | ★★ | Glarb/Thranduil | L-Elf | selection | "Whenever Elrond or another creature you control enters, scry 1" | Scry engine feeder. |
| Elrond, Moon-Reader | 2U | ★ | ★★ | Thranduil/Glarb | L-Elf | CA | "Whenever you activate an ability of a creature, draw a card" | Glarb/Arni/Rona taps draw. Has an activated ability for Thranduil. |
| Fblthp, Lost on the Range | 1UU | ◇ | ★★ | Glarb | — | CA(missed) | "You may plot nonland cards from the top of your library" | Classifier misses the card advantage. |
| Geralf, the Fleshwright | 2U | ◇ | ◇ | other | — | tokens | "other than your first spell that turn, create a 2/2" | Needs cheap spells. |
| Graviton, Fundamental Force | 2U | △ | ◇ | Glarb | — | tempo | "Whenever you draw your second card each turn" | Draw-trigger tap/evasion; minor. |
| Impossible Man | 2U | ◇ | ◇ | other | — | — | "becomes a copy of another target permanent until end of turn" | Clone utility. |
| Invasion of Segovia | 2U | △ | △ | none | — | — | "Noncreature spells you cast have convoke" | Back face matters little. |
| Ioreth of the Healing House | 2U | ★ | ★ | Glarb/Muldrotha | — | — | "{T}: Untap two other target legendary creatures" | Re-taps Glarb, Arni, Rona, Elrond (rule 7). |
| Irma, Part-Time Mutant | 2U | ◇ | ◇ | other | — | — | "becomes a copy of up to one other target creature" | Clone; legend-rule-safe (name stays). |
| Katara, Bending Prodigy | 2U | △ | △ | none | — | CA | "Waterbend {6}: Draw a card" | Weak. |
| Kefnet the Mindful | 2U | ◇ | ★ | Glarb | — | CA | "can't attack or block unless you have seven or more cards in hand" | Hand-size sub-theme; draw sink. |

## Observations
- **Commander definers:** Muldrotha (A), Glarb (B), Maralen (B, Elf + opponent's library). Also Kotis-S, Sidisi, Teval, Nashi ML as A alternates; Gonti/Kotis-F as a combat-theft variant.
- **Thranduil, the Elvenking's graveyard half is nearly blank in this batch:** of 10 legendary Elves here, only Elrond, Moon-Reader has an activated ability. His real value is the legendary-Elf loot (10 L-Elf bodies so far).
- **Scry/surveil cluster is coherent for B:** Glarb, Proft, Elrond (Master of Healing / Lord of Rivendell), Legolas, Chandra, Rashmi, Fblthp (Lost on the Range).
- **Graveyard cluster is deep for A:** Muldrotha, Kotis-S, Sidisi, Teval, Nashi ×2, Sin, Mimeoplasm, Tamiyo −X, Oasis, Bonny Pall, Brokkos; looters Arni, Rona, Malcolm fill the yard.
- **G-42 tension inside A:** Kotis-S, Mimeoplasm, Sin, Tamiyo and Nashi ML all EXILE from your own graveyard. Teval (token on leave) and Oasis (seek on leave) turn that cost into value — keep them together.
- **Rule 7 payoffs here:** Nashi ML, Rona, Ioreth, Thranduil read "legendary" and are free in this pile.
- **Hand-size sub-theme (B):** Tishana, Kruphix, Proft's Eidetic Memory, Vnwxt, Kefnet — small; Tishana and Kefnet are the only real payoffs.
- **Opponent-library theft is combat-gated:** Gonti, Kotis-F, Key to the Vault need connecting attackers; Maralen is the exception (Elf-enter triggered).
- **Classifier holes:** Glarb (cast from top = card advantage, roles []); Fblthp, Lost on the Range (plot from top, no CA); Leovold (draw on target, roles []); Tamiyo +1 and Kiora +1 (protection/tempo, not counted); Callaphe (ward tax).
- **Structural ✗:** Jyoti (needs commander recasts), Nael (5 basic types), Marit Lage's Slumber (snow), Mystic Reflection (nonlegendary target), Tawnos (Beast/Bird) — dead in a Sultai legends pile.
- **Interaction is thin:** 0 real removal in this batch; only tempo (Tamiyo +1, Omega, Chandra −X, Kiora +1).

# Batch 2 — pile entries 63–125 (63 cards; mostly mono-U, then early mono-B)

| Card | Cost | A: graveyard | B: library/exile | Best commander fit | Elf? | Roles | Operative clause | Note |
|---|---|---|---|---|---|---|---|---|
| Kira, Great Glass-Spinner | {1}{U}{U} | ◇ | ◇ | none | — | protection | "counter that spell or ability" (first target each turn) | Team ward vs spot removal; also counters your own first target. Classifier calls it Counter (hole). |
| Lulu, Stern Guardian | {2}{U} | △ | △ | none | — | protection | "Put a stun counter on that creature" | Defensive only; proliferate idle without counters. |
| Matoya, Archon Elder | {2}{U} | ★ | ★★★ | Glarb | — | CA | "Whenever you scry or surveil, draw a card" | Glarb's tap-surveil becomes a draw every turn. |
| Lyra, Tolarian Archangel | {1}{U}{U} | ◇ | ★★ | Glarb/Maralen | — | CA | "drawn three or more cards this turn, create a 3/3" | Payoff for draw-heavy shells; flier body. |
| Mindlink Mech | {2}{U} | ✗ | ✗ | none | — | — | "copy of target nonlegendary creature that crewed it" | Pile is 94% legendary; copies nothing here. |
| Mu Yanling, Sky Dancer | {1}{U}{U} | ★ | ★ | none | — | protection | "−3: Create a 4/4 blue Elemental Bird" | Cheap walker; −2/−0 is tempo, not removal (role over-read). |
| Princess Yue | {2}{U} | ★ | ★★ | Glarb | — | ramp | "{T}: Scry 2" / returns as a land | Scry engine + dies into a land; legendary land trick. |
| Tome of the Infinite | {2}{U} | △ | ◇ | none | — | CA | "Conjure a random card" | Slow random value. |
| Unctus, Grand Metatect | {1}{U}{U} | ◇ | ◇ | Thranduil | — | CA | "becomes tapped, draw a card, then discard" | Rummage engine on blue attackers; feeds discard (A). |
| Wasp, Shrinking Savior | {2}{U} | ◇ | ◇ | none | — | CA | "draw a card for each creature with power less than 0" | Needs power <0; weak draw. |
| Alora, Rogue Companion | {3}{U} | △ | △ | none | — | — | "can't be blocked this turn" | Evasion, returns it to hand — tempo only. |
| Arwen's Gift | {3}{U} | ★ | ★★ | any | — | CA | "Scry 2, then draw two cards" | Legend discount always on (rule 7); scry trigger for Matoya. |
| Charix, the Raging Isle | {2}{U}{U} | △ | △ | none | — | — | "+X/-X … number of Islands" | Islands-matter; 3c deck. |
| Gale, Conduit of the Arcane | {3}{U} | ◇ | ◇ | none | — | recursion | "return target instant or sorcery card" | Pile has few instants/sorceries. |
| God-Eternal Kefnet | {2}{U}{U} | △ | ◇ | Glarb | — | — | "copy that card … costs {2} less" | Needs instants/sorceries; top-deck knowledge with Glarb. |
| Gandalf, Friend of the Shire | {3}{U} | △ | ◇ | none | — | — | "cast sorcery spells as though they had flash" | Ring-tempt payoff absent. |
| Irenicus's Vile Duplication | {3}{U} | ◇ | ◇ | Yarok | — | — | "copy of target creature … isn't legendary" | Clone a legend: copies an ETB engine. |
| Jace, the Perfected Mind | {2}{U}{U/P} | ★★ | ★★ | Sidisi/Teval | — | CA | "−X: Target player mills three times X" | Self-mill fuel (A) OR opp mill/exile fuel (B). |
| Jace, Wielder of Mysteries | {1}{U}{U}{U} | ★ | ◇ | Sidisi | — | CA | "library has no cards … you win" | Self-mill alt-win; 100-card deck makes it slow (rule 5). |
| Leader, Super-Genius | {2}{U}{U} | ★★ | ◇ | Muldrotha | — | CA | "you draw a card, then that creature connives" | Every combat: draw + loot = discard fuel (A). Classifier hole: no CA role. |
| Multiversal Recruitment | {3}{U} | ★ | ◇ | Yarok | — | — | "copy … isn't legendary. Flashback" | Double clone of an ETB legend; flashback from yard. |
| Orvar, the All-Form | {3}{U} | △ | △ | none | — | — | "create a token that's a copy" | Needs targeting instants. |
| Taeko, the Patient Avalanche | {3}{U} | △ | ◇ | none | — | — | "leaves … if it didn't die, scry 1" | Blink/bounce payoff — no blink here. |
| Tezzeret, Betrayer of Flesh | {2}{U}{U} | ◇ | ◇ | none | — | CA | "+1: Draw two cards. Then discard two" | Loot 2 per turn — A discard fuel. |
| The Clone Saga | {3}{U} | ★ | ★ | any | — | CA | "Surveil 3" / "copy it … isn't legendary" | Surveil 3 fills yard (A) and triggers Matoya (B). |
| The Water Crystal | {2}{U}{U} | ✗ | ★★ | Glarb/Gonti | — | — | "they mill that many cards plus four" | Opp-mill amplifier; only matters for B exile/steal (rule 5). |
| The Theorist, Jace Beleren | {2}{U}{U} | ★ | ★★ | any | — | CA, INT(tempo) | "each opponent's draw step, you draw a card" | Extra draw each turn; −2 bounce = tempo (G-25). |
| Tui and La, Moon and Ocean | {3}{U} | ◇ | ◇ | none | — | CA | "become tapped, draw a card" | Attacker draw engine. |
| Urza, Lord High Artificer | {2}{U}{U} | △ | ◇ | none | — | ramp | "{5}: … exile the top card … play … free" | Needs artifacts; few here. |
| Vesuvan Duplimancy | {3}{U} | △ | △ | none | — | — | "spell that targets … copy" | Needs targeted spells. |
| Yue, the Moon Spirit | {3}{U} | ◇ | ◇ | none | — | cheat | "cast a noncreature spell … without paying" | Pile is creature-heavy. |
| Iymrith, Desert Doom | {3}{U}{U} | ◇ | ◇ | none | — | CA, protection | "draw cards equal to the difference" | Good evasive refill. |
| Jace, Memory Adept | {3}{U}{U} | ★★ | ★★ | Sidisi/Teval | — | CA | "0: Target player mills ten cards" | Mill-10 either target: self (A) or opp (B). |
| Jace, Unraveler of Secrets | {3}{U}{U} | ◇ | ★ | Glarb | — | CA, scry | "+1: Scry 1, then draw a card" | Scry+draw each turn (Matoya double). −2 bounce = tempo. |
| Jin-Gitaxias // The Great Synthesis | {3}{U}{U} | ◇ | ★★ | Glarb | — | CA, protection | "No maximum hand size" / "cast … without paying" | Hand-size engine; Saga II bounces all non-Phyrexian (sweeper, symmetric). |
| Krang, the All-Powerful | {4}{U} | ◇ | ★ | Glarb | — | — | "drawing a card causes a triggered ability … additional time" | Doubles draw triggers (Lyra, Teferi, Sheoldred). |
| Pharaoh Rama-Tut | {4}{U} | ★ | ◇ | Muldrotha | — | CA | "noncreature spell, Pharaoh Rama-Tut connives" | Loot engine needs noncreature density. |
| Syr Elenora, the Discerning | {3}{U}{U} | △ | ◇ | none | — | CA | "power is equal to the number of cards in your hand" | Hand-size body. |
| Teferi, Temporal Pilgrim | {3}{U}{U} | ◇ | ★ | Glarb | — | CA | "Whenever you draw a card, put a loyalty counter" | Draw-trigger walker. |
| Thryx, the Sudden Storm | {3}{U}{U} | ◇ | ★ | Glarb | — | cheat | "mana value 5 or greater cost {1} less" | MV≥5 support beside Glarb's MV≥4 top casts (rule 4). |
| Victor Timely, Wily Tycoon | {4}{U} | ◇ | △ | Muldrotha | — | recursion | "cast target artifact, instant, or sorcery … free" | Few targets in this pile. |
| Jace, Arcane Strategist | {4}{U}{U} | ◇ | ★ | Glarb | — | CA | "+1: Draw a card" | Second-draw payoff. |
| Kitsune, Dragon's Daughter | {4}{U}{U} | ◇ | ◇ | Yarok | — | INT | "exchange control of two other target creatures" | Steal on ETB and combat damage — real interaction. |
| Pol Jamaar, Illusionist | {4}{U}{U} | ◇ | ◇ | Thranduil | — | CA | "Draw a card for each creature … of that type" | Elf or Zombie count dependent. |
| Reed Richards, Smartest Man | {5}{U} | ◇ | ★★ | Glarb | — | CA | "draw four cards instead" | First extra draw each turn becomes four; Krang/Lyra synergy. |
| Ruric Thar, Biomagus | {4}{U}{U} | △ | ◇ | none | — | CA | "becomes the target … draw a card" | Mostly a vanilla 6-drop flier here. |
| Zahid, Djinn of the Lamp | {4}{U}{U} | △ | △ | none | — | — | "tap an untapped artifact" | Vanilla 5/6 flier. |
| Jin-Gitaxias, Progress Tyrant | {5}{U}{U} | ◇ | ◇ | none | — | INT | "counter that spell" (once per turn) | Real soft counter; MV7 castable off Glarb's top. |
| Jadzi, Oracle of Arcavios | {6}{U}{U} | ◇ | ◇ | Glarb | — | ramp | "cast it by paying {1}" | Needs instants/sorceries; back face ramps. |
| Jin-Gitaxias, Core Augur | {8}{U}{U} | ◇ | ★ | Glarb | — | CA | "draw seven cards" | Hand-size bomb; Glarb casts it off the top (rule 4). |
| The Magic Mirror | {6}{U}{U}{U} | △ | ◇ | none | — | CA | "costs {1} less for each instant and sorcery" | UUU + few spells. |
| Wan Shi Tong, Librarian | {X}{U}{U} | ◇ | ◇ | none | — | CA | "Whenever an opponent searches their library … draw" | Flash X draw. |
| Gadwick, the Wizened | {X}{U}{U}{U} | ◇ | ◇ | none | — | CA, INT(tempo) | "draw X cards" / "tap target nonland permanent" | Draw-X; UUU in 3c. |
| Aphelia, Viper Whisperer | {1}{B} | △ | △ | none | — | — | "create a 1/1 black Snake … deathtouch" | Attack-for-value 2-drop. |
| Reezug, the Bonecobbler | {1}{B} | ★★ | ◇ | Muldrotha/Kotis-S | — | recursion | "creature card in your graveyard … cast that card this turn" | Repeatable cast-from-graveyard on a 2-drop. |
| Splinter, the Mentor | {1}{B} | ◇ | △ | none | — | — | "leaves the battlefield, create a Mutagen token" | Partner-commander text irrelevant in Brawl. |
| Azula, Ruthless Firebender | {2}{B} | ◇ | △ | none | — | — | "you may discard a card" | Discard outlet on attack (A fuel). |
| Gix, Yawgmoth Praetor | {1}{B}{B} | ★ | ★★ | Gonti/Maralen | — | CA | "Exile the top X cards of target opponent's library … play … free" | Combat draw + cast-their-library finisher (B). |
| Isareth the Awakener | {1}{B}{B} | ★★ | ◇ | Muldrotha | — | INT? no; reanimate | "return target creature card with mana value X" | Repeatable reanimation each attack. |
| Kaervek, the Punisher | {1}{B}{B} | ★ | ◇ | Muldrotha | — | recursion | "exile up to one target black card … copy it" | Crime-triggered recast from yard. |
| Tatsunari, Toad Rider | {2}{B} | △ | △ | none | — | — | "Whenever you cast an enchantment spell" | Few enchantments. |
| Yahenni, Undying Partisan | {2}{B} | ◇ | ◇ | none | — | protection | "Sacrifice another creature: … indestructible" | Sac outlet. |
| Davriel, Soul Broker | {2}{B}{B} | ◇ | ◇ | none | — | INT | "−3: Target creature … perpetually gets -3/-3" | Real removal (classifier gives no role — hole). |

## Observations
- **Glarb is the clear magnet for this batch**: Matoya (draw per surveil), Princess Yue (tap scry), Jace Unraveler, Arwen's Gift and The Clone Saga all turn his tap-surveil into cards; Reed Richards / Krang / Lyra / Teferi form a DRAW-TRIGGER cluster on top.
- **Glarb's MV≥4 top-casting makes the expensive blue legends playable** (rule 4): Jin-Gitaxias Core Augur (MV10), Progress Tyrant (MV7), Reed Richards (MV6), Kitsune, Iymrith, Thryx (MV≥5 discount).
- **Deck A fuel from blue**: Jace Memory Adept (mill 10), Jace Perfected Mind (−X mill), The Clone Saga (surveil 3), loot engines (Leader, Tezzeret, Unctus, Pharaoh) feeding Reezug, Isareth, Kaervek recursion.
- **Opponent-mill amplifier The Water Crystal is B-only** (rule 5); pairs with Jace Memory Adept / Perfected Mind targeting the opponent for an exile/steal plan (Gix casts from their library).
- **Interaction in this batch is thin**: real removal only Davriel (−3: −3/−3), Kitsune (control exchange), Jin-Gitaxias Progress Tyrant (soft counter); Mu Yanling/Wasp/Gadwick/Theorist are tempo.
- **Classifier holes**: Davriel, Soul Broker (−3 perpetual −3/−3 = removal, roles empty); Leader, Super-Genius (draw each combat = CA, roles empty); Mu Yanling "Removal (spot)" is an over-read (−2/−0 is not removal); Kira's "Counter" is self-protection, not interaction.
- **Legendary clone family** (Irenicus's Vile Duplication, Multiversal Recruitment, The Clone Saga II) only matters with an ETB engine to copy — Yarok shell, not core.
- **Hand-size cluster** (Reed Richards, Jin-Gitaxias Great Synthesis, Syr Elenora, Magic Mirror, Core Augur) is real but thin — a sub-theme of a Glarb draw deck, not its own deck.
- **No Elves in this batch**; Wizards present (Lulu, Gale, Gandalf, Ruric, Jadzi, Gadwick, Isareth) with zero Wizard payoffs (rule 3 holds).
- **Instant/sorcery payoffs** (God-Eternal Kefnet, Jadzi, Gale, Magic Mirror, Victor Timely, Yue) have almost no instants/sorceries in a legends pile — dead cluster.

# Batch 3 — pile entries 126–188 (63 cards)

| Card | Cost | A: graveyard | B: library/exile | Best fit | Elf? | Roles | Operative clause | Note |
|---|---|---|---|---|---|---|---|---|
| Doctor Doom, Unrivaled | {2}{B}{B} | ★★ | ★★ | Glarb / Muldrotha | | CA | "{T}: You draw a card… if your library has no cards… you win" | Self-mill win-con (rule 5 inverted: self-mill IS the clock); repeatable draw either deck. |
| Erebos, God of the Dead | {3}{B} | ★ | ★ | other | | CA | "{1}{B}, Pay 2 life: Draw a card." | Indestructible mana-sink draw; devotion rarely met in 3c. |
| Gisa, Glorious Resurrector | {2}{B}{B} | ★ | ◇ | Muldrotha | | — | "opponent… would die, exile it instead… onto the battlefield under your control" | Steals their dead creatures; classifier sees nothing. |
| Kels, Fight Fixer | {2}{B}{B} | ★ | △ | Muldrotha | | CA, protection | "Whenever you sacrifice a creature, you may pay {U/B}… draw" | Needs a sac outlet deck; thin in pile. |
| Liliana of the Dark Realms | {2}{B}{B} | △ | △ | none | | ramp, INT(−3) | "−3: Target creature gets… -X/-X… X is the number of Swamps" | Swamp-count gate weak in 3c Brawl. |
| Kingpin, Wilson Fisk | {3}{B} | ◇ | △ | Muldrotha | | ramp | "Whenever you sacrifice… create two Treasure tokens" | Sacrifice payoff, few outlets. |
| Lo and Li, Royal Advisors | {2}{B}{B} | △ | ★ | Maralen / Glarb | | mill | "{2}{U/B}: Target player mills four cards" | Repeatable opp mill — fuel for Ashiok −7/exile plans (rule 5). |
| Lord Dregg, Insect Invader | {3}{B} | ◇ | △ | Teval | | CA | "Disappear… if a permanent left the battlefield… create a 1/1" | Token engine, generic. |
| Madame Hydra, Reanimated | {3}{B} | ★★ | ✗ | Muldrotha / Sidisi | | self-mill | "+1/+1 for each creature card in your graveyard… enters or attacks, mill two" | Self-mill body; fights deck B (rule 5). |
| Massacre Girl, Known Killer | {2}{B}{B} | ◇ | ◇ | none | | CA | "Creatures you control have wither… toughness less than 1, draw" | Wither + draw; good vs go-wide, off-plan. |
| Moonstone, Harsh Mistress | {3}{B} | ★★ | ◇ | Thranduil | | CA | "Whenever you discard… exile… you may play that card" | Turns Thranduil's discard into card advantage. |
| One Ring to Rule Them All | {2}{B}{B} | ★ | ◇ | any | | INT (sweeper) | "II — Destroy all nonlegendary creatures." | One-sided-ish sweeper in a 94%-legendary deck (rule 7/8). |
| Price of Fame | {3}{B} | ★★★ | ★★★ | any | | INT | "costs {2} less if it targets a legendary… Destroy target creature. Surveil 2." | Premium removal (rule 8); surveil feeds both. |
| Rev, Tithe Extractor | {3}{B} | △ | ★★ | Gonti / Kotis-F | | ramp, CA | "look at the top card of that player's library… exile… may cast" | Combat theft + Treasure; deck B steal sub-theme. |
| Sarevok the Usurper | {3}{B} | ◇ | ✗ | Muldrotha | | — | "+X/+0… X is the number of creature cards in your graveyard" | Weak scaler. |
| Sheoldred, the Apocalypse | {2}{B}{B} | ★★ | ★★★ | Glarb | | drain | "Whenever an opponent draws a card, they lose 2 life." | Draw-trigger payoff; best in draw-heavy deck B. |
| Yawgmoth, Thran Physician | {2}{B}{B} | ★★ | ◇ | Muldrotha | | INT, CA | "Sacrifice another creature: Put a -1/-1 counter… draw" | Repeatable removal/draw with token fodder (Teval/Sidisi Zombies). |
| Whisper, Blood Liturgist | {3}{B} | ◇ | ✗ | Muldrotha | | reanimation | "Sacrifice two creatures: Return target creature card…" | Costly; fine with Zombie tokens. |
| Aclazotz, Deepest Betrayal | {3}{B}{B} | ★★ | ★ | any | | CA, land | "When Aclazotz dies, return it… transformed" | MDFC-ish land/threat; discard attack. |
| Ashiok, Wicked Manipulator | {3}{B}{B} | ✗ | ★★★ | Glarb / Maralen | | CA | "+1: Look at the top two… Exile one… other into your hand" | Exile-to-win anchor (−7 scales with your own exiled MV). Fights deck A (rule 6). |
| Black Widow, Daring Operative | {4}{B} | ★★ | ✗ | Sidisi / Muldrotha | | drain | "each opponent loses life equal to the number of creature cards in your graveyard" | Self-mill payoff. |
| Drana, the Last Bloodchief | {3}{B}{B} | ★ | ✗ | Muldrotha | | recursion | "defending player chooses a nonlegendary creature card" | Pile is all legendary → nearly dead (rule 7). |
| Garruk, Veiled Butcher | {3}{B}{B} | ★★ | ★★ | any | | INT, CA | "−2: Each player sacrifices… −3: Each opponent discards two" | Removal + card advantage; real interaction. |
| Ghoulcaller Gisa | {3}{B}{B} | ★ | △ | Muldrotha | | tokens | "Sacrifice another creature: Create X 2/2 black Zombie" | Sac outlet. |
| Gisa, the Hellraiser | {3}{B}{B} | ★ | ★ | other | | tokens | "Whenever you commit a crime, create two… Zombie Rogue" | Crime = target opponent; Zombie token engine. |
| Junji, the Midnight Sky | {3}{B}{B} | ★★ | ◇ | Muldrotha | | reanimation | "When Junji dies… Put target non-Dragon creature card… onto the battlefield" | Recursive threat. |
| Lo and Li, Twin Tutors | {4}{B} | ◇ | ◇ | Thranduil | | tutor | "search your library for a Lesson or Noble card" | Tutors Noble: Thranduil/Maralen/Glarb are Nobles. |
| M.O.D.O.K., Evil Intellect | {3}{B}{B} | ◇ | ★★ | Glarb / Thranduil | | INT | "Whenever you draw your second card each turn, target opponent sacrifices" | Repeatable edict in draw deck. |
| Maha, Its Feathers Night | {3}{B}{B} | ★ | ★ | any | | protection | "Creatures your opponents control have base toughness 1." | Strong vs blockers, combo with wither. |
| Ob Nixilis Reignited | {3}{B}{B} | ★★ | ★★ | any | | INT, CA | "+1: You draw… −3: Destroy target creature." | Interaction + draw. |
| Sauron, the Necromancer | {3}{B}{B} | ★★ | ✗ | Muldrotha | | recursion | "exile target creature card from your graveyard. Create… copy" | Graveyard attack engine. |
| Seizan, Perverter of Truth | {3}{B}{B} | ◇ | ★ | Glarb | | CA, drain | "each player's upkeep, that player loses 2 life and draws two" | Symmetric; Sheoldred combo. |
| Seymour Flux | {4}{B} | ◇ | ★ | Glarb | | CA | "pay 1 life… draw a card and put a +1/+1 counter" | Ashiok replaces life with exile. |
| Shredder, Shadow Master | {3}{B}{B} | △ | △ | none | | — | "deals combat damage… that player loses half their life" | 1v1 combat finisher, no synergy. |
| Sheoldred // The True Scriptures | {3}{B}{B} | ★★★ | ★★ | any | | INT, reanimation | "each opponent sacrifices… III — Put all creature cards from all graveyards onto the battlefield" | Edict + mass reanimate; self-mill boosts. |
| Skithiryx, the Blight Dragon | {3}{B}{B} | △ | △ | none | | — | "Infect" | Lone infect threat; off-plan. |
| Syr Konrad, the Grim | {3}{B}{B} | ★★ | ★ | Muldrotha / Sidisi | | drain, mill | "creature card leaves your graveyard… 1 damage to each opponent" | Mill+leave-graveyard payoff (pairs Teval). |
| Tergrid, God of Fright | {3}{B}{B} | ◇ | ◇ | none | | — | "Whenever an opponent sacrifices… discards a permanent card… put that card… under your control" | Needs edicts/discard. |
| Witch-king of Angmar | {3}{B}{B} | ◇ | ◇ | any | | INT (reactive) | "each opponent sacrifices a creature… that dealt combat damage to you" | Defensive edict. |
| Yawgmoth's Vile Offering | {4}{B} | ★★★ | ★★ | any | | INT, reanimation | "onto the battlefield under your control. Destroy up to one target creature" | Two-for-one; legendary sorcery free here (rule 7). |
| Doctor Doom | {4}{B}{B} | ★ | ★ | any | | CA, tokens | "you draw a card and lose 1 life" | Value body. |
| Bolas's Citadel | {3}{B}{B}{B} | ◇ | ★★★ | Glarb | | CA | "cast spells from the top of your library… pay life" | Top-of-library engine; BBB pip-heavy in 3c. |
| Ink-Eyes, Servant of Oni | {4}{B}{B} | △ | ◇ | Kotis-F | | reanimation | "put target creature card from that player's graveyard onto the battlefield" | Opponent-mill synergy. |
| Lich's Mastery | {3}{B}{B}{B} | △ | △ | none | | CA | "Whenever you lose life… exile a permanent… or a card from your hand or graveyard" | Too risky; fights deck A. |
| Liliana, Death Mage | {4}{B}{B} | ★★ | ★ | Muldrotha | | INT, recursion | "+1: Return… creature card… −3: Destroy target creature" | Interaction + recursion. |
| Tetzimoc, Primal Death | {4}{B}{B} | ◇ | ◇ | none | | INT (slow) | "destroy each creature… with a prey counter" | Slow sweeper. |
| The Cloning of Shredder | {4}{B}{B} | ★★ | ✗ | Muldrotha | | recursion | "Exile target creature card from your graveyard. Create a token that's a copy" | Three tokens from one graveyard creature. |
| Vraska, Betrayal's Sting | {4}{B}{B/P} | ★ | ★★ | any | | INT, CA | "0: You draw… −2: Target creature becomes a Treasure" | Removal + draw. |
| K'rrik, Son of Yawgmoth | {4}{B/P}{B/P}{B/P} | ◇ | ◇ | none | | — | "you may pay 2 life rather than pay that mana" | Life-for-mana; Ashiok converts life to exile. |
| Count Nefaria | {6}{B} | △ | ✗ | none | | — | "costs {3} less… if you've sacrificed" | Vanilla flier. |
| Sheoldred, Whispering One | {5}{B}{B} | ★★★ | ◇ | Muldrotha | | INT, reanimation | "upkeep, return target creature card… each opponent's upkeep… sacrifices" | Engine + edict. |
| Morlun, Devourer of Spiders | {X}{B}{B} | ◇ | ◇ | none | | drain | "deals X damage to target opponent" | Classifier calls it removal — it hits only opponents (hole). |
| Dionus, Elvish Archdruid | {3}{G} | ◇ | ◇ | Thranduil | L-Elf | — | "Elves… untap it and put a +1/+1 counter" | Elf-mana untap; needs Elf activations. |
| Celeborn the Wise | {3}{G} | ◇ | ◇ | Thranduil | L-Elf | — | "attack with one or more Elves, scry 1" | Legendary Elf body (Thranduil draw trigger). |
| Wrenn and Realmbreaker | {1}{G}{G} | ★★ | ★ | any | | ramp, recursion | "Lands… Add one mana of any color… −2: Mill three… permanent card… into your hand" | Fixing + self-mill selection. |
| Goreclaw, Terror of Qal Sisma | {3}{G} | ◇ | ◇ | none | | cost | "power 4 or greater cost {2} less" | Generic. |
| Kona, Rescue Beastie | {3}{G} | ◇ | △ | other | | cheat | "put a permanent card from your hand onto the battlefield" | Needs tapping. |
| Leyline Immersion | {3}{G} | ★ | ★ | any | | ramp | "Enchant legendary creature… Add five mana" | Big ramp in all-legend deck (rule 7). |
| Mythweaver Poq | {3}{G} | △ | △ | none | | ramp | "conjure a duplicate of it onto the battlefield" | Land ramp; landfall-adjacent. |
| Oyaminartok, Polar Werebear | {2}{G}{G} | △ | △ | none | | — | "deals combat damage… create a Food" | Off-plan. |
| Radagast of Rhosgobel | {2}{G}{G} | ◇ | ★ | any | | cost | "first creature spell… costs {2} less… flash" | Tempo; Wizard body (rule 3: no Wizard payoff). |
| Tyvar Kell | {2}{G}{G} | ◇ | ◇ | Thranduil | | ramp | "Elves you control have '{T}: Add {B}'… 0: Create a 1/1… Elf Warrior" | Elf mana-ability source for Thranduil's grant? (Thranduil gives Elf CARDS' abilities only.) |
| Ashaya, Soul of the Wild | {3}{G}{G} | △ | △ | none | | ramp | "Nontoken creatures you control are Forest lands" | Landfall/land-count only. |

## Observations
- **Two clean clusters**: A (self-mill → recursion) is deep in black — Sheoldred Whispering One, Sheoldred//True Scriptures, Junji, Liliana Death Mage, Cloning of Shredder, Sauron, Madame Hydra, Black Widow, Syr Konrad. B (library/exile/draw) — Ashiok Wicked Manipulator, Bolas's Citadel, Sheoldred Apocalypse, M.O.D.O.K., Seizan, Rev, Lo and Li (opp mill).
- **Doctor Doom, Unrivaled is a self-mill WIN** — an empty library wins; turns deck A's self-mill into a clock (rule 5 cuts both ways).
- **G-42**: Ashiok Wicked Manipulator exiles your OWN library (and life-payment exiles) — fine in B, a cost in A. Lich's Mastery exiles your graveyard — fights A; out.
- **Drana** returns only NONlegendary creatures — near-dead in a 94%-legendary list (rule 7). **One Ring's** "destroy all nonlegendary" is close to one-sided here.
- **Interaction in this batch (rule 8)**: Price of Fame, Yawgmoth's Vile Offering, Sheoldred//Scriptures, Sheoldred Whispering One, Garruk Veiled Butcher, Ob Nixilis, Liliana Death Mage, Vraska Betrayal's Sting, M.O.D.O.K., Yawgmoth Thran Physician, One Ring — ~11, most in black; both decks want them.
- **Classifier holes**: Morlun scored Removal but only damages a player (false positive); Gisa Glorious Resurrector (steals dying creatures) and Gisa the Hellraiser score nothing useful; Tergrid's theft unscored; One Ring tagged Sweeper correctly.
- **Elf count here**: only 2 legendary Elves (Dionus, Celeborn) + Tyvar Kell (Elf payoff PW). Thin batch for Thranduil.
- **Thranduil caveat**: he gains activated abilities of Elf CARDS in the graveyard — Tyvar Kell (a planeswalker granting Elf mana) does nothing from the graveyard; Dionus has no activated ability.
- **Lo and Li, Twin Tutors** finds a Noble — Thranduil, Maralen, Glarb, Celeborn are Nobles; a commander-redundancy tutor.
- **Variant signal**: a black "aristocrats/edict" core (Yawgmoth, Kels, Ghoulcaller Gisa, Whisper, Kingpin, Tergrid) — too thin on outlets to be its own deck; fold sac outlets into A.
- **Pip warning**: Bolas's Citadel and Lich's Mastery are {B}{B}{B}; Citadel still worth it in B.

# Batch 4 — pile entries 189–249 (61 cards)

A = graveyard deck · B = library/exile deck. Rule numbers refer to the framework in `.cycle/sultai-pile-analysis.md`.

| Card | Cost | A | B | Best commander fit | Elf? | Roles | Operative clause | Note |
|---|---|---|---|---|---|---|---|---|
| Bosco, Just a Bear | {4}{G} | △ | △ | none | — | — | "create a Food token for each legendary creature you control" | Food without a Food payoff; only Ygra wants it. |
| Greensleeves, Maro-Sorcerer | {3}{G}{G} | ◇ | ◇ | Glarb | — | protection | "Landfall — … create a 3/3 green Badger" | Landfall threat; good with land-recursion (Muldrotha/Teval). |
| Wrenn and Seven | {3}{G}{G} | ★★ | ◇ | Muldrotha | — | CA, ramp | "+1: … rest into your graveyard" | Self-mill plus lands in hand; −8 returns every permanent. Rule 5 feeds A. |
| Garruk, Caller of Beasts | {4}{G}{G} | ★ | ★ | Glarb | — | CA | "+1: … Put all creature cards … into your hand" | Creature-dense CA; puts misses on the BOTTOM, so neutral for A. |
| Mitotic Ultimus | {7}{G}{G} | △ | △ | none | — | — | "costs {X} less … greatest power" | Conjure gimmick; no real home. |
| Invasion of Ikoria | {X}{G}{G} | ★★ | ★ | Muldrotha | — | ramp/tutor | "search your library and/or graveyard for a non-Human creature" | Reanimate-or-tutor at instant power; flexible X. |
| Kamahl's Druidic Vow | {X}{G}{G} | ★★ | ★ | Muldrotha | — | ramp | "put any number of land and/or legendary permanent cards … rest into your graveyard" | Pile is 94% legendary (rule 7); misses fill the yard (rule 5). |
| Golbez, Crystal Collector | {U}{B} | ◇ | △ | none | — | recursion | "if you control four or more artifacts, return target creature card" | Needs artifacts the pile lacks. |
| Lazav, the Multifarious | {U}{B} | ★★ | ◇ | Muldrotha | — | recursion | "{X}: Lazav becomes a copy of target creature card in your graveyard" | Cheap toolbox off a full yard. |
| Krydle of Baldur's Gate | {U}{B} | △ | ◇ | Gonti | Elf (legendary Elf) | — | "that player loses 1 life and mills a card … scry 1" | Weak body; a legendary Elf for Thranduil's draw. |
| The Ancient One | {U}{B} | ★★ | ★ | Muldrotha | — | CA (loot) | "Draw a card, then discard … target player mills cards equal to its MV" | Loot in A, mill-clock in B (rule 5); Descend 8. |
| Zimone the Calculating | {U}{B} | ★ | △ | Sidisi | — | INT (back: −3/−0) | "Whenever one or more cards are put into your graveyard from your library" | Prepared-on-mill; back face is weak interaction. |
| Lazav, Familiar Stranger | {1}{U}{B} | ◇ | ◇ | none | — | — | "exile a card from a graveyard … become a copy" | Can exile own yard (rule 6 cost in A). |
| Locke Cole | {1}{U}{B} | △ | ◇ | Gonti | — | loot | "deals combat damage … draw a card, then discard" | Small evasive looter. |
| Ringsight | {1}{U}{B} | ★ | ★ | any | — | tutor | "Search your library for a card that shares a color with a legendary creature" | Unconditional tutor in a legends deck. |
| Rona, Disciple of Gix | {1}{U}{B} | ◇ | ★ | Glarb | — | CA | "You may cast spells from among cards exiled with Rona" | Exiles own historic card (rule 6 cost in A); B-side value. |
| Emet-Selch of the Third Seat | {2}{U}{B} | ★ | △ | Muldrotha | — | cost cheat | "Spells you cast from your graveyard cost {2} less" | Discounts Muldrotha/Kotis recasts; instants are scarce in the pile. |
| Xande, Dark Mage | {2}{U}{B} | ◇ | △ | none | — | — | "+1/+1 for each noncreature, nonland card in your graveyard" | Beater; the pile is creature-heavy. |
| Ashiok, Nightmare Muse | {3}{U}{B} | ★ | ★★★ | Gonti / Kotis-F | — | INT (−3 bounce), threat | "each opponent exiles the top two cards … cast … from exile" | Exile-win core; the −7 casts their cards. |
| Phenax, God of Deception | {3}{U}{B} | ◇ | ★★ | other | — | mill engine | "Creatures you control have '{T}: Target player mills X'" | Mill-to-win in B; can self-mill in A. |
| Uchbenbak, the Great Mistake | {3}{U}{B} | ★★ | △ | Muldrotha | — | recursion | "Descend 8 — Return this card from your graveyard to the battlefield" | Self-returning threat; descend deck. |
| Ultimecia, Time Sorceress | {3}{U}{B} | ★★ | ◇ | Muldrotha | — | — | "enters or attacks, surveil 2 … exile eight cards from your graveyard" | Surveil feeds A; the transform cost exiles 8 (rule 6 tension). |
| Ashiok, Sculptor of Fears | {4}{U}{B} | ★★ | ★★ | either | — | CA, reanimate | "+2: Draw a card. Each player mills two … −5: … from a graveyard" | Fits both decks. |
| Dragonlord Silumgar | {4}{U}{B} | ★★ | ★★ | either | — | INT (steal) | "gain control of target creature or planeswalker" | Interaction (rule 8); Glarb-castable from the top. |
| Tezzeret, Master of the Bridge | {4}{U}{B} | △ | △ | none | — | — | "affinity for artifacts" | Artifact deck card; the pile has few. |
| Krang & Shredder | {4}{U/B}{U/B} | ◇ | ★★ | Gonti / Kotis-F | — | CA (theft) | "each opponent exiles cards … cast a card exiled … without paying" | Cast-their-cards engine. |
| Xanathar, Guild Kingpin | {4}{U}{B} | ◇ | ★★ | Gonti | — | lock + theft | "can't cast spells … you may play the top card of their library" | Soft lock on their turn too; B core. |
| Prototype X-8 | {8}{U}{B} | ★ | △ | Mimeoplasm | — | — | "costs {2} less for each creature card in your graveyard" | Big yard discount; rest is Alchemy fluff. |
| Chevill, Bane of Monsters | {B}{G} | ◇ | ◇ | none | — | CA (repeat) | "you gain 3 life and draw a card" | Bounty CA needs removal to cash in. |
| Dina, Soul Steeper | {B}{G} | △ | △ | none | — | drain | "Whenever you gain life, each opponent loses 1 life" | Lifegain deck card. |
| Slimefoot, Thallid Transplant | {B}{G} | ◇ | ◇ | Glarb | — | CA | "Whenever a Swamp or Forest enters … draft a card" | Landfall-like CA on basics. |
| Vraska Joins Up | {B}{G} | ★ | ★ | any | — | CA | "Whenever a legendary creature you control deals combat damage … draw" | Legends deck (rule 7). |
| Abomination of Llanowar | {1}{B}{G} | ★ | ◇ | Thranduil | L-Elf | — | "number of Elves you control plus … Elf cards in your graveyard" | Elf + yard; best under Thranduil. |
| Dina, Essence Brewer | {1}{B}{G} | ◇ | △ | none | — | CA | "Whenever you sacrifice a creature, draw a card" | Sacrifice outlet; aristocrats light. |
| Journey to Eternity | {1}{B}{G} | ★★ | ◇ | Muldrotha | — | reanimate, ramp | "return it … then return this card … transformed" | Becomes a repeatable reanimation land. |
| Long Feng, Grand Secretariat | {1}{B/G}{B/G} | ◇ | △ | none | — | — | "creature … or a land … put into a graveyard" | Counters payoff; fetch synergy (owned). |
| Pharika, God of Affliction | {1}{B}{G} | ✗ | ◇ | none | — | yard hate | "Exile target creature card from a graveyard. Its owner creates…" | Rule 6: hate that fights A; gives the owner a token. |
| Sarulf, Realm Eater | {1}{B}{G} | ◇ | ★ | any | — | INT (sweeper) | "exile each other nonland permanent with MV ≤ counters" | One-sided-ish sweeper; slow. |
| Sméagol, Helpful Guide | {1}{B}{G} | ◇ | ★★ | Gonti | — | ramp, mill | "reveals … until … land … onto the battlefield … rest into their graveyard" | Steals lands and mills them (rule 5). |
| The Mycotyrant | {1}{B}{G} | ★★ | △ | Muldrotha | — | tokens | "X … Fungus tokens … times you descended" | Descend payoff (any permanent to the yard). |
| Furgul, Quag Nurturer | {2}{B}{G} | ◇ | △ | Thranduil | L-Elf | ramp | "{T}, Sacrifice a creature: Add … {G}" | Alchemy; the Elf mana ability Thranduil could borrow. |
| High Perfect Morcant | {2}{B}{G} | ★ | ◇ | Thranduil | L-Elf | INT-ish | "Elf … enters, each opponent blights 1" | Elf-entry chip removal; Thranduil gains his proliferate. |
| Kagha, Shadow Archdruid | {2}{B}{G} | ★★ | ◇ | Muldrotha / Thranduil | L-Elf | CA | "cast a permanent spell from … put there from your library this turn" | Self-mill plus recast; Elf. |
| Lathril, Blade of the Elves | {2}{B}{G} | ★ | ◇ | Thranduil | L-Elf | win-con | "Tap ten untapped Elves: Each opponent loses 10 life" | Thranduil gains the ability from the yard. |
| Nissa of Shadowed Boughs | {2}{B}{G} | ★★ | ◇ | Muldrotha | — | reanimate | "−5: … creature card … from your hand or graveyard" | Landfall loyalty; reanimates. |
| Nemata, Primeval Warden | {2}{B}{G} | ✗ | ★ | Gonti | — | CA | "If a creature an opponent controls would die, exile it instead" | Exiles their creatures: fine in B, a non-issue in A (theirs). |
| Tyvar the Bellicose | {2}{B}{G} | ◇ | △ | Thranduil | L-Elf | — | "Whenever one or more Elves you control attack … deathtouch" | Elf combat lord; mana-dork counters. |
| Vraska, Golgari Queen | {2}{B}{G} | ★★ | ★★ | either | — | INT, CA | "−3: Destroy target nonland permanent with MV 3 or less" | Interaction plus sacrifice-draw (rule 8). |
| Cloud of Darkness | {2}{B}{G}{G} | ★★★ | ◇ | Muldrotha | — | INT | "−X/−X … X is the number of permanent cards in your graveyard" | Scaling removal in a full-yard deck. |
| Ygra, Eater of All | {3}{B}{G} | ◇ | ◇ | none | — | — | "Other creatures are Food artifacts" | Lifegain/Food deck; no home. |
| Yargle and Multani | {3}{B}{B}{G} | △ | △ | none | — | — | (vanilla 18/6) | Big reanimation target only. |
| Beledros Witherbloom | {5}{B}{G} | ★ | ◇ | Muldrotha | — | tokens | "create a 1/1 … Pest … Untap all lands" | Recurring token engine and a reanimation target. |
| Witherbloom, the Balancer | {6}{B}{G} | ◇ | ◇ | none | — | — | "Affinity for creatures … Instant and sorcery … affinity" | Spells deck card; few instants here. |
| Arwen Undómiel | {G}{U} | ◇ | ★ | Glarb | L-Elf | — | "Whenever you scry, put a +1/+1 counter" | Scry payoff; Elf. |
| Kinnan, Bonder Prodigy | {G}{U} | ◇ | ◇ | Thranduil | — | ramp | "tap a nonland permanent for mana, add one" | Needs mana dorks (Elves). |
| Absorbing Man | {1}{G}{U} | △ | △ | none | — | — | "becomes a copy of … artifact, … enchantment, or land" | Gimmick. |
| Albiorix, Goose Tyrant | {1}{G}{U} | ★ | ◇ | Muldrotha | — | loot | "Draw two cards, then discard two" | Adventure loot fills the yard. |
| Galadriel of Lothlórien | {1}{G}{U} | ◇ | ★★ | Glarb | L-Elf | ramp | "Whenever you scry, … land card … onto the battlefield" | Scry ramp; legendary Elf. |
| Kiora of Salt and Sand | {1}{G}{U} | △ | ◇ | none | — | — | "Planeswalkers you control have '[−8]: … 8/8'" | Superfriends only (owned). |
| Kasmina, Enigma Sage | {1}{G}{U} | △ | ★ | Glarb | — | scry | "+2: Scry 1" | Shares loyalty abilities; scry engine. |
| Nissa, Steward of Elements | {X}{G}{U} | ◇ | ★ | Glarb | — | CA/ramp | "0: Look at the top card … onto the battlefield" | Top-of-library value. |

## Observations

- **Deck A (graveyard) core here:** Cloud of Darkness (scaling removal), Wrenn and Seven, Kamahl's Druidic Vow (rule 7: misses fill the yard), Journey to Eternity, Uchbenbak and The Ancient One (Descend 8), The Mycotyrant (descend payoff), Kagha, Nissa of Shadowed Boughs, Lazav the Multifarious, Invasion of Ikoria. Muldrotha is the best fit for most.
- **Deck B (library/exile) core here:** Ashiok, Nightmare Muse, Krang & Shredder, Xanathar, Sméagol, Phenax, Dragonlord Silumgar, plus Rona and Nemata. Gonti / Kotis-F / Glarb fit them best. Ashiok, Sculptor of Fears is a real two-deck card.
- **G-42 conflicts in A:**
  - Pharika exiles creature cards from a graveyard; target theirs only, or it's a ✗.
  - Lazav, Familiar Stranger can exile your own yard.
  - Rona exiles one historic card of yours.
  - Ultimecia's transform exiles eight of your cards.
- **Legendary Elves in this batch: 9.** Krydle, Abomination, Furgul, Morcant, Kagha, Lathril, Tyvar, Arwen and Galadriel.
  - Payoff texts here: Abomination, Morcant, Lathril and Tyvar.
  - Thranduil borrows activated abilities, and the Elves here that have one are Lathril (10-Elf drain), Morcant (proliferate) and Furgul (sac for mana).
  - Elves are a real but THIN sub-theme here (rule 3).
- **Scry/top-of-library cluster** (Glarb or a Galadriel-style B): Galadriel of Lothlórien, Arwen Undómiel, Kasmina, Nissa, Steward of Elements, Ringsight. Galadriel plus Arwen make scry both ramp and counters.
- **Classifier holes:**
  - High Perfect Morcant: "each opponent blights 1" is repeatable chip removal, no role assigned.
  - Ashiok, Nightmare Muse: the −3 bounce is tempo, correctly not interaction, but the card scores NO role at all (roles=[]).
  - Kamahl's Druidic Vow and Invasion of Ikoria: no role, though both put permanents onto the battlefield (ramp/cheat).
  - Zimone's back face (−3/−0) is not removal.
- **Rule 8 interaction in this batch:** Dragonlord Silumgar, Vraska Golgari Queen, Cloud of Darkness and Sarulf are real. Ashiok, Nightmare Muse is tempo. That's four pieces in 61 cards, confirming the pile is short.
- **Variant signal:** the Golgari cards (Vraska, Nissa, Cloud of Darkness, Mycotyrant, Journey) sit squarely in A. The Dimir theft cards (Xanathar, Krang & Shredder, Ashiok, Sméagol) cluster in B. That's a clean split.
- **No home:** Mitotic Ultimus, Yargle and Multani, Absorbing Man, Golbez, Tezzeret, Bosco, Ygra, Dina Soul Steeper and Witherbloom (artifact/Food/lifegain/spells shells absent).


## 5. Consolidated plan (live)

Three shells, two decks plus an optional variant. Each lists the PILE core; the draft
(`/draft-deck`) fills ~7–12 slots from outside the pile (ramp, 2–4 more removal) and 36–38 lands.
A card in two lists goes in both — copies are shared.

**SHARED by every shell (the pile's removal + card advantage, rule 8):** Price of Fame;
Yawgmoth's Vile Offering; Sheoldred // The True Scriptures; Garruk, Veiled Butcher; Ob Nixilis
Reignited; Vraska, Golgari Queen; Vraska, Betrayal's Sting; Dragonlord Silumgar; Ashiok, Sculptor
of Fears; Doctor Doom, Unrivaled.

### Deck A — GRAVEYARD ENGINE, commander Muldrotha, the Gravetide (alt: Teval)
- *Recursion engines:* Teval; Sidisi, Brood Tyrant; Kotis, Sibsig Champion; Nashi, Moon's Legacy;
  Nashi, Illusion Gadgeteer; Mimeoplasm; Sin; Tamiyo, Compleated Sage; Oasis of Renewal; Reezug;
  Isareth; Junji; Sauron, the Necromancer; The Cloning of Shredder; Lazav, the Multifarious;
  Uchbenbak; Brokkos; Nissa of Shadowed Boughs; Kagha; Journey to Eternity; Invasion of Ikoria;
  Kamahl's Druidic Vow; Aclazotz.
- *Fuel (self-mill, loot, discard, lands back):* Jace, Memory Adept; Jace, the Perfected Mind;
  Madame Hydra; Wrenn and Realmbreaker; Wrenn and Seven; Thranduil, Sindarin Liege; The Ancient
  One; Arni; Rona, Herald of Invasion; Leader, Super-Genius; Albiorix; Malcolm; Bonny Pall; Glarb.
- *Payoffs:* Black Widow; Syr Konrad; The Mycotyrant (descend); Moonstone (discard → play);
  Doctor Doom, Unrivaled (empty library WINS — self-mill becomes a clock); Cloud of Darkness.
- *A-only interaction:* Sheoldred, Whispering One; Liliana, Death Mage; Cloud of Darkness;
  Yawgmoth, Thran Physician; One Ring to Rule Them All (II destroys all NONlegendary creatures —
  near one-sided here).
- *Pile core ≈ 55 nonland cards; 13 counted interaction before any outside add.*
- *Protect (the ranking cannot see why):* Teval and Oasis of Renewal (they pay for every
  own-graveyard exile), Muldrotha's permanent-type spread (a land, creature, artifact,
  enchantment and planeswalker each recastable), Doctor Doom, Unrivaled (alt-win).

### Deck B — TOP OF THE LIBRARY, commander Glarb, Calamity's Augur
- *Scry/surveil engines:* Matoya; Proft, Consulting Detective; Elrond (Master of Healing, Lord of
  Rivendell, Moon-Reader); Legolas; Arwen Undómiel; Galadriel of Lothlórien; Kasmina; Princess Yue;
  Arwen's Gift; The Clone Saga; Chandra, Chill of Compliance; Jace, Unraveler of Secrets.
- *Play from the top:* Rashmi; Fblthp, Lost on the Range; Bolas's Citadel; Nissa, Steward of
  Elements; Ashiok, Wicked Manipulator.
- *Draw triggers and big top-casts (MV ≥ 4 is free under Glarb, rule 4):* Sheoldred, the
  Apocalypse; Lyra; Reed Richards; Krang, the All-Powerful; Teferi, Temporal Pilgrim; The Theorist;
  Tishana; Jin-Gitaxias // The Great Synthesis; Jin-Gitaxias, Core Augur; Iymrith; Thryx; Leovold.
- *Their library as a resource:* Ashiok, Nightmare Muse; Krang & Shredder; Xanathar; Gix; Jace,
  Memory Adept aimed at them (Yawgmoth's Vile Offering then reanimates from THEIR graveyard).
- *B-only interaction:* M.O.D.O.K. (edict on your second draw each turn); Kitsune; Jin-Gitaxias,
  Progress Tyrant; Davriel, Soul Broker.
- *Pile core ≈ 50 nonland cards; 12 counted interaction.*
- *Protect:* Matoya and Proft (they make Glarb's surveil a card each turn — no tag sees it),
  Fblthp, Lost on the Range (classifier misses its card advantage).

### Variant B2 — ELVES STEAL, commander Maralen, Fae Ascendant (optional)
- Keeps deck B's scry Elves (Elronds, Legolas, Arwen, Galadriel, Rashmi), the theft package and the
  shared removal; swaps the pure draw-trigger slots for: Thranduil, the Elvenking (loot on every
  legendary Elf; borrows Lathril / Morcant / Furgul / Elrond, Moon-Reader from the graveyard);
  Thranduil, Sindarin Liege; Leovold; Celeborn; Lathril; High Perfect Morcant; Kagha; Furgul;
  Tyvar the Bellicose; Abomination of Llanowar; Krydle; Ezuri; Dionus; Gonti; Kotis, the
  Fangkeeper; Rev; Sméagol; The Key to the Vault; Nemata; Yarok (doubles Maralen's exile).
- Maralen's free cast is capped by your Elf + Faerie count and only reads cards exiled THIS turn,
  so it needs MORE Elves than the pile's 22 legendary ones: 8–10 cheap nonlegendary Elves come
  from outside the pile at draft time.

### Out of every shell (34 cards, △/✗ in both)
Jyoti; Nael; Tawnos; Goldberry; Katara (both); Marit Lage's Slumber; Mystic Reflection; Naban;
Callaphe; Invasion of Segovia; Lulu; Mindlink Mech; Alora; Charix; Orvar; Vesuvan Duplimancy;
Zahid; Aphelia; Tatsunari; Liliana of the Dark Realms; Shredder; Skithiryx; Lich's Mastery; Count
Nefaria; Mythweaver Poq; Oyaminartok; Ashaya; Bosco; Mitotic Ultimus; Tezzeret, Master of the
Bridge; Dina, Soul Steeper; Yargle and Multani; Absorbing Man.
