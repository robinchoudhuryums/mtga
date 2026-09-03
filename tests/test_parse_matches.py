"""Unit tests for the Arena match-log parser.

Pinned against a REAL log sample rather than a shape invented to match the regex — the
lesson from this project's dead-pattern bugs, where every pattern passed a test written by
its own author and only real card text disproved it. The fixture below is the structure
Arena actually emitted for one completed match, with the identifying fields replaced.

The load-bearing fact these tests exist to protect: the JSON carries the result and both
seats but NOT which seat is yours. That is only in the `Match to <userId>:` header prefix.
If the parser ever "recovers" from a missing header by guessing, every result becomes a
coin flip and the record silently becomes noise — so the skip-and-warn path is tested as
carefully as the happy one."""
import json

import parse_matches as pm

ME = "AAAABBBBCCCCDDDDEEEEFFFFGG"
OPP = "ZZZZYYYYXXXXWWWWVVVVUUUUTT"


def _event(match_id="m-1", my_team=2, winner=1, games=((1,),), timestamp="1785197326489",
           my_course="Avatar_Basic_BlackPanther_MSH", opp_course="Avatar_Basic_Slimefoot_DMU",
           reason="MatchCompletedReasonType_Success", ended_by="ResultReason_Game"):
    """One finalMatchResult line, in Arena's real nesting.

    `reason` and `ended_by` are DIFFERENT fields and the distinction is the point:
    `reason` is `matchCompletedReason` (Success for every completed match, hence the
    column that carried no information), `ended_by` is the match-scope result's own
    reason (Game vs Concede, the half that varies)."""
    results = [{"scope": "MatchScope_Game", "result": "ResultType_WinLoss",
                "winningTeamId": g[0], "reason": ended_by} for g in games]
    results.append({"scope": "MatchScope_Match", "result": "ResultType_WinLoss",
                    "winningTeamId": winner, "reason": ended_by})
    payload = {
        "transactionId": "t-1", "requestId": 332, "timestamp": timestamp,
        "matchGameRoomStateChangedEvent": {"gameRoomInfo": {
            "gameRoomConfig": {
                "reservedPlayers": [
                    {"userId": OPP, "playerName": "SomeOpponent", "systemSeatId": 1,
                     "teamId": 3 - my_team, "courseId": opp_course,
                     "platformId": "AndroidPhone", "eventId": "Play"},
                    {"userId": ME, "playerName": "SomePlayer", "systemSeatId": 2,
                     "teamId": my_team, "courseId": my_course,
                     "platformId": "SteamMac", "eventId": "Play"},
                ],
                "matchId": match_id,
            },
            "stateType": "MatchGameRoomStateType_MatchCompleted",
            "finalMatchResult": {
                "matchId": match_id, "matchCompletedReason": reason,
                "resultList": results,
            },
        }},
    }
    return json.dumps(payload)


def _header(date="7/27/2026", time="7:08:46 PM", user=ME):
    return (f"[UnityCrossThreadLogger]{date} {time}: Match to {user}: "
            f"MatchGameRoomStateChangedEvent")


def _setdeck(name="07 Earth’s Mightiest", guid="e3a6c595-914d-4809-bd6d-630b3758ca89",
             when="2026-08-07T07:33:23.850462-05:00", event="Play", cut=600):
    """One EventSetDeckV3 line in Arena's real nesting — JSON inside a JSON string, with
    the timestamp attributes double-encoded on top of that.

    Built by SERIALIZING the structure rather than by typing the escaped text, so the
    escaping is Arena's rather than the test author's, and truncated at 600 chars because
    that is what the documented `cut -c1-600` extraction produces — neither `json.loads`
    survives it, which is exactly the case the regex path exists for."""
    inner = {
        "EventName": event,
        "Summary": {
            "DeckId": guid, "Mana": "", "Name": name,
            "Attributes": [
                {"name": "Version", "value": "11"},
                {"name": "TileID", "value": "104895"},
                {"name": "LastPlayed", "value": json.dumps(when)},
                {"name": "LastUpdated",
                 "value": json.dumps("2026-07-21T08:41:23.805305-05:00")},
                {"name": "IsFavorite", "value": "false"},
                {"name": "Format", "value": "Standard"},
            ],
            "Description": None,
        },
    }
    def _j(obj):
        # Arena emits compact, non-ASCII-escaped JSON: no spaces after `:` or `,`, and a
        # curly apostrophe stays a curly apostrophe. Both matter — the extraction regexes
        # read the raw line, so a prettified fixture would be testing a shape the client
        # never writes.
        return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)

    line = ("[UnityCrossThreadLogger]==> EventSetDeckV3 "
            + _j({"id": "634cfd01-d7f2-4012-8355-411362deb142", "request": _j(inner)}))
    return line[:cut] if cut else line


def _log(*events, header=True):
    lines = []
    for e in events:
        if header:
            lines.append(_header())
        lines.append(e)
    return "\n".join(lines)


class TestTheRealSample:
    """The exact shape the user's log produced: seat 2, match won by team 1 -> LOSS."""

    def test_a_loss_is_derived_from_the_seat_not_guessed(self):
        rows, warns = pm.parse_log(_log(_event(my_team=2, winner=1)))
        assert warns == []
        assert len(rows) == 1
        assert rows[0]["Result"] == "L"

    def test_the_mirror_case_is_a_win(self):
        """Proves the derivation reads the seat rather than hardcoding an outcome."""
        rows, _ = pm.parse_log(_log(_event(my_team=1, winner=1)))
        assert rows[0]["Result"] == "W"

    def test_it_records_both_avatars_and_the_reason(self):
        rows, _ = pm.parse_log(_log(_event()))
        r = rows[0]
        # `courseId` is the AVATAR cosmetic, not a deck — the columns say so.
        assert r["My Avatar"] == "Avatar_Basic_BlackPanther_MSH"
        assert r["Opponent Avatar"] == "Avatar_Basic_Slimefoot_DMU"
        assert r["Reason"] == "Success"        # the enum prefix is stripped
        assert r["Event"] == "Play"

    def test_ended_by_separates_a_concede_from_a_played_out_game(self):
        """The half of the reason data that VARIES. `matchCompletedReason` is Success for
        every completed match — all 15 rows of the first real record read `Success`, i.e.
        the stored column carried zero bits, while this one distinguished 2 of 3."""
        played, _ = pm.parse_log(_log(_event(match_id="m-a")))
        scooped, _ = pm.parse_log(_log(_event(match_id="m-b",
                                              ended_by="ResultReason_Concede")))
        assert played[0]["Ended By"] == "Game"
        assert scooped[0]["Ended By"] == "Concede"
        # Both still complete normally, so the OLD column cannot tell them apart.
        assert played[0]["Reason"] == scooped[0]["Reason"] == "Success"

    def test_a_missing_result_reason_is_blank_not_guessed(self):
        raw = json.loads(_event())
        fin = (raw["matchGameRoomStateChangedEvent"]["gameRoomInfo"]["finalMatchResult"])
        for r in fin["resultList"]:
            r.pop("reason", None)
        rows, _ = pm.parse_log(_log(json.dumps(raw)))
        assert rows[0]["Ended By"] == ""

    def test_the_result_evidence_is_carried_but_never_written(self):
        """G-52 — the dry run prints the two integers the W/L verdict came from. They ride
        on the row as underscore keys; `write_matches` emits only HEADER, so they must not
        reach the CSV (and must not appear as columns)."""
        rows, _ = pm.parse_log(_log(_event(my_team=2, winner=1)))
        assert (rows[0]["_my_team"], rows[0]["_win_team"]) == (2, 1)
        assert "my team 2" in pm._result_evidence(rows[0])
        assert "winner 1" in pm._result_evidence(rows[0])
        assert not [k for k in pm.HEADER if k.startswith("_")]

    def test_the_evidence_names_a_draw_rather_than_printing_team_zero(self):
        rows, _ = pm.parse_log(_log(_event(winner=0)))
        assert rows[0]["Result"] == "D"
        assert "winner none" in pm._result_evidence(rows[0])

    def test_evidence_is_empty_for_a_row_that_came_back_from_csv(self):
        """`report` runs over rows loaded from disk, which never carry the fields."""
        assert pm._result_evidence({"Date": "2026-08-14", "Result": "W"}) == ""

    def test_a_seat_with_no_team_prints_a_question_mark_not_nothing(self):
        """The distinction the presence check buys. A parsed row whose seat carries no
        `teamId` still derives a W/L — and that is the LEAST trustworthy verdict there is,
        so it must not fall into the same silent-empty branch as a CSV row."""
        assert pm._result_evidence({"_my_team": None, "_win_team": 1}) == \
            "[my team ? · winner 1]"

    def test_game_scores_are_counted_per_team(self):
        rows, _ = pm.parse_log(_log(_event(my_team=2, winner=2, games=((2,), (1,), (2,)))))
        assert (rows[0]["Games Won"], rows[0]["Games Lost"]) == (2, 1)


class TestDeckSelection:
    """`courseId` on a seat is the AVATAR cosmetic, not a deck — nine matches were
    recorded against it before anyone read the values. The deck actually played is in
    EventSetDeckV3, which Arena writes seconds before the match starts."""

    def test_it_reads_name_guid_and_time_from_a_truncated_line(self):
        name, guid, when = pm.parse_deck_selection(_setdeck())
        assert name == "07 Earth’s Mightiest"
        assert guid == "e3a6c595-914d-4809-bd6d-630b3758ca89"
        assert (when.year, when.month, when.day, when.hour) == (2026, 8, 7, 7)

    def test_the_double_encoded_timestamp_survives_the_offset(self):
        """`LastPlayed` is a JSON string inside a JSON string inside a JSON string, and
        carries a -05:00 offset the match headers do not. Both end up on one clock."""
        _, _, when = pm.parse_deck_selection(
            _setdeck(when="2026-08-09T18:15:50.315752-05:00"))
        assert when == __import__("datetime").datetime(2026, 8, 9, 18, 15, 50, 315752)

    def test_the_neighbouring_lastupdated_is_not_mistaken_for_it(self):
        _, _, when = pm.parse_deck_selection(_setdeck())
        assert when.month == 8            # LastUpdated in the fixture is 2026-07-21

    def test_the_response_line_carries_the_marker_and_no_payload(self):
        assert pm.parse_deck_selection(
            "<== EventSetDeckV3(634cfd01-d7f2-4012-8355-411362deb142)") is None

    def test_an_unrelated_line_is_not_a_selection(self):
        assert pm.parse_deck_selection(_header()) is None
        assert pm.parse_deck_selection(_event()) is None
        assert pm.parse_deck_selection("") is None
        assert pm.parse_deck_selection(None) is None

    def test_the_event_name_key_is_not_read_as_the_deck_name(self):
        """`"EventName":"Play"` ends in `Name":"Play"`; only a quote-anchored `"Name":"`
        may match, or every deck would be called Play."""
        assert pm.parse_deck_selection(_setdeck(event="Ladder"))[0] == "07 Earth’s Mightiest"


