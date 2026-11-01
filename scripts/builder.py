#!/usr/bin/env python3
"""Builder projects — a deck-building pile kept as data, with everything else derived.

A Builder project is one JSON file, `builds/<slug>/build.json`, holding ONLY what a person
(or Claude) decided by hand:

  * which decks the project builds (ids, in display order, each with a short key),
  * which piles exist (label, intro, the deck a pile favours),
  * which cards are in the project and on which pile,
  * the REASON written for each card, and the version of each deck it was written against.

Everything else — oracle text, cost, type, rarity, owned count, roles, whether a deck runs
the card, whether it is protected, each deck's live stats, its nonland list with `cuts`
ranks — is DERIVED at read time from the repo, by calling the deck model (never by
re-implementing it). That split is the lesson of the Sultai pile board: stats typed into a
page went stale at the first swap, and the reason is the only part worth storing.

A reason records `graded_at`: a hash of each deck's card list when the reason was written.
`check` reports a reason whose deck has changed since, because a placement can go stale when
a deck changes plan (three "fits neither" cards on the Sultai board had been graded for a
plan the deck no longer had). The theme-fit grade is deliberately NOT stored or shown as a
verdict here — it misreads graveyard polarity and interaction (G-42).

Subcommands:
  new <slug> --decks ID [ID …] [--keys K …] [--title T]
  add <slug> NAME … [--file F] [--pile P] [--src S]
  place <slug> CARD PILE
  reason <slug> CARD --text "…" [--group G]
  hidden <slug> CARD --role interaction|card-advantage [--remove]
                                     a role the classifier misses but the card really plays
  check <slug>                       stale reasons, unresolved names, unplaced cards
  picks <slug> [FILE|-]              the board's "Copy as text" block → swap --package lines
  derive <slug> [--out FILE] [--no-tempo]   the page's data (cards + live deck stats)
  render <slug> --target pages|artifact --out DIR [--no-tempo] [--no-images]
                                     the page: scripts/builder_template.html + the derived
                                     data (PAGE = TEMPLATE + DATA). `artifact` also writes
                                     img/lg/ (672 px) and img/thumbs.jpg next to it; `pages`
                                     hot-links Scryfall and needs no image files.

Run from the repo root, e.g. `python3 scripts/builder.py check sultai`.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import REPO_ROOT, alias_front, atomic_write  # noqa: E402

BUILDS_DIR = os.path.join(REPO_ROOT, "builds")
SCHEMA = 1
DEFAULT_GROUPS = {}
ROLE_GROUP = [("Interaction", ("Removal", "Sweeper", "Counter")),
              ("Card advantage", ("Card advantage",)),
              ("Ramp", ("Ramp",)),
              ("Recursion", ("Recursion", "Reanimation")),
              ("Payoff / engine", ("Payoff",))]


class BuildError(Exception):
    """A request the build cannot satisfy (unknown slug, card, pile or deck)."""


# ---------------------------------------------------------------- deck model access
def _deck():
    import deck as D  # imported lazily: deck.py is large and `--help` should stay fast
    return D


def deck_ref(ref):
    """The deck record for an id or a path (scratch decks in tests use paths)."""
    d = _deck().find_deck(ref, allow_path=True)
    if not d:
        raise BuildError(f"no deck {ref!r} (try: python3 scripts/deck.py list)")
    return d


def deck_hash(ref):
    """A short hash of the deck's CARD LIST — quantities and names, not headers or prose,
    so editing `#: notes:` does not mark every reason stale while any swap does."""
    D = _deck()
    _meta, cards = D.parse_deck_file(deck_ref(ref)["path"])
    tally = {}
    for q, n, _s, _c in cards:
        k = D._ms_key(n)
        tally[k] = tally.get(k, 0) + q
    blob = "\n".join(f"{q} {k}" for k, q in sorted(tally.items()))
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]


def _name_index():
    D = _deck()
    cd = D.load_card_data()
    disp = lambda k: cd[k].get("name") or k  # noqa: E731
    return cd, disp, D._squash_index(cd, disp)


def resolve_name(name, _idx=None):
    """The canonical card name for `name`, or BuildError. A name not on Arena (absent from
    the pool and the library) is refused rather than stored, since nothing could be
    derived for it."""
    D = _deck()
    cd, disp, sq = _idx or _name_index()
    key, cands = D._resolve_card_name(name.strip(), cd, disp, sq)
    if key:
        return disp(key)
    if cands:
        raise BuildError(f"{name!r} is ambiguous: {'; '.join(cands[:5])}")
    raise BuildError(f"{name!r} is not a known Arena card (not in card-pool.csv or the library)")


def role_groups(roles):
    return [g for g, keys in ROLE_GROUP if any(r.startswith(k) for r in roles for k in keys)]


# ---------------------------------------------------------------- file I/O
def build_path(slug):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", slug or ""):
        raise BuildError(f"bad build name {slug!r}: use lowercase letters, digits and hyphens")
    return os.path.join(BUILDS_DIR, slug, "build.json")


def load_build(slug):
    p = build_path(slug)
    if not os.path.exists(p):
        raise BuildError(f"no build {slug!r} (expected {os.path.relpath(p, REPO_ROOT)})")
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def save_build(slug, build):
    p = build_path(slug)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    text = json.dumps(build, indent=1, ensure_ascii=False, sort_keys=False) + "\n"
    atomic_write(p, lambda fh: fh.write(text), backup=os.path.exists(p))


def _card_entry(build, name):
    for c in build["cards"]:
        if c["name"] == name:
            return c
    return None


def _pile_keys(build):
    return [p["key"] for p in build.get("piles", [])]


def _deck_keys(build):
    return [d["key"] for d in build["decks"]]


def current_hashes(build):
    return {d["id"]: deck_hash(d["id"]) for d in build["decks"]}


# ---------------------------------------------------------------- mutations
def new_build(slug, deck_ids, keys=None, title=None):
    if os.path.exists(build_path(slug)):
        raise BuildError(f"build {slug!r} already exists")
    if not deck_ids:
        raise BuildError("a build needs at least one deck")
    decks, used = [], set()
    for i, did in enumerate(deck_ids):
        d = deck_ref(did)
        meta, _ = _deck().parse_deck_file(d["path"])
        label = (meta.get("commander") or d.get("name") or did).split(",")[0].split(" ")[0]
        k = (keys[i] if keys and i < len(keys) else label[:1].upper()) or "D"
        while k in used:
            k = k + str(i + 1)
        used.add(k)
        decks.append({"key": k, "id": did, "label": label})
    piles = [{"key": d["key"], "label": f"{d['label']}'s pile", "deck": d["key"], "intro": ""}
             for d in decks]
    if len(decks) > 1:
        piles.append({"key": "B", "label": "Either deck", "deck": None, "intro": ""})
    piles.append({"key": "N", "label": "Fits neither", "deck": None, "intro": ""})
    build = {"schema": SCHEMA, "title": title or slug.replace("-", " ").title(),
             "decks": decks, "piles": piles, "groups": dict(DEFAULT_GROUPS),
             "cards": [], "reasons": {}}
    save_build(slug, build)
    return build


def add_cards(build, names, pile=None, src="added"):
    """Add resolved names; returns (added, already_present). Raises on the first name that
    does not resolve, before anything is written, so a typo never leaves half a batch."""
    if pile is not None and pile not in _pile_keys(build):
        raise BuildError(f"no pile {pile!r} (piles: {', '.join(_pile_keys(build))})")
    idx = _name_index()
    resolved = [resolve_name(n, idx) for n in names if n.strip()]
    added, present = [], []
    for n in resolved:
        if _card_entry(build, n):
            present.append(n)
            continue
        build["cards"].append({"name": n, "pile": pile, "src": src})
        added.append(n)
    return added, present


def place_card(build, name, pile):
    if pile not in _pile_keys(build):
        raise BuildError(f"no pile {pile!r} (piles: {', '.join(_pile_keys(build))})")
    n = resolve_name(name)
    c = _card_entry(build, n)
    if not c:
        raise BuildError(f"{n!r} is not in this build; add it first")
    c["pile"] = pile
    return n


def set_reason(build, name, text, group=None):
    n = resolve_name(name)
    if not _card_entry(build, n):
        raise BuildError(f"{n!r} is not in this build; add it first")
    if not (text or "").strip():
        raise BuildError("a reason needs text")
    build["reasons"][n] = {"group": group or "", "text": text.strip(),
                           "graded_at": current_hashes(build)}
    return n


HIDDEN_ROLES = ("interaction", "card advantage")


def set_hidden(build, name, role, remove=False):
    """Record (or drop) a role the card really plays that the role classifier does not
    count. Report-only: it feeds the page's "incl. hidden roles" line and is a lead for a
    pattern fix (G-67), never a change to deck.py's counts or the tier floor."""
    role = role.replace("-", " ").lower()
    if role not in HIDDEN_ROLES:
        raise BuildError(f"unknown role {role!r} — use interaction or card-advantage")
    n = resolve_name(name)
    if not _card_entry(build, n):
        raise BuildError(f"{n!r} is not in this build; add it first")
    h = build.setdefault("hidden", {})
    cur = [r for r in h.get(n, []) if r != role]
    if not remove:
        cur.append(role)
    if cur:
        h[n] = sorted(cur)
    else:
        h.pop(n, None)
    return n


