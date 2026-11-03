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
        # The cut is any non-commander card deck 96 protects, so a live-deck trim cannot
        # take it away (it used to be Counterspell, which the owner cut on 2026-11-03).
        meta, held = D.parse_deck_file(str(deck_path))
        held = {n for _q, n, _s, _c in held}
        prot = [n.strip() for n in (meta.get("protect") or "").split(";")]
        cut = next(n for n in prot if n in held and n != (meta.get("commander") or "").strip())
        add = "Murder"                                          # Murder is not in deck 96
        assert add not in held
        b = B.new_build("t", [str(deck_path)], keys=["G"])
        B.add_cards(b, [add, cut], pile="G")
        data = B.derive(b, tempo=False)
        picks = {B.image_slug(add): {"picks": ["addG"], "note": "", "pair": {"G": cut}}}
        paste = "Deck\n1 Murder (M21) 109\n2x Opt\nCounterspell (MAR) 52\n\nSideboard\nMurder"
        fx = tmp_path / "in.json"
        fx.write_text(json.dumps({"live": data["meta"]["live"], "cards": data["cards"], "picks": picks,
                                  "key": "G", "paste": paste}))
        js = tmp_path / "fns.js"
        js.write_text(_extract_consts(["hidOf", "hidBonus"]) + "\n" + _extract(["bandOf", "project", "parseNames"]))
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


def _extract_consts(names):
    """One-line `const NAME = …;` helpers, lifted like the functions above."""
    out = []
    for name in names:
        m = re.search(rf"^const {name} = .*$", SRC, re.M)
        assert m, f"const {name} is no longer in the template"
        out.append(m.group(0))
    return "\n".join(out)


_HARNESS_2B = """
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const slug = n => String(n||"").toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"").slice(0,180) || "card";
const LIVE = input.live, CARDS = input.cards; CARDS.forEach(c => c.id = slug(c.n));
const BYID = Object.fromEntries(CARDS.map(c => [c.id, c]));
const DK = Object.keys(LIVE), DECKS = Object.fromEntries(DK.map(k=>[k,{label:k, list:LIVE[k].list}]));
const PROT = Object.fromEntries(DK.map(k=>[k,new Set(LIVE[k].protect||[])]));
const nameOf = id => (BYID[id]&&BYID[id].n) || "";
let picks = input.picks;
eval(fs.readFileSync(process.argv[2], 'utf8'));
console.log(JSON.stringify({
  applied: input.ask.map(([id,v]) => isApplied(id,v)),
  conflicts: conflicts().map(x => x.msg),
  next: nextBand("G", 3, 2), top: nextBand("G", 99, 99)}));
"""


@pytest.mark.skipif(not _NODE, reason="node not installed (CI sets PYTEST_NO_SKIPS, so CI cannot skip)")
class TestAppliedAndConflicts:
    def test_applied_conflicts_and_next_band(self, tmp_path):
        """Synthetic deck G: In1 and In2 are in it, In2 protected; Out is not. The page must
        call an add of a card now IN the deck applied, a cut of a card now OUT applied, and
        flag a cut chosen twice, a protected cut, and a cut that has left the deck."""
        cards = [{"n": "In1", "iG": True, "pG": False}, {"n": "In2", "iG": True, "pG": True},
                 {"n": "Out", "iG": False, "pG": False}, {"n": "A1", "iG": False}, {"n": "A2", "iG": False},
                 {"n": "A3", "iG": False}]
        live = {"G": {"list": [{"n": "In1"}, {"n": "In2", "prot": True}], "protect": ["In2"],
                      "req": {"A": [7, 11], "B": [4, 7], "C": [0, 2]}}}
        picks = {"in1": {"picks": ["addG"]}, "out": {"picks": ["cutG"]},
                 "a1": {"picks": ["addG"], "pair": {"G": "In1"}}, "a2": {"picks": ["addG"], "pair": {"G": "In1"}},
                 "a3": {"picks": ["addG"], "pair": {"G": "In2"}}, "a1x": {"picks": []}}
        picks["out2"] = {"picks": []}
        fx = tmp_path / "in.json"
        fx.write_text(json.dumps({"live": live, "cards": cards, "picks": picks,
                                  "ask": [["in1", "addG"], ["out", "cutG"], ["a1", "addG"], ["in1", "cutG"]]}))
        js = tmp_path / "fns.js"
        js.write_text(_extract_consts(["KINDS", "deckOfPick", "hasPick"]) + "\n"
                      + _extract(["isApplied", "conflicts", "bandOf", "nextBand"]))
        h = tmp_path / "h.js"
        h.write_text(_HARNESS_2B)
        out = json.loads(subprocess.run([_NODE, str(h), str(js), str(fx)], capture_output=True,
                                        text=True, check=True).stdout)
        assert out["applied"] == [True, True, False, False]
        assert any("In1 is the cut for 2 adds" in m for m in out["conflicts"])
        assert any("In2, a protected card" in m for m in out["conflicts"])
        assert out["next"] == {"b": "B", "parts": ["+1 interaction", "+1 more interaction or card advantage"]}  # the +1 interaction also counts toward the sum
        assert out["top"] is None


