# Handoff — start the next session here

Rewritten 2026-08-09 after the **broad-scan-3** cycle closed, updated 2026-08-12 for the
**broad-scan-4** cycle, refreshed 2026-08-19, and again 2026-08-24 (**§0-current is the
current state and supersedes anything under it where they disagree**; the numbered sections below it are
dated records, kept because their reasoning is still worth reading). Written for a session with none of this one's context. Read it before
CLAUDE.md's Common Gotchas, not instead of them. The broad-scan-2 cycle it previously
described is in `.cycle/blocks/2026-08-broad-scan2-*.md` if you need it.

**Read the evidence file when a rule's reasoning matters.** CLAUDE.md carries the RULE and
any live residual; the incident and measurement live under the anchor the rule ends with —
`[G-nn]` / `[K-nn]` in `docs/gotchas.md`, `[C-nn]` in `docs/cycle-config.md`. Nothing was
deleted; open the long form before deciding a rule looks arbitrary.

**Also live: `docs/systems-map.md`** — which command answers a question, and why two
commands disagree.

---

## 0-current. THE 2026-08-24 SESSION (READ THIS FIRST — supersedes §0-latest below)

> **STATE STAMP, 2026-09-03.** Broad scan #8 is MERGED as PR #163 — eight commits: seven
> implementation batches, a deck re-grade pass and two doc syncs. `main` is the place to
> branch from. Live gates: `check_all` all invariants hold with the SAME one soft warning
> described below (the four accepted dead tutors); **1658 pytest passed / 0 skipped**.
> What changed, in one line each: colour sources are read from land TEXT through one
> primitive (any-colour lands were zero sources); the role classifier no longer counts
> blink as removal or reads reminder text; the tier floor's thresholds were re-derived
> from the roster (they had saturated at A for 104 of 117 decks) and a spread sweep
> watches for it happening again; 60-card Brawl resolves to Standard's legality key;
> rotation uses the Standard year; the editor's save gates equal `check_all`'s and the
> CSV save carries a staleness token; INV-01b rejects a library printing that exists
> nowhere; hand-logged matches no longer advance the ingest watermark; and
> `check_commands` covers Makefile targets. Full detail per batch in `.cycle/blocks/`
> (five new blocks, newest `2026-09-broad-scan-8-batch6-7-*`). Open residuals worth
> knowing before you start: the LIBRARY still carries stale `sacrifice`/`ramp` tags
> because `--merge` cannot remove one (the pool is corrected); five Low interface items
> P-09..P-13; and Regression Scenarios 12–18 are written but unwalked.
>
> **STATE STAMP, 2026-09-02.** Everything through 2026-09-02 is MERGED to `main` as PR
> #162 — deck 78's craft ingest, Niko into deck 27, both tooling batches, the ten logged
> matches, deck 40a's rename and the doc sync. `main` is the place to branch from. (This
> paragraph spent part of the day warning that eight commits sat unmerged with no PR; it
> is kept in this shape as the reminder that the branch state is the first thing a
> resuming session cannot see and the first thing this file has to tell it.)
>
> The rules and reasoning in this section are all still current; only its FIGURES had
> aged. Live gates: `check_all` all invariants hold with the SAME one soft warning
> described just below; **1572 pytest passed / 0 skipped**. Five cycles have run since
> this section was written — the granted-keyword tagger fix, the match-ingest watermark,
> the skill-layer sweep, the `--sync-names` dry-run fix, and (2026-09-01/02) the
> role-verb / wishlist-target / deck-id batch and the granted-non-evergreen /
> manabase-figure batch — each with its own verbatim block in `.cycle/blocks/` (newest:
> `2026-09-granted-keywords-and-manabase-figures-broad-implement.md`). Read those for what
> changed; read this section for why the rules below exist. The figures in the paragraph
> that follows are the 2026-08-24 snapshot and are kept as a dated record.

Gates: `check_all` all invariants hold with **ONE soft warning** (see below — it is
expected, not a regression); **1423 pytest passed / 1 skipped**. Merged as PR #150 and
#151. §0-latest's "ZERO soft warnings / 1333 tests" is the 2026-08-19 state.

**The one soft warning is the G-75 sweep reporting four ACCEPTED dead tutors** — The
Masters of Evil in decks 20a/20b (needs Plan cards, deck holds 0) and Hobbit Hole in
50a/69a (its Halflingcycling rider finds nothing). Both cards are still worth their slot;
the SEARCH is dead, not the card. Do not "fix" these by editing decks — the flag is doing
its job. A FIFTH hit would be new and worth reading.

### Four rules landed, and one of them came from a real game

- **G-75 dead library searches.** Deck 76 ran ZERO basics while TWO cards searched for
  them; the user found it IN PLAY, no gate could see it, and the second card had been
  added the day before *on the fetched basics as its stated rationale*. `deck.py targets`
  counts library searches now and `check_all` sweeps the zero case.
- **G-76 state gates — report the FREE end, not just the dead one.** All 13
  `_TARGET_GATES` count cards in the LIST, so a card gated on a GAME STATE was invisible
  both ways. Ketramose needs 7 cards in exile against 3 sources; Lake-town Toymaker needs
  "drawn two or more cards this turn" in the deck that draws two every turn, so its pump
  is UNCONDITIONAL — and it scored fit 17 / power 2 / uniqueness 0 / **no detected role**
  and was three proposals from being cut. **Only 2 of 6 families shipped**; four were
  measured across the roster and deleted as saturated, delirium because its proxy counted
  types in the DECK when the card asks about the GRAVEYARD.
- **G-77 `swap --section`.** G-05's advisory could only be acted on by hand-editing a deck
  line, which G-65 forbids — and doing it four times in one session invented two collector
  numbers. Pass `--section "<header>"` in the same swap; never hand-move a card line.
