#!/usr/bin/env python3
"""Project integrity check — the deterministic gate for the card library.

Verifies the invariants that keep the interdependent files consistent (see the
Invariant Library in CLAUDE.md). This is the project's "Test Command": it exits
non-zero on any hard integrity break, so /broad-implement and CI can rely on it.

Checks (hard = fails the run):
  INV-01  card-library.csv passes validate.py (header, columns, quantities,
          no duplicate printings).                                    [hard]
  INV-02  every library Card Name has a row in card-mana.csv.          [hard]
  INV-03  the derived reference files exist (card-mana.csv, card-pool.csv,
          gallery.html).                                               [hard]
  INV-04  every deck file under decks/ parses with no bad lines.       [hard]
  (info)  deck buildability summary vs. the collection — not a hard
          invariant (CLAUDE.md's INV-05 is the Color(s)=identity rule). [info]

Usage:
    python3 scripts/check_all.py          # full check, exit 1 on hard failures
    python3 scripts/check_all.py --quiet  # one-line summary only (for hooks)
"""

import argparse
import csv
import os
import sys

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint
from validate import validate
import deck as deckmod

MANA_CSV = os.path.join(REPO_ROOT, "card-mana.csv")
POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")
GALLERY = os.path.join(REPO_ROOT, "gallery.html")


