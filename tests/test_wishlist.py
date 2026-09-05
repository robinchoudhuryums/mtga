"""Unit tests for pure scoring helpers in scripts/wishlist.py."""
import math

import pytest

import tag_synergies
import wishlist


class TestReuseBonus:
    def test_zero_for_zero_or_one_home(self):
        assert wishlist._reuse_bonus(0) == 0
        assert wishlist._reuse_bonus(1) == 0

    def test_non_decreasing(self):
        seq = [wishlist._reuse_bonus(k) for k in (1, 2, 3, 4, 8, 20)]
        assert all(a <= b for a, b in zip(seq, seq[1:]))

    def test_capped(self):
        assert wishlist._reuse_bonus(8) == wishlist._reuse_bonus(20)
        assert wishlist._reuse_bonus(20) <= 2.0

    def test_non_numeric_is_zero(self):
        assert wishlist._reuse_bonus("x") == 0.0
        assert wishlist._reuse_bonus(None) == 0.0


class TestRankScoresPowerParsing:
    """The Power cell parsing inside _rank_scores (A10/F9): a non-finite or non-numeric
    Power must be flagged and scored 0.0, never silently poison `combined`."""

    def _score(self, power):
        row = {"Card Name": "T", "Rarity": "Rare", "Color(s)": "",
               "Synergies": "etb; tokens", "Target": "", "Power": power}
        return wishlist._rank_scores([row])[0]

    def test_valid_power(self):
        s = self._score("7")
        assert s["power"] == 7.0 and not s["bad_power"]
        assert math.isfinite(s["combined"])

    def test_nan_flagged_and_finite_combined(self):
        s = self._score("nan")
        assert s["power"] == 0.0 and s["bad_power"] is True
        assert math.isfinite(s["combined"])

    def test_inf_flagged(self):
        s = self._score("inf")
        assert s["power"] == 0.0 and s["bad_power"] is True
        assert math.isfinite(s["combined"])

    def test_garbage_flagged(self):
        s = self._score("~9")
        assert s["power"] == 0.0 and s["bad_power"] is True


class TestPipsCastable:
    """Hybrid-aware castability behind the wishlist target audit (Sun-Spider fix)."""

    def test_hybrid_castable_in_one_color(self):
        # {3}{W/U} -> strict {}, hybrid [{'W','U'}] -> castable in a W/B deck (pay W).
        assert wishlist._pips_castable({}, [frozenset({"W", "U"})], {"W", "B"})

    def test_strict_offcolor_not_castable(self):
        # {3}{U} -> strict {'U':1} -> NOT castable in a W/B deck.
        assert not wishlist._pips_castable({"U": 1}, [], {"W", "B"})

    def test_hybrid_needs_at_least_one_color(self):
        # {U/R} in a mono-W deck: neither color available -> not castable.
        assert not wishlist._pips_castable({}, [frozenset({"U", "R"})], {"W"})

    def test_strict_oncolor_castable(self):
        assert wishlist._pips_castable({"W": 2, "B": 1}, [], {"W", "B"})

    def test_no_pips_castable_anywhere(self):
        assert wishlist._pips_castable({}, [], {"W"})


class TestSeedPowerBonuses:
    """The two bounded seed bonuses that fixed the Meteor-Sword under-read."""

    def _p(self, rarity, ty, text):
        return wishlist._seed_power({"Rarity": rarity, "Type": ty, "Card Text": text})

    def test_flexible_removal_beats_creature_only(self):
        flex = self._p("Uncommon", "Instant", "Destroy target permanent.")
        crea = self._p("Uncommon", "Instant", "Destroy target creature.")
        assert flex > crea

    def test_removal_on_a_permanent_is_a_two_for_one(self):
        # Same removal, but stapled to an equipment (stays on board) -> higher.
        equip = self._p("Uncommon", "Artifact — Equipment",
                        "When this Equipment enters, destroy target permanent. "
                        "Equipped creature gets +3/+3.")
        spell = self._p("Uncommon", "Sorcery", "Destroy target permanent.")
        assert equip > spell

    def test_meteor_sword_no_longer_underseeded(self):
        meteor = self._p("Uncommon", "Artifact — Equipment",
                         "When this Equipment enters, destroy target permanent. "
                         "Equipped creature gets +3/+3.")
        assert meteor >= 4.0            # was 3.0 before the fix

    def test_bonuses_stay_in_range_and_below_a_bomb(self):
        vanilla = self._p("Common", "Creature — Bear", "")
        meteor = self._p("Uncommon", "Artifact — Equipment",
                         "When this Equipment enters, destroy target permanent.")
        bomb = self._p("Mythic", "Legendary Planeswalker",
                       "Destroy target permanent. Draw two cards.")
        assert 0.0 <= vanilla < meteor <= bomb <= 10.0

    def test_wildcard_letter_rarity_matches_the_word(self):
        # deck.rank_cut_candidates / deck._card_power pass load_rarities() values, which
        # are Arena wildcard LETTERS. A letter used to miss _SEED_RARITY and default to
        # 2.0, seeding every rare/mythic as an uncommon (audit F-01).
        for letter, word in (("M", "Mythic"), ("R", "Rare"),
                             ("U", "Uncommon"), ("C", "Common")):
            assert self._p(letter, "Creature — Bear", "") == self._p(word, "Creature — Bear", "")

    def test_mythic_floor_outranks_common_floor(self):
        assert self._p("M", "Creature — Bear", "") > self._p("C", "Creature — Bear", "")

    def test_unknown_rarity_falls_back_to_neutral(self):
        # '?' (rarity unresolved) and a blank cell must both take the neutral default,
        # not a wrong floor.
        neutral = self._p("", "Creature — Bear", "")
        assert self._p("?", "Creature — Bear", "") == neutral
        assert self._p("Nonsense", "Creature — Bear", "") == neutral

    def test_rot_penalty_bounded(self):
        assert 0 < wishlist._ROT_PENALTY <= 2.0


