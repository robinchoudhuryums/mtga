# UW equipment / artifact pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into the
deck files' `#: notes:` blocks. A scratchpad, not a source of truth — decks/ are.

**Source list:** `/tmp/claude-0/scratch/pile.txt` — 95 lines = the 22-card blue-equipment
pile + the 73-card second pile. 1 card (Katara, Water Tribe's Hope) is already in deck 27
and is dropped; **94 to evaluate**.

**The question:** does this pile warrant a NEW UW deck, and where do the cards that do not
make that deck belong among the existing UW / mono-U decks (15 Air Nomads, 16 Moon Spirit,
18 Atlantis Attacks, 27 Blink, 47 Grid Overload, 51/51a Unlocked)?

---

## 1. The decision framework

Written before batch 1. Later batches cite these by number.

**F1 — "Already in another deck" is NOT a disqualifier.** Decks share the collection
(CLAUDE.md, Key Design Decisions): one owned copy can sit in any number of decks at once,
so a card living in deck 57 is fully available to a new deck. The only real dedupe is
against the deck a card is being *proposed into*. 69 of the 94 have homes; those homes are
recorded as **context** (a card in seven decks is a known-good generic, a card in zero is
either a gem or a misfit), never as a veto.

**F2 — For deck 27 (Blink), the deciding number is ETB-VALUE-PER-BLINK, and the blink
count is SEVEN of which FOUR reach artifacts.** *(Corrected in batch 1 — see E1. The rule
as written before batch 1 said "four, of which two"; both halves were wrong.)* The
artifact-capable blinkers are **Don & Leo** (end step, artifact + creature, repeatable),
**Wiccan, Rising Magician** (any nonland nontoken permanent, on every noncreature spell —
missed entirely in the pre-batch count), **The Mighty Thor, Jane Foster** (nontoken
artifact or creature, on attack) and **The Mind Stone** (any other nonland permanent, once
harnessed for {5}{W}). Y'shtola, Daydream and Niko are creature-only. An equipment earns a
27 slot if its ETB pays when re-triggered by those four, or if it is strong with no blink
synergy at all.

**F3 — A creature blink UNATTACHES its equipment, so an equipment package fights deck
27's engine (G-42 shape, stated in the reverse direction).** The creature returns as a new
object; the equipment falls off and must be re-equipped at full cost. Counting the number
that would be discarded before adding is the G-42 discipline. This is the strongest prior
argument that the equipment half belongs in a NEW deck rather than in 27.

**F4 — For a NEW equipment deck the deciding number is the EQUIP TAX, not card quality.**
An equipment is card disadvantage plus a per-body mana tax. A deck built on them needs one
of: attach-on-entry, `Equip {0}`/cheap equip, Reconfigure, attach-as-part-of-cast, or
payoffs that never require attaching (see F5). Grade every equipment on **how it gets onto
a body**, and say so.

**F5 — Count PAYOFFS before bodies (G-59, applied one type over).** G-59's measured lesson
is that a tribe's viability is its payoff count and body count decides nothing. An
equipment pile is the same shape: 22 equipment with three cards that care is a pile, not a
deck. Payoffs here are of three kinds and they are NOT interchangeable —
  (a) **counts** ("for each Equipment you control", affinity for Equipment — G-83's
      cost-scale family, floor 4 / key 10 / cap 12),
  (b) **triggers** ("whenever an Equipment enters / becomes attached"),
  (c) **free attachers** (which are payoff and enabler at once and are the scarcest).
Count each separately and write the three numbers down before declaring a thesis.

**F6 — Castability is read from the PRINTED COST, never from `Color(s)` (G-58).** The bulk
pull runs `deck._candidate_castability`, the same primitive `screen` uses. A hybrid or a
transform-derived identity is castable; never bin a card by its identity column. For the
pile as a whole, `deck.py screen` is run in addition (G-58 requires it over ~10 cards).

**F7 — Standard legality is checked IN the pull, not later.** Rotation is a legality fact
about the deck's FUTURE and is in scope (G-30). Craft cost is NOT a quality argument and is
reported as information at the end only (CLAUDE.md Player Profile, G-10).

**F8 — Grade the FACE YOU CAST.** A split / Room / Adventure / DFC's stored Mana Value is
the combined or front-face cost (G-02, G-43). Dirgur Island Dragon // Skimming Strike is
the one live instance in this pile.

**F9 — Never dismiss by category, and never dismiss on a zero-result literal search.**
"Fliers belong in the fliers deck" and "Equipment belongs in deck 38" are category
dismissals (Stage-2 rule 6). A pool sweep that returns zero is an unverified search, not a
fact about the format — search the EFFECT SHAPE, not the noun (K-13).

**F10 — A repeated rejection reason IS the variant signal.** If a coherent cluster keeps
falling out for the same reason, that cluster is the deck asking to be built (Stage-2 rule
7). Log it in §3; decide at the end, never mid-batch.

**F11 — Axes no tool here scores, so they must be read by hand:**
  - the **Equipment / attach bucket** earns role credit but is explicitly NEVER counted as
    interaction (G-67, 2026-09-06) — an equipment deck's interaction figure is honest;
  - **equip costs are invisible to the curve** — avg MV under-reads an equipment deck's
    real mana consumption in the same direction the `{X}` distortion runs (G-60);
  - **"drawn two or more cards this turn"**-style gates are G-76 STATE gates: free in a
    deck that draws every turn, dead in one that does not — report both ends;
  - `type_scale` (G-84) and `cost_scale` (G-83) primitives exist and are wired to
    `suggest-homes` / `cuts`; use them rather than eyeballing a count.

---

## 2. Live vector — deck 27 (Blink), measured 2026-09-10

Every later verdict about deck 27 is relative to these numbers.

| axis | value |
|---|---|
| claimed tier / metrics floor | B / B (consistent) |
| plan | midrange |
| interaction | 4 (+3? — Y'shtola, Don & Leo, Daydream read as interaction, untagged) |
| card advantage | 4 (3 repeatable, 1 one-shot; 2 unclassified) |
| protection | 1 |
| avg MV | 3.59 printed / 3.30 effective (6 cheat-cost cards) |
| central themes | 14 — DIFFUSE |
| shape | WIDE 14 / tall 0 — 32 creature copies, 9 evasive |
| interaction profile | 2 instant / 2 sorcery · **0 answers to a noncreature permanent** |
| gated effects | none |
| engines | tokens balanced (10/7); counters 13 enablers **no payoff**; lifegain 7 enablers **no payoff** |

Reading: 27's real deficits are **card advantage, protection, and noncreature answers** —
not bodies and not ETB density. An add that does not move one of those three is competing
against a deck that already does its job.

---

## 3. Cross-batch observations

### O1 — F5 measured: the WU equipment archetype HAS payoffs. 13-20 of them.

Pool sweep, Standard-legal and WU-castable by printed cost, equipment themselves excluded,
buckets non-exclusive (see E2):

| kind | n | cards |
|---|---|---|
| **(a) COUNT** — scale with equipment count | 7 | Adelbert Steiner {1}{W}, Beatrix {4}{W}{W}, Dwalin {1}{R/W} (hybrid, on-colour in W), Slash of Light {1}{W}, Vow to Erebor {1}{W}, Weapons Vendor {3}{W}, Super-Soldier Serum {1}{W} |
| **(b) TRIGGER** — on an Equipment entering / attaching | 2 | **The Mighty Thor, Jane Foster** {1}{W}{U}, **Kíli the Resourceful** {1}{W} |
| **(c) FREE ATTACH** — non-equipment | 4 | Super-Soldier Serum (mass attach on attack/block), Weapons Vendor ({1} each combat), **Cloud, Midgar Mercenary** {W}{W} (tutor + doubles equipment triggers), Sun-Spider {3}{W/U} (tutor) |
| **(d) MODIFIED** — count attachments as modifications | 4 | SP//dr {3}{W}{U}, Silver Sable {2}{W}, Skyward Spider {W/U}{W/U}, Costume Closet {1}{W} |

Against G-59's calibration (Dragon 20 payoffs = buildable as deck 49; Vampire 3 = not),
this clears the bar. **The archetype is buildable. That is not the same as it being needed
— see O2.**

**And the payoff half is almost entirely WHITE.** Every kind-(a) payoff is mono-W. Blue's
entire contribution to an equipment deck is Jane Foster, Assimilation Aegis, Biorganic
Carapace, SP//dr, Skyward Spider, Wizard's Staff, The Key to the Vault and Glamdring. So a
"UW equipment deck" is a WHITE equipment deck splashing blue, and the blue half has to
justify itself on card advantage, not on the equipment theme.

### O2 — THE ROSTER ALREADY HOLDS FOUR EQUIPMENT DECKS, and this is the finding that decides the question.

| deck | colors | note |
|---|---|---|
| **38 Armory** | **WB** | 23 Equipment/attach cards, 19 artifacts — the reference build |
| 39 Starforge | WR | |
| 74 Iron Hills Forge (+74a) | WR | |
| 26 Iron Forge (+26a, 26b) | UR | |

A UW equipment deck would be the **fourth W-based** equipment deck. `suggest-homes` puts
deck 38 or 39/74 first for almost every equipment in this pile, which is the theme model
saying the same thing. Distinctness (G-47 `similar`) is the live risk, not power.

### O3 — The 11 HOMELESS equipment are homeless for one reason: they are BLUE.

Assimilation Aegis, Thief's Knife, The Key to the Vault, Super Suit, Cursed Windbreaker,
Sage's Nouliths, Illvoi Light Jammer, Glamdring, Biorganic Carapace, The Dominion Bracelet,
Dissection Tools. Every equipment deck on the roster is W+B, W+R or U+R — **none is W+U**,
so a `{U}` or `{W}{U}` equipment has nowhere to go by construction. This is the honest
statement of the user's question: it is not "are these cards good", it is "is the empty
WU slot worth filling".

### O4 — VARIANT SIGNAL (F10), logged not decided.

Deck 27 already runs **Jane Foster**, whose second ability draws a card whenever an
Equipment enters, and runs **zero Equipment** (E3). It also runs four artifact-capable
blinkers. That is a UW equipment shell already half-present inside deck 27 — which is a
different proposal from a new deck, and cheaper. Decide at the end.


---

### O5 — THE SECOND PILE IS NOT AN EQUIPMENT PILE. It is a "draw your second card each turn" deck, and that is F10 firing.

Reading all 67 non-equipment cards, the repeated shape is not fliers and not artifacts — it
is **a trigger keyed on drawing more than once per turn**. In the pile alone: Kid Loki,
Lady Octopus, Lakeshore Apothecary, Knowledge Seeker, Mischievous Mystic, Master's
Councillors, Messenger Hawk, Clinquant Skymage, Ravenhill Flock, Astrologian's Planisphere,
Lake-town Toymaker — eleven, plus roughly forty more cards that exist to *cause* the extra
draw (eight Clue makers, five loot/tap-to-draw bodies, the cantrips, Vnwxt, Quantum
Riddler).

Pool sweep, Standard-legal and WU-castable, by effect shape (K-13 — the family never names
a number, so a literal search for "draw two" misses it):

- **21 payoffs.** Aether Syphon, Astrologian's Planisphere, Atlantean Cavalry, Bard the
  Bowman, Clinquant Skymage, Erudite Wizard, Homunculus Horde, Jaded Analyst, Kid Loki,
  Knowledge Seeker, Lady Octopus, Lake-town Toymaker, Lakeshore Apothecary, Master's
  Councillors, Messenger Hawk, Mischievous Mystic, Otter-Penguin, Private Eye, Ravenhill
  Flock, Thopter Fabricator, Tiger-Seal.
- **12 of those 21 are in NO deck on the roster.**
- **4 guaranteed enablers**: Scrawling Crawler {3}, Vnwxt {1}{U}, Friendly Teddy {2},
  Quantum Riddler {3}{U}{U}. This is the thin half, and it is the half that decides whether
  the deck functions (F5, kind-by-kind).

**Scrawling Crawler is the keystone and nothing else in these colours does its job.** Its
upkeep draw is your first card of the turn and your draw step is your second, so **every
"second card each turn" payoff fires every turn for free**, with no cards spent. It is
Foundations (FDN) — long legality, does not rotate. Its second line drains the opponent 1
per draw, which is the deck's only reach.

### O6 — Distinctness: the mechanic exists on the roster, in the wrong colours and the wrong plan.

`deck.py rotation`-style roster scan of the 27-card family: **deck 37 Wizardz (UBR)** holds
6 and its `#: archetype:` says outright "heavy card draw feeds 'draw your second card'
payoffs". Deck 43 (WUB hand-SIZE control) holds 5, deck 12 (UB draw control) 4.

So the mechanic is represented — as a **Grixis Wizard value/storm** deck. A WU build is a
different deck on every other axis (colours, tribe, plan, curve): fliers and Clue tokens
with a lifegain/tokens sub-theme, not a spell chain into copiers. G-47's rule applies —
theme similarity and card overlap are different questions, and the castable overlap with 37
is ~6 mono-U cards. **Some overlap is fine; state it rather than hide it.**

No WU deck and no mono-U deck on the roster runs this theme. 16 Moon Spirit is WU tempo,
27 Blink is WU ETB value, 51 Unlocked is mono-U Rooms control, 47 Grid Overload is mono-U
affinity — none of them draws twice a turn on purpose.

### O7 — The opponent-draw axis is real, is exactly three cards, and two are unowned.

Answering the question the pile raised at Gleaming Splendor. Pool sweep by effect shape for
"an opponent draws" — **5 Standard cards exist, 3 are WU-castable**:

| card | cost | text |
|---|---|---|
| **Gleaming Splendor** | {1}{W} | opponent's **second** card each turn → you create a Treasure. Plus `{2}{W}: two target players each draw a card` |
| **The Unagi of Kyoshi Island** | {3}{U}{U} | opponent's **second** card each turn → **you draw two cards**. Flash, ward—waterbend {4} |
| **Scrawling Crawler** | {3} | each opponent draw → they lose 1 life; upkeep: each player draws |
| *(off-colour)* Razorkin Needlehead {R}{R}, Mornsong Aria {1}{B}{B} | | |

These three interlock, and Gleaming Splendor's activated ability is what makes the axis an
engine rather than a hope: **{2}{W} gives BOTH players a card.** Used on the opponent's
turn after their draw step it is their second card — Splendor makes a Treasure, Unagi draws
you two, Scrawling Crawler drains them — and the two cards it hands you are your own second
draw, firing every payoff on their turn as well as yours.

**Honest cost:** Scrawling Crawler and Gleaming Splendor both give the opponent cards. Two
of the three are unowned. This is a build risk to state, not a reason to skip the axis.

### O8 — Rotation (G-30), on the proposed spine: 14 of 44 rotate this year or next.

Rotating: the whole **MKM Clue package** — Alquist Proft, Case of the Filched Falcon,
Curious Inquiry, Private Eye, Jaded Analyst — plus Assimilation Aegis, The Key to the
Vault, Cursed Windbreaker, Friendly Teddy, Mu Yanling, Thopter Fabricator, Vnwxt,
Astrologian's Planisphere, Thief's Knife. Safe: Scrawling Crawler (FDN), and the entire
TLA/MSH/HOB/SPM/EOE half including Gleaming Splendor, The Unagi, Ravenhill Flock,
Lakeshore Apothecary, Master's Councillors, Lake-town Toymaker, Bard the Bowman, Kid Loki,
Knowledge Seeker, Messenger Hawk, Air Nomad Legacy, Trusty Boomerang.

The deck's *core* survives rotation; its Clue half largely does not. Build the Clue package
as the replaceable layer.

## 4. Standing error list

**E1 — I claimed deck 27 held FOUR blink effects of which TWO reached artifacts. It holds
SEVEN of which FOUR do.** The miss was **Wiccan, Rising Magician** — "whenever you cast a
noncreature spell, exile another target nonland, nontoken permanent" is a repeatable
artifact blink triggered by every equipment cast, and I had not read it. Also miscounted:
Niko is a seventh blinker (creature-only). The error ran in the direction that *understated*
the case for equipment in 27, which is the harder kind to notice, because the conclusion it
supported ("build a separate deck") was the one I already expected.

**E2 — The first payoff sweep used mutually exclusive buckets with a `break`, and
mis-filed the single most important payoff.** "Equipment you control" appears in both the
COUNT and the TRIGGER templating, so `Whenever an Equipment you control enters, draw a
card` (Jane Foster) matched COUNT first and the TRIGGER bucket read **1**. Re-run
non-exclusively it reads 2 (Jane Foster, Kíli). A bucket count from a first-match loop is
not a count — this is the G-67 whitelist problem wearing a control-flow disguise.

**E3 — Deck 27 runs Jane Foster and ZERO Equipment, so half her text is dead right now.**
`deck.py targets 27` reports "No gated effects detected": a trigger with no possible source
in the list is exactly the G-75 dead-search shape one clause over, and nothing here sees
it. Logged for Stage 4.


---

## 5. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`

### Batch 1 — the 27 Equipment (all Standard-legal, all WU-castable)

`27` = fit for deck 27 Blink · `UW` = fit for a new UW equipment deck · homes = decks already running it

| card | cost | 27 | UW | read |
|---|---|:--:|:--:|---|
| **Assimilation Aegis** | {1}{W}{U} | ★★★ | ★★★ | ETB **exiles a creature** until it leaves — real removal, and all four artifact blinkers re-fire it. Attaching copies the exiled card. Triggers Jane Foster's draw. Fixes 27's biggest gap without being an equipment-theme card. |
| **Bespoke Bō** | {2}{U} | ★★★ | ★★ | ETB bounces **any nonland permanent**. Deck 27 has **0 answers to a noncreature permanent** (`stats` flags it); this is one, and it is repeatable through Wiccan/Don & Leo. Currently in deck 04. |
| **Trusty Boomerang** | {1} | ★★★ | ★★ | Equipped creature taps a creature for {1}, Boomerang **returns to hand** — recast it and Jane Foster / Kíli draw again. Repeatable tap-down is credited as interaction (G-67, 2026-08-19). In deck 38. |
| **Wizard's Staff** | {1}{U} | ★★ | ★★★ | **Doubles the equipped creature's triggered abilities.** On Cloudblazer that is draw 4 per blink. Equip {3} for a non-Wizard is the tax — Astrologian's Planisphere makes the carrier a Wizard, dropping it to {1}. In deck 57; `suggest-homes` rates 27 KEY. |
| **Cursed Windbreaker** | {2}{U} | ★★ | ★★ | ETB manifest dread **and attaches to that creature** — brings its own 2/2 flier and bins a card. Blink → another body. Self-contained (F4). |
| **Biorganic Carapace** | {2}{W}{U} | ★ | ★★★ | Combat damage → **draw a card for each modified creature you control**. The blue half's best argument: a real draw engine that only exists in an equipment deck. |
| **Falcon's Wing Harness** | {1}{U} | ★★ | ★★ | ETB attach; flying + **ward {1}**. Deck 27's protection axis is 1 and `stats`/`tier` both flag it. In deck 26. |
| **Illvoi Light Jammer** | {1}{U} | ★★ | ★★ | **Flash**, ETB attach + hexproof until EOT — a 2-mana counter-the-removal trick that then stays as +1/+2. Protection axis again. |
| **Thunder Lasso** | {2}{W} | ★★ | ★★ | ETB attach; attacks → tap a defender. Repeatable interaction, free to attach. In deck 38. |
| **Web-Shooters** | {1}{W} | ★★ | ★★ | +1/+1, reach, attacks → tap an opponent's creature. Same shape as Thunder Lasso, cheaper, Equip {2}. In 38/39. |
| **Sword of Wealth and Power** | {3} | ★★ | ★★ | +2/+2 and **protection from instants and sorceries** — which is most removal. Damage → Treasure + copy your next instant/sorcery. In deck 54. |
| **Mirrormind Crown** | {4} | ★★ | ★ | First tokens each turn instead enter as **copies of the equipped creature**. In deck 27 (7 token makers, Cloudblazer/Beza ETBs) that is a bomb, but 4 + equip 2 = 6 mana and a creature blink knocks it off (F3). In deck 38. |
| **Glider Staff** | {2}{W} | ★★ | ★ | ETB airbend (exile; they may recast for {2}) — soft removal, re-triggerable. In 15/38. |
| **Thief's Knife** | {2}{U} | ★★ | ★★ | Job select: brings its own 1/1 Hero and attaches. Combat damage → draw. Blink → a second Hero token. Equip {4} is steep, but you never pay it. |
| **Astrologian's Planisphere** | {1}{U} | ★ | ★★ | Job select; carrier becomes a **Wizard** (enabling Wizard's Staff's Equip {1}) and grows on noncreature spells and on your third draw each turn. In deck 37. |
| **Atomic Microsizer** | {U} | ★ | ★★ | 1 mana. Attacks → a creature **can't be blocked and becomes base 1/1** — evasion plus a genuine shrink effect. In deck 26. |
| **The Key to the Vault** | {1}{U} | ★ | ★★ | Combat damage → impulse-dig that many and cast one free. Needs an evasive carrier; 27 has 9 evasive bodies. Equip {2}{U}. |
| **Super Suit** | {1}{U} | ◇ | ★★ | Flash, ETB attach **and untaps** the creature — a pseudo-vigilance ambush. Free attach (F4); the body it makes is nothing on its own. |
| **White Mage's Staff** | {1}{W} | ★ | ★ | Job select; +1/+1, attacks → gain 1. 27 has 7 lifegain enablers and **no lifegain payoff**, so the lifegain is incidental; the free 1/1 is the value. In deck 03. |
| **Dragoon's Lance** | {1}{W} | ★ | ★ | Job select; Knight, flying on your turn. **Equip {4}** — it is a 1/1 flier for 2 and nothing more. In deck 38. |
| **Orcrist, Goblin-cleaver** | {3} | ★ | ◇ | +2/+2 trample; damage → choose a type, Treasure per creature of it (G-84). `suggest-homes` reads deck 27's best type at a middling count; it belongs in 39/74 (dwarf 18) where it already is. |
| **Sage's Nouliths** | {1}{U} | △ | ◇ | Job select; +1/+0 and untap an attacker. The token is the card. |
| **Fishing Pole** | {1} | ◇ | ◇ | Bait-counter loop makes 1/1 Fish only when the equipped creature **untaps** — slow, and it wants a tapper. In deck 73. |
| **Dissection Tools** | {5} | ◇ | △ | ETB manifest dread + attach, deathtouch + lifelink. Five mana, and **Equip—Sacrifice a creature** is a real cost in a deck with no sacrifice payoff. |
| **Bark of Doran** | {1}{W} | ✗ | △ | Damage = toughness. Needs a high-toughness body; neither deck has one. In deck 20. |
| **The Dominion Bracelet** | {2} | ✗ | △ | The {15}-minus-power mode is a gimmick; +1/+1 for 2 with Equip {1} is filler. |
| **Glamdring, Foe-hammer** | {2} // {3}{U} | ✗ | ✗ | Instants/sorceries cost {X} less where X = equipped power (F8: the adventure half is the {3}{U} mill-six). Deck 27 runs ~4 noncreature spells and a UW equipment deck would run few — the discount has nothing to discount. |


---

### Batches 2-3 — the 67 non-equipment cards (all Standard-legal, all WU-castable)

`27` = deck 27 Blink · `NEW` = the proposed WU draw deck (O5)

**The draw-matters spine** — these are the deck.

| card | cost | 27 | NEW | read |
|---|---|:--:|:--:|---|
| **Scrawling Crawler** | {3} | ◇ | ★★★ | *(not in the pile — surfaced by the O7 sweep, unowned)* Upkeep "each player draws" makes your draw step your SECOND card **every turn**, free. FDN, does not rotate. The keystone. |
| **The Unagi of Kyoshi Island** | {3}{U}{U} | ✗ | ★★★ | *(not in the pile, unowned)* Opponent's second draw → **you draw two**. Flash + ward. |
| **Gleaming Splendor** | {1}{W} | ✗ | ★★★ | The `{2}{W}` is the engine, not the Treasure: it hands both players a card on demand, turning on your payoffs on the OPPONENT'S turn too. |
| **Kid Loki** | {U} | ◇ | ★★★ | One mana. Second card → counter; and every creature you countered this turn has **hexproof** — the protection axis a draw deck otherwise lacks. |
| **Lady Octopus, Inspired Inventor** | {U} | ◇ | ★★★ | First *or* second card each turn → ingenuity counter; tap to cast an artifact free at that MV. With a Clue package this casts real cards by turn 5. |
| **Lakeshore Apothecary** | {1}{U} | ◇ | ★★ | Vigilant 2-drop that grows every turn Scrawling Crawler is out. Unowned, HOB, no rotation. |
| **Knowledge Seeker** | {1}{U} | ◇ | ★★ | Grows on the second draw **and** replaces itself with a Clue when it dies. |
| **Mischievous Mystic** | {1}{U} | ◇ | ★★★ | Second draw → a 1/1 **flier** every turn. The token half of the plan and the best payoff at 2 mana. |
| **Master's Councillors** | {1}{U} | ✗ | ★★ | Second draw → mill 3, and +2/+0 per seven-card graveyard — it mills itself into a threat. Unowned, HOB. |
| **Ravenhill Flock** | {3}{U} | ◇ | ★★ | Grows on **every** draw, not just the second — the payoff that scales with the whole engine. 4 mana for a 2/2-ish body is the cost. **Craft answer: yes, but only into this deck** — `suggest-homes` finds no current home, and it is unowned and unplaced precisely because no roster deck draws repeatedly. |
| **Clinquant Skymage** | {3}{U} | ◇ | ★★ | Same trigger as Ravenhill Flock, already owned, already in deck 37. |
| **Astrologian's Planisphere** | {1}{U} | ★ | ★★ | Third card each turn + noncreature spells; and it makes the carrier a **Wizard**, which is Wizard's Staff's Equip {1}. ⚠ rotates. |
| **Messenger Hawk** | {2}{U/B} | ◇ | ★★ | Hybrid, on-colour in U (G-58). ETB Clue **and** +2/+0 once you have drawn two — enabler and payoff in one card. |
| **Lake-town Toymaker** | {3}{W} | ✗ | ★★ | A G-76 state gate: dead in most decks, **unconditional here**. |
| **Vnwxt, Verbose Host** | {1}{U} | ✗ | ★★ | Max speed doubles every draw. Getting to max speed needs the opponent to lose life on four of your turns — Scrawling Crawler does that by itself. ⚠ rotates. |
| **Quantum Riddler** | {3}{U}{U} | ★ | ★ | Draw +1 only while your hand is **one or fewer**, which fights a draw deck's own plan (G-42 shape). ETB draw + Warp {1}{U} are the real text. |

**The Clue / extra-draw layer** — each Clue is one on-demand second draw.

| card | cost | 27 | NEW | read |
|---|---|:--:|:--:|---|
| **Air Nomad Legacy** | {W}{U} | ★ | ★★★ | ETB Clue **and** a flying anthem — both halves of the deck in one 2-drop. Currently deck 15. |
| **The Mechanist, Aerial Artisan** | {2}{U} | ★ | ★★★ | A Clue on **every noncreature spell**, and it turns an artifact token into a 3/1 flier — Clues become a clock. |
| **Agent 13, Sharon Carter** | {2}{W} | ✗ | ★ | Investigates only when a creature **attacks alone**, which fights the go-wide flier plan (G-42). Unowned. |
| **Case of the Filched Falcon** | {U} | ◇ | ★★ | ETB Clue; solves on three artifacts (Clues count); solved, it makes a 4/4 flying artifact. ⚠ rotates. |
| **Curious Inquiry** | {U} | ✗ | ★ | A one-mana Aura that investigates on damage. Card disadvantage if they kill the creature. ⚠ rotates. |
| **Alquist Proft, Master Sleuth** | {1}{W}{U} | ★ | ★★ | ETB Clue plus an X-draw-and-gain sink. The deck's mana sink. ⚠ rotates, unowned. |
| **Cryogen Relic** | {1}{U} | ★★★ | ★★ | **Draws on enter AND on leave.** In deck 27 that is two cards per blink from a 2-mana artifact, on the axis `stats` says 27 is weakest (card advantage 4). Best single non-equipment add for 27 in the whole pile. |
| **Esoteric Duplicator** | {2}{U} | ◇ | ★ | A Clue that copies artifacts you sacrifice — Clue-into-Clue. Slow. |
| **Kitsa, Otterball Elite** | {1}{U} | ✗ | ★★ | `{T}: loot` is a repeatable second draw on a 2-drop body. |
| **Mechan Navigator** | {1}{U} | ✗ | ★ | Loots whenever it becomes **tapped** — needs a tap outlet; Fishing Pole and Trusty Boomerang are two. |
| **Unstable Experiment** / **Enter the Enigma** / **I Am Iron Man** / **Confusticate and Bebother** | {1}{U} / {U} / {2}{U} / {2}{U} | ◇ | ★★ / ★ / ★ / ★★ | Cantrips — the cheap second draws. Confusticate is modal (counter-or-draw-two) and is the best of them. |
| **Moonlit Lamenter** | {2}{W} | ✗ | ◇ | A slow repeatable draw off its own -1/-1 counter; only two activations. |
| **Uncover the Moon-Letters** | {3}{U} | ✗ | ◇ | Draws X = **mana spent**, not mana value (framework: gates read different numbers) — wrong axis for a cheap deck, and discarding two is steep. |

**Fliers and combat-damage draw** — the body of the deck.

| card | cost | 27 | NEW | read |
|---|---|:--:|:--:|---|
| **Mu Yanling, Wind Rider** | {2}{U}{U} | ★ | ★★★ | Makes a Vehicle, gives Vehicles flying, and **draws whenever your fliers connect**. ⚠ rotates. |
| **Teo, Spirited Glider** | {3}{U} | ★ | ★★ | Fliers attack → loot + a counter. Second draw on your own attack step. |
| **Sunpearl Kirin** | {1}{W} | ★★ | ★★ | Flash flier; ETB bounces your own permanent and **draws if it was a token** — a Clue or a Faerie becomes a card. Re-triggerable by 27's blinkers. |
| **Beast, Erudite Aerialist** | {3}{G/U} | ◇ | ★ | Hybrid, on-colour in U. Draws on damage but needs a +1/+1 counter that turn to fly. |
| **Ray Fillet, Man Ray** | {3}{U} | ◇ | ★ | Flier; converts +1/+1 counters into draws for {2}. |
| **Kastral, the Windcrested** | {3}{W}{U} | ✗ | ◇ | Modal Bird payoff — needs a Bird count the deck does not have (F5/G-59). Deck 19 is its home. |
| **Drogskol Reaver** | {5}{W}{U} | ✗ | ◇ | Seven mana. Draw-on-lifegain is a real engine but this deck is not a lifegain deck. |
| **Dirgur Island Dragon** | {5}{U} // {1}{U} | ◇ | ★ | F8 — grade the **Omen half**, `{1}{U}` tap + draw. That half is the card; the 6-drop is a late-game mode. |
| **Marang River Regent** | {4}{U}{U} // {3}{U} | ★★ | ★ | Same shape: the `{3}{U}` Omen draws three. The creature half's ETB double-bounce is what deck 27 wants. |
| **Overlord of the Floodpits** | {3}{U}{U} | ★ | ★★ | Impending {1}{U}{U}; draws two on **enter or attack** — an enchantment on turn 3 that becomes a flier. Already in 43/51/67. |
| **Wan Shi Tong, Librarian** | {X}{U}{U} | ★ | ★ | Flash flier, X counters + X/2 draws. In seven decks already. |
| **Glen Elendra Guardian** | {2}{U} | ★★ | ★★ | Flash flying **counterspell** on a body — 27's interaction is 4 and this is instant-speed and answers a **noncreature** permanent's spell. |
| **Spider-UK** | {3}{W} | ★★ | ★ | "Two or more creatures entered this turn → draw + gain 2" is near-unconditional in deck 27 (WIDE 14, 32 creature copies). Web-slinging {2}{W} rebuys an ETB. Unowned. |
| **Enduring Innocence** | {1}{W}{W} | ★★ | ★ | Draws on a small creature entering, once a turn, and **returns itself when it dies**. Deck 27's card advantage is 4; this is a repeatable source that survives a wipe. |
| **Haliya, Guided by Light** | {2}{W} | ★★ | ★ | Gains 1 on **every creature or artifact** entering and draws at end step at 3 life gained. In deck 27 (WIDE, 7 lifegain enablers and **no lifegain payoff** per `engines`) it is the payoff that engine is missing. |
| **Belladonna Took** | {1}{W} | ★★ | ★★ | Escalating token payoff: gain 1 → draw → **counter on every creature**. Deck 27 makes tokens from 10 sources. |
| **G'raha Tia** | {4}{W} | ◇ | ★ | **Yes — Clues and Treasures count.** A token put into a graveyard has *died*; the dies-trigger resolves before it ceases to exist. So cracking a Clue draws you an extra card. Once per turn, and five mana for that is the problem, not the rules question. |
| **Sunstar Lightsmith** | {3}{W} | ◇ | ★ | Second **spell** each turn, not second card — a different number (framework F-rule on which gate reads which). Four mana. |
| **Viv Vision** / **The Vision** / **Iron Lad** / **H.E.R.B.I.E.** | {3} / {4} / {2}{U} / {4} | ◇ | ★ / ◇ / ★ / ◇ | Artifact-creature fliers that draw. Iron Lad is the best (1-mana-ish repeatable draw off artifact topdecks, and Clues make the top artifact-dense). The Vision wants a spell density this deck does not have. |
| **Yue, the Moon Spirit** / **Katara, Bending Prodigy** / **Waterbender Ascension** / **Elrond, Moon-Reader** | | ✗ | ◇ | Waterbend and activate-an-ability payoffs — a coherent cluster that belongs to decks 16/22/35, not here. Elrond's once-a-turn draw off an **activated ability** is live if the deck runs tappers. |
| **Moonlit Meditation** | {2}{U} | ★ | ◇ | **Answering the Fishing Pole question directly:** it copies the enchanted permanent the first time you make tokens each turn, so with Fishing Pole you get one copy of your best creature per untap — but that is a **three-card** setup (Pole + Meditation + an untapper) for an effect Mirrormind Crown does in two. Its real partners are the Clue makers: an ETB-Clue becomes a copy of your bomb. Still a build-around, not a role-player. |
| **Fractal Anomaly** / **Super Intelligence** | {U} / {U} | ✗ | ★ / ◇ | Fractal Anomaly scales with cards drawn **this turn** — a real payoff at instant speed. Super Intelligence is a symmetric Aura; the draw goes to the enchanted creature's controller, so it is a **gift** unless you enchant your own. |
| **The Legend of Yangchen** | {3}{W}{W} | ★ | ◇ | Chapter II is a symmetric draw-three that turns on every opponent-draw payoff at once — but a 5-mana Saga is a different deck's card. Decks 15/16 own it. |
| **The Arkenstone** | {5} // {2}{W} | ✗ | ◇ | End-step draw + anthem for five. F8: the {2}{W} adventure tutors a legend. Deck 68's. |


## 6. Consolidated plan (live)

### The answer, in three parts

**(1) Do NOT build a UW *equipment* deck.** Not on power — the archetype clears G-59's
buildability bar (O1) — but on need. The roster already holds **four** equipment decks
(38 WB, 39 WR, 74 WR, 26 UR), every kind-(a) equipment payoff in these colours is **mono-
white** and already sits in 38, and `suggest-homes` puts 38/39/74 first for nearly every
equipment in this pile. A UW build would be the fourth W-based one. The 11 blue equipment
are homeless because **no equipment deck is W+U** (O3), which is a gap in the colour grid,
not a deck-shaped hole.

**(2) DO build a new deck — on the second pile's actual theme: `WU — draw your second card
each turn`.** 21 Standard WU-castable payoffs, **12 of them in no deck at all**; the
mechanic exists on the roster only as **Grixis Wizard storm (37)**, so a WU fliers-and-
Clues build is distinct in colours, tribe, plan and curve (O5, O6). Roughly **60 of the 67**
second-pile cards feed it. This is F10 firing exactly as the rule predicts: the cluster
that kept getting rejected for the same reason was the deck asking to be built.

**(3) Put the genuinely-blue equipment into deck 27, not into a new deck.** Deck 27 already
runs **The Mighty Thor, Jane Foster**, whose "whenever an Equipment you control enters,
draw a card" is **dead right now** — the deck runs zero Equipment (E3). Four artifact-
capable blinkers re-fire equipment ETBs (F2). Six equipment turn that trigger on and fix
27's three measured deficits at once.

---

### A. New deck — `WU Second Draw` (proposal for `/draft-deck`)

**Thesis:** draw twice every turn as a matter of course, and turn each extra draw into a
board. **Not** a control deck: the payoffs are 1- and 2-drops that grow, so it curves out.

**The engine (the part that must be right):**
- **Scrawling Crawler** {3} — upkeep "each player draws" makes your draw step your *second*
  card every turn, for free. FDN, no rotation. **Unowned.** Nothing else in WU does this.
- **Gleaming Splendor** {1}{W} — `{2}{W}: two players each draw` is a repeatable on-demand
  second draw for BOTH sides, plus a Treasure on their second draw. **Owned.**
- **The Unagi of Kyoshi Island** {3}{U}{U} — their second draw → you draw two. Flash + ward.
  **Unowned.**
- **Vnwxt, Verbose Host** {1}{U} — max speed doubles every draw; Scrawling Crawler's drain
  gets you there. ⚠ rotates.

**Payoffs, cheapest first:** Kid Loki {U} (+ hexproof), Lady Octopus {U}, Tiger-Seal {U},
Jaded Analyst {1}{U}⚠, Lakeshore Apothecary {1}{U}, Knowledge Seeker {1}{U}, **Mischievous
Mystic {1}{U}** (a flier every turn), Master's Councillors {1}{U}, Atlantean Cavalry
{2}{U}, Erudite Wizard {2}{U}, Thopter Fabricator {2}{U}⚠, Bard the Bowman {1}{W}{U},
Private Eye {1}{W}{U}⚠, Messenger Hawk {2}{U/B}, Clinquant Skymage {3}{U}, Ravenhill Flock
{3}{U}, Lake-town Toymaker {3}{W}.

**Clue layer (each = one on-demand second draw):** Air Nomad Legacy {W}{U} (Clue + flying
anthem — the single best 2-drop for this deck), The Mechanist {2}{U}, Case of the Filched
Falcon {U}⚠, Alquist Proft {1}{W}{U}⚠, Curious Inquiry {U}⚠, Messenger Hawk.

**Fliers / finishers:** Mu Yanling, Wind Rider {2}{U}{U}⚠, Teo {3}{U}, Overlord of the
Floodpits {3}{U}{U} (impending {1}{U}{U}), Sunpearl Kirin {1}{W}, Glen Elendra Guardian
{2}{U} (the interaction), Wan Shi Tong {X}{U}{U}.

**Build risks to state up front, not discover later:**
1. **You are giving the opponent cards.** Scrawling Crawler and Gleaming Splendor both do.
   Against a deck that uses them better than you, that is the loss.
2. **Rotation splits the deck** (O8): the core (Scrawling Crawler FDN + the whole HOB/TLA/
   MSH half) survives; the **MKM Clue package rotates**. Build the Clues as the replaceable
   layer, not the spine.
3. **The interaction axis will grade low.** A draw-payoff deck's removal comes from
   `suggest --needs/--interaction`, never from theme-`suggest` (G-38).
4. **Two of the three engine pieces are unowned.** Reported as information (G-10), not as a
   design constraint — the list above is the optimal list regardless.

### B. Deck 27 Blink — the equipment adds, ranked

Deck 27's measured deficits (§2): **card advantage 4, protection 1, ZERO answers to a
noncreature permanent.** Everything below is chosen against those three, not against the
equipment theme.

| # | add | cost | fixes | why the cut is safe |
|---|---|---|---|---|
| 1 | **Cryogen Relic** | {1}{U} | card advantage | Draws on enter **and leave** — two cards per blink from a 2-mana artifact, and all four artifact blinkers hit it. Also a stun-counter sac mode. Owned. |
| 2 | **Bespoke Bō** | {2}{U} | **noncreature answer** | ETB bounces any nonland permanent, repeatable through Wiccan/Don & Leo. Closes the hole `stats` flags. Owned (deck 04 — copies are shared, F1). |
| 3 | **Assimilation Aegis** | {1}{W}{U} | interaction | ETB exiles a creature and it stays gone; attaching copies it. Turns on Jane Foster. Owned. ⚠ rotates. |
| 4 | **Trusty Boomerang** | {1} | interaction + card adv | Tap a creature for {1}, Boomerang returns to hand, recast → **Jane Foster draws again**. A repeatable draw+tap loop for two 1-mana casts. Owned (deck 38). |
| 5 | **Glen Elendra Guardian** | {2}{U} | interaction (instant) | Flash flying body that counters a noncreature spell. 27 has 2 instant-speed pieces. Owned. |
| 6 | **Haliya, Guided by Light** | {2}{W} | card advantage | `engines` reports 7 lifegain enablers and **no lifegain payoff**; Haliya is that payoff, and every creature/artifact entering feeds her. Owned. |
| 7 | **Belladonna Took** | {1}{W} | card advantage | Escalating payoff off 10 token sources. Owned. |
| 8 | **Falcon's Wing Harness** | {1}{U} | **protection** | ETB attach; ward {1} on 27's key creature. Protection is 1. Owned (deck 26). |
| 9 | **Illvoi Light Jammer** | {1}{U} | **protection** | Flash + hexproof until EOT for {1}{U} — counters a removal spell, then stays. |
| 10 | **Cursed Windbreaker** | {2}{U} | bodies + card adv | Brings its own 2/2 flier; blink → another. ⚠ rotates. |
| — | **Enduring Innocence** | {1}{W}{W} | card advantage | Non-equipment alternative to 8-10 if the equipment count stays low; recurs itself after a wipe. Owned. |

**Do NOT add to deck 27, despite looking right:**
- **Wizard's Staff.** `screen` labels it `✱ multiplier — doubles triggers (32 feeders here)`
  and it is the highest-density doubler in the pile — but it doubles the **equipped
  creature's** triggers, and **every blink unattaches it** (F3). The one deck whose engine
  it appears built for is the one deck that structurally cannot keep it attached. This is
  the G-42 shape and the tool cannot see it. Its homes are 57 (already there), 37/37a.
- **Mirrormind Crown.** Same unattach problem, plus 4 mana + equip {2}.
- **Moonlit Meditation.** Does what Mirrormind Crown does for 2 less and with no equip cost
  — if a token-copy effect goes into 27 at all, this is the one. Still a build-around.

### C. PROTECT list — what the rankings structurally cannot see

If any of these sort to the top of a `cuts` list, that is the ranking failing, not the card:
- **Jane Foster (deck 27)** — she is the *reason* the equipment adds work; `cuts` scores
  theme fit and cannot see that she converts an entire card class into cantrips.
- **Scrawling Crawler (new deck)** — a 3-mana 1/4-ish body with no theme tags. Its whole
  value is that it makes every other card's trigger free, and `cuts`' fit term is gated on
  derived tags (K-04), which it has almost none of.
- **Gleaming Splendor (new deck)** — its activated ability is the engine; the ranking reads
  the static Treasure line.
- **Air Nomad Legacy (new deck)** — a 2-mana enchantment doing two jobs, neither tagged.

### D. Craft cost — INFORMATION ONLY, at the end, per the Player Profile

Unowned in the plan above: **Scrawling Crawler** (R), **The Unagi of Kyoshi Island** (R),
**Ravenhill Flock** (U), **Lakeshore Apothecary** (C), **Master's Councillors** (U),
**Jaded Analyst / Private Eye / Otter-Penguin / Tiger-Seal / Atlantean Cavalry / Erudite
Wizard / Homunculus Horde / Thopter Fabricator / Bard the Bowman** (mixed C/U/R),
**Alquist Proft** (M), **Case of the Filched Falcon / Curious Inquiry** (U), **Lake-town
Toymaker / Agent 13 / Spider-UK / Cursed Windbreaker / Thief's Knife / The Key to the
Vault** (U/R). Sequencing note only: **Scrawling Crawler first** — nothing else in the list
changes as many cards' behaviour.

### E. Not resolved here

- Whether to also spin a **`38a` UW variant** of Armory rather than a new deck. Cheaper in
  roster terms, but it inherits 38's white payoff shell and does not use the draw theme —
  which is where these blue cards actually want to be. Named so it is a decision, not an
  omission.
