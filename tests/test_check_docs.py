"""Pin the doc-structure gate (`scripts/check_docs.py`).

CLAUDE.md is the only file a fresh session loads automatically. The split put each
operative rule (plus any still-live residual) there and its evidence in
``docs/gotchas.md``, linked by anchor — which is a hand-kept cross-reference, and this
project's recurring lesson is that those rot silently.

These tests pin the four properties that make the arrangement survivable, and each was
mutation-tested against the real gate.
"""
import os

import check_docs as cd
import pytest


class TestLiveRepo:
    def test_the_repo_passes(self):
        assert cd.check() == []

    def test_every_anchor_resolves_both_ways(self):
        """The round-trip is the whole point: a dangling anchor loses the evidence, an
        orphaned section is evidence nothing can reach."""
        refs = set(cd.ANCHOR_RE.findall(cd._read(cd.CLAUDE_MD)))
        defs = set()
        for path in set(cd.EVIDENCE.values()):
            defs |= {m.group(1) for m in
                     (cd.HEADING_RE.match(l) for l in cd._read(path).split("\n")) if m}
        assert refs == defs
        assert len(refs) >= 70, "the split covers ~80 rules; a big drop means loss"

    def test_each_prefix_lives_in_its_own_file(self):
        """A [C-nn] section in gotchas.md would resolve while pointing the reader at the
        wrong document — as useless as no evidence at all."""
        for path in set(cd.EVIDENCE.values()):
            for l in cd._read(path).split("\n"):
                m = cd.HEADING_RE.match(l)
                if m:
                    assert cd.EVIDENCE[m.group(1).split("-")[0]] == path, m.group(1)

    def test_a_section_in_the_wrong_evidence_file_fails(self, tmp_path, monkeypatch):
        c = tmp_path / "CLAUDE.md"
        c.write_text(_claude_stub("Rule. [C-01]"))
        g = tmp_path / "gotchas.md"
        g.write_text("## [C-01] Misfiled\n\nbody\n")
        y = tmp_path / "cycle.md"
        y.write_text("placeholder\n")
        monkeypatch.setattr(cd, "CLAUDE_MD", str(c))
        monkeypatch.setattr(cd, "EVIDENCE", {"G": str(g), "K": str(g), "C": str(y)})
        assert any("belongs to" in e for e in cd.check())

    def test_a_shared_evidence_file_is_read_once(self, tmp_path, monkeypatch):
        """G and K share gotchas.md. Iterating the PREFIX map read it twice and reported
        every G/K anchor as a duplicate — a gate that fails on a healthy repo."""
        c = tmp_path / "CLAUDE.md"
        c.write_text(_claude_stub("A [G-01]") + "\n- B [K-01]\n")
        g = tmp_path / "gotchas.md"
        g.write_text("## [G-01] a\n\nx\n\n## [K-01] b\n\ny\n")
        y = tmp_path / "cycle.md"
        y.write_text("placeholder\n")
        monkeypatch.setattr(cd, "CLAUDE_MD", str(c))
        monkeypatch.setattr(cd, "EVIDENCE", {"G": str(g), "K": str(g), "C": str(y)})
        assert not any("more than once" in e for e in cd.check())


class TestAnchorRoundTrip:
    def test_a_dangling_anchor_fails(self, tmp_path, monkeypatch):
        c = tmp_path / "CLAUDE.md"
        c.write_text(_claude_stub("Rule text. [G-01]\n- Another. [G-99]"))
        g = tmp_path / "gotchas.md"
        g.write_text("## [G-01] One\n\nbody\n")
        monkeypatch.setattr(cd, "CLAUDE_MD", str(c))
        monkeypatch.setattr(cd, "EVIDENCE", {"G": str(g), "K": str(g), "C": str(g)})
        errs = cd.check()
        assert any("G-99" in e and "no such section" in e for e in errs)

    def test_an_orphaned_section_fails(self, tmp_path, monkeypatch):
        """Evidence nothing points at reads as covered while covering nothing — the
        same failure as an unreachable command."""
        c = tmp_path / "CLAUDE.md"
        c.write_text(_claude_stub("Rule text. [G-01]"))
        g = tmp_path / "gotchas.md"
        g.write_text("## [G-01] One\n\nbody\n\n## [G-02] Stranded\n\nbody\n")
        monkeypatch.setattr(cd, "CLAUDE_MD", str(c))
        monkeypatch.setattr(cd, "EVIDENCE", {"G": str(g), "K": str(g), "C": str(g)})
        assert any("G-02" in e and "orphan" in e for e in cd.check())

    def test_a_duplicate_anchor_fails(self, tmp_path, monkeypatch):
        c = tmp_path / "CLAUDE.md"
        c.write_text(_claude_stub("Rule text. [G-01]"))
        g = tmp_path / "gotchas.md"
        g.write_text("## [G-01] One\n\nbody\n\n## [G-01] Again\n\nbody\n")
        monkeypatch.setattr(cd, "CLAUDE_MD", str(c))
        monkeypatch.setattr(cd, "EVIDENCE", {"G": str(g), "K": str(g), "C": str(g)})
        assert any("more than once" in e for e in cd.check())


