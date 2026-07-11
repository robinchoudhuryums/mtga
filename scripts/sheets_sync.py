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
    python3 scripts/sheets_sync.py pull
    python3 scripts/sheets_sync.py push --worksheet "Library" --dry-run

The CSV itself is the interchange format, so even without this script you can
always File > Import (or download as CSV) in Google Sheets manually — this just
automates the round-trip.
"""

import argparse
import os
import sys

from lib import HEADER, DEFAULT_CSV, load_rows, write_rows, eprint

SHEET_ID_ENV = "MTGA_SHEET_ID"


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
    ws.update(range_name="A1", values=grid)
    print(f"Pushed {len(rows)} row(s) to Google Sheet worksheet {worksheet_name!r}.")
    return 0


def pull(worksheet_name, dry_run):
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
    if dry_run:
        print(f"[dry-run] would write {len(rows)} row(s) to {DEFAULT_CSV}. "
              f"Nothing written.")
        return 0
    write_rows(rows, DEFAULT_CSV)
    print(f"Pulled {len(rows)} row(s) from Google Sheet into {DEFAULT_CSV}.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Sync the card library with Google Sheets.")
    ap.add_argument("direction", choices=["push", "pull"], help="push local->sheet or pull sheet->local")
    ap.add_argument("--worksheet", default="card-library", help="worksheet/tab name")
    ap.add_argument("--dry-run", action="store_true", help="report only, transfer nothing")
    args = ap.parse_args()
    if args.direction == "push":
        return push(args.worksheet, args.dry_run)
    return pull(args.worksheet, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
