---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- P1 | Fuzzy name resolution in `deck.py resolve` / `screen` — 22 of 111 real names failed to resolve
- P2 | `screen`'s off-color flag read identity, not the printed cost — 8 of 9 flagged cards were castable
- P3 | `screen`'s KEY label fired on 66% of a pile, carrying almost no information
- P4 | `/add-cards` had no step requiring `screen`, so hand-triage was the default path
- P5 | G-58 documented the single-card identity-vs-cost trap but not the bulk-triage one

Files modified:
- scripts/deck.py
- scripts/check_patterns.py
- tests/test_deck.py
- .claude/commands/add-cards.md
- CLAUDE.md
- docs/gotchas.md

CHANGES:
P1 | scripts/deck.py | New `_name_query` (strips trailing `(notes)`), `_squash` (punctuation-
   insensitive match key), `_squash_index` (built once per surface), `_resolve_card_name`
   (exact → DFC front → squashed → unique substring, reporting ambiguity). Wired into BOTH
   `cmd_resolve` and `cmd_screen`, replacing two divergent inline resolvers. `screen` now
   separates "Ambiguous" from "Not found" the way `resolve` always did. Measured on the
   motivating 111-card pile: unresolved 22 → 2 (`Astrologian Planisphere`, missing the
   possessive, and the genuine typo `Impostoer Syndrome`). Typos are still NOT corrected.
P2 | scripts/deck.py | New `_candidate_castability(cost, ident, declared)` → `(castable, note)`,
   read from the PRINTED cost and mirroring `_castability_lint`'s hybrid rules so the two
   cannot drift. `screen` replaces `offcolor=not (ident <= declared)` with it, sorts
   uncastable candidates below castable ones, and prints one of: `⚠ NOT castable — needs X`
   (a real exclusion), `identity has X (hybrid — paid on-color)`, `(off-color ability — still
   castable)`, `(cost unknown …)`. On the pile: 5 identity-based flags → 1 cost-based flag,
   and that one (Iroh, `{3}{G}{U}{R}`) is the only genuinely gold card in the pile.
P3 | scripts/deck.py | `_strong_signature_themes` now requires a GENERIC theme to clear HALF
   the `#: protect:` list; a SPECIFIC theme keeps the flat `>=2` bar. The flat bar was tuned
   against a 3-to-5-card protect list and does not survive a longer one (at 14 protected cards
   `>=2` is 14% of them). Roster measurement before the change: 26 of 33 decks carried a
   signature that was >=50% generic — deck 46 rescued `Human`/`combat`/`flying`, deck 51
   rescued `card draw`/`graveyard`/`mana`/`tokens`. After: 18 decks change, 51 signature
   themes drop, every genuine spine stands (49 keeps `Dragon`, 47 keeps `affinity`/`artifacts`).
P4 | .claude/commands/add-cards.md | New Stage 0b requiring `deck.py screen <id> <pile>` for any
   pile over ~10 cards, naming the hand-rolled `Color(s)` filter as the anti-pattern, and telling
   the reader that `Not found` / `Ambiguous` lines are the ones to act on (a silently-dropped
   name looks exactly like a card that was considered and rejected).
P5 | CLAUDE.md, docs/gotchas.md | G-58 extended with the BULK-TRIAGE variant, including the
   table of all nine mis-sorted cards and the two identity leaks the hybrid framing alone
   does not cover (a TRANSFORM cost and a MANA ABILITY both leak into `Color(s)`). Also records
   that Standard does not restrict by colour identity at all — only Brawl does.

TEST RESULTS: 744 passed (was 725; +19 new across TestNameResolution, TestCandidateCastability,
TestGenericSignatureBar). `check_all.py` — all invariants hold. `check_suggest` OK,
`check_agreement` OK, `check_patterns` OK after registering the two new NAME regexes in
`_EXCLUDED` with reasons. `deck.py --help`, `screen --help`, `resolve --help` all clean (G-55).

REGRESSION RISKS:
- P3 changes a SHARED primitive with six callers (`cuts`, `similar` ×2, `screen`,
  `suggest-homes`, the quality vector). Blast radius measured per K-12 across 4,440
  (deck, card) fit judgements: KEY 13% → 8%, 223 labels changed, and ALL 223 ran
  KEY → weaker. No card gained a KEY anywhere, so the change is strictly tightening.
  The residual risk is a genuine spine on a long protect list now reading weaker; deck 51
  keeps only `cost-reduction`, which is defensible but is the case to re-check first.
- P1 could in principle mint a WRONG match where the old code reported nothing. Mitigated
  by deduping on DISPLAY name (a DFC's front and full name are one card, not an ambiguity)
  and by refusing typo correction; `test_a_typo_is_reported_not_guessed` pins that.
- CAUGHT DURING THE WORK: the new castability helper was first named `_castability`, which
  SHADOWED the existing `_castability(cards, declared, mana, carddata)` and broke 15 tests
  plus two check_all gates. Renamed to `_candidate_castability`. Worth noting because the
  failure was loud — a silent shadow of a 4-arg function by a 3-arg one would not have been.

INVARIANTS AT RISK: None. No writer touched; INV-01…06 unaffected. The only data files read
are `card-pool.csv` / `card-mana.csv` / `card-library.csv`, all read-only on these paths.

NET SCORE: 5 production fixes − 0 new failure modes = 5
(a) Would each have fired this month? P1 YES, P2 YES, P3 YES — all three fired on the deck-51
    pile in this cycle and produced nine mis-classified cards. P4/P5 are process fixes for
    the same incident. (b) New failure modes introduced: none documented; the P3 residual
    above is a tightening, not a new class of error.

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push. No dashboard template or `#data` island
was touched, so the Pages rebuild is a no-op here.

FOLLOW-ON ITEMS:
- `card-mana.csv` stores only the FRONT face cost of a MODAL double-faced card. Bruce Banner
  is recorded as `{U}` and Norman Osborn as `{1}{U}`, but Scryfall reports `layout:
  modal_dfc` with a real `mana_cost` on BOTH faces (`{2}{R}{R}{G}{G}` and `{1}{U}{B}{R}`) —
  either face is castable from hand. Rooms and splits DO store two costs (`{2}{U} //
  {5}{U}{U}`), so the gap is specific to modal DFCs keyed under a single name. This was
  found by checking a rules question against Scryfall and it caused a wrong answer in chat
  ("the back faces are unreachable"). `build_mana.py` needs to record both faces, and the
  432 two-faced rows currently holding one cost need auditing to separate the transform
  DFCs (one cost is CORRECT) from the modal ones (one cost is a data loss). Out of scope here.
- `screen`'s KEY at ~9% on a broad pile may now be too selective. It is honest — the pile
  really was mostly tangential to deck 51 — but the label has not been calibrated against a
  pile that was pre-filtered for one deck. Worth a second measurement next cycle.
- `_squash` matching is O(cards) per surface at index-build time and fine at current scale;
  no action.

DOCUMENTATION UPDATES NEEDED:
- Done in this session: CLAUDE.md G-58 (bulk-triage variant), docs/gotchas.md G-58 long form,
  .claude/commands/add-cards.md Stage 0b.
- README's `screen` description does not mention the castability note or the resolver; a
  `/sync-docs` pass should pick it up.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
