"""Unit tests for the workflow-coverage gate.

The gate exists because correctness gates are blind to a capability that WORKS and is
never REACHED. CLAUDE.md records the real instance: `/tune-deck` sat on the command set
it shipped with while `consistency`, `engines`, `shape`, `cuts`, `flex` and the
needs-aware `suggest --needs/--interaction/--ramp/--lands` were built around it. Every
one of those was correct, gated and documented — and unused, because the workflow never
learned they existed.

These tests pin both halves: that an unreachable command is reported, and that the
exemption registry can't rot into a list of decisions about things that are gone."""
import check_commands as cc


class TestSubcommandDiscovery:
    def test_reads_subcommands_from_the_source(self):
        """Static, so check_all stays in-process — no subprocess per gate. The CLI
        surface itself is covered by tests/test_cli.py."""
        subs = cc.deck_subcommands()
        assert len(subs) > 25
        for expected in ("audit", "stats", "cuts", "tier", "rotation", "sync"):
            assert expected in subs

    def test_runnable_scripts_excludes_libraries(self):
        scripts = cc.runnable_scripts()
        assert "deck.py" in scripts and "check_all.py" in scripts
        # lib.py and scryfall.py are imported, never run.
        assert "lib.py" not in scripts and "scryfall.py" not in scripts


class TestTheRealGatePasses:
    def test_the_repo_is_currently_covered(self):
        assert cc.check() == []

    def test_every_exemption_carries_a_reason(self):
        for key, reason in cc.INTERACTIVE_ONLY.items():
            assert str(reason).strip(), key

    def test_every_exemption_names_something_real(self):
        """A stale exemption is worse than none: it reads as a considered decision while
        covering nothing, and pre-grants a pass to any future command reusing the name."""
        subs = set(cc.deck_subcommands())
        import os
        for kind, name in cc.INTERACTIVE_ONLY:
            if kind == "deck.py":
                assert name in subs, name
            else:
                assert os.path.exists(os.path.join(cc.SCRIPTS_DIR, name)), name


