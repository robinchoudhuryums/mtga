"""Mutation tests for the canonical WRITE path — lib.atomic_write / backup_path /
latest_backup / write_rows.

`tests/test_lib.py` already asserts what the writer DOES. This file asserts that those
assertions would actually FAIL if the writer stopped doing it, which is a different
claim and the one the project's standing rule cares about: a check never watched failing
is not a check. The gate runner got that layer in BS2-29; the writer never did, and it
is the component with the most to lose — every canonical file in the repo is written
through it, and its failure mode is a truncated or silently-clobbered source of truth.

The method is deliberate. Each test states a safety property as an executable predicate,
then runs that predicate against TWO implementations: the real `lib.atomic_write` (must
pass) and a MUTANT with exactly one safety step removed (must fail). The mutants are not
hypothetical — every one of them is a bug this writer actually had, cited by name in
lib.py's own comments:

  * no temp file            → the in-place truncation audit F5 fixed
  * backup after the replace → a `.bak` holding the new content, not the old
  * no copymode             → the silent 644 → 600 mode flip (masked by git checkouts)
  * temp left behind        → `.tmp` litter beside the canonical CSVs
  * replace before fsync    → the "durably" the docstring promised and the code didn't
  * a fixed backup name     → audit F22's same-second collision
  * latest_backup by mtime  → broad-scan F-04, the revert→save→revert data loss

A mutant that the property does NOT catch is the finding: it means the property is
weaker than it reads, and the real writer could regress that way unnoticed.
"""
import csv
import os
import shutil
import stat
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import lib  # noqa: E402
import pytest  # noqa: E402


# ── the mutants ─────────────────────────────────────────────────────────────
# Each has atomic_write's signature so a property can be run against either.

def mut_no_temp(path, write_fn, *, backup=True):
    """Writes straight to the target: the pre-F5 shape. A raising write_fn has already
    truncated the file by the time the exception escapes."""
    if backup and os.path.exists(path):
        shutil.copy2(path, lib.backup_path(path))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        write_fn(fh)


def mut_backup_after_replace(path, write_fn, *, backup=True):
    """Promotes the temp first, then backs up — so the `.bak` captures the NEW
    content and the previous version is gone."""
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
        write_fn(fh)
    os.replace(tmp, path)
    if backup:
        shutil.copy2(path, lib.backup_path(path))


def mut_no_copymode(path, write_fn, *, backup=True):
    """Skips `shutil.copymode`, so the target inherits mkstemp's 0600."""
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
        write_fn(fh)
    if backup and os.path.exists(path):
        shutil.copy2(path, lib.backup_path(path))
    os.replace(tmp, path)


def mut_leaks_temp(path, write_fn, *, backup=True):
    """Has the temp file but no cleanup on failure."""
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
        write_fn(fh)          # raises → tmp stays on disk forever
    if backup and os.path.exists(path):
        shutil.copy2(path, lib.backup_path(path))
    os.replace(tmp, path)


# ── the properties ──────────────────────────────────────────────────────────

def prop_failed_write_preserves_original(writer, tmp_path):
    """A write_fn that raises must leave the previous content in place."""
    p = tmp_path / "data.csv"
    p.write_text("original\n", encoding="utf-8")

    def boom(fh):
        fh.write("partial")
        raise RuntimeError("mid-write failure")

    with pytest.raises(RuntimeError):
        writer(str(p), boom)
    return p.read_text(encoding="utf-8") == "original\n"


