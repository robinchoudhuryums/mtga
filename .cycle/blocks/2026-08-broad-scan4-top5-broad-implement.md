---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- BS5-01 | `deck.py similar` returned a different answer on every run (G-54 violation, live)
- BS5-10 | `gallery.html` light mode painted a hardcoded near-black bar track on a white panel
- BS5-02 / BS5-03 | Two dashboard controls were reachable by mouse only
- BS5-13 | `_file_memo`'s read-only premise was false — five call sites mutated the shared tables
- BS5-05 | A roster-wide craft-pick regression published an empty dashboard with a green build

Files modified: scripts/deck.py, scripts/build_gallery.py, scripts/build_dashboard.py,
tests/test_deck.py, tests/test_templates.py, gallery.html (rebuilt), dashboard.html (rebuilt)

CHANGES:

BS5-01 | scripts/deck.py | Three sites, one cause: a SET feeding a tie-able sort key.
  `_deck_central_weights` iterated `_central_themes()` — a set — so the weight vector's
  insertion order was hash-seed dependent, and every consumer that breaks a TIE on that
  order inherited it. Now built in sorted key order. `cmd_similar`'s shared-theme list
  gained the tag as a tie-break (`(-weight, t)`), and `_theme_cosine` sums over
  `sorted(shared)` so float-addition order can no longer jitter the value the row sort
  reads. The return TYPE of `_central_themes` is deliberately unchanged: two callers do
  `ctags & _central_themes(...)`, so a tuple would have been a TypeError.
  Verified: `similar 40` and `similar 1` are now byte-identical across six PYTHONHASHSEED
  values (previously five seeds gave five different outputs).

BS5-10 | scripts/build_gallery.py | Four new tokens, three declarations de-hardcoded.
  `--track` replaces the literal `#0f1115` on `.bar .track`; `--plate` / `--plate-ink` /
  `--plate-accent` replace the `rgba(10,11,14,.8x)` plates and their flipping ink on
  `.qty` / `.setcode`. The light block gains `--track` plus mid-tone `--W…--C`, because
  flipping the track without flipping the pastel mana colours would have traded one
  unreadable panel for another. `--plate*` deliberately does NOT flip — it sits on card
  ART, not on the page — and the comment says why so the next reader does not "fix" it.
  Dark mode is byte-identical except `.setcode`'s plate alpha (.80 -> .85), consolidated
  onto the one token.

BS5-02 / BS5-03 | scripts/build_dashboard.py | The triage table's Deck cell is an `<a>`
  with no href and the card finder's chips are bare `<span>`s; both had a click handler
  and nothing else. Both now route through the existing `a11y()` helper, so they inherit
  the same role/tabindex/Enter-Space contract as the other ~20 controls and the page's
  universal `:focus-visible` ring. The triage one is applied inside `onRowExtra`, not
  after `appendChild`: `sortableTable`'s internal `redraw()` rebuilds `<tbody>` on every
  sort click, so attributes applied once would be discarded by the first sort.

BS5-13 | scripts/deck.py | `_file_memo` hands every caller the same dict and its docstring
  rested the memo's safety on a scan asserting no caller mutates one. The scan had missed
  five sites in the same file: `fetch_missing_mana` / `fetch_missing_rarities` mutate the
  dict they are given, and cmd_stats / cmd_mana / cmd_consistency / _do_swap /
  cmd_wildcards were handing them the cached object. Those five now pass
  `dict(load_mana())` / `dict(load_rarities())` — the docstring's own prescription. The
  docstring itself was rewritten to state the contract, name the two mutating helpers, and
  point at the behavioural pin instead of repeating a claim about all callers.

BS5-05 | scripts/build_dashboard.py | `craft_rows` swallowed every failure into `[]`, and
  main()'s wholesale-failure scan read only the three `detail` text panels — so a
  roster-wide `suggest_scored` regression rendered every craft table empty, exited 0, and
  Pages published a page reading "nothing to craft". `craft_rows(d, problems)` now records
  why it could not compute; `collect()` carries the list in the payload as
  `_craft_problems`; main() applies the same majority threshold as the existing scan and a
  sub-threshold advisory below it. A `no-themes` deck is explicitly NOT counted — the gate
  must fire on a regression, not on data.

TEST RESULTS: passed. 1266 tests collected, full suite green (exit 0). `check_all.py`:
all invariants hold, ZERO soft warnings (the 7 blank-Card-Text lines are the K-11 vanilla
creatures, expected). 10 new tests added, each watched failing against the unfixed code:
the four BS5-13 pins fail with `assert not True` when scripts/deck.py is stashed, and the
BS5-01 order pin fails on the pre-fix body (`['mango','apple','zebra']` is not sorted).
NOTE: Stage 1 of the scan reported "1,264 passed" read off dot output rather than a
summary line; the real pre-change baseline was 1,256.

REGRESSION RISKS:
- BS5-10 changes a palette NOBODY HAS EVER RENDERED. The light-mode mana colours are
  chosen, not verified — see the operator check below. Dark mode is unchanged apart from
  a 0.05 alpha shift on the `.setcode` plate.
- BS5-01 alters `_theme_cosine`'s float summation ORDER, so a similarity value can differ
  in its last bits from the pre-fix run. That is the point (it is now reproducible), and
  the display is `{sim*100:.0f}%`, but a previously-recorded percentage could in principle
  land on the other side of a rounding boundary.
