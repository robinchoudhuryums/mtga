"""Unit tests for the ingest/tagging pure functions: import_arena parsing and the
tag_synergies heuristics (the source of every synergy tag downstream code relies on)."""
import pytest

import import_arena
import import_collection as ic
import tag_synergies as ts


class TestImportArenaParse:
    def test_basic_line(self):
        entries, warnings = import_arena.parse("Deck\n2 Llanowar Elves (DOM) 168")
        assert entries == [(2, "Llanowar Elves", "DOM", "168")]
        assert warnings == []

    def test_section_headers_skipped(self):
        entries, _ = import_arena.parse("Deck\n1 Shock (M19) 156\nSideboard\n2 Negate (M19) 69")
        assert (1, "Shock", "M19", "156") in entries
        assert (2, "Negate", "M19", "69") in entries

    def test_name_without_set(self):
        entries, _ = import_arena.parse("3 Forest")
        assert entries == [(3, "Forest", "", "")]

    def test_skip_basics(self):
        entries, _ = import_arena.parse("2 Llanowar Elves (DOM) 168\n9 Forest", skip_basics=True)
        assert entries == [(2, "Llanowar Elves", "DOM", "168")]

    def test_comment_and_blank_ignored(self):
        entries, warnings = import_arena.parse("# a comment\n\n// another\n1 Shock (M19) 156")
        assert entries == [(1, "Shock", "M19", "156")]
        assert warnings == []

    def test_unparseable_line_warns_not_dropped_silently(self):
        entries, warnings = import_arena.parse("this is not a card line")
        assert entries == []
        assert len(warnings) == 1


class TestMergeQuantities:
    def test_max_by_default(self):
        rows = [{"Card Name": "Shock", "Set Code": "M19", "Collector #": "156",
                 "Quantity Owned": "4", "Type": "", "Card Text": "", "Color(s)": "",
                 "Synergies": ""}]
        added, updated = import_arena.merge(rows, [(2, "Shock", "M19", "156")], sum_mode=False)
        assert rows[0]["Quantity Owned"] == "4"  # max(4, 2) — a lower-bound line can't drop a count
        assert added == 0

    def test_sum_mode(self):
        rows = [{"Card Name": "Shock", "Set Code": "M19", "Collector #": "156",
                 "Quantity Owned": "1", "Type": "", "Card Text": "", "Color(s)": "",
                 "Synergies": ""}]
        import_arena.merge(rows, [(2, "Shock", "M19", "156")], sum_mode=True)
        assert rows[0]["Quantity Owned"] == "3"

    def test_new_printing_added(self):
        rows = []
        added, _ = import_arena.merge(rows, [(1, "Shock", "M19", "156")], sum_mode=False)
        assert added == 1 and rows[0]["Card Name"] == "Shock"


class TestTagsFor:
    def test_impending_maps_to_tempo(self):
        tags = ts.tags_for({"Type": "Enchantment Creature", "Card Text": "Impending 4—{1}{G}{G}"}, ["Impending"])
        assert "tempo" in tags and "cost-reduction" in tags

    def test_flavor_keyword_denylisted(self):
        # A Marvel flavor name must NOT become a synergy tag.
        tags = ts.tags_for({"Type": "Creature", "Card Text": ""}, ["Animal May-Ham"])
        assert "animal may-ham" not in [t.lower() for t in tags]

    def test_removal_from_text(self):
        assert "removal" in ts.tags_for({"Type": "Instant", "Card Text": "Destroy target creature."}, [])


