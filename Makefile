# Convenience targets. The CORE tooling (validate/enrich/query/deck/pool/build_*)
# is pure standard library and needs none of this — only the optional editing app
# (scripts/app.py) uses Flask, which `make app` installs into a local venv.

VENV  := .venv
PYBIN := $(VENV)/bin/python
ARGS  ?=

.PHONY: help app check test-units verify refresh dashboard postedit clean-venv

help:
	@echo "make app             set up a local venv, install Flask, and launch the editor"
	@echo "make app ARGS=...    pass args through, e.g. make app ARGS='--port 8000 --no-browser'"
	@echo "make check           run the integrity gate (no dependencies)"
	@echo "make test-units      run the pytest unit layer (installs requirements-dev.txt)"
	@echo "make verify          BOTH gates: integrity + unit tests (run before committing)"
	@echo "make refresh         rebuild derived data in dependency order (incremental; needs Scryfall)"
	@echo "make refresh REFETCH=1   same, but re-price every card from scratch (slow)"
	@echo "make dashboard       rebuild the committed dashboard.html (offline, ~2 min; pages.yml also rebuilds it on every push to main)"
	@echo "make postedit        the after-every-deck-edit tail: re-baseline roles, rebuild dashboard, run the gate"
	@echo "make matches         extract Arena match results from Player.log (run on the Arena machine)"
	@echo "make matches APPLY=1 same, but write them into matches.csv"
	@echo "make log-match DECK=49 R=W [OPP=mono-red WHY=flood PLAY=play NOTE=...]  hand-log one match"
	@echo "make log-match ... APPLY=1   same, but write it (dry run otherwise)"
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
# INCREMENTAL: every step skips work it has already done — enrich.py fills only blank
# fields, build_gallery.py reuses its image cache, build_mana.py reuses the rows it has
# already resolved (a printed mana cost does not change), and build_pool.py reuses a pool
# built within the last week for the same query. A no-change refresh is ~13s — nearly all of
# it the check_all step at the end — and needs no network at all; a four-card ingest fetches
# four cards. It used to cost ~5 minutes every single run regardless, 99% of that the pool's
# 91 paginated pages at ~2.4s each.
#
# Skipping the pool is correct, not merely fast: card-pool.csv is the whole Arena pool and
# is INDEPENDENT of what you own, so an ingest cannot change it. What does go stale is
# Legalities (rotation, bans, rebalances) and the arrival of a new set — hence a time
# window, not a blanket reuse.
#
# `make refresh REFETCH=1` forces both fetches, for an errata/rebalance sweep or a new set.
# That is a FLAG on this one target, not a second target: the order is the thing that must
# have a single definition, and a separate "quick refresh" recipe is how it drifts.
REFETCH ?=

# Pull match results out of Arena's Player.log. Run this ON THE MACHINE RUNNING ARENA.
# The grep is the whole trick and the two lines AROUND the result JSON are load-bearing
# (G-57): `finalMatchResult` carries the outcome but NOT which seat is yours — only the
# `Match to <userId>:` prefix does — and the deck you played is in `EventSetDeckV3`. A
# paste missing either is unparseable, and the parser SKIPS rather than guessing.
# The sed drops the deck card lists, which are 92% of an EventSetDeckV3 line.
# Needs Arena → Settings → Account → "Detailed Logs (Plugin Support)", then a restart.
# PREREQUISITE THIS TARGET CANNOT CHECK: the Arena machine must have this repo cloned.
# It often does not — Arena on a Mac, the repo only ever opened in Claude sessions — and
# then this target does not exist to run. `/log-matches` carries a ~/.zshrc function that
# needs no checkout; that is the right shortcut for that setup.
MTGA_LOGS ?= $(HOME)/Library/Logs/Wizards Of The Coast/MTGA
MATCHES_OUT ?= /tmp/mtga-matches.log
matches:
	@echo "==> reading $(MTGA_LOGS)"
	@grep -hE 'Match to .*MatchGameRoomStateChangedEvent|"finalMatchResult"|==> EventSetDeckV3' \
	    "$(MTGA_LOGS)"/Player*.log \
	  | sed -E 's/\\"(MainDeck|Sideboard)\\":\[[^]]*\]/\\"\1\\":[]/g' > $(MATCHES_OUT)
	@echo "==> wrote $(MATCHES_OUT) ($$(wc -l < $(MATCHES_OUT)) lines)"
	python3 scripts/parse_matches.py $(MATCHES_OUT) $(if $(APPLY),--apply,)
	@$(if $(APPLY),,echo "";echo "DRY RUN — nothing written. Re-run with: make matches APPLY=1")

