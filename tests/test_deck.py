"""Unit tests for the pure analysis helpers in scripts/deck.py.

Covers the mana-pip parser, the canonical role tally, tier floor, engine-role
classifier, rotation math, and the git-independent card-delta arithmetic — the
functions the whole grading/ranking stack is built on. The check_* gates assert the
same models at the integration level; these pin the isolated edge cases fast."""
from datetime import date, timedelta

import pytest

import deck
import lib


class TestParsePips:
    def test_strict_pips(self):
        strict, hybrid = deck.parse_pips("{2}{W}{U}")
        assert strict == {"W": 1, "U": 1}
        assert hybrid == []

    def test_true_multicolor_hybrid(self):
        strict, hybrid = deck.parse_pips("{W/U}")
        assert strict == {}
        assert hybrid == [frozenset({"W", "U"})]

    def test_monocolor_hybrid_is_len1(self):
        # {2/W} is payable without W, so it must not constrain castable colors.
        _strict, hybrid = deck.parse_pips("{2/W}")
        assert hybrid == [frozenset({"W"})]
        assert all(len(h) < 2 for h in hybrid)

    def test_phyrexian_is_len1(self):
        _strict, hybrid = deck.parse_pips("{W/P}")
        assert all(len(h) < 2 for h in hybrid)

    def test_empty(self):
        assert deck.parse_pips("") == ({}, [])

    def test_split_cost_reads_only_the_front_face(self):
        """Funeral Room's `{2}{B} // {6}{B}{B}`. You never pay both halves, so the
        merged string wanted three black pips where the door you cast wants one."""
        strict, _hybrid = deck.parse_pips("{2}{B} // {6}{B}{B}")
        assert strict == {"B": 1}

    def test_adventure_cost_reads_only_the_creature_half(self):
        # Emeritus of Abundance `{2}{G} // {1}{G}` — one green pip, not two.
        strict, _hybrid = deck.parse_pips("{2}{G} // {1}{G}")
        assert strict == {"G": 1}

    def test_single_face_cost_is_unchanged(self):
        assert deck.parse_pips("{5}{W}{B}")[0] == {"W": 1, "B": 1}


class TestSplitCostMana:
    """A split / Room / Adventure card stores both halves joined by ' // '. The RULES
    mana value is the combined total, which is not what a curve or a cast-on-curve
    probability wants — Funeral Room came through as MV 11."""

    def test_front_face_cost(self):
        assert lib.front_face_cost("{2}{B} // {6}{B}{B}") == "{2}{B}"
        assert lib.front_face_cost("{5}{W}{B}") == "{5}{W}{B}"
        assert lib.front_face_cost("") == ""
        assert lib.front_face_cost(None) == ""

    def test_mana_value_counts_generic_plus_one_per_symbol(self):
        assert lib.mana_value("{2}{B}") == 3
        assert lib.mana_value("{5}{W}{B}") == 7
        assert lib.mana_value("{W/U}{2}") == 3       # a hybrid symbol is ONE mana
        assert lib.mana_value("{W/P}") == 1
        assert lib.mana_value("{2/G}{2/G}") == 4     # monocolor hybrid: larger half (CR 202.3f)
        assert lib.mana_value("") == 0

    def test_x_counts_zero(self):
        # Off the stack, X is 0 — the same rule the stored values follow.
        assert lib.mana_value("{X}{B}{B}") == 2

    def test_room_mana_value_is_the_front_door(self):
        assert lib.mana_value(lib.front_face_cost("{2}{B} // {6}{B}{B}")) == 3

    def test_adventure_value_agrees_with_the_stored_one(self):
        # Scryfall already stores the front-face value for Adventure cards, so
        # recomputing must AGREE with them and only correct the split/Room shape.
        for cost, stored in (("{2}{G} // {1}{G}", 3), ("{U} // {U}", 1),
                             ("{4}{W} // {1}{W}", 5), ("{2}{G}{U} // {G}{U}", 4)):
            assert lib.mana_value(lib.front_face_cost(cost)) == stored, cost


class TestClassifyRoles:
    def test_spot_removal(self):
        assert "Removal (spot)" in deck.classify_roles("Destroy target creature.")

    def test_card_advantage(self):
        assert "Card advantage" in deck.classify_roles("Draw two cards.")

    def test_single_cantrip_not_card_advantage(self):
        # A one-card draw is deliberately NOT counted as card advantage.
        assert "Card advantage" not in deck.classify_roles("Draw a card.")

    def test_vanilla_has_no_interaction_role(self):
        # Combat keywords are not functional interaction/card-advantage.
        roles = deck.classify_roles("Flying. Vigilance.")
        assert not (roles & deck._INTERACTION_ROLES)
        assert "Card advantage" not in roles

    # --- Under-count fixes. Each string below scored ZERO roles before the list-aware
    # removal pattern / widened Counter pattern / library-tuck pattern went in, so the
    # cards read as having no interaction at all and the tier floor graded on that.
    NONCREATURE_REMOVAL = [
        # Origin of Metalbending, Seedship Impact — a two-type "or" list.
        "Destroy target artifact or enchantment.",
        # Broken Wings, Shattered Wings, Spider Food — a comma list ending in a creature.
        "Destroy target artifact, enchantment, or creature with flying.",
    ]
    ADJECTIVE_REMOVAL = [
        # The hand-kept alternation spelled these out; the rewrite must not lose them.
        "Destroy target creature.", "Exile target attacking creature.",
        "Destroy target tapped creature.", "Destroy target nonland permanent.",
        "Exile target creature or planeswalker.",
    ]

    def test_noncreature_permanent_removal_counts(self):
        for text in self.NONCREATURE_REMOVAL:
            assert "Removal (spot)" in deck.classify_roles(text), text

    def test_adjective_and_plain_removal_still_counts(self):
        for text in self.ADJECTIVE_REMOVAL:
            assert "Removal (spot)" in deck.classify_roles(text), text

    # ── Variable damage in TARGET-FIRST word order. Both pre-existing variable-damage
    # patterns assume "equal to X" precedes "to target"; Magic also templates it the
    # other way round. Fixtures are the cards' REAL text (G-67), not paraphrases.

    TARGET_FIRST_VARIABLE_DAMAGE = [
        # Triumphant Chomp — a {R} sorcery that kills anything up to a 12/12, scored
        # ZERO roles, and `cuts` therefore ranked it deck 28's WEAKEST card.
        "Triumphant Chomp deals damage to target creature equal to 2 or the greatest "
        "power among Dinosaurs you control, whichever is greater.",
        "Rumbling Rockslide deals damage to target creature equal to the number of "
        "lands you control.",
        "When this creature enters, it deals damage to target creature an opponent "
        "controls equal to the number of Goblins you control.",
    ]

    def test_target_first_variable_damage_is_removal(self):
        for text in self.TARGET_FIRST_VARIABLE_DAMAGE:
            assert "Removal (spot)" in deck.classify_roles(text), text

    def test_player_only_variable_damage_is_still_not_removal(self):
        # BS2-06's guard: player-only burn read as spot removal and 14 decks over-read
        # the interaction axis. Widening the pattern must not re-open that.
        assert "Removal (spot)" not in deck.classify_roles(
            "When this creature enters, it deals damage to each player equal to the "
            "number of nonbasic lands that player controls.")

    def test_damage_to_a_target_spells_controller_is_not_removal(self):
        # Refuse — "target spell's controller" is a PLAYER, and it was the only false
        # positive when this pattern was measured against the whole pool.
        assert "Removal (spot)" not in deck.classify_roles(
            "Refuse deals damage to target spell's controller equal to that spell's "
            "mana value.")

    def test_counter_up_to_n_target_counts(self):
        # Repulsive Mutation. Missed by the Counter pattern AND by the coverage net,
        # so the under-read was invisible to the audit meant to catch it.
        assert "Counter" in deck.classify_roles(
            "Put X +1/+1 counters on target creature you control. Then counter up to one "
            "target spell unless its controller pays mana equal to the greatest power "
            "among creatures you control.")

    def test_reversed_avg_mv_phrasing_is_read_both_ways(self):
        # The rationale audit carries number-first patterns for interaction, card
        # advantage, protection, early drops and "N curve" — but the avg-MV reversal was
        # only ever taught the word "curve", and the FORWARD pattern needs "average" to be
        # followed by MV. So a bare "3.19 average" matched in neither direction, and deck
        # 53's prose quoted 3.19 against a live 3.39 while the audit reported it CURRENT.
        for probe in ["3.19 average", "3.19 curve", "avg MV 3.19", "Average nonland MV 3.19"]:
            keys = [k for rx, k in deck._RATIONALE_FIGURES if rx.search(probe)]
            assert "avg_mv" in keys, probe

    def test_split_choose_then_destroy_is_removal(self):
        # Quag Feast: the target is named in one sentence and the destroy verb lands in a
        # later one, with "the chosen permanent" standing in for it. The main removal
        # pattern needs destroy|exile immediately before "target", so this card scored
        # ZERO roles — invisible to the interaction count the tier floor grades on, not
        # merely to the noncreature-answer profile.
        assert "Removal (spot)" in deck.classify_roles(
            "Choose target creature, planeswalker, or Vehicle. Mill two cards, then "
            "destroy the chosen permanent if its mana value is less than or equal to "
            "the number of cards in your graveyard.")

    def test_creature_or_enchantment_answers_a_noncreature_permanent(self):
        # The planeswalker cues allowed any text between "target" and the type; the
        # artifact/enchantment cues required the type IMMEDIATELY after "target". So
        # "creature or PLANESWALKER" counted and "creature or ENCHANTMENT" did not —
        # the same list templated the other way round. Withering Torment and Feed the
        # Swarm were the only two enchantment answers on the roster, and neither counted.
        for text in [
            "Destroy target creature or enchantment. You lose 2 life.",
            "Destroy target creature or enchantment an opponent controls. You lose life "
            "equal to that permanent's mana value.",
        ]:
            assert any(p.search(text.lower()) for p in deck._NONCREATURE_ANSWER_CUES), text

    def test_plain_creature_removal_is_not_a_noncreature_answer(self):
        # The guard on the fix above: sentence-bounded `[^.]*` must not reach a later
        # sentence that merely mentions an artifact.
        text = "destroy target creature. create a food token. (it's an artifact with \"{2}, " \
               "{t}, sacrifice this token: you gain 3 life.\")"
        assert not any(p.search(text) for p in deck._NONCREATURE_ANSWER_CUES), text

    def test_any_colour_source_is_ramp_fixing(self):
        # The ramp pattern required a literal `{` right after "add", so it read
        # "{T}: Add {G}" and missed "{T}: Add one mana of any color" — i.e. EVERY rainbow
        # source. Bloom Tender, Great Divide Guide, Springleaf Drum and Agatha's Soul
        # Cauldron all scored ZERO roles, in decks whose #1 weakness is the manabase.
        for text in [
            "Vivid — {T}: For each color among permanents you control, add one mana of that color.",
            'Each land and Ally you control has "{T}: Add one mana of any color."',
            "{T}, Tap an untapped creature you control: Add one mana of any color.",
            "You may spend mana as though it were mana of any color to activate abilities "
            "of creatures you control.",
            "Lands you control gain all basic land types until end of turn. Draw a card.",
        ]:
            assert "Ramp / fixing" in deck.classify_roles(text), text

    def test_cast_from_top_of_library_is_card_advantage(self):
        # A permanent draw substitute — Vizier of the Menagerie, Bolas's Citadel. Scored
        # nothing. Etali's "each player's library" was missed by the your-library scoping.
        assert "Card advantage" in deck.classify_roles(
            "You may look at the top card of your library any time. You may cast creature "
            "spells from the top of your library.")
        assert "Card advantage" in deck.classify_roles(
            "Whenever Etali attacks, exile the top card of each player's library, then you "
            "may cast any number of spells from among them without paying their mana costs.")

    def test_clue_token_is_card_advantage(self):
        # `investigate` was indexed but the spelled-out token was not, so The Mechanist —
        # a Clue per noncreature spell — scored Payoff/engine only and a deck built on it
        # read card advantage 0. A Clue IS a delayed draw.
        assert "Card advantage" in deck.classify_roles(
            "Whenever you cast a noncreature spell, create a Clue token. (It's an artifact "
            'with "{2}, Sacrifice this token: Draw a card.")')

    def test_impulse_is_card_advantage(self):
        # "Exile the top card of your library. You may play that card this turn" is a card
        # you would not otherwise have had. Nothing matched it: Zuko, Exiled Prince scored
        # ZERO roles, and deck 45 — built entirely on cast-from-exile — read 0.
        for text in [
            "{3}: Exile the top card of your library. You may play that card this turn.",
            "At the beginning of your upkeep, exile the top two cards of your library. "
            "You may play them this turn.",
        ]:
            assert "Card advantage" in deck.classify_roles(text), text

    def test_plain_library_exile_is_not_card_advantage(self):
        # The guard: exiling from a library without permission to play it is not advantage.
        assert "Card advantage" not in deck.classify_roles(
            "Exile the top card of your library. If it's a land card, you lose 2 life.")

    def test_scaling_damage_to_a_target_is_removal(self):
        # The only scaling-damage pattern hard-coded "power", so a spell whose size comes
        # from a COUNT read as nothing. Combustion Technique scored ZERO roles in the deck
        # that lists it under `#: protect:` — same failure as Quag Feast above.
        assert "Removal (spot)" in deck.classify_roles(
            "Combustion Technique deals damage equal to 2 plus the number of Lesson cards "
            "in your graveyard to target creature. If that creature would die this turn, "
            "exile it instead.")
        assert "Removal (spot)" in deck.classify_roles(
            "When this creature enters, it deals damage equal to the number of Swamps you "
            "control to any target.")

    def test_scaling_damage_to_a_player_is_not_removal(self):
        # The guard on the fix above, and the ONLY false-positive class a roster sweep of
        # the first draft found across 116 newly-matched cards: damage aimed at a player is
        # reach, not an answer. Gravitic Punch, Sif's Spearmaster, Runebound Wolf.
        for text in [
            "Target creature you control deals damage equal to its power to target player.",
            "{3}{R}, {T}: This creature deals damage equal to the number of Wolves and "
            "Werewolves you control to target opponent.",
        ]:
            assert "Removal (spot)" not in deck.classify_roles(text), text

    def test_divided_damage_is_removal(self):
        # Every fixed-damage pattern expects "to target"/"to any target" right after the
        # number; the Fiery Confluence template says "divided as you choose among" instead.
        assert "Removal (spot)" in deck.classify_roles(
            "Arc Lightning deals 3 damage divided as you choose among one, two, or three "
            "targets.")
        assert "Removal (spot)" in deck.classify_roles(
            "Whenever you cast a noncreature spell, create a tapped Treasure token and put "
            "a plan counter on this enchantment. When the fourth plan counter is put on "
            "this enchantment, sacrifice it. When you do, it deals 7 damage divided as you "
            "choose among one or two targets.")

    def test_library_tuck_is_removal(self):
        # Floodpits Drowner's activated ability — the creature leaves the battlefield.
        assert "Removal (spot)" in deck.classify_roles(
            "{1}{U}, {T}: Shuffle this creature and target creature with a stun counter "
            "on it into their owners' libraries.")

    def test_equal_draw_discard_loot_is_not_card_advantage(self):
        # Kiora, the Rising Tide: net zero cards, so not advantage — the same rule that
        # excludes a single-draw cantrip.
        assert "Card advantage" not in deck.classify_roles(
            "When Kiora enters, draw two cards, then discard two cards.")

    def test_net_positive_draw_survives_the_loot_filter(self):
        # Draw 3 / discard 1 is +2 cards: the loot filter must not swallow it.
        assert "Card advantage" in deck.classify_roles("Draw three cards. Discard a card.")
        # And a loot alongside a real draw keeps the role.
        assert "Card advantage" in deck.classify_roles(
            "Draw two cards, then discard two cards. Then draw three cards.")

    def test_half_x_draw_counts(self):
        # Wan Shi Tong, Librarian — "draw half X cards" was in neither the role pattern
        # nor the audit cue, so it was uncounted AND unflagged.
        assert "Card advantage" in deck.classify_roles(
            "When this creature enters, put X +1/+1 counters on him. Then draw half X "
            "cards, rounded down.")

    # --- Second under-count sweep. Driven by the roster-wide coverage audit itself: the
    # `role_coverage_flags` lists named 26 distinct under-read and 98 unclassified cards,
    # and reading their oracle text turned up these seven templatings. Each scored ZERO
    # matching roles before, so the tier floor graded 34 of 58 decks on a low number.
    BOUNCE = [
        # THE BIG ONE. The pattern read `(?:owner|their) hand`, which requires the literal
        # text "owner hand" — but MTG writes "to its OWNER'S hand". So every unconditional
        # bounce spell in the collection scored nothing, for the whole life of the pattern.
        "Return target nonland permanent to its owner's hand. If you controlled that "
        "permanent, draw a card.",
        "Return target creature an opponent controls to its owner's hand.",
        "Return target creature to its owner's hand.",
        "Return up to one target artifact or enchantment to its owner's hand.",
        "Return target permanent to their owner's hand.",
    ]
    EDICTS = [
        # Tribute to Hunger / Cornered by Black Mages. An edict answers hexproof, and it
        # sat in the broad audit cue while missing from the role list entirely.
        "Target opponent sacrifices a creature of their choice.",
        "Each player sacrifices a creature of their choice.",
        "Each opponent sacrifices a permanent of their choice.",
    ]

    def test_bounce_to_owners_hand_is_removal(self):
        for text in self.BOUNCE:
            assert "Removal (spot)" in deck.classify_roles(text), text

    def test_edict_is_removal(self):
        for text in self.EDICTS:
            assert "Removal (spot)" in deck.classify_roles(text), text

    def test_x_damage_is_removal(self):
        # Hell to Pay. The fixed-damage patterns all require a DIGIT.
        assert "Removal (spot)" in deck.classify_roles(
            "Hell to Pay deals X damage to target creature. Create a number of tapped "
            "Treasure tokens equal to the amount of excess damage dealt to that creature.")

    def test_aura_library_tuck_is_removal(self):
        # Watery Grasp — the Aura form of the tuck already covered as an activated ability.
        assert "Removal (spot)" in deck.classify_roles(
            "Enchant creature\nWaterbend {5}: Enchanted creature's owner shuffles it into "
            "their library.")

    def test_mass_edict_is_a_sweeper(self):
        # Bringer of the Last Gift is a wrath by another name.
        assert "Sweeper" in deck.classify_roles(
            "When this creature enters, if you cast it, each player sacrifices all other "
            "creatures they control.")

    def test_repeatable_upkeep_draw_is_card_advantage(self):
        # Phyrexian Arena. A REPEATABLE single draw accrues advantage — the cantrip
        # exclusion is about ONE-SHOT single draws, and reading Arena as a cantrip is why
        # deck 42's card-advantage line said 1.
        assert "Card advantage" in deck.classify_roles(
            "At the beginning of your upkeep, you draw a card and you lose 1 life.")
        # ...and a one-shot single draw is still not advantage.
        assert "Card advantage" not in deck.classify_roles(
            "When this creature enters, draw a card.")

    def test_repeatable_draw_on_a_non_upkeep_phase_is_card_advantage(self):
        """The phase was hardcoded to `upkeep` while Magic puts the same recurring draw
        on the end step just as often. Haliya, Guided by Light drew every turn the deck
        gained 3 life and scored zero card advantage for it."""
        assert "Card advantage" in deck.classify_roles(
            "Whenever Haliya or another creature or artifact you control enters, you gain "
            "1 life.\nAt the beginning of your end step, draw a card if you've gained 3 or "
            "more life this turn.")

    def test_a_whenever_triggered_draw_is_card_advantage(self):
        """`Whenever X, draw a card` recurs by construction. Exemplar of Light draws on
        every turn it gets a counter; it was read as a cantrip."""
        assert "Card advantage" in deck.classify_roles(
            "Whenever you gain life, put a +1/+1 counter on this creature.\nWhenever you "
            "put one or more +1/+1 counters on this creature, draw a card. This ability "
            "triggers only once each turn.")

    def test_a_draw_PAYOFF_is_not_card_advantage(self):
        """The false-positive class the comma discriminator exists for, and the one that
        makes this a discrimination problem rather than a widening one. `Whenever you
        draw a card, <effect>` puts the draw in the CONDITION — the card CARES about
        drawing, it does not draw. A naive `whenever .* draw a card` scored 45 pool cards
        (Chasm Skulker, Orcish Bowmasters, Queza) as card advantage, which is backwards.
        Magic templates a trigger as `Whenever <condition>, <effect>`, so requiring the
        draw to fall after the comma separates the two."""
        assert "Card advantage" not in deck.classify_roles(
            "Whenever you draw a card, put a +1/+1 counter on this creature.")
        assert "Card advantage" not in deck.classify_roles(
            "Flash\nWhenever an opponent draws a card, this creature deals 1 damage to "
            "that player.")
        # A trigger whose CONDITION contains commas must still match on the effect side.
        assert "Card advantage" in deck.classify_roles(
            "Whenever a Cleric, Rogue, Warrior, or Wizard you control enters, draw a card.")

    # --- K-14: a draw reached by PAYING a cost. Every pattern in this bucket was
    # trigger-shaped, so an activated ability — repeatable by construction, which is the
    # same argument the `whenever` pattern rests on — matched nothing at all. 187 pool
    # cards, 24 of them planeswalkers. Every text below is a card's REAL oracle text,
    # newlines included: the line anchor is load-bearing and a paraphrase would not
    # exercise it.

    def test_activated_ability_draw_is_card_advantage(self):
        """Arcane Encyclopedia, Spectral Sailor, Kingpin's Enforcers — a cost you can pay
        again next turn is a draw engine, not a cantrip."""
        assert "Card advantage" in deck.classify_roles("{3}, {T}: Draw a card.")
        assert "Card advantage" in deck.classify_roles(
            "Flash (You may cast this spell any time you could cast an instant.)\nFlying\n"
            "{3}{U}: Draw a card.")
        assert "Card advantage" in deck.classify_roles(
            "Lifelink\n{2}{B}, Sacrifice an artifact or creature: Draw a card.")

    def test_loyalty_ability_draw_is_card_advantage(self):
        """Chandra, Spark Hunter. Her draw sits one sentence past the cost behind an
        'If you do', which is why the second pattern exists — and why the original
        measurement of this bug missed the card that demonstrates it."""
        assert "Card advantage" in deck.classify_roles(
            "At the beginning of combat on your turn, choose up to one target Vehicle you "
            "control. Until end of turn, it becomes an artifact creature and gains "
            "haste.\n+2: You may sacrifice an artifact or discard a card. If you do, draw "
            "a card.\n0: Create a 3/2 colorless Vehicle artifact token with crew 1.")
        # Professor Dellian Fel — the plain in-sentence loyalty draw.
        assert "Card advantage" in deck.classify_roles(
            "+2: You gain 3 life.\n0: You draw a card and lose 1 life.\n−3: Destroy "
            "target creature.")

    def test_ability_word_gated_activation_still_counts(self):
        """Raving Visionary, Jodah's Codex, Thought Shucker. An ability word pushes the
        cost off the line start; measured at exactly these three cards, so widening the
        prefix further needs the same measurement re-run."""
        assert "Card advantage" in deck.classify_roles(
            "{U}, {T}: Draw a card, then discard a card.\nDelirium — {2}{U}, {T}: Draw a "
            "card. Activate only if there are four or more card types among cards in your "
            "graveyard.")
        assert "Card advantage" in deck.classify_roles(
            "Domain — {5}, {T}: Draw a card. This ability costs {1} less to activate for "
            "each basic land type among lands you control.")

    def test_rummaging_cost_is_not_card_advantage(self):
        """Charging Strifeknight, Professor Zei. Discarding to draw is card-NEUTRAL —
        the same rule `_LOOT_RE` implements one clause over. The only difference is which
        side of the colon the discard sits on."""
        assert "Card advantage" not in deck.classify_roles(
            "Haste\n{T}, Discard a card: Draw a card.")
        assert "Card advantage" not in deck.classify_roles(
            "{T}, Discard a card: Draw a card.\n{1}, {T}, Sacrifice Professor Zei: Return "
            "target instant or sorcery card from your graveyard to your hand.")

    def test_self_sacrifice_draw_is_a_cantrip_not_an_engine(self):
        """Aether Spellbomb and the common `Sacrifice this land: Draw a card` tapland
        cycle. Consuming the source makes it a ONE-SHOT single draw, which the cantrip
        rule above already excludes. Counting these took the change from 24 decks to 58
        and would have re-graded the roster off a flood-insurance land."""
        assert "Card advantage" not in deck.classify_roles(
            "{U}: Return target creature to its owner's hand.\n{1}, Sacrifice this "
            "artifact: Draw a card.")
        assert "Card advantage" not in deck.classify_roles(
            "This land enters tapped.\n{T}: Add {G} or {W}.\n{4}, {T}, Sacrifice this "
            "land: Draw a card.")
        # Sacrificing something ELSE is repeatable and DOES count (Ayara, Technodrome).
        assert "Card advantage" in deck.classify_roles(
            "{T}, Sacrifice another black creature: Draw a card.")

    def test_activated_loot_is_not_card_advantage(self):
        """Bag of Holding, Collector's Vault, Merfolk Looter. Before the singular pair was
        added to `_LOOT_RE`, nothing matched a bare `draw a card`, so a looter was excluded
        by ACCIDENT rather than by rule — and the moment a cost-shaped pattern landed it
        would have scored as a draw engine."""
        assert "Card advantage" not in deck.classify_roles("{T}: Draw a card, then discard a card.")
        assert "Card advantage" not in deck.classify_roles(
            "Whenever you discard a card, exile that card from your graveyard.\n"
            "{2}, {T}: Draw a card, then discard a card.")
        # Connive's reminder text is the same singular pair, and must not be swept in.
        assert "Card advantage" not in deck.classify_roles(
            "Whenever this creature attacks, it connives. (Draw a card, then discard a "
            "card. If you discarded a nonland card, put a +1/+1 counter on it.)")

    def test_reminder_text_cost_does_not_grant_the_role(self):
        """The line anchor's real job. A Clue's reminder text quotes `{2}, Sacrifice this
        artifact: Draw a card.` mid-line, so a card that merely MAKES one must not pick up
        the role from the quote — an over-count is the one failure this bucket has never
        had, and the anchor is what keeps it that way."""
        assert "Card advantage" not in deck.classify_roles(
            "When this creature enters, put a +1/+1 counter on target creature.\n"
            "{2}, {T}: Create a Blood token. (It's an artifact with \"{1}, {T}, Discard a "
            "card, Sacrifice this artifact: Draw a card.\")")
        # The control case: a CLUE maker does get the role — from the `create a clue
        # token` clause that has always been in this bucket, not from the quoted cost.
        # Same reminder-text shape, opposite answer, so the assertion above is testing the
        # anchor rather than an accident of these two cards.
        assert "Card advantage" in deck.classify_roles(
            "{2}, {T}: Create a Clue token. (It's an artifact with \"{2}, Sacrifice this "
            "artifact: Draw a card.\")")

    def test_the_under_read_channel_now_sees_these(self):
        """The half that made the miss invisible: both cards got SOME role (Payoff,
        Lifegain), so `unclassified` could never name them, and the broad `_CA_CUES` net
        missed the same phrasing the precise pattern did — the 'missable by BOTH' failure
        the superset property exists to prevent."""
        exemplar = ("Whenever you gain life, put a +1/+1 counter on this creature.\n"
                    "Whenever you put one or more +1/+1 counters on this creature, draw "
                    "a card. This ability triggers only once each turn.")
        cards = [(1, "Exemplar of Light", "FDN", "733")]
        carddata = {"exemplar of light": {"name": "Exemplar of Light",
                                          "type": "Creature — Angel", "text": exemplar}}
        unclassified, under_read, _ = deck.role_coverage_flags(cards, carddata)
        # Now that the pattern matches, it is a COUNTED role rather than a flagged one.
        assert "Card advantage" in deck.classify_roles(exemplar)
        assert not [a for n, a in under_read if "card advantage" in a]
        assert "Exemplar of Light" not in unclassified

    def test_fixed_damage_to_each_opponent_is_burn(self):
        assert "Burn / drain" in deck.classify_roles(
            "At the beginning of each end step, if you put a counter on a creature this "
            "turn, this enchantment deals 2 damage to each opponent.")


