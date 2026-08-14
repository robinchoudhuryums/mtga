# Handoff — start the next session here

Rewritten 2026-08-09 after the **broad-scan-3** cycle closed, then updated 2026-08-12 for
the **broad-scan-4** cycle (§0 below is the newest state and supersedes anything under it
where they disagree). Written for a session with none of this one's context. Read it before
CLAUDE.md's Common Gotchas, not instead of them. The broad-scan-2 cycle it previously
described is in `.cycle/blocks/2026-08-broad-scan2-*.md` if you need it.

**Read the evidence file when a rule's reasoning matters.** CLAUDE.md carries the RULE and
any live residual; the incident and measurement live under the anchor the rule ends with —
`[G-nn]` / `[K-nn]` in `docs/gotchas.md`, `[C-nn]` in `docs/cycle-config.md`. Nothing was
deleted; open the long form before deciding a rule looks arbitrary.

**Also live: `docs/systems-map.md`** — which command answers a question, and why two
commands disagree.

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