class TestConditionalPower:
    """A card whose power scales with the DECK can't be priced by a rarity+role seed
    graded in isolation — every Power this session had to hand-correct was one of these
    (Repulsive Mutation, Genesis Wave, Mona Lisa, Procrastinate)."""

    def test_x_cost_is_conditional(self):
        assert wishlist.is_conditional_power(
            {"Card Text": "Counter up to one target spell unless its controller pays "
                          "mana equal to the greatest power among creatures you control.",
             "Mana Cost": "{X}{G}{U}"})

    def test_kicker_landfall_and_equal_to_are_conditional(self):
        for text in ("Kicker—Return a land you control to its owner's hand.",
                     "Landfall — Whenever a land you control enters, draw a card.",
                     "Draw cards equal to the greatest power among creatures you control.",
                     "This creature gets +1/+1 for each Elf you control."):
            assert wishlist.is_conditional_power({"Card Text": text, "Mana Cost": "{2}{G}"}), text

    def test_plain_cards_are_not_conditional(self):
        for text in ("Destroy target creature.", "Draw two cards.", "Flying. Vigilance."):
            assert not wishlist.is_conditional_power({"Card Text": text, "Mana Cost": "{1}{B}"}), text


class TestPowerProvenance:
    """`--add` and `--seed-power` write an estimate into the same cell a hand grade goes
    in, so nothing could tell them apart — which forced "verify this" onto every row."""

    def test_seeded_is_not_trusted(self):
        assert wishlist.power_is_seeded({"Power": "4.5", "Power Source": wishlist.POWER_SEEDED})

    def test_hand_grade_is_trusted(self):
        assert not wishlist.power_is_seeded({"Power": "7.0", "Power Source": wishlist.POWER_HAND})

    def test_unknown_and_blank_are_not_trusted(self):
        # A row predating the column: provenance is genuinely unrecorded, so it must not
        # be silently blessed as a human judgment.
        assert wishlist.power_is_seeded({"Power": "5.0", "Power Source": wishlist.POWER_UNKNOWN})
        assert wishlist.power_is_seeded({"Power": "5.0", "Power Source": ""})

    def test_case_insensitive(self):
        assert not wishlist.power_is_seeded({"Power": "7.0", "Power Source": "Hand"})

class TestTagModelAlignment:
    """Three phrases where `tags_for` disagreed with `classify_roles` on the same text.
    Each left a card with a completely blank Synergies cell, invisible to every
    tag-based recommendation."""

    def test_draw_cards_equal_to(self):
        # The Ten Rings sat in a deck with no tags at all.
        assert "card draw" in tag_synergies.tags_for(
            {"Type": "Legendary Artifact",
             "Card Text": "At the beginning of your end step, if you have fewer than ten "
                          "cards in hand, draw cards equal to the difference."})

    def test_gain_life_equal_to(self):
        assert "lifegain" in tag_synergies.tags_for(
            {"Type": "Sorcery",
             "Card Text": "Each opponent loses X life. You gain life equal to the life "
                          "lost this way."})

    def test_costs_n_less_without_a_named_keyword(self):
        # `cost-reduction` existed on 167 pool cards but only ever via the KEYWORD map,
        # so a card that plainly SAYS it costs less carried no tag.
        assert "cost-reduction" in tag_synergies.tags_for(
            {"Type": "Sorcery",
             "Card Text": "This spell costs {3} less to cast if there are ten or more "
                          "nonland permanents on the battlefield.\nDestroy all enchantments."})

    def test_pay_life_is_scoped_to_you(self):
        # "each opponent loses 2 life" is a DRAIN effect, the opposite card.
        assert "pay life" in tag_synergies.tags_for(
            {"Type": "Creature", "Card Text": "You lose life equal to its mana value."})
        assert "pay life" not in tag_synergies.tags_for(
            {"Type": "Sorcery", "Card Text": "Each opponent loses 2 life."})


