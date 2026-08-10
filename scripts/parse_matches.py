#!/usr/bin/env python3
"""Parse MTG Arena match results out of Player.log into matches.csv.

Arena's "Detailed Logs (Plugin Support)" setting (Settings -> Account) makes the client
write match events to a local log. That is free — it is the same feed every third-party
tracker reads; their subscriptions buy cloud analytics, not log access. Collection data
was locked down years ago, which is why ingestion has to undercount; MATCH results were
not.

WHAT IT READS. Three line shapes. The first two are required; the third is what makes
the record attributable to a deck:

    [UnityCrossThreadLogger]7/27/2026 7:08:46 PM: Match to QAGEO...UI: MatchGameRoomStateChangedEvent
    { "timestamp": "...", "matchGameRoomStateChangedEvent": { ... "finalMatchResult": {...} } }
    [UnityCrossThreadLogger]==> EventSetDeckV3 {"id":"...","request":"{\"EventName\":\"Play\",
        \"Summary\":{\"DeckId\":\"<guid>\",...,\"Name\":\"07 Earth's Mightiest\",...}}"}

The JSON carries the result and both players' seats — but NOT which seat is yours. The
local player's userId appears only in the `Match to <userId>:` header prefix, so a paste
of the JSON alone is unparseable: every result would be a coin flip between win and loss.
`--me <userId>` overrides when the header is missing.

WHAT IT WRITES. One row per match in matches.csv, deduped by Arena's matchId so
re-pasting an overlapping log is safe. Deliberately stores NO userId and NO playerName —
neither is needed to compute a win rate, and a match log is not a place to accumulate
identity.

DECK IDENTITY — and the trap that cost a whole first pass. `courseId` on a seat LOOKS
like a deck id and is not: every value the sample produced was an `Avatar_Basic_*`
cosmetic (BlackPanther, Galactus, Kaito…), i.e. the AVATAR, which is a global profile
setting a player changes independently of the deck. Nine matches were recorded against it
before anyone read the values, and the two columns are named `My Avatar` /
`Opponent Avatar` now so the next reader cannot repeat it. It stays recorded — the
opponent's avatar is a cosmetic, not a person — but it identifies nothing.

The deck you actually played is in `EventSetDeckV3`, which Arena writes when it submits a
deck for an event, seconds before the match starts. It carries the Arena deck NAME, the
stable `DeckId` GUID, and a `LastPlayed` local timestamp. Each match is attributed to the
selection with the latest `LastPlayed` at or before the match's own header timestamp
(falling back to log ORDER when a paste lacks timestamps), so a session that switches
decks mid-way attributes each match correctly. A selection more than
`_MAX_SELECTION_GAP_H` hours before a match is NOT used — that is a rotated log, not a
deck choice.

Arena name -> repo deck id resolves in three steps, most explicit first:
  * `--deck <id>` tags every match in the paste, overriding everything;
  * `#: arena: <Arena deck name>` or `#: arena: <DeckId GUID>` in a deck file (comma-
    separate several); the GUID survives a rename, the name is the one you can type;
  * failing both, the leading NUMBER of the Arena name — "07 Earth's Mightiest" -> deck
    7, "19b …" -> deck 19b — accepted only when that deck id exists. The run PRINTS every
    name it resolved and how, because a heuristic that assigns data has to show its work.
A match that resolves to nothing keeps its Arena deck name with a blank Deck; the report
lists what is unattributed. Nothing is dropped for being unmapped.

Those headers KEEP THEMSELVES CURRENT: every ingest also harvests the paste's deck
summaries (EventSetDeckV3 = the deck submitted for an event, DeckUpsertDeckV3 = the deck
just saved/renamed/imported — both nest the same `{"DeckId":…,"Name":…}` object) and, on
--apply, writes any new or renamed header before resolving the matches, so header upkeep
is not a separate command nobody runs. `--map-decks` is the roster-scale version of the
same pass — feed it a paste grepped for `==> (EventSetDeckV3|DeckUpsertDeckV3)` and it
maps every deck the client has touched. (NOT DeckGetDeckSummariesV3: Arena logs its
request and a bare ack with no payload — measured 0 decks from 5 calls.) Dry-run by
default; two Arena decks claiming one repo deck write NOTHING, because a header naming
the wrong one of two is worse than no header — the parser would then attribute matches
to it with confidence.

Usage:
    python3 scripts/parse_matches.py session.log            # dry run
    python3 scripts/parse_matches.py - --apply              # from stdin
    python3 scripts/parse_matches.py - --apply --deck 12    # tag this session's deck
    python3 scripts/parse_matches.py session.log --map-decks           # dry run
    python3 scripts/parse_matches.py session.log --map-decks --apply   # write headers
    python3 scripts/parse_matches.py --report               # win/loss per deck

Extract on the machine running Arena (macOS shown; Player.log is overwritten on every
launch, so grab it before relaunching):

    p=~/Library/Logs/"Wizards Of The Coast"/MTGA
    grep -hE 'Match to .*MatchGameRoomStateChangedEvent|"finalMatchResult"|==> EventSetDeckV3' \
        "$p"/Player*.log | pbcopy

Better: don't extract by hand at all. A launchd job that appends the filtered lines to a
rolling archive every 15 minutes makes the overwrite-on-launch data loss structurally
impossible (the 2026-07-27 match is a permanent casualty of not having one); re-ingesting
the archive is safe because dedup is by matchId. The setup block lives in
.claude/commands/log-matches.md, Stage 0.
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
from lib import (MATCHES_CSV, REPO_ROOT, atomic_write,  # noqa: E402,F401
                 csv_schema_error, eprint)
HEADER = ["Date", "Match ID", "Deck", "Arena Deck", "Arena Deck ID", "My Avatar",
          "Event", "Result", "Games Won", "Games Lost", "Opponent Avatar", "Reason"]

# The pre-attribution column names, kept readable so an unmigrated matches.csv is not
# silently blanked on the next write. `Course ID` was never a course or a deck — it is
# the player's AVATAR cosmetic (see the module docstring), and renaming it was the point.
_LEGACY_COLUMNS = {"Course ID": "My Avatar", "Opponent Course": "Opponent Avatar"}

# `Match to <userId>:` — the ONLY place the local player's seat is identified.
# The id charset is deliberately broad ([A-Za-z0-9] + separators): the original
# [A-Z0-9]+ TRUNCATED an id containing lowercase, so the truncated id matched no
# seat and every match was skipped — the safe direction (skip, never guess a
# seat), but the warning blamed a missing header that was present (batch 5).
_ME_RE = re.compile(r"Match to ([A-Za-z0-9_-]+):")
# The log line's own timestamp is LOCAL; the JSON's epoch field is UTC, and using it files
# an evening session under the next day (the sample: header 7/27, epoch 7/28).
_DATE_RE = re.compile(r"\](\d{1,2})/(\d{1,2})/(\d{4})\s")
_STAMP_RE = re.compile(r"\](\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})\s*"
                       r"([AaPp][Mm])?")
# EventSetDeckV3's payload is JSON-inside-a-JSON-string, and the realistic paste is
# TRUNCATED (the extraction is hand-run through `cut`), so neither json.loads survives.
# These read a backslash-STRIPPED copy of the raw line, which is why they look unescaped:
# `\"DeckId\":\"…\"` flattens to `"DeckId":"…"`. `"Name"` is capital-N and the sibling
# attribute keys are lower-case `"name"`, so the deck name cannot be confused with them.
_SETDECK_MARKER = "EventSetDeckV3"
_DECK_GUID_RE = re.compile(r'"DeckId":"([^"]+)"')
_DECK_NAME_RE = re.compile(r'"Name":"([^"]*)"')
_LASTPLAYED_RE = re.compile(r'"LastPlayed".{0,40}?'
                            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?'
                            r'(?:[+-]\d{2}:\d{2}|Z)?)')
# An Arena deck named for its repo deck ("07 Earth's Mightiest", "19b …"). The letter is
# case-SENSITIVE and may not be separated by a space: with `[a-z]` case-insensitive and
# `\s*` in front, "07 Earth's Mightiest" resolved to deck id "7e".
_NUM_PREFIX_RE = re.compile(r"^0*(\d+)([a-z]?)(?![A-Za-z0-9])")
# Below this many matches a percentage is noise, so the report refuses to print one.
_MIN_SAMPLE = 20
# A deck selection older than this is a ROTATED LOG, not a choice: Arena re-submits the
# deck on every event join, so a real selection precedes its match by seconds (2–20s
# across the whole sample). Without the bound, a paste spanning a log rotation attributes
# an old session's deck to a new session's match — which reads as data, not as a gap.
_MAX_SELECTION_GAP_H = 12


def _local_date(line):
    """YYYY-MM-DD from a UnityCrossThreadLogger line's LOCAL timestamp, or ''."""
    m = _DATE_RE.search(line or "")
    if not m:
        return ""
    mo, day, yr = (int(x) for x in m.groups())
    return f"{yr:04d}-{mo:02d}-{day:02d}"


