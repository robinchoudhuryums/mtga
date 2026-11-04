---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: the two backlog items the owner chose on 2026-11-02:
  A. Card-draw shapes the role classifier missed (G-67 pattern holes, K-12)
  B. Keyword themes for the six keywords baselined 2026-11-01 (K-01), with an enchantments theme built so constellation has one to map onto
Files modified: scripts/deck.py, scripts/tag_synergies.py, scripts/check_patterns.py, scripts/keyword_baseline.txt, scripts/role_baseline.txt; card-pool.csv, card-library.csv, card-mana.csv (one row), gallery.html, dashboard.html (make refresh / make postedit); 18 deck files (tier prose figures); CLAUDE.md (K-01, K-09 figure, K-12, K-15); docs/gotchas.md (K-01, K-12, K-15 long forms); tests/test_deck.py, tests/test_ingest.py; .cycle/STATE.md

CHANGES:
A | scripts/deck.py | Seven Card-advantage changes. Each was measured on the pool before it landed: 64 cards gained the role, none lost it.
  - `draws? (six|…|ten) cards` (23: Jin-Gitaxias, Griselbrand, the draw-seven wheels)
  - `draws? an additional card` (8: Dictate of Kruphix, Howling Mine, Midnight Oil)
  - `instead … you draw a card` (2: Notion Thief, Leader, Super-Genius)
  - `you may play the exiled cards` (1: Black Cat, Cunning Thief)
  - The phase-trigger MODE pattern reads "combat on your turn" and a "hasn't been chosen this turn" reset (2: Glorious Sunrise, Shadrix). It still excludes Zuko's once-a-game form.
  - A new WHENEVER-trigger mode pattern (7: Elder Gargaroth, Galadriel, Kastral, The Vision). It excludes a rummage mode (Territorial Kavu) and a sacrifice-to-choose trigger (Gorbag).
  - The whenever condition window goes 80 → 120 (21: Tidus, Haliya, Kutzil); the effect window is unchanged.
A | 18 deck files | Before/after roster diff: 37 decks' card advantage rose by 1–3, 0 tier floors moved, 0 errors. Every `#: tier:` / `#: archetype:` / `#~ note:` card-advantage figure the audit named was re-grounded to the live count (stale tier rationale 18 → 0). Two sentences changed meaning and were rewritten:
  - deck 87's "Leader and Black Cat score no role";
  - 78-historic-brawl's "losing two interaction or card-advantage cards puts the floor back at B", which is now interaction only, since the sum has three to spare.
B | scripts/tag_synergies.py | `_ENCHANTMENT_MATTERS_RE`, an `enchantments` mechanic rule (K-15's artifacts rule one card type over).
  - Same guards: no hate templating, either-type guards, the enters anchor.
  - One new guard: the count span cannot cross a comma. The first draft hit Volatile Orbit's "if you control a Planet, this enchantment".
  - 101 pool cards, 0.63%.
  - KEYWORD_THEMES: constellation → enchantments·payoff, battalion → go-wide·aggro, seek → card draw.
B | scripts/keyword_baseline.txt | constellation, battalion and seek removed. ascend (counts permanents), conjure (Alchemy creation) and partner (deckbuilding only) stay baselined.
B | data | `make refresh`: the tagger hash staled the pool and it was rebuilt. 209 pool rows changed Synergies, additions only (enchantments 101, card draw 99, payoff 16, go-wide 6, aggro 5, plus Mjölnir's `equip` from a one-row keyword fetch). `make postedit`: dashboard rebuilt, role baseline pruned 12 stale entries (the cards this batch now classifies).
gate | scripts/check_patterns.py | `_ENCHANTMENT_MATTERS_RE` registered ("norm"). check_all had hard-failed on it, which is what the gate exists to catch.
docs | CLAUDE.md, docs/gotchas.md | K-12's dated log moved to its long form (291 → 228 words) with the 2026-11-02 entry. K-01 and K-15 record the triage and the enchantments twin. The K-09 pool-blank figure is 351 → 349 (figure_drift caught it).
tests | tests/test_deck.py, tests/test_ingest.py | TestCardDrawHoles20261102 (10 real-text positives, 3 real-text negatives) and TestEnchantmentsThemeAndKeywordTriage (enchantress positives, hate and Volatile Orbit negatives, the keyword map, the baseline).

TEST RESULTS: passed. Full pytest suite green; check_all OK, 5 soft (the same five as at session start: owned counts, a wishlist printing, 4 pre-existing flex-note figures in decks 24/28/50, dead library searches, castability).
REGRESSION RISKS: The tags feed cuts/suggest/centrality, so recommendations re-rank for decks holding enchantments-tagged or seek cards; this was not measured as a cuts top-3 diff. The tier floor reads roles, not tags, and its diff is 0. The wider whenever window could admit a long granted-ability condition; the 21 gains were hand-read and all real.
INVARIANTS AT RISK: INV-03 (derived files keep their schema): the pool was rebuilt by its own builder, and check_all is green. INV-06 (tags regenerated after the tag edit): done through `make refresh`.
NET SCORE: 2 production fixes − 0 new failure modes = 2 (the card-advantage under-count fired on 37 live decks; constellation/battalion/seek were tagless on live pool cards)

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds the dashboard on push to main

FOLLOW-ON ITEMS:
- "Ajani, Unyielding +2" from the 2026-11-01 note is not in the pool under that name; nothing to measure.
- The if-clause whenever pattern still has an 80-character condition window. Widen it only after measuring it on its own.
- A `cuts` top-3 diff for the new tags was not taken.
- Four pre-existing flex-note figures (decks 24, 28, 50) are still stale.

DOCUMENTATION UPDATES NEEDED:
- None beyond what landed (K-01, K-09, K-12, K-15 and their long forms)
---END BROAD SCAN IMPLEMENTATION SUMMARY---
