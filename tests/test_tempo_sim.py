"""Pins `deck.simulate_tempo` / `sim_land_model` — the land-drop simulation behind
`consistency --tempo` (2026-10-28).

The access table `consistency` prints is a closed-form hypergeometric; this is a Monte
Carlo, so its tests check STRUCTURE (a deck with no tapped land costs nothing, taplands
cost something, a gate reads the lands in play) and agreement with the closed form where
the two answer the same question, rather than exact numbers. Oracle text is real (G-67)."""
import math

import deck as D

THRIVING_MOOR = ("This land enters tapped. As it enters, choose a color other than black.\n"
                 "{T}: Add {B} or one mana of the chosen color.")
SPIREBLUFF = ("This land enters tapped unless you control two or fewer other lands.\n"
              "{T}: Add {U} or {R}.")
BLAZEMIRE = "{T}: Add {B}.\n{T}: Add {R}. Activate only if you control a Swamp or a Mountain."
WILDS = ("{T}, Sacrifice this land: Search your library for a basic land card, put it onto "
         "the battlefield tapped, then shuffle.")
RAZORTRAP = "This land enters tapped unless a player has 13 or less life.\n{T}: Add {B} or {R}."
BLOOD_CRYPT = ("({T}: Add {B} or {R}.)\nAs this land enters, you may pay 2 life. If you "
               "don't, it enters tapped.")
STARTING_TOWN = ("This land enters tapped unless it's your first, second, or third turn of "
                 "the game.\n{T}: Add {C}.\n{T}, Pay 1 life: Add one mana of any color.")
DRAGONSKULL = ("This land enters tapped unless you control a Swamp or a Mountain.\n"
               "{T}: Add {B} or {R}.")
DREAMROOT = ("This land enters tapped unless you control two or more other lands.\n"
             "{T}: Add {G} or {U}.")
SNARL = ("As this land enters, you may reveal a Forest or Island card from your hand. If you "
         "don't, this land enters tapped.\n{T}: Add {G} or {U}.")

B, R, G, U = D._COLOR_BIT["B"], D._COLOR_BIT["R"], D._COLOR_BIT["G"], D._COLOR_BIT["U"]


def _basic(name):
    return D.sim_land_model(name, "", "Basic Land")


class TestLandModel:
    def test_enter_kinds_read_from_text(self):
        kinds = {
            "Thriving Moor": D.sim_land_model("Thriving Moor", THRIVING_MOOR, "Land")["enter"],
            "Spirebluff Canal": D.sim_land_model("Spirebluff Canal", SPIREBLUFF, "Land")["enter"],
            "Razortrap Gorge": D.sim_land_model("Razortrap Gorge", RAZORTRAP, "Land")["enter"],
            "Blood Crypt": D.sim_land_model("Blood Crypt", BLOOD_CRYPT,
                                            "Land — Swamp Mountain", "B/R")["enter"],
            "Starting Town": D.sim_land_model("Starting Town", STARTING_TOWN,
                                              "Land — Town")["enter"],
            "Dragonskull Summit": D.sim_land_model("Dragonskull Summit", DRAGONSKULL,
                                                   "Land")["enter"],
            "Dreamroot Cascade": D.sim_land_model("Dreamroot Cascade", DREAMROOT,
                                                  "Land")["enter"],
            "Vineglimmer Snarl": D.sim_land_model("Vineglimmer Snarl", SNARL, "Land")["enter"],
            "Blazemire Verge": D.sim_land_model("Blazemire Verge", BLAZEMIRE, "Land")["enter"],
        }
        assert kinds == {"Thriving Moor": "tapped", "Spirebluff Canal": "fast",
                         "Razortrap Gorge": "board", "Blood Crypt": "shock",
                         "Starting Town": "early", "Dragonskull Summit": "check",
                         "Dreamroot Cascade": "slow", "Vineglimmer Snarl": "reveal",
                         "Blazemire Verge": "untapped"}

    def test_verge_second_colour_is_gated(self):
        m = D.sim_land_model("Blazemire Verge", BLAZEMIRE, "Land")
        assert m["free"] == B
        assert m["gated"] == [(R, B | R)]

    def test_fetch_finds_a_tapped_basic(self):
        m = D.sim_land_model("Evolving Wilds", WILDS, "Land")
        assert m["fetch"] == 31 and m["fetch_tapped"]
        assert not D._sim_enters_untapped(m, [], 3, [])


