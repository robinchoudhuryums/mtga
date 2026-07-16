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

### Import — ingest an Arena export

```
python3 scripts/import_arena.py batch.txt          # merge a deck/collection export
python3 scripts/import_arena.py deck.txt --skip-basics   # reconcile owned counts from a built deck
```

Parses MTG Arena's `<qty> <Name> (<SET>) <collector#>` export format and merges
it into `card-library.csv`, keyed by Card Name + Set Code + Collector # (one row
per printing). Re-imports take the **max** quantity seen (decks share one
collection, so counts don't sum); `--skip-basics` ignores basic lands so a deck
list can true up owned counts without polluting the collection. Follow with
`enrich.py` to backfill new cards.

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
never written silently. (Add more mappings in `SET_ALIASES` at the top of
`scripts/enrich.py` as you hit them.)

> Requires outbound access to `api.scryfall.com`. Some managed/CI environments
> block it by policy; if so, run enrich locally. No API key needed.

### Tag synergies — populate deck-building tags

```
python3 scripts/tag_synergies.py --dry-run   # preview
python3 scripts/tag_synergies.py             # fill blank Synergies cells
```

Derives tags for the Synergies column from each card's type line (tribal
subtypes, key card types), oracle text heuristics (counters, graveyard,
reanimator, lifegain, removal, burn, ramp, tokens, …), and — when `card-mana.csv`
has been built — **Scryfall's authoritative keyword list** mapped to
deck-building themes (Surveil → `surveil; graveyard`, Convoke → `convoke;
go-wide; ramp`, Escape → `graveyard; recursion`, …). Using Scryfall's per-card
keywords means real-keyword coverage is complete and maintained, not a hand-kept
list; a small `FLAVOR_KEYWORDS` denylist drops Universe-Beyond flavor ability
names (Firaga, Wave Cannon, …) that Scryfall also reports as keywords, so they
don't pollute the tags. Fills only blank cells by default (`--force` regenerates). These make `query.py
--synergy` / `pool.py --synergy` and the gallery filters useful; tags are
hand-editable. Rerun `build_mana.py` then `tag_synergies.py --force` after
importing new cards to refresh keyword-aware tags.

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

### Card pool — reference cards you don't own yet

For deck-building you often want to see options beyond your collection. The pool
is a separate reference of Arena-playable cards (built from Scryfall), kept apart
from your owned inventory. `card-library.csv` stays exactly your collection.

```
python3 scripts/build_pool.py            # (re)build card-pool.csv — Standard-legal Arena cards
python3 scripts/build_pool.py --all      # every Arena-craftable card (~15.8k) instead
```

`card-pool.csv` carries a **Rarity** column (= Arena wildcard cost). Search it
with `pool.py`, which joins against what you own so each result is flagged owned
or craftable:

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
python3 scripts/wishlist.py --add batch.txt   # append an Arena-export batch (enriches each)
python3 scripts/wishlist.py                    # browse the whole wishlist
python3 scripts/wishlist.py --set SOS --rarity rare,mythic   # filter (substring, AND-ed)
python3 scripts/wishlist.py --color R --synergy firebending  # by color/theme
python3 scripts/wishlist.py --target 14        # what you've earmarked for a deck
python3 scripts/wishlist.py --by-set           # PACK OPTIMIZATION: cards per set, by rarity
python3 scripts/wishlist.py --rank             # WILDCARD PRIORITY: theme fit + hand-graded power, blended
python3 scripts/wishlist.py --owned            # cards you've since acquired — prune these
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
packs first. `--rank` is the **wildcard-spend order**. It scores each card on two
independent axes and blends them:

- **Fit** — theme fit (the same idf model as `--suggest-targets`) plus *cross-deck
  breadth* (how many decks it's castable in **and** shares a *specific* theme with;
  generic overlap doesn't count). This is a synergy signal, **not** raw power — an
  idf model can't tell that a generic-tagged planeswalker is a bomb.
- **Power** — the hand-graded 1–10 `Power` column (constructed impact), so those
  bombs aren't buried by a low fit score.

The two are normalized and blended 50/50 into a `combined` score; the list still
groups into fit tiers (A = confident home / real breadth, B = one clear deck,
C = situational). The published wishlist artifact renders the same data with a
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
`card-mana.csv` row so INV-02 keeps holding, drops it from `card-wishlist.csv`, and
lists the decks that reference it so you can re-check buildability. The line's
quantity becomes the owned count (so `4 Scoured Barrens (FDN) 266` sets it to 4).
Dry-run by default; after `--apply`, run `build_gallery.py` + `check_all.py` (or
`/refresh`). This is the fast fix for the **"not in library" undercount symptom**
— a card you own that `deck.py check` still lists as a craft target.

### Deck — manage decks and variations

```
python3 scripts/deck.py list          # every deck + variant, with buildable status
python3 scripts/deck.py wildcards     # roster-wide crafting plan (wildcards to finish decks)
python3 scripts/deck.py check 1a      # owned vs needed + a castability lint (off-color cards)
python3 scripts/deck.py diff 1 1a     # what variant 1a changes vs base deck 1
python3 scripts/deck.py arena 1a      # emit an Arena-importable decklist to paste back
python3 scripts/deck.py stats 1a      # curve, colors, types, cost flags, functional roles
python3 scripts/deck.py mana 1a       # hybrid-aware color requirements + castability lint
python3 scripts/deck.py tribes 1a     # creature-subtype breakdown + type-matters synergies
python3 scripts/deck.py suggest 1a --owned   # pool cards that fit; --owned = 0-wildcard upgrades
python3 scripts/deck.py legal 1a      # construction lint: deck size, copy limits, format legality
python3 scripts/deck.py cuts 1a       # rank the deck's weakest-fit cards as cut candidates
python3 scripts/deck.py flex 1a       # suggested swaps recorded in the file (#~ lines)
python3 scripts/deck.py swap 1a --cut A --add B   # preview deltas + FULL oracle text of both; --apply writes (.bak) + auto-retires stale #~ flex lines
python3 scripts/deck.py apply-flex 1a 2      # promote flex swap #2 into the 60 (--apply writes)
```

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

Each pick also carries a **`Decks` column** — a cross-deck reuse count of how many
of your *other* decks the card is *castable* (its identity ⊆ the deck's colors)
**and** shares a **central** theme with (the deck being analyzed is excluded, so it
can't inflate its own picks). "Central" means a theme carried by at least a quarter
of that deck's most-common theme's copies — so a card that merely grazes a deck on
one incidental tag no longer counts, and the number tracks genuine fit rather than
any single-tag overlap. It's still a rough value-per-wildcard signal (a craft that
fits several decks outranks a one-deck sidegrade) — read it as breadth, not curated
fit. A "High cross-deck reuse" line summarizes the top picks.

By default `suggest` also **filters to the deck's `#: format:`** (using the
`Legalities` column `build_pool.py` writes), so it won't recommend a card you
can't legally play or acquire in that format — a Historic deck gets Historic-legal
picks, a Standard deck gets Standard-legal ones. Override with `--format <fmt>`
(e.g. `--format standard` to check what a Historic brew would need for Standard)
or `--any-format` to turn the filter off. (Requires a legality-aware pool; rerun
`build_pool.py` if yours predates the column.)

