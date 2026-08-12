---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS5-04 (B1) | Buildability was re-derived in three more places despite G-70's "one
  definition"; two keyed on the raw display name where the canonical helper keys lowercase
- BS5-11 (B2) | `build_mana`'s alias merge could write one card's mana cost onto another's row
- BS5-12 (B3) | RETRACTED — false finding, see below. No change made.
- Batch A (A1/A2/A3) | NOT IMPLEMENTABLE HERE — operator actions. A1's install block was
  verified end-to-end instead.

Files modified: scripts/deck.py, scripts/build_dashboard.py, scripts/build_mana.py,
scripts/check_agreement.py, tests/test_build_mana.py, dashboard.html (rebuilt)

CHANGES:

BS5-04 | scripts/deck.py, scripts/build_dashboard.py, scripts/check_agreement.py |
  Three surfaces now route through `deck_requirements` / `deck_build_gap`:
  * `cmd_list` — its hand-rolled loop keyed the per-name aggregation on the raw DISPLAY
    name, so two lines differing only in case would not have summed there while `check`
    summed them. It also folded missing and short into one "N short" label; the two are
    reported separately now, so `deck.py list` and `deck.py check` describe a deck the same
    way (deck 44 read "12 short" and now reads "12 missing", matching `check`).
  * `deck_quality_vector` — same raw-display-name key, on the number that feeds
    `preflight`'s READY/BLOCKED verdict and `quality --vs`'s "became UNbuildable" flag.
    The basics special-case went with it: `owned()` already reports a basic as unlimited,
    which is why `deck_build_gap` never needed one.
  * `build_dashboard.collect` — counts from `deck_build_gap`; the per-card copies-short
    list (which no shared helper provides, since nothing else needs it) now walks the same
    `deck_requirements`, so it cannot disagree with the counts about what the deck needs.
  Plus `_agree_buildability` in check_agreement.py — the gate built for "two functions
  answering the same question" had no pair for the question with the worst drift record in
  the repo. It checks three things: a synthetic split-line deck (2+2 of a card owned 3 is
  SHORT — the case no roster deck exercises, so a roster-only check cannot see it), a
  two-casings deck (the exact axis all three re-derivations got wrong), and every roster
  deck's summary against a fresh walk of the canonical requirements. It also asserts the
  per-line CONTROL still disagrees, so the pair cannot go vacuous.

BS5-11 | scripts/build_mana.py, tests/test_build_mana.py | The front-face aliasing moved
  out of `fetch()` and onto the MERGED table in `main()`. `alias_front` guarantees it will
  not shadow a real row — but only within the dict it is handed, and `fetch`'s output does
  not contain the already-resolved `reuse` rows, so a newly fetched `Life // Death` emitted
  an alias under `life` and `data.update()` wrote it over the real card named Life.
  Demonstrated before/after: pre-fix `Life -> ('{B} // {1}{B}', …)`, post-fix
  `Life -> ('{G}', …)` with the DFC intact under its own key. The aliasing is load-bearing
  and is NOT removed — the library stores most DFCs under the front name while the pool
  stores `A // B`, so both spellings reach the write loop and the front one needs a value
  or the card writes out BLANK; a pin covers that direction too.

BS5-12 | (no change) | RETRACTED. `collection.html` already joins the row key with
  `'\x01'` (U+0001), a control character that cannot occur in a CSV cell, so the key is not
  ambiguous. I misread `join('\x01')` as `join('')` because the Read tool renders a raw
  0x01 byte invisibly — and then "confirmed" it with a Python collision check that
  reproduced my MISREADING (`name + set + cn`) rather than the code. Worth recording: the
  measurement looked like verification and was actually a second copy of the assumption.
  The proposed fix would have made things WORSE — joining on a space, as I intended, is
  genuinely ambiguous, because a space can appear in a card name.

Batch A | (no change) | A1 (launchd archive), A2 (`import_collection.py` against a real
  tracker export) and A3 (the two operator visual checks) are all human-only: A1 needs
  `launchctl` on the Mac running Arena, A2 needs an export file only the owner has, A3
  needs a person at a browser. What WAS done is verifying the A1 artifact so the install is
  not a wasted session: the Stage 0 snapshot script was run end-to-end against a synthetic
  `Player.log` tree on this box — run 1 creates the archive (4 lines), run 2 is idempotent
  (still 4), and run 3 after an Arena relaunch that WIPES `Player.log` preserves the old
  lines and appends the new match (6 lines), which is the exact property the archive exists
  for. The plist parses (`plistlib`) with sane fields, and the resulting archive feeds
  `parse_matches.py` cleanly, resolving both deck headers. The block is correct as written.

TEST RESULTS: passed. **1270 tests collected, full suite green.** `check_all.py`: all
invariants hold, ZERO soft warnings. `check_agreement.py` reports 7 questions (was 6) and
passes. +4 tests: 3 new pins in test_build_mana.py, and test_check_agreement.py's
`@parametrize("fn", ca.PAIRS)` picked up the new pair automatically. The new pair was
watched FIRING — regressing `deck_build_gap` back to the per-line shape raises 3 errors.

