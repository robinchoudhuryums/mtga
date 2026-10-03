# Claude Code mods for this repo

Two Claude Code mods (plugins of function hooks) built 2026-10-03. They run inside a
Claude Code session opened at the repo root, and read the repo through its own CLI, so
they can never disagree with the tools.

| Mod | What it does |
|---|---|
| `deck-pane/` | `/deck <id>` opens a side pane for one deck: claimed tier vs metrics floor, interaction and card advantage (with their uncertainty), protection, board power, avg MV, early drops, colour sources, keepable %, the three weakest cast-on-curve cards, and buildability. It re-reads itself after any `deck.py swap/move/resolve/sync`, `make postedit`, git checkout/pull, or edit under `decks/`. Refresh button, hotkey `r`. |
| `pile-tracker/` | A band above the prompt naming every live `/pile-analysis` doc (`.cycle/*-analysis.md`) with its `**Status: …**` line. Rescans at session start and after every turn. **Hide** dismisses it for the session; `/piles` lists them all and shows it again. |

## Loading them

From the repo root, per session:

```
claude --plugin-dir tools/mods/deck-pane --plugin-dir tools/mods/pile-tracker
```

For sessions you cannot pass a flag to (the desktop app, an SDK host), list the same
absolute paths in `CLAUDE_CODE_PLUGIN_DIRS` (in the process environment or the `env`
block of `~/.claude/settings.json`). A `--plugin-dir` folder is watched, so saving a file
reloads the mod.

## Checking them

```
claude plugin validate tools/mods/deck-pane
claude plugin test tools/mods/deck-pane        # 4 tests
claude plugin validate tools/mods/pile-tracker
claude plugin test tools/mods/pile-tracker     # 3 tests
```

Once loaded, the engine lays its type declarations in each mod's `.claude-plugin/types/`
(generated, git-ignored) and `tsc -p tools/mods/<mod>` type-checks it.

## Coupling to know about

- `deck-pane` parses `deck.py quality --json`, plus the TEXT of `deck.py tier` and
  `deck.py consistency`. If that wording changes, the affected rows read `?` rather than a
  wrong number; `tests/parse.test.ts` pins the shapes it expects, so update it with them.
- `pile-tracker` reads the `**Status: …**` line the `/pile-analysis` skill writes. A doc
  without one shows "no status line".
