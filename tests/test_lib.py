"""Unit tests for scripts/lib.py — the shared primitives every tool routes through.

These pin the exact edge cases behind the F1/F2 (color parsing) and F6 (DFC
ownership) fixes, plus the atomic-write safety net, so a refactor can't regress them
without a red test (the static/behavioural check_* gates cover the same ground at
the integration level; this is the fast, isolated layer)."""
import csv

import pytest

import lib


class TestCardColors:
    def test_colorless_is_empty(self):
        # The F1 trap: "Colorless" contains an R, so a naive parse read it as {'R'}.
        assert lib.card_colors("Colorless") == set()

    def test_slash_gold(self):
        assert lib.card_colors("B/G") == {"B", "G"}

    def test_five_color(self):
        assert lib.card_colors("W/U/B/R/G") == set("WUBRG")

    def test_mono(self):
        assert lib.card_colors("U") == {"U"}

    def test_blank_and_none(self):
        assert lib.card_colors("") == set()
        assert lib.card_colors(None) == set()


class TestColorMatches:
    """The --color FILTER primitive (broad-scan BS-10). Its predecessor was a raw
    substring test in query/pool/wishlist, so `--color R` matched every Colorless
    card ("r" in "colorless" — the F1 trap as a filter)."""

    def test_colorless_card_does_not_match_R(self):
        assert not lib.color_matches("Colorless", "R")

    def test_gold_card_matches_either_color(self):
        assert lib.color_matches("B/R", "R")
        assert lib.color_matches("B/R", "B")

    def test_multi_letter_needle_requires_all(self):
        assert lib.color_matches("B/R", "BR")
        assert not lib.color_matches("B/R", "BRW")

    def test_colorless_needle_matches_only_colorless(self):
        assert lib.color_matches("Colorless", "colorless")
        assert not lib.color_matches("B", "colorless")

    def test_no_needle_is_no_filter(self):
        assert lib.color_matches("B", None)
        assert lib.color_matches("Colorless", "")

    def test_colorless_is_subset_of_everything(self):
        # A colorless identity must be castable in every deck.
        assert lib.card_colors("Colorless").issubset(set())
        assert lib.card_colors("Colorless").issubset({"W", "U"})


class TestColorWithin:
    """The --within SUBSET filter (DD-4) — "castable in a deck of these colors", the
    from-scratch draft survey question color_matches' superset semantics cannot ask:
    `--color WRG` returned five-color cards on both 2026-08-21 drafts."""

    def test_five_color_card_does_not_fit_naya(self):
        assert not lib.color_within("W/U/B/R/G", "WRG")

    def test_mono_and_guild_cards_fit_their_shard(self):
        assert lib.color_within("R", "WRG")
        assert lib.color_within("W/R", "WRG")
        assert lib.color_within("W/R/G", "WRG")

    def test_off_color_card_does_not_fit(self):
        assert not lib.color_within("U", "WRG")
        assert not lib.color_within("B/G", "WRG")

    def test_colorless_fits_any_deck(self):
        assert lib.color_within("Colorless", "WRG")
        assert lib.color_within("Colorless", "U")

    def test_the_naive_substring_trap_stays_dead(self):
        # "colorless" contains the letter r — set semantics, never substring (BS-10).
        assert lib.color_within("Colorless", "R")
        assert not lib.color_within("R", "colorless")

    def test_no_needle_is_no_filter(self):
        assert lib.color_within("B/R", None)
        assert lib.color_within("B/R", "")


