#!/usr/bin/env python3
"""Anchor + static sanity checks for the DFC front/full-name ownership convention.

The library keys a double-faced card under its FRONT name only; the pool and wishlist
key the full ``Front // Back``. Every ownership JOIN across that boundary must go through
``lib.owned_qty`` (which falls back to the front face) — the audit A3/A4/F6 class of bug
is a lookup that BYPASSES it and reads an owned DFC as unowned / a craft target.

Five guards. The first two mirror check_colors; the rest grew as G-63 kept producing
bugs one layer further out than the rule then reached.

  (1) BEHAVIORAL — lib.owned_qty and its delegating wrappers (wishlist._owned_of,
      pool.owned_of) resolve an owned DFC by its front face when the index is keyed by
      the library's front-name convention. This locks the primitive and the wrappers,
      so a regression in owned_qty (or a wrapper that stops delegating) fails the build.

  (2) STATIC — no script may re-implement an ownership lookup with a raw ``.get()`` /
      subscript on the conventional ownership-index variables (``owned`` / ``by_name_qty``)
      instead of owned_qty. That is the exact bypass shape A3 hit in wishlist.py. A short,
      justified allowlist exempts the two canonical sites (the index BUILDER and the
      deck-side owned() helper, whose keys are already front names by contract).

  (3) INDEX-ALIAS registry (BEHAVIORAL) — every registered name-keyed loader over
      pool-shaped data actually resolves a live DFC's front key.

  (4) REGISTRY COMPLETENESS (STATIC) — and every such loader is REGISTERED. (3) can only
      check the loaders someone listed; each real bug so far was a loader nobody listed.
      This scan finds them in the AST instead, so the hand-kept list cannot go stale
      silently. See _pool_index_builders.

  (5) EDITOR PAYLOAD — the serialized ownership map consumed by JS, where no Python scan
      reaches (BS-08).

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
import re
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
#   (module, attr, index_position[, args_factory])
#     index_position=None → the return IS the dict; an int → the dict sits at that
#     tuple position. args_factory is optional: a callable (full, front) -> tuple of
#     positional args, for a loader that does not take zero arguments.
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
    # BS3-01: found by the registry-completeness scan below, which is the point of it —
    # `_legality_of` builds the same shape and nothing verified it. It takes the names
    # it should index, so it needs an args_factory; every other entry is zero-arg.
    ("deck", "_legality_of", None, lambda full, front: ([full],)),
    # LIBRARY-SHAPED ownership indexes (BS6-01). Every one of these was outside the
    # scan's old pool-only scope, which is how a gate built for exactly this bug class
    # missed four instances of it at once. `verify_ingest.library_index` was still
    # BROKEN when the widened scan found it — the other three had been fixed by hand.
    ("deck", "load_mana", None),
    ("deck", "load_collection", 2),
    ("pool", "owned_counts", None),
    ("card", "_owned_index", None, lambda full, front: (_library_rows(),)),
    ("verify_ingest", "library_index", 0),
    ("wishlist", "owned_index", None),
)


def _library_rows():
    """card-library.csv as a list of row dicts — the argument `card._owned_index` takes."""
    import csv as _csv
    from lib import DEFAULT_CSV as _lib_csv
    if not os.path.exists(_lib_csv):
        return []
    with open(_lib_csv, newline="", encoding="utf-8") as fh:
        return [dict(r) for r in _csv.DictReader(fh)]


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
    # A SECOND probe, from the LIBRARY. The pool probe alone made every library-shaped
    # loader pass VACUOUSLY: the check is `full in idx and front not in idx`, and the
    # pool's first DFC ("Life // Death") is not in the collection at all, so `full in
    # idx` was False and the loader was never actually exercised. A gate that cannot
    # fire is not a gate — so probe with a name the index can actually hold, and say so
    # out loud when neither probe reaches a registered loader.
    lib_full = None
    lib_csv = os.path.join(_root, "card-library.csv")
    if os.path.exists(lib_csv):
        with open(lib_csv, newline="", encoding="utf-8") as fh:
            for r in _csv.DictReader(fh):
                n = (r.get("Card Name") or "").strip()
                if " // " in n:
                    lib_full = n.lower()
                    break
    probes = [(f, f.split(" // ")[0].strip()) for f in (full, lib_full) if f]
    if not probes:
        # No two-faced card in either file — say so rather than pass silently.
        print("check_dfc: no DFC in card-pool.csv or card-library.csv — "
              "index-alias registry not exercised.")
        return []
    errs = []
    for entry in _ALIASED_LOADERS:
        mod_name, attr, pos = entry[:3]
        argf = entry[3] if len(entry) > 3 else None
        try:
            mod = importlib.import_module(mod_name)
            fn = getattr(mod, attr)          # AttributeError == stale registry entry
            out = fn(*(argf(full, front) if argf else ()))
            idx = out if pos is None else out[pos]
        except Exception as e:
            errs.append(f"index-alias registry: {mod_name}.{attr} failed to run "
                        f"({type(e).__name__}: {e}) — stale entry, or the loader broke.")
            continue
        exercised = False
        for pfull, pfront in probes:
            if pfull not in idx:
                continue
            exercised = True
            if pfront not in idx:
                errs.append(f"{mod_name}.{attr}: holds the full name {pfull!r} but not "
                            f"its front {pfront!r} — the index lost its front-face alias "
                            f"pass (route it through lib.alias_front; G-63/BS-12).")
        if not exercised:
            # NOT an error — a loader may legitimately hold neither probe — but it must
            # not read as a pass. Silence is what made the library entries vacuous.
            print(f"check_dfc: {mod_name}.{attr} holds neither probe "
                  f"({', '.join(p[0] for p in probes)}) — alias NOT exercised.")
    return errs


# (4) REGISTRY COMPLETENESS. Guard (3) verifies every loader the registry NAMES; it is
# blind to a loader nobody named, and the registry is hand-kept — its own comment claims
# "a new loader added to the list is covered on arrival", which is true and answers the
# wrong question. Every G-63 index bug so far was a loader that existed and was never on
# any list: `load_keywords` (BS-12) and reconcile_crafts' pool map (BS-16) were both
# written, shipped and consumed before anyone thought to register them. That is the
# `check_commands` lesson one subsystem over — a capability nothing reaches is invisible,
# and here it is a loader nothing CHECKS.
#
# So: find the builders statically instead of trusting the list. A "pool-shaped name
# index" is a function that (a) names the pool, (b) reads it with a csv.DictReader, and
# (c) stores into a dict under a key derived from the `Card Name` column. That last clause
# is what keeps the scan honest — `suggest_scored` / `suggest_lands` iterate the same rows
# and build `theme_w` / `deck_curve`, which are not name-keyed and must not be flagged.
# Measured at introduction: 9 builders found, 0 false positives, 1 unregistered
# (`deck._legality_of`, now registered — it had a fourth private copy of the alias loop
# that nothing verified).
_BUILDER_SCAN_SKIP = {"lib.py", "check_dfc.py"}

# WHAT THE SCAN LOOKS AT. It was POOL-ONLY (`DictReader` + a card-pool.csv cue) until
# BS6-01, and that scope is exactly why the gate could not see its own bug class: every
# OWNERSHIP index reads card-library.csv, through `lib.load_rows` rather than a
# DictReader, so all four of them sat outside a scan written to find unaliased name
# indexes. `deck.owned` then answered "NOT IN LIBRARY" for an owned card while this gate
# stayed green. A scan whose scope excludes the file the bug lives in is not a narrow
# gate, it is an absent one.
_READER_CUES = ("DictReader", "load_rows", "Quantity Owned")
_SOURCE_CUES = ("card-pool.csv", "POOL_CSV", "card-library.csv", "DEFAULT_CSV",
                "Quantity Owned")

# Builders that legitimately stay out of the behavioral registry, each WITH A REASON —
# a bare allowlist is the stale-assertion shape _ACCESS_ALLOW was burned by above. All
# three entries are false positives of the WIDENED scan, kept visible rather than tuned
# away, because the tuning that would remove them would also remove real builders.
_BUILDER_ALLOW = {
    ("query", "print_table"):
        "keys a COLUMN-WIDTH map by column name, and one of the columns is literally "
        "'Card Name' — so the taint analysis is right that a Card Name string reaches "
        "the key, and wrong about what the dict is. Nothing here is a card index.",
    ("import_arena", "merge"):
        "a WRITER's printing index keyed by `key(name, set, collector)`. The tuple comes "
        "back from a call rather than a literal, so `_tuple_bound_names` cannot see it. "
        "A printing key is INV-01's business; a front-face alias is meaningless for one.",
    ("reconcile_crafts", "reconcile"):
        "already aliases its pool map inline via `lib.alias_front` (BS-16 put it there). "
        "It is a whole reconcile RUN with side effects, not a loader that can be called "
        "for its index, so the behavioral registry cannot exercise it.",
}


def _seg(lines, node):
    """Source text of `node`, sliced from PRE-SPLIT lines.

    Not a style preference: ``ast.get_source_segment`` re-splits the whole file on every
    call, so asking it for each of deck.py's several hundred functions made this scan
    take 39 seconds — for a gate check_all runs on every invocation. Slicing a list
    split once per file takes it to well under a second."""
    end = getattr(node, "end_lineno", None) or node.lineno
    return "".join(lines[node.lineno - 1:end])


def _pool_index_builders():
    """[(module, function, file, lineno)] — every pool-shaped name-index builder in
    scripts/, found statically. Shared by the gate and its tests."""
    found = []
    for fn in sorted(f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".py")):
        # A gate's own scratch index is not a consumer surface, and forcing one into the
        # production registry would assert something false about it. Stated residual: a
        # check_*.py that builds a REAL consumer index is not covered here.
        if fn in _BUILDER_SCAN_SKIP or fn.startswith("check_"):
            continue
        path = os.path.join(SCRIPTS_DIR, fn)
        try:
            src = open(path, encoding="utf-8").read()
            tree = ast.parse(src)
        except (OSError, SyntaxError) as e:
            found.append(("<unparsed>", str(e), fn, 0))
            continue
        # Whole-file pre-filter: most scripts never touch either card CSV at all.
        if not any(c in src for c in _READER_CUES) or not any(c in src for c in _SOURCE_CUES):
            continue
        lines = src.splitlines(keepends=True)
        for f in ast.walk(tree):
            if not isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            seg = _seg(lines, f)
            if not any(cue in seg for cue in _READER_CUES):
                continue
            if not any(cue in seg for cue in _SOURCE_CUES):
                continue
            keys = _cardname_derived(f, lines)
            if keys and _stores_keyed_by(f, keys):
                found.append((fn[:-3], f.name, fn, f.lineno))
    return found


def _cardname_derived(f, lines):
    """Local names bound (transitively, shallowly) from a `Card Name` column read.
    `lines` is the enclosing file split with keepends (see _seg)."""
    tainted = set()
    assigns = [n for n in ast.walk(f)
               if isinstance(n, (ast.Assign, ast.AnnAssign)) and n.value is not None]
    # Precompute per-assignment facts once; the fixpoint below only re-reads `refs`.
    facts = [(n, "Card Name" in _seg(lines, n.value),
              {x.id for x in ast.walk(n.value) if isinstance(x, ast.Name)},
              n.targets if isinstance(n, ast.Assign) else [n.target])
             for n in assigns]
    for _ in range(4):                      # fixpoint; 4 hops is far more than any site
        grew = False
        for _n, from_col, refs, targets in facts:
            if not from_col and not (refs & tainted):
                continue
            for t in targets:
                for x in ast.walk(t):
                    if isinstance(x, ast.Name) and x.id not in tainted:
                        tainted.add(x.id)
                        grew = True
        if not grew:
            break
    return tainted


def _tuple_bound_names(f):
    """Local names bound from a TUPLE literal — a `(name, set, collector)` PRINTING key.

    A front-face alias is meaningless for a printing key: it identifies one physical
    printing, which is INV-01's business, not G-63's. Without this the widened scan
    below reported `app.save`, `validate.validate` and `import_arena.merge` as
    unregistered name indexes — three false positives out of eight, which is the rate at
    which a scan stops being read."""
    out = set()
    for n in ast.walk(f):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Tuple):
            for t in n.targets:
                for x in ast.walk(t):
                    if isinstance(x, ast.Name):
                        out.add(x.id)
    return out


def _stores_keyed_by(f, keys):
    """True iff the function stores into a dict under one of `keys` — either
    ``d[name] = …`` or ``d.setdefault(name, …)`` — where the key is a BARE NAME.

    A tuple key (literal or via a tuple-bound local) is excluded; see
    `_tuple_bound_names`."""
    keys = keys - _tuple_bound_names(f)
    for n in ast.walk(f):
        subs = []
        if isinstance(n, ast.Assign):
            subs = [t for t in n.targets if isinstance(t, ast.Subscript)]
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Subscript):
            subs = [n.target]
        for t in subs:
            if not isinstance(t.value, ast.Name) or isinstance(t.slice, ast.Tuple):
                continue
            if {x.id for x in ast.walk(t.slice) if isinstance(x, ast.Name)} & keys:
                return True
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "setdefault" and n.args
                and isinstance(n.func.value, ast.Name)
                and not isinstance(n.args[0], ast.Tuple)):
            if {x.id for x in ast.walk(n.args[0]) if isinstance(x, ast.Name)} & keys:
                return True
    return False


def _registry_completeness_flags():
    """Static: every pool-shaped name-index builder must be behaviorally verified."""
    registered = {(e[0], e[1]) for e in _ALIASED_LOADERS}
    errs = []
    for mod, func, fn, lineno in _pool_index_builders():
        if mod == "<unparsed>":
            errs.append(f"pool-index builder scan: could not parse {fn} ({func})")
            continue
        if (mod, func) in registered or (mod, func) in _BUILDER_ALLOW:
            continue
        errs.append(
            f"unregistered pool-shaped name index in {fn}:{lineno} (function {func!r}) — "
            f"it keys a dict on the pool's `Card Name`, so a consumer holding a FRONT-face "
            f"name misses every `Front // Back` row (G-63; that is exactly how BS-12 and "
            f"BS-16 shipped). Alias it via lib.alias_front and add "
            f"({mod!r}, {func!r}, None) to _ALIASED_LOADERS so the behavioral anchor "
            f"covers it — or add it to _BUILDER_ALLOW WITH A REASON.")
    return errs


def _payload_flags():
    """The SERIALIZED index: templates/deck.html consumes the ownership map in JS,
    where no Python scan can reach — which is exactly how BS-08 shipped (a raw
    `name in OWNED` with no front fallback; one app, two buildability verdicts).
    Pin the fix's two load-bearing markers: the `ownedOf` helper exists and it
    front-splits — plus, since BS4-14, every USE of the index.

    That third check closed the residual this docstring used to state and then
    demonstrate: "a NEW raw lookup added elsewhere in the template would not fire this"
    was true, and `renderFlex` was already doing exactly that, so a flex line naming a
    DFC by its full name read "not owned" while the rows above read it correctly. The
    pin guarded the helper, not its callers — the same "a pure-function anchor cannot
    see whether a caller asks" shape G-40 records."""
    tpl = os.path.join(os.path.dirname(SCRIPTS_DIR), "templates", "deck.html")
    if not os.path.exists(tpl):
        # LOUD, like _index_alias_flags' own missing-input case — a template rename
        # or move made the pin return clean, i.e. the guard for "the G-63 class
        # beyond Python's reach" vanished with its file (Batch C small leaks).
        return [f"editor-payload pin: {tpl} not found — the template moved or was "
                "renamed, and the BS-08 ownedOf pin is not being checked at all. "
                "Update the path here."]
    src = open(tpl, encoding="utf-8").read()
    errs = []
    if "function ownedOf" not in src:
        errs.append("templates/deck.html: the `ownedOf` front-face ownership helper is "
                    "gone — the JS payload consumer is back to raw `name in OWNED` "
                    "lookups (BS-08; the G-63 class beyond Python's reach).")
    elif ".split(' // ')[0]" not in src:
        errs.append("templates/deck.html: `ownedOf` no longer falls back to the front "
                    "face — a front-named DFC line reads 'not owned' again (BS-08).")
    # Every USE of the serialized index must go through the helper. The two lookups
    # INSIDE `ownedOf` are the definition itself, so they are the only legitimate ones;
    # anything else is a consumer that skipped the front-face fallback.
    # Comment lines are excluded: the fix's own explanation quotes the banned shape, and
    # a scan that flags the comment describing it is a scan nobody can satisfy.
    uses = [ln.strip() for ln in src.splitlines()
            if re.search(r"\bin OWNED\b|\bOWNED\[", ln) and "OWNED = " not in ln
            and not ln.strip().startswith(("//", "*", "/*"))]
    stray = [ln for ln in uses
             if not (ln.startswith("if (name in OWNED)") or ln.startswith("return front"))]
    for ln in stray:
        errs.append(
            f"templates/deck.html: raw ownership lookup outside `ownedOf` — {ln[:72]!r}. "
            "Every consumer of the serialized OWNED index must call `ownedOf(name)`, "
            "which falls back to the DFC front face; a raw lookup reads an owned "
            "double-faced card as 'not owned' (BS-08 on the card rows, BS4-14 on the "
            "flex panel — one fix, two consumers, and the second sat unnoticed).")
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
        errs += _registry_completeness_flags()
    except Exception as e:  # pragma: no cover - defensive
        errs.append(f"DFC registry-completeness scan errored ({type(e).__name__}: {e})")
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
