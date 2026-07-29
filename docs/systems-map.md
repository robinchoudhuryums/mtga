# Systems map — task-first

**Status: LIVE.** Regenerate when a cycle adds a subcommand or a skill stage.
Measured 2026-07-29 against 64 decks, 1,853 owned cards, a 15.8k-card pool.

This maps the four things the user actually **does**, not the modules the code is
organised into. That choice is the point: the module structure
(`deck.py` / `lib.py` / `wishlist.py` / the gates) is already legible and is not where
the friction is. The friction is in composition — which commands to run, in what order,
and **what to do when two of them disagree**.

So the deliverable here is the **reconciliation points**: every place a human has to
resolve two answers by hand. Everything else is context for those.

---

## 1. How to read this

- **⚖ marks a reconciliation point** — two commands answer overlapping questions and
  the tooling does not settle it for you.
- Costs are wall-clock for a cold process, which is how a skill actually invokes them.
  They are small; **cost is not the friction in this repo** — the number of judgment
  calls is.
- A command that PRINTS a shortlist is never a verdict. The repo's standing rule is
  grade-from-oracle-text; the map does not repeat that per row.

---

## 2. Ingest new cards — `/ingest`

| # | Command | Returns | Cost |
|---|---|---|---|
| 1 | *route the paste* | which of 5 writers owns this data | — |
| 2 | `reconcile_crafts.py <export>` / `import_arena.py` / `import_collection.py` | dry-run diff, then `--apply` | <1s |
| 3 | `make refresh` | rebuilt derived data | **13s** no-change / ~5 min full |
| 4 | `verify_ingest.py <export>` | per-card present / at count / mana-covered | <1s |
| 5 | `card.py "<name>"` per new card | full text, legality, owned, decks | 0.3s |
| 6 | `deck.py suggest-homes "<name>"` per new card | ranked homes + a cut hint | 3.1s |
| 7 | `deck.py check <id>` for touched decks | newly buildable? | 0.3s |

**Reconciliation points**

- ⚖ **Step 1 is the whole risk.** Five writers disagree about what a quantity MEANS —
  lower bound (`import_arena`, `reconcile_crafts`) vs authoritative (`import_collection`,
  which is the only one that can lower a count). Nothing detects a wrong choice
  afterwards: both outcomes leave `check_all` green. The skill routes it; a human
  answering "is this a deck list or a collection export?" is the actual gate.
- **Step 3 used to cost the same for a 4-card ingest as for a full rebuild** — ~10 min,
  re-pricing ~15.9k cards through Scryfall's rate limit. **Fixed:** every step now skips
  work it has already done, so a no-change refresh is **13s** (nearly all of it the final
  `check_all`) and needs no network, and a four-card ingest fetches four cards.
  `make refresh REFETCH=1` forces the full rebuild. No longer a reconciliation point.
- **Step 4 is the one nothing else covers.** `check_all` proves the library is
  self-consistent, not that it contains what you pasted; a card that never arrived
  breaks no invariant.

## 3. Build a new deck — `/draft-deck`

| # | Command | Returns | Cost |
|---|---|---|---|
| 1 | `pool.py --owned --role <role>` (×7 roles) | owned cards by what they DO | ~0.5s each |
| 2 | `deck.py resolve <names…>` | pasteable `<qty> Name (SET) #` lines | 0.4s |
| 3 | `deck.py text NN` | full oracle text of the draft | 0.3s |
| 4 | `deck.py legal NN` → `preflight NN` | construction lint → one-call gate | 0.3s → **6.4s** |
| 5 | `deck.py mana NN` + `consistency NN` | pip demand → cast probabilities | 0.9s |
| 6 | `deck.py similar NN` | is it a duplicate of an existing deck? | 0.5s |
| 7 | `deck.py screen NN <rejected pile>` | re-score the pile against the CURRENT plan | ~1s |
| 8 | `deck.py cuts NN` + `suggest NN --owned/--needs` | trim filler, slot upgrades | 0.8s / 1.6s |
| 9 | `deck.py tier NN` | the metrics floor to grade the letter against | 0.6s |

**Reconciliation points**

- ⚖ **`similar` gives a number, not a verdict.** A cosine of 84% can rest on five
  shared cards, four of them lands. `--full` prints the shared card names; the
  distinct-or-duplicate call is human.
- ⚖ **`screen` must be re-run after any change of plan.** Its whole reason to exist is
  that a pile graded once keeps stale verdicts. Nothing detects staleness — the
  re-run is a discipline, not a check.
- ⚖ **`preflight` is 6.4s because it runs a full `check_all`.** Fine once per build;
  it is the wrong thing to put in a loop.

## 4. Refine a deck — `/tune-deck` → `/apply-changes`

The longest path, and the one that most needs a map.

**Gather (`/tune-deck` Stage 1)** — 13 commands, ~10s total:

