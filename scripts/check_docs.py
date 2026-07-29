#!/usr/bin/env python3
"""Doc-structure gate — keeps CLAUDE.md's rules and their evidence linked.

CLAUDE.md is the ONLY file a fresh session loads automatically, and it had grown to
2,219 lines because every operative rule carried the incident that produced it: 57
Common Gotchas averaging 22 lines each, the longest 97. The rules and the evidence were
fused, so a session could not load one without the other.

The split puts the imperative rule (plus any still-live residual) in CLAUDE.md and the
reasoning, measurements and incident in ``docs/gotchas.md``, keyed by a stable anchor
like ``[G-23]``. **Nothing was deleted** — the history is why the rules are trusted, and
a rule that looks arbitrary is exactly the one a later session "simplifies" away.

That arrangement only survives if something enforces it, because it is a hand-kept
cross-reference and this project's recurring lesson is that those rot (``check_patterns``
fell 13 patterns behind; ``_INLINE_PARSE_ALLOW`` could name deleted code). Five checks:

  1. Every anchor in CLAUDE.md resolves to a section in docs/gotchas.md.
  2. Every section in docs/gotchas.md is referenced by CLAUDE.md — **no orphans**. A
     stranded section is evidence nothing can reach, which is the same failure as an
     unreachable command: it reads as covered while covering nothing.
  3. No duplicate anchors on either side.
  4. The section headings the VENDORED workflow commands depend on still exist.
     ``broad-scan`` / ``broad-implement`` / ``health-pulse`` / ``sync-docs`` say
     "read CLAUDE.md (especially Common Gotchas and Key Design Decisions)" and
     "CLAUDE.md's Cycle Workflow Config"; they are copied verbatim from
     claude-workflow-tools and must not be edited here, so renaming a section would
     break them with no local fix.
  5. A per-bullet LINE CAP on the two split sections. Past it a rule is certainly
     carrying its evidence again, and without this the file re-fuses in a few cycles —
     the regression is gradual and no other check can see it. Deliberately no exemption
     list: an allowlist here would rot exactly like the registries above, and a rule too
     long for the cap has somewhere to put the overflow.

Distribution-independent, no third-party deps. check_all.py folds this in as a HARD
gate. Run standalone (``python3 scripts/check_docs.py``). Returns a list of error
strings; empty == healthy.
"""
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE_MD = os.path.join(REPO_ROOT, "CLAUDE.md")
GOTCHAS_MD = os.path.join(REPO_ROOT, "docs", "gotchas.md")

# Sections the vendored commands name. Renaming one breaks a command we may not edit.
REQUIRED_SECTIONS = [
    "Common Gotchas",
    "Known Issues",
    "Key Design Decisions",
    "Cycle Workflow Config",
]
# Cycle Workflow Config carries these as bold field labels rather than headings.
REQUIRED_LABELS = ["Invariant Library", "Test Command", "Subsystems"]

# The two sections whose evidence lives in docs/gotchas.md.
SPLIT_SECTIONS = ["Common Gotchas", "Known Issues"]
LINE_CAP = 15               # max lines for one bullet in a split section

ANCHOR_RE = re.compile(r"\[([GK]-\d{2})\]")
HEADING_RE = re.compile(r"^##\s*\[([GK]-\d{2})\]\s*(.*)$")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _section_bullets(lines, name):
    """The top-level bullets of one `## <name>` section, as [(head, [lines])]."""
    try:
        a = next(i for i, l in enumerate(lines) if l.startswith("## " + name))
    except StopIteration:
        return []
    b = next((i for i, l in enumerate(lines) if i > a and l.startswith("## ")), len(lines))
    out, cur, buf = [], None, []
    for l in lines[a + 1:b]:
        if re.match(r"^- ", l):
            if cur is not None:
                out.append((cur, buf))
            cur, buf = l, [l]
        elif cur is not None:
            buf.append(l)
    if cur is not None:
        out.append((cur, buf))
    return out


def check():
    errs = []
    if not os.path.exists(CLAUDE_MD):
        return ["CLAUDE.md is missing"]
    claude = _read(CLAUDE_MD)
    lines = claude.split("\n")

    # (4) section headings the vendored commands depend on
    for name in REQUIRED_SECTIONS:
        if f"## {name}" not in claude:
            errs.append(
                f"CLAUDE.md no longer has a '## {name}' section. The vendored workflow "
                "commands name it verbatim and cannot be edited here — restore the "
                "heading (see check_docs REQUIRED_SECTIONS).")
    for label in REQUIRED_LABELS:
        if label not in claude:
            errs.append(f"CLAUDE.md no longer mentions '{label}', which the vendored "
                        "workflow commands read out of the Cycle Workflow Config.")

    if not os.path.exists(GOTCHAS_MD):
        errs.append("docs/gotchas.md is missing — CLAUDE.md's rule anchors point at it.")
        return errs
    gotchas = _read(GOTCHAS_MD)

    # (1)-(3) the anchor round-trip
    defined, dupes = {}, []
    for l in gotchas.split("\n"):
        m = HEADING_RE.match(l)
        if m:
            if m.group(1) in defined:
                dupes.append(m.group(1))
            defined[m.group(1)] = m.group(2).strip()
    for a in sorted(set(dupes)):
        errs.append(f"docs/gotchas.md defines [{a}] more than once.")

    referenced = {}
    for i, l in enumerate(lines, 1):
        for a in ANCHOR_RE.findall(l):
            referenced.setdefault(a, []).append(i)
    for a, at in sorted(referenced.items()):
        if len(at) > 1:
            errs.append(f"CLAUDE.md references [{a}] on {len(at)} lines "
                        f"({', '.join(map(str, at[:4]))}) — an anchor names one rule.")

    for a in sorted(set(referenced) - set(defined)):
        errs.append(f"CLAUDE.md references [{a}] but docs/gotchas.md has no such "
                    "section — the rule's evidence is unreachable.")
    for a in sorted(set(defined) - set(referenced)):
        errs.append(f"docs/gotchas.md defines [{a}] ({defined[a][:48]!r}) but nothing in "
                    "CLAUDE.md points at it — an orphaned section reads as covered while "
                    "covering nothing.")

    # (5) the line cap that stops the two files re-fusing
    for name in SPLIT_SECTIONS:
        for head, buf in _section_bullets(lines, name):
            if len(buf) > LINE_CAP:
                title = re.sub(r"\s+", " ", head)[:64]
                errs.append(
                    f"CLAUDE.md '{name}' bullet is {len(buf)} lines (cap {LINE_CAP}): "
                    f"{title}… — that length means the evidence has moved back in. Keep "
                    "the rule and the live residual here; put the rest in its "
                    "docs/gotchas.md section.")
    return errs


def main():
    errs = check()
    for e in errs:
        print(f"FAIL: {e}")
    if not errs:
        claude = _read(CLAUDE_MD).split("\n")
        n = len(set(ANCHOR_RE.findall(_read(CLAUDE_MD))))
        print(f"Doc structure: OK ({n} rule(s) linked to docs/gotchas.md; "
              f"CLAUDE.md {len(claude)} lines)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
