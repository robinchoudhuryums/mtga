---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
  BS13-01 | A hybrid pip with ZERO sources of one half was priced as no constraint at all, so 41 roster cards reported 100% castability — the worst against a true 52.5%
  BS13-02 | A figure stated with a COPULA ("interaction is 7") is invisible to `tier --audit-rationale`, which requires the number ADJACENT to the label

Files modified: scripts/deck.py, tests/test_deck.py, decks/27-blink/deck.txt,
  decks/44-grand-larceny/deck.txt, decks/46-lightwing/deck.txt, decks/57-tempest/deck.txt,
  decks/56-boros-tall/56b-ball-lightning.txt

CHANGES:
BS13-01 | scripts/deck.py | New `binding_pips(cost, sources)` — the strict colour demand a
  cost places on a deck with THESE sources. `parse_pips` splits strict from hybrid and every
  probability surface then DROPPED the hybrid half, on the premise `cast_probability`'s
  docstring states: a hybrid is strictly easier, so the strict demand binds. True everywhere
  except at ZERO, where it fails SILENTLY: with no sources of one half, `{B/G}` IS `{B}`.
  Three cases and only the middle one changes — 2+ live halves stays non-binding; exactly ONE
  live half collapses to a strict pip on it; NO live half is left to the castability lint,
  because inventing a pip there means picking a colour the deck cannot produce, which is a
  guess. A monocolor `{2/W}` or Phyrexian `{W/P}` hybrid is a single-colour frozenset payable
  generically and never binds — the same rule `_candidate_castability` uses.
  Wired into BOTH probability surfaces so they cannot disagree: `pip_depth_warning` and
  `consistency`'s cast-on-curve table. The table's footer claimed "hybrids excluded as
  non-binding", which the fix makes false, and was corrected in the same change.
  MEASURED: **41 cards across 24 decks**, every one of them previously SKIPPED ENTIRELY by
  the cast-on-curve table (`if not strict: continue`), so they printed no row at all rather
  than a wrong one. 27 were overstated by 5+ points. Worst: deck 14's Long Feng, Grand
  Secretariat (`{1}{B/G}{B/G}`, G=0, B=11) at 100% against a true **52.5%** — and it was
  invisible while its strictly EASIER twin, a `{B}{B}` card off the same 11 sources, was
  flagged at 65.1%. Deck 14's below-90% count goes 7 -> 10.
  **0 of 111 tier floors moved**, verified against a stashed baseline: this feeds probability
  and FLAG surfaces only, and G-32 keeps `pip_depth_warning` a flag, never a score.
BS13-01 | tests/test_deck.py | `test_hybrids_excluded` encoded the OLD blanket rule in its
  name and comment; renamed to `..._while_BOTH_halves_are_live` and joined by three new
  cases pinning the one-dead-half collapse, the no-live-half abstention, and the
  monocolor/Phyrexian exemption.
BS13-02 | scripts/deck.py | Three copula patterns added to `_RATIONALE_FIGURES`
  (interaction / card advantage / protection), with a CLOSED verb list taken from what the
  roster actually writes and a hedge absorber for "only / just / down to / up to".
  G-26 has recorded "a copula hides a figure" as a known residual for a year without anyone
  measuring it. Measured: **23 copula claims on the roster, 6 mismatching** — a 26% error
  rate on the exact axes a tier letter rests on.
  ONE EXCLUSION, and it was earned by the sweep rather than guessed: `_FIG_SPEED_QUALIFIED`
  rejects a number immediately re-qualified by a SPEED word. Deck 26b writes "the interaction
  is 1 instant-speed against 11 sorcery-speed", which is a claim about the interaction
  PROFILE that `stats` splits by speed (G-24), not the axis total. It was the only one of the
  23 whose number is re-qualified, it DID match the new pattern, and only an unrelated
  suppression kept the audit quiet — a false positive waiting to fire, not a rule. Verified
  that the exclusion drops that one and keeps the other 22.
