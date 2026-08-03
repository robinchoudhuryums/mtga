# Deck 54 / 54a — pile-dump re-analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete this file once the swaps land and the findings are folded
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
   clause). A payoff reading *mana value* is turned ON at maximum — **Thor, God of Thunder**
   deals damage equal to the spell's MV, so a `{1}`-flashbacked Improvisation Capstone (MV 7)
   deals 7. Check which word the card uses before grading it.

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

### Batch 3 — pending
### Batch 4 — pending
### Batch 5 — pending
### Batch 6 (18 cards) — pending
