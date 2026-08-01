---BROAD SCAN FINDINGS---
Source: NOT a `/broad-scan` run. These were found by APPLYING the tooling — building decks
52 and 52a from a ~116-card concept pile, plus the wishlist/budget and ingest work in the
same session. Every finding below was reproduced deliberately after being noticed, and the
reproduction command is given so the fix can be tested against it.

Why that provenance matters: none of these were caught by a gate. `check_all` was green,
`preflight` said READY, and 804 tests passed through every one of them. The gates verify
that the MODELS are right; what failed here is mostly a model being asked a question it was
never given a term for.

Scope: scripts/deck.py (tier_band, cuts, similar, screen, consistency, the rationale audit),
scripts/check_all.py (INV-04).

=== F-01 | Deck-line (Set) and Collector # are NEVER validated | Data/Decks | HIGH ===
A deck line's printing fields are decorative to every gate, while being load-bearing in the
Arena import block the same tools EMIT.

REPRO:
  put `1 Eaten Alive (ZZZ) 172` (a set code that does not exist) into any deck, then:
    deck.py legal      -> "✓ No construction issues for standard"
    deck.py check      -> "1 / 1   Eaten Alive (ZZZ)"      <- reports it OWNED
    deck.py preflight  -> "Verdict: READY"
    check_all.py       -> "All invariants hold. ✓"
  `(FDN) 99999` behaves identically.

WHY: INV-04 checks that a line PARSES. Every ownership/legality join keys on the card NAME,
so the set and collector number are never read. A deck file can be simultaneously READY,
integrity-clean, and un-importable.

NOT HYPOTHETICAL: while building deck 52 I hand-wrote `1 Eaten Alive (FDN) 610`. The true
collector number is 172. Nothing complained; it was caught only because `deck.py resolve`
was run separately and the numbers were eyeballed.

