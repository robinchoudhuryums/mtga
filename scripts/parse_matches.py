#!/usr/bin/env python3
"""Parse MTG Arena match results out of Player.log into matches.csv.

Arena's "Detailed Logs (Plugin Support)" setting (Settings -> Account) makes the client
write match events to a local log. That is free — it is the same feed every third-party
tracker reads; their subscriptions buy cloud analytics, not log access. Collection data
was locked down years ago, which is why ingestion has to undercount; MATCH results were
not.

WHAT IT READS. Two line shapes, and BOTH are required:

    [UnityCrossThreadLogger]7/27/2026 7:08:46 PM: Match to QAGEO...UI: MatchGameRoomStateChangedEvent
    { "timestamp": "...", "matchGameRoomStateChangedEvent": { ... "finalMatchResult": {...} } }

The JSON carries the result and both players' seats — but NOT which seat is yours. The
local player's userId appears only in the `Match to <userId>:` header prefix, so a paste
of the JSON alone is unparseable: every result would be a coin flip between win and loss.
`--me <userId>` overrides when the header is missing.

WHAT IT WRITES. One row per match in matches.csv, deduped by Arena's matchId so
re-pasting an overlapping log is safe. Deliberately stores NO userId and NO playerName —
neither is needed to compute a win rate, and a match log is not a place to accumulate
identity. Opponent DECK (courseId) is kept; that is an archetype, not a person.

DECK IDENTITY. `courseId` is Arena's deck identifier ("Avatar_Basic_BlackPanther_MSH" for
a precon). It is not the repo's deck id and there is no way to derive one from the other,
so the mapping is learned rather than guessed:
  * put `#: arena: <courseId>` in a deck file and matches resolve to that deck id, or
  * pass `--deck <id>` to tag every match in one paste, or
  * neither, and the row keeps its courseId with a blank Deck — the report lists unmapped
    courseIds so you know what to add. Nothing is dropped for being unmapped.

Usage:
    python3 scripts/parse_matches.py session.log            # dry run
    python3 scripts/parse_matches.py - --apply              # from stdin
    python3 scripts/parse_matches.py - --apply --deck 12    # tag this session's deck
    python3 scripts/parse_matches.py --report               # win/loss per deck

Extract on the machine running Arena (macOS shown; Player.log is overwritten on every
launch, so grab it before relaunching):

    p=~/Library/Logs/"Wizards Of The Coast"/MTGA
    grep -hE 'Match to .*MatchGameRoomStateChangedEvent|"finalMatchResult"' "$p"/Player*.log | pbcopy
"""

import argparse
import csv
import datetime
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import REPO_ROOT, atomic_write, csv_schema_error, eprint  # noqa: E402

MATCHES_CSV = os.path.join(REPO_ROOT, "matches.csv")
HEADER = ["Date", "Match ID", "Deck", "Course ID", "Event", "Result",
          "Games Won", "Games Lost", "Opponent Course", "Reason"]

# `Match to <userId>:` — the ONLY place the local player's seat is identified.
# The id charset is deliberately broad ([A-Za-z0-9] + separators): the original
# [A-Z0-9]+ TRUNCATED an id containing lowercase, so the truncated id matched no
# seat and every match was skipped — the safe direction (skip, never guess a
# seat), but the warning blamed a missing header that was present (batch 5).
_ME_RE = re.compile(r"Match to ([A-Za-z0-9_-]+):")
# The log line's own timestamp is LOCAL; the JSON's epoch field is UTC, and using it files
# an evening session under the next day (the sample: header 7/27, epoch 7/28).
_DATE_RE = re.compile(r"\](\d{1,2})/(\d{1,2})/(\d{4})\s")
# Below this many matches a percentage is noise, so the report refuses to print one.
_MIN_SAMPLE = 20


def _local_date(line):
    """YYYY-MM-DD from a UnityCrossThreadLogger line's LOCAL timestamp, or ''."""
    m = _DATE_RE.search(line or "")
    if not m:
        return ""
    mo, day, yr = (int(x) for x in m.groups())
    return f"{yr:04d}-{mo:02d}-{day:02d}"


