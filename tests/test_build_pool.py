"""Pin `build_pool.py`'s freshness skip.

This step was 99% of `make refresh` — measured 222.5s of a 224.3s run, 91 paginated pages
at ~2.4s each, against 1.8s to derive every row. So the only lever is not fetching.

Skipping is CORRECT, not just fast: card-pool.csv is the whole Arena card pool and is
INDEPENDENT of what you own, so the motivating case (`make refresh` after an ingest, which
changes the LIBRARY) cannot change it. What genuinely goes stale is `Legalities` (rotation,
bans, Alchemy rebalances) and the arrival of a new set — hence a time WINDOW rather than a
blanket reuse, plus `--refetch`.

The query has to match too. `--all` and the Standard-only default produce different files,
and reusing a Standard-scoped pool for an `--all` request would freeze the wrong scope —
the shrink guard catches a shrink but cannot see that the file answers a different question.
"""
import csv
import datetime
import os

import build_pool
import pytest


def _pool(path, n=100):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=build_pool.POOL_HEADER)
        w.writeheader()
        for i in range(n):
            w.writerow({k: "" for k in build_pool.POOL_HEADER}
                       | {"Card Name": f"Card {i}"})


def _stamp(path, days_ago, query):
    d = (datetime.date.today() - datetime.timedelta(days=days_ago)).isoformat()
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(d + "\n" + (query + "\n" if query is not None else ""))


@pytest.fixture
def env(tmp_path, monkeypatch):
    out = tmp_path / "card-pool.csv"
    stamp = tmp_path / "card-pool.build"
    _pool(out)
    monkeypatch.setattr(build_pool, "POOL_PATH", str(out))
    monkeypatch.setattr(build_pool, "POOL_BUILD_STAMP", str(stamp))
    calls = []
    monkeypatch.setattr(build_pool, "fetch_all",
                        lambda q: calls.append(q) or [])
    return {"out": out, "stamp": stamp, "calls": calls, "mp": monkeypatch}


def _run(env, *extra):
    env["mp"].setattr("sys.argv",
                      ["build_pool.py", "--all", "--out", str(env["out"]), *extra])
    return build_pool.main()


class TestReadStamp:
    def test_a_missing_stamp_yields_nothing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(build_pool, "POOL_BUILD_STAMP", str(tmp_path / "absent"))
        assert build_pool.read_stamp() == (None, None, None)

    def test_a_legacy_date_only_stamp_has_no_query(self, tmp_path, monkeypatch):
        p = tmp_path / "s"
        p.write_text("2026-07-01\n")
        monkeypatch.setattr(build_pool, "POOL_BUILD_STAMP", str(p))
        assert build_pool.read_stamp() == ("2026-07-01", None, None)

    def test_a_two_line_stamp_yields_date_and_query(self, tmp_path, monkeypatch):
        """A pre-BS2-23 stamp has no tag fingerprint — it must read as UNKNOWN (None),
        which the freshness check treats as "cannot tell, do not force a rebuild",
        rather than as a mismatch that rebuilds the 15.9k-card pool on every run."""
        p = tmp_path / "s"
        p.write_text("2026-07-01\ngame:arena\n")
        monkeypatch.setattr(build_pool, "POOL_BUILD_STAMP", str(p))
        assert build_pool.read_stamp() == ("2026-07-01", "game:arena", None)

    def test_a_three_line_stamp_yields_the_tag_fingerprint(self, tmp_path, monkeypatch):
        """BS2-23: the third line records tag_synergies.py's content hash, so a
        tag-pattern edit defeats the freshness reuse — K-10 mandates
        `build_pool.py --all` after one, and the reuse made it a silent no-op."""
        p = tmp_path / "s"
        p.write_text("2026-07-01\ngame:arena\nabc123def456\n")
        monkeypatch.setattr(build_pool, "POOL_BUILD_STAMP", str(p))
        assert build_pool.read_stamp() == ("2026-07-01", "game:arena", "abc123def456")

    def test_the_fingerprint_is_content_not_mtime(self, monkeypatch):
        """Stable across calls, and it changes when the tagger's BYTES change. mtime
        would force a full rebuild after every fresh clone, since git stamps all
        files at checkout time in arbitrary order (the F-04 content-not-mtime rule)."""
        a = build_pool.tagger_fingerprint()
        assert a and a == build_pool.tagger_fingerprint()

    def test_age_is_computed_from_the_date(self):
        y = (datetime.date.today() - datetime.timedelta(days=3)).isoformat()
        assert build_pool.stamp_age_days(y) == 3
        assert build_pool.stamp_age_days(None) is None
        assert build_pool.stamp_age_days("not-a-date") is None


