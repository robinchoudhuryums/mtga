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

Three mechanical checks close that gap:

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
  3. COMPLETENESS — every module-level compiled pattern in deck / lib /
     tag_synergies must be either REGISTERED above or explicitly EXCLUDED with
     a reason. Checks 1 and 2 only ever saw a hand-maintained list, and the
     list had silently fallen 13 patterns behind the code (broad-scan F-04):
     the whole of `lib.structural_distinctiveness`, every `_DOUBLER_AXES`
     matcher, `_DOUBLER_POWER_RE` and `_REMINDER_RE` were uncovered. The
     structural-distinctiveness miss was the dangerous one — `card_distinctiveness`
     returns `max(tag_score, structural)`, so a dead pattern there silently
     collapses the structural signal to 0 and the `max()` hides it. A gate whose
     coverage is hand-kept grows holes; this makes a new pattern fail the build
     until someone says what corpus it runs against.

Run standalone or via check_all.py.
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deck  # noqa: E402
import lib  # noqa: E402
import tag_synergies  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")

# A quantifier that has been through str.format / an f-string: `{0,2}` -> `(0, 2)`.
_TUPLE_LEAK_RE = re.compile(r"\(\d+, \d+\)")

# Modules whose module-level patterns the COMPLETENESS check enumerates.
_SCANNED_MODULES = (deck, lib, tag_synergies)

# Patterns that are NOT card-text classifiers, keyed (module, attribute) -> why.
# Every entry is a deliberate statement that a live-corpus check is meaningless
# here, not a place to park an inconvenient failure. Two families:
#   * deck-file / mana-symbol SYNTAX — matches the repo's own file formats, not
#     oracle text (the exclusion the original docstring already described).
#   * tier-RATIONALE prose — `_HISTORY_CUES` and friends read the `#: tier:`
#     argument a human wrote, so the Arena pool is the wrong corpus for them.
#     They are covered by unit tests in tests/test_deck.py instead, which is
#     where their documented false-negative history is pinned.
_EXCLUDED = {
    ("deck", "LINE_RE"): "deck-file card-line syntax, not card text",
    ("deck", "META_RE"): "deck-file `#:` header syntax, not card text",
    ("deck", "FORMAT_VARIANT_RE"): "deck-id/format syntax, not card text",
    ("deck", "_DECK_MARKER_RE"): "Arena paste `Deck` marker, not card text",
    ("deck", "SYMBOL_RE"): "mana-symbol syntax ({W}), not card text",
    ("lib", "_MANA_SYMBOL_RE"): "mana-symbol syntax ({W}), not card text",
    ("deck", "_HISTORY_CUES"): "tier-RATIONALE prose; unit-tested in test_deck.py",
    ("deck", "_COMPARISON_CUES"): "tier-RATIONALE prose; unit-tested in test_deck.py",
    ("deck", "_FIGURE_PAST"): "tier-RATIONALE prose; unit-tested in test_deck.py",
    ("deck", "_ARRIVING_CUES"): "tier-RATIONALE prose; unit-tested in test_deck.py",
    ("deck", "_ARRIVING_BREAK"): "tier-RATIONALE prose; unit-tested in test_deck.py",
    ("deck", "_DEPARTING_CUES"): "tier-RATIONALE prose; unit-tested in test_deck.py",
    ("deck", "_ARROW_AFTER"): "tier-RATIONALE prose; unit-tested in test_deck.py",
    ("deck", "_SIMILE_BEFORE"): "tier-RATIONALE prose (6-char lookbehind slice, not a "
                                "card-text corpus); unit-tested in test_deck.py",
    ("deck", "_EXCLUSION_CUES"): "deck-HEADER prose (wrong_exclusion_claims); "
                                 "unit-tested in test_deck.py",
    ("deck", "_EXCLUSION_PAREN"): "deck-HEADER prose punctuation, not card text; "
                                  "unit-tested in test_deck.py",
    ("deck", "_EXCLUSION_STOP"): "deck-HEADER prose punctuation (clause boundary), not "
                                 "card text; unit-tested in test_deck.py",
    ("deck", "_BELOW_FLOOR_ARGUMENT"): "tier-RATIONALE prose (F-07: does the header argue "
                                       "for grading UNDER the metrics floor); unit-tested "
                                       "in test_deck.py",
    ("deck", "_TRAILING_NOTE_RE"): "hand-typed card NAME normalization (strips a pile's "
                                   "'(needs Lessons)' note), not card text; unit-tested "
                                   "in test_deck.py::TestNameResolution",
    ("deck", "_SQUASH_RE"): "hand-typed card NAME normalization (punctuation-insensitive "
                            "match key), not card text; unit-tested in "
                            "test_deck.py::TestNameResolution",
    ("lib", "_BAK_STAMP_RE"): "`.bak` FILENAME stamp syntax (the creation timestamp "
                              "backup_path embeds, read back by latest_backup), not card "
                              "text; unit-tested in test_lib.py::TestBackupSelection",
}