- **G-78 sharing claims + a MEASURED residual.** A "cards shared with deck N" clause
  asserts the card is in THIS deck, so the cross-deck suppression was wrong there.
  **The residual is bigger than the fix and is settled, do not re-litigate it without new
  measurements:** `_RATIONALE_MIN_LEN = 9` hides every single-word card name shorter than
  nine characters, which is what actually hid the bug. Lowering to 7 gives 3 real / 2
  false roster-wide, to 5 gives 3 real / 4 false; both would put permanent false warnings
  in `check_all`. The floor STAYS at 9. Three real citations were found and fixed on the
  way (43 Wolfbat, 42a Ahriman ×2).

### CLOSED, and it was still open in this file for a week: the TRK printing question

**This section used to read "UNRESOLVED AND RECORDED NOWHERE ELSE" and tell you to go
paste-test a deck in Arena. Do not. The work landed in this same cycle** — commit
`e269b5e`, "Ingest: keep UNRELEASED printings out of the pool, and repair the 109 lines
(G-79)" — which went in AFTER `00a6975` wrote this handoff, and nobody came back to the
handoff. Verified 2026-08-24 (broad-scan S1-01):

    (TRK) lines under decks/      : 0        (was 109 across 47 files)
    TRK rows in card-library.csv  : 0        (was 2 — Watery Grave, Overgrown Tomb)
    future-dated card-pool.csv rows: 0       (was 114)

The cause is worth keeping, because the RESIDUAL is real: Scryfall indexes spoiled cards
immediately and `unique=cards` returns the NEWEST printing, so a reprint in an unreleased
set becomes the only printing the pool holds — and `deck.py resolve`, the mandated source
of deck-line printings (G-65), then emits it. `build_pool`'s defaults now carry the
literal token `date<=now` (load-bearing as the token, not a formatted date, or the
freshness reuse refetches daily), `resolve --fix <deck> --apply` is the repair half, and a
`check_all` soft sweep watches the pool. **A custom `--query` is NOT rewritten**, so a
hand-built pool can re-open this. That is G-79; read it there, not here.

**THE TRANSFERABLE LESSON, which is why this section is being kept rather than deleted.**
This file is the one CLAUDE.md orders a fresh session to read FIRST and declares
authoritative ("supersedes anything under it where they disagree"). So a stale open item
here does not merely fail to help — it actively spends the next session's first hour on
finished work, with the full authority of the handoff behind it. The project already
knows that *a handoff nobody is told to read is invisible*; the mirror is that **a handoff
that IS read and is wrong is worse than one that is not read.** When work closes an item
named in §0-current, close it HERE in the same commit. `docs/verify-commit-tail.md` is the
shared tail every writing skill ends with, and it now says so.

**That last sentence was itself the wrong-handoff shape, corrected 2026-08-26.** It was
true of the DOCUMENT and false of the SKILLS: the tail said so, and only 5 of 12 skills
cited it. `/ingest` and `/refresh` rewrite `card-library.csv` and every derived file and
had no commit step at all, so neither ever reached step 4 — the step this very paragraph
argues for. `/add-deck` carried its own one-line commit instruction. All three cite the
tail now, and its header carries the enumerated list of writers plus the rule that a new
writing skill must be added there AND cite the file from itself in the same change.
Nothing enforces that mechanically: `check_commands.py` proves a command is REACHED, not
that the skill reaching it is right. The lesson generalizes past this file — **a
"standardized" ending is standard only over the callers that say they use it**, and
"and any future data-editing skill" was doing no work at all.

### Deck work this session (all merged)

- **Deck 43 Overdraft — ten swaps**, the HOB pass plus two correctives. Final: interaction
  4, card advantage 15, avg MV 3.17, floor **B = claimed B**, preflight READY. Two
  uncommon crafts owed (Bard the Bowman, Lake-town Toymaker), both wishlisted.
- **The mechanic worth not re-deriving:** Doctor Octopus and The Ten Rings each SET a
  maximum hand size (8 / 10). A set is a FLOOR as well as a ceiling — the end step
  precedes cleanup, so the trigger draws you UP and cleanup discards you DOWN, leaving the
  hand at exactly N every turn. Under Marina Vendrell's Grimoire hand size IS life, so
  that is a per-turn life reset. **Both cards were cut on the opposite reading and
  restored the same day.** Costs: burst beats a fixed 8, and Ms. Marvel's clock is capped.
  Two setters do NOT stack — land The Ten Rings after Doc Ock to keep the 10.
- **Deck 43's path to the A floor is ONE CARD**, measured: `+1 interaction (4→5)`, card
  advantage already 15. Adding Makeshift Binding / Erode / Negate over a non-interaction
  cut each lands the floor on A (tested, then reverted). The user chose to leave it as is
  for now. Note `tier --to`'s own plan proposes cutting Bitter Triumph, which IS
  interaction, and flags that itself — read its add list as "cheap", not "good".

### Where the session left off

**REWRITTEN 2026-09-02 — the paragraph this replaces said "Nothing in flight. Working tree
clean, HEAD == origin/main", which stopped being true and is exactly the failure the
commit tail's §4 warns about: a handoff that IS read and is wrong is worse than one that
is not read.**

**Working tree clean, everything merged to `main`.** PR #162 carried the day's eight
commits: deck 78's craft ingest, Niko into deck 27, the granted-non-evergreen-keywords +
manabase-figure-axis batch (block in `.cycle/blocks/`), ten Arena matches, deck 40a's
rename and file rename, this handoff, and the doc sync. PRs #160 and #161 (deck 78's
tuning and its doubler/manabase pass) landed earlier the same day. Nothing is in flight.

**Deck 78 "Team Avatar" is the live deck.** Built and tuned from scratch 2026-08-31 →
09-02, fully buildable, preflight READY, floor A on a **claimed B that is still marked
PROVISIONAL** — that is a pending HUMAN call (never auto-write a tier letter), and the
first evidence is now in: **5-2 across its first seven games**, n=7 against the 20-match
floor, so it is encouraging and not yet a reading. Two swaps were measured and offered and
have no decision: `−Sheriff of Safe Passage / +Ojer Taq` and `−Kyoshi Warriors / +Byrke`.

