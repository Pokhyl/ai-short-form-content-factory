"""Choose a feasible reviewed-media plan before asking for narration."""
from copy import deepcopy
from .grounding import validate_evidence
from .preflight import freeze, validate_asset, digest
from .visual_plan import plan_visuals
from .worker_adapters import DENSITY


class CoverageUnavailable(ValueError):
    pass


def approved(review, asset, unit, evidence_hash):
    contract=unit["contract"]
    checks=review.get("must_show_checks",[])
    score=review.get("match_score")
    return (
      review.get("evidence_sha256")==evidence_hash
      and review.get("scene_id")==unit["id"] and review.get("asset_id")==asset["id"]
      and review.get("asset_sha256")==asset["sha256"]
      and review.get("contract_sha256")==digest(contract)
      and bool(review.get("receipt_id")) and bool(review.get("model"))
      and review.get("is_real_photo") is True
      and not isinstance(score,bool) and isinstance(score,(int,float)) and 55<=score<=100
      and all(review.get(k) is True for k in ("must_show_visible","must_not_show_clear","intent_match"))
      and [c.get("concept") for c in checks]==contract["must_show"]
      and all(c.get("visible") is True for c in checks)
      and set(unit["fact_ids"])<=set(review.get("supported_fact_ids",[])))


def select_catalog(root, evidence, catalog, required_facts, count, search_budget=2000):
    facts=validate_evidence(evidence)
    required=set(required_facts)
    if not required or not required<=facts.keys():
        raise ValueError("required facts missing from research evidence")
    units=catalog["units"]
    if len(units)>64 or len({u["id"] for u in units})!=len(units):
        raise ValueError("catalog unit identity or size invalid")
    assets={}
    for asset in catalog["assets"]:
        validate_asset(root,asset)
        if asset["id"] in assets:
            raise ValueError("duplicate asset identity")
        assets[asset["id"]]=asset
    graph={}; eligible_reviews={}
    evidence_hash=digest(evidence)
    for unit in units:
        if not unit.get("fact_ids") or not set(unit["fact_ids"])<=facts.keys():
            raise ValueError("catalog refers to unknown facts")
        if not unit.get("contract",{}).get("must_show") or not unit["contract"].get("visual_intent"):
            raise ValueError("catalog visual contract missing")
        valid=[]
        for review in catalog["reviews"]:
            asset=assets.get(review.get("asset_id"))
            if asset and approved(review,asset,unit,evidence_hash):
                valid.append(asset["sha256"])
                eligible_reviews.setdefault(unit["id"],[]).append(review)
        graph[unit["id"]]=sorted(set(valid))
    full=plan_visuals(graph)
    if full["matched"]<count:
        raise CoverageUnavailable("not enough globally unique reviewed photos: "+str(full["matched"])+"/"+str(count))
    available=[u for u in units if graph[u["id"]]]
    covered=set().union(*(set(u["fact_ids"]) for u in available))
    if not required<=covered:
        raise CoverageUnavailable("required fact coverage unavailable: "+",".join(sorted(required-covered)))
    visited=0
    def search(index,chosen,covered):
        nonlocal visited
        visited+=1
        if visited>search_budget:
            raise CoverageUnavailable("bounded catalog planning budget exhausted")
        if len(chosen)==count:
            if required<=covered:
                return chosen
            return None
        if len(chosen)+len(available)-index<count:
            return None
        remaining=set().union(*(set(u["fact_ids"]) for u in available[index:]))
        if not required<=covered|remaining:
            return None
        for position in range(index,len(available)):
            unit=available[position]
            tentative=chosen+[unit]
            if plan_visuals({u["id"]:graph[u["id"]] for u in tentative})["status"]!="feasible":
                continue
            result=search(position+1,tentative,covered|set(unit["fact_ids"]))
            if result is not None:
                return result
        return None
    selected=search(0,[],set())
    if selected is None:
        raise CoverageUnavailable("no visual plan covers required facts")
    return selected,eligible_reviews,assets


def prepare(root, topic, language, seconds, evidence, catalog, required_facts, compose, review_script):
    if language not in {"pl","en","ru","uk"} or seconds not in DENSITY:
        raise ValueError("unsupported language or duration")
    selected,eligible,assets=select_catalog(root,evidence,catalog,required_facts,DENSITY[seconds])
    # The composer may paraphrase facts; it cannot replace contracts, add scenes or invent citations.
    request={"topic":topic,"language":language,"seconds":seconds,"evidence":deepcopy(evidence),
      "scenes":[{"id":u["id"],"contract":deepcopy(u["contract"]),"fact_ids":u["fact_ids"]} for u in selected]}
    draft=compose(deepcopy(request))
    entries=draft.get("scenes",[])
    if [s.get("id") for s in entries]!=[u["id"] for u in selected]:
        raise ValueError("composer changed available scene identity/order")
    scenes=[];used_facts=set()
    for entry,unit in zip(entries,selected):
        ids=entry.get("fact_ids",[])
        if not ids or not set(ids)<=set(unit["fact_ids"]):
            raise ValueError("composer introduced unsupported facts")
        if not isinstance(entry.get("narration"),str) or not entry["narration"].strip():
            raise ValueError("composer returned empty narration")
        if set(entry)-{"id","narration","fact_ids"}:
            raise ValueError("composer attempted to change frozen visual contract")
        used_facts.update(ids)
        scenes.append({"id":unit["id"],"narration":entry["narration"].strip(),
                       "evidence_ids":ids,"contract":deepcopy(unit["contract"])})
    if not set(required_facts)<=used_facts:
        raise ValueError("composer omitted required factual scope")
    reviews=[deepcopy(r) for u in selected for r in eligible[u["id"]]]
    chosen_assets={r["asset_id"] for r in reviews}
    script=" ".join(s["narration"] for s in scenes)
    semantic_review=review_script({"topic":topic,"seconds":seconds,"language":language,"script":script,"scenes":deepcopy(scenes),"evidence":deepcopy(evidence)})
    return freeze(root,language,seconds,script,scenes,
                  [deepcopy(assets[a]) for a in sorted(chosen_assets)],reviews,evidence=evidence,script_review=semantic_review,topic=topic)
