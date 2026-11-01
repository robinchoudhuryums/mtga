import sys, json, re
sys.path.insert(0, "scripts")
import deck as D
from lib import card_colors
carddata, cardmeta, mana = D.load_card_data(), D.load_card_meta(), D.load_mana()
legal, rar = D.load_legalities(), D.load_rarities()
_, _, qty = D.load_collection()
def ctx(i):
    d = D.find_deck(i); dmeta, cards = D.parse_deck_file(d["path"])
    tw = {}
    for q, n, s, c in cards:
        if n.lower() in D.BASICS: continue
        m = cardmeta.get(n.lower())
        if m:
            for t in m["synergies"]: tw[t] = tw.get(t, 0) + q
    central = D._central_themes(tw)
    di, dca = D.deck_role_counts(cards, carddata)
    sig = D._strong_signature_themes(dmeta, cards, cardmeta)
    return dict(id=i, meta=dmeta, cards=cards, tw=tw, central=central, di=di, dca=dca, sig=sig,
                in_deck={D._ms_key(n) for q, n, s, c in cards},
                declared=set(D._declared_colors(dmeta) or D._deck_castable_colors(dmeta, cards, mana)),
                lock=D.commander_identity_lock(dmeta, carddata),
                fmt=(dmeta.get("format") or "").strip().lower())
decks = {"T": ctx("75-historic-brawl"), "G": ctx("96")}
sq = D._squash_index(carddata, lambda k: carddata[k].get("name") or k)
names = [l.strip() for l in open(sys.argv[1]) if l.strip()]
src = sys.argv[2]
out = []
for q in names:
    key, cands = D._resolve_card_name(q, carddata, lambda k: carddata[k].get("name") or k, sq)
    if not key:
        out.append(dict(query=q, name=q, src=src, unresolved=cands[:4])); continue
    cd = carddata[key]; name = cd.get("name") or q; nl = name.lower(); text = cd.get("text") or ""
    cost, mv = (mana.get(nl) or mana.get(nl.split(" // ")[0]) or (None, None))
    ident = card_colors(cd.get("colors")); ctags = set(cardmeta.get(nl, {}).get("synergies", []))
    legs = legal.get(nl) or legal.get(nl.split(" // ")[0]) or set()
    row = dict(query=q, name=name, src=src, cost=cost, mv=mv, rar=rar.get(nl, "?"),
               owned=D.owned_qty(qty, name), roles=sorted(D.classify_roles(text)),
               type=cd.get("type") or "", text=text)
    for k, c in decks.items():
        shared = sorted(ctags & c["central"])
        st = D.fit_strength(shared, c["tw"], text, c["di"], c["dca"], c["sig"],
                            overlay=lambda t=text, c=c: D.structural_overlay_hit(t, c["cards"], carddata),
                            scale=D.deck_floor_scale(c["meta"], c["cards"]))
        ok, note = D._candidate_castability(cost, ident, c["declared"], lock=c["lock"])
        row[k] = dict(strength=st, shared=shared, castable=ok, note=note,
                      illegal=bool(c["fmt"] and legs and D.pool_format_key(c["fmt"]) not in legs),
                      present=D._ms_key(nl) in c["in_deck"])
    out.append(row)
json.dump(out, open(sys.argv[3], "w"))
print(len(out), sum(1 for r in out if r.get("unresolved") is not None))