class TestAttribution:
    """The join that makes the record useful: which deck was each match played with."""

    def _session(self):
        """The real 8/7 session: two matches on deck 07, then two on deck 19."""
        return "\n".join([
            _setdeck(name="07 Earth’s Mightiest", guid="g7",
                     when="2026-08-07T07:33:23.850462-05:00"),
            _header(date="8/7/2026", time="7:33:25 AM"),
            _header(date="8/7/2026", time="7:39:28 AM"), _event(match_id="m-a"),
            _setdeck(name="19 Bird Brain- Bant", guid="g19",
                     when="2026-08-07T07:46:08.103602-05:00"),
            _header(date="8/7/2026", time="7:46:15 AM"),
            _header(date="8/7/2026", time="7:46:35 AM"), _event(match_id="m-b"),
        ])

    def test_each_match_gets_the_deck_selected_before_it(self):
        rows, warns = pm.parse_log(self._session())
        assert warns == []
        assert [(r["Match ID"], r["Arena Deck"]) for r in rows] == [
            ("m-a", "07 Earth’s Mightiest"), ("m-b", "19 Bird Brain- Bant")]
        assert [r["Arena Deck ID"] for r in rows] == ["g7", "g19"]

    def test_two_separate_greps_concatenated_still_attribute_by_TIME(self):
        """The realistic mis-ordering, and the one that produced this feature: the user
        runs the match grep and the EventSetDeckV3 grep as SEPARATE commands and pastes
        both, so every selection lands in one block and every match in another. A log-ORDER
        walk then hands the single last selection to every match — one deck for the whole
        session, which reads as data. The timestamps still separate them."""
        lines = self._session().splitlines()
        sels = [ln for ln in lines if "EventSetDeckV3" in ln]
        rest = [ln for ln in lines if "EventSetDeckV3" not in ln]
        rows, _ = pm.parse_log("\n".join(sels + rest))
        assert {r["Match ID"]: r["Arena Deck"] for r in rows} == {
            "m-a": "07 Earth’s Mightiest", "m-b": "19 Bird Brain- Bant"}

    def test_a_match_before_every_selection_stays_blank(self):
        """The 7/27 row in the real record: the log holding its selection had rotated.
        Blank is the only safe answer — borrowing a LATER session's deck would invent a
        record that reads exactly like data."""
        log = "\n".join([_header(date="7/27/2026", time="7:08:46 PM"), _event(),
                         _setdeck(when="2026-08-07T07:33:23.850462-05:00")])
        rows, warns = pm.parse_log(log)
        assert rows[0]["Arena Deck"] == "" and rows[0]["Arena Deck ID"] == ""
        assert warns == []

    def test_a_selection_past_the_gap_bound_is_refused_and_reported(self):
        """A rotated log leaves an ancient selection as the nearest one. Arena re-submits
        the deck on every event join — the whole real sample sits 2–20 SECONDS before its
        match — so anything hours old is not a deck choice."""
        log = "\n".join([_setdeck(when="2026-08-01T09:00:00.000000-05:00"),
                         _header(date="8/7/2026", time="7:33:25 AM"),
                         _header(date="8/7/2026", time="7:39:28 AM"), _event()])
        rows, warns = pm.parse_log(log)
        assert rows[0]["Arena Deck"] == ""
        assert any("rotated log" in w for w in warns)

    def test_a_paste_with_no_timestamps_falls_back_to_log_order(self):
        log = "\n".join([_setdeck(when="not-a-timestamp"), _header(date="", time=""),
                         _event()])
        rows, _ = pm.parse_log(log, me=ME)
        assert rows[0]["Arena Deck"] == "07 Earth’s Mightiest"

    def test_the_avatar_is_never_used_as_the_deck(self):
        """The whole point of the rewrite. Both seats' cosmetics are recorded, and
        neither may leak into a deck field."""
        rows, _ = pm.parse_log(self._session())
        for r in rows:
            assert "Avatar_" not in r["Arena Deck"]
            assert "Avatar_" not in r["Arena Deck ID"]
            assert "Avatar_" not in r["Deck"]


class TestIdentityIsNeverStored:
    """A design promise, not an implementation detail: neither field is needed to compute
    a win rate, and a match log is not a place to accumulate identity."""

    def test_no_userid_or_playername_reaches_a_row(self):
        rows, _ = pm.parse_log(_log(_event()))
        blob = json.dumps(rows[0])
        assert ME not in blob and OPP not in blob
        assert "SomePlayer" not in blob and "SomeOpponent" not in blob

    def test_the_csv_header_has_no_identity_column(self):
        for col in pm.HEADER:
            assert "user" not in col.lower() and "player" not in col.lower()


class TestTheHeaderIsLoadBearing:
    """Without it, which seat is yours is unknowable — so the parser must SKIP, never
    guess. A 50%-accurate record is worse than an empty one: it looks like data."""

    def test_json_alone_is_skipped_with_an_actionable_warning(self):
        rows, warns = pm.parse_log(_event())
        assert rows == []
        assert len(warns) == 1
        assert "--me" in warns[0]

    def test_the_me_override_recovers_it(self):
        rows, warns = pm.parse_log(_event(), me=ME)
        assert warns == [] and len(rows) == 1

    def test_a_seat_that_matches_nobody_is_skipped(self):
        rows, warns = pm.parse_log(_event(), me="NOTAPLAYERINTHISMATCH")
        assert rows == []
        assert "no seat matches" in warns[0]


class TestDates:
    def test_the_local_header_date_wins_over_the_utc_epoch(self):
        """The sample's own discrepancy: the header said 7/27, the epoch resolves to
        7/28. An evening session must not file under the next day."""
        assert pm._utc_date("1785197326489") == "2026-07-28"
        rows, _ = pm.parse_log(_log(_event(timestamp="1785197326489")))
        assert rows[0]["Date"] == "2026-07-27"

    def test_the_epoch_is_the_fallback_when_no_header_date_exists(self):
        """Occasionally a day off still beats blank — a blank sorts to the top of
        matches.csv and can't be scoped in time."""
        rows, _ = pm.parse_log(_event(timestamp="1785197326489"), me=ME)
        assert rows[0]["Date"] == "2026-07-28"

    def test_a_junk_timestamp_yields_a_blank_not_a_crash(self):
        for bad in ("", None, "not-a-number", "0", "-5"):
            assert pm._utc_date(bad) == ""
        rows, _ = pm.parse_log(_event(timestamp="banana"), me=ME)
        assert rows[0]["Date"] == ""

    def test_single_digit_month_and_day_are_zero_padded(self):
        line = _header(date="1/2/2026")
        assert pm._local_date(line) == "2026-01-02"

    def test_a_line_with_no_timestamp_reads_blank(self):
        assert pm._local_date("Match to SOMEONE: MatchGameRoomStateChangedEvent") == ""
        assert pm._local_date(None) == ""


class TestMalformedInput:
    """A log paste is hand-extracted, so truncation is the expected failure — it must
    warn, not raise."""

    def test_truncated_json_warns_and_continues(self):
        good = _event(match_id="m-good")
        bad = _event(match_id="m-bad")[:120]
        rows, warns = pm.parse_log(_log(bad, good))
        assert [r["Match ID"] for r in rows] == ["m-good"]
        assert any("TRUNCATED" in w for w in warns)

    def test_a_cut_before_the_result_marker_is_still_reported(self):
        """The realistic cut point, and the one that used to be SILENT. `finalMatchResult`
        sits late in the line — after both seats — so a width cap removes it, and keying
        the scan on that marker meant the line matched nothing and the match vanished with
        the run still reporting success. The scan keys on the event instead."""
        bad = _event(match_id="m-bad")[:120]
        assert '"finalMatchResult"' not in bad          # the cut really does remove it
        assert '"matchGameRoomStateChangedEvent"' in bad
        rows, warns = pm.parse_log(_log(bad))
        assert rows == []
        assert len(warns) == 1 and "missing" in warns[0]

    def test_a_state_change_that_is_not_a_completed_match_is_ignored(self):
        """`finalMatchResult` appears on lines whose gameRoomInfo lacks the config."""
        line = json.dumps({"matchGameRoomStateChangedEvent": {"gameRoomInfo": {
            "finalMatchResult": {"matchId": "m-x"}}}})
        rows, warns = pm.parse_log(_log(line))
        assert rows == [] and warns == []

    def test_a_result_list_with_no_match_scope_is_reported(self):
        payload = json.loads(_event())
        fin = payload["matchGameRoomStateChangedEvent"]["gameRoomInfo"]["finalMatchResult"]
        fin["resultList"] = [r for r in fin["resultList"] if r["scope"] != "MatchScope_Match"]
        rows, warns = pm.parse_log(_log(json.dumps(payload)))
        assert rows == []
        assert "no match-scope result" in warns[0]

    def test_empty_input_is_empty_output(self):
        assert pm.parse_log("") == ([], [])
        assert pm.parse_log(None) == ([], [])

    def test_a_draw_is_neither_a_win_nor_a_loss(self):
        rows, _ = pm.parse_log(_log(_event(winner=0)))
        assert rows[0]["Result"] == "D"


