# Handoff — start the next session here

Written 2026-08-06, refreshed three times on 2026-08-07 (latest: after the G-68 gate),
for a session with none of this one's context.
Read this before CLAUDE.md's Common Gotchas, not instead of them.

**Read the evidence file when a rule's reasoning matters.** CLAUDE.md carries the RULE and
any live residual; the incident and measurement live under the anchor the rule ends with —
`[G-nn]` / `[K-nn]` in `docs/gotchas.md`, `[C-nn]` in `docs/cycle-config.md`. Nothing was
deleted; open the long form before deciding a rule looks arbitrary.

**Also live: `docs/systems-map.md`** — which command answers a question, and why two
commands disagree.

---

## 1. Repo position

- Working branch **`claude/broad-scan-hekdj0`**. PRs #101–#107 all merged, including the
  last one, so the branch holds ONLY merged history. **Restart it from `main` before your
  first commit** — `git fetch origin main && git checkout -B claude/broad-scan-hekdj0
  origin/main` (CLAUDE.md Git rules).
- **The two other remote branches are fully merged too — do not try to recover them.**
  `claude/broad-scan-fzu6nq` shows **27 commits ahead** of `main` and
  `claude/project-development-continuation-3hnw5r` shows 1, but both went in by SQUASH
  merge (PRs #96–#99 and #95), which rewrites the commits so the originals stay
  permanently "ahead". Verified 2026-08-07: every file they added is in `main` except
  `.cycle/54-pile-reanalysis.md`, which was deliberately deleted when its swaps landed,
  and the ROADMAP blob is byte-identical. `git cherry` reports 26 of them as missing —
  that is a patch-ID artifact of squashing, not lost work.
- Gates green: `check_all` all invariants hold, **with ZERO soft warnings** — first time
  this cycle. 951 tests. The long-standing `Rogue's Passage (FDN) 264` warning (decks 26a
  and 50) is fixed; the real printing is `(HOC) 212`, from `deck.py resolve`.
- Collection **2,085 library rows / 2,081 distinct names / 2,154 copies** (the session-start
  hook prints the distinct-name figure, so 2081 vs 2085 is not a discrepancy); roster
  **95 decks**, numbered through **63**. Two code changes on 08-07 — the K-14 role-pattern
  fix (§2b item 5) and the G-68 header-staleness gate (§2c); everything else was data and
  decks.

## 2. What the 2026-08-05/06 sessions did

1. **Five new decks, four of them from owned cards only.** **59 Stampede Engine** (Gruul
   combat-ramp: attacking makes mana, mana buys creatures — the third corner of the
   combat-mana triangle), **60 Redline** (Rakdos max speed, the roster's first Start your
   engines! deck), **60a Night Circuit** (the UB speed-DRAIN variant 60's notes parked —
   drain ticks speed without combat), **61 Pony Express** (GW Mounts on a +1/+1 counter
   spine), **62 Rot and Bloom** (the first Sultai deck — wraths that draw, feeding
   reanimation), **63 Heirloom** (Abzan +1/+1 counters — see §4).
2. **Tooling: eight findings implemented** (`/broad-implement #1-8`, block in
   `.cycle/blocks/`). The two that change daily work: **craft views now carry `⚠rot`**
   (`check`, `wildcards`, and the new `wildcards --dedup` cross-deck union), and the
   **rationale audit now DETECTS shorthand citations** of absent cards. Also `resolve
   --expect N` (caught a 59-card draft three times since), vanilla-vs-data-gap messaging,
   counters-payoff patterns, and `make postedit`.
3. **Rotation-proofing, twice.** Deck 28's craft plan held FOUR cards rotating within
   months; deck 36's held one. Both fixed by swapping to owned rotation-safe cards. **Deck
   49 still holds EIGHT** and its Route A plan is written but NOT applied — see §3.
4. **Ingests:** two crafted batches (14 + 2) and one 16-card TDM pack, all verified
   16/16-style by `verify_ingest`, with the placement swaps applied across ~20 decks.

## 2b. What the 2026-08-07 session did

1. **Six more ingest batches** (14 + 13 + 18 + 19 + 18 + 15 = ~97 cards) plus a
   single-card Chandra ingest, every one `verify_ingest`-confirmed. Batches 11–13 held
   cards that are NOT Standard-legal; those are noted in their commits, not silently kept.
2. **~35 placement swaps** across the roster from those batches. Deck 35a is now **one
   card (Omniscience) from buildable**; decks 62 and 63 are fully buildable.
3. **Chandra, Spark Hunter into five decks in one pass** — 26b, 48, 58, 10, 45a — plus
   48a where she was already maindecked as a craft target and simply became owned. The
   selection is the worked example of G-61: `suggest-homes` rated her KEY in 14 of 42
   decks on generic red themes, and the five real homes were chosen by hand-counting
   artifacts / token producers / Vehicles / Mayhem cards. **Do not re-derive this** — the
   table is in `docs/gotchas.md` under `[G-31]`.
4. **Deck 26b's `#: protect:` header named a card the deck has never run** (Summon:
   Bahamut). This became G-68 the same day — see §2c; there IS a gate for it now.
5. **K-14 found AND FIXED (same day).** `role_tally` could not see a draw clause behind an
   ACTIVATION cost, so every planeswalker's draw ability read as zero card advantage (187
   pool cards, 24 planeswalkers). Two patterns added, `_LOOT_RE` given the singular pair.
   **Result: 18 decks up, 12 down, interaction unchanged, ZERO tier floors moved**, and the
   16 decks left with a stale `#: tier:` figure were re-grounded in the same commit.
   **One thing is left for a human:** deck 21a's card advantage went 3 → 5, which removes
   one of the two weaknesses its below-floor letter rests on. The file says so and asks for
   a re-grade; the letter was not auto-written (design constraint).