class TestExileCastTheme:
    """`exile cast` = the card is cast FROM EXILE, or pays off casting outside your hand.

    Closes the gap that made Spider-Verse return no fits at all and pointed Virtue of
    Loyalty at counters decks instead of the cast-from-exile deck its Adventure half feeds.
    """

    def _t(self, type_line, text):
        return ts.is_exile_cast_text(type_line, text.lower())

    def test_warp_plot_foretell_are_enablers(self):
        assert self._t("Creature", "Warp {1}{W} (You may cast this card from your hand for "
                                   "its warp cost...)")
        assert self._t("Creature", "Plot {3}{R} (You may pay {3}{R} and exile this card...)")

    def test_adventure_is_an_enabler_from_the_type_line(self):
        # The Adventure half exiles the card; you then cast the other half FROM EXILE.
        assert self._t("Enchantment // Instant — Adventure", "Create a 2/2 Knight token.")

    def test_payoff_side_shares_the_tag(self):
        assert self._t("Planeswalker", "Whenever you cast a spell from exile, this deals 2 "
                                       "damage to each opponent.")
        assert self._t("Enchantment", "Whenever you cast a spell from anywhere other than "
                                      "your hand, you may copy it.")
        assert self._t("Creature", "Whenever a permanent you control enters from exile, put "
                                   "a +1/+1 counter on each creature you control.")

    def test_plain_cards_are_not_tagged(self):
        assert not self._t("Instant", "Shock deals 2 damage to any target.")
        assert not self._t("Creature — Elf Druid", "{T}: Add {G}.")

    def test_impulse_stays_a_separate_concept(self):
        # Exiling from YOUR library to play the exiled card is `impulse`; the card itself
        # is not being cast out of exile, so it must not pick up `exile cast`.
        assert not self._t("Sorcery", "Exile the top two cards of your library. Until the "
                                      "end of your next turn, you may play those cards.")

    def test_tag_reaches_tags_for(self):
        tags = ts.tags_for({"Type": "Creature — Angel", "Card Text":
                            "Flying, lifelink\nWarp {1}{W} (You may cast this card from your "
                            "hand for its warp cost.)"}, ["Warp"])
        assert "exile cast" in tags


class TestKeywordFrequencyCountsDistinctCards:
    def test_a_dfc_counts_once(self, tmp_path):
        """card-mana.csv keys a DFC twice (front name AND full name), so a row-tally read a
        card-UNIQUE keyword as frequency 2 and it escaped the noise filter — which is how
        'Goblin Formula' (Norman Osborn only) reached the unindexed-mechanic radar."""
        p = tmp_path / "mana.csv"
        p.write_text("Card Name,Mana Cost,Mana Value,Keywords\n"
                     "Norman Osborn,{1}{U},2,Goblin Formula\n"
                     "Norman Osborn // Green Goblin,{1}{U},2,Goblin Formula\n"
                     "Shock,{R},1,\n", encoding="utf-8")
        ts._freq_cache.pop(str(p), None)
        freq, n = ts.keyword_frequencies(str(p))
        assert freq["goblin formula"] == 1, "a DFC's two rows are ONE card"
        assert n == 2


