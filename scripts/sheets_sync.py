#!/usr/bin/env python3
"""Sync card-library.csv with the companion Google Sheet.

Two directions:
    push  -  overwrite the Google Sheet with the contents of the local CSV
    pull  -  overwrite the local CSV with the contents of the Google Sheet

Setup (one-time):
    1. pip install -r requirements.txt        (installs gspread + google-auth)
    2. Create a Google Cloud service account, enable the Google Sheets API,
       and download its JSON key.
    3. Share the target Google Sheet with the service account's email
       (found in the JSON key as "client_email") as an Editor.
    4. Point this script at the key and the sheet:
         export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
         export MTGA_SHEET_ID=<the long id from the sheet's URL>

Usage:
    python3 scripts/sheets_sync.py push
    python3 scripts/sheets_sync.py pull            # DRY RUN — reports what it would write
    python3 scripts/sheets_sync.py pull --apply    # actually overwrite card-library.csv
    python3 scripts/sheets_sync.py push --worksheet "Library" --dry-run

`pull` is dry-run by default and refuses a >50% row-count shrink without
--allow-shrink: it is the one authoritative overwrite of the whole inventory, and
a header-only worksheet (a cleared sheet, a partially-loaded get_all_values(), a
wrong-but-existing tab) passes both the header check and validate() — zero rows is
a "valid" library. Every sibling overwrite path (import_collection, build_pool,
build_mana) already carries a shrink guard; this one gets the same, plus the
dry-run default every other destructive tool here uses (broad-scan BS-03).

The CSV itself is the interchange format, so even without this script you can
always File > Import (or download as CSV) in Google Sheets manually — this just
automates the round-trip.
"""

import argparse
import contextlib
import csv
import io
import os
import shutil
import sys
import tempfile

from lib import (HEADER, DEFAULT_CSV, REPO_ROOT, load_rows, write_rows, eprint,
                 backup_path, atomic_write)
from validate import validate

SHEET_ID_ENV = "MTGA_SHEET_ID"
MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")
MANA_HEADER = ["Card Name", "Mana Cost", "Mana Value", "Keywords"]


def _ensure_mana_rows(rows):
    """Append a BLANK card-mana.csv row for every library name that lacks one, so
    INV-02 (every library Card Name has a mana row) survives a pull. Returns the
    names added.

    `pull()` overwrites the whole inventory and can therefore introduce cards the
    mana file has never seen — and it was the ONE row-adding path that didn't
    maintain INV-02, so the next `check_all` would fail with no hint that the pull
    caused it (broad-scan F-05). Every sibling path already does this: `app.py add`
    appends a row, and `reconcile_crafts.py` writes a deliberately BLANK one when it
    has no cost to copy, on the reasoning that a blank row keeps the invariant while
    `build_mana.py` / `/refresh` fills in the real cost later. Same reasoning here —
    a blank row is honest (we have no cost from a spreadsheet) and repairable, where
    a missing row is a hard failure.
    """
    have = set()
    if os.path.exists(MANA_CSV):
        with open(MANA_CSV, newline="", encoding="utf-8") as fh:
            existing = list(csv.reader(fh))
        header, body = (existing[0], existing[1:]) if existing else (MANA_HEADER, [])
        have = {(r[0] or "").strip().lower() for r in body if r}
    else:
        header, body = MANA_HEADER, []
    added = []
    for r in rows:
        name = (r.get("Card Name") or "").strip()
        if name and name.lower() not in have:
            have.add(name.lower())
            body.append([name, "", "", ""])
            added.append(name)
    if added:
        atomic_write(MANA_CSV,
                     lambda fh: csv.writer(fh).writerows([header] + body))
    return added


