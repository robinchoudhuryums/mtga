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
count is FOUR of which only TWO reach artifacts.** Jane Foster and The Mind Stone are the
artifact-capable blinkers (both repeatable); Y'shtola and Daydream are creature-only. So an
equipment earns a 27 slot only if (a) it has an ETB those two can re-trigger, or (b) it is
strong with no blink synergy at all. Do not credit a blink deck for equipment generally.

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

*(filled as batches complete)*

---

## 4. Standing error list

*(every misreading, so batch N+1 does not repeat it)*

---

## 5. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`

---

## 6. Consolidated plan (live)

*(per deck: tiered ADDS with reasoning, CUTS with reasoning, and a PROTECT list naming
what the ranking structurally cannot see)*
