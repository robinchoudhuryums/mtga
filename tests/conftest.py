"""Pytest bootstrap: put scripts/ on sys.path so the unit tests can import the
tooling modules (lib, deck, wishlist, …) the same way the scripts import each other.

This unit layer is a COMPLEMENT to `scripts/check_all.py` (the deterministic
integrity + model-sanity gate). check_all stays pure-stdlib and is the primary gate;
these tests pin the edge-case behaviour of the pure helper functions so a refactor
can't silently change them. Run with `pytest` (see requirements-dev.txt) — never
imported by check_all, so the core tooling keeps its zero-dependency guarantee.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))


# ── PYTEST_NO_SKIPS: a skip is a failure in CI ───────────────────────────────────────
#
# `tests/test_app_editor.py` importorskips Flask, which lives in requirements-app.txt.
# CI installed only requirements-dev.txt, so its SIX write-safety pins on `app.py` — 1,035
# lines that write card-library.csv and deck files — skipped on every push and every PR,
# and had done since they were written. They pass fine; nothing automated ever ran them.
# That is G-53's "a capability that works and is never reached is invisible to every
# correctness gate", applied to a test rather than a command, and the only visible trace
# was the unremarkable `1 skipped` in the summary line.
#
# Installing Flask in CI fixes today's instance. This turns the CLASS into a failure: with
# PYTEST_NO_SKIPS=1 (set by .github/workflows/tests.yml) any skip fails the run, so the
# next optional dependency cannot quietly take a module out of coverage. Local runs are
# untouched — skipping is legitimate on a dev box without the editor's dependency, which
# is the split `make app` already draws.
def pytest_runtest_makereport(item, call):
    """Convert a skip into a failure when PYTEST_NO_SKIPS is set. Returns None for every
    other case so pytest's own report generation is left alone."""
    if not os.environ.get("PYTEST_NO_SKIPS"):
        return None
    import _pytest.runner
    report = _pytest.runner.TestReport.from_item_and_call(item, call)
    if report.skipped:
        report.outcome = "failed"
        report.longrepr = (
            f"SKIPPED with PYTEST_NO_SKIPS set: {item.nodeid}\n"
            f"  reason: {getattr(report, 'longrepr', '?')}\n"
            "  A skipped test is not coverage. Install the missing dependency in CI, or "
            "delete the test — see the note in tests/conftest.py."
        )
        return report
    return None


@pytest.hookimpl(hookwrapper=True)
def pytest_make_collect_report(collector):
    """The COLLECTION-time twin of the hook above (BS8-07). A module-level
    `pytest.importorskip(...)` — the way an optional dependency is normally guarded, and
    exactly how tests/test_app_editor.py guards Flask — raises during collection and is
    reported through a CollectReport, which `pytest_runtest_makereport` never sees. So the
    one skip shape PYTEST_NO_SKIPS was built for passed straight through it: with Flask
    missing the run printed "1 skipped" and exited 0. A HOOKWRAPPER here rewrites the
    report before the terminal reporter counts it (a plain `pytest_collectreport` runs
    after the count and changes nothing — measured), so the module becomes a collection
    ERROR and the run exits non-zero: "a skipped test is not coverage" at both stages."""
    outcome = yield
    if not os.environ.get("PYTEST_NO_SKIPS"):
        return
    report = outcome.get_result()
    if report.skipped:
        report.outcome = "failed"
        report.longrepr = (
            f"SKIPPED at collection with PYTEST_NO_SKIPS set: {report.nodeid}\n"
            "  A module skipped at collection is not coverage. Install the missing "
            "dependency in CI, or delete the module — see the note in tests/conftest.py."
        )


# ── The suite must not write the repo's own data ─────────────────────────────────────
#
# On 2026-10-01 `test_app_editor.py` was found reverting the REAL card-library.csv on every
# run: one test POSTed `/api/revert` without the fixture that repoints `app.DEFAULT_CSV`,
# so the endpoint restored the newest `.bak` over the inventory — i.e. it UNDID the last
# library write. It discarded a tag merge twice in one day (once through the SessionStart
# hook's suite run) and had gone unnoticed for weeks, because the newest backup usually held
# the same bytes, so the only trace was an extra `.bak` nobody looked at.
#
# The fix there is local; this is the class. Fingerprint every canonical data file and deck
# file — CONTENT, plus the NAMES of the `.bak` files beside them — at session start, and
# fail the run if any moved. The `.bak` half is what makes it deterministic: a revert that
# restores identical bytes changes no content but always writes a new backup.
#
# Do not edit data or deck files while the suite runs (the 2026-09-20 process rule already
# says so for source); a deliberate edit mid-run will trip this, and that is correct.
_GUARDED_DATA = ("card-library.csv", "card-mana.csv", "card-pool.csv", "card-wishlist.csv",
                 "matches.csv", "recommendations.csv", "arena-cards.csv",
                 "collection-stamp.json")


def _repo_data_fingerprint(root):
    import glob
    import hashlib

    def digest(path):
        try:
            with open(path, "rb") as fh:
                return hashlib.sha256(fh.read()).hexdigest()
        except OSError:
            return None

    fp = {}
    for name in _GUARDED_DATA:
        path = os.path.join(root, name)
        fp[name] = digest(path)
        fp[name + " (.bak files)"] = tuple(sorted(
            os.path.basename(b) for b in glob.glob(glob.escape(path) + ".*bak*")))
    for path in sorted(glob.glob(os.path.join(root, "decks", "**", "*"), recursive=True)):
        if os.path.isfile(path):
            rel = os.path.relpath(path, root)
            fp[rel] = "bak" if ".bak" in os.path.basename(path) else digest(path)
    return fp


_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def pytest_sessionstart(session):
    session.config._repo_data_fp = _repo_data_fingerprint(_REPO_ROOT)


def pytest_sessionfinish(session, exitstatus):
    before = getattr(session.config, "_repo_data_fp", None)
    if before is None:
        return
    after = _repo_data_fingerprint(_REPO_ROOT)
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    if not changed:
        return
    tr = session.config.pluginmanager.get_plugin("terminalreporter")
    msg = ("REPO DATA CHANGED DURING THE TEST RUN — a test wrote the repo's own files "
           "instead of a tmp copy:\n" + "\n".join(f"  {k}" for k in changed[:20])
           + ("\n  …" if len(changed) > 20 else "")
           + "\nRestore with `git checkout -- <file>` (and delete any new .bak), then give "
             "the offending test a fixture that repoints the path. See tests/conftest.py.")
    if tr is not None:
        tr.write_line("")
        tr.write_line(msg, red=True, bold=True)
    else:
        print(msg)
    session.exitstatus = pytest.ExitCode.TESTS_FAILED
