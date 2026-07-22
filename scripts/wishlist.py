#!/usr/bin/env python3
"""Craft-target / wishlist manager — unowned cards you want to craft or build around.

Separate from card-library.csv (what you OWN) and card-pool.csv (EVERY Arena
card): this is your curated shortlist of unowned cards worth crafting, slotting
into a deck, or building a new concept around — plus a per-set summary so you can
pick which packs to open with gems.

card-wishlist.csv columns:
    Card Name, Type, Card Text, Color(s), Synergies, Set Code, Collector #,
    Rarity, Target, Note

Rarity / Color(s) / Type / Card Text / Synergies are auto-filled from
card-pool.csv (with a Scryfall fallback for cards the pool lacks — e.g. newer
double-faced cards, stored under their full "Front // Back" name). `Target` and
`Note` are yours to annotate: a deck id it's for, "general", "concept: ...", or
why it caught your eye.

Usage:
    # add a batch pasted from MTG Arena ("<qty> <Name> (<SET>) <#>" lines)
    python3 scripts/wishlist.py --add batch.txt
    pbpaste | python3 scripts/wishlist.py --add -

    # browse / filter (case-insensitive substring, AND-ed)
    python3 scripts/wishlist.py                        # the whole wishlist
    python3 scripts/wishlist.py --set SOS --rarity rare,mythic
    python3 scripts/wishlist.py --color R --synergy firebending
    python3 scripts/wishlist.py --target 14 --note ""  # by annotation

    # pack optimization: how many wishlist cards each set would net you, by rarity
    python3 scripts/wishlist.py --by-set

    # cards you've since acquired (time to drop them from the wishlist)
    python3 scripts/wishlist.py --owned

Set a card's Target/Note by editing card-wishlist.csv directly (it's a plain CSV).
"""

import argparse
import csv
import os
import sys

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint, atomic_write, owned_qty, card_colors
from scryfall import ScryfallUnavailable

WISHLIST_CSV = os.path.join(REPO_ROOT, "card-wishlist.csv")
POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")

HEADER = ["Card Name", "Type", "Card Text", "Color(s)", "Synergies",
          "Set Code", "Collector #", "Rarity", "Target", "Note", "Power"]
RARITY_RANK = {"Mythic": 0, "Rare": 1, "Uncommon": 2, "Common": 3, "": 4, "?": 5}