def prop_backup_holds_the_previous_content(writer, tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("v1\n", encoding="utf-8")
    writer(str(p), lambda fh: fh.write("v2\n"))
    baks = list(tmp_path.glob("data.csv.*.bak"))
    return len(baks) == 1 and baks[0].read_text(encoding="utf-8") == "v1\n"


def prop_mode_is_preserved(writer, tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("v1\n", encoding="utf-8")
    os.chmod(p, 0o644)
    writer(str(p), lambda fh: fh.write("v2\n"))
    return stat.S_IMODE(os.stat(p).st_mode) == 0o644


def prop_no_temp_litter_after_failure(writer, tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("original\n", encoding="utf-8")

    def boom(fh):
        raise RuntimeError("mid-write failure")

    with pytest.raises(RuntimeError):
        writer(str(p), boom)
    return not list(tmp_path.glob("*.tmp"))


class TestAtomicWriteMutants:
    """Real writer passes; each mutant fails the property that names its bug."""

    def test_real_writer_satisfies_every_property(self, tmp_path):
        for i, prop in enumerate((prop_failed_write_preserves_original,
                                  prop_backup_holds_the_previous_content,
                                  prop_mode_is_preserved,
                                  prop_no_temp_litter_after_failure)):
            d = tmp_path / f"ok{i}"
            d.mkdir()
            assert prop(lib.atomic_write, d), f"{prop.__name__} failed on the REAL writer"

    def test_writing_in_place_loses_the_original(self, tmp_path):
        assert not prop_failed_write_preserves_original(mut_no_temp, tmp_path)

    def test_backing_up_after_the_replace_captures_the_wrong_version(self, tmp_path):
        assert not prop_backup_holds_the_previous_content(mut_backup_after_replace, tmp_path)

    @pytest.mark.skipif(os.name != "posix", reason="POSIX mode bits")
    def test_dropping_copymode_flips_the_file_to_0600(self, tmp_path):
        assert not prop_mode_is_preserved(mut_no_copymode, tmp_path)

    def test_no_cleanup_leaves_a_temp_beside_the_csv(self, tmp_path):
        assert not prop_no_temp_litter_after_failure(mut_leaks_temp, tmp_path)


class TestDurabilityOrdering:
    """`fsync` before `os.replace` cannot be observed by reading the file back — a
    power cut is not simulable in a unit test — so the only honest pin is the CALL
    ORDER the docstring's "durably" rests on. Stated plainly because an interaction
    test is weaker evidence than a behavioural one: this asserts the writer still
    does the thing, not that the thing works."""

    def test_the_file_is_fsynced_before_it_is_promoted(self, tmp_path, monkeypatch):
        seen = []
        real_fsync, real_replace = os.fsync, os.replace

        def spy_fsync(fd):
            seen.append("fsync")
            return real_fsync(fd)

        def spy_replace(a, b):
            seen.append("replace")
            return real_replace(a, b)

        monkeypatch.setattr(os, "fsync", spy_fsync)
        monkeypatch.setattr(os, "replace", spy_replace)
        p = tmp_path / "data.csv"
        p.write_text("v1\n", encoding="utf-8")
        lib.atomic_write(str(p), lambda fh: fh.write("v2\n"))

        assert "replace" in seen, "the writer never promoted the temp"
        assert seen.index("fsync") < seen.index("replace"), \
            "os.replace ran before the content was flushed to disk — the temp can be " \
            "promoted empty after a power loss (the durability the docstring promises)"


class TestBackupNamingMutants:
    def test_two_writes_in_the_same_second_leave_two_backups(self, tmp_path):
        """audit F22: a second-precision name is overwritten by a same-second write,
        so the older version silently disappears."""
        p = tmp_path / "data.csv"
        p.write_text("v1\n", encoding="utf-8")
        lib.atomic_write(str(p), lambda fh: fh.write("v2\n"))
        lib.atomic_write(str(p), lambda fh: fh.write("v3\n"))
        baks = sorted(q.read_text(encoding="utf-8") for q in tmp_path.glob("data.csv.*.bak"))
        assert baks == ["v1\n", "v2\n"]

    def test_a_fixed_backup_name_would_lose_one(self, tmp_path, monkeypatch):
        """The mutant: prove the property above is doing work rather than passing
        because two writes happen to land in different microseconds anyway."""
        monkeypatch.setattr(lib, "backup_path", lambda target: f"{target}.fixed.bak")
        p = tmp_path / "data.csv"
        p.write_text("v1\n", encoding="utf-8")
        lib.atomic_write(str(p), lambda fh: fh.write("v2\n"))
        lib.atomic_write(str(p), lambda fh: fh.write("v3\n"))
        assert [q.name for q in tmp_path.glob("*.bak")] == ["data.csv.fixed.bak"]
        assert (tmp_path / "data.csv.fixed.bak").read_text(encoding="utf-8") == "v2\n"

    def test_backup_path_is_monotonic_under_a_frozen_clock(self, tmp_path):
        """Collision handling, forced: every name distinct and sorted by creation."""
        target = str(tmp_path / "x")
        names = []
        for _ in range(5):
            n = lib.backup_path(target)
            open(n, "w").close()
            names.append(n)
        assert len(set(names)) == 5
        assert lib.latest_backup(names) == names[-1]


def _mtime_latest(paths):
    """The WRONG reader lib.latest_backup exists to replace (broad-scan F-04)."""
    paths = list(paths or [])
    return max(paths, key=os.path.getmtime) if paths else None


class TestLatestBackupMutant:
    """The revert→save→revert sequence, run against both selectors. This is the one
    mutation in the file that reproduces a user-visible data loss rather than a
    durability weakness: under mtime selection the second revert restores the state
    the FIRST revert already discarded, silently re-applying the undone change."""

    def _sequence(self, selector, tmp_path):
        target = tmp_path / "lib.csv"
        target.write_text("v0\n")

        def save(v):
            shutil.copy2(target, lib.backup_path(str(target)))
            target.write_text(f"v{v}\n")

        def revert():
            baks = [str(p) for p in tmp_path.iterdir() if p.name.endswith(".bak")]
            newest = selector(baks)
            shutil.copy2(target, lib.backup_path(str(target)))
            shutil.copy2(newest, target)

        save(1)
        save(2)
        revert()
        first = target.read_text()
        save(3)
        revert()
        return first, target.read_text()

    def test_stamp_selection_restores_the_pre_save_state(self, tmp_path):
        """Both reverts land on v1: the first undoes save(2), the second undoes
        save(3) back to the state save(3) was made from — which is v1, because the
        first revert already put it there."""
        assert self._sequence(lib.latest_backup, tmp_path) == ("v1\n", "v1\n")

    def test_mtime_selection_restores_the_discarded_state(self, tmp_path):
        """The mutant must actually diverge — otherwise the stamped scheme is
        ceremony and `latest_backup` could be deleted.

        It diverges because copy2 carries the SOURCE's mtime: the backup save(3) takes
        of the reverted file inherits v1's original mtime, so it sorts BEFORE the
        backup holding v2. mtime-max therefore picks v2 — the exact state the first
        revert discarded, silently re-applying the change the user had just undone."""
        first, second = self._sequence(_mtime_latest, tmp_path)
        assert first == "v1\n"
        assert second == "v2\n", \
            "mtime selection no longer diverges from stamp selection — either copy2 " \
            "stopped preserving mtimes or the sequence no longer exercises F-04"


class TestWriteRowsSchemaGuard:
    """F-02 and its mirror: write_rows emits exactly HEADER, so pointing it at a
    derived file destroys that file's own columns. The guard is what stands between
    `tag_synergies.py card-pool.csv` and a pool with no Rarity/Legalities."""

    def _pool(self, tmp_path):
        p = tmp_path / "card-pool.csv"
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["Card Name", "Rarity", "Legalities"])
            w.writeheader()
            w.writerow({"Card Name": "Shock", "Rarity": "C", "Legalities": "standard"})
        return p

    def test_a_derived_target_is_refused(self, tmp_path):
        p = self._pool(tmp_path)
        with pytest.raises(lib.WrongSchema):
            lib.write_rows([{"Card Name": "Shock"}], str(p))

    def test_the_refusal_happens_before_any_write(self, tmp_path):
        """A guard that raises AFTER the temp is promoted is not a guard. Assert the
        file is byte-identical and no backup or temp was produced."""
        p = self._pool(tmp_path)
        before = p.read_bytes()
        with pytest.raises(lib.WrongSchema):
            lib.write_rows([{"Card Name": "Shock"}], str(p))
        assert p.read_bytes() == before
        assert not list(tmp_path.glob("*.bak")) and not list(tmp_path.glob("*.tmp"))

    def test_without_the_guard_the_derived_columns_are_destroyed(self, tmp_path, monkeypatch):
        """The mutant: disable the schema check and watch the pool become a library.
        This is the concrete damage audit F-02 recorded, made executable."""
        p = self._pool(tmp_path)
        monkeypatch.setattr(lib, "csv_schema_error", lambda path: None)
        lib.write_rows([{"Card Name": "Shock"}], str(p))
        with open(p, newline="", encoding="utf-8") as fh:
            got = next(csv.reader(fh))
        assert got == list(lib.HEADER)
        assert "Rarity" not in got and "Legalities" not in got

    def test_a_matching_header_is_written_normally(self, tmp_path):
        p = tmp_path / "card-library.csv"
        with open(p, "w", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, fieldnames=lib.HEADER).writeheader()
        lib.write_rows([{"Card Name": "Shock", "Quantity Owned": "2"}], str(p))
        with open(p, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert rows[0]["Card Name"] == "Shock" and rows[0]["Quantity Owned"] == "2"