# ---------------------------------------------------------------- check
def check_build(build):
    """[(severity, message)] — 'stale' (a deck changed since the reason was written),
    'unknown' (a name no longer resolves), 'unplaced' (no pile or an unknown pile),
    'reasonless' (in no deck of the build and carries no reason). Never raises on a card."""
    out = []
    try:
        hashes = current_hashes(build)
    except BuildError as e:
        return [("deck", str(e))]
    piles = set(_pile_keys(build))
    labels = {d["id"]: d.get("label") or d["id"] for d in build["decks"]}
    in_any = set()
    D = _deck()
    for d in build["decks"]:
        _m, cards = D.parse_deck_file(deck_ref(d["id"])["path"])
        in_any |= {D._ms_key(n) for _q, n, _s, _c in cards}
    idx = _name_index()
    for c in build["cards"]:
        try:
            resolve_name(c["name"], idx)
        except BuildError as e:
            out.append(("unknown", str(e)))
            continue
        if c.get("pile") not in piles:
            out.append(("unplaced", f"{c['name']} is on no pile"))
        r = build["reasons"].get(c["name"])
        if r:
            moved = [labels[i] for i, h in (r.get("graded_at") or {}).items()
                     if i in hashes and hashes[i] != h]
            if moved:
                out.append(("stale", f"{c['name']}: reason written before {', '.join(moved)}'s "
                                     f"list changed — re-read it"))
        elif D._ms_key(c["name"]) not in in_any:
            out.append(("reasonless", f"{c['name']} is in no deck and has no reason yet"))
    for n in build["reasons"]:
        if not _card_entry(build, n):
            out.append(("orphan", f"reason for {n}, which is not in the build"))
    return out