class TestOwnedQty:
    IDX = {"fable of the mirror-breaker": 2, "llanowar elves": 4}

    def test_dfc_resolves_by_front_face(self):
        # Library keys a DFC under its front name; the pool/wishlist pass the full name.
        assert lib.owned_qty(self.IDX, "Fable of the Mirror-Breaker // Reflection of Kiki-Rikki") == 2

    def test_plain_front_name(self):
        assert lib.owned_qty(self.IDX, "Llanowar Elves") == 4

    def test_unowned_is_zero_not_none(self):
        assert lib.owned_qty(self.IDX, "Nonexistent Card") == 0

    def test_case_insensitive(self):
        assert lib.owned_qty(self.IDX, "LLANOWAR ELVES") == 4

    def test_deck_owned_helper_resolves_a_dfc_by_front_face(self):
        """deck.owned() must resolve a FULL `A // B` deck line to the library's front name.

        Regression: deck.owned() did a bare dict lookup and returned "not in library",
        allow-listed in check_dfc.py on the claim that deck-file names are always
        front-face. `deck.py resolve` falsifies that — it emits the full name, because
        that is how the pool keys a DFC and how Arena exports one — so a deck built by
        resolve reported its own OWNED double-faced card as missing (deck 45a said it
        about Norman Osborn) while lib.owned_qty had it right all along.
        """
        import deck
        qty, found = deck.owned(self.IDX, "Fable of the Mirror-Breaker // Reflection of Kiki-Rikki")
        assert (qty, found) == (2, True)
        # and the plain / unowned paths still behave
        assert deck.owned(self.IDX, "Llanowar Elves") == (4, True)
        assert deck.owned(self.IDX, "Nonexistent Card") == (0, False)


class TestBackupPath:
    def test_sortable_and_unique(self):
        a = lib.backup_path("/tmp/x.csv")
        assert a.startswith("/tmp/x.csv.") and a.endswith(".bak")

    def test_collision_suffix_sorts_after(self, tmp_path):
        # A same-timestamp collision must get a suffix that sorts AFTER the base name
        # (audit F22), so "newest by name" stays correct.
        target = str(tmp_path / "x")
        base = lib.backup_path(target)
        open(base, "w").close()
        # Force the collision path by reusing the same stamp portion.
        stamp = base[len(target) + 1:-4]
        collide = f"{target}.{stamp}.bak"
        assert collide == base  # sanity: we reconstructed the exact name
        nxt = lib.backup_path(target)
        # a fresh call returns a name >= the existing one lexically (monotonic)
        assert nxt >= base