- BS5-13 adds a ~16.7k-entry shallow dict copy per invocation of five commands. Values are
  tuples/strings, so shallow is sufficient; cost is sub-millisecond against the ~300ms CSV
  parse the memo exists to avoid.
- `_craft_problems` is now serialized into the published `#data` island (empty on a healthy
  build). The page's JS reads only known keys.

INVARIANTS AT RISK: None. INV-01/02/04/05/06 were not touched — no CSV or deck file was
written. INV-03 was exercised and re-verified: gallery.html was rebuilt (2,186 cards, data
island present) and dashboard.html rebuilt (101 decks), and check_all passes both legs.
Deliberate bounded deviation from G-13: I ran `build_gallery.py --no-fetch` and
`build_dashboard.py` directly rather than `make refresh`, because only the two PRESENTATION
artifacts changed and neither the enrich -> build_pool -> build_mana -> tag_synergies chain
nor its ORDER is affected by any edit here. No upstream derived data was regenerated.

NET SCORE: 5 production fixes − 0 new failure modes = 5
(Honest sub-tally on "would it have fired this month": BS5-01 YES — `similar` is reached by
/draft-deck and roster review, and every run this month produced an arbitrary theme list.
The other four NO: the gallery light palette has never been rendered, the owner is a mouse
user, the memo leak needs the Flask editor across several decks in one session, and
suggest_scored did not regress. Four of five are latent defects fixed on the mechanism.)

OPERATOR ACTIONS / DEPLOY:
- Render gallery.html in LIGHT mode and confirm the Collection-overview panel: bar tracks
  must read as a light neutral (not black slabs), each colour bar must be visible against
  the track, and a card's ×N badge / set code must stay legible on their dark plate.
  This is the perceptual half of BS5-10 and it is the only part a file cannot prove.
  | BLOCKS DEPLOY: N
- Keyboard-walk the dashboard's Triage table and Card finder: Tab to a deck row's name and
  to a card-finder chip, confirm a visible focus ring, and confirm Enter and Space both
  filter the deck list. This is the acceptance test for BS5-02/BS5-03. | BLOCKS DEPLOY: N
Deploy: Presentation subsystem — `.github/workflows/pages.yml` rebuilds build_dashboard.py
and publishes to GitHub Pages automatically on every push to main. Data + local tooling
ship by commit/push (no build step). The committed dashboard.html and gallery.html
snapshots were rebuilt in this session, so no local `make dashboard` is outstanding.

(Not complete in production until blocking operator actions are done AND the deploy step is
confirmed. There are no BLOCKING actions here.)

FOLLOW-ON ITEMS:
- BS5-04 | Buildability is re-derived in three more places (`cmd_list`, `deck_quality_vector`,
  `build_dashboard.collect`) despite G-70 claiming one definition, two of them keyed on the
  raw display name while `deck_requirements` keys lowercase. Measured: zero live divergence
  across all 103 decks. Wants a `_agree_buildability` pair in check_agreement.py.
- BS5-11 | `build_mana.py`'s `data.update(fetch(todo))` merges front-face ALIAS keys over
  already-resolved `reuse` rows; `alias_front` guards within its own dict and cannot see
  `reuse`, so a new `X // Y` could overwrite a distinct real card `X`. Measured: 0
  genuinely-distinct front-name collisions in today's pool. G-63's own lesson says to fix
  the mechanism, not defer on the census.
- BS5-12 | `templates/collection.html` keys rows on `[name,set,cn].join('')` with no
  delimiter; every other printing key in the repo is a tuple. Measured: 0 collisions in
  2,186 rows.
- BS5-06 | The pool's tag fingerprint hashes all of `deck.py`, so the pool reads STALE after
  any deck.py edit — including this one. Consider hashing `repr(deck.ENGINE_THEMES)`.
- BS5-07 | `check_colors`' exemption is a substring test for "colorless" over the whole
  enclosing function, so a comment grants it. All four current sites are genuinely guarded.
- BS5-08 | `card.py` still prints the COMBINED mana value for split/Room cards (G-02
  residual 2); `load_mana` already corrects it, `card.py` reads the CSV directly.
- BS5-09 | `parse_matches.py --report <file>` silently ignores `--report`.
- `docs/tooling-improvement-plan.md` is historical, referenced from nowhere, and reads like
  a live plan.

DOCUMENTATION UPDATES NEEDED:
- CLAUDE.md Common Gotchas: G-54 should record that its first live violation was
  `deck.py similar` and that the fix is a total-order KEY, not a changed return type
  (the set is load-bearing for two `&` callers).
- CLAUDE.md: a new rule for the BS5-13 class — a memoized shared table plus a helper that
  mutates its argument. The general form is "a claim about all callers is only as good as
  the last person who added one; pin the property, not the scan."
- CLAUDE.md / Regression Scenario 7: a rule that a control created in JS is a control only
  if it goes through `a11y()`, and that `tests/test_templates.py` pins `templates/` plus
  NAMED dashboard controls only — the generated pages are where BS5-02/03/10 all lived.
- Regression Scenario 5 or a new one should carry the gallery light-mode check above.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
