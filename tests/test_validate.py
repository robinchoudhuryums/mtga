"""Behavioral coverage for scripts/validate.py — the INV-01 gate itself. It ran
inside check_all and sheets_sync for years with no direct tests (broad-scan
BS-20/batch 6); a validator that silently stops catching what INV-01 claims is a
gate that never fires."""
import csv
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from validate import validate  # noqa: E402
from lib import HEADER  # noqa: E402


def _write(tmp_path, rows, header=None):
    p = tmp_path / "lib.csv"
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header or HEADER)
        for r in rows:
            w.writerow(r)
    return str(p)


def _row(name, set_code="M21", cn="1", qty="1"):
    return [name, "Instant", "Some text.", "R", "", set_code, cn, qty]


class TestInv01:
    def test_a_clean_library_passes(self, tmp_path):
        assert validate(_write(tmp_path, [_row("Shock"), _row("Duress", cn="2")])) == 0

    def test_header_mismatch_fails(self, tmp_path):
        assert validate(_write(tmp_path, [], header=["Name", "Qty"])) == 1

    def test_duplicate_printing_fails(self, tmp_path):
        assert validate(_write(tmp_path, [_row("Shock"), _row("Shock")])) == 1

    def test_same_name_different_printing_passes(self, tmp_path):
        assert validate(_write(tmp_path, [_row("Shock", cn="1"), _row("Shock", cn="2")])) == 0

    def test_negative_quantity_fails(self, tmp_path):
        assert validate(_write(tmp_path, [_row("Shock", qty="-1")])) == 1

    def test_non_numeric_quantity_fails(self, tmp_path):
        assert validate(_write(tmp_path, [_row("Shock", qty="two")])) == 1

    def test_blank_quantity_is_legal(self, tmp_path):
        assert validate(_write(tmp_path, [_row("Shock", qty="")])) == 0

    def test_missing_file_is_an_error_not_a_crash(self, tmp_path):
        assert validate(str(tmp_path / "nope.csv")) == 1

    def test_header_only_zero_rows_PASSES_by_design(self, tmp_path):
        """CHARACTERIZATION, not endorsement: INV-01 makes no row-count claim, so
        an empty library is 'valid' — which is exactly why sheets_sync pull and
        import_collection carry their own shrink guards (BS-03). If this ever
        starts failing, those guards' division of labor changed: update them
        together, not this test alone."""
        assert validate(_write(tmp_path, [])) == 0
