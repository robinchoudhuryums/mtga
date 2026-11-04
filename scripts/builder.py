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
  add-deck <slug> ID [--key K] [--label L]   a deck joins an existing build, with its own pile
  place <slug> CARD PILE
  reason <slug> CARD --text "…" [--group G]
  hidden <slug> CARD --role interaction|card-advantage [--remove]
                                     a role the classifier misses but the card really plays
  check <slug>                       stale reasons, unresolved names, unplaced cards
  picks <slug> [FILE|-]              the board's "Copy as text" block → swap --package lines
  derive <slug> [--out FILE] [--no-tempo]   the page's data (cards + live deck stats)
  site --out DIR [--no-tempo]       every build for GitHub Pages, offline: DIR/builder.html,
                                     DIR/builds/<slug>.html and DIR/builds/index.json
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
    return _cards_hash(cards)


def _cards_hash(cards):
    D = _deck()
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
SHARED_PILE_KEYS = ("B", "N")         # the "more than one deck" and "no deck" piles


def shared_pile_labels(n):
    """The default labels of the two deck-less piles for a build of `n` decks: (the "fits more
    than one deck" pile, or None when there is only one deck; the "fits no deck" pile)."""
    if n <= 1:
        return None, "Doesn't fit"
    return ("Either deck", "Fits neither") if n == 2 else ("More than one deck", "Fits none")


def new_build(slug, deck_ids, keys=None, title=None):
    if os.path.exists(build_path(slug)):
        raise BuildError(f"build {slug!r} already exists")
    if not deck_ids:
        raise BuildError("a build needs at least one deck")
    # A deck's key is also its pile's key, so it must not be one of the deck-less piles'
    # keys: a Bruvac or Nashi deck used to get "B" / "N" and share a key with the shared or
    # the no-fit pile. A derived key steps aside (B → B1); an explicit one is refused.
    reserved = set(SHARED_PILE_KEYS)
    bad = [x for x in (keys or []) if x in reserved]
    if bad:
        raise BuildError(f"deck key(s) {', '.join(bad)} are the shared piles' keys — pick others")
    decks, used = [], set(reserved)
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
    shared, none = shared_pile_labels(len(decks))
    if shared:
        piles.append({"key": "B", "label": shared, "deck": None, "intro": ""})
    piles.append({"key": "N", "label": none, "deck": None, "intro": ""})
    build = {"schema": SCHEMA, "title": title or slug.replace("-", " ").title(),
             "decks": decks, "piles": piles, "groups": dict(DEFAULT_GROUPS),
             "cards": [], "reasons": {}}
    save_build(slug, build)
    return build


def add_deck(build, did, key=None, label=None):
    """Add a deck to an existing build (a variant drafted from the pile, say), with its own
    pile. Existing reasons keep their `graded_at`, so `check` reads them as written before
    this deck joined — a reason never claims to have been graded against a list it predates."""
    d = deck_ref(did)
    if any(x["id"] == d["id"] for x in build["decks"]):
        raise BuildError(f"deck {did!r} is already in this build")
    meta, _ = _deck().parse_deck_file(d["path"])
    label = label or (meta.get("commander") or d.get("name") or did).split(",")[0].split(" ")[0]
    used = set(_deck_keys(build)) | set(_pile_keys(build)) | set(SHARED_PILE_KEYS)  # B/N even before they exist
    k = key or label[:1].upper() or "D"
    if k in used:
        if key:
            raise BuildError(f"key {k!r} is already used by a deck or pile")
        k = next(f"{k}{i}" for i in range(2, 99) if f"{k}{i}" not in used)
    old_n = len(build["decks"])
    build["decks"].append({"key": k, "id": d["id"], "label": label})
    piles = build.setdefault("piles", [])
    at = next((i for i, p in enumerate(piles) if p.get("deck") is None), len(piles))
    piles.insert(at, {"key": k, "label": f"{label}'s pile", "deck": k, "intro": ""})
    # A deck count change changes what the deck-less piles mean. A label still at the OLD
    # default follows the new count; one the owner renamed is left alone. Going from one deck
    # to two adds the shared pile a one-deck build has no use for.
    (o_sh, o_no), (n_sh, n_no) = shared_pile_labels(old_n), shared_pile_labels(old_n + 1)
    shared = next((p for p in piles if p.get("deck") is None and p["key"] != "N"), None)
    if shared is None and n_sh and "B" not in {p["key"] for p in piles} and "B" not in _deck_keys(build):
        piles.insert(next((i for i, p in enumerate(piles) if p["key"] == "N"), len(piles)),
                     {"key": "B", "label": n_sh, "deck": None, "intro": ""})
    elif shared is not None and shared.get("label") == o_sh:
        shared["label"] = n_sh
    none = next((p for p in piles if p["key"] == "N" and p.get("deck") is None), None)
    if none is not None and none.get("label") == o_no:
        none["label"] = n_no
    return k


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
    hashes = current_hashes(build)
    build["reasons"][n] = {"group": group or "", "text": text.strip(), "graded_at": hashes}
    record_snapshots(build, hashes)
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


# The pile-analysis legend, best first. A verdict is a hand grade of one card for one deck.
VERDICTS = ("★★★", "★★", "★", "◇", "△", "✗")
VERDICT_LABEL = {"★★★": "take", "★★": "strong", "★": "real", "◇": "situational",
                 "△": "marginal", "✗": "out"}
_VERDICT_ALIAS = {"3": "★★★", "2": "★★", "1": "★", "s": "◇", "m": "△", "x": "✗",
                  **{v: k for k, v in VERDICT_LABEL.items()}}


def norm_verdict(mark):
    m = (mark or "").strip()
    m = _VERDICT_ALIAS.get(m.lower(), m).replace("*", "★")
    if m not in VERDICTS:
        raise BuildError(f"unknown verdict {mark!r} — use one of {' '.join(VERDICTS)} "
                         f"(or 3/2/1/s/m/x, or take/strong/real/situational/marginal/out)")
    return m


def deck_key_of(build, ref):
    """A deck of the build by key, label or id (case-insensitive)."""
    r = (ref or "").strip().lower()
    for d in build["decks"]:
        if r in (d["key"].lower(), (d.get("label") or "").lower(), str(d["id"]).lower()):
            return d["key"]
    raise BuildError(f"{ref!r} is not a deck of this build "
                     f"({', '.join(d['key'] + '=' + (d.get('label') or d['id']) for d in build['decks'])})")


def set_verdict(build, name, deck, mark, pre=False, _idx=None, _hashes=None):
    """Record (or, with mark '-', drop) one card's verdict for one deck. `graded_at` is that
    deck's list hash, so a swap marks the verdict stale; `pre` records a grade written before
    the deck existed in its current form (an import from an analysis doc) — graded_at None,
    which the page shows as "pre-draft" until someone re-grades it."""
    n = resolve_name(name, _idx)
    if not _card_entry(build, n):
        raise BuildError(f"{n!r} is not in this build; add it first")
    k = deck_key_of(build, deck)
    allv = build.setdefault("verdicts", {})
    cur = allv.setdefault(n, {})
    if (mark or "").strip() in ("-", ""):
        cur.pop(k, None)
    else:
        did = next(d["id"] for d in build["decks"] if d["key"] == k)
        h = (_hashes or {}).get(did) or deck_hash(did)
        cur[k] = {"m": norm_verdict(mark), "graded_at": None if pre else h}
        if not pre:
            snaps = build.setdefault("snapshots", {}).setdefault(did, {})
            if h not in snaps:
                _m, cards = _deck().parse_deck_file(deck_ref(did)["path"])
                snaps[h] = _names_of(cards)
    if not cur:
        allv.pop(n, None)
    return n, k


def read_verdict_file(text):
    """Lines of `card<TAB>deck<TAB>mark` (blank lines and # comments skipped)."""
    out = []
    for i, raw in enumerate((text or "").splitlines(), 1):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            raise BuildError(f"line {i}: expected card<TAB>deck<TAB>mark, got {line!r}")
        out.append(tuple(p.strip() for p in parts))
    return out


def verdict_status(build, hashes=None):
    """{deck_key: {"missing": [...], "pre": [...], "stale": [...]}} over the build's cards."""
    hashes = hashes or current_hashes(build)
    current = current_names(build)
    out = {}
    allv = build.get("verdicts", {})
    for d in build["decks"]:
        k, did = d["key"], d["id"]
        st = {"missing": [], "pre": [], "stale": []}
        for c in build["cards"]:
            v = allv.get(c["name"], {}).get(k)
            if not v:
                st["missing"].append(c["name"])
            elif v.get("graded_at") is None:
                st["pre"].append(c["name"])
            elif verdict_stale(build, c["name"], did, v["graded_at"], hashes, current):
                st["stale"].append(c["name"])
        out[k] = st
    return out