class TestCoverageNetIsSuperset:
    """The audit net must see everything the precise classifier can, or a phrasing is
    missed by BOTH — the hole that hid Repulsive Mutation's counter."""

    def test_interaction_net_covers_every_precise_pattern(self):
        for label in deck._INTERACTION_ROLES:
            for pat in deck._ROLE_COMPILED_MAP[label]:
                assert pat in deck._INT_CUE_PATS, f"{label}: {pat.pattern}"

    def test_card_advantage_net_covers_every_precise_pattern(self):
        for pat in deck._ROLE_COMPILED_MAP["Card advantage"]:
            assert pat in deck._CA_CUE_PATS, pat.pattern

    def test_reminder_text_does_not_fake_a_missed_role(self):
        """Ward's reminder text ends '…counter it unless that player pays {2}.', which
        tripped the Counter cue — so every warded creature was reported as a missed
        interaction piece. The list exists to be read card-by-card, so a false cue is the
        one thing that degrades it."""
        warded = {"name": "Warded Body", "type": "Creature — Human",
                  "text": ("Ward {2} (Whenever this creature becomes the target of a "
                           "spell or ability an opponent controls, counter it unless "
                           "that player pays {2}.)"),
                  "colors": "W", "power": "2", "toughness": "2"}
        carddata = {"warded body": warded}
        cards = [(1, "Warded Body", None, None)]
        _unclassified, under_read, _no_data = deck.role_coverage_flags(cards, carddata)
        assert under_read == [], under_read

    def test_reminder_stripping_does_not_hide_a_real_miss(self):
        """The strip only applies to the audit net, and the net includes the precise
        patterns — so a genuine under-read outside reminder text is still reported."""
        carddata = {"odd answer": {
            "name": "Odd Answer", "type": "Instant",
            "text": "Target player sacrifices a nonland permanent of their choice.",
            "colors": "B", "power": "", "toughness": ""}}
        _unclassified, under_read, _no_data = deck.role_coverage_flags(
            [(1, "Odd Answer", None, None)], carddata)
        assert [n for n, _axis in under_read] == ["Odd Answer"]


class TestZoneConflict:
    """The MIRROR of cost_upside_flags: a fine card that fights your own engine.

    Every card in here is quoted from a REAL pool card, because the two bugs this
    detector had on its first run were both invisible to invented strings — Strategic
    Betrayal reads "exiles a creature they control AND their graveyard", so the verb and
    the zone sit at opposite ends of the clause, and Hama says "that player's graveyard"
    where the first draft only knew "target player's"."""

    def _cd(self, name, text, type_line="Instant"):
        return {name.lower(): {"name": name, "type": type_line, "text": text,
                               "colors": "B", "power": "", "toughness": ""}}

    # --- emptier scope -----------------------------------------------------------
    def test_strategic_betrayal_is_opponent_scoped_hate(self):
        assert deck.graveyard_emptier(
            "Target opponent exiles a creature they control and their graveyard."
        ) == "opponent"

    def test_pit_of_offerings_is_a_targeted_exile(self):
        assert deck.graveyard_emptier(
            "When this land enters, exile up to three target cards from graveyards."
        ) == "choose"

    def test_mass_exile_is_scoped_all(self):
        assert deck.graveyard_emptier("Exile all graveyards.") == "all"

    def test_escape_cost_is_not_hate(self):
        """90 pool cards say 'exile this card from your graveyard' — that is escape /
        flashback COST, a graveyard USER. Reading it as hate would flag the entire
        recursion family against its own deck."""
        assert deck.graveyard_emptier(
            "Escape—{3}{B}, Exile four other cards from your graveyard.") is None

    def test_delve_style_own_yard_cost_is_not_hate(self):
        assert deck.graveyard_emptier(
            "As an additional cost to cast this spell, exile three cards from your "
            "graveyard.") is None

    def test_a_heist_card_that_exiles_their_yard_is_not_hate(self):
        """Tinybones/Hama/Azula exile an opponent's graveyard IN ORDER TO CAST from it.
        They are the engine; a naive exile+graveyard rule flags them against themselves."""
        assert deck.graveyard_emptier(
            "When this enters, target opponent mills three cards. Exile up to one "
            "noncreature, nonland card from that player's graveyard. For as long as you "
            "control this, you may cast the exiled card.") is None

    # --- dependency side ---------------------------------------------------------
    def test_casting_from_their_yard_needs_their_yard(self):
        assert "opponent" in deck.graveyard_dependent(
            "You may cast that card from that player's graveyard this turn.")

    def test_a_graveyard_payoff_needs_your_own_yard(self):
        assert "own" in deck.graveyard_dependent(
            "Return target creature card from your graveyard to the battlefield.")

    # --- the pairing -------------------------------------------------------------
    def test_targeted_exile_does_not_fight_an_OWN_graveyard_deck(self):
        """You pick the yard, so in a reanimator deck you simply aim it at theirs. This
        is the discrimination that took the roster from 12 flags to 2."""
        cards = [(1, "Picker", None, None), (1, "Reanimate A", None, None),
                 (1, "Reanimate B", None, None)]
        cd = {}
        cd.update(self._cd("Picker", "Exile up to one target card from a graveyard."))
        cd.update(self._cd("Reanimate A", "Return target creature card from your graveyard to the battlefield."))
        cd.update(self._cd("Reanimate B", "Return target creature card from your graveyard to the battlefield."))
        assert deck.zone_conflict_flags(cards, cd) == []

    def test_targeted_exile_DOES_fight_a_heist_deck(self):
        cards = [(1, "Picker", None, None), (1, "Thief A", None, None),
                 (1, "Thief B", None, None)]
        cd = {}
        cd.update(self._cd("Picker", "Exile up to one target card from a graveyard."))
        for nm in ("Thief A", "Thief B"):
            cd.update(self._cd(nm, "You may cast that card from that player's graveyard this turn."))
        flags = deck.zone_conflict_flags(cards, cd)
        assert [f[0] for f in flags] == ["Picker"]
        assert sorted(flags[0][3]) == ["Thief A", "Thief B"]

    def test_mass_exile_fights_an_own_graveyard_deck(self):
        cards = [(1, "Wiper", None, None), (1, "Reanimate A", None, None),
                 (1, "Reanimate B", None, None)]
        cd = {}
        cd.update(self._cd("Wiper", "Exile all graveyards."))
        for nm in ("Reanimate A", "Reanimate B"):
            cd.update(self._cd(nm, "Return target creature card from your graveyard to the battlefield."))
        assert [f[0] for f in deck.zone_conflict_flags(cards, cd)] == ["Wiper"]

    def test_one_dependent_is_not_a_plan(self):
        """_ZONE_MIN_DEPENDENTS guards against a lone payoff manufacturing a conflict."""
        cards = [(1, "Wiper", None, None), (1, "Reanimate A", None, None)]
        cd = {}
        cd.update(self._cd("Wiper", "Exile all graveyards."))
        cd.update(self._cd("Reanimate A", "Return target creature card from your graveyard to the battlefield."))
        assert deck.zone_conflict_flags(cards, cd) == []

    def test_a_card_cannot_conflict_with_itself(self):
        cards = [(1, "Both", None, None), (1, "Thief", None, None)]
        cd = {}
        cd.update(self._cd("Both", "Exile all graveyards. You may cast that card from "
                                   "that player's graveyard this turn."))
        cd.update(self._cd("Thief", "You may cast that card from that player's graveyard this turn."))
        # Only one OTHER dependent remains, below the floor -> no flag, not a self-flag.
        assert deck.zone_conflict_flags(cards, cd) == []


class TestFlexStaleness:
    """A `#~` flex line rots silently: `swap --apply` retires only the lines invalidated
    by the swap it is performing, and the rationale audit reads `#: tier:` / `#:
    archetype:` prose and never the flex block. Five stale lines were sitting on the
    roster when this check was added."""

    DECK = """#: name: Probe
#: format: Standard
#: colors: B

Deck
4 Swamp (MSH) 291
1 Vengeful Bloodwitch (FDN) 76

#~ -Vengeful Bloodwitch | +Agent Venom | a live line: the cut card IS in the deck
#~ -Prideful Parent | +Azula, On the Hunt | STALE: the cut card already left
#~ note: a bare note has no -Out and can never be stale
#~ +Restoration Magic | | an add-only line has nothing to check against
"""

    def _write(self, tmp_path):
        p = tmp_path / "deck.txt"
        p.write_text(self.DECK, encoding="utf-8")
        return str(p)

    def test_flags_only_the_line_whose_cut_card_is_gone(self, tmp_path):
        stale = deck.flex_staleness(self._write(tmp_path))
        assert [c for c, _a, _w in stale] == ["Prideful Parent"]

    def test_reports_the_paired_add_so_the_line_is_identifiable(self, tmp_path):
        stale = deck.flex_staleness(self._write(tmp_path))
        assert stale[0][1] == "Azula, On the Hunt"

    def test_a_note_or_add_only_line_is_never_stale(self, tmp_path):
        # Nothing to check a line against when it names no -Out card.
        outs = [c for c, _a, _w in deck.flex_staleness(self._write(tmp_path))]
        assert "Restoration Magic" not in outs

    def test_clean_deck_reports_nothing(self, tmp_path):
        p = tmp_path / "deck.txt"
        p.write_text("#: name: Probe\n#: colors: B\n\nDeck\n4 Swamp (MSH) 291\n"
                     "#~ -Swamp | +Bloodfell Caves | live\n", encoding="utf-8")
        assert deck.flex_staleness(str(p)) == []

    # ── The +In side rots too, and nothing checked it. Live on deck 28 (2026-08-11):
    # `#~ -Triumphant Chomp | +Bushwhack` sat in the flex block while Bushwhack was
    # ALREADY maindecked, so the line proposed an add the deck runs. G-04 documents
    # the stale-CUT rot; this is its mirror on the other half of the same line.

    def test_flags_a_line_whose_add_card_is_already_in_the_deck(self, tmp_path):
        p = tmp_path / "deck.txt"
        p.write_text("#: name: Probe\n#: colors: B\n\nDeck\n4 Swamp (MSH) 291\n"
                     "1 Bushwhack (BRO) 174\n"
                     "#~ -Swamp | +Bushwhack | the add is already maindecked\n",
                     encoding="utf-8")
        stale = deck.flex_staleness(str(p))
        assert [(c, a) for c, a, _w in stale] == [("Swamp", "Bushwhack")]
        assert "already in the deck" in stale[0][2]

    def test_an_add_only_line_is_checked_on_its_add(self, tmp_path):
        # The old docstring said a line with no -Out "can never be stale — there is
        # nothing to check it against". There is: whether the deck already runs the +In.
        p = tmp_path / "deck.txt"
        p.write_text("#: name: Probe\n#: colors: B\n\nDeck\n4 Swamp (MSH) 291\n"
                     "1 Bushwhack (BRO) 174\n"
                     "#~ +Bushwhack | | add-only, and already here\n", encoding="utf-8")
        assert [(c, a) for c, a, _w in deck.flex_staleness(str(p))] == [("", "Bushwhack")]

    def test_a_live_add_is_not_flagged(self, tmp_path):
        p = tmp_path / "deck.txt"
        p.write_text("#: name: Probe\n#: colors: B\n\nDeck\n4 Swamp (MSH) 291\n"
                     "#~ -Swamp | +Bushwhack | a genuine craft suggestion\n",
                     encoding="utf-8")
        assert deck.flex_staleness(str(p)) == []

    def test_a_basic_land_add_is_never_a_duplicate(self, tmp_path):
        # Basics are unlimited in Arena, so "+Island" against a deck already running
        # Islands proposes ONE MORE land. Deck 51's `-Krang | +Island | THE 25TH LAND`
        # was the only false positive in the +In check's first roster sweep.
        p = tmp_path / "deck.txt"
        p.write_text("#: name: Probe\n#: colors: U\n\nDeck\n4 Island (TRK) 319\n"
                     "1 Bushwhack (BRO) 174\n"
                     "#~ -Bushwhack | +Island | the 25th land\n", encoding="utf-8")
        assert deck.flex_staleness(str(p)) == []


class TestHeaderCardStaleness:
    """`#: protect:` / `#: uncastable-ok:` entries naming a card the deck does not run.

    Found by hand on deck 26b, whose header protected Summon: Bahamut — a card that deck
    has never run. Two failures, neither visible: the entry protected NOTHING (`cuts`
    excludes protected cards by NAME, so a name matching no card drops silently out of
    the mechanism), and it inflated the build-around count the zero-protection flag
    prints, in the exact sentence used to argue the deck's tier cap. The sweep then found
    two more on deck 56, whose Boros header protected two GREEN cards that live only in
    its Gruul variant.
    """

    DECK = """#: name: Probe
#: format: Standard
#: colors: B
#: protect: Vengeful Bloodwitch; Summon: Bahamut
#: uncastable-ok: Ojer Axonil, Deepest Might; Craterhoof Behemoth

Deck
4 Swamp (MSH) 291
1 Vengeful Bloodwitch (FDN) 76
1 Ojer Axonil, Deepest Might // Temple of Power (LCI) 145
"""

    def _write(self, tmp_path):
        p = tmp_path / "deck.txt"
        p.write_text(self.DECK, encoding="utf-8")
        return str(p)

    def test_flags_the_absent_protect_entry_only(self, tmp_path):
        stale = deck.header_card_staleness(self._write(tmp_path))
        assert ("protect", "summon: bahamut") in stale
        assert not any(n == "vengeful bloodwitch" for _h, n in stale)

    def test_sweeps_uncastable_ok_too(self, tmp_path):
        """The more dangerous of the pair: `#: uncastable-ok:` SUPPRESSES a castability
        failure, so a stale entry there is a disabled check, not a disabled boost."""
        stale = deck.header_card_staleness(self._write(tmp_path))
        assert ("uncastable-ok", "craterhoof behemoth") in stale

    def test_a_dfc_named_by_its_front_face_is_not_stale(self, tmp_path):
        """G-63: the header says `Ojer Axonil, Deepest Might`, the deck line stores the
        full `Front // Back`. Joining on the raw name would report a live entry as stale —
        the exact bug `_ms_key` exists to prevent, and this join must use it."""
        stale = deck.header_card_staleness(self._write(tmp_path))
        assert not any("ojer axonil" in n for _h, n in stale)

    def test_a_deck_with_no_such_headers_reports_nothing(self, tmp_path):
        p = tmp_path / "deck.txt"
        p.write_text("#: name: Probe\n#: colors: B\n\nDeck\n4 Swamp (MSH) 291\n",
                     encoding="utf-8")
        assert deck.header_card_staleness(str(p)) == []

    def test_the_roster_is_clean(self):
        """A behavioural anchor, not a unit test: both known instances (26b, 56) are
        fixed, so a NEW one is a regression someone introduced."""
        hits = [(d["id"], h, n) for d in deck.roster_decks()
                for h, n in deck.header_card_staleness(d["path"])]
        assert hits == [], f"stale card-name header(s): {hits}"


class TestBuildabilityIsPerNameNotPerLine:
    """BS4-13. `cmd_check` has always compared TOTAL need against TOTAL owned — and said
    so in a comment — but `app.py`'s /decks overview and `check_all`'s info summary each
    re-derived the question per LINE. A deck listing 2+2 of a card owned 3 therefore read
    "buildable" on those two surfaces while `deck.py check`, the dashboard and the deck
    editor all called it short. Three implementations of one question; the two that
    drifted were the two that copied the loop instead of calling it."""

    CARDS = [(2, "Duress", "M21", "96"), (2, "Duress", "DMU", "94"),
             (1, "Shock", "M21", "159")]

    def test_requirements_sum_duplicate_lines(self):
        reqs = deck.deck_requirements(self.CARDS)
        assert [(n, q) for _k, n, _s, q in reqs] == [("Duress", 4), ("Shock", 1)]

    def test_first_seen_order_and_printing_are_kept(self):
        reqs = deck.deck_requirements(self.CARDS)
        assert [r[0] for r in reqs] == ["duress", "shock"]
        assert reqs[0][2] == "M21"          # the FIRST line's printing, as cmd_check shows

    def test_split_lines_over_total_owned_read_as_short(self):
        """The exact divergence: 2+2 against 3 owned. Per-line it passes twice."""
        missing, short = deck.deck_build_gap(self.CARDS, {"duress": 3, "shock": 4})
        assert (missing, short) == (0, 1)

    def test_enough_copies_is_buildable(self):
        missing, short = deck.deck_build_gap(self.CARDS, {"duress": 4, "shock": 1})
        assert (missing, short) == (0, 0)

    def test_absent_card_counts_as_missing_not_short(self):
        missing, short = deck.deck_build_gap(self.CARDS, {"shock": 1})
        assert (missing, short) == (1, 0)


class TestArchetypeFiguresAreAudited:
    """BS4-07: the figure half of the rationale audit read `#: tier:` ALONE while the card
    half swept `#: tier:` AND `#: archetype:`. G-27 documented both, so the doc was true of
    half the function, and deck 26a quoted "avg MV 3.05" against a live 2.97 for as long as
    it took someone to check by hand."""

    def _deck(self, tmp_path, header_block, name="Probe"):
        p = tmp_path / "deck.txt"
        p.write_text(f"#: name: {name}\n#: colors: B\n{header_block}\n\nDeck\n"
                     "4 Swamp (MSH) 291\n", encoding="utf-8")
        return {"id": "zz", "path": str(p), "name": name, "variant": None}

    def test_a_stale_figure_in_archetype_prose_is_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(deck, "deck_quality_vector", lambda d: {"interaction": 7})
        d = self._deck(tmp_path, "#: archetype: a real clock (interaction 3, fine curve).")
        _cards, figs = deck.rationale_staleness(d, carddata={})
        assert ("interaction", "3", 7) in figs

    def test_a_matching_figure_is_not_flagged(self, tmp_path, monkeypatch):
        monkeypatch.setattr(deck, "deck_quality_vector", lambda d: {"interaction": 7})
        d = self._deck(tmp_path, "#: archetype: a real clock (interaction 7, fine curve).")
        assert deck.rationale_staleness(d, carddata={})[1] == []

    def test_a_figure_about_the_card_POPULATION_is_not_a_claim_about_this_deck(
            self, tmp_path, monkeypatch):
        """Deck 49 argues "Standard's Dragons average MV 5.30, so a deck that wants to
        field several must SOLVE ITS OWN MANA" — true about the format, and the first cut
        of this fix reported it as a stale claim about the deck's own 4.03 curve."""
        monkeypatch.setattr(deck, "deck_quality_vector", lambda d: {"avg_mv": 4.03})
        d = self._deck(tmp_path, "#: archetype: Standard's Dragons average MV 5.30, so "
                                 "this deck must solve its own mana.")
        assert deck.rationale_staleness(d, carddata={})[1] == []

    def test_a_figure_about_ANOTHER_ROSTER_DECK_is_not_a_claim_about_this_one(
            self, tmp_path, monkeypatch):
        """Deck 44a's distinctness clause quotes deck 1's card advantage by NAME rather
        than by 'deck 1', which the id-based suppressor could not see."""
        monkeypatch.setattr(deck, "deck_quality_vector", lambda d: {"card_advantage": 3})
        other = deck._roster_deck_names()[0]
        d = self._deck(tmp_path, f"#: archetype: DISTINCTNESS vs {other}: it is aggro "
                                 f"with card advantage 0 — it wins by racing.")
        assert deck.rationale_staleness(d, carddata={})[1] == []

    def test_a_PARENT_deck_name_does_not_mute_a_variant_own_figure(
            self, tmp_path, monkeypatch):
        """The variant convention makes this essential: 26a is named "Iron Forge —
        Virulent", so its parent's name is a substring of its OWN. An exact-match
        exclusion suppressed the one genuinely stale figure this fix exists to catch."""
        monkeypatch.setattr(deck, "deck_quality_vector", lambda d: {"avg_mv": 2.97})
        parent = deck._roster_deck_names()[0]
        d = self._deck(tmp_path,
                       f"#: archetype: Variant of {parent}: a real clock (avg MV 3.05).",
                       name=f"{parent} — Probe")
        assert ("avg_mv", "3.05", 2.97) in deck.rationale_staleness(d, carddata={})[1]

    def test_the_roster_figure_sweep_is_clean(self):
        """Behavioural anchor: with archetype prose in scope, the roster must still be
        clean — a new hit is a rationale someone let go stale."""
        hits = [(d["id"], f) for d in deck.roster_decks()
                for f in deck.rationale_staleness(d)[1]]
        assert hits == [], f"stale rationale figure(s): {hits}"