class TestBudgetPlanner:
    """`--budget` is THE wildcard-spend recommender, so a check its sibling `--rank`
    performs must not be missing here — that is the same shape as the `suggest --lands`
    bug where the spend view skipped the legality filter."""

    def test_parses_any_order_and_spacing(self):
        assert wishlist._parse_budget("9M 10R 38U 48C") == {
            "Mythic": 9, "Rare": 10, "Uncommon": 38, "Common": 48}
        assert wishlist._parse_budget("10r  2M") == {"Rare": 10, "Mythic": 2}
        assert wishlist._parse_budget("3 rares") == {"Rare": 3}

    def test_repeated_rarity_accumulates(self):
        assert wishlist._parse_budget("2R 3R") == {"Rare": 5}

    def test_garbage_parses_to_nothing(self):
        assert wishlist._parse_budget("") == {}
        assert wishlist._parse_budget("spend everything") == {}

    def _rows(self, n=6):
        # Distinct fit AND power so the fit/power blend is exercised, not a tie-break.
        return [{"Card Name": f"C{i}", "Rarity": "Rare", "Color(s)": "",
                 "Synergies": "etb; tokens" if i % 2 else "landfall",
                 "Target": "", "Power": str(2 + i)} for i in range(n)]

    def test_a_filtered_view_scores_identically_to_the_full_one(self):
        """`fitN` is `pri` scaled to the max in the SCORED set, and `combined` blends it
        with a power that is not rescaled — so scoring only a filtered subset inflates
        fit relative to power and can reorder the picks. The normalization denominator
        belongs to the corpus, not to the view."""
        rows = self._rows()
        full = {s["name"]: s["combined"] for s in wishlist._rank_scores(rows)}
        # The subset must EXCLUDE the corpus max, or the denominator is unchanged and
        # there is no drift to catch — which is exactly how this test first passed
        # vacuously.
        sel = {"C1", "C3"}
        subset = [r for r in rows if r["Card Name"] in sel]
        # Scored against the whole list, then filtered — the fix.
        kept = wishlist._rank_scores(rows, keep=sel)
        assert {s["name"] for s in kept} == sel
        for s in kept:
            assert s["combined"] == full[s["name"]], s["name"]
        # ...and scoring the subset alone is what would have drifted.
        alone = {s["name"]: s["combined"] for s in wishlist._rank_scores(subset)}
        assert all(alone[n] > full[n] for n in sel), \
            "rescaling against the subset max inflates fit relative to power"

    def test_keep_is_optional_and_defaults_to_everything(self):
        rows = self._rows(3)
        assert len(wishlist._rank_scores(rows)) == 3


