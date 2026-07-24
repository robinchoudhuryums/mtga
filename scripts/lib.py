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

# Repo root is the parent of the scripts/ directory this file lives in.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CSV = os.path.join(REPO_ROOT, "card-library.csv")


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
    files are gitignored. (Readers that need the newest should still prefer mtime.)
    """
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = f"{target}.{stamp}.bak"
    n = 0
    while os.path.exists(path):
        n += 1
        path = f"{target}.{stamp}{n:04d}.bak"
    return path


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
        if backup and os.path.exists(path):
            shutil.copy2(path, backup_path(path))
        os.replace(tmp, path)
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


def owned_qty(index, name):
    """Quantity owned for a card name from a name→count index, DFC-aware.

    The library — and every ownership index built from it — keys a double-faced card
    under its FRONT face, while the pool / wishlist store the full ``Front // Back``
    name. So look up the full name, then fall back to the front, else an owned DFC
    reads as unowned (audit F6). Every pool-facing ownership join routes through here
    so the three copies of this logic can't drift apart.
    """
    nl = (name or "").strip().lower()
    return index.get(nl) or index.get(nl.split(" // ")[0], 0)


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
    return (f"{os.path.basename(path)} is not the card library — its header is "
            f"{existing}, not the canonical {header}. Writing it with the library "
            f"header would DROP {lost or 'columns'}. Refusing (audit F-02); rebuild "
            f"derived files with their own builder (build_pool.py / build_mana.py).")


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


def full_card_text(name, _cache={}):
    """Return a card's COMPLETE, untruncated oracle text — library first, then the
    pool (so unowned cards resolve too). '' if not found.

    This is the accessor every card-EVALUATION path should use. Grading a card from
    a truncated / sliced read is a known, repeated mistake (see CLAUDE.md's card.py
    gotcha); routing evaluators through one never-truncating accessor removes the
    temptation. DFC names match on the full name or the front face.
    """
    nl = (name or "").strip().lower()
    if not nl:
        return ""
    front = nl.split(" // ")[0]
    if not _cache:
        for path in (DEFAULT_CSV, _POOL_CSV):
            if not os.path.exists(path):
                continue
            with open(path, newline="", encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    cn = (r.get("Card Name") or "").strip().lower()
                    if cn and cn not in _cache:
                        _cache[cn] = r.get("Card Text") or ""
                        _cache.setdefault(cn.split(" // ")[0], _cache[cn])
    return _cache.get(nl) or _cache.get(front) or ""


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
    """Cached pool ability-rarity model. Returns (idf, tribe_tags, n):
      idf         {tag: log(N/(1+df))} over the full pool — a tag on FEW cards scores high.
      tribe_tags  capitalized creature SUBTYPES seen anywhere in the pool (Human, Ape,
                  Otter, …) — identity, not ability, so a niche tribe doesn't read as a
                  distinctive MECHANIC.
      n           pool card count.
    Empty model ({}, set(), 0) if the pool is missing — callers degrade to a neutral 0.0.
    """
    if _cache:
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
    _cache.update(idf=idf, tribes=tribes, n=n)
    return idf, tribes, n


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