def _utc_date(stamp):
    """YYYY-MM-DD from the JSON's epoch-ms `timestamp`, or ''.

    A FALLBACK only. It is UTC, so an evening session files a day late (in the sample:
    header 7/27, epoch 7/28) — which is exactly why `_local_date` wins when a header is
    present. But a date that is occasionally a day off still beats a blank one: a blank
    sorts to the top of matches.csv and makes the row impossible to scope in time."""
    try:
        ms = int(str(stamp).strip())
    except (TypeError, ValueError):
        return ""
    if ms <= 0:
        return ""
    try:
        return datetime.datetime.fromtimestamp(
            ms / 1000, datetime.timezone.utc).strftime("%Y-%m-%d")
    except (OverflowError, OSError, ValueError):
        return ""


def parse_log(text, me=None):
    """(rows, warnings) — one dict per completed match, oldest first.

    Walks the log in order, remembering the most recent `Match to <userId>` header, then
    resolves each finalMatchResult against it."""
    rows, warnings = [], []
    current_me, current_date = me, ""
    for raw in (text or "").splitlines():
        hit = _ME_RE.search(raw)
        if hit:
            if me is None:
                current_me = hit.group(1)
            d = _local_date(raw)
            if d:
                current_date = d
        # Deliberately keyed on the EVENT, not on `"finalMatchResult"`. A truncated paste
        # is the expected failure here (the extraction is hand-run, and a width cap or a
        # clipboard cut takes the tail), and `finalMatchResult` sits LATE in the line —
        # after both players' seats — so any realistic cut removes the marker. Testing for
        # it meant a truncated match line matched nothing and was dropped in SILENCE: the
        # run reported success while losing a match. Matching the event key, which sits
        # near the front, means a cut line still reaches the JSON parse and gets reported.
        start = raw.find("{")
        if start < 0 or '"matchGameRoomStateChangedEvent"' not in raw:
            continue
        try:
            data = json.loads(raw[start:])
        except json.JSONDecodeError as e:
            warnings.append(f"a match-event line did not parse as JSON ({e}) — the paste "
                            f"looks TRUNCATED, so a match may be missing from this run. "
                            f"Re-extract without a width cap and re-run (already-recorded "
                            f"matches dedupe, so re-pasting is safe).")
            continue
        try:
            info = data["matchGameRoomStateChangedEvent"]["gameRoomInfo"]
            cfg, fin = info["gameRoomConfig"], info["finalMatchResult"]
            players = cfg["reservedPlayers"]
        except (KeyError, TypeError):
            continue                       # a state change that isn't a completed match
        if not current_me:
            warnings.append(f"match {fin.get('matchId','?')[:8]} skipped: no `Match to "
                            f"<userId>` header seen, so which seat is yours is unknown. "
                            f"Re-extract including the header lines, or pass --me <userId>.")
            continue
        mine = next((p for p in players if p.get("userId") == current_me), None)
        if mine is None:
            warnings.append(f"match {fin.get('matchId','?')[:8]} skipped: no seat matches "
                            f"the local userId")
            continue
        opp = next((p for p in players if p.get("userId") != current_me), {})
        results = fin.get("resultList") or []
        match_res = next((r for r in results if r.get("scope") == "MatchScope_Match"), None)
        games = [r for r in results if r.get("scope") == "MatchScope_Game"]
        if match_res is None:
            warnings.append(f"match {fin.get('matchId','?')[:8]} has no match-scope result")
            continue
        my_team = mine.get("teamId")
        win_team = match_res.get("winningTeamId")
        # A draw reports no winning team (or one belonging to neither seat).
        result = "D" if win_team in (None, 0) else ("W" if win_team == my_team else "L")
        rows.append({
            "Date": current_date or _utc_date(data.get("timestamp")),
            "Match ID": fin.get("matchId", ""),
            "Deck": "",
            "Course ID": mine.get("courseId", ""),
            "Event": mine.get("eventId", ""),
            "Result": result,
            "Games Won": sum(1 for g in games if g.get("winningTeamId") == my_team),
            "Games Lost": sum(1 for g in games
                              if g.get("winningTeamId") not in (None, 0, my_team)),
            "Opponent Course": opp.get("courseId", ""),
            "Reason": (fin.get("matchCompletedReason", "")
                       .replace("MatchCompletedReasonType_", "")),
        })
    return rows, warnings


