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

A fourth shape is optional and comes from `scripts/mtga_extract.sh` (the Mac's
~/mtga-logs/extract.sh), which boils each finished game's play-by-play down to one line:

    [MTGA-GAME]9/27/2026 9:50:18 AM: {"matchId": "...", "game": 1, "seat": 2, "first": 1,
        "turns": 14, "mulligans": {"1": 0, "2": 1}, ..., "cards": ["1:97950:RG", ...]}

It joins to a match on the matchId and fills who went first, mulligans, the last turn
number and the cards the opponent showed — see `GAME_FACT_PREFIX`.

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
          # HAND-ENTERED, appended 2026-08-20 (`--add` / `--annotate`). The match-result
          # lines say nothing about what you faced, whether you were on the play, or why
          # you lost, and these are the fields that answer "what should I change". All
          # four are OPTIONAL — a reader must treat blank as "not recorded", never as a
          # value. `On Play` is ALSO filled from the play-by-play since 2026-09-27 (see
          # `GAME_FACT_PREFIX`), but only when blank: a value you typed is never replaced.
          "On Play", "Opponent Archetype", "Loss Reason", "Note",
          # FROM THE PLAY-BY-PLAY, appended 2026-09-27 — see `LOG_DETAIL_COLUMNS`.
          "My Mulligans", "Opp Mulligans", "Turns", "Opponent Colors", "Opponent Cards"]

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