def _pattern_groups():
    """(label, compiled, case) for every card-classifying pattern in the toolkit.

    Deliberately NOT every regex in the codebase — deck-file parsing patterns
    (LINE_RE, META_RE) match deck syntax, not card text, so a live-corpus check
    is meaningless for them. This is the set that reads ORACLE TEXT and whose
    silent failure mode is an under-count nobody sees. Everything deliberately
    left out is enumerated with a reason in `_EXCLUDED`, and the COMPLETENESS
    check fails the build on any pattern that is in neither place — so "not
    registered" can no longer mean "nobody noticed".

    `case` is the text form the pattern is really run against:
      "norm"   – the lowercased / unicode-minus-normalized form `classify_roles` uses.
      "raw"    – ORIGINAL-case text, on purpose. The tribal-payoff scan is this kind —
                 Magic capitalizes real creature types but lower-cases generic
                 "creatures"/"lands", which is the whole filter — so checking it
                 against lowercased text would report four working patterns as dead.
      "window" – run against a SHORT SLICE of a card's text, never the whole thing
                 (`_POWER_SCOPE_*` read `text[m.start()-25:m.start()]` and are
                 `$`-anchored). These match 0 of 15.8k whole texts BY CONSTRUCTION,
                 so the live-corpus check must skip them — registering them naively
                 would fail the build on two healthy patterns. They still get the
                 format-leak check, which needs no corpus.

    Feeding a pattern the wrong corpus is the same class of mistake this file exists
    to catch, so the distinction is explicit rather than assumed.
    """
    out = []
    for label, pats in deck._ROLE_COMPILED_MAP.items():
        out += [(f"role:{label}", p, "norm") for p in pats]
    # `targets`' gate table. These live NESTED in a list of tuples rather than as
    # module-level attributes, so the completeness check cannot see them and they were
    # uncovered — which is how the `permanent cards in your graveyard` gate shipped
    # digit-only and matched nothing at all. Registered explicitly so the live-corpus
    # check proves each one still matches a real card.
    out += [(f"target-gate:{kind}", rx, "norm") for rx, _label, kind in deck._TARGET_GATES]
    for name in ("_INT_CUES", "_CA_CUES", "_LOOT_RE", "_PROTECTION_RE",
                 "_POWER_THRESHOLD_RE", "_MANA_PRODUCE_RE", "_RESTRICT_RE",
                 "_INT_COUNT_RE", "_INT_FIGHT_RE",
                 # F-09b: the non-removal sibling of _INT_COUNT_RE — a card whose
                 # value is a COUNT in the deck ("damage equal to the number of
                 # Swamps you control") reads at its floor in every model here.
                 "_DECK_STATE_AXIS_RE",
                 # Added by broad-scan F-04 — live, but previously uncovered.
                 "_DOUBLER_POWER_RE", "_REMINDER_RE",
                 # Zone-conflict detector (the mirror of cost_upside_flags): which
                 # graveyards a card EMPTIES, and which it NEEDS populated. A dead
                 # pattern here silently stops the flag firing — the failure this whole
                 # gate exists for, and the reason the detector's own patterns were
                 # built by surveying real pool text rather than invented strings.
                 "_GY_HATE_OPP_RE", "_GY_HATE_ALL_RE", "_GY_HATE_CHOOSE_RE",
                 "_GY_OWN_SCOPE_RE", "_GY_NEED_OPP_RE",
                 # The rainbow-fixer detector behind suggest-homes' colour-count
                 # overlay. A dead pattern here is silent in BOTH directions: the
                 # broad half going dead demotes every real manabase fixer to a
                 # cost-discounted single source, and the single half going dead
                 # makes `_is_color_fixer` return False, which switches off the
                 # cut-side guard as well — so the tool resumes proposing that you
                 # cut your best fixer. Nothing would error.
                 "_FIXER_BROAD_RE", "_FIXER_SINGLE_RE"):
        out.append((f"deck.{name}", getattr(deck, name), "norm"))
    for name in ("_NONCREATURE_ANSWER_CUES", "_WIDE_CUES", "_TALL_CUES"):
        out += [(f"deck.{name}", p, "norm") for p in getattr(deck, name)]
    for label, pats in deck._CONTEXT_COMPILED.items():
        out += [(f"context:{label}", p, "norm") for p in pats]
    # The doubler co-signal: axis classification + its feeder counting. CLAUDE.md
    # calls the restriction half "load-bearing, not a nicety" (unrestricted support
    # over-counted Delney 6x and would have minted a false KEY), so a dead pattern
    # here mis-scores suggest-homes silently.
    for axis, pats in deck._DOUBLER_AXES.items():
        out += [(f"deck._DOUBLER_AXES[{axis}]", p, "norm") for p in pats]
    # `screen`'s strict-upgrade test normalises a card's SELF-REFERENCE before comparing
    # two cards' clauses. If this goes dead, modern "this creature"-templated cards stop
    # matching their own older "<Name>"-templated equivalents and the upgrade flag simply
    # never fires — a silent false negative in the one check built to catch a silent
    # false negative.
    out.append(("deck._UPGRADE_SELF_RE", deck._UPGRADE_SELF_RE, "norm"))
    # The whole of lib.structural_distinctiveness. card_distinctiveness returns
    # max(tag_score, structural), so a dead pattern here drops the structural signal
    # to 0 and the max() hides it — no error, no visible count change.
    for name in ("_STRUCT_NONETB_TRIGGER_RE", "_STRUCT_ACTIVATED_RE",
                 "_STRUCT_RULEBEND_RE", "_STRUCT_MODAL_RE", "_STRUCT_REMINDER_RE"):
        out.append((f"lib.{name}", getattr(lib, name), "norm"))
    out += [("tag_synergies._TRIBAL_PAYOFF_RES", p, "raw")
            for p in tag_synergies._TRIBAL_PAYOFF_RES]
    for name in ("_HEIST_CAST_LOOSE", "_HEIST_CAST_STRICT", "_HEIST_OPP_ZONE",
                 "_EXILE_CAST_ENABLE", "_EXILE_CAST_PAYOFF"):
        out.append((f"tag_synergies.{name}", getattr(tag_synergies, name), "norm"))
    for name in ("_POWER_SCOPE_MINE_RE", "_POWER_SCOPE_TOTAL_RE"):
        out.append((f"deck.{name}", getattr(deck, name), "window"))
    return out


