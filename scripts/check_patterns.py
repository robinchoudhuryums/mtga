#!/usr/bin/env python3
"""Dead-pattern gate — the check that would have caught this project's two most
expensive bugs on the spot.

Both were regex typos that COMPILED FINE and matched nothing:

  * `rf"... (?:[a-z-]+ ){0,2}?{_PERM_TYPE_LIST}"` — a bare `{0,2}` inside an
    f-string is a REPLACEMENT FIELD, so it compiled to the literal text
    `(0, 2)`. Every "destroy target creature" in the collection stopped
    matching; 46 decks silently lost their interaction count.
  * `r"return target creature.{0,40}?(?:owner|their) hand"` — requires the
    literal text "owner hand", but Magic writes "to its OWNER'S hand". Every
    unconditional bounce spell scored zero roles, for the whole life of the
    pattern.

Neither was caught by a unit test (each pattern was tested against a string the
author wrote to match it) nor by any invariant. Both were caught by a
roster-wide before/after diff — which only works if you remember to run one, and
only tells you that SOMETHING moved.

Two mechanical checks close that gap:

  1. LIVE-CORPUS — every classifier pattern must match at least one card in
     card-pool.csv (~15.8k cards). A pattern that matches nothing across the
     entire Arena pool is dead: a typo, or a phrasing Magic does not use. One
     hit is the right bar — several real patterns are genuinely narrow (the
     Aura library-tuck matches exactly one card), so anything stricter would
     false-flag a working pattern.
  2. FORMAT-LEAK — no compiled pattern's source may contain a Python tuple
     repr like `(0, 2)`. That is what a quantifier looks like AFTER an
     f-string ate it, so this catches the brace bug directly, at the point of
     the mistake, without needing a corpus at all.

Run standalone or via check_all.py.
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deck  # noqa: E402
import tag_synergies  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")

# A quantifier that has been through str.format / an f-string: `{0,2}` -> `(0, 2)`.
_TUPLE_LEAK_RE = re.compile(r"\(\d+, \d+\)")


def _pattern_groups():
    """(label, compiled, case) for every card-classifying pattern in the toolkit.

    Deliberately NOT every regex in the codebase — deck-file parsing patterns
    (LINE_RE, META_RE) match deck syntax, not card text, so a live-corpus check
    is meaningless for them. This is the set that reads ORACLE TEXT and whose
    silent failure mode is an under-count nobody sees.

    `case` is the text form the pattern is really run against: "norm" for the
    lowercased/unicode-minus-normalized form `classify_roles` uses, "raw" for
    the ones that read ORIGINAL-case text on purpose. The tribal-payoff scan is
    the second kind — Magic capitalizes real creature types but lower-cases
    generic "creatures"/"lands", which is the whole filter — so checking it
    against lowercased text would report four working patterns as dead. Feeding
    a pattern the wrong corpus is the same class of mistake this file exists to
    catch, so the distinction is explicit rather than assumed.
    """
    out = []
    for label, pats in deck._ROLE_COMPILED_MAP.items():
        out += [(f"role:{label}", p, "norm") for p in pats]
    for name in ("_INT_CUES", "_CA_CUES", "_LOOT_RE", "_PROTECTION_RE",
                 "_POWER_THRESHOLD_RE", "_MANA_PRODUCE_RE", "_RESTRICT_RE",
                 "_INT_COUNT_RE", "_INT_FIGHT_RE"):
        out.append((f"deck.{name}", getattr(deck, name), "norm"))
    for name in ("_NONCREATURE_ANSWER_CUES", "_WIDE_CUES", "_TALL_CUES"):
        out += [(f"deck.{name}", p, "norm") for p in getattr(deck, name)]
    for label, pats in deck._CONTEXT_COMPILED.items():
        out += [(f"context:{label}", p, "norm") for p in pats]
    out += [("tag_synergies._TRIBAL_PAYOFF_RES", p, "raw")
            for p in tag_synergies._TRIBAL_PAYOFF_RES]
    return out


def _pool_texts():
    """({"norm": [...], "raw": [...]}) — both forms of every pool card's text."""
    forms = {"norm": [], "raw": []}
    if not os.path.exists(POOL_CSV):
        return forms
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            raw = row.get("Card Text") or ""
            if not raw.strip():
                continue
            forms["raw"].append(raw)
            forms["norm"].append(deck._norm_role_text(raw))
    return forms


def check():
    """Return a list of hard-error strings (empty == pass)."""
    errors = []
    groups = _pattern_groups()

    # 2. FORMAT-LEAK — corpus-free, so it still fires on an empty/absent pool.
    for label, pat, _case in groups:
        leak = _TUPLE_LEAK_RE.search(pat.pattern)
        if leak:
            errors.append(
                f"{label}: pattern source contains a Python tuple repr "
                f"({leak.group(0)}) — a bare {{m,n}} quantifier inside an "
                f"f-string is a replacement field. Double the braces: "
                f"{{{{m,n}}}}.  /{pat.pattern[:90]}/")

    # 1. LIVE-CORPUS.
    forms = _pool_texts()
    if not forms["norm"]:
        # No pool to check against. Not an error — the pool is a derived file and
        # INV-03 already guards its existence; say so rather than pass silently.
        print("check_patterns: card-pool.csv unavailable — format-leak check only.")
        return errors
    for label, pat, case in groups:
        texts = forms[case]
        if not any(pat.search(t) for t in texts):
            errors.append(
                f"{label}: matches 0 of {len(texts)} cards in the Arena pool — "
                f"dead pattern (typo, or a phrasing Magic doesn't use). "
                f"/{pat.pattern[:90]}/")
    return errors


def main():
    errors = check()
    if errors:
        print(f"check_patterns: {len(errors)} dead/malformed pattern(s)")
        for e in errors:
            print(f"  ERROR: {e}")
        return 1
    print(f"check_patterns: {len(_pattern_groups())} card-text pattern(s) "
          f"all live against the pool. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
