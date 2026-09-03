from __future__ import annotations

import copy
from typing import Any

from .graphic_spec import validate_graphic_spec_map

CANVAS_W = 720
CANVAS_H = 1280


def _phase_range(phase: int, max_phase: int, duration: float) -> list[float]:
    if max_phase <= 0:
        return [0.0, min(duration, 0.55)]
    usable = max(0.6, duration - 0.7)
    start = min(duration - 0.25, phase / (max_phase + 1) * usable)
    end = min(duration, start + min(0.65, max(0.3, duration * 0.12)))
    return [round(start, 3), round(end, 3)]


def _wrap_label(label: str, max_chars: int = 18) -> list[str]:
    words = label.split()
    if not words:
        return [label]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    if len(lines) <= 3:
        return lines
    return [lines[0], lines[1], " ".join(lines[2:])]


def _box_elements(entity: dict[str, Any], x: float, y: float, *, enter: list[float], width: int = 240, height: int = 118) -> list[dict[str, Any]]:
    shape = entity["shape"]
    if shape == "circle":
        base = {"id": f"{entity['id']}-shape", "type": "circle", "cx": x, "cy": y, "r": 66,
                "fill": "#152238", "stroke": "#75D7FF", "strokeWidth": 4, "enter": enter, "from": {"scale": 0.72, "opacity": 0}}
    else:
        rx = 58 if shape == "pill" else 18
        base = {"id": f"{entity['id']}-shape", "type": "rect", "x": x - width/2, "y": y - height/2,
                "width": width, "height": height, "rx": rx, "fill": "#152238", "stroke": "#75D7FF", "strokeWidth": 4,
                "enter": enter, "from": {"scale": 0.86, "opacity": 0}}
    lines = _wrap_label(entity["label"])
    font_size = 25 if len(lines) > 1 else 28
    line_gap = font_size + 5
    first_y = y - ((len(lines) - 1) * line_gap) / 2 + 9
    labels = [{"id": f"{entity['id']}-label-{index}", "type": "text", "x": x, "y": first_y + index * line_gap,
               "text": line, "fontSize": font_size, "fontWeight": 700, "fill": "#F7FAFC",
               "enter": enter, "from": {"opacity": 0}} for index, line in enumerate(lines)]
    return [base, *labels]


def _spread_x(count: int) -> list[float]:
    if count <= 0:
        return []
    if count == 1:
        return [360]
    if count == 2:
        return [180, 540]
    if count == 3:
        return [120, 360, 600]
    return [90 + i * (540 / (count - 1)) for i in range(count)]


def _layout_positions(spec: dict[str, Any]) -> dict[str, tuple[float, float]]:
    entities = spec["entities"]
    kind = spec["archetype"]
    positions: dict[str, tuple[float, float]] = {}

    if kind in {"flow", "layered_stack"}:
        ordered = sorted(entities, key=lambda e: (e["order"], e["id"]))
        top, bottom = 280, 1030
        step = (bottom - top) / max(1, len(ordered) - 1)
        for i, entity in enumerate(ordered):
            positions[entity["id"]] = (360, top + i * step)
    elif kind == "comparison":
        for lane, x in (("left", 190), ("right", 530)):
            lane_entities = sorted([e for e in entities if e["lane"] == lane], key=lambda e: (e["order"], e["id"]))
            top, bottom = 300, 1000
            step = (bottom - top) / max(1, len(lane_entities) - 1)
            for i, entity in enumerate(lane_entities):
                positions[entity["id"]] = (x, top + i * step)
    elif kind in {"merge", "assembly"}:
        inputs = [e for e in entities if e["role"] in {"input", "subject"}]
        middle = [e for e in entities if e["role"] == "process"]
        outputs = [e for e in entities if e["role"] in {"output", "result"}]
        xs = _spread_x(len(inputs))
        for entity, x in zip(inputs, xs):
            positions[entity["id"]] = (x, 340)
        for i, entity in enumerate(middle):
            positions[entity["id"]] = (360, 620 + i * 150)
        for i, entity in enumerate(outputs):
            positions[entity["id"]] = (360, 980 + i * 130)
    elif kind == "split":
        inputs = [e for e in entities if e["role"] == "input"]
        middle = [e for e in entities if e["role"] == "process"]
        outputs = [e for e in entities if e["role"] in {"output", "result"}]
        positions[inputs[0]["id"]] = (360, 300)
        for i, entity in enumerate(middle):
            positions[entity["id"]] = (360, 540 + i * 150)
        xs = _spread_x(len(outputs))
        for entity, x in zip(outputs, xs):
            positions[entity["id"]] = (x, 960)
    else:
        raise ValueError(f"unsupported archetype: {kind}")
    return positions


def compile_graphic_spec(spec: dict[str, Any], duration_seconds: float) -> dict[str, Any]:
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")
    positions = _layout_positions(spec)
    phases = [e["phase"] for e in spec["entities"]] + [r["phase"] for r in spec["relations"]]
    max_phase = max(phases, default=0)
    elements: list[dict[str, Any]] = []

    for entity in spec["entities"]:
        x, y = positions[entity["id"]]
        enter = _phase_range(entity["phase"], max_phase, duration_seconds)
        elements.extend(_box_elements(entity, x, y, enter=enter))

    for index, relation in enumerate(spec["relations"], 1):
        sx, sy = positions[relation["from"]]
        tx, ty = positions[relation["to"]]
        draw = _phase_range(relation["phase"], max_phase, duration_seconds)
        elements.append({
            "id": f"relation-{index}-{relation['from']}-{relation['to']}",
            "type": "line", "x1": sx, "y1": sy + 58, "x2": tx, "y2": ty - 58,
            "stroke": "#FFB454", "strokeWidth": 6, "arrow": True, "draw": draw,
        })
        if relation.get("label"):
            elements.append({
                "id": f"relation-{index}-label", "type": "text", "x": (sx+tx)/2, "y": (sy+ty)/2 - 16,
                "text": relation["label"], "fontSize": 22, "fontWeight": 600, "fill": "#FFDBA8",
                "enter": draw, "from": {"opacity": 0},
            })

    return {
        "durationSeconds": round(duration_seconds, 3),
        "background": "#08111F",
        "title": spec.get("title"),
        "elements": elements,
        "source": {
            "beat_id": spec["beat_id"],
            "archetype": spec["archetype"],
            "compiler": "graphic_compiler_v1",
        },
    }


def compile_timeline_graphics(resolved_timeline: dict[str, Any], spec_map: Any) -> dict[str, Any]:
    out = copy.deepcopy(resolved_timeline)
    beats = out.get("beats")
    if not isinstance(beats, list) or not beats:
        raise ValueError("resolved timeline requires beats")
    constructed = [str(b.get("beat_id") or "") for b in beats if (b.get("primary_visual") or {}).get("source_class") == "constructed"]
    validated = validate_graphic_spec_map(spec_map, constructed)
    compiled_count = 0
    for beat in beats:
        beat_id = str(beat.get("beat_id") or "")
        if beat_id not in validated:
            continue
        duration = float(beat.get("end_seconds") or 0) - float(beat.get("start_seconds") or 0)
        beat["compiled_graphic"] = compile_graphic_spec(validated[beat_id], duration)
        beat["construction_required"] = False
        compiled_count += 1
    out["graphic_compilation"] = {
        "compiled_constructed_beats": compiled_count,
        "all_constructed_beats_compiled": compiled_count == len(constructed),
        "compiler": "graphic_compiler_v1",
    }
    return out
