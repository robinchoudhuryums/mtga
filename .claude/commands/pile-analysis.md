Work a LARGE card pile (roughly 60+ cards) against one or more decks, in batches,
keeping a running analysis doc that survives context loss.

Input: a pile dump (Arena export lines, or bare names) plus the deck(s) it is aimed at,
in $ARGUMENTS or the user's latest message.

**Use `/add-cards` instead for a small pile of owned cards you just want placed** — that
is a one-pass fit check across the roster and it is finished in a single reply. This
command is for the case `/add-cards` handles badly: a pile too big to hold in one
context, aimed at a specific deck or deck family, where the answer is a *ranked swap
plan* and possibly a *new variant deck* rather than a list of homes.

It exists because that job was done once by hand and the expensive failures were all
process failures, not card-reading failures:

- the first pass graded every card on its **hard-cast rate**, which was the wrong number
  for those decks — and nothing caught it for 200+ cards;
- the session **compacted mid-analysis**, and only the parts written to disk survived;
- the same misreadings recurred batch after batch because nothing recorded them;
- three cards were dismissed by **category** ("landfall payoffs") rather than by text,
  and half of them were not payoffs at all.

This skill **orchestrates the existing scripts** and never re-implements them. Read
CLAUDE.md's Common Gotchas first — G-59 and G-61 (count before you decide), G-58
(identity is not castability), G-02/G-43/G-63 (front face vs stored metadata), G-42
(a card that fights your own engine), and G-67 (a pattern set is a whitelist).

---

## Stage 0 — Set up the working doc, before reading a single card

**Deduplicate the pile against every existing deck first.** A pile aimed at deck N is
usually 20–30% cards deck N already runs, and grading those is pure waste.

```
python3 - <<'PY'
import sys, os, re
sys.path.insert(0, "scripts"); import deck as D
pile = [l.strip() for l in open("<pile file>") if l.strip()]
names = [m.group(1).strip() for l in pile
         if (m := re.match(r"^\d+\s+(.+?)(?:\s+\([A-Z0-9]{2,5}\)\s*\d+)?$", l))]
inuse = set()
for p in __import__("glob").glob("decks/*/*.txt"):
    try: _m, cards = D.parse_deck_file(p)
    except Exception: continue
    inuse |= {n for _q, n, _s, _c in cards}
seen, rem = set(), []
for n in names:
    if n in seen: continue
    seen.add(n)
    if n not in inuse: rem.append(n)
print(f"{len(names)} lines / {len(seen)} distinct / {len(seen)-len(rem)} already in decks "
      f"-> {len(rem)} to evaluate")
open("<scratchpad>/pile-remaining.txt", "w").write("\n".join(rem))
PY
```

Then create `.cycle/<pile-name>-analysis.md` with the skeleton in **Stage 5**, marked
`TEMPORARY`, and **commit it before batch 1**. The commit is the point: a doc that only
exists in chat does not survive compaction, and this process reliably outlives one
context window.

## Stage 1 — Write the FRAMEWORK before batch 1. Do not skip this.

**This is the step whose absence caused the original re-do.** Before grading anything,
write a section that answers: *for THESE decks, what number actually decides a card?*

The first pass through one pile graded on hard-cast rate. The decks in question cast
their expensive spells from the graveyard for a flat `{1}`, so printed cost was close to
irrelevant — and roughly two hundred cards were graded against the wrong axis before
anyone noticed. The framework is what makes batch 1 and batch 6 comparable.

Ask, and write down:

- **What does this deck pay for a card, versus what is printed on it?** Cost reducers,
  alternative costs, recursion and cheat effects all break the printed number. If two
  decks in the family pay differently, that difference IS the framework.
- **Which gates read a number, and which number?** "Mana **value**" and "mana **spent**"
  select opposite card pools. So do "cards in your graveyard" and "cards you've drawn".
