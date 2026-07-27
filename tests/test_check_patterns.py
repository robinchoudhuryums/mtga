"""Unit tests for the dead-pattern gate.

The gate exists because this project's signature bug is a regex that COMPILES
FINE and matches nothing. These tests prove it fires on both historical shapes,
and — just as important — that it does NOT fire on a narrow-but-working pattern,
since a gate that cries wolf gets ignored."""
import re

import check_patterns


class TestFormatLeak:
    """A bare {m,n} quantifier inside an f-string is a REPLACEMENT FIELD, so it
    compiles to the literal text `(m, n)`. This is the `{0,2}` bug that cost 46
    decks their interaction count, and it needs no corpus to detect."""

    def test_tuple_repr_is_caught(self):
        # Built the way the bug was: an f-string whose {0,2} is read as a
        # replacement field holding the tuple (0, 2), not as a quantifier.
        span = (0, 2)
        leaked = f"target (?:[a-z-]+ ){span}?creature"
        assert leaked == "target (?:[a-z-]+ )(0, 2)?creature"
        assert check_patterns._TUPLE_LEAK_RE.search(leaked)

    def test_a_real_quantifier_is_not_flagged(self):
        assert not check_patterns._TUPLE_LEAK_RE.search(
            r"target (?:[a-z-]+ ){0,2}?creature")

    def test_ordinary_alternation_is_not_flagged(self):
        assert not check_patterns._TUPLE_LEAK_RE.search(
            r"deals? \d+ damage to (?:any target|target creature)")


class TestLiveCorpus:
    """Every card-text pattern must match at least one card in the Arena pool. One
    hit is the bar on purpose: several real patterns are genuinely narrow (the Aura
    library-tuck matches exactly one card in 15.8k), so anything stricter would
    report a working pattern as dead."""

    def test_the_real_gate_passes(self):
        assert check_patterns.check() == []

    def test_every_group_declares_a_corpus_form(self):
        # Feeding a pattern the wrong text form is the same class of mistake the
        # gate exists to catch — the case-sensitive tribal-payoff scan reads
        # ORIGINAL-case text and reported as dead against a lowercased corpus.
        # "window" joined the set with F-04: a `$`-anchored pattern run against a
        # short slice of a card's text matches 0 whole texts BY CONSTRUCTION.
        for label, pat, case in check_patterns._pattern_groups():
            assert case in ("norm", "raw", "window"), label
            assert isinstance(pat, re.Pattern), label

    def test_window_patterns_are_exempt_from_the_corpus_check(self):
        """`_POWER_SCOPE_*` are `$`-anchored and run against text[start-25:start].
        Registering them as whole-text patterns would fail the build on two healthy
        regexes — the exact false-positive this gate must not produce."""
        forms = check_patterns._pool_texts()
        windowed = [(l, p) for l, p, c in check_patterns._pattern_groups()
                    if c == "window"]
        assert windowed, "the window case should have at least one member"
        for label, pat in windowed:
            # Zero whole-text hits is CORRECT for these...
            assert not any(pat.search(t) for t in forms["norm"]), label
        # ...and yet the gate is clean, because the corpus check skips them.
        assert check_patterns.check() == []


class TestCompleteness:
    """The gate's coverage was a hand-maintained list, and the list fell 13 patterns
    behind the code — including all of `lib.structural_distinctiveness`, whose failure
    mode is invisible (`card_distinctiveness` takes max(), so a dead structural
    pattern silently collapses to the tag score). A hand-kept registry grows holes;
    this makes a new pattern fail the build until it is classified."""

    def test_an_unregistered_pattern_is_reported(self, monkeypatch):
        import deck
        monkeypatch.setattr(deck, "_XX_NEW_CUE_RE",
                            re.compile(r"whenever you cast a spell"), raising=False)
        errors = check_patterns.check()
        assert any("_XX_NEW_CUE_RE" in e for e in errors)

    def test_structural_distinctiveness_is_covered(self):
        """The specific 5-pattern hole F-04 found. `max(tag, structural)` means a dead
        pattern here changes no visible number, so only this gate would catch it."""
        import lib
        registered = {id(p) for _l, p, _c in check_patterns._pattern_groups()}
        for name in ("_STRUCT_NONETB_TRIGGER_RE", "_STRUCT_ACTIVATED_RE",
                     "_STRUCT_RULEBEND_RE", "_STRUCT_MODAL_RE", "_STRUCT_REMINDER_RE"):
            assert id(getattr(lib, name)) in registered, name

    def test_doubler_axes_are_covered(self):
        import deck
        registered = {id(p) for _l, p, _c in check_patterns._pattern_groups()}
        for axis, pats in deck._DOUBLER_AXES.items():
            for p in pats:
                assert id(p) in registered, axis
        assert id(deck._DOUBLER_POWER_RE) in registered

    def test_every_exclusion_names_a_real_attribute(self):
        """A stale exclusion is a hole that looks like a decision."""
        import deck, lib, tag_synergies  # noqa: F401
        mods = {m.__name__: m for m in check_patterns._SCANNED_MODULES}
        for (mod_name, attr), reason in check_patterns._EXCLUDED.items():
            assert mod_name in mods, mod_name
            assert hasattr(mods[mod_name], attr), f"{mod_name}.{attr}"
            assert reason.strip(), f"{mod_name}.{attr} needs a reason"

    def test_pool_supplies_both_text_forms(self):
        forms = check_patterns._pool_texts()
        assert len(forms["norm"]) == len(forms["raw"]) > 1000
        assert any(t != t.lower() for t in forms["raw"])
        assert all(t == t.lower() for t in forms["norm"])

    def test_a_dead_pattern_would_be_reported(self):
        """The historical bounce bug: `(?:owner|their) hand` requires the literal
        text 'owner hand', but Magic writes 'to its owner's hand'."""
        forms = check_patterns._pool_texts()
        broken = re.compile(r"return target creature.{0,40}?(?:owner|their) hand")
        assert not any(broken.search(t) for t in forms["norm"])
        # ...and the fixed spelling does match.
        fixed = re.compile(r"return target creature.{0,60}?(?:owner'?s?|their) hand")
        assert any(fixed.search(t) for t in forms["norm"])
