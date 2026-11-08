# G'raha Tia pile — analysis (TEMPORARY working doc)

**Status: DRAFTED as deck 98 (Throw Wide the Gates), 2026-11-08; owner deciding the Aura lean.** Builder project `builds/graha`, board https://claude.ai/artifact/XakxYe3Et9JHgUZTao4QjJ. Delete once the deck is drafted and the findings are folded into its
`#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Source list:** the owner's 230-card pile (2026-11-08), saved in the session scratchpad as
`graha/remaining.txt`. All 230 resolve in the pool; 46 already sit in another deck, which does not
matter here (the collection is shared — CLAUDE.md, "Decks share the collection").

**Target:** a NEW Historic Brawl deck (100 cards, singleton, 25 life, free first mulligan),
commander **G'raha Tia, Scion Reborn** {W}{U}{B} — Esper. No deck file yet, so the Builder project
starts after the draft (the Rocco pile did the same: board created with deck 97).

## 1. The decision framework

The commander's text, which every rule below reads from:

> Lifelink. **Throw Wide the Gates** — Whenever you cast a noncreature spell, you may pay X life,
> where X is that spell's mana value. If you do, create a 1/1 colorless Hero creature token and put
> X +1/+1 counters on it. Do this only once each turn.

1. **A noncreature spell is worth a body.** The first noncreature spell each turn becomes an
   (X+1)/(X+1) Hero token for X life. So a noncreature spell's value here is its own effect PLUS a
   creature. Grade noncreature spells up; grade a creature on what it does without that bonus.
2. **"Once each turn" means EACH turn, the opponent's included.** An instant, a flash enchantment or
   an activated-at-instant-speed planeswalker cast on the opponent's turn makes a second token per
   round. Instant-speed noncreature spells are worth more than sorcery-speed ones of equal power.
3. **The number that decides it is noncreature-spell DENSITY, not raw count of good cards.** To hit
   the trigger most turns the deck wants roughly 30–38 noncreature spells (about one per turn drawn
   plus what is in hand). Track the running count in §3; a creature-heavy list starves the engine.
4. **Mana value is BOTH the payoff and the cost.** X counters on the token, X life paid. MV 2–4 is the
   sweet spot (a 3/3–5/5 for 2–4 life); MV 5–6 is a big body at real life cost; MV 0–1 makes a 1/1–2/2.
   The payment is OPTIONAL ("you may"), so an expensive spell never forces it — but the deck's life
   budget is the constraint, which makes rule 5 structural, not a theme.
5. **Life is a resource the deck spends every turn, so lifegain is FUEL, not a subtheme.** G'raha has
   lifelink; lifelink creatures, drain ("each opponent loses N, you gain N") and gain-on-cast effects
   all refill the budget. Cards that PAY life (or care about life lost) are synergy, not a drawback.
   25 starting life in Brawl.
6. **Every token is a Hero AND carries +1/+1 counters.** So three payoff families are live: Hero
   payoffs (the Marvel cards), +1/+1-counter payoffs (proliferate, "creature with a counter", counter
   doublers), and token/go-wide payoffs. A card scaling with one of those is graded on the density the
   commander supplies, not the density of the 99 alone.
7. **Esper castability from the PRINTED cost** (G-58). Identity outside W/U/B is illegal in Brawl.
   Mono-colour and two-colour costs are easy; three-colour costs are the manabase's problem.
8. **What is structurally invisible to the tools:** the commander's token per noncreature spell (no
   model counts tokens as bodies — G-86), the life-payment economy (no axis), and the second token on
   the opponent's turn. Count these by hand.
9. **Interaction is still required** (1v1, a recastable commander on the other side): ≥12 interaction
   at 100 cards for the A floor, with instant-speed answers preferred (rule 2 doubles their value).

## 2. Standing error list

Misreadings the four batches surfaced, so a later pass does not repeat them:

1. **A God or Enchantment Creature is a CREATURE spell.** Ephara, Athreos, Summon: Primal Odin and
   Heliod's front face give no trigger when cast; "isn't a creature" applies only on the battlefield.
2. **An Adventure half is a noncreature spell.** Swift Spiral (Twining Twins), Throw a Line (Ondu
   Knotmaster) and Giant Secrets (Stormkeld Curator) trigger G'raha from a creature card.
3. **G'raha reads the MV on the STACK, and card-mana.csv books split cards combined and X at 0** (G-02,
   G-60). Consecrate is 2, Consume 4; Revival 2, Revenge 6; Invasion of New Phyrexia X+2; Sphinx's
   Revelation X+3; Dance of the Manse X+2. Size the token per cast; never filter on the stored figure.
4. **Cost reduction is not MV reduction.** Danitha Capashen, Transcendent Envoy, affinity, Killian, Head
   of the Class and Inquisitive Glimmer cut what you pay; the token still gets the printed MV.
5. **Activations are not casts.** Class levels, power-ups, Doom Foretold, graveyard-return abilities
   and rebound-in-upkeep do not add triggers (rebound actually spends the turn's one trigger).
6. **Blink and exile lose tokens.** Brokers' Safeguard, Hallowed Respite, Photon and Don & Leo exile a
   creature and return it: a Hero token is gone for good, a real creature loses its counters (G-42).
7. **"Nontoken" clauses skip the whole engine.** Isilu's persist, Swift Spiral's blink and Doom
   Foretold's sacrifice cannot touch the commander's tokens.
8. **Creature-spell payoffs are off-plan** (Ace Flockbringer, Abigale Poet Laureate, Champions of Tyr,
   Lulu): the deck deliberately casts fewer creatures.
9. **A 0-MV cast makes a token with no counters**, so "modified" / "creature with counters" payoffs
   only count tokens from MV 1+ spells.
11. **Tool notes from the draft.** `stats` scores no role for Petrify, Nahiri's Binding, Skyblade's Boon, Angelic Destiny and Leyline of Anticipation (interaction 22 "+5 unclassified") — a G-67 hole for removal Auras to fix in a batch. The Builder lists Heliod twice: the deck line stores the front name and the pile the full DFC name, and the deck-only list does not alias them.
10. **Kaya's −2 token doubling:** the standard ruling for "create a token, then put counters on it"
    under a doubler is that every created token gets the counters. Treat it as working, but confirm in
    play the first time.

## 3. Cross-batch observations

- **Noncreature density is not a problem.** 84 of the 230 are noncreature spells (plus three Adventure
  halves), and 38 of the 56 cards graded ★★★/★★ are noncreature, so rule 3's 30–38 is met from the top
  grades alone. The creature count is the thin side: the core has about 18 creatures, which is fine
  because every turn adds a Hero token.
- **The pile splits into six usable clusters**, all of which point the same way:
  1. **Esper control suite** (instant-speed, rule 2): Absorb, Anguished Unmaking, Mortify, Void Rend,
     Ojutai's Command, Azorius Charm, Despark, Fracture, Consecrate, Sphinx's Revelation, Lawmage's
     Binding (flash Aura). About 18 interaction pieces at ★★ or better.
  2. **Flash enablers** that double the tokens per round: Leyline of Anticipation, Heliod's back face.
  3. **Counter / Hero / token payoffs** that read the commander's output: Metropolis Angel, Biorganic
     Carapace, Barrensteppe Siege, Serra Redeemer, Quintorius (proliferate), Kaya, Dramatic Finale,
     Captain America, Wings of Freedom and Super-Soldier, Baron Bertram, Ephara.
  4. **Life fuel** (rule 5): Y'shtola (drains on MV 3+ spells and DRAWS off the commander's own life
     payment), Sorin's extort, Doctor Strange's doubler, Revenge, Sphinx's Revelation, Absorb,
     Ojutai's Command, Archnemesis, Kambal, Elas il-Kor, plus lifelink bodies.
  5. **Planeswalkers**, each a noncreature cast with a life or counter engine: Teferi ×2, Kaya,
     Quintorius, Dovin, Narset.
  6. **Aura package** (17 Auras): removal Auras (Sheltered by Ghosts, Petrify, Nahiri's Binding,
     Lawmage's Binding), the repeatable Skyblade's Boon, and draw engines Sram and Pearl-Ear (every
     Hero token is "modified").
- **Combos worth protecting:** Y'shtola + any MV 4+ spell (the life payment is the draw trigger);
  Ephara + a token on each turn (two draws a round); Leyline of Anticipation + the removal suite;
  Skyblade's Boon (a 3/3 Hero every turn) + Sram; Serra Redeemer (+2 counters per token); Baron
  Bertram + Kambal + Elas (one spell = extra lifelink body, drain and life).
- **Variant signal (rule 7 of the skill):** the Aura cluster (Sram, Kor Spiritdancer, Light-Paws,
  Pearl-Ear, Danitha ×2, Greater Auramancy, 17 Auras) is coherent enough to be its own mono-white or
  Orzhov Aura deck with Light-Paws as commander. Noted, not pursued here.
- **Thin and off-plan:** Knights (History of Benalia carries it alone), Ninjas, party, Vampire tribal,
  Birds; big vanilla-ish creatures (Chromium, The Ur-Sphinx, Shattered Seraph).

## 4. Running verdicts

Legend: ★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out. Totals: ★★★ 13 · ★★ 43 ·
★ 66 · ◇ 65 · △ 42 · ✗ 1. The reasons move into the Builder project when the deck is drafted; until
then this table is their only durable home.

| Card | MV | NC? | Mark | Reason |
|---|---|---|---|---|
| Absorb | 3 | Y | ★★★ | Instant hard counter plus "You gain 3 life", which repays the X=3 Hero it makes on the opponent's turn (r2, r4, r5, r9) |
| Anguished Unmaking | 3 | Y | ★★★ | Instant "Exile target nonland permanent", MV 3 → 4/4 Hero on either turn (r2/r4/r9); the 3 life is the only cost |
| Ephara, God of the Polis | 4 | N | ★★★ | "Each upkeep, if another creature entered under your control last turn, draw" — a Hero on each turn (r2) = a card on BOTH upkeeps; indestructible |
| Invasion of New Phyrexia // Teferi Akosa of Zhalfir | X+2 | Y | ★★★ | "create X 2/2 … Knight tokens": the stack MV is X+2, so X=3 gives 3 Knights + a 6/6 Hero (r4/r6), go-wide; flips into a PW |
| Kaya, Geist Hunter | 3 | Y | ★★★ | PW → 4/4 Hero; "+1: … +1/+1 counter on up to one target creature token" (r6); "−2: … twice that many … tokens" doubles the next Hero |
| Leyline of Anticipation | 4 | Y | ★★★ | "Cast spells as though they had flash" — every noncreature spell can trigger on their turn, doubling tokens per round (r2) |
| Mortify | 3 | Y | ★★★ | Instant "Destroy target creature or enchantment", MV 3 → 4/4 Hero, on either turn (r2/r9) |
| Quintorius, Fate Splitter | 5 | Y | ★★★ | 6/6 Hero on cast (r1); "0: Proliferate. You gain 3 life" grows EVERY Hero token and refills life (r5/r6); −3 makes a token and puts a counter on each creature |
| Sheltered by Ghosts | 2 | Y | ★★★ | O-Ring "exile target nonland permanent" (r9) plus "lifelink and ward {2}" on a Hero token (r5, r6), all at MV 2 (r4). |
| Sphinx's Revelation | X+3 | Y | ★★★ | Instant, so cast it at the opponent's end step for a second token (r2); "You gain X life" refunds most of the X+3 payment (r5); card draw too |
| Teferi, Hero of Dominaria | 5 | Y | ★★★ | Planeswalker: "+1: Draw a card… untap up to two lands" refunds mana for a second spell; "−3" tucks any nonland permanent (r1, r9); MV5 trigger is optional (r4) |
| Void Rend | 3 | Y | ★★★ | Instant "destroy target nonland permanent", can't be countered — flexible answer at MV3 that can trigger on their turn (r2,r4,r9) |
| Y'shtola, Night's Blessed | 4 | N | ★★★ | "Noncreature spell MV 3+ → 2 damage, gain 2" refunds the X life (r5); paying X≥4 life to G'raha self-triggers her end-step draw (r4) |
| Abigale, Eloquent First-Year | 2 | N | ★★ | ETB on a Hero token loses nothing (tokens have no text) and gains flying/first strike/LIFELINK counters (r5/r6); a 2-drop lifelink body itself |
| Aerith Rescue Mission | 4 | Y | ★★ | "Create three 1/1 colorless Hero tokens" + G'raha's = 4 Heroes (r6) or tap three + stun (r9); MV4 sweet spot (r4) |
| Alela, Artful Provocateur | 4 | N | ★★ | Flying deathtouch lifelink (r5); "cast an artifact or enchantment spell → 1/1 flyer" doubles bodies with G'raha on every enchantment (r1,r6) |
| Archnemesis | 3 | Y | ★★ | MV3 aura on opponent: each attack "loses 2… you draw a card and gain 2 life" — Hero attackers make it card + life every turn (r4,r5) |
| Azorius Charm | 2 | Y | ★★ | Instant MV2: tuck an attacker/blocker on top of its library, or draw, or team lifelink; the lifelink mode turns a Hero swing into life fuel (r2, r4, r5, r9) |
| Baron Bertram Graywater | 4 | N | ★★ | "tokens … enter, create a 1/1 … Vampire Rogue … with lifelink" once per turn: every Hero gives an extra lifelink body (r5/r6); sac → draw |
| Barrensteppe Siege | 4 | Y | ★★ | Abzan "+1/+1 counter on each creature you control" every end step grows every Hero token (r6); Mardu edict if tokens trade; MV4 sweet spot (r4) |
| Biorganic Carapace | 4 | Y | ★★ | Equipment, auto-attaches; draws "a card for each modified creature" and every Hero token arrives carrying counters, so they are all modified (r1, r6) |
| Captain America, Super-Soldier | 3 | N | ★★ | "You and other Heroes you control have hexproof" while it keeps its shield: every commander token is a Hero (r6), and the life total is protected too (r5). |
| Captain America, Wings of Freedom | 3 | N | ★★ | "Each other Hero you control gets +X/+X" (X = toughness 3) on attack — every G'raha token is a Hero (r6); flying, first strike, ward |
| Consecrate // Consume | 2 | Y | ★★ | Consecrate is an INSTANT (MV 2) with gy hate + draw, a 3/3 on the opp's turn (r2/r4); Consume (MV 4) is an edict + "gain life equal to its power" (r5/r9) |
| Despark | 2 | Y | ★★ | Instant exile for "mana value 4 or greater" (r9), MV 2, so a 3/3 for 2 on the opp's turn (r2/r4); narrow targets |
| Detention Sphere | 3 | Y | ★★ | Exiles any nonland permanent, and every token sharing its name; MV3 noncreature (r1, r4, r9); sorcery speed only |
| Doctor Strange, Surgeon | 5 | N | ★★ | "If you would gain life, you gain twice that much": doubles G'raha's lifelink and every drain (r5). Reaching 35 life gives "+2/+2 and vigilance" to a go-wide Hero board (r6). |
| Dragoon's Lance | 2 | Y | ★★ | Job select "create a 1/1 colorless HERO token": with the commander, one MV-2 spell makes two Hero bodies (r1, r4, r6). Flying on your turn. |
| Dramatic Finale | 4 | Y | ★★ | "Creature tokens you control get +1/+1" = anthem for every Hero (r6); 2/1 flyer on nontoken death; hybrid cost easy (r7) |
| Firja's Retribution | 4 | Y | ★★ | MV4 Saga: 4/4 flyer, then a creature-kill tap ability (r9), then double strike — three chapters of value plus the trigger (r1,r4) |
| Fracture | 2 | Y | ★★ | Instant "Destroy target artifact, enchantment, or planeswalker", MV 2, so a 3/3 on the opp's turn (r2/r9) |
| Glasswing Grace // Age-Graced Chapel | 5 | Y | ★★ | MDFC: land when needed, else MV5 aura "+2/+2, flying and lifelink" — on a Hero token turns it into a lifelink fuel source (r5,r6) |
| Halvar, God of Battle // Sword of the Realms | 4 | Y | ★★ | Modal DFC: Sword (MV 2, noncreature) for the trigger and recursion (r1, r4), or Halvar for "enchanted or equipped creatures have double strike" on the Aura board. |
| Heliod, the Radiant Dawn // Heliod, the Warped Eclipse | 4 | N | ★★ | Back face: "You may cast spells as though they had flash", so EVERY noncreature spell can trigger the commander on the opponent's turn (r2); {U/P} costs 2 life (r5) |
| History of Benalia | 3 | Y | ★★ | MV-3 noncreature Saga (r1, r4): two 2/2 vigilance Knights plus a Hero token, then "Knights +2/+1". Three bodies from one card. |
| Invasion of New Capenna // Holy Frazzle-Cannon | 2 | Y | ★★ | Battle removal (sacrifice a spent Hero) (r9); back-face equip puts a counter on "each other creature … that shares a creature type": every Hero token (r6) |
| Invasion of Tolvada // The Broken Sky | 5 | Y | ★★ | ETB reanimates any nonbattle permanent; flipped "creature tokens get +1/+0 and have lifelink" turns every Hero into fuel (r5,r6) |
| Lawmage's Binding | 3 | Y | ★★ | FLASH aura "can't attack or block, abilities can't be activated" — instant-speed removal that triggers on their turn (r2,r9) |
| Metropolis Angel | 4 | N | ★★ | "Whenever you attack with one or more creatures with counters on them, draw a card": every Hero token has counters, so it draws each combat (r6) |
| Ojutai's Command | 4 | Y | ★★ | Instant: "Counter target creature spell" or "Draw a card" plus "You gain 4 life", which pays for its own 5/5 Hero; can reanimate a MV≤2 creature (r2, r5) |
| Ondu Knotmaster // Throw a Line | 4 | Y* | ★★ | Throw a Line is a MV2 sorcery cast = trigger (r1,r4) distributing counters; later a lifelinker that grows when a modified (countered) Hero dies (r6) |
| Pearl-Ear, Imperial Advisor | 3 | N | ★★ | Draws when "an Aura spell targets a MODIFIED permanent". Every Hero token carries counters and so counts as modified (r6). Lifelink (r5), plus Aura affinity. |
| Pull of the Mist Moon | 3 | Y | ★★ | O-ring enchantment, "exile target nonland permanent"; the kicker perpetually grants a second O-ring to a card in hand (r1, r4, r9) |
| Quake, Agent of S.H.I.E.L.D. | 3 | N | ★★ | Hero; "whenever you cast a noncreature spell, tap target creature or land" with NO once-per-turn cap — tempo off every spell (r1,r2) |
| Revival // Revenge | 2 | Y | ★★ | Revenge (MV 6): "Double your life total" is the biggest life refill here (r5); Revival (MV 2) reanimates MV ≤3 |
| Rite of Oblivion | 2 | Y | ★★ | "sacrifice a nonland permanent" (a spent 1/1 Hero) to exile any nonland permanent; Flashback is a second CAST → second trigger (r1/r9) |
| Serra Redeemer | 5 | N | ★★ | "Another creature with power 2 or less enters → two +1/+1 counters": a Hero token enters as a 1/1 before G'raha's counters, so every token gets +2 (r6). Same for the Lance token and Knights. |
| Shaile, Dean of Radiance // Embrose, Dean of Shadow | 2 | N | ★★ | Shaile puts a counter on "each creature that entered… this turn", which includes the turn's Hero token; Embrose pings 2 and draws when a countered creature dies (r6) |
| Skyblade's Boon | 2 | Y | ★★ | "{2}{W}: Return to hand", from the battlefield OR the graveyard: a repeatable MV-2 noncreature cast every turn, i.e. a 3/3 Hero each turn (r1, r3, r4). |
| Sorin of House Markov // Sorin, Ravenous Neonate | 2 | N | ★★ | Extort on "Whenever you cast a spell" drains 1 per spell, which refills the life the commander spends (r5); lifelink plus the commander flips him; −1 burns |
| Spider-Woman, Secret Agent | 4 | N | ★★ | Flash Hero; locks down a creature "for as long as you control Spider-Woman", so it is instant-speed interaction (r9); enables Hylda/Sharae taps |
| Sram, Senior Edificer | 2 | N | ★★ | "Whenever you cast an Aura, Equipment, or Vehicle spell, draw a card", with no per-turn cap: the card-advantage engine for this part's Aura/Equipment package. |
| Stormkeld Curator // Giant Secrets | 6 | Y* | ★★ | Giant Secrets is an INSTANT {X}{U}{U}: X=2 is MV4 → 5/5 Hero on their turn + 2 cards (r2,r4); Curator body re-buys auras late |
| Teferi, Who Slows the Sunset | 4 | Y | ★★ | PW cast = 5/5 Hero for 4 life (r1/r4); "+1 … You gain 2 life" refunds half the payment (r5); −2 card selection; sorcery-speed only |
| The Mighty Thor, Jane Foster | 3 | N | ★★ | Esper 3-drop flyer. The attack trigger "exile … nontoken artifact or creature … return tapped" clears a blocker (r9 tempo), and "Equipment enters, draw" pairs with Lance and Sword. |
| Twining Twins // Swift Spiral | 4 | Y* | ★★ | *Adventure "Swift Spiral" is an MV2 instant, a noncreature cast on either turn (r1, r2); it blinks a nontoken creature to save it, then a 4-MV flier |
| Adeline, Resplendent Cathar | 3 | N | ★ | "Power equal to the number of creatures you control" scales with the commander's tokens (r6), and it makes a 1/1 on each attack. A strong card, but no trigger (r1). |
| Angelic Destiny | 4 | Y | ★ | "+4/+4, flying, first strike", returns to hand when the creature dies so you can recast it for another trigger (r1). Makes the creature an Angel for Lyra. |
| Arvad, Weatherlight Smuggler | 2 | N | ★ | 2-drop deathtouch+lifelink (r5); the perpetual growth needs deaths (sac outlets in this part) |
| Aryel, Knight of Windgrace | 4 | N | ★ | Activated Knight tokens + "Destroy target creature with power X or less"; pairs with Invasion of New Phyrexia's Knights |
| Aven Wind Guide | 4 | N | ★ | "Creature tokens you control have flying and vigilance": every Hero token becomes an evasive attacker that can still block (r6) |
| Ayli, Eternal Pilgrim | 2 | N | ★ | "Sacrifice another creature: You gain life equal to … toughness": a spent X+1 Hero refunds the payment (r5); exile mode needs 35 life in Brawl |
| Banish into Fable | 6 | Y | ★ | Instant bounce + Knight, so it works on the opponent's turn (r2); copies off artifact/enchantment; MV 6 = a 7/7 for 6 life, so usually decline (r4) |
| Benalish Sleeper | 2 | N | ★ | Kicked: "each player sacrifices a creature", and a 1/1 Hero token is the cheap sacrifice, so it is a one-sided edict (r6, r9) |
| Captain America, Unbowed | 4 | N | ★ | Flash, then "Soldiers and Heroes you control gain indestructible": an instant-speed wrath answer for a Hero-token board (r6, r9). It is a creature, so no trigger. |
| Cid, Timeless Artificer | 4 | N | ★ | "Artifact creatures and Heroes you control get +1/+1 for each Artificer", an anthem for every Hero token (r6); any number of copies are legal; cycling |
| Coerced to Kill | 5 | Y | ★ | Sorcery-speed steal "You control enchanted creature" as a 1/1 deathtouch — removal that adds a blocker (r9); MV5 life cost (r4) |
| Dance of the Manse | 2 | Y | ★ | X counts on the stack: MV X+2 sizes the Hero (r4); returns non-Aura enchantments ≤X — good if the 99 is enchantment-dense |
| Danitha Capashen, Paragon | 3 | N | ★ | First strike, vigilance and lifelink (r5). "Aura and Equipment spells cost {1} less" speeds up the package without lowering MV, so X is intact (r4). |
| Danitha, Sword of Hope | 3 | N | ★ | "Equipment spell or a spell that targets a creature you control, draw a card", once each turn. Every Aura qualifies, so it draws about once a turn here (r3). |
| Denzilore Fatehold | 4 | N | ★ | Flash flier; "Whenever you scry or surveil, put a +1/+1 counter on each creature" grows the Hero tokens (r6), but the scry count in this part is thin (Runic Shot kicker, Niko Shards) |
| Doctor Spectrum | 5 | N | ★ | The ETB "+1/+1 counter on each other Hero you control" scales with the commander's tokens (r6); the "destroy target enchantment" mode is a flexible answer (r9). |
| Dovin, Architect of Law | 6 | Y | ★ | "+1: You gain 2 life and draw a card" is a life+card engine (r5); −1 taps a creature (tempo); 6 MV makes the Hero cost 6 life (r4) |
| Drana and Linvala | 4 | N | ★ | Flying vigilance body that shuts off opposing creatures' activated abilities and steals them; creature, so no trigger (r1) — graded on hate value |
| Eirdu, Carrier of Dawn // Isilu, Carrier of Twilight | 5 | N | ★ | Flying lifelink body (r5); Isilu gives "nontoken" creatures persist, so the Hero tokens get nothing; convoke only helps creature spells |
| Elas il-Kor, Sadistic Pilgrim | 2 | N | ★ | "Whenever another creature you control enters, you gain 1 life": every Hero token refunds 1 (r5); drain on death |
| Elenda, the Dusk Rose | 4 | N | ★ | Lifelink (r5) and "whenever another creature dies, +1/+1 counter" — chump-blocking Heroes grow her; death leaves lifelink tokens |
| Ethereal Absolution | 6 | Y | ★ | "+1/+1 ours, -1/-1 theirs" anthems every Hero and wipes opposing 1/1s (r6,r9); MV6 = 6 life for the Hero (r4) |
| Faithful Mending | 2 | Y | ★ | Instant: "gain 2 life, draw two, then discard two", and flashback is a second noncreature cast later (r1, r2, r5); card-neutral filtering |
| Friendly Neighborhood | 4 | Y | ★ | "Create three 1/1 … Citizen tokens" plus a 5/5 Hero: four bodies from one MV-4 noncreature spell (r1, r4, r6). The pump land stays as a mana sink. |
| Gift of Orzhova | 3 | Y | ★ | Aura MV 3 → 4/4 Hero (r1), then "flying and lifelink" on that Hero turns it into a life engine (r5/r6); aura risk |
| Gold-Forged Thopteryx | 2 | N | ★ | 2-mana flying lifelink (r5); "Each legendary permanent you control has ward {2}" protects the commander |
| Hardened Tactician | 3 | N | ★ | "{1}, Sacrifice a token: Draw a card": a spent Hero token becomes a card (r6) |
| Hawkeye, Bowslinger | 3 | N | ★ | Hero; "cast a spell that targets a creature" → counter + scry — auras and removal fire it (r6) |
| Hindering Light | 2 | Y | ★ | Instant "Counter target spell that targets you or a permanent you control. Draw a card." protects the commander and the token board (r2) |
| Humiliate | 2 | Y | ★ | Sorcery hand attack + "+1/+1 counter on a creature you control" (on a Hero, r6); MV 2 → 3/3 |
| Hylda of the Icy Crown | 4 | N | ★ | "Whenever you tap an untapped creature an opponent controls", pay {1} for a 4/4, team counters or a card; needs the tap package (Spider-Woman SA, Sharae) |
| Indulging Patrician | 3 | N | ★ | Flying lifelink; "if you gained 3 or more life this turn, each opponent loses 3": G'raha's lifelink helps hit it (r5) |
| Kambal, Profiteering Mayor | 3 | N | ★ | "Whenever one or more tokens you control enter, each opponent loses 1 life and you gain 1": fires off each Hero (r5/r6); copies their tokens |
| Killian, Ink Duelist | 2 | N | ★ | Lifelink menace 2-drop (r5); "cost {2} less" cuts the price, not the MV, so removal makes the same-size Hero for less mana (r4) |
| King T'Challa // Black Panther, Hope Enduring | 3 | N | ★ | Flash Hero; "Whenever a player draws their second card each turn, you draw", which pairs with the draw spells in this part (Mending, Charm, Teferi) |
| Light of Promise | 3 | Y | ★ | "Whenever you gain life, put that many +1/+1 counters": on lifelinked G'raha, or with Doctor Strange doubling, every hit grows it (r5, r6). |
| Malcator, Purity Overseer | 3 | N | ★ | 3 mana for two bodies (a 3/3 Golem artifact token); Cid pumps artifact creatures; the end-step clause rarely fires |
| Nahiri's Binding | 3 | Y | ★ | Pacifism for a "creature or planeswalker" with activated abilities locked (r9), plus a 4/4 Hero (r1, r4). Sorcery speed. |
| Narset Transcendent | 4 | Y | ★ | +1 takes "a noncreature, nonland card", a hit rate that rises with r3 density; −2 rebound recasts an instant on your upkeep, which uses that turn's trigger (r1) |
| Neva, Stalked by Nightmares | 4 | N | ★ | Menace; ETB regrows a creature or enchantment; grows + scry when an enchantment (Sagas, Sieges) leaves — card advantage body |
| Niko, Light of Hope | 4 | N | ★ | Two Shard enchantment tokens (scry 1, draw); the copy ability can't target tokens' value well. Shards feed Denzilore's scry (r6) |
| Nimble Larcenist | 3 | N | ★ | 3-MV flyer whose ETB exiles an artifact/instant/sorcery from their hand — proactive disruption (r9), creature so no trigger |
| Paladin's Arms | 3 | Y | ★ | MV3 cast = G'raha Hero + Job-select Hero (two bodies, r1,r6); +2/+1 ward 1; equip {4} is clunky |
| Pearl Collector | 3 | N | ★ | Deathtouch and lifelink; with 4+ life gained it conjures Mox Pearl, an MV0 noncreature cast that makes a free 1/1 Hero (r1, r5) |
| Petrify | 2 | Y | ★ | MV-2 Aura removal, "can't attack or block … activated abilities can't be activated", plus a 3/3 Hero token (r1, r4, r9). Sorcery speed. |
| Plaza of Heroes | 0 | N | ★ | Its any-colour mana is spendable "only to cast a legendary spell" (the commander qualifies, r7), and "{3},{T}, exile: hexproof and indestructible" protects G'raha. |
| Protect the Negotiators | 2 | Y | ★ | Instant soft counter that taxes "{1} for each creature you control", and Hero tokens raise the tax; kicker adds a Soldier (r2, r6, r9) |
| Queza, Augur of Agonies | 4 | N | ★ | "Whenever you draw a card… lose 1, you gain 1" — steady life refill (r5); pairs with Ephara/Y'shtola draws; creature |
| Rampage of the Valkyries | 5 | Y | ★ | MV5 enchantment: 4/4 flying vigilance Angel + edict whenever an Angel dies; Firja's Angel also qualifies (r1,r9) |
| Rodolf Duskbringer | 6 | N | ★ | Flying, deathtouch, lifelink 6-drop; reanimates MV≤"life gained this turn", and the commander's lifelink sets that number (r5) |
| Runic Shot | 1 | Y | ★ | "Destroy target tapped creature": anything that attacked you last turn is still tapped on your turn; MV1 makes only a 2/2 (r4, r9) |
| Ruthless Lawbringer | 3 | N | ★ | "sacrifice another creature. When you do, destroy target nonland permanent": a spent Hero buys removal (r9) |
| SP//dr, Piloted by Peni | 5 | N | ★ | "Whenever a modified creature you control deals combat damage … draw a card": every Hero token carries counters, so they all count as modified (r6, density from the commander) |
| Saruman of Many Colors | 6 | N | ★ | "Second spell each turn" → free copy of their instant/sorcery/enchantment = a free noncreature cast; ward-discard; 6-drop creature (r1) |
| Scriv, the Obligator | 4 | N | ★ | Flying deathtouch; Contract tokens make their attackers "lose 2 life" in 1v1 — drain-style pressure; tokens are Auras for Eriette (r5) |
| Secret Identity | 1 | Y | ★ | 1-mana instant that triggers on the opponent's turn (r2). Conceal gives hexproof and saves a pumped token from removal; Reveal makes a 3/4 flyer. Only a small body (r4). |
| Sentinel's Mark | 2 | Y | ★ | Flash Aura: a noncreature spell on the opponent's turn for a second token per round (r2). "+1/+2, vigilance"; main-phase casts add lifelink (r5). |
| Sharae of Numbing Depths | 4 | N | ★ | ETB tap plus stun counter (tempo interaction); draws "once each turn" when you tap their creatures, which overlaps with Hylda |
| Spider-Woman, Stunning Savior | 2 | N | ★ | 2-mana flying Hero with hybrid {W/U}; opposing creatures "enter tapped", buying a turn for the life-paying plan |
| Staggering Insight | 2 | Y | ★ | Aura: lifelink plus "draw a card" on combat damage; put it on an evasive Hero token for life fuel (r1, r5); aura risk applies |
| Summon: Primal Odin | 6 | N | ★ | Its Enchantment Creature type makes it a CREATURE spell, so no trigger (r1). Chapter I "Destroy target creature" plus chapter III "Draw two" is real interaction (r9); the 2 life loss is minor (r5). |
| The Circle of Loyalty | 6 | Y | ★ | Legendary artifact: "Creatures you control get +1/+1" on a token board (r6), and a Knight on each "legendary spell" (the commander too). Affinity cuts its cost, not its MV, so X stays 6 (r4). |
| Tymna the Weaver | 3 | N | ★ | Lifelink; "pay X life … draw X cards" at most 1 per turn in 1v1, and Hero tokens connecting enable it (r5) |
| White Widow, Free Agent | 4 | N | ★ | Hero; ETB +1/+1 counters on two creatures (r6) or regrow an artifact/enchantment card — flexible value |
| Wiccan, Rising Magician | 5 | N | ★ | "Whenever you cast a noncreature spell, exile another target nonland, nontoken permanent" until end step: a blocker or blink every spell, with no once-per-turn cap (r1, r3). |
| Zur, Eternal Schemer | 3 | N | ★ | Enchantment creatures get deathtouch, lifelink, hexproof; {1}{W} animates non-Aura enchantments (MV-sized bodies) — enchantment-deck value |
| Abigale, Poet Laureate // Heroic Stanza | 3 | N | ◇ | Becomes prepared only on a "creature spell" cast (G'raha's tokens aren't cast). The copy of the sorcery half (+1/+1 counter, MV 2) does trigger r1, but the deck is noncreature-heavy (r3). |
| Arvad the Cursed | 5 | N | ◇ | Deathtouch and lifelink (r5). "Other legendary creatures +2/+2" misses Hero tokens (not legendary) unless they carry Super-Soldier Serum. |
| Athreos, Shroud-Veiled | 6 | N | ◇ | Creature SPELL on the stack (no trigger, r1); coin-counter recursion is slow value; devotion 7 unlikely |
| Azor, the Lawbringer | 6 | N | ◇ | The attack trigger pays {X}{W}{U}{U} for "gain X life and draw X" (r5), but it's a 6-MV creature that has to survive to attack; no help to the engine |
| Bard the Bowman | 3 | N | ◇ | "draw your second card each turn": a counter plus lifelink, which needs a draw spell every turn to fire |
| Black Panther, Most Dangerous | 3 | N | ◇ | Hero; damage-reflection body; power-up {5}{W}{W} team pump is an activation, not a cast (r1) |
| Born to Drive | 3 | Y | ◇ | "+1/+1 for each creature" on a wide board (r6). Channel makes two Pilots, but Channel is an activated ability, not a cast, so no trigger. |
| Captain America, Skybound | 5 | N | ◇ | Battalion "+1/+1 counter on each attacking creature" plus indestructible fits a wide Hero board (r6). A 5-drop with no trigger (r1). |
| Captain America, Steve Rogers | 5 | N | ◇ | Lifelink (r5) and "+1/+1 counter on another target creature" on attack grows a Hero token (r6); a 5-drop creature that adds no trigger (r1). |
| Commanding Presence | 4 | Y | ◇ | "+2/+2, first strike" plus a Soldier token on combat damage. MV 4 for a 5/5 Hero (r4), but a mid-power Aura. |
| Cruel Celebrant | 2 | N | ◇ | Drain 1 on each death (r5): only as good as the sac-outlet count |
| Dion, Bahamut's Dominant // Bahamut, Warden of Light | 4 | N | ◇ | ETB 2/2 Knight. The back face's "+1/+1 counter on each other creature" stacks on Heroes (r6) and Gigaflare is removal. The {4}{W}{W} transform is slow. |
| Diviner of Fates | 3 | N | ◇ | ETB connive + "seek a card that shares a type" once per turn on discard; filter body, no engine tie, creature (r1) |
| Eagle's Rescue | 4 | Y | ◇ | +2/+2 flying aura at MV4 (r1); graveyard return is an activation onto power ≤1 — only an X=0 Hero qualifies (r6), so recursion rarely live |
| Edgar, Ancient Bloodlord | 2 | N | ◇ | Gain 1 on each death; the sac outlet can turn spent Heroes into counters; aristocrats glue |
| Elenda, Saint of Dusk | 4 | N | ◇ | Bonus needs "life total greater than your starting life total" — fights the X-life payments the deck makes every turn (r5); lifelink only |
| Eriette of the Charmed Apple | 3 | N | ◇ | End-step drain X = Auras you control (r5); Scriv's Contract tokens count; needs aura density the 99 may not have |
| Eriette, the Beguiler | 4 | N | ◇ | Steal clause needs Auras on opponents' permanents with MV ≥ target (Lawmage's Binding steals MV≤3); aura-density dependent, lifelink (r5) |
| Errant and Giada | 3 | N | ◇ | Flash flier; cast "spells with flash or flying" from the top, but instants do not have flash, so it does not reach the noncreature core (r3) |
| Ezrim, Agency Chief | 5 | N | ◇ | "investigate twice" = 2 Clues, and cracking them is not a cast; WWUU 5-drop creature, can gain lifelink by sacrificing an artifact (r5), off-engine |
| Feast of the Victorious Dead | 2 | Y | ◇ | Noncreature MV 2 → 3/3 (r1); the end-step gain + counters needs a death that turn (r6) |
| Frodo, Adventurous Hobbit | 2 | N | ◇ | "if you gained 3 or more life this turn": G'raha's lifelink turns this on; the Ring is slow value |
| Golden Sidekick | 2 | N | ◇ | Flying lifelink 2-drop (r5); the perpetual pump only reaches creature cards in hand, and this deck is spell-heavy |
| Greater Auramancy | 2 | Y | ◇ | Shroud for enchantments and enchanted creatures protects the Aura pile. A cheap trigger (r4), but no effect on the board. |
| Head of the Class | 2 | N | ◇ | Spells that target a creature "cost {W}{B} less": a cost cut keeps the MV, so the token is unchanged (r4); Repartee grows it |
| Hope Against Hope | 3 | Y | ◇ | "+1/+1 for each creature you control" scales with the commander's tokens (r6). An aggro Aura that adds a trigger. |
| Inquisitive Glimmer | 2 | N | ◇ | "Enchantment spells cost {1} less" — MV is unchanged so the Hero size and X life are the same (r4); pure ramp, creature |
| Invasion of Xerex // Vertex Paladin | 4 | Y | ◇ | A Battle is a noncreature cast (r1); the ETB bounce is tempo; it flips to a flier sized by "the number of creatures you control", which Hero tokens grow |
| Ishai, Ojutai Dragonspeaker | 4 | N | ◇ | Flier that grows on opponent spells; partner is irrelevant under G'raha; a plain beater |
| Kambal, Consul of Allocation | 3 | N | ◇ | Taxes the OPPONENT's noncreature spells (drain 2) (r5); a matchup card, not engine |
| Karai, Future of the Foot | 3 | N | ◇ | Combat-damage recursion; the sneak line wants unblocked attackers; off-engine |
| Kels, Fight Fixer | 4 | N | ◇ | Draws "whenever you sacrifice a creature", and Hero tokens are fodder, but the sac outlet is only "{1}, Sacrifice: indestructible" (r6) |
| Killian, Decisive Mentor | 3 | N | ◇ | Enchantment ETB taps+goads (tempo); draw when aura'd creatures attack — needs auras on own attackers; creature (r1) |
| Kor Spiritdancer | 2 | N | ◇ | "Whenever you cast an Aura spell, you may draw": good only with heavy Aura density (this part has ~17). It's a creature (r1). |
| Kunoros, Hound of Athreos | 3 | N | ◇ | Vigilance/menace/lifelink body (r5), but "can't cast spells from graveyards" kills your own Rite flashback and Revival/Karai/Sandbender |
| Lavinia, Azorius Renegade | 2 | N | ◇ | A hoser against cheated and free spells and the opponent's big noncreature spells; it does not restrict you; meta-dependent (r9) |
| Leyline of Hope | 4 | Y | ◇ | "+1 per lifegain" pads lifelink (r5); the +2/+2 needs 7 over starting life, which X-payments make rare; free on turn 0 skips the cast |
| Leyline of Transformation | 4 | Y | ◇ | Choose Hero: every creature is a Hero for Captain America/Hero payoffs (r6) — value scales with Hero-payoff count, does nothing alone |
| Light-Paws, Emperor's Voice | 2 | N | ◇ | A cast Aura tutors a second Aura of equal or lower MV onto Light-Paws. It needs the deck built as Auras, and it's a creature (r1). |
| Mockingbird, Ace Agent | 4 | N | ◇ | Hero, double strike; counters only on spells targeting her — needs own-targeting auras; creature (r1) |
| Naomi, Pillar of Order | 5 | N | ◇ | Samurai tokens only "if you control an artifact and an enchantment"; MV5 creature (r1) with a condition to count |
| Obscura Ascendancy | 3 | Y | ◇ | Needs spells at MV 1,2,3,4,5 in sequence for Spirits; MV3 cast trigger itself (r1); Spirit anthem doesn't hit Heroes (r6) |
| One Last Job | 3 | Y | ◇ | Spree reanimation (creature, or Aura/Equipment attached). MV is 3 whatever modes you pay, so a 4/4 token (r4). Sorcery. |
| Pariah | 3 | Y | ◇ | "All damage that would be dealt to you is dealt to enchanted creature": shields the life budget (r5). Best on an indestructible or large Hero token. |
| Restricted Office // Lecture Hall | 4 | Y | ◇ | FIGHTS ENGINE: "destroy all creatures with power 3 or greater" kills your own Heroes (the X=3 token from casting it is 4/4); Lecture Hall's unlock is not a cast |
| Rise to Glory | 5 | Y | ◇ | MV5 sorcery reanimating a creature and an Aura (r1); fine value but slow and graveyard-dependent; 5 life for the Hero (r4) |
| Rogue Class | 2 | Y | ◇ | MV2 cast trigger; levels are activations, not casts (r1); Hero attackers exile/play their cards — slow |
| Sandbender Scavengers | 2 | N | ◇ | Grows on each sacrifice; the death trigger reanimates; needs a sac density this part only half provides |
| Senate Guildmage | 2 | N | ◇ | "{W},{T}: You gain 2 life" repays an X=2 Hero every turn (r5) but costs mana and a tap; slow |
| Shilgengar, Sire of Famine | 5 | N | ◇ | Sacrifices Hero tokens for Blood; six Blood reanimates the whole yard; slow and grindy, and it eats the board the commander built |
| Skycat Sovereign | 2 | N | ◇ | Flier lord counts "other creature you control with flying"; it scales only with Aven Wind Guide making Hero tokens fly (r6) |
| Snooping Page | 3 | N | ◇ | Repartee unblockable + draw on hit; needs targeted instants/sorceries |
| Spectral Steel | 2 | Y | ◇ | "+2/+2", and its graveyard ability buys back another Aura or Equipment. A cheap trigger (r4). |
| Sun-Spider, Nimble Webber | 4 | N | ◇ | Hero that tutors "an Aura or Equipment card" for Biorganic Carapace or Staggering Insight; the value depends on that package's size |
| Super-Soldier Serum | 2 | Y | ◇ | "+2/+2, first strike, vigilance, legendary Soldier": makes a Hero token legendary, so Arvad pumps it and Cap Unbowed protects it. Mostly a cheap trigger (r4). |
| Superior Spider-Man | 4 | N | ◇ | Hero clone of "any creature card in a graveyard" (either yard); value depends on what has died; creature slot (r3) |
| Symbiote Spider-Man | 3 | N | ◇ | Hybrid Hero; combat-damage dig; Find New Host is an activation, not a cast, but it can put its abilities on a Hero token from the graveyard (r6) |
| Syr Vondam, Sunstar Exemplar | 2 | N | ◇ | Counter + gain 1 on each death/exile (r5/r6); at 4+ power its death destroys a nonland permanent |
| Taigam, Ojutai Master | 4 | N | ◇ | Rebound needs "Taigam attacked this turn"; the rebound cast lands in YOUR upkeep, which spends that turn's once-each-turn trigger (r1, r2) |
| Tameshi, Reality Architect | 3 | N | ◇ | Sorcery activation returns artifact/enchantment ≤X by bouncing a land — slow recursion, not a cast (r1) |
| Tomik, Wielder of Law | 3 | N | ◇ | Flying vigilance; in 1v1, when they attack with two or more creatures: drain 3 + draw; affinity for planeswalkers |
| Tura Kennerüd, Skyknight | 5 | N | ◇ | "Whenever you cast an instant or sorcery spell, create a 1/1": stacks with G'raha off the same spells, but it's a 5-drop creature and misses PWs, auras and battles |
| War Machine, James Rhodes | 4 | N | ◇ | Is a Hero but pays off nothing; "Whenever War Machine attacks, tap up to one target creature" is a fine evasive 4-drop, creature (r1 no bonus) |
| Will, Scion of Peace | 3 | N | ◇ | Sorcery-speed tap: W/U spells cost X less "where X is the amount of life you gained this turn"; the commander's lifelink sets X; it needs combat first |
| Wondrous Revival | 6 | Y | ◇ | "Up to three target Hero creature CARDS": tokens never reach the yard as cards, so it needs real Heroes (9 in this part). MV 6 means a 7/7 for 6 life (r4). |
| Acclaimed Contender | 3 | N | △ | Its ETB digs for "a Knight, Aura, Equipment, or legendary artifact" but needs another Knight. A creature (r1). |
| Ace Flockbringer | 3 | N | △ | Triggers on "a creature spell without flying", which pulls the deck toward creatures, the opposite of r3 |
| Athreos, God of Passage | 3 | N | △ | A God is a creature card off the battlefield, so this is a CREATURE spell (no trigger); returning dead creatures misses tokens; rarely a creature |
| Battlewise Hoplite | 2 | N | △ | Heroic needs "a spell that targets this creature", and this part has few targeted own-creature spells (Insight, Safeguard) |
| Black Widow, Double Agent | 3 | N | △ | Deathtouch Hero; "attacks alone" grants first strike plus menace, which works against a go-wide Hero-token board (r6) |
| Brigone, Soldier of Meletis | 2 | N | △ | Heroic counter plus "remove a counter: draw" wants spells that target it. Many Auras do, but it's a 2-drop body. |
| Brokers' Safeguard | 2 | Y | △ | Instant MV2 noncreature (r2), but it blinks a creature to protect it, and a blinked Hero TOKEN is exiled and gone; nontoken creatures only |
| Captain America, Living Legend | 3 | N | △ | Untaps creatures first tapped "during your turn", a team-vigilance effect for Hero tokens; a soft effect on a creature slot (r3) |
| Champions of Tyr | 4 | N | △ | The one-time boon fires only on a "creature spell" cast. The deck wants noncreature density (r3). |
| Chromium, the Mutable | 7 | N | △ | Flash uncounterable 7-drop flyer; no engine interaction and 7 MV creature crowds the curve (r1,r4) |
| Cleric of Life's Bond | 2 | N | △ | "first time each turn" gain → +1/+1 counter; a small body, and the Cleric clause is narrow |
| Dark Leo & Shredder | 2 | N | △ | Ninja payoff with no Ninja density; Hero tokens aren't Ninjas |
| Don & Leo, Problem Solvers | 5 | N | △ | End-step blink of "a creature you control" would EXILE a Hero token for good (tokens cease to exist); it's optional ("up to one"), but the only good target is your own creature |
| Doom Foretold | 4 | Y | △ | Symmetric "sacrifices a nonland, nontoken permanent" each upkeep eats OUR commander/enchantments; Hero tokens don't satisfy it — fights the engine |
| Due Diligence | 3 | Y | △ | "+2/+2, vigilance" plus a one-turn +2/+2. Vanilla pump at MV 3 that adds only the trigger (r1). |
| Fiendslayer Paladin | 3 | N | △ | First strike and lifelink is modest fuel (r5). Otherwise a vanilla 3-drop creature (r1). |
| Fleshtaker | 2 | N | △ | Sac outlet: gain 1 + scry 1 per sac; low impact |
| General's Enforcer | 2 | N | △ | "Legendary Humans … indestructible": few targets here; the gy-exile ability makes a token, but it's expensive |
| Gwaihir the Windlord | 6 | N | △ | 6-MV flier; the discount needs two draws in a turn and the Bird clause is dead; nothing for the engine |
| Hallowed Respite | 2 | Y | △ | A sorcery blink that kills your own Hero tokens and resets their counters; it only taps an opposing creature; flashback is a second cast (r1) |
| Hashaton, Scarab's Fist | 2 | N | △ | Needs "discard a creature card": no discard engine here |
| Jubilant Skybonder | 3 | N | △ | Taxes targeting of your fliers by {2}, which helps only if Hero tokens fly (Aven Wind Guide); a weak body |
| Knights' Charge | 3 | Y | △ | Drain only "whenever a Knight attacks" — only Paladin's Arms makes Knights here (r6 count ≈ 1); MV3 trigger is its only value |
| Lo and Li, Royal Advisors | 4 | N | △ | Mill grows only Advisors (itself); blind mill is a clock, not interaction (G-62) |
| Lulu, Forgetful Hollyphant | 3 | N | △ | The one-time boon gives flying to a creature SPELL. Tokens aren't cast, so it misses the engine (r1, r3). |
| Lyra, Archangel of Dawn | 3 | N | △ | "Whenever you gain life, +1/+1 counter on each ANGEL": Hero tokens aren't Angels except under Angelic Destiny, so its lifegain hook rarely pays (r5). |
| Marshal of Zhalfir | 2 | N | △ | "Other Knights +1/+1": Hero tokens aren't Knights unless they hold the Lance. The tap ability is mild tempo. |
| Nalia de'Arnise | 3 | N | △ | Full-party clause: Hero tokens aren't party classes; play-from-top only for 4 classes |
| Panicked Bystander // Cackling Culprit | 2 | N | △ | "gain 1 life" on each death; small lifegain fuel (r5) but a weak body |
| Photon, Lady of Light | 4 | N | △ | Fights the engine: "exile … then return that card" kills a Hero TOKEN outright, and blinking a real creature wipes its counters (r6, G-42). |
| Rona, Herald of Invasion // Rona, Tolarian Obliterator | 2 | N | △ | A looter that untaps on "a legendary spell"; the back face costs 6; few legendary noncreature spells in this part |
| Seething Skitter-Priest | 4 | N | △ | Mite-on-death grant is perpetual only to creatures present/in hand at ETB, so future Hero tokens miss it; toxic 1 off-plan; creature (r1) |
| Shattered Seraph | 7 | N | △ | {2} exile-from-hand fixing is an activation, not a cast; the later cast is a creature spell (r1); 3 life on ETB only |
| Silverquill Pledgemage | 3 | N | △ | Magecraft grants flying or lifelink for the turn; a weak 3-drop body |
| Slumbering Keepguard | 1 | N | △ | "Whenever an enchantment you control enters, scry 1" plus a pump per enchantment: live with this part's aura density, but a 1-drop body that adds no trigger (r1). |
| Splinter, Radical Rat | 3 | N | △ | Doubles triggers of NINJA creatures only; the deck has no Ninjas and Heroes aren't Ninjas (r6 count = 0) |
| Squall, SeeD Mercenary | 4 | N | △ | "Attacks alone … double strike" works against a go-wide Hero board (r6). Recursion of a permanent with MV 3 or less is the upside. |
| Taeko, the Patient Avalanche | 4 | N | △ | It grows when creatures leave "if it didn't die" (blink and bounce); enters tapped; the unblockable clause has a cost |
| The Sentry, Golden Guardian | 4 | N | △ | ETB gives the opponent a 5/5 flying INDESTRUCTIBLE Void — hands them a threat our removal can't kill; Hero tag isn't worth it |
| The Ur-Sphinx | 9 | N | △ | 9-MV creature with no Sphinx density; free casts of milled cards rarely land before the game is decided (r4) |
| Transcendent Envoy | 2 | N | △ | Enchantment Creature: a creature spell. "Aura spells cost {1} less" leaves X intact (MV unchanged), but it's a 2/2-ish flyer with no trigger. |
| Wingbright Thief | 2 | N | △ | 2-MV flyer; perpetual "opponent draws and gains 3" tax on one of their cards is minor; creature (r1) |
| Voracious Vampire | 3 | N | ✗ | Its ETB pumps only "target Vampire you control"; there is no Vampire spine. A 2/2 menace creature with no trigger (r1). |

## 5. Consolidated plan (live)

**Direction: Esper spells-and-Heroes control.** Instant-speed removal and planeswalkers as the
noncreature base, flash enablers to trigger on both turns, payoffs that read the Hero tokens and their
counters, and lifegain to keep paying. The 56 cards at ★★★/★★ are already a near-complete core: 38
noncreature, about 18 creatures, roughly 18 interaction pieces.

**Core (★★★, 13):** Teferi, Hero of Dominaria; Absorb; Quintorius, Fate Splitter; Invasion of New
Phyrexia; Sphinx's Revelation; Anguished Unmaking; Kaya, Geist Hunter; Mortify; Void Rend; Y'shtola,
Night's Blessed; Ephara, God of the Polis; Leyline of Anticipation; Sheltered by Ghosts.

**Strong (★★, 43):** see §4. Every one is in the starting pool for the draft.

**To fill the last ~7 slots, best ★ candidates:** Light of Promise, Gift of Orzhova, Angelic Destiny,
Friendly Neighborhood, Petrify, Nahiri's Binding, Faithful Mending, Sentinel's Mark, Kambal,
Profiteering Mayor, Elas il-Kor, Gold-Forged Thopteryx, Captain America, Unbowed.

**Gaps the pile does not cover:** lands (only Plaza of Heroes and Glasswing Grace's land face) — the
manabase comes from the collection; little acceleration (no mana rocks); few cheap creatures.

**Protect list (value the tools cannot see, rule 8):** G'raha's token engine itself, Y'shtola,
Ephara, Leyline of Anticipation, Heliod, Serra Redeemer, Skyblade's Boon, Biorganic Carapace,
Metropolis Angel — all scale with the commander's tokens, which no model counts as bodies.

**Next:** owner picks the direction, then `/draft-deck` builds the 100 and the Builder board.
