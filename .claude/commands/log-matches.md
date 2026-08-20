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
`matchId`. Run once on the Mac running Arena:

```sh
mkdir -p ~/mtga-logs && cat > ~/mtga-logs/snapshot.sh <<'EOF'
#!/bin/sh
p="$HOME/Library/Logs/Wizards Of The Coast/MTGA"
d="$HOME/mtga-logs"
grep -hE 'Match to .*MatchGameRoomStateChangedEvent|"finalMatchResult"|==> EventSetDeckV3|==> DeckUpsertDeckV3' \
    "$p"/Player*.log > "$d/.capture" 2>/dev/null
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
Claude sessions) → a shell function in `~/.zshrc`, which needs nothing checked out:

```sh
mtga-matches() {
  local p="$HOME/Library/Logs/Wizards Of The Coast/MTGA"
  grep -hE 'Match to .*MatchGameRoomStateChangedEvent|"finalMatchResult"|==> EventSetDeckV3' \
      "$HOME/mtga-logs/arena.log" "$p"/Player*.log 2>/dev/null \
    | sed -E 's/\\"(MainDeck|Sideboard)\\":\[[^]]*\]/\\"\1\\":[]/g' \
    | pbcopy
  echo "copied $(pbpaste | wc -l | tr -d ' ') lines to the clipboard"
}
```

`mtga-matches` then puts a pasteable export on the clipboard. It reads the rolling
archive first and the live `Player.log` second, so it covers history Arena has already
overwritten.

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

Do not ask for the whole log — it is tens of MB of game-state spam. The grep is the ask.

**Privacy:** the parser deliberately stores no `userId` and no `playerName`. If a raw
paste lands in the conversation it still contains both; don't echo them back, and don't
put them in a commit. Both players' avatar cosmetics are kept — that is a cosmetic, not
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

**Headers keep themselves current.** The same `--apply` also harvests the paste's deck
summaries and writes any new or renamed `#: arena:` header (with `.bak`s, conflicts
refused) *before* resolving the matches — so a deck renamed in the client re-maps in the
same run, and a paste of deck summaries with no matches in it still syncs headers rather
than erroring. `--map-decks` remains for the explicit roster-wide pass, but routine
ingests need no separate upkeep step.

**Deck NAMES are offered, never adopted silently.** Every run also reports any deck whose
repo `#: name:` differs from its Arena name, and `--sync-names` adopts them:

```
python3 scripts/parse_matches.py --sync-names          # reconcile from the stored headers
python3 scripts/parse_matches.py <file> --sync-names   # …or from a fresh paste
```

Four things make this safe enough to be automatic, and each one is load-bearing:

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

**The log cannot see four things that matter, and one whole platform.** Arena records the
deck you submitted and the raw outcome; it records nothing about the opponent's
archetype, whether you were on the play, or why you lost. And a **phone game never
reaches the desktop `Player.log` at all** — that log is written by the install that
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
log already has a row with a real deck, result and date — what it lacks is the four
things only you know. **Do not re-enter those through `--add`.** `--add` cannot dedupe
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
```

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
`+` add, `~` update, `=` unchanged, `!` conflict. **A conflict writes nothing** — two Arena
decks claiming one repo deck (an old copy left in the client) has to be resolved by hand,
because a header naming the wrong one of the two is worse than no header. Arena decks
whose names carry no repo deck number are listed, never forced.

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
