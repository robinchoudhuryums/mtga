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
"""
import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import REPO_ROOT  # noqa: E402

BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "role_baseline.txt")


def load_baseline():
    """Lowercased set of acknowledged zero-role card names."""
    if not os.path.exists(BASELINE):
        return set()
    with open(BASELINE, encoding="utf-8") as fh:
        return {ln.strip().lower() for ln in fh if ln.strip() and not ln.startswith("#")}


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


def main():
    ap = argparse.ArgumentParser(description="Radar for cards with no detected functional role.")
    ap.add_argument("--all", action="store_true", help="show every zero-role card (ignore baseline)")
    ap.add_argument("--update-baseline", action="store_true", help="acknowledge the current set")
    ap.add_argument("--limit", type=int, default=40, help="max rows to print (0 = all)")
    args = ap.parse_args()
    if args.update_baseline:
        n = _write_baseline()
        print(f"Baseline updated: {n} acknowledged zero-role card(s) written to "
              f"{os.path.basename(BASELINE)}.")
        return 0
    res = check(include_baselined=args.all)
    if not res:
        print("No new zero-role cards (roster, vs baseline).")
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