# Hand-log ONE match — a phone game, or anything Player.log cannot see (the opponent's
# archetype, play/draw, why you lost). For a whole session use the dashboard's "Log a
# match" panel, which queues on your phone and hands back these same lines in a block.
# Dry run unless APPLY=1, like every other writer here.
log-match:
	@test -n "$(DECK)" || { echo "usage: make log-match DECK=<id> R=<W|L|D> [OPP=… WHY=… PLAY=play|draw NOTE=…] [APPLY=1]"; exit 2; }
	@test -n "$(R)" || { echo "R= is required (W, L or D)"; exit 2; }
	@printf '%s %s%s%s%s%s\n' "$(DECK)" "$(R)" \
	  "$(if $(OPP), opp=\"$(OPP)\",)" "$(if $(WHY), why=$(WHY),)" \
	  "$(if $(PLAY), play=$(PLAY),)" "$(if $(NOTE), note=\"$(NOTE)\",)" \
	  | python3 scripts/parse_matches.py - --add $(if $(APPLY),--apply,)

refresh:
	@echo "==> 1/6 enrich.py            (fill blank Type/Text/Color/Collector #)"
	python3 scripts/enrich.py
	@echo "==> 2/6 build_pool.py --all  (full Arena pool; BEFORE build_mana, which reads it)"
	python3 scripts/build_pool.py --all $(if $(REFETCH),--refetch,)
	@echo "==> 3/6 build_mana.py --pool (costs + keywords; reuses resolved rows)"
	python3 scripts/build_mana.py --pool $(if $(REFETCH),--refetch,)
	@echo "==> 4/6 tag_synergies.py --merge  (keyword-aware tags; --merge keeps hand edits)"
	python3 scripts/tag_synergies.py --merge
	@echo "==> 5/6 build_gallery.py     (gallery.html + images)"
	python3 scripts/build_gallery.py
	@echo "==> 6/6 check_all.py         (invariants)"
	python3 scripts/check_all.py
	@echo "NOTE: dashboard.html is NOT rebuilt by refresh (it costs ~2 min of full deck"
	@echo "      analysis and pages.yml rebuilds it on every push to main anyway)."
	@echo "      Run 'make dashboard' if you want the committed copy current locally."

# Deliberately OUTSIDE refresh: a no-change refresh is ~13s and this step alone is
# ~1m45s of roster-wide deck analysis, for an artifact the deploy workflow
# (.github/workflows/pages.yml) rebuilds from data on every push to main. The
# committed copy is a convenience snapshot; this is its one-command rebuild.
dashboard:
	python3 scripts/build_dashboard.py

# The after-every-deck-edit tail, as ONE command. Every deck edit in the 2026-08
# sessions ended with this same three-step chain typed by hand (re-baseline any new
# roleless engine cards, rebuild the committed dashboard, run the full gate), and at
# ~2 min it outlives a foreground shell window — a recurring ceremony is exactly the
# thing that gets skipped under time pressure (broad-implement #8). Order matters:
# the baseline must update BEFORE check_all or the gate warns about the cards the
# baseline was about to acknowledge.
#
# THAT ORDERING IS ALSO HOW THE RADAR GOT MUTED (BS4-02). Consuming
# the warning is the point of step 1, but consuming it SILENTLY meant a _ROLE_PATTERNS
# edit that re-zeroed fifty cards was acknowledged wholesale, with an unread diff of a
# 425-line file as the only trace. So step 1 now (a) names every card it acknowledges
# and (b) REFUSES a jump bigger than MAXNEW, which is a pattern regression rather than
# a batch of genuinely roleless new cards. Raise it deliberately for a real bulk
# acknowledge: `make postedit MAXNEW=40`.
MAXNEW ?= 8
postedit:
	@echo "==> 1/3 check_roles.py --update-baseline  (acknowledge new zero-role cards)"
	python3 scripts/check_roles.py --update-baseline --max-new $(MAXNEW)
	@echo "==> 2/3 build_dashboard.py               (committed snapshot; ~2 min)"
	python3 scripts/build_dashboard.py
	@echo "==> 3/3 check_all.py                     (invariants + soft sweeps)"
	python3 scripts/check_all.py

clean-venv:
	rm -rf $(VENV)