def current_names(build):
    D = _deck()
    out = {}
    for d in build["decks"]:
        _m, cards = D.parse_deck_file(deck_ref(d["id"])["path"])
        out[d["id"]] = _names_of(cards)
    return out


def verdict_stale(build, name, did, graded, hashes, current):
    """A verdict is out of date when its deck's list changed since it was given AND the change
    touches it: the card itself entered or left, or the card's reason names a card that did
    (the reason rule, applied per deck). An earlier list that cannot be found counts as stale."""
    if hashes.get(did) == graded:
        return False
    changed = _list_changes(build, did, graded, current)
    if changed is None:
        return True
    D = _deck()
    r = build["reasons"].get(name) or {}
    return any(D._ms_key(n) == D._ms_key(name) for n in changed) or bool(mentioned(r.get("text", ""), changed))


# ---------------------------------------------------------------- check
# ---------------------------------------------------------------- reason staleness
# A reason used to go stale when ANY card in its deck changed, so one round of swaps flagged
# every reason on the board (426 after the Glarb trim) and the warning stopped meaning
# anything. A reason is now stale only when a card that ENTERED or LEFT the deck since it was
# written is the reason's own card or is named in its text. That needs the list as it was:
# `snapshots` in build.json keeps it per graded hash, and for a reason written before
# snapshots existed the deck file's git history is searched for the version with that hash.
_HISTORY = {}


def _names_of(cards):
    seen, out = set(), []
    for _q, n, _s, _c in cards:
        k = _deck()._ms_key(n)
        if k not in seen:
            seen.add(k)
            out.append(n)
    return sorted(out)


def record_snapshots(build, hashes):
    """Store each deck's card names under its current hash, and drop snapshots nothing
    refers to any more (no reason or verdict graded against them, and not current)."""
    D = _deck()
    snaps = build.setdefault("snapshots", {})
    for did, h in hashes.items():
        s = snaps.setdefault(did, {})
        if h not in s:
            _m, cards = D.parse_deck_file(deck_ref(did)["path"])
            s[h] = _names_of(cards)
    used = {(i, h) for r in build["reasons"].values() for i, h in (r.get("graded_at") or {}).items()}
    ids = {d["key"]: d["id"] for d in build["decks"]}
    used |= {(ids[k], x["graded_at"]) for vv in build.get("verdicts", {}).values()
             for k, x in vv.items() if k in ids and x.get("graded_at")}
    used |= {(i, h) for i, h in hashes.items()}
    for did, s in snaps.items():
        for h in [h for h in s if (did, h) not in used]:
            del s[h]


def _history_names(did, h, limit=400):
    """The deck's card names at the commit whose list hashes to `h`, from git, or None."""
    key = (did, h)
    if key in _HISTORY:
        return _HISTORY[key]
    _HISTORY[key] = None
    path = deck_ref(did)["path"]
    rel = os.path.relpath(path, REPO_ROOT)
    try:
        revs = subprocess.run(["git", "log", f"-n{limit}", "--format=%H", "--", rel], cwd=REPO_ROOT,
                              capture_output=True, text=True, timeout=60).stdout.split()
    except (OSError, subprocess.SubprocessError):
        return None
    D = _deck()
    import tempfile
    for rev in revs:
        try:
            text = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=REPO_ROOT, capture_output=True,
                                  text=True, timeout=30).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        if not text:
            continue
        fd, tmp = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(text)
            _m, cards = D.parse_deck_file(tmp)
        except Exception:
            continue
        finally:
            os.remove(tmp)
        hv = _cards_hash(cards)
        _HISTORY.setdefault((did, hv), _names_of(cards))
        if hv == h:
            _HISTORY[key] = _names_of(cards)
            return _HISTORY[key]
    return None


def _name_forms(name):
    """The spellings a reason uses for a card: the full name, a split card's front, and a
    legend's short name before the comma (four letters or more, so "Ob" is never a match)."""
    forms = {name, name.split(" // ")[0]}
    head = name.split(" // ")[0].split(",")[0].strip()
    if len(head) >= 4:
        forms.add(head)
    return forms


def mentioned(text, names):
    """The names in `names` that `text` mentions, by any of their forms, as whole words."""
    out = []
    for n in names:
        for f in _name_forms(n):
            if re.search(r"(?<![A-Za-z])" + re.escape(f) + r"(?![A-Za-z])", text or "", re.I):
                out.append(n)
                break
    return out


def _list_changes(build, did, h, current):
    """Card names that entered or left deck `did` since its list hashed to `h`, or None when
    that list is not on record (no snapshot, and not in the deck file's git history)."""
    D = _deck()
    old = (build.get("snapshots", {}).get(did, {}) or {}).get(h) or _history_names(did, h)
    if old is None:
        return None
    ok, nk = {D._ms_key(n): n for n in old}, {D._ms_key(n): n for n in current[did]}
    return [ok[k] for k in ok.keys() - nk.keys()] + [nk[k] for k in nk.keys() - ok.keys()]


def reason_changes(build, name, reason, hashes, current):
    """For one reason: [(deck id, changed names it concerns)] for each deck whose list
    changed since it was written in a way that touches it, or [(deck id, None)] when the
    deck's earlier list cannot be found (a stale reason, as before snapshots existed)."""
    D = _deck()
    out = []
    for did, h in (reason.get("graded_at") or {}).items():
        if did not in hashes or hashes[did] == h:
            continue
        changed = _list_changes(build, did, h, current)
        if changed is None:
            out.append((did, None))
            continue
        hit = [n for n in changed if D._ms_key(n) == D._ms_key(name)] + mentioned(reason.get("text", ""), changed)
        if hit:
            out.append((did, sorted(set(hit))))
    return out


def check_build(build):
    """[(severity, message)] — 'stale' (a card the reason concerns entered or left a deck since
    it was written),
    'unknown' (a name no longer resolves), 'unplaced' (no pile or an unknown pile),
    'reasonless' (in no deck of the build and carries no reason). Never raises on a card."""
    out = []
    try:
        hashes = current_hashes(build)
    except BuildError as e:
        return [("deck", str(e))]
    piles = set(_pile_keys(build))
    labels = {d["id"]: d.get("label") or d["id"] for d in build["decks"]}
    in_any, current = set(), {}
    D = _deck()
    for d in build["decks"]:
        _m, cards = D.parse_deck_file(deck_ref(d["id"])["path"])
        in_any |= {D._ms_key(n) for _q, n, _s, _c in cards}
        current[d["id"]] = _names_of(cards)
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
            for did, hit in reason_changes(build, c["name"], r, hashes, current):
                if hit is None:
                    out.append(("stale", f"{c['name']}: reason written before {labels[did]}'s list "
                                         f"changed, and that list is not on record — re-read it"))
                else:
                    out.append(("stale", f"{c['name']}: reason concerns {', '.join(hit)}, which "
                                         f"entered or left {labels[did]} since — re-read it"))
        elif D._ms_key(c["name"]) not in in_any:
            out.append(("reasonless", f"{c['name']} is in no deck and has no reason yet"))
    for n in build["reasons"]:
        if not _card_entry(build, n):
            out.append(("orphan", f"reason for {n}, which is not in the build"))
    for n in build.get("verdicts", {}):
        if not _card_entry(build, n):
            out.append(("orphan", f"verdict for {n}, which is not in the build"))
    # Verdicts are work in progress, so one summary line per deck, never a strict failure.
    for k, st in verdict_status(build, hashes).items():
        parts = [f"{len(st[x])} {lab}" for x, lab in (("missing", "with no verdict"),
                 ("pre", "pre-draft"), ("stale", "graded before the list changed")) if st[x]]
        if parts:
            lab = next(d.get("label") or d["id"] for d in build["decks"] if d["key"] == k)
            out.append(("verdicts", f"{lab}: " + ", ".join(parts)))
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
    parts = ([f"{st} reason(s) name a card that entered or left a deck since"] if st else []) + \
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
    return {"pairs": [], "adds": [], "cuts": [], "protect": [], "unprotect": [], "bench": [], "out": []}


