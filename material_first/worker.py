"""Photo fallback bridge to the existing continuous-voice renderer.

Photo plans use local rendering and a practical natural-voice duration window.
Source-video interval rendering remains a separate adapter boundary.
"""
from copy import deepcopy
from factory_v3.worker_adapters import WorkerAdapters
from factory_v3.executor import Executor
from .engine import verify
from .rendering import render


class PhotoWorker(WorkerAdapters):
    def _duration_window(self, payload):
        return round(payload["seconds"] * 800), round(payload["seconds"] * 1200)

    def _post(self, path, payload, timeout=60):
        if path.startswith("/renders/"):
            return render(self.root, path.removeprefix("/renders/"), payload)
        return super()._post(path, payload, timeout)

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
                            expected_scenes=len(payload["scenes"]), audio_window=self._duration_window(payload))
        if result.get("passed") is not True or result.get("sha256") != outputs["render"]["sha256"]:
            raise ValueError("actual final media audit failed")
        return {"status": "ready", "machine_pass": True, "human_pass": False, **result}


def executor(ledger, media_root, adapters):
    return Executor(ledger, media_root, adapters, verifier=verify)
