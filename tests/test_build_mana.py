"""Pin `build_mana.py`'s INCREMENTAL rebuild.

`make refresh` cost ~10 minutes whether you had ingested four cards or rebuilt the world,
because this step re-priced all ~15.9k pool cards against Scryfall's rate limit every run.
A printed mana cost does not change, so the fetch is now scoped to names that are NEW or
still unresolved, with `--refetch` for a deliberate full rebuild.

The rebuild ORDER is untouched and there is no second recipe — the Makefile step is still
`build_mana.py --pool`, it simply stops doing work it already did. A "quick refresh"
target would have been the obvious alternative and is exactly what CLAUDE.md forbids.

These tests cover the paths a live run cannot: `--refetch`, the shrink guard, a Scryfall
outage, and the Mana Value rendering bug the reuse path exposed.
"""
import csv
import io
import os

import build_mana
import pytest


HEADER = ["Card Name", "Mana Cost", "Mana Value", "Keywords"]


def _write_csv(path, rows, header=HEADER):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def _rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture
def env(tmp_path, monkeypatch):
    """A synthetic library + pool + output, with `fetch` recorded rather than called."""
    lib = tmp_path / "lib.csv"
    _write_csv(lib, [["Alpha", "", "", "", "", "", "", ""]],
               header=["Card Name", "Set Code", "Collector #", "Quantity Owned",
                       "Type", "Card Text", "Color(s)", "Synergies"])
    pool = tmp_path / "pool.csv"
    _write_csv(pool, [["Beta"], ["Gamma"]], header=["Card Name"])
    out = tmp_path / "mana.csv"
    monkeypatch.setattr(build_mana, "DEFAULT_CSV", str(lib))
    monkeypatch.setattr(build_mana, "POOL_CSV", str(pool))
    calls = []

    def fake_fetch(names):
        calls.append(list(names))
        return {n.lower(): (f"{{{n[0]}}}", 1.0, "Flying") for n in names}

    monkeypatch.setattr(build_mana, "fetch", fake_fetch)
    return {"out": out, "calls": calls, "monkeypatch": monkeypatch, "tmp": tmp_path}


def _run(env, *extra):
    env["monkeypatch"].setattr(
        "sys.argv", ["build_mana.py", "--pool", "--out", str(env["out"]), *extra])
    return build_mana.main()


class TestLoadExisting:
    """The resolved/unresolved predicate is the whole basis of reuse."""

    def test_a_land_with_a_blank_cost_is_RESOLVED(self, tmp_path):
        """673 pool lands have a blank Mana Cost and a real Mana Value of 0. Keying
        'resolved' off the COST would re-fetch every one of them forever."""
        p = tmp_path / "m.csv"
        _write_csv(p, [["Wastes", "", "0", ""]])
        assert build_mana.load_existing(str(p)) == {"wastes": ("", "0", "")}

    def test_an_all_blank_row_is_UNRESOLVED_and_retried(self, tmp_path):
        p = tmp_path / "m.csv"
        _write_csv(p, [["Armed // Dangerous", "", "", ""]])
        assert build_mana.load_existing(str(p)) == {}

    def test_it_keys_the_exact_name_only_not_the_dfc_front_face(self, tmp_path):
        """`_store` indexes a FETCHED card under both names; reuse deliberately does not.
        Reuse must never answer for a name it was not written for — a wrong cost that
        persists across runs is worse than a redundant fetch."""
        p = tmp_path / "m.csv"
        _write_csv(p, [["Life // Death", "{B}", "1", ""]])
        got = build_mana.load_existing(str(p))
        assert "life // death" in got
        assert "life" not in got

    def test_a_missing_file_is_empty_not_an_error(self, tmp_path):
        assert build_mana.load_existing(str(tmp_path / "nope.csv")) == {}


