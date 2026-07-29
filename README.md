# MTG Arena Card Library

A structured record of Robin's MTG Arena collection, used as a reference during
deck-building sessions. The collection lives in a single CSV file at the repo
root; a small set of standard-library Python scripts help validate, enrich,
search, and build decks against it.

## The data: `card-library.csv`

One row per unique card **printing** (the same card in two sets = two rows).

| Column           | Notes |
|------------------|-------|
| Card Name        | Full printed name. For MDFC/Adventure cards, front-face name only (unless the back matters for search, e.g. `Cheerful Osteomancer // Raise Dead`). |
| Type             | Full type line, e.g. `Legendary Creature — Merfolk`. |
| Card Text        | Oracle text, verbatim where wording affects rulings. |
| Color(s)         | Color/mana shorthand, e.g. `U`, `B/G`, `Colorless`. |
| Synergies        | Free-text deck-building tags, separated by semicolons. |
| Set Code         | Three/four-letter set code. |
| Collector #      | Collector number within that set printing. |
| Quantity Owned   | Integer count owned. Left **blank** (not `0`) when ownership is unconfirmed. |

Fields containing commas are quoted per standard CSV escaping (the scripts
handle this automatically).

## Tooling

All scripts live in `scripts/` and run on Python 3 with no dependencies, except
`sheets_sync.py` (see below). Run them from the repo root.

### Import — get card data into the library

Five tools write owned-card data, and they are **not** interchangeable: they disagree
about what a quantity means. A deck dump is a **lower bound** (it says what that deck
plays, not what you own); a collection export is **authoritative**. Picking wrong either
undercounts your collection or overwrites it, so `/ingest` exists to route the choice:

| What you have | Tool | A quantity means |
|---|---|---|
| Cards you just crafted or opened | `reconcile_crafts.py` (via `/ingest`) | lower bound — takes `max(existing, line)` |
| A deck list you built in Arena | `import_arena.py --skip-basics` | lower bound |
| A tracker's full-collection CSV/TSV | `import_collection.py` | **authoritative** — sets exact, including down |
| The companion Google Sheet | `sheets_sync.py pull` | authoritative (needs credentials) |
| One card to fix by hand | `make app` | interactive |

```
python3 scripts/import_arena.py batch.txt                # merge a deck/collection export
python3 scripts/import_arena.py deck.txt --skip-basics   # true up owned counts from a built deck
python3 scripts/import_collection.py collection.csv      # dry run; --apply to write
```

`import_arena.py` parses MTG Arena's `<qty> <Name> (<SET>) <collector#>` format and
merges into `card-library.csv`, keyed by Card Name + Set Code + Collector # (one row per
printing). Re-imports take the **max** quantity seen (decks share one collection, so
counts don't sum); `--skip-basics` ignores basic lands.

`import_collection.py` is the counterpart for a full-collection export, and the only tool
here that can **lower** a count — which is why it is dry-run by default, refuses an export
covering under half the library, and leaves cards absent from the export alone unless you
pass `--zero-missing`. Columns are matched by alias against the header (so most trackers
work unchanged) and it stops rather than guessing if it can't identify one; map them with
`--map name=Card,qty=Have`.

**After any import, rebuild the derived data** — a new card has no `card-mana.csv` row,
so INV-02 fails until `build_mana.py --pool` runs. `/refresh` runs the whole chain.

### Validate — catch problems early

```
python3 scripts/validate.py
```

Checks the header, that every row has all 8 columns, that Card Name is present,
that Quantity Owned is blank or a non-negative integer, and that there are no
duplicate printings. Warns about rows still missing Type/Card Text. Exits
non-zero on errors, so it doubles as a pre-commit / CI check.

### Enrich — auto-fill from Scryfall

```
python3 scripts/enrich.py --dry-run     # preview
python3 scripts/enrich.py               # fill blank Type / Card Text / Color(s) / Collector #
```

Looks cards up on [Scryfall](https://scryfall.com/docs/api) in **batches** (75 per
request via the collection endpoint, so a few hundred cards take seconds) and
fills only **blank** fields — your Synergies and Quantity Owned are never
touched. So you can add rows with just a Card Name (and ideally a Set Code) and
let this backfill the rest. Handles multi-face cards (with a single-card fallback
for `Front // Back` names).

**Set codes & collector numbers:** Type, Card Text, and Color(s) are the same
across every printing, so they're filled from any match. Collector # is
printing-specific: it's filled from the batch match when that printing's set
equals the row's Set Code, and otherwise via a targeted `/cards/named?exact=&set=`
lookup of the row's own set (the batch endpoint returns one representative
printing per name — usually the newest, rarely the row's set — so this makes the
number actually resolve for older printings). Set mapping applies first (known
Arena→Scryfall differences, e.g. Arena `DAR` = Scryfall `DOM` for Dominaria). If
neither resolves the row's set, Collector # is left as-is, so a wrong number is
never written silently — and enrich now **reports** the set codes it couldn't
resolve (rather than leaving them blank silently), so an Arena-specific code shows
up as a prompt to add it. (Add more mappings in `SET_ALIASES` at the top of
`scripts/enrich.py` as you hit them.)

> Requires outbound access to `api.scryfall.com`. Some managed/CI environments
> block it by policy; if so, run enrich locally. No API key needed.

### Tag synergies — populate deck-building tags

```
python3 scripts/tag_synergies.py --dry-run   # preview
python3 scripts/tag_synergies.py             # fill blank Synergies cells only
python3 scripts/tag_synergies.py --merge     # ADD new tags to non-blank cells, keep hand edits
python3 scripts/tag_synergies.py --force     # REPLACE every cell (destructive — clobbers hand edits)
```

Derives tags for the Synergies column from each card's type line (tribal
subtypes, key card types), oracle text heuristics (counters, graveyard,
reanimator, lifegain, removal, burn, ramp, tokens, …), and — when `card-mana.csv`
has been built — **Scryfall's authoritative keyword list** mapped to
deck-building themes (Surveil → `surveil; graveyard`, Convoke → `convoke;
go-wide; ramp`, Escape → `graveyard; recursion`, …). Using Scryfall's per-card
keywords means real-keyword coverage is complete and maintained, not a hand-kept
list; a `FLAVOR_KEYWORDS` denylist drops card-*unique* Universe-Beyond flavor
ability names (Firaga, Wave Cannon, and the Marvel signature moves — Trick Arrows,
Radar Sense, Technopathy, …) that Scryfall also reports as keywords, so they don't
pollute the tags. The denylist is guarded in both directions: `check_keywords.py`
flags a new set's keyword that isn't indexed yet, and its `flavor_overreach()`
flags a denylisted word that shows up on several cards — i.e. a *real* mechanic
being suppressed. A recurring mechanic that just isn't themed yet (Vivid, Opus,
Jump, …) belongs in `scripts/keyword_baseline.txt`, not the denylist.
Note the writer emits only the canonical 8 library columns, so point it at
`card-library.csv` only — it refuses any other CSV; refresh the pool's tags with
`build_pool.py --all`. Fills only blank cells by default; **`--merge`** adds
newly-derived tags to non-blank cells while KEEPING existing/hand-curated ones (the
safe refresh mode), and `--force` REPLACES every cell (use it only for a deliberate
destructive regenerate). It also warns when `card-mana.csv` is older than the
library, since new cards would otherwise get keyword-less tags. One theme worth knowing about: **`pay life`** tags a card that spends *your* life for an
effect (351 pool cards). It's scoped to you — "each opponent loses 2 life" is a drain
effect, the opposite card — and it exists because an entire archetype was invisible
without it: Dark Confidant read as a *tangential* fit for the deck built around paying
life, on a shared creature type. **`heist`** is the other one to know: it tags a card that
lets you CAST a card out of an opponent's zone (82 pool cards, 0.52%). Keep it distinct from
the older **`theft`** tag, which means "gain control of" — stealing a permanent already on
the battlefield. They are different mechanics, and naming a new theme after an existing one
merges the two silently, since a tag collision breaks no invariant and `check_all` stays
green. Check `MECHANIC_RULES` for the name before adding a theme. These make `query.py
--synergy` / `pool.py --synergy` and the gallery filters useful; tags are
hand-editable. Rerun `build_mana.py` then `tag_synergies.py --merge` after
importing new cards to refresh keyword-aware tags without losing curation.

### Query — search the collection

```
python3 scripts/query.py --color U --type Merfolk      # blue Merfolk
python3 scripts/query.py --synergy counters            # counters-matter cards
python3 scripts/query.py --set MSH --text "draw a card"
python3 scripts/query.py --min-owned 1 --count         # how many distinct cards you own
python3 scripts/query.py --color G --csv               # emit CSV to pipe elsewhere
```

Case-insensitive substring filters, AND-ed together. Table output by default.
`query.py` searches only cards you **own** (`card-library.csv`); to search the
full set of cards you *could* play, use `pool.py` below.

### Card — inspect one card in full

```
python3 scripts/card.py "morningtide"            # substring / fuzzy match
python3 scripts/card.py "Ghalta, Primal Hunger"  # exact
```

