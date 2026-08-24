Analyze a deck and propose improvements — with owned cards and craftable upgrades.

Input: a deck id in $ARGUMENTS (e.g. `18` or `18a`).

## Stage 0 — Read the play-style profile

Check CLAUDE.md's **Player Profile** for the default deck-building style on the
creative ↔ competitive dial, and honor any per-run override in $ARGUMENTS
(e.g. `19 competitive`, `19 creative`). The style changes how you weight cuts and
swaps (see "Play-style weighting" below) — not the data-gathering.

## Stage 1 — Gather the full picture (before recommending anything)

Read the actual card text — never judge by mana value or a single subtype:
0. **`python3 scripts/deck.py text <id>` FIRST — phased ingestion.** Dump and
   *read* the full oracle text of every nonland card before running any other
   analysis. This is non-negotiable: the recurring mis-grade in past sessions came
   from grading a keep/cut/swap off a role label, a tag match, or a truncated
   `Card Text[:N]` slice — missing board-wide effects (M.O.D.O.K.), modal /
   leaves-play triggers (Momo), alt-costs, and deck-dependent scaling. The dump
   prints a `⚠` on exactly those classes (board-wide / modal / leaves-play /
   converge·devotion·affinity·X / ◊·△ cost). Ingest the whole deck's text here so
   nothing downstream is graded from a summary.
1. `python3 scripts/deck.py check <id>` — owned vs. craft targets.
2. `python3 scripts/deck.py stats <id>` — types, curve, the ◊ (cheaper) /
   △ (added-cost) flags, and a **Functional roles** breakdown (heuristic count of
   removal / counters / card advantage / ramp / anthems). Use the roles numbers —
   especially the interaction total — to ground the Health scorecard instead of
   eyeballing "light on interaction". Treat printed MV skeptically for ◊/△ cards.
   **Read the uncertainty, not just the number.** The classifier reports a false
   negative as a FACT — a card it can't parse contributes 0, and 0 reads as "none".
   `stats` prints `7`, `3 +2?`, or `8 +4? (3 unclassified)` plus a "⚠ Possible
   UNDER-COUNT — verify" list and a `(classifier found no role for N noncreature
   spell(s))` line. **Read those cards' text before citing the count** — deck 40a
   was once graded on interaction 3 against a hand count of 7. Also record
   **protection** (real ward/hexproof/indestructible, not combat pumps): a ZERO
   against a `#: protect:` build-around is a finding, and it is reported but
   deliberately NOT in the tier floor, so only a human read surfaces it.
2c. `python3 scripts/deck.py consistency <id>` — the PROBABILITY layer `mana`
   lacks: keepable %, screw/flood, land-drop consistency, and per-card P(cast on
   curve) with a Karsten-style source recommendation. Run it whenever a splash, a
   double pip, or a top-end bomb is in question — it is what settles "is this
   actually castable" instead of hand-waving from a source count. Grade a modal /
   split / adventure card by the FACE YOU CAST: Decadent Dragon was drafted for
   its `{2}{B}` adventure half and cut once `consistency` priced its `{2}{R}{R}`
   FRONT face at 53% on turn four.
