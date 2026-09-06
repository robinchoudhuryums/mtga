"""Smoke tests for the command-line surface — the one thing no other gate touches.

`check_all.py` imports `deck` as a MODULE and calls its MODEL functions — 16 of them,
and NO `cmd_*` at all (this docstring said otherwise until 2026-08-24, as did CLAUDE.md
and docs/cycle-config.md). Nothing in it, and nothing else under tests/, ever constructs
an `ArgumentParser`. So the parsers were unreachable from every gate in the project, and
`deck.py --help` shipped broken for four days with three green workflows (F-01/F-12):

    help="... (keepable %, land drops, ...)"

argparse renders a help string through `help % params`, so a bare `%` raises
`ValueError: unsupported format character` — and because the top-level help expands
every subaction, ONE bad subcommand string killed the whole `--help` output. Every
model-sanity gate, invariant and unit test passed throughout.

The help tests are deliberately shallow: they prove each entry point STARTS and
renders its help. The COMMAND-layer tests at the bottom of this file go one level
deeper — they run each subcommand for real and pin the contract it owes (exit cleanly,
no traceback, produce output) — because `check_all` reaching no `cmd_*` means everything
those functions do at RENDER time is otherwise ungated. Semantic depth still lives in
the other test modules and in check_all.py. They run as subprocesses because that is the only way to exercise
`main()` and the argparse tree the way a user does — and in a thread pool, because 28
interpreter startups in series is the difference between ~2s and ~20s.
"""
import concurrent.futures
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
TRACEBACK = "Traceback (most recent call last)"


def _scripts():
    return sorted(f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".py"))


def _uses_argparse(filename):
    with open(os.path.join(SCRIPTS_DIR, filename), encoding="utf-8") as fh:
        return "ArgumentParser" in fh.read()


def _run(args, timeout=120, stdin=None):
    """(returncode, stdout+stderr) for `python3 <args>` from the repo root."""
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True,
                       cwd=REPO_ROOT, timeout=timeout, input=stdin)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _run_all(arg_lists):
    """Run many commands concurrently -> {key: (rc, output)}. Subprocesses are
    IO-bound from the parent's view, so a thread pool is enough."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {key: pool.submit(_run, args) for key, args in arg_lists}
        return {key: f.result() for key, f in futures.items()}


@pytest.fixture(scope="module")
def script_help():
    """`<script> --help` for every script, run once and shared across the tests."""
    return _run_all([(f, [os.path.join("scripts", f), "--help"]) for f in _scripts()])


@pytest.fixture(scope="module")
def subcommands():
    """deck.py's subcommand list, read from its own `--help` output."""
    rc, out = _run([os.path.join("scripts", "deck.py"), "--help"])
    assert rc == 0, out
    start, end = out.find("{"), out.find("}")
    assert 0 <= start < end, f"could not read the subcommand list from:\n{out[:400]}"
    return sorted(out[start + 1:end].split(","))


class TestScriptEntryPoints:
    """Every script must START. This is the contract F-01 broke."""

    def test_no_script_crashes_on_help(self, script_help):
        crashed = {f: out for f, (_rc, out) in script_help.items() if TRACEBACK in out}
        assert not crashed, (
            "these scripts raise on `--help`:\n"
            + "\n".join(f"  {f}: {out.strip().splitlines()[-1]}"
                        for f, out in crashed.items()))

    def test_argparse_scripts_render_usage(self, script_help):
        """A script with an ArgumentParser must exit 0 on --help and print usage.

        Scripts without one are excluded by inspection, not by name: `validate.py`
        and `card.py` take a bare positional via sys.argv, and the check_*.py gates
        just run. Excluding them by a hardcoded list would go stale the moment one
        gains a parser; deriving it from the source cannot."""
        problems = []
        for f, (rc, out) in script_help.items():
            if not _uses_argparse(f):
                continue
            if f == "app.py" and "needs Flask" in out:
                continue  # optional dependency absent — its own friendly message
            if rc != 0 or "usage:" not in out:
                problems.append(f"{f}: rc={rc}, first line {out.strip()[:80]!r}")
        assert not problems, "\n".join(problems)

    def test_the_f01_regression_specifically(self):
        """A bare `%` in any argparse help string takes the WHOLE top-level help
        down, because rendering expands every subaction. deck.py has dozens of
        subparsers, so it is both the likeliest place for this and the costliest.
        (Deliberately count-free: a hardcoded count here rotted twice.)"""
        rc, out = _run([os.path.join("scripts", "deck.py"), "--help"])
        assert rc == 0, out
        assert "unsupported format character" not in out
        assert "usage: deck.py" in out


