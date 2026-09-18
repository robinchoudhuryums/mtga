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

# The view-state functions. Same extraction, different question: these decide what
# survives a refresh, which is browser behaviour no Python test can reach.
_STATE_FUNCS = ["parseHash", "restorePrefs", "buildHash", "persist"]

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
  truncated: !!r.truncated,
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
    # A FRAGMENT (18 of 28 cards, under the 75% floor). The fixtures held no partial
    # paste, so the JS side's missing TRUNCATED flag — it rendered "⟳ drifted — 0 added /
    # 10 removed", inviting a sync that would cut the deck down to the fragment — agreed
    # with Python on every pinned field and the mirror drift stayed invisible (BS8-43).
    ["4 Shock (M21) 159", "10 Island (M21) 1", "4 Opt (M21) 2"],
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
                     "runnerUp": (ru or {}).get("id") if m.get("lowconf") and ru else None,
                     "truncated": bool(m.get("truncated"))})
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

    def test_both_flag_a_truncated_paste(self, js_side):
        """BS8-43: the JS mirror had no `truncated` field at all, so a 16-of-60 fragment
        rendered as an ordinary drift. G-08's write-side guard is server-only; this panel
        is read-only, which is exactly why the LABEL has to be right."""
        assert js_side[3]["truncated"] is True, js_side[3]
        assert [r.get("truncated") for r in js_side] == [
            r.get("truncated") for r in _python_side()]
        assert js_side[0]["truncated"] is False, "a full paste is not a fragment"

    def test_the_codepoint_tiebreak_is_what_decides_an_exact_tie(self, js_side):
        """Decks 3 and 10 are identical here, so only the id tie-break separates them.
        Python sorts strings by CODEPOINT, where "10" < "3" — the reason the JS uses plain
        `<` rather than localeCompare, which would order hyphenated ids differently."""
        assert js_side[0]["id"] == "10", js_side[0]
        assert js_side[0]["lowconf"] is True and js_side[0]["runnerUp"] == "3"


# ---------------------------------------------------------------------------- #
# NOTE these are CONCATENATED around the extracted source rather than `eval`-ing it the
# way the matcher harness above does. `eval` leaks FUNCTION declarations into the
# surrounding scope but not a `const`, so an eval'd `const STATE = {...}` is invisible to
# the assertions and the run dies with "STATE is not defined".
_STATE_STUBS = """
let _ls = {};
const localStorage = { getItem: k => (k in _ls ? _ls[k] : null),
                       setItem: (k, v) => { _ls[k] = String(v); } };
let _hash = '';
const location = { get hash(){ return _hash; }, href: 'file:///d.html' };
const history = { replaceState: (a, b, u) => {
  _hash = (u || '').trim().startsWith('#') ? u.trim() : ''; } };
const document = { documentElement: { setAttribute: () => {} } };
const window = { matchMedia: () => ({ matches: false }) };
"""

_STATE_ASSERTS = """
const out = {};
function reset(h){ _hash = h || ''; }

// Expand a deck: the ADDRESS BAR must not carry it…
reset(''); restorePrefs(); STATE.open['45'] = true; persist();
out.addressBar = _hash;
// …but a link you deliberately hand someone must.
out.shareLink = buildHash(true);
// A plain refresh re-reads whatever persisted — nothing should be open.
restorePrefs();
out.afterRefresh = STATE.open;
// An inbound deep link still opens the deck.
reset('#d=45'); restorePrefs();
out.deepLink = STATE.open;
// …while a REAL preference still survives a refresh.
reset(''); restorePrefs(); STATE.theme = 'light'; STATE.pinned = {'41': true}; persist();
restorePrefs();
out.theme = STATE.theme; out.pinned = STATE.pinned;
console.log(JSON.stringify(out));
"""


def _extract_state_js():
    """`STATE` plus the view-state functions, from the shipped source."""
    src = open(BUILD_DASHBOARD, encoding="utf-8").read()
    i = src.index("const STATE = {")
    end = src.index("};", i) + 2
    parts = [src[i:end]]
    for name in _STATE_FUNCS:
        marker = f"function {name}("
        assert marker in src, f"{name} is no longer defined in build_dashboard.py"
        j = src.index(marker)
        depth, start = 0, src.index("{", j)
        for k in range(start, len(src)):
            if src[k] == "{":
                depth += 1
            elif src[k] == "}":
                depth -= 1
                if depth == 0:
                    parts.append(src[j:k + 1])
                    break
        else:
            raise AssertionError(f"unbalanced braces extracting {name}")
    return "\n".join(parts)


@pytest.fixture(scope="module")
def state_side(tmp_path_factory):
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed (CI sets PYTEST_NO_SKIPS, which fails on this)")
    d = tmp_path_factory.mktemp("dashstate")
    (d / "run.js").write_text(
        _STATE_STUBS + "\n" + _extract_state_js() + "\n" + _STATE_ASSERTS,
        encoding="utf-8")
    r = subprocess.run([node, str(d / "run.js")],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"node failed:\n{r.stderr[:2000]}"
    return json.loads(r.stdout)


class TestExpandedPanelsDoNotSurviveARefresh:
    """A user reported that "whenever I refresh, one or more of the decks' details are
    expanded for some reason", and the "for some reason" was the whole bug: the expanded
    set was written to BOTH localStorage and the URL hash, so a panel opened once to read
    something stayed open on every later visit with nothing on screen to explain it.

    The distinction the fix draws — and what these pin — is between a PREFERENCE you
    deliberately set (theme, view mode, colour chips, pinned decks) and a transient
    DISCLOSURE you clicked to read something. The first persists; the second does not.
    Deep links keep working because that route is visible in the address bar, and the 🔗
    share button still captures the open panels because a link you hand someone is a
    deliberate act.

    Browser behaviour, so no Python test can reach it — the same reason this file's other
    class runs the matcher under Node."""

    def test_the_state_js_still_extracts(self):
        """Guards the test itself, like its sibling above: a rename must fail loudly here
        rather than quietly leave the refresh behaviour uncovered."""
        js = _extract_state_js()
        assert "const STATE = {" in js
        for name in _STATE_FUNCS:
            assert f"function {name}(" in js

    def test_expanding_a_deck_does_not_touch_the_address_bar(self, state_side):
        assert state_side["addressBar"] == "", state_side

    def test_the_share_button_still_captures_expanded_decks(self, state_side):
        assert state_side["shareLink"] == "#d=45", state_side

    def test_nothing_is_expanded_after_a_refresh(self, state_side):
        """The reported bug. `STATE.open` used to be restored from localStorage."""
        assert state_side["afterRefresh"] == {}, state_side

    def test_a_deep_link_still_opens_the_deck(self, state_side):
        assert state_side["deepLink"] == {"45": True}, state_side

    def test_real_preferences_still_survive(self, state_side):
        """The other half: this must not have thrown out the state that SHOULD persist."""
        assert state_side["theme"] == "light", state_side
        assert state_side["pinned"] == {"41": True}, state_side