Prints one card's **complete, untruncated oracle text** alongside its mana cost,
**format legality** (from the pool's `Legalities` column), owned quantity,
rarity/wildcard, and which decks run it — in a single view. Use it as the default
way to read a card before grading a cut or recommending a craft: it removes the
temptation to read a *sliced* text dump (which once hid a card's game-changing
clause), and it puts legality up front so a Historic-only card is never mistaken
for a Standard-legal craft (`✗ NOT Standard-legal`). Matches the library first,
then the pool, so it works for unowned cards too.

### Card pool — reference cards you don't own yet

For deck-building you often want to see options beyond your collection. The pool
is a separate reference of Arena-playable cards (built from Scryfall), kept apart
from your owned inventory. `card-library.csv` stays exactly your collection.

```
python3 scripts/build_pool.py            # (re)build card-pool.csv — Standard-legal Arena cards
python3 scripts/build_pool.py --all      # every Arena-craftable card (~15.8k) instead
python3 scripts/build_pool.py --allow-shrink   # permit an empty / far-smaller result to overwrite
```

`build_pool.py` refuses to overwrite an existing pool with an **empty** result (a
query typo, or Scryfall's zero-match 404) or one **less than half** the current row
count — so a mistaken query, or a plain Standard rebuild run over a full `--all`
pool, can't silently destroy the reference. Pass `--allow-shrink` when the shrink
is intentional. (The write itself is atomic, so an interrupted build leaves the
existing pool intact.)

`card-pool.csv` carries a **Rarity** column (= Arena wildcard cost) and a
**`Released`** column (each card's set release date). `build_pool.py` also writes
a `card-pool.build` sidecar stamping when the pool was last built — together these
let `deck.py suggest` reason about **rotation** (Standard holds ~the last 3 years
of sets), flagging picks whose set has aged out even when the static `Legalities`
snapshot still says `standard`. Search the pool with `pool.py`, which joins
against what you own so each result is flagged owned or craftable:

```
python3 scripts/pool.py --color U --text "counter target"    # all blue counters, owned or not
python3 scripts/pool.py --color G --synergy ramp --unowned   # green ramp you'd need to craft
python3 scripts/pool.py --synergy removal --rarity rare,mythic --unowned
python3 scripts/pool.py --type Merfolk --count               # how many exist vs. how many you own
```

Each row shows `×N` (copies owned) or `craft`, plus rarity; the summary totals
the wildcard cost of the craftable results. Rebuild the pool after a new set
releases. For formats outside the stored pool (e.g. a one-off Historic card),
just ask Claude Code — it can query Scryfall live and cross-check your library.

### Wishlist — track craft targets you don't own yet

`card-wishlist.csv` is a curated shortlist of **unowned** cards worth crafting,
slotting into a deck, or building a new concept around — kept apart from your
owned inventory (`card-library.csv`) and the full pool (`card-pool.csv`). Each card
is auto-enriched (Rarity, Color, Type, oracle text, synergy tags) from the pool,
with a Scryfall fallback for cards the pool lacks (e.g. newer double-faced cards,
stored under their full `Front // Back` name). Three columns are yours to annotate:
**Target** (a deck id, `general`, or `concept: …`), **Note** (why it caught your
eye), and **Power** (a 1–10 hand-graded constructed-power score — see `--rank`
below, which blends it with theme fit).

```
python3 scripts/wishlist.py --add batch.txt   # append a batch (enriches + AUTO-seeds a Power estimate)
python3 scripts/wishlist.py                    # browse the whole wishlist
python3 scripts/wishlist.py --set SOS --rarity rare,mythic   # filter (substring, AND-ed)
python3 scripts/wishlist.py --color R --synergy firebending  # by color/theme
python3 scripts/wishlist.py --target 14        # what you've earmarked for a deck
python3 scripts/wishlist.py --by-set           # PACK OPTIMIZATION: cards per set, by rarity
python3 scripts/wishlist.py --rank             # WILDCARD PRIORITY: theme fit + hand-graded power, blended
python3 scripts/wishlist.py --budget "9M 10R 38U 48C"   # optimal craft plan within a wildcard budget
python3 scripts/wishlist.py --budget "3R" --set TMT     # ...scoped to one set (filters apply to --rank/--budget/--by-set)
python3 scripts/wishlist.py --seed-power       # first-pass heuristic estimate for BLANK Power cells (+ --write)
python3 scripts/wishlist.py --owned            # cards you've since acquired — prune these
python3 scripts/wishlist.py --audit-targets    # flag cards whose Target deck can't cast them (hybrid-aware color drift)
python3 scripts/wishlist.py --suggest-targets  # propose a Target per card (confidence-flagged)
python3 scripts/wishlist.py --suggest-targets --write   # auto-fill the confident picks
```

**Auto-targeting workflow (efficient + catch-all-resistant).** `--suggest-targets`
scores each card's fit to every deck by **theme rarity (idf)**: a card that shares
a *specific* theme with a deck (food → Gastromancer, earthbend → Earth Kingdom,
the Ninja `sneak` package → Honor Among Thieves) gets a confident `STRONG`/`ok`
pick, while a card that only overlaps on *generic* themes (`etb`, `counters`,
`tokens`, `lifegain`, …) — the ones central to nearly every deck — is flagged
`review`. That idf-weighting is deliberate: raw theme-overlap makes broad decks
(5-color, or many-themed like Gastromancer) act as **catch-alls** that soak up
anything castable; weighting by rarity kills that. Evergreen keywords (trample,
deathtouch, …) are excluded from the signal too, so an incidental keyword can't
manufacture a false-confident match. The intended loop for a new batch:

1. `wishlist.py --add batch.txt` — append + enrich.
2. `wishlist.py --suggest-targets --write` — auto-fill the `STRONG`/`ok` picks
   into blank `Target`s (never overwrites your edits without `--overwrite`).
3. Judge only the `review` cards from card text — they're the generic-value /
   multi-home / new-concept cards where the tag heuristic genuinely can't decide.

`--by-set` is the gem-spending view: it ranks the sets by how many wishlist cards
each pack could net you (broken down by rarity), so you open the highest-value
packs first. `--rank` is the **wildcard-spend order**. It scores each card on three
independent axes and blends them:

- **Fit** — theme fit (the same idf model as `--suggest-targets`). This is a synergy
  signal, **not** raw power — an idf model can't tell that a generic-tagged
  planeswalker is a bomb.
- **Power** — the hand-graded 1–10 `Power` column (constructed impact), so those
  bombs aren't buried by a low fit score.
- **Breadth** — cross-deck reuse (the `use` column, ★ at ≥3): how many decks the card
  is castable in **and** shares a *specific* theme with (generic overlap doesn't
  count). A **bounded** bonus to the blend, so a multi-home craft outranks an equal
  fit+power one-deck sidegrade without ever dominating — craft once, play it
  everywhere (copies are fungible across decks).

A fourth column, **`uq` (ability-distinctiveness, 0–10)**, is *diagnostic* (it does
**not** feed the blend): how distinctive a card's abilities are — ~0 is generic
templating (`etb`/`tokens`/`sacrifice`, the overlap that trips broad synergy checks),
high is a distinctive mechanic. It's the **max of two signals**: **tag-rarity** (how
rare the card's synergy tags are across the pool) and a **structural** read of the
oracle text's shape (an unusual non-ETB trigger, a non-mana activated ability, rule-
bending/replacement language, modality) — so a distinctive card whose ability was
*tagged* generically is still caught by its text (Ragnarok's dies-trigger, a copy
engine), while a truly generic card (low on both) stays ~0. A low `uq` on a `review`
card confirms it's filler; a high `uq` says the tags under-read it (grade from text).
The same metric feeds a **bounded** nudge in `deck.py cuts` (its `Uq` column) — a
generic-ability body sorts up the cut list, a distinctive card is protected —
orthogonal to Power (a vanilla 6/6 is high power, low distinctiveness).

**Lands are scored on a different axis.** A land has no synergy themes, so theme
fit would sink it to ~0; instead `--rank` rates a land on **manabase value** for
its target deck — how much of the deck's colors it actually produces (a WB dual in
a mono-W deck is half-dead), with a bonus for entering untapped — on the same
0–10 scale, then blends that with `Power`. So a dual or verge that fixes a
two-color deck ranks as the real upgrade it is (`sig: manabase (land)`), instead
of being buried under spells.

A craft target whose Standard-legal set rotates this year or next is flagged
**`⚠rot~YEAR`** — a wildcard there won't last, so verify before spending (the timing
is a heuristic from set release; a reprint can read early).

The two are normalized and blended 50/50 into a `combined` score; the list still
groups into fit tiers (A = confident home / real breadth, B = one clear deck,
C = situational). A **`state`** column shows each card's target deck as
`tier·remaining-crafts` (★ = the card helps *finish* a near-complete deck), so a
wildcard that **upgrades a deck you already play** (low remaining) reads apart from
one that only **builds an unbuilt project** (a big remaining count) — the strategic
overlay the raw combined score can't capture. Cards with a blank `Power` are marked
`pow?` and flagged, since `--add` auto-seeds an estimate you should review. The
published wishlist artifact renders the same data with a
live **fit↔power slider** so you can reweight the ranking on the fly. `--owned`
flags anything you've since crafted so you can drop it (or reconcile it with
`reconcile_crafts.py`, below). Set `Target`/`Note`/`Power` by editing the CSV
directly. Paste a new batch anytime — Claude Code can add it and suggest which
deck each card fits.

