# Convenience targets. The CORE tooling (validate/enrich/query/deck/pool/build_*)
# is pure standard library and needs none of this — only the optional editing app
# (scripts/app.py) uses Flask, which `make app` installs into a local venv.

VENV  := .venv
PYBIN := $(VENV)/bin/python
ARGS  ?=

.PHONY: help app check clean-venv

help:
	@echo "make app             set up a local venv, install Flask, and launch the editor"
	@echo "make app ARGS=...    pass args through, e.g. make app ARGS='--port 8000 --no-browser'"
	@echo "make check           run the integrity gate (no dependencies)"
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

clean-venv:
	rm -rf $(VENV)