class TestVendoredSectionNames:
    """`broad-scan`, `broad-implement`, `health-pulse` and `sync-docs` name these
    sections verbatim and are copied from claude-workflow-tools, so they cannot be
    fixed here. Renaming one breaks a command with no local remedy."""

    @pytest.mark.parametrize("name", cd.REQUIRED_SECTIONS)
    def test_the_section_exists(self, name):
        assert f"## {name}" in cd._read(cd.CLAUDE_MD)

    def test_a_renamed_section_fails(self, tmp_path, monkeypatch):
        c = tmp_path / "CLAUDE.md"
        c.write_text(_claude_stub("Rule. [G-01]").replace("## Common Gotchas",
                                                          "## Gotchas And Pitfalls"))
        g = tmp_path / "gotchas.md"
        g.write_text("## [G-01] One\n\nbody\n")
        monkeypatch.setattr(cd, "CLAUDE_MD", str(c))
        monkeypatch.setattr(cd, "EVIDENCE", {"G": str(g), "K": str(g), "C": str(g)})
        assert any("Common Gotchas" in e and "vendored" in e for e in cd.check())


class TestLineCap:
    """Without this the two files quietly re-fuse over a few cycles, and no other
    check can see it happening — the regression is gradual, not an event."""

    def test_an_overlong_bullet_fails(self, tmp_path, monkeypatch):
        long_rule = "- Rule. [G-01]\n" + "\n".join(
            f"  continuation {i}" for i in range(cd.LINE_CAP + 3))
        c = tmp_path / "CLAUDE.md"
        c.write_text(_claude_stub(None, raw_bullets=long_rule))
        g = tmp_path / "gotchas.md"
        g.write_text("## [G-01] One\n\nbody\n")
        monkeypatch.setattr(cd, "CLAUDE_MD", str(c))
        monkeypatch.setattr(cd, "EVIDENCE", {"G": str(g), "K": str(g), "C": str(g)})
        assert any("cap" in e and "evidence has moved back in" in e for e in cd.check())

    def test_the_live_file_is_under_the_cap(self):
        lines = cd._read(cd.CLAUDE_MD).split("\n")
        for name in cd.SPLIT_SECTIONS:
            for head, buf in cd._section_bullets(lines, name):
                assert len(buf) <= cd.LINE_CAP, f"{name}: {head[:60]}"

    def test_there_is_no_exemption_list(self):
        """An allowlist here would rot exactly like the registries this gate imitates,
        and a rule too long for the cap has somewhere to put the overflow."""
        src = cd.check.__code__.co_consts + tuple(vars(cd))
        assert not any("EXEMPT" in str(x).upper() or "ALLOW" in str(x).upper()
                       for x in vars(cd))


def _claude_stub(rule_line, raw_bullets=None):
    bullets = raw_bullets if raw_bullets is not None else f"- {rule_line}"
    return (
        "# CLAUDE.md\n\n"
        "## Key Design Decisions\n\n- something\n\n"
        "## Common Gotchas\n\n" + bullets + "\n\n"
        "## Known Issues\n\n- none\n\n"
        "## Cycle Workflow Config\n\n"
        "**Test Command:** x\n\nSubsystems\n\nInvariant Library\n"
    )


class TestFigureDriftIsWiredIntoTheGate:
    """BS8-22: `figure_drift` was invoked by `check_docs.main()` alone — i.e. only when
    someone ran the file by hand, which nothing does. It is a radar the gate CONTAINED
    but never reached (G-53 one layer in)."""

    def test_check_all_appends_drift_to_the_soft_list(self):
        import os
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "scripts", "check_all.py")
        with open(p, encoding="utf-8") as fh:
            src = fh.read()
        assert "from check_docs import figure_drift" in src
        i = src.find("from check_docs import figure_drift")
        assert "soft.append(" in src[i:i + 700]
        # It must come AFTER `soft` exists: appending beside the hard doc check raised
        # NameError into that block's `except` and reported a false "doc structure check
        # errored" — a radar whose own wiring is the failure it reports.
        assert src.find("soft = list(derived_warns)") < i

    def test_the_baseline_figure_counts_entries_not_lines(self):
        """The K-09 figure said 188 (the FILE's lines, comments included) while the
        acknowledged set was 173 entries — the number a reader takes it to mean."""
        import os
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "scripts", "tag_role_baseline.txt")
        with open(base, encoding="utf-8") as fh:
            lines = fh.readlines()
        entries = [ln for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]
        assert len(entries) < len(lines), "the baseline carries comments — the two differ"
        assert cd.figure_drift() == [] or all(
            "tag/role baseline" not in lbl for lbl, _s, _l in cd.figure_drift())

    def test_the_gate_count_is_measured_not_asserted(self):
        """BS8-26: three documents carried three different gate counts (11 / 12 / 14)
        against a real 13. A count of files is a measurement, so the radar holds it."""
        assert all("model-sanity gates" not in lbl for lbl, _s, _l in cd.figure_drift()), \
            cd.figure_drift()
