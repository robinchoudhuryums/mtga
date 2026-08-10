# Cycle Workflow Config — the long form

The detail behind `CLAUDE.md`'s **Cycle Workflow Config**, keyed by the `[C-nn]` anchor
each field carries.

That section has a canonical shape, defined by `setup-cycle.md` in
[claude-workflow-tools](https://github.com/robinchoudhuryums/claude-workflow-tools) — the
command that writes it. **Test Command is a single line. A Subsystem is a comma-separated
file list. A Regression Scenario is Steps plus Expected.** The vendored workflow commands
read those fields, so the field STRUCTURE is load-bearing; the reasoning that had accreted
inside them is not, and it lives here instead.

**Nothing was deleted in the split** — every section below is the original text, moved
verbatim. `scripts/check_docs.py` gates the link in both directions.


## [C-01] Test Command — the gate stack

**2026-08 broad-scan Batch 4 — four sub-checks and a channel fix, all "watched to
fail" before being trusted.** (1) `check_suggest` anchor **13d**, sibling-castability
parity: the synthetic world now carries cards whose color identity and printed cost
DISAGREE (a mono-U-castable `{1}{U/R}` hybrid, a `{3}` rock with 5-color identity,
their suggest_scored twin, an uncastable `{W}{W}` control), run end-to-end through
`suggest_scored` / `suggest_mana` / `suggest_interaction` — so the BS-01 shape (a
castability fix landing in one sibling and not the others, which hid 34 interaction
cards + 25 mana sources for a full cycle) fails the build at introduction. (2)
`check_dfc` grew an **index-alias registry** — ten name-keyed loaders behaviorally
verified to resolve a live DFC's front key, with getattr-at-run-time resolution so a
renamed loader is a hard error — plus, since 2026-08, a **registry-completeness AST
scan** that finds the builders instead of trusting the list: the registry could only
ever check loaders someone remembered to add, and every bug in this class (BS-12,
BS-16) was a loader on no list. It found `deck._legality_of` on its first run — and a
**payload pin** on `templates/deck.html`'s
`ownedOf` helper, the serialized-index consumer (BS-08's channel) no Python scan can
reach; aliasing itself now has one home, `lib.alias_front`. (3) `check_patterns`'
perimeter covers **wishlist.py** (BS-04): `_FLEX_REMOVAL_RE` and
`_CONDITIONAL_POWER_RE` are live-corpus checked — the flex-removal seed bonus going
dead was invisible to every other gate, since `check_rankings` anchor 7 stays green
without it. (4) `check_roles` grew the baseline's **pruning half**
(`stale_baseline_entries`, wired into check_all): an entry a pattern fix un-zeroed
would otherwise mask a future re-zeroing regression forever. Channel fix: check_all
now PROMOTES crash-skipped soft radars above the ordinary warnings with their own
"N RADAR(S) DID NOT RUN" count (a radar that cannot run is a gate that never fires),
`check_keywords.flavor_overreach` reports its own skip instead of `except: pass`,
`check_docs`' anchor regex survives a three-digit [G-100], and the
unverified-printings warning names its first offenders instead of a delta-blind
count. Perf note: the BS-18 membership scan initially cost +28s of check_all
(unconditional `ast.get_source_segment` per `in`-node); a constant-subtree
pre-filter restored it, with the sensitivity re-verified against the original bug
shape.

**2026-08 addition — INV-04 grew a printing check.** It used to assert only that a
deck line PARSES; a `(SET)` code that exists nowhere is now a HARD failure and an
unheld `COLLECTOR #` within a real set is a soft warning. The split, and why basics
are exempt, is measured in gotchas.md under [G-65]. Roster at the time of the change:
0 hard, 27 soft across 15 decks — all pre-existing and silent until the check existed.

(deterministic integrity gate; exits non-zero on any hard invariant break —
NOTE it imports `deck` as a MODULE and calls `cmd_*` directly, so it never builds an
argparse tree — the CLI surface is covered separately by `tests/test_cli.py` and a
dependency-free smoke step in `.github/workflows/integrity.yml`; see the CLI gotcha
above —
INV-01…04 plus a **ranking-model sanity check** (`check_rankings.py`) that guards
the Doctor-Doom-class regression: a scoring change that silently reclassifies a
real tribal theme as "generic". The ranking check is distribution-based, so it
survives cards being crafted off the wishlist; it also carries a **wiring** anchor
asserting `_seed_power` reads an Arena wildcard LETTER and the matching rarity WORD
identically — deck.py's `cuts`/`redundancy` pass letters, and a mismatch silently
seeded every rare and mythic as an uncommon (audit F-01). Note INV-03 is now
existence **and schema**: a derived file that loses its own columns (a pool without
`Rarity`, a mana file without `Mana Cost`) is a HARD failure, since the old
existence-only check let a library-header rewrite pass green. Five more model-sanity checks are
also hard-gated: **color-parsing** (`check_colors.py`) locks in the F1/F2 fix (a
colorless card must not read as red; a slash-gold must pass the subset test) and a
static scan bans the naive inline `if ch in "WUBRG"` parse outside `lib.py` — in
**BOTH** its shapes, the comprehension AND the equivalent `for` STATEMENT, since the
scan originally tested only the comprehension node types and the same bug written as a
loop passed green (broad-scan F-07). It also rejects a **stale `_INLINE_PARSE_ALLOW`
entry** naming a file or function that no longer exists: an exemption for code that is
gone reads as a considered decision while covering nothing, and silently pre-grants a
pass to any future function that reuses the name — the same hand-kept-registry rot the
`check_patterns` completeness check exists for;
**DFC ownership-join** (`check_dfc.py`) guards the front/full-name convention — a
behavioral anchor that `lib.owned_qty` and its wrappers (`wishlist._owned_of`,
`pool.owned_of`) resolve an owned double-faced card by its front face, plus a static
scan that flags a raw ownership lookup bypassing `owned_qty` (the A3/A4/F6 class), and
a static scan for pool-shaped name-index BUILDERS that must each be registered or
exempted with a reason (9 found, 0 false positives at introduction);
**suggest scoring** (`check_suggest.py`) keeps the needs-aware suggest/cuts terms
BOUNDED — the diminishing-returns role credit and the curve-gap factor can't
silently reorder a tuned deck (#1/#2), the suggest power co-signal never overrides
theme fit (#6), the `suggest-homes` rainbow-fixer boost stays bounded/capped
and zero below 3 colors while `_is_color_fixer` reads TEXT in mana/land-type context
(so an UNINDEXED mechanic can't hide a real fixer — Vivid was the case that proved it
and has since been themed, which retires the example and not the guard; and a Treasure's reminder
text can't fake one) and `_fixer_rate` keeps a single any-color source discounted below
the KEY bar (anchor 6) — with anchor 15 pinning the WIRING half, that `_weakest_cut`
never proposes cutting a fixer to make room for a fixer, the CUTS power co-signal stays bounded/neutral-centered/
monotonic so it only breaks near-ties in the cut ranking (anchor 7), and the CUTS
ability-distinctiveness co-signal stays bounded/neutral-centered/monotonic (anchor 8,
which also proves the tag-rarity metric reads a vanilla card as ~0 and a rare mechanic
above a generic one, AND that the structural-text signal reads vanilla/plain-ETB/bare-mana
low while rescuing an unusual trigger, `card_distinctiveness` taking the max so structural
only ever raises), and the `suggest --lands` synergy + shortfall nudges stay bounded/
non-negative and fixing-dominant, favoring the deck's top theme / scarcest color (anchor 9),
and the NEEDS-model nudges (`--ramp` accel-want / restriction-fit, `--interaction` scaling
boost) stay bounded/rising-with-support (anchor 10), and `fit_strength` never credits a
bare BROAD-TRIBE overlap (`_GENERIC_TRIBES`: Human/Hero/Villain) as a KEY home — not as the
top theme nor via a `#: protect:` signature — while a narrow tribe and a specific theme
still read KEY (anchor 11, the Hawkeye-"KEY"-in-every-Hero-deck fix), and **anchor 11b
asserts the WIRING of that same demotion one category over** — `fit_strength` must be handed
the STRICT `_strong_signature_themes` (a theme carried by ≥2 `#: protect:` cards), never the
loose `_signature_themes` that unions every protected card's tags. With the loose set deck
37's signature held 25 themes (etb, removal, sacrifice, combat, tempo…), so Azula, Cunning
Usurper — a Human Noble Rogue — read KEY for three WIZARD-tribal decks on `Human, etb` alone;
roster-wide the loose set gave 99 KEYs where the strict set gives 54, and all 45 differences
were KEY→tangential. It HAS to be a wiring anchor: `fit_strength` is RIGHT to mint KEY from
any signature it is handed, because the rescue's whole point is that a generic theme IS a
signature when it is genuinely the spine (`counters` is in GENERIC_THEMES, and deck 30's
strict signature is exactly `{counters}`), so asserting the pure function returns
`tangential` for a generic signature would CONTRADICT the rescue — the strictness lives in
the CALLER and only reading the call site catches it. And the suggest-homes
curve co-signal (`_home_curve_fit`) stays a bounded/never-boosting SORT nudge while
`_central_themes` admits a curated mechanical sub-theme at floor 2 yet still gates a generic
theme (anchor 12, finding #5 + the secondary-payoff centrality fix), and — unlike every other
check in this suite — **anchor 13 runs the real ENTRY POINTS end-to-end** over a synthetic
deck+pool and asserts the OUTPUT ORDER (a mythic and a common differing ONLY in rarity must
not score the same power; an off-theme card must not be suggested; both breadth models must
agree). Pure-function anchors cannot see WIRING — F-01 shipped past eleven green gates
because `_cuts_power_adj` was provably bounded/monotonic while its CALLER handed the seed the
wrong rarity shape, so a model correct in every part was still wired up wrong (F-18). And
**anchor 14** keeps the suggest-homes DOUBLER term bounded — zero below
`_DOUBLER_MIN_SOURCES`, never above `_DOUBLER_CAP`, monotonic in feeder count — and pins the
two halves the term is worthless without: `doubler_axis` classifying tokens/counters/triggers,
and `doubler_restriction` reading a doubler's own "power N or less" scope (unrestricted
support over-counted Delney 6× and would have minted a false KEY); and **anchor 16** does
the same for the CUTS side of that signal — `_cuts_multiplier_adj` bounded, zero below
`_CUTS_MULT_MIN_SOURCES`, never negative, rising with support, plus the new LIFEGAIN axis
and its discriminator (a `plus 1 instead` replacement must NOT read as a doubler). Its
WIRING half lives in `tests/test_deck_models.py`, because the pure function was already
correct here — the bug was that `rank_cut_candidates` never called it;
**engine classifier** (`check_engines.py`) anchors the enabler/
payoff detection on canonical cards (#3); **tier floor** (`check_tier.py`) proves
the archetype-aware floor grades non-aggro decks identically to before and only
ever raises an aggro band (#4); and **dead patterns** (`check_patterns.py`) — THREE
checks over 145 registered patterns: every card-text classifier regex must match ≥1 card
in the ~15.8k-card pool, no pattern source may contain a Python tuple repr like `(0, 2)`,
and **every module-level compiled pattern in `deck`/`lib`/`tag_synergies` must be either
REGISTERED or explicitly EXCLUDED with a reason** (the COMPLETENESS check). This is the
gate for THIS PROJECT'S SIGNATURE BUG: a regex that compiles fine and can never fire. Both historical
instances shipped past every other gate — the f-string `{0,2}` that became the literal
`(0, 2)` (46 decks lost their interaction count) and `(?:owner|their) hand`, which
demands the text "owner hand" while Magic writes "owner's hand" (every bounce spell
scored zero roles). Unit tests structurally cannot catch these, because each pattern was
tested against a string its author wrote to match it; only a roster-wide diff did, and
only when someone remembered to run one. It found a THIRD on its first run — `costs {1}
less for each`, where Magic writes "costs {1} less TO CAST for each" — which was invisible
even to a diff, since a general pattern already covered those cards so no count ever
moved. Note the check must feed each pattern the text form it really runs against
(`norm` / `raw` / `window`): the case-sensitive tribal-payoff scan reads ORIGINAL-case
text and reads as dead against a lowercased corpus, while a **`window`** pattern is
`$`-anchored and run against a SHORT SLICE (`_POWER_SCOPE_*` read
`text[m.start()-25:m.start()]`), so it matches 0 of 15.8k WHOLE texts by construction —
registering those two naively would have failed the build on two healthy regexes. They
keep the corpus-free format-leak check and skip the live-corpus one.
**The COMPLETENESS check exists because the coverage list was hand-kept and had fallen
13 patterns behind the code** (broad-scan F-04): all five of `lib.structural_
distinctiveness`, every `_DOUBLER_AXES` matcher, `_DOUBLER_POWER_RE` and `_REMINDER_RE`
were uncovered. The structural-distinctiveness hole was the dangerous one —
`card_distinctiveness` returns `max(tag_score, structural)`, so a dead pattern there
silently collapses the structural signal to 0 and the `max()` HIDES it: no error, no
visible count change, `cuts`' `Uq` column quietly reverting to tag-only. Anything
deliberately left out is enumerated with a justification in `_EXCLUDED` (deck-file /
mana-symbol SYNTAX, and the tier-RATIONALE prose patterns, which read a human argument
rather than card text and are unit-tested in `tests/test_deck.py` instead). A new
pattern now fails the build until someone says what corpus it runs against — the same
lesson as the checks that could never fire: a hand-kept registry grows holes.
**MODEL AGREEMENT** (`check_agreement.py`) is the twelfth hard gate and the one that
covers what the other eleven structurally cannot: **two functions that are each correct
and disagree with each other.** Every anchor above evaluates a model in ISOLATION, and a
divergence exists only BETWEEN models — so the recurring bug of the last cycle (*the
model was right and the caller never asked*) shipped five times with every gate green.
It registers QUESTIONS, each with two implementations and a shared input, and fails when
they differ: the deck's most-cuttable card (`rank_cut_candidates` vs `_weakest_cut`),
a card's format legality (`load_legalities` vs `_legality_of`), copies owned
(`lib.owned_qty` vs `deck.owned`), the interaction count, the power seed, and
owned-vs-craft role-filler FILTER parity. Prior art is `check_suggest` #13 and
`tests/test_verify_ingest.py`, which are left where they are — moving them would trade
one registry for two. Two design rules, both earned: **prefer the LIVE ROSTER to a
synthetic fixture** where the pair is deck-shaped (a synthetic case only proves the pair
agrees on the example its author wrote — the cut divergence passed every pure-function
anchor while disagreeing on 36 of 64 real decks), and **a stale entry is a HARD failure**
(resolution is by attribute lookup at run time, so a rename fails the build instead of
silently skipping the pair — the `_INLINE_PARSE_ALLOW` rule). It cost check_all 5.5s →
10.8s, which is the price of the one gate that can see across models.
**Its own first two drafts were VACUOUS, and that is the part worth remembering.** The
role-filler pair ran green with the format filter deliberately deleted from
`owned_role_fillers` — twice — for two independent reasons: it read the DEFAULT `limit`,
so it saw the cheapest ten rows rather than the filtered SET and the illegal card sorted
below the cut; and it asked only about the INTERACTION role set, whose one illegal filler
(Dovin's Veto) is off-color for every deck in the sampled slice, while the card the
original bug actually offered (**Deadly Dispute**) is a CARD-ADVANTAGE filler. Both were
found by mutating the code and watching the check stay green, never by reading it. **A
pair is only covered on the axes you ask about, and a truncated view is not the set.**
It also emits **soft, non-gating warnings**:
wishlist target drift — a card whose Target deck can no longer cast it
after a retune — via `wishlist.py --audit-targets`; and **new unindexed mechanics**
— `check_keywords.py` flags a keyword on an owned card that isn't in
`tag_synergies.py`'s map yet (a new set's mechanic), baselined in
`keyword_baseline.txt` so it stays quiet until something genuinely new appears
(`check_keywords.py --update-baseline` to acknowledge one); **FLAVOR_KEYWORDS
registry staleness** — `check_keywords.stale_registry_entries()` flags a
`FLAVOR_KEYWORDS` or `keyword_baseline.txt` entry matching NO card in the corpus (a
suppression with nothing behind it; both lists only ever grow, and nothing pruned them
when a set left the pool). Soft on purpose — it breaks no invariant — and skipped below
the corpus floor, where a pool-wide mechanic can legitimately sit on zero owned cards
(the `harmonize` case). A stale `_INLINE_PARSE_ALLOW` entry is HARD by contrast, because
it sits inside a hard gate; and **FLAVOR_KEYWORDS
overreach** — `check_keywords.flavor_overreach()` flags a denylisted "flavor" word
that's also theme-mapped, or one shared by several owned cards (likely a real
mechanic being suppressed, audit F24); **theme coverage** — `check_themes.py` flags
an owned card whose oracle text clearly plays a high-confidence theme (food, landfall,
proliferate, convoke, graveyard, lifegain, counters) it ISN'T tagged with (the theme
analog of `role_coverage_flags`; a stale/removed tag distorts every tag-based
recommendation), summarized to one line (#7); **role coverage** — `check_roles.py`
flags a card in a deck that `classify_roles` scores with NO functional role at all,
baselined in `role_baseline.txt` so it stays quiet until a deck edit or a new set
introduces one. `_ROLE_PATTERNS` is a WHITELIST of phrasings, and a whitelist's misses
are silent under-counts the tier floor inherits as fact — eight such holes surfaced in
one 2026-08 session, every one found by a human reading a card rather than by a gate
(see G-67). Soft because a genuinely roleless card — a vanilla body, a pure combat trick
— is a legitimate zero; read the number as a DELTA rather than a backlog, since the
baseline of 367 is partly legitimate. `check_roles.py --update-baseline` acknowledges the
current set; and **tier mismatch**
— `deck.py tier_consistency_issues()` flags a deck whose claimed `#: tier:` sits ≥2
bands above the tier its measurable quality vector supports (an inflated/stale
letter — see the Competitive Tiering rubric); and **stale flex lines** —
`deck.flex_staleness()` flags a `#~ -Out | +In` line whose cut card already left the deck,
which nothing else covered; and **stale tier rationales** — `deck.rationale_staleness()`
roster-wide. That last one is the lesson: the check EXISTED for a long time and nothing ran
it. `deck.py tier <id> --audit-rationale` could always find these, but only for one deck, on
demand, and the instruction to run it after every deck edit lived in CLAUDE.md prose that no
skill executed — so its two siblings swept the roster every run while it waited to be
remembered, and **13 stale figures across 10 decks accumulated with every gate green**. Same
shape as the dead-regex bugs: a check that cannot fire is not a check. It is now automatic
(and `/apply-changes` + `/tune-deck` run the per-deck form at the moment of the edit, where a
human is present to fix the prose). Soft warnings never fail the build.)

**The reference-table loaders are memoized** (`deck._file_memo`, keyed on each source
file's `(mtime_ns, size)`). `load_mana` / `load_card_data` / `load_card_meta` /
`load_collection` / `load_keywords` / `load_rarities` re-parsed their CSVs on EVERY call, and a roster pass
calls them once per deck — 65 × ~0.31s ≈ 21s of `check_all`'s runtime, and the reason a
roster-wide rationale sweep looked too expensive to run automatically, which is precisely
how the check above never got wired in. **check_all went 23s → ~5s including the new
sweep.** Two design points worth keeping: the decorator takes the module-global NAMES of
its files and resolves them per call, because `check_suggest`'s wiring anchor repoints
`deck.POOL_CSV` at a synthetic pool and a path captured at decoration time would key the
cache on the REAL file while the loader body read the synthetic one — a stale-cache bug in
the one check whose job is catching wiring mistakes; and the tables are now SHARED, so a
caller that needs to mutate one must copy it first (no caller does today — verified by
scanning `scripts/` for external mutation).
**`load_rarities` was the one loader left OUT of that sweep, and it hid for a cycle
because it is read per CARD-SCORING PASS rather than per command.** `rank_cut_candidates`
calls it for the power co-signal, so a full-pool re-parse ran for every deck a roster
sweep touched: it was **85% of `deck.py cuts`' runtime** (0.69s of 0.81s under cProfile).
Invisible in any single command's wall clock — 0.8s reads as fine — it only surfaced when
a roster-wide gate made the per-deck cost add up, and fixing it took the new agreement
gate's cut-ranking pair from 12.0s to 2.3s. **When adding a reference-table loader, check
whether it is called per COMMAND or per ROW; the second needs the memo far more and shows
the cost far less.**

A **pytest unit layer** (`tests/`, run with `pytest` or `make test-units`, deps in
`requirements-dev.txt`) COMPLEMENTS this gate — fast, isolated tests that pin the
edge-case behaviour of the pure helper functions. It is NOT part of the Test Command
above (check_all stays zero-dependency); both run in CI via `.github/workflows/tests.yml`.


## [C-02] Subsystem: Data

Data: card-library.csv, card-pool.csv (+ Power/Toughness), card-mana.csv, card-wishlist.csv (+ Power Source provenance), matches.csv (played-match record; created on first `/log-matches`, absent until then — deliberately NOT an invariant, since a repo with no logged games is healthy), recommendations.csv (recommendation-outcome ledger; same treatment — accrues from `swap --apply`, absent until the first swap)


## [C-03] Subsystem: Outcomes

Outcomes: scripts/parse_matches.py (Arena `Player.log` → matches.csv, `/log-matches`) — the ONLY subsystem that has seen a game; recommendations.csv + `deck.py feedback` (the recommendation ledger — how `cuts`/`suggest` scored against the swaps you actually applied; written by `swap --apply`, report-only, never fed back into a score). Every other model grades a deck on its LIST; `#: tier:` is a human competitive judgment with no outcome data behind it, which is why the rubric leans on measurable proxies.


## [C-04] Subsystem: Ingest & Enrich

Ingest & Enrich: scripts/import_arena.py, scripts/import_collection.py (authoritative full-collection tracker import — sets exact counts including DOWN), scripts/verify_ingest.py (reads a paste BACK against the library — present? at the expected count? covered by card-mana.csv? — because every failure mode here is a silent undercount and `check_all` structurally cannot see one: a card that never arrived breaks no invariant), scripts/enrich.py, scripts/tag_synergies.py, scripts/build_pool.py, scripts/build_mana.py, scripts/reconcile_crafts.py, scripts/sheets_sync.py, scripts/scryfall.py (shared resilient Scryfall client), scripts/lib.py


## [C-05] Subsystem: Analysis

Analysis: scripts/deck.py, scripts/query.py, scripts/card.py, scripts/pool.py, scripts/wishlist.py, scripts/validate.py, scripts/check_all.py, scripts/check_rankings.py, scripts/check_keywords.py, scripts/check_colors.py, scripts/check_dfc.py, scripts/check_suggest.py, scripts/check_engines.py, scripts/check_tier.py, scripts/check_themes.py, scripts/check_patterns.py, scripts/check_commands.py, scripts/check_agreement.py, scripts/check_docs.py, scripts/keyword_baseline.txt (acknowledged-but-unindexed mechanics, read by check_keywords.py), scripts/check_roles.py, scripts/role_baseline.txt (acknowledged zero-role cards, read by check_roles.py — see G-67)


## [C-06] Subsystem: Presentation

Presentation: scripts/build_gallery.py, gallery.html, image-manifest.json, scripts/build_dashboard.py, dashboard.html, .github/workflows/pages.yml (Pages deploy), scripts/app.py (optional Flask editor), templates/, Makefile (`make app` launcher / `make check` / `make refresh` — the ONE executable definition of the derived-data rebuild order). The dashboard now also renders a **Recently edited** panel (repo→Arena sync: last-edit date + commit changelog + card-level delta, with a last-edit / net·7d / net·30d "since" toggle — from git, needs `pages.yml` fetch-depth: 0) and a **Standard rotation** panel. The deck grid groups into per-format shelves (Standard / Brawl / Alchemy / …) when the roster spans more than one format, and **nests variant decks under their core** — a core deck's same-format variants render as an always-visible `↳ Variants (N)` strip inside its card (id + name + build-status per row, click opens the variant's modal), so they're clearly grouped yet never hidden; searching a variant still surfaces it as its own card, and a cross-format variant (e.g. `3-brawl`) stays standalone in its own format shelf (families are built per shelf). The page is **mobile-responsive** (single-column grids, wide data tables scroll in-box, a horizontally-scrollable section-nav) and uses **progressive disclosure**: every section collapses — the utility ones (card finder / stale-check / recently-edited / rotation) default CLOSED — a sticky **section-nav strip** jumps to and auto-expands a section with a scroll-spy highlight, and the long lists (wishlist tiers, crafting leverage) cap at ~12 rows with a *show all* toggle while the roster-triage table defaults to the ACTIONABLE decks (the page analog of `deck.py audit --flagged`). The **wishlist** filters by free text (card/target/signal) AND by **wildcard rarity** (M/R/U/C chips, multi-select, mirroring `wishlist.py --rarity`). All of this is template-only (the `#data` island is untouched) and persists in `localStorage`.
The EDITOR's colour filter (`templates/collection.html`) follows the dashboard's chip
contract verbatim — `role="button"` + `tabindex` + `aria-pressed` + Enter/Space, per
`build_dashboard.py`'s `a11y()`. It is the same control, so a second interaction
contract would be a drift bug, not a style choice; the key handler routes through
`.click()` rather than re-implementing the toggle, for the same reason. Its focus ring
is an `outline`, never the border — `.pip.on` already uses border-color for the ACTIVE
state, so sharing it would make focused and selected the same pixel. Pinned by
`tests/test_templates.py`.
The DECK editor's analysis tabs (`templates/deck.html`) had the identical defect and
the identical fix — bare `<span class="tab">`s with a container click handler, so all
four were mouse-only — plus the ARIA structure the dashboard's own tabs still lack:
`role="tablist"` on the strip and `role="tabpanel"` on the output (a `role="tab"`
outside a tablist is invalid ARIA). The output `<pre>` is focusable because it
scrolls. Both editor pages carry a `<main>` landmark and a `:focus-visible` rule
wherever they style `:hover`. **Auditing the SIBLING templates is what found this** —
the pip fix named one file, and the same bug was sitting two files over.


## [C-07] Subsystem: Testing

Testing: tests/ (pytest unit layer over the pure helpers — tests/test_templates.py is the MARKUP-CONTRACT layer over `templates/`, stdlib-`html.parser` only and deliberately NOT a browser test: what a file CAN prove is whether a control is a control at all — role, tabindex, an accessible name, a key handler, `aria-pressed` kept in sync, and a focus ring that uses `outline` rather than the border `.pip.on` already claims. A `<div>` with a click handler and none of those is invisible to a keyboard and to assistive tech, which is how the editor's six colour pips stayed mouse-only through six deferrals of the I-01 fix with every gate green; the perceptual half stays a human walk (Regression Scenario 7); tests/test_cli.py is the CLI ENTRY-POINT layer, the one surface no other gate touches: `--help` on every script in `scripts/` (listed dynamically — a hardcoded count here rotted, so it no longer carries one) plus every deck.py subcommand, asserting no traceback and that argparse scripts exit 0 with usage (F-01/F-12); tests/test_check_commands.py pins the workflow-coverage gate (an unreachable subcommand is reported; a prose mention does NOT count as coverage; a stale or unexplained INTERACTIVE_ONLY entry fails; /roster-review drives the five roster commands and /ingest routes all four ownership writers); tests/test_deck_models.py is the ANALYSIS-MODEL layer — deck_quality_vector (the F10 guard's core, which had no direct test at all), tier_gap, legality_report, interaction_profile, effect_redundancy, deck_needs, deck_role_counts, the pure helpers, and the eight POOL-backed models (owned/craft_role_fillers, functional_theme_options, suggest_lands/mana/interaction, audit_roster, brawl_readiness) — all against a SYNTHETIC card universe and a synthetic pool, so they assert the model's contract rather than the current roster's numbers. Its pool carries a deliberately NON-Standard card and a DFC, because the two `owned_role_fillers` bugs need exactly those: the missing format filter (the owned half of `tier --to` skipping the check its craft sibling applied) and the double-faced row printed twice (`load_card_data` keys a DFC under both its full name and its front face, same display name on both). It also holds the cuts MULTIPLIER wiring anchor — `_cuts_multiplier_adj` being bounded and monotonic says nothing about whether `rank_cut_candidates` calls it, and it did not; the test compares the SAME doubler's keep-score across two decks (with and without feeders) so every other component is held constant. That closes the layer: 21 analysis functions had no direct test, now 0; tests/test_check_patterns.py pins the dead-pattern gate on both historical bug shapes, plus the COMPLETENESS check (an unregistered pattern is reported; structural_distinctiveness and the doubler axes are covered; every `_EXCLUDED` entry names a real attribute) and the `window` corpus form (a `$`-anchored slice pattern matches 0 whole texts and must be exempt); tests/test_check_agreement.py pins the AGREEMENT gate — the stale-registry rule (a pair naming a deleted function fails rather than skips), the weakest-cut pair in BOTH directions (the roster agrees today; a hint monkeypatched to answer differently is reported), that `cut_keep_score` is the one definition both cut rankings read, and the two properties that took the role-filler pair from VACUOUS to real: it must lift the default `limit` (both halves sort cheapest-first then truncate, so the default view is the cheap corner of the filtered set and an illegal card below the cut is invisible) and it must ask about the CARD-ADVANTAGE axis, not interaction alone (the roster's one illegal interaction filler is off-color for every sampled deck, while Deadly Dispute — the card the original bug actually offered — is a card-advantage filler). Both holes were found by mutating the code and watching the check stay green, and all three tests were themselves mutation-tested; tests/test_deck.py is the DECK-ANALYSIS helper layer (the biggest file, and the default home for a `deck.py` pure function) — front_face_cost / mana_value (split-Room-Adventure front-face costs), flex_staleness, the rationale figure audit (the bare-`over` false negative, `_ARROW_AFTER` transition notation, `_figure_is_history` — the `removal`/`craft target` domain-vocabulary suppressions plus the `a 2.44 curve` house phrasing — and the third sweep's three pattern holes: parenthesised figures, number-first figures, `early_drops` with no pattern at all, plus both false-positive classes the sweep produced, the `(N)`-must-close breakdown rule and the quoted-span suppression), the tag/role alignments (`draw cards equal to`, `gain life equal to`, `costs {N} less`, `pay life` scoping); tests/test_lib.py is the SHARED-PRIMITIVE layer over `lib.py` — the accessors every other model routes through, so a regression here is roster-wide: card_colors (the F1/F2 colourless-reads-as-red parse), card_power, owned_qty (the DFC front-face ownership join), distinctiveness_score (tag-rarity, tribe/evergreen-excluded), structural_distinctiveness (oracle-text-shape rescue), card_distinctiveness (max-combine) and _creature_subtypes; back in test_deck.py, parse_pips, role_tally, tier_band, engine_roles, rotation math, _reuse_bonus, hypergeometric consistency math, _cuts_power_adj, _cuts_uniq_adj, _land_synergy_bonus / _land_shortfall_bonus (bounded manabase-recommender nudges), _accel_want / _ramp_restriction_fit / _int_scaling / _int_scaling_boost (needs-model signals), _produces_mana, plan_redundancy_fill (virtual-copies-first), _pips_castable (hybrid-aware target audit), fit_strength (specific-theme-gated KEY + broad-tribe demotion), _home_curve_fit (bounded suggest-homes curve nudge), the color-fixer overlay (_is_color_fixer reading TEXT not tags so an unindexed mechanic can't hide a fixer, the Treasure-reminder exclusion, _fixer_rate's broad-vs-single cost discount, and _weakest_cut refusing to cut a fixer for a fixer), pip_depth_warning / deck_color_sources (the colored-pip DEPTH flag the identity-subset castability test can't see), doubler_axis / doubler_restriction / doubler_support / doubler_boost (the bounded deck-magnitude co-signal for doublers, incl. the LIFEGAIN axis and the plus-N-is-not-a-doubling discriminator), _cuts_multiplier_adj (the cuts-side multiplier term: bounded, zero below the floor, never negative), strict_upgrades (`screen`'s text-containment upgrade test — the extra clause, the non-symmetry, identical-text-is-redundancy, the empty-clause guard against a vanilla incumbent, and the cost ceiling), _central_themes (mechanical sub-theme floor-2 admission), _theme_cosine (generic-damped deck-similarity), the role-classifier under-count fixes (permanent-type-list removal, `counter up to N target`, library-tuck removal, the draw-N/discard-N LOOT exclusion, `half X` draw, the second sweep — bounce to `owner's` hand, edict, X-damage, Aura tuck, mass-edict sweeper, repeatable-upkeep-draw card advantage, damage to each opponent — and the THIRD sweep's card-advantage half: a repeatable draw on any PHASE not just the upkeep, a `whenever`-triggered draw, and the draw-PAYOFF false positive the trigger-comma discriminates against, plus that the under-read channel no longer flags what it now counts) plus a structural assertion that the coverage net is a SUPERSET of the precise patterns and that stripping reminder text kills the Ward false cue without hiding a real miss, protection_effects (real ward/hexproof/indestructible vs a combat pump), rotation_year/rotation_risk (`_SET_ROTATION_OVERRIDE`, calendar-year risk), cost_upside_flags, _drop_cost_themes, section_mismatch, power_threshold_flags (incl. the SCOPE fix: removal/opponent-facing and `total power` sums must not flag), _cites_as_arriving (the reversed-replacement claim, plus the `re.I`-defeated `+X` capital and the "cut for cause" idiom), count_conf (role counts carry their own uncertainty, quantity-weighted), match_paste's TIE-BREAK (drift, then more shared, then lower id — order-independent; the rule the dashboard's JS copy mirrors), _file_memo (reference-table cache: a same-size rewrite and a REPOINTED path both invalidate), deck_shape (wide/tall from text, amplifiers-only), near_duplicates (interchangeable-card groups); tests/test_wishlist.py is the WISHLIST-model layer — wishlist.is_conditional_power, wishlist.power_is_seeded, wishlist._parse_budget / _rank_scores(keep=…) (the budget planner: spec parsing, and that a FILTERED view scores identically to the full one — the subset must exclude the corpus max or the test passes vacuously); tests/test_ingest.py is the INGEST + TAGGING layer over `import_arena.py` / `tag_synergies.py` — import_arena, is_heist_text (TestHeistTheme: cross-sentence matching, the impulse/graveyard-hate exclusions, and the `theft`/`heist` name-collision regression), is_exile_cast_text (TestExileCastTheme: the Adventure type-line enabler, the Warp/Plot/Foretell keyword family, and the cast-from-exile payoffs), keyword_frequencies (distinct cards, not rows — the DFC double-count that let a card-unique flavor keyword escape the noise filter), tags_for (incl. the toughness-matters / noncombat-damage / spell-copy / tribal-payoff mechanical-synergy tags); tests/test_parse_matches.py pins the match parser against the REAL log shape (the seat-derived W/L (and its mirror, so the outcome isn't hardcoded), the skip-and-warn when the `Match to` header is missing, the local-date-beats-UTC-epoch rule, dedup by matchId, `_wilson`'s bounds, the `_MIN_SAMPLE` refusal to print a percentage, and that no userId/playerName ever reaches a row) plus the DECK-ATTRIBUTION layer added when `courseId` turned out to be the avatar cosmetic rather than a deck: `parse_deck_selection` against an `EventSetDeckV3` line BUILT BY SERIALIZING the real nesting (JSON inside a JSON string, timestamps double-encoded on top, compact separators, non-ASCII kept) and truncated at the 600 chars the documented `cut` extraction produces — so the regex path, not `json.loads`, is what the tests exercise; that the response line `<== EventSetDeckV3(<id>)` carries the marker and no payload; that `"EventName":"Play"` is not read as the deck name and the neighbouring `LastUpdated` is not read as `LastPlayed`; the TIME join beating log ORDER on the paste people actually produce (the match grep and the selection grep run separately and concatenated, which hands one deck to the whole session under an order walk); the 12-hour rotated-log bound refusing an ancient selection with a warning rather than borrowing it; a match before every selection staying blank; `resolve_deck`'s three routes, including that the name-prefix regex is case-SENSITIVE and adjacency-bound (the first draft read "07 Earth's Mightiest" as deck "7e") and that a prefix naming no real deck resolves to nothing; and the column migration — a pre-rename `matches.csv` keeps its avatar cells through a read/write round trip, while a genuinely foreign CSV is still refused by the F-02 mirror guard. Every one of those was mutation-tested against the code path it pins; tests/test_verify_ingest.py pins the ingest verifier (lower-bound vs `--exact` authoritative quantities, the DFC front-face key shared by the quantity and INV-02 checks, basics skipped by design, an absent card-mana.csv not blamed on the ingest) AND the rebuild ORDER in the Makefile — asserting `build_pool` precedes `build_mana --pool`, `build_mana` precedes `tag_synergies`, the full-scope flags survive, `--merge` not `--force`, and that the three dependency CLAIMS the order rests on are still true in the code, so a future change fails the test instead of silently invalidating the order; tests/test_recommendations.py pins the recommendation ledger — the cut-percentile math, disagreements-worst-first, that an unrankable row is excluded from n rather than counted as agreement, the call-time path resolution, that a broken model loses its column and not the swap, the STRUCTURAL guarantee that no scoring function reads the ledger (wiring feedback into a score has to delete a test), and TestSegments over the creature/noncreature split — the three-way bucketing, that an `unknown` card is never folded into `noncreature`, that the agreement boundary at exactly pct 0.5 matches `recommendation_summary`, and both directions of the per-segment sample floor. That last pair needs a SYNTHETIC card universe injected via `load_card_data`, and the first draft did not have one: the fixture names are not real cards, so every row bucketed as `unknown`, no split could print, and the floor test passed VACUOUSLY — caught only by mutation-testing the floor away, the same "the subset must exclude the corpus max" trap `test_wishlist.py` records one file over; the SIX 2026-08 batch-6 files close the coverage-hole-is-the-bug-map gap (three of the seven untested scripts carried BS-10, a fourth BS-16): tests/test_reconcile_crafts.py is the INGEST-WRITER layer (a tmp four-CSV world with repointed module paths — dry-run writes nothing, --apply lands the library row + blank INV-02 mana row + wishlist removal with .baks, lower-bound lines can't drop a count, and a front-name DFC paste with an unheld printing resolves via the aliased pool index); tests/test_sheets_sync.py is the SYNC-GUARD layer over BOTH directions with the Google side faked at `_worksheet` — `pull`: header-only and >50%-shrink sheets refused (a zero-row sheet passes validate(), which is the BS-03 case), dry-run default, --allow-shrink escape, invalid rows leave the CSV untouched, a real apply overwrites + backs up + repairs INV-02; and `push`, which had no tests at all until BS3-03 even though it CLEARS the operator's tab before writing — the mirror shrink guard refuses before clearing rather than after, the RAW value_input_option that stops a `=`-leading cell running as a live formula is finally pinned (audit F10), and a READ is proven never to create a worksheet, the bug where a typo'd `--worksheet` added an empty tab to the spreadsheet and then reported it empty; tests/test_validate.py pins INV-01's letter plus a CHARACTERIZATION test that a header-only zero-row library passes by design, naming the shrink guards that exist because of it; tests/test_query_pool.py pins both CLIs' `matches()` (the BS-10 color-set semantics, AND-ed filters, rarity/legalities cells, --role through the lazy deck proxy); tests/test_scryfall.py is the RESILIENCE layer with scripted urlopen and stubbed sleeps (404 is a miss never an outage, a 400 is NEVER retried — one call, "client error" named — 429/5xx/timeout classify transient, recovery after a blip); tests/test_enrich.py pins the F-02 schema refusal before any traffic, the F-11 vanilla no-requeue rule, hand-curated Synergies surviving, and the clean outage abort; back in test_wishlist.py, TestOutageReseed walks the F20 outage-add → re-enrich → re-seed path end to end with a hand-grade-survives control, and TestPowerRangeFlag pins the 0–10 range enforcement (the 78-scores-as-flagged-zero case); tests/test_check_all.py is the GATE-RUNNER mutation layer — every other gate had a "watched it fail" layer and the runner implementing INV-01…04 did not, which is how INV-04's documented malformed-line check turned out not to exist (BS2-14); tests/test_app_editor.py pins the Flask editor's write safety (importorskip'd, so the core tooling keeps its zero-dependency guarantee); tests/test_check_dfc.py pins the G-63 builder SCAN rather than the registry it feeds — that it finds the real builders, that it does NOT flag `suggest_scored`/`suggest_lands`, which iterate the same pool rows building `theme_w`/`deck_curve` without keying on a name, and that dropping a registry entry actually fails; tests/test_writer_mutations.py is the WRITE-PATH mutation layer over lib.atomic_write / backup_path / latest_backup / write_rows — each safety property runs against the real writer AND a mutant with one step removed (no temp file, backup-after-replace, no copymode, no cleanup, a fixed backup name, mtime-based backup selection, the F-02 schema guard disabled), every mutant being a bug this writer actually had; tests/test_gates_fire.py is the WATCHED-IT-FAIL layer for the seven gates that had none — check_colors, check_rankings, check_suggest (728 lines, the largest), check_engines, check_tier, check_keywords and check_themes — closing a gap this file's own sibling asserted was already closed: test_check_all.py's docstring claimed "every other gate has a watched it fail layer" while seven did not, which is the rule it states applied one level up. Each test breaks the model a gate guards and asserts the gate reports it, with a baseline class proving all seven are quiet against the real repo first so a firing is attributable to the mutation; the tests were then themselves mutation-tested by making each hard gate's check() return [] unconditionally (the vacuous-gate shape), which is DETECTED in all five cases — so they catch a dead gate, not merely a broken model. Two mutations had to be measured rather than guessed: an EMPTY theme model makes check_rankings return early ("too few decks to assert a distribution"), so the real model is kept and only the cutoff moved, in both directions; and engine_roles returns {theme: {roles}}, not a set. With it, all fourteen model-sanity gates have a fail-watched layer; tests/conftest.py holds the shared fixtures and path setup every one of these imports through), requirements-dev.txt (pytest, dev-only), pytest.ini, .github/workflows/tests.yml (runs pytest + check_all on push/PR), Makefile (`make test-units`). COMPLEMENTS check_all.py — it stays the pure-stdlib gate; pytest is never required to run the core tooling.


## [C-08] Regression Scenario 1 — ingest a batch

Ingest a batch — `import_arena.py <file>` → **`make refresh`** → `verify_ingest.py <file>`. Expect: check_all clean, gallery card count == library row count, and verify_ingest reporting every pasted card present at the expected count. **`build_mana.py` is not optional when the batch introduced a NEW card** — it has no `card-mana.csv` row until then, so INV-02 fails; this scenario used to omit it (and so did `import_arena.py`'s own "Next:" line), which left the gate red with no hint why (broad-scan F-06). It then carried the steps in the WRONG ORDER for a further cycle (`build_pool.py` after `build_mana.py`), which is why the chain now lives in the Makefile instead of in four disagreeing prose copies. **`verify_ingest.py` is the step nothing else covers:** check_all proves the library is self-consistent, not that it contains what you pasted — a card that never arrived breaks no invariant.


## [C-09] Regression Scenario 2 — analyze a deck

Analyze a deck — `deck.py check|mana|consistency|tribes|stats|shape|legal|cuts|tier|tier --audit-rationale|redundancy|targets|text|verify <id>`, plus `deck.py feedback` (the recommendation ledger; empty until a swap has been applied, and a dry-run `swap` must leave it untouched), the needs-aware recommenders `deck.py suggest <id> --lands|--ramp|--interaction|--needs`, `deck.py screen <id> <names>` (re-scores candidates against the CURRENT list; ★ strict upgrade + ✱ multiplier flags), and roster-wide `deck.py audit` / `deck.py suggest-homes <card>` / `deck.py similar <id>` / `deck.py resolve <names>` / `deck.py rotation` (+ `pool.py --role`). Expect: no traceback; mana is hybrid-aware; consistency reports keepable %/land-drops/cast-on-curve (with the splash / color-hungry fix notes); tribes surfaces type-matters payoffs; legal flags size/copy/format violations; cuts/text print full oracle text; tier shows claimed-vs-floor (and `--audit-rationale` flags a tier rationale citing cut
cards or stale figures); stats reports the protection axis and flags a ZERO; redundancy buckets effects by virtual-copy depth and proposes functional copies first, duplicates as fallback; targets counts, per gated card, how many cards in the list satisfy the gate its text names (`✗ NOTHING` = a dead card, `⚠ thin` = ≤3) — the automated half of the "state the count, then decide" discipline; suggest `--lands`/`--needs` surface the STRUCTURAL fills (fixing · acceleration · interaction, with board-scalers flagged) the theme model can't; audit scores every deck TUNE/craft/review/ok, with `review` reserved for an off-color ABILITY or thin interaction (a hybrid you pay on-color shows as `Ns` in the Cast column but never reaches the verdict); verify diffs a pasted Arena export against the stored deck. Also `python3 scripts/deck.py --help` and one subcommand help — the CLI surface check_all cannot reach.


## [C-10] Deploy Command

**Deploy Command:** Data + local tooling ship by commit/push (no build/release step). The
one deployed artifact is the **roster dashboard**: `.github/workflows/pages.yml` rebuilds
`build_dashboard.py` offline and publishes it to **GitHub Pages on every push to `main`**
(no manual step). Everything else is read/run locally. The generated page is a themed
(dark/light) self-contained view: the BUILD stays offline (embedded data, system fonts,
no CDN), and the page's only online touches are optional/non-blocking — Scryfall hover
images and a ⟳ live re-sync from the Pages URL — always falling back to the embedded
snapshot. `build_dashboard.py` restyles are **template-only**: the data pipeline
(`collect`/`deck_viz`/`craft_rows` → the `#data` island) is the source of truth and must
stay untouched by any restyle (the payload shape is what `deck.py`/`wishlist.py` produce).


## [C-11] Regression Scenario 7 — keyboard-only traversal, in full

Keyboard-only traversal | Subsystem: Presentation & Interface
Steps:
  - In `dashboard.html`, using Tab / Shift-Tab only, reach in order: a color filter
    chip, a quick-filter pill, a roster-table sort header, a section header (collapse
    it with Enter or Space), and a deck's ⤢ detail opener
  - Open the modal, Tab through it, press Escape
  - On a deck card's tab strip (Craft / Stats / Mana / Legal / Cuts), press ← and →
  - Tab to a wishlist card NAME and check the card image appears without a mouse
  - In the DECK editor, remove a card line with its ✕ and watch where focus lands
Expected: every one is reachable with a VISIBLE focus ring; Enter and Space both
activate; ← / → step along a tab strip and switch the panel with it (the strips
became real tablists — container role, tabpanel, aria-controls — at S-2; before
that a screen reader announced "Craft, tab" with no group and no "2 of 5"); the card
preview follows FOCUS as well as hover (S-7, the craft-decision evidence was
mouse-only); removing a row leaves focus on the next row's ✕ rather than falling to
`<body>` (S-6, which used to cost a full re-traversal per cut); Tab inside the modal
cycles within it and never reaches the page behind; Escape closes it and returns
focus to the ⤢ that opened it. Walk the whole scenario once in EACH OS colour
scheme: since S-8 the editor pages carry a light palette and follow
`prefers-color-scheme`, so the walk no longer snaps from a light dashboard into a
forced-dark editor halfway through. This is the acceptance
test for I-01/I-04 — before those, nothing in that list was reachable at all.
Then the EDITOR's half of the same fix (`make app`, `templates/collection.html`):
  - Focus the search box, then Tab — the six colour pips must come next, in W U B R
    G C order, each with a visible ring; Enter and Space both toggle one, Space must
    not scroll the page; the card grid re-filters
Then the DECK editor (`/deck/<id>`, `templates/deck.html`):
  - Tab to the Analysis strip — each of Stats / Mana / Tribes / Suggestions must take
    focus with a visible ring; Enter and Space both run one; the output `<pre>` is
    itself focusable, since it scrolls
Expected: the selected tab is the only one reporting `aria-selected="true"`, and a
save toast is announced (it is a `role="status"` live region). Note the SUCCESS toast
is cut short by the `location.reload()` that follows it — see the follow-on below;
the failure toasts are the readable ones.
Expected: identical behaviour to the dashboard's colour chips, because they are the
same control — `role="button"` + `aria-pressed`, per `build_dashboard.py`'s `a11y()`.
The pips were bare `<div>`s until this landed, so the editor's whole colour filter
was mouse-only. The MARKUP half of this is now pinned automatically by
`tests/test_templates.py` (attributes, key handler, `aria-pressed` sync, focus ring);
what still needs a person is the perceptual part — that the ring is actually visible
and the order actually matches what you see.
