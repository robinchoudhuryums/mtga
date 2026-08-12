#!/usr/bin/env python3
"""Anchor sanity checks for color-identity parsing (lib.card_colors + its call sites).

Guards the exact regression fixed in broad-scan F1/F2: the naive idiom
``{ch for ch in Color(s).upper() if ch in "WUBRG"}`` reads the literal string
"Colorless" as {'R'} — because the WORD contains an R — so every colorless card
(mana rocks, artifacts, Eldrazi) was mis-routed by suggest / suggest-homes /
fingerprints (excluded from non-red decks, offered to red ones). A sibling variant
``set(Color(s).replace(" ",""))`` kept the "/" so gold cards failed the subset test.

These checks are distribution-independent (they assert behavior, not card names), so
they keep working as the collection changes. check_all.py folds them in as a HARD
gate — a re-introduction of the bug fails the build, the same way check_rankings
guards the Doctor-Doom scoring regression.

Run standalone (`python3 scripts/check_colors.py`) or via check_all.py.
Returns a list of human-readable error strings; empty == healthy.
"""
import ast
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import REPO_ROOT, card_colors, color_matches  # noqa: E402

LIB_CSV = os.path.join(REPO_ROOT, "card-library.csv")
POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Sites that legitimately extract WUBRG letters from a string that is NOT a Color(s)
# identity cell, so card_colors() (which special-cases the literal "Colorless") does
# not apply. Keyed (filename, function). Keep this list SHORT and justified — every
# entry is a place the static scan below would otherwise flag.
_INLINE_PARSE_ALLOW = {
    # parse_pips extracts the colored pips of a single MANA-COST symbol (e.g. "{W}{U}"),
    # not a color-identity cell — there is no "Colorless" string to mishandle.
    ("deck.py", "parse_pips"),
}


def _has_wubrg_membership(node):
    """True iff `node` contains a ``... in "WUBRG"`` membership test."""
    for cmp in ast.walk(node):
        if isinstance(cmp, ast.Compare) and any(isinstance(o, ast.In) for o in cmp.ops):
            if any(isinstance(c, ast.Constant) and c.value == "WUBRG" for c in cmp.comparators):
                return True
    return False


def _iterates_something_other_than_wubrg(iters):
    """True iff any iterable here is NOT the literal ``"WUBRG"``. Iterating the constant
    itself (``for c in "WUBRG"``) is the safe shape — building a per-color tally — and
    must not be flagged."""
    return any(not (isinstance(it, ast.Constant) and it.value == "WUBRG") for it in iters)


def _is_wubrg_identity_comprehension(node):
    """True iff `node` is the naive ``{ch for ch in <some string> if ch in "WUBRG"}``
    identity-extraction idiom, in EITHER of its two shapes — a comprehension, or the
    equivalent ``for`` STATEMENT:

        colors = {ch for ch in col.upper() if ch in "WUBRG"}      # comprehension
        for ch in col.upper():                                    # for-statement
            if ch in "WUBRG": ...

    Both read the literal ``"Colorless"`` as ``{'R'}`` — the word contains an R (audit
    F1/F2). The scan originally tested ONLY the comprehension node types, so the
    for-statement form was invisible to it and the same bug written that way would have
    passed the gate green (broad-scan F-07). One such loop already exists in
    build_dashboard.py; it is correct today because its enclosing function special-cases
    "colorless", which is exactly the exemption below — but the gate could not see it
    either way, which is the point. A gate that cannot fire is not a gate."""
    if isinstance(node, (ast.SetComp, ast.ListComp, ast.GeneratorExp, ast.DictComp)):
        return (_has_wubrg_membership(node)
                and _iterates_something_other_than_wubrg([g.iter for g in node.generators]))
    if isinstance(node, (ast.For, ast.AsyncFor)):
        # Only the loop's own test matters; a nested comprehension is reported separately
        # by its own node, so don't double-count it here.
        body_tests = [n for n in ast.walk(node)
                      if not isinstance(n, (ast.SetComp, ast.ListComp,
                                            ast.GeneratorExp, ast.DictComp))]
        if not any(_has_wubrg_membership(n) for n in body_tests
                   if isinstance(n, (ast.If, ast.Compare, ast.BoolOp))):
            return False
        return _iterates_something_other_than_wubrg([node.iter])
    return False


