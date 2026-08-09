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
from lib import REPO_ROOT, eprint  # noqa: E402

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
    """Lowercased set of every keyword the tagger already understands — mapped to a
    theme, on the explicit flavor denylist, or dropped by one-card suppression
    (`tag_synergies.is_noise_keyword`). That set has to be included here or the
    radar would report every keyword it silently drops as a "new unindexed mechanic",
    re-flooding the channel F-05 cleared."""
    import tag_synergies as ts
    known = ({k.lower() for k in ts.KEYWORD_THEMES}
             | {x.lower() for x in ts.FLAVOR_KEYWORDS})
    freq, corpus = ts.keyword_frequencies()
    known |= {k for k in freq if ts.is_noise_keyword(k, freq, corpus)}
    return known


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


def flavor_overreach(threshold=3):
    """Guard the FLAVOR_KEYWORDS denylist against over-suppression (audit F24).

    Three signals, all returned as (keyword, count, note):
      • a word in BOTH FLAVOR_KEYWORDS and KEYWORD_THEMES (count -1) — a
        contradiction: it's denylisted yet mapped to a theme.
      • a word denylisted BUT named in deck.py's ENGINE_THEMES patterns (count -2) —
        the engine classifier treats it as a real two-sided-engine mechanic while the
        tagger suppresses it. This is the blind spot that let `harmonize` sit
        denylisted for a full cycle: it's a graveyard self-recursion keyword
        ("cast this from your graveyard for its harmonize cost") that deck.py counts
        as a graveyard ENABLER, but the collection holds exactly ONE such card, so the
        owned-count signal below could never reach `threshold` and flag it.
      • a denylisted word on >= `threshold` OWNED cards (count = N) — flavor names
        are card-UNIQUE, so a denylisted word shared by several cards is likely a
        real mechanic being silently suppressed (e.g. a future set ships "Trance").
    Empty == healthy.
    """
    import tag_synergies as ts
    flavor = {k.lower() for k in ts.FLAVOR_KEYWORDS}
    themed = {k.lower() for k in ts.KEYWORD_THEMES}
    out = [(k, -1, "denylisted AND mapped in KEYWORD_THEMES — resolve the contradiction")
           for k in sorted(flavor & themed)]
    # Cross-check the ENGINE_THEMES regexes: a `\bword\b` pattern naming a denylisted
    # keyword means two subsystems disagree about whether it's a real mechanic.
    try:
        import deck as _dk
        engine_words = set()
        # `getattr(..., {})` would make a RENAME of ENGINE_THEMES return an empty dict and
        # take the silent-default path: the loop produces no engine words, the `-2` signal
        # evaporates, and the `except` below — added precisely so this could not die
        # quietly — never fires, because nothing raised. A structural error was loud while
        # the likeliest refactor was silent (BS4-26). Ask for the attribute directly.
        if not hasattr(_dk, "ENGINE_THEMES"):
            raise AttributeError(
                "deck.ENGINE_THEMES is gone (renamed?) — the engine-mechanic screen has "
                "nothing to read. Point this cross-check at its new name")
        for _theme, _sides in _dk.ENGINE_THEMES.items():
            for _role, _pats in _sides.items():
                for _p in _pats:
                    engine_words |= {m.lower() for m in re.findall(r"\\b([a-z][a-z'\- ]+)\\b", _p)}
        out += [(k, -2, "denylisted but named in deck.ENGINE_THEMES as a real engine "
                        "mechanic — the tagger suppresses what the engine classifier counts")
                for k in sorted(flavor & engine_words)]
    except Exception as e:
        # deck.py unavailable — the other two signals still run, but SAY so: this
        # is the signal built specifically for the `harmonize` blind spot, and a
        # bare pass meant a deck.py refactor of ENGINE_THEMES' shape killed it
        # with no "skipped" line anywhere — the one degraded path in the gate
        # suite that reported nothing (broad-scan batch 4).
        eprint(f"check_keywords: ENGINE_THEMES cross-check skipped "
               f"({type(e).__name__}: {e}) — the flavor-overreach signal is "
               f"running WITHOUT its engine-mechanic denylist screen")
    if not os.path.exists(MANA_CSV):
        return out
    owned = _owned_names()
    counts, example = {}, {}
    with open(MANA_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if (r.get("Card Name") or "").strip().lower() not in owned:
                continue
            for k in (r.get("Keywords") or "").split(";"):
                k = k.strip().lower()
                if k in flavor:
                    counts[k] = counts.get(k, 0) + 1
                    example.setdefault(k, (r.get("Card Name") or "").strip())
    out += [(k, c, f"denylisted but on {c} owned cards, e.g. {example[k]} — real mechanic?")
            for k, c in sorted(counts.items()) if c >= threshold]
    return out


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


def baseline_delta():
    """(newly_acknowledged, pruned) — what `--update-baseline` WOULD change.

    The keyword sibling of `check_roles.baseline_delta`, and it exists for the same
    reason (BS4-10/G-69): `_write_baseline` rewrites the file from the CURRENT unindexed
    set, so it cannot distinguish "one new set's mechanic" from "a `KEYWORD_THEMES` edit
    just un-indexed thirty keywords". Acknowledging one entry acknowledged every
    concurrent regression in the same run, and a bare total is what the caller printed.

    K-01 is the reason this matters more here than the count suggests: a keyword's
    reported COUNT is not its population (`jump` reports 13 cards of which 11 are
    `Jump-start`), so these entries have to be READ, one at a time, not tallied."""
    base = load_baseline()
    current = set(_signal_a(known_keywords(), _owned_names()))
    return (sorted(k for k in current if k not in base),
            sorted(k for k in base if k not in current))


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
    ap.add_argument("--max-new", type=int, default=0,
                    help="with --update-baseline, REFUSE to acknowledge more than N new "
                         "keywords in one run (0 = no limit). A large jump is a "
                         "KEYWORD_THEMES regression, not a new set")
    ap.add_argument("--show-delta", action="store_true",
                    help="with --update-baseline, print exactly what was acknowledged "
                         "and what stale entries were pruned")
    args = ap.parse_args()
    if args.update_baseline:
        # Same contract as check_roles: name what you acknowledge, and refuse a
        # regression-sized jump (BS4-10). A keyword especially must be READ rather than
        # tallied — K-01's `jump` reports 13 cards of which 11 are the wrong mechanic.
        new, pruned = baseline_delta()
        if args.max_new and len(new) > args.max_new:
            eprint(f"REFUSING to update the baseline: {len(new)} NEW unindexed keyword(s) "
                   f"exceeds --max-new {args.max_new}. A jump this size is usually a "
                   f"KEYWORD_THEMES/FLAVOR_KEYWORDS regression rather than a new set. "
                   f"Review them first:")
            for kw in new[:20]:
                eprint(f"    + {kw}")
            if len(new) > 20:
                eprint(f"    … and {len(new) - 20} more")
            return 1
        n = _write_baseline()
        print(f"Baseline updated: {n} acknowledged unindexed keyword(s) written to "
              f"{os.path.basename(BASELINE)}.")
        if new or pruned:
            print(f"  {len(new)} newly acknowledged, {len(pruned)} stale entr(ies) pruned.")
            show = args.show_delta or len(new) <= 10
            for kw in (new if show else new[:10]):
                print(f"    + {kw}   (NEW — READ the cards; a reported count is not a "
                      f"population, see K-01)")
            if not show and len(new) > 10:
                print(f"    … and {len(new) - 10} more (--show-delta for all)")
            if args.show_delta:
                for kw in pruned:
                    print(f"    - {kw}   (pruned)")
        else:
            print("  No change to the acknowledged set.")
        return 0
    # ALL THREE signals, exactly as check_all consumes them (BS2-C small leaks):
    # a standalone run used to report only the unindexed list — and, worse,
    # `stale_registry_entries` was DEFINED BELOW the `if __name__` guard, so under
    # `python3 scripts/check_keywords.py` the sys.exit fired before the function
    # existed at all. Anyone debugging a flavor_overreach or stale-registry warning
    # by re-running the gate by hand got a clean bill of health.
    res = check(text_shape=args.text_shape, include_baselined=args.all)
    over = flavor_overreach()
    stale = stale_registry_entries()
    if not (res or over or stale):
        print("No new unindexed mechanics (owned cards, vs baseline); no denylist "
              "overreach; no stale registry entries.")
        return 0
    if res:
        scope = "unindexed" if args.all else "NEW unindexed (since baseline)"
        print(f"{len(res)} {scope} mechanic(s) on owned cards — add each to "
              "tag_synergies KEYWORD_THEMES (a synergy) or FLAVOR_KEYWORDS (flavor):\n")
        for kw, ex, sig in res:
            print(f"  [{sig:10}] {kw:26} e.g. {ex}")
    for kw, _n, note in over:
        print(f"  FLAVOR_KEYWORDS overreach: {kw!r} — {note}")
    for reg, kw, note in stale:
        print(f"  stale {reg} entry {kw!r} — {note}")
    return 0


def stale_registry_entries():
    """Hand-kept keyword registries whose entries no longer match any card in the corpus.

    `FLAVOR_KEYWORDS` (the "this is card-unique flavour, not a mechanic" denylist) and
    `keyword_baseline.txt` (the acknowledged-but-unindexed list) are both maintained by
    hand, and both only ever grow — nothing prunes them when a set rotates out of the
    pool or a keyword is renamed. A stale entry is a suppression with nothing behind it:
    harmless in isolation, but it makes the registry look considered while covering
    nothing, and it silently pre-suppresses the name if a FUTURE set reuses it for a real
    mechanic. That is the same shape `check_patterns`' coverage list had before the
    completeness check (broad-scan F-04), so it gets the same treatment: make it
    falsifiable instead of trusting that someone pruned it.

    SOFT by design — unlike a stale colour-parse exemption, a stale keyword entry breaks
    no invariant and suppresses nothing real, so it is a tidy-up prompt, not a build
    failure. Returns [(registry, keyword, note)]; empty == healthy. Never raises.
    """
    out = []
    try:
        # Lazy, matching this file's existing style (flavor_overreach imports deck the
        # same way) so an import problem degrades to a skip rather than breaking the
        # module for the checks that don't need it.
        import tag_synergies
        freq, corpus = tag_synergies.keyword_frequencies()
    except Exception as e:                      # pragma: no cover - corpus unavailable
        return [("(registry audit)", "-", f"skipped: {e}")]
    # Below the corpus floor the frequency table is library-scoped, where a pool-wide
    # mechanic can legitimately sit on zero owned cards (the `harmonize` case). Judging
    # staleness there would produce exactly the false positives this check must not add.
    if corpus < tag_synergies._NOISE_MIN_CORPUS:
        return out
    for kw in sorted(tag_synergies.FLAVOR_KEYWORDS):
        if freq.get(kw.lower(), 0) == 0:
            out.append(("FLAVOR_KEYWORDS", kw,
                        "denylisted but on no card in the corpus — the set it came from "
                        "is gone; drop it so the denylist keeps meaning something"))
    try:
        baseline = load_baseline()
    except Exception:                           # pragma: no cover
        baseline = set()
    for kw in sorted(baseline):
        if freq.get(kw.lower(), 0) == 0:
            out.append(("keyword_baseline.txt", kw,
                        "acknowledged-but-unindexed, yet on no card in the corpus — "
                        "drop it (check_keywords.py --update-baseline rewrites the file)"))
    return out


if __name__ == "__main__":
    sys.exit(main())