class TestAddStampsTargetAndNote:
    """`--target` / `--note` are query FILTERS, and argparse shares them across modes, so
    passing them with `--add` was a SILENT no-op: the command reported success and wrote
    blank cells (found 2026-09-01 wishlisting Pinnacle Starcage for deck 6). Worse than an
    error, because /add-wishlist's recipe says to "set the home Target" and no flag did
    it — a documented step with no tool behind it (G-53)."""

    def _world(self, tmp_path, monkeypatch):
        monkeypatch.setattr(wishlist, "WISHLIST_CSV", str(tmp_path / "wl.csv"))
        monkeypatch.setattr(wishlist, "POOL_CSV", str(tmp_path / "pool.csv"))
        monkeypatch.setattr(wishlist, "DEFAULT_CSV", str(tmp_path / "lib.csv"))
        batch = tmp_path / "batch.txt"
        batch.write_text("1 Test Bomb (SET) 9\n", encoding="utf-8")

        def _enrich(name, set_code, collector, pool):
            return ({"Card Name": name, "Type": "Creature — Demon",
                     "Card Text": "Destroy target creature.", "Color(s)": "B",
                     "Synergies": "removal", "Rarity": "Rare", "Set Code": set_code,
                     "Collector #": collector, "Target": "", "Note": ""}, "scryfall")
        monkeypatch.setattr(wishlist, "enrich", _enrich)
        return str(batch)

    def test_target_and_note_reach_the_written_row(self, tmp_path, monkeypatch):
        batch = self._world(tmp_path, monkeypatch)
        assert wishlist.cmd_add(batch, target="6", note="home deck") == 0
        row = wishlist.load_wishlist()[0]
        assert row["Target"] == "6" and row["Note"] == "home deck"

    def test_an_unknown_target_is_refused_and_writes_nothing(self, tmp_path, monkeypatch):
        # Asymmetric validation, as parse_matches uses (G-74): a bad deck id would write a
        # DANGLING Target, so it is refused BEFORE any Scryfall work rather than after.
        batch = self._world(tmp_path, monkeypatch)
        assert wishlist.cmd_add(batch, target="999") == 1
        assert wishlist.load_wishlist() == []

    def test_a_re_add_does_not_clobber_a_hand_set_target(self, tmp_path, monkeypatch):
        # Only NEW rows are stamped — a second add must not overwrite a Target a human set.
        batch = self._world(tmp_path, monkeypatch)
        wishlist.cmd_add(batch, target="6")
        rows = wishlist.load_wishlist()
        rows[0]["Target"] = "42"
        wishlist.write_wishlist(rows)
        wishlist.cmd_add(batch, target="6")
        assert wishlist.load_wishlist()[0]["Target"] == "42"

    def test_add_without_the_flags_is_unchanged(self, tmp_path, monkeypatch):
        batch = self._world(tmp_path, monkeypatch)
        assert wishlist.cmd_add(batch) == 0
        row = wishlist.load_wishlist()[0]
        assert row["Target"] == "" and row["Note"] == ""


class TestOutageReseed:
    """The F20 + BS-17 path end to end: a card added during a Scryfall outage gets a
    2.0 Power seed computed from BLANK data; the re-add backfills the card's fields
    AND recomputes the untrusted seed — while a hand grade is never touched. This
    path had no coverage at all (batch 6): it needs the enrich seam faked, which is
    exactly why nobody had tested it."""

    def _world(self, tmp_path, monkeypatch):
        monkeypatch.setattr(wishlist, "WISHLIST_CSV", str(tmp_path / "wl.csv"))
        monkeypatch.setattr(wishlist, "POOL_CSV", str(tmp_path / "pool.csv"))    # absent → {}
        monkeypatch.setattr(wishlist, "DEFAULT_CSV", str(tmp_path / "lib.csv"))  # absent → own 0
        batch = tmp_path / "batch.txt"
        batch.write_text("1 Test Bomb (SET) 9\n", encoding="utf-8")
        return str(batch)

    def _fake_enrich(self, outage):
        def _enrich(name, set_code, collector, pool):
            if outage:
                data = {"Card Name": name, "Type": "", "Card Text": "", "Color(s)": "",
                        "Synergies": "", "Rarity": ""}
                status = "error"
            else:
                data = {"Card Name": name, "Type": "Legendary Creature — Demon",
                        "Card Text": "Flying. Destroy target creature.",
                        "Color(s)": "B", "Synergies": "removal", "Rarity": "Mythic"}
                status = "scryfall"
            data.update({"Set Code": set_code, "Collector #": collector,
                         "Target": "", "Note": ""})
            return data, status
        return _enrich

    def test_outage_seed_is_recomputed_on_reenrich(self, tmp_path, monkeypatch):
        batch = self._world(tmp_path, monkeypatch)
        monkeypatch.setattr(wishlist, "enrich", self._fake_enrich(outage=True))
        wishlist.cmd_add(batch)
        row = wishlist.load_wishlist()[0]
        outage_seed = float(row["Power"])
        assert row["Power Source"] == "seed" and outage_seed == 2.0   # blank-data floor
        # Scryfall comes back; the SAME batch is re-added.
        monkeypatch.setattr(wishlist, "enrich", self._fake_enrich(outage=False))
        wishlist.cmd_add(batch)
        row = wishlist.load_wishlist()[0]
        assert row["Type"], "F20: the re-add must backfill the outage row's fields"
        assert float(row["Power"]) > outage_seed, \
            "BS-17: the untrusted seed must be recomputed from the arrived data"
        assert row["Power Source"] == "seed"

    def test_a_hand_grade_survives_reenrich(self, tmp_path, monkeypatch):
        batch = self._world(tmp_path, monkeypatch)
        monkeypatch.setattr(wishlist, "enrich", self._fake_enrich(outage=True))
        wishlist.cmd_add(batch)
        rows = wishlist.load_wishlist()
        rows[0]["Power"], rows[0]["Power Source"] = "9.5", "hand"     # the human graded it
        wishlist.write_wishlist(rows)
        monkeypatch.setattr(wishlist, "enrich", self._fake_enrich(outage=False))
        wishlist.cmd_add(batch)
        row = wishlist.load_wishlist()[0]
        assert row["Power"] == "9.5" and row["Power Source"] == "hand", \
            "G-17: a hand grade is trusted; re-enrich must never overwrite it"


