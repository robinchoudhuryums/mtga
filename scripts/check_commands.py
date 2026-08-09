#!/usr/bin/env python3
"""Workflow-coverage gate — every command must be reachable from a workflow.

This project's three most expensive bugs this cycle were the same bug: a HAND-KEPT
REGISTRY GROWS HOLES. `check_patterns`' coverage list had fallen 13 patterns behind the
code (including the whole of `structural_distinctiveness`, whose failure `max()` hides);
`_INLINE_PARSE_ALLOW` could name a function that no longer existed; and no gate ever
built an argparse tree, so `deck.py --help` was broken for four days with three green
workflows. Each was fixed by making the registry falsifiable.

The SKILLS in `.claude/commands/` are the last hand-kept registry with no gate on it.
They are the composition layer — `/tune-deck` alone scripts 28 tool invocations — and
nothing forces one to learn about a command a later cycle added. CLAUDE.md already
records this happening: "/tune-deck was still built around the command set it shipped
with and had no step for `consistency`, `engines`, `shape`, `cuts`, `flex` … The
load-bearing omission was the needs-aware `suggest --needs/--interaction/--ramp/--lands`:
plain `suggest` filters candidates to cards sharing a synergy THEME and so structurally
CANNOT surface removal or a land, i.e. the one recommender a tune-for-interaction would
reach for is blind to the fix."

That capability existed, was correct, was gated, was documented — and went unused,
because the workflow never learned it was there. Correctness gates cannot see this: every
one of those commands passed every check while being unreachable in practice.

Two checks, mirroring `check_patterns`:

  1. COVERAGE — every `deck.py` subcommand and every runnable script is invoked by a
     skill, invoked by another script, or listed in `INTERACTIVE_ONLY` with a reason.
  2. STALENESS — every `INTERACTIVE_ONLY` entry still names something that exists. An
     exemption for a command that is gone reads as a considered decision while covering
     nothing, and pre-grants a pass to any future command that reuses the name.

Run standalone (`python3 scripts/check_commands.py`) or via check_all.py.
Returns a list of human-readable error strings; empty == healthy.
"""
import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import REPO_ROOT  # noqa: E402

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(REPO_ROOT, ".claude", "commands")
DECK_PY = os.path.join(SCRIPTS_DIR, "deck.py")

# Commands a workflow deliberately does NOT drive, each with the reason. Keep this SHORT
# and justified — every entry is a capability no skill will ever remind you exists, so it
# had better be one you reach for deliberately. "I couldn't be bothered to wire it up" is
# not a reason; wire it up instead.
INTERACTIVE_ONLY = {
    ("deck.py", "history"):
        "per-deck git forensics — you run it when you want to know why a deck changed, "
        "not on a schedule; nothing downstream consumes it",
    ("deck.py", "diff"):
        "ad-hoc comparison of two decks you already have in mind; a workflow has no way "
        "to guess the pair",
    ("deck.py", "arena"):
        "clipboard helper — emits the Arena import block; the dashboard's copy button and "
        "build_dashboard.py are its real consumers",
    ("deck.py", "list"):
        "orientation command; every skill addresses decks by id directly",
    ("script", "app.py"):
        "the optional Flask editor — an interactive GUI launched by `make app`, not a "
        "step any workflow drives (/ingest routes single-card fixes to it by name, but "
        "the editing itself is a human at a browser)",
    ("script", "query.py"):
        "ad-hoc owned-collection search — every argument comes from the conversation "
        "(/tune-deck names it for themed deep-reads), so no workflow can carry a fixed "
        "invocation; surfaced when BS2-31 stopped counting prose mentions as coverage",
}
# NOTE: sheets_sync.py and import_collection.py were exempt here until /ingest existed.
# Both are ingest routes, so the honest fix was to give them a workflow rather than a
# standing exemption — which is the gate working as intended: an exemption should be a
# statement that no workflow COULD drive a command, not a note that none does yet.

# Scripts that are libraries or gates, not workflow steps: a library has no CLI, and a
# gate runs inside check_all.py rather than being invoked by a skill.
_LIBRARY = {"lib.py", "scryfall.py"}


def deck_subcommands(path=DECK_PY):
    """Subcommand names registered via `sub.add_parser("name", ...)`, read from the
    SOURCE. Static so this stays in-process and fast — check_all must not pay for a
    subprocess per gate, and the CLI surface itself is covered by tests/test_cli.py."""
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (OSError, SyntaxError) as e:
        raise RuntimeError(f"could not parse {os.path.basename(path)}: {e}")
    out = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_parser" and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            out.append(node.args[0].value)
    return sorted(set(out))


