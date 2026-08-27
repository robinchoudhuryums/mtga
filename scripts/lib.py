"""Shared helpers for the MTG Arena card library tooling.

Every script in this repo reads and writes the same CSV file, so the column
definition and the load/save logic live here in one place.
"""

import csv
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime

# The canonical column order. This MUST match the header row in card-library.csv
# and the companion Google Sheet, so the two stay compatible if ever merged.
HEADER = [
    "Card Name",
    "Type",
    "Card Text",
    "Color(s)",
    "Synergies",
    "Set Code",
    "Collector #",
    "Quantity Owned",
]

# The five basic land names plus Wastes. NOT part of the collection — Arena gives you
# unlimited copies — so every ingest writer skips them and every analysis treats them as
# free. Defined ONCE here after living in four modules as four identical literals: they
# could not drift without someone noticing, but a fifth writer forgetting the set entirely
# is exactly what happened to `reconcile_crafts` (BS4-03), and a name you have to import
# is one you notice you need.
BASICS = frozenset({"plains", "island", "swamp", "mountain", "forest", "wastes"})

# Repo root is the parent of the scripts/ directory this file lives in.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CSV = os.path.join(REPO_ROOT, "card-library.csv")
# ONE definition of the played-match record's path, because two modules now read it:
# parse_matches.py owns the file, and deck.py's roster audit reports games played from
# it. A second `os.path.join(REPO_ROOT, "matches.csv")` is the drift shape
# `check_agreement` exists for — same reasoning as BASICS living here.
MATCHES_CSV = os.path.join(REPO_ROOT, "matches.csv")


def load_rows(path=DEFAULT_CSV):
    """Return (header, rows) where rows is a list of dicts keyed by column name.

    Raises FileNotFoundError if the CSV is missing.
    """
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        rows = [dict(r) for r in reader]
    return header, rows


def backup_path(target):
    """A unique, lexicographically-sortable ``.bak`` path for ``target``.

    Every backup in the toolkit routes through here so the naming can't drift into the
    collision/ordering bugs audit F22 found (a second-precision name overwritten by a
    same-second write; an ``-%f.N`` counter that sorted BEFORE its base). A microsecond
    timestamp gives chronological lexical order; a sub-microsecond collision appends a
    zero-padded counter placed so it still sorts AFTER the collision-free name. ``.bak``
    files are gitignored.

    Read the newest one back with ``latest_backup``, NOT with ``max(..., key=getmtime)``
    — see that function for why mtime is the wrong key for a file made by ``copy2``.
    """
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = f"{target}.{stamp}.bak"
    n = 0
    while os.path.exists(path):
        n += 1
        path = f"{target}.{stamp}{n:04d}.bak"
    return path


# The stamp `backup_path` embeds: `<target>.YYYYmmdd-HHMMSS-ffffff[NNNN].bak`.
_BAK_STAMP_RE = re.compile(r"\.(\d{8}-\d{6}-\d{6})(\d{4})?\.bak$")


def backup_stamp(path):
    """The CREATION stamp `backup_path` embedded, as a sortable tuple, or None if the
    name doesn't follow the scheme (a hand-made or legacy `.bak`)."""
    m = _BAK_STAMP_RE.search(path or "")
    return (m.group(1), m.group(2) or "") if m else None


def latest_backup(paths):
    """The most recently CREATED backup among `paths` (None if empty).

    Selects on the stamp in the NAME, not on mtime, because every backup here is made
    with ``shutil.copy2`` — which copies the source's mtime. A `.bak`'s mtime is
    therefore *when its contents were written*, not when the backup was taken, and those
    orders diverge the moment anything restores an old file: `app.py`'s ``revert`` writes
    a restored (old-mtime) file back into place, so the NEXT save's backup inherits that
    old mtime and sorts before backups of newer content. Reproduced end to end — save,
    save, revert, save, revert restored the state that had already been discarded rather
    than the pre-save one, silently re-applying the change the user had just undone
    (broad-scan F-04).

    The names are microsecond-stamped at creation and lexically ordered by construction
    (that is what `backup_path` is for), so they are the reliable key. Falls back to
    mtime only when NO name carries a stamp — the legacy/hand-made case F22's mtime
    selection was reaching for; a stamped name always wins over an unstamped one, which
    is correct, since the stamped scheme is the current one.
    """
    paths = list(paths or [])
    if not paths:
        return None
    stamped = [p for p in paths if backup_stamp(p)]
    if stamped:
        return max(stamped, key=backup_stamp)

    def _mtime(p):
        # A path that has vanished sorts last rather than raising: this is the fallback
        # inside a RESTORE path, and losing the selector to a stat error is worse than
        # picking the next-newest file.
        try:
            return os.path.getmtime(p)
        except OSError:
            return -1.0
    return max(paths, key=_mtime)


