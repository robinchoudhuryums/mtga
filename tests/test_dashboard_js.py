"""Cross-language agreement: the dashboard's in-browser matcher vs `deck.match_paste`.

`build_dashboard.py` reimplements deck matching in JavaScript so the stale-deck panel can
run entirely in the browser, and its own comments state the contract:

    Mirrors deck.match_paste exactly; change both or neither.

That contract was prose, and prose is what this project keeps learning is not a
mechanism. It has already broken once: F-08 found the JS comparing drift with a strict
`<` while Python preferred more shared cards then the lower id, so the browser and the CLI
named DIFFERENT decks for the same paste — in exactly the sibling-variant case the
low-confidence flag exists for. The Python side is pinned in test_deck.py; the JS side had
no tests at all, because the repo has no JS test infrastructure.

So this runs BOTH and compares. The JS is extracted from `build_dashboard.py` (the
shipped source, not a copy) and executed under Node against the same fixtures the Python
call gets.

WHY IT SKIPS RATHER THAN FAILING when Node is absent, and why that is not the
test_app_editor.py trap: `PYTEST_NO_SKIPS=1` is set by the CI workflow, and
tests/conftest.py turns any skip into a failure under it. So this runs on a dev box with
Node, skips cleanly without one, and CANNOT quietly stop running in CI — which is the
whole point of the guard C1 added. GitHub's ubuntu-latest ships Node by construction
(every JS action needs it).

The fixtures are chosen for the places the two could diverge, not for coverage breadth:
an exact drift TIE across two decks (where the id tie-break decides, and "10" < "3" by
CODEPOINT is the behaviour the JS comment explains at length), a one-card drift, and a
paste that must match nothing.
"""
import json
import os
import shutil
import subprocess

import pytest

import deck as deckmod

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DASHBOARD = os.path.join(REPO_ROOT, "scripts", "build_dashboard.py")

# The JS functions the stale-deck panel's match path is built from, in dependency order.
_JS_FUNCS = ["parseLine", "formatHint", "deckFormatClass", "multiset", "diffSets",
             "bestMatch", "analyzeOne"]

_HARNESS = """
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
const input = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const D = { decks: input.decks };
eval(src);
const out = input.pastes.map(seg => analyzeOne(seg));
console.log(JSON.stringify(out.map(r => r && (r.unmatched ? {unmatched: true} : {
  id: r.deck.id, added: r.added, removed: r.removed, shared: r.shared,
  sync: r.sync, lowconf: !!r.lowconf, runnerUp: r.runnerUp ? r.runnerUp.id : null,
}))));
"""

DECKS = [
    {"id": "3", "name": "A", "format": "Standard",
     "cards": {"shock": ["Shock", 4], "island": ["Island", 20], "opt": ["Opt", 4]}},
    {"id": "3-brawl", "name": "A Brawl", "format": "Brawl",
     "cards": {"shock": ["Shock", 1], "island": ["Island", 20], "opt": ["Opt", 1]}},
    {"id": "10", "name": "B", "format": "Standard",
     "cards": {"shock": ["Shock", 4], "island": ["Island", 20], "opt": ["Opt", 4]}},
]
PASTES = [
    ["4 Shock (M21) 159", "20 Island (M21) 1", "4 Opt (M21) 2"],   # exact tie: 3 vs 10
    ["4 Shock (M21) 159", "20 Island (M21) 1", "3 Opt (M21) 2"],   # one-card drift
    ["1 Forest (M21) 1", "1 Plains (M21) 2", "1 Mountain (M21) 3"],  # matches nothing
]


def _extract_js():
    """The named functions, lifted brace-balanced out of build_dashboard.py's source.

    Reads the SHIPPED source rather than a copied fixture: a fixture would be a third
    implementation to keep in sync, which is the problem this test exists for. A rename
    breaks extraction loudly instead of silently testing stale code."""
    src = open(BUILD_DASHBOARD, encoding="utf-8").read()
    out = []
    for name in _JS_FUNCS:
        marker = f"function {name}("
        assert marker in src, (
            f"{name} is no longer defined in build_dashboard.py — the extraction is stale, "
            "so this agreement test would silently stop covering the matcher.")
        i = src.index(marker)
        depth, start = 0, src.index("{", i)
        for k in range(start, len(src)):
            if src[k] == "{":
                depth += 1
            elif src[k] == "}":
                depth -= 1
                if depth == 0:
                    out.append(src[i:k + 1])
                    break
        else:
            raise AssertionError(f"unbalanced braces extracting {name}")
    return "\n".join(out)


def _python_side():
    from import_arena import parse as parse_arena
    decks = [({"id": d["id"], "name": d["name"], "format": d["format"]},
              {k: (v[0], v[1]) for k, v in d["cards"].items()}) for d in DECKS]
    rows = []
    for seg in PASTES:
        entries, _w = parse_arena("\n".join(seg))
        pasted = deckmod._multiset(entries)
        hint = deckmod.paste_format_hint(seg, sum(q for q, *_ in entries))
        m = deckmod.match_paste(pasted, decks, fmt_hint=hint)
        if m.get("unmatched"):
            rows.append({"unmatched": True})
            continue
        ru = m.get("runner_up")
        rows.append({"id": m["deck"]["id"], "added": m["added"], "removed": m["removed"],
                     "shared": m["shared"], "sync": bool(m["drift"] == 0),
                     "lowconf": bool(m.get("lowconf")),
                     "runnerUp": (ru or {}).get("id") if m.get("lowconf") and ru else None})
    return rows


@pytest.fixture(scope="module")
def js_side(tmp_path_factory):
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed (CI sets PYTEST_NO_SKIPS, which fails on this)")
    d = tmp_path_factory.mktemp("dashjs")
    (d / "m.js").write_text(_extract_js(), encoding="utf-8")
    (d / "h.js").write_text(_HARNESS, encoding="utf-8")
    (d / "in.json").write_text(json.dumps({"decks": DECKS, "pastes": PASTES}),
                               encoding="utf-8")
    r = subprocess.run([node, str(d / "h.js"), str(d / "m.js"), str(d / "in.json")],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"node failed:\n{r.stderr[:2000]}"
    return json.loads(r.stdout)


class TestDashboardMatcherAgreesWithPython:
    def test_the_js_still_extracts(self):
        """Guards the test itself: a renamed function must fail here rather than quietly
        leave the matcher uncovered."""
        js = _extract_js()
        for name in _JS_FUNCS:
            assert f"function {name}(" in js

    def test_both_implementations_name_the_same_decks(self, js_side):
        py = _python_side()
        assert [r.get("id") for r in js_side] == [r.get("id") for r in py], (
            f"\n  JS: {js_side}\n  PY: {py}")

    def test_both_agree_on_drift_and_confidence(self, js_side):
        """The full record, not just the winner: F-08 changed WHICH deck won, but a
        divergence in the low-confidence flag or the drift counts would mislead just as
        badly while naming the same deck."""
        assert js_side == _python_side(), f"\n  JS: {js_side}\n  PY: {_python_side()}"

    def test_the_codepoint_tiebreak_is_what_decides_an_exact_tie(self, js_side):
        """Decks 3 and 10 are identical here, so only the id tie-break separates them.
        Python sorts strings by CODEPOINT, where "10" < "3" — the reason the JS uses plain
        `<` rather than localeCompare, which would order hyphenated ids differently."""
        assert js_side[0]["id"] == "10", js_side[0]
        assert js_side[0]["lowconf"] is True and js_side[0]["runnerUp"] == "3"
