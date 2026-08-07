#!/usr/bin/env python3
"""Anchor + static sanity checks for the DFC front/full-name ownership convention.

The library keys a double-faced card under its FRONT name only; the pool and wishlist
key the full ``Front // Back``. Every ownership JOIN across that boundary must go through
``lib.owned_qty`` (which falls back to the front face) — the audit A3/A4/F6 class of bug
is a lookup that BYPASSES it and reads an owned DFC as unowned / a craft target.

Two guards, mirroring check_colors:

  (1) BEHAVIORAL — lib.owned_qty and its delegating wrappers (wishlist._owned_of,
      pool.owned_of) resolve an owned DFC by its front face when the index is keyed by
      the library's front-name convention. This locks the primitive and the wrappers,
      so a regression in owned_qty (or a wrapper that stops delegating) fails the build.

  (2) STATIC — no script may re-implement an ownership lookup with a raw ``.get()`` /
      subscript on the conventional ownership-index variables (``owned`` / ``by_name_qty``)
      instead of owned_qty. That is the exact bypass shape A3 hit in wishlist.py. A short,
      justified allowlist exempts the two canonical sites (the index BUILDER and the
      deck-side owned() helper, whose keys are already front names by contract).

Coverage note: a function-misuse bug — passing a FULL pool name to a non-fallback lookup
like deck.owned() — is a semantically-wrong argument to a normal call, NOT a distinct
syntactic shape, so it is not statically detectable (this is how A4 slipped in). The
behavioral anchor locks the primitive; the static scan catches the raw-access bypass; the
residual (function misuse) is covered only by the printed guidance to prefer owned_qty.

Distribution-independent. check_all.py folds this in as a HARD gate. Run standalone
(``python3 scripts/check_dfc.py``) or via check_all.py. Returns a list of error strings;
empty == healthy.
"""
import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import owned_qty  # noqa: E402

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# The conventional names an ownership index is bound to across this toolkit. A raw
# .get()/subscript on one of these is an ownership lookup that should route through
# owned_qty (front-face aware) instead.
_OWNERSHIP_VARS = {"owned", "by_name_qty"}

# Sites that legitimately touch an ownership index directly, keyed (filename, function):
#   * load_collection BUILDS the index (accumulating counts by library front-name).
#   * owned() IS the deck-side lookup helper. It used to be allow-listed on the claim that
#     deck-file names are "already front-face by convention, so it needs no fallback" —
#     WHICH WAS FALSE, and this file asserting it is what kept the bug alive. `deck.py
#     resolve` emits the FULL `A // B` name for a DFC (that is how the pool keys one, and
#     how Arena exports one), so any deck built by resolve reported its own owned DFC as
#     "NOT IN LIBRARY". owned() now delegates its miss path to owned_qty; it stays on the
#     allow-list because it still does a raw fast-path hit first. The lesson: an allow-list
#     entry is an ASSERTION about the code, and this one was never tested.
_ACCESS_ALLOW = {
    ("deck.py", "load_collection"),
    ("deck.py", "owned"),
}

# A synthetic DFC: the library stores it under the FRONT name, the pool/wishlist under
# the full name. The join must bridge that.
_DFC_FULL = "Fable of the Mirror-Breaker // Reflection of Kiki-Rikki"
_DFC_FRONT = "fable of the mirror-breaker"