- **What does the deck already have too much of?** Run `deck.py stats`, `engines`,
  `shape`, `targets` and `tier` once, now, and record the live vector in the doc. Every
  later verdict is relative to those numbers.
- **What is structurally invisible?** Note the axes no tool scores — G-67's whitelist
  problem, unindexed keywords (K-01), themes with no tag.

Record it as numbered rules. Later batches cite them by number, which is what keeps a
six-batch analysis internally consistent.

## Stage 2 — Batch at 30, and read the FULL text of every card

Thirty is the working size: small enough to read completely, large enough that patterns
across the batch become visible.

**Bulk-pull complete oracle text. Never grade from a summary, a tag list, or memory.**

```
PYTHONPATH=scripts python3 - <<'PY'
import csv
import deck as dk
from lib import card_colors
names = [...]   # this batch
pool = {r['Card Name']: r for r in csv.DictReader(open('card-pool.csv'))}
mana = {r['Card Name']: r for r in csv.DictReader(open('card-mana.csv'))}
lib  = {}
for r in csv.DictReader(open('card-library.csv')):
    lib[r['Card Name']] = lib.get(r['Card Name'], 0) + int(r.get('Quantity Owned') or 0)
for n in names:
    p = pool.get(n)
    if not p:
        print(f"\n### {n} -- NOT FOUND", [k for k in pool if n.split(',')[0].lower() in k.lower()][:3]); continue
    m = mana.get(n, {}); ci = card_colors(p.get('Color(s)', ''))
    # CASTABILITY FROM THE PRINTED COST, never from `Color(s)` (G-58). This line used to
    # read `ci <= set("<deck colors>")` and print ✗OFF — the exact identity-subset triage
    # G-58 records mis-binning 9 of a 111-card pile, 8 of them castable, INSIDE the skill
    # that tells you not to do it two paragraphs down (BS8-25).
    cast_ok, note = dk._candidate_castability(m.get('Mana Cost', ''), ci, set("<deck colors>"))
    ok = "✓" if cast_ok else "✗OFF " + "".join(sorted(ci))
    if cast_ok and note: ok += "  (" + note + ")"
    std = "" if 'standard' in (p.get('Legalities') or '') else "  !!NOT-STANDARD"
    print(f"\n### {n}  {m.get('Mana Cost','?')}  MV {m.get('Mana Value','?')}  "
          f"{p.get('Rarity','')[:1]} own={lib.get(n,0)}  {ok}{std}")
    print(f"    [{p.get('Type','')}]")
    for line in (p.get('Card Text','') or '').split("\n"): print(f"    {line}")
PY
```

Notes on that pull, each of which cost something the first time:

- **A name that does not resolve is a name to fix, not a card to skip.** Split, Adventure,
  Room and DFC cards live under `Front // Back`; the near-match list is there so a typo
  ("Photoon Blast Barrage") gets corrected rather than dropped.
- **Check Standard legality in the pull, not later.** One candidate was graded, ranked and
  written into a plan before anyone noticed it had rotated.
- **The printed MV of a split/Room card is the COMBINED cost** (G-02). Grade the face you
  cast (G-43).
- **Off-colour by IDENTITY is not off-colour by CAST COST** (G-58). A card whose colour
  comes from a transform ability or a mana ability is castable; `deck.py screen <id>` and
  `preflight` are the arbiters, not the `Color(s)` column. The pull above reads the cost
  through `deck._candidate_castability` — the same primitive `screen` uses — so this note
  and the code now agree. **For a pile over ~10 cards run `deck.py screen <id> <names…>`
  anyway**: it applies the deck's format, the strict-upgrade test and the KEY-saturation
  warning, none of which this pull has.

### Grading rules for the batch

1. **Cite the framework rule by number** for anything you accept or reject on cost.
2. **Count before you dismiss** (G-61, G-59). "Too narrow" is a claim about a number in
   the deck list — state the number. "This tribe has no payoffs" is a claim about the
   pool — search the *effect shape*, not the noun (K-13), because a zero-result literal
   search is an unverified search, not a fact.
