"""Pre-voice global feasibility. No providers, TTS, database or production writes."""
import argparse
import hashlib
import json
from pathlib import Path


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def plan_visuals(choices):
    if not isinstance(choices, dict) or not choices:
        raise ValueError("nonempty shot-to-reviewed-assets mapping required")
    graph = {}
    for shot, assets in choices.items():
        if not isinstance(shot, str) or not shot or not isinstance(assets, list):
            raise ValueError("invalid shot or asset list")
        if any(not isinstance(asset, str) or not asset for asset in assets):
            raise ValueError("asset identity must be a nonempty string")
        graph[shot] = sorted(set(assets))
    owner = {}

    def augment(shot, seen):
        for asset in graph[shot]:
            if asset in seen:
                continue
            seen.add(asset)
            if asset not in owner or augment(owner[asset], seen):
                owner[asset] = shot
                return True
        return False

    for shot in sorted(graph, key=lambda s: (len(graph[s]), s)):
        augment(shot, set())
    selected = {shot: asset for asset, shot in owner.items()}
    missing = sorted(set(graph) - set(selected))
    witnesses = []
    for root in missing:
        shots, assets, todo = {root}, set(), [root]
        while todo:
            shot = todo.pop()
            for asset in graph[shot]:
                assets.add(asset)
                matched = owner.get(asset)
                if matched is not None and matched not in shots:
                    shots.add(matched)
                    todo.append(matched)
        witness = {"shots": sorted(shots), "assets": sorted(assets),
                   "deficit": len(shots) - len(assets)}
        if witness not in witnesses:
            witnesses.append(witness)
    return {"status": "blocked" if missing else "feasible",
            "required": len(graph), "matched": len(selected),
            "selection": dict(sorted(selected.items())),
            "unmatched": missing, "deficits": witnesses,
            "graph_sha256": hashlib.sha256(canonical(graph)).hexdigest()}


def require_complete_plan(report, choices):
    """Recompute before permitting downstream work; a status flag is insufficient."""
    actual = plan_visuals(choices)
    if report != actual:
        raise ValueError("plan changed or receipt does not match reviewed choices")
    if actual["status"] != "feasible":
        raise ValueError("visual plan infeasible; narration and TTS must not start")
    return actual["selection"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.input.read_text())
    choices = source.get("approved_choices", source)
    report = plan_visuals(choices)
    report["provenance"] = {
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "scope": "feasibility only; imported approvals are not new visual acceptance",
        "provider_calls": 0, "tts_calls": 0, "production_mutations": 0}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "required", "matched", "deficits")}))
    return 2 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