class TestHeistTheme:
    """`heist` = you cast a card out of an OPPONENT's zone.

    Distinct from the pre-existing `theft` tag, which means "gain control of" — stealing
    a permanent already on the battlefield. Two different mechanics; a deck built on one
    is not automatically helped by the other, so they stay separate tags.

    The scoping is the whole difficulty: the huge self-exile families (impulse draw,
    foretell, adventure) use nearly identical wording, and the cast clause usually sits
    in a DIFFERENT SENTENCE from the zone it came out of.
    """

    def _t(self, text):
        return ts.is_heist_text(text.lower())

    def test_same_sentence_form(self):
        assert self._t("Target opponent exiles the top four cards of their library. "
                       "You may cast those cards for as long as they remain exiled.")

    def test_cross_sentence_form(self):
        # The common templating: the exile and the permission are separate sentences,
        # which a single same-sentence regex structurally cannot connect.
        assert self._t("Whenever this creature deals combat damage to a player, exile "
                       "the top card of their library. You may play it this turn.")

    def test_cast_straight_from_their_graveyard(self):
        assert self._t("Cast target nonland card from an opponent's graveyard without "
                       "paying its mana cost.")
        assert self._t("Each opponent mills three cards, then you may cast a spell from "
                       "each opponent's graveyard without paying its mana cost.")

    def test_reanimating_their_creature_is_heist(self):
        assert self._t("Whenever this creature deals combat damage to a player, you may "
                       "put target creature card from that player's graveyard onto the "
                       "battlefield under your control.")

    def test_impulse_draw_is_not_heist(self):
        # Exiling from YOUR OWN library and playing it is the single biggest false-positive
        # family; the opponent-zone half of the match is what excludes it.
        assert not self._t("Exile the top two cards of your library. Until the end of your "
                           "next turn, you may play those cards.")

    def test_graveyard_hate_is_not_heist(self):
        # Regression: `(?:cast|play)` without \b matches the `play` inside "each PLAYer",
        # which tagged 13 graveyard-hate cards as heists.
        assert not self._t("Each player exiles a card from their graveyard.")
        assert not self._t("Each player shuffles up to three target cards from their "
                           "graveyard into their library.")

    def test_each_opponent_phrasing_matches(self):
        # Regression: the alternation `(?:an?|each|that )?` carried a trailing space on
        # `that ` but not on `each`, so "from EACH opponent's graveyard" never matched.
        assert self._t("You may cast a spell from each opponent's graveyard.")
        assert self._t("You may cast a spell from an opponent's graveyard.")
        assert self._t("You may cast a spell from that player's graveyard.")

    def test_from_among_those_cards(self):
        # Laughing Jasper Flint — a REPEATABLE heist engine that read as `Lizard; Rogue`
        # only, because the permission is "cast spells from among those cards" rather than
        # the "cast it/that" the first draft keyed on.
        assert self._t("At the beginning of your upkeep, exile the top X cards of target "
                       "opponent's library, where X is the number of outlaws you control. "
                       "Until end of turn, you may cast spells from among those cards.")

    def test_top_of_their_library_word_order(self):
        # Rakdos, the Muscle — "cards … from THE TOP OF target player's library" inverts
        # the "top X CARDS OF … library" order the zone pattern assumed, and says "target
        # player's" where the pattern only listed "that player's".
        assert self._t("Whenever you sacrifice another creature, exile cards equal to its "
                       "mana value from the top of target player's library. Until your "
                       "next end step, you may play those cards.")

    def test_opponent_must_own_the_exiled_zone(self):
        # Fireglass Mentor: the opponent appears only in a CONDITION, and the exile is from
        # YOUR library. A gap that crossed the comma read this as a heist.
        assert not self._t("At the beginning of your second main phase, if an opponent lost "
                           "life this turn, exile the top two cards of your library. Choose "
                           "one of them. Until end of turn, you may play that card.")
        # …while the opponent as the actual SUBJECT of the exile still matches.
        assert self._t("Each opponent chooses a creature they control and exiles it. Then "
                       "put a creature card exiled with it onto the battlefield under your "
                       "control.")

    def test_tag_reaches_tags_for(self):
        tags = ts.tags_for({"Type": "Sorcery", "Card Text":
                            "Target opponent exiles the top X cards of their library face "
                            "down. You may look at and play those cards for as long as "
                            "they remain exiled."}, [])
        assert "heist" in tags

    def test_does_not_collide_with_gain_control_theft(self):
        # `theft` (gain control of a permanent) and `heist` (cast their card) must stay
        # separate: a naming collision silently merged 93 gain-control cards into the
        # new theme, doubling its size and destroying its specificity.
        gain = ts.tags_for({"Type": "Sorcery", "Card Text":
                            "Gain control of target creature until end of turn."}, [])
        assert "theft" in gain and "heist" not in gain

    def test_food_theme(self):
        assert "food" in ts.tags_for({"Type": "Artifact — Food", "Card Text": "Create a Food token."}, [])

    def test_subtype_tribal_tag(self):
        tags = ts.tags_for({"Type": "Creature — Merfolk Wizard", "Card Text": ""}, [])
        assert "Merfolk" in tags and "Wizard" in tags

    def test_keyword_expands_to_theme(self):
        # Surveil (a Scryfall keyword) implies the graveyard theme.
        tags = ts.tags_for({"Type": "Creature", "Card Text": ""}, ["Surveil"])
        assert "graveyard" in tags

    # --- Mechanical-synergy PAYOFF tags (tagging-misreads #3) ---
    def test_toughness_matters_tag(self):
        # Doran-style payoff — shares a theme with a toughness-swap deck.
        tags = ts.tags_for({"Type": "Artifact — Equipment", "Card Text":
            "As long as equipped creature's toughness is greater than its power, it "
            "assigns combat damage equal to its toughness rather than its power."}, [])
        assert "toughness matters" in tags

    def test_noncombat_damage_tag_amplifier(self):
        tags = ts.tags_for({"Type": "Creature", "Card Text":
            "If a source you control would deal noncombat damage to an opponent, "
            "instead it deals that much damage plus 2."}, [])
        assert "noncombat damage" in tags

    def test_noncombat_damage_tag_repeatable_pinger(self):
        # A pinger PERMANENT (deals ability damage to opponents) reaches the theme.
        tags = ts.tags_for({"Type": "Creature — Human Wizard", "Card Text":
            "Whenever you cast a noncreature spell, this creature deals 1 damage "
            "to each opponent."}, [])
        assert "noncombat damage" in tags

    def test_noncombat_damage_excludes_burn_spell(self):
        # A one-shot burn SPELL must NOT get the theme (else 2 burn spells fake a
        # ping deck); it's already covered by the "burn" tag.
        tags = ts.tags_for({"Type": "Instant", "Card Text":
            "Lightning Strike deals 3 damage to any target."}, [])
        assert "noncombat damage" not in tags

    def test_noncombat_damage_excludes_combat_trigger(self):
        tags = ts.tags_for({"Type": "Creature — Beast", "Card Text":
            "Whenever this creature deals combat damage to a player, draw a card."}, [])
        assert "noncombat damage" not in tags

    def test_spell_copy_tag(self):
        tags = ts.tags_for({"Type": "Artifact", "Card Text":
            "{T}: Add {R}. When that mana is spent to cast a red instant or sorcery "
            "spell, copy that spell and you may choose new targets for the copy."}, [])
        assert "spell copy" in tags

    def test_tribal_payoff_captures_referenced_tribe(self):
        # A lord/tutor gets the tribe it REWARDS even if it isn't that tribe itself.
        tags = ts.tags_for({"Type": "Legendary Creature — Human Warrior", "Card Text":
            "Search your library for a Dinosaur card. Dinosaurs you control gain "
            "double strike."}, [])
        assert "Dinosaur" in tags

    def test_tribal_payoff_ignores_generic_nouns(self):
        # 'Creatures/Lands you control' must NOT mint a bogus tribe tag.
        tags = ts.tags_for({"Type": "Enchantment", "Card Text":
            "Creatures you control get +1/+1. Lands you control have vigilance."}, [])
        assert "Creature" not in tags and "Land" not in tags