BS13-02 | five deck files | The 5 genuinely stale figures the new patterns surfaced, each
  read IN CONTEXT first to confirm it was a live claim and not a history citation:
  27 card advantage 1 -> 4; 44 protection 2 -> 1; 46 protection 4 -> 3; 56b protection 1 -> 3;
  57 card advantage 5 -> 6. Deck 46's neighbouring "exactly the sum of 7" was CHECKED and is
  still correct (interaction 5 + card-adv 2), so it was left alone.
  TWO needed more than a number. Deck 27's cap rested on "two thin axes" of which one was the
  false figure, so the corrected prose states the arithmetic and is marked RE-GRADE CANDIDATE
  with the letter untouched — the human call, per the design constraint. Deck 56b named
  "(Boots)" as its single protection source against a live 3, so the parenthetical went with
  the number. NO TIER LETTER WAS TOUCHED.

TEST RESULTS: passed. Full suite **1813 passed / 0 failed / 0 skipped** (exit 0), up 3 for
  the new hybrid cases. `check_all.py`: all invariants hold, and the rationale sweep is now
  CLEAN where it had five silent stale figures. `make postedit` exit 0, role baseline
  unchanged. All six decks that the copula sweep implicated report 0 warnings.

REGRESSION RISKS:
- `binding_pips` is NEW; `parse_pips` is untouched, so the other eleven callers (identity
  lint, dashboard pip bars, wishlist) are unaffected by construction. Only the two
  probability surfaces changed behaviour, and both changed in the same direction.
- Was the old behaviour ever correct? For a hybrid with 2+ live halves, yes — and that path
  is unchanged and pinned by the renamed test.
- The copula patterns can only ADD matches, so the risk is false positives. The roster sweep
  found exactly one class and it is excluded; 22 of 23 matches are genuine figure claims.
- Deck-file edits touch `#: tier:` PROSE only. No card line, no letter, no header the
  tooling reads as an instruction (`#: protect:` / `#: uncastable-ok:` untouched).

INVARIANTS AT RISK: None. INV-04 re-verified by `check_all` after the five deck edits; no
  card line was altered, so no `(SET) COLLECTOR#` field was retyped (G-65).

NET SCORE: 2 production fixes − 0 new failure modes = 2
  BS13-01 fired this month by construction — it is why Krang & Shredder had to be
  hand-measured during the deck 45 pass, and it still misreports Krang by ~25 points in decks
  48a and 26b. BS13-02 fired on five roster decks that were silently arguing from wrong
  numbers. Neither introduces a new failure mode; both are narrowed by measurement.

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: N/A for Analysis. The committed dashboard was refreshed by `make postedit`; Pages
  rebuilds on push to main.

FOLLOW-ON ITEMS:
- The hybrid collapse is applied at the two PROBABILITY surfaces. `build_dashboard.py` still
  splits strict/hybrid itself for its pip bars (a DISPLAY of demand, not a probability), so
  its bars still show a zero-source hybrid as unconstrained. Deliberately out of scope — it
  is a different question — but it is now the only surface that disagrees.
- `deck.py mana` prints "N card(s) are hybrid-only — castable with any of their colors",
  which is the wrong reassurance for a deck with zero sources of one half. Not a probability
  surface, so untouched here; it is the sentence that made the deck-14 case look fine.
- The G-26 residuals NOT closed by this: a figure spelled as a WORD ("six of it"), and
  cast-on-curve / keepable PERCENTAGES, which are absent from `_figure_lookup` entirely.
  Measured separately: 9 percentage claims across 8 decks, NONE currently wrong, so this is a
  gap rather than a defect and was left alone.
- Deck 27 is now a live RE-GRADE CANDIDATE and deck 47 and deck 45 remain open tier calls.

DOCUMENTATION UPDATES NEEDED:
- G-32 (`pip_depth_warning`) says "Hybrids are excluded (strictly easier)" — now true only
  while both halves are live.
- G-36 (`consistency`) and the `cast_probability` docstring carry the same premise; the
  docstring was corrected in place but the CLAUDE.md rule was not.
- G-26 should record that the copula residual is CLOSED for the three axes, with the
  speed-qualifier exclusion named, and that the word-spelled and percentage residuals remain.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
