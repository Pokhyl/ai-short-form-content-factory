from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from .upstream import bootstrap

DEFAULT_SOURCES = ("pexels", "pixabay_video", "wikimedia", "archive_org")


def _candidate_to_dict(candidate: Any) -> dict[str, Any]:
    if is_dataclass(candidate):
        data = asdict(candidate)
    else:
        keys = (
            "source", "source_id", "source_url", "download_url", "kind",
            "width", "height", "duration", "creator", "license",
            "source_tags", "thumbnail_url", "extra",
        )
        data = {key: getattr(candidate, key, None) for key in keys}
    return data


def discover(
    query: str,
    *,
    kind: str = "video",
    sources: tuple[str, ...] = DEFAULT_SOURCES,
    per_source: int = 6,
    orientation: str | None = None,
    min_width: int | None = None,
) -> dict[str, Any]:
    if not query.strip():
        raise ValueError("query is required")
    if kind not in {"video", "image"}:
        raise ValueError("kind must be video or image")
    bootstrap()
    from tools.video.stock_sources import SearchFilters, get_source

    result: dict[str, Any] = {"query": query.strip(), "kind": kind, "providers": {}}
    for name in sources:
        source = get_source(name)
        if not source.is_available():
            result["providers"][name] = {"active": False, "candidates": [], "error": "provider reports unavailable"}
            continue
        try:
            candidates = source.search(
                query,
                SearchFilters(
                    kind=kind,
                    per_page=max(1, min(int(per_source), 20)),
                    page=1,
                    orientation=orientation,
                    min_width=min_width,
                ),
            )
            result["providers"][name] = {
                "active": True,
                "candidates": [_candidate_to_dict(c) for c in candidates[:per_source]],
                "error": None,
            }
        except Exception as exc:
            result["providers"][name] = {
                "active": False,
                "candidates": [],
                "error": f"{type(exc).__name__}: {exc}",
            }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="V5 asset-first raw provider inventory")
    parser.add_argument("--query", required=True)
    parser.add_argument("--kind", choices=("video", "image"), default="video")
    parser.add_argument("--sources", default=",".join(DEFAULT_SOURCES))
    parser.add_argument("--per-source", type=int, default=6)
    parser.add_argument("--orientation", choices=("portrait", "landscape", "square"))
    parser.add_argument("--min-width", type=int)
    parser.add_argument("--out")
    args = parser.parse_args()
    payload = discover(
        args.query,
        kind=args.kind,
        sources=tuple(x.strip() for x in args.sources.split(",") if x.strip()),
        per_source=args.per_source,
        orientation=args.orientation,
        min_width=args.min_width,
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
