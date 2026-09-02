"""Unit tests for the ingest/tagging pure functions: import_arena parsing and the
tag_synergies heuristics (the source of every synergy tag downstream code relies on)."""
import pytest

import import_arena
import import_collection as ic
import lib
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

    def test_deck_plus_sideboard_copies_SUM(self):
        """Deck and Sideboard copies draw from the collection simultaneously: a Bo3
        export with 2+2 Duress proves 4 owned — max() recorded 2 (batch 5)."""
        entries, _ = import_arena.parse(
            "Deck\n2 Duress (M21) 96\nSideboard\n2 Duress (M21) 96")
        assert entries == [(4, "Duress", "M21", "96")]

    def test_two_deck_blocks_take_the_MAX_not_the_sum(self):
        """Decks share one collection: 2 Duress in each of two decks proves 2, not 4."""
        entries, _ = import_arena.parse(
            "Deck\n2 Duress (M21) 96\n\nDeck\n2 Duress (M21) 96")
        assert entries == [(2, "Duress", "M21", "96")]

    def test_companion_line_does_not_double_its_sideboard_row(self):
        entries, _ = import_arena.parse(
            "Companion\n1 Yorion, Sky Nomad (IKO) 232\n"
            "Deck\n4 Shock (M19) 156\n"
            "Sideboard\n1 Yorion, Sky Nomad (IKO) 232")
        assert (1, "Yorion, Sky Nomad", "IKO", "232") in entries

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
        added, updated, _ = import_arena.merge(rows, [(2, "Shock", "M19", "156")], sum_mode=False)
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
        added, _, _ = import_arena.merge(rows, [(1, "Shock", "M19", "156")], sum_mode=False)
        assert added == 1 and rows[0]["Card Name"] == "Shock"

    def test_front_name_line_bumps_a_full_name_stored_printing(self):
        """BS2-02: the library stores a handful of DFCs under the full `A // B`
        name (the DSK Rooms), and Arena exports name the FRONT face — an
        exact-name key appended a second row for the same physical printing,
        silently splitting the owned count across two spellings."""
        rows = [{"Card Name": "Bottomless Pool // Locker Room", "Set Code": "DSK",
                 "Collector #": "43", "Quantity Owned": "1", "Type": "",
                 "Card Text": "", "Color(s)": "", "Synergies": ""}]
        added, updated, _ = import_arena.merge(
            rows, [(2, "Bottomless Pool", "DSK", "43")], sum_mode=False)
        assert added == 0 and updated == 1
        assert len(rows) == 1 and rows[0]["Quantity Owned"] == "2"
        assert rows[0]["Card Name"] == "Bottomless Pool // Locker Room"


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

    def test_forage_maps_to_graveyard_and_food(self):
        # Forage is a COST: "exile three cards from your graveyard or sacrifice a Food",
        # so it consumes exactly those two resources. It matters ONLY on the cards whose
        # text omits the reminder — 7 of the 9 forage cards quote it and already earn
        # both tags from text, so a text-only model looked like it worked. Traverse
        # Valley's whole text is "Kicker—Forage." and it was tagged neither.
        tags = ts.tags_for({"Type": "Sorcery", "Card Text": "Kicker—Forage."}, ["Forage"])
        assert "graveyard" in tags and "food" in tags

    def test_forage_does_not_imply_sacrifice(self):
        # Deliberately narrower than the reminder text reads: the keyword only means the
        # card MAY pay with a Food. Traverse Valley is a kicked land fetch, not a
        # sacrifice card, and cards that really do sacrifice earn the tag from their
        # own text.
        tags = ts.tags_for({"Type": "Sorcery", "Card Text": "Kicker—Forage."}, ["Forage"])
        assert "sacrifice" not in tags

    def test_renew_maps_to_graveyard_and_counters(self):
        """`renew` is the same COST+EFFECT shape as forage and maps to the two resources
        it touches: activated FROM YOUR GRAVEYARD, and it puts COUNTERS on a creature.

        Like forage — only more so — the mapping changes no stored tag: all 14 pool cards
        state the template without reminder text ("Exile this card from your graveyard:
        Put a +1/+1 counter ..."), so the TEXT rules already earn both. The mapping's real
        job is to DECLARE it a known mechanic, which is what stops it warning on every
        check_all run and keeps `is_noise_keyword` from ever suppressing it."""
        tags = ts.tags_for({"Type": "Creature — Human", "Card Text": "Renew"}, ["Renew"])
        assert "graveyard" in tags and "counters" in tags

    def test_renew_is_not_sacrifice_or_recursion(self):
        """Nothing is sacrificed, and the card never comes BACK — it is exiled to pay for
        the counters. A renew card in the yard is a resource to spend, not a rebuy, so
        tagging it `recursion` would point reanimator decks at cards that do not recur."""
        tags = ts.tags_for({"Type": "Creature — Human", "Card Text": "Renew"}, ["Renew"])
        assert "sacrifice" not in tags and "recursion" not in tags

    def test_triple_is_baselined_not_themed(self):
        """`triple` is NOT a mechanic — Scryfall surfaces the ordinary word from "deals
        triple that damage" / "Triple target creature's power". Its sibling `double`, which
        appears on the very same card (Tifa's Limit Break), was already baselined, so this
        matches the precedent rather than inventing a theme for three unrelated cards."""
        import check_keywords
        baseline = {ln.strip().lower() for ln in open(check_keywords.BASELINE,
                                                      encoding="utf-8") if ln.strip()}
        assert "triple" not in {k.lower() for k in ts.KEYWORD_THEMES}
        assert "triple" in baseline
        assert "double" in baseline, "the precedent this follows must still hold"
        # And the radar must be quiet about it — that is the whole point of the triage.
        assert not [k for k in check_keywords.check() if k[1].lower() == "triple"]


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
        entries, warn, unread = ic.parse_export(
            "Card Name,Set Code,Collector Number,Quantity\nShock,M21,159,4\n")
        assert entries == [(4, "Shock", "M21", "159")] and warn == [] and unread == []

    def test_sniffs_a_tab_separated_export(self):
        entries, _, _ = ic.parse_export("Name\tEdition\tHave\nShock\tM21\t3\n")
        assert entries == [(3, "Shock", "M21", "")]

    def test_a_non_numeric_quantity_is_reported_not_zeroed(self):
        """Silently reading a bad cell as 0 would DELETE that card's copies."""
        entries, warn, unread = ic.parse_export("Name,Count\nShock,\nBolt,two\n")
        assert entries == []
        assert len(warn) == 2 and "Shock" in warn[0]
        # BS2-03: the unreadable rows are named, so plan() can protect them from
        # the --zero-missing pass — "couldn't read the cell" must never become 0.
        assert unread == ["Shock", "Bolt"]

    def test_foil_and_nonfoil_rows_of_one_printing_SUM(self):
        """Trackers export foil and non-foil as separate rows sharing (name, set,
        collector), told apart only by a finish column. 2 foil + 2 non-foil is 4
        Arena copies; the finish-blind path collapsed them on max to 2 — and this
        is the one tool that can LOWER a count (broad-scan BS-15)."""
        entries, _, _ = ic.parse_export(
            "Name,Set,Number,Quantity,Finish\n"
            "Shock,M21,159,2,normal\nShock,M21,159,2,foil\n")
        assert entries == [(4, "Shock", "M21", "159")]

    def test_a_repeated_row_with_the_SAME_finish_still_takes_max(self):
        """One holding stated twice is not two holdings — max within a finish."""
        entries, _, _ = ic.parse_export(
            "Name,Set,Number,Quantity,Finish\n"
            "Shock,M21,159,2,foil\nShock,M21,159,2,foil\n")
        assert entries == [(2, "Shock", "M21", "159")]

    def test_no_finish_column_keeps_the_old_max_semantics(self):
        entries, _, _ = ic.parse_export(
            "Name,Set,Number,Quantity\nShock,M21,159,2\nShock,M21,159,3\n")
        assert entries == [(3, "Shock", "M21", "159")]

    def test_basics_are_skipped(self):
        entries, _, _ = ic.parse_export("Name,Count\nForest,40\nShock,4\n")
        assert [e[1] for e in entries] == ["Shock"]

    def test_no_printing_columns_SUMS_repeated_names(self):
        """BS2-04: with no set/collector column every row of a card shares the
        degenerate ("name","","") key, so two genuinely distinct printings
        (2 + 1 = 3 owned) collapsed to max = 2 — a silent LOWERING on the one
        tool that can lower a count. A tracker exports one row per printing, so
        repeated names here are distinct printings: SUM, and warn."""
        entries, warn, _ = ic.parse_export(
            "Name,Count\nLlanowar Elves,2\nLlanowar Elves,1\n")
        assert entries == [(3, "Llanowar Elves", "", "")]
        assert any("SUMMED" in w and "Llanowar Elves" in w for w in warn)

    def test_printing_columns_keep_max_on_a_true_repeat(self):
        """The max-on-repeat reading stays where the printing key is REAL —
        the same (name, set, collector) twice is one holding stated twice."""
        entries, _, _ = ic.parse_export(
            "Name,Set,Number,Quantity\nShock,M21,159,2\nShock,M21,159,2\n")
        assert entries == [(2, "Shock", "M21", "159")]

    def test_a_zero_count_is_kept(self):
        """0 is a real, meaningful value here — it is how the export says 'disenchanted'."""
        entries, _, _ = ic.parse_export("Name,Count\nShock,0\n")
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

    def test_an_unreadable_quantity_is_never_zeroed(self):
        """BS2-03: a row whose quantity cell couldn't be read was dropped from
        `entries`, and the zero pass then read "not in entries" as "absent from
        the export" — so a mis-read cell ("1,024") became 0 by a different route
        than the one the strict read guards. The export MENTIONED the card, so
        it is not absent; `unreadable` marks it seen."""
        rows = [self._row("Llanowar Elves", qty="4")]
        r = ic.plan(rows, [(1, "Other", "M21", "2")], zero_missing=True,
                    unreadable=["Llanowar Elves"])
        assert r["zeroed"] == []
        assert rows[0]["Quantity Owned"] == "4"      # untouched

    def test_unreadable_protects_via_the_front_face_too(self):
        rows = [self._row("Bottomless Pool // Locker Room", "DSK", "43", "2")]
        r = ic.plan(rows, [(1, "Other", "M21", "2")], zero_missing=True,
                    unreadable=["Bottomless Pool"])
        assert r["zeroed"] == [] and rows[0]["Quantity Owned"] == "2"

    def test_an_ambiguous_card_is_not_also_reported_as_missing(self):
        rows = [self._row("Shock", "M21", "159", "2"), self._row("Shock", "DAR", "12", "2")]
        r = ic.plan(rows, [(3, "Shock", "", "")])
        assert r["zeroed"] == []

    def test_several_export_printings_SUM_onto_one_library_row(self):
        """A tracker exports one row per PRINTING while the library may hold fewer of
        them, so both entries resolve to the same row. Assigning each in turn made the
        LAST one win and silently drop the rest — an undercount from the one tool that
        may lower a count, and the report looked clean (broad-scan F-01)."""
        rows = [self._row("Llanowar Elves", "DOM", "168", "1")]
        r = ic.plan(rows, [(2, "Llanowar Elves", "M19", "314"),
                           (1, "Llanowar Elves", "DOM", "168")])
        assert rows[0]["Quantity Owned"] == "3"
        assert r["updated"] == [("Llanowar Elves", "1", "3")]   # one NET line, not a pair

    def test_the_sum_does_not_depend_on_export_order(self):
        for entries in ([(2, "Llanowar Elves", "M19", "314"), (1, "Llanowar Elves", "DOM", "168")],
                        [(1, "Llanowar Elves", "DOM", "168"), (2, "Llanowar Elves", "M19", "314")]):
            rows = [self._row("Llanowar Elves", "DOM", "168", "1")]
            ic.plan(rows, entries)
            assert rows[0]["Quantity Owned"] == "3", entries

    def test_summing_does_not_break_a_genuine_DECREASE(self):
        """The whole point of the tool still has to work: one entry, one row, count down."""
        rows = [self._row("Shock", qty="4")]
        ic.plan(rows, [(1, "Shock", "M21", "1")])
        assert rows[0]["Quantity Owned"] == "1"

    def test_a_REPEATED_printing_is_not_summed(self):
        """Summing is right for DISTINCT printings and wrong for a repeated one: a
        tracker emitting the same (name, set, collector) twice is stating one holding
        twice, not two holdings. Identical export keys collapse on max first — the
        reading `import_arena` applies to a repeated line — so the accumulation fix
        can't over-count where the old last-wins was correct."""
        rows = [self._row("Llanowar Elves", "DOM", "168", "1")]
        ic.plan(rows, [(2, "Llanowar Elves", "DOM", "168"),
                       (2, "Llanowar Elves", "DOM", "168")])
        assert rows[0]["Quantity Owned"] == "2"

    def test_two_lines_for_one_NEW_printing_do_not_append_two_rows(self):
        """Two rows with the same (Card Name, Set Code, Collector #) is a duplicate
        printing — an INV-01 break, written by the importer itself."""
        r = ic.plan([], [(1, "Brand New", "XXX", "9"), (2, "Brand New", "XXX", "9")])
        assert r["added"] == [("Brand New", "XXX", "9", 2)]

    def test_distinct_new_printings_stay_distinct(self):
        r = ic.plan([], [(1, "Brand New", "XXX", "9"), (2, "Brand New", "YYY", "4")])
        assert r["added"] == [("Brand New", "XXX", "9", 1), ("Brand New", "YYY", "4", 2)]

    def test_a_row_that_received_a_summed_total_is_not_also_zeroed(self):
        rows = [self._row("Shock", "M21", "1", "4")]
        r = ic.plan(rows, [(2, "Shock", "M21", "1"), (1, "Shock", "M20", "5")])
        assert r["zeroed"] == [] and rows[0]["Quantity Owned"] == "3"


