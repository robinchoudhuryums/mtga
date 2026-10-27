# Zimone pile — analysis (TEMPORARY working doc)

**Status: IN PROGRESS.** Delete once the deck is drafted and the findings are folded into
the deck file's `#: notes:` block. A scratchpad, not a source of truth — decks/ are.

**Source list:** the owner's 141-card pile, pasted 2026-10-27, aimed at a NEW **Historic
Brawl** deck (100 cards, singleton), commander **Zimone, Paradox Sculptor** ({2}{G}{U}, 1/4).
Owner's themes: exponential counters, Merfolk, Elves, "other synergies that surface". 140
distinct nonland cards, no lands; every card resolves, is Historic-Brawl legal and inside
G/U identity. Cards already in other decks stay ELIGIBLE (copies are shared). Scratch copy:
`zimone/pile.txt` in the session scratchpad.

Zimone: "At the beginning of combat on your turn, put a +1/+1 counter on each of up to two
target creatures you control. {G}{U}, {T}: Double the number of each kind of counter on up to
two target creatures and/or artifacts you control."

## 1. The decision framework

- **R1 — The currency is COUNTERS on creatures and artifacts.** Zimone adds two +1/+1
  counters every combat and, once she can tap, doubles EVERY kind of counter on two targets
  each turn. Grade a card by how many counters it puts out (X-cost Hydras and Fractals,
  "enters with N counters", counter-placing triggers) and by whether it PAYS for a big pile
  (power-matters, "for each counter", trample/evasion to cash it in).
- **R2 — "Each kind" includes non-+1/+1 counters, but only on creatures and artifacts.**
  Charge/oil/other counters on artifacts double; loyalty on planeswalkers and lore on Sagas
  do NOT (not a creature or artifact). Planeswalkers gain only from proliferate.
- **R3 — Doublers stack multiplicatively.** A "twice that many counters" replacement
  (Branching Evolution and kin) doubles every counter PLACED; Zimone doubles what is already
  there. Grade replacement doublers as engine pieces, not filler.
- **R4 — Zimone needs a turn and a tap.** The doubling is a {T} ability, so she cannot use it
  the turn she enters, and she is a 1/4 — protect her (Brawl tax {2} per recast). The combat
  counters arrive at the beginning of combat even if she does not attack.
- **R5 — Tribes are judged by PAYOFF count, not body count (G-59).** Merfolk (Lord of
  Atlantis, Svyelun, Kumena, Tishana, Deeproot…) and Elves (Imperious Perfect, Dionus,
  Eladamri, Thranduil…) are both present; count the payoffs per tribe at the end. Zimone
  is a Human Wizard — neither tribe.
- **R6 — Brawl floor is scaled ×1.67.** A needs interaction 12 and interaction + card
  advantage 19. Simic interaction is thin: counterspells, fight/bite, and -X effects count;
  single-target BOUNCE is report-only tempo since 2026-10-07 (G-25), not interaction. Count
  real interaction carefully.
- **R7 — Two colours: mana is easy, but X-cost cards want MANA.** Ramp and mana creatures
  (Elves) have real value here because the counter cards scale with X.

## 2. Standing error list

- **E1 — A token COPY of an X-counter creature enters with no counters.** Hydras and Fractals
  are 0/0 bodies that ENTER with X counters; Echocasting Symposium, Irma, Undercover Operative
  and other copy effects copy the card, not the counters, so a copied Hydra dies on entry.
  Copy the creature that carries static value, never the X-body.
- **E2 — Doubling a BAD counter is bad.** Zimone doubles every kind of counter, so stun
  counters (The Watcher in the Water) and -1/-1 counters on your own creatures double too.

## 3. Cross-batch observations