class TestPersistence:
    def test_a_roundtrip_preserves_every_column(self, tmp_path):
        rows, _ = pm.parse_log(_log(_event()))
        out = str(tmp_path / "matches.csv")
        pm.write_matches(rows, out)
        back = pm.load_matches(out)
        assert len(back) == 1
        for col in pm.HEADER:
            assert str(back[0][col]) == str(rows[0].get(col, ""))

    def test_a_missing_file_reads_as_empty(self, tmp_path):
        assert pm.load_matches(str(tmp_path / "nope.csv")) == []

    def test_a_pre_attribution_csv_keeps_its_avatar_columns(self, tmp_path):
        """`write_matches` emits only HEADER, so a CSV still carrying `Course ID` would be
        rewritten with those cells BLANK — silently losing the one field the old rows had.
        Renaming on READ makes the migration happen on the next write instead."""
        out = tmp_path / "m.csv"
        out.write_text("Date,Match ID,Deck,Course ID,Event,Result,Games Won,Games Lost,"
                       "Opponent Course,Reason\n"
                       "2026-07-27,m1,,Avatar_Basic_BlackPanther_MSH,Play,L,0,1,"
                       "Avatar_Basic_Slimefoot_DMU,Success\n", encoding="utf-8")
        rows = pm.load_matches(str(out))
        assert rows[0]["My Avatar"] == "Avatar_Basic_BlackPanther_MSH"
        assert rows[0]["Opponent Avatar"] == "Avatar_Basic_Slimefoot_DMU"
        pm.write_matches(rows, str(out))
        assert pm.load_matches(str(out))[0]["My Avatar"] == "Avatar_Basic_BlackPanther_MSH"

    def test_the_previous_schema_migrates_when_a_column_is_added(self, tmp_path):
        """The regression that generalized `_is_own_earlier_schema`. It used to compare
        against the ONE header remembered from the avatar rename, which worked exactly
        once: adding `Ended By` made the then-current file an "earlier schema" too, and an
        exact match cannot see that — so the guard would refuse the very write that
        performs the upgrade, which is the bug it exists to prevent."""
        out = tmp_path / "m.csv"
        prev = [c for c in pm.HEADER if c != "Ended By"]
        out.write_text(",".join(prev) + "\n"
                       + "2026-08-14,m1,15,15 Air Nomads,g-1,Avatar_Basic_ShangChi_MSH,"
                         "Play,W,1,0,Avatar_Basic_ScarletWitch_MSH,Success\n",
                       encoding="utf-8")
        rows = pm.load_matches(str(out))
        pm.write_matches(rows, str(out))       # must not raise
        back = pm.load_matches(str(out))
        assert back[0]["Result"] == "W"
        assert back[0]["Deck"] == "15"
        assert back[0]["Ended By"] == ""       # unknown, not invented

    def test_a_reordered_header_is_refused(self, tmp_path):
        """Every column is one of mine — but not in my order, so it is not my file."""
        out = tmp_path / "m.csv"
        swapped = list(pm.HEADER)
        swapped[0], swapped[1] = swapped[1], swapped[0]
        out.write_text(",".join(swapped) + "\n", encoding="utf-8")
        assert pm._is_own_earlier_schema(str(out)) is False

    def test_a_schema_missing_the_core_columns_is_refused(self, tmp_path):
        """An ordered subset of my names is not enough: without Match ID there is no
        identity to dedup on, so it cannot be a matches.csv."""
        out = tmp_path / "m.csv"
        out.write_text("Date,Deck,Event\n", encoding="utf-8")
        assert pm._is_own_earlier_schema(str(out)) is False

    def test_a_foreign_csv_is_still_refused(self, tmp_path):
        """The migration allowance accepts only headers built from THIS module's own
        column names in their own order, so the F-02 mirror guard still stops this writer
        overwriting a file it does not own."""
        out = tmp_path / "card-library.csv"
        out.write_text("Card Name,Set Code,Collector #,Quantity Owned,Color(s),"
                       "Card Type,Card Text,Synergies\nShock,M21,159,4,R,Instant,,burn\n",
                       encoding="utf-8")
        try:
            pm.write_matches([{"Date": "2026-07-27"}], str(out))
        except ValueError as e:
            assert "DIFFERENT schema" in str(e)
        else:
            raise AssertionError("the mirror guard did not fire")

    def test_rows_are_written_in_date_order(self, tmp_path):
        rows = [{"Date": "2026-07-28", "Match ID": "b"},
                {"Date": "2026-07-01", "Match ID": "a"}]
        out = str(tmp_path / "m.csv")
        pm.write_matches(rows, out)
        assert [r["Match ID"] for r in pm.load_matches(out)] == ["a", "b"]


class TestDedup:
    """Re-pasting an overlapping log has to be safe — Player.log is overwritten on every
    launch, so the natural extraction habit produces overlapping pastes."""

    def test_the_same_match_id_appears_once_across_two_pastes(self):
        first, _ = pm.parse_log(_log(_event(match_id="m-1")))
        second, _ = pm.parse_log(_log(_event(match_id="m-1"), _event(match_id="m-2")))
        assert [r["Match ID"] for r in pm.fresh_rows(second, first)] == ["m-2"]

    def test_a_duplicate_WITHIN_one_paste_is_recorded_once(self):
        """BS4-15: concatenating two overlapping extracts puts the same match in ONE
        paste. The filter only compared against the CSV, so both copies were written and
        the match was double-counted in `--report` forever — while the docstring and the
        truncation warning both told the user re-pasting was safe."""
        rows, _ = pm.parse_log(_log(_event(match_id="m-1"), _event(match_id="m-2"),
                                    _event(match_id="m-1")))
        assert len(rows) == 3                       # the parser reports what it saw
        assert [r["Match ID"] for r in pm.fresh_rows(rows, [])] == ["m-1", "m-2"]

    def test_id_less_rows_are_never_deduped_against_each_other(self):
        """"" is not an identity. Deduping on it dropped every id-less match after the
        first as 'already recorded' — a silent loss that reads as data (batch 5)."""
        rows = [{"Match ID": "", "Result": "W"}, {"Match ID": "", "Result": "L"}]
        assert len(pm.fresh_rows(rows, [])) == 2
        assert len(pm.fresh_rows(rows, [{"Match ID": ""}])) == 2


class TestUnreadableResults:
    """BS4-24: `b[r.get("Result", "L")]` only defaulted when the KEY was absent, so a row
    with `Result=""` incremented a `b[""]` bucket printed in no column and excluded from
    n = W+L. The header count and the per-deck totals then disagreed with nothing said —
    the 'reads as data, not as a gap' failure this module is otherwise built to avoid."""

    def _rows(self):
        return [{"Deck": "5", "Result": "W", "Course ID": "c"},
                {"Deck": "5", "Result": "", "Course ID": "c"},
                {"Deck": "5", "Result": "?", "Course ID": "c"}]

    def test_the_bad_rows_are_reported_not_silently_dropped(self, capsys):
        pm.report(self._rows())
        out = capsys.readouterr().out
        assert "unreadable Result" in out
        assert "do not sum to 3" in out

    def test_good_rows_still_count(self, capsys):
        pm.report(self._rows())
        out = capsys.readouterr().out
        assert "3 match(es) recorded" in out      # the header still counts every row

    def test_a_clean_record_says_nothing_extra(self, capsys):
        pm.report([{"Deck": "5", "Result": "W", "Course ID": "c"},
                   {"Deck": "5", "Result": "L", "Course ID": "c"}])
        assert "unreadable Result" not in capsys.readouterr().out

    def test_case_and_whitespace_are_tolerated(self, capsys):
        pm.report([{"Deck": "5", "Result": " w ", "Course ID": "c"}])
        assert "unreadable Result" not in capsys.readouterr().out


class TestWilson:
    """The naive normal approximation is wrong at exactly the sample sizes this record
    will live at, which is the whole reason a CI is printed instead of a bare rate."""

    def test_the_interval_brackets_the_point_estimate(self):
        lo, hi = pm._wilson(6, 10)
        assert lo < 60 < hi

    def test_it_stays_inside_zero_and_one_hundred(self):
        for wins, n in ((0, 1), (1, 1), (0, 5), (5, 5), (13, 40)):
            lo, hi = pm._wilson(wins, n)
            assert 0 <= lo <= hi <= 100

    def test_more_games_narrow_it(self):
        lo_small, hi_small = pm._wilson(5, 10)
        lo_big, hi_big = pm._wilson(50, 100)
        assert (hi_big - lo_big) < (hi_small - lo_small)

    def test_zero_games_does_not_divide_by_zero(self):
        assert pm._wilson(0, 0) == (0.0, 0.0)


class TestReportRestraint:
    """`57%` off 7 games invites a tuning decision the data cannot support. Same restraint
    `count_conf` shows for role counts: a number that looks certain when it isn't is the
    expensive kind of wrong."""

    def test_a_small_sample_prints_no_percentage(self, capsys):
        rows = [{"Date": "2026-07-27", "Match ID": f"m{i}", "Deck": "12",
                 "Course ID": "c", "Result": "W" if i % 2 else "L"} for i in range(5)]
        pm.report(rows)
        out = capsys.readouterr().out
        assert "too few to read" in out
        assert "%" not in out.split("too few")[0].split("Read")[-1]

    def test_a_large_enough_sample_prints_a_rate_with_its_interval(self, capsys):
        rows = [{"Date": "2026-07-27", "Match ID": f"m{i}", "Deck": "12",
                 "Course ID": "c", "Result": "W" if i % 2 else "L"}
                for i in range(pm._MIN_SAMPLE + 4)]
        pm.report(rows)
        out = capsys.readouterr().out
        assert "95% CI" in out and "too few to read" not in out

    def test_unmapped_matches_are_surfaced_never_dropped(self, capsys):
        rows = [{"Date": "2026-07-27", "Match ID": "m1", "Deck": "",
                 "Arena Deck": "07 Earth's Mightiest", "Result": "L"}]
        pm.report(rows)
        out = capsys.readouterr().out
        assert "07 Earth's Mightiest" in out
        assert "#: arena:" in out          # tells you how to fix it

    def test_a_match_with_no_deck_selection_is_reported_as_a_gap(self, capsys):
        """The 7/27 row in the real record: its log had rotated, so no EventSetDeckV3
        survives. It must read as an unattributed gap with a route to fixing it."""
        rows = [{"Date": "2026-07-27", "Match ID": "m1", "Deck": "", "Arena Deck": "",
                 "My Avatar": "Avatar_Basic_BlackPanther_MSH", "Result": "L"}]
        pm.report(rows)
        out = capsys.readouterr().out
        assert "no Arena deck at all" in out
        assert "EventSetDeckV3" in out

    def test_an_empty_record_says_so(self, capsys):
        pm.report([])
        assert "No matches recorded" in capsys.readouterr().out