class TestHeaderConsumersJoinOnMsKey:
    """BS4-01, the last open member of the G-63 class (was BS2-07).

    Both header readers returned raw `.lower()` names while the CONSUMERS compared them
    against a deck line's raw `.lower()` name, so a header naming a DFC by its FRONT face
    never matched a line storing the full `Front // Back` — the instruction the header
    encodes silently did nothing. It was left open on a "zero live instances" measurement
    that expired when deck 66 was drafted: its `#: protect:` header named the deck's own
    title card and `cuts` ranked that card as cuttable anyway.

    The reason it needed a TEST rather than a measurement: `header_card_staleness` (the
    G-68 gate above) has always joined on `_ms_key`, so it reported the header HEALTHY
    while the consumers could not read it. A gate that vouches for a disabled instruction
    cannot also be the thing that detects it."""

    DECK = """#: name: Probe
#: format: Standard
#: colors: B
#: protect: Eddie Brock
#: uncastable-ok: Ojer Axonil, Deepest Might

Deck
4 Swamp (MSH) 291
1 Eddie Brock // Venom, Lethal Protector (SPM) 55
1 Ojer Axonil, Deepest Might // Temple of Power (LCI) 145
"""

    def _meta(self, tmp_path):
        p = tmp_path / "deck.txt"
        p.write_text(self.DECK, encoding="utf-8")
        return deck.parse_deck_file(str(p))

    def test_readers_return_ms_key_normalized_names(self, tmp_path):
        meta, _cards = self._meta(tmp_path)
        assert deck._protected(meta) == {"eddie brock"}
        assert deck._uncastable_ok(meta) == {"ojer axonil, deepest might"}

    def test_signature_themes_reads_a_front_named_protected_dfc(self, tmp_path):
        """A real consumer, not a re-implementation of the join. The protected card's tags
        ARE the deck's signature spine, which drives KEY promotion in `fit_strength` /
        `screen` / `similar` — so a missed join quietly costs the deck its spine."""
        meta, cards = self._meta(tmp_path)
        cardmeta = {"eddie brock // venom, lethal protector": {"synergies": ["reanimator"]}}
        assert deck._signature_themes(meta, cards, cardmeta) == frozenset({"reanimator"})

    def test_castability_exempts_a_front_named_uncastable_ok_entry(self, tmp_path):
        """The more dangerous half: a miss here does not fail to protect a card, it
        silently RE-ENABLES the castability failure the header suppresses — capping the
        tier floor at C and flipping `preflight` to BLOCKED for a card working as
        designed (G-64)."""
        meta, cards = self._meta(tmp_path)
        carddata = {"ojer axonil, deepest might // temple of power":
                    {"type": "Legendary Creature — God", "colors": "R", "text": ""}}
        mana = {"ojer axonil, deepest might // temple of power": ("{2}{R}{R}", 4)}
        uncast, _off, _abil, intended = deck._castability(
            cards, {"B"}, mana, carddata, deck._uncastable_ok(meta))
        assert [n for n, _w in intended] == ["Ojer Axonil, Deepest Might // Temple of Power"]
        assert uncast == []          # NOT counted as a build error

    def test_deck_66s_protected_title_card_is_off_the_cut_list(self):
        """The live instance. Deck 66's header names the front face; the line stores the
        full name. Behavioural anchor against the real roster."""
        d = deck.find_deck("66")
        if not d:                                  # roster-dependent, skip if renumbered
            return
        _rows, _central, prot_present, _int = deck.rank_cut_candidates(d)
        assert any(p.startswith("Eddie Brock") for p in prot_present), prot_present


class TestLifegainRoleAlignment:
    """`gain(s) life equal to` (Exsanguinate, Corrupt, Sifter Wurm — 68 pool cards) was in
    neither the role classifier nor the tag model. The tag half went in with the `pay
    life` work; this is the role half, so the two agree on the phrase."""

    def test_gain_life_equal_to_is_lifegain(self):
        assert "Lifegain" in deck.classify_roles(
            "Each opponent loses X life. You gain life equal to the life lost this way.")

    def test_fixed_number_lifegain_still_counts(self):
        assert "Lifegain" in deck.classify_roles("You gain 3 life.")
        assert "Lifegain" in deck.classify_roles("Flying, lifelink")

    def test_opponent_losing_life_is_not_lifegain(self):
        assert "Lifegain" not in deck.classify_roles("Each opponent loses 2 life.")


class TestRationaleFigureAudit:
    """The FIGURE half of `rationale_staleness` was silently disabled roster-wide by one
    over-broad history cue, and the arrow notation it accidentally covered then needed
    handling on its own."""

    def test_bare_over_is_not_a_history_cue(self):
        """"card advantage 9 OVER a 2.91 curve" is the house phrasing for a quality
        vector, so a bare "over" suppressed the very sentence that states the CURRENT
        figure. Deck 43 quoted interaction 10 against a live 8 and read clean."""
        assert not deck._HISTORY_CUES.search("card advantage 9 over a 2.91 curve")

    def test_real_history_words_still_suppress(self):
        for phrase in ("interaction was 4", "Bite Down replaced Shock",
                       "no longer in the deck", "held out of the 60",
                       "queued as a craft target"):
            assert deck._HISTORY_CUES.search(phrase), phrase

    def test_arrow_notation_marks_the_from_side_as_history(self):
        # "card advantage 0→1" states the OLD value first; only the second is current.
        for arrow in ("→", "->"):
            assert deck._ARROW_AFTER.match(f"{arrow}1")
            assert deck._ARROW_AFTER.match(f" {arrow} 1")

    def test_a_plain_figure_is_not_treated_as_an_arrow(self):
        assert not deck._ARROW_AFTER.match(" (seven of it instant-speed)")
        assert not deck._ARROW_AFTER.match(" plus card advantage 9")

    def _fig(self, prose, needle="interaction 9"):
        """_figure_is_history over the position of `needle` in `prose`."""
        i = prose.index(needle)
        return deck._figure_is_history(prose, i, i + len(needle))

    def test_domain_vocabulary_does_not_suppress_a_current_figure(self):
        """The second silent disabling, same shape as the bare `over`: the CARD scan's
        cue list was reused for figures, and `remov\\w*` (meant for "removed") matches
        "removal" — the commonest noun in a rationale that argues about interaction.
        Four decks quoted a stale interaction count and the audit reported clean."""
        assert not self._fig(
            "The floor reads A on interaction 9 (seven of it instant-speed) over a "
            "2.56 curve — five surplus removal spells were traded for card advantage")
        assert not self._fig(
            "The metrics floor reads A on interaction 9 across a 3.03 curve, and the "
            "deck is FULLY OWNED — zero craft targets, unusual for a from-scratch build")

    def test_a_figure_stated_as_past_is_still_suppressed(self):
        for prose in ("interaction was 9 before the removal package",
                      "card advantage is up from 9 at the last pass",
                      "the old rationale cited a 2.65 curve; the list is now 3.0"):
            i = next(k for k, ch in enumerate(prose) if ch.isdigit())
            assert deck._figure_is_history(prose, i, i + 1), prose

    def test_a_prescriptive_figure_is_not_a_claim(self):
        assert self._fig("PATH TO A: this wants interaction 9 to clear the floor")

    def _arriving(self, prose, needle):
        return deck._cites_as_arriving(prose, prose.index(needle))

    def test_the_arriving_side_of_a_replacement_is_a_live_claim(self):
        """The residual left over from the figure fix: the audit could see an absent
        card and a wrong number, but not a claim pointing the WRONG WAY. "Spell Pierce
        was CUT for Shriek" names Shriek as the card that came IN — so once the swap was
        reverted the sentence was false, yet "CUT" sat adjacent and silenced it."""
        for prose, needle in (
                ("Spell Pierce was CUT for Shriek, Treblemaker, which keeps", "Shriek"),
                ("Harsh Annotation became Starseer Mentor last pass", "Starseer"),
                ("Bite Down was replaced by Agatha's Soul Cauldron", "Agatha"),
                ("Kapow! was swapped for Felling Blow", "Felling")):
            assert self._arriving(prose, needle), prose

    def test_the_departing_side_stays_suppressed(self):
        # "+A (over B)" names both sides; B legitimately left.
        assert not self._arriving("+The Legend of Kyoshi (over Squirrel Girl)", "Squirrel")
        assert not self._arriving("took the slot instead of Dazzling Angel", "Dazzling")

    def test_a_list_plus_is_not_a_swap_marker(self):
        """`re.I` on the cue pattern defeated the capital-letter test that makes "+X"
        mean a card name, so the "+" in "hard counters + a mythic finisher" read as a
        swap and reported deck 12's queued craft target as stale."""
        assert not self._arriving(
            "QUALITY (hard counters + a mythic finisher) clears the bar. Disdainful "
            "Stroke is the queued net-add", "Disdainful")

    def test_cut_for_a_reason_is_not_cut_for_a_card(self):
        """"Two heist cards were CUT for cause: Doom Reigns Supreme wants five Villains"
        means cut for a REASON. The arriving card has to sit immediately after the cue."""
        assert not self._arriving(
            "Two more owned black heist cards were CUT for cause: Doom Reigns Supreme "
            "wants five Villains", "Doom Reigns")

    def test_house_curve_phrasing_is_read(self):
        """The avg_mv pattern only read "curve of 2.44" / "avg MV 2.44"; the rationales
        write "a tight 2.44 curve" — 14 uses against 1, so the check was decorative."""
        pats = [rx for rx, key in deck._RATIONALE_FIGURES if key == "avg_mv"]
        assert any(rx.search("a tight 2.44 curve") for rx in pats)
        assert any(rx.search("a curve of 2.44") for rx in pats)

    # --- the parenthesised / number-first / early-drop misses (roster sweep 0 -> 12) ---
    def _read(self, key, text):
        return [m.group(1)
                for rx, k in deck._RATIONALE_FIGURES if k == key
                for m in rx.finditer(text)]

    def test_parenthesised_figure_is_read(self):
        """`interaction (3)` put the digits behind a bracket, so the whitespace-then-digits
        pattern saw nothing. Eight such figures sat on the roster; deck 23 reported clean
        while quoting a 3.6 curve against a live 3.47."""
        assert self._read("interaction", "dense interaction (12)") == ["12"]
        assert self._read("interaction", "the interaction total (3)") == ["3"]
        assert self._read("card_advantage", "card advantage is thinner (3)") == ["3"]
        assert self._read("avg_mv", "a slow curve (2.81)") == ["2.81"]

    def test_breakdown_subcount_is_not_read_as_the_claim(self):
        """The house style is a number-first claim plus a BREAKDOWN — "7 interaction
        (5 spot removal + 2 sweepers)". A permissive `\\((\\d+)` read the 5 as the figure
        and reported four decks stale against numbers they never asserted, so the
        parenthesised form must require the bracket to close on the digits."""
        assert self._read("interaction", "7 interaction (5 spot removal + 2 sweepers)") == ["7"]
        assert self._read("interaction", "deep interaction (6 removal + 3 sweepers)") == []

    def test_number_first_figures_are_read(self):
        """The roster writes these number-first far more often than label-first — 13
        interaction figures, 3 card-advantage, 1 protection, none ever audited. Same
        miss already recorded for avg_mv, on the axes the tier floor is computed from."""
        assert self._read("interaction", "low curve + 7 interaction + reach") == ["7"]
        assert self._read("card_advantage", "engine + 3 card advantage on a base") == ["3"]
        assert self._read("protection", "and 2 protection pieces") == ["2"]

    def test_early_drops_is_audited(self):
        """early_drops was in the quality vector but had no pattern, so a count could go
        stale in silence — deck 23 claimed "6 one-two-drops" against a live 11."""
        assert self._read("early_drops", "a tight 2.53 curve (22 early drops)") == ["22"]
        assert self._read("early_drops", "3.47 curve and 11 one-two-drops") == ["11"]

    def test_quoted_figure_is_suppressed_as_history(self):
        """A figure inside quotation marks cites earlier prose rather than claiming it:
        deck 7 writes `The old one-line reason ("fast clock but thin interaction (3)") is
        no longer true`. _FIGURE_PAST cannot reach it — its cue must sit within 24 chars
        and "old" is 47 back — and widening that window would loosen every other
        suppression."""
        prose = ('The old one-line reason ("fast clock but thin interaction (3)") '
                 'is no longer true')
        i = prose.index("(3)")
        assert deck._figure_is_history(prose, i, i + 3)
        # …but an ordinary unquoted figure is still a live claim.
        plain = "grindy value, 7 interaction and reach"
        j = plain.index("7")
        assert not deck._figure_is_history(plain, j, j + 1)


class TestRotationOverride:
    """A reprint inherits the newest printing's date, so a card reprinted into a set with
    an announced LONG Standard legality read as rotating in three years."""

    def test_foundations_uses_its_announced_window(self):
        # Genesis Wave (FDN, 2024-11-15): 2029, not 2027.
        assert deck.rotation_year("2024-11-15", set_code="FDN") == 2029
        assert deck.rotation_risk("2024-11-15", set_code="FDN") is False

    def test_ordinary_set_still_uses_release_plus_three(self):
        assert deck.rotation_year("2024-02-09", set_code="MKM") == 2027
        assert deck.rotation_year("2023-09-08", set_code="WOE") == 2026

    def test_blank_release_is_graceful(self):
        assert deck.rotation_year("") is None
        assert deck.rotation_risk("") is False

    def test_risk_is_calendar_year_based(self):
        # Rotation happens at a fall rotation, not on a card's 3rd birthday: a 2023 set
        # rotates during 2026, so it is at risk for all of 2026.
        import datetime
        y = datetime.date.today().year
        assert deck.rotation_risk(f"{y - 3}-09-01") is True
        assert deck.rotation_risk(f"{y - 1}-09-01") is False


class TestCostAsUpside:
    def test_kicker_land_bounce_flags_in_a_landfall_deck(self):
        text = ("Kicker—Return a land you control to its owner's hand. Target creature "
                "you control deals damage equal to its power to target creature.")
        assert deck.cost_upside_flags(text, {"landfall", "counters"})

    def test_same_card_is_silent_without_the_theme(self):
        text = "Kicker—Return a land you control to its owner's hand."
        assert deck.cost_upside_flags(text, {"lifegain", "flying"}) == []

    def test_leaves_play_trigger_flags_in_a_counters_deck(self):
        text = ("This creature enters with X +1/+1 counters on it. When this creature "
                "leaves the battlefield, put its counters on target creature you control.")
        assert deck.cost_upside_flags(text, {"counters"})

    def test_plain_card_never_flags(self):
        assert deck.cost_upside_flags("Flying. Vigilance.", {"counters", "landfall"}) == []


class TestCostThemes:
    """`graveyard` is a benefit only where the deck pays it off; elsewhere it's a cost."""
    CD = {
        "escape artist": {"type": "Creature", "colors": "U",
                          "text": "Escape—{2}{U}, Exile four other cards from your graveyard."},
        "vanilla": {"type": "Creature", "colors": "G", "text": "Flying."},
    }

    def test_theme_dropped_without_payoffs(self):
        cards = [(1, "Vanilla", "", "")]
        assert deck._drop_cost_themes(["graveyard", "counters"], cards, self.CD) == ["counters"]

    def test_theme_kept_with_enough_payoffs(self):
        cards = [(2, "Escape Artist", "", "")]
        assert "graveyard" in deck._drop_cost_themes(["graveyard"], cards, self.CD)

    def test_non_cost_themes_pass_through(self):
        cards = [(1, "Vanilla", "", "")]
        assert deck._drop_cost_themes(["counters", "landfall"], cards, self.CD) == \
            ["counters", "landfall"]


class TestSectionMismatch:
    CD = {
        "broodguard elite": {"type": "Creature", "colors": "G",
                             "text": "This creature enters with X +1/+1 counters on it."},
        "divination": {"type": "Sorcery", "colors": "U", "text": "Draw two cards."},
        "shock": {"type": "Instant", "colors": "R", "text": "Shock deals 2 damage to any target."},
    }

    def test_wrong_section_warns(self):
        lines = ["Deck", "# Card advantage", "1 Shock (M21) 159"]
        assert "Card advantage" in (deck.section_mismatch(lines, 2, "Shock", self.CD) or "")

    def test_matching_section_is_silent(self):
        lines = ["Deck", "# Card advantage", "1 Divination (M21) 56"]
        assert deck.section_mismatch(lines, 2, "Divination", self.CD) is None

    def test_ambiguous_section_is_silent(self):
        # "Counter DOUBLERS" means +1/+1 counters, not counterspells.
        lines = ["Deck", "# Counter DOUBLERS — the engine", "1 Broodguard Elite (EOE) 175"]
        assert deck.section_mismatch(lines, 2, "Broodguard Elite", self.CD) is None

    def test_no_header_is_silent(self):
        assert deck.section_mismatch(["Deck", "1 Shock (M21) 159"], 1, "Shock", self.CD) is None

    def test_unclassified_card_gets_the_softer_wording(self):
        lines = ["Deck", "# Card advantage", "1 Broodguard Elite (EOE) 175"]
        msg = deck.section_mismatch(lines, 2, "Broodguard Elite", self.CD) or ""
        assert "verify" in msg  # a prompt, not an assertion that it's misfiled


class TestProtectionAxis:
    def test_real_protection_detected(self):
        for text in ("Enchanted creature has ward {2}.",
                     "Target creature you control gains hexproof until end of turn.",
                     "It gains indestructible until end of turn.",
                     "Creatures you control have protection from red."):
            assert deck.protection_effects(text), text

    def test_combat_pump_is_not_protection(self):
        # The broad "Protection / trick" role counts these; this axis must not.
        for text in ("Target creature gets +2/+2 until end of turn.",
                     "Double target creature's power and toughness until end of turn.",
                     "Target creature you control gets +0/+10 until end of turn."):
            assert not deck.protection_effects(text), text

    def test_cant_be_regenerated_boilerplate_is_not_protection(self):
        # "It can't be regenerated" rides along on removal spells, so keying on the word
        # would score half the format's removal as protection.
        assert not deck.protection_effects(
            "Destroy target creature. It can't be regenerated.")

    def test_role_tally_reports_protection_quantity_weighted(self):
        cd = {"snakeskin veil": {"type": "Instant", "colors": "G",
                                 "text": "Put a +1/+1 counter on target creature you "
                                         "control. It gains hexproof until end of turn."},
              "shock": {"type": "Instant", "text": "Shock deals 2 damage to any target.",
                        "colors": "R"}}
        t = deck.role_tally([(2, "Snakeskin Veil", "", ""), (1, "Shock", "", "")], cd)
        assert t["protection"] == 2
        assert t["interaction"] == 1


class TestRoleTally:
    CD = {
        "go for the throat": {"type": "Instant", "text": "Destroy target creature.", "colors": "B"},
        "divination": {"type": "Sorcery", "text": "Draw two cards.", "colors": "U"},
        "forest": {"type": "Basic Land — Forest", "text": "", "colors": ""},
    }

    def test_quantity_weighted_and_land_skipped(self):
        cards = [(2, "Go for the Throat", "", ""), (1, "Divination", "", ""), (4, "Forest", "", "")]
        t = deck.role_tally(cards, self.CD)
        assert t["interaction"] == 2      # 2 copies of removal
        assert t["card_advantage"] == 1   # Divination
        # a basic land contributes to neither

    def test_split_across_lines_sums(self):
        cards = [(2, "Go for the Throat", "S1", ""), (1, "Go for the Throat", "S2", "")]
        assert deck.role_tally(cards, self.CD)["interaction"] == 3

    def test_interaction_count_matches_role_tally(self):
        cards = [(2, "Go for the Throat", "", "")]
        assert deck._interaction_count(cards, self.CD) == deck.role_tally(cards, self.CD)["interaction"]


class TestRarityLoader:
    """Every reference-table loader answers for a DFC's FRONT face — except this one,
    which reads the POOL (keyed only by the full `Front // Back` name) and had no alias.
    47 roster names resolved to "", `_power_seed` fell to its default floor, and every
    mythic/rare DFC was seeded as low-rarity and sorted UP the cut list; Ojer Axonil's
    `_cuts_power_adj` came out -0.70 against a real +0.17, so the nudge changed SIGN
    (broad-scan F-14)."""

    def _pool(self, tmp_path, rows):
        p = tmp_path / "pool.csv"
        p.write_text("Card Name,Rarity\n" + "".join(f"{n},{r}\n" for n, r in rows))
        return str(p)

    def test_a_dfc_resolves_by_its_front_face(self, tmp_path, monkeypatch):
        monkeypatch.setattr(deck, "POOL_CSV",
                            self._pool(tmp_path, [("Ojer Axonil // Temple of Power", "mythic")]))
        rar = deck.load_rarities()
        assert rar["ojer axonil // temple of power"] == "M"
        assert rar["ojer axonil"] == "M"          # the deck-file spelling

    def test_a_real_card_is_never_shadowed_by_a_front_face_alias(self, tmp_path, monkeypatch):
        """`Life` is a card as well as the front of `Life // Death`. Aliasing inside the
        row loop would let whichever came first win; the alias pass runs after every real
        row is in, so the result is order-independent."""
        for order in ([("Life // Death", "uncommon"), ("Life", "rare")],
                      [("Life", "rare"), ("Life // Death", "uncommon")]):
            monkeypatch.setattr(deck, "POOL_CSV", self._pool(tmp_path, order))
            deck.load_rarities.cache_clear()
            assert deck.load_rarities()["life"] == "R", order

    def test_every_roster_deck_card_now_prices(self, tmp_path):
        """The measured symptom: 47 distinct deck-file names had no rarity at all."""
        rar = deck.load_rarities()
        missing = {n for d in deck.roster_decks()
                   for _q, n, _s, _c in deck.parse_deck_file(d["path"])[1]
                   if n.lower() not in deck.BASICS and n.lower() not in rar}
        assert missing == set(), sorted(missing)[:8]


class TestMultisetAndDelta:
    def test_multiset_case_insensitive_sums(self):
        ms = deck._multiset([(2, "Shock", "", ""), (1, "shock", "", "")])
        assert ms == {"shock": ("Shock", 3)}  # first spelling kept

    def test_multiset_normalizes_a_dfc_to_its_front_face(self):
        """The two legitimate spellings of a two-faced card are ONE card. Keying on the
        raw name made `verify` report a phantom +1/-1 on an identical deck and would have
        had `sync --apply` rewrite the stored full name to the bare front — the
        un-importable line P8 fixed `_printing_of` to stop writing (broad-scan F-02)."""
        ms = deck._multiset([(1, "Ojer Axonil, Deepest Might // Temple of Power", "", ""),
                             (1, "Ojer Axonil, Deepest Might", "", "")])
        assert list(ms) == ["ojer axonil, deepest might"]
        assert ms["ojer axonil, deepest might"][1] == 2

    def test_multiset_keeps_the_IMPORTABLE_spelling(self):
        """First-seen wins (audit F4) EXCEPT that the full `Front // Back` form beats a
        bare front face, in either order — that name is what a deck file must carry."""
        front_first = deck._multiset([(1, "Ojer Axonil, Deepest Might", "", ""),
                                      (1, "Ojer Axonil, Deepest Might // Temple of Power", "", "")])
        full_first = deck._multiset([(1, "Ojer Axonil, Deepest Might // Temple of Power", "", ""),
                                     (1, "Ojer Axonil, Deepest Might", "", "")])
        for ms in (front_first, full_first):
            assert ms["ojer axonil, deepest might"][0] == \
                "Ojer Axonil, Deepest Might // Temple of Power"

    def test_two_spellings_of_one_card_are_not_drift(self):
        stored = deck._multiset([(1, "Ojer Axonil, Deepest Might // Temple of Power", "", "")])
        pasted = deck._multiset([(1, "Ojer Axonil, Deepest Might", "", "")])
        added, removed, diffs = deck._ms_diff(pasted, stored)
        assert (added, removed, diffs) == (0, 0, [])

    def test_reconcile_keeps_a_dfc_line_when_the_paste_names_the_front(self):
        """The write half: the stored line must survive with its printing and its place
        in the file, not be dropped and re-appended under the front-face spelling."""
        lines = ["# Creatures",
                 "1 Ojer Axonil, Deepest Might // Temple of Power (LCI) 158",
                 "2 Shock (M21) 159"]
        target = deck._multiset([(1, "Ojer Axonil, Deepest Might", "", ""),
                                 (2, "Shock", "", "")])
        assert deck.reconcile_lines(lines, target, {}) == lines

    def test_ms_delta(self):
        prev = deck._multiset([(2, "A", "", ""), (1, "B", "", "")])
        cur = deck._multiset([(1, "A", "", ""), (1, "C", "", "")])
        added, removed = deck._ms_delta(prev, cur)
        assert added == [("C", 1)]
        assert removed == [("A", 1), ("B", 1)]

    def test_ms_delta_no_change(self):
        ms = deck._multiset([(1, "A", "", "")])
        assert deck._ms_delta(ms, ms) == ([], [])


