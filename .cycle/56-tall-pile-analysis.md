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

## 3. Cross-batch observations

(empty — batch 1 pending)

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

## 5. Consolidated plan (live)

Carried in from `/tune-deck 56` pending the pile (see header). Re-ranked after each batch.