class TestAtomicWrite:
    def test_writes_and_backs_up(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("original\n", encoding="utf-8")
        lib.atomic_write(str(p), lambda fh: fh.write("new\n"))
        assert p.read_text(encoding="utf-8") == "new\n"
        baks = list(tmp_path.glob("data.csv.*.bak"))
        assert len(baks) == 1 and baks[0].read_text(encoding="utf-8") == "original\n"

    def test_no_backup_flag(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("original\n", encoding="utf-8")
        lib.atomic_write(str(p), lambda fh: fh.write("new\n"), backup=False)
        assert not list(tmp_path.glob("data.csv.*.bak"))

    def test_failed_write_leaves_original(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("original\n", encoding="utf-8")

        def boom(fh):
            raise RuntimeError("mid-write failure")

        try:
            lib.atomic_write(str(p), boom)
        except RuntimeError:
            pass
        assert p.read_text(encoding="utf-8") == "original\n"  # untouched
        assert not list(tmp_path.glob("*.tmp"))  # temp cleaned up


class TestDistinctiveness:
    # A small hand-built pool model: idf per tag, the tribe-tag set, and pool size.
    IDF = {"etb": 1.6, "tokens": 1.7, "sacrifice": 2.0, "landcycling": 7.0,
           "Case": 7.2, "Human": 1.9, "Bear": 6.0}
    TRIBES = {"Human", "Bear"}
    N = 15000

    def score(self, tags):
        return lib.distinctiveness_score(tags, self.IDF, self.TRIBES, self.N)

    def test_vanilla_tribe_only_is_zero(self):
        # Grizzly Bears: a bare creature type is identity, not a distinctive ability.
        assert self.score(["Bear"]) == 0.0

    def test_evergreen_only_is_zero(self):
        # A french-vanilla body (only an evergreen keyword) has no distinctive ability.
        assert self.score(["flying", "trample"]) == 0.0

    def test_empty_is_zero(self):
        assert self.score([]) == 0.0

    def test_rare_mechanic_outscores_generic(self):
        generic = self.score(["etb", "tokens"])
        rare = self.score(["landcycling", "etb"])
        assert 0.0 < generic < rare <= 10.0

    def test_rarest_two_drive_the_score(self):
        # Adding a common tag to a card that already has a rare one shouldn't dilute it
        # much — the top-2 mean is driven by the rarest abilities, not the average.
        just_rare = self.score(["landcycling", "Case"])
        with_filler = self.score(["landcycling", "Case", "etb", "tokens", "sacrifice"])
        assert with_filler == just_rare  # top-2 unchanged by generic filler

    def test_tribe_excluded_from_ability_score(self):
        # A rare TRIBE (Bear idf 6.0) must NOT count as a distinctive ability — only the
        # mechanic tags do, so this scores off 'etb' alone, not off 'Bear'.
        assert self.score(["Bear", "etb"]) == self.score(["etb"])

    def test_bounds_and_empty_model(self):
        for tags in (["landcycling"], ["Case", "etb"], ["etb"]):
            assert 0.0 <= self.score(tags) <= 10.0
        # No pool model → neutral 0.0, never a crash.
        assert lib.distinctiveness_score(["landcycling"], {}, set(), 0) == 0.0


class TestStructuralDistinctiveness:
    """The oracle-text-shape signal that rescues cards the tag metric mis-reads."""

    def test_vanilla_and_keyword_only_low(self):
        assert lib.structural_distinctiveness("") == 0.0
        assert lib.structural_distinctiveness("Trample") <= 1.0

    def test_plain_etb_stays_low(self):
        # A plain ETB token/lifegain body is generic — the enters-lookahead skips it.
        assert lib.structural_distinctiveness(
            "When this creature enters, create a 1/1 white Soldier creature token.") <= 2.0
        assert lib.structural_distinctiveness(
            "When this creature enters, you gain 3 life.") <= 2.0

    def test_bare_mana_ability_excluded(self):
        # A mana dork's "{T}: Add {G}" is generic, not a distinctive activated ability.
        assert lib.structural_distinctiveness("{T}: Add {G}.") <= 1.0

    def test_unusual_trigger_scores_high(self):
        rich = lib.structural_distinctiveness(
            "When this creature dies, destroy target permanent and return target "
            "nonlegendary permanent card from your graveyard to the battlefield.")
        plain = lib.structural_distinctiveness(
            "When this creature enters, create a 1/1 token.")
        assert rich > plain and rich >= 4.0

    def test_copy_engine_scores_high(self):
        # Thousand-Year Storm's shape: a "whenever you cast" trigger + a copy effect.
        assert lib.structural_distinctiveness(
            "Whenever you cast an instant or sorcery spell, copy it for each spell "
            "cast before it this turn.") >= 4.0

    def test_real_activated_ability_counts(self):
        assert lib.structural_distinctiveness(
            "{2}, {T}, Sacrifice this artifact: Draw a card.") >= 3.0

    def test_bounds(self):
        for txt in ("", "Flying", "{T}: Add {C}.",
                    "Whenever you cast a spell, draw a card. Choose one — instead you may "
                    "search your library. As long as you control it, spells cost less."):
            assert 0.0 <= lib.structural_distinctiveness(txt) <= 10.0


class TestCardDistinctivenessMax:
    """card_distinctiveness takes the MAX of tag-rarity and structural — only RAISES."""

    def test_text_omitted_is_tag_only(self):
        # Backward-compatible: no text → tag-only score (structural term is 0).
        assert lib.card_distinctiveness(["Bear"]) == lib.card_distinctiveness(["Bear"], "")

    def test_structural_rescues_mistagged(self):
        rescue_text = ("When this creature dies, destroy target permanent and return "
                       "target card from your graveyard to the battlefield.")
        tag_only = lib.card_distinctiveness(["etb", "tokens"], "")
        combined = lib.card_distinctiveness(["etb", "tokens"], rescue_text)
        assert combined >= 4.0 and combined >= tag_only

    def test_never_lowers(self):
        # Whatever the structure, the combined score is >= the tag-only score.
        for text in ("", "Flying", "{T}: Add {G}."):
            assert (lib.card_distinctiveness(["landcycling", "etb"], text)
                    >= lib.card_distinctiveness(["landcycling", "etb"], ""))


class TestCreatureSubtypes:
    def test_creature_line_yields_tribes(self):
        assert lib._creature_subtypes("Creature — Human Warrior") == {"Human", "Warrior"}

    def test_noncreature_subtype_excluded(self):
        # Equipment/Aura are mechanics we WANT to keep as ability tags, so the tribe set
        # must not swallow them (only Creature-line subtypes are tribes).
        assert lib._creature_subtypes("Artifact — Equipment") == set()
        assert lib._creature_subtypes("Enchantment — Aura") == set()

    def test_dfc_both_faces(self):
        got = lib._creature_subtypes("Creature — Elf Druid // Creature — Beast")
        assert got == {"Elf", "Druid", "Beast"}


class TestWriteRows:
    def test_roundtrip_canonical_header(self, tmp_path):
        p = tmp_path / "lib.csv"
        rows = [{"Card Name": "Shock", "Type": "Instant", "Card Text": "Deal 2",
                 "Color(s)": "R", "Synergies": "burn", "Set Code": "M19",
                 "Collector #": "156", "Quantity Owned": "4", "StrayKey": "ignored"}]
        lib.write_rows(rows, str(p))
        with open(p, newline="", encoding="utf-8") as fh:
            got = list(csv.DictReader(fh))
        assert got[0]["Card Name"] == "Shock"
        assert "StrayKey" not in got[0]  # only canonical columns emitted
        assert list(got[0].keys()) == lib.HEADER

    def test_refuses_a_derived_file(self, tmp_path):
        # A pool-shaped CSV must not be rewritten with the 8 library columns — that
        # silently drops Rarity / Legalities / Released (audit F-02).
        p = tmp_path / "card-pool.csv"
        p.write_text("Card Name,Type,Card Text,Color(s),Synergies,Set Code,"
                     "Collector #,Rarity,Legalities,Released\nShock,Instant,,R,burn,"
                     "M19,156,Common,standard,2018-07-13\n", encoding="utf-8")
        assert lib.csv_schema_error(str(p))
        with pytest.raises(lib.WrongSchema):
            lib.write_rows([{"Card Name": "Shock"}], str(p))
        # ...and the file is untouched.
        assert "Legalities" in p.read_text(encoding="utf-8").splitlines()[0]

    def test_allows_missing_empty_and_matching_targets(self, tmp_path):
        missing = tmp_path / "new.csv"
        assert lib.csv_schema_error(str(missing)) is None
        empty = tmp_path / "empty.csv"
        empty.write_text("", encoding="utf-8")
        assert lib.csv_schema_error(str(empty)) is None      # a fresh mkstemp target
        matching = tmp_path / "lib.csv"
        matching.write_text(",".join(lib.HEADER) + "\n", encoding="utf-8")
        assert lib.csv_schema_error(str(matching)) is None


class TestCardPower:
    """Magic prints `*`, `1+*`, `X` as often as `4`; coercing those would invent facts."""

    def test_numeric(self):
        assert lib.card_power("4") == 4
        assert lib.card_power(0) == 0
        assert lib.card_power(" 7 ") == 7

    def test_non_numeric_is_none(self):
        for v in ("*", "1+*", "X", "∞", "*+1", ""):
            assert lib.card_power(v) is None, v

    def test_none_and_missing(self):
        assert lib.card_power(None) is None


class TestPrimaryTypeHasOneDefinition:
    """`build_gallery.py` carried its own copy of `_primary_type` with the identical
    back-face bug, and it went on mis-typing the gallery's breakdown for as long as the
    copy existed — a fix applied to one definition cannot reach the other. The wiring is
    the half a pure-function test structurally cannot see (the recurring failure shape
    here), so this asserts both callers resolve to lib's object, not merely that they
    agree today."""

    def test_deck_and_gallery_both_use_libs_definition(self):
        import deck
        import build_gallery
        assert deck._primary_type is lib.primary_type
        assert build_gallery._primary_type is lib.primary_type

    def test_the_back_face_never_decides_the_type(self):
        assert lib.primary_type("Legendary Creature — God // Land") == "Creature"
        assert lib.primary_type("Legendary Artifact // Legendary Artifact Land") == "Artifact"

    def test_a_real_land_front_is_still_a_land(self):
        assert lib.primary_type("Land — Town // Sorcery — Adventure") == "Land"

    def test_missing_and_empty(self):
        assert lib.primary_type("") == "Other"
        assert lib.primary_type(None) == "Other"


class TestBackupSelection:
    """`backup_path` writes a creation-ordered name; `latest_backup` reads it back.

    They are two halves of one scheme and must agree, because the obvious reader —
    `max(..., key=getmtime)` — is WRONG for a file made by `shutil.copy2`: copy2 copies
    the SOURCE's mtime, so a `.bak`'s mtime is when its contents were written, not when
    the backup was taken. The two orders diverge the moment anything restores an old
    file, which is exactly what `app.py`'s revert does (broad-scan F-04)."""

    def test_stamp_parses_with_and_without_the_collision_counter(self):
        assert lib.backup_stamp("card-library.csv.20260731-225802-123456.bak") == \
            ("20260731-225802-123456", "")
        assert lib.backup_stamp("card-library.csv.20260731-225802-1234560001.bak") == \
            ("20260731-225802-123456", "0001")

    def test_a_name_outside_the_scheme_has_no_stamp(self):
        assert lib.backup_stamp("card-library.csv.2026-07-31.bak") is None
        assert lib.backup_stamp("") is None

    def test_newest_is_by_creation_stamp(self):
        assert lib.latest_backup([
            "x.20260731-225802-000001.bak",
            "x.20260731-225802-000002.bak",
            "x.20260731-225801-999999.bak"]) == "x.20260731-225802-000002.bak"

    def test_the_collision_counter_sorts_after_its_base(self):
        # backup_path places the counter so it still sorts AFTER the collision-free name.
        assert lib.latest_backup([
            "x.20260731-225802-000001.bak",
            "x.20260731-225802-0000010001.bak"]) == "x.20260731-225802-0000010001.bak"

    def test_a_stamped_name_beats_an_unstamped_one(self):
        assert lib.latest_backup(
            ["x.legacy.bak", "x.20260731-225802-000001.bak"]) == "x.20260731-225802-000001.bak"

    def test_empty_returns_none(self):
        assert lib.latest_backup([]) is None
        assert lib.latest_backup(None) is None

    def test_revert_save_revert_restores_the_pre_save_state(self, tmp_path):
        """The end-to-end sequence that made mtime selection wrong. Under the old
        `max(..., key=getmtime)` the second revert restored the state the FIRST revert had
        already discarded — silently re-applying the change the user just undid."""
        import os
        import shutil
        target = tmp_path / "lib.csv"
        target.write_text("v0\n")

        def save(v):
            shutil.copy2(target, lib.backup_path(str(target)))
            target.write_text(f"v{v}\n")

        def revert():
            baks = [str(p) for p in tmp_path.iterdir() if p.name.endswith(".bak")]
            newest = lib.latest_backup(baks)
            shutil.copy2(target, lib.backup_path(str(target)))   # revert is itself undoable
            shutil.copy2(newest, target)

        save(1)
        save(2)
        revert()
        assert target.read_text() == "v1\n"
        save(3)
        revert()
        assert target.read_text() == "v1\n"      # the pre-save-3 state, not the discarded v2
        assert os.path.exists(target)


class TestOwnedQtyExplicitZero:
    """BS4-19: `index.get(nl) or index.get(front, 0)` treated a stored count of a real 0
    as ABSENT and fell through to the front-face key. `import_collection --zero-missing`
    writes exactly that, and INV-01 permits it. `card_power` in the same file documents
    this trap for a printed power of 0; quantity had not had the lesson applied."""

    def test_an_explicit_zero_is_returned_not_treated_as_missing(self):
        idx = {"life // death": 0, "life": 4}
        # The full name says you own NONE. Falling through would answer 4 — a different
        # card's count.
        assert lib.owned_qty(idx, "Life // Death") == 0

    def test_the_front_fallback_still_works_when_the_full_name_is_absent(self):
        assert lib.owned_qty({"life": 3}, "Life // Death") == 3

    def test_a_missing_card_is_zero(self):
        assert lib.owned_qty({}, "Nonesuch") == 0

    def test_a_real_count_is_unchanged(self):
        assert lib.owned_qty({"shock": 4}, "Shock") == 4


class TestPoolAbilityModelCacheIsKeyed:
    """BS6-08. It memoized on a bare `if _cache:`, so the FIRST call won permanently —
    a pool rebuilt inside a long-lived process served the old model, and a first call
    made before the pool existed pinned the EMPTY model for the life of the process.
    That second case is a silent degradation: `card_distinctiveness` falls back to the
    structural term alone and `cuts`' Uq co-signal flattens with nothing printed."""

    def test_the_live_model_is_populated(self):
        _idf, _tribes, n = lib.pool_ability_model()
        assert n > 0, "no pool — the rest of this class cannot distinguish cache from data"

    def test_repointing_the_pool_invalidates(self, monkeypatch):
        before = lib.pool_ability_model()[2]
        monkeypatch.setattr(lib, "_POOL_CSV", "/nonexistent/card-pool.csv")
        assert lib.pool_ability_model()[2] == 0, "stale model served after the file moved"
        monkeypatch.undo()
        assert lib.pool_ability_model()[2] == before

    def test_cache_clear_is_exposed(self):
        lib.pool_ability_model.cache_clear()
        assert lib.pool_ability_model()[2] > 0

class TestCollectionStamp:
    """The freshness stamp behind `lib.collection_stamp_note` — the fact the CSVs
    cannot hold (WHEN counts were last exact; mtime lies per F-04). Three states:
    never reconciled, stale, fresh."""

    def test_absent_stamp_says_never_reconciled(self, tmp_path):
        note = lib.collection_stamp_note(path=str(tmp_path / "none.json"))
        assert note and "never been exactly reconciled" in note

    def test_fresh_stamp_is_silent(self, tmp_path):
        p = str(tmp_path / "s.json")
        lib.write_collection_stamp(2500, path=p)
        assert lib.collection_stamp_note(path=p) is None

    def test_old_stamp_names_its_age(self, tmp_path):
        import datetime as dt, json
        p = tmp_path / "s.json"
        old = (dt.date.today() - dt.timedelta(days=45)).isoformat()
        p.write_text(json.dumps({"reconciled": old, "rows": 1, "tool": "t"}),
                     encoding="utf-8")
        note = lib.collection_stamp_note(path=str(p))
        assert note and "45 days ago" in note

    def test_a_corrupt_stamp_degrades_to_never(self, tmp_path):
        p = tmp_path / "s.json"
        p.write_text("{not json", encoding="utf-8")
        note = lib.collection_stamp_note(path=str(p))
        assert note and "never been exactly reconciled" in note



class TestLandProduction:
    """`lib.land_production` (BS8-01/02): what a land PRODUCES, from its text — the one
    reader behind every colour-source count and the manabase recommender."""

    def test_any_colour_no_extra_cost_is_free_in_all_five(self):
        p = lib.land_production("{T}: Add one mana of any color.", "Colorless")
        assert p["free"] == set("WUBRG") and p["any"] and not p["conditional"]

    def test_extra_mana_cost_is_conditional_not_free(self):
        p = lib.land_production("{T}: Add {C}.\n{1}, {T}: Add one mana of any color.",
                                "Colorless")
        assert p["free"] == set() and p["conditional"] == set("WUBRG") and p["any"]

    def test_spend_only_is_restricted_and_identity_cannot_launder_it(self):
        p = lib.land_production(
            "{T}: Add {C}.\n{T}: Add {B}. Spend this mana only to cast a creature spell.", "B")
        assert p["restricted"] == {"B"} and "B" not in p["free"]

    def test_paying_life_is_a_real_source(self):
        p = lib.land_production("{T}, Pay 1 life: Add one mana of any color.", "Colorless")
        assert p["free"] == set("WUBRG")

    def test_basic_fetch_is_flagged_and_produces_nothing_itself(self):
        p = lib.land_production("{T}, Sacrifice this land: Search your library for a basic "
                                "land card, put it onto the battlefield tapped, then shuffle.",
                                "Colorless")
        assert p["fetch"] and p["free"] == set() and not p["any"]

    def test_reminder_text_does_not_make_a_treasure_maker_a_rainbow_land(self):
        p = lib.land_production("{T}: Add {G}.\n{2}, {T}: Create a Treasure token. (It's an "
                                "artifact with \"{T}, Sacrifice this artifact: Add one mana "
                                "of any color.\")", "G")
        assert p["free"] == {"G"} and not p["any"]

    def test_identity_is_the_fallback_for_blank_text(self):
        assert lib.land_production("", "R/G")["free"] == {"R", "G"}

class TestLandProductionExclusions:
    """Four shapes that reported FIVE FREE COLOURS for a land producing little or nothing.
    All four surfaced on 2026-09-04 when a breadth-aware term was added to
    `wishlist._land_value`: the term is correct, and it promoted these lands to the top of
    dozens of decks' suggestions because the primitive underneath was wrong. `free` feeds
    `deck_source_profile` as well as the recommender, so each of these was also a latent
    over-count of a deck's colour sources."""

    def test_choose_once_on_entry_is_marked_but_still_counted(self):
        """"As it enters, choose a color" supplies exactly ONE colour per game. It stays in
        `free` because for ACCESS it really is a source of whichever colour you name — the
        same generosity a fetch gets — but `chosen` lets a breadth score decline to credit
        colours it can never produce simultaneously."""
        p = lib.land_production(
            "This land enters tapped. As it enters, choose a color.\n"
            "{T}: Add one mana of the chosen color.", "Colorless")
        assert p["free"] == set("WUBRG")
        assert p["chosen"] == set("WUBRG")

    def test_a_true_any_colour_land_is_not_marked_chosen(self):
        """Starting Town produces any colour on EVERY tap; it must keep full breadth."""
        p = lib.land_production("{T}: Add {C}.\n{T}, Pay 1 life: Add one mana of any color.",
                                "Colorless")
        assert p["free"] == set("WUBRG") and p["chosen"] == set()

    def test_production_reachable_only_by_transforming_is_not_production(self):
        """Branch of Vitu-Ghazi taps for {C}; its "add two mana of any one color" line
        fires only when the card is turned face up via Disguise. It scored the maximum
        10.0 in `suggest --lands` and rose to #1 in dozens of decks."""
        p = lib.land_production(
            "{T}: Add {C}.\n"
            "When this land is turned face up, add two mana of any one color.", "Colorless")
        assert p["free"] == set() and p["chosen"] == set()

    def test_an_ability_granted_to_other_permanents_is_not_this_lands_production(self):
        """Forgotten Monument gives the any-colour ability to OTHER Caves. Whether those
        are in the deck is a different question this function is not asked."""
        p = lib.land_production(
            '{T}: Add {C}.\n'
            'Other Caves you control have "{T}, Pay 1 life: Add one mana of any color."',
            "Colorless")
        assert p["free"] == set()

    def test_an_extra_non_mana_tap_cost_is_conditional_not_free(self):
        """Scene of the Crime's any-colour ability costs "Tap an untapped creature you
        control" — an extra body, the non-mana sibling of an extra mana symbol."""
        p = lib.land_production(
            "This land enters tapped.\n{T}: Add {C}.\n"
            "{T}, Tap an untapped creature you control: Add one mana of any color.",
            "Colorless")
        assert p["free"] == set() and p["conditional"] == set("WUBRG")

    def test_the_ordinary_cases_are_untouched(self):
        """The guard rails: a plain tri-land, a dual and a fetch must read as before."""
        tri = lib.land_production("This land enters tapped.\n{T}: Add {U}, {R}, or {W}.", "")
        assert tri["free"] == {"U", "R", "W"} and tri["chosen"] == set()
        fetch = lib.land_production(
            "{T}, Sacrifice this land: Search your library for a basic land card, put it "
            "onto the battlefield tapped, then shuffle.", "")
        assert fetch["fetch"] is True
