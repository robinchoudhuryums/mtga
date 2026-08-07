# Handoff — start the next session here

Written 2026-08-06, refreshed 2026-08-07, for a session with none of this one's context.
Read this before CLAUDE.md's Common Gotchas, not instead of them.

**Read the evidence file when a rule's reasoning matters.** CLAUDE.md carries the RULE and
any live residual; the incident and measurement live under the anchor the rule ends with —
`[G-nn]` / `[K-nn]` in `docs/gotchas.md`, `[C-nn]` in `docs/cycle-config.md`. Nothing was
deleted; open the long form before deciding a rule looks arbitrary.

**Also live: `docs/systems-map.md`** — which command answers a question, and why two
commands disagree.

---

## 1. Repo position

- Working branch **`claude/broad-scan-hekdj0`**. PRs #101–#105 all merged; the branch was
  restarted from `main` after each. **If the current PR is merged when you resume, restart
  the branch from `main` before the first new commit** (CLAUDE.md Git rules). The commits
  after `0c47ab4` (the #105 merge) are unpushed-to-`main` data work — no PR yet.
- Gates green: `check_all` all invariants hold; 939 tests. One standing SOFT warning:
  decks 26a and 50 name `Rogue's Passage (FDN) 264`, a printing the repo does not hold —
  fix with `deck.py resolve` next time either deck is touched.
- Collection **2,085 library rows / 2,154 copies**; roster **95 decks**, numbered through
  **63**. Nothing in `scripts/` changed on 2026-08-07 — that day was all data and decks,
  so tooling behaviour is exactly as the 08-05/06 notes below describe it.

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

## 2b. What the 2026-08-07 session did (data only — no code)

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
   Bahamut). Worth a spot-check elsewhere: a protect entry for an absent card silently
   shields nothing, and no gate flags it.
5. **New rule K-14** — `role_tally` cannot see a draw clause behind an ACTIVATION cost, so
   every planeswalker's draw ability reads as zero card advantage (187 pool cards, ≥12 on
   the roster). This is the first thing to fix if a tooling cycle wants a small, high-value
   pattern job; the measurement is done and written up.

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

- **`matches.csv` is still EMPTY.** ~12 decks now carry "B/A PROVISIONAL — re-grade after
  real games" and zero games are recorded. Every tier argument on the new decks is
  unfalsifiable until `/log-matches` runs once. This is the single largest gap in the
  project and it needs the user, not the tooling.
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
- **A quality-guard regression can be the METRIC being wrong.** Deck 58's guard reported
  card advantage 4→3 on a swap that raised it, because the classifier reads a
  trigger-shaped draw and not a cost-shaped one (K-14). The guard is soft for a reason:
  check which side is wrong before "fixing" the deck.
