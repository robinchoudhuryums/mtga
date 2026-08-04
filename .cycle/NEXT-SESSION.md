# Handoff — start the next session here

Written 2026-08-04, for a session with none of this one's context.
Read this before CLAUDE.md's Common Gotchas, not instead of them.

**Read the evidence file when a rule's reasoning matters.** CLAUDE.md carries the RULE and
any live residual; the incident and measurement live under the anchor the rule ends with —
`[G-nn]` / `[K-nn]` in `docs/gotchas.md`, `[C-nn]` in `docs/cycle-config.md`. Nothing was
deleted; open the long form before deciding a rule looks arbitrary.

**Also live: `docs/systems-map.md`** — which command answers a question, and why two
commands disagree.

---

## 1. Repo position

- Working branch **`claude/broad-scan-hekdj0`**. Its PR **#100** (the 2026-08 broad-scan
  cycle: BS-01..BS-20, six new test files, 922 pytest) was squash-merged to `main` as
  `1df3fbb`; the branch was then restarted from `main` and now carries UNMERGED commits:
  the data-hygiene pass (`1899be3` — 15 Power cells re-scaled, 27 printings repointed,
  4 stale rationales re-grounded), the five 55-mardu pile-analysis batches, and the three
  drafted decks (55 / 55a / 55b). **No PR is open for these — the user has not asked.**
- Gates green at handoff: `check_all` all invariants hold, ZERO soft warnings; full pytest
  suite green (922 tests, 24 files).
- Collection: **1,895 cards, 83 deck files** (dashboard rebuilt at each deck landing).

## 2. What this session did

1. **Drafted the three Mardu decks** from the completed 131-card pile analysis, via
   /draft-deck each: **55 Mardu Waves** (Mobilize pulse; tier A PROVISIONAL at the floor),
   **55a Mardu Spellstorm** (C2+D+E cast-cadence; A PROVISIONAL), **55b Mardu Airbender**
   (C1 exile-cast; **B PROVISIONAL, argued UNDER the A floor** — the header carries the
   argument). All three: legal clean, preflight READY (WIP craft targets expected),
   rationale audits current, manabases rebalanced from `consistency` reads.
2. **Two text-level corrections** worth keeping: Zuko/Appa trigger on casts FROM EXILE
   only — flashback casts from the GRAVEYARD and does NOT feed them (the pile doc's
   "pairs with flashback" was wrong; 55b's notes carry the ruling). And `similar` caught
   **deck 45 Exile Dividend** already owning the exile-cast identity (same colors, same
   Zuko/Appa payoffs) — 55b's archetype states the real differentiation (45
   impulses/heists off libraries and drains; 55b exiles its OWN board and goes wide).
3. **`.cycle/55-mardu-analysis.md` is DELETED** per its own contract — durable findings
   folded into the three deck files' `#:` headers (timing spine in 55, gate counts in
   55a, exile-only ruling + rotation exposure in 55b, parked-not-dead list with revival
   counts in 55).
4. Six newly-roleless deck cards baselined in `role_baseline.txt` (373 now): Frontline
   Rush, Neriv, Blazing Firesinger, Brazen Collector, Pigment Wrangler, Knight Luminary —
   token-makers, doublers and prepared/combat mana, all baseline-taxonomy shapes.

## 3. Open work, in priority order

1. **`.cycle/54-pile-reanalysis.md` §5/§5b — the queued swap plans for decks 54/54a/54b
   are still NOT applied.** That doc is live and TEMPORARY; apply via /apply-changes or
   re-judge, then delete it.
2. The three 55-family decks are aspirational WIPs — craft-cost sequencing is in each
   preflight; `wishlist.py --budget` is the planner. Quintorius Kand (in 55b and 45)
   rotates ~2026 with WOE Heartflame; 55b's OTJ plot spine rotates ~2027 (needs a
   re-draft then — noted in its header).
3. Standing roadmap bets, owner-paced: log the first matches (`matches.csv` still
   empty), deck lifecycle status, keyword theming Tier 1 (`keyword_baseline.txt`).
4. app.py's Flask routes and build_gallery's HTML output remain the two untested
   surfaces (need a Flask test client / HTML assertions — a different harness class).

## 4. Traps that cost time this session

- A same-pile sibling deck goes in the CORE deck's directory as `NNx-slug.txt`
  (`decks/55-mardu-waves/55a-spellstorm.txt`), NOT its own `decks/55a-…/deck.txt` —
  the id won't parse otherwise.
- `tier --audit-rationale` reads "copies a Seething Song" as a stale card citation —
  phrase similes as effects ("a +5 red burst"), not card names.
- Hand-dated rotation years were wrong twice; `deck.py rotation` has the per-deck
  years — cite it, don't date sets from memory.
