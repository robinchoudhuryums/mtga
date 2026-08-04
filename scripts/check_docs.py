#!/usr/bin/env python3
"""Doc-structure gate — keeps CLAUDE.md's rules and their evidence linked.

CLAUDE.md is the ONLY file a fresh session loads automatically, and it had grown to
2,219 lines because every operative rule carried the incident that produced it: 57
Common Gotchas averaging 22 lines each, the longest 97. The rules and the evidence were
fused, so a session could not load one without the other.

The split puts the imperative rule (plus any still-live residual) in CLAUDE.md and the
reasoning, measurements and incident in an evidence file, keyed by a stable anchor whose
PREFIX names the destination — ``G``/``K`` for the Common Gotchas and Known Issues rules
(``docs/gotchas.md``), ``C`` for the Cycle Workflow Config fields
(``docs/cycle-config.md``). **Nothing was deleted** — the history is why the rules are
trusted, and a rule that looks arbitrary is exactly the one a later session "simplifies"
away.

Cycle Workflow Config has a further constraint: its canonical shape is defined by
``setup-cycle.md`` in claude-workflow-tools, the command that WRITES it. Test Command is a
single line, a Subsystem is a comma-separated file list, a Regression Scenario is Steps
plus Expected. Keep the fields terse and in that shape.

That arrangement only survives if something enforces it, because it is a hand-kept
cross-reference and this project's recurring lesson is that those rot (``check_patterns``
fell 13 patterns behind; ``_INLINE_PARSE_ALLOW`` could name deleted code). Five checks:

  1. Every anchor in CLAUDE.md resolves to a section in the evidence file its PREFIX
     names. A ``[C-nn]`` heading sitting in gotchas.md would resolve but send the reader
     to the wrong document, so that is a failure too.
  2. Every section in an evidence file is referenced by CLAUDE.md — **no orphans**. A
     stranded section is evidence nothing can reach, which is the same failure as an
     unreachable command: it reads as covered while covering nothing.
  3. No duplicate anchors anywhere.
  4. The section headings the VENDORED workflow commands depend on still exist.
     ``broad-scan`` / ``broad-implement`` / ``health-pulse`` / ``sync-docs`` say
     "read CLAUDE.md (especially Common Gotchas and Key Design Decisions)" and
     "CLAUDE.md's Cycle Workflow Config"; they are copied verbatim from
     claude-workflow-tools and must not be edited here, so renaming a section would
     break them with no local fix.
  5. A per-bullet LINE CAP on the split sections. Past it a rule is certainly
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
CYCLE_MD = os.path.join(REPO_ROOT, "docs", "cycle-config.md")

# Anchor prefix -> the evidence file that must define it. One prefix per destination, so
# a rule's anchor says WHERE its long form lives: G/K are the Common Gotchas and Known
# Issues rules, C the Cycle Workflow Config fields.
EVIDENCE = {"G": GOTCHAS_MD, "K": GOTCHAS_MD, "C": CYCLE_MD}

# Sections the vendored commands name. Renaming one breaks a command we may not edit.
REQUIRED_SECTIONS = [
    "Common Gotchas",
    "Known Issues",
    "Key Design Decisions",
    "Cycle Workflow Config",
]
# Cycle Workflow Config carries these as bold field labels rather than headings.
REQUIRED_LABELS = ["Invariant Library", "Test Command", "Subsystems"]

# The sections whose long form lives in an evidence file.
SPLIT_SECTIONS = ["Common Gotchas", "Known Issues", "Cycle Workflow Config"]
LINE_CAP = 15               # max lines for one bullet in a split section

# {2,3}: gotchas are at G-67 and rising roughly monotonically — a two-digit cap
# would make the first [G-100] invisible to BOTH scans at once (reference and
# heading), so the round-trip gate would go silent exactly when the numbering
# rolled over (broad-scan batch 4).
ANCHOR_RE = re.compile(r"\[([GKC]-\d{2,3})\]")
HEADING_RE = re.compile(r"^##\s*\[([GKC]-\d{2,3})\]\s*(.*)$")


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
        elif cur is None:
            continue
        elif l and not l.startswith((" ", "\t")):
            # A non-indented, non-bullet line STARTS A NEW BLOCK and so ends the bullet.
            # Without this, a section that is not a pure bullet list (Cycle Workflow
            # Config, with its `**Field:**` labels and numbered scenarios) charged
            # everything after its last bullet to that bullet — INV-06 measured 85 lines.
            out.append((cur, buf))
            cur, buf = None, []
        else:
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

    missing = [p for p in sorted(set(EVIDENCE.values())) if not os.path.exists(p)]
    for p in missing:
        errs.append(f"{os.path.relpath(p, REPO_ROOT)} is missing — CLAUDE.md's rule "
                    "anchors point at it.")
    if missing:
        return errs

    # (1)-(3) the anchor round-trip. Each prefix must be defined in ITS OWN evidence
    # file: a [C-nn] heading sitting in gotchas.md would resolve but send the reader to
    # the wrong document, which is the same failure as no evidence at all.
    defined, dupes, wrong_file = {}, [], []
    # Iterate the distinct FILES, not the prefixes: G and K share gotchas.md, so looping
    # over EVIDENCE.items() read it twice and reported every G/K anchor as a duplicate.
    for path in sorted(set(EVIDENCE.values())):
        for l in _read(path).split("\n"):
            m = HEADING_RE.match(l)
            if not m:
                continue
            a = m.group(1)
            if a in defined:
                dupes.append(a)
            defined[a] = m.group(2).strip()
            if EVIDENCE.get(a.split("-")[0]) != path:
                wrong_file.append((a, os.path.relpath(path, REPO_ROOT)))
    for a in sorted(set(dupes)):
        errs.append(f"[{a}] is defined more than once across the evidence files.")
    for a, where in sorted(set(wrong_file)):
        errs.append(f"[{a}] is defined in {where}, but its prefix belongs to "
                    f"{os.path.relpath(EVIDENCE[a.split('-')[0]], REPO_ROOT)}.")

    referenced = {}
    for i, l in enumerate(lines, 1):
        for a in ANCHOR_RE.findall(l):
            referenced.setdefault(a, []).append(i)
    for a, at in sorted(referenced.items()):
        if len(at) > 1:
            errs.append(f"CLAUDE.md references [{a}] on {len(at)} lines "
                        f"({', '.join(map(str, at[:4]))}) — an anchor names one rule.")

    for a in sorted(set(referenced) - set(defined)):
        want = EVIDENCE.get(a.split("-")[0])
        where = os.path.relpath(want, REPO_ROOT) if want else "any evidence file"
        errs.append(f"CLAUDE.md references [{a}] but {where} has no such section — "
                    "the rule's evidence is unreachable.")
    for a in sorted(set(defined) - set(referenced)):
        errs.append(f"[{a}] ({defined[a][:48]!r}) is defined but nothing in CLAUDE.md "
                    "points at it — an orphaned section reads as covered while covering "
                    "nothing.")

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
        files = ", ".join(sorted({os.path.relpath(p, REPO_ROOT)
                                  for p in EVIDENCE.values()}))
        print(f"Doc structure: OK ({n} rule(s) linked to {files}; "
              f"CLAUDE.md {len(claude)} lines)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
