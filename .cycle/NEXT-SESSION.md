# Handoff — start the next session here

Written 2026-08-05, for a session with none of this one's context.
Read this before CLAUDE.md's Common Gotchas, not instead of them.

**Read the evidence file when a rule's reasoning matters.** CLAUDE.md carries the RULE and
any live residual; the incident and measurement live under the anchor the rule ends with —
`[G-nn]` / `[K-nn]` in `docs/gotchas.md`, `[C-nn]` in `docs/cycle-config.md`. Nothing was
deleted; open the long form before deciding a rule looks arbitrary.

**Also live: `docs/systems-map.md`** — which command answers a question, and why two
commands disagree.

---

## 1. Repo position

- Working branch **`claude/broad-scan-hekdj0`**. PR **#100** (the 2026-08 broad-scan
  cycle) merged earlier as `1df3fbb`; the branch was restarted and now carries the
  Mardu-family work, which is being PR'd and merged at this handoff's writing. After
  that merge the branch must be RESTARTED from `main` again before any new commit
  (CLAUDE.md Git rules).
- Gates green: `check_all` all invariants hold, zero soft warnings; 922 tests.
- Collection: 1,895 cards; the deck roster now runs through **58** (see §2).

## 2. What the 2026-08-04/05 sessions did

1. **Seven decks from one pile family.** The 131-card Mardu pile produced **55 Mardu
   Waves** (Mobilize pulse, A PROV), **55a Spellstorm** (cast-cadence, A PROV), **55b
   Airbender** (exile-cast, B PROV argued under the floor). The user then extended the
   pile (+59 cards, three concepts); the addendum verdicts produced **56 One Fell Swoop**
   (Boros ultra-tall — the white package beat the green in a drafted A/B on every axis),
   **56a Overgrowth** (the Gruul variant, revived with green's own protection suite),
   **57 Jeskai Tempest** (prowess tempo; the pile has ZERO mono-U spells — first tuning
   axis is crafting blue tempo), and **58 Gold Standard** (Jund Treasure economy around
   Roxanne's token-mana doubling; the RGB concept that finally had an unclaimed
   identity). Concept G (generic RGB) was proven infeasible-as-stated by count (zero G/B
   cards in the pile; deck 8 already owns BRG sacrifice).
2. **Tuning swaps applied** (all quality-guarded, ledger-recorded): 55a — Equilibrium
   Adept + Antiquities in, Blazing Firesinger + Pigment Wrangler out; 55 — Taii Wakeen
   in for one Lightning Helix, Jolly Balloon Man in for Snow Villiers; 58 — Callous
   Sell-Sword in for one Lightless Evangel; 55b — Red Tiger Mechan recorded as a
   flex-line craft (user keeps Longhorn after the plot ruling: the plotted card's BODY
   comes back, cast free from exile, feeding Zuko/Appa/Quintorius).
3. **`.cycle/55-mardu-analysis.md` deleted (again, finally)** — every durable finding
   lives in the seven decks' `#:` headers; the addendum's batch verdicts are in git
   history of that file.
4. Two doc residuals recorded from real incidents: G-66 (targets counts CARDS — a token
   economy reads false-thin; deck 58) and K-03 (a card keying a TYPE it never carries —
   Gilgamesh's "Equipment cards" — is tag-invisible, so suggest-homes missed deck 39).

## 3. Open work, in priority order

1. **`.cycle/54-pile-reanalysis.md` §5/§5b — the queued swap plans for decks 54/54a/54b
   are STILL not applied** (verified against git: decks/54 untouched since PR #99).
   Apply via /apply-changes or re-judge, then delete that doc.
2. **Pending placements the user is still considering** (cut candidates already
   delivered in-session; screens/homes verified): Mabel + Gilgamesh + Veteran Guardmouse
   → deck 39 (cuts: Slash of Light, Go Ninja Go, Barret Wallace); Zidane → 45 (cut
   Bitter Triumph); Aziza → 55a (cut Thunder Salvo; 57 weaker — tap-cost fights tempo);
   Team Avatar → 55 as a flex line (attacks-alone reads the wave — documented ruling);
   Leyline of the Guildpact → 17 (cut Bender's Waterskin).
3. **Wildcard/pack guidance delivered:** craft directly Castle Doom (7 decks), Electro
   (6), Appa (6), Cosmogrand (5); pack priority FDN > TDM > OTJ > EOE; avoid LCI/WOE
   packs (rotating ~2026).
4. The 56-core-vs-56a A/B continues in real games — whichever wins takes the buildable
   slot; 57's blue-tempo craft axis; 58's engine speed decides its B-vs-floor letter.
5. Standing roadmap bets, owner-paced: log the first matches (`matches.csv` still
   empty), deck lifecycle status, keyword theming Tier 1 (`keyword_baseline.txt`).
6. app.py's Flask routes and build_gallery's HTML output remain the two untested
   surfaces (need a Flask test client / HTML assertions — a different harness class).

## 4. Traps that cost time this session

- A same-pile sibling deck goes in the CORE deck's directory as `NNx-slug.txt`
  (`decks/55-mardu-waves/55a-spellstorm.txt`), NOT its own `decks/55a-…/deck.txt` —
  the id won't parse otherwise.
- `tier --audit-rationale` reads "copies a Seething Song" as a stale card citation —
  phrase similes as effects ("a +5 red burst"), not card names.
- Hand-dated rotation years were wrong twice; `deck.py rotation` has the per-deck
  years — cite it, don't date sets from memory.
- Never hand-write a collector number even in a scripted replacement — Temple of
  Malady went in as 702 against resolve's 700 (G-65's exact failure, caught by legal).
- `suggest-homes`' KEY can be label-only (generic tag overlap) AND its misses can be
  structural (the K-03 tag hole) — judge every label against the card's text and the
  target deck's engine before acting.
