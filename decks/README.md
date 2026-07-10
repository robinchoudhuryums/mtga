# Decks

Deck lists live here as plain-text files. Each references cards by name (and
optionally a specific printing) so you can check a deck against your collection
with `scripts/deck.py` and spot gaps before building it in Arena.

## File format

One card per line: a quantity, then the card name. Everything after `#` is a
comment, and blank lines are ignored.

```
# Deck: Merfolk Tribal
# Format: Standard
4 Llanowar Elves
2 Cheerful Osteomancer
1 Kumena, Tyrant of Orazca (XLN)   # a trailing (SET) pins one printing
```

- `4 Card Name` and `4x Card Name` are both accepted.
- A trailing `(SETCODE)` restricts the ownership check to that printing; omit it
  to count copies across every printing you own.

## Checking a deck

```
python3 scripts/deck.py decks/example-merfolk.txt
```

This prints how many copies you own versus how many the deck needs, and flags
any shortfalls or cards not yet in `card-library.csv`. It exits non-zero if the
deck isn't fully buildable, so it also works in scripts.