def _client():
    """Authorize a gspread client, with a friendly message if deps are missing."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        eprint(
            "ERROR: this command needs gspread + google-auth.\n"
            "       Install them with:  pip install -r requirements.txt"
        )
        raise SystemExit(2)

    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path or not os.path.exists(key_path):
        eprint(
            "ERROR: set GOOGLE_APPLICATION_CREDENTIALS to your service-account "
            "JSON key path (see the setup notes in this file's docstring)."
        )
        raise SystemExit(2)

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(key_path, scopes=scopes)
    return __import__("gspread").authorize(creds)


def _worksheet(name):
    sheet_id = os.environ.get(SHEET_ID_ENV)
    if not sheet_id:
        eprint(f"ERROR: set {SHEET_ID_ENV} to your Google Sheet's ID.")
        raise SystemExit(2)
    spreadsheet = _client().open_by_key(sheet_id)
    try:
        return spreadsheet.worksheet(name)
    except Exception:
        # Create the worksheet if it doesn't exist yet.
        return spreadsheet.add_worksheet(title=name, rows=1000, cols=len(HEADER))


def push(worksheet_name, dry_run):
    _, rows = load_rows(DEFAULT_CSV)
    grid = [HEADER] + [[r.get(c, "") or "" for c in HEADER] for r in rows]
    if dry_run:
        print(f"[dry-run] would write {len(rows)} row(s) to worksheet "
              f"{worksheet_name!r}. Nothing sent.")
        return 0
    ws = _worksheet(worksheet_name)
    ws.clear()
    # RAW so a cell whose text begins with '=', '+', '-', or '@' is stored as
    # literal text, never evaluated as a spreadsheet formula — a CSV-injection
    # guard for the companion Sheet that also keeps values (e.g. leading-zero
    # collector numbers) verbatim, without mutating the pristine local CSV
    # (audit F10). USER_ENTERED would let such a value run as a live formula.
    ws.update(range_name="A1", values=grid, value_input_option="RAW")
    print(f"Pushed {len(rows)} row(s) to Google Sheet worksheet {worksheet_name!r}.")
    return 0


_SHRINK_FLOOR = 0.5   # same floor as import_collection: refuse a >50% shrink


def pull(worksheet_name, apply=False, allow_shrink=False):
    ws = _worksheet(worksheet_name)
    grid = ws.get_all_values()
    if not grid:
        eprint("ERROR: the worksheet is empty.")
        return 1
    header, *data = grid
    if header != HEADER:
        eprint(
            "ERROR: sheet header does not match the canonical columns.\n"
            f"  expected: {HEADER}\n"
            f"  found:    {header}"
        )
        return 1
    rows = [dict(zip(HEADER, row + [""] * (len(HEADER) - len(row)))) for row in data]
    # Shrink guard (BS-03): validate() passes a header-only, ZERO-row library, so a
    # cleared / wrong / partially-loaded worksheet could replace the whole inventory
    # with nothing. Same floor and escape hatch as import_collection.
    try:
        _, local = load_rows(DEFAULT_CSV)
    except FileNotFoundError:
        local = []
    if local and len(rows) < len(local) * _SHRINK_FLOOR and not allow_shrink:
        eprint(f"ERROR: the worksheet holds {len(rows)} row(s) against "
               f"{len(local)} in {os.path.basename(DEFAULT_CSV)} — a "
               f">{int((1 - _SHRINK_FLOOR) * 100)}% shrink. A cleared sheet or a "
               f"wrong tab looks exactly like this. Pass --allow-shrink if the "
               f"shrink is real. Nothing written.")
        return 1
    if not apply:
        print(f"[dry-run] would write {len(rows)} row(s) to {DEFAULT_CSV} "
              f"(replacing {len(local)}). Nothing written — pass --apply to write.")
        return 0
    # pull() overwrites the canonical inventory in place, so the incoming data
    # must clear the SAME validate() gate every other write path honors — a sheet
    # with a matching header but bad rows (non-numeric quantities, duplicate
    # printings) must not be able to overwrite the local CSV. Write to a temp file
    # in the target directory, validate it, and only then back up + atomically
    # promote it; on any failure the real CSV is left untouched.
    target = os.path.abspath(DEFAULT_CSV)
    fd, tmp = tempfile.mkstemp(suffix=".csv", dir=os.path.dirname(target))
    os.close(fd)
    try:
        write_rows(rows, tmp, backup=False)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = validate(tmp)
        if rc != 0:
            eprint("ERROR: the pulled data failed validation; local CSV left untouched.")
            for ln in [l for l in buf.getvalue().splitlines() if l.strip()][-8:]:
                eprint(f"  {ln}")
            return 1
        if os.path.exists(target):
            backup = backup_path(target)  # shared collision-free naming (audit F22)
            shutil.copy2(target, backup)
            print(f"Backed up existing CSV to {os.path.basename(backup)} before overwrite.")
            # Carry the target's own mode across, exactly as lib.atomic_write does:
            # mkstemp creates 0600 and os.replace keeps the TEMP's mode, so this
            # promote-my-own-temp path silently flipped card-library.csv 644 -> 600 —
            # the regression atomic_write documents fixing, reintroduced by the one
            # caller that stages its own file (broad-scan Batch G). Masked locally
            # because a git checkout resets modes.
            shutil.copymode(target, tmp)
        else:
            os.chmod(tmp, 0o644)
        os.replace(tmp, target)
        tmp = None
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)
    print(f"Pulled {len(rows)} row(s) from Google Sheet into {DEFAULT_CSV}.")
    # Only AFTER the library write lands, so a rejected pull can't strand the mana
    # file out of step with it — the ordering app.py's add()/remove() use for the
    # same reason.
    added = _ensure_mana_rows(rows)
    if added:
        shown = ", ".join(added[:8]) + ("…" if len(added) > 8 else "")
        print(f"Added {len(added)} BLANK card-mana.csv row(s) to keep INV-02: {shown}\n"
              f"  Run build_mana.py (or /refresh) to fill in cost/keywords.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Sync the card library with Google Sheets.")
    ap.add_argument("direction", choices=["push", "pull"], help="push local->sheet or pull sheet->local")
    ap.add_argument("--worksheet", default="card-library", help="worksheet/tab name")
    ap.add_argument("--dry-run", action="store_true", help="report only, transfer nothing")
    ap.add_argument("--apply", action="store_true",
                    help="pull only: actually overwrite card-library.csv "
                         "(pull is a DRY RUN by default; push still writes unless --dry-run)")
    ap.add_argument("--allow-shrink", action="store_true",
                    help="pull only: permit replacing the library with <50%% of its rows")
    args = ap.parse_args()
    if args.direction == "push":
        return push(args.worksheet, args.dry_run)
    return pull(args.worksheet, apply=args.apply and not args.dry_run,
                allow_shrink=args.allow_shrink)


if __name__ == "__main__":
    sys.exit(main())
