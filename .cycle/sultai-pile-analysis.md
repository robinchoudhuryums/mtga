# Sultai legends pile (250 cards) — analysis (TEMPORARY working doc)

**Status: REOPENED 2026-11-01 for the three-pile split (section 8).** Both decks are drafted (75-historic-brawl Thranduil, 96 Glarb). Phase 1 = the split; phase 2+ = why each card is or is not in each deck. Delete once the owner has the answers.

**Board:** https://claude.ai/artifact/RfDuwKXX3WmTHYcUrLTgAR (slug `c7b18c80-55b2-42c0-93ae-ea36e2fa15be`, source `.cycle/board/index.html`; card images in `.cycle/board/img/` are gitignored — regenerate with `python3 .cycle/board/fetch_images.py`). The owner's picks live in its db collection `picks` (doc id = card-name slug; fields `card`, `picks` ⊂ {addT, cutT, addG, cutG, bench, out}, `note`) — read them with db_list. Per-card reasons are embedded in the page data and republished from `.cycle/board/index.html` each phase (the page also overlays any `reasons` docs from its db, unused so far).
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

## 6. Outside-the-pile search (owner's clarification, 2026-11-01)

The pile is capped at 250 by Arena, so a light theme IN the pile may be deep in the POOL. "Win
from exile" means self-/opponent-mill plus cards that exile libraries heavily or repeatedly.
Measured over the 8,956 Historic-Brawl-legal cards castable in UBG (`/tmp/sultai/measure.py`).

### Phase 1 — the themes rule 3 had ruled out, plus mill/exile
| Theme | Pool (UBG) | In pile | Owned | Verdict |
|---|---|---|---|---|
| Elf bodies | 282 | 22 | 57 | — |
| Elf payoffs (text rewards Elves) | **56** | 9 | 24 | **A full tribe** (deck 49 was built on Dragon 71/20). Rule 3 REVERSED. |
| Elf creatures with an ACTIVATED ability | **95** (34 mana) | 4 | — | **Thranduil's graveyard half is real**: Priest of Titania, Elvish Archdruid, Imperious Perfect, Fauna Shaman, Elvish Warmaster, Deathrite Shaman, Lathril… in the yard, all on Thranduil. His loot puts them there. |
| Wizard bodies | 373 | 20 | 63 | — |
| Wizard payoffs | 13 (+3 Wizard-conditional spells) | 1 | 1 | Still NOT a deck. Wizard's Retort / Arcane Epiphany are a cheap-counter rider for a blue deck that happens to hold Wizards (Glarb is one). |
| Mutate creatures (each with a "whenever this mutates" trigger) | 17 | 1 | 0 | A narrow third option under Brokkos; not part of the two main decks. |
| Opponent mill | **122** | 10 | 10 | **A real win plan.** Doublers: Bruvac the Grandiloquent, Fraying Sanity. Half-library: Traumatize, Fleet Swallower, kicked Maddening Cacophony. Draw→mill bridges: Psychic Corrosion, Teferi's Tutelage, Sphinx's Tutelage. Landfall→mill: Ruin Crab. |
| Repeated library EXILE | 17 | 5 | 3 | Ulamog, the Ceaseless Hunger (20 per attack), Tasha's Hideous Laughter, Ashiok, Nightmare Weaver / Dream Render, Villainous Wealth, Mind's Dilation, Inside Information. |
| Payoffs on their graveyard size | few | 0 | 1 | Consuming Aberration (owned), Visions of Beyond, Syr Konrad. |
| Empty-library win (self-mill) | 4 | 3 | 2 | Laboratory Maniac (owned) joins Doctor Doom, Fblthp, Jace. |

**What phase 1 changes:**
- Elves graduate from "variant" to a full deck. Thranduil becomes a strong commander once the
  OUTSIDE Elves with activated abilities are counted; Maralen stays the steal-flavoured alternative.
- Deck B can be a MILL-OUT deck, not just a library-value deck: Glarb's draw engines feed
  Psychic Corrosion / the Tutelages, and the pile's Ashiok exile cards plus Ulamog / Tasha's finish.
- Wizards and Mutate stay out of the two main decks.

