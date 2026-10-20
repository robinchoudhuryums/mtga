---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Brawl tooling plan Batch 7. Section placement is AUTOMATIC by default,
with a warning when it cannot be decided. This was the owner's call (2026-10-20) and changes G-05.
Files modified: scripts/deck.py, scripts/check_patterns.py, tests/test_deck.py

CHANGES:
Batch 7 | scripts/deck.py | Header CLAIMS are read from the header's HEAD only.
  - `_section_claims` reads the text before a dash, paren or colon, split on `/ + , & ; and`,
    using the label tables `_SECTION_TYPE_LABELS` / `_SECTION_ROLE_LABELS`. A head with any
    unknown piece claims nothing.
  - This replaces the substring table `_SECTION_EXPECTATIONS`, which was removed along with
    its check_patterns exclusion.
  - Measured on the roster's 5,439 existing placements: a substring reading called 260 of
    them misfiled, mostly the header's DESCRIPTION talking ("# Lands-from-graveyard
    engine", "# Interaction / tricks"). The head-only reading flags 57: 13 type misfits,
    all real misfiles, and 44 role misfits.
Batch 7 | scripts/deck.py | `section_fit(header, card, carddata)` returns (verdict, reason,
  kind). It is the ONE definition behind `section_mismatch` and `auto_section`.
  - Type claims (Lands / Nonland / Creatures / Noncreature / Planeswalkers) use the
    front face's type line.
  - Role claims are unioned within a group; type and role groups are joint.
  - A role the classifier cannot read is soft (None), not a misfit.
Batch 7 | scripts/deck.py | `auto_section(lines, idx, card, carddata)` plans placement.
  - It MOVES only on an objective TYPE misfit with exactly one typed header that fits.
  - It also moves a LAND outside any land header to the deck's one land header, since a
    role header like "# Ramp" also fits a land by role.
  - A ROLE misfit (K-12 heuristic) WARNS and names the candidate headers.
  - Ambiguous or absent targets warn.
  - Roster replay: 4 of the 5,439 existing placements would move, and all 4 are
    objectively misfiled: 35a Capital City and Captivating Cave sit under a spells
    header; 37a Hawkeye and Unsparing Boltcaster sit under "Noncreature".
Batch 7 | scripts/deck.py | Wrapped headers are ONE section.
  - `_section_headers` coalesces adjacent `#` comment lines; `full=True` gives the
    block's text, which is what needle matching reads.
  - `_card_section_header` climbs to the block's first line.
  - Without this, the first roster replay planned to move 73 lands out of the section
    they were already in. Their header wraps, and each continuation line read as its
    own header.
Batch 7 | scripts/deck.py | `_relocate_to_header(lines, card, header_index)` was split out
  of `_relocate_card_line`. The auto target is a header INDEX, because a header's full
  text can be a substring of another's.
Batch 7 | scripts/deck.py | `_place_swapped_line` is shared by `swap --apply`, the dry run,
  `apply-flex` and `--package`.
  - An explicit `--section` wins.
  - A planned move is applied before the write, inside the same try, and printed
    "↪ section: placed under `# X`". The dry run prints "will place under".
  - Undecidable cases print the existing ⚠ with the `deck.py move` remedy.
  - New `swap --keep-section` opts out of the move and keeps the warning. It conflicts
    with `--section`, and `--package` refuses it.
Batch 7 | scripts/check_patterns.py | The two label tables are listed in `_EXCLUDED`
  (they run over `# section` header prose, not card text). The stale
  `_SECTION_EXPECTATIONS` entry was removed.
Batch 7 | tests/test_deck.py | `TestAutoSection`, 13 tests:
  - head-only claims; Nonland is not land; role union
  - type move; role warns; ambiguous target warns; a silent header plans nothing
  - a wrapped header is one section; the land-home rule
  - apply moves; dry run previews and writes nothing; `--keep-section`
  - undo still byte-restores after an automatic move

TEST RESULTS: The full suite passes (2186 passed, exit 0). check_all: OK, 5 soft.
check_patterns failed once on the new tables before they were excluded; fixed in-batch.
REGRESSION RISKS:
- `section_mismatch` now reads header HEADS. Mixed headers ("# Sacrifice value + removal",
  "# Interaction / tricks") no longer warn. The roster measurement says those warnings were
  mostly false, but a real misfile under such a header now goes unflagged.
- `_section_headers` coalescing changes `move --section` needle matching to the whole
  wrapped block. That fixes a latent bug: a needle could previously hit a continuation line
  and insert the card mid-header. Error messages list first lines only.
- An automatic move is a reorder only. `swap --undo`'s multiset proof is unaffected (tested).
INVARIANTS AT RISK: INV-04. The moved line is written through `_safe_write_lines` (parse
fidelity plus a total-preserving guard), and the line text is verbatim, so G-65's printing
fields cannot change.
NET SCORE: 2 − 0 = 2.
  - Lands landing under a spells/role header on a swap: YES, it fired in production this
    month (Brawl builds 84–86).
  - Wrapped-header misreading in `move --section`: YES, it is latent on most decks.
  - No new failure mode found. The roster replay moves 4 of 4 objectively misfiled lines
    and nothing else.

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — local tooling only (the dashboard does not read section placement).

FOLLOW-ON ITEMS:
- Existing roster misfiles the new reading finds; editorial, so the owner's call.
  - 4 are auto-movable with `deck.py move`:
    - 35a Capital City and Captivating Cave → `Lands`. They are lands under
      `# Push-through / evasion + burn spells`.
    - 37a Hawkeye, Young Avenger and Unsparing Boltcaster → `Creatures`. They are
      creatures under `# Noncreature`.
  - 11 more type misfits have no single target:
    - 1: Bot Bashing Time under `Creatures`.
    - 24b and 24: an enchantment under `Lands`.
    - 26: Arc Reactor, Improvised Arsenal and Ugin under `Creatures`.
    - 35a: Great Divide Guide and Bloom Tender under `Lands (24)`.
    - 36a: Felidar Retreat. 38: The Aetherspark. 44a: Sothera. All three are under a
      `Creatures —` header.
- `cmd_move`'s "from `# …`" display line still walks to the nearest comment line, not the
  block's first line. Cosmetic.
- Blank-Legalities exclusion in suggest/screen/cuts (Batch 1 open half); `apply-flex` undo;
  `--by-set` uses deck-line sets only. All still open from earlier batches.
- Batch 6's speed-up candidates (classify_roles memo, rationale_staleness guard, loader memos).

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-05: placement is automatic on a type misfit (land → the land header), warns
  otherwise, and `--keep-section` opts out. The "advisory / UNAMBIGUOUS headers only" text
  is now stale. G-77: note the automatic form.
- README swap line: `--keep-section`.
- `.claude/commands/apply-changes.md` Stage 2: the swap now auto-places, and `--section` is
  only for overriding.
- docs/gotchas.md G-05 long form: the 260 → 57 head-only measurement, and the 73-land
  wrapped-header near-miss.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
