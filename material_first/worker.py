"""Photo fallback bridge to the existing continuous-voice renderer.

Video interval rendering is a separate adapter boundary: this bridge accepts
photo-only plans, rather than letting the legacy worker silently loop clips.
"""
from copy import deepcopy
from factory_v3.worker_adapters import WorkerAdapters
from factory_v3.executor import Executor
from .engine import verify


class PhotoWorker(WorkerAdapters):
    def _validate_scene_count(self, payload):
        if payload.get("schema") != "material-first" or not payload.get("scenes"):
            raise ValueError("material-first story required")
        if any(a.get("media_type") != "photo" for a in payload["assets"]):
            raise ValueError("photo fallback adapter requires photographs")

    def _stage_photos(self, job_id, payload):
        projected = deepcopy(payload)
        projected["selection"] = {s["id"]: s["material_id"] for s in payload["scenes"]}
        return super()._stage_photos(job_id, projected)

    def qa(self, job_id, payload, outputs):
        result = self.audit(job_id, payload["seconds"], self.root,
                            expected_scenes=len(payload["scenes"]))
        if result.get("passed") is not True or result.get("sha256") != outputs["render"]["sha256"]:
            raise ValueError("actual final media audit failed")
        return {"status": "ready", "machine_pass": True, "human_pass": False, **result}


def executor(ledger, media_root, adapters):
    return Executor(ledger, media_root, adapters, verifier=verify)