class TestRotation:
    def test_rotation_year(self):
        assert deck.rotation_year("2023-11-17", 3) == 2026
        assert deck.rotation_year("2024-01-01", 2) == 2026

    def test_rotation_year_blank_or_bad(self):
        assert deck.rotation_year("", 3) is None
        assert deck.rotation_year("not-a-date", 3) is None
        assert deck.rotation_year(None, 3) is None

    def test_rotation_risk_relative_to_today(self):
        old = (date.today() - timedelta(days=365 * 4)).isoformat()
        new = (date.today() - timedelta(days=365)).isoformat()
        assert deck.rotation_risk(old, 3) is True
        assert deck.rotation_risk(new, 3) is False

    def test_rotation_risk_blank_is_false(self):
        assert deck.rotation_risk("", 3) is False
        assert deck.rotation_risk(None, 3) is False


def _vec(plan, inter, ca, uncast=0, avg_mv=3.0, early=0, reach=0):
    return {"plan": plan, "interaction": inter, "card_advantage": ca,
            "uncastable": uncast, "avg_mv": avg_mv, "early_drops": early, "reach": reach}


class TestTierBand:
    def test_a_floor(self):
        assert deck.tier_band(_vec("midrange", 5, 3)) == "A"

    def test_b_floor(self):
        assert deck.tier_band(_vec("midrange", 3, 1)) == "B"

    def test_d_floor(self):
        assert deck.tier_band(_vec("midrange", 0, 0)) == "D"

    def test_uncastable_caps_at_c(self):
        assert deck.tier_band(_vec("midrange", 5, 3, uncast=1)) == "C"

    def test_aggro_clock_only_raises(self):
        fast = deck.tier_band(_vec("aggro", 2, 0, avg_mv=2.0, early=16, reach=10))
        mid = deck.tier_band(_vec("midrange", 2, 0, avg_mv=2.0, early=16, reach=10))
        assert deck.TIER_RANK[fast] >= deck.TIER_RANK[mid]

    def test_clock_score_bounded(self):
        for v in (_vec("aggro", 0, 0, avg_mv=2.0, early=20, reach=20),
                  _vec("aggro", 0, 0, avg_mv=9.0, early=0, reach=0)):
            assert 0 <= deck._clock_score(v) <= 7

    def test_deck_plan_honours_header(self):
        assert deck.deck_plan({"plan": "aggro"}) == "aggro"
        assert deck.deck_plan({"plan": "control"}) == "control"
        assert deck.deck_plan({"archetype": "Golgari midrange value"}) == "midrange"


class TestScoringTermsBounded:
    def test_role_credit_flat_and_zero(self):
        R = next(iter(deck.IMPACT_ROLES))
        assert deck._role_credit({R}) == 9   # base 3 + impact 6
        assert deck._role_credit(set()) == 0

    def test_role_credit_diminishing(self):
        R = next(iter(deck.IMPACT_ROLES))
        seq = [deck._role_credit({R}, {R: k}) for k in (0, 1, 2, 4, 8)]
        assert all(a > b for a, b in zip(seq, seq[1:]))
        assert min(seq) >= 3

    def test_curve_gap_factor_bounded(self):
        curves = [{}, {1: 4, 2: 4, 3: 2}, {2: 12}]
        for cv in curves:
            for mv in (None, 0, 1, 3, 6, 12):
                assert 0.85 <= deck._curve_gap_factor(mv, cv) <= 1.15


class TestConsistencyMath:
    """The hypergeometric manabase/opening-hand model behind `deck.py consistency`."""

    def test_hypergeom_bounds(self):
        # k=0 is certain; wanting more successes than exist is impossible.
        assert deck.hypergeom_at_least(60, 24, 7, 0) == 1.0
        assert deck.hypergeom_at_least(60, 3, 7, 4) == 0.0   # only 3 successes, want 4
        assert deck.hypergeom_at_least(60, 24, 0, 1) == 0.0  # draw nothing, want 1

    def test_hypergeom_monotonic_in_sources(self):
        # More sources in the deck -> higher P of hitting the pip requirement.
        seq = [deck.hypergeom_at_least(60, k, 9, 2) for k in (4, 8, 12, 16, 20)]
        assert all(a < b for a, b in zip(seq, seq[1:]))

    def test_hypergeom_matches_known_value(self):
        # P(>=1 of 24 lands in the opening 7 of 60) = 1 - C(36,7)/C(60,7) ≈ 0.978.
        import math
        p = deck.hypergeom_at_least(60, 24, 7, 1)
        assert abs(p - (1 - math.comb(36, 7) / math.comb(60, 7))) < 1e-9
        assert 0.97 < p < 0.99

    def test_cards_seen_play_vs_draw(self):
        assert deck.cards_seen(1, on_play=True) == 7     # opening, no turn-1 draw
        assert deck.cards_seen(1, on_play=False) == 8    # on the draw, +1
        assert deck.cards_seen(3, on_play=True) == 9

    def test_cast_probability_multicolor_is_product(self):
        srcs = {"B": 16, "R": 1, "W": 0, "U": 0, "G": 0}
        # A {B}{R} card on turn 2 with a single red source should be dismal.
        p = deck.cast_probability(60, srcs, 2, {"B": 1, "R": 1})
        assert 0.0 < p < 0.3
        # An empty pip demand is always castable.
        assert deck.cast_probability(60, srcs, 2, {}) == 1.0

    def test_min_sources_for_increases_with_pip_count(self):
        one = deck.min_sources_for(60, 3, 1, target=0.90)
        two = deck.min_sources_for(60, 3, 2, target=0.90)
        assert two > one > 0

    def test_opening_land_stats_partition(self):
        st = deck.opening_land_stats(60, 24)
        # keepable + screw + flood covers 0..7 lands exactly (a partition).
        assert abs(st["keepable"] + st["screw"] + st["flood"] - 1.0) < 1e-9
        assert 0.0 <= st["hit2"] <= 1.0 and st["hit3"] < st["hit2"]

    def test_more_lands_fewer_screw(self):
        assert deck.opening_land_stats(60, 26)["screw"] < deck.opening_land_stats(60, 20)["screw"]


class TestCutsPowerAdj:
    """The bounded card-quality co-signal folded into the cut ranking (#3)."""

    def test_bounded_both_directions(self):
        for p in (0, 2.5, 5, 7.5, 10):
            assert -deck._CUTS_POWER_CAP <= deck._cuts_power_adj(p) <= deck._CUTS_POWER_CAP
        # The clamp is a safety rail for out-of-range power (seed is always 0–10).
        assert deck._cuts_power_adj(100) == deck._CUTS_POWER_CAP
        assert deck._cuts_power_adj(-100) == -deck._CUTS_POWER_CAP

    def test_neutral_at_center(self):
        assert deck._cuts_power_adj(deck._CUTS_POWER_NEUTRAL) == 0.0

    def test_monotonic_bomb_beats_weak(self):
        assert deck._cuts_power_adj(9) > deck._cuts_power_adj(3)


class TestCutsUniqAdj:
    """The bounded ability-distinctiveness co-signal folded into the cut ranking."""

    def test_bounded_both_directions(self):
        for u in (0, 1.5, 4, 6, 8, 10):
            assert -deck._CUTS_UNIQ_CAP <= deck._cuts_uniq_adj(u) <= deck._CUTS_UNIQ_CAP
        assert deck._cuts_uniq_adj(100) == deck._CUTS_UNIQ_CAP
        assert deck._cuts_uniq_adj(-100) == -deck._CUTS_UNIQ_CAP

    def test_neutral_at_center(self):
        assert deck._cuts_uniq_adj(deck._CUTS_UNIQ_NEUTRAL) == 0.0

    def test_monotonic_distinctive_beats_generic(self):
        # A distinctive-mechanic card is protected; a generic-ability filler sorts up.
        assert deck._cuts_uniq_adj(9) > deck._cuts_uniq_adj(1)

    def test_cap_stays_a_tiebreaker(self):
        # Smaller than the theme-fit scale — it can't override a real fit gap.
        assert deck._CUTS_UNIQ_CAP <= 3.0


class TestLandSuggestBonuses:
    """The bounded synergy + shortfall co-signals of the manabase recommender."""
    THEMES = {"equipment": 17, "counters": 3, "pump": 15}
    DEFICIT = {"W": 0.30, "R": 0.05}

    def test_synergy_zero_without_overlap(self):
        assert deck._land_synergy_bonus([], self.THEMES) == 0.0
        assert deck._land_synergy_bonus(["landfall"], self.THEMES) == 0.0
        assert deck._land_synergy_bonus(["counters"], {}) == 0.0

    def test_synergy_bounded_and_scaled(self):
        for tags in ([], ["counters"], ["equipment"], ["equipment", "pump"]):
            assert 0.0 <= deck._land_synergy_bonus(tags, self.THEMES) <= deck._LAND_SYN_CAP
        # a land on the deck's TOP theme beats one on a minor theme
        assert (deck._land_synergy_bonus(["equipment"], self.THEMES)
                > deck._land_synergy_bonus(["counters"], self.THEMES))

    def test_shortfall_bounded(self):
        for cols in ([], ["W"], ["R"], ["W", "R"]):
            assert 0.0 <= deck._land_shortfall_bonus(cols, self.DEFICIT) <= deck._LAND_SHORT_CAP

    def test_shortfall_favors_scarce_color(self):
        assert (deck._land_shortfall_bonus(["W"], self.DEFICIT)
                > deck._land_shortfall_bonus(["R"], self.DEFICIT))
        # a land covering the scarce color scores == the scarce single, via max()
        assert (deck._land_shortfall_bonus(["W", "R"], self.DEFICIT)
                == deck._land_shortfall_bonus(["W"], self.DEFICIT))

    def test_shortfall_zero_when_nothing_scarce(self):
        assert deck._land_shortfall_bonus(["W"], {}) == 0.0
        assert deck._land_shortfall_bonus(["W"], {"W": 0.0, "R": 0.0}) == 0.0

    def test_caps_keep_fixing_dominant(self):
        # Both nudges must be small next to the 0–10 fixing axis.
        assert deck._LAND_SYN_CAP <= 3.0 and deck._LAND_SHORT_CAP <= 3.0


class TestNeedsModelSignals:
    """The bounded co-signals of the --ramp / --interaction needs-aware recommenders."""

    def test_accel_want_lean_curve_is_zero(self):
        assert deck._accel_want(2.0, 0.0) == 0.0
        assert deck._accel_want(2.2, 0.1) == 0.0

    def test_accel_want_bounded_and_rising(self):
        for mv, h in ((2.0, 0.0), (3.0, 0.3), (3.8, 0.5), (6.0, 0.9)):
            assert 0.0 <= deck._accel_want(mv, h) <= 1.0
        assert deck._accel_want(4.0, 0.6) > deck._accel_want(3.0, 0.3)

    def test_restriction_fit_unrestricted_is_zero(self):
        assert deck._ramp_restriction_fit("{T}: Add {G}.", {"equipment": 0.4}) == 0.0

    def test_restriction_fit_match_vs_mismatch(self):
        hi = deck._ramp_restriction_fit(
            "Spend this mana only to cast an Equipment spell.", {"equipment": 0.5})
        lo = deck._ramp_restriction_fit(
            "Spend this mana only to cast an Equipment spell.", {"equipment": 0.0})
        assert 0 < hi <= deck._RAMP_RESTRICT_CAP
        assert -deck._RAMP_RESTRICT_CAP <= lo < 0

    def test_scaling_axis_detection(self):
        assert deck._int_scaling("Target creature you control fights target creature.") == "fight"
        assert deck._int_scaling(
            "deals damage equal to the number of creatures you control") == "creatures"
        assert deck._int_scaling("Deal {X} damage") == "x-cost"
        assert deck._int_scaling("Destroy target creature.") is None

    def test_scaling_boost_bounded_and_rising(self):
        assert deck._int_scaling_boost(None, 1.0) == 0.0
        for m in (0.0, 0.3, 0.7, 1.0):
            assert 0.0 <= deck._int_scaling_boost("fight", m) <= deck._INT_SCALE_CAP
        assert deck._int_scaling_boost("fight", 0.9) > deck._int_scaling_boost("fight", 0.1)

    def test_caps_stay_tiebreakers(self):
        assert deck._RAMP_ACCEL_CAP <= 3.0
        assert deck._RAMP_RESTRICT_CAP <= 3.0
        assert deck._INT_SCALE_CAP <= 3.0


class TestProducesMana:
    """The broad mana-source detector behind the tier tune plan's ramp-loss flag —
    catches dorks the 'Ramp / fixing' role misses (the 'add one mana' phrasing)."""

    def test_symbol_tap_dork(self):
        assert deck._produces_mana("{T}: Add {G}.")
        assert deck._produces_mana("{T}: Add {C}{C}.")

    def test_add_one_mana_phrasing(self):
        # Bloom Tender's Vivid ability — no "{T}: add {SYM}" template.
        assert deck._produces_mana(
            "Vivid — {T}: For each color among permanents you control, add one mana of that color.")
        assert deck._produces_mana("{T}: Add one mana of any color.")

    def test_not_a_mana_source(self):
        assert not deck._produces_mana("Converge — deals X damage, where X is the number of "
                                       "colors of mana spent to cast this spell.")
        assert not deck._produces_mana("Put a +1/+1 counter on target creature.")
        assert not deck._produces_mana("")


class TestFitStrength:
    """card→deck fit labels — the fix that stops a generically-good card reading KEY
    in every low-interaction deck it merely shares a generic tag with."""

    def test_generic_only_plus_role_gap_is_tangential(self):
        # A removal card sharing ONLY generic themes with a low-interaction deck must
        # NOT read KEY just because the deck is short on interaction (the Get Lost bug).
        s = deck.fit_strength(["etb", "tokens"], {"etb": 5, "tokens": 5, "Cat": 10},
                              "Destroy target creature.", deck_int=2, deck_ca=0)
        assert s == "tangential"

    def test_specific_theme_plus_role_gap_is_key(self):
        s = deck.fit_strength(["Wizard"], {"Wizard": 10},
                              "Destroy target creature.", deck_int=2, deck_ca=0)
        assert s == "KEY"

    def test_signature_match_is_key(self):
        s = deck.fit_strength(["counters"], {"counters": 10}, "", 8, 8,
                              signature={"counters"})
        assert s == "KEY"

    def test_specific_top_theme_is_key(self):
        assert deck.fit_strength(["Cat"], {"Cat": 10}, "", 8, 8) == "KEY"

    def test_specific_secondary_theme_is_role_player(self):
        assert deck.fit_strength(["Cat"], {"Cat": 2, "tokens": 10}, "", 8, 8) == "role-player"

    def test_generic_only_no_gap_is_tangential(self):
        assert deck.fit_strength(["tokens"], {"tokens": 10}, "", 8, 8) == "tangential"

    # --- broad background tribes never mint a KEY by themselves (tagging-misreads #4) ---
    def test_broad_tribe_top_theme_is_not_key(self):
        # Hawkeye sharing only Human/Hero with a mono-Human deck must NOT read KEY even
        # though Human is the deck's most-common theme (the KEY-in-every-Hero-deck fix).
        assert deck.fit_strength(["Human", "Hero"], {"Human": 19, "Hero": 15},
                                 "", 8, 8) == "tangential"

    def test_broad_tribe_not_key_via_signature(self):
        # A broad tribe can't mint KEY even when a protected card carries it.
        assert deck.fit_strength(["Human"], {"Human": 19}, "", 8, 8,
                                 signature={"Human"}) == "tangential"

    def test_broad_tribe_plus_role_gap_is_not_key(self):
        # A removal card sharing only a broad tribe stays out of KEY on a low-int deck.
        assert deck.fit_strength(["Human"], {"Human": 19}, "Destroy target creature.",
                                 deck_int=2, deck_ca=0) == "tangential"

    def test_narrow_tribe_still_key(self):
        # Narrow, build-around tribes remain real signals.
        assert deck.fit_strength(["Ninja"], {"Ninja": 10}, "", 8, 8) == "KEY"

    def test_specific_theme_survives_alongside_broad_tribe(self):
        # A card sharing a broad tribe AND a specific theme is graded on the specific one.
        assert deck.fit_strength(["Human", "Dinosaur"], {"Human": 5, "Dinosaur": 10},
                                 "", 8, 8) == "KEY"


class TestDeckSimilarity:
    """deck.py similar — cosine over central-theme weights with generic themes damped so
    IDENTITY overlap (a shared specific theme) drives the score, not shared value generics."""

    def test_identical_vectors_are_one(self):
        v = {"Dinosaur": 10, "ramp": 4}
        assert abs(deck._theme_cosine(v, dict(v)) - 1.0) < 1e-9

    def test_disjoint_is_zero(self):
        assert deck._theme_cosine({"Ninja": 5}, {"Dinosaur": 5}) == 0.0

    def test_specific_overlap_beats_generic_overlap(self):
        # Two decks sharing a SPECIFIC theme are more similar than two sharing only a
        # generic one at the same raw weight.
        specific = deck._theme_cosine({"Dinosaur": 8, "x": 1}, {"Dinosaur": 8, "y": 1})
        generic = deck._theme_cosine({"etb": 8, "x": 1}, {"etb": 8, "y": 1})
        assert specific > generic

    def test_generic_is_damped_not_removed(self):
        # A generic-only shared theme still yields SOME similarity (decks that both draw
        # cards are loosely alike), just less than the raw weight would imply.
        s = deck._theme_cosine({"card draw": 5}, {"card draw": 5})
        assert 0 < s <= 1.0

    def test_theme_is_generic(self):
        assert deck._theme_is_generic("etb") and deck._theme_is_generic("card draw")
        assert deck._theme_is_generic("Human")          # broad tribe
        assert not deck._theme_is_generic("Dinosaur") and not deck._theme_is_generic("Ninja")

    def test_specific_only_drops_generic_overlap(self):
        # A generic-only overlap scores 0 under the pure-identity lens.
        assert deck._theme_cosine({"etb": 5, "Ninja": 1}, {"etb": 5, "Cat": 1},
                                  specific_only=True) == 0.0

    def test_specific_only_keeps_specific_overlap(self):
        # Sharing a SPECIFIC theme still scores 1.0 under the identity lens (generics ignored,
        # so only the shared Ninja axis remains for both vectors).
        s = deck._theme_cosine({"Ninja": 5, "etb": 9}, {"Ninja": 5, "etb": 2}, specific_only=True)
        assert abs(s - 1.0) < 1e-9

    def test_sim_specific_signature_rescues_generic(self):
        assert not deck._sim_specific("counters", frozenset())          # generic by default
        assert deck._sim_specific("counters", frozenset({"counters"}))  # rescued as a spine
        assert deck._sim_specific("Ninja", frozenset())                 # specific always

    def test_keep_rescues_generic_in_cosine(self):
        # Rescuing a shared generic SPINE (a counters-doubler deck) makes the pair read as
        # MORE similar than treating counters as damped value overlap.
        a, b = {"counters": 10, "Ninja": 1}, {"counters": 10, "Cat": 1}
        assert deck._theme_cosine(a, b, keep=frozenset({"counters"})) > deck._theme_cosine(a, b)

    def test_strong_signature_needs_multiple_protected_cards(self):
        # A theme is a real spine only if >=2 protected cards carry it — a lone protected
        # bomb's incidental tag (card draw) must NOT be rescued.
        meta = {"protect": "A; B; C"}
        cards = [(1, "A", "", ""), (1, "B", "", ""), (1, "C", "", "")]
        cardmeta = {"a": {"synergies": ["counters", "flying"]},
                    "b": {"synergies": ["counters", "haste"]},
                    "c": {"synergies": ["card draw"]}}
        sig = deck._strong_signature_themes(meta, cards, cardmeta)
        assert "counters" in sig and "card draw" not in sig and "flying" not in sig


class TestHomeCurveFit:
    """suggest-homes curve co-signal (#5): a bounded, never-boosting SORT nudge that
    penalizes a top-heavy / win-more card in a low-curve deck."""

    def test_unknown_mv_is_neutral(self):
        assert deck._home_curve_fit(None, 3.0) == 1.0
        assert deck._home_curve_fit(5.0, 0.0) == 1.0

    def test_within_two_mv_no_penalty(self):
        assert deck._home_curve_fit(4.0, 2.5) == 1.0
        assert deck._home_curve_fit(2.0, 2.4) == 1.0

    def test_top_heavy_penalized_but_bounded(self):
        m = deck._home_curve_fit(6.0, 2.4)          # excess 3.6
        assert 1.0 - deck._HOME_CURVE_CAP <= m < 1.0

    def test_never_boosts(self):
        # A cheap card in a heavy deck must NOT be boosted (curve nudge is one-sided).
        assert deck._home_curve_fit(2.0, 5.0) == 1.0

    def test_penalty_capped(self):
        assert deck._home_curve_fit(15.0, 2.0) == 1.0 - deck._HOME_CURVE_CAP