class TestFlavorKeywordHeuristic:
    """The card-uniqueness rule that replaces hand-maintaining FLAVOR_KEYWORDS: a
    keyword on exactly one card in a pool-sized corpus is a flavor name; a mechanic
    recurs. Guards matter more than the rule — suppressing a real mechanic is the
    expensive mistake (that is how `harmonize` went missing for a cycle)."""

    BIG = 15000
    FREQ = {"trick arrows": 1, "harmonize": 11, "jump": 13, "flashback": 111,
            "newflavor": 1, "newmechanic": 9}

    def _f(self, kw, corpus=None):
        return ts.is_noise_keyword(kw, self.FREQ, self.BIG if corpus is None else corpus)

    def test_card_unique_name_is_flavor(self):
        assert self._f("trick arrows")

    def test_new_flavor_name_needs_no_code_change(self):
        assert self._f("newflavor")

    def test_recurring_keyword_is_kept(self):
        assert not self._f("newmechanic")
        assert not self._f("jump")

    def test_mapped_theme_is_never_suppressed(self):
        assert not self._f("flashback")

    def test_engine_mechanic_is_never_suppressed(self):
        # deck.ENGINE_THEMES names harmonize as a graveyard enabler.
        assert not self._f("harmonize")

    def test_small_corpus_disables_the_heuristic(self):
        # A library-only card-mana.csv can't distinguish "rare" from "card-unique".
        assert not self._f("newflavor", corpus=1695)

    def test_explicit_denylist_wins_regardless_of_corpus(self):
        assert ts.is_noise_keyword("firaga", {}, 10)

    def test_unknown_keyword_is_not_flavor_when_absent_from_the_corpus(self):
        assert not self._f("nevermentioned")


