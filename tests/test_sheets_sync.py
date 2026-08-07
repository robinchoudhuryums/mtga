"""Behavioral coverage for scripts/sheets_sync.py — BOTH directions.

`pull` is the authoritative overwrite of the whole inventory, and (until broad-scan
BS-03) the one outside the guard family. It has never been run in production, and "a
complete script nobody has ever run is indistinguishable from a broken one" (ROADMAP)
— these tests are the difference.

`push` was the untested half, which is the same argument one direction over: it CLEARS
the operator's tab and writes the local CSV over it, so it is a destructive overwrite
of the copy you would recover FROM, and it had neither a shrink guard nor a single test
— including none over the RAW value_input_option that keeps a `=`-leading cell from
running as a live formula (audit F10). Added with the guard in BS3-03.

The Google side is faked at `_worksheet`; everything below it (validation, both shrink
guards, dry-run default, atomic overwrite, INV-02 repair, RAW writes) is the real code.
"""
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
        self.cleared = False
        self.written = None          # (range_name, values, value_input_option)

    def get_all_values(self):
        return self.grid

    # The push side of the fake. `clear` before `update` is the destructive part the
    # BS3-03 guard stands in front of, so the tests need to see whether it happened.
    def clear(self):
        self.cleared = True
        self.grid = []

    def update(self, range_name=None, values=None, value_input_option=None):
        self.written = (range_name, values, value_input_option)
        self.grid = values


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
    """Install a fake worksheet and hand it back, so a push test can inspect it.

    The `create` parameter is not decoration: `_worksheet` creates a tab only when
    asked, and push asks while pull does not (BS3-03). A double that ignored it would
    hide a pull that started creating tabs again."""
    ws = FakeWS(grid)
    monkeypatch.setattr(ss, "_worksheet", lambda name, create=False: ws)
    return ws


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


class TestPushGuards:
    """`push` had NO test and NO shrink guard: it clears the tab and writes the local
    CSV over it, so it is the mirror of the operation BS-03 hardened, pointed at the
    operator's other copy. Everything here is the real code with the Google side faked."""

    def test_a_full_size_push_clears_and_writes_the_grid(self, world, monkeypatch):
        _lib, _mana, local = world
        ws = _use_ws(monkeypatch, _grid(local))
        assert ss.push("x", dry_run=False) == 0
        assert ws.cleared
        rng, values, opt = ws.written
        assert rng == "A1"
        assert values[0] == list(HEADER)
        assert len(values) == len(local) + 1

    def test_values_are_written_RAW_not_evaluated(self, world, monkeypatch):
        """audit F10: a cell whose text starts `=`/`+`/`-`/`@` must be stored as
        literal text. USER_ENTERED would let a card name run as a live formula in the
        operator's spreadsheet — a CSV-injection guard with no test until now."""
        ws = _use_ws(monkeypatch, [[]])
        assert ss.push("x", dry_run=False) == 0
        assert ws.written[2] == "RAW"

    def test_dry_run_sends_nothing(self, world, monkeypatch):
        ws = _use_ws(monkeypatch, [[]])
        assert ss.push("x", dry_run=True) == 0
        assert not ws.cleared and ws.written is None

    def test_a_big_shrink_is_refused_and_the_tab_is_left_intact(self, world, monkeypatch):
        """The BS3-03 case: 4 local rows against 40 remote. The tab must still be
        there afterwards — refusing AFTER clear() would be no guard at all."""
        remote = [_row(f"Remote {i}", cn=str(i)) for i in range(40)]
        ws = _use_ws(monkeypatch, _grid(remote))
        assert ss.push("x", dry_run=False) == 1
        assert not ws.cleared and ws.written is None
        assert len(ws.grid) == 41

    def test_allow_shrink_is_the_escape_hatch(self, world, monkeypatch):
        remote = [_row(f"Remote {i}", cn=str(i)) for i in range(40)]
        ws = _use_ws(monkeypatch, _grid(remote))
        assert ss.push("x", dry_run=False, allow_shrink=True) == 0
        assert ws.cleared

    def test_an_empty_remote_tab_is_not_a_shrink(self, world, monkeypatch):
        """A first push into a fresh tab must not be blocked by its own guard."""
        ws = _use_ws(monkeypatch, [])
        assert ss.push("x", dry_run=False) == 0
        assert ws.cleared

    def test_a_small_shrink_is_allowed(self, world, monkeypatch):
        """The floor is >50%, matching pull and import_collection — 4 against 6 is
        an ordinary edit and must go through."""
        remote = [_row(f"Remote {i}", cn=str(i)) for i in range(6)]
        ws = _use_ws(monkeypatch, _grid(remote))
        assert ss.push("x", dry_run=False) == 0
        assert ws.cleared


class TestCheckSetup:
    """`check` is the reason the round-trip was reachable but unused: four independent
    setup steps that each announced themselves only by failing a real transfer."""

    def test_missing_env_reports_each_part_and_moves_no_data(self, world, monkeypatch, capsys):
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        monkeypatch.delenv(ss.SHEET_ID_ENV, raising=False)
        assert ss.check_setup("card-library") == 1
        out = capsys.readouterr().out
        assert "GOOGLE_APPLICATION_CREDENTIALS" in out and ss.SHEET_ID_ENV in out
        assert "Setup incomplete" in out

    def test_a_bad_key_path_is_named_specifically(self, world, monkeypatch, capsys):
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/nope/key.json")
        monkeypatch.setenv(ss.SHEET_ID_ENV, "sheet123")
        ss.check_setup("card-library")
        assert "missing file" in capsys.readouterr().out


class TestWorksheetCreation:
    """A READ must not mutate the remote document. `pull` used to create the tab it
    failed to find, then report it empty."""

    def test_pull_does_not_create_a_missing_worksheet(self, monkeypatch):
        created = []

        class FakeSpreadsheet:
            def worksheet(self, name):
                raise RuntimeError("no such tab")

            def worksheets(self):
                return [type("W", (), {"title": "card-library"})()]

            def add_worksheet(self, **kw):
                created.append(kw)
                return FakeWS([])

        monkeypatch.setattr(ss, "_spreadsheet", lambda: FakeSpreadsheet())
        with pytest.raises(SystemExit):
            ss._worksheet("typo-tab")
        assert created == [], "a read created a worksheet in the operator's sheet"

    def test_push_may_create_one(self, monkeypatch):
        created = []

        class FakeSpreadsheet:
            def worksheet(self, name):
                raise RuntimeError("no such tab")

            def worksheets(self):
                return []

            def add_worksheet(self, **kw):
                created.append(kw)
                return FakeWS([])

        monkeypatch.setattr(ss, "_spreadsheet", lambda: FakeSpreadsheet())
        ss._worksheet("new-tab", create=True)
        assert created and created[0]["title"] == "new-tab"

    def test_the_error_lists_the_tabs_that_do_exist(self, monkeypatch, capsys):
        class FakeSpreadsheet:
            def worksheet(self, name):
                raise RuntimeError("no such tab")

            def worksheets(self):
                return [type("W", (), {"title": "Library"})()]

            def add_worksheet(self, **kw):     # pragma: no cover - must not be reached
                raise AssertionError("read path created a worksheet")

        monkeypatch.setattr(ss, "_spreadsheet", lambda: FakeSpreadsheet())
        with pytest.raises(SystemExit):
            ss._worksheet("card-libary")       # the realistic typo
        assert "'Library'" in capsys.readouterr().err
