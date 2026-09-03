#!/usr/bin/env python3
"""Manage constructed decks and their variations against your collection.

Decks live under decks/ as one folder per core deck, with variants as sibling
files:

    decks/
      01-avatar-tempo/
        deck.txt              # the base deck   -> id "1"
        1a-counter-heavy.txt  # a variation     -> id "1a"
        1b-aggro-splash.txt   # another         -> id "1b"
        notes.md              # optional free-form notes

Each deck file is a full, self-contained list in Arena export format
(`<qty> <Name> (<SET>) <collector#>`), optionally preceded by a metadata header
whose lines start with `#:` — for example:

    #: name: Avatar Tempo
    #: format: Standard
    #: colors: WU
    #: archetype: Azorius (W/U) fliers / tempo   (one-line identity; `list` shows it)
    #: notes: removal-heavy base build   (free-form; may span several `#: notes:` lines)

    4 Katara, Bending Prodigy (TLA) 59
    ...

Plain `#` lines are comments; blank lines are ignored. Loose `decks/<name>.txt`
files (no folder) work too, with the filename as the id.

Commands:
    python3 scripts/deck.py list                # all decks + variants, buildable?
    python3 scripts/deck.py wildcards           # roster crafting plan (wildcards to finish)
    python3 scripts/deck.py check 1a            # owned vs needed vs your collection
    python3 scripts/deck.py diff 1 1a           # what the variant changes
    python3 scripts/deck.py arena 1a            # emit an Arena-importable list
    python3 scripts/deck.py stats 1a            # mana curve, colors, types, functional roles
    python3 scripts/deck.py mana 1a             # hybrid-aware color requirements + castability lint
    python3 scripts/deck.py suggest 1a --owned  # OWNED pool cards that fit the deck (0 wildcards)
    python3 scripts/deck.py legal 1a            # construction lint: size, copy limits, format legality
    python3 scripts/deck.py cuts 1a             # rank the deck's weakest-fit cards as cut candidates
    python3 scripts/deck.py swap 1a --cut A --add B   # preview a swap's deltas (--apply to write)
    python3 scripts/deck.py apply-flex 1a 2     # promote flex swap #2 into the maindeck

Mana analysis reads card-mana.csv (real mana costs, built by build_mana.py), so
hybrid {W/U} pips are counted as flexible rather than demanding both colors.
"""

import argparse
import csv
import json
import math
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request

import lib
from lib import (BASICS as lib_BASICS, DEFAULT_CSV, MATCHES_CSV, REPO_ROOT,
                 load_rows, eprint, card_colors, owned_qty,
                 card_distinctiveness, backup_path, card_power, front_face_cost,
                 mana_value, primary_type, atomic_write, alias_front,
                 land_production)
from scryfall import post_collection, ScryfallUnavailable

POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")

DECKS_DIR = os.path.join(REPO_ROOT, "decks")
MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")
BASICS = lib_BASICS          # one definition, in lib.py


def _file_memo(*path_names):
    """Memoize a zero-arg reference-table loader on its source files' (mtime_ns, size).

    The reference tables (mana / card data / collection / meta / keywords) were read
    from CSV on EVERY call, and a roster-wide pass calls them once per deck: 65 decks
    x ~0.31s of re-parsing was ~21s of the integrity gate's runtime, and it is why a
    roster-wide rationale sweep looked too expensive to run automatically — which is
    exactly the check that then never ran, and let 13 stale figures accumulate. With
    this, check_all goes 23s -> 4s and the sweep becomes affordable.

    Takes the module-global NAMES of the source files, not their values, and resolves
    them per call. `check_suggest`'s wiring anchor repoints `deck.POOL_CSV` at a
    synthetic pool, and a path captured at decoration time would key the cache on the
    REAL file while the loader body read the synthetic one — a stale-cache bug in the
    one check whose entire job is catching wiring mistakes. The resolved path is part
    of the key, so repointing invalidates.

    Keyed on (mtime_ns, size) rather than held forever, so a rebuild (`build_mana.py`,
    an `app.py` write) invalidates it inside a long-running process.

    THE RESULT IS SHARED AND MUST BE TREATED AS READ-ONLY. This docstring used to claim
    that every caller already did, "verified by scanning all of scripts/" — and the scan
    had missed five call sites in this very file: `fetch_missing_mana` and
    `fetch_missing_rarities` MUTATE the dict they are handed, and `cmd_stats`, `cmd_mana`,
    `cmd_consistency`, `_do_swap` and `cmd_wildcards` were handing them the cached object
    (broad-scan BS5-13). Benign on a one-shot CLI run; visible in the Flask editor, which
    serves many decks from one process, where deck B's Stats tab then computed its curve
    from costs deck A's Mana tab had live-fetched and disagreed with a fresh `deck.py
    stats B`. Those five now pass `dict(load_*())`.

    So: if you need to mutate one, COPY IT FIRST — and note that a claim about all callers
    is only as good as the last person who added one. `tests/test_deck.py`'s
    TestMemoizedTablesAreNotMutated pins the property behaviourally instead.
    """
    def deco(fn):
        cache = {}

        def stamp(name):
            path = globals().get(name)
            try:
                st = os.stat(path)
            except (OSError, TypeError):
                return (path, None)
            # ns, not getmtime()'s float seconds: app.py can rewrite a CSV twice
            # within one mtime tick, and a same-size rewrite would then serve stale.
            return (path, st.st_mtime_ns, st.st_size)

        def wrapped():
            key = tuple(stamp(n) for n in path_names)
            if cache.get("key") != key:
                cache["key"], cache["val"] = key, fn()
            return cache["val"]

        wrapped.__name__, wrapped.__doc__ = fn.__name__, fn.__doc__
        wrapped.cache_clear = cache.clear
        return wrapped
    return deco

# Formats the pool's Legalities column can carry (mirrors build_pool.py). Used to
# filter `suggest` to a deck's format so craft picks are legal to play/acquire.
POOL_FORMATS = {"standard", "pioneer", "modern", "legacy", "vintage", "pauper",
                "historic", "timeless", "alchemy", "explorer", "brawl"}

# Arena wildcard tiers. A card's Rarity == the wildcard needed to craft a copy.
WC_LETTER = {"common": "C", "uncommon": "U", "rare": "R", "mythic": "M"}
WC_NAMES = [("M", "Mythic"), ("R", "Rare"), ("U", "Uncommon"),
            ("C", "Common"), ("?", "Unknown")]

# "4 Card Name" / "4x Card Name", optional "(SET)" and collector number.
LINE_RE = re.compile(r"^\s*(\d+)\s*[xX]?\s+(.+?)\s*(?:\(([^)]+)\)\s*([^\s]+)?)?\s*$")
# A HYPHEN is legal in a `#:` key. It was not, and the deck files had been using one
# anyway: 24 `#: based-on:` lines across the roster were silently dropped — the line
# matched no meta key, fell through to the card-line branch, matched no card either, and
# vanished without a warning. Nothing read `based-on`, so nothing noticed. Found while
# adding `#: uncastable-ok:` (F-02), whose key has the same shape. Nothing iterates meta
# keys (only named lookups), so widening this adds keys without changing any output.
META_RE = re.compile(r"^#:\s*([A-Za-z_][A-Za-z_-]*)\s*:\s*(.*)$")

# Game-type (format) variant filenames: `<core>-<format>[-slug].txt`. These get the
# id `<core>-<format>` so a Brawl/Alchemy adaptation of a core deck reads as *that
# deck's* Brawl/Alchemy version, distinct from a Standard sub-variant (3a). The format
# token here is only for the id/organization; the deck's `#: format:` header remains the
# authoritative format for the legality/rotation tooling.
_FORMAT_SLUGS = ("alchemy", "historic-brawl", "brawl", "timeless", "explorer",
                 "pioneer", "modern", "pauper", "historic")
FORMAT_VARIANT_RE = re.compile(r"^(\d+)-(" + "|".join(_FORMAT_SLUGS) + r")(?:[-.])", re.I)


# --------------------------------------------------------------------------- #
# Deck discovery + parsing
# --------------------------------------------------------------------------- #
def parse_deck_file(path):
    """Return (meta_dict, [(qty, name, set, collector), ...]).

    A repeated `#:` key (notably a multi-line `#: notes:` block) is concatenated
    in order rather than overwritten, so the FULL note survives — previously only
    the last `#: notes:` line was kept, which truncated a deck's documented intent
    to a mid-sentence fragment in every tool that reads it."""
    meta, cards = {}, []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            m = META_RE.match(raw.strip())
            if m:
                key, val = m.group(1).lower(), m.group(2).strip()
                if key in meta and meta[key] and val:
                    meta[key] = f"{meta[key]} {val}"
                elif key not in meta or val:
                    meta[key] = val
                continue
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            cm = LINE_RE.match(line)
            if cm:
                cards.append((int(cm.group(1)), cm.group(2).strip(),
                              (cm.group(3) or "").strip(), (cm.group(4) or "").strip()))
    return meta, cards


# Stray block markers an Arena paste carries ("Deck", "Sideboard", …). Tolerated by
# `malformed_deck_lines` because 12 roster files hold a leftover `Deck` line and it is
# harmless — but ONLY these: anything else that fails LINE_RE is a card the deck
# silently isn't playing.
_STRAY_MARKERS = {"deck", "sideboard", "commander", "companion", "maybeboard", "about"}


def malformed_deck_lines(path):
    """[(lineno, text)] — non-blank, non-comment lines that are NEITHER a `#:` header,
    a card line, nor a tolerated Arena block marker. The MISSING channel of INV-04.

    `parse_deck_file` discards a line `LINE_RE` rejects with no record, so INV-04 —
    documented as "every deck file parses with no malformed card lines" — actually
    failed only when a file had ZERO parseable cards. `Lightning Bolt (DMU) 137`
    (quantity omitted, the most plausible hand-edit) or a BOM-prefixed line was
    silently deleted from the deck: `check` reported the remaining 59 buildable, the
    curve/tier floor graded a list that is not the file, and every gate stayed green
    (broad-scan BS2-14). The `(SET) COLLECTOR#` half of this exact function was
    hardened for G-65; this is the line-syntax half of the same sentence."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for i, raw in enumerate(fh, start=1):
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            line = s.split("#", 1)[0].strip()
            if not line or LINE_RE.match(line):
                continue
            if line.lower() in _STRAY_MARKERS:
                continue
            out.append((i, line))
    return out


def discover_decks():
    """Return a list of deck records: {id, name, path, core, variant}."""
    decks = []
    if not os.path.isdir(DECKS_DIR):
        return decks
    for entry in sorted(os.listdir(DECKS_DIR)):
        full = os.path.join(DECKS_DIR, entry)
        if os.path.isdir(full):
            m = re.match(r"^(\d+)-(.+)$", entry)
            core = str(int(m.group(1))) if m else entry
            for fn in sorted(os.listdir(full)):
                if not fn.endswith(".txt"):
                    continue
                p = os.path.join(full, fn)
                if fn == "deck.txt":
                    decks.append(_record(core, core, p, core, False))
                else:
                    # A GAME-TYPE variant — `<core>-<format>[-slug].txt` (e.g.
                    # 3-brawl-knights-edge.txt) gets the id `<core>-<format>` (e.g.
                    # `3-brawl`), so an Alchemy/Brawl adaptation of core deck 3 reads as
                    # deck 3's Brawl version, NOT as another Standard sub-variant like 3a.
                    fmv = FORMAT_VARIANT_RE.match(fn)
                    if fmv:
                        did = f"{int(fmv.group(1))}-{fmv.group(2).lower()}"
                    else:
                        vm = re.match(r"^(\d+)([a-z]+)-", fn)
                        # `str(int(...))` matches the core-id normalization above, so a
                        # zero-padded variant file cannot carry an id its core does not.
                        did = (f"{int(vm.group(1))}{vm.group(2)}" if vm
                               else os.path.splitext(fn)[0])
                    decks.append(_record(did, core, p, core, True))
        elif entry.endswith(".txt"):
            did = os.path.splitext(entry)[0]
            decks.append(_record(did, did, full, did, False))
    return decks


def _record(did, core, path, core_id, variant):
    meta, _ = parse_deck_file(path)
    return {"id": did, "name": meta.get("name", ""), "path": path,
            "core": core_id, "variant": variant, "meta": meta}


def _norm_deck_id(raw):
    """Canonical form of a deck id: strip a ZERO-PADDED numeric prefix.

    `discover_decks` derives a core id with `str(int(...))`, so the directory
    `06-dead-or-alive` yields id `6` — but ten deck directories are zero-padded ON DISK,
    so the id you read off an `ls` is exactly the one every by-id command rejected
    (`deck.py stats 06` -> "No deck with id '06'", while `6` works). Found 2026-09-01.
    Variant ids are normalized the same way, closing a latent asymmetry: the variant
    branch takes its digits RAW, so a file named `06a-….txt` would have carried id `06a`
    against a core of `6`. No such file exists today, which is why nothing caught it.
    """
    t = (raw or "").strip().lower()
    m = re.match(r"^0+(\d.*)$", t)
    return m.group(1) if m else t


def find_deck(deck_id):
    want = _norm_deck_id(deck_id)
    for d in discover_decks():
        if _norm_deck_id(d["id"]) == want:
            return d
    return None


# Decks that exist as documentation/placeholders rather than lists you'd sleeve up.
# A `#: status:` header naming one of these keeps the deck fully addressable by id —
# `check`, `stats`, `cuts`, the editor all still work on it — while dropping it from
# ROSTER-WIDE views, where it is pure noise. The example deck is a 26-card illustration
# of the file format, so it is permanently illegal: it sat at the top of `deck.py audit`
# occupying BOTH ★ TUNE slots, making the triage's most actionable output ("Full-tune
# candidates: 0, 0a") 100% false positive and permanently un-actionable (broad-scan
# F-06). It also counted as a deck a card could be "reused" in. `wishlist._theme_model`
# already excluded it by a card-count heuristic; this makes the intent explicit and
# shared, so every roster view agrees on what counts as part of the roster.
NONROSTER_STATUSES = {"example", "template", "placeholder", "retired", "archived"}


def deck_status(meta):
    """The `#: status:` keyword (lowercased first word), or '' when unset."""
    raw = (meta or {}).get("status", "") or ""
    return raw.strip().split()[0].strip().lower() if raw.strip() else ""


def is_roster_deck(d):
    """True when a deck should COUNT toward roster-wide views (audit / rotation / brawl /
    wildcards / cross-deck reuse / tier sweep). False for a documentation placeholder or a
    retired list. Never affects addressing a deck directly by id."""
    return deck_status(d.get("meta") or {}) not in NONROSTER_STATUSES


def roster_decks():
    """`discover_decks()` narrowed to the decks that are really part of the roster."""
    return [d for d in discover_decks() if is_roster_deck(d)]


# --------------------------------------------------------------------------- #
# Collection lookup
# --------------------------------------------------------------------------- #
@_file_memo("DEFAULT_CSV")
def load_collection():
    """Return (by_key, by_name, by_name_qty).

    by_key/by_name map to a representative row (for type/printing lookups);
    by_name_qty sums Quantity Owned across every printing of a name, since Arena
    copies are fungible across sets (see owned()).

    FRONT-FACE ALIASED, in a second pass (G-63). `lib.owned_qty` resolves the full
    `A // B` name down to a front-face key, which is the right direction for the
    library's stated convention — and that convention is not what the data actually
    holds. Eight rows are stored under the FULL name (the DSK Rooms, plus two DFCs),
    so a query by the FRONT name resolved to nothing and `deck.owned` reported an
    owned card as "NOT IN LIBRARY" — the exact string G-10 trains you to fix with
    `reconcile_crafts.py`, pointing at a card that is already there (broad-scan
    BS6-01). `import_collection.plan` and `reconcile_crafts` each discovered the
    exception and handled it locally; the SHARED join never did, and
    `check_agreement`'s ownership pair could not see it because both implementations
    agreed on the same wrong answer (0).

    `alias_front` adds a front key only where no real row already claims it, so a
    distinct card named `Front` is never shadowed by a DFC — the reason this is a
    second pass and not a `setdefault` inside the loop.
    """
    _, rows = load_rows(DEFAULT_CSV)
    by_key, by_name, by_name_qty = {}, {}, {}
    for r in rows:
        name = (r.get("Card Name") or "").strip()
        if not name:
            continue
        nl = name.lower()
        key = (nl, (r.get("Set Code") or "").strip().lower(),
               (r.get("Collector #") or "").strip().lower())
        by_key[key] = r
        by_name.setdefault(nl, r)
        q = (r.get("Quantity Owned") or "").strip()
        by_name_qty[nl] = by_name_qty.get(nl, 0) + (int(q) if q.isdigit() else 0)
    return by_key, alias_front(by_name), alias_front(by_name_qty)


_PIP_DEPTH_MIN = 2          # 2 pips are checked too, but against a STRICTER bar (below)
_PIP_DEPTH_TURN = 5         # grade on-curve-ish, capped like `consistency` does
_PIP_DEPTH_TARGET = 0.70    # below this, say so; deliberately looser than consistency's 0.90
# The bar is PIP-COUNT AWARE, and the two rows mean different things.
#
# 3+ pips at 0.70 is the original rule and is UNCHANGED: that band catches the
# arithmetically hopeless card (the {W}{W}{W}{W}{W} case in the docstring below).
#
# 2 pips joined the check after a {2}{B}{B} craft target was recommended into a deck
# holding EIGHT black sources — 45% on curve — and nothing said so, because the floor
# was 3. But 2 pips graded at 0.70 is far too loud: it fires on 109 maindecked cards
# across the roster against 25 today, and most of the additions are ordinary (a 2-pip
# card on 10-11 sources), which would train the reader to ignore the flag. At 0.55 it
# fires on 43 and isolates the real class — 2 pips on 3-9 sources. Measured 2026-08-13.
_PIP_DEPTH_TARGET_BY_PIPS = {2: 0.55}


def deck_color_sources(cards, meta, carddata):
    """{colour: number of LANDS in the deck producing it} — the same count `deck.py mana`
    and `consistency` print, via `deck_source_profile` (ONE implementation since BS8-01;
    this used to be a third copy that read colour identity alone, so every any-colour
    land counted as zero). `meta` is accepted for signature compatibility and used only
    as a colour fallback for a card `carddata` does not know.
    """
    src, _nlands, _total, _notes = deck_source_profile(cards, {}, {}, carddata, meta=meta)
    return src


def pip_depth_warning(cost, sources, total=None):
    """(colour, pips, have, want) when a card's DEEPEST single-colour pip demand is more
    than the deck's sources realistically support — else None.

    `suggest` / `suggest-homes` test castability as `card identity ⊆ deck colours`, which
    is a set question and cannot see DEPTH. That is how Anti-Venom, Horrifying Healer
    ({W}{W}{W}{W}{W}) was recommended as a KEY fit for two GWR decks holding 10 and 11
    white sources — about a 1% chance of casting it on turn five. Identity said yes; the
    arithmetic says never. Five pips wants roughly 33 sources for 85%, which no 60-card
    deck can reach, so this is genuinely un-castable rather than merely greedy.

    Reported as a FLAG, never a filter: a deep-pip card can still be a fine late-game
    play in a deck that leans hard on its colour, and the caller prints the numbers so a
    human decides. Hybrids are excluded (strictly easier), matching `parse_pips`.

    THE BAR IS PIP-COUNT AWARE (`_PIP_DEPTH_TARGET_BY_PIPS`). 3+ pips grade at 0.70,
    unchanged. 2 pips grade at 0.55, because the 3-pip floor let a {2}{B}{B} craft target
    be recommended into a deck with eight black sources — 45% on curve — and returned
    None. Read the two bands as different claims: a 3-pip flag says "you cannot cast
    this", a 2-pip flag says "you will cast this late".
    """
    strict, _hybrid = parse_pips(cost or "")
    if not strict:
        return None
    col, pips = max(strict.items(), key=lambda kv: kv[1])
    if pips < _PIP_DEPTH_MIN:
        return None
    have = sources.get(col, 0)
    seen = cards_seen(_PIP_DEPTH_TURN)
    # Deck SIZE is a parameter, not a constant 60 (broad-scan Batch G). The docstring
    # says this shares `consistency`'s model, and `cmd_consistency` reads the real
    # total (`N = total or 60`) while this hardcoded 60 in three places — so for a
    # 100-card Brawl list, which `cmd_suggest_homes` runs this over for every roster
    # deck, it badly OVERSTATED P: 14 sources / 3 pips / turn 5 is 50.2% at N=60 but
    # 18.2% at N=100, i.e. the flag was suppressed exactly where colour depth is
    # hardest. Latent today (every roster deck is 60), and `legality_report` already
    # contemplates min_size 100 for BIG_DECK_FORMATS.
    n = total or 60
    target = _PIP_DEPTH_TARGET_BY_PIPS.get(pips, _PIP_DEPTH_TARGET)
    if hypergeom_at_least(n, have, seen, pips) >= target:
        return None
    want = next((s for s in range(have + 1, 41)
                 if hypergeom_at_least(n, s, seen, pips) >= target), None)
    return (col, pips, have, want)


def owned(by_name_qty, name):
    """(count_owned, in_library) for a deck card.

    Basics count as unlimited. Copies are summed across ALL printings of a card,
    because an Arena playset is fungible regardless of set/collector number — a
    card owned 1x in one set and 1x in another counts as 2 toward a deck's needs
    (mirrors pool.py's owned_counts, which also sums across printings).
    """
    if name.lower() in BASICS:
        return 99, True
    nl = name.lower()
    if nl in by_name_qty:
        return by_name_qty[nl], True
    # DFC fallback. This used to be a bare `return 0, False`, on the documented
    # assumption that deck-file names are always FRONT-face by convention — an
    # assumption `deck.py resolve` falsifies, because it emits the full `A // B`
    # name (that is how the pool keys a DFC, and how Arena exports one). So a deck
    # built by `resolve` reported its own owned DFC as "NOT IN LIBRARY": deck 45a
    # said that about Norman Osborn the moment it was opened, while `lib.owned_qty`
    # resolved it correctly the whole time. Route through the shared helper rather
    # than re-implement the split — that is the A3/A4/F6 rule.
    # The front-face fallback, via the shared helper (the A3/A4/F6 rule). Membership,
    # NOT truthiness (BS6-07): `if qty` treated a stored count of a real 0 as ABSENT and
    # answered "not in library" for a card that IS in it — the exact string G-10 sends
    # you to `reconcile_crafts.py` about, pointing at a row already there. No library row
    # carries 0 today, but `import_collection --zero-missing` writes them and INV-01
    # permits them, at which point a single-faced 0 read "short" while a front/full 0
    # read "missing" — two spellings of one state. Same trap as `owned_qty`'s own `or`.
    qty = owned_qty(by_name_qty, name)
    return qty, (nl in by_name_qty or nl.split(" // ")[0] in by_name_qty)


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def _deck_identity(meta, width=92):
    """One-line 'meant-for' summary for `list`: the `#: archetype:` field if the
    deck declares one, else the first sentence of its `#: notes:`. '' if neither."""
    txt = (meta.get("archetype") or "").strip()
    if not txt:
        note = (meta.get("notes") or "").strip()
        txt = re.split(r"(?<=[.;])\s", note, 1)[0] if note else ""
    return (txt[:width - 1].rstrip() + "…") if len(txt) > width else txt


def cmd_list(_args):
    decks = discover_decks()
    if not decks:
        print("No decks yet. Add one under decks/<NN-name>/deck.txt "
              "(see decks/README.md).")
        return 0
    _, _, by_name_qty = load_collection()
    cores = {}
    for d in decks:
        cores.setdefault(d["core"], []).append(d)

    for core in sorted(cores, key=lambda c: (len(c), c)):
        group = sorted(cores[core], key=lambda d: (d["variant"], d["id"]))
        for d in group:
            _, cards = parse_deck_file(d["path"])
            total = sum(q for q, *_ in cards)
            # Through the ONE definition (G-70). This loop aggregated per name — the
            # rule — but keyed on the raw DISPLAY name while `deck_requirements` keys
            # lowercase, so two lines differing only in case would not have summed here
            # and would have summed in `check`. G-70 named three surfaces and
            # consolidated two; this was the third, still re-deriving (broad-scan BS5-04).
            # `missing` and `short` are also reported SEPARATELY now: this line used to
            # fold them into one "N short", so a card you own none of and a card you are
            # one copy short of read identically against a `check` that distinguishes them.
            missing, short = deck_build_gap(cards, by_name_qty)
            status = ("OK " if not (missing or short)
                      else ", ".join(x for x in ((f"{missing} missing" if missing else ""),
                                                 (f"{short} short" if short else "")) if x))
            label = d["name"] or os.path.basename(os.path.dirname(d["path"])) or d["id"]
            tag = "  └─ variant" if d["variant"] else "CORE"
            # `list` shows EVERY deck (it's the index), but marks the ones roster-wide
            # views skip so their absence from `audit`/`rotation`/`wildcards` isn't a
            # mystery.
            st = deck_status(d["meta"])
            mark = f"  [{st}]" if st in NONROSTER_STATUSES else ""
            print(f"  [{d['id']:>4}] {tag:12} {label:28} {total:3} cards  {status}{mark}")
            ident = _deck_identity(d["meta"])
            if ident:
                print(f"          {ident}")
    return 0


# --- wildcard (crafting) planning ------------------------------------------- #
@_file_memo("POOL_CSV")
def load_rarities():
    """name_lower -> wildcard letter (C/U/R/M) from card-pool.csv's Rarity.

    Memoized like every other reference-table loader. It was the ONE left out when
    `_file_memo` landed, and it is read per CARD-SCORING PASS rather than per command:
    `rank_cut_candidates` calls it for the power co-signal, so a full-pool re-parse ran
    for every deck a roster sweep touched. It was **85% of `deck.py cuts`' runtime**
    (0.69s of 0.81s) and, being invisible in any single command's wall clock, it only
    surfaced when a roster-wide gate made the per-deck cost add up.

    ANSWERS FOR A DFC'S FRONT FACE TOO, like every other reference-table loader
    (`load_card_data`, `load_mana`, `load_legalities`, `load_card_meta`,
    `_pool_rotation_index`). This one read the POOL, which keys only the full
    `Front // Back` name, and had no alias — so 47 distinct names across the live roster
    resolved to `""`, which is not an error anywhere: `cut_keep_score` hands the empty
    string to `_power_seed`, which falls to its default floor. Every mythic/rare DFC was
    therefore seeded as low-rarity and sorted UP the cut list — Ojer Axonil's
    `_cuts_power_adj` came out −0.70 where the real mythic gives +0.17, so the sign of
    the nudge flipped and the model treated a bomb as more cuttable. This is the SAME
    bug the note in `cut_keep_score` records as fixed for the rarity word-vs-letter
    shape (F-01); the front-face shape was never covered (broad-scan F-14).

    The alias is a SECOND PASS on purpose. Adding `out.setdefault(front, …)` inside the
    row loop would let a `Front // Back` row seen early shadow a real, distinct card
    named `Front` seen later — `"Life"` is a card as well as the front of
    `"Life // Death"`, the same trap `build_mana._front_face_retry` guards. Aliasing
    only after every real row is in the dict makes the result order-independent."""
    out = {}
    if not os.path.exists(POOL_CSV):
        return out
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            rar = (r.get("Rarity") or "").strip().lower()
            if n and rar:
                out.setdefault(n, WC_LETTER.get(rar, "?"))
    return alias_front(out)


def fetch_missing_rarities(names, rarities):
    """Live-fetch rarity for craft targets absent from the pool (e.g. non-Standard
    WIP cards). Degrades gracefully to '?' if Scryfall is unreachable."""
    todo = [n for n in names if n.lower() not in rarities]
    for i in range(0, len(todo), 75):
        chunk = todo[i:i + 75]
        try:
            data = post_collection(chunk)
        except ScryfallUnavailable as e:
            # A slow/flaky Scryfall (timeout, 5xx, bad body) must degrade to '?'
            # here, not crash — this helper exists precisely for the offline case.
            eprint(f"WARN:  could not reach Scryfall for rarity lookup ({e}); "
                   f"{len(todo) - i} card(s) will show wildcard '?'.")
            break
        for card in data.get("data", []):
            rar = WC_LETTER.get((card.get("rarity") or "").lower(), "?")
            full = card.get("name", "").lower()
            # REAL name only in-pass; the front alias is a second pass below. Aliasing
            # both with `setdefault` here let a live-fetched `Front // Back` claim the
            # bare front key, so a distinct card of that name fetched later could never
            # record its own rarity — the G-63 in-pass trap (BS4-18).
            rarities.setdefault(full, rar)
        time.sleep(0.1)
    return alias_front(rarities)


def _wc_breakdown(shortfalls, rar_of):
    """{wildcard letter: copies} for a list of (name, missing_copies)."""
    by = {}
    for name, miss in shortfalls:
        r = rar_of(name)
        by[r] = by.get(r, 0) + miss
    return by


def _wc_str(by):
    return " ".join(f"{by[r]}{r}" for r, _ in WC_NAMES if by.get(r))


def cmd_wildcards(args):
    """Roster-wide crafting plan: what to craft, and which crafts unlock the most
    decks. Owned copies are shared across decks and summed across printings, so a
    card is only ever short by (max any deck needs − total owned). `--dedup` prints
    the cross-deck UNION of craft targets ranked by decks-served-per-copy — the
    "most efficient next N crafts" question that was previously answered by hand
    each cycle (broad-implement #5)."""
    decks = roster_decks()   # a documentation placeholder must not demand wildcards
    if not decks:
        print("No decks yet. Add one under decks/<NN-name>/deck.txt.")
        return 0
    _fresh = lib.collection_stamp_note()
    if _fresh:
        print(_fresh + "\n")
    _, _, by_name_qty = load_collection()
    # COPY — `fetch_missing_rarities` below mutates the dict it is given, and
    # `load_rarities` is `@_file_memo`-cached (BS5-13, same class as the `load_mana`
    # copies; see the note at `cmd_stats`).
    rarities = dict(load_rarities())

    deck_short = {}       # deck id -> [(name, missing_copies)]
    max_need = {}         # name_lower -> max copies any single deck needs
    display = {}          # name_lower -> display name
    needed_by = {}        # name_lower -> set(deck ids short on it)
    for d in decks:
        _, cards = parse_deck_file(d["path"])
        need = {}
        for q, n, s, c in cards:
            if n.lower() in BASICS:
                continue  # basics are free/unlimited in Arena
            need[n] = need.get(n, 0) + q
        shorts = []
        for n, req in need.items():
            nl = n.lower()
            display[nl] = n
            max_need[nl] = max(max_need.get(nl, 0), req)
            have, _ = owned(by_name_qty, n)
            miss = max(0, req - have)
            if miss > 0:
                shorts.append((n, miss))
                needed_by.setdefault(nl, set()).add(d["id"])
        deck_short[d["id"]] = shorts

    # Resolve rarities for every craft target (pool first, live fallback).
    short_names = sorted({n for shorts in deck_short.values() for n, _ in shorts})
    if short_names:
        fetch_missing_rarities(short_names, rarities)
    rar_of = lambda name: rarities.get(name.lower(), "?")
    pool_rot, _ = _pool_rotation_index()

    if getattr(args, "dedup", False):
        # Cross-deck union: one row per distinct craft target. copies = what the
        # SHARED collection is short (max any single deck needs − owned), decks =
        # every deck advanced by owning it. Sort: most decks served first, then
        # cheapest rarity, then name — 'value per wildcard', the ranking the four
        # 2026-08 craft-efficiency cycles derived by hand from #: notes: prose.
        rar_rank = {r: i for i, (r, _) in enumerate(WC_NAMES)}
        rows = []
        for nl, ids in needed_by.items():
            have, _f = owned(by_name_qty, display[nl])
            copies = max(0, max_need[nl] - have)
            if copies:
                rows.append((display[nl], rar_of(display[nl]), copies, sorted(ids, key=lambda x: (len(x), x))))
        rows.sort(key=lambda r: (-len(r[3]), rar_rank.get(r[1], 99), r[0]))
        print("Craft targets — cross-deck union (shared collection; most decks per copy first)\n")
        print(f"{'Copies':>6}  {'R':1}  {'Decks':>5}  Card")
        print("-" * 72)
        for name, rar, copies, ids in rows:
            rot = craft_rot_note(name, pool_rot)
            print(f"{copies:>6}  {rar:1}  {len(ids):>5}  {name}{rot}   [{', '.join(ids)}]")
        if not rows:
            print("  Nothing to craft — the whole roster is buildable. ✓")
        else:
            print(f"\n{len(rows)} distinct card(s). ⚠rot = rotates out of Standard this "
                  "year or next; spend those wildcards knowingly or not at all.")
        return 0

    # Per-deck: wildcards to finish, closest-to-done first.
    print("Roster crafting plan\n")
    print(f"{'Deck':>5}  {'Name':26}  Wildcards to finish")
    print("-" * 60)
    ordered = sorted(decks, key=lambda d: (sum(m for _, m in deck_short[d["id"]]),
                                           len(d["id"]), d["id"]))
    for d in ordered:
        shorts = deck_short[d["id"]]
        label = (d["name"] or d["id"])[:26]
        total = sum(m for _, m in shorts)
        if total == 0:
            print(f"{d['id']:>5}  {label:26}  buildable ✓")
        else:
            print(f"{d['id']:>5}  {label:26}  {total:2} copy(s):  "
                  f"{_wc_str(_wc_breakdown(shorts, rar_of))}")

    # Highest-leverage crafts: one craft, multiple decks unblocked.
    multi = sorted(((nl, ids) for nl, ids in needed_by.items() if len(ids) >= 2),
                   key=lambda kv: (-len(kv[1]), kv[0]))
    if multi:
        print("\nHighest-leverage crafts (one card, multiple decks):")
        for nl, ids in multi[:15]:
            decks_s = ", ".join(sorted(ids, key=lambda x: (len(x), x)))
            rot = craft_rot_note(display[nl], pool_rot)
            print(f"  {display[nl]} ({rar_of(display[nl])})  — {len(ids)} decks: {decks_s}{rot}")

    # Roster totals: one shared collection, so per card only max(0, maxneed-owned).
    roster = {}
    for nl, req in max_need.items():
        have, _ = owned(by_name_qty, display[nl])
        miss = max(0, req - have)
        if miss > 0:
            r = rar_of(display[nl])
            roster[r] = roster.get(r, 0) + miss
    print("\nTotal wildcards to make EVERY deck buildable (shared collection):")
    if roster:
        print("  " + "   ".join(f"{roster[r]} {name}" for r, name in WC_NAMES
                                if roster.get(r)))
        if roster.get("?"):
            print("  ('?' = rarity unresolved — rebuild card-pool.csv or check "
                  "Scryfall connectivity.)")
    else:
        print("  Nothing to craft — the whole roster is buildable. ✓")
    return 0


def _declared_colors(meta):
    """The deck's stated colors as a WUBRG set, from the `#: colors:` header."""
    return card_colors(meta.get("colors"))


def _deck_castable_colors(dmeta, cards, mana):
    """The colors a deck can actually CAST — the declared `#: colors:` if present,
    else derived from its nonland mana COSTS (never color identity, so off-color
    activated abilities don't widen it). Same rule `suggest` uses."""
    cols = _declared_colors(dmeta)
    if cols:
        return cols
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        entry = mana.get(n.lower())
        if entry and entry[0]:
            strict, hybrid = parse_pips(entry[0])
            # Only a TRUE multicolor hybrid ({W/U}) constrains castable colors; a
            # monocolor hybrid ({2/W}) or Phyrexian ({W/P}) is payable WITHOUT its
            # color, so it must not widen the deck's colors (audit F15; mirrors
            # suggest_scored line ~1401 and _castability's len(h) >= 2).
            cols |= set(strict) | {x for h in hybrid if len(h) >= 2 for x in h}
    return cols


BASIC_COLOR = {"plains": "W", "island": "U", "swamp": "B", "mountain": "R", "forest": "G"}
# Snow-covered basics produce the same color (the source-count sites that guard on
# `nl in BASICS` never reach these entries today — widening those guards is a
# follow-on — but any direct BASIC_COLOR lookup resolves them correctly).
BASIC_COLOR.update({f"snow-covered {n}": c for n, c in list(BASIC_COLOR.items())})


def _castability(cards, declared, mana, carddata, exempt=frozenset()):
    """Flag nonland cards whose color needs fall outside `declared` (a WUBRG set).

    Returns (uncastable, off_identity, off_ability, intended):
      intended     – the SUBSET of would-be-uncastable cards the deck's
                     `#: uncastable-ok:` header names on purpose (a reanimator's
                     targets). Still reported by every surface, but never counted as
                     a failure and never fed to `tier_band`. See `_uncastable_ok`.

    Returns (uncastable, off_identity, off_ability):
      uncastable   – [(name, "needs X")] : a STRICT pip, or a true multicolor
                     hybrid with NO in-declared-color option, in a color the deck
                     can't produce. These genuinely can't be cast off the stated
                     colors. (Needs real mana costs — pass a populated `mana`.)
      off_identity – [(name, why)] : castable as printed, but the card's color
                     IDENTITY strays outside declared — every stray, for display.
      off_ability  – the SUBSET of off_identity whose stray is NOT explained by a
                     hybrid pip in the mana cost, i.e. it comes from rules text (an
                     activated ability you can't pay, another face). This is the
                     only part that is ever actionable.

    The two kinds were reported as one list, and the `why` string ("identity has R")
    could not tell them apart — so `audit_deck` counted both and the roster triage's
    `review` verdict fired on 22 of 63 decks with a measured 0% actionable rate
    (broad-scan F-03). A hybrid you pay on-color costs you nothing: Knight's Edge is
    mono-W and runs two R/W hybrids that are simply white cards in that deck. An
    off-color ABILITY is different — Super-Skrull casts for {1}{B}{B}{B} but its
    {4}{R} ability is dead in a deck with no red, and that is worth a look. Splitting
    them turns a saturated flag back into a shortlist; the display keeps showing
    both, since "this card's identity is wider than the deck" is still true and
    useful to see, and only the VERDICT narrows.

    An empty `declared` disables the lint. With an empty `mana` dict the strict
    check is skipped and only the offline identity check runs (so `check` stays
    network-free) — note that with no costs to read, no stray can be shown to be
    hybrid-explained, so every stray reads as an ability stray. That is the
    conservative direction: it over-reports rather than silently clearing a deck."""
    uncastable, off_ident, off_ability, intended = [], [], [], []
    if not declared:
        return uncastable, off_ident, off_ability, intended
    seen = set()
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS or nl in seen:
            continue
        cd = carddata.get(nl)
        if cd is None:
            # No type/identity data for this card (in neither library nor pool —
            # e.g. a brand-new WIP craft target). We can't tell a land from a
            # spell or read its identity, so don't lint it rather than treat it
            # as a nonland and flag it against empty color data.
            continue
        if "Land" in _primary_type(cd["type"]):
            continue
        seen.add(nl)
        entry = mana.get(nl)
        strict, hybrid = parse_pips(entry[0] if entry else "")
        off_strict = sorted(set(strict) - declared)
        # A single-color hybrid ({2/W} generic-or-W, {W/P} phyrexian) can always be
        # paid without its color; only a true multicolor hybrid constrains castability.
        bad_hybrid = sorted({x for h in hybrid
                             if len(h) >= 2 and not (h & declared) for x in h})
        if off_strict or bad_hybrid:
            why = "needs " + "/".join(sorted(set(off_strict + bad_hybrid)))
            # `exempt` holds _ms_key keys (see `_header_card_keys`), so the join must
            # too — a raw `nl` test missed any DFC the header named by its front face,
            # which silently RE-ENABLED the failure the header suppresses.
            (intended if _ms_key(n) in exempt else uncastable).append((n, why))
            continue
        ident = card_colors(cd["colors"] if cd else "")
        stray = sorted(ident - declared)
        if stray:
            # A stray colour that appears ONLY as a hybrid pip in the cost is one you
            # pay on-colour — the card is a plain on-colour card in this deck. Anything
            # else came from the rules text (an off-colour activated ability, another
            # face), which is the part worth reviewing.
            #
            # Without a cost we cannot tell the two apart, and asserting either would be
            # a claim we can't support: `cmd_check` deliberately passes an empty `mana`
            # to stay offline, and every stray there would otherwise be labelled an
            # off-colour ability — false for the R/W hybrids in a mono-W deck. So say
            # "unknown" in the text, while still COUNTING it as actionable, which keeps
            # the offline path over-reporting rather than silently clearing a deck.
            hybrid_colors = set().union(*hybrid) if hybrid else set()
            known_cost = bool(entry and entry[0])
            by_hybrid = known_cost and set(stray) <= hybrid_colors
            note = (" (hybrid — paid on-color)" if by_hybrid
                    else " (off-color ability)" if known_cost
                    else " (cost unknown — run `deck.py mana` to tell hybrid from ability)")
            why = "identity has " + "/".join(stray) + note
            off_ident.append((n, why))
            if not by_hybrid:
                off_ability.append((n, why))
    return uncastable, off_ident, off_ability, intended


def deck_requirements(cards):
    """[(key, display_name, set_code, total_qty)] — one entry per DISTINCT card, in
    first-seen order, with copies SUMMED across duplicate lines.

    A deck may list the same card on more than one line, and owned counts are per-name
    (fungible across printings), so a buildability check must compare total-need against
    total-owned rather than line-by-line. `cmd_check` has always done that and says so;
    the problem was that it said so in a comment, and two other surfaces re-derived the
    same question per LINE — `app.py`'s `/decks` overview and `check_all`'s info summary
    both reported "buildable" for a deck listing 2+2 of a card owned 3, while `cmd_check`,
    the dashboard and the deck editor all correctly reported it short (BS4-13).

    Extracted so the answer has ONE definition. Three implementations of one question is
    the shape `check_agreement.py` exists to catch, and the two that drifted were the two
    that had copied the loop instead of calling it."""
    need, order, printing = {}, [], {}
    for q, n, s, c in cards:
        nl = n.lower()
        if nl not in need:
            order.append(nl)
            printing[nl] = (n, s)
        need[nl] = need.get(nl, 0) + q
    return [(nl, printing[nl][0], printing[nl][1], need[nl]) for nl in order]


def deck_build_gap(cards, by_name_qty):
    """(missing, short) — counts of DISTINCT cards the collection can't cover for this
    deck. `missing` = not in the library at all; `short` = held, but fewer than the
    deck's TOTAL requirement. The summary half of `deck_requirements`, for the callers
    that want the two numbers rather than the per-card rows."""
    missing = short = 0
    for _nl, n, _s, req in deck_requirements(cards):
        have, found = owned(by_name_qty, n)
        if not found:
            missing += 1
        elif have < req:
            short += 1
    return missing, short


def cmd_check(args):
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    _, _, by_name_qty = load_collection()
    meta, cards = parse_deck_file(d["path"])

    reqs = deck_requirements(cards)
    need = {nl: q for nl, _n, _s, q in reqs}
    order = [nl for nl, _n, _s, _q in reqs]
    printing = {nl: (n, s) for nl, n, s, _q in reqs}

    print(f"Deck {d['id']}: {d['name'] or d['path']}")
    print(f"{'Have':>4} / {'Need':<4}  Card")
    print("-" * 44)
    # Craft targets get a rotation flag inline: a missing/short card is exactly the
    # one a wildcard is about to be spent on, and the deck 28 plan bought four
    # rotating cards past this view with nothing said (broad-implement #1).
    pool_rot, _ = _pool_rotation_index()
    missing, short, rot_flagged = [], [], []
    for nl in order:
        n, s = printing[nl]
        req = need[nl]
        have, found = owned(by_name_qty, n)
        flag = ""
        if not found:
            flag = "  <- NOT IN LIBRARY"
            missing.append(n)
        elif have < req:
            flag = f"  <- short {req - have}"
            short.append(n)
        if flag:
            rot = craft_rot_note(n, pool_rot)
            if rot:
                flag += rot
                rot_flagged.append(n)
        shown = "unlim" if nl in BASICS else have
        print(f"{str(shown):>4} / {req:<4}  {n} ({s}){flag}")
    print("-" * 44)
    total = sum(need.values())
    print(f"{len(order)} unique, {total} total.")
    if missing:
        print(f"{len(missing)} not in library: {', '.join(missing)}")
    if short:
        print(f"{len(short)} short of the deck's requirement.")
    if missing or short:
        _fresh = lib.collection_stamp_note()
        if _fresh:
            print(f"  {_fresh}")
    if rot_flagged:
        print(f"⚠ {len(rot_flagged)} craft target(s) rotate out of Standard this year or "
              f"next ({', '.join(rot_flagged)}) — see `deck.py rotation` before crafting.")
    if not missing and not short:
        print("You own everything in this deck. Ready to build.")

    # Castability lint (offline, identity-only — pass an empty mana dict). Flags
    # cards whose color identity strays outside the deck's declared colors.
    declared = _declared_colors(meta)
    _, off_ident, _, _ = _castability(cards, declared, {}, load_card_data())
    if declared and off_ident:
        cols = "".join(sorted(declared))
        print(f"\n⚠ {len(off_ident)} card(s) stray outside the deck's {cols} colors "
              f"(run `deck.py mana {d['id']}` for castability detail):")
        for n, why in off_ident:
            print(f"    {n} — {why}")
    return 1 if (missing or short) else 0


def _ms_key(name):
    """The canonical comparison key for a card NAME: lowercased, FRONT FACE only.

    Every other name-facing join in this repo resolves `Front // Back` to the front
    (`lib.owned_qty`, `load_card_data`, `load_mana`, `load_legalities`,
    `_pool_rotation_index`, `_printing_of`, `_printing_index`). `_multiset` was the
    exception, and it is the key behind `verify` / `sync` / `diff` / the dashboard's
    stale-check — the commands whose whole job is matching a pasted list against a
    stored one BY NAME. So a deck file storing `Ojer Axonil, Deepest Might // Temple of
    Power` against an export naming just the front read as a real change:

        +1  Ojer Axonil, Deepest Might
        -1  Ojer Axonil, Deepest Might // Temple of Power

    `verify` exited non-zero on an identical deck, and `sync --apply` would have
    "repaired" the file by replacing the full name with the bare front — the exact
    un-importable line P8 fixed `_printing_of` to stop writing, re-introduced from the
    other side, past a green INV-04 check (the copy count is unchanged). 14 deck files
    carry a `Front // Back` line. Fifth member of the G-63 class (broad-scan F-02)."""
    return (name or "").strip().lower().split(" // ")[0]


def _ms_display(existing, incoming):
    """Pick the display name to keep when two spellings of one card meet.

    FIRST-SEEN wins (the long-standing rule audit F4 established), with ONE exception:
    the full `Front // Back` form beats a bare front face. A bare front name parses and
    passes INV-04 but fails an Arena import (P8), so when either spelling knows the
    two-faced name it is the one that belongs in a deck file."""
    if existing is None:
        return incoming
    if " // " in (incoming or "") and " // " not in existing:
        return incoming
    return existing


def _multiset(cards):
    """{name_key: (display_name, total_qty)} — keyed case-insensitively (like every
    other command) so the SAME card spelled with different casing across two files
    isn't reported as a spurious −N / +N change (audit F4), and FRONT-FACE normalized
    (see `_ms_key`) so the two legitimate spellings of a double-faced card aren't
    either. The fullest spelling seen is kept for display, so a reconcile that has to
    write the line back writes the importable name."""
    m = {}
    for q, n, s, c in cards:
        nl = _ms_key(n)
        disp, cur = m.get(nl, (None, 0))
        m[nl] = (_ms_display(disp, n), cur + q)
    return m


def cmd_diff(args):
    a, b = find_deck(args.a), find_deck(args.b)
    if not a or not b:
        eprint("Both deck ids must exist. Try: deck.py list")
        return 1
    ma = _multiset(parse_deck_file(a["path"])[1])
    mb = _multiset(parse_deck_file(b["path"])[1])
    print(f"Diff {a['id']} -> {b['id']}  (what {b['id']} changes)")
    print("-" * 40)
    names = sorted(set(ma) | set(mb))
    added = removed = 0
    for nl in names:
        da, db = ma.get(nl, (None, 0)), mb.get(nl, (None, 0))
        disp = db[0] or da[0]  # prefer the target deck's spelling, else the base's
        if db[1] > da[1]:
            print(f"  +{db[1] - da[1]}  {disp}")
            added += db[1] - da[1]
        elif da[1] > db[1]:
            print(f"  -{da[1] - db[1]}  {disp}")
            removed += da[1] - db[1]
    if not added and not removed:
        print("  (identical)")
    else:
        print("-" * 40)
        print(f"+{added} added, -{removed} removed")
    return 0


def cmd_arena(args):
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}.")
        return 1
    _, cards = parse_deck_file(d["path"])
    print("Deck")
    for q, n, s, c in cards:
        line = f"{q} {n}"
        if s:
            line += f" ({s})" + (f" {c}" if c else "")
        print(line)
    return 0


# --- mana data: real costs from card-mana.csv, with a live fallback --------- #
@_file_memo("MANA_CSV")
def load_mana():
    """name_lower -> (mana_cost, mana_value) from card-mana.csv (built by build_mana.py)."""
    import csv as _csv
    out = {}
    if not os.path.exists(MANA_CSV):
        return out
    with open(MANA_CSV, newline="", encoding="utf-8") as fh:
        for r in _csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            if not n:
                continue
            cost = r.get("Mana Cost") or ""
            mv = (r.get("Mana Value") or "").strip()
            mv = int(mv) if mv.isdigit() else None
            if " // " in cost:
                # A split / Room card's RULES mana value is the combined total, which
                # is what Scryfall stores — and it is not the number a curve or a
                # cast-on-curve probability wants. Funeral Room came through as MV 11
                # and inflated deck 42a's average; the door you cast costs 3. Adventure
                # cards already store the front-face value, so recomputing agrees with
                # them and only corrects the split/Room shape.
                mv = mana_value(front_face_cost(cost))
            out[n] = (cost, mv)
    # SECOND pass through the shared helper (BS6-09). This aliased in-pass with
    # `setdefault`, the shape G-63 bans. It happened to be SAFE — a real card's own row
    # is a direct assignment, so it always wins over a DFC's setdefault whatever the file
    # order — but "safe by accident of assignment order" is a property nobody verified
    # and nothing gated: this reads card-mana.csv, so `check_dfc`'s builder scan (even
    # widened to the library) did not reach it. Registered now, and routed through the
    # one home so a future correction to aliasing lands here too.
    return alias_front(out)


def fetch_missing_mana(names, mana):
    """Live-fetch costs for names absent from card-mana.csv (e.g. unowned WIP cards)."""
    todo = [n for n in names if n.lower() not in mana]
    for i in range(0, len(todo), 75):
        chunk = todo[i:i + 75]
        try:
            data = post_collection(chunk)
        except ScryfallUnavailable as e:
            eprint(f"WARN:  could not reach Scryfall for live mana lookup "
                   f"({e}); {len(todo) - i} card(s) not in card-mana.csv will "
                   f"show as unknown. This is a network issue, not stale data.")
            break
        for card in data.get("data", []):
            faces = card.get("card_faces") or [{}]
            cost = card.get("mana_cost") or faces[0].get("mana_cost", "")
            mv = card.get("cmc", 0)
            mv = int(mv) if isinstance(mv, (int, float)) else None
            if cost and " // " in cost:
                # Scryfall's root cmc for a split/Room card is the COMBINED total;
                # the analysis convention is the FRONT face's (G-02). load_mana
                # applies this correction to stored rows — this live-fetch fallback
                # skipped it, so a Room fetched live booked at MV 10 while its CSV
                # twin booked at 3, and the curve/consistency read depended on which
                # path supplied the number (broad-scan BS-13).
                mv = mana_value(front_face_cost(cost))
            full = card.get("name", "").lower()
            mana[full] = (cost or "", mv)
        time.sleep(0.1)
    # Second pass, like `load_mana` above (BS6-09) — and note this one MUTATES the dict
    # it was handed, which is why the alias runs after the whole batch rather than per
    # card: `alias_front` only adds a front key when nothing already claims it, so
    # aliasing mid-batch could let an early DFC claim a key a later real card owns.
    return alias_front(mana)


SYMBOL_RE = re.compile(r"\{([^}]+)\}")


def parse_pips(cost):
    """Classify a mana cost's symbols into (strict, hybrid).

    strict: {color: count} of single-color pips that MUST be paid with that color.
    hybrid: list of frozensets of colors a symbol accepts (e.g. {'W','U'}) — each
            payable with ANY one of them (hybrid {W/U}, monocolor hybrid {2/W},
            or phyrexian {W/P}).

    Reads only the FRONT FACE (``lib.front_face_cost``). A split / Room / Adventure
    card's stored cost is ``A // B`` and you never pay both halves, so the merged
    string double-counted pips for all 292 such cards in the pool — Funeral Room's
    ``{2}{B} // {6}{B}{B}`` read as wanting three black pips when the door you cast
    wants one.
    """
    strict, hybrid = {}, []
    for sym in SYMBOL_RE.findall(front_face_cost(cost)):
        colors = set(ch for ch in sym.upper() if ch in "WUBRG")
        if "/" in sym:
            if colors:
                hybrid.append(frozenset(colors))
        elif len(colors) == 1:
            (c,) = colors
            strict[c] = strict.get(c, 0) + 1
    return strict, hybrid


# The definition lives in lib.primary_type — build_gallery.py needs the same answer and
# had its own copy with the same back-face bug. Kept under the private name because ~35
# call sites below, build_dashboard.py and the tests all reach for `_primary_type`.
_primary_type = primary_type


# --- card data (type + text) for synergy / cost analysis -------------------- #
@_file_memo("DEFAULT_CSV", "POOL_CSV")
def load_card_data():
    """name_lower -> {'name','type','text','colors','power','toughness'} from
    card-library.csv then card-pool.csv.

    The pool fills in oracle text/type for unowned WIP cards so analysis works on
    decks that aren't fully owned yet. `power`/`toughness` are RAW strings (Magic
    prints `*`, `1+*`, `X`), only present on pool rows — the library CSV has no such
    columns — and are '' when unknown. Parse via `lib.card_power`, never int() them.
    """
    data = {}
    for path in (DEFAULT_CSV, POOL_CSV):
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                n = (r.get("Card Name") or "").strip().lower()
                if not n:
                    continue
                if n not in data:
                    data[n] = {"name": (r.get("Card Name") or "").strip(),
                               "type": r.get("Type") or "", "text": r.get("Card Text") or "",
                               "colors": r.get("Color(s)") or "",
                               "power": r.get("Power") or "",
                               "toughness": r.get("Toughness") or ""}
                elif not data[n]["power"] and (r.get("Power") or r.get("Toughness")):
                    # P/T is a POOL-only column — card-library.csv has no such fields.
                    # Because the library is read FIRST and wins, every card you OWN
                    # would otherwise read as unknown-P/T, i.e. the new data would be
                    # missing on exactly the cards most likely to be graded. Backfill
                    # from the pool without disturbing the library's type/text/colors,
                    # which stay authoritative.
                    data[n]["power"] = r.get("Power") or ""
                    data[n]["toughness"] = r.get("Toughness") or ""
    # The old in-loop setdefault stored the alias the moment a full-name row was
    # seen, so a REAL card named exactly like a DFC's front, arriving later in CSV
    # order, could never claim its own key — only its P/T backfilled (the G-63
    # in-pass shape, broad-scan batch 5).
    return alias_front(data)


def creature_subtypes(type_line):
    """Creature subtypes (after the em dash) across all faces of a type line."""
    subs = []
    for face in type_line.split("//"):
        if "creature" in face.lower() and "—" in face:
            subs += face.split("—", 1)[1].split()
    return subs


@_file_memo("MANA_CSV")
def load_keywords():
    """name_lower -> [keywords] from card-mana.csv (Scryfall's per-card list)."""
    kw = {}
    if not os.path.exists(MANA_CSV):
        return kw
    with open(MANA_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            raw = (r.get("Keywords") or "").strip()
            if n:
                kw[n] = [k.strip().lower() for k in raw.split(";") if k.strip()]
    # This was the sixth unaliased name-keyed index over a pool-shaped file: the
    # mana file keys a DFC under its full `Front // Back` while deck lines store
    # the front, so a front-named line's keywords read as a clean "none" — deck
    # 42's Cecil, Dark Knight lost its ⌘ keywords line (G-63; broad-scan BS-12).
    return alias_front(kw)


# Keywords whose real cost is LOWER than the printed mana value (alt/reduced cost).
CHEAPER_KW = {
    "warp", "sneak", "plot", "convoke", "affinity", "delve", "improvise",
    "emerge", "spectacle", "evoke", "offering", "surge", "miracle", "foretell",
}
# Keywords that gate an ability or mode behind an ADDITIONAL / activated cost —
# so the card does more than its base cost implies (and you pay for it).
GATED_KW = {
    "kicker", "multikicker", "bargain", "gift", "spree", "teamwork", "saddle",
    "station", "power-up", "boast", "channel", "craft", "exhaust", "disguise",
    "cycling", "landcycling", "typecycling", "basic landcycling", "plainscycling",
    "islandcycling", "swampcycling", "mountaincycling", "forestcycling",
    "escape", "embalm", "eternalize", "flashback", "jump-start", "unearth",
    "reconfigure", "equip", "level up", "adapt", "outlast", "monstrosity",
}
CHEAPER_TEXT = [("less to cast", "cost reduction"),
                ("without paying its mana cost", "free cast"),
                ("as though it had flash", "conditional flash")]


def x_cost_cards(cards, carddata, mana):
    """Nonland cards whose printed cost contains {X} -> [(name, cost)], sorted.

    The curve, `avg_mv` and the early-drop count all read `mana_value`, which counts
    X as 0 because that is what the rules say off the stack. That is correct for
    castability and for cast-on-curve probability — you really can cast Wildwood
    Scourge for {G} — but it makes an {X} spell look like a ONE-DROP on the curve
    when you will realistically pay three to five for it.

    The distortion runs in BOTH directions and bit deck 50a twice: adding two {X}
    spells made avg MV appear to drop 3.85 -> 3.70, and removing one made it appear
    to rise 3.55 -> 3.76. Neither move changed the real curve much. Report-only —
    this deliberately does NOT feed `deck_quality_vector` or `tier_band`, because a
    new term there would silently re-grade the whole roster.
    """
    out, seen = [], set()
    for _q, n, _s, _c in cards:
        if n.lower() in BASICS or n in seen:
            continue
        d2 = carddata.get(n.lower())
        if not d2 or "Land" in _primary_type(d2["type"]):
            continue
        entry = mana.get(n.lower())
        cost = (entry[0] if entry else "") or ""
        if "{X}" in cost.upper():
            seen.add(n)
            out.append((n, cost))
    return sorted(out)


def classify_cost(keywords, text):
    """Return (cheaper_reasons, gated_reasons) for a card's cost profile."""
    kset = set(keywords or [])
    t = (text or "").lower()
    cheaper = sorted(kset & CHEAPER_KW)
    for phrase, label in CHEAPER_TEXT:
        if phrase in t:
            cheaper.append(label)
    gated = sorted(kset & GATED_KW)
    return list(dict.fromkeys(cheaper)), list(dict.fromkeys(gated))


# Functional-role heuristics: bucket a nonland card by the JOB it does for the
# deck (interaction, card advantage, ramp, ...) by pattern-matching oracle text.
# This is intentionally heuristic — a card can fill several roles, and single
# "draw a card" cantrips are NOT counted as card advantage (they're card-neutral,
# the same reason Spellbook Seeker reads as filtering, not advantage). The point
# is to MEASURE the "light on removal / card advantage" judgment the /tune-deck
# scorecard used to make by eye, not to be authoritative.
ROLE_ORDER = ["Removal (spot)", "Sweeper", "Counter", "Card advantage",
              "Ramp / fixing", "Reanimation", "Payoff / engine", "Burn / drain",
              "Lifegain", "Cost reduction / cheat", "Team pump / anthem",
              "Protection / trick", "Recursion"]
# A permanent-type LIST as MTG templates it: "creature", "artifact or enchantment",
# "artifact, enchantment, or creature with flying". The removal patterns used to spell
# out a handful of fixed combinations by hand, so anything outside that list matched
# NOTHING and the card read as having no removal role at all. Verified misses:
#   Origin of Metalbending / Seedship Impact — "Destroy target artifact or enchantment"
#   Broken Wings                             — "Destroy target artifact, enchantment,
#                                               or creature with flying"  → zero roles
# Those three all count toward `_NONCREATURE_ANSWER_CUES` (the "can it answer a
# planeswalker/enchantment/artifact" test) already, so the codebase treated them as
# answers everywhere EXCEPT the count the tier floor grades on. One list-aware pattern
# replaces the hand-kept combinations, so a new templating can't slip through again.
_PERM_TYPE = (r"(?:nonland permanent|artifact creature|artifact|enchantment|creature|"
              r"permanent|planeswalker|spacecraft|vehicle|land)")
_PERM_TYPE_LIST = rf"{_PERM_TYPE}s?(?:,? (?:or |and )?{_PERM_TYPE}s?)*"

# Shared tail for the targeted-removal patterns (BS8-27/28): not a permanent YOU
# control/own (blink, self-sacrifice tricks) and not a CARD (graveyard hate).
_NOT_OWN_OR_CARD = r"(?! cards?\b)(?![^.]{0,25}?\byou (?:control|own)\b)"

_ROLE_PATTERNS = {
    "Removal (spot)": [
        # destroy / exile a targeted permanent, including a comma-or list of types, and
        # allowing the adjectives MTG puts before the type ("target ATTACKING creature",
        # "target TAPPED creature") — the old hand-kept alternation listed some of those
        # spellings explicitly, so the list-aware rewrite has to keep them or it would
        # LOSE coverage it previously had (caught by a roster-wide before/after diff:
        # decks 15 and 16 each dropped an interaction piece on the first draft).
        # NOTE the doubled braces: this is an f-string, so a bare {0,2} is parsed as a
        # replacement field and silently compiles to the literal text "(0, 2)". That is
        # exactly what happened on the first draft — every "destroy target creature" in
        # the collection stopped matching and 46 decks lost interaction. Caught only by
        # the roster-wide before/after diff, which is why that diff is worth running.
        # `,?` admits the comma qualifier ("nonland, nontoken permanent" — Skyclave
        # Apparition) the 3–5-word sibling below already allowed (BS8-28).
        # The two lookaheads are BS8-27 and BS8-28's graveyard-hate class: "exile
        # target creature YOU CONTROL, then return it" is BLINK (41 pool cards, seven
        # in thirteen decks; six tier floors rested on it), and "exile target creature
        # CARD from a graveyard" is graveyard hate (24 pool cards) — neither answers an
        # opponent's threat, and both fed the axis the floor grades.
        rf"(?:destroy|exile) (?:up to \w+ )?target (?:[a-z-]+,? ){{0,2}}?{_PERM_TYPE_LIST}"
        rf"{_NOT_OWN_OR_CARD}",
        # COORDINATED QUALIFIER LIST before the type. The run above allows at most TWO
        # adjective words, which covers "target TAPPED creature" but not the qualifier
        # LISTS Magic templates constantly — "attacking or blocking" and "green or white"
        # are three words, and "non-Angel, non-Demon, non-Devil, non-Dragon" is four with
        # commas that `[a-z-]+ ` cannot cross. So an entire family of plain removal scored
        # ZERO roles: Divine Verdict, Sudden Strike, Puncturing Light, Protective Response,
        # Devouring Light, Farm // Market (attacking-or-blocking), Deathmark (colour), Power
        # Word Kill (the exclusion list), Nissa's Defeat, Thraben Exorcism, Sigrid. Eleven
        # cards, all of them unambiguous spot removal, on the axis the tier floor grades
        # (G-67; broad-scan BS6-10).
        #
        # A SEPARATE pattern rather than widening the run above, deliberately: raising
        # `{0,2}` to `{0,5}` would re-score every removal card in the pool at once, and
        # BS2-06 is the record of what a silent OVER-count costs. Requiring at least THREE
        # qualifier words makes this strictly additive — anything the existing run already
        # reaches is out of scope here — so the roster diff attributes every change to it.
        #
        # The zone guard is load-bearing and was measured, not assumed: `land` and
        # `creature` are in `_PERM_TYPE`, so without it "exile target card other than a
        # basic land card from an opponent's graveyard" (Kotose) and "exile target red,
        # white, or black creature card from your graveyard" (Offspring's Revenge) both
        # read as removal — graveyard hate and a recursion cost, neither an answer to a
        # permanent. `[^.]` keeps the lookahead inside the same sentence, so "Destroy
        # target creature." is untouched. With it: 11 matches, zero false positives.
        rf"(?:destroy|exile) (?:up to \w+ )?target (?:[a-z-]+,? ){{3,5}}?{_PERM_TYPE_LIST}"
        rf"{_NOT_OWN_OR_CARD}(?![^.]{{0,40}}?\bgraveyard\b)",
        # REMOVAL AURA. `enchanted creature can't attack or block` (Pacifism) is already
        # in this bucket a few lines down, which settles the design question: this repo
        # counts a neutralizing Aura as spot removal. Its twin — the Aura that shrinks the
        # creature instead of taxing it — was never written, so Dead Weight, Debilitating
        # Injury, Mire's Grasp, Stab Wound, Failed Conversion and 15 more scored ZERO
        # roles. The non-Aura templating of the identical effect (`target creature gets
        # -N/-N`) is fully covered — 120 pool cards, no misses — which is G-67's exact
        # signature: same effect, one noun covered and its sibling not.
        #
        # It is also a live K-09 violation, and that is how it was found: `tag_synergies`
        # tags Dead Weight `removal` while `classify_roles` returned nothing, so the two
        # models disagreed about the same text on the axis `tier_band` grades.
        #
        # `-N/-0` counts alongside `-N/-N` for the Pacifism reason: a -6/-0 creature has
        # been answered as an attacker. The `enchant creature you control` guard is the
        # one measured false positive — Craving of Yeenoghu is a BUFF Aura on your own
        # creature whose recursion clause perpetually gains "-1/-1". Note it must not
        # catch Duskmourn's Domination, whose "You control enchanted creature" is a
        # Control-Magic steal (a real answer) and reads in the other word order. Guarded:
        # 20 matches, zero false positives.
        r"(?s)\A(?!.*enchant creature you control).*?enchanted creature gets -[0-9x]+/-[0-9x]+",
        # LETHAL SHRINK in the +N/-M shape. `target creature gets -N/-N` is covered (120
        # cards) and its twin `gets +N/-N` was not, so Auger Spree, Nameless Inversion,
        # Lash of Malice, Flowstone Infusion and Desperate Measures scored zero roles.
        #
        # DO NOT reach for the PERMANENCE rule the neutralization block below rests on —
        # it INVERTS here, and that is the whole point of writing this separately. A
        # `-4/-4 until end of turn` still KILLS, and a dead creature does not come back at
        # cleanup, so the temporary version does permanent work. Auger Spree is a removal
        # spell in a way Merfolk Trickster is not, despite both saying "until end of turn".
        # This family is graded on LETHALITY, not duration.
        #
        # Scoped to the TARGETED spell. 29 pool cards carry a `+N/-M` clause and 23 of
        # them are firebreathing-style self-pumps on your own body ("{U}: This creature
        # gets +1/-1") — the same drawback-vs-answer split `its controller's` handles for
        # tap-down. `target … creature` plus a `you control` guard isolates the 5 real
        # ones with no false positives. The AURA form (+N/-M) is deliberately LEFT OUT:
        # Immolation reads as removal and Mogis's Favor (+2/-1) reads as a pump, two cards
        # that a shape test genuinely cannot separate — the leading-minus Aura pattern
        # below already covers the unambiguous half.
        r"target (?:[a-z-]+ ){0,2}?creature (?!you control)[^.]{0,20}?gets \+\d+/-\d",
        # ── NEUTRALIZATION: the answer that leaves the permanent on the battlefield ──
        # Magic answers a creature three ways — kill it, exile it, or turn it off — and this
        # bucket read only the first two. The third was 124 pool cards of nothing (G-67's
        # standing TAXONOMY residual), even though `enchanted creature can't attack or block`
        # (Pacifism) has been in this bucket all along, which is the repo already deciding
        # that a neutralizing Aura IS spot removal. These three patterns finish that thought.
        #
        # THE LINE IS PERMANENCE, and it is drawn deliberately. A one-turn effect is TEMPO,
        # not an answer, so `doesn't untap during its controller's NEXT untap step` (Frost
        # Lynx, White Dragon — 35 cards) and `loses all abilities UNTIL end of turn / until
        # your next turn` (Merfolk Trickster, Azure Beastbinder) are all EXCLUDED. That
        # matches how the rest of this file treats a one-shot, and it is the conservative
        # direction: a tempo card read as removal would inflate the axis the tier floor
        # grades on, which is the BS2-06 failure.
        #
        # (1) TAP-DOWN, permanent. `its controller's` is doing real work: the same clause
        # appears as a DRAWBACK on your own card ("Colossus of Sardia doesn't untap during
        # YOUR untap step"), and 11 such cards would otherwise read as removal. With it:
        # 37 matches — Waterknot, Capture Sphere, Frozen in Ice, Dungeon Geists, Tidebinder
        # Mage, Tamiyo's Compleation — and zero false positives.
        r"doesn't untap during its controller's untap step",
        # (2) ABILITY-STRIP, Aura form. Same `enchant creature you control` guard as the
        # removal-Aura pattern above and for the same reason (a bestow/buff Aura on your own
        # creature is not an answer), plus the permanence rule. 19 matches — Frogify,
        # Kasmina's Transmutation, Witness Protection, Ichthyomorphosis, Reprobation — and
        # zero false positives. Trickster's Elk is a TRUE positive despite being a bestow
        # creature: cast as an Aura on a bomb it strips the bomb, which is the play.
        r"(?s)\A(?!.*enchant creature you control)"
        r"(?!.*until end of turn[^.]{0,50}loses all abilities)"
        r".*?enchanted (?:creature|permanent|artifact)[^.]{0,60}?loses all abilities",
        # (3) ABILITY-STRIP, targeted form. `except ` excludes Town-Razer Tyrant's "loses all
        # abilities EXCEPT mana abilities" — land punishment, not an answer to a threat.
        # 6 matches: Oko, Patriar's Humiliation, Resolute Rejection, Curious Colossus,
        # Abigale, Lizard. All permanent, all true positives.
        r"(?s)\A(?!.*until (?:end of turn|your next turn)[^.]{0,50}loses all abilities)"
        r".*?(?:target|each creature target opponent controls)[^.]{0,70}?"
        r"loses all abilities(?![^.]{0,40}(?:until |except ))",
        # (4) ABILITY-STRIP, ANAPHOR form — the target is named in one sentence and the
        # strip lands in the next, pointing back with "It". Matches exactly ONE card today
        # (The Wondrous Wasp), and a pattern for one card is normally a smell — this one
        # earns its place because it closes an INCONSISTENCY rather than adding coverage.
        # The Wasp taps a creature and strips it "for as long as The Wondrous Wasp remains
        # on the battlefield"; Ty Lee, Chi Blocker does the identical thing one clause over
        # ("for as long as you control Ty Lee") and IS counted by pattern (1). Two cards
        # with one effect shape were landing on opposite sides of the line. Anchored the
        # same way the file's other anaphor patterns are (an explicit upstream `target`, a
        # sentence boundary, and both duration guards), so it cannot drift onto a
        # self-referential "It loses all abilities" on your own card.
        r"(?s)\A(?!.*until (?:end of turn|your next turn)[^.]{0,50}loses all abilities)"
        r".*?target [^.]{0,60}\.\s*it loses all abilities(?![^.]{0,40}(?:until |except ))",
        # SPLIT TEMPLATE: the target is named in one sentence and the destroy verb lands
        # in a later one, with an anaphor standing in for the target — Quag Feast reads
        # "CHOOSE target creature, planeswalker, or Vehicle. Mill two cards, then destroy
        # THE CHOSEN PERMANENT if …". The pattern above needs `destroy|exile` immediately
        # before `target`, so nothing matched and the card scored ZERO roles: it was
        # absent from the interaction count the tier floor grades on, not merely from the
        # noncreature-answer profile. Anchoring on the anaphor is precise on its own —
        # "destroy/exile the chosen <permanent>" only ever appears in removal text.
        r"(?:destroy|exile) the chosen (?:permanent|creature|card|artifact|enchantment)",
        # The `(?!(?:player|opponent)\b(?! or planeswalker))` guard mirrors the one the
        # scaling-damage sibling below documents as load-bearing: "deals N damage to
        # target OPPONENT/PLAYER" is reach, not an answer, and this fixed-damage twin
        # shipped without it — 89 pool cards of player-only burn (HYDRA Assault Robot,
        # Shocking Sharpshooter, Ozai's Cruelty …) classified as spot removal, and 17
        # roster decks over-reported the interaction axis the tier floor grades on
        # (deck 10 read 15 against a real 12) — the one measured OVER-count in a
        # pattern set whose failure mode is otherwise uniformly under (broad-scan
        # BS2-06). "player or planeswalker" / "opponent or planeswalker" stay IN: that
        # older templating can hit a planeswalker, which is an answer (42 pool cards).
        r"deals? \d+ damage to (?:any target|(?:another )?target (?!(?:player|opponent)\b(?! or planeswalker)))",
        r"deals? \d+ damage to up to \w+ target",
        # BACK-REFERENCED target: the target is named in one clause and the damage lands
        # in a later one, pointing back with "that creature". Every fixed-damage pattern
        # above needs the literal word "target" adjacent to the damage clause, so this
        # whole templating was a whitelist hole (G-67) — Trial of Agony ("Choose two
        # target creatures controlled by the same opponent. That player chooses one of
        # those creatures. Trial of Agony deals 5 damage to that creature.") scored ZERO
        # roles. It is the anaphor twin of the "destroy the chosen permanent" pattern
        # above, and the same anchoring makes it precise. Two guards, both measured
        # against the whole pool: `(?!\'s)` excludes "that creature\'s CONTROLLER" (Blur
        # of Blades), which is reach at a player, not an answer; and requiring an explicit
        # "choose ... target creature" upstream excludes incidental COMBAT damage, where
        # "that creature" back-references a blocker (Ashmouth Hound, Ornery Goblin). With
        # both, the pattern matches exactly 3 pool cards and all 3 are true positives.
        r"(?s)choose (?:up to )?(?:\w+ )?target creatures?"
        r".{0,300}?deals? \d+ damage to that creature(?!\'s)",
        # any "fight" is removal (Novel Nunchaku "fights up to one target", Longstalk
        # Brawl "fight each other") — the old pattern only caught "fights target".
        r"\bfights?\b|creatures? fight",
        r"deals? damage equal to (?:twice )?.{0,20}?power to target (?:creature|creature or planeswalker|attacking)",
        # SCALING damage whose size is anything OTHER than a power reference. The pattern
        # above hard-codes "power", so Combustion Technique — "deals damage equal to 2 plus
        # the number of Lesson cards in your graveyard to target creature" — matched
        # nothing and scored ZERO roles, in the deck that PROTECTS it as a marquee payoff.
        # Same failure shape as Quag Feast above: a removal template no pattern read, so
        # the card was absent from the interaction count the tier floor grades on. `[^.]`
        # keeps the span inside one sentence so an unrelated later clause can't be swept in.
        # The `(?!player|opponent)` guard is load-bearing: "deals damage equal to its power
        # to target PLAYER" (Gravitic Punch, Sif's Spearmaster, Runebound Wolf) is reach,
        # not an answer, and a roster sweep of the first draft showed that was the ONLY
        # false-positive class among 116 newly-matched cards.
        r"deals? damage equal to [^.]{0,80}?to (?:any target|(?:another )?target (?!player|opponent)\w+)",
        # "UP TO ONE target" — the optional-target templating. Both scaling-damage patterns
        # above require "to target" or "to any target" immediately after the size clause,
        # and the fixed-damage half has carried its `up to \w+ target` twin since the
        # beginning; the scaling half never got one, so 8 pool cards that all point damage
        # at a creature scored no Removal (Thorin, Mountain-king; Assert Perfection; Burrog
        # Barrage; Feral Encounter; Legolas x2; Pyretic Rebirth; Dragonspark Reactor).
        # Measured against the whole pool: 8 matches, zero false positives — the player
        # guard is kept anyway, since "to up to one target player" is the same reach the
        # sibling patterns exclude.
        r"deals? damage equal to [^.]{0,80}?to up to \w+ (?:another )?target (?!player|opponent)\w+",
        # TARGET-FIRST word order. The two patterns above both assume "equal to X"
        # precedes "to target"; Magic also templates it the other way round, and that
        # half was a whitelist hole (G-67). Triumphant Chomp — "deals damage to target
        # creature equal to 2 or the greatest power among Dinosaurs you control" — is a
        # {R} sorcery that kills anything up to a 12/12 and scored ZERO roles, which is
        # why `cuts` ranked it deck 28's WEAKEST card (2026-08-11). The exclusions are
        # BS2-06's guard, extended: player-only burn must not read as spot removal, and
        # "target spell's controller" (Refuse) is a player too — it was the single false
        # positive when this pattern was measured against the whole pool.
        r"deals? damage to (?:any target|(?:up to \w+ )?(?:another )?target "
        r"(?!player\b|opponent\b|spell\b))[^.]{0,60}?equal to",
        # DIVIDED damage — the Fiery Confluence / Death to Our Enemies template. Every
        # fixed-damage pattern above expects "to target"/"to any target" immediately after
        # the number, and this one says "divided as you choose among …" instead.
        r"deals? \d+ damage divided as you choose among",
        # -N/-N or -X/-X shrink on a targeted creature (incl. "creature an opponent
        # controls gets -X/-X" — Cloud of Darkness, Wick's Patrol).
        r"target creature (?:an opponent controls )?gets -[0-9x]",
        r"creature an opponent controls gets -[0-9x]",
        # BOUNCE. Note `owner'?s?` — MTG templates this as "to its OWNER'S hand", and the
        # original pattern spelled the alternation `(?:owner|their) hand`, which requires
        # the literal text "owner hand". So it matched NOTHING: every unconditional bounce
        # spell in the collection (Boomerang Basics, Into the Flood Maw, ...) scored zero
        # roles for the entire life of the pattern, while the broad audit cue DID fire —
        # which is why bounce dominated the roster-wide "possible under-count" list. The
        # type is a full `_PERM_TYPE_LIST` so "nonland permanent" is covered alongside
        # "creature", and `[^.]` keeps the span inside one sentence.
        rf"return (?:up to \w+ )?target (?:[a-z-]+ ){{0,2}}?{_PERM_TYPE_LIST}"
        rf"[^.]{{0,60}}?(?:owner'?s?|owners'|their) hands?",
        # EDICT. Sacrifice-a-creature-of-their-choice is removal (it answers hexproof),
        # and it sat in the broad audit cue while missing from this list entirely.
        # EDICTS, generalized (BS8-28): the two narrow forms this replaces ("sacrifices a
        # creature" / "a permanent") missed "sacrifices TWO creatures" (Barter in Blood),
        # "a NONTOKEN creature", "a NONLAND permanent", "X creatures" — 29 pool cards.
        r"(?:target|each) (?:player|opponent) sacrifices (?:a|an|two|three|four|x|half)"
        r"(?: of)?(?: the)? (?:[a-z-]+ ){0,2}?(?:creature|permanent)s?",
        # LIBRARY TUCK (BS8-28): "put target creature on top/bottom of its owner's
        # library" — the pattern below requires "into", so Condemn / Run Aground /
        # Anchor to the Aether (15 pool cards) scored nothing.
        r"put (?:up to \w+ )?target (?:[a-z-]+ ){0,2}?(?:creature|permanent|nonland permanent)"
        r"[^.]{0,40}?(?:on top|on the bottom|second from the top) of (?:its|their) owner'?s'? librar",
        # X-damage: the fixed patterns above require a DIGIT, so "deals X damage to target
        # creature" scored nothing (Hell to Pay).
        r"deals? x damage to (?:target|any target|up to \w+ target)",
        # Tuck via an Aura — same class as the activated-ability tuck already covered.
        r"enchanted creature'?s owner shuffles it into their library",
        r"enchanted creature can't attack or block",
        # Removal by TUCKING a creature into a library. It leaves the battlefield, so
        # it is a real answer, but no destroy/exile/damage/-N-N pattern saw it:
        # Floodpits Drowner's "{1}{U}, {T}: Shuffle this creature and target creature
        # with a stun counter on it into their owners' libraries" scored ZERO roles,
        # which is why an earlier tier note wrongly wrote it off as "taps and stuns
        # rather than answers" (session finding — the same card twice).
        r"shuffle[^.]{0,80}?target (?:creature|permanent)[^.]{0,60}?librar",
        r"target creature[^.]{0,80}?into (?:their|its) (?:owner'?s? )?librar",
    ],
    # SCOPED since BS8-11: "exile all" matched graveyards, hands, libraries and every
    # "End the turn" reminder (Rest in Peace, Hex Magic, Time Stop — 20 pool cards), and
    # "all creatures get -" matched a -N/-0 power shrink that kills nothing (13). The
    # additions further down are BS8-28's misses: "destroy/exile EACH creature" (18),
    # "damage equal to … to each creature" (18), "each player sacrifices all/two/X" (15).
    "Sweeper": [r"destroy all (?!(?:cards?|counters|tokens you control)\b)",
                r"exile all (?!(?:the cards?|cards?|graveyards?|spells?|other spells|opponents'|tokens you control)\b)",
                r"all (?:other )?creatures get -[0-9x]+/-[1-9x]",
                r"each (?:other )?creature (?:gets -[0-9x]+/-[1-9x]|deals|is dealt|you don't control)",
                # one-sided / opponent-only wraths ("creatures your opponents control
                # get -2/-2" — Massacre Wurm) the "all creatures" pattern misses.
                r"creatures (?:you don't control|your opponents control|target player controls) get -[0-9x]+/-[1-9x]",
                # scalable / conditional wipes the fixed patterns above miss
                r"creature with mana value.{0,20}?or less.{0,40}?destroy",
                r"destroy those creatures",
                r"deals? (?:\d+|x) damage to each (?:other )?creature",
                r"(?:destroy|exile) each (?:other )?(?:[a-z-]+ ){0,2}?(?:creature|nonland permanent|permanent)s?\b(?! card)",
                r"deals? damage (?:equal to|to each (?:other )?creature equal to)[^.]{0,60}?(?:to each (?:other )?creature|for each)",
                # "each player sacrifices all other creatures they control" (Bringer of
                # the Last Gift) is a wrath by another name; so is "two"/"X"/"half".
                r"each (?:player|opponent) sacrifices (?:all|two|three|four|x|half)"
                r"(?: of)?(?: the)? (?:other )?(?:creatures|permanents)"],
    # "counter up to one target spell unless…" (Repulsive Mutation) matched neither
    # this pattern NOR the broad coverage net below, so it scored zero roles AND was
    # never flagged as an under-read — the worst case, a miss invisible to the very
    # audit that exists to catch misses (session finding).
    "Counter": [r"counter (?:up to \w+ )?target", r"counter (?:that|the chosen) spell",
                # BS8-28: the hard-counter ALTERNATIVES — "exile/return target spell"
                # (Aven Interrupter, Spell Queller, Reprieve — 16 pool cards) and
                # "counter all/each" (Summary Dismissal, Glen Elendra's Answer).
                r"(?:exile|return) target spell", r"counter (?:all|each) (?:other )?spell"],
    # Surfaced while testing the lexicon unification: "five" and "half X" were in
    # neither the role pattern nor the audit cue, so Wan Shi Tong, Librarian ("draw
    # half X cards, rounded down") was uncounted AND unflagged — the same
    # missed-by-both hole as Repulsive Mutation, on the card-advantage axis.
    "Card advantage": [r"draws? (?:two|three|four|five|half x|x|that many) cards?",
                       r"draw a card for each", r"draws? cards? equal to",
                       # A REPEATABLE single draw accrues advantage; the cantrip rule is
                       # about ONE-SHOT single draws. Phyrexian Arena reads as a cantrip
                       # to a pattern that only counts how many cards one resolution
                       # draws, which is why deck 42's card-advantage line said 1.
                       #
                       # Repeatability is the whole test, and it comes in two templatings
                       # — the first version of this pattern only read ONE of them. A
                       # PHASE trigger recurs every turn, and "upkeep" was hardcoded while
                       # Magic puts the same effect on the end step, the draw step and
                       # combat just as often (Haliya, Guided by Light draws at the
                       # beginning of your END STEP). And a "WHENEVER" trigger recurs by
                       # construction — Exemplar of Light draws every turn it gets a
                       # counter. Neither was matched here NOR by the broad `_CA_CUES`
                       # net, so both cards were the "missable by BOTH" failure the
                       # superset comment below exists to prevent: they got a role
                       # (Payoff, Lifegain), so they were not `unclassified` either, and
                       # deck 46 reported card advantage 1 against a real 3 with the
                       # uncertainty channel silent.
                       #
                       # "When" vs "WHENEVER" is the load-bearing distinction and it is
                       # Magic's own templating rule: "When this creature enters, draw a
                       # card" is a one-shot ETB cantrip (Inspiring Overseer) and stays
                       # excluded; "Whenever X, draw a card" recurs. Matching a bare
                       # "draw a card" would have swept every cantrip in the format into
                       # card advantage and inverted the rule this pattern implements.
                       r"at the beginning of (?:your|each|the) "
                       r"(?:upkeep|end step|draw step|combat|precombat main phase)"
                       r"[^.]{0,60}?draws? a card",
                       # The phase-trigger pattern above puts the possessive FIRST
                       # ("at the beginning of YOUR combat"), but Magic templates the
                       # combat trigger the other way round — "at the beginning of combat
                       # ON YOUR TURN" — so the word order defeats the `(?:your|each|the)`
                       # group and that whole templating was a whitelist hole (G-67).
                       # Nexus of Becoming and Mister Fantastic both draw every turn and
                       # scored no card advantage. Same repeatability test as above: a
                       # phase trigger recurs by construction. Matches exactly those 2
                       # pool cards, both true positives.
                       r"at the beginning of combat on your turn"
                       r"[^.]{0,60}?draws? a card",
                       # The draw must fall AFTER the trigger's comma. Magic templates a
                       # triggered ability as "Whenever <condition>, <effect>", so the
                       # comma is what separates a card that DRAWS from a card that CARES
                       # about drawing: "Whenever you draw a card, this creature gets
                       # +1/+1" (Chasm Skulker, Orcish Bowmasters, Queza — 45 of them on
                       # the pool) puts "draw a card" in the CONDITION, and a naive
                       # `whenever .* draw a card` swept every one into card advantage —
                       # scoring a draw-payoff as a draw, which is backwards.
                       r"\bwhenever\b[^.,]{0,80}?, [^.]{0,60}?draws? a card",
                       r"\binvestigate\b",
                       # A CLUE TOKEN *is* a delayed draw ("{2}, Sacrifice this token:
                       # Draw a card"), and `investigate` above is the KEYWORD form of
                       # exactly that. But plenty of cards spell the token out instead of
                       # using the keyword — The Mechanist, Aerial Artisan makes a Clue per
                       # noncreature spell and scored Payoff/engine only, so a deck built
                       # on it still read card advantage 0.
                       r"create (?:a|\w+|that many) clue tokens?",
                       # IMPULSE. "Exile the top card of your library. You may play that
                       # card this turn" is a card you would not otherwise have had — the
                       # same advantage a draw gives, one zone over. Nothing matched it:
                       # Zuko, Exiled Prince scored ZERO roles despite a repeatable {3}
                       # impulse ability, and it is a whole deck archetype (deck 24, deck
                       # 45) that the card-advantage axis could not see. `[^.]` keeps the
                       # span inside the sentence pair so an unrelated later clause cannot
                       # be swept in.
                       # BS8-28: the impulse phrased with the window FIRST — "Exile the top
                       # card of your library. Until end of your next turn, you may play
                       # that card" (Crimson Operative, Blazing Crescendo — 30 pool cards)
                       # — and the trigger-cost draw that crosses a period: "Whenever …,
                       # you may pay {1}. If you do, draw a card" (54, rummage excluded).
                       r"exile the top card of your library[^.]{0,40}\. (?:until (?:the )?end of (?:turn|your next turn), )?you may (?:play|cast) (?:it|that card)",
                       r"\bwhenever\b[^.]{0,80}?, you may (?!discard)[^.]{0,60}?\. if you do, [^.]{0,40}?draws? a card",
                       r"exile the top \w+ cards? of your library[^.]{0,60}\. (?:you may play|until )",
                       # Impulse off EACH PLAYER'S library — Etali, Primal Storm exiles
                       # the top card of every library and lets you cast them. The two
                       # patterns above are scoped to "your library" and missed it.
                       r"exile the top card of each player's library[^.]{0,60}?(?:you may cast|you may play)",
                       # CASTING OFF THE TOP of your own library is a permanent draw
                       # substitute — Vizier of the Menagerie, Mm'menon. Scored nothing.
                       r"you may (?:cast|play) (?:\w+ ){0,3}(?:spells|cards?) from the top of your library",
                       # AN ACTIVATED ABILITY IS REPEATABLE BY CONSTRUCTION, which is the
                       # same argument the "whenever" pattern above rests on — but every
                       # pattern in this bucket was TRIGGER-shaped, so a draw you reach by
                       # PAYING a cost matched nothing at all. `+1: Draw a card`,
                       # `{3}, {T}: Draw a card` (Arcane Encyclopedia), `{2}{B}, Sacrifice
                       # an artifact or creature: Draw a card` (Kingpin's Enforcers) all
                       # scored zero, and so did EVERY planeswalker's draw ability.
                       # Measured at 187 pool cards before the fix, 24 of them
                       # planeswalkers. The cost that surfaced it: deck 58's quality guard
                       # reported "card advantage 4→3" on a swap that RAISED it, because
                       # the card cut had a trigger-shaped draw and the card added has a
                       # cost-shaped one (K-14).
                       #
                       # `(?m)^` is load-bearing. Oracle text puts each ability on its own
                       # LINE, so anchoring there is what distinguishes a real ability from
                       # the same words quoted inside REMINDER text — a Clue's reminder
                       # ('It\'s an artifact with "{2}, Sacrifice this artifact: Draw a
                       # card."') is mid-line, so every card that merely CREATES a Clue or
                       # a Blood token stays out. Granting those cards the role via
                       # reminder text would have been a silent over-count, the one failure
                       # this bucket has never had.
                       #
                       # TWO EXCLUSIONS INSIDE THE COST SPAN, both taken from rules this
                       # module already states rather than invented here:
                       #   `discard`       — `{T}, Discard a card: Draw a card` (Charging
                       #                     Strifeknight, Professor Zei) is RUMMAGING. It
                       #                     is card-neutral, exactly what _LOOT_RE filters
                       #                     one clause over; the only difference is which
                       #                     side of the colon the discard sits on.
                       #   `sacrifice this`— `{2}, Sacrifice this artifact: Draw a card`
                       #                     (Aether Spellbomb, Candy Trail, the common
                       #                     "{4}, {T}, Sacrifice this land: Draw a card"
                       #                     tapland cycle) consumes the source, so it is a
                       #                     ONE-SHOT single draw — a cantrip with delayed
                       #                     timing, and the cantrip rule above already
                       #                     excludes those. Keeping them would have taken
                       #                     the change from 24 decks to 58 and re-graded
                       #                     the roster off a flood-insurance land.
                       # Sacrificing something ELSE (Ayara "another black creature",
                       # Fountainport "a token", Technodrome "another artifact") is
                       # repeatable and counts.
                       #
                       # The optional `<ability word> — ` prefix is there because an
                       # ABILITY-WORD-gated activation still starts its own line but does
                       # NOT start with the cost: "Delirium — {2}{U}, {T}: Draw a card"
                       # (Raving Visionary), "Domain — {5}, {T}: Draw a card" (Jodah's
                       # Codex), "Threshold — {1}{U}: … and draw a card" (Thought Shucker).
                       # Measured: it changes the final answer for exactly those THREE
                       # cards and nothing else, which is the check worth repeating if the
                       # prefix is ever widened — a looser prefix reaches into reminder
                       # text and the line anchor stops earning its keep.
                       r"(?m)^(?:[a-z][a-z']{2,14}(?: \d+)? [-—] )?"
                       r"(?:[+-]?\d+|\{[^}]+\})(?:(?!discard|sacrifice this)[^.:\n])"
                       r"{0,60}:[^.\n]{0,60}?draws? a card",
                       # The same ability with the draw one sentence later, behind an
                       # "if you do" — Chandra, Spark Hunter's `+2: You may sacrifice an
                       # artifact or discard a card. If you do, draw a card.` The pattern
                       # above stops at the sentence break and missed her, which is how the
                       # measurement of K-14 failed to include the card that demonstrates
                       # it. KNOWN RESIDUAL: her discard mode IS a rummage, so a modal cost
                       # whose worst branch is card-neutral reads here as full advantage.
                       # Under-counting is this bucket's stated preference, but the cost
                       # span is the only thing either pattern can see, and hers is `+2`.
                       r"(?m)^(?:[a-z][a-z']{2,14}(?: \d+)? [-—] )?"
                       r"(?:[+-]?\d+|\{[^}]+\})(?:(?!discard|sacrifice this)[^.:\n])"
                       r"{0,60}:[^.\n]{0,90}\.\s*(?:if|when) you do[^.\n]{0,40}?draws? a card"],
    "Ramp / fixing": [r"search your library for .{0,30}?\bland",
                      r"\{t\}: add \{",
                      r"put (?:a|that|those|up to \w+).{0,40}?land.{0,40}?onto the battlefield",
                      # ANY-COLOUR MANA. The pattern above requires a literal `{` right
                      # after "add", so it reads "{T}: Add {G}" and misses "{T}: Add one
                      # mana of any color" — which is how Magic templates EVERY rainbow
                      # source. Bloom Tender, Great Divide Guide, Springleaf Drum and
                      # Agatha's Soul Cauldron all scored ZERO roles, in decks whose #1
                      # graded weakness is the manabase. The cost prefix is left open
                      # because these come as `{T}:`, `{1},{T}:`, `{T}, Tap an untapped
                      # creature:` and as a granted ability in quotes ("Each land you
                      # control has '{T}: Add one mana of any color'").
                      r"add (?:one|two|three|x|that much|an amount of) mana (?:of|in) any",
                      # The per-colour (Vivid) form says "of THAT color", not "of any" —
                      # Bloom Tender reads "For each color among permanents you control,
                      # add one mana of that color". Caught only because the test above
                      # used the card's real text instead of a paraphrase.
                      r"for each color[^.]{0,60}?add (?:one|that much|x) mana of that color",
                      # Colour-fixing that adds no mana at all — it lets the mana you
                      # already have pay a cost it otherwise could not. Same job.
                      r"spend mana as though it were mana of any color",
                      r"spend (?:this |that )?mana as though it were mana of any (?:one )?color",
                      r"you can spend mana of any type",
                      # All-basic-land-types (K-03 names this shape as a fixer the tagger
                      # could not see); Energybending and friends.
                      r"lands? you control (?:gain|have) all basic land types"],
    # KNOWN RESIDUAL on the any-colour patterns above: they match the REMINDER TEXT of a
    # Treasure token, including on cards that hand the Treasure to someone else ("Exile
    # target nonland permanent. ITS CONTROLLER creates a Treasure token"). Those pick up a
    # spurious Ramp/fixing role. Left in deliberately — Ramp/fixing does NOT feed
    # `deck_quality_vector`, so the blast radius is the `stats` breakdown and
    # `redundancy`'s depth count, not the tier floor. Tighten only if a real call is made
    # off an inflated ramp depth.
    # Return a permanent to the BATTLEFIELD from the graveyard (higher value than
    # to-hand recursion). Catches "in your graveyard … return … to the battlefield"
    # phrasing, which the old "from your graveyard" Recursion pattern silently missed
    # (Too Evil to Stay Dead, Bringer of the Last Gift, sagas, etc.).
    # STRICT since BS8-10: the two bag-of-words patterns this replaces needed no
    # graveyard at all, so 297 of 655 pool "reanimators" were land drops, blink and
    # cheat-from-hand (Scaled Herbalist, Teleportation Circle, Champion of Rhonas) —
    # an IMPACT role, so `cuts` protected them and `redundancy` built all-false
    # buckets in 22 decks. A graveyard is required in the CLAUSE; the recursion
    # keywords are reanimation templated as a keyword (unearth, embalm, escape…),
    # which the old text patterns MISSED (60 pool cards).
    "Reanimation": [
        r"(?:card|creature|permanent)[^.]{0,80}?(?:in|from) (?:your|a|an|any|each|their|that|target) graveyard[^.]{0,80}?(?:on)?to the battlefield",
        r"return [^.]{0,60}?(?:creature|permanent|card)[^.]{0,40}?from (?:your|a|an|any|each|their|that|target) graveyard[^.]{0,60}?to the battlefield",
        r"put [^.]{0,50}?(?:creature|card|permanent)[^.]{0,50}?from (?:your|a|an|any|each|their|that|target) graveyard[^.]{0,60}?onto the battlefield",
        r"return (?:this|it|that card) from your graveyard to the battlefield",
        r"\b(?:unearth|embalm|eternalize|encore|disturb|escape—|persist|undying)\b",
    ],
    # Repeatable/triggered engines — the death, ETB-matters, lifegain and
    # leaves-play payoffs the role map used to score as "no functional role"
    # (Judge Magister Gabranth, Rot Farm Mortipede, aristocrats/lifedrain bodies).
    "Payoff / engine": [
        r"whenever .{0,60}?dies",
        r"whenever (?:a|another|one or more) .{0,40}?(?:enters|leave|leaves|die|dies)",
        r"whenever you gain life",
        r"whenever you cast",
        # (`put a +1/+1 counter on … whenever` was removed at BS8-30: its only matches
        # crossed reminder text, which the classifier no longer reads, so it went dead.)
        # The counter quantity is an alternation, not the literal "a": "put two /
        # X / that many +1/+1 counters" is how Magic templates every scaling
        # counter payoff (Serra Redeemer, Woodland Champion), and the bare-"a"
        # form missed all 34 of them. Strict superset of the old catch-all;
        # measured 2026-08-28: 25 decks' Payoff counts up, axes/floors 0/0.
        r"\bwhenever\b.{0,80}?(?:draw a card|put (?:a|an|x|\d+|two|three|"
        r"one or more|that many) \+1/\+1 counters?|create|each opponent loses)",
        # K-14's exact shape one bucket over: every pattern above is `whenever`-shaped,
        # so the SAME payoff on a per-turn clock ("At the beginning of combat on your
        # turn, put a +1/+1 counter on each creature you control" — Ouroboroid,
        # Dragonmaster Outcast, Virtue of Loyalty) scored ZERO roles. A your-turn-only
        # beginning-of-phase trigger is repeatable BY CONSTRUCTION — the same argument
        # `whenever` and the activated-draw widening rested on. Scoped to YOUR phases
        # (an opponent's-upkeep trigger is a different card); payoff list and counter
        # quantities mirror the catch-all above, which gained the same quantity
        # alternation a day later. Measured before shipping (2026-08-27): +187 pool cards,
        # 47 roster cards (19 previously ZERO-role), 60 decks' Payoff counts up,
        # interaction / card-advantage / tier floors moved: 0 / 0 / 0.
        r"at the beginning of (?:combat on your turn|your upkeep|your end step|"
        r"each of your turns)"
        r"[^.]{0,60}?(?:put (?:a|an|x|\d+|two|three|one or more|that many) "
        r"\+1/\+1 counters? on|create|draw a card|each opponent loses)",
    ],
    # Direct damage / life loss to a player — reach & finishers the fixed-number
    # removal pattern misses (Cat-Gator, drain effects).
    "Burn / drain": [
        r"deals? damage equal to .{0,60}?(?:any target|a player|target player|each opponent|that player)",
        r"(?:each opponent|target opponent|any opponent|that player|each player) loses \d",
        r"deals? \d+ damage to each opponent",
        r"loses life equal to",
    ],
    # `gain(s) life equal to ...` (Exsanguinate, Corrupt, Sifter Wurm — 68 pool cards)
    # was in neither this pattern nor the tag model; the tag half was fixed with the
    # `pay life` work and this is the role half, so the two agree on the phrase.
    "Lifegain": [r"\blifelink\b", r"you gain \d+ life", r"gain \d+ life",
                 r"gains? life equal to"],
    # Cost reducers / free-cast enablers — the value that makes a nominally
    # expensive card cheap (Diamond Weapon, affinity/convoke, cascade cheats).
    "Cost reduction / cheat": [
        # Magic writes "This spell costs {1} less TO CAST for each artifact you
        # control", so a `costs {1} less for each` pattern (the words adjacent)
        # matched zero of 15.8k pool cards — the third instance of this project's
        # signature bug: a regex that compiles fine and can never fire. Found by
        # `check_patterns.py` on its first run. Harmless in effect (the general
        # pattern below already covers every one of the 155 cards it was meant
        # for), which is exactly why it survived: a dead pattern hiding behind a
        # live one changes no count and shows up in no diff.
        # BS8-29: 263 of 810 hits were a card discounting ITSELF ("this spell costs {1}
        # less to cast for each…", "this ability costs {1} less") — self-pricing, not a
        # cost-reduction engine, and an IMPACT role worth +6 in `cuts`.
        r"(?<!this spell )(?<!this ability )costs? (?:up to )?\{[0-9x]+\} less",
        r"\baffinity\b", r"\bconvoke\b", r"\bimprovise\b", r"\bcascade\b",
        r"without paying its mana cost",
    ],
    "Team pump / anthem": [
        r"(?:other )?creatures you control get \+",
        # TRIBAL LORDS. The pattern above hard-codes the noun "creatures", so every lord
        # in the format — "Other Elves you control get +1/+1", "Zombies you control get
        # +1/+0", "Creature tokens you control get +1/+1" — scored NO anthem role. 146
        # pool cards, i.e. the largest single whitelist hole measured here (G-67), and it
        # sits on the exact card class a tribal deck is built out of. Requiring the full
        # +N/+N body keeps this off "lands you control get" style text; the first half
        # must be a PLUS so a symmetric shrink can't read as a pump.
        r"\b\w+s you control get \+\d+/[-+]\d+",
        # A QUALIFIER between the noun and the verb defeats both patterns above:
        # "Creatures you control WITH FLYING get +1/+1" (Favorable Winds, Empyrean Eagle),
        # "Creatures you control OF THE CHOSEN TYPE get +2/+2" (An Unexpected Party) --
        # the choose-a-type category K-13 warns never contains the type name.
        r"creatures you control (?:of the chosen type |with [^.]{0,30}?)get \+",
    ],
    # `ward` mirrors _PROTECTION_RE (which always counted it): the role counted bare
    # hexproof/indestructible but not their modern replacement, so the AXIS and the
    # ROLE answered the same text differently (the K-09 shape) — 259 pool cards, 131
    # of them otherwise ZERO-role. Measured 2026-08-28: 58 decks' Protection counts
    # up, interaction / card-advantage / tier floors 0 / 0 / 0.
    "Protection / trick": [r"\bhexproof\b", r"\bindestructible\b", r"protection from",
                           r"\bward\b",
                           # R-13: a card pumping ITSELF (firebreathing, prowess) is not a
                           # trick you can point at the creature you need to save.
                           r"(?<!this creature )(?<!this permanent )gets \+\d+/\+\d+ until end of turn"],
    "Recursion": [r"from your graveyard", r"card in your graveyard",
                  r"return .{0,40}?to your hand"],
}
_ROLE_COMPILED = [(label, [re.compile(p) for p in _ROLE_PATTERNS[label]])
                  for label in ROLE_ORDER]
_ROLE_COMPILED_MAP = dict(_ROLE_COMPILED)

# The roles that make a card "interaction" for the resilience axis the tier floor
# grades on. Defined HERE, next to the patterns, because the coverage-audit net below
# is built from them — it used to sit ~1000 lines later, which is how the net and the
# classifier drifted apart in the first place.
_INTERACTION_ROLES = {"Removal (spot)", "Sweeper", "Counter"}

# "draw N, then discard N" is a LOOT — card-NEUTRAL filtering, not card advantage, for
# exactly the reason a single-draw cantrip isn't counted (see ROLE_ORDER's note). Kiora,
# the Rising Tide's "draw two cards, then discard two cards" used to score +1 card
# advantage, which both inflated her value when the deck was graded and made cutting her
# register as a regression the quality guard reported but that wasn't real (session
# finding). Only an EQUAL, adjacent draw/discard pair is filtered — a genuinely
# net-positive "draw three cards. Discard a card." is untouched.
#
# THE SINGULAR PAIR ("draw a card, then discard a card") was added with the
# activated-cost patterns above, and it closes a hole this comment used to paper over.
# It said connive "never counted in the first place" — true, but only because nothing
# matched a bare "draw a card" at all, not because anything excluded it. The moment a
# cost-shaped pattern landed, `{2}, {T}: Draw a card, then discard a card` (Bag of
# Holding, Collector's Vault, Agna Qel'a, Kitsa) would have counted as card advantage —
# a looter scoring as a draw engine, which is the exact inversion the plural half exists
# to prevent. The invariant is now true by construction rather than by accident.
_LOOT_RE = re.compile(
    r"draws? (two|three|four|five|x|that many) cards?,? (?:then )?"
    r"discards? (?:\1|that many) cards?"
    r"|draws? a card,? (?:then )?discards? a card"
    # BS8-28 (R-05): the two loot shapes the comma form cannot see — DISCARD-FIRST
    # ("discard up to two cards, then draw that many": Sokka, Seasoned Pyromancer, 33
    # pool cards) and the PERIOD form ("Draw three cards. Then discard two": Thirst for
    # Knowledge, 14). Both are card-neutral and scored as advantage.
    # EQUAL counts only, like the comma form: "discard a card, then draw two" is +1 and
    # "Draw three cards. Discard a card" is +2 — both stay advantage (pinned).
    r"|discards? a card,? then draws? a card(?! for each)"
    r"|discards? (?:up to )?(?P<n>two|three|four|x|that many|any number of) cards,?"
    r" then draws? (?:(?P=n)|that many) cards(?! plus)"
    r"|discards? your hand,? then draws? that many cards(?! plus)"
    r"|draws? (?P<m>two|three|four|x|that many) cards\.\s*(?:then )?discards? (?:(?P=m)|that many) cards")

# Real PROTECTION for a permanent you control — deliberately NARROWER than the
# "Protection / trick" role, which lumps a combat pump ("gets +2/+2 until end of turn")
# in with an actual answer to removal.
#
# This axis exists because its absence was the single biggest weakness of an all-in
# single-threat deck and NO view could see it: `stats`, `quality` and `tier` all count
# interaction and card advantage, and nothing asked "can I protect the thing I win
# with?" It was found by an ad-hoc grep, not by any tool (session finding).
#
# `regenerate` is deliberately absent: "It can't be regenerated" is boilerplate on
# removal spells, so keying on the word would score half the removal in the format as
# protection. Prefer under-counting to a wrong count on a measured axis.
_PROTECTION_RE = re.compile(
    r"\bhexproof\b|\bindestructible\b|\bward\b|protection from"
    r"|can'?t be the target of (?:spells|abilities)"
    r"|counter target spell that targets"
    r"|\bphases? out\b")


# "power 4 or greater" style conditions — the class of card that was ungradeable while
# the repo stored no P/T. The payoff reads unconditional in a synergy model ("draws you
# cards!") but only fires off bodies that actually meet the bar ON ENTRY, and a counters
# deck full of X-creatures printed 0/0 meets it far less often than it looks.
_POWER_THRESHOLD_RE = re.compile(
    r"\b(power|toughness) (\d+) or (?:greater|more)\b", re.I)
_POWER_THRESHOLD_THIN = 0.30       # <30% of creatures qualifying = worth flagging

# The flag counts YOUR creatures against the bar, so it only means anything when the
# clause is about creatures YOU CONTROL *and* is a PER-CREATURE threshold. Two shapes
# break that, and both were firing — 16 of the roster's 27 flags, 59%, were false:
#
#   * REMOVAL / opponent-facing (83 pool cards). "Destroy target creature with power 4
#     or greater" (Sandbenders' Storm, Battle Menu, Valorous Stance) measures the wrong
#     board entirely — the card wants THEIR creatures big. For a sweeper like Dusk
#     ("destroy all creatures with power 3 or greater") few of your own qualifying is
#     the whole POINT, so the warning inverted the card's reading. Same for "can't be
#     blocked by creatures with power 3 or greater", which is about their blockers.
#   * "TOTAL power/toughness N or greater" (153 pool cards). Teamwork ("tap any number
#     of creatures you control with total power 4 or more") and Betor's "if creatures
#     you control have total toughness 10 or greater" are SUMS: three 2/2s satisfy
#     "total power 4". Counting creatures at printed power >= 4 is the wrong
#     arithmetic, not a conservative read of the right one — deck 34 was told 0 of its
#     19 creatures could pay a teamwork cost it can pay trivially.
#
# Opt IN on "you control" rather than blacklisting the bad shapes: Magic's templating
# puts "you control" directly before "with power N", and an affirmative test can't be
# silently widened by a phrasing nobody has written yet. The cost is losing a scope
# spelled some other way (Gwenna's "whenever you cast a creature spell with power 5 or
# greater"), which is the right direction to err — this list exists to be read
# card-by-card, so a false cue is the expensive kind.
_POWER_SCOPE_MINE_RE = re.compile(r"you control(?:[^.]{0,25})?$", re.I)
_POWER_SCOPE_TOTAL_RE = re.compile(r"\btotal\s+$", re.I)
_POWER_SCOPE_BACK = 40


def power_threshold_flags(cards, carddata):
    """[(payoff_name, attr, N, qualifying_copies, creature_copies)] for each card whose
    text keys on "power/toughness N or greater", with how many of the deck's creatures
    meet that bar on their PRINTED stats. Only flags a payoff the deck under-supports.

    Printed P/T only — a card that grows after it enters (counters, anthems, an equip)
    still reads by its printed value, which is exactly right for an ENTERS trigger and
    conservative for anything else. Creatures whose P/T isn't a number (`*`, `X`) are
    counted as NOT qualifying and reported separately by the caller if needed, since
    guessing would re-introduce the invented-fact problem `lib.card_power` avoids.

    Scoped: only a clause about creatures YOU CONTROL, and only a per-creature bar —
    see `_POWER_SCOPE_MINE_RE` for the removal / "total power" shapes this used to
    misread and why the test opts in rather than blacklisting."""
    creatures = []
    for q, n, _s, _c in cards:
        cd = carddata.get(n.lower())
        if not cd or "Creature" not in _primary_type(cd.get("type") or ""):
            continue
        creatures.append((q, cd))
    total = sum(q for q, _ in creatures)
    out = []
    if not total:
        return out
    seen = set()
    for q, n, _s, _c in cards:
        cd = carddata.get(n.lower())
        if not cd:
            continue
        text = cd.get("text") or ""
        for m in _POWER_THRESHOLD_RE.finditer(text):
            back = text[max(0, m.start() - _POWER_SCOPE_BACK):m.start()]
            if _POWER_SCOPE_TOTAL_RE.search(back):
                continue                      # a SUM across creatures, not a per-body bar
            if not _POWER_SCOPE_MINE_RE.search(back):
                continue                      # removal / opponent-facing — wrong board
            attr, bar = m.group(1).lower(), int(m.group(2))
            key = (cd["name"], attr, bar)
            if key in seen:
                continue
            seen.add(key)
            # TIMING of the gated trigger, read from the ability's own line (an oracle
            # ability owns its line — the same `(?m)^` convention K-14 rests on). It
            # decides what a printed-stat count MEANS: an ENTERS trigger really is
            # blind to later growth, but Scalestorm Summoner and Ruby check on ATTACK
            # ("whenever … attacks … if/while you control"), so pumped bodies DO
            # satisfy them — and the flag's one-size ENTERS caveat was copied into a
            # tier block as a fabricated weakness and had to be retracted (2026-08-09).
            line_lo = text.rfind("\n", 0, m.start()) + 1
            line_hi = text.find("\n", m.start())
            ability = text[line_lo:line_hi if line_hi >= 0 else len(text)]
            # "attacks" wins over "enters" when a line has both — the attack reading
            # (printed count is a FLOOR) is the conservative one for a growing board.
            if re.search(r"\battack", ability, re.I):
                timing = "attack"
            elif re.search(r"\benters?\b", ability, re.I):
                timing = "enters"
            else:
                timing = "other"
            qualify = sum(cq for cq, ccd in creatures
                          # NOT `card_power(...) or -1`: a printed 0 is real and common
                          # (every X-creature is 0/0), and `or` collapses it to unknown —
                          # the exact idiom G-16 bans, sitting in the function that rule
                          # documents, ready to be copied (BS4-32).
                          if (pv := card_power(ccd.get(attr))) is not None and pv >= bar)
            if qualify / total < _POWER_THRESHOLD_THIN:
                out.append((cd["name"], attr, bar, qualify, total, timing))
    return out


# DECK SHAPE. The single question this toolkit could never answer: "does this deck win
# WIDE or TALL, FAST or SLOW, on one threat or many?" Every distinctness call needs it,
# and answering it by reading `#: archetype:` headers produced the worst misread of the
# session — deck 30 was called a wide deck from its header while the question was
# whether a TALL counters plan duplicated it. Themes can't answer this: "counters" is
# the same tag whether they all go on one creature or spread across twelve.
_WIDE_CUES = [re.compile(p, re.I) for p in [
    r"create (?:a|an|two|three|four|five|\w+|x) .{0,60}?creature tokens?",
    r"creatures you control get \+", r"for each creature you control",
    r"creatures you control have", r"populate\b", r"\bconvoke\b",
    r"whenever (?:another )?(?:a )?creature you control enters",
]]
# TALL is about CONCENTRATION, not counters. The first draft keyed on "put a +1/+1
# counter on target creature" and "target creature gets +N/+N" — which read deck 4
# (27 creatures, a WIDE value board) as tall, because a single counter is a wide
# deck's glue too. Only AMPLIFIERS count: effects that make one body disproportionate.
_TALL_CUES = [re.compile(p, re.I) for p in [
    r"double (?:the number of )?.{0,30}?(?:\+1/\+1 counters?|counters|power)",
    r"twice (?:that much|that many|its power)",
    r"triple .{0,20}?power",
    r"equipped creature gets \+", r"enchanted creature gets \+",
    r"gets \+x/\+x", r"where x is (?:the number of|its|this creature'?s) ",
    r"base power and toughness \d+/\d+",
]]


def deck_shape(cards, carddata, mana=None):
    """Structural shape of a deck, measured from oracle text rather than tags.

    Returns a dict with WIDE / TALL scores (quantity-weighted card counts), creature
    and token counts, evasion, curve, and a plain-English verdict. It is a SHAPE read,
    not a quality read — a wide deck is not better or worse than a tall one; the point
    is that two decks sharing every theme tag can be opposite decks."""
    wide = tall = creatures = evasive = 0
    mvs, wide_cards, tall_cards = [], [], []
    for q, n, _s, _c in cards:
        if n.lower() in BASICS:
            continue
        cd = carddata.get(n.lower())
        if not cd:
            continue
        tline = cd.get("type") or ""
        if "Land" in _primary_type(tline):
            continue
        text = cd.get("text") or ""
        if "Creature" in _primary_type(tline):
            creatures += q
        if re.search(r"\bflying\b|\bmenace\b|can't be blocked|\btrample\b|\bfear\b|\bshadow\b",
                     text, re.I):
            evasive += q
        if any(p.search(text) for p in _WIDE_CUES):
            wide += q
            wide_cards.append(cd.get("name") or n)
        if any(p.search(text) for p in _TALL_CUES):
            tall += q
            tall_cards.append(cd.get("name") or n)
        if mana:
            e = mana.get(n.lower())
            if e and e[1] is not None:
                mvs += [e[1]] * q
    avg_mv = round(sum(mvs) / len(mvs), 2) if mvs else 0.0
    # A verdict only when one axis clearly leads — a deck can legitimately be neither.
    # Creature DENSITY is its own signal: a deck fielding 25+ creature copies is wide
    # almost by construction, and one fielding under ~14 cannot go wide whatever its
    # text says. Fold it in rather than trusting the text scan alone.
    if creatures >= 22:
        wide += 2
    elif creatures <= 14:
        # The body-count nudge only means something when there ARE bodies. It fired
        # unconditionally, so a 0-creature spells deck scored wide 0 / tall 2 and was
        # reported "TALL — few bodies, effects that scale one creature UP" with an EMPTY
        # tall-cards list, and the honest "no board-growth axis" verdict was unreachable
        # for any deck at or under 14 creature copies (BS4-33). Report-only, but a
        # verdict that is affirmatively wrong is worse than a vague one.
        if creatures:
            tall += 2
    lead = abs(wide - tall)
    if lead < 2:
        axis = "BALANCED / neither" if (wide or tall) else "no board-growth axis"
    elif wide > tall:
        axis = "WIDE — many bodies, effects that scale with creature COUNT"
    else:
        axis = "TALL — few bodies, effects that scale one creature UP"
    if avg_mv and avg_mv <= 2.5:
        speed = "FAST curve"
    elif avg_mv >= 3.3:
        speed = "SLOW curve"
    else:
        speed = "MIDRANGE curve"
    return {"wide": wide, "tall": tall, "creatures": creatures, "evasive": evasive,
            "avg_mv": avg_mv, "axis": axis, "speed": speed,
            "wide_cards": sorted(set(wide_cards)), "tall_cards": sorted(set(tall_cards))}


def protection_effects(text):
    """True if a card grants/has a real protection effect (ward, hexproof,
    indestructible, protection from, untargetable, a counter-that-targets). Counts the
    CARD, not its reach — a self-only ward on an irrelevant body still counts, which is
    why the deck-level check below only flags an outright ZERO rather than scoring a
    thin count as adequate."""
    return bool(_PROTECTION_RE.search(_norm_role_text(text)))

# Mechanics whose value depends on the DECK (colors of mana available, board
# state), not the card in isolation — the cuts/grade step must check them against
# the specific deck, never rank them from the label alone (e.g. converge is dead
# in a mono-color deck; affinity/X scale with your board).
_CONTEXT_PATTERNS = {
    "converge": [r"\bconverge\b", r"for each color of mana spent"],
    "devotion": [r"\bdevotion\b"],
    "affinity": [r"\baffinity\b"],
    "convoke": [r"\bconvoke\b"],
    "improvise": [r"\bimprovise\b"],
}
_CONTEXT_COMPILED = {k: [re.compile(p) for p in v] for k, v in _CONTEXT_PATTERNS.items()}

# COST-AS-UPSIDE. A card's additional cost or drawback reads as a downside in isolation
# and every scoring model here grades cards in isolation — but in the matching deck the
# same clause is an ENGINE TRIGGER. CLAUDE.md warns humans about this in prose ("ask what
# does this do *here*"); nothing detected it, so a card whose cost is secretly an upside
# sorted like a card with a real drawback. Observed cases:
#   • Chocobo Kick's "Kicker — Return a land you control to its owner's hand" in a
#     LANDFALL deck: replaying the land re-triggers every landfall payoff, so paying the
#     kicker is pure profit.
#   • Broodguard Elite's Warp (self-exile at end of turn) in a COUNTERS deck: leaving the
#     battlefield is what moves its counters onto your threat.
#   • A "sacrifice a creature/artifact" cost in a sacrifice/aristocrats deck.
# Each entry maps a cost pattern → the deck themes that turn it into an upside. This is a
# FLAG for a human read, never a score change — the same posture as `⚠ scales w/`, and
# for the same reason: the signal is real but too fuzzy to move a ranking on its own.
_COST_UPSIDE = [
    (re.compile(r"return a land you control to its owner'?s hand", re.I),
     {"landfall", "lands", "ramp"}, "kicker returns a land → re-triggers landfall"),
    (re.compile(r"\bwarp\b|exile this creature at the beginning of the next end step", re.I),
     {"counters", "etb", "blink"}, "warp self-exile → leaves-play / re-ETB value"),
    (re.compile(r"when this .{0,30}?leaves the battlefield", re.I),
     {"counters", "sacrifice", "blink"}, "leaves-play trigger → the 'drawback' is the payoff"),
    (re.compile(r"as an additional cost.{0,60}?sacrifice", re.I),
     {"sacrifice", "food", "tokens", "aristocrats"}, "sacrifice cost → feeds your outlets"),
    (re.compile(r"\bdiscard (?:a|one|two|that) card", re.I),
     {"graveyard", "reanimator", "recursion", "madness"}, "discard cost → fills the yard"),
]


# Themes that are only a BENEFIT when the deck is built to reward them; otherwise the
# same interaction is a COST. Filling your graveyard is value in a reanimator deck and
# pure damage in a control deck that needs its counterspells in the library — but a
# theme-overlap model sees one tag either way.
#
# The observed miss: Genesis Wave read KEY for deck 40 (Simic ramp-CONTROL) purely on a
# `graveyard` match — i.e. it scored highly BECAUSE it mills you, which there is the
# reason not to play it (15 of 34 nonlands, including Finale of Revelation and the whole
# counterspell suite, get binned). The fix reuses machinery that already exists rather
# than adding a model: `engine_roles` knows which cards are graveyard PAYOFFS, so the
# theme only counts as a fit when the deck actually fields some.
_COST_THEMES = {
    "graveyard": "graveyard",
    "mill": "graveyard",
    "discard": "graveyard",
    "self-mill": "graveyard",
}
_COST_THEME_MIN_PAYOFFS = 2


def _drop_cost_themes(shared, cards, carddata):
    """Remove cost-shaped themes from a shared-theme list unless the deck fields at least
    `_COST_THEME_MIN_PAYOFFS` cards that PAY THEM OFF. Themes with no cost interpretation
    pass through untouched."""
    risky = {t for t in shared if t.lower() in _COST_THEMES}
    if not risky:
        return shared
    payoffs = {}
    for q, n, _s, _c in cards:
        cd = carddata.get(n.lower())
        if not cd:
            continue
        for theme, sides in engine_roles(cd.get("text") or "").items():
            if "payoff" in sides:
                payoffs[theme] = payoffs.get(theme, 0) + q
    keep = []
    for t in shared:
        engine = _COST_THEMES.get(t.lower())
        if engine and payoffs.get(engine, 0) < _COST_THEME_MIN_PAYOFFS:
            continue      # the deck pays the cost but collects no reward — not a fit
        keep.append(t)
    return keep


# ── Zone conflicts: a fine card that fights your own engine ────────────────────────
# The MIRROR of `cost_upside_flags` below. That flag catches a drawback that is secretly
# an UPSIDE in this deck; nothing caught an upside that is secretly a DRAWBACK here, and
# that shape shipped into two finished decks. Strategic Betrayal ("Target opponent exiles
# a creature they control and their graveyard") and Pit of Offerings ("exile up to three
# target cards from graveyards") both read as perfectly good cards — and both empty a
# graveyard that four heist cards in the same deck need FULL. `cuts` ranked Strategic
# Betrayal second-weakest, so the shortlist saw it; only a full-text read explained WHY.
# A model that grades a card in isolation structurally cannot see this.
#
# CLAUDE.md states the rule for humans — "when a deck DEPENDS on a zone being populated,
# audit every card that empties it" — and this detects that pairing.
#
# The patterns are built from the POOL's real phrasings, not from strings written to
# match them (the lesson the `heist` tag's four pattern bugs taught). Two findings from
# that survey shape the design:
#   * `exile this card from YOUR graveyard` is on 90 pool cards and is escape / flashback
#     / delve COST — a graveyard USER, the opposite of hate. Anything scoped to your own
#     yard is excluded outright.
#   * A heist card exiles an opponent's graveyard IN ORDER TO CAST FROM IT (Tinybones
#     "exile it from their graveyard with a stash counter", Hama, Azula). Those are the
#     deck's ENGINE, and a naive exile+graveyard rule flags them as hostile to
#     themselves. `tag_synergies.is_heist_text` already separates "casts cards you don't
#     own" from real hate, so the emptier test reuses it rather than adding a model.
_ZONE_MIN_DEPENDENTS = 2   # one card is a singleton, not a plan worth protecting

# Emptied scope = the OPPONENT's yard only.
_GY_HATE_OPP_RE = re.compile(
    # A GAP before "their graveyard" is required, not optional: Strategic Betrayal reads
    # "Target opponent exiles a creature they control AND their graveyard", so the verb
    # and the zone sit at opposite ends of the clause. Demanding them adjacent missed the
    # single card this detector was built for — found by running it, not by reading it.
    r"exiles?[^.]{0,60}?\b(?:their|his or her) graveyard"
    r"|exile (?:target |each )?(?:player'?s?|opponent'?s?) graveyard"
    # "that player's graveyard" (Hama) is as common as "target player's" and was absent.
    r"|exile[^.]{0,50}?\bfrom (?:an? opponent'?s?|target player'?s?|that player'?s?|their) graveyard", re.I)
# Emptied scope = EVERY yard at once, with no choice — the only shape that can hit YOUR
# graveyard against your will.
_GY_HATE_ALL_RE = re.compile(
    r"exile (?:all|each) graveyards?"
    r"|exile all cards? from (?:all|each) graveyards?"
    r"|graveyards? (?:is|are) exiled", re.I)
# TARGETED graveyard exile — "exile up to one target card from a graveyard". The
# controller PICKS the yard, so in an own-graveyard deck you simply aim it at theirs and
# there is no conflict; it only fights a plan that needs THEIR yard as a resource. Keeping
# this apart from the mass shape is what turns the flag from noise into a shortlist: on
# the roster it drops the count from 12 to the decks where it is actually a conflict.
_GY_HATE_CHOOSE_RE = re.compile(
    r"exile[^.]{0,50}?\bfrom (?:a|a single|each|target) graveyard\b"
    r"|exile[^.]{0,50}?\bfrom graveyards\b", re.I)
# The escape / delve / flashback COST family — a graveyard USER, never hate.
_GY_OWN_SCOPE_RE = re.compile(r"\byour graveyard\b|\byour own graveyard\b", re.I)
# Needs the OPPONENT's yard populated (casting or stealing from it).
# CONSUMES their yard: turns cards in an opponent's graveyard into YOUR resources.
# Split out of `_GY_NEED_OPP_RE` (2026-08-28) because "needs their yard populated" and
# "converts their yard into your resources" are different questions and only the second
# is an engine PAYOFF. Riverchurn Monument mills "cards equal to the number of cards in
# their graveyard" — it genuinely wants their yard full (so it belongs in the broad
# predicate, which the zone-conflict flag reads) while being an ENABLER that fills yards,
# so counting it as a payoff inverted its role.
_GY_CONSUME_OPP_RE = re.compile(
    r"(?:cast|play|return|exile)[^.]{0,60}?from (?:an? opponent'?s?|target player'?s?|that player'?s?|their) graveyard",
    re.I)
_GY_NEED_OPP_RE = re.compile(
    r"(?:cast|play|return|exile)[^.]{0,60}?from (?:an? opponent'?s?|target player'?s?|that player'?s?|their) graveyard"
    r"|in your opponents'? graveyards"
    r"|cards? in (?:their|each opponent'?s?) graveyard", re.I)


def graveyard_emptier(text):
    """``'opponent'`` / ``'all'`` / ``None`` — which graveyards this card EMPTIES.

    Three scopes, because they conflict with different plans:
      ``all``      – untargeted mass exile; hits YOUR yard whether you like it or not.
      ``opponent`` – scoped to their yard.
      ``choose``   – targeted ("exile up to one target card from a graveyard"); you pick
                     the yard, so it only fights a plan that needs THEIRS populated.

    ``None`` for a card that only touches YOUR yard (escape/delve costs) and for any
    card whose exile is a heist (it exiles in order to cast, so it needs the yard full —
    it is the engine, not the hate)."""
    t = _norm_role_text(text or "")
    if not t:
        return None
    try:
        from tag_synergies import is_heist_text
        if is_heist_text(text or ""):
            return None
    except Exception:
        pass                      # tag_synergies unavailable — fall through, over-report
    if _GY_HATE_ALL_RE.search(t):
        return "all"
    if _GY_HATE_OPP_RE.search(t):
        return "opponent"
    if _GY_HATE_CHOOSE_RE.search(t):
        return "choose"
    # Left last on purpose: a card scoped ONLY to your own yard is a user, not an emptier.
    return None


def graveyard_dependent(text, type_line=""):
    """``{'own'}`` / ``{'opponent'}`` / both / empty — which graveyards this card NEEDS
    populated. Own-yard dependence reuses `engine_roles`' graveyard PAYOFF side (the
    trustworthy half of that classifier) rather than adding a second model."""
    t = text or ""
    needs = set()
    # REMINDER TEXT STRIPPED FIRST. The crime reminder — "Targeting opponents, anything
    # they control, and/or cards in their graveyards is a crime" — contains the literal
    # phrase this regex's third branch looks for, so EVERY crime card read as needing an
    # opponent's graveyard populated. Measured 2026-08-28 on four: Servant of the
    # Stinger, Rattleback Apothecary, Riverchurn Monument and Deepmuck Desperado, none
    # of which consume a yard (the last two FILL one — they are enablers). This is the
    # exact trap `role_coverage_flags` records one screen up, where Ward's reminder
    # tripped the Counter cue and reported every warded creature as missed interaction.
    if _GY_NEED_OPP_RE.search(_REMINDER_RE.sub(" ", _norm_role_text(t))):
        needs.add("opponent")
    try:
        if "payoff" in engine_roles(t).get("graveyard", set()):
            needs.add("own")
    except Exception:
        pass
    return needs


def zone_conflict_flags(cards, carddata):
    """[(card_name, scope, why, [dependent card names])] — cards that EMPTY a graveyard
    this deck depends on being populated.

    Fires only when the deck fields >= `_ZONE_MIN_DEPENDENTS` cards needing that yard, so
    a lone graveyard payoff can't manufacture a conflict. A FLAG for a human read, never a
    score change — the same posture as `cost_upside_flags` and `scales w/`, because the
    signal is real but the judgement (is the hate worth it against this meta?) is not
    mechanical."""
    need_opp, need_own = [], []
    seen = set()
    for _q, n, _s, _c in cards:
        nl = n.lower()
        if nl in BASICS or nl in seen:
            continue
        seen.add(nl)
        cd = carddata.get(nl)
        if not cd:
            continue
        needs = graveyard_dependent(cd.get("text") or "", cd.get("type") or "")
        if "opponent" in needs:
            need_opp.append(n)
        if "own" in needs:
            need_own.append(n)

    out, seen = [], set()
    for _q, n, _s, _c in cards:
        nl = n.lower()
        if nl in BASICS or nl in seen:
            continue
        seen.add(nl)
        cd = carddata.get(nl)
        if not cd:
            continue
        scope = graveyard_emptier(cd.get("text") or "")
        if not scope:
            continue
        # Only an untargeted mass exile can hurt your OWN yard; a targeted one you aim.
        hit = list(need_opp)
        if scope == "all":
            hit += [x for x in need_own if x not in hit]
        hit = [x for x in hit if x.lower() != nl]     # a card can't conflict with itself
        if len(hit) < _ZONE_MIN_DEPENDENTS:
            continue
        where = {"all": "every graveyard, including your own",
                 "opponent": "an opponent's graveyard",
                 "choose": "a graveyard you target"}[scope]
        out.append((n, scope,
                    f"empties {where}, which {len(hit)} card(s) here need populated", hit))
    return out


def cost_upside_flags(text, deck_themes):
    """['<why>'] for each additional cost / drawback in `text` that this deck's themes
    turn into an UPSIDE. Empty when the deck doesn't support it — the point is that the
    same clause is a downside elsewhere."""
    t = _norm_role_text(text)
    themes = {str(x).lower() for x in (deck_themes or ())}
    return [why for rx, want, why in _COST_UPSIDE if rx.search(t) and (want & themes)]

# Coverage self-audit (F15). The role classifier above is PRECISE (low false
# positives) but inevitably misses phrasings, silently UNDER-counting — the recurring
# failure only a hands-on read used to catch (a creature-ETB kill, an edict, a -1/-1,
# a bounce, "exile up to one target"). These BROAD cues are the complement: high-
# recall nets for "this text interacts / draws cards." When a broad cue fires but the
# precise classifier tagged NO matching role, that's a likely under-read — flagged for
# a human verify, never silently changing a count. Tuned to the classifier's intent:
# single-card draw is a cantrip (deliberately not card advantage), and damage to a
# PLAYER is burn/reach, not creature interaction — so both are excluded here.
_INT_CUES = re.compile(
    r"(?:destroy|exile) (?:target |up to \w+ target |all |each |those |that |another )?"
    r"(?:creature|permanent|nonland permanent|artifact|enchantment|planeswalker|tapped|attacking)"
    r"|counter (?:target|that spell|it unless)"
    r"|deals? \d+ damage to (?:any target|target creature|each (?:other )?creature|up to \w+ target)"
    r"|\bfights?\b"
    r"|gets? -\d+/-[0-9x]+|gets? \-[0-9x]+/\-[0-9x]+"
    r"|(?:each opponent|target opponent|target player|each player) sacrifices"
    r"|return target (?:creature|permanent|nonland permanent)[^.]{0,40}?hand",
    re.I)
_CA_CUES = re.compile(
    r"draws? (?:two|three|four|five|x|that many) cards?"
    r"|draw cards? equal to|draw a card for each"
    r"|\binvestigate\b",
    re.I)

# The audit net MUST be a SUPERSET of what the precise classifier can match, or a
# phrasing can be missed by BOTH — which is exactly what happened to Repulsive
# Mutation ("counter up to one target spell unless…"): too narrow for the Counter
# pattern AND absent from the broad cue, so the under-read wasn't even flagged.
# Unioning the precise interaction/card-advantage patterns in makes that structurally
# impossible: anything the classifier CAN see, the net also sees, and the flag still
# only fires when the classifier tagged no matching role.
# Parenthetical REMINDER text. Non-nested is enough — MTG never nests reminders.
_REMINDER_RE = re.compile(r"\([^()]*\)")

_INT_CUE_PATS = [_INT_CUES] + [p for lbl in sorted(_INTERACTION_ROLES)
                               for p in _ROLE_COMPILED_MAP[lbl]]
_CA_CUE_PATS = [_CA_CUES] + _ROLE_COMPILED_MAP["Card advantage"]


def role_coverage_flags(cards, carddata):
    """Cards whose oracle text likely holds a role the precise classifier MISSED — a
    coverage self-audit so a silent under-count becomes an explicit 'read these.'
    Returns (unclassified, under_read):
      • unclassified — noncreature, nonland spells that matched NO functional role
        (the classifier had nothing to say about them; read the text yourself),
      • under_read   — (name, axis) where a broad interaction / card-advantage cue
        fires but classify_roles tagged no matching role (a likely under-read).
    Neither changes any count — both are review prompts (grade from full text via
    card.py / deck.py text)."""
    unclassified, under_read, no_data = [], [], []
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        cd = carddata.get(n.lower())
        if not cd:
            # No library/pool row at all (e.g. a WIP craft target): role_tally can't
            # read its text, so it silently contributes 0 interaction/card-advantage.
            # Surface it so the under-count is explicit, not invisible (audit F14).
            no_data.append(n)
            continue
        if "Land" in _primary_type(cd.get("type") or ""):
            continue
        text = cd.get("text") or ""
        roles = set(classify_roles(text))
        # Match the cues against the SAME normalized form classify_roles uses, and
        # against the superset net, so the audit can't be blind where the classifier is
        # — minus REMINDER TEXT. Ward's reminder ("…counter it unless that player pays
        # {2}.") tripped the Counter cue, so every warded creature in the collection was
        # reported as a missed interaction piece: a false cue, which is the one thing
        # that degrades this list (it exists to be read card-by-card, so noise in it is
        # expensive). Stripping reminders can't create a blind spot, because the net
        # includes the precise patterns and the flag only fires when NO role was tagged
        # — anything a role pattern sees in reminder text is already a tagged role.
        t = _REMINDER_RE.sub(" ", _norm_role_text(text))
        missed = []
        if any(p.search(t) for p in _INT_CUE_PATS) and not (roles & _INTERACTION_ROLES):
            missed.append("interaction")
        # A loot is deliberately NOT card advantage, so strip it before testing the
        # card-advantage cue — otherwise every looter would be reported as an
        # under-read of the very rule that excludes it.
        if (any(p.search(_LOOT_RE.sub(" ", t)) for p in _CA_CUE_PATS)
                and "Card advantage" not in roles):
            missed.append("card advantage")
        if missed:
            under_read.append((n, "/".join(missed)))
        # `_primary_type` (G-63), not a whole-line scan: a card whose FRONT is a
        # noncreature spell but whose BACK is a Creature was dropped from the
        # unclassified list, so the uncertainty channel under-reported on exactly the
        # DFC class this codebase keeps tripping over (broad-scan Batch G).
        elif not roles and "Creature" not in _primary_type(cd.get("type") or ""):
            unclassified.append(n)
    return unclassified, under_read, no_data


def _norm_role_text(text):
    """Lowercased, unicode-minus-normalized oracle text with REMINDER TEXT removed — the
    one form every role pattern and coverage cue is matched against, so the precise
    classifier and its audit net can't disagree about the input either.

    Reminder text is stripped HERE since BS8-30: `role_coverage_flags` stripped it and
    `classify_roles` did not, so a Treasure maker's "(… Add one mana of any color.)"
    read as Ramp, every Food maker as Lifegain, every delve/embalm reminder as
    Recursion, and "End the turn" reminders as a Sweeper in five decks — the exact
    K-09 disagreement, one layer down. A keyword's own word stays (the reminder
    explains it; the keyword is outside the brackets)."""
    return _REMINDER_RE.sub(" ", (text or "").lower().replace("−", "-"))


def classify_roles(text):
    """Return the set of functional-role labels a card's oracle text matches."""
    t = _norm_role_text(text)
    roles = {label for label, pats in _ROLE_COMPILED if any(p.search(t) for p in pats)}
    if "Card advantage" in roles and _LOOT_RE.search(t):
        # Blank the loot clause(s) and re-test: only drop the role when nothing ELSE
        # in the text is a real net-positive draw (a card can loot AND draw).
        stripped = _LOOT_RE.sub(" ", t)
        if not any(p.search(stripped) for p in _ROLE_COMPILED_MAP["Card advantage"]):
            roles.discard("Card advantage")
    return roles


# Mana production, detected broadly enough to catch dorks the "Ramp / fixing" role
# misses: that role keys on the "{T}: add {SYM}" template, but a flavor-keyword dork
# (Bloom Tender's "Vivid — {T}: … add one mana …") phrases it as "add one mana" and
# slips through. Used by the tier tune plan to warn when a proposed cut is a mana
# source (losing it hurts the manabase) — a heuristic flag, not a role reclassification.
_MANA_PRODUCE_RE = re.compile(
    r"\badd\s+\{[wubrgcpx0-9/]"        # "add {G}", "add {C}{C}", "add {W/U}"
    r"|\badd\b[^.\n]{0,40}?\bmana\b",  # "add one mana", "add two mana of any color"
    re.IGNORECASE)


def _produces_mana(text):
    """True if a card's text taps for / produces mana (a dork, rock, or ramp spell) —
    broader than the 'Ramp / fixing' role so an 'add one mana' phrasing still counts."""
    return bool(text and _MANA_PRODUCE_RE.search(text))


# The roles that make a card a keeper almost regardless of theme fit — a removal
# spell, a card-advantage engine, ramp, a cost-reducer, a payoff. `cuts`/`suggest-homes`
# weight these extra so a strong-but-off-tribe card (Cosmic Cube, Shuri, Mjölnir) stops
# floating to the TOP of the cut list just because its synergy tags don't match the
# deck's central themes. Incidental roles (lifegain, a combat trick, an anthem) get the
# base credit only. Still a shortlist signal — grade the finalists from oracle text.
IMPACT_ROLES = {"Removal (spot)", "Sweeper", "Counter", "Card advantage",
                "Ramp / fixing", "Cost reduction / cheat", "Payoff / engine",
                "Reanimation", "Burn / drain"}


def _role_credit(roles, saturation=None):
    """Keep-score credit for a card's functional roles: base 3 each, +6 more for each
    IMPACT role, so a card that does a high-value job clears the no-role 'filler' band
    (theme-fit only, ~0–8) and doesn't rank as a top cut. It can't fully offset a large
    theme-fit gap — an off-theme power card (Cosmic Cube, The Ten Rings) still sorts
    low in a tuned deck, which is inherent to a synergy model and exactly why `cuts`
    prints full oracle text and wishlist ranking pairs fit with a hand-graded Power.

    When `saturation` (role → how many copies the deck ALREADY runs of that role) is
    passed, the +6 IMPACT bonus DIMINISHES with saturation — the 1st removal spell is
    worth the full bonus, the 8th very little (diminishing returns, improvement #1). So
    `suggest` stops over-valuing the Nth copy of an effect the deck is already deep in,
    and `cuts` ranks a redundant piece as more cuttable while protecting a scarce one
    (the deck's only counterspell keeps its full credit). With no `saturation` the
    credit is the original flat value (unchanged for any caller that doesn't opt in)."""
    base = 3 * len(roles)
    impact_roles = set(roles) & IMPACT_ROLES
    if saturation is None:
        return base + 6 * len(impact_roles)
    bonus = 0.0
    for r in impact_roles:
        have = max(0, saturation.get(r, 0))
        bonus += 6.0 / (1 + 0.5 * have)   # have 0→6, 1→4, 2→3, 3→2.4, 6→~1.5
    return base + bonus


def _curve_gap_factor(mv, curve):
    """A bounded (0.85–1.15) multiplier on a candidate's `suggest` score by how its mana
    value fits the deck's CURVE (improvement #2). Archetype-agnostic and deliberately
    gentle so it re-ranks near-ties without overriding a clear theme-fit winner:

      • an OVER-FULL bucket (more copies than the deck's average slot) is gently
        penalized at ANY cost — you don't need the 9th three-drop;
      • a THIN CHEAP bucket (MV ≤ 3, below average) is gently boosted — nearly every
        deck wants its early plays filled;
      • a thin EXPENSIVE bucket is left alone (factor 1.0) — boosting top-end would be
        archetype-wrong for an aggro deck, so the curve signal never does it.

    `curve` is the deck's nonland MV histogram (bucket → copies). Returns 1.0 when the
    card's MV or the curve is unknown, so a missing mana row never distorts the score."""
    if mv is None or not curve:
        return 1.0
    b = min(int(mv), 7)
    avg = sum(curve.get(i, 0) for i in range(1, 8)) / 7.0
    if avg <= 0:
        return 1.0
    ratio = curve.get(b, 0) / avg
    if ratio > 1.0:
        return max(0.85, 1.0 - 0.15 * (ratio - 1.0))
    # Boost a thin CHEAP spell slot (MV 1–3) only; MV 0 (lands / free spells) isn't a
    # curve slot — the deck curve counts nonland cards, so a land would else read as a
    # perpetually-thin "0-drop" and get an unearned boost.
    if 1 <= b <= 3 and ratio < 1.0:
        return min(1.15, 1.0 + 0.15 * (1.0 - ratio))
    return 1.0


_HOME_CURVE_CAP = 0.15  # ±15%, matching _curve_gap_factor's bound


def _home_curve_fit(card_mv, deck_avg_mv):
    """A bounded (0.85–1.0) SORT multiplier for `suggest-homes` (finding #5): gently
    penalize placing a card whose mana value sits well ABOVE a deck's average nonland MV —
    a top-heavy / win-more add (an ~11-mana Aettir and Priwen) fits an aggressive low-curve
    deck worse than a midrange one, which pure theme-overlap can't see. Unlike
    `_curve_gap_factor` this is keyed to the DECK'S average (constant per card in a
    suggest-homes run, so a card-MV signal alone couldn't reorder decks). It NEVER boosts
    and is capped at _HOME_CURVE_CAP, so it only reorders same-strength fits — it can't
    relabel a KEY/role-player/tangential verdict or override theme fit. Returns 1.0 when a
    MV is unknown or the card is within ~a turn of the deck's average."""
    if not card_mv or not deck_avg_mv:
        return 1.0
    excess = card_mv - deck_avg_mv
    if excess <= 2.0:                      # within ~2 MV of the average — a normal top-end,
        return 1.0                         # not a win-more; only flag genuinely heavy cards
    return max(1.0 - _HOME_CURVE_CAP, 1.0 - 0.05 * (excess - 2.0))


# Weight of the power co-signal in `suggest` (#6): power is 0–10, so at 1.0 a bomb adds
# up to ~10 — comparable to a strong role bonus, enough to lift a modest-fit bomb above a
# same-fit vanilla, but small next to a strongly-on-theme card's theme_w. Never dominant.
_SUGGEST_POWER_W = 1.0


# Cuts power co-signal (#3): fold the wishlist power model into the cut RANKING so an
# on-theme-but-WEAK card can surface as cuttable and an on-theme BOMB is protected — the
# thing pure theme-fit can't see (a vanilla body and a bomb that share one tag look
# identical to a synergy model). Centered so an average card (~5) is neutral; BOUNDED so
# it only re-ranks near-ties (theme fit stays dominant — guarded by check_suggest #7).
_CUTS_POWER_NEUTRAL = 5.0
_CUTS_POWER_W = 0.35
_CUTS_POWER_CAP = 2.5


def _cuts_power_adj(power):
    """Bounded keep-score nudge from a card's 0–10 power: >0 protects a bomb (harder to
    cut), <0 makes a weak card more cuttable. Clamped to ±_CUTS_POWER_CAP so it can only
    break near-ties, never override theme fit."""
    adj = _CUTS_POWER_W * (power - _CUTS_POWER_NEUTRAL)
    return max(-_CUTS_POWER_CAP, min(_CUTS_POWER_CAP, adj))


# Ability-distinctiveness co-signal: theme fit and power both miss a distinct question —
# is this card's ability set GENERIC TEMPLATING (the etb/tokens/sacrifice body that trips
# broad synergy-overlap everywhere) or a distinctive mechanic? `lib.card_distinctiveness`
# scores that as the max of pool tag-rarity and a structural read of the oracle text (so a
# mis-tagged distinctive card is still caught by its text shape). A generic-ability filler
# is more cuttable; a distinctive card is mildly protected. Centered at _CUTS_UNIQ_NEUTRAL,
# BOUNDED to ±cap so
# it only breaks near-ties (theme fit stays dominant — guarded by check_suggest #8). It is
# ORTHOGONAL to power (a vanilla 6/6 is high power, low distinctiveness), so it earns its
# own small term rather than folding into the power adj.
_CUTS_UNIQ_NEUTRAL = 4.0
_CUTS_UNIQ_W = 0.30
_CUTS_UNIQ_CAP = 1.5


def _cuts_uniq_adj(uniq):
    """Bounded keep-score nudge from a card's 0–10 ability-distinctiveness: >0 protects a
    distinctive-mechanic card, <0 makes a generic-ability filler more cuttable. Clamped to
    ±_CUTS_UNIQ_CAP so it only breaks near-ties, never overrides theme fit."""
    adj = _CUTS_UNIQ_W * (uniq - _CUTS_UNIQ_NEUTRAL)
    return max(-_CUTS_UNIQ_CAP, min(_CUTS_UNIQ_CAP, adj))


# A MULTIPLIER's value lives in what it does to the REST of the deck, and both halves of
# the cut score are structurally blind to that: theme-fit sees a card with few tags, and
# `_role_credit` sees no functional role, because "doubles a trigger" is not a role. So
# Delney, Streetwise Lookout — which doubles the triggered ability of every creature in
# deck 46's small-body engine layer — ranked as the WEAKEST card in the deck, and
# Valkyrie's Call ranked near it. The information was already in the codebase: `doubler_
# axis`/`doubler_support` were built for `suggest-homes` and score Delney correctly, but
# `cuts` never asked. This routes the SAME primitives into the cut score rather than
# adding a second model, so the two cannot disagree about what a doubler is worth.
_CUTS_MULT_CAP = 3.0
_CUTS_MULT_MIN_SOURCES = 4      # below this, a doubler genuinely has nothing to double
_CUTS_MULT_PER_SOURCE = 0.35


def _cuts_multiplier_adj(support, axis=None):
    """Keep-bias for a doubler, proportional to the magnitude it multiplies.

    Bounded to 0…_CUTS_MULT_CAP and ZERO below the axis floor — a doubler in a deck that
    does not feed its axis really is cuttable, which is why this only ever RAISES a
    keep-score and never lowers one: the no-support case is already handled by theme-fit,
    and subtracting there would punish the same card twice.

    Density is counted ABOVE the floor, and the floor is the AXIS's (`doubler_calib`)
    where that axis has its own, else this term's `_CUTS_MULT_MIN_SOURCES`. The rate and
    cap stay this term's own. Without the per-axis floor this saturated even harder than
    the `suggest-homes` boost it mirrors: at 0.35/source it pins its 3.0 cap by 9 feeders,
    and the `triggers` axis has a roster MINIMUM of 10 — so every deck on the roster got
    the identical maximum keep-bias for any trigger doubler, on 100% of decks rather than
    the 92% the fit boost hit. Two terms, one bug, and the code comment beside the caller
    promising the two models "can't disagree" was what made it worth checking both.
    """
    floor = (_DOUBLER_CALIB[axis][0] if axis in _DOUBLER_CALIB
             else _CUTS_MULT_MIN_SOURCES)
    if support < floor:
        return 0.0
    return min(_CUTS_MULT_CAP, (support - floor + 1) * _CUTS_MULT_PER_SOURCE)


# `suggest --lands` co-signals. A land's dominant value is FIXING (wishlist._land_value,
# 0–10), but a land's ABILITY can also play the deck (Abandoned Air Temple's team-pump in a
# go-wide deck, Fire Nation Palace's firebending ramp) — so a bounded SYNERGY term lifts a
# land whose text matches the deck's central themes, and a bounded SHORTFALL term favors a
# land producing the color the deck is scarcest on. Both are CAPPED so fixing stays dominant
# (a land is chosen for its mana first) — guarded by check_suggest anchor 9.
_LAND_SYN_CAP = 2.0
_LAND_SHORT_CAP = 1.5


def _land_synergy_bonus(land_tags, theme_w):
    """Bounded [0, _LAND_SYN_CAP] nudge: a land whose synergy tags hit the deck's central
    themes ranks above a vanilla dual. Scaled by the land's STRONGEST shared theme relative
    to the deck's top theme, so a land on the deck's spine gets the full cap and an incidental
    overlap gets little. 0 when the land shares nothing (a plain dual) — fixing then decides."""
    if not theme_w or not land_tags:
        return 0.0
    shared = [theme_w[t] for t in land_tags if t in theme_w]
    if not shared:
        return 0.0
    mx = max(theme_w.values()) or 1
    return round(min(_LAND_SYN_CAP, _LAND_SYN_CAP * (max(shared) / mx)), 2)


def _land_shortfall_bonus(land_colors, deficit):
    """Bounded [0, _LAND_SHORT_CAP] nudge toward the color the deck is SHORTEST on. `deficit`
    is {color: >=0 scarcity} (pip-demand share minus source share); a land producing the
    scarcest color it covers gets the most. 0 when it produces no under-served color."""
    if not deficit or not land_colors:
        return 0.0
    mx = max(deficit.values()) or 0.0
    if mx <= 0:
        return 0.0
    best = max((deficit.get(c, 0.0) for c in land_colors), default=0.0)
    return round(min(_LAND_SHORT_CAP, _LAND_SHORT_CAP * best / mx), 2)


# ── The "needs model": suggest --ramp / --interaction / --needs ──────────────────────────
# suggest_scored answers "what SYNERGIZES with my themes"; these answer "what my deck
# structurally LACKS" (fixing, acceleration, interaction) — the axes a theme model can't see
# by design (the idf model was BUILT to reject catch-alls, so we never weaken its filter; we
# add a parallel needs-aware path instead). Every nudge below is BOUNDED so it re-ranks within
# a needs-filtered candidate set and can't manufacture a catch-all pick (check_suggest #10).
_RAMP_ACCEL_CAP = 2.0       # a top-heavy deck wants acceleration; a low-curve deck wants none
_RAMP_RESTRICT_CAP = 1.5    # a restricted-mana dork ('add R only for Equipment') matching the deck
_INT_SCALE_CAP = 1.5        # a board-scaling removal spell the deck's board actually supports


def _accel_want(avg_mv, heavy_share):
    """0–1 'this deck wants acceleration', from curve top-heaviness: a high average MV and a
    large share of 4+-drops => wants ramp; a lean aggro curve => ~0. Bounded [0, 1]."""
    a = (avg_mv - 2.3) / 1.2           # 2.3 avg -> 0, 3.5 avg -> 1
    h = (heavy_share - 0.15) / 0.30    # 15% at 4+ -> 0, 45% -> 1
    return round(max(0.0, min(1.0, 0.5 * max(0.0, a) + 0.5 * max(0.0, h))), 2)


_RESTRICT_RE = re.compile(
    r"spend this mana only to (?:cast|activate)[^.\n]*?\b"
    r"(equipment|artifact|instant|sorcery|creature|enchantment)", re.I)


def _ramp_restriction_fit(text, type_share):
    """Bounded ± nudge for a RESTRICTED mana source ('add R, spend only to cast an Equipment
    spell'): + when that type is well-represented in the deck, − when it's scarce (a spell-only
    dork in a creature deck is near-dead), 0 for unrestricted mana. `type_share` maps a type
    word -> fraction of the deck's nonland cards of that type. Centered at ~20% representation."""
    m = _RESTRICT_RE.search(text or "")
    if not m:
        return 0.0
    kind = m.group(1).lower()
    share = (type_share.get("instant", 0) + type_share.get("sorcery", 0)
             if kind in ("instant", "sorcery") else type_share.get(kind, 0))
    val = _RAMP_RESTRICT_CAP * (share - 0.20) / 0.20
    return round(max(-_RAMP_RESTRICT_CAP, min(_RAMP_RESTRICT_CAP, val)), 2)


_INT_FIGHT_RE = re.compile(r"\bfights?\b[^.\n]*?target creature", re.I)
_INT_COUNT_RE = re.compile(
    r"number of (?:\w+ )?(creatures|artifacts|equipment|permanents|lands) you control", re.I)


def _int_scaling(text):
    """The deck-STATE axis a removal card scales with, or None. 'fight' scales with YOUR
    creatures' power; 'damage = number of X you control' scales with that count; an {X} deal/
    destroy scales with mana. These are the deck-dependent removal cards a tag model can't grade
    in the abstract — surface them and FLAG the axis for a human read (never silently boost)."""
    t = text or ""
    if _INT_FIGHT_RE.search(t):
        return "fight"
    m = _INT_COUNT_RE.search(t)
    if m:
        return m.group(1).lower()
    if "{X}" in t and re.search(r"\b(deal|destroy|damage)\b", t, re.I):
        return "x-cost"
    return None


def _int_scaling_boost(axis, deck_metric):
    """Bounded [0, _INT_SCALE_CAP] boost for a board-scaling removal spell the deck actually
    supports. `deck_metric` is a 0–1 strength on the card's axis (avg creature power for fight,
    board density for a count-based card). Modest by design — the human confirms from the flag;
    0 for a non-scaling card or a deck that can't turn the scaling on."""
    if not axis:
        return 0.0
    m = max(0.0, min(1.0, deck_metric))
    return round(min(_INT_SCALE_CAP, _INT_SCALE_CAP * m), 2)


def deck_needs(d):
    """The deck's STRUCTURAL profile — the axes suggest_scored's theme model can't see.
    Returns {colors, sources, deficit, avg_mv, accel, interaction, int_target, int_short,
    type_share, creature_power, board_density, central, names}. Shared by --ramp / --interaction
    / --needs so they can't drift. Pure read (no writes)."""
    meta = load_card_meta()
    dmeta, cards = parse_deck_file(d["path"])
    mana_map, carddata = load_mana(), load_card_data()
    deck_colors = _declared_colors(dmeta)
    if not deck_colors:
        # COSTS, not identity. `suggest_scored` derives an undeclared deck's castable
        # colours from mana costs and says why — "never color identity, so a card's
        # off-color activated abilities don't widen the deck and surface uncastable
        # picks" (audit F3/F15) — while this function and `suggest_lands` fell back to
        # identity, which is the same question answered two ways on the paths G-38 routes
        # a scorecard deficit to. Latent today (all 99 decks declare `#: colors:`) and
        # exactly the G-45 shape: two siblings, different filters (BS4-12).
        deck_colors = _deck_castable_colors(dmeta, cards, mana_map)

    theme_w, names = {}, set()
    sources = {c: 0 for c in deck_colors}
    demand = {c: 0 for c in deck_colors}
    nonland = mv_sum = mv_n = heavy = cre = equip = arti = inst = sorc = ench = 0
    for q, n, _s, _c in cards:
        nl = n.lower()
        names.add(nl.split(" // ")[0])
        if nl in BASICS:
            col = BASIC_COLOR.get(nl)
            if col in sources:
                sources[col] += q
            continue
        m = meta.get(nl)
        cd = carddata.get(nl)
        tline = (cd["type"] if cd else "") or ""
        if "Land" in _primary_type(tline):
            for col in (m["colors"] if m else set()):
                if col in sources:
                    sources[col] += q
            continue
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
        entry = mana_map.get(nl)
        mv = entry[1] if (entry and entry[1] is not None) else None
        nonland += q
        if mv is not None:
            mv_sum += mv * q
            mv_n += q
            if mv >= 4:
                heavy += q
        if entry and entry[0]:
            strict, _hy = parse_pips(entry[0])
            for col, cnt in strict.items():
                if col in demand:
                    demand[col] += cnt * q
        pt = _primary_type(tline)
        low = tline.lower()
        if "Creature" in pt:
            cre += q
        if "artifact" in low:
            arti += q
        if "equipment" in low:
            equip += q
        if "Instant" in pt:
            inst += q
        if "Sorcery" in pt:
            sorc += q
        if "Enchantment" in pt:
            ench += q

    tot_d = sum(demand.values()) or 1
    tot_s = sum(sources.values()) or 1
    deficit = {c: max(0.0, demand[c] / tot_d - sources[c] / tot_s) for c in deck_colors}
    avg_mv = round(mv_sum / mv_n, 2) if mv_n else 0.0
    heavy_share = heavy / mv_n if mv_n else 0.0
    tally = role_tally(cards, carddata)
    ts = (lambda x: round(x / nonland, 2) if nonland else 0.0)
    central = _central_themes(theme_w)
    return {
        "colors": deck_colors, "sources": sources, "deficit": deficit, "avg_mv": avg_mv,
        "accel": _accel_want(avg_mv, heavy_share),
        "interaction": tally.get("interaction", 0), "int_target": 5,
        "int_short": tally.get("interaction", 0) < 5,
        "type_share": {"creature": ts(cre), "artifact": ts(arti), "equipment": ts(equip),
                       "instant": ts(inst), "sorcery": ts(sorc), "enchantment": ts(ench)},
        "board_density": round(min(1.0, (cre + equip) / max(1, nonland)), 2),
        "central": central, "central_w": {t: theme_w[t] for t in central},
        "names": names, "theme_w": theme_w,
        "format": (dmeta.get("format") or "").strip().lower(),
    }


def _scaling_metric(axis, needs):
    """Map a removal card's scaling AXIS (_int_scaling) to the deck's 0–1 strength on it:
    a FIGHT card wants a deck that makes big creatures (equipment/creature density); a
    'number of X you control' card wants that permanent to be dense; an {X} card wants ramp."""
    ts = needs["type_share"]
    if axis == "fight":
        return min(1.0, ts.get("creature", 0) + ts.get("equipment", 0))
    if axis in ("creatures", "permanents"):
        return needs["board_density"]
    if axis in ("equipment", "artifacts"):
        return min(1.0, ts.get("equipment", 0) + ts.get("artifact", 0)) if axis == "artifacts" \
            else ts.get("equipment", 0)
    if axis == "x-cost":
        return needs["accel"]
    return needs["board_density"]


def _produced_colors(text, deck_colors):
    """The colors a mana source can make, scoped to the deck: an 'any color / any type' dork
    reads as all the deck's colors; else the explicit `{W}`… symbols in its text."""
    t = text or ""
    if re.search(r"any color|any type|mana of any", t, re.I):
        return set(deck_colors)
    return {c for c in "WUBRG" if "{" + c + "}" in t}


_power_seed_warned = False  # one-time guard for the A14 degradation warning


def _power_seed(row):
    """A card's heuristic power (0–10) for suggest's card-quality co-signal (#6) — the
    same rarity+role estimate the wishlist seeds Power with, so an owned/craftable bomb
    surfaces even on a modest theme fit. Lazy-imports wishlist (which itself lazy-imports
    deck) to avoid a load cycle; returns 0.0 if unavailable, so power just drops out."""
    try:
        import wishlist
        return wishlist._seed_power(row)
    except Exception as e:
        # Degrade (power drops out of the ranking) but say so ONCE — this runs per
        # candidate in a hot loop, so a silent 0.0 for every card would hide a real
        # regression in the power seed (audit A14).
        global _power_seed_warned
        if not _power_seed_warned:
            _power_seed_warned = True
            eprint(f"WARN:  power co-signal unavailable ({type(e).__name__}: {e}); "
                   "suggest ranking proceeds without the power dimension.")
        return 0.0


# --------------------------------------------------------------------------- #
# Engine roles — enabler vs payoff WITHIN a theme (improvement #3)
# --------------------------------------------------------------------------- #
# A synergy tag says "sacrifice" appears in the deck; it does NOT say which cards
# FEED the engine (sac outlets / fodder) and which cards PAY IT OFF (death triggers).
# The most common real deckbuilding flaw — payoffs with no enablers (or vice versa) —
# is invisible to a bag-of-tags model. For the handful of themes that are actual
# two-sided engines, classify each card's oracle text as ENABLER (produces/enables the
# resource) and/or PAYOFF (rewards/consumes it), so `engine_balance` can flag a
# lopsided engine. Heuristic and text-based (so it catches an untagged outlet too);
# the `engines` command prints the card lists for a human read, like `cuts`/`tribes`.
ENGINE_THEMES = {
    "counters": {
        "enabler": [
            r"put (a|one|two|three|four|x|that many|another|\d+)[^.]*\+1/\+1 counter",
            r"enters[^.]*with[^.]*\+1/\+1 counter", r"\bproliferate\b", r"\badapt\b",
            r"\bbolster\b", r"\bsupport \d", r"\bmonstrosity\b", r"\btraining\b",
        ],
        "payoff": [
            r"for each \+1/\+1 counter",
            r"\+1/\+1 counter[^.]*(among (creatures|permanents) you control|on creatures you control)",
            # Singular AND plural passive: Wildwood Scourge's "whenever one or more
            # +1/+1 counters ARE put on another non-Hydra creature" slipped the
            # singular-only pattern — found during the deck 9 tune, the passive-voice
            # sibling of the active-voice gap fixed in broad-implement #6.
            r"whenever[^.]*\+1/\+1 counters? (is|are) (put|placed)",
            # ACTIVE voice was missing — the passive pattern above let Knight of
            # Wundagore ("Whenever you put a +1/+1 counter on another creature, put a
            # +1/+1 counter on this creature") read as roleless, and deck 36's engines
            # view reported "counters: 12 enablers, NO payoff" through three real
            # payoffs (broad-implement #6; fixture from the printed text, G-67).
            r"whenever you put (a|one|two|x|\d+)[^.]*counter",
            # The grown-past-its-base shape: Kutzil ("creatures you control each with
            # power greater than its base power") and Sovereign Okinec Ahau ("power
            # greater than that creature's base power") reward counters without ever
            # saying 'counter' in the clause.
            r"greater than (its|that creature's) base power",
            r"if[^.]*would[^.]*\+1/\+1 counter[^.]*instead", r"twice that many \+1/\+1",
            r"remove (a|one|x|\d+)[^.]*\+1/\+1 counter", r"move (a|one|any number of)[^.]*\+1/\+1 counter",
        ],
    },
    "tokens": {
        "enabler": [r"create[s]? [^.]*\btoken", r"\bpopulate\b", r"\bfabricate\b"],
        "payoff": [
            r"for each (creature|token|artifact) you control", r"creatures you control get \+",
            r"whenever a[^.]*token[^.]*enters", r"creatures you control (have|gain)",
            r"each creature you control", r"sacrifice (a|another|\w+)[^.]*token",
        ],
    },
    "sacrifice": {   # aristocrats: outlets/fodder vs death & sacrifice triggers
        # A "whenever ~ dies" trigger ('death') fires on ANY death — combat included — so
        # it is NOT sac-outlet-dependent the way a "whenever you sacrifice" payoff is.
        # engine_balance keeps them apart: only sac-triggers "sit dead" without an outlet;
        # death triggers are combat-fed when the deck has a real creature base (F-engines).
        # The passive-voice sibling `whenever[^.]*is sacrificed` matched 0 of ~15.9k
        # pool texts — Magic templates sacrifice triggers actively ("whenever you
        # sacrifice …") — and sat dead for the pattern's whole life because the
        # completeness gate's walker stopped one container level up (broad-scan
        # BS2-13, the `(?:owner|their) hand` failure verbatim). Removed rather than
        # kept-just-in-case: check_patterns now sees this table, and a pattern that
        # matches nothing FAILS the build, which is the forcing function working.
        "enabler": [r"\bsacrifice (a|an|another|two|three|\d+|x|it|them)\b", r"you may sacrifice"],
        "payoff": [r"whenever you sacrifice"],
        "death": [r"whenever[^.]*\bdies\b"],
    },
    "graveyard": {   # fill the yard vs use the yard (reanimator / recursion)
        # Self-recursion mechanics (flashback / escape / harmonize / …) put the card into
        # the yard THEMSELVES, so a card that plays them is its own enabler — counted on
        # BOTH sides so a graveyard full of flashback spells doesn't read as "unenabled".
        "enabler": [r"\bmill\b", r"\bsurveil\b", r"discard[^.]*card", r"put[^.]*(from|into)[^.]*graveyard",
                    r"into your graveyard", r"\bdredge\b",
                    r"\bflashback\b", r"\bescape\b", r"\bdisturb\b", r"\bunearth\b", r"\bharmonize\b",
                    r"\bjump-start\b", r"\bretrace\b", r"\baftermath\b", r"cast [^.]*from (your )?graveyard"],
        "payoff": [r"return[^.]*from (your )?graveyard to the battlefield", r"from your graveyard",
                   r"for each[^.]*in your graveyard", r"\bescape\b", r"\bflashback\b", r"\bdelve\b",
                   r"\bdisturb\b", r"\bunearth\b", r"cards? in your graveyard"],
    },
    "lifegain": {
        "enabler": [r"gain (\d+|x|that much) life", r"gains? \d+ life", r"\blifelink\b"],
        "payoff": [r"whenever you gain life", r"for each[^.]*life[^.]*gained",
                   r"if you (gained|would gain)[^.]*life", r"(the amount of )?life you gained"],
    },
    "food": {
        "enabler": [r"create[s]? [^.]*food"],
        "payoff": [r"sacrifice a food", r"for each food", r"food[^.]*you control"],
    },
}
_ENGINE_COMPILED = {
    theme: {role: [re.compile(p) for p in pats] for role, pats in sides.items()}
    for theme, sides in ENGINE_THEMES.items()
}

# A deck fielding this many creatures trades in combat often enough that a "whenever ~
# dies" death trigger is fed without any sac outlet — so combat-fed death triggers are
# exempt from the sacrifice dead-payoff flag at/above this creature count.
_COMBAT_FED_MIN = 6


def engine_roles(text):
    """{theme: {roles}} — for each engine theme, which side(s) of its two-sided engine a
    card's oracle text plays: 'enabler' (feeds the engine) and/or 'payoff' (rewards it).
    A card can be both (a sac outlet that also triggers on death) or neither. Text-based,
    so an untagged piece is still caught. `− → -` normalized like classify_roles."""
    t = (text or "").lower().replace("−", "-")
    out = {}
    for theme, sides in _ENGINE_COMPILED.items():
        hit = {role for role, pats in sides.items() if any(p.search(t) for p in pats)}
        if hit:
            out[theme] = hit
    return out


def engine_balance(cards, carddata, central, signature=frozenset(), weights=None):
    """For each engine theme CENTRAL to the deck, tally enabler vs payoff copies and a
    verdict. Only reports themes that are (a) real two-sided engines (in ENGINE_THEMES)
    and (b) central to THIS deck — so an incidental one-off doesn't raise a flag.

    `signature` (the deck's built-around themes, from `_signature_themes`) gates the
    NOISY verdicts: 'payoffs with no enablers' (dead payoffs) is a hard flag for ANY
    central engine, but 'enablers with no payoff' / a skew is only flagged for a
    SIGNATURE engine — a deck naturally has incidental lifegain/counters enablers it
    doesn't need to pay off, so those must not cry wolf.

    Returns {theme: {'enablers': [(name,q)], 'payoffs': [(name,q)], 'en': n, 'pay': n,
    'verdict': str, 'flag': bool}} ordered by the deck's theme centrality."""
    sig = {t.lower() for t in signature}
    # `central` is a SET (from `_central_themes`), and iterating it set-ordered made an
    # unchanged deck print its engines in a different order run to run under hash
    # randomization — reproduced across five runs of `engines 46` (broad-scan BS2-20,
    # the exact G-54 shape). Sort by the deck's theme WEIGHT (the centrality order the
    # docstring already promised) with the name as the tie-break, so the key is a
    # total order; callers that have no weights get stable alphabetical order.
    w = weights or {}
    central_engines = sorted((t for t in central if t.lower() in _ENGINE_COMPILED),
                             key=lambda t: (-w.get(t, 0), t.lower()))
    result = {}
    creatures = 0
    for theme in central_engines:
        result[theme] = {"enablers": [], "payoffs": [], "deaths": [],
                         "en": 0, "pay": 0, "death": 0}
    # Quantity-weighted per card, summed ACROSS lines (matching the canonical role_tally;
    # a `seen`-set + first-line q under-counted a card split over two lines, audit A11).
    qty_by_name, disp = {}, {}
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS:
            continue
        qty_by_name[nl] = qty_by_name.get(nl, 0) + q
        disp.setdefault(nl, n)
    for nl, q in qty_by_name.items():
        cd = carddata.get(nl)
        if not cd:
            continue
        n = disp[nl]
        if "Creature" in _primary_type(cd.get("type") or ""):   # FRONT face (BS4-34)
            creatures += q
        roles = engine_roles(cd.get("text") or "")
        # THE GRAVEYARD ENGINE HAS TWO OWNERS AND THE TWO SIDES DISAGREED ABOUT WHICH.
        # ENGINE_THEMES' graveyard ENABLER cues are ownership-BLIND (`\bmill\b`,
        # `discard[^.]*card` match "each opponent discards a card" / "target opponent
        # mills three"), while its PAYOFF cues are own-scoped (`from your graveyard`,
        # `cards? in your graveyard`). So a deck that fills THEIR yard and casts from it
        # counted every enabler and no payoff: deck 44a, whose plan is exactly that, read
        # "12 enablers, no payoff — your engine has no reward" while fielding four working
        # payoffs (both Tinybones, Shark Shredder, Hama — each "from THAT PLAYER's
        # graveyard"). Fixed HERE rather than in ENGINE_THEMES on purpose: that dict's
        # VALUE is hashed into the pool build stamp (G-18/K-10), so editing it would
        # defeat the freshness reuse and force a full pool refetch for a reporting bug.
        # `graveyard_dependent` already answers "whose yard does this card need" — it was
        # written for the zone-conflict flag and no other caller asked (G-40).
        if "graveyard" in {t.lower() for t in central_engines}:
            if _GY_CONSUME_OPP_RE.search(
                    _REMINDER_RE.sub(" ", _norm_role_text(cd.get("text") or ""))):
                roles.setdefault("graveyard", set()).add("payoff")
        for theme in central_engines:
            r = roles.get(theme.lower(), set())
            if "enabler" in r:
                result[theme]["enablers"].append((n, q)); result[theme]["en"] += q
            if "payoff" in r:
                result[theme]["payoffs"].append((n, q)); result[theme]["pay"] += q
            if "death" in r:
                result[theme]["deaths"].append((n, q)); result[theme]["death"] += q
    # Flags fire only off the PAYOFF side. Payoff cues ("whenever you gain life", "for
    # each +1/+1 counter") are specific, so a payoff gap is trustworthy; enabler cues
    # ("gain N life", "sacrifice a …") are broad and match incidental cards, so an
    # enabler-heavy count is NOISE — reported for the human read, never a ⚠.
    #
    # DEATH TRIGGERS ("whenever ~ dies") are combat-fed: with a real creature base they
    # never "sit dead" for lack of a sac outlet, so they count toward the payoff readout
    # but are EXEMPT from the dead-payoff flag once the deck fields ≥ _COMBAT_FED_MIN
    # creatures (fixes the go-wide/deathtouch false positive). Only genuine sac-trigger
    # payoffs ("whenever you sacrifice") stay outlet-dependent.
    for theme, d in result.items():
        en, pay, death = d["en"], d["pay"], d["death"]
        is_sig = theme.lower() in sig
        combat_fed = theme.lower() == "sacrifice" and creatures >= _COMBAT_FED_MIN
        total_pay = pay + death                          # payoffs for the readout
        dead_pay = pay + (0 if combat_fed else death)    # payoffs that truly need an enabler
        note = ""
        if death:
            note = (f", {death} combat-fed" if combat_fed
                    else f", {death} death-trigger/{creatures} creatures")
        if dead_pay >= 2 and en == 0:
            d["verdict"], d["flag"] = "payoffs but NO enablers — the payoffs sit dead", True
        elif total_pay >= 3 and en * 3 <= total_pay and dead_pay > 0:
            d["verdict"], d["flag"] = (f"payoff-heavy ({en} enabler / {total_pay} payoff{note}) — "
                                       "thin on enablers to turn the payoffs on"), True
        elif en and total_pay:
            d["verdict"], d["flag"] = f"balanced ({en} enabler / {total_pay} payoff{note})", False
        elif en >= 2 and total_pay == 0:
            d["verdict"] = (f"{en} enablers, no payoff — your engine has no reward"
                            if is_sig else f"{en} enablers, no payoff (incidental)")
            d["flag"] = False   # broad enabler side — inform, don't cry wolf
        elif total_pay and en == 0 and combat_fed:
            d["verdict"], d["flag"] = (f"death-fed ({total_pay} death-trigger payoff(s), "
                                       f"combat-fed by {creatures} creatures — no sac outlet "
                                       "needed)"), False
        elif en or total_pay:
            d["verdict"], d["flag"] = f"({en} enabler / {total_pay} payoff)", False
        else:
            d["verdict"], d["flag"] = "no enabler/payoff cards detected", False
    return result


def context_flags(text, mana_cost):
    """Mechanics whose value is deck-dependent (converge/devotion/affinity/X-cost);
    these must be graded against the deck, not from the shortlist label."""
    t = (text or "").lower()
    flags = [k for k, pats in _CONTEXT_COMPILED.items() if any(p.search(t) for p in pats)]
    if mana_cost and "{x}" in mana_cost.lower():
        flags.append("X-cost")
    return flags


def read_flags(text, mana_cost, keywords=None):
    """Caution tags for a card whose FULL text must be read before grading — the
    classes that have slipped past a role/tag label before: board-wide effects,
    modal choices, leaves-play triggers, deck-dependent scaling (context_flags),
    and alt/added costs (classify_cost). A signal to READ, not a grade."""
    t = (text or "").lower()
    flags = []
    if re.search(r"\ball creatures\b|each creature|creatures you control|"
                 r"creatures your opponents control|each opponent|each player", t):
        flags.append("board-wide")
    if re.search(r"\bchoose one\b|choose two|choose one or more|choose up to", t):
        flags.append("modal")
    if re.search(r"leaves the battlefield|\bwhen[^.]*dies\b|\bwhenever[^.]*dies\b", t):
        flags.append("leaves-play")
    flags += context_flags(text, mana_cost)
    cheaper, gated = classify_cost(keywords, text)
    if cheaper:
        flags.append("◊ " + ", ".join(cheaper))
    if gated:
        flags.append("△ " + ", ".join(gated))
    return flags


def cmd_text(args):
    """Dump the FULL oracle text of every card in a deck — the phased-ingestion read
    that grading a keep/cut/swap must be based on, never a role/tag label or a
    truncated field (the recurring mis-grade in past sessions). Flags cards whose
    text hides something a label can miss (board-wide / modal / leaves-play /
    deck-dependent / alt-cost). Basics are omitted."""
    import textwrap
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    carddata, mana, kw = load_card_data(), load_mana(), load_keywords()
    _, cards = parse_deck_file(d["path"])
    agg, order = {}, []
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS:
            continue
        if nl not in agg:
            agg[nl] = [0, n]
            order.append(nl)
        agg[nl][0] += q

    nonland, land = [], []
    for nl in order:
        cd = carddata.get(nl)
        tline = (cd["type"] if cd else "") or ""
        (land if "Land" in _primary_type(tline) else nonland).append(nl)

    print(f"Deck {d['id']}: {d['name'] or d['id']} — full card text (read before grading)")
    for group, label in ((nonland, "NONLAND"), (land, "NONBASIC LANDS")):
        if not group:
            continue
        print(f"\n══ {label} ({len(group)}) ══")
        for nl in group:
            qty, disp = agg[nl]
            cd = carddata.get(nl)
            tline = (cd["type"] if cd else "") or "?"
            text = (cd["text"] if cd else "") or ""
            cost, mv = (mana.get(nl) or (None, None))
            print(f"\n• {qty}× {disp}   [{tline}]" + (f"   ·  MV {mv}" if mv is not None else ""))
            card_kw = kw.get(nl) or []
            if card_kw:
                # Surface Scryfall's per-card keywords so a named mechanic (Warp,
                # Increment, …) is never skimmed over as "just a word" — its meaning
                # is in the oracle text below, but the label makes sure it's read.
                print(f"    ⌘ keywords: {', '.join(k.title() for k in card_kw)}")
            flags = read_flags(text, cost, kw.get(nl))
            if flags:
                print(f"    ⚠ {' · '.join(flags)}")
            # A resolved row (real type line) with blank text is a GENUINE vanilla
            # creature (K-11), not an enrichment failure — the old message sent a
            # session to Scryfall to re-learn that (broad-implement #3).
            if not text:
                text = ("(no rules text — a vanilla creature (K-11), not a data gap)"
                        if tline else
                        "(no oracle text on file — card not resolved; enrich/build the pool)")
            for para in text.split("\n"):
                for line in (textwrap.wrap(para, width=90) or [""]):
                    print(f"    {line}")
    print("\nGrade every keep / cut / swap from the text above — not a role or tag label.")
    return 0


def cmd_stats(args):
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}.")
        return 1
    carddata = load_card_data()
    meta, cards = parse_deck_file(d["path"])

    colors, types, total = {}, {}, 0
    nonland_names = []
    for q, n, s, c in cards:
        total += q
        cd = carddata.get(n.lower())
        tline = (cd["type"] if cd else "") or ""
        ptype = "Land" if n.lower() in BASICS else _primary_type(tline)
        types[ptype] = types.get(ptype, 0) + q
        if ptype == "Land":
            continue
        nonland_names.append(n)
        col = (cd["colors"] if cd else "") or ""
        if col.lower() == "colorless":
            colors["C"] = colors.get("C", 0) + q
        else:
            for ch in col.upper():
                if ch in "WUBRG":
                    colors[ch] = colors.get(ch, 0) + q

    print(f"Deck {d['id']}: {d['name'] or d['path']}  ({total} cards)")
    print("\nTypes:")
    for t, n in sorted(types.items(), key=lambda kv: -kv[1]):
        print(f"  {t:13} {n:3}  {'#' * n}")
    print("\nColor identity (rough — run `mana` for hybrid-aware requirements):")
    for ch in "WUBRGC":
        if colors.get(ch):
            print(f"  {ch}  {colors[ch]:3}  {'#' * colors[ch]}")

    # Mana curve from real mana values.
    # COPY, not the memoized table itself: `fetch_missing_mana` MUTATES the dict it
    # is given, and `load_mana` is `@_file_memo`-cached — so live-fetched rows leaked
    # into a table every other caller shares. `_file_memo` rests the whole memo on
    # "every caller treats these tables as READ-ONLY … if you ever need to mutate
    # one, copy it first", and five call sites did not (broad-scan BS5-13). In the
    # Flask editor — one long-lived process — that made deck B's Stats tab compute
    # its curve from costs deck A's Mana tab had fetched, disagreeing with the CLI.
    mana = dict(load_mana())
    fetch_missing_mana(sorted(set(nonland_names)), mana)
    curve, unknown = {}, 0
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        d2 = carddata.get(n.lower())
        if d2 and "Land" in _primary_type(d2["type"]):
            continue
        entry = mana.get(n.lower())
        mv = entry[1] if entry else None
        if mv is None:
            unknown += q
            continue
        bucket = mv if mv < 7 else 7
        curve[bucket] = curve.get(bucket, 0) + q
    print("\nMana curve (nonland):" + (f"  [{unknown} unknown]" if unknown else ""))
    for b in range(0, 8):
        if curve.get(b):
            label = f"{b}+" if b == 7 else str(b)
            print(f"  {label:>2} MV  {curve[b]:3}  {'#' * curve[b]}")

    # Cost nature: cheaper-than-MV cards, and cards whose abilities/modes carry
    # an added cost (from Scryfall keywords + oracle text). The printed curve
    # doesn't capture either, so surface both.
    kw_by = load_keywords()
    cheaper, gated = [], []
    seen_f = set()
    for q, n, s, c in cards:
        if n.lower() in BASICS or n in seen_f:
            continue
        d2 = carddata.get(n.lower())
        if not d2 or "Land" in _primary_type(d2["type"]):
            continue
        ch, ga = classify_cost(kw_by.get(n.lower()), d2["text"])
        if ch or ga:
            seen_f.add(n)
            if ch:
                cheaper.append((n, ", ".join(ch)))
            if ga:
                gated.append((n, ", ".join(ga)))
    if cheaper:
        print("\nEffective cost may be LOWER than printed MV (◊):")
        for n, r in cheaper:
            print(f"  ◊ {n} — {r}")
    if gated:
        print("\nAbility/mode has an ADDED cost or condition — check text (△):")
        for n, r in gated:
            print(f"  △ {n} — {r}")

    xs = x_cost_cards(cards, carddata, mana)
    if xs:
        print("\nX-COST cards — the curve books these at MV 1, X counts as 0 (✕):")
        for n, c in xs:
            print(f"  ✕ {n} — {c}")
        print(f"  Read avg MV and the early-drop count with that in mind: {len(xs)} card(s) "
              "register cheaper than you will cast them.")

    # Functional roles: what jobs the nonland spells actually do. Heuristic from
    # oracle text (see classify_roles) so the tune-deck health scorecard can
    # MEASURE interaction / card advantage / ramp instead of eyeballing it.
    role_counts = role_tally(cards, carddata)
    if any(v for k, v in role_counts.items() if k in ROLE_ORDER):
        print("\nFunctional roles (heuristic from card text; a card can fill several):")
        for label in ROLE_ORDER:
            cnt = role_counts.get(label, 0)
            if cnt:
                print(f"  {label:20} {cnt:3}  {'#' * cnt}")
        # Once-per-card union (a modal removal+counter card counts once), matching the
        # audit and quality/tier vectors — NOT the sum of the buckets above.
        print(f"  {'interaction total':20} {count_conf(role_counts, 'interaction'):>7}  "
              "(distinct removal/sweeper/counter cards; +N? = cards whose text reads like "
              "interaction the classifier could NOT tag)")
        print(f"  {'card advantage':20} {count_conf(role_counts, 'card_advantage'):>7}")

    # PROTECTION axis. The role table's "Protection / trick" bucket mixes combat pumps
    # in with real answers to removal, so a deck could show a healthy trick count while
    # having no way at all to keep its key permanent alive. Report the narrow measure,
    # and say so loudly at zero — especially when a `#: protect:` header names cards the
    # deck is built around, which is the case where a single removal spell ends the game
    # plan. (Found by hand-grepping a deck, not by any tool — that gap is the point.)
    prot = role_counts.get("protection", 0)
    print(f"  {'protection':20} {prot:3}  (ward/hexproof/indestructible-class — real "
          "answers to removal, not combat pumps)")
    if not prot:
        signature = _protected(meta)
        if signature:
            print(f"    ⚠ ZERO protection, but `#: protect:` names {len(signature)} "
                  f"build-around card(s) ({', '.join(sorted(signature)[:3])}"
                  + ("…" if len(signature) > 3 else "")
                  + ") — one removal spell undoes the plan.")
        else:
            print("    ⚠ ZERO protection — nothing here answers targeted removal on a key "
                  "permanent; fine for a spell-based deck, a real gap for a threat-based one.")

    # Power-threshold payoffs. A "power 4 or greater" trigger reads unconditional to a
    # synergy model, but only fires off bodies that meet the bar on their PRINTED stats —
    # and an X-creature or a counters payoff is very often printed 0/0. This is measurable
    # only since card-pool.csv started carrying Power/Toughness.
    for name, attr, bar, qualify, total, timing in power_threshold_flags(cards, carddata):
        head = (f"\n  ⚠ {name} keys on {attr} {bar}+, but only {qualify} of {total} "
                f"creature copies are printed at {attr} {bar}+ — ")
        if timing == "enters":
            print(head + "the trigger is far more conditional than the card reads. "
                  "(Printed stats: a body that GROWS after it enters still won't "
                  "satisfy an ENTERS trigger.)")
        elif timing == "attack":
            print(head + "checked at ATTACK time, so bodies pumped after entering DO "
                  "qualify. Read the printed count as a FLOOR — in a deck that grows "
                  "its board, the gate is looser than this number.")
        else:
            print(head + "more conditional than the card reads. (Printed stats — read "
                  "the trigger's own timing before believing the count.)")

    # Interaction profile (#5): the raw count treats all interaction alike, but a suite
    # that's all sorcery-speed and creature-only has real gaps. Break it down by speed
    # and by whether it can answer a NONCREATURE permanent (planeswalker / enchantment /
    # artifact), and flag the gaps — measured, not eyeballed.
    ip = interaction_profile(cards, carddata)
    if ip["total"]:
        print(f"\n  Interaction profile: {ip['total']} piece(s) — {ip['instant']} instant-speed"
              f" / {ip['sorcery']} sorcery-speed · {ip['noncreature']} can answer a noncreature "
              "permanent (pw/ench/artifact)")
        for f in ip["flags"]:
            print(f"    ⚠ {f}")

    # Coverage self-audit (F15): the classifier is precise but misses phrasings, so a
    # count can silently UNDER-read. Surface the cards whose text reads like a role it
    # didn't tag, so the miss becomes an explicit "verify" instead of a silent gap.
    unclassified, under_read, no_data = role_coverage_flags(cards, carddata)
    if no_data:
        print(f"\n⚠ {len(no_data)} card(s) not in library/pool — no oracle text on file, so"
              " the interaction / card-advantage counts are a FLOOR (they contribute 0):")
        print(f"    {', '.join(no_data[:8])}{'…' if len(no_data) > 8 else ''}"
              "  — enrich them (build_pool.py) for a real count")
    if under_read:
        print("\n⚠ Possible UNDER-COUNT — text reads like a role the classifier didn't tag;"
              " verify from full text (card.py):")
        for name, axis in under_read:
            print(f"    {name}  → looks like {axis}")
    if unclassified:
        print(f"\n  (classifier found no role for {len(unclassified)} noncreature spell(s): "
              f"{', '.join(unclassified[:6])}{'…' if len(unclassified) > 6 else ''} — read if grading)")

    # Engine balance (#3): flag a lopsided two-sided engine (payoffs with no enablers,
    # or a lopsided signature engine) among the deck's CENTRAL themes — the detail and
    # card lists are in `deck.py engines`.
    cardmeta = load_card_meta()
    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = cardmeta.get(n.lower())
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    signature = _signature_themes(meta, cards, cardmeta)
    flagged = [(t, info) for t, info in
               engine_balance(cards, carddata, _central_themes(theme_w), signature,
                              weights=theme_w).items()
               if info["flag"]]
    if flagged:
        print(f"\n⚠ Engine balance (detail: `deck.py engines {d['id']}`):")
        for t, info in flagged:
            print(f"    {t}: {info['verdict']}")

    # Zone conflicts — a card that EMPTIES a zone this deck needs populated. Engine
    # balance above asks "are the two sides of the engine in proportion"; this asks the
    # different question "is something here working AGAINST the engine", which no other
    # view covers. Reported, never scored (see zone_conflict_flags).
    zconf = zone_conflict_flags(cards, carddata)
    if zconf:
        print(f"\n⛔ Fights your own engine ({len(zconf)}) — grade from full text "
              f"(`deck.py cuts {d['id']}`):")
        for nm, _scope, why, hit in zconf:
            print(f"    {nm}: {why}")
            print(f"      needs it populated: {', '.join(hit[:4])}"
                  + (f" … (+{len(hit) - 4})" if len(hit) > 4 else ""))
    return 0


def _tribe_ref_re(t):
    """Compiled pattern matching a creature TYPE reference in oracle text — singular
    OR plural. Lords overwhelmingly template plural ("Ninjas you control get +1/+1",
    "Elves you control"), and the old `\\b<type>\\b` scan could not see a plural (no
    word boundary before the 's'), so the payoff list under-reported exactly the
    count G-59 says decides tribal viability (broad-scan BS-11). English plurals as
    Magic templates them: -y → -ies (Mercenaries), -f → -ves (Elves, Dwarves,
    Wolves), sibilants → -es (Foxes, Sphinxes), else +s; a couple of irregulars."""
    forms = [re.escape(t)]
    irregular = {"Mouse": "Mice", "Ox": "Oxen"}
    if t in irregular:
        forms.append(irregular[t])
    elif t.endswith("y"):
        forms.append(re.escape(t[:-1] + "ies"))
    elif t.endswith("f"):
        forms.append(re.escape(t[:-1] + "ves"))
    elif t.endswith(("s", "x", "z", "ch", "sh")):
        forms.append(re.escape(t + "es"))
    else:
        forms.append(re.escape(t + "s"))
    return re.compile(rf"\b(?:{'|'.join(forms)})\b")


def cmd_tribes(args):
    """Creature-subtype breakdown + type-matters synergy scan."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}.")
        return 1
    _, cards = parse_deck_file(d["path"])
    data = load_card_data()

    subcount = {}
    subs_by_card = {}   # name -> set(subtypes)
    for q, n, s, c in cards:
        d2 = data.get(n.lower())
        if not d2:
            continue
        subs = creature_subtypes(d2["type"])
        if subs:
            subs_by_card[n] = set(subs)
            for st in subs:
                subcount[st] = subcount.get(st, 0) + q

    print(f"Deck {d['id']}: {d['name'] or d['path']} — creature types & synergies\n")
    print("Creature subtypes:")
    for st, cnt in sorted(subcount.items(), key=lambda kv: -kv[1]):
        print(f"  {st:14} {cnt:3}  {'#' * cnt}")

    deck_types = {st for subs in subs_by_card.values() for st in subs}
    changelings = {n for q, n, s, c in cards
                   if re.search(r"\bchangeling\b|is every creature type",
                                (data.get(n.lower()) or {}).get("text") or "", re.I)}
    payoffs = []
    seen_p = set()
    for q, n, s, c in cards:
        if n in seen_p:
            continue
        d2 = data.get(n.lower())
        if not d2 or not d2["text"]:
            continue
        # A type named only inside a "create … token" clause is a BODY the card makes,
        # not a type it rewards (BS8-33 — 320 of 902 roster payoff rows were this: "The
        # Earth King rewards Bear" on "create a 4/4 Bear token"). The reference has to
        # occur outside every token-creation clause. Changelings qualify for every type a
        # payoff names (they ARE every creature type — G-59), and the payoff card itself
        # is not one of its own qualifiers.
        _txt = _REMINDER_RE.sub(" ", d2["text"])
        _clauses = [c for c in re.split(r"[.\n]", _txt) if c.strip()]
        refs = {t for t in deck_types
                if any(_tribe_ref_re(t).search(c) and not re.search(
                       r"\bcreates?\b[^.]*\btokens?\b", c, re.I) for c in _clauses)}
        if refs:
            qual = sum(q2 for q2, n2, s2, c2 in cards
                       if n2 != n and (subs_by_card.get(n2, set()) & refs
                                       or n2 in changelings))
            seen_p.add(n)
            payoffs.append((qual, n, sorted(refs)))
    if payoffs:
        print("\nType-matters payoffs (cards whose text rewards types you run):")
        for qual, n, refs in sorted(payoffs, reverse=True):
            print(f"  {n} — rewards {', '.join(refs)}  ({qual} qualifying creatures)")
    return 0


# --- deck suggestions from the pool ----------------------------------------- #
@_file_memo("DEFAULT_CSV", "POOL_CSV")
def load_card_meta():
    """name_lower -> {'colors': set(WUBRG), 'synergies': [tags]} from library then
    pool. Color(s) is color IDENTITY, which is exactly what we want for deck fit
    (a card is playable in a deck whose identity covers it)."""
    meta = {}
    for path in (DEFAULT_CSV, POOL_CSV):
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                nl = (r.get("Card Name") or "").strip().lower()
                if not nl or nl in meta:
                    continue
                cols = card_colors(r.get("Color(s)"))
                tags = [t.strip() for t in (r.get("Synergies") or "").split(";") if t.strip()]
                meta[nl] = {"colors": cols, "synergies": tags}
    # SECOND pass, per lib.alias_front's contract (BS2-40): this was the last loader
    # still aliasing IN-pass, and its `nl in meta: continue` made the order-dependence
    # into row LOSS — a real card named like an earlier DFC's front hit the alias and
    # was dropped entirely, inheriting the DFC's colors and tags in suggest /
    # suggest-homes / fingerprints / cut context (the documented "Life // Death"
    # shadowing trap, latent at 0 collisions today). Registered in check_dfc's
    # _ALIASED_LOADERS so the gate can see it.
    return alias_front(meta)


# High-confidence, high-precision mechanical SUB-themes (the tag-synergy payoffs added
# for the tagging-misreads fix): a card carrying one is a deliberate build piece even at a
# small count. They sit BELOW the 25% relative centrality cutoff in a deck with a dominant
# theme, so a secondary payoff (Bark of Doran in a toughness-swap deck, Hawkeye in a ping
# deck) never surfaced — `_central_themes` admits them at a flat floor of 2 instead. Kept
# small + specific so they can't fake a generic overlap into a home (unlike the broad
# GENERIC_THEMES, which STAY gated behind the 25% cutoff).
_MECHANIC_SUBTHEMES = {"toughness matters", "noncombat damage", "spell copy"}


def _central_themes(theme_w, frac=0.25):
    """The themes that are actually CENTRAL to a deck: those carried by at least a
    quarter of the deck's most-common theme's copies (floor of 2 copies). Filters
    out one-off tag overlaps so a generic sac/tokens card doesn't read as fitting a
    deck it only grazes. Curated high-precision mechanical sub-themes
    (`_MECHANIC_SUBTHEMES`) are also admitted at a flat floor of 2, so a real 2-card
    payoff sub-synergy reads central even under a heavier dominant theme (the
    specific-effect analog of the `#: protect:` signature rescue)."""
    if not theme_w:
        return set()
    cutoff = max(2, frac * max(theme_w.values()))
    return {t for t, w in theme_w.items()
            if w >= cutoff or (t in _MECHANIC_SUBTHEMES and w >= 2)}


# Themes carried by nearly every deck — low signal for how KEY a fit is (mirrors
# wishlist.NON_SIGNAL_TAGS's intent, kept local so deck.py has no wishlist import).
# Covers the broad "matters" generics (etb/tokens/counters/…), generic card-quality
# themes (selection/value — most decks scry/dig), AND the evergreen combat keywords
# (a card sharing only "flying" or "ward" with a deck is not a synergy fit). Keeping
# these out of the "specific" set is what stops a generically-good removal or card-
# advantage card reading KEY in every deck it merely shares an incidental tag with.
GENERIC_THEMES = {
    "etb", "tokens", "counters", "lifegain", "sacrifice", "card draw", "graveyard",
    "mana", "ramp", "combat", "aggro", "tempo", "pump", "removal", "evasion",
    "flying", "trample", "menace", "deathtouch", "lifelink", "vigilance",
    "selection", "value", "first strike", "double strike", "haste", "reach",
    "prowess", "ward", "hexproof", "indestructible", "protection", "defense",
    "defender", "resilience", "shroud", "fear", "intimidate",
}
# Creature tribes so broad they carry no HOME signal — nearly every creature in a
# superhero/anime multiverse is a Human and a Hero or Villain, so sharing one is not a
# synergy. Treated as generic by `fit_strength` (the tribal analog of GENERIC_THEMES) so a
# card doesn't read KEY in a deck merely for sharing a background tribe (the Hawkeye-"KEY"-
# in-every-Hero/Human-deck over-assignment). Narrow, build-around tribes (Ninja, Cat,
# Dinosaur, Knight, Wizard, Merfolk, …) are deliberately NOT here — those ARE real
# signature themes. A genuine broad-tribe payoff (a "Heroes you control get +1/+1" lord)
# can still read KEY via the deck's `#: protect:` signature; this only stops a BARE shared
# tribe from carrying a home by itself. Kept separate from GENERIC_THEMES so other
# consumers (which compare Title-case) are unaffected — fit_strength lowercases.
_GENERIC_TRIBES = {"human", "hero", "villain"}


def role_tally(cards, carddata):
    """The CANONICAL per-deck functional-role tally — the single source every view
    (stats, audit, quality/tier) routes through so their interaction / card-advantage
    numbers can't drift apart (they used to: three separate counters disagreed by ±1,
    which is exactly the kind of gap that could move a tier band the user couldn't
    reproduce in `stats`). Rules, fixed once here:
      • quantity-weighted (2 copies of a removal spell = 2 interaction),
      • a card counts ONCE toward 'interaction' regardless of how many interaction
        roles it fills (a modal removal+counter card is one interaction card, not
        two — the per-role buckets still credit each role for the stats display),
      • basics and nonbasic lands are skipped.
    Returns a dict: each role → weighted count, plus 'interaction' (once-per-card
    union of Removal/Sweeper/Counter), 'card_advantage', and 'protection' (real
    ward/hexproof/indestructible-class effects — see `protection_effects`)."""
    per_role = {}
    interaction = ca = prot = 0
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        cd = carddata.get(n.lower())
        if not cd or "Land" in _primary_type(cd["type"]):
            continue
        roles = set(classify_roles(cd["text"]))
        for r in roles:
            per_role[r] = per_role.get(r, 0) + q
        if roles & _INTERACTION_ROLES:
            interaction += q
        if "Card advantage" in roles:
            ca += q
        if protection_effects(cd["text"]):
            prot += q
    per_role["interaction"] = interaction
    per_role["card_advantage"] = ca
    per_role["protection"] = prot
    # CONFIDENCE, carried WITH the count. The classifier reports a false negative as a
    # fact: a card it can't parse contributes 0, and `0` reads as "none" rather than
    # "not detected". That is the single most damaging failure this toolkit has had — a
    # deck graded on interaction 3 when a hand count said 7, because three cards that
    # unambiguously interact scored zero roles. `role_coverage_flags` already computed
    # this, but printed it as a separate warning several lines away, so the NUMBER still
    # read as fact. Attaching the remainder to the tally means every consumer gets it.
    unclassified, under_read, no_data = role_coverage_flags(cards, carddata)
    # Quantity-weight the uncertainty the SAME way the counts themselves are weighted.
    # `interaction`/`card_advantage`/`protection` above are quantity-weighted (2 copies of
    # a removal spell = 2), but these remainders were CARD counts — so `8 +4?` compared a
    # weighted base against an unweighted remainder, and a deck running 4x of a card with
    # no oracle text on file reported "+1?" when four copies were unread (broad-scan
    # F-09). Understating uncertainty is the wrong direction for a signal whose entire
    # job is to stop a heuristic count from reading as fact.
    #
    # Dedupe by name first: role_coverage_flags emits one entry per LINE, so a card split
    # across two printing lines would otherwise be weighted by its full quantity twice.
    # (No deck on the roster does that today; the guard is for when one does.)
    _qty_of = {}
    for _q, _n, _s, _c in cards:
        _qty_of[(_n or "").lower()] = _qty_of.get((_n or "").lower(), 0) + _q
    def _weigh(names):
        return sum(_qty_of.get((n or "").lower(), 1) for n in dict.fromkeys(names))
    per_role["interaction_unread"] = _weigh([n for n, ax in under_read if "interaction" in ax])
    per_role["card_advantage_unread"] = _weigh([n for n, ax in under_read if "card advantage" in ax])
    # `unclassified` is the WORSE case and must not be invisible: a noncreature spell that
    # matched no role AND tripped no broad cue. That is exactly Broken Wings and Repulsive
    # Mutation — cards that unambiguously interact and scored zero. It can't be attributed
    # to a single axis, so it is reported globally rather than folded into one count.
    per_role["unclassified"] = _weigh(unclassified)
    per_role["unreadable"] = _weigh(no_data)
    return per_role


def count_conf(tally, key):
    """A measured count rendered with its uncertainty: `7`, or `3 +2?` when 2 more cards
    read like that role but the classifier couldn't tag them. Use this ANYWHERE a role
    count is shown to a human — a bare number invites exactly the over-trust that a
    heuristic classifier doesn't deserve."""
    n = tally.get(key, 0)
    unread = tally.get(f"{key}_unread", 0)
    unclass = tally.get("unclassified", 0)
    bad = tally.get("unreadable", 0)
    out = str(n)
    if unread:
        out += f" +{unread}?"
    notes = []
    if unclass:
        notes.append(f"{unclass} unclassified")
    if bad:
        notes.append(f"{bad} unreadable")
    if notes:
        out += f" ({', '.join(notes)})"
    return out


# Text cues that an interaction spell can hit a NONCREATURE permanent (planeswalker /
# enchantment / artifact) or any target — the "reach past creatures" test for #5.
_NONCREATURE_ANSWER_CUES = [re.compile(p) for p in [
    r"destroy target permanent", r"exile target permanent", r"return target permanent",
    r"destroy target (artifact|enchantment)", r"destroy target artifact or enchantment",
    r"exile target (artifact|enchantment)", r"target permanent you don't control",
    r"destroy target[^.]*planeswalker", r"destroy target[^.]*or planeswalker",
    r"exile target[^.]*planeswalker", r"destroy all permanents", r"destroy each",
    r"any target",  # burn to any target answers a planeswalker (and the opponent)
    r"deals? \d+ damage to any target", r"destroy target nonland permanent",
    # The planeswalker rows above allow ANY text between "target" and the type
    # (`[^.]*`, sentence-bounded); the artifact/enchantment rows required the type to
    # follow "target" IMMEDIATELY. So "destroy target creature or PLANESWALKER" counted
    # and "destroy target creature or ENCHANTMENT" did not — the same list, templated
    # the other way round. Measured misses when this was found: Withering Torment and
    # Feed the Swarm, i.e. the only two enchantment answers on the whole roster.
    r"destroy target[^.]*\b(artifact|enchantment)", r"exile target[^.]*\b(artifact|enchantment)",
    # Split template — see the Removal (spot) note on Quag Feast. "Choose target
    # creature, planeswalker, or Vehicle … destroy the chosen permanent" reaches past
    # creatures, but names the types a sentence away from the verb.
    r"choose target[^.]*\b(planeswalker|artifact|enchantment|vehicle|spacecraft|permanent)",
]]


def interaction_profile(cards, carddata):
    """Qualitative interaction breakdown (#5): beyond the raw count, how much of a deck's
    interaction is INSTANT-speed vs sorcery-speed, and how much can answer a NONCREATURE
    permanent (planeswalker / enchantment / artifact) — so 'thin against planeswalkers /
    all sorcery-speed' is measured, not eyeballed. Quantity-weighted, once per card.

    Returns {total, instant, sorcery, noncreature, flags:[…]}. Heuristic: instant-speed =
    an Instant, a card with Flash, or a Counter (counters resolve at instant speed);
    noncreature-answer = a Counter (answers any spell) or a removal cue that reaches past
    creatures."""
    total = instant = sorcery = noncreature = 0
    # Quantity-weighted per card, summed ACROSS lines: a card split over two lines
    # (e.g. two printings) must count its full quantity, matching the canonical
    # role_tally — a `seen`-set + first-line q under-counted it (audit A11).
    qty_by_name = {}
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS:
            continue
        qty_by_name[nl] = qty_by_name.get(nl, 0) + q
    for nl, q in qty_by_name.items():
        cd = carddata.get(nl)
        if not cd:
            continue
        # Same nonbasic-LAND filter the canonical `role_tally` applies — this profile
        # skipped it, so 13 decks printed two contradicting interaction figures eleven
        # lines apart in one `stats` run (29a: total 13 vs profile 14, the extra being
        # the land Abraded Bluffs), and the all-sorcery / no-noncreature-answer flags
        # fired off the inflated total (broad-scan BS2-18; K-12's one-canonical-counter
        # contract).
        if "Land" in _primary_type(cd.get("type") or ""):
            continue
        text = cd.get("text") or ""
        roles = classify_roles(text)
        if not (roles & _INTERACTION_ROLES):
            continue
        total += q
        tl = (cd.get("type") or "").lower()
        tx = text.lower()
        is_counter = "Counter" in roles
        # `\bflash\b` matches the Flash keyword but NOT "flashback" — a sorcery-speed
        # flashback recast is not instant-speed interaction (audit A7).
        if "instant" in tl or re.search(r"\bflash\b", tx) or is_counter:
            instant += q
        else:
            sorcery += q
        if is_counter or any(p.search(tx) for p in _NONCREATURE_ANSWER_CUES):
            noncreature += q
    flags = []
    if total >= 3 and instant == 0:
        flags.append("all sorcery-speed — no instant-speed answers (you can't react)")
    if total >= 3 and noncreature == 0:
        flags.append("no answer to a noncreature permanent (planeswalkers / enchantments / "
                     "artifacts slip through)")
    return {"total": total, "instant": instant, "sorcery": sorcery,
            "noncreature": noncreature, "flags": flags}


def deck_role_counts(cards, carddata):
    """(interaction, card_advantage) for a deck, from the canonical `role_tally` —
    used to tell whether a candidate card FILLS A GAP (interaction / card advantage
    the deck is short on), which makes an otherwise-secondary fit a KEY one."""
    t = role_tally(cards, carddata)
    return t["interaction"], t["card_advantage"]


def fit_strength(shared, theme_w, card_text, deck_int, deck_ca, signature=frozenset()):
    """Classify a card→deck fit as KEY / role-player / tangential (F04).

      KEY          – shares the deck's SIGNATURE theme (top central theme, OR a theme
                     carried by the deck's `#: protect:` cards), OR shares a SPECIFIC
                     (non-generic) theme AND fills a role the deck is short on
                     (interaction < 5 / card advantage < 3), OR shares the deck's most-
                     common specific theme.
      role-player  – shares a specific central theme, but not the signature.
      tangential   – shares only GENERIC themes (etb/tokens/…) or broad background tribes
                     (_GENERIC_TRIBES: Human/Hero/Villain): broadly playable, not a home.

    `signature` corrects the idf blind spot: a theme in GENERIC_THEMES is still
    SPECIFIC-for-this-deck if the deck protects cards built on it — so a counter-doubler
    in a counters deck reads KEY, not tangential. Callers must pass the STRICT
    `_strong_signature_themes` (a theme carried by >=2 `#: protect:` cards), NOT the
    loose `_signature_themes` that unions every protected card's tags. With the loose
    set, deck 37's signature held 25 themes including etb / removal / sacrifice /
    combat / tempo, so almost any card sharing any of them read KEY — Azula, Cunning
    Usurper (a Human Noble Rogue) read KEY for three WIZARD-tribal decks on `Human, etb`
    alone. `similar` already used the strict set for exactly this reason. The motivating
    rescue is unaffected: deck 30's strict signature is precisely {counters}.

    The role-gap KEY is gated on a SPECIFIC-theme match (checked AFTER the `not
    specific` short-circuit below): a generically-good removal / card-advantage card
    would otherwise read KEY in every low-interaction deck it merely shares an
    etb/tokens tag with (the Get-Lost-"KEY"-in-15-decks over-assignment). Its broad
    utility is real, but it belongs to the cross-deck BREADTH signal (wishlist `use`
    column), not a specific home — so a fit resting only on generic themes stays
    tangential even when the deck happens to be short on that role.
    """
    specific = [t for t in shared
                if (t.lower() not in GENERIC_THEMES or t in signature)
                and t.lower() not in _GENERIC_TRIBES]
    # A signature-theme match is a genuine home (the deck's spine) — but a broad
    # background tribe (Human/Hero/Villain) is NOT a signature even when a protected card
    # happens to carry it, so it can't mint a KEY by itself (tagging-misreads #4).
    if signature and any(t in signature and t.lower() not in _GENERIC_TRIBES
                         for t in shared):
        return "KEY"
    # No SPECIFIC shared theme -> at most GENERICALLY playable here, not a synergy home.
    # Checked BEFORE the role-gap branch on purpose (see docstring).
    if not specific:
        return "tangential"
    roles = set(classify_roles(card_text or ""))
    gap = (bool(roles & _INTERACTION_ROLES) and deck_int < 5) or \
          ("Card advantage" in roles and deck_ca < 3)
    if gap:                       # on a specific theme AND fills a role the deck lacks
        return "KEY"
    top = max(theme_w.values()) if theme_w else 0
    if top and any(theme_w.get(t, 0) >= top for t in specific):
        return "KEY"
    return "role-player"


def cross_deck_breadth(card_colors, card_themes, fps, cost=""):
    """How many decks a card is BOTH castable in AND shares ≥1 SPECIFIC theme with —
    the single definition of "cross-deck breadth" in this toolkit.

    `fps` is [(deck_id, castable_colors:set, specific_themes:set), …]. Callers supply
    their own per-deck specific-theme set, because the two ranking models legitimately
    decide "specific" differently and that difference is deliberate:
      • `deck.suggest_scored` uses the GENERIC_THEMES/_GENERIC_TRIBES denylist plus the
        `#: protect:` signature rescue (`_sim_specific`), the same test `similar` uses;
      • `wishlist._rank_scores` uses the idf threshold (`spec_idf`) + NON_SIGNAL_TAGS,
        which self-calibrates to the deck count.
    What must NOT differ is the COUNTING RULE, and it used to: two hand-written copies
    drifted until one required a specific theme and the other accepted any central one,
    so `suggest`'s column saturated at 99% while the wishlist's stayed meaningful
    (broad-scan F-04). Routing both through here makes that impossible; `check_suggest`
    anchor 13 asserts the two agree on a synthetic card."""
    # Castability by PRINTED COST when one is given (BS8-14): identity subset read
    # Bullseye, Death Dealer (`{2}{B/R}`) as fitting 13 decks against 34 by cost, so the
    # "value per wildcard" column under-read every hybrid by ~2.5×. Identity stays the
    # fallback for a card with no cost on file (`_filler_castable`, G-58).
    return sum(1 for _id, dcols, dthemes in fps
               if _filler_castable(cost, card_colors, dcols) and (card_themes & dthemes))


def _deck_fingerprints(meta, exclude_id=None):
    """[(id, colors:set, specific_central_themes:set), ...] for every deck — used to
    score a craft target's cross-deck reuse (a card that fits several of your decks is
    worth more per wildcard). Colors are the deck's declared `#: colors:` (else the
    union of its cards' identities).

    Themes are the deck's central synergy tags NARROWED TO THE SPECIFIC ones — the
    same `_sim_specific` test `similar` uses, so a GENERIC theme (etb / tokens /
    counters / lifegain …) or a broad background tribe can't carry a home, while a
    generic theme that IS this deck's `#: protect:` spine still counts. Centrality
    alone was not enough: nearly every deck is central on the same handful of generic
    themes, so the reuse count saturated — 99% of a deck's picks scored >=3 and the
    median pick "fit" 31 of 56 other decks, which made the ★ high-reuse callout and
    the per-wildcard signal it feeds carry no information at all (audit F-04). This is
    the gate `wishlist._rank_scores` already applies to its own breadth column; the
    two now measure the same thing.

    VARIANTS ARE COLLAPSED to their core deck. A variant is an alternate build of the
    same archetype, so counting 19, 19b and 19c as three homes triple-counts one deck's
    worth of value — the second inflation source in this signal, and the same reasoning
    `wishlist._theme_model` documents for its own idf/breadth model. Excluding a deck by
    `exclude_id` therefore excludes its whole family, so analyzing 19b can't count 19.

    `exclude_id` drops one deck from the roster (the deck being analyzed), so a
    suggestion's reuse count is 'how many OTHER decks it fits' — otherwise the
    current deck always counts itself and inflates every score by one."""
    fps = []
    skip_core = None
    if exclude_id is not None:
        skip_core = next((d["core"] for d in roster_decks()
                          if d["id"].lower() == exclude_id.lower()), None)
    for dd in roster_decks():
        if dd["variant"]:
            continue                      # an alternate build of a core already counted
        if exclude_id is not None and (dd["id"].lower() == exclude_id.lower()
                                       or (skip_core is not None and dd["core"] == skip_core)):
            continue
        dm, cards = parse_deck_file(dd["path"])
        colors, ident, theme_w = _declared_colors(dm), set(), {}
        for q, n, s, c in cards:
            if n.lower() in BASICS:
                continue
            m = meta.get(n.lower())
            if not m:
                continue
            ident |= m["colors"]
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
        # A generic theme is rescued only when it's a real BUILD-AROUND spine (carried
        # by >=2 `#: protect:` cards) — the stricter signature test, so a lone protected
        # bomb's incidental etb/card-draw tag can't re-open the saturation it closes.
        sig = _strong_signature_themes(dm, cards, meta)
        specific = {t for t in _central_themes(theme_w) if _sim_specific(t, sig)}
        fps.append((dd["id"], colors or ident, specific))
    return fps


POOL_BUILD_STAMP = os.path.join(REPO_ROOT, "card-pool.build")


def pool_staleness_days():
    """Days since card-pool.csv was built (from the card-pool.build sidecar), or
    None if unstamped. Standard rotates on a schedule, so an old pool can still
    mark a rotated-out card as `standard` — this lets `suggest` warn and prompt a
    rebuild. Dormant until a `build_pool.py` run writes the stamp."""
    if not os.path.exists(POOL_BUILD_STAMP):
        return None
    try:
        import datetime
        built = datetime.date.fromisoformat(open(POOL_BUILD_STAMP).read().strip()[:10])
        return (datetime.date.today() - built).days
    except Exception:
        return None


# Sets whose Standard legality does NOT follow the release-date + 3 years rule, keyed
# by Arena set code → the year they actually leave Standard.
#
# FOUNDATIONS is the case that matters: it is deliberately Standard-legal for FIVE years
# (through 2029), not three. Because the pool keys ONE printing per card, a card whose
# newest printing is in FDN inherits FDN's 2024 release date and read "⚠rot~2027" — so
# Genesis Wave, legal for another four years, was flagged as "don't spend a wildcard on
# a card about to leave the format." CLAUDE.md documented the reprint caveat in prose;
# this encodes it. Add a row here whenever a set gets an announced non-standard window.
_SET_ROTATION_OVERRIDE = {
    "FDN": 2029,   # Foundations — announced Standard-legal through 2029
}


# Standard rotates ONCE a year, with the fall set, and a set leaves with the "Standard
# year" it was released into — the fall set and everything released before the NEXT
# fall set go together. `release year + 3` got every spring set wrong by a year
# (BS8-13): MKM/OTJ/BIG (Feb–Apr 2024) rotate in 2026 with WOE/LCI, and DFT/TDM/FIN
# (Feb–Jun 2025) in 2027 with BLB/DSK, while the heuristic said 2027 and 2028. Checked
# against the announced schedule for every set from DMU (2022) to TLA (2025): a set
# released in August or later belongs to that year's Standard year, one released
# January–July to the previous year's. `_SET_ROTATION_OVERRIDE` still wins for an
# announced exception (Foundations).
_STANDARD_YEAR_STARTS_MONTH = 8


def rotation_year(released, years=3, set_code=""):
    """The year a set rotates out of Standard — the STANDARD YEAR it was released into
    (its release year, or the year before for a January–July release) + `years`, or an
    announced date from `_SET_ROTATION_OVERRIDE`. None if the date is blank or
    unparseable. The single primitive behind `rotation_sweep`, the wishlist ⚠rot flag
    and `rotation_risk`, so 'when does this rotate' is computed one way everywhere."""
    override = _SET_ROTATION_OVERRIDE.get((set_code or "").strip().upper())
    if override:
        return override
    try:
        year = int((released or "")[:4])
        month = int((released or "")[5:7]) if len(released or "") >= 7 else _STANDARD_YEAR_STARTS_MONTH
    except (ValueError, TypeError):
        return None
    standard_year = year if month >= _STANDARD_YEAR_STARTS_MONTH else year - 1
    return standard_year + years


def rotation_risk(released, years=3, set_code="", legal=None):
    """True if a card is past ~`years` of Standard life — so a still-`standard`-marked
    pick may have rotated (stale pool) or rotates THIS YEAR OR NEXT. Routed through
    `rotation_year` so an announced long-legality set (Foundations) can't be
    false-flagged. Empty or unparseable `released` → False (graceful before a pool
    rebuild captures the column).

    The window is `year + 1`, matching `craft_rot_note` and `wishlist`'s ⚠rot. It read
    `<= year` until 2026-08-28, one year STRICTER than every other craft surface, while
    `craft_rot_note`'s docstring asserted the two "cannot disagree" — a claim about
    agreement is not agreement. `cmd_suggest` was the sole remaining caller, so the
    format's whole craft recommender under-flagged by a year: a deck-44a tune was
    offered Valgavoth (DSK, rotates ~2027) with no ⚠rot in the same session that
    `check` warned about OTJ/BLB/MKM cards rotating in that same wave. Measured at the
    fix: Standard-legal pool flag rate 11% → 34%, which is simply the share of Standard
    that rotates within ~15 months and is the rate the other four surfaces already
    showed (G-30)."""
    import datetime
    if legal is not None and "standard" not in legal:
        return False          # not in Standard — nothing to rotate out of (BS8-12)
    yr = rotation_year(released, years, set_code)
    return bool(yr) and yr <= datetime.date.today().year + 1


def unreleased_pool_cards(pool_path=None):
    """[(name, set_code, released)] for pool rows whose set has NOT been released yet.

    The 2026-08-24 Ingest audit found `Released` was read in exactly ONE direction —
    `rotation_risk` and the ⚠rot flags, which answer "when does this LEAVE Standard".
    Nothing anywhere asked "is this available YET", so 114 pool rows dated in the future
    were fully recommendable: `suggest` (and its --lands/--ramp/--interaction siblings),
    `tier --to`'s craft fillers and `wishlist --rank/--budget` would all price a wildcard
    for a card that cannot be crafted.

    `build_pool`'s `date<=now` bound (A1) keeps them out at the source, so this is the
    backstop for the two cases that bound cannot cover: a pool built with a custom
    `--query`, and a pool built before that bound existed. Deliberately a POOL-level
    check rather than a flag threaded through five recommenders — the exposure is a
    property of the file, so one report covers every surface at once and, being
    report-only, it re-ranks nothing (no K-12 roster diff needed).

    Empty/unparseable dates are skipped, like `rotation_risk` — graceful before a rebuild
    captures the column."""
    import datetime
    path = pool_path or POOL_CSV
    today = datetime.date.today().isoformat()
    out = []
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            rdr = csv.DictReader(fh)
            if "Released" not in (rdr.fieldnames or []):
                return []
            for r in rdr:
                rel = (r.get("Released") or "").strip()
                if len(rel) == 10 and rel > today:
                    out.append(((r.get("Card Name") or "").strip(),
                                (r.get("Set Code") or "").strip(), rel))
    except OSError:
        return []
    return out


def craft_rot_note(name, pool_rot):
    """'⚠rot~YYYY' if `name`'s pool printing is Standard-legal but its set rotates
    this year or next, else ''. The CRAFT-TARGET views (`check`, `wildcards`) join
    through this so a card is flagged at the exact moment a wildcard decision is
    made: deck 28's craft plan held FOUR cards rotating within months and nothing on
    the craft path said so — `wishlist --rank` had the flag, but a deck line that
    never reached the wishlist bypassed it entirely. Same `rotation_year` primitive
    and same this-year-or-next window as the wishlist's ⚠rot, so the two surfaces
    cannot disagree. Degrades to '' with no pool / no Released column, like
    `rotation_risk`."""
    info = pool_rot.get((name or "").strip().lower())
    if not info:
        return ""
    released, legal, set_code = info
    # ONE predicate (BS8-12): this used to re-implement the window beside
    # `rotation_risk`, and the two disagreed on SCOPE — `suggest` flagged owned rows
    # and Brawl decks — while a docstring said they "cannot disagree".
    if not rotation_risk(released, set_code=set_code, legal=legal):
        return ""
    return f"  ⚠rot~{rotation_year(released, set_code=set_code)}"


def _pool_rotation_index():
    """name_lower (full AND DFC front) -> (released, {legalities}, set_code) from the pool.
    Returns (index, has_released). `has_released` is False for a pool built before the
    Released column existed — callers then warn instead of silently reporting nothing."""
    idx, has_released = {}, False
    if not os.path.exists(POOL_CSV):
        return idx, has_released
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        has_released = "Released" in (rdr.fieldnames or [])
        for r in rdr:
            nl = (r.get("Card Name") or "").strip().lower()
            if not nl:
                continue
            info = ((r.get("Released") or "").strip(),
                    {x.strip().lower() for x in (r.get("Legalities") or "").split(";") if x.strip()},
                    (r.get("Set Code") or "").strip())
            idx.setdefault(nl, info)
    return alias_front(idx), has_released


def rotation_sweep(fmt="standard", years=3, within=2):
    """Roster-wide rotation exposure for `fmt` (default Standard): which cards each deck
    runs are CLOSEST to rotating, so you can see what rotates NEXT and which decks it
    hits. A card's rotation year is its set's release year + `years` (Standard's ~3-year
    window); a card is surfaced when that year is within `within` years of now — i.e. it
    rotates this year, soon, or is already past-due (a stale-pool signal). Reads the
    pool's Released/Legalities snapshot (the same data `suggest`'s ⚠rot flag uses). Note:
    gating on release-age here (rather than `rotation_risk`'s strict >years boolean) is
    deliberate — on a freshly-built pool every still-legal card is BY DEFINITION inside
    the window, so the >years test would report nothing; the point is what rotates *next*.
    Offline.

    Returns (decks, rollup, meta):
      decks  = [{id, name, atrisk:[{name,set,rotates,qty}], n_slots}] for `fmt` decks,
               most-exposed first (each at-risk list sorted soonest-rotating first).
      rollup = {rotates_year: {'slots':n, 'cards':set, 'decks':set}} (a card counted per
               deck it appears in — "deck-slots" — since the point is roster exposure).
      meta   = {has_released, stale_days, unverified, n_decks, this_year, within}.

    Caveat: the pool keys one representative printing per card, so a card reprinted into a
    newer Standard set may carry an OLDER printing's Released — its rotation year can read
    earlier than reality. Verify against the official schedule before disenchanting.
    """
    import datetime
    this_year = datetime.date.today().year
    pool, has_released = _pool_rotation_index()
    fmt = (fmt or "").strip().lower()
    decks_out, rollup, unverified = [], {}, 0
    for d in roster_decks():
        dm, cards = parse_deck_file(d["path"])
        if fmt and (dm.get("format") or "").strip().lower() != fmt:
            continue
        atrisk = []
        for q, n, s, c in cards:
            nl = n.lower()
            if nl in BASICS:
                continue
            info = pool.get(nl) or pool.get(nl.split(" // ")[0])
            if not info:
                unverified += 1
                continue
            released, legals, setc = info
            if fmt and legals and fmt not in legals:
                continue  # not legal in this format anyway — it can't "rotate out" of it
            rotates = rotation_year(released, years, setc)
            if rotates is None:
                continue  # no usable release date — can't place it on the timeline
            if rotates > this_year + within:
                continue  # not rotating within the horizon
            atrisk.append({"name": n, "set": setc or s, "rotates": rotates, "qty": q})
            rr = rollup.setdefault(rotates, {"slots": 0, "cards": set(), "decks": set()})
            rr["slots"] += 1
            rr["cards"].add(n)
            rr["decks"].add(d["id"])
        atrisk.sort(key=lambda x: (x["rotates"], x["name"]))
        decks_out.append({"id": d["id"], "name": d["name"] or d["id"],
                          "atrisk": atrisk, "n_slots": len(atrisk)})
    decks_out.sort(key=lambda x: (-x["n_slots"], x["id"]))
    meta = {"has_released": has_released, "stale_days": pool_staleness_days(),
            "unverified": unverified, "n_decks": len(decks_out),
            "this_year": this_year, "within": within}
    return decks_out, rollup, meta


def _brawl_commanders(cards, carddata):
    """[(name, identity_set)] for each legendary creature/planeswalker in the deck —
    the candidate commanders. Deduped, basics/non-carddata skipped."""
    out, seen = [], set()
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in seen or nl in BASICS:
            continue
        seen.add(nl)
        cd = carddata.get(nl) or carddata.get(nl.split(" // ")[0])
        if not cd:
            continue
        t = cd.get("type", "") or ""
        if "Legendary" in t and ("Creature" in t or "Planeswalker" in t):
            out.append((n, card_colors(cd.get("colors", ""))))
    return out


def brawl_readiness(fmt_filter="standard"):
    """Roster-wide 'distance to a legal Brawl conversion' per deck (#2). For each deck in
    `fmt_filter`, pick the best in-deck commander (the legendary creature/PW whose color
    identity leaves the FEWEST cards stray), then measure how far the deck is from a legal
    Brawl build: cards to de-duplicate to singleton + cards outside that commander's
    identity + any Brawl-illegal cards. Reuses the same identity/commander rules
    `deck.py legal` enforces, so the estimate can't drift from the actual check. Offline.

    Returns rows sorted closest-first: [{id, name, colors, commander, cmd_ident, dup,
    stray, notlegal, distance, no_commander, converted}], plus a `converted` flag when a
    `<core>-brawl` variant already exists."""
    carddata = load_card_data()
    leg = load_legalities()
    # cores that already have a Brawl variant (so we can mark them done)
    converted = {d["core"] for d in roster_decks()
                 if str(d["id"]).endswith("-brawl")}
    fmt_filter = (fmt_filter or "").strip().lower()
    rows = []
    for d in roster_decks():
        meta, cards = parse_deck_file(d["path"])
        if fmt_filter and (meta.get("format") or "").strip().lower() != fmt_filter:
            continue
        declared = _declared_colors(meta)
        tot, disp = {}, {}
        for q, n, s, c in cards:
            nl = n.lower()
            if nl in BASICS:
                continue
            tot[nl] = tot.get(nl, 0) + q
            disp.setdefault(nl, n)
        dup = sum(1 for nl, q in tot.items() if q > 1)
        notlegal = sum(1 for nl in tot
                       if leg.get(nl) is not None
                       and pool_format_key("brawl") not in leg[nl])
        idents = {nl: card_colors((carddata.get(nl) or carddata.get(nl.split(" // ")[0])
                                   or {}).get("colors", "")) for nl in tot}

        best = None  # (name, ident, strays)
        for name, ident in _brawl_commanders(cards, carddata):
            strays = sum(1 for nl, ci in idents.items() if not ci <= ident)
            # Prefer fewest strays; tiebreak an exact deck-color match, then broader ident.
            key = (strays, ident != declared, -len(ident), name)
            if best is None or key < best[0]:
                best = (key, name, ident, strays)
        no_commander = best is None
        stray = best[3] if best else len(tot)
        distance = dup + stray  # card-swaps to reach a legal Brawl 60 (basics refill)
        rows.append({
            "id": d["id"], "name": d["name"] or d["id"],
            "colors": (meta.get("colors") or "").strip().upper(),
            "commander": best[1] if best else None,
            "cmd_ident": "".join(sorted(best[2])) or "C" if best else "",
            "dup": dup, "stray": stray, "notlegal": notlegal,
            "distance": distance, "no_commander": no_commander,
            "converted": d["core"] in converted,
        })
    rows.sort(key=lambda r: (r["no_commander"], r["distance"], r["id"]))
    return rows


def suggest_scored(d, *, unowned=False, owned=False, limit=0, fmt=None, any_format=False):
    """Structured core of `suggest` — returns the scored, sorted, limited picks as
    plain dicts so both `cmd_suggest` (renders below) and build_dashboard.py (craft
    table) read from ONE code path and can't drift. See `cmd_suggest` for how each
    field is displayed.

    Returns a dict:
      ok         – False if there's nothing to score (see `reason`).
      reason     – 'no-pool' | 'no-themes' when ok is False.
      colors     – the deck's castable colors (WUBRG set).
      themes     – top-6 [(theme, weight)] for the header line.
      fmt/apply_fmt/has_leg – format-filter state for the header messages.
      picks      – [{name, rarity, owned, decks, score, matches:[themes]}], ranked.
                   `decks` = cross-deck reuse: other decks the card is castable in AND
                   shares a SPECIFIC central theme with (see `_deck_fingerprints`).
      total      – len(picks) (== the shown count).
      hi_reuse   – [(name, decks)] for craftable picks that fit >=3 other decks.
    """
    res = {"ok": False, "reason": None, "colors": set(), "themes": [], "fmt": "",
           "apply_fmt": False, "has_leg": False, "picks": [], "total": 0, "hi_reuse": []}
    if not os.path.exists(POOL_CSV):
        res["reason"] = "no-pool"
        return res

    dmeta, cards = parse_deck_file(d["path"])
    meta = load_card_meta()

    # Format filter: default to the deck's own `#: format:` (--format overrides,
    # --any-format disables). Only bites when the pool carries legality data.
    fmt = "" if any_format else (fmt or dmeta.get("format") or "").strip().lower()

    # Deck fingerprint: theme weights from synergy tags (copies carrying each tag).
    # Front-face normalized: deck files store a DFC under its FRONT name while the pool
    # keys the full "Front // Back", so normalizing both sides to the front lets the
    # "already in deck" filter below catch a DFC that's already maindecked (audit A8/F6).
    deck_names = {n.lower().split(" // ")[0] for _, n, _, _ in cards}
    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = meta.get(n.lower())
        if not m:
            continue
        for t in m["synergies"]:
            theme_w[t] = theme_w.get(t, 0) + q
    if not theme_w:
        res["reason"] = "no-themes"
        return res

    # Deck function + curve profile for the gap-aware scoring below (improvements
    # #1/#2): how many of each functional role the deck ALREADY runs, and its nonland
    # mana curve, so a candidate is weighted by what the deck NEEDS, not just theme fit.
    carddata = load_card_data()
    mana_map = load_mana()
    deck_roles = role_tally(cards, carddata)   # role → copies already in the deck
    deck_curve = {}                            # nonland MV bucket → copies
    for q, n, s, c in cards:
        nl2 = n.lower()
        if nl2 in BASICS:
            continue
        cd2 = carddata.get(nl2)
        if cd2 and "Land" in _primary_type(cd2.get("type") or ""):
            continue
        e = mana_map.get(nl2)
        if e and e[1] is not None:
            b = min(int(e[1]), 7)
            deck_curve[b] = deck_curve.get(b, 0) + q

    # Deck colors = the colors the deck can actually CAST. Prefer the declared
    # `#: colors:`; else derive from mana COSTS — never color identity, so a card's
    # off-color activated abilities don't widen the deck and surface uncastable picks.
    deck_colors = _declared_colors(dmeta)
    if not deck_colors:
        for q, n, s, c in cards:
            if n.lower() in BASICS:
                continue
            entry = mana_map.get(n.lower())
            if entry and entry[0]:
                strict, hybrid = parse_pips(entry[0])
                # Only a TRUE multicolor hybrid ({W/U}) constrains castable colors;
                # a monocolor hybrid ({2/W}) or Phyrexian ({W/P}) is payable WITHOUT
                # its color, so it must not widen the deck's colors and surface
                # uncastable picks (audit F3; mirrors _castability's len(h) >= 2).
                deck_colors |= set(strict) | {x for h in hybrid if len(h) >= 2 for x in h}

    # Score every pool card not already in the deck.
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        pool = list(csv.DictReader(fh))
    has_leg = bool(pool) and "Legalities" in pool[0]
    lkey = pool_format_key(fmt)          # BS8-04: the pool key, not the raw name
    apply_fmt = bool(lkey) and has_leg
    _, _, by_name_qty = load_collection()
    suggestions = []
    for r in pool:
        name = (r.get("Card Name") or "").strip()
        nl = name.lower()
        if not name or nl.split(" // ")[0] in deck_names or nl in BASICS:
            continue
        # LANDS ARE NOT CANDIDATES HERE — `suggest --lands` is the manabase recommender
        # (G-37), and this theme path cannot grade one. The guard is load-bearing rather
        # than tidy: castability below reads the PRINTED COST (G-58), and a land HAS no
        # cost, so `_candidate_castability` passes every land unconditionally — an
        # off-colour one included. That is how a U/G Town (Balamb Garden, SeeD Academy)
        # was offered to Rakdos deck 44a, whose fixing it cannot provide. Front-face
        # typed via `_primary_type`, since a `// Land` BACK face is not a land you cast
        # (the same read `wishlist._is_land` and `suggest --lands` were fixed to use).
        # `functional_theme_options` already carried this exact guard; this caller did
        # not — a working primitive one caller does not reach (G-40).
        if "Land" in _primary_type(r.get("Type") or ""):
            continue
        # CASTABILITY IS READ FROM THE PRINTED COST, not from color identity. The block
        # above is careful to derive the DECK's colors from costs "never color identity";
        # this filter then compared CANDIDATES on identity, so the two halves disagreed.
        # A `{1}{U/R}` hybrid and a `{6}` colorless card are both castable in mono-U or
        # mono-R and both read as off-color in `Color(s)`, so `suggest` could never
        # surface either for any deck. Measured on the red pool: 55 Standard cards a red
        # filter hides that mono-red can cast, including two Dragons at MV 4 whose absence
        # led to a written conclusion that deck 49's curve could not be fixed (G-58,
        # bulk-triage variant). `_candidate_castability` mirrors `_castability_lint`, so
        # a monocolor/Phyrexian hybrid never constrains and only a TRUE multicolor one does.
        ccolors = card_colors(r.get("Color(s)"))
        cast_ok, _ = _candidate_castability(
            (mana_map.get(nl) or mana_map.get(nl.split(" // ")[0]) or ("", None))[0],
            ccolors, deck_colors)
        if not cast_ok:
            continue  # genuinely uncastable for this deck
        if apply_fmt and lkey not in {x.strip() for x in
                                     (r.get("Legalities") or "").split(";")}:
            continue  # not legal in the target format
        shared = [t for t in (r.get("Synergies") or "").split(";")
                  if t.strip() and t.strip() in theme_w]
        if not shared:
            continue
        shared = [t.strip() for t in shared]
        # Theme fit + gap-aware role credit + curve fit. Among on-theme picks, a card
        # that fills a high-value functional role the deck is THIN on (removal / card
        # advantage / ramp / cost-reduction / payoff) outranks a same-theme vanilla body
        # — but that role bonus DIMINISHES if the deck already runs plenty of it (#1), so
        # `suggest` stops recommending the 9th removal spell. The whole score is then
        # nudged by how the card's MV fits the deck's curve (#2) — bounded ±15%, so it
        # re-ranks near-ties without overriding a clear theme-fit winner. Reads the
        # pool's Card Text; a text-less / mana-less row just gets no bonus / factor 1.0.
        roles = classify_roles(r.get("Card Text") or "")
        base = sum(theme_w[t] for t in shared) + _role_credit(roles, deck_roles)
        cand_mv = (mana_map.get(nl) or (None, None))[1]
        # Card-quality (power) co-signal (#6): a heuristic 1–10 power seed (rarity floor +
        # roles + planeswalker/legendary), added modestly so an owned/craftable BOMB with
        # only MODEST theme overlap isn't buried under a well-tagged vanilla body. It can't
        # pull in off-theme junk — only cards already sharing ≥1 theme are scored here — so
        # it re-ranks WITHIN the on-theme set, the way wishlist --rank pairs fit with power.
        score = round(base * _curve_gap_factor(cand_mv, deck_curve) + _SUGGEST_POWER_W * _power_seed(r), 2)
        suggestions.append((score, name, r, shared))

    # Ownership is keyed by the LIBRARY name (DFCs stored under their front face), but
    # pool card names are the full "Front // Back" — the shared lib.owned_qty falls
    # back to the front so an owned DFC isn't mis-surfaced as a craft target (audit F6).
    owned_of = lambda nl: owned_qty(by_name_qty, nl)
    if unowned:
        suggestions = [x for x in suggestions if owned_of(x[1].lower()) == 0]
    if owned:
        suggestions = [x for x in suggestions if owned_of(x[1].lower()) > 0]
    # Rank: strongest theme fit first, then NAME for a total order (G-54).
    # Ownership used to be the tiebreaker, 'so quick adds float up' — which meant that
    # at equal fit the owned card always printed above the unowned one, and a reader
    # working down the list met the owned pool first by construction. Two reasons that
    # is wrong: the goal is the best LIST, not the cheapest one, and this repo's
    # owned/unowned data is hand-maintained, so the tiebreak silently ranks on
    # information that may be weeks stale. Ownership is still SHOWN on every row
    # (`×N` / `craft R`) — it is a note, not a ranking term. The `--owned` /
    # `--unowned` FILTERS are untouched: those are the user asking a scoped question.
    suggestions.sort(key=lambda x: (-x[0], x[1].lower()))
    top = suggestions if limit == 0 else suggestions[:limit]

    fps = _deck_fingerprints(meta, exclude_id=d["id"])
    _mm = load_mana()
    # ⚠rot is a CRAFT flag (G-30: an owned card costs no wildcard) and a STANDARD flag —
    # a Brawl deck's picks do not rotate out of Brawl. Until BS8-12 it printed on owned
    # rows and on 20–29 of 40 picks for each Brawl deck.
    _rot_deck = pool_format_key(dmeta.get("format")) == "standard" if not any_format else False
    picks, hi_reuse = [], []
    for score, name, r, shared in top:
        h = owned_of(name.lower())
        card_cols = card_colors(r.get("Color(s)"))
        card_themes = {t.strip() for t in (r.get("Synergies") or "").split(";") if t.strip()}
        _me = _mm.get(name.lower())
        fits = cross_deck_breadth(card_cols, card_themes, fps, cost=_me[0] if _me else "")
        if h == 0 and fits >= 3:
            hi_reuse.append((name, fits))
        picks.append({"name": name, "rarity": (r.get("Rarity") or "").strip(),
                      "owned": h, "decks": fits, "score": score, "matches": shared,
                      "rotates": bool(_rot_deck and h == 0 and rotation_risk(
                          r.get("Released") or "", set_code=r.get("Set Code") or "",
                          legal={x.strip() for x in (r.get("Legalities") or "").split(";")}))})

    res.update(ok=True, colors=deck_colors,
               themes=sorted(theme_w.items(), key=lambda kv: -kv[1])[:6],
               fmt=fmt, apply_fmt=apply_fmt, has_leg=has_leg,
               picks=picks, total=len(top), hi_reuse=hi_reuse)
    return res


def suggest_lands(d, unowned=False, owned=False, limit=20, fmt=None, any_format=False):
    """Recommend LANDS for a deck's manabase — the axis theme-based `suggest` is blind to
    (it filters candidates to cards sharing a synergy theme, and lands rarely do, so it can
    never surface a manabase upgrade). Scores each on-color land by FIXING value
    (`wishlist._land_value`: produces the deck's colors, untapped premium — the DOMINANT
    axis) PLUS a bounded SYNERGY nudge (a land whose ability plays the deck's central themes
    — Air Temple's team-pump in a go-wide deck) and a bounded SHORTFALL nudge (favor the
    color the deck is scarcest on, from pip-demand vs current sources)."""
    import wishlist
    meta = load_card_meta()
    dmeta, cards = parse_deck_file(d["path"])
    mana_map = load_mana()
    carddata = load_card_data()
    pool_rot, _has_released = _pool_rotation_index()

    deck_colors = _declared_colors(dmeta)
    if not deck_colors:
        # COSTS, not identity — the same rule `suggest_scored` follows and states, so an
        # off-colour activated ability or a transform face cannot widen the deck and
        # surface picks it cannot actually cast (audit F3/F15, BS4-12).
        deck_colors = _deck_castable_colors(dmeta, cards, mana_map)

    # central themes (for the synergy nudge) + names already in the deck
    theme_w, deck_names = {}, set()
    for q, n, _s, _c in cards:
        nl = n.lower()
        deck_names.add(nl.split(" // ")[0])
        if nl in BASICS:
            continue
        m = meta.get(nl)
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    central = _central_themes(theme_w)
    central_w = {t: theme_w[t] for t in central}

    # current color sources (lands) + strict pip demand -> per-color scarcity (deficit)
    all_sources = deck_color_sources(cards, meta, carddata)   # ONE count (BS8-01)
    sources = {c: all_sources.get(c, 0) for c in deck_colors}
    demand = {c: 0 for c in deck_colors}
    for q, n, _s, _c in cards:
        nl = n.lower()
        if nl in BASICS:
            continue
        cd = carddata.get(nl)
        if "Land" in _primary_type((cd["type"] if cd else "") or ""):
            continue
        entry = mana_map.get(nl)
        if entry and entry[0]:
            strict, _hy = parse_pips(entry[0])
            for col, cnt in strict.items():
                if col in demand:
                    demand[col] += cnt * q
    tot_d = sum(demand.values()) or 1
    tot_s = sum(sources.values()) or 1
    deficit = {c: max(0.0, demand[c] / tot_d - sources[c] / tot_s) for c in deck_colors}

    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        pool = list(csv.DictReader(fh))
    has_leg = bool(pool) and "Legalities" in pool[0]
    # Default to the deck's own `#: format:`, exactly as the card-facing `suggest` does
    # (--format overrides, --any-format disables). Without this line the land recommender
    # only filtered when someone passed --format explicitly, so a plain
    # `suggest --lands <id>` on a Standard deck offered Underground River and Duskmantle,
    # House of Shadow as craft targets — neither is Standard-legal. This is a
    # WILDCARD-SPEND recommender, so an unfiltered pick costs real resources, and it is
    # exactly the "recommending a craft without a legality check" failure CLAUDE.md warns
    # about. Found by USING the tool to build a deck, not by any test.
    fmt = "" if any_format else (fmt or dmeta.get("format") or "").strip().lower()
    lkey = pool_format_key(fmt)          # BS8-04: the pool key, not the raw name
    apply_fmt = bool(lkey) and has_leg
    _, _, by_name_qty = load_collection()
    owned_of = lambda nl: owned_qty(by_name_qty, nl)

    picks = []
    for r in pool:
        name = (r.get("Card Name") or "").strip()
        nl = name.lower()
        if not name or nl.split(" // ")[0] in deck_names or nl in BASICS:
            continue
        # FRONT face, via `_primary_type` — the same test `wishlist._is_land` was fixed to
        # use in BS2-11, and the manabase RECOMMENDER kept the whole-type-line substring
        # scan it was fixed away from. So any card with `// Land` on its BACK qualified:
        # three of `suggest 52 --lands`' four highest-scored picks were Tarrian's Journal
        # (Artifact front), Grasping Shadows (Enchantment front) and Aclazotz (Creature
        # front). Those are reached by TRANSFORMING, never by a land drop — maindeck one
        # and the deck is a land short with INV-04 seeing nothing wrong, because the line
        # is a perfectly valid card line. G-37's live residual; the G-63 TYPE-column shape.
        if _primary_type(r.get("Type") or "") != "Land":
            continue
        if apply_fmt and lkey not in {x.strip() for x in (r.get("Legalities") or "").split(";")}:
            continue
        txt = (r.get("Card Text") or "")
        # What the land PRODUCES, from its text (`lib.land_production`, BS8-02). The old
        # test was identity plus a bare `{W}` scan, which is EMPTY for every "Add one mana
        # of any color" land and every basic fetch — 33 Standard-legal any-colour lands
        # and 9 fetches were skipped before scoring, so the five-colour deck 17 got 199
        # picks holding none of them. A fetch produces whichever basics the deck runs;
        # restricted / extra-cost production is admitted here and discounted in
        # `_land_value`, which prints `·restricted` for the human read.
        lp = land_production(txt, r.get("Color(s)"))
        prod = set(lp["free"]) | set(lp["restricted"]) | set(lp["conditional"])
        if lp["fetch"]:
            prod |= set(deck_colors)
        on_color = prod & deck_colors
        if not on_color:
            continue  # off-color / colorless-only: doesn't fix THIS deck's manabase
        h = owned_of(nl)
        if unowned and h > 0:
            continue
        if owned and h == 0:
            continue
        fix = wishlist._land_value(r, deck_colors)
        tags = [t.strip() for t in (r.get("Synergies") or "").split(";") if t.strip()]
        syn = _land_synergy_bonus(tags, central_w)
        short = _land_shortfall_bonus(on_color, deficit)
        low = txt.lower()
        tapped = ("enters tapped" in low or "enters the battlefield tapped" in low)
        # CONDITIONAL vs FLAT tapping, shown separately. `_land_value` treats both as
        # tapped, which is the conservative read and is exactly right for a deck that
        # cannot meet the condition — but it is an UNDER-score for one that can (Great
        # Arashin City enters untapped in any deck with a Forest). Deciding satisfiability
        # needs the deck's contents, so this REPORTS the condition instead of guessing:
        # G-52's rule that a verdict surface prints its evidence.
        cond_tapped = tapped and "unless" in low
        # Restricted production ("Spend this mana only to cast a creature spell"). The
        # score already discounts it; this is what lets a human tell WHY.
        restricted = "spend this mana only" in low
        picks.append({
            "name": name, "rarity": (r.get("Rarity") or "").strip(), "owned": h,
            "fix": fix, "syn": syn, "short": short, "score": round(fix + syn + short, 2),
            "produces": "".join(c for c in "WUBRG" if c in on_color),
            "tapped": tapped, "cond_tapped": cond_tapped, "restricted": restricted,
            "text": txt, "matches": sorted(set(tags) & central),
            # G-30 on a WILDCARD-SPEND surface. `check`, `wildcards` and `wishlist --rank`
            # all flag a rotating craft target; this recommender — which exists to be
            # spent on — said nothing, and deck 28's plan bought four rotating cards past
            # views that were quiet in exactly this way (BS4-11).
            "rot": craft_rot_note(name, pool_rot),
        })
    # Ownership is NOT a ranking term — the same decision `suggest_scored` records and
    # explains: the goal is the best LIST, not the cheapest one, and this repo's
    # owned/unowned data is hand-maintained and may be weeks stale (G-10 saw five wrong
    # counts in one session). It stays SHOWN on every row as `×N` / `craft`. These three
    # siblings kept the old tiebreak, so at equal score the owned card always outranked a
    # possibly-better unowned one on exactly the wildcard-spend surfaces (BS4-36).
    picks.sort(key=lambda p: (-p["score"], p["name"].lower()))
    if limit and limit > 0:
        picks = picks[:limit]
    return {"ok": True, "colors": deck_colors, "picks": picks, "fmt": fmt,
            "apply_fmt": apply_fmt, "has_leg": has_leg, "sources": sources, "deficit": deficit}


def cmd_suggest_lands(args, d):
    """Render suggest_lands (the manabase recommender)."""
    res = suggest_lands(d, unowned=args.unowned, owned=getattr(args, "owned", False),
                        limit=args.limit, fmt=getattr(args, "fmt", None),
                        any_format=getattr(args, "any_format", False))
    dc = res["colors"]
    print(f"Deck {d['id']}: {d['name'] or d['path']} — LAND suggestions (manabase)\n")
    print("Colors: " + ("/".join(sorted(dc)) or "Colorless") + "  ·  current sources: "
          + ", ".join(f"{c} {res['sources'].get(c, 0)}" for c in sorted(dc)))
    scarce = sorted(res["deficit"].items(), key=lambda kv: -kv[1])
    if scarce and scarce[0][1] > 0:
        print(f"Scarcest color (strict pip-demand vs sources): {scarce[0][0]} "
              "— lands producing it get the shortfall nudge.")
    if res["apply_fmt"]:
        print(f"Format: {res['fmt']}-legal only  (override with --format / --any-format)")
    if not res["picks"]:
        print("\nNo on-color lands to suggest (rebuild card-pool.csv with build_pool.py --all?).")
        return 0
    print(f"\n  {'Have':5} {'Land':30} {'Rarity':8} {'Prod':4} {'Fix':>4} {'Syn':>4} "
          f"{'Sh':>4} {'Score':>5}")
    print("-" * 78)
    rotting = 0
    for p in res["picks"]:
        have = f"×{p['owned']}" if p["owned"] else "craft"
        tap = (" ·tapped?" if p.get("cond_tapped") else " ·tapped") if p["tapped"] else ""
        tap += " ·restricted" if p.get("restricted") else ""
        # Only a CRAFT pick's rotation matters here — an owned land costs no wildcard.
        rot = f" {p['rot']}" if p.get("rot") and not p["owned"] else ""
        rotting += 1 if rot else 0
        print(f"  {have:5} {p['name'][:30]:30} {(p['rarity'] or '?')[:8]:8} "
              f"{p['produces']:4} {p['fix']:>4.1f} {p['syn']:>4.1f} {p['short']:>4.1f} "
              f"{p['score']:>5.1f}{tap}{rot}")
    if rotting:
        print(f"\n⚠ {rotting} craft pick(s) rotate out of Standard this year or next — "
              "see `deck.py rotation` before spending a wildcard.")
    if getattr(args, "full", False):
        import textwrap
        print("\n── Oracle text of the top picks (grade the ability, not just the fixing) ──")
        for p in res["picks"][:min(8, len(res["picks"]))]:
            print(f"\n• {p['name']}"
                  + (f"   synergy: {', '.join(p['matches'])}" if p["matches"] else ""))
            for para in (p["text"] or "(no oracle text)").split("\n"):
                for line in (textwrap.wrap(para, width=86) or [""]):
                    print(f"    {line}")
    if any(p.get("cond_tapped") for p in res["picks"]):
        print("\n·tapped? = enters tapped UNLESS a condition holds — scored as tapped "
              "(conservative). Read the clause: if THIS deck meets it, the land is better "
              "than its score says.")
    if any(p.get("restricted") for p in res["picks"]):
        print("·restricted = the colored mana has a 'spend this only to…' clause. Its "
              "fixing premium is halved; judge it against what your deck actually casts.")
    print("\nScore = FIXING value (0–10, dominant: produces your colors, untapped premium) "
          "+ bounded SYNERGY (land ability hits a deck theme) + bounded SHORTFALL (produces "
          "the scarce color). Ownership is a NOTE (×N / craft), not a ranking term — "
          "a 0-wildcard fixer is often the right pick, but that is your call, not the "
          "sort's, and the owned data here goes stale between updates.")
    return 0


def suggest_mana(d, needs, unowned=False, owned=False, limit=20, fmt=None):
    """Recommend nonland MANA SOURCES (dorks / rocks / ramp) — the structural need theme-based
    suggest can't see (a fixer shares no synergy theme). Per-card rank = FIXING (produces the
    deck's / scarce colors) + RESTRICTION-fit (a restricted-mana dork matching the deck's
    dominant type) + a small power tiebreak. Whether the deck WANTS ramp at all is the deck-
    level `needs['accel']`, shown in the header — not a per-card term (it'd just scale the list).
    """
    dc, deficit, ts = needs["colors"], needs["deficit"], needs["type_share"]
    mana_map = load_mana()
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        pool = list(csv.DictReader(fh))
    has_leg = bool(pool) and "Legalities" in pool[0]
    lkey = pool_format_key(fmt)          # BS8-04: the pool key, not the raw name
    apply_fmt = bool(lkey) and has_leg
    _, _, by_name_qty = load_collection()
    owned_of = lambda nl: owned_qty(by_name_qty, nl)
    pool_rot, _has_released = _pool_rotation_index()      # G-30 craft flag (BS4-11)
    picks = []
    for r in pool:
        name = (r.get("Card Name") or "").strip()
        nl = name.lower()
        if not name or nl.split(" // ")[0] in needs["names"] or nl in BASICS:
            continue
        tline = r.get("Type") or ""
        pt = _primary_type(tline)
        if pt in ("Land", "Instant", "Sorcery"):
            continue  # lands are --lands' job; instants/sorceries are one-shot rituals, not ramp
        txt = r.get("Card Text") or ""
        # a REPEATABLE mana source: an activated mana ability (":" before "add"), so an
        # ETB-treasure body or a vanilla creature that merely mentions mana doesn't qualify.
        if not (_produces_mana(txt) and re.search(r":[^.\n]{0,40}\badd\b", txt, re.I)):
            continue
        # Castability from the PRINTED COST, not color identity — the exact filter
        # suggest_scored uses (G-58): an identity-subset test here hid 25 castable mana
        # sources, including every `{N}` rock whose identity comes from its mana ability
        # (Haunted Screen's 5-color identity excluded it from EVERY deck). Worst place
        # for that bug: per G-38 this recommender IS the fix path for a mana deficit.
        cast_ok, _ = _candidate_castability(
            (mana_map.get(nl) or mana_map.get(nl.split(" // ")[0]) or ("", None))[0],
            card_colors(r.get("Color(s)")), dc)
        if not cast_ok:
            continue  # genuinely uncastable for this deck
        if apply_fmt and lkey not in {x.strip() for x in (r.get("Legalities") or "").split(";")}:
            continue
        h = owned_of(nl)
        if (unowned and h > 0) or (owned and h == 0):
            continue
        # Ramp is about ACCELERATION, not fixing (a 2-color deck's fixing is nearly solved) —
        # so the dominant axis is CHEAPNESS × the deck's accel-want (a 1-drop dork ramps a
        # top-heavy deck; a 4-mana rainbow rock barely helps). Fixing enters only as the
        # bounded scarce-color bonus (reused from --lands), and restriction-fit + power tiebreak.
        prod = _produced_colors(txt, dc)
        mv = (mana_map.get(nl) or (None, None))[1]
        cheap = max(0.0, (5 - (mv if mv is not None else 3))) / 4.0   # 1-drop→1.0, 5-drop→0.0
        accel_c = round(_RAMP_ACCEL_CAP * needs["accel"] * min(1.0, cheap), 2)
        fixb = _land_shortfall_bonus(prod & dc, deficit)
        restr = _ramp_restriction_fit(txt, ts)
        power = _power_seed(r)
        score = round(accel_c + fixb + restr + max(0.0, min(1.0, 0.2 * (power - 4))), 2)
        picks.append({"name": name, "rarity": (r.get("Rarity") or "").strip(), "owned": h,
                      "fix": fixb, "accel": accel_c, "restr": restr, "power": round(power, 1),
                      "score": score, "mv": mv if mv is not None else "?",
                      "produces": "".join(c for c in "WUBRG" if c in prod) or "?",
                      "restricted": _RESTRICT_RE.search(txt) is not None, "text": txt,
                      "rot": craft_rot_note(name, pool_rot)})   # G-30 (BS4-11)
    # Ownership is NOT a ranking term — the same decision `suggest_scored` records and
    # explains: the goal is the best LIST, not the cheapest one, and this repo's
    # owned/unowned data is hand-maintained and may be weeks stale (G-10 saw five wrong
    # counts in one session). It stays SHOWN on every row as `×N` / `craft`. These three
    # siblings kept the old tiebreak, so at equal score the owned card always outranked a
    # possibly-better unowned one on exactly the wildcard-spend surfaces (BS4-36).
    picks.sort(key=lambda p: (-p["score"], p["name"].lower()))
    return picks[:limit] if limit and limit > 0 else picks


def suggest_interaction(d, needs, unowned=False, owned=False, limit=20, fmt=None):
    """Recommend INTERACTION (removal / sweeper / counter) — including OFF-THEME cards that
    theme-suggest filters out. Per-card rank = impact role credit + a bounded SCALING boost for
    a board-dependent removal spell the deck's board supports (fight in an equipment deck,
    'damage = creatures you control' in a go-wide deck) + a small power tiebreak. The scaling is
    FLAGGED with the deck metric so the human confirms — it's never a silent boost."""
    dc = needs["colors"]
    mana_map = load_mana()
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        pool = list(csv.DictReader(fh))
    has_leg = bool(pool) and "Legalities" in pool[0]
    lkey = pool_format_key(fmt)          # BS8-04: the pool key, not the raw name
    apply_fmt = bool(lkey) and has_leg
    _, _, by_name_qty = load_collection()
    owned_of = lambda nl: owned_qty(by_name_qty, nl)
    pool_rot, _has_released = _pool_rotation_index()      # G-30 craft flag (BS4-11)
    picks = []
    for r in pool:
        name = (r.get("Card Name") or "").strip()
        nl = name.lower()
        if not name or nl.split(" // ")[0] in needs["names"] or nl in BASICS:
            continue
        if "land" in (r.get("Type") or "").lower():
            continue
        txt = r.get("Card Text") or ""
        roles = set(classify_roles(txt))
        if not (roles & _INTERACTION_ROLES):
            continue  # not interaction
        # Castability from the PRINTED COST, not color identity — the exact filter
        # suggest_scored uses (G-58): an identity-subset test here hid 34 castable
        # Standard interaction cards from mono-color decks (Bullseye, Death Dealer
        # `{2}{B/R}` — the card G-58 names — read as off-color in `Color(s)`). Worst
        # place for that bug: per G-38 this IS the fix path for an interaction deficit.
        cast_ok, _ = _candidate_castability(
            (mana_map.get(nl) or mana_map.get(nl.split(" // ")[0]) or ("", None))[0],
            card_colors(r.get("Color(s)")), dc)
        if not cast_ok:
            continue
        if apply_fmt and lkey not in {x.strip() for x in (r.get("Legalities") or "").split(";")}:
            continue
        h = owned_of(nl)
        if (unowned and h > 0) or (owned and h == 0):
            continue
        axis = _int_scaling(txt)
        boost = _int_scaling_boost(axis, _scaling_metric(axis, needs)) if axis else 0.0
        power = _power_seed(r)
        # Rank on card QUALITY (power, 0–10) + the board-scaling boost + a small flex credit
        # for answering more than one thing (modal / covers a noncreature permanent).
        flex = 0.5 if len(roles & _INTERACTION_ROLES) > 1 else 0.0
        score = round(power + boost + flex, 2)
        picks.append({"name": name, "rarity": (r.get("Rarity") or "").strip(), "owned": h,
                      "roles": sorted(roles & _INTERACTION_ROLES), "axis": axis, "boost": boost,
                      "power": round(power, 1), "score": score, "text": txt,
                      "rot": craft_rot_note(name, pool_rot)})   # G-30 (BS4-11)
    # Ownership is NOT a ranking term — the same decision `suggest_scored` records and
    # explains: the goal is the best LIST, not the cheapest one, and this repo's
    # owned/unowned data is hand-maintained and may be weeks stale (G-10 saw five wrong
    # counts in one session). It stays SHOWN on every row as `×N` / `craft`. These three
    # siblings kept the old tiebreak, so at equal score the owned card always outranked a
    # possibly-better unowned one on exactly the wildcard-spend surfaces (BS4-36).
    picks.sort(key=lambda p: (-p["score"], p["name"].lower()))
    return picks[:limit] if limit and limit > 0 else picks


def _needs_fmt(args, needs):
    """The format filter for the needs recommenders (--ramp/--interaction/--needs) —
    the SAME normalization `suggest_scored`/`suggest_lands` apply, honouring
    --any-format, and never silent when the filter cannot bite. These three wrappers
    used to hand `args.fmt` through raw: `--format Standard` (the natural spelling)
    failed the exact-membership `fmt in POOL_FORMATS` test in the workers, so ALL
    format filtering was dropped with no message — non-Standard cards surfaced as top
    craft picks on exactly the paths G-38 routes a deficit to, the G-37 incident
    relived — and `--any-format` parsed but never reached the workers at all
    (broad-scan BS2-08; the G-45 "diff the siblings' filters" shape, third time on
    this family after G-58 and BS-01)."""
    if getattr(args, "any_format", False):
        return ""
    fmt = (getattr(args, "fmt", None) or needs["format"] or "").strip().lower()
    if not fmt:
        return fmt
    if not pool_format_key(fmt):
        print(f"Format: '{fmt}' not tracked — not filtering. "
              f"(known: {', '.join(sorted(POOL_FORMATS))})")
    elif "Legalities" not in (_header_of_pool() or []):
        print(f"Format: '{fmt}' filter requested but card-pool.csv has no legality "
              "data — rebuild with build_pool.py. Showing all.")
    return fmt


def _header_of_pool():
    """card-pool.csv's header row, or None — one cheap read for the warning above."""
    try:
        with open(POOL_CSV, newline="", encoding="utf-8") as fh:
            return next(csv.reader(fh), None)
    except OSError:
        return None


def cmd_suggest_ramp(args, d):
    needs = deck_needs(d)
    fmt = _needs_fmt(args, needs)
    picks = suggest_mana(d, needs, unowned=args.unowned, owned=getattr(args, "owned", False),
                         limit=args.limit, fmt=fmt)
    accel = needs["accel"]
    band = "HIGH" if accel >= 0.5 else "moderate" if accel >= 0.2 else "LOW"
    print(f"Deck {d['id']}: {d['name'] or d['path']} — MANA-SOURCE suggestions (dorks/rocks)\n")
    print(f"Colors: {'/'.join(sorted(needs['colors'])) or 'Colorless'}  ·  avg MV {needs['avg_mv']}"
          f"  ·  acceleration want: {band} ({accel})")
    if band == "LOW":
        print("  (a lean curve — you may not want dorks at all; ranked on FIXING value.)")
    if not picks:
        print("\nNo on-color mana sources to suggest.")
        return 0
    print(f"\n  {'Have':5} {'Card':28} {'MV':>2} {'Prod':4} {'Acl':>4} {'Fix':>4} {'Rstr':>5} "
          f"{'Pw':>3} {'Score':>5}")
    print("-" * 74)
    rotting = 0
    for p in picks:
        have = f"×{p['owned']}" if p["owned"] else "craft"
        tag = " ·restricted" if p["restricted"] else ""
        rot = f" {p['rot']}" if p.get("rot") and not p["owned"] else ""
        rotting += 1 if rot else 0
        print(f"  {have:5} {p['name'][:28]:28} {str(p['mv']):>2} {p['produces']:4} "
              f"{p['accel']:>4.1f} {p['fix']:>4.1f} {p['restr']:>5.1f} {p['power']:>3.0f} "
              f"{p['score']:>5.1f}{tag}{rot}")
    if rotting:
        print(f"\n⚠ {rotting} craft pick(s) rotate out of Standard this year or next — "
              "see `deck.py rotation` before spending a wildcard.")
    print("\nScore = ACCELERATION (cheapness × the deck's accel-want — a cheap dork ramps a "
          "top-heavy deck) + bounded FIXING (scarce color) + RESTRICTION-fit (a restricted dork "
          "matching your deck type; − if mismatched) + power tiebreak. Grade ETB value from text.")
    return 0


def cmd_suggest_interaction(args, d):
    needs = deck_needs(d)
    fmt = _needs_fmt(args, needs)
    picks = suggest_interaction(d, needs, unowned=args.unowned, owned=getattr(args, "owned", False),
                                limit=args.limit, fmt=fmt)
    it, tgt = needs["interaction"], needs["int_target"]
    state = f"SHORT ({it} < {tgt})" if needs["int_short"] else f"adequate ({it})"
    print(f"Deck {d['id']}: {d['name'] or d['path']} — INTERACTION suggestions (incl. off-theme)\n")
    print(f"Colors: {'/'.join(sorted(needs['colors'])) or 'Colorless'}  ·  "
          f"current interaction: {state}")
    if not needs["int_short"]:
        print("  (already at target — showing anyway; a board-scaling pick may still upgrade.)")
    if not picks:
        print("\nNo on-color interaction to suggest.")
        return 0
    print(f"\n  {'Have':5} {'Card':28} {'Rarity':8} {'Role':16} {'Pw':>3} {'Score':>5}  Scaling")
    print("-" * 86)
    rotting = 0
    for p in picks:
        have = f"×{p['owned']}" if p["owned"] else "craft"
        role = "/".join(x.split()[0] for x in p["roles"])[:16]
        scale = ""
        if p["axis"]:
            metric = _scaling_metric(p["axis"], needs)
            scale = f"⚠ scales w/ {p['axis']} (deck {metric:.0%}, +{p['boost']:.1f})"
        rot = f" {p['rot']}" if p.get("rot") and not p["owned"] else ""
        rotting += 1 if rot else 0
        print(f"  {have:5} {p['name'][:28]:28} {(p['rarity'] or '?')[:8]:8} {role:16} "
              f"{p['power']:>3.0f} {p['score']:>5.1f}  {scale}{rot}")
    if rotting:
        print(f"\n⚠ {rotting} craft pick(s) rotate out of Standard this year or next — "
              "see `deck.py rotation` before spending a wildcard.")
    print("\nScore = impact role credit + a bounded SCALING boost (a board-dependent removal "
          "spell your board supports) + power tiebreak. ⚠ scaling cards are FLAGGED with your "
          "deck's strength on that axis — grade them for THIS board from full text.")
    return 0


def cmd_suggest_needs(args, d):
    """Unified structural-needs view: fixing (lands + dorks), acceleration (dorks), interaction —
    the one-stop 'what does my deck LACK' report, composing the three needs-aware recommenders."""
    needs = deck_needs(d)
    fmt = _needs_fmt(args, needs)
    print(f"Deck {d['id']}: {d['name'] or d['path']} — STRUCTURAL NEEDS\n")
    dc = needs["colors"]
    scarce = sorted(needs["deficit"].items(), key=lambda kv: -kv[1])
    scarce_c = scarce[0][0] if scarce and scarce[0][1] > 0 else None
    print(f"Colors {'/'.join(sorted(dc)) or 'Colorless'} · sources "
          + ", ".join(f"{c} {needs['sources'].get(c, 0)}" for c in sorted(dc))
          + (f" · scarcest {scarce_c}" if scarce_c else " · balanced"))
    accel = needs["accel"]
    aband = "HIGH" if accel >= 0.5 else "moderate" if accel >= 0.2 else "LOW"
    print(f"Acceleration want: {aband} (avg MV {needs['avg_mv']}) · "
          f"Interaction: {needs['interaction']}/{needs['int_target']}"
          + ("  ⚠ short" if needs["int_short"] else "  ok"))

    def _top(title, rows, fmt_row, n=4):
        print(f"\n── {title} ──")
        if not rows:
            print("  (nothing to suggest)")
            return
        for p in rows[:n]:
            print("  " + fmt_row(p))

    # any_format must be FORWARDED here, not folded into fmt="": suggest_lands treats
    # a blank fmt as "fall back to the deck's own #: format:", which would re-enable
    # the filter --any-format just disabled.
    lands = suggest_lands(d, owned=True, limit=4, fmt=fmt,
                          any_format=getattr(args, "any_format", False))["picks"]
    _top("Fixing · owned lands", lands,
         lambda p: f"×{p['owned']} {p['name'][:34]:34} {p['produces']:4} score {p['score']:.1f}")
    dorks = suggest_mana(d, needs, owned=True, limit=4, fmt=fmt)
    _top("Fixing / acceleration · owned mana sources", dorks,
         lambda p: f"×{p['owned']} {p['name'][:34]:34} {p['produces']:4} score {p['score']:.1f}"
                   + (" ·restricted" if p["restricted"] else ""))
    inter = suggest_interaction(d, needs, owned=True, limit=4, fmt=fmt)
    _top("Interaction · owned" + ("  (deck is SHORT)" if needs["int_short"] else ""), inter,
         lambda p: f"×{p['owned']} {p['name'][:30]:30} {('/'.join(x.split()[0] for x in p['roles']))[:14]:14}"
                   + (f"  ⚠{p['axis']}" if p["axis"] else "") + f"  score {p['score']:.1f}")
    print("\n(owned/0-wildcard picks shown; add --unowned to any single mode for craft targets. "
          "These are STRUCTURAL fills the theme-based `suggest` can't see — grade from text.)")
    return 0


def cmd_suggest(args):
    """Recommend pool cards that fit a deck's color identity and synergy themes.

    Scores each candidate by how strongly its tags overlap the deck's themes
    (weighted by how central each theme is to the deck), filters to the deck's
    colors, and flags owned vs. craftable with wildcard rarity. Composes
    card-pool.csv + the synergy tags + tribes-style theme matching. Rendering only —
    the scoring lives in suggest_scored() so the dashboard shares it verbatim.
    With --lands, defers to the manabase recommender (cmd_suggest_lands) instead.
    """
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    if not os.path.exists(POOL_CSV):
        eprint("No card-pool.csv. Build it: python3 scripts/build_pool.py")
        return 1
    if getattr(args, "lands", False):
        return cmd_suggest_lands(args, d)
    if getattr(args, "ramp", False):
        return cmd_suggest_ramp(args, d)
    if getattr(args, "interaction", False):
        return cmd_suggest_interaction(args, d)
    if getattr(args, "needs", False):
        return cmd_suggest_needs(args, d)

    res = suggest_scored(d, unowned=args.unowned, owned=getattr(args, "owned", False),
                         limit=args.limit, fmt=getattr(args, "fmt", None),
                         any_format=getattr(args, "any_format", False))
    if not res["ok"]:
        if res["reason"] == "no-themes":
            print(f"Deck {d['id']} has no synergy tags to match against "
                  "(run tag_synergies.py). Nothing to suggest.")
            return 0
        eprint("No card-pool.csv. Build it: python3 scripts/build_pool.py")
        return 1

    deck_colors, fmt = res["colors"], res["fmt"]
    print(f"Deck {d['id']}: {d['name'] or d['path']} — suggestions from the pool\n")
    print(f"Colors: {'/'.join(sorted(deck_colors)) or 'Colorless'}  ·  "
          f"top themes: {', '.join(f'{t}({w})' for t, w in res['themes'])}")
    if res["apply_fmt"]:
        print(f"Format: {fmt}-legal only  (override with --format <fmt> / --any-format)")
    elif fmt and not res["has_leg"]:
        print(f"Format: '{fmt}' filter requested but card-pool.csv has no legality "
              "data — rebuild with build_pool.py. Showing all.")
    elif fmt and not pool_format_key(fmt):
        print(f"Format: '{fmt}' not tracked — not filtering. "
              f"(known: {', '.join(sorted(POOL_FORMATS))})")
    stale = pool_staleness_days()
    if stale is not None and stale > 180:
        print(f"⚠ card-pool.csv was built {stale} days ago — Standard legality may be "
              "stale (sets rotate). Rebuild: build_pool.py --all (or /refresh).")
    if not res["picks"]:
        print("\nNo pool cards matched this deck's colors + themes.")
        return 0
    rotn = sum(1 for p in res["picks"] if p.get("rotates"))
    if rotn:
        print(f"({rotn} pick(s) marked ⚠rot — set >3yr old, may have rotated / rotates soon)")
    # PIP DEPTH. `suggest`'s colour filter is a SET test (card identity ⊆ deck colours)
    # and cannot see whether the deck can pay the pips — the same blind spot
    # `suggest-homes` has carried a flag for since G-32, which this surface never called.
    # It recommended Elegy Acolyte ({2}{B}{B}) into a deck holding 8 black sources, 45%
    # on curve. Display only: it never filters a pick or moves a score.
    _pipmeta, _pipcards = parse_deck_file(d["path"])
    _pipsrc = deck_color_sources(_pipcards, load_card_meta(), load_card_data())
    _piptot = sum(q for q, *_ in _pipcards)
    _pipmana = load_mana()
    pipwarns = {}
    for p in res["picks"]:
        _e = (_pipmana.get(p["name"].lower())
              or _pipmana.get(p["name"].split(" // ")[0].lower()))
        w = pip_depth_warning(_e[0] if _e else "", _pipsrc, total=_piptot)
        if w:
            pipwarns[p["name"]] = w
    print(f"\n{'Have':>5}  {'Card':28}  {'Rarity':8}  {'Decks':>5}  Matches (deck themes)")
    print("-" * 82)
    craftby = {}
    for p in res["picks"]:
        h = p["owned"]
        have = f"×{h}" if h > 0 else "craft"
        rar = p["rarity"]
        if h == 0:
            craftby[rar] = craftby.get(rar, 0) + 1
        rotflag = " ⚠rot" if p.get("rotates") else ""
        pw = pipwarns.get(p["name"])
        pipflag = f"  ⚠⚠{pw[1]}x{{{pw[0]}}} vs {pw[2]} src" if pw else ""
        print(f"{have:>5}  {p['name'][:28]:28}  {rar[:8]:8}  {p['decks']:>5}  "
              f"{', '.join(p['matches'][:5])}{rotflag}{pipflag}")
    if pipwarns:
        print(f"⚠⚠ {len(pipwarns)} pick(s) flagged on PIP DEPTH — the colour filter is a set "
              "test and cannot see whether you can pay the pips. 3+ pips means you likely "
              "cannot cast it; 2 pips means you will cast it late. `deck.py consistency "
              f"{d['id']}` prices any of them exactly.")
    ncraft = sum(craftby.values())
    print("-" * 82)
    print(f"{res['total']} suggestion(s) — {res['total'] - ncraft} owned, {ncraft} to craft"
          + (f" ({', '.join(f'{n} {r}' for r, n in sorted(craftby.items()))})"
             if ncraft else ""))
    print("Decks = how many of your OTHER decks the card is castable in + shares a "
          "SPECIFIC central theme with — generic overlap (etb/tokens/counters/…) and "
          "broad tribes don't count (higher = more value per wildcard).")
    if res["hi_reuse"]:
        print("High cross-deck reuse: "
              + ", ".join(f"{n} ({k})" for n, k in sorted(res["hi_reuse"], key=lambda x: -x[1])[:6]))

    # --full: phased ingestion for ADDS — print the full oracle text + keywords +
    # ⚠ flags of the picks, so a craft/owned add is graded from text (like `cuts`
    # does for the deck's own cards), never from the tag-match line above.
    if getattr(args, "full", False) and res["picks"]:
        import textwrap
        carddata, mana, kw = load_card_data(), load_mana(), load_keywords()
        print(f"\n── Full text of the {len(res['picks'])} pick(s) — grade adds from THIS ──")
        for p in res["picks"]:
            nl = p["name"].lower()
            cd = carddata.get(nl)
            tline = (cd["type"] if cd else "") or "?"
            text = (cd["text"] if cd else "") or ""
            cost, mv = (mana.get(nl) or (None, None))
            have = f"×{p['owned']}" if p["owned"] else "craft"
            print(f"\n• {p['name']}   [{tline}]"
                  + (f"  ·  MV {mv}" if mv is not None else "")
                  + f"  ·  {p['rarity'] or '?'} · {have} · fits {p['decks']} other deck(s)")
            card_kw = kw.get(nl) or []
            if card_kw:
                print(f"    ⌘ keywords: {', '.join(k.title() for k in card_kw)}")
            flags = read_flags(text, cost, card_kw)
            if flags:
                print(f"    ⚠ {' · '.join(flags)}")
            for para in (text or "(no oracle text on file)").split("\n"):
                for line in (textwrap.wrap(para, width=90) or [""]):
                    print(f"    {line}")
    return 0


# --- consistency / manabase probability model (hypergeometric) ------------- #
# Pure, deck-agnostic helpers behind `deck.py consistency`. They answer the two
# questions the diagnosis-only `mana` command couldn't: "how often do I actually
# cast this on curve" (#1, a Karsten-style cast-probability model) and "how often
# is my opening hand keepable / do I hit my land drops" (#2, a hypergeometric
# land model). Kept separate from any deck I/O so they're unit-testable.

def hypergeom_at_least(N, K, n, k):
    """P(drawing AT LEAST k of the K 'successes' when drawing n from a deck of N).
    N deck size, K successes in deck, n cards drawn, k successes wanted. Exact —
    sums the hypergeometric PMF over j∈[k, min(K,n)]."""
    if k <= 0:
        return 1.0
    if N <= 0 or K < k or n < k:
        return 0.0
    n = min(n, N)
    total = math.comb(N, n)
    if total == 0:
        return 0.0
    s = 0
    for j in range(k, min(K, n) + 1):
        s += math.comb(K, j) * math.comb(N - K, n - j)
    return s / total


def cards_seen(turn, on_play=True):
    """Cards seen by the START of your `turn` (after that turn's draw). Opening 7,
    +1 per turn drawn: on the play you skip turn 1's draw (7+turn-1), on the draw
    you don't (7+turn)."""
    return 7 + (turn - 1) + (0 if on_play else 1)


def cast_probability(N, sources, turn, pips, on_play=True):
    """P(having enough colored sources to pay `pips` by `turn`). `pips` is a strict
    {color: count} demand; `sources` is {color: land count producing it}. Per-color
    hypergeometric, multiplied across colors (Karsten's independence approximation).
    Hybrid pips are excluded by the caller — they're strictly easier, so the strict
    demand is the binding constraint."""
    seen = cards_seen(turn, on_play)
    p = 1.0
    for col, cnt in pips.items():
        if cnt <= 0:
            continue
        p *= hypergeom_at_least(N, sources.get(col, 0), seen, cnt)
    return p


def min_sources_for(N, turn, pip_count, target=0.90, on_play=True):
    """Fewest sources of ONE color to hit `target` P of having `pip_count` of them by
    `turn` — the Karsten "how many sources do I need" number. Returns N if even a full
    deck of them can't (impossible target)."""
    seen = cards_seen(turn, on_play)
    for src in range(0, N + 1):
        if hypergeom_at_least(N, src, seen, pip_count) >= target:
            return src
    return N


def opening_land_stats(N, lands, on_play=True):
    """Opening-hand + land-drop consistency for a deck of N with `lands` lands:
    keepable (2–5 lands in the opening 7), screw (0–1), flood (6–7), and P(≥n lands
    by turn n) for n=2,3,4 (land-drop consistency). All exact hypergeometric."""
    seven = math.comb(N, 7) if N >= 7 else 0

    def p7(k):  # P(exactly k lands in the opening 7)
        if not seven or lands < k or N - lands < 7 - k:
            return 0.0
        return math.comb(lands, k) * math.comb(N - lands, 7 - k) / seven

    keepable = sum(p7(k) for k in range(2, 6))
    screw = sum(p7(k) for k in range(0, 2))
    flood = sum(p7(k) for k in range(6, 8))
    return {"keepable": keepable, "screw": screw, "flood": flood,
            "hit2": hypergeom_at_least(N, lands, cards_seen(2, on_play), 2),
            "hit3": hypergeom_at_least(N, lands, cards_seen(3, on_play), 3),
            "hit4": hypergeom_at_least(N, lands, cards_seen(4, on_play), 4)}


def cmd_mana(args):
    """Hybrid-aware color requirements: which colors a deck STRICTLY needs."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}.")
        return 1
    by_key, by_name, _ = load_collection()
    meta, cards = parse_deck_file(d["path"])
    # COPY, not the memoized table itself: `fetch_missing_mana` MUTATES the dict it
    # is given, and `load_mana` is `@_file_memo`-cached — so live-fetched rows leaked
    # into a table every other caller shares. `_file_memo` rests the whole memo on
    # "every caller treats these tables as READ-ONLY … if you ever need to mutate
    # one, copy it first", and five call sites did not (broad-scan BS5-13). In the
    # Flask editor — one long-lived process — that made deck B's Stats tab compute
    # its curve from costs deck A's Mana tab had fetched, disagreeing with the CLI.
    mana = dict(load_mana())
    if not mana:
        eprint("No card-mana.csv found. Build it: python3 scripts/build_mana.py")
        return 1
    nonland = [n for q, n, s, c in cards if n.lower() not in BASICS]
    fetch_missing_mana(sorted(set(nonland)), mana)

    strict_pips = {c: 0 for c in "WUBRG"}
    cards_need = {c: 0 for c in "WUBRG"}
    hybrid_pips = {}
    hybrid_only = unknown = 0
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        row = by_key.get((n.lower(), s.lower(), c.lower())) or by_name.get(n.lower())
        if row and "Land" in _primary_type((row.get("Type") or "")):
            continue
        entry = mana.get(n.lower())
        if entry is None:
            unknown += q
            continue
        strict, hybrid = parse_pips(entry[0])
        if not entry[0]:  # no mana cost (nonbasic land not in library, or 0-cost)
            continue
        for col, cnt in strict.items():
            strict_pips[col] += cnt * q
        for col in strict:
            cards_need[col] += q
        for h in hybrid:
            hybrid_pips[h] = hybrid_pips.get(h, 0) + q
        if hybrid and not strict:
            hybrid_only += q

    print(f"Deck {d['id']}: {d['name'] or d['path']} — mana requirements (hybrid-aware)\n")
    print("Strict color requirements (must be paid with that color):")
    for c in "WUBRG":
        if cards_need[c]:
            note = _commitment(cards_need[c])
            print(f"  {c}  {strict_pips[c]:3} pips across {cards_need[c]:2} card(s)   {note}")
    if hybrid_pips:
        print("\nHybrid pips (payable with EITHER color — don't demand their own sources):")
        for h, n in sorted(hybrid_pips.items(), key=lambda kv: -kv[1]):
            print(f"  {'/'.join(sorted(h))}  {n} pip(s)")
    if hybrid_only:
        print(f"\n{hybrid_only} card(s) are hybrid-only — castable with any of their colors.")
    if unknown:
        print(f"\n{unknown} card(s) had no cost data (run build_mana.py to refresh).")

    # Color-source adequacy: count how many lands can PRODUCE each color, then flag
    # cards whose strict colored-pip demand looks thin against those sources — the
    # "wants UU but this is a U-splash deck" check the identity lint can't make.
    # ONE count (`deck_source_profile`, BS8-01): this used to be an inline copy that read
    # colour identity alone, so a "{T}: Add one mana of any color" land was zero sources
    # and the `△ Pip-intensive` flag below fired on manabases built to fix exactly that.
    # Mana dorks aren't counted, so read it as a review signal, not a hard failure.
    carddata = load_card_data()
    sources, nlands, _total, source_notes = deck_source_profile(cards, by_key, by_name, carddata)

    def _is_land(nl, s, c):
        row = by_key.get((nl, s.lower(), c.lower())) or by_name.get(nl)
        cd = carddata.get(nl)
        tline = (row.get("Type") if row else "") or (cd["type"] if cd else "")
        colid = (row.get("Color(s)") if row else "") or (cd.get("colors") if cd else "")
        return "Land" in _primary_type(tline), colid

    active = [c for c in "WUBRG" if sources[c] or cards_need[c]]
    if active:
        print("\nColor sources (lands producing each color):")
        print("  " + "   ".join(f"{c} {sources[c]}" for c in active) + f"   ({nlands} lands)")
        for line in format_source_notes(source_notes, indent="    "):
            print(line)
        thin, seen_t = [], set()
        for q, n, s, c in cards:
            nl = n.lower()
            if nl in BASICS or n in seen_t:
                continue
            land, _ = _is_land(nl, s, c)
            entry = mana.get(nl)
            if land or not (entry and entry[0]):
                continue
            strict, _hy = parse_pips(entry[0])
            for col, cnt in sorted(strict.items(), key=lambda kv: -kv[1]):
                if cnt >= 2 and sources[col] < 9:
                    thin.append((n, f"wants {col}{col} but only {sources[col]} {col} sources"))
                    seen_t.add(n)
                    break
                if cnt == 1 and sources[col] < 4:
                    thin.append((n, f"wants {col} but only {sources[col]} {col} source(s)"))
                    seen_t.add(n)
                    break
        if thin:
            print("△ Pip-intensive vs your sources (heuristic review — not a hard fail):")
            for n, why in thin:
                print(f"    {n} — {why}")

    # Castability lint: compare each card's real color needs against the deck's
    # declared colors (the `#: colors:` header). Only meaningful when declared.
    declared = _declared_colors(meta)
    if declared:
        uncastable, off_ident, _, intended = _castability(
            cards, declared, mana, load_card_data(), _uncastable_ok(meta))
        cols = "".join(sorted(declared))
        if intended:
            print(f"\n◆ Intentionally uncastable (`#: uncastable-ok:`) — reanimation "
                  "targets you never cast from hand:")
            for n, why in intended:
                print(f"    {n} — {why}")
        if uncastable:
            print(f"\n✗ Uncastable off the deck's {cols} colors "
                  "(a pip needs a color the deck can't produce):")
            for n, why in uncastable:
                print(f"    {n} — {why}")
        if off_ident:
            print(f"\n△ Castable, but color identity strays outside {cols} "
                  "(off-color ability, or a hybrid you'd pay on-color):")
            for n, why in off_ident:
                print(f"    {n} — {why}")
        if not uncastable and not off_ident:
            print(f"\nCastability: every nonland card fits the declared {cols} colors. ✓")
    return 0


def _commitment(n):
    if n <= 3:
        return "<- light splash"
    if n <= 8:
        return "<- secondary color"
    return "<- primary color"


# Labels `deck_source_profile` files a nonbasic land under, in the order they print.
_SOURCE_KINDS = (("any", "any colour, no extra cost"),
                 ("any-cost", "any colour for an extra mana (counted — a real source from the turn after it lands, a filter on curve)"),
                 ("fetch", "basic-land fetch (counted for each colour the deck runs a basic of)"),
                 ("restricted", "spend-only mana (NOT counted — read the restriction)"))


def deck_source_profile(cards, by_key, by_name, carddata, meta=None):
    """(sources{WUBRG:count}, nlands, total, notes) for a cards list — THE manabase count
    behind `mana`, `consistency`, `deck_color_sources` (and through it `pip_depth_warning`
    and the rationale audit's colour-source figures). One implementation, because three
    copies agreed with each other and were all wrong (BS8-01).

    Basics count by name. A nonbasic land counts by what its TEXT says it produces
    (`lib.land_production`): colours it adds freely, colours it adds for an extra mana
    ("{1}, {T}: Add one mana of any color" — counted, since the land IS a source of that
    colour from the turn after it lands, and labelled so a reader can discount it on
    curve), and a basic-land fetch, counted for each colour the deck runs a basic of.
    Spend-only mana ("Spend this mana only to cast a creature spell") is NOT counted and
    is reported instead — whether it is a source depends on what you are casting. Mana
    dorks are not lands and are never counted.

    `notes` maps each `_SOURCE_KINDS` label to a sorted [(qty, name)] list so a surface
    can print what the count is made of; `_deck_source_counts` drops it for callers that
    only want the numbers.
    """
    sources = {c: 0 for c in "WUBRG"}
    nlands = total = 0
    basics_present = set()
    for _q, n, _s, _c in cards:
        nl = n.lower()
        base = nl[len("snow-covered "):] if nl.startswith("snow-covered ") else nl
        if base in BASICS and BASIC_COLOR.get(base):
            basics_present.add(BASIC_COLOR[base])
    notes = {k: [] for k, _ in _SOURCE_KINDS}
    for q, n, s, c in cards:
        total += q
        nl = n.lower()
        base = nl[len("snow-covered "):] if nl.startswith("snow-covered ") else nl
        if base in BASICS:
            col = BASIC_COLOR.get(base)
            if col:
                sources[col] += q
            nlands += q
            continue
        row = by_key.get((nl, s.lower(), c.lower())) or by_name.get(nl)
        cd = carddata.get(nl)
        tline = (row.get("Type") if row else "") or (cd["type"] if cd else "")
        if "Land" not in _primary_type(tline):
            continue
        nlands += q
        colid = (row.get("Color(s)") if row else "") or (cd.get("colors") if cd else "")
        if not colid and meta and meta.get(nl):
            colid = "".join(sorted(meta[nl].get("colors") or ()))
        text = (cd.get("text") if cd else "") or (row.get("Card Text") if row else "") or ""
        prod = land_production(text, colid)
        counted = set(prod["free"]) | set(prod["conditional"])
        if prod["fetch"]:
            counted |= basics_present
            notes["fetch"].append((q, n))
        if prod["any"]:
            if set("WUBRG") <= prod["free"]:
                notes["any"].append((q, n))
            elif prod["conditional"]:
                notes["any-cost"].append((q, n))
            elif prod["restricted"]:
                notes["restricted"].append((q, n))
        elif prod["restricted"]:
            notes["restricted"].append((q, n))
        for col in counted:
            if col in sources:
                sources[col] += q
    for k in notes:
        notes[k].sort(key=lambda t: t[1])
    return sources, nlands, total, notes


def _deck_source_counts(cards, by_key, by_name, carddata):
    """(sources{WUBRG:count}, nlands, total) — `deck_source_profile` without the notes.
    Kept as the name `consistency` and the tests call; the count lives in one place."""
    sources, nlands, total, _notes = deck_source_profile(cards, by_key, by_name, carddata)
    return sources, nlands, total


def format_source_notes(notes, indent="  "):
    """Lines describing what a source count is made of — one per non-empty
    `_SOURCE_KINDS` label, so `mana` and `consistency` print the same explanation."""
    out = []
    for key, label in _SOURCE_KINDS:
        rows = notes.get(key) or []
        if rows:
            out.append(f"{indent}{sum(q for q, _ in rows)} {label}: "
                       + ", ".join(f"{q}× {n}" for q, n in rows))
    return out


_TAPLAND_RE = re.compile(r"enters(?: the battlefield)? tapped", re.I)
_TAPLAND_COND_RE = re.compile(r"enters(?: the battlefield)? tapped[^.\n]*\b(unless|if )", re.I)


def tapland_profile(cards, carddata):
    """(unconditional, conditional, nonbasic_land_total) — each a sorted [(qty, name)].

    REPORT-ONLY tempo context for `consistency`, which prices color ACCESS and is
    structurally blind to the turn a tapland costs: the 2026-08-26 deck-68b land pass
    raised every cast-on-curve figure while taking the deck to 7 unconditional
    taplands of 11 nonbasics, and the model's numbers moved only in the direction
    that looked good. A conditional tapland (\"unless…\") is split out rather than
    scored — whether its condition helps EARLY (when tempo matters) is a text read,
    e.g. Etched Cornfield's \"unless a player has 13 or less life\" is usually tapped
    exactly when you want it untapped. Never feeds a score (the G-25/G-60 rule:
    a new term silently re-grades)."""
    uncond, cond, total = [], [], 0
    for q, n, _s, _c in cards:
        row = carddata.get((n or "").lower()) or {}
        typ = row.get("type") or ""
        if "Land" not in typ or _ms_key(n) in BASICS or n in BASICS:
            continue
        # front-face read (G-63): a back-face land is not a land you play from hand
        if "//" in typ and not typ.split("//")[0].strip().startswith(("Land", "Legendary Land", "Basic Land")):
            continue
        total += q
        text = row.get("text") or ""
        if _TAPLAND_COND_RE.search(text):
            cond.append((q, n))
        elif _TAPLAND_RE.search(text):
            uncond.append((q, n))
    return sorted(uncond, key=lambda t: t[1]), sorted(cond, key=lambda t: t[1]), total


def cmd_consistency(args):
    """Manabase + opening-hand CONSISTENCY (#1/#2): the probability layer `mana` lacks.
    Given the deck's land count and per-color sources, model P(keepable opening hand),
    screw/flood, land-drop consistency, and — per card — P(casting on curve) with a
    Karsten-style source recommendation for the ones that come up short. Diagnosis with
    numbers, not vibes: `mana` says 'thin', this says '62% on turn 3, want +2 sources'."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    by_key, by_name, _ = load_collection()
    meta, cards = parse_deck_file(d["path"])
    # COPY, not the memoized table itself: `fetch_missing_mana` MUTATES the dict it
    # is given, and `load_mana` is `@_file_memo`-cached — so live-fetched rows leaked
    # into a table every other caller shares. `_file_memo` rests the whole memo on
    # "every caller treats these tables as READ-ONLY … if you ever need to mutate
    # one, copy it first", and five call sites did not (broad-scan BS5-13). In the
    # Flask editor — one long-lived process — that made deck B's Stats tab compute
    # its curve from costs deck A's Mana tab had fetched, disagreeing with the CLI.
    mana = dict(load_mana())
    if not mana:
        eprint("No card-mana.csv found. Build it: python3 scripts/build_mana.py")
        return 1
    carddata = load_card_data()
    nonland = [n for q, n, s, c in cards if n.lower() not in BASICS]
    fetch_missing_mana(sorted(set(nonland)), mana)

    sources, nlands, total, source_notes = deck_source_profile(cards, by_key, by_name, carddata)
    on_play = not getattr(args, "on_draw", False)
    # `or 0.90` made `--target 0` silently mean 0.90, and nothing range-checked the
    # value: `--target 90` (the obvious mis-read of "as a fraction") made
    # min_sources_for return N for every card and printed an unreachable source count
    # for the whole deck (broad-scan Batch G).
    target = getattr(args, "target", None)
    target = 0.90 if target is None else float(target)
    if not (0.0 < target < 1.0):
        eprint(f"--target must be a fraction strictly between 0 and 1 (got {target}); "
               f"e.g. 0.90 for 'castable on curve 90% of the time'.")
        return 2
    N = total or 60
    coin = "on the play" if on_play else "on the draw"

    print(f"Deck {d['id']}: {d['name'] or d['path']} — consistency ({N}-card deck, {coin})\n")

    # #2 — opening hand + land drops.
    ls = opening_land_stats(N, nlands, on_play)
    print(f"Lands: {nlands}/{N}  ({100*nlands/N:.0f}% of the deck)")
    print("Opening hand (7 cards):")
    print(f"  keepable (2–5 lands) : {100*ls['keepable']:5.1f}%")
    print(f"  mana screw (0–1)     : {100*ls['screw']:5.1f}%     "
          f"flood (6–7): {100*ls['flood']:4.1f}%")
    print("Land-drop consistency (P of ≥N lands by turn N):")
    print(f"  turn 2: {100*ls['hit2']:5.1f}%   turn 3: {100*ls['hit3']:5.1f}%   "
          f"turn 4: {100*ls['hit4']:5.1f}%")
    _tl_u, _tl_c, _tl_n = tapland_profile(cards, load_card_data())
    if _tl_u or _tl_c:
        _tapped = sum(q for q, _ in _tl_u) + sum(q for q, _ in _tl_c)
        bits = []
        if _tl_u:
            bits.append(f"{sum(q for q, _ in _tl_u)} unconditional: "
                        + ", ".join(n for _, n in _tl_u))
        if _tl_c:
            bits.append("conditional: " + ", ".join(n for _, n in _tl_c))
        print(f"  ⓘ taplands: {_tapped} of {_tl_n} nonbasic land(s) enter tapped "
              f"({'; '.join(bits)}) — every figure here prices color ACCESS, not the "
              f"turn a tapland costs; that tempo is invisible to this model.")
    # A gentle land-count read — the classic 17-source floor is deck-dependent, so flag
    # only clear extremes rather than prescribe a number.
    if ls["keepable"] < 0.85:
        # Both directions were reachable, and on a low-curve list BOTH trip. Deck 52 at 24
        # lands read "consider FEWER"; the same list at 23 read "consider MORE", at a WORSE
        # keepable (82.5%) with three cards falling under 90% on curve. An advisory that
        # reverses and can be satisfied by nothing is worse than silence, so check the
        # neighbour before prescribing: if moving one land the suggested way makes keepable
        # worse too, say the threshold is unreachable for this shape and point at the
        # measurement that CAN be optimised.
        want = "more" if nlands < N * 0.40 else "fewer"
        step = 1 if want == "more" else -1
        alt = _keepable_at(nlands + step, N)
        if alt is not None and alt <= ls["keepable"]:
            print(f"  △ keepable {100*ls['keepable']:.0f}% is low, and moving to "
                  f"{nlands + step} lands does not improve it ({100*alt:.0f}%) — this curve "
                  "cannot clear the threshold at any land count. Optimise on the "
                  "cast-on-curve table below instead.")
        else:
            print(f"  △ keepable {100*ls['keepable']:.0f}% is low — consider {want} lands "
                  f"(most 60-card decks run 23–26).")

    # Color sources.
    active = [c for c in "WUBRG" if sources[c]]
    # A "splash" color has so few sources that a card demanding it on curve is
    # effectively a late-game card, not an on-curve one — so the per-card
    # recommendation below reframes as "cast later or cut" instead of printing an
    # impractical land count (a {B}{R} 2-drop off 1 red source wants ~15 R sources).
    SPLASH_MAX = 3
    splash = [c for c in active if sources[c] <= SPLASH_MAX]
    if active:
        print("\nColor sources (lands producing each color):")
        print("  " + "   ".join(f"{c} {sources[c]}" for c in active))
        for line in format_source_notes(source_notes, indent="    "):
            print(line)
        if splash:
            print("  splash (≤%d sources): " % SPLASH_MAX
                  + ", ".join(f"{c} ({sources[c]})" for c in splash)
                  + " — a card needing one of these on curve reads low below; treat it as a "
                    "late-game splash (cast when you've drawn the source), not a curve play.")

    # #1 — per-card cast probability on curve. Cast turn = the card's MV (min 1),
    # capped so a 7-drop isn't judged as if cast on turn 7 verbatim (you've usually
    # stabilized your colors by ~turn 5). Strict pips only; hybrids are easier and
    # excluded (they don't demand their own sources — same rule `mana` uses).
    CAST_CAP = 5
    rows = []
    seen = set()
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS or nl in seen:
            continue
        row = by_key.get((nl, s.lower(), c.lower())) or by_name.get(nl)
        if row and "Land" in _primary_type((row.get("Type") or "")):
            continue
        entry = mana.get(nl)
        if not entry or not entry[0]:
            continue
        strict, _hy = parse_pips(entry[0])
        if not strict:
            continue
        seen.add(nl)
        mv = entry[1] if entry[1] is not None else sum(strict.values())
        turn = max(1, min(int(mv) if mv else 1, CAST_CAP))
        p = cast_probability(N, sources, turn, strict, on_play)
        # The BINDING single-color demand drives the fix recommendation — the color
        # whose per-color hypergeometric term is LOWEST, not the one with the most
        # pips: a {B}{B}{R} cost off B=16/R=2 is dragged down by the one-pip R
        # splash, and keying on pip count pointed the → note (and the splash
        # reframing) at B, prescribing sources for the color that wasn't the
        # problem. Tiebreak: more pips, then name (a total order, G-54).
        seen_by_turn = cards_seen(turn, on_play)
        worst_col = min(strict, key=lambda col: (
            hypergeom_at_least(N, sources.get(col, 0), seen_by_turn, strict[col]),
            -strict[col], col))
        need = min_sources_for(N, turn, strict[worst_col], target, on_play)
        rows.append((p, n, turn, strict, worst_col, need))

    rows.sort(key=lambda r: r[0])
    below = [r for r in rows if r[0] < target]
    print(f"\nCast-on-curve probability (turn = mana value, capped at {CAST_CAP}; "
          f"target {100*target:.0f}%):")
    if not rows:
        print("  (no colored-pip cards with cost data)")
    else:
        show = below if below else rows[:5]
        if not below:
            print(f"  ✓ every colored card casts on curve at ≥{100*target:.0f}% — "
                  "manabase supports the deck. Lowest 5:")
        for p, n, turn, strict, worst_col, need in show:
            pipstr = "".join(f"{{{col}}}" * cnt for col, cnt in sorted(strict.items()))
            have_col = sources.get(worst_col, 0)
            flag = ""
            if p < target and need > have_col:
                if have_col <= SPLASH_MAX:
                    # Genuine splash: too few sources to ever be on-curve at this turn.
                    # Reframe as cast-late/cut rather than print an absurd land count
                    # (a {B}{R} 2-drop off 1 red source "wanting" 15 R sources).
                    flag = (f"   → {worst_col} is a {have_col}-source splash — cast it late "
                            f"(once you've drawn a source) or cut it; don't chase "
                            f"{100*target:.0f}% on curve")
                elif need > nlands:
                    # A main color, but a color-hungry EARLY cost (e.g. {B}{B} on T2) that no
                    # realistic land base guarantees on time — say so instead of "+N sources".
                    flag = (f"   → color-hungry: {100*target:.0f}% at T{turn} would need {need} "
                            f"{worst_col} sources (> the deck's {nlands} lands) — expect it a "
                            f"turn or two later than T{turn}")
                else:
                    flag = (f"   → want {need} {worst_col} sources "
                            f"(have {have_col}, +{need - have_col})")
            print(f"  {100*p:5.1f}%  T{turn}  {pipstr:10} {n[:30]:30}{flag}")
        if below:
            print(f"\n  {len(below)} card(s) below {100*target:.0f}% on curve — the → note is the "
                  f"Karsten source count to reach target, a splash flag for a thin (≤{SPLASH_MAX}-source) "
                  "color (cast late or cut), or a color-hungry flag for an early double pip.")
    print("\nModel: hypergeometric (exact); per-color independence for multi-color costs "
          "(a mild over-estimate), hybrids excluded as non-binding. A planning aid, not a "
          "guarantee — mulligans, scry, and card draw all shift the real numbers.")
    return 0


# --- flex / suggested swaps ------------------------------------------------- #
def _parse_flex_line(s):
    """Parse one stripped line into a flex entry dict, or None if it isn't a
    (non-empty) `#~` line.  Format:  #~ -Out card | +In card | reason"""
    if not s.startswith("#~"):
        return None
    e = {"out": "", "in": "", "note": ""}
    for col in (c.strip() for c in s[2:].split("|")):
        if col.startswith("-"):
            e["out"] = col[1:].strip()
        elif col.startswith("+"):
            e["in"] = col[1:].strip()
        elif col:
            e["note"] = (e["note"] + "  " + col).strip()
    return e if (e["out"] or e["in"] or e["note"]) else None


def parse_flex(path):
    """Return the deck's flex suggestions from `#~` lines.

    A flex line is a comment (so it never counts toward the 60 or reaches Arena
    import), machine-readable as:  #~ -Out card | +In card | reason
    Any of the three fields may be omitted; a lone free-text field is a note.
    """
    entries = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            e = _parse_flex_line(raw.strip())
            if e:
                entries.append(e)
    return entries


def flex_staleness(path):
    """Flex lines that no longer describe a possible change → [(out, in, why)].

    A `#~` line rots silently. `swap --apply` retires only the lines invalidated by
    the swap it is PERFORMING, and `tier --audit-rationale` reads `#: tier:` /
    `#: archetype:` prose, never the flex block — so a line can sit for rounds
    proposing a cut that already happened. Found in practice on deck 42a, where an
    Azula line still named Prideful Parent two swaps after it left, and again where an
    interaction fix pointed at a card three swaps stale.

    BOTH HALVES OF THE LINE ROT, and only the `-Out` half used to be checked. Deck 28
    carried `-Triumphant Chomp | +Bushwhack` while Bushwhack was already maindecked —
    a line proposing an add the deck runs, printed by `deck.py flex` without comment
    (2026-08-11). This function's own docstring had encoded the gap as a rule ("a line
    with no -Out … is never stale — there is nothing to check it against"); there is,
    namely whether the deck already runs the `+In`. G-04 documents the stale-CUT rot;
    this is its mirror.

    A pure NOTE (no `-Out` and no `+In`) is still never stale — that one really has
    nothing to check against.
    """
    _, cards = parse_deck_file(path)
    # Lowercased on both sides — every other name join here is case-insensitive
    # (audit F4's rule), and this one was exact-case, so a flex line typed in
    # different case from its deck line read permanently STALE (broad-scan batch 5).
    have = {n.lower() for _q, n, _s, _c in cards}
    have |= {n.split(" // ")[0] for n in list(have)}

    def _held(nm):
        nl = nm.lower()
        return nl in have or nl.split(" // ")[0] in have

    out = []
    for e in parse_flex(path):
        cut = (e.get("out") or "").strip()
        add = (e.get("in") or "").strip()
        if cut and not _held(cut):
            out.append((cut, add, "the -Out card is no longer in the deck"))
        elif add and add.lower() not in BASICS and _held(add):
            # BASICS are exempt: they are unlimited in Arena, so "+Island" against a
            # deck that already runs Islands is a proposal for one MORE land, not a
            # duplicate. Deck 51's `-Krang | +Island | THE 25TH LAND` was the single
            # false positive in this check's first roster sweep (7 of 8 were real).
            # Reported on the ADD side only when the CUT side is still live (or
            # absent), so one rotten line yields one row rather than two.
            out.append((cut, add, "the +In card is already in the deck"))
    return out


def header_card_staleness(path):
    """`#: protect:` / `#: uncastable-ok:` entries naming a card the deck does NOT run.

    → [(header, name)].

    Found on deck 26b (2026-08-07): its `#: protect:` header named Summon: Bahamut, a
    card that deck has never run — it went to variant 48a in the pivot the deck's own
    notes record. Two things were wrong and neither was visible:

      1. The entry protected NOTHING. `cuts` hard-excludes protected cards from its
         ranking, so a name that matches no card silently drops out of the mechanism it
         was written for, and the card it was meant to shield (if the name were a typo
         rather than a leftover) stays cuttable.
      2. It inflated a number a HUMAN reads. The zero-protection flag in `stats` and
         `tier` prints "`#: protect:` names N build-around card(s)", so 26b reported
         five build-arounds against a real four — in the exact sentence used to argue
         the deck's tier cap.

    NO GATE COULD SEE IT. `check_all` validates deck LINES (INV-04) and the rationale
    audit reads `#: tier:` / `#: archetype:` PROSE; a card-name list in a third header
    was checked by nothing, which is this project's recurring shape — a capability that
    exists and is never reached. Roster-wide and automatic now.

    `#: uncastable-ok:` is swept too, and is the more dangerous of the pair: it SUPPRESSES
    a castability failure, so a stale entry there is a disabled check rather than a
    disabled boost. Advisory either way — pruning a header is a human editorial call.
    """
    meta, cards = parse_deck_file(path)
    have = {_ms_key(n) for _q, n, _s, _c in cards}
    out = []
    for header, reader in (("protect", _protected), ("uncastable-ok", _uncastable_ok)):
        for name in sorted(reader(meta)):
            if _ms_key(name) not in have:
                out.append((header, name))
    return out


def cmd_flex(args):
    """Show a deck's flex suggestions, enriching the +In card with cost / owned /
    rarity so you can see what each swap would take."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    entries = parse_flex(d["path"])
    print(f"Deck {d['id']}: {d['name'] or d['id']} — flex / suggested swaps")
    if not entries:
        print("  (none yet — add '#~ -Out card | +In card | reason' lines to the deck file.)")
        return 0
    mana = load_mana()
    rar = load_rarities()
    _, _, qty = load_collection()
    print("-" * 62)
    for e in entries:
        left = f"− {e['out']}" if e["out"] else ""
        right = ""
        if e["in"]:
            m = mana.get(e["in"].lower())
            cost = m[0] if (m and m[0]) else ""
            have, _ = owned(qty, e["in"])
            r = rar.get(e["in"].lower(), "")
            meta = " ".join(x for x in [cost, r, (f"×{have}" if have > 0 else "craft")] if x)
            right = f"+ {e['in']}" + (f"  ({meta})" if meta else "")
        if left and right:
            print(f"  {left}   →   {right}")
        elif left or right:
            print(f"  {left or right}")
        if e["note"]:
            print(f"      {e['note']}")
    stale = flex_staleness(d["path"])
    if stale:
        print("\n  \u26a0 STALE flex line(s) — they no longer describe a possible change:")
        for cut, add, why in stale:
            label = "  \u2192  ".join(x for x in ((f"\u2212{cut}" if cut else ""),
                                              (f"+{add}" if add else "")) if x)
            print(f"      {label}   ({why} \u2014 retarget or retire the line)")
    figs = note_figure_staleness(d)
    if figs:
        print("\n  \u26a0 STALE figure(s) in `#~ note:` prose "
              "\u2014 the live vector disagrees:")
        for note, key, quoted, actual in figs:
            print(f"      {key} quoted as {quoted}, live {actual}")
            print(f"        \u2026{' '.join(note.split())[:110]}")
    return 0


# --- swap preview / apply (and flex promotion) ------------------------------ #
def _printing_of(name):
    """Best-known `(display_name, set, collector#)` for a card name: an owned library
    printing first (so the added line matches something you have), else any known
    printing. `(name, '', '')` if unknown — a bare '1 Name' line still parses/checks.

    MATCHES A DFC BY ITS FRONT FACE TOO, and returns the CANONICAL display name. The
    CSVs key a two-faced card under its full `Front // Back` name, so an exact-only
    lookup for the front name found nothing and `swap --apply` wrote a bare `1 Runescale
    Stormbrood` with no printing. INV-04 passed and `legal` reported clean, because a
    bare line parses — but the line is not a valid Arena import, so the failure surfaced
    only when a human tried to paste the deck. Returning the display name as well is what
    stops the file recording the front-face shorthand instead of the real card name."""
    nl = name.strip().lower()
    best = (name.strip(), "", "")
    # The CANONICAL display is the full `Front // Back`, and it must survive an OWNED
    # printing that is filed under the bare front name. reconcile_crafts.py stores a
    # crafted DFC front-name-only BY DESIGN (G-10/G-63), so the moment you own one the
    # owned-row branch below started returning the shorthand and this function stopped
    # doing the one thing its docstring promises. Caught by
    # TestPrintingOfDFC::test_the_swap_writes_the_canonical_name after a 2026-08-27
    # ingest, not by any gate on the deck files -- the 127 roster lines already written
    # under a bare front name are the long-standing convention and parse fine, so
    # nothing downstream complains. Resolve the printing and the DISPLAY separately.
    canon = ""
    for path, owned_pref in ((DEFAULT_CSV, True), (POOL_CSV, False)):
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                disp = (r.get("Card Name") or "").strip()
                dl = disp.lower()
                if dl != nl and dl.split(" // ")[0] != nl:
                    continue
                setc = (r.get("Set Code") or "").strip()
                cn = (r.get("Collector #") or "").strip()
                if not setc:
                    continue
                if " // " in disp and not canon:
                    canon = disp
                if owned_pref:
                    try:
                        q = int(r.get("Quantity Owned") or 0)
                    except ValueError:
                        q = 0
                    if q > 0:
                        # printing from the owned row, display from the canonical name
                        owned = (disp, setc, cn)
                        if canon:
                            return (canon, setc, cn)
                        best_owned = owned
                        for r2 in _pool_rows_for(nl):
                            d2 = (r2.get("Card Name") or "").strip()
                            if " // " in d2:
                                return (d2, setc, cn)
                        return best_owned
                if not best[1]:
                    best = (disp, setc, cn)
    if canon and best[1]:
        return (canon, best[1], best[2])
    return best


def _pool_rows_for(nl):
    """Pool rows whose name equals `nl` or fronts to it. Only reached when an OWNED
    library row resolved first and we still need the canonical `Front // Back` display
    (the library files a crafted DFC under its front name by design)."""
    if not os.path.exists(POOL_CSV):
        return []
    out = []
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            d = (r.get("Card Name") or "").strip().lower()
            if d == nl or d.split(" // ")[0] == nl:
                out.append(r)
    return out


def _card_line_name(line):
    """If a raw line is a card line, return its parsed name; else None. Comment
    lines (`#`, `#:`, `#~`) split to empty and return None."""
    body = line.split("#", 1)[0].strip()
    if not body:
        return None
    m = LINE_RE.match(body)
    return m.group(2).strip() if m else None


def _deck_summary(cards, carddata, mana):
    """Small before/after fingerprint for a cards list: totals, creature count,
    average nonland MV, and color identity (excluding basics/lands)."""
    total = crea = mv_sum = mv_n = 0
    colors = set()
    for q, n, s, c in cards:
        total += q
        nl = n.lower()
        if nl in BASICS:
            continue
        cd = carddata.get(nl)
        tline = (cd["type"] if cd else "") or ""
        if "Land" in _primary_type(tline):
            continue
        # FRONT face (G-63): a whole-line scan counts a DFC whose BACK is a creature,
        # while `deck_quality_vector` / `deck_shape` use `_primary_type`. Two surfaces
        # disagreeing on one count (BS4-34).
        if "Creature" in _primary_type(tline):
            crea += q
        col = (cd["colors"] if cd else "") or ""
        if col.lower() != "colorless":
            colors |= {ch for ch in col.upper() if ch in "WUBRG"}
        entry = mana.get(nl)
        if entry and entry[1] is not None:
            mv_sum += entry[1] * q
            mv_n += q
    return {"total": total, "creatures": crea,
            "avg_mv": (mv_sum / mv_n if mv_n else 0.0), "colors": colors}


def _cards_after_swap(cards, cut, add, add_printing):
    """Return the cards list with one copy of `cut` replaced by `add`, or None
    if `cut` isn't present. If `add` is already in the deck, its existing line is
    bumped by one rather than adding a second line for the same card — matched on
    `_ms_key` (front face), because `_do_swap` canonicalizes the add to the pool's
    full `Front // Back` name while the deck may store the front-face spelling: an
    exact-name match missed that line and split the card's count across two
    spellings, which `legality_report`'s copy counter then couldn't sum
    (broad-scan BS-05). The existing line's own spelling is kept.

    The CUT side matches on `_ms_key` too (broad-scan BS2-21): it was exact-name while
    the add side was front-face aware, so `swap 51 --cut "Mirror Room"` refused with
    "'Mirror Room' is not in deck 51" for a card the deck stores as
    `Mirror Room // Fractured Realm` — the spelling `cuts`, `card.py` and G-02's own
    worked example all use. G-63: key every name JOIN on `_ms_key`."""
    out, removed = [], False
    cut_key = _ms_key(cut)
    for (q, n, s, c) in cards:
        if not removed and _ms_key(n) == cut_key:
            if q > 1:
                out.append((q - 1, n, s, c))
            removed = True
            continue
        out.append((q, n, s, c))
    if not removed:
        return None
    add_key = _ms_key(add)
    for i, (q, n, s, c) in enumerate(out):
        if _ms_key(n) == add_key:
            out[i] = (q + 1, n, s, c)
            break
    else:
        out.append((1, add.strip(), add_printing[0], add_printing[1]))
    return out


# Section comments a swap can INHERIT and thereby falsify. The add takes the cut's line
# slot, so it lands under whatever `# ...` header preceded the cut — which is how
# Broodguard Elite (a counter battery) ended up filed under `# Card advantage`, the
# section Kiora had occupied. Harmless to the tooling, but the file then lies to the
# next reader, and these files are read far more often than they're parsed.
#
# Only sections whose meaning is UNAMBIGUOUS are checked. "# Counter DOUBLERS" means
# +1/+1 counters, not counterspells, and "# Threats" / "# Creatures" / "# Payoff" are
# too broad to contradict — a false warning on every swap would train the reader to
# ignore the real ones.
_SECTION_EXPECTATIONS = [
    (re.compile(r"card advantage|card draw", re.I), {"Card advantage"}),
    (re.compile(r"\bremoval\b|\binteraction\b|counterspell", re.I),
     {"Removal (spot)", "Sweeper", "Counter"}),
    (re.compile(r"\bramp\b|\bfixing\b|\bdorks?\b", re.I), {"Ramp / fixing"}),
]


def section_mismatch(lines, idx, add_name, carddata):
    """A warning string when the card now sitting at `lines[idx]` doesn't do what its
    enclosing `# section` comment claims, else None. Advisory only — it never edits the
    file, and it stays silent for ambiguous or absent section headers."""
    header = None
    for j in range(idx - 1, -1, -1):
        ln = lines[j].strip()
        if _card_line_name(lines[j]):
            continue                      # another card in the same section
        if ln.startswith("#:") or ln.startswith("#~") or not ln:
            continue                      # metadata / flex / blank
        if ln.startswith("#"):
            header = ln.lstrip("# ").strip()
            break
    if not header:
        return None
    cd = carddata.get((add_name or "").strip().lower())
    if not cd:
        return None
    roles = classify_roles(cd.get("text") or "")
    for rx, expected in _SECTION_EXPECTATIONS:
        if not rx.search(header):
            continue
        if roles & expected:
            return None
        if roles:
            # High confidence: we know what the card does, and it isn't this.
            return (f"{add_name} now sits under `# {header}` (inherited from the cut "
                    f"card's slot) but classifies as {', '.join(sorted(roles))} — move "
                    f"the line or retitle the section so the file doesn't mislead.")
        # Low confidence: the classifier found NO role. This session established that
        # "no role" often means a lexicon gap rather than a weak card, so this is
        # phrased as a prompt to look, not as an assertion that the card is misfiled.
        return (f"{add_name} now sits under `# {header}` (inherited from the cut card's "
                f"slot); nothing in its text matched a functional role, so verify the "
                f"section still describes it.")
    return None


def _section_headers(lines):
    """[(index, header_text)] for the `# section` comments that group card lines.
    Metadata (`#:`) and flex (`#~`) lines are not sections."""
    out = []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("#") and not s.startswith("#:") and not s.startswith("#~"):
            out.append((i, s.lstrip("# ").strip()))
    return out


def _relocate_card_line(lines, card_name, needle):
    """Move `card_name`'s line under the section whose header contains `needle`,
    preserving the line VERBATIM. Returns new lines; raises ValueError if the card or
    the section is missing or ambiguous.

    This exists because of the bug the WARNING caused. `section_mismatch` correctly
    flags an add that inherited the cut card's `# section`, but the only way to act on
    it was to hand-edit the file — and hand-editing deck lines is exactly what G-65
    forbids: relocating four lines that way in one session produced two invented
    collector numbers (`(HOB) 26` for a real 24, `(HOB) 21` for a real 19), caught only
    because `resolve --check` happened to be run afterwards. An advisory that can only
    be resolved by a forbidden edit is a hazard, not a warning. Moving the exact line
    text keeps the printing fields untouched by construction."""
    # `_ms_key` BOTH sides (G-63), not raw `.lower()`. `_swap_edit_lines` — the function
    # that just wrote the line this one is asked to move — matches on `_ms_key` precisely
    # because a card is stored under either face spelling (59 deck lines carry a full
    # `Front // Back` name). Its two siblings in the same code path did not, so when the
    # add already had a line under the OTHER spelling the raw comparison found zero
    # matches and this raised — and because the relocation runs inside `_do_swap`'s write
    # `try`, that aborted the ENTIRE swap with a message reading "appears on 0 card
    # line(s)" about a card the deck demonstrably holds (broad-scan S1-02, reproduced
    # against deck 53: `_relocate_card_line(lines, "Funeral Room", "Lands")` against a
    # file storing `Funeral Room // Awakening Hall`).
    key = _ms_key(card_name or "")
    idxs = [i for i, ln in enumerate(lines)
            if _ms_key(_card_line_name(ln) or "") == key]
    if len(idxs) != 1:
        raise ValueError(f"{card_name!r} appears on {len(idxs)} card line(s) — expected "
                         "exactly one to move.")
    src = idxs[0]
    heads = _section_headers(lines)
    hits = [(i, h) for i, h in heads if needle.strip().lower() in h.lower()]
    if not hits:
        avail = "; ".join(h for _i, h in heads) or "(none)"
        raise ValueError(f"no `# section` header contains {needle!r}. Headers: {avail}")
    if len(hits) > 1:
        raise ValueError(f"{needle!r} matches {len(hits)} headers "
                         f"({'; '.join(h for _i, h in hits)}) — be more specific.")
    hidx = hits[0][0]
    # End of that section's card block: the last card line before the next header.
    nxt = next((i for i, _h in heads if i > hidx), len(lines))
    last = max((i for i in range(hidx + 1, min(nxt, len(lines)))
                if _card_line_name(lines[i])), default=hidx)
    if hidx < src <= last:
        return list(lines)                      # already in the target section
    line = lines[src]
    rest = lines[:src] + lines[src + 1:]
    # Re-find the insertion point in the shortened list.
    dest = last - 1 if src < last else last
    return rest[:dest + 1] + [line] + rest[dest + 1:]


def cmd_move(args):
    """Relocate ONE card line under a different `# section` header, VERBATIM.

    The mechanical form of the edit G-65 forbids doing by hand, available OUTSIDE a
    swap. `swap --section` covers relocation only while a real swap is happening;
    moving an EXISTING line used to take a swap-out/swap-in pair, which wrote the
    pair to recommendations.csv as if cutting the card you had just added were a
    decision — four such rows landed in one 2026-08-27 session (G-56 warned about
    exactly this shape). A relocation is not a decision, so this command writes NO
    ledger row. Dry-run by default; `--apply` writes with a .bak and the same
    total-preserving guard the swap path uses."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    with open(d["path"], encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    _meta, cards = parse_deck_file(d["path"])
    total = sum(q for q, _n, _s, _c in cards)
    key = _ms_key(args.card or "")
    src = next((i for i, ln in enumerate(lines)
                if _ms_key(_card_line_name(ln) or "") == key), None)
    cur = "(no section)"
    if src is not None:
        for i in range(src, -1, -1):
            if lines[i].startswith("# ") and not lines[i].startswith("#:"):
                cur = lines[i].lstrip("# ").strip()
                break
    try:
        new_lines = _relocate_card_line(lines, args.card, args.section)
    except ValueError as e:
        eprint(f"Not moved: {e}")
        return 1
    if new_lines == lines:
        print(f"{args.card!r} is already under a section matching {args.section!r} — "
              "nothing to do.")
        return 0
    print(f"Move {args.card!r}: `# {cur}` → the header matching {args.section!r} "
          "(line kept verbatim, printing fields untouched).")
    if not args.apply:
        print("(dry run — pass --apply to write the change with a .bak)")
        return 0
    try:
        bak = _safe_write_lines(d["path"], new_lines, total)
    except ValueError as e:
        eprint(f"Not saved: {e}")
        return 1
    print(f"Applied. Wrote {os.path.relpath(d['path'], REPO_ROOT)} "
          f"(backup: {os.path.basename(bak)}).")
    print("No recommendations.csv row — a relocation is not a decision (G-56).")
    return 0


def _line_comment(ln):
    """The trailing inline `# …` comment on a card line, or '' — so a line rewrite
    (quantity bump/decrement here, `reconcile_lines`) re-attaches it instead of
    silently deleting a human note. The parser has always ACCEPTED inline comments;
    every rebuild dropped them (broad-scan batch 5; latent — no current deck file
    carries one)."""
    i = ln.find("#")
    return ("   " + ln[i:].rstrip()) if i >= 0 else ""


def _swap_edit_lines(lines, cut, add, add_printing, drop_flex=None):
    """Apply the swap to raw file lines: -1 copy of `cut` (removed if it was a
    singleton, else decremented) with the `add` line taking its slot; optionally
    drop the flex line matching `drop_flex` (an entry dict). Raises ValueError if
    `cut` isn't a card line."""
    out = list(lines)
    # `_ms_key` both sides (BS2-21): the cut may arrive as either face-spelling of a
    # line stored the other way; exact-name matching refused a front-named cut of a
    # full-name-stored card while `_cards_after_swap` (fixed for the same reason)
    # accepted it — the two halves of one swap disagreeing about whether the card
    # exists.
    ci = next((i for i, ln in enumerate(out)
               if _ms_key(_card_line_name(ln) or "") == _ms_key(cut)), None)
    if ci is None:
        raise ValueError(f"{cut!r} is not a card line in this deck.")
    m = LINE_RE.match(out[ci].split("#", 1)[0].strip())
    qty = int(m.group(1))
    setc, cn = add_printing
    add_line = f"1 {add.strip()}"
    if setc:
        add_line += f" ({setc})" + (f" {cn}" if cn else "")

    # If `add` is already a line in the deck, bump that line by one instead of
    # writing a second line for the same card (which would split its count).
    # Matched on `_ms_key` (front face), mirroring `_cards_after_swap`: the add
    # arrives canonicalized to the pool's full `Front // Back` name while the deck
    # line may store the front-face spelling (broad-scan BS-05). The existing
    # line keeps its own spelling — the rebuild below reuses its matched groups.
    ai = next((i for i, ln in enumerate(out)
               if _ms_key(_card_line_name(ln)) == _ms_key(add)), None)
    if ai is not None:
        am = LINE_RE.match(out[ai].split("#", 1)[0].strip())
        a_indent = out[ai][:len(out[ai]) - len(out[ai].lstrip())]
        a_rebuilt = f"{a_indent}{int(am.group(1)) + 1} {am.group(2).strip()}"
        if am.group(3):
            a_rebuilt += f" ({am.group(3).strip()})" + (f" {am.group(4).strip()}" if am.group(4) else "")
        out[ai] = a_rebuilt + _line_comment(out[ai])
        if qty > 1:
            indent = out[ci][:len(out[ci]) - len(out[ci].lstrip())]
            rebuilt = f"{indent}{qty - 1} {m.group(2).strip()}"
            if m.group(3):
                rebuilt += f" ({m.group(3).strip()})" + (f" {m.group(4).strip()}" if m.group(4) else "")
            out[ci] = rebuilt + _line_comment(out[ci])
        else:
            del out[ci]
    elif qty > 1:
        indent = out[ci][:len(out[ci]) - len(out[ci].lstrip())]
        rebuilt = f"{indent}{qty - 1} {m.group(2).strip()}"
        if m.group(3):
            rebuilt += f" ({m.group(3).strip()})" + (f" {m.group(4).strip()}" if m.group(4) else "")
        out[ci] = rebuilt + _line_comment(out[ci])
        out.insert(ci + 1, add_line)
    else:
        out[ci] = add_line
    if drop_flex is not None:
        for j, ln in enumerate(out):
            e = _parse_flex_line(ln.strip())
            if e and e["out"].lower() == drop_flex["out"].lower() \
                    and e["in"].lower() == drop_flex["in"].lower():
                del out[j]
                break

    # Auto-retire flex lines made stale by THIS swap: a `#~ -Out | +In` proposal
    # is stale once we've maindecked its +In card, or cut its -Out card (and it's
    # no longer in the deck). Replace the first such line with an `applied` note
    # and drop the rest. Only touches `#~` comment lines, never card lines — so it
    # can't affect the copy count or INV-04. (Past sessions hand-cleaned these.)
    # `_ms_key` throughout (BS2-21): a `#~` flex line is a human note, so its spelling
    # is whichever face the author typed — raw `.lower()` comparisons meant a swap of
    # a full-name DFC never retired a flex line naming its front face.
    add_k, cut_k = _ms_key(add), _ms_key(cut)
    maindeck = {_ms_key(_card_line_name(ln) or "") for ln in out if _card_line_name(ln)}
    cut_gone = cut_k not in maindeck
    cleaned, noted = [], False
    for ln in out:
        e = _parse_flex_line(ln.strip())
        if e and e["out"] and e["in"] and (
                _ms_key(e["in"]) == add_k or (_ms_key(e["out"]) == cut_k and cut_gone)):
            if not noted:
                indent = ln[:len(ln) - len(ln.lstrip())]
                cleaned.append(f"{indent}#~ note: applied — {add.strip()} in for {cut.strip()}.")
                noted = True
            continue
        cleaned.append(ln)
    return cleaned


def _safe_write_lines(path, lines, expected_total):
    """temp write -> INV-04 parse-check (parses cleanly AND total copies ==
    expected) -> timestamped .bak -> atomic replace. Returns the .bak path.

    The .bak name comes from the shared `lib.backup_path` (microsecond stamp +
    collision counter), like every other backup in the toolkit. A local
    second-precision name meant two writes in the same second — e.g. a skill applying
    a set of swaps in sequence — silently overwrote the pre-edit snapshot (audit F-03,
    the F22 fix that never reached deck.py)."""
    target = os.path.abspath(path)
    text = "\n".join(lines).rstrip("\n") + "\n"
    fd, tmp = tempfile.mkstemp(suffix=".txt", dir=os.path.dirname(target))
    os.close(fd)
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
        _, parsed = parse_deck_file(tmp)
        got = sum(q for q, *_ in parsed)
        if got != expected_total:
            raise ValueError(f"post-write copy count {got} != expected "
                             f"{expected_total}; not saved.")
        bak = backup_path(target)
        shutil.copy2(target, bak)
        os.replace(tmp, target)
        tmp = None
        return bak
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


RECS_CSV = os.path.join(REPO_ROOT, "recommendations.csv")
RECS_HEADER = ["Date", "Deck", "Source", "Cut", "Add", "Cut Rank", "Cut Of",
               "Cut Protected", "Add Surfaced", "Add Rank", "Add Of"]
# `suggest`'s default display window — "surfaced" means "a human running the default
# command would have SEEN it", not "it appears somewhere in 2,500 scored picks".
_RECS_SUGGEST_WINDOW = 20
# Below this many recorded swaps the report refuses to summarize, the same restraint
# `parse_matches --report` and `count_conf` show. A hit rate over six swaps is noise.
_RECS_MIN_SAMPLE = 20


def recommendation_row(d, cut, add, source, today=None):
    """Score an ACCEPTED swap against what the recommenders said at that moment.

    `swap --apply` is the only place in this toolkit where a human's real add/cut
    decision is observable, and nothing recorded it — so every ranking model here
    (`cuts`, `suggest`, the bounded co-signals, the whole gated stack) has been graded
    on argument and anchor tests, never against a single decision anyone actually made.
    That is the same gap CLAUDE.md records for the `Decks` column: it read as working
    right up until someone MEASURED it and found a 0% actionable rate.

    Deliberately measurement ONLY — nothing here feeds back into a score. The scoring
    terms are bounded and anchored by `check_suggest` precisely so they can't silently
    reorder a tuned deck, and a feedback loop that quietly re-weighted them would defeat
    that by construction. This writes a ledger a human reads.

    Ranks are captured NOW, against the pre-swap deck, because that is the list the
    decision was made against; re-deriving one later would score against a deck the swap
    already changed.

    Returns a row dict, or None if neither model could be computed."""
    import datetime
    row = {c: "" for c in RECS_HEADER}
    row.update({"Date": today or datetime.date.today().isoformat(),
                "Deck": d["id"], "Source": source, "Cut": cut, "Add": add})
    got = False

    # The cut side is the CLEAN measurement: `cuts` ranks the cards already in the deck,
    # so the cut always has a well-defined position in a list that always contains it.
    try:
        rows, _central, prot_present, _int = rank_cut_candidates(d)
        # `_ms_key` both sides, like the `Cut Protected` join below it. A raw `.lower()`
        # compare blanked `Cut Rank` whenever the deck stored a DFC under one face and the
        # swap named the other — telemetry only (G-56 keeps this ledger report-only, and
        # `append_recommendation`'s caller swallows any error), but a silently-empty
        # column is what `deck.py feedback` computes agreement FROM.
        cl = _ms_key(cut)
        idx = next((i for i, r in enumerate(rows) if _ms_key(r[1]) == cl), None)
        row["Cut Of"] = len(rows)
        row["Cut Protected"] = "yes" if _ms_key(cut) in {_ms_key(p) for p in prot_present} \
            else "no"
        if idx is not None:
            row["Cut Rank"] = idx + 1          # 1 = the model's most-cuttable card
        got = True
    except Exception:
        # Telemetry must never cost a swap. A model that raises here (missing pool,
        # unreadable card data) loses its column, not the edit.
        pass

    # The add side is INCOMPLETE by construction and must be read as such: `suggest`
    # filters candidates to cards sharing a synergy THEME, so it is structurally blind
    # to lands and off-theme removal (that is what `--lands`/`--interaction`/`--ramp`
    # exist for). "Not surfaced" is therefore common and is NOT on its own a model miss.
    try:
        res = suggest_scored(d, limit=0)
        if res.get("ok"):
            picks = res["picks"]
            al = add.strip().lower()
            ai = next((i for i, p in enumerate(picks)
                       if p["name"].strip().lower() == al
                       or p["name"].strip().lower().split(" // ")[0] == al), None)
            row["Add Of"] = len(picks)
            row["Add Surfaced"] = "yes" if ai is not None and ai < _RECS_SUGGEST_WINDOW \
                else "no"
            if ai is not None:
                row["Add Rank"] = ai + 1
            got = True
    except Exception:
        pass
    return row if got else None


def load_recommendations(path=None):
    """Rows from the ledger, or [] if it doesn't exist yet. `path` resolves the module
    global at CALL time — a default argument would bind the real file even when a test
    repoints RECS_CSV, the stale-path bug `_file_memo` documents."""
    path = path or RECS_CSV
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def recent_ledger_adds(deck_id, days=14, path=None):
    """`_ms_key` set of cards ADDED to `deck_id` by a ledger swap in the last `days`.

    DISPLAY-ONLY, deliberately: `cmd_cuts` annotates a newcomer because a card added
    for a STRUCTURAL reason (protection, removal, an artifact engine) has a thin tag
    profile by nature, so the theme-fit term reads it as the deck's weakest card the
    moment it arrives — Delney scored fit 3 and Dracogenesis ranked the #1 cut minutes
    after being added (2026-08-27, both decks of that session). K-04 one layer down.
    This function must NEVER be called from the scoring stack;
    test_recommendations.py pins that the seven scoring functions cannot read the
    ledger, and an annotation at the cmd layer is the report-only use G-56 permits."""
    import datetime as _dt
    cutoff = (_dt.date.today() - _dt.timedelta(days=days)).isoformat()
    out = set()
    for r in load_recommendations(path):
        if _norm_deck_id(r.get("Deck")) != _norm_deck_id(str(deck_id)):
            continue
        if (r.get("Date") or "") < cutoff:
            continue
        a = (r.get("Add") or "").strip()
        if a:
            out.add(_ms_key(a))
    return out


def append_recommendation(row, path=None):
    """Append one row, writing through the shared atomic path so an interrupted write
    can't truncate the ledger. Its own DictWriter on its own fieldnames — never
    `lib.write_rows`, which emits the canonical 8 LIBRARY columns and would rewrite this
    file with the wrong header (audit F-02)."""
    path = path or RECS_CSV
    rows = load_recommendations(path) + [row]

    def _w(fh):
        w = csv.DictWriter(fh, fieldnames=RECS_HEADER, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in RECS_HEADER})
    # backup=True (Batch G): this is a full-file REWRITE projected onto RECS_HEADER,
    # so any column added to recommendations.csv — by hand, or by a future field — is
    # dropped for all 250+ historical rows on the next `swap --apply`, with no .bak to
    # recover from. CLAUDE.md scopes backup=False to "a scratch temp the caller
    # promotes itself"; the ledger is a Data subsystem (C-02), not a scratch file.
    atomic_write(path, _w)
    return len(rows)


def _rec_percentile(row):
    """Where the cut sat in the cut list, 0.0 = the model's top cut candidate and 1.0 =
    the card it most wanted kept. None when unrankable."""
    try:
        rank, total = int(row.get("Cut Rank")), int(row.get("Cut Of"))
    except (TypeError, ValueError):
        return None
    if total < 2:
        return None
    return (rank - 1) / (total - 1)


def recommendation_summary(rows):
    """Pure summary of the ledger: (n, agreed, disagreements, median_pct, unsurfaced).

    `disagreements` are the swaps where the model wanted to KEEP the card the human
    cut (upper half of the cut list) — the informative direction, and the reason this
    report leads with them rather than with a hit rate. An AGREEMENT is contaminated by
    the shortlist having been read before the decision; a DISAGREEMENT is a case the
    model got wrong whether or not anyone read it."""
    scored = [(r, _rec_percentile(r)) for r in rows]
    scored = [(r, p) for r, p in scored if p is not None]
    n = len(scored)
    disagreements = sorted((r for r, p in scored if p > 0.5),
                           key=lambda r: -(_rec_percentile(r) or 0))
    agreed = n - len(disagreements)
    pcts = sorted(p for _, p in scored)
    median = None
    if pcts:
        mid = len(pcts) // 2
        median = pcts[mid] if len(pcts) % 2 else (pcts[mid - 1] + pcts[mid]) / 2
    unsurfaced = [r for r in rows if r.get("Add Surfaced") == "no"]
    return n, agreed, disagreements, median, unsurfaced


def recommendation_segments(rows, is_creature):
    """Split the ledger's cut ranking by whether the CUT card was a CREATURE.

    Returns `{segment: (n, agreed, median_pct)}` keyed `creature` / `noncreature` /
    `unknown`. Exists because ONE pooled agreement rate averages two regimes that
    differ by a factor of two, and a single number over a healthy and a broken
    channel reads as healthy — the same saturation failure as the `Decks` column at
    99% and the `review` verdict at 22-of-63.

    Creatures DO carry more tags than noncreature spells (pool means 5.31 vs 3.15,
    tribes + keywords + ability tags) and `fit` is an unnormalized SUM over them — but
    that is an observation, not the diagnosis this docstring used to state. Normalizing
    was pre-registered and tested at 2026-08: it lifts creature agreement and collapses
    noncreature agreement, so the sum is load-bearing for the segment that works. See
    `.cycle/blocks/2026-08-creature-cut-retest.md`.

    `is_creature` is INJECTED (name -> True / False / None) to keep this pure and to
    let a test supply a fake classifier. **A None is its own bucket, never folded into
    `noncreature`**: a card missing from `load_card_data` is unknown, and defaulting an
    unknown to "not a creature" would silently corrupt exactly the segment that reads
    as well-calibrated. Same rule as `lib.card_power` returning None for `*`/`X` rather
    than inventing a number.
    """
    buckets = {}
    for r in rows:
        pct = _rec_percentile(r)
        if pct is None:
            continue
        v = is_creature(r.get("Cut", ""))
        key = "unknown" if v is None else ("creature" if v else "noncreature")
        buckets.setdefault(key, []).append(pct)
    out = {}
    for key, pcts in buckets.items():
        pcts.sort()
        mid = len(pcts) // 2
        median = pcts[mid] if len(pcts) % 2 else (pcts[mid - 1] + pcts[mid]) / 2
        # `agreed` mirrors recommendation_summary: a disagreement is pct > 0.5, so an
        # agreement is everything at or below. Keep the two in step — they are the same
        # question asked of the same rows.
        out[key] = (len(pcts), sum(1 for p in pcts if p <= 0.5), median)
    return out


def cut_creature_classifier(carddata):
    """name -> True (creature) / False (noncreature) / None (not on file), for
    `recommendation_segments`. Resolves a DFC by its FRONT face the way every other
    name join here does (`load_card_data` keys it under both, but a ledger row stores
    whatever the deck line said)."""
    def check(name):
        nl = (name or "").strip().lower()
        if not nl:
            return None
        cd = carddata.get(nl) or carddata.get(nl.split(" // ")[0])
        if not cd:
            return None
        return "Creature" in (cd.get("type") or "")
    return check


_SEGMENT_LABEL = {"creature": "creature cuts", "noncreature": "noncreature cuts",
                  "unknown": "cut card not on file"}

# A segment dominated by ONE deck is not a rate for that segment — it is a rate for
# that deck wearing the segment's name. Decks with at least this many rows get their own
# line; a rate under three rows is not a rate. There is deliberately NO share threshold —
# see segment_concentration.
_RECS_CONC_MIN_ROWS = 3


def segment_concentration(rows, is_creature, segment="creature",
                          min_rows=_RECS_CONC_MIN_ROWS):
    """Per-deck breakdown of one segment, as (deck, n, agreed, share), worst-agreement
    first, for every deck contributing at least `min_rows` rows.

    Exists because testing the creature hypothesis turned up something the pooled
    segment rate hid: **the creature agreement rate is not a property of creatures.**
    Per deck it runs 0/6, 1/6, 3/6, 2/4, 4/4 — from 0% to 100% — so the 45% figure is
    largely a statement about which decks happened to be edited in the ledger window,
    not about how `cuts` grades bodies.

    The tempting story is that deck 46 (0/6) was rebuilt from scratch during the
    window, and a cut made while a deck is being BUILT means "this didn't make the 60",
    which is not the question `cuts` ranks — it scores against a coherent list a
    half-built deck does not yet have. That is a real mechanism and it fits deck 46.
    **It does not fit deck 3 at 1/6**, which was an ordinary tune. So the rebuild
    effect is at best partial, and the wider finding is the variance itself.

    Disclosed, NOT corrected for: these are post-hoc subgroups of 4-6 rows, the
    intervals are enormous and overlap everything, and excluding deck 46 moves the
    segment only 45% → 56% — still under the noncreature 90%. The honest move is to
    show the reader where the rows came from and let a pre-registered test on future
    data settle it, the same restraint `_MIN_SAMPLE` and `count_conf` apply elsewhere.

    **There is deliberately no SHARE threshold.** The first draft disclosed a deck
    holding >20% of the segment, and deck 46 — the case that motivated the whole
    function — sits at 6/31 = 19.4% and did not print. The fix is not a lower cutoff:
    a threshold tuned until the finding you already believe appears is not a
    threshold, it is the finding smuggled into a constant. Every deck with enough rows
    for a rate gets a line, and the reader sees the concentration whatever it is.
    """
    per = {}
    for r in rows:
        pct = _rec_percentile(r)
        if pct is None:
            continue
        v = is_creature(r.get("Cut", ""))
        key = "unknown" if v is None else ("creature" if v else "noncreature")
        if key != segment:
            continue
        d = r.get("Deck") or "?"
        n, ok = per.get(d, (0, 0))
        per[d] = (n + 1, ok + (1 if pct <= 0.5 else 0))
    total = sum(n for n, _ in per.values())
    if not total:
        return []
    out = [(d, n, ok, n / total) for d, (n, ok) in per.items() if n >= min_rows]
    return sorted(out, key=lambda t: (t[2] / t[1], -t[1]))


def _print_recommendation_segments(rows):
    """Print the agreement rate split by creature vs noncreature cut.

    Each segment is held to the SAME `_RECS_MIN_SAMPLE` floor the pooled rate is: a
    segment rate computed off six rows is exactly the noise the floor exists to refuse,
    and splitting a sample is the moment that becomes easy to forget."""
    segs = recommendation_segments(rows, cut_creature_classifier(load_card_data()))
    shown = {k: v for k, v in segs.items()
             if k != "unknown" and v[0] >= _RECS_MIN_SAMPLE}
    if len(shown) < 2:
        thin = [f"{_SEGMENT_LABEL[k]} n={v[0]}" for k, v in sorted(segs.items())
                if k != "unknown" and v[0] < _RECS_MIN_SAMPLE]
        if thin:
            print(f"  (by segment: {', '.join(thin)} — under ~{_RECS_MIN_SAMPLE}, "
                  f"so no split rate; the pooled figure is all this sample supports.)")
        return
    print("\n  By segment — the pooled rate above averages these, so read them instead:")
    for key in ("creature", "noncreature"):
        if key not in shown:
            continue
        n, agreed, median = shown[key]
        print(f"    {_SEGMENT_LABEL[key]:18} {agreed}/{n} ({100 * agreed / n:.0f}%)"
              f"   median {median:.0%} toward 'keep'")
    unk = segs.get("unknown")
    if unk:
        print(f"    ({unk[0]} row(s) whose cut card is not in card-library/pool — "
              f"excluded from both, not folded into either.)")
    lo = min(shown.items(), key=lambda kv: kv[1][1] / kv[1][0])
    if lo[1][1] / lo[1][0] < 0.55:
        # This used to assert a CAUSE — "cuts sums theme weights with no normalization
        # for tag count, so creatures are systematically protected" — and the cause was
        # tested and refuted (BS3-04, pre-registered, .cycle/blocks/
        # 2026-08-creature-cut-retest.md). Normalizing `fit` by tag count does raise
        # creature agreement (53% → 68%), and it COLLAPSES noncreature agreement
        # (83% → 51%): the unnormalized sum is carrying real signal for the segment that
        # works. So the asymmetry is real (creatures average 5.3 tags to a noncreature
        # spell's 3.2, measured over the pool) but it is not a defect with a known fix,
        # and a warning that names a wrong cause is worse than one that names none —
        # it sends the next reader to fix something that would make the tool worse.
        # State what is measured, and stop there.
        print(f"  ⚠ {_SEGMENT_LABEL[lo[0]]} sit near a coin flip. A theme-fit model "
              f"ranks bodies poorly and no fix has survived testing — body quality "
              f"(2026-07) and tag-count normalization (2026-08) were both measured and "
              f"both rejected. Treat the cut ranking as a shortlist there, not a "
              f"signal; grade from the printed oracle text.")
        # Disclose a deck dominating the weak segment. One deck's rate wearing the
        # segment's name is the same "a pooled number hides a split" failure the
        # segmentation itself exists for, one level down (see segment_concentration).
        conc = segment_concentration(rows, cut_creature_classifier(load_card_data()),
                                     segment=lo[0])
        if conc:
            print(f"    Where these rows come from (≥{_RECS_CONC_MIN_ROWS} rows), "
                  f"worst agreement first:")
            for d, n, ok, share in conc:
                print(f"      deck {d:<5} {ok}/{n} ({100 * ok / n:>3.0f}%)  "
                      f"— {share:.0%} of the segment")
            print("      A deck being BUILT contributes cuts meaning \"this didn't make "
                  "the 60\", which is not the\n      question `cuts` ranks — it scores "
                  "against a coherent list a half-built deck does not\n      yet have. "
                  "Read a dominating deck's rows before trusting the segment rate.")


# A deck needs this many logged matches on ONE side of a swap before a record is worth
# reading as anything. Same number and same reasoning as `_RECS_MIN_SAMPLE` and
# `parse_matches._MIN_SAMPLE`: below it a W/L is noise, and printing it invites a tuning
# decision the data cannot support.
_OUTCOME_MIN_SAMPLE = 20


def swap_outcomes(rows, matches):
    """Join applied swaps to the games played after them → per-deck outcome rows.

    THE GAP THIS CLOSES. `recommendations.csv` records what the models SAID and what the
    human DECIDED; `matches.csv` records what then HAPPENED. Both have existed for a
    cycle and nothing connected them, so every ranking model here is still graded on its
    own argument and on `feedback`'s agreement rate — a number CLAUDE.md itself warns is
    contaminated, because the human read the shortlist before deciding. An outcome is the
    only signal in this project that the models cannot influence.

    Returns [{deck, swaps, first_swap, before, after, ...}] sorted by deck id, where
    `before`/`after` are (wins, losses) split on the deck's FIRST recorded swap — the
    point from which its list stopped being the one the earlier games were played with.
    Draws are excluded from both, matching `parse_matches.report`.

    THE SPLIT IS DELIBERATELY COARSE. A per-swap before/after would be the interesting
    analysis and is not honest at any volume this record will reach soon: a deck
    accumulates many swaps, their windows overlap almost completely, and attributing a
    result to one of four changes made the same week is a story, not a measurement. Per
    DECK, split once, is the strongest claim the data shape supports.

    REPORT-ONLY, and structurally so: nothing here is reachable from a scoring function,
    and `tests/test_recommendations.py` scans the seven of them for `MATCHES_CSV`,
    `load_match_counts` and `swap_outcomes` for the same reason it already scans for
    `load_recommendations` (G-56). An outcome signal is the single most tempting thing to
    quietly feed back into a ranking, and doing so would defeat the bounded-and-anchored
    property `check_suggest` exists to hold."""
    by_deck = {}
    for r in rows:
        did = (r.get("Deck") or "").strip()
        date = (r.get("Date") or "").strip()
        if not did or not date:
            continue
        e = by_deck.setdefault(did, {"deck": did, "swaps": 0, "first_swap": date})
        e["swaps"] += 1
        e["first_swap"] = min(e["first_swap"], date)

    played = {}
    for m in matches:
        did = (m.get("Deck") or "").strip()
        if did:
            played.setdefault(did, []).append(m)

    out = []
    for did, e in by_deck.items():
        ms = played.get(did, [])
        if not ms:
            continue
        before = after = None
        bw = bl = aw = al = 0
        for m in ms:
            res = (m.get("Result") or "").strip().upper()
            if res not in ("W", "L"):
                continue                      # a draw or an unreadable cell decides nothing
            if (m.get("Date") or "") < e["first_swap"]:
                bw, bl = bw + (res == "W"), bl + (res == "L")
            else:
                aw, al = aw + (res == "W"), al + (res == "L")
        before, after = (bw, bl), (aw, al)
        out.append({**e, "matches": len(ms), "before": before, "after": after,
                    "n_after": aw + al, "n_before": bw + bl})
    return sorted(out, key=lambda x: (len(x["deck"]), x["deck"]))


def _print_swap_outcomes(rows):
    """The outcome section of `feedback`. Prints the COVERAGE honestly and refuses the
    read below `_OUTCOME_MIN_SAMPLE`, which is where this record sits and will sit for a
    long time — the point of building it now is that the analysis is already in place when
    volume arrives, not that it can say anything today."""
    matches = []
    try:
        import parse_matches as pm
        matches = pm.load_matches(MATCHES_CSV)
    except Exception:
        pass                                   # matches.csv is deliberately not required
    if not matches:
        print("\nOutcomes: no matches.csv yet — `/log-matches` records them, and a swap's "
              "effect is the one signal these models cannot influence.")
        return
    joined = swap_outcomes(rows, matches)
    attributed = sum(1 for m in matches if (m.get("Deck") or "").strip())
    print(f"\nOutcomes — {len(rows)} recorded swap(s) against {len(matches)} logged "
          f"match(es) ({attributed} attributed to a deck):")
    if not joined:
        print("  No deck has both a recorded swap and a logged match yet.")
        return
    print(f"    {'deck':6} {'swaps':>5} {'games':>6}  {'before':>7} {'after':>7}")
    for j in joined:
        b, a = j["before"], j["after"]
        print(f"    {j['deck']:6} {j['swaps']:>5} {j['matches']:>6}  "
              f"{b[0]}-{b[1]:<5} {a[0]}-{a[1]:<5}"
              f"   (split at the first swap, {j['first_swap']})")
    best = max((j["n_after"] for j in joined), default=0)
    if best < _OUTCOME_MIN_SAMPLE:
        print(f"  ⚠ the largest post-swap sample is n={best}, far below the "
              f"~{_OUTCOME_MIN_SAMPLE} a win rate needs. NO outcome is reported above and "
              f"none should be read into those records — they are printed so the coverage "
              f"is visible, not so the numbers are.")
        print("  This is the project's real bottleneck, and it is owner-paced: the "
              "pipeline works end to end, so the only missing input is games.")


_TUNED_UNPLAYED_FLOOR = 5     # swaps before a deck earns a most-tuned/least-played row


def _print_tuned_vs_played(rows, deck_filter=None):
    """Most-tuned, least-played — a PLAY QUEUE, not a scold.

    Measured 2026-08-27 on the live ledger: 31 decks carried ≥5 recorded swaps and
    ZERO recorded matches, and the eight most-tuned decks had ONE match among them —
    so `swap_outcomes`' 20-match floor is unreachable for exactly the decks with the
    most invested tuning, and the record structurally cannot say whether any of those
    tunes worked. Report-only, roster-shaped (skipped under a deck filter), and read
    with G-74's caveat built in: the match record is young and a PHONE game never
    reaches the desktop log, so "0 matches" means unRECORDED, not necessarily
    unplayed."""
    if deck_filter:
        return
    from collections import Counter
    tuned = Counter((r.get("Deck") or "").strip() for r in rows)
    tuned.pop("", None)
    played = load_match_counts()
    heavy = [(d, c) for d, c in tuned.items() if c >= _TUNED_UNPLAYED_FLOOR]
    if not heavy:
        return
    unplayed = sorted(d for d, _c in heavy if not played.get(d))
    print("\nMost tuned vs. least played (swaps recorded / matches recorded):")
    for d, c in sorted(heavy, key=lambda t: (-t[1], t[0]))[:8]:
        print(f"    deck {d:<5} {c:>3} swap(s)   {played.get(d, 0):>3} match(es)")
    if unplayed:
        print(f"  {len(unplayed)} deck(s) with ≥{_TUNED_UNPLAYED_FLOOR} swaps and ZERO "
              f"recorded matches: {', '.join(unplayed)}")
    print("  A play queue, not a verdict: `swap_outcomes` needs ~20 matches per deck "
          "before it can say whether a tune WORKED, and a phone game never reaches the "
          "desktop log (G-74) — log those via the dashboard panel / `--add`.")


def cmd_feedback(args):
    """Report how the recommenders scored against the swaps actually applied."""
    rows = load_recommendations()
    if getattr(args, "id", None):
        # Normalized both sides (G-82 / BS8-17): `feedback 06` read "nothing recorded"
        # for deck 6, and an unknown id was indistinguishable from an un-tuned deck.
        if not find_deck(args.id):
            eprint(f"No deck with id {args.id!r}. Try: deck.py list")
            return 1
        want = _norm_deck_id(args.id)
        rows = [r for r in rows if _norm_deck_id(r.get("Deck")) == want]
    if not rows:
        print("No recommendation outcomes recorded yet. They accrue automatically "
              "every time `deck.py swap --apply` or `apply-flex --apply` runs.")
        return 0

    n, agreed, disagreements, median, unsurfaced = recommendation_summary(rows)
    print(f"{len(rows)} applied swap(s) recorded"
          + (f" for deck {args.id}" if getattr(args, "id", None) else "")
          + f"; {n} with a usable cut ranking.\n")

    # Lead with the misses. An agreement is partly the shortlist's own influence — the
    # human read `cuts` before deciding — so it cannot validate the model. A
    # disagreement is a case the model got wrong whichever way the decision was reached.
    if disagreements:
        print(f"⚠ {len(disagreements)} swap(s) where the model wanted to KEEP the card "
              f"you cut (upper half of its own cut list).")
        print("  These are the informative ones — read the card and ask what the "
              "ranking couldn't see.\n")
        for r in disagreements[:12]:
            pct = _rec_percentile(r)
            print(f"    {r.get('Date','')}  deck {r.get('Deck','')}: "
                  f"−{r.get('Cut','')} → +{r.get('Add','')}")
            print(f"        cuts ranked it {r.get('Cut Rank')}/{r.get('Cut Of')} "
                  f"({pct:.0%} toward 'keep')"
                  + ("   [was #: protect:]" if r.get("Cut Protected") == "yes" else ""))
        if len(disagreements) > 12:
            print(f"    … and {len(disagreements) - 12} more")
        print()

    if unsurfaced:
        print(f"{len(unsurfaced)} add(s) that `suggest` did not surface in its default "
              f"top {_RECS_SUGGEST_WINDOW}:")
        for r in unsurfaced[:10]:
            print(f"    +{r.get('Add','')}  (deck {r.get('Deck','')})")
        if len(unsurfaced) > 10:
            print(f"    … and {len(unsurfaced) - 10} more")
        print("  EXPECTED to be high, and not on its own a model miss: `suggest` filters "
              "to cards sharing a synergy THEME, so it is structurally blind to lands "
              "and off-theme removal. That is what `suggest --lands/--interaction/--ramp` "
              "are for. Read it as 'which fills the theme model can't reach'.")
        # The single health number for the recommender over time, with the same caveat
        # as the list above it: it measures how often the theme model and the human
        # were shopping in the same aisle, not whether either was right.
        rated = [r for r in rows if (r.get("Add Surfaced") or "") in ("yes", "no")]
        if len(rated) >= _RECS_MIN_SAMPLE:
            yes = sum(1 for r in rated if r["Add Surfaced"] == "yes")
            print(f"  Surfaced-rate over the whole ledger: {yes}/{len(rated)} chosen "
                  f"add(s) ({100 * yes / len(rated):.0f}%) appeared in `suggest`'s top "
                  f"{_RECS_SUGGEST_WINDOW} beforehand. Watch the TREND, not the level — "
                  f"the level is dominated by structural picks the theme gate excludes "
                  f"by design (G-38).")
        print()

    if n < _RECS_MIN_SAMPLE:
        tail = ("The rows above are worth reading individually"
                if (disagreements or unsurfaced)
                else "Nothing has diverged from the models yet")
        print(f"n={n} — too few to summarize (need ~{_RECS_MIN_SAMPLE}). {tail}; "
              f"a rate computed off {n} is noise.")
    else:
        print(f"Agreement: the cut sat in the model's cut half {agreed}/{n} times "
              f"({100 * agreed / n:.0f}%); median position {median:.0%} toward 'keep' "
              f"(0% = the model's top cut candidate).")
        print("  Read with care: you saw the shortlist before deciding, so a high "
              "agreement rate partly measures the list's INFLUENCE, not its accuracy. "
              "The disagreements above are the part that doesn't suffer from that.")
        _print_recommendation_segments(rows)
    _print_tuned_vs_played(rows, deck_filter=getattr(args, "id", None))
    _print_swap_outcomes(rows)
    print("\nThis ledger is REPORT-ONLY and never feeds back into a score — the ranking "
          "terms are bounded and anchored by check_suggest so they can't silently "
          "reorder a tuned deck, and an automatic re-weighting would defeat that.")
    return 0


def _do_swap(d, cut, add, apply, flex_entry=None, section=None):
    """Shared engine for `swap` and `apply-flex`: preview deltas, and on --apply
    perform the edit with a .bak + INV-04 re-check."""
    add_disp, add_set, add_cn = _printing_of(add)
    # Write the CANONICAL name, not the front-face shorthand the caller typed.
    # Resolved BEFORE the self-swap guard, and the guard compares `_ms_key` (front
    # face): `--cut "Bruce Banner" --add "Bruce Banner // The Incredible Hulk"` is
    # the same card under two spellings, and the exact-name compare let it through —
    # whereupon the raw-line edit's cut-rebuild overwrote its own bump of the shared
    # line, the audit-F2 corruption from a second direction (broad-scan BS-05).
    add = add_disp
    # A card can't be swapped for itself: it's a no-op, and on --apply the raw-line
    # edit would decrement (or delete) the shared line instead (audit F2). The
    # INV-04 copy-count guard wouldn't catch it, since a 1-for-1 swap preserves the
    # total — so reject it up front rather than silently corrupt the count.
    if _ms_key(cut) == _ms_key(add):
        eprint(f"Cut and add are the same card ({cut!r}) — nothing to swap.")
        return 1
    carddata = load_card_data()
    # COPY — this function calls `fetch_missing_mana`, which mutates (BS5-13). See the
    # longer note at `cmd_stats`' own copy.
    mana = dict(load_mana())
    _, cards = parse_deck_file(d["path"])
    after = _cards_after_swap(cards, cut, add, (add_set, add_cn))
    if after is None:
        eprint(f"{cut!r} is not in deck {d['id']}. Nothing swapped.")
        return 1
    # `_ms_key` both sides (BS2-21): the header may name either face-spelling of the
    # card being cut, and a raw `.lower()` comparison let a protected DFC be cut
    # without the ⚠ when the spellings differed. The header side is normalized by
    # `_protected` itself now (BS4-01), so only the cut argument needs keying here.
    if _ms_key(cut) in _protected(d.get("meta") or {}):
        eprint(f"⚠ {cut!r} is marked protected (#: protect:) in deck {d['id']} — a "
               "signature/spice card. Proceeding, but reconsider; remove it from the "
               "header if this cut is intentional.")

    nonland = [n for q, n, s, c in cards if n.lower() not in BASICS]
    fetch_missing_mana(sorted(set(nonland + [add])), mana)
    before_s = _deck_summary(cards, carddata, mana)
    after_s = _deck_summary(after, carddata, mana)

    cut_cd = carddata.get(cut.lower()) or {}
    cut_t = cut_cd.get("type", "") or "?"
    add_cd = carddata.get(add.lower())
    add_t = (add_cd or {}).get("type", "") or "?"
    _, _, qty_by = load_collection()
    have, _ = owned(qty_by, add)
    rar = load_rarities().get(add.lower(), "")
    add_mv = (mana.get(add.lower()) or (None, None))[1]

    # Print the FULL oracle text of both cards. Grading a swap from a type line
    # (or a truncated read) hides later abilities — the whole card must be in view.
    def _oracle(cd):
        return [ln for ln in (cd.get("text", "") or "").splitlines() if ln.strip()]

    print(f"Deck {d['id']}: {d['name'] or d['id']} — swap preview\n")
    print(f"  − {cut}   [{cut_t}]")
    for ln in _oracle(cut_cd):
        print(f"        {ln}")
    tail = " ".join(x for x in [rar, (f"×{have}" if have > 0 else "craft"),
                                (f"MV {add_mv}" if add_mv is not None else "")] if x)
    print(f"  + {add}   [{add_t}]" + (f"   ({tail})" if tail else ""))
    for ln in _oracle(add_cd or {}):
        print(f"        {ln}")
    if not add_cd:
        print(f"  ⚠ '{add}' not found in library or pool — check spelling; "
              "it will be added as a bare line.")

    def delta(a, b):
        d_ = b - a
        return f"{a} → {b}" + (f"  ({d_:+d})" if d_ else "")

    print("\n  deltas:")
    print(f"    total cards     {delta(before_s['total'], after_s['total'])}")
    print(f"    creatures       {delta(before_s['creatures'], after_s['creatures'])}")
    print(f"    avg nonland MV  {before_s['avg_mv']:.2f} → {after_s['avg_mv']:.2f}"
          f"  ({after_s['avg_mv'] - before_s['avg_mv']:+.2f})")
    b_col = "/".join(sorted(before_s["colors"])) or "—"
    a_col = "/".join(sorted(after_s["colors"])) or "—"
    print(f"    color identity  {b_col} → {a_col}"
          + ("   (adds a color!)" if after_s["colors"] - before_s["colors"] else ""))

    if not apply:
        print("\n(dry run — pass --apply to write the change with a .bak)")
        return 0

    # Score the recommenders against this decision BEFORE the edit — the pre-swap deck
    # is the list the human actually chose from. Never fatal: a swap must not fail
    # because telemetry did.
    try:
        rec = recommendation_row(d, cut, add, "flex" if flex_entry is not None else "swap")
    except Exception:
        rec = None

    with open(d["path"], encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    try:
        # `(add_set, add_cn)`, the same printing tuple `_cards_after_swap` gets above.
        # P8 split `_printing_of`'s return from a 2-tuple into three values and updated
        # the first call site but not this one, leaving `add_pr` dangling — so EVERY
        # `swap --apply` raised NameError while the dry run, which returns before this
        # line, stayed clean. Nothing caught it: `check_commands` marks `swap` covered
        # because a skill REFERENCES it, and no test drives the write path.
        new_lines = _swap_edit_lines(lines, cut, add, (add_set, add_cn),
                                     drop_flex=flex_entry)
        # Relocation happens BEFORE the write and inside the same try, so a bad
        # `--section` aborts the swap entirely rather than leaving the line misfiled
        # with an error printed after the fact. `_safe_write_lines`' card-total guard
        # still applies — a move preserves the total by construction.
        if section:
            new_lines = _relocate_card_line(new_lines, add, section)
        bak = _safe_write_lines(d["path"], new_lines, before_s["total"])
    except ValueError as e:
        eprint(f"Not saved: {e}")
        return 1
    print(f"\nApplied. Wrote {os.path.relpath(d['path'], REPO_ROOT)} "
          f"(backup: {os.path.basename(bak)}).")
    if flex_entry is not None:
        print("Removed the consumed flex line.")
    # The add inherits the cut's line slot, and therefore the cut's `# section` comment.
    # Warn when that makes the file lie (advisory — the swap is already written, and
    # moving a line is a human editorial call, not something to do automatically).
    # `_ms_key` both sides, same reason as `_relocate_card_line` above (S1-02): when the
    # add was BUMPED onto an existing line rather than written fresh, that line keeps its
    # own face spelling, so a raw comparison returned None and the G-05 advisory was
    # skipped WITHOUT saying it had been skipped — a warning that silently does not run
    # is worse than one that fires, since the file then lies to the next reader unflagged.
    ai = next((i for i, ln in enumerate(new_lines)
               if _ms_key(_card_line_name(ln) or "") == _ms_key(add)), None)
    if ai is not None:
        warn = section_mismatch(new_lines, ai, add.strip(), load_card_data())
        if warn:
            print(f"  ⚠ section comment: {warn}")
            print(f'     Move it mechanically (never by hand — G-65): '
                  f'deck.py move {d["id"]} "{add}" --section "<header substring>" '
                  f'--apply relocates the line verbatim, with no ledger row.')
    # Record how the recommenders scored this decision. Written AFTER the edit lands, so
    # a rejected write leaves no phantom row; announced rather than silent, because a
    # command that writes a second file should say so.
    if rec is not None:
        try:
            total = append_recommendation(rec)
            bits = []
            if rec.get("Cut Rank"):
                bits.append(f"cuts ranked −{cut} {rec['Cut Rank']}/{rec['Cut Of']}")
            if rec.get("Add Surfaced"):
                bits.append(f"suggest surfaced +{add}: {rec['Add Surfaced']}")
            print(f"  · recorded to {os.path.basename(RECS_CSV)} ({total} swap(s)): "
                  + "; ".join(bits) + ".  Read it: deck.py feedback")
        except Exception as e:
            # BROADER than OSError (Batch G): a csv.Error / UnicodeDecodeError from a
            # corrupted ledger propagated after the deck file was already written, so
            # the user saw a traceback and reasonably concluded the swap had failed —
            # against G-56's "recording never blocks a swap".
            eprint(f"  · could not record the outcome ({type(e).__name__}: {e}) — "
                   f"the swap itself is saved.")
    return 0


def cmd_swap(args):
    """Preview (or --apply) a single -cut/+add swap with before/after deltas."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    return _do_swap(d, args.cut, args.add, args.apply,
                    section=getattr(args, "section", None))


def cmd_apply_flex(args):
    """Promote flex swap #n (a `#~ -Out | +In` line) into the maindeck."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    swaps = [e for e in parse_flex(d["path"]) if e["out"] and e["in"]]
    if not swaps:
        print("No applicable flex swaps (need a '#~ -Out | +In' line). "
              f"See: deck.py flex {args.id}")
        return 0
    if args.n < 1 or args.n > len(swaps):
        eprint(f"Flex swap #{args.n} out of range (1..{len(swaps)}). "
               f"See: deck.py flex {args.id}")
        return 1
    e = swaps[args.n - 1]
    return _do_swap(d, e["out"], e["in"], args.apply, flex_entry=e)


# --- deck-construction legality lint ---------------------------------------- #
# Formats where the deck is singleton (at most one of each nonbasic) and/or has a
# larger minimum size than the 60-card constructed default.
SINGLETON_FORMATS = {"brawl", "historic brawl", "commander", "oathbreaker", "duel"}
BIG_DECK_FORMATS = {"commander", "historic brawl", "oathbreaker"}
# ARENA RENAMED THESE AND THE REPO KEPT THE OLD NAMES, so the two labels are INVERTED
# against the client's UI: Arena's "Brawl" is 100-card Historic Brawl (`historic brawl`
# here) and Arena's "Standard Brawl" is the 60-card one (`brawl` here). A `#: format:`
# is hand-written free text, so the spellings a person will actually reach for have to
# resolve — and before this map, `historic-brawl` (the hyphenated slug that IS in
# `_FORMAT_SLUGS` for legality lookup) matched NEITHER set, silently giving a 100-card
# singleton deck a 60-card floor AND no copy limit at all: both construction checks off
# at once, with `legal` still printing a clean bill. Normalize before every set test.
_FORMAT_ALIASES = {
    "historic-brawl": "historic brawl",
    "historicbrawl": "historic brawl",
    "standard brawl": "brawl",
    "standard-brawl": "brawl",
}


def normalize_format(fmt):
    """Canonical form of a `#: format:` value for the construction-rule sets above.
    Lowercased, whitespace-collapsed, and aliased (see `_FORMAT_ALIASES`)."""
    f = " ".join((fmt or "").strip().lower().split())
    return _FORMAT_ALIASES.get(f, f)


# The pool's `Legalities` column carries SCRYFALL's keys, and Scryfall's `brawl` is
# Arena's 100-card HISTORIC Brawl. The repo's `Brawl` (G-08) is Arena's 60-card Standard
# Brawl, whose card pool is Standard's — so a `#: format: Brawl` deck must be checked and
# recommended against `standard`, and a `Historic Brawl` deck against `brawl`. Until
# BS8-04 every legality surface tested the raw string: a Historic-only card passed
# `legal` in deck 3-brawl, `suggest` on it returned 2,238 of 3,228 picks that were not
# Standard-legal, and a Historic Brawl deck got no legality check at all ("isn't
# tracked"). ONE mapping, read by every site that asks "is this card legal here".
_POOL_FORMAT_KEY = {"brawl": "standard", "historic brawl": "brawl"}


def pool_format_key(fmt):
    """The pool `Legalities` key a deck's `#: format:` is checked against, or "" when
    the format is untracked (size/copy rules still apply — see `legality_report`)."""
    f = normalize_format(fmt)
    key = _POOL_FORMAT_KEY.get(f, f)
    return key if key in POOL_FORMATS else ""
# Formats led by a legendary creature/planeswalker commander with a color-identity lock
# (Oathbreaker's PW-commander + signature-spell rules differ, so it's excluded here).
_COMMANDER_FORMATS = {"brawl", "historic brawl", "commander", "duel"}


@_file_memo("MATCHES_CSV")
def load_match_counts():
    """deck_id -> matches PLAYED, from matches.csv. `{}` when no record exists.

    Read through `parse_matches.load_matches` rather than a local DictReader, so the
    schema (and the pre-rename `Course ID` migration it performs) has one owner. The
    import is lazy and the failure is swallowed to `{}` on purpose: matches.csv is
    deliberately NOT an invariant — the project ran without one for its whole life and
    a repo with no logged games is healthy — so nothing here may start requiring it.

    Counts ROWS, not results: a row whose Result cell is unreadable is still a match
    that was played, and dropping it would under-report the one thing this number is
    for. Variants are NOT folded into their parent (19b keeps its own count) because
    they are different lists, and the whole point of a variant is to grade it on its
    own. Deliberately returns a COUNT and no win/loss: at these sample sizes a rate is
    noise, `--report` refuses to print one below 20 matches, and a `2-2` sitting in a
    skimmable triage table is exactly the invitation that restraint exists to refuse.
    """
    try:
        import parse_matches as pm
        # Pass the path EXPLICITLY. `load_matches`' default binds `MATCHES_CSV` at
        # definition time, so a bare call reads the real file forever while
        # `_file_memo` keys the cache on whatever `deck.MATCHES_CSV` currently points
        # at — the two disagree, and the loader serves data from a file the cache is
        # not watching. That is the same stale-cache wiring bug `_file_memo`'s
        # docstring describes for POOL_CSV, and it made every repointed-path test
        # below pass against the live record instead of its fixture.
        rows = pm.load_matches(MATCHES_CSV)
    except Exception:
        return {}
    out = {}
    for r in rows:
        did = (r.get("Deck") or "").strip()
        if did:
            out[did] = out.get(did, 0) + 1
    return out


def load_legalities():
    """name_lower -> set(formats the card is legal in), from card-pool.csv's
    Legalities column. Empty if the pool is missing or predates the column."""
    out = {}
    if not os.path.exists(POOL_CSV):
        return out
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            if not n:
                continue
            legs = {x.strip().lower() for x in (r.get("Legalities") or "").split(";")
                    if x.strip()}
            out.setdefault(n, legs)
    return alias_front(out)


def legality_report(meta, cards, fmt, leg, carddata=None):
    """Pure legality computation shared by `legal` (verbose, one deck) and `audit`
    (one line per deck) so both apply IDENTICAL size/copy/format rules. Returns a
    dict: problems (list of strings), unknown (pool-absent card names), notes
    (informational lines about untracked formats / missing legality data), plus
    total / min_size / copy_limit / singleton for the caller to render. Offline —
    `leg` is a pre-loaded load_legalities() map (pass {} to skip the format check).

    Format-aware extras:
      • Singleton formats (Brawl/Commander) enforce the 1-copy limit (already), and
        when `carddata` is supplied ALSO validate the `#: commander:` — it must be a
        legendary creature/planeswalker in the deck, and every nonbasic card's color
        identity must sit within the commander's (Brawl's defining rule).
      • Alchemy: a card that's Standard-legal but not Alchemy-legal is REBALANCED, not
        illegal — Arena plays its A- version — so it's a note, not a problem."""
    # Copy counts key on `_ms_key` (front face), like every other name-facing join
    # (see `_ms_key`'s docstring): the roster live-mixes `Front // Back` and front-only
    # spellings of the same card, and an exact-name key saw them as two different cards
    # — 4 copies under one spelling plus 1 under the other passed the 4-copy limit, and
    # two "singletons" passed Brawl (broad-scan BS-06). The first-seen spelling is kept
    # for display; `leg` / `carddata` lookups below already alias the front face.
    counts, order, disp, total = {}, [], {}, 0
    for q, n, s, c in cards:
        total += q
        nl = n.lower()
        # Snow-covered basics are BASIC lands (CR 205.4c): exempt from the copy
        # limit like their plain siblings, which this loop flagged at 5+ copies
        # (broad-scan batch 5). Deliberately NOT added to BASICS itself — that set
        # also means "unlimited in the Arena collection", and snow basics are real
        # craftable cards there, so the ownership sites must keep counting them.
        if nl in BASICS or nl.startswith("snow-covered "):
            continue
        key = _ms_key(n)
        if key not in counts:
            order.append(key)
            disp[key] = n
        counts[key] = counts.get(key, 0) + q

    cfmt = normalize_format(fmt)
    singleton = cfmt in SINGLETON_FORMATS
    copy_limit = 1 if singleton else 4
    min_size = 100 if cfmt in BIG_DECK_FORMATS else 60

    problems, unknown, notes = [], [], []
    if fmt and total < min_size:
        problems.append(f"deck has {total} cards — {fmt} minimum is {min_size}")

    for nl in order:
        if counts[nl] > copy_limit:
            problems.append(f"{disp[nl]}: {counts[nl]} copies (max {copy_limit}"
                            + (", singleton format" if singleton else "") + ")")

    lkey = pool_format_key(fmt)
    if fmt and lkey and leg:
        illegal, rebalanced = [], []
        for nl in order:
            card_leg = leg.get(nl)
            if card_leg is None:
                unknown.append(disp[nl])
            elif lkey not in card_leg:
                # A Standard card that isn't Alchemy-legal is rebalanced (A- version),
                # not illegal — it's still playable in Alchemy.
                if lkey == "alchemy" and "standard" in card_leg:
                    rebalanced.append(disp[nl])
                else:
                    illegal.append(disp[nl])
        for name in illegal:
            problems.append(f"{name}: not legal in {fmt}")
        if rebalanced:
            notes.append(f"{len(rebalanced)} card(s) are Alchemy-rebalanced — they play as "
                         f"their A- version in Alchemy (still legal): "
                         + ", ".join(rebalanced[:8]) + (" …" if len(rebalanced) > 8 else ""))
    elif fmt and not lkey:
        notes.append(f"Format '{fmt}' isn't tracked for legality "
                     f"(known: {', '.join(sorted(POOL_FORMATS))}) — checking size/copies only.")
    elif fmt and not leg:
        notes.append("card-pool.csv has no legality data (rebuild with build_pool.py) — "
                     "checking size/copies only.")

    # Commander rules (Brawl / Commander) — needs card types + identities.
    if singleton and cfmt in _COMMANDER_FORMATS and carddata is not None:
        cmd_name = (meta.get("commander") or "").strip()
        if not cmd_name:
            problems.append(f"{fmt} needs a `#: commander:` header — a legendary creature "
                            "or planeswalker in the deck (it leads from the command zone)")
        else:
            cnl = cmd_name.lower()
            ccd = carddata.get(cnl) or carddata.get(cnl.split(" // ")[0])
            cident = None
            if ccd is None:
                notes.append(f"commander {cmd_name!r} not in card data — can't verify its "
                             "type/identity (check spelling, or rebuild the pool)")
            else:
                ctype = ccd.get("type", "") or ""
                if not ("Legendary" in ctype and ("Creature" in ctype or "Planeswalker" in ctype)):
                    problems.append(f"commander {cmd_name}: must be a legendary creature or "
                                    f"planeswalker (is {ctype or '?'})")
                cident = card_colors(ccd.get("colors", ""))
                # Presence keys on `_ms_key` too: a `#: commander:` naming the front
                # face against a full-name deck line is the same card (BS-06).
                if _ms_key(cmd_name) not in counts:
                    notes.append(f"commander {cmd_name} isn't listed in the deck — add it "
                                 f"(it counts as one of the {min_size})")
            if cident is not None:
                strays = []
                for nl in order:
                    cd2 = carddata.get(nl) or carddata.get(nl.split(" // ")[0])
                    if cd2 and not card_colors(cd2.get("colors", "")) <= cident:
                        strays.append(disp[nl])
                if strays:
                    ident_s = "".join(sorted(cident)) or "C"
                    problems.append(f"outside commander's color identity ({ident_s}): "
                                    + ", ".join(strays[:8]) + (" …" if len(strays) > 8 else ""))

    return {"problems": problems, "unknown": unknown, "notes": notes,
            "total": total, "min_size": min_size, "copy_limit": copy_limit,
            "singleton": singleton}


def cmd_legal(args):
    """Deck-construction legality lint: deck size, copy limits, and per-card format
    legality against the deck's declared `#: format:` (override with --format). Size
    and copy rules are offline; the legality check needs the pool's Legalities
    column (build_pool.py). Basic lands are exempt (unlimited)."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    meta, cards = parse_deck_file(d["path"])
    fmt = (getattr(args, "fmt", None) or meta.get("format") or "").strip().lower()

    rep = legality_report(meta, cards, fmt, load_legalities(), carddata=load_card_data())
    problems, unknown, total, min_size = (rep["problems"], rep["unknown"],
                                          rep["total"], rep["min_size"])

    print(f"Deck {d['id']}: {d['name'] or d['path']} — legality check"
          + (f"  ({fmt})" if fmt else "  (no #: format: declared)"))
    print("-" * 52)

    print(f"Deck size: {total} cards" + (f"  (min {min_size})" if fmt else ""))
    for note in rep["notes"]:
        print(note)

    if problems:
        print(f"\n✗ {len(problems)} construction issue(s):")
        for p in problems:
            print(f"    {p}")
    else:
        print("\n✓ No construction issues"
              + (f" for {fmt}." if fmt else " (size/copy rules only — no format declared)."))

    # PRINTING sanity. Legality is about the card; this is about whether the LINE names
    # a printing that exists — the half nothing checked, so a wrong collector number
    # produced a file that read clean everywhere and would not import (F-01).
    bad_set, unverified = printing_problems(cards)
    if bad_set:
        print(f"\n✗ {len(bad_set)} line(s) name a SET CODE that does not exist:")
        for n, st, cn in bad_set:
            print(f"    {n} — ({st}) {cn}")
    if unverified:
        print(f"\n△ {len(unverified)} unverified printing(s) — the set is real but this "
              "collector number is not one we hold (the pool keys ONE printing per card, "
              "so an alternate art lands here too):")
        for n, st, cn, kn in unverified:
            known = ", ".join(f"({a.upper()}) {b}" for a, b in kn)
            print(f"    {n} — ({st}) {cn}   known: {known}")
    if unknown:
        shown = ", ".join(unknown[:8]) + ("…" if len(unknown) > 8 else "")
        print(f"\n{len(unknown)} card(s) not in the pool — {fmt} legality unverified "
              f"(WIP / older printings): {shown}")
    # A nonexistent set code is a HARD failure per G-65 and prints a ✗ above — it
    # must fail the exit code too, not just the page: `legal` exited 0 on it, and
    # preflight's construction-PASS inherited the blind spot, rescued only by the
    # separate check_all leg (broad-scan batch 5). `unverified` stays soft.
    return 1 if (problems or bad_set) else 0


# --- cut candidates: the companion to `suggest` (adds) ---------------------- #
def _header_card_keys(meta, header):
    """The card names in a semicolon-separated `#: <header>:` list, as `_ms_key`
    COMPARISON KEYS (lowercased, front face only).

    The normalization is the whole point, and it was the last open member of the G-63
    class (BS2-07). Both header readers used to return raw `.lower()` names while every
    consumer compared them against a deck line's raw `.lower()` name — so a header
    naming a DFC by its FRONT face ("Eddie Brock") never matched the line storing the
    full name ("Eddie Brock // Venom, Lethal Protector"), and the instruction the header
    encodes silently did nothing. It was left open on a "zero live instances" measurement
    that expired the moment deck 66 was drafted: its `#: protect:` header named the
    deck's own title card, and `cuts` ranked that card as cuttable anyway.

    `header_card_staleness` — the G-68 gate built to catch a dead header entry — has
    always joined on `_ms_key`, so it reported the header as HEALTHY while the consumers
    could not read it. A gate that vouches for a disabled instruction is worse than no
    gate, which is why the fix belongs HERE, at the one place both readers share, rather
    than at each call site deciding again."""
    raw = (meta or {}).get(header, "") or ""
    return {_ms_key(p) for p in raw.split(";") if p.strip()}


def _protected(meta):
    """Cards a deck's `#: protect:` header marks as signature/spice — the tooling
    must never propose cutting them. Format: `#: protect: Card A; Card B`
    (repeatable across lines; SEMICOLON-separated — card names contain commas, so
    comma can't be the separator). Returns a set of `_ms_key` comparison keys, so
    every consumer must test `_ms_key(name) in _protected(meta)` — see
    `_header_card_keys` for why a raw `.lower()` join was a silent no-op on DFCs."""
    return _header_card_keys(meta, "protect")


def _uncastable_ok(meta):
    """Cards the deck AUTHOR asserts are intentionally uncastable — a REANIMATOR's
    targets, which you never cast from hand and cheat in from the graveyard instead.
    Format: `#: uncastable-ok: Card A; Card B` (semicolon-separated, like `#: protect:`,
    because card names contain commas). Returns a set of `_ms_key` comparison keys —
    this is the MORE dangerous half of the pair to get wrong, since a name the consumer
    cannot match doesn't merely fail to protect a card, it silently re-enables the
    castability failure the header exists to suppress (floor capped at C, `preflight`
    BLOCKED). See `_header_card_keys`.

    Why this exists: the castability lint and `tier_band` both model "you cannot cast
    this" as a build ERROR, which is right by default and wrong for a whole archetype.
    Measured on deck 52a, a mono-black reanimator: adding ONE five-colour bomb moved
    `preflight` from READY to BLOCKED and the metrics floor from A to C — three bands,
    for a card working exactly as designed. Reanimator is not an exotic case; it is the
    reason `Zombify` and `Rise of the Dark Realms` are in the pool at all.

    Deliberately OPT-IN and per-card. Most uncastable cards really are mistakes, so the
    default stays a hard FAIL; this is the author making a specific claim, the same
    shape as `#: protect:` naming signature cards the tooling must not propose cutting.
    An exempt card is still SHOWN everywhere it was shown before — it moves out of the
    failure list, not out of sight (G-52: a verdict surface must print its evidence)."""
    return _header_card_keys(meta, "uncastable-ok")


def _signature_themes(meta, cards, cardmeta):
    """The themes carried by a deck's `#: protect:` cards — the human-designated
    SPINE. A theme here counts as the deck's signature even when it's otherwise
    'generic' (idf-low): a counters deck that protects two counter-doublers IS a
    counters deck, so a counter card is a KEY fit, not tangential. Corrects the idf
    blind spot where a broadly-common theme (counters/tokens/…) is THIS deck's actual
    plan. Empty when no `#: protect:` header is set (falls back to pure idf)."""
    prot = _protected(meta)
    if not prot:
        return frozenset()
    sig = set()
    for q, n, s, c in cards:
        if _ms_key(n) in prot:                 # G-63: `prot` holds _ms_key keys
            m = cardmeta.get(n.lower())
            if m:
                sig.update(m["synergies"])
    return frozenset(sig)


def cut_scoring_context(meta, cards, cardmeta, carddata):
    """The deck-level inputs a cut keep-score reads: theme weights, the central
    themes, the `#: protect:` spine, the deck's role tally (for saturation) and its
    creature-subtype counts. Split out so `rank_cut_candidates` and `_weakest_cut`
    build the SAME context from the same cards — see `cut_keep_score`."""
    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = cardmeta.get(n.lower())
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    sub_count = {}
    for q, n, s, c in cards:
        cd = carddata.get(n.lower())
        if cd:
            for st in creature_subtypes(cd["type"]):
                sub_count[st] = sub_count.get(st, 0) + q
    return {
        "cards": cards,
        "carddata": carddata,
        "theme_w": theme_w,
        "central": _central_themes(theme_w),
        # The STRICT spine (a theme carried by >=2 `#: protect:` cards), not the loose
        # union of every protected card's tags. Measured: the loose set fired the +2
        # keep-boost on **86%** of nonland cards across the 22 decks that declare
        # `#: protect:` — 100% in decks 20 and 46 — and a boost applied to every card in
        # a ranking is a constant, carrying no information where it saturates and applied
        # off a 25-theme union where it does not. The strict set fires on 66%.
        #
        # This is `check_suggest` anchor 11b's fix one caller over: that anchor forces
        # `cmd_suggest_homes` to hand `fit_strength` the strict set for the same reason
        # (the loose union gave 99 KEYs where the strict gives 54, every difference a
        # false KEY). The rescue this term exists for survives — deck 30's protected
        # counter-doublers give a strict signature of exactly `{counters}`, so a counters
        # card in a counters deck is still boosted.
        "signature": _strong_signature_themes(meta, cards, cardmeta),
        "deck_tally": role_tally(cards, carddata),
        "sub_count": sub_count,
    }


def cut_keep_score(ctx, tline, text, tags, rarity="", qty=1):
    """THE keep-score for "how cuttable is this card in this deck" — higher = keep.

    ONE definition, because there used to be two. `rank_cut_candidates` (what
    `deck.py cuts` prints, what `tier --to` pairs its adds against, and what the
    recommendation ledger scores a swap by) summed nine terms; `_weakest_cut` — the
    cut hint `suggest-homes` prints on every fit row — summed three of them, and
    matched none of the co-signals added since. They disagreed on **36 of 64 decks**,
    and the disagreements were not cosmetic: `suggest-homes` proposed cutting Bloom
    Tender from deck 17 and Vizier of the Menagerie from decks 34/36 — the roster's
    best fixers, and the exact cards the `_is_color_fixer` work was done to protect.

    This is the F-01 shape one more time, and the reason a pure-function anchor could
    not see it: every co-signal here (`_cuts_power_adj` / `_cuts_uniq_adj` /
    `_cuts_multiplier_adj`) is provably bounded and monotonic, and each is gated by a
    `check_suggest` anchor — but a second caller that never calls them is invisible to
    all of that. `check_agreement.py` now holds the two answers together on the live
    roster, which is the only place the divergence was ever visible.

    Returns (keep, parts) — `parts` carries the display pieces the cut table shows
    (fit, roles, power, uniq, the multiplier axis/support, the cost-as-upside flags)
    so the caller never recomputes one and drifts again."""
    theme_w, central = ctx["theme_w"], ctx["central"]
    fit, hit_central = 0, False
    for t in tags:
        if t in theme_w:
            fit += theme_w[t]
            if t in central:
                hit_central = True
    roles = classify_roles(text)
    subs = set(creature_subtypes(tline))
    tribal = sum(ctx["sub_count"].get(st, 0) for st in subs)
    upside = cost_upside_flags(text, central)
    sig_hit = bool(set(tags) & ctx["signature"])

    # Card-quality co-signal (#3): the wishlist's rarity+role power estimate, so an
    # on-theme-but-WEAK card sorts UP the cut list and an on-theme BOMB is protected —
    # something pure theme-fit can't distinguish (a vanilla and a bomb sharing one tag
    # look equal). Bounded (±_CUTS_POWER_CAP), so it only breaks near-ties (see
    # _cuts_power_adj / check_suggest #7); it never overrides theme fit.
    # NOTE: `rarity` comes from load_rarities() — Arena wildcard LETTERS ("M"/"R"/"U"/
    # "C"), not rarity words. wishlist._norm_rarity accepts both shapes; before it did,
    # every rare/mythic fell through to the default floor and seeded as an uncommon (F-01).
    power = _power_seed({"Rarity": rarity, "Card Text": text, "Type": tline})

    # Ability-distinctiveness co-signal: a generic-ability body (low pool tag-rarity)
    # sorts UP the cut list; a distinctive-mechanic card is mildly protected. Bounded
    # (±_CUTS_UNIQ_CAP) and orthogonal to power (see _cuts_uniq_adj / check_suggest #8).
    uniq = card_distinctiveness(tags, text)

    # Multiplier co-signal: a doubler is worth what it doubles, and neither theme-fit
    # nor role-credit can see that. Routed through the SAME doubler primitives
    # `suggest-homes` uses, so the two models can't disagree (see _cuts_multiplier_adj
    # / check_suggest #16).
    mult_axis = doubler_axis(text)
    mult_support = (doubler_support(mult_axis, ctx["cards"], ctx["carddata"],
                                    doubler_restriction(text))
                    if mult_axis else 0)

    # keep-score: higher = keep; cut candidates sort to the top (lowest keep).
    # Role credit is impact-weighted (see _role_credit) so a strong-but-off-theme
    # card (removal/engine/cost-reducer) isn't mis-ranked as a top cut. Passing the
    # deck's role tally makes that credit SATURATION-aware (#1): a redundant piece
    # (the 8th removal spell) loses most of its bonus and sorts UP the cut list,
    # while the deck's ONLY counterspell keeps full credit and stays protected. A
    # card on the deck's #: protect: signature theme gets a further keep-boost (F#3)
    # so a generic-tagged-but-central theme (e.g. counters) isn't mistaken for filler.
    keep = (fit + _role_credit(roles, ctx["deck_tally"]) + (1 if hit_central else 0)
            + (2 if sig_hit else 0) + min(tribal, 6)
            + _cuts_power_adj(power) + _cuts_uniq_adj(uniq)
            + _cuts_multiplier_adj(mult_support, mult_axis))

    reasons = []
    if tags and not hit_central:
        reasons.append("off the deck's central themes")
    elif not tags:
        reasons.append("no synergy tags")
    if not roles:
        reasons.append("role not auto-detected — read text")
    if subs and tribal <= qty:
        reasons.append("off-tribe")
    if power <= 3.0 and (hit_central or sig_hit):
        reasons.append(f"on-theme but low power (~{power:.1f})")
    if uniq <= 1.5 and not sig_hit:
        reasons.append("generic ability — trips broad synergy checks")

    return keep, {"fit": fit, "roles": roles, "power": power, "uniq": uniq,
                  "upside": upside, "reasons": reasons, "tribal": tribal,
                  "is_int": bool(set(roles) & _INTERACTION_ROLES),
                  "mult": (mult_axis, mult_support)}


def _cut_feeds_axis(cut_row, axis):
    """Does this cut candidate itself supply the axis the tune plan is trying to RAISE?
    `cut_row` is a `rank_cut_candidates` row: index 3 is the role set, index 8 the
    once-per-card interaction flag `role_tally` computes."""
    if axis == "interaction":
        return bool(cut_row[8])
    return "Card advantage" in (cut_row[3] or set())


def pair_adds_with_cuts(adds, cut_pool):
    """Pair each tune-plan filler with the weakest-fit cut that does NOT feed that
    filler's own axis. Returns [(add, cut)].

    This was `zip(adds, cut_pool)` — a positional pairing blind to what the cut does. So
    a plan closing an INTERACTION gap could propose cutting an interaction card: the two
    cancel, the projected floor comes back short, and the reader is told to "pick another
    cut" for a choice the tool had all the information to make itself. Measured
    2026-08-24: 3 of the 11 decks with an assembled `--to A` plan contained such a pair
    (22, 43, 61), and deck 43's was hit live — it offered −Bitter Triumph / +An Offer You
    Can't Refuse, both interaction, a net zero.

    A cut is consumed once, so the two axes cannot both claim the same card. When nothing
    axis-neutral is left the weakest remaining cut is used anyway, preserving the old
    behaviour AND its warning: a plan with a flagged compromise is more useful than a
    silently truncated one, and this is exactly where the human judgement the command
    reserves belongs.

    The RAMP warning is deliberately NOT filtered on. Losing a mana source is an
    editorial trade-off, not an arithmetic contradiction — the plan does not get more
    correct by avoiding it, so it stays a warning."""
    remaining = list(cut_pool)
    out = []
    for a in adds:
        if not remaining:
            break
        axis = a[0]
        idx = next((i for i, c in enumerate(remaining)
                    if not _cut_feeds_axis(c, axis)), 0)
        out.append((a, remaining.pop(idx)))
    return out


def rank_cut_candidates(d):
    """Rank a deck's nonland cards most→least cuttable and return
    (rows_sorted, central, prot_present, deck_int). Each row is
    (keep, name, mv, roles, fit, reasons, ctx, text, is_int, power) — the shared
    ranking behind both `cmd_cuts` (which prints it) and the tier `--to` tune plan
    (which pairs the weakest cuts with the fillers that close a tier gap). Higher
    `keep` = keep; lower sorts to the top of the cut list.

    Scores each card through the shared `cut_keep_score`, which `_weakest_cut` also
    uses — the two answers to "this deck's most-cuttable card" used to be computed by
    separate formulas and disagreed on 36 of 64 decks."""
    meta, cards = parse_deck_file(d["path"])
    protected = _protected(meta)
    cardmeta = load_card_meta()
    carddata = load_card_data()
    mana = load_mana()
    rar = load_rarities()

    sctx = cut_scoring_context(meta, cards, cardmeta, carddata)
    central = sctx["central"]
    deck_int = sctx["deck_tally"]["interaction"]           # for the F#1 interaction guard

    rows, seen, prot_present = [], set(), []
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS or nl in seen:
            continue
        if _ms_key(n) in protected:            # G-63: `protected` holds _ms_key keys
            prot_present.append(n)
            seen.add(nl)
            continue
        cd = carddata.get(nl)
        tline = (cd["type"] if cd else "") or ""
        if "Land" in _primary_type(tline):
            continue
        seen.add(nl)
        tags = cardmeta.get(nl, {}).get("synergies", [])
        text = cd["text"] if cd else ""
        cost, mv = (mana.get(nl) or (None, None))
        ctx = context_flags(text, cost)
        keep, p = cut_keep_score(sctx, tline, text, tags, rarity=rar.get(nl, ""), qty=q)
        rows.append((keep, n, mv, sorted(p["roles"]), p["fit"], p["reasons"], ctx, text,
                     p["is_int"], p["power"], p["uniq"], p["upside"], p["mult"]))

    rows.sort(key=lambda r: (r[0], r[1].lower()))
    return rows, central, prot_present, deck_int


def cmd_cuts(args):
    """Rank the deck's nonland cards from most to least cuttable — the counterpart
    to `suggest` (which proposes adds). Heuristic from data the rest of the tooling
    already computes: a card is more cuttable when it sits OFF the deck's central
    themes, fills no functional role, and (in a tribal deck) shares no creature type
    the deck runs in numbers. Transparent by design — it shows the components so you
    judge, and it does NOT know your spice/signature cards, so read it as a
    shortlist, not a verdict."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    rows, central, prot_present, deck_int = rank_cut_candidates(d)
    # Ledger read is DISPLAY-only (see recent_ledger_adds) — never inside the ranking.
    try:
        _newcomers = recent_ledger_adds(d["id"])
    except Exception:
        _newcomers = set()
    if not rows:
        print(f"Deck {d['id']}: no nonland cards to evaluate.")
        return 0
    limit = args.limit if getattr(args, "limit", 0) and args.limit > 0 else len(rows)

    print(f"Deck {d['id']}: {d['name'] or d['path']} — cut candidates (weakest fit first)")
    print(f"Central themes: {', '.join(sorted(central)) or '(none)'}")
    if prot_present:
        print(f"Protected (kept OFF the cut list via #: protect:): {'; '.join(prot_present)}")
    print("Heuristic shortlist — read the text; it can't see spice/signature cards "
          "beyond the #: protect: header.\n")
    if deck_int < 5:
        print(f"⚠ deck runs only {deck_int} interaction piece(s) — rows tagged "
              f"⚠interaction are your removal/counters; cutting them lowers resilience.")
    # Zone conflicts (the mirror of ⚡): a card that EMPTIES a graveyard this deck needs
    # populated. Computed once for the deck and looked up by name, so the row tuple stays
    # the shape every other reader expects.
    _zmeta, _zcards = parse_deck_file(d["path"])
    _zconf = {nm: (scope, why, hit) for nm, scope, why, hit
              in zone_conflict_flags(_zcards, load_card_data())}
    if _zconf:
        # NAME them here rather than only tagging the row: `cuts` shows 8 rows by default
        # and a conflicted card can rank anywhere, so a header that just says "1 card"
        # can point below the fold — which is the same "the shortlist saw it but nobody
        # could tell why" failure this flag exists to fix.
        print(f"⛔ {len(_zconf)} card(s) FIGHT this deck's own engine — a good card that "
              f"empties a zone your plan needs FULL:")
        for _zn, (_sc, _why, _hit) in sorted(_zconf.items()):
            print(f"     {_zn} — {_why}")
            print(f"       needs it populated: {', '.join(_hit[:4])}"
                  + (f" … (+{len(_hit) - 4})" if len(_hit) > 4 else ""))
        print()
    # WHICH AXIS IS ACTUALLY SHORT. The `⚠interaction (deck runs N)` note below says a
    # removal card is redundant, and on deck 52a — whose measured weakness is its CURVE
    # (4.22 average, 12 early drops) — that hint put four ONE-MANA removal spells at the
    # top of the cut list. Trimming cheap cards from a deck that is too slow is backwards.
    # `tier --to` and `suggest --needs` both know what a deck is short on; `cuts` did not,
    # so it optimised the axis it could see. Stated rather than scored — the ranking is a
    # shortlist and this is the context that makes it readable.
    _vec = deck_quality_vector(d)
    _short = []
    if _vec["interaction"] < 5:
        _short.append(f"interaction {_vec['interaction']}")
    if _vec["card_advantage"] < 3:
        _short.append(f"card advantage {_vec['card_advantage']}")
    if _vec.get("early_drops", 99) < 18:
        _short.append(f"early drops {_early_drops_note(_vec)} (avg MV {_vec['avg_mv']})")
    if _short:
        print(f"  ⓘ This deck is short on {', '.join(_short)} — weigh a `⚠interaction` note "
              "against that before cutting a cheap card from an axis you are not long on.")
    print(f"  {'Card':30} {'MV':>3}  {'Fit':>4}  {'Pw':>3}  {'Uq':>3}  Roles / why-cuttable")
    print("-" * 82)
    for (keep, n, mv, roles, fit, reasons, ctx, text, is_int, power, uniq, upside,
         mult) in rows[:limit]:
        mvs = str(mv) if mv is not None else "?"
        tail = ", ".join(roles) if roles else ("; ".join(reasons) if reasons else "—")
        low_pow = [r for r in reasons if r.startswith("on-theme but low power")]
        if roles and low_pow:  # a detected-role card can still be a weak body — say so
            tail += "  ·  " + low_pow[0]
        gen = [r for r in reasons if r.startswith("generic ability")]
        if roles and gen:  # a detected-role card can still be generic templating — say so
            tail += "  ·  " + gen[0]
        if ctx:
            tail += f"   ⚠ context: {'/'.join(ctx)}"
        if is_int:
            tail += f"   ⚠interaction (deck runs {deck_int})"
        # A card whose COST this deck turns into an upside is easy to mis-cut: every
        # model here grades it in isolation, where the cost reads as a drawback.
        if upside:
            tail += f"   ⚡cost-as-upside HERE ({upside[0]})"
        # The MIRROR: a card that reads fine alone but works AGAINST this deck's plan.
        if n in _zconf:
            tail += f"   ⛔fights your engine ({_zconf[n][1]})"
        # A MULTIPLIER: its value is in the rest of the deck, which is exactly what the
        # fit and role columns cannot show. Named so a keep-reason is legible, not just
        # baked into the score.
        if mult[0] and mult[1]:
            tail += f"   ✱multiplier — doubles {mult[0]} ({mult[1]} feeder(s) here)"
        # A card whose VALUE is a function of a deck property reads as its FLOOR here, so
        # it sorts up the cut list on a number that is not what you would cast it for:
        # Cat-Gator scores as a 7-mana 3/2 lifelink when its ETB is damage equal to your
        # Swamp count (24 in deck 52a). `suggest --needs` already flags this shape with
        # `⚠ scales w/`; `cuts` had no equivalent, so the same card was graded two ways by
        # two commands. FLAG only — the axis is fuzzy, and a score change on a fuzzy signal
        # is exactly what this file keeps having to undo.
        _ax = _int_scaling(text) or _deck_state_axis(text)
        if _ax:
            tail += f"   ⌁scales w/ {_ax} — graded here at its FLOOR"
        # Right after a tune, the freshly added structural cards dominate this list —
        # their tag profiles are thin by nature, not by weakness (K-04's shape).
        if _ms_key(n) in _newcomers:
            tail += ("   ✚ NEWCOMER — added by a swap in the last 14d; "
                     "tag-fit under-reads it, not a cut signal")
        print(f"  {n[:30]:30} {mvs:>3}  {fit:>4}  {power:>3.0f}  {uniq:>3.0f}  {tail}")

    # Surface the actual oracle text so a cut is graded from what the card DOES,
    # never from the label above (the role map is a shortlist, not a verdict).
    import textwrap
    # `--limit 0` documents itself as "0 = all", and the TABLE honours it (limit =
    # len(rows) above) — while this line silently capped the oracle block at 12 and
    # then announced "the top 12", so the one flag you reach for to see EVERYTHING
    # left 23 of the printed rows with no text, presented as if 12 were what you
    # asked for. G-09/G-52 make printing the evidence the load-bearing property of
    # `cuts` (broad-scan Batch G). Same expression as the table's, deliberately.
    text_n = args.limit if getattr(args, "limit", 0) and args.limit > 0 else limit
    print(f"\n── Oracle text of the top {min(text_n, len(rows))} cut candidates "
          f"(grade from THIS, not the label) ──")
    for (keep, n, mv, roles, fit, reasons, ctx, text, is_int, power, uniq, upside,
         _mult) in rows[:text_n]:
        warn = f"   ⚠ context: {'/'.join(ctx)} — value depends on this deck" if ctx else ""
        if is_int:
            warn += f"   ⚠interaction — 1 of the deck's {deck_int}"
        for u in upside:
            warn += f"\n    ⚡ cost-as-upside in THIS deck: {u}"
        if n in _zconf:
            _sc, _why, _hit = _zconf[n]
            warn += (f"\n    ⛔ FIGHTS YOUR ENGINE: {_why} — "
                     f"{', '.join(_hit[:4])}{' …' if len(_hit) > 4 else ''}")
        print(f"\n• {n}{warn}")
        for para in (text or "(no oracle text on file)").split("\n"):
            for line in (textwrap.wrap(para, width=86) or [""]):
                print(f"    {line}")
    print(f"\nRead the text above before cutting — the ranking is a shortlist, not a "
          f"verdict, and can't see spice/signature cards. Pair with "
          f"`deck.py suggest {d['id']}` for adds; preview a swap with "
          f"`deck.py swap {d['id']} --cut <weak> --add <pick>` (shows full text of both).")
    return 0


def cmd_verify(args):
    """Compare a pasted/piped Arena export against a stored deck and report either
    'identical' or a +/- differential by card. Case-insensitive, quantity-aware,
    and printing-fungible — a different printing (or basic-land art) of the same
    card counts as a match, since Arena copies are fungible across printings."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    try:
        text = sys.stdin.read() if args.source == "-" else open(args.source, encoding="utf-8").read()
    except OSError as e:
        eprint(f"Could not read {args.source!r}: {e}")
        return 1
    from import_arena import parse as parse_arena
    # A multi-deck paste merges into ONE multiset here: `parse_arena` treats a bare
    # `Deck` marker as a section header, not a separator, so pasting a full multi-deck
    # export at `verify <id>` reports the rest of the collection as `+N` additions.
    # `sync` splits blocks (split_paste); `verify` never did, and it already warns
    # about a Sideboard section, which is why the omission read as an oversight rather
    # than a decision (broad-scan Batch G). Report-only, so this is a warning, not a
    # refusal — the same shape as the sideboard note below it.
    if len(split_paste(text)) > 1:
        eprint(f"WARN:  the paste contains {len(split_paste(text))} `Deck` blocks — "
               f"`verify` compares ONE deck and merges them all into a single list, so "
               f"the extra blocks will read as additions. Paste deck {d['id']} alone, "
               f"or use `deck.py sync` for a multi-deck paste.")
    entries, warnings = parse_arena(text)
    for w in warnings:
        eprint(f"WARN:  {w}")
    if not entries:
        eprint("No card lines found in the pasted export.")
        return 1

    stored_cards = parse_deck_file(d["path"])[1]
    stored = _multiset(stored_cards)
    pasted = _multiset(entries)
    print(f"Deck {d['id']}: {d['name'] or d['id']} — vs pasted export")
    print("-" * 48)
    if "sideboard" in {ln.strip().lower() for ln in text.splitlines()}:
        eprint("Note: the export has a Sideboard section — its cards are included "
               "in this comparison (stored decks are maindeck-only).")
    added = removed = 0
    diffs = []
    for nl in sorted(set(stored) | set(pasted)):
        sd, pd = stored.get(nl, (None, 0)), pasted.get(nl, (None, 0))
        disp = pd[0] or sd[0]
        if pd[1] > sd[1]:
            diffs.append(f"  +{pd[1] - sd[1]}  {disp}")
            added += pd[1] - sd[1]
        elif sd[1] > pd[1]:
            diffs.append(f"  -{sd[1] - pd[1]}  {disp}")
            removed += sd[1] - pd[1]
    if not added and not removed:
        s_total = sum(q for q, *_ in stored_cards)
        print(f"  ✓ identical — the pasted export matches deck {d['id']} ({s_total} cards).")
        return 0
    for ln in diffs:
        print(ln)
    print("-" * 48)
    print(f"  {added} added, {removed} removed vs the stored deck")
    print("  (+ = the paste has more, − = the repo has more; compared by card name/qty "
          "— printings & basic-land art are the same card.)")
    return 1


# --- sync: reconcile stored decks FROM a multi-deck Arena paste -------------- #
# `verify` answers "did deck N drift?" for ONE deck you already identified, and the
# dashboard's stale-check answers it for many — but neither WRITES, so the actual repair
# was always "read a diff, then hand-edit N files". `sync` closes that loop: paste
# everything you exported from Arena, and it matches each block to its stored deck and
# reconciles the files. The matching rule is deliberately identical to the dashboard
# panel's (closest by total drift, with a shared-card floor and a low-confidence flag),
# since the two answer the same question; that JS copy can't share this code, so any
# change here belongs there too (build_dashboard.py, the stale-deck compare block).
_DECK_MARKER_RE = re.compile(r"^deck\s*$", re.I)


def strip_boards(block):
    """(maindeck_lines, board_card_count) for one pasted block: drop the lines under a
    `Sideboard` / `Maybeboard` heading, counting the card COPIES dropped.

    `import_arena.parse` skips section HEADINGS but keeps their card lines — the right
    call for an ownership import (a sideboard card is owned) and wrong for `sync`, the
    WRITE half: stored decks are maindeck-only, so an in-sync deck exported with a
    7-card sideboard read "drifted: 7 added" and `--apply` wrote those cards into the
    60. `verify`, the READ half, had warned about exactly this since it shipped; the
    write half didn't even detect it (broad-scan BS-07). Commander / Companion
    sections are KEPT — a stored Brawl deck lists its commander among the 100."""
    from import_arena import SECTIONS, LINE_RE as _ALINE
    keep, dropped_n, skipping = [], 0, False
    for ln in block:
        s = ln.strip().lower()
        if s in SECTIONS:
            skipping = s in ("sideboard", "maybeboard")
            keep.append(ln)               # headings are skipped by parse either way
            continue
        if skipping:
            m = _ALINE.match(ln.strip())
            if m:
                dropped_n += int(m.group(1))
            continue
        keep.append(ln)
    return keep, dropped_n


def split_paste(text):
    """An Arena paste containing one or MANY decks -> a list of line-blocks. Arena
    exports start each deck with a bare `Deck` line; text before the first one is
    treated as its own block, so a single-deck paste with no marker still works."""
    segs, cur = [], None
    for ln in (text or "").splitlines():
        if _DECK_MARKER_RE.match(ln.strip()):
            cur = []
            segs.append(cur)
            continue
        if cur is None:
            cur = []
            segs.append(cur)
        cur.append(ln)
    return [s for s in segs if any(x.strip() for x in s)]


def _ms_diff(pasted, stored):
    """(added, removed, diffs) between two `_multiset`s — `+` = the paste has more."""
    added = removed = 0
    diffs = []
    for nl in sorted(set(pasted) | set(stored)):
        p = pasted.get(nl, (None, 0))[1]
        s = stored.get(nl, (None, 0))[1]
        disp = pasted.get(nl, (None, 0))[0] or stored.get(nl, (None, 0))[0] or nl
        if p > s:
            added += p - s
            diffs.append(("+", p - s, disp))
        elif s > p:
            removed += s - p
            diffs.append(("-", s - p, disp))
    return added, removed, diffs


def paste_format_hint(block, total):
    """``'commander' | 'sixty' | None`` — one pasted block's STRUCTURAL format signal.

    A Brawl/Commander export names its commander under a ``Commander`` heading, and
    failing that its ~100-card size still says commander-shaped; a 60-card constructed
    export says sixty. ``None`` when the block is ambiguous (76–89 cards, no heading),
    so the matcher falls back to pure drift — the pre-hint behavior. This exists
    because a Standard deck and its Brawl sibling share most card NAMES: matching on
    drift alone put deck 3 and 3-brawl inside each other's low-confidence window, when
    the paste itself said unambiguously which family it belonged to."""
    for ln in block:
        if ln.strip().lower() == "commander":
            return "commander"
    if total >= 90:
        return "commander"
    if 0 < total <= 75:
        return "sixty"
    return None


def _deck_format_class(d):
    """'commander' | 'sixty' | None for a stored deck record — from `#: format:`."""
    fmt = ((d.get("meta") or {}).get("format") or d.get("format") or "").strip().lower()
    if not fmt:
        return None
    return "commander" if fmt in ("brawl", "commander", "historic brawl") else "sixty"


def match_paste(pasted, decks, fmt_hint=None):
    """Best stored deck for one pasted block (Arena exports carry no deck name).

    `decks` is [(deck_record, multiset)]. Returns a dict describing the match, or
    ``{'unmatched': True}`` when nothing is close enough. Same rule as the dashboard:
    minimise total drift; require the block to share at least max(3, 30% of its distinct
    cards) with the deck, so an unrelated paste doesn't get force-fitted; flag LOW
    CONFIDENCE when the runner-up is within 2 drift and nearly as many shared cards
    (variants of one core deck look alike, and picking the wrong sibling would rewrite
    the wrong file).

    ``fmt_hint`` (from `paste_format_hint`) is the FORMAT tie-breaker: a deck whose
    `#: format:` class contradicts the paste's structural signal sorts behind every
    format-consistent candidate, and a format-mismatched rival never triggers the
    low-confidence flag — a Standard 60 and its Brawl sibling share most card names,
    and drift alone had them confusing the matcher for exactly that reason. A deck
    with no `#: format:` header is never penalized (unknown ≠ mismatch)."""
    uniq = len(pasted)
    ranked = []
    for d, ms in decks:
        added, removed, diffs = _ms_diff(pasted, ms)
        shared = sum(1 for nl in pasted if nl in ms)
        cls = _deck_format_class(d)
        mm = 1 if (fmt_hint and cls and cls != fmt_hint) else 0
        ranked.append({"deck": d, "drift": added + removed, "shared": shared,
                       "added": added, "removed": removed, "diffs": diffs, "_mm": mm,
                       "_ms": ms})
    if not ranked:
        return {"unmatched": True, "uniq": uniq}
    ranked.sort(key=lambda r: (r["_mm"], r["drift"], -r["shared"], r["deck"]["id"]))
    best = ranked[0]
    if best["shared"] < max(3, uniq * 0.3):
        return {"unmatched": True, "uniq": uniq}
    runner = next((r for r in ranked[1:] if r["_mm"] == best["_mm"]), None)
    best["lowconf"] = bool(runner and runner["drift"] - best["drift"] <= 2
                           and runner["shared"] >= best["shared"] * 0.8)
    best["runner_up"] = runner["deck"] if (runner and best["lowconf"]) else None
    best["sync"] = best["drift"] == 0
    best["uniq"] = uniq
    # TRUNCATION guard (broad-scan BS2-01). The shared-card floor above is measured
    # against the PASTE, so a partial paste — a strict subset of its deck — passes it
    # trivially, matches with full confidence, and `--apply` would rewrite the stored
    # 60 down to the fragment (reproduced: the first 8 lines of deck 52 dry-ran as
    # "0 added / 52 removed", not low-confidence). An Arena export is always the WHOLE
    # deck, and the largest legitimate shrink a sync performs is trimming an oversized
    # draft (64→60 ≈ 0.94 of the stored total), so a paste under 75% of the stored
    # total is a fragment, not an edit. Flag, don't unmatch: the match itself is
    # usually RIGHT — it is the write that must not happen (cmd_sync skips it unless
    # --force, the same handling as a low-confidence sibling match).
    best["paste_total"] = sum(q for _disp, q in pasted.values())
    best["deck_total"] = sum(q for _disp, q in best["_ms"].values())
    best["truncated"] = best["paste_total"] < best["deck_total"] * 0.75
    for r in ranked:
        del r["_ms"]
    return best


def reconcile_lines(lines, target, printings):
    """Rewrite a deck file's raw lines so its card list becomes `target` (a `_multiset`).

    Line-level editing, like `_swap_edit_lines`: an existing card line keeps its printing
    and section position and only its QUANTITY changes, a card no longer in the list has
    its line dropped, and genuinely new cards are appended after the last card line — so
    `# Creatures` / `# Lands` comments, the `#:` header and `#~` flex lines all survive.
    A card split across two printing lines has its whole quantity assigned to the first
    and the rest dropped, matching `_multiset`'s printing-fungible view.

    Existing lines are matched on `_ms_key` — the SAME front-face-normalized key
    `_multiset` builds `target` with. Keying the file side on the raw name while the
    target side is normalized would make every `Front // Back` line look absent: its
    line would be dropped and a fresh one appended, silently rewriting the stored
    spelling and moving the card out of its `# section` (broad-scan F-02)."""
    remaining = {nl: q for nl, (_disp, q) in target.items()}
    out, last_card = [], -1
    for ln in lines:
        nm = _card_line_name(ln)
        if nm is None:
            out.append(ln)
            continue
        nl = _ms_key(nm)
        want = remaining.pop(nl, None)
        if not want:
            continue                      # dropped from the deck (or a consumed 2nd line)
        m = LINE_RE.match(ln.split("#", 1)[0].strip())
        indent = ln[:len(ln) - len(ln.lstrip())]
        rebuilt = f"{indent}{want} {m.group(2).strip()}"
        if m.group(3):
            rebuilt += f" ({m.group(3).strip()})" + (f" {m.group(4).strip()}" if m.group(4) else "")
        out.append(rebuilt + _line_comment(ln))
        last_card = len(out) - 1
    new = []
    for nl, q in remaining.items():
        if not q:
            continue
        disp, setc, coll = printings.get(nl, (target[nl][0], "", ""))
        # `printings` is keyed front-face too, and for a DFC the LIBRARY row wins there —
        # and the library stores the front name alone. Writing that bare name back is the
        # P8 failure (parses, passes INV-04 and `legal`, fails an Arena import), so let
        # the fuller of the two spellings decide, exactly as `_multiset` does.
        disp = _ms_display(disp, target[nl][0])
        line = f"{q} {disp}"
        if setc:
            line += f" ({setc})" + (f" {coll}" if coll else "")
        new.append(line)
    at = last_card + 1 if last_card >= 0 else len(out)
    return out[:at] + sorted(new) + out[at:]


def cmd_sync(args):
    """Reconcile stored deck files FROM a pasted Arena export — the write half of
    `verify`. Dry-run by default; `--apply` writes each drifted deck with a `.bak` and
    the INV-04 re-check."""
    try:
        text = sys.stdin.read() if args.source == "-" else open(args.source, encoding="utf-8").read()
    except OSError as e:
        eprint(f"Could not read {args.source!r}: {e}")
        return 1
    from import_arena import parse as parse_arena
    blocks = split_paste(text)
    if not blocks:
        eprint("No deck blocks found in the paste.")
        return 1

    # Roster only (BS-14): an `example`/`retired` deck must not be a sync match
    # target — a low-confidence paste match could rewrite a retired list. A
    # non-roster deck can still be verified/edited directly by id.
    decks = [(d, _multiset(parse_deck_file(d["path"])[1])) for d in roster_decks()]
    printings = _printing_index()
    results, rc, unmatched = [], 0, 0
    claimed = {}                       # deck id → block number that matched it first
    print(f"Sync — {len(blocks)} pasted deck block(s) vs {len(decks)} stored decks\n")
    for i, block in enumerate(blocks, 1):
        # Maindeck only: stored decks carry no sideboard, so board cards must not
        # read as drift — or be written into the file on --apply (BS-07).
        block, board_n = strip_boards(block)
        if board_n:
            print(f"  (block {i}: ignoring {board_n} sideboard/maybeboard card(s) — "
                  "stored decks are maindeck-only)")
        entries, warnings = parse_arena("\n".join(block))
        for w in warnings:
            eprint(f"WARN:  block {i}: {w}")
        if not entries:
            continue
        pasted = _multiset(entries)
        hint = paste_format_hint(block, sum(q for q, *_ in entries))
        m = match_paste(pasted, decks, fmt_hint=hint)
        if m.get("unmatched"):
            n = sum(q for q, *_ in entries)
            print(f"  ? block {i}: {n} cards, {m['uniq']} unique — no close stored deck "
                  "(a new deck? add it with /add-deck).")
            unmatched += 1
            rc = 1
            continue
        d = m["deck"]
        label = f"#{d['id']} {d['name'] or d['id']}"
        # ONE stored deck per paste (broad-scan BS2-10). Blocks are matched
        # independently, so two blocks can both resolve to the same deck — pasting a
        # 52/52a family where one variant is retired makes both blocks legitimately
        # match the survivor — and the write loop then wrote the file TWICE, the
        # second write clobbering the first with only an intermediate .bak between
        # them. The low-confidence rule compares a block against runner-up DECKS,
        # never blocks against each other, so it cannot see this. First claim wins;
        # later blocks are reported and skipped (re-paste separately to choose).
        if d["id"] in claimed:
            print(f"  ✗ block {i}: ALSO matched {label}, already claimed by block "
                  f"{claimed[d['id']]} — skipped. If this block is the real list, "
                  "re-paste it alone; two blocks matching one deck usually means a "
                  "variant is retired or renamed.")
            unmatched += 1
            rc = 1
            continue
        claimed[d["id"]] = i
        if m["sync"]:
            print(f"  ✓ {label} — in sync")
            continue
        rc = 1
        conf = (f"   ⚠ low confidence — #{m['runner_up']['id']} is nearly as close"
                if m.get("runner_up") else "")
        if m.get("truncated"):
            conf += (f"   ⚠ TRUNCATED? paste holds {m['paste_total']} cards vs the "
                     f"stored {m['deck_total']} — looks like a partial paste, not an edit")
        print(f"  ⟳ {label} — drifted: {m['added']} added / {m['removed']} removed{conf}")
        for sign, qty, nm in m["diffs"]:
            print(f"        {sign}{qty}  {nm}")
        results.append((d, pasted, m))

    if not results:
        print("\nEvery matched deck is already in sync. ✓")
        return rc
    if not getattr(args, "apply", False):
        print(f"\n(dry run — {len(results)} deck file(s) would be rewritten to match the "
              "paste; pass --apply to write, each with a .bak)")
        return rc
    failures = 0
    for d, pasted, m in results:
        if m.get("lowconf") and not getattr(args, "force", False):
            eprint(f"  ✗ #{d['id']}: skipped — low-confidence match (#{m['runner_up']['id']} "
                   "is nearly as close). Re-paste that deck alone, or pass --force.")
            failures += 1
            continue
        if m.get("truncated") and not getattr(args, "force", False):
            eprint(f"  ✗ #{d['id']}: skipped — the paste holds {m['paste_total']} cards "
                   f"against the stored {m['deck_total']}, which looks like a TRUNCATED "
                   "paste, not a deck edit; writing it would discard the rest of the "
                   "list. Re-paste the full export, or pass --force for a deliberate cut.")
            failures += 1
            continue
        with open(d["path"], encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        try:
            new_lines = reconcile_lines(lines, pasted, printings)
            bak = _safe_write_lines(d["path"], new_lines,
                                    sum(q for _disp, q in pasted.values()))
        except ValueError as e:
            eprint(f"  ✗ #{d['id']}: not saved — {e}")
            failures += 1
            continue
        print(f"  ✓ #{d['id']}: wrote {os.path.relpath(d['path'], REPO_ROOT)} "
              f"(backup: {os.path.basename(bak)})")
    print("\nRe-check with `deck.py check <id>` / `deck.py preflight <id>`.")
    # Drift DETECTED is the right non-zero for the dry run ("differences exist") and
    # the wrong one for the write half: a fully successful --apply repair exited 1,
    # so a scripted caller read a clean sync as failure (broad-scan batch 5). After
    # --apply, non-zero means something still needs attention: an unmatched block,
    # a low-confidence skip, or a failed write.
    return 1 if (unmatched or failures) else 0


def _interaction_count(cards, carddata):
    """Copies of nonland spells that do removal / sweeping / countering — the same
    'interaction total' cmd_stats reports and the same number the quality/tier vector
    uses, all via the canonical `role_tally` so the three can't drift."""
    return role_tally(cards, carddata)["interaction"]


AUDIT_ORDER = {"TUNE": 0, "craft": 1, "review": 2, "ok": 3}

# Competitive power tier (from the deck's `#: tier:` header) — a win-capability
# grade separate from the maintenance-health verdict. S strongest → D weakest;
# "" (ungraded) sorts last.
TIER_ORDER = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4, "": 5}


def _deck_tier(meta):
    """The competitive tier LETTER (S/A/B/C/D) from a deck's `#: tier:` header,
    or '' if ungraded. The header is `#: tier: B — one-line rationale`; we keep
    only the leading letter so the audit can column/sort on it."""
    raw = (meta.get("tier") or "").strip()
    m = re.match(r"([SABCD])\b", raw)
    return m.group(1) if m else ""


def audit_deck(d, *, by_name_qty, carddata, mana, leg, cmeta, played=None):
    """Score one deck for the roster triage — the structured core shared by
    `cmd_audit` (CLI table) and build_dashboard.py (the roster Audit view), so the
    two can't drift. Pass the big lookups (collection / card data / mana / legalities
    / card meta) in pre-loaded so a whole-roster pass reads each CSV once. Returns a
    dict of raw counts + a verdict (TUNE / craft / review / ok) + human reasons; each
    caller renders its own cells. Offline — no Scryfall.

    `played` ({deck_id: matches}, from `load_match_counts`) is OPTIONAL and defaults to
    an empty map, so a caller that predates it — and a repo with no matches.csv, which
    is the healthy default state — keeps working unchanged. It is REPORT-ONLY and must
    stay so: it never reaches `verdict`, `reasons` or any threshold. Feeding outcome
    data into a structural triage at these sample sizes would let 2 games re-sort the
    roster, which is the failure `_MIN_SAMPLE` and the protection axis (G-25) are both
    kept out of scoring to avoid."""
    meta, cards = parse_deck_file(d["path"])
    fmt = (meta.get("format") or "").strip().lower()

    # Ownership: unique cards that are missing or short of the deck's need.
    need = {}
    for q, n, s, c in cards:
        need[n.lower()] = need.get(n.lower(), 0) + q
    short = 0
    for nl, req in need.items():
        disp = next(n for q, n, s, c in cards if n.lower() == nl)
        have, found = owned(by_name_qty, disp)
        if not found or have < req:
            short += 1

    rep = legality_report(meta, cards, fmt, leg, carddata=carddata)
    n_illegal = len(rep["problems"])

    declared = _declared_colors(meta)
    # `off_ability` — NOT `off_ident` — drives the verdict. A stray explained by a
    # hybrid pip is a card you pay on-color and never need to look at, and counting
    # those fired `review` on 22 of 63 decks with a 0% actionable rate (F-03).
    uncast, off_ident, off_ability, _intended = _castability(
        cards, declared, mana, carddata, _uncastable_ok(meta))

    interaction = _interaction_count(cards, carddata)

    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = cmeta.get(n.lower())
        if not m:
            continue
        for t in m["synergies"]:
            theme_w[t] = theme_w.get(t, 0) + q
    n_themes = len(_central_themes(theme_w))

    # Verdict: hard problems first (a tune target), then unbuilt, then soft.
    thin = interaction < (5 if rep["min_size"] >= 100 else 3)
    reasons = []
    if n_illegal:
        reasons.append(f"illegal ×{n_illegal}")
    if uncast:
        reasons.append(f"uncastable ×{len(uncast)}")
    if n_illegal or uncast:
        verdict = "TUNE"
    elif short:
        verdict = "craft"
        reasons.append(f"{short} to craft")
    elif off_ability or thin:
        verdict = "review"
        if off_ability:
            reasons.append(f"off-color ability ×{len(off_ability)}")
        if thin:
            reasons.append(f"thin interaction ({interaction})")
    else:
        verdict = "ok"

    return {
        "id": d["id"],
        "name": (d["name"] or os.path.basename(os.path.dirname(d["path"])) or d["id"]),
        "tier": _deck_tier(meta),
        "sz": rep["total"],
        "short": short,
        "illegal": n_illegal,
        "uncast": len(uncast),
        "stray": len(off_ident),
        # The actionable subset of `stray` — the only one that reaches the verdict.
        # `stray` stays the TOTAL so the Cast column keeps agreeing with `deck.py mana`.
        "stray_ability": len(off_ability),
        "int": interaction,
        "thm": n_themes,
        "thin": thin,
        # REPORT-ONLY — deliberately below `verdict`, which is computed above and never
        # reads it. See the docstring.
        "played": (played or {}).get(d["id"], 0),
        "verdict": verdict,
        "why": ", ".join(reasons),
    }


def audit_roster():
    """Score every deck for the roster triage — loads each reference CSV once, then
    runs audit_deck per deck. Returns the list of row dicts (unsorted, discovery
    order). Shared by the CLI and the dashboard."""
    decks = roster_decks()
    refs = dict(by_name_qty=load_collection()[2], carddata=load_card_data(),
                mana=load_mana(), leg=load_legalities(), cmeta=load_card_meta(),
                played=load_match_counts())
    return [audit_deck(d, **refs) for d in decks]


def cmd_audit(args):
    """Roster-wide triage scorecard — one cheap, OFFLINE line per deck so you can see
    which decks actually need a full (expensive) tune-deck pass instead of re-tuning
    all of them. Reuses the same primitives the single-deck commands do:
      • Own   — ownership drift (missing / short craft targets), like `check`.
      • Legal — size / copy-limit / format-legality construction issues, like `legal`.
      • Cast  — cards that stray outside the deck's declared colors (strict-pip
                uncastable 'u' + softer off-identity 's'), like `check`/`mana`.
      • Int   — interaction count (removal + sweeper + counter), like `stats`.
      • Thm   — number of CENTRAL synergy themes (redundancy / focus signal).
      • Pld   — matches PLAYED, from matches.csv (`/log-matches`). REPORT-ONLY.
    A deck is flagged TUNE for a hard problem (illegal / uncastable), review for a
    soft one (off-identity strays / thin interaction), craft when it's just unbuilt,
    else ok. No Scryfall calls — everything is read from the already-built CSVs.

    `Pld` answers the one question the match record can support at its current size:
    which decks have never been tested. It is NOT a win rate and never becomes one —
    34 decks carry a provisional tier promising a re-grade "after real games", and this
    column says which ones are still waiting. `parse_matches.py --report` holds the
    W/L, with its own refusal to print a percentage below 20 matches."""
    scored = audit_roster()
    if not scored:
        print("No decks yet. Add one under decks/<NN-name>/deck.txt (see decks/README.md).")
        return 0

    _by_id = lambda ids: sorted(ids, key=lambda i: (len(i), i))
    tune = _by_id([r["id"] for r in scored if r["verdict"] == "TUNE"])
    craft = _by_id([r["id"] for r in scored if r["verdict"] == "craft"])
    review = _by_id([r["id"] for r in scored if r["verdict"] == "review"])

    rows = []
    for r in scored:
        # `Ns` is every identity stray (matching `deck.py mana`); `Na` marks the subset
        # that is an off-color ABILITY rather than a hybrid you pay on-color — the only
        # kind that reaches the verdict, so the column shows why a deck did or didn't.
        cast_cell = "✓" if not (r["uncast"] or r["stray"]) else \
            " ".join(([f"{r['uncast']}u"] if r["uncast"] else [])
                     + ([f"{r['stray']}s"] if r["stray"] else [])
                     + ([f"{r['stray_ability']}a"] if r["stray_ability"] else []))
        rows.append({**r, "own": "✓" if r["short"] == 0 else f"{r['short']}✗",
                     "legal": "✓" if r["illegal"] == 0 else f"{r['illegal']}✗",
                     "cast": cast_cell})

    if args.flagged:
        rows = [r for r in rows if r["verdict"] != "ok"]
    if getattr(args, "by_tier", False):
        # Sort by competitive tier (S→D, ungraded last), then id.
        rows.sort(key=lambda r: (TIER_ORDER.get(r["tier"], 5), len(r["id"]), r["id"]))
    else:
        rows.sort(key=lambda r: (AUDIT_ORDER[r["verdict"]], len(r["id"]), r["id"]))

    print(f"Deck roster audit — {len(scored)} decks "
          f"(offline triage; full-tune only the flagged ones)\n")
    name_w = min(32, max(4, max((len(r["name"]) for r in rows), default=4)))
    hdr = (f"  {'ID':<4}  {'Deck':<{name_w}}  {'Tier':<4}  {'Sz':>3}  {'Own':<4}  {'Legal':<5}  "
           f"{'Cast':<7}  {'Int':>3}  {'Thm':>3}  {'Pld':>3}  Action")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for r in rows:
        label = {"TUNE": "★ TUNE", "craft": "craft", "review": "review", "ok": "ok"}[r["verdict"]]
        action = label + (f" — {r['why']}" if r["why"] else "")
        print(f"  {r['id']:<4}  {r['name'][:name_w]:<{name_w}}  {(r['tier'] or '·'):<4}  "
              f"{r['sz']:>3}  {r['own']:<4}  {r['legal']:<5}  {r['cast']:<7}  {r['int']:>3}  "
              f"{r['thm']:>3}  {(str(r['played']) if r['played'] else '·'):>3}  {action}")

    print(f"\nLegend: Tier S→D competitive/win-capability (· = ungraded) · "
          f"Own/Legal ✓ clean · Cast Nu=uncastable Ns=identity stray "
          f"Na=of those, off-color ABILITY (the rest are hybrids you pay on-color) · "
          f"Int=removal+sweeper+counter · Thm=central themes · "
          f"Pld=matches played (· = none), report-only — never a verdict input")

    # A column of dots means two different things, and only one of them is about the
    # decks: "never played" vs "no record exists at all". Saying which is the whole
    # difference between a finding and a gap — the failure this subsystem keeps
    # producing (a blank Deck column read as data for nine matches).
    played_total = sum(r["played"] for r in scored)
    if not played_total:
        print("  Pld is empty because matches.csv holds no attributed matches yet — "
              "that is a missing RECORD, not 99 untested decks. See /log-matches.")
    else:
        never = [r["id"] for r in scored if not r["played"]]
        print(f"  {played_total} match(es) recorded across "
              f"{len(scored) - len(never)} deck(s); {len(never)} never played.")
        # A count attributed to a deck id the roster no longer has is invisible in a
        # per-deck table — it would just quietly stop appearing.
        orphans = sorted(set(load_match_counts()) - {r["id"] for r in scored})
        if orphans:
            print(f"  ⚠ matches.csv attributes games to {len(orphans)} unknown deck "
                  f"id(s): {', '.join(orphans)} — renamed or deleted decks.")
    print(f"Summary: {len(tune)} to tune · {len(craft)} to craft · "
          f"{len(review)} to review · {len(scored) - len(tune) - len(craft) - len(review)} ok")
    if tune:
        print(f"\nFull-tune candidates (hard flags): {', '.join(tune)}")
        print("  → run: python3 scripts/deck.py text <id>  then  /tune-deck <id>")
    if review:
        print(f"Worth a look (soft flags): {', '.join(review)}")
    return 0


def _weakest_cut(dmeta, cards, cardmeta, carddata, add_is_fixer=False):
    """The single most-cuttable nonland card in a deck (lowest theme-fit + role
    score), skipping `#: protect:` cards — a hint for suggest-homes. Run
    `deck.py cuts` for the full, oracle-text-graded shortlist.

    `add_is_fixer` is the CARD BEING ADDED, and it is here because this hint used to be
    computed BLIND to it: the caller asked only "what is this deck's weakest card", so
    nothing stopped it proposing a cut that does the very job motivating the add. Mana
    fixing is where that bites, because the keep-score is theme-fit + role credit and
    NEITHER has a fixing term — a rainbow fixer carries almost no synergy tags and no
    classified role, so it sorts to the TOP of the cut list in exactly the multi-colour
    decks that need it. `suggest-homes "Guy in the Chair"` proposed cutting Prismatic
    Undercurrents from deck 13 and Bloom Tender from deck 17 — each strictly better at
    fixing than the card being added. So when the add is a fixer, incumbent fixers are
    not cut candidates: swapping fixing for fixing is a wash at best, and the ranking
    cannot see which one is better.

    Deliberately NOT a general "same role" exclusion. Roles the classifier DOES score
    (removal, card advantage) already reach the keep-score through `_role_credit`, so
    excluding those too would double-count. Fixing is the resource the score is blind
    to, which is precisely why it needs the guard.

    Scored by the SHARED `cut_keep_score` — the same formula `deck.py cuts` prints and
    `tier --to` pairs its adds against. It used to carry its own three-term copy (theme
    fit over central themes + unsaturated role credit) and so inherited none of the
    co-signals: no power, no distinctiveness, no multiplier, no tribal or signature
    term, and a role credit blind to how much of that role the deck already runs. The
    two answers to "this deck's most-cuttable card" disagreed on **36 of 64 decks**.
    Ties break on the card name, matching `rank_cut_candidates`' sort — a min-scan that
    keeps the first-seen winner would otherwise resolve a tie by deck-file order and
    disagree with the printed ranking on exactly the cards that scored equal.
    """
    protected = _protected(dmeta)
    sctx = cut_scoring_context(dmeta, cards, cardmeta, carddata)
    rar = load_rarities()
    best = None
    for q, n, s, c in cards:
        nl = n.lower()
        # G-63: `protected` holds _ms_key keys — must match rank_cut_candidates', or the
        # two answers to "most-cuttable card" diverge on exactly the protected DFCs.
        if nl in BASICS or _ms_key(n) in protected:
            continue
        cd = carddata.get(nl)
        tline = (cd["type"] if cd else "") or ""
        if "Land" in _primary_type(tline):
            continue
        tags = cardmeta.get(nl, {}).get("synergies", [])
        ctext = cd["text"] if cd else ""
        if add_is_fixer and _is_color_fixer(tags, ctext):
            continue
        keep, _ = cut_keep_score(sctx, tline, ctext, tags,
                                 rarity=rar.get(nl, ""), qty=q)
        key = (keep, n.lower())
        if best is None or key < best[0]:
            best = (key, n)
    return best[1] if best else None


_FIXER_TAGS = {"ramp", "mana"}
# A fixer is recognised from its TEXT, not from a synergy tag. The tag gate this
# replaced (`ctags & {ramp, mana}` AND a loose cue) depended on `tag_synergies`'
# hand-kept keyword map, so a fixer whose mechanic is UNINDEXED scored as a non-fixer:
# Bloom Tender ("{T}: For each color among permanents you control, add one mana of that
# color") and Prismatic Undercurrents (fetch X basics, X = your colour count) both key
# off **Vivid**, which sits in `keyword_baseline.txt` as acknowledged-but-unmapped, so
# they tag `vivid` — matching nothing — and read is_fixer=False. Meanwhile Guy in the
# Chair ({2}{G}, taps for one any-colour) carried a `mana` tag and read True, took the
# full boost and the automatic KEY, and `suggest-homes` proposed cutting each deck's
# BETTER fixer to make room for it (decks 13 and 17). Reading the text directly makes
# the predicate independent of which keywords happen to be indexed this cycle.
#
# BROAD = fixes several colours at once, or grants colour-agnostic permission. This is
# the Overlord/Bloom Tender/Vizier shape and it is worth full value at any mana cost.
_FIXER_BROAD_RE = re.compile(
    # every/all/each basic land type (Overlord's token, a Triome-maker)
    r"(?:every|all|each) basic land type"
    # colour-agnostic SPENDING permission (Vizier: "spend mana of any type to cast")
    r"|spend .{0,40}?mana (?:of any (?:color|type)|as though it were mana of any)"
    r"|as though it were mana of any (?:color|type)"
    # a MASS grant — every creature/land you control becomes a rainbow source
    # (Enduring Vitality, Great Divide Guide). One card, many sources.
    r"|you control ha(?:ve|s)[^.]{0,80}?add (?:one )?mana of any"
    # production that SCALES with your colour count (Bloom Tender's Vivid)
    r"|for each color among [^.]{0,60}?add (?:one|that much|x)? ?mana"
    r"|add (?:one|two|three|x) mana of each color"
    # a fetch whose count scales with your colour count (Prismatic Undercurrents)
    r"|search .{0,60}?for (?:up to )?x basic land",
    re.I)
# SINGLE = you choose ONE colour per activation (a Command Tower, a rainbow dork, Gilded
# Lotus' three-of-one-colour). Real fixing, but its worth is bounded by what it costs —
# see `_fixer_rate`. `any one color` and Chrome Mox's `any of the exiled card's colors`
# are the same class as `any color`; the first sweep omitted both and dropped 38 genuine
# fixers, which only the roster-wide before/after diff surfaced.
_FIXER_SINGLE_RE = re.compile(
    r"add (?:\w+ )?mana of any(?: one)? (?:color|type)"
    r"|mana of any of [^.]{0,50}?colors",
    re.I)
# Rate floor/ceiling for a SINGLE-source fixer: a 1–2 mana rainbow source is full value,
# and each mana past that discounts it. `Guy in the Chair` at MV 3 lands at 0.67, below
# `_FIXER_KEY_RATE`, so it stays a role-player instead of being auto-promoted to KEY.
_FIXER_SINGLE_PAR = 2.0
_FIXER_RATE_FLOOR = 0.25
# A fixer must be at least this efficient before the colour-count overlay promotes it
# straight to KEY. Broad fixers rate 1.0 and always clear it.
_FIXER_KEY_RATE = 0.7


# DOUBLERS — a card whose value scales with HOW MUCH of a thing the deck already does.
# Theme overlap sees "this card mentions tokens" and stops there, so Exalted Sunborn ("if
# one or more tokens would be created under your control, twice that many are created
# instead") scored deck 45 at fit 52 over Knight's Edge at 46 — when 45 fields SIX
# token-makers and Knight's Edge fields FOURTEEN. The tag model cannot see magnitude, only
# membership, and a doubler is worth exactly the magnitude.
#
# A tag would NOT have fixed this: the card already shared `tokens` with those decks and
# still lost the ranking. What is missing is a deck-side COUNT, so this is a scoring term
# on the same bounded pattern as `_fixer_boost` (whose value likewise scales with a
# deck-side quantity, the colour count).
_DOUBLER_AXES = {
    # axis -> (what the DOUBLER's text looks like, what a deck card that FEEDS it looks like)
    "tokens": (
        re.compile(r"if one or more[^.]{0,80}?tokens? would be created[^.]{0,80}?"
                   r"(?:twice that many|instead)", re.I),
        re.compile(r"creates? (?:a|an|two|three|four|\w+) [^.]{0,60}?token", re.I)),
    "counters": (
        re.compile(r"if one or more[^.]{0,80}?counters? would be put[^.]{0,80}?"
                   r"(?:twice that many|instead)", re.I),
        re.compile(r"put (?:a|an|two|three|\w+) \+1/\+1 counter", re.I)),
    "triggers": (
        re.compile(r"triggers? an additional time|that ability triggers? one more time", re.I),
        re.compile(r"\bwhenever\b|\bwhen .{0,40}?enters\b", re.I)),
    # LIFEGAIN was the missing axis, and The Wind Crystal is why. A card that doubles every
    # lifegain is a multiplier exactly the way a token or counter doubler is, but the axis
    # list stopped at three and so it read `None` — no doubler support, no fit bump, and
    # `cuts` ranked it as an ordinary artifact. Requires the literal "twice that much"
    # rather than reusing the other axes' looser `instead` alternative, because a
    # REPLACEMENT that is not a doubling is templated identically: Angel of Vitality's
    # "you gain that much life plus 1 instead" is +1, not ×2, and would qualify on
    # `instead` alone.
    "lifegain": (
        re.compile(r"if you would gain life[^.]{0,60}?twice that much", re.I),
        re.compile(r"\bgains? \d+ life|\bgain that much life|\blifelink\b", re.I)),
}
_DOUBLER_PER_SOURCE = 1.2   # fit points per feeding card ABOVE the axis floor
# Ceiling chosen as a SAFETY rail, not an operating point: real decks feed an axis with
# 4-15 cards, so at 1.2/source the term is effectively linear across that whole range and
# the cap only bites past 15. Capping lower (12) made it saturate at 10 and stop
# distinguishing Knight's Edge's 14 token-makers from Avengers' 10 — which is the exact
# discrimination this term exists to provide. Comparable in size to `_fixer_boost` (max 20).
_DOUBLER_CAP = 18
_DOUBLER_MIN_SOURCES = 5    # below this the deck does not do the thing enough to matter
_DOUBLER_KEY_SOURCES = 10   # at this density the doubler IS a key card (mirrors the
                            # fixer overlay promoting at 4+ colours)

# THE FLOOR IS THE AXIS'S ZERO POINT, AND THE BOOST USED TO MEASURE FROM ACTUAL ZERO.
# `_DOUBLER_MIN_SOURCES` is defined as "below this the deck does not do the thing enough
# to matter", so density ABOVE it is the quantity a doubler is worth — but `doubler_boost`
# grew as `support * per` from 0, which double-counts the baseline every deck already has.
# Where the baseline is small next to the range that error is harmless; where it is large
# the term saturates and stops carrying information, and the roster says the `triggers`
# axis is exactly that case. Feeder counts across the 115 decks:
#
#     axis        p10  p25  p50  p75  p90  max   at/over the old cap (15 feeders)
#     tokens        3    5    8   11   16   29    16 decks = 14%
#     counters      2    3    6   10   13   25     8 decks =  7%
#     lifegain      1    3    5    8   13   30    10 decks =  9%
#     triggers     17   20   23   25   30   35   106 decks = 92%
#
# The global constants are ROSTER PERCENTILES for the three healthy axes — floor 5 ~ p25,
# key 10 ~ p75, cap reached ~ p90 — and `triggers` is the one axis whose distribution sits
# nowhere near them: its MINIMUM is 10, so every deck cleared both the floor and the KEY
# promotion, and 92% pinned the cap. The term was therefore constant roster-wide on the
# axis with the most doubler cards in the pool (32 of 57). Measured consequence:
# Wizard's Staff, a trigger doubler, collected the identical +18 in deck 37 (30 feeders),
# 37b (35) and 57 (22), so ranking fell back to theme overlap and put the ONE-Wizard deck
# above the two 20-Wizard decks for a card reading "Equip Wizard {1}".
#
# Fix is per-axis floor/key at each axis's OWN p25/p75, with `per` and `cap` left global;
# the three healthy axes keep their existing numbers because their distributions already
# match. Same method and same standing hazard as `TIER_FLOOR_REQ` (BS8-06): these are
# calibrated against a roster that grows, so re-derive when a distribution moves, and
# never treat the fact that one axis discriminates as evidence that all four do.
_DOUBLER_CALIB = {
    # axis -> (floor, key_sources), from that axis's roster p25 / p75
    "triggers": (20, 25),
}


def doubler_calib(axis):
    """(floor, key_sources) for an axis — its own p25/p75, else the global defaults."""
    return _DOUBLER_CALIB.get(axis, (_DOUBLER_MIN_SOURCES, _DOUBLER_KEY_SOURCES))


def doubler_axis(text):
    """Which quantity this card DOUBLES ('tokens' / 'counters' / 'triggers'), or None."""
    if not text:
        return None
    for axis, (dbl, _feed) in _DOUBLER_AXES.items():
        if dbl.search(text):
            return axis
    return None


# Some doublers only apply to a SUBSET of the axis — Delney, Streetwise Lookout doubles
# triggers of "creatures you control with power 2 or less". Counting every trigger in the
# deck roughly DOUBLED the real support (deck 24 read 24 sources against a true 4, enough
# to flip it over the KEY threshold on its own), so the restriction is parsed off the
# doubler's own text rather than assumed away.
_DOUBLER_POWER_RE = re.compile(r"power (\d+) or less", re.I)


def doubler_restriction(text):
    """Max creature power a doubler's effect applies to, or None for unrestricted."""
    m = _DOUBLER_POWER_RE.search(text or "")
    return int(m.group(1)) if m else None


def doubler_support(axis, cards, carddata, max_power=None):
    """How many copies in the deck FEED that axis — the magnitude a doubler multiplies.

    `max_power` restricts the count to creatures at or below that printed power, for a
    doubler whose text is scoped that way. Printed power is the correct read (a creature
    that GROWS later still wasn't small when the doubler was evaluated), and
    `lib.card_power` returns None for `*`/`X` rather than inventing a number — those are
    excluded from a restricted count rather than assumed to qualify.
    """
    feed = _DOUBLER_AXES.get(axis, (None, None))[1]
    if not feed:
        return 0
    n = 0
    for q, name, _s, _c in cards:
        nl = name.lower()
        if nl in BASICS:
            continue
        cd = carddata.get(nl) or carddata.get(nl.split(" // ")[0])
        if not cd or not feed.search(cd.get("text") or ""):
            continue
        if max_power is not None:
            if "Creature" not in (cd.get("type") or ""):
                continue
            p = card_power(cd.get("power"))
            if p is None or p > max_power:
                continue
        n += q
    return n


def doubler_boost(support, axis=None, per=_DOUBLER_PER_SOURCE, cap=_DOUBLER_CAP,
                  floor=None):
    """Bounded fit bump for a doubler, growing with the deck's density of what it doubles.

    Zero below the axis floor (a deck making three tokens does not want a token doubler),
    linear in the density ABOVE that floor, hard-capped at `cap` so it can reorder decks
    that are otherwise close without ever overriding a genuine theme match — the same
    contract as `_fixer_boost`.

    Growth is measured FROM THE FLOOR, not from zero. The floor is the axis's zero point
    by definition, and counting the baseline every deck already has is what let the
    `triggers` axis pin the cap on 92% of the roster — see `_DOUBLER_CALIB` for the
    distributions and the measured consequence. Pass `axis` so the per-axis floor
    applies; `floor` overrides it outright, for a caller with its own calibration.
    """
    if floor is None:
        floor = doubler_calib(axis)[0]
    if support < floor:
        return 0.0
    # `support - floor + 1`: the floor is the FIRST QUALIFYING level, not the zero level,
    # so a deck sitting exactly on it still earns the minimum bump. Dropping the +1 makes
    # the boost 0 at the floor, which is a different claim (the deck does not do the thing
    # at all) and breaks the pinned "nonzero at the floor, rising after" contract.
    return min((support - floor + 1) * per, float(cap))


def _fixer_boost(ncolors, per_color=4, cap=5, rate=1.0):
    """Bounded fit bump for a rainbow fixer in an `ncolors`-color deck — grows with
    the color count (a fixer earns more in a 5-color deck than a 3-color one) but is
    CAPPED (at `cap` colors) so it nudges ordering among fixer-eligible decks without
    ever dwarfing a genuine theme match. Returns 0 below 3 colors (mono/two-color
    decks don't need the fixing).

    `rate` (0..1, from `_fixer_rate`) scales the bump by how much fixing the card
    actually BUYS. Without it the term read only the deck's colour count, so Overlord
    of the Hauntwoods (a permanent land token with every basic land type) and Guy in
    the Chair ({2}{G}, taps for exactly one) collected the identical +16 and the
    identical KEY — the term could not tell a manabase fix from a mediocre dork.
    """
    if ncolors < 3:
        return 0
    return min(ncolors, cap) * per_color * rate


def _fixer_rate(text, mv=None):
    """How much fixing a rainbow fixer actually buys, as a 0..1 multiplier on the
    colour-count boost. BROAD fixers (several colours at once, or colour-agnostic
    spending permission) rate 1.0 at any cost — that value does not decay with mana.
    A SINGLE any-colour source rates by cost: full value at `_FIXER_SINGLE_PAR` mana
    or less, discounted above it, floored at `_FIXER_RATE_FLOOR` so an expensive
    rainbow source is still recognised as fixing rather than dropping to nothing.
    Returns 0.0 for a non-fixer. Unknown MV is treated as par (no penalty), since
    guessing against missing data should not manufacture a demotion.

    Parenthetical REMINDER text is stripped first, and that single line is what keeps
    this from saturating: a Treasure token's reminder is literally `(It's an artifact
    with "{T}, Sacrifice this token: Add one mana of any color.")`, so without the strip
    every Treasure-maker in the pool reads as a rainbow fixer — 150-odd cards, and a
    signal that fires on everything carries nothing. A one-shot sacrificial token is
    ramp, not a manabase. Chromatic Sphere states the same ability as REAL text rather
    than a reminder, so it still qualifies, which is the right split."""
    t = _REMINDER_RE.sub(" ", text or "")
    if _FIXER_BROAD_RE.search(t):
        return 1.0
    if not _FIXER_SINGLE_RE.search(t):
        return 0.0
    if mv is None or mv <= _FIXER_SINGLE_PAR:
        return 1.0
    return max(_FIXER_RATE_FLOOR, _FIXER_SINGLE_PAR / float(mv))


def _is_color_fixer(ctags, text):
    """True when a card's value is multi-color mana FIXING whose worth SCALES with a
    deck's color count — a rainbow fixer (Overlord's every-basic-land-type token,
    Vizier's 'spend mana as though any color', a Triome-maker). A theme-overlap model
    can't see fixing (it isn't a 'theme'), and its value is proportional to how many
    colors the target deck must cast — so `suggest-homes` under-rates it in exactly
    the 3+-color decks that want it most (the Overlord → decks 17/21a miss).

    Read from TEXT alone, in explicit MANA/land-type context. `ctags` is accepted and
    ignored: the previous tag gate (`ramp`/`mana` + a loose "any color" substring) made
    the predicate a hostage of `tag_synergies`' keyword map, and every fixer built on an
    UNINDEXED mechanic read False — see `_FIXER_BROAD_RE`. Requiring mana context is
    what keeps the loose cue honest without the tag: "protection from the color of your
    choice" says "color of your choice" and is not fixing, and a mono-color ramp spell
    ('add {G}{G}') never matches either pattern."""
    return bool(_fixer_rate(text))


def _deck_central_weights(meta, cards, cardmeta):
    """A deck's CENTRAL themes as a {theme: copies} weight vector — the same `_central_themes`
    set the roster tools share, kept weighted so a dominant theme counts for more.

    Built in SORTED key order (G-54). `_central_themes` returns a SET, so iterating it
    gave the dict a hash-seed-dependent insertion order — and every consumer that ranks
    these themes by weight (`cmd_similar`'s "top themes" line, its shared-theme list, the
    float summation inside `_theme_cosine`) breaks ties on that order. `deck.py similar`
    therefore printed a different answer on every run: five PYTHONHASHSEED values produced
    five different outputs, and because the display truncates to `shared[:5]` and the ⚠ line
    names `top[5][:3]`, WHICH themes the reader is shown changed run to run — deck 40 read
    `✦Druid` against 40a on one run and `removal` on the next. G-47 tells the reader to grade
    on exactly those ✦ SPECIFIC overlaps. Alphabetical is arbitrary but TOTAL, which is the
    property that matters (broad-scan BS5-01)."""
    tw = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = cardmeta.get(n.lower())
        if m:
            for t in m["synergies"]:
                tw[t] = tw.get(t, 0) + q
    return {t: tw[t] for t in sorted(_central_themes(tw))}


_SIM_GENERIC_DAMP = 0.35   # generic themes are shared by nearly every value deck, so they
                           # signal little about IDENTITY overlap — damp them in the cosine.


def _theme_is_generic(t):
    return t.lower() in GENERIC_THEMES or t.lower() in _GENERIC_TRIBES


def _strong_signature_themes(meta, cards, cardmeta, min_cards=2):
    """Signature themes carried by ≥`min_cards` of the deck's `#: protect:` cards — a real
    BUILD-AROUND spine (a counters deck that protects several counter-doublers), NOT a generic
    theme incidental to one protected bomb. Stricter than `_signature_themes` (which unions
    ALL protected cards' tags): used by `similar`'s generic-rescue so a lone protected card's
    card-draw/etb tag can't promote a diffuse value deck's generic overlap into a false
    identity match (a counters spine spans multiple protected cards; Finale's card-draw doesn't).

    A GENERIC theme must additionally clear HALF the protect list, and that proportional bar
    is the whole point of this function rather than a refinement of it. The signature exists
    for one job — rescuing a theme that idf calls generic when it is genuinely the deck's
    spine — so a SPECIFIC theme never needed rescuing and keeps the flat ≥2 bar. But ≥2 was
    tuned against a 3-to-5-card protect list, and it does not survive a longer one: at 7
    protected cards ≥2 is 29% of them, and at 14 it is 14%. Measured on the roster, that let
    26 of 33 decks carry a signature that was ≥50% GENERIC — deck 46 rescued `Human`,
    `combat`, `flying` and five more off 14 protected cards, and deck 51 rescued `card draw`,
    `graveyard`, `mana` and `tokens` off 7. Since `fit_strength` is right to mint KEY from any
    signature theme it is handed (see check_suggest anchor 11b — the strictness must live in
    the caller, not the function), those false spines propagated straight into `screen`'s KEY
    label, which fired on 66% of a 111-card pile and so carried almost no information. The
    proportional bar drops 51 signature themes across 18 decks and leaves every genuine spine
    standing (deck 49 keeps `Dragon`, deck 47 keeps `affinity`/`artifacts`). Same shape as
    G-09: a keep-boost that applies to nearly everything is a constant, not a signal."""
    prot = _protected(meta)
    if not prot:
        return frozenset()
    counts = {}
    for q, n, s, c in cards:
        if _ms_key(n) in prot:                 # G-63: `prot` holds _ms_key keys
            m = cardmeta.get(n.lower())
            if m:
                for t in set(m["synergies"]):
                    counts[t] = counts.get(t, 0) + 1
    generic_bar = max(min_cards, math.ceil(len(prot) / 2))
    return frozenset(t for t, k in counts.items()
                     if k >= (generic_bar if _theme_is_generic(t) else min_cards))


def _sim_specific(t, keep):
    """Is theme `t` SPECIFIC for a similarity comparison? Non-generic themes always are; a
    generic-by-idf theme counts as specific when it's a deck's `#: protect:` SIGNATURE
    (in `keep`) — so a counters-doubler deck whose spine IS counters reads counters as an
    identity theme, not generic value overlap (the same signature rescue `fit_strength` uses)."""
    return (not _theme_is_generic(t)) or t in keep


def _sim_weights(vec, specific_only=False, keep=frozenset()):
    """Down-weight GENERIC themes/tribes in a central-theme vector for the similarity cosine:
    two decks sharing a SPECIFIC theme (a tribe, a build-around mechanic) are far more alike
    than two that merely both run card-draw/etb — otherwise every diffuse value deck reads as
    a near-duplicate of every other. `keep` (the pair's signature themes) rescues a generic
    theme that IS a deck's spine. `specific_only` DROPS the remaining generics entirely (a
    pure-identity lens), so a diffuse good-stuff deck honestly reads as sharing nothing specific."""
    out = {}
    for t, w in vec.items():
        spec = _sim_specific(t, keep)
        if not spec and specific_only:
            continue
        out[t] = w * (1.0 if spec else _SIM_GENERIC_DAMP)
    return out


def _theme_cosine(a, b, specific_only=False, keep=frozenset()):
    """Cosine similarity of two {theme: weight} vectors (generic-damped via `_sim_weights`,
    or generic-EXCLUDED when specific_only; `keep` = the pair's signature themes). A shared
    SPECIFIC dominant theme drives the score far more than an incidental etb overlap — the
    'do these two decks do the same thing' signal, not 'are they both value decks'."""
    a, b = _sim_weights(a, specific_only, keep), _sim_weights(b, specific_only, keep)
    shared = set(a) & set(b)
    if not shared:
        return 0.0
    # SORTED, because float addition is not associative: summing over a set made `dot`
    # differ in its last bits between runs, and `cmd_similar` sorts rows on that value —
    # so a tie between two decks could flip. Costs nothing and removes the last piece of
    # run-to-run variance from `similar` (G-54 / broad-scan BS5-01).
    dot = sum(a[t] * b[t] for t in sorted(shared))
    na = math.sqrt(sum(w * w for w in a.values()))
    nb = math.sqrt(sum(w * w for w in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def cmd_similar(args):
    """Rank the decks most SIMILAR to <id> by shared central-theme overlap — the roster
    'is this deck distinct, or does it duplicate an existing one?' check (the question a
    from-scratch build always raises). Cosine over the central-theme WEIGHT vectors, so a
    shared dominant theme dominates the score; a color-overlap % is shown alongside."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    cardmeta, mana = load_card_meta(), load_mana()
    spec_only = getattr(args, "specific_only", False)
    meta, cards = parse_deck_file(d["path"])
    aw = _deck_central_weights(meta, cards, cardmeta)
    acols = _declared_colors(meta) or _deck_castable_colors(meta, cards, mana)
    if not aw:
        print(f"Deck {d['id']} has no central themes to compare (too few tagged cards).")
        return 0
    sig_a = _strong_signature_themes(meta, cards, cardmeta)   # multi-card spine — rescues a
    a_specific = [t for t in aw if _sim_specific(t, sig_a)]   # generic theme that's the identity
    if spec_only and not a_specific:
        print(f"Deck {d['id']}: {d.get('name') or d['id']} has NO specific central themes — "
              "it's a diffuse good-stuff/value deck, so it's distinct BY IDENTITY from every\n"
              "deck (nothing specific to duplicate). Drop --specific-only for a value-overlap view.")
        return 0
    carddata = load_card_data()
    # Keyed on `_ms_key` (G-63), displayed under the deck's own spelling: this set
    # feeds the "▸ Most shared CARDS" figure G-47 tells the reader to trust when it
    # disagrees with the cosine, and raw display names meant a card the two decks
    # spell differently (front vs full) never counted as shared. Intersecting KEYS
    # while printing the mapped display name keeps the count right without turning
    # the printed list into lowercased keys.
    anames = {_ms_key(n): n for _q, n, _s, _c in cards if n.lower() not in BASICS
              and "Land" not in _primary_type((carddata.get(n.lower()) or {}).get("type") or "")}
    rows = []
    # Roster only (BS-14): distinctness against a retired/example list is noise —
    # is_roster_deck's own contract scopes "cross-deck reuse" to the roster.
    for dd in roster_decks():
        if dd["id"].lower() == d["id"].lower():
            continue
        m2, c2 = parse_deck_file(dd["path"])
        bw = _deck_central_weights(m2, c2, cardmeta)
        keep = sig_a | _strong_signature_themes(m2, c2, cardmeta)   # EITHER deck's spine counts
        sim = _theme_cosine(aw, bw, spec_only, keep)
        if sim <= 0:
            continue
        bcols = _declared_colors(m2) or _deck_castable_colors(m2, c2, mana)
        colj = len(acols & bcols) / len(acols | bcols) if (acols | bcols) else 0.0
        # `(-weight, t)`, not `-weight` alone: `shared` is a SET and the weight ties
        # constantly (every theme carried by the same number of copies), so the tail of
        # this list was set-iteration order — and the display shows only `shared[:5]`
        # (BS5-01). The tag itself is a total order, matching the tie-break
        # `wishlist._rank_scores` already applies to its own `specific` list.
        shared = sorted(set(aw) & set(bw), key=lambda t: (-(min(aw[t], bw[t])), t))
        spec = [t for t in shared if _sim_specific(t, keep)]
        # CARD overlap, the thing the theme cosine cannot see. This model compares
        # {theme: weight} vectors, so two decks can read 84% similar while sharing five
        # card names — four of them lands. Without this column the score reads as "these
        # are the same deck" when it often means "these are both Orzhov value decks".
        # Lands are excluded: a shared manabase is not a shared identity.
        bnames = {_ms_key(n) for _q, n, _s, _c in c2 if n.lower() not in BASICS
                  and "Land" not in _primary_type((carddata.get(n.lower()) or {}).get("type") or "")}
        both = set(anames) & bnames
        rows.append((sim, colj, dd["id"], dd.get("name") or dd["id"], shared, spec,
                     len(both), sorted(anames[k] for k in both)))
    # Theme cosine stays the PRIMARY order — it answers "does this duplicate an
    # identity", which is the question. But it is not the same question as "which deck do
    # I share the most cards with", and the two can rank in opposite orders: deck 52a
    # reads 96% against deck 6 (4 shared cards, 33% colours) and 81% against its own
    # parent 52 (13 shared cards, 100% colours). A reader acts on row order, so the
    # card-overlap answer is stated explicitly below rather than left in a column.
    rows.sort(key=lambda r: (-r[0], -r[1], r[2]))
    limit = getattr(args, "limit", 8) or 8
    lens = "SPECIFIC-theme overlap only" if spec_only else "central-theme overlap"
    print(f"Deck {d['id']}: {d.get('name') or d['id']} — most similar decks ({lens})\n"
          f"Your colors: {'/'.join(sorted(acols)) or '—'}  ·  top themes: "
          f"{', '.join(f'{t}({aw[t]})' for t in sorted(aw, key=lambda t: -aw[t])[:6])}\n")
    print(f"  {'sim':>4} {'col':>4} {'cards':>5}  {'deck':6} shared themes (✦ = a SPECIFIC identity theme)")
    print("  " + "-" * 84)
    for sim, colj, did, name, shared, spec, ncards, cardnames in rows[:limit]:
        # A shared SPECIFIC theme = a real identity match ⇒ ⚠ overlap. High sim on GENERIC
        # themes only = both are value decks, not a duplicate ⇒ the softer '· value overlap'.
        if sim >= 0.60 and spec:
            flag = " ⚠ overlap"
        elif sim >= 0.60:
            flag = " · value overlap"
        elif sim >= 0.30:
            flag = ""
        else:
            flag = " · distinct"
        specset = set(spec)
        disp = ", ".join((("✦" + t) if t in specset else t) for t in shared[:5])
        print(f"  {sim*100:>3.0f}% {colj*100:>3.0f}% {ncards:>5}  {did:6} {disp}{flag}")
    if getattr(args, "full", False):
        print("\n  Shared nonland cards — the concrete evidence the cosine cannot show:")
        for sim, colj, did, name, shared, spec, ncards, cardnames in rows[:limit]:
            print(f"    {did:6} ({ncards}) {', '.join(cardnames) if cardnames else '—'}")
    top = rows[0] if rows else None
    # The deck with the most shared CARDS, computed up front so the ⚠ headline can name
    # it (DD-5): for deck 77 the headline named 51a (93% themes, 2 shared cards) while
    # the true neighbour 64 (88%, NINE shared cards) sat one row down — the ▸ line below
    # carried the truth, but the headline is what a distinctiveness read acts on.
    by_cards = sorted(rows, key=lambda r: (-r[6], -r[1], r[2]))
    cards_top = by_cards[0] if by_cards and by_cards[0][6] else None
    if top and top[0] >= 0.60 and top[5]:
        # Temper the warning with the card count: a high cosine on few shared CARDS is a
        # both-are-value-decks signal, not a duplicate.
        tail = (f" But they share only {top[6]} nonland card(s), so the overlap is in what "
                f"the decks TAG as, not what they play — grade the win-cons from "
                f"`deck.py text`." if top[6] <= 5 else
                f" They also share {top[6]} nonland cards — check that list first.")
        if top[6] <= 5 and cards_top and cards_top[2] != top[2] and cards_top[6] > top[6]:
            tail += (f" The closer CARD neighbour is deck {cards_top[2]} "
                     f"({cards_top[6]} shared) — check that one too.")
        print(f"\n⚠ Closest is #{top[2]} {top[3]} at {top[0]*100:.0f}% and shares a SPECIFIC theme "
              f"({', '.join(top[5][:3])}).{tail}")
    elif top and top[0] >= 0.60:
        print(f"\nClosest is #{top[2]} {top[3]} at {top[0]*100:.0f}%, but only on GENERIC value "
              "themes — a loose 'both value decks' overlap, not a duplicate identity.")
    elif top:
        print(f"\nClosest is #{top[2]} {top[3]} at {top[0]*100:.0f}% — comfortably distinct.")
    # The deck you share the most CARDS with, when the theme ranking does not put it first.
    if cards_top and rows and cards_top[2] != rows[0][2]:
        top = cards_top
        rank = next(i for i, r in enumerate(rows, 1) if r[2] == top[2])
        print(f"  ▸ Most shared CARDS: deck {top[2]} ({top[6]} nonland card(s), "
              f"{top[1] * 100:.0f}% colours) — it ranks #{rank} by theme. Theme similarity "
              "and card overlap are different questions; some overlap between decks is "
              "fine, so read this as 'where the lists actually meet'.\n")
    print("\n✦ marks a SPECIFIC (identity) theme; plain = generic value overlap. A SHORTLIST — "
          "grade the DOMINANT theme + win-con from `deck.py text`, not the number. "
          "`--specific-only` scores identity themes alone.")
    return 0


_TRAILING_NOTE_RE = re.compile(r"\s*\([^()]*\)\s*$")
_SQUASH_RE = re.compile(r"[^a-z0-9]+")


def _name_query(raw):
    """Normalize a HAND-TYPED candidate name: drop trailing parenthetical notes and collapse
    whitespace. A pile is written by a person, so `Master Pakku (needs Lessons)` and
    `Bruce Banner (mostly for its front face)` name the same cards as the bare strings."""
    q = " ".join(str(raw).split())
    prev = None
    while prev != q:                       # `Foo (a) (b)` — strip every trailing note
        prev = q
        q = _TRAILING_NOTE_RE.sub("", q).strip()
    return q


def _squash(s):
    """Comparison key with every non-alphanumeric character removed, so a hand-typed name
    matches the printed one across the punctuation people drop: `Ramos Dragon Engine` ->
    `Ramos, Dragon Engine`, `Gran Gran` -> `Gran-Gran`, `Flotsam//Jetsam` ->
    `Flotsam // Jetsam`. Deliberately NOT a typo-corrector — `Impostoer Syndrome` still
    fails to resolve, because guessing at a misspelling silently grades the wrong card,
    which is worse than reporting the name back."""
    return _SQUASH_RE.sub("", s.lower())


def _squash_index(table, display):
    """squashed-name -> {key: display}, built ONCE per surface. Screening a 111-card pile
    would otherwise re-scan every pool key per query."""
    out = {}
    for k in table:
        for variant in (k, k.split(" // ")[0]):
            out.setdefault(_squash(variant), {})[k] = display(k)
    return out


def _resolve_card_name(query, table, display, squashed):
    """Resolve a hand-typed card name against `table` (a dict keyed by lowercase name).
    Returns `(key, candidates)` — `key` on a unique match, `candidates` (sorted display
    names) when genuinely ambiguous, `(None, [])` when nothing matched.

    Order: exact -> DFC front -> squashed punctuation -> unique substring.

    THE SQUASH STEP IS THE LOAD-BEARING ONE, and it exists because a real pasted pile
    concentrates its interesting cards in exactly the names it recovers. Screening one
    111-card pile left 22 names unresolved, and they were overwhelmingly `Name, Epithet`
    legendary creatures typed without the comma — so the triage tool silently handed back
    the fifth of the pile that most needed it, and those cards got graded by hand instead.
    Ambiguity is still reported rather than guessed at (G-47: a shortlist that guesses is
    worse than one that admits it doesn't know)."""
    ql = _name_query(query).lower()
    if ql in table:
        return ql, []
    front = ql.split(" // ")[0]
    if front in table:
        return front, []
    hits = squashed.get(_squash(ql)) or {}
    names = set(hits.values())
    if len(names) == 1:
        return sorted(hits, key=len)[0], []
    if len(names) > 1:
        return None, sorted(names)
    subs = sorted((k for k in table if ql in k), key=len)
    names = {display(k) for k in subs}
    if len(names) == 1:
        return subs[0], []
    if len(names) > 1:
        return None, sorted(names)
    return None, []


def _candidate_castability(cost, ident, declared):
    """`(castable, note)` for a CANDIDATE card against a deck's declared colors, read from
    the PRINTED COST rather than from color identity.

    Identity and cost disagree in precisely the cases a pile is full of: `{1}{U/R}` is
    payable with Islands alone, `{6}` is payable anywhere, and BOTH read as off-color in
    the `Color(s)` column. Triaging a 111-card pile on that column mis-sorted nine cards,
    eight of which were castable (G-58, bulk-triage variant). Mirrors `_castability_lint`
    so the two surfaces cannot drift: only a TRUE multicolor hybrid constrains
    castability; a monocolor (`{2/W}`) or Phyrexian (`{W/P}`) hybrid never does."""
    strict, hybrid = parse_pips(cost or "")
    off_strict = sorted(set(strict) - declared)
    bad_hybrid = sorted({x for h in hybrid
                         if len(h) >= 2 and not (h & declared) for x in h})
    if off_strict or bad_hybrid:
        return False, "⚠ NOT castable — needs " + "/".join(sorted(set(off_strict + bad_hybrid)))
    stray = sorted(ident - declared)
    if not stray:
        return True, ""
    if not cost:
        return True, ("identity has " + "/".join(stray)
                      + " (cost unknown — run `deck.py mana` to tell hybrid from ability)")
    hybrid_colors = set().union(*hybrid) if hybrid else set()
    if set(stray) <= hybrid_colors:
        return True, "identity has " + "/".join(stray) + " (hybrid — paid on-color)"
    return True, "identity has " + "/".join(stray) + " (off-color ability — still castable)"


def _printing_index():
    """name_lower (full AND DFC front) -> (display, set_code, collector), preferring
    owned∩pool > owned > pool (DD-1). Used by `deck.py resolve`.

    "Owned printing wins" alone was the old rule, and when you own SEVERAL printings the
    arbitrary last library row won: Llanowar Elves resolved to its (M19) printing while
    the owned (FDN) one — the pool's format-canonical printing, the one deck 31 already
    plays — sat one row earlier. The pool keys ONE printing per card from the format
    query (G-18), so an owned printing that MATCHES the pool's is both "what you have"
    and "what the format knows"; prefer it, then any owned printing (last row wins, as
    before, so single-printing behaviour is unchanged), then the pool's.

    Front faces are aliased in a SECOND pass (G-63) — never in-pass with setdefault,
    which let a DFC seen early claim the bare front key a distinct card owns (BS4-18)."""
    pool_info, lib_rows = {}, {}
    for path, store in ((POOL_CSV, "pool"), (DEFAULT_CSV, "lib")):
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                disp = (r.get("Card Name") or "").strip()
                nl = disp.lower()
                if not nl:
                    continue
                info = (disp, (r.get("Set Code") or "").strip(), (r.get("Collector #") or "").strip())
                if store == "pool":
                    pool_info[nl] = info
                else:
                    lib_rows.setdefault(nl, []).append(info)
    idx = dict(pool_info)
    for nl, infos in lib_rows.items():
        pool = pool_info.get(nl)
        # Compare on (set, collector) only — display capitalisation may differ per row.
        if pool and any(i[1:] == pool[1:] for i in infos):
            idx[nl] = pool                       # owned AND the pool's canonical printing
        else:
            idx[nl] = infos[-1]                  # any owned printing (last row, as before)
    for nl in list(idx):                         # second-pass front aliasing (G-63)
        idx.setdefault(nl.split(" // ")[0], idx[nl])
    return idx


@_file_memo("DEFAULT_CSV", "POOL_CSV")
def known_printings():
    """(by_name, set_codes) — every (set, collector) this repo knows, per card.

      by_name    : name_lower -> {(set_lower, collector_lower), …}
      set_codes  : {set_lower, …} across the whole pool + library

    The deck-line fields `(SET) COLLECTOR#` were validated by NOTHING. `1 Eaten Alive
    (ZZZ) 172` — a set code that does not exist — passed `legal`, passed `check` (which
    reported it as OWNED, since ownership joins on the NAME), passed `preflight` READY
    and passed `check_all` "All invariants hold". INV-04 only asserts a line PARSES, so a
    deck file could be integrity-clean and un-importable at the same time. That is not
    hypothetical: deck 52 was written with `(FDN) 610` for a card whose collector number
    is 172, and nothing complained.

    Front faces are aliased in a SECOND pass so a `Front // Back` row cannot shadow a
    real card named `Front` (G-63) — and only when the front name has no rows of its own.
    """
    by_name, set_codes, real = {}, set(), set()
    for path in (POOL_CSV, DEFAULT_CSV):
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                nl = (r.get("Card Name") or "").strip().lower()
                if not nl:
                    continue
                sc = (r.get("Set Code") or "").strip().lower()
                pr = (sc, (r.get("Collector #") or "").strip().lower())
                by_name.setdefault(nl, set()).add(pr)
                real.add(nl)
                if sc:
                    set_codes.add(sc)
    for nl in list(by_name):
        front = nl.split(" // ")[0]
        if front != nl and front not in real:
            by_name.setdefault(front, set()).update(by_name[nl])
    return by_name, set_codes


def printing_problems(cards):
    """(bad_set, unverified) for a deck's card lines.

      bad_set     : [(name, set, collector)] — the set code appears in NO card anywhere,
                    so the line is certainly wrong. HARD: zero across the whole roster.
      unverified  : [(name, set, collector, known)] — the name and set code are both
                    real, but this exact printing is not one we hold. SOFT, because the
                    pool keys ONE printing per card by construction, so a legitimate
                    alternate printing lands here too.

    BASIC LANDS ARE EXEMPT. Arena prints several arts per set (Swamp MSH 291 and 292 are
    both real) while the pool carries one, so a hard rule would have failed 61 of 78 deck
    files on basics alone — measured before choosing the split. A line with no printing
    stated at all is also skipped: that is a legal, if under-specified, deck line."""
    by_name, set_codes = known_printings()
    bad_set, unverified = [], []
    for _q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS or nl.startswith("snow-covered "):
            continue
        if not s and not c:
            continue
        if s and s.lower() not in set_codes:
            bad_set.append((n, s, c))
            continue
        known = by_name.get(nl) or by_name.get(nl.split(" // ")[0])
        if not known:
            continue                      # unknown card entirely — reported elsewhere
        if (s.lower(), c.lower()) not in known:
            unverified.append((n, s, c, sorted(known)[:3]))
    return bad_set, unverified


def _legality_of(names):
    """name_lower -> set(formats) from the pool, for a legality warning on any surface
    that hands back card names. Empty dict if the pool has no Legalities column."""
    out = {}
    if not os.path.exists(POOL_CSV):
        return out
    want = {n.lower() for n in names} | {n.split(" // ")[0].lower() for n in names}
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            if n in want or n.split(" // ")[0] in want:
                legs = {x.strip() for x in (r.get("Legalities") or "").split(";") if x.strip()}
                out[n] = legs
                out.setdefault(n.split(" // ")[0], legs)
    return out


# A card's value can lie ENTIRELY in its relationship to a list you already have, and
# every scoring model here grades a card on its own text. Two consequences drove this:
#
#  1. A pile graded ONCE against an early plan keeps those verdicts after the plan
#     changes. Deck 46's 76-card pile was screened against a "one enormous body" plan;
#     when the plan became "several growing lifelink bodies", only the cards the user
#     re-raised were re-graded, and the rest carried stale reasoning forward. Shrike
#     Force, Linden, The Wind Crystal and Prayer of Binding all sat in that bucket.
#  2. Nothing asked whether a candidate is a STRICT UPGRADE of a card already in the
#     deck. Prayer of Binding is Liminal Hold plus Flash — identical cost, identical
#     text — and Liminal Hold was in the 60 while Prayer of Binding sat on the excluded
#     list with a note comparing it to a different card entirely.
#
# `screen` answers both by re-scoring a whole candidate list against the deck AS IT IS
# NOW, so the answer cannot be stale, and by naming the incumbents each candidate beats.
_UPGRADE_SELF_RE = re.compile(r"\bthis (?:creature|permanent|enchantment|artifact|land|spell|card)\b", re.I)


def _upgrade_clauses(name, text):
    """A card's text as a set of comparable clauses: reminder text stripped, the card's
    own name normalised to a placeholder (older templating self-references by name, newer
    says "this creature"), split on sentence and line breaks.

    Deliberately a TEXT-CONTAINMENT test with no judgment in it. That makes it blind to
    most real upgrades — but its false-positive rate is near zero, which is the right
    error direction for a flag whose whole claim is "you already run a worse version of
    this card"."""
    t = _REMINDER_RE.sub(" ", (text or "").lower())
    for nm in filter(None, [(name or "").lower(), (name or "").lower().split(" // ")[0],
                            (name or "").lower().split(",")[0]]):
        t = t.replace(nm, "~")
    t = _UPGRADE_SELF_RE.sub("~", t)
    return {c.strip(" .;") for c in re.split(r"[\n.]", t) if c.strip(" .;")}


def strict_upgrades(cand_name, cand_text, cand_mv, cards, carddata, mana, cand_pt=(None, None)):
    """In-deck card names that `cand` STRICTLY upgrades — every clause of the incumbent's
    text is present in the candidate's, at the same or lower mana value, AND the candidate
    does strictly more (an extra clause, or the same text for less mana). Color identity
    is deliberately NOT part of the test — `screen` flags off-color separately, and
    folding it in here would make a text-containment result depend on the deck's colors.
    Two cards with identical text and cost are
    NOT an upgrade of each other — that is redundancy, which is a different (and often
    good) thing."""
    cc = _upgrade_clauses(cand_name, cand_text)
    if not cc:
        return []
    out = []
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS or nl == (cand_name or "").lower():
            continue
        cd = carddata.get(nl) or {}
        if "Land" in _primary_type(cd.get("type") or ""):
            continue
        ic = _upgrade_clauses(n, cd.get("text") or "")
        if not ic or not ic <= cc:
            continue                                   # incumbent says something the candidate doesn't
        imv = (mana.get(nl) or (None, None))[1]
        if cand_mv is not None and imv is not None and cand_mv > imv:
            continue                                   # costs more — not strict
        # POWER / TOUGHNESS are part of "strictly more" (BS8-32): the text-only test called
        # a 1/2 for {1}{W} a ★ STRICT UPGRADE of a 2/3 for {2}{W} with the same clause set
        # — 121 such pool groups. A smaller body on either axis is not an upgrade; a bigger
        # one at equal text and cost is. `card_power` returns None for `*`/X, which
        # compares as unknown (neither blocks nor grants).
        cp, ct = card_power(cand_pt[0]), card_power(cand_pt[1])
        ip, it = card_power(cd.get("power")), card_power(cd.get("toughness"))
        if (cp is not None and ip is not None and cp < ip) or \
                (ct is not None and it is not None and ct < it):
            continue                                   # a smaller body — not strict
        bigger = (cp is not None and ip is not None and cp > ip) or \
                 (ct is not None and it is not None and ct > it)
        strictly_more = len(cc) > len(ic) or bigger or (
            cand_mv is not None and imv is not None and cand_mv < imv)
        if strictly_more:
            out.append(n)
    return out


def cmd_screen(args):
    """Re-score a list of CANDIDATE cards against a deck as it stands right now — the
    anti-staleness pass for a build that has changed plan since the pile was first graded,
    and the one place that flags a candidate as a STRICT UPGRADE of a card already in the
    60. Reads names from args or stdin (one per line, optional leading quantity, `#`
    comments ignored). Prints full oracle text, because a verdict surface that hides the
    evidence is how a card gets mis-graded twice."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    dmeta, cards = parse_deck_file(d["path"])
    carddata, cardmeta, mana = load_card_data(), load_card_meta(), load_mana()
    legal, rar = load_legalities(), load_rarities()
    _, _, qty = load_collection()
    fmt = (args.format or dmeta.get("format") or "").strip().lower()
    if fmt in ("any", "all"):
        fmt = ""

    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = cardmeta.get(n.lower())
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    central = _central_themes(theme_w)
    d_int, d_ca = deck_role_counts(cards, carddata)
    sig = _strong_signature_themes(dmeta, cards, cardmeta)
    in_deck = {_ms_key(n) for q, n, s, c in cards}   # G-63: front-face join
    declared = set(_declared_colors(dmeta) or _deck_castable_colors(dmeta, cards, mana))

    raw = list(args.names or [])
    if not raw or raw == ["-"]:
        raw = sys.stdin.read().splitlines()
    queries = []
    for ln in raw:
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        m = re.match(r"^\s*\d+\s+(.*)$", ln)
        queries.append((m.group(1) if m else ln).strip())

    rows, unresolved, ambiguous = [], [], []
    sqidx = _squash_index(carddata, lambda k: carddata[k].get("name") or k)
    for qname in queries:
        key, cands = _resolve_card_name(
            qname, carddata, lambda k: carddata[k].get("name") or k, sqidx)
        if not key:
            (ambiguous if cands else unresolved).append((qname, cands))
            continue
        cd = carddata[key]
        name = cd.get("name") or qname
        nl = name.lower()
        text = cd.get("text") or ""
        cost, mv = (mana.get(nl) or mana.get(nl.split(" // ")[0]) or (None, None))
        ident = card_colors(cd.get("colors"))
        ctags = set(cardmeta.get(nl, {}).get("synergies", []))
        shared = sorted(ctags & central)
        strength = fit_strength(shared, theme_w, text, d_int, d_ca, sig)
        roles = sorted(classify_roles(text))
        ax = doubler_axis(text)
        sup = doubler_support(ax, cards, carddata, doubler_restriction(text)) if ax else 0
        ups = strict_upgrades(name, text, mv, cards, carddata, mana,
                              cand_pt=(cd.get("power"), cd.get("toughness")))
        legs = legal.get(nl) or legal.get(nl.split(" // ")[0]) or set()
        cast_ok, cast_note = _candidate_castability(cost, ident, declared)
        rows.append(dict(name=name, cost=cost, mv=mv, text=text, roles=roles,
                         strength=strength, shared=shared, axis=ax, support=sup,
                         upgrades=ups, ident=ident,
                         owned=owned_qty(qty, name), rar=rar.get(nl, "?"),
                         illegal=bool(fmt and legs and pool_format_key(fmt) not in legs),
                         castable=cast_ok, cast_note=cast_note,
                         # `in_deck` holds _ms_key keys while `nl` is the resolved card's
                         # FULL display name, so every pool-keyed DFC read as absent and
                         # `screen` graded a maindecked card as a fresh candidate —
                         # silently, on the surface G-47 points at for stale verdicts.
                         present=_ms_key(nl) in in_deck))

    # The header counts RESOLVED candidates, not INPUTS. It used to print len(queries),
    # so `screen 52 "Demon"` announced "screening 1 candidate(s)" and then graded zero —
    # and, worse, a pile passed with broken shell quoting announced "222 candidate(s)"
    # when 83 names were given. The unresolved/ambiguous block moved ABOVE the results
    # for the same reason: it used to print after ~200 lines of output, which is exactly
    # where a reader does not look. (Use `-` and one name per line to avoid the whole
    # class of problem — `screen` reads stdin.)
    print(f"Deck {d['id']}: {d['name'] or d['path']} — screening {len(rows)} candidate(s) "
          f"against the CURRENT list"
          + (f" ({len(queries)} name(s) given)" if len(rows) != len(queries) else ""))
    print(f"Central themes: {', '.join(sorted(central)) or '(none)'}"
          + (f"  ·  format {fmt}" if fmt else ""))
    print("Re-scored now, so nothing here is carried over from an earlier plan.")
    if ambiguous:
        print("\nAmbiguous (be more specific — not guessed at):")
        for q, cands in ambiguous:
            print(f"    {q!r} → {'; '.join(cands[:6])}")
    if unresolved:
        print("\nNot found (fix the name, don't guess): "
              + ", ".join(q for q, _ in unresolved))
    print()

    order = {"KEY": 0, "role-player": 1, "tangential": 2}
    rows.sort(key=lambda r: (bool(r["present"]), r["illegal"], not r["castable"],
                             order.get(r["strength"], 3), -r["support"], r["name"].lower()))
    for r in rows:
        flags = []
        if r["present"]:
            flags.append("already in the deck")
        if r["illegal"]:
            flags.append(f"⚠ NOT legal in {fmt}")
        if r["cast_note"]:
            flags.append(r["cast_note"])
        if r["upgrades"]:
            flags.append("★ STRICT UPGRADE of " + ", ".join(r["upgrades"]))
        if r["axis"] and r["support"]:
            flags.append(f"✱ multiplier — doubles {r['axis']} ({r['support']} feeder(s) here)")
        own = f"×{r['owned']}" if r["owned"] else f"craft {r['rar']}"
        print(f"  {r['strength']:<12} {r['name'][:34]:36} {(r['cost'] or '?'):12} "
              f"{own:9} {', '.join(r['roles']) or '—'}")
        if r["shared"]:
            print(f"       shares: {', '.join(r['shared'])}")
        for f in flags:
            print(f"       {f}")
        # Text ON BY DEFAULT (G-52): it sat behind an opt-in `--full` that no skill and
        # no session ever passed, so the highest-volume verdict surface handed out
        # KEY/tangential labels with no evidence — five 68b cards were mis-graded from
        # exactly those labels in one 2026-08 session, every one corrected by the user.
        # Evidence on a verdict surface must be opt-OUT, never opt-in (the G-40 shape:
        # a capability nothing asks for is invisible).
        if not getattr(args, "no_text", False):
            for line in (r["text"] or "(no text)").split("\n"):
                print(f"         {line}")
        print()
    # SATURATION. KEY means "shares the deck's signature theme", and when that theme is
    # broad the label fires on everything: measured at 51% of 83 candidates on deck 52 and
    # 45% of 119 on 52a, where the strict signature is {graveyard, reanimator} and half the
    # black pool carries `graveyard`. Tightening was TRIED and rejected — requiring a
    # non-generic signature theme dropped deck 30's KEY rate 21%->1% and demoted
    # Innkeeper's Talent, the counter-doubler-in-a-counters-deck rescue the signature
    # branch exists for. So this REPORTS rather than re-scores, like the protection axis
    # and the role-count confidence: a reader who knows the label is saturated can still
    # use the ordering, but will not mistake KEY for a recommendation.
    keys = [r for r in rows if r["strength"] == "KEY"]
    if len(rows) >= 10 and len(keys) / len(rows) >= _SCREEN_KEY_SATURATED:
        by_theme = {}
        for r in keys:
            for t in r["shared"]:
                if t in sig:
                    by_theme[t] = by_theme.get(t, 0) + 1
        top = sorted(by_theme.items(), key=lambda kv: (-kv[1], kv[0]))[:2]
        print(f"⚠ KEY is SATURATED here — {len(keys)} of {len(rows)} candidates "
              f"({len(keys) / len(rows) * 100:.0f}%)"
              + (f", mostly on `{'`, `'.join(t for t, _ in top)}`" if top else "")
              + ". A label that fires on half the pile is not a shortlist. Read the shared"
              " themes and the oracle text, and treat the ORDER as the signal, not the word.")
    print("Trust KEY, judge role-player, read tangential as 'probably not here'. A ★ strict "
          "upgrade is a TEXT-CONTAINMENT test — it is deliberately conservative and misses "
          "most real upgrades, so its silence is not a verdict.")
    return 0


def _resolve_check(target, idx):
    """`resolve --check <deck>`: verify an existing deck file's `(SET) COLLECTOR#`
    fields against known printings, STRICTLY (DD-2).

    Eleven hand-written collector numbers shipped wrong across two consecutive
    from-scratch drafts (7 in deck 76, 4 in deck 77) — every one a real set with a
    wrong number, i.e. exactly the class `check_all` keeps SOFT (G-65: the pool keys
    one printing per card, so a legitimate alternate printing is indistinguishable
    there). They were caught only by a hand-run diff against resolver output. In a
    freshly DRAFTED file the lines are supposed to COME from `resolve`, so an unheld
    printing here is presumed a typo and fails hard; basics stay exempt (several
    arts per set). Prints the resolver's preferred printing beside each flagged line
    so the fix is a paste."""
    d = find_deck(target)
    path = d["path"] if d else target
    if not os.path.exists(path):
        eprint(f"--check: no deck id or file {target!r}.")
        return 1
    _meta, cards = parse_deck_file(path)
    if not cards:
        eprint(f"--check: no parseable card lines in {path}.")
        return 1
    bad_set, unverified = printing_problems(cards)
    label = d["id"] if d else os.path.relpath(path, REPO_ROOT)
    if not bad_set and not unverified:
        print(f"✓ {label}: every stated printing is a known one "
              f"({len(cards)} line(s); basics exempt).")
        return 0
    for n, s, c in bad_set:
        print(f"✗ {n} ({s}) {c} — set code exists NOWHERE in pool or library.")
    for n, s, c, known in unverified:
        pref = idx.get(n.lower()) or idx.get(n.split(' // ')[0].lower())
        hint = f"resolver has: ({pref[1]}) {pref[2]}" if pref else \
               f"known: {', '.join(f'({ks.upper()}) {kc}' for ks, kc in known)}"
        print(f"✗ {n} ({s}) {c} — not a printing this repo holds; {hint}.")
    print(f"\n{len(bad_set) + len(unverified)} bad printing(s) in {label}. Replace each "
          "line with `deck.py resolve` output — never hand-write `(SET) #` (G-65).")
    return 1


def _resolve_fix(target, idx, apply):
    """`resolve --fix <deck>`: rewrite a deck file's bad `(SET) COLLECTOR#` fields to the
    resolver's printing, in place, preserving everything else on the line VERBATIM.

    `--check` (DD-2) reports these and tells you to replace each line with `resolve`
    output — which, done by hand across many lines, is exactly the operation G-65 forbids
    and G-77 was written about: relocating four lines by hand in one session invented two
    collector numbers. A gate whose only remedy is a forbidden edit produces a second,
    quieter error class, so the repair has to be mechanical.

    Earned by the 2026-08-24 Ingest audit: `build_pool` recorded printings from spoiled
    but UNRELEASED sets, so 109 lines across 47 decks named a set three months out. That
    is too many to retype safely, and every one of them passes `--check` today because the
    set and number are both real — they are simply not available yet.

    Only the printing fields are touched. The quantity, the card name and any trailing
    comment are carried over from the original line, so a rewrite cannot restructure the
    file. Dry-run by default; `--apply` goes through `_safe_write_lines`, so the INV-04
    parse and the copy-count guard both run before anything replaces the file."""
    d = find_deck(target)
    path = d["path"] if d else target
    if not os.path.exists(path):
        eprint(f"--fix: no deck id or file {target!r}.")
        return 1
    _meta, cards = parse_deck_file(path)
    if not cards:
        eprint(f"--fix: no parseable card lines in {path}.")
        return 1
    label = d["id"] if d else os.path.relpath(path, REPO_ROOT)
    bad_set, unverified = printing_problems(cards)
    # Key on (name, stated set, stated collector) so only the exact lines `--check`
    # objects to are considered — a card correctly listed twice under two printings must
    # not have its good line rewritten because its bad twin matched by name.
    wanted = {(n, s, c) for n, s, c in bad_set} | {(n, s, c) for n, s, c, _k in unverified}
    # BASICS: `printing_problems` exempts them, correctly — Arena prints several arts per
    # set and the pool carries one, so their collector numbers cannot be validated. But a
    # basic whose SET CODE exists nowhere is wrong for exactly the same reason a nonbasic
    # is, and it is equally unimportable. 76 of the 109 lines the 2026-08-24 audit found
    # were basics pointing at an unreleased set, invisible to the check that was supposed
    # to catch them. Only the set-code half is applied here; a basic's number stays exempt.
    _known_sets = known_printings()[1]
    for _q, n, sc, cl in cards:
        if n.lower() in BASICS and sc and sc.lower() not in _known_sets:
            wanted.add((n, sc, cl or ""))
    if not wanted:
        print(f"✓ {label}: every stated printing is a known one — nothing to fix.")
        return 0

    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    fixed, unresolved = [], []
    for i, ln in enumerate(lines):
        # Strip the inline comment BEFORE matching, the way every other line-rewriting
        # site here does (`_swap_edit_lines`, `reconcile_lines`): LINE_RE anchors on `$`,
        # so a trailing `# note` otherwise swallows the printing into the name group and
        # the line silently fails to match.
        m = LINE_RE.match(ln.split("#", 1)[0].strip())
        if not m or ln.strip().startswith("#"):
            continue
        qty, name, setc, coll = m.group(1), m.group(2).strip(), m.group(3), m.group(4)
        if (name, setc or "", coll or "") not in wanted:
            continue
        pref = idx.get(name.lower()) or idx.get(name.split(" // ")[0].lower())
        if not pref:
            unresolved.append(name)
            continue
        comment = _line_comment(ln)
        new = f"{qty} {pref[0]} ({pref[1]}) {pref[2]}" + (f"  {comment}" if comment else "")
        if new != ln:
            fixed.append((ln.strip(), new.strip()))
            lines[i] = new
    for old, new in fixed:
        print(f"  {old}\n    -> {new}")
    for n in unresolved:
        print(f"  ⚠ {n}: no printing in the pool or library — left unchanged.")
    if not fixed:
        print(f"{label}: nothing rewritten.")
        return 0 if not unresolved else 1
    if not apply:
        print(f"\n{len(fixed)} line(s) would change in {label} (dry run — pass --apply).")
        return 0
    total = sum(q for q, *_ in cards)
    try:
        bak = _safe_write_lines(path, lines, total)
    except ValueError as e:
        eprint(f"Not saved: {e}")
        return 1
    print(f"\nFixed {len(fixed)} line(s) in {label}; wrote "
          f"{os.path.relpath(path, REPO_ROOT)} (backup: {os.path.basename(bak)}).")
    return 1 if unresolved else 0


def cmd_resolve(args):
    """Turn card NAMES into ready-to-paste deck lines `<qty> <Name> (<SET>) <#>` with a valid
    printing (exact → DFC front → unique substring; owned printing preferred, else the pool's).
    Reads names from args or stdin (one per line, optional leading quantity). Reports
    unresolved / ambiguous names instead of guessing — the scaffolding step a from-scratch
    build otherwise does by hand."""
    idx = _printing_index()
    if not idx:
        eprint("No card data — build card-pool.csv (build_pool.py) / card-library.csv first.")
        return 1
    if getattr(args, "check", None):
        return _resolve_check(args.check, idx)
    if getattr(args, "fix", None):
        return _resolve_fix(args.fix, idx, bool(getattr(args, "apply", False)))
    raw = list(args.names or [])
    if not raw or raw == ["-"]:
        raw = [ln for ln in sys.stdin.read().splitlines()]
    lines, unresolved, ambiguous = [], [], []
    sqidx = _squash_index(idx, lambda k: idx[k][0])
    for ln in raw:
        ln = ln.strip()
        if not ln or ln.lstrip().startswith("#"):
            continue
        m = re.match(r"^\s*(\d+)\s+(.*)$", ln)          # optional leading quantity
        qty, query = (m.group(1), m.group(2)) if m else ("1", ln)
        # Shared resolver: exact -> DFC front -> squashed punctuation -> unique substring,
        # deduped by DISPLAY name (a DFC's front and full name are two keys but ONE card).
        key, cands = _resolve_card_name(query, idx, lambda k: idx[k][0], sqidx)
        if not key:
            (ambiguous if cands else unresolved).append(
                (query, cands[:6]) if cands else query)
            continue
        disp, setc, coll = idx[key]
        lines.append(f"{qty} {disp} ({setc}) {coll}".rstrip())
    for ln in lines:
        print(ln)
    # LEGALITY WARNING. `resolve` is the scaffolding step for a from-scratch deck, and it
    # used to hand back any card it could find a printing for — which is how Bloodchief
    # Ascension, a TLE supplemental card, reached a finished 60 and was only caught two
    # validation steps later by `deck.py legal`. Surfacing it here means the name list is
    # checked at the moment it becomes deck lines.
    fmt = (getattr(args, "format", None) or "standard").strip().lower()
    if fmt and fmt != "any":
        resolved = [_card_line_name(ln) or "" for ln in lines]
        legal = _legality_of([n for n in resolved if n])
        illegal = [n for n in resolved
                   if n and legal.get(n.lower()) is not None
                   and fmt not in legal.get(n.lower(), set())]
        if illegal:
            eprint(f"\n⚠ NOT legal in {fmt} ({len(illegal)}): {', '.join(illegal)}")
            eprint("   Resolving a printing is not a legality check — pass --format any to "
                   "silence, or pick a different card.")
    if ambiguous:
        eprint("\n⚠ ambiguous (be more specific):")
        for q, opts in ambiguous:
            eprint(f"    {q!r} → {'; '.join(opts)}")
    if unresolved:
        eprint("\n⚠ not found:")
        for q in unresolved:
            eprint(f"    {q!r}")
    # COUNT SUMMARY. Two consecutive from-scratch drafts (decks 60 and 60a) went to
    # validation at 59 cards because nothing on this path counts — the skill even
    # warns "the resolver won't catch an off-by-one", which was a description of a
    # gap, not a law (broad-implement #4). Totals go to stderr so a piped paste of
    # the resolved lines stays clean.
    total = sum(int((re.match(r"^(\d+)\s", ln) or [None, "1"])[1]) for ln in lines)
    eprint(f"\nTotal: {total} card(s) across {len(lines)} line(s).")
    expect = getattr(args, "expect", None)
    if expect is not None and total != expect:
        eprint(f"✗ expected {expect}, resolved {total} — off by {total - expect:+d}.")
        return 1
    return 1 if (unresolved or ambiguous) else 0


def cmd_suggest_homes(args):
    """For a card you own, scan EVERY deck: where is it both castable and on-theme,
    is it already there, and what's the weakest card it could replace? Automates
    the manual 'which of my decks does this new card improve' fit pass."""
    card = args.card
    carddata = load_card_data()
    cardmeta = load_card_meta()
    mana = load_mana()
    cd = carddata.get(card.lower())
    if not cd:
        # Resolve a partial name the way card.py does. Exact + DFC front are already keyed
        # in carddata; this adds UNIQUE-substring matching so 'Ojer Taq' resolves to
        # 'Ojer Taq, Deepest Foundation // …' (a God//Land DFC) instead of "not found".
        ql = card.strip().lower()
        subs = sorted({c0["name"] for k, c0 in carddata.items() if ql in k}, key=len)
        if len(subs) == 1:
            card = subs[0]
            cd = carddata.get(card.lower())
        elif len(subs) > 1:
            eprint(f"{args.card!r} is ambiguous — matches: " + "; ".join(subs[:8])
                   + (" …" if len(subs) > 8 else "") + "\nUse a more specific name.")
            return 1
    if not cd:
        eprint(f"{card!r} not found in card-library.csv or card-pool.csv — check spelling.")
        return 1
    # Format-legality: a card can only be a "home" for a deck it's LEGAL in that deck's
    # format (Triumph of the Hordes is not Standard-legal, so it isn't a Standard home).
    # Reuses the pool's Legalities snapshot; unverified (pool-absent) legalities are
    # treated as legal, matching `suggest`/`legal`. `--any-format` disables the filter.
    any_format = getattr(args, "any_format", False)
    _pool_idx, _ = _pool_rotation_index()
    _cinfo = _pool_idx.get(card.lower()) or _pool_idx.get(card.split(" // ")[0].lower())
    card_legals = _cinfo[1] if _cinfo else None
    ccols = card_colors(cd.get("colors"))
    ctags = set(cardmeta.get(card.lower(), {}).get("synergies", []))
    # Card MV for the curve co-signal (#5): a top-heavy card is a worse home for a
    # low-curve deck than a midrange one — see _home_curve_fit. Also feeds the fixer
    # RATE below, so `is_fixer` is derived after it.
    _cmv = mana.get(card.lower()) or mana.get(card.split(" // ")[0].lower())
    card_mv = _cmv[1] if _cmv and _cmv[1] is not None else None
    fixer_rate = _fixer_rate(cd.get("text") or "", card_mv)
    is_fixer = bool(fixer_rate)

    print(f"Card: {card}  [{'/'.join(sorted(ccols)) or 'Colorless'}]  ({cd['type']})")
    _fixnote = ("   [rainbow fixer — value scales with a deck’s color count"
                + ("" if fixer_rate >= _FIXER_KEY_RATE
                   else f"; single source at MV {card_mv} — discounted") + "]")
    print(f"Themes: {', '.join(sorted(ctags)) or '(none)'}"
          f"{_fixnote if is_fixer else ''}")
    # The VERDICT surfaces are where the misreads clustered this cycle. `cuts` and `swap`
    # print full oracle text and produced the fewest bad calls; suggest-homes hands out
    # KEY / role-player / tangential labels with NO text, which is how Genesis Wave was
    # rated KEY for a deck whose engine it mills away. One card, one text block, always
    # printed: six lines of cost so the label is never the only evidence.
    import textwrap as _tw
    print()
    for _para in (cd.get("text") or "(no oracle text on file)").split("\n"):
        for _ln in (_tw.wrap(_para, width=84) or [""]):
            print(f"    {_ln}")
    print()

    # Which quantity (if any) this card DOUBLES — computed once; the per-deck half is the
    # density of that quantity, which is what the boost scales with.
    _daxis = doubler_axis(cd.get("text") or "")
    _drestrict = doubler_restriction(cd.get("text") or "") if _daxis else None
    results = []
    skipped_illegal = 0
    # Roster only (BS-14): a retired/example deck must not be rated a KEY home —
    # `suggest`'s Decks column already excludes them via _deck_fingerprints, and the
    # two surfaces answering "where does this card fit" must agree on the universe.
    _ce = mana.get(card.lower()) or mana.get(card.split(" // ")[0].lower())
    for dd in roster_decks():
        dmeta, cards = parse_deck_file(dd["path"])
        castable = _deck_castable_colors(dmeta, cards, mana)
        # Read castability from the PRINTED COST, not from color identity — the same
        # `_candidate_castability` `suggest`/`--lands`/`--ramp`/`--interaction` use.
        # This was the LAST identity-subset test on a recommender path, and it is the
        # G-58 rule failing in the tool that exists to apply it: `{2}{G/U}{G/U}`
        # Thranduil, Sindarin Liege reads identity {G,U}, which is not a subset of a
        # BG deck's colours — so an Elf lord was withheld from the roster's 16-Elf
        # deck (16 green sources, both pips payable off green) and every other hybrid
        # was withheld the same way. `mana` fell back to identity when a cost is
        # missing, which is what `_candidate_castability` does with cost="" anyway.
        # NO COST ON FILE FALLS BACK TO IDENTITY, which is not a detail — it is the
        # difference between a fix and a regression. `_candidate_castability("")`
        # returns castable-with-a-note, right for triaging a PILE (show it, annotate
        # it) and wrong for a recommender GATE: a LAND carries no cost, so the bare
        # cost-aware test offered WUR Mystic Monastery to decks in none of those
        # colours — a land's whole value is the colours it produces. `wishlist`'s
        # `_castable_in` already resolves this exact case the same way ("no cost data
        # -> identity fallback"); this is that convention, not a new one.
        if _ce and _ce[0]:
            cast_ok, _cnote = _candidate_castability(_ce[0], ccols, castable)
        else:
            cast_ok = ccols.issubset(castable)
        if not cast_ok:
            continue
        # Castability above reads the cost but still cannot see pip DEPTH;
        # pip_depth_warning supplies the arithmetic (G-32).
        # load_mana values are (cost, mana_value) tuples, not dicts.
        pipwarn = pip_depth_warning(_ce[0] if _ce else "",
                                    deck_color_sources(cards, cardmeta, carddata),
                                    total=sum(q for q, *_ in cards))
        # Skip a deck whose format the card isn't legal in (see card_legals above).
        if not any_format and card_legals:
            dfmt = pool_format_key(dmeta.get("format"))
            if dfmt and dfmt not in card_legals:
                skipped_illegal += 1
                continue
        theme_w = {}
        d_mvs = []
        for q, n, s, c in cards:
            if n.lower() in BASICS:
                continue
            m = cardmeta.get(n.lower())
            if m:
                for t in m["synergies"]:
                    theme_w[t] = theme_w.get(t, 0) + q
            cdn = carddata.get(n.lower())
            if cdn and "Land" not in _primary_type(cdn.get("type") or ""):
                e = mana.get(n.lower())
                if e and e[1] is not None:
                    d_mvs += [e[1]] * q
        shared = sorted(ctags & _central_themes(theme_w))
        shared = _drop_cost_themes(shared, cards, carddata)
        if not shared:
            continue
        deck_avg_mv = sum(d_mvs) / len(d_mvs) if d_mvs else 0.0
        # BOTH sides through `_ms_key` (G-63). The card side was front-normalized and the
        # DECK side was not, so a deck storing the full `Front // Back` spelling read as
        # not running the card — printing `in? no` plus a cut hint, i.e. advising the deck
        # make room for a card already in its 60.
        already = _ms_key(card) in {_ms_key(n) for _, n, _, _ in cards}
        fit = sum(theme_w.get(t, 0) for t in shared)
        d_int, d_ca = deck_role_counts(cards, carddata)
        # STRICT (>=2 protected cards) — see fit_strength's docstring: the loose
        # union made a generic theme a signature and minted KEY nearly everywhere.
        sig = _strong_signature_themes(dmeta, cards, cardmeta)
        strength = fit_strength(shared, theme_w, cd.get("text") or "", d_int, d_ca, sig)
        # Color-fixer overlay: a rainbow fixer's worth scales with the deck's color
        # count, which theme-overlap can't see. In a 3+-color deck it's at least a
        # role-player manabase upgrade; in a 4+-color deck it's a KEY one (the fixing
        # is doing real work every game). The fit bump is BOUNDED (fixer_boost) so it
        # nudges ordering among fixer-eligible decks without dwarfing a real theme
        # match; the strength promotion never DEMOTES a fit fit_strength already rated
        # KEY. This closes the Overlord → 17/21a miss without touching mono-color decks.
        # The promotion is now rate-gated too: only a fixer that BUYS enough fixing
        # (`_fixer_rate` >= _FIXER_KEY_RATE — broad, or a cheap single source) is worth
        # an automatic KEY. A 3-mana one-mana-any-colour dork gets the role-player step
        # instead, which is what it is. Without this, colour count alone minted KEY and
        # the label sorts ahead of fit, so nothing downstream could correct it.
        if is_fixer and len(castable) >= 3:
            fit += _fixer_boost(len(castable), rate=fixer_rate)
            if len(castable) >= 4 and fixer_rate >= _FIXER_KEY_RATE:
                strength = "KEY"
            elif strength == "tangential":
                strength = "role-player"
        # DOUBLER overlay, same shape as the fixer one: a card that doubles tokens /
        # counters / triggers is worth the deck's DENSITY of that thing, which theme
        # overlap cannot see (it reads membership, not magnitude). Bounded, and it only
        # ever promotes a tangential fit one step — never demotes, never overrides a KEY.
        dsupport = (doubler_support(_daxis, cards, carddata, _drestrict)
                    if _daxis else 0)
        if dsupport:
            _dboost = doubler_boost(dsupport, _daxis)
            fit += _dboost
            # Mirrors the fixer overlay's promotion rule. A doubler in a deck that really
            # does the thing IS a key card, and the strength label sorts ahead of fit — so
            # without this the boost could not reorder anything: Exalted Sunborn stayed
            # behind every KEY row no matter how many token-makers the deck fielded.
            if dsupport >= doubler_calib(_daxis)[1]:
                strength = "KEY"
            elif _dboost and strength == "tangential":
                strength = "role-player"
        # Bounded curve co-signal (#5): gently sort a top-heavy card BELOW efficient fits
        # in an aggressive low-curve deck (never boosts, never relabels — see
        # _home_curve_fit). `top_heavy` flags the row so the clunk is visible, not silent.
        curve_mult = _home_curve_fit(card_mv, deck_avg_mv)
        fit *= curve_mult
        top_heavy = curve_mult < 1.0
        cut = (None if already else
               _weakest_cut(dmeta, cards, cardmeta, carddata, add_is_fixer=is_fixer))
        results.append((fit, dd["id"], already, shared, cut, strength, top_heavy, pipwarn))

    if skipped_illegal:
        print(f"({skipped_illegal} castable deck(s) skipped — the card isn't legal in "
              f"their format; use --any-format to include them.)\n")
    if not results:
        print("No deck is both castable and shares a central theme with this card.\n"
              "(Off-color everywhere, its themes are too generic, or it's format-illegal "
              "everywhere — try `deck.py suggest <id>` from a specific deck instead.)")
        return 0
    # Sort KEY fits first (then role-player, then tangential), then by fit weight —
    # so the decks the card most belongs in lead, differentiating a key from a
    # tangential home (F04).
    _srank = {"KEY": 0, "role-player": 1, "tangential": 2}
    results.sort(key=lambda r: (_srank.get(r[5], 3), -r[0], r[1]))
    print(f"  {'deck':5} {'strength':11} {'fit':>4}  {'in?':3}  shared themes  ·  suggested cut")
    print("  " + "-" * 82)
    for fit, did, already, shared, cut, strength, top_heavy, pipwarn in results:
        tag = "yes" if already else "no"
        hint = "already maindecked" if already else (f"cut ~ {cut}" if cut else "")
        if top_heavy:
            hint = (hint + "  " if hint else "") + "⚠ top-heavy for this curve"
        if pipwarn:
            _col, _pips, _have, _want = pipwarn
            hint = ((hint + "  " if hint else "")
                    + f"⚠⚠ {_pips}x{{{_col}}} vs {_have} sources")
        print(f"  {did:5} {strength:11} {fit:>4.0f}  {tag:3}  {', '.join(shared[:3]):28}  {hint}")
    _pw = [r for r in results if r[7]]
    if _pw:
        _col, _pips, _have, _want = _pw[0][7]
        _need = f"~{_want}" if _want else "more than a 60-card deck can hold"
        print(f"\n⚠⚠ = PIP DEPTH. Castability here is a SET test (the card's colours ⊆ the "
              f"deck's), which cannot see that this card wants {_pips} {{{_col}}} in one cast. "
              f"Those decks hold as few as {_have} {{{_col}}} sources; {_need} is what a 70% "
              "turn-5 cast needs. Identity says yes, the arithmetic says no — verify before "
              "spending a wildcard.")
    if any(r[6] for r in results):
        print(f"\n⚠ = the card (MV {card_mv}) sits well above that deck's average curve — a "
              "win-more/top-heavy add there; grade it from text.")
    strong = [r for r in results if not r[2]]
    if len(strong) >= 2:
        print(f"\nCastable + on-theme in {len(strong)} decks it's not already in — one owned "
              "copy serves every deck in Arena, so slot it into all that earn it.")
    print(f"\nGrade each from full text: `deck.py cuts <id>`, then "
          f'`deck.py swap <id> --cut <weak> --add "{card}"` (shows both cards\' full text).')
    return 0


def _early_drops_note(vec):
    """`early_drops` rendered with the share of it that only makes MANA. The bare int
    still feeds `tier_band` and the F10 guard; this is what a human should read, the
    same split `count_conf` makes for the role counts (G-48)."""
    n, m = vec.get("early_drops", 0), vec.get("early_mana", 0)
    return f"{n} ({m} mana source{'s' if m != 1 else ''})" if m else str(n)


def deck_quality_vector(d):
    """A deck's measurable QUALITY vector (F10), from the same primitives the CLI
    uses — so a cut/swap can be checked for regression before/after: buildable,
    uncastable strays, interaction + card-advantage role counts, curve (avg nonland
    MV + early-drop count), and central-theme coverage."""
    dmeta, cards = parse_deck_file(d["path"])
    mana, carddata, cardmeta = load_mana(), load_card_data(), load_card_meta()
    _, _, qty = load_collection()
    # Through the ONE definition (G-70). BS2-22 fixed the per-LINE comparison here and
    # left a hand-rolled per-name loop behind, keyed on the raw DISPLAY name where
    # `deck_requirements` keys lowercase — so this and `check` could still disagree on a
    # deck listing one card under two spellings, on the number feeding `preflight`'s
    # verdict and `quality --vs`'s "became UNbuildable" flag (broad-scan BS5-04). Basics
    # need no special case: `owned()` already reports them unlimited.
    missing, short = deck_build_gap(cards, qty)
    theme_w, mvs, early = {}, [], 0
    early_mana = 0
    creatures = reach = 0
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS:
            continue
        cd = carddata.get(nl)
        tline = (cd.get("type") if cd else "") or ""
        m = cardmeta.get(nl)
        tags = set(m["synergies"]) if m else set()
        if cd and "Land" not in _primary_type(tline):
            entry = mana.get(nl)
            if entry and entry[1] is not None:
                mvs += [entry[1]] * q
                if entry[1] <= 2:
                    early += q
                    # A cheap MANA SOURCE is not a cheap THREAT, and `early_drops`
                    # counts them alike — which is how a curve argument gets made from
                    # a number that does not support it (deck 59, 2026-08-31: four of
                    # its nine "early drops" tap for mana, so "nine early drops" read
                    # as a fast start it does not have). Reminder text is stripped
                    # first, the way every other text predicate here reads a card.
                    if _MANA_SOURCE_RE.search(_REMINDER_RE.sub(" ", cd.get("text") or "")):
                        early_mana += q
        if "Creature" in _primary_type(tline):
            creatures += q
        # Reach = ability to CLOSE a game (the aggro axis): burn/drain reach, or an
        # evasive body that keeps connecting. Used only by the archetype-aware floor.
        if ("Burn / drain" in classify_roles((cd.get("text") if cd else "") or "")
                or (tags & _EVASION_TAGS)):
            reach += q
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    declared_hdr = _declared_colors(dmeta)
    declared = declared_hdr or _deck_castable_colors(dmeta, cards, mana)
    uncast, _off, _off_ability, _intended = _castability(
        cards, declared, mana, carddata, _uncastable_ok(dmeta))
    _tally = role_tally(cards, carddata)
    d_int, d_ca = _tally["interaction"], _tally["card_advantage"]
    return {
        "buildable": missing == 0 and short == 0, "missing": missing, "short": short,
        # Whether castability was audited against a DECLARED identity. Without a
        # `#: colors:` header, `declared` is derived from the deck's own cards, so
        # uncastable is 0 by construction (unverified, not a clean bill) — audit F16.
        "colors_declared": bool(declared_hdr),
        "uncastable": len(uncast), "interaction": d_int, "card_advantage": d_ca,
        # Real ward/hexproof/indestructible-class effects. Reported, NOT fed into
        # `tier_band` — the floor's formula is anchored by check_tier.py and a new term
        # would silently re-grade the whole roster. Surfaced so a human sees a zero.
        "protection": _tally["protection"],
        # The counts again, rendered WITH their uncertainty (see count_conf). The bare
        # ints stay for the tier floor and the F10 guard, which need numbers to compare;
        # these are what a human should read.
        "interaction_conf": count_conf(_tally, "interaction"),
        "card_advantage_conf": count_conf(_tally, "card_advantage"),
        "avg_mv": round(sum(mvs) / len(mvs), 2) if mvs else 0.0, "early_drops": early,
        # How many of those early drops only make MANA. Reported beside the count so a
        # human reading it for a CURVE argument sees what it is made of, and subtracted
        # from the aggro `_clock_score` where "cheap threat" is what the term means.
        "early_mana": early_mana,
        "creatures": creatures, "reach": reach,
        # The deck's game PLAN drives which axes its tier floor weights (#4): an aggro
        # deck is graded on its clock, not an interaction suite it doesn't want.
        "plan": deck_plan(dmeta, avg_mv=(round(sum(mvs) / len(mvs), 2) if mvs else 0.0),
                          interaction=d_int, early=early),
        "central_themes": len(_central_themes(theme_w)),
        "central": sorted(_central_themes(theme_w)),
        # Full per-theme copy counts — lets the F10 guard tell a theme that truly LEFT
        # the deck (0 copies) from one merely demoted below the centrality cutoff (F#2).
        "theme_copies": dict(theme_w),
    }


def _quality_vector_at(d, ref):
    """The quality vector for a deck's list AS OF a git ref — evaluates that past
    version against CURRENT card knowledge (so 'was my old list better?' is a
    like-for-like comparison). Returns (vec, None) or (None, error)."""
    import subprocess
    import tempfile
    rel = os.path.relpath(d["path"], REPO_ROOT)
    r = subprocess.run(["git", "show", f"{ref}:{rel}"], capture_output=True, text=True,
                       cwd=REPO_ROOT)
    if r.returncode != 0:
        return None, (r.stderr.strip() or f"deck not found at {ref}")
    fd, tmp = tempfile.mkstemp(suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(r.stdout)
        return deck_quality_vector({"id": d["id"], "path": tmp, "name": d.get("name")}), None
    finally:
        os.remove(tmp)


def cmd_quality(args):
    """Deck-quality guard (F10): print the quality vector, diff it against a saved
    snapshot (`--vs FILE`) to flag regressions from a cut/swap, and/or check that a
    proposed add isn't a merely-tangential fit (`--add NAME`). `--at REF` compares
    this deck's list at a past git ref against now. Soft by design — it WARNS (some
    regressions are intentional trades); exits 0 unless --strict."""
    import json
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    vec = deck_quality_vector(d)
    if getattr(args, "at", None):
        # `--at` returns below without ever reading --json/--vs/--add/--strict, so a
        # caller asking for JSON got human prose and a JSONDecodeError (broad-scan
        # Batch G). Composing them is feature work; dropping them SILENTLY is the bug.
        ignored = [f for f, v in (("--json", getattr(args, "json", False)),
                                  ("--vs", getattr(args, "vs", None)),
                                  ("--add", getattr(args, "add", None)),
                                  ("--strict", getattr(args, "strict", False))) if v]
        if ignored:
            eprint(f"NOTE:  --at is a past-vs-now comparison and does not combine with "
                   f"{', '.join(ignored)} — {'that flag is' if len(ignored) == 1 else 'those flags are'} "
                   f"ignored for this run.")
        old, err = _quality_vector_at(d, args.at)
        if old is None:
            eprint(f"could not read deck {d['id']} at {args.at!r}: {err} "
                   f"(renamed? see `deck.py history {d['id']}`)")
            return 1
        print(f"Quality — deck {d['id']} @ {args.at}  →  current:")
        for k in ("buildable", "uncastable", "interaction", "card_advantage",
                  "avg_mv", "early_drops", "central_themes"):
            o, n = old[k], vec[k]
            delta = "" if o == n else f"   ({o} → {n})"
            print(f"  {k:15}: {n}{delta}")
        lost = sorted(set(old["central"]) - set(vec["central"]))
        gained = sorted(set(vec["central"]) - set(old["central"]))
        if lost:
            print(f"  central themes lost since {args.at}: {', '.join(lost)}")
        if gained:
            print(f"  central themes gained: {', '.join(gained)}")
        return 0
    if getattr(args, "json", False):
        print(json.dumps(vec))
        return 0
    print(f"Quality — deck {d['id']}: {d['name'] or d['path']}")
    for k in ("buildable", "uncastable", "interaction", "card_advantage",
              "avg_mv", "early_drops", "central_themes"):
        print(f"  {k:15}: {_early_drops_note(vec) if k == 'early_drops' else vec[k]}")

    regressions = []
    if getattr(args, "vs", None):
        try:
            before = json.load(open(args.vs))
        except Exception as e:
            eprint(f"could not read --vs snapshot {args.vs!r}: {e}")
            return 1
        if before.get("buildable") and not vec["buildable"]:
            regressions.append("became UNbuildable")
        if vec["uncastable"] > before.get("uncastable", 0):
            regressions.append(f"castability worse ({before.get('uncastable',0)}→{vec['uncastable']})")
        if vec["interaction"] < before.get("interaction", 0):
            regressions.append(f"interaction dropped ({before['interaction']}→{vec['interaction']})")
        if vec["card_advantage"] < before.get("card_advantage", 0):
            regressions.append(f"card advantage dropped ({before['card_advantage']}→{vec['card_advantage']})")
        # A central theme dropping out of the set is only a REAL regression if the
        # theme's cards actually left the deck (0 copies now). A theme that merely fell
        # below the 25% centrality cutoff because a strongly on-theme add concentrated
        # the top theme is a benign reclassification, not a loss (F#2 — this used to
        # false-alarm, e.g. adding Zimone flagged Druid/mill/selection as "lost" while
        # their cards were still in the deck).
        tc = vec.get("theme_copies", {})
        demoted = set(before.get("central", [])) - set(vec["central"])
        truly_lost = {t for t in demoted if tc.get(t, 0) == 0}
        if truly_lost:
            regressions.append(
                f"lost central theme(s) — 0 copies remain: {', '.join(sorted(truly_lost))}")
        # Guard the direct index: a hand-written / schema-drifted --vs snapshot may lack
        # avg_mv. With .get(...,0) the comparison fires for any real curve, then
        # before['avg_mv'] would KeyError (audit A9). Skip the check when it's absent
        # rather than crash or print a misleading "0→X".
        b_mv = before.get("avg_mv")
        if b_mv is not None and vec["avg_mv"] - b_mv > 0.3:
            regressions.append(f"curve heavier (avg MV {b_mv}→{vec['avg_mv']})")

    weak_add = None
    if getattr(args, "add", None):
        dmeta, cards = parse_deck_file(d["path"])
        carddata, cardmeta = load_card_data(), load_card_meta()
        theme_w = {}
        for q, n, s, c in cards:
            if n.lower() in BASICS:
                continue
            m = cardmeta.get(n.lower())
            if m:
                for t in m["synergies"]:
                    theme_w[t] = theme_w.get(t, 0) + q
        cd = carddata.get(args.add.lower())
        ctags = set(cardmeta.get(args.add.lower(), {}).get("synergies", []))
        shared = sorted(ctags & _central_themes(theme_w))
        d_int, d_ca = deck_role_counts(cards, carddata)
        # STRICT (>=2 protected cards) — see fit_strength's docstring: the loose
        # union made a generic theme a signature and minted KEY nearly everywhere.
        sig = _strong_signature_themes(dmeta, cards, cardmeta)
        strength = fit_strength(shared, theme_w, (cd or {}).get("text") or "", d_int, d_ca, sig)
        if strength == "tangential":
            weak_add = f"add {args.add!r} is only a TANGENTIAL fit (generic themes only)"

    if regressions or weak_add:
        print("\n⚠ QUALITY GUARD:")
        for r in regressions:
            print(f"  - {r}")
        if weak_add:
            print(f"  - {weak_add}")
        print("  (soft — intentional trades are fine; re-grade the cut from full "
              "text via `deck.py cuts`/`card.py` if unsure)")
        if getattr(args, "strict", False):
            return 1
    elif getattr(args, "vs", None) or getattr(args, "add", None):
        print("\n✓ QUALITY GUARD: net improvement / no regressions.")
    return 0


# Competitive-tier robustness (F12). The tier LETTER is a human competitive
# judgment and is NEVER auto-assigned — but it should be DEFENSIBLE against the
# deck's measurable quality vector. `tier_band` maps that vector to the tier FLOOR
# the metrics alone support; it is deliberately blind to raw card power / bombs /
# meta positioning (an idf + role model can't see those), so it systematically
# UNDER-rates. A human letter one band above the floor is fine — that band credits
# the intangibles. A letter TWO-or-more bands above the floor is indefensible or
# stale, and that's the only thing the guard flags.
TIER_RANK = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}


# Evasion tags that let a creature keep connecting — the "reach" the aggro floor credits.
_EVASION_TAGS = {"evasion", "flying", "menace", "trample", "fear", "intimidate",
                 "shadow", "skulk", "horsemanship", "unblockable", "double strike"}
_AGGRO_WORDS = ("aggro", "aggressive", "hyper-aggressive", "burn")


def deck_plan(meta, avg_mv=None, interaction=None, early=None):
    """The deck's game PLAN — 'aggro' | 'control' | 'combo' | 'midrange' — which decides
    the axes its tier floor weights (#4). Source order: an explicit `#: plan:` header,
    then keywords in `#: archetype:`, then a conservative metric inference. Defaults to
    'midrange' (the current interaction+card-advantage floor), so anything not clearly
    aggro/control/combo is graded exactly as before."""
    explicit = (meta.get("plan") or "").strip().lower()
    if explicit in ("aggro", "control", "combo", "midrange"):
        return explicit
    arc = (meta.get("archetype") or "").lower()
    if any(w in arc for w in _AGGRO_WORDS):
        return "aggro"
    if "control" in arc:
        return "control"
    if "combo" in arc:
        return "combo"
    if any(w in arc for w in ("midrange", "ramp", "value", "goodstuff", "tempo")):
        return "midrange"
    # Inference (only when nothing is declared): a clearly fast, cheap, low-interaction
    # deck reads aggro. Deliberately strict so it never surprises a non-aggro deck.
    if (avg_mv is not None and avg_mv <= 2.4 and (interaction or 0) < 4
            and (early or 0) >= 8):
        return "aggro"
    return "midrange"


# A mana ability, read off the text the same way `granted_keywords` reads a grant:
# "{T}: Add {G}", "Add one mana of any color". Reminder text is stripped by the caller.
_MANA_SOURCE_RE = re.compile(r"\badds?\s+(?:\{|one mana|two mana|three mana|X mana|"
                             r"that much|mana of any)", re.I)


def _clock_score(vec):
    """Aggressive 'clock' proxy (0–7): a low curve + cheap threats + reach to close.
    Substitutes for interaction in `tier_band` ONLY for an aggro plan — a fast deck's
    resilience is its speed, not its removal count. Bounded so it can't wildly inflate."""
    # NOT `vec.get("avg_mv") or 99.0` (BS6-12): a deck whose nonland cards all lack cost
    # data has avg_mv 0.0, and `0.0 or 99.0` is 99.0 — the falsy-zero trap `card_power`
    # and `owned_qty` each carry a paragraph about, sitting in the one function that can
    # RAISE a tier band. The effect was conservative (no clock credit) so nothing was
    # mis-graded, but the shape must not be copied. `None` is the real "no data" case and
    # is what deserves the sentinel; a measured 0.0 curve is a fact about the deck.
    mv = vec.get("avg_mv")
    mv = 99.0 if mv is None else mv
    # THREATS, not bodies: a turn-two mana dork does not shorten the clock, and this
    # term is the substitute for interaction that lets an aggro deck float its floor.
    # Measured before shipping (K-14): 0 of 114 decks change band, and no deck on an
    # aggro plan has a mana-dense early curve today — so this is a correction that
    # buys nothing now and stops a future ramp deck buying a band it has not earned.
    early = max(0, vec.get("early_drops", 0) - vec.get("early_mana", 0))
    reach = vec.get("reach", 0)
    c = 3 if mv <= 2.2 else 2 if mv <= 2.6 else 1 if mv <= 3.0 else 0
    c += 2 if early >= 12 else 1 if early >= 8 else 0
    c += 2 if reach >= 8 else 1 if reach >= 4 else 0
    return c


# A rationale that grades BELOW the measurable floor and says why is a defensible human
# call — the rubric credits intangibles in the other direction too, and deck 51 set the
# precedent. Flagging it anyway gave decks 51, 52 and 52a a permanent "possibly
# UNDER-graded" nudge for being honest, and a standing warning is one nobody reads.
# Narrow on purpose: the prose must name the floor or the rubric's own language, not just
# be long.
# The weakness clause is the rubric's OWN A-band wording ("at most one clear weakness"),
# so decks cite it in shorthand — deck 35 writes `More than the "≤1 weakness" an A allows`
# and deck 17 `not a coherent engine with one weakness`. Matching only the long form left
# both nagged for making exactly the argument this suppression exists to honour, which is
# the failure the paragraph above describes, unfixed on two decks. Measured before
# widening (K-14): of the 62 decks sitting below their floor, 12 were flagged and the
# widen suppresses exactly these 2, both true positives — 10 still flagged.
_BELOW_FLOOR_ARGUMENT = re.compile(
    r"(?:below the (?:measurable |metrics )?floor|band BELOW|deliberately (?:one )?band|"
    r"conservative (?:read|grade)|fails? (?:the )?(?:fourth|two|three)|"
    r"(?:≤\s*1|at most one|one) (?:clear )?weakness|PROVISIONAL|"
    # The HELD-BY family, measured 2026-08-31. The cue list above spells the rubric's
    # own vocabulary; what the roster actually writes is "held at B by <reason>",
    # "Residual cap: <reason>", "WHAT CAPS IT IS <reason>" and a weakness COUNT above
    # the one an A allows. Seven of the ten decks the guard was nagging make exactly
    # the argument the suppression exists to honour — a 70% false-positive rate on a
    # standing warning, which is the saturation shape G-07 measured on `audit`'s
    # review flag and the reason nobody reads it.
    r"held (?:at|below)\b|\bletter (?:stays|is held)\b|"
    r"\bresidual cap\b|\bwhat caps it\b|\bcaps it\b|\bcapped\b|"
    # The weakness COUNT must be related to a BAND to count, not merely stated: the
    # roster writes "Three weaknesses, where A allows one" and "Two clear weaknesses is
    # past what B tolerates", while a bare "two weaknesses, both covered" is a topic
    # match the pattern's own "narrow on purpose" note forbids.
    r"(?:two|three|four|\d+) (?:clear )?weakness(?:es)?"
    r"[^.]{0,40}?(?:where|than|past what|allows?|tolerat))", re.I)
# ...and the OVERRIDE, because three of those ten decks ASK for the flag in the same
# breath as they argue the cap: 7 opens "RE-GRADE CANDIDATE, and the argument for B has
# now expired", 19 says "the letter stays B pending the human call the flag asks for",
# 23 "HELD at B pending a human re-grade". A rationale that defers the call wants the
# nudge; one that makes the call does not. This is checked AFTER the argument cues, so
# a deck can hold at B by a stated reason and still be flagged while it says the reason
# is provisional.
_WANTS_UNDER_GRADE_FLAG = re.compile(
    r"(?:re-?grade candidate|pending (?:a|the) (?:human )?(?:re-?grade|call|judgment))",
    re.I)


def _argues_below_floor(meta):
    """True when `#: tier:` explicitly argues for grading under the metrics floor —
    and does not, in the same block, defer the call to a human it wants prompted."""
    prose = (meta or {}).get("tier", "") or ""
    if _WANTS_UNDER_GRADE_FLAG.search(prose):
        return False
    return bool(_BELOW_FLOOR_ARGUMENT.search(prose))


def _keepable_at(nlands, deck_size, hand=7):
    """P(opening hand holds 2–5 lands) at a hypothetical land count — used to check
    whether the land advisory's suggested direction actually improves anything."""
    if nlands < 0 or nlands > deck_size:
        return None
    from math import comb
    tot = comb(deck_size, hand)
    return sum(comb(nlands, k) * comb(deck_size - nlands, hand - k)
               for k in range(2, 6) if k <= nlands and hand - k <= deck_size - nlands) / tot


# Cards whose value is a COUNT in the deck rather than anything in their own text. The
# `_int_scaling` sibling covers removal; this covers the rest — "equal to the number of
# Swamps you control", "for each creature card in your graveyard", "X is the number of".
# Every scoring model here grades a card in isolation, so these read at their floor.
_DECK_STATE_AXIS_RE = re.compile(
    r"(?:equal to the number of|for each|where X is the number of)\s+"
    r"([\w' -]{3,30}?)\s+(you control|in your graveyard|on the battlefield)", re.I)


def _deck_state_axis(text):
    """The deck property a card's value scales with, or None. Report-only.

    The ZONE is part of the axis: "cards" alone is uninformative, "cards in your
    graveyard" tells you which number to go count."""
    m = _DECK_STATE_AXIS_RE.search(text or "")
    if not m:
        return None
    return f"{m.group(1).strip()} {m.group(2).strip()}"[:40] or None


def tier_band(vec):
    """The tier FLOOR (S/A/B/C/D) a deck's measurable quality vector supports.
    Metrics-only and blind to bombs/meta, so it under-rates by design — used to flag
    a claimed tier sitting ≥2 bands above it, never to assign a tier.

    It rates the LIST's competitive power independent of whether the cards are owned
    — tier is a power judgment, and build-state (ownership) is tracked separately by
    `check`/`audit`, so an aspirational unbuilt list is graded on its merits. A
    castability stray IS a list flaw (a dead card), so it caps the floor."""
    inter, ca = vec["interaction"], vec["card_advantage"]
    # An AGGRO deck closes on a fast clock, not an interaction suite — so for an aggro
    # plan a strong clock (low curve + cheap threats + reach) substitutes for the
    # interaction the resilience floor otherwise demands, and a genuinely fast deck
    # isn't floored at C just for running light removal (#4). Every other plan keeps
    # the exact interaction+card-advantage floor (clock = 0), so nothing else regrades.
    clock = _clock_score(vec) if vec.get("plan") == "aggro" else 0
    ir = inter + clock                    # effective pressure/interaction axis
    resil = inter + ca + clock            # grind / resilience / closing speed
    # ONE table (`TIER_FLOOR_REQ`) for the classifier and the gap diagnostic. The
    # thresholds used to be duplicated here as literals — and were (5, 7) / (3, 4),
    # which the roster had long outgrown: with a median interaction of 8 the floor read
    # A for 104 of 117 decks and C/D for none, so the ≥2-band guard could only fire on
    # an S claim, the under-grade nudge fired on every claimed B, and `tier --to A`
    # answered "already meets" for 90% of the roster (broad-scan BS8-06). Re-derived
    # from the roster distribution 2026-09-02: A at (7, 11) ≈ the roster median on both
    # axes, B at (4, 7) ≈ its 10th percentile, C unchanged. `check_all` now warns when
    # the floor collapses into one band again (`tier_floor_spread`).
    if ir >= TIER_FLOOR_REQ["A"][0] and resil >= TIER_FLOOR_REQ["A"][1]:
        band = "A"                        # measurable ceiling; S is a human call on top
    elif ir >= TIER_FLOOR_REQ["B"][0] and resil >= TIER_FLOOR_REQ["B"][1]:
        band = "B"
    elif resil >= TIER_FLOOR_REQ["C"][1]:
        band = "C"
    else:
        band = "D"
    # A castability stray CAPS the floor at C — it does not SET it (broad-scan F-16).
    # The old form returned "C" outright, so a deck whose measurable floor was D got
    # RAISED by having a dead card in it. "Caps" is what the docstring and CLAUDE.md
    # both already said; only the code disagreed. Note the count reaching here excludes
    # cards the deck's `#: uncastable-ok:` header declares intentional (F-02).
    if vec["uncastable"] > 0 and TIER_RANK[band] > TIER_RANK["C"]:
        band = "C"
    return band


# The measurable FLOOR requirement per band: (min interaction, min interaction+ca).
# THE single source for the classifier (`tier_band` reads it) and the gap diagnostic
# (`tier_gap`), so they cannot disagree about what a band needs. Re-derived from the
# roster distribution on 2026-09-02 (BS8-06); the previous (5, 7) / (3, 4) had every
# deck on the roster at A or B. `check_tier.py` anchors the shape, `tier_floor_spread`
# watches the roster for the collapse that motivated the change.
TIER_FLOOR_REQ = {"S": (7, 11), "A": (7, 11), "B": (4, 7), "C": (0, 2), "D": (0, 0)}

# The share of the roster one floor band may hold before `check_all` warns that the
# floor has stopped discriminating. 104 of 117 (89%) is where BS8-06 found it.
TIER_SPREAD_MAX_SHARE = 0.85


def tier_floor_spread(decks=None):
    """{band: count} of the measurable floor across the roster, plus the check_all
    message when one band holds more than `TIER_SPREAD_MAX_SHARE` of it, else None.

    `check_tier` pins the floor's SHAPE on synthetic vectors, which cannot see the
    roster: the thresholds were right when written and silently fell below every deck
    as the role patterns widened, each widening reporting "0 tier floors moved" — a
    measurement the saturation guaranteed. This is the distribution check that would
    have shown it. Soft and roster-wide, like the mismatch sweep beside it: a collapsed
    spread is a reason to re-derive the thresholds, not a deck defect."""
    from collections import Counter
    bands = Counter()
    for d in (decks if decks is not None else roster_decks()):
        try:
            bands[tier_band(deck_quality_vector(d))] += 1
        except Exception:
            continue
    n = sum(bands.values())
    msg = None
    if n >= 20:
        band, top = max(bands.items(), key=lambda kv: (kv[1], kv[0]))
        if top / n > TIER_SPREAD_MAX_SHARE:
            msg = (f"tier floor has collapsed: {top} of {n} decks ({top / n:.0%}) sit at "
                   f"the {band} floor — the thresholds in `deck.TIER_FLOOR_REQ` no longer "
                   f"discriminate; re-derive them from the roster distribution (BS8-06)")
    return dict(bands), msg


def tier_gap(vec, target):
    """What a deck's measurable vector needs to reach `target` tier's FLOOR (F14):
    the exact axis shortfall — +N interaction, +N card advantage, and any uncastable
    strays to clear (they cap the floor at C). Blind to bombs/meta like tier_band, so
    it reports the measurable floor gap, NOT the intangible A-vs-S judgment. Returns
    None for a bad target; a dict {target, add_interaction, add_card_advantage,
    fix_uncastable, met, summary[]} otherwise."""
    target = (target or "").upper()
    if target not in TIER_FLOOR_REQ:
        return None
    need_i, need_r = TIER_FLOOR_REQ[target]
    inter, ca = vec["interaction"], vec["card_advantage"]
    # For an aggro plan the clock already counts toward the floor (see tier_band), so
    # the interaction the deck still needs is measured against interaction + clock (#4).
    clock = _clock_score(vec) if vec.get("plan") == "aggro" else 0
    inter_eff = inter + clock
    parts = []
    # Any target above C requires 0 castability strays (a stray caps the floor at C).
    fix_unc = vec["uncastable"] if (TIER_RANK[target] > TIER_RANK["C"] and vec["uncastable"]) else 0
    if fix_unc:
        parts.append(f"clear {fix_unc} uncastable stray(s) — they cap the floor at C")
    add_i = max(0, need_i - inter_eff)
    # Interaction adds also raise the resilience sum; only the remainder needs card advantage.
    add_ca = max(0, need_r - (inter_eff + ca + add_i))
    if add_i:
        label = "interaction or clock" if clock or vec.get("plan") == "aggro" else "interaction"
        parts.append(f"+{add_i} {label} ({inter_eff}→{inter_eff + add_i})")
    if add_ca:
        parts.append(f"+{add_ca} card advantage ({ca}→{ca + add_ca})")
    if vec.get("plan") == "aggro" and add_i:
        parts.append("(aggro: raise the clock — lower the curve / add cheap threats / add "
                     "reach — or add interaction)")
    return {"target": target, "add_interaction": add_i, "add_card_advantage": add_ca,
            "fix_uncastable": fix_unc,
            "met": not [p for p in parts if not p.startswith("(aggro:")], "summary": parts}


def _filler_castable(cost, ident, declared):
    """Castability for a FILLER candidate (`tier --to`, `redundancy`): the PRINTED COST
    through `_candidate_castability`, exactly as `suggest` / `screen` / `suggest-homes`
    read it (G-58). The three filler functions were the last identity-subset holdouts —
    `ident <= declared` — so Bullseye, Death Dealer (`{2}{B/R}`, the card G-58 names)
    was excluded from mono-black 52a and 10–17 castable owned interaction cards per
    deck were hidden from the wildcard-spend planner (BS8-05). Identity stays as the
    FALLBACK for a card with no cost on file, which is the only case where it is the
    best evidence available."""
    if not cost:
        return ident <= declared
    ok, _note = _candidate_castability(cost, ident, declared)
    return ok


def owned_role_fillers(d, roles, *, limit=10):
    """Owned, on-color cards NOT already in deck d that fill any role in `roles`
    (e.g. `_INTERACTION_ROLES`, or {"Card advantage"}) — the 0-wildcard fillers that
    can close a tier gap, cheapest first. On-color = the card's identity ⊆ the deck's
    declared/derived colors, so it won't surface an uncastable pick.

    ALSO format-legal, on the same rule as `craft_role_fillers`. This half used to skip
    the check its sibling applied, so `tier <id> --to A` printed the craft list as
    "format-legal" and the owned list unfiltered right above it — and it offered Deadly
    Dispute, an FCA card with no Standard legality, as a filler for Standard deck 42a.
    Being owned is not a licence to play it: the recommendation costs no wildcard but it
    still costs a DECK SLOT, and an illegal maindeck card is a worse outcome than a
    wasted craft. Same failure CLAUDE.md records for `suggest --lands`, one command over.
    A pool-absent / unverified legality is treated as legal, matching `legal`/`suggest`.
    """
    meta, cards = parse_deck_file(d["path"])
    mana, carddata = load_mana(), load_card_data()
    _, _, qty = load_collection()
    legalities = load_legalities()
    fmt = pool_format_key(meta.get("format"))     # BS8-04: the pool's key
    # `_ms_key` both sides (BS2-19): `carddata` keys a DFC under BOTH spellings, so a
    # raw-name `in_deck` suppressed only the spelling the deck file used — the OTHER
    # key sailed through, `owned()` resolved it via the front-face fallback, and the
    # deck was offered its own maindecked card as a 0-wildcard filler (25 such rows at
    # full limit; reaches `tier --to` and `redundancy`). The display-name dedupe below
    # can't help — the two entries were separate dicts.
    in_deck = {_ms_key(n) for q, n, s, c in cards}
    declared = set(_declared_colors(meta) or _deck_castable_colors(meta, cards, mana))
    out = []
    for nl, cd in carddata.items():
        if _ms_key(nl) in in_deck or nl in BASICS:
            continue
        if "Land" in _primary_type(cd.get("type") or ""):
            continue
        name = cd.get("name") or nl
        have, found = owned(qty, name)
        if not found or have < 1:
            continue
        ident = card_colors(cd.get("colors"))
        entry = mana.get(nl)
        if not _filler_castable(entry[0] if entry else "", ident, declared):
            continue
        legs = legalities.get(nl) or legalities.get(nl.split(" // ")[0]) or set()
        if fmt and legs and fmt not in legs:
            continue
        hit = set(classify_roles(cd.get("text") or "")) & set(roles)
        if not hit:
            continue
        mv = entry[1] if entry and entry[1] is not None else 99
        out.append((mv, name, "".join(sorted(ident)) or "C", sorted(hit),
                    (cd.get("text") or "").split("\n")[0][:64]))
    # `carddata` keys a DFC under BOTH its full "Front // Back" name and its front face,
    # and both rows carry the same display name — so a double-faced filler was printed
    # twice, wasting a line of a six-line list. Dedupe on the display name, keeping the
    # cheapest entry (the sort below is stable on mv, so first-seen wins after sorting).
    out.sort(key=lambda r: (r[0], r[1]))
    seen, deduped = set(), []
    for row in out:
        if row[1] in seen:
            continue
        seen.add(row[1])
        deduped.append(row)
    return deduped[:limit]


def craft_role_fillers(d, roles, *, limit=8):
    """Unowned pool cards (CRAFT targets) not already in deck d that fill any role in
    `roles`, on-color and legal in the deck's format — the wildcard-spend options to
    close a tier gap when the owned pool is thin (the natural question for an
    aspirational/unbuilt deck). Sorted cheaper-wildcard first, then mana value."""
    if not os.path.exists(POOL_CSV):
        return []
    meta, cards = parse_deck_file(d["path"])
    mana = load_mana()
    _, _, qty = load_collection()
    # `_ms_key` (BS2-19), same reason as `owned_role_fillers`: the pool keys the full
    # `Front // Back` while the deck line may store the front, so an UNOWNED DFC
    # already maindecked as a WIP craft target was offered as a craft for its own deck
    # (the owned_qty skip below only masks the owned case).
    in_deck = {_ms_key(n) for q, n, s, c in cards}
    declared = set(_declared_colors(meta) or _deck_castable_colors(meta, cards, mana))
    fmt = pool_format_key(meta.get("format"))     # BS8-04: the pool's key
    RANK = {"Common": 0, "Uncommon": 1, "Rare": 2, "Mythic": 3}
    pool_rot, _has_released = _pool_rotation_index()
    out, seen = [], set()
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            name = (r.get("Card Name") or "").strip()
            nl = name.lower()
            if not nl or nl in seen or _ms_key(nl) in in_deck or nl in BASICS:
                continue
            if "Land" in _primary_type(r.get("Type") or ""):
                continue
            # want CRAFT targets — skip owned. Pool names are the full "Front // Back";
            # owned_qty falls back to the DFC front face so an owned DFC isn't listed as
            # a craft target (audit F6/F19), unlike the local owned() which needs an
            # exact key. Mirrors suggest_scored.
            if owned_qty(qty, name) > 0:
                continue
            ident = card_colors(r.get("Color(s)"))
            entry = mana.get(nl)
            if not _filler_castable(entry[0] if entry else "", ident, declared):
                continue
            legs = {x.strip().lower() for x in (r.get("Legalities") or "").split(";") if x.strip()}
            if fmt and legs and fmt not in legs:
                continue
            if not (set(classify_roles(r.get("Card Text") or "")) & set(roles)):
                continue
            seen.add(nl)
            entry = mana.get(nl)
            mv = entry[1] if entry and entry[1] is not None else 99
            rar = (r.get("Rarity") or "?").strip()
            # G-30: `tier --to` is described in CLAUDE.md as doubling as a WILDCARD-SPEND
            # PLANNER, and this is its craft half — the one list here that costs real
            # wildcards — so a rotating pick must say so (BS4-11).
            rot = craft_rot_note(name, pool_rot)
            out.append((RANK.get(rar, 9), mv, name, "".join(sorted(ident)) or "C", rar,
                        (r.get("Card Text") or "").split("\n")[0][:56], rot))
    out.sort(key=lambda x: (x[0], x[1], x[2]))
    return out[:limit]


# --- redundancy / functional-copies planner ("virtual copies first") ---------- #
# A competitive deck needs to draw its plan reliably. The blunt way is 4-ofs; the
# subtler way is FUNCTIONAL REDUNDANCY — running distinct, similar-but-different cards
# that do the same job ("virtual copies"), which keeps a singleton/highlander feel while
# still drawing the EFFECT every game. This planner encodes the user's preference: when
# firming up a thin effect, try distinct virtual copies FIRST, and fall back to true
# duplicates only when there aren't enough of acceptable quality.
_REDUNDANCY_TARGET = 4          # a plan-critical effect wants ~this many (virtual) copies
_REDUNDANCY_THIN = 2            # depth ≤ this = a consistency risk worth firming up
_REDUNDANCY_QUALITY_TOL = 1.5   # a virtual copy >this far below your best is "much weaker"


def plan_redundancy_fill(depth, best_power, functional_options, *,
                         target=_REDUNDANCY_TARGET, tol=_REDUNDANCY_QUALITY_TOL):
    """Decide how to firm up an effect the deck runs `depth` distinct copies of.

    `functional_options` = [(power, name), …] distinct cards (NOT in the deck) that do the
    same job, best-power first. `best_power` = the deck's strongest existing copy of the
    effect. Prefer functional (virtual) copies as long as they're within `tol` of your
    best — that keeps the deck semi-singleton; only when functional copies run out (or the
    remaining ones are significantly weaker) fall back to running true DUPLICATES of the
    best existing card. Pure/deterministic — unit-tested.

    Returns {need, functional:[(power,name)…], duplicates:int, reason}."""
    need = max(0, target - depth)
    if need == 0:
        return {"need": 0, "functional": [], "duplicates": 0, "reason": "already deep enough"}
    picks = []
    for pw, nm in functional_options:
        if len(picks) >= need:
            break
        if pw >= best_power - tol:            # acceptable quality → prefer the virtual copy
            picks.append((pw, nm))
    dup = max(0, need - len(picks))
    if dup == 0:
        reason = "functional copies cover it — stays singleton"
    elif not picks and not functional_options:
        reason = "no functional copies exist — duplicates are the only option"
    elif dup and picks:
        reason = "functional copies as far as they go, then duplicates for the rest"
    else:
        reason = "remaining functional copies are much weaker — duplicate instead"
    return {"need": need, "functional": picks, "duplicates": dup, "reason": reason}


def _card_power(nl, carddata, rar):
    """Heuristic 0–10 power of a card (by lowercase name) via the shared wishlist seed.

    `rar` is a load_rarities() map — Arena wildcard LETTERS, which the seed normalizes
    (wishlist._norm_rarity); passing a letter used to silently score as an uncommon (F-01)."""
    cd = carddata.get(nl) or {}
    return _power_seed({"Rarity": rar.get(nl, ""), "Card Text": cd.get("text", "") or "",
                        "Type": cd.get("type", "") or ""})


def functional_theme_options(d, theme, *, limit=8):
    """Distinct owned+craft cards (NOT in deck d) that carry synergy `theme`, on-color and
    format-legal — functional (virtual) copies of a THEME effect (e.g. the deck's ping
    payoff via the shared 'burn' tag). Returns [(power, name, owned_bool, mv, rarity)]
    best-power first. The theme analog of owned/craft_role_fillers."""
    meta, cards = parse_deck_file(d["path"])
    cardmeta = load_card_meta()
    carddata = load_card_data()
    mana = load_mana()
    rar = load_rarities()
    leg = load_legalities()
    _, _, qty = load_collection()
    in_deck = {_ms_key(n) for q, n, s, c in cards}   # G-63: front-face join
    declared = set(_declared_colors(meta) or _deck_castable_colors(meta, cards, mana))
    fmt = pool_format_key(meta.get("format"))     # BS8-04: the pool's key
    out, seen = [], set()
    for nl, m in cardmeta.items():
        if nl in seen or nl in in_deck or nl in BASICS:
            continue
        if theme not in m.get("synergies", []):
            continue
        cd = carddata.get(nl)
        if not cd or "Land" in _primary_type(cd.get("type") or ""):
            continue
        name = cd.get("name") or nl
        entry = mana.get(nl)
        if not _filler_castable(entry[0] if entry else "", card_colors(cd.get("colors")),
                                declared):
            continue
        legs = leg.get(nl)
        if fmt and legs is not None and fmt not in legs:
            continue
        seen.add(nl)
        mv = entry[1] if entry and entry[1] is not None else 99
        out.append((_card_power(nl, carddata, rar), name, owned_qty(qty, name) > 0, mv,
                    (rar.get(nl) or "?")))
    out.sort(key=lambda r: (-r[0], r[3], r[1]))
    return out[:limit]


def effect_redundancy(d):
    """Bucket a deck's nonland cards by the EFFECTS they provide — functional roles
    (Removal/Counter/Card advantage/…) and specific (non-generic) synergy themes — and
    return {effect: {"kind": "role"|"theme", "cards": [names], "depth": n}}. Depth is the
    count of DISTINCT cards providing the effect = its virtual-copy count."""
    meta, cards = parse_deck_file(d["path"])
    cardmeta = load_card_meta()
    carddata = load_card_data()
    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        for t in cardmeta.get(n.lower(), {}).get("synergies", []):
            theme_w[t] = theme_w.get(t, 0) + q
    central = _central_themes(theme_w)
    buckets = {}
    seen = set()
    for q, n, s, c in cards:
        nl = n.lower()
        if nl in BASICS or nl in seen:
            continue
        cd = carddata.get(nl)
        if cd and "Land" in _primary_type(cd.get("type") or ""):
            continue
        seen.add(nl)
        effects = set()
        for r in classify_roles(cd["text"] if cd else ""):
            if r in IMPACT_ROLES:
                effects.add(("role", r))
        for t in cardmeta.get(nl, {}).get("synergies", []):
            # `_GENERIC_TRIBES` too, not just GENERIC_THEMES: every other specific-theme
            # test here excludes a background tribe (Human/Hero/Villain), so without it a
            # central `Human` tag became a redundancy bucket and `cmd_redundancy` could
            # propose "firming up Human" (BS4-35).
            if t in central and t not in GENERIC_THEMES and t not in _GENERIC_TRIBES:
                effects.add(("theme", t))
        for kind, name in effects:
            b = buckets.setdefault(name, {"kind": kind, "cards": []})
            b["cards"].append(n)
    for b in buckets.values():
        b["depth"] = len(b["cards"])
    return buckets


def near_duplicates(cards, carddata, mana=None):
    """[(role_tuple, [card names])] — GROUPS of nonland cards that do the same job in this
    deck: identical non-empty functional-role sets, within a 1-mana band of each other.

    `redundancy` buckets by EFFECT and answers "how many virtual copies of this effect do
    I have"; nothing answered "which of my specific cards are interchangeable". That gap
    produced a real bad recommendation: cutting Chelonian Tackle was proposed without
    noticing Epic Fight already provided the fight mode, so the deck would have kept the
    weaker of two near-identical cards. Reported as GROUPS, not pairs — a 6-card removal
    suite is 15 pairs and one useful fact. Redundancy is often DESIRABLE; this reports,
    it does not judge."""
    buckets = {}
    for q, n, _s, _c in cards:
        if n.lower() in BASICS:
            continue
        cd = carddata.get(n.lower())
        if not cd or "Land" in _primary_type(cd.get("type") or ""):
            continue
        roles = tuple(sorted(classify_roles(cd.get("text") or "")))
        if not roles:
            continue                     # no signal — saying nothing beats guessing
        mv = None
        if mana:
            e = mana.get(n.lower())
            mv = e[1] if e and e[1] is not None else None
        buckets.setdefault(roles, []).append((cd.get("name") or n, mv))
    out = []
    for roles, members in buckets.items():
        if len(members) < 2:
            continue
        # Split a bucket into cost BANDS so a 1-drop and a 6-drop with the same role
        # aren't called interchangeable — cost is most of what makes two answers differ.
        known = sorted((m for m in members if m[1] is not None), key=lambda x: x[1])
        unknown = [m for m in members if m[1] is None]
        bands, cur = [], []
        for name, mv in known:
            if cur and mv - cur[0][1] > 1:
                bands.append(cur)
                cur = []
            cur.append((name, mv))
        if cur:
            bands.append(cur)
        if unknown:
            bands.append(unknown)
        for band in bands:
            if len(band) >= 2:
                out.append((roles, sorted(n for n, _mv in band)))
    out.sort(key=lambda r: (-len(r[1]), r[0]))
    return out


def cmd_shape(args):
    """Report a deck's structural SHAPE — wide/tall, fast/slow — from oracle text."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    meta, cards = parse_deck_file(d["path"])
    carddata, mana = load_card_data(), load_mana()
    sh = deck_shape(cards, carddata, mana)
    print(f"Shape — deck {d['id']}: {d['name'] or d['path']}\n")
    print(f"  axis          : {sh['axis']}")
    print(f"  speed         : {sh['speed']}  (avg nonland MV {sh['avg_mv']})")
    print(f"  wide score    : {sh['wide']:>3}   creature copies {sh['creatures']}, "
          f"evasive {sh['evasive']}")
    print(f"  tall score    : {sh['tall']:>3}")
    if sh["wide_cards"]:
        print(f"\n  WIDE effects ({len(sh['wide_cards'])}): {', '.join(sh['wide_cards'][:10])}"
              + ("…" if len(sh['wide_cards']) > 10 else ""))
    if sh["tall_cards"]:
        print(f"  TALL effects ({len(sh['tall_cards'])}): {', '.join(sh['tall_cards'][:10])}"
              + ("…" if len(sh['tall_cards']) > 10 else ""))
    print("\n  Shape is not quality — a wide deck is not better than a tall one. This "
          "answers the\n  question themes cannot: two decks sharing every tag can be "
          "opposite decks, and a\n  `#: archetype:` header is prose that can go stale. "
          "Read the effect lists, not just\n  the verdict — the scores are a text scan.")
    return 0


def _print_near_duplicates(cards, carddata, mana):
    groups = near_duplicates(cards, carddata, mana)
    if not groups:
        return
    print("\nINTERCHANGEABLE cards (same functional roles, same cost band) — these do the "
          "same job\nin this deck. Often deliberate redundancy; the point is to SEE the "
          "group before cutting\none at random, or before adding an eighth copy of an "
          "effect you are already deep in:")
    for roles, names in groups[:8]:
        print(f"  [{', '.join(roles)}] ×{len(names)}: {', '.join(names)}")
    if len(groups) > 8:
        print(f"  … and {len(groups) - 8} more group(s)")


def cmd_redundancy(args):
    """Competitive-consistency planner (virtual copies first). Shows each plan-effect's
    depth (distinct cards providing it), flags the THIN ones, and for each proposes how to
    firm it up — functional (virtual) copies FIRST so the deck stays semi-singleton, with
    true duplicates only as a fallback when there aren't enough of acceptable quality."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    carddata = load_card_data()
    rar = load_rarities()
    # For the gate check on each PROPOSED add (`unmet_gate_note`) — this command did not
    # otherwise need the card list, which is exactly why nobody asked `target_counts`
    # about a recommendation.
    _rmeta, _rcards = parse_deck_file(d["path"])
    _rmana = load_mana()
    target = getattr(args, "target", None) or _REDUNDANCY_TARGET
    buckets = effect_redundancy(d)
    if not buckets:
        print(f"Deck {d['id']}: no plan-effects to analyze.")
        return 0
    print(f"Redundancy — deck {d['id']}: {d['name'] or d['path']}  "
          f"(competitive consistency; virtual copies first, target {target})")
    print("\nEffect depth (distinct cards = virtual-copy count; higher = drawn more reliably):")
    for name, b in sorted(buckets.items(), key=lambda kv: (-kv[1]["depth"], kv[0])):
        mark = "✓ deep" if b["depth"] >= target else ("~ ok" if b["depth"] > _REDUNDANCY_THIN else "△ THIN")
        print(f"  {name:22} {b['depth']:>2}  {mark}   ({b['kind']})")

    thin = {n: b for n, b in buckets.items() if b["depth"] <= _REDUNDANCY_THIN}
    if not thin:
        print(f"\n✓ every plan-effect runs >{_REDUNDANCY_THIN} virtual copies — already consistent.")
        return 0
    print(f"\nThin effects (≤{_REDUNDANCY_THIN} copies = the real singleton variance) — "
          "firm up FUNCTIONALLY first, duplicate only as fallback:")
    for name, b in sorted(thin.items(), key=lambda kv: kv[1]["depth"]):
        best = max((_card_power(c.lower(), carddata, rar) for c in b["cards"]), default=0.0)
        if b["kind"] == "role":
            owned_f = owned_role_fillers(d, {name}, limit=8)
            craft_f = craft_role_fillers(d, {name}, limit=8)
            opts = [(_card_power(nm.lower(), carddata, rar), nm, True) for _mv, nm, *_ in owned_f]
            opts += [(_card_power(nm.lower(), carddata, rar), nm, False)
                     for _rk, _mv, nm, *_rest in craft_f]
            opts.sort(key=lambda r: -r[0])
        else:
            opts = [(pw, nm, own) for pw, nm, own, _mv, _r in functional_theme_options(d, name, limit=10)]
        plan = plan_redundancy_fill(b["depth"], best, [(p, n) for p, n, *_ in opts], target=target)
        own_of = {n: o for p, n, o in opts}
        print(f"\n  {name}  ({b['depth']} now: {', '.join(b['cards'])}):")
        if plan["functional"]:
            print("    ✓ add virtual copies (distinct cards — keeps it singleton):")
            for pw, nm in plan["functional"]:
                tag = "owned" if own_of.get(nm) else "craft"
                gate = unmet_gate_note(nm, _rcards, carddata, _rmana)
                print(f"        + {nm[:34]:34} [{tag}]  pw~{pw:.1f}"
                      + (f"   {gate}" if gate else ""))
        if plan["duplicates"]:
            strongest = max(b["cards"], key=lambda c: _card_power(c.lower(), carddata, rar))
            print(f"    ⚠ then run {plan['duplicates']} true duplicate(s) — {plan['reason']}:")
            print(f"        run {plan['duplicates']}× more {strongest} (pw~{best:.1f})")
        elif not plan["functional"]:
            print(f"    (already at target, or nothing to add)")
        else:
            print(f"    → {plan['reason']}")
    print("\nVirtual copies keep the highlander feel and score the SAME tier floor (the floor "
          "counts effects, not distinct cards); duplicates are the fallback when a specific "
          "effect can't be diversified at comparable power.")
    _meta_r, _cards_r = parse_deck_file(d["path"])
    _print_near_duplicates(_cards_r, carddata, load_mana())
    return 0


def tier_consistency(d):
    """(claimed, implied, mismatch, msg) for a deck's claimed tier vs its metrics
    floor. `mismatch` is True only when a claimed tier sits ≥2 bands ABOVE the floor
    (indefensible / stale) — a soft signal to re-grade, never an auto-assignment.
    An untiered deck returns claimed='' and mismatch False."""
    meta, _cards = parse_deck_file(d["path"])
    claimed = _deck_tier(meta)
    vec = deck_quality_vector(d)
    implied = tier_band(vec)
    if not claimed:
        return "", implied, False, "untiered"
    gap = TIER_RANK.get(claimed, 0) - TIER_RANK.get(implied, 0)
    if gap >= 2:
        why = []
        if vec["uncastable"]:
            why.append(f"{vec['uncastable']} uncastable")
        why.append(f"interaction {vec['interaction']}, card-adv {vec['card_advantage']}")
        if vec.get("plan") == "aggro":
            why.append(f"aggro clock {_clock_score(vec)}/7")
        return claimed, implied, True, (
            f"tier {claimed} sits {gap} bands above the metrics floor (~{implied}): "
            + "; ".join(why))
    return claimed, implied, False, f"tier {claimed}, metrics floor ~{implied}"


def tier_consistency_issues():
    """Roster-wide (id, claimed, implied, msg) for decks whose claimed tier is
    indefensibly high vs its metrics — folded into check_all as a soft warning."""
    out = []
    for d in roster_decks():
        claimed, implied, mismatch, msg = tier_consistency(d)
        if mismatch:
            out.append((d["id"], claimed, implied, msg))
    return out


# A deck's `#: tier:` rationale is prose, so nothing kept it honest as the list changed
# underneath it — and it went stale twice in one session: 40a's rationale still argued
# from Chelonian Tackle and Unforgiving Aim after both were cut, and deck 40's cited a
# 2.26 curve after a swap moved it to 2.32. A *defensible* grade rotting into an
# indefensible one is the exact failure the tier guard exists to prevent, but the guard
# only compares the LETTER to the floor — it never reads the argument. This does.
#
# Figures worth checking are the ones a rationale actually quotes. Each maps to a live
# vector key; a mismatch is reported, never rewritten (the prose is a human argument).
# Between a label and its number the prose often puts a bracket, a qualifier, or both:
# `interaction (3)`, `interaction total (3)`, `card advantage is thinner (3)`, `curve
# (2.81)`. The original patterns demanded whitespace then digits, so EVERY parenthesised
# figure was invisible — eight of them sat on the roster, and deck 23 reported "clean"
# while quoting a curve of 3.6 against a live 3.47. Same silent-false-negative class as
# the bare-`over` and `a 2.44 curve` misses recorded above; a figure the audit cannot see
# is a figure that rots.
#
# The gap is bounded to two intervening lowercase words so a label cannot reach across a
# clause and adopt an unrelated number — "interaction and card advantage 7" stays unmatched
# for `interaction` (three words) and is picked up by the card-advantage pattern instead.
#
# The parenthesised form requires the bracket to close IMMEDIATELY after the digits, and
# that is the load-bearing part. The roster's house style is a number-first claim followed
# by a BREAKDOWN — "7 interaction (5 spot removal + 2 sweepers)", "8 interaction (6 removal
# + 2 sweepers)" — where the parenthetical decomposes the figure instead of restating it.
# A permissive `\((\d+)` read the first sub-count as the claim and reported four decks as
# stale against numbers they never asserted. `\((\d+)\)` keeps the genuine cases
# ("dense interaction (12)", "card advantage is thinner (3)") and drops every breakdown.
_FIG_GAP = r"[  ]+(?:[a-z]+[  ]+){0,2}"
_FIG_PAREN = _FIG_GAP + r"\((\d+)\)"
# The NUMBER-FIRST patterns below start with a bare `(\d+)`, which is unanchored — so it
# happily matches the tail of a LARGER number that happens to sit before the metric word.
# A DATE is the case that fires in practice: deck 63's rationale said "three cards after
# the 2026-08 protection pass" and the audit reported `protection 08` against a live 4,
# i.e. it invented a claim the prose never made. A false POSITIVE here is the expensive
# direction — it trains you to ignore the audit, which is the one check that reads the
# argument rather than the letter. This guard rejects a number preceded by a digit, a
# decimal point, or a digit-hyphen (the `YYYY-MM` shape); each lookbehind is fixed-width,
# as Python requires. It deliberately also rejects a RANGE ("2-3 interaction"), which is
# not a precise claim and should not be audited as one.
_FIG_NUM = r"(?<![\d.])(?<!\d-)(\d+)"
_FIG_DEC = r"(?<![\d.])(?<!\d-)(\d+\.\d+)"
_RATIONALE_FIGURES = [
    (re.compile(r"interaction[  ]+(\d+)", re.I), "interaction"),
    (re.compile(r"interaction" + _FIG_PAREN, re.I), "interaction"),
    (re.compile(r"card[- ]adv(?:antage)?[  ]+(\d+)", re.I), "card_advantage"),
    (re.compile(r"card[- ]adv(?:antage)?" + _FIG_PAREN, re.I), "card_advantage"),
    # `avg` alone missed the word people actually write. Deck 52a's rationale said
    # "Average nonland MV 4.17" and the audit passed it while the live value was 4.22 —
    # "avg" is not a prefix of "Average", so no pattern here could ever see it. Same
    # class as the number-first miss recorded below: the pattern knew one spelling of a
    # figure the prose writes several ways.
    (re.compile(r"(?:avg|average) (?:nonland )?MV[  ]+(\d+\.\d+)", re.I), "avg_mv"),
    (re.compile(r"curve(?: of)?[  ]+(\d+\.\d+)", re.I), "avg_mv"),
    (re.compile(r"(?:avg|average) (?:nonland )?MV" + _FIG_PAREN.replace(r"(\d+)",
                                                                        r"(\d+\.\d+)"), re.I),
     "avg_mv"),
    (re.compile(r"curve" + _FIG_PAREN.replace(r"(\d+)", r"(\d+\.\d+)"), re.I), "avg_mv"),
    # The roster writes these NUMBER-FIRST far more often than the label-first form the
    # original patterns read — 13 interaction figures, 3 card-advantage, 1 protection,
    # none of them ever audited. Exactly the miss already recorded for avg_mv below,
    # repeated on the three axes the tier FLOOR is actually computed from.
    (re.compile(_FIG_NUM + r"[  ]+interaction", re.I), "interaction"),
    (re.compile(_FIG_NUM + r"[  ]+card[- ]adv(?:antage)?", re.I), "card_advantage"),
    (re.compile(_FIG_NUM + r"[  ]+protection", re.I), "protection"),
    # …and the house phrasing, where the number comes FIRST ("a tight 2.44 curve").
    # The pattern above only reads "curve of 2.44" / "avg MV 2.44", which the rationales
    # essentially never use: roster-wide it matched ONE figure against fourteen written
    # the other way round, so the avg_mv half of this audit was decorative. Six stale
    # curve figures were sitting in the prose, invisible, when this was added.
    (re.compile(_FIG_DEC + r"[  ]+curve", re.I), "avg_mv"),
    # The reversal above was only ever taught the word "curve". The other house phrasing
    # for the same figure is "3.19 average" — and the FORWARD pattern requires "average"
    # to be followed by MV, so a bare number-then-"average" matched nothing in either
    # direction. Deck 53's prose read "3.19 average" while the live vector said 3.39 and
    # the audit reported the rationale CURRENT. Same shape as the G-26 residual where a
    # copula between a label and its number hides a figure: the audit is only as good as
    # its phrasing coverage, and a miss here is silent by construction.
    (re.compile(_FIG_DEC + r"[  ]+average", re.I), "avg_mv"),
    (re.compile(_FIG_NUM + r"[- ]theme", re.I), "central_themes"),
    (re.compile(_FIG_NUM + r" central themes", re.I), "central_themes"),
    (re.compile(r"protection[  ]+(\d+)", re.I), "protection"),
    (re.compile(r"protection" + _FIG_PAREN, re.I), "protection"),
    # EARLY DROPS were in the quality vector but never audited, so a count could go stale
    # in total silence — deck 23 claimed "6 one-two-drops" against a live 11. Both
    # phrasings below are taken from the roster's own prose rather than invented.
    (re.compile(_FIG_NUM + r"[  ]+(?:early|cheap) drops?", re.I), "early_drops"),
    (re.compile(_FIG_NUM + r"[- ]one[- ]two[- ]drops?", re.I), "early_drops"),
]

# COLOUR SOURCES — the manabase axis, which every pattern above is blind to because it is
# not in `deck_quality_vector`. Deck 78's tier block claimed "~51% against 13/8/8
# sources", the manabase was rebuilt to 13/8/10 (56.6%), and `--audit-rationale` still
# reported the rationale CURRENT (2026-09-02): a colour-source claim could rot forever.
#
# One pattern per colour, so the existing single-capture-group shape holds and EVERY
# suppression the figure loop already applies (other-deck id, roster deck name,
# population subject, history, percent/draw misreads) is reused rather than
# reimplemented by a parallel pass.
#
# Two guards, both measured against the roster rather than invented:
#   DELTAS — prose writes a change as often as a count ("wanting roughly +8 white
#   sources", deck 19), and a delta is not a claim about the current list.
#   WANTS  — `deck.py consistency` prints "want 13 G sources (have 8, +5)" and that line
#   gets pasted into rationales verbatim; the target is not the holding.
# Case-SENSITIVE on purpose: the single-letter alternative would otherwise let a stray
# lowercase "g"/"r" before "sources" match.
_FIG_COLOR_WORDS = (("W", "white"), ("U", "blue"), ("B", "black"),
                    ("R", "red"), ("G", "green"))
_FIG_SOURCE_WANT = re.compile(r"\bwants?\b[^.;]{0,20}$", re.I)
_RATIONALE_FIGURES += [
    (re.compile(rf"(?<![+\-\d])\b(\d{{1,2}})[  ]+(?:{_c}|{_w})[  ]+sources?\b"),
     f"sources_{_c}")
    for _c, _w in _FIG_COLOR_WORDS
]


# The SLASH idiom — "13/8/10 sources", the shape deck 78's own tier line writes and the
# case that motivated the per-colour patterns above, which cannot see it (BS8-16). The
# claim is a MULTISET of the deck's non-zero source counts (the colour order is whatever
# the prose chose), so it is checked as one: same WANT/DELTA guards as the per-colour form.
_FIG_SOURCE_SLASH = re.compile(r"(?<![+\-\d/])(\d{1,2}(?:/\d{1,2}){1,4})[  ]+sources?\b")

# THE FLOOR BAND IS A CLAIM AND IT WAS THE ONE CLAIM NOTHING CHECKED. Every figure this
# audit prices resolves through `_figure_lookup`, which holds the quality vector plus
# the colour-source counts — all NUMBERS. A rationale's commonest structural assertion
# is a LETTER ("the metrics floor is A", "one band UNDER its A floor"), and a letter
# matched no pattern, so it was unverifiable by construction. That is not a hypothetical
# gap: re-deriving `TIER_FLOOR_REQ` from the roster distribution (BS8-06) moved 30-odd
# floors and left 15 of the roster's 36 floor-band claims false the same day, every one
# of them reported CURRENT by this audit. The letter is cheap to check — the floor is a
# pure function of the vector — and the claim is unambiguous, which is why this scan has
# none of the hedging the figure families need: measured on the roster at 36 raw hits,
# 15 stale, and ZERO false positives.
#
# The letter class is deliberately NOT case-folded (the words around it are): a band is
# written uppercase in every rationale on the roster, and `re.I` on the letter would
# read the article in "a floor of about 4 sources" as a claim of band A.
_FIG_FLOOR_BAND = re.compile(
    r"(?:metrics[ -]?)?floor\s+(?:reads?|is|sits\s+at|of|at)\s+(?:an?\s+)?(?P<b1>[SABCD])\b"
    r"|one\s+band\s+(?:under|over|above|below)\s+(?:its|the)\s+(?P<b2>[SABCD])[ -]"
    r"(?:metrics\s+)?floor\b"
    r"|(?:reads?|sits\s+at)\s+(?:an?\s+)?(?P<b3>[SABCD])[ -]floor\b", re.I)

# A claim about a floor the deck is AIMING at ("to reach an A floor", `tier --to A`) is a
# target, not an assertion about the current list — the same rule `_FIG_SOURCE_WANT`
# applies to a colour-source want.
_FIG_FLOOR_WANT = re.compile(r"\b(?:wants?|to\s+reach|target(?:s|ing)?|--to|aim\w*\s+(?:at|for))"
                             r"\b[^.;]{0,24}$", re.I)

# A band claim is NOT suppressed by the shared `_figure_is_history`, and that is the one
# place this scan deliberately parts company with the numeric families beside it. Their
# history rule keys on a change narrative (`4 -> 7`, `re-graded B→A`), which for a NUMBER
# means the figure next to it is probably the old value. For a BAND the same narrative
# means the opposite: "interaction 4 -> 7 … put the metrics floor at A" is an assertion
# about where the change LANDED, i.e. a claim about the current floor. Applying the
# shared rule silently dropped 3 of the roster's 15 stale claims (decks 12/23/69a), all
# three of them real. What actually marks a band claim as history is the TENSE of the
# verb the pattern already captured — "the floor READ A" against "the floor READS A" —
# plus an explicit retrospective cue.
_FIG_FLOOR_PAST = re.compile(r"\b(?:used\s+to|before|until|previously|no\s+longer)\b"
                             r"[^.;]{0,30}$", re.I)

# "…held ONE band under the floor AT B" names the LETTER, not the floor — deck 75's
# idiom, and the one false positive the roster produced. The bare `at` verb is what
# admits it (the sibling "put the metrics floor at A" needs `at` and is a real claim), so
# only that form is guarded, and only against a BAND-RELATIVE preposition: after
# "under/over/above/below the", the letter following `at` is where the deck is HELD.
_FIG_FLOOR_HELD = re.compile(r"\b(?:under|over|above|below)\s+(?:the|its)\s+$", re.I)


def _floor_band_claims(prose, live_band):
    """[(key, quoted, actual)] for every claim in `prose` about THIS deck's metrics floor
    whose band letter is not the live one. `live_band` is `tier_band(vec)`.

    Positional suppressions only (a want cue before the match); the CLAUSE-scoped
    cross-deck and history rules are applied by the caller, which already computes them
    for the figure loop, so a floor claim about another deck or a documented past floor
    is suppressed by exactly the rules that suppress a numeric one."""
    out = []
    for m in _FIG_FLOOR_BAND.finditer(prose or ""):
        band = next(g for g in (m.group("b1"), m.group("b2"), m.group("b3")) if g)
        if not band.isupper():
            continue
        if _FIG_FLOOR_WANT.search(prose[max(0, m.start() - 30):m.start()]):
            continue
        if _FIG_FLOOR_PAST.search(prose[max(0, m.start() - 40):m.start()]):
            continue
        # "the floor READ A" is the past value; "the floor READS A" is the claim.
        if re.match(r"(?:metrics[ -]?)?floor\s+read\b", m.group(0), re.I):
            continue
        if (re.match(r"(?:metrics[ -]?)?floor\s+at\b", m.group(0), re.I)
                and _FIG_FLOOR_HELD.search(prose[max(0, m.start() - 30):m.start()])):
            continue
        if band != live_band:
            out.append((m.start(), m.end(), band))
    return out



def _slash_source_claims(prose, sources, colors=None):
    """[(key, quoted, actual)] for every "N/N/N sources" claim in `prose` whose numbers
    do not match the deck's source counts as a multiset. `sources` is the
    `deck_color_sources` dict; `colors` (the deck's `#: colors:`, in header order)
    scopes the comparison to the colours the deck RUNS — an any-colour land is a real
    source of every colour, so the off-colour counts are non-zero and are not what the
    prose claims. `actual` is rendered in header order so a re-grounding reads
    naturally. A claim preceded by `want`/`+` is a target or a delta, not a count, and
    is skipped — the same rule the per-colour patterns apply."""
    out = []
    scope = card_colors(colors) if colors else set()
    order = [c for c in "WUBRG" if c in scope] or [c for c in "WUBRG" if (sources or {}).get(c)]
    live_in_order = [(sources or {}).get(c, 0) for c in order]
    live = sorted(live_in_order)
    for m in _FIG_SOURCE_SLASH.finditer(prose or ""):
        before = prose[max(0, m.start() - 24):m.start()]
        if _FIG_SOURCE_WANT.search(before):
            continue
        qvals = [int(x) for x in m.group(1).split("/")]
        if sorted(qvals) != live:
            # Render the live counts in the ORDER the prose used, matched by rank (the
            # prose's colour order is whatever it chose; a re-grounding must not reorder
            # its argument): "13/8/10" against live W14 U9 G11 reads back as "14/9/11".
            by_rank = sorted(live, reverse=True)
            qrank = sorted(range(len(qvals)), key=lambda i: -qvals[i])
            rendered = [0] * len(qvals)
            for pos, i in enumerate(qrank):
                rendered[i] = by_rank[pos] if pos < len(by_rank) else 0
            if len(qvals) != len(live):
                rendered = live_in_order
            out.append(("sources", m.group(1), "/".join(str(n) for n in rendered)))
    return out


def _figure_lookup(vec, cards, carddata):
    """The quality vector PLUS the deck's colour-source counts, keyed `sources_W` etc.

    One lookup so the figure loop stays single-pass. `deck_color_sources` is the same
    rule `deck.py mana` prints — and it wants `load_card_meta()`, NOT the deck's `#:`
    header meta: passing the latter counts basics only and reports almost every claim
    stale, which is how this fix was nearly mis-measured on the day it was written."""
    out = dict(vec)
    try:
        src = deck_color_sources(cards, load_card_meta(), carddata)
    except Exception:
        return out          # a figure we cannot price is skipped, never guessed
    for col, n in src.items():
        out[f"sources_{col}"] = n
    return out
# Words that are also real card names ("Negate", "Rest in Peace", …). Requiring a
# multi-word name or a long single word keeps the scan quiet; a citation of a one-word
# card is rare in prose and not worth a false positive on every "Opt" or "Duress".
_RATIONALE_MIN_LEN = 9

# A rationale legitimately names cards that AREN'T in the deck: it documents the swap
# that removed one ("Essence Scatter's creatures-only … became hard counters"), notes a
# land that left, or points at a flex/craft option deliberately held out of the 60
# (Genesis Wave). Flagging those would make the audit noise, and a noisy audit gets
# ignored — which is worse than no audit. So a citation sitting next to change- or
# flex-language is treated as history, not as a live argument. The cost is a real miss
# when someone writes "held from A by <cut card>" right after the word "replaced"; the
# figure check below is the independent backstop for that.
# NOTE what is NOT here: a bare "over". It was, and it silently disabled the FIGURE
# half of this audit across the roster, because "card advantage 9 OVER a 2.86 curve" is
# the house phrasing for a quality vector — so the one cue meant to catch a rationale
# describing a PAST figure was matching the sentence that states the CURRENT one. Deck
# 43 quoted interaction 10 against a live 8 and the audit reported clean. Every other
# cue here is a word that only appears when prose is describing a change; "over" is
# ordinary English and was far too broad to earn a place among them.
# `remov\w*` used to sit here, and it suppressed a card citation by matching the card's
# own ORACLE TEXT. The archetype prose of deck 52a read "Summon: Bahamut is a {9} that
# REMOVES two nonland permanents"; `removes` fell inside the ±140 window, so the audit
# reported "rationale is current" while the header argued from a card two swaps had
# already cut. The same word is already documented four lines down as "the worst of
# them" on the FIGURE path, where it was narrowed because `removal` is the commonest
# noun in a rationale about interaction — but only the figure path was fixed, and the
# CARD path kept the broad form. `removes` is oracle-text vocabulary, not change
# language; a rationale states a change in the past or progressive ("removed it",
# "removing the second wipe"), so those are what the cue needs to match.
_HISTORY_CUES = re.compile(
    r"\b(?:was|were|became|becomes|replac\w*|swap\w*|cut\w*|remov(?:ed|ing)|dropp\w*|"
    r"left|leaves|instead|no longer|previously|earlier|former\w*|queued|flex|"
    r"craft target|alternative|revisit|option|skipped|held out|used to|missing|"
    r"exclud\w*)\b", re.I)
# The last three joined on the 2026-08-09 clause-scoping sweep: "the argument this
# block USED TO make for Ramos", "still MISSING the tribal payoffs (Regal
# Imperiosaur…)" and "Fire Lord Zuko was EXCLUDED for…" are all change-/WIP-language
# that the old ±140 window happened to suppress via unrelated cues further away.
_HISTORY_WINDOW = 140
# "<in-deck card> is <other card> that …" — a comparison used to EXPLAIN a card the deck
# runs. Matched immediately before the citation, never as a window cue (see the call site).
_SIMILE_BEFORE = re.compile(r"\b(?:is|are)\s+$", re.I)
# `0→1` / `1->4`: the matched number is the FROM side of a stated change.
_ARROW_AFTER = re.compile(r"\s*(?:→|->|—>|–>)")
# "X does NOT do this" — a citation immediately followed by a negation is a contrast
# with an absent card, not a claim the deck runs it (26a's Mjölnir note).
_NEGATION_AFTER = re.compile(r"\s+(?:does\s+not|doesn'?t|is\s+not|isn'?t|cannot|can'?t)\b", re.I)

# The SECOND way a citation is not a claim about the current list: it is about ANOTHER
# DECK, or about a change you have not made yet. Three real false positives drove this,
# all from rationales written the same week:
#   • "DISTINCTNESS vs deck 8 … that one is built on Bloodthirsty Conqueror" — naming a
#     card in the deck being compared AGAINST.
#   • "PATH TO A: a second copy of the payoff axis (a Drogskol Reaver …)" — naming a
#     card to ADD.
#   • "`similar` reads 91% against 42 Blood Price" — naming another DECK whose name is
#     also a card (Blood Price, ZNR). That one is fixed exactly, by masking roster deck
#     names; these cues cover the other two, which are prose shapes rather than names.
# Kept narrow deliberately: a rationale's own argument is written in the present tense
# about this deck, so comparative and prescriptive language is a reliable signal that
# the sentence has changed subject.
_COMPARISON_CUES = re.compile(
    r"\b(?:path to|vs\.?|versus|unlike|compared|comparison|distinctness|roster'?s|"
    r"another deck|other deck|that deck|that one|elsewhere|would|"
    r"consider|candidate|upgrade to|next add|instead of|variant|rather than|"
    r"parent|sibling|same shape)\b", re.I)
# `would` widened from `would be|would need` — "…where Laughing Jasper Flint and
# Rakdos, the Muscle WOULD each demand a hard {R}" is hypothetical-mode prose about a
# fork not taken, and the modal alone is the signal. `parent`/`sibling` are this
# repo's variant-comparison vocabulary ("its PARENT counts CREATURES — Craterhoof's X,
# Enduring Vitality…"); `same shape` is its simile idiom ("Funeral Room and Susur
# Secundi are the same shape"). All from the 2026-08-09 roster sweep.


# A clause boundary ends a suppression window. `[.;]` and not the em-dash, which this
# repo's prose uses mid-clause constantly ("— the deck wants"); requires following
# whitespace so decimals ("avg MV 2.42") and "e.g." survive.
_CLAUSE_BREAK = re.compile(r"[.;!?](?=\s)")
# "deck 56" / "deck 40a" — an explicit reference to a deck by id. Requires the word
# `deck` so a bare count ("16 Birds") can never read as one.
# `deck 42` is one way the prose cites a sibling; the POSSESSIVE `42's` is the other, and
# it is the commoner one — 35 occurrences roster-wide against a handful of the explicit
# form. Deck 68b's archetype says "{1}{G}{G}{G} on 68a's 12 green sources measured 31.6%",
# a claim about ANOTHER deck that the word-anchored pattern could not see, so it flagged
# against 68b's own 17 (2026-09-02, found by the colour-source scan below — the first
# figure family where bare-id citation is normal prose). Requiring the id to be a REAL
# roster id keeps it from eating ordinary possessives like "the 4's slot".
_OTHER_DECK_RE = re.compile(r"\bdeck\s+(\d+[a-z]?)\b", re.I)
# The POSSESSIVE form — `42's`, `68a's` — is the commoner idiom here: 35 occurrences
# roster-wide against a handful of the explicit `deck 42`. It is kept as a SEPARATE
# pattern gated on the id being a real roster id, because a bare `\d+[a-z]?'s` would
# otherwise eat ordinary prose ("the 4's slot", "a 2's worth of mana").
_OTHER_DECK_POSS_RE = re.compile(r"\b(\d{1,3}[a-z]?)'s\b")


def _other_deck_ids(clause):
    """Deck ids a clause CITES, lowercased. Both idioms, flattened, roster-checked.

    `_OTHER_DECK_RE.findall` returns plain strings for the word-anchored form; the
    possessive form is matched separately and filtered against the live roster so it
    cannot suppress on a number that merely looks like an id."""
    ids = {g.lower() for g in _OTHER_DECK_RE.findall(clause)}
    poss = {g.lower() for g in _OTHER_DECK_POSS_RE.findall(clause)}
    if poss:
        ids |= poss & {str(x["id"]).lower() for x in discover_decks()}
    return ids
# A SHARING claim is not a comparison, and treating it as one is how a false card
# citation survived for months. Deck 43's tier block read "only FIVE nonland cards are
# shared (Erode, Healer's Hawk, Starscape Cleric, Stroke of Midnight and Mister
# Negative)" — a sentence that names deck 42, so `_OTHER_DECK_RE` suppressed the whole
# clause as comparison context. But deck 43 had not run Erode for a long time, and a
# sharing claim ASSERTS THE CARD IS IN BOTH LISTS: it is a statement about this deck,
# not merely about the other one. Found by hand, 2026-08-24, while looking for
# interaction to add.
#
# So the other-deck suppression is skipped inside a sharing clause. This is a carve-out,
# not a loosening: every other cross-deck citation still suppresses exactly as before,
# and the cue list is kept NARROW on purpose (G-26 — a false positive is noisy and gets
# noticed, a false negative is silent). Measured across the roster when it landed.
_SHARING_CUES = re.compile(
    r"\b(?:share[sd]?|sharing|in common|both run|both play|overlap(?:s|ping)?)\b", re.I)
# A figure whose SUBJECT is the card POPULATION rather than this list. Deck 49's
# archetype prose argues "Standard's Dragons average MV 5.30, so a deck that wants to
# field several must SOLVE ITS OWN MANA" — a true statement about the format that the
# figure scan read as a stale claim about the deck's own 4.03 curve. Possessive form
# only, deliberately: "Standard's Dragons average…" names a population, while "fine in
# Standard, avg MV 2.4" is still a claim about this deck and must keep auditing.
_POPULATION_SUBJECT_RE = re.compile(
    r"\b(?:standard|alchemy|historic|brawl|pioneer|modern|explorer|timeless)'s\b"
    r"|\bthe (?:format|pool|meta|average)(?:'s)?\b", re.I)


def _clause_bounds(prose, start, end):
    """(lo, hi) of the clause containing prose[start:end] — the span between the
    nearest sentence-ish breaks. Both suppression families below are scoped to it."""
    lo = 0
    for m in _CLAUSE_BREAK.finditer(prose, 0, start):
        lo = m.end()
    m = _CLAUSE_BREAK.search(prose, end)
    hi = m.start() + 1 if m else len(prose)
    return lo, hi


def _cites_as_history(prose, pos, length):
    """True when a card citation is NOT an argument that this deck runs the card.

    Two families: change-/flex-language (the card left, or was deliberately held out —
    see _HISTORY_CUES) and comparative/prescriptive language (the sentence is about a
    different deck, or about a card to add — see _COMPARISON_CUES).

    Two scoping rules, both bought by live misses on 2026-08-09:
      * The window stops at a CLAUSE boundary. It used to be a flat ±140 chars, so a
        change-cue about DIFFERENT cards in the PREVIOUS sentence suppressed a live
        citation — deck 66's "…were cut for the aristocrats package. Mayhem stays as
        SEASONING on (Spider-Islanders, …)" audited clean after Spider-Islanders left,
        because "cut" sat one sentence back. A cue only speaks for its own clause.
      * The citation's own span is EXCLUDED from the cue search. `_HISTORY_CUES` has
        `swap\\w*`, so the card *Crib Swap* was suppressed by the "Swap" in its own
        name — the same class as the documented `remov\\w*` incident (a card whose
        oracle text said "removes" suppressed its own report), one level worse: no
        prose edit can ever un-suppress a card whose NAME matches a cue."""
    clo, chi = _clause_bounds(prose, pos, pos + length)
    lo = max(clo, pos - _HISTORY_WINDOW)
    hi = min(chi, pos + length + _HISTORY_WINDOW)
    before, after = prose[lo:pos], prose[pos + length:hi]
    if (_HISTORY_CUES.search(before) or _COMPARISON_CUES.search(before)
            or _HISTORY_CUES.search(after) or _COMPARISON_CUES.search(after)):
        return True
    # COMPARISON context reaches one clause further back than change-language does.
    # A distinctness passage sets its frame in the clause BEFORE the citations —
    # "taking the RED side of the fork instead of the blue one. Where 44 spends its
    # splash on two one-shot ETB thefts (Azula, Etrata), …" — while a HISTORY cue in
    # the previous clause is usually about different cards entirely (the deck-66
    # Spider-Islanders miss), so only the comparison family gets the extension.
    # An explicit other-deck reference ("Deck 26 ramps with MANA — …, Tony Stark's
    # free artifact drop") counts as comparison context the cue lists can't spell.
    prev_lo = max(_clause_bounds(prose, max(0, clo - 2), max(0, clo - 2))[0],
                  pos - _HISTORY_WINDOW)
    frame = prose[prev_lo:pos] + " " + prose[pos + length:hi]
    if _SHARING_CUES.search(prose[clo:chi]):
        # A sharing claim names cards this deck is asserted to RUN, so the other-deck
        # reference in it is not comparison context. Everything else still suppresses.
        return bool(_COMPARISON_CUES.search(prose[prev_lo:clo]))
    return bool(_COMPARISON_CUES.search(prose[prev_lo:clo])
                or _OTHER_DECK_RE.search(frame))


# A FIGURE is history under much narrower conditions than a CARD citation, and reusing
# the card rule for both is what silently disabled this half of the audit.
#
# `_cites_as_history` sweeps ±140 chars for any change-word, which is right for a card:
# "Essence Scatter … became hard counters" is about a card that left, and the whole
# sentence is history. A FIGURE is different — the number is history only when the
# NUMBER ITSELF is stated as past. A rationale routinely states a CURRENT figure in a
# sentence that also mentions a change, and the domain's ordinary vocabulary collides
# with the cue list head-on:
#
#   deck 41  "The floor reads A on interaction 9 … five surplus REMOVAL spells WERE
#             traded for the card advantage below"      → live interaction 8
#   deck 42  "…interaction 8 … five surplus REMOVAL spells BECAME the pay-life engine"
#                                                        → live interaction 6
#   deck 45a "…interaction 13 … 1. THE PAYOFF IS THE ONE CRAFT TARGET"
#                                                        → live interaction 12
#   deck 42a "\"restore the interaction\" WAS not the whole fix … At interaction 6"
#                                                        → live interaction 5
#
# `remov\w*` is the worst of them: it exists to catch "removed", and it matches
# "removal" — the single most common noun in a rationale that argues about interaction.
# This is the same shape as the bare `over` cue documented above: an ordinary word of
# the domain sitting in a list meant for change-language, silently suppressing the
# sentence it was supposed to check. Four stale interaction figures were hidden by it.
#
# So the figure test looks BACKWARD only, and only for past-tense language directly
# governing this number ("was 4", "up from 2", "it cited a 2.65 curve"). Comparison
# cues still apply — a prescriptive "path to A: +3 interaction" is not a claim — but on
# a tight window, since those shapes sit next to the number too.
_FIGURE_PAST = re.compile(
    r"\b(?:was|were|had|up from|down from|previously|formerly|used to be|"
    r"cited|quoted|read|stated|re-?graded|took it (?:from|to)|moved it (?:from|to))"
    r"\b[^.;]{0,24}$", re.I)
_FIGURE_BACK_WINDOW = 60
_FIGURE_CMP_WINDOW = 60


# A matched number that is not the metric at all. Both shapes are latent in the SHARED
# `_RATIONALE_FIGURES` patterns, so the guard sits with them and both scans call it.
#   PERCENT — "cast-on-curve 76.7%" matches `curve (\d+\.\d+)` and was reported as a
#   76.7 average mana value (deck 28's notes, twice). A percentage is a different
#   measurement wearing the same words.
#   DRAW-N  — "sac->draw 2 card advantage" matches `(\d+) card[- ]adv`; the 2 belongs to
#   "draw", and the adjacency is a coincidence (deck 8).
_FIGURE_PCT_AFTER = re.compile(r"\s*%")
_FIGURE_DRAW_BEFORE = re.compile(r"\bdraws?\s*$", re.I)


def _figure_misreads_prose(prose, start, end):
    """True when the pattern matched a number that is not this metric."""
    if _FIGURE_PCT_AFTER.match(prose, end):
        return True
    return bool(_FIGURE_DRAW_BEFORE.search(prose[max(0, start - 10):start]))


def _figure_is_history(prose, start, end):
    """True when a quoted figure is presented as a PAST value, not a current claim."""
    if _ARROW_AFTER.match(prose, end):
        return True                       # "0→1" — the match is the FROM side.
    # A figure inside QUOTATION MARKS is a citation of earlier prose, not a live claim:
    # deck 7 writes `The old one-line reason ("fast clock but thin interaction (3)") is no
    # longer true`, which asserts the opposite of what the number says. `_FIGURE_PAST`
    # cannot reach it — its cue must sit within 24 chars and "old" is 47 back — and
    # widening that window to compensate would loosen every other suppression. An odd
    # count of quote marks before the figure means we are inside a quoted span.
    if prose.count('"', 0, start) % 2 == 1:
        return True
    if _FIGURE_PAST.search(prose[max(0, start - _FIGURE_BACK_WINDOW):start]):
        return True
    lo, hi = max(0, start - _FIGURE_CMP_WINDOW), min(len(prose), end + _FIGURE_CMP_WINDOW)
    return bool(_COMPARISON_CUES.search(prose[lo:hi]))


# A replacement claim has TWO sides, and only one of them may name an absent card.
# `_cites_as_history` treats them alike: it sees change-language near the citation and
# stays quiet. That is RIGHT for the DEPARTING card ("Essence Scatter became hard
# counters" — Essence Scatter left, the sentence documents it) and WRONG for the
# ARRIVING one. "Spell Pierce was CUT for Shriek, Treblemaker" names Shriek as the card
# that came IN, so if Shriek is not in the deck the sentence isn't history — it is
# REVERSED, and it asserts a swap that no longer exists.
#
# That is not hypothetical: the Shriek swap was applied and then undone, and the audit
# reported deck 37b clean through both, because "CUT" sat adjacent to the name either
# way. It is the residual left over from the figure fix — the audit could see an absent
# card and a wrong number, but not a claim pointing the wrong way.
#
# The cue lists cover only the directional shapes the roster's prose actually uses
# (surveyed across every `#: tier:` block, not guessed): "cut/traded/swapped/exchanged
# … for X", "became X", "replaced by X", "in place of X", and the "+X" shorthand. A
# DEPARTING marker between the cue and the citation closes the window, because "+A
# (over B)" names both sides in one clause and B is legitimately gone.
# Two of my own bugs, both caught by sweeping the roster rather than by reasoning:
#   * the `+X` shorthand needs a CASE-SENSITIVE capital to mean "a card name", and the
#     `re.I` on this pattern silently defeated it — so the `+` in "hard counters + a
#     mythic finisher" read as a swap marker (deck 12). Hence the `(?-i:[A-Z])`.
#   * "cut for" is not always a replacement: "two heist cards were CUT for cause: Doom
#     Reigns Supreme wants five Villains" means cut for a REASON (deck 45). So the
#     arriving card must sit IMMEDIATELY after the cue — a short gap with no sentence
#     break in it, which "for cause:" fails and "for Shriek, Treblemaker" passes.
_ARRIVING_CUES = re.compile(
    r"\b(?:cut|traded|swapped|exchanged)\s+(?:it\s+)?for\b|\bbecames?\b"
    r"|\breplaced by\b|\bin place of\b|(?<![\w])\+(?=\s?(?-i:[A-Z]))", re.I)
_DEPARTING_CUES = re.compile(
    r"\bover\b|\binstead of\b|\brather than\b|(?<![\w])-(?=\s?(?-i:[A-Z]))", re.I)
_ARRIVING_WINDOW = 70
_ARRIVING_GAP = 25                 # cue → citation; longer means the subject moved on
_ARRIVING_BREAK = re.compile(r"[.;:—]")


def _cites_as_arriving(prose, pos):
    """True when a citation sits on the ARRIVING side of a stated replacement — i.e. the
    prose claims this card came IN, so its absence makes the claim false, not historical.
    """
    # The slice runs one char PAST the citation start: the `+X` cue is a lookahead for
    # a capital letter, and that capital IS prose[pos] — sliced at pos exactly, the
    # lookahead had nothing to see, so "+Crib Swap" never read as arriving (found via
    # the 2026-08-09 fixtures). A cue must still END at or before the citation.
    lo = max(0, pos - _ARRIVING_WINDOW)
    back = prose[lo:pos + 1]
    cue = None
    for m in _ARRIVING_CUES.finditer(back):
        if m.end() <= pos - lo:
            cue = m                              # nearest cue before the citation
    if cue is None:
        return False
    gap = back[cue.end():pos - lo]
    if len(gap) > _ARRIVING_GAP or _ARRIVING_BREAK.search(gap):
        return False
    return not _DEPARTING_CUES.search(gap)


def _roster_deck_names(_cache={}):
    """Every deck's `#: name:`, longest first — masked out of a rationale before the
    card scan. A deck name that is ALSO a card name ("Blood Price", "Sacrifices") read
    as a stale citation whenever one deck's rationale named another for contrast, which
    is exactly what the distinctness prose is FOR. Exact, not heuristic."""
    if not _cache:
        names = set()
        for rec in discover_decks():
            nm = (rec.get("name") or "").strip()
            # Split a decorated title ("Blood Price — Orzhov Aristocrats") so the core
            # name masks too; drop short fragments that would mask real prose.
            for part in re.split(r"\s+[—–-]\s+", nm):
                part = part.strip()
                if len(part) >= _RATIONALE_MIN_LEN or " " in part:
                    names.add(part)
            if nm:
                names.add(nm)
        _cache["names"] = sorted(names, key=len, reverse=True)
    return _cache["names"]


def _find_word_bounded(text, needle):
    """First word-bounded occurrence of `needle` in `text`, or -1. The boundary rule
    is the citation scan's: a neighbour that is alphanumeric, an apostrophe or a
    hyphen means we are inside a longer word ("Deliberately" must not match
    *Deliberate*)."""
    start = 0
    while True:
        i = text.find(needle, start)
        if i < 0:
            return -1
        before_ok = i == 0 or not (text[i - 1].isalnum() or text[i - 1] in "'-")
        j = i + len(needle)
        after_ok = j >= len(text) or not (text[j].isalnum() or text[j] in "'-")
        # POSSESSIVE. "`consistency` prices Aven Interrupter's {W}{W} at 58%" cites
        # Aven Interrupter, but the apostrophe rule above — built to keep *Deliberate*
        # out of "Deliberately" — read the 's as "inside a longer word", so every
        # possessive citation was invisible to the scan (the audit's fifth live miss
        # of 2026-08-09, reproduced in tests). An 's that ENDS the word is grammar,
        # not a longer card name.
        if (not after_ok and text[j] == "'" and text[j:j + 2] in ("'s", "'S")
                and (j + 2 >= len(text)
                     or not (text[j + 2].isalnum() or text[j + 2] in "'-"))):
            after_ok = True
        if before_ok and after_ok:
            return i
        start = i + 1


def _shorthand_index(carddata, _cache={}):
    """shorthand fragment -> full display name, for MULTI-WORD card names.

    The citation scan matches FULL names, so a rationale that abbreviates an ABSENT
    card was invisible: deck 28's archetype cited "Gishath" after Gishath, Sun's
    Avatar was cut, deck 36's cited "Okinec Ahau" after Sovereign Okinec Ahau was
    cut, and both audits reported clean (broad-implement #2). G-26's "shorthand IS
    handled" covered only the SUPPRESSION direction — an abbreviation of a card the
    deck RUNS must not flag — never detection. Fragments are the comma-head
    ("Gishath") and the capitalized word-tails ("Okinec Ahau"). Maps fragment ->
    sorted tuple of EVERY full name it abbreviates: an ambiguous fragment stays in
    the index, because a citation whose every candidate is absent from the deck is
    stale whichever card it meant — "Okinec Ahau" abbreviates both Envoy of and
    Sovereign Okinec Ahau, and dropping ambiguity is exactly how the real deck 36
    miss would have survived this fix. A fragment shared by more than a few names
    is an epithet, not shorthand, and is dropped; so is one that IS a full card
    name (the main scan owns those). Memoized per carddata generation."""
    key = id(carddata)
    if _cache.get("key") == key:
        return _cache["idx"]
    frags = {}
    for name, row in carddata.items():
        disp = row.get("name") or name
        front = disp.split(" // ")[0]
        cands = set()
        # Comma-head minimum is 4, not 6: "Inti exiles the top card" cited Inti,
        # Seneschal of the Sun after he was cut, and a 6-char floor kept every short
        # legend name (Inti, Ruby, Zuko, Suki, Momo…) out of the index — an entire
        # class of Universe-Beyond first-name shorthand was invisible (2026-08-09).
        # The epithet cap (≤3 full names), case-sensitivity and the in-deck substring
        # suppression carry the false-positive load a shorter floor admits.
        head = front.split(",")[0].strip()
        if "," in front and len(head) >= 4 and head[0].isupper():
            cands.add(head)
        words = front.replace(",", "").split()
        for i in range(1, max(0, len(words) - 1)):
            tail = " ".join(words[i:])
            if len(tail) >= 8 and tail[0].isupper():
                cands.add(tail)
        for c in cands:
            frags.setdefault(c, set()).add(disp)
    full_names = {row.get("name") or n for n, row in carddata.items()}
    # Guild names are the domain's COLOR vocabulary before they are card comma-heads:
    # "Rakdos sacrifice deck" cites no card, and four decks false-flagged on it in the
    # first roster sweep of this fix. (Shards/wedges — Naya, Jeskai — aren't comma-heads
    # of any pool card, so the ten guilds are the whole collision class.)
    _GUILDS = {"Azorius", "Dimir", "Rakdos", "Gruul", "Selesnya",
               "Orzhov", "Izzet", "Golgari", "Boros", "Simic"}
    idx = {c: tuple(sorted(names)) for c, names in frags.items()
           if c not in full_names and c not in _GUILDS and len(names) <= 3}
    _cache.clear()
    _cache.update(key=key, idx=idx)
    return idx


def _shorthand_candidates(masked, frags):
    """[(fragment, pos)] — capitalized 1–3-word spans of `masked` that are known
    shorthand fragments. Prose-driven so cost scales with the rationale's length,
    not the pool's size."""
    tokens = [(m.group(0), m.start()) for m in re.finditer(r"[A-Za-z][\w'-]*", masked)]
    out = []
    for k, (w, p) in enumerate(tokens):
        if not w[0].isupper():
            continue
        for n in (1, 2, 3):
            if k + n > len(tokens):
                break
            lw, lp = tokens[k + n - 1]
            frag = masked[p:lp + len(lw)]
            if frag in frags:
                # A fragment WRITING A LABEL is prose structure, not a citation:
                # "Down: the manabase is three colours" is the house "what argues
                # DOWN" idiom, and with 4-char comma-heads indexed it read as
                # shorthand for *Down, Down to Goblin-town* (54a, roster sweep).
                if masked[lp + len(lw):lp + len(lw) + 1] == ":":
                    continue
                out.append((frag, p))
    return out


def rationale_staleness(d, carddata=None):
    """(stale_cards, stale_figures) for a deck's `#: tier:` / `#: notes:` prose.

      stale_cards   — [(name, header)] the rationale names that are NOT in the deck
                      any more (a cut card the argument still leans on),
      stale_figures — [(key, quoted, actual)] a figure the prose quotes that no longer
                      matches `deck_quality_vector`.

    Report-only: the prose is a human argument and this never edits it. Names are
    matched against known cards so ordinary English can't trip it."""
    carddata = carddata if carddata is not None else load_card_data()
    meta, cards = parse_deck_file(d["path"])
    in_deck = {n for _q, n, _s, _c in cards}
    in_deck |= {n.split(" // ")[0] for n in list(in_deck)}
    stale_cards, stale_figures = [], []
    # `#: archetype:` is scanned alongside `#: tier:` because it is equally a CLAIM
    # about the current deck — "these cards push your life total up" is false once those
    # cards are cut, and the header is what a reader trusts first. (Found by this deck's
    # own archetype text surviving three rounds of swaps that removed every card it
    # named.) `#: notes:` stays out: it is a free-form build log where naming an absent
    # card is correct.
    for header in ("tier", "archetype"):
        prose = (meta or {}).get(header, "") or ""
        if not prose:
            continue
        # Mask every card the deck DOES run before scanning, longest name first. Without
        # this, a shorter card name nested inside a longer one reads as a stale citation:
        # "the Ooze Spill / Amazing Acrobatics upgrade" reported the card *The Ooze*.
        masked = prose
        for nm in sorted(in_deck, key=len, reverse=True):
            masked = masked.replace(nm, " " * len(nm))
        # ...and mask roster DECK names, which the distinctness prose names on purpose.
        for nm in _roster_deck_names():
            masked = masked.replace(nm, " " * len(nm))
        # Every full card name that OCCURS in this prose, whether it was reported stale
        # or suppressed. Consumed by the shorthand pass below — see the comment there.
        seen_full_names = set()
        for name, row in carddata.items():
            disp = row.get("name") or name
            if len(disp) < _RATIONALE_MIN_LEN and " " not in disp:
                continue
            if disp in in_deck or name in BASICS or disp.split(" // ")[0] in in_deck:
                continue
            # SHORTHAND. A rationale abbreviates a card it runs — deck 33 writes
            # "Heartfire sac-removal" for Heartfire Immolator — and `Heartfire` is
            # itself a real card, so the scan reported a stale citation of a card the
            # prose never meant. Masking cannot help: the full name is not in the text.
            # A citation that is a strict word-prefix of a card the deck DOES run is an
            # abbreviation of that card, not a reference to a different one.
            if any(other.startswith(disp + " ") for other in in_deck):
                continue
            # CASE-SENSITIVE: prose capitalizes a card citation, so this is what keeps
            # ordinary vocabulary out. A lowercase "counterspell"/"food"/"negate" in a
            # sentence is not a reference to the card of that name.
            # Word-boundary match. A bare substring search reported the card
            # *Deliberate* inside the word "Deliberately" — and card names are common
            # enough English that this class of hit is frequent, not exotic.
            pos = _find_word_bounded(masked, disp)
            if pos < 0:
                continue
            seen_full_names.add(disp)
            # History suppression, EXCEPT on the arriving side of a stated replacement:
            # a card the prose says came IN is a claim about the current list, and its
            # absence means the sentence points the wrong way (see `_cites_as_arriving`).
            if (_cites_as_history(masked, pos, len(disp))
                    and not _cites_as_arriving(masked, pos)):
                continue
            # SIMILE. "It'll Quench Ya! is Spell Pierce that hits creatures too" explains
            # a card the deck runs BY NAMING a card it does not — the citation is the
            # yardstick, not the claim. This is positional rather than a window cue on
            # purpose: `is`/`are` in the ±140 window would suppress almost everything,
            # but immediately before the name it is reliable, because this scan only ever
            # sees cards the deck does NOT run (a real "the win condition is Krang" names
            # an in-deck card and never reaches here).
            if _SIMILE_BEFORE.search(masked[max(0, pos - 6):pos]):
                continue
            stale_cards.append((disp, header))
        # SHORTHAND DETECTION — the mirror of the suppression above: an ABSENT card
        # cited by abbreviation ("Gishath" for Gishath, Sun's Avatar; "Okinec Ahau"
        # for Sovereign Okinec Ahau). Both real misses survived a clean audit
        # (broad-implement #2). Same suppressions as a full-name citation.
        #
        # Scan a string with every OCCURRING full card name blanked, not `masked`.
        # `masked` hides only the cards the deck RUNS, so an ABSENT card's full name
        # is still in the text when the fragment pass runs — and a fragment of it then
        # resolves to whatever OTHER card abbreviates to that fragment. Live on deck 28
        # (2026-08-11): prose citing "Savage Land Dinosaur" produced a second, false
        # report of "Ka-Zar of the Savage Land", a card the prose never names; fixing
        # the one real citation cleared both flags, which is how the false one was
        # identified. The epithet cap cannot see this — "Savage Land" abbreviates
        # exactly ONE card, so it is not ambiguous, it is a PREFIX COLLISION.
        # Blanking suppressed names too is the load-bearing half: otherwise the
        # fragment path smuggles back a citation the full-name scan deliberately let
        # go (history, simile, negation), under a different card's name.
        # Length-preserving, like the mask above, so `pos` stays comparable.
        masked_frags = masked
        for nm in sorted(seen_full_names, key=len, reverse=True):
            masked_frags = masked_frags.replace(nm, " " * len(nm))
        frags = _shorthand_index(carddata)
        for frag, pos in _shorthand_candidates(masked_frags, frags):
            fulls = frags[frag]
            # If ANY candidate is in the deck, the citation means that card — and an
            # abbreviation contained in an in-deck name is that card's shorthand
            # either way (the Heartfire rule, extended to fragments). PLAIN substring
            # on purpose, not word-bounded: "Tishana" must suppress against in-deck
            # "Tishana's Tidebinder", and over-suppression is the safe direction here.
            if any(f in in_deck or f.split(" // ")[0] in in_deck for f in fulls):
                continue
            if any(frag in other for other in in_deck):
                continue
            if (_cites_as_history(masked, pos, len(frag))
                    and not _cites_as_arriving(masked, pos)):
                continue
            if _SIMILE_BEFORE.search(masked[max(0, pos - 6):pos]):
                continue
            # "Note Mjölnir does NOT do this" — a contrast citation explains this deck
            # by NEGATING an absent card's behavior; the negation IS the claim that
            # the card isn't here. Positional like the simile rule.
            if _NEGATION_AFTER.match(masked, pos + len(frag)):
                continue
            stale_cards.append((fulls[0] if len(fulls) == 1
                                else f"{frag} (one of: {' / '.join(fulls)})", header))
    if stale_cards:
        stale_cards = sorted(set(stale_cards))
    vec = deck_quality_vector(d)
    figure_values = _figure_lookup(vec, cards, carddata)
    own_id = str(d.get("id") or "").lower()
    # The FIGURE half sweeps the SAME two headers as the CARD half above. It read
    # `#: tier:` alone, so a figure in `#: archetype:` could contradict the live vector
    # indefinitely: deck 26a quoted "avg MV 3.05, 15 early drops" against a live 2.97 and
    # the audit reported the deck clean. G-27 has always DOCUMENTED both headers as in
    # scope — only the card scan implemented it, so the doc was true of half the function
    # (BS4-07). Same reasoning as the card half: `#: archetype:` is a claim about the
    # CURRENT list and is the header a reader trusts first, while `#: notes:` stays out
    # as a free-form build log.
    for header in ("tier", "archetype"):
        prose = (meta or {}).get(header, "") or ""
        if not prose:
            continue
        for rx, key in _RATIONALE_FIGURES:
            for m in rx.finditer(prose):
                quoted, actual = m.group(1), figure_values.get(key)
                if actual is None:
                    continue
                if key.startswith("sources_") and _FIG_SOURCE_WANT.search(
                        prose[max(0, m.start() - 24):m.start()]):
                    continue
                # A figure quoted about ANOTHER DECK is not a claim about this one. 56a's
                # block compared itself to its parent — "deck 56 core is a genuine aggro
                # deck (clock 5/7, interaction 7, avg MV 2.42)" — and both numbers flagged
                # as stale against 56a's own vector (two false positives, 2026-08-09).
                # Scoped to the figure's clause, and only an id OTHER than this deck's
                # suppresses, so a rationale citing its own number by id still audits.
                clo, chi = _clause_bounds(prose, m.start(), m.end())
                clause = prose[clo:chi]
                ids = _other_deck_ids(clause)
                if ids - {own_id}:
                    continue
                # The same rule by NAME, which is how the prose usually writes it. Deck
                # 44a's distinctness clause — "Black Sun is aggro-sacrifice with a 5/7
                # clock and card advantage 0" — is a claim about DECK 1, but names it
                # rather than saying "deck 1", so the id rule above could not see it and
                # the figure flagged against 44a's own card advantage of 3. The card scan
                # has masked roster deck names since it was written; this is the figure
                # half of the same idea (BS4-07).
                # A name that is part of THIS deck's own name is not another deck. The
                # variant convention makes that essential rather than pedantic: 26a is
                # "Iron Forge — Virulent", so its PARENT's name is a substring of its own,
                # and an exact-match exclusion suppressed 26a's genuinely stale figure —
                # the one case this whole fix exists to catch.
                own_name = (meta or {}).get("name", "").strip()
                if any(nm in clause for nm in _roster_deck_names()
                       if nm and nm not in own_name):
                    continue
                # …and a figure about the card POPULATION is not a claim about this list.
                if _POPULATION_SUBJECT_RE.search(clause):
                    continue
                # A rationale legitimately quotes PAST figures when it documents a change
                # ("took interaction 1→4", "it cited a 2.65 curve; the list is now 3.0"),
                # and flagging those makes the check cry wolf, which is how a check gets
                # ignored. Only a figure presented as the CURRENT state is worth
                # reporting. This used to reuse the CARD scan's `_cites_as_history`; see
                # `_figure_is_history` for why that was wrong and what it hid.
                if _figure_is_history(prose, m.start(), m.end()):
                    continue
                # …and the number may not be this metric at all (a percentage, a
                # "draw N" count). Shared with `note_figure_staleness`, because the
                # trap is in the PATTERNS both of them use.
                if _figure_misreads_prose(prose, m.start(), m.end()):
                    continue
                same = (abs(float(quoted) - float(actual)) < 0.005 if "." in quoted
                        else int(quoted) == int(actual))
                if not same and (key, quoted, actual) not in stale_figures:
                    stale_figures.append((key, quoted, actual))
    # The slash idiom ("13/8/10 sources") is checked as a multiset (BS8-16) — the
    # per-colour patterns above cannot see it, and it is the shape deck 78 writes.
    _src = {k[len("sources_"):]: v for k, v in figure_values.items() if k.startswith("sources_")}
    _cols = (meta or {}).get("colors") or ""
    for header in ("tier", "archetype"):
        for claim in _slash_source_claims((meta or {}).get(header, "") or "", _src, _cols):
            if claim not in stale_figures:
                stale_figures.append(claim)
    # …and the FLOOR BAND, the structural claim that is a letter rather than a number and
    # so matched none of the patterns above. Same two headers, same clause suppressions
    # as the figure loop: a floor quoted for ANOTHER deck is not a claim about this one,
    # and a documented past floor ("the floor read A before the re-derivation") is
    # history. Whitespace is collapsed first so a claim wrapped across two `#: tier:`
    # continuation lines is still one match.
    try:
        live_band = tier_band(vec)
    except Exception:
        live_band = None    # a band we cannot price is skipped, never guessed
    own_name = (meta or {}).get("name", "").strip()
    for header in ("tier", "archetype") if live_band else ():
        prose = re.sub(r"\s+", " ", (meta or {}).get(header, "") or "")
        for start, end, band in _floor_band_claims(prose, live_band):
            clo, chi = _clause_bounds(prose, start, end)
            clause = prose[clo:chi]
            if _other_deck_ids(clause) - {own_id}:
                continue
            if any(nm in clause for nm in _roster_deck_names()
                   if nm and nm not in own_name):
                continue
            claim = ("metrics floor", band, live_band)
            if claim not in stale_figures:
                stale_figures.append(claim)
    return stale_cards, stale_figures


# The past-cue family, reused CLAUSE-SCOPED by the note scan below. The shared
# `_FIGURE_PAST` constrains its cue to 24 chars before the figure, which is right for
# `#: tier:` prose (a claim, where history is the exception) and wrong for a build log
# (history-dense by construction): deck 50a's "it read avg MV 4.18 with SEVEN early
# drops and interaction 4" sits the cue ~48 chars from the figure it governs. Widening
# the shared window instead would loosen every other suppression — the code comment on
# `_figure_is_history` says so — hence a second, clause-scoped reading of the SAME cues
# rather than a looser one. It keeps the tense distinction that matters: `\bread\b`
# does not match "reads", so deck 31's live "role_tally still reads card-adv 1" is not
# swallowed by the rule that suppresses 50a's past "it read".
_FIGURE_PAST_CUE = re.compile(_FIGURE_PAST.pattern.split(r"\b[^.;]")[0] + r"\b", re.I)


def note_figure_staleness(d, vec=None, meta_cards=None):
    """[(note, key, quoted, actual)] — figures in `#~ note:` prose the live vector
    contradicts.

    `#~` notes sat outside every staleness scan. The CARD half deliberately stays out,
    on G-27's reasoning that a build log naming an ABSENT card is correct — measured at
    252 such citations across 51 decks of 537 note lines, which would bury any signal.
    A bare present-tense FIGURE is different: it is a claim about the CURRENT list
    wherever it is written, and deck 50's "this deck's whole advantage is a 3.11 curve
    with 21 early drops" is an argument that stops being true when the curve moves.

    Suppressions are the shared ones (arrow/delta, quoted spans, cross-deck ids and
    names, population subjects, percentages, draw-N) plus the clause-scoped past cue
    above. Measured on the roster the day it was written: 47 raw matches -> 9 reported,
    of which 8 were genuinely stale.

    KNOWN RESIDUAL, kept rather than papered over with a one-instance cue: a figure
    describing a HYPOTHETICAL configuration reads as a live claim. Deck 26's "the best
    curve of the three pass-3 alternatives (avg MV 3.61, early drops 11)" is the case —
    that number was true of an option, not of the deck. Report-only, so the cost is one
    line a human dismisses.
    """
    meta, cards = parse_deck_file(d["path"])
    vec = vec if vec is not None else deck_quality_vector(d)
    # Same combined lookup as the tier/archetype scan, so a colour-source claim in a
    # `#~ note:` is checked by exactly the rules that check one in `#: tier:` — the
    # deck-78 Orcrist note quoted an avg MV and the two scans must not drift apart.
    figure_values = _figure_lookup(vec, cards, load_card_data())
    own_id = str(d.get("id") or "").lower()
    own_name = (meta or {}).get("name", "").strip()
    out = []
    for e in parse_flex(d["path"]):
        note = (e.get("note") or "").strip()
        if not note:
            continue
        for rx, key in _RATIONALE_FIGURES:
            for m in rx.finditer(note):
                quoted, actual = m.group(1), figure_values.get(key)
                if actual is None:
                    continue
                if key.startswith("sources_") and _FIG_SOURCE_WANT.search(
                        note[max(0, m.start() - 24):m.start()]):
                    continue
                if _figure_is_history(note, m.start(), m.end()):
                    continue
                if _figure_misreads_prose(note, m.start(), m.end()):
                    continue
                lo, hi = _clause_bounds(note, m.start(), m.end())
                clause = note[lo:hi]
                if _other_deck_ids(clause) - {own_id}:
                    continue
                if any(nm in clause for nm in _roster_deck_names()
                       if nm and nm not in own_name):
                    continue
                if _POPULATION_SUBJECT_RE.search(clause):
                    continue
                if _FIGURE_PAST_CUE.search(clause):
                    continue
                same = (abs(float(quoted) - float(actual)) < 0.005 if "." in quoted
                        else int(quoted) == int(actual))
                if not same:
                    row = (note, key, quoted, actual)
                    if row not in out:
                        out.append(row)
        _src = {k[len("sources_"):]: v for k, v in figure_values.items()
                if k.startswith("sources_")}
        _cols = (meta or {}).get("colors") or ""
        for key, quoted, actual in _slash_source_claims(note, _src, _cols):    # BS8-16
            row = (note, key, quoted, actual)
            if row not in out:
                out.append(row)
    return out


_EXCLUSION_CUES = re.compile(
    r"\b(?:NOT included|not included|deliberately not|not run|left out|"
    r"kept out of the (?:list|deck|60)|not in the (?:list|deck|60))\b", re.I)
_EXCLUSION_PAREN = re.compile(r"\([^()]*\)")
# The claim ends at the first clause boundary. Without this, "Craterhoof is deliberately
# NOT here — Summon: Titan's third chapter is this deck's mass pump" reads the REPLACEMENT
# as the excluded card: the excluded name sits BEFORE the cue in that shape, and whatever
# follows is the explanation. Same trap as 52a's own note, which named Quag Feast as the
# card that replaced an excluded one.
_EXCLUSION_STOP = re.compile(r"[;—–.]")
_EXCLUSION_HEAD = 60


def wrong_exclusion_claims(d, carddata=None):
    """[(name, header)] — cards the prose says are NOT in the deck, that the deck RUNS.

    The mirror of `rationale_staleness`, and the case G-27 deliberately leaves out of
    that scan. `#: notes:` is exempted there because it is a build log where naming an
    ABSENT card is correct — but "Deliberately NOT included: Bringer of the Last Gift"
    is not naming an absent card, it is a false claim about the CURRENT list, and it
    survives exactly the edit that makes it false (adding the card). Deck 52a carried
    that sentence for one commit after Bringer was added.

    Scans `notes` as well as `tier`/`archetype`, since the exclusion shape is what makes
    it checkable — an exclusion claim is a claim about the current list wherever it is
    written. Report-only, like the rest of the audit."""
    carddata = carddata if carddata is not None else load_card_data()
    meta, cards = parse_deck_file(d["path"])
    in_deck = {n for _q, n, _s, _c in cards}
    in_deck |= {n.split(" // ")[0] for n in list(in_deck)}
    out = []
    for header in ("notes", "tier", "archetype"):
        prose = (meta or {}).get(header, "") or ""
        # SHAPE, not proximity, and it took three tries to get there — the measurements
        # are the reason this is written the way it is. A plain ±400-char window produced
        # TEN roster hits and every one sampled was noise; splitting the whole post-cue
        # prose on `;` produced THIRTY-SEVEN. What works is reading only the CLAUSE that
        # the cue introduces: parentheticals stripped (the reason text is where innocent
        # names live) and cut at the first boundary (the shape "X is deliberately NOT
        # here — Y does the job" names the replacement after the dash). Roster-wide this
        # form reports zero, and still catches the 52a sentence that motivated the check.
        for m in _EXCLUSION_CUES.finditer(prose):
            seg = _EXCLUSION_PAREN.sub(" ", prose[m.end():m.end() + _EXCLUSION_HEAD])
            stop = _EXCLUSION_STOP.search(seg)
            head = seg[:stop.start()] if stop else seg
            for nm in sorted(in_deck, key=len, reverse=True):
                if len(nm) < _RATIONALE_MIN_LEN and " " not in nm:
                    continue
                if nm in BASICS or nm.lower() in BASICS:
                    continue
                if nm in head:
                    out.append((nm, header))
    return sorted(set(out))


def cmd_tier(args):
    """Tier robustness (F12): show a deck's claimed tier next to the tier FLOOR its
    measurable quality vector supports, and flag an indefensible/stale letter. It
    NEVER writes the tier — grading is a human judgment that credits bombs/meta the
    metrics can't see; this only surfaces a letter ≥2 bands above what the numbers
    support (or, conversely, a deck the metrics say is under-graded)."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    meta, _cards = parse_deck_file(d["path"])
    claimed = _deck_tier(meta)
    vec = deck_quality_vector(d)
    implied = tier_band(vec)
    if getattr(args, "audit_rationale", False):
        # Same silent-drop shape as `quality --at` (broad-scan Batch G): this branch
        # returns without reading --to/--strict.
        _ign = [f for f, v in (("--to", getattr(args, "to", None)),
                               ("--strict", getattr(args, "strict", False))) if v]
        if _ign:
            eprint(f"NOTE:  --audit-rationale checks the ARGUMENT, not the letter, and "
                   f"does not combine with {', '.join(_ign)} — ignored for this run. "
                   f"Run `deck.py tier {args.id}` on its own for the band/gap view.")
        cards_stale, figs = rationale_staleness(d)
        wrong_excl = wrong_exclusion_claims(d)
        print(f"Rationale audit — deck {d['id']}: {d['name'] or d['path']}")
        if not cards_stale and not figs and not wrong_excl:
            print("  ✓ rationale is current — every card it cites is still in the deck, "
                  "every figure matches the live vector, and nothing it calls excluded "
                  "is actually in the list.")
            return 0
        for nm, hdr in cards_stale:
            print(f"  ⚠ `#: {hdr}:` argues from {nm}, which is NO LONGER in the deck.")
        for nm, hdr in wrong_excl:
            print(f"  ⚠ `#: {hdr}:` says {nm} is NOT included — but the deck RUNS it.")
        for key, quoted, actual in figs:
            print(f"  ⚠ `#: tier:` quotes {key.replace('_', ' ')} {quoted}, "
                  f"but the live vector says {actual}.")
        print("  Rewrite the prose (or re-grade) — a stale argument is how a defensible "
              "letter turns into an indefensible one. Nothing was changed.")
        return 0
    print(f"Tier — deck {d['id']}: {d['name'] or d['path']}")
    print(f"  claimed tier  : {claimed or '(untiered)'}")
    print(f"  metrics floor : {implied}   (measurable-only — blind to bombs/meta, so it under-rates)")
    print(f"  plan          : {vec.get('plan', 'midrange')}"
          + (f"  ·  clock {_clock_score(vec)}/7 (curve/threats/reach substitutes for interaction)"
             if vec.get('plan') == 'aggro' else "  (floor weights interaction + card advantage)"))
    print(f"  vector        : buildable {vec['buildable']} · uncastable {vec['uncastable']} · "
          f"interaction {vec.get('interaction_conf') or vec['interaction']} · "
          f"card-adv {vec.get('card_advantage_conf') or vec['card_advantage']} · "
          f"protection {vec.get('protection', 0)} · "
          f"avg MV {vec['avg_mv']} · central themes {vec['central_themes']}")
    # An {X} spell is priced at MV 1 (X counts as 0 off the stack), so the avg MV printed
    # just above under-reads a list that runs several. REPORT-only, like protection — a
    # new term in tier_band would silently re-grade the roster.
    _cd = load_card_data()
    _mana = load_mana()
    _xs = x_cost_cards(_cards, _cd, _mana)
    if _xs:
        print(f"  ⚠ avg MV under-reads: {len(_xs)} X-cost card(s) "
              f"({', '.join(n for n, _c in _xs[:3])}{'…' if len(_xs) > 3 else ''}) "
              "book as MV 1 because X counts as 0 — see `deck.py stats` for the list.")
    # Protection is REPORTED, never fed into tier_band (the floor formula is anchored by
    # check_tier.py). A zero here is a judgment prompt, not a band change.
    if not vec.get("protection"):
        sig = _protected(meta)
        print("  ⚠ ZERO protection (no ward/hexproof/indestructible-class effect)"
              + (f" while `#: protect:` names {len(sig)} build-around card(s)" if sig else "")
              + " — weigh this before granting a band the metrics floor allows.")
    # The floor caps at C on any uncastable stray; without a #: colors: header that
    # count is derived from the deck's own cards, so it's 0 by construction — say so
    # rather than imply a verified-clean castability (audit F16).
    if not vec.get("colors_declared"):
        print("  ⚠ castability UNVERIFIED — no `#: colors:` header, so uncastable=0 is "
              "self-derived; add a colors header for the floor's stray-cap to mean anything.")
    # F15: warn if the count may be under-read, since the floor grades on it.
    _meta2, _cards2 = parse_deck_file(d["path"])
    _unc, _under, _nodata = role_coverage_flags(_cards2, load_card_data())
    if _under:
        names = ", ".join(f"{n} ({a})" for n, a in _under[:4])
        print(f"  ⚠ count may under-read {len(_under)} card(s) — verify via `deck.py stats {d['id']}`: {names}"
              + ("…" if len(_under) > 4 else ""))
    if _nodata:
        print(f"  ⚠ {len(_nodata)} card(s) have no oracle text on file — the floor grades on a "
              f"partial count; enrich via build_pool.py ({', '.join(_nodata[:4])}"
              + ("…" if len(_nodata) > 4 else "") + ")")
    if not claimed:
        print("\n  (untiered — add a `#: tier: X — rationale` header; see the tier rubric in CLAUDE.md)")
        return 0
    gap = TIER_RANK.get(claimed, 0) - TIER_RANK.get(implied, 0)
    if gap >= 2:
        print(f"\n⚠ TIER MISMATCH: {claimed} sits {gap} bands above the metrics floor ({implied}).")
        print("  Either the letter is inflated/stale (re-grade from the CLAUDE.md rubric), or it")
        print("  genuinely rests on bombs/meta the metrics can't see — state which in the")
        print("  `#: tier:` rationale so the call is auditable.")
        return 1 if getattr(args, "strict", False) else 0
    if gap <= -1 and _argues_below_floor(meta):
        print(f"\n  ✓ deliberately conservative — {claimed} sits below the {implied} floor and "
              "the rationale argues why. Not flagged.")
    elif gap <= -1:
        print(f"\n  ↑ possibly UNDER-graded: even the (under-rating) metrics floor is {implied}. "
              "Consider re-grading up.")
    elif gap == 1:
        print(f"\n  ✓ defensible — {claimed} is one band above the floor (intangibles credit).")
    else:
        print(f"\n  ✓ consistent — {claimed} matches the metrics floor.")

    # F14 — tier-gap diagnostic: the MEASURABLE work to reach a target band's floor,
    # plus the owned (0-wildcard) on-color cards that fill the short axis. The
    # selection stays a human call (protect signature/spice — that's /tune-deck's job).
    target = getattr(args, "to", None)
    if target:
        gapinfo = tier_gap(vec, target)
        if not gapinfo:
            eprint(f"\n--to: unknown target tier {target!r} (use S/A/B/C/D)")
            return 1
        print(f"\n── Path to the {gapinfo['target']} floor ──")
        if gapinfo["met"]:
            print(f"  ✓ already meets the {gapinfo['target']} floor "
                  f"(interaction {vec['interaction']}, card-adv {vec['card_advantage']}) — "
                  "the letter is a human call from here (bombs/meta).")
            return 0
        print("  measurable gap: " + "; ".join(gapinfo["summary"]))

        # `adds` accumulates the fillers that close the gap, in the order we'll pair
        # them with cuts: owned (0-wildcard) first, then craft targets. Each entry is
        # (axis, kind, mv, name, ident, note).
        adds = []

        def _axis(role_set, add_flag, label):
            if not add_flag:
                return
            owned_f = owned_role_fillers(d, role_set, limit=6)
            craft = craft_role_fillers(d, role_set, limit=6)
            # ONE list, ordered by mana value, with ownership as an ANNOTATION. These used
            # to print as two sections — owned first, then craft — each capped at six, so a
            # better craft filler sat below six owned ones and the assembled plan below
            # reserved owned picks first. That is a build gated on ownership, and ownership
            # here is hand-maintained data that goes stale between updates. Cost still
            # prints on every row; it just no longer decides the order.
            merged = [(mv, name, ident, "owned", "owned", txt)
                      for mv, name, ident, _hit, txt in owned_f]
            merged += [(mv, name, ident, (rar[:1] or "?") + " craft", "craft",
                        (rot + " " if rot else "") + txt)
                       for _rk, mv, name, ident, rar, txt, rot in craft]
            merged.sort(key=lambda r: (r[0], r[1].lower()))
            if merged:
                print(f"\n  on-color, format-legal {label} to add "
                      f"(ranked by cost; ownership is a note, not a preference):")
                for mv, name, ident, tag, _kind, txt in merged:
                    print(f"    MV{mv:>2} {name:28} [{ident:4}] {tag:8} {txt}")
            else:
                print(f"\n  (no on-color {label} filler found)")
            adds.extend((label, kind, mv, name, ident,
                         "0 WC" if kind == "owned" else tag)
                        for mv, name, ident, tag, kind, _t in merged[:add_flag])

        _axis(_INTERACTION_ROLES, gapinfo["add_interaction"], "interaction")
        _axis({"Card advantage"}, gapinfo["add_card_advantage"], "card advantage")

        # #4 — assemble the concrete before/after tune package: pair each filler with a
        # weakest-fit cut (from the SAME cut ranking `deck.py cuts` prints, so the two
        # can't disagree), then project the resulting quality vector and floor. It's a
        # STARTING plan, not an auto-apply: the card selection stays a human call
        # (protect signature/spice — that's /tune-deck), so it prints, never writes.
        cut_rows, _c, _pp, _di = rank_cut_candidates(d)
        # Don't propose cutting a card we're also adding (a filler already in the 60
        # would be surfaced as a cut otherwise).
        add_names = {a[3].lower() for a in adds}
        cut_pool = [r for r in cut_rows if r[1].lower() not in add_names]
        pairs = pair_adds_with_cuts(adds, cut_pool)
        if pairs:
            print(f"\n── Assembled tune plan → {gapinfo['target']} (starting point; grade & "
                  "protect signature/spice) ──")
            int_gain = ca_gain = 0
            for (axis, kind, mv, name, ident), cut in ((a[:5], c) for a, c in pairs):
                cut_name, cut_mv, cut_roles, cut_text, cut_is_int = (
                    cut[1], cut[2], cut[3], cut[7], cut[8])
                cut_ca = "Card advantage" in cut_roles
                # A mana source: the Ramp/fixing role, OR a dork whose "add one mana"
                # phrasing (a flavor-keyword ability) the role classifier misses.
                cut_ramp = "Ramp / fixing" in cut_roles or _produces_mana(cut_text)
                # Net axis change: +1 for the add's axis, −1 if the cut fed that axis.
                if axis == "interaction":
                    int_gain += 1
                else:
                    ca_gain += 1
                if cut_is_int:
                    int_gain -= 1
                if cut_ca:
                    ca_gain -= 1
                mvs = f"MV{mv:>2}" if isinstance(mv, int) else "MV ?"
                cmvs = f"MV{cut_mv:>2}" if isinstance(cut_mv, int) else "MV ?"
                warn = ""
                if cut_is_int:
                    warn = "  ⚠ cut feeds interaction — pick another cut"
                elif cut_ca:
                    warn = "  ⚠ cut feeds card advantage — pick another cut"
                elif cut_ramp:
                    warn = "  ⚠ cut is a ramp/fixing source — losing it may hurt the manabase"
                print(f"  − {cut_name[:28]:28} {cmvs}   →   + {name[:26]:26} {mvs} "
                      f"[{ident:4}] ({axis}, {kind}){warn}")
            if len(adds) > len(cut_pool):
                print(f"  … {len(adds) - len(cut_pool)} more add(s) needed but the cut list is "
                      "exhausted — the deck may already be tight; loosen a #: protect: card.")
            # Projected floor: apply the net axis changes to the vector, re-band.
            proj = dict(vec)
            proj["interaction"] = max(0, vec["interaction"] + int_gain)
            proj["card_advantage"] = max(0, vec["card_advantage"] + ca_gain)
            proj_band = tier_band(proj)
            print(f"\n  projected: interaction {vec['interaction']}→{proj['interaction']}, "
                  f"card-adv {vec['card_advantage']}→{proj['card_advantage']}  "
                  f"⇒ metrics floor {implied}→{proj_band}"
                  + (f"  ✓ meets {gapinfo['target']} floor" if TIER_RANK.get(proj_band, 0)
                     >= TIER_RANK.get(gapinfo['target'], 9) else
                     f"  (still short of {gapinfo['target']} — more adds or a heavier tune)"))
            print("  Preview any line with `deck.py swap %s --cut <A> --add <B>` "
                  "(shows full text of both)." % d["id"])
        else:
            print("\n  → make room with `deck.py cuts %s` (grade cuts from full text); the card"
                  " SELECTION\n    is a judgment call — protect signature/spice (that's /tune-deck)."
                  % d["id"])
    return 0


def deck_git_history(path, limit=None):
    """[{hash, date, subject}] for a deck file, newest first, from `git log --follow`.
    The commit messages ARE the deck's changelog (they state the thematic + technical
    why). Empty list if git is unavailable / the file is untracked — the CLI and the
    dashboard 'recently edited' panel both read THIS one helper so they can't drift."""
    import subprocess
    rel = os.path.relpath(path, REPO_ROOT)
    args = ["git", "log", "--follow", "--date=short", "--format=%h\t%ad\t%s"]
    if limit:
        args.append(f"-n{int(limit)}")
    args += ["--", rel]
    try:
        r = subprocess.run(args, capture_output=True, text=True, cwd=REPO_ROOT)
    except Exception:
        return []
    if r.returncode != 0:
        return []
    out = []
    for ln in r.stdout.splitlines():
        if not ln.strip():
            continue
        parts = ln.split("\t", 2)
        if len(parts) == 3:
            out.append({"hash": parts[0], "date": parts[1], "subject": parts[2]})
    return out


def deck_recent_card_delta(path):
    """Card-level diff of the MOST RECENT edit to a deck file: {added, removed, prev}
    where added/removed are [(display_name, qty)] between the deck's current list and
    its previous committed version (printing- and case-fungible via `_multiset`). None
    when there's no prior version (a brand-new deck) or git is unavailable — so the
    'recently edited' panel can show WHAT changed, not just when."""
    rel = os.path.relpath(path, REPO_ROOT)
    hashes = _deck_commit_hashes(rel)
    if len(hashes) < 2:
        return None  # no prior committed version to diff against
    prev_ms = _deck_ms_at_ref(rel, hashes[1])
    if prev_ms is None:
        return None
    added, removed = _ms_delta(prev_ms, _multiset(parse_deck_file(path)[1]))
    return {"added": added, "removed": removed, "prev": hashes[1][:9]}


def _deck_commit_hashes(rel, before=None):
    """Full commit hashes touching a deck file, newest first; with `before` (an ISO
    date) only those at/before it. [] on any git failure. Shared by the card-delta
    helpers so the git plumbing lives in one place."""
    import subprocess
    args = ["git", "log", "--follow", "--format=%H"]
    if before:
        args.append(f"--before={before}")
    args += ["--", rel]
    try:
        r = subprocess.run(args, capture_output=True, text=True, cwd=REPO_ROOT)
    except Exception:
        return []
    return [h for h in r.stdout.split() if h] if r.returncode == 0 else []


def _deck_ms_at_ref(rel, ref):
    """The card multiset of a deck file AS OF a git ref, or None on failure."""
    import subprocess
    import tempfile
    r = subprocess.run(["git", "show", f"{ref}:{rel}"], capture_output=True, text=True,
                       cwd=REPO_ROOT)
    if r.returncode != 0:
        return None
    fd, tmp = tempfile.mkstemp(suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(r.stdout)
        return _multiset(parse_deck_file(tmp)[1])
    except Exception:
        return None
    finally:
        os.remove(tmp)


def _ms_delta(prev_ms, cur_ms):
    """(added, removed) as sorted [(display, qty)] between two card multisets."""
    added = sorted((disp, q - prev_ms.get(nl, (disp, 0))[1])
                   for nl, (disp, q) in cur_ms.items() if q > prev_ms.get(nl, (disp, 0))[1])
    removed = sorted((disp, q - cur_ms.get(nl, (disp, 0))[1])
                     for nl, (disp, q) in prev_ms.items() if q > cur_ms.get(nl, (disp, 0))[1])
    return added, removed


def deck_card_delta_since(path, since):
    """Cumulative card-level delta between a deck's current list and its state AS OF an
    ISO date `since` — {added, removed, base, base_date} or None when there's no
    committed version at/before that date or git is unavailable. 'What have I NET-changed
    since date X (and still need to push to Arena)', vs `deck_recent_card_delta`'s single
    most-recent edit. Printing/case-fungible via `_multiset`."""
    import subprocess
    rel = os.path.relpath(path, REPO_ROOT)
    hashes = _deck_commit_hashes(rel, before=since)
    if not hashes:
        return None  # deck had no committed version at/before that date
    base = hashes[0]
    base_ms = _deck_ms_at_ref(rel, base)
    if base_ms is None:
        return None
    added, removed = _ms_delta(base_ms, _multiset(parse_deck_file(path)[1]))
    bd = subprocess.run(["git", "show", "-s", "--format=%ad", "--date=short", base],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    return {"added": added, "removed": removed, "base": base[:9],
            "base_date": bd.stdout.strip() if bd.returncode == 0 else ""}


def cmd_history(args):
    """Show a deck file's git change history — the accurate, complete record of how
    the deck evolved (each commit message states the thematic + technical why). This
    is the deck's changelog; it lives in git rather than in-file so it can't get
    unwieldy or drift. Pair with `deck.py quality <id> --at <hash>` to compare a past
    version's measurable vector (interaction / curve / themes) against now."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    rel = os.path.relpath(d["path"], REPO_ROOT)
    since = getattr(args, "since", None)
    hist = deck_git_history(d["path"])
    if since:
        # git's --date=short is zero-padded ISO, so a STRING compare only works for a
        # zero-padded ISO needle: `--since 2026-8-1` silently matched nothing
        # ("2026-08-07" >= "2026-8-1" is False) while the card-delta half below, which
        # hands the same string to `git log --before=`, happily parsed it — one command
        # printing "0 commit(s)" above a populated delta (broad-scan Batch G).
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", since.strip()):
            eprint(f"--since must be a zero-padded ISO date (YYYY-MM-DD); got "
                   f"{since!r}. Try {since.strip()[:4]}-08-01.")
            return 2
        hist = [h for h in hist if h["date"] >= since]
    scope = f" since {since}" if since else ""
    print(f"History — deck {d['id']}: {d['name'] or rel}{scope}  ({len(hist)} commit(s))")
    for h in hist:
        print(f"  {h['hash']}  {h['date']}  {h['subject']}")
    if since:
        # The cumulative card-level net change since that date — 'what do I still need to
        # push to Arena', printing/case-fungible.
        delta = deck_card_delta_since(d["path"], since)
        if delta and (delta["added"] or delta["removed"]):
            print(f"\n  Net card change since {delta['base_date'] or since} "
                  f"(base {delta['base']}):")
            for nm, q in delta["added"]:
                print(f"    + {q}× {nm}")
            for nm, q in delta["removed"]:
                print(f"    − {q}× {nm}")
        elif delta:
            print(f"\n  No net card change since {delta['base_date'] or since} "
                  "(edits may have cancelled out, or only metadata changed).")
    if hist:
        print(f"\n  full text of any version:   git show <hash>:{rel}"
              f"\n  compare a version's metrics: deck.py quality {d['id']} --at <hash>")
    return 0


def cmd_preflight(args):
    """One-call verification for the skills (F05): construction legality + owned/
    buildable + castability + repo integrity, as a structured PASS/FAIL block.
    Orchestrates the existing checks (legal/check_all) rather than re-implementing
    them. Exits non-zero only on a HARD failure (illegal deck or broken integrity);
    unowned craft targets / hybrid strays are WARN, since WIP decks are legitimate."""
    import io
    import contextlib
    import subprocess
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    dmeta, cards = parse_deck_file(d["path"])

    # Construction legality (size, copies, format) — reuse cmd_legal, captured.
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        legal_rc = cmd_legal(argparse.Namespace(id=args.id, fmt=None))

    # Owned / buildable.
    _, _, qty = load_collection()
    missing = short = 0
    # Per aggregated NAME (BS2-22), matching cmd_check's explicit comment: a deck may
    # list one card on two printing lines, and per-line comparison let preflight say
    # "PASS — fully owned" where `check` said short (2+2 lines against 3 owned). The
    # counts are also per-CARD now, so a two-line missing card is one craft target.
    need = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        need[n] = need.get(n, 0) + q
    for n, req in need.items():
        have, inlib = owned(qty, n)
        if not inlib:
            missing += 1
        elif have < req:
            short += 1

    # Castability.
    mana = load_mana()
    carddata = load_card_data()
    declared = _declared_colors(dmeta) or _deck_castable_colors(dmeta, cards, mana)
    uncast, off_ident, _, intended = _castability(
        cards, declared, mana, carddata, _uncastable_ok(dmeta))

    # Repo integrity — the deterministic gate, run out-of-process for a clean signal.
    integ = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "check_all.py"), "--quiet"],
        capture_output=True, text=True)
    integ_ok = integ.returncode == 0

    def mark(ok):
        return "PASS" if ok else "FAIL"
    legal_ok = legal_rc == 0
    print(f"Preflight — deck {d['id']}: {d['name'] or d['path']}")
    print(f"  legal (construction) : {mark(legal_ok)}")
    print(f"  owned (buildable)    : "
          + ("PASS — fully owned" if missing == 0 and short == 0
             else f"WARN — {missing} craft target(s), {short} short (WIP-ok)"))
    print(f"  castability          : "
          + ("PASS" if not uncast else f"FAIL — {len(uncast)} uncastable")
          + (f" (+{len(intended)} intended, exempt)" if intended else "")
          + (f" (+{len(off_ident)} hybrid stray, ok)" if off_ident else ""))
    print(f"  integrity (check_all): {mark(integ_ok)}")
    hard = (not legal_ok) or bool(uncast) or (not integ_ok)
    print(f"Verdict: {'BLOCKED' if hard else 'READY'}")
    return 1 if hard else 0


              # A gate names a RESOURCE the card needs; the count is how much of it the
              # deck actually holds. Each entry: (regex, label, kind). `kind` selects the
              # counter below — keeping the two apart is what lets a new gate be one line.
_SCREEN_KEY_SATURATED = 0.40   # KEY on this share of a pile carries no information
_TARGET_WORD_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
_TARGET_FAT_MV = 5      # at/above this, reanimating a card gains real mana
_TARGET_GATES = [
    (re.compile(r"mana value (\d+) or less", re.I), "creature MV ≤{0} in the yard", "mv"),
    (re.compile(r"total mana value (\d+) or less", re.I), "cards totalling MV ≤{0}", "mv"),
    (re.compile(r"sacrifice (?:an artifact or creature|a creature or artifact)", re.I),
     "artifacts + creatures to sacrifice", "sac_ac"),
    (re.compile(r"sacrifice (?:a|another) creature", re.I), "creatures to sacrifice", "sac_c"),
    # Lookahead, or this double-fires on "sacrifice an artifact or creature" and reports
    # the artifact-only count next to the correct combined one.
    (re.compile(r"sacrifice an artifact\b(?! or creature)", re.I),
     "artifacts to sacrifice", "sac_a"),
    (re.compile(r"(?:return|put) target creature card", re.I), "creature cards to return", "creat"),
    # WORD-numbers, because Magic writes "eight or more permanent cards", not "8 or more".
    # The digit-only form of this pattern never matched a single card — it was written
    # against Starving Revenant's Descend 8 and could not see it. Nothing noticed because
    # a gate that silently reports nothing looks exactly like a deck with no gates.
    (re.compile(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten) or more "
                r"permanent cards in your graveyard", re.I),
     "permanent cards (needs {0})", "perm"),
    # CARD-TYPE thresholds in the graveyard. Found by running `targets` against deck 54,
    # a Lesson deck built entirely on them, and getting "no gated effects detected" — the
    # table knew MV caps, sacrifice costs and the permanent-count threshold, and nothing
    # about "three or more Lesson cards in your graveyard" or "the number of Lesson cards
    # in your graveyard". Those are the same question (does the list hold the resource?)
    # in the shape a TYPE-matters deck writes it. `permanent` is excluded because the rule
    # above already owns it and would otherwise report the same gate twice.
    (re.compile(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten) or more "
                r"(?!permanent)([A-Za-z]+) cards? in (?:your|all) graveyards?", re.I),
     "{1} cards in the yard (needs {0})", "gy_type"),
    (re.compile(r"number of (?!permanent)([A-Za-z]+) cards? in (?:your|all) graveyards?", re.I),
     "{0} cards in the yard", "gy_type"),
    # Both spellings of the copula: Dragonfly Swarm writes "if there's a Lesson card in
    # your graveyard" and Dawnhand Eulogist writes "if there is an Elf card in your
    # graveyard" — the contraction-only form saw the first and was BLIND to the second,
    # so deck 77 shipped Eulogist with a fully dead Elf rider (zero Elves) and `targets`
    # reported nothing (DD-3; the G-67 phrasing-whitelist shape).
    (re.compile(r"there(?:'s| is) an? (?!permanent)([A-Za-z]+) card in (?:your|a) graveyard", re.I),
     "{0} cards in the yard (needs 1)", "gy_type"),
    # LIBRARY SEARCHES — a tutor is worth exactly the number of things it can FIND in
    # THIS deck, and that count is invisible to every model here: each grades the search
    # card's own text, where "search your library for two basic Forests" reads as ramp.
    # Deck 76 ran ZERO basics while TWO cards searched for them (Bloomvine Regent's Omen
    # half and Encroaching Dragonstorm) — found by the user IN PLAY, by no gate, and the
    # second had been ADDED the day before on the reasoning that a Leyline of the
    # Guildpact would upgrade the fetched basics (its basic-land-type clause reads lands
    # you CONTROL, never lands in your library). A dead tutor is the purest form of the
    # G-61 failure: a card whose value is a number in the LIST, not in its own text.
    #
    # NARROW BY CONSTRUCTION, per the saturation rule this table already states: fire
    # only where the resource can genuinely be SHORT. An unconditional "search your
    # library for a card" (Lively Dirge, Servant of the Stinger, Hour of Victory) is
    # always satisfiable and never fires; so are the broad "creature card" / "land card"
    # / "nonland permanent card" searches, which in a 60-card deck report "you have a
    # deck" — the same non-signal the discard rule below was deleted for.
    (re.compile(r"search your library for (?:up to \w+ |a |an |two |three |that many |X )?"
                r"basic (Forest|Island|Swamp|Mountain|Plains) cards?", re.I),
     "basic {0} cards in the deck", "basic_named"),
    (re.compile(r"search your library for (?:up to \w+ |a |an |two |three |that many |X )?"
                r"basic land cards?", re.I),
     "basic lands in the deck", "basic_any"),
    # A named SUBTYPE (capitalised, so "a card" and "an artifact card" cannot match).
    # Land types count every land carrying the subtype, not just basics — a shock IS an
    # Island card — which is why this reads the TYPE LINE rather than the name.
    # Case-INSENSITIVE with an explicit exclusion list, not a capital-letter test: the
    # `[A-Z]` guard worked at runtime but `check_patterns` proves every gate against the
    # LOWERCASED corpus, where it could never match — a pattern that is dead to its own
    # gate is dead (the hard failure that caught this). The exclusions are the nouns that
    # would saturate: an unconditional "search your library for a card", and the
    # type-wide searches (creature / land / artifact / permanent) that in a 60-card deck
    # report "you have a deck".
    (re.compile(r"search your library for (?:up to \w+ |a |an |two |three )?"
                # `cards?` (plural — "search for two CARDS" read "cards" as a type), the
                # colour words and the legendary/token adjectives (BS8-15): each printed a
                # false "✗ NOTHING" (Behold the Beyond, Mausoleum Secrets, Unmarked Grave).
                r"(?!cards?\b|creature|land|artifact|permanent|nonland|instant|sorcery|"
                r"enchantment|planeswalker|colorless|basic|white|blue|black|red|green|"
                r"monocolored|multicolored|legendary|nonlegendary|nontoken|historic|"
                r"two\b|three\b|four\b|any\b|that\b)"
                r"([A-Za-z]{3,}) cards?", re.I),
     "{0} cards in the deck", "lib_type"),

    # NO generic "cards to discard" rule. It was written, and it reported 35 for every
    # discard outlet in a 60-card deck — i.e. "you have a hand", which is true of every
    # deck and decides nothing. Same saturation failure this file already documents for
    # `suggest`'s Decks column and `cuts`' protect boost: a signal that fires on
    # everything is not a signal. A gate earns a row only when the resource can be SHORT.
]


def unmet_gate_note(cand_name, cards, carddata, mana):
    """``'⚠ gate: <label> — 0 in this deck'`` if adding `cand_name` would bring a GATE
    this deck cannot satisfy, else ``''``.

    `target_counts` already answers "does this deck hold what this card's text asks
    for" — but only for cards ALREADY in the list. Nothing asked it about a card being
    RECOMMENDED, so `redundancy`'s virtual-copy planner proposed Party Dude (draws only
    when an OPPONENT's artifact dies) and Agent Maria Hill (needs a teamwork cost the
    deck has none of) as card-advantage copies for deck 6 — two of four picks, each
    drawing exactly zero. A working primitive one caller does not reach (G-40).

    Report-only, and inherits every limit of `target_counts`: a heuristic over card
    text, so read the card, not the flag."""
    cd = carddata.get((cand_name or "").lower())
    if not cd:
        return ""
    probe = list(cards) + [(1, cand_name, "", "")]
    try:
        rows = target_counts(probe, carddata, mana)
    except Exception:
        return ""
    for card, label, count, need in rows:
        if card != cand_name:
            continue
        if count == 0:
            return f"⚠ gate: {label} — 0 in this deck"
    return ""


def target_counts(cards, carddata, mana):
    """[(card, gate_label, count, need)] — for every card whose text names a GATE, how
    many cards in THIS deck satisfy it.

    The question no command answered. Deck 52's concept pile held 24 ways to return a
    creature against 8 creatures worth returning, and that number came from a
    hand-written script — `engines` grades enabler↔payoff by synergy TAG, which is a
    different question, and every scoring model here reads a card in ISOLATION. G-61
    states the discipline in prose ("state the count, then decide") with an incident list
    of four dismissals that were overturned, precisely because nothing automates it.

    Counts EXCLUDE the card itself (a sacrifice outlet is not its own fodder) and
    exclude lands unless the gate is about lands. `need` is the number the text demands
    when it states one (descend 8), else None. Report-only, and a heuristic on card
    text like every model here — read the list, don't just read the number."""
    pool = []
    for q, n, _s, _c in cards:
        nl = n.lower()
        cd = carddata.get(nl) or carddata.get(nl.split(" // ")[0]) or {}
        entry = mana.get(nl) or mana.get(nl.split(" // ")[0])
        mv = mana_value(front_face_cost(entry[0])) if entry and entry[0] else None
        pool.append({"n": n, "q": q, "type": (cd.get("type") or "").lower(),
                     "text": cd.get("text") or "", "mv": mv})
    out, seen = [], set()
    for c in pool:
        # Lands are skipped as GATE SOURCES (a sacrifice outlet is not its own fodder,
        # and land text would clutter every other row) — with one exception, found by
        # this module's own test: the fetch-lands are exactly where library searches
        # live (Evolving Wilds, Terramorphic Expanse, Hobbit Hole all search for a basic
        # land), so a land whose text searches your library would otherwise be the one
        # dead tutor this gate structurally could not see.
        is_land = "land" in c["type"] and "creature" not in c["type"]
        if c["n"] in seen or (is_land and "search your library" not in c["text"].lower()):
            continue
        seen.add(c["n"])
        for rx, label, kind in _TARGET_GATES:
            m = rx.search(c["text"])
            if not m:
                continue
            groups = [g for g in (m.groups() or ()) if g is not None]
            num = None
            if groups:
                g0 = groups[0].lower()
                num = int(g0) if g0.isdigit() else _TARGET_WORD_NUM.get(g0)
            others = [o for o in pool if o["n"] != c["n"]]
            if kind == "mv":
                hits = [o for o in others if "creature" in o["type"]
                        and o["mv"] is not None and o["mv"] <= num]
            elif kind == "sac_ac":
                hits = [o for o in others
                        if "creature" in o["type"] or "artifact" in o["type"]]
            elif kind == "sac_c":
                hits = [o for o in others if "creature" in o["type"]]
            elif kind == "sac_a":
                hits = [o for o in others if "artifact" in o["type"]]
            elif kind == "creat":
                hits = [o for o in others if "creature" in o["type"]]
                # The count that actually decided something on deck 52: not "how many
                # creatures" (nearly all of them) but how many are BIG enough that
                # cheating them in gains you mana. 24 ways to return against 8 worth
                # returning is the shape of an over-built reanimation package.
                fat = sum(o["q"] for o in hits
                          if o["mv"] is not None and o["mv"] >= _TARGET_FAT_MV)
                out.append((c["n"], f"creature cards to return ({fat} at MV{_TARGET_FAT_MV}+)",
                            sum(o["q"] for o in hits), None))
                continue
            elif kind == "perm":
                hits = [o for o in others if not {"instant", "sorcery"} & set(o["type"].split())]
            elif kind == "basic_any":
                hits = [o for o in others if o["n"].lower().replace("snow-covered ", "") in BASICS]
            elif kind == "basic_named":
                want = groups[-1].lower()
                hits = [o for o in others
                        if o["n"].lower().replace("snow-covered ", "") == want]
            elif kind == "lib_type":
                # TYPE LINE, not name: "an Island card" is satisfied by any land with the
                # Island subtype (a shock, a triland), not only by the basic.
                want = groups[-1].lower()
                hits = [o for o in others if want in o["type"].lower()]
            elif kind == "gy_type":
                # The captured word is a TYPE or SUBTYPE ("Lesson", "creature", "artifact"),
                # so match the type LINE. Case-insensitive: Magic capitalizes a real subtype
                # but lower-cases the generic nouns, and both spellings appear in gate text.
                want = groups[-1].lower()
                hits = [o for o in others if want in o["type"].lower()]
            else:
                hits = [o for o in others if "land" not in o["type"]]
            # Normalise a word-number in the label ("needs three" -> "needs 3") so the
            # column reads uniformly whichever spelling the card used.
            disp_groups = list(groups)
            if disp_groups and num is not None and not disp_groups[0].isdigit():
                disp_groups[0] = str(num)
            try:
                shown = label.format(*disp_groups) if disp_groups else label
            except (IndexError, KeyError):
                shown = label
            out.append((c["n"], shown, sum(o["q"] for o in hits),
                        num if kind in ("perm", "gy_type") else None))
    return out


# ── STATE gates: conditions on the GAME STATE, not on cards in the deck ─────────────
#
# `_TARGET_GATES` above answers one question: "does this deck CONTAIN N cards of shape
# X". Every one of its 13 entries counts cards in the list. That leaves a whole second
# family unanswered — a card gated on a STATE the deck has to reach ("if you've drawn
# two or more cards this turn", "unless there are seven or more cards in exile") — and
# both of this session's misreads were in it, one in each direction:
#
#   Ketramose, the New Dawn  — "can't attack or block unless there are seven or more
#     cards in exile" in a deck with ONE repeatable exile effect. A near-blank body,
#     reported by nothing.
#   Lake-town Toymaker — "if you've drawn two or more cards this turn" in a deck whose
#     entire second engine is drawing your second card every turn. An UNCONDITIONAL
#     repeatable pump, and it was nearly cut as a conditional one: `cuts` scored it fit
#     17 / power 2 / uniqueness 0 / NO detected role.
#
# So this table reports BOTH ENDS, which is the point. Every gate model here is
# one-sided — it asks whether a gate is DEAD and never whether a gate is FREE — and a
# free gate raises a card's grade exactly as much as a dead one lowers it. `✓ free` is
# the half that had no tool.
#
# The proxy for "can the deck reach this state" is a COUNT of the sources that produce
# it, and wherever a role already measures that, the proxy is `role_tally` — the
# canonical counter — so these numbers cannot drift from the ones `stats` prints.
#
# Thresholds are MEASURED, not chosen: see `tests/test_deck.py` and the roster sweep in
# the commit that added this. A band that fires on nearly every deck is a non-signal
# (the G-07 saturation lesson), so a family that saturated was dropped rather than
# shipped with a threshold tuned to hide it — `descended` went that way at 11 pool cards
# and ~100% satisfaction, and "unless you control a creature" was never written.
_STATE_GATES = [
    (re.compile(r"you'?ve drawn (?:your )?(?:a |two|three|second)"
                r"(?:\w+)? ?(?:or more )?cards? this turn", re.I),
     "draws per turn (needs 2+)", "draw"),
    (re.compile(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten) or more "
                r"cards in exile", re.I),
     "exile sources (needs {0} cards)", "exile"),
]

# FOUR MORE FAMILIES WERE BUILT, MEASURED AND DROPPED, and the measurements are the
# reason this table is short. A gate earns a row only if a real deck can FAIL it; one
# whose every roster instance reads the same is a non-signal, and tuning its threshold
# until it varies is manufacturing a signal rather than finding one (the G-07 saturation
# lesson, which cost `suggest`'s Decks column and the `review` audit flag before it).
#   • lifegain   ("if you gained life this turn") — 10 roster instances, counts 10..18,
#     never once below the band. A card gated on having gained life is only ever played
#     in a lifegain deck, so the gate has no failure mode.
#   • artifacts  ("you control three or more artifacts") — 9 instances, counts 8..9
#     against a stated need of 3. Same structural reason.
#   • drain      ("an opponent lost life this turn") — 1 instance. Not saturated;
#     simply no evidence either way, and a band guessed off n=1 is a guess.
#   • delirium   ("four or more card types among cards in your graveyard") — 7
#     instances, counts 5..6, always over. This one is the instructive failure: it is
#     not merely saturated, the PROXY MEASURES THE WRONG THING. Delirium asks about
#     types in the GRAVEYARD, which depends on self-mill and discard; counting types in
#     the DECK is a weak upper bound that any 60-card list clears by construction
#     (creature + instant + sorcery + land is already four). Fixing it means modelling
#     yard-fill, which is a different piece of work.
# `descended` was never written: 11 pool cards and a condition nearly every deck meets.

# A gate with no stated number is graded against a band; one that states its own number
# (exile) self-calibrates and needs none. Bands measured across the 116-deck roster.
_STATE_BANDS = {           # kind: (thin_at_or_below, free_at_or_above)
    "draw": (2, 8),
}


def _state_axis_counts(cards, carddata, mana):
    """The per-deck counts the state gates are graded against. `role_tally` is reused
    wherever a role already measures the axis, so a state gate and `stats` can never
    report different numbers for the same question."""
    tally = role_tally(cards, carddata)
    exile = 0
    for q, n, _s, _c in cards:
        if n.lower() in BASICS:
            continue
        cd = carddata.get(n.lower()) or carddata.get(n.lower().split(" // ")[0]) or {}
        # An exile SOURCE here is anything that puts a card into the exile zone, because
        # the gate this feeds ("seven or more cards in exile") counts the ZONE and does
        # not care who filled it or from where. That is deliberately broader than
        # Ketramose's own DRAW trigger, which fires only on exile from a graveyard or
        # the battlefield — the two are different questions about the same card, and
        # conflating them is what made the deck 43 hand-count hard to reproduce.
        text = (cd.get("text") or "").lower()
        if re.search(r"exile (?:it|them|that card|target|up to|all|each)|exile this", text):
            exile += q
    return {"draw": tally.get("Card advantage", 0), "exile": exile}


def state_gate_counts(cards, carddata, mana):
    """[(card, label, count, need, verdict)] — for each card gated on a GAME STATE, the
    deck's count on the axis that produces it, and whether the gate is dead, thin or
    free.

    Report-only and heuristic, like every model here. `verdict` is one of "dead",
    "thin", "ok", "free". Read the list, not the number: a free gate says the CONDITION
    is cheap, never that the card is good, and a dead one says the same in reverse."""
    axes = _state_axis_counts(cards, carddata, mana)
    out, seen = [], set()
    for q, n, _s, _c in cards:
        if n in seen or n.lower() in BASICS:
            continue
        seen.add(n)
        cd = carddata.get(n.lower()) or carddata.get(n.lower().split(" // ")[0]) or {}
        text = cd.get("text") or ""
        for rx, label, kind in _STATE_GATES:
            m = rx.search(text)
            if not m:
                continue
            groups = [g for g in (m.groups() or ()) if g is not None]
            need = None
            if groups:
                g0 = groups[0].lower()
                need = int(g0) if g0.isdigit() else _TARGET_WORD_NUM.get(g0)
            count = axes[kind]
            if need is not None:
                verdict = "dead" if count == 0 else ("thin" if count < need else "ok")
            else:
                low, high = _STATE_BANDS[kind]
                verdict = ("dead" if count == 0 else "thin" if count <= low
                           else "free" if count >= high else "ok")
            disp = list(groups)
            if disp and need is not None and not disp[0].isdigit():
                disp[0] = str(need)
            try:
                shown = label.format(*disp) if disp else label
            except (IndexError, KeyError):
                shown = label
            out.append((n, shown, count, need, verdict))
    return out


def dead_library_searches(cards, carddata, mana):
    """[(card, gate_label)] for library SEARCHES in this deck that can find NOTHING —
    the deck 76 bug class (G-61).

    Report-only and deliberately ZERO-only: a thin count is an editorial judgement, an
    empty one is a dead line of text. Read it as a claim about the SEARCH, not the CARD:
    the first roster run turned up Hobbit Hole in decks 50a/69a, where its basic-land
    fetch works fine and only the Halflingcycling rider whiffs, and The Masters of Evil
    in 20a/20b, which is still a Villain anthem with a dead tutor ability."""
    out = []
    for name, label, count, _need in target_counts(cards, carddata, mana):
        if count == 0 and "in the deck" in label:
            out.append((name, label))
    return out


def cmd_targets(args):
    """Does this deck contain TARGETS for its own effects? Counts, per gated card, how
    many cards in the list satisfy the gate its text names."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    _meta, cards = parse_deck_file(d["path"])
    rows = target_counts(cards, load_card_data(), load_mana())
    print(f"Deck {d['id']}: {d['name'] or d['path']} — targets for its own effects")
    if not rows:
        print("  No gated effects detected (no MV cap, sacrifice cost or count threshold "
              "in this list's text).")
        _print_state_gates(cards)
        return 0
    print(f"  {'Card':32} {'What its text needs':42} {'in deck':>7}")
    print("  " + "-" * 84)
    thin = 0
    for name, label, count, need in sorted(rows, key=lambda r: (r[2], r[0])):
        flag = ""
        if count == 0:
            flag = "  ✗ NOTHING"
            thin += 1
        elif need is not None and count < need:
            flag = f"  ⚠ short of {need}"
            thin += 1
        elif count <= 3:
            flag = "  ⚠ thin"
            thin += 1
        print(f"  {name[:32]:32} {label[:42]:42} {count:>7}{flag}")
    print(f"\n  {len(rows)} gated effect(s); {thin} thin or unmet. A gate with nothing "
          "behind it is a dead card, and a card graded in isolation cannot show you that "
          "(G-61). Counts exclude the card itself; read the list, not just the number.")
    _print_state_gates(cards)
    return 0


_STATE_FLAG = {"dead": "  ✗ CANNOT turn on", "thin": "  ⚠ thin",
               "free": "  ✓ free (deck always meets it)", "ok": ""}


def _print_state_gates(cards):
    """The second half of the targets report: gates on GAME STATE rather than on cards
    in the list. Prints both ends — a gate the deck cannot reach AND one it meets for
    free — because a free condition is not a condition, and reading one as a drawback is
    what nearly cut Lake-town Toymaker out of deck 43."""
    rows = state_gate_counts(cards, load_card_data(), load_mana())
    if not rows:
        return
    order = {"dead": 0, "thin": 1, "ok": 2, "free": 3}
    print(f"\n  {'Card':32} {'State its text needs':42} {'in deck':>7}")
    print("  " + "-" * 84)
    for name, label, count, _need, verdict in sorted(rows, key=lambda r: (order[r[4]], r[0])):
        print(f"  {name[:32]:32} {label[:42]:42} {count:>7}{_STATE_FLAG[verdict]}")
    nfree = sum(1 for r in rows if r[4] == "free")
    nbad = sum(1 for r in rows if r[4] in ("dead", "thin"))
    print(f"\n  {len(rows)} STATE gate(s): {nbad} the deck struggles to meet, {nfree} it "
          "meets for free. The free ones are the point — every other model here grades a "
          "gated card as if the gate were a cost, and in the deck built to satisfy it it "
          "is not one. Proxy counts come from `role_tally`, the same counter `stats` "
          "prints. Report-only; read the card.")


def cmd_engines(args):
    """Engine analysis: for each two-sided engine theme the deck is built on, show its
    ENABLERS (feed the engine) vs PAYOFFS (reward it) and flag a lopsided engine —
    payoffs with no enablers, or enablers with no reward — the flaw a bag-of-tags model
    can't see. Heuristic + text-based; prints the card lists so you grade the balance."""
    d = find_deck(args.id)
    if not d:
        eprint(f"No deck with id {args.id!r}. Try: deck.py list")
        return 1
    meta, cards = parse_deck_file(d["path"])
    cardmeta = load_card_meta()
    carddata = load_card_data()
    theme_w = {}
    for q, n, s, c in cards:
        if n.lower() in BASICS:
            continue
        m = cardmeta.get(n.lower())
        if m:
            for t in m["synergies"]:
                theme_w[t] = theme_w.get(t, 0) + q
    central = _central_themes(theme_w)
    signature = _signature_themes(meta, cards, cardmeta)
    bal = engine_balance(cards, carddata, central, signature, weights=theme_w)

    print(f"Deck {d['id']}: {d['name'] or d['path']} — engine analysis (enabler ↔ payoff)")
    if not bal:
        print("\nNo two-sided engine themes are central to this deck. Engines covered: "
              + ", ".join(sorted(ENGINE_THEMES)) + ".")
        return 0

    def fmt(pairs):
        return ", ".join(f"{n}×{q}" if q > 1 else n for n, q in pairs)

    flagged = 0
    for theme, info in bal.items():
        mark = "⚠ " if info["flag"] else "  "
        print(f"\n{mark}{theme}: {info['verdict']}")
        if info["enablers"]:
            print(f"    enablers ({info['en']}): {fmt(info['enablers'])}")
        if info["payoffs"]:
            print(f"    payoffs  ({info['pay']}): {fmt(info['payoffs'])}")
        if info.get("deaths"):
            print(f"    death-triggers ({info['death']}, combat-fed): {fmt(info['deaths'])}")
        flagged += 1 if info["flag"] else 0

    print("\nHeuristic + text-based — a card can play both sides, and the classifier can "
          "miss an unusual phrasing, so read the lists. Fix a ⚠ by adding the short side "
          "(`deck.py suggest`) or trimming dead payoffs (`deck.py cuts`).")
    return 0


def cmd_rotation(args):
    """Roster-wide Standard-rotation exposure — which of your decks run cards closest to
    rotating, and what rotates next. Offline: reads the pool's Released/Legalities
    snapshot. A card's rotation year is its set's release + `--years` (Standard's ~3y
    window); `--within` sets how far ahead to look (default 2). Scope with --format."""
    fmt = (args.fmt or "standard").strip().lower()
    decks, rollup, meta = rotation_sweep(fmt, years=args.years, within=args.within)
    if not meta["has_released"]:
        eprint("card-pool.csv has no Released column — rebuild it (build_pool.py --all) so "
               "rotation dates are available. Nothing to report until then.")
        return 1
    if meta["stale_days"] is not None and meta["stale_days"] > 120:
        eprint(f"⚠ card-pool.csv is {meta['stale_days']} days old — its legality/rotation "
               "snapshot may lag the current Standard; rebuild with build_pool.py --all.")
    this_year = meta["this_year"]
    total = sum(d["n_slots"] for d in decks)
    print(f"Rotation sweep ({fmt}, ~{args.years}y window, next {args.within}y) — "
          f"{meta['n_decks']} deck(s), {total} rotating card-slot(s).")
    if not total:
        print(f"No cards rotating within {args.within} year(s). ✓ "
              "(widen with --within, or rebuild the pool if it's stale.)")
        return 0

    print("\nRotates by year (deck-slots · distinct cards · decks) — soonest first:")
    for ry in sorted(rollup):
        rr = rollup[ry]
        soon = "  ⚠ SOON" if ry <= this_year + 1 else ""
        past = "  (past-due — pool may be stale)" if ry < this_year else ""
        print(f"  ~{ry:>7}: {rr['slots']:>3} slot(s) · {len(rr['cards']):>3} card(s) · "
              f"{len(rr['decks']):>2} deck(s){soon}{past}")

    print("\nBy deck (most-exposed first):")
    for d in decks:
        if not d["n_slots"]:
            continue
        print(f"\n  deck {d['id']:>4}  {d['name'][:34]:34} {d['n_slots']} rotating")
        for c in d["atrisk"]:
            print(f"       ~{c['rotates']:>4}  {c['qty']}× {c['name']} ({c['set']})")

    if meta["unverified"]:
        print(f"\n({meta['unverified']} card-slot(s) not found in the pool — unverified, "
              "skipped; rebuild the pool if they're recent.)")
    print("\nTiming is a ~%d-year heuristic from set release, not the official schedule, and "
          "the pool keys one printing per card (a reprint can read early) — verify before "
          "disenchanting." % args.years)
    return 0


def cmd_brawl(args):
    """Roster-wide Brawl-readiness — which of your decks are closest to a legal Brawl
    conversion, and the best commander for each. Offline. `distance` = cards to change:
    duplicates to trim to singleton + cards outside the best commander's color identity
    (basics refill the freed slots). A deck at distance 0 with a commander is Brawl-ready
    as-is; pick the commander, add `#: commander:` + `#: format: Brawl`."""
    rows = brawl_readiness(fmt_filter=args.fmt)
    if not rows:
        print(f"No {args.fmt} decks to assess.")
        return 0
    ready = [r for r in rows if not r["no_commander"] and r["distance"] == 0 and not r["converted"]]
    done = [r for r in rows if r["converted"]]
    print(f"Brawl-readiness — {len(rows)} {args.fmt} deck(s), closest to a legal Brawl "
          f"conversion first. distance = duplicates-to-singleton + off-identity cards.")
    if done:
        print(f"Already converted (a *-brawl variant exists): "
              + ", ".join(f"{r['id']}" for r in done))
    print(f"\n  {'dist':>4} {'deck':>5} {'name':24} {'col':5} {'commander (identity)':34} {'dup':>3} {'stray':>5}")
    print("  " + "-" * 92)
    for r in rows:
        if r["no_commander"]:
            continue
        tag = " ✓" if r["converted"] else ""
        cmd = (f"{r['commander'][:26]} ({r['cmd_ident']})") if r["commander"] else "—"
        print(f"  {r['distance']:>4} {r['id']:>5} {r['name'][:24]:24} {r['colors']:5} "
              f"{cmd:34} {r['dup']:>3} {r['stray']:>5}{tag}")
    nocmd = [r for r in rows if r["no_commander"]]
    if nocmd:
        print(f"\n  No in-deck commander (needs a legendary creature/planeswalker added): "
              + ", ".join(f"{r['id']} {r['name'][:18]}" for r in nocmd[:10]))
    print("\nRead it like `rotation`/`audit` — a shortlist. distance 0 (+ commander) = "
          "ready as-is; a few strays = swap those for on-identity cards (deck.py legal "
          "<id> --format brawl names them). Copies are fungible, so a Brawl build costs "
          "no extra owned cards. Grade the commander from full text (deck.py text / card.py).")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Manage decks and variations.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list all decks and variants")
    p = sub.add_parser("wildcards", help="roster-wide crafting plan (wildcards to finish decks)")
    p.add_argument("--dedup", action="store_true",
                   help="cross-deck union of craft targets, ranked by decks served per copy")
    p = sub.add_parser("audit", help="roster-wide triage scorecard — which decks need a tune (offline)")
    p.add_argument("--flagged", action="store_true",
                   help="show only decks with a flag (hide the 'ok' rows)")
    p.add_argument("--by-tier", action="store_true",
                   help="sort by competitive tier (S→D, ungraded last) instead of by maintenance verdict")
    p = sub.add_parser("check", help="owned vs needed vs your collection")
    p.add_argument("id")
    p = sub.add_parser("diff", help="show what one deck changes vs another")
    p.add_argument("a"); p.add_argument("b")
    p = sub.add_parser("arena", help="emit an Arena-importable decklist")
    p.add_argument("id")
    p = sub.add_parser("stats", help="mana curve, colors, and type breakdown")
    p.add_argument("id")
    p = sub.add_parser("mana", help="hybrid-aware color requirements")
    p.add_argument("id")
    p = sub.add_parser("consistency",
                       # `%%`, not `%`: argparse renders a help string through
                       # `help % params`, so a bare `%` raises ValueError and takes
                       # the WHOLE top-level `--help` down with it (broad-scan F-01).
                       help="manabase + opening-hand probability (keepable %%, land drops, cast-on-curve)")
    p.add_argument("id")
    p.add_argument("--on-draw", action="store_true",
                   help="model on the draw (extra card) instead of on the play")
    p.add_argument("--target", type=float, metavar="P",
                   help="cast-probability target as a fraction (default 0.90)")
    p = sub.add_parser("tribes", help="creature-subtype breakdown + type-matters synergies")
    p.add_argument("id")
    p = sub.add_parser("engines", help="enabler vs payoff balance for the deck's engine themes")
    p.add_argument("id")
    p = sub.add_parser("targets", help="does the deck contain TARGETS for its own gated effects (MV caps, sacrifice costs, count thresholds)")
    p.add_argument("id")
    p = sub.add_parser("brawl", help="roster-wide Brawl-readiness — which decks are closest to a legal Brawl conversion")
    p.add_argument("--format", dest="fmt", default="standard",
                   help="which decks to assess (default: standard)")
    p = sub.add_parser("rotation", help="roster-wide Standard-rotation exposure — which decks run aging-out cards")
    p.add_argument("--format", dest="fmt", default="standard",
                   help="format to check rotation for (default: standard)")
    p.add_argument("--years", type=int, default=3,
                   help="rotation window in years (default: 3, Standard's rough window)")
    p.add_argument("--within", type=int, default=2,
                   help="how many years ahead to surface (default: 2 — what rotates next)")
    p = sub.add_parser("suggest", help="recommend pool cards that fit a deck's colors + themes")
    p.add_argument("id")
    p.add_argument("--limit", type=int, default=20,
                   help="max suggestions (default 20; 0 = unlimited)")
    p.add_argument("--format", dest="fmt", metavar="FMT",
                   help="only suggest cards legal in FMT (default: the deck's "
                        "#: format:). Needs a legality-aware pool (build_pool.py).")
    p.add_argument("--any-format", action="store_true",
                   help="don't filter suggestions by format legality")
    p.add_argument("--full", action="store_true",
                   help="also print full oracle text + keywords/flags of the picks "
                        "(grade adds from text, not the tag-match line)")
    p.add_argument("--lands", action="store_true",
                   help="recommend LANDS for the manabase (fixing value + a bounded "
                        "synergy/shortfall nudge) — the axis theme-based suggest is blind to")
    p.add_argument("--ramp", action="store_true",
                   help="recommend nonland MANA SOURCES (dorks/rocks) — fixing + acceleration "
                        "+ restriction-fit; the structural need theme-suggest can't see")
    p.add_argument("--interaction", action="store_true",
                   help="recommend INTERACTION incl. off-theme removal, with a bounded "
                        "board-scaling boost (fight/'damage = creatures you control'), flagged")
    p.add_argument("--needs", action="store_true",
                   help="unified STRUCTURAL-NEEDS view: fixing · acceleration · interaction")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--unowned", action="store_true", help="only craftable suggestions")
    g.add_argument("--owned", action="store_true",
                   help="only cards you already own (0 wildcards)")
    p = sub.add_parser("legal", help="deck-construction lint: size, copy limits, format legality")
    p.add_argument("id")
    p.add_argument("--format", dest="fmt", metavar="FMT",
                   help="check against FMT instead of the deck's #: format:")
    p = sub.add_parser("preflight", help="one-call verify: legal + owned + castable + integrity (for skills)")
    p.add_argument("id")
    p = sub.add_parser("quality", help="deck-quality vector + regression guard for a cut/swap (for skills)")
    p.add_argument("id")
    p.add_argument("--json", action="store_true", help="print the quality vector as JSON (snapshot before a change)")
    p.add_argument("--vs", metavar="FILE", help="diff against a saved --json snapshot and flag regressions")
    p.add_argument("--add", metavar="NAME", help="warn if adding NAME would be a merely-tangential fit")
    p.add_argument("--at", metavar="REF", help="compare this deck's list at a past git ref against now")
    p.add_argument("--strict", action="store_true", help="exit non-zero on any regression/weak-add (default: warn only)")
    p = sub.add_parser("history", help="show a deck file's git change history (its changelog)")
    p.add_argument("id")
    p.add_argument("--since", metavar="YYYY-MM-DD",
                   help="only commits on/after this date, plus the cumulative card-level "
                        "net change since then (what you still need to push to Arena)")
    p = sub.add_parser("tier", help="check a deck's claimed tier against its measurable quality floor")
    p.add_argument("id")
    p.add_argument("--strict", action="store_true", help="exit non-zero on a tier mismatch (default: warn only)")
    p.add_argument("--to", metavar="TIER", help="show the measurable gap + owned fillers to reach TIER's floor (S/A/B/C/D)")
    p.add_argument("--audit-rationale", action="store_true",
                   help="flag `#: tier:`/`#: notes:` prose that has gone stale — cards it "
                        "cites that are no longer in the deck, and figures that no longer "
                        "match the live quality vector")
    p = sub.add_parser("shape", help="wide vs tall, fast vs slow — the structural read themes can't give")
    p.add_argument("id")
    p = sub.add_parser("redundancy",
                       help="competitive-consistency planner: virtual (functional) copies first, duplicates as fallback")
    p.add_argument("id")
    p.add_argument("--target", type=int, metavar="N",
                   help=f"virtual-copy depth to aim each plan-effect at (default {_REDUNDANCY_TARGET})")
    p = sub.add_parser("cuts", help="rank the deck's weakest-fit cards as cut candidates")
    p.add_argument("id")
    p.add_argument("--limit", type=int, default=8,
                   help="how many cut candidates to show (default 8; 0 = all)")
    p = sub.add_parser("flex", help="show a deck's flex / suggested swaps (#~ lines)")
    p.add_argument("id")
    p = sub.add_parser("swap", help="preview/apply a single -cut/+add swap with deltas")
    p.add_argument("id")
    p.add_argument("--cut", required=True, help="card to remove")
    p.add_argument("--add", required=True, help="card to add")
    p.add_argument("--apply", action="store_true",
                   help="write the change (with a .bak); default is a dry-run preview")
    p.add_argument("--section", metavar="HEADER",
                   help="place the added line under the `# section` whose header "
                        "contains this substring, instead of inheriting the cut card's "
                        "slot (G-05). Moves the line VERBATIM, so the (SET) COLLECTOR# "
                        "fields cannot be mistyped the way a hand edit can (G-65). "
                        "Refuses an absent or ambiguous header without writing.")
    p = sub.add_parser("move",
                       help="relocate one card line under a different `# section` "
                            "header, verbatim (the mechanical form of the hand edit "
                            "G-65 forbids; writes NO recommendations row)")
    p.add_argument("id")
    p.add_argument("card", help="card name (either face spelling of a DFC)")
    p.add_argument("--section", required=True, metavar="HEADER",
                   help="target `# section` header substring; refuses an absent or "
                        "ambiguous header before writing anything")
    p.add_argument("--apply", action="store_true",
                   help="write the change (with a .bak and the total-preserving "
                        "guard); default is a dry-run preview")
    p = sub.add_parser("feedback",
                       help="how the recommenders scored against the swaps you applied")
    p.add_argument("id", nargs="?", help="limit to one deck (default: the whole roster)")
    p = sub.add_parser("apply-flex", help="promote a flex swap (#~ line) into the maindeck")
    p.add_argument("id")
    p.add_argument("n", type=int, help="which flex swap (1-based; see deck.py flex <id>)")
    p.add_argument("--apply", action="store_true",
                   help="write the change (with a .bak); default is a dry-run preview")
    p = sub.add_parser("verify", help="compare a pasted/piped Arena export against a stored deck")
    p.add_argument("id")
    p.add_argument("source", nargs="?", default="-",
                   help="path to an export file, or '-' / omitted to read stdin")
    p = sub.add_parser("sync", help="reconcile stored deck files FROM a pasted Arena export (many decks at once)")
    p.add_argument("source", nargs="?", default="-",
                   help="path to an export file, or '-' / omitted to read stdin")
    p.add_argument("--apply", action="store_true",
                   help="write the drifted deck files (with .bak); default is a dry run")
    p.add_argument("--force", action="store_true",
                   help="also write decks whose match was low-confidence (a variant sibling "
                        "was nearly as close) — check the diff first")
    p = sub.add_parser("text", help="dump every card's FULL oracle text (read before grading cuts/swaps)")
    p.add_argument("id")
    p = sub.add_parser("suggest-homes",
                       help="find which decks a card fits (castable + shared theme), with a cut")
    p.add_argument("card", help="card name to place across your decks")
    p.add_argument("--any-format", action="store_true",
                   help="don't filter to decks whose format the card is legal in")
    p = sub.add_parser("similar", help="rank the decks most similar to <id> (is it distinct?)")
    p.add_argument("id")
    p.add_argument("--limit", type=int, default=8, help="how many similar decks to show (default 8)")
    p.add_argument("--specific-only", action="store_true",
                   help="score SPECIFIC (identity) themes only — drop generic value overlap")
    p.add_argument("--full", action="store_true",
                   help="list the shared nonland CARD names — the concrete evidence behind "
                        "the theme cosine")
    p = sub.add_parser("resolve",
                       help="turn card names into deck lines `<qty> Name (SET) #` (from args or stdin)")
    p.add_argument("names", nargs="*",
                   help="card names (optional leading qty); omit or '-' to read stdin")
    p.add_argument("--format", default="standard",
                   help="warn about names not legal in this format (default standard; "
                        "'any' disables the check)")
    p.add_argument("--expect", type=int, default=None,
                   help="fail unless the resolved quantities total exactly this many "
                        "cards (e.g. --expect 60 for a from-scratch draft)")
    p.add_argument("--check", metavar="DECK",
                   help="verify an EXISTING deck file's (SET) COLLECTOR# fields against "
                        "known printings instead of resolving names — deck id or path. "
                        "STRICT: an unheld printing fails here (G-65 keeps it soft in "
                        "check_all because a legitimate alternate printing exists; a "
                        "drafted file's lines should come from resolve, so here it is "
                        "presumed a typo). Run it after writing a from-scratch deck.")
    p.add_argument("--fix", metavar="DECK",
                   help="REPAIR what --check reports: rewrite each bad (SET) COLLECTOR# "
                        "to the resolver's printing, in place, preserving the quantity, "
                        "name and any trailing comment verbatim. Dry-run unless --apply. "
                        "Exists because --check's only remedy was a hand edit, which is "
                        "the operation G-65 forbids and G-77 was written about.")
    p.add_argument("--apply", action="store_true",
                   help="with --fix, write the change (with a .bak and the INV-04 "
                        "re-check); default is a dry-run preview")
    p = sub.add_parser("screen",
                       help="re-score candidate cards against a deck's CURRENT list; "
                            "flags strict upgrades of cards already in it")
    p.add_argument("id", help="deck id")
    p.add_argument("names", nargs="*",
                   help="card names (optional leading qty); omit or '-' to read stdin")
    p.add_argument("--format", default=None,
                   help="legality format (default: the deck's own; 'any' disables)")
    p.add_argument("--full", action="store_true",
                   help="(default since 2026-08-28; kept for compatibility)")
    p.add_argument("--no-text", action="store_true",
                   help="suppress the per-candidate oracle text (labels only — the "
                        "mis-grade mode G-52 exists to prevent; know why you want this)")
    args = ap.parse_args()

    return {
        "list": cmd_list, "wildcards": cmd_wildcards, "audit": cmd_audit, "check": cmd_check,
        "diff": cmd_diff, "arena": cmd_arena, "stats": cmd_stats,
        "mana": cmd_mana, "consistency": cmd_consistency,
        "tribes": cmd_tribes, "engines": cmd_engines, "targets": cmd_targets,
        "suggest": cmd_suggest,
        "rotation": cmd_rotation, "brawl": cmd_brawl,
        "legal": cmd_legal, "cuts": cmd_cuts,
        "shape": cmd_shape,
        "flex": cmd_flex, "swap": cmd_swap, "apply-flex": cmd_apply_flex,
        "verify": cmd_verify, "sync": cmd_sync, "text": cmd_text,
        "suggest-homes": cmd_suggest_homes,
        "similar": cmd_similar, "resolve": cmd_resolve, "screen": cmd_screen,
        "move": cmd_move,
        "preflight": cmd_preflight, "quality": cmd_quality, "tier": cmd_tier,
        "redundancy": cmd_redundancy, "history": cmd_history,
        "feedback": cmd_feedback,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
