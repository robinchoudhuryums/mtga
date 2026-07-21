"""Shared helpers for the MTG Arena card library tooling.

Every script in this repo reads and writes the same CSV file, so the column
definition and the load/save logic live here in one place.
"""

import csv
import os
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


def write_rows(rows, path=DEFAULT_CSV, *, backup=True):
    """Write rows (list of dicts) back to the CSV using the canonical header.

    Uses QUOTE_MINIMAL so fields containing commas/quotes/newlines are escaped
    per standard CSV rules, matching the formatting the header established. The
    write goes through ``atomic_write`` (temp file + timestamped ``.bak`` + atomic
    replace), so an interrupted write can't truncate the canonical inventory. Pass
    ``backup=False`` when writing to a scratch temp the caller will promote itself.
    """
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


def eprint(*args, **kwargs):
    """Print to stderr (keeps machine-readable output clean on stdout)."""
    print(*args, file=sys.stderr, **kwargs)
