from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .schema import DirectorPlan


def build_visual_manifest(plan: DirectorPlan) -> list[dict[str, Any]]:
    """Translate director scenes into explicit production obligations.

    No scene is silently changed to stock.  Diagram/card/exact obligations stay
    explicit so a missing provider result cannot become unrelated b-roll.
    """
    manifest: list[dict[str, Any]] = []
    for index, scene in enumerate(plan.scenes, 1):
        item = asdict(scene)
        item["sequence"] = index
        item["production_adapter"] = {
            "stock": "moneyprinterturbo.material.download_videos",
            "exact_media": "exact-media-adapter",
            "diagram": "remotion-diagram",
            "screen_text": "remotion-card",
            "generated_image": "optional-local-image-provider",
        }[scene.visual_mode]
        manifest.append(item)
    return manifest


def stock_terms(plan: DirectorPlan) -> list[str]:
    return [scene.visual_query for scene in plan.scenes if scene.visual_mode == "stock"]
