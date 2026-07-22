#!/usr/bin/env python3
"""Anchor sanity checks for the engine-role classifier (deck.py, improvement #3).

`engine_roles` splits a card's oracle text into ENABLER (feeds an engine) vs PAYOFF
(rewards it) for the two-sided engine themes (sacrifice, counters, tokens, graveyard,
lifegain, food), so `engine_balance` / `deck.py engines` can flag a lopsided engine —
payoffs with no enablers, the flaw a bag-of-tags model can't see.

These checks lock the classifier's known-good behavior on canonical cards (the same way
check_rankings/check_colors/check_suggest guard their models): a regex edit that breaks
a textbook enabler/payoff, or lets an edict masquerade as a sac outlet, fails the gate.
Card-text based and distribution-independent, so they keep holding as the collection
changes. Returns a list of error strings; empty == healthy.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# (label, oracle text, theme, expected-role-subset). role in {"enabler","payoff","death"}.
CASES = [
    ("sac outlet",   "Sacrifice a creature: Draw a card.",                       "sacrifice", "enabler"),
    # "whenever ~ dies" is now its own COMBAT-FED role ('death'), distinct from a
    # sac-outlet-dependent 'payoff' — the split that stops the go-wide false positive.
    ("death trigger","Whenever a creature you control dies, each opponent loses 1 life.", "sacrifice", "death"),
    ("sac trigger",  "Whenever you sacrifice a permanent, draw a card.",        "sacrifice", "payoff"),
    ("counter placer","Put a +1/+1 counter on target creature.",                "counters",  "enabler"),
    ("counter payoff","Ghalta's power is equal to the number of +1/+1 counters among creatures you control.", "counters", "payoff"),
    ("token maker",  "Create a 1/1 white Soldier creature token.",              "tokens",    "enabler"),
    ("yard filler",  "Mill three cards, then return a creature card to your hand.", "graveyard", "enabler"),
    ("reanimator",   "Return target creature card from your graveyard to the battlefield.", "graveyard", "payoff"),
    # Flashback (and escape/harmonize/…) put the card in the yard itself → self-enabling:
    # it must read as an ENABLER, not only a payoff, so a flashback-heavy deck isn't
    # mis-flagged as "payoffs with no enablers".
    ("self-recursion enabler", "Lightning deals 3 damage to any target. Flashback {4}{R}.", "graveyard", "enabler"),
    ("lifegain payoff","Whenever you gain life, draw a card.",                   "lifegain",  "payoff"),
    ("food maker",   "Create a Food token.",                                    "food",      "enabler"),
]

# Texts that must NOT be classified as the given (theme, role) — false-positive guards.
NEG_CASES = [
    ("edict != our outlet", "Target player sacrifices a creature.", "sacrifice", "enabler"),
    ("vanilla != engine",   "Flying. Vigilance.",                   "sacrifice", "enabler"),
    ("vanilla != counters", "Flying. Vigilance.",                   "counters",  "payoff"),
    # a death trigger must be 'death', NOT 'payoff' — else it double-counts and re-earns
    # the sac-outlet dependency the split exists to remove.
    ("death != sac-payoff", "Whenever a creature you control dies, each opponent loses 1 life.",
     "sacrifice", "payoff"),
]


def check():
    """Return a list of error strings (empty == healthy). Never raises."""
    try:
        import deck
    except Exception as e:  # pragma: no cover - import guard
        return [f"engine classifier: could not import deck.py ({e})"]

    errs = []
    for label, text, theme, role in CASES:
        got = deck.engine_roles(text).get(theme, set())
        if role not in got:
            errs.append(f"engine classifier: '{label}' should be a {theme} {role}; "
                        f"engine_roles gave {theme}→{sorted(got) or 'none'}.")
    for label, text, theme, role in NEG_CASES:
        got = deck.engine_roles(text).get(theme, set())
        if role in got:
            errs.append(f"engine classifier: '{label}' must NOT read as a {theme} {role} "
                        f"(false positive); got {theme}→{sorted(got)}.")

    # engine_balance verdicts: payoffs with no enablers flags; a balanced pair does not.
    try:
        cd = {
            "blood artist": {"name": "Blood Artist", "type": "Creature",
                             "text": "Whenever a creature dies, target player loses 1 life.", "colors": "B"},
            "viscera seer": {"name": "Viscera Seer", "type": "Creature",
                             "text": "Sacrifice a creature: Scry 1.", "colors": "B"},
        }
        dead = deck.engine_balance([(2, "Blood Artist", "", ""), (2, "Blood Artist", "", "")],
                                   cd, ["sacrifice"])
        # Blood Artist ×4 (quantity-weighted, summed across both lines — audit A11) is
        # still < _COMBAT_FED_MIN creatures → death triggers can't be combat-fed, no
        # outlet → still a dead engine, must flag.
        if not dead.get("sacrifice", {}).get("flag"):
            errs.append("engine_balance: death-trigger sacrifice engine with almost no board "
                        "(2 creatures, no outlet) should FLAG as lopsided, but didn't.")
        bal = deck.engine_balance([(2, "Blood Artist", "", ""), (2, "Viscera Seer", "", "")],
                                  cd, ["sacrifice"])
        if bal.get("sacrifice", {}).get("flag"):
            errs.append("engine_balance: a sacrifice engine with BOTH an outlet and a payoff "
                        "should read balanced, but flagged.")

        # Combat-fed exemption (#3 refinement): the SAME death-trigger payoffs, now backed
        # by a real creature base and STILL no sac outlet, must NOT flag — combat feeds them.
        cd2 = dict(cd)
        cd2["grizzly bears"] = {"name": "Grizzly Bears", "type": "Creature — Bear",
                                "text": "", "colors": "G"}
        # 8 vanilla bodies + the death-trigger payoff, no sac outlet (quantity-weighted count).
        wide = [(2, "Blood Artist", "", ""), (8, "Grizzly Bears", "", "")]
        combat = deck.engine_balance(wide, cd2, ["sacrifice"])
        if combat.get("sacrifice", {}).get("flag"):
            errs.append("engine_balance: combat-fed death triggers (Blood Artist + 8 creatures, "
                        "no outlet) must NOT flag — a go-wide board feeds them without a sac "
                        "outlet (the go-wide/deathtouch false positive).")

        # Graveyard self-recursion: a yard full of flashback spells is self-enabling and must
        # read balanced (not "payoff-heavy / no enablers").
        cdg = {
            "faithless salvage": {"name": "Faithless Salvage", "type": "Instant",
                                  "text": "Draw two cards, then discard a card. Flashback {3}{R}.", "colors": "R"},
            "runic repetition":  {"name": "Runic Repetition", "type": "Sorcery",
                                  "text": "Return target card you own from exile to your hand. Flashback {2}{U}.", "colors": "U"},
        }
        gy = deck.engine_balance([(2, "Faithless Salvage", "", ""), (2, "Runic Repetition", "", "")],
                                 cdg, ["graveyard"])
        if gy.get("graveyard", {}).get("flag"):
            errs.append("engine_balance: flashback (self-recursion) spells must read as their own "
                        "enablers — a flashback-heavy graveyard must NOT flag as payoff-heavy.")
    except Exception as e:
        errs.append(f"engine_balance raised {type(e).__name__}: {e}")

    return errs


def main():
    errs = check()
    if errs:
        print("Engine classifier sanity: FAIL")
        for e in errs:
            print(f"  ✗ {e}")
        return 1
    print("Engine classifier sanity: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
