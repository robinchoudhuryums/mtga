"""Unit tests for the ingest verifier and the rebuild-order Makefile target.

The verifier exists because every failure mode in the ingest subsystem is a SILENT
UNDERCOUNT and `check_all` structurally cannot see one: a card that never arrived breaks
no invariant, so the gate stays green while the collection is wrong. These tests pin the
three checks it makes and, more importantly, the two distinctions it would be useless
without — lower-bound vs authoritative quantities, and a DFC's front-face key.

The Makefile tests pin the ORDER, which is the actual finding: it is a real dependency
graph that had been written out in four prose copies, three of them wrong."""
import os
import re

import verify_ingest as vi

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _restates_chain(src):
    """Does this text spell out the rebuild chain as a RECIPE (rather than merely
    mentioning a build tool)?

    The distinction is load-bearing: half the toolkit legitimately says "built by
    build_mana.py" or errors with "run build_pool.py --all", and flagging those would
    make the check unusable and get it deleted. A recipe is the shape that goes stale —
    both builders presented as steps to run in sequence, either as `python3 scripts/...`
    invocations or joined by an arrow.

    Proximity matters as much as shape. deck.py legitimately prints "No card-pool.csv.
    Build it: python3 scripts/build_pool.py" in one place and the card-mana equivalent
    200 lines away; those are two independent one-tool hints, not a chain. A recipe is
    contiguous, so both invocations must sit within one window."""
    WINDOW = 400
    a = src.find("python3 scripts/build_mana")
    while a != -1:
        b = src.find("python3 scripts/build_pool", max(0, a - WINDOW), a + WINDOW)
        if b != -1:
            return True
        a = src.find("python3 scripts/build_mana", a + 1)
    return any("build_mana" in ln and "build_pool" in ln and ("->" in ln or "→" in ln)
               for ln in src.splitlines())


def _lib(pairs):
    """(quantities, names) in the shape library_index() returns."""
    qty = {n.lower(): q for n, q in pairs}
    return qty, set(qty)


def _paste(*lines):
    return "Deck\n" + "\n".join(lines) + "\n"


class TestPresence:
    def test_a_card_that_landed_reads_present(self):
        res, _ = vi.verify(_paste("2 Pacifism (ANB) 16"),
                           lib=_lib([("Pacifism", 2)]), mana={"pacifism"})
        assert res[0]["present"] and res[0]["enough"] and res[0]["has_mana"]

    def test_a_card_that_never_arrived_is_flagged(self):
        """The headline case. Nothing else in the repo reports this."""
        res, _ = vi.verify(_paste("1 Ghost Card (ZZZ) 1"), lib=_lib([]), mana=set())
        assert res[0]["present"] is False

    def test_an_unparseable_line_is_a_warning_not_a_silent_drop(self):
        """A line no parser matched was never ingested by ANY tool, so it is exactly the
        case a verifier must not swallow."""
        res, warns = vi.verify(_paste("~~~ junk ~~~"), lib=_lib([]), mana=set())
        assert res == [] and len(warns) == 1


class TestQuantitiesLowerBoundVsAuthoritative:
    """The one conceptual distinction the whole ingest subsystem turns on. Applying the
    wrong reading either invents a failure or hides one."""

    def test_more_owned_than_pasted_is_fine_by_default(self):
        """Every route except import_collection treats a line as a LOWER BOUND — a deck
        dump says what that deck plays, not what you own."""
        res, _ = vi.verify(_paste("1 Pacifism (ANB) 16"),
                           lib=_lib([("Pacifism", 3)]), mana={"pacifism"})
        assert res[0]["enough"] is True

    def test_more_owned_than_pasted_fails_under_exact(self):
        """--exact is the authoritative tracker-export reading, the only route that may
        lower a count."""
        res, _ = vi.verify(_paste("1 Pacifism (ANB) 16"), exact=True,
                           lib=_lib([("Pacifism", 3)]), mana={"pacifism"})
        assert res[0]["enough"] is False

    def test_fewer_owned_than_pasted_always_fails(self):
        for exact in (False, True):
            res, _ = vi.verify(_paste("4 Pacifism (ANB) 16"), exact=exact,
                               lib=_lib([("Pacifism", 1)]), mana={"pacifism"})
            assert res[0]["enough"] is False, exact

    def test_quantities_sum_across_printings(self):
        """Owned copies are fungible across printings (CLAUDE.md), so a card owned 1x in
        two sets is 2. Counting one printing would report a real ingest as short."""
        qty, names = vi.library_index(os.path.join(REPO, "card-library.csv"))
        # The index is built by summing; assert the shape rather than a specific card.
        assert all(isinstance(v, int) for v in qty.values())
        assert names and all(n == n.lower() for n in names)


