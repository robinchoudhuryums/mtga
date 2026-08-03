# Deck 54 / 54a — pile-dump re-analysis (TEMPORARY working doc)

**Status: ALL SIX BATCHES READ.** Next step is the final ranking + swap application. Delete this file once the swaps land and the findings are folded
into the two deck files' `#: notes:` blocks. It is a scratchpad, not a source of truth —
`decks/54-grand-lotus/deck.txt` and `54a-encore.txt` are.

**What this is.** The 212-line concept pile that produced deck 54 is being re-read in
batches of 30 against a decision framework that did not exist the first time. The first
pass graded cards by hard-cast rate; the framework below says that is the wrong number for
these two decks specifically. This doc carries the framework, the standing error list, and
the running verdicts so that batch N+1 does not repeat batch N's mistakes.

**Source list:** `/tmp/.../scratchpad/pile54-remaining.txt` (168 cards after removing the
44 already in 54 or 54a). Regenerate from the pile if lost.

---

## 1. The decision framework

The engine card in both decks lets you cast spells from the graveyard. **What matters is
what the recast COSTS relative to the card's printed cost**, and the enablers split three
ways. This is the whole reason the first pass was wrong.

**Class A — COST-INDEPENDENT.** The recast price does not scale with the card's cost.
  - Iroh, Grand Lotus: **Lessons flashback flat `{1}`** (deck 54's founding insight)
  - Archmage's Newt **saddled**: flashback `{0}`
  - Daring Waverider: free, capped at **MV ≤ 4**
  - The Dawning Archaic: free, on attack
  - Songcrafter Mage: harmonize minus a tapped creature's **power**
  - Reenact the Crime: copy + cast free
  → **Expensive is strictly better. Monotonically.**

**Class B — FIXED DISCOUNT.**
  - Melek, Reforged Researcher: **`{3}` off** the first instant/sorcery each turn
  - Doc Aurlock: `{2}` off every graveyard/exile cast
  - Norman Osborn (back face): `{2}` off graveyard casts
  → The discount FLATTENS the cost curve, it does not invert it. A `{R}` spell recast
    costs `{R}`; a `{3}{R}` recast costs `{1}{R}` — still two more mana. So this class
    implies a **sweet spot at MV ≈ total discount + 1–2**, not "more is better".
    Melek + Doc Aurlock stacked = `{5}` off → MV 5–6 is nearly free.

**Class C — MANA-COST-EQUAL.** Iroh on non-Lessons, Flashback, Slickshot Lockpicker,
Sphinx of Forgotten Lore, Norman's Goblin Formula mayhem.
  → No discount to under-utilise. **The thesis is false here** — expensive stays expensive.

### Three rules that fall out of it

1. **`{X}` SPELLS ARE ANTI-SYNERGISTIC WITH CLASS A.** Casting a spell "without paying its
   mana cost" sets **X = 0**. Free-cast granters turn an `{X}` spell into 0 damage / MV 0.
   `{X}` spells want **Class C**, the class we otherwise deprioritise.
   *Exception:* a card that is BEST at X=0 inverts this — **Fractalize** sets a creature's
   base P/T to X+1, so a free cast makes their bomb a 1/1.
2. **DISCOUNTS REDUCE GENERIC MANA, NOT COLOURED PIPS.** A card whose cost is mostly pips
   cannot be discounted meaningfully. Nature's Rhythm's Harmonize is `{X}{G}{G}{G}{G}` and
   no enabler here touches those four green pips. Only a **flat-cost replacement** (Iroh's
   `{1}` on a Lesson) beats pips.
3. **"MANA SPENT" vs "MANA VALUE" DECIDES CARDS.** A payoff reading *mana spent* is turned
   OFF by these decks (Thunderdrum Soloist's upgrade, Increment, The Emperor's counter
   clause, Muse Seeker's no-discard rider). A payoff reading *mana value* is turned ON at
   maximum — **Thor, God of Thunder** deals damage equal to the spell's MV, so a
   `{1}`-flashbacked Improvisation Capstone (MV 7) deals 7. Check which word the card uses.
   **3b — THE POSITIVE HALF, found in batch 5.** A whole family reads *"whenever you cast a
   spell with **mana value** 4 or greater"* — Tanufel Rimespeaker, Enraged Flamecaster,
   Spider Manifestation, Equilibrium Adept, Kulrath Mystic, Galvanic Giant. These are the
   mana-spent trap **inverted**: they fire on a `{1}` recast of an expensive card, so the
   thesis turns them ON rather than off. When a card gates on a number, read whether that
   number is the printed cost or the mana leaving your pool — it decides the card.
4. **IN A SELF-MILLING DECK, "PLAY LANDS FROM YOUR GRAVEYARD" IS NOT RAMP — IT RECOVERS A
   COST THE ENGINE IMPOSES.** Milling is not free. 54a is 25 lands / 60, so roughly **42% of
   every mill is a land**, and those are dead cards: Glacierwood Siege alone bins ~4 per
   spell cast. A card that plays lands out of the graveyard converts the engine's own
   downside into land drops — and it does so **without depending on drawing them**, which
   matters because 54a's turn-4 land-drop consistency is only 67.5%. Grading these as "ramp
   in a deck that isn't ramping" is the wrong frame and cost three cards a fair read
   (user pushback, 2026-08).
   *Counter-caution:* each landfall slot is a slot NOT spent on a cast-from-graveyard
   payoff, and that layer is already the deck's #1 graded weakness at 4–5 cards. Recovery
   is real value; a full landfall sub-theme is a different deck.

### Per-deck differences

- **Deck 54** — Iroh's flat `{1}` applies to **LESSONS ONLY**. So 54 wants *expensive
  Lessons*; a non-Lesson there is Class C plus Doc Aurlock's `{2}`. Only **one** card in
  the 37-card shortlist was a Lesson (Shared Roots), which is why 54's plan is thin.
- **Deck 54a** — sweet spot **MV 3–5**. The `MV ≤ 4` cap is Daring Waverider's alone, i.e.
  one enabler of ten; treat it as a **tiebreaker, not a filter** (user decision 2026-08).
  Heavy hitters discounted by Melek/Songcrafter/Doc Aurlock stay in scope.
- **Both** — Treasures and any-colour sources ARE a payoff: the manabase is the #1 graded
  weakness of both decks (54: U10/R9/G12; 54a: U14/R14/G10).

### Live needs, by deck

| | deck 54 | deck 54a |
|---|---|---|
| tier / floor | B / A | B / A |
| weakness 1 | manabase | payoff layer is 4–5 cards |
| weakness 2 | ONE-card engine (Iroh only) | protection 1, on a creature engine |
| weakness 3 | 8 counter enablers, **no payoff** | — |
| other | Lessons fell 21→17; 2 payoffs SCALE with the count | interaction 10 but only **2 instant-speed** |

---

## 2. Standing error list — do not repeat these

Every one of these was made in this analysis and caught late.

1. **Grading a card by the ability that is BROKEN instead of the ability that PAYS.**
   Cost me Topiary Lecturer, Berta, Loki Laufeyson and The Emperor of Palamecia in one
   pass — all dismissed on their Increment/counter clause while their mana or copy ability
   was unconditional.
2. **Not counting the deck property a card depends on before dismissing it** (G-61). State
   the count, then decide. Iron Fist has 3 targeting enablers today and ~6 with the
   protection package — that number, not the card, decides him.
3. **Reading a trigger's cadence wrong.** Firebender Ascension was called "slow" on the
   assumption of one quest counter per turn; it is one per *attacking creature per combat*,
   and 54a fields six attack-trigger creatures.
4. **Identity vs castability** (G-58). Norman Osborn was rejected for "needing a fourth
   colour" when the black is on a TRANSFORM ability, not the `{1}{U}` cast cost.
   `preflight` reads it as "+1 hybrid stray, ok" and `#: colors:` stays GUR.
5. **Asserting what a card's text does without re-reading it.** Deck 54's header claimed
   "Accumulate Wisdom bins two of three"; it bottoms them. **No gate catches this** —
   `rationale_staleness` checks card PRESENCE and quoted FIGURES, never whether a claim
   about a card's text is true.
6. **Grading the printed cost of a Room/split card** (G-02). Greenhouse // Rickety Gazebo
   prints MV 7 and is a `{2}{G}` three-drop.

---

## 3. Cross-batch observations

- **An ATTACK sub-theme is emerging that 54a was not built for.** Sphinx of Forgotten Lore,
  The Dawning Archaic, Archmage's Newt, Norman Osborn, Firebender Ascension, Iron Fist and
  The Lord Master of Hell all pay off on attacking — but `shape` measures 54a as **TALL,
  wide 1, 2 evasive**. Either commit to attacking (evasion/protection) or stop adding cards
  that need it. **Decide this before the final ranking.**
- **The candidate list already exceeds what either deck can absorb.** The end state is a
  RANKING, not a collection. Every add needs a cut, and both decks are exactly 60.
- **Thor, God of Thunder → `#: protect:` in both decks** (user decision 2026-08), to be
  written at the moment he is added, not before — a protect entry naming an absent card is
  a claim the file cannot support (see error 5).
- **A MILL → LAND-RECOVERY → LANDFALL LOOP is available in 54a and is coherent** (rule 4):
  Glacierwood Siege mills → Mole Man / Icetill Explorer play the milled lands → landfall
  fires Bristly Bill's counter, Mole Man's Moloid, Claim the Kingdom's counter → more board,
  more counters, and Icetill mills again on the way. It fixes THREE measured weaknesses at
  once (land-drop consistency 67.5%, wide score 1, only 3 counter sources).
  **The cost is slots**, and they come out of the 4–5 card payoff layer. Decide how many
  landfall cards 54a takes at the final ranking — the answer is probably 2–3, not a theme.

---

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out

### Batch 1 (30 cards)

| Card | 54 | 54a | Note |
|---|---|---|---|
| Thor, God of Thunder `{3}{R}{R}` own | ★★★ | ★★★ | Damage = spell's **MANA VALUE**. Capstone at MV 7 → 7 damage for `{1}`. The per-spell amplifier the pile was missing. |
| Case of the Ransacked Lab `{2}{U}` | — | ★★ | `{1}` off all instants/sorceries; solved (4 spells/turn) = draw per spell. Hits 54a's card-advantage 3. |
| High Fae Trickster `{3}{U}` own | — | ★★ | Cast ALL spells as though they had flash. Fixes the 2-instant/8-sorcery profile. |
| Electro, Assaulting Battery `{1}{R}{R}` own | — | ★★ | `{R}` per instant/sorcery cast + mana doesn't empty. Makes the recast chain self-funding. |
| Valley Floodcaller `{2}{U}` | — | ★ | Flash on noncreature spells, 1 cheaper than High Fae; untaps Otters (Daring Waverider is one). |
| The Last Agni Kai `{1}{R}` own | — | ★ | Instant fight; excess damage → `{R}` that persists. Removal keyed to POWER. |
| Fractalize `{X}{U}` | — | ★ | The `{X}` card that WANTS a free cast: X=0 makes their bomb a 1/1. |
| Return the Favor `{R}{R}` own | — | ★ | Copies an activated OR triggered ability — Sphinx's grant, Archaic's free cast. |
| Firebender Ascension `{1}{R}` own | — | ◇★ | **Revised up.** One quest counter per attacking creature per combat; at 4+, copies EVERY subsequent trigger. Gated on attacking. |
| Iron Fist, Living Weapon `{2}{R}` own | ◇ | ◇★ | **Revised up.** Payoff, not amplifier. 3 enablers today → ~6 with the protection package. Overprotect on Iron Fist = 6/6 hexproof that taps for 6. |
| Jeong Jeong, the Deserter `{2}{R}` own | ◇ | — | Exhaust: copy your next **Lesson**. Deck 54 only. |
| Springleaf Drum / Barrels of Blasting Jelly | ◇ | ◇ | 1-mana any-colour fixing. Drum competes for taps with Songcrafter/Topiary. |
| Coruscation Mage `{1}{R}` own | — | ◇ | 1 damage/opponent per noncreature spell. Per-spell clock, and an Otter. |
| Terrapact Intimidator / Confounding Riddle / Avatar Destiny | — | ◇ | |
| Loot, Exuberant Explorer `{2}{G}` own | △ | △ | Can cheat Iroh in, but `{4}{G}{G}` per activation. Rank below Ember Island Production. |
| Uthros Psionicist `{2}{U}` | △ | △ | Not an enabler — a discount, and `{2}` off ONE spell/turn. Loses to Doc Aurlock. Only argument: works from HAND (the weak phase). Abstract Paintmage is the better version. |
| Fated Firepower | ✗ | ✗ | `{X}` **and** `{R}{R}{R}` — fails both rule 1 and rule 2. |
| Photon Blast Barrage | ✗ | ✗ | Needs a per-damage amplifier; Thor is per-**spell** and copies aren't cast. |
| Thunderdrum Soloist | ✗ | ✗ | Upgrade clause reads "five or more mana **spent**". Rule 3. |
| Hell to Pay / Rime Chill / Kavaron / Iridescent Tiger (off-colour) | ✗ | ✗ | |
| Wingblade Disciple / Reverberating Summons / Bulk Up / Fire Nation Palace | ✗ | ✗ | Below rate. |

### Batch 2 (30 cards)

| Card | 54 | 54a | Note |
|---|---|---|---|
| Melek, Reforged Researcher `{3}{U}{R}` own | ★★ | ★★★ | **`{3}` off** the first instant/sorcery each turn — the biggest Class B discount in these colours; stacks with Doc Aurlock to `{5}`. P/T = 2× the yard, and **Songcrafter taps him to reduce a harmonize by his power**. Strongest interaction found so far. |
| Bloom Tender `{1}{G}` own | ★★★ | ★★★ | Vivid: three mana of the right colours off a two-drop. Best manabase card in the pool. K-01 unindexed. |
| Great Divide Guide `{1}{G}` own | ★★★ | ★★★ | Every land **and Ally** taps for any colour. Greenhouse for one less, on a body — and Iroh, Gran-Gran, Hermitic Herbalist are all Allies. |
| Abstract Paintmage `{U}{U/R}{R}` | — | ★★ | Two free mana every turn, restricted to instants/sorceries. The "helps the hard-cast game" argument, done properly. |
| Zimone, Paradox Sculptor `{2}{G}{U}` own | ◇ | ★★ | Free counter on two creatures **every combat** + a doubling activation. 54a has only 3 counter sources. |
| Rapturous Moment `{4}{U}{R}` | — | ★★ | Draw 3, **discard 2**, add `{U}{U}{R}{R}{R}`. Refunds five mana; recast via Iroh it nets negative. |
| Guru Pathik `{2}{G/U}{G/U}` own | ★★ | ◇ | Digs 5 for a **Lesson**, then a counter per Lesson cast. Deck 54 runs 17 Lessons and has 8 counter enablers with no payoff. |
| The Emperor of Palamecia `{U}{R}` own | — | ★★ | **Revised up (user, 2026-08).** Graded on the wrong clause. The mana ability is unconditional; external counters do most of the work to 3 and only ONE 4-mana hard-cast is needed to fire the check; and the back face's Starfall deals damage = **noncreature nonland cards in your graveyard**, i.e. this deck's core resource, every attack. Gated on attacking (see §3). |
| Thousand-Year Storm `{4}{U}{R}` own | — | ★★⚠ | Powerful and on-plan, but it is **deck 25's signature finisher**. Running it collapses 54a toward 25 on `similar`. User call. |
| Esper Origins `{1}{G}` | — | ★ | Surveil 2, and **"if this spell was cast from a graveyard"** it transforms — another cast-from-graveyard payoff, 54a's #1 shortage. |
| Frontier Bivouac | ★ | ★ | True GUR tri-land. Straight upgrade over a Stark Industries. |
| Quandrix, the Proof `{4}{G}{U}` own | — | ★ | Cascade on instants/sorceries, but **"from your hand"** — fights the plan. |
| Tumbleweed Rising `{1}{G}` | — | ★ | X/X off greatest power; **Plot** = a cast from exile = Spider-Verse / Spider-Man 2099 trigger. |
| Speedball, New Warrior `{2}{U/R}` own | — | ◇ | Protection by **misdirection**: their removal aimed at him gets re-targeted. Also an Iron Fist enabler. |
| Growth Curve / Tempest Angler / Teach by Example / The Lion-Turtle / Traumatic Critique / Venus / Roar of Endless Song / Zaffai | — | ◇ | Zaffai's free cast is **hand-only** and seven mana. |
| Leyline of Mutation / Urban Retreat / Flamehold Grappler | ✗ | ✗ | Off-colour. Leyline's alt cost is literally `{W}{U}{B}{R}{G}`. |
| Troyan / Eshki Dragonclaw / Rydia / Grappling Kraken | ✗ | ✗ | On merit. |

### Batch 3 (30 cards)

**THE HEADLINE: three Lessons were cut from deck 54 EARLIER IN THIS SESSION on hard-cast
rate, which is the exact error the framework exists to prevent.** A Lesson is Class A in
deck 54 — Iroh replaces its whole cost with a flat `{1}`, pips included — so its printed
cost is close to irrelevant there. Re-examine all three before the final ranking.

| Card | 54 | 54a | Note |
|---|---|---|---|
| **Toph, Hardheaded Teacher** `{2}{R}{G}` | ★★★ | ★★ | ETB returns an instant/sorcery from the yard to hand (discard = yard fill). Then **every spell earthbends 1** — a land becomes a 0/0 haste creature with a counter, **+1 more if the spell is a Lesson**. That is a counter source per spell AND a BOARD built out of lands, which attacks 54's weakness #3 head-on (`shape`: wide score ZERO). Also a power source for Songcrafter / Iron Fist / The Last Agni Kai. |
| **Elemental Teachings** `{4}{G}` own | ★★ | — | **REVERSAL — I cut this from 54 this session.** It is an Instant **Lesson**, so Iroh casts it for `{1}`: search **four land cards with different names** (NOT basic-restricted — this is the "curated lands" card), opponent bins two, two enter tapped. Two lands, any lands, for `{1}`. I cut it on its `{4}{G}` hard-cast rate. |
| **Planetarium of Wan Shi Tong** `{6}` own M | ★★ | ★★ | `{1}`,`{T}`: Scry 2 — and **whenever you scry or surveil, you may cast the top card of your library FREE**, once a turn. Self-contained: `{1}` per turn for a free spell. Class A, so rule 1 applies (`{X}` spells become X=0). Six mana is the price. |
| **Redirect Lightning** `{R}` own R | ★★ | ◇ | An Instant **Lesson** that changes the target of a spell or ability. Deck 54 casts it from the yard for `{1}` + the additional cost (5 life or `{2}`), **every turn** — repeatable protection on a deck whose protection is 2. |
| **Ashling, Rekindled** `{1}{R}` own R | ◇ | ★★ | Two-drop: loots on entry/transform (yard fill), flips for `{U}`, and the back face adds **two mana of any one colour, spend only on MV 4 or greater** — a restriction the thesis makes nearly free. Flip back and forth for loot + ramp on alternating turns. |
| **Mona Lisa, Science Geek** `{2}{G}` own | ◇ | ★★ | `{T}`: add **X mana of any one colour, X = her power**. Scales directly with the counters layer; a three-drop that becomes a rainbow Sol Ring. |
| **Hydro-Channeler** `{1}{U}` own | ◇ | ★ | `{T}`: `{U}`, or `{1}`,`{T}`: any colour — **restricted to instants and sorceries**, which is what 54a casts. Ramp and fixing on a two-drop. |
| **Lost Days** `{4}{U}` own | ★ | — | **REVERSAL, same shape as Elemental Teachings.** Instant Lesson → `{1}` via Iroh for a tuck plus a Clue. Cut this session on hard-cast rate. |
| **The Legend of Roku** `{2}{R}{R}` own M | ◇ | ★ | Chapter I exiles three and lets you play them — each is a **cast from exile**, i.e. a Spider-Verse / Spider-Man 2099 trigger. Flips into a firebending-4 attacker. |
| **Temur Battlecrier** `{G}{U}{R}` | — | ◇★ | **Revised up from ✗.** `{1}` less per power-4 creature, on **all** spells during your turn including graveyard recasts — a Class B discount that scales with the counters layer. The Berta Increment anti-synergy is real but is one of her three lines. |
| **White Lotus Tile** `{4}` M | ◇ | ◇★ | X mana of one colour, X = most creatures sharing a type. 54a fields ~6 **Humans**. Enters tapped, needs a board. |
| **Vizier of the Menagerie** `{3}{G}` own M | ◇ | ◇ | *"Spend mana of any type to cast creature spells"* + cast creatures off the top. Total fixing, but only for creatures, and these are spell decks. |
| **Energybending** `{2}` own | ◇★ | ◇ | Instant Lesson: all basic land types + draw. `{1}` via Iroh = a turn of perfect fixing plus a card. |
| Conduit Pylons / Hidden Grotto | ◇ | ◇ | ETB **surveil 1** + `{1}`,`{T}` any colour — virtual copies of Surveillance Room (G-46), and the surveil triggers Planetarium. |
| Bender's Waterskin `{3}` own | ◇ | ◇ | Untaps during **each other player's** untap step — mana on their turn, i.e. instant-speed enablement. |
| Bioengineered Future / Weather Maker / Captivating Cave / Baxter Building / Gene Pollinator / Temur Devotee / Firebending Lesson | ◇ | ◇ | |
| **Secret of Bloodbending** | ✗ | ✗ | Framework does not change it: it is a Lesson, but it **exiles itself**, so it is a one-shot, and what `{1}` buys is one declined attack step. Already recorded in 54's `#: notes:`. |
| Grow from the Ashes / Shared Roots | — | — | Shared Roots already ★ for 54 (a Lesson). Grow from the Ashes is not a Lesson and loses to New Horizons. |
| Temur Monument / Potioner's Trove / Uncharted Haven / Daily Bugle Building | ✗ | ✗ | Below rate. |

**New standing error (7): I CUT CARDS FROM DECK 54 ON HARD-CAST RATE WHILE HOLDING THE
FRAMEWORK THAT SAYS NOT TO.** Elemental Teachings and Lost Days were both cut in the
five-swap fixing package. Before any further Lesson leaves deck 54, price it at `{1}`.

**New standing error (8): DISMISSING A CARD BY ITS CATEGORY INSTEAD OF ITS TEXT.** "Landfall
payoffs belong in a landfall deck" swept six cards out in one line, and three of them were
not payoffs at all — they were **recovery** for a cost this deck's own engine imposes
(rule 4). A category label is a hypothesis about a card, not a reading of it.
### Batch 4 (32 cards — heavily landfall, so much of it is deck 30/50a material)

**THE TRAP OF THE BATCH: Taigam, Master Opportunist looks perfect and fights the engine.**
*"Flurry — whenever you cast your second spell each turn, copy it, then **exile** the spell
you cast with four time counters on it… it gains suspend."* A free copy plus a free recast
later reads as a dream 54a card. But the original is **exiled instead of reaching your
graveyard**, so every second spell each turn is removed from the recursion pipeline — and
it shrinks Melek's power, The Lord Master of Hell's Starfall, and Steal the Show's damage,
all of which count cards *in the graveyard*. This is the G-42 mirror: a fine card that
attacks your own engine. **✗ despite the power level.**

| Card | 54 | 54a | Note |
|---|---|---|---|
| **Bristly Bill, Spine Sower** `{1}{G}` own M | ◇ | ★★ | Landfall: a +1/+1 counter **every land drop**, i.e. one guaranteed per turn — the repeatable counter source the utility layer lacks, on a two-drop. `{3}{G}{G}` doubles all counters. Cheaper than Zimone for the same job. |
| **Shang-Chi, Master of Kung Fu** `{1}{G}` own M | ◇ | ★★ | *"You may activate abilities of creatures you control as though those creatures had haste."* Topiary Lecturer, Berta, Mona Lisa, Hydro-Channeler, Loki and Iron Fist all have `{T}` abilities that otherwise idle a turn. Accelerates the whole activated-ability manabase. |
| **Doc Samson, Super Psychiatrist** `{4}{G}` own | ◇ | ★ | Counters arrive **plus one**, on every kind — and `{T}`: X mana of any colour where X is his power. A counters amplifier that is also a mana engine. Five mana. |
| **Claim the Kingdom** `{1}{G}` own | ◇ | ★ | Counter per land drop + an **indestructible counter** at four — counters and protection, the axis 54a sits at 1. |
| **Primeval Bounty** `{5}{G}` own M | ◇ | ★ | **Three** +1/+1 counters per noncreature spell. Enormous for the counters layer; six mana is the price. |
| **Hardbristle Bandit** `{1}{G}` | ◇ | ★ | `{T}`: any colour, and it **untaps whenever you commit a crime** — 54a targets opponents every turn, so it is effectively two rainbow mana per turn from a two-drop. |
| **The Mechanist, Aerial Artisan** `{2}{U}` own | ◇ | ◇★ | A **Clue per noncreature spell** — real card advantage on 54a's weakest axis (3), in a deck casting 3–5 spells a turn. |
| **The Everflowing Well** `{2}{U}` own | ◇ | ◇★ | ETB **mill two, draw two** — yard fill and cards in one, for three mana. |
| **Roxanne, Starfall Savant** `{3}{R}{G}` | — | ★ | Meteorite tokens: 2 damage on entry **and** a rainbow mana source, then doubles artifact-token mana. Removal plus fixing; five mana and wants to attack. |
| **Undercover Skrull** `{1}{G}` own | ◇ | ◇★ | Two-drop rainbow source that becomes a 3/3 all-types once two creature cards are in the yard. |
| **Muse Seeker** `{1}{U}` own | ◇ | ◇ | **RULE 3 CARD — read it carefully.** *"draw a card, then discard unless five or more mana was **spent**"* means a `{1}`-recast deck **always discards**. It is a LOOTER (yard fill), not card advantage. Fine — but not what it looks like. |
| Astrologian's Planisphere / Illvoi Operative / Razzle-Dazzler / Splashy Spellcaster / Kulrath Mystic | — | ◇ | Small spell-count payoffs. Razzle-Dazzler grants itself **unblockable**, which matters if 54a commits to the attack sub-theme. |
| Mole Man / A Realm Reborn / Galvanic Giant / Ojer Pakpatiq / Redshift / Dragonbroods' Relic | — | △ | A Realm Reborn does Great Divide Guide's job for four more mana. Ojer Pakpatiq's rebound is **hand-only and instant-only**. Redshift's mana is restricted to activated abilities. Dragonbroods' Relic adds a WUBRG stray. |
| **Taigam, Master Opportunist** own M | ✗ | ✗⚠ | See above — exiles your second spell each turn out of the graveyard pipeline. |
| **Mole Man, Moloid Master** `{2}{G}` own | — | ★ | **REVISED UP (user, 2026-08) — see rule 4.** Plays lands from the graveyard, which recovers the ~42% of every mill that is a land; and its landfall makes a **1/1 Moloid that mills on attack**, so it also answers the wide-score-1 problem and feeds the yard again. Three on-plan lines on a two-drop. |
| **Icetill Explorer** `{2}{G}{G}` | — | ★ | **REVISED UP.** All three lines are on-plan: an extra land drop, lands from the graveyard (rule 4), and **landfall mills a card** — more fuel. My "ramp in a deck that isn't ramping" read was simply wrong. The honest remaining objection is `{G}{G}` on 10 green sources (~59% on curve, same band as Germination Practicum). |
| **Seedship Agrarian** `{3}{G}` own | — | ◇ | **REVISED UP.** *"Whenever this creature **becomes tapped**"* — and **Songcrafter Mage's harmonize taps a creature to reduce its cost**, so reducing a recast pays you a Lander. Real loop; the Lander is still a slow `{2}`-to-crack basic fetcher. |
| Tannuk / Gladiolus Amicitia / Tifa Lockhart / Dragonback Assault | — | △ | Genuine landfall *payoffs* rather than recovery — they need multiple land drops per turn to be good, which only happens once Icetill/Mole Man are already there. Dragonback Assault's ETB also kills your own Moloids and tokens. Primary home is still **deck 30 / 50a**. |
| Tam, Observant Sequencer | — | — | **Not in the pool under any spelling** — check the name. |

---

## 5. CONSOLIDATED PLAN (live — rewritten after every batch)

Both decks are exactly 60, so **every add needs a cut**. This section is the running
answer, not a wish list; it is re-ranked as batches land.

### Deck 54 — adds

| Tier | Card | Reasoning |
|---|---|---|
| **1** | **Thor, God of Thunder** `{3}{R}{R}` own | Damage = the spell's **mana value**, so a `{1}`-flashbacked Improvisation Capstone (MV 7) deals 7 to any target. Converts the deck's founding insight into a clock. → `#: protect:` on add. |
| **1** | **Toph, Hardheaded Teacher** `{2}{R}{G}` | Every spell earthbends a land into a growing creature, +1 extra on a **Lesson**. Builds the board `shape` measures at **wide score ZERO** (weakness #3) and returns an instant/sorcery from the yard on ETB. |
| **1** | **Great Divide Guide** `{1}{G}` own | Every land **and Ally** taps for any colour — and Iroh, Gran-Gran, Hermitic Herbalist are Allies. Weakness #1, on a two-drop. |
| **1** | **Bloom Tender** `{1}{G}` own | Three mana of the right colours from a two-drop. Weakness #1. |
| **2** | **Elemental Teachings** `{4}{G}` own | **Un-cut it.** A Lesson → `{1}` via Iroh, fetching **four land cards with different names** (not basics). The curated-lands card. |
| **2** | **Shared Roots** `{1}{G}` | A Lesson, so a repeatable `{1}` land drop. Lessons 17 → 18. |
| **2** | **Ember Island Production** `{3}{U}{U}` own | A **non-legendary** copy of Iroh — actual redundancy for weakness #2, which Fierce Empath only *finds*. |
| **2** | **Guru Pathik** `{2}{G/U}{G/U}` own | Digs 5 for a Lesson, then a counter per Lesson cast — feeds the 8 counter enablers that currently have no payoff. |
| **3** | **Inspiring Call** `{2}{G}` | The counters **payoff** (weakness #3) plus team indestructible; protection is 2. |
| **3** | **Redirect Lightning** `{R}` own | A Lesson that redirects, recastable for `{1}` + 5 life **every turn**. Repeatable protection. |
| **3** | **Zimone's Experiment** `{3}{G}` own · **Overprotect** `{1}{G}` · **Lost Days** `{4}{U}` own (un-cut) · **Jeong Jeong** `{2}{R}` own (copies a Lesson) | |

### Deck 54 — cuts, and the constraint that shapes them

**The cut pool is mostly Lessons, and cutting a Lesson costs the two payoffs that SCALE
with the count** (Combustion Technique, Bumi's X). Prefer non-Lesson cuts; note that five
of the tier-1/2 adds are themselves Lessons, so the count holds or rises.

| Cut | Reasoning |
|---|---|
| **Fierce Empath** `{2}{G}` | Narrow tutor (MV 6+ only), Pw 1. Ember Island Production is better engine redundancy. Non-Lesson. |
| **It'll Quench Ya!** `{1}{U}` | The one card actively fighting the plan — a reactive `{2}`-tax counter in a deck that taps out. Lesson, so it costs 1 from the count. |
| **Serpent of the Pass** `{7}` | Seven-drop on a 3.06 curve. Non-Lesson. |
| **Seismic Sense** `{G}` | Cheapest Lesson, lowest impact; `⌁scales w/ lands` so it is graded at its floor — read before cutting. |
| **Formidable Speaker** `{2}{G}` | ⚡cost-as-upside (discard fills the yard) and one of two Iroh finders — **cut last**. |
| **Abandon Attachments** `{1}{U/R}` | ⚡cost-as-upside, low power. Lesson. |
| ⓘ | `cuts` warns deck 54 is **short on early drops (17)** — three of these are MV 1–2. Do not take all of them. |

### Deck 54a — adds

| Tier | Card | Reasoning |
|---|---|---|
| **1** | **Melek, Reforged Researcher** `{3}{U}{R}` own | **`{3}` off** the first instant/sorcery each turn — the largest Class B discount in these colours, stacking with Doc Aurlock to `{5}`. P/T = 2× the yard, and **Songcrafter taps him to reduce a harmonize by his power**, which makes any expensive spell free from the graveyard. |
| **1** | **Thor, God of Thunder** `{3}{R}{R}` own | As above; MV 3–5 recasts become 3–5 damage each, repeatedly. → `#: protect:` on add. |
| **1** | **Bloom Tender** + **Great Divide Guide** `{1}{G}` own | Four mana total closes the manabase weakness (U14/R14/G10). |
| **1** | **Steal the Show** `{2}{R}` | Choose one **or both**: yard fill *and* damage = instants+sorceries in the graveyard. Scaling removal on the exact resource the deck hoards. |
| **2** | **Retrieve the Esper** `{3}{U}` own | *"if this spell was cast from a graveyard, put two +1/+1 counters"* — a **fifth payoff** for the deck's #1 weakness (4 payoffs), and Iroh recasts it at `{3}{U}`, Doc Aurlock at `{1}{U}`. |
| **2** | **Kid Loki** `{U}` own · **Overprotect** `{1}{G}` | Protection 1 → 3. Kid Loki's hexproof needs a counter placed **that turn**, so on the opponent's turn it runs off Agatha's Soul Cauldron's untimed `{T}`. |
| **2** | **Bristly Bill** `{1}{G}` own · **Shang-Chi** `{1}{G}` own | A guaranteed counter per turn, and haste for every `{T}` ability. Both two-drops, both owned. |
| **2** | **Abstract Paintmage** `{U}{U/R}{R}` · **Ashling, Rekindled** `{1}{R}` own | Two free mana per turn for instants/sorceries; loot + ramp restricted to MV 4+, which the thesis makes free. |
| **2** | **The Emperor of Palamecia** `{U}{R}` own | Unconditional mana ability; back face deals damage = noncreature nonland cards in your graveyard, per attack. |
| **3** | **High Fae Trickster** `{3}{U}` own | Cast all spells as though they had flash — fixes the **2 instant / 8 sorcery** profile. |
| **3** | **Electro** `{1}{R}{R}` own · **Rapturous Moment** `{4}{U}{R}` · **Zimone** `{2}{G}{U}` own · **Loading Zone** `{3}{G}` own · **Inspiring Call** · **Case of the Ransacked Lab** `{2}{U}` · **Iron Fist** `{2}{R}` own · **Firebender Ascension** `{1}{R}` own | Iron Fist and Firebender Ascension are **contingent on the attack decision** in §3. |
| **3** | **Frontier Bivouac** (true GUR tri-land) · **Mona Lisa** · **Hydro-Channeler** · **Planetarium** `{6}` own | |
| **2–3** | **Mole Man** `{2}{G}` own · **Icetill Explorer** `{2}{G}{G}` | Rule-4 recovery, not ramp: they convert the ~42% of every mill that is a land back into land drops, and Mole Man's Moloids add bodies to a wide-score-1 deck. **Cap the landfall count at 2–3** — every slot competes with the payoff layer. |
| **⚠** | **Thousand-Year Storm** own | Powerful and on-plan, but it is deck 25's signature card and collapses 54a toward it on `similar`. **User call.** |

### Deck 54a — cuts

| Cut | Reasoning |
|---|---|
| **Duel Tactics** `{R}` | 1 damage. The single card extracting nothing from any enabler class — the thesis's clearest target. |
| **Boomerang Basics** `{U}` | Weakest removal (`cuts` fit 16, Pw 3); bounce is the softest interaction, and MV 1 wastes every discount. |
| **Channeled Dragonfire** `{R}` | 2 damage, and its Harmonize is `{5}{R}{R}` — coloured pips no discount touches (rule 2). |
| **Tome Blast** `{1}{R}` | 2 damage, flashback `{4}{R}`. Same shape, one mana worse. |
| **Accumulate Wisdom** `{1}{U}` | **Not yard fill** — it bottoms what it doesn't take. Pure selection; held only for the Lesson-count gate. |
| **Self-Reflection** `{4}{U}{U}` | Strictly worse than Ember Island Production, whose copy is **not legendary** (so it can copy Iroh). |
| **Abandon Attachments** `{1}{U/R}` | ⚡cost-as-upside, but low power and MV 2. |
| **Glacial Dragonhunt** `{U}{R}` | **Cut LAST** — loot + conditional removal + yard fill in one, with a power-reducible Harmonize. Better than its ranking. |
| **PROTECT** | **Loki Laufeyson, Berta, Germination Practicum** — `cuts` ranks all three near the top because their payoffs are power-scaling activated abilities and unindexed Increment (K-01) that no tag-gated tool can see. **Origin of Metalbending** is 1 of only 4 noncreature answers *and* the deck's other protection source. |

### Batch 5 (30 cards — spell-count payoffs)

**THOR HAS A TWIN.** Ovika reads the same word Thor does and pays in bodies instead of
damage. Together they are the two cards that convert "expensive spells cast for `{1}`" into
a win condition, and both are owned.

| Card | 54 | 54a | Note |
|---|---|---|---|
| **Ovika, Enigma Goliath** `{5}{U}{R}` own R | ★★★ | ★★★ | *"create X 1/1 Phyrexian Goblin tokens, where X is the **mana value** of that spell"*, with haste. Deck 54 flashing back Improvisation Capstone (MV 7) for `{1}` makes **seven hasty bodies**; 54a's MV 3–5 recasts make 3–5 each. Also the answer to 54a's **wide score of 1**, and ward `{3}`+3 life protects it. Seven mana. |
| **Balmor, Battlemage Captain** `{U}{R}` own | — | ★★ | Every instant/sorcery gives the team **+1/+0 and trample**. A two-drop that converts the spell count into damage — this is the card that makes the attack sub-theme (§3) actually work. |
| **Wiccan, Rising Magician** `{4}{U}` own | ◇ | ★★ | Per noncreature spell, **exile another target nonland nontoken permanent, return at end step**. Blinks your own ETB granters (Slickshot Lockpicker, Daring Waverider, Songcrafter Mage) for a re-trigger, or removes a blocker for a turn. Every spell. |
| **Seifer Almasy** `{3}{R}` own R | — | ★★ | *"Whenever Seifer deals combat damage to a player, you may cast target instant or sorcery card with **mana value 3 or less** from your graveyard **without paying its mana cost**."* An eleventh granter, Class A, capped at MV 3. Feeds the attack sub-theme. |
| **Spinerock Tyrant** `{3}{R}{R}` own M | — | ★★ | Copy **every single-target instant/sorcery**, and the copies gain wither so burn becomes permanent −1/−1 counters. No G-42 risk — those land on their creatures, not on your +1/+1 layer. |
| **Ral, Crackling Wit** `{2}{U}{R}` M | — | ★★ | A loyalty counter per noncreature spell, so it ults fast here. `−3` draws three and discards two — card advantage **and** yard fill on 54a's weakest axis, on a permanent that dodges creature removal. |
| **Emeritus of Conflict // Lightning Bolt** `{1}{R}` own M | ◇ | ★★ | Split card — grade the face you cast (G-43). As Lightning Bolt it is premium `{R}` removal; as the creature it becomes **prepared** on your third spell each turn for a free copy of its own Bolt. "Prepared" is unindexed (K-01). |
| **Guttersnipe** `{2}{R}` | — | ★ | 2 damage to each opponent per instant/sorcery — strictly better than Coruscation Mage's 1. |
| **Tanufel Rimespeaker** `{3}{U}` | ◇ | ★ | **Rule 3b:** draw a card per **MV 4+** spell. The thesis turns it on. Card advantage on the weak axis. |
| **Spider Manifestation** `{1}{R/G}` own | ◇ | ★ | **Rule 3b:** `{T}` for `{R}`/`{G}`, and it **untaps on every MV 4+ spell** — a mana source that goes several times a turn. Hybrid, so trivially castable. |
| **Sword of Wealth and Power** `{3}` M | — | ★ | **Protection from instants and sorceries** (an axis at 1), plus a Treasure and a copy of your next spell on combat damage. Needs a creature to connect. |
| **Great Hall of the Biblioplex** | ◇ | ★ | Taps for any colour at 1 life, **restricted to instants and sorceries** — a free restriction here. Better than a colourless utility land. |
| Enraged Flamecaster / Equilibrium Adept / Rodeo Pyromancers / Cool but Rude / Prismatic Undercurrents / Boar-q-pine / Devoted Duelist | — | ◇ | Rodeo Pyromancers is a ritual every turn; Prismatic Undercurrents fetches basics **to hand** (slow) but adds a land drop. |
| **Shantotto, Tactician Magician** own | ✗ | ✗ | **Rule 3.** Both the pump and the draw read *mana **spent***; a `{1}`-recast deck triggers neither. |
| **Aberrant Manawurm** · **Prompto Argentum** · **Colorstorm Stallion** (token half) | ✗ | ✗ | Same — all gate on mana spent. |
| Wildgrowth Archaic / Quilled Greatwurm / Jackal | — | △ | Creature-spell payoffs; these are spell decks. |
| **Fire Lord Azula** own | ✗ | ✗ | Confirmed: must be **attacking** when you cast, and needs black **in the cast cost** — the Cauldron fixes activated abilities only. |
| **Sokka, Tenacious Tactician** own · **Avatar Aang** own · **Ramos** | ✗ | ✗ | Off-colour. Aang's back face (*"spells cost `{W}{U}{B}{R}{G}` less"*) is spectacular and unreachable — the front costs `{R}{G}{W}{U}`. |

### Batch 6 (18 cards — six already graded in earlier batches)

**THE ANTI-CARD OF THE BATCH: Wisdom of Ages EMPTIES the resource.** *"Return **all** instant
and sorcery cards from your graveyard to your hand."* In a deck whose discounts (Melek `{3}`,
Doc Aurlock `{2}`) apply **only to graveyard and exile casts**, moving ten cards to hand
means paying full price for all of them — and it collapses Melek's power, The Lord Master
of Hell's Starfall and Steal the Show's damage in the same turn. Same shape as Festival of
Embers. ✗ despite looking like mass card advantage.

| Card | 54 | 54a | Note |
|---|---|---|---|
| **Omenpath Journey** `{3}{G}` M | ★★ | ★★ | Search **five land cards with different names** — not basics — exile them, then drop one onto the battlefield at every end step. The curated-lands thesis fully realised, and a five-turn engine against weakness #1. Random selection is the cost. |
| **Earth's Mightiest Heroes** `{4}{G}{G}` own M | ◇ | ★★ | Reveal eight, put creatures onto the battlefield, **rest into your graveyard** — mass yard fill AND cheating the engine into play, both on-plan. Teamwork 5 taps power-4 creatures, which the counters layer supplies. |
| **Multiversal Incursion** `{5}{U}{U}` own M | ◇ | ★★ | A copy of every nontoken creature, ***except it isn't legendary*** — so it duplicates Iroh, Melek and Norman, which the legend rule would otherwise forbid. MV 7; Melek + Doc Aurlock take a recast to `{U}{U}`. |
| **Dragonclaw Strike** `{2/G}{2/U}{2/R}` own | — | ◇★ | Double power, then fight — removal that scales with the counters layer, and the `{2/X}` hybrids make it castable off six generic in the worst case. |
| **The Earth King** `{3}{G}` own R | ◇ | ◇★ | A 4/4 body plus land ramp per power-4 attacker. **Contingent on the attack decision (§3).** |
| **Full Throttle** `{4}{R}{R}` | — | ◇ | Two extra combat phases. Pure attack payoff — same contingency. |
| **Raphael's Technique** `{4}{R}{R}` | — | ◇ | Discard your hand, draw seven: real yard fill and refuel, but **symmetric** — it refills the opponent too. |
| Worlds Within Worlds / Celestial Reunion / Sagu Wildling / Mammoth Bellow | — | △ | Celestial Reunion is an `{X}` spell (**rule 1**). Worlds Within Worlds wipes your own engine as hard as theirs. |
| **Wisdom of Ages** own | ✗ | ✗⚠ | See above — empties the graveyard the deck runs on. |
| **Narset's Rebuke** | ✗ | ✗ | Off-colour (needs W). |
| Nature's Rhythm · Ember Island Production · Mirrorform · Artistic Process · Sozin's Comet | — | — | Graded in earlier batches; see there. |

---

## 5b. CONSOLIDATED PLAN — DECK 54b (Grand Lotus — Comet)

**54b inverts the framework, and that is the headline of its whole plan.** Decks 54 and 54a
DISCOUNT spells, so every payoff reading *"if N or more mana was **spent**"* is dead in them
(rule 3). **54b does the opposite — it manufactures surplus red mana in combat and spends
all of it.** Casting Fated Firepower for X=4 spends seven. Flashing a spell back at its
mana cost per Class C spends full price. So the entire mana-spent family, rejected across
batches 1–5 for the other two decks, is **LIVE here and only here.**

Live needs, measured 2026-08: interaction 6 · **card advantage 3** · **protection 1** ·
avg MV 3.23 · early drops 15 · WIDE 6, 23 creatures, 9 evasive · 8 instants, 1 sorcery.

### Adds

| Tier | Card | Reasoning |
|---|---|---|
| **1** | **Full Throttle** `{4}{R}{R}` | *"After this main phase, there are two additional combat phases. At the beginning of each combat this turn, untap all creatures that attacked."* **THREE combats = firebending mana ×3**, and every attack trigger fires three times — Sphinx, The Dawning Archaic, Archmage's Newt, Norman, and three quest counters onto Firebender Ascension. No other deck on the roster converts this card so directly. |
| **1** | **Thunderdrum Soloist** `{1}{R}` own | **The reversal card.** Rejected in batch 1 on rule 3; here the upgrade clause fires. 1 damage per instant/sorcery, **3 if five or more mana was spent** — which is the normal case in a combat-mana deck. Reach, so it blocks while the rest attacks. |
| **1** | **Prompto Argentum** `{1}{R}` | Haste, and a **Treasure per noncreature spell cast with 4+ mana**. Treasures are the fix for the deck's real structural leak: they turn combat mana into **permanent** mana, and they are **rainbow**, which is Azula's black. Two graded problems in one two-drop. |
| **1** | **Sword of Wealth and Power** `{3}` M | **Protection from instants and sorceries** on an axis sitting at **1**, plus a Treasure and a **copy of your next instant/sorcery** on combat damage. Three of this deck's needs on one colourless card. |
| **2** | **Shantotto, Tactician Magician** `{1}{U}{R}` own | Second reversal. `+X/+0` where X is mana spent, and **draw a card when X ≥ 4** — card advantage (axis 3) on a body that grows huge off a Fated Firepower turn. |
| **2** | **Muse Seeker** `{1}{U}` own | Third reversal, and it was cut from this very deck for Azula. *"Draw a card, then discard **unless five or more mana was spent**"* — in 54 and 54a that is always a loot; **here it is often a true draw.** |
| **2** | **Roxanne, Starfall Savant** `{3}{R}{G}` | Attack trigger that makes a **Meteorite: 2 damage on entry AND a rainbow mana source**, then doubles all artifact-token mana. Removal + fixing + attack payoff, and it compounds with Prompto's Treasures. |
| **3** | **Fire Nation Attacks** `{4}{R}` | An **instant** that makes two firebending-1 bodies — a combat-mana sink that pays for itself in future combat mana. Iroh grants flashback at its `{4}{R}` mana cost, which beats its printed `{8}{R}`. |
| **3** | **The Earth King** `{3}{G}` own · **Colorstorm Stallion** `{1}{U}{R}` own | A 4/4 plus land ramp per power-4 attacker; and a hasty warded body that **copies itself when 5+ mana is spent**. |
| **3** | **Coruscation Mage** `{1}{R}` own · **Devoted Duelist** `{1}{R}` | Cheap per-spell drains that also lower the curve — the deck is short on early drops (15). |

### Cuts

| Cut | Reasoning |
|---|---|
| **Ran and Shaw** `{3}{R}{R}` | Its ETB needs *three or more Dragon and/or Lesson cards in your graveyard* — 54b runs **four Lessons and one Dragon**, so the copy almost never happens. Five mana for a firebending-2 flier is the worst rate in the package. |
| **Wisecrack** `{2}{R}` | Narrowest removal in the list; `cuts` fit 5, Pw 2. |
| **Combustion Technique** `{1}{R}` | Damage is *2 + Lessons in your graveyard*, and this deck has **four Lessons**, not seventeen. It is a deck-54 card that came along for the ride — `targets` already flags it `⚠ thin`. |
| **Firebending Lesson** `{R}` | 2 damage for `{R}`; the kicker costs `{4}` and buys 3 more. Keep only if the Lesson count matters for Combustion Technique, and it will not if that goes. |
| **Bulk Up** `{1}{R}` | A pure combat trick with no engine role. |
| **Guttersnipe** `{2}{R}` own | 2 damage per spell is real, but Thunderdrum Soloist does the same job with a **3-damage** upside and reach. Cut only if Soloist lands. |
| **PROTECT — do not cut on the ranking's word** | **Sozin's Comet** is ranked WEAKEST (fit 4) and grants **firebending 5 to every creature** — with eight attackers that is forty red mana, the deck's single biggest turn; the fit score cannot see it. **The Last Agni Kai** is one of only TWO cards that stop red mana emptying. **Return the Favor** copies a **triggered ability**, i.e. Sphinx's or The Dawning Archaic's. **Bloom Tender** is fixing on a four-colour manabase. |

**Sequencing note.** Adds 1–4 do not touch the recursion spine, so they are safe first. The
`#: notes:` abandon test still governs: if the six graveyard granters ever fall below four,
this has become deck 14 in the wrong colours.

---

## 6. Was a "rule 3b" variant deck viable? — ASKED AND ANSWERED (2026-08)

**Counted first, per G-59.** A pool sweep of the effect shape returns **19 Standard payoffs
gating on a spell's MANA VALUE, 16 of them GUR-castable.** By the tribe benchmark that is a
buildable number (Dragon 20 → built as deck 49; Dinosaur 11; Vampire 3).

**Verdict: enough cards, but not a deck. Three reasons.**

1. **The payoff QUALITY is uniformly low.** Reading all 16: exactly three do anything but
   combat stats — Tanufel Rimespeaker (draw 1), Superior Foes of Spider-Man (impulse 1),
   Flaring Cinder (loot 1). The other thirteen are small creatures that grow or ping for
   1–2: Angry Rabble, Lurking Lizards, Kulrath Mystic, Stormkeld Prowler, Skybeast Tracker,
   Enraged Flamecaster, Rhino, Tempest Hart, Spider Manifestation, Galvanic Giant. **There
   is no bomb and no engine in the family.** Compare what 54a's payoff layer does — copy a
   spell (Spider-Verse), MV in damage (Thor), MV in bodies (Ovika).
2. **3b payoffs do not need a recursion engine.** They fire on any MV 4+ cast, hard-cast
   included, so the natural 3b shell is **ramp into big spells** — which is deck 30's shell,
   in deck 30's colours, and deck 30 is tier A and fully owned.
3. **The marriage beats the divorce.** 3b + recursion means casting an MV 6–7 spell for
   `{1}` *and* collecting the trigger — a discount no other deck gets. That argues for
   putting the best two or three 3b cards **inside** 54/54a, not building around the rest.

**Falsifiable counterfactual:** if two or three members of this family were genuinely large
— something that ends a game off an MV 4+ trigger — it would be a deck. The ceiling today
is "draw a card".

**Action:** take **Spider Manifestation** and **Tanufel Rimespeaker** into 54a as
role-players. Note **Disdainful Stroke** is the family's anti-card and sits in the same
colours, so a dedicated 3b deck would telegraph into it.
