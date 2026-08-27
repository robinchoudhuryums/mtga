#!/bin/sh
# SessionStart hook body (called from .claude/settings.json).
#
# The full pytest suite (~2-4 min) used to run on EVERY session resume; one long
# session resumed ~a dozen times and spent ~half an hour re-proving an unchanged
# tree. It also caught a real regression at startup once (the _printing_of DFC
# display bug greeted a resume as "1 failed"), so the tripwire must stay armed —
# the fix is to skip only when NOTHING the suite reads has changed:
#
#   sig = HEAD tree hashes of scripts/ + tests/ + Makefile/pytest.ini blobs,
#         and ONLY when the working tree is clean for those paths.
#
# On a green run the sig is stored (gitignored); a matching sig on the next start
# skips pytest and says so. Any edit under scripts/ or tests/ — committed or not —
# reruns the full suite. Deck/CSV edits alone do not, which is correct: the suite's
# fixtures are synthetic by design (C-07), and check_all (below, always run) is the
# gate that reads live data.
set -u
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

python3 scripts/check_all.py --quiet 2>/dev/null

if ! python3 -c 'import pytest' 2>/dev/null; then
    echo '[unit tests] pytest not installed — run: make test-units'
    exit 0
fi

SIG_FILE=".cycle/.tests-green-sig"
sig=""
if [ -z "$(git status --porcelain scripts tests Makefile pytest.ini 2>/dev/null)" ]; then
    sig=$(git rev-parse HEAD:scripts HEAD:tests HEAD:Makefile HEAD:pytest.ini 2>/dev/null | tr '\n' ' ')
fi

if [ -n "$sig" ] && [ -f "$SIG_FILE" ] && [ "$(cat "$SIG_FILE")" = "$sig" ]; then
    echo "[unit tests] unchanged since last green run — skipped (rm $SIG_FILE to force)"
    exit 0
fi

result=$(python3 -m pytest 2>&1 | grep -aE '[0-9]+ (passed|failed|error)' | tail -1)
echo "[unit tests] $result"
case "$result" in
    *failed*|*error*) rm -f "$SIG_FILE" ;;
    *passed*) [ -n "$sig" ] && printf '%s' "$sig" > "$SIG_FILE" ;;
esac
exit 0
