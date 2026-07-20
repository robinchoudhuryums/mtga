# Tooling Improvement Plan

A structured findings list for `/broad-implement`. Each finding is self-contained:
**why**, **files**, **changes**, and **acceptance**. Implement in ID order —
later findings depend on earlier primitives. Every change must keep
`scripts/check_all.py` green and follow CLAUDE.md's Common Gotchas.

**Design constraints (apply to all findings):**
- Skills **orchestrate the scripts; never reimplement their logic** — the scripts
  stay the single source of truth, so skills can't drift from them.
- Card evaluation reads **complete** oracle text by default (F01). No path may
  truncate a card's text to grade/classify/rank it.
- Do **not** auto-write tier letters — tier is a competitive judgment; prompt a
  human re-grade instead.

---

## F01 — Full-text-by-default in every card-evaluation path

**Why.** Repeated mis-grades came from reading a *sliced* card (a clause hidden by
truncation). `card.py` fixed the chat entry point; this makes full-text the
enforced default everywhere and gives every evaluator one accessor.

**Files.** `scripts/lib.py` (new shared accessor), audit `scripts/deck.py`
(`classify_roles`, `cuts`, `suggest`, `suggest-homes`), `scripts/wishlist.py`
(`_rank_scores`, `_seed_power`, `cmd_suggest_targets`), `scripts/tag_synergies.py`;
`CLAUDE.md`.

**Changes.**
1. Add `lib.full_card_text(name)` → the complete `Card Text` (library then pool),
   never truncated; refactor evaluators to use it.
2. Grep-audit for any text slicing (`Card Text`[:N], `.split(...)[0]` on text,
   `head`-style caps) in evaluation code and remove.
3. `card.py` becomes the mandated pre-grade read; add a one-line CLAUDE.md
   principle: "evaluate a card only from its full text — via `card.py` in chat, via
   `full_card_text()` in code."

**Acceptance.** An audit shows no evaluation path truncates card text; a card whose
key clause is on its *last* line classifies/roles correctly.

---

## F02 — New/unindexed mechanic detector

**Why.** When a set introduces a new keyword/mechanic, it falls through
`tag_synergies.KEYWORD_THEMES` (mis-tagged or missed). Catch it automatically.

**Files.** New `scripts/check_keywords.py`; wire into `scripts/check_all.py` as a
**soft** (non-gating) warning; expose the known-keyword set from
`tag_synergies.py`; `card.py` (surface per-card).

**Changes.**
1. Build the known-keyword set = `KEYWORD_THEMES` keys ∪ `FLAVOR_KEYWORDS`.
2. **Signal A (authoritative):** any keyword in `card-mana.csv`'s Scryfall
   `Keywords` column not in the known set → candidate new mechanic.
