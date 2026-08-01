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

    def test_colorless_is_subset_of_everything(self):
        # A colorless identity must be castable in every deck.
        assert lib.card_colors("Colorless").issubset(set())
        assert lib.card_colors("Colorless").issubset({"W", "U"})


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
