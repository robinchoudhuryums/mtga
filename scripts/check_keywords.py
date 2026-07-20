#!/usr/bin/env python3
"""check_keywords.py — radar for NEW card mechanics the synergy tagger doesn't index.

When a new set ships a keyword/mechanic, it falls through tag_synergies'
KEYWORD_THEMES map — tagged verbatim or dropped — so its synergies never register.

Scryfall reports hundreds of "keywords" across Arena's full history (most are
card-unique flavor names like "Blizzaga"), so a raw scan is pure noise. Instead
this is a **delta radar**:

  known    = KEYWORD_THEMES keys ∪ FLAVOR_KEYWORDS  (already handled)
  baseline = scripts/keyword_baseline.txt           (acknowledged-but-unindexed)
  scope    = keywords on cards you OWN (card-library.csv) — the ones actually tagged

`check()` returns only unindexed keywords that are NOT in the baseline — i.e.
mechanics that appeared since the baseline was last refreshed (a new set landed).
check_all.py folds this in as a soft, non-gating warning; because it's baselined,
it stays quiet until something genuinely new shows up.

Triage a flag by adding the keyword to tag_synergies.KEYWORD_THEMES (a real
synergy) or FLAVOR_KEYWORDS (a flavor name), then re-run; or acknowledge the whole
current set with `--update-baseline`.

  python3 scripts/check_keywords.py                 # new-since-baseline (owned)
  python3 scripts/check_keywords.py --all           # every unindexed owned keyword
  python3 scripts/check_keywords.py --text-shape     # + the '<Word> —' heuristic
  python3 scripts/check_keywords.py --update-baseline  # acknowledge current set
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import REPO_ROOT  # noqa: E402

MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")
LIB_CSV = os.path.join(REPO_ROOT, "card-library.csv")
POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")
BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keyword_baseline.txt")

import re  # noqa: E402

_B_STOP = {
    "choose", "i", "ii", "iii", "iv", "v", "vi", "sacrifice", "discard", "spend",
    "search", "target", "when", "whenever", "at", "as", "then", "each", "put",
    "create", "draw", "exile", "return", "destroy", "level", "the", "this", "you",
}
_LINE_RE = re.compile(r"^([A-Z][A-Za-z'’]+(?: [A-Z][A-Za-z'’]+){0,2})\s+—")


def known_keywords():
    """Lowercased set of every keyword the tagger already understands."""
    import tag_synergies as ts
    return ({k.lower() for k in ts.KEYWORD_THEMES}
            | {x.lower() for x in ts.FLAVOR_KEYWORDS})


def _owned_names():
    names = set()
    if os.path.exists(LIB_CSV):
        with open(LIB_CSV, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                n = (r.get("Card Name") or "").strip().lower()
                if n:
                    names.add(n)
                    names.add(n.split(" // ")[0])
    return names


def load_baseline():
    if not os.path.exists(BASELINE):
        return set()
    with open(BASELINE, encoding="utf-8") as fh:
        return {ln.strip().lower() for ln in fh if ln.strip() and not ln.startswith("#")}


def unknown_for_card(keywords_str, known=None):
    """Scryfall keywords on ONE card not recognized — for card.py's per-card line."""
    known = known if known is not None else known_keywords()
    return [k.strip() for k in (keywords_str or "").split(";")
            if k.strip() and k.strip().lower() not in known]


def _signal_a(known, owned):
    """Unindexed Scryfall keywords on OWNED cards → {keyword: example_card}."""
    found = {}
    if not os.path.exists(MANA_CSV):
        return found
    with open(MANA_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            name = (r.get("Card Name") or "").strip()
            if name.lower() not in owned:
                continue
            for k in (r.get("Keywords") or "").split(";"):
                k = k.strip()
                if k and k.lower() not in known:
                    found.setdefault(k.lower(), name)
    return found


def _signal_b(known, owned, min_cards=3):
    counts, example = {}, {}
    for path in (LIB_CSV, POOL_CSV):
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if (r.get("Card Name") or "").strip().lower() not in owned:
                    continue
                for line in (r.get("Card Text") or "").split("\n"):
                    m = _LINE_RE.match(line.strip())
                    if not m:
                        continue
                    key = m.group(1).lower()
                    if key in known or key.split()[0] in known or key.split()[0] in _B_STOP:
                        continue
                    counts[key] = counts.get(key, 0) + 1
                    example.setdefault(key, (r.get("Card Name") or "").strip())
    return {k: example[k] for k, c in counts.items() if c >= min_cards}


def check(text_shape=False, include_baselined=False):
    """[(mechanic, example, signal)] of unindexed mechanics on owned cards. By
    default only those NOT in the baseline (genuinely new); empty == healthy."""
    known = known_keywords()
    owned = _owned_names()
    base = set() if include_baselined else load_baseline()
    out = [(kw, ex, "keyword") for kw, ex in sorted(_signal_a(known, owned).items())
           if kw not in base]
    if text_shape:
        seen = {k for k, _, _ in out}
        for kw, ex in sorted(_signal_b(known, owned).items()):
            if kw not in base and kw not in seen and kw.split()[0] not in seen:
                out.append((kw, ex, "text-shape"))
    return out


def _write_baseline():
    known, owned = known_keywords(), _owned_names()
    kws = sorted(_signal_a(known, owned))
    with open(BASELINE, "w", encoding="utf-8") as fh:
        fh.write("# Acknowledged-but-unindexed card keywords (mostly Universe-Beyond\n")
        fh.write("# flavor names). check_keywords.py flags only mechanics NOT here — a\n")
        fh.write("# new set's mechanic. Triage into tag_synergies, or re-run\n")
        fh.write("# `check_keywords.py --update-baseline` to acknowledge the current set.\n")
        for k in kws:
            fh.write(k + "\n")
    return len(kws)


def main():
    ap = argparse.ArgumentParser(description="Radar for unindexed card mechanics.")
    ap.add_argument("--all", action="store_true", help="show every unindexed owned keyword (ignore baseline)")
    ap.add_argument("--text-shape", action="store_true", help="also run the '<Word> —' heuristic")
    ap.add_argument("--update-baseline", action="store_true", help="acknowledge the current unindexed set")
    args = ap.parse_args()
    if args.update_baseline:
        n = _write_baseline()
        print(f"Baseline updated: {n} acknowledged unindexed keyword(s) written to "
              f"{os.path.basename(BASELINE)}.")
        return 0
    res = check(text_shape=args.text_shape, include_baselined=args.all)
    if not res:
        print("No new unindexed mechanics (owned cards, vs baseline).")
        return 0
    scope = "unindexed" if args.all else "NEW unindexed (since baseline)"
    print(f"{len(res)} {scope} mechanic(s) on owned cards — add each to "
          "tag_synergies KEYWORD_THEMES (a synergy) or FLAVOR_KEYWORDS (flavor):\n")
    for kw, ex, sig in res:
        print(f"  [{sig:10}] {kw:26} e.g. {ex}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
