"""Prepare a source-bound story from inspected photographs and video intervals.

Operations are server-owned adapters, not public approval fields. This module
does not certify the correctness of a model's observations or HUMAN acceptance.
"""
from copy import deepcopy
import math
from pathlib import Path
import hashlib
import json
import subprocess

from factory_v3.preparation import ResourceUnavailable
from factory_v3.grounding import validate_evidence, validate_script_review
from factory_v3.preflight import asset_path, digest, validate_asset
from .targets import validate_targets, matched_targets
from .visuals import POLICY, CALM_POLICY, WHOLE_POLICIES, candidate_limit, make_visuals, validate_visuals
from .presentation import preferred_shots, minimum_shots


class MaterialUnavailable(ValueError):
    pass


def probe_media(file):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(file)],
        capture_output=True, text=True, timeout=20, check=True)
    data = json.loads(result.stdout)
    videos = [s for s in data["streams"] if s.get("codec_type") == "video"]
    if len(videos) != 1:
        raise ValueError("material must contain one visual stream")
    stream = videos[0]
    duration = stream.get("duration", data.get("format", {}).get("duration"))
    # ffprobe gives a JPEG a nominal 40 ms stream duration. Actual frame
    # count distinguishes a still image from an animated image.
    image_format = data.get("format", {}).get("format_name", "")
    if image_format in {"image2", "jpeg_pipe", "png_pipe", "webp_pipe"}:
        if stream.get("nb_read_frames") == "1":
            duration = None
    return {"width": int(stream["width"]), "height": int(stream["height"]),
            "duration_ms": round(float(duration) * 1000) if duration is not None else None}


def validate_material(root, asset, probe=probe_media):
    validate_asset(root, asset)
    kind = asset.get("media_type")
    if kind not in {"photo", "video"}:
        raise ValueError("unsupported real material type")
    path = asset_path(root, asset["path"])
    allowed = {"photo": {".jpg", ".jpeg", ".png", ".webp"},
               "video": {".mp4", ".webm", ".mov"}}
    if path.suffix.lower() not in allowed[kind]:
        raise ValueError("material extension differs from declared type")
    actual = probe(path)
    if actual["width"] < 320 or actual["height"] < 320:
        raise ValueError("material resolution too low")
    if kind == "video":
        if not isinstance(actual.get("duration_ms"), int) or actual["duration_ms"] <= 0:
            raise ValueError("video duration missing")
        if asset.get("duration_ms") != actual["duration_ms"]:
            raise ValueError("video duration differs from actual file")
    elif actual.get("duration_ms") is not None:
        raise ValueError("animated images must not be declared photographs")
    return actual


def inspected_material(asset, receipt, evidence, facts, validation_mode="gemini"):
    if validation_mode == "metadata":
        from .metadata import material
        return material(asset, receipt, evidence, facts)
    if validation_mode != "gemini" or receipt.get("validation_method") == "metadata":
        raise ValueError("visual validation mode changed")
    """Metadata tags alone can never admit a material to the composer."""
    if (receipt.get("asset_id") != asset["id"] or receipt.get("asset_sha256") != asset["sha256"]
            or receipt.get("evidence_sha256") != digest(evidence)
            or not receipt.get("receipt_id") or not receipt.get("model")
            or receipt.get("accepted") is not True or receipt.get("is_real_material") is not True):
        return None
    visible = receipt.get("visible_description")
    support = receipt.get("supported_fact_ids")
    if not isinstance(visible, str) or not visible.strip() or not isinstance(support, list) or not support:
        return None
    if len(set(support)) != len(support) or not set(support) <= facts.keys():
        raise ValueError("inspection introduced an unknown fact")
    if asset["media_type"] == "photo":
        interval = None
        # A still illustrates source-backed narration, including actions.
        # It can remain on screen for the narrated beat without inventing motion.
        capacity = 60000  # Longest supported request; no artificial hold limit.
    else:
        start, end = receipt.get("source_start_ms"), receipt.get("source_end_ms")
        if (type(start) is not int or type(end) is not int
                or not 0 <= start < end <= asset["duration_ms"]):
            raise ValueError("inspection interval outside real video")
        interval = {"start_ms": start, "end_ms": end}
        capacity = end - start
        if capacity < 1000:
            return None
    target_matches = matched_targets(asset, receipt)
    if target_matches is not None and not target_matches:
        return None
    result = {"id": asset["id"], "media_type": asset["media_type"],
            "sha256": asset["sha256"], "visible_description": visible.strip(),
            "supported_fact_ids": support, "source_interval": interval,
            "capacity_ms": capacity, "inspection": deepcopy(receipt)}
    if target_matches is not None:
        result['matched_visual_targets'] = target_matches
    return result


