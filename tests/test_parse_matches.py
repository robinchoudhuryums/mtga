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
           reason="MatchCompletedReasonType_Success"):
    """One finalMatchResult line, in Arena's real nesting."""
    results = [{"scope": "MatchScope_Game", "result": "ResultType_WinLoss",
                "winningTeamId": g[0], "reason": "ResultReason_Game"} for g in games]
    results.append({"scope": "MatchScope_Match", "result": "ResultType_WinLoss",
                    "winningTeamId": winner, "reason": "ResultReason_Game"})
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

    def test_a_foreign_csv_is_still_refused(self, tmp_path):
        """The migration allowance accepts exactly ONE predecessor header, so the F-02
        mirror guard still stops this writer overwriting a file it does not own."""
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