- **O1 — Xolatoyac untaps every permanent with a counter at YOUR end step.** Give Zimone one
  of her own combat counters and she doubles twice per turn cycle (main phase, then again
  after the end-step untap, on the opponent's turn). Jace, Ingenious Mind-Mage's +1 (untap
  all creatures) does the same. Untap effects are an engine axis here.
- **O2 — A blue DRAW → COUNTERS sub-theme:** Pensive Professor (counters → draw), Baxter and
  Stark's Ingenuity (draw → counters), Tui and La, Krang (draw triggers twice), Teferi.
- **O3 — A PROLIFERATE sub-theme:** Inexorable Tide (proliferate per spell), Tekuthal
  (proliferate twice), Ichormoon Gauntlet (walkers proliferate; extra counter per
  noncreature spell). Proliferate is the only thing that grows planeswalker loyalty (R2).
- **O4 — Counter REPLACEMENT doublers are deep in green.** Branching Evolution, The Earth
  Crystal, Shang-Chi, Innkeeper's Talent (level 3, ALL counter kinds), plus Michelangelo
  (+1 per placement) and Bristly Bill / Seismic Tutelage (double existing). Order matters:
  apply +1 replacements before doublers when you choose the order (you do, as the
  affected creature's controller). Five-plus doublers is a real engine, not filler.

## 4. Running verdicts

Legend: `★★★ take · ★★ strong · ★ real · ◇ situational · △ marginal · ✗ out`.

### Batch 1 (28, blue)

| Card | Verdict | Note |
|---|---|---|
| Xolatoyac, the Smiling Flood | ★★★ | end-step untap of everything with a counter = Zimone doubles twice a cycle (O1) |
| Eluge, the Shoreless Sea | △ | UUU; Island-count body; flood counters sit on LANDS (R2) |
| Ichormoon Gauntlet | ★ | +1 counter per noncreature spell; walkers proliferate (O3) |
| Irma, Part-Time Mutant | ◇ | copies a creature each combat + a counter (E1: never a Hydra) |
| Namor the Sub-Mariner | ◇ | Merfolk payoff; tokens off blue noncreature spells |
| Pensive Professor | ★★ | every counter placement draws; Zimone feeds it each combat (O2) |
| Stark's Ingenuity | ★ | draw X, then a counter per draw |
| Commit // Memory | ★ | instant answer to a spell or permanent (interaction) |
| Baxter, Fly in the Ointment | ★ | grows on draws; team with counters flies on enter/attack |
| Orvar, the All-Form | △ | needs targeted instants/sorceries on your own permanents |
| Tekuthal, Inquiry Dominus | ★ | proliferate twice; 3/5 flier |
| Tui and La, Moon and Ocean | ★ | draw when tapped, counter when untapped — pairs with O1 untaps |
| Undercover Operative | ★ | clone; its shield counter doubles under Zimone |
| Vesuvan Duplimancy | △ | needs single-target spells on your own creatures |
| Vulture, Feathered Fiend | ◇ | flying-damage draw |
| Yue, the Moon Spirit | ◇ | free noncreature spell from hand |
| Bribery | ◇ | steal their best creature; off-theme |
| Inexorable Tide | ★★ | proliferate on every spell (O3) |
| Krang, the All-Powerful | ◇ | doubles draw triggers (O2) |
| Mesmerizing Benthid | ◇ | defensive hexproof body |
| Namor, Scourge of the Seas | ★ | connive each combat; Merfolk with counters fly |
| Teferi, Temporal Pilgrim | ◇ | loyalty per draw; walkers get nothing from Zimone (R2) |
| Thryx, the Sudden Storm | ◇ | flash flier; MV 5+ discount |
| The Watcher in the Water | ✗ | stun counters (E2) |
| Echocasting Symposium | ◇ | free copy every main phase; copy a static creature, not a Hydra (E1) |
| Jace, Ingenious Mind-Mage | ★ | +1 untaps all creatures — a second Zimone activation (O1) |
| Sublime Epiphany | ★★ | modal counter / bounce / copy / draw — real interaction |
| One with the Multiverse | ◇ | 8 mana |

### Batch 2 (28, green + blue)

| Card | Verdict | Note |
|---|---|---|
| Mockingbird | ◇ | X clone with flying |
| Ambitious Augmenter | ★ | 1-drop increment; dies into a Fractal carrying its counters |
| Burgeoning | ◇ | ramp in 1v1, one extra land per opposing land |
| Smuggler's Surprise | ★ | modal: dig, cheat two creatures, or hexproof+indestructible for power 4+ |
| Bristly Bill, Spine Sower | ★★★ | landfall counters; {3}{G}{G} doubles every creature's +1/+1 counters |
| Fractal Anomaly | ◇ | instant Fractal = cards drawn this turn |
| As Foretold | ◇ | free spells as time counters build |
| Chandra, Chill of Compliance | ◇ | −X stun is real interaction; walker gets nothing from Zimone |
| Imperial Cosmographer | △ | needs blink/bounce of your own creatures |
| Jadzi // Oracle's Gift | ★ | loot 2 on entry; prepared copy makes X Fractals with X counters EACH |
| Herald of Secret Streams | ★★ | every creature with a +1/+1 counter is unblockable — the finisher |
| Serpentine Curve | △ | few instants/sorceries to scale it |
| The Theorist, Jace Beleren | ★ | draw on their draw step; −2 bounces (tempo) |
| Innkeeper's Talent | ★★★ | combat counter; ward 1 on countered permanents; L3 doubles ALL counter kinds |
| Inscription of Abundance | ★★ | instant fight + counters (interaction) |
| Michelangelo, Weirdness to 11 | ★★ | +1 on every counter placement (O4) |
| Arwen, Weaver of Hope | ★ | Elf; others enter with counters = her toughness, which grows |
| Branching Evolution | ★★★ | doubler (O4) |
| Seismic Tutelage | ★ | doubles counters on each attack |
| The Earth Crystal | ★★★ | doubler + green discount |
| Germination Practicum | ★★ | +2 to the team, and free again every first main phase (paradigm) |
| Herd Baloth | ★★ | a 4/4 every time counters land on it — Zimone's combat counter included |
| Nissa, Who Shakes the World | ★ | Forest mana doubling; animated lands carry counters |
| Railway Brawler | ★★ | others enter with counters = their power |
| Shang-Chi, Martial Mentor | ★★ | doubler on a 4/4 body |
| Ancient Bronze Dragon | ◇ | 7-mana flier, random d20 counters |
| Feral Hydra | ◇ | plain X Hydra |
| Goldvein Hydra | ★ | X Hydra with haste and trample; Treasures on death |

## 5. Consolidated plan (live)

- (after the last batch)