_HARNESS_BENCH = """
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const CARDS = input.cards, BYID = Object.fromEntries(CARDS.map(c => [c.id, c]));
const DK = ["T","G"], DECKS = {T:{label:"Thranduil"}, G:{label:"Glarb"}};
const PILEDEFS = [{k:"T",deck:"T"},{k:"G",deck:"G"},{k:"B",deck:null}];
const PICKLAB = {}; DK.forEach(k=>["add","cut","bench","out","prot","unprot"].forEach(x=>PICKLAB[x+k]=x+k));
const nameOf = id => (BYID[id]&&BYID[id].n) || "";
let picks = {}, toasts = [];
const canWrite = true, snapshot = () => {}, persist = () => {}, banner = () => {}, toast = m => toasts.push(m);
let GESTURE = null; const gesture = (label, fn) => fn();       // toggleScoped's one-undo wrapper
eval(fs.readFileSync(process.argv[2], 'utf8'));
const res = {};
res.legacy = input.legacy.map(([id, list]) => upgradeLegacy(id, list).sort());
res.scope = CARDS.map(c => pileScope(c));
picks = {a: {picks: ["addT", "benchG"]}};
togglePick("a", "outT"); res.afterOut = [...picks.a.picks].sort();
togglePick("a", "benchT"); res.afterBench = [...picks.a.picks].sort();
toggleScoped("b", "out"); res.scopedOn = [...picks.b.picks].sort();
toggleScoped("b", "out"); res.scopedOff = [...picks.b.picks].sort();
res.toasts = toasts.length;
console.log(JSON.stringify(res));
"""


@pytest.mark.skipif(not _NODE, reason="node not installed (CI sets PYTEST_NO_SKIPS, so CI cannot skip)")
class TestPerDeckBenchAndKeepOut:
    def test_exclusion_scope_and_legacy_upgrade(self, tmp_path):
        """Within one deck Add, Bench and Keep out exclude each other (and the page says what it
        cleared); the other deck's mark is untouched; a deck's own pile scopes b/o to that deck,
        a shared pile to every deck; a legacy deck-less mark spreads over the decks it covered."""
        cards = [{"id": "a", "n": "A", "p": "T"}, {"id": "b", "n": "B", "p": "B"},
                 {"id": "c", "n": "C", "p": "T", "iT": True}]
        legacy = [["a", ["addT", "bench"]], ["b", ["out"]], ["c", ["bench"]], ["a", ["addG", "addT", "bench"]]]
        fx = tmp_path / "in.json"
        fx.write_text(json.dumps({"cards": cards, "legacy": legacy}))
        js = tmp_path / "fns.js"
        js.write_text(_extract_consts(["KINDS", "deckOfPick", "kindOf", "pileScope", "hasPick"]) + "\n"
                      + _extract(["upgradeLegacy", "togglePick", "toggleScoped"])
                      + "\nglobalThis.pileScope = pileScope;")   # an eval'd const is not visible outside it
        h = tmp_path / "h.js"
        h.write_text(_HARNESS_BENCH)
        out = json.loads(subprocess.run([_NODE, str(h), str(js), str(fx)], capture_output=True,
                                        text=True, check=True).stdout)
        assert out["legacy"] == [["addT", "benchG"], ["outG", "outT"], ["benchG"], ["addG", "addT"]]
        assert out["scope"] == [["T"], ["T", "G"], ["T"]]
        assert out["afterOut"] == ["benchG", "outT"]          # Keep out of T cleared + T only
        assert out["afterBench"] == ["benchG", "benchT"]      # Bench in T cleared Keep out of T
        assert out["scopedOn"] == ["outG", "outT"] and out["scopedOff"] == []
        assert out["toasts"] == 2                              # each clearing said so


