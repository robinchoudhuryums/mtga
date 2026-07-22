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
