# Block — Cycle Workflow Config: restore the canonical shape (2026-07-29)

Phase 2 of the doc split. **CLAUDE.md 956 → 757 lines** (2,219 at the start of the day).
Cycle Workflow Config 336 → ~140, with eleven blocks moved verbatim into
`docs/cycle-config.md`.

## The spec settled the design

The user supplied `setup-cycle.md` from claude-workflow-tools — **the command that WRITES
this section** — which turned a judgement call into a specification:

- **Test Command: a SINGLE LINE.** Ours was 208 lines (529–736), the whole gate narrative
  living inside a parenthetical.
- **A Subsystem: a comma-separated file list.** Ours carried 13.6k characters of inline
  prose across two entries — `Testing` alone was a single **11,613-character bullet**
  (1,530 words) and `Presentation` 1,996.
- **A Regression Scenario: Steps + Expected.** Scenarios 1–4 were dense prose; 5–8 already
  used the canonical shape.
- Invariant Library, Policy Configuration and Frozen Subsystems already matched.

So this was **restoring a format, not inventing one** — a much stronger mandate than
"trim the long bits", and it made every keep/move decision fall out of the spec.

## What moved

Eleven `[C-nn]` blocks, moved VERBATIM as in phase 1: the gate narrative (C-01, 207
lines), the six subsystem inventories (C-02…C-07), regression scenarios 1, 2 and 7
(C-08, C-09, C-11), and the Deploy Command paragraph (C-10).

Conservation proved **11/11 byte-identical** after normalisation.

## Two real findings the checks produced

**1. I dropped a live known issue, and the conservation check caught it.** The retained
half of the section is *retyped*, not moved, so conservation cannot cover it — I wrote a
second check comparing every retained original line against the new text in 6-word
shingles. It flagged 18 lines; recovering them surfaced that my compressed Regression
Scenario 7 had silently dropped the note that **the editor's SUCCESS toast is cut short by
the `location.reload()` that follows it, so only the failure toasts are readable**. That is
a live caveat about a manual test, exactly the residual-loss class the whole method exists
to prevent. Scenario 7 became its own verbatim block (C-11) with an anchored summary.
Re-run: 18 → 5 flagged lines, all five deliberate (one intentional wording update, one
correction below, three Steps/Expected compressions).

**2. Regression Scenario 3 carried the rebuild chain in the WRONG ORDER — and the gate
written to catch exactly that had never looked at CLAUDE.md.** It read
`build_mana.py → tag_synergies.py --merge → build_pool.py → build_gallery.py`:
`build_pool` AFTER `build_mana`, the inversion `[G-13]` documents as the eleven-copies bug.
`tests/test_verify_ingest.py::_restates_chain` scans `scripts/*.py` and
`.claude/commands/*.md` — **never CLAUDE.md**, the one file every session loads
automatically. Scenario 3 now says `make refresh`, and the test gained
`test_claude_md_defers_to_the_make_target`, mutation-tested by reintroducing a wrong-order
line. The `docs/` evidence files stay out of that scan on purpose: `[G-13]` must state the
correct order to explain why the Makefile is the single definition — the same one-place
exemption `refresh.md` already has.

## The gate, generalised

`check_docs.py` now maps an anchor PREFIX to its evidence file
(`G`/`K` → `docs/gotchas.md`, `C` → `docs/cycle-config.md`) and additionally fails a
section defined in the WRONG file — a `[C-nn]` heading in gotchas.md would resolve while
sending the reader to the wrong document, which is as useless as no evidence.

**Two bugs in my own generalisation, both caught by running it:**

- It iterated the prefix map, so `gotchas.md` was read twice (G and K share it) and every
  G/K anchor reported as a duplicate — a gate failing on a healthy repo. Now iterates the
  distinct files. Pinned by `test_a_shared_evidence_file_is_read_once`.
- The line cap mis-measured a section that is not a pure bullet list: `_section_bullets`
  charged everything after the last `- ` bullet to that bullet, so INV-06 measured **85
  lines**. A bullet now ends at any non-indented, non-bullet line.

## Verification

- `check_all` — all invariants hold. `pytest` — 690 passed (was 686; +4).
- Conservation 11/11 on the moved blocks; the retained-half shingle check down to 5
  deliberate differences.
- Mutations confirmed to fail: wrong-order recipe in CLAUDE.md; section in the wrong
  evidence file; shared-file double-read; plus the three phase-1 gate mutations still hold.

## Where the doc split ended up

| file | lines |
|---|---|
| CLAUDE.md | **757** (from 2,219) |
| docs/gotchas.md | 1,937 |
| docs/cycle-config.md | 328 |

80 anchored rules/fields, round-trip gated in both directions.

## Follow-on

- The `Health Dimensions` field keeps one-line descriptions rather than the spec's bare
  comma-separated names. Deliberate — the descriptions are short and carry real
  information — but it is a knowing deviation from `setup-cycle.md`.
- Regression scenarios 5, 6 and 8 remain inline at full length. They are Steps + Expected,
  which IS the canonical shape, so there is nothing to move; they are just long because a
  manual browser walk needs its steps.
