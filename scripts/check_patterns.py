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
import wishlist  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")

# A quantifier that has been through str.format / an f-string: `{0,2}` -> `(0, 2)`.
_TUPLE_LEAK_RE = re.compile(r"\(\d+, \d+\)")

# Modules whose module-level patterns the COMPLETENESS check enumerates.
# wishlist was OUTSIDE this perimeter (broad-scan BS-04): its `_FLEX_REMOVAL_RE`
# (the Meteor-Sword flex-removal seed bonus) and `_CONDITIONAL_POWER_RE` (the G-19
# `pow~` flag) are oracle-text classifiers with the exact silent-death failure mode
# this gate exists for — and check_rankings' anchor 7 stays green with the flex
# bonus dead, so nothing else would notice.
_SCANNED_MODULES = (deck, lib, tag_synergies, wishlist)

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
    ("deck", "_CLAUSE_BREAK"): "tier-RATIONALE prose (clause bounds for the 2026-08-09 "
                               "suppression scoping); unit-tested in test_deck.py",
    ("deck", "_OTHER_DECK_RE"): "tier-RATIONALE prose (a 'deck N' reference marks a "
                                "cross-deck clause); unit-tested in test_deck.py",
    ("deck", "_OTHER_DECK_POSS_RE"): "tier-RATIONALE prose (the POSSESSIVE sibling of "
                                     "_OTHER_DECK_RE — \"68a's 12 green sources\" is a "
                                     "cross-deck clause the word-anchored form cannot "
                                     "see); unit-tested in test_deck.py",
    ("deck", "_FIG_SOURCE_WANT"): "tier-RATIONALE prose (a 'want N sources' target is "
                                  "not a claim about the current list — `deck.py "
                                  "consistency` prints that line and it gets pasted in "
                                  "verbatim); unit-tested in test_deck.py",
    ("deck", "_SHARING_CUES"): "tier-RATIONALE prose (a SHARING claim asserts the card "
                               "is in THIS deck, so the cross-deck suppression is "
                               "skipped there); unit-tested in test_deck.py",
    ("deck", "_POPULATION_SUBJECT_RE"): "tier/archetype-RATIONALE prose (a figure whose "
                                        "subject is the card POPULATION, not this list); "
                                        "unit-tested in test_deck.py",
    ("deck", "_NEGATION_AFTER"): "tier-RATIONALE prose (positional contrast-citation "
                                 "suppressor); unit-tested in test_deck.py",
    ("deck", "_SIMILE_BEFORE"): "tier-RATIONALE prose (6-char lookbehind slice, not a "
                                "card-text corpus); unit-tested in test_deck.py",
    ("deck", "_FIGURE_PCT_AFTER"): "tier/note-RATIONALE prose (a '%' right after a "
                                   "matched figure means it is a percentage, not an "
                                   "avg MV); unit-tested in test_deck.py",
    ("deck", "_FIGURE_DRAW_BEFORE"): "tier/note-RATIONALE prose (a 'draw N' count that "
                                     "the card-advantage pattern matched by adjacency); "
                                     "unit-tested in test_deck.py",
    ("deck", "_FIGURE_PAST_CUE"): "`#~ note:` RATIONALE prose (the shared _FIGURE_PAST "
                                  "cues re-read CLAUSE-scoped, because a build log is "
                                  "history-dense); unit-tested in test_deck.py",
    ("deck", "_EXCLUSION_CUES"): "deck-HEADER prose (wrong_exclusion_claims); "
                                 "unit-tested in test_deck.py",
    ("deck", "_EXCLUSION_PAREN"): "deck-HEADER prose punctuation, not card text; "
                                  "unit-tested in test_deck.py",
    ("deck", "_EXCLUSION_STOP"): "deck-HEADER prose punctuation (clause boundary), not "
                                 "card text; unit-tested in test_deck.py",
    ("deck", "_BELOW_FLOOR_ARGUMENT"): "tier-RATIONALE prose (F-07: does the header argue "
                                       "for grading UNDER the metrics floor); unit-tested "
                                       "in test_deck.py",
    ("deck", "_WANTS_UNDER_GRADE_FLAG"): "tier-RATIONALE prose (the override on "
                                         "_BELOW_FLOOR_ARGUMENT: does the header defer "
                                         "the call to a human it wants prompted); "
                                         "unit-tested in test_deck.py",
    ("deck", "_TRAILING_NOTE_RE"): "hand-typed card NAME normalization (strips a pile's "
                                   "'(needs Lessons)' note), not card text; unit-tested "
                                   "in test_deck.py::TestNameResolution",
    ("deck", "_SQUASH_RE"): "hand-typed card NAME normalization (punctuation-insensitive "
                            "match key), not card text; unit-tested in "
                            "test_deck.py::TestNameResolution",
    ("lib", "_BAK_STAMP_RE"): "`.bak` FILENAME stamp syntax (the creation timestamp "
                              "backup_path embeds, read back by latest_backup), not card "
                              "text; unit-tested in test_lib.py::TestBackupSelection",
    ("wishlist", "LINE_RE"): "wishlist-batch card-line syntax (mirrors deck.LINE_RE), "
                             "not card text",
    # Surfaced by the BS2-13 deep walk — previously below the walker's depth, so
    # they were silently exempt rather than declared. Declared now, with the same
    # reasoning as their _HISTORY_CUES siblings.
    ("deck", "_RATIONALE_FIGURES"): "tier-RATIONALE prose (quoted figures); "
                                    "unit-tested in test_deck.py",
    ("deck", "_SECTION_EXPECTATIONS"): "deck-file `# section` comment prose, not card "
                                       "text; unit-tested via section_mismatch tests",
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
    # Same treatment for the STATE gates, and for the same reason one layer over: they
    # are the family that answers "can this deck REACH the condition", so a pattern that
    # quietly matches nothing reads as "this deck has no gated cards" — indistinguishable
    # from a clean result, which is precisely how the digit-only descend gate hid.
    out += [(f"state-gate:{kind}", rx, "norm") for rx, _label, kind in deck._STATE_GATES]
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
                 "_GY_OWN_SCOPE_RE", "_GY_NEED_OPP_RE", "_GY_CONSUME_OPP_RE",
                 # The mana-ability detector behind the early-drop threat/mana split. It
                 # goes dead in the quiet direction — every early drop reads as a threat
                 # again, which is exactly the pre-fix behaviour.
                 "_MANA_SOURCE_RE",
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
    # Same corpus form and the same reason: a card TYPE the text builds around is
    # capitalized in oracle text ("crews a Vehicle"), so these run on the raw form.
    out += [("tag_synergies._TYPE_MATTERS_RES", p, "raw")
            for p in tag_synergies._TYPE_MATTERS_RES]
    for name in ("_HEIST_CAST_LOOSE", "_HEIST_CAST_STRICT", "_HEIST_OPP_ZONE",
                 "_EXILE_CAST_ENABLE", "_EXILE_CAST_PAYOFF"):
        out.append((f"tag_synergies.{name}", getattr(tag_synergies, name), "norm"))
    # GRANTED-keyword scan. One pattern per evergreen keyword, nested in a dict rather
    # than bound as module attributes, so the completeness check cannot see them
    # individually — the same shape that let `_TARGET_GATES` ship a gate matching nothing.
    # Registered per keyword so a single dead one is named, not averaged away: these run
    # in a loop that appends on the FIRST match, so a dead entry looks exactly like a
    # keyword nobody grants.
    out += [(f"tag_synergies._GRANT_RES[{kw}]", rx, "norm")
            for kw, rx in tag_synergies._GRANT_RES.items()]
    # The two REJECTION filters for that scan. They are not classifiers — they decide
    # what the scan throws AWAY — but a dead rejection filter fails silently and in the
    # expensive direction: it stops rejecting, and opponent-facing grants ("creatures your
    # opponents control gain haste") start tagging as if they were yours. A live-corpus
    # check proves each still matches real oracle text.
    for name in ("_GRANT_OPP_RE", "_GRANT_NEG_RE"):
        out.append((f"tag_synergies.{name}", getattr(tag_synergies, name), "norm"))
    for name in ("_POWER_SCOPE_MINE_RE", "_POWER_SCOPE_TOTAL_RE"):
        out.append((f"deck.{name}", getattr(deck, name), "window"))
    # tapland_profile (G-25/G-60-style report-only tempo context in `consistency`)
    for name in ("_TAPLAND_RE", "_TAPLAND_COND_RE"):
        out.append((f"deck.{name}", getattr(deck, name), "norm"))
    # wishlist's oracle-text classifiers (BS-04): the flex-removal seed bonus and the
    # G-19 conditional-power (`pow~`) flag. If _FLEX_REMOVAL_RE goes dead, the seed
    # ranking's other terms keep check_rankings green, so this is the ONLY gate that
    # would notice. Both compile with re.I, so the norm corpus is the right one
    # (_CONDITIONAL_POWER_RE also reads Mana Cost for `{x}` — its text alternatives
    # alone are what the live-corpus check proves alive, which is enough).
    for name in ("_FLEX_REMOVAL_RE", "_CONDITIONAL_POWER_RE"):
        out.append((f"wishlist.{name}", getattr(wishlist, name), "norm"))
    # The two-sided engine tables and the cost-as-upside detector (BS2-13): 68
    # oracle-text classifiers that lived below the old walker's one-level depth,
    # so neither the live-corpus nor the completeness check ever saw them — which
    # is how a sacrifice-payoff pattern matching 0 pool texts shipped and stayed.
    # engine_roles lowercases with the same −→- normalization classify_roles uses,
    # and _COST_UPSIDE compiles re.I, so the norm corpus is right for both.
    for theme, sides in deck._ENGINE_COMPILED.items():
        for role, pats in sides.items():
            out += [(f"engine:{theme}/{role}", p, "norm") for p in pats]
    out += [(f"deck._COST_UPSIDE[{i}]", rx, "norm")
            for i, (rx, _themes, _why) in enumerate(deck._COST_UPSIDE)]
    return out


