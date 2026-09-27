#!/bin/sh
# mtga_extract.sh — reduce Arena's Player.log to the lines parse_matches.py reads.
#
#   sh scripts/mtga_extract.sh Player-prev.log Player.log > capture.log
#
# Output is IN LOG ORDER and must never be sorted: the parser pairs each match result
# with the `Match to` header above it. Two kinds of line come out:
#
#   * the four shapes the match record has always used, verbatim — match headers,
#     finalMatchResult, EventSetDeckV3 (the deck you played) and DeckUpsertDeckV3;
#   * one `[MTGA-GAME]<local time>: {json}` line per FINISHED game, boiled down from
#     the play-by-play (GREMessageType_GameStateMessage): your seat, who went first,
#     the last turn number, each seat's mulligans, life totals, the game result, and
#     every card each seat showed as "owner:grpId:colours" (L = land).
#
# WHY SUMMARISE HERE rather than keep the raw lines: the play-by-play is 1.0-2.4 MB per
# match (measured 2026-09-27, 8 matches; single lines up to 88 KB). Archived raw, the
# 15-minute snapshot would rewrite hundreds of MB, and no paste could carry it. A fact
# line is about 1 KB.
#
# Plain POSIX sh + awk, because macOS ships BSD awk, not gawk — and that awk's regex
# engine scans about 3 MB/s, so a regex over a whole 88 KB line is the one thing this
# must not do (measured: each full-line match() or regex split() cost ~10 s on a 36 MB
# log). The line is split on the single character "{" instead, which is literal and
# fast, and regexes only ever run on the short pieces between braces.
#
# This file is ALSO the Mac's ~/mtga-logs/extract.sh: /log-matches embeds it verbatim,
# and tests/test_parse_matches.py fails if the two copies differ.

grep -hE 'Match to .*MatchGameRoomStateChangedEvent|"finalMatchResult"|==> EventSetDeckV3|==> DeckUpsertDeckV3|GREMessageType_GameStateMessage' "$@" 2>/dev/null |
awk '
# The value after "key": in s, or "" when the key is absent. index(), not match():
# the regex engine is the slow part even on short pieces (see above).
function num(s, key,   i) {
    i = index(s, "\"" key "\":"); if (!i) return ""
    return substr(s, i + length(key) + 3) + 0
}
function str(s, key,   i, r) {
    i = index(s, "\"" key "\":"); if (!i) return ""
    r = substr(s, i + length(key) + 3); i = index(r, "\""); if (!i) return ""
    r = substr(r, i + 1); i = index(r, "\""); return i ? substr(r, 1, i - 1) : ""
}
function colours(s,   c) {
    c = ""
    if (index(s, "CardColor_White")) c = c "W"
    if (index(s, "CardColor_Blue"))  c = c "U"
    if (index(s, "CardColor_Black")) c = c "B"
    if (index(s, "CardColor_Red"))   c = c "R"
    if (index(s, "CardColor_Green")) c = c "G"
    return c
}
function perseat(arr, k,   n, s, i, o) {
    n = split(seats[k], s, " "); o = ""
    for (i = 1; i <= n; i++) o = o (o == "" ? "" : ", ") "\"" s[i] "\": " ((k, s[i]) in arr ? arr[k, s[i]] : 0)
    return "{" o "}"
}
function emit(k, e,   res, why) {
    res = str(e, "result"); sub(/^ResultType_/, "", res)
    why = str(e, "reason"); sub(/^ResultReason_/, "", why)
    print "[MTGA-GAME]" stamp ": {\"matchId\": \"" mid "\", \"game\": " game \
        ", \"seat\": " (k in seat ? seat[k] : 0) ", \"first\": " (k in first ? first[k] : 0) \
        ", \"turns\": " (k in turns ? turns[k] : 0) ", \"winner\": " (num(e, "winningTeamId") + 0) \
        ", \"result\": \"" res "\", \"reason\": \"" why "\"" \
        ", \"mulligans\": " perseat(mull, k) ", \"teams\": " perseat(team, k) \
        ", \"life\": " perseat(life, k) ", \"cards\": [" cards[k] "]}"
    done[k] = 1
}
index($0, "GREMessageType_GameStateMessage") == 0 {
    if (match($0, /\][0-9]+\/[0-9]+\/[0-9]+ [0-9]+:[0-9]+:[0-9]+( [AP]M)?/))
        stamp = substr($0, RSTART + 1, RLENGTH - 1)
    print; next
}
{
    n = split($0, t, "{")
    for (i = 2; i <= n; i++)
        if (index(t[i], "\"matchID\"")) {
            v = str(t[i], "matchID")
            if (v != "") { mid = v; g = num(t[i], "gameNumber"); game = (g == "" ? 1 : g) }
        }
    if (mid == "") next
    k = mid SUBSEP game
    inres = 0; resseen = 0; ng = 0
    for (i = 2; i <= n; i++) {
        p = t[i]; j = index(p, "}"); body = j ? substr(p, 1, j - 1) : p
        e = t[i - 1]; tail = substr(e, length(e) - 15); h = substr(p, 1, 16)
        if (!(k in seat) && index(p, "\"systemSeatIds\"") && match(p, /"systemSeatIds": *\[ *[0-9]+ *\]/)) {
            v = substr(p, RSTART, RLENGTH); gsub(/[^0-9]/, "", v); seat[k] = v
        }
        if (index(tail, "\"turnInfo\":")) {
            tn = num(body, "turnNumber"); a = num(body, "activePlayer")
            if (tn != "") {
                if (!(k in turns) || tn > turns[k]) turns[k] = tn
                if (tn == 1 && a != "" && !(k in first)) first[k] = a
            }
        } else if (index(h, "\"lifeTotal\"")) {
            s = num(body, "systemSeatNumber")
            if (s != "") {
                if (!((k, s) in life)) seats[k] = seats[k] (seats[k] == "" ? "" : " ") s
                life[k, s] = num(body, "lifeTotal")
                v = num(body, "mulliganCount")
                if (v != "" && (!((k, s) in mull) || v > mull[k, s])) mull[k, s] = v
                v = num(body, "teamId"); if (v != "") team[k, s] = v
            }
        } else if (index(h, "\"instanceId\"") && index(body, "\"GameObjectType_Card\"")) {
            o = num(body, "ownerSeatId"); gid = num(body, "grpId")
            if (o != "" && gid != "" && !((k, o ":" gid) in have)) {
                have[k, o ":" gid] = 1
                cards[k] = cards[k] (cards[k] == "" ? "" : ", ") "\"" o ":" gid ":" colours(body) \
                    (index(body, "CardType_Land") ? "L" : "") "\""
            }
        }
        # One MatchScope_Game entry per game played SO FAR, so game N is entry N. A
        # best-of-three is assumed to accumulate them; no Bo3 log has been read yet.
        if (index(tail, "\"results\":")) { inres = !resseen; resseen = 1 }
        if (inres) {
            if (index(body, "MatchScope_Game")) gr[++ng] = body
            if (j && index(substr(p, j), "]")) inres = 0
        }
    }
    if (!(k in done) && ng >= game) emit(k, gr[game])
}'
