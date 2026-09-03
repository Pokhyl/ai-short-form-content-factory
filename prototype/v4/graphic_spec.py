from __future__ import annotations

import copy
from typing import Any

ARCHETYPES = {"flow", "merge", "split", "comparison", "layered_stack", "assembly"}
ENTITY_ROLES = {"input", "process", "output", "layer", "subject", "result"}
ENTITY_SHAPES = {"box", "pill", "circle"}
LANES = {"left", "right"}
RELATION_KINDS = {"flow", "joins", "splits", "emits", "blocks", "contains", "transforms"}
FORBIDDEN_GEOMETRY_FIELDS = {
    "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "width", "height",
    "points", "translate", "scale", "rotate", "path", "d",
}


def _text(value: Any, field: str) -> str:
    out = str(value or "").strip()
    if not out:
        raise ValueError(f"{field} is required")
    return out


def _phase(value: Any, field: str) -> int:
    try:
        out = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an integer") from exc
    if out < 0 or out > 20:
        raise ValueError(f"{field} must be between 0 and 20")
    return out


def _reject_raw_geometry(value: Any, path: str = "spec") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_GEOMETRY_FIELDS:
                raise ValueError(f"{path}.{key} is raw geometry and is forbidden in high-level graphic specs")
            _reject_raw_geometry(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_raw_geometry(child, f"{path}[{index}]")


def validate_graphic_spec(spec: Any, *, expected_beat_id: str | None = None) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise ValueError("graphic spec must be an object")
    _reject_raw_geometry(spec)

    beat_id = _text(spec.get("beat_id"), "beat_id")
    if expected_beat_id is not None and beat_id != expected_beat_id:
        raise ValueError(f"graphic spec beat mismatch: {beat_id} != {expected_beat_id}")
    archetype = _text(spec.get("archetype"), "archetype")
    if archetype not in ARCHETYPES:
        raise ValueError(f"invalid graphic archetype: {archetype}")

    raw_entities = spec.get("entities")
    if not isinstance(raw_entities, list) or not raw_entities:
        raise ValueError("entities must be a non-empty array")

    entities: list[dict[str, Any]] = []
    ids: set[str] = set()
    for index, raw in enumerate(raw_entities, 1):
        if not isinstance(raw, dict):
            raise ValueError(f"entities[{index}] must be an object")
        entity_id = _text(raw.get("id"), f"entities[{index}].id")
        if entity_id in ids:
            raise ValueError(f"duplicate entity id: {entity_id}")
        ids.add(entity_id)
        role = _text(raw.get("role"), f"entities[{index}].role")
        if role not in ENTITY_ROLES:
            raise ValueError(f"invalid entity role: {role}")
        shape = str(raw.get("shape") or "box").strip()
        if shape not in ENTITY_SHAPES:
            raise ValueError(f"invalid entity shape: {shape}")
        lane = str(raw.get("lane") or "").strip() or None
        if lane is not None and lane not in LANES:
            raise ValueError(f"invalid entity lane: {lane}")
        order_raw = raw.get("order")
        order = int(order_raw) if order_raw is not None else index - 1
        phase = _phase(raw.get("phase", index - 1), f"entities[{index}].phase")
        entities.append({
            "id": entity_id,
            "label": _text(raw.get("label"), f"entities[{index}].label"),
            "role": role,
            "shape": shape,
            "lane": lane,
            "order": order,
            "phase": phase,
        })

    raw_relations = spec.get("relations", [])
    if not isinstance(raw_relations, list):
        raise ValueError("relations must be an array")
    relations: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_relations, 1):
        if not isinstance(raw, dict):
            raise ValueError(f"relations[{index}] must be an object")
        source = _text(raw.get("from"), f"relations[{index}].from")
        target = _text(raw.get("to"), f"relations[{index}].to")
        if source not in ids or target not in ids:
            raise ValueError(f"relation references unknown entity: {source}->{target}")
        if source == target:
            raise ValueError("relation cannot self-reference")
        kind = str(raw.get("kind") or "flow").strip()
        if kind not in RELATION_KINDS:
            raise ValueError(f"invalid relation kind: {kind}")
        phase = _phase(raw.get("phase", index), f"relations[{index}].phase")
        relations.append({
            "from": source,
            "to": target,
            "kind": kind,
            "label": str(raw.get("label") or "").strip() or None,
            "phase": phase,
        })

    roles = [entity["role"] for entity in entities]
    if archetype == "flow":
        if len(entities) < 2:
            raise ValueError("flow requires at least two entities")
    elif archetype == "merge":
        if roles.count("input") < 2 or not any(role in {"output", "result"} for role in roles):
            raise ValueError("merge requires at least two inputs and one output/result")
    elif archetype == "split":
        if roles.count("input") != 1 or sum(role in {"output", "result"} for role in roles) < 2:
            raise ValueError("split requires one input and at least two outputs/results")
    elif archetype == "comparison":
        lanes = {entity["lane"] for entity in entities}
        if not {"left", "right"}.issubset(lanes):
            raise ValueError("comparison requires entities in both left and right lanes")
    elif archetype == "layered_stack":
        if sum(role == "layer" for role in roles) < 2:
            raise ValueError("layered_stack requires at least two layer entities")
    elif archetype == "assembly":
        if sum(role in {"input", "subject"} for role in roles) < 2 or not any(role in {"result", "output"} for role in roles):
            raise ValueError("assembly requires at least two inputs/subjects and one result/output")

    return {
        "beat_id": beat_id,
        "archetype": archetype,
        "title": str(spec.get("title") or "").strip() or None,
        "entities": entities,
        "relations": relations,
    }


def validate_graphic_spec_map(spec_map: Any, constructed_beat_ids: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(spec_map, dict):
        raise ValueError("graphic spec map must be an object keyed by beat_id")
    expected = set(constructed_beat_ids)
    actual = set(spec_map)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        raise ValueError(f"missing graphic specs for constructed beats: {missing}")
    if extra:
        raise ValueError(f"graphic specs contain non-constructed/unknown beats: {extra}")
    return {beat_id: validate_graphic_spec(copy.deepcopy(spec_map[beat_id]), expected_beat_id=beat_id) for beat_id in constructed_beat_ids}