class TestSetlessLines:
    """BS2-24: a set-less line ('4 Llanowar Elves', a website list) keyed on
    ("name","","") which matches no real row, so merge APPENDED a phantom blank-set
    printing — and since every consumer SUMS across printings, a real 4 read as 5:
    the one over-count path in a subsystem that otherwise only undercounts."""

    def _rows(self):
        return [{"Card Name": "Llanowar Elves", "Set Code": "M19", "Collector #": "314",
                 "Quantity Owned": "4", "Type": "", "Card Text": "", "Color(s)": "",
                 "Synergies": ""}]

    def test_covered_setless_line_changes_nothing(self):
        rows = self._rows()
        added, updated, notes = import_arena.merge(rows, [(4, "Llanowar Elves", "", "")],
                                                   sum_mode=False)
        assert added == 0 and updated == 0 and len(rows) == 1
        assert rows[0]["Quantity Owned"] == "4"
        assert any("already covered" in n for n in notes)

    def test_setless_line_above_the_summed_total_tops_up_not_appends(self):
        rows = self._rows()
        added, updated, notes = import_arena.merge(rows, [(6, "Llanowar Elves", "", "")],
                                                   sum_mode=False)
        assert added == 0 and len(rows) == 1        # NO phantom blank-set row
        assert rows[0]["Quantity Owned"] == "6"      # topped up to the claimed total
        assert any("topped up" in n for n in notes)

    def test_setless_line_for_an_unknown_card_is_added_loudly(self):
        rows = []
        added, _, notes = import_arena.merge(rows, [(2, "New Card", "", "")],
                                             sum_mode=False)
        assert added == 1 and rows[0]["Set Code"] == ""
        assert any("BLANK set code" in n for n in notes)


