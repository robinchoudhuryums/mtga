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
        for label, pat, case in check_patterns._pattern_groups():
            assert case in ("norm", "raw"), label
            assert isinstance(pat, re.Pattern), label

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
