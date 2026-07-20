Apply a set of confirmed swaps to a deck, keep flex/wishlist in sync, verify,
and commit.

Input: a deck id + a list of swaps in $ARGUMENTS or the user's latest message —
each as `−<cut> / +<add>` (from a `/tune-deck` Recommended-changes block or
named directly in chat). Apply these **only after the user has confirmed them**
(the standing "propose, don't apply until confirmed" rule); this skill is the
apply half of that loop.

This skill **orchestrates the existing scripts** — `deck.py swap` does the real
edit (with a `.bak`, an INV-04 re-parse, and stale-flex retirement), `deck.py
quality` is the regression guard, `deck.py preflight` is the gate. Read CLAUDE.md
Common Gotchas first (the swap gotcha especially: grade every cut from FULL
oracle text against THIS deck's engine, never a role/fit label).

## Stage 1 — Snapshot quality BEFORE the change (F10 guard baseline)

1. `python3 scripts/deck.py quality <id> --json > /tmp/quality-<id>-before.json`
   — captures the deck's quality vector (buildable, uncastable strays,
   interaction / card-advantage counts, curve, central themes) so the same
   change can be graded after.

## Stage 2 — Apply each swap (read both cards' full text first)

For each `−cut / +add`:

2. **Preview it:** `python3 scripts/deck.py swap <id> --cut "<cut>" --add "<add>"`
   (dry run) — prints the **full oracle text of BOTH cards** plus the
   card-count / creature / avg-MV / color deltas. Grade the cut from that text
   against this deck's engine (a "sacrifice"/"attacks alone"/kicker clause is
   often an upside here — CLAUDE.md). If the preview changes your mind, stop and
   say so rather than applying a bad swap.
3. **Apply it:** add `--apply` — writes with a `.bak`, re-checks INV-04, bumps an
   existing line instead of duplicating if the add is already present, and
   **auto-retires `#~` flex lines** the swap made stale (a line proposing the
   card you just maindecked, or cutting one you just removed).
4. **Handle the add's ownership:**
   - **Unowned add →** wishlist it targeted at this deck:
     `python3 scripts/wishlist.py --add -` with a one-line export (Target set to
     `<id>`), or flag it as a craft in the report. `--add` auto-seeds a heuristic
     Power and the F03 land-value axis handles lands; hand-adjust bombs.
   - **Now-owned add** (you crafted it as part of this change) → catalog it with
     `python3 scripts/reconcile_crafts.py <export> --apply` and prune it from the
     wishlist (see `/add-cards` Stage 1).
5. **Freed cut:** if the cut card is now run in **no** deck (`card.py "<cut>"`
   shows `in decks: (none)`), note it — it's a free wildcard's worth of card
   sitting idle, a candidate for another deck. Copies are fungible, so a cut here
   never "frees" a copy for elsewhere — it was already available everywhere; the
   note is just "nothing plays this now."

## Stage 3 — Grade the change with the quality guard (F10)

6. `python3 scripts/deck.py quality <id> --vs /tmp/quality-<id>-before.json` —
   diffs after-vs-before and flags **regressions**: interaction/card-advantage
   dropped, castability broke, a central theme lost its last copy, or the curve
   got heavier with no offsetting gain. It's a **soft** guard (intentional trades
   are fine) — but if it warns, re-read the cut from full text and justify the
   trade in the report, or reconsider the swap. A clean run prints "net
   improvement / no regressions."
7. For a *proposed* (not-yet-applied) add you're unsure about, `deck.py quality
   <id> --add "<name>"` warns if it's only a **tangential** fit.

## Stage 4 — Verify

8. `python3 scripts/deck.py preflight <id>` — legal + owned/buildable + castable
   + integrity in one block. A hard FAIL (illegal / uncastable / broken
   integrity) must be resolved before committing; unowned craft targets are WARN,
   not blockers, for a WIP deck.

## Stage 5 — Structured report

9. Report, scannably:
   - **Swaps applied:** each `−cut / +add` with the operative oracle clause of
     the cut quoted (grade-from-text) and the wildcard cost of any crafted add.
   - **Quality delta:** the F10 before/after — interaction / card-advantage /
     curve / central-theme changes; state "net improvement" or name each
     regression and why it's an acceptable trade.
   - **Wishlist / flex changes:** rows added or pruned, flex lines auto-retired.
   - **Tier:** run `python3 scripts/deck.py tier <id>` — it shows the claimed
     `#: tier:` against the tier its post-change metrics now support. If the letter
     no longer matches (the guard flags a mismatch, or the change plausibly moves
     it), **prompt the user to re-grade** against the CLAUDE.md rubric (e.g. "the
     metrics floor is now B — confirm and I'll update the header"). **Never
     auto-write a tier letter** — tier is a competitive judgment (design
     constraint).
   - **Verification:** the preflight verdict.
   - **Arena block:** paste `python3 scripts/deck.py arena <id>` — the clean
     `Deck`-prefixed import block the user pastes into Arena on mobile (the raw
     file with `#` headers is useless to them).

## Stage 6 — Commit

Commit the deck file (+ any wishlist/library/gallery changes) per the shared
**verify + commit tail** in `docs/verify-commit-tail.md` verbatim: `check_all`
must pass first; the commit ends with the `Co-Authored-By:` / `Claude-Session:`
trailer and never contains the model ID; push to the working branch (restart from
`main` first if its PR is already merged).
