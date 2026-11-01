import json,re,sys
C=json.load(open('/tmp/sultai/ubg_pool.json'))
def show(label, pred, limit=40):
    hits=[c for c in C if pred(c)]
    inp=sum(c['pile'] for c in hits); ow=sum(c['own'] for c in hits)
    print(f"\n## {label}: {len(hits)} in UBG pool  (in pile {inp}, owned {ow})")
    hits.sort(key=lambda c:(not c['pile'], not c['own'], c['name']))
    print('  '+'; '.join(f"{c['name']}{'[P]' if c['pile'] else '[o]' if c['own'] else ''}" for c in hits[:limit]))
    return hits
mode=sys.argv[1]
if mode=='tribes':
    for tribe,pl in [('Elf','Elves'),('Wizard','Wizards')]:
        body=lambda c,t=tribe: re.search(rf'\b{t}\b',c['tf']) and 'Creature' in c['tf']
        pay=lambda c,t=tribe,p=pl: re.search(rf"\b{p} you control|\b{t}s? you control|\bfor each {t}\b|\banother {t}\b|\b{t} spells?\b|\b{t} cards?\b|\bnumber of {p}\b|\b{p} and\b|\b{t} or\b|\beach {t}\b|\bother {p}\b|\bwhenever an? {t}\b|\buntapped {p}\b",c['text']) and not re.fullmatch(r'.*',c['text'])==None
        b=show(f'{tribe} BODIES (creature type)', body, 30)
        p=show(f'{tribe} PAYOFFS (text cares about {pl})', pay, 60)
    show('Changelings (count as every type)', lambda c: re.search(r'\bChangeling\b|is every creature type|all creature types',c['text']) is not None, 30)
elif mode=='mutate':
    show('MUTATE cards', lambda c: re.search(r'\bMutate\b',c['text']) is not None, 60)
    show('MUTATE payoffs (whenever this creature mutates / mutated creature)', lambda c: re.search(r'mutates|mutated',c['text']) is not None, 60)
elif mode=='mill':
    show('OPPONENT mill (target/each opponent or target player mills)', lambda c: re.search(r"(target player|target opponent|each opponent|that player|each player|any number of target players) mills?",c['text'],re.I) is not None, 80)
    show('Repeated/large LIBRARY EXILE (exile the top N of a library)', lambda c: re.search(r"exiles? the top (\w+ )?cards? of (target|each|that|their|an? )?(player|opponent)?'?s? ?library|exile the top \w+ cards of (each|target) (player|opponent)",c['text'],re.I) is not None, 80)
    show('PAYOFFS reading opponents\' graveyards/exile/library size', lambda c: re.search(r"cards? in (target|an?|each) opponent'?s'? graveyards?|cards? your opponents? owns? in exile|opponents own in exile|cards in exile|library has (twenty|ten|\w+) or fewer|fewer cards in (their|his|its) library|no cards in (their|his|its) library",c['text'],re.I) is not None, 60)
    show('Self empty-library WIN', lambda c: re.search(r"(your library has no cards|no cards in your library).{0,40}win|win the game.{0,60}library",c['text'],re.I) is not None, 30)
