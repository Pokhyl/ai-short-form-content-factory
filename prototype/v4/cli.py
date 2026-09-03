from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from .director import generate_director
from .schema import parse_director_payload
from .speech import ensure_speech_ready
from .upstream_mpt import synthesize_edge, transcribe_whisper, verify_upstream
from .visual_router import build_visual_manifest

VOICES = {
    "en": "en-US-AndrewNeural",
    "pl": "pl-PL-MarekNeural",
    "ru": "ru-RU-DmitryNeural",
    "uk": "uk-UA-OstapNeural",
}


def load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(path: str, value) -> None:
    out = Path(path); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Product-first V4 direct prototype")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("verify-upstream")

    p = sub.add_parser("validate")
    p.add_argument("director")

    p = sub.add_parser("director")
    p.add_argument("--topic", required=True)
    p.add_argument("--language", choices=sorted(VOICES), required=True)
    p.add_argument("--seconds", type=int, choices=[15,30,45,60], required=True)
    p.add_argument("--evidence", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--provider", default=os.environ.get("V4_LLM_PROVIDER", "ollama"))
    p.add_argument("--model", default=os.environ.get("V4_LLM_MODEL", ""))
    p.add_argument("--base-url", default=os.environ.get("V4_LLM_BASE_URL", ""))

    p = sub.add_parser("voice")
    p.add_argument("director")
    p.add_argument("--output", required=True)

    p = sub.add_parser("transcribe")
    p.add_argument("audio")
    p.add_argument("--output", required=True)

    p = sub.add_parser("manifest")
    p.add_argument("director")
    p.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.cmd == "verify-upstream":
        print(verify_upstream())
        return 0
    if args.cmd == "validate":
        plan = parse_director_payload(load_json(args.director))
        ensure_speech_ready(plan.spoken_script)
        print(f"V4_DIRECTOR_VALID scenes={len(plan.scenes)} facts={len(plan.facts)}")
        return 0
    if args.cmd == "director":
        evidence = load_json(args.evidence)
        if not isinstance(evidence, list):
            raise ValueError("evidence file must contain a JSON array")
        plan = generate_director(topic=args.topic, language=args.language, target_seconds=args.seconds, evidence=evidence, provider=args.provider, model=args.model, base_url=args.base_url)
        dump_json(args.output, asdict(plan))
        print(f"V4_DIRECTOR_CREATED {args.output}")
        return 0
    if args.cmd == "voice":
        plan = parse_director_payload(load_json(args.director))
        duration = synthesize_edge(plan.spoken_script, voice_name=VOICES[plan.language], output_file=args.output)
        print(f"V4_VOICE_CREATED duration={duration:.3f} path={args.output}")
        return 0
    if args.cmd == "transcribe":
        rows = transcribe_whisper(args.audio, args.output)
        print(f"V4_WHISPER_CREATED subtitles={len(rows)} path={args.output}")
        return 0
    if args.cmd == "manifest":
        plan = parse_director_payload(load_json(args.director))
        dump_json(args.output, build_visual_manifest(plan))
        print(f"V4_VISUAL_MANIFEST_CREATED {args.output}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