def match_materials(available, draft, *, contextual=False):
    """Assign unique inspected pictures to claims, preferring model choices."""
    result = deepcopy(draft)
    known = {m['id']: m for m in available}
    beats = result['beats']
    options = []
    for beat in beats:
        if beat['material_id'] not in known:
            raise ValueError('composer invented material')
        facts = set(beat['fact_ids'])
        target = beat.get('visual_target_id')
        candidates = [m['id'] for m in available if (contextual or facts <= set(m['supported_fact_ids']))
                      and (target is None or target in m.get('matched_visual_targets', {}))]
        candidates.sort(key=lambda identity: identity != beat['material_id'])
        options.append(candidates)
    owners = {}
    def assign(index, visited):
        for identity in options[index]:
            if identity in visited:
                continue
            visited.add(identity)
            previous = owners.get(identity)
            if previous is None or assign(previous, visited):
                owners[identity] = index
                return True
        return False
    for index in range(len(beats)):
        if not assign(index, set()):
            raise MaterialUnavailable('not enough distinct inspected pictures for narrated claims')
    for identity, index in owners.items():
        beats[index]['material_id'] = identity
    return result


def validate_story(request, evidence, available, draft):
    known = {m["id"]: m for m in available}
    contextual = request.get("presentation_policy") in WHOLE_POLICIES
    allowed_facts = {f["id"] for f in evidence["facts"]}
    beats = draft.get("beats")
    if not isinstance(beats, list) or not 1 <= len(beats) <= len(available):
        raise ValueError("story must use existing inspected materials")
    seen, seen_bytes, narrated = set(), set(), set()
    scenes = []
    targets = request.get('visual_targets')
    known_targets = validate_targets(targets, {f['id'] for f in evidence['facts']}) if targets is not None else None
    seen_targets = set()
    for order, beat in enumerate(beats):
        expected = {"material_id", "narration", "fact_ids"}
        if known_targets is not None:
            expected.add('visual_target_id')
        if set(beat) != expected:
            raise ValueError("composer cannot invent media, intervals or approvals")
        material = known.get(beat["material_id"])
        if material is None or material["id"] in seen or material["sha256"] in seen_bytes:
            raise ValueError("invented or repeated real material")
        fact_ids = beat["fact_ids"]
        if (not isinstance(fact_ids, list) or not fact_ids
                or len(set(fact_ids)) != len(fact_ids)
                or not set(fact_ids) <= (allowed_facts if contextual else set(material["supported_fact_ids"]))):
            raise ValueError("narration exceeds inspected material support")
        text = beat["narration"]
        if not isinstance(text, str) or not text.strip():
            raise ValueError("empty narration")
        seen.add(material["id"]); seen_bytes.add(material["sha256"]); narrated.update(fact_ids)
        scenes.append({"id": "beat-" + str(order + 1), "material_id": material["id"],
            "narration": text.strip(), "evidence_ids": fact_ids,
            "source_interval": material["source_interval"], "capacity_ms": material["capacity_ms"],
            "contract": {"visual_intent": material["visible_description"],
                         "must_show": [material["visible_description"]], "must_not_show": []}})
        if known_targets is not None:
            target_id = beat['visual_target_id']
            if target_id not in known_targets or target_id not in material.get('matched_visual_targets', {}):
                raise MaterialUnavailable('picture does not show the exact explanatory target')
            target = known_targets[target_id]
            seen_targets.add(target_id)
            scenes[-1]['visual_target_id'] = target_id
            scenes[-1]['contract'] = {'visual_intent': target['must_show'],
                'must_show': [target['must_show'], material['matched_visual_targets'][target_id]],
                'must_not_show': [target['must_not_show']]}
    if known_targets is not None and len(seen_targets) < 2:
        raise MaterialUnavailable('story has no visual variety beyond one composition role')
    if not set(request["required_fact_ids"]) <= narrated:
        raise MaterialUnavailable("story omitted the original required topic coverage")
    # Still photographs may cover narration of any supported length. Video
    # intervals remain bounded by their actual source duration.
    if sum(s["capacity_ms"] for s in scenes) < request["seconds"] * 1000:
        raise MaterialUnavailable("real material cannot cover requested duration without repetition")
    return scenes


