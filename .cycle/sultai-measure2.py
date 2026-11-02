# Phase-2 theme measurement over the UBG Historic-Brawl pool (see sultai-pile-analysis.md §6).
import json,re,sys
C=json.load(open('/tmp/sultai/ubg_pool.json'))
T={
 # GRAVEYARD
 'G1 reanimate (graveyard -> battlefield)': r"from (your|a|an opponent's|their) graveyards? (on)?to the battlefield|return (up to \w+ )?target (\w+ )?(creature|permanent) cards? from (your|a) graveyard to the battlefield",
 'G2 cast/play from your graveyard (permission)': r"(cast|play) [^.]{0,60}from your graveyard|from your graveyard[^.]{0,40}(cast|play)|\bflashback\b|\bescape\b|\bunearth\b|\bembalm\b|\beternalize\b|\bdisturb\b|\bjump-start\b|\bretrace\b|\baftermath\b",
 'G3 graveyard-size payoffs (cards in your graveyard / threshold / delirium)': r"(creature |permanent |land |instant and sorcery )?cards? in your graveyard|\bthreshold\b|\bdelirium\b|\bundergrowth\b",
 'G4 descend payoffs': r"\bdescend",
 'G5 self-mill enablers (you mill)': r"(?<!opponent )(you|each player) mills?|\bmill (two|three|four|five|six|\d+) cards|surveil [2-9]",
 'G6 discard payoffs (whenever you discard / madness)': r"whenever you discard|\bmadness\b|discarded this way.{0,40}(return|put|onto)|whenever (one or more )?cards? (is|are) discarded",
 # LIBRARY
 'L1 scry/surveil payoffs (whenever you scry/surveil)': r"whenever you (scry|surveil)|if you (scried|surveilled)",
 'L2 cards leaving/entering your library triggers': r"(put into|leave|leaves) your (graveyard )?from your library|cards? (are|is) put into your graveyard from your library|whenever one or more cards leave your library|put on the bottom of your library.{0,30}whenever",
 'L3 play/cast from top of your library': r"(play|cast) [^.]{0,50}(from )?the top of your library|look at the top card of your library any time",
 'L4 cast/play from an OPPONENT library or exile of theirs': r"(exile|reveal) the top [^.]{0,40}(target|each|that) (opponent|player)'?s library[^.]{0,120}(cast|play)|you may (cast|play) [^.]{0,60}(cards? )?(they|its owner|an opponent) owns?|spells? you (cast but )?don'?t own",
 # DRAW / HAND
 'D1 draw-trigger payoffs (whenever you draw / second card)': r"whenever you draw (a|your second|one or more)|draw your second card each turn|drawn (two|three) or more cards this turn",
 'D2 hand-size payoffs (cards in hand / no max)': r"(number of )?cards in your hand|no maximum hand size|seven or more cards in hand|hellbent",
 # LANDS
 'F1 landfall payoffs': r"\blandfall\b|whenever (a|one or more) lands? (you control )?enters? (the battlefield )?under your control|whenever a land you control enters",
 'F2 land fetch / extra lands / lands from graveyard': r"search your library for (a|up to \w+) (basic )?land|play an additional land|land cards? from your graveyard|(play|put) lands? from your graveyard",
 # ARTIFACTS
 'A1 artifact payoffs (artifacts you control / whenever an artifact enters / for each artifact)': r"artifacts? you control|whenever (an|another|one or more) (nontoken )?artifacts? (you control )?enters?|for each artifact|\baffinity for artifacts\b|\bimprovise\b|\bmetalcraft\b|artifact spells? you cast",
 'A2 artifact token makers (Treasure/Clue/Food/Map/Blood/Powerstone/Thopter)': r"create [^.]{0,40}(Treasure|Clue|Food|Map|Blood|Powerstone|Thopter|Servo|Construct|Incubator|Gold|Junk|Shard)",
}
def show(lbl,rx,limit=26):
    hits=[c for c in C if re.search(rx,c['text'],re.I)]
    hits.sort(key=lambda c:(not c['pile'],not c['own'],c['rar']!='M',c['rar']!='R',c['name']))
    print(f"\n## {lbl}: {len(hits)} pool  | pile {sum(c['pile'] for c in hits)} | owned {sum(c['own'] for c in hits)}")
    print('  '+'; '.join(f"{c['name']}{'[P]' if c['pile'] else '[o]' if c['own'] else ''}" for c in hits[:limit]))
sel=sys.argv[1] if len(sys.argv)>1 else ''
for k,v in T.items():
    if k.startswith(sel): show(k,v)
