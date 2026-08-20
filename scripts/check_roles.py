#!/usr/bin/env python3
"""check_roles.py — radar for cards `classify_roles` reads as having NO functional role.

WHY THIS EXISTS. `deck._ROLE_PATTERNS` is a WHITELIST of phrasings, and a whitelist's
failure mode is silent: a card whose effect is templated a way no pattern anticipates
scores ZERO roles, and every consumer downstream — the tier floor, the `cuts` ranking,
the `quality` guard, `check_all`'s own reporting — inherits that as fact. It is never
an error and never an over-count, always an invisible under-count.

Eight such holes were found in one 2026-08 session, every one of them by a HUMAN
reading a card rather than by any gate:

  · the split "choose target X … destroy the chosen permanent" template (Quag Feast)
  · "creature or enchantment" where "creature or planeswalker" was indexed
  · damage "divided as you choose among" where "to target" was indexed
  · scaling damage sized by anything other than a power reference
  · a spelled-out Clue token where only the `investigate` KEYWORD was indexed
  · impulse ("exile the top card, you may play it") — not indexed at all
  · the ramp pattern requiring a literal `{` after "add", so EVERY any-colour source
    ("{T}: Add one mana of any color") read as roleless
  · casting off the top of your library

Quag Feast, Combustion Technique, Zuko and Bloom Tender were all ZERO-role cards. This
gate makes that population visible.

HOW IT WORKS — the `keyword_baseline.txt` design, applied to roles:

  scope    = every nonland, non-blank-text card in any decks/*.txt file
  zero     = those `deck.classify_roles()` returns nothing for
  baseline = scripts/role_baseline.txt (acknowledged: genuinely roleless, or a known
             hole nobody has triaged yet)

`check()` returns only the zero-role cards NOT in the baseline, so it stays quiet until
a deck edit or a new set introduces one. check_all.py folds it in as a SOFT, non-gating
warning — a roleless card breaks no invariant, and a real vanilla creature is a
legitimate zero.

READ THE NUMBER AS A DELTA, NOT A TARGET. The baseline is large (a few hundred) and a
meaningful fraction of it is genuinely roleless — vanilla bodies, pure combat tricks,
build-arounds whose value is in another card. The gate's job is that the set only ever
shrinks, and that a NEW zero gets looked at once.

  python3 scripts/check_roles.py                  # new-since-baseline
  python3 scripts/check_roles.py --all            # every zero-role card, ignore baseline
  python3 scripts/check_roles.py --update-baseline # acknowledge the current set

SECOND SWEEP — WHERE THE TWO MODELS DISAGREE (BS6-10 follow-up).

The zero-role radar above is ROSTER-scoped, and that scope is deliberate: the pool is
16k cards, 5,368 of them nonland with no role, so a pool-wide zero list is 33% of the
pool and unreadable as a worklist. But roster scope is also why the radar could not see
BS6-10 — the removal Auras it missed are cards you do not own, and unowned cards are
exactly the recommender's candidate set.

`tag_role_disagreements()` is the pool-scoped sweep that IS readable, because it asks a
narrower question: which cards does `tag_synergies` call `removal` on the strength of
their TEXT, while `deck.classify_roles` gives them no interaction role at all? Two
models, one question, different answers — K-09's rule, and the shape that surfaced Dead
Weight (tagged `removal`, scored nothing, and it is the ROLE model that feeds
`tier_band`).

Scoped by CONSTRUCTION, not by an allowlist:

  · It reads the tagger's OWN `MECHANIC_RULES` predicates rather than a copy of them, so
    a third text rule added there is swept automatically and the two cannot drift.
  · The KEYWORD path (`deathtouch` → removal, `fight` → removal) is excluded because it
    lives in KEYWORD_THEMES, not MECHANIC_RULES. That matters: deathtouch is a fair claim
    about a BODY and not about spot removal, and it is 250 of the 388 raw disagreements —
    an allowlist would have had to enumerate them, and this does not.

Baselined like its sibling, and read the same way: a DELTA, not a target. A large share
of what remains is legitimate divergence — the tagger's `"exile target"` substring also
fires on graveyard hate, and its `gets -N/-N` also fires on a self-shrink. The job is
that the set only ever shrinks, and that a NEW disagreement gets looked at once.

  python3 scripts/check_roles.py --tags           # new-since-baseline disagreements
  python3 scripts/check_roles.py --tags --all     # every disagreement
  python3 scripts/check_roles.py --update-tag-baseline
"""
import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import REPO_ROOT, eprint  # noqa: E402

BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "role_baseline.txt")
TAG_BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "tag_role_baseline.txt")


def _load(path):
    """Lowercased set of acknowledged card names from a baseline file."""
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        return {ln.strip().lower() for ln in fh if ln.strip() and not ln.startswith("#")}


def load_baseline():
    """Lowercased set of acknowledged zero-role card names."""
    return _load(BASELINE)


def load_tag_baseline():
    """Lowercased set of acknowledged tagger-vs-classifier disagreements."""
    return _load(TAG_BASELINE)


def _roster_cards():
    """{lowercased name: (display name, type, text)} for every nonland card with text
    that appears in any deck file. Deck-scoped rather than pool-scoped on purpose: the
    pool is ~30k cards and most of them will never be graded, so a pool-wide scan would
    be noise. A card in a deck is a card some model has already been asked about."""
    import deck as D
    cd = D.load_card_data()
    out = {}
    for path in glob.glob(os.path.join(REPO_ROOT, "decks", "*", "*.txt")):
        try:
            _meta, cards = D.parse_deck_file(path)
        except Exception:
            continue
        for _q, name, _s, _c in cards:
            key = name.lower()
            if key in out:
                continue
            card = cd.get(key)
            if not card:
                continue
            ctype = card.get("type") or ""
            if "Land" in ctype:
                continue
            text = (card.get("text") or "").strip()
            if not text:
                continue          # K-11: genuinely text-less vanillas are expected
            out[key] = (card.get("name") or name, ctype, text)
    return out


def zero_role_cards():
    """[(name, type, text)] for every roster card `classify_roles` returns nothing for.

    Sorted by NAME, which is a total order — a set plus a tie-able sort key is a
    nondeterministic output (G-54), and this feeds a file that gets diffed."""
    import deck as D
    out = []
    for _key, (name, ctype, text) in _roster_cards().items():
        if not D.classify_roles(text):
            out.append((name, ctype, text))
    return sorted(out, key=lambda r: r[0].lower())


def check(include_baselined=False):
    """[(name, type, text)] of zero-role cards NOT in the baseline; empty == healthy."""
    base = set() if include_baselined else load_baseline()
    return [r for r in zero_role_cards() if r[0].lower() not in base]


def _removal_text_rules():
    """The tagger's OWN text predicates for the `removal` tag, read live from
    `tag_synergies.MECHANIC_RULES` — never a copy.

    A copy is the drift this repo keeps paying for: the point of this sweep is that two
    models disagree, so re-implementing one of them here would compare a model against a
    stale imitation of itself. Reading the rules live also means a third text rule added
    to the tagger is swept on arrival rather than when someone remembers.

    Returns [] if tag_synergies is unavailable, which the caller turns into an explicit
    skip rather than a silent clean bill."""
    from tag_synergies import MECHANIC_RULES
    return [pred for tag, pred in MECHANIC_RULES if tag == "removal"]


def tag_role_disagreements():
    """[(name, type, text)] — pool cards the TAGGER calls `removal` on the strength of
    their text, while `classify_roles` gives them no interaction role at all.

    The KEYWORD path is excluded by construction, not by an allowlist: `deathtouch` and
    `fight` map to `removal` through `KEYWORD_THEMES`, which this never touches. That is
    250 of the 388 raw disagreements, and every one is a fair claim about a BODY rather
    than about spot removal — enumerating them would have been an allowlist that rots.

    Sorted by NAME (G-54: this feeds a diffed file, so the key must be a total order)."""
    import csv as _csv
    import deck as D
    rules = _removal_text_rules()
    pool = os.path.join(REPO_ROOT, "card-pool.csv")
    if not rules or not os.path.exists(pool):
        return []
    interaction = D._INTERACTION_ROLES
    out, seen = [], set()
    with open(pool, newline="", encoding="utf-8") as fh:
        for r in _csv.DictReader(fh):
            name = (r.get("Card Name") or "").strip()
            text = (r.get("Card Text") or "").strip()
            key = name.lower()
            if not name or not text or key in seen:
                continue
            tline = (r.get("Type") or "")
            if not any(_safe(p, tline.lower(), text.lower()) for p in rules):
                continue
            if D.classify_roles(text) & interaction:
                continue
            seen.add(key)
            out.append((name, tline, text))
    return sorted(out, key=lambda x: x[0].lower())


