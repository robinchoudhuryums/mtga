#!/usr/bin/env python3
# RAW docstring: the extraction recipe below contains shell regex (`\[`, `\\"`), and in a
# normal string those are invalid escape sequences — a DeprecationWarning today and a
# SyntaxError on a future Python, from a comment.
r"""Parse MTG Arena match results out of Player.log into matches.csv.

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
        "$p"/Player*.log \
      | sed -E 's/\\"(MainDeck|Sideboard)\\":\[[^]]*\]/\\"\1\\":[]/g' | pbcopy

The `sed` stage drops EventSetDeckV3's CARD LISTS, which nothing here reads — attribution
uses only the Name, DeckId and LastPlayed from the same line. It is not cosmetic: a real
52-card selection line measures 1919 bytes and slims to 152, a 92% cut, and there is one
such line per event join. Without it the paste is mostly card ids, and the pastes that
surfaced this were hand-truncated in an editor before use — which is JSON surgery on the
one line the whole attribution chain depends on. Let sed do it, or keep the arrays; do
not trim them by hand.

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
          "Event", "Result", "Games Won", "Games Lost", "Opponent Avatar", "Reason",
          "Ended By",
          # HAND-ENTERED, appended 2026-08-20 (`--add`). The log cannot supply any of
          # these: Arena records the deck YOU submitted and the raw outcome, and nothing
          # about what you faced, whether you were on the play, or why you lost. They are
          # also the only fields that answer "what should I change", which is why they
          # exist. All four are OPTIONAL and blank on every log-parsed row by
          # construction — a reader must treat blank as "not recorded", never as a value.
          "On Play", "Opponent Archetype", "Loss Reason", "Note"]

# The loss-reason vocabulary. CLOSED so it can be COUNTED — free text cannot answer
# "which decks flood out", which is the whole reason to record it. An unrecognized value
# is still WRITTEN (with a warning naming the known ones): the vocabulary is a starting
# point someone will outgrow, and refusing the entry would cost a real match to protect a
# list I guessed at. Add a key here when a warning keeps recurring.
LOSS_REASONS = {
    "flood":      "too many lands",
    "screw":      "too few lands / colour screw",
    "slow":       "outraced — curve too high or clock too slow",
    "answer":     "no answer to their threat",
    "removed":    "my threat or engine got killed",
    "keep":       "bad mulligan or bad keep",
    "misplay":    "my own error",
    "outclassed": "they were simply stronger",
}
_ON_PLAY = {"play", "draw"}

# TWO reason fields, and for a year only the uninformative one was stored.
#   `Reason`   = `matchCompletedReason`, which is `Success` for every match that
#                COMPLETED — by construction. All 15 rows of the first real record read
#                `Success`, i.e. the column carried exactly zero bits. It is kept because
#                a non-Success value (a disconnect, a timeout) is genuinely worth having;
#                it simply has not fired yet.
#   `Ended By`  = the MATCH-scope result's own `reason` — `Game` vs `Concede`. This one
#                varies (2 of 3 in the batch that surfaced the gap) and is the half that
#                means something at low n: a concede-win on turn three is not the same
#                evidence about a deck as a game-win, and the record lives permanently
#                near the small-sample floor where that distinction is most of the signal.
# Blank on every pre-existing row, which is honest — those matches were parsed before the
# field was read, so the value is unknown rather than "Game".
_ENDED_BY_PREFIX = "ResultReason_"

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
            "Ended By": (match_res.get("reason") or "").replace(_ENDED_BY_PREFIX, ""),
            # Not columns — `write_matches` emits only HEADER, so these are dropped on
            # write. They exist so the dry run can PRINT the raw read the W/L verdict
            # came from (G-52: a verdict surface must print its evidence). Without them
            # the only way to check an inverted result was to re-read the JSON by hand,
            # which is exactly what was being done, match by match.
            "_my_team": my_team,
            "_win_team": win_team,
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


def deck_names():
    """{deck id: repo `#: name:`}, for DISCLOSING what a name-prefix guess resolved to.

    Report-only, and that is a measured decision rather than a cautious one. The obvious
    design was a name-AGREEMENT gate: the prefix route validates only the leading NUMBER,
    so "15 Anything At All" resolves to deck 15 and `--apply` then writes a permanent
    `#: arena:` header off that guess. Comparing the name's remainder against the repo
    deck's name looked like a free confirmation.

    It is not. Measured 2026-08-14 over the 22 `#: arena:` headers then on the roster —
    every one of them a correct mapping — 8 DISAGREED with the repo name under a
    containment test: Arena's "49 Big Draco" was repo deck 49 "Scaleforge", "58 Treasure
    Planet" was "Gold Standard", "45 The Exiles" was "Exile Dividend". The Arena names are
    flavour names, not repo names. A gate would therefore have been wrong 36% of the time,
    blocking correct attributions — the same saturation that made the `review` flag 0%
    actionable in G-07.

    Those three examples now read as agreements, because `--sync-names` was run the same
    day and the repo adopted Arena's names. **That does not retire the measurement.** The
    divergence is generated by how the owner names decks in the client, not by a one-time
    drift, so it regrows the moment a deck is renamed there — and the sync is opt-in, so
    the roster is only ever as reconciled as the last run. Re-measure before trusting a
    name; do not read today's agreement as a reason to add the gate.

    So the number stays the sole criterion and the NAME is shown instead: a wrong guess
    is visible in the dry run, before --apply makes it a header, and a right-but-renamed
    deck still resolves. Disclosure over gating, the G-38 stance for a fuzzy signal."""
    try:
        import deck as dk
        return {d["id"]: d["name"] for d in dk.discover_decks()}
    except Exception:
        return {}


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


_NAME_HEADER_RE = re.compile(r"^#:\s*name\s*:", re.I)
# An `#: arena:` header holds `<name>, <GUID>` in either order, and a deck NAME can look
# like anything — so the GUID is identified by its own shape rather than by position.
_GUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                      re.I)
# Arena's deck names cannot hold an em dash, so the client copy of a variant is typed
# "54b Grand Lotus- Comet" against the repo's "Grand Lotus — Comet". Adopting the raw
# string would import that degradation into the repo and, worse, make a name that is
# ALREADY correct look different every run. Only a hyphen followed by whitespace is
# converted — "Spider-Man" has none, so it is untouched.
_ARENA_DASH_RE = re.compile(r"(\S)-\s+")


def _name_key(s):
    """Comparison key for two deck names: words only, case- and punctuation-blind.

    The trigger for a rename must be a difference in WORDS, never in typography. Arena
    writes a curly apostrophe ("Earth’s"), a doubled space ("66  Lethal Protector") and a
    hyphen for an em dash; all three are the SAME name and must not churn the repo."""
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _adopted_name(arena_name, rec, parent_name):
    """The repo `#: name:` that adopting `arena_name` implies, or '' if it cannot tell.

    Two rules beyond stripping the deck number. Arena's degraded separator is restored to
    the repo's em dash (see `_ARENA_DASH_RE`). And the VARIANT CONVENTION is preserved:
    repo variants are named "<parent> — <variant>", which G-27's rationale audit depends
    on ("a name forming part of THIS deck's own name is not another deck"), so a variant
    adopting "Ancient Decay" becomes "Iron Forge — Ancient Decay", not a bare name that
    would orphan it from its family. When Arena's own name already carries the parent
    ("Grand Lotus- Comet") the prefix is not doubled."""
    rest = _NUM_PREFIX_RE.sub("", (arena_name or "").strip()).strip()
    rest = _ARENA_DASH_RE.sub(r"\1 — ", rest).strip()
    if not rest:
        return ""
    if not (rec.get("variant") and parent_name):
        return rest
    pk, rk = _name_key(parent_name), _name_key(rest)
    if rk.startswith(pk) and rk != pk:
        # Arena repeated the parent — keep the repo's spelling of it, not Arena's.
        tail = rest
        while tail and _name_key(tail) != rk[len(pk):]:
            tail = tail[1:]
        rest = tail.lstrip(" —-").strip() or rest
    return f"{parent_name} — {rest}" if _name_key(rest) != pk else parent_name


def deck_name_plan(names):
    """[(deck_id, path, current_name, adopted_name)] for decks Arena has RENAMED.

    IDENTITY IS THE DeckId GUID, not a card list and not the deck number. That is a
    deliberate substitution for what was asked, and it is the stronger test: a GUID is
    stable across every edit Arena lets you make, whereas a card list changes the moment
    you tune — so card-matching would refuse exactly the decks under active development,
    which are the ones most likely to have been renamed. It is also the only option that
    works today: nothing in this repo maps Arena's numeric `cardId` to a card name, and
    the documented extraction now strips the `MainDeck` array precisely because nothing
    reads it.

    So a deck qualifies only when its own `#: arena:` header carries the GUID the paste
    reports under a new name — i.e. a human already confirmed the pairing. A name-prefix
    match is NOT enough and never adopts: that route validates the leading number alone.
    """
    try:
        import deck as dk
        records = {d["id"]: d for d in dk.discover_decks()}
    except Exception:
        return []
    mapping = arena_deck_map()
    plan = []
    for guid, arena_name in sorted(names.items(), key=lambda kv: kv[1]):
        did = mapping.get((guid or "").strip().lower())     # GUID proof, nothing weaker
        rec = records.get(did or "")
        if not rec:
            continue
        parent = records.get(rec.get("core") or "")
        adopted = _adopted_name(arena_name, rec, (parent or {}).get("name", ""))
        current = rec.get("name") or ""
        if adopted and _name_key(adopted) != _name_key(current):
            plan.append((did, rec["path"], current, adopted))
    return plan


def _write_deck_name(path, new_name):
    """Rewrite one `#: name:` line. Returns the .bak path.

    Same `deck._safe_write_lines` route as the arena-header writer: re-parses the file
    (INV-04) and verifies the copy count is unchanged, so a header edit cannot touch a
    card line."""
    import deck as dk
    with open(path, encoding="utf-8") as fh:
        lines = [ln.rstrip("\n") for ln in fh]
    _, cards = dk.parse_deck_file(path)
    total = sum(q for q, *_ in cards)
    out, placed = [], False
    for ln in lines:
        if not placed and _NAME_HEADER_RE.match(ln):
            out.append(f"#: name: {new_name}")
            placed = True
            continue
        out.append(ln)
    if not placed:
        out.insert(0, f"#: name: {new_name}")
    return dk._safe_write_lines(path, out, total)


def _variant_orphans(old_name, own_id, adopted):
    """[(variant id, its name)] for variants whose own name carries the OLD parent name.

    The mirror of the convention `_adopted_name` protects. Renaming a variant keeps its
    "<parent> — <variant>" shape; renaming the PARENT silently breaks that shape for every
    variant beneath it. The 2026-08-14 sync did exactly that four times — deck 28a was
    left as "Dino Stampede — Owned Build" under a parent renamed to "Triceraton", and 45a,
    48a and 51a the same — which is why this flag exists and why the four were then fixed
    by hand. Those variants have no Arena pairing of their own — a GUID is per Arena
    deck and the repo's variants mostly are not separate Arena decks — so nothing here can
    rename them from evidence. Flagged rather than cascaded: picking the new variant name
    is editorial, and this tool adopts, it does not compose."""
    if not old_name or _name_key(old_name) in _name_key(adopted):
        return []
    try:
        import deck as dk
        decks = dk.discover_decks()
    except Exception:
        return []
    own = next((d for d in decks if d["id"] == own_id), None)
    if not own or own.get("variant"):
        return []                          # only a PARENT rename can orphan anything
    return [(d["id"], d["name"]) for d in decks
            if d["id"] != own_id and d.get("core") == own.get("core")
            and old_name.lower() in (d.get("name") or "").lower()]


def _name_citations(old_name, own_id, adopted):
    """Deck ids whose `#:` header prose names `old_name` and would be left stale.

    A rename is not a local edit: 50 of the 106 decks are named inside another deck's
    header prose, so adopting Arena's name can strand a reference the rationale audit
    cannot see (it checks CARD names and FIGURES, never deck names). Nothing rewrites
    prose automatically — that is editorial — so the cost is shown at decision time
    instead.

    Suppressed when the adopted name still CONTAINS the old one ("Unlock" -> "Unlocked",
    "Bird Brain" -> "Bird Brain — Bant"): the citation keeps reading correctly, and
    flagging it would bury the five real cases in noise."""
    if _name_key(old_name) in _name_key(adopted):
        return []
    if len(old_name or "") < 6:            # too short to match on without false hits
        return []
    try:
        import deck as dk
        decks = dk.discover_decks()
    except Exception:
        return []
    hits = []
    for d in decks:
        if d["id"] == own_id:
            continue
        try:
            with open(d["path"], encoding="utf-8") as fh:
                prose = "\n".join(ln for ln in fh if ln.startswith("#"))
        except OSError:
            continue
        if old_name.lower() in prose.lower():
            hits.append(d["id"])
    return hits


def sync_deck_names(text, apply=False, out=print):
    """Adopt Arena's deck names into the repo. Returns (written, plan).

    ALWAYS REPORTS, writes only under `--sync-names`. An `#: arena:` header is bookkeeping
    the tooling owns; a deck's NAME is human-authored prose that other files cite — 50 of
    the 106 decks are named inside another deck's header prose — so a rename is offered
    rather than performed. Reporting unconditionally is the other half: a capability
    behind a flag nobody runs is invisible (G-53), so the run says a rename is available
    even when it will not make one."""
    return _report_name_plan(deck_name_plan(parse_deck_names(text)), apply=apply, out=out)


def _report_name_plan(plan, apply=False, out=print):
    """Print a rename plan and, on `apply`, perform it. Returns (written, plan)."""
    if not plan:
        return 0, []
    out(f"\n{len(plan)} deck(s) are named differently in Arena than in the repo "
        f"(matched on the DeckId GUID, so these are the same decks):")
    for did, _path, current, adopted in plan:
        out(f"   deck {did:<5} {current!r}  ->  {adopted!r}")
        orphans = _variant_orphans(current, did, adopted)
        if orphans:
            out(f"        ⚠ VARIANT(S) carry the old parent name and are NOT renamed "
                f"here: {', '.join(f'{i} {n!r}' for i, n in orphans)}")
        cites = _name_citations(current, did, adopted)
        if cites:
            out(f"        ⚠ old name cited in {len(cites)} other deck file(s): "
                f"{', '.join(cites)}")
    if not apply:
        out("   (reported only — pass --sync-names to adopt Arena's names. Nothing "
            "rewrites\n    the prose in other deck files, so a ⚠ above is a citation you "
            "fix by hand.)")
        return 0, plan
    written = 0
    for did, path, _current, adopted in plan:
        _write_deck_name(path, adopted)
        written += 1
    out(f"   adopted {written} name(s); a .bak was written beside each deck file.")
    return written, plan


def stored_arena_names():
    """{DeckId GUID: Arena deck name} from the `#: arena:` headers already on disk.

    The headers are Arena's own answer, recorded by earlier runs — reading them back is
    how a divergence that built up over months gets reconciled without a paste covering
    the whole roster. Only a header carrying BOTH a name and a GUID is used, since the
    GUID is the identity proof `deck_name_plan` requires."""
    try:
        import deck as dk
        decks = dk.discover_decks()
    except Exception:
        return {}
    out = {}
    for d in decks:
        meta, _ = dk.parse_deck_file(d["path"])
        parts = [p.strip() for p in (meta.get("arena") or "").replace(";", ",").split(",")]
        parts = [p for p in parts if p]
        if len(parts) < 2:
            continue
        name = next((p for p in parts if not _GUID_RE.fullmatch(p)), "")
        guid = next((p for p in parts if _GUID_RE.fullmatch(p)), "")
        if name and guid:
            out[guid] = name
    return out


def sync_deck_names_from_headers(apply=False, out=print):
    """`sync_deck_names` sourced from the stored headers instead of a fresh paste."""
    plan = deck_name_plan(stored_arena_names())
    return _report_name_plan(plan, apply=apply, out=out)


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


def _slug(text):
    """An archetype label normalized so two spellings of one deck COUNT AS ONE.

    `Mono Red`, `mono-red` and `Mono  Red ` all key `mono-red`. Without this the
    breakdown splits one archetype across three rows and each lands under the read
    floor — the same saturation-by-fragmentation that makes a free-text field
    uncountable. Display keeps the slug, so what you type back next time matches."""
    out = "-".join((text or "").strip().lower().split())
    return "".join(ch for ch in out if ch.isalnum() or ch in "-/+").strip("-")


def parse_manual(text, existing_ids=(), deck_ids=None, today=None):
    """([row, ...], [warning, ...]) from the compact hand-entry syntax.

    One match per line:

        <deck> <W|L|D> [opp=<archetype>] [why=<reason>] [play=play|draw]
                       [event=<name>] [date=YYYY-MM-DD] [note="free text"]

    Blank lines and `#` comments are skipped. Keys are order-independent; `note` may be
    quoted. Every field after the result is optional.

    WHY A SEPARATE ENTRY PATH rather than editing the CSV by hand: a hand-written row
    has no `Match ID`, and the ID is what makes re-running the log parser idempotent
    (dedup is by ID). Rows entered here get `manual-YYYYMMDD-NN`, unique against
    `existing_ids`, so the two writers cannot collide or double-count.

    VALIDATION IS ASYMMETRIC ON PURPOSE. An unknown DECK id is a hard reject — it would
    silently create a phantom deck row in `--report` that no deck file backs. An unknown
    `why` is a WARNING that still records: the vocabulary is a guess, and losing a real
    match to protect it is the worse trade. `why` on a WIN is refused outright, because a
    loss reason attached to a win is not a typo with a sensible reading."""
    import datetime as _dt
    import shlex
    rows, warnings = [], []
    used = set(existing_ids)
    day = today or _dt.date.today().isoformat()
    seq = {}
    for lineno, raw in enumerate((text or "").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parts = shlex.split(line)
        except ValueError as e:
            warnings.append(f"line {lineno}: unbalanced quotes ({e}) — skipped: {line!r}")
            continue
        if len(parts) < 2:
            warnings.append(f"line {lineno}: need at least `<deck> <W|L|D>` — skipped: {line!r}")
            continue
        deck, result, rest = parts[0], parts[1].upper(), parts[2:]
        if result not in ("W", "L", "D"):
            warnings.append(f"line {lineno}: result {parts[1]!r} is not W, L or D — skipped")
            continue
        if deck_ids is not None and deck not in deck_ids:
            warnings.append(f"line {lineno}: no deck {deck!r} in decks/ — skipped. An "
                            f"unknown id would appear in --report as a deck that does "
                            f"not exist.")
            continue
        kv, bad = {}, False
        for tok in rest:
            if "=" not in tok:
                warnings.append(f"line {lineno}: {tok!r} is not key=value — skipped")
                bad = True
                break
            k, v = tok.split("=", 1)
            kv[k.strip().lower()] = v.strip()
        if bad:
            continue
        unknown = set(kv) - {"opp", "why", "play", "event", "date", "note"}
        if unknown:
            warnings.append(f"line {lineno}: unknown key(s) {sorted(unknown)} — skipped. "
                            f"Known: opp, why, play, event, date, note.")
            continue
        why = (kv.get("why") or "").strip().lower()
        if why and result != "L":
            warnings.append(f"line {lineno}: why={why!r} on a {result} — skipped. A loss "
                            f"reason on a non-loss has no reading; drop it or use note=.")
            continue
        if why and why not in LOSS_REASONS:
            warnings.append(f"line {lineno}: why={why!r} is not in the vocabulary — "
                            f"RECORDED ANYWAY so the match is not lost, but it will not "
                            f"group with the known ones: {', '.join(sorted(LOSS_REASONS))}.")
        on_play = (kv.get("play") or "").strip().lower()
        if on_play and on_play not in _ON_PLAY:
            warnings.append(f"line {lineno}: play={on_play!r} is not play/draw — dropped")
            on_play = ""
        date = (kv.get("date") or "").strip() or day
        try:
            _dt.date.fromisoformat(date)
        except ValueError:
            warnings.append(f"line {lineno}: date={date!r} is not YYYY-MM-DD — skipped")
            continue
        stamp = date.replace("-", "")
        n = seq.get(stamp, 0)
        while True:
            n += 1
            mid = f"manual-{stamp}-{n:02d}"
            if mid not in used:
                break
        seq[stamp] = n
        used.add(mid)
        rows.append({
            "Date": date, "Match ID": mid, "Deck": deck, "Arena Deck": "",
            "Arena Deck ID": "", "My Avatar": "",
            "Event": (kv.get("event") or "Play").strip(), "Result": result,
            "Games Won": "", "Games Lost": "", "Opponent Avatar": "",
            "Reason": "", "Ended By": "",
            "On Play": on_play, "Opponent Archetype": _slug(kv.get("opp")),
            "Loss Reason": why, "Note": (kv.get("note") or "").strip(),
        })
    return rows, warnings


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


# Any earlier schema must still carry these, or it is not a matches.csv at all. They are
# the row's identity and its payload: without Match ID dedup cannot work, and without
# Date/Result there is nothing to migrate that is worth keeping.
_SCHEMA_CORE = ("Date", "Match ID", "Result")


def _is_own_earlier_schema(path):
    """True when `path` is a matches.csv written by an EARLIER version of this module.

    The F-02 mirror guard compares headers and cannot tell "another file's schema" from
    "an earlier version of MY OWN" — so without this the guard refuses the one write that
    performs the migration, and a user with an existing matches.csv gets a traceback
    instead of an upgrade.

    This used to hard-code the ONE header the module emitted before the avatar rename,
    which worked exactly once. The next column to land (`Ended By`) made the CURRENT file
    an "earlier schema" too, and an exact match against a single remembered header cannot
    see that — so the guard would have refused the very write that performs the upgrade,
    reproducing the bug this function exists to prevent. Generalized to: every column is
    one of MINE, in MY order, with nothing foreign and nothing missing from the core.
    That accepts any past or intermediate shape (columns have been both RENAMED and
    INSERTED MID-HEADER here, so neither a prefix nor a subset test would do) while still
    refusing a genuinely foreign CSV, which would have to be an ordered sub-sequence of
    these thirteen names by accident."""
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            head = next(csv.reader(fh), None)
    except (OSError, UnicodeDecodeError):
        return False
    legacy = [_LEGACY_COLUMNS.get(c, c) for c in (head or [])]
    if not legacy or any(c not in HEADER for c in legacy):
        return False
    if len(set(legacy)) != len(legacy):
        return False                       # a duplicate column is not a schema of mine
    if any(c not in legacy for c in _SCHEMA_CORE):
        return False
    order = [HEADER.index(c) for c in legacy]
    return order == sorted(order)


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


def _result_evidence(row):
    """`[my team 1 · winner 1]` — the raw read the W/L verdict came from.

    G-52: a verdict surface must print its evidence. The result is derived from exactly
    two integers, and a single inverted seat read would flip EVERY row in a paste in the
    same direction — a failure that looks like a losing streak rather than like a bug.
    Printing the pair costs one column and makes the check a glance instead of a hand
    re-read of the JSON, which is how the first fifteen matches were actually verified.
    Keyed on the field's PRESENCE, not its truthiness. A row loaded back from CSV never
    carries these at all and must print nothing (the report path). But a parsed row whose
    seat has no `teamId` carries the key with None — and that is the case where the
    verdict is least trustworthy, so it prints `?` rather than falling into the same
    silent-empty branch as a CSV row."""
    if "_my_team" not in row:
        return ""
    mine, win = row.get("_my_team"), row.get("_win_team")
    return (f"[my team {mine if mine is not None else '?'} · "
            f"winner {win if win not in (None, 0) else 'none'}]")


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


def _tally(rows):
    """{W,L,D} over `rows`, ignoring anything whose Result is not W/L/D."""
    b = {"W": 0, "L": 0, "D": 0}
    for r in rows:
        res = (r.get("Result") or "").strip().upper()
        if res in b:
            b[res] += 1
    return b


def _read_of(b):
    """The Read cell for a tally — a rate with its interval, or the distance to one."""
    n = b["W"] + b["L"]
    if n >= _MIN_SAMPLE:
        lo, hi = _wilson(b["W"], n)
        return f"{100 * b['W'] / n:.0f}%  (95% CI {lo:.0f}–{hi:.0f}%)"
    short = _MIN_SAMPLE - n
    return f"n={n} — {short} more for a read"


def _print_pooled(rows):
    """Pooled reads, because the per-deck split cannot reach the sample floor.

    The per-deck table is the honest way to ask "is THIS deck good", and at 106 decks it
    is also unreachable: the best row after a month of play sits at n=4 against a floor of
    20, and splitting new matches across the roster keeps it there. A record that can
    never be read is a record nobody keeps.

    Pooling fixes the arithmetic by answering a DIFFERENT question, and the difference has
    to stay in front of the reader or the number gets used for deck decisions it cannot
    support. `ALL DECKS` measures the player-and-roster together — "am I winning" — not
    any deck in it. The EVENT split is the one cut worth making at this size: Play and
    Ladder face different opposition, so pooling across them measures a blend of two
    populations, and separating them costs nothing.

    Same `_MIN_SAMPLE` refusal as everywhere else — pooling buys a reachable denominator,
    not permission to read a small one. The distance is printed instead of a percentage
    so the floor reads as a countdown rather than as a wall."""
    graded = [r for r in rows if (r.get("Result") or "").strip().upper() in ("W", "L", "D")]
    if not graded:
        return
    overall = _tally(graded)
    print(f"\n  {'Pooled — a DIFFERENT question than the rows above':50}  {'W':>3} "
          f"{'L':>3} {'D':>3}   Read")
    print("  " + "-" * 68)
    print(f"  {'ALL DECKS — the player and the roster together':50}  {overall['W']:>3} "
          f"{overall['L']:>3} {overall['D']:>3}   {_read_of(overall)}")
    by_event = {}
    for r in graded:
        by_event.setdefault((r.get("Event") or "").strip() or "(no event)", []).append(r)
    if len(by_event) > 1:
        for ev in sorted(by_event, key=lambda e: -len(by_event[e])):
            b = _tally(by_event[ev])
            print(f"    {ev[:48]:48}  {b['W']:>3} {b['L']:>3} {b['D']:>3}   {_read_of(b)}")
    print("\n  A pooled rate says whether YOU are winning, never whether a deck is good — "
          "it\n  averages a tuned deck with a brew. Use it to notice a slump; use the "
          "per-deck\n  rows, once they fill, to judge a deck.")


def parse_annotations(text):
    """([(match_id, {col: value}), ...], [warning, ...]) from `<matchId> key=value ...`.

    The counterpart to `parse_manual`, and the DIFFERENCE is the whole point. A match
    Arena already logged has a real `matchId` and a real W/L; what it lacks is the four
    things only a human knows. Emitting it through `--add` would append a SECOND row for
    a match already recorded — `--add` cannot dedupe, so the record would double-count
    exactly the matches you cared enough to annotate. Keying on the id UPDATES instead,
    which also makes re-annotating idempotent: run it twice and the row is the same."""
    import shlex
    out, warnings = [], []
    for lineno, raw in enumerate((text or "").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parts = shlex.split(line)
        except ValueError as e:
            warnings.append(f"line {lineno}: unbalanced quotes ({e}) — skipped")
            continue
        mid, rest = parts[0], parts[1:]
        if not rest:
            continue                    # an id with nothing to add is a no-op, not an error
        kv, bad = {}, False
        for tok in rest:
            if "=" not in tok:
                warnings.append(f"line {lineno}: {tok!r} is not key=value — line skipped")
                bad = True
                break
            k, v = tok.split("=", 1)
            kv[k.strip().lower()] = v.strip()
        if bad:
            continue
        unknown = set(kv) - {"opp", "why", "play", "note"}
        if unknown:
            warnings.append(f"line {lineno}: unknown key(s) {sorted(unknown)} — skipped. "
                            f"Annotation takes opp, why, play, note; the deck, result and "
                            f"date come from the log and are not editable here.")
            continue
        fields = {}
        if "opp" in kv:
            fields["Opponent Archetype"] = _slug(kv["opp"])
        if "note" in kv:
            fields["Note"] = kv["note"]
        if "play" in kv:
            v = kv["play"].lower()
            if v and v not in _ON_PLAY:
                warnings.append(f"line {lineno}: play={v!r} is not play/draw — dropped")
            else:
                fields["On Play"] = v
        if "why" in kv:
            v = kv["why"].lower()
            if v and v not in LOSS_REASONS:
                warnings.append(f"line {lineno}: why={v!r} is not in the vocabulary — "
                                f"applied anyway, but it will not group with "
                                f"{', '.join(sorted(LOSS_REASONS))}.")
            fields["Loss Reason"] = v
        if fields:
            out.append((mid, fields))
    return out, warnings


def annotate(text, out=MATCHES_CSV, apply=False):
    """`--annotate`: fill the hand-only columns on matches the LOG already recorded.

    An unknown id is a hard reject rather than a silent no-op: a mistyped or truncated
    id would otherwise report success having changed nothing, and the operator would
    believe the annotation landed. A `why` on a non-loss is refused for the same reason
    `--add` refuses it — a loss reason on a win has no reading."""
    rows = load_matches(out)
    by_id = {(r.get("Match ID") or "").strip(): r for r in rows}
    pairs, warnings = parse_annotations(text)
    for w in warnings:
        eprint(f"WARN:  {w}")
    applied, changes = 0, []
    for mid, fields in pairs:
        row = by_id.get(mid)
        if row is None:
            eprint(f"WARN:  no match {mid!r} in {os.path.basename(out)} — skipped. "
                   f"Annotation joins on the Arena match id; ingest the log first.")
            continue
        if fields.get("Loss Reason") and (row.get("Result") or "").upper() != "L":
            eprint(f"WARN:  {mid[:8]}: why={fields['Loss Reason']!r} on a "
                   f"{row.get('Result')} — dropped, the rest applied.")
            fields = {k: v for k, v in fields.items() if k != "Loss Reason"}
            if not fields:
                continue
        was = {k: row.get(k, "") for k in fields}
        if all((was.get(k) or "") == v for k, v in fields.items()):
            continue                      # already says this — idempotent, not a change
        row.update(fields)
        applied += 1
        changes.append((mid, row, was, fields))
    if not changes:
        print("Nothing to change — every annotation already matches what is stored.")
        return 0
    print(f"{applied} match(es) to annotate:")
    for mid, row, was, fields in changes:
        bits = [f"{row.get('Date','?')}  {row.get('Result','?')}  deck {row.get('Deck') or '?':<4}"]
        for k, v in fields.items():
            old = (was.get(k) or "").strip()
            bits.append(f"{k}: {old + ' → ' if old else ''}{v or '(cleared)'}")
        print("   " + "  ·  ".join(bits))
    if not apply:
        print(f"\n(dry run — pass --apply to update {os.path.basename(out)})")
        return 0
    write_matches(rows, out)
    print(f"\nUpdated {applied} match(es) in {os.path.basename(out)}.")
    return 0


def add_manual(text, out=MATCHES_CSV, apply=False, report_after=False):
    """`--add`: append hand-entered matches. DRY RUN by default, like every writer here.

    Existing rows are never touched — this only appends — so a re-paste of lines already
    entered creates DUPLICATES (they get fresh ids; there is no Arena matchId to dedupe
    on). The dry run prints every row so that is visible before it is written, which is
    the only guard available: `--add` cannot tell a repeat from a genuine second game
    against the same deck on the same day, and those are indistinguishable by design."""
    existing = load_matches(out)
    rows, warnings = parse_manual(text, existing_ids={r.get("Match ID") for r in existing},
                                  deck_ids=deck_ids() or None)
    for w in warnings:
        eprint(f"WARN:  {w}")
    if not rows:
        eprint("Nothing to add — no line parsed into a match.")
        return 1
    print(f"{len(rows)} match(es) to add:")
    for r in rows:
        bits = [f"{r['Date']}  {r['Result']}  deck {r['Deck']:<4}"]
        if r["Opponent Archetype"]:
            bits.append(f"vs {r['Opponent Archetype']}")
        if r["On Play"]:
            bits.append(f"on the {r['On Play']}")
        if r["Loss Reason"]:
            bits.append(f"lost to {r['Loss Reason']}")
        if r["Note"]:
            bits.append(f"— {r['Note']}")
        print("   " + "  ".join(bits))
    if not apply:
        print(f"\n(dry run — pass --apply to append to {os.path.basename(out)})")
        return 0
    # WRITE BEFORE NARRATING (G-10): a script that reports success and then writes can
    # die on a BrokenPipeError mid-report having written nothing, which is exactly how
    # two batches were lost in 2026-08.
    write_matches(existing + rows, out)
    print(f"\nAppended {len(rows)} match(es) to {os.path.basename(out)} "
          f"({len(existing) + len(rows)} total).")
    if report_after:
        print()
        report(load_matches(out))
    return 0


def _print_manual_axes(rows):
    """The hand-entered axes: what you faced, whether you were on the play, why you lost.

    Each obeys the SAME read floor as the per-deck table, and for the same reason — these
    columns are the newest and therefore the thinnest, so they are the likeliest place to
    read a story into four games. Loss reasons are the exception to the floor and are
    shown as COUNTS, never a rate: "6 of my losses were flood" is a tally of a thing that
    happened, not an estimate of a probability, so a small n makes it thin rather than
    wrong. Sections print only when something was recorded, so a log-only record shows
    none of this rather than three empty tables."""
    def _tally(key):
        by = {}
        for r in rows:
            v = (r.get(key) or "").strip()
            res = (r.get("Result") or "").strip().upper()
            if not v or res not in ("W", "L", "D"):
                continue
            b = by.setdefault(v, {"W": 0, "L": 0, "D": 0})
            b[res] += 1
        return by

    opp = _tally("Opponent Archetype")
    if opp:
        print(f"\n  {'Opponent archetype':32}  {'W':>3} {'L':>3} {'D':>3}   Read")
        print("  " + "-" * 68)
        for k in sorted(opp, key=lambda k: -(opp[k]["W"] + opp[k]["L"] + opp[k]["D"])):
            b = opp[k]
            n = b["W"] + b["L"]
            read = (f"n={n} — too few to read (need ~{_MIN_SAMPLE})" if n < _MIN_SAMPLE
                    else f"{100*b['W']/n:.0f}%  (95% CI %.0f–%.0f%%)"
                    % _wilson(b["W"], n))
            print(f"  {k[:32]:32}  {b['W']:>3} {b['L']:>3} {b['D']:>3}   {read}")

    play = _tally("On Play")
    if play:
        print(f"\n  {'On the play / draw':32}  {'W':>3} {'L':>3} {'D':>3}   Read")
        print("  " + "-" * 68)
        for k in ("play", "draw"):
            b = play.get(k)
            if not b:
                continue
            n = b["W"] + b["L"]
            read = (f"n={n} — too few to read (need ~{_MIN_SAMPLE})" if n < _MIN_SAMPLE
                    else f"{100*b['W']/n:.0f}%  (95% CI %.0f–%.0f%%)" % _wilson(b["W"], n))
            print(f"  {k[:32]:32}  {b['W']:>3} {b['L']:>3} {b['D']:>3}   {read}")

    why = {}
    for r in rows:
        v = (r.get("Loss Reason") or "").strip()
        if v:
            why.setdefault(v, []).append(r.get("Deck") or "?")
    if why:
        total = sum(len(v) for v in why.values())
        print(f"\n  Why {total} loss(es) happened — COUNTS, not rates")
        print("  " + "-" * 68)
        for k in sorted(why, key=lambda k: -len(why[k])):
            decks = ", ".join(sorted(set(why[k])))
            gloss = LOSS_REASONS.get(k, "(not in the vocabulary)")
            print(f"  {k[:14]:14} {len(why[k]):>3}   {gloss[:30]:30} decks: {decks[:24]}")
        print("  A reason is your judgement AFTER the fact, and the losses you bother to"
              "\n  explain are not a random sample of your losses. Read the big bars.")


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
    _print_pooled(rows)
    _print_manual_axes(rows)
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
    ap.add_argument("--sync-names", action="store_true",
                    help="adopt Arena's deck names into the repo `#: name:` headers "
                         "(GUID-matched decks only; reported without this flag)")
    ap.add_argument("--add", action="store_true",
                    help="record HAND-ENTERED matches (phone games, or anything the log "
                         "cannot see) from `<deck> <W|L|D> [opp= why= play= note=]` "
                         "lines given as the source file or on stdin")
    ap.add_argument("--annotate", action="store_true",
                    help="fill opp/why/play/note on matches the LOG already recorded, "
                         "from `<matchId> key=value` lines — updates rows in place "
                         "rather than appending, so it cannot double-count")
    ap.add_argument("--out", default=MATCHES_CSV)
    args = ap.parse_args()

    if args.annotate:
        if not args.source:
            ap.error("--annotate needs the lines: a file, or '-' for stdin")
        text = sys.stdin.read() if args.source == "-" else \
            open(args.source, encoding="utf-8", errors="replace").read()
        return annotate(text, args.out, apply=args.apply)
    if args.add:
        if not args.source:
            ap.error("--add needs the lines: a file, or '-' for stdin")
        text = sys.stdin.read() if args.source == "-" else \
            open(args.source, encoding="utf-8", errors="replace").read()
        return add_manual(text, args.out, apply=args.apply, report_after=args.report)
    if args.report and not args.source:
        return report(load_matches(args.out))
    if args.sync_names and not args.source:
        # Sourceless reconcile. The repo ALREADY holds Arena's name for every deck with
        # an `#: arena:` header — harvested from real pastes by previous runs — so the
        # names are on hand and no fresh log is needed. Not circular: the header is
        # Arena's answer, recorded; this only asks whether `#: name:` still agrees with
        # it. Without this the feature needs a paste covering all 106 decks to reconcile
        # a divergence that accumulated over months, which is a capability nobody
        # reaches (G-53).
        written, plan = sync_deck_names_from_headers(apply=True)
        if not plan:
            print("Every GUID-paired deck's `#: name:` already matches its Arena name.")
        return 0
    if not args.source:
        ap.error("give a log file (or '-' for stdin), or use --report")
    # `--report` WITH a source used to be dropped on the floor: the gate above requires
    # `not args.source`, so the natural post-ingest invocation
    # (`parse_matches.py session.log --apply --report`) did the ingest and printed no
    # report, with nothing said. Ingest first, then report — the composition the flag
    # combination obviously means (broad-scan BS5-09).

    try:
        text = sys.stdin.read() if args.source == "-" else \
            open(args.source, encoding="utf-8", errors="replace").read()
    except OSError as e:
        eprint(f"Could not read {args.source!r}: {e}")
        return 1

    def _with_report(rc):
        """Run `--report` after the ingest when both were asked for (BS5-09), on every
        SUCCESS path — including the summaries-only one, which is a legitimate outcome
        and returned before the report on the first pass at this fix. Error paths are
        deliberately excluded: a report after a failed read would read as reassurance.
        Reads matches.csv back rather than reporting `existing + fresh` in memory, so a
        dry run honestly describes the record as it STANDS, not as it would stand."""
        if args.report:
            print()
            report(load_matches(args.out))
        return rc

    if args.map_decks:
        map_decks(text, apply=args.apply)
        # The roster-scale header pass is exactly where a roster-scale RENAME shows up,
        # so it offers the same adoption the match path does.
        sync_deck_names(text, apply=args.sync_names)
        return _with_report(0)

    rows, warnings = parse_log(text, me=args.me)
    for w in warnings:
        eprint(f"WARN:  {w}")

    # Header upkeep rides along with every ingest — BEFORE the mapping is built, so a
    # header written from this paste resolves this paste's own matches, and BEFORE the
    # no-matches bailout, so a paste of deck summaries alone (the --map-decks extraction
    # shape) still keeps headers current instead of dying with a misleading error.
    sync_headers(text, apply=args.apply)
    # AFTER the header sync, which is what establishes the GUID pairing this reads. A
    # deck first seen in this paste therefore becomes eligible in the SAME run — but only
    # via the header the sync just wrote, never via the number-prefix guess that found it.
    sync_deck_names(text, apply=args.sync_names)

    if not rows:
        if parse_deck_names(text):
            print("No completed matches in this paste — deck summaries only. Header "
                  "changes, if any, are reported above"
                  + ("." if args.apply else " (dry run — pass --apply to write them)."))
            return _with_report(0)
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
        repo_names = deck_names()
        print(f"\nDeck attribution — {len(shown)} Arena deck(s) seen:")
        guessed = False
        for (name, guid), (did, how) in sorted(shown.items()):
            label = name or guid
            target = f"deck {did}  ({how})" if did else "UNRESOLVED — blank Deck"
            # The repo deck's own name, on the GUESS route only. The explicit header
            # route needs no confirming — a human wrote it — but the prefix route
            # validates the NUMBER and nothing else, and --apply turns it into a
            # permanent header. See `deck_names` for why this discloses instead of gates.
            extra = ""
            if did and how == "name prefix":
                guessed = True
                extra = f"  — repo deck is {repo_names.get(did, '?')!r}, confirm it"
            print(f"   {label[:40]:40}  ->  {target}{extra}")
        if guessed:
            print("\n   A `name prefix` route matched on the LEADING NUMBER only. If the "
                  "repo deck\n   named above is not the deck you played, stop: --apply "
                  "writes that guess into\n   the deck file as a `#: arena:` header, and "
                  "every later match resolves to it.")
        print()

    print(f"Found {len(rows)} completed match(es); {len(fresh)} new, "
          f"{len(rows) - len(fresh)} already recorded.")
    for r in fresh:
        deck_label = r["Deck"] or f"(unattributed: {r['Arena Deck'] or 'deck unknown'})"
        ended = f" by {r['Ended By'].lower()}" if r.get("Ended By") else ""
        print(f"   {r['Date']}  {r['Result']}  {r['Games Won']}-{r['Games Lost']}{ended}  "
              f"{deck_label}  vs {r['Opponent Avatar'] or '?'}  [{r['Event']}]"
              f"   {_result_evidence(r)}")
    if fresh:
        print("\n   Evidence is the raw finalMatchResult read: W when your team is the "
              "winning\n   team, L when it is not, D when there is none. Check it — an "
              "inverted seat\n   read would make every row here wrong in the same "
              "direction.")
    if not args.apply:
        print("\n(dry run — pass --apply to write matches.csv)")
        return _with_report(0)
    if not fresh:
        print("\nNothing new to write.")
        return _with_report(0)
    write_matches(existing + fresh, args.out)
    print(f"\nWrote {args.out} ({len(existing) + len(fresh)} total). "
          f"See the record with: parse_matches.py --report")
    return _with_report(0)


if __name__ == "__main__":
    sys.exit(main())
