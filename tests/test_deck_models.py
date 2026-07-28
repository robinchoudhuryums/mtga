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
]


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
                            "Legalities": "standard", "Released": "2024-01-01"})
        ddir = tmp_path / "90-synth"
        ddir.mkdir(exist_ok=True)
        (ddir / "deck.txt").write_text(
            f"#: name: Synth\n#: format: Standard\n#: colors: {colors}\n\n"
            + "\n".join(deck_lines) + "\n", encoding="utf-8")

        carddata = {n.lower(): _card(n, ty, tx, col) for n, ty, tx, col, _t, _r in POOL_CARDS}
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
                            lambda: {n.lower(): {"standard"} for n, *_ in POOL_CARDS})
        monkeypatch.setattr(deck, "load_collection",
                            lambda: ({}, {}, {n.lower(): 4 for n in owned}))
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
