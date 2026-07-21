#!/usr/bin/env python3
"""Theme-coverage self-audit — the theme analog of deck.py's role_coverage_flags (#7).

Every recommendation (`suggest`, `cuts`, `suggest-homes`, fingerprints, engine analysis)
rides on the Synergies tags, so a card whose oracle text clearly plays a theme it ISN'T
tagged with silently distorts all of them. `tag_synergies` DERIVES these tags from text,
so a mismatch means a tag was hand-removed or went stale — worth a look.

To stay low-noise this only checks a handful of UNAMBIGUOUS mechanics (each `cue` is a
named keyword or a fixed template), and only flags a card when NONE of the theme's
satisfying tags is present (so a synonym tag — 'reanimator' for graveyard — isn't a
false positive). Owned cards only (the collection whose tag quality actually matters).
Folded into check_all as a SOFT, non-gating warning. Empty == healthy.
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import REPO_ROOT  # noqa: E402

LIB_CSV = os.path.join(REPO_ROOT, "card-library.csv")

# theme -> (text cues, tags that SATISFY the theme so it isn't flagged).
THEME_CUES = {
    "food":        ([r"\bfood\b"], {"food"}),
    "landfall":    ([r"\blandfall\b"], {"landfall", "lands-matter", "lands matter"}),
    "proliferate": ([r"\bproliferate\b"], {"proliferate", "counters"}),
    "convoke":     ([r"\bconvoke\b"], {"convoke", "go-wide", "tokens"}),
    "graveyard":   ([r"\bflashback\b", r"\bescape\b", r"\bdisturb\b", r"\bunearth\b", r"\bdredge\b"],
                    {"graveyard", "recursion", "reanimator", "escape", "flashback", "mill"}),
    "lifegain":    ([r"whenever you gain life"], {"lifegain", "lifegain-payoff", "life"}),
    "counters":    ([r"\+1/\+1 counter"], {"counters", "+1/+1 counters", "proliferate"}),
}
_COMPILED = {t: ([re.compile(p) for p in cues], sat) for t, (cues, sat) in THEME_CUES.items()}


def flags(limit=40):
    """[(card_name, theme, cue_keyword)] for owned cards whose text plays a theme they
    aren't tagged with. Deduped by (name, theme); capped at `limit`."""
    if not os.path.exists(LIB_CSV):
        return []
    out, seen = [], set()
    with open(LIB_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            name = (r.get("Card Name") or "").strip()
            text = (r.get("Card Text") or "").lower().replace("−", "-")
            if not name or not text:
                continue
            tags = {t.strip().lower() for t in (r.get("Synergies") or "").split(";") if t.strip()}
            for theme, (cues, satisfy) in _COMPILED.items():
                if tags & {s.lower() for s in satisfy}:
                    continue
                m = next((p for p in cues if p.search(text)), None)
                if m and (name.lower(), theme) not in seen:
                    seen.add((name.lower(), theme))
                    out.append((name, theme, m.pattern.strip("\\b")))
                    if len(out) >= limit:
                        return out
    return out


def check():
    """Human-readable strings for the flagged mis-tags (soft warnings). Empty == healthy."""
    return [f"{name}: text plays '{theme}' (cue: {cue}) but isn't tagged {theme} "
            "— re-run tag_synergies.py --merge or add the tag"
            for name, theme, cue in flags()]


def main():
    res = flags()
    if not res:
        print("Theme coverage: OK — no owned card is missing a high-confidence theme tag.")
        return 0
    print(f"{len(res)} owned card(s) may be missing a synergy tag their text implies:\n")
    for name, theme, cue in res:
        print(f"  {name:40} → {theme}  (cue: {cue})")
    print("\nFix by re-running `tag_synergies.py --merge`, or add the tag by hand if the "
          "heuristic is wrong. Advisory — tags are hand-editable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
