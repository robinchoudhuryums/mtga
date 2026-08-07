"""Pin the DFC front-face gate (`scripts/check_dfc.py`), guard (4) in particular.

Guards (1)–(3) lock the primitive, the bypass shape and the loaders someone REGISTERED.
Guard (4) is the one that had no equivalent: the registry is hand-kept, and every G-63
index bug so far — `load_keywords` (BS-12), reconcile_crafts' pool map (BS-16) — was a
loader that existed, shipped, was consumed, and appeared on no list. A gate that checks
only what a list names cannot see the bug that has actually happened four times.

So the properties worth pinning are about the SCAN, not the registry: that it finds the
real builders, that it does not flag the near-misses that iterate the same rows without
keying on a name, and that dropping a registry entry actually fails. Each was
mutation-tested against the live gate.
"""
import ast
import textwrap

import check_dfc as cd


class TestLiveRepo:
    def test_the_repo_passes(self):
        assert cd.check() == []

    def test_scan_finds_the_known_builders(self):
        """Non-vacuity: the scan must actually be finding things. If a refactor moves
        the loaders behind a shape the scan can't see, this fails LOUD rather than
        letting guard (4) quietly pass by finding nothing at all."""
        found = {(m, f) for m, f, _fn, _ln in cd._pool_index_builders()}
        for expected in (("deck", "load_card_data"), ("deck", "load_rarities"),
                         ("deck", "load_legalities"), ("deck", "_legality_of"),
                         ("wishlist", "load_pool_index")):
            assert expected in found, f"{expected} no longer detected as a pool index"

    def test_every_found_builder_is_registered_or_allowed(self):
        registered = {(e[0], e[1]) for e in cd._ALIASED_LOADERS}
        for mod, func, fn, lineno in cd._pool_index_builders():
            assert (mod, func) in registered or (mod, func) in cd._BUILDER_ALLOW, \
                f"{fn}:{lineno} {func} builds a pool-shaped name index and is unregistered"

    def test_the_allowlist_has_no_stale_entries(self):
        """_ACCESS_ALLOW's own comment records that an allowlist entry is an ASSERTION
        about the code, and that one of them was false for a year. An entry naming a
        builder the scan no longer finds is exactly that shape."""
        found = {(m, f) for m, f, _fn, _ln in cd._pool_index_builders()}
        for entry in cd._BUILDER_ALLOW:
            assert entry in found, f"_BUILDER_ALLOW names {entry}, which the scan does not find"

    def test_registry_entries_carry_a_reason_shaped_allowlist(self):
        """Every allowlist value must be a non-trivial reason string — a bare `None`
        or `''` is the un-argued exemption the gate exists to prevent."""
        for entry, reason in cd._BUILDER_ALLOW.items():
            assert isinstance(reason, str) and len(reason) > 20, \
                f"_BUILDER_ALLOW[{entry}] needs a real reason, got {reason!r}"


def _fn(src):
    """Parse a snippet and hand back (function_node, lines) for the helpers, which take
    the enclosing file already split (see check_dfc._seg — get_source_segment re-splits
    the whole file per call and cost this scan 39 seconds)."""
    src = textwrap.dedent(src)
    tree = ast.parse(src)
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    return node, src.splitlines(keepends=True)