def stale_summary(slug):
    """One soft line for check_all, or None. Counts only what drifts on its own (stale and
    unknown); reasonless/unplaced cards are work in progress, not decay."""
    try:
        issues = check_build(load_build(slug))
    except (BuildError, OSError, ValueError) as e:
        return f"builder {slug}: could not be checked ({e})"
    st = sum(1 for s, _ in issues if s == "stale")
    un = sum(1 for s, _ in issues if s in ("unknown", "deck"))
    if not st and not un:
        return None
    parts = ([f"{st} reason(s) written against an older deck list"] if st else []) + \
            ([f"{un} unresolved name(s) or deck(s)"] if un else [])
    return f"builder {slug}: {', '.join(parts)} — python3 scripts/builder.py check {slug}"


def all_builds():
    if not os.path.isdir(BUILDS_DIR):
        return []
    return sorted(s for s in os.listdir(BUILDS_DIR)
                  if os.path.exists(os.path.join(BUILDS_DIR, s, "build.json")))


# ---------------------------------------------------------------- picks
_SWAP_LINE = re.compile(r"deck\.py swap\s+(\S+)\s+--package\s+(.+)$")
_PAIR = re.compile(r'"([^"=]+)=([^"]+)"')


def _empty_deck_picks():
    return {"pairs": [], "adds": [], "cuts": [], "protect": [], "unprotect": []}


def parse_picks(text):
    """Read the board's "Copy as text" block. Returns {deck_id: {"pairs": [(cut, add)],
    "adds": [...], "cuts": [...], "protect": [...], "unprotect": [...]}} plus "notes",
    "own" [(qty, name, set, collector)] and "hidden" [(name, role)]. Unknown lines are
    ignored."""
    out, notes, cur, section = {}, [], None, None
    own, hidden = [], []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        m = _SWAP_LINE.search(line)
        if m:
            d = out.setdefault(m.group(1), _empty_deck_picks())
            d["pairs"].extend(_PAIR.findall(m.group(2)))
            cur = m.group(1)
            continue
        m = re.match(r"^.+\((\S+)\):$", line)
        if m and not line.startswith("-"):
            cur = m.group(1)
            out.setdefault(cur, _empty_deck_picks())
            section = None
            continue
        if line.startswith("adds with no cut chosen:") and cur:
            out[cur]["adds"] += [x.strip() for x in line.split(":", 1)[1].split(";") if x.strip()]
            continue
        if line.startswith("cuts with no add:") and cur:
            out[cur]["cuts"] += [x.strip() for x in line.split(":", 1)[1].split(";") if x.strip()]
            continue
        m = re.match(r"^(protect|unprotect):\s*(.*)$", line)
        if m and cur:
            out[cur][m.group(1)] += [x.strip() for x in m.group(2).split(";") if x.strip()]
            continue
        if line == "Notes:":
            section = "notes"
            continue
        if line.startswith("Ownership (I own exactly"):
            section = "own"
            continue
        m = re.match(r"^Counts as (interaction|card advantage):$", line)
        if m:
            section = "hid:" + m.group(1)
            continue
        if section == "own":
            m = re.match(r"^(\d+)\s+(.+?)(?:\s+\(([A-Z0-9]{2,6})\)\s*(\S+))?$", line)
            if m:
                own.append((int(m.group(1)), m.group(2), m.group(3), m.group(4)))
                continue
        if section and section.startswith("hid:") and line.startswith("- "):
            hidden.append((line[2:], section[4:]))
            continue
        if line.endswith(":"):
            section = None
            continue
        if section == "notes" and line.startswith("- "):
            notes.append(line[2:])
    return {"decks": out, "notes": notes, "own": own, "hidden": hidden}