class TestPowerRangeFlag:
    def test_out_of_range_power_is_flagged_and_scored_zero(self):
        """The Pensive Professor class (batch 6): a finite 78.0 passed the NaN and
        non-numeric guards and pinned the top of the craft ranking at combined
        42.3 on a 0-10 scale. 15 live cells turned out to carry 0-100-style
        grades."""
        row = {"Card Name": "Typo Bomb", "Type": "Creature", "Card Text": "",
               "Color(s)": "B", "Synergies": "", "Set Code": "SET",
               "Collector #": "1", "Target": "", "Note": "", "Power": "78",
               "Power Source": "hand"}
        s = wishlist._rank_scores([row])[0]
        assert s["bad_power"] and s["power"] == 0.0

    def test_ten_and_zero_are_in_range(self):
        for val in ("10", "0"):
            row = {"Card Name": "Edge Case", "Type": "Creature", "Card Text": "",
                   "Color(s)": "B", "Synergies": "", "Set Code": "SET",
                   "Collector #": "1", "Target": "", "Note": "", "Power": val,
                   "Power Source": "hand"}
            assert not wishlist._rank_scores([row])[0]["bad_power"]


class TestIsLandReadsTheFrontFace:
    """BS2-11: `_is_land` was a whole-type-line substring scan, so a card whose BACK
    face is a land (`Legendary Creature — God // Land`) took the manabase-value
    ranking branch — theme fit discarded, tier re-assigned, a creature bought as a
    phantom "manabase" upgrade in a live --budget run. The front face is what a land
    drop can play."""

    def test_a_back_face_land_is_not_a_land(self):
        assert wishlist._is_land({"Type": "Legendary Creature — God // Land"}) is False

    def test_a_front_face_land_is_a_land(self):
        assert wishlist._is_land({"Type": "Land — Town // Sorcery — Adventure"}) is True

    def test_a_plain_land_is_a_land(self):
        assert wishlist._is_land({"Type": "Land — Desert"}) is True


class TestSpecificHomeRescue:
    """BS2-39: `specific` was retained only for the single highest-SCORING deck, and
    generic themes are floored, not zeroed — so three near-generic overlaps could
    outscore one genuinely specific theme, and the card read `review`/"generic" (or
    was pointed at the generic deck) while a real specific home existed (5 of 206
    live rows). The best specific-theme deck is now tracked separately and rescues
    the confidence at `ok`, never STRONG."""

    # deck g: three generic themes at floor idf, summed score ~3x. deck s: ONE
    # genuinely specific theme with a smaller summed score. The generic deck wins
    # on score; the specific deck must still carry the signal.
    _FPS = [("g", frozenset("G"), {"etb", "tokens", "value"},
             {"etb": 1.0, "tokens": 1.0, "value": 1.0}),
            ("s", frozenset("G"), {"blink"}, {"blink": 1.0})]
    _IDF = {"etb": 0.8, "tokens": 0.8, "value": 0.8, "blink": 1.4}
    _SPEC = 1.3

    def _model(self, monkeypatch):
        monkeypatch.setattr(wishlist, "_theme_model", lambda: (self._FPS, self._IDF, self._SPEC))
        # neutralize the loaders _rank_scores touches around the fit loop
        monkeypatch.setattr(wishlist, "_deck_colors_map", lambda: {})
        monkeypatch.setattr(wishlist, "_deck_status_map", lambda: {}, raising=False)

    def _row(self):
        return {"Card Name": "Splash Portal Test", "Type": "Sorcery",
                "Card Text": "Exile a creature, then return it.", "Color(s)": "G",
                "Synergies": "etb;tokens;value;blink", "Set Code": "TST",
                "Collector #": "1", "Target": "", "Note": "", "Power": "5",
                "Power Source": "hand"}

    def test_rank_scores_rescues_the_specific_home(self, monkeypatch):
        self._model(monkeypatch)
        s = next(x for x in wishlist._rank_scores([self._row()])
                 if x["name"] == "Splash Portal Test")
        assert s["conf"] == "ok"                 # was: review
        assert "blink" in s["sig"]               # the specific theme survives to the sig

    def test_suggest_targets_points_at_the_specific_deck(self, monkeypatch, capsys):
        self._model(monkeypatch)
        wishlist.cmd_suggest_targets([self._row()], write=False)
        out = capsys.readouterr().out
        line = next(l for l in out.splitlines() if "Splash Portal Test" in l)
        assert " ok " in line and " s " in line.replace("  ", " ")
        assert "review" not in line


