#!/usr/bin/env python3
"""Agreement gate — two functions answering the SAME question must give the SAME answer.

Eleven gates verify that each model is CORRECT. Not one of them can see two models
that are each correct and disagree with each other, because every anchor evaluates a
function in isolation and a divergence only exists BETWEEN functions. That blind spot
produced the same bug five times in one cycle, always in the shape *the model was
right and the caller never asked*:

  | incident              | the model was right                       | the caller was wrong        |
  |-----------------------|-------------------------------------------|-----------------------------|
  | `cuts` multiplier     | doubler_axis/_support scored Delney right | rank_cut_candidates skipped |
  | `owned_role_fillers`  | craft_role_fillers filtered on format     | its owned sibling did not   |
  | `suggest --lands`     | the legality check existed                | the lands path skipped it   |
  | `rationale_staleness` | the per-deck check worked                 | nothing swept the roster    |
  | `_weakest_cut`        | rank_cut_candidates scored 9 terms        | the hint scored 3           |

Every one was found in production, and the fix each time was a one-off anchor for that
one pair (`check_suggest` #13 for the two breadth models, `tests/test_verify_ingest.py`
for the rebuild order). This gate is the general form of those: a registry of QUESTIONS,
each with two independent implementations and a shared input, asserting they agree.

Two design rules, both learned the expensive way in this repo:

  * **Prefer the LIVE ROSTER to a synthetic fixture** where the pair is deck-shaped.
    A synthetic case proves the pair agrees on the example its author wrote; only the
    roster shows a divergence nobody predicted. `_weakest_cut` vs `rank_cut_candidates`
    passed every pure-function anchor while disagreeing on 36 of 64 real decks.
  * **A stale entry is a failure.** A pair naming a function that no longer exists
    reads as a considered check while covering nothing — the same hand-kept-registry
    rot that put `check_patterns`' coverage list 13 patterns behind the code and that
    `_INLINE_PARSE_ALLOW` is screened for. Resolution happens by attribute lookup at
    run time, so a rename fails the build rather than silently skipping the pair.

NOT covered here, deliberately: pairs that already have a home. `check_suggest` #13
holds the two cross-deck-breadth models and `tests/test_verify_ingest.py` holds the
Makefile rebuild order — moving them would trade one registry for two.

Distribution-independent. check_all.py folds this in as a HARD gate. Run standalone
(``python3 scripts/check_agreement.py``). Returns a list of error strings; empty ==
healthy.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import deck  # noqa: E402
import lib  # noqa: E402

# Every (module, attribute) a registered pair depends on. Resolved at run time so a
# rename or deletion fails the build instead of quietly disabling the check.
REQUIRED = [
    ("deck", "_weakest_cut"), ("deck", "rank_cut_candidates"),
    ("deck", "cut_keep_score"), ("deck", "cut_scoring_context"),
    ("deck", "load_legalities"), ("deck", "_legality_of"),
    ("deck", "owned"), ("lib", "owned_qty"),
    ("deck", "_interaction_count"), ("deck", "role_tally"),
    ("deck", "_power_seed"), ("wishlist", "_seed_power"),
    ("deck", "owned_role_fillers"), ("deck", "craft_role_fillers"),
]


def _stale_entries():
    """A registered dependency that no longer exists. See the module docstring: an
    exemption or a check naming dead code covers nothing while reading as coverage."""
    errs = []
    for modname, attr in REQUIRED:
        try:
            mod = __import__(modname)
        except Exception as e:  # pragma: no cover - import guard
            errs.append(f"agreement registry: module {modname!r} unavailable "
                        f"({type(e).__name__}: {e})")
            continue
        if not hasattr(mod, attr):
            errs.append(f"agreement registry names {modname}.{attr}, which no longer "
                        "exists — a pair covering nothing. Update or remove the entry.")
    return errs


def _agree_weakest_cut(errs):
    """QUESTION: which card in this deck is the most cuttable?

    A: `rank_cut_candidates` — what `deck.py cuts` prints, what `tier --to` pairs its
       adds against, and what the recommendation ledger scores a swap by.
    B: `_weakest_cut` — the cut hint on every `suggest-homes` fit row.

    Checked on the LIVE ROSTER, because that is the only place the divergence was ever
    visible: B carried its own three-term formula and inherited none of the co-signals
    A gained (power, distinctiveness, multiplier, tribal, signature, saturation-aware
    role credit). They disagreed on 36 of 64 decks, and the disagreements were not
    cosmetic — B proposed cutting Bloom Tender from deck 17 and Vizier of the Menagerie
    from decks 34/36, the roster's best fixers and the exact cards `_is_color_fixer` was
    written to protect."""
    cardmeta = deck.load_card_meta()
    carddata = deck.load_card_data()
    bad = []
    for d in deck.roster_decks():
        meta, cards = deck.parse_deck_file(d["path"])
        if not cards:
            continue
        try:
            hint = deck._weakest_cut(meta, cards, cardmeta, carddata)
            rows, _c, _p, _i = deck.rank_cut_candidates(d)
        except Exception as e:
            errs.append(f"weakest-cut agreement errored on deck {d['id']} "
                        f"({type(e).__name__}: {e})")
            return
        if not rows or hint is None:
            continue
        if hint != rows[0][1]:
            bad.append(f"{d['id']}: suggest-homes hint {hint!r} vs cuts rank-1 "
                       f"{rows[0][1]!r}")
    if bad:
        errs.append("the two cut rankings disagree on the deck's most-cuttable card — "
                    "`suggest-homes` would print a cut `deck.py cuts` does not rank "
                    "first, and a user reconciling them by hand has no way to tell "
                    "which is the model. Route both through `cut_keep_score`.\n    "
                    + "\n    ".join(bad[:8])
                    + (f"\n    … and {len(bad) - 8} more" if len(bad) > 8 else ""))


def _agree_legality(errs):
    """QUESTION: which formats is this card legal in?

    A: `load_legalities()` — the whole-pool map used by `legal`, `audit`,
       `owned_role_fillers` and `functional_theme_options`.
    B: `_legality_of(names)` — the by-name lookup used by `resolve` and `screen`.

    Two independent readers of the same pool column, and this axis has broken twice in
    production (`suggest --lands` and `owned_role_fillers` each shipped without the
    check its sibling applied). They also normalise differently — A lowercases the
    format strings and B does not — which is latent only for as long as the pool keeps
    writing them lowercase, i.e. it is a data coincidence rather than a property."""
    full = deck.load_legalities()
    if not full:
        # Pool predates the Legalities column — nothing to compare, but say so: this
        # SOFT data state (a documented G-21 degradation, INV-03 only warns) was
        # silently switching off two-thirds of a HARD gate, on exactly the axis
        # (`owned_role_fillers` vs `craft_role_fillers`) that has gone vacuous twice
        # before (broad-scan BS2-32). A skipped pair must be visible in the gate's
        # own output, not indistinguishable from a passing one.
        lib.eprint("WARN:  check_agreement: legality pairs NOT exercised — card-pool.csv "
                   "has no Legalities column (rebuild with build_pool.py --all). The "
                   "quiet result here is 'unverified', not 'agreeing'.")
        return
    sample = sorted(full)[::97][:120]   # a spread across the pool, not the first N
    byname = deck._legality_of(sample)
    bad = []
    for n in sample:
        a = {x.lower() for x in full.get(n, set())}
        b = {x.lower() for x in byname.get(n, set())}
        if a != b:
            bad.append(f"{n!r}: load_legalities={sorted(a)} vs _legality_of={sorted(b)}")
    if bad:
        errs.append("the two pool-legality readers disagree — a card can then be legal "
                    "to `legal`/`audit` and illegal to `resolve`/`screen`, or the "
                    "reverse.\n    " + "\n    ".join(bad[:6]))


def _agree_owned(errs):
    """QUESTION: how many copies of this card do I own?

    A: `lib.owned_qty` — the shared front-face-aware join `check_dfc` locks.
    B: `deck.owned` — the deck-side helper, which returns (count, in_library).

    `check_dfc` anchors A and statically bans a RAW bypass, but it explicitly records
    that a function-misuse bug — a second helper that resolves the DFC split its own
    way — is not statically detectable. This is that residual, held behaviourally."""
    _, _, by_name_qty = deck.load_collection()
    if not by_name_qty:
        # LOUD, matching the discipline its two siblings already follow (BS2-32): an
        # empty collection silently turned this pair OFF, and "no disagreement found" is
        # indistinguishable from "nothing was compared" in the output. Quiet = unverified.
        errs.append("WARN: the ownership-join pair did not run — the collection index is "
                    "empty, so lib.owned_qty vs deck.owned is UNVERIFIED, not agreed.")
        return
    names = sorted(by_name_qty)[::37][:150]
    # Include real double-faced names, the case the two helpers can differ on.
    dfc = [n for n in deck.load_card_data() if " // " in n][:25]
    bad = []
    for n in names + dfc:
        if n in deck.BASICS:
            continue  # deck.owned treats a basic as unlimited by design
        a = lib.owned_qty(by_name_qty, n)
        b, _found = deck.owned(by_name_qty, n)
        if a != b:
            bad.append(f"{n!r}: lib.owned_qty={a} vs deck.owned={b}")
    if bad:
        errs.append("the two ownership joins disagree — the A3/A4/F6 class, where an "
                    "owned double-faced card reads as a craft target on one surface "
                    "and as owned on another.\n    " + "\n    ".join(bad[:6]))


def _agree_interaction(errs):
    """QUESTION: how much interaction does this deck run?

    A: `role_tally(...)["interaction"]` — the canonical count `stats`, `quality` and
       the tier floor all grade on.
    B: `_interaction_count` — what the roster `audit` column reports.

    Three separate counters used to disagree by ±1; B is a delegate today, and this
    holds it to that. The number decides a tier band, so a drift here re-grades decks."""
    carddata = deck.load_card_data()
    bad = []
    for d in deck.roster_decks():
        _meta, cards = deck.parse_deck_file(d["path"])
        if not cards:
            continue
        a = deck.role_tally(cards, carddata)["interaction"]
        b = deck._interaction_count(cards, carddata)
        if a != b:
            bad.append(f"{d['id']}: role_tally={a} vs _interaction_count={b}")
    if bad:
        errs.append("the interaction counters disagree — `audit` would flag a deck as "
                    "thin that `stats`/`tier` grade as fine.\n    "
                    + "\n    ".join(bad[:6]))


def _agree_power_seed(errs):
    """QUESTION: how powerful is this card, on the 0–10 rarity+role seed?

    A: `wishlist._seed_power` — what the wishlist writes into the Power column.
    B: `deck._power_seed` — the co-signal `suggest` and `cuts` read.

    B delegates to A, and this holds it there. `check_rankings` already anchors the
    WIRING of the rarity argument (letters vs words — F-01); this anchors the value."""
    try:
        import wishlist as wl
    except Exception as e:  # pragma: no cover - import guard
        errs.append(f"power-seed agreement skipped ({type(e).__name__}: {e})")
        return
    rows = [
        {"Rarity": "M", "Card Text": "Destroy target creature.", "Type": "Instant"},
        {"Rarity": "C", "Card Text": "Vanilla.", "Type": "Creature — Bear"},
        {"Rarity": "Rare", "Card Text": "Draw two cards.", "Type": "Sorcery"},
        {"Rarity": "", "Card Text": "", "Type": "Artifact"},
    ]
    for r in rows:
        a, b = wl._seed_power(r), deck._power_seed(r)
        if a != b:
            errs.append(f"power seed disagrees on {r['Type']!r}/{r['Rarity']!r}: "
                        f"wishlist._seed_power={a} vs deck._power_seed={b} — the "
                        "co-signal has stopped delegating.")


# The filters BOTH role-filler halves must apply. Expressed as shared invariants
# rather than equality, because the two answer the same question over DISJOINT
# inputs (owned vs unowned) and so can never return the same cards.
_ROLE_FILLER_DECKS = 3          # see the cap note in _agree_role_fillers
def _agree_role_fillers(errs):
    """QUESTION: which cards could fill role R in deck D?

    A: `owned_role_fillers` — the 0-wildcard half.
    B: `craft_role_fillers` — the wildcard-spend half.

    They can never return the same cards, so agreement here means agreeing on the
    FILTERS. That is exactly where they diverged: A skipped the format check B applied,
    and `tier --to A` printed the craft list headed "format-legal" with an unfiltered
    owned list directly above it, offering Deadly Dispute to a Standard deck. Owning a
    card is not a licence to play it — the pick costs no wildcard but still costs a
    deck slot."""
    legal = deck.load_legalities()
    if not legal:
        # Same loud-skip rule as _agree_legality (BS2-32): with no legality data the
        # `legs and fmt not in legs` guards below can never flag anything, so the
        # pair would pass while asserting nothing.
        lib.eprint("WARN:  check_agreement: role-filler format pair NOT exercised — "
                   "card-pool.csv has no Legalities column. Quiet = unverified.")
        return
    # BOTH axes `tier --to` asks for. Testing interaction alone was not enough: the
    # roster's only illegal interaction filler is Dovin's Veto and it is on-color for
    # decks 15-27, none of which fall in the sampled slice, so the check ran green
    # against the deleted filter. The card-advantage axis exposes Deadly Dispute on 32
    # decks including the first — and Deadly Dispute is the card the original bug
    # actually offered. A pair is only covered on the axes you ask about.
    role_sets = (("interaction", deck._INTERACTION_ROLES),
                 ("card advantage", {"Card advantage"}))
    bad = []
    # Capped, and saying so rather than truncating silently: `craft_role_fillers` walks
    # the whole ~15.8k-card pool per deck, so the roster sweep this gate prefers costs
    # ~7s here against ~2s for every other pair combined. The cap is defensible for THIS
    # pair specifically — the property is per-deck filter parity and the filters key on
    # the deck's `#: format:`, which is Standard for all 64 decks today, so deck 7 tests
    # exactly what deck 40 would. Raise it (or scope it by distinct format) the day the
    # roster spans more than one format, or the sample stops covering the input space.
    for d in deck.roster_decks()[:_ROLE_FILLER_DECKS]:
        meta, _cards = deck.parse_deck_file(d["path"])
        fmt = (meta.get("format") or "").strip().lower()
        if not fmt:
            continue
        # `limit` MUST be lifted. Both halves sort cheapest-first and then truncate, so
        # the default top-10 view is not the filtered SET — it is the cheap corner of
        # it, and an illegal card sitting below the cut is invisible. Verified: with the
        # default limit this check passed with the format filter deliberately deleted
        # from `owned_role_fillers`, i.e. it was green against the exact bug it names.
        for axis, roles in role_sets:
            for label, rows, name_at in (
                    ("owned", deck.owned_role_fillers(d, roles, limit=10_000), 1),
                    ("craft", deck.craft_role_fillers(d, roles, limit=10_000), 2)):
                for row in rows:
                    name = row[name_at]
                    nl = name.lower()
                    legs = legal.get(nl) or legal.get(nl.split(" // ")[0]) or set()
                    if legs and fmt not in legs:
                        bad.append(f"{d['id']} ({label} {axis}): {name!r} is not "
                                   f"{fmt}-legal")
    if bad:
        errs.append("the owned and craft role-filler halves apply different filters — "
                    "one of them is recommending a card the deck may not play.\n    "
                    + "\n    ".join(bad[:8]))


PAIRS = (_agree_weakest_cut, _agree_legality, _agree_owned,
         _agree_interaction, _agree_power_seed, _agree_role_fillers)


def check():
    """Run every registered agreement pair. Returns a list of error strings."""
    errs = _stale_entries()
    if errs:
        return errs
    for fn in PAIRS:
        try:
            fn(errs)
        except Exception as e:
            errs.append(f"{fn.__name__} errored ({type(e).__name__}: {e})")
    return errs


def main():
    errs = check()
    for e in errs:
        print(f"FAIL: {e}")
    if not errs:
        print(f"Model agreement: OK ({len(PAIRS)} question(s), both implementations "
              f"agree; role-filler parity sampled on {_ROLE_FILLER_DECKS} decks)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