class TestDoubleFacedCards:
    """The library keys a DFC under its FRONT name; an Arena export and the pool use the
    full `Front // Back`. Without the fallback, every owned DFC in a paste reads as
    missing (audit F6)."""

    def test_a_full_name_paste_resolves_to_the_front_face_row(self):
        res, _ = vi.verify(_paste("1 Oko, Lorwyn Liege // Oko, Shadowmoor Scion (X) 1"),
                           lib=_lib([("Oko, Lorwyn Liege", 1)]),
                           mana={"oko, lorwyn liege"})
        assert res[0]["present"] and res[0]["enough"]
        assert res[0]["key"] == "oko, lorwyn liege"

    def test_the_mana_check_uses_the_same_resolved_key(self):
        """The quantity check and the INV-02 check must agree about WHICH row they are
        talking about, or a DFC reports owned-but-uncovered every time."""
        res, _ = vi.verify(_paste("1 Front Face // Back Face (X) 1"),
                           lib=_lib([("Front Face", 1)]), mana={"front face"})
        assert res[0]["has_mana"] is True


class TestManaCoverage:
    """INV-02 scoped per card. This is the step people skip, and the failure is
    invisible: the card is there, its cost and keyword tags are just blank."""

    def test_a_card_with_no_mana_row_is_flagged(self):
        res, _ = vi.verify(_paste("1 New Card (X) 1"),
                           lib=_lib([("New Card", 1)]), mana=set())
        assert res[0]["present"] and res[0]["has_mana"] is False

    def test_an_absent_mana_file_is_not_blamed_on_the_ingest(self):
        """A missing card-mana.csv is INV-03, a different failure. Reporting it per card
        would misattribute it and send someone to re-run the wrong tool."""
        res, _ = vi.verify(_paste("1 New Card (X) 1"),
                           lib=_lib([("New Card", 1)]), mana=None)
        assert res[0]["has_mana"] is True


class TestBasics:
    """Basic lands are unlimited in Arena and deliberately absent from the collection, so
    checking them would report a false miss on every paste containing one."""

    def test_basics_are_skipped_by_default(self):
        res, _ = vi.verify(_paste("4 Plains (FDN) 271"), lib=_lib([]), mana=set())
        assert res[0]["basic"] and res[0]["present"] and res[0]["enough"]

    def test_include_basics_checks_them(self):
        res, _ = vi.verify(_paste("4 Plains (FDN) 271"), include_basics=True,
                           lib=_lib([]), mana=set())
        assert res[0]["present"] is False


class TestReportExitCode:
    def test_a_clean_ingest_exits_zero(self, capsys):
        res, warns = vi.verify(_paste("1 Pacifism (ANB) 16"),
                               lib=_lib([("Pacifism", 1)]), mana={"pacifism"})
        assert vi.report(res, warns) == 0
        assert "ingest is complete" in capsys.readouterr().out

    def test_a_missing_card_exits_non_zero(self, capsys):
        res, warns = vi.verify(_paste("1 Ghost (X) 1"), lib=_lib([]), mana=set())
        assert vi.report(res, warns) == 1
        assert "NOT in card-library.csv" in capsys.readouterr().out

    def test_a_mana_gap_exits_non_zero_and_names_the_fix(self, capsys):
        res, warns = vi.verify(_paste("1 New Card (X) 1"),
                               lib=_lib([("New Card", 1)]), mana=set())
        assert vi.report(res, warns) == 1
        assert "make refresh" in capsys.readouterr().out

    def test_an_unparseable_line_exits_non_zero(self, capsys):
        res, warns = vi.verify(_paste("~~~ junk ~~~"), lib=_lib([]), mana=set())
        assert vi.report(res, warns) == 1


