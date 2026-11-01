R = {}
def add(group, items):
    for n, t in items: R[n] = (group, t)
add("Swap candidate", [
 ("Krang, the All-Powerful", "\"If a player drawing a card causes a triggered ability of a permanent you control to trigger, that ability triggers an additional time\" doubles Psychic Corrosion, both Tutelages, Sheoldred and The Theorist — the deck's whole engine. **Strongest add on this list.** Left out on slot count."),
 ("Phenax, God of Deception", "Gives your creatures `{T}: Target player mills X cards, where X is this creature's toughness`. Most of the 20 creatures here have toughness 4–5 (Bruvac, Matoya, Reed, both Sheoldreds, Silumgar, M.O.D.O.K.), so each is a mill-4 engine, doubled under Bruvac. Indestructible."),
 ("Jin-Gitaxias // The Great Synthesis", "\"Whenever you cast a noncreature spell with mana value 3 or greater, draw a card\" — 28 such spells here, and each draw mills two. Owned. Lost its slot to Jin-Gitaxias, Core Augur, but both fit."),
 ("Drowned Secrets", "\"Whenever you cast a blue spell, target player mills two cards\" — 42 blue spells here. A 2-mana engine that does not need a draw."),
 ("Jin-Gitaxias, Progress Tyrant", "Copies your first artifact/instant/sorcery each turn — a second Traumatize empties a library — and counters the opponent's first one. Mana value 7, so Glarb casts it off the top."),
 ("Seizan, Perverter of Truth", "\"At the beginning of each player's upkeep, that player loses 2 life and draws two cards\": the opponent loses two library cards a turn, and your two draws mill four through Psychic Corrosion. Symmetric, which this deck wants (it already runs Dictate of Kruphix)."),
 ("Visions of Beyond", "1 mana: \"If a graveyard has twenty or more cards in it, draw three cards instead\" — the opponent's graveyard passes 20 early here, so it is a 1-mana draw-three (six milled through Corrosion)."),
 ("Lo and Li, Royal Advisors", "`{2}{U/B}: Target player mills four cards`, repeatable at instant speed; an Advisor (with Bruvac and The Master of Lake-town) that grows when they mill."),
 ("Riverchurn Monument", "Owned. `{1}, {T}`: mill two every turn, and once per game its exhaust mills \"cards equal to the number of cards in their graveyard\" — doubles a half-milled yard."),
 ("Chandra, Chill of Compliance", "Owned. +1 surveil feeds Matoya and Proft; the other +1 adds mana for noncreature spells; −X stuns a threat. Screened KEY against the list."),
 ("Memory Deluge", "Instant: two of the top X, then flashback — four draws for eight mana of the late game, each draw milling two."),
])
add("Different finisher, same job", [
 ("Fleet Swallower", "\"Whenever this creature attacks, target player mills half their library\" — a 7-mana creature that must attack; Traumatize and kicked Maddening Cacophony do it from the hand."),
 ("Cut Your Losses", "Half a library for 6 (twice with casualty); the deck already holds Traumatize, Maddening Cacophony and Jidoor's Overture as half-library mills."),
 ("Terisian Mindbreaker", "Half a library on attack, unearth for `{1}{U}{U}{U}`; a 7-mana artifact creature doing Fleet Swallower's job."),
 ("Jace, Wielder of Mysteries", "+1 mills two and draws one (four milled under Corrosion); its alt-win needs YOUR library empty, which this deck never aims for. `{1}{U}{U}{U}` is hard in three colours."),
 ("Gyruda, Doom of Depths", "\"Each player mills four cards\" and you take a creature from among them — a one-shot, symmetric 6-drop."),
 ("Cruel Somnophage // Can't Wake Up", "Mill four for 2, then a body that grows with creature cards in all graveyards. Fine; smaller than the deck's 2-mana mills (Glimpse the Unthinkable mills ten)."),
 ("Hama, the Bloodbender", "Owned. Mills three and lets you cast one of their noncreature spells by waterbending — deck 22's engine piece; a 5-mana one-shot here."),
 ("Brain Freeze", "Mill three plus storm; the deck casts one or two spells a turn, so it is usually mill three."),
 ("Navigator's Ruin", "Raid — mill four only if you attacked; this deck rarely attacks."),
 ("Didn't Say Please", "Counter + mill three — the same card as Thought Collapse, which is in. The first card to add if you want more counters."),
 ("Sokka's Haiku", "Owned. Counter + draw, but \"mill three cards\" mills YOU, and it costs 5."),
])
add("Mill outlet whose cost the deck lacks", [
 ("Altar of Dementia", "\"Sacrifice a creature: mills … equal to the sacrificed creature's power\" — the deck makes almost no fodder (its tokens are a few Ashiok Nightmares)."),
 ("Lord of the Forsaken", "`{B}, Sacrifice another creature: mill three` — same missing fodder; 6 mana."),
 ("Persistent Petitioners", "Its 12-card mill needs four Advisors tapped; it is the one card a deck may run in any number, so it only works as a dozen-copy package — a different deck."),
 ("Grindstone", "`{3}, {T}`: mill two, repeating while the two share a colour — about 2–4 a turn for 3 mana each turn."),
 ("Keening Stone", "6 to cast and `{5}, {T}` to mill X = their graveyard; Riverchurn Monument's exhaust does the same once for 4."),
 ("Duskmantle, House of Shadow", "A land that makes only colourless — in a three-colour deck already at 3.5 points of tapped-land cost — for a 3-mana mill one."),
])
add("Duplicates Glarb's top-of-library", [
 ("Bolas's Citadel", "Glarb already casts MV 4+ off the top; Citadel adds the cheap ones for life. `{3}{B}{B}{B}` with 20 black sources, and the life matters against aggro."),
 ("Fblthp, Lost on the Range", "Plots from the top — a slower version of what Glarb already does."),
 ("Precognition Field", "Instants and sorceries from the top (21 here) — the closest of these; covers the cheap ones Glarb cannot. Bench."),
 ("Augur of Autumn", "Lands from the top — Glarb does it; the creature half needs coven."),
 ("Courser of Kruphix", "Lands from the top plus life; Glarb does the first part. `{1}{G}{G}` on 15 green sources."),
 ("Vivien, Monsters' Advocate", "Creatures from the top; the deck runs 20 creatures, mostly utility. `{3}{G}{G}`."),
 ("Nissa, Steward of Elements", "Scry 2 and puts lands/small creatures from the top into play; green-blue value without a mill tie."),
 ("Imoti, Celebrant of Bounty", "Cascade on mana value 6+ — the deck has few 6+ spells."),
 ("Rona, Disciple of Gix", "Exiles one of YOUR historic cards to cast later and exiles your own top card for {4}; little here."),
])
add("Cast their cards / combat-gated", [
 ("Gonti, Canny Acquisitor", "Steals a card on combat damage; the deck is a control deck that rarely connects."),
 ("Rev, Tithe Extractor", "Treasure + steal on combat damage — same problem."),
 ("Kotis, the Fangkeeper", "Exiles X on combat damage and casts them free — an aggressive card in a deck that wins by milling."),
 ("Gix, Yawgmoth Praetor", "Combat draws; its `{4}{B}{B}{B}` exile needs a hand to discard."),
 ("Xanathar, Guild Kingpin", "Strong — they cannot cast spells on your turn and you play their top card — but 6 mana for a value engine the mill plan does not need. Bench."),
 ("Krang & Shredder", "Owned. Exiles to a nonland and casts it if a permanent left your control — needs a sacrifice the deck lacks."),
 ("Villainous Wealth", "Exile X of their library and cast them — real library exile, but `{X}{B}{G}{U}` competes with Tasha's Hideous Laughter, which exiles until 20 total mana value — usually ten or more cards — for 3."),
 ("Inside Information", "Exile X and play them this turn for life; a one-turn burst."),
 ("Mind's Dilation", "7 mana; exiles one card per opponent spell — slow as library exile."),
 ("The Key to the Vault", "Equipment that casts from YOUR library on combat damage — combat-gated."),
 ("Sméagol, Helpful Guide", "Needs a creature to die each turn for the Ring to tempt you."),
])
add("Draw engine, outranked", [
 ("Howling Mine", "Symmetric extra draw — the same job as Dictate of Kruphix, which is in; a second one would refill their hand too. Bench."),
 ("Lyra, Tolarian Archangel", "Owned. A 3/3 Angel at end step when you drew three — common here, but it is a body, not a draw or a mill."),
 ("Arcane Epiphany", "Draw three for 4 (Glarb is a Wizard); fine, outranked by the repeatable engines."),
 ("Arwen's Gift", "Scry 2, draw 2 (cheaper with two legends); one-shot."),
 ("Jace, Arcane Strategist", "6 mana for +1: draw a card."),
 ("Jace, Unraveler of Secrets", "5 mana; +1 scry 1 then draw (Matoya draws again). Close; −2 bounce is tempo."),
 ("Iymrith, Desert Doom", "Draws on combat damage only."),
 ("Seymour Flux", "Pay 1 life: draw one each upkeep — a Phyrexian Arena on a body, and Arena is in."),
 ("Kefnet the Mindful", "`{3}{U}`: draw one — an expensive sink."),
 ("Tishana, Voice of Thunder", "Draws one per creature you control — usually 2–4 here; 7 mana."),
 ("Wan Shi Tong, Librarian", "Owned. Flash X body that draws half X, and more when they search; decent filler."),
 ("Proft's Eidetic Memory", "Draws one, no hand size, counters on combat — the counters do nothing here."),
 ("Tam, Observant Sequencer // Deep Sight", "Owned. Draw one on landfall-prepared casts; small."),
 ("Kasmina, Enigma Sage", "+2 scry 1 (feeds Matoya) and shares loyalty abilities with the deck's three Ashioks and Jaces — cute, low impact."),
 ("Thryx, the Sudden Storm", "Spells with mana value 5+ cost {1} less and can't be countered — a flash flier; the deck's MV 5+ spells mostly come off the top already."),
 ("Radagast of Rhosgobel", "First creature each turn costs {2} less with flash; 20 creatures, few of them cheap."),
 ("Hullbreaker Horror", "A 7-mana bounce engine; strong in control, but each turn's mill matters more than tempo here."),
 ("Nemata, Primeval Warden", "Exiles their dying creatures (keeps them out of the graveyard Consuming Aberration counts) and draws off Saprolings."),
 ("Opt", "Scry 1 then draw — under Matoya that is two draws, four milled. A cheap filler; Brainstorm is in."),
 ("Preordain", "Scry 2 then draw; same as Opt, slightly better."),
 ("Folio of Fancies", "`{X}{X}, {T}`: each player draws X (both libraries shrink; yours mills them twice through Corrosion), then `{2}{U}` mills them equal to hand size. A real engine; bench."),
])
add("Fights the engine (G-42)", [
 ("Ashiok, Dream Render", "Cut at draft: its −1 \"exile each opponent's graveyard\" empties the yard Consuming Aberration, Drown in the Loch and Sheoldred's transform count."),
 ("Ashiok, Wicked Manipulator", "\"If you would pay life … exile that many cards from the top of your library instead\" — Phyrexian Arena, Doctor Doom and Infernal Grasp would exile YOUR library in a deck that already draws hard. Its −7 is a real finisher; the static is the problem."),
])