class TestColorFixerOverlay:
    """The rainbow-fixer overlay behind suggest-homes, and the cut-side guard that
    pairs with it. Both halves shipped a real bad recommendation: `suggest-homes
    "Guy in the Chair"` rated a {2}{G} one-mana-any-colour dork KEY for decks 13/17
    and proposed cutting Prismatic Undercurrents / Bloom Tender — each strictly
    better at the exact job motivating the add."""

    # --- detection is TEXT-based, not tag-based -------------------------------------
    def test_unindexed_mechanic_still_reads_as_a_fixer(self):
        # Bloom Tender and Prismatic Undercurrents key off Vivid, which sits in
        # keyword_baseline.txt and maps to NO theme — so the old `ctags & {ramp,mana}`
        # gate read both as non-fixers. The predicate must not depend on which
        # keywords tag_synergies happens to index this cycle.
        assert deck._is_color_fixer(set(), "Vivid — {T}: For each color among "
                                           "permanents you control, add one mana of "
                                           "that color.")
        assert deck._is_color_fixer({"etb", "vivid"},
                                    "Vivid — When this enchantment enters, search your "
                                    "library for up to X basic land cards, where X is "
                                    "the number of colors among permanents you control.")

    def test_mana_context_required(self):
        # The strictness the tag gate used to supply now lives in requiring MANA or
        # land-type context — "any color" alone is not fixing.
        assert not deck._is_color_fixer({"ramp"}, "Add {G}{G}.")
        assert not deck._is_color_fixer(
            set(), "Target creature gains protection from the color of your choice.")
        assert not deck._is_color_fixer(
            set(), "Draw a card for each color among permanents you control.")

    def test_mass_grant_and_spend_permission_are_broad(self):
        # Enduring Vitality grants the ability to every creature; Vizier grants
        # colour-agnostic SPENDING. Both are manabase fixes, not single sources.
        assert deck._fixer_rate('Creatures you control have "{T}: Add one mana of any '
                                'color."', 3) == 1.0
        assert deck._fixer_rate("You can spend mana of any type to cast creature "
                                "spells.", 4) == 1.0

    def test_any_one_color_counts(self):
        # `any one color` (Gilded Lotus) and Chrome Mox's `any of the exiled card's
        # colors` are the same class as `any color`. The first sweep omitted both and
        # silently dropped 38 real fixers — caught only by a roster-wide diff.
        assert deck._is_color_fixer(set(), "{T}: Add three mana of any one color.")
        assert deck._is_color_fixer(
            set(), "{T}: Add one mana of any of the exiled card's colors.")

    def test_treasure_reminder_text_does_not_count(self):
        # A Treasure's reminder literally reads "Add one mana of any color". Counting
        # it makes ~150 pool cards read as manabase fixers, and a signal that fires on
        # everything carries none. The same ability as REAL text must still qualify.
        assert not deck._is_color_fixer(
            set(), 'When this creature enters, create a Treasure token. (It\'s an '
                   'artifact with "{T}, Sacrifice this token: Add one mana of any '
                   'color.")')
        assert deck._is_color_fixer(
            set(), "{1}, {T}, Sacrifice this artifact: Add one mana of any color. "
                   "Draw a card.")

    # --- rate: how much fixing the card actually buys --------------------------------
    def test_broad_rate_does_not_decay_with_cost(self):
        for mv in (1, 4, 9):
            assert deck._fixer_rate("create a land token that is every basic land "
                                    "type", mv) == 1.0

    def test_single_source_discounted_by_cost_bounded_and_monotonic(self):
        sing = "{T}: Add one mana of any color."
        rates = [deck._fixer_rate(sing, m) for m in (1, 2, 3, 5, 9)]
        assert all(a >= b for a, b in zip(rates, rates[1:]))
        assert all(deck._FIXER_RATE_FLOOR <= r <= 1.0 for r in rates)
        # Cheap fixing is full value; the 3-mana dork falls below the KEY bar.
        assert rates[0] == rates[1] == 1.0
        assert deck._fixer_rate(sing, 3) < deck._FIXER_KEY_RATE

    def test_unknown_mv_is_not_penalized(self):
        # Guessing against missing data must not manufacture a demotion.
        assert deck._fixer_rate("{T}: Add one mana of any color.", None) == 1.0

    def test_non_fixer_rates_zero(self):
        assert deck._fixer_rate("Draw two cards.", 2) == 0.0

    def test_boost_scales_with_rate_and_stays_bounded(self):
        full = deck._fixer_boost(4, rate=1.0)
        half = deck._fixer_boost(4, rate=0.5)
        assert 0 < half < full
        assert deck._fixer_boost(2, rate=1.0) == 0      # mono/two-colour: no bump
        assert deck._fixer_boost(20, rate=1.0) == deck._fixer_boost(5, rate=1.0)

    # --- the cut side must not be blind to the add -----------------------------------
    def _fixture(self):
        cards = [(1, "Rainbow Rock", "S", "1"), (1, "Filler Bear", "S", "2"),
                 (4, "Mountain", "S", "3")]
        cardmeta = {"rainbow rock": {"synergies": []},
                    "filler bear": {"synergies": ["Bear"]}}
        carddata = {
            "rainbow rock": {"type": "Artifact",
                             "text": "{T}: Add one mana of any color."},
            "filler bear": {"type": "Creature — Bear", "text": "Vanilla."},
            "mountain": {"type": "Basic Land — Mountain", "text": ""},
        }
        return {}, cards, cardmeta, carddata

    def test_fixer_no_longer_tops_the_cut_list_on_role_credit_alone(self):
        # BASELINE CHANGED 2026-08, and the change is an improvement rather than a
        # regression. This used to assert "Rainbow Rock", on the premise that a fixer
        # "carries no synergy tags AND NO CLASSIFIED ROLE, so theme-fit + role-credit
        # ranks it most-cuttable". The second half of that premise is no longer true:
        # `_ROLE_PATTERNS` required a literal `{` after "add", so "{T}: Add one mana of
        # any color" — the templating of EVERY rainbow source — scored zero roles. With
        # that hole closed a fixer earns Ramp/fixing credit and stops sorting to the top
        # on its own.
        #
        # The `add_is_fixer` guard below is NOT redundant now: role credit makes a fixer
        # less cuttable, it does not make it uncuttable, and a fixer in a deck full of
        # higher-fit cards can still surface. The guard is what makes that safe.
        assert deck._weakest_cut(*self._fixture(), add_is_fixer=False) == "Filler Bear"

    def test_fixer_excluded_when_the_add_is_a_fixer(self):
        assert deck._weakest_cut(*self._fixture(), add_is_fixer=True) == "Filler Bear"

    def test_protected_and_lands_still_skipped(self):
        dmeta, cards, cardmeta, carddata = self._fixture()
        dmeta = {"protect": "Filler Bear"}
        # Only the fixer is left, and the add is a fixer → no honest hint to give.
        assert deck._weakest_cut(dmeta, cards, cardmeta, carddata,
                                 add_is_fixer=True) is None


class TestCentralThemesMechanicSubtheme:
    """centrality residual fix: a curated mechanical sub-theme surfaces at a flat floor
    of 2 even below the 25% cutoff, but a generic theme stays gated."""

    def test_mechanic_subtheme_admitted_at_floor_two(self):
        mech = next(iter(deck._MECHANIC_SUBTHEMES))
        assert mech in deck._central_themes({"tokens": 20, mech: 2})

    def test_generic_theme_still_gated_at_low_weight(self):
        assert "counters" not in deck._central_themes({"tokens": 20, "counters": 2})

    def test_mechanic_subtheme_below_floor_excluded(self):
        mech = next(iter(deck._MECHANIC_SUBTHEMES))
        assert mech not in deck._central_themes({"tokens": 20, mech: 1})


class TestRedundancyPlanner:
    """The 'virtual copies first, duplicates as fallback' decision helper."""

    def test_already_deep(self):
        p = deck.plan_redundancy_fill(4, 5.0, [(5.0, "X")], target=4)
        assert p["need"] == 0 and p["functional"] == [] and p["duplicates"] == 0

    def test_functional_covers_stays_singleton(self):
        opts = [(5.0, "A"), (4.5, "B"), (4.0, "C"), (4.0, "D")]
        p = deck.plan_redundancy_fill(1, 5.0, opts, target=4)  # need 3, all within tol
        assert p["duplicates"] == 0
        assert [n for _, n in p["functional"]] == ["A", "B", "C"]

    def test_no_options_falls_back_to_duplicates(self):
        p = deck.plan_redundancy_fill(1, 5.0, [], target=4)
        assert p["functional"] == [] and p["duplicates"] == 3
        assert "only option" in p["reason"]

    def test_much_weaker_options_duplicate_instead(self):
        # best existing is 6.0; the only virtual copy is 3.0 (>1.5 below) -> duplicate.
        p = deck.plan_redundancy_fill(2, 6.0, [(3.0, "weak")], target=4)
        assert p["functional"] == [] and p["duplicates"] == 2
        assert "weaker" in p["reason"]

    def test_partial_functional_then_duplicate(self):
        # one acceptable virtual copy, still short -> mix.
        p = deck.plan_redundancy_fill(1, 5.0, [(5.0, "A")], target=4)
        assert [n for _, n in p["functional"]] == ["A"] and p["duplicates"] == 2

    def test_tolerance_boundary_inclusive(self):
        # exactly tol below the best is still acceptable (>=).
        p = deck.plan_redundancy_fill(3, 5.0, [(3.5, "edge")], target=4)  # 5.0-1.5==3.5
        assert [n for _, n in p["functional"]] == ["edge"] and p["duplicates"] == 0


class TestEngineRoles:
    def test_sac_outlet_is_enabler(self):
        assert "enabler" in deck.engine_roles("Sacrifice a creature: Draw a card.").get("sacrifice", set())

    def test_death_trigger_is_death_not_payoff(self):
        got = deck.engine_roles("Whenever a creature you control dies, each opponent loses 1 life.").get("sacrifice", set())
        assert "death" in got and "payoff" not in got

    def test_sac_trigger_is_payoff(self):
        assert "payoff" in deck.engine_roles("Whenever you sacrifice a permanent, draw a card.").get("sacrifice", set())

    def test_edict_is_not_our_outlet(self):
        assert "enabler" not in deck.engine_roles("Target player sacrifices a creature.").get("sacrifice", set())

    def test_flashback_self_enables_graveyard(self):
        got = deck.engine_roles("Lightning deals 3 damage to any target. Flashback {4}{R}.").get("graveyard", set())
        assert "enabler" in got


class TestSyncPaste:
    """The pure pieces behind `deck.py sync` — splitting a multi-deck paste, matching a
    block to its stored deck, and rewriting a deck file's lines to a target list."""

    def _ms(self, **kw):
        return {k.lower(): (k, v) for k, v in kw.items()}

    def _d(self, i):
        return {"id": i, "name": f"deck{i}", "path": ""}

    def test_split_multi_deck_paste(self):
        segs = deck.split_paste("Deck\n1 A\n2 B\n\nDeck\n3 C\n")
        assert len(segs) == 2
        assert [l for l in segs[0] if l.strip()] == ["1 A", "2 B"]

    def test_split_without_a_deck_marker(self):
        # A bare paste (no "Deck" header) is still one block.
        assert len(deck.split_paste("1 A\n2 B\n")) == 1

    def test_split_ignores_empty_blocks(self):
        assert deck.split_paste("Deck\n\nDeck\n1 A\n") == [["1 A"]]

    def test_diff_direction(self):
        added, removed, diffs = deck._ms_diff(self._ms(A=3, B=1), self._ms(A=1, C=2))
        assert (added, removed) == (2 + 1, 2)          # +2 A, +1 B, -2 C
        assert ("+", 2, "A") in diffs and ("-", 2, "C") in diffs

    def test_matches_closest_deck(self):
        m = deck.match_paste(self._ms(A=4, B=4, C=4),
                             [(self._d("1"), self._ms(A=4, B=4, C=4)),
                              (self._d("2"), self._ms(A=4, B=4, Z=4))])
        assert m["deck"]["id"] == "1" and m["sync"] is True

    def test_unrelated_paste_is_unmatched(self):
        m = deck.match_paste(self._ms(Q=4, R=4, S=4, T=4),
                             [(self._d("1"), self._ms(A=4, B=4, C=4))])
        assert m.get("unmatched") is True

    # --- the FORMAT tie-breaker (deck 3 vs 3-brawl confusion) ----------------------
    # A Standard deck and its Brawl sibling share most card NAMES, so drift alone put
    # each inside the other's low-confidence window — while the paste itself carried an
    # unambiguous structural signal (Commander heading / deck size). `paste_format_hint`
    # reads that signal and `match_paste` sorts format-mismatched decks behind every
    # consistent one and excludes them from the low-confidence comparison. The dashboard
    # JS mirrors all of this (formatHint / deckFormatClass / bestMatch); change both.

    def _df(self, i, fmt):
        return {"id": i, "name": f"deck{i}", "path": "", "meta": {"format": fmt}}

    def test_format_hint_commander_heading(self):
        assert deck.paste_format_hint(["Commander", "1 A"], 60) == "commander"

    def test_format_hint_by_size(self):
        assert deck.paste_format_hint(["1 A"], 100) == "commander"
        assert deck.paste_format_hint(["1 A"], 60) == "sixty"
        assert deck.paste_format_hint(["1 A"], 80) is None

    def test_sixty_paste_prefers_sixty_sibling_over_closer_brawl(self):
        # The Brawl sibling is CLOSER by drift, but the paste is sixty-shaped:
        # the format-consistent deck must win.
        m = deck.match_paste(self._ms(A=4, B=4, C=4),
                             [(self._df("3", "standard"), self._ms(A=4, B=4, C=2)),
                              (self._df("3-brawl", "brawl"), self._ms(A=4, B=4, C=4))],
                             fmt_hint="sixty")
        assert m["deck"]["id"] == "3"

    def test_commander_paste_prefers_brawl_sibling(self):
        m = deck.match_paste(self._ms(A=1, B=1, C=1, D=1),
                             [(self._df("3", "standard"), self._ms(A=4, B=1, C=1, D=1)),
                              (self._df("3-brawl", "brawl"), self._ms(A=1, B=1, C=1, E=1))],
                             fmt_hint="commander")
        assert m["deck"]["id"] == "3-brawl"

    def test_format_mismatch_does_not_trigger_low_confidence(self):
        # The Brawl sibling is within 2 drift with plenty of shared cards — exactly the
        # shape that used to fire lowconf. A format-mismatched rival must not.
        m = deck.match_paste(self._ms(A=4, B=4, C=4, D=4),
                             [(self._df("3", "standard"), self._ms(A=4, B=4, C=4, D=4)),
                              (self._df("3-brawl", "brawl"), self._ms(A=4, B=4, C=4, D=2))],
                             fmt_hint="sixty")
        assert m["deck"]["id"] == "3" and m["lowconf"] is False

    def test_no_hint_keeps_pure_drift_behavior(self):
        m = deck.match_paste(self._ms(A=4, B=4, C=4),
                             [(self._df("3", "standard"), self._ms(A=4, B=4, C=2)),
                              (self._df("3-brawl", "brawl"), self._ms(A=4, B=4, C=4))])
        assert m["deck"]["id"] == "3-brawl"

    def test_unknown_deck_format_is_never_penalized(self):
        m = deck.match_paste(self._ms(A=4, B=4, C=4),
                             [(self._d("9"), self._ms(A=4, B=4, C=4))],
                             fmt_hint="sixty")
        assert m["deck"]["id"] == "9" and m["sync"] is True

    def test_low_confidence_between_siblings(self):
        m = deck.match_paste(self._ms(A=4, B=4, C=4, D=4, E=1),
                             [(self._d("1"), self._ms(A=4, B=4, C=4, D=4, E=2)),
                              (self._d("1a"), self._ms(A=4, B=4, C=4, D=4, E=1, F=1))])
        assert m["lowconf"] is True and m["runner_up"] is not None

    def test_clear_winner_is_not_flagged(self):
        m = deck.match_paste(self._ms(A=4, B=4, C=4),
                             [(self._d("1"), self._ms(A=4, B=4, C=4)),
                              (self._d("2"), self._ms(X=4, Y=4, Z=4))])
        assert m["lowconf"] is False

    # --- the truncation guard (broad-scan BS2-01) ----------------------------------
    # A partial paste is a strict SUBSET of its deck, so the shared-card floor —
    # measured against the paste — passes trivially and the match is full-confidence.
    # The first 8 lines of a 60-card deck dry-ran as "0 added / 52 removed" and
    # --apply would have rewritten the file to the fragment. A paste under 75% of the
    # stored total must flag `truncated` so cmd_sync refuses the write without --force.

    def test_subset_paste_is_flagged_truncated(self):
        m = deck.match_paste(self._ms(A=4, B=4, C=4),
                             [(self._d("1"), self._ms(A=4, B=4, C=4, D=4, E=4, F=4))])
        assert m.get("unmatched") is None          # it still MATCHES (the match is right)
        assert m["truncated"] is True              # ...but the write half must refuse
        assert m["paste_total"] == 12 and m["deck_total"] == 24

    def test_ordinary_edit_is_not_flagged_truncated(self):
        # A real edit pastes the whole deck with a few cards changed (here 12 vs 14,
        # ~0.86 — inside the legitimate trim range, e.g. an oversized draft cut down).
        m = deck.match_paste(self._ms(A=4, B=4, C=4),
                             [(self._d("1"), self._ms(A=4, B=4, C=4, D=2))])
        assert m["truncated"] is False

    def test_grown_deck_is_not_flagged_truncated(self):
        # The paste being LARGER than the stored deck is growth, never truncation.
        m = deck.match_paste(self._ms(A=4, B=4, C=4, D=4),
                             [(self._d("1"), self._ms(A=4, B=4, C=4))])
        assert m["truncated"] is False

    # --- the tie-break rule, pinned (broad-scan F-08) ------------------------------
    # `match_paste`'s docstring promises the dashboard's stale-check panel applies the
    # same rule, and the JS copy had drifted: it compared drift alone with a strict `<`,
    # so on an equal-drift tie the first deck in ITERATION order won, while Python
    # preferred more shared cards and then the lower id. Same paste, two answers —
    # exactly in the sibling-variant case low-confidence exists for. These pin the rule
    # the JS mirrors; if you change either, change both.

    def test_tie_on_drift_prefers_more_shared_cards(self):
        # Both decks are 2 cards of drift away. Deck "2" shares three cards, deck "1"
        # shares two, so "2" must win despite sorting later by id.
        m = deck.match_paste(self._ms(A=4, B=4, C=4),
                             [(self._d("1"), self._ms(A=4, B=4, Z=2)),
                              (self._d("2"), self._ms(A=4, B=4, C=2))])
        assert m["deck"]["id"] == "2"

    def test_tie_on_drift_and_shared_prefers_lower_id(self):
        # Identical drift AND identical shared count: the id decides, by CODEPOINT order
        # (the JS uses < / > rather than localeCompare for the same reason).
        m = deck.match_paste(self._ms(A=4, B=4, C=4),
                             [(self._d("2"), self._ms(A=4, B=4, C=2)),
                              (self._d("1"), self._ms(A=4, B=4, C=2))])
        assert m["deck"]["id"] == "1"

    def test_tie_break_is_independent_of_input_order(self):
        # The bug's actual signature: reordering the candidate list changed the answer.
        decks = [(self._d("1"), self._ms(A=4, B=4, C=2)),
                 (self._d("2"), self._ms(A=4, B=4, C=2))]
        a = deck.match_paste(self._ms(A=4, B=4, C=4), decks)
        b = deck.match_paste(self._ms(A=4, B=4, C=4), list(reversed(decks)))
        assert a["deck"]["id"] == b["deck"]["id"] == "1"

    def test_reconcile_preserves_structure_and_applies_target(self):
        lines = ["#: name: T", "", "# Creatures", "4 Foo (SET) 1", "1 Bar (SET) 2",
                 "# Lands", "20 Island", "#~ -Bar | +Baz | flex note"]
        out = deck.reconcile_lines(lines, self._ms(Foo=2, Baz=1, Island=20),
                                   {"baz": ("Baz", "NEW", "9")})
        assert "#: name: T" in out and "# Creatures" in out and "# Lands" in out
        assert "#~ -Bar | +Baz | flex note" in out          # comments/flex survive
        assert "4 Foo (SET) 1" not in out and "2 Foo (SET) 1" in out   # qty rewritten
        assert not any(l.startswith("1 Bar") for l in out)  # dropped card
        assert "1 Baz (NEW) 9" in out                       # new card, resolved printing

    def test_reconcile_new_card_without_a_known_printing(self):
        out = deck.reconcile_lines(["1 Foo (S) 1"], self._ms(Foo=1, Mystery=2), {})
        assert "2 Mystery" in out                            # bare line still parses

    def test_reconcile_totals_match_the_target(self):
        target = self._ms(Foo=3, Island=20)
        out = deck.reconcile_lines(["# c", "1 Foo (S) 1", "24 Island"], target, {})
        parsed = [deck.LINE_RE.match(l) for l in out if deck._card_line_name(l)]
        assert sum(int(m.group(1)) for m in parsed) == sum(q for _d, q in target.values())


class TestPowerThresholdFlags:
    """A "power 4 or greater" payoff reads unconditional to a synergy model but only
    fires off bodies that meet the bar on their PRINTED stats — measurable only since
    card-pool.csv started carrying Power/Toughness."""
    CD = {
        "garruk's uprising": {"name": "Garruk's Uprising", "type": "Enchantment",
                              "text": "Whenever a creature you control with power 4 or "
                                      "greater enters, draw a card.",
                              "power": "", "toughness": ""},
        "x hydra": {"name": "X Hydra", "type": "Creature — Hydra",
                    "text": "This creature enters with X +1/+1 counters on it.",
                    "power": "0", "toughness": "0"},
        "big beater": {"name": "Big Beater", "type": "Creature — Beast",
                       "text": "Trample.", "power": "6", "toughness": "6"},
        "star creature": {"name": "Star Creature", "type": "Creature — Avatar",
                          "text": "Power equal to cards in your graveyard.",
                          "power": "*", "toughness": "*"},
    }

    def test_flags_a_payoff_the_creatures_dont_support(self):
        cards = [(1, "Garruk's Uprising", "", ""), (8, "X Hydra", "", "")]
        flags = deck.power_threshold_flags(cards, self.CD)
        assert flags == [("Garruk's Uprising", "power", 4, 0, 8, "enters")]

    def test_attack_time_gates_report_their_timing(self):
        # G-16's live residual: the flag's caveat said "won't satisfy an ENTERS
        # trigger" for EVERY firing, and Scalestorm/Ruby check on ATTACK — pumped
        # bodies DO satisfy those. The timing now travels with the flag so the
        # caveat can tell the truth per trigger.
        cd = dict(self.CD, **{"attack gate": {
            "name": "Attack Gate", "type": "Creature — Human",
            "text": "Whenever this creature attacks while you control a creature "
                    "with power 4 or greater, draw a card.",
            "power": "1", "toughness": "1"}})
        cards = [(1, "Attack Gate", "", ""), (8, "X Hydra", "", "")]
        flags = deck.power_threshold_flags(cards, cd)
        assert flags[0][0] == "Attack Gate" and flags[0][5] == "attack"

    def test_silent_when_the_deck_supports_it(self):
        cards = [(1, "Garruk's Uprising", "", ""), (8, "Big Beater", "", "")]
        assert deck.power_threshold_flags(cards, self.CD) == []

    def test_star_power_counts_as_not_qualifying(self):
        # `*` is unknowable from printed stats; guessing would invent a fact.
        cards = [(1, "Garruk's Uprising", "", ""), (8, "Star Creature", "", "")]
        assert deck.power_threshold_flags(cards, self.CD)[0][3] == 0

    def test_no_creatures_is_not_an_error(self):
        assert deck.power_threshold_flags([(1, "Garruk's Uprising", "", "")], self.CD) == []

    # ---- scope: 16 of the roster's 27 flags were false, in two distinct shapes ----

    SCOPED = dict(CD, **{
        "sandbenders' storm": {
            "name": "Sandbenders' Storm", "type": "Instant", "power": "", "toughness": "",
            "text": "Destroy target creature with power 4 or greater."},
        "dusk": {
            "name": "Dusk", "type": "Sorcery", "power": "", "toughness": "",
            "text": "Destroy all creatures with power 3 or greater."},
        "beloved princess": {
            "name": "Beloved Princess", "type": "Creature — Human", "power": "1",
            "toughness": "1",
            "text": "Lifelink. This creature can't be blocked by creatures with "
                    "power 3 or greater."},
        "teamwork spell": {
            "name": "Teamwork Spell", "type": "Sorcery", "power": "", "toughness": "",
            "text": "Teamwork 4 (As an additional cost to cast this spell, you may tap "
                    "any number of creatures you control with total power 4 or more.) "
                    "Draw a card."},
        "betor": {
            "name": "Betor", "type": "Creature — Angel", "power": "4", "toughness": "4",
            "text": "At the beginning of your end step, if creatures you control have "
                    "total toughness 10 or greater, draw a card."},
    })

    def test_removal_targeting_their_creature_is_not_flagged(self):
        """"Destroy target creature with power 4 or greater" measures the WRONG board —
        the card wants THEIR creatures big. Deck 13 was warned that 6 of its 22
        creatures met a bar its removal spell asks of the opponent."""
        cards = [(1, "Sandbenders' Storm", "", ""), (8, "X Hydra", "", "")]
        assert deck.power_threshold_flags(cards, self.SCOPED) == []

    def test_a_sweeper_is_not_flagged_for_dodging_its_own_sweep(self):
        # For Dusk, FEW of your own creatures qualifying is the point of the card.
        cards = [(1, "Dusk", "", ""), (8, "X Hydra", "", "")]
        assert deck.power_threshold_flags(cards, self.SCOPED) == []

    def test_a_clause_about_their_blockers_is_not_flagged(self):
        cards = [(1, "Beloved Princess", "", ""), (8, "X Hydra", "", "")]
        assert deck.power_threshold_flags(cards, self.SCOPED) == []

    def test_total_power_is_a_sum_not_a_per_creature_bar(self):
        """Teamwork taps creatures with TOTAL power 4 — three 2/2s pay it. Counting
        bodies at printed power >= 4 is the wrong arithmetic, not a conservative read
        of the right one: deck 34 was told 0 of 19 creatures could pay a cost it pays
        trivially. This one still says "you control", so the total-check is load-bearing
        rather than incidentally covered by the scope test."""
        cards = [(1, "Teamwork Spell", "", ""), (8, "X Hydra", "", "")]
        assert deck.power_threshold_flags(cards, self.SCOPED) == []

    def test_total_toughness_is_a_sum_too(self):
        cards = [(1, "Betor", "", ""), (8, "X Hydra", "", "")]
        assert deck.power_threshold_flags(cards, self.SCOPED) == []

    def test_the_your_creatures_case_still_flags(self):
        # The whole point of the check must survive the scoping.
        cards = [(1, "Garruk's Uprising", "", ""), (8, "X Hydra", "", "")]
        assert deck.power_threshold_flags(cards, self.SCOPED) == [
            ("Garruk's Uprising", "power", 4, 0, 8, "enters")]