class TestGateFires:
    """A gate that cannot fire is not a gate — this project's most-repeated lesson."""

    def test_a_stale_subcommand_exemption_is_reported(self, monkeypatch):
        reg = dict(cc.INTERACTIVE_ONLY)
        reg[("deck.py", "no_such_command")] = "a reason"
        monkeypatch.setattr(cc, "INTERACTIVE_ONLY", reg)
        assert any("no_such_command" in e for e in cc.check())

    def test_a_stale_script_exemption_is_reported(self, monkeypatch):
        reg = dict(cc.INTERACTIVE_ONLY)
        reg[("script", "gone.py")] = "a reason"
        monkeypatch.setattr(cc, "INTERACTIVE_ONLY", reg)
        assert any("gone.py" in e for e in cc.check())

    def test_an_unexplained_exemption_is_reported(self, monkeypatch):
        reg = dict(cc.INTERACTIVE_ONLY)
        reg[("deck.py", "list")] = "   "
        monkeypatch.setattr(cc, "INTERACTIVE_ONLY", reg)
        assert any("no reason" in e for e in cc.check())

    def test_an_unreachable_subcommand_is_reported(self, monkeypatch):
        """The headline case: a command exists, works, and no workflow drives it."""
        monkeypatch.setattr(cc, "deck_subcommands", lambda *a, **k: ["orphan_cmd"])
        assert any("orphan_cmd" in e for e in cc.check())

    def test_a_prose_mention_does_not_count_as_coverage(self, monkeypatch):
        """The first draft matched the string "deck.py <name>" anywhere in scripts/, so a
        docstring cross-reference counted as coverage — and every docstring in this repo
        cross-references commands. Five genuinely unreachable commands passed. Coverage
        now requires a real `cmd_*` call or a skill invocation."""
        monkeypatch.setattr(cc, "deck_subcommands", lambda *a, **k: ["mentioned_only"])
        monkeypatch.setattr(cc, "_script_text",
                            lambda *a, **k: '# see `deck.py mentioned_only` for detail')
        monkeypatch.setattr(cc, "_skill_text", lambda *a, **k: "")
        assert any("mentioned_only" in e for e in cc.check())

    def test_a_script_prose_mention_does_not_count_as_coverage(self, monkeypatch):
        """BS2-31: the script half accepted ANY filename mention — two of
        build_pool.py's three skill 'mentions' were warnings NOT to run it, so
        deleting the one real invocation left the gate green. Coverage now needs an
        executable shape: `python3 scripts/<fn>` in a skill or `scripts/<fn>` in the
        Makefile."""
        monkeypatch.setattr(cc, "deck_subcommands", lambda *a, **k: [])
        monkeypatch.setattr(cc, "runnable_scripts", lambda *a, **k: ["phantom_tool.py"])
        monkeypatch.setattr(cc, "_script_text", lambda *a, **k: "")
        monkeypatch.setattr(cc, "_skill_text",
                            lambda *a, **k: "never run phantom_tool.py by hand")
        assert any("phantom_tool.py" in e for e in cc.check())

    def test_a_script_invocation_does_count(self, monkeypatch):
        monkeypatch.setattr(cc, "deck_subcommands", lambda *a, **k: [])
        monkeypatch.setattr(cc, "runnable_scripts", lambda *a, **k: ["phantom_tool.py"])
        monkeypatch.setattr(cc, "_script_text", lambda *a, **k: "")
        monkeypatch.setattr(cc, "_skill_text",
                            lambda *a, **k: "run `python3 scripts/phantom_tool.py`")
        assert not any("phantom_tool.py" in e for e in cc.check())

    def test_suggest_does_not_inherit_coverage_from_suggest_homes(self, monkeypatch):
        """BS2-31's regex half: `\b` is satisfied at a hyphen, so `deck.py suggest`
        matched "deck.py suggest-homes" and an unrelated command vouched for it."""
        monkeypatch.setattr(cc, "deck_subcommands", lambda *a, **k: ["suggest"])
        monkeypatch.setattr(cc, "_script_text", lambda *a, **k: "")
        monkeypatch.setattr(cc, "_skill_text",
                            lambda *a, **k: "run `deck.py suggest-homes <card>`")
        assert any("`deck.py suggest`" in e for e in cc.check())

    def test_a_real_call_does_count_as_coverage(self, monkeypatch):
        monkeypatch.setattr(cc, "deck_subcommands", lambda *a, **k: ["viz"])
        monkeypatch.setattr(cc, "_script_text",
                            lambda *a, **k: "out = deckmod.cmd_viz(ns)")
        monkeypatch.setattr(cc, "_skill_text", lambda *a, **k: "")
        assert not any("deck.py viz" in e for e in cc.check())

    def test_a_hyphenated_subcommand_maps_to_its_underscored_function(self, monkeypatch):
        monkeypatch.setattr(cc, "deck_subcommands", lambda *a, **k: ["suggest-homes"])
        monkeypatch.setattr(cc, "_script_text",
                            lambda *a, **k: "deckmod.cmd_suggest_homes(ns)")
        monkeypatch.setattr(cc, "_skill_text", lambda *a, **k: "")
        assert not any("suggest-homes" in e for e in cc.check())


class TestRosterReviewSkillExists:
    """The gate's first run flagged audit / brawl / rotation / sync / verify — all
    roster-level. They weren't random: the per-deck loop had skills, the roster loop had
    none. /roster-review is what closed it, so it is worth pinning that the skill both
    exists and actually drives those commands."""

    def _text(self):
        import os
        p = os.path.join(cc.SKILLS_DIR, "roster-review.md")
        return open(p, encoding="utf-8").read() if os.path.exists(p) else ""

    def test_the_skill_exists(self):
        assert self._text().strip()

    def test_it_drives_the_roster_commands(self):
        t = self._text()
        for cmd in ("audit", "rotation", "brawl", "verify", "sync", "wildcards"):
            assert f"deck.py {cmd}" in t, cmd