def _walk_patterns(obj, _depth=0):
    """Every re.Pattern reachable inside nested lists/tuples/dicts/sets, any depth.

    The predecessor descended exactly ONE container level, so `_ENGINE_COMPILED`
    (dict → dict → list, depth three) and every list-of-TUPLES table
    (`_COST_UPSIDE`, `_TARGET_GATES`, `_RATIONALE_FIGURES`) were invisible to the
    completeness check — 90 of 419 module-level patterns, 68 of them oracle-text
    classifiers, outside every check. Not latent: an engine payoff pattern that
    matched 0 of ~15.9k pool texts shipped and sat dead behind a green gate, the
    exact failure this file's own docstring is about (broad-scan BS2-13). Depth
    is capped only to guard against a cyclic structure."""
    if _depth > 6:
        return
    if isinstance(obj, re.Pattern):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_patterns(v, _depth + 1)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for v in obj:
            yield from _walk_patterns(v, _depth + 1)


def _module_patterns():
    """(module_name, attr_name, compiled) for every module-level pattern in the
    scanned modules, at ANY nesting depth (see `_walk_patterns`)."""
    out = []
    for mod in _SCANNED_MODULES:
        for name, obj in sorted(vars(mod).items()):
            out += [(mod.__name__, name, p) for p in _walk_patterns(obj)]
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

    # 3b. _EXCLUDED STALENESS — every sibling gate screens its hand-kept registry
    #     from inside check() (check_colors' allowlist, check_commands' exemptions,
    #     check_agreement's REQUIRED, check_keywords' registries); this one's screen
    #     lived only in the pytest layer, which the dependency-free integrity
    #     workflow cannot run (Batch C small leaks). An entry naming a vanished
    #     attribute suppresses nothing while looking considered.
    mods = {m.__name__: m for m in _SCANNED_MODULES}
    for mod_name, attr in sorted(_EXCLUDED):
        mod = mods.get(mod_name)
        if mod is None:
            errors.append(f"_EXCLUDED entry ({mod_name!r}, {attr!r}): module "
                          f"{mod_name!r} is not in _SCANNED_MODULES — stale entry.")
        elif not hasattr(mod, attr):
            errors.append(f"_EXCLUDED entry ({mod_name!r}, {attr!r}): no such attribute "
                          f"any more — the exclusion covers nothing; remove it.")

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