def atomic_write(path, write_fn, *, backup=True):
    """Write `path` durably: render to a temp file in the same directory, optionally
    back the existing file up to a timestamped `.bak`, then atomically ``os.replace``.

    ``write_fn(fh)`` receives the open text handle (``newline=""``, UTF-8) and writes
    the full content. A crash mid-write leaves the original file — and the ``.bak`` —
    intact: the temp is removed and never promoted. This mirrors the safety app.py /
    deck.py already use, so the ingest/rebuild write paths stop truncating the source
    of truth in place (audit F5). ``.bak`` files are gitignored. Pass ``backup=False``
    when the caller manages its own backup or the target is itself a scratch temp.
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
            write_fn(fh)
            # fsync BEFORE the rename: os.replace is atomic against a process crash
            # either way, but without the flush-to-disk a power loss shortly after a
            # "successful" write could surface an empty/old file — the docstring
            # promised "durably" and the code didn't deliver it (broad-scan batch 5).
            fh.flush()
            os.fsync(fh.fileno())
        # mkstemp creates the temp 0600 and os.replace keeps the temp's mode, so
        # every write silently flipped the canonical CSV 644 → 600 (masked locally
        # because git checkouts reset modes). Carry the target's own mode over.
        if os.path.exists(path):
            shutil.copymode(path, tmp)
        else:
            os.chmod(tmp, 0o644)
        if backup and os.path.exists(path):
            shutil.copy2(path, backup_path(path))
        os.replace(tmp, path)
        try:
            # fsync the DIRECTORY too, so the rename itself survives power loss.
            dfd = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except OSError:
            pass  # some platforms can't fsync a directory; atomicity still holds
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def card_colors(colstr):
    """Color IDENTITY as a set of WUBRG letters from a ``Color(s)`` cell.

    Handles the two representations used in the CSVs: the literal string
    ``"Colorless"`` (→ empty set) and slash-joined gold cards (``"B/G"`` → {B, G}).
    The naive ``{ch for ch in s.upper() if ch in "WUBRG"}`` is WRONG for
    ``"Colorless"`` — the word contains an ``R``, so a colorless card would read as
    red and get mis-routed by suggest/suggest-homes (audit F1). Slashes and spaces
    are ignored automatically because they aren't WUBRG letters (audit F2, where a
    ``.replace(" ", "")`` variant left the ``/`` in and broke the subset test).
    """
    s = (colstr or "").strip()
    if s.lower() == "colorless":
        return set()
    return {ch for ch in s.upper() if ch in "WUBRG"}


def alias_front(index):
    """SECOND-PASS front-face aliasing for a name-keyed index over pool-shaped data:
    every `Front // Back` key gets its FRONT aliased to the same value — but only
    when no REAL row already claims the front name, so a distinct card named
    `Front` is never shadowed ("Life" is a card as well as the front of
    "Life // Death"). Call it AFTER the loop that inserts real rows; aliasing
    in-pass (`setdefault` inside the row loop) is order-dependent — a full-name row
    seen early claims the front before the real card's own row arrives (G-63).

    This is the index half of G-63 given ONE home: six loaders each carried their
    own copy of this loop, two aliased in-pass with the shadowing trap, and a
    seventh (`reconcile_crafts`' pool map) never aliased at all, reporting owned
    DFCs "NOT FOUND in pool" (broad-scan BS-16/batch 4). `check_dfc` behaviorally
    verifies each registered loader resolves a DFC's front key. Mutates and
    returns `index`."""
    for n in list(index):
        front = n.split(" // ")[0].strip()
        if front and front != n and front not in index:
            index[front] = index[n]
    return index


def color_matches(cell, needle):
    """Does a ``Color(s)`` identity cell match a user's ``--color`` filter?

    SET semantics through ``card_colors`` on BOTH sides — never a substring test.
    The substring predecessor was the F1 trap wearing a filter's clothes:
    ``"r" in "colorless"`` is True, so ``--color R`` matched every Colorless card
    (104 of the 546 library rows it returned; all 1,116 Colorless pool cards) in
    query.py / pool.py / wishlist.py at once, and the AST gate couldn't see it
    because a substring ``in`` is not the comprehension idiom it scans for
    (broad-scan BS-10/BS-18 — check_colors now scans for this shape too).

    A needle with WUBRG letters ("R", "WU", "B/G") matches cards whose identity
    CONTAINS all of them; a needle with none ("colorless", "c") matches only
    colorless cards; None/blank means "no filter" and matches everything.
    """
    if needle is None or not str(needle).strip():
        return True
    want = card_colors(needle)
    have = card_colors(cell)
    return want <= have if want else not have


def color_within(cell, needle):
    """Does a ``Color(s)`` identity cell fit WITHIN a deck of the given colors?

    The SUBSET complement of ``color_matches`` (DD-4). ``color_matches`` asks "does
    this card's identity CONTAIN the filter's colors" — right for "show me red cards",
    wrong for the question every from-scratch draft asks: "which cards are castable in
    a Naya deck". Under superset semantics ``--color WRG`` returned five-color cards,
    and both 2026-08-21 drafts fell back to hand-written subset loops for the Stage-1
    pool survey. Here the card's identity must be a SUBSET of the filter's colors, and
    a COLORLESS card always passes — it is castable in any deck. Same set discipline
    as ``color_matches``: through ``card_colors`` on both sides, never a substring.
    Note this reads IDENTITY, so a hybrid stays castable-broader than it looks and an
    ability-only off-color identity reads stricter than the printed cost (G-58) —
    a review filter, not a castability verdict.
    """
    if needle is None or not str(needle).strip():
        return True
    want = card_colors(needle)
    have = card_colors(cell)
    return have <= want


def owned_qty(index, name):
    """Quantity owned for a card name from a name→count index, DFC-aware.

    The library — and every ownership index built from it — keys a double-faced card
    under its FRONT face, while the pool / wishlist store the full ``Front // Back``
    name. So look up the full name, then fall back to the front, else an owned DFC
    reads as unowned (audit F6). Every pool-facing ownership join routes through here
    so the three copies of this logic can't drift apart.
    """
    nl = (name or "").strip().lower()
    # NOT `index.get(nl) or index.get(front, 0)`: a stored count of a real 0 — which
    # `import_collection --zero-missing` can now write and INV-01 permits — is falsy, so
    # `or` treated an explicit "you own none of this" as ABSENT and fell through to the
    # front-face key. Today the fallback also returns 0, but paired with a front-name
    # collision it would return a DIFFERENT card's count. `card_power` in this same file
    # documents exactly this trap for a printed power of 0; the lesson had not been
    # applied to quantity (BS4-19).
    if nl in index:
        return index[nl]
    return index.get(nl.split(" // ")[0], 0)


def card_power(value):
    """A card's printed power/toughness as an int, or ``None`` when it isn't a number.

    Magic prints ``*``, ``1+*``, ``X`` and ``∞`` as often as it prints ``4``, so this
    NEVER coerces — a caller that needs "power 4 or greater" gets ``None`` and must
    decide what unknown means, rather than silently treating a ``*`` as 0. A leading
    sign is accepted because a few cards print negative toughness.

    Nothing in the repo stored P/T before, which left a whole class of card
    ungradeable by any tool: "whenever a creature with power 4 or greater enters"
    (Garruk's Uprising), Doran-style toughness-matters payoffs, and every "power N or
    greater" condition. It also produced a real mis-read — Mossborn Hydra reads like a
    big body but is printed 0/0 and enters with a single counter, so it does not
    trigger Garruk on entry.
    """
    if value is None:
        return None
    # NOTE `str(value or "")` would be wrong here: a printed power of 0 is real and
    # common (every X-creature is 0/0), and `0 or ""` collapses it to unknown.
    s = str(value).strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


_MANA_SYMBOL_RE = re.compile(r"\{([^}]+)\}")
# Scryfall joins the two castable halves of a split / Room / Adventure card with " // ".
_COST_SPLIT = " // "


def front_face_cost(cost):
    """The half of a mana cost you actually pay — the FRONT face.

    Scryfall stores a split, Room or Adventure card's cost as ``A // B`` (e.g. Funeral
    Room's ``{2}{B} // {6}{B}{B}``), and you never pay both. Reading the merged string
    over-counts pips for EVERY such card — 292 of them in the pool, 15 across the deck
    roster — so a two-half card looked far more colour-hungry than it is: Funeral Room
    read as a ``{B}{B}{B}`` turn-5 play when the door this deck casts is ``{2}{B}``,
    one black pip on turn 3.

    FRONT is the convention, matching ``owned_qty``'s front-face rule for DFCs: it is
    the creature on an Adventure card and the cheap door on a Room. The residual is a
    deck that plays a split card mainly for its BACK half, which then reads cheaper
    than it plays — grade that from the printed card, as with any front-face read.
    """
    return (cost or "").split(_COST_SPLIT, 1)[0]


def primary_type(type_line):
    """The card's type for analysis, read from the FRONT FACE ONLY.

    A two-faced card's type line is stored as `Front // Back`, and a substring scan
    over the whole string reports the BACK face's type whenever it sorts earlier in
    `order` — which for `Land` is always. So `Legendary Creature — God // Land`
    (Ojer Axonil) and `Legendary Artifact // Legendary Artifact Land` (Matzalantli)
    both read as LAND, and every one of deck.py's ~35 `"Land" in primary_type(...)`
    guards then skipped them: excluded from the curve, uncounted as creatures, and
    ADDED to the land total. `consistency 49` reported "Lands: 26/60" for a deck
    holding 25, with keepable computed against a phantom land. 81 pool cards share the
    shape; three were live in decks (Matzalantli in 51/51a, Ojer Kaslem in 50a).

    The front face is the correct read for the same reason G-02 gives for cost: it is
    the half you cast or play. A card whose front really IS a land (Jidoor's
    `Land — Town // Sorcery — Adventure`) still reports Land, because the front says so.

    Lives HERE, not in deck.py, because build_gallery.py had its own copy carrying the
    identical back-face bug — the second copy went on mis-typing the gallery's breakdown
    for as long as it existed separately. One definition, one fix.
    """
    front = (type_line or "").split("//")[0]
    order = ["Land", "Creature", "Planeswalker", "Battle", "Artifact",
             "Enchantment", "Instant", "Sorcery"]
    for t in order:
        if t.lower() in front.lower():
            return t
    return "Other"


def mana_value(cost):
    """Mana value of ONE cost string: generic numbers plus one per non-generic symbol.

    ``X`` counts 0 (as the rules do off the stack). Pass a single face — split costs
    should go through ``front_face_cost`` first, since a split card's *rules* mana
    value is the combined total and that is NOT the number a curve or a
    cast-on-curve probability wants.
    """
    total = 0
    for sym in _MANA_SYMBOL_RE.findall(cost or ""):
        s = sym.strip().upper()
        if s.isdigit():
            total += int(s)
        elif s in ("X", "Y", "Z"):
            continue
        elif "/" in s and any(p.isdigit() for p in s.split("/")):
            # A MONOCOLOR hybrid contributes its larger half (CR 202.3f): {2/G} is
            # mana value 2, not 1. Counting it 1 under-read Wildgrowth Archaic's
            # {2/G}{2/G} as MV 2 against a real 4, and made a recompute disagree
            # with the stored Mana Value column — a two-answers split (batch 5).
            total += max(int(p) for p in s.split("/") if p.isdigit())
        else:
            # A colored, hybrid or phyrexian symbol is worth 1 regardless of how
            # many colours it offers ({W/U} is one mana, not two; {W/P} is 1).
            total += 1
    return total


class WrongSchema(Exception):
    """Refused to write a CSV that isn't the card library (see ``csv_schema_error``)."""


def csv_schema_error(path, header=None):
    """Why ``path`` must NOT be written with the canonical library ``header``, or None.

    ``write_rows`` emits exactly ``HEADER``, so pointing a library writer at a DERIVED
    file silently drops every extra column. ``tag_synergies.py`` / ``enrich.py`` take a
    ``path`` argument, and CLAUDE.md tells you to re-tag ``card-pool.csv`` — which used
    to rewrite the pool with the 8 library columns, destroying ``Rarity`` /
    ``Legalities`` / ``Released`` and silently breaking every format filter, rotation
    flag and wildcard price (audit F-02). ``check_all`` couldn't catch it: INV-03 only
    checks that the derived files EXIST.

    A missing or empty file is fine (a fresh temp, or a first write); a file whose
    header already matches is fine. Anything else is refused by name.
    """
    header = header or HEADER
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            existing = next(csv.reader(fh), None)
    except OSError as e:
        return f"could not read the existing header of {os.path.basename(path)}: {e}"
    if existing is None or existing == header:
        return None
    lost = [c for c in existing if c not in header]
    # Direction-NEUTRAL wording. F-02 was "a library writer pointed at a derived
    # file", and the message said so literally — which read backwards the moment the
    # MIRROR guard landed (build_pool/build_mana/parse_matches `--out`): it called
    # card-library.csv "not the card library" and advised rebuilding it with a
    # derived builder, i.e. the very thing being refused (broad-scan Batch G). State
    # the mismatch and name the owning tool instead of assuming which side is which.
    return (f"{os.path.basename(path)} already holds a DIFFERENT schema: its header is "
            f"{existing}, but this writer emits {header}. Writing it would DROP "
            f"{lost or 'columns'}. Refusing (audit F-02 and its mirror) — each file is "
            f"written by the tool that OWNS it: card-library.csv by the ingest/enrich "
            f"writers, card-pool.csv by build_pool.py, card-mana.csv by build_mana.py.")


def write_rows(rows, path=DEFAULT_CSV, *, backup=True):
    """Write rows (list of dicts) back to the CSV using the canonical header.

    Uses QUOTE_MINIMAL so fields containing commas/quotes/newlines are escaped
    per standard CSV rules, matching the formatting the header established. The
    write goes through ``atomic_write`` (temp file + timestamped ``.bak`` + atomic
    replace), so an interrupted write can't truncate the canonical inventory. Pass
    ``backup=False`` when writing to a scratch temp the caller will promote itself.

    Raises ``WrongSchema`` if ``path`` is an existing CSV with a DIFFERENT header —
    the writer emits only ``HEADER``, so that would silently destroy a derived file's
    extra columns (audit F-02). See ``csv_schema_error``.
    """
    problem = csv_schema_error(path)
    if problem:
        raise WrongSchema(problem)

    def _write(fh):
        writer = csv.DictWriter(fh, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for row in rows:
            # Only emit known columns, in canonical order; ignore stray keys.
            writer.writerow({col: (row.get(col, "") or "") for col in HEADER})

    atomic_write(path, _write, backup=backup)


_POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")


# ── Card ability-distinctiveness ────────────────────────────────────────────
# The deck theme model already weights how RARE a theme is across DECKS (idf) — but
# nothing measured how generic a CARD's own abilities are, so a body carrying five
# common tags (etb; tokens; sacrifice; lifegain; pump) tripped broad synergy-overlap
# checks everywhere, indistinguishable from a card with a genuinely distinctive
# mechanic. This model supplies the missing CARD-level signal: the pool-rarity of a
# card's own ability tags. Evergreen combat keywords + broad role descriptors are
# incidental to a card (a trample body isn't "distinctive"), so they're excluded —
# the same low-signal set wishlist.NON_SIGNAL_TAGS / deck.GENERIC_THEMES intend, kept
# local so lib has no import cycle.
_EVERGREEN_TAGS = frozenset({
    "flying", "trample", "menace", "deathtouch", "lifelink", "vigilance", "haste",
    "reach", "first strike", "double strike", "ward", "hexproof", "shroud", "prowess",
    "defender", "indestructible", "protection", "intimidate", "fear", "evasion",
    "combat", "aggro", "tempo", "pump", "defense", "resilience", "selection", "value",
})


def _creature_subtypes(tline):
    """Subtypes after the em-dash on a CREATURE face ('Creature — Human Warrior' ->
    {'Human','Warrior'}). CREATURE-only on purpose: creature subtypes are tribes
    (identity, handled by the tribal model), whereas noncreature subtypes are often
    mechanics we DO want to score (Equipment, Aura, Saga, Vehicle, Food, Clue). DFC-aware."""
    out = set()
    for face in (tline or "").split(" // "):
        if "—" not in face:
            continue
        pre, post = face.split("—", 1)
        if "Creature" not in pre:
            continue
        out.update(post.split())
    return out


def pool_ability_model(_cache={}):
    """Pool ability-rarity model, memoized on the pool file's (mtime_ns, size).
    Returns (idf, tribe_tags, n):
      idf         {tag: log(N/(1+df))} over the full pool — a tag on FEW cards scores high.
      tribe_tags  capitalized creature SUBTYPES seen anywhere in the pool (Human, Ape,
                  Otter, …) — identity, not ability, so a niche tribe doesn't read as a
                  distinctive MECHANIC.
      n           pool card count.
    Empty model ({}, set(), 0) if the pool is missing — callers degrade to a neutral 0.0.

    KEYED, not held forever (broad-scan BS6-08). It used to memoize on a bare `if
    _cache:`, so the FIRST call won permanently: a `build_pool.py` run inside a
    long-lived process served the old model afterwards, and — worse — a first call made
    before the pool existed pinned the empty model for the life of the process, which is
    a SILENT degradation rather than a visible one. `card_distinctiveness` then returns
    the structural term alone and `cuts`' `Uq` co-signal quietly flattens, with nothing
    printed. Every other reference-table loader here keys on (mtime_ns, size) — the same
    reasoning `deck._file_memo` documents, including why ns beats getmtime's float
    seconds — and this was the one that did not.

    `cache_clear()` is exposed for the same reason `_file_memo` exposes it: a test that
    repoints `_POOL_CSV` needs to invalidate deterministically rather than hope the
    stat key differs.
    """
    try:
        st = os.stat(_POOL_CSV)
        key = (_POOL_CSV, st.st_mtime_ns, st.st_size)
    except OSError:
        key = (_POOL_CSV, None, None)
    if _cache.get("key") == key:
        return _cache["idf"], _cache["tribes"], _cache["n"]
    import math
    df, tribes, n = {}, set(), 0
    if os.path.exists(_POOL_CSV):
        with open(_POOL_CSV, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                n += 1
                for t in (r.get("Synergies") or "").split(";"):
                    t = t.strip()
                    if t:
                        df[t] = df.get(t, 0) + 1
                tribes |= _creature_subtypes(r.get("Type") or "")
    idf = {t: math.log(n / (1 + c)) for t, c in df.items()} if n else {}
    _cache.update(key=key, idf=idf, tribes=tribes, n=n)
    return idf, tribes, n


def _pool_model_cache_clear(_cache=None):
    """Drop the memoized pool ability model (see `pool_ability_model`)."""
    pool_ability_model.__defaults__[0].clear()


pool_ability_model.cache_clear = _pool_model_cache_clear


def distinctiveness_score(tags, idf, tribe_tags, n, *, k=2):
    """Pure 0–10 score of how distinctive a card's ABILITIES are, from the pool-rarity
    of its own synergy tags. Evergreen keywords and bare creature TRIBES are dropped
    (incidental / identity, not ability); the score is the mean of the card's k RAREST
    remaining tags' idf, normalized by the pool's max idf (log N) — so a standout
    mechanic isn't diluted by also carrying etb/tokens. A vanilla or purely-generic-
    ability card scores ~0. Pure (no I/O) so it's unit-testable with a hand-built model."""
    if not n or not idf:
        return 0.0
    import math
    ability = [t for t in tags
               if t.lower() not in _EVERGREEN_TAGS and t not in tribe_tags and t in idf]
    if not ability:
        return 0.0
    ceil = math.log(n) or 1.0
    top = sorted((idf[t] for t in ability), reverse=True)[:k]
    return round(min(10.0, 10.0 * (sum(top) / len(top)) / ceil), 1)


# ── Structural distinctiveness (oracle-text shape) ──────────────────────────
# The tag-rarity metric above is bounded by tag QUALITY: a distinctive card mis-tagged
# etb/tokens still reads generic (Ragnarok's dies-trigger, Thousand-Year Storm's copy
# payoff). This complementary signal reads the oracle TEXT's STRUCTURE — an unusual
# (non-ETB) trigger, an activated ability, rule-bending / replacement language,
# modality — to catch "this card does something the tags didn't capture," with NO
# corpus / build artifact / normalization pipeline (the cheap alternative to a text
# TF-IDF model). card_distinctiveness takes the MAX of the two signals, so a
# mis-calibration here can RESCUE a mis-tagged card but never scramble the ranking.
_STRUCT_REMINDER_RE = re.compile(r"\([^)]*\)")  # parenthetical reminder text — not an ability
# A triggered ability on an event OTHER than a plain ETB — the distinctive shape a
# generic "when this enters" token/lifegain body lacks. (Conservative: a combined
# "enters or attacks" trigger is skipped by the enters-lookahead — safe, it only
# under-fires, and the metric only ever RAISES.)
_STRUCT_NONETB_TRIGGER_RE = re.compile(
    r"when(?:ever)?\b(?![^.]*\benters\b)[^.]*?\b("
    r"dies|attacks?|blocks?|deals? (?:combat )?damage|leaves the battlefield|"
    r"you (?:cast|draw|gain|sacrifice|discard|cycle)|is (?:dealt|put into)|"
    r"an? (?:opponent|player)|beginning of|end step|upkeep|becomes)\b", re.I)
# An activated ability whose effect is NOT a bare mana ability ("{T}: Add …", generic).
_STRUCT_ACTIVATED_RE = re.compile(r"(?mi)^\s*[^:\n]{1,60}:\s*(?!add\b)\S")
# Rule-bending / replacement / asymmetric / recursion / free-cast language.
_STRUCT_RULEBEND_RE = re.compile(
    r"\b(instead|rather than|if you would|as though|can't be|without paying|"
    r"any number of|additional|extra turn|double|for each|as long as|"
    r"each (?:opponent|player)|from (?:your |a )?(?:graveyard|exile)|"
    r"search your library|copy)\b", re.I)
_STRUCT_MODAL_RE = re.compile(
    r"(choose (?:one|two|up to)|\bkicker\b|•|escape|adventure|foretell|"
    r"\bmodal\b|\bconvoke\b)", re.I)


def structural_distinctiveness(text):
    """0–10 heuristic for how much a card's oracle TEXT does BEYOND a plain body, from
    structural cues (an unusual non-ETB trigger, a non-mana activated ability, rule-
    bending / replacement language, modality, clause depth). Complements the tag-rarity
    metric for cards whose distinctive ability was tagged generically. Pure (regex only)
    — no corpus, no I/O, no normalization pipeline. A vanilla / french-vanilla / plain-
    ETB body reads low; a dies-trigger-that-recurs or a copy engine reads high."""
    t = _STRUCT_REMINDER_RE.sub(" ", text or "")
    if not t.strip():
        return 0.0
    score = 0.0
    if _STRUCT_NONETB_TRIGGER_RE.search(t):
        score += 4.0
    if _STRUCT_ACTIVATED_RE.search(t):
        score += 3.0
    if _STRUCT_RULEBEND_RE.search(t):
        score += 3.0
    if _STRUCT_MODAL_RE.search(t):
        score += 2.0
    # Clause depth, LIGHTLY: extra sentences beyond the first, capped low — a wordy
    # card isn't thereby distinctive, so verbosity can never carry the score alone.
    clauses = [c for c in re.split(r"[.\n]", t) if c.strip()]
    score += min(max(len(clauses) - 1, 0), 2) * 0.5
    return round(min(10.0, score), 1)


def card_distinctiveness(tags, text=""):
    """0–10 ability-distinctiveness for a card — the MAX of two complementary signals:
    tag-rarity (pool tag-idf) and structural (oracle-text shape). A distinctive card
    mis-tagged generically is still caught by its text structure, while a truly generic
    card (low on both) stays ~0. Structural only ever RAISES the score, so it can
    rescue a mis-tag but never scramble the ranking. Pool unavailable → tag term 0;
    text omitted → tag-only (backward-compatible with the tag-only call)."""
    idf, tribes, n = pool_ability_model()
    tag_score = distinctiveness_score(tags, idf, tribes, n)
    return max(tag_score, structural_distinctiveness(text))


def eprint(*args, **kwargs):
    """Print to stderr (keeps machine-readable output clean on stdout)."""
    print(*args, file=sys.stderr, **kwargs)


# ── Collection freshness (G-10's premise, made visible) ──────────────────────────────
# `import_collection.py` is the ONLY writer that sets owned counts EXACTLY (including
# down); everything else is a lower bound by construction. That fact lived only in
# prose, so every craft-cost surface quoted `Quantity Owned` as if it were current —
# and in one 2026-08-26 session a card the user owned read OWNED: 0 and was excluded
# from a recommendation on a wildcard cost they did not owe, while a deck's craft list
# read 19 missing against a real 4. The stamp records the one fact the CSVs cannot:
# WHEN the counts were last exact. A sidecar is justified here for the same reason the
# match watermark rejected one is inverted — matches.csv already stored its dates; the
# library stores no reconcile date anywhere, and mtime is not one (F-04: backups copy
# the source's mtime; git checkouts rewrite it).
COLLECTION_STAMP = os.path.join(REPO_ROOT, "collection-stamp.json")


def write_collection_stamp(rows, tool="import_collection", path=None):
    """Record an EXACT reconcile. Called only by writers whose counts are
    authoritative — a deck-dump import or a craft reconcile is a lower bound and must
    NOT advance this (the watermark's hand-row rule, one subsystem over)."""
    import datetime as _dt
    import json as _json
    with open(path or COLLECTION_STAMP, "w", encoding="utf-8") as fh:
        _json.dump({"reconciled": _dt.date.today().isoformat(),
                    "rows": int(rows), "tool": tool}, fh, indent=1)
        fh.write("\n")


def collection_stamp_note(max_age_days=30, path=None):
    """One-line ⓘ note when owned counts are not trustworthy, else None.

    Three states: no stamp (never exactly reconciled — the current repo's real state),
    a stamp older than `max_age_days`, or fresh (None). Report-only; callers print it
    beside a craft cost or an OWNED figure, never gate on it."""
    import datetime as _dt
    import json as _json
    p = path or COLLECTION_STAMP
    try:
        with open(p, encoding="utf-8") as fh:
            stamp = _json.load(fh)
        when = _dt.date.fromisoformat(str(stamp.get("reconciled", "")))
    except (OSError, ValueError):
        return ("ⓘ owned counts are LOWER BOUNDS — the collection has never been "
                "exactly reconciled (run import_collection.py with a tracker export; "
                "deck-dump imports only ever raise counts, G-10)")
    age = (_dt.date.today() - when).days
    if age > max_age_days:
        return (f"ⓘ owned counts last exactly reconciled {age} days ago "
                f"({when.isoformat()}) — consider a fresh import_collection.py run "
                f"before spending wildcards on them")
    return None