def picks_report(build, text, slug=None):
    """Validated `swap --package` commands for each deck in the build, plus warnings."""
    parsed = parse_picks(text)
    D = _deck()
    lines, ids = [], {d["id"]: d for d in build["decks"]}
    idx = _name_index()
    for did, p in parsed["decks"].items():
        if did not in ids:
            lines.append(f"# {did}: not a deck of this build — skipped")
            continue
        _m, cards = D.parse_deck_file(deck_ref(did)["path"])
        runs = {D._ms_key(n) for _q, n, _s, _c in cards}
        good, warn = [], []
        for cut, add in p["pairs"]:
            try:
                cut_n, add_n = resolve_name(cut, idx), resolve_name(add, idx)
            except BuildError as e:
                warn.append(str(e))
                continue
            if D._ms_key(cut_n) not in runs:
                warn.append(f"{cut_n} is not in {did}, so it cannot be cut")
            elif D._ms_key(add_n) in runs:
                warn.append(f"{add_n} is already in {did}")
            else:
                good.append(f'"{cut_n}={add_n}"')
        lines.append(f"# {ids[did].get('label') or did} ({did})")
        if good:
            lines.append(f"python3 scripts/deck.py swap {did} --package {' '.join(good)}")
        for w in warn:
            lines.append(f"#   skipped: {w}")
        if p["adds"]:
            lines.append(f"#   adds with no cut chosen: {'; '.join(p['adds'])}")
        if p["cuts"]:
            lines.append(f"#   cuts with no add: {'; '.join(p['cuts'])}")
        # protect requests are a `#: protect:` HEADER edit, not a swap: report them checked
        # against the deck's current header so a stale request (already protected, or no
        # longer in the deck) is named rather than applied.
        protected = D._protected(_m)
        for kind in ("protect", "unprotect"):
            ok, bad = [], []
            for n in p[kind]:
                try:
                    rn = resolve_name(n, idx)
                except BuildError as e:
                    bad.append(str(e))
                    continue
                k = D._ms_key(rn)
                if k not in runs:
                    bad.append(f"{rn} is not in {did}")
                elif (kind == "protect") == (k in protected):
                    bad.append(f"{rn} is {'already' if kind == 'protect' else 'not'} protected in {did}")
                else:
                    ok.append(rn)
            if ok:
                lines.append(f"#   {kind} (header edit): {'; '.join(ok)}")
            lines += [f"#   skipped {kind}: {b}" for b in bad]
    if parsed["own"]:
        # Ownership corrections are an /ingest batch, never applied from here: an exact
        # count goes through reconcile_crafts --set-exact (it can LOWER a count), and a
        # card owned across two printings sums them — read the dry run (G-10).
        lines.append("# ownership — save these lines to a file, then /ingest (dry run first):")
        for q, n, st, cn in parsed["own"]:
            lines.append(f"{q} {n}" + (f" ({st}) {cn}" if st else "") + ("" if st else "   # no printing: add (SET) #"))
        lines.append("#   python3 scripts/reconcile_crafts.py <file> --set-exact      # then --apply")
    for n, role in parsed["hidden"]:
        lines.append(f"python3 scripts/builder.py hidden {slug or '<slug>'} "
                     f"\"{n}\" --role {role.replace(' ', '-')}")
    if parsed["notes"]:
        lines.append("# notes:")
        lines += [f"#   {n}" for n in parsed["notes"]]
    return lines


# ---------------------------------------------------------------- derive
def _tapped_cost(did):
    o = subprocess.run([sys.executable, os.path.join(REPO_ROOT, "scripts", "deck.py"),
                        "consistency", did, "--tempo"], capture_output=True, text=True,
                       cwd=REPO_ROOT).stdout
    m = re.search(r"Tapped lands cost ([\d.]+) point", o)
    return m.group(1) if m else "?"


