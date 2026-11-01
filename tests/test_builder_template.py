"""The Builder page template (scripts/builder_template.html): markup contracts and the
page's arithmetic, checked against the Python model.

The template is generated output's source, so the same two gates the dashboard and the
editor pages carry apply here: every `var(--x)` the page consumes is defined, and both dark
blocks redefine the same theme tokens (a token defined in one mode only keeps the other
mode's value — G-72's colour half). The JS half runs the template's own functions under
Node, like test_dashboard_js.py: the page projects a pick's effect on interaction / card
advantage / tier floor by adding per-card counts, and its own text says "these match
deck.py" — so this test makes that a measurement rather than a claim.
"""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "scripts"))
import builder as B  # noqa: E402
import deck as D  # noqa: E402

SRC = open(B.TEMPLATE, encoding="utf-8").read()
STYLE = SRC[SRC.index("<style>"):SRC.index("</style>")]


def _tokens(block):
    return set(re.findall(r"(--[A-Za-z0-9-]+)\s*:", block))


class TestTokens:
    def test_every_consumed_token_is_defined_on_root(self):
        root = re.search(r":root\{(.*?)\n\}", STYLE, re.S).group(1)
        used = set(re.findall(r"var\((--[A-Za-z0-9-]+)(?![\w$])", SRC))   # skip var(--id${x}) built names
        # tokens set inline per element (deck colour, stripe, quick-pick colour, tab colour…)
        inline = set(re.findall(r"(--[a-z]+):", SRC[SRC.index("<script>", SRC.index("</style>")):]))
        assert used <= _tokens(root) | inline | {"--dc", "--qc", "--tc", "--pct", "--stripe", "--qn"}, \
            sorted(used - _tokens(root) - inline)

    def test_both_dark_blocks_define_the_same_tokens(self):
        media = re.search(r'@media \(prefers-color-scheme: dark\)\{ :root:not\(\[data-theme="light"\]\)\{(.*?)\} \}', STYLE, re.S)
        attr = re.search(r':root\[data-theme="dark"\]\{(.*?)\}', STYLE, re.S)
        assert media and attr
        assert _tokens(media.group(1)) == _tokens(attr.group(1))


class TestMarkup:
    def test_no_inline_event_handlers(self):
        assert not re.search(r"\son[a-z]+=", SRC), "use delegated listeners, not inline handlers"

    def test_every_static_button_has_a_type(self):
        for b in re.findall(r"<button[^>]*>", SRC):
            assert 'type="button"' in b or "type=\\\"button\\\"" in b, b

    def test_theme_toggle_merges_into_the_shared_prefs(self):
        """The dashboard stores several prefs in one mtga-prefs object; overwriting it would
        wipe them, so the toggle must read, update `theme`, and write back."""
        fn = SRC[SRC.index("function toggleTheme"):SRC.index("function toggleTheme") + 400]
        assert 'readJSON("mtga-prefs")' in fn and "p.theme=next" in fn

    def test_keys_are_ignored_while_typing(self):
        k = SRC[SRC.index('document.addEventListener("keydown"'):]
        assert '["input","textarea","select"].includes(tag)' in k


# ---------------------------------------------------------------- Node: the page's own JS
_NODE = shutil.which("node")


def _extract(names):
    out = []
    for name in names:
        marker = f"function {name}("
        assert marker in SRC, f"{name} is no longer in the template"
        i = SRC.index(marker)
        depth, start = 0, SRC.index("{", i)
        for k in range(start, len(SRC)):
            if SRC[k] == "{":
                depth += 1
            elif SRC[k] == "}":
                depth -= 1
                if depth == 0:
                    out.append(SRC[i:k + 1])
                    break
    return "\n".join(out)


_HARNESS = """
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const slug = n => String(n||"").toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"").slice(0,180) || "card";
const LIVE = input.live, CARDS = input.cards; CARDS.forEach(c => c.id = slug(c.n));
const BYID = Object.fromEntries(CARDS.map(c => [c.id, c]));
let picks = input.picks;
eval(fs.readFileSync(process.argv[2], 'utf8'));
console.log(JSON.stringify({proj: project(input.key), names: parseNames(input.paste)}));
"""


@pytest.mark.skipif(not _NODE, reason="node not installed (CI sets PYTEST_NO_SKIPS, so CI cannot skip)")
class TestPageArithmeticMatchesTheModel:
    def test_projection_and_name_parser(self, tmp_path, monkeypatch):
        monkeypatch.setattr(B, "BUILDS_DIR", str(tmp_path / "builds"))
        src = D.find_deck("96")["path"]
        deck_path = tmp_path / "deck96.txt"
        shutil.copy(src, deck_path)
        text = deck_path.read_text(encoding="utf-8")
        add, cut = "Murder", "Counterspell"                     # Murder is not in deck 96
        b = B.new_build("t", [str(deck_path)], keys=["G"])
        B.add_cards(b, [add, cut], pile="G")
        data = B.derive(b, tempo=False)
        picks = {B.image_slug(add): {"picks": ["addG"], "note": "", "pair": {"G": cut}}}
        paste = "Deck\n1 Murder (M21) 109\n2x Opt\nCounterspell (MAR) 52\n\nSideboard\nMurder"
        fx = tmp_path / "in.json"
        fx.write_text(json.dumps({"live": data["meta"]["live"], "cards": data["cards"], "picks": picks,
                                  "key": "G", "paste": paste}))
        js = tmp_path / "fns.js"
        js.write_text(_extract(["bandOf", "project", "parseNames"]))
        h = tmp_path / "h.js"
        h.write_text(_HARNESS)
        out = json.loads(subprocess.run([_NODE, str(h), str(js), str(fx)], capture_output=True,
                                        text=True, check=True).stdout)
        # the model's answer: the same swap applied to a scratch copy of the deck file
        lines = text.splitlines()
        i = next(n for n, ln in enumerate(lines) if re.match(rf"^\d+ {re.escape(cut)}\b", ln))
        lines[i] = f"1 {add}"
        after = tmp_path / "after.txt"
        after.write_text("\n".join(lines) + "\n", encoding="utf-8")
        vec = D.deck_quality_vector(D.find_deck(str(after), allow_path=True))
        p = out["proj"]
        assert (p["i1"], p["c1"]) == (vec["interaction"], vec["card_advantage"])
        assert p["f1"] == D.tier_band(vec)
        assert p["size1"] == p["size0"]
        # the page's name parser and the CLI's --file reader agree on an Arena export
        args = type("A", (), {"names": [], "file": str(tmp_path / "paste.txt")})
        (tmp_path / "paste.txt").write_text(paste)
        assert out["names"] == list(dict.fromkeys(B._read_names(args)))