REGRESSION RISKS:
- `deck.py list`'s status column CHANGED WORDING for decks with missing cards ("12 short" →
  "12 missing"). That is the fix — it now agrees with `check` — but it is a user-visible
  string, and anything parsing `list` output would see it. Nothing in the repo does.
- `build_mana.fetch()` no longer returns front aliases. It has one production caller
  (`main()`, updated) and three tests, none of which relied on aliasing. A future caller
  that assumes the old shape would silently get blank rows for front-spelled names — the
  docstring says so explicitly.
- `deck_quality_vector` now counts basics through `deck_build_gap` rather than skipping
  them. Behaviourally identical (`owned()` returns 99/unlimited for a basic) and verified
  across the roster, but it is a widened input set rather than a pure refactor.
- Verified no live divergence: all 101 roster decks produce identical `missing`, `short`,
  `buildable`, `wc`, `wcBy`, `craft`, `viz` and `audit` values before and after.

INVARIANTS AT RISK: None. INV-01/02/04/05/06 untouched — no CSV or deck file was written.
INV-03 re-verified by check_all. `card-mana.csv` was NOT regenerated: BS5-11 changes only
WHERE the alias pass runs, the current file has zero genuinely-distinct front-name
collisions, and regenerating it needs Scryfall egress — the next `make refresh` will
rewrite it through the corrected path. dashboard.html was rebuilt; the only field that
moved is `delta_windows`, because the 7-day git base slid overnight (2026-07-29/08-04 →
08-04), which is a calendar effect and not a consequence of any edit here.

NET SCORE: 2 production fixes − 0 new failure modes = 2
(Neither would have fired this month: BS5-04 needs a deck spelling one card two ways, and
BS5-11 needs a distinct card sharing a DFC's front name — measured at 0 live instances
each. Both are fixed on the MECHANISM per G-63, which is why they were batched. The third
item in the batch turned out not to be a bug at all.)

OPERATOR ACTIONS / DEPLOY:
- **A1 — install the launchd rolling archive** (`.claude/commands/log-matches.md` Stage 0).
  Verified correct here; still needs running on the Mac. `Player.log` is overwritten on
  every Arena launch, so every unextracted session is lost until this exists. Verify with
  `~/mtga-logs/snapshot.sh && wc -l ~/mtga-logs/arena.log`; a zero count most likely means
  macOS is withholding Full Disk Access from `/bin/sh`. | BLOCKS DEPLOY: N
- **A2 — run `import_collection.py` against a full tracker export.** Five ownership counts
  were wrong on 2026-08-09, one load-bearing in a recommendation, and nothing in the
  toolchain can detect it. Should precede any wildcard spend. | BLOCKS DEPLOY: N
- **A3 — the two visual checks** now scheduled in Regression Scenarios 5 and 7 (gallery
  light mode; keyboard walk of the two repaired dashboard controls). | BLOCKS DEPLOY: N
Deploy: Presentation — `.github/workflows/pages.yml` rebuilds build_dashboard.py and
publishes to Pages on every push to main. Data + local tooling ship by commit/push. The
committed dashboard.html snapshot was rebuilt in this session.

(Not complete in production until blocking operator actions are done AND the deploy step is
confirmed. None of the three operator actions blocks deploy.)

FOLLOW-ON ITEMS:
- `cmd_check`'s summary lines join card names with `", "` while card names CONTAIN commas
  ("Tinybones, Bauble Burglar"), so "12 not in library: …" reads as 16 names. The repo
  already knows this rule — `#: protect:` uses `;` as its separator precisely because
  "card names contain commas" — and the same fix applies here. Noticed while verifying
  BS5-04, out of scope for it.
- `launchctl load` in the Stage 0 block is deprecated on macOS 11+ in favour of
  `launchctl bootstrap gui/$(id -u) <plist>`. It still works (with a warning), so the block
  is not broken; worth modernising the next time that file is touched.
- Batch C (determinism gate, a11y scan over the generated pages, BS5-07), Batch D (BS5-06,
  BS5-08, BS5-09, retire docs/tooling-improvement-plan.md) and Batch E (strategic) are
  untouched and remain as prioritised.

DOCUMENTATION UPDATES NEEDED:
- G-70's bullet says buildability has "one definition" and names the surfaces BS4-13
  consolidated. It should record that three MORE were still re-deriving it when the rule
  was written, that the axis they got wrong was the KEY (raw display name vs lowercase),
  and that the question now has an agreement pair rather than only a convention.
- The BS5-12 retraction is worth a line somewhere in the scanning guidance: a measurement
  that reproduces your reading of the code verifies the reading, not the code. Read the
  BYTES when the finding is about a delimiter.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
