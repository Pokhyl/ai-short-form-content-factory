from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .speech import ensure_speech_ready

PURPOSES = {"hook", "explain", "proof", "example", "transition", "close"}
VISUAL_MODES = {"exact_media", "stock", "diagram", "screen_text", "generated_image"}


def _text(value: Any, field: str) -> str:
    out = str(value or "").strip()
    if not out:
        raise ValueError(f"{field} is required")
    return out


def _string_list(value: Any, field: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    out = tuple(str(item).strip() for item in value if str(item).strip())
    if not allow_empty and not out:
        raise ValueError(f"{field} must not be empty")
    return out


@dataclass(frozen=True)
class Fact:
    fact_id: str
    claim: str
    source_urls: tuple[str, ...]


@dataclass(frozen=True)
class Scene:
    scene_id: str
    narration: str
    purpose: str
    visual_mode: str
    visual_query: str
    must_show: tuple[str, ...]
    must_not_show: tuple[str, ...]
    source_refs: tuple[str, ...]
    on_screen_text: str | None


@dataclass(frozen=True)
class DirectorPlan:
    topic: str
    language: str
    target_seconds: int
    hook: str
    spoken_script: str
    facts: tuple[Fact, ...]
    scenes: tuple[Scene, ...]


def parse_director_payload(payload: Any) -> DirectorPlan:
    if not isinstance(payload, dict):
        raise ValueError("director payload must be an object")
    topic = _text(payload.get("topic"), "topic")
    language = _text(payload.get("language"), "language").lower()
    if language not in {"en", "pl", "ru", "uk"}:
        raise ValueError("language must be en/pl/ru/uk")
    target_seconds = int(payload.get("target_seconds") or 0)
    if target_seconds not in {15, 30, 45, 60}:
        raise ValueError("target_seconds must be 15/30/45/60")
    hook = ensure_speech_ready(_text(payload.get("hook"), "hook"))
    spoken_script = ensure_speech_ready(_text(payload.get("spoken_script"), "spoken_script"))

    raw_facts = payload.get("facts")
    if not isinstance(raw_facts, list) or not raw_facts:
        raise ValueError("facts must be a non-empty array")
    facts: list[Fact] = []
    seen_fact_ids: set[str] = set()
    for index, raw in enumerate(raw_facts, 1):
        if not isinstance(raw, dict):
            raise ValueError(f"facts[{index}] must be an object")
        fact_id = _text(raw.get("fact_id"), f"facts[{index}].fact_id")
        if fact_id in seen_fact_ids:
            raise ValueError(f"duplicate fact_id: {fact_id}")
        seen_fact_ids.add(fact_id)
        facts.append(Fact(fact_id, _text(raw.get("claim"), f"facts[{index}].claim"), _string_list(raw.get("source_urls"), f"facts[{index}].source_urls")))

    raw_scenes = payload.get("scenes")
    if not isinstance(raw_scenes, list) or not raw_scenes:
        raise ValueError("scenes must be a non-empty array")
    scenes: list[Scene] = []
    seen_scene_ids: set[str] = set()
    for index, raw in enumerate(raw_scenes, 1):
        if not isinstance(raw, dict):
            raise ValueError(f"scenes[{index}] must be an object")
        scene_id = _text(raw.get("scene_id"), f"scenes[{index}].scene_id")
        if scene_id in seen_scene_ids:
            raise ValueError(f"duplicate scene_id: {scene_id}")
        seen_scene_ids.add(scene_id)
        narration = ensure_speech_ready(_text(raw.get("narration"), f"scenes[{index}].narration"))
        purpose = _text(raw.get("purpose"), f"scenes[{index}].purpose")
        if purpose not in PURPOSES:
            raise ValueError(f"invalid scene purpose: {purpose}")
        visual_mode = _text(raw.get("visual_mode"), f"scenes[{index}].visual_mode")
        if visual_mode not in VISUAL_MODES:
            raise ValueError(f"invalid visual_mode: {visual_mode}")
        visual_query = str(raw.get("visual_query") or "").strip()
        must_show = _string_list(raw.get("must_show", []), f"scenes[{index}].must_show", allow_empty=visual_mode in {"screen_text"})
        must_not_show = _string_list(raw.get("must_not_show", []), f"scenes[{index}].must_not_show", allow_empty=True)
        source_refs = _string_list(raw.get("source_refs"), f"scenes[{index}].source_refs")
        unknown_refs = [ref for ref in source_refs if ref not in seen_fact_ids]
        if unknown_refs:
            raise ValueError(f"scene {scene_id} references unknown facts: {unknown_refs}")
        if visual_mode in {"stock", "exact_media", "generated_image"} and not visual_query:
            raise ValueError(f"scene {scene_id} requires visual_query for mode {visual_mode}")
        on_screen_text = str(raw.get("on_screen_text") or "").strip() or None
        scenes.append(Scene(scene_id, narration, purpose, visual_mode, visual_query, must_show, must_not_show, source_refs, on_screen_text))

    reconstructed = " ".join(scene.narration for scene in scenes)
    if reconstructed != spoken_script:
        raise ValueError("scene narration must reconstruct spoken_script exactly")
    if scenes[0].purpose != "hook":
        raise ValueError("first scene must be hook")

    return DirectorPlan(topic, language, target_seconds, hook, spoken_script, tuple(facts), tuple(scenes))
