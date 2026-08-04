"""Behavioral coverage for scripts/sheets_sync.py `pull` — the one authoritative
overwrite of the whole inventory, and (until broad-scan BS-03) the one outside the
guard family. It has never been run in production, and "a complete script nobody
has ever run is indistinguishable from a broken one" (ROADMAP) — these tests are
the difference. The Google side is faked at `_worksheet`; everything below it
(validation, shrink guard, dry-run default, atomic overwrite, INV-02 repair) is
the real code."""
import csv
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import sheets_sync as ss  # noqa: E402
from lib import HEADER  # noqa: E402


class FakeWS:
    def __init__(self, grid):
        self.grid = grid

    def get_all_values(self):
        return self.grid


def _row(name, qty="1", set_code="M21", cn="1"):
    r = {c: "" for c in HEADER}
    r.update({"Card Name": name, "Type": "Instant", "Set Code": set_code,
              "Collector #": cn, "Quantity Owned": qty})
    return r


def _grid(rows):
    return [HEADER] + [[r.get(c, "") for c in HEADER] for r in rows]


@pytest.fixture
def world(tmp_path, monkeypatch):
    """A 4-row local library + empty mana file, module paths repointed."""
    lib = tmp_path / "card-library.csv"
    mana = tmp_path / "card-mana.csv"
    local = [_row(f"Card {i}", cn=str(i)) for i in range(4)]
    with open(lib, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER)
        w.writeheader()
        for r in local:
            w.writerow(r)
    with open(mana, "w", newline="", encoding="utf-8") as fh:
        fh.write("Card Name,Mana Cost,Mana Value,Keywords\n")
    monkeypatch.setattr(ss, "DEFAULT_CSV", str(lib))
    monkeypatch.setattr(ss, "MANA_CSV", str(mana))
    # validate() reads its own module-level default — point it at the same file.
    import validate as _v
    monkeypatch.setattr(_v, "DEFAULT_CSV", str(lib), raising=False)
    return lib, mana, local


def _use_ws(monkeypatch, grid):
    monkeypatch.setattr(ss, "_worksheet", lambda name: FakeWS(grid))


class TestPullGuards:
    def test_header_only_sheet_is_refused(self, world, monkeypatch):
        """THE case the guard exists for: a cleared/wrong-but-existing tab passes
        the header check AND validate() (zero rows is a 'valid' library), and
        would have replaced the whole inventory with nothing (BS-03)."""
        lib, _mana, local = world
        _use_ws(monkeypatch, [HEADER])
        assert ss.pull("x", apply=True) == 1
        with open(lib, newline="", encoding="utf-8") as fh:
            assert len(list(csv.DictReader(fh))) == len(local)   # untouched

    def test_a_big_shrink_is_refused_without_allow_shrink(self, world, monkeypatch):
        _use_ws(monkeypatch, _grid([_row("Only Card")]))         # 1 row vs 4 local
        assert ss.pull("x", apply=True) == 1

    def test_allow_shrink_is_the_escape_hatch(self, world, monkeypatch):
        lib, _mana, _local = world
        _use_ws(monkeypatch, _grid([_row("Only Card")]))
        assert ss.pull("x", apply=True, allow_shrink=True) == 0
        with open(lib, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert [r["Card Name"] for r in rows] == ["Only Card"]

    def test_pull_is_dry_run_by_default(self, world, monkeypatch):
        lib, _mana, local = world
        _use_ws(monkeypatch, _grid([_row("Replacement %d" % i, cn=str(i)) for i in range(4)]))
        assert ss.pull("x", apply=False) == 0
        with open(lib, newline="", encoding="utf-8") as fh:
            names = [r["Card Name"] for r in csv.DictReader(fh)]
        assert names == [r["Card Name"] for r in local]          # nothing written

    def test_wrong_header_is_refused(self, world, monkeypatch):
        _use_ws(monkeypatch, [["Name", "Qty"], ["Shock", "1"]])
        assert ss.pull("x", apply=True) == 1

    def test_invalid_rows_leave_the_local_csv_untouched(self, world, monkeypatch):
        """The validate() gate: a matching header with bad rows (duplicate
        printing) must not overwrite — write-to-temp, validate, only then promote."""
        lib, _mana, local = world
        dup = _row("Twice", cn="9")
        _use_ws(monkeypatch, _grid([dup, dup, _row("A"), _row("B")]))
        assert ss.pull("x", apply=True) == 1
        with open(lib, newline="", encoding="utf-8") as fh:
            assert len(list(csv.DictReader(fh))) == len(local)


class TestPullWrite:
    def test_full_size_apply_writes_backs_up_and_repairs_inv02(self, world, monkeypatch):
        lib, mana, _local = world
        incoming = [_row(f"New {i}", cn=str(i)) for i in range(4)]
        _use_ws(monkeypatch, _grid(incoming))
        assert ss.pull("x", apply=True) == 0
        with open(lib, newline="", encoding="utf-8") as fh:
            names = {r["Card Name"] for r in csv.DictReader(fh)}
        assert names == {f"New {i}" for i in range(4)}
        # .bak of the pre-overwrite CSV (audit F22 naming, shared scheme)
        assert any(f.endswith(".bak") for f in os.listdir(os.path.dirname(lib)))
        # INV-02: every pulled name got a (blank) card-mana.csv row — pull was the
        # ONE row-adding path that didn't maintain it (broad-scan F-05).
        with open(mana, newline="", encoding="utf-8") as fh:
            mana_names = {r["Card Name"] for r in csv.DictReader(fh)}
        assert mana_names == names