### Phase 2 — graveyard, library, draw/hand, lands, artifacts (`.cycle/sultai-measure2.py`)
| Theme | Pool (UBG) | In pile | Owned | Verdict |
|---|---|---|---|---|
| Reanimation (graveyard → battlefield) | 194 | 10 | 32 | Deep |
| Cast/play from your graveyard | 197 | 7 | 29 | Deep |
| Graveyard-size payoffs (threshold, delirium, "cards in your graveyard") | 296 | 16 | 64 | Deep |
| Self-mill enablers | 256 | 15 | 77 | Deep |
| Descend payoffs | 23 | 3 | 2 | A seasoning inside the graveyard deck, not a deck |
| Discard payoffs (whenever you discard, madness) | 29 | 1 | 3 | Thin; discard stays an ENABLER (loot → graveyard), not a payoff theme |
| Scry/surveil payoffs | 20 | **7** | 2 | The pile already holds a third of the pool's payoffs; it does not grow much outside |
| Cards-leave-your-library triggers | 9 | 2 | 0 | Too narrow to build on |
| Play/cast from the top of your library | 32 | 3 | 7 | Real sub-theme (Courser, Augur of Autumn, Oracle of Mul Daya, Precognition Field, Vivien Monsters' Advocate, Eladamri) |
| Cast from an opponent's library | ≈17 (phase 1 exile list) | 5 | 3 | Sub-theme; most are combat-gated |
| Draw-trigger payoffs | **71** | 6 | **30** | Deep — and it feeds the draw→mill bridges |
| Hand-size payoffs | 60 | 12 | 11 | Sub-theme of a draw deck |
| Landfall payoffs | 88 | 4 | **39** | Deep, mostly green; lands-from-graveyard (Muldrotha, Teval, Wrenn) and fetches (226) feed it |
| Artifact payoffs | 137 | 5 | 31 | A real theme in U/B, light in the pile (12 artifacts, 6 payoff texts) |
| Artifact token makers (Treasure/Clue/Food/Thopter…) | 274 | 6 | 72 | Deep; pairs with artifact payoffs and with draw (Clues) |

**What phase 2 changes:**
- The GRAVEYARD deck is the deepest theme in the whole pool, not just the pile — reanimation,
  recasting and self-mill each run ~200 cards. Muldrotha stays its commander; descend, discard,
  landfall-from-graveyard and artifact recasting (Muldrotha replays an artifact each turn) all fold in.
- Draw triggers are deep (71, 30 owned) and are the bridge to opponent mill (Psychic Corrosion, the
  Tutelages) — so the LIBRARY deck is really a DRAW + MILL/EXILE deck under Glarb, with scry payoffs
  (mostly already in the pile) and top-of-library as seasoning.
- Artifacts are real in the pool but have no Sultai commander that rewards them; they belong as a
  sub-theme (Clue/Thopter makers for the draw deck, recast artifacts for Muldrotha), or as a
  UB-artifact build outside this pile's colour identity.
- Scry payoffs and leave-library triggers do NOT deepen outside the pile — the pile already holds
  most of what exists.

### Phase 3 — leave-graveyard triggers (owner's addition)
| Theme | Pool (UBG) | In pile | Owned |
|---|---|---|---|
| Leave-graveyard trigger payoffs (whenever cards leave / are exiled from your graveyard) | 22 | 3 (Teval, Oasis of Renewal, Syr Konrad) | 5 |
| Graveyard-exile as a cost or fuel (delve, escape, collect evidence, "exile N cards from your graveyard:") | 158 | 6 | 28 |

Outside the pile: Insidious Roots, Desecrated Tomb, Chalk Outline, Attuned Hunter, Kishla Skimmer,
Rot Farm Mortipede, Undead Hand Ninja, Dredger's Insight, Along the Crooked Way, Willow Geist.

**What it changes:** rule 6 treated exiling your own graveyard as a COST. With ~20 leave-graveyard
payoffs it becomes a second engine: delve/escape/Kotis-style costs, recasting and reanimation all
make tokens, cards or damage. **Caveat for a Thranduil deck (G-42):** Thranduil only has the
abilities of Elf cards that STAY in the graveyard, so exile-from-graveyard costs should spend
non-Elf cards; reanimating an Elf trades its borrowed ability for the body.

## 7. Owner's decision (2026-11-01)
Two decks:
1. **Graveyard & Elves** — commander **Thranduil, the Elvenking**: legendary Elves loot cards into
   the graveyard; Elves with activated abilities there become Thranduil's; reanimation, recasting,
   self-mill and leave-graveyard payoffs from deck A's list; landfall Elves and Elf mana.
2. **Draw + mill/exile** — commander **Glarb, Calamity's Augur**: draw-trigger engines that mill
   (Psychic Corrosion, Tutelages), mill doublers (Bruvac, Fraying Sanity), half-library mills,
   repeated library exile (Ulamog, Tasha's, three Ashioks), scry payoffs, top-of-library, hand size,
   Clue/Thopter artifacts.
Next: outside-the-pile shortlists per deck, then `/draft-deck` each.

## 8. Three-pile split (2026-11-01 — owner's request after both decks were drafted)

**Scope:** the 250-card pile plus 177 outside cards the searches surfaced (both decklists, the Glarb candidate pulls, section 6's named cards) = **427 cards**. 13 searched names are not on Arena and are dropped: Hedron Crab, Jace's Erasure, Mindcrank, Kitsune the Fangkeeper, Legolas Greenleaf, Kami of the Crescent Moon, Font of Mythos, Alandra, Fellwar Stone, Kodama's Reach, Three Visits, Fact or Fiction, Behold the Multitude.

**How a card was placed:** the pile cards keep their section-4 hand verdicts (column A ≈ the graveyard deck, now Thranduil's; column B = the library deck, now Glarb's) — a full star step apart sends it to that deck, closer is BOTH, ◇ or worse on both sides is NOT A FIT. Every outside card and every case where the hand verdict and the deck it landed in disagree was placed by hand. `screen`'s fit model was run against both decks and is NOT the decider: Glarb's deck carries `graveyard` as a central theme (its mill fills THEIR yard), so the model rates own-graveyard recursion KEY there — the G-42 polarity trap — and it rates every generic removal spell `tangential` everywhere, because interaction shares no theme. Legendary Elves default to Thranduil (each one entering is a loot).

Marks: **[T]** in Thranduil's list · **[G]** in Glarb's list · **[T+G]** in both. Unmarked = in neither (Phase 2 explains why).

### Pile 1 — better in THRANDUIL (75-historic-brawl) — 113 cards
- *In Thranduil's list (52):* Abomination of Llanowar; Bounty of Skemfar; Cantankerous Keepers; Circle of Dreams Druid; Cloud of Darkness; Dawnhand Eulogist; Deathbloom Ritualist; Dionus, Elvish Archdruid; Dwynen, Gilt-Leaf Daen; Eclipsed Realms; Elderfang Ritualist; Elvish Archdruid; Elvish Mystic; Elvish Warmaster; Fauna Shaman; Gloom Ripper; Harald Unites the Elves; Harald, King of Skemfar; Heartless Act; High Perfect Morcant; Imperious Perfect; Insidious Roots; Izoni, Thousand-Eyed; Journey to Eternity // Atzal, Cave of Eternity; Kagha, Shadow Archdruid; Kamahl's Druidic Vow; Lathril, Blade of the Elves; Leaf-Crowned Visionary; Liliana, Death Mage; Llanowar Elves; Lluwen, Imperfect Naturalist; Lys Alana Dignitary; Marwyn, the Nurturer; Morcant's Eyes; Morcant's Loyalist; Muldrotha, the Gravetide; Oasis of Renewal; Overlord of the Balemurk; Priest of Titania; Selvala, Heart of the Wilds; Shaman of the Pack; Sheoldred, Whispering One; Skemfar Avenger; Teval, the Balanced Scale; Thranduil, Sindarin Liege; Thranduil, the Elvenking; Trystan's Command; Trystan, Callous Cultivator; Voice of the Woods; Wastewood Verge; Woodland Weavemaster; Wrenn and Realmbreaker
- *In neither list (61):* Aclazotz, Deepest Betrayal // Temple of the Dead; Along the Crooked Way; Arni, Humble Scribe; Attuned Hunter; Beledros Witherbloom; Black Widow, Daring Operative; Bonny Pall, Clearcutter; Brokkos, Apex of Forever; Celeborn the Wise; Chalk Outline; Deathrite Shaman; Desecrated Tomb; Drana, the Last Bloodchief; Dredger's Insight; Eladamri, Korvecdal; Emet-Selch of the Third Seat; Ezuri, Stalker of Spheres; Furgul, Quag Nurturer; Ghoulcaller Gisa; Gisa, Glorious Resurrector; Invasion of Ikoria // Zilortha, Apex of Ikoria; Isareth the Awakener; Junji, the Midnight Sky; Kaervek, the Punisher; Kels, Fight Fixer; Kishla Skimmer; Kotis, Sibsig Champion; Krydle of Baldur's Gate; Laboratory Maniac; Lazav, the Multifarious; Leader, Super-Genius; Madame Hydra, Reanimated; Malcolm, Alluring Scoundrel; Mimeoplasm, Revered One; Moonstone, Harsh Mistress; Nael, Avizoa Aeronaut; Nashi, Illusion Gadgeteer; Nashi, Moon's Legacy; Nissa of Shadowed Boughs; Pharaoh Rama-Tut; Prototype X-8; Reezug, the Bonecobbler; Rona, Herald of Invasion // Rona, Tolarian Obliterator; Rot Farm Mortipede; Sauron, the Necromancer; Scavenger's Talent; Sidisi, Brood Tyrant; Sin, Spira's Punishment; Syr Konrad, the Grim; Tamiyo, Compleated Sage; The Ancient One; The Cloning of Shredder; The Mycotyrant; Tyvar the Bellicose; Uchbenbak, the Great Mistake; Ultimecia, Time Sorceress; Undead Hand Ninja; Willow Geist; Wrenn and Seven; Yawgmoth, Thran Physician; Zimone the Calculating // Simple Subtraction

### Pile 2 — better in GLARB (96) — 126 cards
- *In Glarb's list (55):* Arcane Signet; Archive Trap; Ashiok, Nightmare Muse; Ashiok, Nightmare Weaver; Assassin's Trophy; Birds of Paradise; Brainstorm; Breach the Multiverse; Bruvac the Grandiloquent; Consuming Aberration; Counterspell; Cyclonic Rift; Damnation; Dictate of Kruphix; Drown in the Loch; Fraying Sanity; Glarb, Calamity's Augur; Glimpse the Unthinkable; Growth Spiral; Hero's Downfall; Jidoor, Aristocratic Capital // Overture; Jin-Gitaxias, Core Augur; Kaito, Bane of Nightmares; M.O.D.O.K., Evil Intellect; Maddening Cacophony; Matoya, Archon Elder; Mind Stone; Mystic Remora; Notion Thief; Phyrexian Arena; Princess Yue; Proft, Consulting Detective; Psychic Corrosion; Reed Richards, Smartest Man; Restless Reef; Rhystic Study; Ruin Crab; Sheoldred, the Apocalypse; Sphinx Mindbreaker; Sphinx's Tutelage; Startled Awake // Persistent Nightmare; Sunken Hollow; Talisman of Curiosity; Talisman of Dominance; Tasha's Hideous Laughter; Teferi's Ageless Insight; Teferi's Tutelage; Teferi, Temporal Pilgrim; The Master of Lake-town; The Theorist, Jace Beleren; The Water Crystal; Theorix Charm; Thought Collapse; Traumatize; Ulamog, the Ceaseless Hunger
- *In neither list (71):* Altar of Dementia; Arcane Epiphany; Arwen's Gift; Ashiok, Dream Render; Ashiok, Wicked Manipulator; Augur of Autumn; Bolas's Citadel; Brain Freeze; Chandra, Chill of Compliance; Courser of Kruphix; Cruel Somnophage // Can't Wake Up; Cut Your Losses; Didn't Say Please; Drowned Secrets; Duskmantle, House of Shadow; Fblthp, Lost on the Range; Fleet Swallower; Folio of Fancies; Gix, Yawgmoth Praetor; Gonti, Canny Acquisitor; Grindstone; Gyruda, Doom of Depths; Hama, the Bloodbender; Howling Mine; Hullbreaker Horror; Imoti, Celebrant of Bounty; Inside Information; Iymrith, Desert Doom; Jace, Arcane Strategist; Jace, Unraveler of Secrets; Jace, Wielder of Mysteries; Jin-Gitaxias // The Great Synthesis; Jin-Gitaxias, Progress Tyrant; Kasmina, Enigma Sage; Keening Stone; Kefnet the Mindful; Kotis, the Fangkeeper; Krang & Shredder; Krang, the All-Powerful; Lo and Li, Royal Advisors; Lord of the Forsaken; Lyra, Tolarian Archangel; Memory Deluge; Mind's Dilation; Navigator's Ruin; Nemata, Primeval Warden; Nissa, Steward of Elements; Opt; Persistent Petitioners; Phenax, God of Deception; Precognition Field; Preordain; Proft's Eidetic Memory; Radagast of Rhosgobel; Rev, Tithe Extractor; Riverchurn Monument; Rona, Disciple of Gix; Seizan, Perverter of Truth; Seymour Flux; Sméagol, Helpful Guide; Sokka's Haiku; Tam, Observant Sequencer // Deep Sight; Terisian Mindbreaker; The Key to the Vault; Thryx, the Sudden Storm; Tishana, Voice of Thunder; Villainous Wealth; Visions of Beyond; Vivien, Monsters' Advocate; Wan Shi Tong, Librarian; Xanathar, Guild Kingpin

### Pile 3 — good in BOTH / either — 89 cards
- *In both decks (27):* Blooming Marsh; Botanical Sanctum; Breeding Pool; Clearwater Pathway // Murkwater Pathway; Command Tower; Darkbore Pathway // Slitherbore Pathway; Darkslick Shores; Dragonlord Silumgar; Drowned Catacomb; Go for the Throat; Hedge Maze; Hinterland Harbor; Infernal Grasp; Llanowar Wastes; Ob Nixilis Reignited; Overgrown Tomb; Paradise Druid; Price of Fame; Sheoldred // The True Scriptures; Undercity Sewers; Underground Mortuary; Underground River; Watery Grave; Woodland Cemetery; Yavimaya Coast; Yawgmoth's Vile Offering; Zagoth Triome
- *In Thranduil's list (6):* Elrond, Moon-Reader; Garruk, Veiled Butcher; Leovold, Emissary of Trest; Maralen, Fae Ascendant; Vraska, Betrayal's Sting; Vraska, Golgari Queen
- *In Glarb's list (4):* Ashiok, Sculptor of Fears; Doctor Doom, Unrivaled; Jace, Memory Adept; Jace, the Perfected Mind
- *In neither list (52):* Albiorix, Goose Tyrant // Wild Goose Chase; Anoint with Affliction; Arwen Undómiel; Bitter Triumph; Bloodchief's Thirst; Consider; Cultivate; Davriel, Soul Broker; Delighted Halfling; Doctor Doom; Elrond, Lord of Rivendell; Elrond, Master of Healing; Erebos, God of the Dead; Farseek; Fatal Push; Fblthp, Impossibly Lost; Feed the Swarm; Galadriel of Lothlórien; Garruk, Caller of Beasts; Gisa, the Hellraiser; Ioreth of the Healing House; Jace Reawakened; Kenrith's Transformation; Kiora, the Crashing Wave; Kitsune, Dragon's Daughter; Legolas, Counter of Kills; Leyline Immersion; Maha, Its Feathers Night; Memory Lapse; Mu Yanling, Sky Dancer; Multiversal Recruitment; Murderous Rider // Swift End; Mystic Snake; Nature's Lore; One Ring to Rule Them All; Oracle of Mul Daya; Pongify; Rashmi, Eternities Crafter; Ringsight; Sarulf, Realm Eater; Saw It Coming; Sheoldred's Edict; Talisman of Resilience; Tamiyo, Inquisitive Student // Tamiyo, Seasoned Scholar; Tear Asunder; The Clone Saga; The Everflowing Well // The Myriad Pools; Thought Scour; Toxic Deluge; Vraska Joins Up; Wizard's Retort; Yarok, the Desecrated

### Not a fit for either (listed so nothing is silently dropped) — 98 cards
- *In neither list (98):* Absorbing Man; Alora, Rogue Companion; Aphelia, Viper Whisperer; Ashaya, Soul of the Wild; Azula, Ruthless Firebender; Bosco, Just a Bear; Callaphe, Beloved of the Sea; Charix, the Raging Isle; Chevill, Bane of Monsters; Chulane, Teller of Tales; Count Nefaria; Dina, Essence Brewer; Dina, Soul Steeper; Gadwick, the Wizened; Gale, Conduit of the Arcane; Gandalf, Friend of the Shire; Geralf, the Fleshwright; Glamdring, Foe-hammer // Gleam of Death; God-Eternal Kefnet; Golbez, Crystal Collector; Goldberry, River-Daughter; Goreclaw, Terror of Qal Sisma; Graviton, Fundamental Force; Greensleeves, Maro-Sorcerer; Impossible Man; Ink-Eyes, Servant of Oni; Invasion of Segovia // Caetus, Sea Tyrant of Segovia; Irenicus's Vile Duplication; Irma, Part-Time Mutant; Jadzi, Oracle of Arcavios // Journey to the Oracle; Jyoti, Moag Ancient; K'rrik, Son of Yawgmoth; Katara, Bending Prodigy; Katara, Waterbending Master; Kingpin, Wilson Fisk; Kinnan, Bonder Prodigy; Kiora of Salt and Sand; Kira, Great Glass-Spinner; Kogla and Yidaro; Kona, Rescue Beastie; Kruphix, God of Horizons; Lazav, Familiar Stranger; Lich's Mastery; Liliana of the Dark Realms; Lo and Li, Twin Tutors; Locke Cole; Long Feng, Grand Secretariat; Lord Dregg, Insect Invader; Lulu, Stern Guardian; Marit Lage's Slumber; Massacre Girl, Known Killer; Mindlink Mech; Mitotic Ultimus; Morlun, Devourer of Spiders; Mystic Reflection; Mythweaver Poq; Naban, Dean of Iteration; Niv-Mizzet, Visionary; Oko, the Trickster; Omega, Heartless Evolution; Orvar, the All-Form; Oyaminartok, Polar Werebear; Pharika, God of Affliction; Pol Jamaar, Illusionist; Roalesk, Apex Hybrid; Ruric Thar, Biomagus; Sarevok the Usurper; Shredder, Shadow Master; Skithiryx, the Blight Dragon; Slimefoot, Thallid Transplant; Splinter, the Mentor; Syr Elenora, the Discerning; Taeko, the Patient Avalanche; Tatsunari, Toad Rider; Tawnos, the Toymaker; Tergrid, God of Fright // Tergrid's Lantern; Tetzimoc, Primal Death; Tezzeret, Betrayer of Flesh; Tezzeret, Master of the Bridge; The Magic Mirror; Tome of the Infinite; Tui and La, Moon and Ocean; Tyvar Kell; Unctus, Grand Metatect; Urza, Lord High Artificer; Vesuvan Duplimancy; Victor Timely, Wily Tycoon; Vnwxt, Verbose Host; Wasp, Shrinking Savior; Whisper, Blood Liturgist; Witch-king of Angmar; Witherbloom, the Balancer; Xande, Dark Mage; Yahenni, Undying Partisan; Yargle and Multani; Ygra, Eater of All; Yue, the Moon Spirit; Zahid, Djinn of the Lamp

## 9. Phase 2 — why each card is NOT in its pile's deck

### 9.1 Pile 1 → Thranduil (75-historic-brawl): the 61 cards not in the list

**The test every card had to pass.** The deck is Elf-first: 40 of its 63 nonland cards are Elves (17 legendary),
and 38 of its 45 creatures are. Thranduil pays twice for that density — a legendary Elf entering loots, and an
Elf CARD in the yard lends him its activated abilities. So a graveyard card that is NOT an Elf has to beat an Elf
for the slot, and the yard is mostly Elves, which turns any "exile cards from your graveyard" cost into a tax on
Thranduil's toolbox (G-42). The graveyard package already holds Teval, Muldrotha, Oasis of Renewal, Insidious
Roots, Overlord of the Balemurk, Kamahl's Druidic Vow, Journey to Eternity, Sheoldred, Whispering One and Wrenn
and Realmbreaker.

**A. Real swap candidates — left out on slot pressure, not on merit (propose, don't apply).**
| Card | Why it was not in the draft | What it would do here |
|---|---|---|
| Deathrite Shaman | Missed at draft time — it surfaced in the phase-1 Elf search but never reached the list | A 1-mana Elf with THREE activated abilities, so it is a Thranduil card twice: in play, and in the yard (`{T}: Exile target land card from a graveyard. Add one mana of any color`; `{B}`: drain 2; `{G}`: gain 2). Can target the OPPONENT'S graveyard, so it need not eat Elves. **Strongest add on this list.** |
| Eladamri, Korvecdal | Missed at draft time | Legendary Elf (a loot); "You may cast creature spells from the top of your library" with 45 creatures; from the yard Thranduil gets `{G}, {T}, Tap two untapped creatures: … put it onto the battlefield` — a free creature cheat every turn. |
| Tyvar the Bellicose | Missed at draft time | Legendary Elf; "Whenever a mana ability of this creature resolves, put +1/+1 counters equal to the mana produced" turns the 11 mana Elves into growing bodies; Elves attacking gain deathtouch. |
| Yawgmoth, Thran Physician | Not an Elf; the deck runs no dedicated sacrifice outlet | `Pay 1 life, Sacrifice another creature: -1/-1 counter … and draw a card` is repeatable removal plus card draw off the Elf tokens (Imperious Perfect, Elvish Warmaster, Voice of the Woods, Lathril). |
| Wrenn and Seven | Not an Elf; Wrenn and Realmbreaker took the green-walker slot | +1 reveals four, lands to hand and "the rest into your graveyard" — a self-mill that never misses a land drop; −3 is a huge reach body. A real upgrade for any non-Elf slot. |
| Sidisi, Brood Tyrant | Not an Elf, and its mill is random where Thranduil's loot chooses | Mills three on entry and attack; with 45 creatures most mills make a 2/2 Zombie. Strong, just not Elf-synergistic (the Zombies feed nothing Elf-gated). |
| Invasion of Ikoria | Not an Elf; competes with Kamahl's Druidic Vow and Journey as a cheat | `search your library and/or graveyard for a non-Human creature card with mana value X or less and put it onto the battlefield` — a tutor that also reanimates; finds Priest of Titania at X=2. |
| Moonstone, Harsh Mistress | Not an Elf | "Whenever you discard a card, you may exile that card … you may play that card" — every Thranduil loot becomes card-neutral. But it EXILES the discard, which removes an Elf's ability from Thranduil (G-42), so it is best with non-Elf discards. ◇ |

**B. Exile your own graveyard as the cost or the effect — fights Thranduil's toolbox (G-42).**
| Card | Operative clause | Why not |
|---|---|---|
| Kotis, Sibsig Champion | "cast a creature spell from your graveyard by exiling three other cards from your graveyard" | Three cards a turn, in a yard that is mostly Elves; Muldrotha recasts without exiling anything. |
| Mimeoplasm, Revered One | "exile up to X creature cards from your graveyard" | Eats exactly the Elf creature cards Thranduil borrows from. |
| Sin, Spira's Punishment | "exile a permanent card from your graveyard at random" | Random — will hit Elves; 7 mana. |
| Sauron, the Necromancer | "Whenever Sauron attacks, exile target creature card from your graveyard" | Same tax each attack; the token is temporary. |
| The Cloning of Shredder | "Exile target creature card from your graveyard" | Six mana for copies of a card Thranduil was already using. |
| Nashi, Moon's Legacy | "exile up to one target legendary or Rat card from your graveyard and copy it" | Can target a non-Elf legend, but the deck's legends ARE mostly Elves; menace 3-drop otherwise. |
| Tamiyo, Compleated Sage | "−X: Exile target nonland permanent card with mana value X from your graveyard" | Same; the +1 tap is tempo, not removal. |
| Kaervek, the Punisher | "exile up to one target black card from your graveyard and copy it" | Needs crimes; few black cards to copy outside the Elf core. |
| Ultimecia, Time Sorceress | Transform: "exile eight cards from your graveyard" | Eight cards is most of Thranduil's toolbox; the extra turn costs nine mana. |

**C. Leave-the-graveyard payoffs (the phase-3 search) — the deck already runs the best three.**
Teval, Oasis of Renewal and Insidious Roots are in. The rest are smaller, non-Elf versions of the same payoff, and the
deck's leave-graveyard events are occasional (Muldrotha recasts, reanimation, Journey) rather than every turn:
| Card | Operative clause | Why not |
|---|---|---|
| Chalk Outline | "Whenever one or more creature cards leave your graveyard, create a 2/2 … then investigate" | Best of the rest; 4-mana do-nothing until a recast. First reserve if the recursion count grows. |
| Desecrated Tomb | "…leave your graveyard, create a 1/1 black Bat" | Weaker Chalk Outline. |
| Along the Crooked Way | ETB "return target creature card … to your hand"; leave → amass Goblins | The Goblin army is off-tribe. |
| Attuned Hunter / Willow Geist / Rot Farm Mortipede | +1/+1 counters or menace/lifelink when cards leave | Vanilla-ish bodies that need the event every turn. |
| Kishla Skimmer | "Whenever a card leaves your graveyard during your turn, draw a card" (once a turn) | Fine card draw, but a 2-mana non-Elf; Elrond, Moon-Reader is the draw engine here. |
| Undead Hand Ninja | drain 1 when creature cards leave | Too small. |
| Dredger's Insight | ETB mill four, take an artifact/creature/land | A one-shot dig; the deck has better self-mill on Elf bodies. |

**D. Non-Elf graveyard bodies — good cards, outranked by an Elf in the same job.**
| Card | Why not |
|---|---|
| Madame Hydra, Reanimated | Self-mill 2 per attack and grows with creature cards; a non-Elf 4-drop beater in a deck whose bodies want to be Elves. |
| Black Widow, Daring Operative | Mill 3 then drains = creature cards in yard on combat damage — combat-gated, 5 mana. |
| Isareth the Awakener | Reanimates on attack for {X}, but the returned creature is exiled if it leaves — and the reanimated Elf no longer lends Thranduil its ability. |
| Junji, the Midnight Sky | A 5-mana flier whose value is its death trigger; the deck wants Elves in the yard, not Dragons. |
| Drana, the Last Bloodchief | "defending player chooses a nonlegendary creature card" — the OPPONENT picks, so they give you a mana Elf. |
| Uchbenbak, the Great Mistake | Descend 8 recursion for a 6/4 vigilance-menace body; nothing Elf. |
| Beledros Witherbloom | Pest each upkeep; 7 mana and "Pay 10 life" untap — no Elf payoff for Pests. |
| Ghoulcaller Gisa | Sac outlet that makes Zombies = power; Elves are small, so X is 1–2. |
| Gisa, Glorious Resurrector | Steals THEIR dead creatures for a turn; off-plan here (a better fit for a removal-heavy deck). |
| Nissa of Shadowed Boughs | −5 reanimates; landfall loyalty — the deck plays ~1 land a turn, so −5 is slow. |
| Brokkos, Apex of Forever | Recursive mutate threat; Elves are non-Human so it can mutate, but it adds a body, not an engine. |
| Bonny Pall, Clearcutter | 6 mana; "Whenever you attack, draw a card, then … put a land card from your hand or graveyard onto the battlefield" — real value, wrong curve slot beside Selvala/Kamahl's Vow. |
| Aclazotz, Deepest Betrayal | A 5-mana flier with hand attack; strong card, no Elf or graveyard tie. |

**E. Looters and discard engines — Thranduil already IS the looter.**
Every legendary Elf entering draws two and discards one, so a non-Elf looter duplicates the commander:
Arni, Humble Scribe (`{T}: Draw a card, then discard a card`); Rona, Herald of Invasion (same, untaps on legendary
spells — the closest of these, since most of the deck is legendary); Leader, Super-Genius (connive each combat);
Malcolm, Alluring Scoundrel (combat-gated loot); Pharaoh Rama-Tut (connives on noncreature spells — 19 here);
The Ancient One (loot that mills a player; descend 8 to attack). None is bad; each lost to an Elf.

**F. Legendary Elves that are only a loot trigger.** The deck already has 17 legendary Elves; these add the trigger
and little else:
| Card | Why not |
|---|---|
| Celeborn the Wise | "Whenever you attack with one or more Elves, scry 1" and a pump — combat-only, minor. |
| Ezuri, Stalker of Spheres | "Whenever you proliferate, draw a card" — the deck has one proliferate source (Vraska, Betrayal's Sting). |
| Furgul, Quag Nurturer | `{T}, Sacrifice a creature: Add {G}` equal to power — a sac outlet Thranduil can borrow, plus a free Leech each turn. The closest of these to a swap; Alchemy (conjure). ◇ |
| Krydle of Baldur's Gate | Combat trigger mills 1 / scry 1 — negligible. |
| Nael, Avizoa Aeronaut | Domain: Sultai lands give at most 3 basic types, so "if there are five … draw a card" never happens. |

**G. Plan mismatches.**
| Card | Why not |
|---|---|
| Laboratory Maniac | Self-mill alt-win; a 100-card deck never empties its own library on purpose. |
| Emet-Selch of the Third Seat | Pays off instants/sorceries from the yard; the deck runs 8. |
| Kels, Fight Fixer | Sacrifice payoff; the deck has no sacrifice engine (Yawgmoth would be the outlet, see A). |
| Scavenger's Talent | Same — Food and "whenever you sacrifice" need an outlet the deck lacks. |
| The Mycotyrant | Counts Fungi/Saprolings; descend tokens only. |
| Prototype X-8 | 10 mana minus 2 per creature card in the yard; its "sacrifice it, conjure a duplicate" line is a gimmick here. |
| Lazav, the Multifarious | Copies a creature card in the yard for {X} — mostly copying an Elf Thranduil already has. |
| Reezug, the Bonecobbler | Casts a creature card from the yard as an artifact; recasting an Elf takes its ability off Thranduil. |
| Nashi, Illusion Gadgeteer | Conjures a copy of a yard card into hand (keeps the original — no G-42 cost); a 4-mana non-Elf. ◇ |
| Zimone the Calculating | Prepared on self-mill; the adventure is a −3/−0. Minor. |
| Syr Konrad, the Grim | Pings on every creature death, mill and leave-graveyard; strong in a self-mill deck, but 5 mana for 1-point pings. Bench. |

### 9.2 Pile 2 → Glarb (96): the 71 cards not in the list

**The test every card had to pass.** Deck 96 wins by emptying the opponent's library, and its engine is DRAWING: Psychic Corrosion and both Tutelages turn each draw into mill 2, Bruvac doubles, The Water Crystal adds 4. Its 64 nonland cards hold 42 blue spells, 21 instants/sorceries, 28 noncreature spells of mana value 3+, and 20 creatures, most with toughness 4–5. Glarb already plays lands and casts mana value 4+ off the top, so a card that only does that is redundant, and a card that needs combat damage or sacrifice fodder asks for something this control deck does not build. (`Jin-Gitaxias` and `Jin-Gitaxias // The Great Synthesis` were one card listed twice; collapsed.)

**Swap candidate (11).**
| Card | Why not in the list |
|---|---|
| Krang, the All-Powerful | "If a player drawing a card causes a triggered ability of a permanent you control to trigger, that ability triggers an additional time" doubles Psychic Corrosion, both Tutelages, Sheoldred and The Theorist — the deck's whole engine. **Strongest add on this list.** Left out on slot count. |
| Phenax, God of Deception | Gives your creatures `{T}: Target player mills X cards, where X is this creature's toughness`. Most of the 20 creatures here have toughness 4–5 (Bruvac, Matoya, Reed, both Sheoldreds, Silumgar, M.O.D.O.K.), so each is a mill-4 engine, doubled under Bruvac. Indestructible. |
| Jin-Gitaxias // The Great Synthesis | "Whenever you cast a noncreature spell with mana value 3 or greater, draw a card" — 28 such spells here, and each draw mills two. Owned. Lost its slot to Jin-Gitaxias, Core Augur, but both fit. |
| Drowned Secrets | "Whenever you cast a blue spell, target player mills two cards" — 42 blue spells here. A 2-mana engine that does not need a draw. |
| Jin-Gitaxias, Progress Tyrant | Copies your first artifact/instant/sorcery each turn — a second Traumatize empties a library — and counters the opponent's first one. Mana value 7, so Glarb casts it off the top. |
| Seizan, Perverter of Truth | "At the beginning of each player's upkeep, that player loses 2 life and draws two cards": the opponent loses two library cards a turn, and your two draws mill four through Psychic Corrosion. Symmetric, which this deck wants (it already runs Dictate of Kruphix). |
| Visions of Beyond | 1 mana: "If a graveyard has twenty or more cards in it, draw three cards instead" — the opponent's graveyard passes 20 early here, so it is a 1-mana draw-three (six milled through Corrosion). |
| Lo and Li, Royal Advisors | `{2}{U/B}: Target player mills four cards`, repeatable at instant speed; an Advisor (with Bruvac and The Master of Lake-town) that grows when they mill. |
| Riverchurn Monument | Owned. `{1}, {T}`: mill two every turn, and once per game its exhaust mills "cards equal to the number of cards in their graveyard" — doubles a half-milled yard. |
| Chandra, Chill of Compliance | Owned. +1 surveil feeds Matoya and Proft; the other +1 adds mana for noncreature spells; −X stuns a threat. Screened KEY against the list. |
| Memory Deluge | Instant: two of the top X, then flashback — four draws for eight mana of the late game, each draw milling two. |

**Different finisher, same job (11).**
| Card | Why not in the list |
|---|---|
| Fleet Swallower | "Whenever this creature attacks, target player mills half their library" — a 7-mana creature that must attack; Traumatize and kicked Maddening Cacophony do it from the hand. |
| Cut Your Losses | Half a library for 6 (twice with casualty); the deck already holds Traumatize, Maddening Cacophony and Jidoor's Overture as half-library mills. |
| Terisian Mindbreaker | Half a library on attack, unearth for `{1}{U}{U}{U}`; a 7-mana artifact creature doing Fleet Swallower's job. |
| Jace, Wielder of Mysteries | +1 mills two and draws one (four milled under Corrosion); its alt-win needs YOUR library empty, which this deck never aims for. `{1}{U}{U}{U}` is hard in three colours. |
| Gyruda, Doom of Depths | "Each player mills four cards" and you take a creature from among them — a one-shot, symmetric 6-drop. |
| Cruel Somnophage // Can't Wake Up | Mill four for 2, then a body that grows with creature cards in all graveyards. Fine; smaller than the deck's 2-mana mills (Glimpse the Unthinkable mills ten). |
| Hama, the Bloodbender | Owned. Mills three and lets you cast one of their noncreature spells by waterbending — deck 22's engine piece; a 5-mana one-shot here. |
| Brain Freeze | Mill three plus storm; the deck casts one or two spells a turn, so it is usually mill three. |
| Navigator's Ruin | Raid — mill four only if you attacked; this deck rarely attacks. |
| Didn't Say Please | Counter + mill three — the same card as Thought Collapse, which is in. The first card to add if you want more counters. |
| Sokka's Haiku | Owned. Counter + draw, but "mill three cards" mills YOU, and it costs 5. |

**Mill outlet whose cost the deck lacks (6).**
| Card | Why not in the list |
|---|---|
| Altar of Dementia | "Sacrifice a creature: mills … equal to the sacrificed creature's power" — the deck makes almost no fodder (its tokens are a few Ashiok Nightmares). |
| Lord of the Forsaken | `{B}, Sacrifice another creature: mill three` — same missing fodder; 6 mana. |
| Persistent Petitioners | Its 12-card mill needs four Advisors tapped; it is the one card a deck may run in any number, so it only works as a dozen-copy package — a different deck. |
| Grindstone | `{3}, {T}`: mill two, repeating while the two share a colour — about 2–4 a turn for 3 mana each turn. |
| Keening Stone | 6 to cast and `{5}, {T}` to mill X = their graveyard; Riverchurn Monument's exhaust does the same once for 4. |
| Duskmantle, House of Shadow | A land that makes only colourless — in a three-colour deck already at 3.5 points of tapped-land cost — for a 3-mana mill one. |

**Duplicates Glarb's top-of-library (9).**
| Card | Why not in the list |
|---|---|
| Bolas's Citadel | Glarb already casts MV 4+ off the top; Citadel adds the cheap ones for life. `{3}{B}{B}{B}` with 20 black sources, and the life matters against aggro. |
| Fblthp, Lost on the Range | Plots from the top — a slower version of what Glarb already does. |
| Precognition Field | Instants and sorceries from the top (21 here) — the closest of these; covers the cheap ones Glarb cannot. Bench. |
| Augur of Autumn | Lands from the top — Glarb does it; the creature half needs coven. |
| Courser of Kruphix | Lands from the top plus life; Glarb does the first part. `{1}{G}{G}` on 15 green sources. |
| Vivien, Monsters' Advocate | Creatures from the top; the deck runs 20 creatures, mostly utility. `{3}{G}{G}`. |
| Nissa, Steward of Elements | Scry 2 and puts lands/small creatures from the top into play; green-blue value without a mill tie. |
| Imoti, Celebrant of Bounty | Cascade on mana value 6+ — the deck has few 6+ spells. |
| Rona, Disciple of Gix | Exiles one of YOUR historic cards to cast later and exiles your own top card for {4}; little here. |

**Cast their cards / combat-gated (11).**
| Card | Why not in the list |
|---|---|
| Gonti, Canny Acquisitor | Steals a card on combat damage; the deck is a control deck that rarely connects. |
| Rev, Tithe Extractor | Treasure + steal on combat damage — same problem. |
| Kotis, the Fangkeeper | Exiles X on combat damage and casts them free — an aggressive card in a deck that wins by milling. |
| Gix, Yawgmoth Praetor | Combat draws; its `{4}{B}{B}{B}` exile needs a hand to discard. |
| Xanathar, Guild Kingpin | Strong — they cannot cast spells on your turn and you play their top card — but 6 mana for a value engine the mill plan does not need. Bench. |
| Krang & Shredder | Owned. Exiles to a nonland and casts it if a permanent left your control — needs a sacrifice the deck lacks. |
| Villainous Wealth | Exile X of their library and cast them — real library exile, but `{X}{B}{G}{U}` competes with Tasha's Hideous Laughter, which exiles until 20 total mana value — usually ten or more cards — for 3. |
| Inside Information | Exile X and play them this turn for life; a one-turn burst. |
| Mind's Dilation | 7 mana; exiles one card per opponent spell — slow as library exile. |
| The Key to the Vault | Equipment that casts from YOUR library on combat damage — combat-gated. |
| Sméagol, Helpful Guide | Needs a creature to die each turn for the Ring to tempt you. |

**Draw engine, outranked (21).**
| Card | Why not in the list |
|---|---|
| Howling Mine | Symmetric extra draw — the same job as Dictate of Kruphix, which is in; a second one would refill their hand too. Bench. |
| Lyra, Tolarian Archangel | Owned. A 3/3 Angel at end step when you drew three — common here, but it is a body, not a draw or a mill. |
| Arcane Epiphany | Draw three for 4 (Glarb is a Wizard); fine, outranked by the repeatable engines. |
| Arwen's Gift | Scry 2, draw 2 (cheaper with two legends); one-shot. |
| Jace, Arcane Strategist | 6 mana for +1: draw a card. |
| Jace, Unraveler of Secrets | 5 mana; +1 scry 1 then draw (Matoya draws again). Close; −2 bounce is tempo. |
| Iymrith, Desert Doom | Draws on combat damage only. |
| Seymour Flux | Pay 1 life: draw one each upkeep — a Phyrexian Arena on a body, and Arena is in. |
| Kefnet the Mindful | `{3}{U}`: draw one — an expensive sink. |
| Tishana, Voice of Thunder | Draws one per creature you control — usually 2–4 here; 7 mana. |
| Wan Shi Tong, Librarian | Owned. Flash X body that draws half X, and more when they search; decent filler. |
| Proft's Eidetic Memory | Draws one, no hand size, counters on combat — the counters do nothing here. |
| Tam, Observant Sequencer // Deep Sight | Owned. Draw one on landfall-prepared casts; small. |
| Kasmina, Enigma Sage | +2 scry 1 (feeds Matoya) and shares loyalty abilities with the deck's three Ashioks and Jaces — cute, low impact. |
| Thryx, the Sudden Storm | Spells with mana value 5+ cost {1} less and can't be countered — a flash flier; the deck's MV 5+ spells mostly come off the top already. |
| Radagast of Rhosgobel | First creature each turn costs {2} less with flash; 20 creatures, few of them cheap. |
| Hullbreaker Horror | A 7-mana bounce engine; strong in control, but each turn's mill matters more than tempo here. |
| Nemata, Primeval Warden | Exiles their dying creatures (keeps them out of the graveyard Consuming Aberration counts) and draws off Saprolings. |
| Opt | Scry 1 then draw — under Matoya that is two draws, four milled. A cheap filler; Brainstorm is in. |
| Preordain | Scry 2 then draw; same as Opt, slightly better. |
| Folio of Fancies | `{X}{X}, {T}`: each player draws X (both libraries shrink; yours mills them twice through Corrosion), then `{2}{U}` mills them equal to hand size. A real engine; bench. |

**Fights the engine (G-42) (2).**
| Card | Why not in the list |
|---|---|
| Ashiok, Dream Render | Cut at draft: its −1 "exile each opponent's graveyard" empties the yard Consuming Aberration, Drown in the Loch and Sheoldred's transform count. |
| Ashiok, Wicked Manipulator | "If you would pay life … exile that many cards from the top of your library instead" — Phyrexian Arena, Doctor Doom and Infernal Grasp would exile YOUR library in a deck that already draws hard. Its −7 is a real finisher; the static is the problem. |

### 9.3 Pile 3 → either deck: the 62 cards not in both lists

**How to read it.** Both decks are Historic Brawl Sultai, so every card here is castable and legal in both; the question is which deck's ENGINE it feeds. Thranduil's engine is legendary Elves entering (a loot) and Elf cards in the graveyard; Glarb's is drawing (each draw mills two) and casting mana value 4+ off the top. Both decks already sit at the A floor (interaction 15 and 16), so removal here is interchangeable rather than missing. Copies are shared in Arena, so a card can go in both.

**Swap candidate (9).**
| Card | Thranduil (75-historic-brawl) | Glarb (96) |
|---|---|---|
| Yarok, the Desecrated | If a permanent entering causes a trigger "that ability triggers an additional time" — Thranduil's legendary-Elf loot becomes draw 4, discard 2, and every Elf ETB doubles. **Strong add.** | Doubles Sphinx Mindbreaker (mill 20) and Sheoldred's edict, but few ETBs here. |
| Ioreth of the Healing House | `{T}: Untap two other target legendary creatures` — untap Thranduil for a second borrowed {T} ability each turn (Dionus's job, again). **Strong add.** | Untaps Glarb for a second surveil 2, which Matoya turns into a second draw. Real, smaller. |
| One Ring to Rule Them All | Chapter II "Destroy all nonlegendary creatures" kills most of the Elves. | II is nearly one-sided here (6 nonlegendary creatures), I mills each player by your Ring-bearer's power, and III drains for each creature card in THEIR graveyard — which the mill fills. **Strong add.** |
| Multiversal Recruitment | Copy Priest of Titania or Voice of the Woods, flashback later. Fine. | "Create a token that's a copy of target creature you control, except it isn't legendary" — a second Bruvac quadruples every mill. **Spicy add.** |
| Tamiyo, Inquisitive Student // Tamiyo, Seasoned Scholar | Flips on the third draw in a turn — Thranduil's loot gets there; the walker's −3 regrows instants/sorceries (8 here). | Flips on your third draw — routine here — and her −7 draws half your library: through Psychic Corrosion that mills them for about twice as many. Spicy, risky. |
| Garruk, Caller of Beasts | +1: reveal five, all creature cards to hand — about 2 a turn with 45 creatures in 99 cards. A real card-advantage engine for the Elf deck. | 20 creatures, so +1 finds about one. |
| Wizard's Retort | No Wizards; a plain 3-mana counter. | Glarb is a Frog Wizard, so it costs `{U}{U}` with Glarb out. The best counter left out. |
| Tear Asunder | Kicked, it exiles any nonland permanent — the deck answers few noncreature permanents (4 of 15 pieces). Good add. | Same: kicked, a 4-mana exile-anything; the deck has Assassin's Trophy and Cyclonic Rift already. |
| The Everflowing Well // The Myriad Pools | Mill two, draw two — the mill feeds Thranduil. | Draw two mills four through Corrosion. Owned. Either is fine. |

**Removal (interchangeable) (13).**
| Card | Thranduil (75-historic-brawl) | Glarb (96) |
|---|---|---|
| Murderous Rider // Swift End | Instant kill + a lifelink body. Interchangeable with Go for the Throat. | Same. |
| Sheoldred's Edict | Instant edict that also hits planeswalkers or a token. Interchangeable. | Same. |
| Bloodchief's Thirst | Sorcery; 1 mana early, 4 kicked for anything. Interchangeable. | Same. |
| Fatal Push | Mana value 2 or less without revolt — narrow in Brawl's bigger threats. | Same. |
| Feed the Swarm | Also kills an enchantment — one of the few noncreature answers; you lose life equal to its mana value. | Same. |
| Bitter Triumph | Discard a card — fuel here — or pay 3 life: instant kill of a creature or planeswalker. Good fit. | Discarding costs a card in a draw deck; pay 3 life instead. |
| Anoint with Affliction | Mana value 3 or less only. | Same. |
| Pongify | 1 mana but gives them a 3/3. | Same. |
| Toxic Deluge | A sweeper that kills your own Elves. | A sweeper; the deck already runs Damnation. |
| Kenrith's Transformation | Turns a threat into a 3/3 and draws a card. | Same, and the draw mills two. |
| Davriel, Soul Broker | −3 perpetual −3/−3; +1 taxes attackers. Real removal the classifier misses. | Same. |
| Kitsune, Dragon's Daughter | 6 mana: swap a weak creature of yours for their best. | Same; mana value 6, so Glarb can cast it off the top. |
| Sarulf, Realm Eater | Slow, conditional sweeper. | Same. |

**Counterspell (3).**
| Card | Thranduil (75-historic-brawl) | Glarb (96) |
|---|---|---|
| Memory Lapse | Counters are off-plan in a tap-out Elf deck. | Counter that puts the spell back on top of their library — it delays, and it undoes a mill. |
| Saw It Coming | Off-plan here. | A 3-mana counter (foretell 2); outranked by Wizard's Retort. |
| Mystic Snake | Off-plan here. | Flash counter on a body; `{1}{G}{U}{U}` on 15 green sources. |

**Ramp (6).**
| Card | Thranduil (75-historic-brawl) | Glarb (96) |
|---|---|---|
| Nature's Lore | Fetches any Forest-typed land untapped — Overgrown Tomb, Breeding Pool, Zagoth Triome. The deck already has 11 mana Elves. | Same; 8 ramp pieces already. |
| Cultivate | Two basics; the deck ramps on Elves. | Slower than the rocks in the list. |
| Farseek | Finds Watery Grave / Overgrown Tomb tapped. Fine. | Same. |
| Talisman of Resilience | Elves are better ramp here. | Cut at draft for Kaito, Bane of Nightmares. |
| Delighted Halfling | Any colour for legendary spells, uncounterable — good with 17 legendary Elves, but not an Elf. | Fewer legends here. |
| Oracle of Mul Daya | An Elf: extra land drop and lands from the top. Good. | Extra land drop plus Ruin Crab's landfall; Glarb already plays lands from the top. |

**Scry Elf (6).**
| Card | Thranduil (75-historic-brawl) | Glarb (96) |
|---|---|---|
| Arwen Undómiel | A legendary Elf (a loot trigger), but its payoff is scry, which the deck barely does. | Scry payoff with Matoya; small. |
| Elrond, Lord of Rivendell | Legendary Elf; scry 1 per creature entering — modest. | Each scry triggers Matoya — a draw per creature entering. Close. |
| Elrond, Master of Healing | Legendary Elf; counters on scry, draws when targeted. | Few creatures to put counters on. |
| Galadriel of Lothlórien | Legendary Elf; scry ramp needs the Ring. | Lands onto the battlefield on scry — ramp plus Matoya draws. |
| Legolas, Counter of Kills | Legendary Elf body; minor text. | Minor. |
| Rashmi, Eternities Crafter | Legendary Elf; a free spell off the top each turn. Bench in both. | Same, and the top card is visible under Glarb, so you know when it hits. |

**Value card (15).**
| Card | Thranduil (75-historic-brawl) | Glarb (96) |
|---|---|---|
| Albiorix, Goose Tyrant // Wild Goose Chase | The adventure draws two, discards two — fuel. Flier body after. | Draw two mills four. |
| Doctor Doom | Two 3/3 Doombots and a draw each end step for 6. | The end-step draw mills two. |
| Erebos, God of the Dead | `{1}{B}, Pay 2 life: Draw a card`. | Same, and each draw mills two. |
| Fblthp, Impossibly Lost | Draw two on combat damage. | Rarely attacks. |
| Gisa, the Hellraiser | Zombies on crimes (any removal you aim at them) — off-tribe. | Same. |
| Jace Reawakened | Loot every turn — feeds the yard. | Loot draws mill two. |
| Kiora, the Crashing Wave | −1 draw + extra land; +1 fogs one threat. | Same. |
| Leyline Immersion | On Thranduil: ward 2 and `{T}`: five mana for spells — but it spends the {T} he uses for borrowed abilities. | Same on Glarb: it spends his surveil tap. |
| Maha, Its Feathers Night | Their creatures have base toughness 1 — pairs with Gloom Ripper. Flier. | A big flier. |
| Mu Yanling, Sky Dancer | −3: a 4/4 flier. | Same. |
| Ringsight | Tutor a card sharing a colour with a legendary creature. | Same. |
| The Clone Saga | Surveil 3 fills the yard; II copies a creature spell. | Surveil 3 triggers Matoya and Proft. |
| Thought Scour | Target yourself: mill two, draw one. | Cut at draft for Theorix Charm; target them: mill two, and the draw mills two more. |
| Consider | Surveil 1 + draw. | Surveil triggers Matoya: two draws for 1 mana. |
| Vraska Joins Up | Deathtouch counters; draw when a legend deals combat damage — the Elves do attack. | Rarely attacks. |

**In one list only (10).**
| Card | Thranduil (75-historic-brawl) | Glarb (96) |
|---|---|---|
| Ashiok, Sculptor of Fears | +2 draws and mills BOTH players two — your two feed Thranduil; −5 reanimates from any yard. **Good add here too.** | *in the list* |
| Doctor Doom, Unrivaled | `{T}: draw a card` on a 4-mana lifelink body — fine; non-Elf. | *in the list* |
| Jace, Memory Adept | Its 0 "Target player mills ten cards" can target YOU — ten cards of Elves for Thranduil. **Good add here too.** | *in the list* |
| Jace, the Perfected Mind | −X mills yourself 3X — self-mill on demand; `{2}{U}{U/P}`. | *in the list* |
| Elrond, Moon-Reader | *in the list* | "Whenever you activate an ability of a creature, draw a card" (once a turn) — Glarb's own surveil tap triggers it, so every turn is a draw that mills two. **Good add here too.** |
| Garruk, Veiled Butcher | *in the list* | Interaction (+2 shrink, −2 edict) and −3 card advantage; the deck's interaction is already 16. |
| Leovold, Emissary of Trest | *in the list* | "Each opponent can't draw more than one card each turn" switches off Dictate of Kruphix and Seizan's extra draws for them — it fights this deck's mill. |
| Maralen, Fae Ascendant | *in the list* | Exiles two of their library per Elf or Faerie entering — this deck has almost none. |
| Vraska, Betrayal's Sting | *in the list* | 0: draw (mills two) and proliferate; −2 neutralises a creature. A fine add; 6 mana. |
| Vraska, Golgari Queen | *in the list* | +2 needs a permanent to sacrifice; −3 kills mana value 3 or less. Fine. |
