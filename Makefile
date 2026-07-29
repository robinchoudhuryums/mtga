# Convenience targets. The CORE tooling (validate/enrich/query/deck/pool/build_*)
# is pure standard library and needs none of this — only the optional editing app
# (scripts/app.py) uses Flask, which `make app` installs into a local venv.

VENV  := .venv
PYBIN := $(VENV)/bin/python
ARGS  ?=

.PHONY: help app check test-units verify refresh clean-venv

help:
	@echo "make app             set up a local venv, install Flask, and launch the editor"
	@echo "make app ARGS=...    pass args through, e.g. make app ARGS='--port 8000 --no-browser'"
	@echo "make check           run the integrity gate (no dependencies)"
	@echo "make test-units      run the pytest unit layer (installs requirements-dev.txt)"
	@echo "make verify          BOTH gates: integrity + unit tests (run before committing)"
	@echo "make refresh         rebuild derived data in dependency order (incremental; needs Scryfall)"
	@echo "make refresh REFETCH=1   same, but re-price every card from scratch (slow)"
	@echo "make clean-venv      remove the local .venv"

# Launch the editor. Depends on the venv sentinel so deps install on first run
# (and re-install only when requirements-app.txt changes).
app: $(VENV)/.installed
	$(PYBIN) scripts/app.py $(ARGS)

$(VENV)/.installed: requirements-app.txt
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --quiet --upgrade pip
	$(VENV)/bin/pip install --quiet -r requirements-app.txt
	@touch $@

check:
	python3 scripts/check_all.py

# Fast, isolated unit tests for the pure helper functions (complements `make check`).
test-units:
	python3 -m pip install --quiet -r requirements-dev.txt
	python3 -m pytest

# The pre-commit gate. `make check` alone passes while a unit test is red — the unit
# layer used to run ONLY in CI, so a local cycle could land a change that broke it and
# not find out until push (audit F-16). Run this instead.
verify: check test-units

# The ONE executable definition of the derived-data rebuild order.
#
# The order is a real dependency graph, not a convention, and it was written down in
# THREE places that disagreed: `/refresh` had it right, while CLAUDE.md's Regression
# Scenario 1 and its "Regenerate derived data after imports" gotcha both put
# build_pool.py AFTER build_mana.py. Read from the code instead of the prose:
#
#   enrich.py         reads/writes card-library.csv only
#   build_pool.py     independent — takes keywords straight off the Scryfall response
#   build_mana.py     --pool READS card-pool.csv, so the pool must exist FIRST
#   tag_synergies.py  reads card-mana.csv's keywords, so mana must be built FIRST
#   build_gallery.py  reads card-library.csv, last
#
# Getting it wrong is not loud: with build_pool last, a newly released set's pool cards
# have no card-mana.csv row until the NEXT cycle, so they silently rank with no cost and
# no keyword tags. Three prose copies is three chances to get that wrong; this is one.
#
# Needs Scryfall egress. Each step announces itself so a failure is attributable, and make
# stops at the first non-zero exit rather than running the rest against half-built data.
#
# INCREMENTAL: every step now skips work it has already done — enrich.py fills only blank
# fields, build_gallery.py reuses its image cache, and build_mana.py reuses the rows it has
# already resolved (a printed mana cost does not change). A no-change refresh takes seconds
# and needs no network at all; a four-card ingest fetches four cards. It used to re-price
# all ~15.9k pool cards against the rate limit every single run, ~10 minutes regardless.
#
# `make refresh REFETCH=1` forces the full re-price, for an errata or rebalance sweep. That
# is a FLAG on this one target, not a second target: the order is the thing that must have
# a single definition, and a separate "quick refresh" recipe is how it drifts.
REFETCH ?=

refresh:
	@echo "==> 1/6 enrich.py            (fill blank Type/Text/Color/Collector #)"
	python3 scripts/enrich.py
	@echo "==> 2/6 build_pool.py --all  (full Arena pool; BEFORE build_mana, which reads it)"
	python3 scripts/build_pool.py --all
	@echo "==> 3/6 build_mana.py --pool (costs + keywords; reuses resolved rows)"
	python3 scripts/build_mana.py --pool $(if $(REFETCH),--refetch,)
	@echo "==> 4/6 tag_synergies.py --merge  (keyword-aware tags; --merge keeps hand edits)"
	python3 scripts/tag_synergies.py --merge
	@echo "==> 5/6 build_gallery.py     (gallery.html + images)"
	python3 scripts/build_gallery.py
	@echo "==> 6/6 check_all.py         (invariants)"
	python3 scripts/check_all.py

clean-venv:
	rm -rf $(VENV)