def _safe(pred, tline, text):
    """Run a tagger predicate the way `tags_for` does — swallowing a bad regex rather
    than letting one malformed rule take the whole sweep down."""
    import re as _re
    try:
        return bool(pred(tline, text))
    except _re.error:
        return False


def check_tags(include_baselined=False):
    """[(name, type, text)] of disagreements NOT in the tag baseline; empty == healthy."""
    base = set() if include_baselined else load_tag_baseline()
    return [r for r in tag_role_disagreements() if r[0].lower() not in base]


def stale_baseline_entries():
    """[(name, why)] for baseline entries that no longer describe a zero-role roster
    card — the pruning half the baseline never had (broad-scan BS-19).

    keyword_baseline gets `check_keywords.stale_registry_entries`; this is the same
    guard for roles. Two stale shapes, and the first is the dangerous one: a card a
    pattern fix UN-ZEROED stays acknowledged forever, so a later regression
    re-zeroing it is silent for good — the baseline quietly converts from "known
    holes" into a mask. The second (the card left every deck) acknowledges nothing,
    since the scan is roster-scoped. `--update-baseline` clears both, but only this
    check makes them VISIBLE instead of waiting for someone to diff the file."""
    base = load_baseline()
    if not base:
        return []
    roster = _roster_cards()
    zero = {r[0].lower() for r in zero_role_cards()}
    out = []
    for nm in sorted(base):
        if nm not in roster:
            out.append((nm, "no longer in any deck — the roster-scoped entry acknowledges nothing"))
        elif nm not in zero:
            out.append((nm, "now classifies with roles — prune it, or a regression "
                            "re-zeroing this card is silent forever"))
    return out


def baseline_delta():
    """(newly_acknowledged, pruned) — what `--update-baseline` WOULD change.

    `--update-baseline` rewrites the file from the current zero-role set, so it is
    all-or-nothing: it cannot tell "one genuinely roleless new card" from "a
    `_ROLE_PATTERNS` edit just re-zeroed fifty cards". That is tolerable when a human
    runs it after reading the new entries, and it was NOT what happened — `make
    postedit` ran it unconditionally, BEFORE `check_all`, so the radar's warning was
    consumed by the same command that was supposed to surface it (BS4-02). Exposing the
    delta is what lets the caller show its work instead of absorbing it.

    `newly_acknowledged` carries DISPLAY names — a human is supposed to read these and
    go look the card up, and the lowercased comparison key is worse at both."""
    base = load_baseline()
    rows = zero_role_cards()
    zero = {r[0].lower() for r in rows}
    return (sorted((r[0] for r in rows if r[0].lower() not in base), key=str.lower),
            sorted(n for n in base if n not in zero))


def _write_baseline():
    rows = zero_role_cards()
    with open(BASELINE, "w", encoding="utf-8") as fh:
        fh.write("# Cards in decks/ that deck.classify_roles() scores with NO functional\n")
        fh.write("# role. ACKNOWLEDGED, not approved: some are genuinely roleless (vanilla\n")
        fh.write("# bodies, pure combat tricks, build-arounds whose value sits on another\n")
        fh.write("# card), and some are classifier holes nobody has triaged yet.\n")
        fh.write("#\n")
        fh.write("# This list should only ever SHRINK. A new entry means either a deck edit\n")
        fh.write("# introduced an untriaged card or a pattern regressed.\n")
        fh.write("# `check_roles.py --update-baseline` to acknowledge the current set.\n")
        for name, _t, _x in rows:
            fh.write(name + "\n")
    return len(rows)