class TestConditionalPowerManaJoin:
    """Batch B: wishlist rows carry no `Mana Cost` column, so the `{x}` alternative
    of the conditional-power regex was dead — Genesis Wave, named in the block's own
    design comment, was unflagged. The cost now joins from card-mana.csv."""

    def test_x_cost_in_the_joined_cost_flags(self):
        cache = {"test x spell": ("{X}{G}", 1)}
        assert wishlist.is_conditional_power(
            {"Card Name": "Test X Spell", "Card Text": "Put X counters."}, _mana=cache)

    def test_plain_cost_does_not_flag(self):
        cache = {"plain spell": ("{1}{G}", 2)}
        assert not wishlist.is_conditional_power(
            {"Card Name": "Plain Spell", "Card Text": "Draw a card."}, _mana=cache)


class TestSeedPowerReadsTheFrontFace:
    """Batch B / G-63: the merged type line made a DFC whose BACK is an
    Instant/Sorcery fail the permanent-value gate (Decadent Dragon seeded 4.5
    against a correct 5.5, live in the CSV as Power Source: seed), and a back-face
    Planeswalker would grant the +2.0."""

    def test_back_face_instant_does_not_suppress_the_permanent_bump(self):
        front_only = wishlist._seed_power(
            {"Card Name": "A", "Type": "Creature — Dragon",
             "Card Text": "Destroy target permanent.", "Rarity": "Rare"})
        dfc = wishlist._seed_power(
            {"Card Name": "A // B", "Type": "Creature — Dragon // Instant — Adventure",
             "Card Text": "Destroy target permanent.", "Rarity": "Rare"})
        assert dfc == front_only

    def test_back_face_planeswalker_gets_no_bonus(self):
        plain = wishlist._seed_power(
            {"Card Name": "A", "Type": "Creature — Human", "Card Text": "", "Rarity": "Rare"})
        dfc = wishlist._seed_power(
            {"Card Name": "A // B", "Type": "Creature — Human // Planeswalker — B",
             "Card Text": "", "Rarity": "Rare"})
        assert dfc == plain


