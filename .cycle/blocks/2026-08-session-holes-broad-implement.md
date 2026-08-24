---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: H-1 (G-05's advisory could only be resolved by a G-65-forbidden
hand edit); H-2 (the citation audit suppresses a SHARING claim as a cross-deck
comparison). H-3 (G-27 clause-scoping friction) was investigated and DECLINED.
Files modified: scripts/deck.py, scripts/check_patterns.py, tests/test_deck.py,
CLAUDE.md, docs/gotchas.md, .claude/commands/apply-changes.md,
decks/43-overdraft/deck.txt, decks/42-blood-price/42a-orzhov-aristocrats.txt,
dashboard.html

CHANGES:
H-1 | scripts/deck.py, .claude/commands/apply-changes.md | New `swap --section
  "<header substring>"` relocates the added line under a named `# section` as part of
  the same write, moving the line VERBATIM. Validates before writing: an absent or
  ambiguous header aborts the swap with the real header list, leaving the file and the
  recommendations ledger untouched. `_relocate_card_line` + `_section_headers` are the
  mechanism; `section_mismatch`'s warning now names the flag. Documented as G-77.
H-2 | scripts/deck.py, scripts/check_patterns.py | `_SHARING_CUES` carve-out in
  `_cites_as_history`: a clause containing share/shared/sharing/in common/both run/both
  play/overlap no longer suppresses on its other-deck reference, because a sharing claim
  asserts the named card is in THIS deck. Every other cross-deck citation suppresses
  unchanged. Registered in check_patterns' _EXCLUDED. Documented as G-78.
H-2b | decks/43-overdraft, decks/42-blood-price/42a | THREE real stale citations found
  by the investigation and fixed: deck 43's archetype prose still listed Wolfbat as a
  live second-card cluster member after it was cut this session, and deck 42a's tier AND
  archetype prose both cited Ahriman as an active engine piece — a card 42a does not run.
  Also corrected deck 43's own prose, which stated the WRONG cause for the Erode error.

TEST RESULTS: passed — 1423 passed, 1 skipped. check_all green (1 soft: the 4 accepted
dead library searches). check_patterns 268 live. check_commands OK. check_docs OK.
deck.py --help and swap --help both build.
Four mutants watched failing: relocate-guesses-on-ambiguity, carve-out-removed, and
(from the preceding G-76 commit) widened-band and re-added-saturated-family.

REGRESSION RISKS:
- `_do_swap` gained a keyword-only-in-practice `section=None` parameter. `cmd_apply_flex`
  and `cmd_swap` are the only callers; apply-flex passes nothing and is unaffected.
- The `_SHARING_CUES` carve-out narrows an existing suppression. Risk is a false positive
  on prose that says two OTHER decks share a card. Judged low (deck prose compares to
  this deck, not between third parties) and measured: roster sweep returned 0 new hits,
  and a control test pins that an ordinary cross-deck comparison still suppresses.
- Relocation runs inside the existing try/except and before `_safe_write_lines`, so the
  card-total guard is unchanged and a move preserves the total by construction.

INVARIANTS AT RISK: None. INV-04 is strengthened in practice — `--section` removes the
hand-edit path that produced two invalid printings. Verified with `resolve --check` on an
end-to-end relocation before reverting the probe.

NET SCORE: 2 production fixes + 3 real stale citations found − 0 new failure modes = 5

OPERATOR ACTIONS / DEPLOY:
- None
Deploy: dashboard rebuilt via `make postedit`; GitHub Pages republishes on push to main.

FOLLOW-ON ITEMS:
- `_RATIONALE_MIN_LEN = 9` hides every single-word card name shorter than nine
  characters — this is what actually hid `Erode`, not the cross-deck suppression.
  MEASURED and DECLINED: lowering to 7 gives 3 real / 2 false roster-wide, to 5 gives
  3 real / 4 false. Both would put permanent false warnings in check_all, which trains
  readers to ignore the sweep. The three false positives have identifiable causes worth
  fixing FIRST if the floor is ever to come down: a bare "over" (deliberately not a
  history cue, since it is the house phrasing for a quality vector), a mechanic name
  capitalized at a sentence start (defeats the case-sensitivity rule), and a punctuation
  variant of an in-deck card name ("Kona Rescue Beastie" vs "Kona, Rescue Beastie")
  defeating the exact-name masking. Recorded as G-78.
- H-3, DECLINED with reasoning: the G-27 requirement that a change-cue sit in the SAME
  clause as the card name cost three prose rewrites this session. That is the rule
  working as designed, not a defect — G-26 states the cue lists must stay NARROW because
  a false positive is noisy and gets noticed while a false negative is silent. Loosening
  the clause scoping to save the author some rewording would trade a visible cost for an
  invisible one. Not fixed, deliberately.
- The G-76 state-gate families are still n=4 and n=1 on the roster; bands are provisional.

DOCUMENTATION UPDATES NEEDED:
- Done in this commit: G-77 and G-78 in CLAUDE.md with full evidence in docs/gotchas.md,
  and the `--section` step in .claude/commands/apply-changes.md.
- /sync-docs to follow for README currency and the Cycle Workflow Config gate counts.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
