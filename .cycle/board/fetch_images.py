# Regenerates .cycle/board/img/ (gitignored): one ~336px JPEG per board card, from image-manifest.json or Scryfall. Run from the repo root.
import json, re, sys, unicodedata, urllib.request, io, os, time
sys.path.insert(0, "scripts")
import scryfall
from PIL import Image
def slug(n):
    n = unicodedata.normalize("NFKD", n.lower()); n = re.sub(r"[^a-z0-9]+", "-", n).strip("-"); return n[:180] or "card"
s = open(".cycle/board/index.html").read()
m = re.search(r'<script type="application/json" id="data">(.*?)</script>', s, re.S)
cards = json.loads(m.group(1).replace("<\\/", "</"))["cards"]
man = json.load(open("image-manifest.json"))
urls, need = {}, []
for c in cards:
    k = c["n"].lower(); u = man.get(k) or man.get(k.split(" // ")[0])
    if u: urls[c["n"]] = u
    else: need.append(c["n"])
for i in range(0, len(need), 70):
    batch = need[i:i+70]
    res = scryfall.post_collection([n.split(" // ")[0] if "//" in n else n for n in batch])
    got = {}
    for d in res.get("data", []):
        iu = d.get("image_uris") or ((d.get("card_faces") or [{}])[0].get("image_uris")) or {}
        if iu.get("normal"):
            got[d["name"].lower()] = iu["normal"]; got[d["name"].lower().split(" // ")[0]] = iu["normal"]
    for n in batch:
        u = got.get(n.lower()) or got.get(n.lower().split(" // ")[0])
        if u: urls[n] = u
    time.sleep(0.2)
print("urls", len(urls), "of", len(cards), "missing:", [c["n"] for c in cards if c["n"] not in urls])
ok = 0; tot = 0
for n, u in urls.items():
    out = f".cycle/board/img/{slug(n)}.jpg"
    if os.path.exists(out): ok += 1; tot += os.path.getsize(out); continue
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "mtga-card-library/1.0", "Accept": "image/*"})
        raw = urllib.request.urlopen(req, timeout=30).read()
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        im.thumbnail((336, 470))
        im.save(out, "JPEG", quality=78, optimize=True, progressive=True)
        ok += 1; tot += os.path.getsize(out)
    except Exception as e:
        print("fail", n, e)
    time.sleep(0.08)
print("saved", ok, "total MB", round(tot/1e6, 1))