def _scan_stale_allowlist():
    """Fail if an ``_INLINE_PARSE_ALLOW`` entry names a file or function that no longer
    exists.

    The allowlist is hand-kept, and a stale entry is worse than an absent one: it is an
    exemption for code that is gone, so it reads as a considered decision while covering
    nothing — and if a function of that name is ever reintroduced, it inherits a blanket
    pass nobody granted it. This is the same failure shape ``check_patterns``' coverage
    list had (broad-scan F-04), applied to the other hand-kept registry in this file:
    make the registry falsifiable rather than trusting that someone pruned it."""
    errs = []
    for fn, fname in sorted(_INLINE_PARSE_ALLOW):
        path = os.path.join(SCRIPTS_DIR, fn)
        if not os.path.exists(path):
            errs.append(f"stale _INLINE_PARSE_ALLOW entry ({fn!r}, {fname!r}): "
                        f"{fn} no longer exists. Remove the entry.")
            continue
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (OSError, SyntaxError) as e:
            errs.append(f"could not parse {fn} to verify _INLINE_PARSE_ALLOW ({e})")
            continue
        defined = {n.name for n in ast.walk(tree)
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        if fname not in defined:
            errs.append(f"stale _INLINE_PARSE_ALLOW entry ({fn!r}, {fname!r}): "
                        f"{fn} defines no function {fname!r}. Remove the entry, or fix "
                        f"the name if it was renamed.")
    return errs


def _guards_colorless(node):
    """True iff `node` (a function) actually TESTS for the literal "Colorless", rather
    than merely mentioning the word.

    The exemption used to be ``"colorless" in ast.get_source_segment(...).lower()`` — a
    substring test over the whole enclosing function, which a COMMENT satisfies (broad-scan
    BS5-07). That is the same shape as the bug this file exists to catch: a substring
    standing in for a real comparison. All four exempted sites do compare
    (``col.lower() == "colorless"``), so nothing changes today; what changes is that a
    future function which only talks about the trap can no longer claim to handle it.

    Two accepted shapes: an equality/membership comparison against the literal, and a call
    to the safe primitives — a function that routes through ``card_colors`` /
    ``color_matches`` has delegated the trap rather than guarding it inline."""
    for n in ast.walk(node):
        if isinstance(n, ast.Compare):
            parts = [n.left, *n.comparators]
            if any(isinstance(p, ast.Constant) and isinstance(p.value, str)
                   and p.value.strip().lower() == "colorless" for p in parts):
                return True
        if isinstance(n, ast.Call):
            fn = n.func
            name = getattr(fn, "id", None) or getattr(fn, "attr", None)
            if name in ("card_colors", "color_matches"):
                return True
    return False


def _scan_inline_color_parses():
    """Static call-site guard: fail if any script outside lib.py re-implements color-
    identity extraction with the naive ``if ch in "WUBRG"`` comprehension instead of
    ``lib.card_colors()``. This is the coverage gap that let the F1 bug regress into
    wishlist.py / app.py undetected — the behavioral checks below only exercised
    lib.card_colors and one deck.py call site. A comprehension whose ENCLOSING function
    already special-cases ``"colorless"`` is exempt (it handles the trap explicitly), as
    are the few non-identity sites in _INLINE_PARSE_ALLOW (mana-symbol parsing)."""
    errs = []
    for fn in sorted(f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".py")):
        if fn == "lib.py":
            continue
        path = os.path.join(SCRIPTS_DIR, fn)
        try:
            src = open(path, encoding="utf-8").read()
            tree = ast.parse(src)
        except (OSError, SyntaxError) as e:
            errs.append(f"color call-site scan: could not parse {fn} ({e})")
            continue
        funcs = [n for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for node in ast.walk(tree):
            if not _is_wubrg_identity_comprehension(node):
                continue
            enc = None
            for f in funcs:
                if f.lineno <= node.lineno <= (getattr(f, "end_lineno", None) or node.lineno):
                    if enc is None or f.lineno > enc.lineno:  # innermost wins
                        enc = f
            fname = enc.name if enc else "<module>"
            if (fn, fname) in _INLINE_PARSE_ALLOW:
                continue
            if enc is not None and _guards_colorless(enc):
                continue  # the function TESTS for the trap, not just mentions it
            if enc is None and _guards_colorless(tree):
                continue  # module-level comprehension in a module that guards
            shape = ("for-statement" if isinstance(node, (ast.For, ast.AsyncFor))
                     else "comprehension")
            errs.append(
                f"inline color parse in {fn}:{node.lineno} (function {fname!r}, {shape}) — "
                f"the naive `x in \"WUBRG\"` idiom reads \"Colorless\" as {{'R'}} "
                f"(audit F1). Route it through lib.card_colors(), or (if it parses a mana "
                f"symbol / non-identity string) add ({fn!r}, {fname!r}) to "
                f"_INLINE_PARSE_ALLOW in check_colors.py.")
    return errs


def _scan_color_cell_membership():
    """Static guard for the F1 bug's THIRD shape: a substring/membership test whose
    CONTAINER is a raw ``Color(s)`` cell.

    The comprehension scan above catches ``{ch … if ch in "WUBRG"}``; it cannot see
    ``needle in row.get("Color(s)").lower()`` — yet that is the same trap as a filter:
    ``"r" in "colorless"`` is True, so ``--color R`` matched every Colorless card in
    query.py / pool.py / wishlist.py simultaneously, with this gate green throughout
    (broad-scan BS-10/BS-18). Flag any ``in``/``not in`` whose container's source
    mentions ``Color(s)`` and does not route through ``card_colors`` /
    ``color_matches``. Testing a set already parsed by ``card_colors()`` is the
    correct shape and never flagged; ``"Color(s)" in header`` puts the string on the
    LEFT, not the container, so header checks pass untouched."""
    def _names_color_cell(node):
        # Cheap subtree walk for the literal "Color(s)" — the expensive
        # ast.get_source_segment (O(file) per call) runs ONLY on the rare node
        # that passes this, not on every `in` test in a 10k-line file: doing it
        # unconditionally added ~28s to check_all (batch-4 profiling).
        return any(isinstance(x, ast.Constant) and x.value == "Color(s)"
                   for x in ast.walk(node))

    errs = []
    for fn in sorted(f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".py")):
        if fn == "lib.py":
            continue
        path = os.path.join(SCRIPTS_DIR, fn)
        try:
            src = open(path, encoding="utf-8").read()
            if "Color(s)" not in src:
                continue
            tree = ast.parse(src)
        except (OSError, SyntaxError) as e:
            errs.append(f"color membership scan: could not parse {fn} ({e})")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            if not any(isinstance(o, (ast.In, ast.NotIn)) for o in node.ops):
                continue
            for comp in node.comparators:
                if not _names_color_cell(comp):
                    continue
                seg = ast.get_source_segment(src, comp) or ""
                if "card_colors" not in seg and "color_matches" not in seg:
                    errs.append(
                        f"membership test against a raw Color(s) cell in {fn}:"
                        f"{node.lineno} — a substring `in` re-implements the F1 trap "
                        f"(\"r\" in \"colorless\" is True; broad-scan BS-10). Parse "
                        f"both sides with lib.card_colors(), or use "
                        f"lib.color_matches() for a --color-style filter.")
    return errs


