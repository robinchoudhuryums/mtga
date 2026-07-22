"""Pytest bootstrap: put scripts/ on sys.path so the unit tests can import the
tooling modules (lib, deck, wishlist, …) the same way the scripts import each other.

This unit layer is a COMPLEMENT to `scripts/check_all.py` (the deterministic
integrity + model-sanity gate). check_all stays pure-stdlib and is the primary gate;
these tests pin the edge-case behaviour of the pure helper functions so a refactor
can't silently change them. Run with `pytest` (see requirements-dev.txt) — never
imported by check_all, so the core tooling keeps its zero-dependency guarantee.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