# A match the owner VOIDS — stepped away mid-game, a misclick into a queue — keeps its row
# with this Result. Deleting the row would not remove the match: dedup keys on the row, so
# the next paste (which `mtga-matches` starts from the last copy's day) would re-add it as
# a live loss. Every tally already skips a Result that is not W/L/D; `--report` names the
# voided ones instead of flagging them as unreadable, and the original result stays
# derivable from Games Won / Games Lost, so `void=no` restores it.
VOID = "X"
_UNVOID = {"no", "undo", "restore"}

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
# The deck's last EDIT. A deck deleted in the client and re-imported as a new deck gets a
# new DeckId with a fresh LastUpdated, which is how the newest of several same-named
# copies is told apart (`_newest_copy`).
_LASTUPDATED_RE = re.compile(r'"LastUpdated".{0,40}?'
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


# ── The play-by-play: one `[MTGA-GAME]` line per finished game ──────────────────────
#
# G-74 recorded the match log as blind to what you faced, whether you were on the play
# and why you lost. That was true of the lines this module read, NOT of the log: with
# Detailed Logs on, Arena also writes the full game state (GREMessageType_GameStateMessage)
# — the turn structure, each player's mulligans and every card either side showed. It is
# 1.0-2.4 MB per match, so `scripts/mtga_extract.sh` reduces each finished game to one
# `[MTGA-GAME]` line on the Mac and this module only reads that line. It carries no
# userId and no player name.
#
# "Why you lost" stays a human call (`--annotate`): the log shows what happened, not
# which part of it decided the game.
GAME_FACT_PREFIX = "[MTGA-GAME]"
_GAME_FACT_RE = re.compile(r"^\[MTGA-GAME\][^{]*(\{.*\})\s*$")
# Filled only from those lines, and RECOMPUTED whenever a run sees a match's game lines:
# they are derived, so the log is their authority, which is also what lets a later run
# replace a `#<id>` placeholder once Scryfall can name the card. `Turns` is Arena's own
# turn number, which counts BOTH players' turns — 14 is each player's 7th. A match of
# several games joins each game's value with "/".
LOG_DETAIL_COLUMNS = ("My Mulligans", "Opp Mulligans", "Turns", "Opponent Colors",
                      "Opponent Cards")
# grpId -> card name, cached so each card costs one Scryfall request ever. The log names
# a card only by Arena's numeric id (its `name` field is a localisation id, not text).
ARENA_CARDS_CSV = os.path.join(REPO_ROOT, "arena-cards.csv")
_ARENA_CARDS_HEADER = ["Arena ID", "Card Name"]
ARENA_CARD_URL = "https://api.scryfall.com/cards/arena/{}"


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def parse_game_facts(text):
    """({match_id: [game, ...] ordered by game number}, [warning, ...]).

    One entry per (match, game); a repeated line replaces the earlier one, so a paste
    carrying both the archived and the live copy of a game counts it once."""
    games, warnings = {}, []
    for raw in (text or "").splitlines():
        if not raw.startswith(GAME_FACT_PREFIX):
            continue
        m = _GAME_FACT_RE.match(raw.strip())
        try:
            fact = json.loads(m.group(1)) if m else None
        except json.JSONDecodeError:
            fact = None
        if not isinstance(fact, dict) or not fact.get("matchId"):
            warnings.append(f"a {GAME_FACT_PREFIX} line did not parse — it looks truncated; "
                            f"that game's details are skipped (the match itself is not).")
            continue
        games.setdefault(fact["matchId"], {})[_int(fact.get("game")) or 1] = fact
    return {mid: [g[n] for n in sorted(g)] for mid, g in games.items()}, warnings


# Arena ids below this are rules objects, not printed cards: the first real log (2026-09-27)
# showed an opponent object with grpId 3 — a face-down permanent, which has no name to
# look up and would sit in Opponent Cards as "#3" forever. Real card ids run from ~5000.
_MIN_CARD_GRPID = 1000


def _game_cards(game):
    """[(owner seat, grpId, colours, is_land)] from a game line's "owner:grpId:flags"."""
    out = []
    for tok in game.get("cards") or []:
        parts = str(tok).split(":")
        if len(parts) != 3 or not parts[0].isdigit() or not parts[1].isdigit():
            continue
        if int(parts[1]) < _MIN_CARD_GRPID:
            continue
        flags = parts[2]
        out.append((int(parts[0]), int(parts[1]),
                    "".join(c for c in "WUBRG" if c in flags), "L" in flags))
    return out


def _seats(game):
    """(your seat, the opponent's seat); 0 where the line cannot say."""
    me = _int(game.get("seat"))
    known = {_int(x) for x in (game.get("mulligans") or {})} | {1, 2}
    others = sorted(x for x in known if x and x != me)
    return me, (others[0] if me and others else 0)


def opponent_card_ids(games):
    """Every grpId the opponent showed across a match's games."""
    ids = set()
    for g in games:
        _me, opp = _seats(g)
        ids |= {grp for owner, grp, _c, _l in _game_cards(g) if owner == opp}
    return ids


def match_details(games, names=None):
    """(fields, problem) — the matches.csv cells a match's game lines imply.

    `problem` is a one-line reason when nothing can be derived. Without YOUR seat nothing
    here has an owner — "first" and every mulligan count are per SEAT — so the match is
    skipped rather than guessed, the same stance `parse_log` takes on a missing header."""
    names = names or {}
    if not games:
        return {}, "no game lines"
    seat, _opp = _seats(games[0])
    if not seat:
        return {}, "the game lines do not say which seat was yours"
    out = {}
    first = _int(games[0].get("first"))
    if first:
        out["On Play"] = "play" if first == seat else "draw"

    def per_game(fn):
        return "/".join(str(fn(g)) for g in games)
    out["My Mulligans"] = per_game(
        lambda g: _int((g.get("mulligans") or {}).get(str(_seats(g)[0]))))
    out["Opp Mulligans"] = per_game(
        lambda g: _int((g.get("mulligans") or {}).get(str(_seats(g)[1]))))
    out["Turns"] = per_game(lambda g: _int(g.get("turns")))
    colours, cards = set(), []
    for g in games:
        _me, opp = _seats(g)
        for owner, grp, col, _land in _game_cards(g):
            if owner != opp:
                continue
            colours |= set(col)
            label = names.get(grp) or f"#{grp}"
            if label not in cards:
                cards.append(label)
    # Colours of the opponent's NONLAND cards as Arena reports them — a card's colours,
    # not its identity or its mana; lands carry none, so a deck seen only as lands reads
    # blank rather than guessed.
    out["Opponent Colors"] = "".join(c for c in "WUBRG" if c in colours)
    out["Opponent Cards"] = "; ".join(cards)
    return out, None


def load_arena_cards(path=None):
    """{grpId: card name} from the cache; {} when there is none yet."""
    path = path or ARENA_CARDS_CSV
    if not os.path.exists(path):
        return {}
    with open(path, newline="", encoding="utf-8") as fh:
        return {int(r["Arena ID"]): r["Card Name"] for r in csv.DictReader(fh)
                if (r.get("Arena ID") or "").strip().isdigit()
                and (r.get("Card Name") or "").strip()}


def write_arena_cards(names, path=None):
    path = path or ARENA_CARDS_CSV

    def _w(fh):
        w = csv.writer(fh)
        w.writerow(_ARENA_CARDS_HEADER)
        for grp in sorted(names):
            w.writerow([grp, names[grp]])
    atomic_write(path, _w, backup=False)


def _scryfall_arena_name(grp):
    """The card Scryfall files under Arena id `grp`, or None if it has none (a token,
    or a card Scryfall has not indexed yet). ScryfallUnavailable propagates."""
    import time
    import scryfall
    time.sleep(0.1)                        # Scryfall asks for 50-100 ms between requests
    try:
        card = scryfall.get_json(ARENA_CARD_URL.format(int(grp)))
    except scryfall.NotFound:
        return None
    return (card or {}).get("name") or None


def resolve_arena_names(grpids, cache, fetch=None):
    """({grpId: name} for everything known, {grpId: name} newly fetched, error or None).

    A miss is NOT cached, so a card Scryfall indexes later still resolves on a later
    run. An outage stops the lookups and is reported: the match is still written, with
    `#<id>` for the cards it could not name, and the next run that sees the game line
    names them."""
    import scryfall
    fetch = fetch or _scryfall_arena_name
    names, new = dict(cache), {}
    for grp in sorted(set(grpids) - set(names)):
        try:
            name = fetch(grp)
        except scryfall.ScryfallUnavailable as e:
            return names, new, str(e)
        if name:
            names[grp] = new[grp] = name
    return names, new, None


def apply_game_details(rows_by_id, facts, names):
    """Fill each recorded match's play-by-play columns. Returns (changes, orphans, notes).

    `changes` is [(match_id, row, {column: (old, new)})] for rows whose cells moved;
    `orphans` counts matches with game lines but no row (their result line was not in
    this paste and they are not recorded yet); `notes` are per-match warnings. `On Play`
    is written only into a BLANK cell — a value typed by hand is kept even when the log
    disagrees, and the disagreement is reported rather than resolved."""
    changes, notes, orphans = [], [], 0
    for mid, games in facts.items():
        row = rows_by_id.get(mid)
        if row is None:
            orphans += 1
            continue
        fields, problem = match_details(games, names)
        if problem:
            notes.append(f"{mid[:8]}: {problem} — details skipped")
            continue
        moved = {}
        for col, new in fields.items():
            old = (row.get(col) or "").strip()
            if col == "On Play" and old:
                if old != new:
                    notes.append(f"{mid[:8]}: On Play is {old!r} by hand but the log says "
                                 f"{new!r} — kept yours; fix it with --annotate if the "
                                 f"log is right")
                continue
            if old != new:
                moved[col] = (old, new)
                row[col] = new
        if moved:
            changes.append((mid, row, moved))
    return changes, orphans, notes


def opponent_spells(games, names, limit=4):
    """The opponent's first NONLAND cards, by name, in the order Arena first showed them.

    A land says little about what beat you, and the stored `Opponent Cards` keeps them all
    (they give the colours), so a one-line prompt reads better from this subset."""
    out = []
    for g in games:
        _me, opp = _seats(g)
        for owner, grp, _c, land in _game_cards(g):
            if owner == opp and not land:
                label = names.get(grp) or f"#{grp}"
                if label not in out:
                    out.append(label)
    return out[:limit]


def _print_missing_details(fresh, facts, out=print):
    """Name the NEW matches that have no play-by-play line (item 5, 2026-09-27).

    Without this a match with no details was simply absent from the details block, so a
    phone game and an extractor that is not installed looked the same as nothing at all."""
    if not fresh:
        return
    bare = [r for r in fresh if (r.get("Match ID") or "").strip() not in facts]
    if not bare:
        return
    if not facts:
        out(f"\nNo game details in this paste for the {len(fresh)} new match(es) — either "
            f"`extract.sh` is not installed on the Mac (see /log-matches Stage 0) or they "
            f"were played on another device.")
        return
    out(f"\n{len(bare)} new match(es) have no play-by-play line — a phone game, or a log "
        f"that rotated before the extractor saw it:")
    for r in bare:
        out(f"   {r.get('Date') or '?'}  {r.get('Result') or '?'}  deck "
            f"{r.get('Deck') or '?':<4} {(r.get('Match ID') or '')[:8]}")


def _print_loss_prompt(losses, facts, names, out=print):
    """Ready-to-fill `--annotate` lines for the losses this run WROTE (item 1).

    The why column was empty on all 94 recorded losses: the fill-in step lived on the
    dashboard and in the skill's prose, and a paste that has just landed is the one moment
    the owner still remembers the game. The comment line carries the game details so the
    question can be answered from it.

    BS11-35: this text used to say "a blank value records nothing" while `--annotate`'s
    documented, tested contract (log-matches Stage 1c, README) is that an empty value
    CLEARS the field — the way a wrong annotation is fixed. On these rows the fields are
    still empty, so a blank left in the template changes nothing; the wording now says
    what the writer actually does, so the line is not reused against an annotated row
    on the strength of a false promise."""
    if not losses:
        return
    out(f"\nWhy did the {len(losses)} new loss(es) happen? One word each — "
        f"{' / '.join(LOSS_REASONS)} — then run the lines through --annotate "
        f"(a blank value CLEARS that field — on these new rows it is already empty):")
    for r in losses:
        mid = (r.get("Match ID") or "").strip()
        bits = [f"{r.get('Date') or '?'}  deck {r.get('Deck') or '?'}"]
        if r.get("On Play"):
            bits.append(f"on the {r['On Play']}")
        if r.get("Turns"):
            bits.append(f"turn {r['Turns']}")
        seen = opponent_spells(facts.get(mid, []), names) if mid in facts else []
        opp = r.get("Opponent Colors") or ""
        if seen or opp:
            bits.append(f"vs {opp or '?'}" + (f": {'; '.join(seen)}" if seen else ""))
        elif mid not in facts:
            bits.append("no game details")
        out(f"   # {' · '.join(bits)}")
        out(f"   {mid} why= opp=")


_BASIC_NAMES = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"}


def deck_history(rows, deck_id, out=print):
    """`--report --deck <id>`: one deck's matches, one line each (item 4, 2026-09-27).

    The pooled report answers "am I winning"; this answers "what does THIS deck meet and
    lose to", which is the question a tune actually asks. The same restraint applies and is
    printed: below `_MIN_SAMPLE` there is no rate, the loss tallies are COUNTS, and nothing
    here is evidence for a swap or a tier letter."""
    want = _norm_id(deck_id)
    mine = sorted((r for r in rows if _norm_id(r.get("Deck") or "") == want),
                  key=lambda r: (r.get("Date") or "", r.get("Match ID") or ""))
    if not mine:
        out(f"No recorded matches for deck {deck_id}.")
        return 0
    b = {"W": 0, "L": 0, "D": 0}
    voided = 0
    for r in mine:
        res = (r.get("Result") or "").strip().upper()
        if res in b:
            b[res] += 1
        voided += res == VOID
    n = b["W"] + b["L"]
    read = (f"n={n} — too few to read (need ~{_MIN_SAMPLE})" if n < _MIN_SAMPLE
            else f"{100 * b['W'] / n:.0f}%  (95% CI %.0f–%.0f%%)" % _wilson(b["W"], n))
    extra = f" (+{voided} voided, not counted)" if voided else ""
    out(f"Deck {deck_id} — {len(mine) - voided} match(es){extra}, "
        f"{b['W']}-{b['L']}-{b['D']}   {read}\n")
    out(f"  {'Date':10}  R  {'On':4}  {'Turns':5}  {'Opp':5}  {'Why':10}  Opponent cards")
    out("  " + "-" * 86)
    for r in mine:
        cards = [c for c in (r.get("Opponent Cards") or "").split("; ")
                 if c and c not in _BASIC_NAMES]
        shown = "; ".join(cards[:4]) + (f"  (+{len(cards) - 4})" if len(cards) > 4 else "")
        out(f"  {r.get('Date') or '?':10}  {(r.get('Result') or '?')[:1]}  "
            f"{(r.get('On Play') or '·')[:4]:4}  {(r.get('Turns') or '·')[:5]:5}  "
            f"{(r.get('Opponent Colors') or '·')[:5]:5}  {(r.get('Loss Reason') or '·')[:10]:10}"
            f"  {shown[:48] or '·'}")
    losses = [r for r in mine if (r.get("Result") or "").upper() == "L"]
    for title, key in (("losses by opponent colours", "Opponent Colors"),
                       ("losses by reason", "Loss Reason")):
        tally = {}
        for r in losses:
            k = (r.get(key) or "").strip() or "(not recorded)"
            tally[k] = tally.get(k, 0) + 1
        if tally:
            out(f"\n  {title.capitalize()} — COUNTS, not rates: "
                + ", ".join(f"{k} {v}" for k, v in sorted(tally.items(),
                                                        key=lambda kv: (-kv[1], kv[0]))))
    out("\nA handful of games says what this deck has MET, not how good it is. Read it for "
        "patterns worth a closer look, never as a reason to cut a card or move a tier.")
    return 0


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


def _norm_id(raw):
    """Zero-padded ids accepted, like every by-id command (G-82 / BS8-17): `06 L` used
    to be refused while `deck.py stats 06` worked. Delegates to deck.py when available."""
    try:
        import deck as dk
        return dk._norm_deck_id(raw)
    except Exception:
        return (raw or "").strip().lower()


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


def _log_dt(match):
    """A naive datetime from a `_LASTPLAYED_RE` / `_LASTUPDATED_RE` match, or None."""
    if not match:
        return None
    try:
        return datetime.datetime.fromisoformat(match.group(1)).replace(tzinfo=None)
    except ValueError:
        return None


def parse_deck_times(text):
    """{DeckId GUID: (last_updated, last_played)} — the latest of each seen in the paste.

    Read only from a line carrying exactly ONE deck summary, so a timestamp can never be
    credited to a neighbouring deck. Either half may be None."""
    out = {}
    for raw in (text or "").splitlines():
        flat = raw.replace("\\", "")
        found = _SUMMARY_RE.findall(flat)
        if len(found) != 1:
            continue
        guid = found[0][0]
        upd, played = _log_dt(_LASTUPDATED_RE.search(flat)), _log_dt(_LASTPLAYED_RE.search(flat))
        old_upd, old_played = out.get(guid, (None, None))
        out[guid] = (max(filter(None, (upd, old_upd)), default=None),
                     max(filter(None, (played, old_played)), default=None))
    return out


def _newest_copy(hits, times):
    """(name, guid) of the newest of several Arena decks claiming one repo deck, or None.

    THE OWNER'S WORKFLOW (2026-09-27): after a significant edit the old Arena deck is
    deleted and the new version imported as a NEW deck, so the client can hold several
    copies under one name and the MOST RECENT is the correct one. Deck 58 had three
    "58 Treasure Planet" copies and warned on every ingest because this used to refuse.

    Newest-wins applies only when every claimant carries the SAME name (typography-blind)
    and a timestamp. NOT `_name_key`: that drops a trailing "(...)" as a repo-side gloss,
    and in an ARENA name the parentheses are part of the name — "07 Earth's Mightiest
    (old)" is a different deck, which the first draft of this treated as a copy. Two differently named decks resolving to one repo deck
    are not copies of one deck, so that stays a conflict: a header naming the wrong one is
    worse than no header. Ordered by LastUpdated, then LastPlayed, then the GUID, so a tie
    cannot make the pick depend on iteration order (G-54)."""
    if len({re.sub(r"[^a-z0-9]+", "", (n or "").lower()) for n, _g in hits}) != 1:
        return None
    floor = datetime.datetime.min
    keyed = []
    for name, guid in hits:
        upd, played = (times or {}).get(guid, (None, None))
        if upd is None and played is None:
            return None
        keyed.append(((upd or floor, played or floor, guid), name, guid))
    _key, name, guid = max(keyed)
    return name, guid


def _arena_header_plan(names, times=None, notes=None):
    """[(deck_id, path, header_line, status)] for the decks `names` resolves to.

    Status is one of `add` / `update` / `unchanged` / `conflict`. A CONFLICT — two Arena
    decks resolving to one repo deck — writes nothing: a header naming the wrong one of two
    decks is worse than no header, because the parser would then attribute matches to it
    with full confidence. The exception is several same-named COPIES, which is how the
    owner replaces a deck (`_newest_copy`): the newest is written, and a line naming the
    superseded copies is appended to `notes` when a list is passed."""
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
            pick = _newest_copy(hits, times)
            if pick is None:
                plan.append((did, rec["path"], "; ".join(n for n, _ in hits), "conflict"))
                continue
            name, guid = pick
            if notes is not None:
                notes.append((did, f"{len(hits)} Arena decks named {name!r} claim deck "
                                   f"{did}; using the newest ({guid[:8]}). The older "
                                   f"copies' matches still resolve by name."))
        else:
            name, guid = hits[0]
        line = f"#: arena: {name}, {guid}"
        try:
            with open(rec["path"], encoding="utf-8") as fh:
                current = [ln.rstrip("\n") for ln in fh]
        except OSError:
            continue
        existing = [ln for ln in current if _ARENA_HEADER_RE.match(ln)]
        status = "unchanged" if existing == [line] else ("update" if existing else "add")
        # A paste covering only an OLD copy's period must not move the header BACK to it
        # (2026-10-06). With one claimant there is nothing to compare inside the paste, so
        # compare against the record: if the copy the header already names played LATER
        # (matches.csv) than anything the paste shows for the claimant, the header is
        # newer and stays. Day resolution, strictly earlier only — a tie still updates.
        if status == "update" and len(existing) == 1:
            held = _GUID_RE.search(existing[0])
            if held and held.group(0).lower() != guid.lower():
                held_last = _guid_last_played(held.group(0))
                new_last = _guid_last_played(guid, times)
                if held_last and new_last and new_last < held_last:
                    status = "older"
        plan.append((did, rec["path"], line, status))
    return plan


def _guid_last_played(guid, times=None):
    """The latest DAY an Arena deck GUID is known to have been used: the paste's own
    LastPlayed/LastUpdated stamp when given, else its newest matches.csv row. None when
    neither knows it."""
    days = []
    upd, played = (times or {}).get(guid, (None, None))
    days += [t.date() for t in (upd, played) if t]
    try:
        with open(MATCHES_CSV, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if (r.get("Arena Deck ID") or "").strip().lower() == guid.lower():
                    try:
                        days.append(datetime.date.fromisoformat((r.get("Date") or "")[:10]))
                    except ValueError:
                        pass
    except OSError:
        pass
    return max(days) if days else None


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


# A trailing "(...)" on a repo `#: name:` is a GLOSS, not part of the name — the one-line
# premise the roster carries so a creative name still says how the deck works ("Hoofprint
# (creatures are the mana)"). It exists only on this side: Arena holds the short name, and
# nothing here writes to Arena. So it belongs in exactly the category `_name_key` already
# has for the curly apostrophe and the doubled space — a difference that is NOT a rename.
#
# Without this the reconciler reads every glossed deck as renamed. Measured before the
# change: 49 glosses would take the standing divergence report from 8 lines to 57, burying
# the 8 real ones — a permanent false warning, which is the bar this project holds a
# standing report to.
_NAME_GLOSS_RE = re.compile(r"\s*\([^()]*\)\s*$")


def _name_gloss(s):
    """The trailing "(...)" gloss on a deck name, without surrounding space, or ''."""
    m = _NAME_GLOSS_RE.search((s or "").strip())
    return m.group(0).strip() if m else ""


def _name_bare(s):
    """A deck name with its trailing gloss removed."""
    return _NAME_GLOSS_RE.sub("", (s or "").strip()).strip()


def _name_key(s):
    """Comparison key for two deck names: words only, case- and punctuation-blind.

    The trigger for a rename must be a difference in WORDS, never in typography. Arena
    writes a curly apostrophe ("Earth’s"), a doubled space ("66  Lethal Protector") and a
    hyphen for an em dash; all three are the SAME name and must not churn the repo. A
    trailing repo-side gloss is the same kind of difference (see `_NAME_GLOSS_RE`) and is
    dropped before comparing."""
    return re.sub(r"[^a-z0-9]+", "", _name_bare(s).lower())


# What may sit between a parent name Arena repeats and the variant's own name. `_name_key`
# ignores punctuation, so the tail search in `_adopted_name` stops AT the separator and
# this strips it. The colon is the one that cost something: "69a Bear-Wolf: Ursa Major"
# adopted as "Bear-Wolf — : Ursa Major" while only " —-" were stripped (2026-09-25).
_VARIANT_SEPARATORS = " \t—–-:|/,"


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
    # The repo's own gloss survives an adoption — Arena never had it to offer, so dropping
    # it here would make every `--sync-names --apply` silently strip the premise lines.
    gloss = _name_gloss(rec.get("name"))
    parent_name = _name_bare(parent_name)
    if not (rec.get("variant") and parent_name):
        return (rest + " " + gloss).strip() if gloss else rest
    pk, rk = _name_key(parent_name), _name_key(rest)
    if rk.startswith(pk) and rk != pk:
        # Arena repeated the parent — keep the repo's spelling of it, not Arena's.
        tail = rest
        while tail and _name_key(tail) != rk[len(pk):]:
            tail = tail[1:]
        # …but only if the parent ends on a WORD boundary (BS11-38): the keys are
        # letters-only, so parent "Dino" matched the front of "Dinosaur Party" and the
        # adoption read "Dino — saur Party". A cut inside a word is not a repeated parent.
        cut = len(rest) - len(tail)
        if tail and cut and rest[cut - 1].isalnum() and tail[0].isalnum():
            tail = ""
        rest = tail.lstrip(_VARIANT_SEPARATORS).strip() or rest
    out = f"{parent_name} — {rest}" if _name_key(rest) != pk else parent_name
    return (out + " " + gloss).strip() if gloss else out


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
        if adopted and _rename_key(adopted, current) != _rename_key(current, current):
            plan.append((did, rec["path"], current, adopted))
    return plan


def _rename_key(name, current):
    """`_name_key` for the rename test, stripping only the REPO's own gloss (BS11-37).

    `_name_key` drops ANY trailing "(...)", which is right for the repo-side premise gloss
    and wrong when the "(...)" came from ARENA: "Foo (old)" → "Foo (new)" keyed "foo" on
    both sides and the rename was invisible. `_adopted_name` re-appends the current name's
    gloss, so removing exactly that gloss (when present) leaves Arena's words — including
    any parenthetical Arena itself wrote — to compare."""
    g = _name_gloss(current)
    s = (name or "").strip()
    if g and s.endswith(g):
        s = s[: -len(g)].strip()
    return re.sub(r"[^a-z0-9]+", "", s.lower())


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
    is editorial, and this tool adopts, it does not compose.

    Compared on the BARE name through `_name_key`. The raw `#: name:` carries the
    parent's "(...)" gloss, which no variant repeats, so a raw substring test could never
    fire on a glossed parent: renaming 26 "Iron Forge (ramp into artifact bombs)" flagged
    neither "Iron Forge — Virulent" nor "Iron Forge — Ancient Decay" (2026-09-25), and 69
    the same for both of its variants."""
    if not old_name or _name_key(old_name) in _name_key(adopted):
        return []
    old_key = _name_key(old_name)
    if not old_key:
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
            and old_key in _name_key(d.get("name") or "")]


# The marker a `#` line opens with — "#:", "#~" or a bare "#" — plus one "key:" label.
# Stripped so a name WRAPPED across two header lines reads as one phrase once the lines
# are joined: deck 43 cites "12 Drawn\n#: tier: Conclusions", which no line-at-a-time
# test can see.
_PROSE_PREFIX_RE = re.compile(r"^#[:~]?\s*(?:[a-z][a-z-]*\s*:)?\s*", re.I)
# Header lines that NAME a deck rather than cite one. A variant's `#: name:` carrying
# the parent is `_variant_orphans`' report, not a stranded citation, and `#: arena:` is
# Arena's string, which a repo rename does not touch.
_NAME_LINE_RE = re.compile(r"^#:\s*(?:name|arena)\s*:", re.I)


def _citation_prose(path):
    """A deck file's `#` prose as ONE line — markers stripped, name/arena lines dropped,
    curly apostrophes folded to straight so Arena's typography cannot hide a match."""
    with open(path, encoding="utf-8") as fh:
        lines = [_PROSE_PREFIX_RE.sub("", ln.rstrip("\n")) for ln in fh
                 if ln.startswith("#") and not _NAME_LINE_RE.match(ln)]
    return " ".join(lines).replace("’", "'")


def _cited_by_id(text, start, end, deck_id):
    """True when the deck's own id sits beside the name: "41 Soul Inversion",
    "deck 24 (Eternal Flame", "Black Sun (1)", "04 Quantum Realm" for deck 4."""
    n = re.escape((deck_id or "").lstrip("0") or "0")
    before, after = text[max(0, start - 16):start], text[end:end + 16]
    return bool(re.search(rf"(?<![\w.])(?:deck[\s-]*)?0*{n}\s*\(?\s*$", before, re.I)
                or re.match(rf"\s*\(\s*(?:deck\s*)?0*{n}\s*\)", after, re.I))


def _name_citations(old_name, own_id, adopted):
    """Deck ids whose `#` header prose names `old_name` and would be left stale.

    A rename is not a local edit: 50 of the 106 decks are named inside another deck's
    header prose, so adopting Arena's name can strand a reference the rationale audit
    cannot see (it checks CARD names and FIGURES, never deck names). Nothing rewrites
    prose automatically — that is editorial — so the cost is shown at decision time
    instead.

    Suppressed when the adopted name still CONTAINS the old one ("Unlock" -> "Unlocked",
    "Bird Brain" -> "Bird Brain — Bant"): the citation keeps reading correctly, and
    flagging it would bury the five real cases in noise.

    WHAT COUNTS AS A CITATION, measured 2026-09-25 against a hand-labelled roster sweep
    (every deck's name searched in every other deck's prose, 78 real deck->file
    citations). The rule it replaced — the raw `#: name:` as a case-insensitive substring,
    line by line — flagged 53 pairs at 58% precision and 40% recall. Three independent
    faults, each fixed here:
      * the GLOSS: the raw name carries its "(...)" premise, which prose never repeats,
        so every glossed deck was invisible (41 in 42, 71 in 25, 26 in 26a and 56b);
      * CASE: "Second Draw" matched "second draw" and "Sacrifices" matched the verb in 15
        decks, so a name is matched case-sensitively on word boundaries;
      * CARD NAMES that contain a deck name — "Web of Life and Destiny", "Team Avatar",
        "Herd Heirloom", "Secret of Bloodbending" — are masked, unless the deck's id sits
        beside the name ("23 Avengers Assemble!" cites the deck; "Avengers Assemble!"
        alone is the card). Joining wrapped lines is what lets the mask see "Herd /
        Heirloom", and it also recovered three real citations split across a line break.
    Result: 81 flagged, 78 real (96%), recall 100%. Requiring the id adjacent everywhere
    was measured too — 100% precision but 74% recall, since prose often names a deck bare
    ("vs Zaffai's Maelstrom"). The 3 residual false hits are card SHORTHANDS
    ("Triceraton" for Triceraton Commander, "Web of Life" for Web of Life and Destiny);
    masking prefixes too would cost real bare citations, so they are left.

    A VARIANT is cited by its OWN half: "48a Motor Pool", never "Doombots — Motor Pool".
    So the part after " — " is searched as well, but only with the id beside it — a tail
    is often a common word ("Competitive", "Brawl", "Encore") and the id is what makes it
    a reference. Measured: 4 such citations on the roster, 4 real. The 2026-09-25 rename
    of 48a had three (26b, 61, 74a) and this function reported none."""
    if _name_key(old_name) in _name_key(adopted):
        return []
    bare = _name_bare(old_name).replace("’", "'")
    tail = bare.split(" — ", 1)[1].strip() if " — " in bare else ""
    if tail and _name_key(tail) in _name_key(adopted):
        tail = ""                          # the adopted name still reads for it
    tail_re = re.compile(rf"(?<!\w){re.escape(tail)}(?!\w)") if tail else None
    if len(bare) < 6 and not tail_re:      # too short to match on without false hits
        return []
    try:
        import deck as dk
        decks = dk.discover_decks()
    except Exception:
        return []
    try:
        cards = {f.strip().replace("’", "'") for v in dk.load_card_data().values()
                 for f in (v.get("name") or "").split(" // ")}
    except Exception:
        cards = set()
    containing = sorted(c for c in cards if bare in c)
    name_re = re.compile(rf"(?<!\w){re.escape(bare)}(?!\w)")
    hits = []
    for d in decks:
        if d["id"] == own_id:
            continue
        try:
            text = _citation_prose(d["path"])
        except OSError:
            continue
        masked = [m.span() for c in containing
                  for m in re.finditer(rf"(?<!\w){re.escape(c)}(?!\w)", text)]
        cited = len(bare) >= 6 and any(
            _cited_by_id(text, *m.span(), own_id)
            or not any(a <= m.start() and m.end() <= b for a, b in masked)
            for m in name_re.finditer(text))
        if not cited and tail_re:
            cited = any(_cited_by_id(text, *m.span(), own_id)
                        for m in tail_re.finditer(text))
        if cited:
            hits.append(d["id"])
    return hits


def sync_deck_names(text, apply=False, out=print):
    """Adopt Arena's deck names into the repo. Returns (written, plan).

    ALWAYS REPORTS, writes only under `--sync-names --apply`. An `#: arena:` header is
    bookkeeping the tooling owns; a deck's NAME is human-authored prose that other files
    cite — 50 of the 106 decks are named inside another deck's header prose — so a rename
    is offered rather than performed. Reporting unconditionally is the other half: a
    capability behind a flag nobody runs is invisible (G-53), so the run says a rename is
    available even when it will not make one.

    **`--sync-names` selects the operation; `--apply` writes it** — the same split every
    other writer here uses, and it did not hold until 2026-08-26. `main()` passed
    `apply=args.sync_names` on the paste path and a hardcoded `apply=True` on the
    sourceless one, so the flag that reads like "show me the renames" performed them, and
    the sourceless reconcile could not be previewed AT ALL. It adopted ten names
    unannounced in one session. The parameter was always here and correct; no caller
    asked — the G-40 shape, one layer up from the primitive."""
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
        # Names the FULL invocation on purpose: this line prints both when no flag was
        # given at all (an ordinary ingest, offering the capability per G-53) and when
        # `--sync-names` was given without `--apply` (the preview). One phrasing is
        # correct in both, where "pass --apply" would be a puzzle in the first case.
        out("   (reported only — pass --sync-names --apply to adopt Arena's names. "
            "Nothing rewrites\n    the prose in other deck files, so a ⚠ above is a "
            "citation you fix by hand.)")
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
    notes = []
    plan = _arena_header_plan(names, parse_deck_times(text), notes)
    matched = {p[0] for p in plan}
    out(f"{len(names)} Arena deck(s) in the paste; {len(matched)} resolved to a repo "
        f"deck.\n")
    for did, _path, line, status in plan:
        mark = {"add": "+", "update": "~", "unchanged": "=", "conflict": "!",
                "older": "<"}[status]
        out(f"  {mark} deck {did:<5} {line if status != 'conflict' else line}")
        if status == "older":
            out(f"      ^ an OLDER Arena copy than the one the header names (it played "
                f"later) — header kept, nothing written")
        if status == "conflict":
            out(f"      ^ two Arena decks claim deck {did} — resolve by hand, nothing "
                f"written")
        for note_did, note in notes:
            if note_did == did:
                out(f"      ^ {note}")
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
    notes = []
    plan = _arena_header_plan(parse_deck_names(text), parse_deck_times(text), notes)
    for did, _path, names, _status in plan:
        if _status == "conflict":
            out(f"⚠ deck {did}: two Arena decks claim it ({names}) — no header written; "
                f"resolve by hand")
    todo = [p for p in plan if p[3] in ("add", "update")]
    # A superseded copy is news only on the run that moves the header to the newest one;
    # once the header holds it, repeating the note every ingest is the noise this removed.
    for did, note in notes:
        if did in {p[0] for p in todo}:
            out(f"ⓘ {note}")
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
        if deck_ids is not None:
            _canon = {_norm_id(x): x for x in deck_ids}
            if _norm_id(deck) not in _canon:
                warnings.append(f"line {lineno}: no deck {deck!r} in decks/ — skipped. An "
                                f"unknown id would appear in --report as a deck that does "
                                f"not exist.")
                continue
            # WRITE the canonical id, not the spelling typed (BS11-33): it was validated
            # normalised and stored as typed, so `06` and `6` became two record rows and
            # every by-deck count (`load_match_counts`, `swap_outcomes`) missed the first.
            deck = _canon[_norm_id(deck)]
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
            mid = f"{MANUAL_ID_PREFIX}{stamp}-{n:02d}"
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
            # A hand row has no play-by-play; these stay blank, never guessed.
            **{c: "" for c in LOG_DETAIL_COLUMNS},
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


MANUAL_ID_PREFIX = "manual-"


def is_manual_id(match_id):
    """True for a hand-entered row's id (`manual-YYYYMMDD-NN`, stamped by
    `parse_manual`). The ONE definition, read by the watermark and by `--watermark`'s
    "recorded from logs" count — a second prefix literal is how the two would drift."""
    return (match_id or "").startswith(MANUAL_ID_PREFIX)


def ingest_watermark(path=MATCHES_CSV):
    """(newest_ingested_date, n_known_ids) for matches ALREADY recorded from a log.

    The transport problem this answers: `Player.log` and the rolling `arena.log` archive
    are never consumed — deliberately, because they are the full-fidelity record that
    makes re-ingest and `--annotate` possible (G-57's dedup is what makes re-pasting
    safe). So every extraction re-emits the entire history. Measured: a 280-line paste
    whose large majority was matches from 08/07-08/23, all long since recorded, and a
    6-match paste of which 2 were already in the CSV. Nothing was wrong with the DATA —
    the parser deduped correctly both times — the cost is purely that the lines are
    carried, read and discarded.

    DERIVED FROM matches.csv, never from a second stamp file. The CSV already stores the
    Date and the Match ID; a sidecar recording the same fact is a second source of truth
    for it, and this repo's recurring failure is two places that can disagree. There is
    nothing to keep in sync because there is nothing else.

    ONLY rows carrying a LOG Match ID count. A hand-entered row (`--add`, for a phone
    game the desktop log never saw) carries a user-supplied date, so letting one set the
    watermark could advance it PAST log matches that were never ingested — and those
    would then be filtered out of every future paste, silently. The filter must only
    ever be as confident as the log-derived rows make it.

    A hand row is NOT id-less: `parse_manual` stamps every one `manual-YYYYMMDD-NN` so
    `--annotate` and dedup have something to key on. This guard used to test for a
    BLANK id — a shape the writer never produces — so a phone game logged today advanced
    the watermark to today and `--since-last` dropped every older un-ingested desktop
    line as "already recorded" (broad-scan BS8-03; the test fixture had the blank id
    too, which is why it passed). Hand rows are recognised by their prefix."""
    dates, ids = [], set()
    for r in load_matches(path):
        mid = (r.get("Match ID") or "").strip()
        if not mid or is_manual_id(mid):
            continue                      # hand row — see the docstring
        ids.add(mid)
        d = (r.get("Date") or "").strip()
        if _ISO_DATE_RE.fullmatch(d):
            dates.append(d)
    return (max(dates) if dates else "", len(ids))


_ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def filter_since(text, cutoff):
    """(kept_text, n_lines_dropped) — log lines from `cutoff` (YYYY-MM-DD) onward.

    INCLUSIVE of the cutoff DAY, and that is the whole safety margin. A day routinely
    holds both ingested and un-ingested matches (this session's own paste did), so
    filtering to `> cutoff` would drop a real match whose neighbours happened to be
    recorded first. Keeping the boundary day costs a handful of lines and hands the
    overlap to the matchId dedup, which is exactly what dedup is for.

    ORDER IS PRESERVED and never sorted. `resolve_matches` walks the log in order and
    pairs each result with the most recent `Match to <userId>` header — the only place
    the local seat appears — so re-ordering would silently mis-attribute every W/L. This
    filters lines out; it never moves one.

    Each line is dated by the best evidence it carries, in this order:
      * an EventSetDeckV3 line by its own `LastPlayed` (it PRECEDES the matches it
        explains, so inheriting a neighbour's date would misfile it by a whole session);
      * a UnityCrossThreadLogger line by its own local timestamp;
      * anything else — notably the bare `{...finalMatchResult...}` JSON blob, which
        carries no date prefix — INHERITS the last dated line above it, which is the
        header it belongs to.

    An UNDATABLE line before any date is known is KEPT. Dropping what cannot be dated
    would be guessing in the destructive direction, and this whole feature is a
    convenience over a record that is already correct."""
    kept, dropped, current = [], 0, ""
    for line in (text or "").splitlines():
        stamp = ""
        if _SETDECK_MARKER in line:
            sel = parse_deck_selection(line)
            if sel and sel[2] is not None:
                stamp = sel[2].strftime("%Y-%m-%d")
        if not stamp:
            stamp = _local_date(line)
        if stamp:
            current = stamp
        if current and current < cutoff:
            dropped += 1
            continue
        kept.append(line)
    return ("\n".join(kept) + ("\n" if kept else ""), dropped)


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
        unknown = set(kv) - {"opp", "why", "play", "note", "void"}
        if unknown:
            warnings.append(f"line {lineno}: unknown key(s) {sorted(unknown)} — skipped. "
                            f"Annotation takes opp, why, play, note, void; the deck, result "
                            f"and date come from the log and are not editable here.")
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
        if "void" in kv:
            # Not an edit of the result: the match stays recorded and stops COUNTING.
            # The reason is required so a voided row always says why it is out.
            v = kv["void"].strip()
            if not v:
                warnings.append(f"line {lineno}: void= needs a reason (void=afk), or "
                                f"void=no to restore — dropped")
            else:
                fields["_void"] = v
        if fields:
            out.append((mid, fields))
    return out, warnings


_VOID_NOTE_RE = re.compile(r"^void(?: \(was ([WLD])\))?: ")


def _void_fields(row, why):
    """The column changes `void=<why>` (or `void=no`) makes to one row, or None when the
    change must be REFUSED.

    Voiding sets Result to VOID and records the reason AND the result it replaced at the
    front of Note (`void (was W): afk`); restoring puts that result back and takes the
    reason out. Restoring used to re-derive W/L/D from Games Won/Lost (BS11-32), which are
    BLANK on every hand-entered row and 0-0 on 44 log rows — so W → void → restore came back
    a D, and `void=no` on a row that was never voided rewrote its W to D. Now: a row that
    is not VOID is refused, and a legacy `void: …` note (no recorded result) restores from
    the game score only when that score can decide — 0-0 is refused, never guessed."""
    note = (row.get("Note") or "").strip()
    m = _VOID_NOTE_RE.match(note)
    was = m.group(1) if m else None
    if m:                                         # an earlier void reason is replaced
        note = note.split(" · ", 1)[1] if " · " in note else ""
    if why.lower() in _UNVOID:
        if (row.get("Result") or "").strip().upper() != VOID:
            return None
        if not was:
            try:
                won, lost = int(row.get("Games Won") or 0), int(row.get("Games Lost") or 0)
            except ValueError:
                won = lost = 0
            if won == lost:
                return None
            was = "W" if won > lost else "L"
        return {"Result": was, "Note": note}
    cur = (row.get("Result") or "").strip().upper()
    prior = was if cur == VOID else cur           # re-voiding keeps the ORIGINAL result
    tag = f"void (was {prior})" if prior in ("W", "L", "D") else "void"
    return {"Result": VOID, "Note": f"{tag}: {why}" + (f" · {note}" if note else "")}


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
        fields = dict(fields)
        if "_void" in fields:
            _why = fields.pop("_void")
            _vf = _void_fields(row, _why)
            if _vf is None:
                eprint(f"WARN:  {mid[:8]}: void={_why} refused — the row is "
                       + ("not voided" if (row.get("Result") or "").upper() != VOID
                          else "voided with no recorded result and a tied game score")
                       + "; the rest applied.")
                if not fields:
                    continue
            else:
                fields.update(_vf)
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
    (`On Play` is also filled from the play-by-play since 2026-09-27; a hand value wins.)

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
        # A reason counts only on a LOSS that still counts (BS11-36): a voided loss kept
        # its why= and still swelled the tally the report says is "your losses".
        if v and (r.get("Result") or "").strip().upper() == "L":
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


def _print_log_axes(rows):
    """Two reads the play-by-play makes possible: record by the opponent's COLOURS and
    by whether you mulliganed. Same floor as every other table here — these are the
    newest columns, so they are the thinnest. Printed only once something is recorded.

    Colours are those of the opponent's NONLAND cards Arena showed, so a match conceded
    before they cast anything is blank and not counted, rather than read as colourless."""
    def _table(title, keyfn, order=None):
        by = {}
        for r in rows:
            k = keyfn(r)
            res = (r.get("Result") or "").strip().upper()
            if not k or res not in ("W", "L", "D"):
                continue
            by.setdefault(k, {"W": 0, "L": 0, "D": 0})[res] += 1
        if not by:
            return
        print(f"\n  {title:32}  {'W':>3} {'L':>3} {'D':>3}   Read")
        print("  " + "-" * 68)
        keys = order or sorted(by, key=lambda k: (-(by[k]["W"] + by[k]["L"] + by[k]["D"]), k))
        for k in keys:
            b = by.get(k)
            if not b:
                continue
            n = b["W"] + b["L"]
            read = (f"n={n} — too few to read (need ~{_MIN_SAMPLE})" if n < _MIN_SAMPLE
                    else f"{100*b['W']/n:.0f}%  (95% CI %.0f–%.0f%%)" % _wilson(b["W"], n))
            print(f"  {k[:32]:32}  {b['W']:>3} {b['L']:>3} {b['D']:>3}   {read}")

    _table("Opponent colours (from the log)", lambda r: (r.get("Opponent Colors") or "").strip())

    def _mull(r):
        v = (r.get("My Mulligans") or "").strip()
        if not v:
            return ""
        return "kept 7" if all(x.strip() == "0" for x in v.split("/")) else "mulliganed"
    _table("Your mulligans (from the log)", _mull, order=["kept 7", "mulliganed"])


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
    unreadable, voided = [], []
    for r in rows:
        # An unattributed row buckets by its ARENA DECK NAME, never by the avatar: the
        # avatar is a cosmetic shared across decks and changed at whim, so keying on it
        # merges unrelated decks into one row and splits one deck across several — the
        # same misreading that put an `Avatar_Basic_*` value in a column called "Course
        # ID" in the first place. With no Arena deck the honest bucket is "unknown".
        key = r.get("Deck") or f"(unattributed: {r.get('Arena Deck') or 'deck unknown'})"
        res = (r.get("Result") or "").strip().upper()
        if res == VOID:
            # Before the bucket is created (BS11-36): a deck whose only match was voided
            # printed a 0-0-0 row, i.e. a deck "played" in a table that counts matches.
            voided.append((key, r.get("Date") or "?", r.get("Note") or ""))
            continue
        b = by.setdefault(key, {"W": 0, "L": 0, "D": 0})
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
    _print_log_axes(rows)
    if voided:
        print(f"\n{len(voided)} voided match(es) — recorded so a re-paste cannot re-add "
              f"them, counted nowhere above (`--annotate <id> void=no` restores one):")
        for key, date, note in voided[:10]:
            print(f"    {date}  {key[:32]:32} {note}")
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


def _print_game_details(changes, orphans, notes, lookup_err, n_facts, out=print):
    """Show what the play-by-play is about to write, per match (G-52: a surface that
    fills data prints the data it filled)."""
    out(f"\nGame details from the play-by-play — {n_facts} game line(s), "
        f"{len(changes)} match(es) to fill:")
    for mid, row, moved in sorted(changes, key=lambda c: (c[1].get("Date") or "", c[0])):
        val = {c: new for c, (_old, new) in moved.items()}
        cur = lambda c: val.get(c, row.get(c) or "")          # noqa: E731
        bits = []
        if cur("On Play"):
            bits.append(f"on the {cur('On Play')}")
        bits.append(f"mulligans {cur('My Mulligans') or '?'} vs {cur('Opp Mulligans') or '?'}")
        bits.append(f"turn {cur('Turns') or '?'}")
        bits.append(f"opponent {cur('Opponent Colors') or '(no coloured card seen)'}")
        out(f"   {row.get('Date') or '?'}  {row.get('Result') or '?'}  "
            f"deck {row.get('Deck') or '?':<4} {mid[:8]}   " + " · ".join(bits))
        cards = [c for c in (cur("Opponent Cards") or "").split("; ") if c]
        if cards:
            more = f"  … (+{len(cards) - 8})" if len(cards) > 8 else ""
            out(f"        {'; '.join(cards[:8])}{more}")
    if orphans:
        out(f"   {orphans} match(es) have game lines but no result in this paste or in "
            f"matches.csv — their details wait for the result line.")
    for n in notes:
        out(f"   ⚠ {n}")
    if lookup_err:
        out(f"   ⚠ Scryfall unavailable ({lookup_err}) — unnamed cards are written as "
            f"#<Arena id> and named by the next run that sees these game lines.")
    out("   Turn is Arena's count of BOTH players' turns (14 = each player's 7th). "
        "Mulligans are yours vs theirs.")


def main():
    ap = argparse.ArgumentParser(
        description="Parse Arena match results from Player.log into matches.csv.")
    ap.add_argument("source", nargs="?", help="log file, or '-' for stdin")
    ap.add_argument("--apply", action="store_true",
                    help="WRITE (default: dry run) — matches.csv, plus any `#: arena:` "
                         "header or `--sync-names` rename the same run produces")
    ap.add_argument("--deck", help="tag every match in this paste with a repo deck id")
    ap.add_argument("--me", help="your Arena userId, if the paste lacks the `Match to` headers")
    ap.add_argument("--report", action="store_true", help="win/loss per deck from matches.csv")
    ap.add_argument("--map-decks", action="store_true",
                    help="learn `#: arena:` headers for the whole roster from the log's "
                         "deck summaries, instead of parsing matches")
    ap.add_argument("--sync-names", action="store_true",
                    help="reconcile the repo's `#: name:` headers against Arena's deck "
                         "names (GUID-matched decks only). DRY RUN unless --apply is "
                         "also given; the plan is reported even without this flag")
    ap.add_argument("--add", action="store_true",
                    help="record HAND-ENTERED matches (phone games, or anything the log "
                         "cannot see) from `<deck> <W|L|D> [opp= why= play= note=]` "
                         "lines given as the source file or on stdin")
    ap.add_argument("--annotate", action="store_true",
                    help="fill opp/why/play/note on matches the LOG already recorded, "
                         "from `<matchId> key=value` lines — updates rows in place "
                         "rather than appending, so it cannot double-count")
    ap.add_argument("--since", metavar="YYYY-MM-DD",
                    help="ignore log lines dated before this (INCLUSIVE of the day). "
                         "The extraction never consumes Player.log, so every paste "
                         "re-carries the whole history; this trims what is transported "
                         "without touching what is recorded")
    ap.add_argument("--since-last", action="store_true",
                    help="like --since, using the newest date already ingested from a "
                         "log (see --watermark). Safe by construction: dedup is on "
                         "Arena's matchId, so an overlap costs nothing")
    ap.add_argument("--watermark", action="store_true",
                    help="print the newest ingested date and exit — the value a local "
                         "extraction script can pass back as --since")
    ap.add_argument("--out", default=MATCHES_CSV)
    args = ap.parse_args()
    # An unknown --deck tags the WHOLE paste to a deck that does not exist, and would then
    # appear in --report as a deck nobody can open. `--add` / `--annotate` refuse an unknown
    # id for exactly that reason (G-74); the log path that tags every row did not (BS8-23).
    if getattr(args, "deck", None):
        _known = deck_ids()
        _canon = {_norm_id(x): x for x in _known}
        if _known and _norm_id(args.deck) in _canon:
            args.deck = _canon[_norm_id(args.deck)]   # canonical id written (BS11-33)
        if _known and _norm_id(args.deck) not in _canon:
            eprint(f"--deck {args.deck!r}: no deck with that id in decks/. "
                   f"An unknown id would appear in --report as a deck that does not exist.")
            return 1

    # Answer --watermark before anything else: it needs no source and is meant to be
    # captured by a shell script (`d=$(parse_matches.py --watermark)`), so it prints the
    # bare date on stdout and everything explanatory on stderr.
    if args.watermark:
        mark, n = ingest_watermark(args.out)
        if not mark:
            eprint("No log-derived matches recorded yet — nothing to filter against.")
            return 1
        eprint(f"{n} match(es) recorded from logs; newest is {mark}. "
               f"Pass --since {mark} (inclusive) to skip what is already in.")
        print(mark)
        return 0

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
        rows = load_matches(args.out)
        return deck_history(rows, args.deck) if args.deck else report(rows)
    if args.sync_names and not args.source:
        # Sourceless reconcile. The repo ALREADY holds Arena's name for every deck with
        # an `#: arena:` header — harvested from real pastes by previous runs — so the
        # names are on hand and no fresh log is needed. Not circular: the header is
        # Arena's answer, recorded; this only asks whether `#: name:` still agrees with
        # it. Without this the feature needs a paste covering all 106 decks to reconcile
        # a divergence that accumulated over months, which is a capability nobody
        # reaches (G-53).
        # DRY RUN unless --apply. This read `apply=True` until 2026-08-26, so the one
        # invocation whose entire purpose is the rename could not be previewed, and the
        # command that reads like a report rewrote ten `#: name:` headers in one run.
        written, plan = sync_deck_names_from_headers(apply=args.apply)
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

    # Trim the paste to what is not already recorded. Applied HERE — after the read and
    # before every consumer — so the whole log path (matches, `#: arena:` header harvest,
    # --sync-names, --map-decks) sees one consistently filtered text rather than each
    # deciding for itself.
    cutoff = args.since
    if args.since_last and not cutoff:
        cutoff, _n = ingest_watermark(args.out)
        if not cutoff:
            eprint("--since-last: nothing ingested from a log yet, so there is no "
                   "watermark to filter against — parsing the whole paste.")
    if cutoff:
        if not _ISO_DATE_RE.fullmatch(cutoff):
            ap.error(f"--since expects YYYY-MM-DD, got {cutoff!r}")
        text, dropped = filter_since(text, cutoff)
        if dropped:
            eprint(f"Filtered out {dropped} log line(s) dated before {cutoff} "
                   f"(inclusive of that day). Nothing was deleted — the log still holds "
                   f"them, and re-running without --since re-reads everything.")

    def _with_report(rc):
        """Run `--report` after the ingest when both were asked for (BS5-09), on every
        SUCCESS path — including the summaries-only one, which is a legitimate outcome
        and returned before the report on the first pass at this fix. Error paths are
        deliberately excluded: a report after a failed read would read as reassurance.
        Reads matches.csv back rather than reporting `existing + fresh` in memory, so a
        dry run honestly describes the record as it STANDS, not as it would stand."""
        if args.report:
            print()
            rows = load_matches(args.out)
            deck_history(rows, args.deck) if args.deck else report(rows)
        return rc

    if args.map_decks:
        map_decks(text, apply=args.apply)
        # The roster-scale header pass is exactly where a roster-scale RENAME shows up,
        # so it offers the same adoption the match path does.
        sync_deck_names(text, apply=(args.sync_names and args.apply))
        return _with_report(0)

    rows, warnings = parse_log(text, me=args.me)
    facts, fact_warnings = parse_game_facts(text)
    for w in warnings + fact_warnings:
        eprint(f"WARN:  {w}")

    # Header upkeep rides along with every ingest — BEFORE the mapping is built, so a
    # header written from this paste resolves this paste's own matches, and BEFORE the
    # no-matches bailout, so a paste of deck summaries alone (the --map-decks extraction
    # shape) still keeps headers current instead of dying with a misleading error.
    sync_headers(text, apply=args.apply)
    # AFTER the header sync, which is what establishes the GUID pairing this reads. A
    # deck first seen in this paste therefore becomes eligible in the SAME run — but only
    # via the header the sync just wrote, never via the number-prefix guess that found it.
    #
    # BOTH flags, deliberately. `--sync-names` selects the operation and `--apply` writes
    # it, matching `sync_headers`/`map_decks`/`add_manual` on the lines around this one;
    # it used to read `apply=args.sync_names`, which made this the only writer in the file
    # that ignored --apply. The conjunction also means a routine `session.log --apply`
    # ingest never renames a deck as a side effect — the rename must be asked for.
    sync_deck_names(text, apply=(args.sync_names and args.apply))

    if not rows and not facts:
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
            r["Deck"] = args.deck          # validated in main() before any parsing
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
    # The play-by-play joins on the match id, so it fills this paste's new rows AND rows
    # recorded by an earlier run — which is how matches logged before the extractor
    # existed get their details, from whatever game lines the logs still hold.
    detail_changes, names, names_new = [], {}, {}
    cards_csv = os.path.join(os.path.dirname(os.path.abspath(args.out)),
                             os.path.basename(ARENA_CARDS_CSV))
    if facts:
        by_id = {mid: r for r in existing + fresh
                 if (mid := (r.get("Match ID") or "").strip())}
        wanted = set()
        for mid, games in facts.items():
            if mid in by_id:
                wanted |= opponent_card_ids(games)
        names, names_new, lookup_err = resolve_arena_names(wanted, load_arena_cards(cards_csv))
        detail_changes, orphans, notes = apply_game_details(by_id, facts, names)
        _print_game_details(detail_changes, orphans, notes, lookup_err,
                            n_facts=sum(len(g) for g in facts.values()))
    _print_missing_details(fresh, facts)

    if not args.apply:
        print("\n(dry run — pass --apply to write matches.csv)")
        return _with_report(0)
    if not fresh and not detail_changes:
        print("\nNothing new to write.")
        return _with_report(0)
    write_matches(existing + fresh, args.out)
    if names_new:
        write_arena_cards(names, cards_csv)
    fresh_ids = {id(r) for r in fresh}
    filled = sum(1 for _m, r, _c in detail_changes if id(r) not in fresh_ids)
    print(f"\nWrote {args.out} ({len(existing) + len(fresh)} total"
          + (f"; game details filled on {filled} match(es) already recorded" if filled else "")
          + "). See the record with: parse_matches.py --report")
    # Printed AFTER the write, because --annotate refuses an id matches.csv does not hold.
    _print_loss_prompt([r for r in fresh if (r.get("Result") or "").upper() == "L"],
                       facts, names)
    return _with_report(0)


if __name__ == "__main__":
    sys.exit(main())
