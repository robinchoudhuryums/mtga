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
    python3 scripts/sheets_sync.py check           # is the setup complete? writes nothing
    python3 scripts/sheets_sync.py push
    python3 scripts/sheets_sync.py pull            # DRY RUN — reports what it would write
    python3 scripts/sheets_sync.py pull --apply    # actually overwrite card-library.csv
    python3 scripts/sheets_sync.py push --worksheet "Library" --dry-run

Start with `check`. The setup has four independent parts (two packages, a key file,
a sheet id) plus a share on the Google side, and each used to announce itself only
by failing a real transfer — so a missing share and a typo'd tab name looked alike.
`check` reports all of them and moves no data.

BOTH directions refuse a >50% row-count shrink without --allow-shrink. `pull` is the
authoritative overwrite of the whole inventory, and a header-only worksheet (a cleared
sheet, a partially-loaded get_all_values(), a wrong-but-existing tab) passes both the
header check and validate() — zero rows is a "valid" library (broad-scan BS-03). `push`
CLEARS the tab before writing, so a short local CSV would destroy the remote copy you
would otherwise recover from; it got the mirror guard in BS3-03. Every sibling overwrite
path (import_collection, build_pool, build_mana) carries the same floor. `pull` is
additionally a dry run by default, like every other destructive tool here.

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


def _spreadsheet():
    sheet_id = os.environ.get(SHEET_ID_ENV)
    if not sheet_id:
        eprint(f"ERROR: set {SHEET_ID_ENV} to your Google Sheet's ID.")
        raise SystemExit(2)
    return _client().open_by_key(sheet_id)


def _worksheet(name, create=False):
    """Open worksheet `name`. Creates it ONLY when `create` is set.

    It used to create unconditionally, on a bare `except Exception` — so a typo in
    `--worksheet` on the READ side made `pull` add an empty tab to the operator's
    spreadsheet and then report "the worksheet is empty", which is a read operation
    silently mutating the remote document, and a misleading error on top of it. The
    blanket except also swallowed auth and network failures and turned them into an
    add_worksheet attempt, so a credentials problem surfaced as an unrelated error.
    """
    spreadsheet = _spreadsheet()
    try:
        return spreadsheet.worksheet(name)
    except Exception as e:
        if not create:
            try:
                have = ", ".join(repr(w.title) for w in spreadsheet.worksheets())
            except Exception:            # the failure was not "no such tab"
                eprint(f"ERROR: could not open worksheet {name!r}: {e}")
                raise SystemExit(2)
            eprint(f"ERROR: no worksheet named {name!r} in this spreadsheet.\n"
                   f"       Tabs present: {have or '(none)'}\n"
                   f"       Reading will not create one — pass --worksheet with an "
                   f"existing tab name.")
            raise SystemExit(2)
        return spreadsheet.add_worksheet(title=name, rows=1000, cols=len(HEADER))


_SHRINK_FLOOR = 0.5   # same floor as import_collection: refuse a >50% shrink


def push(worksheet_name, dry_run, allow_shrink=False):
    _, rows = load_rows(DEFAULT_CSV)
    grid = [HEADER] + [[r.get(c, "") or "" for c in HEADER] for r in rows]
    if dry_run:
        print(f"[dry-run] would write {len(rows)} row(s) to worksheet "
              f"{worksheet_name!r}. Nothing sent.")
        return 0
    ws = _worksheet(worksheet_name, create=True)
    # Push CLEARS the tab, so it is an overwrite of the operator's other copy and it
    # deserves the same floor as its mirror. `pull` has had one since BS-03 and this
    # direction had none at all: every reason a local CSV can be short — an aborted
    # import, a bad merge, a half-written file — would have been propagated straight
    # over the Sheet, destroying the copy you would otherwise have pulled BACK from.
    # Same floor, same escape hatch, same wording as pull.
    if not allow_shrink:
        try:
            remote = max(len(ws.get_all_values()) - 1, 0)   # minus the header row
        except Exception:
            remote = 0
        if remote and len(rows) < remote * _SHRINK_FLOOR:
            eprint(f"ERROR: {os.path.basename(DEFAULT_CSV)} holds {len(rows)} row(s) "
                   f"against {remote} in worksheet {worksheet_name!r} — a "
                   f">{int((1 - _SHRINK_FLOOR) * 100)}% shrink. A half-written or "
                   f"partially-imported local CSV looks exactly like this, and push "
                   f"CLEARS the tab. Pass --allow-shrink if the shrink is real. "
                   f"Nothing sent.")
            return 1
    # WRITE FIRST, then trim — never clear-then-write. `ws.clear()` followed by a
    # separate `ws.update()` leaves a window in which an auth expiry, a transient 5xx or
    # a dropped connection ends with the tab EMPTY: the Sheet is the one REMOTE copy the
    # shrink guard above exists to protect, and the failure destroyed exactly what `pull`
    # would have recovered from (BS4-16). Every LOCAL write in this repo stages and then
    # promotes (`lib.atomic_write`); this was the one overwrite with no equivalent.
    #
    # Overwriting in place is the closest thing the Sheets API offers to that: after a
    # successful update the new grid occupies A1..; only the rows BELOW it are stale, and
    # those are deleted afterwards. A failure at any point leaves either the old content
    # or the new — never nothing.
    #
    # RAW so a cell whose text begins with '=', '+', '-', or '@' is stored as
    # literal text, never evaluated as a spreadsheet formula — a CSV-injection
    # guard for the companion Sheet that also keeps values (e.g. leading-zero
    # collector numbers) verbatim, without mutating the pristine local CSV
    # (audit F10). USER_ENTERED would let such a value run as a live formula.
    try:
        previous = len(ws.get_all_values())
    except Exception:
        previous = 0
    ws.update(range_name="A1", values=grid, value_input_option="RAW")
    # Trim any rows the OLD contents left below the new grid. Best-effort and
    # non-fatal: the data is already correct at this point, and a failed tidy-up must
    # not report the push as failed (it would invite a re-push of a correct Sheet).
    if previous > len(grid):
        try:
            ws.delete_rows(len(grid) + 1, previous)
        except Exception as e:
            eprint(f"WARN:  pushed {len(rows)} row(s), but could not delete "
                   f"{previous - len(grid)} leftover row(s) below the new data "
                   f"({e}). The pushed rows are correct; clear the tail by hand.")
    print(f"Pushed {len(rows)} row(s) to Google Sheet worksheet {worksheet_name!r}.")
    return 0


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