class TestDeckSubcommands:
    """deck.py is the project's main interface — dozens of subparsers, each with its
    own help strings, and the roster of commands a skill is supposed to be re-read
    against. Each subparser's own `--help` must render too."""

    def test_the_subcommand_list_is_discoverable(self, subcommands):
        assert len(subcommands) > 25
        for expected in ("stats", "mana", "consistency", "cuts", "tier", "audit"):
            assert expected in subcommands

    def test_every_subcommand_help_renders(self, subcommands):
        results = _run_all([(c, [os.path.join("scripts", "deck.py"), c, "--help"])
                            for c in subcommands])
        problems = [f"{c}: rc={rc} :: {out.strip().splitlines()[-1] if out.strip() else ''}"
                    for c, (rc, out) in sorted(results.items())
                    if rc != 0 or TRACEBACK in out]
        assert not problems, "\n".join(problems)


# ── The COMMAND layer, run for real ──────────────────────────────────────────────────
#
# Everything above proves an entry point STARTS and renders its help. Nothing proved one
# COMPUTES. That gap is bigger than it looks, and the 2026-08-24 Analysis audit measured
# why: `check_all` imports `deck` as a module and calls 16 MODEL functions and ZERO
# `cmd_*` — a fact CLAUDE.md and docs/cycle-config.md both stated backwards for a year.
# So the whole command layer — argument plumbing, output assembly, and every arithmetic
# that happens at RENDER time — was reachable by no gate at all.
#
# `tier --to` is the worked example. It paired each filler with a cut by positional
# `zip`, blind to what the cut did, so a plan closing an interaction gap could propose
# cutting an interaction card: the two cancelled, the projection came back short, and the
# user was told to "pick another cut" for a decision the tool could have made. Three of
# eleven roster plans were affected. Every model function it calls was correct; the bug
# was entirely in the layer nothing ran.
#
# These tests are one level deeper than the help smoke above and still deliberately
# shallow on semantics — depth belongs in test_deck.py and check_all.py. What they pin is
# the contract every command owes: exit 0, no traceback, and OUTPUT. A command that
# silently prints nothing is the failure this catches, and it is indistinguishable from a
# healthy one in any other gate.
#
# ARGS is exhaustive on purpose. A subcommand missing from it FAILS rather than being
# skipped, so a new command must be classified deliberately — the same discipline
# check_commands applies to workflow reachability, where a stale exemption is itself a
# failure (G-53). Every entry is a READ-ONLY invocation: the four write-capable commands
# (swap, apply-flex, sync, resolve --fix) are all dry-run until `--apply`, verified.
# Sentinel: this command reads a pasted deck from STDIN, so it gets a real export rather
# than an empty pipe. With no input `sync` correctly reports "no deck blocks found" and
# exits 1 — true, but it exercises the guard instead of the matching path this covers.
_STDIN = object()