3. **Signal B (text-structure heuristic, for keywords Scryfall hasn't tagged):**
   flag ability lines matching a keyword-ability shape — a capitalized word/phrase
   at line start followed by `" — "`, or parenthetical reminder text `"(As this …"`
   — whose lead word isn't a known keyword or English stop-word.
4. Report distinct unknown mechanics with an example card each; soft-warn in
   `check_all`; add a `⚠ unindexed mechanic: <kw>` line to `card.py` output.

**Acceptance.** A synthetic card with a made-up keyword is flagged by both the
standalone check and `check_all`'s soft warning; known keywords produce no
false positives; `check_all` still exits 0 (soft only).

---

## F03 — Land-aware wishlist rating axis

**Why.** The ranking is *theme-fit + power*; lands have no synergy themes, so they
score ~0 fit and rank on an ambiguous "power." Lands need a manabase-value axis.

**Files.** `scripts/wishlist.py` (`_rank_scores`); reuse `deck.py` mana-source
logic.

**Changes.** When a wishlist card is a land, replace the theme-fit axis with a
**manabase-value** score for its target deck: (a) do the colors it produces match
the deck's colors (a WB dual in mono-W is half-dead)? (b) does the deck *need* that
fixing — cross-reference `deck.py mana` source counts vs pip demand (short on a
color the land makes → high)? (c) untapped/fixing quality (untapped > tapland >
gainland-tapland). Blend with `Power` as today; keep the `combined` scale so
`--budget` and the ranking gate stay valid.

**Acceptance.** A dual in a matching 2-color deck short on one of its colors ranks
high; the same dual targeted at a mono-color deck ranks low; `check_rankings.py`
still passes.

---

## F04 — Fit-strength labels (KEY / role-player / tangential)

**Why.** When a card lists multiple deck fits, nothing differentiates a *key* fit
from a *tangential* one.

**Files.** `scripts/deck.py` (`suggest-homes`, `suggest`); `scripts/wishlist.py`
(reuse in `--rank`/`--suggest-targets` output where a home is shown).

**Changes.** For each card→deck fit, classify strength: **KEY** (shares the deck's
*most-central* theme, or fills a named gap the deck is short on — interaction /
card advantage), **role-player** (a central but secondary theme), **tangential**
(only generic / one-off overlap). Surface the label in the per-deck fit rows.

**Acceptance.** A food card → Gastromancer = KEY; a removal spell → an
interaction-light deck = KEY; a generic-etb card → a broad deck = tangential.

---

## F05 — Shared `preflight` verification primitive

**Why.** Every change ends with the same checks; the skills need one call.

**Files.** `scripts/deck.py` (new `preflight <id>` subcommand — distinct from the
existing Arena-drift `verify`).

**Changes.** `deck.py preflight <id>` runs legal + owned/buildable + castability +
a `check_all` pass and returns a compact structured PASS/FAIL block the skills can
parse.

**Acceptance.** `deck.py preflight 19` reports legal/owned/castable/integrity in
one structured block; non-zero exit on any hard failure.

---

## F06 — Skill: `add-cards` (systematic owned-card intake)

**Why.** Codifies the reconcile-and-fit-check loop repeated ~10× per session.

**Files.** `.claude/commands/add-cards.md`.

**Changes.** Pipeline: parse an Arena export of newly-owned cards →
`reconcile_crafts.py --apply` → `build_gallery.py` → prune reconciled rows from the
wishlist + re-home drift (`wishlist.py --audit-targets`) → **per card:** `card.py`
(full text + legality; heed F02 unindexed-mechanic flags) + `deck.py suggest-homes`
with F04 strength labels → classify each real fit as **key upgrade / sidegrade /
different-flavor** with a cut candidate → `deck.py preflight` on touched decks →
**structured report** (cataloged N; per-card fits: card→deck (strength) + cut
candidate) → standardized commit (F08). Orchestrates scripts only.

**Acceptance.** Pasting an owned-cards export runs the whole pipeline and emits the
structured report; no logic duplicated from the scripts.

---

## F07 — Skill: `apply-changes` (systematic swap application)

**Why.** Codifies the swap→flex→wishlist→verify→commit loop repeated ~15× per session.

**Files.** `.claude/commands/apply-changes.md`.

**Changes.** Pipeline: parse swaps (from a `/tune-deck` result block or chat as
`−cut / +add`) → per swap `deck.py swap --apply` (auto-retires stale flex lines;
INV-04 recheck) → if an *add* is unowned: wishlist it (Target = this deck, F03/F04
aware) or flag craft; if a *cut* frees a card used nowhere else, note it → reconcile
any now-owned adds and prune them from the wishlist → `deck.py preflight` →
**structured report** (swaps, wildcard cost, interaction/curve deltas, wishlist
changes, tier-before/after with a *prompt* to re-grade, verification) →
standardized commit (F08). Orchestrates scripts only.

**Acceptance.** A swap list applies systematically with the structured report; flex
notes and wishlist stay in sync; tier letter is prompted, not auto-written.

---

## F08 — Standardized verify+commit tail (shared by F06/F07)

**Why.** The avoidable mistakes live here (model-ID in a commit, skipped
`check_all`, stale flex note).

**Files.** A shared snippet/section referenced by `add-cards.md` and
`apply-changes.md`.

**Changes.** Encode the tail once: `check_all` must pass first; commit message ends
with the Co-Authored-By + Claude-Session lines and **never** contains the model ID;
push to the working branch; if the branch's PR is already merged, restart from
`main` per CLAUDE.md.

**Acceptance.** Both skills reference the same tail; a dry-run shows the exact
commit discipline.

---

## F09 — Docs sync

**Why.** Keep CLAUDE.md/README from drifting from the new tools/skills.

**Files.** `CLAUDE.md`, `README.md`.

**Changes.** Document: the full-text-by-default principle (F01), the
unindexed-mechanic detector (F02), the land rating (F03) and fit-strength labels
(F04), `deck.py preflight` (F05), and the two skills (F06/F07). Add `card.py`,
`check_keywords.py` to the Subsystems lists. Note `check_all`'s new soft warning.

**Acceptance.** `sync-docs` finds no remaining drift for these features.
