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

from lib import DEFAULT_CSV, REPO_ROOT, load_rows, eprint

WISHLIST_CSV = os.path.join(REPO_ROOT, "card-wishlist.csv")
POOL_CSV = os.path.join(REPO_ROOT, "card-pool.csv")

HEADER = ["Card Name", "Type", "Card Text", "Color(s)", "Synergies",
          "Set Code", "Collector #", "Rarity", "Target", "Note"]
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
        for k in (n, n.split(" // ")[0]):
            counts[k] = counts.get(k, 0) + c
    return counts


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
    with open(WISHLIST_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow({c: (r.get(c, "") or "") for c in HEADER})


# --------------------------------------------------------------------------- #
# Enrichment (pool first, Scryfall fallback)
# --------------------------------------------------------------------------- #
def _from_scryfall(name, set_code):
    """Best-effort single lookup for a card the pool lacks (e.g. a new DFC). Returns
    an enrichment dict or None. Imports network/enrich bits lazily so the common
    (pool-hit) path stays dependency- and network-free."""
    import json
    import time
    import urllib.error
    import urllib.parse
    import urllib.request
    from enrich import color_shorthand, oracle_fields
    from tag_synergies import tags_for

    def _get(params):
        url = "https://api.scryfall.com/cards/named?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(
            url, headers={"User-Agent": "mtga-card-library/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)

    card = None
    for params in ({"exact": name, "set": set_code.lower()} if set_code else {"exact": name},
                   {"fuzzy": name}):
        try:
            card = _get(params)
            break
        except (urllib.error.URLError, ValueError):
            continue
    time.sleep(0.1)
    if not card:
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
    """Build a wishlist row for one card. Uses the canonical (full) name from the
    pool/Scryfall so double-faced cards join cleanly with the rest of the tooling."""
    p = pool.get(name.lower())
    if p:
        data = {"Card Name": p.get("Card Name", name), "Type": p.get("Type", ""),
                "Card Text": p.get("Card Text", ""), "Color(s)": p.get("Color(s)", ""),
                "Synergies": p.get("Synergies", ""), "Rarity": p.get("Rarity", "")}
    else:
        s = _from_scryfall(name, set_code)
        if s is None:
            eprint(f"WARN:  could not resolve {name!r} in pool or Scryfall — "
                   "added with name only.")
            data = {"Card Name": name, "Type": "", "Card Text": "", "Color(s)": "",
                    "Synergies": "", "Rarity": ""}
        else:
            data = s
    data["Set Code"] = set_code
    data["Collector #"] = collector
    data.setdefault("Target", "")
    data.setdefault("Note", "")
    return data


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
    seen = {((r.get("Card Name") or "").strip().lower(),
             (r.get("Set Code") or "").strip().lower(),
             (r.get("Collector #") or "").strip().lower()) for r in existing}

    added, dupes, owned_hits, warns = 0, 0, [], 0
    for name, setc, cn in entries:
        row = enrich(name, setc, cn, pool)
        key = (row["Card Name"].strip().lower(), setc.lower(), cn.lower())
        if key in seen:
            dupes += 1
            continue
        if owned.get(name.lower(), 0) > 0:
            owned_hits.append(row["Card Name"])
        if not row.get("Rarity") and not row.get("Type"):
            warns += 1
        existing.append(row)
        seen.add(key)
        added += 1

    write_wishlist(existing)
    print(f"Added {added} card(s) to the wishlist ({dupes} already listed). "
          f"Wishlist now has {len(existing)} card(s). Wrote {os.path.basename(WISHLIST_CSV)}.")
    if owned_hits:
        print(f"NOTE: {len(owned_hits)} added card(s) you ALREADY OWN "
              f"(consider removing): {', '.join(owned_hits[:8])}"
              + ("…" if len(owned_hits) > 8 else ""))
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
        if owned.get((c.get("Card Name") or "").strip().lower(), 0) > 0:
            continue  # already acquired — don't count toward crafting/packs
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
    """Build the deck theme model for target suggestion. Returns (fps, idf):

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
    idf = {t: math.log(n / (1 + c)) for t, c in df.items()}
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
        ccols = {ch for ch in (r.get("Color(s)") or "").upper() if ch in "WUBRG"}
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
    out = []
    for r in rows:
        ccols = {ch for ch in (r.get("Color(s)") or "").upper() if ch in "WUBRG"}
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
        out.append({
            "name": r.get("Card Name", ""), "rarity": (r.get("Rarity") or "").capitalize(),
            "target": (r.get("Target") or "").strip() or "—",
            "conf": conf, "fit": round(best, 2), "reuse": reuse,
            "pri": round(pri, 2), "tier": tier,
            "sig": "/".join(best_specific[:2]) or ("generic/no-theme" if conf == "review" else ""),
        })
    order = {"A": 0, "B": 1, "C": 2}
    out.sort(key=lambda s: (order[s["tier"]], -s["pri"], -_WC_RANK.get(s["rarity"], 0), s["name"]))
    return out


def cmd_rank(rows):
    """Rank the wishlist by wildcard-spend priority, grouped by recommendation tier."""
    scored = _rank_scores(rows)
    labels = {"A": "TIER A — craft first (confident theme home and/or real cross-deck breadth)",
              "B": "TIER B — solid targeted upgrade (one clear deck)",
              "C": "TIER C — situational / build-around (niche; craft when you build that deck)"}
    cur = None
    for s in scored:
        if s["tier"] != cur:
            cur = s["tier"]
            n = sum(1 for x in scored if x["tier"] == cur)
            print(f"\n{labels[cur]}  ({n} cards)")
            print(f"  {'#':>3} {'Card':32} {'WC':3} {'Deck':6} {'reuse':>5} {'pri':>5}  signal")
            print("  " + "-" * 86)
            i = 0
        i += 1
        wc = (s["rarity"] or "?")[:1] or "?"
        print(f"  {i:>3} {s['name'][:32]:32} {wc:3} {s['target']:6} "
              f"{s['reuse']:>5} {s['pri']:>5}  {s['sig'][:34]}")
    print("\n" + "=" * 60)
    print("Wildcard cost by tier (you spend that rarity's wildcards):")
    for t in ("A", "B", "C"):
        by = {}
        for s in scored:
            if s["tier"] == t:
                by[s["rarity"]] = by.get(s["rarity"], 0) + 1
        line = ", ".join(f"{by[k]} {k}" for k in ("Mythic", "Rare", "Uncommon", "Common") if by.get(k))
        print(f"  Tier {t}: {line}")
    print("\nNote: ranking reads THEME-fit, not raw power — a few generic-tagged bombs "
          "(planeswalkers, mana rocks, Krenko-likes) sit in Tier C; eyeball those.")
    return 0


def print_table(hits, owned):
    cols = ["Have", "Card Name", "Type", "Color(s)", "Set", "Rarity", "Target"]
    def have_of(c):
        return "own" if owned.get((c.get("Card Name") or "").strip().lower(), 0) > 0 else ""
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
                    help="rank cards by wildcard-spend priority (fit + cross-deck breadth), "
                         "grouped by recommendation tier")
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

    hits = [c for c in rows if _match(c, args)]
    if args.owned:
        hits = [c for c in hits if owned.get((c.get("Card Name") or "").strip().lower(), 0) > 0]

    if args.count:
        print(len(hits))
        return 0
    if not hits:
        eprint("No wishlist cards matched.")
        return 0

    print_table(hits, owned)
    still = sum(1 for c in hits
                if owned.get((c.get("Card Name") or "").strip().lower(), 0) == 0)
    from collections import Counter
    by_r = Counter((c.get("Rarity") or "?").capitalize() for c in hits
                   if owned.get((c.get("Card Name") or "").strip().lower(), 0) == 0)
    tail = ", ".join(f"{by_r[x]} {x}" for x in ("Mythic", "Rare", "Uncommon", "Common", "?")
                     if by_r[x])
    print(f"\n{len(hits)} card(s) — {still} to craft" + (f" ({tail})" if tail else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