def deck_live(did, tempo=True):
    """Live figures for one deck, from the model: floor, interaction, card advantage,
    sources, tapped-land cost, crafts, avg MV, protect list, nonland list with `cuts`
    ranks, and the scaled floor thresholds the page uses to project a pick's effect."""
    D = _deck()
    carddata = D.load_card_data()
    d = deck_ref(did)
    meta, cards = D.parse_deck_file(d["path"])
    vec = D.deck_quality_vector(d)
    src = D.deck_color_sources(cards, meta, carddata)
    rows, _central, prot, _ = D.rank_cut_candidates(d)
    rank = {r[1]: i + 1 for i, r in enumerate(rows)}
    mvs = {r[1]: r[2] for r in rows}
    nonland, lands = [], 0
    for q, n, _s, _c in cards:
        cd = carddata.get(n.lower()) or {}
        if "Land" in (cd.get("type") or "").split(" // ")[0]:
            lands += q
            continue
        if meta.get("commander") and n == meta.get("commander"):
            continue
        nonland.append({"n": n, "mv": mvs.get(n), "r": rank.get(n), "prot": n in prot,
                        "roles": role_groups(sorted(D.classify_roles(cd.get("text") or "")))})
    nonland.sort(key=lambda c: (c["r"] is None, c["r"] or 0, c["n"]))
    return {"id": did, "name": d["name"], "cmd": meta.get("commander"), "size": vec.get("size"),
            "floor": D.tier_band(vec), "interaction": vec["interaction"], "ca": vec["card_advantage"],
            # the deck's own colours only: a commander-identity land reads as five colours
            # in deck_color_sources (G-37 residual), which put a phantom "W1 · R1" on a UBG deck
            "sources": " · ".join(f"{c}{src.get(c, 0)}" for c in "WUBRG"
                                  if c in (set(D._declared_colors(meta) or "") or set("WUBRG"))
                                  and src.get(c)),
            "tapped": _tapped_cost(did) if tempo else "?", "crafts": vec.get("missing", 0),
            "avg_mv": vec.get("avg_mv"), "avg_mv_n": vec.get("avg_mv_n"), "lands": lands,
            "list": nonland, "protect": sorted(prot),
            "req": {b: list(D.floor_requirements(vec, b)) for b in ("A", "B", "C")},
            "keys": sorted({D._ms_key(n) for _q, n, _s, _c in cards})}