def _pick_deck():
    """(deck_id, cut_card, section_header, add_card, variant_pair) chosen FROM the live
    roster, not hardcoded (BS8-24).

    `_DECK = "43"` plus the literal card names "Stroke of Midnight" / "Bilbo, Luckwearer"
    and the header "Removal" pinned this suite to one deck's current contents — and the
    handoff records the user weighing exactly the swap that would remove one of them, so
    a legitimate tune would have turned CI red on a file the tune never touched.

    Everything the command args need is derived from whatever the roster holds today: a
    Standard deck with at least two UNAMBIGUOUS `# section` headers (what `swap --section`
    and `move` require), a nonland card sitting under one of them, a DIFFERENT header to
    relocate it to, and an `add` card the deck does not already run.
    """
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    "scripts"))
    import deck as dk
    variant = next(((d["core"], d["id"]) for d in dk.discover_decks() if d["variant"]), None)
    assert variant, "no parent/variant pair on the roster — `diff` has nothing to compare"
    best = None
    for d in dk.roster_decks():
        meta, cards = dk.parse_deck_file(d["path"])
        if (meta.get("format") or "").strip().lower() != "standard":
            continue
        heads, under = [], {}       # header text in file order; header -> [card names]
        cur = None
        with open(d["path"], encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.rstrip("\n")
                if ln.startswith("# ") and not ln.startswith("#:"):
                    cur = ln[2:].strip()
                    heads.append(cur)
                elif cur and ln.strip() and not ln.startswith("#"):
                    m = dk.CARD_LINE_RE.match(ln.strip()) if hasattr(dk, "CARD_LINE_RE") else None
                    name = m.group(2).strip() if m else ln.strip().split(" (")[0][2:].strip()
                    if name and name.lower() not in dk.BASICS:
                        under.setdefault(cur, []).append(name)
        uniq = [h for h in heads if heads.count(h) == 1]
        pairs = [(h, under[h][0], t) for h in uniq if under.get(h)
                 for t in uniq if t != h]
        if pairs and (best is None or len(under) > best[1]):
            best = ((d["id"], pairs[0][1], pairs[0][2]), len(under))
    assert best, "no Standard roster deck with two unambiguous section headers"
    did, cut, section = best[0]
    have = {n.lower() for _q, n, _s, _c in dk.parse_deck_file(dk.find_deck(did)["path"])[1]}
    add = next((c for c in ("Negate", "Duress", "Opt", "Shock", "Cancel")
                if c.lower() not in have and dk.load_card_data().get(c.lower())), None)
    assert add, "no stock card outside the chosen deck to preview as an add"
    return did, cut, section, add, variant


_DECK, _CUT_CARD, _SECTION, _ADD_CARD, _VARIANT = _pick_deck()
_ARGS = {
    # roster-wide, no argument
    "list": [], "wildcards": [], "audit": [], "brawl": [], "rotation": [], "feedback": [],
    # one deck id
    "check": [_DECK], "arena": [_DECK], "stats": [_DECK], "mana": [_DECK],
    "consistency": [_DECK], "tribes": [_DECK], "engines": [_DECK], "targets": [_DECK],
    "suggest": [_DECK], "legal": [_DECK], "preflight": [_DECK], "quality": [_DECK],
    "history": [_DECK], "tier": [_DECK], "shape": [_DECK], "redundancy": [_DECK],
    "cuts": [_DECK], "flex": [_DECK], "text": [_DECK], "similar": [_DECK],
    # everything else takes its own shape
    "diff": list(_VARIANT),         # a REAL parent/variant pair, found on the roster
    "swap": [_DECK, "--cut", _CUT_CARD, "--add", _ADD_CARD],            # dry run
    "apply-flex": [_DECK, "1"],                                         # dry run
    "verify": [_DECK],
    "sync": _STDIN,                 # fed a real export by the command_runs fixture
    "suggest-homes": [_ADD_CARD],
    "resolve": [_ADD_CARD],
    "screen": [_DECK, _ADD_CARD],
    # dry run against a card + header that exist in _DECK; `move` is the standalone
    # G-77 relocation and must never write a recommendations row
    "move": [_DECK, _CUT_CARD, "--section", _SECTION],
}


@pytest.fixture(scope="module")
def command_runs(subcommands):
    """Every subcommand actually executed, once, shared across the tests below."""
    rc, export = _run([os.path.join("scripts", "deck.py"), "arena", _DECK])
    assert rc == 0 and "Deck" in export, export[:200]
    plain = [(c, [os.path.join("scripts", "deck.py"), c, *_ARGS[c]])
             for c in subcommands if c in _ARGS and _ARGS[c] is not _STDIN]
    out = _run_all(plain)
    for c in (c for c in subcommands if _ARGS.get(c) is _STDIN):
        out[c] = _run([os.path.join("scripts", "deck.py"), c], stdin=export)
    return out


class TestVerdictSurfacesPrintEvidence:
    """G-52 wiring, pinned at the CLI because both regressions were CALLER-shaped:
    `screen`'s oracle text sat behind an opt-in `--full` no skill ever passed (five
    68b cards mis-graded from bare labels in one session), and `card.py`'s complete
    output was truncated by the grader's own `sed` pipe — invisible, because nothing
    marked the end."""

    def test_screen_prints_oracle_text_by_default(self, command_runs):
        rc, out = command_runs["screen"]
        assert rc == 0
        assert "Counter target noncreature spell" in out, \
            "screen must print the candidate's text"

    def test_screen_no_text_suppresses_it(self):
        rc, out = _run([os.path.join("scripts", "deck.py"), "screen", _DECK,
                        "Negate", "--no-text"])
        assert rc == 0 and "Counter target noncreature spell" not in out

    def test_card_py_ends_with_the_end_marker(self):
        rc, out = _run([os.path.join("scripts", "card.py"), "Negate"])
        assert rc == 0
        last = out.rstrip().splitlines()[-1]
        assert last.startswith("━━ end · "), (
            "the closing bar is the truncation tell (G-01); it must be the LAST line")

    def test_move_writes_no_recommendations_row(self, command_runs):
        """`move` in _ARGS is a dry run; the write-path no-ledger property is pinned
        in test_deck.py::TestCmdMove — here just prove the dry run says so."""
        rc, out = command_runs["move"]
        assert rc == 0 and "dry run" in out


class TestSubcommandsActuallyRun:
    def test_every_subcommand_is_classified(self, subcommands):
        """A new subcommand must be given a real invocation here, not silently skipped —
        otherwise this whole layer quietly stops covering it, which is the failure mode
        it exists to prevent."""
        missing = [c for c in subcommands if c not in _ARGS]
        assert not missing, (
            "these subcommands have no invocation in _ARGS, so nothing runs them:\n  "
            + ", ".join(missing))

    def test_no_subcommand_raises(self, command_runs):
        crashed = {c: out for c, (_rc, out) in command_runs.items() if TRACEBACK in out}
        assert not crashed, "\n".join(
            f"  {c}: {out.strip().splitlines()[-1]}" for c, out in crashed.items())

    def test_every_subcommand_exits_cleanly(self, command_runs):
        """Exit 0, or the documented non-zero of a command that REPORTS a problem.
        `preflight` returns non-zero when a deck is not READY and `legal`/`check` do the
        same, which is a finding about the deck, not about the command."""
        reports_findings = {"preflight", "legal", "check", "verify"}
        bad = [f"{c}: rc={rc}" for c, (rc, _o) in sorted(command_runs.items())
               if rc != 0 and c not in reports_findings]
        assert not bad, "\n".join(bad)

    def test_every_subcommand_produces_output(self, command_runs):
        """The contract no other gate checks. A command that silently prints nothing
        looks identical to a healthy one everywhere else in this repo."""
        silent = [c for c, (_rc, out) in sorted(command_runs.items())
                  if len(out.strip()) < 20]
        assert not silent, f"these subcommands printed (almost) nothing: {silent}"


class TestTunePlanOutputContract:
    """The specific render-time layer B1's bug lived in. `tier --to` prints a plan and
    then a PROJECTION of the resulting floor; both are assembled in `cmd_tier`, and if
    the pairing is wrong the projection dutifully reports the worse number instead of the
    plan being better."""

    def test_a_plan_never_cuts_a_card_feeding_the_axis_it_adds(self):
        """Roster-wide. Before the fix, 3 of the 11 decks with an assembled plan paired an
        interaction add with an interaction cut. A ⚠ on the SAME axis being added means
        the plan cancelled itself; a cross-axis ⚠ is a legitimate trade and allowed."""
        rc, out = _run([os.path.join("scripts", "deck.py"), "tier", _DECK, "--to", "A"])
        assert rc == 0, out
        for line in out.splitlines():
            if "→" in line and "(interaction" in line:
                assert "cut feeds interaction" not in line, line
            if "→" in line and "(card advantage" in line:
                assert "cut feeds card advantage" not in line, line

    def test_the_plan_reaches_the_floor_it_claims(self):
        """A plan that CLAIMS to close the gap must actually close it. Before the fix a
        deck one interaction from the A floor printed 'still short of A' having proposed a
        self-cancelling swap — the user-visible symptom.

        The deck is CHOSEN, not hardcoded (BS8-24): the old form asserted deck 43 reaches
        the A floor, which is a fact about one deck's current list and would go red on a
        legitimate tune. Here any roster deck that assembles a plan is a valid subject,
        and the property is the tool's own consistency."""
        import deck as dk
        checked = 0
        for d in dk.roster_decks():
            vec = dk.deck_quality_vector(d)
            band = dk.tier_band(vec)
            target = {"B": "A", "C": "B", "D": "C"}.get(band)
            if not target:
                continue
            rc, out = _run([os.path.join("scripts", "deck.py"), "tier", d["id"],
                            "--to", target])
            assert rc == 0, out
            if "Assembled tune plan" not in out:
                continue
            checked += 1
            if f"meets {target} floor" in out:
                assert "still short" not in out, (d["id"], out[-600:])
                return
        assert checked, "no roster deck assembled a tune plan — the planner is unreachable"


class TestRotationTakesADeckId:
    """`rotation <id>` is the per-deck view (owned rotating cards included). The roster
    sweep still runs with no argument — `_ARGS` covers that shape."""

    def test_rotation_with_a_deck_id_lists_that_deck_only(self):
        rc, out = _run(["scripts/deck.py", "rotation", _DECK])
        assert rc == 0 and TRACEBACK not in out
        assert out.startswith(f"Deck {_DECK}:"), out[:120]
        assert "Rotation sweep" not in out

    def test_a_scratch_path_works_for_a_reader_and_not_for_a_writer(self, tmp_path):
        import deck                                   # sys.path is set by _pick_deck
        src = deck.find_deck(_DECK)["path"]
        p = tmp_path / "scratch.txt"
        p.write_text(open(src, encoding="utf-8").read(), encoding="utf-8")
        rc, out = _run(["scripts/deck.py", "stats", str(p)])
        assert rc == 0 and TRACEBACK not in out and "Deck scratch:" in out
        rc, out = _run(["scripts/deck.py", "swap", str(p), "--cut", _CUT_CARD, "--add", _ADD_CARD])
        assert rc != 0 and "No deck with id" in out