class TestDetectorShape:
    """The detector is a taint walk: a var bound from the `Card Name` column, then a
    dict store keyed by it. Both halves have to be right or the gate is noise."""

    def test_taints_a_direct_cardname_read(self):
        f, lines = _fn('''
            def loader():
                for r in csv.DictReader(fh):
                    name = (r.get("Card Name") or "").strip()
        ''')
        assert "name" in cd._cardname_derived(f, lines)

    def test_taint_follows_a_derived_binding(self):
        """`nl = name.lower()` is the near-universal spelling here; a detector that
        only saw the direct read would miss most real loaders."""
        f, lines = _fn('''
            def loader():
                for r in csv.DictReader(fh):
                    name = (r.get("Card Name") or "").strip()
                    nl = name.lower()
        ''')
        assert {"name", "nl"} <= cd._cardname_derived(f, lines)

    def test_does_not_taint_an_unrelated_column(self):
        f, lines = _fn('''
            def loader():
                for r in csv.DictReader(fh):
                    rarity = (r.get("Rarity") or "").strip()
        ''')
        assert cd._cardname_derived(f, lines) == set()

    def test_store_detected_for_subscript_assignment(self):
        f, lines = _fn('''
            def loader():
                idx = {}
                name = (r.get("Card Name") or "").strip()
                idx[name] = r
        ''')
        assert cd._stores_keyed_by(f, cd._cardname_derived(f, lines))

    def test_store_detected_for_setdefault(self):
        f, lines = _fn('''
            def loader():
                idx = {}
                name = (r.get("Card Name") or "").strip()
                idx.setdefault(name, set()).add(1)
        ''')
        assert cd._stores_keyed_by(f, cd._cardname_derived(f, lines))

    def test_counting_by_a_non_name_key_is_not_an_index(self):
        """The false positive the scan was tuned against: `suggest_scored` and
        `suggest_lands` iterate the very same pool rows and build `theme_w` /
        `deck_curve`. Those are not name-keyed and flagging them would make guard (4)
        cost more than it pays."""
        f, lines = _fn('''
            def scorer():
                theme_w = {}
                for r in csv.DictReader(fh):
                    name = (r.get("Card Name") or "").strip()
                    for t in tags:
                        theme_w[t] = theme_w.get(t, 0) + 1
        ''')
        keys = cd._cardname_derived(f, lines)
        assert "name" in keys                      # the read still taints
        assert not cd._stores_keyed_by(f, keys)    # but nothing is keyed by it

    def test_the_two_real_scorers_are_not_flagged(self):
        found = {(m, f) for m, f, _fn_, _ln in cd._pool_index_builders()}
        assert ("deck", "suggest_scored") not in found
        assert ("deck", "suggest_lands") not in found


class TestGateFires:
    """Mutation: the gate must FAIL when the property it guards is broken. A check
    never watched failing is not a check."""

    def test_dropping_a_registry_entry_fails_the_gate(self, monkeypatch):
        kept = tuple(e for e in cd._ALIASED_LOADERS
                     if (e[0], e[1]) != ("deck", "_legality_of"))
        monkeypatch.setattr(cd, "_ALIASED_LOADERS", kept)
        errs = cd._registry_completeness_flags()
        assert any("_legality_of" in e for e in errs)

    def test_the_message_names_the_fix(self, monkeypatch):
        """A gate that fails without saying what to do gets suppressed, not fixed."""
        kept = tuple(e for e in cd._ALIASED_LOADERS
                     if (e[0], e[1]) != ("deck", "load_rarities"))
        monkeypatch.setattr(cd, "_ALIASED_LOADERS", kept)
        msg = "\n".join(cd._registry_completeness_flags())
        assert "alias_front" in msg and "_ALIASED_LOADERS" in msg

    def test_an_allowlisted_builder_is_exempt(self, monkeypatch):
        kept = tuple(e for e in cd._ALIASED_LOADERS
                     if (e[0], e[1]) != ("deck", "_legality_of"))
        monkeypatch.setattr(cd, "_ALIASED_LOADERS", kept)
        monkeypatch.setattr(cd, "_BUILDER_ALLOW",
                            {("deck", "_legality_of"): "exempt for this test only"})
        assert cd._registry_completeness_flags() == []

    def test_an_args_factory_entry_is_actually_invoked(self):
        """`_legality_of` is the only entry needing arguments, so a regression that
        ignored args_factory would call it wrong and be reported as a broken loader —
        not silently skipped. Assert the entry runs clean on the live repo."""
        entry = next(e for e in cd._ALIASED_LOADERS if e[1] == "_legality_of")
        assert len(entry) == 4 and callable(entry[3])
        assert not [e for e in cd._index_alias_flags() if "_legality_of" in e]


class TestScanSkips:
    def test_the_primitive_and_the_gate_are_out_of_scope(self):
        """lib.py owns alias_front and check_dfc.py reads the pool to build its own
        fixture; scanning either would flag the mechanism as its own violation."""
        assert {"lib.py", "check_dfc.py"} <= cd._BUILDER_SCAN_SKIP
        files = {fn for _m, _f, fn, _ln in cd._pool_index_builders()}
        assert not any(f.startswith("check_") for f in files)
