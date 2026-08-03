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