class TestSetStampedLinesWithoutACollector:
    """BS4-04: `LINE_RE` makes the collector number OPTIONAL, so `4 Llanowar Elves (DOM)`
    parsed to ("llanowar elves","dom","") — which matches no real row, because every real
    row carries a collector number. BS2-24 routed only FULLY set-less lines through the
    summed-total comparison, so this shape still APPENDED a phantom printing beside the
    owned one, and since every consumer sums across printings a real 4 read as 8.

    It also passed INV-01 (the collector differs), and if `enrich` later backfilled the
    blank collector from the set-scoped lookup the row became an exact-duplicate printing
    — breaking INV-01 long after, and far from, the import that caused it."""

    def _rows(self):
        return [{"Card Name": "Llanowar Elves", "Set Code": "DOM", "Collector #": "168",
                 "Quantity Owned": "4", "Type": "", "Card Text": "", "Color(s)": "",
                 "Synergies": ""}]

    def test_covered_claim_appends_nothing(self):
        rows = self._rows()
        added, updated, notes = import_arena.merge(
            rows, [(4, "Llanowar Elves", "DOM", "")], sum_mode=False)
        assert added == 0 and len(rows) == 1        # NO phantom (DOM)/blank printing
        assert rows[0]["Quantity Owned"] == "4"
        assert any("already covered" in n for n in notes)

    def test_claim_above_the_total_tops_up_the_real_printing(self):
        rows = self._rows()
        added, _u, notes = import_arena.merge(
            rows, [(6, "Llanowar Elves", "DOM", "")], sum_mode=False)
        assert added == 0 and len(rows) == 1
        assert rows[0]["Quantity Owned"] == "6"
        assert any("topped up" in n for n in notes)

    def test_a_blank_collector_row_is_topped_up_not_duplicated(self):
        """G-11: `enrich` leaves Collector # blank rather than guessing an unconfirmed
        printing, so blank-collector rows are legitimate and must join, not duplicate."""
        rows = [{"Card Name": "Llanowar Elves", "Set Code": "DOM", "Collector #": "",
                 "Quantity Owned": "2", "Type": "", "Card Text": "", "Color(s)": "",
                 "Synergies": ""}]
        added, _u, _n = import_arena.merge(
            rows, [(3, "Llanowar Elves", "DOM", "")], sum_mode=False)
        assert added == 0 and len(rows) == 1
        assert rows[0]["Quantity Owned"] == "3"

    def test_unknown_card_is_still_added_and_says_what_is_missing(self):
        rows = []
        added, _u, notes = import_arena.merge(
            rows, [(2, "New Card", "DOM", "")], sum_mode=False)
        assert added == 1 and rows[0]["Set Code"] == "DOM"
        assert any("BLANK collector #" in n for n in notes)

    def test_a_fully_printed_line_still_takes_the_normal_path(self):
        """The guard must not swallow ordinary Arena exports — those carry a collector."""
        rows = self._rows()
        added, updated, _n = import_arena.merge(
            rows, [(4, "Llanowar Elves", "DOM", "168")], sum_mode=False)
        assert added == 0 and len(rows) == 1 and updated == 0


