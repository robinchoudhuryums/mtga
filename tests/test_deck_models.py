"""Direct tests for deck.py's analysis MODELS — the layer that had none.

These 21 functions were reachable only through their own `cmd_*`, so they were observed
only through printed output. That is thin cover for a model whose failure is a wrong
NUMBER rather than a crash: `deck_quality_vector` is the core of the F10 guard that
`/apply-changes` runs around EVERY swap, and a change to it passed silently unless it
happened to move a tier band far enough for `check_tier` to notice.

Everything here runs against a SYNTHETIC card universe rather than the live CSVs. That is
deliberate: a test asserting "deck 3 has interaction 8" is really a test of the current
roster and starts failing the next time the deck is tuned, which trains people to ignore
it. These assert the model's CONTRACT — that the pieces agree with each other, that a
change in the input moves the output in the right direction — so they keep working as the
collection changes, the same property `check_rankings` was built for.
"""
import argparse

import pytest

import deck


# --------------------------------------------------------------------------- #
# A small, fully-controlled card universe.
# --------------------------------------------------------------------------- #
def _card(name, type_line, text="", colors="", power="", toughness=""):
    return {"name": name, "type": type_line, "text": text, "colors": colors,
            "power": power, "toughness": toughness}


UNIVERSE = {
    # Two unambiguous removal spells -> interaction. One instant, one sorcery, so the
    # speed split in interaction_profile is observable.
    "zap": _card("Zap", "Instant", "Destroy target creature.", "B"),
    "slow zap": _card("Slow Zap", "Sorcery", "Destroy target creature.", "B"),
    # Answers a NONCREATURE permanent — the axis interaction_profile adds over the count.
    "shatter": _card("Shatter", "Instant", "Destroy target artifact or enchantment.", "B"),
    # Repeatable draw -> card advantage (a single cantrip deliberately would not count).
    "arena": _card("Arena", "Enchantment",
                   "At the beginning of your upkeep, you draw a card and you lose 1 life.", "B"),
    "bear": _card("Bear", "Creature — Bear", "", "B", "2", "2"),
    "big bear": _card("Big Bear", "Creature — Bear", "", "B", "5", "5"),
    # Off-colour: identity R in a mono-B deck, and its cost demands R, so it is
    # genuinely UNCASTABLE rather than a hybrid you pay on-colour.
    "red bear": _card("Red Bear", "Creature — Bear", "", "R", "2", "2"),
    "swamp": _card("Swamp", "Basic Land — Swamp", "", ""),
}

MANA = {
    "zap": ("{1}{B}", 2), "slow zap": ("{1}{B}", 2), "shatter": ("{1}{B}", 2),
    "arena": ("{2}{B}", 3), "bear": ("{1}{B}", 2), "big bear": ("{4}{B}", 5),
    "red bear": ("{1}{R}", 2), "swamp": ("", 0),
}

META = {
    "zap": {"colors": {"B"}, "synergies": ["removal"]},
    "slow zap": {"colors": {"B"}, "synergies": ["removal"]},
    "shatter": {"colors": {"B"}, "synergies": ["removal"]},
    "arena": {"colors": {"B"}, "synergies": ["card draw"]},
    "bear": {"colors": {"B"}, "synergies": ["Bear"]},
    "big bear": {"colors": {"B"}, "synergies": ["Bear"]},
    "red bear": {"colors": {"R"}, "synergies": ["Bear"]},
}


