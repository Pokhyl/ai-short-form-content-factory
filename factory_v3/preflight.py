"""Freeze exact reviewed render bytes and scene contracts before voice synthesis."""
import hashlib
import json
from pathlib import Path
from .visual_plan import canonical, plan_visuals, require_complete_plan

LICENSES = {"Public Domain", "PDM", "CC0", "CC BY", "CC BY-SA",
            "Pixabay Content License", "Pexels License"}


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def asset_path(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("asset must exist within media root")
    return path


def validate_asset(root, asset):
    for key in ("id", "path", "sha256", "source_url", "author", "license", "license_url"):
        if not isinstance(asset.get(key), str) or not asset[key].strip():
            raise ValueError("missing asset provenance: " + key)
    if asset["license"] not in LICENSES:
        raise ValueError("unsupported license")
    observed = hashlib.sha256(asset_path(root, asset["path"]).read_bytes()).hexdigest()
    if observed != asset["sha256"]:
        raise ValueError("render asset bytes changed")
    return observed


def freeze(root, language, seconds, script, scenes, assets, reviews, evidence=None, script_review=None, topic=None):
    if language not in {"pl", "en", "ru", "uk"} or seconds not in {15, 30, 45, 60}:
        raise ValueError("unsupported language or duration")
    if not isinstance(script, str) or not script.strip() or not scenes:
        raise ValueError("nonempty narration and scenes required")
    if len({s["id"] for s in scenes}) != len(scenes):
        raise ValueError("duplicate scene identity")
    if evidence is not None:
        from .grounding import validate_evidence, validate_script_review
        facts = validate_evidence(evidence)
        validate_script_review(evidence, language, script, scenes, script_review, topic=topic)
        if any(not set(scene["evidence_ids"]) <= facts.keys() for scene in scenes):
            raise ValueError("scene references unknown research facts")
    asset_map = {}
    for asset in assets:
        if asset["id"] in asset_map:
            raise ValueError("duplicate asset identity")
        validate_asset(root, asset)
        asset_map[asset["id"]] = asset
    graph = {}
    eligible_ids = {}
    for scene in scenes:
        contract = scene["contract"]
        if not contract.get("visual_intent") or not contract.get("must_show"):
            raise ValueError("missing visual contract")
        if not scene.get("evidence_ids") or not scene.get("narration"):
            raise ValueError("scene must bind narration to evidence")
        valid = []
        for review in reviews:
            asset = asset_map.get(review.get("asset_id"))
            if asset is None or review.get("scene_id") != scene["id"]:
                continue
            if review.get("asset_sha256") != asset["sha256"] or review.get("contract_sha256") != digest(contract):
                continue
            if evidence is not None and review.get("evidence_sha256") != digest(evidence):
                continue
            if evidence is not None and (review.get("is_real_photo") is not True or not set(scene["evidence_ids"]) <= set(review.get("supported_fact_ids", []))):
                continue
            if not review.get("receipt_id") or not review.get("model"):
                continue
            score = review.get("match_score")
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not 55 <= score <= 100:
                continue
            if any(review.get(key) is not True for key in ("must_show_visible", "must_not_show_clear", "intent_match")):
                continue
            checks = review.get("must_show_checks", [])
            if [c.get("concept") for c in checks] != contract["must_show"] or any(c.get("visible") is not True for c in checks):
                continue
            valid.append(asset["sha256"])
            eligible_ids[(scene["id"], asset["sha256"])] = min(asset["id"], eligible_ids.get((scene["id"], asset["sha256"]), asset["id"]))
        graph[scene["id"]] = valid
    if " ".join(s["narration"].strip() for s in scenes) != script.strip():
        raise ValueError("final narration differs from reviewed scene narration")
    plan = plan_visuals(graph)
    physical_selection = require_complete_plan(plan, graph)
    selection = {scene: eligible_ids[(scene, sha)] for scene, sha in physical_selection.items()}
    payload = {"schema": 1, "language": language, "seconds": seconds,
               "script": script, "scenes": scenes, "selection": selection,
               "assets": [asset_map[k] for k in sorted(asset_map)],
               "reviews": reviews, "visual_plan": plan}
    if topic is not None:
        payload["topic"] = topic
    if evidence is not None:
        payload["evidence"] = evidence
        payload["script_review"] = script_review
    # A content digest detects stale/changed local state; it is not a provider signature.
    return {"payload": payload, "sha256": digest(payload)}


def verify_before_voice(root, frozen):
    payload = frozen["payload"]
    if digest(payload) != frozen["sha256"]:
        raise ValueError("frozen plan modified")
    current = freeze(root, payload["language"], payload["seconds"], payload["script"],
                     payload["scenes"], payload["assets"], payload["reviews"], evidence=payload.get("evidence"), script_review=payload.get("script_review"), topic=payload.get("topic"))
    if current != frozen:
        raise ValueError("frozen plan no longer matches media or review state")
    return payload