**One find from 2026-09-02 worth not re-deriving.** Deck 78's `#: notes:` claimed Starfield
Vocalist saw four noncreature permanents while naming two lands (Birnin Zana Plaza, Temple
of Enlightenment) that the same day's manabase rebuild had already removed — and their
replacements (Gathering Place, Urban Retreat) have no triggered ability at all, so the
real count is TWO. Corrected in the deck file with the reasoning. The general shape:
**a manabase swap can quietly cut a doubler's fodder, and no gate sees it** — G-27 keeps
`#: notes:` out of the staleness scan on purpose, because a build log may legitimately
name an absent card.

`.cycle/team-avatar-pile-analysis.md` was DELETED 2026-09-02, its contract satisfied — the
swaps landed and its findings are folded into deck 78's 57 `#: notes:` lines. The other
three working docs (prune, wylie-tap, hob-followup) are still live and still awaiting the
user's calls. Standing items the user has explicitly deferred: the Endstone shell, Wylie
Variant B, the Army/amass deck, 26a near-mono-blue rebuild, deck 76 second-wave crafts, and
the unexamined fit-pass leads (Innocuous Rat → 62, Graveshifter → 77, Carrot Cake → 42a,
Fanatic of the Harrowing → 70, six deck 31 suitors). Deck 8 still carries a pre-existing
pip-intensive flag (16 B / 1 R / 3 G against thin R–G splashes) — noted, never actioned.