class TestFreshnessSkip:
    def test_a_fresh_pool_for_the_same_query_is_reused(self, env):
        _stamp(env["stamp"], 0, "game:arena")
        assert _run(env) == 0
        assert env["calls"] == [], "a fresh pool must not be re-fetched"

    def test_a_stale_pool_is_rebuilt(self, env):
        _stamp(env["stamp"], build_pool.FRESH_DAYS + 1, "game:arena")
        _run(env)
        assert env["calls"] == ["game:arena"]

    def test_a_DIFFERENT_query_is_never_reused(self, env):
        """Reusing a Standard-scoped pool for an --all request would freeze the wrong
        scope, and the shrink guard cannot see that."""
        _stamp(env["stamp"], 0, "game:arena legal:standard")
        _run(env)
        assert env["calls"] == ["game:arena"]

    def test_a_legacy_stamp_with_no_query_is_never_reused(self, env):
        """Without a recorded query the scope cannot be proven, so rebuild."""
        _stamp(env["stamp"], 0, None)
        _run(env)
        assert env["calls"] == ["game:arena"]

    def test_refetch_overrides_freshness(self, env):
        _stamp(env["stamp"], 0, "game:arena")
        _run(env, "--refetch")
        assert env["calls"] == ["game:arena"]

    def test_max_age_zero_always_rebuilds(self, env):
        _stamp(env["stamp"], 0, "game:arena")
        _run(env, "--max-age", "0")
        assert env["calls"] == ["game:arena"]

    def test_a_missing_pool_file_is_rebuilt(self, env):
        _stamp(env["stamp"], 0, "game:arena")
        os.unlink(env["out"])
        _run(env)
        assert env["calls"] == ["game:arena"]

    def test_the_skip_leaves_the_file_untouched(self, env):
        _stamp(env["stamp"], 0, "game:arena")
        before = os.path.getmtime(env["out"])
        assert _run(env) == 0
        assert os.path.getmtime(env["out"]) == before


class TestStampContract:
    """The sidecar gained a second line. `deck.pool_staleness_days` reads `[:10]` of the
    stripped file, so the DATE must stay first — this is a cross-module contract."""

    def test_deck_still_reads_the_age_from_a_two_line_stamp(self, tmp_path, monkeypatch):
        import deck
        p = tmp_path / "card-pool.build"
        d = (datetime.date.today() - datetime.timedelta(days=5)).isoformat()
        p.write_text(d + "\ngame:arena\n")
        monkeypatch.setattr(deck, "POOL_BUILD_STAMP", str(p))
        assert deck.pool_staleness_days() == 5

    def test_the_stamp_build_pool_ACTUALLY_WRITES_is_readable_by_deck(self, env):
        """Hand-writing the stamp proves nothing about the WRITE ORDER. Verified: with
        the two lines swapped — query first, date second — every other test here still
        passed while `deck.pool_staleness_days` returned None. A contract test has to
        consume the real producer's output."""
        import deck
        env["mp"].setattr(
            build_pool, "fetch_all",
            lambda q: [{"name": f"C{i}", "type_line": "Creature", "oracle_text": "",
                        "set": "tst", "collector_number": str(i), "rarity": "common",
                        "legalities": {}, "released_at": "2026-01-01", "cmc": 1,
                        "colors": [], "keywords": []} for i in range(500)])
        env["mp"].setattr(build_pool, "POOL_PATH", str(env["out"]))
        assert _run(env) == 0
        env["mp"].setattr(deck, "POOL_BUILD_STAMP", str(env["stamp"]))
        assert deck.pool_staleness_days() == 0, \
            "build_pool must write the DATE on line 1 — deck reads stamp[:10]"
        assert build_pool.read_stamp()[1] == "game:arena"

    def test_the_live_stamp_is_readable_by_both(self):
        """Whatever shape the committed stamp is in, BOTH readers must cope.

        Deliberately does NOT require a query line: a stamp written before this change
        is date-only, and that is a legitimate state the freshness check handles by
        rebuilding. An earlier draft asserted `date and query` and failed the moment the
        committed date-only stamp was restored — coupling the suite to a transient data
        state rather than to a contract."""
        import deck
        if not os.path.exists(deck.POOL_BUILD_STAMP):
            pytest.skip("no pool stamp in this checkout")
        assert deck.pool_staleness_days() is not None
        date, query, _tags = build_pool.read_stamp()
        assert date, "the date must always be readable — deck reads stamp[:10]"
        assert query is None or isinstance(query, str)