`wildcards` reads every deck's craft targets (cards you're short of), prices each
by rarity (= its Arena wildcard, from `card-pool.csv`, with a live Scryfall
fallback for non-Standard cards), and reports three things: per-deck wildcards to
finish (closest-to-done first), the **highest-leverage crafts** (one card that
unblocks multiple decks), and the total wildcards to make the *whole* roster
buildable — deduplicated, since one shared collection means a card is only ever
short by `max(any deck needs) − total owned`.

`stats` also flags **cost nature** — `◊` for cards whose text reduces their cost
or grants flash (convoke/delve/"costs {1} less", so the printed mana value doesn't
mislead), `△` for abilities/modes that carry an added or conditional cost — and
breaks the nonland spells into **functional roles**: a heuristic read of card text
that counts removal / counters / card advantage / ramp / anthems (with an
interaction total), so "light on interaction" is *measured*, not eyeballed.
`mana` and `check` add a **castability lint** that flags any card whose real color
needs fall outside the deck's declared `#: colors:` — a strict off-color pip means
uncastable, an off-color identity (a hybrid you'd pay on-color, or an off-color
ability) is a softer heads-up. `tribes` reads oracle text to surface
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
central its synergy themes are to the deck, whether it fills a functional role, and
its tribal contribution — and shows those components so you judge. It doesn't know
your spice/signature cards, so read it as a shortlist, not a verdict; pair it with
`suggest` and preview the result with `swap`.

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
```

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
on its tile; or **⤺ Revert last save** to undo. It binds to `127.0.0.1` only — a
personal, local tool, so there's no auth.

**Every change is safe by construction:** the new rows are written to a temp file
and run through `validate.py` first; only if that passes is the current CSV backed
up to a timestamped `.bak` (gitignored) and then atomically replaced. Bad input —
a non-numeric quantity, a duplicate printing — is rejected before anything is
written, so the inventory can't be corrupted, and any change is one `.bak` away
from undo (which is exactly what Revert does). Adding a card also appends a
`card-mana.csv` row, so the integrity gate's INV-02 keeps holding; run
`build_mana.py` (or `/refresh`) afterwards to fill in its real mana cost/keywords.

**Deck editing** lives under the same app: the **Decks →** link opens a deck list
(with live buildable status), and each deck opens an editor where you change
quantities, add/remove cards, and see **live buildability** (owned vs. needed,
short/missing) update as you type. Saving writes the deck's `.txt` file through
the same safe path — validated (the file must re-parse with every card line
intact, INV-04), backed up to a `.bak`, atomically replaced — and it preserves
the file's `# Creatures` / `# Lands` section comments. The editor also lets you
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
header but bad rows can't corrupt the inventory. Setup details are in the
docstring at the top of `scripts/sheets_sync.py`. (Since the CSV is the
interchange format, you can also import/export manually in Sheets without this.)