**Ranking sanity is gated.** Because the fit model's "specific theme" cutoff is
distribution-sensitive (it once drifted and silently reclassified a real tribe as
"generic", burying bombs), `scripts/check_rankings.py` asserts the cutoff still
behaves — a rare theme stays *specific*, a broad theme stays *generic* — and it
runs inside `check_all.py`, so a scoring regression fails the integrity gate.

### Reconcile crafts — fold newly-crafted cards into the library

```
python3 scripts/reconcile_crafts.py crafts.txt          # dry run (default)
python3 scripts/reconcile_crafts.py crafts.txt --apply   # write, with .bak backups
```

When you craft (or discover you already own) cards, paste them as an Arena export
(`1 Doctor Doom (MSH) 95`). This adds each to `card-library.csv` (a double-faced
card under its **front** name, matching the library convention), adds the matching
`card-mana.csv` row so INV-02 keeps holding (a **blank** row when the card has no
source mana row yet — a later `build_mana.py`/`/refresh` fills the cost), drops it
from `card-wishlist.csv`, and lists the decks that reference it so you can re-check
buildability. For a **new** card the line's quantity is the owned count; for a card
**already** in the library it takes `max(existing, line)`, so pasting a deck-dump
slice (each line a lower bound) can't silently drop a real count — pass
`--set-exact` to set the count exactly (allowing a deliberate decrease). Lines that
look like a card but don't parse are reported (not silently skipped). Dry-run by
default; after `--apply`, run `build_gallery.py` + `check_all.py` (or `/refresh`).
This is the fast fix for the **"not in library" undercount symptom** — a card you
own that `deck.py check` still lists as a craft target.

### Deck — manage decks and variations

```
python3 scripts/deck.py list          # every deck + variant, with buildable status
python3 scripts/deck.py wildcards     # roster-wide crafting plan (wildcards to finish decks)
python3 scripts/deck.py audit         # roster triage: one line per deck — which decks need a tune
python3 scripts/deck.py similar 40    # decks most alike by central-theme overlap (is it distinct?)
python3 scripts/deck.py resolve "Bloom Tender" "2 Island"   # names → deck lines `<qty> Name (SET) #`
python3 scripts/deck.py check 1a      # owned vs needed + a castability lint (off-color cards)
python3 scripts/deck.py diff 1 1a     # what variant 1a changes vs base deck 1
python3 scripts/deck.py arena 1a      # emit an Arena-importable decklist to paste back
python3 scripts/deck.py stats 1a      # curve, colors, types, cost flags, roles + interaction profile
python3 scripts/deck.py mana 1a       # hybrid-aware color requirements + castability lint
python3 scripts/deck.py consistency 1a # opening-hand keepable %, land drops, P(cast on curve) + source fix
python3 scripts/deck.py tribes 1a     # creature-subtype breakdown + type-matters synergies
python3 scripts/deck.py engines 1a    # enabler ↔ payoff balance for the deck's engine themes
python3 scripts/deck.py suggest 1a --owned   # pool cards that fit; --owned = 0-wildcard upgrades
python3 scripts/deck.py suggest 1a --lands --owned  # MANABASE recommender: owned lands that fix your colors (fixing + synergy + scarce-color nudges)
python3 scripts/deck.py suggest 1a --needs   # STRUCTURAL needs the theme model can't see: fixing · acceleration (--ramp) · interaction (--interaction, board-scalers flagged)
python3 scripts/deck.py legal 1a      # construction lint: deck size, copy limits, format legality
python3 scripts/deck.py shape 1a      # wide vs tall, fast vs slow — the structural read themes can't give
python3 scripts/deck.py cuts 1a       # rank the deck's weakest-fit cards as cut candidates
python3 scripts/deck.py screen 1a <names>    # re-score candidate cards against the deck AS IT IS NOW (★ strict upgrade, ✱ multiplier)
python3 scripts/deck.py flex 1a       # suggested swaps recorded in the file (#~ lines)
python3 scripts/deck.py swap 1a --cut A --add B   # preview deltas + FULL oracle text of both; --apply writes (.bak) + auto-retires stale #~ flex lines
python3 scripts/deck.py apply-flex 1a 2      # promote flex swap #2 into the 60 (--apply writes)
python3 scripts/deck.py feedback             # how cuts/suggest scored against the swaps you applied (report-only)
pbpaste | python3 scripts/deck.py verify 1a  # diff a pasted Arena export against the stored deck
pbpaste | python3 scripts/deck.py sync        # reconcile MANY decks from one Arena paste (--apply to write)
python3 scripts/deck.py text 1a              # full oracle text of every card (read before grading)
python3 scripts/deck.py suggest 1a --unowned --full  # picks WITH full text + keywords + flags
python3 scripts/deck.py suggest-homes "Crib Swap"    # which decks a card fits, with a fit-strength label
python3 scripts/deck.py rotation             # roster-wide: which Standard decks run cards aging out (what rotates next); --within N, --years N, --format
python3 scripts/deck.py brawl                 # roster-wide: which decks are closest to a legal Brawl conversion + the best commander for each
python3 scripts/deck.py preflight 1a         # one-call verify: legal + owned + castable + integrity
python3 scripts/deck.py quality 1a --json    # deck-quality vector; --vs FILE diffs a before-snapshot
python3 scripts/deck.py tier 1a              # claimed #: tier: vs the tier its metrics support
python3 scripts/deck.py tier 1a --to A       # gap to A + owned fillers AND craft targets for the short axis
python3 scripts/deck.py tier 1a --audit-rationale  # is the #: tier: argument still true? (cut cards, stale figures)
python3 scripts/deck.py redundancy 1a        # competitive consistency: virtual (functional) copies first, duplicates as fallback
python3 scripts/deck.py history 1a           # the deck's git change history (its changelog); --since YYYY-MM-DD adds the net card change since then
python3 scripts/deck.py quality 1a --at HASH # compare this deck's list at a past commit vs now
```

`feedback` closes the loop on the recommenders. Every ranking model here grades
itself on its own argument; `swap --apply` is the only moment a real add/cut
*decision* is observable, so it now appends a row to `recommendations.csv` recording
where `cuts` ranked the card you cut and whether `suggest` surfaced the card you
added. The report **leads with the disagreements** — swaps where the model wanted to
keep the card you cut — because an *agreement* is contaminated: you read the shortlist
before deciding, so a high agreement rate partly measures the list's influence rather
than its accuracy. A disagreement is a case the model got wrong either way. Below ~20
swaps it refuses to compute a rate at all.

The rate is **split by creature vs noncreature cut**, because one pooled number hid a
two-fold difference: at 52 swaps the pooled figure read 63%, while noncreature cuts
agreed 90% and creature cuts sat at 45% — a coin flip. The cause is that `cuts` scores a
card by *summing* theme weights over its tags with no normalization for tag count, and
creatures carry roughly twice as many tags as noncreature spells (tribes, keywords and
ability tags), so they are systematically protected from the cut list. Normalizing was
simulated across all 64 decks and does not fix it, so this is reported rather than
re-weighted: **on a creature-heavy deck, treat the cut ranking as a shortlist rather
than a signal** and grade from the printed oracle text. It is **report-only and never feeds back
into a score** — the scoring terms are bounded and gated by `check_suggest` so they
can't silently reorder a tuned deck, and an automatic re-weighting would defeat that
invisibly. Note that "add not surfaced" is expected to be common: `suggest` filters to
cards sharing a synergy theme, so it is structurally blind to lands and off-theme
removal (that's what `--lands` / `--interaction` / `--ramp` are for).

`audit` is the **roster triage** for when you don't want to full-tune all your
decks at once. It prints one offline line per deck — competitive **`Tier`**
(S/A/B/C/D win-capability, from the deck's `#: tier:` header; sort with
`--by-tier`), ownership drift (`Own`), construction legality (`Legal`), color
strays (`Cast`: `Nu` uncastable / `Ns` identity stray / `Na` of those, an off-color
ABILITY), interaction count (`Int`),
and central-theme count (`Thm`) — then
labels each deck **★ TUNE** (a hard problem: illegal or uncastable cards),
**craft** (just unbuilt), **review** (a soft flag: an off-color **ability** or thin
interaction), or **ok**. Only `Na` reaches the `review` verdict: a stray explained by a
hybrid pip is a card you simply pay on-color — two R/W hybrids in a mono-W deck are
white cards there — whereas an off-color activated ability is dead mana you can't spend.
Counting both had put 22 of 63 decks in `review` with nothing actionable in any of them. It reuses the exact `check` / `legal` / `mana` / `stats`
primitives, so a flag means the same thing it does in those commands — but across
the whole roster in one pass and with no Scryfall calls. Use it to pick the few
decks worth the expensive `/tune-deck` read; `--flagged` hides the `ok` rows.