def _module_patterns():
    """(module_name, attr_name, compiled) for every module-level pattern in the
    scanned modules — including those nested one level inside a list/tuple/dict
    value, which is where `_DOUBLER_AXES` and the role tables live."""
    out = []
    for mod in _SCANNED_MODULES:
        for name, obj in sorted(vars(mod).items()):
            if isinstance(obj, re.Pattern):
                out.append((mod.__name__, name, obj))
            elif isinstance(obj, (list, tuple)):
                out += [(mod.__name__, name, p) for p in obj if isinstance(p, re.Pattern)]
            elif isinstance(obj, dict):
                for v in obj.values():
                    for p in (v if isinstance(v, (list, tuple)) else [v]):
                        if isinstance(p, re.Pattern):
                            out.append((mod.__name__, name, p))
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

    # 3. COMPLETENESS — a pattern the registry never heard of is a pattern neither
    #    check above can see. Compared by IDENTITY, not source text, so two patterns
    #    that happen to share a source (deck.SYMBOL_RE / lib._MANA_SYMBOL_RE) can't
    #    vouch for each other.
    registered = {id(p) for _label, p, _case in groups}
    for mod_name, attr, pat in _module_patterns():
        if id(pat) in registered or (mod_name, attr) in _EXCLUDED:
            continue
        errors.append(
            f"{mod_name}.{attr}: compiled pattern is neither registered in "
            f"_pattern_groups() nor listed in _EXCLUDED — so neither the live-corpus "
            f"nor the dead-pattern check covers it. Register it with the corpus form "
            f"it runs against ('norm' / 'raw' / 'window'), or add "
            f"({mod_name!r}, {attr!r}) to _EXCLUDED with a reason.  /{pat.pattern[:70]}/")

    # 1. LIVE-CORPUS.
    forms = _pool_texts()
    if not forms["norm"]:
        # No pool to check against. Not an error — the pool is a derived file and
        # INV-03 already guards its existence; say so rather than pass silently.
        print("check_patterns: card-pool.csv unavailable — format-leak check only.")
        return errors
    for label, pat, case in groups:
        if case == "window":
            continue        # anchored to a text SLICE — see _pattern_groups' docstring
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
