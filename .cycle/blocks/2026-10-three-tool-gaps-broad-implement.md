---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- G-33 KNOWN GAP 2 — a doubler that doubles two axes (Doubling Season) was priced on its FIRST axis only, and counter doublers carried no `counters` tag
- G-38 — `deck_needs` (the `suggest --needs` header and the `deficit` `--ramp` ranks on) summed land colour IDENTITY instead of the shared manabase count
- K-12 — a ONE-SIDED damage sweep ("deals X damage to each opponent and each creature they control") scored zero roles

Files modified: scripts/deck.py, scripts/tag_synergies.py, scripts/check_suggest.py, tests/test_deck.py, tests/test_deck_models.py, card-pool.csv, card-pool.build, card-library.csv, gallery.html, dashboard.html, scripts/role_baseline.txt, decks/07-*/deck.txt, decks/30-temur-fractals/deck.txt, decks/56-boros-tall/56a-executioners-song.txt, CLAUDE.md, docs/gotchas.md, .cycle/NEXT-SESSION.md, .cycle/STATE.md

CHANGES:
K-12 | scripts/deck.py, tests/test_deck.py | Two `Sweeper` patterns: "deals N/X damage to (each opponent | target player/opponent | that player) and [N damage to] each creature [and planeswalker] (they | that player | target player | your opponents) control(s)", plus the scalable "deals damage to each creature your opponents control equal to". 15 pool cards, all real one-sided sweeps on a full-text read; Homing Lightning (same-name spot removal) and Balefire Dragon (on-hit sweep) pinned OUT. Roster: interaction +1 in decks 30 (7→8) and 56a (5→6), 0 tier floors moved, `cuts` #1 changed in 1 deck (56a, where Soul Immolation was the top cut as a zero-role card). The suite's roster figure sweep caught 56a's stale "interaction 5"; decks 30 and 56a prose re-grounded.
G-38 | scripts/deck.py, tests/test_deck_models.py | `deck_needs` takes sources from `deck_color_sources` (→ `deck_source_profile`) restricted to the deck's colours — the call `suggest_lands` already made. 53 of 114 decks' `--needs` counts changed, in both directions (any-colour/fetch lands read 0 by identity — deck 21a B 5 vs 12; gated Verges read full — deck 28 G 16 vs 12). 0 of 114 now disagree with `consistency` (checked with its own library-row inputs). `--ramp` top-10 re-ordered in 5 decks, #1 changed in 0; 0 tier floors. New synthetic any-colour land in the model-test universe; the test fails on the old code.
G-33 gap 2 (code) | scripts/deck.py, scripts/check_suggest.py, tests/test_deck.py | `doubler_axes` (every axis), `doubler_axis` (first, kept as a label) and one pricing primitive `doubler_best` → (axis, support): the axis furthest above its own `doubler_calib` floor, MAX not sum (one card can feed two axes). `cut_keep_score`'s ✱ term, `screen` and `suggest-homes` call it; `structural_overlay_hit` checks every axis. `check_suggest` gained a two-axis probe. Roster: Doubling Season re-priced on counters in decks 4 (27, was tokens 14), 78 (13/11), 78-brawl (12/11); deck 30 scratch copy counters 18 vs tokens 9. `suggest-homes "Doubling Season"`: 40/42 rows re-ordered, 6 counters decks role-player→KEY, #1 unchanged. 0 tier floors.
G-33 gap 2 (tags) | scripts/tag_synergies.py, card-pool.csv, card-library.csv | The `counters` rule also matches "one or more counters | counters? would be put" — 12 pool cards, all counters cards; the plural "counters on" (90 cards, mostly "remove all counters on") measured and rejected. `make refresh` rebuilt the pool (stamp hash, K-10) and `--merge` tagged 4 library rows. Roster: Doubling Season left the `cuts` top 3 in 5 decks (4, 58, 69b, 78, 78-brawl), Doc Samson left deck 4's; 0 `cuts` #1 changes; 0 tier floors. Deck 7 central themes 14→12 (Doc Samson's tag), prose re-grounded. `suggest-homes "Loading Zone"` 13 rows / KEY 4 → 47 / 26, matching its already-tagged siblings (Innkeeper's Talent and The Earth Crystal 47/24, Michelangelo 52/28).

TEST RESULTS: passed — full pytest suite exit 0 (but see the HIGH follow-on: that run reverted card-library.csv, restored afterwards); `check_all.py` all invariants hold (soft warnings pre-existing: lower-bound counts, deck 28 flex note, 3 dead library searches); `check_suggest` OK; `check_docs` OK. Watched-it-fail: the G-38 test fails with scripts/deck.py stashed. The first K-12 run failed `test_the_roster_figure_sweep_is_clean` on deck 56a's stale prose — caused by this change, fixed by re-grounding the prose (the gate working as G-67 intends).
REGRESSION RISKS: (1) `doubler_axis` keeps its return contract, so no caller breaks; the three pricing callers moved to `doubler_best`, and `structural_overlay_hit` already tolerated a sequence. (2) `deck_needs`' `sources` dict keeps its keys (deck colours); values now follow the shared count, so `deficit` shifts — measured above. (3) The pool rebuild carried 3 days of unrelated Scryfall drift: 9 Reality Fracture reprints became Standard-legal (Chandra Torch of Defiance, Tarmogoyf, five slowlands, Tetsuko Umezawa, Yargle), which re-ordered 8 decks' `--ramp` lists and changed 2 decks' #1 to Chandra; Agent of Raffine lost `ramp` on a Scryfall text change. (4) Loading Zone and Doubling Season now trip the suggest-homes KEY-saturation warning (26 and 32 of 114) — the counters axis's key-at-p75 calibration predicts ~25%.
INVARIANTS AT RISK: None — INV-03 (pool schema) rebuilt by its own builder; INV-02 unaffected (no library rows added); INV-04 deck edits were `#: tier:` prose only; INV-06 tags regenerated by the documented path (`make refresh`, `--merge`).
NET SCORE: 3 − 0 = 3

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds and publishes `dashboard.html` on the next push to `main` (automatic). Data + tooling ship by commit/push.

(Not complete in production until blocking operator actions are done AND
the deploy step is confirmed.)

FOLLOW-ON ITEMS:
- **HIGH — the pytest suite reverts the REAL card-library.csv on every run.**
  `tests/test_app_editor.py::TestRequestGuard::test_a_post_with_no_origin_is_allowed` posts
  to `/api/revert` without the `library` fixture, so `app.DEFAULT_CSV` is the repo's own
  library and the endpoint restores its newest `.bak` — i.e. it UNDOES the last library
  write. Caught here: the full-suite run at 16:08 discarded `tag_synergies --merge`'s four
  rows (backup `card-library.csv.20261001-160850-883249.bak` holds them; the live file came
  back with the 02:52 content and mtime), and the first commit of this change went out
  without them; restored by re-running `tag_synergies.py --merge` and committed after.
  The backups stamped 13:23 and 14:20 today are the same test on earlier runs (invisible
  then, because nothing had been written since the newest backup). Any ingest or tag write
  that is not committed before the suite runs (including the SessionStart hook's suite
  after a code change) is silently undone. Fix: give that test the `library` fixture (and
  audit the other fixture-less `/api/*` POSTs in the class).
- suggest-homes' KEY-saturation warning says "KEY scores THEME OVERLAP ALONE", which is wrong when the doubler-density overlay minted the KEY (the whole counter-doubler family: Innkeeper's Talent, The Earth Crystal, Michelangelo, Loading Zone, Doubling Season).
- `structural_overlay_hit` ignores a doubler's power restriction (`doubler_restriction`) while `doubler_best` applies it — pre-existing, left as-is to keep scope; G-70 shape.
- G-33 KNOWN GAP 1 still open: a TYPE-scoped doubler (Splinter's Ninja clause) is counted against the whole deck.
- K-12 residuals still open: Cheering Crowd's conditional mana ability; Balefire Dragon's on-hit sweep deliberately unscored.
- Nine Reality Fracture reprints are now Standard-legal in the pool (slowlands, Chandra, Tarmogoyf…) — relevant to the queued deck 55/60 FRA swaps and any manabase pass.

DOCUMENTATION UPDATES NEEDED:
- None outstanding — CLAUDE.md (G-33, G-35 caller list, G-38, K-12) and docs/gotchas.md (dated closure sections under [G-33], [G-38], [K-12]) updated in this change.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