_HARNESS_VERDICT = """
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const META = {verdicts: input.legend};
eval(fs.readFileSync(process.argv[2], 'utf8'));
console.log(JSON.stringify({
  ranks: input.cards.map(c => vrank(c, "T")),
  match: input.filters.map(f => input.cards.filter(c => vfMatch(c, f)).map(c => c.n))}));
"""


@pytest.mark.skipif(not _NODE, reason="node not installed (CI sets PYTEST_NO_SKIPS, so CI cannot skip)")
class TestVerdictFilter:
    def test_rank_and_filter_bands(self, tmp_path):
        """The page's verdict filter reads the same legend builder.py writes (best first), and an
        ungraded card sorts after every graded one."""
        legend = [[m, B.VERDICT_LABEL[m]] for m in B.VERDICTS]
        cards = [{"n": n, "vd": ({"T": m} if m else {})} for n, m in
                 (("a", "★★★"), ("b", "★★"), ("c", "★"), ("d", "◇"), ("e", "✗"), ("f", None))]
        fx = tmp_path / "in.json"
        fx.write_text(json.dumps({"legend": legend, "cards": cards,
                                  "filters": ["T|top2", "T|top3", "T|low", "T|none", "all"]}))
        js = tmp_path / "fns.js"
        js.write_text(_extract_consts(["VORDER", "vrank"]) + "\n" + _extract(["vfMatch"])
                      + "\nglobalThis.vrank = vrank;")        # an eval'd const is not visible outside it
        h = tmp_path / "h.js"
        h.write_text(_HARNESS_VERDICT)
        out = json.loads(subprocess.run([_NODE, str(h), str(js), str(fx)], capture_output=True,
                                        text=True, check=True).stdout)
        assert out["ranks"] == [0, 1, 2, 3, 5, 99]
        assert out["match"] == [["a", "b"], ["a", "b", "c"], ["d", "e"], ["f"], list("abcdef")]


_HARNESS_SYM = """
const fs = require('fs');
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
eval(fs.readFileSync(process.argv[2], 'utf8'));
const t = "{T}: Add {G}{G}. {2}{B/P}, {Q}: draw. Keep {braces} and {10} words {X}.";
console.log(JSON.stringify({out: sym(esc(t))}));
"""


@pytest.mark.skipif(not _NODE, reason="node not installed (CI sets PYTEST_NO_SKIPS, so CI cannot skip)")
class TestSymbolsInText:
    def test_symbols_become_pips_and_prose_braces_stay(self, tmp_path):
        js = tmp_path / "fns.js"
        js.write_text(_extract_consts(["SYMWORD", "sym"]) + "\n" + _extract(["pip1"])
                      + "\nglobalThis.sym = sym;")
        h = tmp_path / "h.js"
        h.write_text(_HARNESS_SYM)
        out = json.loads(subprocess.run([_NODE, str(h), str(js), "-"], capture_output=True,
                                        text=True, check=True).stdout)["out"]
        assert out.count('class="pip in') == 8                  # T, G, G, 2, B/P, Q, 10, X
        assert 'aria-label="tap"' in out and 'aria-label="untap"' in out
        assert "{braces}" in out                                  # prose in braces is left alone
        assert "{T}" not in out.replace('title="{T}', "")