| Command | Answers | Cost |
|---|---|---|
| `text` | the full oracle text (read FIRST, always) | 0.3s |
| `check` | do I own it | 0.3s |
| `stats` | curve, roles, interaction profile, protection, count uncertainty | 0.7s |
| `consistency` | keepable %, land drops, P(cast on curve) | 0.6s |
| `engines` | enabler ↔ payoff balance | 0.5s |
| `shape` | wide vs tall | 0.3s |
| `tier` / `tier --to A` | claimed letter vs floor / the measurable gap | 0.6s |
| `mana` | hybrid-aware pip demand + source lint | 0.3s |
| `tribes` | type-matters payoffs | 0.3s |
| `suggest --owned/--unowned` | on-theme adds | 0.9s |
| `suggest --needs/--interaction/--ramp/--lands` | STRUCTURAL adds themes can't see | 1.6s |
| `cuts` | ranked weakest-fit + full text | 0.8s |
| `screen` / `flex` | candidate re-score / stale flex lines | ~1s |

**Apply (`/apply-changes`)** — `quality --json` → `swap --apply` → `quality --vs` →
`preflight` → `tier` → `tier --audit-rationale` → `arena`.

**Reconciliation points**

- ⚖ **Six commands rank cards by fit** — `cuts`, `suggest`, `suggest-homes`, `screen`,
  `redundancy`, `tier --to` — each composing the same theme-fit + role machinery
  differently. Two of them answering the same question is now gated
  (`check_agreement.py`); the rest genuinely answer different questions and the
  reconciliation is yours.
- ⚖ **`cuts` is a 45% coin flip on CREATURES** — measured on the recommendation ledger
  (90% agreement on noncreature cuts, 45% on creature cuts, n=52). `fit` is an
  unnormalized sum, so tag count drives the keep-score and creatures carry ~5.7 tags
  against ~3.0 for spells. **This is the regime where `cuts` is used most.** Read it as
  a shortlist, never a signal, on a creature-heavy deck. Normalization was simulated
  across all 64 decks and rejected (it moves 1% of shortlist slots), and the standing
  P/T fix-hypothesis was **tested and rejected** (§7). Two caveats now attach to the 45%
  itself: per deck it runs 0% to 100%, so it is partly a statement about which decks were
  edited; and `deck.py feedback` discloses that breakdown so you can see it.
- ⚖ **`suggest` alone is blind to structural needs.** It filters to cards sharing a
  synergy theme, so a removal spell, a dork or a land can never surface through it.
  If the scorecard's deficit is interaction or mana, the fix comes from `--needs`,
  not from plain `suggest`. Two commands, and knowing which is the human's job.
- ⚖ **`tier` grades the LETTER; `tier --audit-rationale` grades the ARGUMENT.** A swap
  moves the figures the prose quotes *by construction*, so the rationale goes stale on
  essentially every application of `/apply-changes`.
- **Known blind spot, live:** a `"X stays"` claim in a `#: tier:` rationale is NOT
  covered by the audit (§7). Check it by hand after a swap.

## 5. Prioritize crafts — `/add-wishlist`

| # | Command | Returns | Cost |
|---|---|---|---|
| 1 | `wishlist.py --add <export>` | rows + auto-seeded Power | ~1s |
| 2 | `wishlist.py --suggest-targets [--write]` | idf-weighted home deck | ~1s |
| 3 | `deck.py suggest-homes "<card>"` per card | genuine second homes | 3.1s |
| 4 | `wishlist.py --rank` / `--budget "9M 10R …"` | ranked picks / a wildcard plan | 0.7s |
| 5 | `wishlist.py --audit-targets` | target a deck can no longer cast | <1s |

**Reconciliation points**

- ⚖ **The Power column mixes a machine guess with a human grade.** `Power Source`
  (`seed`/`hand`/`unknown`) is the only thing distinguishing them, and `--rank` flags a
  CONDITIONAL power as `pow~` because a rarity+role seed structurally cannot price a
  card that scales with your deck. Every Power that needed hand-correcting in practice
  was that class.
- ⚖ **Breadth (`use`) vs a specific second home.** `--rank` already credits reach; the
  human step is recording only a GENUINE specific second home in `Target`, not stuffing
  every fit into it.

---

## 6. Overlapping answers — the inventory

Every place two implementations answer one question. Measured, not asserted.

| Question | A | B | Agreement | Held by |
|---|---|---|---|---|
| Most-cuttable card in a deck | `rank_cut_candidates` | `_weakest_cut` | **64/64** (was 28/64) | `check_agreement` |
| Formats a card is legal in | `load_legalities` | `_legality_of` | agrees on a 120-card spread | `check_agreement` |
| Copies owned | `lib.owned_qty` | `deck.owned` | agrees incl. DFCs | `check_agreement` + `check_dfc` |
| Deck's interaction count | `role_tally` | `_interaction_count` | delegates | `check_agreement` |
| Card power seed | `wishlist._seed_power` | `deck._power_seed` | delegates | `check_agreement` + `check_rankings` |
| Role fillers (owned vs craft) | `owned_role_fillers` | `craft_role_fillers` | same filters | `check_agreement` |
| Cross-deck breadth | `deck.cross_deck_breadth` | wishlist `_breadth_of` | agrees | `check_suggest` #13 |
| Deck ↔ Arena paste match | `deck.match_paste` | the dashboard's JS | agrees on the tie-break | `tests/test_deck.py` |
| Derived-data rebuild order | `Makefile` | every prose copy | one definition | `tests/test_verify_ingest.py` |
| A "specific" theme | `_theme_is_generic` denylist | wishlist idf cutoff | **deliberately different** | — |
| A deck's signature themes | `_signature_themes` (loose) | `_strong_signature_themes` (strict) | **diverge — see §7** | — |