def _line_dt(line):
    """Naive LOCAL datetime from a UnityCrossThreadLogger line's timestamp, or None.

    Naive on purpose: the match header prints wall-clock local time with no zone, and
    EventSetDeckV3's `LastPlayed` carries the local offset — dropping it puts both on the
    one clock they were written against, which is what the ordering join needs."""
    m = _STAMP_RE.search(line or "")
    if not m:
        return None
    mo, day, yr, hh, mi, ss = (int(x) for x in m.groups()[:6])
    ampm = (m.group(7) or "").upper()
    if ampm == "PM" and hh != 12:
        hh += 12
    elif ampm == "AM" and hh == 12:
        hh = 0
    try:
        return datetime.datetime(yr, mo, day, hh, mi, ss)
    except ValueError:
        return None


def parse_deck_selection(raw):
    """(arena_name, deck_guid, selected_at) from an EventSetDeckV3 line, or None.

    Returns None for the `<== EventSetDeckV3(<id>)` RESPONSE line, which carries the
    marker and no payload."""
    if not raw or _SETDECK_MARKER not in raw:
        return None
    flat = raw.replace("\\", "")
    guid = _DECK_GUID_RE.search(flat)
    name = _DECK_NAME_RE.search(flat)
    if not guid and not name:
        return None
    when, dt = _LASTPLAYED_RE.search(flat), None
    if when:
        try:
            dt = datetime.datetime.fromisoformat(when.group(1)).replace(tzinfo=None)
        except ValueError:
            dt = None
    return (name.group(1) if name else "",
            guid.group(1) if guid else "",
            dt)


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