class TestCollectionColumnDetection:
    """Every tracker spells its columns differently, so they are matched by ALIAS. The
    one thing this must never do is GUESS: a mis-identified quantity column would rewrite
    every count in the inventory, and unlike import_arena this tool can lower them."""

    def test_detects_the_common_spellings(self):
        got = ic.detect_columns(["Card Name", "Set Code", "Collector Number", "Quantity"])
        assert got["name"] == "Card Name" and got["qty"] == "Quantity"
        assert got["set"] == "Set Code" and got["collector"] == "Collector Number"

    def test_detection_ignores_case_and_punctuation(self):
        got = ic.detect_columns(["  card_name ", "HAVE", "edition"])
        assert got["name"] == "  card_name " and got["qty"] == "HAVE"
        assert got["set"] == "edition"

    def test_name_and_qty_are_required(self):
        with pytest.raises(ValueError) as e:
            ic.detect_columns(["thing", "howmany"])
        # The message must show what it actually saw, or the operator can't fix it.
        assert "thing" in str(e.value) and "--map" in str(e.value)

    def test_map_override_wins(self):
        got = ic.detect_columns(["thing", "howmany"],
                                {"name": "thing", "qty": "howmany"})
        assert got["name"] == "thing" and got["qty"] == "howmany"

    def test_map_rejects_a_column_that_does_not_exist(self):
        with pytest.raises(ValueError):
            ic.detect_columns(["a", "b"], {"name": "nope", "qty": "b"})

    def test_set_and_collector_are_optional(self):
        got = ic.detect_columns(["Name", "Count"])
        assert got["name"] == "Name" and "set" not in got


class TestCollectionParse:
    def test_reads_a_plain_csv(self):
        entries, warn = ic.parse_export(
            "Card Name,Set Code,Collector Number,Quantity\nShock,M21,159,4\n")
        assert entries == [(4, "Shock", "M21", "159")] and warn == []

    def test_sniffs_a_tab_separated_export(self):
        entries, _ = ic.parse_export("Name\tEdition\tHave\nShock\tM21\t3\n")
        assert entries == [(3, "Shock", "M21", "")]

    def test_a_non_numeric_quantity_is_reported_not_zeroed(self):
        """Silently reading a bad cell as 0 would DELETE that card's copies."""
        entries, warn = ic.parse_export("Name,Count\nShock,\nBolt,two\n")
        assert entries == []
        assert len(warn) == 2 and "Shock" in warn[0]

    def test_basics_are_skipped(self):
        entries, _ = ic.parse_export("Name,Count\nForest,40\nShock,4\n")
        assert [e[1] for e in entries] == ["Shock"]

    def test_a_zero_count_is_kept(self):
        """0 is a real, meaningful value here — it is how the export says 'disenchanted'."""
        entries, _ = ic.parse_export("Name,Count\nShock,0\n")
        assert entries == [(0, "Shock", "", "")]


