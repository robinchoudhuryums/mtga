Record Arena match results into `matches.csv`, then read what the record can support.

Every other model in this repo grades a deck on its LIST — synergy tags, role counts, a
metrics floor. None of them has ever seen a game. `#: tier:` is a human judgment about
competitive power with no outcome data behind it, which is why the rubric leans so hard on
measurable proxies. This is the one loop that closes: what actually happened.

It **orchestrates `scripts/parse_matches.py` and never re-implements it** — the parser
stays the single source of truth for how a log line becomes a result.

## Stage 0 — Get the log (one-time setup, then per session)

Arena writes match events only when **Detailed Logs (Plugin Support)** is enabled:
Arena → Settings → Account → check "Detailed Logs (Plugin Support)", then **restart
Arena**. Nothing before the restart is captured.

**Recommended one-time setup — the rolling archive.** `Player.log` is **overwritten on
every launch**, so any session not extracted before the next launch is gone (the
roster's 2026-07-27 match is a permanent casualty of exactly this). A launchd job that
appends the filtered lines to `~/mtga-logs/arena.log` every 15 minutes makes that loss
structurally impossible; re-ingesting the archive is always safe because dedup is by
`matchId`. Run once on the Mac running Arena. Three files: the extractor, the snapshot
job that calls it, and the launchd entry that runs the snapshot.

**The extractor is `scripts/mtga_extract.sh`, copied verbatim** — the Mac has no checkout,
so this block carries it, and `tests/test_parse_matches.py` fails if this copy and the
script differ. Edit the script, then paste it here; never edit only this copy. It passes
the four match/deck line shapes through untouched and turns each finished game's
play-by-play into one `[MTGA-GAME]` line (see "The play-by-play" below).

```sh
mkdir -p ~/mtga-logs && cat > ~/mtga-logs/extract.sh <<'EXTRACT_EOF'
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
EXTRACT_EOF
cat > ~/mtga-logs/snapshot.sh <<'EOF'
#!/bin/sh
p="$HOME/Library/Logs/Wizards Of The Coast/MTGA"
d="$HOME/mtga-logs"
sh "$d/extract.sh" "$p"/Player*.log > "$d/.capture" 2>/dev/null
cat "$d/arena.log" "$d/.capture" 2>/dev/null | awk '!seen[$0]++' > "$d/.merged" \
    && mv "$d/.merged" "$d/arena.log"
EOF
chmod +x ~/mtga-logs/snapshot.sh
cat > ~/Library/LaunchAgents/com.mtga.logsnapshot.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.mtga.logsnapshot</string>
  <key>ProgramArguments</key>
  <array><string>/bin/sh</string><string>-c</string><string>"$HOME"/mtga-logs/snapshot.sh</string></array>
  <key>StartInterval</key><integer>900</integer>
  <key>RunAtLoad</key><true/>
</dict></plist>
EOF
launchctl load ~/Library/LaunchAgents/com.mtga.logsnapshot.plist
```

**Updating an existing install** needs only the `extract.sh` and `snapshot.sh` halves of
that block (and the `mtga-matches` file below): launchd runs `snapshot.sh` by path, so the
next run picks the new one up, and reloading the plist is unnecessary.

The dedupe is line-identical and safe: every captured line shape is unique (match
headers carry timestamps, the JSON payloads carry ids). With the archive in place, the
per-session ask is:

```sh
sed -E 's/\\"(MainDeck|Sideboard)\\":\[[^]]*\]/\\"\1\\":[]/g' ~/mtga-logs/arena.log | pbcopy
```

**Slim at PASTE time, never at capture time.** The `sed` drops the deck CARD LISTS, which
nothing in the parser reads — attribution uses only Name, DeckId and LastPlayed off the
same line — and they are almost the entire payload: a real 52-card selection line is 1919
bytes and slims to 152, a 92% cut, once per event join. Leaving the archive itself
unslimmed keeps it a full-fidelity record AND keeps `awk '!seen[$0]++'` working; slimming
inside `snapshot.sh` would put two forms of the same line in the archive and defeat its
own dedupe. If the paste is still too big and no decks were renamed, additionally drop
`==> DeckUpsertDeckV3` lines — but they are what keeps `#: arena:` headers current
through a rename, so prefer the sed.

**The one thing reduced at CAPTURE time is the play-by-play, and only because raw is not
an option.** Measured on a real log 2026-09-27: 1.0–2.4 MB per match across 8 matches,
single lines up to 88 KB. Kept raw, the archive would grow by hundreds of MB and the
15-minute job would rewrite all of it every run, and no paste could carry it. The
extractor keeps one ~1 KB `[MTGA-GAME]` line per game instead; the four match/deck line
shapes still go into the archive verbatim.

**Without the archive**, grab the log before relaunching Arena. Ask the user to run
this on the machine running Arena and paste the output.

**Two shortcuts, and WHICH ONE APPLIES DEPENDS ON WHETHER THE ARENA MACHINE HAS THIS
REPO.** That is the question to ask first, and it is easy to get wrong from inside a
session: the repo is checked out wherever *you* are reading this, which says nothing
about the Mac running Arena. Measured the hard way — `make matches` was added, handed
over, and failed with "No rule to make target", because the machine playing Arena had
never cloned the repo at all.

**Repo IS on the Arena machine** → `make matches` (dry run) / `make matches APPLY=1`
(writes). It wraps the extraction below plus the parse. `MTGA_LOGS=...` overrides the
path for Windows or a non-default install.

**Repo is NOT on the Arena machine** (the common case — Arena on a Mac, this repo only in
Claude sessions) → a shell function kept in `~/mtga-logs/mtga-matches.zsh` and loaded
from `~/.zshrc`, which needs nothing checked out. Keeping it in its own file makes an
update one paste; if an older copy sits inline in `~/.zshrc`, delete it (the `source`
line comes later, so the file's version wins either way):

```sh
cat > ~/mtga-logs/mtga-matches.zsh <<'MTGA_EOF'
mtga-matches() {
  local p="$HOME/Library/Logs/Wizards Of The Coast/MTGA"
  local d="$HOME/mtga-logs"
  local stamp="$d/.last-copy"          # the day of the previous copy, written below
  local cut="$1" how=""
  if [ "$cut" = "all" ]; then
    cut=""; how=" (everything)"
  elif [ -z "$cut" ] && [ -r "$stamp" ]; then
    cut=$(cat "$stamp")
    how=" (since your last copy; if that one was never pasted, run: mtga-matches all)"
  fi
  if [ -n "$cut" ] && ! [[ "$cut" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "mtga-matches: date must be YYYY-MM-DD or 'all' (got '$cut')" >&2
    echo "  a malformed date filters SILENTLY: '2026-9-2' keeps NOTHING, '09-02-2026' keeps EVERYTHING" >&2
    return 2
  fi
  local out
  out=$({ cat "$d/arena.log" 2>/dev/null
          if [ -r "$d/extract.sh" ]; then sh "$d/extract.sh" "$p"/Player*.log
          else grep -hE 'Match to .*MatchGameRoomStateChangedEvent|"finalMatchResult"|==> EventSetDeckV3' "$p"/Player*.log 2>/dev/null; fi; } \
    | grep -E 'Match to .*MatchGameRoomStateChangedEvent|"finalMatchResult"|==> EventSetDeckV3|^\[MTGA-GAME\]' \
    | awk '!seen[$0]++' \
    | sed -E 's/\\"(MainDeck|Sideboard)\\":\[[^]]*\]/\\"\1\\":[]/g' \
    | sed -E 's/"(playerName|platformId|systemSeatId|transactionId|requestId)"[[:space:]]*:[[:space:]]*("[^"]*"|[0-9]+)[[:space:]]*,[[:space:]]*//g; s/[[:space:]]*,[[:space:]]*"(playerName|platformId|systemSeatId|transactionId|requestId)"[[:space:]]*:[[:space:]]*("[^"]*"|[0-9]+)//g' \
    | awk '
        match($0, /Match to [A-Za-z0-9_-]+:/) {
          me = substr($0, RSTART + 9, RLENGTH - 10)
          $0 = substr($0, 1, RSTART - 1) "Match to ME:" substr($0, RSTART + RLENGTH)
        }
        index($0, "\"userId\"") {
          s = $0; o = ""
          while (match(s, /"userId": *"[^"]*"/)) {
            v = substr(s, RSTART, RLENGTH); sub(/^"userId": *"/, "", v); sub(/"$/, "", v)
            o = o substr(s, 1, RSTART - 1) "\"userId\": \"" (v == me ? "ME" : "OPP") "\""
            s = substr(s, RSTART + RLENGTH)
          }
          $0 = o s
        }
        { print }' \
    | awk -v cut="$cut" '
        function iso(s,   a) { split(s, a, "/"); return sprintf("%04d-%02d-%02d", a[3], a[1], a[2]) }
        cut == "" { print; next }
        {
          d = ""
          if ($0 ~ /LastPlayed/) { i = index($0, "LastPlayed"); s = substr($0, i, 90)
            if (match(s, /[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/)) d = substr(s, RSTART, RLENGTH) }
          else if (match($0, /\][0-9]+\/[0-9]+\/[0-9]+ /)) { d = iso(substr($0, RSTART+1, RLENGTH-2)) }
          if (d != "") cur = d
          if (cur == "" || cur >= cut) print
        }')
  local n=0
  if [ -n "$out" ]; then printf '%s\n' "$out" | pbcopy; n=$(printf '%s\n' "$out" | wc -l | tr -d ' ')
  else : | pbcopy; fi
  echo "copied $n lines to the clipboard${cut:+ since $cut}$how"
  if [ "$n" -gt 0 ]; then date +%Y-%m-%d > "$stamp"; fi
  if [ "$n" -eq 0 ] && [ -n "$cut" ]; then
    echo "  nothing since $cut — run 'mtga-matches all' if that looks wrong; the parser dedupes by matchId" >&2
  fi
}
MTGA_EOF
grep -q 'mtga-matches.zsh' ~/.zshrc 2>/dev/null || echo 'source ~/mtga-logs/mtga-matches.zsh' >> ~/.zshrc
source ~/mtga-logs/mtga-matches.zsh
```

**Three things in there are not obvious, and the date `awk` is deliberately NOT one of
them — it is byte-identical to the version this function shipped with**, because it
mirrors `parse_matches.filter_since` line for line and the two must not drift.

**`awk '!seen[$0]++'` — the paste was carrying every current-session line TWICE.**
`snapshot.sh` merges `Player.log` into `arena.log` every 15 minutes, and this function
greps BOTH. So every line already snapshotted is emitted once from the archive and again
from the live log, and the whole current session is duplicated whenever a snapshot has
run since Arena started (i.e. almost always). The dedupe is the same line-identical rule
`snapshot.sh` already applies to build the archive, and safe for the reason recorded
there: match headers carry timestamps and JSON payloads carry ids, so no two distinct
events produce the same line. It runs BEFORE the `sed` so it dedupes the same raw form
the archive does. Verified against the parser on a synthetic overlap: **12 lines → 8, and
`parse_matches.py` reports the identical 4 new matches from either.**

**The date is validated, because a malformed one fails SILENTLY IN BOTH DIRECTIONS.** The
comparison is lexical, so `2026-9-2` — the natural thing to type, and wrong only in its
zero-padding — sorts above every real date and keeps **nothing**, while `09-02-2026`
sorts below every real date and keeps **everything**. Measured on an 8-line fixture: 0
lines and 8 lines respectively, against 6 for the correct `2026-09-02`. The first case is
the dangerous one — an empty clipboard reads as "no new matches", not as "bad argument" —
so an unparseable date is now refused with a non-zero exit rather than obeyed, and a zero
result WITH a cut says so on stderr.

**The second `sed` drops five fields the parser never reads** — `playerName`,
`platformId`, `systemSeatId`, `transactionId`, `requestId` — verified against
`resolve_matches`, which reads only `userId` / `teamId` / `courseId` / `eventId` per seat,
plus `matchId`, `matchCompletedReason`, `resultList` and the top-level `timestamp`. Two
substitutions rather than one so a stripped field can sit first, middle or LAST in its
object without leaving a dangling comma; the line must stay valid JSON, because the parser
`json.loads` it. Measured: a `finalMatchResult` line 969 → 775 bytes spaced and 1021 → 843
compact (~18%), a whole export 3866 → 3284, with `parse_matches.py` reporting byte-identical
results from either. The ESCAPED `\"…\"` fields on an `EventSetDeckV3` line are untouched
by construction (these patterns match bare quotes), verified at 603 → 603 bytes.

Dropping `playerName` also stops opponents' display names riding along on the clipboard,
which matches what the parser already does deliberately — the module docstring says it
"stores NO userId and NO playerName".

**The coupling this creates is real and is worth stating**: it puts "what the parser
needs" in a second place, so a future parser that starts reading one of these five would
silently get nothing from a trimmed paste. What makes that acceptable is the same rule
that governs the existing MainDeck/Sideboard slim — **slim at PASTE time, never at
capture time**. `snapshot.sh` keeps `arena.log` full-fidelity, so any field dropped here
is one re-extraction away.

**The live log goes through the extractor too** (2026-09-27), so a paste carries the
`[MTGA-GAME]` lines for games the 15-minute snapshot has not reached yet. The second
`grep` keeps them alongside the three match shapes and still leaves `DeckUpsertDeckV3`
out of the paste. If `extract.sh` is missing the function falls back to the plain grep —
the matches still arrive, only their game details do not.

**`pbpaste` is gone from the count.** It round-tripped the entire clipboard through the
pasteboard a second time just to count lines, and read whatever was on the clipboard
rather than what was just written — a race if anything else copied in between. The output
is held once and counted directly.

**The paste carries no Arena user ids (2026-09-27).** One real paste held 184 of them
belonging to 47 people — you and 46 opponents — and the parser only needs to know which
seat is YOURS. The function's third `awk` rewrites your id to `ME` (read from the
`Match to <id>:` header) and every other `"userId"` to `OPP` before copying. The parser
and the dashboard's paste reader both find your seat by matching the header id to a seat
id, so `ME` = `ME` resolves exactly as the real id did; `tests/test_parse_matches.py`
runs this function from this file under bash and parses its output. The archive on the
Mac keeps the real ids — anonymise at PASTE time, the same rule as the slimming.

**It remembers the last copy (2026-09-27).** `mtga-matches` with no argument copies from
the day of its previous successful copy, kept in `~/mtga-logs/.last-copy`, and says so;
`mtga-matches all` copies everything; `mtga-matches <YYYY-MM-DD>` still works. The stamp
advances only when something was copied. The one way to lose a match is to copy and then
never paste that copy: the next copy starts from its day, so anything only in the unpasted
copy from EARLIER days is skipped — the message names `mtga-matches all` for that case,
and re-pasting everything is always safe because dedup is by matchId.

`mtga-matches` then puts a pasteable export on the clipboard. It reads the rolling
archive first and the live `Player.log` second, so it covers history Arena has already
overwritten.

**A date by hand still works** — `mtga-matches 2026-08-25` emits only that day onward —
and is what the default above computes for you. The log is NEVER trimmed — this filters the CLIPBOARD, not the
archive, which is the distinction that keeps re-ingest and `--annotate` working. Get the
date from the repo side:

```
python3 scripts/parse_matches.py --watermark      # prints the newest ingested date
```

**The `awk '!seen[$0]++'` dedupe still has no memory of its own** — it removes lines
duplicated WITHIN one invocation (the archive/Player.log overlap). What shortens a paste
ACROSS sessions is the `.last-copy` stamp above, which records what was COPIED, not what
was ingested: nothing on the Mac knows what `matches.csv` holds. `--since-last` (below) is
the repo-side filter, reading the watermark from the CSV itself.

**Why this is worth doing, and why it is only a convenience.** The archive is deliberately
never consumed, so every extraction re-emits the whole history: a real paste ran 280 lines
of which the large majority were matches from two weeks earlier, all long since recorded.
Nothing was WRONG — dedup is on Arena's `matchId` (G-57), so re-pasting is idempotent and
always was. The cost is that the lines get carried, read and discarded, and a big block
buries the handful of rows that are actually new. So: never let this filter decide
correctness. If in doubt, drop the argument and paste everything; the parser will dedupe.

The awk mirrors `parse_matches.filter_since` line for line — same date-inheritance rules,
same inclusive boundary — and the two were verified byte-identical on a real paste. If you
change one, change both, or the clipboard and the repo will disagree about what "since"
means.

**The boundary day is INCLUSIVE, deliberately.** A day routinely holds both ingested and
un-ingested matches (the 2026-08-25 session did), so `> cutoff` would drop a real match
whose neighbours happened to be recorded first. Keeping the day costs a few lines and
hands the overlap to the matchId dedup, which is what dedup is for.

**Repo-side equivalents**, for when the whole paste arrives anyway:

```
python3 scripts/parse_matches.py <file> --since-last    # filter to the stored watermark
python3 scripts/parse_matches.py <file> --since 2026-08-25
```

`--since-last` reads the watermark from `matches.csv` itself — the Date of the newest row
that carries a `Match ID`. There is no sidecar stamp file, because the CSV already holds
the fact and a second copy of it is a second thing that can drift. **Hand rows are
excluded from the watermark**: a `--add` row (a phone game the desktop log never saw) has
no matchId and a user-supplied date, so letting one advance the mark would silently filter
out LOG matches that were never ingested.

**NEVER pipe either form through `sort`/`sort -u`.** `resolve_matches` walks the log IN
ORDER and pairs each result with the most recent `Match to <userId>` header — the only
place your seat appears — so sorting silently mis-attributes every W/L. Duplicate lines
are harmless: the parser dedups by matchId.

```
# macOS
p=~/Library/Logs/"Wizards Of The Coast"/MTGA
# Windows (PowerShell): $p="$env:APPDATA\..\LocalLow\Wizards Of The Coast\MTGA"

grep -hE 'Match to .*MatchGameRoomStateChangedEvent|"finalMatchResult"|==> EventSetDeckV3' \
    "$p"/Player*.log \
  | sed -E 's/\\"(MainDeck|Sideboard)\\":\[[^]]*\]/\\"\1\\":[]/g'
```

The `sed` drops the deck card lists (92% of an EventSetDeckV3 line, and nothing reads
them). Keep it: without it the pastes get hand-trimmed in an editor instead, which is
JSON surgery on the one line attribution depends on.

**All three line shapes are required, in ONE grep.** The JSON carries the result and both
seats but NOT which seat is theirs — the local `userId` appears only in the `Match to
<userId>:` header prefix. A paste of the JSON alone makes every result a coin flip, and
the parser refuses it rather than guessing (it warns and skips). If they only have the
JSON, `--me <userId>` is the escape hatch. `EventSetDeckV3` is the deck they actually
played (Stage 3); without it every row is unattributed.

One grep, not three pastes: the parser joins matches to decks on the log's own
timestamps, so a split paste still resolves — but a `cut`-truncated line loses its
timestamp and then only the ORDER is left, which a split paste destroys.

Do not ask for the whole log — it is tens of MB, almost all of it the play-by-play. That
part is worth having, but only through the extractor, which reduces each game to one
line; the grep (or `mtga-matches`) is the ask.

### The play-by-play (`[MTGA-GAME]` lines, 2026-09-27)

With Detailed Logs on, Arena also writes the full game state
(`GREMessageType_GameStateMessage`). The extractor reads it and emits, per finished game:
your seat, who went first, the last turn number, each seat's mulligans, the life totals,
the result, and every card each seat showed (Arena id + colours). The parser joins it to
the match on the match id and fills **On Play** (only when blank — a value you typed is
kept, and a disagreement is reported), **My Mulligans**, **Opp Mulligans**, **Turns**,
**Opponent Colors** and **Opponent Cards**. It fills rows recorded by EARLIER runs too, so
the matches still in `Player.log` / `Player-prev.log` get their details on the next
paste. Older games are gone: the archive did not keep these lines before this change.

- **Card names** come from Scryfall's Arena-id lookup and are cached in
  `arena-cards.csv`, so each card costs one request ever. A card Scryfall cannot name, or
  any card during an outage, is written as `#<Arena id>` and named by a later run that sees
  the same game line.
- **Turns** is Arena's turn counter, which counts both players' turns — 14 is each
  player's 7th.
- **Opponent Colors** are the colours of the NONLAND cards they showed; a match conceded
  before they cast anything reads blank rather than guessed.
- **Why you lost stays yours** (`--annotate`). The log shows what happened, not which part
  of it decided the game.

A best-of-three is handled per game (values joined with `/`) but has never been checked
against a real Bo3 log; read the first one's dry run closely.

**Privacy:** the parser deliberately stores no `userId` and no `playerName`, and since
2026-09-27 `mtga-matches` removes both before anything is copied (`ME` / `OPP`). A paste
made by hand — the raw `grep` above, or an older copy of the function — still contains
them; don't echo them back, and don't put them in a commit. Both players' avatar cosmetics are kept — that is a cosmetic, not
a person — as is the user's own Arena deck name.

## Stage 1 — Parse (dry run first)

Save the paste to a scratch file, then:

```
python3 scripts/parse_matches.py <file>                 # dry run — always first
```

Read the output back to the user: one line per match with date, W/L, game score, deck,
opponent deck. Check two things before applying:

- **Does the date look right?** The parser prefers the log line's LOCAL timestamp and
  falls back to the JSON's UTC epoch, which files an evening session a day late. A blank
  or shifted date means the header lines were stripped from the paste.
- **Do the game details look right?** Each match with a `[MTGA-GAME]` line prints on the
  play/draw, mulligans, the last turn and the opponent's colours and first cards. Play or
  draw is the one you can check from memory; an inverted seat read would flip it.
- **Does every new match have details?** A new match with no `[MTGA-GAME]` line is named
  under "have no play-by-play line" — a phone game, or a log that rotated first. If NONE
  of the paste has game lines, the run says `extract.sh` is probably not installed.
- **Is the deck attributed?** The run prints a `Deck attribution` block: every Arena deck
  name it saw, the repo deck it resolved to, and *how* (`#: arena: header` or the
  `name prefix` guess). Read it — the prefix step assigns data from a naming convention,
  so it is the line worth checking. Unattributed rows are **kept, not dropped** — see
  Stage 3.

Then write:

```
python3 scripts/parse_matches.py <file> --apply
python3 scripts/parse_matches.py <file> --apply --deck 12   # tag one session's deck
```

Rows dedupe by Arena's `matchId`, so re-pasting an overlapping log is safe and re-running
is not destructive.

**End every log report with the next command:** `mtga-matches` with no argument — it
resumes from this copy. (`mtga-matches all` if the owner says a copy went unpasted.)

## Stage 1d — Ask why each new loss happened (right after `--apply`)

**Do this every time an ingest wrote a loss.** The loss-reason column was empty on all 94
recorded losses when this stage was added (2026-09-27): the fill-in path existed on the
dashboard and in Stage 1c, and nobody reached it, because the moment to ask is right after
the game, while the owner still remembers it — which is exactly now.

`--apply` prints, after the write, one block per new loss:

```
   # 2026-09-27  deck 21 · on the play · turn 16 · vs WB: Ajani's Pridemate; Fisk Tower; …
   c6bfb302-0aa2-49e5-886c-b5bf7c69b60e why= opp=
```

1. Show the owner each loss as a short line — deck, play/draw, turns, opponent colours and
   the cards they showed — and ask for ONE word from the vocabulary (`flood screw slow
   answer removed keep misplay outclassed`), plus the opponent's archetype if they want
   to name it. Ask once for all of them together.
2. **Never fill a reason in yourself.** The details say what happened, not what decided
   the game — a 16-turn loss to a lifegain deck can be `outclassed` or `misplay`, and only
   the owner knows which. A loss they do not remember stays blank.
3. Write their answers with Stage 1c's `--annotate` (dry run, then `--apply`), keeping
   the ids the block printed. A value left empty CLEARS that field (on these new rows it is
   already empty, so leaving one blank changes nothing).
4. **A match the owner wants thrown out** (they stepped away, misclicked into a queue):
   `<id> void=<why>` — e.g. `void=stepped-away`. Never delete the row. Dedup keys on it,
   and the next paste starts from the last copy's day, so a deleted match comes straight
   back as a live loss. A voided row keeps Result `X`, counts in no tally and no `Pld`,
   and `--report` lists it by name. The note keeps the result it replaced
   (`void (was L): stepped-away`) and `void=no` restores exactly that; an older void
   restores from its game score, and is refused rather than guessed when that is tied.

Skip the stage if the owner would rather not; it is the one step that must never be
guessed.

**Headers keep themselves current.** The same `--apply` also harvests the paste's deck
summaries and writes any new or renamed `#: arena:` header (with `.bak`s, conflicts
refused) *before* resolving the matches — so a deck renamed in the client re-maps in the
same run, and a paste of deck summaries with no matches in it still syncs headers rather
than erroring. `--map-decks` remains for the explicit roster-wide pass, but routine
ingests need no separate upkeep step.

**Deck NAMES are offered, never adopted silently.** Every run also reports any deck whose
repo `#: name:` differs from its Arena name. `--sync-names` SELECTS the reconcile and
`--apply` WRITES it — **preview first, always**:

```
python3 scripts/parse_matches.py --sync-names            # PREVIEW, from the stored headers
python3 scripts/parse_matches.py --sync-names --apply    # …adopt them
python3 scripts/parse_matches.py <file> --sync-names --apply    # …or from a fresh paste
```

**Show the user the plan and get a confirmation before passing `--apply`.** A rename is
prose other files cite, and the preview is the only place the ⚠ flags below appear before
the write. Until 2026-08-26 `--sync-names` wrote on its own and the sourceless form could
not be previewed at all; a session ran it and adopted TEN names having shown the user two.
A routine `<file> --apply` ingest never renames anything — the rename must be asked for by
name — so there is no reason to reach for `--sync-names` unless a rename is the task.

Four things make this safe enough to offer automatically, and each one is load-bearing:

- **Identity is the DeckId GUID**, never the deck number and never the card list. A GUID
  survives every edit Arena permits; a card list changes the moment you tune, so
  card-matching would refuse exactly the decks under active development. A `name prefix`
  match is *never* enough to rename — that route validates the leading number alone.
- **Typography is not a rename.** Arena writes a curly apostrophe, doubled spaces and a
  hyphen where the repo uses an em dash. Comparison is on words only, so
  `54b Grand Lotus- Comet` leaves `Grand Lotus — Comet` untouched instead of churning it
  every run.
- **The variant convention survives.** A variant adopting `Ancient Decay` becomes
  `Iron Forge — Ancient Decay`, because G-27's rationale audit leans on the
  `<parent> — <variant>` shape. Arena repeating the parent is not doubled.
- **Stranded citations are flagged.** 50 of the 106 decks are named inside another deck's
  header prose, and nothing rewrites prose automatically. A `⚠` on a rename means the old
  name is cited elsewhere and you fix those by hand. Suppressed when the new name still
  contains the old one (`Unlock` → `Unlocked` keeps every citation valid).

A parent rename also **orphans its variants** — they carry the old parent name in their
own `#: name:` and have no Arena GUID of their own, so nothing can rename them from
evidence. Those are flagged too, and composing the new variant name is a hand edit.

Report the plan to the user and let them choose. Renaming is editorial: when the roster
was first reconciled (2026-08-14, 12 decks) `Stampede Engine` → `Stampede` and
`Jeskai Tempest` → `Tempest` each dropped a word that was doing work, and only the owner
knows whether Arena's name or the repo's is the one they meant.

## Stage 1b — Hand-entered matches (`--add`)

**The log cannot see two things that matter, and one whole platform.** Arena records the
deck you submitted, the outcome and — through the extractor — who went first, mulligans
and the cards the opponent showed; it records no archetype LABEL for their deck and
nothing about why you lost. And a **phone game never reaches the desktop `Player.log` at
all** — that log is written by the install that
played the match, so a couch session on iOS is invisible to Stage 1 no matter how you
extract it. `--add` is the path for both.

One match per line, `<deck> <W|L|D>` plus optional `key=value`:

```
49 W opp="Mono Red" play=play
49 L opp=mono-red why=flood note="kept a greedy 3-lander"
19 L opp=azorius-control why=slow play=draw
```

```
python3 scripts/parse_matches.py <file> --add            # dry run — always first
python3 scripts/parse_matches.py <file> --add --apply    # append
make log-match DECK=49 R=L OPP=mono-red WHY=flood        # one match, same dry-run rule
make log-match DECK=49 R=W APPLY=1
```

Keys: `opp`, `why`, `play` (play/draw), `event`, `date`, `note`. The loss vocabulary is
`flood screw slow answer removed keep misplay outclassed` — **closed so it can be
COUNTED**, since free text cannot answer "which decks flood out", which is the reason to
record it at all.

**Three validation rules, and their asymmetry is deliberate.** An unknown DECK id is a
hard reject (it would show in `--report` as a deck no file backs). A `why` on a non-loss
is refused (a loss reason on a win has no reading). An unknown `why` is warned about and
**recorded anyway** — the vocabulary is a guess, and losing a real match to protect a list
someone invented is the worse trade. Add a key to `LOSS_REASONS` when a warning recurs.

**`--add` only appends, and cannot dedupe.** The log path is idempotent because Arena
supplies a `matchId`; a hand row has none, so re-pasting lines already entered creates
duplicates. That is why the dry run prints every row — it is the only guard, and it
cannot distinguish a repeat from a genuine second game against the same deck that day.

**From a phone: the dashboard's "Log a match" panel.** The published page is static and
writes nothing — it queues matches in that browser's `localStorage` and hands back these
exact lines to copy. Log during a session, copy the block afterwards, then `--add`. The
queue survives a reload, which is the load-bearing part: without it, backgrounding the
browser would discard an evening's matches.

## Stage 1c — Annotate matches the log DID record (`--annotate`)

Stage 1b is for matches Arena never saw. This is the other half: a match Arena *did*
log already has a row with a real deck, result and date — what it lacks is what only you
know (and `play`, when the game lines were not captured). **Do not re-enter those through `--add`.** `--add` cannot dedupe
(no Arena `matchId` on a hand row), so it would append a second row for a match already
recorded — double-counting precisely the matches you cared enough to annotate.

`--annotate` joins on the match id and UPDATES in place:

```
b48ecdfd-60a1-49a2-940b-96e673182aa5 opp="Mono Red" why=flood play=draw
```

```
python3 scripts/parse_matches.py <file> --annotate            # dry run
python3 scripts/parse_matches.py <file> --annotate --apply
```

Takes `opp`, `why`, `play`, `note` only. **`deck`, `result` and `date` are refused** —
they come from the log, and accepting them here would be a second, silent way to state a
result. An **unknown id is a hard reject**, not a no-op, so a truncated id cannot report
success having changed nothing. An **empty value clears** the field, which is how you fix
a wrong annotation without hand-editing the CSV. Re-running is idempotent.

**Getting the ids without reading a log by hand: the dashboard.** Paste a `Player.log`
block into the "…or annotate matches Arena already logged" box; the page lists every
match it finds with date, deck, result and the opponent's avatar, gives each one the same
four fields, and hands back these lines. It parses the block **only to label the rows for
you** — every line it emits carries the match id and nothing else, so even a parsing error
on that side cannot put a wrong W/L into `matches.csv`. (Cross-checked at build time on
the 57-match sample: the page's seat read agreed with the parser's on all 57.)

The normal order is: ingest the log (Stage 1) → annotate (here). Annotating first fails
loudly, because the ids are not in `matches.csv` yet.

## Stage 2 — Report

```
python3 scripts/parse_matches.py --report
python3 scripts/parse_matches.py --report --deck 21     # one deck, one line per match
```

**`--report --deck <id>` is the per-deck history (2026-09-27)**: each match with its
result, play/draw, turns, opponent colours, the loss reason and the opponent's first
non-basic cards, then the losses tallied by opponent colours and by reason as COUNTS. It
answers "what does this deck meet and lose to" — the question a tune asks — where the
pooled report answers "am I winning". The same floor applies and is printed: no rate
under 20 matches, and nothing in it is a reason to cut a card or move a tier.

**Read this the way the tool prints it, not the way a percentage invites.** Below ~20
matches it refuses to show a rate at all, and above it the 95% Wilson interval is usually
still 30 points wide. State the interval whenever you quote a number.

**The per-deck rows will not fill, and the pooled block is the answer to that.** At 106
decks the per-deck split cannot reach n=20 in any realistic timeframe — after a month of
play the best row sat at n=4 — so the report also pools: `ALL DECKS`, then a Play/Ladder
split, each with the distance to a readable sample printed as a countdown rather than a
wall. **Pooling answers a different question and the difference is not decorative**: a
pooled rate says whether *you* are winning, never whether a deck is good, because it
averages a tuned deck with a brew. Use it to notice a slump. Route any per-deck verdict
to the rows above, once they fill.

The honest reading: **a win rate separates a broken deck from a fine one; it will not
separate a 55% deck from a 45% one without hundreds of games.** Use it to find disasters,
never to justify a marginal swap. If the user asks "should I cut X because the deck is
losing", the answer routes to `/tune-deck` and full oracle text — the match record says
the deck is losing, not why.

Do **not** feed this into `#: tier:`. Tier rates the LIST's competitive power against the
rubric in CLAUDE.md; a small-sample win rate is not evidence at that resolution, and
writing one into the prose would be exactly the stale-rationale failure
`tier --audit-rationale` exists to catch.

## Stage 3 — Map the decks (the part that makes the record useful)

**`courseId` is NOT the deck.** Every value the first real sample produced was an
`Avatar_Basic_*` cosmetic — the avatar, a global profile setting changed independently of
the deck — and nine matches were recorded against it before anyone read the values. The
columns are `My Avatar` / `Opponent Avatar` now. Never map a deck from one, and never
quote one as an opponent archetype.

The deck actually played comes from `EventSetDeckV3`, which carries the Arena deck NAME
and a stable `DeckId` GUID. It resolves to a repo deck in three steps: `--deck <id>`
overrides everything; then a `#: arena:` header; then the leading number of the Arena name
("07 Earth's Mightiest" → deck 7), accepted only when that deck id exists.

**Do the whole roster in one pass, not one deck at a time.** Ask for the client's deck
list and let the parser write every header:

```
p=~/Library/Logs/"Wizards Of The Coast"/MTGA
grep -hE '==> (EventSetDeckV3|DeckUpsertDeckV3)' "$p"/Player*.log
```

(Not `DeckGetDeckSummariesV3` — its name promises the whole collection, but Arena logs
only the request and a bare ack with no payload: measured 0 decks from 5 calls in the
first real sample. Grepping for it hauls in nothing.)

```
python3 scripts/parse_matches.py <file> --map-decks           # dry run — always first
python3 scripts/parse_matches.py <file> --map-decks --apply   # writes, with .baks
```

It harvests every `{"DeckId":…,"Name":…}` the paste contains, matches each to a repo deck
by the leading-number convention, and writes `#: arena: <name>, <GUID>`. Read the dry run:
`+` add, `~` update, `=` unchanged, `!` conflict. **Several copies of one deck resolve to
the newest (2026-09-27, owner decision)**: the owner replaces a deck by deleting it in
Arena and importing the new version as a NEW deck, so same-named copies are expected and
the most recent is correct. When every claimant carries the same name and a timestamp,
the one with the latest `LastUpdated` (then `LastPlayed`) is written and the older copies
are named once; their matches still resolve by name. **A conflict still writes nothing**
when the claimants' NAMES differ or carry no timestamp — that is not a copy, and a header
naming the wrong deck is worse than no header. Arena decks whose names carry no repo deck
number are listed, never forced.

To set one by hand, the header takes the name, the GUID, or both:

```
#: arena: 07 Earth’s Mightiest, e3a6c595-914d-4809-bd6d-630b3758ca89
```

The GUID survives a rename in the Arena client; the name is the one a person can type
without a log. Prefer setting **both**. A row with no Arena deck at all had its
`EventSetDeckV3` in a log that already rotated — that one is unrecoverable, and the report
says so rather than borrowing a neighbouring session's deck.

After editing a deck file, confirm INV-04 still holds (Stage 4 covers it).

## Stage 4 — Verify and commit

Follow `docs/verify-commit-tail.md` verbatim: `python3 scripts/check_all.py` must print
"All invariants hold. ✓" before committing; stage only `matches.csv` and any deck files
whose `#: arena:` header you added; use this session's own trailer lines; no model ID in
the commit; do not open a PR unless asked.
