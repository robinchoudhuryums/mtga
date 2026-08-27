# Gotchas — the long form

The evidence behind every rule in CLAUDE.md's **Common Gotchas** and **Known Issues**.

CLAUDE.md is auto-loaded by every session, so it carries the operative rule and any
still-live residual; the reasoning, the measurements and the incident that produced each
rule live here, one anchor away. **Nothing was deleted in the split** — every section
below is the original text, moved verbatim.

Read this when you need to know *why* a rule exists, when a rule looks arbitrary and you
are tempted to simplify it, or when you are working directly on the subsystem it governs.
The history is why the rules are trusted: several of them look like over-engineering
until you read the bug that produced them.

`scripts/check_docs.py` gates the link in both directions — a CLAUDE.md anchor with no
section here, or a section here nothing points at, fails the build.


---

# Common Gotchas


## [G-01] Inspect one card with `card.py <name>`, never a truncated slice

**Inspect one card with `card.py <name>`, never a truncated slice.** `scripts/card.py
"<name>"` (substring/fuzzy match) prints a card's **complete, untruncated oracle
text** plus mana cost, **format legality**, owned quantity, rarity/wildcard, and
which decks run it — all in one place. It exists to stop two recurring mistakes:
(1) grading a card from a *sliced* read (piping `query.py --full` through `head`
hid Morningtide's Light's "prevent all damage" clause and mis-graded the cut), and
(2) recommending a craft without a **legality check** (Champion of Rhonas / Chord
of Calling read as green cheat enablers but are Historic-only, not Standard;
Heartfire Hero likewise). Before grading or recommending ANY card in chat, run
`card.py` — the pool's `Legalities` column is authoritative, so "it's in the pool"
is NOT "it's Standard-legal." **In code, never slice a card's text to
grade/classify/rank it** — the rule holds today because every evaluator reads a
whole `Card Text` cell off `load_card_data()` (library→pool) or a pool row, and
truncation appears only in DISPLAY (a first-line preview in a filler list).
`load_card_data()` is the ONE name→card accessor; a `lib.full_card_text()` was once
added as a dedicated funnel but never acquired a caller (every evaluator already
holds a carddata dict, and a second cache of the same column is worse than one), so
it was removed rather than left as dead code the docs pointed at (broad-scan F-07).
Note `load_card_data` resolves library-first, so a library row with BLANK text would
shadow a populated pool row — harmless today (all 6 blank-text rows are genuinely
vanilla in both files) but the thing to check if an evaluator ever reads a card as
text-less.

### Its key convention is not the CSV convention, and the mismatch fails silently (2026-08)

Every CSV reader in this repo keys on the **exact card name** and exposes the CSV's own
column names (`Card Name`, `Card Text`, `Mana Cost`). `load_card_data()` does neither:

- keys are **lowercased** — `cd["joo dee, one of many"]`, not `cd["Joo Dee, One of Many"]`
- the oracle field is **`text`**, not `Card Text`; the others are `name`, `type`, `colors`,
  `power`, `toughness`

So the natural sweep — `(cd.get(name) or {}).get("Card Text")` — matches **nothing**, for
**every** card, and returns an empty string rather than raising. Written ad hoc during the
deck 52 pass to count scry/surveil sources, it reported **0 sources for all three decks**
and looked like a clean result. It was only caught because the author happened to know Joo
Dee surveils.

**This is the K-13 shape one layer down.** K-13 says a zero-result *search* is an unverified
search, not a fact about the format. This says a zero-result *accessor sweep* is not a fact
about the deck. Both fail the same way: a false negative arrives formatted exactly like an
answer. When an ad-hoc sweep returns zero, spot-check one card you KNOW should match before
believing it.


**The 2026-08 variant came from the INSIDE: `card.py` piped through `sed -n '1,14p'`.**
The command exists so a grader sees the whole card, and its output was truncated by the
grader's own shell pipe — repeatedly, in the same sessions where cards were being graded
from labels (Ouroboroid, Dollmaker's Shop, Crystal Barricade, all corrected by the user).
No tool can stop its caller truncating stdout; what it CAN do is make the truncation
visible, so `card.py` now ends every printout with `━━ end · <name> ━━`. An output without
the closing bar was cut short — treat it as an unread card. The general rule: on a verdict
surface, evidence must be opt-OUT, never opt-in; the same session found `screen`'s oracle
text sitting behind a `--full` flag that no skill and no session had ever passed.

## [G-02] A split / Room / Adventure card's stored cost covers BOTH halves — read the FRONT face

**A split / Room / Adventure card's stored cost covers BOTH halves — read the FRONT
face.** Scryfall joins them with `" // "` (Funeral Room is `{2}{B} // {6}{B}{B}`), and
you never pay both, so reading the merged string over-counts pips for all 292 such
cards in the pool and 15 across the roster. Worse, a split/Room card's *rules* mana
value is the COMBINED total — which is correct and useless: Funeral Room came through
at **MV 11**, inflating deck 42a's curve and making `consistency` read it as a
`{B}{B}{B}` turn-5 play when the door that deck casts is `{2}{B}`, one black pip on
turn 3. **`lib.front_face_cost()`** takes the castable half and **`lib.mana_value()`**
computes MV from one face; `parse_pips` reads the front face and `load_mana`
recomputes MV whenever the cost contains `" // "`. FRONT is the convention, matching
`owned_qty`'s DFC rule — the creature on an Adventure card, the cheap door on a Room —
and Adventure cards already stored the front-face value, so recomputing AGREES with
them and only corrects the split/Room shape. Roster diff when this landed: 18 of 59
decks changed, **every one downward**. Residual 1: a deck that plays a split card mainly
for its BACK half reads cheaper than it plays; grade that from the printed card.

**Residual 2, found while building deck 51 and worse because it sits on the surface a
session is TOLD to trust.** `card.py` prints the mana value stored in `card-mana.csv`,
which for a two-half card is the COMBINED total — so a Room reads far MORE expensive than
it plays, the opposite direction from residual 1. Mirror Room // Fractured Realm displays
`{2}{U} // {5}{U}{U} (MV 10)`, and it was very nearly filed as an unbuildable ten-drop; it
is a `{2}{U}` THREE-DROP whose back door unlocks separately for `{5}{U}{U}`, and you never
pay ten. The analysis paths are all correct — `deck.py stats 51` counts it at MV 3, and
`consistency` prices it off the front face — so the *inspection* surface and the *analysis*
surface disagree about the same card. G-01 tells a session to run `card.py` before grading
anything, which is exactly when this misleads. **Read the printed COST, not the MV,
whenever a name contains `" // "`.** The narrow code fix would be for `card.py` to render
`mana_value(front_face_cost(cost))` and show the combined total only as an aside; until
that lands the rule above is the mitigation.

**Later development: MODAL double-faced cards now store both costs the same way.** A
modal DFC is castable as either face, so it belongs in the same `A // B` convention, and
`build_mana` used to keep only the front — see G-63 for the incident and the wider class.
Two things follow for this rule. Every reader here is unaffected, because they all take
the head of the string via `front_face_cost` and that is still the front face. And a modal
DFC does NOT hit residual 2 above: Scryfall's `cmc` for one is the FRONT face's value
(Bruce Banner is MV 1, not MV 6), so `card.py` prints `{U} // {2}{R}{R}{G}{G} (MV 1)` —
correct on both halves. The combined-MV trap is specific to split and Room cards.


## [G-03] Don't judge a card by printed mana value or a single subtype

**Don't judge a card by printed mana value or a single subtype.** `deck.py
stats` flags cost flexibility (`◊` cheaper / `△` added cost), buckets spells
into functional roles (removal / card advantage / ramp / …, heuristic from
oracle text), and `deck.py tribes` reads oracle text for cross-type synergies
(e.g. a Serpent feeding a Leviathan payoff). `deck.py mana` / `check` also run
a castability lint against the deck's declared `#: colors:`. Read the card text
(stored in the CSV) for real evaluation.


## [G-04] A `#~` flex line rots SILENTLY — `deck.flex_staleness()` is the check

**A `#~` flex line rots SILENTLY — `deck.flex_staleness()` is the check.**
`swap --apply` retires only the lines invalidated by the swap it is PERFORMING, and
`--audit-rationale` reads `#: tier:` / `#: archetype:` prose and never the flex block,
so a line can sit for rounds proposing a cut that already happened. Surfaced by
`deck.py flex <id>` and as a soft `check_all` warning; it found FIVE on its first run
(decks 6, 7, 9 and 38a ×2). Note two of those were **obsolete rather than mis-aimed** —
38a's "add a 2nd protection piece" was written when protection was thin and `stats` now
counts six — so the fix is sometimes to RETIRE the line, not retarget it. Advisory: a
flex line is a human note, so this never edits one.

**BOTH HALVES OF THE LINE ROT, and only one was checked (fixed 2026-08-11).** A `#~`
line is `-Out card | +In card | reason`, and `flex_staleness` only ever verified the
`-Out`. Deck 28 carried `-Triumphant Chomp | +Bushwhack` while Bushwhack was already in
the maindeck — a line proposing an add the deck runs — and `deck.py flex` printed it
without comment. The gap had been written down as a RULE rather than noticed as a bug:
the function's own docstring said "a line with no `-Out` (a pure note, or an add-only
suggestion) is never stale — there is nothing to check it against." There is, namely
whether the deck already runs the `+In`. First roster sweep found **8, of which 7 were
real**; the one false positive was deck 51's `-Krang, Utrom Warlord | +Island | THE 25TH
LAND`, and it produced the exemption: basics are unlimited in Arena, so `+Island` against
a deck already running Islands proposes one more land, not a duplicate. A pure NOTE (no
`-Out` and no `+In`) really does have nothing to check against and is still never stale.

**FIGURES IN `#~ note:` PROSE ARE CHECKED TOO** (`note_figure_staleness`, 2026-08-11),
and the asymmetry with card names is the whole design. The card half was measured first
and DECLINED: 252 absent-card citations across 51 decks of 537 note lines, because a
build log discussing cards the deck does NOT run is correct by construction — the same
reasoning G-27 uses to keep `#: notes:` out of the staleness scan. A bare present-tense
FIGURE is a different object: it is a claim about the CURRENT list wherever it is
written, and deck 50's parked-suggestion note argued from "this deck's whole advantage is
a 3.11 curve with 21 early drops" against a live 3.31 / 16. Funnel: **47 raw matches → 9
reported, 8 genuinely stale.** Most of the suppression was already there (arrow/delta,
quoted spans, cross-deck ids and names, population subjects); three rules were added.

Two of the three are SHARED with the `#: tier:` scan, because the trap is in the figure
PATTERNS both use, and neither had a live instance in tier prose to expose it:

- **A percentage is not an average mana value.** "cast-on-curve 76.7%" matches
  `curve (\d+\.\d+)` and was reported as a 76.7 avg MV, twice, in deck 28's notes.
- **A "draw N" count is not a card-advantage figure.** "sac->draw 2 card advantage"
  matches `(\d+) card[- ]adv`; the 2 belongs to "draw" and the adjacency is a coincidence.

The third is deliberately NOT shared. `_FIGURE_PAST` constrains its cue to 24 characters
before the figure, which is right for `#: tier:` prose (a claim, where history is the
exception) and wrong for a build log (history-dense by construction): deck 50a's "it read
avg MV 4.18 with SEVEN early drops and interaction 4" sits the cue ~48 characters from
the figure it governs. Widening the shared window would loosen every other suppression —
`_figure_is_history`'s own comment says so — so the note scan re-reads the SAME cues
CLAUSE-scoped instead. That preserves the distinction that decided two live cases:
`\bread\b` does not match "reads", so 50a's past "it read" is suppressed while deck 31's
live "role_tally still reads card-adv 1" is still reported.

**Residual, kept rather than papered over with a one-instance cue:** a figure describing
a HYPOTHETICAL configuration reads as a live claim. Deck 26's "the best curve of the
three pass-3 alternatives (avg MV 3.61, early drops 11)" was 1 of the 9 — that number was
true of an option, not of the deck. The fix for that shape is what the warning already
advises: mark it as history.


## [G-05] A swap inherits the cut card's `# section` comment

**A swap inherits the cut card's `# section` comment.** The add takes the cut's line
slot, so it lands under whatever header preceded it — which is how a counter battery
(Broodguard Elite) ended up filed under `# Card advantage`, the section Kiora had
occupied. Harmless to the tooling, but the file then lies to the next reader, and these
files are read far more often than they're parsed. `swap --apply` now warns via
`section_mismatch`. Only UNAMBIGUOUS headers are checked — "Counter DOUBLERS" means
+1/+1 counters, not counterspells, and "Threats"/"Payoff"/"Creatures" are too broad to
contradict — and a card the classifier gave NO role gets softer "verify" wording rather
than a mismatch claim, since a no-role read usually means a lexicon gap, not a weak card.
Advisory: it never moves the line, because that's a human editorial call.


## [G-06] Previewing and applying swaps

**Previewing and applying swaps.** `deck.py swap <id> --cut A --add B` shows a
swap's before/after deltas plus the **full oracle text of BOTH the cut and add
cards** (not just the type line) — so a later ability can't hide behind a
truncated read (this is how M.O.D.O.K.'s board-wide −1/−1 and Momo's modal
leaves-play trigger got missed when grading cuts from a sliced text field).
**Always grade a cut from full oracle text — the `swap` preview or the text
block `cuts` now prints — never from a role/fit label or a `Card Text[:N]`
slice.** **And grade the text against THIS deck's engine, not the card in the
abstract:** a cost or effect that reads as a downside in isolation is often an
*upside* in the matching deck — a "sacrifice an artifact / creature" cost is
cheap and *triggers your payoffs* in a Food/aristocrats deck (Deadly Precision
in deck 21), "attacks alone" can be a finisher while your other creatures hold
back to block (Team Avatar), a kicker unlocks a mode the base card hides (Divine
Resilience → mass indestructible), and a symmetric board wipe is a *reset the
reanimator rebuilds from* (Villainous Wrath / Rise of Sozin). Ask "what does
this do *here*" before calling it weak — repeated mis-grades this session traced
to judging cards in isolation. `--apply` writes with a `.bak` and an INV-04
re-check; if the add card is already in the deck it bumps that line rather than
adding a second line for the same card, and it **auto-retires `#~` flex lines
made stale by the swap** (a line proposing the card you just maindecked, or
cutting a card you just removed) — replacing the first with an `applied` note.
`deck.py apply-flex <id> <n>` promotes a `#~` flex line into the 60. Both
default to a dry run.


## [G-07] Triage the roster before full-tuning it

**Triage the roster before full-tuning it.** `deck.py audit` is the cheap,
offline funnel that answers "which decks actually need a tune" so you don't run
the expensive `/tune-deck` text-read on all 30+ decks. One line per deck reusing
the same primitives the single-deck commands do — ownership drift (`check`),
construction legality (`legal`), color strays (`mana`/`check` castability),
interaction count and central-theme count (`stats`) — labelled **★ TUNE** (hard:
illegal / uncastable), **craft** (unbuilt), **review** (soft: an off-color ABILITY
or thin interaction), or **ok**. `--flagged` drops the ok rows. Each deck also
carries a competitive **`Tier`** (S/A/B/C/D win-capability) read from its `#:
tier:` header — shown as a column and sortable with `deck.py audit --by-tier`
(and a color-coded pill on the dashboard). The dashboard opens
with the same scorecard as a sortable **Roster-triage** table (both render from a
shared `audit_deck()` scorer, so CLI and page can't drift). It's a SHORTLIST
SIGNAL like `suggest`/`cuts`: a flag says "look here," then grade the flagged deck
from `deck.py text` + `/tune-deck` — a review/ok label is not a verdict on the
deck. (A stale `#: colors:` header inflates the `Cast` column — a deck whose header is
narrower than the colors it actually casts shows spurious "uncastable" rows; fixing the
header to the deck's real castable colors clears it, same as it does for `mana`/`check`.)
**The `review` verdict counts only an off-color ABILITY, never a hybrid you pay
on-color** — `_castability` returns `off_ability` as a subset of `off_identity`, and
`audit_deck` reads the subset. Counting every identity stray had saturated the flag:
it fired on 22 of 63 decks, and on ALL 26 flagged decks every flagged card's strict
pips were inside the declared colors, i.e. a measured 0% actionable rate (broad-scan
F-03). Knight's Edge is mono-W and runs two R/W hybrids that are simply white cards
there; Super-Skrull casts for `{1}{B}{B}{B}` but its `{4}{R}` ability is dead in a
deck with no red, and only the second is worth a look. Roster impact: review 22 → 6,
ok 22 → 38. Nothing became invisible — the `Cast` column still shows every stray as
`Ns` (matching `deck.py mana`) and marks the actionable subset `Na`, so the column
says WHY a deck did or didn't reach the verdict. Same saturation shape as audit F-04's
`Decks` column: a flag that always fires reads as working.

**The `Pld` column — the first outcome data on a structural surface, and it is kept
report-only on purpose.** `matches.csv` finally holds real games, and the question it can
support at n=9 is not "which deck wins" but "which decks have never been tested" — 34
decks carry a provisional tier promising a re-grade *after real games*, and this column
says which ones are still waiting. So it is a COUNT, deliberately not a W-L: `--report`
already refuses a percentage below 20 matches, and a `2-2` sitting in a skimmable triage
table is exactly the invitation that refusal exists to decline. Four design rules, each
mutation-tested:

* **It never reaches the verdict.** `played` is added to the returned dict BELOW the
  verdict computation, which does not read it; a test grades the same deck with `{}`,
  `{id: 1}` and `{id: 999}` and asserts every other field is identical. Letting 2 games
  re-sort a roster triage is the failure `_MIN_SAMPLE` exists to prevent, and the same
  reason the protection axis (G-25) and the X-cost advisory (G-60) are kept out of
  `tier_band`.
* **The `played` kwarg is OPTIONAL.** `matches.csv` is deliberately not an invariant, and
  `build_dashboard.py` calls `audit_deck` with explicit kwargs — a required parameter
  would have broken the dashboard build. The loader degrades to `{}` on any failure, and
  that path needed its own test: the ABSENT-file case never reaches the handler (
  `load_matches` checks `os.path.exists` and returns `[]`), so a mutation replacing
  `except: return {}` with `raise` stayed green until a test put a directory where the
  CSV goes.
* **It counts ROWS, not results.** A match with a mangled `Result` cell was still played.
* **An all-`·` column is disambiguated in prose.** Dots mean either "never played" or "no
  record exists", and only one of those is about the decks — so an empty record prints
  "that is a missing RECORD, not 99 untested decks". A count attributed to a deck id the
  roster no longer has is also named, since an orphan would otherwise just quietly stop
  appearing.

One wiring trap is worth its own note, because it made every fixture pass against live
data. `load_match_counts` is `@_file_memo("MATCHES_CSV")`, but `pm.load_matches()`'s
default argument binds `MATCHES_CSV` **at definition time** — so a bare call reads the
real record forever while the memo keys on whatever `deck.MATCHES_CSV` currently points
at. The two disagree, and the loader serves data from a file the cache is not watching:
the exact stale-cache bug `_file_memo`'s own docstring describes for `POOL_CSV`, one
module over. Pass the path explicitly. The path itself lives in `lib.MATCHES_CSV` — one
definition, read by both `parse_matches` (which owns the file) and `deck` (which reports
from it), the same consolidation `BASICS` got.


## [G-08] Stored decks drift from the real Arena decks

**Stored decks drift from the real Arena decks.** The user edits decks in the Arena
app; the repo only updates when someone writes the deck file, so the two silently
diverge (hit this session: deck `12` had been changed to 2× Super Intelligence / −Futurist
Forge in Arena while the repo still showed the old list). Catch it with **`deck.py verify
<id>`** (pipe/paste an Arena export — reports *identical* or a `+/−` diff, printing- and
basic-fungible) or the dashboard's **"Check for stale decks"** panel (paste one or many
`Deck` blocks; it auto-matches each to its closest stored deck — variants included — and
flags the drifted ones). **Then repair it with `deck.py sync`** — the WRITE half of
`verify`: pipe or pass an export containing ONE OR MANY `Deck` blocks and it matches each
to its closest stored deck (same rule as the dashboard panel) and rewrites the drifted
files to match. That "same rule" is now PINNED by tests rather than asserted in a
docstring: the JS copy had drifted on the TIE-BREAK, comparing drift alone with a strict
`<` so an equal-drift tie went to whichever deck came first in iteration order, while
Python preferred more shared cards then the lower id — same paste, two answers, in
exactly the sibling-variant case the low-confidence flag exists for (broad-scan F-08).
Both now sort by `(drift asc, shared desc, id asc)`, and the JS uses `<`/`>` on the id
rather than `localeCompare`, because Python compares CODEPOINTS and locale collation can
ignore the hyphen in an id like `3-brawl`. Dry-run by default; `--apply` writes each with a `.bak` and the INV-04
re-check. Line-level editing, so an existing card keeps its printing and section position
and only its QUANTITY changes, dropped cards lose their line, new cards are appended after
the last card line, and the `#:` header / `# Creatures` comments / `#~` flex lines all
survive. A block matching two variants nearly equally is reported LOW CONFIDENCE and
SKIPPED on `--apply` (rewriting the wrong sibling is the one expensive mistake here) —
re-paste that deck alone, or pass `--force`. Previously the only repair was reading a diff
and hand-editing each file.

**The truncation guard (broad-scan BS2-01, 2026-08-07).** The anti-force-fit floor —
"share at least max(3, 30% of the block's distinct cards)" — is measured against the
PASTE, and a partial paste is a strict SUBSET of its deck, so it passed trivially with
full confidence. Reproduced: the first 8 lines of deck 52 dry-ran as `⟳ #52 — drifted:
0 added / 52 removed`, not low-confidence, and `--apply` would have rewritten the stored
60 down to the fragment with INV-04 green (deck size is not an invariant) and the real
list surviving only as a `.bak`. An Arena export is always the WHOLE deck, and the
largest legitimate shrink a sync performs is trimming an oversized draft (64→60 ≈ 0.94
of the stored total), so `match_paste` now flags a paste under **75%** of the stored
total as `truncated`; `cmd_sync` prints `⚠ TRUNCATED?` with both totals in the dry run
and refuses the write without `--force` — the same handling as a low-confidence sibling
match, because the MATCH is usually right and it is the WRITE that must not happen.

**The same-deck claim guard (BS2-10, same scan).** Blocks are matched independently, so
two pasted blocks could both resolve to ONE stored deck — pasting a 52/52a family where
one variant is retired makes both blocks legitimately match the survivor — and the write
loop then wrote the file TWICE, the second write clobbering the first with only an
intermediate `.bak` between them. The low-confidence rule compares a block against
runner-up DECKS, never blocks against each other, so it could not see this. `cmd_sync`
now claims each stored deck for the first block that matches it; a later block matching
the same deck is reported ("✗ block N: ALSO matched #id, already claimed by block M")
and skipped — re-paste it alone if it is the real list. Exit is non-zero, since
something needs attention.


## [G-09] Legality lint and cut candidates are separate from ownership

**Legality lint and cut candidates are separate from ownership.** `deck.py check`
answers "do I own this deck"; `deck.py legal <id>` answers "is it a *legal* deck"
— size vs the format minimum, the copy limit (4, or 1 in singleton formats), and
each nonbasic's legality in the deck's `#: format:` (from the pool's `Legalities`
column; `--format` overrides). It exits non-zero on a real violation but treats a
pool-absent card as *unverified*, not illegal (so WIP/older-print decks aren't
false-flagged). It's **format-aware for Alchemy and Brawl**: a Standard card that
isn't Alchemy-legal is *rebalanced* (plays as its `A-` version), so `--format alchemy`
notes it rather than flagging it illegal; and a **Brawl/Commander** deck (a singleton
format) enforces the 1-of limit AND validates the `#: commander:` header — it must be
a legendary creature/planeswalker in the deck, and every card's **color identity** must
sit within the commander's (Brawl's defining rule, which is stricter than Standard's
castability check — a `W/R`-identity card is fine in a mono-W Standard deck but illegal
under a mono-W commander). Game-type variants are organized as `<core>-<format>` decks
(e.g. `3-brawl`) — see `decks/README.md`. **`deck.py brawl`** is the roster-wide
counterpart: it ranks every deck by *distance to a legal Brawl conversion* (duplicates
to trim to singleton + cards outside the best in-deck commander's color identity) and
names that commander, so you can see which decks convert cleanest — a shortlist like
`audit`/`rotation`, marking cores that already have a `*-brawl` variant. `deck.py cuts <id>` is the counterpart to `suggest` (adds): it
ranks nonland cards weakest-fit first (central-theme fit + **impact-weighted**
functional role + tribal contribution) **and prints the full oracle text of the top
candidates plus a `⚠ context` flag on deck-dependent mechanics (converge / devotion /
affinity / X-cost) and a `⚠interaction` tag on removal/counter/sweeper rows showing
the deck's interaction count (with a header warning when the deck runs <5)** — so the
shortlist never silently lists the interaction you deliberately tuned in as
"weakest" (a recurring mis-read: Shock / Spell Pierce sorting to the top of a
freshly-firmed removal suite). A card on the deck's `#: protect:` **signature theme
also gets a keep-boost**, so a generic-tagged-but-central theme (e.g. counters in a
deck that protects counter-doublers) isn't mistaken for filler. This is because the
role/fit line is a SHORTLIST SIGNAL, NOT A GRADE: its classifier can miss what a
card does and can't see spice/signature cards. (Role credit is now impact-weighted — removal / card advantage / ramp /
cost-reduction / payoff engines get a bonus via `_role_credit`, so a strong card no
longer floats to the top of the cut list just for being off-theme; two detection
bugs that hid Shuri's cost-reduction and Mjölnir's removal are fixed too. The
residual is inherent: an off-theme power card with **zero** matching themes still
sorts low in a tuned deck — a synergy model can't see raw power, which is why the
oracle text is printed and why wishlist ranking pairs fit with a hand-graded Power.)
**That residual has now been MEASURED, and it is creature-shaped.** `fit` is an
UNNORMALIZED SUM — `for t in tags: fit += theme_w[t]` — so tag count drives the
keep-score, and every co-signal (`_cuts_power_adj` / `_cuts_uniq_adj` /
`_cuts_multiplier_adj`) is bounded to ±3 and cannot reach a term spanning that range.
Roster-wide, **correlation(tag count, keep-rank) = +0.73, positive in 64 of 64 decks**.
Creatures carry ~5.7 tags against ~3.0 for noncreature spells (tribes + keywords +
ability tags), so they are systematically protected — which is why the ledger's
creature segment sits at a 45% agreement rate against 90% for spells.
**Normalizing does NOT fix it, and that was simulated across all 64 decks before the
idea was dropped:** capping at the top-3 themes moves the correlation +0.73 → +0.72 and
changes **1% of top-5 shortlist slots**; mean-of-hits reaches +0.60 and over-rewards a
narrow card that hits its one theme. The effect is not double-counting WITHIN a card —
tag count proxies for "is this card described by the tag vocabulary at all", and a card
matching zero themes gets fit 0 and sorts straight to the top regardless of quality.
So this stays a documented property, reported by `deck.py feedback`, not a re-weighting
— and re-weighting off the ledger is what `tests/test_recommendations.py` structurally
forbids anyway. Practical consequence: **on a creature-heavy deck the cut ranking is a
shortlist, not a signal.**
**The standing fix-hypothesis was TESTED and REJECTED.** The proposal on file was that
bodies compete on stats / evasion / curve slot, that theme-fit structurally cannot see
any of that, and that `card-pool.csv` already carries `Power`/`Toughness` which nothing
in the cut ranking reads — "the most promising unexplored direction." It was
pre-registered (signal defined from Magic first principles before any result was
computed; one evaluation; no coefficient tuned against the outcomes), then scored
against all 31 creature cuts in the ledger on git-reconstructed PRE-SWAP deck snapshots
so both models saw identical input. Results: as a bounded ±3 co-signal it moved 4 cuts
up and 5 down (p=1.00) and left agreement at 48% — **as predicted, because a ±3 term
provably cannot reach a `fit` whose roster median is 44 (IQR 31–59)**. Scaled up to
span that whole IQR it moved 11 up and 16 down (p=0.44) and made agreement slightly
WORSE (48% → 45%). The decisive measurement is the separation check: a cut creature's
body quality (mean 4.83) is indistinguishable from the median body of the creatures
that STAYED in the same deck (5.00), and the cut card was the worse body only 17 of 31
times — **chance, p=0.72**. The creatures you cut are simply not the worse bodies, so
P/T is not the missing signal. Note the first run of this test was itself invalid and
had to be thrown out: the hand-guessed vanilla benchmark `P+T ≈ 2·MV+1` measured 2
points too generous on this corpus and the raw curve-redundancy count punished every
creature in a 24-creature deck, so 14% of bodies clamped at 0 and the scale was
destroyed — recalibrating against the CORPUS (pool median P+T per MV; redundancy as a
SHARE of the deck's creatures) re-centred it at mean 5.21 before the single real run.
What the experiment DID find is that the 45% is not a property of creatures at all:
per deck it runs 0/6, 1/6, 3/6, 2/4, 4/4 — **0% to 100%** — so the figure says more
about which decks happened to be edited than about how `cuts` grades bodies.
`deck.py feedback` now discloses that per-deck breakdown under the weak segment
(`segment_concentration`). A tempting story — deck 46 was rebuilt from scratch during
the ledger window, and a cut during a BUILD means "this didn't make the 60", which is
not the question `cuts` ranks — fits deck 46 (0/6) but **not deck 3 at 1/6**, an
ordinary tune; excluding deck 46 moves the segment only 45% → 56%, still under the
noncreature 90%. Treat all of that as exploratory: 4–6-row subgroups with enormous
overlapping intervals. **The next real move is more ledger data, not another signal.** **Read the printed oracle text (and check any `⚠ context` mechanic
against the deck's actual colors/board), then preview the swap with `swap`
(which re-shows both cards' full text) before recommending or applying a cut.**
Repeated cut mis-grades in past sessions traced to trusting the label instead
of the text — don't. For a holistic add/cut pass, prefer the `/tune-deck`
skill, which protects signature/spice cards and reserves a fun budget. To
hard-protect a deck's signature/spice cards, add a **`#: protect: Card A; Card
B`** header (semicolon-separated — card names contain commas): `cuts` then keeps
them off the cut list and `swap --cut`-ing one warns. Set these for cards a deck
is built around so the tooling never proposes cutting them.


**The two REPORT-only annotations above the cut table, and what each was for.** `cuts`
prints the axis the deck is SHORT on above the ranking, because a `⚠interaction` note
once put four ONE-MANA spells at the top of the cut list of the slowest deck on the
roster — the ranking answered "weakest fit" while the reader was being told the deck
needed interaction, and nothing reconciled the two. And it flags `⌁scales w/ <axis>` for
a card whose printed stats are its FLOOR rather than its value: Cat-Gator reads as a
7-mana 3/2 until you notice its ETB damage counts the Swamps you CONTROL. Neither
changes a score.

**The `#: protect:` keep-boost reads the STRICT spine, and the loose union saturated.**
`rank_cut_candidates` gave a +2 keep-boost to any card sharing `_signature_themes` — the
union of every `#: protect:` card's tags. Measured across the 22 decks that declare one, it
fired on **87% of nonland cards, and 100% in decks 20 and 46**: a boost applied to every
card in a ranking is a constant, carrying no information where it saturates and applied off
a 25-theme union where it does not. It now reads `_strong_signature_themes` (≥2 protected
cards), which fires on 66% — the same fix `check_suggest` anchor 11b forces on
`cmd_suggest_homes`, one caller over, for the same reason. The rescue the term exists for
survives: deck 30 protects counter-doublers and its strict signature is exactly
`{counters}`. Roster diff: 14 of 64 decks re-scored, 4 top-cut candidates moved (deck 36a's
moved OFF Vizier of the Menagerie, one of the fixers the tooling is meant to protect).

### 2026-08-09 — Arena's two Brawl formats, and the alias that was missing

Arena renamed Historic Brawl to plain **"Brawl"** and calls the 60-card version
**"Standard Brawl"**. This repo kept the older names, so the two labels are INVERTED
against the client UI:

| Arena's label | cards | `#: format:` here |
|---|---|---|
| Brawl | 100, singleton, Historic pool | `Historic Brawl` |
| Standard Brawl | 60, singleton, Standard pool | `Brawl` |

Deck 40-brawl (Paradox Drive) is a **Standard Brawl** conversion and correctly carries
`#: format: Brawl`.

The latent bug found while documenting this: `#: format:` is hand-written free text,
and the construction-rule sets (`SINGLETON_FORMATS`, `BIG_DECK_FORMATS`,
`_COMMANDER_FORMATS`) were tested with raw lowercased strings containing SPACES, while
`_FORMAT_SLUGS` — the list used for legality lookup — carries the HYPHENATED
`historic-brawl`. So a deck written `#: format: historic-brawl` matched neither
singleton nor big-deck: a 100-card commander deck would have been given a **60-card
floor and a 4-copy limit**, with `legal` printing a clean bill. Both construction checks
off at once, from a spelling the repo's own slug list uses.

Fixed with `normalize_format()` (lowercase, collapse whitespace, alias
`historic-brawl`/`historicbrawl` → `historic brawl` and `standard brawl` → `brawl`),
applied at every set test in `legality_report`. Pinned by `TestFormatNormalization`,
including a 99-card deck that must not be flagged undersized.

The general shape is one this file already knows: a set-membership test against a
hand-written string is only as good as its alias table, and the failure is silent in
the permissive direction.

**The third refuted fix, 2026-08-27: role-credit reweighting.** Motivated by a real
pattern — right after a tune, the freshly added structural cards top the cut list (Delney
fit 3; Dracogenesis ranked the #1 cut minutes after being added) — the candidate change
was to raise `_role_credit`'s base from 3 to 6 per role. Measured before writing a line of
production code: the tweak fixed **0 of the 7 named mis-ranks** (Delney 1→1, Dracogenesis
1→1, Crystal Barricade 4→4, The Arkenstone 9→9; Ouroboroid moved the WRONG way) while
changing the top-3 cut set of **28 of 116 decks**. The reason is structural, not a matter
of weight: the worst offenders score **zero roles** (`classify_roles` reads text and their
value lives in clauses no pattern covers — G-67's whitelist, deliberately narrow), and any
multiplier of zero is zero. The failures that CAN be addressed were addressed elsewhere:
G-80 fixed the granted-keyword half of thin tag profiles, and the `✚ NEWCOMER` display
annotation names the post-tune inversion without touching a score. The keep-score's
machinery (role credit, saturation, power/uniq/multiplier co-signals) already exists and
is anchored by `check_suggest`; the lesson stands — measure the fix-rate against the churn
BEFORE believing a weight change, because the plausible story ("roles don't feed fit")
was simply false on inspection.

## [G-10] "Not in library" for a card you own is the deck-dump undercount symptom

**"Not in library" for a card you own is the deck-dump undercount symptom.**
`import_arena.py` takes a lower bound per line, so a card can end up
*undercounted or entirely absent* from `card-library.csv` — then `deck.py
check` reports it as a craft target even though you own it. Fastest fix:
`reconcile_crafts.py <arena-export>` — paste the crafted/owned cards as an Arena
export ("1 Doctor Doom (MSH) 95"), and it adds each to `card-library.csv` (DFC
stored under its **front** name), adds the matching `card-mana.csv` row — a
**blank** one when the card has no source mana row yet, so INV-02 always holds
and `build_mana.py`/`/refresh` fills the cost later (audit F8) — drops it
from `card-wishlist.csv`, and lists the decks to re-check. For a card already in
the library it takes `max(existing, line)` so a deck-dump slice can't drop a real
count (`--set-exact` forces the exact/lower value, audit F17); unparseable lines
are reported, not skipped silently. Dry-run by default; `--apply` writes with
`.bak`s; then run `build_gallery.py` + `check_all.py` (or `/refresh`). (The DFC front-vs-full name handling — pool/mana key `A // B`, the
library keys `A` — was the most error-prone part when done by hand.) Alternatives:
`import_arena.py <deck> --skip-basics` (trues up from a built deck), or append the
`card-pool.csv` row manually. Hit repeatedly in practice (Primeval Bounty, Cat
Collector, Inspiration from Beyond, Dion, Atlantis Attacks, the deck 20–22 FDN
cards, The Everflowing Well, …).


### 2026-08-09 — ownership data was wrong four times in one session

Cosmogrand Zenith 1→2, Halana and Alena 1→2, Ruby, Daring Tracker absent→2, Castle Doom
2→3. Every one was found because the user said "I actually have N", not by any gate:
`check_all` cannot see an undercount, because a missing or low count breaks no invariant.

The reason this is a gotcha and not a chore is the Castle Doom case. A dedup pass over
eleven decks was recommending which duplicate crafts to swap out, and deck 48's argument
opened with "the pending third copy is a rare craft that deepens the deck's worst
weakness". The first clause was false — the copy was owned. The recommendation happened
to survive re-testing on the manabase argument alone (Castle Doom's coloured mana is
artifact-spell-only, and the 39% it cannot cast contains the keystone and every removal
spell), but that was luck, not method.

The rule that follows: craft cost is REPORTED, never REASONED FROM. CLAUDE.md's Player
Profile already says to build the optimal list without gating on ownership; this is the
same rule from the other direction — do not let a craft cost enter the argument as a
*reason* either. When a recommendation does depend on ownership, say so explicitly, so
the premise most likely to be false is the one the reader checks first.


### 2026-08-18: `--apply | head -N` silently lost two batches

`reconcile_crafts.py` computed its changes, printed the full report, and only then
called `_bak_write` three times. Every `print()` between those two points is a place the
process can die, and piping to `head -N` guarantees it will: once `head` has taken its N
lines it closes the pipe, the next `print()` raises `BrokenPipeError`, and Python exits 1
**before any file is touched**.

The failure is maximally deceptive. The report that already reached the terminal reads
`Add to library: 2` followed by the card names — indistinguishable from a successful run,
because the one line that would have disambiguated it (`Applied (with .bak backups)`) is
below the `head` cutoff. Two batches were lost this way in one session:

- Nexus of Becoming + Racers' Scoreboard ×2 — found later by a CSV parse, and confirmed
  by `git show` on the commit that claimed to carry them
- Krang & Shredder — found because a follow-up `grep` came back empty

Both were invisible to `check_all`: a card missing from `card-library.csv` breaks no
invariant, which is the same structural blindness `verify_ingest.py` exists to cover. The
`/ingest` skill mandates that verify step; ad hoc `reconcile_crafts` calls outside the
skill have no such backstop, which is how both slipped through.

Reproduced deliberately before fixing: a card referenced in a deck file produces a
`Decks referencing a reconciled card` section after line 6, so `... --apply | head -6`
exits 1 and writes nothing, while the same command with `| head -8` (or any `tail`, which
drains the pipe) completes normally. That is why the failure looked intermittent — it
depended entirely on how many lines the report happened to emit.

**Fix:** the writes now run before the report. A truncated pipe can lose OUTPUT but never
DATA. `test_writes_land_even_when_stdout_dies_mid_report` pins the ordering by raising
`BrokenPipeError` from a monkeypatched `print` partway through and asserting the rows are
on disk anyway; it was watched to fail against the unfixed source first.

**Generalize it:** any script here that both mutates a canonical file and narrates what it
did should do the durable work first. Narration is the part that is safe to lose.
## [G-11] MTG Arena set codes can differ from Scryfall

**MTG Arena set codes can differ from Scryfall** (e.g. Arena `DAR` = Scryfall
`DOM`). `enrich.py` maps known ones (`SET_ALIASES`). It fills a row's Collector #
from the batch match when that printing's set lines up, else via a targeted
`/cards/named?exact=&set=` lookup of the row's own set (the batch endpoint
returns one representative printing per name, rarely the row's set) — and still
never writes a number from an unconfirmed printing: a set it can't resolve
leaves Collector # blank.


## [G-12] WIP decks legitimately show "missing" cards

**WIP decks legitimately show "missing" cards** in `check_all.py` — those are
craft targets not yet owned (e.g. Atlantis Attacks 18/18a). Not a failure.


## [G-13] Regenerate derived data with `make refresh` — never by hand

**Regenerate derived data with `make refresh` — never by hand.** The order is a real
dependency graph (`build_pool.py` is independent, taking keywords straight off the
Scryfall response; `build_mana.py --pool` READS `card-pool.csv`; `tag_synergies.py`
reads `card-mana.csv`'s keywords; `build_gallery.py` last), and it had been written out
in **eleven** places — this line, Regression Scenario 1, `/refresh`, `/ingest`,
`/add-cards`, and printed or docstring'd copies inside `import_arena.py` (×2),
`import_collection.py` (×2) and `reconcile_crafts.py` — of which only `/refresh` had it
right. The rest put `build_pool.py` AFTER `build_mana.py`, `/ingest` claimed it matched
`/refresh` while contradicting it, and `import_arena.py`'s docstring asserted "IN THIS
ORDER" over the wrong one. The first sweep found four and fixed five; the copies inside
SCRIPTS survived it, which is the worse half — a stale doc misleads a reader, a printed
recipe is an instruction someone follows. `tests/test_verify_ingest.py` now fails the
build on any new copy (`_restates_chain`, which distinguishes a RECIPE — both builders
as adjacent invocations or an arrow chain — from the many legitimate one-tool mentions
like "built by build_mana.py", because a check that flagged those would be deleted). Getting
it wrong is QUIET: a newly released set's pool cards get no `card-mana.csv` row until
the next cycle, so they rank with no cost and no keyword tags, and no invariant notices
(INV-02 covers the LIBRARY, not the pool). The Makefile target is now the one
executable definition; the correct order is `enrich` → `build_pool --all` →
`build_mana --pool` → `tag_synergies --merge` → `build_gallery` → `check_all`. Use **`--merge`** (adds
newly-derived tags without removing existing/hand-curated ones), not `--force`,
which REPLACES every cell and clobbers hand edits (audit F10). `tag_synergies`
also warns when `card-mana.csv` is older than the library — rebuild it first or
new cards get keyword-less tags (audit F21).


## [G-14] Scryfall egress

**Scryfall egress**: needs `api.scryfall.com` + `*.scryfall.io` allowed; some
managed environments block it. Enrichment/pool/mana builds require it. All
Scryfall access now goes through **`scripts/scryfall.py`** (a shared, resilient
client): a slow/flaky Scryfall — read-timeout, 5xx, or a truncated body, none of
which are `URLError` subclasses — maps to `ScryfallUnavailable` (transient) and a
real 404 to `NotFound`, so the **interactive tools degrade instead of crashing**:
`deck.py mana/stats/wildcards/swap` show `?`/unknown, `build_gallery.py` flags
missing art and exits non-zero (instead of reporting an imageless gallery as
success), `wishlist.py --add` marks rows added name-only-due-to-outage
distinctly from a genuine no-match, and the editor's `/api/add` returns an
`enrich_status` of `ok`/`miss`/`offline` instead of 500-ing — it used to hand-roll
its own urllib call catching only `URLError`, so a READ timeout (a `TimeoutError`,
which is NOT a URLError subclass) escaped and crashed the request (audit F-09).
**Every** Scryfall call goes through the shared client; a new one that doesn't will
hit this same class of bug. The rebuild scripts (`enrich.py` /
`build_mana.py` / `build_pool.py`) also fail cleanly on an outage — a clear error
and a non-zero exit that leaves the existing derived file unchanged, rather than
crashing or writing a partial-blank file over good data.


## [G-15] The optional editing app (`scripts/app.py`) mutates `card-library.csv`

**The optional editing app (`scripts/app.py`) mutates `card-library.csv`** via
validated writes + a timestamped `.bak`, appends a `card-mana.csv` row when you
add a card (to keep INV-02), and also edits deck files under `decks/` (gated on
INV-04 — the file must re-parse with every card line intact — `.bak`'d, with
section comments preserved). After an app-editing session, run `/refresh` so
derived data catches up — an added card needs `build_mana.py` for its real
cost/keywords, `tag_synergies.py` for keyword tags, and `build_gallery.py` for
its art (until then it shows a fallback tile).


## [G-16] `card-pool.csv` carries printed `Power` / `Toughness`

**`card-pool.csv` carries printed `Power` / `Toughness`** (front face for a DFC), so
"power N or greater" conditions are gradeable at last. Nothing stored P/T before, which
left a whole class of card unanswerable by ANY tool — Garruk's Uprising's "whenever a
creature you control with power 4 or greater enters", Doran-style toughness-matters
payoffs, every "power 4+" condition — and it produced a real mis-read: **Mossborn Hydra
looks like a big body but is printed 0/0** and enters with a single counter, so it does
NOT trigger Garruk on entry. Values are stored RAW and parsed by **`lib.card_power()`**,
which returns `None` for the 91 pool cards printed `*` / `1+*` / `X` rather than
inventing a number — never `int()` the column yourself, and note `card_power(0)` is a
real 0 (every X-creature is 0/0), which is why the helper can't use `value or ""`.
`load_card_data()` exposes `power`/`toughness` and **backfills them from the pool onto
library rows**, since the library CSV has no such columns and is read first — without
that, exactly the cards you OWN would read as unknown. `deck.py stats` uses it for a
**power-threshold check**: a payoff keying on "power N+" is flagged when few of the
deck's creatures meet the bar on PRINTED stats (40a: Garruk's Uprising sees 2 of 23).
A creature that GROWS after it enters still won't satisfy an ENTERS trigger, so printed
stats are the correct and conservative read. Rebuild via `build_pool.py --all`; INV-03
treats the columns as OPTIONAL so a pool built before them still passes.
**The flag is SCOPED, because counting your own creatures is only the right question for
some "power N+" clauses — 16 of the roster's 27 flags (59%) were false in two shapes.**
(1) REMOVAL / opponent-facing (83 pool cards): "Destroy target creature with power 4 or
greater" (Sandbenders' Storm, Battle Menu, Valorous Stance) measures the WRONG BOARD —
the card wants THEIR creatures big — and for a sweeper like Dusk, few of your own
qualifying is the entire point, so the warning inverted the card. (2) **"TOTAL power N
or greater"** (153 pool cards, the bigger cause and one nobody reported): teamwork's
"tap any number of creatures you control with total power 4 or more" and Betor's "if
creatures you control have total toughness 10 or greater" are SUMS — three 2/2s satisfy
"total power 4" — so counting bodies at printed power ≥4 is the wrong ARITHMETIC, not a
conservative read of the right one. Deck 34 was told 0 of its 19 creatures could pay a
cost it pays trivially. `_POWER_SCOPE_MINE_RE` opts IN on "you control" rather than
blacklisting the bad shapes, because Magic's templating puts "you control" directly
before "with power N" and an affirmative test can't be widened by a phrasing nobody has
written yet; the cost is losing a scope spelled another way (Gwenna's "whenever you cast
a creature spell with power 5 or greater"), which is the right direction to err on a
list that exists to be read card-by-card. Found by asking why deck 13's earthbend deck
was flagged for a removal spell — then the pool survey turned up the larger `total`
family that the single reported case never hinted at.


### 2026-08-09 — the ENTERS-trigger caveat is generic, and it produced a false weakness

`stats`' power-N flag ends with "(Printed stats: a body that GROWS after it enters still
won't satisfy an ENTERS trigger.)" That parenthetical is appended to EVERY firing of the
flag, whatever the card's actual trigger timing.

Deck 56a fired it on two cards, and neither has an enters trigger:

- Scalestorm Summoner — "Whenever this creature **attacks**, create a 3/1 … **if you
  control** a creature with power 4 or greater"
- Ruby, Daring Tracker — "Whenever Ruby **attacks while you control** a creature with
  power 4 or greater"

Both read the board at attack time, so a creature grown by Ashroot Animist, Halana,
Ouroboroid, Bulk Up or Twin Blades satisfies them. In an ultra-tall counters deck that
pumps every combat, the printed-power count (5 of 19 creature copies) understates the
gate badly rather than overstating it.

The caveat was taken at face value and written into 56a's `#: tier:` block as a fourth
weakness supporting a grade. It had to be retracted the same day. The flag is still worth
having — it catches genuinely dead payoffs — but the count answers "how many bodies are
printed at power N", which is only the same question as "does this trigger fire" when the
trigger checks at ETB. Read the timing first.

### 2026-08-09, later the same day — FIXED: the timing now travels with the flag

`power_threshold_flags` reads the gated trigger's timing from its own ability line
(the `(?m)^` one-ability-per-line convention K-14 rests on): `attack` beats `enters`
when a line has both, because the attack reading — printed count is a FLOOR — is the
conservative one for a growing board. `stats` renders a per-timing caveat: ENTERS keeps
the old warning, ATTACK says pumped bodies DO qualify, anything else says to read the
trigger. Pinned in `TestPowerThresholdFlags::test_attack_time_gates_report_their_timing`;
the 56a incident's two cards now print the floor-reading caveat live.

## [G-17] `card-wishlist.csv` records Power PROVENANCE

**`card-wishlist.csv` records Power PROVENANCE** in a `Power Source` column
(`seed` / `hand` / `unknown`). `--add` and `--seed-power` both write a heuristic
estimate into the same cell a hand grade goes in, so nothing could tell an auto-seed
from a human judgment — which forced "verify this number" onto every row including the
graded ones. `wishlist.power_is_seeded()` treats `seed`, `unknown` and blank as
untrusted. **`unknown` is a deliberate third value:** rows predating the column were
mostly auto-seeds but some were hand-graded, so defaulting either way would be wrong in
one direction. Set `Power Source=hand` when you grade one.

**2026-08 (BS-17):** a row added name-only during a Scryfall outage was seeded from
BLANK Type/Text/Rarity — a flat 2.0, so a Mythic bomb ranked like filler — and the seed
was permanent: the F20 re-enrich backfilled the card's data but seeding only iterates
NEW rows, and `--seed-power` fills only blank cells. The re-enrich branch now recomputes
the seed when `power_is_seeded()` says the number is untrusted (seed/unknown/blank); a
hand grade is never touched. Verified: 2.0 from no data → 6.5 once the data arrived.


## [G-18] `card-pool.csv` now holds the full Arena pool

**`card-pool.csv` now holds the full Arena pool** (`build_pool.py --all`,
~15.8k cards) and **`card-mana.csv` covers it** (`build_mana.py --pool`), so
unowned cards have real costs/tags. Both tools DEFAULT to the smaller scope
(Standard pool / library-only mana), so a plain rebuild would SHRINK coverage back —
pass `--all` / `--pool` (as `/refresh` does) to keep full coverage. **Both now REFUSE
a >50% shrink** (`--allow-shrink` to force): `build_pool.py` always did, and
`build_mana.py` gained the same guard after the file was found at 1,695 rows against a
15,850-card pool — this exact mistake, which had also silently disabled the one-card
keyword heuristic that needs a pool-sized corpus. A FULL-refetch mana build is slow
(Scryfall rate limits ~15.9k cards, plus a front-face pass), which is why
`build_mana.py` is now INCREMENTAL by default — it reuses the rows already resolved and
fetches only what is new or still unresolved, with `--refetch` (or
`make refresh REFETCH=1`) for the full re-price. The pool build itself is fast
(paginated search, ~90 requests). `build_mana.py` falls back to a **front-face
`/cards/named` lookup** for names the batch endpoint won't match — SPLIT and room cards
(`Life // Death`), ~630 of them — and accepts the result only when the resolved card IS
the one asked for, since a bare front name can be a different card and a wrong cost is
worse than a blank one.

**The freshness reuse had a hole the reasoning did not cover (BS2-23, fixed 2026-08-07).**
The justification above — "the pool is the whole Arena pool and independent of what you
OWN, so an ingest cannot change it" — is sound for the INGEST case and false for the other
documented reason to run `build_pool.py --all`: **K-10 mandates it after a tag-pattern
edit**, because every pool row's `Synergies` is derived inside `row_for()` at FETCH time.
So a tagger edit followed by `make refresh` left the library re-tagged and the 15.9k-row
pool on the OLD tags for up to a week — with step 2/6 printing "card-pool.csv is fresh
(1d old); not rebuilt", `check_all` green throughout, and unowned craft candidates ranking
on stale tags. The stamp now carries a third line: a content hash of `tag_synergies.py`.
A mismatch defeats the reuse and prints why.

**Content, not mtime — and that choice is the interesting part.** The first implementation
compared the tagger's mtime to the pool's, which works on a developer's machine and is
wrong in general: git stamps every file at CHECKOUT time in arbitrary order, so a fresh
clone would have forced a ~5-minute full rebuild on its first `make refresh`, every time.
This repo had already learned the same lesson from the other direction at F-04, where a
`copy2`'d `.bak`'s mtime describes when its CONTENTS were written rather than when the
backup was taken.

**BS3-02: the grace clause disarmed the whole mechanism, and it took another instance of
the original bug to notice.** A stamp written before BS2-23 has no third line. That read
as None = "cannot tell" and — by explicit design — never forced a rebuild, so that the
upgrade would cost nothing. But **the reuse path returns before any stamp is written**,
so a legacy two-line stamp could never ACQUIRE a fingerprint: as long as the pool stayed
inside the freshness window, the escape hatch could not arm itself, and no tag edit would
ever be detected. The claim in the sentence above — "the upgrade costs exactly one pool
build, once" — described intended behaviour the code did not implement.

It surfaced the only way it could. The seven K-01 keyword mappings were added, `make
refresh` ran, step 2/6 announced `build_pool.py`, `check_all` came back green — and
`card-pool.csv` was byte-identical, with all seven mappings absent from the 16k-row
reference. That is BS2-23's bug happening again, inside its own fix.

The fix is that **unknown means rebuild once**: an absent fingerprint now defeats the
reuse and prints why, the build records the fingerprint, and every later refresh reuses a
fresh pool exactly as before. Pinned by four tests in `tests/test_build_pool.py`,
including the pair that matters — an unknown fingerprint rebuilds, and the run after it
reuses (so "once" is really once). The test helper `_stamp` now writes a three-line stamp
by DEFAULT, because the two-line double it used to write was quietly asserting the old
behaviour in the same file that was supposed to guard the new one.

The general lesson, which is this file's most repeated: **a grace clause added so a fix
costs nothing is a place where the fix can cost nothing.** If "unknown" can never become
"known", the state machine has one absorbing state and it is the broken one.


## [G-19] `card-wishlist.csv` is UNOWNED craft targets

**`card-wishlist.csv` is UNOWNED craft targets**, separate from the owned library
and the full pool. `wishlist.py --add <arena-export>` appends a batch, enriching
each card (Rarity/Color/Type/text/Synergies) from `card-pool.csv` with a Scryfall
fallback — double-faced cards are stored under their **full `Front // Back` name**
(matching the pool) so joins work, unlike the library's front-name convention.
`--by-set` is the pack/gem-optimization view (wishlist cards per set by rarity);
`--budget "9M 10R 38U 48C"` turns a wildcard budget into an optimal craft plan
(top `combined` per rarity cap + alternates + an import block — optimal because Arena
wildcards are strictly per-rarity, so the problem separates and top-K per rarity IS
the answer). **`--budget` is the SPEND view, so every check `--rank` runs has to
appear here too** — it was computing each pick's `rot` flag in `_rank_scores` and then
discarding it at print time, so a 3-slot uncommon budget came back with TWO cards
leaving Standard and no warning. Same shape as the `suggest --lands` legality bug: the
recommender that actually costs you resources was the one missing the check.
**The filter flags (`--set`/`--rarity`/`--color`/…) now apply to `--rank`/`--budget`/
`--by-set`**, which previously dropped them silently — `--budget "3R" --set TMT`
planned against the whole wishlist and returned FIN cards. The maintenance commands
(`--suggest-targets`/`--audit-targets`/`--seed-power`) deliberately keep the FULL list,
since auditing a filtered subset would report "clean" while leaving the rest unchecked.
A filtered view is **normalized against the whole wishlist** (`_rank_scores(rows,
keep=…)` scores everything, then filters): `fitN` is `pri` scaled to the max in the
scored set while `power` is not rescaled, so scoring only the subset inflates fit
relative to power and can genuinely reorder the picks — the normalization denominator
is a property of the CORPUS, not of the view. `--seed-power`
first-passes BLANK `Power` cells with a heuristic estimate (rarity floor + roles;
review it — the classifier undersells bombs); `--owned` flags cards you've since
crafted so you can prune them (or feed them to `reconcile_crafts.py`). `--add`
marks a **CONDITIONAL power** as `pow~` in `--rank`: a rarity+role seed grades a card in
ISOLATION and structurally cannot price one that scales with YOUR deck (X-cost, kicker,
exhaust, warp, landfall, "equal to …", "for each … you control"). Every Power that needed
hand-correcting in practice was this class — Repulsive Mutation seeded near-zero though
its counter is unconditional once the threat is big, Mona Lisa at 2.5 though she's a
3-mana rock that taps for 3, Procrastinate at 1.0 though twice-X stun counters lock a
creature for four untaps. The flag fires **even when Power is filled**, because the CSV
records no PROVENANCE — a value may be a `--add` auto-seed rather than a hand grade. It
says "verify from text", not "wrong". `--add`
**auto-seeds a heuristic `Power`** on the newly-appended rows (so a fresh card
never ranks at a 0.0 blank — the Elf engine and the Dino/Enchantress batches each
sank until graded; review the estimate and hand-adjust the bombs). `--audit-targets`
flags any card whose **Target deck can no longer cast it** (color/theme drift after
a retune — e.g. Neriv orphaned when deck 14 went Mardu→Rakdos) or has blank Power;
it's also folded into `check_all` as a **soft, non-gating warning**. The castability
check is **hybrid-aware** (`_pips_castable`, unit-tested): it reads the card's mana
cost and treats a hybrid pip as payable by either color, so a `{W/U}` card (Sun-Spider)
isn't false-flagged as off-color in a W/B deck — matching deck.py's own castability
lint rather than the raw color-identity subset. `--rank` shows
a **`state`** column (target deck's tier·remaining-crafts, ★ = this card helps
*finish* a near-complete deck) so "upgrade a BUILT deck" reads apart from "build an
UNBUILT one" — the strategic overlay the raw score can't show. `--rank` and
`--budget` **exclude cards you already own** (DFC front-name aware) so a craft plan
never tells you to craft what you have (audit F19); a **non-numeric or non-finite**
(`nan`/`inf`) `Power` is flagged `pow!` (scored 0.0 but surfaced, not silently sunk —
audit F9/A10); and
re-running `--add` on a batch **re-enriches** rows that were added name-only during
an earlier Scryfall outage instead of skipping them as dupes (audit F20).
`Target`/`Note`/`Power` are hand-annotated: `Target` is a
deck id / `general` / `concept: …`; **`Power` is a 1–10 hand-graded constructed-
power score** that `--rank` blends 50/50 with theme fit — plus a **bounded
cross-deck reuse (breadth) bonus** (the `use` column, ★ at ≥3; guarded as
bounded/capped by `check_rankings` anchor 5) so a multi-home craft outranks an equal
fit+power one-deck sidegrade — into a `combined` score
(an idf theme model can't see raw power, so bombs like Doctor Doom get buried
without it — the Power column is the fix; the artifact exposes a live fit↔power
slider). **Lands rank on a different axis:** a land has no synergy themes, so
theme fit would sink it — `--rank` instead rates a land on **manabase value** for
its target deck (how much of the deck's colors it produces, +untapped bonus, on
the same 0–10 scale) and blends *that* with `Power`, tagging it `manabase (land)`.
So a dual/verge that fixes a two-color deck ranks as the upgrade it is instead of
bottoming out under spells; the same dual pointed at a mono-color deck stays low.
The wishlist CSV itself isn't gated by check_all, but the **ranking
model is** — `check_rankings.py` (run inside check_all) guards the specific-theme
cutoff so a scoring change can't silently reclassify a real tribe as "generic".

**2026-08 (batch 6): the Power scale is now range-enforced at rank time.** The
NaN/inf guard (audit A10) and the non-numeric flag (F9) both existed, and a large
FINITE typo passed straight between them: `_rank_scores` now treats a Power outside
0–10 exactly like those (flag `pow!`, score 0.0, named in the ⚠ report). The
incident that earned it: **15 live cells carried 0–100-style grades** ('84', '78',
'74', '66', '60', '52'…) — an entire batch apparently graded on the wrong scale —
and because `combined` blends power at 50%, they didn't just distort the ranking,
they LED it: Pensive Professor sat at #1 with combined 42.3 on a 0–10 scale, so
every `--rank` and `--budget` run was steering wildcards by mis-scaled cells. The
flag replaces a silent over-rank with a loud under-rank; the cells are hand-grade
data (G-17) and stay yours to re-grade — `wishlist.py --rank` lists all 15.


## [G-20] Auto-targeting a wishlist batch: trust STRONG, judge `review`

**Auto-targeting a wishlist batch: trust STRONG, judge `review`.** `wishlist.py
--suggest-targets` scores each card's deck fit by **theme rarity (idf)** so broad
decks stop acting as catch-alls: naive theme-overlap over-assigns to 5-color
decks (17) and many-themed decks (21 Gastromancer) because *generic* themes
(etb/counters/tokens/lifegain/sacrifice) are central to nearly every deck and
carry ~no signal — only a *specific* theme (food, earthbend, firebending, Ninja
`sneak`, reanimator, Merfolk, …) is a confident match. Evergreen keywords
(trample/deathtouch) are excluded from the signal (they'd else fake a match).
Workflow for a new batch: `--add` → `--suggest-targets --write` (fills only
blank Targets with STRONG/ok picks) → text-review the `review` cards (generic/
multi-home/new-concept — the tag heuristic genuinely can't place these). This is
why the first batch's 21/17 buckets needed a manual text pass and were trimmed.


## [G-21] `card-pool.csv` carries a `Legalities` column

**`card-pool.csv` carries a `Legalities` column** (`;`-joined formats a card is
legal in) so `deck.py suggest` filters craft picks to the deck's `#: format:`
by default (override `--format` / disable `--any-format`). It's captured free
during `build_pool.py`, but a pool built before the column exists lacks it —
`suggest` then warns and shows all until you rebuild. `pool.py --legal <fmt>`
uses the same data.


## [G-22] `deck.py suggest` scopes by castable colors, not identity

**`deck.py suggest` scopes by castable colors, not identity.** It builds the
deck's colors from the declared `#: colors:` (else mana costs), so a card's
off-color *activated abilities* (e.g. Super-Skrull's `{4}{R}`) don't surface
uncastable picks. Run it both ways: `--owned --limit 0` scours the collection
for 0-wildcard upgrades already owned; `--unowned` lists craft targets. Picks are
ranked by theme fit **plus the same impact-role credit `cuts` uses** (`_role_credit`),
so among on-theme options a removal / card-advantage / ramp / cost-reduction / payoff
card outranks a same-theme vanilla body instead of being buried by tag overlap alone.
That ranking is now **needs-aware**: the role credit is **saturation-discounted** (the
8th removal spell is worth far less than the 1st, so `suggest` stops recommending an
effect the deck is already deep in and `cuts` ranks a redundant piece as more cuttable
while protecting a scarce one — #1); the score is nudged by a bounded (±15%) **curve
factor** that gently favors filling a thin CHEAP slot and penalizes an over-full one
(#2); and a modest **power co-signal** (the wishlist's rarity+role seed) surfaces an
owned/craftable BOMB with only modest theme overlap without pulling in off-theme junk
(it only re-ranks WITHIN the on-theme set — #6). All three are BOUNDED modifiers on the
dominant theme-fit signal, gated by `check_suggest.py` so they can't silently reorder a
tuned deck.


## [G-23] `deck.py engines <id>` grades a deck's two-sided ENGINES

**`deck.py engines <id>` grades a deck's two-sided ENGINES** (enabler ↔ payoff, #3).
A synergy tag says "sacrifice" is in the deck; it can't say which cards FEED the engine
(outlets/fodder) vs PAY IT OFF (death triggers). `engines` classifies each card's text
as enabler and/or payoff for the engine themes (sacrifice, counters, tokens, graveyard,
lifegain, food) and flags a lopsided engine — the ⚠ fires only off the trustworthy
PAYOFF side ("payoffs but NO enablers" = dead payoffs; "payoff-heavy" = under-enabled),
since enabler cues are broad; `deck.py stats` surfaces the flag inline. It's a shortlist
that prints the card lists — read them, the classifier is heuristic. **Two combat-/self-
fed false-positive classes are now discriminated (guarded by `check_engines.py`):** a
**`sacrifice` "whenever ~ dies" DEATH trigger** is split from an outlet-dependent "whenever
you sacrifice" payoff and is COMBAT-FED — exempt from the dead-payoff ⚠ once the deck fields
≥`_COMBAT_FED_MIN` (6) creatures (so a go-wide/deathtouch deck that trades constantly no
longer reads as "payoffs sit dead" — the deck-31 misfire); and **`graveyard` self-recursion**
(flashback / escape / disturb / unearth / harmonize / jump-start / retrace / aftermath /
"cast from graveyard") counts as its OWN enabler, so a flashback-heavy yard isn't flagged
"payoff-heavy" (the deck-9 misfire). The fix is SURGICAL: a genuine thin-enabler signal —
e.g. many "N cards in your graveyard" *value* payoffs with few active fillers — still flags,
because combat fills the yard only slowly there (unlike an immediate death trigger).


## [G-24] `deck.py stats` also prints an INTERACTION PROFILE

**`deck.py stats` also prints an INTERACTION PROFILE** (#5): the raw interaction count
treats all removal alike, so `stats` breaks it down by SPEED (instant vs sorcery) and by
whether it can answer a NONCREATURE permanent (planeswalker / enchantment / artifact),
flagging "all sorcery-speed" or "no noncreature answer" — measured, not eyeballed.


## [G-25] `deck.py stats` / `tier` measure a PROTECTION axis

**`deck.py stats` / `tier` measure a PROTECTION axis** — "can this deck protect the
permanent it wins with?" Nothing asked that before: `stats`, `quality` and `tier` all
counted interaction and card advantage, so an all-in single-threat deck with ZERO
ward / hexproof / indestructible in 60 cards looked healthy, and the gap had to be
found by hand-grepping the deck list. `role_tally` now returns **`protection`** via
`protection_effects()` — deliberately NARROWER than the "Protection / trick" role,
which lumps a combat pump ("gets +2/+2 until end of turn") in with a real answer to
removal. `regenerate` is excluded on purpose: "It can't be regenerated" is boilerplate
on removal spells, so keying on the word would score half the format's removal as
protection. A **zero** is flagged in both views, naming the `#: protect:` build-arounds
at risk. It is REPORTED, never fed into `tier_band` — that formula is anchored by
`check_tier.py`, and a new term would silently re-grade the roster. It found 5
zero-protection decks on first run (2, 37/37a/37b, 40), three of them with `#: protect:`
headers.


## [G-26] `deck.py tier <id> --audit-rationale` catches a STALE tier argument

**`deck.py tier <id> --audit-rationale` catches a STALE tier argument** — and its
SUPPRESSION RULES are the delicate part, because a citation is often legitimately not
a claim about the current list. Two families, both windowed ±140 chars:
`_HISTORY_CUES` (the card left / was held out) and **`_COMPARISON_CUES`** (the sentence
changed subject — `path to`, `vs`, `unlike`, `distinctness`, `consider`), plus an exact
mask of every **roster DECK name**, since a deck name that is also a card name
("Blood Price", "Sacrifices") read as a stale citation whenever one deck's prose named
another for contrast — which is what the distinctness prose is FOR. Getting these wrong
is asymmetric: a false positive is noisy and gets noticed, a **false negative is
silent**. One did hide for a while — a bare `over` in `_HISTORY_CUES`, which matched
"card advantage 9 **over** a 2.86 curve", the house phrasing for a quality vector, so
the cue meant to catch a PAST figure was suppressing the sentence that states the
CURRENT one. Deck 43 quoted interaction 10 against a live 8 and the audit said clean.
Removing `over` then exposed the case it had been covering by luck — a figure written
as a TRANSITION (`card advantage 0→1` states the OLD value first), now handled
explicitly by **`_ARROW_AFTER`**. Keep these cue lists NARROW and let the roster-wide
sweep be the check.
**A SECOND, larger false negative had the same shape, and the root cause was reusing
ONE rule for two different questions.** A CARD citation and a FIGURE go stale
differently: a card is history when the SENTENCE is about a change ("Essence Scatter
became hard counters"), which is why its ±140-char sweep for any change-word is right;
a figure is history only when **the NUMBER ITSELF is stated as past**. Running the
card rule over figures meant ordinary domain vocabulary suppressed live claims — and
`remov\w*` (in the list to catch "removed") matches **"removal"**, the commonest noun
in a rationale arguing about interaction. `"The floor reads A on interaction 9 … five
surplus REMOVAL spells were traded"` was silenced by its own subject matter. So were
`"…interaction 13 … THE PAYOFF IS THE ONE CRAFT TARGET"` and `"\"restore the
interaction\" WAS not the whole fix … At interaction 6"`. Figures now go through
**`_figure_is_history`**: BACKWARD-looking only, ~24 chars, for past-tense language
directly governing that number (`was`, `up from`, `it cited a 2.65 curve`), plus the
arrow and a tightened comparison window. Separately the avg_mv pattern read only
`curve of 2.44` / `avg MV 2.44` while the rationales write **`a tight 2.44 curve`** —
14 uses against 1 roster-wide, so that half of the audit was decorative. Both fixed
together surfaced **13 stale figures across 10 decks** where the audit had reported
clean, with **zero** false positives on the roster sweep. The lesson generalizes past
this file: when one predicate serves two callers, check that the QUESTION is the same,
not just the shape of the data.
**The residual that fix left was a REVERSED claim, now closed by `_cites_as_arriving`.**
A replacement names TWO cards and only one of them may legitimately be absent:
"Essence Scatter became hard counters" documents a card that LEFT, but `"Spell Pierce
was CUT for Shriek, Treblemaker"` names Shriek as the card that came IN — so when that
swap was reverted the sentence asserted a swap that no longer existed, and the audit
reported the deck clean through both directions because "CUT" sat adjacent either way.
The check now un-suppresses a citation on the ARRIVING side of a directional cue
(`cut/traded/swapped/exchanged … for X`, `became X`, `replaced by X`, `+X`), closed by a
DEPARTING marker (`over Y`, `instead of Y`, `-Y`) since "+A (over B)" names both sides.
**A THIRD sweep found the audit had been reporting the whole roster clean while TWELVE
figures were stale — and this time the misses were in the PATTERNS, not the cues.**
Three independent holes, all the same shape. (1) **Parenthesised figures.** The prose
writes `interaction (3)`, `interaction total (3)`, `card advantage is thinner (3)`,
`curve (2.81)`; the patterns demanded whitespace then digits, so every one was invisible
— eight sat on the roster and deck 23 reported clean while quoting a 3.6 curve against a
live 3.47. (2) **Number-first figures.** The roster writes `7 interaction` far more often
than `interaction 7` — 13 interaction figures, 3 card-advantage, 1 protection, none ever
read. This is EXACTLY the avg_mv miss already recorded two paragraphs up ("14 uses
against 1 roster-wide"), repeated on the three axes the tier floor is actually computed
from, which is the argument for fixing a class rather than an instance. (3) **`early_drops`
was in the quality vector with NO pattern at all**, so that count could rot in total
silence; deck 23 claimed "6 one-two-drops" against a live 11.
Two false-positive classes came out of the same sweep and shaped the fix. The house style
is a number-first claim followed by a **BREAKDOWN** — "7 interaction (5 spot removal + 2
sweepers)" — so a permissive `\((\d+)` read the first SUB-COUNT as the claim and reported
four decks stale against numbers they never asserted; requiring the bracket to close on
the digits (`\((\d+)\)`) keeps the genuine cases and drops every breakdown. And a figure
inside **quotation marks** cites earlier prose rather than claiming it (deck 7's `The old
one-line reason ("thin interaction (3)") is no longer true`) — `_figure_is_history` cannot
reach that with a 24-char window and widening it would loosen every other suppression, so
it now treats an ODD count of preceding quote marks as a quoted span. All twelve findings
were UNDER-statements (live exceeded quoted in 11 of 12), so no tier letter was at risk —
but that is luck, not a property of the bug.
**The KNOWN RESIDUAL is the label side, and it is live:** the figure patterns read
`protection N` and `curve of N` / `a N curve`, so **"protection is 1"** and **"the
reported 2.57"** both sailed through on deck 42a while the real values were 3 and 2.91.
A copula or a participle between the label and the number still hides a figure. Widen it
only with a roster sweep — the gap is deliberately bounded to two intervening lowercase
words so a label cannot reach across a clause and adopt an unrelated number.
Two of MY OWN cue bugs surfaced on the roster sweep, not from reasoning: `re.I` silently
defeated the case-SENSITIVE capital that makes `+X` a card name, so the `+` in "hard
counters + a mythic finisher" read as a swap marker; and "cut for" is not always a
replacement — "two heist cards were CUT for **cause**: Doom Reigns Supreme wants five
Villains" means cut for a REASON, so the arriving card must sit immediately after the
cue (short gap, no `.;:—` in it). Both directions are unit-tested, and the roster sweep
is the check that found them — run it on any cue-list change.
**A SECOND LIVE RESIDUAL, on the CARD side: a change-cue about one card suppresses a
citation of a DIFFERENT card in the same window — even when that clause says the card
STAYS.** Deck 42a's rationale read *"Heartless Act was CUT on exactly that reasoning …
which is why Hero's Downfall and Erode stay"*, and when **Erode** was cut for Ruthless
Lawbringer the audit still reported the deck **clean**: `_HISTORY_CUES` saw `CUT` within
±140 chars of `Erode` and suppressed it. The suppression window is card-BLIND — it asks
"is there change language nearby", not "is this change language about THIS card" — and a
rationale legitimately naming a card it cut is exactly why the window is wide. What makes
this case tractable is that the suppressed clause carries the OPPOSITE of a history
marker: `stay` / `stays` / `remains` / `is kept` asserts CURRENT membership, so a
citation carrying one should be un-suppressed the way `_cites_as_arriving` un-suppresses
the arriving side of a replacement. **Not yet fixed** — per the rule two paragraphs up, a
cue-list change needs a roster sweep first. Until then, a "X stays" claim in a `#: tier:`
rationale is NOT covered by the audit; check it by hand after a swap.

**2026-08 extension — SHORTHAND is handled in both directions.** The scan matched FULL
names only, so a rationale abbreviating an ABSENT card was invisible: deck 28's
archetype cited "Gishath" after Gishath, Sun's Avatar was cut, deck 36's cited
"Okinec Ahau" after Sovereign Okinec Ahau was cut, and both audits reported clean —
two consecutive misses on the header a reader trusts first. `_shorthand_index` now
maps the comma-heads ("Gishath") and capitalized word-tails ("Okinec Ahau") of every
multi-word card name to the full name(s) they abbreviate, and `rationale_staleness`
scans the prose's capitalized 1–3-word spans against it (prose-driven, so cost scales
with the rationale, not the pool). Design points, each earned by the roster sweep that
validated the fix: an AMBIGUOUS fragment stays in the index and flags when EVERY
candidate is absent ("Okinec Ahau" abbreviates both Envoy of and Sovereign — dropping
ambiguity would have re-lost the real miss), a fragment shared by 4+ names is dropped
as an epithet; the ten GUILD names are blocklisted (four decks say "Rakdos" meaning
the color pair); the in-deck suppression gate uses PLAIN containment so "Tishana"
reads as shorthand for an in-deck "Tishana's Tidebinder" (the word-boundary rule
treats the apostrophe as in-word, and over-suppression is the safe direction); and a
citation immediately followed by a negation ("Note Mjölnir does NOT do this") is a
contrast with an absent card, suppressed positionally like the simile rule
(`_NEGATION_AFTER`). The sweep's single surviving flag was a TRUE positive — deck 21's
archetype still claimed Ragost as its core after Ragost moved to variant 21a.

**2026-08-11, a PREFIX COLLISION the epithet cap structurally could not see.** The
shorthand pass scanned `masked`, which blanks only the cards the deck RUNS. So an
ABSENT card's full name was still sitting in the text when the fragment pass ran, and a
fragment of it resolved to a DIFFERENT card: deck 28's prose cited "Savage Land Dinosaur"
— one real stale citation — and the audit reported TWO, the second being "Ka-Zar of the
Savage Land", a card the prose never names. Fixing the single real citation cleared both
flags, which is how the false one was identified. Note this is NOT the ambiguity case the
cap governs: "Savage Land" abbreviates exactly ONE card, so it was never ambiguous — it
is a prefix of a longer name, which is a different failure.

The fix scans a string with every OCCURRING full card name blanked, not just the in-deck
ones. Blanking the SUPPRESSED names too is the load-bearing half: without it the fragment
path smuggles back a citation the full-name scan deliberately let go under history,
simile or negation, which would quietly defeat every suppression above it. Length-
preserving, like the mask it extends, so positions stay comparable.

Two guards landed with it, both latent in the FIGURE patterns rather than the card scan,
and both now called by every consumer of those patterns — the `#: tier:` scan had the
same bugs with no live instance to expose them. A `%` immediately after a match means a
percentage, not an average mana value ("cast-on-curve 76.7%" was reported as a 76.7 avg
MV); and a "draw N" count is not a card-advantage figure ("sac->draw 2 card advantage").
See G-04 for the `#~ note:` scan they were found by.

**A residual this fix does NOT close, found while fixing the others:** a figure needs its
cue ADJACENT to the number. Deck 26b's `#: tier:` says "the fastest curve here at 2.44"
against a live 2.5, and `curve(?: of)?[  ]+(\d+\.\d+)` cannot match across the
intervening words. Left rather than widened, because widening a figure pattern mid-change
is exactly what the archetype-figure extension above shows needs its own sweep.

**2026-08, the FALSE-POSITIVE direction — a DATE read as a figure.** Every fix above
widens what the audit catches; this one narrows it, and the asymmetry is the point. The
NUMBER-FIRST figure patterns (`(\d+)[ ]+interaction`, `…protection`, `(\d+\.\d+)[ ]+curve`
and six siblings) opened with a bare unanchored `(\d+)`, so the group matched the TAIL of
any larger number sitting before the metric word. Deck 63's rationale said *"three cards
after the 2026-08 protection pass"* and the audit reported **`protection 08` against a
live 4** — a claim the prose never made, on a deck whose protection figure was correct.
`_FIG_NUM` / `_FIG_DEC` now prefix those nine patterns with `(?<![\d.])(?<!\d-)`, which
rejects a number preceded by a digit, a decimal point, or the `YYYY-MM` digit-hyphen
shape (each lookbehind fixed-width, as Python requires). It also, deliberately, rejects a
RANGE — *"2-3 interaction"* states a band, not a figure, and auditing a band against an
exact live value would flag prose that is not making an exact claim. **Why this mattered
more than its size suggests:** a false positive here is the expensive direction. Every
other entry in this section documents a SILENT MISS, which costs you one stale sentence;
a false positive trains you to skim past the audit, which costs you all of them. The fix
was validated both ways — four unit cases pin the date, the range and the still-caught
real figure, and a roster-wide diff of old-vs-new matching confirmed the guard rejects
**zero** spans of genuine prose across all 95 decks.


### 2026-08-09 — a figure quoted about ANOTHER deck reads as a claim about this one

Deck 56a's re-graded `#: tier:` block argued that sitting one band below its parent was
coherent, and supported it by citing deck 56's vector: "deck 56 core is a genuine aggro
deck (clock 5/7, interaction 7, avg MV 2.42) and holds A AT its floor."

`--audit-rationale` reported two stale figures: interaction 7 vs live 4, avg mv 2.42 vs
live 2.67. Both "stale" numbers were correct — about deck 56. The scan extracts numbers
from a `#: tier:` block and compares them against the vector of the deck that OWNS the
block; it has no notion of a figure attributed to a different deck, and no cue list can
give it one, since "deck 56 core is…" is exactly the shape of an ordinary claim.

Fixed by dropping the numbers and keeping the comparison in words, with a note in the
file so a later editor does not helpfully restore them. The general rule: **compare with
`deck.py tier <other-id>`, do not quote its numbers into this deck's prose.** This is the
same family as the other G-26 residuals — the audit reasons about a block's text without
a model of who a sentence is about.

### 2026-08-09 — the fixture-driven rework: five live misses in one session

One session produced five audit misses and one false positive, all on real decks, all
while the audit printed "rationale is current". Each was reproduced as a failing
fixture BEFORE any fix (scratch copies of the exact transient file states), then fixed,
then swept roster-wide. The diagnoses:

1. **Possessive citations were invisible.** `_find_word_bounded`'s apostrophe rule —
   built so *Deliberate* cannot match "Deliberately" — read the `'s` in "Aven
   Interrupter's {W}{W}" as "inside a longer word". Fixed: a terminal `'s` is grammar.
2. **A cue word inside the card's own name suppressed it.** `_HISTORY_CUES` has
   `swap\w*`, and *Crib Swap* was suppressed by the "Swap" in its own name — the
   `remov\w*` incident's class, one level worse, since no prose edit can ever fix a
   card whose NAME matches a cue. Fixed: the citation's span is excluded from the cue
   window.
3. **Short comma-heads were not shorthand.** The index required a 6-char head, so
   "Inti" (also Ruby, Zuko, Suki, Momo — the whole Universe-Beyond first-name class)
   could never be detected as a stale abbreviation. Lowered to 4; the epithet cap and
   a new label-idiom rule ("Down: the manabase…" must not read as *Down, Down to
   Goblin-town*) carry the false-positive load.
4. **Suppression crossed sentence boundaries.** The flat ±140-char window let "were
   cut for the aristocrats package." suppress a citation of a DIFFERENT card in the
   NEXT sentence (deck 66's Spider-Islanders). Fixed: both cue families are
   clause-scoped; comparison cues (and an explicit "deck N" reference) reach one
   clause further back, because distinctness passages set their frame first.
5. **Figures about another deck flagged against this one** (the 56a false positive).
   Fixed: a figure whose clause names a different deck id is skipped.

The first roster sweep of the fixed scanner found **six real stale rationales**
(decks 30, 37b, 44, 48a, 51a, 58 — including an archetype block citing a card that
never made the deck's final 60, and one asserting "the second Archivist stays" about
a list with no Archivist at all), every one previously reported clean. All six prose
blocks were corrected in the same commit. Nine cue-list false positives surfaced in
the intermediate sweep and were closed by cue additions (`used to`, `missing`,
`exclud\w*`, `would`, `rather than`, `parent`, `sibling`, `same shape`) — each
recorded in the cue lists' own comments.

The meta-lesson repeats `check_agreement`'s: a check that passes while missing things
reads as coverage. What broke the standoff was FIXTURES FROM LIVE MISSES — not
re-reasoning about cue lists — and a roster sweep after every change.

## [G-27] `deck.py tier <id> --audit-rationale` catches a STALE tier argument

**`deck.py tier <id> --audit-rationale` catches a STALE tier argument.** The `#: tier:`
rationale is prose, so nothing kept it honest as the list changed underneath it — and it
went stale twice in one session (40a's argued from Chelonian Tackle and Unforgiving Aim
after both were cut; deck 40's cited a 2.26 curve after a swap moved it to 2.32). The
tier guard only compares the LETTER to the floor; it never reads the argument. This does:
it flags cards the rationale cites that are no longer in the deck, and figures that
contradict the live quality vector. Card matching is CASE-SENSITIVE against known card
names (prose capitalizes a citation, so a lowercase "counterspell" isn't one), masks the
cards the deck DOES run first (else "the Ooze Spill" reported the card *The Ooze*), and
suppresses citations sitting next to change/flex language — a rationale legitimately
documents what it cut. Scoped to `#: tier:` AND `#: archetype:` — the archetype block makes
claims about the current list just as the tier rationale does ("these cards push your life
total up" is false once those cards are cut), and it is the header a reader trusts first.
It was added to the scope after a deck's own archetype text survived three rounds of swaps
that removed every card it named; it earned its keep again when deck 48's archetype block
went on citing Robotics Mastery a pass after the cut. `#: notes:` is a free-form build log where
naming an absent card is CORRECT. Report-only; it never edits the prose. Note the practical
consequence of the suppression window: a rationale that legitimately NAMES a card it cut
must put the change-cue ADJACENT to the name ("X and Y were CUT because…"), not a sentence
later — three separate rewrites this cycle were needed for exactly that. **Run it after
any deck edit** — a defensible grade rotting into an indefensible one is the exact
failure the tier guard exists to prevent.

### Two calibration notes from the 2026-08 deck 52 pass

**"Adjacent" means the same clause, and a wrapped `#:` line break can break it.** Deck 52's
prose read *"Hero's Downfall came out for Sothera, and / Vayne's Treachery came out for
Zodiark"* — the first passed, the second was reported stale, because the cue and the name
landed on opposite sides of a continuation line. Rewriting the second as **"Vayne's
Treachery was CUT for Zodiark"** cleared it. When the audit flags a card you know you
documented, try moving the cue *before* the name in the same clause first.

**Residual: the EXCLUSION check has a proximity window and misses a wrapped list.**
Deck 52's `#: notes:` carried a five-line "Deliberately NOT included and why:" list with
Baron Helmut Zemo named on the **third** continuation line — while the deck was running
him. `wrong_exclusion_claims` returned `[]`. The check pairs the exclusion cue with names
near it, and "near" does not span a wrapped `#: notes:` list. This is precisely the
false-negative direction G-26 warns is the dangerous one: *a false positive is noisy and
gets noticed, a false negative is silent.* Until it is fixed, re-read the exclusion list by
eye whenever a swap adds a card the deck once rejected — which is common, since a
reconsidered card is exactly the kind that gets excluded in writing first.

**The FIGURE half only joined the archetype scan on 2026-08-09 (BS4-07), and this rule
claimed otherwise for a year.** `rationale_staleness` swept `("tier", "archetype")` for
CARD citations from the day it was written, while the figure loop iterated `tier_prose`
alone — so the documented scope was true of half the function, and an `#: archetype:`
figure could contradict the live vector indefinitely. Deck 26a quoted *"avg MV 3.05, 15
early drops"* against a live 2.97, and the audit reported the deck clean.

Widening it was not a one-line change, which is the part worth carrying forward. The first
roster sweep after the fix returned **three hits, of which only one was genuine**:

| deck | quoted | live | verdict |
|---|---|---|---|
| 26a | avg MV 3.05 | 2.97 | **genuine** — corrected |
| 44a | card advantage 0 | 3 | FALSE — the figure is about deck 1, named "Black Sun" |
| 49 | avg MV 5.30 | 4.03 | FALSE — the figure is about *Standard's* Dragons |

Deck 44a's clause is *"DISTINCTNESS vs 1 Black Sun … Black Sun is aggro-sacrifice with a
5/7 clock and card advantage 0"*. The existing cross-deck suppressor is `_OTHER_DECK_RE`,
which matches the literal `deck N` — and prose names a deck by its NAME. Deck 49's is
*"Standard's Dragons average MV 5.30, so a deck that wants to field several must SOLVE ITS
OWN MANA"*: a true claim about the format that the scan read as a claim about the list.

Two clause-scoped suppressions were added — another roster deck named by NAME (reusing
`_roster_deck_names`, which the CARD scan has masked with since it was written), and
`_POPULATION_SUBJECT_RE` for a possessive population subject. The possessive form is
deliberate: *"Standard's Dragons average…"* names a population, while *"fine in Standard,
avg MV 2.4"* is still a claim about this deck and must keep auditing.

**Then the deck-name suppression muted the one genuine hit**, and the reason is a naming
convention rather than a bug in the idea: deck 26a is named **"Iron Forge — Virulent"**, so
its PARENT's name is a substring of its OWN, and an exact-match exclusion treated "Iron
Forge" as another deck. The rule is now *a name that is part of THIS deck's own name is not
another deck*. Final state: one genuine hit roster-wide, corrected, with a behavioural
anchor asserting the roster figure sweep stays clean.

The lesson is G-26's, earned again: **the roster-wide sweep is least optional exactly when
you WIDEN a scan.** Two-thirds of the new reports were false, and the fix for them was one
naming convention away from silently deleting the only true one.


## [G-28] `deck.py suggest` shows a cross-deck reuse count (`Decks` column)

**`deck.py suggest` shows a cross-deck reuse count (`Decks` column).** For each
pick it counts how many of your OTHER decks (the deck being analyzed is excluded,
so it can't inflate its own picks) the card is *castable* (its identity ⊆ the
deck's declared/derived colors) **and** shares ≥1 *central* theme with (a theme
carried by ≥25% of that deck's most-common theme's copies, floor 2) that is also
**SPECIFIC** — a generic theme (etb/tokens/counters/lifegain/…) or a broad
background tribe doesn't count, unless it's that deck's `#: protect:` build-around
spine (≥2 protected cards). That gate is load-bearing: centrality alone left the
count saturated — nearly every deck is central on the same handful of generic
themes, so 99% of a deck's picks scored ≥3 and the median pick "fit" 31 of 56 other
decks, i.e. the column carried no information (audit F-04). **VARIANTS are collapsed to
their core deck** and `#: status:` placeholders are excluded — 19/19b/19c are one
archetype's worth of value, not three homes (the second inflation source). Median reuse
is now ~1–2 of 41 core decks, spread 0–19. Both models route the counting rule through
**`deck.cross_deck_breadth`**, each supplying its own notion of a "specific" theme
(deck.py's denylist vs the wishlist's idf cutoff — a deliberate difference), so the RULE
can't drift apart again the way it did; `check_suggest` anchor 13 asserts the two agree
on a synthetic card. Read it as a rough "value per wildcard": a craft that fits several
decks outranks a one-deck sidegrade — still breadth, not curated fit. A "High
cross-deck reuse" line summarizes the top fits≥3. Factor it into a craft's ★/~/·
weight in a flex block.


## [G-29] Flex-block craftables are format-scoped

**Flex-block craftables are format-scoped.** When a deck's `#: format:` changes,
re-check its `#~` craft suggestions — a craftable legal under the old format may
have rotated (hit moving decks 1/2 Historic→Standard). `deck.py flex <id>` plus
the pool's `Legalities` column confirm.


## [G-30] The pool's `Legalities` is a build-time SNAPSHOT — Standard rotates

**The pool's `Legalities` is a build-time SNAPSHOT — Standard rotates.** So a
card the pool still marks `standard` may have aged out since the last
`build_pool.py`. `deck.py suggest` guards against this with a **date-aware
rotation check**: `build_pool.py` now writes a `Released` date per card and a
`card-pool.build` date sidecar, and `suggest` marks a pick **`⚠rot`** when its
set is >~3 years old (rotated / rotates soon) and warns when the pool stamp
itself is stale. Treat `⚠rot` as "verify before crafting" and rebuild the pool
(`build_pool.py --all`, per `/refresh`) to refresh both the legality snapshot and
the date stamp. `rotation_risk()` returns False on a blank `Released` (graceful
before a pool rebuild adds the column), so the flag only fires once the data
supports it. The **roster-wide counterpart is `deck.py rotation`**: for each
Standard deck it lists the cards past the ~3-year window (same `rotation_risk`
primitive), a rollup by rotation year (soonest first, `⚠ SOON` for this/next year),
and the most-exposed decks — *what rotates next and which decks it hits*. It reads
the pool's `Released` column (rebuild `build_pool.py --all`, else it prints a
rebuild prompt) and scopes with `--format` / `--years` / `--within` (how many years
ahead to surface — since a freshly-built pool holds only currently-legal cards, it
ranks by each card's rotation YEAR rather than a strict >years boolean). It's also a
**dashboard panel** (Standard rotation), and `wishlist.py --rank` flags a craft target
whose Standard-legal set rotates this year/next as **`⚠rot~YEAR`** (don't spend a
wildcard on a card about to leave the format). **Reprint caveat, now partly encoded:**
the pool keys ONE printing per card, so a card reprinted into a set with an announced
non-standard legality window inherited the wrong date — Genesis Wave read `⚠rot~2027`
off its Foundations printing when FDN is Standard-legal through **2029**, i.e. it was
flagged "about to leave the format" with four years left (it ranked 27th; it now ranks
4th). `deck.rotation_year(released, years, set_code)` consults
**`_SET_ROTATION_OVERRIDE`** (add a row per announced long-legality set), and
`rotation_risk` routes through it so the two primitives can't disagree. `rotation_risk`
is calendar-YEAR based, not days-since-release, because rotation happens at an annual
fall rotation: a 2023 set rotates during 2026 and is at risk for all of 2026, not only
after its third birthday. The RESIDUAL is still real — a card whose newest printing the
pool didn't capture can read early; verify against the official schedule.

**2026-08 extension — the CRAFT views carry the flag too.** The wishlist was the only
flagged craft surface, and a deck line that never reached the wishlist bypassed it:
deck 28's craft plan held FOUR LCI cards rotating within months, invisible to `check`,
`wildcards` and `audit` alike, and caught only by a human cross-referencing `rotation`
output during a roster review. `deck.craft_rot_note()` (same `rotation_year` primitive,
same this-year-or-next window as the wishlist flag, so the surfaces cannot disagree)
now marks each missing/short card `⚠rot~YEAR` inline in `deck.py check` — with a
closing advisory naming the flagged cards — and in `wildcards`' leverage list.
`wildcards --dedup` (the cross-deck UNION of craft targets, one row per card with
copies-short under shared-collection math, rarity, decks-served and the rot flag,
ranked by decks-served then rarity) formalizes the craft-efficiency question that four
2026-08 ingest cycles answered by hand. First run of the flag found deck 49 holding
FIVE 2026-rotating craft targets nothing had reported.


## [G-31] `deck.py suggest-homes <card>` automates the "which of my decks does this new card improve" fit 

**`deck.py suggest-homes <card>` automates the "which of my decks does this new
card improve" fit pass** (the manual dance repeated every craft this session —
Doctor Doom, Elspeth, Wan Shi Tong, Shark Shredder). It scans EVERY deck and
lists the ones where the card is both *castable* (its identity ⊆ the deck's
declared/derived colors), **legal in that deck's `#: format:`** (the pool's
`Legalities` snapshot, so a non-Standard card like Triumph of the Hordes isn't
offered as a Standard home — `--any-format` disables; unverified/pool-absent =
legal, like `suggest`/`legal`), **and** shares ≥1 *central* theme — with
**cost-shaped themes gated** (`_drop_cost_themes`): filling your graveyard is VALUE in a
reanimator deck and DAMAGE in a control deck that needs its counterspells in the library,
but theme overlap sees one tag either way. Genesis Wave read **KEY for a Simic control
deck purely on a `graveyard` match** — i.e. it scored highly BECAUSE it mills you.
`graveyard`/`mill`/`discard` now count as a fit only when the deck fields ≥2 cards that
PAY THEM OFF, reusing `engine_roles` rather than adding a model; it drops the theme for
20 of 56 decks and keeps it for the real graveyard decks. (Note the motivating case is
NOT filtered — that deck does field 3 graveyard payoffs, so the KEY is defensible on that
axis; the objection to Genesis Wave there rests on its `GGG` cost against 15 green
sources and on binning 15 of 34 nonlands.) Same 25%-centrality test as `suggest`'s reuse
count (same
25%-centrality test as `suggest`'s reuse count), ranked by theme-fit, marking where
it's already maindecked and naming the single weakest nonland cut candidate per deck
(`#: protect:` cards excluded). The card name is resolved like `card.py` (exact →
DFC front → unique substring), so a partial name (`Ojer Taq`) or a God//Land DFC
resolves instead of "not found". It's a SHORTLIST, not a verdict — the cut is one
heuristic pick, so still grade from full oracle text via `deck.py cuts <id>` and
preview with `deck.py swap` before applying. **That cut hint is now the SAME ranking
`cuts` prints** — it used to be a private three-term copy (`_weakest_cut`: theme fit
over central themes + unsaturated role credit) that inherited NONE of the co-signals
`rank_cut_candidates` gained, so it had no power, distinctiveness, multiplier, tribal
or signature term and a role credit blind to how much of that role the deck already
runs. **The two disagreed on 36 of 64 decks**, and not cosmetically: `suggest-homes`
proposed cutting **Bloom Tender** from deck 17 and **Vizier of the Menagerie** from
decks 34/36 — the roster's best fixers, and the exact cards the `_is_color_fixer` work
was done to protect (the `add_is_fixer` guard only fires when the card being ADDED is
a fixer, so it never covered these). Both now score through one **`cut_keep_score`**
(with `cut_scoring_context` supplying the deck-level terms), ties break on the card
name so a min-scan can't resolve a tie by deck-file order, and `check_agreement.py`
holds them together on the live roster. This is the F-01 shape one more time and the
reason a pure-function anchor could not see it: every co-signal is provably bounded
and separately gated, and **a second caller that never calls them is invisible to all
of that**. Cost: `suggest-homes` went 0.6s → 3.1s for the real ranking. Because copies are fungible, it
reminds you to slot a card into *all* decks that earn it, not pick one home. A
**bounded curve co-signal** (`_home_curve_fit`, capped at `_HOME_CURVE_CAP`) gently sorts
a top-heavy / win-more card (an ~11-mana Aettir and Priwen, MV well above a deck's average
nonland MV) BELOW efficient fits in a low-curve deck and flags the row `⚠ top-heavy for
this curve` — a one-sided nudge that never boosts, never relabels the KEY/role-player/
tangential verdict, and only reorders same-strength fits (finding #5; anchor 12). Each
fit row now carries a **strength label** (`KEY` / `role-player` / `tangential`):
KEY = it shares the deck's *signature* theme (the top central theme, **or any theme
carried by the deck's `#: protect:` cards** — so a counter-doubler reads KEY in a
counters deck even though "counters" is idf-generic, correcting a blind spot where the
deck's actual spine looked tangential), OR it shares a **specific** (non-generic) theme
AND fills an interaction/card-advantage gap the deck is short on; role-player = a
secondary specific central theme; tangential = generic overlap only
(etb/tokens/lifegain/…). **The role-gap KEY is gated on a specific-theme match**
(`fit_strength` checks generic-only → tangential BEFORE the gap branch): otherwise a
generically-good removal / card-advantage card read KEY in *every* low-interaction deck
it merely shared an etb/tokens tag with (Get Lost "KEY" in 15 decks). Its broad utility
is real, but it belongs to the cross-deck **breadth** signal (wishlist `--rank` `use`
column), not a specific home — so `suggest-homes` no longer inflates it. `GENERIC_THEMES`
(the low-signal denylist behind "specific") covers the broad matters-generics PLUS
card-selection/value and the evergreen combat keywords (flying/ward/first strike/…), so
a keyword-only overlap never fakes a specific fit. **Broad background creature TRIBES
get the same treatment** via `_GENERIC_TRIBES` (Human/Hero/Villain — so common in a
superhero/anime multiverse they carry no home signal): a bare shared tribe can't mint
KEY even as the deck's top theme OR via a `#: protect:` signature (the Hawkeye-"KEY"-in-
every-Hero/Human-deck over-assignment, tagging-misreads #4). Narrow build-around tribes
(Ninja/Cat/Dinosaur/Wizard/Merfolk/…) stay SPECIFIC — a real tribal payoff still reads
KEY (guarded by `check_suggest` anchor 11). Rows sort strongest-first — trust KEY,
judge role-player, and read a tangential fit as "probably not for this deck" (fit_strength
is unit-tested). The same classifier flags a merely-tangential add in `deck.py quality --add`. **A rainbow fixer gets a
color-count-aware overlay** on top of `fit_strength`: a card whose value is
multi-color fixing (`_is_color_fixer`, read from oracle TEXT in explicit mana /
basic-land-type context) is promoted to **KEY in a 4+-color deck / role-player in a
3-color one** (and gets a bounded fit bump, `_fixer_boost`), because fixing value
scales with the deck's color count — something a theme-overlap model can't see. It
never demotes a fit `fit_strength` already rated KEY, and does nothing below 3 colors
(mono/two-color decks don't want the fixing). This closed the Overlord → decks 17/21a
miss. **The promotion is RATE-GATED and the cut side is add-AWARE — both because the
overlay shipped a backwards recommendation.** See the fixer-overlay gotcha below.

### Two residuals, both measured on one card (Chandra, Spark Hunter, 2026-08-07)

**A zero-row result is a THEME miss, not a colour-identity fact.** Asked which Abzan angle
the roster did not cover, a `suggest-homes` sweep returned no WBG rows and that was written
up as "you have no white-black-green deck." There are FOUR — 6 Dead or Alive, 13 Earth
Kingdom, 20b Abzan Toughness Ramp, 21 Gastromancer. What the sweep actually measured was
that no WBG deck shared a *central, specific* theme with the card, which is a different and
much narrower claim. The check costs one command: read `#: colors:` before concluding a
colour pair is unbuilt. This is the K-13 shape one layer up — a zero-result sweep is an
unverified search, not a fact — and it is the more dangerous version, because the sweep
here did not fail. It answered a question correctly; the question was just not the one
being reported.

**KEY scores THEME OVERLAP alone, so for a structurally-valued card it carries little.**
Chandra, Spark Hunter rated KEY in **14 of 42** decks. Nearly every one of them shared only
the generic red trio `burn, card draw, noncombat damage`, and nine of the fourteen ran
**zero artifacts** — where she is a four-mana Merfolk Looter. What actually decided her five
placements was a set of counts the model cannot see, measured by hand per G-61:

| deck | artifact cards | token producers | Vehicles | the deciding payoff |
|---|---|---|---|---|
| 48a Motor Pool | 19 | 17 | **7** | her combat trigger is live at all |
| 48 Doombots | 22 | 12 | 1 | Mechan Assembler, once per turn, matches her `0` |
| 58 Treasure Planet | 0 | **19** | 0 | Crime Novelist / Krenko / Pirate Peddlers read her `+2` |
| 10 Mad Villainy | 9 | 7 | 0 | card advantage 1 — the deficit her `+2` fixes |
| 45a Grixis Mayhem | 2 | 2 | 0 | 5 Mayhem cards want a free repeating discard |

Note the two rows that break the pattern in opposite directions: **58 holds zero artifact
CARDS** and is one of the best homes on the list (its resource is tokens — the G-66
residual), and **45a holds two** and is a fine home for a reason unrelated to artifacts at
all. Neither is derivable from the KEY label. The rule is not "distrust KEY"; it is that
KEY answers "does this share a theme", and for a card whose text names a resource, the
question that decides is "how much of that resource does the deck hold".


## [G-32] `suggest-homes` reads CASTABILITY as an identity SUBSET — which says nothing about whether you c

**`suggest-homes` reads CASTABILITY as an identity SUBSET — which says nothing about
whether you can pay the pips.** A card is "castable" here when its color identity ⊆ the
deck's colors, so **Anti-Venom (`{W}{W}{W}{W}{W}`) was rated KEY for decks 29/29a**, where
10–11 white sources put it at roughly a **1%** chance of being castable on turn five. The
identity test is right for *routing* and structurally blind to *depth*. `deck.py
pip_depth_warning(cost, sources)` closes it with the same hypergeometric model
`consistency` uses: a cost demanding ≥`_PIP_DEPTH_MIN` (3) strict pips of one color is
priced against the deck's real sources (`deck_color_sources`) at turn `_PIP_DEPTH_TURN`
(5), and anything under `_PIP_DEPTH_TARGET` (70%) prints `⚠⚠ 5x{W} vs 10 sources` on the
fit row plus the source count that would clear the bar. It's a FLAG, never a score change
— a deck can legitimately want a color-hungry bomb and fix for it — but the number is now
on screen instead of implied by a subset test that can't see it.

### 2026-08-13 — two gaps closed, both found by the OWNER catching a bad recommendation

`deck.py suggest 55a --unowned` offered **Elegy Acolyte (`{2}{B}{B}`)** as a craft target
to Mardu Spellstorm, which holds **8 black sources**. The owner declined it on a manabase
read; `consistency` priced it at **40.0% on turn four** against a Karsten target of 20
sources. Neither the flag above nor anything else had said a word. Two separate reasons:

**1. The primitive had ONE caller.** `pip_depth_warning` was wired into `cmd_suggest_homes`
and nothing else — so the deck-level recommender, the surface that actually proposes craft
targets, never called it. This is exactly the shape G-40 names: *a pure-function anchor
cannot see whether a caller asks.* The helper was correct, documented and unit-tested the
whole time. `cmd_suggest` calls it now and prints `⚠⚠2x{B} vs 8 src` inline plus a summary
line pointing at `consistency`.

**2. The 3-pip floor excluded the card entirely.** `_PIP_DEPTH_MIN` was 3 — *"only 3+ pips
of ONE colour are worth checking"* — and Elegy Acolyte has two. Even wired in, it would
have returned None. The test suite pinned this exactly (`pip_depth_warning("{3}{W}{W}",
{"W": 8}) is None`), which is the test-double-encoding-old-behaviour case: that assertion
was updated deliberately, not reactively.

**Why 0.55 and not 0.70 for the 2-pip band — measured across all 37 deck files:**

| setting | maindecked cards flagged |
|---|---|
| `MIN=3, target=0.70` (the old rule) | 25 |
| `MIN=2, target=0.70` | **109** |
| `MIN=2, target=0.55` | **43** |
| `MIN=2, target=0.50` | 30 |

Straight `MIN=2` at the existing 0.70 adds 84 flags, ~3 per deck, and the additions are
overwhelmingly ordinary — Vampire Nighthawk on 11 black sources, Phyrexian Arena on 11,
Angelic Destiny on 11. That is noise that teaches a reader to skip the flag. At 0.55 the
band isolates the real class: 2 pips on **3–9** sources — Wonder Man on 3 red, Progenitus
and Appa on 4 white, deck 21's black cards on 5, Overlord on 6, Elegy Acolyte on 8. The
3+ band keeps 0.70 so its meaning is untouched, and a test pins that it is unchanged.


## [G-33] `suggest-homes` also weighs a DOUBLER against the deck's magnitude on its axis

**`suggest-homes` also weighs a DOUBLER against the deck's magnitude on its axis.** A
doubler (Exalted Sunborn, Delney, Anointed Procession, a counters doubler) is worth
roughly what it doubles, and theme overlap cannot see that: Exalted Sunborn shares
`tokens` with a deck that makes 14 tokens and with one that makes 6, and scored them the
same — which is how it read `role-player` for Knight's Edge (deck 3) while ranking a
6-token deck above it. `doubler_axis(text)` classifies the card on one of
`_DOUBLER_AXES` (tokens / counters / triggers), `doubler_support()` COUNTS the deck's
cards that feed that axis, and `doubler_boost()` turns the count into a bounded fit bump
(`_DOUBLER_PER_SOURCE` 1.2 per feeder, capped at `_DOUBLER_CAP` 18, zero below
`_DOUBLER_MIN_SOURCES` 5), promoting to **KEY** at `_DOUBLER_KEY_SOURCES` (10) the way
the fixer overlay promotes at 4 colors — necessary because the strength label sorts ahead
of raw fit. `doubler_restriction()` reads the doubler's OWN scope off its text
(`_DOUBLER_POWER_RE`, e.g. Delney's "power 2 or less") and filters the feeder count to
match; without it Delney's support in deck 24 read 24 instead of 4 — enough to flip it
over the KEY threshold, i.e. the restriction is load-bearing, not a nicety. The cap is set
at 18 rather than 12 so the term stays linear across the realistic 4–15 feeder range
instead of saturating at 10 and calling a 14-token deck the same as a 10-token one.
Bounded and gated by `check_suggest` anchor 14. Exalted Sunborn → deck 3 moves
role-player/51 → KEY/69; Delney goes tangential (a bare `Human` overlap) → KEY for the
decks it actually doubles.
**KNOWN GAP: `doubler_restriction` parses a POWER scope and nothing else, so a doubler
scoped by creature TYPE is counted against the whole deck.** Splinter, Radical Rat —
"If a triggered ability of a **Ninja** creature you control triggers, that ability
triggers an additional time" — scores support **27** in deck 20 against a correct
Ninja-restricted **12**, because `_DOUBLER_POWER_RE` sees no "power N or less" and
returns `None`, which `doubler_support` reads as unrestricted. It is the same defect the
Delney case above calls load-bearing, one scope-kind over: the restriction was built for
the shape that motivated it and the type shape was never asked about. Deck 20's LABEL
does not move (both counts clear `_DOUBLER_KEY_SOURCES`; the boost only goes 18.0 → 14.4,
and 18 is the cap), which is exactly why it survived — a wrong number that lands on the
right side of a threshold looks like a working model. It WILL mis-rank a tribal doubler
in a deck that fields few of its tribe, which is the case `suggest-homes` exists to
judge. Read a `✱ multiplier` figure on a type-scoped doubler as an upper bound until
this is fixed; the fix is a second scope pattern feeding the same filter, not a second
model.


## [G-34] Before committing a deck edit, run `deck.py preflight <id>` — and grade a cut/swap with `deck.py

**Before committing a deck edit, run `deck.py preflight <id>` — and grade a
cut/swap with `deck.py quality`.** `preflight` is the one-call gate the editing
skills use: it folds `legal` + owned/buildable + castability + a full `check_all`
pass into one PASS/FAIL block with a READY/BLOCKED verdict (hard-fails only on an
illegal deck or broken integrity; WIP craft targets are WARN). `quality <id>`
computes a deck-quality vector (buildable · uncastable · interaction/
card-advantage · curve · central themes); snapshot it with `--json` **before** a
change, then `--vs FILE` **after** to flag regressions (interaction dropped,
castability broke, a central theme lost its last copy, curve heavier) so a swap
that *worsens* the deck self-catches. It's a SOFT guard — an intentional trade
(e.g. dropping card advantage for interaction in an aggressive deck) is fine and
it only warns; grade the flagged axis from full text before accepting or
reverting. This is what the `/apply-changes` skill runs around every swap.


## [G-35] `deck.py mana` also lints color SOURCES, not just pip demand

**`deck.py mana` also lints color SOURCES, not just pip demand.** After the pip
breakdown it prints "Color sources (lands producing each color)" (basics by
name, nonbasics by color identity — mana dorks aren't counted) and flags cards
whose strict colored pips look thin against those sources (`△ Pip-intensive`:
wants CC with <9 sources, or C with <4). This catches the "wants UU but this is
really a U-splash" problem the castability lint (which only checks identity ⊆
declared colors) can't see — e.g. a 3-source green splash flagging GG cards. A
heuristic review signal, not a hard fail; it doesn't gate `check_all.py`.


## [G-36] `deck.py consistency <id>` is the PROBABILITY layer `mana` lacks

**`deck.py consistency <id>` is the PROBABILITY layer `mana` lacks.** `mana` diagnoses
("wants UU, only 6 U sources — thin"); `consistency` puts numbers on it via an exact
hypergeometric model: opening-hand **keepable %** (2–5 lands in 7), **screw/flood %**,
**land-drop consistency** (P of ≥N lands by turn N), and — per colored card — **P(casting
on curve)** at turn = its mana value (capped at 5), with a **Karsten-style source
recommendation** for the ones that come up short ("62% on T3 → want +2 R sources"). This
is what caught deck 8's 1-red-source splash reading 12% on turn 2 (The Ruinous Wrecking
Crew) — the "is this splash even castable" question the source-count lint only hand-waves.
The fix note is source-count-aware: a **thin (≤3-source) splash** color is reframed as
"cast late or cut, don't chase it on curve" rather than printing an impractical land
count (15 R sources), and an **early double pip in a MAIN color** ({B}{B} on T2) reads
"color-hungry — expect it a turn or two later" instead of being mislabeled a splash.
Strict pips only (hybrids are strictly easier — excluded, same rule `mana` uses);
multi-color costs use per-color independence (a mild over-estimate). `--on-draw` models
the extra card; `--target P` sets the cast-probability bar (default 0.90). A planning
aid, not a guarantee (mulligans/scry/draw shift the real numbers) — it doesn't gate
`check_all.py`. Pure math helpers (`hypergeom_at_least`, `cards_seen`, `cast_probability`,
`min_sources_for`, `opening_land_stats`) are unit-tested in `tests/test_deck.py`.


## [G-37] `deck.py suggest --lands <id>` is the manabase RECOMMENDER `consistency` was missing

**`deck.py suggest --lands <id>` is the manabase RECOMMENDER `consistency` was missing.**
`consistency` DIAGNOSES a color-source shortfall ("want 18 R, have 12") but nothing turned
that into a list of lands — and plain `suggest` is structurally BLIND to lands (it filters
candidates to cards sharing a synergy THEME, and lands rarely do, so a manabase fix never
surfaces; this is why a batch of hand-picked land/fixer suggestions once had to be found by
a manual CSV query). `--lands` scores each on-color land by **FIXING value** (`wishlist.
_land_value` — produces the deck's colors, untapped premium; the DOMINANT 0–10 axis) plus
two BOUNDED nudges: **synergy** (`_land_synergy_bonus` — a land whose ability plays a deck
theme, e.g. Abandoned Air Temple's team-pump in a go-wide deck: *lands sometimes have
relevant text*) and **shortfall** (`_land_shortfall_bonus` — favor the color the deck is
scarcest on, from strict pip-demand vs current sources). Both caps ≤2 so fixing decides and
the nudges only break near-ties (gated by `check_suggest` anchor 9). `--owned` scours the
collection for 0-wildcard fixers (usually the answer — it surfaced deck 39's owned Boros
duals); `--unowned` ranks craft targets (untapped premium duals first); `--full` prints the
land's oracle text so you grade the ability, not just the fixing. It excludes lands already
in the deck and off-color/colorless-only lands (they don't fix THIS deck).
**It now defaults to the deck's own `#: format:`, as the card-facing `suggest` always did.**
It previously filtered only when someone passed `--format` explicitly, so a plain
`suggest --lands <id>` on a Standard deck offered Underground River and Duskmantle, House of
Shadow as craft targets — neither Standard-legal. On a WILDCARD-SPEND recommender an
unfiltered pick costs real resources, and it is the "recommending a craft without a legality
check" failure this file warns about elsewhere. Found by USING the tool to build a deck, not
by a test. `--any-format` still shows everything.

### LIVE RESIDUAL (2026-08): the top of the list is not always a land

Replacing an unowned mythic land in deck 52, `suggest --lands 52` returned this top four,
and **not one of them is playable in the slot**:

| Rank | Card | Score | Why it fails |
|---|---|---|---|
| 1 | Mudflat Village | 9.2 | `{T}: Add {B}. **Spend this mana only to cast a creature spell.**` 16 of the deck's 36 nonland cards are noncreature spells — 44% cannot use it. Its other ability returns Bat/Lizard/Rat/Squirrel; the deck has none |
| 2 | Tarrian's Journal | 9.2 | **Not a land.** Front is a `{1}{B}` Legendary Artifact — Book |
| 3 | Grasping Shadows | 8.3 | **Not a land.** Front is a `{3}{B}` Enchantment |
| 4 | Aclazotz, Deepest Betrayal | 8.1 | **Not a land.** Front is a `{3}{B}{B}` Legendary Creature — Bat God |

Ranks 2–4 all carry a land on the **back** face, reachable only by transforming — never by
a land drop. The card that was actually correct, **Hidden Necropolis** (a common whose
`{4}{B}, {T}, Sacrifice` discovers 4), ranked **8th**; the next-best real land, Midgar,
ranked 8th-equal and is a genuine land only because ITS front face is the land half.

**Why nothing caught it.** Maindecking rank 2, 3 or 4 in the `# Lands` block leaves the deck
with one fewer real land and **INV-04 passes**: the line parses, the set code exists, the
collector number is held, the card is Standard-legal. `check_all` has no notion of "is this
line a land". The deck would simply play badly.

**Root cause is G-63's class one layer out.** The pool row for a DFC records a land type
whenever EITHER face is a land, and the candidate filter read that row. The accessor rule
("ask which face a column describes") was never applied to the land-ness predicate itself.

**FIXED 2026-08-09.** `suggest_lands` now admits a candidate only when
`_primary_type(type_line) == "Land"` — the FRONT face, which is what a land drop can play.
Measured: **81 pool cards** carry `// Land` on a non-land front and were all eligible
before. Midgar, City of Mako correctly SURVIVES the change (`Land — Town // Sorcery —
Adventure`), which is the case `lib.primary_type`'s own docstring calls out.

The lesson is not "DFCs are tricky" — it is that **`wishlist._is_land` was given this
exact fix in BS2-11 and its sibling recommender was not.** One rule, applied in one place
and not the other, for a year, on two commands that answer the same question about the
same pool rows. When you fix a face-reading predicate, grep for the others.

**Rank 5 was recorded as a fourth miss, and on re-measurement IT IS NOT ONE.** The claim
was that Great Arashin City (*"enters tapped unless you control a Forest or a Plains"*,
unreachable in mono-black) "scored 5.8 fixing rather than the 4.6 given to a flatly-tapped
land, i.e. the scorer treated an unsatisfiable condition as sometimes-satisfied." Measured
2026-08-09:

| land | shape | fixing |
|---|---|---|
| Great Arashin City | mono-B, conditionally tapped | 5.8 |
| Foul Roads | mono-B, conditionally tapped | 5.8 |
| Forum of Amity | **B/W dual**, tapped | 4.6 |

The 5.8-vs-4.6 gap is COLOUR MATCH — a mono-coloured source the deck fully uses against a
dual it half-uses — and has nothing to do with tapping. Both conditional lands are denied
the untapped premium exactly as a flat-tapped land is, because the substring test sees
"enters tapped" in the clause. **The original note compared two cards that differ on a
second axis and attributed the gap to the first.** Re-measure a scoring claim against a
control that differs in only the axis being blamed.

**The real limitation is the OPPOSITE one, and it is conservative.** A conditional land is
scored as always-tapped even for a deck that trivially meets the condition (Great Arashin
City enters untapped in anything running a Forest), so it is UNDER-scored, never over-.
Deciding satisfiability needs the deck's contents, which `_land_value` is not given — so
`suggest --lands` prints `·tapped?` and the clause instead of guessing (G-52).

**The RESTRICTED-MANA miss was real, and is fixed (2026-08-09).** Mudflat Village reads
*"{T}: Add {B}. Spend this mana only to cast a creature spell."* — a black source for
creatures and nothing at all for a removal spell — and it ranked **#1** of deck 52's land
suggestions at 7.2 fixing. `_land_value` now tracks restricted production separately (per
LINE, because the qualifying sentence follows the Add sentence inside one ability, and the
clause scan stops at the period before it) and HALVES the fixing premium when every colour
the deck wants from that land is restricted. Mudflat drops to 5.4, below the unrestricted
mono-B sources at 5.8, which is the ordering a manabase wants. 37 pool lands carry the
clause. The discount is one-directional — it can only lower a land, never invent one — and
half rather than zero because the restriction is narrow: near-full value in a creature
deck, near-dead in a spell deck, and `_land_value` is told only the deck's COLOURS. Hence
the `·restricted` marker for the judgment the score cannot make.

**So: read the type line, the tapped clause and the spend clause.** The type-line half is
now enforced and the restricted half is priced; the two `·` markers are there because the
remaining judgments need the deck, not the card.


## [G-38] `deck.py suggest --ramp / --interaction / --needs` are the NEEDS model — the structural axes the

**`deck.py suggest --ramp / --interaction / --needs` are the NEEDS model — the structural
axes theme-`suggest` is blind to.** The theme model answers "what SYNERGIZES"; a mana dork,
a fixer, or a board-dependent removal spell fills a STRUCTURAL need (fixing / acceleration /
interaction) it can't see — so these opt-in modes score against a shared **`deck_needs(d)`**
profile (per-color source deficit, curve top-heaviness → accel-want, interaction count vs
target) instead of themes. Never weaken the gated theme filter to surface them (the idf model
was BUILT to reject catch-alls); add a parallel path. **`--ramp`** ranks repeatable mana
sources (dorks/rocks; instants/sorceries excluded as one-shot rituals) by CHEAPNESS × the
deck's accel-want (a cheap dork ramps a top-heavy deck; a 2-color deck's fixing is nearly
solved, so fixing is only the bounded scarce-color bonus) + **restriction-fit** (a restricted
dork — "add R only for Equipment spells" — is boosted in a matching deck, penalized in a
mismatched one; `_ramp_restriction_fit`) + a power tiebreak — surfaces Purple Dragon Punks
atop deck 39. **`--interaction`** surfaces removal INCLUDING off-theme (the fix — theme-suggest
filters it out), ranked by power + a bounded **scaling boost** for a board-dependent spell the
deck supports (`_int_scaling` detects fight / "damage = N you control" / X-cost; `_scaling_
metric` reads the deck's strength on that axis) and FLAGS it `⚠ scales w/ <axis>` for a human
read — never a silent boost (the honest stance for a fuzzy signal). **`--needs`** is the
one-stop view composing all three (fixing · acceleration · interaction). All nudges bounded,
gated by `check_suggest` anchor 10.

**2026-08 (BS-01):** `--ramp` and `--interaction` filtered candidates by color IDENTITY,
not printed cost — the G-58 bug re-introduced on exactly the paths this rule routes
deficits to, hiding a measured 34 castable interaction cards + 25 mana sources from
mono-color decks. Both now use `_candidate_castability`, the same filter as `suggest`
proper. Full incident under G-58's 2026-08 addendum.


## [G-39] `deck.py cuts` folds a card-QUALITY (power) co-signal into the ranking (#3)

**`deck.py cuts` folds a card-QUALITY (power) co-signal into the ranking (#3).** Theme
fit alone can't tell a vanilla body from a bomb that share one tag, so cuts blends the
wishlist's rarity+role **Power** estimate into the keep-score: an on-theme-but-WEAK card
sorts UP the cut list (flagged "on-theme but low power") and an on-theme BOMB is
protected. It's a **bounded** nudge (`_cuts_power_adj`, ±`_CUTS_POWER_CAP`, neutral at
power 5) — it only breaks near-ties, never overrides theme fit — and is gated by
`check_suggest.py` anchor 7 (mirrors the suggest power co-signal, anchor 5). A `Pw`
column shows each card's power; still grade from the printed oracle text, not the number.


## [G-40] `deck.py cuts` folds a MULTIPLIER co-signal (`✱`) — and the bug it fixes is a caller, not a mode

**`deck.py cuts` folds a MULTIPLIER co-signal (`✱`) — and the bug it fixes is a caller,
not a model.** A doubler's worth lives in the REST of the deck, and BOTH halves of the
cut score are structurally blind to that: theme-fit sees a card with few tags, and
`_role_credit` sees no functional role, because "doubles a trigger" is not a role. So
**Delney, Streetwise Lookout — which doubles the triggered ability of every creature in
deck 46's small-body engine layer (10 feeders) — ranked as that deck's WEAKEST card**,
with Valkyrie's Call just behind it. The information was already in the codebase:
`doubler_axis` / `doubler_support` were built for `suggest-homes` and score Delney
correctly, *including* its "power 2 or less" restriction. `cuts` simply never asked.
`_cuts_multiplier_adj` routes the SAME primitives into the keep-score — not a second
model, so the two cannot disagree about what a doubler is worth — bounded to
0…`_CUTS_MULT_CAP` and **ZERO below `_CUTS_MULT_MIN_SOURCES`**, because a doubler in a
deck that does not feed its axis genuinely is cuttable. It only ever RAISES a
keep-score: the no-support case is already handled by theme-fit, and subtracting there
would punish the same card twice. Gated by `check_suggest` anchor 16, which pins the
bounds AND (in `tests/test_deck_models.py`) the WIRING — a pure-function anchor cannot
see whether a caller asks, which is exactly the F-01/F-18 failure shape and exactly what
went wrong here. Roster impact: 15 multipliers across 11 decks re-scored; every
non-doubler unchanged.
**A LIFEGAIN axis was added to `_DOUBLER_AXES` at the same time**, because The Wind
Crystal ("if you would gain life, you gain twice that much life instead") read as no
doubler at all — the axis list stopped at tokens/counters/triggers. It requires the
literal `twice that much` rather than reusing the other axes' looser `instead`
alternative, because a replacement that is NOT a doubling is templated identically:
Angel of Vitality's "you gain that much life plus 1 instead" is +1, not ×2, and would
have qualified. Pool diff: 53 → 57 doublers, the four new ones all genuine.


## [G-41] `deck.py cuts` flags COST-AS-UPSIDE (`⚡`) — a cost that is a BENEFIT in this deck

**`deck.py cuts` flags COST-AS-UPSIDE (`⚡`) — a cost that is a BENEFIT in this deck.**
Every scoring model here grades a card in ISOLATION, where an additional cost reads as a
drawback; in the matching deck the same clause is an engine trigger. CLAUDE.md warned
humans about this in prose ("ask what does this do *here*") but nothing detected it, so a
card whose cost is secretly an upside sorted like one with a real drawback.
`cost_upside_flags(text, deck_themes)` pairs a cost pattern with the themes that invert
it: a **kicker returning a land** in a LANDFALL deck re-triggers every landfall payoff
(Chocobo Kick); **Warp / "when this leaves the battlefield"** in a COUNTERS deck is what
moves the counters onto your threat (Broodguard Elite); a **sacrifice** cost feeds a sac
outlet; a **discard** cost fills a reanimator's yard. Shown in the cut table and again in
the oracle-text block. It is a FLAG for a human read, never a score change — the same
posture as `⚠ scales w/`, because the signal is real but too fuzzy to move a ranking.


## [G-42] The MIRROR of cost-as-upside: a fine card that fights your own engine

**The MIRROR of cost-as-upside: a fine card that fights your own engine.** The `⚡` flag
catches a drawback that is secretly an upside here; nothing catches an UPSIDE that is
secretly a drawback here, and that shape shipped into two finished decks. Strategic Betrayal
and Pit of Offerings both read as perfectly good cards — and both EXILE an opponent's
graveyard, while four heist cards in each deck (Tinybones the Pickpocket, Shark Shredder,
Hama, Azula/Rakdos) need that graveyard FULL. `deck.py cuts` did rank Strategic Betrayal
second-weakest, so the shortlist saw it; only the full-text read explained WHY. The general
rule: when a deck DEPENDS on a zone being populated, audit every card that empties it —
graveyard hate in a graveyard deck, hand attack in a deck that wants them holding cards.
Grading a card in isolation cannot see this, which is the same blind spot `⚡` exists for.



**2026-08 — a new member of this class, found by asking rather than by shipping.** The
question was whether white BLINK effects would suit deck 63 (Abzan +1/+1 counters), since
blink is a known way to re-buy ETB triggers. Two measurements answered it, and neither is
visible in any single card's text. First, DENSITY: only **7 of 35 nonland cards** in that
deck are ETB-triggered, and the seven are small (one counter, two, three) — so
re-triggering them is a worse rate than simply casting another placer. Second, and
decisive: **a blinked creature returns as a NEW OBJECT with no counters on it.** In a deck
whose whole plan is accumulating counters on bodies, blink erases the investment it looks
like it should protect — the G-42 shape exactly, a perfectly good card fighting its own
engine, invisible to every model that grades a card in isolation. The contrast that makes
it a rule rather than an anecdote: the same effect is CORRECT in deck 41 (Darkforce
Inversion), which is built on big one-shot ETBs with nothing to erase. **The deck decides,
not the card.** One partial exception is worth knowing: Daydream returns the creature
*with* a +1/+1 counter, so it replaces one of what it erases — which makes it a
PROTECTION card (save the body, lose the counters, beat losing both), never an engine
piece. Generalised: before adding a blink, bounce or flicker package, count what it would
DISCARD, not just what it would re-trigger.

## [G-43] Grade a modal / split / adventure card by the FACE YOU CAST, not the half you want

**Grade a modal / split / adventure card by the FACE YOU CAST, not the half you want.**
Decadent Dragon was drafted into a Rakdos deck for its `{2}{B}` adventure half (a two-card
heist) and cut once `deck.py consistency` priced its `{2}{R}{R}` FRONT face at 53% on turn
four. The rationalization — "the half this deck actually wants is castable" — is exactly what
the front-face costing convention exists to prevent, and `consistency` is the tool that
settles it.


## [G-44] `deck.py cuts` also folds an ability-DISTINCTIVENESS co-signal — the card-level analog of the de

**`deck.py cuts` also folds an ability-DISTINCTIVENESS co-signal — the card-level analog
of the deck-idf theme model.** The deck theme model weights how rare a theme is across
*decks*; nothing measured how generic a *card's own abilities* are, so a body carrying
five common tags (`etb; tokens; sacrifice; lifegain; pump`) tripped broad synergy-overlap
everywhere, indistinguishable from a distinctive-mechanic card. `lib.card_distinctiveness`
scores that from **pool tag-rarity**: a card's ability tags mapped to pool-idf, evergreen
keywords and bare creature TRIBES excluded (identity, not ability — a niche tribe isn't a
distinctive *mechanic*; noncreature subtypes like Equipment/Aura/Case are kept), scored on
its *rarest* couple of tags (top-2 mean, so a standout ability isn't diluted by also
carrying etb) normalized to 0–10. A vanilla card reads ~0; a rare mechanic reads high.
cuts shows a **`Uq`** column and blends it as a **bounded, orthogonal-to-power** keep nudge
(`_cuts_uniq_adj`, ±`_CUTS_UNIQ_CAP`, neutral at 4) — a generic-ability filler sorts UP the
cut list (flagged "generic ability — trips broad synergy checks"), a distinctive card is
mildly protected; gated by `check_suggest.py` anchor 8. It's **orthogonal to power** on
purpose (a vanilla 6/6 is high power, low distinctiveness), so it earns its own small term.
Tags are a lossy projection, so a **second, complementary signal** closes the residual:
`lib.structural_distinctiveness` reads the oracle TEXT's SHAPE — an unusual (non-ETB)
trigger, a non-mana activated ability, rule-bending / replacement language, modality,
clause depth — to catch "this card does something the tags didn't capture," with NO
corpus / build artifact / normalization pipeline (the cheap alternative to a text
TF-IDF model; option 2 of the two follow-ups). `card_distinctiveness(tags, text)` returns
the **MAX** of the tag-rarity and structural signals, so the structural term only ever
RAISES a score — it RESCUES a mis-tagged distinctive card (Ragnarok's dies-trigger 2.1→7.5,
Thousand-Year Storm's copy engine 3.6→7.5) but can never inflate a truly generic one
(vanilla / plain-ETB / bare-mana all stay low; the mana-dork activated ability is excluded).
Both callers pass the card's text; omitting it is tag-only (backward-compatible). The
RESIDUAL caveat is now small but real: a distinctive card with *neither* a rare tag *nor*
an unusual text shape still reads generic — so `Uq` remains a shortlist signal, not a
verdict (a full oracle-TEXT-rarity model is the heavier follow-up if this ever misfires).
`wishlist.py --rank` shows the metric as a **`uq` diagnostic column** (display-only there —
it does NOT feed `combined`): a low `uq` on a `review` card confirms filler, a high `uq`
says the tags under-read it — grade from text.


## [G-45] `deck.py tier <id> --to <TIER>` now assembles a concrete CUT→ADD tune package (#4)

**`deck.py tier <id> --to <TIER>` now assembles a concrete CUT→ADD tune package (#4).**
Past the measurable gap + owned/craft fillers, it pairs each filler that closes the gap
with a weakest-fit cut from the SAME ranking `deck.py cuts` prints (so the two can't
disagree), then **projects the resulting quality vector and floor** ("interaction 2→5 ⇒
floor C→A ✓"). It flags a cut that itself feeds interaction/card-advantage ("⚠ pick
another cut") **or is a mana source** (a dork/rock/ramp spell — "⚠ losing it may hurt
the manabase", caught via `_produces_mana` so an "add one mana" dork the role classifier
misses still flags) and notes when the cut list is exhausted before the gap closes. It's a
STARTING plan that PRINTS, never writes — the card selection stays a human call (protect
signature/spice — that's `/tune-deck`); preview any line with `deck.py swap`.
**Its OWNED filler list used to skip the legality check its CRAFT sibling applied** —
so `--to A` printed one list headed "format-legal" and an unfiltered one directly above
it, and offered **Deadly Dispute** and **Dovin's Veto**, neither Standard-legal, to
Standard decks. Owning a card is not a licence to play it: the pick costs no wildcard
but it still costs a DECK SLOT, and an illegal maindeck card is a worse outcome than a
wasted craft. `owned_role_fillers` now filters on the deck's `#: format:` exactly as
`craft_role_fillers` does (pool-absent/unverified legality = legal, matching
`legal`/`suggest`). Same shape as the `suggest --lands` bug one command over, and the
same lesson: **when two functions answer the same question for owned vs unowned cards,
diff their filters** — one of them will be missing a check. Fixing it exposed a second,
older bug underneath: `load_card_data` keys a DFC under BOTH `Front // Back` and its
front face, and both rows carry the same display name, so a double-faced filler printed
**twice**, wasting a line of a six-line list. Deduped on the display name. Both are
pinned in `tests/test_deck_models.py` (verified to fail on the un-fixed code).


## [G-46] `deck.py redundancy <id>` plans competitive CONSISTENCY the "virtual copies first" way

**`deck.py redundancy <id>` plans competitive CONSISTENCY the "virtual copies first" way.**
A singleton/highlander deck draws a random slice of its plan; the fix for competitive
quality is redundancy — but the *first* lever is **functional redundancy** (distinct,
similar-but-different cards that do the same job — "virtual copies"), which raises
consistency while keeping the singleton feel, and only THEN true 4-of duplicates. The
command buckets the deck's cards by EFFECT (functional roles + specific non-generic
synergy themes), prints each effect's **depth** (distinct cards providing it = its
virtual-copy count), flags the **thin** ones (≤`_REDUNDANCY_THIN`), and for each proposes
how to firm it to `--target` (default `_REDUNDANCY_TARGET`=4): **functional copies FIRST**
(owned/craft distinct cards via `owned/craft_role_fillers` for a role, `functional_theme_
options` for a theme), with **true duplicates only as a FALLBACK** when there aren't enough
of acceptable quality. The decision is the pure, unit-tested `plan_redundancy_fill` — it
prefers a virtual copy unless it's >`_REDUNDANCY_QUALITY_TOL` (1.5 on the 0–10 power scale)
below your best existing copy, else recommends duplicating the strongest existing card.
This is why a functionally-dense singleton (e.g. Wizardz 37b's ping win-con as a virtual
~10-of: Coruscation Mage + Firebrand Archer + Thunderdrum Soloist + Black Waltz + the token
makers) can defensibly grade A: **the tier floor counts effects, not distinct cards**, so
virtual copies score the same floor while dodging singleton variance — a notch below a
true-4-of build (the copies aren't identical — a quality tax — and can't STACK a keystone),
but a real A when the plan hinges on no single card. `/tune-deck` runs it in the competitive
flow (semi-singleton first, duplicates as fallback). It PRINTS a shortlist — grade the
virtual copies from full text like any other add.


## [G-47] Building a deck FROM SCRATCH (not a pasted list) has four helpers

**Building a deck FROM SCRATCH (not a pasted list) has four helpers** — the tooling is
strong at ANALYZING/tuning a list but these close the gap at CREATING one. **`deck.py
similar <id>`** ranks the decks most alike by central-theme overlap (cosine over the
weight vectors, GENERIC themes/tribes DAMPED via `_SIM_GENERIC_DAMP` so a shared SPECIFIC
theme drives the score, not "we both draw cards") + a color-overlap %. It marks each shared
theme `✦` when SPECIFIC (an identity theme) and splits the verdict: a `⚠ overlap` (≥60% AND
shares a specific theme — a real duplicate-identity signal) from a softer `· value overlap`
(high sim on generic value themes only — both are value decks, not the same deck), so a
diffuse good-stuff deck doesn't false-alarm as a duplicate. A generic-by-idf theme is
RESCUED to specific (✦) when it's a deck's real BUILD-AROUND spine — carried by ≥2 of its
`#: protect:` cards (`_strong_signature_themes`), so a counters-doubler deck reads counters
as its identity (30↔04 flags ⚠), while a lone protected bomb's incidental card-draw/etb tag
can't promote a diffuse deck's generic overlap into a false match. `--specific-only` scores
identity themes alone (a diffuse deck then honestly reads as sharing nothing specific). The roster "is
this deck distinct or a duplicate?" check (answers the question a from-scratch build always
raises; it's a SHORTLIST — grade the DOMINANT theme + win-con from `deck.py text`, not the
number — a shared tribe can be incidental, e.g. Druid mana dorks). **`deck.py resolve <names…>`** turns card names into
ready-to-paste deck lines `<qty> Name (SET) #` with a valid printing (exact → DFC front →
unique-substring, OWNED printing preferred; reads args or stdin, optional leading qty),
reporting unresolved/ambiguous names instead of guessing — removes the hand printing-lookup
(and the off-by-one that shipped a 59-card draft). **`pool.py --role <removal|sweeper|
counter|draw|ramp|cheat|payoff>`** filters the collection by FUNCTIONAL role (via
`classify_roles`, aliased to friendly names), so you survey owned cards by what they DO,
not just their synergy tags — the deckbuild axis `--synergy` couldn't reach.
**`deck.py screen <id> <names…>`** is the fourth, and it exists for a failure the other
three cannot touch: a candidate pile graded ONCE keeps those verdicts after the plan
changes. Deck 46's 76-card pile was screened against a "one enormous body" plan; when
the plan became "several growing lifelink bodies with an Angel sub-theme and recursion",
only the cards the user re-raised got re-graded and the rest carried stale reasoning
forward — Shrike Force, Linden, The Wind Crystal and Prayer of Binding all sat in that
bucket, each excluded for a reason that had expired. `screen` re-scores a whole list
against the deck AS IT IS NOW (fit strength, roles, shared central themes, legality,
owned-vs-craft), so an answer cannot be stale by construction. **Re-run it after any
change of plan, not once.** It carries two flags nothing else does: **`✱ multiplier`**
(as `cuts` now does), and **`★ STRICT UPGRADE`** — in-deck cards the candidate strictly
beats. That second one is the bug it was built for: **Prayer of Binding is Liminal Hold
with FLASH** — identical `{3}{W}`, identical text — and Liminal Hold sat in the 60 while
Prayer of Binding sat on the excluded list under a note comparing it to a different card
entirely. `strict_upgrades` is a deliberately conservative TEXT-CONTAINMENT test
(reminder text stripped, self-references normalised via `_UPGRADE_SELF_RE` so modern
"this creature" templating matches older "<Name>" templating): every clause of the
incumbent must appear in the candidate, at the same or lower mana value, and the
candidate must do strictly MORE. Identical text at identical cost is **redundancy, not
an upgrade** — often a good thing (virtual copies), and flagging it would fire on every
deck's own redundancy. Color identity is deliberately NOT in the test (`screen` flags
off-color separately) so a text-containment result never depends on the deck's colors.
It misses most real upgrades by design; **its silence is not a verdict**. Driven by
`/draft-deck` Stage 5 and `/tune-deck` step 6a.


## [G-48] Every role COUNT now carries its own uncertainty

**Every role COUNT now carries its own uncertainty** (`lib`-free `deck.count_conf`).
A heuristic classifier reports a false negative as a FACT: a card it can't parse
contributes 0, and `0` reads as "none" rather than "not detected". That is the single
most damaging failure this toolkit has had — deck 40a was graded on interaction 3
against a hand count of 7. `role_tally` now also returns `interaction_unread` /
`card_advantage_unread` (a broad cue fired but no role matched), **`unclassified`** (a
noncreature spell that matched NO role and tripped NO cue — the Broken Wings /
Repulsive Mutation case, the worst kind, so it is reported even though it can't be
attributed to one axis) and `unreadable` (no oracle text on file). `stats` and `tier`
render `7`, `3 +2?`, or `8 +4? (3 unclassified)`. 54 of 59 decks show uncertainty
inline — mostly the `unclassified` channel, which is exactly the queue the second
under-count sweep was mined out of. The bare ints are unchanged for `tier_band` and the F10 guard, which compare
numbers; the annotated string is what a human reads.
**The remainders are QUANTITY-WEIGHTED, like the counts they annotate.** They used to be
card counts, so `8 +4?` compared a weighted base against an unweighted remainder and a
deck running 4× of a card with no oracle text on file reported `+1?` for four unread
copies (broad-scan F-09) — understating uncertainty, which is the wrong direction for a
signal whose entire job is to stop a heuristic count reading as fact. They are deduped by
NAME first, because `role_coverage_flags` emits one entry per LINE and a card split
across two printing lines would otherwise be weighted twice. Only the annotation moved:
the bare ints feeding `tier_band` were verified unchanged on all 63 decks.


## [G-49] `deck.py shape <id>` answers WIDE vs TALL, FAST vs SLOW

**`deck.py shape <id>` answers WIDE vs TALL, FAST vs SLOW** — the structural question
themes structurally cannot: `counters` is the same tag whether they all go on one
creature or spread across twelve. Reading `#: archetype:` prose instead produced the
worst misread of the cycle (deck 30 was called a wide deck from its header while the
open question was whether a TALL counters plan duplicated it). Scores WIDE cues (token
creation, anthems, count-scaling) against TALL cues — deliberately only AMPLIFIERS
(doubling, equipment/aura pump, "where X is its power"), because the first draft keyed
on "put a +1/+1 counter on target creature" and read a 27-creature WIDE board as tall;
a single counter is wide glue too. Creature DENSITY is folded in (≥22 copies pushes
wide, ≤14 pushes tall) since a text scan can't see it. Prints the effect lists, not
just the verdict. Note it reads deck 30 as BALANCED against its own "go wide" header —
14 creatures plus counter-doublers genuinely is both, and the header is the older claim.


## [G-50] `deck.py resolve --format` warns on cards not legal in the format

**`deck.py resolve --format` warns on cards not legal in the format** (default
standard; `any` disables). Resolving a printing is not a legality check, and that gap
let Bloodchief Ascension — a TLE supplemental card — reach a finished 60-card deck
file, caught only two validation steps later by `deck.py legal`.


## [G-51] `deck.py redundancy` also lists INTERCHANGEABLE cards

**`deck.py redundancy` also lists INTERCHANGEABLE cards** (`near_duplicates`): groups
of nonland cards with identical non-empty role sets inside a 1-mana band. `redundancy`
buckets by EFFECT ("how many virtual copies do I have"); nothing answered "which of my
specific cards are the same card here", and that gap produced a real bad
recommendation — cutting Chelonian Tackle was proposed without noticing Epic Fight
already provided the fight mode. Reported as GROUPS, not pairs (a 6-card removal suite
is 15 pairs and one useful fact), split into cost bands so a 1-drop and a 6-drop aren't
called interchangeable, and cards with NO detected role are never grouped — no signal
beats a guess.


## [G-52] The VERDICT surfaces now print evidence

**The VERDICT surfaces now print evidence.** `cuts` and `swap` print full oracle text
and produced the fewest bad calls all cycle; `suggest-homes` handed out KEY /
role-player / tangential labels with no text at all, which is how Genesis Wave was
rated KEY for a deck whose engine it mills away. `suggest-homes` now always prints the
card's oracle text, and `deck.py similar --full` lists the shared nonland CARD names —
the concrete evidence behind a theme cosine that can read 84% on five shared cards,
four of them lands.


## [G-53] A CAPABILITY THAT WORKS AND IS NEVER REACHED is invisible to every correctness gate

**A CAPABILITY THAT WORKS AND IS NEVER REACHED is invisible to every correctness
gate.** Eleven gates verify that each model is right; not one can see a command nothing
runs. That is not hypothetical — it is written a few paragraphs down in this file:
`/tune-deck` sat on the command set it shipped with while `consistency`, `engines`,
`shape`, `cuts`, `flex` and the needs-aware `suggest --needs/--interaction/--ramp/
--lands` were built around it, and *"the one recommender a tune-for-interaction would
reach for is blind to the fix."* Every one of those was correct, gated, documented —
and unused. The SKILLS are the composition layer, and they were the last hand-kept
registry with no gate, exactly like `check_patterns`' coverage list (13 patterns
behind), `_INLINE_PARSE_ALLOW` (could name deleted code) and the argparse tree (no gate
ever built one). **`check_commands.py` closes it as a hard `check_all` gate**: every
`deck.py` subcommand and every runnable script must be invoked by a skill, called
programmatically by another module, or listed in `INTERACTIVE_ONLY` **with a reason** —
and a stale exemption naming a command that no longer exists is itself a failure.
Two design points worth keeping. Coverage requires a REAL call (`cmd_*`) or a skill
invocation, **not a prose mention**: the first draft matched the string `deck.py <name>`
anywhere under `scripts/`, and since every docstring here cross-references commands, it
passed five genuinely unreachable ones — a check that cannot fire, in the check written
to stop checks that cannot fire. And the first honest run flagged `audit`, `brawl`,
`rotation`, `sync`, `verify` — **all roster-level**, which is the actual finding: the
per-deck loop had `/tune-deck` and `/apply-changes`, and the roster loop had no workflow
at all. **`/roster-review`** is what closed it (triage → rotation → craft plan → Brawl
→ Arena drift), so those five are now driven rather than remembered.


## [G-54] A SET plus a sort key that can TIE is a nondeterministic output

**A SET plus a sort key that can TIE is a nondeterministic output.** `wishlist`'s
displayed `sig` changed between runs of unchanged code: `shared = ctags & central` is a
SET, and `sorted(..., key=lambda t: -idf[t])` left tied themes in set-iteration order.
`Aura`, `aura` and `enchant` all score idf 3.1135, so the signal flipped among them on
every build — and `PYTHONHASHSEED` changed it too. Nothing was WRONG in any single run,
which is why it survived: the cost was that `dashboard.html`'s `#data` island churned on
every rebuild (every Pages deploy republished a payload differing from the last for no
real reason) and the live ⟳ sync could show different signals from the local snapshot.
The fix is to make the key a TOTAL order — `(-idf[t], t)` — so ties break alphabetically
and stably; the same bug sat at two sites (`_rank_scores` and `cmd_suggest_targets`).
**Before sorting anything derived from a set, ask what happens when the key ties.** This
was found by CHECKING the "restyle is template-only" claim (rebuild twice, diff the
payload) rather than asserting it — worth keeping as a habit for any dashboard change,
since a build-to-build diff is the only thing that makes this class visible.

**The first LIVE violation of the rule, 2026-08-12 (broad-scan BS5-01).** The rule above
was written and then broken, in a command a skill runs. `deck.py similar` produced a
different output on every invocation:

    $ for s in 1 2 3 4 5; do PYTHONHASHSEED=$s python3 scripts/deck.py similar 40 | md5sum; done
    731be5ac…  0c6bffc8…  99b2adbb…  924ed4bb…  5b18b811…

Three sites, one cause. `_deck_central_weights` returned `{t: tw[t] for t in
_central_themes(tw)}` — a dict built by iterating a SET, so its key order was hash-seed
dependent; `cmd_similar` then sorted `set(aw) & set(bw)` on `-min(aw[t], bw[t])`, a key
that ties constantly; and `_theme_cosine` summed `a[t]*b[t]` over a set, so even the
similarity VALUE carried float-addition jitter that could flip a row-sort tie.

Why it mattered rather than merely being untidy: the display prints `shared[:5]` and the
⚠ headline names `top[5][:3]`, so the truncation decided WHICH themes a reader saw. Deck
40 read `✦Druid` against 40a on one run and `removal` on the next — and G-47's standing
instruction for this command is "read the ✦ SPECIFIC overlaps, not the number".

**Two things to carry forward.** First, the fix is the KEY, never the return type: two
callers do `ctags & _central_themes(theme_w)`, so returning a tuple would be a TypeError,
and the honest fix is a total order at each site that CONSUMES order (sorted dict build,
`(-weight, t)` tie-break, `sorted(shared)` before the sum). Second, a float SUM over a set
is this same bug wearing arithmetic — associativity makes the result order-dependent in
the last bits, which is enough to reorder a sort. A determinism check is cheap: run the
command twice under different `PYTHONHASHSEED` values and diff. Doing that across the
whole CLI found `similar` and nothing else — `stats`, `cuts`, `tier`, `suggest`, `audit`,
`wildcards`, `screen`, `brawl`, `rotation`, `wishlist --rank`, `pool.py` and `query.py`
were all already stable.


**ENFORCEMENT, 2026-08-12.** This rule was written after the wishlist incident and then
BROKEN in `deck.py similar`, because nothing executed it. `tests/test_determinism.py` now
runs seven read-only commands (`similar`, `stats`, `cuts`, `tier`, `suggest`, `audit`,
`wishlist.py --rank`) under two `PYTHONHASHSEED` values and compares stdout byte for byte.

It lives in the PYTEST layer rather than `check_all` for the reason G-55 gives about the
argparse tree: the check needs SEPARATE INTERPRETERS with a controlled environment, and
`check_all` imports `deck` as a module and calls `cmd_*` in-process — its memoized loaders
and absence of subprocesses are exactly what keep it at ~4s. Cost measured at 7.3s. The
consequence worth knowing: `make check` alone does NOT cover this class; `make verify` and
CI do. It carries `test_the_check_can_actually_fail`, which proves the seed reaches the
subprocess, so the seven assertions cannot go quietly vacuous.


## [G-55] NO GATE BUILT AN ARGPARSE TREE, so a broken `--help` was invisible

**NO GATE BUILT AN ARGPARSE TREE, so a broken `--help` was invisible.** `check_all.py`
imports `deck` as a MODULE and calls `cmd_*` functions directly; `main()` and the
parser only exist under `__main__`, and nothing in `tests/` constructed an
`ArgumentParser`. So `deck.py --help` crashed for four days with three green workflows
(broad-scan F-01/F-12). The cause is a rule worth knowing before you touch any help
string: **argparse renders help through `help % params`, so a bare `%` raises
`ValueError: unsupported format character` — write `%%`.** Worse, the top-level help
EXPANDS EVERY SUBACTION, so one bad string among 33 subparsers takes the whole
`--help` down, i.e. the discovery surface for the project's main tool — the very
"tool list" CLAUDE.md tells you to re-read a skill against. Now covered twice:
`tests/test_cli.py` runs `--help` on every script in `scripts/` (33 today; the test
lists the directory rather than a fixed set, so the COUNT can't go stale even when this
sentence does) plus each deck.py subcommand in a
thread pool (~2s, asserting no traceback and that argparse scripts exit 0 with usage —
argparse use is detected from SOURCE, not a hardcoded list, so it can't go stale), and
a dependency-free shell mirror in `.github/workflows/integrity.yml`, which runs on
EVERY push rather than just main + PRs. Both were verified to fail on a reintroduced
bug. One trap found while writing the CI half: the first shell extraction of the
subcommand list silently yielded ZERO subcommands and still passed, because it guarded
on `[ -z "$subs" ]` and a whitespace-only capture is not empty — a check that covers
nothing while reporting success, which is the exact failure this whole family is about.
It now guards on the COUNT (`-lt 25`).


## [G-56] `swap --apply` is the only moment a real add/cut DECISION is observable — it now records one

**`swap --apply` is the only moment a real add/cut DECISION is observable — it now
records one.** Every ranking model here (`cuts`, `suggest`, the bounded co-signals, the
whole gated stack) had been graded on argument and anchor tests and never against a
decision anyone actually made. That is the same gap CLAUDE.md records for the `Decks`
column: it read as working right up until someone MEASURED it and found a 0% actionable
rate. `deck.py swap --apply` / `apply-flex --apply` now append a row to
**`recommendations.csv`** — where `cuts` ranked the card you cut (rank/total, plus
whether it was `#: protect:`ed) and whether `suggest` surfaced the card you added in its
default top 20. Ranks are captured against the PRE-swap deck, because that is the list
the decision was made against; re-deriving one later would score against a deck the swap
already changed. `deck.py feedback [<id>]` reads it back.
**The report LEADS WITH DISAGREEMENTS, and that ordering is the whole design.** An
agreement is contaminated: you read `cuts` before deciding, so a high agreement rate
partly measures the shortlist's INFLUENCE rather than its accuracy — a metric that
cannot distinguish "the model is right" from "the model was persuasive" is the
saturation failure again. A DISAGREEMENT (you cut a card the model put in its keep half)
is a case the model got wrong whichever way the decision was reached, so it is the
informative direction. Below `_RECS_MIN_SAMPLE` (20) the report refuses to compute a
rate at all, the same restraint `parse_matches --report` and `count_conf` show.
**The rate is SEGMENTED by creature vs noncreature cut, because ONE pooled number hid
a two-fold split.** At 52 scored swaps the pooled figure read 63%, and underneath it
noncreature cuts agreed **19/21 (90%, median 10% toward "keep")** while creature cuts
sat at **14/31 (45%, median 56%)** — a coin flip. **At n=100 the split is unchanged in
kind and slightly worse in degree: pooled 60/96 (62%), noncreature 40/48 (83%, median
14%), creature 20/48 (42%, median 61% toward "keep").** The sample doubling without the
gap closing is the useful part — this was never re-weighted, so the drift is the signal
moving on its own rather than a fix regressing. A single rate averaging a healthy and
a broken channel reads as healthy: the same saturation failure as the `Decks` column at
99% and the `review` verdict firing on 22 of 63 decks. `recommendation_segments(rows,
is_creature)` takes an INJECTED classifier so the summary stays pure and a test can
supply a fake, and an unclassifiable card gets its own **`unknown`** bucket rather than
defaulting into `noncreature` — folding it in would corrupt exactly the segment that
reads as calibrated (the `lib.card_power` rule, one table over). Each segment is held
to the same `_RECS_MIN_SAMPLE` floor as the pooled rate; splitting a sample is the
moment that restraint is easiest to forget.
**The CAUSE is in `cuts` and is NOT a re-weighting candidate** — see the fit-sum note
in the `cuts` section below. The honest fix was to REPORT the weak regime, which is the
same posture as `⚠ scales w/`, `pow~` and `count_conf`: when a signal is unreliable in
a known regime, say so rather than presenting it as fact.
**"Add not surfaced" is EXPECTED and is not on its own a model miss** — `suggest` filters
to cards sharing a synergy THEME and is structurally blind to lands and off-theme
removal (that is what `--lands`/`--interaction`/`--ramp` exist for), so read that count
as "which fills the theme model can't reach."
**It is REPORT-ONLY and must stay that way.** The scoring terms are bounded and anchored
by `check_suggest` precisely so they cannot silently reorder a tuned deck; a feedback
loop that quietly re-weighted them would defeat that by construction *and do it
invisibly*, since every pure-function anchor would still pass. `tests/test_recommendations.py`
pins this structurally — no function in the scoring stack may reference the ledger — so
wiring feedback into a score requires deleting a test, which is the point: it makes the
decision visible instead of incidental. Recording is also **never fatal to a swap**: each
model call sits in its own guard, a swap whose telemetry fails is still saved, and a row
is written only AFTER the edit lands (so a rejected write leaves no phantom row).
**That guarantee covers a REJECTED write, not a REVERTED one, and the difference bites.**
A swap applied purely to MEASURE something — `cp` the deck file, `swap --apply`, read the
new vector, restore the file — leaves the ledger row behind, because the edit did land and
restoring a file is invisible to the ledger. It happened here: a Foot Elite → Requisition
Raid row recorded a decision nobody made, and the ledger's whole value is that a
disagreement is a case the model got wrong, so a fabricated row is worse than a missing
one. Prefer a `--dry-run` `swap` or a scratch COPY of the deck when you are only
measuring; if you do apply-and-revert, delete the trailing row in the same commit.


**OUTCOMES, joined 2026-08-12 (broad-scan E2).** `recommendations.csv` records what the
models said and what the human decided; `matches.csv` records what then happened. Both
existed for a cycle with nothing connecting them, so every ranking model here was graded on
its own argument plus `feedback`'s agreement rate — a number this file already warns is
contaminated, because the human reads the shortlist before deciding. An outcome is the only
signal in this project the models cannot influence.

`swap_outcomes(rows, matches)` splits each deck's W/L at its FIRST recorded swap. Per DECK
and not per SWAP, deliberately: a deck accumulates many swaps whose windows overlap almost
completely, and attributing a result to one of four changes made the same week is a story,
not a measurement. Draws and unreadable Result cells decide nothing but still count as
games played; a match with a blank Deck (the parser refusing to guess a seat) joins to
nothing rather than being borrowed into a record.

It REFUSES to read below 20 games on one side, and that is where the record sits: at the
time of writing, 365 swaps against 9 matches, 8 attributed, 3 decks with both, largest
post-swap sample n=4. The section prints the coverage so the distance from signal is
visible, and says plainly that no outcome is reported and none should be inferred. Building
it before the data exists is the point — the analysis is in place when volume arrives.

**It is banned from the seven scoring functions for a STRONGER reason than the ledger is.**
A win rate looks like ground truth, which makes it the single most tempting thing here to
feed back into a ranking. Doing so would defeat the bounded-and-anchored property
`check_suggest` exists to hold AND would point the models at an 8-match sample.
`tests/test_recommendations.py` scans for `swap_outcomes`, `MATCHES_CSV` and
`load_match_counts` alongside `load_recommendations`.


## [G-57] Match results are FREE from `Player.log` — the lines AROUND the result JSON are the load-bearing halves

**Match results are FREE from `Player.log` — the header line is the load-bearing half.**
Arena's "Detailed Logs (Plugin Support)" setting writes match events locally; that is the
same feed every third-party tracker reads, and their subscriptions buy cloud analytics,
not log access. (COLLECTION data was locked down years ago, which is why ingestion has to
undercount — see the deck-dump gotcha. MATCH results were not.) `scripts/parse_matches.py`
(`/log-matches`) turns a paste into `matches.csv`. Two line shapes are needed and **both
are required**: the `finalMatchResult` JSON carries the outcome and both players' seats
but **NOT which seat is yours** — the local userId appears only in the `Match to <userId>:`
header prefix. A paste of the JSON alone is unparseable, so the parser SKIPS with an
actionable warning rather than guessing; a 50%-accurate record would be worse than an
empty one because it looks like data. (`--me <userId>` is the escape hatch.) Three more
things the real log settled, none of them guessable from the JSON alone: the log line's
LOCAL timestamp must beat the JSON's UTC epoch (an evening session otherwise files a day
late — the sample's own header said 7/27 while its epoch resolved to 7/28), the epoch is
still the right FALLBACK when no header date exists (a blank Date sorts to the top and
can't be scoped in time), and an unmapped match is kept and surfaced, never dropped.
Deliberately stores no userId and no playerName: neither is needed for a win rate, and a
match log is not a place to accumulate identity. The scan keys on the EVENT rather than on `"finalMatchResult"`, because a
truncated paste is the expected failure and that marker sits LATE in the line, after both
seats — so any realistic width cap removed it and the match was dropped in **silence**
while the run reported success. Found by a test, and it is this project's signature bug
class one more time: the check keyed on the thing the failure destroys.
**Read the record with restraint.** Below `_MIN_SAMPLE` (20) matches `--report` refuses
to print a percentage at all, and above it prints a 95% **Wilson** interval (the naive
normal approximation is wrong at exactly these sample sizes). A win rate separates a
BROKEN deck from a fine one; it will not separate a 55% deck from a 45% one without
hundreds of games. Never write one into `#: tier:` — tier grades the LIST against the
rubric, and a small-sample rate is not evidence at that resolution, so citing one would
be precisely the stale-rationale failure `--audit-rationale` exists to catch. Same
restraint `count_conf` shows for role counts: a number that looks certain when it isn't
is the expensive kind of wrong.

**`courseId` is NOT a deck — it is the AVATAR, and the whole first pass was built on the
opposite assumption.** The field sits on each `reservedPlayers` seat next to `eventId`,
its name reads like a deck-list identifier, and the parser's docstring, its `--report`
footer and the `/log-matches` skill all documented a `#: arena: <courseId>` header as the
way to attribute a match to a repo deck. Nine real matches were recorded that way, all
with a blank `Deck`. Then someone read the values: **all eleven distinct ones across both
seats carried the literal `Avatar_` prefix** — `Avatar_Basic_BlackPanther_MSH`,
`Avatar_Basic_Galactus_MSH`, `Avatar_Basic_Kaito_NEO`, and so on. It is the AVATAR
cosmetic, a global profile setting the player changes independently of the deck, and it
identifies nothing. On 2026-08-07 the recorded value went CaptainMarvel → Galactus at
exactly the point the deck changed, which is what made it look like a deck id; on
2026-08-09 the same Galactus value covered a completely different deck. The columns are
`My Avatar` / `Opponent Avatar` now, precisely so the next reader cannot repeat it — and
the "opponent DECK is kept, that is an archetype not a person" line the privacy paragraph
used to carry was wrong for the same reason: an avatar is a cosmetic, and it tells you
nothing about what they were playing. **The general shape: a field whose NAME asserts a
meaning is a claim, not a measurement.** `Color(s)` (identity, not cost) and a DFC's
stored Mana Value (both faces) are the same failure in the card data; this is it in the
match data, and it survived a docstring, a skill and a committed CSV because nobody
looked at what the column contained.

**The deck actually played is in `EventSetDeckV3`, and the join is on TIME.** Arena writes
that line when it submits a deck for an event, 2–20 seconds before the match starts across
the whole sample. Its payload is JSON inside a JSON string and carries the Arena deck NAME,
a stable `DeckId` GUID, and a `LastPlayed` local timestamp — enough to attribute every
match except one whose log had already rotated. Four details are load-bearing:

* **The regex path is the primary one, not the fallback.** The documented extraction pipes
  through `cut`, so neither `json.loads` survives the truncation. The extractors read a
  backslash-STRIPPED copy of the raw line, which is why `\"DeckId\":\"…\"` is matched as
  `"DeckId":"…"`. `"Name"` is capital-N while every sibling attribute key is lower-case
  `"name"`, and `"EventName":"Play"` has no quote before `Name`, so neither can be confused
  with the deck's own name.
* **Timestamps beat log order.** A pure order walk breaks on the paste people actually
  produce: running the match grep and the `EventSetDeckV3` grep as separate commands puts
  every selection in one block and every match in another, and order then hands the single
  last selection to every match — one deck for the whole session, which reads as data.
* **A selection more than 12 hours before a match is refused, with a warning.** Arena
  re-submits the deck on every event join, so a real selection is seconds old; anything
  hours old means the log that held the right one rotated. Without the bound the 7/27 match
  would have borrowed an 8/07 deck. Blank is the only safe direction — an unattributed
  match is a visible gap, a wrongly attributed one is a fabricated win rate.
* **Name → repo id resolves most-explicit-first** (`--deck` → `#: arena:` header, which
  takes the Arena NAME or the GUID or both, comma-separated → the Arena name's leading
  number), and the run PRINTS every name with the route that resolved it, because a
  heuristic that ASSIGNS data has to show its work (the G-52 rule). The prefix step is
  accepted only when the id it produces is a deck that exists. Its regex is
  case-SENSITIVE on the variant letter and requires the letter be adjacent to the number:
  the first draft, `^\s*0*(\d+)\s*([a-z]?)` with `re.I`, read "07 Earth's Mightiest" as
  deck **"7e"**. Note the Arena name need not resemble the repo name at all — when
  measured on 2026-08-14, Arena's "45 The Exiles" was repo deck 45 "Exile Dividend", and 8
  of the 22 paired decks diverged the same way — so a name-similarity check would have
  REJECTED a correct match, and the number is the only part that carries the mapping.
  `--sync-names` is the RECONCILE half (adopting Arena's name for GUID-paired decks, which
  is how deck 45 came to be called "The Exiles" here). It is opt-in, so the divergence
  regrows on the next client-side rename: the number stays the only safe match key.

**Doing the whole roster: `--map-decks`.** Setting `#: arena:` one deck at a time is where
a wrong header hides, and a `#:` header naming something that does not exist is a silent
no-op — the G-68 class exactly. Every message type that mentions a deck (`EventSetDeckV3`
= the deck submitted for an event, `DeckUpsertDeckV3` = the deck just
saved/renamed/imported) nests the SAME `{"DeckId":…,"Name":…}` object, so one bounded
pattern harvests the client's whole deck list rather than one pattern per message layout.
**`DeckGetDeckSummariesV3` is NOT a third source, and the first draft of this section said
it was.** Its name promises the whole collection and it was written into the suggested
grep, the module docstring and a test's docstring on the strength of the name alone —
measured against the first real paste, Arena logs its request and a bare `<== …(id)` ack
with NO payload: 0 decks from 5 calls, against 21 from `DeckUpsertDeckV3`. The same
field-name-as-claim trap as `courseId`, caught the same way (reading the values), and the
grep now excludes it so nobody hauls in dead lines. Three rules make the
bulk write safe: the LAST name for a GUID wins, because a deck renamed in the client
appears under both and `setdefault` would keep the dead one (the G-63 first-writer-claims-
the-key trap, one file over); the `.{0,200}?` window between DeckId and Name is the whole
guard against a summary that has no Name reaching forward and labelling itself with its
neighbour's deck; and two Arena decks resolving to ONE repo deck — which is what an old
copy left in the client looks like — write NOTHING and are reported, because a header
naming the wrong one of two is worse than none: the parser would then attribute matches to
it with full confidence. Writes route through `deck._safe_write_lines`, which re-parses the
file and verifies the copy count is unchanged before replacing it, so a header edit
provably cannot touch a card line.

**Header upkeep rides along with every ingest (`sync_headers`).** A separate `--map-decks`
run is upkeep nobody performs — the G-53 shape, a working capability nothing reaches — and
any paste that can attribute a match already carries the summaries that keep headers
current. So the normal `--apply` flow runs the same plan/write machinery quietly (it
reports only what CHANGES, so a routine ingest is not buried under an all-unchanged roster
listing), with two ordering rules that are the actual content of the fix: the sync runs
BEFORE the deck mapping is built, so a header written from this paste resolves this
paste's own matches (a client-side RENAME is exactly this shape — the new name has no
prefix match and only the freshly-written GUID header can place it); and it runs BEFORE
the no-matches bailout, because the first integration put it after, and a summaries-only
paste — the `--map-decks` extraction shape fed to the normal command — died with "check
that Detailed Logs is enabled", a misleading error about a setting that was fine, without
writing the headers it carried. Both orderings are mutation-tested.

**The rolling archive (Stage 0 of `/log-matches`).** `Player.log` is overwritten on every
Arena launch, so every extraction habit has a structural hole: a session not grabbed
before the next launch is gone, and the roster's 2026-07-27 match is a permanent casualty
(its deck attribution is unrecoverable — the 12-hour bound exists to keep a rotated log's
stale selection from being borrowed in its place). A launchd job appending the filtered
lines to `~/mtga-logs/arena.log` every 15 minutes closes the hole; line-identical dedupe
(`awk '!seen[$0]++'`) is safe because every captured line shape carries a timestamp or an
id, and re-ingesting the archive is idempotent because match dedup is by `matchId`. The
setup block lives in the skill so it survives being needed only once.

Two supporting fixes came out of the same change. `load_matches` renames the pre-rename
columns on READ, because `write_matches` emits only `HEADER` and would otherwise have
rewritten an existing `matches.csv` with those cells blank — silently losing the one field
the old rows had. And the F-02 mirror guard had to learn one exception: it compares headers
and cannot tell "another file's schema" from "an earlier version of my own", so it refused
the very write that performs the migration.

**2026-08-14: that allowance was EXACT, and an exact allowance works exactly once.** It
hard-coded the single header the module emitted before the avatar rename. Adding a column
(`Ended By`, below) made the THEN-CURRENT file an "earlier schema" too — which an exact
match cannot see — so the guard would have refused the very migration write it exists to
permit, reproducing the bug by being narrow. `_is_own_earlier_schema` now asks a general
question: every column is one of MINE, in MY order, no duplicates, and the core three
(`Date` / `Match ID` / `Result`) present. That accepts any past or intermediate shape —
columns here have been both RENAMED and INSERTED MID-HEADER, so neither a prefix nor a
subset test would do — while still refusing a foreign CSV, which would have to be an
ordered sub-sequence of these thirteen names by accident. **The transferable form: a
migration guard that remembers ONE predecessor is a guard against the migration you
already did.**

**Two reason fields, and for a year only the uninformative one was stored.** `Reason` holds
`matchCompletedReason`, which is `Success` for every match that COMPLETED — by
construction. All 15 rows of the first real record read `Success`; the column carried zero
bits. Meanwhile the MATCH-scope result's own `reason` — `ResultReason_Game` vs
`ResultReason_Concede` — was read and discarded. That one varies (2 of 3 in the batch that
surfaced it) and is most of the signal at low n, which is where this record permanently
lives: a concede-win on turn three is not the same evidence about a deck as a game-win.
`Ended By` now carries it. `Reason` is KEPT rather than replaced, because a non-Success
value (a disconnect, a timeout) is genuinely worth having and simply has not fired yet.
Pre-existing rows are BLANK, not backfilled to "Game" — they were parsed before the field
was read, so the value is unknown. Six were recovered from logs still on disk, through
`parse_log` rather than by hand, and the first thing they showed was that deck 15's 2–0
was two opponent concedes.

**The verdict surface prints its evidence (G-52).** The W/L is derived from two integers —
your seat's `teamId` against the match's `winningTeamId` — and printed as a single letter.
A single inverted seat read would flip EVERY row in a paste the same direction, which reads
as a losing streak rather than as a bug, so the first fifteen matches were checked by
re-reading the raw JSON by hand, one at a time. The dry run now prints `[my team 1 · winner
1]` per new match. The fields ride on the row as underscore keys and never reach the CSV;
they key on PRESENCE, not truthiness, so a CSV-loaded row prints nothing while a parsed row
whose seat has no `teamId` prints `?` — that being the least trustworthy verdict there is,
it must not share the silent-empty branch.

**The per-deck split cannot reach the sample floor, so `--report` also POOLS.** At 106
decks the arithmetic never arrives: after a month of play the best per-deck row sat at n=4
against a floor of 20, and every new match splits further. A record that can never be read
is a record nobody keeps. Pooling fixes the denominator by answering a DIFFERENT question,
and that difference has to stay in front of the reader or the number gets used for deck
decisions it cannot support — `ALL DECKS` measures the player and the roster together, not
any deck in it. The EVENT split (Play vs Ladder) is the one cut worth making at this size,
since the two face different opposition. The `_MIN_SAMPLE` refusal is unchanged: pooling
buys a reachable denominator, not permission to read a small one, and the distance prints
as a countdown ("5 more for a read") rather than as a wall.

**The extraction recipe strips the card arrays.** `EventSetDeckV3`'s `MainDeck` is never
read — attribution uses only Name, DeckId and LastPlayed off the same line — and it is
almost the whole payload: a real 52-card selection line measures 1919 bytes and slims to
152, a 92% cut, once per event join. Both documented recipes pipe through
`sed -E 's/\\"(MainDeck|Sideboard)\\":\[[^]]*\]/\\"\1\\":[]/g'`. Slim at PASTE time,
never at capture: doing it inside `snapshot.sh` would put two forms of each line in the
rolling archive and defeat its own `awk '!seen[$0]++'` dedupe. Before this existed the
pastes were hand-trimmed in an editor, which is JSON surgery on the one line the whole
attribution chain depends on.


## [G-58] Never widen `#: colors:` for a HYBRID card — and never reject a card for a widening you don't need

**Never widen `#: colors:` for a HYBRID card, and never reject a card for a widening you
do not need.** Both halves of this were violated inside a single cycle, in opposite
directions, and each cost something real.

**The widening.** Bullseye, Death Dealer (`{B/R}` in its activation) was added to deck 26b,
and the header was widened from `UR` to `UBR` "for" it. That was wrong twice: the card is
payable entirely with red, so the deck needs no black source; and a three-colour baseline
is a WEAKER lint than a two-colour one, because the castability check measures strays
against the declared identity. Widening bought nothing and disarmed the guard — a genuinely
off-colour black card added later would have passed silently. Reverted; header stays `UR`.

**The rejection.** The mirror error is worse because it is invisible. Don & Raph, Hard
Science (`{1}{U/R}{U/R}`) was kept out of mono-blue deck 47 on the written ground that its
R colour identity "would widen `#: colors:` and cost the mono-colour manabase that is this
deck's main structural advantage". Neither clause survives contact: every pip is payable
with blue, so the manabase is untouched and `consistency` still reports every coloured card
on curve at ≥90%; and the header never needed to move. A strong card — it grants affinity
for artifacts to the next noncreature spell each time it attacks, which is deck 47's entire
premise handed to cards that lack it — sat out a whole pass for a bookkeeping fiction.

**The tooling was never confused; only the prose was.** `deck.py mana` prints
`Don & Raph, Hard Science — identity has R (hybrid — paid on-color)` under a "Castable,
but color identity strays" heading, and `preflight` renders the same fact as
`castability PASS (+1 hybrid stray, ok)`. A hybrid stray is the EXPECTED steady state of a
correctly-narrow header, not a defect to design away.

**The distinction that actually decides it is HYBRID vs GOLD, and `Color(s)` cannot show
it.** Colour identity reads `U/R` for both `{U/R}` and `{U}{R}`; only the printed cost
separates them. In the same cycle Captain Storm, Cosmium Raider (`{U}{R}`, gold) genuinely
WAS uncastable in mono-blue 47 and had to go to a two-colour deck, while Don & Raph
(`{1}{U/R}{U/R}`, hybrid) was fine there — two cards with identical identity and opposite
verdicts. This is INV-05 and the `card-mana.csv` design decision applied to a deck header
rather than to a card: read the cost from `card-mana.csv` / `deck.py mana`, never infer a
mana requirement from identity. Related but distinct: [G-32] (identity-subset castability
says nothing about whether you can pay the PIPS) and [G-35] (`mana` lints colour SOURCES
against strict pips). Neither of those states the header rule, which is why it was
re-derived wrongly.


---

# Known Issues


## [G-67] A pattern set is a whitelist, and a whitelist's misses are invisible

`deck._ROLE_PATTERNS` is the model that decides what a card *does*. It is a list of
regexes matched against oracle text — i.e. a **whitelist of phrasings** — and Magic
templates the same effect several different ways. When a card is worded a way no pattern
anticipates, `classify_roles` returns an empty set, and that zero propagates: into
`role_tally`, into the interaction and card-advantage figures the tier floor grades on,
into `cuts`' "role not auto-detected" ranking, into the `quality --vs` guard, and into
`check_all`'s own reporting. It is **never an error**, and the DEFAULT failure is a
silent under-count that every consumer treats as fact — but "never an over-count" turned
out to be false: a too-broad pattern over-counts the same silent way (see the BS2-06
exception below).

### The eight holes, all found in one 2026-08 session, none by a gate

| effect | what was indexed | what was missing |
|---|---|---|
| targeted removal | `destroy target X` | `choose target X … destroy the chosen permanent` (Quag Feast) |
| noncreature answer | `creature or planeswalker` | `creature or enchantment` |
| noncreature answer | creature/artifact/enchantment | spacecraft, vehicle |
| damage removal | `deals N damage to target` | `divided as you choose among` (Death to Our Enemies) |
| scaling damage | `equal to … power` | equal to any other expression (Combustion Technique) |
| card advantage | the `investigate` KEYWORD | a spelled-out `create a Clue token` |
| card advantage | draw effects | impulse — `exile the top card, you may play it` |
| ramp / fixing | `{t}: add {` | `{T}: Add one mana of any color` |

Every one was discovered because a human was grading a specific card and noticed the
number was wrong. That is not a repeatable process, which is the whole argument for the
gate below.

### A ninth, 2026-08-11 — and it was found the same way

Both variable-damage removal patterns assume the clause reads "deals damage **equal to
X** … **to target**". Magic also templates the target first, and that half was indexed by
nothing:

> Triumphant Chomp deals damage **to target creature** equal to 2 or the greatest power
> among Dinosaurs you control, whichever is greater.

A `{R}` sorcery that kills anything up to a 12/12 scored ZERO functional roles, so it was
the "1 unclassified noncreature" `stats` reported — and `cuts`, which folds role coverage
into its ranking, listed it as deck 28's **weakest card**. The user kept it on the merits
and said so; that objection is what surfaced the hole.

The added pattern is `deals? damage to (any target|… target (?!player|opponent|spell))
[^.]{0,60}?equal to`, and the exclusions extend BS2-06's guard rather than inventing one:
player-only burn must not read as spot removal, and "target **spell's controller**"
(Refuse) is a player too — that was the single false positive when the pattern was
measured against the whole pool, which is the measurement this rule demands before
widening a role bucket. Roster before/after: **2 decks moved** (28 interaction 6→7, 28a
3→4) and **ZERO tier floors**, the same shape K-14 reports. `role_baseline.txt`'s entry
for Triumphant Chomp was pruned as part of the fix — a baseline listing a card that now
scores a role is a test double encoding the old behaviour.

### The largest one, and why it mattered

The ramp pattern was `\{t\}: add \{` — a literal `{` required right after "add". That
reads `{T}: Add {G}` and misses `{T}: Add one mana of any color`, which is how Magic
templates **every rainbow source in the format**. Bloom Tender, Great Divide Guide,
Springleaf Drum and Agatha's Soul Cauldron all scored **zero roles** — in the three decks
(54, 54a, 54b) whose #1 graded weakness was, at that moment, the manabase.

Deck 45 is the other worked case: built entirely on cast-from-exile, it measured **card
advantage 0** because impulse was not indexed at all, and nothing complained.

### The one measured OVER-count (broad-scan BS2-06, fixed 2026-08-07)

This anchor claimed the failure mode was *always* an under-count. The second broad scan
falsified that: the fixed-damage removal pattern — `deals? \d+ damage to
(?:target|any target|another target)` — had no target-type guard, so **damage aimed at a
player** classified as spot removal and counted as interaction, the axis `tier_band`
grades on. Its own sibling three lines down (the scaling-damage pattern) carried exactly
the missing guard, with a comment calling it load-bearing. 89 pool cards of player-only
burn (HYDRA Assault Robot, Shocking Sharpshooter, Ozai's Cruelty …) matched only this
pattern; **14 roster decks over-reported interaction** (deck 10 read 15 against a real
12), feeding `tier_band`, `audit`'s thin-verdict, `deck_needs["int_short"]` and `cuts`'
is-interaction guard. The fix added `(?!(?:player|opponent)\b(?! or planeswalker))` —
the trailing clause keeps the 42 pool cards templated "target player **or planeswalker**"
counted, because those CAN answer a planeswalker. Measured roster-wide before landing,
per the K-14 discipline: 14 decks moved, **zero tier floors moved**, two honestly-roleless
cards (Hawkeye's player-only burn mode; Ozai's Cruelty) baselined from full text, and the
nine `#: tier:` figures the change staled were re-grounded in the same commit. The
transferable lesson: an over-broad pattern is as silent as a missing one, and the
roster-wide before/after diff is the only check that sees either direction.

### The gate

`scripts/check_roles.py` + `scripts/role_baseline.txt`, on the `keyword_baseline.txt`
design. Scope is every nonland, non-blank-text card in any `decks/*.txt`; it reports the
ones `classify_roles` returns nothing for and that are not baselined. Three deliberate
choices:

- **Deck-scoped, not pool-scoped.** A ~30k-card pool sweep is noise. A card in a deck is
  one some model has already been asked about.
- **Soft, not hard.** A genuinely roleless card — a vanilla body, a pure combat trick, a
  build-around whose value sits on another card — is a legitimate zero, and it breaks no
  invariant.
- **Read as a DELTA, not a target.** The baseline is 367 and a meaningful fraction of it
  is legitimately roleless. The gate's job is that the set only ever shrinks and that a
  NEW zero gets looked at once.

### Two habits the fix earned

**Write a new pattern's fixture from the card's real text, never a paraphrase.** The first
draft of the ramp fix used "add one mana of any color" — but Bloom Tender's actual text is
the Vivid form, *"For each color among permanents you control, add one mana of **that**
color"*. The paraphrase would have shipped a pattern for a card that does not exist. The
test written from the card's real text is what caught it, and it caught it *after* the
roster diff had already been run and looked clean.

**Check for a test double encoding the old behaviour before you run the suite, not after.**
`check_suggest.py` anchor 15 and its pytest twin asserted that a rainbow fixer ranks
most-cuttable — on the explicit premise that it carries "no synergy tags **and no
classified role**". The ramp fix falsifies the second half, so the anchor started failing
for the right reason. It was re-premised rather than deleted: role credit makes a fixer
*less* cuttable, not uncuttable, so the `add_is_fixer` guard it protects is still load-bearing.

### 2026-08-19: four more holes, found by triaging the `check_roles` backlog

The earlier holes were each found by a human reading one card. This pass worked the other
way round — down the 30-card `check_roles` zero-role list — and found four, of which the
largest had been sitting in plain sight for the life of the pattern set.

| Hole | Templating no pattern read | Pool cards |
| --- | --- | --- |
| Removal — back-referenced target | "Choose two target creatures … deals 5 damage to **that creature**" (Trial of Agony, Spiked Pit Trap) | 3 |
| Removal — optional target on the scaling half | "deals damage equal to its power to **up to one** target creature" (Thorin, Mountain-king + 7) | 8 |
| Card advantage — combat trigger, other word order | "at the beginning of **combat on your turn**, draw a card" (Nexus of Becoming, Mister Fantastic) | 2 |
| **Team pump — tribal lords** | "**Other Elves** you control get +1/+1" — the pattern hard-coded the noun `creatures` | **146** |

The anthem hole is the instructive one. It is not an exotic templating; it is how *every
lord ever printed* is worded, and the roster has tribal decks built out of nothing else.
It survived because anthem is not one of the axes `tier_band` grades, so no floor ever
moved and no gate ever complained — the invisibility G-67 is about, in its purest form.
Twelve of the cards it fixed were already sitting *acknowledged* in `role_baseline.txt`,
which is exactly what a baseline is for: it kept them nameable until someone looked.

Two false-positive classes were measured and excluded before anything shipped, both on the
back-reference pattern: "that creature's **controller**" is reach at a player, not an
answer (Blur of Blades), and "that creature" also back-references a **blocker** in ordinary
combat triggers (Ashmouth Hound, Ornery Goblin). Requiring an explicit upstream "choose …
target creature" and a `(?!'s)` guard takes the pattern to 3 matches, all true.

The K-14 before/after diff over all 113 decks: **3 decks moved on a graded axis (26a +1
interaction, 26b +1 card advantage, 74 +1 interaction), ZERO tier floors moved.** Two
`#: tier:` figures went stale as a direct consequence and were re-grounded — which is the
G-27 rationale sweep doing its job, and the reason to run the diff at all.

**The transferable habit:** the zero-role backlog is a *worklist*, not a chore. Reading it
end to end costs one pass and found in four cards what a year of incidental discovery
found in nine. What remains after this pass is mostly not holes at all — 11 of the 26
still-unclassified cards are Equipment (attach / equip / hone counters), a card class this
taxonomy has no bucket for. That is a TAXONOMY question, not a pattern question, and the
two must not be confused: adding a bucket re-scores every deck that runs the type.

### 2026-08-27: the per-turn engine family — K-14's shape, one bucket over

The deck-49 and 68b tuning sessions each surfaced a card graded "no detected role" while
being its deck's engine: **Ouroboroid** ("At the beginning of combat on your turn, put X
+1/+1 counters on each creature you control") and Dragonmaster Outcast (upkeep Dragon
factory). Cause: every `Payoff / engine` pattern was **`whenever`-shaped**, so the same
payoff on a per-turn clock scored zero — the literal K-14 failure (all Card-advantage
patterns were trigger-shaped) recurring in the neighbouring bucket. The widening argument
is also K-14's: a beginning-of-your-phase trigger is repeatable BY CONSTRUCTION.

The pattern scopes to YOUR phases (`combat on your turn | your upkeep | your end step |
each of your turns`) with the same payoff alternation as the whenever catch-all, plus the
non-`a` counter quantities (`X`, `two`, `that many`) the catch-all still misses. Scoping
is what keeps out the two measured negative classes: a symmetric each-player gift
(Howling Mine) and an opponent-scoped denial clause (Urabrask, Heretic Praetor — whose
"draw a card" sits inside an opponent-upkeep replacement).

Measured before shipping, per this rule's own discipline: **+187 pool cards** (14-card
random sample read end to end — all genuine engines, zero false positives), **47 roster
cards** of which **19 were previously ZERO-role**, **60 of 114 decks' Payoff counts up**
(deck 60: 0→2), and the axes that grade: **interaction 0 moved, card advantage 0 moved,
tier floors 0 moved**. The only quality-vector changes were 15 decks' "unclassified"
uncertainty lists shrinking — the confidence channel getting more honest, which is the
change working as intended. 21 `role_baseline.txt` entries pruned (`--update-baseline`);
the 138-entry tag-disagreement baseline was untouched.

**Family B — evasion grants (the Delney half) — measured and DECLINED.** 47 zero-role
roster cards mention unblockable/menace, but nearly all are native-evasion *bodies*, and
evasion is already counted where it decides something: the quality vector's **reach** axis
reads `_EVASION_TAGS`, and since G-80 a granted keyword lands in the tag model that feeds
`cuts`/`suggest` fit. Delney's own mis-rank was fixed by the G-40 multiplier co-signal.
A new "Evasion" role would be a TAXONOMY change (ROLE_ORDER + IMPACT_ROLES + every stats
display) that double-counts reach and fixes no live mis-rank — the same
taxonomy-vs-pattern line the 2026-08-19 pass drew for Equipment.

### Relationship to the neighbouring rules

G-53 says a capability that works and is never reached is invisible to every correctness
gate. This is the same shape one layer down: **a pattern that was never written is
invisible too.** K-12 says the role counts under-count and to read the uncertainty channel
— that is the symptom; this is the cause, and `check_roles` is the instrument.


## [K-01] A handful of recurring Universe-Beyond flavor *mechanics* (Vivid, Job select, Opus, Increment, I

A handful of recurring Universe-Beyond flavor *mechanics* (Vivid, Job select,
Opus, Increment, Infusion, Paradigm, Disappear, Tiered, **Jump**) aren't in
`tag_synergies.py`'s keyword→theme map, so they're tagged verbatim. They live in
`scripts/keyword_baseline.txt` — the acknowledged-but-unindexed list — so the radar
stays quiet about them; theming them is ROADMAP Tier 1.
**Vivid is the cautionary one on this list:** an unindexed keyword is not inert, it is a
hole every tag-gated predicate inherits — `_is_color_fixer` gated on a `ramp`/`mana` tag
and so read the roster's two best fixers as non-fixers (see the fixer-overlay gotcha).
**`renew` and `triple` were the standing pair, and they triaged in OPPOSITE
directions** — which is the argument for doing this per-keyword rather than in bulk.
`renew` (Tarkir: Dragonstorm, 14 pool cards, every one on the same template) is a real
mechanic of exactly the `forage` shape — a COST plus an EFFECT — so it maps to the two
resources it touches: **`["graveyard", "counters"]`**, since it is activated FROM your
graveyard and puts counters on a creature. Deliberately NOT `sacrifice` (nothing is
sacrificed) and NOT `recursion`: the card is EXILED to pay for the counters and never
comes back, so a renew card in the yard is a resource to spend, not a rebuy, and tagging
it recursion would point reanimator decks at cards that do not recur.
**The mapping changed ZERO stored tags, and that is the forage lesson at full strength.**
All 14 cards state the template without reminder text ("Exile this card from your
graveyard: Put a +1/+1 counter …"), so the TEXT rules already earned both tags —
`tag_synergies --merge` tagged 0 rows and no pool row would change. The mapping's real
job is to DECLARE the mechanic: that silences the radar, and it permanently exempts the
keyword from `is_noise_keyword`, which matters the day a set ships with only one renew
card. Note a mapped keyword KEEPS its literal tag (`forage` does too) — mapping adds the
themes, it does not replace the name.
**`triple` is not a mechanic at all** and must not be themed: Scryfall is surfacing the
ordinary WORD from "deals triple that damage" (Fiery Emancipation, City on Fire) and
"Triple target creature's power" (Tifa's Limit Break). Three unrelated cards, no shared
template. Its sibling **`double` appears on the very same card and was already in
`keyword_baseline.txt`**, so `triple` goes there beside it — following the precedent
rather than inventing a theme. It is baselined rather than denylisted because
FLAVOR_KEYWORDS is for card-UNIQUE flavor ability names, which a common English word is
not.
The lesson worth keeping: **a standing warning is a decision nobody has made yet.** These
two fired on every `check_all` run for several cycles, which is the saturation failure
this file documents elsewhere — a channel that always fires reads as working, and a
genuinely new mechanic arriving beside them would have been invisible.

### 2026-08: the remaining ten, triaged one at a time (broad-scan H-6)

Seven were themed, three were left. Every mapping's DELTA was measured before landing,
because K-02's whole point is that a mapping's value is invisible without one — most
cards quote reminder text the TEXT rules already read, so the map earns its keep on the
tail that states the keyword bare.

| keyword | pool cards | themes | cards that GAINED a theme |
|---|---|---|---|
| vivid | 17 | `multicolor`, `payoff` | 17/17 |
| job select | 16 | `equipment`, `tokens` | **2**/16 |
| opus | 11 | `spellslinger`, `payoff` | 11/11 |
| increment | 10 | `counters`, `spellslinger` | 10/10 |
| infusion | 13 | `lifegain`, `payoff` | 13/13 |
| disappear | 9 | `sacrifice`, `aristocrats` | 9/9 |
| paradigm | 5 | `exile cast`, `card advantage` | 5/5 |

`vivid` scales with "the number of colors among permanents you control" — the same
family as `converge` (colors of mana SPENT), hence the same theme. Nothing in the text
rules reads a colour COUNT, which is why 17/17 gained both, and why K-04's fixer overlay
was blind to Bloom Tender for so long. `job select` is the K-02 shape at full strength:
14 of 16 print the reminder text ("create a 1/1 Hero token, then attach this to it") and
already tagged; the two that state it bare are the reason the map exists. `disappear`
gets `morbid`'s exact pair, deliberately — its known adjacency to BLINK is left untagged
because several disappear cards accumulate +1/+1 counters, which blink ERASES (G-42), so
a `blink` tag would recommend a package that fights half of them. `paradigm` is K-07's
`exile cast` by definition: cast a free copy of your own exiled spell each main phase.

**The three that were left, each for a different reason — this is why bulk triage is
wrong:**

* **`jump` — a SOURCE artifact, and the most instructive of the three.** It reports 13
  cards, of which **11 are `Jump-start` cards**: Scryfall lists both "Jump" and
  "Jump-start" in their keyword arrays. Only Freya Crescent and Kain genuinely have Jump
  ("during your turn, this has flying"). Mapping it to `evasion` would have put that
  theme on 11 unrelated graveyard spells. **A keyword's reported count is not its
  population** — check what the cards actually say before believing the tally.
* **`tiered` — a cost SHAPE, not a resource.** "Choose one additional cost", with
  escalating modes. Its six cards span burn (Fire Magic, Thunder Magic), bounce (Ice
  Magic), lifegain/protection (Restoration Magic) and pump (both Limit Breaks), and the
  text rules already tag each correctly. Any single theme would be wrong for five of
  them, and a new theme for six cards is the fix K-09 warns off.
* **`triple`** — already triaged out once, unchanged. Tiered cards also emit `Double`,
  `Final Heaven` and `Somersault` as keywords, which is the same artifact as `jump`.

Note the follow-through this required: K-10 mandates rebuilding BOTH tag stores after a
pattern edit, and the mechanism meant to enforce that turned out to be disarmed — see
[G-18]'s BS3-02 entry, which was found by this very edit coming back a no-op.


## [K-02] `forage` was THEMED rather than baselined, and the 7-of-9 split is the lesson

**`forage` was THEMED rather than baselined, and the 7-of-9 split is the lesson.**
It is a COST — "exile three cards from your graveyard or sacrifice a Food" — so it maps
to `["graveyard", "food"]`, the two resources it consumes. Deliberately NOT `sacrifice`:
the keyword only means the card MAY pay with a Food, and the cards that really do
sacrifice earn that tag from their own text. **Mapping it changed only 2 of the 9
forage cards**, because the other 7 quote the reminder text — which contains the words
"graveyard", "sacrifice" and "Food" — and so already earned the tags from the TEXT
rules. The two that changed (Traverse Valley, whose entire text is "Kicker—Forage.",
and Euru, Acorn Scrounger) carry the keyword with no reminder, and were tagged neither.
So a text-only tag model looks like it works on this mechanic right up until it meets a
card that states the keyword bare — the keyword map is what covers that tail, and the
gap is invisible unless you check the cards whose text OMITS the reminder. Note the
graveyard side EMPTIES the yard; the tag can't express direction, and that asymmetry is
the zone-conflict detector's job (`_GY_HATE_*` / `_GY_NEED_*`), not the tag model's. Card-*unique* flavor ability
names (Firaga, Wave Cannon, Murasame, and the Marvel signature moves — Trick Arrows,
Radar Sense, Technopathy, …), which Scryfall also reports as keywords, are dropped
via the `FLAVOR_KEYWORDS` denylist so they don't pollute the tags.
**Triage a new set's keywords promptly, and triage on the right axis.** When MSH
shipped, its 27 signature moves went unindexed: `check_all` emitted 27 soft warnings
on EVERY run — saturating the one channel the radar exists to use — and 11 leaked
into the Synergies vocabulary, where `lib.pool_ability_model`'s tag-idf scored a
one-card tag as near-maximally distinctive and inflated those cards' `Uq`. The test
is **card-uniqueness across the POOL, not the collection**: `jump` reads as one
*owned* card but Kain and Freya both carry "Jump — During your turn, ~ has flying",
so it is a real mechanic and belongs in the baseline, NOT the denylist. Both
directions are guarded — `check_keywords.check()` flags an unindexed keyword,
`check_keywords.flavor_overreach()` flags a denylisted word that turns up on ≥3
owned cards, is ALSO mapped in `KEYWORD_THEMES`, or is named in `deck.ENGINE_THEMES`
as a real engine mechanic. That last cross-check exists because `harmonize` — a
graveyard self-recursion keyword deck.py counts as a graveyard ENABLER — sat
denylisted for a full cycle: the collection holds exactly ONE Harmonize card, so the
owned-count signal could never reach the threshold. **Card-uniqueness is judged across
the POOL, and a keyword another subsystem already treats as a mechanic is never flavor.**
That rule is now MECHANICAL rather than hand-kept: `tag_synergies.is_noise_keyword`
drops a keyword carried by exactly ONE card in the corpus, so a new set's signature moves
are suppressed with no code change. It engages only when `card-mana.csv` is POOL-scoped
(`build_mana.py --pool`) — at library scope a pool-wide mechanic can sit on one owned
card (harmonize did), so below the corpus floor it falls back to the explicit list rather
than guess. A keyword in `KEYWORD_THEMES` or named in `deck.ENGINE_THEMES` is never
suppressed. `FLAVOR_KEYWORDS` remains an override for what the corpus can't settle, and
`check_keywords.known_keywords()` counts the heuristic's drops as known so the radar
doesn't re-report them as new mechanics.


## [K-03] `tag_synergies.py` text-tags fixing + topdeck-value engines

**`tag_synergies.py` text-tags fixing + topdeck-value engines** so they stop
hiding under `selection`/`tokens`: "cast/play … from the top of your library" →
`card advantage` (Vizier of the Menagerie, Realmwalker, Bolas's Citadel); "spend
mana of any type / as though it were any color" → `ramp` (Vizier, Fist of Suns);
a card that makes a **`land token`** → `ramp` (the regex requires the phrase *land
token* directly, so a creature token whose ability merely mentions "land" — Gysahl
Greens, Fat Chocobo — isn't mis-tagged); and a card that turns lands into **"every/
all/each basic land type"** → `mana` (rainbow fixing: Overlord of the Hauntwoods'
Everywhere token, Energybending) — so these surface on ramp/value in `suggest` /
`suggest-homes` / `cuts` instead of hiding under `tokens`. **The residual is now
mostly closed for detectable fixers:** a card whose fixing value SCALES with the
target deck's color count used to mis-grade as *role-player* when it was really
KEY, so `suggest-homes` now applies a **color-count-aware fixer overlay**
(`_is_color_fixer` + `_fixer_rate` + `_fixer_boost`, guarded by `check_suggest`
anchors 6 and 15) — a rainbow fixer reads **KEY in a 4+-color deck / role-player in a
3-color one** (Overlord → decks 17/21a, previously role-player/tangential). The
remaining residual is only a fixer whose value scales with color count but whose text
lacks an explicit any-color / basic-land-type cue (so `_is_color_fixer` can't see it)
— grade those from full text (why the shortlists print "grade from text").

**2026-08, the same invisibility one theme over (Gilgamesh, Master-at-Arms):** his text
digs six cards for "Equipment cards" — an equipment-MATTERS payoff — but because he never
equips, attaches or enters as Equipment, the tagger gave him `Human; Samurai; selection`
and no equipment theme. `suggest-homes` therefore ranked him tangential everywhere and
never surfaced deck 39 (Starforge, 13 Equipment), his objectively best home; the fit was
found only by a human asking "what does this card LOOK FOR" and counting it in the deck
(13 Equipment → ~1.3 hits per dig, twice per turn cycle). The rule generalizes K-03's
residual from fixers to any card whose value keys a card TYPE its own type line and
keywords don't carry.


## [K-04] The fixer overlay recommended cutting the BETTER fixer, and it took three separate blind spots t

**The fixer overlay recommended cutting the BETTER fixer, and it took three separate
blind spots to do it.** `suggest-homes "Guy in the Chair"` ({2}{G}, `{T}: Add one mana
of any color`) rated it **KEY at fit 70 for deck 13** and proposed cutting **Prismatic
Undercurrents**; for deck 17 it proposed cutting **Bloom Tender**. Both incumbents are
strictly better fixing than the card being added. Every gate was green throughout,
because each piece was individually correct.
(1) **A TAG GATE made the predicate a hostage of the keyword map.** `_is_color_fixer`
required `ctags & {ramp, mana}`. Bloom Tender (`{T}: For each color among permanents
you control, add one mana of that color`) and Prismatic Undercurrents (fetch X basics,
X = your colour count) both key off **Vivid** — which sits in `keyword_baseline.txt` as
acknowledged-but-unindexed and therefore tags `vivid`, matching nothing. So the two
best fixers on the roster read `is_fixer=False` while a mediocre dork read True. The
fix reads TEXT ONLY; the strictness the tag was standing in for now lives in requiring
**mana / land-type context**, so "protection from the color of your choice" still fails.
The general lesson: *a predicate gated on a derived tag inherits every hole in the
tagger* — and `keyword_baseline.txt` is a list of known holes.
(2) **The boost read only the deck's colour count, never what the fixer BUYS.**
Overlord of the Hauntwoods (a permanent land token with every basic land type) and Guy
in the Chair collected the identical +16 and the identical automatic KEY. `_fixer_rate`
splits **BROAD** (several colours at once, a mass grant, or colour-agnostic spending
permission — full value at any cost) from a **SINGLE** any-colour source (discounted by
mana cost, floored, never zero), and the KEY promotion is gated on `_FIXER_KEY_RATE`.
Guy in the Chair drops to role-player; Bloom Tender / Prismatic Undercurrents / Vizier /
Enduring Vitality all rate 1.0 and read KEY.
(3) **`_weakest_cut` was computed BLIND to the card being added** — the caller asked
only "what is this deck's weakest card". The keep-score is theme-fit + role credit and
NEITHER has a fixing term, so a fixer (few tags, no classified role) sorts to the TOP
of the cut list in exactly the multi-colour decks that need it. It now takes
`add_is_fixer` and excludes incumbent fixers when the add is one: swapping fixing for
fixing is a wash, and the ranking cannot see which is better. Deliberately NOT a
general same-role exclusion — removal and card advantage already reach the keep-score
through `_role_credit`, so excluding those would double-count. Fixing is the resource
the score is blind to, which is why it needs the guard.
**Two process notes worth keeping.** The roster-wide before/after diff (CLAUDE.md's
own rule for pattern edits) was load-bearing *twice*: the first sweep silently dropped
**38 real fixers** by omitting `any one color` / `any of the exiled card's colors`, and
it added **190** by counting a **Treasure token's parenthetical REMINDER text** ("It's
an artifact with `{T}, Sacrifice this token: Add one mana of any color.`") — which would
have made ~150 pool cards read as manabase fixers, the saturation failure again. Reusing
`_REMINDER_RE` fixes the second; Chromatic Sphere states the same ability as REAL text
and correctly survives. Net after both corrections: 304 → 377 recognised fixers, and
`check_all` output is byte-identical (the overlay is scoped to `suggest-homes`). And
**anchor 6 had to be rewritten, not extended** — it asserted that rainbow text with no
fixing tag must NOT qualify, using *Overlord's own ability* as the negative example. The
anchor was pinning the bug. When a gate blocks a fix, check whether it encodes the
intent or merely the old implementation.


## [K-05] `tag_synergies.py` text-tags LIFE AS A COST (`pay life`) — an entire archetype the tag model cou

**`tag_synergies.py` text-tags LIFE AS A COST (`pay life`) — an entire archetype the
tag model could not see.** 351 pool cards (2.2%) spend YOUR life for an effect and none
carried a tag for it, so deck 42's whole thesis was invisible: Dark Confidant, the most
on-thesis card available for an Orzhov life-as-currency deck, read `tangential` in
`suggest-homes` on a shared creature type. Scoped to YOU losing life — "each opponent
loses 2 life" is a DRAIN effect, the opposite card — with a payoff side ("whenever you
lose life", "if you've lost life") the way `lifegain` also tags cards that only CARE.
At 2.2% it reads as a SPECIFIC theme, which is the point: deck 42 now reads KEY.


## [K-06] `tag_synergies.py` text-tags HEIST (`heist`) — casting cards you don't own

**`tag_synergies.py` text-tags HEIST (`heist`) — casting cards you don't own.** 82 pool
cards (0.52%), so it reads as maximally SPECIFIC to the idf model: right for a build-around
and well clear of the 4-card floor that got a `clone` tag rejected. Before it existed, the
spine of a theft deck was invisible — Dream Harvest, Outrageous Robbery, Kotis, Laughing
Jasper Flint and Rakdos, the Muscle all carried a blank or near-blank Synergies cell.
**CHECK `MECHANIC_RULES` FOR THE NAME BEFORE ADDING A THEME.** The first draft was called
`theft` — which was already taken by the "gain control of" rule (Act of Treason, Agent of
Treachery, stealing a permanent already on the battlefield). Reusing the name silently
UNIONED the two: 93 gain-control cards merged in, taking the theme from 81 to 174 cards and
destroying exactly the specificity that makes an idf theme useful — **and `check_all` stayed
green throughout, because a tag collision breaks no invariant.** The two effects are
mechanically different and a deck built on one is not helped by the other, so they stay
separate tags (`heist` = cast their card, `theft` = gain control of their permanent).
Matching needs TWO parts with a BACKWARD PROXIMITY window, because the cast clause and the
opponent's zone usually sit in DIFFERENT SENTENCES ("…exiles the top card of their library.
You may cast it") — a same-sentence regex structurally cannot see the commonest templating.
Both halves are required so the large self-exile families (impulse, foretell, adventure,
plot) stay out. Four pattern bugs surfaced while building it, every one found by reading
real cards rather than testing the regex against strings written to match it: `(?:cast|play)`
without `\b` matched the `play` inside "each PLAYer … from their graveyard" (13 graveyard-HATE
cards tagged as heists); `(?:an?|each|that )?` carried a trailing space on `that ` but not
`each`, so "from EACH opponent's graveyard" never matched; the zone pattern assumed one word
order and missed "from THE TOP OF target player's library"; and the opponent-subject branch
let its gap cross a comma, so "if an opponent lost life this turn, exile the top two cards of
YOUR library" read as a heist. All three patterns are registered with `check_patterns.py`.


## [K-07] `tag_synergies.py` text-tags SELF-EXILE CASTING (`exile cast`) — the sibling theme to `heist`

**`tag_synergies.py` text-tags SELF-EXILE CASTING (`exile cast`) — the sibling theme to
`heist`.** `heist` is deliberately narrow (cast a card that was THEIRS), and that
narrowness left a real archetype untagged: the impulse / Warp / Plot / Foretell / Adventure
family casts from exile too, and the payoffs ("whenever you cast a spell from exile",
"spells you cast from exile cost {1} less", "cast a spell from anywhere other than your
hand") reward BOTH halves. 266 pool cards, 1.68% — specific by the idf model, and it is
what makes decks 45/45a gradeable as a single archetype rather than a pile of unrelated
exile cards. `is_exile_cast_text(type_line, text)` treats an **Adventure type line** as an
automatic enabler (the mechanic IS cast-from-exile, and no oracle phrasing states it), then
matches `_EXILE_CAST_ENABLE` (the keyword family) or `_EXILE_CAST_PAYOFF`. Kept SEPARATE
from `heist` on purpose — the two only look alike; a deck built on casting your own exiled
cards gets nothing from an opponent's graveyard, which is exactly the mistake the
`theft`/`heist` collision taught.


## [K-08] `keyword_frequencies()` counts DISTINCT CARDS, not rows

**`keyword_frequencies()` counts DISTINCT CARDS, not rows.** It backs
`is_noise_keyword`'s one-card-in-the-corpus test, and the mana file stores a DFC under its
full `Front // Back` name while other tables key the front — so a two-faced card could
contribute two rows and clear the "carried by exactly one card" floor without a second
card existing. "Goblin Formula", a genuinely card-unique flavor keyword, escaped the noise
filter that way. Front-names are collapsed into a set before counting.


## [K-09] Three phrases where `tags_for` and `classify_roles` disagreed on the SAME text

**Three phrases where `tags_for` and `classify_roles` disagreed on the SAME text**, each
leaving a card with a completely blank Synergies cell and therefore invisible to every
tag-based recommendation. All three are ALIGNMENT fixes, not new concepts: `draw cards
equal to` → `card draw` (The Ten Rings sat in a deck untagged), `gain(s) life equal to`
→ `lifegain` **and** the Lifegain ROLE (Exsanguinate read no roles at all; 68 pool
cards), and `costs {N} less` → `cost-reduction`, which already existed on 167 pool cards
but only ever arrived via the KEYWORD map (affinity/delve/warp/sneak/plot), so a card
that plainly SAYS it costs less had nothing. Pool blanks 417 → 384. **Deliberately NOT
fixed:** a `clone` tag for the four remaining "becomes a copy of" cards — that would be
a new theme for four cards rather than an alignment. The residual 384 is a long tail of
genuinely un-themeable effects (Oust, Exploration, Wish).


### The first instance ON A GRADED AXIS, 2026-08-19 (BS6-10)

The three phrases above cost a card its **Synergies cell** — bad, but the failure is visible:
a blank cell shows up in the tagger's own coverage counts. The disagreement is worse when it
runs the other way, because then nothing is blank and nothing looks wrong.

**Dead Weight** is the worked case. `tag_synergies` tags it `removal` — correctly, off
`Enchanted creature gets -2/-2` — while `classify_roles` returned an EMPTY set, because
`_ROLE_PATTERNS` had no removal-Aura templating (G-67). So the card was simultaneously a
removal card to the tag model and a roleless card to the role model, and it was the ROLE
model that feeds `role_tally` → the interaction figure → `tier_band`. Nothing was blank;
`check_themes` was green; `check_roles` was green (the card is unowned, and that radar is
roster-scoped). The disagreement was only visible by asking the two models the same question
and comparing.

**That comparison is cheap and worth re-running when either model changes.** A sweep for
"tagged `removal` but no `Removal (spot)`/`Sweeper`/`Counter` role" returns **388** pool cards
after the BS6-10 fix — of which **250 are deathtouch bodies**, where the divergence is
correct: the tagger is making a claim about a BODY, not about spot removal. That leaves **138
to read**. Do not treat the raw count as a defect total; subtract the known-legitimate class
first, then read what is left, the way the zero-role backlog is read.

**And note why this sweep is the tractable form of the "scan the pool" idea.** A pool-wide
ZERO-ROLE scan is what `check_roles._roster_cards` deliberately refuses — 5,368 nonland pool
cards score no role, which is 33% of the pool and unreadable as a worklist. The DISAGREEMENT
between two models is two orders of magnitude smaller and is what actually surfaced Dead
Weight. If a pool-scoped radar is ever built, build it on disagreement, not on zero.

The pool-blank residual stands at **380** and is still the long tail the rule describes
(Oust, Exploration, Wish). A new theme for four cards is still not the fix.

### It is a STANDING GATE now, not a measurement someone ran once (2026-08-19)

The comparison above was run by hand to find Dead Weight. `check_roles.py --tags` makes it
permanent: a pool-scoped sweep for cards the tagger calls `removal` from their TEXT while
`classify_roles` scores no interaction role, baselined at 138, folded into `check_all` as
a soft warning, with `--update-tag-baseline`, `--max-new` and the G-69 delta report.

**Two design choices are the whole reason it is readable.**

First, it is scoped by CONSTRUCTION rather than by an allowlist. It reads the tagger's own
`MECHANIC_RULES` predicates live — never a copy, because comparing a model against a stale
imitation of itself is precisely the drift this sweep exists to detect — and the KEYWORD
path is excluded because `deathtouch`/`fight` map to `removal` through `KEYWORD_THEMES`,
a different table this never touches. That exclusion is **250 of the 388** raw
disagreements; an allowlist would have had to enumerate them and would have rotted.

Second, it asks the NARROW question. The obvious design — a pool-scoped zero-role radar,
which is what the broad scan originally proposed — was measured and rejected:
`check_roles._roster_cards` already refuses pool scope in its docstring, and the numbers
back it. **5,368 nonland pool cards score no role, 33% of the pool.** The disagreement set
is 138. Build a radar on disagreement, not on zero.

Watched failing at introduction: removing the pattern that fixed BS6-10 brings back 16
disagreements, Dead Weight among them.

## [K-10] `tag_synergies.py` also text-tags MECHANICAL-SYNERGY payoffs the keyword map missed (tagging-mis

**`tag_synergies.py` also text-tags MECHANICAL-SYNERGY payoffs the keyword map missed
(tagging-misreads fix)** — the class of fit the tag model was blind to because it saw a
card's own keywords/subtypes but not what its TEXT rewards: **`toughness matters`**
("assigns/deals combat damage equal to its toughness", Doran-style — Bark of Doran +
Kingpin, so a toughness-swap payoff isn't a bare `equipment/pump` body); **`noncombat
damage`** (the literal phrase — Hawkeye/Ojer Axonil amplifiers + the "whenever a source
deals noncombat damage" draw engine — PLUS a repeatable **pinger**: a PERMANENT, not a
one-shot instant/sorcery burn spell, whose ability deals damage to a player / any target
/ each opponent, so a ping-ENGINE deck reaches critical mass on the theme while a couple
of burn SPELLS can't fake it into any aggressive deck; combat-damage triggers excluded);
**`spell copy`** (Pyromancer's Goggles); and a
**tribal-matters PAYOFF** tag — a lord/tutor gets the creature TYPE it rewards even when
it isn't that type itself ("Dinosaurs you control" / "search for a Dinosaur card" →
`Dinosaur`, so Huatli reads KEY in a Dino deck, not role-player). The tribal scan runs on
ORIGINAL-case text (MTG capitalizes real tribes but lower-cases generic "creatures/lands",
a strong natural filter) with a `_NON_TRIBE_WORDS` denylist for sentence-initial capitals.
**These sub-themes surface even as a SECONDARY payoff:** they'd otherwise sit below the
25%-of-top-theme centrality cutoff in a deck with a dominant theme (toughness-swap with
only Kingpin+Bark; noncombat-damage with 2 cards under a heavy Wizard theme), so
`_central_themes` admits the curated `_MECHANIC_SUBTHEMES` set (`toughness matters` /
`noncombat damage` / `spell copy`) at a **flat floor of 2** — the specific-effect analog
of the `#: protect:` signature rescue (a real 2-card payoff sub-synergy reads central,
while a GENERIC theme at the same low weight STAYS gated behind the 25% cutoff, so the
relaxation can't fake a generic overlap into a home; guarded by `check_suggest` anchor 12).
So Bark → 20a/20b and Hawkeye → the ping decks now auto-surface. A tribal payoff clears
the plain cutoff easily (a Dino deck runs ~19 Dinosaurs). After editing these
patterns, regenerate BOTH derived tag stores: `tag_synergies.py --merge` for the
LIBRARY, and **`build_pool.py --all` for the pool** — which re-derives every pool row's
`Synergies` through the same `tags_for()`. Do NOT point `tag_synergies.py` (or
`enrich.py`) at `card-pool.csv`: both write through `lib.write_rows`, which emits only
the canonical 8 LIBRARY columns, so it silently dropped the pool's `Rarity` /
`Legalities` / `Released` and broke every format filter, rotation flag and wildcard
price (audit F-02). Both now refuse a non-library target up front
(`lib.csv_schema_error`), and `check_all` fails if a derived file loses its own
columns. Skip the pool rebuild and UNOWNED craft candidates read stale pool tags.


## [K-11] A few genuinely text-less vanilla creatures trip validate's blank-Card-Text warning (expected, n

A few genuinely text-less vanilla creatures trip validate's blank-Card-Text
warning (expected, not an error).

**2026-08 update — the inspection surfaces now say so.** `card.py` and `deck.py text`
printed "(no oracle text on file — enrich/build the pool)" for a blank-text row, which
is WRONG advice for a vanilla: it sent a session to Scryfall to re-learn that
Quakestrider Ceratops is a 12/8 with no abilities (Tyrox, Saurid Tyrant and Terrian,
World Tyrant likewise — DFT prints several legendary vanillas). A row that RESOLVED
(a real type line from the pool/library) with blank text now prints "(no rules text —
a vanilla creature (K-11), not a data gap)"; only a card with no resolved row at all
still directs you to enrich/build. The distinction is computed from the row, not
guessed: enrichment fills Type and Card Text together, so a populated type line with
empty text is the vanilla signature.


## [K-12] The functional-role breakdown (`deck.py stats`) and castability lint (`deck.py mana` / `check`) 

The **functional-role** breakdown (`deck.py stats`) and **castability lint**
(`deck.py mana` / `check`) are heuristic. Roles are matched from oracle text, so
modal cards land in several buckets and single-draw cantrips are deliberately
*not* counted as card advantage. Because regex matching inevitably misses
phrasings and silently *under*-counts, `stats` and `tier` run a **coverage
self-audit** (`role_coverage_flags`, F15): a broad lexical net flags any card
whose text reads like interaction / card advantage the classifier *didn't* tag,
printing a "⚠ Possible UNDER-COUNT — verify" list so a miss is explicit, never
silent. It only prompts a human read; it never changes a count. **That net is now
built as a strict SUPERSET of the precise patterns** (`_INT_CUE_PATS` /
`_CA_CUE_PATS` union the compiled role regexes in), because a phrasing used to be
missable by BOTH — Repulsive Mutation's "counter up to one target spell unless…"
was too narrow for the Counter pattern *and* absent from the net, so the
under-read was invisible to the audit that exists to catch under-reads.
**A hands-on session found the under-count was much larger than "a residual":**
three cards that unambiguously interact scored ZERO roles, and one deck read
interaction 3 against a hand count of 7. All are fixed and unit-tested — removal
now matches a permanent-type LIST (`destroy target artifact or enchantment`,
`destroy target artifact, enchantment, or creature with flying` — previously
unmatched by the hand-kept alternation), a counter accepts `up to N target`,
library-TUCK removal counts (`shuffle … target creature … into their owners'
libraries` — Floodpits Drowner leaves the battlefield, so it IS an answer), and
card advantage covers `five` / `half X`. Conversely a **LOOT** (`draw N, then
discard N`) is no longer card advantage: it's card-neutral, the same reason a
single-draw cantrip is excluded. Roster impact when this landed: 26 of 56 decks
gained interaction, 2 lost card advantage (both Kiora), 6 metrics floors moved
B→A. **When editing these patterns, run a roster-wide before/after diff** — a
bare `{0,2}` inside an `rf"…"` regex silently compiles to the literal `(0, 2)`,
and only that diff caught it (46 decks had lost all "destroy target creature").
**`check_patterns.py` now catches this class mechanically** (a hard `check_all` gate):
every card-text pattern must match ≥1 pool card, and no pattern source may hold a
tuple repr. Run the diff anyway for anything that changes a COUNT — the gate proves a
pattern is alive, not that it matches the right cards.
**A SECOND sweep, driven by reading the audit's own output, was larger still** —
proof the coverage list is worth actually working through rather than glancing at.
The big one: the bounce pattern spelled `(?:owner|their) hand`, which requires the
literal text "owner hand", while MTG writes "to its **owner's** hand" — so EVERY
unconditional bounce spell in the collection scored zero roles for the entire life
of the pattern (note `owner'?s?`; this is the same class of typo as the `{0,2}`
one). Six more templatings were missing: EDICT (`target opponent sacrifices a
creature of their choice` — it answers hexproof), X-damage removal (the fixed
patterns all demand a DIGIT), the Aura form of the library tuck, mass edict (`each
player sacrifices all other creatures`) → Sweeper, a REPEATABLE upkeep draw →
Card advantage (the cantrip exclusion is about ONE-SHOT single draws; Phyrexian
Arena accrues every turn), and fixed damage to each opponent → Burn/drain. Roster
impact: 34 of 58 decks moved, all upward — interaction 415→464, card advantage
104→112, unclassified 174→157, under-read 48→10. Deck 22 re-graded C→B on it, and
ten more decks had stale figures in their `#: tier:` prose corrected.
**A THIRD under-count sat in the CARD-ADVANTAGE half, and it is the one case so far
that NO uncertainty channel could reach.** The repeatable-draw rule above was added as
a single pattern keyed on the literal word **`upkeep`** — but repeatability comes in
two templatings, and that pattern read only one. A **PHASE** trigger recurs every turn
and Magic writes it on the end step, the draw step and combat as readily as the upkeep
(Haliya, Guided by Light draws at the beginning of your END STEP); and a **`WHENEVER`**
trigger recurs by construction (Exemplar of Light draws every turn it gets a counter).
Neither matched the precise pattern NOR the broad `_CA_CUES` net — the "missable by
BOTH" failure the superset property exists to prevent — so deck 46 reported card
advantage 1 against a real 3. **The reason it was invisible is worth keeping:** both
cards DID match a role (Payoff, Lifegain), so `unclassified` — which by definition only
names cards matching NOTHING — could never reach them, and `under_read` fires per-axis
but is driven by the same cue net that missed them. A card sorted into the *wrong*
bucket is therefore harder to detect than one sorted into no bucket at all. Found by
hand-counting a deck's draws while drafting it, not by any gate.
**The fix is a DISCRIMINATION problem, not a widening one, and the roster diff is what
proved it.** A naive `whenever .* draw a card` took the pool from 777 card-advantage
cards to 1200 — and **45 of those were the exact inverse of the role**: `Whenever you
draw a card, <effect>` (Chasm Skulker, Orcish Bowmasters, Queza) puts the draw in the
CONDITION, so the card CARES about drawing and does not draw. Scoring a draw-PAYOFF as
a draw is backwards, and it is the same shape as the `theft`/`heist` tag collision.
Magic templates a trigger as `Whenever <condition>, <effect>`, so requiring the draw to
fall AFTER the comma separates them; final count 1163. **`When` vs `Whenever` is the
other load-bearing distinction** — "When this creature enters, draw a card" is a
one-shot ETB cantrip (Inspiring Overseer) and stays excluded, which is the cantrip rule
this pattern implements rather than an oversight. Roster impact: 38 of 64 decks moved,
**all upward**, median card advantage 1→2.5 (not saturated — 5 decks still read 0 and
the max is 12); three metrics floors moved (38 and 38a C→B, 42a B→A); no deck landed
≥2 bands off its claimed letter; and **15 decks had a stale card-advantage figure in
`#: tier:` prose**, every one an under-statement. Note 42a now sits one band BELOW its
floor by deliberate choice, which the guard permits and does not nag about.
The coverage net also **strips parenthetical REMINDER text** before matching, because
Ward's reminder ends "…counter it unless that player pays {2}" and was reporting every
warded creature as a missed interaction piece. A FALSE cue is the expensive kind of
error here — the list exists to be read card-by-card — and the strip cannot create a
blind spot, since the net contains the precise patterns and the flag only fires when
NO role was tagged.
The interaction / card-advantage counts are computed by ONE canonical
`role_tally` (F13) — quantity-weighted, a card counted once per axis, basics and
nonbasic lands skipped — that `stats`, `audit`, and the `quality`/`tier` vectors
all route through, so the number you eyeball in `stats` is the number the tier
floor grades on (three separate counters used to disagree by ±1). It also returns
**`protection`** (see below). The lint reads the deck's `#: colors:` header,
so a stale or intentionally-narrow header flags cards as off-color — a header
narrower than the deck's real card pool reads as multicolor strays. Fixing a stale
header to the deck's real castable colors clears the false positives (e.g. deck
`13` was corrected `GR`→`GWBR`). Treat a flag as signal to review, not a hard
failure — it doesn't gate `check_all.py`.
An identity stray now says WHICH KIND it is, in three cases: `(hybrid — paid
on-color)`, `(off-color ability)`, or `(cost unknown — run deck.py mana …)`. The third
exists because **`check` deliberately passes an EMPTY mana dict to stay offline**, and
with no cost to read nothing can be shown to be hybrid-explained — so `check` would
otherwise assert "off-color ability" for a card it cannot classify (false for deck 3's
two R/W hybrids). It still COUNTS an unknown as actionable, so the offline path
over-reports rather than silently clearing a deck; only the claim is softened to match
the evidence. Run `deck.py mana` (which loads real costs) for the definitive read.

### CONNIVE is an unread keyword, and a flat metric after a tune is not proof (2026-08)

Deck 52 took a **ten-swap** tuning pass aimed squarely at card advantage. The metric read
**3 before and 3 after.**

The axis had genuinely moved. `classify_roles` returns `['Payoff / engine', 'Recursion']`
for **Baron Helmut Zemo**, whose only repeatable ability is *"whenever you cast a black
spell from your hand, Baron Helmut Zemo **connives**"* — in a mono-black list that is a
draw-and-discard every single turn. **Funeral Room // Awakening Hall** and **Susur Secundi,
Void Altar** classify the same way for the same reason: their card draw is behind a keyword
or a stationed ability the pattern set does not read.

**The failure mode this creates is a bad decision, not a bad number.** Seeing card advantage
unmoved after a tune, the natural next move is to spend more slots on the same axis — in a
deck that had already fixed it, and whose real constraint had by then become the curve
(2.86 → 3.31 avg MV across the same ten swaps). Adding an eleventh card would have made the
deck worse while chasing a metric that was wrong.

Recorded in the deck's own `#: tier:` prose so the next reader does not repeat it. **When a
targeted tune leaves its target axis flat, check whether the adds are classified before
concluding the tune failed.** Fixing this means teaching `_ROLE_PATTERNS` the keyword —
`connive` is a draw-then-discard, so it belongs in card advantage alongside the explicit
"draw a card" texts.


## [K-13] A literal type-name search cannot see the choose-a-type category — and the false negative reads as an answer

**A literal type-name search cannot see the choose-a-creature-type category, and a false
negative there reads as a finished answer.** Asked whether a Robot-tribal deck had payoffs,
a pool sweep was run for `Robots you control get`, `for each Robot` and `number of Robots`
across every colour in Standard. It returned zero, and the archetype was declined in
writing — "bodies without a payoff" — with the zero quoted as a fact about the format.

**The search was wrong, not the archetype.** There are FOURTEEN cards in those colours whose
text is a lord effect, five of them genuine anthems: Leyline of Transformation, Chronicle of
Victory, Lifecraft Engine, Banner of Kinship, Adaptive Automaton, Patchwork Banner, Roaming
Throne. Every one of them reads `As this enters, choose a creature type` and then talks
about `the chosen type` — the category NEVER contains the type name, because naming it is
the player's job at resolution. The regex was searching for a word the cards structurally
cannot contain. Deck 48 (Doombots) exists only because a later card pile happened to
include Lifecraft Engine and forced the correction; nothing in the toolchain would have
surfaced it, because no gate can see a search that was run once, in chat, and believed.

**Why this is [K-04] one layer earlier.** K-04 says never gate a PREDICATE on a derived tag,
because the predicate inherits every hole in the tagger — `_is_color_fixer` read the
roster's two best fixers as non-fixers. This is the same failure moved upstream to the
SEARCH: gating on a literal noun inherits every way the effect can be phrased without it.
The two share a fix shape — read the effect, not the label.

**The rule: search the EFFECT SHAPE, not the noun.** For a tribal payoff that means
`choose a creature type`, `of the chosen type`, `creatures you control get +1/+1`, and the
kindred/changeling wordings (`is every creature type`) which reach the same place from the
other side. More generally, treat a zero-result sweep as an UNVERIFIED SEARCH rather than a
property of the format, and say so when reporting it — the honest form is "my search found
none, and here is what it searched for", which invites the correction that "there are none"
forecloses. A zero is the one result that cannot distinguish "absent" from "mis-queried".

**Residual, live.** Nothing gates this. `check_commands` can prove a command is reachable
and `check_patterns` can prove a pattern list is current, but neither can see a query typed
into a session. The only defence is the phrasing discipline above plus [G-52]'s rule that a
verdict surface must print its evidence — a sweep that shows its query is a sweep someone
can falsify.


### The BULK-TRIAGE variant: never sort a PILE on the `Color(s)` column

The rule above is easy to hold for one card and silently breaks on a hundred, because the
identity column is the one that is convenient to `GROUP BY`. A 111-card pile pasted for
deck 51 was hand-filtered with an ad-hoc script over `card-pool.csv` that read `Color(s)`,
and it binned NINE cards as "off-colour for mono-U". Eight of them were castable:

| card | printed cost | why identity lied |
|---|---|---|
| Bruce Banner | `{U}` | identity U/R/G comes from the TRANSFORM cost |
| Norman Osborn | `{1}{U}` | identity U/B/R comes from the TRANSFORM cost |
| Ramos, Dragon Engine | `{6}` | identity WUBRG comes from a MANA ABILITY |
| Abandon Attachments | `{1}{U/R}` | hybrid |
| Hama, the Bloodbender | `{2}{U/B}{U/B}{U/B}` | hybrid |
| Flotsam // Jetsam | `{1}{G/U}` // `{4}{U/B}{U/B}` | hybrid, both halves |
| Messenger Hawk | `{2}{U/B}` | hybrid |
| Vulture, Scheming Scavenger | `{5}{U/B}` | hybrid |

Exactly one, Iroh Grand Lotus `{3}{G}{U}{R}`, was genuinely gold. So the filter's error
rate on its own flagged set was 8 of 9. Two further notes worth carrying: **Standard does
not restrict by colour identity at all** (only Brawl does), so `#: colors:` was never a
legality question in the first place — it is a castability heuristic; and a **transform
cost and a mana ability both leak into identity**, which is a second route to the same
mistake that the hybrid framing alone does not cover.

**The fix is a tool, not more care.** `deck.py screen <id> <pile>` already existed and was
never run — it prints the printed mana cost per candidate and now reads castability from
it via `_candidate_castability`, which mirrors `_castability_lint` so the two cannot drift.
`/add-cards` Stage 0b now requires it for any pile over ~10 cards. Same shape as G-53: a
capability that works and is never reached is invisible to every gate.

Two tooling defects surfaced in the same pass and were fixed with it. **Name resolution
dropped 22 of the 111 names** — `resolve`/`screen` matched only exact / DFC-front /
substring, so every `Name, Epithet` legendary typed without its comma fell out, along with
anything carrying a `(note)`. That is not a uniform 20% loss: legendary creatures are
where a pile concentrates its interesting cards, so the tool returned the fifth of the
pile that most needed grading straight back to hand-triage, which is where every error
happened. `_resolve_card_name` now also matches on a punctuation-squashed key, and still
refuses to correct typos. **And `screen`'s `KEY` label fired on 66% of the pile**, tracked
to `_strong_signature_themes`: its flat `>=2` bar was tuned against a 3-to-5-card protect
list and does not survive a longer one, so 26 of 33 decks carried a signature that was
>=50% GENERIC. A generic theme now needs half the protect list; measured across 4,440
(deck, card) judgements that moved KEY from 13% to 8% with all 223 changes running
KEY -> weaker.

**2026-08: the identity-vs-cost bug was RE-INTRODUCED in the needs model** — the exact
fix `suggest_scored` received never reached its siblings. `suggest_mana` and
`suggest_interaction` still filtered candidates with `card_colors(...).issubset(deck)`,
and these are the two recommenders G-38 designates as THE fix path when a deck's
scorecard says the deficit is interaction or mana. Measured before the fix: 34
Standard interaction cards hidden from at least one mono-color deck that could cast
them — including Bullseye, Death Dealer `{2}{B/R}`, the very card this gotcha names —
and 25 mana sources, including every `{N}` rock whose 5-color identity comes from a
mana ability (Haunted Screen was invisible to EVERY deck). Both now route through
`_candidate_castability` (broad-scan BS-01). The lesson is G-45's, at class scope: a
fix applied to one sibling is a bug report about the others.

## [G-59] A tribe's viability is its PAYOFF count, not its body count — and changelings cannot fix the missing half

**A tribe's viability is its payoff count, not its body count, and changelings cannot fix
the missing half.** Asked to find a second tribal ramp deck after deck 49 (Dragons), the
obvious move was to rank creature types by how many creatures exist. That number is easy
to measure and it decides nothing. Splitting each tribe into BODIES and PAYOFFS — cards
whose text actually cares that the type is present — produced this, across Standard:

| tribe | bodies | payoffs |
|---|---|---|
| Dragon | 71 | **20** |
| Dinosaur | 52 | 11 |
| Vampire | 69 | 3 |
| Mutant | 79 | **2** |
| Demon | 28 | 1 |
| Plant | 27 | 1 |
| God | 21 | **0** |
| Leviathan | 5 | 0 |

**Mutant has the most bodies of any tribe considered and is unbuildable**: 79 creatures and
two cards that care, spread across all five colours at a maximum of 13 in any one. Dragons
work because twenty cards read the type — Dragonlord's Servant, Lathliss, Stormscale Scion,
the whole Exhale cycle. God and Leviathan have literally zero.

**Changelings are the trap inside the trap.** A changeling is every creature type, so it
RECEIVES tribal effects and never provides one. Adding ten changelings to a Demon deck
gives you eleven Demons and still exactly one card that cares — the shortage is on the side
changelings do not touch. This is the same inversion as stacking anthem *recipients* with
nothing providing the anthem (see G-58's neighbourhood and the deck 48 Adaptive Automaton
decision): a body is not a payoff, and no quantity of bodies becomes one.

**The rule: count payoffs FIRST, then ask whether the bodies exist.** Search the effect
shape rather than the noun, per K-13 — `"<Type>s you control"`, `"for each <Type>"`,
`"number of <Type>s"`, `"<Type> spells you cast"` — because a payoff phrased generically
("choose a creature type") will not contain the type name at all.

**The corollary that mattered in practice:** when a tribe fails this test, the answer is
usually to drop the tribal constraint rather than to prop it up. Deck 50 was built as a
mono-green *creature-count* deck with no tribe at all, because Craterhoof reads COUNT and
not type — which also sidestepped the deck 31 Elf and deck 28 Dinosaur collisions the
tribal versions kept running into. A separate check confirmed there is no "land-puller
tribe" in green either (Scout leads at 5 pullers of 24 bodies, then Robot 4, Insect 3,
Druid 2 — scattered, not concentrated), and Mouse is a Boros tribe (19 in Standard: W 9 /
R 6 / W-R 3 and exactly one green).

**2026-08 (BS-11): `deck.py tribes`' payoff scan was PLURAL-BLIND.** The type-matters
scan matched `\bNinja\b`, and `\b` finds no word boundary between "Ninja" and a plural
"s" — so "Ninjas you control get +1/+1", the way lords overwhelmingly template, matched
nothing. The payoff list under-reported exactly the count this rule says decides tribal
viability, on the tool built to show it: deck 49's list was missing Lathliss, Dragon
Queen and Dragonlord's Servant; deck 48's was missing Ultron, Ravenous Robots and
Mouser Foundry. Fixed with `_tribe_ref_re` (singular + English plural: -y→-ies,
-f→-ves, sibilants→-es, else +s, Mouse/Ox irregulars). Same family as K-13: a
literal-name search whose misses read as facts. The tribal TABLE above was
hand-measured at the pool level and is not invalidated by this, but a payoff count
near a viability threshold deserves a re-measure through the fixed scan.


## [G-60] An `{X}` spell is priced at MV 1, so a curve reading under-reads a deck that runs several

**An `{X}` spell is priced at MV 1, so a curve reading under-reads any deck running
several — and the distortion runs BOTH ways.** `lib.mana_value` counts `X` as 0 because
that is what the rules say for a spell not on the stack, and that is the RIGHT answer for
the two things it primarily serves: castability (`{X}{G}` really is castable off one
Forest) and `consistency`'s cast-on-curve probability. It is the wrong answer for the
curve, `avg_mv` and the early-drop count, all of which read the same number — a card you
realistically cast for four books as a one-drop *and* as an early drop.

**Deck 50a was misread twice in one cycle, in opposite directions.** Adding Wildwood
Scourge and Jadelight Spelunker read as avg MV 3.85 → 3.70 with early drops 10 → 12, and
the swap was described as improving the curve. Removing Jadelight Spelunker later read as
avg MV 3.55 → 3.76 with early drops 13 → 12, and was nearly rejected on that basis. The
real curve barely moved either time; both figures were the `{X}`-at-MV-1 accounting.

**The fix is a flag, not a formula change.** `deck.py stats` lists the offenders under
`✕ X-COST cards — the curve books these at MV 1, X counts as 0`, with a line reminding
the reader what that does to avg MV and the early-drop count. `deck.py tier` prints a
one-line `⚠ avg MV under-reads: N X-cost card(s)` advisory next to the vector, because
`tier` is the surface where avg MV actually gets quoted into a grade.

**Both are REPORT-ONLY and must stay so.** `x_cost_cards` is deliberately not wired into
`deck_quality_vector` or `tier_band` — a new term there would silently re-grade every
deck on the roster, which is the same reason the protection axis is reported and never
scored. `tests/test_deck_models.py::TestXCostCards` pins this with a source-level
assertion that neither function mentions the helper, alongside behavioural tests that a
fixed-cost card is not flagged and that lands and duplicate copies are excluded.

**Residual:** the flag tells you the number is soft, not what the true curve is — pricing
an `{X}` spell properly would need a model of what X you actually pay, which depends on
the board. Read the flagged cards and judge; do not try to correct `avg_mv` by hand,
because `check_tier.py` anchors the floor formula against the raw value.


## [G-61] Before dismissing a card, count the deck property its value depends on

**Before dismissing a card, count the deck property its value depends on.** Four
dismissals were overturned inside a single cycle, every one the same shape: a card judged
on its own text when the decision actually belonged to a number in the LIST. In each case
the user supplied the number and the verdict flipped immediately.

| card | the dismissal | the count that decided it |
|---|---|---|
| Michelangelo, Improviser | "circular — only triggers on combat damage to a player" | deck 50 has **six** ways to force damage through (Craterhoof ×2, Garruk's Uprising ×2, Aggressive Mammoth, Rogue's Passage) |
| Topiary Lecturer / Mona Lisa / Doc Samson / Rainveil Rejuvenator | "circular — the only pump is Craterhoof, which wins anyway" | the deck runs **Colossification**, +20/+20 and not a win condition; Topiary Lecturer also self-scales via Increment |
| Groundchuck & Dirtbag | "a six-drop worth less than a two-drop that scales" | deck 50a runs **27 lands and exactly 1 creature mana source**, so "tap a land for mana, add {G}" doubles nearly the whole base |
| Agatha's Soul Cauldron | "too narrow — needs exiled creatures with activated abilities" | deck 50a **self-mills four ways**, so it fills its own graveyard as a side effect of its engine |

**The control case is The Earth Crystal.** It was measured and rejected twice, then went
into both decks on the third pass — and the card never changed. What changed was Doc
Samson arriving in 50 (a second counter-doubler, so the two stack) and Agatha's Soul
Cauldron arriving in 50a (whose gate is creatures with +1/+1 counters). A rejection is
therefore a statement about a deck at a moment, not about a card.

**The failure mode is specifically GENERALISING FROM ONE INSTANCE.** "Craterhoof is the
only pump" was true of the best-known pump and false of the list. "It needs combat damage"
was true of the trigger and false of a deck holding six enablers. Each dismissal was a
correct sentence about the card attached to an unchecked assumption about the deck.

**The rule: state the count, then decide.** Lands vs creature mana sources, trample
grants, mill effects, counter sources, bodies of a type — these are all cheap to measure
and each one has now flipped at least one verdict. And when a card is parked rather than
rejected, say WHICH number would have to move for it to come back; that is what makes a
flex line worth reading later instead of re-litigating from scratch (see G-04 on flex
lines rotting silently, and the flex entries in decks 48 and 50 for the shape).

**Residual:** nothing gates this — no check can see a judgement made in prose. `deck.py
stats`, `shape`, `engines` and `redundancy` all print the relevant counts, so the
discipline is to run one of them before writing the word "circular" or "too narrow".

## [G-62] Blind mill is a CLOCK, not interaction — it is provably access-neutral

The question that produced this: *"if the deck is low on interaction, is mill-as-interaction
by disrupting the opponent's deck a valid tactic?"* It is the most common intuition about
mill and it is wrong for a reason that can be stated exactly, so it is worth writing down
rather than re-deriving.

**The proof.** A library is a uniformly random permutation of L cards, k of which are the
opponent's relevant threats or answers. Over the rest of the game they will draw D cards.
With no mill they draw positions 1..D. If you mill M cards first they draw positions
M+1..M+D. Any fixed set of D positions in a uniformly random permutation has the same joint
distribution of contents, so

    P(at least one of the k in their next D draws)  =  1 - C(L-k, D) / C(L, D)

in BOTH cases. Identical. Milling changes neither the density of threats in the library
(composition-neutral) nor the probability that any particular card reaches their hand
(access-neutral). It holds for every k, every D, and every M, right up until L < M + D —
at which point they deck out and lose. That boundary is the entire value of mill.

**So mill's payoff is binary.** Until the library is genuinely empty, a milled opponent is
in exactly the same position as an unmilled one. Interaction changes the board this turn;
mill changes nothing this turn and everything on the turn the library runs out. That is a
clock — the same category as a creature, priced in turns-to-kill — and it should be compared
against the deck's other clocks, never against its removal count.

**Where the intuition comes from, and why it fails hardest when invoked.** The appeal of
"mill as interaction" is strongest when you are behind on board, which is precisely when it
does least: a resolved threat is killing you and milling six does not touch it. Mill is
best when you are stable and have time — the same condition under which you did not need
interaction. The tactic is therefore anti-correlated with the deficit it is proposed to fix.

**The three real exceptions, all of which require the mill to stop being blind:**

1. **Selective mill IS interaction** — "look at the top X, put one in the graveyard" filters
   a choice and does change what they draw. Blind mill does not.
2. **Mill paired with graveyard EXILE** is disruption, because the exile half answers
   recursion. In blue/colorless Standard that is Ghost Vacuum, Soul-Guide Lantern,
   Wreck Remover, Mechanical Mobster, Magic Pot, Gravestone Strider (measured 2026-07).
3. **A library already short** — late enough that M + D exceeds L, the boundary above.

**And the inverse, which is the G-42 shape:** blind mill actively HELPS a graveyard deck.
You are filling the zone their recursion reads. A mill package should be assumed to be a
liability against recursion until the sideboard says otherwise.

**Deck 51 is the worked case.** Its mill package (Riverchurn Monument + Scrabbling
Skullcrab, amplified by The Water Crystal's +4) was added as a SECOND WIN CONDITION and the
deck's `#: tier:` block says so. It was never interaction, and the deck did not need it to
be: `suggest 51 --needs` reads "Interaction: 9/5 ok". Had interaction genuinely been the
deficit, the fix comes from the needs model per G-38 — which surfaced Summon: Bahamut
(score 9.5) and Dawnsire, Sunstar Dreadnought (6.5), both already OWNED — and not from a
mill card.

**Residual:** nothing gates this either. `role_tally` correctly does not count a mill card
as interaction, so the tooling has never made this mistake; only prose can.


## [G-63] The front face and the stored metadata disagree — on every column, not just cost

**G-02 is not a cost rule. It is one member of a class**, and the class produced four
separate bugs in a single cycle — one per column of a `Front // Back` card. Each was
found by deck work, none by a gate, and each had been live for a long time because the
wrong answer is plausible.

**COST.** Scryfall gives a split / Room / Adventure card both halves in the top-level
`mana_cost` (`{U} // {4}{U}`), but leaves a MODAL double-faced card's top-level cost
empty and puts a real cost on each face. `build_mana._front_mana` took face 0, so the
back face vanished: Bruce Banner was stored as a plain `{U}` one-drop with nothing
recording that `{2}{R}{R}{G}{G}` The Incredible Hulk is castable from that same card in
hand. **That produced a wrong answer in chat** — I told the owner both faces were
permanently unreachable, and the correction came from them, verified against Scryfall's
`layout: modal_dfc`. 49 rows were affected. Fixed in `_castable_cost`, which decides on
the SHAPE of the faces rather than a layout string: a card with a real cost on more than
one face is one you may cast either way, whatever the layout is called. A TRANSFORM DFC
is the control case and correctly keeps one cost — Scryfall writes its back face's
`mana_cost` as `""`, because that face is reached by transforming, never by paying.

**COLOR.** `Color(s)` is colour IDENTITY, so a hybrid `{U/R}` and a colorless `{6}` both
read as off-colour for a mono-blue deck. `suggest_scored` filtered candidates on that
column while the surrounding code derived the DECK's colours from printed costs — the two
halves of one function disagreeing about the same question. Measured on the red pool: 55
Standard cards a red filter hid that mono-red can cast. See G-58 for the bulk-triage
variant, where hand-sorting a 111-card pile on that column mis-binned nine cards of which
eight were castable.

**TYPE.** `_primary_type` substring-scanned the whole type line, so it returned the BACK
face's type whenever that type sorted earlier in its list — which for `Land` is always.
`Legendary Creature — God // Land` (Ojer Axonil) read as a Land, and every one of
deck.py's ~35 `"Land" in _primary_type(...)` guards then skipped the card: out of the
curve, uncounted as a creature, and ADDED to the land total. `consistency 49` reported
"Lands: 26/60" for a deck holding 25, and deck 51's tier rationale called its manabase
"flawless" on a keepable figure computed against a phantom land. 81 pool cards share the
shape.

**NAME.** `_printing_of` matched names exactly, so a DFC add resolved to nothing and
`swap --apply` wrote `1 Runescale Stormbrood` with no `(SET) NUM`. It parses, it passes
INV-04, it passes `deck.py legal` — and it fails an Arena import, which is the one place
the failure shows and the one place no gate here runs.

**NAME, a second time — and this is the one that should have been impossible.** The fix
above gave the NAME column an accessor, and a later scan found the same column broken
somewhere else: `_multiset`, the key behind `verify`, `sync`, `diff` and the dashboard's
stale-check — the commands whose entire job is matching a pasted list against a stored one
BY NAME. It keyed on the raw lowercased name, so a deck file storing
`Ojer Axonil, Deepest Might // Temple of Power` against an Arena export naming just the
front reported a real change: `+1 Ojer Axonil, Deepest Might` / `-1 Ojer Axonil, Deepest
Might // Temple of Power`. `verify` exited non-zero on an identical deck, and
`sync --apply` would have "repaired" the file by replacing the full name with the bare
front — writing back the exact un-importable line the previous fix existed to prevent,
past a green INV-04 check, because the copy count never changed. 14 deck files carry such
a line. Fixed with `_ms_key` (front-face) plus `_ms_display`, which keeps first-seen
spelling EXCEPT that the full `Front // Back` form always beats a bare front, since that
is the spelling a deck file must carry.

**RARITY — a column, and a SHAPE, that the accessor rule never covered.** `load_rarities`
reads `card-pool.csv`, which keys only the full `Front // Back` name, and it had no front
alias. 47 distinct card names across the live roster resolved to `""` — and an empty
string is not an error anywhere: `cut_keep_score` hands it to `_power_seed`, which falls
to its default (uncommon) floor. So every mythic and rare double-faced card in every deck
was seeded as low-rarity and sorted UP the cut list. Ojer Axonil's `_cuts_power_adj` came
out **−0.70 against a real +0.17** — the nudge changed SIGN, so the model was actively
arguing to cut a bomb. Avatar Aang, Bruce Banner and Clive each read 2.5 power low. The
irony is documented in the code: `cut_keep_score` already carries a note about rarity
falling through to the default floor, from the earlier fix for the rarity WORD-vs-LETTER
shape. That fix landed; this one was a different way into the same floor.

**The third lesson, which is the general one.** The first two lessons below are about
ACCESSORS, and they are correct as far as they go — but an accessor rule cannot reach an
INDEX. Auditing every reference-table loader found five that alias a DFC's front face
(`load_card_data`, `load_mana`, `load_legalities`, `load_card_meta`,
`_pool_rotation_index`) and two that did not (`load_rarities`, `load_keywords`). Nothing
gated the difference, and nothing could: each loader is individually correct against its
own file. The distinguishing feature is not the column, it is **which file the index is
built over** — a loader over the pool inherits the pool's full-name keying, while a loader
that also reads the library picks up front names for free and looks fine. So: when you
build a name-keyed index over a pool-shaped file, alias the front face — and do it in a
SECOND pass, after every real row is indexed, or a `Front // Back` row seen early will
shadow a genuinely distinct card named `Front` (`Life` is a card as well as the front of
`Life // Death`, the same trap `build_mana._front_face_retry` guards). `load_keywords` has
the same gap and was measured rather than assumed: 1 affected card, 0 behavioural
difference today, because `card-mana.csv` is built from library names too. It is left as a
known-latent case rather than fixed blind.

**The two lessons.** First, each column now has exactly ONE front-face-aware accessor:
`lib.front_face_cost` for cost, the printed cost (not `card_colors` alone) for
castability, `lib.primary_type` for type, `lib.owned_qty` / `_printing_of` for name.
Second, and this is the part that keeps repeating here: **a second copy of an accessor
carries the bug for as long as it exists.** `build_gallery.py` had its own
`_primary_type`, so P7's fix reached the deck tooling and left the gallery still
mis-typing its own breakdown — Creature over-counted by 8, Enchantment under by 9 (the
transforming Sagas), Land by 2. The definition now lives in `lib.py` and the test asserts
both callers resolve to the SAME OBJECT, not merely that they agree today; a same-answer
test would have passed against two copies.

**Standing rule.** When a name contains `" // "`, ask which face the column describes
before you trust it. A metadata column is a claim about a card, and a two-faced card is
two cards wearing one row.

**2026-08 broad scan: five more members, two of them a NEW SHAPE.** Two were the known
index shape — `load_keywords` (a front-named deck line's keywords read as a clean "no
keywords"; deck 42's Cecil, Dark Knight lost its ⌘ line) and `reconcile_crafts`' pool
map, whose "fallback" was provably dead code. Two were exact-name **JOINS**, which the
accessor rule had never been read as covering: `legality_report`'s copy counter keyed
raw line names, so 4 `Bruce Banner` + 1 `Bruce Banner // The Incredible Hulk` passed the
4-copy limit as two different cards — and `swap --apply`'s bump match was the tool that
could *create* that split state, since `_do_swap` canonicalizes an add to the pool's
full name while the deck stores the front. The fifth was the deck editor's client-side
buildability: `app.py` serialized the raw ownership index to JS, whose `name in OWNED`
lookup has no front fallback — a deck read "1 missing" in the editor while `/decks` and
`deck.py check` called it buildable, and `check_dfc`'s Python-only scan structurally
cannot see a consumer in JavaScript. All five fixed 2026-08 (the JS one by front-aliasing
the served payload). The join lesson is now in the standing rule: key every name-facing
JOIN on `_ms_key`, not only every loader.

**The JS member came back once, through the gate's own stated residual (BS4-14,
2026-08-09).** The BS-08 fix added `ownedOf(name)` — full name, then front face — and
`check_dfc._payload_flags` pinned two markers: that the helper exists, and that it
front-splits. Its docstring then said, honestly:

> Residual, stated honestly: a NEW raw lookup added elsewhere in the template would not
> fire this — the pin guards the helper, not every use.

`renderFlex` was already that raw lookup, in the same file, thirty lines below `cardStatus`.
A `#~` flex line naming a DFC by its full `Front // Back` name — which is how the wishlist
stores DFCs (G-19) and how `deck.py resolve` emits them — displayed "not owned" for a card
the deck rows above displayed correctly. One template, two consumers of one index, two
different answers.

The pin guarded the DEFINITION and not the CALLERS, which is the same shape G-40 records
for `cuts` (a pure-function anchor cannot see whether a caller asks) and the same shape
`check_commands` exists for one level up. `_payload_flags` now scans every USE of the
`OWNED` index and fails any lookup outside `ownedOf` — comment lines excluded, since the
comment explaining the fix necessarily quotes the banned shape. Mutation-tested: reverting
`renderFlex` to a raw lookup makes the gate fire.

**When a guard's docstring states a residual, that sentence is a bug report about the
guard.** This one was accurate, specific, and sat unactioned while an instance of exactly
what it described lived in the file it guarded.

**The IN-PASS aliasing members closed 2026-08-09 (BS4-18/20).** `lib.alias_front`'s
docstring has always said that aliasing inside the row loop with `setdefault` is
order-dependent and wrong, and four builders were still doing it:

| site | indexes | why the gate could not see it |
|---|---|---|
| `enrich.index_card` | Scryfall responses | scan covers POOL readers only |
| `build_mana._store` | Scryfall responses | same |
| `deck.fetch_missing_rarities` | Scryfall responses | same |
| `wishlist.owned_index` | library rows | a `+=` counter, not an index build |

The first three now index the REAL (full) name in-pass and call `lib.alias_front` once
after the fetch loop; `owned_index` sums under the stored name and adds a front alias only
where no real row claims it. The failure they share is not that a DFC's front is missing —
it is that a DFC seen EARLY claims the bare front key, so a genuinely distinct card of
that name arriving later can never claim its own. "Life" is a card as well as the front of
"Life // Death".

Measured before and after: **zero front-name collisions exist in the current Arena pool**
(706 two-faced names checked), so every one of these was latent — one printing away from
writing another card's cost, text or rarity over a real card's, silently and
order-dependently. That is the honest reason they were worth fixing anyway: the cost of
the bug is unbounded and the cost of the fix was four second-pass calls.

**2026-08-07 broad scan #2: the class reaches the ingest WRITE side (BS2-02/BS2-25,
fixed same day).** Every prior member was a READER — a loader, an index, a join, a
serialized payload. The second scan found the same shape in the writers that create
library rows. `reconcile_crafts` normalized an incoming card to its FRONT name and then
looked for the existing library row with an **exact**-name join — but the library stores
eight printings under their full `A // B` name (the DSK Rooms), so the join missed and
the tool APPENDED a second row for the *same physical printing* under the front name.
`import_arena`'s `(name, set, collector)` index had the identical miss. INV-01 is blind
(two different Card Names are not a duplicate printing), and `lib.owned_qty` resolves the
pool's full-name key to the full-name row only — so the owned count silently split
across two spellings, a real 3 reading as 1. Worse, the halves composed into a loop:
`verify_ingest` resolved full→front but never front→full, so a front-named paste of an
owned Room reported "✗ NOT in card-library.csv — re-run the ingest", and the prescribed
re-ingest *created* the duplicate. Fixes: both writers join on front faces (a collector
number is unique within a set, so `(front, set, collector)` cannot collide two distinct
cards); `reconcile_crafts`' mana-row check keys on the library row's actual spelling so
INV-02 tracks the real row; `verify_ingest._library_key` gained the front→full third
step, resolving to the STORED spelling so the quantity and mana checks read one row.
The lesson extends the standing rule again: the front-face question is not a read-side
question — **a writer that keys rows by name is a join too.**

**Batch G closed the last read-side stragglers** — `screen` / `redundancy`'s
already-in-deck filters and `similar`'s shared-card intersection, the last of which feeds
the "▸ Most shared CARDS" figure G-47 tells the reader to trust when it disagrees with the
cosine, so a card the two decks spelled differently simply never counted. `similar`
intersects KEYS through a key→display map, keeping the count right without printing
lowercased keys at the reader.

**The last member — the HEADER CONSUMERS — closed 2026-08-09 (BS4-01), and how it was
deferred is the more useful half of the story.** The `#: protect:` / `#: uncastable-ok:`
consumers (`rank_cut_candidates`, `_castability`, `_weakest_cut`, both signature-theme
functions, `recommendation_row`) compared raw lowercase names, while
`header_card_staleness` — the gate built to catch a dead header entry — joins on
`_ms_key`. So a header naming a DFC by its other face was a disabled instruction that the
gate certified as healthy: **a gate vouching for the thing it exists to detect, which is
strictly worse than no gate**, because the green check is itself the evidence of health.

It was left open on a measurement: zero live instances, all 14 DFC-bearing headers using
the full spelling. That measurement was taken 2026-08-07. **Deck 66 was drafted 2026-08-08
with `#: protect: Eddie Brock` against a line storing `Eddie Brock // Venom, Lethal
Protector`, and the count was wrong the next day** — the deck's own title card sat in its
cut ranking, and the staleness sweep reported the roster clean throughout. A
zero-instances count is a fact about a moment; the code property is whether the join can
ever be wrong, and that had not changed. **Defer on the mechanism, never on the census.**

The fix normalizes at the READER rather than per call site: `deck._header_card_keys` is
the one home both headers share, returning `_ms_key` keys, and every consumer keys its
side. Verification worth keeping: the whole 97-deck roster was A/B'd against a pre-fix
copy of `scripts/`, and **exactly one deck changed (66), with zero tier floors moved and
zero uncastable counts changed** — the `uncastable-ok` half is the one that can raise a
floor by exempting a card, and it had no live instance, so nothing silently re-graded.
Four tests pin it, three of which were confirmed to fail against the pre-fix code.

**Batch A/B of the same scan closed five more members in one pass**, all the raw-name
join shape: the swap CUT side (`_cards_after_swap` / `_swap_edit_lines` /
`_do_swap`'s protect guard — a front-name cut of a full-name-stored card refused with
"not in deck" while the ADD side had been `_ms_key`-matched since BS-05), the flex
auto-retire's add/cut/maindeck comparisons, both role fillers' already-in-deck filter
(a deck was offered its OWN maindecked DFC as a 0-wildcard filler — 25 rows roster-wide),
`card.py`'s in-decks join ("in decks: (none)" for five owned, played cards), and
`wishlist._is_land`'s whole-type-line scan (a back-face `// Land` god ranked — and was
bought in a live `--budget` — as a phantom manabase upgrade). The remaining structural
closure: `deck.load_card_meta` and `wishlist.load_pool_index` were the last two loaders
aliasing IN-pass; both now use the second-pass `lib.alias_front` and are REGISTERED in
`check_dfc._ALIASED_LOADERS`, so the behavioral anchor exercises every member.

## [G-64] A reanimator's uncastable bombs are not a build error — `#: uncastable-ok:`

**The measurement that made this a rule.** Deck 52a is a mono-black true reanimator: it
discards or mills a bomb it cannot cast and cheats it onto the battlefield. Adding ONE
five-colour card to it — Cosmic Spider-Man, a 5/5 with flying, first strike, trample,
lifelink and haste, which is exactly what you want to reanimate — produced this:

| | before | after |
|---|---|---|
| `castability` | PASS | **FAIL — 1 uncastable** |
| `preflight` | READY | **BLOCKED** |
| metrics floor | **A** | **C** |

Three tier bands and a blocked pre-commit gate, for a card doing its job. The tooling had
no term for "intentionally uncastable", so it read the archetype as a misbuild.

**Why opt-in and per-card.** Most uncastable cards genuinely are mistakes — a stray from a
mis-typed name, an off-colour card left behind after a colour change, a hybrid misread.
Weakening the default would lose all of that. `#: uncastable-ok: A; B` is the author making
a specific claim about specific cards, structurally the same as `#: protect:` naming
signature cards the tooling must never propose cutting. Semicolon-separated for the same
reason: card names contain commas.

**Nothing disappears.** `_castability` returns the exempt cards as a fourth list,
`intended`. `deck.py mana` prints them under `◆ Intentionally uncastable`, and `preflight`
appends `(+N intended, exempt)` to a PASS. G-52 — a verdict surface must print its evidence
— applies here as much as anywhere: the reader still needs to see that the deck contains
cards it cannot cast, they just should not read as failures.

**A second bug fell out of building this.** `META_RE` allowed only `[A-Za-z_]` in a `#:`
key, so `#: uncastable-ok:` did not parse at all — and neither did `#: based-on:`, which
**24 lines across the roster already used**. Those lines matched no meta key, fell through
to the card-line branch, matched no card, and vanished with no warning. Nothing read
`based-on`, so nothing ever noticed. The key pattern now allows a hyphen.

**The related fix, filed separately as F-16 and latent for a cycle.** `tier_band` returned
`"C"` outright on any stray rather than capping at it, so a deck whose measurable floor was
D got *raised* by holding a dead card. "Caps" is what the docstring and the tiering rubric
both always said; only the code disagreed. Roster sweep after the fix: **0 decks change
floor**, exactly as F-16 predicted when it was filed as latent.

## [G-65] A deck line's `(SET) COLLECTOR#` was validated by nothing

**The hole.** INV-04 asserted that a deck line PARSES. It said nothing about whether the
printing on that line exists. Every ownership and legality join keys on the card NAME, so
the set and collector fields were decorative to the tooling — while being load-bearing in
the Arena import block the same tools EMIT.

Demonstrated with a set code that does not exist:

```
1 Eaten Alive (ZZZ) 172
  deck.py legal      ->  ✓ No construction issues for standard
  deck.py check      ->  1 / 1   Eaten Alive (ZZZ)          <- reports it OWNED
  deck.py preflight  ->  Verdict: READY
  check_all.py       ->  All invariants hold. ✓
```

A deck file could be integrity-clean and un-importable at the same time. **Not
hypothetical**: deck 52 was written with `1 Eaten Alive (FDN) 610` when the real collector
number is 172, and nothing complained. It was caught only because `deck.py resolve` was run
separately and the numbers happened to be compared by eye.

**Why the rule is split hard/soft, and why basics are exempt — measured before deciding.**
A first pass over all 78 deck files found 153 mismatches. The breakdown decided the design:

- **98 basic lands.** Arena prints several arts per set — `Swamp (MSH) 291` and
  `(MSH) 292` are both real — while the pool carries one representative. A hard rule
  without an exemption would have failed **61 of 78 deck files on basics alone.**
- **28 lines with no printing stated.** Legal, if under-specified. Skipped.
- **27 non-basic mismatches** across 15 decks, and these are the real signal:
  `Explosive Derailment (DFT) 130` when the card is `(OTJ) 122`; `Mechan Navigator
  (DFT) 48` vs `(EOE) 64` in two decks; `Burst Lightning (SOA) 41` and `(DMU) 132` vs
  `(FDN) 192` in three; `Vampire Nighthawk (FDN) 186` vs `(FDN) 757` in four.

Some of those 27 may be legitimate alternate printings the pool does not carry — the pool
keys ONE printing per card by construction — which is why the collector-number check is a
WARNING. The set-code check is HARD because a code appearing in no card anywhere cannot be
right, and because it was measured at **zero roster hits** first: a check that fails
nothing today can safely be made hard.

## [G-66] Nothing counted whether a deck holds targets for its own gated effects

**The question no command answered.** A card whose text names a resource — "return target
creature card with mana value 4 or less", "sacrifice an artifact or creature", "eight or
more permanent cards in your graveyard" — is worth exactly as much as the number of cards
in THIS deck that satisfy it. Every scoring model in `deck.py` grades a card in ISOLATION,
so that number was invisible to all of them. `engines` looked closest but answers a
different question: it grades enabler↔payoff by synergy TAG, not by arithmetic on the gate.

**What it cost.** The single most important finding of the deck 52 build — the concept pile
held **24 ways to return a creature against 8 creatures worth returning** — came from a
script written by hand for that one occasion. Nothing in the toolkit could produce it, and
the whole deck plan changed once it existed. G-61 records four separate dismissals that
were overturned by exactly this kind of count, and states the fix as a HUMAN discipline
("state the count, then decide") precisely because nothing automated it.

**What it reports.** Per gated card: the resource its text names, and how many cards in the
list supply it. `✗ NOTHING` is a dead card. `⚠ short of N` means a stated threshold is
unmet. `⚠ thin` fires at ≤3. Counts exclude the card itself — a sacrifice outlet is not its
own fodder — and exclude lands unless the gate is about lands.

**The recursion row reports the count that actually decides something.** "How many creature
cards can I return" is nearly all of them and carries no information; what mattered on deck
52 was how many are MV 5+, i.e. big enough that cheating them in gains real mana. So the row
reads `creature cards to return (9 at MV5+)`.

**One rule was written and deleted, which is the point worth keeping.** A generic "cards to
discard" gate reported **35 for every discard outlet** in a 60-card deck — "you have a
hand", true of every deck, decisive for none. That is the same saturation failure already
recorded for `suggest`'s Decks column (99%, G-28) and `cuts`' protect keep-boost (87%,
G-09). **A gate earns a row only when the resource can be SHORT.** A test now forbids the
rule returning.

**2026-08 residual, found by deck 58 (Treasure Planet): the counter sees CARDS, and a token
economy's resource is TOKENS.** The Jund Treasure deck's whole engine mints artifact tokens
(Treasures, Meteorites, Landers, Maps — 14 producer cards), and `targets` reported its two
artifact-sac payoffs as `⚠ thin — 1 artifact to sacrifice`, counting the one nontoken
artifact in the list. No list scan can see tokens, so the flag is structural, not fixable
by a better pattern. The mitigation is editorial: a deck whose gated resource is tokens
must say so in `#: notes:` (58 does), because a reader who trusts the flag would cut the
deck's best payoffs.

## [K-14] A draw clause behind an activation cost was invisible to the role tally (fixed 2026-08-07)

`classify_roles` decides "Card advantage" from `_ROLE_PATTERNS`, and **every pattern in
that bucket is TRIGGER-shaped**:

```
\bwhenever\b[^.,]{0,80}?, [^.]{0,60}?draws? a card
at the beginning of (?:your|each|the) (?:upkeep|end step|…)[^.]{0,60}?draws? a card
draws? (?:two|three|…) cards?          draws? cards? equal to        \binvestigate\b
exile the top card of your library[^.]{0,40}\. you may play (?:it|that card)
```

There is no pattern for a card-draw clause reached by PAYING something. So all of these
score zero card advantage:

```
+1: Draw a card.                          {T}: Draw a card.
{2}{U}, {T}: Draw a card.                 {1}, Sacrifice this artifact: Draw a card.
```

while `Whenever this creature attacks, draw a card.` scores `{Card advantage, Payoff}`.
The difference is purely the grammar of the sentence, not the effect.

### The measurement (2026-08-07)

Sweeping the pool for a `<cost>: … draw a card` shape, then excluding lands (whose
activated draw is arguably not the same thing) and loot effects (deliberately excluded by
`_LOOT_RE`), and keeping only cards that score NO card advantage:

- **187 pool cards**, of which **24 are planeswalkers**
- **at least 12 on the roster**: Aether Syphon, Charging Strifeknight, Ice Cream Kitty,
  Kingpin's Enforcers, Lunar Convocation, Professor Dellian Fel, Professor Zei, Ravenous
  Amulet, Spectral Sailor, Technodrome, Vampiric Rites, Wrench

"At least" is exact: the sweep's own regex stops at a sentence boundary, so **Chandra,
Spark Hunter is missed by the measurement of the bug she demonstrates** — her clause is
`+2: You may sacrifice an artifact or discard a card. If you do, draw a card.`, and the
draw sits in the next sentence. `classify_roles` returns `{'Removal (spot)'}` for her, and
even that comes from the `−7` emblem's "deals 3 damage to any target", not from anything
she does on the turn you cast her.

### The cost, on a real swap

Deck 58 Treasure Planet, `-Elvish Archivist +Chandra`. The quality guard reported
`⚠ card advantage dropped (4→3)`. Both halves of that are backwards:

- Archivist's draw half is *"whenever one or more ENCHANTMENTS you control enter, draw a
  card"* — trigger-shaped, so it counts — and deck 58 runs **two** enchantments, so it was
  close to dead.
- Chandra's `+2` draws **every turn**, unconditionally, and counts for nothing.

The mirror image showed up in the same batch: interaction read 8→9 in deck 58 and 14→15 in
deck 10, both from her `−7` emblem parsing as removal — an ultimate that will be activated
in a small fraction of games counted as a full removal spell.

**The habit:** a ⚠ card-advantage regression on a swap involving a planeswalker or an
activated-draw engine is UNPROVEN, not a verdict. Check whether the added card's draw is
cost-shaped before accepting it, and record the reasoning in the deck's `#: notes:` (58 and
10 both do) so the next pass does not re-derive it. This is K-12's CONNIVE case one level
down — same failure, different grammar — and a G-67 whitelist miss: never an error, never
an over-count, always a silent UNDER-count.

### The fix (2026-08-07), and why its shape matters more than its content

Two patterns were added to the `Card advantage` bucket, plus one clause to `_LOOT_RE`. The
justification is not new — an activated ability is repeatable BY CONSTRUCTION, which is
verbatim the argument the `whenever …, draw a card` pattern already rested on. What needed
care was not *whether* to widen but *how far*, because this bucket has never produced an
over-count and the change had to keep it that way.

**Three exclusions, each taken from a rule the module already stated rather than invented
for the occasion:**

| exclusion | why | the rule it comes from |
|---|---|---|
| `(?m)^` line anchor | oracle text puts each ability on its own line, so a cost quoted inside REMINDER text is mid-line — every Clue and Blood token maker quotes `{2}, Sacrifice this artifact: Draw a card` and must not pick up the role from the quote | new, and the only genuinely new one |
| `discard` in the cost span | `{T}, Discard a card: Draw a card` (Charging Strifeknight, Professor Zei) is RUMMAGING — card-neutral | `_LOOT_RE`, one clause over; the only difference is which side of the colon the discard sits on |
| `sacrifice this` in the cost span | `{2}, Sacrifice this artifact: Draw a card` consumes the source, so it is a ONE-SHOT single draw | the cantrip rule this bucket already implements ("a one-card draw is deliberately NOT counted") |

The third is the one that mattered most, and it was found by measuring rather than by
reasoning. Counting self-sacrifice draws would have swept in the common
`{4}, {T}, Sacrifice this land: Draw a card` tapland cycle and taken the change from **24
decks to 58** — a roster-wide re-grade driven by flood-insurance lands. An ability-word
prefix (`Delirium — {2}{U}, {T}: Draw a card`) was added after a separate measurement showed
it changes the final answer for exactly THREE cards: Raving Visionary, Jodah's Codex,
Thought Shucker. Re-run that measurement if the prefix is ever loosened.

**`_LOOT_RE` gained the singular pair** — `draw a card, then discard a card`. Its comment
used to say connive "never counted in the first place", which was true only because nothing
matched a bare "draw a card" at all. The moment a cost-shaped pattern landed, Bag of
Holding, Collector's Vault, Agna Qel'a, Merfolk Looter and 74 others would have scored as
draw engines. The invariant is now true by construction instead of by accident.

### The measured result

Roster-wide before/after, per the K-12 mandate:

- **card advantage: 18 decks up, 12 down, 65 unchanged.** Every one of the 12 decreases is
  a looter losing a role it should never have had (Gran-Gran, Silvergill Peddler, Emet-Selch,
  Mechan Navigator). Deck 22's figure fell 11 → 8 and its `#: tier:` claim that the draws are
  "a real engine, not a pile of cantrips" went from asserted to measured.
- **interaction: unchanged on all 95 decks** — the change touches one bucket.
- **tier floors: ZERO moved.** This is the property that made the change shippable at all.
  CLAUDE.md keeps the protection axis and the X-cost advisory REPORT-ONLY precisely so a
  measurement change cannot silently re-grade the roster; a widening that DOES feed
  `tier_band` has to clear the same bar, and this one was checked before it landed rather
  than after.
- **16 decks had a stale `#: tier:` figure afterwards** and were re-grounded in the same
  commit. The largest is deck 42a at 4 → 8 — sacrifice-for-value IS that archetype, so the
  deck most exposed to this blind spot was the one built entirely on it. Deck 21a's 3 → 5
  removed one of the two weaknesses its sub-floor letter rested on, and is flagged in-file
  for a HUMAN re-grade rather than re-graded automatically.

Seven tests pin the behaviour, every fixture written from a card's real oracle text with its
newlines intact — a paraphrase would not exercise the line anchor, which is the whole
defence against the reminder-text over-count.

### The 2026-08-19 pair, found by reading the POOL corpus-wide (BS6-10)

The four holes closed earlier that day came from working `check_roles.py`'s zero-role
**roster** backlog end to end. That list is scoped to cards you OWN or run — which is the
right scope for a radar about your decks, and the wrong one for the recommender, whose
candidate set is the whole pool. Sweeping all 16,067 pool rows instead surfaced two more,
and both are on **`Removal (spot)`, i.e. the interaction axis `tier_band` actually grades**
— unlike the anthem hole above, which was invisible precisely because anthem is not graded.

| templating | example | uncounted |
|---|---|---|
| `Enchanted creature gets -N/-N` (removal Aura) | Dead Weight, Debilitating Injury, Mire's Grasp | **20** |
| `destroy target attacking or blocking creature` | Divine Verdict, Sudden Strike, Puncturing Light | 6 |
| `destroy target <colour> or <colour> creature` | Deathmark | 7 |
| `destroy target non-A, non-B, non-C creature` | Power Word Kill | 1 |

The last three are one root cause: the main pattern's adjective run is `(?:[a-z-]+ ){0,2}?`,
which covers `target TAPPED creature` but not a coordinated qualifier LIST — "attacking or
blocking" is three words, and "non-Angel, non-Demon, non-Devil, non-Dragon" is four with
commas `[a-z-]+ ` cannot cross.

**The Aura hole is the instructive one, twice over.** First, `enchanted creature can't attack
or block` (Pacifism) was ALREADY in this bucket, so the repo had long since decided a
neutralizing Aura is spot removal — the shrink-the-creature twin simply was never written.
Second, the non-Aura templating of the identical effect (`target creature gets -N/-N`) is
fully covered: **120 pool cards, zero misses.** Same effect, one noun covered and its sibling
not, which is this rule's signature. And it is a live **K-09** violation, which is how it was
found at all: `tag_synergies` tags Dead Weight `removal` while `classify_roles` returned
nothing, so the two models disagreed about the same text.

### Why both patterns are ADDITIVE rather than a widening

The obvious fix — raise the shared adjective run from `{0,2}` to `{0,5}` — was rejected. It
re-scores every removal card in the pool at once, and BS2-06 is the record of what a silent
OVER-count costs (89 player-only burn cards read as spot removal; 17 decks over-reported the
graded axis). Requiring **at least three** qualifier words instead makes the new pattern
strictly additive: anything the existing run already reaches is out of its scope, so the
roster diff attributes every change to it.

Both false-positive classes were measured against the whole pool before shipping, not
reasoned about:

- **The graveyard ZONE.** `land` and `creature` are both in `_PERM_TYPE`, so without a
  lookahead "exile target card other than a basic land card from an opponent's graveyard"
  (Kotose) and "exile target red, white, or black creature card from your graveyard"
  (Offspring's Revenge) read as removal — graveyard hate and a recursion cost, neither an
  answer to a permanent. `[^.]{0,40}` keeps the guard inside one sentence, so plain "Destroy
  target creature." is untouched. 13 matches → 11 with the guard, both drops correct.
- **`enchant creature you control`.** Craving of Yeenoghu is a BUFF Aura on your own creature
  whose recursion clause perpetually gains `"Enchanted creature gets -1/-1."` It was the only
  false positive in 23 matches. The guard must NOT catch Duskmourn's Domination, whose "You
  control enchanted creature" is a Control-Magic steal — a real answer — written in the other
  word order, which is why the guard is a literal phrase rather than a colour-of-controller
  test.

### The measured result, and the residual that is the real work

K-14 roster diff over all 113 decks: **0 decks moved a graded axis, 0 tier floors moved.** No
deck currently runs one of the 29 cards, so the entire value is upstream, in what the
recommender can see: `deck.py suggest 38 --interaction` reports "current interaction: SHORT
(3 < 5)" and previously answered with four mythics and three rares, because a 1-mana common
that fixes the deficit was not in the candidate set at all.

**The residual is bigger than the fix and is a TAXONOMY question, not a pattern one.** 124
pool cards neutralize rather than destroy and carry no interaction role: **83** tap-down
(`doesn't untap during its controller's untap step`) and **41** `loses all abilities`. Six
decks are live-affected today — deck 15 by 2, decks 16 / 27 / 32 / 38a / 38 by 1. None
crosses a band right now, but **deck 38 sits at interaction 3, exactly the B floor**, so one
cut on that axis grades it wrong in the other direction. Adding a bucket re-scores every deck
running the type, which is why it belongs with the Equipment question as a decision taken
deliberately with a K-14 diff, not slipped in as a pattern fix.

Nine tests pin the behaviour, every fixture verbatim from the card.

### The neutralization bucket, closed 2026-08-19 — and the line that closes it

The BS6-10 pair above fixed two ways of writing "destroy". This is the THIRD way Magic
answers a creature, and it was the standing TAXONOMY residual this rule carried for a
cycle: you can kill it, exile it, or **turn it off**, and `_ROLE_PATTERNS` read only the
first two — while `enchanted creature can't attack or block` (Pacifism) had been sitting
in the Removal bucket the entire time. The repo had already decided a neutralizing effect
IS spot removal. Only half the templatings were ever written.

| templating | example | closed |
|---|---|---|
| tap-down, permanent | Waterknot, Capture Sphere, Dungeon Geists, Tidebinder Mage | 37 |
| ability-strip, Aura | Frogify, Kasmina's Transmutation, Witness Protection | 19 |
| ability-strip, targeted | Oko, Patriar's Humiliation, Resolute Rejection | 6 |
| ability-strip, anaphor | The Wondrous Wasp | 1 |

**THE LINE IS PERMANENCE, and it is the durable part of this entry.** A one-turn effect
is TEMPO, not an answer, so `doesn't untap during its controller's NEXT untap step` (Frost
Lynx, White Dragon — 35 cards) and `loses all abilities UNTIL end of turn / until your
next turn` (Merfolk Trickster, Azure Beastbinder) are excluded. That is the conservative
direction: a tempo card read as removal inflates the axis the tier floor grades on, which
is the BS2-06 failure this rule already records.

Two guards carry the same weight as the patterns:

- **`its controller's`.** The identical clause is a DRAWBACK on your own card — "Colossus
  of Sardia doesn't untap during YOUR untap step" — and 11 pool cards ride on that one
  word. Without it a vanilla drawback reads as removal.
- **`except `.** Town-Razer Tyrant's "loses all abilities EXCEPT mana abilities" punishes
  a land; it does not answer a threat.

The fourth pattern matches exactly ONE card, which is normally a smell. It earns its place
by closing an INCONSISTENCY rather than adding coverage: The Wondrous Wasp strips "for as
long as this remains on the battlefield" and Ty Lee, Chi Blocker does the identical thing
one clause over and was already counted by the tap-down pattern. Two cards with one effect
shape were landing on opposite sides of the line.

### The measured result, and where the value actually landed

K-14 over 113 decks: **6 decks moved interaction, ZERO tier floors moved, ZERO letters to
re-grade** — deck 15 by 2, decks 16/27/32/38a/38 by 1, exactly the six the audit predicted.
Deck 38 moved 3 → 4, off the B floor it had been sitting exactly on. All six `#: tier:`
rationales audited clean afterwards. `role_baseline.txt` lost two entries the fix un-zeroed
(Frozen in Ice, The Wondrous Wasp), surfaced by the baseline's own stale-entry sweep.

**The payoff is upstream, in what the recommender can see, and that is the general lesson.**
Blue's removal is largely neutralization, so it was invisible to the one command that
exists to fix an interaction deficit: `deck.py suggest 47 --interaction` now surfaces Sleep
Magic, Charmed Sleep and Witness Protection — and the last of those is already OWNED. A
whitelist hole on an axis costs you the recommendation long before it costs you a grade.

### THE NEW RESIDUAL, and why the permanence rule does NOT transfer to it

`target creature gets -N/-N` is covered (120 cards). `target creature gets **+N/-N**` is
not: **5 pool cards** — Nameless Inversion, Auger Spree, Lash of Malice, Flowstone
Infusion, Desperate Measures — score no interaction role at all.

Do not fix this by extending the permanence rule, because the rule inverts here. A
toughness reduction that lasts "until end of turn" still KILLS, and a dead creature does
not come back at cleanup — so unlike an ability-strip, the temporary version does
permanent work. `Auger Spree` is a removal spell in a way `Merfolk Trickster` is not,
despite both saying "until end of turn". Any pattern for this family has to be written
against LETHALITY, not duration.

All five were already sitting in `tag_role_baseline.txt` — the tagger's `gets [+-]?N/-N`
rule caught them, the classifier did not, so the disagreement sweep carried them as
worklist entries rather than losing them. That is the sweep doing its job on the first
hole discovered after it was built.

**CLOSED the same cycle**, and the way it closed is the part worth keeping. The pattern is
scoped to the TARGETED spell, because 23 of the 29 pool cards carrying a `+N/-M` clause are
firebreathing-style self-pumps on your own body ("{U}: This creature gets +1/-1") — the same
drawback-vs-answer split `its controller's` handles for tap-down, one family over. With
`target … creature` plus a `you control` guard: 5 matches, zero false positives, and the
baseline pruned from 143 to 138 by its own stale-entry pass.

**The AURA form is deliberately left unclassified**, and this is the honest kind of residual.
Immolation ("Enchanted creature gets +2/-2") reads as removal; Mogis's Favor ("+2/-1", with
an escape cost) reads as a pump you put on your own creature. Two cards, opposite intents,
identical shape — no regex separates them, and inventing a rule that picks one would be
guessing rather than measuring. Grade those two from the card.

**And the transferable lesson is about rule REUSE, not about pumps.** The neutralization
patterns immediately above rest on PERMANENCE, and reaching for that rule here would have
been wrong in the other direction: it would have excluded exactly the cards that belong.
When a new family looks adjacent to one you have already solved, ask which rule the family
takes before reusing the one that is to hand.

**Measured 2026-08-27 and NOT taken: a "token engine" family.** Desert Were-Worm (extra
combat at total power 12) and Dragonmaster Outcast (a 5/5 every upkeep at six lands) both
score zero roles and landed in the baseline. Before treating that as two more whitelist
holes, the analogous cards were run through `classify_roles` directly: Hop to It, Head of
the Homestead and Rapacious Dragon — token MAKERS — are all zero-role too, while Lathliss
and Sally Pride DO score, and score as *Payoff / engine* for their triggers on other
events, not for the tokens they create. So the taxonomy is consistent: **token creation is
a tag, not a role; a role fires when the card pays off something else happening.** Adding
a token-engine role would not move `tier_band` (which grades interaction + card
advantage), so per the S1-04 precedent (Equipment 31, hand-attack 31 — measured, declined)
the family stays out. The two cards are acknowledged in `role_baseline.txt`, which is the
mechanism built for exactly this: a deliberate zero, on the record.

## [G-68] A `#:` header that lists card names goes stale, and nothing checked one

Two deck headers are a semicolon-separated list of CARD NAMES rather than prose:

```
#: protect: Monument to Endurance; Cool but Rude; Magmakin Artillerist
#: uncastable-ok: Rise of the Dark Realms; Omniscience
```

Both are read by the tooling as instructions. `_protected()` feeds `cuts`, which
hard-excludes those cards from its ranking and prints them above the table;
`_uncastable_ok()` feeds the castability lint and `tier_band`, exempting named cards from
a failure that would otherwise be hard. Neither reader validates that a name matches a
card in the deck — it builds a lowercased set and tests membership, so a name matching
nothing simply never matches anything.

### What that costs, measured on the two decks it was found on

**Deck 26b (found by hand, 2026-08-07).** Its `#: protect:` header named **Summon:
Bahamut**, a card the deck has never run — it went to variant 48a in the pivot the deck's
own `#: notes:` block records. Two separate failures:

1. **The entry protected nothing.** If the name had been a TYPO for a card actually in the
   deck rather than a leftover, the card it was meant to shield would have been silently
   cuttable the whole time, with the header on the page saying otherwise.
2. **It inflated a number a human reads.** `stats` and `tier` both print
   `⚠ ZERO protection, but #: protect: names N build-around card(s)` — 26b reported
   **five against a real four**, inside the exact sentence its `#: tier:` block uses to
   argue why the deck is capped at B. A reader checking that argument would have been
   checking a wrong figure.

**Deck 56 (found by the sweep, the first time it ran).** The Boros core deck's header
protected **Ashroot Animist** and **Halana and Alena, Partners** — both R/G, both living
only in the Gruul variant **56a**. A mono-Boros deck was protecting two green cards it
cannot even cast. Same shape as 26b: a variant split left the parent's header behind.

### Why no gate could see it

This is the project's recurring shape — a capability that exists and is never reached
(G-53) — one layer over from where it usually appears:

| what it checks | what it reads | sees a bad header entry? |
|---|---|---|
| INV-04 | deck card LINES, `(SET) COLLECTOR#` | no — a `#:` line is not a card line |
| `tier --audit-rationale` | `#: tier:` / `#: archetype:` PROSE | no — scoped to those two headers |
| `flex_staleness` | `#~` flex lines | no — different block |
| **nothing** | **`#: protect:` / `#: uncastable-ok:`** | — |

The three sibling sweeps ran on every `check_all` while this one did not exist. Note that
`protect` and `uncastable-ok` were already exactly parallel in FORM (semicolon-separated,
because card names contain commas, and both documented that way in `_protected`'s and
`_uncastable_ok`'s docstrings) — the parallel just never extended to validation.

### The fix

`deck.header_card_staleness(path)` → `[(header, name)]`, swept roster-wide inside
`check_all` as a SOFT warning. Soft because pruning a header is an editorial call: a stale
entry might be a leftover to delete or a typo to correct, and the tool cannot tell which.

The name join goes through **`_ms_key`** (G-63), which is load-bearing rather than
decorative: a header customarily names a DFC by its front face (`Ojer Axonil, Deepest
Might`) while the deck LINE stores the full `Front // Back`. A raw-name join would report
every such live entry as stale — the precise bug `_ms_key` was extracted to prevent, and
`_multiset` is the one that already made it once.

`#: uncastable-ok:` is swept alongside `#: protect:` and is the more dangerous of the two.
A stale `protect` entry disables a BOOST; a stale `uncastable-ok` entry disables a CHECK —
it exists to suppress a castability failure, so a leftover name means a genuine uncastable
card added later could be silently exempted if the names happened to collide.

Five tests pin it, including a roster-wide behavioural anchor: both known instances are
fixed, so any new hit is a regression someone introduced rather than a backlog item.

## [G-69] A baseline updated before the gate that reads it is a muted gate

`check_roles.py` is the radar for cards `classify_roles` scores with NO functional role.
Its contract, in its own docstring, is *"the set only ever SHRINKS, and a NEW zero gets
looked at once."* The looking-at-once is the entire value: `_ROLE_PATTERNS` is a whitelist
(G-67), its failure mode is a silent under-count, and eight such holes were found in one
2026-08 session — every one by a human reading a card.

`make postedit`, the after-every-deck-edit tail, ran:

```
python3 scripts/check_roles.py --update-baseline     # step 1
python3 scripts/build_dashboard.py                   # step 2
python3 scripts/check_all.py                         # step 3
```

and the Makefile comment explained the ordering: *"the baseline must update BEFORE
check_all or the gate warns about the cards the baseline was about to acknowledge."* That
sentence is correct about the mechanics and describes a muted radar. Step 1 consumed the
warning step 3 existed to raise, on precisely the workflow the radar was built for.

**FIXED in broad-scan-7 (S2-02): the order is reversed.** `postedit` now runs
`build_dashboard.py` → `check_all.py` → `check_roles.py --update-baseline`, and its step-3
echo says why — *"acknowledge what step 2 just reported"*. A deck edit that leaves a new
zero-role card now produces the soft warning on the run that earned it, and the same run's
step 3 clears it by name. Measured at the time: 490 of 490 zero-role cards already
baselined, so the sweep is silent on a clean tree and a firing is attributable to the edit.
The Makefile comment that justified the old order is gone with it — **that comment is the
artifact worth remembering, because it was a correct mechanical explanation of a
self-defeating design, and reading it as a reason is what kept the order in place.**

**Why it could not self-correct.** `--update-baseline` rewrites the file from the CURRENT
zero-role set — it is all-or-nothing, with no per-entry acknowledge. So it cannot
distinguish:

* one genuinely roleless new card (a vanilla body, a pure combat trick), from
* a `_ROLE_PATTERNS` edit that just re-zeroed fifty cards that used to classify.

Both are "the baseline grew." The only residual signal was an unreviewed diff of a
425-line file inside a commit that also touched decks and the dashboard, and the printed
output was a single total — a number that moves without naming what moved is exactly the
delta-blind shape K-01 documents.

**The fix keeps the ergonomics and removes the silence.** `baseline_delta()` reports what
an update WOULD change (newly-acknowledged DISPLAY names, plus pruned entries);
`--update-baseline` now always computes it first, NAMES every card it acknowledges, and
REFUSES a jump larger than `--max-new` (exit 1, writing nothing, printing the names and
the remedy). `make postedit` passes `MAXNEW`, default 8; a real bulk acknowledge is
`make postedit MAXNEW=40`, which is a deliberate act rather than a default.

**The generalization is the point.** When one command contains both an ACKNOWLEDGE step
and a WARN step over the same set, the order decides whether the warning exists at all —
and the convenience of automating the pair is what hides it. The same all-or-nothing
rewrite still sits under `check_keywords.py --update-baseline`; it is not currently
automated into a routine command, which is the only reason it is not the same bug.

## [G-70] Buildability is per card NAME, never per line

"Do I own this deck" is a comparison of TOTAL need against TOTAL owned, for two reasons
that are both properties of this data rather than conventions:

* a deck file may list the same card on more than one line (two printings, or an edit
  that appended rather than bumped), and
* owned counts are per NAME, because copies are fungible across printings — the rule
  `deck.py` and `pool.py` already share.

So a per-LINE comparison asks a question nobody wanted the answer to: "is each individual
line covered by my total holding", which passes twice for a card owned once.

`cmd_check` has always done this correctly and carried a comment saying so:

```
# Aggregate copies per card first: a deck may list the same card on more than
# one line, and owned counts are per-name (fungible across printings), so the
# short/missing check must compare total-need vs total-owned, not line-by-line.
```

**A comment is not a mechanism.** Two other surfaces re-derived the same question with
their own loop and got it wrong: `app.py`'s `/decks` overview and `check_all`'s deck
buildability summary both compared each line's quantity against total owned. A deck
listing `2 Duress` + `2 Duress` with 3 owned therefore read **buildable** on those two
surfaces while `deck.py check`, the dashboard's `collect()` (which sums `need[n]`) and the
deck editor's `needFor()` all correctly read **short**. `/decks` additionally reported
`unique` as a count of LINES.

This is the shape `check_agreement.py` exists to catch — two implementations of one
question drifting — in a place it does not reach, because the drifted copies were not
functions it compares. The two that were wrong were precisely the two that had COPIED the
loop instead of calling something.

**Fixed (BS4-13) by giving the question one definition.** `deck.deck_requirements(cards)`
returns the distinct cards in first-seen order with copies summed; `deck.deck_build_gap(
cards, by_name_qty)` returns the `(missing, short)` pair. `cmd_check` calls the first — its
aggregation was extracted, not altered — and both other surfaces call the second. Verified
by cross-checking `/decks` against `deck_build_gap` for all 99 roster decks: no
disagreements.

No displayed number changed on the day of the fix, because no roster deck currently splits
a card across two lines. That is worth stating plainly: the fix is against the CASE, not
against a symptom that was visible. The case arrives the first time someone adds a second
printing of a card a deck already runs — which the editor permits and which the dashboard
and `deck.py` would then report differently from `/decks`.

**The generalizable rule:** when you are about to write a second loop over a deck's
`cards` that compares quantities against owned counts, call the helper. The first loop was
right for ten months and still produced two wrong surfaces.


## [G-71] A memoized table is shared state, and a mutating helper will mutate it

**A MEMOIZED TABLE IS SHARED STATE, and a helper that mutates its ARGUMENT will mutate
it.** `deck._file_memo` exists for a good reason — the reference CSVs were re-parsed on
every loader call, 65 decks × ~0.31s in a roster pass, which is why the rationale sweep
looked too expensive to run automatically and therefore never ran (see G-26). It takes
`check_all` from ~23s to ~4s. The cost is that every caller now receives THE SAME dict.

Its docstring acknowledged that and made a claim about it:

> Safe because every caller treats these tables as READ-ONLY — **verified by scanning all
> of scripts/ for external mutation of a loader's result**; if you ever need to mutate one,
> copy it first, since the dict is now shared.

**The scan had missed five call sites in the same file** (broad-scan BS5-13).
`fetch_missing_mana(names, mana)` and `fetch_missing_rarities(names, rarities)` write into
the dict they are GIVEN — their whole job is to fill gaps — and `cmd_stats`, `cmd_mana`,
`cmd_consistency`, `_do_swap` and `cmd_wildcards` were each handing them `load_mana()` /
`load_rarities()` directly. Demonstrated:

    >>> m1 = deck.load_mana(); m1['__probe__'] = ('{X}', 99)
    >>> '__probe__' in deck.load_mana()
    True

**Why it stayed invisible, and where it was not.** A one-shot CLI run exits before anything
else reads the polluted table, and `build_dashboard._no_network()` stubs both fetchers out,
so the published artifact was never affected. The surface that DOES notice is the Flask
editor: `/api/deck/analysis/<id>/<kind>` serves many decks from one long-lived process, so
opening deck A's Mana tab live-fetched costs into the shared table and deck B's Stats tab
then computed its curve from them — an answer that depended on what you had clicked earlier
in the session, and that disagreed with a fresh `deck.py stats B`.

**The fix** is the docstring's own prescription: the five sites pass `dict(load_mana())` /
`dict(load_rarities())`. A shallow copy suffices (values are tuples and strings) and costs
sub-milliseconds against the ~300ms parse the memo exists to avoid.

**The transferable half is about the CLAIM, not the bug.** "Verified by scanning all of
scripts/" is a statement about a moment, and it decays the instant someone adds a caller —
the same shape as G-63's "defer on the MECHANISM, never on the census" and G-53's
capability-nothing-reaches. So the property is pinned BEHAVIOURALLY now
(`tests/test_deck.py::TestMemoizedTablesAreNotMutated` stubs the fetchers with ones that
write, runs the real `cmd_*`, and asserts the shared table came back unchanged) rather than
by a second source scan — because a source scan is precisely what failed. All four pins
fail with `assert not True` against the unfixed module.


### The scan's SCOPE was the bug (BS6-01, closed 2026-08-19)

Guard (4) exists because every G-63 index bug so far was a loader nobody had listed. It
still missed four at once, and the reason was not the registry — it was the SCAN. It
looked for `csv.DictReader` plus a `card-pool.csv` cue, and every OWNERSHIP index reads
**card-library.csv**, through `lib.load_rows`. So all four sat outside a scan written to
find exactly the bug they had, while the gate reported OK.

A gate whose scope excludes the file the bug lives in is not a narrow gate, it is an
absent one. The cue sets now cover both files and both readers.

**Widening it needed two second-order fixes to stay honest, and both are reusable.**

- **A tuple-key discriminator.** The first widened run reported 8 unregistered builders,
  3 of them printing indexes keyed by `(name, set, collector)` — `app.save`,
  `validate.validate`, `import_arena.merge`. A front-face alias is meaningless for a
  printing key: that identifies one physical printing, which is INV-01's business, not
  G-63's. `_tuple_bound_names` rejects tuple keys, literal or via a tuple-bound local. A
  scan with a 3-in-8 false-positive rate is a scan that stops being read.
- **A second PROBE.** The behavioural check is `full in idx and front not in idx`, and the
  probe was the pool's first DFC — "Life // Death", which is not in the collection at all.
  So `full in idx` was False for every library-shaped loader and all four passed
  **VACUOUSLY**: registered, green, never exercised. There is now a LIBRARY probe as well,
  and a loud "alias NOT exercised" line when neither probe reaches a registered loader,
  because silence was the entire failure.

It found a live bug within minutes of being widened, which is the argument for it:
`verify_ingest.library_index` was the FOURTH library-side ownership index and was still
unaliased — the other three had been fixed by hand — so a paste naming a Room card by its
FRONT face verified as ABSENT, from the tool whose only job is confirming an ingest landed.

## [G-72] A control built in JavaScript is a control only if it goes through a11y()

**A CONTROL BUILT IN JAVASCRIPT IS A CONTROL ONLY IF IT GOES THROUGH `a11y()`.** A `<div>`,
`<span>` or href-less `<a>` carrying a click handler is invisible to a keyboard and to
assistive tech: no role, no tab stop, no Enter/Space. This project has now hit that four
times, and the pattern in WHERE is the useful part:

| where | what | found |
|---|---|---|
| `templates/collection.html` | six colour filter pips | I-01 |
| `templates/deck.html` | the four Analysis tabs | S-2 |
| `build_dashboard.py` | the roster-triage Deck cell (`<a>` with no href) | BS5-02 |
| `build_dashboard.py` | the card finder's `<span>` chips | BS5-03 |

**All three 2026-08 interface defects were in the GENERATED pages** — the two above plus
BS5-10, where `gallery.html`'s light mode painted a hardcoded `#0f1115` bar track onto a
near-white panel. That is not coincidence. `tests/test_templates.py` parses `templates/`
with `html.parser` and can assert "this element is a control"; for `build_dashboard.py` and
`build_gallery.py` the markup does not exist until the browser runs, so the file can only
be pinned by SOURCE assertions on individual named controls — and a control nobody thought
to name is unpinned by construction. The triage table's own note even told the user "Click
a deck to filter the list below" while that click was mouse-only.

**Two mechanics worth remembering.** First, `a11y(node, opts)` is the single definition of
what a control is on that page — it sets role (or preserves a semantic one with
`role:null`), `tabIndex = 0`, the aria state, and an Enter/Space handler that routes through
`.click()` so the click handler stays the only copy of the behaviour. Reuse it; do not
hand-write `tabindex` next to a listener. Second, **inside a sortable table apply it in
`onRowExtra`, not after `appendChild`**: `sortableTable`'s internal `redraw()` rebuilds
`<tbody>` on every sort click, so attributes applied once are discarded by the first sort —
which would have made the fix look correct and fail on the second interaction.

The perceptual halves (focus-ring visibility, the gallery's light palette) cannot be proven
from a file and live in Regression Scenarios 5 and 7.


**THE STATIC GATE WAS ATTEMPTED AND MEASURED UNBUILDABLE (2026-08-12). Do not restart it
from scratch — start from this measurement.** Three designs were prototyped against
`build_dashboard.py` and `build_gallery.py`:

1. Flag every `.onclick =` / `addEventListener('click'` whose target does not appear in an
   `a11y(<target>` call. **14 flags, all false.** Controls are wrapped at CREATION
   (`const pin = a11y(el('span', …), {...})`), so `a11y(pin` never appears; `$('id')`
   targets are real `<button>`s in the static HTML; overlay backdrops take a click to
   close and are correctly not focusable.
2. The same, plus declaration lookup and native-control detection. **13 flags, all false.**
   The blocker is JS variable scoping: four different `tb`, `x`, `p` and `s` exist in
   different scopes, and a regex over a Python string containing JS cannot tell them apart.
3. Markup-level rules (an `<a>` with no `href`; an element named by a delegated click
   selector without `tabindex`). Flags the two sites that ARE fixed — they are a11y'd at
   RUNTIME, so the markup legitimately lacks the attributes — plus a code COMMENT
   containing `<a>` and two `.card` ITERATION selectors.

The common cause: the a11y happens at runtime, so a markup rule flags correct code and a JS
rule cannot resolve scope. A real gate needs a JS parser, which breaks the project's
zero-dependency constraint. The only design that survives scrutiny is a baselined
delta-scan (the `check_roles` pattern), which needs ~14 acknowledged entries and inherits
G-69's acknowledge-before-warn muting risk.

**So the coverage for this class is human and scheduled**: Regression Scenario 7's keyboard
walk. That makes Scenario 7 materially more valuable than a routine perceptual check — it
is the only thing standing between this defect class and production.



---

### The next layer out: an a11y'd NODE is not a11y'd BEHAVIOUR (BS6-03, 2026-08-19)

Every instance above is a control that was never made focusable. This one is the inverse and
is harder to see: the control was fine, and a BEHAVIOUR attached to it silently was not.

`build_dashboard.py`'s `attachHover(node, name)` gives a card name a hover preview — the card
image, which is the EVIDENCE for a craft decision, i.e. G-52 in interface form. The S-7 pass
added `focus`/`blur` listeners beside the mouse ones so "the preview follows FOCUS, not just
the mouse." It has three call sites:

| call site | node | focusable? |
|---|---|---|
| `craftNameCell` — roster craft table | bare `<span class="hovname">` | **no** |
| the impact / leverage grid | bare `<span class="nm">` | **no** (the parent `.lev` card is) |
| the wishlist table | `a11y(el('span','wlname', …))` | yes |

`focus` does not fire on a non-focusable element **and does not bubble**, so the listeners on
the first two were inert from the day they were written. The feature worked at one site out
of three, and the two that failed are the craft plan and the "what does this card unlock"
grid — the two surfaces whose whole job is spending wildcards.

**What made it invisible is the shape worth remembering.** Scenario 7's step list says "focus
a wishlist card NAME to check the card image appears" — it names the ONE call site that
works. A regression scenario written from the fix rather than from the feature will keep
passing over an inert implementation indefinitely. This is G-40's lesson ("a pure-function
anchor cannot see whether a caller asks") in the interface layer, where no static gate can
reach it at all.

**The fix makes the focus host explicit** rather than adding `tabindex` blindly:
`attachHover(node, name, focusHost)`. The default host is the node itself, MADE focusable
with a `tabIndex` and an `aria-label` — what a bare span needs. The leverage grid passes its
already-a11y'd `.lev` card instead, so a second tab stop is not nested inside a
`role="button"`. Mouse behaviour is unchanged at all three sites, and a future call site
cannot inherit the bug, because the default now works.

Note this does NOT trip the redraw trap the rule above describes: `craftNameCell` is a
per-row `node:` factory that `sortableTable`'s internal `redraw()` re-invokes on every sort,
so the attributes are re-applied rather than set once and discarded.

## [G-73] A deck's repo name and its Arena name are different strings, and neither is authoritative

**The measurement, 2026-08-14.** The name-prefix attribution route (`"07 Earth's
Mightiest"` → deck 7) validates the leading NUMBER and nothing else, and `--apply` then
writes that guess into the deck file as a permanent `#: arena:` header, after which every
later match resolves to it with full confidence. Cross-checking the name's remainder
against the repo deck's `#: name:` looks like a free confirmation, and it was proposed as
exactly that.

It is not free. Measured over all 22 `#: arena:` headers then on the roster — **every one
of them a correct mapping** — 8 DISAGREED with the repo name under a containment test:

| Arena name | repo name at the time |
|---|---|
| 48 Doombots | Doombot Array |
| 49 Big Draco | Scaleforge |
| 26b Ancient Decay | Iron Forge — Scrapyard Tithe |
| 45 The Exiles | Exile Dividend |
| 52a Void Realm | Void Demons — Dark Realms |
| 56a Executioner's Song | One Fell Swoop — Overgrowth |
| 58 Treasure Planet | Gold Standard |
| 28 Triceraton | Dino Stampede |

The Arena names are FLAVOUR names, chosen in the client for their own reasons. A gate
would have refused a correct attribution 36% of the time — the same saturation that made
the `review` flag 0% actionable in G-07, arrived at from the opposite direction. So the
number stays the sole match key and the repo name is merely DISCLOSED next to a `name
prefix` route, with a warning that `--apply` makes the guess permanent. Disclosure over
gating, the G-38 stance for a fuzzy signal.

**The reconcile half: `parse_matches.py --sync-names --apply`.** Adopting Arena's name
into the repo removes the divergence rather than tolerating it. It reports on every run
and writes only under BOTH flags, because an `#: arena:` header is bookkeeping the tooling
owns while a deck's NAME is human-authored prose other files cite.

**That two-flag split is a 2026-08-26 fix, and the shape is worth keeping.** The helper
`sync_deck_names(text, apply=…)` had taken the parameter since it was written, and tests
covered both sides of it. What was wrong was what `main()` PASSED: `apply=args.sync_names`
on the paste path — making it the one writer in the file that ignored `--apply` — and a
hardcoded `apply=True` on the sourceless path, so the invocation whose entire purpose is
the rename could not be previewed at all. A flag that reads like "show me the renames"
performed them, and it adopted ten `#: name:` headers in one session when two had been
shown to the user. **A correct, parameterized primitive says nothing about whether its
caller asks** — G-40 one layer up, and the reason the regression tests for this drive
`main()` rather than the helper. It also runs SOURCELESS — the stored
headers already hold Arena's answer, harvested by earlier runs, so a divergence built up
over months reconciles without a paste covering all 106 decks. That is not circular: the
header is Arena's answer recorded; the sync only asks whether `#: name:` still agrees.

Four rules keep it from doing damage, and each was earned rather than assumed:

1. **Identity is the DeckId GUID.** Not the deck number, and NOT a card list — which is
   what was originally asked for. The GUID is strictly stronger: it survives every edit
   Arena permits, whereas a card list changes the moment you tune, so card-matching would
   refuse exactly the decks under active development, which are the ones most likely to
   have been renamed. It is also the only option available — nothing in this repo maps
   Arena's numeric `cardId` to a card name, and the documented extraction now strips the
   `MainDeck` array precisely because nothing reads it (G-57). A name-prefix match NEVER
   renames.
2. **Typography is not a rename.** Arena writes a curly apostrophe (`Earth's`), doubled
   spaces (`66  Lethal Protector`) and a hyphen where the repo uses an em dash
   (`Grand Lotus- Comet`). Comparison is on words only — lowercase, punctuation stripped —
   so 10 of the 22 paired decks correctly reported no change instead of churning the repo
   every run and importing the degradation. Adoption restores the em dash on the way in.
3. **The variant convention survives, in both directions.** Repo variants are named
   `<parent> — <variant>`, which G-27's rationale audit leans on ("a name forming part of
   THIS deck's own name is not another deck"). A variant adopting `Ancient Decay` becomes
   `Iron Forge — Ancient Decay`, and Arena repeating the parent is not doubled. The MIRROR
   has no automatic fix: renaming a PARENT breaks the shape for every variant beneath it,
   and those variants have no Arena GUID of their own, so nothing can rename them from
   evidence. The 2026-08-14 sync orphaned four (28a, 45a, 48a, 51a) and they were fixed by
   hand. `_variant_orphans` flags the case; it does not cascade, because composing a
   variant's new name is editorial and this tool adopts rather than composes.
4. **A rename strands prose citations.** 50 of the 106 decks are named inside another
   deck's `#:` header prose, and nothing rewrites prose automatically — the rationale audit
   reads CARD names and FIGURES, never deck names, so it cannot see this. `_name_citations`
   reports them at decision time (5 across 3 decks in the real run). Suppressed when the
   new name still CONTAINS the old one (`Unlock` → `Unlocked`, `Bird Brain` →
   `Bird Brain — Bant`), where the citation keeps reading correctly and flagging it would
   bury the real cases.

**THE DIVERGENCE REGROWS, and that is the part most likely to be misread later.** It is
generated by how decks get named in the client, not by a one-time drift, and the sync is
opt-in — so the roster is only ever as reconciled as the last run. Several docs cite the
8-of-22 measurement using examples that now read as agreements *because* the sync ran;
they are dated for that reason. **Do not read today's agreement as evidence the gate is
now safe.** Re-measure first.

**Directory slugs are cosmetic.** A deck id comes from the leading NUMBER of its directory
(`45-the-exiles` → 45) and a variant's from its filename prefix (`26b-…`), so the slug text
after the number is free-form. The slugs were re-pointed after the rename for readability
only; the convention is family-dir plus variant-suffix (`54-grand-lotus/54b-comet.txt` for
"Grand Lotus — Comet"), NOT slug-equals-name, so a variant file is slugged on its
distinguishing half alone.


## [G-74] The log cannot see what you faced, play/draw, or why you lost — nor a phone game

**The incident.** After the 2026-08-20 ingest took the record from 15 matches to 58, the
obvious next question was what the record could actually answer. Measured across all 58
rows: six of thirteen columns carried signal (`Date`, `Match ID`, `Deck`, `Result`,
`Event`, `Ended By`). `Reason` was `Success` on 58 of 58 — a literal constant. `My
Avatar` / `Opponent Avatar` are COSMETICS, not decks: `Avatar_Basic_AjaniGoldmane`
appeared 9 times because it is a common default, and reading it as an archetype is the
same misconception that once put an avatar value in a column called "Course ID" (G-57).
`Games Won`/`Games Lost` reads 0-0 on 43 rows, and even intact adds nothing — Play and
Ladder are best-of-one, so the game score restates `Result`.

So the record could say deck 35a went 0-3. It could never say *why*, or against what.

**The platform gap, which is the sharper half.** Every match in the sample showed
`"platformId": "SteamMac"` for the local seat. `Player.log` is written by the install
that played the game; a phone match writes to the phone's own sandboxed log, which Arena
neither exposes nor syncs. There is no extraction to fix and no flag to pass — phone
games are simply absent, and for a player who plays mostly on a phone the record would
be a biased sample of their own play rather than a thin one.

**The design, and the three decisions worth keeping.**

*Closed vocabulary for the loss reason.* Free text captures nuance and can never be
counted, and "which of my decks flood out" is the entire reason to record a reason. The
vocabulary is eight tokens with a free-text `note=` beside it, so the countable and the
nuanced live in different columns instead of fighting for one.

*Asymmetric validation.* An unknown DECK id is a hard reject, because it would appear in
`--report` as a deck no file backs — a phantom row reads as data. A `why` on a win is
refused, because a loss reason attached to a win is not a typo with a sensible reading.
An unknown `why` is warned about and **recorded anyway**: the vocabulary is a guess
someone will outgrow, and losing a real match to protect a list is the worse trade. The
rule generalizes — reject what would corrupt the read, warn about what merely fails to
group.

*Slug normalization on the archetype.* `Mono Red`, `mono-red` and `MONO  RED` all key
`mono-red`. Without it one archetype splits across three rows and each lands under the
20-match read floor, which is fragmentation producing the same nothing that a free-text
field produces.

**What `--add` cannot do, stated rather than hidden.** It only appends. The log path is
idempotent because Arena supplies a `matchId` to dedupe on; a hand-entered row has none,
so re-pasting lines already entered creates duplicates. The dry run printing every row is
the only available guard, and it cannot distinguish a repeat from a genuine second game
against the same deck on the same day — those are indistinguishable by construction.

**The dashboard panel is static and says so.** GitHub Pages cannot write `matches.csv`,
so the form queues rows in `localStorage` and hands back the exact `--add` lines. The
persistence is the load-bearing part rather than a convenience: the intended use is
logging a game on a phone mid-session, and without it a tab reload or a backgrounded
browser silently discards an evening's matches — the failure that makes someone stop
trusting the tool. The form's loss-reason dropdown reads `parse_matches.LOSS_REASONS`
live rather than a copy, so the page and the CLI cannot drift into disagreeing about the
vocabulary (the K-09 shape). `tests/test_parse_matches.py::TestTheDashboardFormAndTheCliAgree`
pins the emitted line's SHAPE, because nothing else connects the two modules and a
malformed line would surface only as a warning on someone's next paste.

**The `--add` vs `--annotate` split, added the same day.** The first design had one
writer. That is wrong, and the reason is worth keeping: a match Arena logged already has
a row carrying a real deck, result and date, and `--add` appends unconditionally because
a hand-entered row has no Arena `matchId` to dedupe on. Feeding logged matches through it
would have DOUBLE-COUNTED exactly the matches someone cared enough to annotate — the
subset most likely to be a deck under active tuning, so the corruption would concentrate
where the record is read hardest.

`--annotate` keys on the match id and writes only the four hand columns. That makes it
idempotent (run it twice, the row is identical), makes an empty value a legitimate CLEAR
so a wrong annotation is fixable without hand-editing the CSV, and makes an unknown id a
hard REJECT rather than a no-op — a truncated id would otherwise report success having
changed nothing. `deck`, `result` and `date` are refused outright: accepting them would
create a second, silent way to state a result, which is the "two writers, one fact" shape
that INV-03 and the `write_rows` schema guard exist to prevent one directory over.

**The page parses the log, and that is a second implementation of a question Python
already answers** — normally the `check_agreement` trap. It is acceptable here only
because of a containment property: the page reads the block ONLY to label rows for a
human, and every line it emits carries the match id and the four hand fields, never a
deck or a result. A seat-parsing error on that side can therefore produce a confusing
LABEL and nothing worse; `matches.csv`'s W/L comes from the Python parser in all cases.
Measured anyway on the 57-match sample: the page's result agreed with the stored Python
result on 57 of 57, with 0 ids found by one and not the other. Re-measure if either
parser's seat logic is touched — the containment is what makes a disagreement survivable,
not acceptable.

## [G-75] A tutor is worth the number of things it can find in THIS deck

**The incident.** Deck 76 (Spirit Call, five-colour Dragons) ran **zero basic lands**
while **two** cards searched for them: Bloomvine Regent's Omen half ("search your library
for up to two basic Forest cards") and Encroaching Dragonstorm ("...up to two basic land
cards"). The user found it by PLAYING A GAME and noticing the Omen did nothing. No gate
could see it, and the reason generalises: every model in this repo grades a card's OWN
TEXT, where "search for two basic Forests" reads as ramp. The number that decides whether
it is ramp or a blank lives in the LIST — the same G-61 shape as the four dismissals that
rule was written for.

**The aggravating half.** Encroaching Dragonstorm had been added the day before, and the
fetched basics were its *stated rationale* — the claim being that Leyline of the Guildpact
would upgrade them. That is a misread: the Leyline's "lands you control are every basic
land type" applies to lands you CONTROL, never to lands in your library, and there were no
basics to fetch in any case. So the swap traded a functional Mox Jasper for a blank, and
the reasoning was checked by nothing either.

**The fix.** `_TARGET_GATES` gained three library-search kinds — `basic_any` (basic land),
`basic_named` (basic Forest/Island/…), and `lib_type` (a named subtype: Equipment, Room,
Dragon, Plan, Halfling, or a land type where a shock counts as an Island card because the
match reads the TYPE LINE, not the name). `deck.dead_library_searches` is the zero-only
filter, and `check_all` runs it as a soft roster sweep — because the bug shipped precisely
BECAUSE nobody ran `targets` after the swap, which is the G-53 "capability that is never
reached" shape.

**Three constraints the build earned, each from something that went wrong:**

1. **ZERO-ONLY.** A thin count is an editorial judgement; an empty one is dead text. The
   roster measured 0 dead when written, so any hit is new rather than a backlog.
2. **SKIP THE SATURATING SEARCHES.** An unconditional "search your library for a card"
   (Lively Dirge, Servant of the Stinger, Hour of Victory) is always satisfiable, and the
   type-wide creature / land / artifact / nonland-permanent searches report "you have a
   deck" in a 60. Excluded by name — the same saturation rule that deleted the generic
   discard gate (G-66).
3. **DO NOT SKIP LANDS.** `target_counts` skips lands as gate sources by design, and that
   made the fetch-lands — Evolving Wilds, Terramorphic Expanse, Hobbit Hole, the exact
   place basic-fetching lives — structurally invisible. Caught by this module's own test,
   not by review. The fix immediately found two more dead searches.

**A fourth thing, caught by an existing gate.** The first `lib_type` pattern required a
capital-letter subtype to avoid matching "a card". It worked at runtime and `check_patterns`
failed it hard: that gate proves every pattern against the LOWERCASED corpus, where a
`[A-Z]` guard can never match. A pattern that is dead to its own gate is dead. Replaced
with a case-insensitive pattern plus the explicit exclusion list above.

**Read a hit as a claim about the SEARCH, not the CARD.** The first roster run found four:
The Masters of Evil in decks 20a/20b (searches for a Plan card; those decks run none — but
it is still a Villain anthem) and Hobbit Hole in 50a/69a (its basic-land fetch works fine;
only the Halflingcycling rider finds nothing).


## [G-76] A gate the deck meets for free is not a cost, and every model read it as one

G-66 gave the project `deck.py targets`, and its whole question is *"does this deck
CONTAIN N cards of shape X"*. All thirteen `_TARGET_GATES` entries count cards in the
list — MV caps, sacrifice fodder, graveyard types, library searches. That leaves a
second family of gated cards completely unmodelled: the ones gated on a **game state**
the deck has to reach. One 2026-08-24 session on deck 43 hit both ends of it.

**The dead end.** Ketramose, the New Dawn reads *"can't attack or block unless there are
seven or more cards in exile."* Deck 43 fielded three exile sources. The 4/4 menace
lifelink indestructible body was mostly a wall, and `targets` reported the deck clean —
its gate patterns read MV caps and sacrifice costs, not zone counts. That miss was
noticed by hand, in the same pass that noticed the card's *draw* trigger is ungated and
had exactly one repeatable enabler.

**The free end, which is the new thing.** Lake-town Toymaker reads *"At the beginning of
combat on your turn, if you've drawn two or more cards this turn, another target
creature you control gets +3/+0 and gains first strike."* Deck 43's entire second engine
is the "whenever you draw your second card each turn" cluster, turned on every turn by
Kitsa's free `{T}` loot. The condition is not a condition in that deck — the pump is
unconditional and repeatable. Every model here disagreed: `cuts` scored it **fit 17,
power 2, uniqueness 0, and no detected functional role at all**, `screen` called it
tangential on "Human, pump", and it was listed as a cut candidate in three consecutive
proposals before the user pushed back and it was re-read. The value was entirely in an
interaction between three other cards (the draw engine that frees the gate, the six
lifelink bodies that turn +3/+0 into +3 cards under Marina Vendrell's Grimoire, and Bard
the Bowman granting lifelink each turn), and a card-in-isolation grader cannot see any
of it.

So the fix reports **both ends** — `✗ CANNOT turn on`, `⚠ thin`, `✓ free`. That is the
asymmetry worth naming: every gate model in this repo asks whether a gate is DEAD and
none asks whether it is FREE, yet a free gate raises a card's grade exactly as much as a
dead one lowers it.

### What the measurement deleted

Six families were written. Four were removed after a sweep of all 116 decks, because
every instance returned the same verdict and a flag that never varies is not a flag —
the G-07 saturation lesson that already cost `suggest`'s Decks column and the `review`
audit flag.

| family | roster rows | counts | why dropped |
|---|---|---|---|
| lifegain | 10 | 10–18 | never below the band; a "gained life this turn" card is only played in a lifegain deck |
| artifacts | 9 | 8–9 vs a stated need of 3 | same structural reason |
| drain | 1 | 6 | not saturated — simply no evidence, and a band guessed off n=1 is a guess |
| delirium | 7 | 5–6 | **mis-proxied**, see below |

Delirium is the instructive failure. It is not merely saturated: the proxy measures the
wrong thing. The card asks for four card types **in your graveyard**, which depends on
self-mill and discard; counting types in the **deck** is an upper bound that any
60-card list clears by construction, since creature + instant + sorcery + land is
already four. Fixing it means modelling yard-fill, which is a different piece of work.
`descended` was never written at all — 11 pool cards and a condition nearly every deck
meets.

The temptation at this point is to lower a band until the saturated family varies. That
manufactures a signal instead of finding one, and the resulting flag is worse than no
flag because it looks like information.

### Live residuals

- The two shipped families are **n=4 and n=1** across the roster. The `draw` band
  (thin ≤2, free ≥8) is measured but thin evidence; treat it as provisional and
  re-measure when more gated cards enter the collection.
- The exile proxy counts anything that puts a card into exile, because the gate it feeds
  counts the **zone** and does not care who filled it. That is deliberately broader than
  Ketramose's own draw trigger, which fires only on exile from a graveyard or the
  battlefield. Two different questions about one card; conflating them is what made the
  deck 43 hand-count hard to reproduce.
- `_STATE_GATES` is registered in `check_patterns` so a pattern that silently matches
  nothing fails the build — without that, a dead state-gate pattern reads as "this deck
  has no gated cards", which is indistinguishable from a clean result. That is exactly
  how the digit-only descend gate hid for months.

## [G-77] An advisory you can only act on by a forbidden edit is a hazard

`section_mismatch` (G-05) does its job well: when a swap's added card inherits the cut
card's `# section` comment, it says so, and it stays quiet on ambiguous or absent
headers. What it did not do was give you any way to *act* on the warning. The card line
was already written at the cut card's position, so resolving the warning meant opening
the deck file and moving a line by hand.

G-65 forbids exactly that. Deck-line `(SET) COLLECTOR#` fields must come from
`deck.py resolve`, never be typed, because nothing else validates them: a wrong number
passes `legal`, passes `check` (ownership joins on the name), passes `preflight` READY
and passes `check_all`, leaving a deck file that is integrity-clean and un-importable at
once.

On 2026-08-24 the two rules collided. Eight swaps into deck 43, `section_mismatch` fired
four times, and each fix was a hand relocation of the line. Two of the four invented a
collector number — `(HOB) 26` for The Queen of Dale's real 24, `(HOB) 21` for Lake-town
Toymaker's real 19. Both were caught, but only because `deck.py resolve --check` was run
afterwards out of habit; nothing in the pipeline would have failed on them.

So the fix is `swap --section "<header substring>"`. It relocates the added line as part
of the same write, moving the line text verbatim so the printing fields cannot be
retyped, and it validates the header *before* writing — an absent or ambiguous substring
aborts the swap entirely rather than leaving a misfiled line with an error printed after
the fact. The advisory now names the flag.

The transferable rule: **when a warning's only remedy is a manual edit of a file the
project's own rules say never to edit manually, the tool owes you the mechanical form of
that edit.** A warning that pushes the reader toward a forbidden operation is worse than
silence, because it produces a second, quieter error class while looking like diligence.

### Design notes

- Ambiguity refuses rather than guessing. Filing a card under a header the author did
  not choose is the same lie the warning is about, one step removed.
- Relocation runs inside the existing `try` and before `_safe_write_lines`, so the
  card-total guard still applies. A move preserves the total by construction.
- A card already in the target section is a no-op, so the flag is safe to pass
  speculatively.

**The standalone form, 2026-08-27: `deck.py move <id> "<card>" --section "<hdr>" --apply`.**
`swap --section` only covers relocation while a swap is happening; fixing a section noticed
AFTER the write took a swap-out/swap-in pair, and that pair is recorded to
recommendations.csv as if each half were a decision — one session left four such rows,
including `cuts ranked −Dracogenesis 1/30` for a card that had been added minutes earlier
(the ranking was "keep it", read back as a disagreement about a cut nobody proposed). The
rows were pruned with a `.bak`, and `move` writes no ledger row at all: a relocation is not
a decision, which is G-56's line applied one command over. Same `_relocate_card_line`
machinery, same verbatim-line guarantee, same refuse-ambiguous-headers-before-writing.

## [G-78] A sharing claim is not a comparison, and short card names are invisible

Two findings from one investigation, and the residual is larger than the fix.

### The fix

`_cites_as_history` suppresses a card citation when the surrounding clause names another
deck, on the reasoning that a distinctness passage cites another deck's cards to contrast
with them. That is right for *"where deck 42 spends its splash on two one-shot ETB
thefts"* and wrong for *"only FIVE nonland cards are shared (Erode, Healer's Hawk, …)"* —
because a **sharing** claim asserts the named cards are in **this** deck too. It is a
statement about the current list wearing the grammar of a comparison.

Deck 43's tier block carried such a list naming a card the deck had not run in a long
time. A narrow `_SHARING_CUES` carve-out (`share`/`shared`/`sharing`/`in common`/`both
run`/`both play`/`overlap`) skips the other-deck suppression inside those clauses only;
every other cross-deck citation suppresses exactly as before. The roster sweep returned
zero new hits, and a control test pins that an ordinary comparison still suppresses —
without it the carve-out would simply be a disabled suppression.

### The residual, measured

The carve-out did **not** catch the deck 43 instance that started this. That prose wrote
*"against 42 Blood Price"* rather than *"deck 42"*, so `_OTHER_DECK_RE` never fired; the
real suppressor was `_RATIONALE_MIN_LEN = 9`, which skips any single-word card name
shorter than nine characters. `Erode` is five.

Lowering the floor was tried and measured across the whole roster:

| floor | hits | real | false |
|---|---|---|---|
| 9 (current) | 0 | 0 | 0 |
| 7 | 5 | 3 | 2 |
| 5 | 7 | 3 | 4 |

The three real ones were found and fixed on discovery: deck 43's archetype prose still
listed **Wolfbat** as a live member of its second-card cluster after it was cut, and deck
42a's tier and archetype prose both cited **Ahriman** as an active engine piece — a card
42a does not run.

The false positives are structural, not tuning noise. `Pacifism` sits next to the word
"over" ("+Summon: Bahamut over Pacifism"), and a bare "over" is deliberately excluded
from the history cues because it is the house phrasing for a quality vector ("card
advantage 9 over a 2.86 curve"). `Impulse` is a mechanic name capitalized at a sentence
start, which defeats the case-sensitivity rule that keeps ordinary vocabulary out.
`Rescue` matches inside *"Kona Rescue Beastie"* — the prose drops the comma the real card
name has, so masking by exact in-deck name does not blank it.

Either rate would put permanent false warnings into `check_all`'s soft output on every
run, and the audit's own design note is explicit that a noisy audit gets ignored, which
is worse than no audit. **The floor stays at 9.** Short single-word card citations are a
known blind spot; re-measure before changing it, and expect to fix the sentence-start and
punctuation-variant cases first if you want the floor to come down.

## [G-79] A previewed set is in Scryfall months before you can play it

`build_pool.py` fetches with `unique=cards`, which returns exactly one printing per card
— the newest. Scryfall indexes previewed cards the moment they are spoiled, weeks or
months ahead of release. Put those together and a reprint in a spoiled set silently
becomes the **only** printing the repo holds.

Measured on 2026-08-24, with Star Trek (TRK) dated three months out:

```
q = game:arena legal:standard !"Watery Grave", unique=cards
  → TRK 306, released 2026-11-13
  discarded: EOE 261 (2025-08-01), GRN 259 (2018-10-05)
```

That matters because `deck.py resolve` is the *mandated* source of deck-line printings
(G-65) — you are explicitly told never to hand-write one. So the pool's choice propagated:

- **114 pool rows** carried a future release date (TRK 91, FRA 20, MBC 3).
- **109 deck lines across 47 files** named an unreleased set — 33 shocklands and 76
  basics.
- **Two round-tripped into ownership.** A deck line went into an Arena export, came back
  through `import_arena` (which correctly records the set code it is given), and
  `card-library.csv` then listed Overgrown Tomb and Watery Grave as owned *in TRK*. Since
  `_printing_index` prefers an owned printing, those two kept resolving to TRK even after
  the pool was fixed — the corruption outlived its cause.

None of it was catchable by the existing gates. `resolve --check` passes a real set with a
real collector number, because the line is structurally valid; it is simply not importable
yet. `check_all`'s INV-04 found the set code present in the library. The deck files were
integrity-clean and un-importable at once, which is exactly the shape G-65 exists for, one
layer out.

### The fix, and the trap inside the obvious version

`date<=now` on both default queries. The literal token `now` is load-bearing, and this is
the part worth remembering: `build_pool` gates its freshness reuse on
`stamp_query == query`, so a query string carrying today's formatted date would differ on
every run, never match the stamp, and force a full ~4-minute refetch on every
`make refresh`. A correctness fix would have become a permanent tax — and a cost paid
every cycle is one an operator learns to wave through, the same failure K-01 records for
standing warnings nobody acts on. Verified that Scryfall accepts `now`; `-is:future` and
`not:future` were tested and do **not** work.

A caller-supplied `--query` is deliberately not rewritten. It is an explicit request for a
scope, and silently editing it would defeat the reason to pass one.

Impact of the rebuild: `game:arena` 16,067 → 15,973. 94 genuinely-unreleased cards
dropped, ~20 reprints re-picked to their newest *released* printing.

### The repair half, and why it had to exist

Fixing 109 lines by hand is the operation G-77 was written about — relocating four lines
by hand in one session invented two collector numbers. So `resolve --fix <deck>` rewrites
only the printing fields, carrying the quantity, name and any trailing comment over
verbatim; dry-run by default, and `--apply` goes through `_safe_write_lines` so the INV-04
parse and copy-count guard both run.

Two details it needed:

- **Keyed on (name, set, collector), not name.** A card legitimately listed under two
  printings must not have its good line rewritten because its bad twin matched.
- **Basics are included, for the set code only.** `printing_problems` exempts basics
  correctly — Arena prints several arts per set and the pool carries one — but a basic
  whose set code exists *nowhere* is equally unimportable, and 76 of the 109 lines were
  exactly that: invisible to the check meant to catch them.

A third detail was a real bug the new tests caught: the rewrite loop matched `LINE_RE`
against the raw line, and since that pattern anchors on `$`, a trailing `# comment`
swallowed the printing into the name group and the line silently failed to match. Every
other line-rewriting site here strips the comment first; this one now does too.

### Backstop and residual

`check_all` gained a soft sweep reporting unreleased rows in the pool. It is deliberately
**pool-level** rather than a flag threaded through the five craft-recommending surfaces:
the exposure is a property of the file, so one report covers `suggest` (and its
`--lands`/`--ramp`/`--interaction` siblings), `tier --to`'s craft fillers and
`wishlist --rank/--budget` at once — and being report-only it re-ranks nothing, so no
K-12 roster diff was needed.

**Live residual:** `Released` is still consumed in only one direction everywhere else —
`rotation_risk` and the ⚠rot flags, which answer *when does this leave Standard*. No
per-card surface asks *is this out yet*. A pool built with a custom `--query`, or one
built before this bound existed, re-opens the whole failure; the soft sweep is what tells
you.

## [G-80] A card that grants a keyword is a card about that keyword

The tagger's keyword tags came from Scryfall's `keywords` field — what a card **has**.
Nothing read what a card **gives**. So a lord handing the whole team deathtouch carried no
`deathtouch` tag, and every model downstream of the tags saw a card with nothing to do with
the deck built around exactly that.

**The distribution is why this mattered rather than being a tidy-up.** Across
`card-pool.csv`, **1,941 cards grant one of the twelve evergreen keywords**, and for four of
them the granted case is the *majority*:

| keyword          | granted | native |
|------------------|--------:|-------:|
| haste            |     366 |    359 |
| trample          |     314 |    545 |
| flying           |     301 |   1657 |
| **indestructible**|    224 |     83 |
| vigilance        |     185 |    455 |
| lifelink         |     177 |    294 |
| **first strike** |     172 |    145 |
| **hexproof**     |     151 |     56 |
| deathtouch       |     130 |    255 |
| menace           |     126 |    290 |
| **double strike**|     112 |     75 |
| reach            |      53 |    304 |

For indestructible and hexproof the tag was tracking the *exception*. A deck built on
handing out hexproof was, to the tagger, a deck with no hexproof in it.

**How it surfaced: the user caught it, no gate could.** Deck 31 (Golgari deathtouch-poison)
was offered Venom Connoisseur as a cut candidate — a card whose entire text is about the
deck's central mechanic. The user said "Venom Connoisseur should not be a suggested cut.
Re-read it, and if you agree, then why was it suggested?" They were right, and the answer
was upstream of the cut ranking: `cut_keep_score`'s fit term is gated on derived tags, so it
inherited the tagger's hole. Fit went **17 → 68** once grants were read, and Maximum
Overdrive **4 → 57**. This is K-04 one layer over — that rule says never gate a predicate on
a derived tag; this is what it costs when you do.

**The fix reads TEXT, with three exclusions taken from the failure modes, not invented.**
`granted_keywords()` strips reminder text first (every keyword's own reminder names the
keyword), then requires a gain/have/get verb within a bounded window, then drops the clause
if it is scoped to an OPPONENT (`opponent`, `creatures you don't control`) or is a LOSS
(`loses`, `can't have`) — a card that strips flying from their team is not a flying card.

**The K-14 diff is the part worth carrying forward, and it is a NEGATIVE result.** Tags feed
`cuts`, `suggest` and theme centrality. They do **not** feed the tier floor: `tier_band`
grades on `role_tally`, which reads oracle text directly. So a change touching 1,941 pool
cards moved **0 decks, 0 tier floors and 0 role counts**. Measure both halves before
believing a tagger change is either safe or significant — this one was large in the
recommenders and inert in the grading, and the two are easy to confuse.

**The side effect that needed a human.** More tags raised the dominant theme's card count,
and `_central_themes` admits a theme at 25% of that count — so the floor rose and four decks'
quoted "N central themes" figures went stale by arithmetic. Three were mechanical
corrections. Deck 35's was not: its `#: tier:` argued its B **from** the figure ("a scattered
plan (20 central themes)"), and the live number is 13. The figure was corrected, the now-weaker
argument recorded in place, and the **letter left alone** — a tier letter is a human call.
**A tagger change that moves a centrality floor moves every prose figure derived from it**,
and nothing sweeps deck prose for arithmetic that was true when written.
