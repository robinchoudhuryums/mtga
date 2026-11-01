"""Re-render the Sultai pile board from its Builder project.

Run from the repo root after any change to either deck:  python3 .cycle/board/src/refresh.py
(`--build-only` re-renders the page from template + data without recomputing.)

The project's hand-made content (decks, piles, placements, reasons) lives in
`builds/sultai/build.json`; everything else is derived by `scripts/builder.py`, which calls
the deck model. This file only writes that derived data next to the board's template and
renders the page: PAGE = TEMPLATE + DATA, so a restyle never touches the data.
"""
import json
import os
import sys

sys.path.insert(0, "scripts")
import builder as B  # noqa: E402

PAGE = ".cycle/board/index.html"
DATA = ".cycle/board/src/data.json"
TEMPLATE = ".cycle/board/src/template.html"
SLUG = "sultai"


def build():
    """Render the page: the template with the data island filled in."""
    t = open(TEMPLATE).read()
    blob = json.dumps(json.load(open(DATA))).replace("</", "<\\/")
    open(PAGE, "w").write(t.replace("__DATA__", blob, 1))


if __name__ == "__main__":
    if "--build-only" not in sys.argv:
        data = B.derive(B.load_build(SLUG), tempo=True)
        json.dump(data, open(DATA, "w"))
        live = data["meta"]["live"]
        print({k: {x: v[x] for x in ("floor", "interaction", "ca", "sources", "tapped", "crafts")}
               for k, v in live.items()},
              sum(1 for c in data["cards"] if c.get("iT")), sum(1 for c in data["cards"] if c.get("iG")))
    build()