def _behavioral_flags():
    """The primitive and its wrappers resolve an owned DFC by its front face."""
    errs = []
    idx = {_DFC_FRONT: 2, "llanowar elves": 4}

    if owned_qty(idx, _DFC_FULL) != 2:
        errs.append(f"lib.owned_qty did not resolve an owned DFC by its front face "
                    f"(index keyed {_DFC_FRONT!r}, queried full name); got "
                    f"{owned_qty(idx, _DFC_FULL)}, expected 2 (audit F6).")
    if owned_qty(idx, "Llanowar Elves") != 4:
        errs.append("lib.owned_qty broke a plain (non-DFC) front-name lookup.")
    if owned_qty(idx, "Nonexistent Card") != 0:
        errs.append("lib.owned_qty should return 0 for an unowned card, not raise/return None.")

    # Wrappers must delegate (not re-implement) so they inherit the front-face fallback.
    for modname, fnname in (("wishlist", "_owned_of"), ("pool", "owned_of")):
        try:
            mod = __import__(modname)
            fn = getattr(mod, fnname)
            if fn(idx, _DFC_FULL) != 2:
                errs.append(f"{modname}.{fnname} did not resolve an owned DFC by its front "
                            f"face — it must delegate to lib.owned_qty (audit A3/F6).")
        except Exception as e:  # pragma: no cover - import guard
            errs.append(f"DFC wrapper check skipped for {modname}.{fnname} "
                        f"({type(e).__name__}: {e})")
    return errs


def _is_ownership_access(node):
    """True iff `node` is a raw ``VAR.get(...)`` call or ``VAR[...]`` subscript where VAR
    is a Name in _OWNERSHIP_VARS — an ownership lookup that bypasses owned_qty."""
    # VAR.get(...)
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get" and isinstance(node.func.value, ast.Name)
            and node.func.value.id in _OWNERSHIP_VARS):
        return True
    # VAR[...]  (a Load — reading the index; index-building assignments are Store and
    # live only in the allowlisted builder anyway)
    if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
            and node.value.id in _OWNERSHIP_VARS):
        return True
    return False