def tag_baseline_delta():
    """(newly_acknowledged, pruned) for the disagreement baseline — the same delta its
    sibling exposes, and for the same reason (G-69): an acknowledge step that does not
    NAME what it is acknowledging cannot tell one new card from a pattern regression
    that just re-flagged fifty."""
    base = load_tag_baseline()
    rows = tag_role_disagreements()
    cur = {r[0].lower() for r in rows}
    return (sorted((r[0] for r in rows if r[0].lower() not in base), key=str.lower),
            sorted(n for n in base if n not in cur))


def _write_tag_baseline():
    rows = tag_role_disagreements()
    with open(TAG_BASELINE, "w", encoding="utf-8") as fh:
        fh.write("# Pool cards that tag_synergies calls `removal` on the strength of their\n")
        fh.write("# TEXT, while deck.classify_roles() gives them NO interaction role.\n")
        fh.write("# K-09's rule — the two models must agree on the same text — held as a\n")
        fh.write("# baselined worklist rather than a hard gate, because a large share of\n")
        fh.write("# this list is LEGITIMATE divergence: the tagger's \"exile target\"\n")
        fh.write("# substring also fires on graveyard hate, and its `gets -N/-N` also\n")
        fh.write("# fires on a self-shrink. Neither is spot removal.\n")
        fh.write("#\n")
        fh.write("# The deathtouch/fight KEYWORD path is not in here at all — it is\n")
        fh.write("# excluded by construction, since this sweep reads MECHANIC_RULES only.\n")
        fh.write("#\n")
        fh.write("# Read as a DELTA, not a target. This list should only ever SHRINK; a\n")
        fh.write("# NEW entry means a pattern regressed or a set introduced a templating\n")
        fh.write("# one model reads and the other does not. That is how BS6-10 was found.\n")
        fh.write("# `check_roles.py --update-tag-baseline` to acknowledge the current set.\n")
        for name, _t, _x in rows:
            fh.write(name + "\n")
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description="Radar for cards with no detected functional role.")
    ap.add_argument("--all", action="store_true", help="show every zero-role card (ignore baseline)")
    ap.add_argument("--update-baseline", action="store_true", help="acknowledge the current set")
    ap.add_argument("--limit", type=int, default=40, help="max rows to print (0 = all)")
    ap.add_argument("--max-new", type=int, default=0,
                    help="with --update-baseline, REFUSE to acknowledge more than N new "
                         "zero-role cards in one run (0 = no limit). A large jump is a "
                         "pattern regression, not a batch of new cards — see --show-delta")
    ap.add_argument("--show-delta", action="store_true",
                    help="with --update-baseline, print exactly which cards were newly "
                         "acknowledged and which stale entries were pruned")
    ap.add_argument("--tags", action="store_true",
                    help="run the TAGGER-vs-CLASSIFIER sweep instead: pool cards "
                         "tag_synergies calls `removal` from their text while "
                         "classify_roles gives them no interaction role (K-09)")
    ap.add_argument("--update-tag-baseline", action="store_true",
                    help="acknowledge the current disagreement set (--tags baseline)")
    args = ap.parse_args()
    if args.update_tag_baseline:
        # Same G-69 discipline as its sibling: name what is being acknowledged, and
        # refuse a jump big enough to be a pattern regression rather than new cards.
        new, pruned = tag_baseline_delta()
        if args.max_new and len(new) > args.max_new:
            eprint(f"REFUSING to update the tag baseline: {len(new)} NEW disagreement(s) "
                   f"exceeds --max-new {args.max_new}. Review them first:")
            for nm in new[:20]:
                eprint(f"    + {nm}")
            if len(new) > 20:
                eprint(f"    … and {len(new) - 20} more")
            return 1
        n = _write_tag_baseline()
        print(f"Tag baseline updated: {n} acknowledged disagreement(s) written to "
              f"{os.path.basename(TAG_BASELINE)}.")
        if new or pruned:
            print(f"  {len(new)} newly acknowledged, {len(pruned)} stale entr(ies) pruned.")
            show = args.show_delta or len(new) <= 10
            for nm in (new if show else new[:10]):
                print(f"    + {nm}   (NEW — read the card; the two models disagree on it)")
            if not show and len(new) > 10:
                print(f"    … and {len(new) - 10} more (--show-delta for all)")
            if args.show_delta:
                for nm in pruned:
                    print(f"    - {nm}   (pruned)")
        else:
            print("  No change to the acknowledged set.")
        return 0
    if args.tags:
        res = check_tags(include_baselined=args.all)
        if not res:
            print("No new tagger-vs-classifier disagreements (pool, vs baseline).")
            return 0
        scope = "disagreement" if args.all else "NEW disagreement (since baseline)"
        print(f"{len(res)} {scope}(s) — tag_synergies reads these as `removal` from their\n"
              f"text while classify_roles scores no interaction role. Some are legitimate\n"
              f"(graveyard hate, a self-shrink); the rest are _ROLE_PATTERNS holes.\n")
        shown = res if args.limit == 0 else res[:args.limit]
        for name, ctype, text in shown:
            print(f"  {name}   [{ctype[:34]}]")
            print(f"      {text.splitlines()[0][:96]}")
        if len(res) > len(shown):
            print(f"  … and {len(res) - len(shown)} more (--limit 0 for all)")
        return 0
    if args.update_baseline:
        # ALWAYS compute the delta first. A bulk rewrite that prints only a total is
        # indistinguishable from a mask (BS4-02): the count moves, nobody reads which
        # cards moved, and a re-zeroing pattern edit is acknowledged wholesale.
        new, pruned = baseline_delta()
        if args.max_new and len(new) > args.max_new:
            eprint(f"REFUSING to update the baseline: {len(new)} NEW zero-role card(s) "
                   f"exceeds --max-new {args.max_new}. A jump this size is usually a "
                   f"_ROLE_PATTERNS regression re-zeroing cards that used to classify, "
                   f"not a batch of genuinely roleless new cards. Review them first:")
            for nm in new[:20]:
                eprint(f"    + {nm}")
            if len(new) > 20:
                eprint(f"    … and {len(new) - 20} more")
            eprint("Then re-run with a higher --max-new (or none) to acknowledge them.")
            return 1
        n = _write_baseline()
        print(f"Baseline updated: {n} acknowledged zero-role card(s) written to "
              f"{os.path.basename(BASELINE)}.")
        # Name what changed, unconditionally for a small delta. The whole failure mode
        # is a number nobody reads standing in for cards nobody looked at.
        if new or pruned:
            print(f"  {len(new)} newly acknowledged, {len(pruned)} stale entr(ies) pruned.")
            show = args.show_delta or len(new) <= 10
            for nm in (new if show else new[:10]):
                print(f"    + {nm}   (NEW — read the card; a pattern hole is fixable)")
            if not show and len(new) > 10:
                print(f"    … and {len(new) - 10} more (--show-delta for all)")
            if args.show_delta:
                for nm in pruned:
                    print(f"    - {nm}   (pruned)")
        else:
            print("  No change to the acknowledged set.")
        return 0
    stale = stale_baseline_entries()
    if stale:
        print(f"{len(stale)} STALE baseline entr(ies) — run --update-baseline after reviewing:")
        for nm, why in stale[:20]:
            print(f"  {nm} — {why}")
        if len(stale) > 20:
            print(f"  … and {len(stale) - 20} more")
        print()
    res = check(include_baselined=args.all)
    if not res:
        print("No new zero-role cards (roster, vs baseline)."
              + (" (stale entries above still need pruning)" if stale else ""))
        return 0
    scope = "zero-role" if args.all else "NEW zero-role (since baseline)"
    print(f"{len(res)} {scope} card(s) in decks/ — each is either genuinely roleless or a\n"
          f"gap in deck._ROLE_PATTERNS. Read the text, then fix the pattern or baseline it.\n")
    shown = res if args.limit == 0 else res[:args.limit]
    for name, ctype, text in shown:
        print(f"  {name}   [{ctype[:34]}]")
        print(f"      {text.splitlines()[0][:96]}")
    if len(res) > len(shown):
        print(f"  … and {len(res) - len(shown)} more (--limit 0 for all)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