def attribute_selections(pending, selections):
    """Fill each match's `Arena Deck` / `Arena Deck ID` from the deck selected before it.

    `pending` is [(order, match_dt, row)]; `selections` is [(order, selected_at, name,
    guid)]. Returns a list of warnings.

    Prefers the TIMESTAMP join over log order, because the documented extraction is a
    `grep -h` across `Player*.log` and the shell expands that glob alphabetically, not
    chronologically — so a paste spanning two logs can present a later session's
    selections first, and a pure order walk would attribute the wrong deck with nothing
    said. Order is the fallback for a paste with no timestamps at all."""
    warnings = []
    timed = sorted((s for s in selections if s[1] is not None), key=lambda s: s[1])
    by_order = sorted(selections, key=lambda s: s[0])
    for order, when, row in pending:
        pick = None
        if when is not None and timed:
            earlier = [s for s in timed if s[1] <= when]
            if earlier:
                cand = earlier[-1]
                gap = (when - cand[1]).total_seconds() / 3600.0
                if gap <= _MAX_SELECTION_GAP_H:
                    pick = cand
                else:
                    warnings.append(
                        f"match {(row.get('Match ID') or '?')[:8]} left unattributed: the "
                        f"nearest deck selection ({cand[2] or cand[3]}) is {gap:.0f}h "
                        f"earlier, past the {_MAX_SELECTION_GAP_H}h bound — that is a "
                        f"rotated log, not a deck choice. Pass --deck <id> if you know it.")
            # No selection at or before this match is not an error: the log that held it
            # was overwritten. The row keeps a blank deck rather than borrowing a later
            # session's, which is the direction that cannot manufacture a record.
        elif by_order:
            prior = [s for s in by_order if s[0] < order]
            if prior:
                pick = prior[-1]
        if pick:
            row["Arena Deck"], row["Arena Deck ID"] = pick[2], pick[3]
    return warnings