2c-bis. `python3 scripts/deck.py targets <id>` — do this deck's GATED cards have
   anything to point at? MV caps ("reanimate a creature MV 4 or less"), sacrifice
   costs and count thresholds all name a resource, and the count of cards satisfying
   it lives in the LIST, not in the card. Read this before cutting a gated card as
   weak — and before adding one. It is the automated half of the "state the count,
   then decide" discipline that overturned four dismissals.
   Its second block, STATE GATES, answers the mirror question and is the one that
   catches a bad CUT: a card gated on a game state the deck always reaches ("if you've
   drawn two or more cards this turn" in a deck built to draw two) is marked `free`,
   and a free condition is not a condition. Deck 43's Lake-town Toymaker was one
   confirmation from being cut as conditional while scoring fit 17 / power 2 / no
   detected role — its whole value was an interaction between three other cards. When
   a row says `free`, re-grade the card as if the clause were not there.

2d. `python3 scripts/deck.py engines <id>` — enabler ↔ payoff balance (dead
   payoffs / under-enabled engine), and `python3 scripts/deck.py shape <id>` for
   WIDE vs TALL. Themes structurally cannot answer shape — `counters` is the same
   tag whether they all go on one creature or spread across twelve — and reading
   `#: archetype:` prose instead of measuring produced a real misread (deck 30 was
   called a wide deck from its own header while the open question was whether a
   TALL plan duplicated it). The header is the older claim; the measurement wins.
2b. `python3 scripts/deck.py tier <id>` — the claimed `#: tier:` vs the tier its
   measurable quality vector supports. If the deck is being tuned to climb a tier,
   add `--to <NEXT>` (e.g. `--to A`): it prints the **exact measurable gap** (e.g.
   "+3 interaction") plus the owned, on-color, 0-wildcard cards that fill the short
   axis. Use this to make the tune **tier-targeted** — aim the Recommended-changes
   block at closing that specific axis, not generic "improvement." The tool does the
   arithmetic; the card SELECTION (which fillers preserve the engine/identity, what to
   cut) stays your judgment — protect signature/spice per the play-style profile.
3. `python3 scripts/deck.py mana <id>` — hybrid-aware color requirements. This,
   not stats' rough color identity, is the truth about how many sources each
   color needs. Hybrids don't demand their off-color.
4. `python3 scripts/deck.py tribes <id>` — creature subtypes and type-matters
   payoffs (which payoff cards reward which types, how many creatures qualify).
5. `python3 scripts/deck.py suggest <id>` — on-color, on-theme pool cards, owned
   vs. craftable with rarity (auto-filtered to the deck's format). Run it BOTH
   ways every time: `--owned --limit 0` to scour the whole collection for
   0-wildcard upgrades already in the roster, AND `--unowned` for craft targets
   (these feed Section 6 — always evaluate them, even for a fully-owned deck).
   **Add `--full`** so the picks come with full oracle text + keyword line + ⚠
   flags — grade every ADD from that text, not the tag-match line (same phased-
   ingestion discipline as `text`/`cuts`; the funnel is "shortlist cheap, read the
   finalists"). For a themed deep-read of the whole library or pool, `query.py
   --synergy X --full` / `pool.py --synergy X --full` dump full text + keywords too.
5b. **`suggest` alone is BLIND to structural needs — use the needs modes when the
   gap is structural.** The theme model answers "what SYNERGIZES"; it filters
   candidates to cards sharing a synergy theme, so a removal spell, a mana dork or
   a land can never surface through it no matter how badly the deck wants one.
   That is by design (the idf model was built to reject catch-alls) — the parallel
   path is `deck.py suggest <id> --needs` (fixing · acceleration · interaction in
   one view), or `--interaction` / `--ramp` / `--lands` individually. **If the
   scorecard says the deficit is interaction or mana, the fix comes from here, not
   from plain `suggest`.** Board-dependent removal is FLAGGED `⚠ scales w/ <axis>`
   with the deck's strength on that axis — grade those from text.
6. `python3 scripts/deck.py cuts <id>` — the ranked weakest-fit shortlist, with the
   full oracle text of the top candidates, a `⚠ context` flag on deck-dependent
   mechanics, `⚠interaction` on removal rows (with the deck's interaction count),
   `⚡` on a cost that is an UPSIDE in this deck, and `Pw`/`Uq` co-signals. It is a
   SHORTLIST SIGNAL, NOT A GRADE — it cannot see raw power or spice, so an
   off-theme bomb sorts high (Etali, whose text IS the deck's plan, sorted first in
   deck 24 purely because the classifier found no role on it). Read the printed
   text, then preview with `deck.py swap` before recommending. Also check the
   MIRROR of `⚡`: a fine card that fights your own engine (graveyard hate in a
   graveyard deck, hand attack against a deck you want holding cards) — no flag
   catches that, only a full-text read against the deck's plan. `cuts` now folds in a
   ✱ MULTIPLIER co-signal, because a doubler's value is in the rest of the deck and
   both halves of the cut score were blind to it — Delney, which doubles the triggered
   ability of every small creature in deck 46's engine layer, ranked as that deck's
   WEAKEST card while `suggest-homes` scored it correctly off the same primitive.
6a. **`python3 scripts/deck.py screen <id> <cards you are considering>`** — score a
   batch of candidates against the deck AS IT IS NOW, rather than against whatever
   plan it had when you last looked at them. Flags a ★ STRICT UPGRADE of a card
   already in the 60 (Prayer of Binding is Liminal Hold plus Flash, and nothing
   noticed while both sat in the same conversation) and a ✱ multiplier. Re-run it
   after any change of plan — stale verdicts are the failure it exists to prevent.
6b. `python3 scripts/deck.py flex <id>` — retire or retarget any `#~` line that is
   already stale before adding new ones, so the block doesn't accumulate two lines
   proposing the same cut.
7. For every card you'd cut OR keep, its full text is already in the Stage 1.0
   dump — a card's real value is in its text (tap engines, alt costs, token
   generation), which the tribes/curve/role tools miss.

**Grade-from-text rule (mandatory).** In the Stage 2 report, **quote the operative
oracle clause** for every card you cut, keep-as-signature, or swap — never a role
or tag label. If you can't quote it, you haven't read it: go back to the `text`
dump. This makes each grade auditable and is the enforced version of "read the
card."

**Verification pass (the secondary pass — do it before finalizing).** Re-read the
full text of every card named in a cut/keep/swap against this checklist, since a
label can hide any of them:
- **board-wide** — does it affect *all* creatures / permanents / each opponent?
  (a sweeper, an anthem, a team-buff, a one-sided wrath)
- **modal / leaves-play** — "choose one/two", or a trigger on dying / leaving /
  being sacrificed that changes its real value.
- **alt / added cost** — evoke/warp/flashback/kicker/station/improvise/affinity:
  the printed MV lies; grade the *effective* cost.
- **deck-dependent scaling** — converge/devotion/affinity/X/"for each artifact":
  check it against THIS deck's actual board, not in the abstract.
- **mis-grouping** — confirm the type line (a "land" or "Defender" may actually be
  an artifact-creature anchor that feeds your payoffs). If a re-read changes a
  grade, say so explicitly in the report ("on a full-text re-read, X is a keep
  because …").

## Stage 2 — Deliver a STRUCTURED report

Use these sections and headings, in order. Keep it scannable: severity- and
wildcard-tagged, with discrete swaps the user can accept or reject individually.

**1. Snapshot** — archetype · format · colors · card/land count · buildability
(owned N / craft M, with the wildcard breakdown by rarity). One status line.

**2. Health scorecard** — rate each dimension **Strong / OK / Weak** + one line:
mana base (sources vs. strict requirements, and the `consistency` cast-on-curve
numbers where a color is thin) · curve fit (for this archetype's speed; credit ◊
cost-reducers) · synergy density (theme/tribal count, payoff-to-enabler ratio from
`engines`) · interaction (amount AND type — the `stats` profile splits it by SPEED
and by whether anything answers a NONCREATURE permanent) · card advantage / reach ·
**protection** (can the deck defend the permanent it wins with? a ZERO against a
`#: protect:` card is a real finding) · consistency (redundancy vs. singleton
context). **Carry the count uncertainty into the rating** — write "interaction 6
(+2 unread)", never a bare 6, when `stats` flagged unclassified cards.

**3. Keep — validated strengths + signature/spice** — engines/cards that are
working; say *explicitly* not to cut them (guardrail against over-tuning). Split
out a **Signature & spice** line: the cards that give the deck its identity / fun
factor. At a creative-leaning style these are *protected* — never cut them for a
generic upgrade unless they're actively non-functional.

**4. Findings** — tagged **Critical / Moderate / Minor**, each grounded in card
text; separate problems from opportunities.

**5. Recommended changes** — ranked; each a discrete swap:
`− Out / + In` | wildcard cost (rarity + owned/craft) | impact deltas (creatures /
tribe / curve / color) | **two-axis verdict: power (helps/neutral/hurts) + fit/fun
(on-identity/neutral/off-identity)** | confidence. Rating both axes keeps the
power-vs-flavor trade visible instead of collapsing it into one "worth it." **If the
goal is a tier climb, lead with the swaps that close the `deck.py tier --to` gap**
(the specific axis it named — e.g. interaction) and say how far each moves it toward
the next floor, so the block is aimed at the target, not scattered.

**6. Craft upgrades** — ALWAYS run `deck.py suggest <id> --unowned` (it
auto-filters to the deck's `#: format:`) and surface the craftable cards that
would improve the deck, read from card text (don't trust the tag match). Do this
**even when the deck is fully owned**. **Tag every pick with an explicit weight so
the user never burns a wildcard on a lateral card:**
- **★ Marked upgrade** — fills a real gap or a large power jump. Worth the
  wildcard; lead with these.
- **~ Sidegrade** — lateral / ~85% of something you already run. Name it only to
  say *skip it* (unless the user specifically wants it).
- **· Minor** — marginal. Explicitly tell the user not to spend a wildcard.

`suggest --unowned` prints a **`Decks` column** (cross-deck reuse: how many of the
user's decks the card is castable + on-theme in). Factor it into the weight — a
card that's only a ~ sidegrade *here* but a marked upgrade in 2-3 other decks earns
its wildcard on reuse (tag it "~ here / ★ across the roster" and name the other
decks). A pick that fits only this deck is judged on this deck alone.

**Before recommending ANY craft, check whether an OWNED card already does ~the
same job** (from the `--owned` scan) — if one does, the craft is at best a
sidegrade: recommend the owned card and downgrade the craft's weight. If nothing
clears the ★ bar, say so plainly ("no craft target beats what you own"). Prefer a
lower-rarity card that does ~90% of a rare's job. For WIP decks, also give the
craft plan for the not-yet-owned cards. Offer to record the top picks as a flex
block (carry the ★/~/· weight into the block).

**7. Routes / branches** — when directions genuinely diverge (e.g. more tempo vs.
more midrange), present as forks with trade-offs, not one linear answer.

**8. Decisions for you** — judgment calls that hinge on preference/meta; surface
them, don't decide unilaterally.

**9. Bottom line** — the single highest-value move + the net wildcard spend.

## Criteria (rules the report must honor)

- **Ground every call in card text.** When the tools contradict a first-glance
  judgment, the data wins — say so.
- **Wildcard-aware always.** Tag every craft with rarity + a worth-it verdict;
  prefer owned or lower-rarity alternatives (an uncommon that does ~90% of a
  rare's job usually wins).
- **Judge against the deck's own intent/archetype**, not a generic ideal.
- **Discrete, individually-acceptable swaps** — never a monolithic "new list."
- **Show before/after deltas** for each change.
- **Respect singleton-vs-playset context** — tuning a 60-card highlander differs
  from a 4-of Standard list.

## Play-style weighting (creative ↔ competitive)

Apply the profile from Stage 0. The dial changes *recommendations*, never the
honesty of the data (always still report the by-the-numbers pick).

- **Creative-leaning** (default for this repo — see CLAUDE.md): optimize for
  interesting/entertaining play, not raw win-rate.
  - **Protect signature/spice cards** — don't cut a functional-but-quirky card
    just because a generic "better" option exists.
  - **Power-gap threshold for homogenizing swaps** — only suggest replacing a
    flavorful card with a staple when the power gap is *large*; otherwise keep
    the flavorful card and merely *note* the option.
  - **Reserve a fun budget** — leave ~15–20% of flex slots for pure-flavor picks
    even if suboptimal; call them out as intentional.
  - Frame trade-offs as choices ("the netdeck pick is X; your Y does ~85% and is
    more your style"), and lead with fit/fun in the two-axis verdict.
- **Competitive-leaning**: flip it — prioritize power, recommend the staples,
  minimal fun budget, lead with the power axis.
  - **Optimize consistency the "virtual copies first" way.** A singleton/highlander
    list draws a random slice of its plan; competitive quality wants redundancy. Run
    **`deck.py redundancy <id>`** — it flags the deck's *thin* effects and proposes
    **functional (virtual) copies FIRST** (distinct similar-but-different cards that do
    the same job, keeping the singleton feel), falling back to true **4-of duplicates**
    only when there aren't enough of acceptable quality. Prefer the functional fills;
    settle for duplicates only where the tool says a specific effect can't be
    diversified at comparable power. This is what lets a functionally-dense singleton
    grade A (the tier floor counts effects, not distinct cards) without losing its
    variety — grade the virtual copies from full text like any other add.
- **Balanced**: in between — surface both the staple and the spicy option and let
  the user pick.

## If asked to build it

Create a variant `<id>a`/`<id>b` (a full list — variants are self-contained), or
overwrite the base if the user wants it promoted to primary. Then show
`deck.py diff <base> <new>`, `deck.py mana <new>`, the Arena import block via
`deck.py arena <new>`, and the wildcard tally. Deck files save with a `.bak` and
must re-parse cleanly (INV-04).

**Then re-ground the prose the change just invalidated.** A tune moves the exact
figures the deck file argues from, so run:

```
python3 scripts/deck.py tier <id>                     # letter vs the new floor
python3 scripts/deck.py tier <id> --audit-rationale   # the ARGUMENT, not the letter
```

Fix every stale figure the audit names **in the same edit as the swap** — correcting
a quoted number to the live value is a factual correction, not a re-grade, so do it
directly. The tier LETTER is different: prompt the user, never auto-write it. Also
re-check `#: colors:` if the swap changed the deck's real castable colors (a stale
header manufactures phantom "uncastable" rows in `audit`/`mana`/`check`), and the
`# section` comment the add inherited from the cut — `swap --apply` warns on an
unambiguous mismatch, and a file that lies to the next reader is the cost of ignoring
it.

**Whenever you apply changes to a deck** (build or swap), finish by pasting the
`deck.py arena <id>` output — the clean, `Deck`-prefixed import block — directly
in chat. The user often imports on mobile (Arena → Decks → Import from clipboard)
and can't run the command themselves, so the raw file (with its `#` headers) is
useless to them; the pasted block is what they actually use.

## Recording flex swaps

When the report surfaces discrete swaps the user might want later (Section 5),
you can persist them as a **flex block** at the end of the deck file so they
travel with the deck instead of living only in chat. These are `#~` comment lines
— ignored by the parser, absent from the Arena export — so they're safe to append
to any list (see `decks/README.md` → *Flex section*):

```
# Flex — suggested swaps (comments; not part of the 60). See: deck.py flex <id>
#~ -Card Out | +Card In | one-line reason grounded in card text
```

Read them back with `deck.py flex <id>` (enriches each `+In` with cost, rarity,
owned count); the editing app shows them in a read-only panel. Promote one into
the 60 with `deck.py apply-flex <id> <n>` (dry-run by default; `--apply` writes a
`.bak` and drops the consumed flex line). To preview any swap's before/after
deltas first, use `deck.py swap <id> --cut A --add B` — it prints the real card
types (so a "vanilla flyer" that's actually a Bird won't slip past) plus the
card-count / creature / avg-MV / color-identity deltas.