_HARNESS_PKG = """
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const slug = n => String(n||"").toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"").slice(0,180) || "card";
const CARDS = input.cards; CARDS.forEach(c => c.id = slug(c.n));
const BYID = Object.fromEntries(CARDS.map(c => [c.id, c]));
const DK = ["T"], PROT = {T: new Set()};
const nameOf = id => (BYID[id]&&BYID[id].n) || "";
let picks = input.picks;
eval(fs.readFileSync(process.argv[2], 'utf8'));
globalThis.r = {pkg: packageOf("T"), need: CARDS.map(c => needsCut(c.id, "T"))};
console.log(JSON.stringify(globalThis.r));
"""


@pytest.mark.skipif(not _NODE, reason="node not installed (CI sets PYTEST_NO_SKIPS, so CI cannot skip)")
class TestSwapPackage:
    def test_package_splits_paired_unpaired_and_lone_cuts(self, tmp_path):
        """One deck's pending package: an add with a cut is paired, an add without one needs a
        cut, a marked cut nobody replaces is a lone cut — and an add that already landed (the card
        is in the deck) is none of these."""
        cards = [{"n": "A1", "iT": False}, {"n": "A2", "iT": False}, {"n": "In1", "iT": True},
                 {"n": "In2", "iT": True}, {"n": "Landed", "iT": True}]
        picks = {"a1": {"picks": ["addT"], "pair": {"T": "In1"}}, "a2": {"picks": ["addT", "benchT"]},
                 "in2": {"picks": ["cutT"]}, "landed": {"picks": ["addT"]}}
        fx = tmp_path / "in.json"
        fx.write_text(json.dumps({"cards": cards, "picks": picks}))
        js = tmp_path / "fns.js"
        js.write_text(_extract_consts(["KINDS", "deckOfPick", "hasPick", "pending", "needsCut"]) + "\n"
                      + _extract(["isApplied", "packageOf"])
                      + "\nglobalThis.needsCut = needsCut;")      # an eval'd const is not visible outside it
        h = tmp_path / "h.js"
        h.write_text(_HARNESS_PKG)
        out = json.loads(subprocess.run([_NODE, str(h), str(js), str(fx)], capture_output=True,
                                        text=True, check=True).stdout)
        assert out["pkg"] == {"paired": [["a1", "In1"]], "unpaired": ["a2"], "cutsOnly": ["in2"]}
        assert out["need"] == [False, True, False, False, False]


_HARNESS_DECIDE = """
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const CARDS = input.cards, BYID = Object.fromEntries(CARDS.map(c => [c.id, c]));
const DK = ["T","G"], DECKS = {T:{label:"Thranduil"}, G:{label:"Glarb"}};
const PILEDEFS = [{k:"T",deck:"T"},{k:"G",deck:"G"},{k:"B",deck:null}];
const PICKLAB = {}; DK.forEach(k=>["add","cut","bench","out","prot","unprot"].forEach(x=>PICKLAB[x+k]=x+k));
const nameOf = id => (BYID[id]&&BYID[id].n) || "";
let picks = input.picks, toasts = [], canWrite = true;
const persist = () => {}, banner = () => {}, toast = m => toasts.push(m), paintUndo = () => {},
      render = () => {}, renderDecks = () => {}, rerenderAfterPick = () => {};
eval(fs.readFileSync(process.argv[2], 'utf8'));
const res = {decided: CARDS.map(c => [decided(c,"T"), decided(c,"G"), decidedInPile(c)])};
toggleScoped("b", "bench"); res.afterB = [...picks.b.picks].sort(); res.undoDepth = UNDO.length;
undo(); res.afterU = picks.b ? picks.b.picks : null; res.toasts = toasts;
console.log(JSON.stringify(res));
"""