3. **Grade the ability that PAYS, not the one that is broken.** Four cards were rejected
   in one pass on a clause that did not fire, while their unconditional mana or copy
   ability went unread.
4. **Read the trigger's cadence.** "Once per turn" and "once per attacking creature per
   combat" are different cards.
5. **Look for the G-42 shape in reverse** — a strong card that fights your own engine.
   Two of the best-looking cards in one pile exiled the graveyard the deck ran on.
6. **Never dismiss by category.** "Landfall payoffs belong in a landfall deck" swept out
   six cards in one line; three of them were not payoffs at all but *recovery* for a cost
   that deck's own engine imposed.
7. **Watch for variant-deck signals.** If a coherent cluster keeps getting rejected for
   the *same* reason ("wants to attack", "wants mana spent"), that is not noise — it is a
   different deck asking to be built. Note it in Cross-batch observations; decide at the
   end, not mid-batch.

## Stage 3 — Update the doc, then COMMIT, after every batch

Add the batch's verdict table, fold anything new into the standing error list and the
cross-batch observations, and **re-rank the consolidated plan** — it is a live answer, not
an append-only log.

Then commit. Per batch, not per session. This is the whole reason the process survives.

## Stage 4 — When a number looks wrong, suspect the tooling (G-67)

A dense read of 150+ cards is the most reliable classifier-hole detector this project has;
one pass surfaced **eight** holes, every one found by a human noticing a figure did not
match a card that had just been read.

When `cuts` calls a card roleless, or a deck's interaction or card-advantage figure
contradicts a card you just read:

```
python3 scripts/check_roles.py --all | head -40     # is it a known zero-role card?
PYTHONPATH=scripts python3 -c "import deck as D; print(D.classify_roles('<oracle text>'))"
```

If it is a hole, fix the pattern **in a batch at the end**, not one at a time — each fix
costs a roster-wide `#: tier:` prose sweep (K-12 requires the before/after diff), and
three separate sweeps in one session is three chances to introduce an error. Record the
hole in the doc as you find it and keep reading.

## Stage 5 — The doc skeleton

```markdown
# <pile> — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the swaps land and the findings are folded into the
deck files' `#: notes:` blocks. A scratchpad, not a source of truth — decks/ are.

**Source list:** <path> (<N> cards after removing those already in decks).

## 1. The decision framework          <- Stage 1; numbered rules, cited later by number
## 2. Standing error list             <- every misreading, so batch N+1 does not repeat it
## 3. Cross-batch observations        <- emerging themes, variant signals, open decisions
## 4. Running verdicts                <- one table per batch: card | deck A | deck B | note
## 5. Consolidated plan (live)        <- per deck: tiered ADDS with reasoning,
                                         CUTS with reasoning, and a PROTECT list
                                         naming what the ranking structurally cannot see
```

Legend for the verdict tables: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

**The consolidated plan is the deliverable.** A verdict table is raw material; a tiered
add list, each add's cut candidates, and the reason each is cuttable is the thing the user
acts on. Include a **protect list** — `cuts` ranks on theme fit and role credit, so a
card whose value sits in the rest of the deck (a doubler, a cost reducer, an unindexed
mechanic) sorts to the top of the cut list and must be named as off-limits with the reason
the ranking cannot see it.

## Stage 6 — Close out

1. Present the consolidated plan and get the user's picks. **Propose, do not apply.**
2. Applying is `/apply-changes`; drafting a variant the pile surfaced is `/draft-deck`.
3. Once the swaps land, fold the durable findings into the deck files' `#: notes:` and
   **delete the working doc** — a temporary file left behind reads as live guidance.

Every commit this skill makes carries the shared verify + commit tail in
`docs/verify-commit-tail.md` — `check_all.py` first, the session's own trailer, no model
ID, and no PR unless the user asks.