def runnable_scripts(directory=SCRIPTS_DIR):
    """Scripts with a `__main__` entry point — i.e. things a person can run."""
    out = []
    for fn in sorted(os.listdir(directory)):
        if not fn.endswith(".py") or fn in _LIBRARY:
            continue
        src = open(os.path.join(directory, fn), encoding="utf-8").read()
        if "__main__" in src:
            out.append(fn)
    return out


def _skill_text(directory=SKILLS_DIR):
    if not os.path.isdir(directory):
        return ""
    return "\n".join(open(os.path.join(directory, f), encoding="utf-8").read()
                     for f in sorted(os.listdir(directory)) if f.endswith(".md"))


def _script_text(directory=SCRIPTS_DIR, exclude=("deck.py",)):
    """Source of every script EXCEPT the given ones. deck.py is excluded when testing
    whether another module drives a subcommand, since deck.py defines them all."""
    return "\n".join(open(os.path.join(directory, f), encoding="utf-8").read()
                     for f in sorted(os.listdir(directory))
                     if f.endswith(".py") and f not in exclude)


# A mention that TELLS YOU NOT TO RUN something is not coverage. Narrow on purpose, and
# clause-scoped, mirroring the rationale audit's suppression design (G-26): a broad cue
# list here would silently DROP real coverage, which is the expensive direction.
_CAUTION_CUES = re.compile(
    r"\b(never|do not|don't|avoid|instead of|rather than|without|deprecated|blindly)\b",
    re.I)
# Sentence-ish bounds. A skill is Markdown, so a newline ends a clause as surely as a stop.
_CLAUSE_EDGE = re.compile(r"[.;:\n]")


def _clause_around(text, pos):
    """The clause containing `pos` — between the nearest sentence-ish breaks."""
    lo = 0
    for m in _CLAUSE_EDGE.finditer(text, 0, pos):
        lo = m.end()
    m = _CLAUSE_EDGE.search(text, pos)
    return text[lo:m.start() if m else len(text)]


def _cited_as_usage(text, pattern):
    """True if `pattern` appears at least once OUTSIDE a caution clause.

    The script half of this gate has required an executable shape since BS2-31, because
    two of `build_pool.py`'s three skill mentions were warnings NOT to run it — so
    deleting its one real invocation would have left the gate green. The SUBCOMMAND half
    kept a plain text match, so the same warning-counts-as-coverage hole was open one
    column over: "never run `deck.py sync --apply` blindly" granted `sync` its coverage
    (BS4-09).

    Requiring `python3 scripts/deck.py <name>` was measured and REJECTED as the fix: the
    skills legitimately write 30 of their command references in the bare `deck.py <name>`
    form and only 3 subcommands appear inside fenced code blocks, so an executable-shape
    rule would have failed 27 live, genuinely-covered commands. Suppressing the caution
    CLAUSE instead costs nothing today (measured: zero subcommands lose coverage) while
    closing the hole — and if every mention of a command is a warning, that command is
    exactly as unreachable as the gate is meant to detect."""
    for m in re.finditer(pattern, text):
        if not _CAUTION_CUES.search(_clause_around(text, m.start())):
            return True
    return False


def _strip_make_comments(text):
    """A Makefile with its comment lines removed.

    Coverage for a script may come from `scripts/<fn>` appearing in the Makefile, since
    `make refresh` IS the invocation. But the match ran against the raw file, so a COMMENT
    counted — Makefile line 3 mentions `scripts/app.py`, and a future "do NOT run
    scripts/foo.py here" comment would grant coverage to a script nothing runs (BS4-25).
    Same warning-counts-as-coverage shape as `_cited_as_usage`, in the other input."""
    return "\n".join(ln for ln in (text or "").splitlines()
                     if not ln.lstrip().startswith("#"))