def arena_deck_map():
    """{courseId: deck_id} from `#: arena:` headers on deck files. Empty if deck.py is
    unavailable, so the parser still works standalone."""
    try:
        import deck as dk
        out = {}
        for d in dk.discover_decks():
            meta, _ = dk.parse_deck_file(d["path"])
            course = (meta.get("arena") or "").strip()
            if course:
                out[course] = d["id"]
        return out
    except Exception:
        return {}


def fresh_rows(rows, existing):
    """The parsed rows not already recorded — deduped by Match ID against `existing`
    AND against each other.

    The within-paste half is the part that was missing (BS4-15). The filter compared only
    against the CSV, so two copies of one `finalMatchResult` in a SINGLE paste — which is
    what concatenating two overlapping log extracts produces — both passed and were both
    written, double-counting that match in `--report` permanently. The module docstring
    promises "deduped by Arena's matchId so re-pasting an overlapping log is safe", and
    the JSON-truncation warning actively tells the user to re-paste, so the documented-safe
    action was the one that corrupted the record.

    A row with NO Match ID is never deduped, against the CSV or within the paste: "" is
    not an identity, and treating it as one silently dropped every id-less match after the
    first as "already recorded" — which reads as data, not as a gap (broad-scan batch 5).
    """
    known = {mid for r in existing if (mid := (r.get("Match ID") or "").strip())}
    seen_here, out = set(), []
    for r in rows:
        mid = (r.get("Match ID") or "").strip()
        if not mid:
            out.append(r)
            continue
        if mid in known or mid in seen_here:
            continue
        seen_here.add(mid)
        out.append(r)
    return out


def load_matches(path=MATCHES_CSV):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def write_matches(rows, path=MATCHES_CSV):
    # Same F-02 mirror guard as the two builders (broad-scan Batch G): `--out`
    # accepts any path, and this writer emits only HEADER — pointed at a canonical
    # CSV it would overwrite it with the match schema.
    problem = csv_schema_error(path, HEADER)
    if problem:
        raise ValueError(problem)

    def _w(fh):
        w = csv.DictWriter(fh, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in sorted(rows, key=lambda x: (x.get("Date") or "", x.get("Match ID") or "")):
            w.writerow({c: r.get(c, "") for c in HEADER})
    atomic_write(path, _w)


def _wilson(wins, n, z=1.96):
    """95% Wilson score interval for a win rate — correct at small n, where the naive
    normal approximation is not. Returns (low, high) as percentages."""
    if not n:
        return (0.0, 0.0)
    p = wins / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * max(0.0, centre - half), 100 * min(1.0, centre + half))