class TestRationaleStaleness:
    """The audit must flag a stale CLAIM without flagging accurate HISTORY — a rationale
    legitimately documents the change that produced the current list."""

    def _deck(self, tmp_path, tier_lines, cards=("1 Shock (M21) 159",)):
        p = tmp_path / "d.txt"
        p.write_text("\n".join([f"#: tier: {ln}" for ln in tier_lines]
                                + ["#: colors: R", "", "Deck", *cards]) + "\n")
        return {"id": "t", "name": "t", "path": str(p)}

    def test_flags_a_cut_card_the_argument_leans_on(self, tmp_path):
        d = self._deck(tmp_path, ["B — held to B because Lightning Bolt is the only answer."])
        cards, _figs = deck.rationale_staleness(d)
        assert "Lightning Bolt" in [c for c, _h in cards]

    def test_history_citation_is_suppressed(self, tmp_path):
        d = self._deck(tmp_path, ["B — re-graded after Lightning Bolt was cut for Shock."])
        cards, _figs = deck.rationale_staleness(d)
        assert cards == []

    def test_lowercase_common_noun_is_not_a_citation(self, tmp_path):
        # "Counterspell" is a real card name; the lowercase word is not a reference.
        d = self._deck(tmp_path, ["B — light on counterspell effects."])
        cards, _figs = deck.rationale_staleness(d)
        assert cards == []

    def test_historical_figure_is_suppressed(self, tmp_path):
        # "took interaction 1->4" describes a past change, not the current state.
        d = self._deck(tmp_path, ["A — the package took interaction 1 to 4."])
        _cards, figs = deck.rationale_staleness(d)
        assert figs == []

    # ── DATE ADJACENCY. The number-first figure patterns opened with a bare `(\d+)`,
    # which is unanchored, so it matched the tail of any larger number sitting before
    # the metric word. Deck 63's rationale said "three cards after the 2026-08
    # protection pass" and the audit reported `protection 08` against a live 4 — a
    # claim the prose never made. A false POSITIVE is the expensive direction here:
    # it teaches you to ignore the one check that reads the argument, not the letter.

    def test_a_date_before_a_metric_word_is_not_a_figure(self, tmp_path):
        d = self._deck(tmp_path, ["B — three answers after the 2026-08 protection pass."])
        _cards, figs = deck.rationale_staleness(d)
        assert [f for f in figs if f[0] == "protection"] == []

    def test_a_date_before_interaction_is_not_a_figure(self, tmp_path):
        d = self._deck(tmp_path, ["B — rebuilt in the 2026-08 interaction pass."])
        _cards, figs = deck.rationale_staleness(d)
        assert [f for f in figs if f[0] == "interaction"] == []

    def test_a_range_is_not_audited_as_a_precise_claim(self, tmp_path):
        # "2-3 interaction" states a band, not a figure; auditing it against an exact
        # live value would flag prose that is not making an exact claim.
        d = self._deck(tmp_path, ["B — sits at 2-3 interaction depending on the draw."])
        _cards, figs = deck.rationale_staleness(d)
        assert [f for f in figs if f[0] == "interaction"] == []

    def test_the_guard_does_not_silence_a_real_number_first_figure(self, tmp_path):
        # The whole point of the number-first patterns: this deck runs 0 interaction,
        # so a claimed 9 must still be caught. Guarding the date must not cost this.
        d = self._deck(tmp_path, ["A — 9 interaction carries it."])
        _cards, figs = deck.rationale_staleness(d)
        assert any(k == "interaction" and q == "9" for k, q, _a in figs)

    # ── Shorthand DETECTION (broad-implement #2). Two real misses survived a clean
    # audit: deck 28 cited "Gishath" after Gishath, Sun's Avatar was cut, and deck 36
    # cited "Okinec Ahau" after Sovereign Okinec Ahau was cut. G-26's "shorthand is
    # handled" covered only the suppression direction (an abbreviation of an IN-deck
    # card must not flag) — a shorthand citation of an ABSENT card matched nothing,
    # because the scan searched for full names only.

    def test_comma_head_shorthand_of_absent_card_is_flagged(self, tmp_path):
        d = self._deck(tmp_path, ["A — big dinos, and Gishath carries the top end."])
        cards, _figs = deck.rationale_staleness(d)
        assert "Gishath, Sun's Avatar" in [c for c, _h in cards]

    def test_tail_shorthand_of_absent_card_is_flagged_even_when_ambiguous(self, tmp_path):
        # "Okinec Ahau" abbreviates BOTH Envoy of and Sovereign Okinec Ahau; with
        # neither in the deck the citation is stale whichever it meant, so ambiguity
        # must not drop the fragment (that is exactly how the real miss would have
        # survived the fix).
        d = self._deck(tmp_path, ["A — the counter payoff Okinec Ahau carries it."])
        cards, _figs = deck.rationale_staleness(d)
        assert any("Okinec Ahau" in c for c, _h in cards)

    def test_shorthand_of_in_deck_card_stays_suppressed(self, tmp_path):
        d = self._deck(tmp_path, ["B — Gishath is the top end."],
                       cards=("1 Gishath, Sun's Avatar (LCI) 229",))
        cards, _figs = deck.rationale_staleness(d)
        assert cards == []

    def test_possessive_in_deck_name_suppresses_its_shorthand(self, tmp_path):
        # "Tishana" must read as shorthand for in-deck "Tishana's Tidebinder" — the
        # word-boundary rule treats the apostrophe as inside-a-word, so the in-deck
        # gate uses plain containment (over-suppression is the safe direction).
        d = self._deck(tmp_path, ["A — the soft tempo suite (Tishana and friends)."],
                       cards=("1 Tishana's Tidebinder (LCI) 81",))
        cards, _figs = deck.rationale_staleness(d)
        assert cards == []

    def test_guild_name_is_color_vocabulary_not_a_citation(self, tmp_path):
        # Four decks false-flagged "Rakdos" (the guild word) as shorthand for a
        # Rakdos legend in the first roster sweep of this fix.
        d = self._deck(tmp_path, ["B — a Rakdos sacrifice shell at heart."])
        cards, _figs = deck.rationale_staleness(d)
        assert cards == []

    def test_negated_contrast_citation_is_suppressed(self, tmp_path):
        # 26a explains itself by contrast: "Note Mjölnir does NOT do this". The
        # negation IS the claim that the card isn't here.
        d = self._deck(tmp_path, ["B — note Gishath does NOT fit this plan."])
        cards, _figs = deck.rationale_staleness(d)
        assert cards == []

    # ── A fragment INSIDE a longer absent name must not resolve to a different card.
    # Live on deck 28 (2026-08-11): the prose cited "Savage Land Dinosaur" — one real
    # stale citation — and the audit reported TWO, the second being "Ka-Zar of the
    # Savage Land", a card the prose never names. Only IN-DECK names are masked before
    # the shorthand pass, so an ABSENT card's full name stays in the text and its
    # fragment gets matched and resolved to whatever else abbreviates to it.

    def test_fragment_inside_a_longer_absent_name_does_not_name_another_card(self, tmp_path):
        d = self._deck(tmp_path, ["A — the pass added Savage Land Dinosaur for reach."])
        cards, _figs = deck.rationale_staleness(d)
        named = [c for c, _h in cards]
        assert "Savage Land Dinosaur" in named, "the real citation must still flag"
        assert not any("Ka-Zar" in c for c in named), \
            "the fragment 'Savage Land' must not resolve to Ka-Zar of the Savage Land"

    def test_a_suppressed_full_name_is_not_re_flagged_via_its_fragment(self, tmp_path):
        # The dangerous half: if the full-name scan SUPPRESSES a citation (history cue
        # here), the fragment path must not smuggle it back in under another card's
        # name — that would defeat every suppression the full-name scan applies.
        d = self._deck(
            tmp_path,
            ["A — Savage Land Dinosaur was CUT 2026-08-11 for a cheaper body."])
        cards, _figs = deck.rationale_staleness(d)
        assert cards == []


class TestRationaleWordBoundary:
    """Card names are ordinary English often enough that a bare substring search
    misfires — it reported the card *Deliberate* inside the word "Deliberately"."""

    def _deck(self, tmp_path, header, text):
        p = tmp_path / "d.txt"
        p.write_text(f"#: {header}: {text}\n#: colors: R\n\nDeck\n1 Shock (M21) 159\n")
        return {"id": "t", "name": "t", "path": str(p)}

    def test_substring_inside_a_longer_word_is_not_a_citation(self, tmp_path):
        d = self._deck(tmp_path, "archetype", "Deliberately runs no Ninjas.")
        cards, _figs = deck.rationale_staleness(d)
        assert cards == []

    def test_archetype_header_is_scanned(self, tmp_path):
        d = self._deck(tmp_path, "archetype", "Built around Lightning Bolt as the finisher.")
        cards, _figs = deck.rationale_staleness(d)
        assert "Lightning Bolt" in [c for c, _h in cards]


class TestCountConfidence:
    """A classifier reports a false negative as a fact: `0` reads as "none" rather than
    "not detected". The count must carry its own uncertainty."""
    CD = {
        "shock": {"name": "Shock", "type": "Instant", "colors": "R",
                  "text": "Shock deals 2 damage to any target.", "power": "", "toughness": ""},
        "odd answer": {"name": "Odd Answer", "type": "Instant", "colors": "B",
                       "text": "Its controller sacrifices a creature of their choice.",
                       "power": "", "toughness": ""},
    }

    def test_clean_count_has_no_suffix(self):
        t = deck.role_tally([(2, "Shock", "", "")], self.CD)
        assert deck.count_conf(t, "interaction") == "2"

    def test_unclassified_card_is_reported_inline(self):
        # "Odd Answer" matches no role AND trips no broad cue — the Broken Wings case,
        # the one that did the most damage. It must not read as a clean count of 1.
        t = deck.role_tally([(1, "Shock", "", ""), (1, "Odd Answer", "", "")], self.CD)
        assert deck.count_conf(t, "interaction") == "1 (1 unclassified)"

    def test_missing_card_data_is_reported(self):
        t = deck.role_tally([(1, "Shock", "", ""), (1, "Unknown Card", "", "")], self.CD)
        assert "unreadable" in deck.count_conf(t, "interaction")


class TestDeckShape:
    """Themes cannot answer wide-vs-tall: "counters" is the same tag whether they all go
    on one creature or spread across twelve."""
    CD = {
        "token maker": {"name": "Token Maker", "type": "Creature", "colors": "W",
                        "text": "When this creature enters, create two 1/1 white Soldier "
                                "creature tokens.", "power": "2", "toughness": "2"},
        "doubler": {"name": "Doubler", "type": "Sorcery", "colors": "G",
                    "text": "Double the number of +1/+1 counters on target creature.",
                    "power": "", "toughness": ""},
        "bear": {"name": "Bear", "type": "Creature", "colors": "G", "text": "Vanilla.",
                 "power": "2", "toughness": "2"},
    }

    def test_token_makers_read_wide(self):
        sh = deck.deck_shape([(6, "Token Maker", "", "")], self.CD)
        assert sh["wide"] > sh["tall"]

    def test_amplifiers_read_tall(self):
        sh = deck.deck_shape([(6, "Doubler", "", "")], self.CD)
        assert sh["tall"] > sh["wide"]

    def test_a_single_counter_is_not_a_tall_signal(self):
        # The first draft counted "put a +1/+1 counter on target creature" as TALL, which
        # read a 27-creature WIDE value board as tall — a single counter is wide glue too.
        assert not any(p.search("Put a +1/+1 counter on target creature.")
                       for p in deck._TALL_CUES)

    def test_creature_density_pushes_wide(self):
        # 24 vanilla bears have no wide TEXT at all, but cannot be a tall deck.
        sh = deck.deck_shape([(24, "Bear", "", "")], self.CD)
        assert sh["wide"] > sh["tall"]


class TestNearDuplicates:
    CD = {
        "epic fight": {"name": "Epic Fight", "type": "Sorcery", "colors": "G",
                       "text": "Target creature you control fights target creature an "
                               "opponent controls.", "power": "", "toughness": ""},
        "chelonian tackle": {"name": "Chelonian Tackle", "type": "Sorcery", "colors": "G",
                             "text": "Target creature you control gets +0/+10, then it "
                                     "fights target creature an opponent controls.",
                             "power": "", "toughness": ""},
        "vanilla": {"name": "Vanilla", "type": "Creature", "colors": "G", "text": "Flying.",
                    "power": "2", "toughness": "2"},
    }
    MANA = {"epic fight": ("{2}{G}", 3, ""), "chelonian tackle": ("{2}{G}", 3, ""),
            "vanilla": ("{1}{G}", 2, "")}

    def test_same_job_same_cost_groups(self):
        groups = deck.near_duplicates(
            [(1, "Epic Fight", "", ""), (1, "Chelonian Tackle", "", "")], self.CD, self.MANA)
        assert groups and set(groups[0][1]) == {"Epic Fight", "Chelonian Tackle"}

    def test_roleless_cards_are_never_grouped(self):
        # No signal beats a guess: a card the classifier can't read isn't a duplicate.
        assert deck.near_duplicates([(2, "Vanilla", "", "")], self.CD, self.MANA) == []

    def test_far_apart_costs_are_not_interchangeable(self):
        mana = dict(self.MANA, **{"chelonian tackle": ("{6}{G}", 7, "")})
        assert deck.near_duplicates(
            [(1, "Epic Fight", "", ""), (1, "Chelonian Tackle", "", "")], self.CD, mana) == []


class TestPipDepthWarning:
    """Castability in suggest/suggest-homes is a SET test (card colours ⊆ deck colours),
    which cannot see pip DEPTH. That is how Anti-Venom ({W}{W}{W}{W}{W}) was recommended
    as a KEY fit for two GWR decks holding 10-11 white sources — ~1% to cast on turn five.
    """

    def test_five_pips_against_a_thin_colour_warns(self):
        w = deck.pip_depth_warning("{W}{W}{W}{W}{W}", {"W": 10})
        assert w is not None
        col, pips, have, want = w
        assert (col, pips, have) == ("W", 5, 10)
        assert want is None or want > have

    def test_deep_pips_with_deep_sources_do_not_warn(self):
        assert deck.pip_depth_warning("{B}{B}{B}", {"B": 24}) is None

    def test_two_pips_are_below_the_floor(self):
        # 2 pips is ordinary; only 3+ of ONE colour is worth flagging.
        assert deck.pip_depth_warning("{3}{W}{W}", {"W": 8}) is None

    def test_hybrids_excluded(self):
        # Hybrid pips are strictly easier to pay, matching parse_pips' rule.
        assert deck.pip_depth_warning("{U/B}{U/B}{U/B}", {"U": 4, "B": 4}) is None

    def test_no_cost_is_safe(self):
        assert deck.pip_depth_warning("", {"W": 10}) is None
        assert deck.pip_depth_warning("{4}", {"W": 10}) is None


class TestDeckColorSources:
    def test_counts_basics_and_nonbasic_lands_only(self):
        cards = [(4, "Plains", "X", "1"), (2, "Sacred Foundry", "X", "2"),
                 (1, "Llanowar Elves", "X", "3")]
        meta = {"sacred foundry": {"colors": {"R", "W"}, "synergies": []},
                "llanowar elves": {"colors": {"G"}, "synergies": []}}
        cd = {"sacred foundry": {"type": "Land"},
              "llanowar elves": {"type": "Creature — Elf Druid"}}
        src = deck.deck_color_sources(cards, meta, cd)
        assert src["W"] == 6 and src["R"] == 2
        assert src["G"] == 0, "a mana dork is not a land source"


class TestDoublerCoSignal:
    """A doubler's worth scales with the deck's DENSITY of what it doubles — a magnitude
    theme overlap cannot see. Exalted Sunborn scored deck 45 (6 token-makers) above
    Knight's Edge (14) because both merely shared the `tokens` tag.
    """

    TOKEN_DBL = ("If one or more tokens would be created under your control, twice that "
                 "many of those tokens are created instead.")
    TRIG_DBL = ("If a triggered ability of a creature you control with power 2 or less "
                "triggers, that ability triggers an additional time.")

    LIFE_DBL = "If you would gain life, you gain twice that much life instead."
    LIFE_PLUS1 = "If you would gain life, you gain that much life plus 1 instead."

    def test_axis_detection(self):
        assert deck.doubler_axis(self.TOKEN_DBL) == "tokens"
        assert deck.doubler_axis(self.TRIG_DBL) == "triggers"
        assert deck.doubler_axis("Shock deals 2 damage to any target.") is None
        assert deck.doubler_axis("") is None

    def test_lifegain_is_an_axis(self):
        """The Wind Crystal read as NO doubler at all because the axis list stopped at
        tokens/counters/triggers, so it got no support, no fit bump, and `cuts` ranked it
        as an ordinary artifact."""
        assert deck.doubler_axis(self.LIFE_DBL) == "lifegain"

    def test_a_plus_N_lifegain_replacement_is_not_a_doubler(self):
        """The discriminator the lifegain axis needs: a replacement that is NOT a doubling
        is templated identically. Angel of Vitality is +1, not x2, and would qualify on the
        other axes' looser `instead` alternative."""
        assert deck.doubler_axis(self.LIFE_PLUS1) != "lifegain"


    def test_boost_is_zero_below_the_floor_and_rises_then_caps(self):
        assert deck.doubler_boost(0) == 0
        assert deck.doubler_boost(deck._DOUBLER_MIN_SOURCES - 1) == 0
        lo = deck.doubler_boost(deck._DOUBLER_MIN_SOURCES)
        hi = deck.doubler_boost(deck._DOUBLER_MIN_SOURCES + 5)
        assert 0 < lo < hi
        assert deck.doubler_boost(9999) == deck._DOUBLER_CAP

    def test_restriction_is_read_off_the_doublers_own_text(self):
        assert deck.doubler_restriction(self.TRIG_DBL) == 2
        assert deck.doubler_restriction(self.TOKEN_DBL) is None

    def test_support_counts_feeding_cards(self):
        cards = [(2, "Maker", "X", "1"), (1, "Bystander", "X", "2"), (7, "Plains", "X", "3")]
        cd = {"maker": {"type": "Creature — Soldier", "text": "When this creature enters, "
                        "create a 1/1 white Soldier creature token.", "power": "2"},
              "bystander": {"type": "Creature — Human", "text": "Vigilance", "power": "1"}}
        assert deck.doubler_support("tokens", cards, cd) == 2
        assert deck.doubler_support("tokens", cards, cd, max_power=1) == 0, \
            "a power restriction must exclude the 2-power maker"

    def test_restricted_support_excludes_unknown_power(self):
        # card_power returns None for */X — those must not be assumed to qualify.
        cards = [(1, "Star", "X", "1")]
        cd = {"star": {"type": "Creature — Elemental",
                       "text": "Whenever this creature attacks, draw a card.", "power": "*"}}
        assert deck.doubler_support("triggers", cards, cd, max_power=2) == 0


class TestCutsMultiplierCoSignal:
    """A multiplier's value is in the REST of the deck, and both halves of the cut score
    are blind to it: theme-fit sees few tags, `_role_credit` sees no role (doubling a
    trigger is not a functional role). Delney ranked as the WEAKEST card in deck 46 while
    `suggest-homes`, reading the SAME primitive, scored it correctly — the model was right
    and one caller never asked."""

    def test_zero_below_the_floor(self):
        assert deck._cuts_multiplier_adj(0) == 0
        assert deck._cuts_multiplier_adj(deck._CUTS_MULT_MIN_SOURCES - 1) == 0

    def test_rises_with_support_then_caps(self):
        lo = deck._cuts_multiplier_adj(deck._CUTS_MULT_MIN_SOURCES)
        hi = deck._cuts_multiplier_adj(deck._CUTS_MULT_MIN_SOURCES + 4)
        assert 0 < lo < hi <= deck._CUTS_MULT_CAP
        assert deck._cuts_multiplier_adj(10_000) == deck._CUTS_MULT_CAP

    def test_never_negative(self):
        """It may only RAISE a keep-score. The no-support case is already handled by theme
        fit, so subtracting there would punish the same card twice."""
        assert min(deck._cuts_multiplier_adj(n) for n in range(0, 60)) >= 0


class TestStrictUpgrades:
    """`screen`'s answer to "you already run a worse version of this". Prayer of Binding is
    Liminal Hold plus Flash -- identical cost, identical text -- and nothing noticed while
    both sat in the same conversation."""

    HOLD = ("When Liminal Hold enters, exile up to one target nonland permanent an "
            "opponent controls until Liminal Hold leaves the battlefield. You gain 2 life.")
    PRAYER = ("Flash\nWhen Prayer of Binding enters, exile up to one target nonland "
              "permanent an opponent controls until Prayer of Binding leaves the "
              "battlefield. You gain 2 life.")

    def _world(self):
        carddata = {"liminal hold": {"name": "Liminal Hold", "type": "Enchantment",
                                     "text": self.HOLD},
                    "prayer of binding": {"name": "Prayer of Binding", "type": "Enchantment",
                                          "text": self.PRAYER},
                    "bear": {"name": "Bear", "type": "Creature — Bear", "text": ""}}
        mana = {"liminal hold": ("{3}{W}", 4), "prayer of binding": ("{3}{W}", 4),
                "bear": ("{1}{G}", 2)}
        return carddata, mana

    def test_flags_the_extra_clause(self):
        cd, mana = self._world()
        cards = [(1, "Liminal Hold", "ECL", "24")]
        assert deck.strict_upgrades("Prayer of Binding", self.PRAYER, 4,
                                    cards, cd, mana) == ["Liminal Hold"]

    def test_is_not_symmetric(self):
        """The worse card must not read as an upgrade of the better one."""
        cd, mana = self._world()
        cards = [(1, "Prayer of Binding", "FDN", "739")]
        assert deck.strict_upgrades("Liminal Hold", self.HOLD, 4, cards, cd, mana) == []

    def test_identical_text_and_cost_is_redundancy_not_an_upgrade(self):
        """Two copies of the same effect are often GOOD (virtual copies). Calling that an
        upgrade would fire the flag on every deck's own redundancy."""
        cd, mana = self._world()
        cd["twin"] = {"name": "Twin", "type": "Enchantment", "text": self.HOLD}
        mana["twin"] = ("{3}{W}", 4)
        cards = [(1, "Liminal Hold", "ECL", "24")]
        assert deck.strict_upgrades("Twin", self.HOLD, 4, cards, cd, mana) == []

    def test_a_textless_incumbent_is_never_upgraded(self):
        """A vanilla creature has an EMPTY clause set, which is a subset of everything —
        so without a guard every card would 'strictly upgrade' every vanilla."""
        cd, mana = self._world()
        cards = [(1, "Bear", "XXX", "1")]
        assert deck.strict_upgrades("Prayer of Binding", self.PRAYER, 4,
                                    cards, cd, mana) == []

    def test_a_more_expensive_card_is_not_an_upgrade(self):
        cd, mana = self._world()
        cards = [(1, "Liminal Hold", "ECL", "24")]
        assert deck.strict_upgrades("Prayer of Binding", self.PRAYER, 9,
                                    cards, cd, mana) == []