class TestDeckMapping:
    def test_the_map_is_learned_from_arena_headers(self, tmp_path, monkeypatch):
        import deck as dk
        d = tmp_path / "decks"
        (d / "90-test").mkdir(parents=True)
        (d / "90-test" / "deck.txt").write_text(
            "#: name: Test\n#: arena: 90 Some Arena Name, dead-beef-guid\n"
            "4 Shock (M21) 159\n")
        monkeypatch.setattr(dk, "DECKS_DIR", str(d))
        m = pm.arena_deck_map()
        # Either key resolves: the GUID survives an Arena rename, the name is typable.
        assert m.get("90 some arena name") == "90"
        assert m.get("dead-beef-guid") == "90"

    def test_it_degrades_to_empty_rather_than_raising(self, monkeypatch):
        """The parser is usable standalone; a broken deck dir must not take it down."""
        import deck as dk
        monkeypatch.setattr(dk, "discover_decks", lambda: (_ for _ in ()).throw(OSError()))
        assert pm.arena_deck_map() == {}


class TestDeckNameHarvest:
    """`--map-decks` learns a `#: arena:` header per deck from one paste. Every message
    type that mentions a deck nests the same {"DeckId":…,"Name":…} object, so ONE pattern
    reads EventSetDeckV3, DeckUpsertDeckV3 and a whole DeckGetDeckSummariesV3 response."""

    def test_it_harvests_from_an_event_set_deck_line(self):
        assert pm.parse_deck_names(_setdeck()) == {
            "e3a6c595-914d-4809-bd6d-630b3758ca89": "07 Earth’s Mightiest"}

    def test_several_summaries_on_one_line_all_come_back(self):
        """Shape-generality pin: the harvest is per-OBJECT, not per-line, so a message
        that packs several summaries into one line yields them all. (No live Arena
        message is known to do this — DeckGetDeckSummariesV3 was assumed to and measured
        to log NO payload at all — but the property is what makes the scan robust to a
        message layout nobody anticipated.)"""
        line = ('{"Summaries":['
                '{"DeckId":"g-a","Mana":"","Name":"07 Earth’s Mightiest"},'
                '{"DeckId":"g-b","Mana":"","Name":"45 The Exiles"}]}')
        assert pm.parse_deck_names(line) == {"g-a": "07 Earth’s Mightiest",
                                            "g-b": "45 The Exiles"}

    def test_a_rename_takes_the_LATER_name(self):
        """A deck renamed in the client appears under both names; the later line is the
        current one. `setdefault` here would be the G-63 first-writer-wins trap."""
        log = "\n".join([_setdeck(guid="g-1", name="19 Old Name"),
                         _setdeck(guid="g-1", name="19 Bird Brain- Bant")])
        assert pm.parse_deck_names(log) == {"g-1": "19 Bird Brain- Bant"}

    def test_a_nameless_summary_cannot_steal_the_next_ones_name(self):
        """The bounded window is the whole guard: without it a summary missing a Name
        reaches forward and labels itself with its neighbour's deck."""
        line = ('{"Summaries":[{"DeckId":"g-a"},' + '{"Pad":"' + "x" * 400 + '"},'
                '{"DeckId":"g-b","Name":"45 The Exiles"}]}')
        assert pm.parse_deck_names(line) == {"g-b": "45 The Exiles"}

    def test_a_log_with_no_summaries_is_empty_not_a_crash(self):
        assert pm.parse_deck_names(_log(_event())) == {}
        assert pm.parse_deck_names("") == {} and pm.parse_deck_names(None) == {}


class TestArenaHeaderWriting:
    """Writing 60-odd headers by hand is where a wrong one hides, so the plan is printed
    before anything is written and every write re-parses the file."""

    def _roster(self, tmp_path, monkeypatch, **decks):
        import deck as dk
        d = tmp_path / "decks"
        for name, body in decks.items():
            (d / name).mkdir(parents=True)
            (d / name / "deck.txt").write_text(body, encoding="utf-8")
        monkeypatch.setattr(dk, "DECKS_DIR", str(d))
        return d

    PLAIN = "#: name: Earth's Mightiest\n#: format: Standard\n4 Shock (M21) 159\n"

    def test_a_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        d = self._roster(tmp_path, monkeypatch, **{"07-earths": self.PLAIN})
        before = (d / "07-earths" / "deck.txt").read_text(encoding="utf-8")
        written, plan = pm.map_decks(_setdeck(), apply=False, out=lambda *_a: None)
        assert written == 0
        assert [p[3] for p in plan] == ["add"]
        assert (d / "07-earths" / "deck.txt").read_text(encoding="utf-8") == before

    def test_apply_inserts_after_the_format_header(self, tmp_path, monkeypatch):
        d = self._roster(tmp_path, monkeypatch, **{"07-earths": self.PLAIN})
        written, _ = pm.map_decks(_setdeck(), apply=True, out=lambda *_a: None)
        assert written == 1
        lines = (d / "07-earths" / "deck.txt").read_text(encoding="utf-8").splitlines()
        assert lines[1].startswith("#: format:")
        assert lines[2] == ("#: arena: 07 Earth’s Mightiest, "
                            "e3a6c595-914d-4809-bd6d-630b3758ca89")
        assert "4 Shock (M21) 159" in lines          # card lines untouched

    def test_a_second_run_is_a_no_op(self, tmp_path, monkeypatch):
        self._roster(tmp_path, monkeypatch, **{"07-earths": self.PLAIN})
        pm.map_decks(_setdeck(), apply=True, out=lambda *_a: None)
        written, plan = pm.map_decks(_setdeck(), apply=True, out=lambda *_a: None)
        assert written == 0 and [p[3] for p in plan] == ["unchanged"]

    def test_a_renamed_deck_REPLACES_the_old_header_rather_than_stacking(
            self, tmp_path, monkeypatch):
        d = self._roster(tmp_path, monkeypatch, **{"07-earths": self.PLAIN})
        pm.map_decks(_setdeck(name="07 Old Name"), apply=True, out=lambda *_a: None)
        written, plan = pm.map_decks(_setdeck(), apply=True, out=lambda *_a: None)
        assert written == 1 and [p[3] for p in plan] == ["update"]
        body = (d / "07-earths" / "deck.txt").read_text(encoding="utf-8")
        assert body.count("#: arena:") == 1
        assert "07 Old Name" not in body

    def test_two_arena_decks_claiming_one_repo_deck_write_NOTHING(
            self, tmp_path, monkeypatch):
        """An old copy left in the client looks exactly like this. A header naming the
        wrong one of two decks is worse than no header — the parser would then attribute
        matches to it with full confidence."""
        d = self._roster(tmp_path, monkeypatch, **{"07-earths": self.PLAIN})
        log = "\n".join([_setdeck(guid="g-a", name="07 Earth’s Mightiest"),
                         _setdeck(guid="g-b", name="07 Earth’s Mightiest (old)")])
        written, plan = pm.map_decks(log, apply=True, out=lambda *_a: None)
        assert written == 0 and [p[3] for p in plan] == ["conflict"]
        assert "#: arena:" not in (d / "07-earths" / "deck.txt").read_text(encoding="utf-8")

    def test_an_arena_deck_matching_no_repo_deck_is_reported_not_forced(
            self, tmp_path, monkeypatch, capsys):
        self._roster(tmp_path, monkeypatch, **{"07-earths": self.PLAIN})
        written, plan = pm.map_decks(_setdeck(name="Some Precon", guid="g-x"),
                                     apply=True)
        assert written == 0 and plan == []
        assert "Some Precon" in capsys.readouterr().out

    def test_the_header_lands_even_with_no_format_line(self, tmp_path, monkeypatch):
        d = self._roster(tmp_path, monkeypatch,
                         **{"07-earths": "#: name: X\n4 Shock (M21) 159\n"})
        pm.map_decks(_setdeck(), apply=True, out=lambda *_a: None)
        lines = (d / "07-earths" / "deck.txt").read_text(encoding="utf-8").splitlines()
        assert lines[1].startswith("#: arena:")

    def test_a_backup_is_written(self, tmp_path, monkeypatch):
        d = self._roster(tmp_path, monkeypatch, **{"07-earths": self.PLAIN})
        pm.map_decks(_setdeck(), apply=True, out=lambda *_a: None)
        assert list((d / "07-earths").glob("*.bak"))


class TestNamePrefixGuessIsDisclosed:
    """The prefix route validates the leading NUMBER and nothing else — "15 Anything At
    All" resolves to deck 15 — and `--apply` then writes that guess into the deck file as
    a permanent `#: arena:` header, after which every later match resolves to it with
    full confidence. So the run must SHOW which repo deck it landed on.

    Deliberately not a name-agreement GATE. Measured over the 22 correct `#: arena:`
    mappings on the roster, 8 disagree with the repo name ("49 Big Draco" is Scaleforge,
    "58 Treasure Planet" is Gold Standard): the Arena names are flavour names. A gate
    would block a correct attribution better than a third of the time.

    Driven through `main()` on purpose. `deck_names` is a working primitive, and G-40 is
    the recurring failure here — a primitive nothing calls is invisible to every gate, so
    the assertion has to run the path a user runs."""

    PLAIN = "#: name: Air Nomads\n#: format: Standard\n4 Shock (M21) 159\n"

    def _run(self, tmp_path, monkeypatch, capsys, arena_name):
        d = TestArenaHeaderWriting._roster(self, tmp_path, monkeypatch,
                                           **{"15-air-nomads": self.PLAIN})
        log = "\n".join([_setdeck(name=arena_name, guid="g-15"),
                         _header(date="8/7/2026", time="7:33:25 AM"), _event()])
        src = tmp_path / "s.log"
        src.write_text(log, encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["parse_matches.py", str(src),
                                         "--out", str(tmp_path / "m.csv")])
        pm.main()
        return d, capsys.readouterr().out

    def test_the_repo_deck_name_is_printed_next_to_the_guess(
            self, tmp_path, monkeypatch, capsys):
        _d, out = self._run(tmp_path, monkeypatch, capsys, "15 Air Nomads")
        assert "name prefix" in out
        assert "'Air Nomads'" in out            # the REPO deck's name, to confirm against
        assert "LEADING NUMBER only" in out     # and the warning that it is a guess

    def test_a_flavour_name_still_resolves_rather_than_being_blocked(
            self, tmp_path, monkeypatch, capsys):
        """The 8-of-22 case. `15 Sky Bison` is a legitimate Arena name for deck 15; a
        name-agreement gate would refuse it and lose the attribution."""
        _d, out = self._run(tmp_path, monkeypatch, capsys, "15 Sky Bison")
        assert "deck 15" in out and "UNRESOLVED" not in out
        assert "'Air Nomads'" in out            # …and the disagreement is visible

    def test_the_explicit_header_route_is_not_nagged(
            self, tmp_path, monkeypatch, capsys):
        """A header a human wrote needs no confirming — only the guess does."""
        body = self.PLAIN.replace("#: format: Standard\n",
                                  "#: format: Standard\n#: arena: 15 Sky Bison, g-15\n")
        TestArenaHeaderWriting._roster(self, tmp_path, monkeypatch,
                                       **{"15-air-nomads": body})
        log = "\n".join([_setdeck(name="15 Sky Bison", guid="g-15"),
                         _header(date="8/7/2026", time="7:33:25 AM"), _event()])
        src = tmp_path / "s.log"
        src.write_text(log, encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["parse_matches.py", str(src),
                                         "--out", str(tmp_path / "m.csv")])
        pm.main()
        out = capsys.readouterr().out
        assert "#: arena: header" in out
        assert "LEADING NUMBER only" not in out


