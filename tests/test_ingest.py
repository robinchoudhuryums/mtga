"""Unit tests for the ingest/tagging pure functions: import_arena parsing and the
tag_synergies heuristics (the source of every synergy tag downstream code relies on)."""
import import_arena
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
