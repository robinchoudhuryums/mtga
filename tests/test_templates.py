"""Markup-contract tests for the Flask editor's templates.

Scope note: these are NOT browser tests. Regression Scenarios 5-8 are deliberately
"a person at a browser" because rendering and perception can't be asserted from a file,
and check_all stays zero-dependency. What CAN be asserted from the file is the part that
regressed silently: whether a control is a control at all. A `<div>` with a click handler
and no role, no tabindex and no key handler is invisible to a keyboard and to assistive
tech, and nothing in this repo would have noticed — the collection editor's six colour
pips sat that way through six deferrals of the I-01 fix.

Stdlib `html.parser` only, so this runs in the existing pytest layer with no new
dependency. The behaviour behind these attributes (Enter/Space actually toggling, the
focus ring being visible, the grid re-filtering) was verified in a real browser when the
fix landed; this pins the contract that verification rested on."""
import html.parser
import os
import re

TEMPLATES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "templates")


def _read(name):
    with open(os.path.join(TEMPLATES, name), encoding="utf-8") as fh:
        return fh.read()


class _Collector(html.parser.HTMLParser):
    """Every start tag as (tag, attrs-dict)."""

    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    handle_startendtag = handle_starttag


def _parse(name):
    p = _Collector()
    p.feed(_read(name))
    return p.tags


def _by_class(tags, cls):
    return [a for _, a in tags if cls in (a.get("class") or "").split()]


class TestColorPipsAreRealControls:
    """The I-01 fix. Before it, all six pips were bare `<div>`s: not focusable, not
    announced, and unreachable without a mouse."""

    def setup_method(self):
        self.tags = _parse("collection.html")
        self.pips = _by_class(self.tags, "pip")

    def test_all_six_pips_are_present(self):
        assert [p["data-c"] for p in self.pips] == ["W", "U", "B", "R", "G", "C"]

    def test_each_pip_is_focusable(self):
        """tabindex=0 is the whole difference between 'reachable by Tab' and 'mouse
        only' for a div."""
        for p in self.pips:
            assert p.get("tabindex") == "0", p.get("data-c")

    def test_each_pip_announces_a_role(self):
        """role="button" + aria-pressed mirrors build_dashboard.py's a11y() helper —
        the dashboard's colour chips are the same control, so the two must not drift
        into two different interaction contracts."""
        for p in self.pips:
            assert p.get("role") == "button", p.get("data-c")

    def test_each_pip_starts_unpressed(self):
        """The toggle state has to be exposed, not just painted: an assistive user has
        no access to the `.on` class or the opacity change that signals it visually."""
        for p in self.pips:
            assert p.get("aria-pressed") == "false", p.get("data-c")

    def test_each_pip_has_a_real_accessible_name(self):
        """A pip's visible text is one letter, and content wins over `title` in the
        accessible-name computation — so without aria-label a screen reader announces
        "W", not "White"."""
        want = ["White", "Blue", "Black", "Red", "Green", "Colorless"]
        assert [p.get("aria-label") for p in self.pips] == [f"Filter by {c}" for c in want]

    def test_the_group_is_named(self):
        grp = next(a for _, a in self.tags if a.get("id") == "pips")
        assert grp.get("role") == "group"
        assert grp.get("aria-label")


class TestPipKeyboardAndFocusWiring:
    """Attributes alone are a promise; these pin the code that keeps it."""

    def setup_method(self):
        self.src = _read("collection.html")

    def test_a_keydown_handler_exists(self):
        assert re.search(r"pipsEl\.addEventListener\('keydown'", self.src)

    def test_enter_and_space_both_activate(self):
        """Space is the one people forget — a real <button> responds to both."""
        block = self.src.split("addEventListener('keydown'")[1][:400]
        assert "'Enter'" in block
        assert "' '" in block or "'Spacebar'" in block

    def test_space_does_not_scroll_the_page(self):
        block = self.src.split("addEventListener('keydown'")[1][:400]
        assert "preventDefault" in block

    def test_the_key_path_routes_through_click(self):
        """Not a second copy of the toggle logic — two definitions of what a pip does
        is exactly how a keyboard path and a mouse path drift apart."""
        block = self.src.split("addEventListener('keydown'")[1][:400]
        assert "pip.click()" in block

    def test_aria_pressed_is_kept_in_sync_on_toggle(self):
        """A state attribute that is set once at render and never updated is worse than
        none: it actively reports the wrong state after the first click."""
        block = self.src.split("addEventListener('click'")[1][:500]
        assert "setAttribute('aria-pressed'" in block

    def test_there_is_a_visible_focus_ring(self):
        m = re.search(r"\.pip:focus-visible\s*\{([^}]*)\}", self.src)
        assert m, "no focus style for .pip"
        assert "outline" in m.group(1)

    def test_focus_uses_outline_not_border(self):
        """`.pip.on` marks the ACTIVE state with border-color, so reusing the border for
        focus would make focused and selected indistinguishable."""
        m = re.search(r"\.pip:focus-visible\s*\{([^}]*)\}", self.src)
        assert "border" not in m.group(1)

    def test_a_focused_pip_is_not_left_dimmed(self):
        """`.pip` sits at opacity .45; a focus ring around a dimmed circle reads as
        disabled."""
        m = re.search(r"\.pip:focus-visible\s*\{([^}]*)\}", self.src)
        assert "opacity: 1" in m.group(1)


class TestNoControlSilentlyLosesItsName:
    """The editor's other controls were already accessible (real <button>/<input>
    elements, or labelled). Pin that, so a future markup edit can't quietly turn one
    back into an unnamed div the way the pips were."""

    def test_every_bare_input_has_a_label(self):
        for tag, a in _parse("collection.html"):
            if tag != "input" or a.get("type") == "hidden":
                continue
            assert a.get("aria-label") or a.get("id") in ("",), a

    def test_every_select_has_a_label(self):
        for tag, a in _parse("collection.html"):
            if tag == "select":
                assert a.get("aria-label"), a
