# Shared verify + commit tail

The standardized ending for **every** skill that writes to the repo — currently
`/add-deck`, `/add-wishlist`, `/apply-changes`, `/draft-deck`, `/ingest`,
`/log-matches`, `/pile-analysis`, `/refresh`, `/roster-review` (which writes deck
files whenever `deck.py sync --apply` runs — added BS8-25), and any future
data-editing skill.
Encoded once here so the skills can't drift on the discipline.

That list used to read "`add-cards`, `apply-changes`, and any future
data-editing skill", and both halves were wrong in the direction that hides the
gap. `/add-cards` writes nothing at all (it proposes; `/apply-changes` applies),
while `/add-deck` carried its own one-line commit instruction and `/ingest` and
`/refresh` — which rewrite `card-library.csv` and every derived file — had no
commit step whatsoever. "Any future data-editing skill" reads as coverage and
was doing no work: a skill only follows this file if it SAYS so. **Add the new
skill to this list and cite this file from it in the same change** — a name here
that no skill references is the same absent mechanism one layer over.

This is where the avoidable mistakes live — a model ID leaking into a commit, a
skipped integrity check, a stale flex note — so follow it verbatim.

## 1. Gate on integrity FIRST

**If the skill changed a DECK FILE or `card-library.csv`, run `make postedit`** —
build_dashboard.py, then `check_all.py`, then `check_roles.py --update-baseline`, in
that order and for that reason (G-69: acknowledging the baseline BEFORE the gate reads
it mutes the warning on the very run that earns it). It leaves the committed dashboard
current and the role radar honest. Otherwise run the gate alone:

`python3 scripts/check_all.py` must print **"All invariants hold. ✓"** (exit 0)
before anything is committed. A hard failure (INV-01…04, ranking sanity) blocks
the commit — fix it first. Soft warnings (wishlist target drift, unindexed
mechanics) do **not** block, but note any that are new.

`make postedit` was reachable from no skill at all until BS8-25 — `/apply-changes`
rebuilt nothing, `/draft-deck` called `build_dashboard.py` directly — so the committed
snapshot went stale until a soft warning noticed. `check_commands.py` now gates every
Makefile target the way it gates scripts and subcommands, which is what caught it.

## 2. Commit with the required trailer

Stage only the files the skill actually changed. Write a clear, specific message
(what changed and why), and end **every** commit with the two trailer lines the
**CURRENT session** supplies — its co-author line and its own session URL:

```
Co-Authored-By: <the co-author line this session was given> <noreply@anthropic.com>
Claude-Session: <this session's claude.ai/code URL>
```

**Take both values from the session you are running in — never copy a literal URL
out of this file.** This document used to hardcode one session's trailer and tell
you to paste it "verbatim", so every commit any skill produced carried a link to
an unrelated, long-finished session (broad-scan F-08). The trailer's whole purpose
is to make a commit traceable back to the conversation that produced it; a
copied-forward URL silently defeats that.

**Never** put the model identifier (the `claude-…` model ID) in the commit
message, code comments, deck files, or any other pushed artifact — it belongs in
chat only. (The co-author line's display name is not the model ID; use whatever
the session specifies.)

## 3. Push to the working branch

`git push -u origin <branch>` (the session's designated feature branch). On a
network error, retry up to 4× with exponential backoff (2s, 4s, 8s, 16s).

**If the branch's PR is already merged**, a merged PR is finished — do not stack
new commits on it. Restart the branch from the latest default branch, keeping the
same name, and push the follow-up there (per CLAUDE.md's Git rules):

```
git fetch origin main
git checkout -B <branch> origin/main
# re-apply the change, then push (a force-with-lease is fine when the branch
# holds only already-merged history)
```

If the branch already carries unmerged commits beyond the merged history, keep
them (rebase onto the new base) rather than discarding them.

## 4. Close what you closed in `.cycle/NEXT-SESSION.md`

If this work resolves something §0-current of `.cycle/NEXT-SESSION.md` names as open —
an UNRESOLVED section, a "what is NOT known", an item under "Where the session left
off" — **edit that file in the same commit.** Say it is closed, keep the reasoning and
any live residual, and record the measurement that proves it.

This is not tidiness. CLAUDE.md orders a fresh session to read that file FIRST and
declares it authoritative over everything below it, so an item left open there is not
merely unhelpful — it sends the next session to redo finished work with the handoff's
full authority behind it. It has already happened: the TRK/unreleased-printing section
was fixed by commit `e269b5e` in the same cycle that wrote the handoff, and stayed
marked "UNRESOLVED AND RECORDED NOWHERE ELSE — cheapest next step: paste one affected
deck into Arena" for a week, complete with a manual next action (broad-scan S1-01).

The project's standing lesson is that *a handoff nobody is told to read is invisible*.
The mirror is that **a handoff that IS read and is wrong is worse than one that is not
read**, because it is trusted. Nothing gates this — `check_docs` proves the `[G-nn]`
anchors resolve, not that a claim is still true — so it lives here, in the tail every
writing skill already runs.

## 5. Do not open a PR unless asked

Creating a pull request requires an explicit request from the user. Committing
and pushing to the working branch is the default end state.
