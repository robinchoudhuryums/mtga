---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS-01 — `suggest --interaction` / `--ramp` filtered candidates by color IDENTITY, not printed cost (the G-58 bug re-introduced in the needs model — the designated fix path per G-38)
- BS-02 — `card.py`: a library SUBSTRING match shadowed an exact pool match; the queried card vanished from output entirely (`card.py "Mimic"` showed Gogo, Master of Mimicry)
- BS-05 — `swap --apply` could write a second line for a card already in the deck under its other DFC spelling (exact-name bump match vs `_printing_of`-canonicalized add)
- BS-06 — `legality_report`'s copy limit and Brawl commander-presence check keyed on the exact line name, not `_ms_key`, so a count split across two DFC spellings passed the 4-copy limit
- BS-07 — `sync --apply` folded a pasted export's Sideboard into the stored maindeck (`verify`, the read half, warned; the write half didn't even detect it)

Files modified: scripts/deck.py, scripts/card.py

CHANGES:
BS-01 | scripts/deck.py | `suggest_mana` and `suggest_interaction` now filter candidates through `_candidate_castability` (printed cost, front-face mana fallback), the exact filter `suggest_scored` uses; `suggest_interaction` gains a (memoized) `load_mana()` call. Measured impact at scan time: 34 Standard interaction cards + 25 mana sources un-hidden from mono-color decks (Bullseye, Death Dealer `{2}{B/R}`; Haunted Screen `{3}`; Ugin `{8}`). Verified live on deck 52: Ugin / Mox Jasper / The Irencrag now surface.
BS-02 | scripts/card.py | New `_exact()` + `_resolve()`: exactness now outranks source (library still wins between two EXACT hits, matching `load_card_data` precedence); substring matches ranked across the MERGED lib+pool set, so the "Others" list stops dropping pool matches. Second instance found during the fix: the field-resolution step also used `_find` (substring fallback), so "Mimic"'s fields resolved from Gogo's library row — now exact-only via `_exact`.
BS-05 | scripts/deck.py | `_cards_after_swap` and `_swap_edit_lines` bump-match the add on `_ms_key` (front face), keeping the existing line's spelling. The self-swap guard in `_do_swap` now canonicalizes the add FIRST (hoisted `_printing_of`) and compares `_ms_key(cut) == _ms_key(add)` — the two-spelling self-swap previously passed the guard and the raw-line edit's cut-rebuild overwrote its own bump (the audit-F2 corruption from a second direction). Verified: `swap 43 --cut "King T'Challa // …" --add "King T'Challa"` now rejects as same-card.
BS-06 | scripts/deck.py | `legality_report` counts/order/disp key on `_ms_key`; commander presence too. `leg`/`carddata` lookups already alias the front face, so downstream lookups unchanged; the report returns only aggregates, so no caller sees the key change. Verified: 4 `Bruce Banner` + 1 `Bruce Banner // The Incredible Hulk` now flags "5 copies (max 4)"; a front-named `#: commander:` against a full-name deck line stops emitting the spurious "isn't listed" note.
BS-07 | scripts/deck.py | New `strip_boards()` beside `split_paste`: per pasted block, Sideboard/Maybeboard card lines are dropped from `sync`'s comparison and write, with a visible "(block N: ignoring K sideboard/maybeboard card(s))" note. Commander/Companion sections are KEPT (a stored Brawl deck lists its commander among the 100). Verified: deck 39's export + a 3-card sideboard reads "in sync" (previously "drifted: 3 added", and --apply would have written them into the 60).

TEST RESULTS: passed — `check_all` all invariants hold (same 2 pre-existing soft warnings: 27 unverified printings; 4 stale tier-rationale claims in decks 40/49); full pytest 861/861 in 35.7s; Regression Scenario 2 walked on the modified surfaces (`--help`, `legal`, `check`, `audit`, `swap` preview both real and error paths, `suggest --needs/--ramp/--interaction`, `sync` dry-run, `card.py` exact/substring/DFC/multi-printing/no-match).

REGRESSION RISKS:
- BS-01 widens strictly (identity ⊆ deck-colors implies cost-castable, so no previously-shown pick disappears); a pool card ABSENT from card-mana.csv is now admitted where identity used to exclude it — the same deliberate tradeoff `suggest_scored` made, and mana coverage of the pool is full.
- BS-05/BS-06 G-63 shadow caveat: a REAL card named exactly like a distinct DFC's front face, in the same deck, would false-merge (a loud false over-limit flag / false same-card rejection). Zero such collisions exist in the pool or library today; the failure direction is loud, vs. the silent under-count it replaces.
- BS-07 is a visible behavior change: a paste whose sideboard the user WANTED written into a maindeck now requires removing the `Sideboard` heading (the per-block note says so).

INVARIANTS AT RISK: None — no CSV write path touched; deck-file writes still route through `_safe_write_lines` (unchanged); INV-01…06 unaffected; `check_all` green post-change.

NET SCORE: 3 production fixes (BS-01, BS-02, BS-07 all reachable in a normal month of tuning/verifying; BS-05/BS-06 are latent hardening of the swap/legal seam) − 0 new failure modes = +3

OPERATOR ACTIONS / DEPLOY:
None
Deploy: N/A — Data + local tooling ship by commit/push; the dashboard redeploys via pages.yml on merge to main (no modified file feeds its build differently).

FOLLOW-ON ITEMS:
- The scan's remaining findings, unimplemented by scope: BS-03 (sheets_sync pull shrink guard), BS-04 (check_patterns perimeter), BS-08 (deck-editor JS front-face buildability), BS-09 (app.py 404 XSS — a one-line html.escape), BS-10 (`--color` substring filter in query/pool/wishlist), BS-11 (plural-blind tribes payoff scan), BS-12 (load_keywords front-face alias), and the Low tail — see the broad-scan report in this session.
- The /broad-implement scope string ended with a dangling "BS-" fragment (truncated). If a sixth finding was intended, it was not implemented — re-run /broad-implement with the ID.
- Noticed, not fixed (out of scope): `deck_needs` derives an undeclared deck's colors from IDENTITY (`m["colors"]`) where `suggest_scored` derives from costs — the same sibling-drift family as suggest_lands (scan Low finding F10a); moot for decks with a `#: colors:` header, which is all current roster decks.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md G-38/G-22 area: can now state the needs recommenders (`--ramp`/`--interaction`) read printed cost like `suggest` proper — they were the undocumented exception.
- docs/gotchas.md: the G-63 long form can add BS-05/BS-06 as the "exact-name JOIN surviving inside a copy counter / bump match" members of the class (the rule's own docstring in `_ms_key` predicted the shape); the G-58 long form can record the needs-model re-introduction.
- CLAUDE.md's check_colors description ("a static AST scan fails the build if any script re-implements the naive idiom") overpromises — a substring re-implementation passes (BS-10/BS-18); worth a caveat when BS-10/18 land.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