def check():
    """Return a list of error strings (empty == healthy). Never raises."""
    errs = []

    # (1) The primitive itself: the two traps F1/F2 hit.
    if card_colors("Colorless"):
        errs.append("card_colors('Colorless') is non-empty — a colorless card would "
                    "read as colored (the 'COLORLESS' contains 'R' trap, audit F1). "
                    f"Got {sorted(card_colors('Colorless'))}, expected empty.")
    if card_colors("B/G") != {"B", "G"}:
        errs.append("card_colors('B/G') != {'B','G'} — a slash-joined gold card is "
                    f"mis-parsed (audit F2). Got {sorted(card_colors('B/G'))}.")
    if card_colors("W/U/B/R/G") != set("WUBRG"):
        errs.append("card_colors('W/U/B/R/G') should be all five colors; got "
                    f"{sorted(card_colors('W/U/B/R/G'))}.")

    # (2) Property: a colorless identity is castable everywhere (subset of any deck's
    #     colors) — the thing the bug broke.
    if not card_colors("Colorless").issubset(set()):  # empty ⊆ empty
        errs.append("a colorless identity is not the empty set — it must be castable "
                    "in every deck (⊆ any WUBRG set).")

    # (3) Call-site guard: pick a real colorless nonland card and assert deck.py's
    #     fingerprint builder (load_card_meta, the main F1 site) gives it NO colors.
    try:
        import deck
        meta = deck.load_card_meta()
        anchor = None
        for path in (LIB_CSV, POOL_CSV):
            if not os.path.exists(path):
                continue
            with open(path, newline="", encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    if (r.get("Color(s)") or "").strip().lower() == "colorless" \
                            and "Land" not in (r.get("Type") or ""):
                        anchor = (r.get("Card Name") or "").strip().lower()
                        break
            if anchor:
                break
        if anchor and anchor in meta and meta[anchor]["colors"]:
            errs.append(f"deck.load_card_meta parsed colorless card {anchor!r} as "
                        f"{sorted(meta[anchor]['colors'])} — expected no colors (audit F1 "
                        "call site regressed).")
    except Exception as e:  # pragma: no cover - import/deck guard
        errs.append(f"color call-site check skipped ({type(e).__name__}: {e})")

    # (1b) The FILTER primitive: --color must never substring-match (BS-10).
    if color_matches("Colorless", "R"):
        errs.append("color_matches('Colorless', 'R') is True — the --color filter is "
                    "substring-matching again ('r' in 'colorless', broad-scan BS-10).")
    if not color_matches("B/R", "R"):
        errs.append("color_matches('B/R', 'R') is False — a gold card must match a "
                    "filter on any of its identity colors.")
    if not color_matches("Colorless", "colorless"):
        errs.append("color_matches('Colorless', 'colorless') is False — the colorless "
                    "filter must match colorless cards.")
    if color_matches("B", "colorless"):
        errs.append("color_matches('B', 'colorless') is True — the colorless filter "
                    "must match ONLY colorless cards.")

    # (4) STATIC call-site scan: no script may re-implement the naive WUBRG parse
    #     instead of card_colors() (the gap that let F1 regress into wishlist.py/app.py).
    errs += _scan_inline_color_parses()

    # (4b) STATIC membership scan: no `in` test against a raw Color(s) cell (BS-18).
    errs += _scan_color_cell_membership()

    # (5) REGISTRY staleness: every exemption must still name a real call site.
    errs += _scan_stale_allowlist()

    return errs


def main():
    errs = check()
    if errs:
        print("Color parsing sanity: FAIL")
        for e in errs:
            print(f"  ✗ {e}")
        return 1
    print("Color parsing sanity: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