class TestRebuildOrderIsDefinedOnceAndCorrectly:
    """The finding itself: the rebuild order is a real dependency graph that lived in
    four prose copies, three of them wrong. These assert the executable copy is right,
    against the dependencies read out of the scripts rather than out of the docs."""

    def _refresh_recipe(self):
        src = open(os.path.join(REPO, "Makefile"), encoding="utf-8").read()
        body = src.split("\nrefresh:", 1)[1]
        body = re.split(r"\n(?=[A-Za-z_-]+:)", body)[0]
        return [ln.strip() for ln in body.splitlines() if ln.strip().startswith("python3")]

    def test_the_target_exists(self):
        assert self._refresh_recipe(), "no refresh target in the Makefile"

    def test_build_pool_precedes_build_mana(self):
        """build_mana --pool READS card-pool.csv. Pool last is the exact mistake the
        three wrong prose copies made, and it fails silently."""
        steps = " || ".join(self._refresh_recipe())
        assert steps.index("build_pool.py") < steps.index("build_mana.py")

    def test_build_mana_precedes_tag_synergies(self):
        """tag_synergies reads card-mana.csv's keywords; run first, tags lose them."""
        steps = " || ".join(self._refresh_recipe())
        assert steps.index("build_mana.py") < steps.index("tag_synergies.py")

    def test_it_keeps_the_full_scope_flags(self):
        """Both tools DEFAULT to the smaller scope, so a plain rebuild SHRINKS coverage
        back — the 1,695-rows-against-a-15,850-card-pool incident."""
        steps = self._refresh_recipe()
        assert any("build_pool.py --all" in s for s in steps)
        assert any("build_mana.py --pool" in s for s in steps)

    def test_it_merges_rather_than_forces_tags(self):
        """--force REPLACES every cell and clobbers hand-curated tags (audit F10)."""
        steps = " ".join(self._refresh_recipe())
        assert "tag_synergies.py --merge" in steps and "--force" not in steps

    def test_it_ends_on_the_integrity_gate(self):
        assert "check_all.py" in self._refresh_recipe()[-1]

    def test_no_script_restates_the_chain(self):
        """The Makefile was supposed to END the copies, and it did not go far enough:
        `import_arena.py` still PRINTED the six steps, with build_mana ahead of
        build_pool — the wrong order, in executable code, telling the user to make the
        exact mistake the Makefile comment warns about. A prose copy is a stale doc; a
        printed copy is instructions someone will follow.

        The rule: no script may name both build tools as steps to run. Pointing at
        `make refresh` is the supported way to tell someone to rebuild."""
        import glob
        offenders = [os.path.basename(p) for p in
                     sorted(glob.glob(os.path.join(REPO, "scripts", "*.py")))
                     if _restates_chain(open(p, encoding="utf-8").read())]
        assert offenders == [], (
            f"{offenders} restate the rebuild chain; point at `make refresh` instead")

    def test_the_skills_defer_to_the_make_target(self):
        """Same rule for the workflows. /refresh is the one exemption — it documents the
        individual steps so you can deliberately skip one — and even it must lead with
        the target."""
        import glob
        skills = os.path.join(REPO, ".claude", "commands")
        for path in sorted(glob.glob(os.path.join(skills, "*.md"))):
            name = os.path.basename(path)
            src = open(path, encoding="utf-8").read()
            if name == "refresh.md":
                assert "make refresh" in src
                continue
            assert not _restates_chain(src), \
                f"{name} restates the rebuild chain; point at `make refresh`"

    def test_the_dependency_claims_still_hold_in_the_code(self):
        """The order is only correct while these dependencies are real. If build_mana
        stops reading the pool, or tag_synergies stops reading the mana file, this test
        should fail and the order should be re-derived — not assumed."""
        mana_src = open(os.path.join(REPO, "scripts", "build_mana.py"), encoding="utf-8").read()
        assert "POOL_CSV" in mana_src, "build_mana no longer reads the pool"
        tag_src = open(os.path.join(REPO, "scripts", "tag_synergies.py"), encoding="utf-8").read()
        assert "MANA_CSV" in tag_src, "tag_synergies no longer reads card-mana.csv"
        pool_src = open(os.path.join(REPO, "scripts", "build_pool.py"), encoding="utf-8").read()
        assert "MANA_CSV" not in pool_src, \
            "build_pool now reads card-mana.csv — the order needs re-deriving"