**Two open design calls carried forward from the 2026-09 blocks, neither a defect:**
`--audit-targets` checks wishlist→deck and nothing checks deck→wishlist (272 deck craft
targets are outside the 186-row wishlist, which is CURATED — whether that view should
exist is the user's call); and the colour-source computation exists three times
(`cmd_mana`, `cmd_consistency`, `deck_color_sources`) and agrees today with nothing
checking that it keeps agreeing.

---

## 0-pre. TWELVE DECKS WERE RENAMED on 2026-08-14 — read this before searching by name

The repo adopted MTG Arena's own deck names via `parse_matches.py --sync-names`. **Older
notes in this file, in `.cycle/STATE.md` and in `.cycle/blocks/` still use the OLD names**
— those are dated records and were deliberately left alone. Match on the deck NUMBER, not
the name, when following an older note.

| # | was | now |  | # | was | now |
|---|---|---|---|---|---|---|
| 19 | Bird Brain | Bird Brain — Bant | | 51 | Unlock | Unlocked |
| 26b | Iron Forge — Scrapyard Tithe | Iron Forge — Ancient Decay | | 52a | Void Demons — Dark Realms | Void Demons — Void Realm |
| 28 | Dino Stampede | Triceraton | | 56a | One Fell Swoop — Overgrowth | One Fell Swoop — Executioner's Song |
| 45 | Exile Dividend | The Exiles | | 57 | Jeskai Tempest | Tempest |
| 48 | Doombot Array | Doombots | | 58 | Gold Standard | Treasure Planet |
| 49 | Scaleforge | Big Draco | | 59 | Stampede Engine | Stampede |

Four variants were then renamed BY HAND to keep the `<parent> — <variant>` convention
(28a, 45a, 48a, 51a); the tool flags those but cannot compose the new name. Three prose
citations in other decks were repointed. **The divergence regrows** — it comes from how
decks are named in the client — so re-run `--sync-names` (it is opt-in and reports without
the flag) rather than assuming the two sides still agree.

**EIGHT DIRECTORY SLUGS MOVED WITH THEM**, so an older note's PATH will 404 even when its
deck number is right. Deck ids come from the leading number, so nothing broke:

    28-dinosaurs -> 28-triceraton          51-unlock          -> 51-unlocked
    45-exile-dividend -> 45-the-exiles     57-jeskai-tempest  -> 57-tempest
    48-doombot-array -> 48-doombots        58-gold-standard   -> 58-treasure-planet
    49-scaleforge -> 49-big-draco          59-stampede-engine -> 59-stampede

Plus three variant FILES: `26b-scrapyard-tithe` → `26b-ancient-decay`, `52a-dark-realms`
→ `52a-void-realm`, `56a-gruul` → `56a-executioners-song`. Resolve any path through
`deck.py`/`discover_decks`, never by typing a slug from an old note.

---

## 0-latest. BROAD SCAN #6 — the top 5 landed 2026-08-19 (superseded by §0-current)

**Supersedes §0-newest below where they disagree.** Gates: all invariants hold with **ZERO
soft warnings**; **1333 pytest passed / 1 skipped**. Full block:
`.cycle/blocks/2026-08-broad-scan6-top5-broad-implement.md`.

### Landed
- **Four removal templatings now score interaction** (they scored ZERO): the removal AURA
  (`enchanted creature gets -N/-N` — Dead Weight, Debilitating Injury, Mire's Grasp, 20 cards)
  and three coordinated-qualifier shapes the two-adjective run could not reach (11 cards).
  **K-14 roster diff: 0 decks moved, 0 tier floors moved** — no deck runs one of the 29, so the
  value is entirely in the recommender's candidate set.
- **Ownership now resolves a FRONT name against a FULL-name library row.** `lib.owned_qty` only
  ever went full → front; 8 rows are stored under the full `A // B` name, so `deck.owned` said
  "NOT IN LIBRARY" for an owned card. Aliased in all four library-side builders
  (`deck.load_collection`, `pool.owned_counts`, `card._owned_index`; `wishlist.owned_index`
  already had it) via `lib.alias_front`.
- **CLAUDE.md's "the library stores the front only" is corrected** — it is false for those 8
  rows, and README had it right the whole time.
- Dashboard mana tokens got **light-mode values** (they were pastel-on-near-white in the deck
  detail's colour bars); `attachHover` takes an explicit **focus host**, so the card preview
  follows focus on all three surfaces instead of one; **deck 73's six hand-written collector
  numbers** were replaced with resolved ones.

### The open item this created, and it is a real decision
**The TAXONOMY half of the classifier hole was deliberately not taken.** 128 pool cards
neutralize rather than destroy — 83 "doesn't untap during its controller's untap step"
(tap-down), 45 "loses all abilities" — and carry no interaction role. **Six decks under-count
interaction today**: 15 by 2; 16, 27, 32, 38a, 38 by 1. None crosses a band right now, but
**deck 38 sits at interaction 3, exactly the B floor**, so one more cut on that axis grades it
wrong in the other direction. This is the same shape as the Equipment-bucket question already
on the list (§0-newest item 5): adding a bucket re-scores every deck running the type, so take
it deliberately with a K-14 diff, not as a pattern slip-in.

### Two gate gaps worth closing before they produce the next instance
- `check_dfc`'s registry-completeness scan only walks builders that read **card-pool.csv**.
  Every ownership index reads card-library.csv, which is why BS6-01 was invisible to it.
- `check_agreement`'s ownership pair compares `lib.owned_qty` against `deck.owned` — which
  agreed on the same WRONG answer. A pair whose two sides share a primitive can only catch
  divergence, never a shared blind spot; that is worth remembering when registering the next one.

### Two operator checks are outstanding (a file cannot prove either)
- **Scenario 5, extended:** dashboard in light mode → a deck's Stats "Color identity" bars and
  Mana "Strict color requirements" bars must be visible against their track.
- **Scenario 7, extended:** Tab to a card name in the roster CRAFT-PLAN table and in the IMPACT
  grid — the card image must appear on focus, as it already does for a wishlist name. Re-check
  the craft table after clicking a sort header.

---

## 0-newest. THE 2026-08-16 → 2026-08-19 SESSIONS (superseded by §0-current)

**Everything below this section predates 2026-08-16.** §0-now's "Library 2254 → 2275
printings" is four days stale: the roster is now **2362 cards / 113 decks** (the
session-start hook prints the live figures — trust it, not any number written here).

### What landed

- **Two ingests** (36 cards, then 24) plus a run of one-off ownership corrections the
  user supplied as they were noticed: Watery Grave, Hobbit Hole, Explosive Derailment ×2,
  Great Train Heist, Nexus of Becoming, Racers' Scoreboard ×2, Krang & Shredder.
- **The 37 Wizard family (37 / 37a / 37b) was tuned hard** off a user observation that
  turned out to be the right diagnosis: the payoffs split into "noncreature spell"
  triggers (17 feeders) and "instant or sorcery" triggers (only 10), and the latter was
  the starved half. Roughly a dozen swaps followed, the manabases went 9 → 6/7 tapped
  lands, and **37a was re-graded B → A at the user's call** (never auto-write a letter).
- **Eagle package** placed into 19 / 19b / 67; **landfall / land-puller** work across
  19, 19b, 40a, 50a (sac-fetch lands, Bonny Pall, Seedship Agrarian, Loot).
- **Artifact family** 26 / 26a / 26b / 48: Simulacrum Synthesizer placement, Lady Octopus
  top-end for 26b, manabase audits (26a 23 → 24 lands, 48 Mountain → Island).
- **`reconcile_crafts.py` write bug FIXED** — it reported before writing, so
  `--apply | head -6` died on BrokenPipeError having printed a success summary and
  written nothing. Two real batches were lost that way, each found only because the user
  re-grepped the library, and `check_all` could not see it. Writes now precede the
  report; pinned by a test that fails against the unfixed source. Rule is G-10.
- **A `/sync-docs` pass**, then **four `_ROLE_PATTERNS` whitelist holes closed** — see
  the G-67 section of `docs/gotchas.md` for the measurements. The big one: the anthem
  pattern hard-coded the noun `creatures`, so every tribal lord (146 cards) scored no
  anthem role, invisible because anthem is not an axis `tier_band` grades.

### State you should verify rather than assume

- **PRs #136 and #137 are merged. Commit `b6ff446` (the role-pattern work) is pushed to
  `claude/magic-deck-swaps-b1h3no` but NOT merged** — no PR was opened for it, because
  the user asks for PRs explicitly and had not for that one. Check `git log
  origin/main..HEAD` before assuming the branch is clean, and per CLAUDE.md restart the
  branch from `origin/main` if its PR turns out to have been squash-merged.
- `check_all` is green with **one** soft warning (6 unverified printings, all deck 73).
  It was three earlier in the cycle; do not read the drop as a regression in the gate.

### Open items, in the order they are worth picking up

1. **`.cycle/prune-analysis.md` — the largest outstanding item, and it is BLOCKED ON THE
   USER, not on analysis.** The roster is at 113 decks against Arena's 100-deck cap. The
   doc carries the finished work — card-overlap matrix, `similar` sweep, playstyle belts,
   a three-tier candidate list — and is waiting on keep/cut calls. Do not re-derive it.
2. **Ownership drift — the two KNOWN cards are cleared, the CLASS is not.** Cool but Rude
   and Captain Howler, Sea Scourge were reconciled on 2026-08-19 and 26b now checks
   fully buildable. But every one of the ~10 corrections this stretch was found the same
   way — **the user noticed**, not a gate — so the honest read is that the library is
   still drifted in places nobody has looked. `import_collection.py` against a tracker
   export is the only tool that sets counts EXACTLY (including DOWN, which
   `import_arena.py` cannot by construction) and would settle the whole class at once.
   Worth doing before any wildcard-spending pass, since ownership is the premise most
   likely to be false (G-10).
3. **Craft options named but not taken** (information, not a budget — per the Player
   Profile, never gate a card on ownership): Undergrowth Recon (best home is now 50a),
   Steam Vents (serves 26 / 26a / 26b / 48), Icetill Explorer, Forensic Gadgeteer,
   Mystical Teachings, Fabled Passage.
4. **Parked cards, with the condition that would un-park them recorded** — Thranduil
   needs a BGU Elf shell; Double Down needs NONLEGENDARY outlaws in blue (the legend rule
   kills the copies, which is why 44/44a were rejected); a second Simulacrum Synthesizer
   is not needed because copies are fungible across decks.
5. **A taxonomy question the role-pattern pass deliberately did not answer.** 11 of the
   26 remaining zero-role cards are **Equipment** (attach / equip / hone counters), a
   class `_ROLE_PATTERNS` has no bucket for; tap-down, extra-combat, taxing and hand
   attack are in the same position. Adding a bucket re-scores every deck running the
   type, so it is a decision to take deliberately, not a pattern fix to slip in.
6. **Wylie Variant B** (mono-W tap-down control) remains specced-but-undrafted in
   `.cycle/wylie-tap-analysis.md`; Variant C parked.
7. Noted in passing: **26a's own file flags that a near-mono-blue rebuild would eliminate
   its mana problems** — a real option nobody has priced.

### Traps this stretch re-confirmed

- **A stale `#: tier:` figure is created BY a successful tune.** Moving a graded axis
  makes the prose citing it wrong; `tier <id> --audit-rationale` catches it and the
  roster sweep in `check_all` is the backstop. Two figures went stale on 2026-08-19 from
  a pattern change alone — the deck files were not even edited.
- **Write a test fixture from the card's REAL text.** A paraphrased Blur of Blades
  fixture passed a pattern that the real card refutes — G-67's stated trap, hit live.
- The user corrects card assessments and is usually right (Lasting Tarfire, Super
  Intelligence, Cornered by Black Mages, Mona Lisa were all defended successfully).
  Re-derive from oracle text before holding a position.

---

## 0-now. THE 2026-08-15 SESSION (superseded by §0-newest above)

**Landed:** a 17-card HOB ingest, four swaps applied, five flex lines added, and the
match-log tooling batch (findings 1–4) that preceded them. Library 2254 → 2275 printings.

- **Ingest (17, all new).** Routed crafted/opened → `reconcile_crafts.py`, 1 copy each.
  Two names had to be corrected before the paste would parse and BOTH are the shape that
  silently loses a card: "Misty mountain raider" is **Misty MountainS Raider** (plural),
  and "Down, down to goblin-" was truncated mid-name. `deck.py resolve` reported the
  first as not-found rather than guessing — trust that refusal.
- **Swaps applied:** 39 −The Last Agni Kai +Chainsaw · 29a −Bombard +The Mountain-king's
  Return · 54a −Loki Laufeyson +Bilbo, Thief in the Night · 19 −Dazzling Denial +Bard,
  King of Dale. All four preflight READY, all four rationales re-grounded.
- **DECK 19'S OPEN RE-GRADE IS CLOSED, and not the way it was leaning.** It had been
  flagged possibly UNDER-graded since 2026-08-09 (floor A, letter held at B pending a
  human call). The swap moved interaction 5 → 4 and card advantage 2 → 3, so the floor is
  now B and matches the letter. Do not re-open it as an under-grade. **Watch interaction
  4** — one more cut on that axis and the floor drops BELOW the claimed B.
- **Open, parked in the decks' own flex blocks** (so they cannot be lost): Bolg of the
  North → 55, Down Down to Goblin-town → 42a, Gandalf Goblins' Bane → 37 / 37a / 37b.
  Each line names its cut and the reasoning. Gandalf goes in ALL THREE — copies are
  fungible, it is not a choice.
- **Owned but with no home yet:** Gleaming Splendor, Key to the Side-Door, Elrond
  Moon-Reader, Misty Mountains Raider, Great Ugly-Looking Goblin, Old Fat Spider Can't
  See Me. The two amass cards want an Army deck the roster does not have — that is a
  build-a-deck idea, not a fit problem.

---

## 0. Repo position — CURRENT (2026-08-12, broad-scan-4)

- Working branch **`claude/broad-scan-xju0r1`**, one commit ahead of `origin/main`
  (`3b8e9bd`, the broad-scan-4 top-5 implementation), **pushed, no PR opened**. PR #120
  merged 2026-08-11, so the branch was restarted from `main` at the start of this cycle.
  **Check `git log origin/main..HEAD` before your first commit** — if it is empty, the last
  PR merged and you must restart from `main`
  (`git fetch origin main && git checkout -B <branch> origin/main`).
- Gates green: `check_all` all invariants hold with **ZERO soft warnings**; **1,266 tests
  in 29 files + conftest**, full suite green. The 7 blank-Card-Text `validate` warnings are
  K-11 vanilla creatures, expected, not a data gap. (The 7 stale flex lines §1 used to name
  were retired in `253cd13`.)
- Collection **2,186 library rows / 2,182 distinct names**; roster **103 deck files, 101
  of them roster-counted**, numbered through **68**; 34 `deck.py` subcommands; 13
  model-sanity gates + `check_all`. **40-brawl** is the roster's third Brawl conversion.
- **`dashboard.html` and `gallery.html` were both rebuilt this cycle** and are current — no
  `make dashboard` outstanding.
- **`ROADMAP.md` was regenerated 2026-08-11**; its strategic bet is match volume.
- **TWO OPERATOR VISUAL CHECKS ARE OUTSTANDING** and are the only part of broad-scan-4 a
  file cannot prove: the gallery in LIGHT mode (Regression Scenario 5's new leg — that
  palette has still never been rendered by a person) and a keyboard walk of the two
  repaired dashboard controls (Scenario 7). Neither blocks anything.

## 1. Repo position (broad-scan-3, 2026-08-09 — superseded by §0)

- Working branch **`claude/broad-scan-3fw71t`** (broad-scan-3, 2026-08-09) — **merged as
  PR #120 on 2026-08-11.** Earlier: PRs #110/#111/#112 all merged 2026-08-09.
- Gates at the time: `check_all` all invariants hold, with **one soft warning** — the 7
  stale flex lines the 2026-08-11 `+In` check surfaced (decks 8, 14, 26, 26a ×3, 50), since
  retired. **1,262 tests in 29 files.**
- Collection **2,186 library rows**; roster **103 deck files**, numbered through **68**.
  (Decks 67 Warpwright and the 68 Frog Sage family — 68 Sultai blink, 68a Bant
  wide-counters, 68b Selesnya burrow — were drafted 2026-08-10/11.)
- **PRs #116/#117/#118 merged 2026-08-11.**

## 2. What the broad-scan-3 cycle did (2026-08-09)

One `/broad-scan` (three stages, five parallel subsystem deep-reads) producing findings
**BS4-01…BS4-45**, then six implementation passes. Every block is in
`.cycle/blocks/2026-08-broad-scan3-*.md` — read those, not this summary, for detail.
Gates ended green with **ZERO soft warnings** and **1,188 tests**.

The changes most likely to affect your daily work:

1. **`suggest --lands` no longer offers back-face lands.** It filtered on a whole type
   line, so any card with `// Land` on its BACK qualified — **81 pool cards**, and three
   of deck 52's four top picks were unplayable as lands. This is the one that would have
   cost you a real deck slot.
2. **Every craft surface now flags rotation.** `suggest --lands/--ramp/--interaction` and
   `tier --to`'s craft fillers were the last silent ones, and they are the surfaces whose
   whole purpose is spending wildcards.
3. **`#: protect:` / `#: uncastable-ok:` finally work on DFCs.** Deck 66's header named
   its own title card and `cuts` ranked it as cuttable anyway.
4. **The rationale audit now checks `#: archetype:` figures**, which G-27 had claimed for
   a year while the figure loop read `#: tier:` alone.
5. **Ownership no longer ranks recommendations.** Three needs recommenders sorted owned
   cards above unowned at equal score; the goal is the best LIST, and owned data goes
   stale (see §5's ownership trap).

## 3. What the cycle decided rather than built

- **`check_commands`' executable-shape rule was measured and REJECTED for subcommands.**
  Requiring `python3 scripts/deck.py <name>` — the rule the SCRIPT half uses — would have
  failed **27 of 34 live subcommands**, because the skills write 30 of their references
  bare and only 3 sit in fenced code blocks. A caution CLAUSE is suppressed instead, which
  measured as costing zero coverage. **Measure before tightening a passing gate.**
- **Widening a scan needs its suppressions in the same change.** Extending the rationale
  audit to archetype figures returned **3 hits of which 2 were FALSE** (one quoting
  another deck by NAME, one quoting *Standard's* Dragons), and the suppressions written
  for those then **muted the 1 real one** until the parent-name case was handled — deck
  26a is "Iron Forge — Virulent", so its PARENT's name is a substring of its own.
- **The gate tests were mutation-tested against VACUOUS gates.** Making each hard gate's
  `check()` return `[]` is DETECTED in all five cases, so `tests/test_gates_fire.py`
  catches a dead gate, not merely a broken model. That is the difference between a
  "watched it fail" layer and a passing test.

## 3b. The 2026-08-09 session: a duplicate-craft sweep, and a data problem

**Read this before recommending any wildcard spend.**

A pass over all eleven decks whose craft plans contained a rare/mythic DUPLICATE (own 1,
deck wants 2) swapped eight of them out for distinct cards, nearly all already owned —
55b (five), 57 (three), 50, 56a, 58, 48 — freeing roughly ten rare-equivalents for the
cost of one common. Six duplicates were KEPT on their merits, each with the reason written
into its deck file: 2nd Appa, 2nd Sokka, 2nd Craterhoof, 2nd Ashroot, 2nd Gas Guzzler,
2nd Vnwxt. **The pattern that held across all eleven: a LEGEND's second copy almost never
survived scrutiny (it cannot share a battlefield with the first), while the duplicates
worth keeping were non-legends doing engine work, or cards with no functional cousin in
the format.** The Last Agni Kai is the priority craft — 56 and 56a are each short their
SECOND copy, and since copies are fungible one more rare completes both. (It was three
decks until 2026-08-31, when deck 59's crafts were ingested; 59 wants one copy and now
owns it.)

**But the ownership data was wrong four times during that pass** — see `[G-10]`. Two decks
were graded against counts that turned out false, and one recommendation used a craft cost
as a *reason*. Nothing in the toolchain can detect this. **Run `import_collection.py`
against a full tracker export before acting on any craft plan**; it is the only tool here
that sets counts exactly, including downward.

## 3c. The 2026-08-09 evening session

**Decks.** 55b/57/66 crafted and now FULLY OWNED (27 cards ingested, verify 27/27) —
55b and 57 were the two the dedup pass reworked most. Deck 19 gained Elspeth, Storm
Slayer (−Dazzling Angel), taking interaction 4→5 and the **metrics floor B→A**; the
LETTER is still B and wants a human call. Deck 26b replaced both ~2026 pending crafts
(−Inti/+Captain Howler, −Captain Storm/+Scrounging Skyray) and parked Vision of Love in
flex. **40-brawl** is a Standard Brawl conversion of deck 40 led by Ignis Scientia — The
Goose Mother was the better card and was rejected because a COMMANDER that rotates in
months is the deck's identity expiring.

**Two swaps were applied and then REVERTED on the user's challenge**, both worth reading
before re-proposing: Marauding Mako into 26b (the deck holds 16 artifact-creators against
17 discard cards — trigger frequency was a tie, and the cut card had trample in a deck
with almost no evasion), and Owlin Historian into 19 (the user wants Aven Interrupter
kept; the `{W}{W}` fix should come from LANDS).

**Tooling.** The rationale audit was **reworked against fixtures from five live misses**
— see `[G-26]`. Its first clean sweep found **six real stale rationales** (decks 30, 37b,
44, 48a, 51a, 58) that a scan run ~20 times that day had passed. `[G-16]`'s ENTERS-caveat
residual is fixed. `normalize_format` closes a latent trap where `#: format: historic-brawl`
disabled both the size floor and the copy limit (`[G-09]`).

## 4. Standing items, owner-paced — unchanged and still the biggest gaps

- **`matches.csv` EXISTS NOW — 9 matches, 8 attributed to decks 7 / 19 / 45.** The gap it
  used to name is only dented: n=2, n=2, n=4 per deck, and `--report` refuses a percentage
  under 20, so 34 decks still carry a PROVISIONAL tier graded against internal consistency
  alone. What changed is that the pipeline has now run end to end against real data, and
  running it again is cheap. **Two things the first real log settled, both the hard way.**
  `courseId` is the AVATAR cosmetic, not the deck — the nine rows were recorded against it,
  and a `#: arena: <courseId>` mapping was documented in the parser, the README and the
  skill, before anyone read the values. The real deck is in `EventSetDeckV3`, so the
  extraction grep is WIDER than the one every doc used to print; use the current one. And
  the 7/27 match is permanently unattributable — its log had rotated — which is what the
  12-hour bound protects: it stays blank rather than borrowing 8/07's deck. Decks 7, 19 and
  45 now carry `#: arena:` headers with both the Arena name and the stable `DeckId` GUID;
  add one to each deck as it gets played. See `[G-57]`. Still owner-paced: it needs games.
- **Deck 49 Big Draco (renamed from "Scaleforge" 2026-08-14) rotation-proofing — Route A,
  measured and NOT applied.** The user
  said "I will hold off on these changes for now," so it is queued, not rejected. Do NOT
  re-derive it: −Gishath/+Etali, Primal Storm · −Palani's Hatcher/+Savage Land Dinosaur ·
  −Decadent Dragon/+Nova Hellkite · −Realm-Scorcher Hellkite/+Steel Hellkite (craft R) ·
  −Flick a Coin/+Molten Exhale (craft C). Craft plan 18 → 15; the only rotating cards left
  would be the 2027 trio (Dragonhawk, Terror of the Peaks, Three Tree City), which is the
  user's call — a year of Standard for premium cards.
- **Deck 21a wants a HUMAN tier re-grade.** The K-14 fix took its card advantage 3 → 5,
  removing one of the two weaknesses its below-floor letter rested on; a one-source blue
  splash is now the only thing holding it down. Letters are never auto-written.
- **The Google Sheets round-trip needs its one-time operator setup.** The dev half is done;
  run `python3 scripts/sheets_sync.py check` — it names every missing part (packages, key
  file, sheet id, and whether the sheet is shared with the service account) and writes
  nothing.
- **The match-log rolling archive needs its one-time operator setup, and it is the one
  setup item with a DEADLINE ATTACHED.** `Player.log` is overwritten on every Arena
  launch, so until the launchd job in `.claude/commands/log-matches.md` Stage 0 is
  installed, every unextracted session is lost permanently — the 2026-07-27 match already
  is, and no tooling can recover its deck. The block was written but NOT executed here
  (this container is Linux; `launchctl` is untestable from it), so **it is unverified on
  the user's machine**: the verification step is `~/mtga-logs/snapshot.sh && wc -l
  ~/mtga-logs/arena.log`, and a zero count most likely means macOS is withholding Full
  Disk Access from `/bin/sh`. Ask about this before asking for a log paste.
- **The perceptual halves of Regression Scenarios 5–8 need a person at a browser**, and
  Scenario 9 needs a person with a real `Player.log`. The markup contracts are pinned by
  `tests/test_templates.py` and the match parser by `tests/test_parse_matches.py`, but
  contrast, focus rings, phone-width reflow, and a real Arena client's naming and rotation
  behaviour are none of them code-checkable.
- **October rotation pass is pre-loaded**: deck 28's flex block names successors for its
  six owned rotating cards; deck 28a has never had the pass; deck 36 loses Kutzil with no
  safe replacement for his "opponents can't cast spells during your turn" half.

## 4a-bis. WHAT THE 2026-08-11 SESSION CHANGED, in one place

Read this before §4b — several of its items moved.

- **Three PRs merged** (#117 ban replacements + deck 28 rebuild, #118 the deck 68 Frog
  Sage family, #119 the tooling/doc pass). Roster is **103 deck files through 68**;
  library **2,186 printings**; **1,262 tests**.
- **Two cards were BANNED out of Standard** (Badgermole Cub, Gran-Gran) and replaced
  across ten decks. The pool's `Legalities` is a build-time snapshot, so nothing in the
  repo flagged it — the ten decks were quietly illegal until a human noticed. **There is
  no gate for this and there cannot easily be one**; treat a ban announcement as an
  event that needs a `grep -rl` over `decks/` and a replacement pass.
- **Two staleness scans gained their missing half** (G-04 `+In`, G-26 prefix collision)
  and a role-pattern hole closed (G-67 target-first variable damage). The roadmap files
  the meta-gate for that whole bug class as Tier 2.1.
- **ROADMAP.md was regenerated** (it had been a 2026-07-31 snapshot through two cycles)
  and its strategic bet is Tier 2.2, match volume — which is §4's first standing item,
  now with a working pipeline behind it.
- **All staleness sweeps are at ZERO** as of this session: rationale, flex (both halves),
  header card-names, and the new `#~ note:` figures. `check_all` reports no soft
  warnings. If a fresh session sees one, it appeared after 2026-08-11.

## 4b. WHERE TO PICK UP — the shortlist for a fresh session

In priority order, with the reason. **Items 1 and 2 are unchanged and still first.**

1. **Run `import_collection.py` against a full tracker export.** FIVE ownership counts
   were wrong on 2026-08-09 (Cosmogrand, Halana, Ruby, Castle Doom, plus Cool but Rude's
   craft status), every one caught only because the user said "I actually have N". One
   was load-bearing in a recommendation. Nothing in the toolchain can detect this, and it
   should precede any wildcard spending.
2. **Deck 19's tier letter.** Its metrics floor is now A and the letter is B; `tier 19`
   reports it as possibly under-graded. The file records both sides. Letters are never
   auto-written — this needs a person.
3. **The three remaining Brawl conversions** the user planned: decks **46 Lightwing**
   (Delney), **4 Quantum Realm** (Ant-Man) and **11 Villainous** (Bullseye — note his
   identity is BR against a mono-B deck; a mono-B legend would be tighter). 40-brawl is
   the worked example; the pattern is one `#: commander:` line plus `#: format: Brawl`.
4. **The 100-card Historic Brawl build** the user asked about: seed **35a** (already
   60-card singleton, interaction 6 / card advantage 7) with **Terra, Magical Adept** as
   commander — her identity is 5-colour but she CASTS for `{1}{R}{G}`, so she unlocks all
   2,124 owned Historic-legal cards while asking the manabase for two. Avatar Aang was
   measured and rejected: he needs all four bends in one turn and airbend is owned 11
   against 22-24 for the others. (BS4-23 widened `wishlist._theme_model`'s deck-size
   window to accept 95–105 cards, so a 100-card deck will now be VISIBLE to
   `--suggest-targets` / `--rank` instead of silently dropped. That trap is pre-cleared.)
5. **Deck 19 Route B** — the white manabase. Aven Interrupter is 58% on turn three and
   Storm 61% on turn four; the fix is white DUALS, not cutting cards (the user said so
   explicitly after a swap was tried and reverted).

**Left open by broad-scan-3, in the order I would take them:**

- ~~G-37's two remaining scoring misses~~ — **DONE 2026-08-09, and only ONE was real.**
  Restricted mana ("spend this only to cast a creature spell") had ranked #1 for deck 52
  and is now discounted + marked `·restricted`. The conditionally-tapped miss **did not
  exist**: the 5.8-vs-4.6 gap the note cited was mono-colour vs DUAL, not tap handling —
  both tapped shapes score identically. The real limitation is the opposite and
  conservative (a conditional land never gets the untapped premium even when the deck
  meets the condition), so it prints `·tapped?` rather than guessing. **The lesson is in
  `docs/gotchas.md` [G-37]: re-measure a scoring claim against a control that differs in
  only the axis being blamed.**
- **`make dashboard`** — the committed snapshot is one rebuild behind BS4-42's KPI data
  path. The deployed Pages copy builds from source and is fine.
- **The six operator visual checks** in
  `.cycle/blocks/2026-08-broad-scan3-batch5-broad-implement.md`, above all the gallery's
  light palette: Batch 5 gave it a colour scheme that has **never been rendered**, and
  correctness there is the half a file cannot prove.
- **`/roadmap`** — ROADMAP.md is a 2026-07-31 snapshot and a whole scan cycle has landed
  since.

## 5. Traps re-confirmed this cycle

- **A grace clause added so a fix costs nothing is a place the fix can cost nothing.**
  BS2-23 made a tag edit defeat the pool's freshness reuse via a content fingerprint, and
  gave pre-existing stamps a pass: unknown → don't rebuild. But the reuse path returns
  BEFORE writing a stamp, so unknown was an ABSORBING state and the check could never arm.
  Found only because Batch H's seven keyword mappings produced a byte-identical
  `card-pool.csv` while step 2/6 announced itself and `check_all` stayed green. **Verify
  the artifact changed; do not trust the step that says it ran.**
- **A registry a human maintains cannot see what nobody added to it.** `check_dfc`'s alias
  registry checked the loaders someone listed, and every bug in that class was a loader on
  no list. The fix was to find them in the AST instead — and it found one immediately.
  This is the `check_commands` lesson again: a capability nothing reaches is invisible.
- **A check never watched failing is not a check.** The writer — the path every canonical
  file in the repo goes through — had thorough tests of what it DOES and nothing proving
  those tests would fail if it stopped. The mutation layer added in Batch H caught a wrong
  expectation of mine on its first run.
- **Before editing a module, scan for its test DOUBLES.** Three broke this cycle by
  encoding old behaviour, twice in Batch H alone (a two-line pool stamp written by
  default; a pinned copy of a warning string whose claim had just been refuted).
- **A swap's prose goes stale BY CONSTRUCTION.** Run `tier <id> --audit-rationale` after
  every apply and fix it in the SAME commit. A roster-wide tag change does this too: the
  H-6 retag moved two central-theme counts and both `#: tier:` figures needed re-grounding.
- **Copies are fungible.** "Already used elsewhere" is never a reason to exclude a card —
  one owned copy plays in every deck simultaneously.
- **A theme miss is not a colour-identity gap.** `suggest-homes` returning zero rows means
  no shared CENTRAL THEME, not that no deck of those colours exists. CLAUDE.md `[G-31]`.
- **Never hand-write `(SET) COLLECTOR#`** — use `deck.py resolve`, and pass `--expect 60`,
  which caught three 59-card drafts.

## 5b. Traps added 2026-08-09

- **A `#: plan:` header is a GRADING INPUT, not a label.** Deck 56a carried `aggro` while
  its own archetype prose said "slower, bigger"; the aggro path substitutes a clock score
  for interaction, which floated its floor to A. Corrected to `midrange`, the floor read B
  and the letter followed. Nothing flags this — the guard compares the letter to the floor,
  and the floor is what the wrong plan moved.
- **`stats`' power-N flag appended an ENTERS-trigger caveat regardless of timing —
  FIXED later the same day** (`[G-16]`): the flag now reads the trigger's own line and
  says "printed count is a FLOOR" for attack-time gates.
- **The rationale audit missed five live cases in one day and was REWORKED against
  fixtures** (`[G-26]`): possessives, self-name cues, short comma-heads, cross-sentence
  suppression and cross-deck figures are fixed; six real stale rationales surfaced on
  the first clean sweep and were corrected. The still-live residuals are in G-26.
- **Craft cost is REPORTED, never REASONED FROM** (`[G-10]`). Four ownership counts were
  wrong in one session and one of them was load-bearing in a recommendation.

## 6. The one open item from the cycle's own findings — NOW CLOSED

**BS2-07's header-consumer sweep is CLOSED (2026-08-09, as BS4-01), and the way it was
deferred is worth carrying forward.** It was left open on a measurement — zero live
instances, all 14 DFC-bearing headers using the full spelling — taken 2026-08-07. **Deck
66 was drafted 2026-08-08 with `#: protect: Eddie Brock` against a line storing `Eddie
Brock // Venom, Lethal Protector`, so the count was wrong the next day**: the deck's own
title card sat in its cut ranking while `header_card_staleness` reported the roster clean,
because that gate joins on `_ms_key` and the consumers did not. A gate vouching for the
thing it exists to detect is worse than no gate.

`deck._header_card_keys` is now the one home both headers share; every consumer keys its
side. Roster A/B against a pre-fix tree: exactly one deck changed (66), **zero tier floors
moved, zero uncastable counts changed**. Full evidence in `docs/gotchas.md` [G-63].

**The transferable lesson, now written into G-63: defer on the MECHANISM, never on the
census.** A zero-instances count is a fact about a moment; whether a join can ever be
wrong is the property that actually decides.
