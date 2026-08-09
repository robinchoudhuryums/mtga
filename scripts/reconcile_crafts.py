#!/usr/bin/env python3
"""Reconcile freshly-crafted / owned cards into the library from an Arena export.

Automates the manual dance repeated many times in past sessions when a card is
crafted (or turns out to be owned-but-undercounted): add it to card-library.csv,
add the matching card-mana.csv row, and drop it from card-wishlist.csv. Handles
the DFC convention automatically — the library stores a double-faced card under
its FRONT name (`A`), while card-pool.csv / card-mana.csv key the FULL name
(`A // B`) — which was the single most error-prone part of doing this by hand.

Input: an Arena-style export (file path, or '-' for stdin), one card per line:
    1 Doctor Doom (MSH) 95
    4 Scoured Barrens (FDN) 266
Matching is by (Set Code, Collector #) against card-pool.csv (robust to the
front/full name difference). For a new card the line's quantity is the owned
count; for a card already in the library it takes max(existing, line) so a
deck-dump slice (each line a lower bound) can't silently DROP a real count —
pass --set-exact to set the count exactly (allowing a deliberate decrease).

DRY-RUN BY DEFAULT (like `deck.py swap`); pass --apply to write. Every written
file gets a timestamped .bak. After --apply, run:  build_gallery.py + check_all.py
(or /refresh) — this tool intentionally does NOT rebuild derived art/data.
"""
import argparse
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import REPO_ROOT, eprint, atomic_write, alias_front  # noqa: E402

LIB = os.path.join(REPO_ROOT, "card-library.csv")
MANA = os.path.join(REPO_ROOT, "card-mana.csv")
POOL = os.path.join(REPO_ROOT, "card-pool.csv")
WISH = os.path.join(REPO_ROOT, "card-wishlist.csv")
LIB_HEADER = ["Card Name", "Type", "Card Text", "Color(s)", "Synergies",
              "Set Code", "Collector #", "Quantity Owned"]
LINE_RE = re.compile(r"^(\d+)\s+(.+?)\s+\(([^)]+)\)\s+(\S+)\s*$")
# Basic lands are NOT part of the collection (unlimited in Arena), which is why
# `import_arena` offers --skip-basics and `import_collection` skips them outright.
# This tool had no guard at all — and it is the one CLAUDE.md (G-10) names as the
# FASTEST fix for reconciling from an Arena export, i.e. the one most likely to be
# handed a full deck list. `7 Forest (BLB) 280` resolves against the pool's real
# basic-land rows, so `--apply` wrote a basics row into the inventory (plus a mana
# row) with no invariant able to object. Hard-skipped, never opt-in: a basic is
# never crafted, so there is no legitimate case for this tool to record one.
BASICS = {"plains", "island", "swamp", "mountain", "forest", "wastes"}


def _front(name):
    """Library convention: a DFC is stored under its front name only."""
    return name.split(" // ")[0]


def _read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _wishlist_hit(row, full, front, rec_set, rec_coll):
    """Does this wishlist row describe the card we just reconciled?

    Matching ONLY on (Set Code, Collector #) — as this did — misses two real cases, so
    a crafted card silently stays on the wishlist forever (audit F-13):
      * the wishlist row records a DIFFERENT printing of the same card, and
      * a row added NAME-ONLY during a Scryfall outage has no set/collector at all.
    So match the NAME too. The wishlist stores a double-faced card under its full
    ``Front // Back`` name while the library/export use the front, so compare both
    (the CLAUDE.md DFC convention). A blank Set Code can't false-match, because an
    Arena export line always carries ``(SET) #``."""
    nm = (row.get("Card Name") or "").strip().lower()
    if nm and nm in {full.strip().lower(), front.strip().lower()}:
        return True
    if nm and nm.split(" // ")[0] == front.strip().lower():
        return True
    rs = (row.get("Set Code") or "").strip()
    rc = str(row.get("Collector #") or "").strip()
    return bool(rs) and rs.upper() == rec_set.upper() and rc == str(rec_coll)


