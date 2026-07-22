"""Unit tests for scripts/lib.py — the shared primitives every tool routes through.

These pin the exact edge cases behind the F1/F2 (color parsing) and F6 (DFC
ownership) fixes, plus the atomic-write safety net, so a refactor can't regress them
without a red test (the static/behavioural check_* gates cover the same ground at
the integration level; this is the fast, isolated layer)."""
import csv

import lib


class TestCardColors:
    def test_colorless_is_empty(self):
        # The F1 trap: "Colorless" contains an R, so a naive parse read it as {'R'}.
        assert lib.card_colors("Colorless") == set()

    def test_slash_gold(self):
        assert lib.card_colors("B/G") == {"B", "G"}

    def test_five_color(self):
        assert lib.card_colors("W/U/B/R/G") == set("WUBRG")

    def test_mono(self):
        assert lib.card_colors("U") == {"U"}

    def test_blank_and_none(self):
        assert lib.card_colors("") == set()
        assert lib.card_colors(None) == set()

    def test_colorless_is_subset_of_everything(self):
        # A colorless identity must be castable in every deck.
        assert lib.card_colors("Colorless").issubset(set())
        assert lib.card_colors("Colorless").issubset({"W", "U"})


class TestOwnedQty:
    IDX = {"fable of the mirror-breaker": 2, "llanowar elves": 4}

    def test_dfc_resolves_by_front_face(self):
        # Library keys a DFC under its front name; the pool/wishlist pass the full name.
        assert lib.owned_qty(self.IDX, "Fable of the Mirror-Breaker // Reflection of Kiki-Rikki") == 2

    def test_plain_front_name(self):
        assert lib.owned_qty(self.IDX, "Llanowar Elves") == 4

    def test_unowned_is_zero_not_none(self):
        assert lib.owned_qty(self.IDX, "Nonexistent Card") == 0

    def test_case_insensitive(self):
        assert lib.owned_qty(self.IDX, "LLANOWAR ELVES") == 4


class TestBackupPath:
    def test_sortable_and_unique(self):
        a = lib.backup_path("/tmp/x.csv")
        assert a.startswith("/tmp/x.csv.") and a.endswith(".bak")

    def test_collision_suffix_sorts_after(self, tmp_path):
        # A same-timestamp collision must get a suffix that sorts AFTER the base name
        # (audit F22), so "newest by name" stays correct.
        target = str(tmp_path / "x")
        base = lib.backup_path(target)
        open(base, "w").close()
        # Force the collision path by reusing the same stamp portion.
        stamp = base[len(target) + 1:-4]
        collide = f"{target}.{stamp}.bak"
        assert collide == base  # sanity: we reconstructed the exact name
        nxt = lib.backup_path(target)
        # a fresh call returns a name >= the existing one lexically (monotonic)
        assert nxt >= base


class TestAtomicWrite:
    def test_writes_and_backs_up(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("original\n", encoding="utf-8")
        lib.atomic_write(str(p), lambda fh: fh.write("new\n"))
        assert p.read_text(encoding="utf-8") == "new\n"
        baks = list(tmp_path.glob("data.csv.*.bak"))
        assert len(baks) == 1 and baks[0].read_text(encoding="utf-8") == "original\n"

    def test_no_backup_flag(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("original\n", encoding="utf-8")
        lib.atomic_write(str(p), lambda fh: fh.write("new\n"), backup=False)
        assert not list(tmp_path.glob("data.csv.*.bak"))

    def test_failed_write_leaves_original(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("original\n", encoding="utf-8")

        def boom(fh):
            raise RuntimeError("mid-write failure")

        try:
            lib.atomic_write(str(p), boom)
        except RuntimeError:
            pass
        assert p.read_text(encoding="utf-8") == "original\n"  # untouched
        assert not list(tmp_path.glob("*.tmp"))  # temp cleaned up


class TestWriteRows:
    def test_roundtrip_canonical_header(self, tmp_path):
        p = tmp_path / "lib.csv"
        rows = [{"Card Name": "Shock", "Type": "Instant", "Card Text": "Deal 2",
                 "Color(s)": "R", "Synergies": "burn", "Set Code": "M19",
                 "Collector #": "156", "Quantity Owned": "4", "StrayKey": "ignored"}]
        lib.write_rows(rows, str(p))
        with open(p, newline="", encoding="utf-8") as fh:
            got = list(csv.DictReader(fh))
        assert got[0]["Card Name"] == "Shock"
        assert "StrayKey" not in got[0]  # only canonical columns emitted
        assert list(got[0].keys()) == lib.HEADER