def parse_log(text, me=None):
    """(rows, warnings) — one dict per completed match, oldest first.

    Walks the log in order, remembering the most recent `Match to <userId>` header, then
    resolves each finalMatchResult against it. EventSetDeckV3 lines are collected as they
    go and joined to the matches in a SECOND pass — the deck that was selected is only
    knowable relative to the other lines, so it cannot be resolved line-at-a-time."""
    rows, warnings, pending, selections = [], [], [], []
    current_me, current_date, current_dt = me, "", None
    for order, raw in enumerate((text or "").splitlines()):
        sel = parse_deck_selection(raw)
        if sel:
            name, guid, when = sel
            selections.append((order, when if when is not None else _line_dt(raw),
                               name, guid))
            continue
        hit = _ME_RE.search(raw)
        if hit:
            if me is None:
                current_me = hit.group(1)
            d = _local_date(raw)
            if d:
                current_date = d
            when = _line_dt(raw)
            if when is not None:
                current_dt = when
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
        row = {
            "Date": current_date or _utc_date(data.get("timestamp")),
            "Match ID": fin.get("matchId", ""),
            "Deck": "",
            "Arena Deck": "",
            "Arena Deck ID": "",
            # NOT a deck: `courseId` is the AVATAR cosmetic. See the module docstring.
            "My Avatar": mine.get("courseId", ""),
            "Event": mine.get("eventId", ""),
            "Result": result,
            "Games Won": sum(1 for g in games if g.get("winningTeamId") == my_team),
            "Games Lost": sum(1 for g in games
                              if g.get("winningTeamId") not in (None, 0, my_team)),
            "Opponent Avatar": opp.get("courseId", ""),
            "Reason": (fin.get("matchCompletedReason", "")
                       .replace("MatchCompletedReasonType_", "")),
        }
        rows.append(row)
        pending.append((order, current_dt, row))
    warnings.extend(attribute_selections(pending, selections))
    return rows, warnings


def arena_deck_map():
    """{key: deck_id} learned from `#: arena:` headers on deck files.

    A key is a lower-cased Arena deck NAME or its `DeckId` GUID — the header takes
    whichever the user has to hand, comma-separated for several. The GUID survives a
    rename in the Arena client; the name is the one a person can type without a log.
    Empty if deck.py is unavailable, so the parser still works standalone."""
    try:
        import deck as dk
        out = {}
        for d in dk.discover_decks():
            meta, _ = dk.parse_deck_file(d["path"])
            for key in (meta.get("arena") or "").replace(";", ",").split(","):
                key = key.strip().lower()
                if key:
                    out[key] = d["id"]
        return out
    except Exception:
        return {}


def deck_ids():
    """Every repo deck id, for validating the name-prefix fallback. Empty on failure."""
    try:
        import deck as dk
        return {d["id"] for d in dk.discover_decks()}
    except Exception:
        return set()


def resolve_deck(name, guid, mapping, known_ids=()):
    """(deck_id, how) for one Arena deck — ('', '') when nothing resolves.

    Explicit first: a `#: arena:` header beats the name-prefix guess, and the guess is
    accepted only when the id it produces is a deck that EXISTS. A prefix that resolves
    to nothing is left blank rather than invented — an unattributed match is a visible
    gap, a wrongly attributed one is a fabricated win rate."""
    for key in ((guid or "").strip().lower(), (name or "").strip().lower()):
        if key and key in mapping:
            return mapping[key], "#: arena: header"
    m = _NUM_PREFIX_RE.match((name or "").strip())
    if m:
        cand = f"{int(m.group(1))}{m.group(2)}"
        if cand in set(known_ids):
            return cand, "name prefix"
    return "", ""


# Any deck SUMMARY, wherever it appears: EventSetDeckV3 carries the deck submitted for
# an event, DeckUpsertDeckV3 the deck just saved/renamed/imported. Both nest the same
# {"DeckId":…,"Name":…} object, so one pattern reads every shape rather than one per
# message layout — and it still reads a multi-summary line should Arena ever log one.
# (DeckGetDeckSummariesV3 was ASSUMED to be a third source and measured to be none:
# Arena logs its request and a bare `<== …(id)` ack, no payload — 0 decks from 5 calls
# in the first real sample, so grepping for it hauls in nothing.) The window is bounded
# so a summary MISSING a Name cannot reach into the next entry's.
_SUMMARY_RE = re.compile(r'"DeckId":"([^"]+)".{0,200}?"Name":"([^"]*)"')
_ARENA_HEADER_RE = re.compile(r"^#:\s*arena\s*:", re.I)