class TestReferenceTableMemo:
    """The reference CSVs were re-parsed on every loader call — 65 decks x ~0.31s of
    it in a roster pass, which is why the rationale sweep looked too expensive to run
    automatically and therefore never ran. The memo makes it affordable; these pin the
    two ways a file cache goes wrong: not noticing a rewrite, and not noticing that the
    PATH moved (which is how `check_suggest`'s synthetic-pool anchor would break)."""

    def _loader(self, tmp_path, monkeypatch):
        src = tmp_path / "table.csv"
        monkeypatch.setattr(deck, "_MEMO_TEST_CSV", str(src), raising=False)
        calls = []

        @deck._file_memo("_MEMO_TEST_CSV")
        def load():
            calls.append(1)
            return open(deck._MEMO_TEST_CSV).read().strip()
        return src, load, calls

    def test_repeat_calls_do_not_reread(self, tmp_path, monkeypatch):
        src, load, calls = self._loader(tmp_path, monkeypatch)
        src.write_text("a\n")
        assert load() == "a" and load() == "a"
        assert len(calls) == 1

    def test_a_rewrite_invalidates(self, tmp_path, monkeypatch):
        src, load, calls = self._loader(tmp_path, monkeypatch)
        src.write_text("a\n")
        assert load() == "a"
        src.write_text("b\n")           # same size, possibly the same mtime second
        assert load() == "b", "a same-size rewrite must invalidate (hence mtime_ns)"
        assert len(calls) == 2

    def test_repointing_the_path_invalidates(self, tmp_path, monkeypatch):
        """`check_suggest` sets `deck.POOL_CSV` to a synthetic pool. A path captured at
        decoration time would key on the real file and serve its cached rows."""
        src, load, _calls = self._loader(tmp_path, monkeypatch)
        src.write_text("real\n")
        assert load() == "real"
        other = tmp_path / "synthetic.csv"
        other.write_text("synthetic\n")
        monkeypatch.setattr(deck, "_MEMO_TEST_CSV", str(other))
        assert load() == "synthetic"

    def test_a_missing_file_is_not_cached_as_present(self, tmp_path, monkeypatch):
        src, load, _calls = self._loader(tmp_path, monkeypatch)
        with pytest.raises(OSError):
            load()
        src.write_text("now here\n")
        assert load() == "now here"


class TestNameResolution:
    """The pile-triage resolver shared by `deck.py resolve` and `deck.py screen`.

    A pasted pile is written by a person, so it drops the punctuation the printed name
    carries. Screening one real 111-card pile left 22 names unresolved — overwhelmingly
    `Name, Epithet` legendaries typed without the comma — so the tool silently handed back
    the fifth of the pile that most needed grading, and those cards were graded by hand
    instead. That is where nine cards got mis-classified."""

    TABLE = {
        "ramos, dragon engine": "Ramos, Dragon Engine",
        "gran-gran": "Gran-Gran",
        "flotsam // jetsam": "Flotsam // Jetsam",
        "flotsam": "Flotsam // Jetsam",
        "master pakku": "Master Pakku",
        "kitsa, otterball elite": "Kitsa, Otterball Elite",
        "kitsune's technique": "Kitsune's Technique",
        "kitsune, dragon's daughter": "Kitsune, Dragon's Daughter",
    }

    def _resolve(self, q):
        disp = lambda k: self.TABLE[k]
        sq = deck._squash_index(self.TABLE, disp)
        return deck._resolve_card_name(q, self.TABLE, disp, sq)

    def test_exact_name_still_wins(self):
        assert self._resolve("Ramos, Dragon Engine")[0] == "ramos, dragon engine"

    def test_missing_comma_resolves(self):
        assert self._resolve("Ramos Dragon Engine")[0] == "ramos, dragon engine"

    def test_missing_hyphen_resolves(self):
        assert self._resolve("Gran Gran")[0] == "gran-gran"

    def test_missing_space_around_dfc_slashes_resolves(self):
        assert self._resolve("Flotsam//Jetsam")[0] == "flotsam // jetsam"

    def test_trailing_parenthetical_note_is_stripped(self):
        assert self._resolve("Master Pakku (needs Lessons)")[0] == "master pakku"

    def test_several_trailing_notes_are_stripped(self):
        assert deck._name_query("Bruce Banner (front face) (owned)") == "Bruce Banner"

    def test_a_typo_is_reported_not_guessed(self):
        """The resolver must NOT be a spell-corrector. Guessing at a misspelling grades
        the wrong card silently, which is strictly worse than reporting the name back."""
        key, cands = self._resolve("Impostoer Syndrome")
        assert key is None and cands == []

    def test_a_genuinely_ambiguous_prefix_reports_candidates(self):
        key, cands = self._resolve("Kitsune")
        assert key is None
        assert cands == ["Kitsune's Technique", "Kitsune, Dragon's Daughter"]

    def test_a_dfc_front_and_full_name_are_one_card_not_an_ambiguity(self):
        key, cands = self._resolve("flotsam")
        assert key is not None and cands == []


class TestCandidateCastability:
    """`screen`'s castability read, off the PRINTED cost rather than color identity.

    Identity and cost disagree exactly where a pile lives: `{1}{U/R}` and `{6}` are both
    payable with Islands alone and both read as off-color in `Color(s)`. Triaging a pile on
    that column mis-sorted nine cards, eight of them castable (G-58, bulk-triage variant)."""

    U = frozenset("U")

    def test_on_color_cost_is_clean(self):
        ok, note = deck._candidate_castability("{1}{U}", set("U"), self.U)
        assert ok and note == ""

    def test_true_hybrid_is_castable_and_labelled(self):
        ok, note = deck._candidate_castability("{1}{U/R}", set("UR"), self.U)
        assert ok and "hybrid — paid on-color" in note

    def test_colorless_cost_is_castable_whatever_the_identity(self):
        """Ramos, Dragon Engine: cost {6}, identity WUBRG from its mana ability."""
        ok, note = deck._candidate_castability("{6}", set("WUBRG"), self.U)
        assert ok and "still castable" in note

    def test_gold_cost_is_not_castable(self):
        ok, note = deck._candidate_castability("{3}{G}{U}{R}", set("URG"), self.U)
        assert not ok and "NOT castable" in note and "G" in note and "R" in note

    def test_monocolor_hybrid_never_constrains(self):
        ok, _ = deck._candidate_castability("{2/W}", set("W"), self.U)
        assert ok

    def test_unknown_cost_says_so_rather_than_asserting(self):
        ok, note = deck._candidate_castability("", set("R"), self.U)
        assert ok and "cost unknown" in note


class TestGenericSignatureBar:
    """`_strong_signature_themes` clears a GENERIC theme only at half the protect list.

    The signature exists to rescue a theme idf calls generic when it is genuinely the
    deck's spine, so a SPECIFIC theme keeps the flat >=2 bar. But >=2 was tuned against a
    3-to-5-card protect list: at 14 protected cards it is 14% of them, which let deck 46
    rescue `Human`, `combat` and `flying`. Those false spines fed `fit_strength`, whose KEY
    label then fired on 66% of a 111-card pile."""

    def _sig(self, protect, tags):
        meta = {"protect": "; ".join(protect)}
        cards = [(1, n, "", "") for n in protect]
        cardmeta = {n.lower(): {"synergies": t} for n, t in tags.items()}
        return deck._strong_signature_themes(meta, cards, cardmeta)

    def test_a_specific_theme_still_clears_at_two(self):
        sig = self._sig(["A", "B", "C", "D", "E", "F", "G", "H"],
                        {"A": ["Dragon"], "B": ["Dragon"], "C": [], "D": [], "E": [],
                         "F": [], "G": [], "H": []})
        assert "Dragon" in sig, "a narrow tribal spine must survive a long protect list"

    def test_a_generic_theme_needs_half_the_protect_list(self):
        prot = ["A", "B", "C", "D", "E", "F", "G", "H"]
        tags = {n: (["card draw"] if n in ("A", "B") else []) for n in prot}
        assert "card draw" not in self._sig(prot, tags)

    def test_a_generic_theme_that_really_is_the_spine_survives(self):
        prot = ["A", "B", "C", "D"]
        tags = {n: ["counters"] for n in prot}
        assert "counters" in self._sig(prot, tags), (
            "the whole point of the rescue: a counters deck protecting counter-doublers")

    def test_a_short_protect_list_is_unchanged(self):
        """The original >=2 behavior held for 3-to-5 protected cards and must not move."""
        sig = self._sig(["A", "B", "C"],
                        {"A": ["counters", "flying"], "B": ["counters", "haste"],
                         "C": ["card draw"]})
        assert "counters" in sig and "card draw" not in sig and "flying" not in sig


class TestPrimaryTypeFrontFace:
    """`_primary_type` reads the FRONT face of a two-faced type line.

    A substring scan over `Front // Back` reports the BACK face's type whenever it
    sorts earlier in the order list — which for `Land` is always. Every one of this
    module's ~35 `"Land" in _primary_type(...)` guards then skipped the card: out of
    the curve, uncounted as a creature, and added to the land total. `consistency 49`
    reported "Lands: 26/60" for a deck holding 25."""

    def test_creature_with_a_land_back_is_a_creature(self):
        assert deck._primary_type("Legendary Creature — God // Land") == "Creature"

    def test_artifact_with_a_land_back_is_an_artifact(self):
        assert deck._primary_type(
            "Legendary Artifact // Legendary Artifact Land") == "Artifact"

    def test_enchantment_with_a_land_back_is_an_enchantment(self):
        assert deck._primary_type("Enchantment // Land — Cave") == "Enchantment"

    def test_a_real_land_front_is_still_a_land(self):
        """Jidoor: the front genuinely IS a land, so it must keep reporting Land."""
        assert deck._primary_type("Land — Town // Sorcery — Adventure") == "Land"

    def test_single_faced_types_are_unchanged(self):
        assert deck._primary_type("Basic Land — Mountain") == "Land"
        assert deck._primary_type("Creature — Dragon") == "Creature"
        assert deck._primary_type("Instant") == "Instant"
        assert deck._primary_type("Enchantment — Room // Enchantment — Room") == "Enchantment"

    def test_unknown_and_empty_are_other(self):
        assert deck._primary_type("") == "Other"
        assert deck._primary_type("Scheme") == "Other"


class TestPrintingOfDFC:
    """`_printing_of` matches a DFC by its FRONT face and returns the CANONICAL name.

    The CSVs key a two-faced card under `Front // Back`, so an exact-only lookup for
    the front name found nothing and `swap --apply` wrote a bare `1 Runescale
    Stormbrood` with no printing. INV-04 passed and `legal` reported clean because a
    bare line parses — the failure only surfaced when a human pasted the deck into
    Arena."""

    def test_a_returned_triple_feeds_a_full_deck_line(self):
        disp, setc, cn = deck._printing_of("Lathliss, Dragon Queen")
        assert disp == "Lathliss, Dragon Queen"
        assert setc and cn, "a known card must resolve to a real printing"

    def test_front_face_query_resolves_to_the_full_name_and_a_printing(self):
        disp, setc, cn = deck._printing_of("Runescale Stormbrood")
        assert disp == "Runescale Stormbrood // Chilling Screech"
        assert setc and cn

    def test_full_dfc_name_still_resolves(self):
        disp, setc, _ = deck._printing_of("Runescale Stormbrood // Chilling Screech")
        assert disp == "Runescale Stormbrood // Chilling Screech" and setc

    def test_an_unknown_name_degrades_to_a_bare_line(self):
        assert deck._printing_of("Not A Real Card") == ("Not A Real Card", "", "")

    def test_the_swap_writes_the_canonical_name(self):
        disp, setc, cn = deck._printing_of("Ojer Axonil, Deepest Might")
        out = deck._cards_after_swap([(1, "Cut Me", "AAA", "1")], "Cut Me", disp, (setc, cn))
        assert out == [(1, "Ojer Axonil, Deepest Might // Temple of Power", setc, cn)]


class TestSwapApplyWritePath:
    """`swap --apply` is the sanctioned way to edit a deck, and it had NO test.

    P8 split `_printing_of`'s return from a 2-tuple into three values and updated one of
    its two call sites, leaving `add_pr` dangling in `_do_swap` — so every `--apply`
    raised NameError while the dry run, which returns before that line, stayed clean.
    `check_commands` reported `swap` covered the whole time, because coverage there means
    a skill REFERENCES the subcommand, not that anything drives it. This pins the write
    path itself."""

    def _deck(self, tmp_path, lines):
        d = tmp_path / "decks" / "99-t"
        d.mkdir(parents=True)
        (d / "deck.txt").write_text("\n".join(lines) + "\n")
        return str(tmp_path / "decks")

    def test_apply_writes_the_swap_and_preserves_the_copy_count(self, tmp_path, monkeypatch):
        from types import SimpleNamespace as NS
        lines = ["#: name: T", "#: colors: R", "", "# Spells",
                 "4 Shock (M21) 159", "2 Lightning Strike (MSH) 142", "54 Mountain"]
        monkeypatch.setattr(deck, "DECKS_DIR", self._deck(tmp_path, lines))
        monkeypatch.setattr(deck, "RECS_CSV", str(tmp_path / "recs.csv"))
        rc = deck.cmd_swap(NS(id="99", cut="Shock", add="Lightning Strike", apply=True))
        assert rc == 0
        _, cards = deck.parse_deck_file(str(tmp_path / "decks" / "99-t" / "deck.txt"))
        got = {n: q for q, n, _s, _c in cards}
        assert sum(got.values()) == 60          # _safe_write_lines' INV-04 total check
        assert got["Shock"] == 3 and got["Lightning Strike"] == 3

    def test_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        from types import SimpleNamespace as NS
        lines = ["#: name: T", "", "4 Shock (M21) 159", "56 Mountain"]
        root = self._deck(tmp_path, lines)
        monkeypatch.setattr(deck, "DECKS_DIR", root)
        before = (tmp_path / "decks" / "99-t" / "deck.txt").read_text()
        deck.cmd_swap(NS(id="99", cut="Shock", add="Lightning Strike", apply=False))
        assert (tmp_path / "decks" / "99-t" / "deck.txt").read_text() == before


class TestPrintingValidation:
    """F-01: a deck line's `(SET) COLLECTOR#` was validated by NOTHING.

    `1 Eaten Alive (ZZZ) 172` — a set code that does not exist — passed `legal`, passed
    `check` (which reported it OWNED, because ownership joins on the NAME), passed
    `preflight` READY and passed `check_all` "All invariants hold". A deck file could be
    integrity-clean and un-importable at the same time. Hit for real: deck 52 was written
    with `(FDN) 610` for a card whose collector number is 172."""

    def test_nonexistent_set_code_is_hard(self):
        bad, unverified = deck.printing_problems([(1, "Eaten Alive", "ZZZ", "172")])
        assert [n for n, _s, _c in bad] == ["Eaten Alive"]
        assert unverified == []

    def test_wrong_collector_in_a_real_set_is_soft(self):
        bad, unverified = deck.printing_problems([(1, "Eaten Alive", "FDN", "610")])
        assert bad == []
        assert [n for n, _s, _c, _k in unverified] == ["Eaten Alive"]

    def test_the_real_printing_is_clean(self):
        assert deck.printing_problems([(1, "Eaten Alive", "FDN", "172")]) == ([], [])

    def test_basic_lands_are_exempt(self):
        """Arena prints several arts per set (Swamp MSH 291 AND 292 are both real) while
        the pool carries one. Measured before choosing the rule: a hard check without
        this exemption failed 61 of 78 deck files on basics alone."""
        assert deck.printing_problems([(24, "Swamp", "MSH", "292")]) == ([], [])

    def test_a_line_with_no_printing_stated_is_not_flagged(self):
        assert deck.printing_problems([(1, "Eaten Alive", "", "")]) == ([], [])

    def test_no_roster_deck_names_a_nonexistent_set(self):
        """The hard half must fail nothing today, or it could not have been made hard."""
        for d in deck.discover_decks():
            _meta, cards = deck.parse_deck_file(d["path"])
            bad, _unv = deck.printing_problems(cards)
            assert bad == [], f"deck {d['id']}: {bad}"


class TestIntentionalUncastable:
    """F-02: an intentionally-uncastable reanimation target read as a build ERROR.

    Measured on deck 52a before the fix: adding ONE five-colour bomb to a mono-black
    reanimator moved `preflight` READY -> BLOCKED and the metrics floor A -> C. Three
    bands, for a card working exactly as designed. Reanimator is not an exotic archetype
    — it is why `Zombify` is in the pool."""

    def test_header_parses_semicolon_separated_names(self):
        assert deck._uncastable_ok({"uncastable-ok": "Cosmic Spider-Man; Krang, Utrom Warlord"}) \
            == {"cosmic spider-man", "krang, utrom warlord"}

    def test_hyphenated_meta_keys_parse_at_all(self, tmp_path):
        """META_RE allowed only [A-Za-z_], so `#: uncastable-ok:` never became a key —
        and neither did `#: based-on:`, which 24 roster lines already used and which was
        being silently dropped."""
        p = tmp_path / "d.txt"
        p.write_text("#: name: T\n#: based-on: deck.txt\n#: uncastable-ok: Shock\n1 Shock (M21) 159\n")
        meta, _ = deck.parse_deck_file(str(p))
        assert meta["based-on"] == "deck.txt"
        assert meta["uncastable-ok"] == "Shock"

    def test_exempt_card_leaves_the_failure_list_but_is_still_reported(self):
        cards = [(1, "Cosmic Spider-Man", "SPM", "175")]
        mana = {"cosmic spider-man": ("{W}{U}{B}{R}{G}", "5")}
        cd = {"cosmic spider-man": {"name": "Cosmic Spider-Man", "type": "Creature",
                                    "text": "", "colors": "W/U/B/R/G"}}
        unc, _oi, _oa, intended = deck._castability(cards, {"B"}, mana, cd)
        assert [n for n, _w in unc] == ["Cosmic Spider-Man"] and intended == []
        unc, _oi, _oa, intended = deck._castability(cards, {"B"}, mana, cd,
                                                    {"cosmic spider-man"})
        assert unc == [] and [n for n, _w in intended] == ["Cosmic Spider-Man"]


class TestUncastableCapsRatherThanSets:
    """F-16, subsumed by F-02: `tier_band` RETURNED "C" on a stray instead of capping at
    it, so a deck whose measurable floor was D got RAISED by holding a dead card. "Caps"
    is what the docstring and CLAUDE.md's rubric always said; only the code disagreed."""

    def test_a_stray_cannot_raise_a_d_floor(self):
        vec = {"uncastable": 1, "interaction": 0, "card_advantage": 0}
        assert deck.tier_band(vec) == "D"

    def test_a_stray_still_caps_an_a_floor(self):
        vec = {"uncastable": 1, "interaction": 10, "card_advantage": 3}
        assert deck.tier_band(vec) == "C"
        vec["uncastable"] = 0
        assert deck.tier_band(vec) == "A"


class TestTargetCounts:
    """F-04: nothing answered "does this deck contain TARGETS for its own effects".

    Deck 52's concept pile held 24 ways to return a creature against 8 worth returning,
    and that number came from a hand-written script. G-61 states the discipline in prose
    with four overturned dismissals behind it, precisely because nothing automated it."""

    CD = {"reanimate": {"name": "Reanimate", "type": "Sorcery",
                        "text": "Return target creature card with mana value 4 or less "
                                "from your graveyard to the battlefield.", "colors": "B"},
          "smallguy": {"name": "SmallGuy", "type": "Creature — Human", "text": "", "colors": "B"},
          "bigguy": {"name": "BigGuy", "type": "Creature — Giant", "text": "", "colors": "B"}}
    MANA = {"reanimate": ("{1}{B}", "2"), "smallguy": ("{1}{B}", "2"), "bigguy": ("{7}{B}", "8")}

    def test_mv_cap_counts_only_the_creatures_under_the_cap(self):
        cards = [(1, "Reanimate", "", ""), (1, "SmallGuy", "", ""), (1, "BigGuy", "", "")]
        rows = deck.target_counts(cards, self.CD, self.MANA)
        mv = [r for r in rows if "MV ≤4" in r[1]]
        assert len(mv) == 1 and mv[0][2] == 1        # SmallGuy only; BigGuy is MV 8

    def test_a_gate_with_nothing_behind_it_reports_zero(self):
        cards = [(1, "Reanimate", "", ""), (1, "BigGuy", "", "")]
        rows = deck.target_counts(cards, self.CD, self.MANA)
        assert [r for r in rows if "MV ≤4" in r[1]][0][2] == 0

    def test_a_card_is_never_its_own_target(self):
        cd = dict(self.CD)
        cd["outlet"] = {"name": "Outlet", "type": "Creature — Human",
                        "text": "Sacrifice a creature: draw a card.", "colors": "B"}
        mana = dict(self.MANA, outlet=("{B}", "1"))
        rows = deck.target_counts([(1, "Outlet", "", "")], cd, mana)
        assert [r for r in rows if "sacrifice" in r[1]][0][2] == 0

    def test_no_saturated_discard_rule(self):
        """A generic "cards to discard" gate was written and removed: it reported 35 for
        every discard outlet in a 60-card deck, i.e. "you have a hand"."""
        assert not any(kind == "any" for _rx, _lbl, kind in deck._TARGET_GATES)


class TestRationaleAuditMisses:
    """F-03: the audit reported "rationale is current" on prose that was stale twice."""

    def test_removes_in_oracle_text_no_longer_suppresses_a_citation(self):
        """`remov\\w*` matched the card's OWN description — "Summon: Bahamut is a {9}
        that REMOVES two nonland permanents" — and suppressed the staleness report. The
        same word is already documented as "the worst of them" on the FIGURE path, where
        it was narrowed; only the CARD path kept the broad form."""
        w = "it attacks the turn it lands. Summon: Bahamut is a {9} that removes two"
        assert not deck._HISTORY_CUES.search(w)
        assert deck._HISTORY_CUES.search("Bahamut was removed for Bringer")

    def test_average_is_read_as_well_as_avg(self):
        """"Average nonland MV 4.17" passed while the live value was 4.22 — "avg" is not
        a prefix of "Average", so no pattern could see it."""
        hits = [key for rx, key in deck._RATIONALE_FIGURES
                if rx.search("TIGHT CURVE — Average nonland MV 4.17 on 12 early drops")]
        assert "avg_mv" in hits

    def test_a_simile_is_not_a_citation(self):
        """"It'll Quench Ya! is Spell Pierce that hits creatures too" explains an in-deck
        card BY NAMING one the deck does not run. The name is the yardstick, not a claim."""
        assert deck._SIMILE_BEFORE.search("Ya! is ")
        assert not deck._SIMILE_BEFORE.search("cut the ")

    def test_shorthand_for_an_in_deck_card_is_not_a_citation(self):
        """Deck 33 writes "Heartfire sac-removal" for Heartfire Immolator, and Heartfire
        is itself a real card. Masking cannot help — the full name is not in the text."""
        assert any(o.startswith("Heartfire" + " ") for o in {"Heartfire Immolator"})


class TestWrongExclusionClaims:
    """F-03, related: `#: notes:` is exempt from the staleness scan because naming an
    ABSENT card there is correct — but "Deliberately NOT included: Bringer of the Last
    Gift" after Bringer was ADDED is a false claim about the current list, the opposite
    direction from the one the exemption covers."""

    def _deck(self, tmp_path, notes, lines):
        d = tmp_path / "decks" / "98-x"
        d.mkdir(parents=True)
        (d / "deck.txt").write_text(f"#: name: X\n#: notes: {notes}\n" + "\n".join(lines) + "\n")
        return {"id": "98", "name": "X", "path": str(d / "deck.txt")}

    def test_claiming_a_card_is_excluded_while_running_it_is_flagged(self, tmp_path):
        d = self._deck(tmp_path, "Deliberately NOT included and why: Lightning Strike "
                                 "(too slow); Shock (worse).", ["4 Lightning Strike (MSH) 142"])
        assert [n for n, _h in deck.wrong_exclusion_claims(d)] == ["Lightning Strike"]

    def test_a_replacement_named_after_the_dash_is_not_the_excluded_card(self, tmp_path):
        """"Craterhoof is deliberately NOT here — Summon: Titan is this deck's mass pump"
        names the REPLACEMENT after the boundary. A plain distance window reported ten
        roster hits and every one sampled was noise; this shape reports zero."""
        d = self._deck(tmp_path, "Craterhoof is deliberately NOT here — Lightning Strike "
                                 "is this deck's reach.", ["4 Lightning Strike (MSH) 142"])
        assert deck.wrong_exclusion_claims(d) == []

    def test_no_roster_deck_trips_it(self):
        for dd in deck.discover_decks():
            assert deck.wrong_exclusion_claims(dd) == [], dd["id"]