**Negative result worth keeping:** `suggest <deck>` and `suggest-homes <card>` are
inverse queries over the same fit question and use *different* theme gates — `suggest`
admits any theme the deck carries, `suggest-homes` requires a CENTRAL one. That looked
like a guaranteed divergence. Measured across 640 picks on 64 decks: **they agree 100%**,
because `suggest` sorts by theme weight and central themes are the heaviest, so the top
of its list always clears the stricter gate. Not a property — a consequence of the
ranking — but not currently a problem either. (My first measurement of this said 100%
*dis*agreement; it was reading a dict's keys as rows. Measure, then check the measurement.)

---

## 7. Open, measured

~~**`_signature_themes` saturates in `cuts`**~~ — **fixed.** The +2 keep-boost fired on
87% of nonland cards across the 22 `#: protect:` decks (100% in decks 20 and 46). It now
reads the STRICT spine (≥2 protected cards), firing on 66% — the same fix `check_suggest`
anchor 11b forces on `cmd_suggest_homes`. Roster diff: 14 of 64 decks re-scored, 4 top-cut
candidates moved. Deck 30's motivating case survives (strict signature = `{counters}`).

**The creature cut-ranking hypothesis: TESTED, REJECTED.** The proposal on file — bodies
compete on stats/evasion/curve slot, and `card-pool.csv` already carries `Power`/
`Toughness` that nothing in the cut ranking reads — was pre-registered and scored against
all 31 creature cuts on git-reconstructed pre-swap snapshots.

| model | paired (up/down/tied) | sign test | creature agreement |
|---|---|---|---|
| body quality as a bounded ±3 co-signal | 4 / 5 / 22 | p=1.00 | 48% → 48% |
| body quality scaled to the creature `fit` IQR | 11 / 16 / 4 | p=0.44 | 48% → **45%** |

The bounded result was predicted: `fit` has a roster median of 44 (IQR 31–59), so a ±3
term cannot reorder anything — the hypothesis is undeliverable as a bounded co-signal by
construction. The decisive number is the separation check: a cut creature's body quality
(mean 4.83) is indistinguishable from the median body of the creatures that STAYED (5.00),
and the cut card was the worse body only **17 of 31** times — chance, p=0.72.

What the test did find: the creature rate is **not a property of creatures**. Per deck it
runs 0/6, 1/6, 3/6, 2/4, 4/4 — 0% to 100%. `deck.py feedback` now prints that breakdown.
The build-vs-tune story fits deck 46 (0/6, rebuilt mid-window) but not deck 3 (1/6, an
ordinary tune), and excluding deck 46 moves the segment only 45% → 56%. All exploratory —
4–6-row subgroups. **The next move here is more ledger data, not another signal.**

**Other live follow-ons** (carried forward, unchanged):

- `tier --audit-rationale` STAY-marker false negative — a change-cue about one card
  suppresses a citation of another in the same ±140-char window, even when the clause
  says the card *stays*. Needs a roster sweep before landing.
- `doubler_restriction` parses POWER scopes only, so a type-scoped doubler (Splinter's
  Ninja clause) counts against the whole deck — 27 feeders in deck 20 against a
  correct 12. The `✱ multiplier` figure on a tribal doubler is an upper bound.
- ~~`make refresh` has no incremental path~~ — **done.** Every step now skips work it has
  already done; `build_mana.py` reuses its already-resolved rows and `build_pool.py` reuses
  a pool built within the last week for the same query (that fetch was 99% of the cost). Implemented as a flag on the one target (`make refresh REFETCH=1`
  forces the full re-price), never a second recipe — the order is the thing that must have
  a single definition.

---

## 8. What the map says about the surface

- **33 `deck.py` subcommands.** No task uses more than ~14 of them; the roster-level
  five (`audit`, `rotation`, `brawl`, `sync`, `verify`) belong to `/roster-review`
  alone, which is why they were unreachable until that skill existed.
- **Cost is not the constraint.** The entire tune-deck gather phase is ~10s, and
  `make refresh` is now incremental. What is expensive is human attention.
- **The commands that print EVIDENCE produce the fewest bad calls.** `cuts` and `swap`
  print full oracle text; `suggest-homes` handed out KEY/role-player/tangential labels
  with no text at all and produced the worst misread of the cycle. Every verdict
  surface now prints its evidence — keep it that way.