def parse_deck_names(text):
    """{DeckId GUID: Arena deck name} for every deck summary anywhere in the log.

    LAST occurrence wins, not the first: a deck renamed in the client appears under both
    names and the later line is the current one. (`setdefault` here would be the G-63
    first-writer-claims-the-key trap one file over.)"""
    out = {}
    for raw in (text or "").splitlines():
        for guid, name in _SUMMARY_RE.findall(raw.replace("\\", "")):
            if name.strip():
                out[guid] = name.strip()
    return out


def _arena_header_plan(names):
    """[(deck_id, path, header_line, status)] for the decks `names` resolves to.

    Status is one of `add` / `update` / `unchanged` / `conflict`. A CONFLICT — two Arena
    decks resolving to one repo deck, which is what an old copy left in the client looks
    like — writes nothing: a header naming the wrong one of two decks is worse than no
    header, because the parser would then attribute matches to it with full confidence."""
    try:
        import deck as dk
        records = {d["id"]: d for d in dk.discover_decks()}
    except Exception:
        return []
    mapping, known = arena_deck_map(), set(records)
    claims = {}
    for guid, name in sorted(names.items(), key=lambda kv: kv[1]):
        did, _how = resolve_deck(name, guid, mapping, known)
        if did:
            claims.setdefault(did, []).append((name, guid))
    plan = []
    for did, hits in sorted(claims.items()):
        rec = records[did]
        if len(hits) > 1:
            plan.append((did, rec["path"], "; ".join(n for n, _ in hits), "conflict"))
            continue
        name, guid = hits[0]
        line = f"#: arena: {name}, {guid}"
        try:
            with open(rec["path"], encoding="utf-8") as fh:
                current = [ln.rstrip("\n") for ln in fh]
        except OSError:
            continue
        existing = [ln for ln in current if _ARENA_HEADER_RE.match(ln)]
        status = "unchanged" if existing == [line] else ("update" if existing else "add")
        plan.append((did, rec["path"], line, status))
    return plan


def _write_arena_header(path, line):
    """Insert or replace one `#: arena:` header. Returns the .bak path.

    Routed through `deck._safe_write_lines`, which re-parses the file (INV-04) and
    verifies the copy count is unchanged before replacing it — a header edit must not be
    able to touch a card line, and the check that proves it already exists."""
    import deck as dk
    with open(path, encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh]
    _, cards = dk.parse_deck_file(path)
    total = sum(q for q, *_ in cards)
    out, placed = [], False
    for ln in lines:
        if _ARENA_HEADER_RE.match(ln):
            if not placed:
                out.append(line)
                placed = True
            continue                       # drop any duplicate arena headers
        out.append(ln)
    if not placed:
        # After `#: format:` when there is one (that is where the three hand-written
        # headers sit), else after `#: name:`, else at the top.
        anchor = -1
        for i, ln in enumerate(out):
            if ln.lower().startswith("#: format:"):
                anchor = i
        if anchor < 0:
            for i, ln in enumerate(out):
                if ln.lower().startswith("#: name:"):
                    anchor = i
        out.insert(anchor + 1, line)
    return dk._safe_write_lines(path, out, total)


