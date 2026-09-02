---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS8-27 Blink ("exile target creature you control, then return it") classified as spot removal
- BS8-30 `classify_roles` read reminder text that its own audit net (`role_coverage_flags`) strips
- BS8-10 Reanimation fired without a graveyard reference (297/655 pool) and missed keyword recursion (60)
- BS8-11 Sweeper unscoped ("exile all graveyards/cards/spells", -N/-0 shrinks)
- BS8-29 Cost reduction credited a card discounting itself (263/810)
- BS8-28 Verified interaction / counter / card-advantage whitelist misses (~150 pool cards) + loot shapes
- BS8-13 (R-13) Protection counted self-pump
Files modified: scripts/deck.py (patterns, `_norm_role_text`, `_LOOT_RE`, `_NOT_OWN_OR_CARD`), scripts/check_patterns.py, scripts/role_baseline.txt, scripts/tag_role_baseline.txt, tests/test_deck.py (one fixture), dashboard.html (rebuilt), 22 deck files (35 prose figures re-numbered to the live counts — see REGRESSION RISKS)

CHANGES:
BS8-30 | deck.py `_norm_role_text` | strips `_REMINDER_RE` before every role pattern (the form `role_coverage_flags` already used). Treasure/Food/delve/"End the turn" reminders no longer create Ramp/Lifegain/Recursion/Sweeper roles. check_patterns: the two reminder strippers re-registered against the RAW corpus (they match nothing in the stripped norm form by design); one Payoff pattern whose only matches crossed reminder text went dead and was removed.
BS8-27/28 | deck.py Removal (spot) | shared tail `_NOT_OWN_OR_CARD` = not "you control/own" (blink) and not "card" (graveyard hate) on both targeted-removal patterns; comma qualifier admitted; `-X/-X` auras; plural "owners' hands"; edicts generalised (two/three/X/half, nontoken/nonland); library tuck (top/bottom/second from the top).
BS8-11/28 | deck.py Sweeper | "destroy/exile all" scoped away from cards/graveyards/spells/hands; -N/-0 excluded; added "destroy/exile each creature", "X damage / damage equal to … to each creature", "each player sacrifices all/two/X".
BS8-28 | deck.py Counter | "exile/return target spell", "counter all/each spell".
BS8-28 | deck.py Card advantage + `_LOOT_RE` | impulse with the window first; trigger-cost draw across a period (rummage excluded); discard-first and period-form loots recognised ONLY at equal counts ("Draw three. Discard a card" stays advantage — pinned by the existing test that caught the first draft).
BS8-10 | deck.py Reanimation | graveyard required in the clause (in/from … graveyard … to the battlefield); "return this from your graveyard to the battlefield"; keyword forms unearth/embalm/eternalize/encore/disturb/escape/persist/undying.
BS8-29 | deck.py Cost reduction | `(?<!this spell )(?<!this ability )costs? … less`.
BS8-13 | deck.py Protection | `(?<!this creature )(?<!this permanent )gets +N/+N until end of turn`.
Pool counts (before → after): Removal 2390→2383 · Sweeper 267→285 · Counter 222→238 · Card advantage 1370→1380 · Reanimation 655→471 · Cost reduction 810→469 · Protection 1505→1148 · Ramp 1634→1355 · Recursion 1456→1185 · Lifegain 1494→1400 · Payoff 2553→2408.
Roster: 45 decks change interaction or card advantage; floor moves: 9 B→A (claimed A), 17 C→B, 42a/55b/70 B→A (claimed B), 23 B→C, 27/68/68a/78 A→B, 41 A→C (all claimed B) — zero ≥2-band mismatches; floor spread 63 A / 43 B / 9 C.
Baselines: `check_roles --update-baseline --max-new 130` acknowledged 119 new zero-role deck cards (blink spells, self-pumpers, Treasure makers — sampled, all genuinely roleless under the corrected read) and pruned 4 stale entries (Beetle-Headed Merchants, Glen Elendra's Answer, Jecht, Rush of Dread now classify); `--update-tag-baseline` re-acknowledged the tag/role worklist.

TEST RESULTS: passed — full suite green with PYTEST_NO_SKIPS=1; check_all all invariants hold, only the G-75 soft warning after `make dashboard`. Mid-batch failures, all mine and fixed: the first loot draft swallowed "Draw three. Discard a card" (caught by the existing pin); `its controller sacrifices it` matched 0 pool cards and was dropped; the reminder-test fixture ("sacrifices a nonland permanent") is now correctly classified, so the fixture moved to "sacrifices an enchantment"; the figure sweeps flagged 35 prose figures computed under the old classifier.
REGRESSION RISKS:
- 35 `#: tier:` / `#: archetype:` / `#~ note:` FIGURES in 22 deck files were re-numbered mechanically to the live counts (e.g. deck 27 "interaction 8" → 4, deck 41 7 → 3, deck 78 8 → 6). The surrounding ARGUMENTS were not rewritten: several still say a count "clears the threshold of five" (the A floor is now 7) or carry a breakdown clause ("6 removal + 2 sweepers") the audit cannot see. These are human arguments and need a human read — listed in FOLLOW-ON.
- Reminder stripping is global to every role: a card whose ONLY text is a keyword plus reminder keeps the keyword (e.g. `ward`, `lifelink`), but any pattern that relied on reminder wording is now blind by design.
- The strict Reanimation form drops blink/land-drop/cheat-from-hand credit in `cuts`/`suggest` for 64 decks (intended); `redundancy` buckets shrink accordingly.
- Extra-cost/self-discount exclusions use fixed-width lookbehinds; "it costs {1} less" (a pronoun subject) is still counted.
INVARIANTS AT RISK: None (deck prose edits only; INV-04 verified by check_all).
NET SCORE: 6 − 0 = 6
(BS8-27, 30, 10, 11, 29, 28 all fire on every `cuts`/`tier`/`stats` run this month; BS8-13 is the seventh but Protection is report-only — counted 6. No new failure mode found; the prose re-numbering is a review item, not a failure mode.)

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: Presentation — pages.yml republishes the dashboard on push to main (snapshot rebuilt).

FOLLOW-ON ITEMS:
- HUMAN READ of the 22 deck files whose figures were re-numbered (git diff decks/): the tier ARGUMENTS around them (threshold clauses, breakdowns) may now be wrong in substance — G-27 keeps arguments out of the audit on purpose.
- Deck 41's floor is now C (interaction 3) against a claimed B — one band, no flag, but worth a look; decks 42a, 55b, 70 now floor A against claimed B (the under-grade nudge will fire unless their prose argues the cap).
- Burn/drain misses "target player" (80 pool cards) and Ramp misses (basic fetch 98, rituals 51, extra land drops 30) were measured in the scan and left out of scope: neither feeds the floor.
- `check_roles --tags` worklist re-baselined at its new size; the tag-side removal/sacrifice/ramp false positives (BS8-31) are batch 5.
- Tier prose that argues from "clears the threshold of five" predates BS8-06's A floor of 7 — the same human-read item, one cause over.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-67 / K-12 / K-09: reminder text is stripped in `_norm_role_text` (one form for classifier and net); the Reanimation strict form; blink/graveyard-hate guards.
- docs/gotchas.md G-67 long form: this batch's measured before/after table.
- README `stats`/`tier` prose if it names the old Reanimation or Sweeper behaviour.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
