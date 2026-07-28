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

    def test_it_records_both_decks_and_the_reason(self):
        rows, _ = pm.parse_log(_log(_event()))
        r = rows[0]
        assert r["Course ID"] == "Avatar_Basic_BlackPanther_MSH"
        assert r["Opponent Course"] == "Avatar_Basic_Slimefoot_DMU"
        assert r["Reason"] == "Success"        # the enum prefix is stripped
        assert r["Event"] == "Play"

    def test_game_scores_are_counted_per_team(self):
        rows, _ = pm.parse_log(_log(_event(my_team=2, winner=2, games=((2,), (1,), (2,)))))
        assert (rows[0]["Games Won"], rows[0]["Games Lost"]) == (2, 1)


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
        known = {r["Match ID"] for r in first}
        fresh = [r for r in second if r["Match ID"] not in known]
        assert [r["Match ID"] for r in fresh] == ["m-2"]


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
                 "Course ID": "Avatar_Basic_BlackPanther_MSH", "Result": "L"}]
        pm.report(rows)
        out = capsys.readouterr().out
        assert "Avatar_Basic_BlackPanther_MSH" in out
        assert "#: arena:" in out          # tells you how to fix it

    def test_an_empty_record_says_so(self, capsys):
        pm.report([])
        assert "No matches recorded" in capsys.readouterr().out


class TestDeckMapping:
    def test_the_map_is_learned_from_arena_headers(self, tmp_path, monkeypatch):
        import deck as dk
        d = tmp_path / "decks"
        (d / "90-test").mkdir(parents=True)
        (d / "90-test" / "deck.txt").write_text(
            "#: name: Test\n#: arena: Avatar_Basic_BlackPanther_MSH\n4 Shock (M21) 159\n")
        monkeypatch.setattr(dk, "DECKS_DIR", str(d))
        assert pm.arena_deck_map().get("Avatar_Basic_BlackPanther_MSH") == "90"

    def test_it_degrades_to_empty_rather_than_raising(self, monkeypatch):
        """The parser is usable standalone; a broken deck dir must not take it down."""
        import deck as dk
        monkeypatch.setattr(dk, "discover_decks", lambda: (_ for _ in ()).throw(OSError()))
        assert pm.arena_deck_map() == {}