def map_decks(text, apply=False, out=print):
    """Learn `#: arena:` headers for the whole roster from one log paste. Returns
    (written, plan)."""
    names = parse_deck_names(text)
    if not names:
        out("No deck summaries found. The paste needs at least one line carrying a "
            "{\"DeckId\":…,\"Name\":…} object — EventSetDeckV3, DeckUpsertDeckV3 or a "
            "DeckGetDeckSummariesV3 response.")
        return 0, []
    plan = _arena_header_plan(names)
    matched = {p[0] for p in plan}
    out(f"{len(names)} Arena deck(s) in the paste; {len(matched)} resolved to a repo "
        f"deck.\n")
    for did, _path, line, status in plan:
        mark = {"add": "+", "update": "~", "unchanged": "=", "conflict": "!"}[status]
        out(f"  {mark} deck {did:<5} {line if status != 'conflict' else line}")
        if status == "conflict":
            out(f"      ^ two Arena decks claim deck {did} — resolve by hand, nothing "
                f"written")
    # Hoisted: both loaders re-parse every deck file, so calling them per candidate made
    # the roster cost quadratic for a line of diagnostics.
    mapping, known = arena_deck_map(), deck_ids()
    unresolved = sorted(n for g, n in names.items()
                        if not resolve_deck(n, g, mapping, known)[0])
    if unresolved:
        out(f"\n{len(unresolved)} Arena deck(s) matched no repo deck (the name carries no "
            f"leading deck number, or that deck does not exist here):")
        for n in unresolved[:20]:
            out(f"    {n}")
        if len(unresolved) > 20:
            out(f"    … and {len(unresolved) - 20} more")
    todo = [p for p in plan if p[3] in ("add", "update")]
    if not apply:
        out(f"\n(dry run — {len(todo)} file(s) would change; pass --apply to write)")
        return 0, plan
    written = 0
    for did, path, line, status in todo:
        _write_arena_header(path, line)
        written += 1
    out(f"\nWrote {written} deck file(s), each with a .bak. Run check_all.py to confirm "
        f"INV-04 still holds.")
    return written, plan


def sync_headers(text, apply=False, out=print):
    """The quiet sibling of `map_decks`, run inside the NORMAL match flow.

    Any paste that can attribute a match already carries the deck summaries that keep
    `#: arena:` headers current, so making header upkeep a separate command meant it was
    upkeep nobody would run — the G-53 shape, a capability nothing reaches. This applies
    the same `_arena_header_plan` (same conflict refusal, same `.bak`-writing
    `_write_arena_header`) but reports only what CHANGES, so a routine log ingest is not
    buried under an all-unchanged roster listing. Returns (written, plan)."""
    plan = _arena_header_plan(parse_deck_names(text))
    for did, _path, names, _status in plan:
        if _status == "conflict":
            out(f"⚠ deck {did}: two Arena decks claim it ({names}) — no header written; "
                f"resolve by hand")
    todo = [p for p in plan if p[3] in ("add", "update")]
    if not todo:
        return 0, plan
    if not apply:
        out(f"{len(todo)} deck(s) would gain or refresh a `#: arena:` header "
            f"(written on --apply): " + ", ".join(p[0] for p in todo))
        return 0, plan
    for _did, path, line, _status in todo:
        _write_arena_header(path, line)
    out(f"Refreshed `#: arena:` header(s) on {len(todo)} deck file(s): "
        + ", ".join(p[0] for p in todo))
    return len(todo), plan


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
    """Rows from matches.csv, with the pre-attribution column names migrated in.

    `write_matches` emits only HEADER, so a CSV still carrying `Course ID` would be
    rewritten with those cells BLANK — silently losing the one field the old rows had.
    Renaming on read makes the migration happen on the next write instead."""
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        rows = []
        for r in csv.DictReader(fh):
            row = dict(r)
            for old, new in _LEGACY_COLUMNS.items():
                if old in row and not (row.get(new) or "").strip():
                    row[new] = row.pop(old)
            rows.append(row)
        return rows


def _is_own_earlier_schema(path):
    """True when `path` is a matches.csv written before the avatar-column rename.

    The F-02 mirror guard compares headers and cannot tell "another file's schema" from
    "an earlier version of MY OWN" — so without this the guard refuses the one write that
    performs the migration, and a user with an existing matches.csv gets a traceback
    instead of an upgrade. Deliberately EXACT: only the one header this module used to
    emit is accepted, so a genuinely foreign CSV is still refused."""
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            head = next(csv.reader(fh), None)
    except (OSError, UnicodeDecodeError):
        return False
    legacy = [_LEGACY_COLUMNS.get(c, c) for c in (head or [])]
    return legacy == [c for c in HEADER if c not in ("Arena Deck", "Arena Deck ID")]


