"""Same input, same answer — the property no other gate in this project checks.

Fourteen gates verify that each model is CORRECT and one verifies that two models
AGREE. None of them can see a command that is correct on any single run and gives a
DIFFERENT answer the next time, because every one of them evaluates the code once,
inside one interpreter, where set iteration order is fixed.

That blind spot shipped. `deck.py similar` returned a different output for every value
of PYTHONHASHSEED (broad-scan BS5-01): `_deck_central_weights` built its weight vector
by iterating `_central_themes()`, a SET, and `cmd_similar` then sorted that set on a key
that ties constantly. Because the display truncates to `shared[:5]`, WHICH themes the
reader saw changed run to run — deck 40 read `✦Druid` against 40a on one run and
`removal` on the next, on the exact ✦ SPECIFIC overlaps G-47 instructs you to grade
identity overlap from. CLAUDE.md's G-54 states this shape precisely ("a SET plus a sort
key that can TIE is a nondeterministic output") and nothing enforced it, so the rule was
written and then broken in a command a skill runs.

WHY THIS LIVES IN pytest AND NOT IN check_all. The check needs SEPARATE INTERPRETERS
with a controlled `PYTHONHASHSEED`, which is the one thing an in-process gate cannot
arrange — `check_all.py` imports `deck` as a module and calls `cmd_*` directly, and its
whole design (memoized loaders, no subprocesses, no network) is what keeps it at ~4s. So
this follows the precedent G-55 established for the argparse tree: a surface check_all is
structurally unable to reach belongs in the pytest layer plus CI, not bolted onto the
integrity gate. Measured cost here: ~2s wall clock for the whole module, because the
commands are 1–3s each and run in a thread pool.

WHAT TO DO WHEN ONE FAILS. The failure names the command and the first differing line.
Look for a SET being ordered: a `sorted(some_set, key=...)` whose key can tie, a dict
built by iterating a set, or a float `sum()` over a set (addition is not associative, so
the last bits move and that is enough to flip a sort). The fix is a TOTAL order — add
the element itself as the final tie-break — not a changed return type; `_central_themes`
stays a set because two callers intersect it with `&`.
"""
import concurrent.futures
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Two seeds is enough to catch it: string hashing is randomized per process, so any
# set-order dependence shows up as soon as the seeds differ. A third adds cost, not
# power. Seed 0 DISABLES randomization, which makes the pair "randomized vs not".
SEEDS = ("0", "1")

# Read-only commands that must be byte-identical run to run. Chosen for coverage of the
# ordering-sensitive surfaces rather than for breadth: the theme/cosine ranking that
# actually broke, the role and tier models, the two recommenders, the roster-wide sweep,
# and one command from a different module so the property is not pinned to deck.py alone.
COMMANDS = [
    ("similar", ["scripts/deck.py", "similar", "1"]),
    ("stats", ["scripts/deck.py", "stats", "1"]),
    ("cuts", ["scripts/deck.py", "cuts", "1"]),
    ("tier", ["scripts/deck.py", "tier", "1"]),
    ("suggest", ["scripts/deck.py", "suggest", "1", "--limit", "10"]),
    ("audit", ["scripts/deck.py", "audit"]),
    ("wishlist-rank", ["scripts/wishlist.py", "--rank"]),
]


def _run(args, seed):
    env = dict(os.environ, PYTHONHASHSEED=seed)
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True,
                       cwd=REPO_ROOT, env=env, timeout=300)
    return r.stdout or ""


@pytest.fixture(scope="module")
def outputs():
    """{(name, seed): stdout} for every command under every seed, run concurrently."""
    jobs = {(name, seed): (args, seed)
            for name, args in COMMANDS for seed in SEEDS}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {k: pool.submit(_run, a, s) for k, (a, s) in jobs.items()}
        return {k: f.result() for k, f in futures.items()}


def _first_difference(a, b):
    """A readable pointer at where two outputs diverge."""
    la, lb = a.split("\n"), b.split("\n")
    for i, (x, y) in enumerate(zip(la, lb), start=1):
        if x != y:
            return f"line {i}\n    seed {SEEDS[0]}: {x[:120]}\n    seed {SEEDS[1]}: {y[:120]}"
    if len(la) != len(lb):
        return f"line count differs: {len(la)} vs {len(lb)}"
    return "outputs differ but no line does (trailing whitespace?)"


@pytest.mark.parametrize("name", [n for n, _ in COMMANDS])
def test_output_does_not_depend_on_hash_seed(outputs, name):
    a, b = outputs[(name, SEEDS[0])], outputs[(name, SEEDS[1])]
    assert a, f"{name} produced no stdout — the command failed; fix that first"
    assert a == b, (
        f"`{' '.join(dict(COMMANDS)[name])}` gives a DIFFERENT answer under a different "
        f"PYTHONHASHSEED, so the same question has two answers (G-54 / BS5-01).\n  "
        + _first_difference(a, b)
        + "\n  Look for a SET being ordered: a sorted() whose key can tie, a dict built "
          "by iterating a set, or a float sum() over one. Make the key a TOTAL order."
    )


def test_the_check_can_actually_fail():
    """A determinism check that cannot fail is worse than none — it reads as coverage.
    This proves the comparison is real by running a command whose output is DESIGNED to
    vary, so a future refactor that stubs out the seed plumbing is caught here."""
    prog = "import random, os; random.seed(); print(os.environ.get('PYTHONHASHSEED'))"
    a = _run(["-c", prog], SEEDS[0])
    b = _run(["-c", prog], SEEDS[1])
    assert a != b, ("the seed is not reaching the subprocess, so every assertion in this "
                    "module is vacuous — check the env plumbing in _run()")