def parse_picks(text):
    """Read the board's "Copy as text" block. Returns {deck_id: {"pairs": [(cut, add)],
    "adds": [...], "cuts": [...], "protect": [...], "unprotect": [...], "bench": [...],
    "out": [...]}} plus "notes",
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
        m = re.match(r"^(protect|unprotect|bench|keep out):\s*(.*)$", line)
        if m and cur:
            key = "out" if m.group(1) == "keep out" else m.group(1)
            out[cur][key] += [x.strip() for x in m.group(2).split(";") if x.strip()]
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
        # A benched card becomes a `#~` flex line in the deck file, so the next tune reads the
        # bench (deck.py flex --add refuses a card the deck runs or another flex line names).
        # Keep out changes no file: it is a decision recorded for the next pass.
        for kind, label in (("bench", "bench"), ("out", "keep out (no edit)")):
            ok, bad = [], []
            for n in p[kind]:
                try:
                    rn = resolve_name(n, idx)
                except BuildError as e:
                    bad.append(str(e))
                    continue
                (bad.append(f"{rn} is in {did} — cut it instead") if D._ms_key(rn) in runs else ok.append(rn))
            if ok and kind == "bench":
                lines.append(f"#   bench → #~ flex lines (add --apply to write each):")
                lines += [f'python3 scripts/deck.py flex {did} --add "+{n} | BENCH (builder {slug or "?"}): '
                          f'benched on the board"' for n in ok]
            elif ok:
                lines.append(f"#   {label}: {'; '.join(ok)}")
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


# ---------------------------------------------------------------- apply
# `apply` turns the board's picks into deck-file edits in one checked run, so a round of picks
# no longer goes through hand-run swaps, flex lines and header edits (where a short card name
# once added a duplicate Jin-Gitaxias). The picks come from the board's DATABASE (read with the
# ArtifactData tool into a folder, then `--db <folder>`), or from a copied "Copy as text" block
# when the board was a GitHub Pages copy, which keeps its picks in the browser only.
_PICK_RE = re.compile(r"^(add|cut|bench|out|prot|unprot)(.+)$")
_BENCH_LINE = re.compile(r"^#~\s*\+(.+?)\s*\|\s*BENCH \(builder (\S+?)\)")


def read_db_dump(path):
    """The board's `picks` documents from a database dump: the folder the ArtifactData tool
    writes with `out_dir` (`<dir>/picks/<doc id>.json`), the `picks` folder itself, or one
    JSON file holding a list of documents. Each document is {card, picks, pair, note, own, hid}."""
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else [data]
    folder = os.path.join(path, "picks") if os.path.isdir(os.path.join(path, "picks")) else path
    if not os.path.isdir(folder):
        raise BuildError(f"no database dump at {path!r}")
    docs = []
    for fn in sorted(os.listdir(folder)):
        if fn.endswith(".json"):
            with open(os.path.join(folder, fn), encoding="utf-8") as fh:
                doc = json.load(fh)
            if isinstance(doc, dict) and isinstance(doc.get("data"), dict) and "card" not in doc:
                doc = doc["data"]                      # a wrapped {id, version, data} record
            docs.append(doc)
    return docs


def picks_from_db(build, docs):
    """The database documents in `parse_picks`' shape, so `apply` and `picks` read one model
    whichever surface the owner marked on. A legacy deck-less `bench` / `out` (before
    2026-11-02) reads as every deck of the build the card is not being added to."""
    keys = {d["key"]: d["id"] for d in build["decks"]}
    out, notes, own, hidden = {}, [], [], []
    for doc in docs:
        name = (doc.get("card") or "").strip()
        if not name:
            continue
        codes = [c for c in (doc.get("picks") or []) if isinstance(c, str)]
        adds = {c[3:] for c in codes if c.startswith("add")}
        for code in codes:
            if code in ("bench", "out"):
                targets = [k for k in keys if k not in adds]
                kind = code
            else:
                m = _PICK_RE.match(code)
                if not m or m.group(2) not in keys:
                    continue
                kind, targets = m.group(1), [m.group(2)]
            for k in targets:
                d = out.setdefault(keys[k], _empty_deck_picks())
                if kind == "add":
                    cut = (doc.get("pair") or {}).get(k)
                    (d["pairs"].append((cut, name)) if cut else d["adds"].append(name))
                elif kind == "cut":
                    d["cuts"].append(name)
                else:
                    d[{"prot": "protect", "unprot": "unprotect"}.get(kind, kind)].append(name)
        note = (doc.get("note") or "").strip()
        if note and (doc.get("replyTo") or "").strip() != note:      # unanswered, or edited since
            notes.append(f"{name} — {note}")
        if isinstance(doc.get("own"), int) and doc["own"] >= 0:
            own.append((doc["own"], name, None, None))
        hidden += [(name, r) for r in (doc.get("hid") or []) if r in ("interaction", "card advantage")]
    # A cut that is also some add's pair is the swap's cut, not a second "cut with no add".
    for d in out.values():
        paired = {c for c, _a in d["pairs"]}
        d["cuts"] = [c for c in d["cuts"] if c not in paired]
    return {"decks": out, "notes": notes, "own": own, "hidden": hidden}


def _builder_bench_lines(path, slug):
    """`#~` bench lines this build wrote into the deck file, as {card key: line text}. Only
    lines tagged `BENCH (builder <slug>)` belong to the board; a hand-written bench line is
    never reconciled away."""
    D = _deck()
    found = {}
    with open(path, encoding="utf-8") as fh:
        for ln in fh.read().split("\n"):
            m = _BENCH_LINE.match(ln)
            if m and m.group(2) == slug:
                found[D._ms_key(m.group(1))] = ln
    return found


def plan_apply(build, parsed, slug, retire_bench=False):
    """What `apply` would do to each deck, checked against the deck file as it is NOW:
    {deck id: {"swaps", "adds", "cuts", "protect", "unprotect", "bench_add", "bench_retire",
    "unprotect_cut", "out", "skipped"}}. A pick the deck already shows (an add it runs, a cut
    it no longer runs) is skipped as applied, so running `apply` twice changes nothing.

    BENCH RECONCILE: the board's bench marks are the whole bench, because the board never
    counts a bench mark as applied and "Clear applied marks" leaves them. So a builder-tagged
    `#~` line whose card is no longer benched (or is now in the deck) is retired, and a
    benched card with no `#~` line gets one. The retirement half only runs with
    `retire_bench`: the owner marks on two surfaces (the claude.ai board keeps its picks in
    its database, a GitHub Pages copy in the browser), and a bench set on one is absent from
    the other — a dry run against the board's database on 2026-11-03 would have pruned nine
    bench lines set on Pages that day. Without the flag the stale lines are only LISTED.

    `consume` lists the board marks this plan settles, as (card, pick code, clears a pair):
    a planned edit, or a pick the deck already shows. `apply --db` turns them into a cleanup
    file so the board stops carrying them. A mark the board never clears outlives its edit,
    and once the deck changes again off the board (a cut made in chat) the old add mark reads
    as pending: the same dry run proposed adding back 25 cards the owner had since cut."""
    D = _deck()
    idx = _name_index()
    carddata = idx[0]
    plans = {}
    for b in build["decks"]:
        did, K = b["id"], b["key"]
        p = parsed["decks"].get(did, _empty_deck_picks())
        ref = deck_ref(did)
        meta, cards = D.parse_deck_file(ref["path"])
        runs = {D._ms_key(n) for _q, n, _s, _c in cards}
        protected = D._protected(meta)
        lock = D.commander_identity_lock(meta, carddata)
        plan = {"label": b.get("label") or did, "swaps": [], "adds": [], "cuts": [], "protect": [],
                "unprotect": [], "unprotect_cut": [], "bench_add": [], "bench_retire": [],
                "out": [], "skipped": [], "bench_stale": [], "consume": []}

        def res(n):
            try:
                return resolve_name(n, idx)
            except BuildError as e:
                plan["skipped"].append(str(e))
                return None

        def off_identity(name):
            if lock is None:
                return False
            cd = carddata.get(D._ms_key(name)) or carddata.get(name.lower())
            ident = D.card_colors(cd.get("colors", "")) if cd else None
            return ident is not None and not ident <= lock

        for cut, add in p["pairs"]:
            c, a = res(cut), res(add)
            if not c or not a:
                continue
            if D._ms_key(a) in runs and D._ms_key(c) not in runs:
                plan["skipped"].append(f"{c} → {a} is already applied")
                plan["consume"] += [(a, "add" + K, True), (c, "cut" + K, False)]
            elif D._ms_key(c) not in runs:
                plan["skipped"].append(f"{c} is not in {did}, so it cannot be cut for {a}")
            elif D._ms_key(a) in runs:
                plan["skipped"].append(f"{a} is already in {did}")
            elif off_identity(a):
                plan["skipped"].append(f"{a} is outside the commander's colour identity")
            else:
                plan["swaps"].append((c, a))
                runs.discard(D._ms_key(c)); runs.add(D._ms_key(a))
                plan["consume"] += [(a, "add" + K, True), (c, "cut" + K, False)]
        for n in p["adds"]:
            a = res(n)
            if not a:
                continue
            if D._ms_key(a) in runs:
                plan["skipped"].append(f"{a} is already in {did} (applied)")
                plan["consume"].append((a, "add" + K, False))
            elif off_identity(a):
                plan["skipped"].append(f"{a} is outside the commander's colour identity")
            else:
                plan["adds"].append(a)
                runs.add(D._ms_key(a))
                plan["consume"].append((a, "add" + K, False))
        for n in p["cuts"]:
            c = res(n)
            if not c:
                continue
            plan["consume"].append((c, "cut" + K, False))
            if D._ms_key(c) not in runs:
                plan["skipped"].append(f"{c} is not in {did} (already cut)")
            else:
                plan["cuts"].append(c)
                runs.discard(D._ms_key(c))
        # A cut card leaves the protect line too: the owner's cut decides, and a stale protect
        # entry is a silent no-op that check_all then flags (G-68).
        for c in [c for c, _a in plan["swaps"]] + plan["cuts"]:
            if D._ms_key(c) in protected:
                plan["unprotect_cut"].append(c)
        for kind in ("protect", "unprotect"):
            for n in p[kind]:
                c = res(n)
                if not c:
                    continue
                k = D._ms_key(c)
                if k not in runs:
                    plan["skipped"].append(f"{kind} {c}: not in {did}")
                elif (kind == "protect") == (k in protected):
                    plan["skipped"].append(f"{c} is {'already' if kind == 'protect' else 'not'} protected")
                    plan["consume"].append((c, ("prot" if kind == "protect" else "unprot") + K, False))
                else:
                    plan[kind].append(c)
                    plan["consume"].append((c, ("prot" if kind == "protect" else "unprot") + K, False))
        bench = []
        for n in p["bench"]:
            c = res(n)
            if not c:
                continue
            if D._ms_key(c) in runs:
                plan["skipped"].append(f"bench {c}: it is in {did} now (cut it first to bench it)")
            else:
                bench.append(c)
        have_flex = {D._ms_key(f["in"]) for f in D.parse_flex(ref["path"]) if f.get("in")}
        plan["bench_add"] = [c for c in bench if D._ms_key(c) not in have_flex]
        want = {D._ms_key(c) for c in bench}
        # A bench line for a card the deck now RUNS is stale on every surface (the G-04 +In
        # rot), so it always goes; one the board merely no longer marks waits for the flag.
        for k, ln in sorted(_builder_bench_lines(ref["path"], slug).items()):
            if k in runs:
                plan["bench_retire"].append(ln)
            elif k not in want:
                plan["bench_retire" if retire_bench else "bench_stale"].append(ln)
        plan["out"] = [x for x in (res(n) for n in p["out"]) if x]
        plans[did] = plan
    return plans


def _plan_lines(plans, parsed, slug):
    lines = []
    for did, pl in plans.items():
        acts = sum(len(pl[k]) for k in ("swaps", "adds", "cuts", "protect", "unprotect",
                                         "bench_add", "bench_retire"))
        lines.append(f"# {pl['label']} ({did}) — {acts} change(s)")
        lines += [f"  swap   −{c}  +{a}" for c, a in pl["swaps"]]
        lines += [f"  add    +{a}   (no cut chosen)" for a in pl["adds"]]
        lines += [f"  cut    −{c}   (no add)" for c in pl["cuts"]]
        lines += [f"  protect     {c}" for c in pl["protect"]]
        lines += [f"  unprotect   {c}" for c in pl["unprotect"]]
        lines += [f"  unprotect   {c}   (cut, so it leaves the protect line)" for c in pl["unprotect_cut"]]
        lines += [f"  bench  +{c}   (new #~ line)" for c in pl["bench_add"]]
        lines += [f"  bench  retire: {ln}" for ln in pl["bench_retire"]]
        lines += [f"  bench  not on the board (kept; --retire-bench removes it): {ln}" for ln in pl["bench_stale"]]
        if pl["out"]:
            lines.append(f"  keep out (no edit): {'; '.join(pl['out'])}")
        lines += [f"  skipped: {s}" for s in pl["skipped"]]
    if parsed.get("own"):
        lines.append("# ownership — not applied here; save the lines to a file, then /ingest (dry run first):")
        lines += [f"  {q} {n}" + (f" ({st}) {cn}" if st else "") for q, n, st, cn in parsed["own"]]
    for n, role in parsed.get("hidden", []):
        lines.append(f"# hidden role — python3 scripts/builder.py hidden {slug} \"{n}\" --role {role.replace(' ', '-')}")
    if parsed.get("notes"):
        lines.append("# notes waiting for a reply (write it to the card's record: reply, replyTo = the note):")
        lines += [f"#   {n}" for n in parsed["notes"]]
    return lines


def _section_header_index(lines):
    """The index of the deck's board-picks section header (`# … board picks …`), or None."""
    for i, ln in enumerate(lines):
        if ln.startswith("# ") and not ln.startswith(("#:", "#~")) and "board picks" in ln.lower():
            return i
    return None