def _printings():
    """{lowercased name: "SET CN"} — the printing an ownership correction names. An owned
    card uses a library row (the printing you hold); otherwise the pool's one printing."""
    import csv
    out = {}
    for path in ("card-pool.csv", "card-library.csv"):          # library last: it wins
        try:
            with open(os.path.join(REPO_ROOT, path), encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    if r.get("Set Code") and r.get("Collector #"):
                        out[r["Card Name"].lower()] = f"{r['Set Code'].upper()} {r['Collector #']}"
        except OSError:
            pass
    alias_front(out)            # second pass, never in-pass setdefault (G-63)
    return out


def derive(build, tempo=True):
    """The page's data: one record per card (facts, flags, reason) and `meta.live` per deck.
    Field names match the board template (n, c, mv, t, r, o, p, x, ro, ri, rc, mf, land,
    i<KEY>, p<KEY>, g, w)."""
    D = _deck()
    carddata, mana = D.load_card_data(), D.load_mana()
    rar = D.load_rarities()
    _, _, qty = D.load_collection()
    live = {d["key"]: deck_live(d["id"], tempo=tempo) for d in build["decks"]}
    keysets = {k: set(v.pop("keys")) for k, v in live.items()}
    prots = {k: set(v["protect"]) for k, v in live.items()}
    printing = _printings()
    hidden = build.get("hidden", {})
    on_board = {c["name"] for c in build["cards"]}
    # Deck-list cards that are on no pile still get a record (pile None), so the page can
    # show them in the Compare view and the card pane like any other card.
    extra = [{"name": x["n"], "pile": None, "src": "deck"} for v in live.values() for x in v["list"]
             if x["n"] not in on_board]
    extra = list({e["name"]: e for e in extra}.values())
    out = []
    for c in build["cards"] + extra:
        n = c["name"]
        nl = n.lower()
        cd = carddata.get(nl) or carddata.get(nl.split(" // ")[0]) or {}
        me = mana.get(nl) or mana.get(nl.split(" // ")[0])
        text = cd.get("text") or ""
        rec = {"n": n, "c": (me[0] if me else "") or "", "mv": me[1] if me else None,
               "mf": me[1] if me else None, "t": cd.get("type") or "",
               "r": (rar.get(nl) or rar.get(nl.split(" // ")[0]) or "?")[:1].upper(),
               "o": D.owned_qty(qty, n), "p": c.get("pile"), "src": c.get("src", ""), "x": text,
               "ro": role_groups(sorted(D.classify_roles(text))),
               "land": "Land" in (cd.get("type") or "").split(" // ")[0]}
        rec["ri"], rec["rc"] = D.deck_role_counts([(1, n, None, None)], carddata)
        _u, under, _nd = D.role_coverage_flags([(1, n, None, None)], carddata)
        rec["hr"] = under[0][1].split("/") if under else []      # suspected: the classifier missed it
        rec["hc"] = list(hidden.get(n, []))                       # confirmed by hand (build.json)
        rec["pr"] = printing.get(nl) or printing.get(nl.split(" // ")[0]) or ""
        for k in live:
            rec["i" + k] = D._ms_key(n) in keysets[k]
            rec["p" + k] = n in prots[k]
        r = build["reasons"].get(n)
        if r:
            rec["g"], rec["w"] = r.get("group", ""), r.get("text", "")
        out.append(rec)
    return {"cards": out,
            "meta": {"title": build.get("title"), "groups": build.get("groups", {}),
                     "decks": build["decks"], "piles": build.get("piles", []),
                     "live": live, "refreshed": datetime.date.today().isoformat()}}


# ---------------------------------------------------------------- render
TEMPLATE = os.path.join(REPO_ROOT, "scripts", "builder_template.html")
TARGETS = ("pages", "artifact")
LARGE = (672, 940)


def image_slug(name):
    """The file name the page uses for a card's image (mirrors the template's slug())."""
    import unicodedata
    n = unicodedata.normalize("NFKD", (name or "").lower())
    n = re.sub(r"[^a-z0-9]+", "-", n).strip("-")
    return n[:180] or "card"


def image_urls(slug, names, fetch=True):
    """{name: Scryfall `normal` image URL} for `names`. Reads, in order, the build's own
    cache (`builds/<slug>/images.json`, committed so an offline Pages build has them),
    the gallery's image-manifest.json, then Scryfall for whatever is still missing, and
    writes any new URLs back to the cache. A name with no image is simply absent."""
    cache_path = os.path.join(os.path.dirname(build_path(slug)), "images.json")
    try:
        cache = json.load(open(cache_path, encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    try:
        man = json.load(open(os.path.join(REPO_ROOT, "image-manifest.json"), encoding="utf-8"))
    except (OSError, ValueError):
        man = {}
    out, need = {}, []
    for n in dict.fromkeys(names):
        k = n.lower()
        u = cache.get(n) or man.get(k) or man.get(k.split(" // ")[0])
        if u:
            out[n] = u
        else:
            need.append(n)
    if need and fetch:
        try:
            import scryfall
            for i in range(0, len(need), 70):
                batch = need[i:i + 70]
                res = scryfall.post_collection([n.split(" // ")[0] for n in batch])
                got = {}
                for d in res.get("data", []):
                    iu = d.get("image_uris") or ((d.get("card_faces") or [{}])[0].get("image_uris")) or {}
                    if iu.get("normal"):
                        got[d["name"].lower()] = got[d["name"].lower().split(" // ")[0]] = iu["normal"]
                for n in batch:
                    u = got.get(n.lower()) or got.get(n.lower().split(" // ")[0])
                    if u:
                        out[n] = u
        except Exception as e:  # an outage degrades to missing images, never a failed render
            print(f"builder: Scryfall image lookup skipped ({e})", file=sys.stderr)
    new = {n: u for n, u in out.items() if cache.get(n) != u}
    if new:
        cache.update(new)
        atomic_write(cache_path, lambda fh: fh.write(json.dumps(cache, indent=1, sort_keys=True) + "\n"),
                     backup=False)
    return out


def _fetch_image(url, out, size):
    """Download one image, shrink it to `size`, save a JPEG. Existing files are kept."""
    if os.path.exists(out):
        return True
    import io
    import urllib.request
    from PIL import Image
    req = urllib.request.Request(url, headers={"User-Agent": "mtga-card-library/1.0", "Accept": "image/*"})
    raw = urllib.request.urlopen(req, timeout=30).read()
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    im.thumbnail(size)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out, "JPEG", quality=80 if size == LARGE else 78, optimize=True, progressive=True)
    return True


SPRITE_CELL, SPRITE_COLS = (68, 94), 20     # 2x the row thumbnail (34 x 47 css px)


def _sprite(out_dir, slugs):
    """All row thumbnails in ONE image, `img/thumbs.jpg`. An artifact version holds at most
    511 files, so a small AND a large file per card stops fitting at ~250 cards; one sprite
    plus one 672 px file per card fits ~500. Returns {"src", "cols", "rows", "w", "h", "i"}
    (`i`: slug → cell index) or None when no large image is on disk yet."""
    from PIL import Image
    have = [s for s in dict.fromkeys(slugs) if os.path.exists(os.path.join(out_dir, "img", "lg", s + ".jpg"))]
    if not have:
        return None
    w, h = SPRITE_CELL
    rows = -(-len(have) // SPRITE_COLS)
    sheet = Image.new("RGB", (w * SPRITE_COLS, h * rows), (40, 40, 40))
    for i, s in enumerate(have):
        im = Image.open(os.path.join(out_dir, "img", "lg", s + ".jpg")).convert("RGB")
        im = im.resize((w, h), Image.LANCZOS)
        sheet.paste(im, ((i % SPRITE_COLS) * w, (i // SPRITE_COLS) * h))
    sheet.save(os.path.join(out_dir, "img", "thumbs.jpg"), "JPEG", quality=82, optimize=True, progressive=True)
    return {"src": "img/thumbs.jpg", "cols": SPRITE_COLS, "rows": rows, "i": {s: i for i, s in enumerate(have)}}


def render(slug, target, out_dir, tempo=True, images=True, data=None):
    """Write `out_dir/index.html` for a build: the template with the derived data inlined.

    `artifact`: images are files next to the page — img/lg/<slug>.jpg (672 px, downloaded
    once and reused) and one thumbnail sprite, img/thumbs.jpg. `pages`: each card carries its Scryfall URL and the
    page hot-links it (small = `normal`, large = `large`). Returns a summary dict."""
    if target not in TARGETS:
        raise BuildError(f"unknown target {target!r} — use one of {', '.join(TARGETS)}")
    b = load_build(slug)
    data = data or derive(b, tempo=tempo)
    meta = data["meta"]
    meta["slug"], meta["target"] = slug, target
    meta["img"] = "remote" if target == "pages" else "local"
    cmds = {k: v.get("cmd") for k, v in meta["live"].items() if v.get("cmd")}
    urls = image_urls(slug, [c["n"] for c in data["cards"]] + list(cmds.values()),
                      fetch=images or target == "pages")
    if target == "pages":
        for c in data["cards"]:
            if urls.get(c["n"]):
                c["im"] = urls[c["n"]]
        meta["portraits"] = {k: urls.get(n, "") for k, n in cmds.items()}
    os.makedirs(out_dir, exist_ok=True)
    got = missing = 0
    if target == "artifact" and images:
        for n, u in urls.items():
            base = image_slug(n) + ".jpg"
            try:
                _fetch_image(u.replace("/normal/", "/large/"), os.path.join(out_dir, "img", "lg", base), LARGE)
                got += 1
            except Exception as e:
                missing += 1
                print(f"builder: image for {n} not fetched ({e})", file=sys.stderr)
    if target == "artifact":
        meta["sprite"] = _sprite(out_dir, [image_slug(n) for n in urls]) if images else None
    import html as _html
    title = meta.get("title") or slug
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = open(TEMPLATE, encoding="utf-8").read()
    page = page.replace("__TITLE__", _html.escape(title), 1).replace("__DATA__", blob, 1)
    if target == "pages":
        page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                + page + "\n</html>\n")
    out = os.path.join(out_dir, "index.html")
    atomic_write(out, lambda fh: fh.write(page), backup=False)
    return {"page": out, "cards": len(data["cards"]), "images": len(urls),
            "fetched": got, "image_errors": missing,
            "no_image": sorted(set(c["n"] for c in data["cards"]) - set(urls))}


# ---------------------------------------------------------------- CLI
def _read_names(args):
    names = list(args.names or [])
    if getattr(args, "file", None):
        fh = sys.stdin if args.file == "-" else open(args.file, encoding="utf-8")
        for line in fh:
            line = re.sub(r"^\s*\d+x?\s+", "", line.strip())
            line = re.sub(r"\s+\([A-Z0-9]{2,6}\)\s*\S*\s*$", "", line).strip()
            if line and not re.fullmatch(r"(?i)deck|commander|sideboard|companion", line):
                names.append(line)
    return names


def main(argv=None):
    ap = argparse.ArgumentParser(prog="builder.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new", help="start a build for one or more decks")
    p.add_argument("slug"); p.add_argument("--decks", nargs="+", required=True)
    p.add_argument("--keys", nargs="+", help="short key per deck (default: commander initial)")
    p.add_argument("--title")
    p = sub.add_parser("add", help="add cards by name (refuses names not on Arena)")
    p.add_argument("slug"); p.add_argument("names", nargs="*")
    p.add_argument("--file", help="a file of names, one per line (Arena export lines work); - for stdin")
    p.add_argument("--pile"); p.add_argument("--src", default="added")
    p = sub.add_parser("place", help="move a card to a pile")
    p.add_argument("slug"); p.add_argument("card"); p.add_argument("pile")
    p = sub.add_parser("reason", help="record why a card is or is not in a deck")
    p.add_argument("slug"); p.add_argument("card"); p.add_argument("--text", required=True)
    p.add_argument("--group", default="")
    p = sub.add_parser("hidden", help="record a role the card plays that the classifier does not count")
    p.add_argument("slug"); p.add_argument("card")
    p.add_argument("--role", required=True, choices=["interaction", "card-advantage"])
    p.add_argument("--remove", action="store_true")
    p = sub.add_parser("check", help="stale reasons, unresolved names, unplaced cards")
    p.add_argument("slug"); p.add_argument("--strict", action="store_true",
                                           help="exit 1 when anything is stale or unresolved")
    p = sub.add_parser("picks", help="turn the board's copied picks into swap --package lines")
    p.add_argument("slug"); p.add_argument("file", nargs="?", default="-")
    p = sub.add_parser("derive", help="print the page data (cards + live deck stats) as JSON")
    p.add_argument("slug"); p.add_argument("--out")
    p.add_argument("--no-tempo", action="store_true", help="skip the tapped-land simulation (faster)")
    p = sub.add_parser("render", help="write the page (template + derived data) for pages or a claude.ai artifact")
    p.add_argument("slug"); p.add_argument("--target", choices=TARGETS, required=True)
    p.add_argument("--out", required=True, help="output directory (index.html, and img/ for artifact)")
    p.add_argument("--no-tempo", action="store_true", help="skip the tapped-land simulation (faster)")
    p.add_argument("--no-images", action="store_true", help="artifact: do not download images")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "new":
            b = new_build(args.slug, args.decks, args.keys, args.title)
            print(f"Created {os.path.relpath(build_path(args.slug), REPO_ROOT)}: "
                  + ", ".join(f"{d['key']}={d['id']}" for d in b["decks"]))
            return 0
        b = load_build(args.slug)
        if args.cmd == "add":
            added, present = add_cards(b, _read_names(args), args.pile, args.src)
            save_build(args.slug, b)
            print(f"Added {len(added)} card(s)" + (f"; already present: {', '.join(present)}" if present else ""))
        elif args.cmd == "place":
            n = place_card(b, args.card, args.pile)
            save_build(args.slug, b)
            print(f"{n} → {args.pile}")
        elif args.cmd == "reason":
            n = set_reason(b, args.card, args.text, args.group)
            save_build(args.slug, b)
            print(f"Reason recorded for {n}")
        elif args.cmd == "hidden":
            n = set_hidden(b, args.card, args.role, args.remove)
            save_build(args.slug, b)
            print(f"{n}: hidden roles now {', '.join(b.get('hidden', {}).get(n, [])) or 'none'}")
        elif args.cmd == "check":
            issues = check_build(b)
            if not issues:
                print(f"{args.slug}: clean ({len(b['cards'])} cards, {len(b['reasons'])} reasons)")
            for sev, msg in issues:
                print(f"  {sev:10} {msg}")
            bad = any(s in ("stale", "unknown", "deck") for s, _ in issues)
            return 1 if (args.strict and bad) else 0
        elif args.cmd == "picks":
            text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
            for line in picks_report(b, text, args.slug):
                print(line)
        elif args.cmd == "render":
            r = render(args.slug, args.target, args.out, tempo=not args.no_tempo,
                       images=not args.no_images)
            shown = os.path.relpath(r["page"], REPO_ROOT)
            print(f"Wrote {r['page'] if shown.startswith('..') else shown}: {r['cards']} cards, "
                  f"{r['images']} image URLs" + (f", {r['fetched']} images on disk" if args.target == "artifact" and not args.no_images else ""))
            if r["no_image"]:
                print(f"  no image found for: {'; '.join(r['no_image'])}")
            if r["image_errors"]:
                print(f"  {r['image_errors']} image download(s) failed (see above)")
        elif args.cmd == "derive":
            data = derive(b, tempo=not args.no_tempo)
            s = json.dumps(data, ensure_ascii=False)
            if args.out:
                atomic_write(args.out, lambda fh: fh.write(s), backup=False)
                print(f"Wrote {args.out} ({len(data['cards'])} cards)")
            else:
                print(s)
    except BuildError as e:
        print(f"builder: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
