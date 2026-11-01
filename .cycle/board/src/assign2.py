import json
rows=json.load(open("/tmp/split/rows.json"))
def sv(s):
    s=s or ""
    return 4 if "★★★" in s else 3 if "★★" in s else 2 if "★" in s else 1.5 if "◇" in s else 1 if "△" in s else 0 if "✗" in s else None
OV={}
def ov(p, names):
    for n in names.split(";"): OV[n.strip().lower()]=p
ov("T","Along the Crooked Way;Chalk Outline;Desecrated Tomb;Attuned Hunter;Kishla Skimmer;Undead Hand Ninja;Dredger's Insight;Willow Geist;Rot Farm Mortipede;Scavenger's Talent;Deathrite Shaman;Laboratory Maniac;Eladamri, Korvecdal")
ov("G","Altar of Dementia;Ashiok, Dream Render;Brain Freeze;Cruel Somnophage // Can't Wake Up;Cut Your Losses;Didn't Say Please;Drowned Secrets;Duskmantle, House of Shadow;Fleet Swallower;Folio of Fancies;Grindstone;Gyruda, Doom of Depths;Hama, the Bloodbender;Jin-Gitaxias // The Great Synthesis;Jin-Gitaxias;Keening Stone;Lord of the Forsaken;Memory Deluge;Navigator's Ruin;Persistent Petitioners;Riverchurn Monument;Sokka's Haiku;Terisian Mindbreaker;Visions of Beyond;Opt;Preordain;Arcane Epiphany;Howling Mine;Hullbreaker Horror;Mind's Dilation;Villainous Wealth;Inside Information;Courser of Kruphix;Precognition Field;Vivien, Monsters' Advocate;Augur of Autumn")
ov("B","Consider;Memory Lapse;Tamiyo, Inquisitive Student // Tamiyo, Seasoned Scholar;The Everflowing Well // The Myriad Pools;Thought Scour;Anoint with Affliction;Bitter Triumph;Bloodchief's Thirst;Fatal Push;Feed the Swarm;Murderous Rider // Swift End;Pongify;Sheoldred's Edict;Tear Asunder;Toxic Deluge;Saw It Coming;Mystic Snake;Wizard's Retort;Kenrith's Transformation;Cultivate;Nature's Lore;Farseek;Delighted Halfling;Talisman of Resilience;Oracle of Mul Daya")

ov("T","Kaervek, the Punisher;Brokkos, Apex of Forever;Gisa, Glorious Resurrector;Beledros Witherbloom;Pharaoh Rama-Tut;Malcolm, Alluring Scoundrel")
ov("G","Jace, Wielder of Mysteries;Jace, Unraveler of Secrets;Jace, Arcane Strategist;Kefnet the Mindful;Krang, the All-Powerful;Nissa, Steward of Elements;Seizan, Perverter of Truth;Seymour Flux;Thryx, the Sudden Storm;Rona, Disciple of Gix;Imoti, Celebrant of Bounty;The Key to the Vault;Radagast of Rhosgobel;Iymrith, Desert Doom;Jin-Gitaxias, Progress Tyrant;Wan Shi Tong, Librarian")
ov("B","Davriel, Soul Broker;Kitsune, Dragon's Daughter;Elrond, Lord of Rivendell;Elrond, Master of Healing;Galadriel of Lothlórien;Rashmi, Eternities Crafter")
ov("N","Niv-Mizzet, Visionary;Chulane, Teller of Tales;Kogla and Yidaro")
for r in rows:
    inT,inG=r["T"]["present"],r["G"]["present"]; k=r["name"].lower()
    if inT and inG: p="B"
    elif k in OV: p=OV[k]
    elif r["src"]=="pile":
        a,b=sv(r["starA"]),sv(r["starB"])
        a=a if a is not None else 0; b=b if b is not None else 0
        if max(a,b)<2: p="N"
        elif abs(a-b)<1: p="B"
        else: p="T" if a>b else "G"
        if inT and p!="T": p = "B" if p in ("B","G") and b>=2 else "T"
        if inG and p!="G": p = "B" if p in ("B","T") and a>=2 else "G"
    else:
        p = "T" if inT else "G" if inG else "?"
    if p=="N" and "Elf" in r.get("type","").split(" // ")[0] and k not in OV: p="T"
    r["pile"]=p
json.dump(rows,open("/tmp/split/rows.json","w"))
from collections import Counter
print(Counter(r["pile"] for r in rows))
print(Counter((r["pile"],r["T"]["present"],r["G"]["present"]) for r in rows))
print([r["name"] for r in rows if r["pile"]=="?"])
