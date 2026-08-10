"""Pins check_roles.py — the radar for cards `classify_roles` scores with no role.

The gate exists because `_ROLE_PATTERNS` is a WHITELIST, and a whitelist fails
silently: a card templated a way no pattern anticipates scores nothing, and the tier
floor, `cuts` and the quality guard all inherit that as fact. What these tests protect
is the gate's own contract, not the pattern set.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import check_roles  # noqa: E402


class TestCheckRoles:
    def test_baseline_file_exists_and_parses(self):
        # A missing baseline silently turns the gate into "report all 368", which floods
        # the soft channel and trains the reader to ignore it.
        assert os.path.exists(check_roles.BASELINE)
        assert len(check_roles.load_baseline()) > 0

    def test_baseline_is_comment_and_blank_tolerant(self, tmp_path):
        f = tmp_path / "b.txt"
        f.write_text("# header\n\nSome Card\nOther Card\n")
        saved = check_roles.BASELINE
        try:
            check_roles.BASELINE = str(f)
            assert check_roles.load_baseline() == {"some card", "other card"}
        finally:
            check_roles.BASELINE = saved

    def test_zero_role_output_is_deterministic(self):
        # G-54: a set plus a tie-able sort key is a nondeterministic output, and this
        # feeds a file that gets diffed. The key must be a total order.
        a = [r[0] for r in check_roles.zero_role_cards()]
        b = [r[0] for r in check_roles.zero_role_cards()]
        assert a == b
        assert a == sorted(a, key=str.lower)

    def test_check_is_quiet_against_its_own_baseline(self):
        # The gate's contract: silent until something NEW appears. If this fails, either a
        # deck edit introduced an untriaged card or a role pattern regressed — read the
        # names, fix the pattern or re-baseline. It is a soft warning, never a hard gate.
        assert check_roles.check() == []

    def test_lands_and_textless_cards_are_never_reported(self):
        # K-11: genuinely text-less vanillas are expected, not findings. Lands are graded
        # by the manabase tools, not by roles.
        for name, ctype, text in check_roles.zero_role_cards():
            assert "Land" not in ctype, name
            assert text.strip(), name


class TestBaselineDelta:
    """BS4-02: `make postedit` ran `--update-baseline` unconditionally BEFORE check_all,
    so the radar's warning was consumed by the same command meant to surface it. A
    `_ROLE_PATTERNS` edit re-zeroing fifty cards was acknowledged wholesale with an
    unread diff of a 425-line file as the only trace. The delta is what lets the caller
    show its work; --max-new is what stops a regression-sized jump landing silently."""

    def _fake_baseline(self, tmp_path, names):
        f = tmp_path / "b.txt"
        f.write_text("# header\n" + "".join(n + "\n" for n in names))
        return str(f)

    def test_delta_names_new_and_pruned(self, tmp_path, monkeypatch):
        monkeypatch.setattr(check_roles, "BASELINE",
                            self._fake_baseline(tmp_path, ["stale card", "kept card"]))
        monkeypatch.setattr(check_roles, "zero_role_cards",
                            lambda: [("Kept Card", "Creature", "x"),
                                     ("Brand New", "Creature", "y")])
        new, pruned = check_roles.baseline_delta()
        # DISPLAY names: a human is meant to read these and go look the card up.
        assert new == ["Brand New"]        # NEW — the thing a human must read
        assert pruned == ["stale card"]    # acknowledged nothing; safe to drop

    def test_update_refuses_a_regression_sized_jump(self, tmp_path, monkeypatch, capsys):
        # The load-bearing half: a pattern regression re-zeroes many cards at once, and
        # that must NOT be absorbable by the routine post-edit command.
        path = self._fake_baseline(tmp_path, [])
        monkeypatch.setattr(check_roles, "BASELINE", path)
        monkeypatch.setattr(check_roles, "zero_role_cards",
                            lambda: [(f"Card {i}", "Creature", "t") for i in range(30)])
        monkeypatch.setattr(sys, "argv",
                            ["check_roles.py", "--update-baseline", "--max-new", "8"])
        assert check_roles.main() == 1
        assert "REFUSING" in capsys.readouterr().err
        # and it must not have written the file it refused to write
        assert check_roles.load_baseline() == set()

    def test_update_below_the_cap_writes_and_names_the_new_cards(self, tmp_path, monkeypatch, capsys):
        path = self._fake_baseline(tmp_path, [])
        monkeypatch.setattr(check_roles, "BASELINE", path)
        monkeypatch.setattr(check_roles, "zero_role_cards",
                            lambda: [("Quag Feast", "Sorcery", "t")])
        monkeypatch.setattr(sys, "argv",
                            ["check_roles.py", "--update-baseline", "--max-new", "8"])
        assert check_roles.main() == 0
        out = capsys.readouterr().out
        assert "Quag Feast" in out and "NEW" in out      # named, not just counted
        assert check_roles.load_baseline() == {"quag feast"}
