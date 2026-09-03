"""BS8-07: `PYTEST_NO_SKIPS` must fail a run for a MODULE-LEVEL `importorskip` — the
shape the flag was built for (tests/test_app_editor.py guards Flask exactly this way)
and the one the per-test hook could not see: it raises at collection and is reported
through a CollectReport. Pinned with a real pytest subprocess on a synthetic module,
because the hook's effect is only observable from outside the session."""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _run(tmp_path, env_flag):
    shutil.copy(os.path.join(HERE, "conftest.py"), tmp_path / "conftest.py")
    (tmp_path / "test_modskip.py").write_text(
        'import pytest\npytest.importorskip("no_such_module_xyz_bs8")\n\n'
        'def test_x():\n    assert True\n', encoding="utf-8")
    (tmp_path / "test_ok.py").write_text("def test_ok():\n    assert True\n",
                                         encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "PYTEST_NO_SKIPS"}
    if env_flag:
        env["PYTEST_NO_SKIPS"] = "1"
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                          cwd=str(tmp_path), env=env, capture_output=True, text=True)


def test_a_module_level_importorskip_fails_the_run_under_the_flag(tmp_path):
    r = _run(tmp_path, True)
    assert r.returncode != 0, r.stdout + r.stderr
    assert "error" in r.stdout.lower() and "SKIPPED at collection" in (r.stdout + r.stderr)


def test_without_the_flag_it_is_still_a_plain_skip(tmp_path):
    r = _run(tmp_path, False)
    assert r.returncode == 0 and "1 skipped" in r.stdout