## Typical workflow

1. Add rows to `card-library.csv` (Card Name + Set Code + Quantity is enough).
2. `python3 scripts/enrich.py` to backfill card details from Scryfall.
3. `python3 scripts/validate.py` to confirm the file is clean.
4. `python3 scripts/query.py …` while brewing; `python3 scripts/deck.py …` to
   check buildability.

## Integrity check & workflow commands

`python3 scripts/check_all.py` is the project's integrity gate — it verifies the
invariants in [`CLAUDE.md`](CLAUDE.md) (CSV structure, `card-mana.csv` coverage,
derived files present, decks parse) plus a **ranking-model sanity check**
(`check_rankings.py`, above), and exits non-zero on any hard break. A
SessionStart hook runs it (quiet) so drift surfaces immediately.

Claude Code slash commands live in `.claude/commands/`:

- **Project:** `/check` (integrity), `/refresh` (rebuild derived data),
  `/add-deck` (ingest a pasted deck), `/tune-deck` (deck-building analysis).
- **Audit (from claude-workflow-tools):** `/broad-scan`, `/broad-implement`,
  `/sync-docs`, `/health-pulse` (quick directional read), `/roadmap` —
  project-agnostic; they read the **Cycle Workflow Config** in `CLAUDE.md` (Test
  Command = `check_all.py`, Health Dimensions, Subsystems, Invariant Library) for
  all project specifics. See also [`ROADMAP.md`](ROADMAP.md).
