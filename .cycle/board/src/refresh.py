"""Recompute the Sultai board's LIVE data from the repo and rewrite the page's data island.
Run from the repo root after any change to either deck:  python3 .cycle/board/src/refresh.py
(`--build-only` re-renders the page from template + data without recomputing.)
Refreshes: each deck's header stats, its current nonland list with `cuts` rank, every card's
in-list flags, roles and mana value. Reasons and pile placement are left as written."""
import json, re, subprocess, sys, datetime
sys.path.insert(0, "scripts")
import deck as D

PAGE = ".cycle/board/index.html"
DATA = ".cycle/board/src/data.json"
TEMPLATE = ".cycle/board/src/template.html"

def build():
    """Render the page: the template with the data island filled in. Styling lives only in the template,
    so a restyle never touches card data or reasons."""
    t = open(TEMPLATE).read()
    open(PAGE, "w").write(t.replace("__DATA__", json.dumps(json.load(open(DATA))).replace("</", "<\\/"), 1))
DECKS = {"T": "75-historic-brawl", "G": "96"}
ROLE_GROUP = [("Interaction", ("Removal", "Sweeper", "Counter")), ("Card advantage", ("Card advantage",)),
              ("Ramp", ("Ramp",)), ("Recursion", ("Recursion", "Reanimation")), ("Payoff / engine", ("Payoff",))]

def role_groups(roles):
    out = [g for g, keys in ROLE_GROUP if any(r.startswith(k) for r in roles for k in keys)]
    return out

def tapped_cost(did):
    o = subprocess.run([sys.executable, "scripts/deck.py", "consistency", did, "--tempo"],
                       capture_output=True, text=True).stdout
    m = re.search(r"Tapped lands cost ([\d.]+) point", o)
    return m.group(1) if m else "?"

if "--build-only" in sys.argv:
    build(); sys.exit(0)
carddata = D.load_card_data()
mana = D.load_mana()
data = json.load(open(DATA))
live = {}
for k, did in DECKS.items():
    d = D.find_deck(did); meta, cards = D.parse_deck_file(d["path"])
    vec = D.deck_quality_vector(d)
    src = D.deck_color_sources(cards, meta, carddata)
    rows, central, prot, _ = D.rank_cut_candidates(d)
    rank = {r[1]: i + 1 for i, r in enumerate(rows)}
    nonland, lands = [], 0
    for q, n, _s, _c in cards:
        cd = carddata.get(n.lower()) or {}
        if "Land" in (cd.get("type") or "").split(" // ")[0]:
            lands += q; continue
        if meta.get("commander") and n == meta.get("commander"):
            continue
        nonland.append({"n": n, "mv": next((r[2] for r in rows if r[1] == n), None),
                        "r": rank.get(n), "prot": n in prot,
                        "roles": role_groups(sorted(D.classify_roles(cd.get("text") or "")))})
    nonland.sort(key=lambda c: (c["r"] is None, c["r"] or 0, c["n"]))
    live[k] = dict(id=did, name=d["name"], cmd=meta.get("commander"), size=vec.get("size"),
                   floor=D.tier_band(vec), interaction=vec["interaction"], ca=vec["card_advantage"],
                   sources=" · ".join(f"{c}{src.get(c, 0)}" for c in "UBG"), tapped=tapped_cost(did),
                   crafts=vec.get("missing", 0), avg_mv=vec.get("avg_mv"), lands=lands, list=nonland,
                   protect=sorted(prot), avg_mv_n=vec.get("avg_mv_n"),
                   req={b: list(D.floor_requirements(vec, b)) for b in ("A", "B", "C")},
                   keys=sorted({D._ms_key(n) for q, n, _s, _c in cards}))
for c in data["cards"]:
    k = D._ms_key(c["n"])
    c["iT"] = k in set(live["T"]["keys"]); c["iG"] = k in set(live["G"]["keys"])
    c["pT"] = c["n"] in live["T"]["protect"]; c["pG"] = c["n"] in live["G"]["protect"]
    cd = carddata.get(c["n"].lower()) or carddata.get(c["n"].lower().split(" // ")[0]) or {}
    c["ro"] = role_groups(sorted(D.classify_roles(cd.get("text") or c.get("x") or "")))
    c["ri"], c["rc"] = D.deck_role_counts([(1, c["n"], None, None)], carddata)
    me = mana.get(c["n"].lower()) or mana.get(c["n"].lower().split(" // ")[0])
    c["mf"] = me[1] if me else None
    c["land"] = "Land" in (cd.get("type") or c.get("t") or "").split(" // ")[0]
for v in live.values(): v.pop("keys")
data["meta"]["live"] = live
data["meta"]["refreshed"] = datetime.date.today().isoformat()
json.dump(data, open(DATA, "w"))
build()
print({k: {x: v[x] for x in ("floor", "interaction", "ca", "sources", "tapped", "crafts")} for k, v in live.items()},
      sum(1 for c in data["cards"] if c["iT"]), sum(1 for c in data["cards"] if c["iG"]))
