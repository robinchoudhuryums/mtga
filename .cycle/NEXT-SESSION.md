# Handoff — start the next session here

Rewritten 2026-08-07 after the broad-scan-2 cycle closed (top-5 → follow-ons → Batches
A–H, plus four `/sync-docs` passes), for a session with none of this one's context.
Read this before CLAUDE.md's Common Gotchas, not instead of them.

**Read the evidence file when a rule's reasoning matters.** CLAUDE.md carries the RULE and
any live residual; the incident and measurement live under the anchor the rule ends with —
`[G-nn]` / `[K-nn]` in `docs/gotchas.md`, `[C-nn]` in `docs/cycle-config.md`. Nothing was
deleted; open the long form before deciding a rule looks arbitrary.

**Also live: `docs/systems-map.md`** — which command answers a question, and why two
commands disagree.

---

## 1. Repo position

- Working branch **`claude/broad-scan-3fw71t`** (broad-scan-3, 2026-08-09), pushed but
  **not yet merged**. Earlier: PRs #110/#111/#112 all merged 2026-08-09. The branch is
  restarted from `main` after each merge. **Check `git log origin/main..HEAD` before your
  first commit** — if it is empty, the last PR merged and you must restart from `main`
  (`git fetch origin main && git checkout -B <branch> origin/main`).
- Gates green: `check_all` all invariants hold, **ZERO soft warnings**. **1,146 tests in
  29 files.** The 7 blank-Card-Text `validate` warnings are K-11 vanilla creatures and are
  expected, not a data gap.
- Collection **2,133 library rows**; roster **99 deck files**, numbered through **66**;
  34 `deck.py` subcommands; 13 model-sanity gates. (Decks 64
  Gray Goo, 65 Web of Life and 66 Lethal Protector were drafted 2026-08-08; 66 was
  promoted out of 65's variant slot. **40-brawl** is the roster's third Brawl conversion,
  added 2026-08-09.)
- **`ROADMAP.md` is a 2026-07-31 snapshot** with a staleness header on it. Individual
  entries are marked DONE as they land, but it wants a `/roadmap` regeneration.

## 2. What the broad-scan-2 cycle did (2026-08-07)

One `/broad-scan`, then nine implementation passes. **57 findings closed + 1 retracted**
in the first eight; Batch H closed the strategic remainder. Tests 951 → 1,078. Every
block is in `.cycle/blocks/2026-08-broad-scan2-*.md` — read those, not this summary, when
you need the detail.

The changes most likely to affect your daily work:

1. **`deck.py sync` refuses a TRUNCATED paste** (under 75% of the stored deck) — a partial
   paste is a strict subset, so the shared-card floor read it as a full-confidence match
   and `--apply` would have rewritten the 60 down to the fragment. `--force` overrides.
2. **`suggest --ramp / --interaction / --needs` now apply the deck's format filter**, and
   read castability from the PRINTED cost like `suggest` proper. They were the two
   siblings the G-58 fix missed, hiding 34 castable interaction cards and 25 mana sources
   from mono-colour decks — on exactly the paths a scorecard deficit routes you to.
3. **Player-only burn no longer counts as spot removal** (14 decks over-read interaction).
4. **The editor refuses a stale deck save with a 409** instead of silently overwriting a
   file a CLI `swap --apply` changed underneath the tab.
5. **Seven Universe-Beyond keywords are themed** (Batch H) — vivid, job select, opus,
   increment, infusion, disappear, paradigm. Roughly 85 pool cards changed tags, so theme
   weights moved roster-wide.

## 3. Batch H, and the two things it decided rather than built

**Read `.cycle/blocks/2026-08-creature-cut-retest.md` before touching the cut ranking.**

- **The creature-cut question is CLOSED for two hypotheses, and the second closure
  inverts what the tool used to say.** At n=251 the split held (creature 50%, noncreature
  86%). The mechanism `deck.py feedback` ITSELF asserted — `fit` sums theme weights
  unnormalized, creatures carry ~2× the tags — is true as an observation (5.31 vs 3.15
  tags per pool card, so 1.7×) and **refuted as a diagnosis**: normalizing lifts creature
  agreement 53→68% and **collapses noncreature 83→51%**. The unnormalized sum is
  load-bearing for the segment that works. **Do not derive a third fix from the tag-count
  asymmetry** — it is real, visible, and misleading, and two pre-registered tests have now
  died on it (body quality 2026-07, normalization 2026-08).
- **The second model is UNDERPOWERED, not rejected.** Excluding creature-subtype tags from
  `fit` (they are already paid for by `min(tribal,6)`) missed both criteria, but the
  harness resolved 38 of 103 creature rows. **Fix the harness before re-asking**: its
  snapshot selector matches a card name anywhere in the file, including a `#:` COMMENT, so
  it can pick a version where the card is discussed but not played. Match parsed lines.
- **`jump` is the keyword lesson worth carrying.** It reports 13 cards; 11 of them are
  `Jump-start` cards that Scryfall also labels "Jump". Mapping it would have put `evasion`
  on 11 graveyard spells for the sake of 2 real ones. **A keyword's reported COUNT is not
  its population** — read the cards before believing a tally.

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
the format.** The Last Agni Kai is the priority craft — 56, 56a and 59 are short the same
copy, so one rare completes three decks.

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

- **`matches.csv` is STILL EMPTY. This is the single largest gap in the project.** 34
  decks carry a PROVISIONAL tier, every one promising a re-grade "after real games", and
  zero games are recorded. The data is free and already in `Player.log`, the parser is
  written and tested (`/log-matches`), and until it runs, every tier letter on the roster
  is graded against internal consistency alone. It needs the user, not the tooling.
- **Deck 49 Scaleforge rotation-proofing — Route A, measured and NOT applied.** The user
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
- **The perceptual halves of Regression Scenarios 5–8 need a person at a browser.** The
  markup contracts are pinned by `tests/test_templates.py`; contrast, focus rings and
  phone-width reflow are not code-checkable.
- **October rotation pass is pre-loaded**: deck 28's flex block names successors for its
  six owned rotating cards; deck 28a has never had the pass; deck 36 loses Kutzil with no
  safe replacement for his "opponents can't cast spells during your turn" half.

## 4b. WHERE TO PICK UP — the shortlist for a fresh session

In priority order, with the reason:

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
   against 22-24 for the others.
5. **Deck 19 Route B** — the white manabase. Aven Interrupter is 58% on turn three and
   Storm 61% on turn four; the fix is white DUALS, not cutting cards (the user said so
   explicitly after a swap was tried and reverted).

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