def check():
    """Return a list of error strings (empty == healthy). Never raises."""
    errs = []
    try:
        subs = deck_subcommands()
        scripts = runnable_scripts()
    except RuntimeError as e:
        return [str(e)]

    skills = _skill_text()
    code = _script_text()
    gate_wiring = ""
    ca = os.path.join(SCRIPTS_DIR, "check_all.py")
    if os.path.exists(ca):
        gate_wiring = open(ca, encoding="utf-8").read()

    # 1. COVERAGE — deck.py subcommands.
    for name in subs:
        if ("deck.py", name) in INTERACTIVE_ONLY:
            continue
        # A skill drives it... `(?![\w-])`, not `\b`: a bare word boundary is satisfied
        # at a hyphen, so `deck.py suggest\b` matched "deck.py suggest-homes" and the
        # `suggest` subcommand inherited coverage from an unrelated command (BS2-31).
        # A mention inside a CAUTION does not count — see `_cited_as_usage`.
        if _cited_as_usage(skills, rf"deck\.py {re.escape(name)}(?![\w-])"):
            continue
        # ...or another module CALLS it programmatically. Deliberately matching the
        # `cmd_*` function rather than the string "deck.py <name>": every docstring in
        # this repo cross-references commands in prose, so a text match would count a
        # comment as coverage and the gate would pass a command nothing actually runs.
        # That is precisely the "a check that cannot fire is not a check" failure.
        fn = "cmd_" + name.replace("-", "_")
        if re.search(rf"\b{re.escape(fn)}\b", code):
            continue
        errs.append(
            f"`deck.py {name}` is invoked by NO skill and no other script — a capability "
            f"nothing will ever remind you exists. Add it to a workflow in "
            f".claude/commands/, or add ('deck.py', {name!r}) to INTERACTIVE_ONLY in "
            f"check_commands.py with the reason it is human-driven.")

    # 2. COVERAGE — runnable scripts.
    for fn in scripts:
        if ("script", fn) in INTERACTIVE_ONLY:
            continue
        if fn == "check_all.py":
            continue                      # the gate runner itself; nothing runs IT but CI
        if fn.startswith("check_"):
            # A gate earns its keep by running inside check_all, not by being in a skill.
            mod = fn[:-3]
            if re.search(rf"from {re.escape(mod)} import|import {re.escape(mod)}\b",
                         gate_wiring):
                continue
            errs.append(
                f"{fn} is a gate but check_all.py never imports it — it runs only if "
                f"someone remembers to. Wire it into check_all.py, or add "
                f"('script', {fn!r}) to INTERACTIVE_ONLY with a reason.")
            continue
        # A REAL invocation, not a prose mention (G-53's own words — the subcommand
        # path above already honours this and says why). A bare-name match counted a
        # WARNING as coverage: two of build_pool.py's three skill mentions were "had
        # build_pool.py in the wrong position" cautions, so deleting the one real
        # `python3 scripts/build_pool.py` call would have left the gate green
        # (BS2-31). Coverage = an executable shape: `python3 scripts/<fn>` in a
        # skill, or `scripts/<fn>` in the Makefile (the one executable definition of
        # the rebuild chain — `make refresh`/`make dashboard` ARE the invocation).
        mk_path = os.path.join(os.path.dirname(SCRIPTS_DIR), "Makefile")
        mk = _strip_make_comments(
            open(mk_path, encoding="utf-8").read() if os.path.exists(mk_path) else "")
        if _cited_as_usage(skills, rf"python3 scripts/{re.escape(fn)}") \
                or re.search(rf"scripts/{re.escape(fn)}", mk):
            continue
        errs.append(
            f"{fn} is INVOKED by no skill and no Makefile target (a prose mention is "
            f"not coverage — G-53). Add a real `python3 scripts/{fn}` call to a "
            f"workflow in .claude/commands/, or add ('script', {fn!r}) to "
            f"INTERACTIVE_ONLY with the reason it is human-driven.")

    # 3. STALENESS — an exemption must still name something real.
    for (kind, name), reason in sorted(INTERACTIVE_ONLY.items()):
        if not str(reason).strip():
            errs.append(f"INTERACTIVE_ONLY entry ({kind}, {name!r}) has no reason — "
                        f"an unexplained exemption is indistinguishable from an oversight.")
        if kind == "deck.py" and name not in subs:
            errs.append(f"stale INTERACTIVE_ONLY entry ('deck.py', {name!r}): no such "
                        f"subcommand any more. Remove it.")
        elif kind == "script" and not os.path.exists(os.path.join(SCRIPTS_DIR, name)):
            errs.append(f"stale INTERACTIVE_ONLY entry ('script', {name!r}): no such "
                        f"script any more. Remove it.")
        elif kind not in ("deck.py", "script"):
            errs.append(f"INTERACTIVE_ONLY key {(kind, name)!r} has an unknown kind "
                        f"{kind!r} — expected 'deck.py' or 'script'.")
    return errs


def main():
    errs = check()
    # `check()` converts an unparseable deck.py into a clean error list; re-deriving the
    # same parse here raised the RuntimeError it had just handled, so the STANDALONE
    # debugging run — the one you reach for when the gate is unhappy — crashed while the
    # in-process path reported properly (BS4-31).
    try:
        subs, scripts = deck_subcommands(), runnable_scripts()
    except RuntimeError as e:
        print(f"Workflow coverage: FAIL — {e}")
        return 1
    if errs:
        print(f"Workflow coverage: FAIL ({len(errs)} issue(s))")
        for e in errs:
            print(f"  ✗ {e}")
        return 1
    print(f"Workflow coverage: OK — {len(subs)} deck.py subcommand(s) and "
          f"{len(scripts)} script(s), all reachable from a workflow "
          f"({len(INTERACTIVE_ONLY)} deliberate exemption(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
