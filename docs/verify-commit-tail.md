# Shared verify + commit tail

The standardized ending for any skill that writes to the repo (`add-cards`,
`apply-changes`, and any future data-editing skill). Encoded once here so the
skills can't drift on the discipline. This is where the avoidable mistakes live —
a model ID leaking into a commit, a skipped integrity check, a stale flex note —
so follow it verbatim.

## 1. Gate on integrity FIRST

`python3 scripts/check_all.py` must print **"All invariants hold. ✓"** (exit 0)
before anything is committed. A hard failure (INV-01…04, ranking sanity) blocks
the commit — fix it first. Soft warnings (wishlist target drift, unindexed
mechanics) do **not** block, but note any that are new.

## 2. Commit with the required trailer

Stage only the files the skill actually changed. Write a clear, specific message
(what changed and why), and end **every** commit with exactly these two trailer
lines:

```
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_017XhPAKK9NnBZes71C5FJTB
```

**Never** put the model identifier (the `claude-…` model ID) in the commit
message, code comments, deck files, or any other pushed artifact — it belongs in
chat only.

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

## 4. Do not open a PR unless asked

Creating a pull request requires an explicit request from the user. Committing
and pushing to the working branch is the default end state.
