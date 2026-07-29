# Block — splitting CLAUDE.md's rules from their evidence (2026-07-29)

**CLAUDE.md 2,219 → 956 lines. Nothing deleted.** Common Gotchas 1,292 → 306, Known
Issues 351 → 56; the evidence moved verbatim into `docs/gotchas.md` (1,937 lines), keyed
by anchor.

## Why

CLAUDE.md is the ONLY file a fresh session loads automatically, and every operative rule
carried the incident that produced it — 57 Common Gotchas averaging 22 lines each, the
longest 97. The rule and its evidence were fused, so a session could not load one without
the other, and acting safely meant reading 2,200 lines of prose first.

## What the analysis found (and how it changed the design)

Measured before designing, and three facts reshaped the plan:

1. **Nothing parses CLAUDE.md at runtime** — every reference is prose. Zero code risk;
   the whole risk is what a future session can still find.
2. **The vendored workflow commands depend on section NAMES.** `broad-scan`,
   `broad-implement`, `health-pulse` and `sync-docs` say "read CLAUDE.md (especially
   Common Gotchas and Key Design Decisions)" and "CLAUDE.md's Cycle Workflow Config".
   They are copied verbatim from claude-workflow-tools and must not be edited here, so
   **renaming a section would break a command with no local fix.** That killed any plan
   that reorganised by topic, and is now asserted by the gate.
3. **26 of the 57 gotchas (654 lines) are about a `deck.py` subcommand README already
   documents — all 26.** Common Gotchas was doing three jobs: a second command
   reference, a set of safety rules, and an incident log. Only the safety rules need
   auto-loading.

Deliberately NOT deduped against README: that needs a second judgement per rule ("does
README really cover this?") and a wrong call silently loses information. One destination,
one judgement per rule — *what is the operative sentence?*

## The method

**The bodies were MOVED, never retyped.** Only the short rule left behind in CLAUDE.md is
newly written. That makes conservation a MEASUREMENT rather than a judgement call: a
scratch checker asserts every original bullet is byte-identical (after whitespace
normalisation) to its `docs/gotchas.md` section. **69/69 conserved**, and it was
mutation-tested by deleting a live residual sentence — the `doubler_restriction`
upper-bound caveat — and watching it fail.

That mattered because the real failure mode here is silently dropping a residual: a
sentence that reads like narrative but is operative. Seven rules carry one; all survived,
and they are called out explicitly in the new CLAUDE.md text (`KNOWN GAP`,
`KNOWN RESIDUAL, live`).

## The gate — `scripts/check_docs.py`

A hand-kept cross-reference is exactly what this project keeps watching rot
(`check_patterns` fell 13 patterns behind; `_INLINE_PARSE_ALLOW` could name deleted
code). Five checks, hard-gated in `check_all`:

1. Every CLAUDE.md anchor resolves to a `docs/gotchas.md` section.
2. Every section is referenced — **no orphans**. Stranded evidence reads as covered
   while covering nothing.
3. No duplicate anchors (it caught my own intro paragraph using `[G-23]` as an example).
4. The section headings the vendored commands name still exist.
5. **A per-bullet line cap (15).** Without it the two files re-fuse over a few cycles and
   no other check can see it — the regression is gradual, not an event. No exemption
   list, because an allowlist here would rot like the registries above.

## The part worth remembering

**`check_commands` caught me deferring the wiring.** The plan was to commit the tooling in
tranche 1 and wire `check_docs` into `check_all` at the end. The workflow-coverage gate
failed the build immediately: *"check_docs.py is a gate but check_all.py never imports it
— it runs only if someone remembers to."* That is this repo's signature lesson enforcing
itself against the person adding the next gate, which is the best possible outcome for it.

Consequence: the tranche-1 commit is momentarily red on this branch (the 57 Common
Gotchas anchors were still unresolved), and the following commit makes it green. Worth
knowing if you bisect through it.

## Verification

- `check_all` — all invariants hold (11.0s). `pytest` — 686 passed (was 673; +13).
- Conservation 69/69 byte-identical, mutation-tested.
- Three gate mutations (orphan check disabled, line cap disabled, vendored-section check
  disabled), each confirmed to fail `tests/test_check_docs.py`.

## Follow-on

**Cycle Workflow Config (336 lines) is deliberately out of scope**, agreed with the user
as a separate pass. What is there: the `- Testing:` subsystem entry is a **single
11,600-character bullet** (1,530 words) and the `Test Command:` paragraph is 2,260 words
— both reference, not operative. But that section is the one the vendored commands
consume *structurally*, so compressing it has a different risk profile. The field labels
(`Test Command`, `Subsystems`, `Invariant Library`) are already asserted by `check_docs`,
which gives the follow-up a safety net it would otherwise lack.