class TestResultEvidenceIsPrinted:
    """G-52 — the surface that decides W/L must show what it decided from. A single
    inverted seat read flips every row in a paste the same way, which reads as a losing
    streak rather than as a bug; the first fifteen matches were checked by re-reading the
    JSON by hand, which is the cost this removes."""

    def _run(self, tmp_path, monkeypatch, capsys, **ev):
        src = tmp_path / "s.log"
        src.write_text("\n".join([_header(), _event(**ev)]), encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["parse_matches.py", str(src),
                                         "--out", str(tmp_path / "m.csv")])
        pm.main()
        return capsys.readouterr().out

    def test_the_dry_run_prints_the_two_integers_behind_the_verdict(
            self, tmp_path, monkeypatch, capsys):
        out = self._run(tmp_path, monkeypatch, capsys, my_team=2, winner=2)
        assert "[my team 2 · winner 2]" in out
        assert "finalMatchResult read" in out    # and how to read it

    def test_a_loss_shows_the_mismatching_pair(self, tmp_path, monkeypatch, capsys):
        out = self._run(tmp_path, monkeypatch, capsys, my_team=2, winner=1)
        assert "[my team 2 · winner 1]" in out

    def test_the_concede_shows_in_the_line(self, tmp_path, monkeypatch, capsys):
        out = self._run(tmp_path, monkeypatch, capsys,
                        ended_by="ResultReason_Concede")
        assert "by concede" in out


class TestAdoptingArenaDeckNames:
    """Arena is allowed to be the source of truth for a deck's NAME — but only where the
    pairing is proven, and only where the difference is real."""

    def _roster(self, tmp_path, monkeypatch, **decks):
        return TestArenaHeaderWriting._roster(self, tmp_path, monkeypatch, **decks)

    GUID = "e3a6c595-914d-4809-bd6d-630b3758ca89"

    def _cored(self, name, arena=None, extra="", guid=None):
        """`guid` defaults to this class's GUID. Every deck in a fixture roster needs its
        OWN — `arena_deck_map` keys on the GUID, so two decks sharing one silently make
        the map resolve to whichever was read last."""
        head = f"#: name: {name}\n#: format: Standard\n"
        if arena:
            head += f"#: arena: {arena}, {guid or self.GUID}\n"
        return head + extra + "4 Shock (M21) 159\n"

    def test_a_guid_matched_rename_is_adopted(self, tmp_path, monkeypatch):
        d = self._roster(tmp_path, monkeypatch,
                         **{"45-exile": self._cored("Exile Dividend", "45 Old Name")})
        written, plan = pm.sync_deck_names(_setdeck(name="45 The Exiles", guid=self.GUID),
                                           apply=True, out=lambda *_a: None)
        assert written == 1
        assert [(p[0], p[2], p[3]) for p in plan] == [("45", "Exile Dividend",
                                                       "The Exiles")]
        assert "#: name: The Exiles" in (d / "45-exile" / "deck.txt").read_text(
            encoding="utf-8")

    def test_a_name_prefix_match_NEVER_adopts(self, tmp_path, monkeypatch):
        """The deck resolves for ATTRIBUTION on the number alone, which is not proof of
        identity — so it must not be allowed to rewrite the deck's name."""
        self._roster(tmp_path, monkeypatch,
                     **{"45-exile": self._cored("Exile Dividend")})   # no #: arena:
        written, plan = pm.sync_deck_names(_setdeck(name="45 The Exiles", guid="g-new"),
                                           apply=True, out=lambda *_a: None)
        assert (written, plan) == (0, [])

    def test_typography_alone_is_not_a_rename(self, tmp_path, monkeypatch):
        """Arena writes a curly apostrophe, a doubled space and a hyphen for an em dash.
        Adopting those would churn the repo every run and import the degradation."""
        self._roster(tmp_path, monkeypatch,
                     **{"07-e": self._cored("Earth's Mightiest", "07 X")})
        _w, plan = pm.sync_deck_names(_setdeck(name="07  Earth’s Mightiest",
                                               guid=self.GUID), out=lambda *_a: None)
        assert plan == []

    def test_a_variant_keeps_its_parent_prefix(self, tmp_path, monkeypatch):
        """G-27's rationale audit leans on the "<parent> — <variant>" convention, so a
        variant adopting "Ancient Decay" must not become a bare orphaned name."""
        self._roster(tmp_path, monkeypatch, **{
            "26-iron-forge": self._cored("Iron Forge", "26 Iron Forge", guid="g-parent"),
        })
        (tmp_path / "decks" / "26-iron-forge" / "26b-scrap.txt").write_text(
            self._cored("Iron Forge — Scrapyard Tithe", "26b Old"), encoding="utf-8")
        _w, plan = pm.sync_deck_names(_setdeck(name="26b Ancient Decay", guid=self.GUID),
                                      out=lambda *_a: None)
        assert [(p[0], p[3]) for p in plan] == [("26b", "Iron Forge — Ancient Decay")]

    def test_a_variant_whose_arena_name_repeats_the_parent_is_not_doubled(
            self, tmp_path, monkeypatch):
        """"54b Grand Lotus- Comet" already carries the parent; adopting it naively gives
        "Grand Lotus — Grand Lotus- Comet". Here it should be a no-op entirely."""
        self._roster(tmp_path, monkeypatch, **{
            "54-lotus": self._cored("Grand Lotus", "54 Grand Lotus", guid="g-parent"),
        })
        (tmp_path / "decks" / "54-lotus" / "54b-comet.txt").write_text(
            self._cored("Grand Lotus — Comet", "54b Old"), encoding="utf-8")
        _w, plan = pm.sync_deck_names(_setdeck(name="54b Grand Lotus- Comet",
                                               guid=self.GUID), out=lambda *_a: None)
        assert plan == []

    def test_it_reports_without_the_flag_and_writes_nothing(self, tmp_path, monkeypatch):
        """G-53 — a capability behind a flag nobody runs is invisible, so the run says a
        rename is available even when it will not make one."""
        d = self._roster(tmp_path, monkeypatch,
                         **{"45-exile": self._cored("Exile Dividend", "45 Old")})
        said = []
        written, plan = pm.sync_deck_names(_setdeck(name="45 The Exiles", guid=self.GUID),
                                           apply=False, out=said.append)
        assert written == 0 and len(plan) == 1
        # The hint names the FULL invocation, since this same line prints both when no
        # flag was given (this case) and when `--sync-names` was given without --apply.
        assert "--sync-names --apply" in "\n".join(said)
        assert "#: name: Exile Dividend" in (d / "45-exile" / "deck.txt").read_text(
            encoding="utf-8")

    def test_card_lines_survive_the_rename(self, tmp_path, monkeypatch):
        d = self._roster(tmp_path, monkeypatch,
                         **{"45-exile": self._cored("Exile Dividend", "45 Old")})
        pm.sync_deck_names(_setdeck(name="45 The Exiles", guid=self.GUID),
                           apply=True, out=lambda *_a: None)
        body = (d / "45-exile" / "deck.txt").read_text(encoding="utf-8")
        assert "4 Shock (M21) 159" in body                      # INV-04 content intact
        assert body.count("#: name:") == 1                      # replaced, not stacked
        assert list((d / "45-exile").glob("*.bak"))              # and a backup exists

    def test_a_stranded_citation_is_flagged(self, tmp_path, monkeypatch):
        """A rename can orphan a reference in ANOTHER deck's prose; nothing rewrites those
        and the rationale audit reads card names, not deck names."""
        self._roster(tmp_path, monkeypatch, **{
            "45-exile": self._cored("Exile Dividend", "45 Old"),
            "54-lotus": self._cored("Grand Lotus", "54 GL", guid="g-other",
                                    extra="#: notes: splits the role with Exile "
                                          "Dividend\n"),
        })
        said = []
        pm.sync_deck_names(_setdeck(name="45 The Exiles", guid=self.GUID), out=said.append)
        assert "old name cited in 1 other deck file(s): 54" in "\n".join(said)

    def test_renaming_a_parent_flags_the_variants_it_orphans(self, tmp_path, monkeypatch):
        """The mirror of the convention `_adopted_name` protects. Renaming a VARIANT keeps
        its "<parent> — <variant>" shape; renaming the PARENT breaks that shape for every
        variant beneath it, and those have no Arena GUID of their own so nothing can
        rename them from evidence. The real sync orphaned four decks this way."""
        self._roster(tmp_path, monkeypatch, **{
            "28-dinos": self._cored("Dino Stampede", "28 Old", guid="g-parent"),
        })
        (tmp_path / "decks" / "28-dinos" / "28a-owned.txt").write_text(
            self._cored("Dino Stampede — Owned Build"), encoding="utf-8")
        said = []
        pm.sync_deck_names(_setdeck(name="28 Triceraton", guid="g-parent"), out=said.append)
        out = "\n".join(said)
        assert "VARIANT(S) carry the old parent name" in out
        assert "28a 'Dino Stampede — Owned Build'" in out

    def test_renaming_a_VARIANT_flags_no_orphans(self, tmp_path, monkeypatch):
        """Only a parent rename can orphan anything — a variant has nothing beneath it."""
        self._roster(tmp_path, monkeypatch, **{
            "28-dinos": self._cored("Dino Stampede", "28 Dino Stampede", guid="g-parent"),
        })
        (tmp_path / "decks" / "28-dinos" / "28a-owned.txt").write_text(
            self._cored("Dino Stampede — Owned Build", "28a Old"), encoding="utf-8")
        said = []
        pm.sync_deck_names(_setdeck(name="28a Raptor Pack", guid=self.GUID),
                           out=said.append)
        assert "VARIANT(S)" not in "\n".join(said)

    def test_a_citation_that_still_reads_correctly_is_not_flagged(
            self, tmp_path, monkeypatch):
        """"Unlock" -> "Unlocked" keeps every citation valid. Flagging it would bury the
        real cases in noise."""
        self._roster(tmp_path, monkeypatch, **{
            "51-unlock": self._cored("Unlock", "51 Old"),
            "54-lotus": self._cored("Grand Lotus", "54 GL", guid="g-other",
                                    extra="#: notes: the Unlock shell does this too\n"),
        })
        said = []
        pm.sync_deck_names(_setdeck(name="51 Unlocked", guid=self.GUID), out=said.append)
        assert "cited in" not in "\n".join(said)