def report(rows):
    """Win/loss per deck, with an explicit refusal to read a small sample.

    Printing `57%` off 7 games is worse than printing nothing: it invites a tuning
    decision the data cannot support. Same restraint `count_conf` shows for role counts —
    a number that looks certain when it isn't is the expensive kind of wrong."""
    if not rows:
        print("No matches recorded yet.")
        return 0
    by = {}
    # A row whose Result is blank or not one of W/L/D is COUNTED SEPARATELY and reported,
    # never folded into a bucket. `b[r.get("Result", "L")]` only defaulted when the KEY was
    # absent, so a row with `Result=""` (hand-edited, or a legacy CSV) incremented `b[""]`
    # — a bucket printed in no column and excluded from `n = W+L`. The header count and
    # the per-deck totals then disagreed with nothing said, which is the "reads as data,
    # not as a gap" failure this module is otherwise built to avoid (BS4-24).
    unreadable = []
    for r in rows:
        key = r.get("Deck") or f"(unmapped: {r.get('Course ID') or '?'})"
        b = by.setdefault(key, {"W": 0, "L": 0, "D": 0})
        res = (r.get("Result") or "").strip().upper()
        if res not in ("W", "L", "D"):
            unreadable.append((key, r.get("Date") or "?", r.get("Result") or ""))
            continue
        b[res] += 1
    print(f"{len(rows)} match(es) recorded\n")
    print(f"  {'Deck':32}  {'W':>3} {'L':>3} {'D':>3}   Read")
    print("  " + "-" * 68)
    for key in sorted(by, key=lambda k: -(by[k]["W"] + by[k]["L"] + by[k]["D"])):
        b = by[key]
        n = b["W"] + b["L"]
        if n < _MIN_SAMPLE:
            read = f"n={n} — too few to read (need ~{_MIN_SAMPLE})"
        else:
            lo, hi = _wilson(b["W"], n)
            read = f"{100*b['W']/n:.0f}%  (95% CI {lo:.0f}–{hi:.0f}%)"
        print(f"  {key[:32]:32}  {b['W']:>3} {b['L']:>3} {b['D']:>3}   {read}")
    if unreadable:
        print(f"\n⚠ {len(unreadable)} row(s) have an unreadable Result and are in NO "
              f"column above — the per-deck totals therefore do not sum to "
              f"{len(rows)}. Fix the Result cell (W/L/D) in matches.csv:")
        for key, date, raw in unreadable[:10]:
            print(f"    {date}  {key[:32]:32} Result={raw!r}")
        if len(unreadable) > 10:
            print(f"    … and {len(unreadable) - 10} more")
    unmapped = sorted({r["Course ID"] for r in rows if not r.get("Deck") and r.get("Course ID")})
    if unmapped:
        print(f"\n{len(unmapped)} unmapped Arena deck(s). Add `#: arena: <courseId>` to the "
              f"matching deck file to attribute these:")
        for c in unmapped[:10]:
            print(f"   {c}")
    print("\nA win rate separates a BROKEN deck from a fine one; it will not separate a "
          "55% deck from a 45% one without hundreds of games. Read it for disasters.")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="Parse Arena match results from Player.log into matches.csv.")
    ap.add_argument("source", nargs="?", help="log file, or '-' for stdin")
    ap.add_argument("--apply", action="store_true", help="write matches.csv (default: dry run)")
    ap.add_argument("--deck", help="tag every match in this paste with a repo deck id")
    ap.add_argument("--me", help="your Arena userId, if the paste lacks the `Match to` headers")
    ap.add_argument("--report", action="store_true", help="win/loss per deck from matches.csv")
    ap.add_argument("--out", default=MATCHES_CSV)
    args = ap.parse_args()

    if args.report and not args.source:
        return report(load_matches(args.out))
    if not args.source:
        ap.error("give a log file (or '-' for stdin), or use --report")

    try:
        text = sys.stdin.read() if args.source == "-" else \
            open(args.source, encoding="utf-8", errors="replace").read()
    except OSError as e:
        eprint(f"Could not read {args.source!r}: {e}")
        return 1

    rows, warnings = parse_log(text, me=args.me)
    for w in warnings:
        eprint(f"WARN:  {w}")
    if not rows:
        eprint("No completed matches found. Check that Detailed Logs (Plugin Support) is "
               "enabled in Arena, and that the paste includes the `Match to ...` header "
               "lines as well as the JSON.")
        return 1

    course_map = arena_deck_map()
    for r in rows:
        r["Deck"] = args.deck or course_map.get(r["Course ID"], "")

    existing = load_matches(args.out)
    # A row with NO matchId must never dedupe against another blank — "" in the
    # known-set silently dropped every subsequent id-less match as "already
    # recorded", which reads as data, not as a gap (broad-scan batch 5).
    fresh = fresh_rows(rows, existing)

    print(f"Found {len(rows)} completed match(es); {len(fresh)} new, "
          f"{len(rows) - len(fresh)} already recorded.")
    for r in fresh:
        deck_label = r["Deck"] or f"(unmapped {r['Course ID']})"
        print(f"   {r['Date']}  {r['Result']}  {r['Games Won']}-{r['Games Lost']}  "
              f"{deck_label}  vs {r['Opponent Course'] or '?'}  [{r['Event']}]")
    if not args.apply:
        print("\n(dry run — pass --apply to write matches.csv)")
        return 0
    if not fresh:
        print("\nNothing new to write.")
        return 0
    write_matches(existing + fresh, args.out)
    print(f"\nWrote {args.out} ({len(existing) + len(fresh)} total). "
          f"See the record with: parse_matches.py --report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