def fit_materials(available, draft, minimum=5):
    """Consolidate adjacent identical roles only if a unique assignment fails.

    The exact narration, facts and role remain unchanged. This is bounded
    planning with inspected files, never another model/provider attempt.
    """
    current = deepcopy(draft)
    while True:
        try:
            return match_materials(available, current)
        except MaterialUnavailable:
            if len(current['beats']) <= minimum:
                raise
            for index, (left, right) in enumerate(zip(current['beats'], current['beats'][1:])):
                if (left.get('visual_target_id') is not None
                        and left.get('visual_target_id') == right.get('visual_target_id')
                        and set(left['fact_ids']) == set(right['fact_ids'])):
                    combined = deepcopy(left)
                    combined['narration'] = left['narration'] + ' ' + right['narration']
                    current['beats'][index:index+2] = [combined]
                    current['merged_adjacent_beats'] = current.get('merged_adjacent_beats', 0) + 1
                    break
            else:
                raise


class Producer:
    """One preparation: research -> collect -> inspect -> compose -> review."""
    def __init__(self, root, operations, *, probe=probe_media, max_materials=None):
        self.root = Path(root).resolve()
        self.operations, self.probe, self.max_materials = operations, probe, max_materials

    def prepare(self, topic, language, seconds):
        if language not in {"pl", "en", "ru", "uk"} or seconds not in {15, 30, 45, 60}:
            raise ValueError("unsupported product input")
        if not isinstance(topic, str) or not 1 <= len(topic.strip()) <= 300:
            raise ValueError("bounded topic required")
        request = {"topic": topic.strip(), "language": language, "seconds": seconds}
        modern = getattr(self.operations, "presentation_policy", None) in WHOLE_POLICIES
        if modern:
            request["presentation_policy"] = self.operations.presentation_policy
            if hasattr(self.operations, "visual_validation_mode"):
                request["visual_validation_mode"] = self.operations.visual_validation_mode
                if request["visual_validation_mode"] not in {"metadata", "gemini"}:
                    raise ValueError("unsupported visual validation mode")
        brief = self.operations.research(deepcopy(request))
        # Research defines essential factual scope, never imaginary visual slots.
        if set(brief) not in ({"evidence", "required_fact_ids", "queries"},
                              {"evidence", "required_fact_ids", "queries", "visual_targets"}):
            raise ValueError("research brief must not contain a storyboard")
        evidence = brief["evidence"]
        facts = validate_evidence(evidence)
        required = brief["required_fact_ids"]
        if not required or len(set(required)) != len(required) or not set(required) <= facts.keys():
            raise ValueError("invalid original topic coverage")
        request["required_fact_ids"] = required
        targets = brief.get('visual_targets')
        if targets is not None:
            validate_targets(targets, facts)
            request['visual_targets'] = deepcopy(targets)
        # Discovery is global and topic-bound, not a search for one imagined shot.
        candidates = self.operations.discover(deepcopy(request), deepcopy(brief["queries"]))
        if not isinstance(candidates, list) or len(candidates) > (self.max_materials or (candidate_limit(seconds,request["presentation_policy"]) if modern else 12)):
            raise ValueError("material discovery exceeded server budget")
        assets, available, hashes = {}, [], set()
        batch_size = 4 if modern else 1
        for offset in range(0, len(candidates), batch_size):
            batch = []
            for candidate in candidates[offset:offset + batch_size]:
                try:
                    asset = self.operations.download(deepcopy(candidate))
                except ResourceUnavailable:
                    continue
                validate_material(self.root, asset, self.probe)
                if targets is not None and asset.get('visual_targets') != targets:
                    raise ValueError('download lost the original visual target contract')
                if asset['id'] in assets or any(a['id'] == asset['id'] for a in batch):
                    raise ValueError('duplicate provider identity')
                if asset['sha256'] in hashes:
                    continue
                hashes.add(asset['sha256'])
                batch.append(asset)
            if not batch:
                continue
            receipts = (self.operations.inspect_many(deepcopy(batch), deepcopy(evidence)) if modern
                        else [self.operations.inspect(deepcopy(batch[0]), deepcopy(evidence))])
            if len(receipts) != len(batch):
                raise ValueError('inspection batch omitted an input')
            for asset, receipt in zip(batch, receipts):
                material = inspected_material(asset, receipt, evidence, facts, request.get("visual_validation_mode", "gemini"))
                if material is not None:
                    assets[asset['id']] = asset
                    available.append(material)
            covered_now = set().union(*(set(m['supported_fact_ids']) for m in available)) if available else set()
            target_coverage = set().union(*(set(m.get('matched_visual_targets', {})) for m in available)) if available else set()
            desired = preferred_shots(seconds,request["presentation_policy"]) if modern else min(12, (seconds * 6 + 14) // 15, len(candidates))
            if (len(available) >= desired
                    and (modern or set(required) <= covered_now)
                    and (targets is None or len(target_coverage) >= 2)):
                break
        covered = set().union(*(set(m['supported_fact_ids']) for m in available)) if available else set()
        if not modern and not set(required) <= covered:
            raise MaterialUnavailable('essential topic facts have no inspected real material')
        if modern and len(available) < minimum_shots(seconds,request["presentation_policy"]):
            raise MaterialUnavailable('not enough inspected distinct photographs for requested cadence')
        if targets is not None:
            covered_targets = set().union(*(set(m.get('matched_visual_targets', {})) for m in available))
            if len(covered_targets) < 2:
                raise MaterialUnavailable('different explanatory visuals unavailable; only one composition role')
        if sum(m["capacity_ms"] for m in available) < seconds * 1000:
            raise MaterialUnavailable("inspected real material has insufficient duration")
        composition = {"request": request, "evidence": evidence, "materials": available}
        draft = self.operations.compose(deepcopy(composition))
        if modern:
            draft = match_materials(available, draft, contextual=True)
        else:
            draft = fit_materials(available, draft) if targets is not None else match_materials(available, draft)
        scenes = validate_story(request, evidence, available, draft)
        script = " ".join(s["narration"] for s in scenes)
        review_input = {**request, "script": script, "scenes": scenes,
                        "evidence": evidence, "materials": available}
        review = self.operations.review_script(deepcopy(review_input))
        validate_script_review(evidence, language, script, scenes, review, topic=topic.strip())
        visuals = make_visuals(seconds, available, scenes,request["presentation_policy"]) if modern else None
        selected = {v['material_id'] for v in visuals} if modern else {s['material_id'] for s in scenes}
        payload = {"schema": "material-first", **request, "script": script, "scenes": scenes,
            "assets": [assets[k] for k in sorted(selected)], "evidence": evidence,
            "observations": [m for m in available if m["id"] in selected], "script_review": review}
        if modern:
            payload['visuals'] = visuals
        if draft.get('merged_adjacent_beats'):
            payload['merged_adjacent_beats'] = draft['merged_adjacent_beats']
        frozen = {"payload": payload, "sha256": digest(payload)}
        verify(self.root, frozen, self.probe)
        return frozen


def verify(root, frozen, probe=probe_media):
    payload = frozen["payload"]
    if payload.get("schema") != "material-first" or digest(payload) != frozen.get("sha256"):
        raise ValueError("material-first plan changed")
    if payload.get('presentation_policy') not in {None, *WHOLE_POLICIES}:
        raise ValueError('unsupported frozen presentation policy')
    facts = validate_evidence(payload["evidence"])
    assets = {a["id"]: a for a in payload["assets"]}
    if len(assets) != len(payload["assets"]):
        raise ValueError("duplicate frozen material identity")
    if len({m['id'] for m in payload['observations']}) != len(payload['observations']):
        raise ValueError('duplicate frozen observation identity')
    observations = []
    for original in payload["observations"]:
        asset = assets.get(original["id"])
        if asset is None:
            raise ValueError("observation has no real material")
        if 'visual_targets' in payload and asset.get('visual_targets') != payload['visual_targets']:
            raise ValueError('frozen asset targets differ from the original story targets')
        validate_material(root, asset, probe)
        current = inspected_material(asset, original["inspection"], payload["evidence"], facts, payload.get("visual_validation_mode", "gemini"))
        if current != original:
            raise ValueError("frozen observation changed")
        observations.append(current)
    if payload.get('presentation_policy') in WHOLE_POLICIES:
        validate_visuals(payload, observations)
    beats = [{"material_id": s["material_id"], "narration": s["narration"],
              "fact_ids": s["evidence_ids"]} for s in payload["scenes"]]
    if 'visual_targets' in payload:
        for beat, scene in zip(beats, payload['scenes']):
            beat['visual_target_id'] = scene['visual_target_id']
    if validate_story(payload, payload["evidence"], observations, {"beats": beats}) != payload["scenes"]:
        raise ValueError("frozen story differs from inspected material")
    if " ".join(s["narration"] for s in payload["scenes"]) != payload["script"]:
        raise ValueError("continuous narration changed")
    validate_script_review(payload["evidence"], payload["language"], payload["script"],
                           payload["scenes"], payload["script_review"], topic=payload["topic"])
    return payload