class TestCollectionPlan:
    """`plan` is pure: it decides the changes without touching a file."""

    def _row(self, name, setc="M21", coll="1", qty="4"):
        return {"Card Name": name, "Type": "", "Card Text": "", "Color(s)": "",
                "Synergies": "", "Set Code": setc, "Collector #": coll,
                "Quantity Owned": qty}

    def test_sets_a_quantity_DOWN(self):
        """The whole reason this tool exists — import_arena takes max() and can never
        learn that you own fewer."""
        rows = [self._row("Shock", qty="4")]
        r = ic.plan(rows, [(1, "Shock", "M21", "1")])
        assert r["updated"] == [("Shock", "4", "1")]
        assert rows[0]["Quantity Owned"] == "1"

    def test_an_unknown_card_is_added(self):
        r = ic.plan([], [(2, "Brand New", "XXX", "9")])
        assert r["added"] == [("Brand New", "XXX", "9", 2)]

    def test_a_new_dfc_is_stored_under_its_front_name(self):
        r = ic.plan([], [(1, "Front // Back", "XXX", "1")])
        assert r["added"][0][0] == "Front"

    def test_a_row_stored_under_the_FULL_name_still_matches(self):
        """The six DSK Room cards are stored as 'Bottomless Pool // Locker Room', not
        under the front face — front-truncating every export name reported all six as
        brand-new on the first real run."""
        rows = [self._row("Bottomless Pool // Locker Room", "DSK", "43", "1")]
        r = ic.plan(rows, [(2, "Bottomless Pool // Locker Room", "DSK", "43")])
        assert r["added"] == [] and r["updated"] == [
            ("Bottomless Pool // Locker Room", "1", "2")]

    def test_an_export_naming_only_the_front_face_also_matches(self):
        rows = [self._row("Bottomless Pool // Locker Room", "DSK", "43", "1")]
        r = ic.plan(rows, [(2, "Bottomless Pool", "DSK", "43")])
        assert r["added"] == [] and len(r["updated"]) == 1

    def test_name_only_row_with_several_printings_is_ambiguous_not_guessed(self):
        """The export says how many you own in total but not which printing to put them
        on; picking one would silently zero the other."""
        rows = [self._row("Shock", "M21", "159", "2"), self._row("Shock", "DAR", "12", "2")]
        r = ic.plan(rows, [(3, "Shock", "", "")])
        assert r["updated"] == [] and len(r["ambiguous"]) == 1
        assert r["ambiguous"][0][0] == "Shock"

    def test_ambiguous_names_are_reported_once(self):
        rows = [self._row("Shock", "M21", "159", "2"), self._row("Shock", "DAR", "12", "2")]
        r = ic.plan(rows, [(3, "Shock", "", ""), (3, "Shock", "", "")])
        assert len(r["ambiguous"]) == 1

    def test_absent_cards_are_left_alone_by_default(self):
        """A filtered export must not be able to wipe the collection."""
        rows = [self._row("Shock", qty="4")]
        r = ic.plan(rows, [(1, "Other", "M21", "2")])
        assert r["zeroed"] == [("Shock", "4")]
        assert rows[0]["Quantity Owned"] == "4"      # untouched

    def test_zero_missing_opts_in_to_zeroing_them(self):
        rows = [self._row("Shock", qty="4")]
        ic.plan(rows, [(1, "Other", "M21", "2")], zero_missing=True)
        assert rows[0]["Quantity Owned"] == "0"

    def test_an_ambiguous_card_is_not_also_reported_as_missing(self):
        rows = [self._row("Shock", "M21", "159", "2"), self._row("Shock", "DAR", "12", "2")]
        r = ic.plan(rows, [(3, "Shock", "", "")])
        assert r["zeroed"] == []