def _static_flags():
    """Flag raw ownership-index accesses that bypass owned_qty (the A3 bypass shape)."""
    errs = []
    for fn in sorted(f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".py")):
        if fn in ("lib.py", "check_dfc.py"):
            continue
        path = os.path.join(SCRIPTS_DIR, fn)
        try:
            src = open(path, encoding="utf-8").read()
            tree = ast.parse(src)
        except (OSError, SyntaxError) as e:
            errs.append(f"DFC call-site scan: could not parse {fn} ({e})")
            continue
        funcs = [n for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for node in ast.walk(tree):
            if not _is_ownership_access(node):
                continue
            enc = None
            for f in funcs:
                if f.lineno <= node.lineno <= (getattr(f, "end_lineno", None) or node.lineno):
                    if enc is None or f.lineno > enc.lineno:  # innermost wins
                        enc = f
            fname = enc.name if enc else "<module>"
            if (fn, fname) in _ACCESS_ALLOW:
                continue
            errs.append(
                f"raw ownership lookup in {fn}:{node.lineno} (function {fname!r}) — a "
                f"`.get()`/subscript on {' / '.join(sorted(_OWNERSHIP_VARS))} bypasses the "
                f"DFC front-face fallback and reads an owned double-faced card as unowned "
                f"(audit A3/F6). Use lib.owned_qty(index, name) (or _owned_of), or (if the "
                f"key is genuinely front-name-only) add ({fn!r}, {fname!r}) to _ACCESS_ALLOW.")
    return errs


# (3) INDEX-ALIAS registry: every name-keyed loader over pool-shaped data that
# consumers hit with FRONT-face keys. G-63's recurring lesson is that the accessor
# rule does not reach an index — six loaders each carried (or lacked) their own
# aliasing copy, and no gate saw the difference until a deck tripped over one
# (`load_keywords` was the sixth, BS-12). Aliasing now has ONE home
# (`lib.alias_front`); this registry asserts each loader's OUTPUT actually resolves
# a real DFC's front, so a new loader added to the list is covered on arrival and a
# loader that drops its alias pass fails the build. Entries resolve by getattr at
# run time — a renamed loader is a hard error, not a silently skipped row (the
# stale-registry rule every hand-kept list here follows).
#   (module, attr, index_position)  index_position=None → the return IS the dict;
#   an int → the dict sits at that tuple position.
_ALIASED_LOADERS = (
    ("deck", "load_keywords", None),
    ("deck", "load_legalities", None),
    ("deck", "load_rarities", None),
    ("deck", "load_card_data", None),
    ("deck", "_pool_rotation_index", 0),
    ("deck", "_printing_index", None),
    ("deck", "known_printings", 0),
    # BS2-40: the last two in-pass aliasing survivors, converted to the second-pass
    # `lib.alias_front` and registered so the behavioral anchor covers them.
    ("deck", "load_card_meta", None),
    ("wishlist", "load_pool_index", None),
)


def _index_alias_flags():
    """Behavioral: each registered loader must resolve a live DFC's FRONT key."""
    import importlib
    import csv as _csv
    from lib import REPO_ROOT as _root
    pool = os.path.join(_root, "card-pool.csv")
    front = full = None
    if os.path.exists(pool):
        with open(pool, newline="", encoding="utf-8") as fh:
            for r in _csv.DictReader(fh):
                n = (r.get("Card Name") or "").strip()
                if " // " in n:
                    full, front = n.lower(), n.lower().split(" // ")[0].strip()
                    break
    if not front:
        # No two-faced card in the pool at all — say so rather than pass silently.
        print("check_dfc: no DFC in card-pool.csv — index-alias registry not exercised.")
        return []
    errs = []
    for mod_name, attr, pos in _ALIASED_LOADERS:
        try:
            mod = importlib.import_module(mod_name)
            fn = getattr(mod, attr)          # AttributeError == stale registry entry
            out = fn()
            idx = out if pos is None else out[pos]
        except Exception as e:
            errs.append(f"index-alias registry: {mod_name}.{attr} failed to run "
                        f"({type(e).__name__}: {e}) — stale entry, or the loader broke.")
            continue
        if full in idx and front not in idx:
            errs.append(f"{mod_name}.{attr}: holds the full name {full!r} but not its "
                        f"front {front!r} — the index lost its front-face alias pass "
                        f"(route it through lib.alias_front; G-63/BS-12).")
    return errs


def _payload_flags():
    """The SERIALIZED index: templates/deck.html consumes the ownership map in JS,
    where no Python scan can reach — which is exactly how BS-08 shipped (a raw
    `name in OWNED` with no front fallback; one app, two buildability verdicts).
    Pin the fix's two load-bearing markers: the `ownedOf` helper exists and it
    front-splits. Residual, stated honestly: a NEW raw lookup added elsewhere in
    the template would not fire this — the pin guards the helper, not every use."""
    tpl = os.path.join(os.path.dirname(SCRIPTS_DIR), "templates", "deck.html")
    if not os.path.exists(tpl):
        return []
    src = open(tpl, encoding="utf-8").read()
    errs = []
    if "function ownedOf" not in src:
        errs.append("templates/deck.html: the `ownedOf` front-face ownership helper is "
                    "gone — the JS payload consumer is back to raw `name in OWNED` "
                    "lookups (BS-08; the G-63 class beyond Python's reach).")
    elif ".split(' // ')[0]" not in src:
        errs.append("templates/deck.html: `ownedOf` no longer falls back to the front "
                    "face — a front-named DFC line reads 'not owned' again (BS-08).")
    return errs


def check():
    """Return a list of error strings (empty == healthy). Never raises."""
    errs = []
    try:
        errs += _behavioral_flags()
    except Exception as e:  # pragma: no cover - defensive
        errs.append(f"DFC behavioral check errored ({type(e).__name__}: {e})")
    try:
        errs += _static_flags()
    except Exception as e:  # pragma: no cover - defensive
        errs.append(f"DFC static scan errored ({type(e).__name__}: {e})")
    try:
        errs += _index_alias_flags()
    except Exception as e:  # pragma: no cover - defensive
        errs.append(f"DFC index-alias check errored ({type(e).__name__}: {e})")
    try:
        errs += _payload_flags()
    except Exception as e:  # pragma: no cover - defensive
        errs.append(f"DFC payload check errored ({type(e).__name__}: {e})")
    return errs


def main():
    errs = check()
    if errs:
        print("DFC ownership-join sanity: FAIL")
        for e in errs:
            print(f"  ✗ {e}")
        return 1
    print("DFC ownership-join sanity: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
