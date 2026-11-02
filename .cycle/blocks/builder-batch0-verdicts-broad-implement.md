---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch 0 of .cycle/builder-picks-plan.md — per-deck verdict stars
- 0a: per-deck verdicts in build.json, `builder.py verdict` (single or --file), check summary, derive fields
- 0b: imported the 250 §4 grades from .cycle/sultai-pile-analysis.md as pre-draft (500 verdicts)
- 0c: graded the 176 unstarred cards for both decks and re-graded 33 Elf-leaning Thranduil grades under the owner's synergy-first rule (385 verdicts), with reasons
- 0d: page — star chip per deck on rows, verdict beside each deck in the pane with a legend, verdict filter, verdict sort
Files modified: scripts/builder.py, scripts/builder_template.html, builds/sultai/build.json, tests/test_builder.py, tests/test_builder_template.py, .cycle/sultai-pile-analysis.md (§11), .cycle/board/index.html, CLAUDE.md (G-89, one sentence), README.md, .claude/commands/pile-analysis.md

CHANGES:
0a | scripts/builder.py | VERDICTS legend (★★★ ★★ ★ ◇ △ ✗) with aliases (3/2/1/s/m/x, take/strong/real/situational/marginal/out); `set_verdict` stores {mark, graded_at = that deck's list hash} per card per deck under a top-level `verdicts` map (not on reasons, as the plan first said: a reason covers both decks, a verdict is one deck's and goes stale on its own); `pre` stores graded_at None. `verdict` CLI validates every line of a --file before writing any. `check` adds one summary line per deck (no verdict / pre-draft / stale) — never a strict failure — plus orphan verdicts. `derive` emits `vd` {deck: mark} and `vs` {deck: pre|stale|""}, and meta.verdicts (the legend).
0b | builds/sultai/build.json | 250 cards × 2 decks from §4's A (→ Thranduil) and B (→ Glarb) columns, all resolved, recorded pre-draft.
0c | builds/sultai/build.json, .cycle/sultai-pile-analysis.md | Five parallel readers graded from full oracle text against both live lists (brief: §1 framework, §10 synergy-first rule, G-42 with the owner's Sin exception, ownership irrelevant). 352 grades for the 176 cards, 33 Thranduil re-grades (14 changed: up — Leader, Super-Genius, Wrenn and Seven, Yawgmoth, Ezuri, Furgul, Krydle, Nael; down — Aclazotz, Black Widow, Uchbenbak, Gisa, Malcolm, Pharaoh Rama-Tut, Celeborn). 101 cards with no reason got one (clause + per-deck why); the 33 re-graded reasons now LEAD with the re-grade and keep the old text as "Earlier:" — the row preview shows a reason's start, so an appended note left the void Elf-first argument on screen. The readers' tables are §11 of the analysis doc, verbatim.
0d | scripts/builder_template.html | Row chip "T ★★" per graded deck (dotted border = pre-draft, dashed = stale, title explains); pane shows each deck's verdict beside its Add/Bench/Keep out row plus a legend line; toolbar "Verdict" filter per deck (★★ or better / ★ or better / ◇ or worse / none); Sort gains "Verdict — <deck>" (ungraded last, then name).

TEST RESULTS: full pytest suite passed (rc=0), incl. 4 new TestVerdicts tests (aliases, set/clear/pre, derive+check stale and pre-draft, CLI validates before writing) and a Node test of the page's vrank/vfMatch against builder's legend. check_all OK, 6 soft — the new one is `builder sultai: 259 reason(s) written against an older deck list`, caused by the nine Thranduil swaps applied earlier the same day (commit 3218c87), not by this batch. Browser walk: Thranduil pile sorted by verdict, ★★-or-better filter, pane legend — no page errors.
REGRESSION RISKS: (1) derive now calls current_hashes() once more per render (two deck parses). (2) A build with no `verdicts` key renders as before (vd/vs empty). (3) The verdict filter's optgroups list every deck — with many decks the select grows; fine at 2–3.
INVARIANTS AT RISK: None — no canonical CSV or deck file written; build.json through atomic_write.
NET SCORE: 0 production fixes − 0 new failure modes = 0. New capability; the re-grade corrected 14 Thranduil grades the owner's rule made wrong (data, not code).

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation: `.github/workflows/pages.yml` publishes the Builder pages on the next merge to main; the claude.ai board is republished (artifact v21).

(Not complete in production until blocking operator actions are done AND
the deploy step is confirmed.)

FOLLOW-ON ITEMS:
- 259 sultai reasons predate the nine Thranduil swaps — re-read (not re-stamp) the Thranduil halves, especially cards the swaps touched.
- 217 Thranduil and 250 Glarb verdicts are still pre-draft (§4 grades from before either deck was drafted); a re-grade pass against the live lists would retire the dotted border.
- Readers' notable calls worth the owner's eye: Damnation △ for Thranduil (wipes the mana Elves), Marwyn ★★★ (Thranduil borrowing her ability reads his own power), Deathrite Shaman only ★ for Glarb (exiling their yard shrinks Drown in the Loch).
- Next plan batch: A (cut picker with previews, compare inspect slot, package view, "needs a cut").

DOCUMENTATION UPDATES NEEDED:
- None beyond what landed (G-89 sentence, README command, /pile-analysis Stage 3 verdict step).
---END BROAD SCAN IMPLEMENTATION SUMMARY---
