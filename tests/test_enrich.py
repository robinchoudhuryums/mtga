"""Behavioral coverage for scripts/enrich.py — a canonical-library WRITER that was
untested beyond --help (BS-20/batch 6). Scryfall is faked at `resolve_cards`; the
schema guard, the needs() queueing rules, the write path, and the clean-abort
contract are the real code."""
import csv
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import enrich as en  # noqa: E402
from lib import HEADER  # noqa: E402
from scryfall import ScryfallUnavailable  # noqa: E402


def _write_lib(tmp_path, rows, header=None):
    p = tmp_path / "lib.csv"
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header or HEADER)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in (header or HEADER)})
    return str(p)


def _read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _card(name, type_line="Instant", text="Card text.", colors=None):
    return {"name": name, "type_line": type_line, "oracle_text": text,
            "colors": colors or ["R"], "set": "m21", "collector_number": "9"}


class TestSchemaGuard:
    def test_refuses_a_derived_file(self, tmp_path, capsys):
        """The F-02 pin: pointing a library writer at a pool-shaped file would
        rewrite it with the 8 library columns, destroying Rarity/Legalities —
        enrich must refuse BEFORE any Scryfall traffic."""
        pool_hdr = HEADER[:-1] + ["Rarity", "Legalities"]
        p = _write_lib(tmp_path, [], header=pool_hdr)
        assert en.enrich(p) == 1
        assert "Refusing" in capsys.readouterr().err
        assert [r for r in _read(p)] == []          # untouched


class TestQueueing:
    def test_blank_fields_are_filled_from_the_resolver(self, tmp_path, monkeypatch):
        p = _write_lib(tmp_path, [{"Card Name": "Shock", "Set Code": "M21",
                                   "Quantity Owned": "1"}])
        monkeypatch.setattr(en, "resolve_cards",
                            lambda names: {"shock": _card("Shock")})
        assert en.enrich(p) == 0
        row = _read(p)[0]
        assert row["Type"] == "Instant" and row["Card Text"] == "Card text."

    def test_an_enriched_vanilla_is_not_requeued_forever(self, tmp_path, monkeypatch, capsys):
        """The F-11 pin: blank Card Text with Type AND Color(s) present is a
        genuine vanilla (Aegis Turtle) — requeueing it meant 'Nothing to enrich'
        was permanently unreachable."""
        p = _write_lib(tmp_path, [{"Card Name": "Aegis Turtle",
                                   "Type": "Creature — Turtle", "Color(s)": "U",
                                   "Set Code": "M21", "Collector #": "1",
                                   "Quantity Owned": "1"}])
        called = []
        monkeypatch.setattr(en, "resolve_cards", lambda names: called.append(names) or {})
        assert en.enrich(p) == 0
        assert called == []                          # nothing queued at all
        assert "Nothing to enrich" in capsys.readouterr().out

    def test_hand_curated_synergies_survive(self, tmp_path, monkeypatch):
        """Synergies is not a FILLABLE column — an enrich pass must never clobber
        hand-curated tags (the --merge/--force discipline lives in tag_synergies)."""
        p = _write_lib(tmp_path, [{"Card Name": "Shock", "Synergies": "burn;spice",
                                   "Set Code": "M21", "Quantity Owned": "1"}])
        monkeypatch.setattr(en, "resolve_cards", lambda names: {"shock": _card("Shock")})
        en.enrich(p)
        assert _read(p)[0]["Synergies"] == "burn;spice"


class TestOutage:
    def test_unreachable_scryfall_aborts_cleanly(self, tmp_path, monkeypatch, capsys):
        """G-14's contract: a rebuild script fails CLEANLY rather than writing a
        partial-blank file over good data."""
        p = _write_lib(tmp_path, [{"Card Name": "Shock", "Set Code": "M21",
                                   "Quantity Owned": "1"}])
        before = open(p, encoding="utf-8").read()
        def _down(names):
            raise ScryfallUnavailable("timed out")
        monkeypatch.setattr(en, "resolve_cards", _down)
        assert en.enrich(p) == 1
        assert open(p, encoding="utf-8").read() == before
        assert "could not reach Scryfall" in capsys.readouterr().err

    def test_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        p = _write_lib(tmp_path, [{"Card Name": "Shock", "Set Code": "M21",
                                   "Quantity Owned": "1"}])
        before = open(p, encoding="utf-8").read()
        monkeypatch.setattr(en, "resolve_cards", lambda names: {"shock": _card("Shock")})
        en.enrich(p, dry_run=True)
        assert open(p, encoding="utf-8").read() == before
