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
from lib import REPO_ROOT, card_colors  # noqa: E402

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


def _is_wubrg_identity_comprehension(node):
    """True iff `node` is a set/list/gen/dict comprehension that filters ``x in "WUBRG"``
    over an iterable that is NOT the literal ``"WUBRG"`` — i.e. the naive
    ``{ch for ch in <some string> if ch in "WUBRG"}`` identity-extraction idiom that
    reads the literal ``"Colorless"`` as ``{'R'}`` (audit F1/F2). Iterating the constant
    ``"WUBRG"`` itself (``for c in "WUBRG"``) is a different, safe shape and is excluded."""
    if not isinstance(node, (ast.SetComp, ast.ListComp, ast.GeneratorExp, ast.DictComp)):
        return False
    has_membership = False
    for cmp in ast.walk(node):
        if isinstance(cmp, ast.Compare) and any(isinstance(o, ast.In) for o in cmp.ops):
            if any(isinstance(c, ast.Constant) and c.value == "WUBRG" for c in cmp.comparators):
                has_membership = True
                break
    if not has_membership:
        return False
    # At least one generator must iterate something OTHER than the "WUBRG" literal.
    return any(not (isinstance(g.iter, ast.Constant) and g.iter.value == "WUBRG")
               for g in node.generators)


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
            enc_src = (ast.get_source_segment(src, enc) or "") if enc else src
            if "colorless" in enc_src.lower():
                continue  # the function guards the "Colorless" trap explicitly
            errs.append(
                f"inline color parse in {fn}:{node.lineno} (function {fname!r}) — the naive "
                f"`{{x for x in … if x in \"WUBRG\"}}` idiom reads \"Colorless\" as {{'R'}} "
                f"(audit F1). Route it through lib.card_colors(), or (if it parses a mana "
                f"symbol / non-identity string) add ({fn!r}, {fname!r}) to "
                f"_INLINE_PARSE_ALLOW in check_colors.py.")
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

    # (4) STATIC call-site scan: no script may re-implement the naive WUBRG parse
    #     instead of card_colors() (the gap that let F1 regress into wishlist.py/app.py).
    errs += _scan_inline_color_parses()

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
