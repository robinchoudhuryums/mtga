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

`Player.log` is **overwritten on every launch**, so grab it before relaunching. Ask the
user to run this on the machine running Arena and paste the output:

```
# macOS
p=~/Library/Logs/"Wizards Of The Coast"/MTGA
# Windows (PowerShell): $p="$env:APPDATA\..\LocalLow\Wizards Of The Coast\MTGA"

grep -hE 'Match to .*MatchGameRoomStateChangedEvent|"finalMatchResult"|==> EventSetDeckV3' \
    "$p"/Player*.log
```

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

## Stage 2 — Report

```
python3 scripts/parse_matches.py --report
```

**Read this the way the tool prints it, not the way a percentage invites.** Below ~20
matches it refuses to show a rate at all, and above it the 95% Wilson interval is usually
still 30 points wide. State the interval whenever you quote a number.

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

For each unattributed Arena deck the report lists, ask the user which repo deck it is,
then add the header to that deck file — the name, the GUID, or both:

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
