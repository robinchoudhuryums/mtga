# Match digest — build plan (TEMPORARY working doc)

**Status: PLANNED, GATED ON STEP 0.** Nothing is built yet. Delete this file once the
build lands and the findings are in CLAUDE.md G-74 / `docs/gotchas.md` — a finished plan
left in place reads as live (the `docs/tooling-improvement-plan.md` lesson).

**Goal.** Record *why* games were lost without the owner having to remember. Arena's
`Player.log` (with Detailed Logs on) streams the whole game state — who went first,
mulligans, land drops, the opponent's revealed cards, turns, life. The current extraction
keeps only three line shapes, which is why `On Play` / `Opponent Archetype` /
`Loss Reason` are blank on all 186 rows and why G-74 says the log "cannot see" them. That
premise is about the *filtered* lines, not the log.

**Evidence the data exists (2026-09-25, not yet verified on the owner's client).**
17Lands' official client (`rconroy293/mtga-log-client`, last commit 2025-10-29) parses
`GREMessageType_GameStateMessage` for on-play, mulligans (both seats), turns, drawn cards
and `opponent_card_ids`, and adapted to a log-format change in April 2025. A tracker
built March 2026 (`Shalkith/MTG-Arena-Tracker`) reads the same messages. The documented
removal (update 2021.8.0.3855) took collection / inventory / draft-pick endpoints, not
game state. Two facts from the 17Lands source shape the design: a log ENTRY can span
several lines (so `grep` cannot extract it — the trimmer must be a program), and a
`LogBusinessEvents` game-end payload carries `StartingTeamId` / `WinningTeamId` /
`GameNumber` directly.

**Design principle — trim on the Mac, interpret in the repo.** The Mac-side script emits
only facts: numbers and Arena card ids. Names, colours, suggestions and every judgement
live in the repo, where they are tested and can change without the owner reinstalling
anything on the Mac.

## Decisions (owner, 2026-09-25)

1. **Opponent info:** NEW columns `Opp Colors` + `Opp Cards`; `Opponent Archetype` stays
   the owner's own label ("mono-red"), never auto-filled.
2. **Loss reasons:** a separate `Suggested Why` column plus a one-reply confirmation;
   a suggestion reaches `Loss Reason` only when the owner confirms it.
3. **Capture:** the trimmer runs inside `snapshot.sh` every 15 minutes, so a game is
   digested before an Arena relaunch wipes `Player.log`.

## Step 0 — confirm the data exists (owner, ~5 min) — THE GATE

Play one game, then BEFORE relaunching Arena, on the Mac:

1. `python3 --version` — decides the trimmer's language. macOS ships no Python by
   default; if absent, the trimmer is written as a JavaScript core run by the built-in
   `osascript -l JavaScript` (and by Node in CI), with nothing to install.
2. The values-free structure sampler (prints field NAMES, types and message-type counts —
   never values, names or ids; tested on a synthetic multi-line log, parses as Python 3.8):

```sh
python3 - <<'EOF'
import json, os, re, sys, collections
d = os.path.expanduser("~/Library/Logs/Wizards Of The Coast/MTGA")
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(d, "Player.log")
START = re.compile(r"^\[(UnityCrossThreadLogger|Client GRE)\]")
def shape(v, depth=0):
    if isinstance(v, dict):
        return {k: shape(x, depth + 1) for k, x in sorted(v.items())} if depth < 6 else "{…}"
    if isinstance(v, list):
        return [shape(v[0], depth + 1)] if v else []
    if isinstance(v, str) and v[:1] in "{[":
        try: return shape(json.loads(v), depth)
        except ValueError: pass
    return type(v).__name__
def merge(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return {k: merge(a.get(k), b.get(k)) if k in a and k in b else a.get(k, b.get(k))
                for k in sorted(set(a) | set(b))}
    if isinstance(a, list) and isinstance(b, list) and a and b:
        return [merge(a[0], b[0])]
    return a if a not in (None, []) else b
entries, buf = [], []
with open(path, encoding="utf-8", errors="replace") as fh:
    for ln in fh:
        if START.match(ln) and buf:
            entries.append(buf); buf = []
        buf.append(ln)
if buf: entries.append(buf)
kinds, skel, multi = collections.Counter(), {}, 0
for e in entries:
    text = "".join(e)
    i = text.find("{")
    if i < 0: continue
    try: blob = json.loads(text[i:])
    except ValueError: continue
    if len(e) > 1: multi += 1
    for m in (blob.get("greToClientEvent") or {}).get("greToClientMessages", []):
        kinds[m.get("type")] += 1
        skel[m.get("type")] = merge(skel.get(m.get("type")), shape(m))
    for key in ("clientToMatchServiceMessageType", "payloadObject"):
        if key in blob:
            kinds["client:" + str(blob.get(key) if key != "payloadObject" else "payload")] += 1
    if "WinningTeamId" in text or "StartingTeamId" in text:
        skel["GAME_END_EVENT"] = merge(skel.get("GAME_END_EVENT"), shape(blob))
print("entries:", len(entries), " JSON entries spanning >1 line:", multi,
      " size MB:", round(os.path.getsize(path) / 1e6, 1))
for k, n in kinds.most_common(): print(f"  {n:6}  {k}")
for k in ("GREMessageType_GameStateMessage", "GREMessageType_ConnectResp",
          "GREMessageType_MulliganReq", "GAME_END_EVENT"):
    print(f"\n== {k}\n" + json.dumps(skel.get(k), indent=1)[:6000])
EOF
```

   Without Python, the fallback is the counting command (counts only):

```sh
p="$HOME/Library/Logs/Wizards Of The Coast/MTGA"
ls -lh "$p"/Player*.log
for k in greToClientEvent GREMessageType_GameStateMessage '"turnInfo"' '"activePlayer"' \
         '"mulliganCount"' '"gameObjects"' '"ownerSeatId"' ClientMessageType_MulliganResp \
         finalMatchResult; do
  printf '%-34s' "$k"; grep -c -- "$k" "$p/Player.log"
done
```

**Gate:** game-state counts of 0 while `finalMatchResult` ≥ 1 means the data is gone —
STOP, and fall back to jotting a few words per loss at paste time. Otherwise the
sampler's output becomes the fixture skeleton for Step 1.

## Step 1 — the trimmer (`scripts/mtga_digest.py`, runs on the Mac)

Reads `Player.log` and `Player-prev.log`, groups multi-line entries the way the 17Lands
client does, tracks each game, and emits ONE line per FINISHED game (~0.5 KB):

```
[MTGA-DIGEST]9/24/2026 9:31:07 PM: {"v":1,"match":"<matchId>","game":1,"won":false,
 "onPlay":false,"mull":1,"oppMull":0,"turns":9,"life":[0,14],"lands":[1,2,2,2,3,4],
 "seen":17,"seenLands":9,"opp":[<opponent grpIds>],"end":"Game"}
```

| Field | Source in the log |
|---|---|
| `onPlay` | game-end `StartingTeamId`; fallback: turn-1 `activePlayer` at the mulligan decision |
| `mull` / `oppMull` | `players[].mulliganCount` + `ClientMessageType_MulliganResp` decisions |
| `turns`, `life` | `turnInfo.turnNumber`, `players[].lifeTotal` at `GameStage_GameOver` |
| `lands` | my `CardType_Land` objects on my battlefield at the start of each of my turns |
| `seen` / `seenLands` | distinct card instances that entered my hand (opening hand + draws), and how many were lands |
| `opp` | distinct `grpId`s of opponent-owned card objects that became visible |
| `won`, `end` | game-end `WinningTeamId` vs my seat; the result reason |

Rules:
- **Private:** no userId, no screen name, no opponent identity. Numbers, match id and
  public card ids only. A test fails the build if either identity field appears.
- **Deterministic:** finished games only, lists sorted, so the same game yields the
  byte-identical line on every run — `snapshot.sh`'s `awk '!seen[$0]++'` dedupe then
  works unchanged (G-54: test under two `PYTHONHASHSEED`s).
- **Loud failure:** an entry that looks like game state but will not parse is counted,
  and a `[MTGA-DIGEST-WARN]` line reports it; the `v` field lets the repo say "your Mac
  copy is out of date, reinstall" instead of silently degrading (G-10's shape).
- **Date prefix mirrors Arena's** (`]M/D/YYYY h:mm:ss PM`), so `mtga-matches`' date
  filter and `parse_matches.filter_since` keep working with no change.
- **Cheap:** `snapshot.sh` skips the run when `Player.log`'s mtime has not moved.

Installation, one copy-paste command in the log-matches skill:
- `~/mtga-logs/mtga_digest.py` (the file itself);
- `snapshot.sh` gains one line — run the digester over `Player*.log` into `.capture`
  before the merge (decision 3);
- `mtga-matches` greps `MTGA-DIGEST` too, so digest lines ride in the normal paste.
  The launchd job runs with a bare PATH, so it calls the interpreter by absolute path
  and the installer prints which one it found.

## Step 2 — ingest (`scripts/parse_matches.py`)

- Parses `[MTGA-DIGEST]` lines; joins on Arena's matchId; fills fact columns on NEW and
  ALREADY-RECORDED rows. Never writes `Deck`, `Result` or `Date` — the "two writers, one
  fact" rule G-74 set for `--annotate`. Re-running is idempotent.
- **New columns, appended after `Note`** (the `_is_own_earlier_schema` guard already
  migrates an older header on the next write):

| Column | Example | Notes |
|---|---|---|
| `On Play` (existing) | `draw` | now filled from the digest — it is a logged fact; a disagreeing hand value is reported and the log wins |
| `Mulligans` | `1` | Bo3: per game, `0/1/0` |
| `Opp Mulligans` | `0` | |
| `Turns` | `9` | |
| `Final Life` | `0-14` | mine–theirs |
| `Lands By Turn` | `1-2-2-2-3-4` | my lands in play at each of my turns |
| `Lands Drawn` | `9/17` | lands / cards seen, opening hand included |
| `Opp Colors` | `UB` | colour identity of cards seen (decision 1) |
| `Opp Cards` | `Tinybones; Go for the Throat; …` | names, first-seen order, capped at 12 (decision 1) |
| `Suggested Why` | `screw` | heuristic, never merged unconfirmed (decision 2) |
| `Digest` | `v1` | provenance: which rows carry facts |

- **Card ids → names:** Scryfall's `/cards/arena/{id}` through `scripts/scryfall.py`,
  cached in a new `arena-ids.csv` (`Arena ID, Card Name, Color Identity`), fetched only
  for ids actually seen. Offline (`ScryfallUnavailable`): ids stay numeric in `Opp Cards`
  and resolve on the next run. Its own `atomic_write` + `DictWriter` writer, never
  `write_rows` (Key Design Decisions).
- **Backfill limit, stated:** the 186 existing rows stay blank. The rolling archive never
  kept game-state lines, so only games still in the current or previous `Player.log` at
  install time can be recovered.

## Step 3 — loss review and report

- **Suggestion rules, pre-registered before any data** (losses only; each printed with
  its evidence):
  - `keep` — I mulliganed to 5 or fewer;
  - `screw` — the game reached my 4th turn with 2 or fewer lands in play;
  - `flood` — lands were ≥ 60% of cards seen, in a game of 7+ turns.
  `misplay`, `outclassed`, `answer`, `removed` and `slow` stay the owner's call.
- **One-reply review (decision 2):** after an ingest the run prints each unconfirmed loss —
  `9/24 · deck 7 · L vs UB (Tinybones, Go for the Throat…) · on the draw · mull 1 ·
  2 lands by T4 → suggested: screw` — numbered. The owner replies "ok" or corrects only
  the wrong ones; the confirmed reasons go in through the existing `--annotate` writer.
  `parse_matches.py --review` reprints the unconfirmed losses on demand.
- **Measured, not trusted:** after 20 confirmed losses, report how often each rule
  matched the owner's call; retune or drop a rule that does not hold up. Record the
  numbers in `docs/gotchas.md`.
- **`--report` gains pooled sections:** play vs draw, winning after a mulligan, colours
  faced, confirmed-reason tally, and facts coverage ("digest on N of M matches"). The
  20-match floor still applies; nothing here feeds any deck score (G-56).

## Step 4 — docs, skill, gates

- `/log-matches`: Stage 0 install (trimmer + `snapshot.sh` + `mtga-matches`), Stage 1
  review step.
- CLAUDE.md G-74 rewritten (its "the log cannot see" premise becomes false for desktop
  games; phone games still never reach the Mac's log); `docs/gotchas.md` G-74 long form;
  C-02 / C-03 subsystem lists (`arena-ids.csv`, the new script); scenario 9 / C-12.
- `check_commands.py`: the new script must be reached by a real `python3 scripts/…` call
  — the Makefile `matches` target (repo-on-the-Arena-machine path) runs it.

## Tests

- Trimmer, on fixtures built from the Step 0 skeleton: multi-line entries, batched
  GameStateMessages, a mulligan to 5, on the draw, a mid-game concede, best-of-three,
  hidden opponent cards, an unfinished game (emits nothing), privacy, determinism,
  size bound per game.
- Ingest: new vs existing rows, idempotent re-run, schema migration, `Opp Cards` with
  Scryfall offline, `filter_since` on digest lines.
- Suggestions: each rule at, just under and just over its threshold; wins never get one.

## Effort

| Step | Size |
|---|---|
| 0 — owner check | 5 min |
| 1 — trimmer + tests | M, ~½ day |
| 2 — ingest, columns, card names | M, ~½ day |
| 3 — suggestions, review, report | S–M, ~3–4 h |
| 4 — docs, skill, gates | S, ~2 h |

## Out of scope for v1

Automatic `removed` detection (needs zone-transfer annotations attributed to the
opponent), colour screw (pips per turn), dashboard display of the facts, and phone
games — which never reach the Mac's log at all.

## Risks

- **Arena changes the format again** — the version field plus the warning line make it
  loud; the trimmer is small enough to re-issue.
- **The matchId in game state must equal `finalMatchResult`'s** — assumed from the
  17Lands client, verified on the first real digest before anything is written.
- **Suggestion thresholds are guesses** until measured against the owner's confirmations —
  hence the separate column and the 20-loss check.