def _bak_write(path, fieldnames, rows):
    # Atomic temp+replace with a shared-scheme timestamped .bak (audit F22), so an
    # interrupted write can't truncate the canonical file in place.
    def _w(fh):
        w = csv.DictWriter(fh, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow({c: (r.get(c, "") or "") for c in fieldnames})
    atomic_write(path, _w)


def reconcile(export_lines, apply=False, set_exact=False):
    pool_by_sc = {}
    pool_by_name = {}
    for r in _read(POOL):
        pool_by_sc[(r["Set Code"].upper(), str(r["Collector #"]))] = r
        pool_by_name[r["Card Name"].lower()] = r
    # The pool keys a DFC under its full `Front // Back` while an Arena export
    # names the FRONT, so the un-aliased index reported an owned DFC "NOT FOUND in
    # pool (skipped)" whenever the exact (set, collector) lookup missed; the old
    # third fallback was provably dead code (broad-scan BS-16).
    alias_front(pool_by_name)

    lib = _read(LIB)
    lib_keys = {(_front(r["Card Name"]).lower(), r["Set Code"].upper(), str(r["Collector #"])) for r in lib}
    mana = _read(MANA)
    mana_names = {r["Card Name"].lower() for r in mana}
    wish = _read(WISH)
    wish_fields = list(wish[0].keys()) if wish else []

    added, bumped, mana_added, wish_removed, notfound, unparsed = [], [], [], [], [], []
    basics = []

    for raw in export_lines:
        s = raw.strip()
        if not s or s.lower() == "deck" or s.startswith("#"):
            continue
        m = LINE_RE.match(s)
        if not m:
            # Don't silently drop a line that looks like a card but didn't parse
            # (e.g. missing the `(SET) #` an Arena export carries) — audit F18.
            unparsed.append(s)
            continue
        qty, name, setc, coll = int(m.group(1)), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()
        # Skip basics BEFORE any pool lookup — REPORTED, not silently dropped, so a
        # user pasting a full deck list can see why those lines produced nothing.
        if _front(name).strip().lower() in BASICS:
            basics.append(f"{name} ({setc}) {coll} x{qty}")
            continue
        exact = pool_by_sc.get((setc.upper(), coll))
        # The name index aliases DFC fronts (above), so one lookup covers both a
        # full-name and a front-name paste.
        pr = exact or pool_by_name.get(name.lower())
        if not pr:
            notfound.append(f"{name} ({setc}) {coll}")
            continue
        full = pr["Card Name"]
        front = _front(full)
        # Which printing to RECORD: the exact pool printing when we matched on
        # (set, collector); otherwise the printing the user actually PASTED — `pr`
        # then only supplies printing-INDEPENDENT details (Type/Text/Color/Synergies),
        # never set/collector. Else a card owned as (ANB) 16 gets recorded as some
        # other pool printing (MSC 575) just because that's the one the pool happened
        # to key by name — the reconcile follow-up bug.
        rec_set = pr["Set Code"] if exact else setc
        rec_coll = str(pr["Collector #"]) if exact else coll
        key = (front.lower(), rec_set.upper(), str(rec_coll))

        # library: add or set-quantity. Match the stored row by FRONT face, not exact
        # name — the library stores most DFCs under the front name but a handful under
        # the full "A // B" (the DSK Rooms), and an exact-name join missed those rows
        # and APPENDED a duplicate front-name row for a printing already owned. The
        # owned count then split across two spellings where `lib.owned_qty` resolves
        # only one — the repair tool manufacturing the undercount it exists to repair
        # (broad-scan BS2-02). (set, collector) keeps the join unambiguous: a collector
        # number is unique within a set, so two DISTINCT cards can never collide here.
        existing = next((r for r in lib if _front(r["Card Name"]).lower() == front.lower()
                         and r["Set Code"].upper() == rec_set.upper()
                         and str(r["Collector #"]) == str(rec_coll)), None)
        if existing is None:
            lib.append({"Card Name": front, "Type": pr["Type"], "Card Text": pr["Card Text"],
                        "Color(s)": pr["Color(s)"], "Synergies": pr["Synergies"],
                        "Set Code": rec_set, "Collector #": rec_coll,
                        "Quantity Owned": str(qty)})
            lib_keys.add(key)
            added.append(f"{front} ({rec_set}) {rec_coll} x{qty}"
                         + ("  [DFC front of " + full + "]" if front != full else ""))
        else:
            old_s = existing.get("Quantity Owned") or ""
            old_n = int(old_s) if old_s.isdigit() else 0
            # Default to max() so pasting a deck-dump slice (each line a LOWER bound,
            # like import_arena) can't silently DROP a real owned count 4->1 (audit
            # F17). --set-exact restores the old "the line IS the count" behavior for a
            # deliberate decrease (e.g. after disenchanting).
            new_n = qty if set_exact else max(old_n, qty)
            if str(new_n) != old_s:
                existing["Quantity Owned"] = str(new_n)
                note = "" if set_exact or qty >= old_n else f"  (kept ≥; paste had {qty})"
                bumped.append(f"{front}: {old_s or '0'} -> {new_n}{note}")

        # mana: ensure a row under the name the LIBRARY row actually carries — the
        # front for a new row (the convention), but the stored spelling for an
        # existing one: the DSK Rooms live in the library (and card-mana.csv) under
        # the full "A // B", and checking the FRONT here appended a spurious
        # front-named mana row for a card whose real row already satisfied INV-02
        # (broad-scan BS2-02's read-side residual).
        lib_name = front if existing is None else existing["Card Name"]
        if lib_name.lower() not in mana_names:
            src = next((r for r in mana if r["Card Name"] == full), None) \
                or next((r for r in mana if r["Card Name"] == front), None)
            if src:
                mana.append({"Card Name": lib_name, "Mana Cost": src["Mana Cost"],
                             "Mana Value": src["Mana Value"], "Keywords": src["Keywords"]})
                mana_names.add(lib_name.lower())
                mana_added.append(lib_name)
            else:
                # No source mana row (a freshly-crafted card not yet in card-mana.csv):
                # still write a BLANK row so every library name has a mana row — else
                # the library gains a card with no mana row and INV-02 breaks on the
                # next check_all (audit F8). build_mana.py/refresh fills in the cost.
                mana.append({"Card Name": lib_name, "Mana Cost": "",
                             "Mana Value": "", "Keywords": ""})
                mana_names.add(lib_name.lower())
                mana_added.append(lib_name + "  (blank — run build_mana.py to fill cost/keywords)")

        # wishlist: drop the card by NAME (full or DFC front) or by the recorded
        # set+collector — see _wishlist_hit. Name matching is what lets a differently-
        # printed or name-only row go too (audit F-13).
        before = len(wish)
        wish = [r for r in wish if not _wishlist_hit(r, full, front, rec_set, rec_coll)]
        if len(wish) != before:
            wish_removed.append(full)

    # report
    def section(title, items):
        print(f"{title}: {len(items)}")
        for x in items:
            print(f"   {x}")

    section("Add to library", added)
    section("Quantity bumped", bumped)
    section("Mana rows added (front-name)", mana_added)
    section("Removed from wishlist", wish_removed)
    if basics:
        section("Basic lands (skipped — not part of the collection; unlimited in Arena)",
                basics)
    if notfound:
        section("NOT FOUND in pool (skipped)", notfound)
    if unparsed:
        section("COULD NOT PARSE (skipped — need `<n> Name (SET) #`)", unparsed)

    # affected decks (cheap: grep deck files for a reconciled front-name)
    recon_names = {a.split(" (")[0] for a in added} | {b.split(":")[0] for b in bumped}
    if recon_names:
        decks_dir = os.path.join(REPO_ROOT, "decks")
        affected = set()
        for root, _dirs, files in os.walk(decks_dir):
            for fn in files:
                if fn.endswith(".txt"):
                    p = os.path.join(root, fn)
                    txt = open(p, encoding="utf-8").read()
                    if any(nm in txt for nm in recon_names):
                        affected.add(os.path.relpath(p, REPO_ROOT))
        if affected:
            print(f"Decks referencing a reconciled card (re-check buildability): {len(affected)}")
            for a in sorted(affected):
                print(f"   {a}")

    if not apply:
        print("\n(dry run — pass --apply to write card-library.csv / card-mana.csv / "
              "card-wishlist.csv with .bak backups)")
        return 0
    if not (added or bumped or mana_added or wish_removed):
        print("\nNothing to write.")
        return 0
    _bak_write(LIB, LIB_HEADER, lib)
    if mana_added:
        _bak_write(MANA, ["Card Name", "Mana Cost", "Mana Value", "Keywords"], mana)
    if wish_removed:
        _bak_write(WISH, wish_fields, wish)
    print("\nApplied (with .bak backups). Next:\n"
          "  make refresh                              # rebuild derived data\n"
          "  python3 scripts/verify_ingest.py <export>  # confirm the batch landed")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Reconcile crafted/owned cards from an Arena export.")
    ap.add_argument("file", help="Arena export file, or '-' for stdin")
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    ap.add_argument("--set-exact", action="store_true",
                    help="set Quantity Owned to the line's count exactly (allows a "
                         "DECREASE); default takes max(existing, line) so a deck-dump "
                         "slice can't drop a real count")
    args = ap.parse_args()
    if args.file == "-":
        lines = sys.stdin.read().splitlines()
    else:
        if not os.path.exists(args.file):
            eprint(f"No such file: {args.file}")
            return 1
        lines = open(args.file, encoding="utf-8").read().splitlines()
    return reconcile(lines, apply=args.apply, set_exact=args.set_exact)


if __name__ == "__main__":
    sys.exit(main())
