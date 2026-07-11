#!/usr/bin/env python3
"""Validate card-library.csv for structural and data integrity.

Checks:
  * Header row matches the canonical column set exactly.
  * Every row has all 8 columns (csv.DictReader flags short/long rows).
  * Card Name is non-empty.
  * Quantity Owned is blank or a non-negative integer.
  * No duplicate (Card Name, Set Code, Collector #) printings.

Warnings (non-fatal) are reported for likely-incomplete rows, e.g. a card with
no Type or Card Text, so you can spot rows that still need enrichment.

Exit code is 0 when there are no errors, 1 when errors are found. Warnings alone
do not fail the run.

Usage:
    python3 scripts/validate.py [path/to/card-library.csv]
"""

import sys

from lib import HEADER, DEFAULT_CSV, load_rows, eprint


def validate(path):
    errors = []
    warnings = []

    try:
        header, rows = load_rows(path)
    except FileNotFoundError:
        eprint(f"ERROR: file not found: {path}")
        return 1

    # --- Header check -------------------------------------------------------
    if header != HEADER:
        errors.append(
            "Header mismatch.\n"
            f"  expected: {HEADER}\n"
            f"  found:    {header}"
        )
        # A wrong header makes per-row column checks unreliable, so stop here.
        _report(errors, warnings)
        return 1

    # --- Per-row checks -----------------------------------------------------
    seen = {}
    for i, row in enumerate(rows, start=2):  # row 1 is the header
        name = (row.get("Card Name") or "").strip()

        # DictReader stores overflow columns under a None key and missing
        # trailing columns as None values — both indicate a malformed row.
        if None in row:
            errors.append(f"Row {i}: too many columns (extra data: {row[None]!r})")
        if any(row.get(col) is None for col in HEADER):
            missing = [col for col in HEADER if row.get(col) is None]
            errors.append(f"Row {i}: missing column(s): {', '.join(missing)}")

        if not name:
            errors.append(f"Row {i}: Card Name is empty")

        qty = (row.get("Quantity Owned") or "").strip()
        if qty:
            if not qty.isdigit():
                errors.append(
                    f"Row {i} ({name}): Quantity Owned must be a non-negative "
                    f"integer or blank, got {qty!r}"
                )

        # Duplicate printing detection: same card + set + collector number.
        key = (
            name.lower(),
            (row.get("Set Code") or "").strip().lower(),
            (row.get("Collector #") or "").strip().lower(),
        )
        if name:
            if key in seen:
                errors.append(
                    f"Row {i} ({name}): duplicate printing of row {seen[key]} "
                    f"(same Card Name + Set Code + Collector #)"
                )
            else:
                seen[key] = i

        # Soft warnings for rows that look unfinished.
        if name and not (row.get("Type") or "").strip():
            warnings.append(f"Row {i} ({name}): Type is blank")
        if name and not (row.get("Card Text") or "").strip():
            warnings.append(f"Row {i} ({name}): Card Text is blank")

    _report(errors, warnings)
    print(f"\nChecked {len(rows)} row(s): {len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


def _report(errors, warnings):
    for w in warnings:
        eprint(f"WARN:  {w}")
    for e in errors:
        eprint(f"ERROR: {e}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    sys.exit(validate(target))