def write_matches(rows, path=MATCHES_CSV):
    # Same F-02 mirror guard as the two builders (broad-scan Batch G): `--out`
    # accepts any path, and this writer emits only HEADER — pointed at a canonical
    # CSV it would overwrite it with the match schema.
    problem = csv_schema_error(path, HEADER)
    if problem and not _is_own_earlier_schema(path):
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
        # An unattributed row buckets by its ARENA DECK NAME, never by the avatar: the
        # avatar is a cosmetic shared across decks and changed at whim, so keying on it
        # merges unrelated decks into one row and splits one deck across several — the
        # same misreading that put an `Avatar_Basic_*` value in a column called "Course
        # ID" in the first place. With no Arena deck the honest bucket is "unknown".
        key = r.get("Deck") or f"(unattributed: {r.get('Arena Deck') or 'deck unknown'})"
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
    unmapped = sorted({r.get("Arena Deck") or "" for r in rows
                       if not r.get("Deck") and (r.get("Arena Deck") or "").strip()})
    if unmapped:
        print(f"\n{len(unmapped)} unmapped Arena deck(s). Add `#: arena: <Arena deck name>` "
              f"(or the DeckId GUID, which survives a rename) to the matching deck file:")
        for c in unmapped[:10]:
            print(f"   {c}")
    blind = sum(1 for r in rows if not r.get("Deck") and not (r.get("Arena Deck") or "").strip())
    if blind:
        print(f"\n{blind} match(es) have no Arena deck at all — the EventSetDeckV3 lines "
              f"were not in the paste, or the log holding them had rotated. Re-extract with "
              f"the widened grep (see the parse_matches.py docstring) and re-run; already-"
              f"recorded rows keep their attribution.")
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
    ap.add_argument("--map-decks", action="store_true",
                    help="learn `#: arena:` headers for the whole roster from the log's "
                         "deck summaries, instead of parsing matches")
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

    if args.map_decks:
        map_decks(text, apply=args.apply)
        return 0

    rows, warnings = parse_log(text, me=args.me)
    for w in warnings:
        eprint(f"WARN:  {w}")

    # Header upkeep rides along with every ingest — BEFORE the mapping is built, so a
    # header written from this paste resolves this paste's own matches, and BEFORE the
    # no-matches bailout, so a paste of deck summaries alone (the --map-decks extraction
    # shape) still keeps headers current instead of dying with a misleading error.
    sync_headers(text, apply=args.apply)

    if not rows:
        if parse_deck_names(text):
            print("No completed matches in this paste — deck summaries only. Header "
                  "changes, if any, are reported above"
                  + ("." if args.apply else " (dry run — pass --apply to write them)."))
            return 0
        eprint("No completed matches found. Check that Detailed Logs (Plugin Support) is "
               "enabled in Arena, and that the paste includes the `Match to ...` header "
               "lines as well as the JSON.")
        return 1

    mapping, known = arena_deck_map(), deck_ids()
    routes = {}
    for r in rows:
        if args.deck:
            r["Deck"] = args.deck
            continue
        key = (r.get("Arena Deck", ""), r.get("Arena Deck ID", ""))
        if key not in routes:
            routes[key] = resolve_deck(key[0], key[1], mapping, known)
        r["Deck"] = routes[key][0]

    existing = load_matches(args.out)
    # A row with NO matchId must never dedupe against another blank — "" in the
    # known-set silently dropped every subsequent id-less match as "already
    # recorded", which reads as data, not as a gap (broad-scan batch 5).
    fresh = fresh_rows(rows, existing)

    # A heuristic that ASSIGNS data has to show its work, so every Arena deck the run saw
    # is printed with the route that resolved it — the same reason `cuts` and `swap` print
    # oracle text rather than a label (G-52).
    # The all-blank key is a match with NO deck selection in the paste, not an Arena deck
    # — it is reported by the per-match lines below and by the report's own blind count.
    shown = {k: v for k, v in routes.items() if k[0].strip() or k[1].strip()}
    if shown:
        print(f"\nDeck attribution — {len(shown)} Arena deck(s) seen:")
        for (name, guid), (did, how) in sorted(shown.items()):
            label = name or guid
            target = f"deck {did}  ({how})" if did else "UNRESOLVED — blank Deck"
            print(f"   {label[:40]:40}  ->  {target}")
        print()

    print(f"Found {len(rows)} completed match(es); {len(fresh)} new, "
          f"{len(rows) - len(fresh)} already recorded.")
    for r in fresh:
        deck_label = r["Deck"] or f"(unattributed: {r['Arena Deck'] or 'deck unknown'})"
        print(f"   {r['Date']}  {r['Result']}  {r['Games Won']}-{r['Games Lost']}  "
              f"{deck_label}  vs {r['Opponent Avatar'] or '?'}  [{r['Event']}]")
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
