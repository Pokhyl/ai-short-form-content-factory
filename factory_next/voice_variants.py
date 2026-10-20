"""Select whole source-bound beat variants using exact local length measurements."""
from itertools import product
from factory_v3.gemini import obj, array, string, validate_json
from .duration import revision_length_fits, NaturalDurationRejected

LABELS=("short","medium","long")

def variant_contract(scenes):
    if not isinstance(scenes,list) or not 1<=len(scenes)<=8:
        raise ValueError("bounded reviewed scenes required")
    return obj({"beat_"+str(i+1):obj({name:obj({"fact_comparison":string(),"narration":{**string(),"maxLength":2000},
                "fact_ids":array(string(scenes[i]["evidence_ids"]),1,len(scenes[i]["evidence_ids"]))})
                                   for name in LABELS})
                for i in range(len(scenes))})

def variant_measurements(reply):
    return {beat:{label:{"words":len(text["narration"].split()),"characters":len(text["narration"].strip())}
                  for label,text in row.items()}
            for beat,row in reply.items()}

def choose_variants(reply,scenes,window):
    validate_json(reply,variant_contract(scenes))
    pools=[]
    for i in range(len(scenes)):
        unique=[]
        for label in LABELS:
            variant=reply["beat_"+str(i+1)][label]
            text=variant["narration"].strip()
            facts=variant["fact_ids"]
            if len(set(facts))!=len(facts):
                continue
            if (len(text.split())>=5 and text[-1:] in ".!?…" and
                    text.casefold() not in [v[0].casefold() for v in unique]):
                unique.append((text,tuple(facts)))
        if not unique:
            raise NaturalDurationRejected("no complete variants for a reviewed beat")
        pools.append(unique)
    best=None
    for candidate in product(*pools):
        if len(set(x[0].casefold() for x in candidate))!=len(candidate):
            continue
        required=set(f for scene in scenes for f in scene["evidence_ids"])
        if not required <= set(f for _,facts in candidate for f in facts):
            continue
        text=" ".join(x[0] for x in candidate)
        if not revision_length_fits(text,window):
            continue
        score=(abs(len(text)-window["target_characters"]),
               abs(len(text.split())-window["target_words"]),candidate)
        if best is None or score<best[0]:
            best=(score,candidate)
    if best is None:
        raise NaturalDurationRejected("no whole-variant combination fits measured voice window")
    return {"beats":[{"material_id":scene["material_id"],
                      "fact_ids":list(facts),"narration":text}
                     for scene,(text,facts) in zip(scenes,best[1])]}