@pytest.mark.skipif(not _NODE, reason="node not installed (CI sets PYTEST_NO_SKIPS, so CI cannot skip)")
class TestDecidedAndGestureUndo:
    def test_decided_rule_and_one_undo_per_gesture(self, tmp_path):
        """Decided for a deck = in it, or Add/Cut/Bench/Keep out for it; a shared pile counts a
        card decided only when every deck is. `b` on a shared pile marks both decks as ONE undo
        entry, and one undo reverses both."""
        cards = [{"id": "a", "n": "A", "p": "T", "iT": True}, {"id": "b", "n": "B", "p": "B"},
                 {"id": "c", "n": "C", "p": "B"}]
        picks = {"c": {"picks": ["outT", "benchG"]}}
        fx = tmp_path / "in.json"
        fx.write_text(json.dumps({"cards": cards, "picks": picks}))
        js = tmp_path / "fns.js"
        js.write_text(_extract_consts(["KINDS", "deckOfPick", "kindOf", "pileScope", "hasPick", "decided",
                                       "decidedInPile", "pushUndo"]) + "\n"
                      + "const UNDO=[]; let GESTURE=null;\n"
                      + _extract(["snapshot", "gesture", "undo", "togglePick", "toggleScoped"])
                      + "\nObject.assign(globalThis, {decided, decidedInPile, UNDO});")
        h = tmp_path / "h.js"
        h.write_text(_HARNESS_DECIDE)
        out = json.loads(subprocess.run([_NODE, str(h), str(js), str(fx)], capture_output=True,
                                        text=True, check=True).stdout)
        assert out["decided"] == [[True, False, True], [False, False, False], [True, True, True]]
        assert out["afterB"] == ["benchG", "benchT"] and out["undoDepth"] == 1
        assert out["afterU"] is None and out["toasts"][-1].startswith("Undid: Bench: B")   # it had no picks before


_HARNESS_QUICK = """
const fs = require('fs');
const input = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
const DK = input.keys, DECKS = Object.fromEntries(DK.map(k => [k, {label: "Glarb", dc: "var(--idU)"}]));
const ONE = DK.length === 1, K1 = DK[0];
const PILEDEFS = [{k:"P", deck: DK[0]}, {k:"B", deck: null}];
const PICKLAB = {}; DK.forEach(k=>["add","cut","bench","out","prot","unprot"].forEach(x=>PICKLAB[x+k]=x+k));
const ICON = {bench: "|", out: "o"};
let picks = {};
eval(fs.readFileSync(process.argv[2], 'utf8'));
const own = quick({id:"a", n:"A", p:"P"}), shared = quick({id:"b", n:"B", p:"B"});
const count = (h, re) => (h.match(re) || []).length;
console.log(JSON.stringify({
  ownBench: count(own, /data-v="bench/g), sharedBench: count(shared, /data-v="bench/g),
  sharedOut: count(shared, /data-v="out/g), menu: shared.includes('class="qmore"'),
  letters: [...shared.matchAll(/>\\+([^<]+)</g)].map(m => m[1]),
  colours: assignColours(input.srcs)}));
"""


@pytest.mark.skipif(not _NODE, reason="node not installed (CI sets PYTEST_NO_SKIPS, so CI cannot skip)")
class TestManyDecks:
    @pytest.mark.parametrize("keys,menu", [(["G", "G2", "G3"], False), (["G", "G2", "G3", "G4", "G5"], True)])
    def test_row_buttons_and_accents(self, tmp_path, keys, menu):
        """Row buttons name decks by their unique KEY (three Glarbs read +G +G2 +G3, not +G +G +G);
        a shared pile offers Bench and Keep out per deck, folded into a menu past three decks;
        two decks of one colour identity get different accents."""
        fx = tmp_path / "in.json"
        fx.write_text(json.dumps({"keys": keys, "srcs": ["U24 · B20 · G15", "U22 · G15", "U10"]}))
        js = tmp_path / "fns.js"
        js.write_text(_extract_consts(["KINDS", "deckOfPick", "kindOf", "pileScope"]) + "\n"
                      + _extract(["pickColour", "quick", "colourRank", "assignColours"]))
        h = tmp_path / "h.js"
        h.write_text(_HARNESS_QUICK)
        out = json.loads(subprocess.run([_NODE, str(h), str(js), str(fx)], capture_output=True,
                                        text=True, check=True).stdout)
        assert out["letters"] == keys
        assert out["ownBench"] == 1 and out["sharedBench"] == out["sharedOut"] == len(keys)
        assert out["menu"] is menu
        assert out["colours"] == ["U", "G", "U"]          # deck 2 avoids U; deck 3 has only U