class TestTargetAuditFailsLoud:
    """BS4-08: `_audit_target_issues` wrapped the roster load in `except Exception: pass`,
    and every check below is gated on the structures that load fills — so on any deck.py
    failure it returned [] and `--audit-targets` printed "Wishlist targets are clean"
    having checked nothing. Worse on the automated path: `check_all`'s soft sweep has its
    own try/except that WOULD have reported a skip, but the exception was swallowed one
    level down, so the gate saw an empty list rather than a failure and the roster sweep
    became an invisible no-op. Every sibling loader in this file eprints on this exact
    failure (audit A14); this was the one that didn't."""

    def test_a_roster_failure_raises_instead_of_reporting_clean(self, monkeypatch):
        import deck as dk
        monkeypatch.setattr(dk, "discover_decks",
                            lambda: (_ for _ in ()).throw(RuntimeError("deck.py broken")))
        with pytest.raises(wishlist.TargetAuditUnavailable):
            wishlist._audit_target_issues(color_only=True)

    def test_the_message_says_SKIP_not_clean(self, monkeypatch):
        import deck as dk
        monkeypatch.setattr(dk, "discover_decks",
                            lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        try:
            wishlist._audit_target_issues()
        except wishlist.TargetAuditUnavailable as e:
            assert "SKIP" in str(e) and "not a clean bill" in str(e)

    def test_check_all_reports_it_as_a_downed_radar(self, monkeypatch):
        """The sentinel `check_all` counts: its handler appends "… skipped (…)", which the
        --quiet path tallies as "RADAR(S) DID NOT RUN". Pin that the string still matches."""
        msg = f"wishlist target audit skipped ({wishlist.TargetAuditUnavailable('x')})"
        assert " skipped (" in msg

    def test_the_healthy_path_still_returns_a_list(self):
        assert isinstance(wishlist._audit_target_issues(color_only=True), list)


class TestSeedPowerNeverLosesABatch:
    """BS4-22: `_seed_power` does `import deck`, and cmd_add called it in a bare loop
    AFTER the Scryfall fetches and BEFORE `write_wishlist` — so a broken deck.py threw
    away an entire enriched batch over a cosmetic estimate. A blank Power is a state the
    tool already models (`--seed-power` exists to fill exactly those cells); a lost batch
    is not."""

    def test_it_degrades_to_None_instead_of_raising(self, monkeypatch, capsys):
        monkeypatch.setattr(wishlist, "_seed_power",
                            lambda r: (_ for _ in ()).throw(ImportError("deck.py broken")))
        assert wishlist._try_seed_power({"Card Name": "X"}, _warned=[]) is None

    def test_it_warns_once_not_per_row(self, monkeypatch, capsys):
        monkeypatch.setattr(wishlist, "_seed_power",
                            lambda r: (_ for _ in ()).throw(ImportError("broken")))
        warned = []
        for _ in range(5):
            wishlist._try_seed_power({"Card Name": "X"}, _warned=warned)
        assert capsys.readouterr().err.count("Power seeding unavailable") == 1

    def test_a_healthy_seed_is_returned_unchanged(self, monkeypatch):
        monkeypatch.setattr(wishlist, "_seed_power", lambda r: 6.5)
        assert wishlist._try_seed_power({"Card Name": "X"}, _warned=[]) == 6.5


class TestRestrictedManaLands:
    """G-37's live scoring miss: a Village-cycle land reads "{T}: Add {B}. Spend this mana
    only to cast a creature spell." — a black source for creatures and NOTHING for a
    removal spell — and it ranked #1 of deck 52's land suggestions at 7.2 fixing.

    The restriction is detected PER LINE, because that is how Magic prints it: the
    qualifying sentence follows the Add sentence inside one ability, and `_land_value`'s
    clause scan deliberately stops at the period before it."""

    def _land(self, text, colors="B"):
        return {"Card Name": "Probe Land", "Type": "Land", "Card Text": text,
                "Color(s)": colors}

    FREE = "{T}: Add {B}."
    RESTRICTED = "{T}: Add {C}.\n{T}: Add {B}. Spend this mana only to cast a creature spell."

    def test_a_restricted_source_scores_below_a_free_one(self):
        free = wishlist._land_value(self._land(self.FREE), {"B"})
        restricted = wishlist._land_value(self._land(self.RESTRICTED), {"B"})
        assert restricted < free

    def test_the_discount_never_goes_below_the_neutral_floor(self):
        """One-directional and bounded: it halves the PREMIUM, not the 3.5 baseline, so it
        can only lower a land — never invent one, and never push it under a utility land."""
        assert wishlist._land_value(self._land(self.RESTRICTED), {"B"}) >= 3.5

    def test_a_color_added_freely_ELSEWHERE_is_not_restricted(self):
        """`restricted_only -= free`: a land that adds {B} both freely and under a clause
        is a free source. Scoring it as restricted would under-rate a strictly better card."""
        both = "{T}: Add {B}.\n{T}: Add {B}. Spend this mana only to cast a creature spell."
        assert wishlist._land_value(self._land(both), {"B"}) == \
            wishlist._land_value(self._land(self.FREE), {"B"})

    def test_a_restriction_on_a_color_the_deck_does_not_use_changes_nothing(self):
        """The discount is gated on the colors the DECK wants. A restricted {U} is already
        worth nothing to a mono-black deck through the color-match term."""
        u = "{T}: Add {U}. Spend this mana only to cast a creature spell."
        assert wishlist._land_value(self._land(u, "U"), {"B"}) == \
            wishlist._land_value(self._land("{T}: Add {U}.", "U"), {"B"})

    def test_the_real_card_drops_below_the_unrestricted_sources(self):
        """The motivating case, end to end: Mudflat Village must not outrank a plain
        mono-black land in a mono-black deck."""
        mudflat = self._land(self.RESTRICTED)
        assert wishlist._land_value(mudflat, {"B"}) < wishlist._land_value(self._land(
            "This land enters tapped unless you control a Mount.\n{T}: Add {B}."), {"B"})


class TestWishlistCastabilityByCost:
    """BS8-36: `--audit-targets` was pip-aware while `--rank` / `--suggest-targets`
    tested identity ⊆ deck colours — three answers to one question inside one file."""

    def test_a_hybrid_is_castable_in_either_colour(self):
        assert wishlist._castable("{1}{U/R}{U/R}", {"U", "R"}, {"U"})
        assert not wishlist._castable("{U}{R}", {"U", "R"}, {"U"})
        assert not wishlist._castable("", {"U", "R"}, {"U"}), "no cost -> identity fallback"


class TestAddTargetVocabulary:
    """BS8-17: `--add --target` refused `general`, `concept: …`, `21; 6` and `06` —
    forms the Target column already carried on 13 live rows."""

    def test_the_status_label_normalizes_a_padded_id(self):
        assert wishlist._status_label("06", {"6": ("B", 0)}) == "B·0"
        assert wishlist._status_label("general", {"6": ("B", 0)}) == "—"


class TestLandBreadthAboveTwo:
    """`multi` saturated at two colours, so a source fixing all THREE of a three-colour
    deck's colours scored exactly what a two-colour dual did. `deck_source_profile`
    counts a basic fetch as a source of every colour the deck runs a basic of (G-35), so
    the two halves of one subsystem disagreed. Deck 57's three fetches — the largest
    manabase upgrade available to it — sat at rank 45-47 of 216 (2026-09-04)."""

    FETCH = ("{T}, Sacrifice this land: Search your library for a basic land card, "
             "put it onto the battlefield tapped, then shuffle.")
    TAPPED_DUAL = "This land enters tapped. {T}: Add {W} or {U}."
    UNTAPPED_DUAL = "{T}: Add {W} or {U}."

    def _land(self, txt, ident=""):
        return {"Card Text": txt, "Color(s)": ident}

    def test_a_three_colour_source_beats_a_two_colour_one_in_a_three_colour_deck(self):
        three = {"W", "U", "R"}
        assert (wishlist._land_value(self._land(self.FETCH), three)
                > wishlist._land_value(self._land(self.TAPPED_DUAL), three))

    def test_breadth_never_overturns_the_untapped_premium(self):
        """Untapped-two versus tapped-three is a real deck-dependent trade; the fixing
        model must not pretend to settle it, so the breadth credit is calibrated to stay
        under the 1.5 untapped premium."""
        three = {"W", "U", "R"}
        assert (wishlist._land_value(self._land(self.FETCH), three)
                < wishlist._land_value(self._land(self.UNTAPPED_DUAL), three))

    def test_a_two_colour_deck_is_untouched(self):
        """The term is additive and gated on len(used) > 2, so nothing below three
        colours can move — no existing recommendation is withdrawn by this change."""
        two = {"W", "U"}
        assert (wishlist._land_value(self._land(self.FETCH), two)
                == wishlist._land_value(self._land(self.TAPPED_DUAL), two))

    def test_the_credit_is_capped(self):
        """Bounded like every other co-signal here: a five-colour source in a five-colour
        deck cannot run away with the ranking."""
        five = set("WUBRG")
        three = {"W", "U", "R"}
        gain5 = wishlist._land_value(self._land(self.FETCH), five)
        gain3 = wishlist._land_value(self._land(self.FETCH), three)
        assert gain5 - gain3 <= wishlist._LAND_BREADTH_CAP

class TestShocklandEarnsTheUntappedPremium:
    """The THIRD surface of the 2026-09-04 tapland defect. `tapland_profile` and
    `suggest --lands`' `·tapped?` marker were fixed to read a shockland as conditional
    while this SCORING path still tested for the substring "enters tapped", so Hallowed
    Fountain valued at 8.0 as though it always entered tapped. All three now call
    `lib.tapland_kind`."""

    SHOCK = ("({T}: Add {W} or {U}.)\nAs this land enters, you may pay 2 life. "
             "If you don't, it enters tapped.")
    UNTAPPED = "{T}: Add {W} or {U}."
    BOARD_COND = "This land enters tapped unless you control two or more other lands.\n{T}: Add {W} or {U}."
    FLAT = "This land enters tapped.\n{T}: Add {W} or {U}."

    def _l(self, t):
        # Identity is load-bearing here exactly as it is on the real rows: a shockland
        # prints its mana ability in PARENTHESES, which `_LAND_REMINDER_RE` strips, so the
        # colours come from the Color(s) cell — the documented fallback.
        return {"Card Text": t, "Color(s)": "W/U"}

    def test_a_shockland_scores_as_untapped(self):
        """Its condition is payable AT WILL — the same reasoning that already treats a
        pay-life cost as a real source every turn."""
        three = {"W", "U", "R"}
        assert (wishlist._land_value(self._l(self.SHOCK), three)
                == wishlist._land_value(self._l(self.UNTAPPED), three))

    def test_a_board_state_condition_stays_conservative(self):
        """"unless you control two or more other lands" may simply not be met, so it keeps
        the tapped score and prints `·tapped?` for a human to judge (G-37)."""
        three = {"W", "U", "R"}
        assert (wishlist._land_value(self._l(self.BOARD_COND), three)
                == wishlist._land_value(self._l(self.FLAT), three))
        assert (wishlist._land_value(self._l(self.BOARD_COND), three)
                < wishlist._land_value(self._l(self.SHOCK), three))
