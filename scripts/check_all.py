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
    """INV-04 (deck parse) + buildability summary (info, not a hard invariant)."""
    errs, info = [], []
    decks = deckmod.discover_decks()
    _, _, by_name_qty = deckmod.load_collection()
    for d in decks:
        _, cards = deckmod.parse_deck_file(d["path"])
        if not cards:
            errs.append(f"deck {d['id']} ({os.path.relpath(d['path'], REPO_ROOT)}) has no parseable cards")
            continue
        missing = short = 0
        for q, n, s, c in cards:
            have, found = deckmod.owned(by_name_qty, n)
            if not found:
                missing += 1
            elif have < q:
                short += 1
        status = "buildable" if (missing == 0 and short == 0) else \
            f"{missing} missing, {short} short"
        info.append(f"  deck {d['id']:>4}  {d['name'] or d['id']:<28} {status}")
    return errs, info, len(decks)


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
    deck_errs, deck_info, ndecks = check_decks()
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

    # Soft: wishlist target drift — a target deck that can no longer cast its card
    # after a retune (e.g. deck 14 Mardu->Rakdos orphaned Neriv). Informational
    # only; never fails the build.
    soft = list(derived_warns)
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
        extra = f", {len(soft)} soft" if soft else ""
        print(f"[card-library] {ncards} cards, {ndecks} decks — integrity: {state}{extra}")
        return 1 if hard else 0

    print(f"\n=== Integrity: {ncards} cards, {ndecks} decks ===")
    for line in deck_info:
        print(line)
    if soft:
        eprint("\nSOFT WARNINGS (not gating):")
        for s in soft:
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