class TestBuildersAliasFrontFacesInASecondPass:
    """BS4-18: `enrich.index_card`, `build_mana._store` and `deck.fetch_missing_rarities`
    all aliased the DFC front IN-PASS with `setdefault` — the order-dependent shadowing
    `lib.alias_front`'s contract forbids. A `Front // Back` card seen early claims the
    bare `Front` key, and a genuinely distinct card of that name arriving later can never
    claim its own ("Life" is a card as well as the front of "Life // Death").

    Latent today — zero front-name collisions exist in the current Arena pool — but one
    printing away from writing another card's cost or text over a real one, silently.
    `check_dfc`'s builder scan cannot see these: it scans functions reading the POOL, and
    these index Scryfall RESPONSES."""

    def test_index_card_does_not_claim_the_front_key_in_pass(self):
        import enrich
        by_name = {}
        enrich.index_card(by_name, {"name": "Life // Death"})
        # In-pass the DFC owns only its own full name.
        assert set(by_name) == {"life // death"}

    def test_a_real_card_owning_the_front_name_is_never_shadowed(self):
        import enrich
        by_name = {}
        enrich.index_card(by_name, {"name": "Life // Death"})   # seen FIRST
        enrich.index_card(by_name, {"name": "Life", "id": "real"})
        lib.alias_front(by_name)
        # The distinct real card keeps its own name; the DFC does not shadow it.
        assert by_name["life"].get("id") == "real"

    def test_the_front_alias_is_still_added_when_nothing_claims_it(self):
        import enrich
        by_name = {}
        enrich.index_card(by_name, {"name": "Life // Death", "id": "dfc"})
        lib.alias_front(by_name)
        assert by_name["life"].get("id") == "dfc"

    def test_store_indexes_only_the_real_name_in_pass(self):
        import build_mana
        out = {}
        build_mana._store(out, {"name": "Life // Death", "cmc": 2, "mana_cost": "{B}"})
        assert set(out) == {"life // death"}
        lib.alias_front(out)
        assert "life" in out