def check_setup(worksheet_name):
    """Report whether this machine can talk to the Sheet, WITHOUT moving any data.

    The setup is four separate things — two packages, a key file, a sheet id, and a
    share on the Google side — and until this existed the only way to find out which
    one was missing was to run a real transfer and read whichever error came back
    first. That is a bad way to learn you forgot to share the sheet with the service
    account, and it is why the round-trip sat documented-but-unused: every failure
    looked the same from outside. Read-only; creates nothing.
    """
    ok = True
    try:
        import gspread            # noqa: F401
        from google.oauth2.service_account import Credentials  # noqa: F401
        print("  ✓ gspread + google-auth installed")
    except ImportError:
        print("  ✗ gspread / google-auth NOT installed — pip install -r requirements.txt")
        ok = False
    key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not key:
        print("  ✗ GOOGLE_APPLICATION_CREDENTIALS is not set")
        ok = False
    elif not os.path.exists(key):
        print(f"  ✗ GOOGLE_APPLICATION_CREDENTIALS points at a missing file: {key}")
        ok = False
    else:
        print(f"  ✓ service-account key present ({os.path.basename(key)})")
    if not os.environ.get(SHEET_ID_ENV):
        print(f"  ✗ {SHEET_ID_ENV} is not set")
        ok = False
    else:
        print(f"  ✓ {SHEET_ID_ENV} set")
    if not ok:
        print("\nSetup incomplete — see the docstring at the top of this file.")
        return 1
    try:
        spreadsheet = _spreadsheet()
        titles = [w.title for w in spreadsheet.worksheets()]
    except SystemExit:
        raise
    except Exception as e:
        print(f"  ✗ could not open the spreadsheet ({type(e).__name__}: {e})\n"
              f"    The commonest cause is not having SHARED the sheet with the "
              f"service account's client_email as an Editor.")
        return 1
    print(f"  ✓ spreadsheet opened — tabs: {', '.join(repr(t) for t in titles)}")
    if worksheet_name in titles:
        rows = max(len(spreadsheet.worksheet(worksheet_name).get_all_values()) - 1, 0)
        _, local = load_rows(DEFAULT_CSV)
        print(f"  ✓ worksheet {worksheet_name!r}: {rows} row(s) "
              f"against {len(local)} local")
    else:
        print(f"  · worksheet {worksheet_name!r} does not exist yet — `push` will "
              f"create it; `pull` will refuse.")
    print("\nSetup OK. Nothing was written.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Sync the card library with Google Sheets.")
    ap.add_argument("direction", choices=["push", "pull", "check"],
                    help="push local->sheet, pull sheet->local, or check the setup")
    ap.add_argument("--worksheet", default="card-library", help="worksheet/tab name")
    ap.add_argument("--dry-run", action="store_true", help="report only, transfer nothing")
    ap.add_argument("--apply", action="store_true",
                    help="pull only: actually overwrite card-library.csv "
                         "(pull is a DRY RUN by default; push still writes unless --dry-run)")
    ap.add_argument("--allow-shrink", action="store_true",
                    help="permit an overwrite that shrinks the destination by >50%% "
                         "(applies to BOTH directions)")
    args = ap.parse_args()
    if args.direction == "check":
        return check_setup(args.worksheet)
    if args.direction == "push":
        return push(args.worksheet, args.dry_run, allow_shrink=args.allow_shrink)
    return pull(args.worksheet, apply=args.apply and not args.dry_run,
                allow_shrink=args.allow_shrink)


if __name__ == "__main__":
    sys.exit(main())
