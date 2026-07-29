"""Pin the doc-structure gate (`scripts/check_docs.py`).

CLAUDE.md is the only file a fresh session loads automatically. The split put each
operative rule (plus any still-live residual) there and its evidence in
``docs/gotchas.md``, linked by anchor — which is a hand-kept cross-reference, and this
project's recurring lesson is that those rot silently.

These tests pin the four properties that make the arrangement survivable, and each was
mutation-tested against the real gate.
"""
import check_docs as cd
import pytest


class TestLiveRepo:
    def test_the_repo_passes(self):
        assert cd.check() == []

    def test_every_anchor_resolves_both_ways(self):
        """The round-trip is the whole point: a dangling anchor loses the evidence, an
        orphaned section is evidence nothing can reach."""
        claude = cd._read(cd.CLAUDE_MD)
        gotchas = cd._read(cd.GOTCHAS_MD)
        refs = set(cd.ANCHOR_RE.findall(claude))
        defs = {m.group(1) for m in
                (cd.HEADING_RE.match(l) for l in gotchas.split("\n")) if m}
        assert refs == defs
        assert len(refs) >= 60, "the split covers ~69 rules; a big drop means loss"


class TestAnchorRoundTrip:
    def test_a_dangling_anchor_fails(self, tmp_path, monkeypatch):
        c = tmp_path / "CLAUDE.md"
        c.write_text(_claude_stub("Rule text. [G-01]\n- Another. [G-99]"))
        g = tmp_path / "gotchas.md"
        g.write_text("## [G-01] One\n\nbody\n")
        monkeypatch.setattr(cd, "CLAUDE_MD", str(c))
        monkeypatch.setattr(cd, "GOTCHAS_MD", str(g))
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
        monkeypatch.setattr(cd, "GOTCHAS_MD", str(g))
        assert any("G-02" in e and "orphan" in e for e in cd.check())

    def test_a_duplicate_anchor_fails(self, tmp_path, monkeypatch):
        c = tmp_path / "CLAUDE.md"
        c.write_text(_claude_stub("Rule text. [G-01]"))
        g = tmp_path / "gotchas.md"
        g.write_text("## [G-01] One\n\nbody\n\n## [G-01] Again\n\nbody\n")
        monkeypatch.setattr(cd, "CLAUDE_MD", str(c))
        monkeypatch.setattr(cd, "GOTCHAS_MD", str(g))
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
        monkeypatch.setattr(cd, "GOTCHAS_MD", str(g))
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
        monkeypatch.setattr(cd, "GOTCHAS_MD", str(g))
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
