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
from .timeline_builder import compile_segment_timeline, sha256_file
from .timeline_contract import validate_timeline_payload
from .commons_media import fetch_commons_file
from .asset_resolver import resolve_timeline_assets
from .graphic_compiler import compile_timeline_graphics
from .render_manifest import assemble_render_manifest
from .render_bundle import stage_render_bundle

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

    p = sub.add_parser("compile-timeline")
    p.add_argument("--script", required=True)
    p.add_argument("--audio", required=True)
    p.add_argument("--whisper", required=True)
    p.add_argument("--visual-obligations", required=True)
    p.add_argument("--output", required=True)

    p = sub.add_parser("validate-timeline")
    p.add_argument("timeline")

    p = sub.add_parser("fetch-commons")
    p.add_argument("--title", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--max-width", type=int, default=1440)

    p = sub.add_parser("resolve-assets")
    p.add_argument("--timeline", required=True)
    p.add_argument("--asset-map", required=True)
    p.add_argument("--output", required=True)

    p = sub.add_parser("compile-graphics")
    p.add_argument("--resolved-timeline", required=True)
    p.add_argument("--graphic-specs", required=True)
    p.add_argument("--output", required=True)

    p = sub.add_parser("build-render-manifest")
    p.add_argument("--compiled-timeline", required=True)
    p.add_argument("--whisper", required=True)
    p.add_argument("--audio", required=True)
    p.add_argument("--output", required=True)

    p = sub.add_parser("stage-render-bundle")
    p.add_argument("--manifest", required=True)
    p.add_argument("--output-dir", required=True)

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
    if args.cmd == "compile-timeline":
        script_text = Path(args.script).read_text(encoding="utf-8").strip()
        whisper = load_json(args.whisper)
        obligations = load_json(args.visual_obligations)
        if not isinstance(obligations, list):
            raise ValueError("visual obligations file must contain a JSON array")
        timeline = compile_segment_timeline(
            whisper_payload=whisper,
            visual_obligations=obligations,
            script_text=script_text,
            audio_sha256=sha256_file(args.audio),
        )
        dump_json(args.output, timeline)
        print(f"V4_TIMELINE_CREATED beats={len(timeline['beats'])} duration={timeline['duration_seconds']:.3f} path={args.output}")
        return 0
    if args.cmd == "validate-timeline":
        result = validate_timeline_payload(load_json(args.timeline))
        print(f"V4_TIMELINE_VALID beats={result['beat_count']} duration={result['duration_seconds']:.3f}")
        return 0
    if args.cmd == "fetch-commons":
        item = fetch_commons_file(args.title, args.output_dir, max_width=args.max_width)
        print(
            f"V4_COMMONS_FETCHED title={item['file_title']} "
            f"size={item['selected_width']}x{item['selected_height']} "
            f"license={item['license']} sha256={item['sha256']} path={item['local_path']}"
        )
        return 0
    if args.cmd == "resolve-assets":
        resolved = resolve_timeline_assets(load_json(args.timeline), load_json(args.asset_map))
        dump_json(args.output, resolved)
        info = resolved['asset_resolution']
        print(
            f"V4_ASSETS_RESOLVED exact={info['exact_resolved']} "
            f"constructed={info['constructed_required']} path={args.output}"
        )
        return 0
    if args.cmd == "compile-graphics":
        compiled = compile_timeline_graphics(load_json(args.resolved_timeline), load_json(args.graphic_specs))
        dump_json(args.output, compiled)
        info = compiled['graphic_compilation']
        print(
            f"V4_GRAPHICS_COMPILED constructed={info['compiled_constructed_beats']} "
            f"all={info['all_constructed_beats_compiled']} path={args.output}"
        )
        return 0
    if args.cmd == "build-render-manifest":
        manifest = assemble_render_manifest(
            load_json(args.compiled_timeline),
            load_json(args.whisper),
            audio_path=args.audio,
        )
        dump_json(args.output, manifest)
        print(
            f"V4_RENDER_MANIFEST_CREATED beats={len(manifest['visual_track'])} "
            f"captions={len(manifest['captions']['items'])} duration={manifest['duration_seconds']:.3f} path={args.output}"
        )
        return 0
    if args.cmd == "stage-render-bundle":
        proof = stage_render_bundle(load_json(args.manifest), args.output_dir)
        print(
            f"V4_RENDER_BUNDLE_STAGED exact={proof['exact_assets']} graphics={proof['motion_graphics']} "
            f"public={proof['public_dir']} props={proof['props_path']}"
        )
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