class TestIncrementalFetch:
    def test_a_first_run_fetches_everything(self, env):
        assert _run(env) == 0
        assert sorted(env["calls"][0]) == ["Alpha", "Beta", "Gamma"]

    def test_a_second_run_fetches_nothing(self, env):
        _run(env)
        env["calls"].clear()
        assert _run(env) == 0
        assert env["calls"] == [], "an unchanged refresh must not call Scryfall at all"

    def test_only_a_NEW_name_is_fetched(self, env):
        _run(env)
        env["calls"].clear()
        with open(env["tmp"] / "pool.csv", "a", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow(["Delta"])
        assert _run(env) == 0
        assert env["calls"] == [["Delta"]]

    def test_an_unresolved_row_is_retried(self, env):
        _write_csv(env["out"], [["Alpha", "{A}", "1", ""],
                                ["Beta", "", "", ""],        # unresolved
                                ["Gamma", "{G}", "1", ""]])
        assert _run(env) == 0
        assert env["calls"] == [["Beta"]]

    def test_refetch_rebuilds_everything(self, env):
        _run(env)
        env["calls"].clear()
        assert _run(env, "--refetch") == 0
        assert sorted(env["calls"][0]) == ["Alpha", "Beta", "Gamma"]


class TestManaValueRendering:
    """The bug the reuse path exposed. Scryfall's `cmc` is a FLOAT; a reused row carries
    the STRING already in the file. The original `int(mv) if isinstance(mv, (int, float))
    else ""` blanked anything non-numeric — which with reuse would have wiped the Mana
    Value of every row it reused, i.e. the whole file on the first incremental run."""

    def test_a_reused_string_mana_value_survives(self, env):
        _write_csv(env["out"], [["Alpha", "", "0", ""],       # a land
                                ["Beta", "{B}", "3", "Flying"],
                                ["Gamma", "{G}", "2", ""]])
        assert _run(env) == 0
        by = {r["Card Name"]: r for r in _rows(env["out"])}
        assert by["Alpha"]["Mana Value"] == "0"
        assert by["Beta"]["Mana Value"] == "3"
        assert by["Beta"]["Keywords"] == "Flying"

    def test_a_fetched_float_renders_as_an_int(self, env):
        assert _run(env) == 0
        assert all(r["Mana Value"] == "1" for r in _rows(env["out"]))

    def test_an_unresolved_name_stays_blank(self, env, monkeypatch):
        monkeypatch.setattr(build_mana, "fetch", lambda names: {})
        assert _run(env) == 0
        assert all(r["Mana Value"] == "" and r["Mana Cost"] == ""
                   for r in _rows(env["out"]))


class TestNoOpWrite:
    def test_an_unchanged_file_is_not_rewritten(self, env):
        """`atomic_write` takes a timestamped `.bak` every time. Now that a refresh is
        cheap enough to run often, rewriting an identical file would litter backups."""
        _run(env)
        before = os.path.getmtime(env["out"])
        baks_before = len(list(env["tmp"].glob("*.bak*")))
        _run(env)
        assert os.path.getmtime(env["out"]) == before
        assert len(list(env["tmp"].glob("*.bak*"))) == baks_before

    def test_a_changed_file_IS_rewritten(self, env):
        _run(env)
        with open(env["tmp"] / "pool.csv", "a", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow(["Delta"])
        assert _run(env) == 0
        assert "Delta" in {r["Card Name"] for r in _rows(env["out"])}


class TestGuardsStillHold:
    def test_the_shrink_guard_still_refuses(self, env, monkeypatch):
        """A pool-scoped file plus a library-only run silently discarded ~14k rows once.
        Incremental reuse must not weaken that."""
        _write_csv(env["out"], [[f"Card {i}", "{W}", "1", ""] for i in range(50)])
        monkeypatch.setattr("sys.argv",
                            ["build_mana.py", "--out", str(env["out"])])  # no --pool
        assert build_mana.main() == 1
        assert len(_rows(env["out"])) == 50, "the file must be left untouched"

    def test_a_scryfall_outage_leaves_the_file_unchanged(self, env, monkeypatch):
        from scryfall import ScryfallUnavailable
        _write_csv(env["out"], [["Alpha", "{A}", "1", ""]])
        before = open(env["out"], encoding="utf-8").read()

        def boom(names):
            raise ScryfallUnavailable("down")

        monkeypatch.setattr(build_mana, "fetch", boom)
        assert _run(env) == 1
        assert open(env["out"], encoding="utf-8").read() == before


class TestModalDfcKeepsBothCosts:
    """A MODAL double-faced card is castable as EITHER face, so both costs must survive.

    Storing only face 0 lost the back half entirely — Bruce Banner read as a plain `{U}`
    one-drop with nothing recording that `{2}{R}{R}{G}{G}` The Incredible Hulk is castable
    from the same card in hand. That produced a wrong answer in chat. 49 rows were affected.
    A TRANSFORM DFC is the control case: its back face is reached by transforming, never by
    paying, so it must keep exactly ONE cost.
    """

    def test_modal_dfc_joins_both_faces_front_first(self):
        card = {"mana_cost": None,
                "card_faces": [{"mana_cost": "{U}"}, {"mana_cost": "{2}{R}{R}{G}{G}"}]}
        assert build_mana._castable_cost(card) == "{U} // {2}{R}{R}{G}{G}"

    def test_transform_dfc_keeps_one_cost(self):
        card = {"mana_cost": None,
                "card_faces": [{"mana_cost": "{3}{W}{W}"}, {"mana_cost": ""}]}
        assert build_mana._castable_cost(card) == "{3}{W}{W}"

    def test_split_card_uses_scryfalls_own_joined_cost(self):
        assert build_mana._castable_cost({"mana_cost": "{U} // {4}{U}"}) == "{U} // {4}{U}"

    def test_a_land_has_no_cost(self):
        assert build_mana._castable_cost({"mana_cost": "", "card_faces": []}) == ""
        assert build_mana._castable_cost({}) == ""

    def test_the_front_face_is_still_the_head_of_the_string(self):
        """`lib.front_face_cost` takes the head, and every curve / pip / castability read
        depends on that being the face you cast (G-02)."""
        from lib import front_face_cost
        card = {"mana_cost": None,
                "card_faces": [{"mana_cost": "{1}{B}"}, {"mana_cost": "{5}{B}{R}"}]}
        assert front_face_cost(build_mana._castable_cost(card)) == "{1}{B}"


class TestFrontFaceRetryIsBatched:
    """The retry for names /cards/collection won't match by FULL name is a batch, not a
    GET per card: on ~700 two-faced names the per-card loop tripped Scryfall's rate
    limiter and its own backoff, making a `--refetch` slower than the whole rest of the
    build. The strict "the resolved card must BE the one asked for" check is what must
    survive the rewrite — a bare front name can name a DIFFERENT card."""

    def _client(self, monkeypatch, responses):
        calls = []

        def fake_post(names, **kw):
            calls.append(list(names))
            return {"data": responses.get(tuple(names), [])}

        monkeypatch.setattr(build_mana.scryfall, "post_collection", fake_post)
        monkeypatch.setattr(build_mana.time, "sleep", lambda *_: None)
        return calls

    def test_a_dfc_is_resolved_by_its_front_name(self, monkeypatch):
        card = {"name": "Bruce Banner // The Incredible Hulk", "cmc": 1, "keywords": [],
                "mana_cost": None,
                "card_faces": [{"mana_cost": "{U}"}, {"mana_cost": "{2}{R}{R}{G}{G}"}]}
        calls = self._client(monkeypatch, {
            ("Bruce Banner // The Incredible Hulk",): [],
            ("Bruce Banner",): [card],
        })
        out = build_mana.fetch(["Bruce Banner // The Incredible Hulk"])
        assert out["bruce banner // the incredible hulk"][0] == "{U} // {2}{R}{R}{G}{G}"
        assert calls == [["Bruce Banner // The Incredible Hulk"], ["Bruce Banner"]]

    def test_a_front_name_that_resolves_to_a_different_card_is_rejected(self, monkeypatch):
        """"Life" is also a card. Writing a wrong cost is worse than writing none."""
        other = {"name": "Life", "cmc": 1, "keywords": [], "mana_cost": "{G}"}
        self._client(monkeypatch, {("Life // Death",): [], ("Life",): [other]})
        out = build_mana.fetch(["Life // Death"])
        assert "life // death" not in out

    def test_the_retry_is_one_request_per_75_names(self, monkeypatch):
        names = [f"Front {i} // Back {i}" for i in range(80)]
        calls = self._client(monkeypatch, {})
        build_mana.fetch(names)
        # 2 batches for the full names, then 2 more for the front-face retry.
        assert len(calls) == 4
        assert calls[2][0] == "Front 0" and calls[3][0] == "Front 75"