class TestEntryConditions:
    def test_checkland_reads_the_lands_in_play(self):
        summit = D.sim_land_model("Dragonskull Summit", DRAGONSKULL, "Land")
        assert not D._sim_enters_untapped(summit, [_basic("Forest")], 2, [])
        assert D._sim_enters_untapped(summit, [_basic("Swamp")], 2, [])
        crypt = D.sim_land_model("Blood Crypt", BLOOD_CRYPT, "Land — Swamp Mountain", "B/R")
        assert D._sim_enters_untapped(summit, [crypt], 2, [])   # a TYPE, not a basic

    def test_fast_and_slow_are_opposite(self):
        fast = D.sim_land_model("Spirebluff Canal", SPIREBLUFF, "Land")
        slow = D.sim_land_model("Dreamroot Cascade", DREAMROOT, "Land")
        two = [_basic("Island"), _basic("Forest")]
        three = two + [_basic("Island")]
        assert D._sim_enters_untapped(fast, two, 3, []) and not D._sim_enters_untapped(fast, three, 4, [])
        assert not D._sim_enters_untapped(slow, two[:1], 2, []) and D._sim_enters_untapped(slow, two, 3, [])

    def test_snarl_needs_the_type_in_hand(self):
        snarl = D.sim_land_model("Vineglimmer Snarl", SNARL, "Land")
        assert D._sim_enters_untapped(snarl, [], 1, [_basic("Forest")])
        assert not D._sim_enters_untapped(snarl, [], 1, [_basic("Swamp")])

    def test_verge_gate_needs_another_land(self):
        verge = D.sim_land_model("Blazemire Verge", BLAZEMIRE, "Land")
        assert D._sim_mana_masks([verge]) == [B]
        assert D._sim_mana_masks([verge, _basic("Mountain")])[0] == B | R


class TestPayable:
    def test_one_land_makes_one_mana(self):
        # The access model counts a dual for both colours; paying {B}{R} needs two lands.
        assert not D._sim_payable([B | R], 2, ((B, 1), (R, 1)))
        assert D._sim_payable([B | R, B | R], 2, ((B, 1), (R, 1)))
        assert not D._sim_payable([B | R, U], 2, ((B, 1), (R, 1)))

    def test_generic_needs_land_count(self):
        assert not D._sim_payable([B, B], 3, ((B, 1),))
        assert D._sim_payable([B, B, U], 3, ((B, 2),))


def _deck(lands, nonland=64):
    return lands + [None] * nonland


class TestSimulation:
    REQS = {"4-drop": (4, 4, ((B, 1),)), "2-drop": (2, 2, ((B, 1),))}

    def test_all_untapped_deck_costs_nothing(self):
        deck = _deck([_basic("Swamp")] * 36)
        res = D.simulate_tempo(deck, self.REQS, games=600, seed=1)
        assert res["tempo"] == res["untapped"]
        assert res["mana_tempo"] == res["mana_untapped"]

    def test_taplands_cost_tempo(self):
        moor = D.sim_land_model("Thriving Moor", THRIVING_MOOR, "Land")
        deck = _deck([moor] * 20 + [_basic("Swamp")] * 16)
        res = D.simulate_tempo(deck, self.REQS, games=600, seed=1)
        for k in self.REQS:
            assert res["tempo"][k] < res["untapped"][k]

    def test_untapped_land_drops_match_the_closed_form(self):
        # With no tapped land, "T untapped mana on turn T" is "T lands among the cards seen",
        # the figure `opening_land_stats` prints as land-drop consistency.
        deck = _deck([_basic("Swamp")] * 36)
        res = D.simulate_tempo(deck, self.REQS, games=4000, seed=7)
        seen = D.cards_seen(4, True)
        exact = sum(math.comb(36, k) * math.comb(64, seen - k) for k in range(4, seen + 1)) \
            / math.comb(100, seen)
        assert abs(res["mana_untapped"][4] - exact) < 0.03

    def test_deterministic_for_a_seed(self):
        moor = D.sim_land_model("Thriving Moor", THRIVING_MOOR, "Land")
        deck = _deck([moor] * 10 + [_basic("Swamp")] * 26)
        a = D.simulate_tempo(deck, self.REQS, games=300, seed=5)
        b = D.simulate_tempo(deck, self.REQS, games=300, seed=5)
        assert a == b
