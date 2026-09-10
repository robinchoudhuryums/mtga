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

## 6. Consolidated plan (live)

*(per deck: tiered ADDS with reasoning, CUTS with reasoning, and a PROTECT list naming
what the ranking structurally cannot see)*