_HARNESS_FACE = """
const fs = require('fs');
let META = {img: "remote"};
eval(fs.readFileSync(process.argv[2], 'utf8'));
const dfc = {id: "rona", im: "https://x/normal/front/r.jpg", im2: "https://x/normal/back/r.jpg", b2: 1};
const one = {id: "opt", im: "https://x/normal/front/o.jpg"};
const out = {};
out.remote = [imgSrc(dfc, "l", true), imgSrc(dfc, "l", false), imgSrc(one, "l", true), hasBack(one)];
META = {img: "local"};
out.local = [imgSrc(dfc, "l", true), imgSrc(one, "l", true), hasBack(dfc), showBack(dfc)];
FLIP.add("rona");
out.flipped = showBack(dfc);
console.log(JSON.stringify(out));
"""


@pytest.mark.skipif(not _NODE, reason="node not installed (CI sets PYTEST_NO_SKIPS, so CI cannot skip)")
class TestBackFaces:
    def test_the_back_face_source_and_the_flip_state(self, tmp_path):
        js = tmp_path / "fns.js"
        js.write_text(_extract_consts(["FLIP", "hasBack", "showBack"]) + "\n" + _extract(["imgSrc"])
                      + "\nglobalThis.FLIP = FLIP; globalThis.hasBack = hasBack; globalThis.showBack = showBack;")
        h = tmp_path / "h.js"
        h.write_text(_HARNESS_FACE)
        out = json.loads(subprocess.run([_NODE, str(h), str(js)], capture_output=True,
                                        text=True, check=True).stdout)
        assert out["remote"] == ["https://x/large/back/r.jpg", "https://x/large/front/r.jpg",
                                 "https://x/large/front/o.jpg", False]
        assert out["local"] == ["img/lg/rona--back.jpg", "img/lg/opt.jpg", True, False]
        assert out["flipped"] is True


_HARNESS_ONE = """
const fs = require('fs');
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
const DK = ["G"], DECKS = {G: {label: "Glarb", dc: "var(--idU)"}}, ONE = true, K1 = "G";
const PILEDEFS = [{k:"G", deck: "G"}, {k:"N", deck: null}];
const PICKLAB = {addG:"Add to the deck", cutG:"Cut from the deck", benchG:"Bench", outG:"Keep out"};
const ICON = {bench: "|", out: "o"};
let picks = {};
eval(fs.readFileSync(process.argv[2], 'utf8'));
const cand = quick({id:"a", n:"A", p:"N"}), inDeck = quick({id:"b", n:"B", p:"G", iG: 1});
const words = h => [...h.matchAll(/<button[^>]*>(.*?)<\\/button>/g)].map(m => m[1].replace(/<[^>]+>/g, "").replace(/[|o](?=Bench|Keep)/, "").trim());
console.log(JSON.stringify({cand: words(cand), inDeck: words(inDeck),
  values: [...cand.matchAll(/data-v="([^"]+)"/g)].map(m => m[1]),
  labels: [...cand.matchAll(/aria-label="([^"]+)"/g)].map(m => m[1])}));
"""


@pytest.mark.skipif(not _NODE, reason="node not installed (CI sets PYTEST_NO_SKIPS, so CI cannot skip)")
class TestOneDeck:
    def test_row_buttons_say_what_they_do_without_a_deck_letter(self, tmp_path):
        """A one-deck build has nothing to tell apart, so a candidate reads + Add / Bench /
        Keep out and a card in the list reads − Cut — while the values stay per deck, so the
        picks, the copy and builder.py picks read exactly what a two-deck board writes."""
        js = tmp_path / "fns.js"
        js.write_text(_extract_consts(["KINDS", "deckOfPick", "kindOf", "pileScope"]) + "\n"
                      + _extract(["pickColour", "quick"]))
        h = tmp_path / "h.js"
        h.write_text(_HARNESS_ONE)
        out = json.loads(subprocess.run([_NODE, str(h), str(js)], capture_output=True,
                                        text=True, check=True).stdout)
        assert out["cand"] == ["+ Add", "Bench", "Keep out"]
        assert out["inDeck"] == ["− Cut"]
        assert out["values"] == ["addG", "benchG", "outG"]
        assert out["labels"] == ["Add to the deck: A", "Bench: A", "Keep out: A"]