# "<qty> <Name>" with optional "(SET)" + collector number — mirrors deck.py/import_arena.
import re
LINE_RE = re.compile(r"^\s*(\d+)\s*[xX]?\s+(.+?)\s*(?:\(([^)]+)\)\s*([^\s]+)?)?\s*$")
SECTIONS = {"deck", "sideboard", "commander", "companion", "maybeboard", "about"}


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def load_pool_index():
    """name_lower (full name AND front-face) -> pool row, for enrichment."""
    idx = {}
    if not os.path.exists(POOL_CSV):
        return idx
    with open(POOL_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            n = (r.get("Card Name") or "").strip().lower()
            if not n:
                continue
            idx.setdefault(n, r)
            idx.setdefault(n.split(" // ")[0], r)
    return idx


def owned_index():
    """name_lower (full AND front-face) -> total quantity owned across printings."""
    counts = {}
    try:
        _, rows = load_rows(DEFAULT_CSV)
    except FileNotFoundError:
        return counts
    for r in rows:
        n = (r.get("Card Name") or "").strip().lower()
        if not n:
            continue
        q = (r.get("Quantity Owned") or "").strip()
        c = int(q) if q.isdigit() else 0
        # Index under the full name AND the front-face name so a lookup by either
        # resolves. Use a SET so a single-faced card (where the two are identical)
        # is counted once, not twice — matching pool.py/deck.py's per-name sum
        # (audit F13). A DFC has two distinct keys, each mapping to its count.
        for k in {n, n.split(" // ")[0]}:
            counts[k] = counts.get(k, 0) + c
    return counts


def _owned_of(owned, name):
    """Copies owned for a wishlist card name — DFC-aware via the shared lib primitive."""
    return owned_qty(owned, name)


def load_wishlist():
    if not os.path.exists(WISHLIST_CSV):
        return []
    with open(WISHLIST_CSV, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_wishlist(rows):
    # Sort for stable, browsable output: set, then rarity (mythic first), then name.
    rows = sorted(rows, key=lambda r: (
        (r.get("Set Code") or "").upper(),
        RARITY_RANK.get((r.get("Rarity") or "").capitalize(), 9),
        (r.get("Card Name") or "").lower()))
    def _write(fh):
        w = csv.DictWriter(fh, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow({c: (r.get(c, "") or "") for c in HEADER})
    # Atomic + timestamped .bak: the hand-annotated Target/Note/Power columns are the
    # source of truth and had no backup before (audit F5).
    atomic_write(WISHLIST_CSV, _write)


# --------------------------------------------------------------------------- #
# Enrichment (pool first, Scryfall fallback)
# --------------------------------------------------------------------------- #
def _from_scryfall(name, set_code):
    """Best-effort single lookup for a card the pool lacks (e.g. a new DFC).

    Returns an enrichment dict on success, or None if Scryfall genuinely has no
    such card. Raises ScryfallUnavailable when Scryfall can't be reached (429 /
    5xx / timeout / bad body) — the caller MUST NOT treat that transient outage as
    a real 'not found' and silently store a blank row (audit F14). Imports the
    enrich/tag bits lazily so the common (pool-hit) path stays dependency-free."""
    import time
    import scryfall
    from enrich import color_shorthand, oracle_fields
    from tag_synergies import tags_for

    card, transient = None, False
    for params in ({"exact": name, "set": set_code.lower()} if set_code else {"exact": name},
                   {"fuzzy": name}):
        try:
            card = scryfall.named(params)
            break
        except scryfall.NotFound:
            continue  # this query didn't match — try the next (fuzzy) one
        except ScryfallUnavailable:
            transient = True  # outage; still try the remaining query in case it hits
            continue
        finally:
            time.sleep(0.1)
    if card is None:
        if transient:
            raise ScryfallUnavailable(f"could not reach Scryfall for {name!r}")
        return None
    type_line, text = oracle_fields(card)
    tags = tags_for({"Type": type_line, "Card Text": text}, card.get("keywords"))
    return {
        "Card Name": card.get("name", name),
        "Type": type_line, "Card Text": text,
        "Color(s)": color_shorthand(card),
        "Synergies": "; ".join(tags),
        "Rarity": (card.get("rarity") or "").capitalize(),
    }


def enrich(name, set_code, collector, pool):
    """Build a wishlist row for one card, using the canonical (full) name from the
    pool/Scryfall so double-faced cards join cleanly with the rest of the tooling.

    Returns (row, status) where status is:
      'pool'     – enriched from card-pool.csv,
      'scryfall' – enriched via a live Scryfall lookup,
      'miss'     – Scryfall has no such card; row is name-only (check spelling),
      'error'    – Scryfall was UNREACHABLE; row is name-only, but the blanks are
                   transient (rerun to fill them), NOT a confirmed miss (F14)."""
    p = pool.get(name.lower())
    if p:
        data = {"Card Name": p.get("Card Name", name), "Type": p.get("Type", ""),
                "Card Text": p.get("Card Text", ""), "Color(s)": p.get("Color(s)", ""),
                "Synergies": p.get("Synergies", ""), "Rarity": p.get("Rarity", "")}
        status = "pool"
    else:
        try:
            s = _from_scryfall(name, set_code)
        except ScryfallUnavailable as e:
            eprint(f"WARN:  Scryfall unreachable while enriching {name!r} ({e}); "
                   "added with name only — rerun the add when Scryfall is reachable.")
            s, status = None, "error"
        else:
            status = "scryfall" if s is not None else "miss"
            if s is None:
                eprint(f"WARN:  no Scryfall match for {name!r} — added with name only.")
        if s is None:
            data = {"Card Name": name, "Type": "", "Card Text": "", "Color(s)": "",
                    "Synergies": "", "Rarity": ""}
        else:
            data = s
    data["Set Code"] = set_code
    data["Collector #"] = collector
    data.setdefault("Target", "")
    data.setdefault("Note", "")
    return data, status


def cmd_add(path):
    text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    entries = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.lower() in SECTIONS or line.startswith("#") or line.startswith("//"):
            continue
        m = LINE_RE.match(line)
        if not m:
            eprint(f"WARN:  line {lineno}: could not parse {raw.strip()!r}")
            continue
        entries.append((m.group(2).strip(), (m.group(3) or "").strip(),
                        (m.group(4) or "").strip()))
    if not entries:
        eprint("No card lines found.")
        return 1

    pool = load_pool_index()
    owned = owned_index()
    existing = load_wishlist()

    def _key(r):
        return ((r.get("Card Name") or "").strip().lower(),
                (r.get("Set Code") or "").strip().lower(),
                (r.get("Collector #") or "").strip().lower())
    by_key = {_key(r): r for r in existing}
    seen = set(by_key)

    added, dupes, owned_hits, reenriched = 0, 0, [], 0
    unenriched_miss, unenriched_err = [], []
    new_rows = []
    for name, setc, cn in entries:
        row, status = enrich(name, setc, cn, pool)
        key = (row["Card Name"].strip().lower(), setc.lower(), cn.lower())
        if key in seen:
            prev = by_key.get(key)
            # F20: a row added NAME-ONLY during a Scryfall outage (blank Type+Text) is
            # otherwise stuck — a re-add hits the dedupe and never enriches. If this
            # pass DID enrich it, backfill the blanks in place instead of counting a dupe.
            if prev is not None and status in ("pool", "scryfall") \
                    and not (prev.get("Type") or "").strip() \
                    and not (prev.get("Card Text") or "").strip():
                for col in ("Type", "Card Text", "Color(s)", "Synergies", "Rarity"):
                    if row.get(col):
                        prev[col] = row[col]
                reenriched += 1
            else:
                dupes += 1
            continue
        if _owned_of(owned, row["Card Name"]) > 0:
            owned_hits.append(row["Card Name"])
        if status == "miss":
            unenriched_miss.append(row["Card Name"])
        elif status == "error":
            unenriched_err.append(row["Card Name"])
        existing.append(row)
        new_rows.append(row)
        seen.add(key)
        by_key[key] = row
        added += 1

    # Auto-seed a first-pass Power estimate for the newly-added rows so they don't
    # rank at 0.0 (which repeatedly buried real cards until hand-graded). It's an
    # ESTIMATE — the printed reminder says to hand-adjust bombs the heuristic misses.
    seeded = 0
    for row in new_rows:
        if not (row.get("Power") or "").strip():
            row["Power"] = str(_seed_power(row))
            seeded += 1

    write_wishlist(existing)
    print(f"Added {added} card(s) to the wishlist ({dupes} already listed). "
          f"Wishlist now has {len(existing)} card(s). Wrote {os.path.basename(WISHLIST_CSV)}.")
    if reenriched:
        print(f"Re-enriched {reenriched} previously name-only row(s) (added during an "
              "earlier Scryfall outage) now that their details resolved.")
    if seeded:
        print(f"Auto-seeded a heuristic Power estimate for {seeded} new card(s) — "
              "REVIEW and hand-adjust (the classifier undersells bombs); see `--rank`.")
    if owned_hits:
        print(f"NOTE: {len(owned_hits)} added card(s) you ALREADY OWN "
              f"(consider removing): {', '.join(owned_hits[:8])}"
              + ("…" if len(owned_hits) > 8 else ""))
    # A transient Scryfall outage must be called out distinctly from a genuine
    # not-found: these rows are name-only ONLY because Scryfall was down, and a
    # re-add (or build_pool.py) will fill them in — they aren't confirmed misses.
    if unenriched_err:
        print(f"WARN: {len(unenriched_err)} card(s) added NAME-ONLY because Scryfall "
              f"was unreachable — transient; re-add them (or run build_pool.py) to "
              f"enrich: {', '.join(unenriched_err[:8])}"
              + ("…" if len(unenriched_err) > 8 else ""))
    if unenriched_miss:
        print(f"NOTE: {len(unenriched_miss)} card(s) had no Scryfall match and were "
              f"added name-only (check spelling): {', '.join(unenriched_miss[:8])}"
              + ("…" if len(unenriched_miss) > 8 else ""))
    return 0


# --------------------------------------------------------------------------- #
# Query / summary
# --------------------------------------------------------------------------- #
def _match(card, args):
    def has(col, needle):
        return needle is None or needle.lower() in (card.get(col) or "").lower()
    if not (has("Card Name", args.name) and has("Type", args.type)
            and has("Card Text", args.text) and has("Color(s)", args.color)
            and has("Synergies", args.synergy) and has("Set Code", args.set)
            and has("Target", args.target) and has("Note", args.note)):
        return False
    if args.rarity:
        want = {x.strip().lower() for x in args.rarity.split(",")}
        if (card.get("Rarity") or "").lower() not in want:
            return False
    return True


def cmd_by_set(rows, owned):
    """Pack-optimization view: wishlist cards per set, broken down by rarity."""
    from collections import Counter
    per_set, per_setrar = Counter(), Counter()
    still = 0
    for c in rows:
        if _owned_of(owned, c.get("Card Name")) > 0:
            continue  # already acquired — don't count toward crafting/packs (DFC-aware)
        still += 1
        s = (c.get("Set Code") or "?").upper()
        per_set[s] += 1
        per_setrar[(s, (c.get("Rarity") or "?").capitalize())] += 1
    if not per_set:
        print("Wishlist is empty (or everything on it is already owned).")
        return 0
    print(f"Wishlist by set — {still} unowned card(s). Open packs of the top sets first.\n")
    print(f"  {'Set':5} {'Cards':>5}   Rarity breakdown")
    print("  " + "-" * 52)
    for s, n in sorted(per_set.items(), key=lambda kv: (-kv[1], kv[0])):
        rr = "  ".join(f"{per_setrar[(s, x)]} {x}"
                       for x in ("Mythic", "Rare", "Uncommon", "Common", "?")
                       if per_setrar[(s, x)])
        print(f"  {s:5} {n:>5}   {rr}")
    return 0


def _theme_model():
    """Build the deck theme model for target suggestion. Returns (fps, idf, spec_idf):

      fps  – [(deck_id, colors:set, central:set, tw_norm:dict)] — one entry per
             CORE archetype (variant builds / raw piles / pools are collapsed to
             their primary, and untuned placeholder lists are skipped) so breadth
             and idf count each real deck once, not once per alternate build.
      idf  – {theme: inverse-deck-frequency weight}. A theme CENTRAL to few decks
             (food, earthbend, firebending, Ninja, …) scores high; one central to
             most decks (etb, counters, tokens, mana, lifegain, …) scores ~0.

    idf-weighting is what stops broad decks from acting as catch-alls: a card that
    only overlaps a deck on generic themes gets a near-zero score and is flagged
    for review, while a specific-theme match (the real signal) ranks confidently.
    """
    import math
    import deck as dk
    meta = dk.load_card_meta()
    fps, df = [], {}
    for dd in dk.discover_decks():
        # One fingerprint per CORE archetype. Variants (alternate builds, raw
        # piles, pre-trim pools) share a core deck's themes, so counting them as
        # separate decks double-counts a theme's centrality (idf) and inflates a
        # card's cross-deck breadth (reuse) — e.g. a Bird card "reaching" 19, 19b
        # AND 19c. Skip variants (keep the primary) and skip any untuned list
        # (the 26-card example placeholder, an 83-card raw pile, an 86-card pool).
        if dd["variant"]:
            continue
        dm, cards = dk.parse_deck_file(dd["path"])
        if not (55 <= sum(q for q, _n, _s, _c in cards) <= 70):
            continue
        colors, ident, tw = dk._declared_colors(dm), set(), {}
        for q, n, s, c in cards:
            if n.lower() in dk.BASICS:
                continue
            m = meta.get(n.lower())
            if not m:
                continue
            ident |= m["colors"]
            for t in m["synergies"]:
                tw[t] = tw.get(t, 0) + q
        central = dk._central_themes(tw)
        mx = max(tw.values()) if tw else 1
        fps.append((dd["id"], colors or ident, central, {t: tw[t] / mx for t in central}))
        for t in central:
            df[t] = df.get(t, 0) + 1
    n = len(fps)
    # Clamp at 0: a theme central to (almost) every deck yields log(n/(1+c)) <= 0,
    # and a *negative* weight would drag down the score of a card that also matches
    # a genuinely specific theme. Floor it so a generic theme is worth zero signal,
    # never negative (audit F15). Values above 0 are unchanged, so ranking output
    # only moves for the pathological central-to-all case.
    idf = {t: max(0.0, math.log(n / (1 + c))) for t, c in df.items()}
    # "specific" cutoff as a fraction of the pool (self-adjusts to deck count):
    # a theme central to <= SPECIFIC_MAX_FRAC of decks clears it.
    spec_idf = math.log(n / (1 + SPECIFIC_MAX_FRAC * n)) if n else 0.0
    return fps, idf, spec_idf


# A theme counts as "specific" (real signal, not a catch-all) when it is central to
# only a small SHARE of decks. Expressed as a FRACTION of the deck pool so the cutoff
# self-adjusts to the deck count — an absolute idf constant silently mis-calibrates when
# decks are added/removed: collapsing variants (34 -> 25 decks) once pushed the 5-deck
# "Villain" tribe below a hard 1.5 cutoff, mislabeling Doctor Doom & other Villain
# payoffs as "generic". 0.25 => central to <= ~1/4 of decks (<= ~6 of 25) is signal.
SPECIFIC_MAX_FRAC = 0.25

# Evergreen keywords / generic role descriptors are rare across decks (so they'd
# score as "specific") but are INCIDENTAL to a card — a trample creature isn't
# thereby a fit for the one deck that happens to run trample. Excluded from the
# confidence signal so they don't manufacture false-confident matches; a strategic
# theme (food, earthbend, reanimator, Ninja, spellslinger, …) still has to carry it.
NON_SIGNAL_TAGS = {
    "flying", "trample", "menace", "deathtouch", "lifelink", "vigilance", "haste",
    "reach", "first strike", "double strike", "ward", "hexproof", "shroud",
    "prowess", "defender", "indestructible", "protection", "intimidate", "fear",
    "evasion", "combat", "aggro", "tempo", "pump", "defense", "resilience",
}


def cmd_suggest_targets(rows, write=False, overwrite=False):
    """Propose a Target per card via idf-weighted theme fit + a confidence flag.

    STRONG/ok picks share a SPECIFIC (rare) theme with the deck; `review` picks
    match only generic themes (or nothing) — those are the catch-all-prone cards a
    human should judge from card text. With --write, fills STRONG/ok picks into
    blank Targets (or all, with --overwrite); `review` cards are always left for you.
    """
    fps, idf, spec_idf = _theme_model()
    strong = ok = review = wrote = 0
    print(f"  {'Card':30} {'Conf':6} {'Target':9} Signal")
    print("  " + "-" * 84)
    for r in rows:
        ccols = card_colors(r.get("Color(s)"))
        ctags = {t.strip() for t in (r.get("Synergies") or "").split(";") if t.strip()}
        fits = []
        for did, dcols, central, twn in fps:
            if not ccols.issubset(dcols):
                continue
            shared = ctags & central
            if not shared:
                continue
            score = sum(idf.get(t, 0) * twn[t] for t in shared)
            specific = sorted((t for t in shared if idf.get(t, 0) >= spec_idf
                               and t.lower() not in NON_SIGNAL_TAGS),
                              key=lambda t: -idf[t])
            fits.append((round(score, 2), did, specific, sorted(shared)))
        fits.sort(reverse=True)

        proposal = None
        if not fits:
            conf, tgt, sig = "review", "?", "no central-theme fit — general/concept?"
        else:
            best = fits[0]
            alts = ",".join(d for _, d, _, _ in fits[1:3])
            if best[2]:  # shares a specific (rare) theme — real signal
                lead = len(fits) < 2 or best[0] >= fits[1][0] + 0.5
                conf = "STRONG" if (lead or best[0] >= 1.5) else "ok"
                tgt = proposal = best[1]
                sig = f"{'/'.join(best[2][:2])}  (score {best[0]}; alts {alts or '—'})"
            else:  # only generic-theme overlap — the catch-all zone
                conf, tgt = "review", best[1] + "?"
                sig = f"only generic: {','.join(best[3][:3])}  (alts {alts or '—'})"

        strong += conf == "STRONG"; ok += conf == "ok"; review += conf == "review"
        if write and proposal and (overwrite or not (r.get("Target") or "").strip()):
            r["Target"] = proposal
            wrote += 1
        print(f"  {r['Card Name'][:30]:30} {conf:6} {str(tgt):9} {sig[:52]}")

    print(f"\n  {strong} strong · {ok} ok · {review} review "
          "(review = generic/no theme match — judge these from card text).")
    if write:
        write_wishlist(rows)
        print(f"  Wrote {wrote} target(s) to {os.path.basename(WISHLIST_CSV)} "
              f"(review cards left blank/unchanged).")
    else:
        print("  Read-only. Re-run with --write to fill blank Targets with strong/ok picks.")
    return 0


_WC_RANK = {"Mythic": 3, "Rare": 2, "Uncommon": 1, "Common": 0}


def _deck_colors_map():
    """deck_id(lower) -> declared color set, for land manabase scoring."""
    try:
        import deck as dk
        return {d["id"].lower(): card_colors(d["meta"].get("colors"))
                for d in dk.discover_decks()}
    except Exception:
        return {}


def _is_land(row):
    return "land" in (row.get("Type") or "").lower()


def _land_value(row, deck_colors):
    """0–10 MANABASE value of a land for its target deck (F03) — the theme-fit axis
    is meaningless for lands (no synergy tags), so score fixing instead: reward
    producing colors the deck actually runs (a WB dual in mono-W is half-dead),
    require the deck to span >=2 of the land's colors for a dual to matter, and
    prize untapped fixing. Colorless/utility or unknown-deck lands score neutral."""
    txt = (row.get("Card Text") or "")
    prod = card_colors(row.get("Color(s)"))
    for c in "WUBRG":
        if "{" + c + "}" in txt:
            prod.add(c)
    if not prod or not deck_colors:
        return 3.5  # colorless/utility land, or no known target — neutral
    used = prod & deck_colors
    match = len(used) / len(prod)                 # fraction of its colors the deck uses
    multi = 1.0 if len(used) >= 2 else 0.5 if len(used) == 1 else 0.0
    base = 3.5 + 4.5 * match * multi              # ~3.5..8 by color usefulness
    if "enters tapped" not in txt.lower() and "enters the battlefield tapped" not in txt.lower():
        base += 1.5                               # untapped fixing is premium
    return round(min(10.0, base), 1)


def _deck_status():
    """deck_id(lower) -> (tier_letter, remaining_craft_count).

    remaining = distinct non-basic cards in the deck the collection doesn't own.
    Lets `--rank` show whether a card's target deck is BUILT (an upgrade to a deck
    you play — high value) or UNBUILT (a build project — lower value per wildcard),
    and surface cards that are the LAST few crafts finishing a near-complete deck.
    """
    try:
        import deck as dk
    except Exception:
        return {}
    _bk, _bn, by_name_qty = dk.load_collection()
    out = {}
    for d in dk.discover_decks():
        meta, cards = dk.parse_deck_file(d["path"])
        tier = dk._deck_tier(meta) or "·"
        need = set()
        for _qty, name, _s, _c in cards:
            cnt, in_lib = dk.owned(by_name_qty, name)
            if cnt == 0 and not in_lib and name.strip().lower() not in dk.BASICS:
                need.add(name.strip().lower())
        out[d["id"].lower()] = (tier, len(need))
    return out


def _status_label(target, status_map):
    """Compact 'built-state' tag for a card's target deck: '<tier>·<remaining>'.
    '★' marks a deck this card would help FINISH (<=3 crafts left). '—' for
    general/concept targets that aren't a single buildable deck."""
    first = ""
    for tok in re.split(r"[;,]", target or ""):
        tok = tok.strip().lower()
        if tok and tok not in ("—", "general") and not tok.startswith("concept"):
            first = tok
            break
    if not first or first not in status_map:
        return "—"
    tier, rem = status_map[first]
    star = "★" if 0 < rem <= 3 else ""
    return f"{tier}·{rem}{star}"


def _rank_scores(rows):
    """Score every wishlist card for wildcard-spend priority. Reuses the idf theme
    model (so it stays consistent with --suggest-targets):

      fit    – idf-weighted theme fit to the card's best-matching deck.
      reuse  – # decks the card is castable in AND shares a SPECIFIC (idf-signal)
               theme with — real cross-deck breadth, not generic overlap.
      pri    – fit + 0.6 * max(0, reuse - 1)   (home-run fit + a breadth bonus).

    Tiers: A = confident theme home (fit>=1.5 on a specific theme) OR breadth>=3;
    B = a specific-theme fit / castable-on-theme in >=1 deck; C = generic/none.
    """
    fps, idf, spec_idf = _theme_model()
    status_map = _deck_status()
    deck_colors = _deck_colors_map()
    out = []
    for r in rows:
        ccols = card_colors(r.get("Color(s)"))
        ctags = {t.strip() for t in (r.get("Synergies") or "").split(";") if t.strip()}
        best, best_specific, reuse = 0.0, [], 0
        for did, dcols, central, twn in fps:
            if not ccols.issubset(dcols):
                continue
            shared = ctags & central
            if not shared:
                continue
            specific = sorted((t for t in shared if idf.get(t, 0) >= spec_idf
                               and t.lower() not in NON_SIGNAL_TAGS),
                              key=lambda t: -idf[t])
            if specific:
                reuse += 1
            score = sum(idf.get(t, 0) * twn[t] for t in shared)
            if score > best:
                best, best_specific = score, specific
        if best_specific and best >= 1.5:
            conf = "STRONG"
        elif best_specific:
            conf = "ok"
        else:
            conf = "review"
        pri = best + 0.6 * max(0, reuse - 1)
        tier = "A" if (conf == "STRONG" or reuse >= 3) else \
               "B" if (best_specific or reuse >= 1) else "C"
        raw_power = (r.get("Power") or "").strip()
        try:
            power = float(raw_power) if raw_power else 0.0
            bad_power = False
        except ValueError:
            # A non-numeric typo ("~9", "4,5", "TBD") must NOT silently score 0.0 and
            # sink a bomb without a flag (audit F9) — surface it like a blank cell.
            power = 0.0
            bad_power = True
        target = (r.get("Target") or "").strip() or "—"
        # F03: lands score on manabase value (not synergy themes), against the
        # target deck's colors. Resolve the first real deck id in the Target.
        land_val = None
        if _is_land(r):
            dcols = set()
            for tok in re.split(r"[;,]", target):
                t = tok.strip().lower()
                if t in deck_colors:
                    dcols = deck_colors[t]
                    break
            land_val = _land_value(r, dcols)
        out.append({
            "name": r.get("Card Name", ""), "rarity": (r.get("Rarity") or "").capitalize(),
            "target": target,
            "conf": conf, "fit": round(best, 2), "reuse": reuse,
            "pri": round(pri, 2), "tier": tier, "power": round(power, 1),
            "state": _status_label(target, status_map),
            "blank_power": not raw_power,
            "bad_power": bad_power, "raw_power": raw_power,
            "land_val": land_val,
            "sig": "/".join(best_specific[:2]) or ("generic/no-theme" if conf == "review" else ""),
        })
    # Normalize fit (pri) to 0-10 and blend 50/50 with the hand-graded power
    # (already 0-10) into a combined value-per-wildcard score. fitN is exposed so
    # the artifact can re-blend live at any fit/power weight.
    mx = max((s["pri"] for s in out), default=0) or 1
    for s in out:
        if s.get("land_val") is not None:
            # F03: a land's "fit" IS its manabase value; blend land-heavy with any
            # hand-graded Power (usually blank for lands → land value carries it),
            # and re-tier from the land value so a well-matched untapped dual ranks
            # like a real upgrade instead of at a 0.0 theme-fit.
            s["fitN"] = s["land_val"]
            pw = s["power"] or s["land_val"]
            s["combined"] = round(0.65 * s["land_val"] + 0.35 * pw, 2)
            s["tier"] = "A" if s["land_val"] >= 7 else "B" if s["land_val"] >= 5 else "C"
            s["sig"] = "manabase (land)"
        else:
            s["fitN"] = round(s["pri"] / mx * 10, 2)
            s["combined"] = round(0.5 * s["fitN"] + 0.5 * s["power"], 2)
    order = {"A": 0, "B": 1, "C": 2}
    out.sort(key=lambda s: (order[s["tier"]], -s["pri"], -_WC_RANK.get(s["rarity"], 0), s["name"]))
    return out


def cmd_rank(rows):
    """Rank the wishlist by wildcard-spend priority — theme fit + hand-graded power
    blended into a `combined` score — grouped by recommendation tier."""
    # Exclude cards already crafted — the wishlist keeps them until pruned, but a
    # craft PLAN must not tell you to spend a wildcard on a card you own (audit F19).
    owned = owned_index()
    unowned = [r for r in rows if not _owned_of(owned, r.get("Card Name"))]
    owned_skipped = len(rows) - len(unowned)
    scored = _rank_scores(unowned)
    order = {"A": 0, "B": 1, "C": 2}
    scored.sort(key=lambda s: (order.get(s["tier"], 9), -s["combined"], s["name"]))
    labels = {"A": "TIER A — craft first (confident theme home and/or real cross-deck breadth)",
              "B": "TIER B — solid targeted upgrade (one clear deck)",
              "C": "TIER C — situational / build-around (niche; craft when you build that deck)"}
    cur = None
    for s in scored:
        if s["tier"] != cur:
            cur = s["tier"]
            n = sum(1 for x in scored if x["tier"] == cur)
            print(f"\n{labels[cur]}  ({n} cards)")
            print(f"  {'#':>3} {'Card':28} {'WC':3} {'Deck':6} {'state':6} {'fit':>4} "
                  f"{'pow':>4} {'comb':>5}  signal")
            print("  " + "-" * 94)
            i = 0
        i += 1
        wc = (s["rarity"] or "?")[:1] or "?"
        pw = f"{s['power']:>4.1f}" + ("?" if s["blank_power"] else "!" if s["bad_power"] else " ")
        print(f"  {i:>3} {s['name'][:28]:28} {wc:3} {s['target']:6} {s['state']:6} "
              f"{s['fitN']:>4.1f} {pw} {s['combined']:>5.1f}  {s['sig'][:28]}")
    print("\n" + "=" * 60)
    print("Wildcard cost by tier (you spend that rarity's wildcards):")
    for t in ("A", "B", "C"):
        by = {}
        for s in scored:
            if s["tier"] == t:
                by[s["rarity"]] = by.get(s["rarity"], 0) + 1
        line = ", ".join(f"{by[k]} {k}" for k in ("Mythic", "Rare", "Uncommon", "Common") if by.get(k))
        print(f"  Tier {t}: {line}")
    blanks = [s["name"] for s in scored if s["blank_power"]]
    print("\ncomb = 50/50 blend of theme fit (fit, 0–10) and hand-graded power (pow). "
          "state = target deck's tier·remaining-crafts (★ = this card helps FINISH a "
          "near-complete deck; '—' = general/concept). A high-value wildcard upgrades a "
          "BUILT deck (low remaining) — a big remaining count is a build PROJECT.")
    if blanks:
        print(f"⚠ {len(blanks)} card(s) have BLANK Power (shown as 'pow?', ranked low until "
              f"graded): {', '.join(blanks[:8])}{' …' if len(blanks) > 8 else ''}. "
              "Run `--seed-power --write` then hand-adjust the bombs.")
    bad = [(s["name"], s["raw_power"]) for s in scored if s["bad_power"]]
    if bad:
        # A malformed Power scored 0.0 and would otherwise sink silently (F9).
        print(f"⚠ {len(bad)} card(s) have a NON-NUMERIC Power (shown as 'pow!', scored 0.0): "
              f"{', '.join(f'{n} ({v!r})' for n, v in bad[:6])}"
              f"{' …' if len(bad) > 6 else ''}. Fix the cell to a 1–10 number.")
    if owned_skipped:
        print(f"({owned_skipped} already-owned card(s) excluded from the ranking — "
              "prune them with `--owned` / reconcile_crafts.py.)")
    print("For an optimal craft plan within your wildcards use "
          '`--budget "9M 10R 38U 48C"`.')
    return 0


_RARITY_LETTER = {"M": "Mythic", "R": "Rare", "U": "Uncommon", "C": "Common"}


def _parse_budget(s):
    """'9M 10R 38U 48C' (any order/spacing, case-insensitive) -> {rarity: count}."""
    caps = {}
    for num, let in re.findall(r"(\d+)\s*([MmRrUuCc])", s or ""):
        caps[_RARITY_LETTER[let.upper()]] = caps.get(_RARITY_LETTER[let.upper()], 0) + int(num)
    return caps


def cmd_budget(rows, budget_str):
    """Given a wildcard budget ('9M 10R 38U 48C'), pick the highest-`combined`
    cards affordable within each rarity's cap (it's separable per rarity, so the
    top-K-by-combined per rarity IS optimal), with 1-2 alternates each and an
    Arena import block of the picks."""
    caps = _parse_budget(budget_str)
    if not caps:
        eprint('Could not parse budget. Example: --budget "9M 10R 38U 48C"')
        return 1
    # Don't spend the budget on cards already owned (audit F19).
    owned = owned_index()
    rows = [r for r in rows if not _owned_of(owned, r.get("Card Name"))]
    scored = _rank_scores(rows)
    by_rar = {}
    for s in scored:
        by_rar.setdefault(s["rarity"], []).append(s)
    for r in by_rar:
        by_rar[r].sort(key=lambda s: (-s["combined"], s["name"]))

    print(f"Wildcard-spend plan for budget: "
          + ", ".join(f"{caps[r]} {r}" for r in ("Mythic", "Rare", "Uncommon", "Common") if caps.get(r)))
    print("(picks = highest combined fit+power within each cap; alts = next best)\n")
    import_block = ["Deck"]
    meta_by = {s["name"]: s for s in scored}
    for rar in ("Mythic", "Rare", "Uncommon", "Common"):
        cap = caps.get(rar, 0)
        if not cap:
            continue
        pool = by_rar.get(rar, [])
        picks, alts = pool[:cap], pool[cap:cap + 2]
        print(f"=== {rar}  ({len(picks)} pick(s) of {cap} WC"
              + (f"; {cap - len(picks)} WC left over — wishlist has no more {rar}s)" if len(picks) < cap else ")"))
        for s in picks:
            print(f"   {s['combined']:>4.1f}  {s['name'][:34]:34} "
                  f"deck {s['target']:6}  (fit {s['fitN']:.1f} / pow {s['power']:.1f})")
        for s in alts:
            print(f"    alt {s['combined']:>3.1f}  {s['name'][:32]:32} deck {s['target']}")
        print()

    # Arena import block of the picks (front/full name is what the wishlist stores).
    wl_by = {(r.get("Card Name") or ""): r for r in rows}
    print("Import block (recommended crafts):\n```")
    print("Deck")
    for rar in ("Mythic", "Rare", "Uncommon", "Common"):
        for s in by_rar.get(rar, [])[:caps.get(rar, 0)]:
            r = wl_by.get(s["name"], {})
            setc, coll = r.get("Set Code", ""), r.get("Collector #", "")
            print(f"1 {s['name']}" + (f" ({setc}) {coll}" if setc else ""))
    print("```")
    return 0


# Heuristic power SEED (a first pass for blank Power cells — NOT authoritative;
# the role classifier underrates bombs whose value is unique text, so treat the
# number as an estimate to hand-adjust). Rarity is the objective floor.
_SEED_RARITY = {"Mythic": 4.5, "Rare": 3.2, "Uncommon": 2.0, "Common": 1.0}
_SEED_ROLE = {"Sweeper": 2.0, "Reanimation": 1.6, "Cost reduction / cheat": 1.6,
              "Payoff / engine": 1.5, "Card advantage": 1.3, "Removal (spot)": 1.1,
              "Burn / drain": 1.1, "Counter": 0.8, "Recursion": 0.7, "Ramp / fixing": 0.6,
              "Team pump / anthem": 0.6, "Protection / trick": 0.4, "Lifegain": 0.3}


def _seed_power(r):
    import deck as dk
    p = _SEED_RARITY.get((r.get("Rarity") or "").capitalize(), 2.0)
    p += sum(_SEED_ROLE.get(x, 0) for x in dk.classify_roles(r.get("Card Text") or ""))
    ty = (r.get("Type") or "").lower()
    if "planeswalker" in ty:
        p += 2.0
    if "legendary" in ty:
        p += 0.3
    return min(10.0, round(p * 2) / 2)  # nearest 0.5


def cmd_seed_power(rows, write=False):
    """Fill BLANK Power cells with a heuristic first-pass estimate (rarity floor +
    functional-role signals). Never touches a Power you've already graded. It's an
    ESTIMATE to review — the classifier can't see a bomb's unique text."""
    blanks = [r for r in rows if not (r.get("Power") or "").strip()]
    if not blanks:
        print("Every wishlist card already has a Power grade — nothing to seed.")
        return 0
    print(f"Heuristic Power seed for {len(blanks)} blank cell(s) "
          "(estimate — review & adjust):\n")
    print(f"  {'seed':>4}  {'WC':3} Card")
    for r in sorted(blanks, key=lambda r: -_seed_power(r)):
        est = _seed_power(r)
        if write:
            r["Power"] = str(est)
        wc = (r.get("Rarity") or "?")[:1]
        print(f"  {est:>4.1f}  {wc:3} {r.get('Card Name', '')[:44]}")
    if write:
        write_wishlist(rows)
        print(f"\nWrote {len(blanks)} Power estimate(s) to {os.path.basename(WISHLIST_CSV)}. "
              "Review and hand-adjust the bombs the heuristic undersells.")
    else:
        print("\nRead-only. Re-run with --write to fill the blank Power cells.")
    return 0


def print_table(hits, owned):
    cols = ["Have", "Card Name", "Type", "Color(s)", "Set", "Rarity", "Target"]
    def have_of(c):
        return "own" if _owned_of(owned, c.get("Card Name")) > 0 else ""
    data = []
    for c in hits:
        data.append({"Have": have_of(c), "Card Name": c.get("Card Name", ""),
                     "Type": c.get("Type", ""), "Color(s)": c.get("Color(s)", ""),
                     "Set": c.get("Set Code", ""), "Rarity": c.get("Rarity", ""),
                     "Target": c.get("Target", "")})
    widths = {col: len(col) for col in cols}
    for d in data:
        for col in cols:
            widths[col] = max(widths[col], len(str(d[col])))
    widths["Type"] = min(widths["Type"], 32)
    widths["Card Name"] = min(widths["Card Name"], 32)

    def fmt(vals):
        return "  ".join(str(vals[c])[:widths[c]].ljust(widths[c]) for c in cols)
    print(fmt({c: c for c in cols}))
    print(fmt({c: "-" * widths[c] for c in cols}))
    for d in data:
        print(fmt(d))


def _audit_target_issues(color_only=False):
    """Return [(severity, card, message)] for wishlist-target problems, checked
    against the CURRENT decks: 'color' = the target deck can't cast the card (the
    drift you get when a deck changes colors, e.g. 14 Mardu->Rakdos orphaned Neriv);
    'target' = an unknown deck id; 'power' = a blank Power cell. With color_only,
    returns just the castability/target-drift issues (for check_all's soft pass)."""
    rows = load_wishlist()
    issues = []
    deck_cols, deck_ids = {}, set()
    try:
        import deck as dk
        for d in dk.discover_decks():
            deck_ids.add(d["id"].lower())
            deck_cols[d["id"].lower()] = card_colors(d["meta"].get("colors"))
    except Exception:
        pass
    for r in rows:
        name = (r.get("Card Name") or "").strip()
        if not color_only and not (r.get("Power") or "").strip():
            issues.append(("power", name, "blank Power (ranks low until graded)"))
        ident = card_colors(r.get("Color(s)"))
        for tok in re.split(r"[;,]", (r.get("Target") or "")):
            tok = tok.strip().lower()
            if not tok or tok in ("—", "general") or tok.startswith("concept"):
                continue
            if deck_ids and tok not in deck_ids:
                issues.append(("target", name, f"target '{tok}' is not a known deck id"))
                continue
            dc = deck_cols.get(tok)
            if dc and ident and not ident.issubset(dc):
                issues.append(("color", name, f"identity {''.join(sorted(ident)) or 'C'} "
                               f"can't be cast in deck {tok} ({''.join(sorted(dc)) or 'C'})"))
    return issues


def cmd_audit_targets(_rows):
    """Audit wishlist Targets against the current decks: flag cards whose target
    deck can't cast them (color/theme drift after a retune) and blank Power cells."""
    issues = _audit_target_issues()
    if not issues:
        print("Wishlist targets are clean: every target deck can cast its card, "
              "and every card has a Power grade.")
        return 0
    groups = {}
    for sev, name, msg in issues:
        groups.setdefault(sev, []).append((name, msg))
    for sev, label in [("color", "OFF-COLOR — target deck can't cast this (re-home the Target)"),
                       ("target", "UNKNOWN TARGET — deck id not found"),
                       ("power", "BLANK POWER — ranks low until graded")]:
        g = groups.get(sev)
        if not g:
            continue
        print(f"\n{label}  ({len(g)})")
        for name, msg in g:
            print(f"  {name[:32]:32} {msg}")
    print(f"\n{len(issues)} issue(s). Re-home color/target drift by editing the Target; "
          "fill blank Power with `--seed-power --write`, then hand-adjust bombs.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Manage the craft-target / wishlist.")
    ap.add_argument("--add", metavar="FILE",
                    help="append an Arena-export batch (or '-' for stdin), enriching each card")
    ap.add_argument("--by-set", action="store_true",
                    help="summarize unowned wishlist cards per set (pack optimization)")
    ap.add_argument("--suggest-targets", action="store_true",
                    help="propose a Target per card (idf-weighted theme fit + confidence); "
                         "review flags are cards to judge from card text")
    ap.add_argument("--write", action="store_true",
                    help="with --suggest-targets: write strong/ok picks into blank Targets")
    ap.add_argument("--overwrite", action="store_true",
                    help="with --suggest-targets --write: also overwrite existing Targets")
    ap.add_argument("--rank", action="store_true",
                    help="rank cards by wildcard-spend priority (theme fit + hand-graded "
                         "power, blended), grouped by recommendation tier")
    ap.add_argument("--budget", metavar="SPEC",
                    help='optimal craft plan within a wildcard budget, e.g. '
                         '"9M 10R 38U 48C" (picks highest combined score per rarity cap)')
    ap.add_argument("--seed-power", dest="seed_power", action="store_true",
                    help="first-pass heuristic estimate for BLANK Power cells "
                         "(add --write to persist; review — it's an estimate)")
    ap.add_argument("--audit-targets", dest="audit_targets", action="store_true",
                    help="flag wishlist cards whose target deck can't cast them "
                         "(color/theme drift after a retune) or have blank Power")
    ap.add_argument("--owned", action="store_true",
                    help="show only wishlist cards you now OWN (drop candidates)")
    ap.add_argument("--name"); ap.add_argument("--type"); ap.add_argument("--text")
    ap.add_argument("--color"); ap.add_argument("--synergy"); ap.add_argument("--set")
    ap.add_argument("--target"); ap.add_argument("--note")
    ap.add_argument("--rarity", help="comma-separated: common,uncommon,rare,mythic")
    ap.add_argument("--count", action="store_true")
    args = ap.parse_args()

    if args.add:
        return cmd_add(args.add)

    rows = load_wishlist()
    if not rows:
        eprint("Wishlist is empty. Add cards: python3 scripts/wishlist.py --add batch.txt")
        return 0
    owned = owned_index()

    if args.by_set:
        return cmd_by_set(rows, owned)
    if args.suggest_targets:
        return cmd_suggest_targets(rows, write=args.write, overwrite=args.overwrite)
    if args.rank:
        return cmd_rank(rows)
    if args.audit_targets:
        return cmd_audit_targets(rows)
    if args.budget:
        return cmd_budget(rows, args.budget)
    if args.seed_power:
        return cmd_seed_power(rows, write=args.write)

    hits = [c for c in rows if _match(c, args)]
    if args.owned:
        hits = [c for c in hits if _owned_of(owned, c.get("Card Name")) > 0]

    if args.count:
        print(len(hits))
        return 0
    if not hits:
        eprint("No wishlist cards matched.")
        return 0

    print_table(hits, owned)
    still = sum(1 for c in hits
                if _owned_of(owned, c.get("Card Name")) == 0)
    from collections import Counter
    by_r = Counter((c.get("Rarity") or "?").capitalize() for c in hits
                   if _owned_of(owned, c.get("Card Name")) == 0)
    tail = ", ".join(f"{by_r[x]} {x}" for x in ("Mythic", "Rare", "Uncommon", "Common", "?")
                     if by_r[x])
    print(f"\n{len(hits)} card(s) — {still} to craft" + (f" ({tail})" if tail else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
