---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented: Batch 6 follow-up. The ranked speed-up candidates were implemented
with BYTE-IDENTICAL outputs. Also: the 4 roster misfiles Batch 7 found were refiled with
`deck.py move` (committed separately).
Files modified: scripts/deck.py, scripts/check_dfc.py, tests/test_deck.py,
tests/test_check_dfc.py, dashboard.html (postedit rebuild)

CHANGES:
1 | scripts/deck.py | `classify_roles` memo: text → frozenset. Each call returns a NEW set.
  The cache resets when any table it reads (`_ROLE_COMPILED`, `_ROLE_COMPILED_MAP`,
  `_LOOT_RE`, `_REMINDER_RE`) is a different object, so a test that monkeypatches a table
  gets fresh answers (test_gates_fire does).
2 | scripts/deck.py | `rationale_staleness`: the SHORTHAND guard
  `any(other.startswith(disp + " ") for other in in_deck)` is now a set lookup. The set
  holds every `o[:i]` where `o[i] == " "`, which is exactly the same predicate. That
  generator was 188M steps and 143s of a 233s check_all profile.
3 | scripts/deck.py | `parse_deck_file` memo, keyed on the file's exact BYTES. A
  (mtime, size) key would not do: Linux timestamps tick at about 4ms and `move` rewrites
  at the same size. Each call gets its own meta dict and card list. The parse goes
  through `io.TextIOWrapper`, so newline handling and decode errors are identical to
  `open()`. This removes the 87k re-parses `discover_decks` caused.
4 | scripts/deck.py | `load_legalities` = a fresh dict over `_load_legalities_cached`,
  which is `_file_memo("POOL_CSV")`. It was re-read 122 times per dashboard build.
5 | scripts/check_dfc.py, tests/test_check_dfc.py | `_load_legalities_cached` is registered
  as the pool-index builder. check_dfc's AST scan found it under its new name, which is
  the gate working.
6 | tests/test_deck.py | `TestHotPathMemos`, 6 tests: a same-size rewrite is re-parsed;
  parse results are independent copies; CRLF reads like `open`; classify_roles returns a
  fresh set; the cache resets on a swapped table; load_legalities returns a fresh dict.
(`_power_seed` needed no change: its cost was classify_roles inside `wishlist._seed_power`.)

MEASURED (same tree, same data):

  | | before | after |
  |---|---|---|
  | check_all | 77s | 36s |
  | build_dashboard | 217s | 80s |
  | swap --apply (scratch) | 6.9s | 2.7s |
  | make postedit | ~305s | 118s |
  | full pytest | 345s | 181s |

IDENTITY CHECK, before vs after on the same tree:
  - check_all full output: byte-identical.
  - dashboard.html: identical apart from its `generated` timestamp.
  - suggest --limit 0 and cuts for decks 85/20/47/6, swap 85 dry run, tier 85
    --audit-rationale, legal 85 and suggest 85 --lands: all byte-identical.

TEST RESULTS: 2192 passed (exit 0). check_all OK, 5 soft.
REGRESSION RISKS:
- A caller that mutated a parse/classify result in place now mutates only its own copy.
  That was already the intended contract.
- Memory: the parse memo holds the bytes of every deck path ever parsed in a process
  (about 123 files, under 1MB), and the role memo holds about 16k entries. Both are
  bounded by the data.
INVARIANTS AT RISK: None. The four memos are read paths, and every write path is unchanged.
NET SCORE: 0 − 0 = 0 (performance only; no behaviour change, as verified above).

OPERATOR ACTIONS / DEPLOY:
None
Deploy: the Pages workflow rebuilds the dashboard on push to main (now about 80s instead
of 217s).

FOLLOW-ON ITEMS:
- `docs/systems-map.md` per-command costs are older snapshots (`preflight` "6.4s" dates
  from a ~6s check_all). Re-measure them in one pass rather than piecemeal.
- 35a still files Great Divide Guide and Bloom Tender (mana creatures) under `Lands (24)`.
  That reads as deliberate, so it was left alone.

DOCUMENTATION UPDATES NEEDED:
None. No documented behaviour changed. G-71's read-only rule is honoured by returning
fresh copies.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