class TestScreenSaturationAndCounts:
    """F-05 / F-10: `screen`'s KEY label fired on ~half of every pile, and its header
    counted INPUTS rather than resolved candidates."""

    def test_key_saturation_threshold_exists_and_is_a_fraction(self):
        assert 0 < deck._SCREEN_KEY_SATURATED < 1

    def test_the_signature_rescue_is_preserved(self):
        """A tightening was TRIED and rejected: requiring a non-generic signature theme
        dropped deck 30's KEY rate 21%->1% and demoted Innkeeper's Talent, the
        counter-doubler-in-a-counters-deck case the signature branch exists for. So the
        fix REPORTS saturation instead of re-scoring — this pins that KEY still fires on a
        generic signature theme."""
        assert deck.fit_strength(["counters"], {"counters": 20}, "", 9, 5,
                                 frozenset({"counters"})) == "KEY"


class TestAlreadyInDeckJoinsAreFrontFaced:
    """BS4-05 / BS4-06 — two more members of the G-63 class, on the two surfaces that
    grade a card AGAINST a deck it might already be in.

    `screen` built `in_deck` with `_ms_key` (the comment even said "G-63: front-face
    join") and then probed it with the candidate's FULL display name, so every pool-keyed
    DFC read as absent: `screen` graded a maindecked card as a fresh candidate and never
    printed "already in the deck" — on the surface G-47 points at precisely to defeat
    stale verdicts. `suggest-homes` had the mirror shape: the CARD side was
    front-normalized and the DECK side was not, so it printed `in? no` plus a cut hint,
    recommending a deck make room for a card already in its 60. Six live deck/card
    combos across decks 6, 11, 31, 40a and 42a."""

    CARD = "Funeral Room // Awakening Hall"

    def _deck_with(self, tmp_path, line_name):
        p = tmp_path / "deck.txt"
        p.write_text("#: name: Probe\n#: colors: B\n\nDeck\n"
                     f"1 {line_name} (DSK) 90\n4 Swamp (MSH) 291\n", encoding="utf-8")
        return deck.parse_deck_file(str(p))

    def test_a_full_name_deck_line_matches_a_front_name_probe(self, tmp_path):
        """The `screen` shape: probe key vs index key must agree on the face."""
        _meta, cards = self._deck_with(tmp_path, self.CARD)
        in_deck = {deck._ms_key(n) for _q, n, _s, _c in cards}
        assert deck._ms_key(self.CARD) in in_deck
        assert deck._ms_key("Funeral Room") in in_deck      # either spelling resolves

    def test_a_front_name_deck_line_matches_a_full_name_probe(self, tmp_path):
        """The `suggest-homes` shape, which failed in the other direction: the DECK side
        was the un-normalized one."""
        _meta, cards = self._deck_with(tmp_path, "Funeral Room")
        deck_keys = {deck._ms_key(n) for _q, n, _s, _c in cards}
        assert deck._ms_key(self.CARD) in deck_keys

    def test_a_distinct_card_is_still_not_in_the_deck(self, tmp_path):
        """The join must not become permissive: a different card stays absent."""
        _meta, cards = self._deck_with(tmp_path, self.CARD)
        in_deck = {deck._ms_key(n) for _q, n, _s, _c in cards}
        assert deck._ms_key("Awakening Hall") not in in_deck     # the BACK face is not a key
        assert deck._ms_key("Lightning Bolt") not in in_deck


class TestBelowFloorArgument:
    """F-07: the tier guard flagged a deliberately conservative grade. Decks 51, 52 and
    52a all sit one band under an A floor WITH a written rubric argument, which the rubric
    permits — and all three carried a permanent "possibly UNDER-graded" nudge for it."""

    def test_a_rationale_that_argues_below_the_floor_is_recognised(self):
        assert deck._argues_below_floor(
            {"tier": "B — PROVISIONAL. One band BELOW the measurable floor, which reads A."})

    def test_a_bare_letter_is_not(self):
        assert not deck._argues_below_floor({"tier": "B — Rakdos aggro, fine curve."})
        assert not deck._argues_below_floor({})


class TestKeepableNeighbour:
    """F-08: the land advisory reversed direction and could not be satisfied — deck 52 at
    24 lands read "consider FEWER", the same list at 23 read "consider MORE" at a WORSE
    keepable."""

    def test_moving_one_land_the_suggested_way_is_actually_checked(self):
        at24, at23 = deck._keepable_at(24, 60), deck._keepable_at(23, 60)
        assert at24 is not None and at23 is not None
        assert at23 < at24          # the "fewer lands" advice made it worse

    def test_out_of_range_is_none(self):
        assert deck._keepable_at(-1, 60) is None and deck._keepable_at(61, 60) is None


class TestDeckStateAxis:
    """F-09b: a card whose value is a COUNT in the deck read at its FLOOR in every model.
    Cat-Gator scores as a 7-mana 3/2 lifelink; its ETB is damage equal to your Swamp
    count, and deck 52a runs 24."""

    def test_the_zone_is_part_of_the_axis(self):
        assert deck._deck_state_axis(
            "When this creature enters, it deals damage equal to the number of Swamps "
            "you control to any target.") == "Swamps you control"
        assert deck._deck_state_axis(
            "destroy it if its mana value is less than or equal to the number of cards "
            "in your graveyard") == "cards in your graveyard"

    def test_a_card_with_no_deck_state_axis_returns_none(self):
        assert deck._deck_state_axis("Destroy target creature.") is None
        assert deck._deck_state_axis("") is None


class TestCrossModuleDeckCallers:
    """`build_dashboard.py` calls into `deck.py`'s internals, and NOTHING exercised that
    seam. When `_castability` went from a 3-tuple to a 4-tuple for the `#: uncastable-ok:`
    header, every caller inside deck.py was found by grep and updated — and the dashboard's
    was missed, because the grep was scoped to one file. `check_all` does not build the
    dashboard, `tests/test_cli.py` only asserts `--help` exits 0, and the gates were green
    the whole time. It broke on the first real `build_dashboard.py` run, one deck later.

    This runs the actual function rather than asserting on the call SHAPE, so it survives
    a future signature change instead of needing to be rewritten alongside one."""

    def test_dashboard_deck_viz_runs_against_a_real_deck(self):
        import build_dashboard as bd
        d = deck.discover_decks()[0]
        meta, cards = deck.parse_deck_file(d["path"])
        viz = bd.deck_viz(meta, cards, deck.load_card_data(), deck.load_mana(),
                          deck.load_keywords(), *deck.load_collection()[:2])
        assert isinstance(viz, dict) and viz

    def test_dashboard_honours_the_uncastable_ok_header(self, tmp_path):
        """The exemption must reach the dashboard too, or a deck reads BLOCKED there and
        READY in `preflight` — the two surfaces disagreeing is the bug class this repo
        keeps rediscovering."""
        import build_dashboard as bd
        p = tmp_path / "d.txt"
        p.write_text("#: name: T\n#: colors: B\n#: uncastable-ok: Cosmic Spider-Man\n"
                     "1 Cosmic Spider-Man (SPM) 175\n1 Swamp (MSH) 291\n")
        meta, cards = deck.parse_deck_file(str(p))
        viz = bd.deck_viz(meta, cards, deck.load_card_data(), deck.load_mana(),
                          deck.load_keywords(), *deck.load_collection()[:2])
        assert not viz.get("uncastable"), viz.get("uncastable")


class TestOwnershipIsNotARankingTerm:
    """The owner's standing rule: build the OPTIMAL list, do not gate a card on whether it
    is owned. Two places in the tooling ranked on ownership rather than merit —
    `suggest`'s sort tiebreak ("owned as a tiebreaker so quick adds float up") and
    `tier --to`, which printed owned fillers first in their own capped section so a better
    craft filler sat below six owned ones. Ownership data here is hand-maintained and goes
    stale between updates, so those tiebreaks ranked on information that may be weeks old.
    Ownership is still SHOWN on every row; it is a note, not a preference."""

    def test_suggest_sort_key_has_no_ownership_term(self):
        import inspect
        src = inspect.getsource(deck.suggest_scored)
        sort_lines = [l for l in src.splitlines() if "suggestions.sort" in l]
        assert sort_lines, "suggest's sort disappeared — re-point this test"
        assert not any("owned" in l for l in sort_lines), sort_lines

    def test_the_owned_unowned_FILTERS_still_work(self):
        """The filters are the user asking a scoped question and must survive — only the
        implicit ranking preference was removed."""
        import inspect
        src = inspect.getsource(deck.suggest_scored)
        assert "if unowned:" in src and "owned_of" in src

    def test_tier_to_merges_owned_and_craft_into_one_ordering(self):
        import inspect
        src = inspect.getsource(deck.cmd_tier)
        assert "merged.sort" in src, "the two filler lists were un-merged"
        assert "ownership is a note" in src


class TestGraveyardTypeGates:
    """`targets` knew MV caps, sacrifice costs and the permanent-count threshold, and
    nothing about CARD-TYPE thresholds in the graveyard. Found by running it against deck
    54 — a Lesson deck built entirely on "three or more Lesson cards in your graveyard"
    and "the number of Lesson cards in your graveyard" — and getting "no gated effects
    detected" on a list with ten of them."""

    CD = {"payoff": {"name": "Payoff", "type": "Creature — Human",
                     "text": "This creature gets +1/+1 as long as there's a Lesson card "
                             "in your graveyard.", "colors": "U"},
          "scaler": {"name": "Scaler", "type": "Instant — Lesson",
                     "text": "Scaler deals damage equal to 2 plus the number of Lesson "
                             "cards in your graveyard.", "colors": "R"},
          "gate3": {"name": "Gate3", "type": "Creature — Serpent",
                    "text": "If there are three or more Lesson cards in your graveyard, "
                            "you may cast this spell as though it had flash.", "colors": "U"},
          "alesson": {"name": "ALesson", "type": "Sorcery — Lesson", "text": "Draw a card.",
                      "colors": "G"},
          "plain": {"name": "Plain", "type": "Instant", "text": "Draw a card.", "colors": "G"}}
    MANA = {k: ("{1}", "1") for k in CD}

    def _rows(self):
        cards = [(1, n, "", "") for n in ("Payoff", "Scaler", "Gate3", "ALesson", "Plain")]
        return deck.target_counts(cards, self.CD, self.MANA)

    def test_a_type_threshold_is_detected_and_counted(self):
        rows = [r for r in self._rows() if r[0] == "Gate3"]
        assert rows, "the 'N or more <type> cards in your graveyard' gate was not detected"
        # Only ALesson and Scaler carry the Lesson subtype; Gate3 excludes itself.
        assert rows[0][2] == 2, rows

    def test_a_word_number_is_parsed_and_shown_as_a_digit(self):
        label = [r[1] for r in self._rows() if r[0] == "Gate3"][0]
        assert "needs 3" in label, label

    def test_the_bare_number_of_form_is_detected(self):
        rows = [r for r in self._rows() if r[0] == "Scaler"]
        assert rows and "Lesson cards in the yard" in rows[0][1]
        assert rows[0][2] == 1          # ALesson only; Scaler excludes itself

    def test_the_there_is_a_card_form_is_detected(self):
        rows = [r for r in self._rows() if r[0] == "Payoff"]
        assert rows and rows[0][2] == 2, rows

    def test_permanent_is_left_to_its_own_rule_and_not_double_reported(self):
        """`permanent` has a dedicated gate; the type rule excludes it so one clause
        cannot produce two rows saying the same thing."""
        cd = dict(self.CD)
        cd["descend"] = {"name": "Descend", "type": "Creature — Horror",
                         "text": "Whenever you draw a card, if there are eight or more "
                                 "permanent cards in your graveyard, gain 1 life.",
                         "colors": "B"}
        mana = dict(self.MANA, descend=("{1}", "1"))
        cards = [(1, v["name"], "", "") for v in cd.values()]
        rows = [r for r in deck.target_counts(cards, cd, mana) if r[0] == "Descend"]
        assert len(rows) == 1, rows
        assert "permanent cards" in rows[0][1]


class TestNeedsFmtNormalization:
    """BS2-08: the needs recommenders (--ramp/--interaction/--needs) handed the raw
    `--format` string to workers whose only gate is exact membership in POOL_FORMATS,
    so `--format Standard` (the natural spelling) silently disabled ALL format
    filtering — non-Standard cards surfaced as top craft picks on exactly the paths
    G-38 routes a deficit to — and `--any-format` parsed but never reached the
    workers. `_needs_fmt` is the shared normalization, mirroring suggest_scored's."""

    def _ns(self, **kw):
        from types import SimpleNamespace
        return SimpleNamespace(**kw)

    def test_cased_format_is_lowered(self):
        assert deck._needs_fmt(self._ns(fmt="Standard"), {"format": ""}) == "standard"

    def test_any_format_disables_the_filter(self):
        assert deck._needs_fmt(self._ns(fmt="Standard", any_format=True),
                               {"format": "standard"}) == ""

    def test_deck_format_is_the_fallback(self):
        assert deck._needs_fmt(self._ns(fmt=None), {"format": "standard"}) == "standard"

    def test_an_untracked_format_warns_instead_of_silently_not_filtering(self, capsys):
        deck._needs_fmt(self._ns(fmt="foo"), {"format": ""})
        assert "not tracked" in capsys.readouterr().out


class TestSyncSameDeckClaim:
    """BS2-10: blocks are matched independently, so two pasted blocks could both
    resolve to one stored deck and the write loop wrote the file twice — the second
    write clobbering the first. First claim wins; later blocks are reported."""

    def test_second_block_matching_the_same_deck_is_skipped(self, tmp_path, monkeypatch, capsys):
        from types import SimpleNamespace
        p = tmp_path / "deck.txt"
        p.write_text("4 Aaa\n4 Bbb\n4 Ccc\n", encoding="utf-8")
        d = {"id": "1", "name": "T", "path": str(p), "core": True, "variant": None}
        monkeypatch.setattr(deck, "roster_decks", lambda: [d])
        monkeypatch.setattr(deck, "_printing_index", lambda: {})
        src = tmp_path / "paste.txt"
        src.write_text("Deck\n4 Aaa\n4 Bbb\n4 Ccc\n\nDeck\n4 Aaa\n4 Bbb\n3 Ccc\n",
                       encoding="utf-8")
        rc = deck.cmd_sync(SimpleNamespace(source=str(src), apply=False, force=False))
        out = capsys.readouterr().out
        assert "ALSO matched" in out and "block 1" in out
        assert rc == 1


class TestMalformedDeckLines:
    """BS2-14: parse_deck_file discards a line LINE_RE rejects with no record, so
    INV-04 — documented as "parses with no malformed card lines" — actually failed
    only on a file with ZERO parseable cards. A quantity-less line or a BOM-prefixed
    paste was silently deleted from every analysis."""

    def _deck(self, tmp_path, body):
        p = tmp_path / "deck.txt"
        p.write_text(body, encoding="utf-8")
        return str(p)

    def test_a_quantityless_card_line_is_reported(self, tmp_path):
        p = self._deck(tmp_path, "#: name: T\n4 Shock (M21) 159\nLightning Bolt (DMU) 137\n")
        hits = deck.malformed_deck_lines(p)
        assert len(hits) == 1 and "Lightning Bolt" in hits[0][1]

    def test_a_bom_prefixed_line_is_reported(self, tmp_path):
        p = self._deck(tmp_path, "﻿1 Island\n4 Shock (M21) 159\n")
        assert len(deck.malformed_deck_lines(p)) == 1

    def test_arena_markers_comments_and_headers_are_tolerated(self, tmp_path):
        p = self._deck(tmp_path,
                       "Deck\n#: name: T\n# Creatures\n#~ -A | +B\n4 Shock (M21) 159\n"
                       "Sideboard\n2 Negate (M21) 69\n")
        assert deck.malformed_deck_lines(p) == []

    def test_a_trailing_comment_on_a_card_line_is_fine(self, tmp_path):
        p = self._deck(tmp_path, "4 Shock (M21) 159  # burn\n")
        assert deck.malformed_deck_lines(p) == []


class TestSwapCutSideFrontFace:
    """BS2-21: the ADD side of a swap was `_ms_key`-matched (BS-05) but the CUT side
    stayed exact-name, so cutting a full-name-stored DFC by its front face refused
    with "not in deck" — the spelling `cuts`, `card.py` and G-02's worked example all
    use — and the flex auto-retire missed cross-spelled `#~` lines."""

    def test_front_name_cut_resolves_a_full_name_line(self):
        cards = [(1, "Mirror Room // Fractured Realm", "DSK", "50"), (4, "Opt", "M21", "1")]
        after = deck._cards_after_swap(cards, "Mirror Room", "Negate", ("M21", "69"))
        assert after is not None
        assert all(deck._ms_key(n) != "mirror room" for _q, n, _s, _c in after)

    def test_full_name_cut_resolves_a_front_name_line(self):
        cards = [(1, "Mirror Room", "DSK", "50"), (4, "Opt", "M21", "1")]
        after = deck._cards_after_swap(
            cards, "Mirror Room // Fractured Realm", "Negate", ("M21", "69"))
        assert after is not None

    def test_swap_edit_lines_accepts_a_front_name_cut(self):
        lines = ["1 Mirror Room // Fractured Realm (DSK) 50", "4 Opt (M21) 1"]
        out = deck._swap_edit_lines(lines, "Mirror Room", "Negate", ("M21", "69"))
        assert any(ln.startswith("1 Negate") for ln in out)
        assert not any("Mirror Room" in ln for ln in out)

    def test_flex_line_naming_the_front_face_is_retired_by_a_full_name_swap(self):
        lines = ["1 Mirror Room // Fractured Realm (DSK) 50",
                 "#~ -Mirror Room | +Negate | tempo"]
        out = deck._swap_edit_lines(
            lines, "Mirror Room // Fractured Realm", "Negate", ("M21", "69"))
        assert any("applied" in ln for ln in out)
        assert not any(ln.strip().startswith("#~ -Mirror Room |") for ln in out)


class TestRationaleStalenessLiveMisses:
    """Pins the 2026-08-09 audit rework: five LIVE misses found in one session (each
    reproduced as a fixture before the fix) plus the cross-deck-figure false positive.
    Every case here reported "rationale is current" — or flagged a correct citation —
    on real roster decks while a human read caught the truth. The suppression rules
    are the delicate part of this audit (G-26): each test names the rule it pins."""

    HEAD = "#: name: Probe\n#: format: Standard\n#: colors: GWU\n"
    BODY = "\nDeck\n1 Llanowar Elves (M19) 314\n1 Storm, Windrider (MSH) 230\n24 Forest (MSH) 295\n"

    def _deck(self, tmp_path, headers):
        p = tmp_path / "deck.txt"
        p.write_text(self.HEAD + headers + self.BODY, encoding="utf-8")
        return {"path": str(p), "id": "99"}

    def _cards(self, tmp_path, headers):
        cards, _figs = deck.rationale_staleness(self._deck(tmp_path, headers))
        return [n for n, _h in cards]

    def test_possessive_citation_is_visible(self, tmp_path):
        # "`consistency` prices Aven Interrupter's {W}{W} at 58%" — the word-boundary
        # rule read the 's as "inside a longer word" and every possessive citation of
        # an absent card was invisible (deck 19, the session's fifth live miss).
        got = self._cards(tmp_path, "#: tier: B. Aven Interrupter's {W}{W} prices at 58% on turn three.\n")
        assert "Aven Interrupter" in got

    def test_a_cue_word_inside_the_cards_own_name_does_not_suppress(self, tmp_path):
        # `_HISTORY_CUES` has swap\w* — and the card *Crib Swap* was suppressed by the
        # "Swap" in its OWN NAME (deck 19's original block). The citation span is now
        # excluded from the cue window; no prose edit could ever have fixed this one.
        got = self._cards(tmp_path, "#: tier: B. The package (+Crib Swap) took interaction 1→4.\n")
        assert "Crib Swap" in got

    def test_short_comma_head_shorthand_is_indexed(self, tmp_path):
        # "Inti exiles the top card" cited Inti, Seneschal of the Sun after he was cut
        # (deck 26b); a 6-char comma-head floor kept every short legend name out of
        # the shorthand index.
        got = self._cards(tmp_path, "#: archetype: Inti exiles the top card and lets you play it.\n")
        assert any("Inti" in n for n in got)

    def test_history_cue_does_not_reach_across_a_clause_boundary(self, tmp_path):
        # Deck 66: "…were cut for the aristocrats package. Mayhem stays as SEASONING
        # on (Spider-Islanders, …)" audited clean after Spider-Islanders left — the
        # ±140-char window let "cut" in the PREVIOUS sentence suppress a live citation.
        got = self._cards(tmp_path,
            "#: archetype: Timeline Culler was cut for the package. Mayhem stays as\n"
            "#: archetype: SEASONING on Spider-Islanders here.\n")
        assert "Spider-Islanders" in got

    def test_history_cue_in_the_same_clause_still_suppresses(self, tmp_path):
        # The mirror: a rationale that documents its own swap with the cue ADJACENT
        # (G-27's contract) must stay quiet.
        got = self._cards(tmp_path, "#: archetype: Spider-Islanders was cut for the package.\n")
        assert "Spider-Islanders" not in got

    def test_figures_about_another_deck_do_not_flag(self, tmp_path):
        # 56a quoted its parent's vector — "deck 56 core … interaction 7" — and both
        # numbers flagged as stale against 56a's own vector (two false positives).
        d = self._deck(tmp_path,
            "#: tier: B. CONSISTENT WITH THE PARENT: deck 56 core reads interaction 7\n"
            "#: tier: and holds A at its own floor.\n")
        _cards, figs = deck.rationale_staleness(d)
        assert figs == []

    def test_bare_figures_still_audit(self, tmp_path):
        # The other-deck rule must not swallow the deck's own numbers: this probe deck
        # has interaction 0, so a bare "interaction 7" is a stale figure.
        d = self._deck(tmp_path, "#: tier: B on interaction 7 with real removal.\n")
        _cards, figs = deck.rationale_staleness(d)
        assert any(k == "interaction" for k, _q, _a in figs)

    def test_label_idiom_is_not_shorthand(self, tmp_path):
        # "Down: the manabase is three colours" is the house what-argues-DOWN idiom;
        # with 4-char comma-heads indexed it read as *Down, Down to Goblin-town*
        # (54a, roster sweep). A fragment writing a label is prose structure.
        got = self._cards(tmp_path, "#: tier: B. Down: the manabase is three colours on 25 lands.\n")
        assert not any("Goblin-town" in n for n in got)

    def test_variant_parent_comparison_does_not_flag(self, tmp_path):
        # "Its parent counts CREATURES — Craterhoof's X, Enduring Vitality…" (50a) is
        # variant-comparison vocabulary about the OTHER deck's cards.
        got = self._cards(tmp_path,
            "#: archetype: Its parent counts CREATURES — Enduring Vitality reads the same number.\n")
        assert "Enduring Vitality" not in got


class TestFormatNormalization:
    """Arena renamed these and the repo kept the old names, so the labels are INVERTED
    against the client UI: Arena's "Brawl" is 100-card Historic Brawl, Arena's
    "Standard Brawl" is the 60-card one. `#: format:` is hand-written, so the spellings
    a person reaches for must resolve — `historic-brawl` (a real slug in _FORMAT_SLUGS)
    previously matched NEITHER construction set, silently giving a 100-card singleton
    deck a 60-card floor and no copy limit, with `legal` reporting clean."""

    def test_hyphenated_historic_brawl_gets_the_100_card_floor(self):
        c = deck.normalize_format("historic-brawl")
        assert c in deck.BIG_DECK_FORMATS and c in deck.SINGLETON_FORMATS

    def test_arena_standard_brawl_label_maps_to_the_60_card_format(self):
        c = deck.normalize_format("Standard Brawl")
        assert c == "brawl"
        assert c not in deck.BIG_DECK_FORMATS and c in deck.SINGLETON_FORMATS

    def test_case_and_spacing_are_normalized(self):
        assert deck.normalize_format("  HISTORIC  BRAWL ") == "historic brawl"

    def test_plain_formats_pass_through(self):
        assert deck.normalize_format("Standard") == "standard"
        assert deck.normalize_format("") == ""

    def test_a_100_card_historic_brawl_deck_is_not_flagged_undersized(self, tmp_path):
        cards = [(1, f"Filler {i}", "SET", str(i)) for i in range(99)]
        rep = deck.legality_report({"commander": ""}, cards, "historic-brawl", {})
        assert not any("minimum is 60" in p for p in rep["problems"])
        assert rep["min_size"] == 100 and rep["copy_limit"] == 1