@pytest.fixture
def synth(tmp_path, monkeypatch):
    """Build a deck from `lines` against the synthetic universe, with every reference
    table monkeypatched. Returns a factory so each test shapes its own deck."""
    def build(lines, header="#: name: Synth\n#: format: standard\n#: colors: B\n",
              owned=None):
        path = tmp_path / "deck.txt"
        path.write_text(header + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
        qty = {k: 4 for k in UNIVERSE} if owned is None else owned
        monkeypatch.setattr(deck, "load_card_data", lambda: UNIVERSE)
        monkeypatch.setattr(deck, "load_mana", lambda: MANA)
        monkeypatch.setattr(deck, "load_card_meta", lambda: META)
        monkeypatch.setattr(deck, "load_collection", lambda: ({}, {}, qty))
        monkeypatch.setattr(deck, "load_legalities", lambda: {})
        return {"id": "synth", "name": "Synth", "path": str(path),
                "core": "synth", "variant": None}
    return build


# --------------------------------------------------------------------------- #
class TestDeckQualityVector:
    """The F10 guard's core. `/apply-changes` snapshots this before a swap and compares
    after, so a swap that worsens the deck self-catches — which only works if the vector
    actually moves when the deck does."""

    def test_counts_interaction_and_card_advantage(self, synth):
        v = deck.deck_quality_vector(synth(["2 Zap", "1 Arena", "1 Bear", "20 Swamp"]))
        assert v["interaction"] == 2          # quantity-weighted: 2 copies of Zap
        assert v["card_advantage"] == 1

    def test_agrees_with_the_canonical_role_tally(self, synth):
        """Three views used to disagree by +/-1; role_tally is now the single source and
        the vector must not drift from it."""
        d = synth(["2 Zap", "1 Slow Zap", "1 Arena", "1 Bear", "20 Swamp"])
        _, cards = deck.parse_deck_file(d["path"])
        tally = deck.role_tally(cards, UNIVERSE)
        v = deck.deck_quality_vector(d)
        assert v["interaction"] == tally["interaction"]
        assert v["card_advantage"] == tally["card_advantage"]

    def test_buildable_flips_when_the_collection_is_short(self, synth):
        full = synth(["4 Zap", "20 Swamp"])
        assert deck.deck_quality_vector(full)["buildable"] is True
        short = synth(["4 Zap", "20 Swamp"], owned={"zap": 1, "swamp": 4})
        v = deck.deck_quality_vector(short)
        assert v["buildable"] is False and v["short"] == 1

    def test_a_card_absent_from_the_collection_reads_as_missing(self, synth):
        v = deck.deck_quality_vector(synth(["1 Zap", "20 Swamp"], owned={"swamp": 4}))
        assert v["missing"] == 1 and v["buildable"] is False

    def test_an_off_colour_card_is_uncastable(self, synth):
        """Red Bear costs {1}{R} in a mono-B deck — a strict off-colour pip, not a
        hybrid you pay on-colour."""
        v = deck.deck_quality_vector(synth(["1 Red Bear", "20 Swamp"]))
        assert v["uncastable"] == 1

    def test_curve_is_the_average_nonland_mana_value(self, synth):
        # Bear 2 + Big Bear 5 -> 3.5; the 20 Swamps must not drag it toward 0.
        v = deck.deck_quality_vector(synth(["1 Bear", "1 Big Bear", "20 Swamp"]))
        assert v["avg_mv"] == pytest.approx(3.5, abs=0.01)

    def test_early_drops_counts_two_mana_and_below(self, synth):
        v = deck.deck_quality_vector(synth(["3 Bear", "1 Big Bear", "20 Swamp"]))
        assert v["early_drops"] == 3

    def test_creatures_are_quantity_weighted(self, synth):
        v = deck.deck_quality_vector(synth(["3 Bear", "1 Zap", "20 Swamp"]))
        assert v["creatures"] == 3

    def test_the_vector_moves_when_the_deck_does(self, synth):
        """The property /apply-changes actually depends on: swapping a threat for an
        answer must show up as more interaction."""
        before = deck.deck_quality_vector(synth(["2 Bear", "20 Swamp"]))
        after = deck.deck_quality_vector(synth(["1 Bear", "1 Zap", "20 Swamp"]))
        assert after["interaction"] > before["interaction"]


class TestTierGap:
    """`tier --to A` turns the gap into a wildcard-spend plan, so the arithmetic has to
    be right in both directions: what is missing, and when nothing is."""

    def test_a_deck_already_at_the_floor_has_no_gap(self):
        vec = {"interaction": 9, "card_advantage": 4, "uncastable": 0}
        gap = deck.tier_gap(vec, "A")
        assert gap["met"] is True and gap["add_interaction"] == 0

    def test_reports_the_missing_interaction(self):
        vec = {"interaction": 2, "card_advantage": 0, "uncastable": 0}
        gap = deck.tier_gap(vec, "A")
        assert gap["met"] is False and gap["add_interaction"] > 0

    def test_an_uncastable_stray_is_reported_as_a_fix(self):
        """CLAUDE.md: any uncastable stray caps a deck at C, so climbing past it means
        fixing the stray, not adding removal."""
        vec = {"interaction": 9, "card_advantage": 4, "uncastable": 2}
        assert deck.tier_gap(vec, "A")["fix_uncastable"] == 2

    def test_a_lower_target_is_easier_than_a_higher_one(self):
        vec = {"interaction": 3, "card_advantage": 1, "uncastable": 0}
        assert (deck.tier_gap(vec, "B")["add_interaction"]
                <= deck.tier_gap(vec, "A")["add_interaction"])


class TestInteractionProfile:
    """Beyond the raw count: how much of the interaction is instant-speed, and how much
    can answer a noncreature permanent."""

    def _cards(self, *names):
        return [(1, n, None, None) for n in names]

    def test_splits_by_speed(self):
        p = deck.interaction_profile(self._cards("Zap", "Slow Zap"), UNIVERSE)
        assert p["total"] == 2 and p["instant"] == 1 and p["sorcery"] == 1

    def test_flags_an_all_sorcery_suite(self):
        # The flags need total >= 3 before they fire — below that the sample is too
        # small to mean anything, which is the same restraint count_conf shows.
        p = deck.interaction_profile([(3, "Slow Zap", None, None)], UNIVERSE)
        assert p["total"] == 3 and p["instant"] == 0
        assert any("sorcery" in f.lower() for f in p["flags"])

    def test_the_flags_stay_quiet_below_the_sample_floor(self):
        assert deck.interaction_profile([(1, "Slow Zap", None, None)],
                                        UNIVERSE)["flags"] == []

    def test_counts_a_noncreature_answer(self):
        p = deck.interaction_profile(self._cards("Zap", "Shatter"), UNIVERSE)
        assert p["noncreature"] >= 1

    def test_flags_having_no_noncreature_answer(self):
        p = deck.interaction_profile(
            [(2, "Zap", None, None), (2, "Slow Zap", None, None)], UNIVERSE)
        assert p["noncreature"] == 0
        assert any("noncreature" in f.lower() for f in p["flags"])

    def test_an_empty_suite_is_not_an_error(self):
        assert deck.interaction_profile(self._cards("Bear"), UNIVERSE)["total"] == 0


class TestDeckRoleCounts:
    def test_matches_role_tally(self):
        cards = [(2, "Zap", None, None), (1, "Arena", None, None)]
        i, ca = deck.deck_role_counts(cards, UNIVERSE)
        tally = deck.role_tally(cards, UNIVERSE)
        assert (i, ca) == (tally["interaction"], tally["card_advantage"])

    def test_is_quantity_weighted(self):
        assert deck.deck_role_counts([(3, "Zap", None, None)], UNIVERSE)[0] == 3


class TestLegalityReport:
    """The pure legality engine shared by `legal` (one deck, verbose) and `audit`
    (roster). A disagreement between those two would be invisible without this."""

    def _cards(self, *pairs):
        return [(q, n, None, None) for q, n in pairs]

    def test_a_legal_standard_deck_has_no_problems(self):
        meta = {"format": "standard"}
        rep = deck.legality_report(meta, self._cards((4, "Zap"), (56, "Swamp")),
                                   "standard", {}, carddata=UNIVERSE)
        assert rep["problems"] == []

    def test_flags_a_deck_under_the_size_minimum(self):
        rep = deck.legality_report({"format": "standard"}, self._cards((4, "Zap")),
                                   "standard", {}, carddata=UNIVERSE)
        assert rep["total"] == 4 and rep["min_size"] == 60
        assert any("60" in str(p) or "size" in str(p).lower() for p in rep["problems"])

    def test_flags_more_than_four_copies(self):
        rep = deck.legality_report({"format": "standard"},
                                   self._cards((5, "Zap"), (55, "Swamp")),
                                   "standard", {}, carddata=UNIVERSE)
        assert any("Zap" in str(p) for p in rep["problems"])

    def test_basics_are_exempt_from_the_copy_limit(self):
        """Unlimited basics is the whole reason the limit can't be a blanket rule."""
        rep = deck.legality_report({"format": "standard"},
                                   self._cards((4, "Zap"), (56, "Swamp")),
                                   "standard", {}, carddata=UNIVERSE)
        assert not any("Swamp" in str(p) for p in rep["problems"])

    def test_a_pool_absent_card_is_unverified_not_illegal(self):
        """WIP decks hold craft targets the pool may not carry; treating those as
        illegal would false-flag every work-in-progress list."""
        rep = deck.legality_report({"format": "standard"},
                                   self._cards((4, "Zap"), (56, "Swamp")),
                                   "standard", {}, carddata=UNIVERSE)
        assert not any("Zap" in str(p) for p in rep["problems"])


class TestPureHelpers:
    """Small pure functions with no test at all — cheap to pin, and each one feeds a
    display or a flag someone reads."""

    def test_creature_subtypes_reads_after_the_em_dash(self):
        # NOTE deck.creature_subtypes returns a LIST; lib._creature_subtypes is a
        # separate function returning a SET. Pinning the shape so a caller doing set
        # arithmetic on the wrong one fails here rather than at a call site.
        assert deck.creature_subtypes("Creature — Human Warrior") == ["Human", "Warrior"]

    def test_creature_subtypes_spans_both_faces(self):
        got = set(deck.creature_subtypes("Creature — Human // Creature — Werewolf"))
        assert {"Human", "Werewolf"} <= got

    def test_creature_subtypes_ignores_a_noncreature_line(self):
        assert deck.creature_subtypes("Artifact — Equipment") == []

    def test_deck_status_is_the_lowercased_first_word(self):
        assert deck.deck_status({"status": "Example placeholder"}) == "example"

    def test_deck_status_is_empty_when_unset(self):
        assert deck.deck_status({}) == ""

    def test_context_flags_catches_an_x_cost(self):
        assert deck.context_flags("Deal X damage to any target.", "{X}{R}")

    def test_context_flags_is_empty_for_a_plain_card(self):
        assert deck.context_flags("Destroy target creature.", "{1}{B}") == []

    def test_read_flags_returns_a_list(self):
        assert isinstance(deck.read_flags("Destroy target creature.", "{1}{B}"), list)


class TestEffectRedundancy:
    """The virtual-copies model behind `redundancy`: how many DISTINCT cards provide
    each effect, which is what lets a singleton deck be consistent without duplicates."""

    def test_buckets_distinct_cards_by_effect(self, synth):
        d = synth(["1 Zap", "1 Slow Zap", "1 Shatter", "20 Swamp"])
        buckets = deck.effect_redundancy(d)
        removal = [b for k, b in buckets.items() if "removal" in k.lower()]
        assert removal and max(b["depth"] for b in removal) >= 3

    def test_depth_counts_distinct_cards_not_copies(self, synth):
        """Four copies of one card is ONE virtual copy — the entire point of the model,
        since duplicates don't reduce the variance a singleton deck is fighting."""
        d = synth(["4 Zap", "20 Swamp"])
        buckets = deck.effect_redundancy(d)
        removal = [b for k, b in buckets.items() if "removal" in k.lower()]
        assert removal and max(b["depth"] for b in removal) == 1


class TestDeckNeeds:
    """The STRUCTURAL profile behind `suggest --needs/--ramp/--interaction` — the axes
    the theme model is blind to."""

    def test_reports_an_interaction_shortfall(self, synth):
        needs = deck.deck_needs(synth(["4 Bear", "20 Swamp"]))
        assert needs["interaction"] == 0 and needs["int_short"] > 0

    def test_a_well_defended_deck_is_not_short(self, synth):
        needs = deck.deck_needs(synth(
            ["2 Zap", "2 Slow Zap", "2 Shatter", "1 Bear", "20 Swamp"]))
        assert needs["interaction"] >= 6 and needs["int_short"] == 0

    def test_a_top_heavy_deck_wants_acceleration(self, synth):
        heavy = deck.deck_needs(synth(["8 Big Bear", "20 Swamp"]))
        light = deck.deck_needs(synth(["8 Bear", "20 Swamp"]))
        assert heavy["avg_mv"] > light["avg_mv"]
        assert heavy["accel"] >= light["accel"]


# --------------------------------------------------------------------------- #
# Pool-backed models. These need a card POOL and a deck DIRECTORY, not just a
# card universe, so they get a second fixture. Same design as check_suggest.py's
# wiring anchor — a synthetic world with the module globals repointed — but its
# cards are chosen to isolate the rarity floor, so reusing that fixture would
# make these tests depend on choices made for a different question.
# --------------------------------------------------------------------------- #
POOL_HEADER = ["Card Name", "Type", "Card Text", "Color(s)", "Synergies",
               "Set Code", "Collector #", "Rarity", "Legalities", "Released"]

# (name, type, text, colors, tags, rarity). Deliberately spans every axis the eight
# pool-backed models read: removal, a mana dork, a dual land, an on-theme body.
POOL_CARDS = [
    ("Pool Zap", "Instant", "Destroy target creature.", "B", "removal", "Common"),
    ("Pool Wrath", "Sorcery", "Destroy all creatures.", "B", "removal", "Rare"),
    ("Pool Dork", "Creature — Elf", "{T}: Add {B}.", "B", "ramp;mana", "Common"),
    ("Pool Rock", "Artifact", "{T}: Add one mana of any color.", "", "ramp;mana", "Uncommon"),
    ("Pool Dual", "Land", "{T}: Add {B} or {G}.", "", "", "Rare"),
    ("Pool Offcolor Land", "Land", "{T}: Add {W} or {U}.", "", "", "Rare"),
    ("Pool Bear", "Creature — Bear", "", "B", "Bear", "Common"),
    ("Pool Counters Guy", "Creature — Elf",
     "When this enters, put a +1/+1 counter on target creature.", "B", "counters", "Uncommon"),
    # Spot removal that is NOT Standard-legal — owned_role_fillers used to offer this,
    # because only its craft-side sibling applied the format check.
    ("Pool Historic Zap", "Instant", "Destroy target creature.", "B", "removal", "Rare"),
    # A double-faced card. `load_card_data` keys a DFC under BOTH its full name and its
    # front face, and both rows carry the same display name — so it printed twice.
    ("Pool Door // Pool Attic", "Enchantment — Room",
     "When you unlock this door, you draw two cards and you lose 2 life.",
     "B", "card draw", "Rare"),
    # A MULTIPLIER, plus a body that FEEDS its axis. Needed for the cuts wiring test:
    # a doubler carries no synergy tags and no functional role, so both halves of the
    # cut score read it as filler unless the multiplier co-signal is actually consulted.
    ("Pool Doubler", "Creature — Wizard",
     "If a triggered ability of a creature you control triggers, that ability "
     "triggers an additional time.", "B", "", "Rare"),
    ("Pool Trigger Body", "Creature — Bear",
     "Whenever this creature attacks, you gain 1 life.", "B", "lifegain", "Common"),
    ("Pool Scaler", "Creature — Horror",
     "Affinity for Bears", "B", "", "Rare"),
]

# Per-card legality overrides; anything unlisted is Standard-legal.
POOL_LEGALITIES = {"pool historic zap": {"historic"}}


@pytest.fixture
def world(tmp_path, monkeypatch):
    """A synthetic pool + deck directory with deck.py's module globals repointed.

    `owned` selects which pool cards the collection holds, so the owned-vs-craft split
    the fillers depend on is controllable rather than inherited from the real library."""
    def build(deck_lines, owned=(), colors="B"):
        pool = tmp_path / "pool.csv"
        import csv as _csv
        with open(pool, "w", newline="", encoding="utf-8") as fh:
            w = _csv.DictWriter(fh, fieldnames=POOL_HEADER)
            w.writeheader()
            for i, (n, ty, tx, col, tags, rar) in enumerate(POOL_CARDS):
                w.writerow({"Card Name": n, "Type": ty, "Card Text": tx,
                            "Color(s)": col or "Colorless", "Synergies": tags,
                            "Set Code": "SYN", "Collector #": str(i), "Rarity": rar,
                            "Legalities": ";".join(
                                sorted(POOL_LEGALITIES.get(n.lower(), {"standard"}))),
                            "Released": "2024-01-01"})
        ddir = tmp_path / "90-synth"
        ddir.mkdir(exist_ok=True)
        (ddir / "deck.txt").write_text(
            f"#: name: Synth\n#: format: Standard\n#: colors: {colors}\n\n"
            + "\n".join(deck_lines) + "\n", encoding="utf-8")

        carddata = {n.lower(): _card(n, ty, tx, col) for n, ty, tx, col, _t, _r in POOL_CARDS}
        # Mirror load_card_data's DFC convention: the full "Front // Back" name AND the
        # front face both resolve, to the SAME display name.
        for n, ty, tx, col, _t, _r in POOL_CARDS:
            if " // " in n:
                carddata[n.split(" // ")[0].lower()] = _card(n, ty, tx, col)
        carddata.update(UNIVERSE)
        cardmeta = {n.lower(): {"colors": set(col) if col else set(),
                                "synergies": [t for t in tags.split(";") if t]}
                    for n, _ty, _tx, col, tags, _r in POOL_CARDS}
        cardmeta.update(META)
        mana = {n.lower(): ("{1}{B}", 2) for n, *_ in POOL_CARDS}
        mana.update(MANA)
        rar = {n.lower(): deck.WC_LETTER[r.lower()] for n, _ty, _tx, _c, _t, r in POOL_CARDS}

        monkeypatch.setattr(deck, "POOL_CSV", str(pool))
        monkeypatch.setattr(deck, "DECKS_DIR", str(tmp_path))
        monkeypatch.setattr(deck, "load_card_data", lambda: carddata)
        monkeypatch.setattr(deck, "load_card_meta", lambda: cardmeta)
        monkeypatch.setattr(deck, "load_mana", lambda: mana)
        monkeypatch.setattr(deck, "load_rarities", lambda: rar)
        monkeypatch.setattr(deck, "load_legalities",
                            lambda: {n.lower(): POOL_LEGALITIES.get(n.lower(), {"standard"})
                                     for n, *_ in POOL_CARDS})
        monkeypatch.setattr(deck, "load_collection",
                            lambda: ({}, {}, {n.lower(): 4 for n in owned}))
        # Repoint the match record too, or `audit_roster` reads the REAL matches.csv
        # and the games-played column stops being hermetic. Left ABSENT by default,
        # which is the healthy state the loader has to degrade to.
        monkeypatch.setattr(deck, "MATCHES_CSV", str(tmp_path / "matches.csv"))
        deck.load_match_counts.cache_clear()
        d = deck.find_deck("90")
        assert d is not None, "synthetic deck did not resolve — harness broken"
        return d
    return build


class TestRoleFillers:
    """`redundancy` proposes virtual copies from these: owned cards fill a thin effect at
    zero wildcard cost, craft targets fill it for wildcards. The split has to be real."""

    def test_owned_fillers_are_limited_to_what_you_own(self, world):
        d = world(["1 Bear", "20 Swamp"], owned=["Pool Zap"])
        names = [r[1] for r in deck.owned_role_fillers(d, {"Removal (spot)"})]
        assert "Pool Zap" in names
        assert "Pool Wrath" not in names        # in the pool, not in the collection

    def test_craft_fillers_are_limited_to_what_you_do_NOT_own(self, world):
        # Pool Wrath is a SWEEPER, not spot removal — "Destroy all creatures" and
        # "Destroy target creature" are different roles, which is the distinction
        # `redundancy` buckets on.
        d = world(["1 Bear", "20 Swamp"], owned=["Pool Zap"])
        names = [r[2] for r in deck.craft_role_fillers(d, {"Sweeper"})]
        assert "Pool Wrath" in names
        assert "Pool Zap" not in names          # owned, so it is not a craft target

    def test_spot_removal_and_a_sweeper_are_different_roles(self, world):
        """Pinning the distinction the filler split depends on."""
        d = world(["1 Bear", "20 Swamp"], owned=["Pool Zap", "Pool Wrath"])
        spot = [r[1] for r in deck.owned_role_fillers(d, {"Removal (spot)"})]
        sweep = [r[1] for r in deck.owned_role_fillers(d, {"Sweeper"})]
        assert "Pool Zap" in spot and "Pool Wrath" not in spot
        assert "Pool Wrath" in sweep

    def test_a_card_already_in_the_deck_is_not_offered(self, world):
        d = world(["1 Pool Zap", "20 Swamp"], owned=["Pool Zap", "Pool Wrath"])
        names = [r[1] for r in deck.owned_role_fillers(d, {"Removal (spot)"})]
        assert "Pool Zap" not in names

    def test_a_maindecked_dfc_is_not_offered_under_its_other_spelling(self, world):
        """BS2-19: carddata keys a DFC under BOTH spellings, and the raw-name in_deck
        filter suppressed only the spelling the deck file used — the other key sailed
        through and the deck was offered its OWN maindecked card as a 0-wildcard
        filler (25 such rows roster-wide at full limit, reaching `tier --to` and
        `redundancy`)."""
        d = world(["1 Pool Door", "20 Swamp"], owned=["Pool Door"])
        names = [r[1] for r in deck.owned_role_fillers(d, {"Card advantage"})]
        assert all("Pool Door" not in n for n in names), names

    def test_an_unowned_maindecked_dfc_is_not_offered_as_a_craft(self, world):
        """The craft sibling has the same join; the owned_qty skip only masks the
        owned case — a WIP craft target already maindecked under its front name was
        offered as a craft for its own deck."""
        d = world(["1 Pool Door", "20 Swamp"], owned=[])
        names = [r[2] for r in deck.craft_role_fillers(d, {"Card advantage"})]
        assert all("Pool Door" not in n for n in names), names

    def test_owned_fillers_exclude_a_card_illegal_in_the_deck_format(self, world):
        """Owning a card is not a licence to play it. `craft_role_fillers` always applied
        the format check and its owned sibling did not, so `tier --to A` printed one list
        labelled format-legal and an unfiltered one directly above it — and offered Deadly
        Dispute, with no Standard legality, to a Standard deck."""
        d = world(["1 Bear", "20 Swamp"], owned=["Pool Zap", "Pool Historic Zap"])
        names = [r[1] for r in deck.owned_role_fillers(d, {"Removal (spot)"})]
        assert "Pool Zap" in names                # Standard-legal, and owned
        assert "Pool Historic Zap" not in names   # owned, but not legal in this format

    def test_owned_fillers_list_a_double_faced_card_once(self, world):
        """`load_card_data` keys a DFC under both its full name and its front face, and
        both rows carry the same display name — so it consumed two lines of a six-line
        list. Exposed by the format filter, but present the whole time."""
        d = world(["1 Bear", "20 Swamp"], owned=["Pool Door"])
        names = [r[1] for r in deck.owned_role_fillers(d, {"Card advantage"})]
        assert names.count("Pool Door // Pool Attic") == 1

    def _doubler_keep(self, world, feeders):
        """Pool Doubler's keep-score in a deck with `feeders` copies of a card that feeds
        its axis. Isolates the multiplier term: the doubler carries no synergy tags, no
        functional role, and no shared creature type with the feeders, so every OTHER
        component of its keep-score is identical across the two decks."""
        lines = ["1 Pool Doubler", "20 Swamp"]
        if feeders:
            lines.insert(1, f"{feeders} Pool Trigger Body")
        rows, *_ = deck.rank_cut_candidates(world(lines))
        return {r[1]: r[0] for r in rows}["Pool Doubler"]

    def test_cuts_consults_the_multiplier_co_signal(self, world):
        """WIRING anchor. `_cuts_multiplier_adj` being bounded and monotonic says nothing
        about whether `rank_cut_candidates` ever CALLS it — and it did not, which is how
        Delney (a doubler with 10 feeders) ranked as the WEAKEST card in deck 46 while
        `suggest-homes`, reading the same primitive, scored it correctly. A doubler has no
        synergy tags and no functional role, so both halves of the cut score read it as
        filler; only the co-signal can tell it apart, and only if it is consulted."""
        # Feeder counts come from the AXIS's own calibration, never a literal. Pool
        # Doubler is a `triggers` doubler, and when that axis was recalibrated (floor
        # 5 -> 20, since its roster MINIMUM is 10) the hardcoded 6 fell below the floor:
        # the anchor then could not tell "not wired" from "correctly zero", which is the
        # bug it exists to catch wearing the fix's clothes.
        floor = deck.doubler_calib("triggers")[0]
        assert self._doubler_keep(world, floor + 5) > self._doubler_keep(world, 0), (
            "rank_cut_candidates is not consulting _cuts_multiplier_adj — a doubler must "
            "be harder to cut in a deck that actually feeds its axis")

    def test_a_doubler_with_nothing_to_double_gets_no_credit(self, world):
        """The other half: ZERO below the AXIS floor, so a doubler in a deck that barely
        feeds its axis stays genuinely cuttable."""
        below = deck.doubler_calib("triggers")[0] - 1
        assert self._doubler_keep(world, below) == self._doubler_keep(world, 0)

    def _scaler_keep(self, world, bodies):
        """Pool Scaler's keep-score in a deck with `bodies` copies of the type its cost
        scales with. Isolates the term: the scaler shares no synergy tag or role with the
        bodies, so every other component of its keep-score is identical."""
        lines = ["1 Pool Scaler", "20 Swamp"]
        if bodies:
            lines.insert(1, f"{bodies} Pool Trigger Body")
        rows, *_ = deck.rank_cut_candidates(world(lines))
        return {r[1]: r[0] for r in rows}["Pool Scaler"]

    def test_cuts_consults_the_cost_scaling_co_signal(self, world):
        """WIRING anchor, the twin of the multiplier one above. A card the deck makes
        CHEAP is not filler — but both halves of the cut score price it at its printed
        cost, so only the co-signal can tell it apart, and only if it is consulted.
        Counts come from the calibration constant, never a literal."""
        n = deck._COST_SCALE_MIN_SOURCES + 6
        assert self._scaler_keep(world, n) > self._scaler_keep(world, 0)

    def test_a_scaler_the_deck_does_not_supply_gets_no_credit(self, world):
        below = deck._COST_SCALE_MIN_SOURCES - 1
        assert self._scaler_keep(world, below) == self._scaler_keep(world, 0)

    def test_functional_theme_options_returns_cards_carrying_the_theme(self, world):
        d = world(["1 Bear", "20 Swamp"], owned=["Pool Counters Guy"])
        names = [r[1] for r in deck.functional_theme_options(d, "counters")]
        assert "Pool Counters Guy" in names


class TestStructuralSuggesters:
    """The NEEDS model — the axes theme-based `suggest` is structurally blind to, since
    it filters candidates to cards sharing a synergy tag and a land rarely has one."""

    def test_suggest_lands_offers_a_land_that_produces_your_colour(self, world):
        d = world(["1 Bear", "20 Swamp"], owned=["Pool Dual", "Pool Offcolor Land"])
        res = deck.suggest_lands(d, owned=True)
        assert res["ok"] is True
        names = [p["name"] for p in res["picks"]]
        assert "Pool Dual" in names               # produces B

    def test_suggest_lands_excludes_an_off_colour_land(self, world):
        """A W/U land fixes nothing in a mono-B deck, so it must not be recommended."""
        d = world(["1 Bear", "20 Swamp"], owned=["Pool Dual", "Pool Offcolor Land"])
        names = [p["name"] for p in deck.suggest_lands(d, owned=True)["picks"]]
        assert "Pool Offcolor Land" not in names

    def test_suggest_mana_offers_repeatable_sources(self, world):
        d = world(["1 Big Bear", "20 Swamp"], owned=["Pool Dork", "Pool Rock"])
        needs = deck.deck_needs(d)
        names = [r["name"] for r in deck.suggest_mana(d, needs, owned=True)]
        assert "Pool Dork" in names or "Pool Rock" in names

    def test_suggest_mana_does_not_offer_a_creature_with_no_mana_ability(self, world):
        d = world(["1 Big Bear", "20 Swamp"], owned=["Pool Dork", "Pool Bear"])
        needs = deck.deck_needs(d)
        names = [r["name"] for r in deck.suggest_mana(d, needs, owned=True)]
        assert "Pool Bear" not in names

    def test_suggest_interaction_surfaces_removal(self, world):
        d = world(["4 Bear", "20 Swamp"], owned=["Pool Zap", "Pool Wrath"])
        needs = deck.deck_needs(d)
        names = [r["name"] for r in deck.suggest_interaction(d, needs, owned=True)]
        assert "Pool Zap" in names

    def test_suggest_interaction_surfaces_OFF_THEME_removal(self, world):
        """The whole point: theme-`suggest` filters to cards sharing a tag, so removal
        with no shared theme is invisible to it. This path must not do that."""
        d = world(["4 Pool Counters Guy", "20 Swamp"], owned=["Pool Zap"])
        needs = deck.deck_needs(d)
        names = [r["name"] for r in deck.suggest_interaction(d, needs, owned=True)]
        assert "Pool Zap" in names        # shares no theme with a counters deck


class TestRosterWideModels:
    def test_audit_roster_scores_every_deck(self, world):
        world(["1 Bear", "20 Swamp"], owned=["Pool Zap"])
        rows = deck.audit_roster()
        assert len(rows) == 1 and rows[0]["id"] == "90"
        assert rows[0]["verdict"] in ("TUNE", "craft", "review", "ok")

    def test_audit_roster_agrees_with_audit_deck(self, world):
        """`audit_roster` is a composition of `audit_deck`; the CLI and the dashboard both
        depend on them not diverging."""
        d = world(["1 Bear", "20 Swamp"], owned=["Pool Zap"])
        one = deck.audit_deck(d, by_name_qty=deck.load_collection()[2],
                              carddata=deck.load_card_data(), mana=deck.load_mana(),
                              leg=deck.load_legalities(), cmeta=deck.load_card_meta())
        assert deck.audit_roster()[0]["verdict"] == one["verdict"]

    def test_played_defaults_to_zero_with_no_record(self, world):
        """matches.csv is deliberately NOT an invariant — the project ran without one
        for its whole life — so its absence must be an ordinary zero, never a raise."""
        world(["1 Bear", "20 Swamp"], owned=["Pool Zap"])
        assert deck.load_match_counts() == {}
        assert deck.audit_roster()[0]["played"] == 0

    def _record(self, world, tmp_path, rows, header=None):
        import parse_matches as pm
        d = world(["1 Bear", "20 Swamp"], owned=["Pool Zap"])
        (tmp_path / "matches.csv").write_text(
            ",".join(header or pm.HEADER) + "\n" + "".join(r + "\n" for r in rows),
            encoding="utf-8")
        deck.load_match_counts.cache_clear()
        return d

    def test_played_counts_matches_per_deck(self, world, tmp_path):
        self._record(world, tmp_path, [
            "2026-08-07,m1,90,Arena Deck,guid,Av,Play,W,1,0,Av2,Success",
            "2026-08-07,m2,90,Arena Deck,guid,Av,Play,L,0,1,Av2,Success",
            "2026-08-07,m3,91,Other,guid2,Av,Play,W,1,0,Av2,Success"])
        assert deck.load_match_counts() == {"90": 2, "91": 1}
        assert deck.audit_roster()[0]["played"] == 2

    def test_an_unreadable_result_still_counts_as_played(self, world, tmp_path):
        """It counts ROWS, not results. A match with a mangled Result cell was still
        played, and this column's only job is 'has this deck been tested'."""
        self._record(world, tmp_path, [
            "2026-08-07,m1,90,A,g,Av,Play,,0,0,Av2,Success",
            "2026-08-07,m2,90,A,g,Av,Play,?,0,0,Av2,Success"])
        assert deck.load_match_counts() == {"90": 2}

    def test_an_unattributed_match_belongs_to_no_deck(self, world, tmp_path):
        self._record(world, tmp_path,
                     ["2026-07-27,m1,,,,Av,Play,L,0,1,Av2,Success"])
        assert deck.load_match_counts() == {}

    def test_a_pre_rename_csv_is_read_through_the_owning_module(self, world, tmp_path):
        """Delegating to `parse_matches.load_matches` rather than a local DictReader is
        what makes the avatar-column migration apply here for free. A second reader
        would have to re-implement it — and would silently not."""
        self._record(world, tmp_path,
                     ["2026-07-27,m1,90,Avatar_X,Play,L,0,1,Avatar_Y,Success"],
                     header=["Date", "Match ID", "Deck", "Course ID", "Event", "Result",
                             "Games Won", "Games Lost", "Opponent Course", "Reason"])
        assert deck.load_match_counts() == {"90": 1}

    def test_the_loader_reads_the_path_the_CACHE_is_watching(self, world, tmp_path):
        """`pm.load_matches()`' default binds MATCHES_CSV at DEFINITION time, so a bare
        call reads the real record forever while `_file_memo` keys on the repointed
        path. The two disagreeing is the stale-cache wiring bug `_file_memo`'s own
        docstring describes — and it made every fixture above pass against live data."""
        self._record(world, tmp_path,
                     ["2026-08-07,m1,90,A,g,Av,Play,W,1,0,Av2,Success"])
        assert deck.load_match_counts() == {"90": 1}
        (tmp_path / "matches.csv").unlink()
        deck.load_match_counts.cache_clear()
        assert deck.load_match_counts() == {}, "read a path the cache is not watching"

    def test_an_UNREADABLE_record_degrades_instead_of_raising(self, world, tmp_path):
        """The absent-file case never reaches the `except` — `load_matches` checks
        os.path.exists and returns []. So the degrade path had no test at all until a
        mutation pass replaced the handler with `raise` and every test stayed green.
        A directory where the CSV should be is the cheap real trigger (IsADirectoryError),
        and standing in for the whole class: an unreadable file, a permission error, a
        parse_matches that fails to import. None of them may take the roster audit down —
        matches.csv is optional data, and `audit` is the roster's triage surface."""
        world(["1 Bear", "20 Swamp"], owned=["Pool Zap"])
        (tmp_path / "matches.csv").mkdir()
        deck.load_match_counts.cache_clear()
        assert deck.load_match_counts() == {}
        assert deck.audit_roster()[0]["played"] == 0      # and the audit still runs

    def test_played_NEVER_reaches_the_verdict(self, world):
        """The load-bearing property. Outcome data at these sample sizes must not
        re-sort a structural triage: 2 games is noise, `--report` refuses to read it,
        and the same restraint keeps the protection axis (G-25) out of `tier_band`."""
        d = world(["1 Bear", "20 Swamp"], owned=["Pool Zap"])
        refs = dict(by_name_qty=deck.load_collection()[2], carddata=deck.load_card_data(),
                    mana=deck.load_mana(), leg=deck.load_legalities(),
                    cmeta=deck.load_card_meta())
        graded = [deck.audit_deck(d, **refs, played=p)
                  for p in ({}, {"90": 1}, {"90": 999})]
        scored = [{k: v for k, v in g.items() if k != "played"} for g in graded]
        assert scored[0] == scored[1] == scored[2]
        assert [g["played"] for g in graded] == [0, 1, 999]

    def test_audit_deck_still_works_without_the_played_kwarg(self, world):
        """build_dashboard.py calls audit_deck with explicit kwargs and does not pass
        this one; a required parameter would have broken the dashboard build."""
        d = world(["1 Bear", "20 Swamp"], owned=["Pool Zap"])
        r = deck.audit_deck(d, by_name_qty=deck.load_collection()[2],
                            carddata=deck.load_card_data(), mana=deck.load_mana(),
                            leg=deck.load_legalities(), cmeta=deck.load_card_meta())
        assert r["played"] == 0 and r["verdict"] in ("TUNE", "craft", "review", "ok")

    def test_an_empty_record_is_reported_as_a_GAP_not_as_zero_play(
            self, world, capsys):
        """A column of dots means either 'never played' or 'no record exists', and only
        one of those is about the decks. Saying which is the difference between a
        finding and a gap — the failure this subsystem already shipped once."""
        world(["1 Bear", "20 Swamp"], owned=["Pool Zap"])
        deck.cmd_audit(argparse.Namespace(flagged=False, by_tier=False))
        out = capsys.readouterr().out
        assert "Pld" in out
        assert "missing RECORD" in out and "not 99 untested decks" not in out.split("Pld")[0]

    def test_a_match_on_an_unknown_deck_id_is_flagged(self, world, tmp_path, capsys):
        """Orphaned counts are invisible in a per-deck table — they would just quietly
        stop appearing when a deck is renamed or deleted."""
        self._record(world, tmp_path, [
            "2026-08-07,m1,90,A,g,Av,Play,W,1,0,Av2,Success",
            "2026-08-07,m2,ZZ9,A,g,Av,Play,L,0,1,Av2,Success"])
        deck.cmd_audit(argparse.Namespace(flagged=False, by_tier=False))
        out = capsys.readouterr().out
        assert "unknown deck id" in out and "ZZ9" in out

    def test_brawl_readiness_reports_distance_per_deck(self, world):
        world(["4 Bear", "20 Swamp"], owned=["Pool Zap"])
        rows = deck.brawl_readiness()
        assert len(rows) == 1
        row = rows[0]
        assert row["id"] == "90" and isinstance(row["distance"], int)

    def test_brawl_readiness_counts_duplicates_as_distance(self, world):
        """Brawl is singleton, so 4 copies of a card is 3 cards to trim — the dominant
        term in 'how far is this from a legal conversion'."""
        world(["4 Bear", "20 Swamp"], owned=["Pool Zap"])
        many = deck.brawl_readiness()[0]
        world(["1 Bear", "20 Swamp"], owned=["Pool Zap"])
        few = deck.brawl_readiness()[0]
        assert many["dup"] > few["dup"]


class TestPoolStaleness:
    """`suggest` warns when the pool's legality snapshot is old. The degrade path matters
    more than the happy one: a missing or malformed sidecar must read as "unknown", not
    crash and not silently report 0 days (which would suppress the warning forever)."""

    def test_reads_the_sidecar(self, tmp_path, monkeypatch):
        import datetime
        stamp = tmp_path / "card-pool.build"
        stamp.write_text((datetime.date.today()
                          - datetime.timedelta(days=5)).isoformat(), encoding="utf-8")
        monkeypatch.setattr(deck, "POOL_BUILD_STAMP", str(stamp))
        assert deck.pool_staleness_days() == 5

    def test_a_missing_sidecar_is_unknown_not_zero(self, tmp_path, monkeypatch):
        monkeypatch.setattr(deck, "POOL_BUILD_STAMP", str(tmp_path / "nope"))
        assert deck.pool_staleness_days() is None

    def test_a_malformed_sidecar_is_unknown_not_a_crash(self, tmp_path, monkeypatch):
        stamp = tmp_path / "card-pool.build"
        stamp.write_text("not a date", encoding="utf-8")
        monkeypatch.setattr(deck, "POOL_BUILD_STAMP", str(stamp))
        assert deck.pool_staleness_days() is None


class TestTierConsistency:
    """The soft roster warning: a claimed `#: tier:` letter two or more bands above the
    tier its measurable vector supports is inflated or stale. Never auto-assigns — it
    only flags a letter to re-grade, since tier is a human judgement."""

    def _deck(self, synth, tier, lines):
        return synth(lines, header=f"#: name: Synth\n#: format: standard\n"
                                   f"#: colors: B\n#: tier: {tier} — synthetic\n")

    def test_an_ungraded_deck_does_not_mismatch(self, synth):
        d = synth(["2 Zap", "20 Swamp"])
        claimed, _implied, mismatch, _msg = deck.tier_consistency(d)
        assert claimed in ("", None) and mismatch is False

    def test_a_wildly_inflated_letter_is_flagged(self, synth):
        """S claimed on a deck with no interaction and no card advantage."""
        d = self._deck(synth, "S", ["8 Bear", "20 Swamp"])
        _claimed, _implied, mismatch, msg = deck.tier_consistency(d)
        assert mismatch is True and msg

    def test_a_defensible_letter_is_not_flagged(self, synth):
        """One band above the floor is fine — that band credits the intangibles the
        metrics can't see, which is why only >=2 bands is reported."""
        d = self._deck(synth, "D", ["8 Bear", "20 Swamp"])
        _claimed, _implied, mismatch, _msg = deck.tier_consistency(d)
        assert mismatch is False


class TestXCostCards:
    """An {X} spell is priced at MV 1 because X counts as 0 off the stack. That is
    correct for castability and cast-on-curve probability, and WRONG as a curve
    reading — it books a card you cast for four as a one-drop. `x_cost_cards` is the
    report-only flag that says so; it must never feed the quality vector, because a
    new term in `tier_band` would silently re-grade the roster."""

    CD = {
        "wildwood scourge": {"type": "Creature — Hydra", "text": "enters with X +1/+1 counters"},
        "bear": {"type": "Creature — Bear", "text": ""},
        "forest": {"type": "Basic Land — Forest", "text": ""},
        "lumbering worldwagon": {"type": "Artifact — Vehicle", "text": ""},
    }
    MANA = {
        "wildwood scourge": ("{X}{G}", 1),
        "bear": ("{1}{G}", 2),
        "lumbering worldwagon": ("{2}{G}", 3),
    }

    @staticmethod
    def _cards(names):
        return [(1, n, "SET", "1") for n in names]

    def test_an_x_spell_is_flagged_with_its_printed_cost(self):
        out = deck.x_cost_cards(self._cards(["Wildwood Scourge", "Bear"]), self.CD, self.MANA)
        assert out == [("Wildwood Scourge", "{X}{G}")]

    def test_a_fixed_cost_card_is_not_flagged(self):
        out = deck.x_cost_cards(self._cards(["Bear", "Lumbering Worldwagon"]), self.CD, self.MANA)
        assert out == []

    def test_lands_and_duplicates_are_excluded(self):
        """A land has no curve slot, and a 4-of should report once, not four times."""
        cards = self._cards(["Wildwood Scourge", "Wildwood Scourge", "Forest"])
        assert deck.x_cost_cards(cards, self.CD, self.MANA) == [("Wildwood Scourge", "{X}{G}")]

    def test_the_flag_does_not_reach_the_quality_vector(self):
        """Report-only by design — `tier_band` must not see it (see the protection axis)."""
        import inspect
        src = inspect.getsource(deck.deck_quality_vector) + inspect.getsource(deck.tier_band)
        assert "x_cost_cards" not in src


class TestQualityVectorOwnership:
    """BS2-22: deck_quality_vector compared ownership per LINE, the exact bug
    cmd_list records as fixed and cmd_check aggregates against — a card split
    across two printing lines read buildable while `check` said short, and
    preflight folds `buildable` into its READY/BLOCKED verdict."""

    def test_a_card_split_across_lines_compares_its_total(self, world):
        # 3 + 2 = 5 needed against 4 owned: per-line (4>=3, 4>=2) read buildable.
        d = world(["3 Pool Zap", "2 Pool Zap", "20 Swamp"], owned=["Pool Zap"])
        vec = deck.deck_quality_vector(d)
        assert vec["buildable"] is False

    def test_an_unsplit_deck_is_unchanged(self, world):
        d = world(["4 Pool Zap", "20 Swamp"], owned=["Pool Zap"])
        assert deck.deck_quality_vector(d)["buildable"] is True


class TestBatch4Corrections:
    """Batch 4's small correctness set — each a documented rule applied in one place and
    not another, so the failure is two surfaces disagreeing rather than a crash."""

    def test_power_threshold_counts_a_printed_zero(self):
        """BS4-32: `card_power(...) or -1` collapses a printed 0 to unknown. Every
        X-creature is 0/0, so a "power 0 or greater" gate must still count them — and the
        idiom sat in the very function G-16 documents the rule for."""
        cd = {
            "zero body": {"name": "Zero Body", "type": "Creature — Elemental",
                          "text": "", "power": "0", "toughness": "0"},
            "payoff": {"name": "Payoff", "type": "Enchantment",
                       "text": "Whenever a creature you control with power 0 or greater "
                               "enters, draw a card.", "power": "", "toughness": ""},
        }
        cards = [(1, "Zero Body", "TST", "1"), (1, "Payoff", "TST", "2")]
        flags = deck.power_threshold_flags(cards, cd)
        # The 0/0 body MEETS a 0-bar, so the payoff must NOT be reported as under-supported.
        assert all(f[0] != "Payoff" for f in flags), flags

    def test_deck_shape_does_not_call_a_creatureless_deck_TALL(self):
        """BS4-33: the `creatures <= 14` nudge fired unconditionally, so a 0-creature
        spells deck scored tall 2 and printed "TALL — few bodies, effects that scale one
        creature UP" with an EMPTY tall-cards list. The honest verdict was unreachable."""
        shape = deck.deck_shape([], {}, {})
        assert shape["creatures"] == 0
        assert "TALL" not in shape["axis"]
        assert shape["axis"] == "no board-growth axis"


class TestTaggerSeesTypesTheCardOnlyTALKSAbout:
    """Two holes of one family, both found by a card returning NO home at all.

    `_TRIBAL_PAYOFF_RES` demanded `search your library for a X card`, so Last Light of
    Durin's Day — "search your hand and/or library for a Dragon card" — carried no
    Dragon theme and never reached the roster's 23-Mountain, 18-Dragon deck. And card
    TYPES are excluded from the tribal path by design (they are types, not tribes)
    while `TYPE_TAGS` reads only the TYPE LINE, so a card that CARES about a type had
    no tag for it: Canyon Vaulter's themes were `Kor, Pilot` while "saddles a Mount or
    crews a Vehicle" — the entire card — was invisible, and `suggest-homes` returned
    zero decks. That is K-03's stated Gilgamesh residual.

    Measured old-vs-new across all 16,067 pool rows: 180 cards change, 196 tags gained,
    NOTHING lost."""

    def _tags(self, type_line, text):
        import tag_synergies
        return set(tag_synergies.tags_for({"Type": type_line, "Card Text": text}))

    def test_a_tutor_that_searches_hand_and_library_still_names_its_tribe(self):
        tags = self._tags("Enchantment",
                          "If it has six or more quest counters on it, sacrifice it. "
                          "If you do, search your hand and/or library for a Dragon card "
                          "and put it onto the battlefield.")
        assert "Dragon" in tags

    def test_a_card_that_only_interacts_with_a_type_carries_that_type(self):
        tags = self._tags("Creature — Kor Pilot",
                          "Whenever this creature saddles a Mount or crews a Vehicle "
                          "during your main phase, that Mount or Vehicle gains flying "
                          "until end of turn.")
        assert {"Mount", "Vehicle"} <= tags

    def test_MOUNTAIN_IS_NOT_A_MOUNT(self):
        """`'Mount' in type_line` matches 'Mountain' — the substring trap `card_colors`
        documents one file over, and it bit the ad-hoc count that measured this fix
        (24 Mounts reported in a deck holding one). The patterns use \\b for exactly
        this reason; a basic land must never read as a Mount."""
        assert "Mount" not in self._tags("Basic Land — Mountain", "({T}: Add {R}.)")
        assert "Mount" not in self._tags(
            "Sorcery", "Search your library for a Mountain card, then shuffle.")

    def test_basic_land_types_still_tag_their_land_matters_payoffs(self):
        """Suppressing basic types globally was TRIED and measured wrong: it minted zero
        new tags to prevent and silently stripped 28 real payoffs (Corrupt, Tendrils of
        Corruption, Gates Ablaze, Eluge). The count settled it, not the reasoning."""
        assert "Swamp" in self._tags(
            "Sorcery", "Corrupt deals damage to any target equal to the number of "
                       "Swamps you control. You gain that much life.")


class TestCheatCostCards:
    """The mirror of `x_cost_cards`: the curve, `avg_mv` and `_clock_score` read the
    PRINTED cost, so a Warp / Plot / Foretell body books at a price you never pay —
    Bygone Colossus (Warp {3}) reads as a nine-drop and on its own moved 56b's aggro floor
    A -> B (pile analysis §5.7 item 6). Report-only by the same G-60 discipline. Fixtures
    are the cards' REAL text (G-67)."""

    CD = {
        "bygone colossus": {"type": "Artifact Creature — Robot Giant",
                            "text": "Warp {3} (You may cast this card from your hand for its "
                                    "warp cost. Exile this creature at the beginning of the next "
                                    "end step, then you may cast it from exile on a later turn.)"},
        "stingerback terror": {"type": "Creature — Scorpion Dragon",
                               "text": "Flying, trample\nThis creature gets -1/-1 for each card "
                                       "in your hand.\nPlot {2}{R} (You may pay {2}{R} and exile "
                                       "this card from your hand. Cast it as a sorcery on a later "
                                       "turn without paying its mana cost. Plot only as a sorcery.)"},
        "tannuk, steadfast second": {"type": "Legendary Creature — Kavu Pilot",
                                     "text": "Other creatures you control have haste.\nArtifact "
                                             "cards and red creature cards in your hand have warp "
                                             "{2}{R}. (You may cast a card from your hand for its "
                                             "warp cost.)"},
        "bear": {"type": "Creature — Bear", "text": ""},
        "forest": {"type": "Basic Land — Forest", "text": ""},
    }
    MANA = {
        "bygone colossus": ("{9}", 9),
        "stingerback terror": ("{3}{R}", 4),
        "tannuk, steadfast second": ("{2}{R}", 3),
        "bear": ("{1}{G}", 2),
    }

    @staticmethod
    def _cards(names):
        return [(1, n, "SET", "1") for n in names]

    def test_a_warp_body_is_flagged_with_both_costs(self):
        out = deck.cheat_cost_cards(self._cards(["Bygone Colossus", "Bear"]), self.CD, self.MANA)
        assert out == [("Bygone Colossus", "{9}", "warp", "{3}", 3)]

    def test_plot_is_priced_from_the_keyword_not_the_reminder_text(self):
        # Plot's reminder quotes the cost again ("You may pay {2}{R}"); the keyword line is
        # what is read, and MV 3 < 4 flags it.
        out = deck.cheat_cost_cards(self._cards(["Stingerback Terror"]), self.CD, self.MANA)
        assert out == [("Stingerback Terror", "{3}{R}", "plot", "{2}{R}", 3)]

    def test_a_card_that_GRANTS_warp_is_not_itself_cheaper(self):
        # Tannuk's own cost is {2}{R}; "have warp {2}{R}" reduces his targets, not him.
        assert deck.cheat_cost_cards(self._cards(["Tannuk, Steadfast Second"]),
                                     self.CD, self.MANA) == []

    def test_fixed_cost_cards_lands_and_duplicates_are_excluded(self):
        cards = self._cards(["Bear", "Forest", "Bygone Colossus", "Bygone Colossus"])
        out = deck.cheat_cost_cards(cards, self.CD, self.MANA)
        assert [n for n, *_r in out] == ["Bygone Colossus"]

    def test_the_flag_does_not_reach_the_quality_vector(self):
        """Report-only by design — `tier_band` must not see it (the X-cost rule, in reverse)."""
        import inspect
        src = (inspect.getsource(deck.deck_quality_vector) + inspect.getsource(deck.tier_band)
               + inspect.getsource(deck._clock_score))
        assert "cheat_cost_cards" not in src


class TestLandUtilityTieBreak:
    """`suggest --lands` scores FIXING and nothing read the rider, so Temple of Triumph,
    Boros Guildgate, Sun-Blessed Peak and Wind-Scarred Crag tied at 10.9 (2026-09-06). The
    rider is a SORT-KEY tie-break, never a score term: the smallest fixing step between
    land classes is 0.1, so any additive nudge would re-rank lands on something other than
    fixing. Real land text (G-67)."""

    TEMPLE = ("This land enters tapped.\nWhen this land enters, scry 1. (Look at the top card "
              "of your library. You may put that card on the bottom.)\n{T}: Add {R} or {W}.")
    PEAK = "This land enters tapped.\n{T}: Add {R} or {W}.\n{4}, {T}, Sacrifice this land: Draw a card."
    GATE = "This land enters tapped.\n{T}: Add {R} or {W}."
    BLUFFS = ("This land enters tapped.\nWhen this land enters, it deals 1 damage to target "
              "opponent.\n{T}: Add {R} or {W}.")
    CRAG = "This land enters tapped.\nWhen this land enters, you gain 1 life.\n{T}: Add {R} or {W}."
    RIDGE = ("This land enters tapped.\n{T}: Add {R} or {G}.\n{2}{R}{G}: This land becomes a 3/4 "
             "red and green Dinosaur creature until end of turn. It's still a land.")
    PARLOR = ("({T}: Add {R} or {W}.)\nThis land enters tapped.\nWhen this land enters, surveil "
              "1. (Look at the top card of your library. You may put it into your graveyard.)")

    def test_each_rider_is_read_and_a_vanilla_dual_scores_zero(self):
        assert deck._land_utility(self.GATE) == (0.0, "")
        assert deck._land_utility(self.TEMPLE) == (0.30, "scry")
        assert deck._land_utility(self.PARLOR) == (0.30, "surveil")
        assert deck._land_utility(self.PEAK) == (0.40, "draw")
        assert deck._land_utility(self.BLUFFS) == (0.20, "ping")
        assert deck._land_utility(self.CRAG) == (0.10, "life")
        assert deck._land_utility(self.RIDGE) == (0.40, "creature")

    def test_the_rider_is_bounded_and_reminder_text_is_ignored(self):
        assert all(v <= 0.4 for v, _l, _rx in deck._LAND_UTILITY_CUES)
        # Only the reminder mentions scrying — no ability does.
        assert deck._land_utility("{T}: Add {G}. (Scry 1 is not something this land does.)") == (0.0, "")

    def test_tie_break_orders_equal_scores_by_rider_and_never_crosses_a_score(self):
        picks = [
            {"name": "Boros Guildgate", "score": 10.9, "util": 0.0},
            {"name": "Sun-Blessed Peak", "score": 10.9, "util": 0.4},
            {"name": "Temple of Triumph", "score": 10.9, "util": 0.3},
            {"name": "Blazemire Verge", "score": 9.1, "util": 0.0},
            {"name": "Kavaron, Memorial World", "score": 8.8, "util": 0.4},   # rider, lower score
        ]
        picks.sort(key=lambda p: (-p["score"], -p["util"], p["name"].lower()))
        assert [p["name"] for p in picks] == ["Sun-Blessed Peak", "Temple of Triumph",
                                              "Boros Guildgate", "Blazemire Verge",
                                              "Kavaron, Memorial World"]

    def test_the_live_recommender_keeps_util_out_of_the_score(self):
        d = deck.find_deck("56")
        if not d:                                   # roster-dependent
            return
        res = deck.suggest_lands(d, owned=True, limit=0)
        for p in res["picks"]:
            assert p["score"] == round(p["fix"] + p["syn"] + p["short"], 2), p["name"]
            assert "util" in p and 0.0 <= p["util"] <= 0.4
        scores = [p["score"] for p in res["picks"]]
        assert scores == sorted(scores, reverse=True)      # score order is untouched


class TestCheatCostGrantsAndEffectiveCurve:
    """Follow-ons to `cheat_cost_cards`: a card that GRANTS an alternative cost (Tannuk)
    is named, and the curve the deck would have with alt costs substituted is reported —
    both report-only, the vector keeps the printed curve."""

    CD = dict(TestCheatCostCards.CD)
    MANA = dict(TestCheatCostCards.MANA)

    @staticmethod
    def _cards(names, q=1):
        return [(q, n, "SET", "1") for n in names]

    def test_a_grant_is_named_with_its_scope(self):
        out = deck.cheat_cost_grants(self._cards(["Tannuk, Steadfast Second", "Bear"]), self.CD)
        assert out == [("Tannuk, Steadfast Second", "warp", "{2}{R}",
                        "Artifact cards and red creature cards in your hand")]

    def test_a_card_with_its_own_warp_is_not_a_grant(self):
        assert deck.cheat_cost_grants(self._cards(["Bygone Colossus"]), self.CD) == []

    def test_effective_avg_mv_substitutes_alt_costs_and_is_quantity_weighted(self):
        cards = [(1, "Bygone Colossus", "SET", "1"), (3, "Bear", "SET", "1"), (1, "Forest", "SET", "1")]
        eff, printed, with_grants = deck.effective_avg_mv(cards, self.CD, self.MANA)
        assert printed == round((9 + 3 * 2) / 4, 2)
        assert eff == round((3 + 3 * 2) / 4, 2)
        assert with_grants is None                      # no grant in this list

    def test_a_grant_is_applied_to_the_cards_in_its_scope_only(self):
        cd = dict(self.CD)
        cd["red dragon"] = {"type": "Creature — Dragon", "text": "Flying", "colors": "R"}
        cd["green bear"] = {"type": "Creature — Bear", "text": "", "colors": "G"}
        cd["rock"] = {"type": "Artifact", "text": "", "colors": ""}
        mana = dict(self.MANA, **{"red dragon": ("{4}{R}", 5), "green bear": ("{4}{G}", 5),
                                  "rock": ("{5}", 5)})
        cards = [(1, "Tannuk, Steadfast Second", "", ""), (1, "Red Dragon", "", ""),
                 (1, "Green Bear", "", ""), (1, "Rock", "", "")]
        eff, printed, with_grants = deck.effective_avg_mv(cards, cd, mana)
        # Tannuk 3 + dragon 5 + bear 5 + rock 5 = 18/4; the grant (warp {2}{R} = 3) reaches
        # the red creature and the artifact, never the green bear: 3 + 3 + 5 + 3 = 14/4.
        assert printed == 4.5 and eff == 4.5 and with_grants == 3.5

    def test_grant_scope_parsing_needs_a_known_type(self):
        assert deck._grant_scope_matches("artifact cards and red creature cards in your hand",
                                         {"type": "Creature — Dragon", "colors": "R"})
        assert not deck._grant_scope_matches("artifact cards and red creature cards in your hand",
                                             {"type": "Creature — Bear", "colors": "G"})
        assert not deck._grant_scope_matches("cards in your hand", {"type": "Creature", "colors": "R"})

    def test_no_cheat_cost_card_means_no_advisory(self):
        assert deck.effective_avg_mv(self._cards(["Bear"]), self.CD, self.MANA) is None

    def test_neither_reaches_the_vector_or_the_floor(self):
        import inspect
        src = (inspect.getsource(deck.deck_quality_vector) + inspect.getsource(deck.tier_band)
               + inspect.getsource(deck._clock_score))
        assert "effective_avg_mv" not in src and "cheat_cost_grants" not in src
        assert "_grant_scope_matches" not in src


class TestTypedSinkLabel:
    IRON_HILLS = ("This land enters tapped.\n{T}: Add {R} or {W}.\n{2}{R}{W}, {T}, Sacrifice this "
                  "land: Put two +1/+1 counters on target Dwarf you control. Activate only as a sorcery.")
    MANSION = "This land enters tapped.\n{T}: Add {R} or {G}.\n{4}, {T}: Surveil 1."

    def test_a_type_restricted_sink_is_labelled_and_worth_the_same_tiebreak(self):
        assert deck._land_utility(self.IRON_HILLS) == (0.30, "sink~")
        assert deck._land_utility(self.MANSION) == (0.30, "sink")
