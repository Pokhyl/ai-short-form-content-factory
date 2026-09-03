from __future__ import annotations

import json
from typing import Any

from .schema import DirectorPlan, parse_director_payload
from .upstream_mpt import director_response


def build_director_prompt(*, topic: str, language: str, target_seconds: int, evidence: list[dict[str, Any]]) -> str:
    evidence_json = json.dumps(evidence, ensure_ascii=False, indent=2)
    return f"""# Role: Short-form video director and factual scriptwriter

Create ONE coherent vertical-video plan for this topic:
{topic}

Language: {language}
Target duration: about {target_seconds} seconds.

Use only facts supported by EVIDENCE below. Paraphrase them naturally; do NOT copy encyclopedia wording as speech.

SPEECH RULES:
- spoken_script and every scene narration must sound natural when read aloud by TTS;
- spell every number, range, percentage, unit and abbreviation as ordinary spoken words in {language};
- do not use digits, measurement abbreviations, acronym spellings, URLs, parentheses or editorial stress marks in spoken text;
- use short conversational sentences and natural pauses;
- scenes.narration joined with one space MUST exactly equal spoken_script.

VISUAL RULES:
- plan visuals semantically from the whole idea, not fragments of individual words;
- choose visual_mode from: exact_media, stock, diagram, screen_text, generated_image;
- mechanism/process/technical explanation should normally use diagram or exact_media, not generic lifestyle stock;
- stock is allowed only when contextual real footage actually communicates the scene;
- visual_query is an English retrieval prompt for stock/exact/generated modes;
- must_show states what a viewer must visibly see; must_not_show prevents misleading substitutions;
- never choose generic fallback footage unrelated to the claim.

Return raw JSON only, no markdown. Schema:
{{
  "topic": "...",
  "language": "{language}",
  "target_seconds": {target_seconds},
  "hook": "speech-ready hook",
  "spoken_script": "all scene narration joined by one space",
  "facts": [{{"fact_id":"F1","claim":"...","source_urls":["https://..."]}}],
  "scenes": [
    {{
      "scene_id":"S1",
      "narration":"...",
      "purpose":"hook|explain|proof|example|transition|close",
      "visual_mode":"exact_media|stock|diagram|screen_text|generated_image",
      "visual_query":"English query or empty for diagram/screen_text",
      "must_show":["..."],
      "must_not_show":["..."],
      "source_refs":["F1"],
      "on_screen_text":"optional"
    }}
  ]
}}

EVIDENCE:
{evidence_json}
""".strip()


def parse_json_response(text: str) -> dict[str, Any]:
    value = str(text or "").strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        value = "\n".join(lines).strip()
    payload = json.loads(value)
    if not isinstance(payload, dict):
        raise ValueError("director response must be a JSON object")
    return payload


def generate_director(*, topic: str, language: str, target_seconds: int, evidence: list[dict[str, Any]], provider: str, model: str, base_url: str = "") -> DirectorPlan:
    prompt = build_director_prompt(topic=topic, language=language, target_seconds=target_seconds, evidence=evidence)
    raw = director_response(prompt, provider=provider, model=model, base_url=base_url)
    return parse_director_payload(parse_json_response(raw))