def _edit_deck_lines(lines, plan, slug, printing):
    """The deck file's lines with `plan`'s unpaired cuts, unpaired adds, protect changes and
    bench retirements applied. Swaps and new bench lines are written by deck.py itself."""
    D = _deck()
    out = list(lines)
    for c in plan["cuts"]:
        k = D._ms_key(c)
        for i, ln in enumerate(out):
            m = re.match(r"^(\d+)\s+(.+?)\s+\(", ln)
            if m and D._ms_key(m.group(2)) == k:
                q = int(m.group(1))
                if q > 1:
                    out[i] = f"{q - 1}" + ln[len(m.group(1)):]
                else:
                    del out[i]
                break
    if plan["adds"]:
        new = [printing(a) for a in plan["adds"]]
        h = _section_header_index(out)
        if h is not None:
            j = h + 1
            while j < len(out) and out[j].strip() and not (out[j].startswith("# ") or out[j].startswith("#~")):
                j += 1
            out[j:j] = new
        else:
            at = next((i for i, ln in enumerate(out) if ln.startswith("# ") and "land" in ln.lower()), None)
            if at is None:
                at = next((i for i, ln in enumerate(out) if ln.startswith("#~")), len(out))
            out[at:at] = [f"# Board picks (builder {slug})"] + new + [""]
    drop = {D._ms_key(c) for c in plan["unprotect"] + plan["unprotect_cut"]}
    if drop or plan["protect"]:
        pidx = [i for i, ln in enumerate(out) if re.match(r"^#:\s*protect:", ln)]
        for i in pidx:
            names = [x.strip() for x in out[i].split(":", 2)[2].split(";") if x.strip()]
            keep = [n for n in names if D._ms_key(n) not in drop]
            out[i] = "#: protect: " + "; ".join(keep) if keep else None
        if plan["protect"]:
            live = [i for i in pidx if out[i] is not None]
            if live:
                out[live[-1]] = out[live[-1]] + "; " + "; ".join(plan["protect"])
            else:
                at = next((i for i, ln in enumerate(out) if ln.startswith("#: notes:")), None)
                if at is None:
                    at = max((i for i, ln in enumerate(out) if ln.startswith("#:")), default=-1) + 1
                out.insert(at, "#: protect: " + "; ".join(plan["protect"]))
        out = [ln for ln in out if ln is not None]
    retire = set(plan["bench_retire"])
    return [ln for ln in out if ln not in retire]


def _run_swap(did, cut, add):
    """One swap through deck.py itself, so its section placement, flex retirement, identity
    refusal, .bak and recommendations.csv row all apply exactly as for a hand-run swap."""
    r = subprocess.run([sys.executable, os.path.join(REPO_ROOT, "scripts", "deck.py"), "swap", did,
                        "--cut", cut, "--add", add, "--apply"], capture_output=True, text=True, cwd=REPO_ROOT)
    return r.returncode == 0 and "Applied." in r.stdout, (r.stdout + r.stderr).strip()


