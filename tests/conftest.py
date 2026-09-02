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