`text` dumps every nonland card's **full oracle text** with a `⌘ keywords:` line
(Scryfall's per-card keyword list) and a `⚠` on the classes a role/tag label can
miss — board-wide / modal / leaves-play / deck-dependent (converge·devotion·
affinity·X) / ◊·△ alt-cost. It's the "read before grading" step: never judge a
cut/keep/swap from a role label or a truncated field. `deck.py cuts` and `deck.py
suggest --full` print the same text+keywords+flags for cut candidates and for
add/craft picks respectively, so both sides of a swap are graded from text. The
keyword line means a named mechanic (Warp, Increment, …) is surfaced explicitly
rather than skimmed as an ordinary word. `query.py --full` / `pool.py --full` do
the same for a themed deep-read of your owned library or the whole pool.

`cuts` also marks **`⚡ cost-as-upside`**: a card's additional cost reads as a
drawback to every model here, because they all grade a card *in isolation* — but in
the matching deck the same clause is an engine trigger. A kicker that returns a land
re-triggers landfall; a Warp / "when this leaves the battlefield" clause is what moves
its counters onto your threat; a sacrifice cost feeds your outlets. The flag fires only
when the deck's own themes invert the cost, and it never changes the ranking — it tells
you to read the card in context before cutting it.

`cuts` also marks **`✱ multiplier`**, and the reason it had to is worth stating: a
doubler's value lives in the *rest* of the deck, and **both** halves of the cut score
are blind to that — theme fit sees a card with few tags, and role credit sees no
functional role, because "doubles a trigger" is not a role. So Delney, Streetwise
Lookout, which doubles the triggered ability of every creature in a deck's small-body
engine layer, ranked as that deck's **weakest card**. The information was already in
the toolkit: the doubler model was built for `suggest-homes` and scored Delney
correctly, restriction and all. `cuts` simply never asked. It now routes the same
primitives, bounded and worth zero when the deck doesn't feed the axis — a doubler with
nothing to double genuinely *is* cuttable.

**`deck.py screen <id> <names…>`** re-scores a list of candidate cards against the deck
**as it currently stands**. That sounds like `suggest-homes` for a batch, but it exists
for a different failure: a pile graded *once* keeps those verdicts after the plan
changes. A 76-card pile screened against one plan, then re-read only for the cards
someone happened to re-raise, carries expired reasoning forward on everything else —
which is how four genuinely good cards stayed excluded for reasons that had stopped
being true. Re-run it after **any** change of plan, not once.

It also answers a question nothing else asked: is this candidate a **`★ STRICT
UPGRADE`** of a card already in the 60? Prayer of Binding is Liminal Hold plus Flash —
identical cost, identical text — and Liminal Hold was in the deck while Prayer of
Binding sat on the excluded list. The test is deliberately conservative *text
containment*: every clause of the incumbent present in the candidate, same or lower
mana value, and the candidate doing strictly more. Identical text at identical cost is
**redundancy, not an upgrade** — often a good thing. It misses most real upgrades by
design, so its silence is not a verdict.

`sync` is `verify`'s write half, for many decks at once: pipe an export containing one
or many `Deck` blocks and it matches each block to its closest stored deck (the same
auto-match the dashboard's stale-check uses) and **rewrites the drifted files to match
Arena**. Dry-run by default — `--apply` writes each with a `.bak` and the INV-04
re-check. Edits are line-level, so an existing card keeps its printing and its place in
the file and only its quantity changes; the `#:` header, `# Creatures` section comments
and `#~` flex lines survive. If a block matches two variants nearly equally it's flagged
**low confidence** and skipped on `--apply` (re-paste that deck alone, or `--force`).
Before this, spotting drift and repairing it were separate jobs: you read a diff, then
hand-edited each file.

`verify` reconciles a decklist you've edited in Arena against the repo: pipe or pass
its **Arena export** (`<qty> <Name> (SET) <#>`) and it reports **identical** or a
`+/−` differential by card — `+` = the paste has more, `−` = the repo has more. It
compares by card **name and quantity** (printings and basic-land art of the same
card count as a match, since Arena copies are fungible), includes basics, and exits
non-zero when they differ, so it's scriptable.

`suggest` fingerprints a deck by its **colors** — the deck's declared
`#: colors:`, falling back to its cards' mana **costs** (never color *identity*,
so a card's off-color activated abilities don't drag in uncastable picks) — and
its synergy themes (weighted by how central each is), then scores the Arena pool
(`card-pool.csv`) for cards that fit — castable, sharing the deck's themes, not
already in the list — and flags each as owned (`×N`) or `craft` with its wildcard
rarity. Use `--owned` to
scour only what you already have (0-wildcard upgrades sitting in your roster),
`--unowned` for craft targets only, and `--limit N` (or `--limit 0` for no cap)
to size the list. It composes the same synergy tags and color data the rest of
the tooling uses, so brew upgrades fall out of what you already own plus what
you'd craft.

The ranking is **needs-aware**, not just theme overlap: the impact-role credit is
**saturation-discounted** (the deck's 9th removal spell scores far below its 1st, so
`suggest` stops piling onto an effect you're already deep in), the score is nudged by
a bounded **curve factor** (gently favoring a thin cheap slot, penalizing an over-full
one), and a modest **power co-signal** (the wishlist's rarity+role seed) floats a
BOMB up even on a modest theme fit — all bounded so theme fit stays in charge, and
gated so a weighting change can't silently reorder a tuned deck.

Each pick also carries a **`Decks` column** — a cross-deck reuse count of how many
of your *other* decks the card is *castable* (its identity ⊆ the deck's colors)
**and** shares a **specific central** theme with (the deck being analyzed is excluded,
so it can't inflate its own picks). "Central" means a theme carried by at least a
quarter of that deck's most-common theme's copies; "**specific**" means it isn't one of
the generic themes nearly every deck shares (`etb`, `tokens`, `counters`, `lifegain`, …)
or a broad background tribe — unless it's that deck's `#: protect:` build-around spine.
Centrality alone wasn't enough: it left the count saturated (99% of a deck's picks
scored ≥3, and the median pick "fit" 31 of 56 other decks), so the column said nothing.
It's the same gate the wishlist's `use` column applies, so the two breadth signals
agree. Read it as a rough value-per-wildcard signal (a craft that fits several decks
outranks a one-deck sidegrade) — breadth, not curated fit. A "High cross-deck reuse"
line summarizes the top picks.

By default `suggest` also **filters to the deck's `#: format:`** (using the
`Legalities` column `build_pool.py` writes), so it won't recommend a card you
can't legally play or acquire in that format — a Historic deck gets Historic-legal
picks, a Standard deck gets Standard-legal ones. Override with `--format <fmt>`
(e.g. `--format standard` to check what a Historic brew would need for Standard)
or `--any-format` to turn the filter off. (Requires a legality-aware pool; rerun
`build_pool.py` if yours predates the column.)

On top of that static filter, `suggest` layers a **date-aware rotation check**:
using each card's `Released` date and today's date, it marks a pick **`⚠rot`**
when its set is more than ~3 years old (rotated out of Standard, or rotating
soon) — so a stale `Legalities` snapshot can't surface a card you can no longer
play. It also warns when the `card-pool.build` stamp is old (the pool itself may
have gone stale since a rotation), prompting a `build_pool.py` rebuild to refresh
both the legality snapshot and the date stamp.

`wildcards` reads every deck's craft targets (cards you're short of), prices each
by rarity (= its Arena wildcard, from `card-pool.csv`, with a live Scryfall
fallback for non-Standard cards), and reports three things: per-deck wildcards to
finish (closest-to-done first), the **highest-leverage crafts** (one card that
unblocks multiple decks), and the total wildcards to make the *whole* roster
buildable — deduplicated, since one shared collection means a card is only ever
short by `max(any deck needs) − total owned`.

**Split, Room and Adventure cards are read on their FRONT face.** Scryfall stores both
halves joined by `" // "` (Funeral Room is `{2}{B} // {6}{B}{B}`) and you never pay both,
so the merged string over-counts pips — and a split card's *rules* mana value is the
combined total, which is correct but useless for a curve: Funeral Room arrived at **MV
11** and read as a `{B}{B}{B}` turn-5 play when the door you cast is one black pip on
turn 3. `lib.front_face_cost` / `lib.mana_value` fix both, matching the front-face
convention already used for double-faced card ownership.

`stats` also flags **cost nature** — `◊` for cards whose text reduces their cost
or grants flash (convoke/delve/"costs {1} less", so the printed mana value doesn't
mislead), `△` for abilities/modes that carry an added or conditional cost — and
breaks the nonland spells into **functional roles**: a heuristic read of card text
that counts removal / counters / card advantage / ramp / anthems (with an
interaction total), so "light on interaction" is *measured*, not eyeballed. Because
that regex read can silently **under**-count a phrasing it doesn't recognize,
`stats` (and `tier`) also run a **coverage self-audit**: a broad lexical net flags
any card whose text *reads like* interaction / card advantage the classifier didn't
tag ("⚠ Possible UNDER-COUNT — verify"), so a miss becomes an explicit prompt to
read the card rather than a silent gap in the count. It never changes a count — it
tells you where to look. (Working that list is worth the time: the second pass
through it found that the bounce pattern required the literal text "owner hand"
while Magic writes "to its *owner's* hand", so every unconditional bounce spell in
the collection had been scoring zero roles. Fixing that plus six other templatings
moved 34 of 58 decks, all upward. Parenthetical **reminder text** is stripped before
the net runs, because Ward's reminder — "…counter it unless that player pays {2}" —
was reporting every warded creature as a missed answer.) `stats` also prints an
**interaction profile**: the raw
count treats all removal alike, so it breaks interaction down by **speed** (instant
vs sorcery) and by whether it can answer a **noncreature permanent** (planeswalker /
enchantment / artifact), flagging "all sorcery-speed" or "no noncreature answer".

Every role **count carries its own uncertainty**. A heuristic classifier reports a
false negative as a fact — a card it can't parse contributes 0, and `0` reads as
"none" rather than "not detected". So counts render as `7`, `3 +2?` (two more cards
read like that role but couldn't be tagged), or `8 +4? (3 unclassified)`. 52 of 57
decks show uncertainty inline; one of them was graded on interaction 3 when a hand
count said 7.

**`deck.py shape <id>`** answers the structural question themes cannot: **wide or
tall, fast or slow?** `counters` is the same tag whether they all go on one creature
or spread across twelve. It scores token-creation and count-scaling against
*amplifiers* (doubling, equipment pump, "where X is its power") and folds in creature
density, then prints the effect lists — not just the verdict.

`stats` also runs a **power-threshold check**. A payoff that keys on "power 4 or
greater" reads unconditional to a synergy model, but only fires off bodies that meet
the bar on their **printed** stats — and a counters deck full of X-creatures printed
0/0 meets it far less often than it looks. The pool now stores Power/Toughness, so
this is measurable: in deck 40a, Garruk's Uprising sees only 2 of 23 creature copies.
(A creature that grows *after* it enters still won't satisfy an *enters* trigger.)

`stats` (and `tier`) also report a **protection** count — real ward / hexproof /
indestructible / protection-from effects, deliberately narrower than the broad
"Protection / trick" role, which lumps a combat pump in with an actual answer to
removal. It answers a question nothing else measured: *can this deck protect the
permanent it wins with?* A **zero** is flagged, naming the `#: protect:`
build-arounds at risk — an all-in single-threat deck with no ward/hexproof anywhere
in 60 cards used to look perfectly healthy on every view.

`engines <id>` grades the deck's two-sided **engines**: a synergy tag says "sacrifice"
is in the deck but not which cards FEED the engine (outlets/fodder) vs PAY IT OFF
(death triggers). It classifies each card as an **enabler** and/or **payoff** for the
engine themes (sacrifice, counters, tokens, graveyard, lifegain, food) and flags a
lopsided engine — the ⚠ fires only off the trustworthy payoff side ("payoffs but no
enablers" = dead payoffs; "payoff-heavy" = under-enabled). A shortlist that prints the
card lists to grade; `stats` surfaces the flag inline.
`mana` and `check` add a **castability lint** that flags any card whose real color
needs fall outside the deck's declared `#: colors:` — a strict off-color pip means
uncastable; an off-color *identity* is a softer heads-up, labelled with which kind it
is: `(hybrid — paid on-color)`, `(off-color ability)`, or `(cost unknown — run deck.py
mana …)`. `check` stays offline and reads no mana costs, so it reports the third rather
than guessing; `mana` gives the definitive read. `tribes` reads oracle text to surface
**type-matters payoffs** — e.g. a Saga that rewards Krakens/Leviathans/Merfolk/
Octopuses/Serpents will list those types and how many of your creatures qualify —
so cross-type tribal synergies aren't missed.

`legal` is a **deck-construction lint**: it checks deck size against the format
minimum (60, or 100 for Commander-likes), the copy limit (4 of any nonbasic — or 1
in singleton formats like Brawl), and every nonbasic card's legality in the deck's
`#: format:` (using the pool's `Legalities` column; `--format` overrides). Basics
are exempt; a card absent from the pool is reported as *legality-unverified* rather
than failed, and the command exits non-zero on a real construction violation — so a
deck can be checked legal before you paste it into Arena. `cuts` is the counterpart
to `suggest` (which proposes adds): it ranks the deck's nonland cards **weakest-fit
first** as cut candidates, scoring each from data the tooling already computes — how
central its synergy themes are to the deck, whether it fills a functional role
(**saturation-aware**, so a redundant piece sorts up the cut list while the deck's
*only* counterspell keeps full credit and stays protected), and its tribal
contribution — and shows those components so you judge. It doesn't know your
spice/signature cards from the numbers alone, so read it as a shortlist, not a
verdict; pair it with `suggest` and preview the result with `swap`.

To hard-protect a deck's signature/spice cards, add a **`#: protect:`** header —
`#: protect: Thousand-Year Storm; Niv-Mizzet, Visionary` (semicolon-separated,
repeatable across lines; card names contain commas, so `;` is the separator).
`cuts` then keeps those cards **off** the cut list (and lists them as protected),
and `swap --cut`-ing one prints a warning. Use it for the cards a deck is built
around so the tooling never proposes cutting them.

`suggest-homes <card>` answers "which of my decks does this new card improve" —
it scans every deck for the ones where the card is *castable* and shares a
*central* theme, and tags each fit with a **strength** label: **KEY** (shares the
deck's *signature* theme, OR shares a **specific** non-generic theme AND fills an
interaction / card-advantage gap the deck is short on), **role-player** (a secondary
specific theme), or **tangential** (only generic overlap — etb/tokens/lifegain/…,
or a broad background tribe like Human/Hero/Villain, which carry no home signal).
The role-gap KEY is gated on a specific-theme match, so a generically-good removal
or card-advantage card no longer reads KEY in every low-interaction deck it merely
shares an etb/tokens tag with — its broad utility shows up in the wishlist `--rank`
`use` (breadth) column instead. Fits are scoped to decks where the card is **legal
in that deck's `#: format:`** (`--any-format` to disable), the card name resolves
like `card.py` (exact → DFC front → unique substring), and a bounded curve nudge
flags a top-heavy / win-more card as `⚠ top-heavy for this curve` in a low-curve deck. A **rainbow mana fixer** gets a
color-count overlay, since its fixing value scales with the deck's colors — something
theme overlap alone can't see. Fixers are recognised from oracle **text** in explicit
mana or basic-land-type context, deliberately not from a synergy tag: the tag comes from
a hand-kept keyword map, so gating on it meant any fixer built on an *unindexed* mechanic
read as a non-fixer. Bloom Tender and Prismatic Undercurrents both key off Vivid, which
maps to no theme, and both scored as non-fixers while a mediocre 3-mana dork scored as
one. The overlay covers any-color production, a mass grant ("creatures you control have
`{T}: Add one mana of any color`"), color-agnostic spending permission, per-color
production, and a basic-land fetch that scales with your colors. A Treasure token's
parenthetical *reminder* text is excluded — counting it would make ~150 pool cards read
as manabase fixers.

How much the fixer **buys** is then priced in. Broad fixing (several colors at once, or a
grant) is full value at any mana cost; a single any-color source is discounted by what it
costs. So a fixer reads **KEY in a 4+-color deck** only if it clears that efficiency bar
— a 3-mana one-mana-any-color dork gets **role-player** instead — and role-player in a
3-color deck. And the **suggested cut is chosen with the add in view**: the cut ranking
scores theme fit and role credit, neither of which has a fixing term, so a fixer (few
tags, no classified role) used to sort straight to the top of the cut list in exactly the
multi-color decks that need it. Adding a fixer therefore proposed cutting a *better* one.
Incumbent fixers are now excluded when the add is itself a fixer.
A **doubler** (tokens / counters / triggers / lifegain) is weighed against how much
this deck actually has to double — Exalted Sunborn shares `tokens` with a 14-token deck
and a 6-token deck, and theme overlap scored them identically — so its feeder count
drives a bounded fit bump and promotes it to KEY past a threshold. The doubler's own
scope is read off its text, so Delney's "power 2 or less" filters the count rather than
over-crediting it — but only a *power* scope is parsed, so a doubler scoped by creature
**type** is still counted against the whole deck (Splinter, Radical Rat's Ninja-only
trigger doubling reads 27 feeders in deck 20 against a real 12). Treat a `✱ multiplier`
figure on a tribal doubler as an upper bound. The **lifegain** axis was added last, because The Wind Crystal read
as no doubler at all while the list stopped at three; it requires the literal "twice
that much", since a replacement that is *not* a doubling is templated identically
(Angel of Vitality's "plus 1 instead" is +1, not ×2).
Castability here is an **identity subset** test, which says nothing about whether you
can pay the pips: Anti-Venom (`{W}{W}{W}{W}{W}`) read KEY for decks with 10 white
sources, roughly 1% castable on turn five. A cost demanding 3+ strict pips of one
colour is now priced against the deck's real sources and flagged `⚠⚠ 5x{W} vs 10
sources`, with the count that would clear the bar. It's a flag, never a score change.
Rows sort strongest-fit first, print the card's oracle text, and name the single
weakest nonland cut candidate per deck. Because copies are fungible, slot a card into
*every* deck it earns, not one.

`preflight <id>` is the one-call gate the editing skills run before committing: it
folds `legal` (construction) + owned/buildable + castability + a full `check_all`
integrity pass into one structured PASS/FAIL block with a **READY / BLOCKED**
verdict, exiting non-zero only on a hard failure (an illegal deck or broken
integrity — unowned craft targets on a WIP deck are a WARN, not a block).
`quality <id>` computes a **deck-quality vector** (buildable · uncastable strays ·
interaction / card-advantage role counts · curve · central themes); `--json`
snapshots it before a change and `--vs FILE` diffs after, flagging **regressions**
(interaction dropped, castability broke, a central theme lost its last copy, the
curve got heavier) so a cut/swap that *worsens* the deck self-catches. It's a soft
guard — intentional trades are fine — so it warns rather than blocking unless
`--strict`; `--add NAME` warns if a proposed add is only a tangential fit.

`tier <id>` keeps the competitive **`#: tier:` letter honest**. It's a human
judgment (never auto-assigned), but it should be *defensible* against the deck's
metrics — so `tier` shows the claimed letter next to the **tier floor** the
measurable quality vector supports (interaction + card-advantage, castability), and
flags a **mismatch** when the letter sits ≥2 bands above that floor (inflated or
stale) or, conversely, when a deck looks **under-graded**. The floor is blind to
raw card power / bombs / meta, so it deliberately under-rates — a letter one band
above it is fine (that band credits the intangibles); two bands is the red flag. A
roster-wide pass is a **soft, non-gating** `check_all` warning, so an inflated or
stale tier can't hide. The floor is **archetype-aware**: an aggro deck closes on a
fast clock (low curve + cheap threats + reach), not an interaction suite, so for an
**aggro** plan a bounded clock score substitutes for the interaction the floor
otherwise demands — a fast burn deck isn't floored at C for light removal — while
every other plan grades exactly as before. Set the plan with a **`#: plan:
aggro|control|combo|midrange`** header (else it's read from `#: archetype:` or
inferred). See the tier **rubric** in [`CLAUDE.md`](CLAUDE.md).

Add **`--audit-rationale`** to check the *argument*, not just the letter. A
`#: tier:` rationale is prose, so nothing kept it honest as the list changed
underneath it — it can end up arguing from cards that were cut, or quoting figures
the deck no longer has. `deck.py tier <id> --audit-rationale` flags both, and
reports nothing when the rationale is current. It never edits the prose; a stale
argument is how a defensible letter quietly becomes an indefensible one. **You no
longer have to remember to run it** — `check_all` sweeps the whole roster as a soft
warning, and `/apply-changes` and `/tune-deck` run the per-deck form at the moment of
the edit, where a human is present to fix the wording. Correcting a quoted figure to
the live value is a factual correction; only the tier *letter* is a judgment call.

Add **`--to <TIER>`** (e.g. `deck.py tier 30 --to A`) for a **tier-gap diagnostic**:
it reports the exact measurable work to reach that band's floor ("+3 interaction")
and lists the owned, on-color, **0-wildcard** cards that fill the short axis, plus a
pointer to `cuts` for room. It does the *arithmetic*; the card **selection** — which
fillers preserve the engine/identity, what to cut — stays a `/tune-deck` judgment
call (protect signature/spice). `/tune-deck` runs it so a tune aims at a concrete
tier target instead of generic improvement. The gap list shows both **owned**
fillers (0 wildcards) and **craft targets** (unowned, cheaper wildcard first), so
it doubles as a wildcard-spend planner for lifting a deck a tier. **Both lists are
filtered to the deck's `#: format:`** — owning a card is not a licence to play it,
since the pick costs no wildcard but still costs a deck slot. (Only the craft half
checked that at first, which is how Deadly Dispute and Dovin's Veto, neither
Standard-legal, were offered to Standard decks.)

A deck's **change history is git** — no in-file changelog to go unwieldy or drift.
`deck.py history <id>` prints the deck file's commit log (each message states the
thematic + technical *why*), and `deck.py quality <id> --at <hash>` re-scores that
past version's list against current card knowledge and diffs it vs now — so "was my
previous version better, technically?" is answerable directly (interaction / curve /
central-theme deltas), and `git show <hash>:<path>` recovers the full old list.

Decks live under `decks/` as one folder per core deck, with variations as sibling
files (`deck.txt` → id `1`, `1a-*.txt` → id `1a`). Basics are treated as
unlimited. Full format + structure docs are in [`decks/README.md`](decks/README.md).

**Mana analysis (`stats` curve and `mana`) reads `card-mana.csv`** — real mana
costs captured from Scryfall by `build_mana.py`. This matters because the CSV's
Color(s) column stores color *identity*, which can't tell a hybrid `{W/U}`
(payable with either color) from a strict `{W}{U}` (needs both). `deck.py mana`
counts hybrids as flexible, so "how much white do I really need?" gets an honest
answer. Rebuild the data after importing new cards:

```
python3 scripts/build_mana.py          # refresh card-mana.csv from card-library.csv
python3 scripts/build_mana.py --pool   # also cover card-pool.csv names
python3 scripts/build_mana.py --allow-shrink   # permit a deliberate narrowing of scope
```

Like `build_pool.py`, it **refuses to shrink the file by more than half** — this tool
defaults to library-only, so a plain rerun over a pool-scoped file would silently discard
~14k rows (and disable the one-card keyword heuristic, which needs a pool-sized corpus).
Names the batch endpoint can't match — split and room cards like `Life // Death` — get a
front-face `/cards/named` fallback, accepted only when the resolved card is the one asked
for; anything still unmatched is written blank **and reported**, never silently.

### Gallery — a visual, filterable view of the collection

```
python3 scripts/build_gallery.py     # resolve card images + build gallery.html
open gallery.html                    # (macOS) view it in your browser
```

Generates a self-contained `gallery.html`: a **collection dashboard** (totals,
color/type/set breakdowns, and clickable top-synergy chips) above a filterable
grid of your cards with real card art, quantity badges, and set/collector labels.
Search by name/type/text/synergy, filter by color (WUBRG/Colorless) or set, and
sort by name/set/quantity — all in the browser, no server. Card data is embedded
in the file; images are hotlinked from Scryfall's CDN (so you need internet to see
the art, but the file stays tiny and portable).

Image URLs are resolved via Scryfall's batch endpoint (≈4 requests for a few
hundred cards) and cached in `.image-cache.json` (gitignored) so rebuilds are
instant and the canonical CSV is never modified. They're also written to
`image-manifest.json`, which **is** committed — so a fresh clone (or anyone you
share the repo with) can render the art and rebuild with `--no-fetch` offline,
without the gitignored working cache. Use `--no-fetch` to rebuild from the
manifest/cache without touching the network. Rerun after importing new cards.

### Dashboard — an always-on roster view (craft plan + deck analysis)

```
python3 scripts/build_dashboard.py            # writes a self-contained dashboard.html
python3 scripts/build_dashboard.py --out x.html
```

Surfaces the two things that otherwise live only behind a terminal prompt — the
roster-wide **craft plan** (`deck.py wildcards`) and each deck's **analysis** — as
one self-contained page. It opens with a **Roster triage** table (the `deck.py
audit` scorecard): one sortable row per deck — Own / Legal / Cast / Int / Thm — with
a color-coded **★ tune / craft / review / ok** verdict, so you see at a glance which
decks need attention; click a deck to filter the list below to it. Every deck (and
variant) shows its buildable status and a one-click **⧉ Copy Arena import** button
(the clean `deck.py arena` block, for pasting into Arena on mobile); expanding a deck
gives sortable **Craft picks** and a **Wishlist priority** table (the `wishlist.py
--rank` tiers), plus Stats / Mana / Cuts / Legal / Arena panels. The triage and craft
numbers come from the same `audit_deck()` / `suggest_scored()` the CLI renders, so
the dashboard can't drift from the commands.

The page is a **premium dark / light theme** (violet accent; toggle with the ◐ button
or `t`, remembered across visits). Up top, an **analytics band** shows the buildable-ready
%, wildcards-needed by rarity, and color / format / mana-curve distributions across the
whole roster. The deck grid filters by **color pips** or quick filters (Buildable / Needs
mythic / Needs work) and switches to a **Compact** table. A **Crafting-leverage** section
ranks the cards shared by the most decks' craft lists — click one to highlight every deck
it advances — and a **payoff simulator** projects how many more decks become buildable if
you craft each wishlist tier. A **⌘K command palette** (plus `g d`/`g w`/`g p` jumps and
`/` to focus the filter) navigates; hovering a craft- or wishlist-card name shows its
**Scryfall image**; **⤢** opens a per-deck detail modal and **🖨** prints its craft plan.
The 🔗 button copies a deep-link that restores the current filters / view.

It also has a **"Check for stale decks"** panel: paste one deck's Arena export to see
whether it drifted from the stored list, or paste several `Deck` blocks at once for a
roster staleness report (*N in sync · M drifted*, naming the decks to update). Each
paste is **auto-matched to its closest stored deck — variants included** (Arena
exports carry no deck name), then diffed by card name + quantity with printings and
basic-land art treated as fungible — the **same rules as `deck.py verify`**, run
entirely client-side (nothing is uploaded). Use it to spot which decks you've edited
in Arena but not yet updated in the repo (or vice-versa).

Its mirror is the **"Recently edited decks"** panel — the *repo→Arena* direction: the
decks you've changed most recently (from git history), newest first, each showing the
edit date, the card-level change of the most recent edit (with a *last edit / net·7d /
net·30d* "since" toggle), the commit changelog, and a **⧉ Copy Arena import** button to
re-import into Arena. A **"Standard rotation"** panel shows what rotates next (by year,
⚠ SOON) and which decks it hits — the dashboard view of `deck.py rotation`. (Both need
the pool's `Released` column: `build_pool.py --all`; the recently-edited dates need
git history, so `pages.yml` checks out with `fetch-depth: 0`.) When your roster spans
more than one format, the **Decks & variants** grid splits into per-format shelves
(Standard / Brawl / Alchemy / …) so each game-type reads separately.

A **"Find a card"** search box (top of the page) is the dashboard mirror of
`card.py`'s *in decks* line: type any card name and it lists every deck **including
variants** that runs it (with the copy count), each a click-through chip that
filters the deck list to that deck. It searches the same per-deck card multisets the
stale-deck compare uses, entirely in-browser.

**Progressive disclosure** keeps the page from reading as a wall: every section
**collapses** (the utility ones — card finder, stale-check, recently-edited, rotation —
start closed), a **section-nav strip** in the header jumps to any section (auto-expanding
it) with a scroll-spy highlight, and the long lists (wishlist tiers, crafting leverage)
**cap at a dozen rows** with a *show all* toggle. The roster-triage table defaults to the
**actionable** decks (the dashboard analog of `deck.py audit --flagged`). The **wishlist**
filters by free text (card / target / signal) **and by wildcard rarity** — click the
`M`/`R`/`U`/`C` chips (multi-select; empty = all) to scope the craft list to the wildcards
you're spending, the dashboard mirror of `wishlist.py --rarity`. All of this persists in
the same `localStorage` prefs as the theme/filters. The layout is **responsive down to
phone widths** — grids collapse to one column, wide tables scroll inside their own box,
and the section-nav scrolls horizontally.

The **build** is **offline** — it disables `deck.py`'s live-Scryfall fallbacks and reads
only committed data (`card-*.csv` + `decks/`), so it never touches the network and runs
in CI. The **page** stays self-contained (data embedded, system-font stack, no CDN) and
works fully offline; its only online touches are **optional and non-blocking** — Scryfall
hover images, and a **⟳ live re-sync** that pulls the latest published snapshot from Pages
— each falling back to the embedded data if the network is unavailable.

**Hosting it (GitHub Pages).** `.github/workflows/pages.yml` rebuilds the dashboard
and publishes it on every push to `main`, so it stays current at a permanent,
bookmarkable URL with no local setup. One-time operator steps:

1. Make the repo **public** (GitHub Pages on a *private* repo requires GitHub Pro).
2. **Settings → Pages → Build and deployment → Source: "GitHub Actions."**

Once enabled, the site publishes at `https://<owner>.github.io/<repo>/` on the next
push to `main`. Prefer not to host it? The self-contained `dashboard.html` opens
straight from disk — no server, no setup.

### Editing app — edit the collection in your browser (optional)

```
make app                               # one command: venv + install + launch + open browser
# ...or manually:
pip install -r requirements-app.txt
python3 scripts/app.py                  # opens http://127.0.0.1:5000 in your browser
python3 scripts/app.py --port 8000 --no-browser
```

`make app` sets up an isolated `.venv`, installs Flask into it, launches the app,
and opens your browser — so from a fresh clone it's a single command. (Run
manually if you prefer; `--no-browser` skips the auto-open.)

**Run it in the cloud, without a local clone (GitHub Codespaces).** The editor is
a small server that reads and *writes* your CSV/deck files, so it can't run on a
static host like GitHub Pages — but a Codespace is a live git checkout, which is
exactly what it needs:

1. On the repo page, **Code → Codespaces → Create codespace on `main`**.
2. In the Codespace terminal: `make app ARGS='--no-browser'`.
3. When the "port 5000 is available" prompt appears (or via the **Ports** tab),
   open the forwarded URL — the full editor, in your browser.
4. **To keep your edits, commit and push from the Codespace** (`git add -A &&
   git commit -m "edits" && git push`) — the app writes to the Codespace's copy
   of the repo, so unpushed changes are lost when it's deleted.

Codespace port-forwarding is private to your GitHub account, which matters since
the app has no auth. (A public host like Render is a poor fit: its free-tier disk
is ephemeral so edits vanish on restart, edits don't flow back to git, and the
auth-less editor would be exposed publicly.)

A small local Flask app that turns the collection into an **editable** grid: card
art (from `image-manifest.json`), search/color/set filters, and each card's
`Quantity Owned` and `Synergies` as inline fields with live "dirty" highlighting.
Edit the fields and **Save**; **＋ Add card** a new printing (its type/text/color/
synergies auto-fill from Scryfall by exact name); remove a printing with the `✕`
on its tile; or **⤺ Revert last save** to undo. It binds to `127.0.0.1` by default —
a personal, local tool, so there's no auth. Because there's no auth, it **refuses**
to run `--debug` on a non-local `--host` (the Flask debugger would be a remote
code-execution console) and prints a loud warning on any non-local bind. Its write
endpoints are serialized behind a single lock, so two overlapping requests can't
lose an edit.

"No auth" still shouldn't mean "any website can drive it", so every request passes a
small guard: a state-changing request carrying a cross-site `Origin` is rejected
(**CSRF** — most endpoints were only accidentally safe, because a form post can't set
`Content-Type: application/json`, but `/api/revert` takes no body at all, so any page
you visited while the editor was running could have rolled your collection back), and
while bound to loopback the `Host` header must be a loopback name (**DNS rebinding** —
otherwise a hostile hostname resolving to 127.0.0.1 can script the editor and read the
whole collection). Same-origin traffic from the editor's own page, and non-browser
clients like `curl` that send no `Origin`, are unaffected.

**Every change is safe by construction:** the new rows are written to a temp file
and run through `validate.py` first; only if that passes is the current CSV backed
up to a timestamped `.bak` (gitignored) and then atomically replaced. Bad input —
a non-numeric quantity, a duplicate printing — is rejected before anything is
written, so the inventory can't be corrupted, and any change is one `.bak` away
from undo. **Revert** restores the most recent snapshot — snapshotting the current
state to a fresh `.bak` first and swapping the file in atomically, so a revert
can't leave a half-written CSV and is itself undoable. Backups are timestamped to
the microsecond, so two saves in the same second never overwrite each other. Adding
a card also appends a `card-mana.csv` row (only after the library write succeeds),
so the integrity gate's INV-02 keeps holding; run `build_mana.py` (or `/refresh`)
afterwards to fill in its real mana cost/keywords.

**Deck editing** lives under the same app: the **Decks →** link opens a deck list
(with live buildable status), and each deck opens an editor where you change
quantities, add/remove cards, and see **live buildability** (owned vs. needed,
short/missing) update as you type. Saving writes the deck's `.txt` file through
the same safe path — validated (every card line must re-parse to the *exact* same
card it was entered as, INV-04, so a name containing `(` or `#` — which the parser
would read as a set delimiter / comment — is rejected rather than silently
mangled), backed up to a `.bak`, atomically replaced — and it preserves the file's
`# Creatures` / `# Lands` section comments. The editor also lets you
edit the `#:` metadata fields, run **Stats / Mana / Tribes / Suggestions**
analysis tabs (the same `deck.py` output, in-browser), and **＋ New deck** to
create a fresh numbered deck.

Flask is the only part of the toolkit with a dependency; it's isolated in
`requirements-app.txt`, and the core scripts (and `check_all.py` / CI) never
import it.

### Sheets sync — round-trip with Google Sheets (optional)

```
pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export MTGA_SHEET_ID=<sheet id from its URL>
python3 scripts/sheets_sync.py push    # local CSV  -> Google Sheet
python3 scripts/sheets_sync.py pull    # Google Sheet -> local CSV
```

Keeps the CSV and the companion Google Sheet in sync. `pull` overwrites the local
CSV, so the incoming rows are run through `validate.py` on a temp file first (and
the current CSV is backed up to a timestamped `.bak`) — a sheet with a matching
header but bad rows can't corrupt the inventory. `push` writes cells as **RAW**
values, so a field whose text begins `=`, `+`, `-`, or `@` is stored literally and
never evaluated as a spreadsheet formula (a CSV-injection guard, and it also keeps
leading-zero collector numbers intact). Setup details are in the docstring at the
top of `scripts/sheets_sync.py`. (Since the CSV is the interchange format, you can
also import/export manually in Sheets without this — note that a *manual* File →
Import applies Sheets' own formula parsing, which this RAW guard can't cover.)

### Verify an ingest — did the cards you pasted actually land?

```
python3 scripts/verify_ingest.py cards.txt          # after importing
python3 scripts/verify_ingest.py cards.txt --exact  # tracker-export route only
```

Every failure mode in the import path is a **silent undercount**, and `check_all`
cannot see one — it proves the library is internally consistent, and a card that
never arrived breaks no invariant. This reads the paste back and reports, per
card, whether it is present, at the expected count, and covered by
`card-mana.csv` (the INV-02 step that is easy to skip). Double-faced cards pasted
under their full `Front // Back` name resolve to the library's front-name row, and
basic lands are skipped — they are deliberately not in the collection.

`--exact` requires `owned == pasted`; use it **only** for the authoritative
`import_collection.py` route. Every other route treats a line as a lower bound.

### Rebuilding derived data

```
make refresh
```

Runs the whole chain in dependency order: `enrich` → `build_pool --all` →
`build_mana --pool` → `tag_synergies --merge` → `build_gallery` → `check_all`.
The order is a real dependency graph (`build_mana --pool` reads `card-pool.csv`;
`tag_synergies` reads `card-mana.csv`'s keywords), and getting it wrong is quiet
rather than loud — a new set's pool cards end up with no mana row until the next
cycle. The Makefile is the one place it is defined. Slow, and needs Scryfall.

### Matches — record what actually happened (optional)

```
python3 scripts/parse_matches.py session.log            # dry run
python3 scripts/parse_matches.py session.log --apply    # write matches.csv
python3 scripts/parse_matches.py --report               # win/loss per deck
```

Every other tool here grades a deck on its **list**. This one records **games**.
Turn on Arena → Settings → Account → **Detailed Logs (Plugin Support)**, restart
Arena, then extract the two relevant line shapes (`Player.log` is overwritten on
every launch, so grab it before relaunching):

```
p=~/Library/Logs/"Wizards Of The Coast"/MTGA          # macOS
grep -hE 'Match to .*MatchGameRoomStateChangedEvent|"finalMatchResult"' "$p"/Player*.log
```

**Both shapes are required.** The JSON carries the result and both players' seats
but not *which seat is yours* — that appears only in the `Match to <userId>:`
header prefix — so a paste of the JSON alone is skipped with a warning rather than
guessed at (`--me <userId>` overrides). Rows dedupe by Arena's match id, so
re-pasting an overlapping log is safe. No userId or player name is ever stored.

Arena's `courseId` has no derivable relationship to a repo deck id, so the mapping
is learned: put `#: arena: <courseId>` in a deck file (the report lists the
unmapped ones) or pass `--deck <id>` to tag one session. Unmapped matches are kept.

`--report` shows W/L per deck and **refuses to print a percentage below ~20
matches**, with a 95% Wilson interval above that. A win rate separates a broken
deck from a fine one; it will not separate a 55% deck from a 45% one without
hundreds of games. Read it for disasters, not for marginal swaps.

## Typical workflow

1. Add rows to `card-library.csv` (Card Name + Set Code + Quantity is enough).
2. `python3 scripts/enrich.py` to backfill card details from Scryfall.
3. `python3 scripts/validate.py` to confirm the file is clean.
4. `python3 scripts/query.py …` while brewing; `python3 scripts/deck.py …` to
   check buildability.

## Integrity check & workflow commands

`python3 scripts/check_all.py` is the project's integrity gate — it verifies the
invariants in [`CLAUDE.md`](CLAUDE.md) (CSV structure, `card-mana.csv` coverage,
derived files present **and still carrying their own columns** — a pool that lost
its `Rarity`/`Legalities` is a hard failure, not a silent degrade — decks parse)
plus ten **model-sanity checks** that keep the
grading/ranking models from silently drifting: the **ranking model**
(`check_rankings.py`), **color parsing** (`check_colors.py` — also a static scan
banning the naive inline `WUBRG` parse outside `lib.py`), the **DFC ownership-join**
convention (`check_dfc.py` — an owned double-faced card must resolve by its front
face), the needs-aware **suggest/cuts scoring** (`check_suggest.py` — bounded
modifiers, power never overrides theme fit), the **engine classifier**
(`check_engines.py`), the archetype-aware **tier floor** (`check_tier.py` —
non-aggro grades unchanged, the aggro clock only ever raises a band), and
**dead patterns** (`check_patterns.py`). That last one guards this project's
signature bug: a regex that *compiles fine and can never fire*. Every card-text
pattern must match at least one card in the ~15.8k-card pool, and no pattern source
may contain a Python tuple repr like `(0, 2)` — which is what a `{0,2}` quantifier
becomes when an f-string eats it. Both historical instances of that bug (the `{0,2}`
one, and `(?:owner|their) hand` demanding the text "owner hand" while Magic writes
"owner's hand") were invisible to unit tests, because each pattern had been tested
against a string written to match it. The gate found a third on its first run.
Then **workflow coverage** (`check_commands.py` — every subcommand and script must be
reachable from a skill, or exempted with a reason: a capability that works and is never
reached is invisible to every correctness gate above), and **model agreement**
(`check_agreement.py`). That last one covers what the other eight structurally cannot:
**two functions that are each correct and disagree with each other.** Every check above
evaluates a model in isolation, and a divergence exists only *between* models — which is
how `suggest-homes` came to print a "weakest card" cut hint that `deck.py cuts` did not
rank first on **36 of 64 decks**, with every gate green. It registers questions with two
implementations each (the most-cuttable card, a card's format legality, copies owned, the
interaction count, the power seed, owned-vs-craft filler filters) and fails when they
disagree — on the live roster, not a fixture, because a synthetic case only proves the
pair agrees on the example its author wrote. Finally **doc structure**
(`check_docs.py`): CLAUDE.md is the only file a fresh session loads automatically, so
each operative rule lives there and its evidence — the incident, the measurement, the
reasoning — lives in `docs/gotchas.md` under an anchor. That is a hand-kept
cross-reference, so the gate checks the link in BOTH directions (a dangling anchor loses
the evidence; an orphaned section is evidence nothing can reach), asserts the section
headings the vendored workflow commands name verbatim still exist, and caps a bullet's
length so the two files cannot quietly re-fuse. It exits
non-zero on any hard break. It also
emits **soft warnings** (never gating): wishlist target drift (a card whose target
deck can no longer cast it); **new unindexed card mechanics** (`check_keywords.py`);
**theme coverage** — `check_themes.py` flags an owned card whose text plays a theme
it isn't tagged with (a stale tag distorts every recommendation), summarized to one
line; **tier mismatch** — a deck whose claimed `#: tier:` sits ≥2 bands above its
measurable floor; **stale flex lines** — a `#~ -Out | +In` suggestion whose cut card
already left the deck, which nothing else covered (it found five sitting on the roster);
and **stale tier rationales** — a `#: tier:` argument citing a card the deck no longer
runs, or quoting a figure the live quality vector contradicts. That last one is the
cautionary tale: the check EXISTED for a long time and nothing ran it. `deck.py tier
<id> --audit-rationale` could always find these, but only one deck at a time, on
demand, and the instruction to run it after every edit lived in prose no script
executed — so its two siblings above swept the roster every run while it waited to be
remembered, and 13 stale figures across 10 decks piled up with every gate green. Same
shape as the dead-regex bugs it sits next to: a check that cannot fire is not a check.
A SessionStart hook runs the gate (quiet) **and the unit layer** so
drift in either surfaces immediately; `make verify` runs both before you commit.

A **pytest unit layer** (`tests/`) complements the gate — fast, isolated tests that
pin the pure helper functions (color/DFC parsing, mana pips, role tally, tier floor,
engine roles, rotation math, ingest/tagging). It's dev-only: `pip install -r
requirements-dev.txt` then `pytest` (or `make test-units`, or `make verify` for both
gates at once — the integrity check alone passes while a unit test is red); the core tooling and
`check_all.py` stay pure standard library. Both run in CI (`.github/workflows/tests.yml`).

Claude Code slash commands live in `.claude/commands/`:

- **Project:** `/check` (integrity), `/refresh` (rebuild derived data),
  `/ingest` (**start here for any incoming card data** — routes to the right one of the
  five ingest tools, then runs the rebuild chain), `/add-deck` (ingest a pasted deck),
  `/draft-deck` (build a new deck from scratch around a concept), `/tune-deck`
  (deck-building analysis for ONE deck), `/roster-review` (the roster loop — triage,
  rotation exposure, craft plan, Brawl conversions, Arena drift), `/add-cards` (the
  cross-deck FIT PASS for cards you ALREADY own — cataloguing lives in `/ingest`, which
  runs this pass itself whenever an ingest added new cards; reach for it directly to
  re-run placement after a retune, after `tag_synergies` gains a theme, or for a card
  you have owned for months), `/add-wishlist` (intake unowned craft targets to
  the wishlist — enrich, set the home Target, do the cross-deck fit review),
  `/apply-changes` (apply confirmed swaps, run the quality guard, verify + commit).

  The per-deck loop is `/tune-deck` → `/apply-changes`; the roster loop is
  `/roster-review` → pick a deck → the per-deck loop. `check_commands.py` fails the build
  if a command exists that no workflow drives, so this list can't silently fall behind
  the tooling again.
- **Audit (from claude-workflow-tools):** `/broad-scan`, `/broad-implement`,
  `/sync-docs`, `/health-pulse` (quick directional read), `/roadmap` —
  project-agnostic; they read the **Cycle Workflow Config** in `CLAUDE.md` (Test
  Command = `check_all.py`, Health Dimensions, Subsystems, Invariant Library) for
  all project specifics. See also [`ROADMAP.md`](ROADMAP.md).

  Cycle state lives in `.cycle/` — start a fresh session at
  [`.cycle/NEXT-SESSION.md`](.cycle/NEXT-SESSION.md) (the current diagnosis, the
  agreed next task, and the measurements not worth re-deriving), with `STATE.md` for
  the prose record and `blocks/` for the per-run implementation summaries.
  Note `docs/tooling-improvement-plan.md` is a **completed** cycle's plan kept for
  reference, not instructions.
