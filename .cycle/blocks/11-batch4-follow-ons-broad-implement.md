---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented (the Batch 4 follow-ons, block 11-batch4-tagger-accuracy-broad-implement.md):
- FO-1 — a tribe missing from the embedded type list was silently untagged on its payoffs: now surfaced by a soft radar
- FO-2 — "Merfolk / Kithkin / Mice you control" (non-`s` plurals) never reached the tribal resolver
- FO-3 — `tag_synergies --merge` cannot remove a stale library tag: DECLINED (see below)
- FO-4 — K-09's pool-blank figure drifted 348 → 350

Files modified: scripts/tag_synergies.py, scripts/check_keywords.py, scripts/check_all.py,
tests/test_ingest.py, CLAUDE.md (K-09 figure), card-pool.csv + card-pool.build (re-derived),
card-library.csv (--merge, 1 row), gallery.html, dashboard.html

CHANGES:
FO-1 | check_keywords.py, check_all.py | `check_keywords.unknown_subtypes()` lists every subtype on a pool Creature/Kindred/Land/Artifact/Enchantment face that `tag_synergies._TRIBE_VOCAB` lacks; check_all reports each as a SOFT warning beside the keyword radar (a new set is a data refresh — hard would be the G-69 trap). Live pool: 0 unknown today.
FO-2 | tag_synergies.py | `_INVARIANT_PLURAL_TRIBES` (Merfolk, Kithkin, Moonfolk, Treefolk, Eldrazi, Samurai, Kor, Djinn, Efreet, Fish, Sheep, Jellyfish) join the "Xs you control" template; `_IRREGULAR_PLURALS` maps Mice→Mouse, Oxen→Ox in `_resolve_tribe`. Pool: 5 cards gain their tribe (Deeproot Pilgrimage, Valley Questcaller, Godo, Path of Annihilation, Bruse Tarl). Ninja/Phyrexian deliberately excluded (their plurals take an `s`).
FO-3 | — | DECLINED, not implemented. `--merge` cannot tell a stale auto-tag from a hand-curated one, which is exactly why it only adds (K-09, INV-06); the pool is the corrected store and every model, card.py and the gallery read it first. Batch 4 removed the one KNOWN class of junk (the invented tribes) by name.
FO-4 | CLAUDE.md | K-09 residual 348 → 350 (the figure-drift soft warning cleared).

TEST RESULTS: passed — full pytest suite green; check_all OK; 2 new tests (TestScan11TaggerFollowOns), including the radar firing on a planted unknown type.
REGRESSION RISKS: the subtype radar reads card-pool.csv per check_all run (one file pass, ~16k rows; negligible). A singular "X you control" reference (e.g. "a Dragon you control", 492 tags if widened) is still not captured — measured and left out of scope, see follow-ons.
INVARIANTS AT RISK: None.
NET SCORE: 2 − 0 = 2 (FO-2 real tags gained; FO-1 defensive, measured 0 today; FO-4 docs)

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — pages.yml rebuilds the dashboard on push to main (committed copy rebuilt).

FOLLOW-ON ITEMS:
- SINGULAR tribal references ("Whenever a Dragon you control attacks", "a Samurai or Warrior you control") are a pattern hole of their own: widening template 1 to singulars adds 492 pool tags across ~100 types (Army 59 of them via amass reminder text). G-67 triage: a widening that needs its own measured pass, not a follow-on fix.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md C-01 / check_all list: name the subtype radar beside the keyword radar.
- The Batch 4 doc items (tagger fixes, canonical tag case) are still pending /sync-docs.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
