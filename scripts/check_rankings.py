#!/usr/bin/env python3
"""Anchor sanity checks for the wishlist ranking model (wishlist.py).

Guards the exact regression that shipped once this session: a change to the
theme model (collapsing variant decks) lowered every idf value, silently
pushing a real tribal theme ("Villain", central to ~5 decks) below the hard
`SPECIFIC_IDF = 1.5` cutoff — so Doctor Doom and other bombs were mislabeled
"generic/no-theme" and dumped to Tier C.

These checks are DISTRIBUTION-based, not card-name based, so they keep working
as cards are crafted off the wishlist:

  1. The "specific theme" cutoff must classify a theme central to only a small
     share of decks (<= ~n/5) as SPECIFIC — the Doom-class guard.
  2. It must classify a BROAD theme (central to >= ~n/2 decks) as generic.
  3. End-to-end: a synthetic card sharing a rare theme must NOT score
     "generic/no-theme"; a card with only broad/evergreen themes MUST.

Run standalone (`python3 scripts/check_rankings.py`) or via check_all.py.
Returns a list of human-readable error strings; empty == healthy.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check():
    """Return a list of error strings (empty == healthy). Never raises."""
    try:
        import wishlist
    except Exception as e:  # pragma: no cover - import guard
        return [f"ranking model: could not import wishlist.py ({e})"]

    try:
        fps, idf, spec = wishlist._theme_model()
    except Exception as e:
        return [f"ranking model: _theme_model() raised {type(e).__name__}: {e}"]

    n = len(fps)
    if n < 4:
        return []  # too few decks to assert a distribution meaningfully

    non = {t.lower() for t in getattr(wishlist, "NON_SIGNAL_TAGS", set())}
    df = Counter()
    for _id, _cols, central, _tw in fps:
        for t in central:
            df[t] += 1

    errs = []
    rare_cap = max(2, n // 5)
    broad_floor = max(3, n // 2)
    rare = [t for t, c in df.items() if 2 <= c <= rare_cap and t.lower() not in non]
    broad = [t for t, c in df.items() if c >= broad_floor]

    # (1) a small-share strategic theme must clear the "specific" cutoff.
    misfiled = sorted(t for t in rare if idf.get(t, 0) < spec)
    if misfiled:
        errs.append(
            f"ranking model: specific-theme cutoff TOO STRICT — themes central to "
            f"<= {rare_cap} of {n} decks scored generic: {', '.join(misfiled[:6])} "
            f"(cutoff idf >= {spec:.2f}). This is the Doctor-Doom-class regression "
            f"(a real tribe read as 'generic/no-theme'). Recalibrate SPECIFIC_MAX_FRAC.")

    # (2) a broad theme must NOT be treated as specific signal.
    wrong = sorted(t for t in broad if idf.get(t, 0) >= spec)
    if wrong:
        errs.append(
            f"ranking model: specific-theme cutoff TOO LOOSE — broad themes central to "
            f">= {broad_floor} of {n} decks scored specific: {', '.join(wrong[:6])}.")

    # (3) end-to-end: a card on a rare theme is a real match, not 'review'.
    if rare:
        t = rare[0]
        home = next((f for f in fps if t in f[2]), None)
        if home:
            cols = "".join(sorted(home[1]))
            synth = {"Card Name": "__anchor_rare__", "Rarity": "Rare",
                     "Color(s)": cols, "Synergies": f"{t}; etb; tokens",
                     "Target": "", "Power": "5"}
            s = wishlist._rank_scores([synth])[0]
            if s["conf"] == "review" or s["sig"] == "generic/no-theme":
                errs.append(
                    f"ranking model: an anchor card sharing the specific theme {t!r} "
                    f"misfiled as '{s['sig']}' (conf {s['conf']}) — should be a real match.")

    # (4) end-to-end: a card with only broad/evergreen themes IS 'review'.
    synth2 = {"Card Name": "__anchor_generic__", "Rarity": "Rare", "Color(s)": "",
              "Synergies": "etb; tokens; mana", "Target": "", "Power": "5"}
    try:
        s2 = wishlist._rank_scores([synth2])[0]
        if s2["conf"] != "review":
            errs.append(
                f"ranking model: a purely-generic anchor card should be 'review' "
                f"but scored conf {s2['conf']} (sig {s2['sig']!r}).")
    except Exception as e:
        errs.append(f"ranking model: _rank_scores() raised {type(e).__name__}: {e}")

    return errs


def main():
    errs = check()
    if errs:
        print("Ranking model sanity: FAIL")
        for e in errs:
            print(f"  ✗ {e}")
        return 1
    print("Ranking model sanity: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