def _ledger_rows(ref, plan):
    """recommendations.csv rows for the plan's unpaired adds and cuts, scored against the deck
    BEFORE the write, as `swap --apply` scores a swap. Swaps record their own rows through
    deck.py. Telemetry never costs an edit: any failure here records nothing."""
    D = _deck()
    cache, rows = {}, []
    try:
        for a in plan["adds"]:
            r = D.recommendation_row(ref, "", a, "builder", cache=cache)
            if r:
                rows.append(r)
        for c in plan["cuts"]:
            r = D.recommendation_row(ref, c, "", "builder", cache=cache)
            if r:
                rows.append(r)
    except Exception:
        return []
    return rows


def _append_ledger(rows):
    D = _deck()
    done = 0
    for r in rows:
        try:
            D.append_recommendation(r)
            done += 1
        except Exception:
            break
    return done


def execute_apply(build, plans, slug, run_swap=None):
    """Write each deck's plan: swaps first (deck.py swap), then one checked write for the
    unpaired cuts and adds, protect changes and bench retirements (deck.py's INV-04 write:
    the copy count must come out as planned or nothing is saved), then the new bench lines
    (deck.py's flex writer). Returns log lines. A failed swap stops that deck's remaining
    steps, so a half-applied deck is never followed by edits that assumed the swap.
    Returns (log lines, consumed marks): only a deck whose run finished settles its marks."""
    D = _deck()
    run_swap = run_swap or _run_swap
    idx = D._printing_index()
    sq = D._squash_index(idx, lambda k: idx[k][0])

    def printing(name):
        key, _c = D._resolve_card_name(name, idx, lambda k: idx[k][0], sq)
        if not key:
            raise BuildError(f"no printing found for {name!r}")
        disp, setc, coll = idx[key]
        return f"1 {disp} ({setc}) {coll}"

    log, consumed = [], []
    for did, pl in plans.items():
        ref = deck_ref(did)
        ok = True
        for c, a in pl["swaps"]:
            good, out = run_swap(did, c, a)
            log.append(f"{did}: swap −{c} +{a} — {'done' if good else 'FAILED'}")
            if not good:
                log.append("  " + out.splitlines()[-1] if out else "  (no output)")
                ok = False
                break
        if not ok:
            log.append(f"{did}: stopped — the remaining picks for this deck were not applied")
            continue
        if any(pl[k] for k in ("adds", "cuts", "protect", "unprotect", "unprotect_cut", "bench_retire")):
            with open(ref["path"], encoding="utf-8") as fh:
                lines = fh.read().rstrip("\n").split("\n")
            _m, cards = D.parse_deck_file(ref["path"])
            total = sum(q for q, *_ in cards) + len(pl["adds"]) - len(pl["cuts"])
            recs = _ledger_rows(ref, pl)
            D._safe_write_lines(ref["path"], _edit_deck_lines(lines, pl, slug, printing), total)
            n = _append_ledger(recs)
            if n:
                log.append(f"{did}: {n} unpaired pick(s) recorded in recommendations.csv")
            log.append(f"{did}: +{len(pl['adds'])} add(s), −{len(pl['cuts'])} cut(s), "
                       f"{len(pl['protect'])} protect, {len(pl['unprotect']) + len(pl['unprotect_cut'])} unprotect, "
                       f"{len(pl['bench_retire'])} bench line(s) retired")
        for c in pl["bench_add"]:
            line, _bak = D._flex_add(ref, f"+{c} | BENCH (builder {slug}): benched on the board", True)
            log.append(f"{did}: bench line written — {line}")
        consumed += pl["consume"]
    return log, consumed


def cleanup_ops(docs, consumed, at=None):
    """The board-database writes that settle marks: one entry per affected document,
    {id, card, picks, pair, done}, where `picks` and `pair` are the values AFTER the cleanup
    and `done` is the document's history with each settled mark appended as {v, at}. A
    settled mark moves to `done` rather than vanishing, so a mark that leaves `picks` with no
    `done` entry is one the owner took back, and the two stay distinguishable. Bench and Keep
    out marks are never consumed: they are standing state."""
    at = at or datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    by_id = {}
    for doc in docs:
        if (doc.get("card") or "").strip():
            by_id[image_slug(doc["card"])] = doc
    changed = {}
    for name, code, clear_pair in consumed:
        did = image_slug(name)
        doc = by_id.get(did)
        if not doc:
            continue
        e = changed.setdefault(did, {"id": did, "card": doc["card"], "picks": list(doc.get("picks") or []),
                                     "pair": dict(doc.get("pair") or {}), "done": list(doc.get("done") or [])})
        if code in e["picks"]:
            e["picks"].remove(code)
            e["done"].append({"v": code, "at": at})
        if clear_pair:
            e["pair"].pop(code[3:], None)
    return [e for did, e in sorted(changed.items())
            if e["picks"] != list(by_id[did].get("picks") or []) or e["pair"] != dict(by_id[did].get("pair") or {})]


def apply_log_entry(plans, log, at=None):
    """The record of one `apply --apply` run for the board's `log` collection: when, and what
    landed in each deck, so the owner reads on the board what changed and when."""
    at = at or datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    lines = []
    for did, pl in plans.items():
        lines += [f"{pl['label']}: −{c} +{a}" for c, a in pl["swaps"]]
        lines += [f"{pl['label']}: +{a}" for a in pl["adds"]] + [f"{pl['label']}: −{c}" for c in pl["cuts"]]
        lines += [f"{pl['label']}: protect {c}" for c in pl["protect"]]
        lines += [f"{pl['label']}: unprotect {c}" for c in pl["unprotect"] + pl["unprotect_cut"]]
        lines += [f"{pl['label']}: bench {c}" for c in pl["bench_add"]]
        lines += [f"{pl['label']}: bench line retired — " + ln.split("|")[0].replace("#~", "").strip()
                  for ln in pl["bench_retire"]]
    failed = [ln for ln in log if "FAILED" in ln or "stopped" in ln]
    return {"at": at, "lines": lines, "failed": failed}