## 2c. The 2026-08-07 tooling tail

1. **`Rogue's Passage` printing fixed** in decks 26a and 50 — `(FDN) 264` → `(HOC) 212`,
   resolved rather than hand-written (G-65). That clears the oldest standing soft warning.
2. **New gate `[G-68]`: a `#:` header that lists CARD NAMES goes stale, and nothing
   checked one.** `#: protect:` and `#: uncastable-ok:` are read as instructions, so an
   entry naming an absent card is a silent no-op — and `protect` also inflates the
   build-around count the zero-protection flag prints, which deck 26b was doing inside the
   sentence arguing its own tier cap. `deck.header_card_staleness` now sweeps the roster
   in `check_all` (soft). **It found two more on its first run**: deck 56's Boros header
   protected two GREEN cards that live only in its Gruul variant 56a. Both fixed; a
   roster-wide test anchor means any new hit is a regression, not backlog.

## 3. The agreed next task

**Deck 49 Scaleforge rotation-proofing — Route A, proposed and NOT applied.** The user
said "I will hold off on these changes for now," so it is queued, not rejected. The plan,
already measured:

- −Gishath / +Etali, Primal Storm (owned) · −Palani's Hatcher / +Savage Land Dinosaur
  (owned) · −Decadent Dragon / +Nova Hellkite (owned) · −Realm-Scorcher Hellkite /
  +Steel Hellkite (craft R, safe) · −Flick a Coin / +Molten Exhale (craft C, safe)
- Effect: craft plan 18 → 15, three rares of rotating wildcards saved, and the only
  rotating cards left are the 2027 trio (Dragonhawk, Terror of the Peaks, Three Tree
  City) which the user must decide on — a year of Standard for premium cards.
- Do NOT re-derive this; the measurements are in the transcript and the plan is stable.

## 4. Standing items, owner-paced

- **`matches.csv` is still EMPTY, and the gap is bigger than this file used to say.**
  **34 decks** carry a PROVISIONAL tier (an earlier note said ~12 — recount, do not trust
  that figure), every one of them promising a re-grade "after real games", and zero games
  are recorded. Every tier argument on those decks is unfalsifiable until `/log-matches`
  runs once. Still the single largest gap in the project, and it needs the user, not the
  tooling.
- **Deck 21a wants a HUMAN tier re-grade.** The K-14 fix took its card advantage 3 → 5,
  which removes one of the two weaknesses its below-floor letter rested on; the manabase
  (a ONE-source blue) is now the only thing holding it down. The file argues this in its
  own `#: tier:` block. Letters are never auto-written, so this is yours to settle.
- **October rotation pass is pre-loaded**: deck 28's flex block names successors for its
  six owned rotating cards; deck 28a has never had the pass; deck 36 loses Kutzil with no
  safe replacement for his "opponents can't cast spells during your turn" half.
- **Deck 63's first upgrade is PROTECTION, not more counters** — it runs three modal
  answers after the 2026-08 pass; Daydream and Airtight Alibi are benched as flex lines
  with their reasons.

## 5. Traps this cycle re-confirmed

- **Never hand-write `(SET) COLLECTOR#`** — use `deck.py resolve`. Violated twice in
  earlier cycles; the `Rogue's Passage` soft warning above is the same class, still open.
- **`resolve` does not count for you unless you ask** — pass `--expect 60`. Three
  from-scratch drafts resolved to 59 this cycle and the flag caught all three.
- **A swap's prose goes stale BY CONSTRUCTION.** Run `tier <id> --audit-rationale` after
  every apply; this cycle it caught seven stale figures and one cut-card citation in a
  single batch. Fix them in the SAME commit.
- **Copies are fungible.** "Already used elsewhere" is never a reason to exclude a card —
  one owned copy plays in every deck simultaneously. This came up explicitly this cycle
  and the answer changed a deck-building decision.
- **A theme miss is not a color-identity gap.** `suggest-homes` returning zero rows means
  no shared CENTRAL THEME, not that no deck of those colors exists — reporting the second
  when you measured the first produced a wrong "you have no Abzan deck" claim (you have
  four). Check `#: colors:` before concluding a color pair is unbuilt. **Now a permanent
  rule** — CLAUDE.md `[G-31]`, with the long form in `docs/gotchas.md`.
- **"No gate checks this" was true TWICE in one cycle, on the same shape.** K-14 (a role
  bucket nothing exercised) and G-68 (a `#:` header nothing validated) were both live for
  months behind fully green gates. When something reads like a fact about the deck — a
  count, a header, a label — ask which gate would fail if it were wrong, and if the answer
  is none, that is the finding. Both were cheap to fix once stated.
- **A quality-guard regression can be the METRIC being wrong.** Deck 58's guard reported
  card advantage 4→3 on a swap that RAISED it. That specific cause is FIXED (K-14 — the
  classifier now reads a draw behind an activation cost), so do not go looking for it;
  the transferable half is the habit. The guard is soft for a reason: when it fires,
  ask which side is wrong before "fixing" the deck.
- **Widening a role bucket needs a floor measurement BEFORE it lands.** K-14 is the worked
  example: the first draft counted `Sacrifice this land: Draw a card`, which would have
  swept in a whole tapland cycle and moved the change from 24 decks to 58. Measured
  roster-wide first, so what shipped moved 18 decks up, 12 down, and **zero tier floors**.
  Anything feeding `tier_band` has to clear that bar — and it left 16 decks with a stale
  `#: tier:` figure, all re-grounded in the same commit.