class TestGrantedKeywordsAreTagged:
    """A card that GRANTS a keyword is a card ABOUT that keyword, and until now none of
    them were tagged for it.

    The keyword tags come from Scryfall's `keywords` field, which lists what a card HAS.
    So the theme model could not see the cards a keyword deck is built to FIND. Measured
    on the 15,973-row pool: 2,269 cards grant one of the twelve evergreen keywords and
    carried no tag for it — indestructible 223 of 229, hexproof 155 of 156, i.e. those
    keywords are almost always granted rather than native, so the tag was tracking the
    rare case.

    The live consequence, and why the fixtures below are the real cards: deck 31 is a
    Fynn deathtouch-poison deck, and Venom Connoisseur ("all creatures you control gain
    deathtouch") tagged Human/Druid/alliance/aggro/value with NO deathtouch — `cuts` fit
    17. Maximum Overdrive tagged `counters` alone — fit 4. The two lowest-fit cards in
    the deck were two of its engine pieces, and both were proposed as cuts. K-04 one
    layer over: `cuts`' fit is a predicate gated on a derived tag."""

    def _t(self, type_line, text, keywords=None):
        return ts.tags_for({"Type": type_line, "Card Text": text}, keywords or [])

    def test_the_card_that_produced_the_bug(self):
        """REAL text, per G-67's trap: a paraphrased fixture passed a pattern the real
        card refutes."""
        tags = self._t("Creature — Human Druid",
                       "Alliance — Whenever another creature you control enters, this "
                       "creature gains deathtouch until end of turn. If this is the "
                       "second time this ability has resolved this turn, all creatures "
                       "you control gain deathtouch until end of turn.", ["Alliance"])
        assert "deathtouch" in tags

    def test_a_grant_implies_the_same_themes_as_a_native_keyword(self):
        """Same tag AND same implied themes, through the same KEYWORD_THEMES table — the
        drift this fix exists to close."""
        tags = self._t("Instant", "Put a +1/+1 counter on target creature. It gains "
                                  "deathtouch and indestructible until end of turn.")
        assert {"deathtouch", "indestructible"} <= set(tags)
        assert set(ts.KEYWORD_THEMES["deathtouch"]) <= set(tags)      # combat, removal
        assert set(ts.KEYWORD_THEMES["indestructible"]) <= set(tags)  # resilience

    def test_reminder_text_does_not_count_as_a_grant(self):
        """Reminder text is parenthetical and QUOTES the keyword it explains, so a scan
        over raw text would tag every card whose reminder names one."""
        assert "flying" not in ts.granted_keywords(
            "Whenever this creature attacks, scry 1. (Look at the top card of your "
            "library. Creatures with flying can block it.)")

    def test_an_opponent_facing_grant_is_the_opposite_card(self):
        """"Creatures your opponents control gain haste" is a DRAWBACK, not a haste
        payoff."""
        assert "haste" not in ts.granted_keywords(
            "Creatures your opponents control gain haste until end of turn.")

    def test_a_negation_is_not_a_grant(self):
        assert "flying" not in ts.granted_keywords(
            "Target creature loses flying until end of turn.")

    def test_the_order_is_total_so_two_runs_cannot_disagree(self):
        """G-54: the scan iterates a TUPLE, not a set, so the tag order is stable."""
        text = ("Creatures you control have trample and haste. They also gain "
                "deathtouch until end of turn.")
        assert ts.granted_keywords(text) == [
            k for k in ts._GRANTED_KEYWORDS if k in ts.granted_keywords(text)]

    def test_a_granted_NON_evergreen_keyword_is_read_too(self):
        """The list shipped as the twelve evergreens, so a card that GRANTED any other
        keyword was invisible while a card that HAD it was tagged — G-80's own asymmetry,
        one keyword over. Found 2026-09-02: `check_themes` flagged Dazzling Theater
        ("Creature spells you cast have convoke") and `tags_for` returned only ['Room']."""
        assert "convoke" in ts.granted_keywords(
            "Creature spells you cast have convoke.")
        assert "ward" in ts.granted_keywords(
            "Each other Human you control gets +1/+0 and has ward {1}.")
        assert "affinity" in ts.granted_keywords(
            "Spells you cast have affinity for artifacts.")
        assert "prowess" in ts.granted_keywords("Creatures you control have prowess.")

    def test_the_added_keywords_are_ones_the_project_already_tags(self):
        """The widening introduces no new THEME: every added keyword already resolves
        through `KEYWORD_THEMES`, which is what makes a granted one tag exactly like a
        native one. A keyword with no theme mapping would tag a bare string nothing reads."""
        for kw in ("ward", "convoke", "affinity", "prowess", "flash"):
            assert kw in ts._GRANTED_KEYWORDS
            assert ts.KEYWORD_THEMES.get(kw), kw

    def test_cascade_was_considered_and_left_out(self):
        """Zero pool cards grant it, and an unexercised whitelist entry is one nobody can
        check. Recorded as a decision so it is not silently re-added."""
        assert "cascade" not in ts._GRANTED_KEYWORDS

    def test_the_new_keywords_keep_the_opponent_and_negation_guards(self):
        assert "ward" not in ts.granted_keywords(
            "Creatures your opponents control have ward {2}.")
        assert "convoke" not in ts.granted_keywords(
            "Creature spells you cast lose convoke.")

    def test_a_card_that_grants_nothing_is_untouched(self):
        assert ts.granted_keywords("Draw a card.") == []



class TestArenaAboutBlockAndSameRunPhantom:
    def test_the_name_line_under_about_is_not_a_parse_failure(self):
        """BS8-08: every modern Arena export carries `About / Name <deck>` above `Deck`;
        the Name line raised "could not parse" (and "never ingested by ANY tool")."""
        entries, warnings = import_arena.parse("About\nName 49 Big Draco\nDeck\n1 Opt (M21) 59\n")
        assert [e[1] for e in entries] == ["Opt"]
        assert warnings == []

    def test_a_name_only_line_after_a_printed_line_in_one_paste_does_not_phantom(self):
        """BS8-35: `by_front` was built once before the merge loop, so a name-only line
        for a card whose printed line was appended in the SAME paste created a blank-set
        phantom row — 2 (AA1) + 3 name-only read as owned 5 against a lower bound of 3."""
        rows = []
        entries = [(2, "Champion's Helm", "AA1", "3"), (3, "Champion's Helm", "", "")]
        import_arena.merge(rows, entries, sum_mode=False)
        assert len(rows) == 1, rows
        assert rows[0]["Set Code"] == "AA1" and rows[0]["Quantity Owned"] == "3"
