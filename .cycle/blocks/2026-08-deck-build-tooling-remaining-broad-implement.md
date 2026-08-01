---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: the REMAINING six from `2026-08-deck-build-tooling-scan.md`
- F-05 — `screen`'s KEY label saturated at 45–51% of every pile.
- F-06 — `similar` ranked anti-correlated with actual shared cards.
- F-07 — the tier guard flagged a deliberately conservative grade as "possibly UNDER-graded".
- F-08 — `consistency`'s land advisory reversed direction and could be satisfied by nothing.
- F-09 — `cuts` optimised the wrong axis (a) and read a deck-state-scaling card at its floor (b).
- F-10 — `screen`'s header counted INPUTS, and the unresolved block printed last.

Files modified: scripts/deck.py, scripts/check_patterns.py, tests/test_deck.py

CHANGES:
F-05 | scripts/deck.py | **A fix was designed, measured, and REJECTED — that is the main content of this finding.** The saturation was diagnosed precisely: all 54 KEYs on the 52a screen came through ONE branch of `fit_strength`, the signature override, because `_strong_signature_themes` returns `{graveyard, reanimator}` and `graveyard` — already in `GENERIC_THEMES` — is carried by roughly half the black pool. The obvious tightening (a GENERIC signature theme cannot mint KEY alone) was implemented against the live roster: deck 52a 51% → 11%, which is the goal — but deck 30 went 21% → **1%**, and `Innkeeper's Talent` (shared `counters`, the deck's whole spine) fell from KEY to role-player. That is the counter-doubler-in-a-counters-deck rescue the signature branch was BUILT for, documented in `fit_strength`'s own docstring. Shipping it would have traded a noisy label for a wrong one. So `screen` now REPORTS the saturation instead: when ≥40% of ≥10 resolved candidates come back KEY, it names the themes responsible and says the ORDER is the signal, not the word. Same posture as the protection axis and `count_conf` — report what the model cannot fix rather than silently re-score it.
F-06 | scripts/deck.py | Theme cosine stays the PRIMARY order (it answers "does this duplicate an identity", which is the question `similar` is for), but the card-overlap answer is now stated instead of left in a column: `▸ Most shared CARDS: deck 52 (14 nonland cards, 100% colours) — it ranks #4 by theme`. Printed only when the two answers disagree. The note says explicitly that some overlap between decks is fine — the user's standing position, and the thing this session over-weighted when it cut two good cards from 52a to lower a number.
F-07 | scripts/deck.py | New `_argues_below_floor(meta)` + `_BELOW_FLOOR_ARGUMENT`. The guard is asymmetric by design — one band OVER is credited to intangibles — but it treated ANY amount under as suspect, so decks 51, 52 and 52a each carried a permanent "possibly UNDER-graded" nudge for being honestly graded, and a standing warning is one nobody reads. A rationale that explicitly argues for grading under the floor now reads `✓ deliberately conservative`. Deliberately narrow: the prose must name the floor or the rubric's own language. Roster split after the change: **20 decks suppressed (they argue why), 12 still flagged** — not a blanket silencing.
F-08 | scripts/deck.py | New `_keepable_at(nlands, deck_size)`. The advisory prescribed a direction without checking it: deck 52 at 24 lands read "consider FEWER", the same list at 23 read "consider MORE" at a WORSE keepable (82.5%) with three cards falling under 90% on curve. It now computes keepable at the suggested neighbour first, and when that is no better says the threshold is unreachable for this curve and points at the cast-on-curve table — the measurement that CAN be optimised, and the one that actually settled the question.
F-09a | scripts/deck.py | `cuts` prints which axis the deck is SHORT on above the table. The `⚠interaction (deck runs N)` note says a removal card is redundant, and on deck 52a — whose measured weakness is its curve (4.22 average, 12 early drops) — that put four ONE-MANA removal spells at the top of the cut list. Trimming cheap cards from a deck that is too slow is backwards. `tier --to` and `suggest --needs` both know what a deck lacks; `cuts` did not, so it optimised the only axis it could see. Stated, not scored.
F-09b | scripts/deck.py | New `_deck_state_axis(text)` + a `⌁scales w/ <axis>` flag on `cuts`, the sibling of `_int_scaling` (which covers removal only). A card whose value is a COUNT in the deck reads at its FLOOR in every model here: Cat-Gator scores as a 7-mana 3/2 lifelink when its ETB is damage equal to your Swamp count, and deck 52a runs 24. The ZONE is part of the axis label — "cards" alone is uninformative, "cards in your graveyard" tells you which number to go count. FLAG only; `suggest --needs` already takes this posture for board-dependent removal, and the two commands were grading the same card two different ways.
F-10 | scripts/deck.py | `screen`'s header counts RESOLVED candidates, not inputs (`screening 0 candidate(s) … (1 name(s) given)`), and the ambiguous / not-found block moved ABOVE the results. It used to print after ~200 lines, which is exactly where a reader does not look — and that is how a pile passed with broken shell quoting ("222 candidate(s)" for 83 names) ran unnoticed in this session. Note `screen` already accepts stdin, which avoids the whole class; the header now makes the mistake visible when it does happen.
— | scripts/check_patterns.py | `_DECK_STATE_AXIS_RE` registered against the live pool corpus; `_BELOW_FLOOR_ARGUMENT` excluded with a reason (tier-rationale prose, unit-tested). The completeness gate caught both on the first run — working as designed, twice this cycle.

TEST RESULTS: PASSED. `python3 scripts/check_all.py` — all invariants hold, exit 0, the same 2 soft warnings as the previous block (27 unverified printings, 4 stale rationale citations; both are findings this cycle SURFACED, not regressions). `pytest` — **834 passed** (was 826; +8 anchors in 4 new classes). All ten `check_*` gates green standalone; `check_patterns` 146 live.

Regression Scenarios walked:
- Scenario 2 (Analyze a deck) — **PASS**. 14 subcommands re-walked after the changes plus `--help`; no traceback. `cuts`, `similar`, `consistency`, `tier` and `screen` all changed output and all still run clean.
- Scenarios 1, 3, 4–8 — **NOT APPLICABLE**. No ingest, derived-data, app or presentation file was touched.

REGRESSION RISKS:
- **F-05 changes no scores at all** — that is the point, and the rejected alternative is recorded above so a future session does not re-derive it and ship it.
- F-07 suppresses a warning. If a rationale contains the trigger vocabulary while NOT actually arguing below the floor, a genuinely under-graded deck goes unflagged. Measured: 20 suppressed / 12 still flagged, so the cue is discriminating rather than matching everything.
- F-08 adds a `math.comb` call on one branch; no behaviour change when the advisory is not tripped.
- F-09a reads `deck_quality_vector` inside `cuts`, which is already memoized per file. F-09b is a new text scan on the cut rows only.
- F-06 and F-10 are print-order and print-content changes. Anything parsing `screen`'s stdout would see a different first line — nothing does; the tests assert on functions, not stdout.

INVARIANTS AT RISK: None. No invariant logic was touched; INV-01…04 re-verified via `check_all` after every change.

NET SCORE: 6 production fixes − 0 new failure modes = **6**
(Per-fix: F-05 YES, it fired this session — I nearly acted on a KEY label that meant nothing on a 119-card screen. F-06 YES — the 96%-vs-81% inversion is what made me cut two good cards from 52a. F-07 YES — three decks carry the nudge right now. F-08 YES — it gave me contradictory advice on deck 52 and I had to ignore it. F-09 YES — `cuts` proposed trimming one-mana removal from the slowest deck on the branch, and read Cat-Gator at its floor. F-10 YES — a 222-token screen ran unnoticed this session. New failure modes: none. The one nearly introduced — F-05's tightening, which would have broken `fit_strength`'s documented rescue — was caught by measuring against deck 30 before shipping, not after.)

OPERATOR ACTIONS / DEPLOY:
- None. | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push. Presentation untouched.

FOLLOW-ON ITEMS:
- **F-05's real fix is still open.** The saturation is now reported, not solved. A proper fix needs a notion of "specific for this deck AND discriminating among candidates" that does not break the generic-signature rescue — probably a per-theme density comparison (deck density vs pool density) rather than the binary GENERIC_THEMES membership. Worth doing; not worth guessing at.
- The 27 unverified printings and 4 stale rationale citations from the previous block remain unfixed.
- `#: based-on:` parses now and nothing reads it (from the previous block).

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md **G-09** (`cuts` is a shortlist): add that it now prints the deck's SHORT axis and a `⌁scales w/` flag, so a `⚠interaction` note is read in context.
- CLAUDE.md **G-28**-adjacent or a new bullet: `screen`'s KEY saturation report — what it means and that the label was measured at 45–51%.
- CLAUDE.md the `similar` bullet [G-47]: the `▸ Most shared CARDS` line, and that theme similarity and card overlap are different questions.
- CLAUDE.md **Competitive Tiering**: the guard no longer flags a deck graded below the floor when the rationale argues why.
- CLAUDE.md **G-36** (`consistency`): the land advisory now detects the unsatisfiable case.
- README: `screen` / `cuts` / `similar` / `consistency` output changes.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