class TestAddCardsDoesNotDuplicateTheIngest:
    """/add-cards used to catalog AND place, re-stating /ingest's reconcile recipe and
    carrying its own copy of the rebuild chain. Two definitions of cataloging is the
    hand-kept-registry failure again; it is now the fit pass alone."""

    def _text(self):
        import os
        p = os.path.join(cc.SKILLS_DIR, "add-cards.md")
        return open(p, encoding="utf-8").read() if os.path.exists(p) else ""

    def test_it_does_not_carry_its_own_catalog_step(self):
        assert "reconcile_crafts.py <export> --apply" not in self._text()

    def test_it_routes_uncatalogued_cards_to_the_front_door(self):
        assert "/ingest" in self._text()

    def test_it_keeps_the_fit_pass(self):
        """The half worth keeping: the grading rubric a bare suggest-homes run lacks."""
        t = self._text()
        assert "suggest-homes" in t
        for verdict in ("key upgrade", "sidegrade", "different-flavor"):
            assert verdict in t, verdict


class TestIngestFrontDoorExists:
    """Five tools write owned-card data and they disagree about what a quantity MEANS —
    a deck dump is a LOWER BOUND, a tracker export is AUTHORITATIVE. Picking wrong either
    undercounts the collection or overwrites it. /ingest is the router."""

    def _text(self):
        import os
        p = os.path.join(cc.SKILLS_DIR, "ingest.md")
        return open(p, encoding="utf-8").read() if os.path.exists(p) else ""

    def test_the_skill_exists(self):
        assert self._text().strip()

    def test_it_routes_to_every_ingest_tool(self):
        t = self._text()
        for script in ("import_arena.py", "import_collection.py",
                       "reconcile_crafts.py", "sheets_sync.py"):
            assert script in t, script

    def test_it_names_the_step_INV_02_depends_on(self):
        """The shared tail is the part that gets skipped: a newly added card has no
        card-mana.csv row, so INV-02 stays red until build_mana.py runs. Both ingest
        recipes omitted it once (broad-scan F-06).

        This used to assert the literal `build_mana.py --pool` in the skill. It no
        longer appears there, and that is the fix rather than a regression: the skill
        now routes to `make refresh`, because spelling the chain out here was the
        SECOND bug — three of the four prose copies had build_pool.py in the wrong
        position. So assert the guarantee (the skill explains INV-02 and sends you to
        the one definition) and let tests/test_verify_ingest.py assert that the
        definition contains the right step in the right order."""
        t = self._text()
        assert "INV-02" in t and "build_mana.py" in t
        assert "make refresh" in t

    def test_it_places_the_new_cards(self):
        """Cataloging is bookkeeping; placing the cards is the point. The fit pass lived
        in /add-cards, which meant the half that actually decides anything was the
        optional half — a user who ran /ingest got their cards catalogued and no idea
        where they go. It is conditional on cards being NEW: a full-collection import
        must not trigger a thousand fit passes."""
        t = self._text()
        assert "deck.py suggest-homes" in t
        assert "card.py" in t
        assert "key upgrade" in t and "sidegrade" in t

    def test_it_reports_decks_that_became_buildable(self):
        """An ingest is the one event that flips a deck from 'craft targets outstanding'
        to 'ready to build', and nothing else in the workflow reports it — /roster-review
        would, but nobody runs a roster survey after opening a pack."""
        assert "newly buildable" in self._text().lower()

    def test_it_verifies_the_ingest_landed(self):
        """check_all proves the library is self-consistent, not that it contains what
        you pasted — a card that never arrived breaks no invariant, so every silent
        undercount in this subsystem passes the gate. The router has to close that."""
        assert "verify_ingest.py" in self._text()

    def test_it_distinguishes_lower_bound_from_authoritative(self):
        """The one conceptual trap the router exists to prevent."""
        t = self._text().lower()
        assert "lower bound" in t and "authoritative" in t
