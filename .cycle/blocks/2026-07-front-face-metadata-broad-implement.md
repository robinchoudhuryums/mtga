---BROAD SCAN IMPLEMENTATION SUMMARY---
Findings implemented:
- P6 | `suggest` scoped candidates by color IDENTITY, so it could never surface a hybrid or colorless-cost card for any deck
- P7 | `_primary_type` classified any DFC whose BACK face is a land as a LAND
- P8 | `_printing_of` matched names exactly, so `swap --apply` wrote a DFC add as a bare line with no printing

Files modified:
- scripts/deck.py
- tests/test_deck.py
- decks/03-knights-edge/deck.txt
- decks/22-bloodbending/deck.txt
- decks/49-scaleforge/deck.txt
- decks/50-hoofprint/50a-strata.txt
- decks/51-unlock/deck.txt
- decks/51-unlock/51a-overdue.txt

CHANGES:
P6 | scripts/deck.py | `suggest_scored`'s candidate filter now reads castability from the
   PRINTED COST via `_candidate_castability` instead of `card_colors(r["Color(s)"])`. The
   surrounding code already derived the DECK's colors from costs "never color identity";
   the candidate half then compared on identity, so the two disagreed. Measured on the red
   pool: 55 Standard cards a red filter hides that mono-red can cast. Verified live —
   `suggest 49 --unowned` now surfaces Decadent Dragon and Ramos, Dragon Engine, neither of
   which it could ever show before.
P7 | scripts/deck.py | `_primary_type` reads the FRONT face (`split("//")[0]`). A substring
   scan over `Front // Back` returned the BACK face's type whenever it sorted earlier in
   `order`, which for `Land` is always, so ~35 `"Land" in _primary_type(...)` guards skipped
   the card: out of the curve, uncounted as a creature, and ADDED to the land total. 81 pool
   cards share the shape; four decks were live. Land counts corrected: deck 49 26 -> 25,
   deck 51 25 -> 24, deck 51a 25 -> 24.
P8 | scripts/deck.py | `_printing_of` now also matches a DFC by its FRONT face and returns
   `(display_name, set, collector)` rather than `(set, collector)`. `_do_swap` uses the
   canonical display name, so the written line is the real card name and not the shorthand
   the caller typed. Previously `swap 49 --add "Runescale Stormbrood" --apply` wrote
   `1 Runescale Stormbrood` — parses, passes INV-04, passes `legal`, fails an Arena import.

DOC CORRECTIONS FORCED BY P7 (the fix moved real numbers, so the prose had to follow):
- deck 3 avg MV 3.46 -> 3.44; deck 49 4.18 -> 4.17; deck 50a 3.76 -> 3.79; deck 51 4.06 -> 4.03
- deck 22 card advantage 10 -> 11 (The Everflowing Well's draw now counts)
- decks 51 / 51a: the recorded manabase was WRONG, not just stale. Both claimed 25 lands and
  keepable 86.0%; both actually run 24 lands at keepable 84.4%, which `consistency` flags as
  low. Deck 51's tier block described the manabase as "flawless" on the strength of that
  figure — the on-curve half of the claim survives (every coloured card >=90%), the keepable
  half does not, and the block now says so. 51a's note that a 25th land settled the question
  is re-opened: the reading that closed it was the artifact.

TEST RESULTS: 755 passed (was 744; +11 across TestPrimaryTypeFrontFace and
TestPrintingOfDFC). `check_all.py` — all invariants hold, and the soft stale-rationale
warning that the fix raised is now clear on all five decks. check_suggest OK,
check_agreement OK, check_patterns OK (145 patterns live), check_dfc OK, check_colors OK,
check_rankings OK. `deck.py --help` and `suggest --help` clean (G-55).

REGRESSION RISKS:
- P7 touches a primitive with ~35 call sites in deck.py plus build_dashboard.py. The change
  is strictly narrowing (it can only stop reporting a type that came from the back face), and
  every affected card is one where the old answer was wrong. The risk that remains is the
  opposite direction: a card whose front is a land and back is not (Jidoor) must still read
  Land — pinned by `test_a_real_land_front_is_still_a_land`.
- P7 changed published numbers in five decks. All corrected in the same commit; the
  stale-rationale sweep is the check and it is clean.
- P6 can only WIDEN what `suggest` shows. A card it now surfaces that the deck genuinely
  cannot cast would be a new failure mode; `_candidate_castability` is shared with
  `_castability_lint`, and `check_suggest`'s on-colour anchor still passes.
- P8 changed `_printing_of`'s return arity from 2 to 3. Only one caller exists
  (`_do_swap`), updated in the same edit; grep confirms no other reference.

INVARIANTS AT RISK: None. INV-04 is strengthened rather than threatened — P8 makes the
written line MORE complete than before. No writer was touched; the deck edits are prose and
figure corrections only.

NET SCORE: 3 production fixes − 0 new failure modes = 3
(a) Fired this month? P6 YES — it is why deck 49 was told its curve could not be fixed.
    P7 YES — it produced a wrong land count and keepable figure in four decks, one of
    which ("flawless manabase") was quoted as an argument in a tier grade. P8 YES — it
    wrote two unimportable lines into deck 49 this session. (b) New failure modes: none
    identified; all three changes are narrowing or additive with shared helpers.

OPERATOR ACTIONS / DEPLOY:
- None | BLOCKS DEPLOY: N
Deploy: Data + local tooling ship by commit/push. `build_dashboard.py` consumes
`_primary_type`, so the next Pages build will pick up the corrected land/type counts
automatically; no template change was made.

FOLLOW-ON ITEMS:
- `card-mana.csv` stores only the FRONT cost of a MODAL double-faced card (Bruce Banner
  reads `{U}`; Scryfall reports `layout: modal_dfc` with a real cost on both faces). Carried
  over from the previous block, still unfixed. `build_mana.py` is the fix site, and the 432
  two-faced rows holding one cost need splitting into transform (correct) vs modal (loss).
- `build_gallery.py` has its OWN `_primary_type` at line 217 with the same substring bug. Out
  of scope here; it affects the gallery's type breakdown, not any analysis or deck grading.
- Deck 51 and 51a now read keepable 84.4% with `consistency` flagging it low. Whether to add
  a 25th land is a real open question in both, newly re-opened by this fix.

DOCUMENTATION UPDATES NEEDED:
- A gotcha for the front-face-vs-metadata class would be justified: G-02 covers COST, and
  this session found the same split on TYPE (P7), on NAME (P8) and on COLOR (P6/G-58). Not
  written — it wants a name and a home, and that is a judgement call for the owner.
- README's `suggest` description says it "scopes by CASTABLE COLORS, not identity", which was
  aspirational before P6 and is true now; no edit needed, but worth knowing it was a claim
  the code did not honour.
---END BROAD SCAN IMPLEMENTATION SUMMARY---