class TestOneDeckMarkup:
    """The one-deck switches the browser walk exercises, pinned where a refactor would drop them."""

    def test_copy_as_text_keeps_the_deck_named_labels(self):
        # PICKLAB is the shown label and leaves the deck out on one deck; the copied block is
        # read back by `builder.py picks` and by a person, so it keeps FULLLAB.
        fn = SRC[SRC.index("function copyText"):SRC.index("function copyText") + 900]
        assert "FULLLAB[v]" in fn and "PICKLAB[v]" not in fn

    def test_compare_is_home_and_the_piles_lose_their_tabs(self):
        assert "const PILES = [...(ONE?[]:PILEDEFS), CMPTAB," in SRC

    def test_an_old_pile_link_lands_on_compare_with_that_pile(self):
        fn = SRC[SRC.index("function fromHash"):SRC.index("function fromHash") + 300]
        assert "if(!p&&ONE)" in fn and "CMP.pile=pd.k" in fn

    def test_the_curve_moves_to_the_deck_panel(self):
        fn = SRC[SRC.index("function cmpSummaryHTML"):SRC.index("function cmpSummaryHTML") + 300]
        assert "if(ONE) return `${packageHTML(k)}${confHTML(k)}`" in fn
        assert "${ONE?`</div>${curveHTML(k)}</div>`" in SRC


_HARNESS_SECTIONS = """
const fs = require('fs');
const VORDER = ["★★★","★★","★","◇","△","✗"];
eval(fs.readFileSync(process.argv[2], 'utf8'));
const xs = [{n:"a", vd:{G:"✗"}}, {n:"b"}, {n:"c", vd:{G:"★★"}}, {n:"d", vd:{G:"★★★"}},
            {n:"e", vd:{G:"★★"}}, {n:"f", vd:{T:"★★★"}}, {n:"g", vd:{G:"?"}}];
console.log(JSON.stringify(verdictSections(xs, "G").map(s => [s.m, s.cards.map(c => c.n)])));
"""


@pytest.mark.skipif(not _NODE, reason="node not installed (CI sets PYTEST_NO_SKIPS, so CI cannot skip)")
class TestVerdictSections:
    def test_best_first_ungraded_before_out_and_order_kept_inside(self):
        """One deck: the candidate column is grouped by THIS deck's verdict, best first. A card
        with no verdict (or another deck's, or an unknown mark) sits before ✗, so the reject
        pile is last; inside a section the toolbar's sort order is kept; empty sections are
        dropped."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            js = os.path.join(td, "fns.js")
            with open(js, "w", encoding="utf-8") as f:
                f.write(_extract_consts(["VNONE", "vBand"]) + "\n" + _extract(["verdictSections"]))
            h = os.path.join(td, "h.js")
            with open(h, "w", encoding="utf-8") as f:
                f.write(_HARNESS_SECTIONS)
            out = json.loads(subprocess.run([_NODE, h, js], capture_output=True, text=True,
                                            check=True).stdout)
        assert out == [["★★★", ["d"]], ["★★", ["c", "e"]], ["–", ["b", "f", "g"]], ["✗", ["a"]]]


class TestVerdictSectionMarkup:
    def test_out_starts_collapsed_and_the_choice_is_remembered(self):
        assert 'let VCOLL = new Set(Array.isArray(PREFS.vcoll) ? PREFS.vcoll : ["✗"]);' in SRC
        fn = SRC[SRC.index("function savePrefs"):SRC.index("function savePrefs") + 200]
        assert "vcoll:[...VCOLL]" in fn

    def test_a_collapsed_section_is_not_shown_so_keys_and_bulk_marks_skip_it(self):
        # COLIDS.L is what j/k walk and what a bulk mark covers; it must leave collapsed cards out
        assert "L=grouped?secs.flatMap(s=>VCOLL.has(s.m)?[]:s.cards):all" in SRC

    def test_jumps_open_the_section_first(self):
        assert SRC.count("revealCand(") >= 3      # the definition, the package link, Your picks