def _post_checks(did):
    """One line each from the checks a hand-applied round ran: size and legality, printings,
    and the rationale audit."""
    def run(*a):
        r = subprocess.run([sys.executable, os.path.join(REPO_ROOT, "scripts", "deck.py"), *a],
                           capture_output=True, text=True, cwd=REPO_ROOT)
        return (r.stdout or "") + (r.stderr or "")
    legal = run("legal", did)
    size = next((ln.strip() for ln in legal.splitlines() if ln.startswith("Deck size")), "")
    issues = next((ln.strip() for ln in legal.splitlines() if "construction issue" in ln), "")
    printing = (run("resolve", "--check", did).strip().splitlines() or [""])[-1].strip()
    audit = [ln.strip() for ln in run("tier", did, "--audit-rationale").splitlines() if "⚠" in ln or "✓" in ln]
    return [f"{did}: {size}" + (f" · {issues}" if issues else ""), f"{did}: {printing}"] + \
           [f"{did}: {a}" for a in audit]


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
    cfmt = D.normalize_format(meta.get("format"))
    return {"id": did, "name": d["name"], "cmd": meta.get("commander"), "size": vec.get("size"),
            # the format's size: exact for a singleton (Brawl) deck, a minimum otherwise —
            # the deck panel counts the cuts still to make against it
            "target": 100 if cfmt in D.BIG_DECK_FORMATS else 60, "exact": cfmt in D.SINGLETON_FORMATS,
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
    verdicts, hashes = build.get("verdicts", {}), current_hashes(build)
    names_now = current_names(build)
    ids = {d["key"]: d["id"] for d in build["decks"]}
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
        vv = verdicts.get(n, {})
        rec["vd"] = {k: x["m"] for k, x in vv.items() if k in live}
        rec["vs"] = {k: ("pre" if x.get("graded_at") is None else
                         "stale" if verdict_stale(build, n, ids[k], x["graded_at"], hashes, names_now) else "")
                     for k, x in vv.items() if k in live}
        out.append(rec)
    return {"cards": out,
            "meta": {"title": build.get("title"), "groups": build.get("groups", {}),
                     "verdicts": [[m, VERDICT_LABEL[m]] for m in VERDICTS],
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


BACK_KEY = "back:"   # images.json key prefix for a two-faced card's back face


def back_image_urls(slug, names, fetch=True, two_faced=()):
    """{name: Scryfall `normal` URL of the BACK face} for the two-faced cards among `names`.

    `image_urls` keeps only the front face: Scryfall puts a transform or modal DFC's
    images under `card_faces`, and the front is all a row thumbnail needs. The back is
    a different card face, so the pane and the zoom view need it too. A split, Adventure
    or Room card shares one image with both halves on it, and is cached as "" (no separate
    back) so it is not looked up again. Candidates are names with " // " plus `two_faced`:
    a card the build stores under its FRONT name only ("Trystan, Callous Cultivator") has no
    " // " in its name, so the caller passes the names whose TYPE line has one (2026-11-03 —
    the owner found Trystan's and Ultimecia's backs missing on the board). Cached in
    the same images.json under `back:<name>`; an outage leaves the cache as it was."""
    cache_path = os.path.join(os.path.dirname(build_path(slug)), "images.json")
    try:
        cache = json.load(open(cache_path, encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    two = set(two_faced)
    cand = [n for n in dict.fromkeys(names) if " // " in n or n in two]
    need = [n for n in cand if BACK_KEY + n not in cache]
    if need and fetch:
        try:
            import scryfall
            for i in range(0, len(need), 70):
                batch = need[i:i + 70]
                got = {}
                for d in scryfall.post_collection([n.split(" // ")[0] for n in batch]).get("data", []):
                    faces = d.get("card_faces") or []
                    back = ""
                    if not d.get("image_uris") and len(faces) > 1:
                        back = (faces[1].get("image_uris") or {}).get("normal", "")
                    got[d["name"].lower()] = got[d["name"].lower().split(" // ")[0]] = back
                for n in batch:
                    k = n.lower()
                    if k in got or k.split(" // ")[0] in got:
                        cache[BACK_KEY + n] = got.get(k, got.get(k.split(" // ")[0], ""))
            atomic_write(cache_path, lambda fh: fh.write(json.dumps(cache, indent=1, sort_keys=True) + "\n"),
                         backup=False)
        except Exception as e:  # an outage degrades to a front-only card, never a failed render
            print(f"builder: Scryfall back-face lookup skipped ({e})", file=sys.stderr)
    return {n: cache[BACK_KEY + n] for n in cand if cache.get(BACK_KEY + n)}


_ART_FX = {"showcase": "showcase", "extendedart": "extended art", "etched": "etched",
           "textless": "textless"}   # the treatments a reader would call a different look
ART = (366, 267)            # an art-crop cell: 3x the pane's 122 x 89 thumbnail, 1x when enlarged
ART_COLS, ART_PER_SHEET = 6, 60


def printing_arts(slug, names, fetch=True):
    """{name: [printing, …]} — every Arena printing with a DIFFERENT illustration, oldest
    first, for the cards that have more than one. View-only: the owner picks the art in
    Arena; nothing here touches a deck line (the project keys one printing per card and an
    unknown set code is a hard INV-04 failure).

    Scryfall's `unique:art` keeps one printing per illustration, so a frame-only variant —
    Arena's borderless "see-through text box" treatment of the same art — collapses into
    the original and is never listed. Cached in `builds/<slug>/printings.json` (committed,
    so the offline Pages job has it); a card with one art is cached as [] so it is not
    looked up again. An outage leaves the cache as it was."""
    path = os.path.join(os.path.dirname(build_path(slug)), "printings.json")
    try:
        cache = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    need = [n for n in dict.fromkeys(names) if n not in cache]
    if need and fetch:
        try:
            import urllib.parse
            import scryfall
            oid = {}
            for i in range(0, len(need), 70):
                for d in scryfall.post_collection([n.split(" // ")[0] for n in need[i:i + 70]]).get("data", []):
                    oid[d["name"].lower()] = d["oracle_id"]
            alias_front(oid)                       # second pass, never in-pass (G-63)
            want = {n: oid.get(n.lower()) or oid.get(n.lower().split(" // ")[0]) for n in need}
            ids = sorted({v for v in want.values() if v})
            by_oid = {}
            for i in range(0, len(ids), 12):       # a longer OR list overflows the URL (HTTP 400)
                q = "game:arena unique:art (" + " or ".join(f"oracleid:{x}" for x in ids[i:i + 12]) + ")"
                url = "https://api.scryfall.com/cards/search?" + urllib.parse.urlencode({"q": q, "order": "released", "dir": "asc"})
                while url:
                    r = scryfall.get_json(url)
                    for d in r.get("data", []):
                        iu = d.get("image_uris") or ((d.get("card_faces") or [{}])[0].get("image_uris")) or {}
                        by_oid.setdefault(d["oracle_id"], []).append({
                            "set": d["set"].upper(), "cn": d["collector_number"], "sn": d.get("set_name", ""),
                            "r": (d.get("rarity") or "?")[:1].upper(), "y": (d.get("released_at") or "")[:4],
                            "a": d.get("artist", ""), "art": iu.get("art_crop", ""), "im": iu.get("normal", ""),
                            "fx": sorted((set(_ART_FX.get(x, "") for x in (d.get("frame_effects") or []))
                                          | ({"borderless"} if d.get("border_color") == "borderless" else set())
                                          | ({"full art"} if d.get("full_art") else set())) - {""})})
                    url = r.get("next_page")
            for n, o in want.items():
                if o:
                    arts = by_oid.get(o, [])
                    cache[n] = arts if len(arts) > 1 else []
        except Exception as e:  # an outage leaves the cache as it was
            print(f"builder: Scryfall printings lookup skipped ({e})", file=sys.stderr)
        atomic_write(path, lambda fh: fh.write(json.dumps(cache, indent=1, sort_keys=True, ensure_ascii=False) + "\n"),
                     backup=False)
    return {n: cache[n] for n in names if cache.get(n)}


def _art_sprites(out_dir, arts):
    """Every alternate art as a cell in a few sheets (`img/arts-<n>.jpg`), so the artifact
    stays under its 511-file ceiling. Returns {"cols", "w", "h", "sheets", "i": {key: [sheet,
    cell]}} with key = "<card slug>|<SET>|<cn>"."""
    import io
    import urllib.request
    from PIL import Image
    w, h = ART
    cells = [(f"{image_slug(n)}|{p['set']}|{p['cn']}", p["art"]) for n, ps in arts.items() for p in ps if p.get("art")]
    cache_dir = os.path.join(out_dir, "img", "art")
    os.makedirs(cache_dir, exist_ok=True)
    out = {"cols": ART_COLS, "w": w, "h": h, "sheets": [], "rows": [], "i": {}}
    for s0 in range(0, len(cells), ART_PER_SHEET):
        chunk = cells[s0:s0 + ART_PER_SHEET]
        rows = -(-len(chunk) // ART_COLS)
        sheet = Image.new("RGB", (w * ART_COLS, h * rows), (40, 40, 40))
        for j, (key, url) in enumerate(chunk):
            f = os.path.join(cache_dir, re.sub(r"[^A-Za-z0-9-]+", "_", key) + ".jpg")
            try:
                if not os.path.exists(f):
                    req = urllib.request.Request(url, headers={"User-Agent": "mtga-card-library/1.0", "Accept": "image/*"})
                    im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")
                    im.resize(ART, Image.LANCZOS).save(f, "JPEG", quality=82)
                sheet.paste(Image.open(f).convert("RGB"), ((j % ART_COLS) * w, (j // ART_COLS) * h))
                out["i"][key] = [len(out["sheets"]), j]
            except Exception as e:
                print(f"builder: art for {key} not fetched ({e})", file=sys.stderr)
        name = f"img/arts-{len(out['sheets'])}.jpg"
        sheet.save(os.path.join(out_dir, name), "JPEG", quality=82, optimize=True, progressive=True)
        out["sheets"].append(name)
        out["rows"].append(rows)
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


def render(slug, target, out_dir, tempo=True, images=True, data=None, page_name="index.html",
           fetch=True, home=None):
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
    if home:
        meta["home"] = home              # the page's link back (the dashboard, on Pages)
    cmds = {k: v.get("cmd") for k, v in meta["live"].items() if v.get("cmd")}
    urls = image_urls(slug, [c["n"] for c in data["cards"]] + list(cmds.values()),
                      fetch=fetch and (images or target == "pages"))
    arts = printing_arts(slug, [c["n"] for c in data["cards"]], fetch=fetch)
    backs = back_image_urls(slug, [c["n"] for c in data["cards"]],
                            fetch=fetch and (images or target == "pages"),
                            two_faced=[c["n"] for c in data["cards"] if " // " in (c.get("t") or "")])
    for c in data["cards"]:
        if arts.get(c["n"]):
            c["al"] = arts[c["n"]]          # alternate Arena printings (view-only)
    if target == "pages":
        for c in data["cards"]:
            if urls.get(c["n"]):
                c["im"] = urls[c["n"]]
            if backs.get(c["n"]):
                c["im2"] = backs[c["n"]]        # the back face of a two-faced card
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
        for c in data["cards"]:
            u = backs.get(c["n"])
            if not u:
                continue
            try:
                _fetch_image(u.replace("/normal/", "/large/"),
                             os.path.join(out_dir, "img", "lg", image_slug(c["n"]) + "--back.jpg"), LARGE)
                c["b2"] = 1                     # img/lg/<id>--back.jpg is on disk
            except Exception as e:
                print(f"builder: back face for {c['n']} not fetched ({e})", file=sys.stderr)
    if target == "artifact":
        meta["sprite"] = _sprite(out_dir, [image_slug(n) for n in urls]) if images else None
        meta["arts"] = _art_sprites(out_dir, arts) if images and arts else None
    import html as _html
    title = meta.get("title") or slug
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = open(TEMPLATE, encoding="utf-8").read()
    page = page.replace("__TITLE__", _html.escape(title), 1).replace("__DATA__", blob, 1)
    if target == "pages":
        page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                + page + "\n</html>\n")
    out = os.path.join(out_dir, page_name)
    atomic_write(out, lambda fh: fh.write(page), backup=False)
    return {"page": out, "cards": len(data["cards"]), "images": len(urls),
            "fetched": got, "image_errors": missing,
            "no_image": sorted(set(c["n"] for c in data["cards"]) - set(urls))}


# ---------------------------------------------------------------- Pages site
# ---------------------------------------------------------------- publish plan
# A claude.ai board is a page plus image files (img/lg/*.jpg, img/thumbs.jpg, img/arts-*.jpg).
# Republishing index.html alone left new cards with no picture and the thumbnail sprite out of
# step with the page's sprite map (found 2026-11-04: 16 new cards had no image, and the sprite
# on the board was the previous layout). `publish_plan` lists exactly what changed since the
# last publish, recorded in <out>/.published.json, so each republish sends those files.
PUBLISHED = ".published.json"


def _file_sig(path):
    with open(path, "rb") as fh:
        return f"{os.path.getsize(path)}:{hashlib.sha1(fh.read()).hexdigest()[:16]}"


_SITE_FILE = re.compile(r"^(index\.html|img/thumbs\.jpg|img/arts-\d+\.jpg|img/lg/[^/]+\.jpg)$")


def site_files(out_dir):
    """{published path: signature} for the files `render` writes for an artifact board
    (index.html, the thumbnail and art sprites, the large images); leftovers of an older
    layout in the same folder are not part of the board and are ignored."""
    out = {}
    for root, _dirs, files in os.walk(out_dir):
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, out_dir).replace(os.sep, "/")
            if _SITE_FILE.match(rel):
                out[rel] = _file_sig(full)
    return out


def publish_plan(out_dir, mark=False):
    """(changed, removed): paths to send and paths to drop since the last recorded publish.
    `mark` records the current files as published; run it after the publish succeeds."""
    now = site_files(out_dir)
    rec = os.path.join(out_dir, PUBLISHED)
    before = {}
    if os.path.exists(rec):
        with open(rec, encoding="utf-8") as fh:
            before = json.load(fh)
    changed = sorted(p for p, s in now.items() if before.get(p) != s)
    removed = sorted(p for p in before if p not in now)
    if mark:
        with open(rec, "w", encoding="utf-8") as fh:
            json.dump(now, fh, indent=0, sort_keys=True)
    return changed, removed


def _offline():
    """No network during a site build: the Pages job runs offline (like build_dashboard's
    `_no_network`), so deck.py's live-Scryfall fallbacks are neutralised and image URLs
    come from each build's committed images.json cache only."""
    D = _deck()
    D.fetch_missing_mana = lambda names, mana: mana
    D.fetch_missing_rarities = lambda names, rar: rar


PICKER = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Deck Builder</title>
<script>(function(){ try{ var p=JSON.parse(localStorage.getItem("mtga-prefs")||"{}")||{}; if(p.theme==="light"||p.theme==="dark") document.documentElement.setAttribute("data-theme",p.theme); }catch(e){} })();</script>
<style>
:root{ --bg:#f2f3f1; --panel:#ffffff; --ink:#161a18; --muted:#5b6660; --line:#dce1dd; --accent:#0e6b62; --brass:#8f7034; color-scheme: light; }
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){ --bg:#0e1211; --panel:#151b19; --ink:#e5eae7; --muted:#93a099; --line:#26302c; --accent:#45bcae; --brass:#c8a35a; color-scheme: dark; } }
:root[data-theme="dark"]{ --bg:#0e1211; --panel:#151b19; --ink:#e5eae7; --muted:#93a099; --line:#26302c; --accent:#45bcae; --brass:#c8a35a; color-scheme: dark; }
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:860px;margin:0 auto;padding:24px 16px 48px}
h1{font:400 1.9rem/1.2 Georgia,serif;letter-spacing:.04em;margin:0 0 4px}
p.sub{color:var(--muted);margin:0 0 18px}
a{color:var(--accent)} a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
ul{list-style:none;padding:0;margin:0;display:grid;gap:10px}
li{background:var(--panel);border:1px solid var(--line);border-top:2px solid var(--brass);border-radius:6px;padding:12px 14px}
li a.t{font:600 1.1rem/1.3 Georgia,serif;text-decoration:none}
li .m{color:var(--muted);font-size:.9rem;margin-top:2px}
.empty{color:var(--muted);font-style:italic}
</style>
</head>
<body>
<main>
<p><a href="__HOME__">← Dashboard</a></p>
<h1>Deck Builder</h1>
<p class="sub">Each project is a pile of candidate cards beside the decks it is for. Picks and notes stay in this browser; copy them out from <b>Your picks</b> and paste them to Claude.</p>
__LIST__
</main>
</body>
</html>
"""


def site(out_dir, tempo=True, home="index.html"):
    """Render every build for GitHub Pages: `<out>/builds/<slug>.html` (self-contained, data
    inline, images hot-linked from Scryfall), `<out>/builds/index.json` (the project list)
    and `<out>/builder.html` (the picker). Offline. A build that fails to render is left
    out of the index and reported; returns (projects, failures)."""
    import html as _html
    _offline()
    projects, failures = [], []
    bdir = os.path.join(out_dir, "builds")
    for slug in all_builds():
        try:
            b = load_build(slug)
            r = render(slug, "pages", bdir, tempo=tempo, page_name=f"{slug}.html", fetch=False,
                       home="../" + home)
            projects.append({"slug": slug, "title": b.get("title") or slug,
                             "decks": [{"id": d["id"], "label": d.get("label") or d["id"]} for d in b["decks"]],
                             "cards": len(b["cards"]), "reasons": len(b.get("reasons", {})),
                             "page": f"builds/{slug}.html", "no_image": len(r["no_image"]),
                             "refreshed": datetime.date.today().isoformat()})
        except Exception as e:  # one bad project must not take the others down
            failures.append(f"{slug}: {type(e).__name__}: {e}")
    os.makedirs(bdir, exist_ok=True)
    atomic_write(os.path.join(bdir, "index.json"),
                 lambda fh: fh.write(json.dumps({"projects": projects}, indent=1) + "\n"), backup=False)
    items = "".join(
        f'<li><a class="t" href="{_html.escape(p["page"])}">{_html.escape(p["title"])}</a>'
        f'<div class="m">{" · ".join(_html.escape(d["label"]) + " (deck " + _html.escape(d["id"]) + ")" for d in p["decks"])}'
        f' · {p["cards"]} cards · {p["reasons"]} reasons</div></li>' for p in projects)
    page = PICKER.replace("__HOME__", _html.escape(home)).replace(
        "__LIST__", f"<ul>{items}</ul>" if items else '<p class="empty">No builder projects yet.</p>')
    atomic_write(os.path.join(out_dir, "builder.html"), lambda fh: fh.write(page), backup=False)
    return projects, failures


def summaries():
    """Light per-project facts for the dashboard (no derivation): title, decks, counts."""
    out = []
    for slug in all_builds():
        b = load_build(slug)
        out.append({"slug": slug, "title": b.get("title") or slug,
                    "decks": [{"id": d["id"], "label": d.get("label") or d["id"]} for d in b["decks"]],
                    "cards": len(b["cards"]), "reasons": len(b.get("reasons", {})),
                    "page": f"builds/{slug}.html"})
    return out


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
    p = sub.add_parser("add-deck", help="add a deck (and its pile) to an existing build")
    p.add_argument("slug"); p.add_argument("id"); p.add_argument("--key"); p.add_argument("--label")
    p = sub.add_parser("place", help="move a card to a pile")
    p.add_argument("slug"); p.add_argument("card"); p.add_argument("pile")
    p = sub.add_parser("reason", help="record why a card is or is not in a deck")
    p.add_argument("slug"); p.add_argument("card"); p.add_argument("--text", required=True)
    p.add_argument("--group", default="")
    p = sub.add_parser("hidden", help="record a role the card plays that the classifier does not count")
    p.add_argument("slug"); p.add_argument("card")
    p.add_argument("--role", required=True, choices=["interaction", "card-advantage"])
    p.add_argument("--remove", action="store_true")
    p = sub.add_parser("verdict", help="record a card's verdict for one deck (★★★ ★★ ★ ◇ △ ✗), or many with --file")
    p.add_argument("slug"); p.add_argument("card", nargs="?"); p.add_argument("deck", nargs="?")
    p.add_argument("mark", nargs="?", help="★★★ ★★ ★ ◇ △ ✗ (or 3 2 1 s m x); - clears it")
    p.add_argument("--file", help="lines of card<TAB>deck<TAB>mark; - for stdin")
    p.add_argument("--pre", action="store_true",
                   help="graded before the deck existed in its current form (an import): shown as pre-draft")
    p = sub.add_parser("check", help="stale reasons, unresolved names, unplaced cards")
    p.add_argument("slug"); p.add_argument("--strict", action="store_true",
                                           help="exit 1 when anything is stale or unresolved")
    p = sub.add_parser("picks", help="turn the board's copied picks into swap --package lines")
    p.add_argument("slug"); p.add_argument("file", nargs="?", default="-")
    p = sub.add_parser("apply", help="apply the board's picks to the deck files (dry run unless --apply)")
    p.add_argument("slug"); p.add_argument("file", nargs="?",
                                           help="a Copy as text block (- for stdin); omit with --db")
    p.add_argument("--db", help="a dump of the board's database (the folder ArtifactData writes with out_dir)")
    p.add_argument("--apply", action="store_true", help="write the edits (default: print the plan)")
    p.add_argument("--retire-bench", action="store_true",
                   help="also remove this build's #~ bench lines whose card is no longer benched on the board")
    p.add_argument("--cleanup", help="with --db: where to write the board cleanup file (default: <dump>/cleanup.json)")
    p = sub.add_parser("derive", help="print the page data (cards + live deck stats) as JSON")
    p.add_argument("slug"); p.add_argument("--out")
    p.add_argument("--no-tempo", action="store_true", help="skip the tapped-land simulation (faster)")
    p = sub.add_parser("render", help="write the page (template + derived data) for pages or a claude.ai artifact")
    p.add_argument("slug"); p.add_argument("--target", choices=TARGETS, required=True)
    p.add_argument("--out", required=True, help="output directory (index.html, and img/ for artifact)")
    p.add_argument("--no-tempo", action="store_true", help="skip the tapped-land simulation (faster)")
    p.add_argument("--no-images", action="store_true", help="artifact: do not download images")
    p = sub.add_parser("publish-plan", help="list a rendered board's files changed since its last publish")
    p.add_argument("out", help="the render's output directory (e.g. .cycle/board)")
    p.add_argument("--mark", action="store_true", help="record the current files as published (after publishing)")
    p = sub.add_parser("site", help="render every build for GitHub Pages (offline): builder.html + builds/")
    p.add_argument("--out", required=True, help="the site directory (e.g. _site)")
    p.add_argument("--no-tempo", action="store_true", help="skip the tapped-land simulation (faster)")
    args = ap.parse_args(argv)
    if args.cmd == "site":
        projects, failures = site(args.out, tempo=not args.no_tempo)
        print(f"Wrote {args.out}/builder.html and {len(projects)} project page(s): "
              + ", ".join(p["slug"] for p in projects))
        for p in projects:
            if p["no_image"]:
                print(f"WARN: builder {p['slug']}: {p['no_image']} card(s) have no cached image URL "
                      f"(run `builder.py render {p['slug']} --target pages` online to fill images.json)",
                      file=sys.stderr)
        for f in failures:
            print(f"WARN: builder project failed to render — {f}", file=sys.stderr)
        return 1 if failures else 0
    if args.cmd == "publish-plan":
        changed, removed = publish_plan(args.out, mark=args.mark)
        if args.mark:
            print(f"Recorded {len(site_files(args.out))} file(s) as published.")
            return 0
        print(f"{len(changed)} file(s) to send" + (f", {len(removed)} to remove" if removed else "") + ":")
        for x in changed:
            print(f"  {x}")
        for x in removed:
            print(f"  remove {x}")
        return 0
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
        elif args.cmd == "add-deck":
            k = add_deck(b, args.id, args.key, args.label)
            save_build(args.slug, b)
            print(f"Added deck {args.id} as {k} (pile {k})")
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
        elif args.cmd == "verdict":
            if args.file:
                text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
                rows = read_verdict_file(text)
            elif args.card and args.deck and args.mark:
                rows = [(args.card, args.deck, args.mark)]
            else:
                raise BuildError("give CARD DECK MARK, or --file")
            idx, hashes = _name_index(), current_hashes(b)
            for card, deck, mark in rows:          # validate everything before writing anything
                norm_verdict(mark) if mark.strip() not in ("-", "") else None
                deck_key_of(b, deck)
                if not _card_entry(b, resolve_name(card, idx)):
                    raise BuildError(f"{card!r} is not in this build; add it first")
            for card, deck, mark in rows:
                set_verdict(b, card, deck, mark, pre=args.pre, _idx=idx, _hashes=hashes)
            save_build(args.slug, b)
            print(f"Recorded {len(rows)} verdict(s)" + (" (pre-draft)" if args.pre else ""))
        elif args.cmd == "check":
            issues = check_build(b)
            if not issues:
                print(f"{args.slug}: clean ({len(b['cards'])} cards, {len(b['reasons'])} reasons)")
            for sev, msg in issues:
                print(f"  {sev:10} {msg}")
            bad = any(s in ("stale", "unknown", "deck") for s, _ in issues)
            return 1 if (args.strict and bad) else 0
        elif args.cmd == "apply":
            if bool(args.db) == bool(args.file):
                raise BuildError("give the picks one way: --db <dump folder> or a Copy as text file (- for stdin)")
            docs = None
            if args.db:
                docs = read_db_dump(args.db)
                parsed = picks_from_db(b, docs)
            else:
                text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
                parsed = parse_picks(text)
            known = {d["id"] for d in b["decks"]}
            for did in parsed["decks"]:
                if did not in known:
                    print(f"# {did}: not a deck of this build — skipped")
            plans = plan_apply(b, parsed, args.slug, retire_bench=args.retire_bench)
            for line in _plan_lines(plans, parsed, args.slug):
                print(line)
            if not args.apply:
                if docs is not None:
                    n = len(cleanup_ops(docs, [c for pl in plans.values() for c in pl["consume"]]))
                    print(f"\n{n} board record(s) would have their settled marks cleared after --apply.")
                print("\n(dry run — pass --apply to write; each deck file gets a .bak)")
                return 0
            print()
            log, consumed = execute_apply(b, plans, args.slug)
            for line in log:
                print(line)
            if docs is not None:
                ops = cleanup_ops(docs, consumed)
                entry = apply_log_entry(plans, log)
                dest = args.cleanup or os.path.join(args.db if os.path.isdir(args.db) else os.path.dirname(args.db),
                                                    "cleanup.json")
                with open(dest, "w", encoding="utf-8") as fh:
                    json.dump({"picks": ops, "log": entry}, fh, indent=1, ensure_ascii=False)
                print(f"\nBoard cleanup: {len(ops)} record(s) and one log entry → {dest}. Write them to the "
                      "board now: `update` each `picks` record's picks, pair and done (settled marks move "
                      "to done, so the board shows them as history), and `set` the log entry in the `log` "
                      "collection under a new id, so an applied mark cannot come back as a pending pick.")
            else:
                print("\nThese picks came from copied text: on the page you copied them from, open "
                      "Your picks and press Clear applied marks.")
            for did, pl in plans.items():
                if any(pl[k] for k in ("swaps", "adds", "cuts", "protect", "unprotect", "unprotect_cut",
                                       "bench_add", "bench_retire")):
                    for line in _post_checks(did):
                        print(line)
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
