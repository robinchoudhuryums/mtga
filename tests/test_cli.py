"""Smoke tests for the command-line surface — the one thing no other gate touches.

`check_all.py` imports `deck` as a MODULE and calls `cmd_*` directly; nothing in it,
and nothing else under tests/, ever constructs an `ArgumentParser`. So the parsers
were unreachable from every gate in the project, and `deck.py --help` shipped broken
for four days with three green workflows (broad-scan F-01/F-12):

    help="... (keepable %, land drops, ...)"

argparse renders a help string through `help % params`, so a bare `%` raises
`ValueError: unsupported format character` — and because the top-level help expands
every subaction, ONE bad subcommand string killed the whole `--help` output. Every
model-sanity gate, invariant and unit test passed throughout.

These tests are deliberately shallow: they prove each entry point STARTS and renders
its help, not that it computes anything. Depth lives in the other test modules and in
check_all.py. They run as subprocesses because that is the only way to exercise
`main()` and the argparse tree the way a user does — and in a thread pool, because 28
interpreter startups in series is the difference between ~2s and ~20s.
"""
import concurrent.futures
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
TRACEBACK = "Traceback (most recent call last)"


def _scripts():
    return sorted(f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".py"))


def _uses_argparse(filename):
    with open(os.path.join(SCRIPTS_DIR, filename), encoding="utf-8") as fh:
        return "ArgumentParser" in fh.read()


def _run(args, timeout=120):
    """(returncode, stdout+stderr) for `python3 <args>` from the repo root."""
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True,
                       cwd=REPO_ROOT, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _run_all(arg_lists):
    """Run many commands concurrently -> {key: (rc, output)}. Subprocesses are
    IO-bound from the parent's view, so a thread pool is enough."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {key: pool.submit(_run, args) for key, args in arg_lists}
        return {key: f.result() for key, f in futures.items()}


@pytest.fixture(scope="module")
def script_help():
    """`<script> --help` for every script, run once and shared across the tests."""
    return _run_all([(f, [os.path.join("scripts", f), "--help"]) for f in _scripts()])


@pytest.fixture(scope="module")
def subcommands():
    """deck.py's subcommand list, read from its own `--help` output."""
    rc, out = _run([os.path.join("scripts", "deck.py"), "--help"])
    assert rc == 0, out
    start, end = out.find("{"), out.find("}")
    assert 0 <= start < end, f"could not read the subcommand list from:\n{out[:400]}"
    return sorted(out[start + 1:end].split(","))


class TestScriptEntryPoints:
    """Every script must START. This is the contract F-01 broke."""

    def test_no_script_crashes_on_help(self, script_help):
        crashed = {f: out for f, (_rc, out) in script_help.items() if TRACEBACK in out}
        assert not crashed, (
            "these scripts raise on `--help`:\n"
            + "\n".join(f"  {f}: {out.strip().splitlines()[-1]}"
                        for f, out in crashed.items()))

    def test_argparse_scripts_render_usage(self, script_help):
        """A script with an ArgumentParser must exit 0 on --help and print usage.

        Scripts without one are excluded by inspection, not by name: `validate.py`
        and `card.py` take a bare positional via sys.argv, and the check_*.py gates
        just run. Excluding them by a hardcoded list would go stale the moment one
        gains a parser; deriving it from the source cannot."""
        problems = []
        for f, (rc, out) in script_help.items():
            if not _uses_argparse(f):
                continue
            if f == "app.py" and "needs Flask" in out:
                continue  # optional dependency absent — its own friendly message
            if rc != 0 or "usage:" not in out:
                problems.append(f"{f}: rc={rc}, first line {out.strip()[:80]!r}")
        assert not problems, "\n".join(problems)

    def test_the_f01_regression_specifically(self):
        """A bare `%` in any argparse help string takes the WHOLE top-level help
        down, because rendering expands every subaction. deck.py has 31 of them,
        so it is both the likeliest place for this and the costliest."""
        rc, out = _run([os.path.join("scripts", "deck.py"), "--help"])
        assert rc == 0, out
        assert "unsupported format character" not in out
        assert "usage: deck.py" in out


class TestDeckSubcommands:
    """deck.py is the project's main interface — 31 subparsers, each with its own
    help strings, and the roster of commands a skill is supposed to be re-read
    against. Each subparser's own `--help` must render too."""

    def test_the_subcommand_list_is_discoverable(self, subcommands):
        assert len(subcommands) > 25
        for expected in ("stats", "mana", "consistency", "cuts", "tier", "audit"):
            assert expected in subcommands

    def test_every_subcommand_help_renders(self, subcommands):
        results = _run_all([(c, [os.path.join("scripts", "deck.py"), c, "--help"])
                            for c in subcommands])
        problems = [f"{c}: rc={rc} :: {out.strip().splitlines()[-1] if out.strip() else ''}"
                    for c, (rc, out) in sorted(results.items())
                    if rc != 0 or TRACEBACK in out]
        assert not problems, "\n".join(problems)