def check_mana_coverage():
    """INV-02: every library card name appears in card-mana.csv."""
    if not os.path.exists(MANA_CSV):
        return ["card-mana.csv missing (run build_mana.py)"], 0, 0
    have = set()
    with open(MANA_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            have.add((r.get("Card Name") or "").strip().lower())
    _, rows = load_rows(DEFAULT_CSV)
    names = {(r.get("Card Name") or "").strip().lower() for r in rows if (r.get("Card Name") or "").strip()}
    missing = sorted(n for n in names if n not in have)
    return [f"card-mana.csv missing {len(missing)} card(s): {', '.join(missing[:8])}"
            + ("…" if len(missing) > 8 else "")] if missing else [], len(names), len(missing)


# INV-03's SCHEMA half. Existence alone was never enough: a derived CSV rewritten with
# the library's 8-column header keeps its name and its Card Name column but loses
# everything that makes it useful, and every format filter / rotation flag / wildcard
# price silently degrades (audit F-02). These are the columns without which the file is
# no longer that file. Legalities/Released are deliberately NOT here — a pool built
# before those columns existed is a documented graceful-degradation case, so they warn.
_REQUIRED_COLUMNS = {
    "card-mana.csv": ["Card Name", "Mana Cost", "Mana Value", "Keywords"],
    "card-pool.csv": ["Card Name", "Type", "Card Text", "Color(s)", "Synergies",
                      "Set Code", "Rarity"],
}
_OPTIONAL_COLUMNS = {"card-pool.csv": ["Legalities", "Released", "Power", "Toughness"]}


def _header_of(path):
    """The CSV header row on disk, or None if unreadable/empty."""
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            return next(csv.reader(fh), None)
    except OSError:
        return None


def check_derived_files():
    """INV-03: derived reference files exist AND still carry their own columns.

    Returns (hard_errors, soft_warnings)."""
    errs, warns = [], []
    for path, name in [(MANA_CSV, "card-mana.csv"), (POOL_CSV, "card-pool.csv"),
                       (GALLERY, "gallery.html")]:
        if not os.path.exists(path):
            errs.append(f"{name} missing")
            continue
        required = _REQUIRED_COLUMNS.get(name)
        if not required:
            continue
        header = _header_of(path) or []
        missing = [c for c in required if c not in header]
        if missing:
            errs.append(f"{name} lost column(s) {missing} — it has {header}. A derived file "
                        f"rewritten with another file's header silently breaks every lookup "
                        f"built on it (audit F-02); restore its .bak or rebuild it "
                        f"({'build_mana.py' if 'mana' in name else 'build_pool.py --all'}).")
            continue
        absent = [c for c in _OPTIONAL_COLUMNS.get(name, []) if c not in header]
        if absent:
            warns.append(f"{name} predates column(s) {absent} — format/rotation checks "
                         f"degrade until you rebuild (build_pool.py --all).")
    return errs, warns


def check_decks():
    """INV-04 (deck parse + real printings) + buildability summary (info).

    INV-04 used to assert only that a line PARSES. It said nothing about whether the
    `(SET) COLLECTOR#` on that line names a printing that exists, so `1 Eaten Alive
    (ZZZ) 172` passed here, passed `legal`, passed `check` (reported OWNED — ownership
    joins on the NAME) and passed `preflight` READY. A deck file could be
    integrity-clean and un-importable at once. An unknown SET CODE is now hard; an
    unknown printing WITHIN a real set is soft, because the pool keys one printing per
    card by construction. See `deck.printing_problems` for why basics are exempt."""
    errs, warns, info = [], [], []
    decks = deckmod.discover_decks()
    _, _, by_name_qty = deckmod.load_collection()
    for d in decks:
        _, cards = deckmod.parse_deck_file(d["path"])
        if not cards:
            errs.append(f"deck {d['id']} ({os.path.relpath(d['path'], REPO_ROOT)}) has no parseable cards")
            continue
        # The line-syntax half of INV-04 (BS2-14). `parse_deck_file` discards a line
        # LINE_RE rejects with no record, so a malformed card line ("Lightning Bolt
        # (DMU) 137" with the quantity omitted, a BOM-prefixed paste) was silently
        # DELETED from every analysis — the deck graded as a 59-card list while the
        # file said 60, and this gate's own docstring claimed the check existed.
        for lineno, text in deckmod.malformed_deck_lines(d["path"]):
            errs.append(f"deck {d['id']}: line {lineno} is not a card line, `#:` header, "
                        f"comment or Arena marker — it is silently EXCLUDED from every "
                        f"analysis: {text[:60]!r}")
        # Total-need vs total-owned, through deck.py's one definition. This summary used
        # to compare each LINE against total owned, so it could report "buildable" for a
        # deck `deck.py check` calls short (BS4-13) — info-only here, but the gate's own
        # output disagreeing with the command it summarises is its own problem.
        missing, short = deckmod.deck_build_gap(cards, by_name_qty)
        status = "buildable" if (missing == 0 and short == 0) else \
            f"{missing} missing, {short} short"
        info.append(f"  deck {d['id']:>4}  {d['name'] or d['id']:<28} {status}")
        bad_set, unverified = deckmod.printing_problems(cards)
        for n, st, cn in bad_set:
            errs.append(f"deck {d['id']}: {n} — set code ({st}) does not exist in the pool or library; the line cannot import")
        for n, st, cn, kn in unverified:
            warns.append(
                f"deck {d['id']}: {n} ({st}) {cn} is not a printing we hold "
                f"(known: {', '.join(f'({a.upper()}) {b}' for a, b in kn)})")
    return errs, warns, info, len(decks)


def main():
    ap = argparse.ArgumentParser(description="Card-library integrity check.")
    ap.add_argument("--quiet", action="store_true", help="one-line summary only")
    args = ap.parse_args()

    hard = []

    # INV-01 — suppress validate's per-row chatter in quiet mode.
    if args.quiet:
        import contextlib
        with open(os.devnull, "w") as null, \
                contextlib.redirect_stdout(null), contextlib.redirect_stderr(null):
            inv01 = validate(DEFAULT_CSV)
    else:
        inv01 = validate(DEFAULT_CSV)  # prints its own errors/warnings
    if inv01 != 0:
        hard.append("card-library.csv failed validate.py")

    # INV-02
    mana_errs, ncards, nmiss = check_mana_coverage()
    hard += mana_errs

    # INV-03 — existence + schema (a derived file must keep its own columns).
    derived_errs, derived_warns = check_derived_files()
    hard += derived_errs

    # INV-04 / INV-05
    deck_errs, deck_warns, deck_info, ndecks = check_decks()
    hard += deck_errs

    # Ranking-model sanity — guards the Doctor-Doom-class scoring regression
    # (a real tribe silently read as "generic" after a threshold drifted).
    try:
        from check_rankings import check as check_rankings
        hard += check_rankings()
    except Exception as e:
        hard.append(f"ranking model sanity check errored: {e}")

    # Color-identity parsing sanity — guards the F1/F2 regression (a colorless card
    # read as red; a slash-gold failing the subset test) that mis-routed suggest.
    try:
        from check_colors import check as check_colors
        hard += check_colors()
    except Exception as e:
        hard.append(f"color parsing sanity check errored: {e}")

    # DFC ownership-join sanity — guards the A3/A4/F6 class: an ownership lookup that
    # bypasses lib.owned_qty (front-face fallback) and reads an owned double-faced card
    # as unowned. Behavioral anchor on the primitive + wrappers, plus a static scan for
    # the raw-access bypass shape.
    try:
        from check_dfc import check as check_dfc
        hard += check_dfc()
    except Exception as e:
        hard.append(f"DFC ownership-join sanity check errored: {e}")

    # Suggest/cuts gap-aware scoring sanity — keeps the diminishing-returns role credit
    # and the curve factor as BOUNDED modifiers (they can't silently reorder a tuned
    # deck's recommendations by overriding theme fit).
    try:
        from check_suggest import check as check_suggest
        hard += check_suggest()
    except Exception as e:
        hard.append(f"suggest scoring sanity check errored: {e}")

    # Engine-role classifier sanity — locks the enabler/payoff detection (#3) on
    # canonical cards so a regex edit can't silently break the imbalance flag.
    try:
        from check_engines import check as check_engines
        hard += check_engines()
    except Exception as e:
        hard.append(f"engine classifier sanity check errored: {e}")

    # Archetype-aware tier floor sanity (#4) — non-aggro decks grade exactly as before,
    # and the aggro clock only ever raises a band (never lowers or mis-grades one).
    try:
        from check_tier import check as check_tier
        hard += check_tier()
    except Exception as e:
        hard.append(f"tier floor sanity check errored: {e}")

    # DEAD-PATTERN gate — every card-text classifier pattern must match at least one
    # card in the Arena pool, and no pattern source may contain a Python tuple repr.
    # This project's signature bug is a regex that COMPILES FINE and matches nothing:
    # a bare {0,2} inside an f-string became the literal "(0, 2)" (46 decks lost their
    # interaction count), and `(?:owner|their) hand` required the text "owner hand"
    # while Magic writes "owner's hand" (every bounce spell scored zero roles). Unit
    # tests can't catch these — each pattern was tested against a string written to
    # match it — and a roster diff only catches them if you remember to run one.
    try:
        from check_patterns import check as check_patterns
        hard += check_patterns()
    except Exception as e:
        hard.append(f"dead-pattern check errored: {e}")

    # WORKFLOW-COVERAGE gate — every deck.py subcommand and runnable script must be
    # reachable from a skill, called by another module, or exempted with a reason. The
    # correctness gates above all verify a capability WORKS; none of them can see a
    # capability that works and is never reached. That is not hypothetical: CLAUDE.md
    # records `/tune-deck` sitting on the command set it shipped with while `consistency`,
    # `engines`, `shape`, `cuts`, `flex` and the needs-aware `suggest` were added around
    # it — every one correct, gated and documented, and unused. Same hand-kept-registry
    # shape as check_patterns' coverage list, so it gets the same treatment.
    try:
        from check_commands import check as check_commands
        hard += check_commands()
    except Exception as e:
        hard.append(f"workflow coverage check errored: {e}")

    # AGREEMENT gate — two functions answering the same question must give the same
    # answer. Every gate above verifies one model in isolation, which is structurally
    # blind to a divergence BETWEEN two correct models: `_weakest_cut` scored three
    # terms while `rank_cut_candidates` scored nine, and they named a different
    # most-cuttable card on 36 of 64 decks with all eleven gates green. Same shape as
    # the format filter `owned_role_fillers` skipped and its craft sibling applied.
    try:
        from check_agreement import check as check_agreement
        hard += check_agreement()
    except Exception as e:
        hard.append(f"model agreement check errored: {e}")

    # DOC-STRUCTURE gate — CLAUDE.md is the only file a fresh session loads
    # automatically, and it had grown to 2,219 lines because every operative rule
    # carried the incident that produced it. The rule now lives there and the evidence
    # in docs/gotchas.md, linked by anchor. That is a hand-kept cross-reference, and
    # this project's recurring lesson is that those rot — so the link is checked in
    # BOTH directions, the section names the vendored commands depend on are asserted,
    # and a per-bullet line cap stops the two files quietly re-fusing.
    try:
        from check_docs import check as check_docs
        hard += check_docs()
    except Exception as e:
        hard.append(f"doc structure check errored: {e}")

    # Soft: wishlist target drift — a target deck that can no longer cast its card
    # after a retune (e.g. deck 14 Mardu->Rakdos orphaned Neriv). Informational
    # only; never fails the build.
    soft = list(derived_warns)
    # Printing lines that name a real set but an unheld collector number. Soft
    # because the pool keys ONE printing per card, so a legitimate alternate art
    # lands here too — summarised, since 27 sit on the roster today.
    if deck_warns:
        # NAMED, not just counted: a bare "27" was delta-blind — a new bad printing
        # moved a standing number nobody reads, the exact "standing warning is a
        # decision nobody has made yet" shape K-01 documents (broad-scan batch 4).
        ex = "; ".join(w.split(" is not ")[0] for w in deck_warns[:3])
        soft.append(f"unverified printing(s): {len(deck_warns)} deck line(s) name a "
                    f"(SET) COLLECTOR# this repo does not hold — {ex}"
                    + ("; …" if len(deck_warns) > 3 else "")
                    + " (run `deck.py legal <id>` for the per-deck detail)")
    try:
        import wishlist as wl
        for _sev, name, msg in wl._audit_target_issues(color_only=True):
            soft.append(f"wishlist target drift: {name} — {msg}")
    except Exception as e:
        soft.append(f"wishlist target audit skipped ({e})")

    # Soft: NEW unindexed card mechanics (a new set's keyword not yet in the synergy
    # map). Baselined, so it stays quiet until something genuinely new appears.
    try:
        import check_keywords as ck
        for kw, ex, _sig in ck.check():
            soft.append(f"unindexed mechanic '{kw}' (e.g. {ex}) — add to tag_synergies "
                        "KEYWORD_THEMES/FLAVOR_KEYWORDS or run check_keywords.py --update-baseline")
        # Denylist overreach — a flavor keyword that may actually be a real mechanic.
        for kw, _n, note in ck.flavor_overreach():
            soft.append(f"FLAVOR_KEYWORDS overreach: '{kw}' — {note}")
        # Registry staleness — an entry in a hand-kept keyword list that no longer
        # matches any card. Suppresses nothing real, but a registry that looks
        # considered while covering nothing is the shape F-04 found in check_patterns'
        # coverage list. Soft: it breaks no invariant, it's a tidy-up prompt.
        for reg, kw, note in ck.stale_registry_entries():
            soft.append(f"stale {reg} entry '{kw}' — {note}")
    except Exception as e:
        soft.append(f"keyword radar skipped ({e})")

    # Soft: ZERO-ROLE cards — a card in a deck that `classify_roles` reads as having no
    # functional role at all. `_ROLE_PATTERNS` is a WHITELIST of phrasings, so a card
    # templated a way no pattern anticipates scores nothing, and the tier floor, the
    # `cuts` ranking and the quality guard all inherit that as fact. Eight such holes were
    # found in one 2026-08 session, every one by a human reading a card. Baselined, so it
    # stays quiet until a deck edit or a new set introduces one; soft because a genuinely
    # roleless card (a vanilla body, a pure combat trick) is a legitimate zero.
    try:
        import check_roles as cr
        rflags = cr.check()
        if rflags:
            ex = ", ".join(n for n, _t, _x in rflags[:4])
            soft.append(f"role coverage: {len(rflags)} deck card(s) score NO functional role and "
                        f"are not baselined (e.g. {ex}"
                        + (", …" if len(rflags) > 4 else "")
                        + ") — read the text, then fix the pattern in deck._ROLE_PATTERNS "
                          "or run check_roles.py --update-baseline")
        # BS-19: the baseline's pruning half. An entry a pattern fix un-zeroed stays
        # acknowledged forever, so a later regression re-zeroing that card would be
        # silent for good — surface stale entries instead of trusting someone to
        # diff role_baseline.txt.
        rstale = cr.stale_baseline_entries()
        if rstale:
            ex = ", ".join(n for n, _w in rstale[:4])
            soft.append(f"role baseline: {len(rstale)} STALE entr(ies) masking nothing "
                        f"(e.g. {ex}" + (", …" if len(rstale) > 4 else "")
                        + ") — review `check_roles.py`, then --update-baseline to prune")
    except Exception as e:
        soft.append(f"role coverage check skipped ({e})")

    # Soft: THEME coverage — owned cards whose text plays a theme they aren't tagged with
    # (the theme analog of role_coverage_flags); distorts every tag-based recommendation.
    # Summarized to one line so a batch of mis-tags doesn't flood the soft section.
    try:
        import check_themes as ct
        tflags = ct.flags()
        if tflags:
            ex = ", ".join(f"{n} ({t})" for n, t, _ in tflags[:4])
            soft.append(f"theme coverage: {len(tflags)} owned card(s) may be missing a synergy "
                        f"tag their text implies (e.g. {ex}"
                        + (", …" if len(tflags) > 4 else "")
                        + ") — run `check_themes.py`, then tag_synergies.py --merge")
    except Exception as e:
        soft.append(f"theme coverage check skipped ({e})")

    # Soft: STALE FLEX LINES — a `#~ -Out | +In` line whose -Out card already left the
    # deck. `swap --apply` retires only the lines its own swap invalidated, and the
    # rationale audit reads `#: tier:` / `#: archetype:` prose and never the flex block,
    # so these rot silently — five were sitting on the roster undetected when this check
    # was added. Advisory: a flex line is a human note, so this never edits or gates.
    try:
        flex_stale = []
        for d in deckmod.roster_decks():
            for cut, add, _why in deckmod.flex_staleness(d["path"]):
                flex_stale.append(f"deck {d['id']}: −{cut}" + (f" / +{add}" if add else ""))
        if flex_stale:
            soft.append(f"stale flex line(s): {len(flex_stale)} propose cutting a card the "
                        f"deck no longer runs — {'; '.join(flex_stale[:3])}"
                        + (" …" if len(flex_stale) > 3 else "")
                        + " (retarget or retire; see `deck.py flex <id>`)")
    except Exception as e:
        soft.append(f"stale-flex check skipped ({e})")

    # Soft: STALE CARD-NAME HEADERS — a `#: protect:` or `#: uncastable-ok:` entry naming
    # a card the deck does not run. Both headers are read by the tooling as instructions,
    # so a leftover name is a silent no-op, and `protect` additionally inflates a figure a
    # HUMAN reads (the zero-protection flag prints "names N build-around card(s)").
    #
    # Nothing could see this class. INV-04 validates deck LINES; the rationale audit reads
    # `#: tier:` / `#: archetype:` PROSE; a card-name list in a third header was checked by
    # nothing — the same "capability that is never reached" shape as the rationale sweep
    # above. Found by hand on deck 26b, and this sweep immediately turned up two more on
    # deck 56, whose Boros header protected two GREEN cards that live only in its Gruul
    # variant. Advisory: pruning a header is a human editorial call.
    try:
        hdr_stale = []
        for d in deckmod.roster_decks():
            for header, name in deckmod.header_card_staleness(d["path"]):
                hdr_stale.append(f"deck {d['id']}: `#: {header}:` names {name!r}")
        if hdr_stale:
            soft.append(f"stale card-name header(s): {len(hdr_stale)} name a card the deck "
                        f"no longer runs — {'; '.join(hdr_stale[:3])}"
                        + (" …" if len(hdr_stale) > 3 else "")
                        + " (prune the entry, or fix the name if it is a typo)")
    except Exception as e:
        soft.append(f"stale-header check skipped ({e})")

    # Soft: STALE TIER RATIONALE — a `#: tier:` argument citing a card the deck no
    # longer runs, or a figure that no longer matches the live quality vector.
    #
    # This is the check that EXISTED and never ran. `deck.py tier <id>
    # --audit-rationale` has always been able to find these, but only for one deck, on
    # demand, and CLAUDE.md's instruction to run it after every deck edit lived in prose
    # that nothing executed — so the sibling checks above (flex staleness, tier
    # mismatch) swept the roster every run while this one waited to be remembered.
    # Thirteen stale figures across ten decks accumulated behind that gap while every
    # gate stayed green, which is the same shape as this project's dead-regex bugs: a
    # check that cannot fire is not a check. Roster-wide and automatic now; the loaders
    # are memoized, so the sweep costs ~1s rather than the ~30s that made it look
    # unaffordable. Advisory, never gating — the prose is a human argument.
    try:
        rot = []
        for d in deckmod.roster_decks():
            cards, figs = deckmod.rationale_staleness(d)
            for name, _hdr in cards:
                rot.append(f"deck {d['id']}: cites {name!r}, not in the deck")
            for key, quoted, actual in figs:
                rot.append(f"deck {d['id']}: {key} {quoted} vs live {actual}")
        if rot:
            soft.append(f"stale tier rationale: {len(rot)} claim(s) the list no longer "
                        f"supports — {'; '.join(rot[:3])}"
                        + (" …" if len(rot) > 3 else "")
                        + " (see `deck.py tier <id> --audit-rationale`)")
    except Exception as e:
        soft.append(f"tier-rationale check skipped ({e})")

    # Soft: tier robustness — a deck whose claimed #: tier: sits ≥2 bands above the
    # tier its measurable quality vector supports (inflated or stale). Never gating —
    # tier is a human judgment, this only flags an indefensible letter to re-grade.
    try:
        for did, claimed, implied, msg in deckmod.tier_consistency_issues():
            soft.append(f"tier mismatch: deck {did} — {msg} "
                        "(re-grade from the CLAUDE.md rubric, or justify the bombs/meta in the rationale)")
    except Exception as e:
        soft.append(f"tier robustness check skipped ({e})")

    if args.quiet:
        state = "OK" if not hard else f"{len(hard)} ISSUE(S)"
        # Carry the crashed-radar promotion onto the hook path too (Batch C small
        # leaks): the full output distinguishes "a radar did not run" from an
        # ordinary warning precisely because a broken radar reads as quiet — and
        # --quiet, the mode documented as "for hooks" (the one nobody reads
        # closely), collapsed both into the same soft count.
        down = sum(1 for s in soft if " skipped (" in s)
        extra = f", {len(soft)} soft" if soft else ""
        if down:
            extra += f" (⚠ {down} RADAR(S) DID NOT RUN)"
        print(f"[card-library] {ncards} cards, {ndecks} decks — integrity: {state}{extra}")
        return 1 if hard else 0

    print(f"\n=== Integrity: {ncards} cards, {ndecks} decks ===")
    for line in deck_info:
        print(line)
    if soft:
        # A soft RADAR that crashed degrades to one "skipped" line forever — and a
        # radar that cannot run is a gate that never fires, visible only to someone
        # reading this section closely. Promote crash-skips above the ordinary
        # warnings with their own count, so a permanently-broken radar reads as a
        # problem, not as quiet (broad-scan batch 4; stateless on purpose — no
        # cross-run counter, just impossible to mistake for health).
        down = [s for s in soft if " skipped (" in s]
        rest = [s for s in soft if " skipped (" not in s]
        eprint("\nSOFT WARNINGS (not gating):")
        if down:
            eprint(f"  ⚠ {len(down)} RADAR(S) DID NOT RUN — the quiet sections they "
                   "cover are unverified, not healthy:")
            for s in down:
                eprint(f"    ⚠ {s}")
        for s in rest:
            eprint(f"  ~ {s}")
    if hard:
        eprint("\nHARD FAILURES:")
        for e in hard:
            eprint(f"  ✗ {e}")
        print(f"\n{len(hard)} hard failure(s).")
        return 1
    print("\nAll invariants hold. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