FIX: `resolve` already holds every valid (name, set, collector#) triple. Cross-check each
deck line against it in INV-04 (hard) or `legal` (soft). Cheap, and it closes a silent hole
in the mandated pre-commit gate.

=== F-02 | An intentionally-uncastable reanimation target is graded as a build ERROR ===
| Analysis (tier_band, preflight) | HIGH |
Reanimator is a real archetype: you play a bomb you cannot cast, put it in the graveyard,
and cheat it in. The tooling has no term for that and treats it as a misbuild.

REPRO (deck 52a, a mono-black reanimator, before/after adding ONE WUBRG bomb):
                     BEFORE                     AFTER (+1 Cosmic Spider-Man)
  castability        PASS                       FAIL — 1 uncastable
  preflight          READY                      BLOCKED
  metrics floor      A                          C
One card, working exactly as designed, moves the deck three tier bands and blocks the
pre-commit gate.

RELATED, and this is the mechanism: broad-scan F-16 (unimplemented) found that `tier_band`
SETS the floor to C on an uncastable stray rather than CAPPING it. F-16 was filed as latent
because no roster deck was in range. This is the case that puts a deck in range.

FIX (two parts, the first is enough to unblock):
 1. An opt-in header — `#: uncastable-ok: <card>; <card>` or `#: plan: reanimator` — that
    exempts named cards from the castability FAIL and from the tier floor collapse. The
    deck author is asserting "this is intended", which is exactly the kind of claim the
    `#: protect:` header already models.
 2. Implement F-16 so a stray CAPS rather than SETS, per its original filing.
NOTE the honest counter-argument: castability FAIL is a good default, and most uncastable
cards really are mistakes. This is an opt-in, not a weakening of the default.

=== F-03 | `tier --audit-rationale` false negative on live data | Analysis | HIGH ===
After two swaps on deck 52a the header was stale three ways. The audit found ONE.

REPRO: apply the 2026-08 swaps to 52a (Summon: Bahamut -> Bringer of the Last Gift,
Shinra Reinforcements -> Forum Necroscribe), then fix ONLY the card-advantage figure:
  stale, and correctly flagged : `#: tier:` "card advantage 2"      (live 1)
  stale, and MISSED            : `#: archetype:` cites Summon: Bahamut  (removed)
  stale, and MISSED            : `#: tier:` "avg nonland MV 4.17"   (live 4.22)
  audit output                 : "✓ rationale is current — every card it cites is still in
                                  the deck and every figure matches the live vector."

TWO DISTINCT DEFECTS:
 (a) A removed card cited in `#: archetype:` was not detected. I tested a colon-in-name
     hypothesis (`Summon: Bahamut`) and DISPROVED it — `Starfall Invocation`, which the
     audit HAD flagged in a different sentence earlier in the session, also passes when
     injected into the sentence shape "The deck also wins with X often." So detection is
     sensitive to the surrounding sentence in a way I could not characterise. G-26 already
     documents copula and change-cue residuals; this is a third, uncharacterised one.
     Whoever fixes this should start by finding what makes those two sentences differ.
 (b) `avg MV` is not among the figures compared. The vector has 7 fields; the audit checks
     a subset. Any figure a rationale can quote should be checkable.

RELATED, same surface: `#: notes:` is deliberately out of audit scope (G-27: "a free-form
build log where naming an absent card is correct"). But 52a's notes block said
"Deliberately NOT included: Bringer of the Last Gift" AFTER Bringer was added. That is not
"naming an absent card" — it is a false claim about the CURRENT list, in the opposite
direction from the one G-27 exempts. Worth a narrow rule: an EXCLUSION claim in `#: notes:`
naming a card the deck now runs is always wrong.

=== F-04 | Nothing answers "does this deck contain TARGETS for its own effects" ===
| Analysis — MISSING CAPABILITY | HIGH |
The single most important finding of the whole deck build — the concept pile held 24 ways to
return a creature against 8 creatures worth returning — came from a hand-written script. No
command produces it.

`engines` grades enabler <-> payoff by synergy TAG, which is a different question. What is
missing is arithmetic on the gates written into the card text:
  Scrounge for Eternity   "mana value 5 or less"   -> how many legal targets in THIS list?
  Too Evil to Stay Dead   "mana value 4 or less"   -> ?
  Lively Dirge            "total mana value 4"     -> ?
  Deadly Precision        "sacrifice an artifact or creature" -> how many artifacts?
  Descend 8               "eight permanent cards"  -> how many permanents reach the yard?

CLAUDE.md's G-61 states this as a HUMAN discipline ("state the count, then decide") with an
incident list of four overturned dismissals, precisely because nothing automates it. A
`deck.py targets <id>` that parsed MV caps / type gates / zone gates out of the deck's own
oracle text and counted the satisfying cards would convert G-61 from a discipline into a
check. Highest analytical value of anything in this file.

=== F-05 | `screen`'s KEY label is saturated — measured | Analysis | MEDIUM ===
  deck 52   83 candidates graded, 42 KEY  -> 51%
  deck 52a 119 candidates graded, 54 KEY  -> 45%
The docs say "trust KEY, judge role-player". A label that fires on HALF the pile carries
almost no information.

CAUSE: KEY fires off any shared CENTRAL theme. In a mono-black graveyard deck, `graveyard`
is on nearly every black card, so the theme test is satisfied by colour alone.

THIS IS THE THIRD INSTANCE OF A FIXED BUG CLASS. CLAUDE.md documents the same saturation for
`suggest`'s Decks column (99%, G-28) and `cuts`' `#: protect:` keep-boost (87%, G-09), both
fixed by gating on a SPECIFIC (idf-rare) theme rather than any theme. `screen` appears never
to have received that gating. FIX: apply the same specific-theme gate; then re-measure the
KEY rate on these two decks as the acceptance test.

=== F-06 | `similar` ranks anti-correlated with actual card overlap | Analysis | MEDIUM ===
Deck 52a's neighbour table:
  sim   colours  shared cards  deck
  96%     33%         4         6
  94%     50%         4         5
  83%    100%         7        11
  81%    100%        13        52   <- its own PARENT
The deck sharing 13 cards and every colour ranks FOURTH, 15 points below a deck sharing 4
cards and a third of its colours.

The tool prints an honest caveat ("grade the win-cons from `deck.py text`"), and the caveat
is correct — but the ORDERING is what a person acts on, and it puts the wrong deck first. A
ranking that inverts is worse than no ranking.

FIX: fold shared-card count and colour overlap into the sort key, not just the printed
columns — or print two ranks (theme-similarity and card-overlap) and stop implying one
ordering. NOTE the user's standing position, recorded here so a future session does not
over-correct: SOME CARD OVERLAP BETWEEN DECKS IS ACCEPTABLE. `similar` is a shortlist for
"is this a new deck", not a constraint to be minimised, and this session over-weighted it
(two good cards were cut from 52a purely to lower the number).

=== F-07 | The tier guard flags a deliberately CONSERVATIVE grade | Analysis | MEDIUM ===
Decks 52 and 52a are both graded B against an A floor, each with the four-criterion rubric
argument written into the header, which is what deck 51 already does and what the rubric
permits. Both now carry a standing `↑ possibly UNDER-graded` warning.

The guard is asymmetric: it tolerates one band OVER (correct — that band credits intangibles
the metrics cannot see) but treats ANY amount under as suspect. Net effect: honest grading
produces permanent warnings, and a permanent warning is one nobody reads.

FIX: suppress the under-graded nudge when the `#: tier:` rationale contains an explicit
argument against the floor — the same way a change-cue suppresses a citation flag. One band
under WITH a written reason is a defensible human call, not an anomaly.

=== F-08 | `consistency`'s land advisory is unsatisfiable for a low-curve list ===
| Analysis | MEDIUM |
Deck 52, same list, two land counts:
  24 lands -> "keepable 84% is low — consider FEWER lands (most 60-card decks run 23–26)."
  23 lands -> "keepable 82% is low — consider MORE lands (most 60-card decks run 23–26)."
Both trip the same warning, the advice REVERSES, and no configuration clears it. 24 was
chosen by measuring both and reading the cast-on-curve table instead.

FIX: the keepable threshold appears calibrated for a higher curve than a 2.83-average
singleton deck. Either scale it by avg MV / early-drop count, or — simpler and more honest —
when both directions would trip, say so ("this curve cannot clear the keepable threshold at
any land count; optimise on cast-on-curve instead") rather than emitting a direction.

=== F-09 | `cuts` optimises the wrong axis, and cannot see deck-state scaling ===
| Analysis | MEDIUM |
TWO related defects on the same surface.

(a) WRONG BINDING CONSTRAINT. On deck 52a — whose stated and measured weakness is its CURVE
(4.22 avg, 12 early drops) — `cuts` proposed trimming one-mana removal, because interaction
11 is redundant. Cutting cheap cards from a deck that is too slow is exactly backwards. The
ranking has no notion of which axis the deck is actually short on, though `tier --to <TIER>`
and `suggest --needs` both do. FIX: let `cuts` read the same needs model, and de-prioritise
cutting from an axis the deck is already short on.

(b) BLIND TO DECK-STATE SCALING. Cat-Gator scores as a 7-mana 3/2 lifelink; its ETB deals
damage equal to your Swamp count, and the deck runs 24. Moonshadow scores as a 1-mana 7/7
with six -1/-1 counters. Both sort by their FLOOR rather than their realistic value.
`suggest --needs` already has the right primitive — it prints `⚠ scales w/ <axis>` instead
of silently scoring — and `cuts` has no equivalent. This is the `✱ multiplier` co-signal
(G-33/G-40) generalised past doublers to any card whose value is a function of a deck
property. Same shape as F-04: the value lives in a COUNT, not in the card's own text.

=== F-10 | `screen`'s header counts INPUTS, not resolved candidates | Analysis | LOW ===
`deck.py screen 52 "Demon"` prints "screening 1 candidate(s)" and then grades zero — 'Demon'
is ambiguous and correctly refused. The count is the input count.

This is minor on its own, but it is what let a mistake of MINE run unnoticed: 83 names were
passed as shell positional arguments with broken quoting, 222 tokens arrived, and fragments
that happen to be real card names (Darkness, Six, Endurance, Conviction) resolved SILENTLY
because each is individually unambiguous. The header said "screening 222 candidate(s)" and I
read the head of the output. `screen` DOES report ambiguous and not-found names — but at the
BOTTOM, where a 200-line run scrolls them away.

TO BE CLEAR THIS ONE IS MOSTLY OPERATOR ERROR: `screen` already accepts stdin (`-`, one name
per line), which removes the hazard entirely, and it was not used. FIX is small: count
RESOLVED candidates in the header, and print the ambiguous/not-found block FIRST.

---
PRIORITY, if implementing in order:
  1. F-01 — silent, sits inside the mandated pre-commit gate, fix is a cross-check against
     data `resolve` already holds.
  2. F-02 — actively obstructs an archetype the user asked to build; subsumes F-16.
  3. F-04 — highest analytical value; converts G-61 from discipline into a check.
  4. F-03 — a correctness gate reporting clean on stale prose is worse than no gate.
  5. F-05 — third instance of a bug class already fixed twice; the fix is known.
  6. F-06, F-07, F-08, F-09, F-10.

NOT FOUND / EXPLICITLY CHECKED AND FINE:
  - `resolve` refuses to guess and reports ambiguity — correct, and the model the other
    name-taking commands should copy.
  - `swap --apply` correctly recorded all four swaps to recommendations.csv with the
    pre-swap `cuts` rank, and never blocked a swap.
  - `mana`'s hybrid handling was right every time (Ultimate Green Goblin read as
    "hybrid — paid on-color", per G-58, with no false stray).
  - `consistency`'s cast-on-curve table was the single most useful output in the build; it
    settled the 23-vs-24 land question that its own keepable advisory could not.
---END BROAD SCAN FINDINGS---