class TestSourcelessNameReconcile:
    """`--sync-names` with no log. The repo already holds Arena's name for every
    GUID-paired deck, so reconciling a months-old divergence must not require a paste
    covering all 106 decks — that is a capability nobody reaches (G-53)."""

    def _roster(self, tmp_path, monkeypatch, **decks):
        return TestArenaHeaderWriting._roster(self, tmp_path, monkeypatch, **decks)

    def test_it_reads_arena_names_back_out_of_the_headers(self, tmp_path, monkeypatch):
        self._roster(tmp_path, monkeypatch, **{
            "45-exile": TestAdoptingArenaDeckNames._cored(
                TestAdoptingArenaDeckNames, "Exile Dividend", "45 The Exiles",
                guid="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        })
        assert pm.stored_arena_names() == {
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee": "45 The Exiles"}
        _w, plan = pm.sync_deck_names_from_headers(out=lambda *_a: None)
        assert [(p[0], p[3]) for p in plan] == [("45", "The Exiles")]

    def test_the_guid_is_found_by_SHAPE_not_by_position(self, tmp_path, monkeypatch):
        """A deck NAME can look like anything, including something comma-ish, so the two
        header fields cannot be told apart by order."""
        self._roster(tmp_path, monkeypatch, **{
            "45-exile": "#: name: Exile Dividend\n#: format: Standard\n"
                        "#: arena: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee, 45 The Exiles\n"
                        "4 Shock (M21) 159\n",
        })
        assert pm.stored_arena_names() == {
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee": "45 The Exiles"}

    def test_a_header_with_no_guid_is_skipped(self, tmp_path, monkeypatch):
        """Only a GUID is proof of identity, so a name-only header cannot drive a
        rename."""
        self._roster(tmp_path, monkeypatch, **{
            "45-exile": "#: name: Exile Dividend\n#: format: Standard\n"
                        "#: arena: 45 The Exiles\n4 Shock (M21) 159\n",
        })
        assert pm.stored_arena_names() == {}
        assert pm.sync_deck_names_from_headers(out=lambda *_a: None) == (0, [])


class TestSyncNamesIsADryRunWithoutApply:
    """`--sync-names` SELECTS the rename; `--apply` WRITES it.

    Every assertion here drives `main()`, not the helper, because the helper was never
    the problem: `sync_deck_names(text, apply=…)` has taken the flag since it was
    written and `TestAdoptingArenaDeckNames` proves both sides of it. What was wrong was
    what `main()` PASSED — `apply=args.sync_names` on the paste path (the only writer in
    the file ignoring --apply) and a hardcoded `apply=True` on the sourceless one, which
    could therefore not be previewed at all. It rewrote ten `#: name:` headers in one
    2026-08-25 session when two had been shown to the user.

    That is the G-40 shape one layer up, and it is why these live at the CLI: a
    parameterized primitive tells you nothing about whether its caller asks."""

    GUID = "e3a6c595-914d-4809-bd6d-630b3758ca89"

    def _roster(self, tmp_path, monkeypatch):
        return TestArenaHeaderWriting._roster(self, tmp_path, monkeypatch, **{
            "45-exile": TestAdoptingArenaDeckNames._cored(
                TestAdoptingArenaDeckNames, "Exile Dividend", "45 The Exiles",
                guid=self.GUID)})

    def _name(self, d):
        return [ln for ln in (d / "45-exile" / "deck.txt").read_text(
            encoding="utf-8").splitlines() if ln.startswith("#: name:")][0]

    def _run(self, tmp_path, monkeypatch, *argv):
        monkeypatch.setattr("sys.argv", ["parse_matches.py", *argv,
                                         "--out", str(tmp_path / "m.csv")])
        return pm.main()

    # ---- sourceless reconcile: the path that could not be previewed at all -------

    def test_sourceless_sync_names_alone_writes_nothing(
            self, tmp_path, monkeypatch, capsys):
        d = self._roster(tmp_path, monkeypatch)
        self._run(tmp_path, monkeypatch, "--sync-names")
        out = capsys.readouterr().out
        assert "'The Exiles'" in out                       # the plan IS shown…
        assert "--apply" in out                            # …with how to take it
        assert self._name(d) == "#: name: Exile Dividend"  # …and nothing was written
        assert not list((d / "45-exile").glob("*.bak"))

    def test_sourceless_sync_names_with_apply_writes(self, tmp_path, monkeypatch):
        d = self._roster(tmp_path, monkeypatch)
        self._run(tmp_path, monkeypatch, "--sync-names", "--apply")
        assert self._name(d) == "#: name: The Exiles"
        assert list((d / "45-exile").glob("*.bak"))

    # ---- paste path -------------------------------------------------------------

    def _log(self, tmp_path):
        src = tmp_path / "s.log"
        src.write_text("\n".join([_setdeck(name="45 The Exiles", guid=self.GUID),
                                  _header(date="8/7/2026", time="7:33:25 AM"),
                                  _event()]), encoding="utf-8")
        return str(src)

    def test_paste_sync_names_alone_writes_nothing(self, tmp_path, monkeypatch):
        d = self._roster(tmp_path, monkeypatch)
        self._run(tmp_path, monkeypatch, self._log(tmp_path), "--sync-names")
        assert self._name(d) == "#: name: Exile Dividend"

    def test_paste_sync_names_with_apply_writes(self, tmp_path, monkeypatch):
        d = self._roster(tmp_path, monkeypatch)
        self._run(tmp_path, monkeypatch, self._log(tmp_path), "--sync-names", "--apply")
        assert self._name(d) == "#: name: The Exiles"

    def test_a_routine_apply_ingest_never_renames_a_deck(self, tmp_path, monkeypatch):
        """The other half of the conjunction, and the one a user hits by accident.
        `session.log --apply` is the ordinary ingest; it must not rewrite a deck's name
        as a side effect of recording a match, even though the paste contains the
        Arena name that would drive the rename."""
        d = self._roster(tmp_path, monkeypatch)
        self._run(tmp_path, monkeypatch, self._log(tmp_path), "--apply")
        assert self._name(d) == "#: name: Exile Dividend"


class TestPooledReads:
    """The per-deck split cannot reach the sample floor at this roster size, so the
    record needs a denominator that can."""

    def _rows(self, spec):
        return [{"Deck": d, "Result": r, "Event": e} for d, r, e in spec]

    def test_all_decks_pools_across_the_roster(self, capsys):
        pm.report(self._rows([("7", "W", "Play"), ("7", "L", "Play"),
                              ("45", "W", "Ladder")]))
        out = capsys.readouterr().out
        assert "ALL DECKS" in out
        assert "n=3 — 17 more for a read" in out

    def test_the_event_split_appears_only_when_there_is_more_than_one(self, capsys):
        pm.report(self._rows([("7", "W", "Play"), ("7", "L", "Play")]))
        one = capsys.readouterr().out
        assert "Ladder" not in one and "  Play" not in one
        pm.report(self._rows([("7", "W", "Play"), ("7", "L", "Ladder")]))
        assert "Ladder" in capsys.readouterr().out

    def test_pooling_still_refuses_a_small_sample(self, capsys):
        pm.report(self._rows([("7", "W", "Play")] * 5))
        out = capsys.readouterr().out
        assert "%" not in out.split("Pooled")[1].split("A pooled rate")[0]

    def test_a_reachable_sample_does_print_a_rate_and_interval(self, capsys):
        pm.report(self._rows([("7", "W", "Play")] * 12 + [("45", "L", "Play")] * 8))
        pooled = capsys.readouterr().out.split("Pooled")[1]
        assert "60%" in pooled and "95% CI" in pooled

    def test_the_pooled_caveat_is_always_printed(self, capsys):
        pm.report(self._rows([("7", "W", "Play")]))
        assert "never whether a deck is good" in capsys.readouterr().out


class TestHeaderSyncRidesAlong:
    """Header upkeep as a separate command is upkeep nobody runs (the G-53 shape), so
    the normal match flow performs it — quietly, and only when something changes."""

    PLAIN = TestArenaHeaderWriting.PLAIN

    def _roster(self, tmp_path, monkeypatch):
        return TestArenaHeaderWriting._roster(self, tmp_path, monkeypatch,
                                              **{"07-earths": self.PLAIN})

    def test_apply_writes_the_header_a_dry_run_does_not(self, tmp_path, monkeypatch):
        d = self._roster(tmp_path, monkeypatch)
        f = d / "07-earths" / "deck.txt"
        written, _ = pm.sync_headers(_setdeck(), apply=False, out=lambda *_a: None)
        assert written == 0 and "#: arena:" not in f.read_text(encoding="utf-8")
        written, _ = pm.sync_headers(_setdeck(), apply=True, out=lambda *_a: None)
        assert written == 1 and "#: arena:" in f.read_text(encoding="utf-8")

    def test_an_all_unchanged_roster_says_nothing(self, tmp_path, monkeypatch):
        """A routine re-ingest must not bury the match report under header noise."""
        self._roster(tmp_path, monkeypatch)
        pm.sync_headers(_setdeck(), apply=True, out=lambda *_a: None)
        said = []
        written, _ = pm.sync_headers(_setdeck(), apply=True, out=said.append)
        assert written == 0 and said == []

    def test_a_header_written_from_the_paste_resolves_that_pastes_matches(
            self, tmp_path, monkeypatch):
        """The ordering promise in main(): sync BEFORE the mapping is built. An Arena
        name with NO deck-number prefix is resolvable only through its header — via the
        GUID here, exactly a client-side rename's shape — so if the header landed after
        the mapping was read, this paste's own match would stay unattributed."""
        self._roster(tmp_path, monkeypatch)
        renamed = _setdeck(name="Earth's Finest")             # no leading number
        pm.sync_headers(_setdeck(), apply=True, out=lambda *_a: None)   # learn the GUID
        pm.sync_headers(renamed, apply=True, out=lambda *_a: None)      # then the rename
        assert pm.resolve_deck("Earth's Finest",
                               "e3a6c595-914d-4809-bd6d-630b3758ca89",
                               pm.arena_deck_map(), pm.deck_ids())[0] == "7"

    def test_a_conflict_is_reported_and_nothing_written(self, tmp_path, monkeypatch):
        d = self._roster(tmp_path, monkeypatch)
        log = "\n".join([_setdeck(guid="g-a", name="07 Earth’s Mightiest"),
                         _setdeck(guid="g-b", name="07 Earth’s Mightiest (old)")])
        said = []
        written, _ = pm.sync_headers(log, apply=True, out=said.append)
        assert written == 0
        assert any("resolve by hand" in s for s in said)
        assert "#: arena:" not in (d / "07-earths" / "deck.txt").read_text(encoding="utf-8")

    def test_a_summaries_only_paste_syncs_headers_and_exits_cleanly(
            self, tmp_path, monkeypatch, capsys):
        """The --map-decks extraction shape fed to the NORMAL command: no matches at all.
        The first integration ran the no-matches bailout before the sync, so this exact
        paste died with 'check that Detailed Logs is enabled' — a misleading error about
        a setting that was fine — and the headers it carried were never written."""
        import sys as _sys
        d = self._roster(tmp_path, monkeypatch)
        log_file = tmp_path / "summaries.log"
        log_file.write_text(_setdeck() + "\n", encoding="utf-8")
        monkeypatch.setattr(_sys, "argv",
                            ["parse_matches.py", str(log_file), "--apply",
                             "--out", str(tmp_path / "m.csv")])
        assert pm.main() == 0
        assert "#: arena:" in (d / "07-earths" / "deck.txt").read_text(encoding="utf-8")
        assert "deck summaries only" in capsys.readouterr().out


class TestResolveDeck:
    """Arena deck name -> repo deck id. The name-prefix step ASSIGNS data from a naming
    convention, so its bounds are the load-bearing part."""

    KNOWN = {"7", "19", "19b", "45"}

    def test_the_arena_header_wins_over_the_prefix(self):
        mapping = {"07 earth’s mightiest": "45"}      # deliberately contradictory
        assert pm.resolve_deck("07 Earth’s Mightiest", "", mapping, self.KNOWN) == \
            ("45", "#: arena: header")

    def test_the_guid_resolves_even_when_the_deck_was_renamed_in_arena(self):
        mapping = {"e3a6c595": "7"}
        assert pm.resolve_deck("Totally Different Name", "E3A6C595",
                               mapping, self.KNOWN)[0] == "7"

    def test_a_zero_padded_prefix_resolves_to_the_unpadded_deck_id(self):
        assert pm.resolve_deck("07 Earth’s Mightiest", "", {}, self.KNOWN) == \
            ("7", "name prefix")

    def test_the_prefix_does_not_swallow_the_first_word_as_a_variant_letter(self):
        """`^\\s*0*(\\d+)\\s*([a-z]?)` with re.I read "07 Earth’s…" as deck "7e" — the
        letter has to be case-sensitive AND adjacent to the number."""
        assert pm.resolve_deck("07 Earth’s Mightiest", "", {}, self.KNOWN | {"7e"})[0] == "7"

    def test_a_variant_letter_is_kept_when_it_really_is_adjacent(self):
        assert pm.resolve_deck("19b GW Chocobo", "", {}, self.KNOWN) == ("19b", "name prefix")

    def test_a_prefix_naming_no_real_deck_resolves_to_nothing(self):
        """An unattributed match is a visible gap; a wrongly attributed one is a
        fabricated win rate. Blank is the only safe direction."""
        assert pm.resolve_deck("88 Not A Deck", "", {}, self.KNOWN) == ("", "")
        assert pm.resolve_deck("Some Precon", "", {}, self.KNOWN) == ("", "")

    def test_a_leading_year_is_not_a_deck_id(self):
        assert pm.resolve_deck("2026 Ladder Pile", "", {}, self.KNOWN) == ("", "")


class TestManualEntry:
    """`--add`: the hand-entered path for matches Player.log cannot see — a phone game,
    the opponent's archetype, play/draw, why a loss happened."""

    def test_the_minimal_line_is_deck_and_result(self):
        rows, warns = pm.parse_manual("49 W", deck_ids={"49"}, today="2026-08-20")
        assert warns == []
        assert rows[0]["Deck"] == "49" and rows[0]["Result"] == "W"
        assert rows[0]["Date"] == "2026-08-20"
        assert rows[0]["Event"] == "Play"

    def test_every_optional_field_round_trips(self):
        rows, warns = pm.parse_manual(
            '19 L opp="Azorius Control" why=slow play=draw note="kept a 2-lander"',
            deck_ids={"19"}, today="2026-08-20")
        assert warns == []
        r = rows[0]
        assert r["Opponent Archetype"] == "azorius-control"
        assert r["Loss Reason"] == "slow"
        assert r["On Play"] == "draw"
        assert r["Note"] == "kept a 2-lander"

    def test_archetype_spellings_collapse_to_one_key(self):
        """The whole reason to normalize: three spellings of one deck must COUNT as one,
        or each lands under the read floor and the breakdown says nothing."""
        rows, _ = pm.parse_manual("49 W opp='Mono Red'\n49 L opp=mono-red\n49 W opp='MONO  RED'",
                                  deck_ids={"49"}, today="2026-08-20")
        assert {r["Opponent Archetype"] for r in rows} == {"mono-red"}

    def test_an_unknown_deck_is_refused(self):
        """A phantom deck id would appear in --report as a deck no file backs."""
        rows, warns = pm.parse_manual("99 W", deck_ids={"49"}, today="2026-08-20")
        assert rows == []
        assert any("no deck '99'" in w for w in warns)

    def test_a_loss_reason_on_a_win_is_refused(self):
        rows, warns = pm.parse_manual("49 W why=flood", deck_ids={"49"}, today="2026-08-20")
        assert rows == []
        assert any("has no reading" in w for w in warns)

    def test_an_unknown_reason_is_warned_but_still_recorded(self):
        """Asymmetric on purpose: the vocabulary is a guess, and losing a real match to
        protect it is the worse trade."""
        rows, warns = pm.parse_manual("49 L why=banana", deck_ids={"49"}, today="2026-08-20")
        assert len(rows) == 1 and rows[0]["Loss Reason"] == "banana"
        assert any("not in the vocabulary" in w for w in warns)

    def test_ids_are_unique_against_the_existing_record(self):
        """Dedup for the LOG path is by Arena matchId; a hand row has none, so the
        generated id must not collide with one already stored."""
        rows, _ = pm.parse_manual("49 W\n49 L", deck_ids={"49"}, today="2026-08-20",
                                  existing_ids={"manual-20260820-01"})
        ids = [r["Match ID"] for r in rows]
        assert ids == ["manual-20260820-02", "manual-20260820-03"]
        assert len(set(ids)) == 2

    def test_blank_lines_and_comments_are_skipped(self):
        rows, warns = pm.parse_manual("\n# a session\n\n49 W\n", deck_ids={"49"},
                                      today="2026-08-20")
        assert len(rows) == 1 and warns == []

    def test_a_manual_row_fills_only_columns_the_log_cannot(self):
        """The four hand columns must never masquerade as log-derived data: a manual row
        leaves the Arena-sourced cells BLANK rather than inventing them."""
        rows, _ = pm.parse_manual("49 W opp=mono-red", deck_ids={"49"}, today="2026-08-20")
        r = rows[0]
        for col in ("Arena Deck", "Arena Deck ID", "My Avatar", "Opponent Avatar",
                    "Games Won", "Games Lost", "Reason", "Ended By"):
            assert r[col] == "", f"{col} should be blank on a hand-entered row"
        assert set(r) == set(pm.HEADER)


class TestTheDashboardFormAndTheCliAgree:
    """The published page emits `--add` lines and the CLI parses them. Nothing else
    connects the two, so the SHAPE of that line is a contract — and it is exactly the
    kind that rots silently, because the page is built by a different module and a
    malformed line only shows up as a warning on someone's next paste."""

    def test_the_line_the_form_builds_parses_with_no_warnings(self):
        """Byte-for-byte the string `logLine()` produces for a fully-populated match."""
        line = ('49 L opp="Mono Red" why=flood play=draw date=2026-08-20 '
                'note="kept a greedy 3-lander"')
        rows, warns = pm.parse_manual(line, deck_ids={"49"})
        assert warns == []
        r = rows[0]
        assert (r["Deck"], r["Result"], r["Opponent Archetype"], r["Loss Reason"],
                r["On Play"], r["Date"]) == ("49", "L", "mono-red", "flood", "draw",
                                             "2026-08-20")
        assert r["Note"] == "kept a greedy 3-lander"

    def test_the_forms_dropdown_reads_the_cli_vocabulary_not_a_copy(self):
        import build_dashboard
        assert build_dashboard._loss_reasons() == pm.LOSS_REASONS
        assert "flood" in build_dashboard._loss_reasons()


class TestAnnotation:
    """`--annotate`: fill the hand-only columns on matches the LOG already recorded.

    The reason this exists rather than reusing `--add`: a match Arena logged already has
    a row. Adding it again would DOUBLE-COUNT exactly the matches you cared enough to
    annotate, and `--add` cannot dedupe because a hand row has no Arena matchId."""

    def _rows(self):
        return [dict(zip(pm.HEADER, ["2026-08-20", "abc123", "49", "", "", "", "Play",
                                     "L", "", "", "", "", "", "", "", "", ""]))]

    def test_it_updates_in_place_and_never_appends(self, tmp_path):
        csvp = tmp_path / "m.csv"
        pm.write_matches(self._rows(), str(csvp))
        pm.annotate('abc123 opp="Mono Red" why=flood play=draw', str(csvp), apply=True)
        out = pm.load_matches(str(csvp))
        assert len(out) == 1, "annotate must UPDATE the row, not add a second one"
        assert out[0]["Opponent Archetype"] == "mono-red"
        assert out[0]["Loss Reason"] == "flood"
        assert out[0]["On Play"] == "draw"

    def test_it_leaves_every_log_sourced_column_alone(self, tmp_path):
        csvp = tmp_path / "m.csv"
        pm.write_matches(self._rows(), str(csvp))
        pm.annotate("abc123 opp=mono-red", str(csvp), apply=True)
        r = pm.load_matches(str(csvp))[0]
        assert (r["Deck"], r["Result"], r["Date"], r["Event"]) == ("49", "L", "2026-08-20", "Play")

    def test_it_is_idempotent(self, tmp_path):
        csvp = tmp_path / "m.csv"
        pm.write_matches(self._rows(), str(csvp))
        pm.annotate("abc123 why=flood", str(csvp), apply=True)
        first = pm.load_matches(str(csvp))
        pm.annotate("abc123 why=flood", str(csvp), apply=True)
        assert pm.load_matches(str(csvp)) == first

    def test_an_unknown_id_changes_nothing(self, tmp_path):
        """A mistyped id must not report success having done nothing."""
        csvp = tmp_path / "m.csv"
        pm.write_matches(self._rows(), str(csvp))
        pm.annotate("nope opp=mono-red", str(csvp), apply=True)
        assert pm.load_matches(str(csvp))[0]["Opponent Archetype"] == ""

    def test_a_why_on_a_non_loss_is_dropped_but_the_rest_lands(self, tmp_path):
        csvp = tmp_path / "m.csv"
        rows = self._rows()
        rows[0]["Result"] = "W"
        pm.write_matches(rows, str(csvp))
        pm.annotate("abc123 opp=mono-red why=flood", str(csvp), apply=True)
        r = pm.load_matches(str(csvp))[0]
        assert r["Loss Reason"] == "" and r["Opponent Archetype"] == "mono-red"

    def test_an_empty_value_clears_the_field(self, tmp_path):
        """Correcting a wrong annotation must be possible without editing the CSV."""
        csvp = tmp_path / "m.csv"
        pm.write_matches(self._rows(), str(csvp))
        pm.annotate("abc123 opp=mono-red why=flood", str(csvp), apply=True)
        pm.annotate("abc123 opp= why=", str(csvp), apply=True)
        r = pm.load_matches(str(csvp))[0]
        assert r["Opponent Archetype"] == "" and r["Loss Reason"] == ""

    def test_deck_result_and_date_are_not_annotatable(self, tmp_path):
        """They come from the log. Accepting them here would create a second, silent
        way to state a result — two writers for one fact."""
        pairs, warns = pm.parse_annotations("abc123 deck=12 result=W")
        assert pairs == []
        assert any("not editable here" in w for w in warns)

    def test_the_line_the_page_emits_parses_exactly(self):
        """Byte-for-byte what `annoLine()` produces. Nothing else connects the published
        page to this parser, so the line's SHAPE is a contract that rots silently."""
        line = 'b48ecdfd-60a1-49a2-940b-96e673182aa5 opp="Mono Red" why=flood play=draw'
        pairs, warns = pm.parse_annotations(line)
        assert warns == []
        mid, fields = pairs[0]
        assert mid == "b48ecdfd-60a1-49a2-940b-96e673182aa5"
        assert fields == {"Opponent Archetype": "mono-red", "Loss Reason": "flood",
                          "On Play": "draw"}


class TestIngestWatermark:
    """The transport problem, not a data problem.

    `Player.log` and the rolling `arena.log` archive are never consumed — deliberately,
    because they are what makes re-ingest and `--annotate` possible — so every extraction
    re-emits the whole history. Measured: a 280-line paste whose large majority was
    already-recorded matches from 08/07-08/23, and a 6-match paste of which 2 were
    already in. The parser deduped correctly both times; the cost is that the lines are
    carried, read and discarded."""

    def _csv(self, tmp_path, rows):
        p = tmp_path / "m.csv"
        with open(p, "w", newline="", encoding="utf-8") as fh:
            fh.write(",".join(pm.HEADER) + "\n")
            for r in rows:
                fh.write(",".join((r.get(c) or "") for c in pm.HEADER) + "\n")
        return str(p)

    def test_the_watermark_is_the_newest_logged_date(self, tmp_path):
        p = self._csv(tmp_path, [{"Date": "2026-08-07", "Match ID": "a", "Result": "W"},
                                 {"Date": "2026-08-25", "Match ID": "b", "Result": "L"},
                                 {"Date": "2026-08-19", "Match ID": "c", "Result": "W"}])
        assert pm.ingest_watermark(p) == ("2026-08-25", 3)

    def test_a_HAND_row_can_never_advance_the_watermark(self, tmp_path):
        """A `--add` row (a phone game the desktop log never saw) carries the id
        `parse_manual` stamps (`manual-YYYYMMDD-NN`) and a user-supplied date. Letting one
        set the watermark would filter out LOG matches that were never ingested —
        silently, and forever. The fixture uses the WRITER's real id shape: the old one
        used a blank id, which the writer never produces, so the guard it pinned never
        fired on a real row (BS8-03)."""
        p = self._csv(tmp_path, [{"Date": "2026-08-07", "Match ID": "a", "Result": "W"},
                                 {"Date": "2026-12-31", "Match ID": "manual-20261231-01",
                                  "Result": "L"}])
        assert pm.ingest_watermark(p) == ("2026-08-07", 1)

    def test_the_fixture_uses_the_id_shape_the_writer_stamps(self):
        """Pins the fixture to the writer: if `parse_manual`'s prefix ever changes, this
        fails rather than letting the watermark test go vacuous again."""
        assert pm.is_manual_id(f"{pm.MANUAL_ID_PREFIX}20261231-01")
        assert not pm.is_manual_id("a1b2c3")
        assert not pm.is_manual_id("")

    def test_no_logged_rows_yet_reports_no_watermark(self, tmp_path):
        assert pm.ingest_watermark(self._csv(tmp_path, [])) == ("", 0)


class TestFilterSince:
    def test_it_keeps_the_cutoff_DAY(self):
        """Inclusive on purpose: a day routinely holds both ingested and un-ingested
        matches, so `> cutoff` would drop a real match whose neighbours happened to be
        recorded first. The overlap costs nothing — dedup is on matchId."""
        text = "\n".join([_header(date="8/24/2026"), _event(match_id="old"),
                          _header(date="8/25/2026"), _event(match_id="new")])
        kept, dropped = pm.filter_since(text, "2026-08-25")
        assert "new" in kept and "old" not in kept
        assert dropped == 2

    def test_the_undated_JSON_blob_follows_its_header(self):
        """The `{...finalMatchResult...}` line carries no date prefix. It must inherit the
        `Match to` header above it — the header it belongs to — or a kept match loses its
        result and a dropped one keeps it."""
        text = "\n".join([_header(date="8/24/2026"), _event(match_id="old")])
        kept, _ = pm.filter_since(text, "2026-08-25")
        assert "old" not in kept and kept.strip() == ""

    def test_a_setdeck_line_is_dated_by_its_OWN_LastPlayed(self):
        """EventSetDeckV3 PRECEDES the matches it explains, so inheriting a neighbour's
        date would misfile it by a whole session — and losing it un-attributes every
        match in that session."""
        old = _setdeck(name="07 Old", when="2026-08-07T07:33:23.850462-05:00")
        new = _setdeck(name="31 New", when="2026-08-25T07:43:01.617881-05:00")
        kept, _ = pm.filter_since(old + "\n" + new, "2026-08-25")
        assert "31 New" in kept and "07 Old" not in kept

    def test_order_is_preserved_and_never_sorted(self):
        """`resolve_matches` walks the log IN ORDER and pairs each result with the most
        recent `Match to` header — the only place the seat appears. Re-ordering would
        mis-attribute every W/L, so this filters lines out and never moves one."""
        lines = [_header(date="8/25/2026"), _event(match_id="m1"),
                 _header(date="8/25/2026"), _event(match_id="m2")]
        kept, dropped = pm.filter_since("\n".join(lines), "2026-08-25")
        assert dropped == 0
        assert kept.splitlines() == lines

    def test_an_undatable_line_before_any_date_is_KEPT(self):
        """Dropping what cannot be dated would be guessing in the destructive direction,
        and this is a convenience over a record that is already correct."""
        kept, dropped = pm.filter_since("some preamble\n" + _header(date="8/25/2026"),
                                        "2026-08-25")
        assert "some preamble" in kept and dropped == 0

    def test_filtering_does_not_change_what_survives(self):
        """The whole safety claim: a filtered paste parses to the SAME matches as the
        unfiltered one, minus the ones already recorded."""
        text = "\n".join([_header(date="8/25/2026"), _event(match_id="keep", my_team=2,
                                                            winner=1)])
        kept, _ = pm.filter_since(text, "2026-08-25")
        a, _wa = pm.parse_log(text)
        b, _wb = pm.parse_log(kept)
        assert [r["Match ID"] for r in a] == [r["Match ID"] for r in b] == ["keep"]
        assert a[0]["Result"] == b[0]["Result"]


class TestManualDeckIdIsNormalized:
    def test_a_zero_padded_id_is_accepted(self):
        """BS8-17 / G-82: `06 L` was refused while `deck.py stats 06` worked."""
        rows, warnings = pm.parse_manual("06 L", deck_ids={"6", "19b"})
        assert warnings == [] and rows[0]["Deck"] == "06"

    def test_an_unknown_id_is_still_refused(self):
        rows, warnings = pm.parse_manual("999 L", deck_ids={"6"})
        assert rows == [] and "no deck" in warnings[0]


class TestLogDeckFlagIsValidated:
    """BS8-23: `--deck <id>` tags the WHOLE paste, and an unknown id would appear in
    `--report` as a deck nobody can open. `--add` / `--annotate` refuse one for exactly
    that reason (G-74); the log path that tags every row did not."""

    def test_an_unknown_id_exits_nonzero_before_parsing(self, tmp_path):
        import subprocess
        import sys
        empty = tmp_path / "log.txt"
        empty.write_text("", encoding="utf-8")
        r = subprocess.run([sys.executable, "scripts/parse_matches.py", "--deck", "999",
                            str(empty)], capture_output=True, text=True, timeout=120)
        assert r.returncode == 1
        assert "no deck with that id" in (r.stdout + r.stderr)

    def test_a_padded_real_id_is_accepted(self, tmp_path):
        import subprocess
        import sys
        empty = tmp_path / "log.txt"
        empty.write_text("", encoding="utf-8")
        r = subprocess.run([sys.executable, "scripts/parse_matches.py", "--deck", "06",
                            str(empty)], capture_output=True, text=True, timeout=120)
        assert "no deck with that id" not in (r.stdout + r.stderr)
