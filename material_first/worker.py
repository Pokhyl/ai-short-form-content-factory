"""Photo fallback bridge to the existing continuous-voice renderer.

New plans use whole photographs, independent visual cuts and natural-speed voice with at most one second of trailing silence.
Source-video interval rendering remains a separate adapter boundary.
"""
from copy import deepcopy
from pathlib import Path
from factory_v3.worker_adapters import WorkerAdapters
from factory_v3.executor import Executor
from .engine import verify
from .rendering import render, sha
from .presentation import render_whole_photos, visual_timeline
from .visuals import POLICY, CALM_POLICY, WHOLE_POLICIES, ordered_visuals
from .qa import audit_whole
from factory_v3.worker_adapters import identity
import json


class PhotoWorker(WorkerAdapters):
    def _duration_window(self, payload):
        if payload.get('presentation_policy') in WHOLE_POLICIES:
            return payload['seconds'] * 1000 - 1000, payload['seconds'] * 1000
        return round(payload["seconds"] * 800), round(payload["seconds"] * 1200)

    def voice(self, job_id, payload, outputs, before_send):
        from .speech_timing import validate_timing
        validate_timing(payload['script'], payload.get('speech_timing'), payload['language'], payload['seconds'])
        return super().voice(job_id, payload, outputs, before_send)

    def _voice_measurement(self, job_id, payload, result):
        from .speech_timing import record_sample
        record_sample(self.root, job_id, payload['language'], payload['script'],
                      result['duration_ms'], result['sha256'])

    def _post(self, path, payload, timeout=60):
        if path.startswith("/renders/"):
            return render(self.root, path.removeprefix("/renders/"), payload)
        return super()._post(path, payload, timeout)

    def _validate_scene_count(self, payload):
        if payload.get("schema") != "material-first" or not payload.get("scenes"):
            raise ValueError("material-first story required")
        if payload.get("presentation_policy") in WHOLE_POLICIES:
            visual_timeline(payload["seconds"], len(payload["visuals"]),payload["presentation_policy"])
        if any(a.get("media_type") != "photo" for a in payload["assets"]):
            raise ValueError("photo fallback adapter requires photographs")

    def _stage_photos(self, job_id, payload):
        projected = deepcopy(payload)
        if payload.get('presentation_policy') in WHOLE_POLICIES:
            projected['scenes'] = payload['visuals']
        projected["selection"] = {s["id"]: s["material_id"] for s in projected["scenes"]}
        return super()._stage_photos(job_id, projected)

    def render(self, job_id, payload, outputs):
        if payload.get('presentation_policy') not in WHOLE_POLICIES:
            return super().render(job_id, payload, outputs)
        voice, alignment = outputs['voice'], outputs['align']
        source = self.root / 'voiceovers' / job_id / 'final.mp3'
        if sha(source) != voice['sha256'] or alignment['audio_sha256'] != voice['sha256']:
            raise ValueError('voice identity changed before fitted render')
        ordered = ordered_visuals(payload, alignment['scene_timings'], voice['duration_ms'])
        staged = voice['staged_photos']
        assets = {a['id']: a for a in payload['assets']}
        photos = []
        for visual in ordered:
            photo = staged[visual['id']]
            expected = assets[visual['material_id']]['sha256']
            if photo['asset_sha256'] != expected or sha(Path(photo['path'])) != expected:
                raise ValueError('staged visual differs from frozen reviewed photograph')
            photos.append(photo['path'])
        directory = self.root / 'renders' / job_id
        proof = render_whole_photos(directory, source, photos, payload['seconds'], policy=payload['presentation_policy'], timeline=[{k:v[k] for k in ('start_frame','end_frame')} for v in ordered])
        if proof['source_audio_duration_ms'] != voice['duration_ms']:
            raise ValueError('stored voice duration changed')
        segments = []
        for order, visual in enumerate(ordered, 1):
            photo = staged[visual['id']]
            segments.append({**visual, 'segment_order': order,
                'scene_uuid': identity(job_id, 'scene', visual['narration_scene_id']),
                'shot_uuid': photo['shot_uuid'], 'visual_asset_id': photo['visual_asset_id'],
                'asset_path': photo['path'], 'asset_sha256': photo['asset_sha256'],
                'media_type': 'photo', 'start_ms': visual['start_frame'] * 1000 / 30,
                'end_ms': visual['end_frame'] * 1000 / 30})
        final = directory / 'final.mp4'
        result = {'status': 'ready', 'qa_passed': True, 'job_id': job_id,
            'sha256': proof['video_sha256'], 'storage_path': str(final), 'bytes': final.stat().st_size,
            'input_audio_sha256': voice['sha256'], 'audio_duration_ms': voice['duration_ms'],
            'fitted_audio_sha256': proof['fitted_audio_sha256'], 'audio_tempo_factor': proof['audio_tempo_factor'],
            'requested_duration_ms': payload['seconds'] * 1000, 'target_duration_ms': payload['seconds'] * 1000,
            'actual_duration_ms': proof['actual_duration_ms'], 'frame_count': proof['frame_count'],
            'shot_count': proof['shot_count'], 'framing': proof['framing'],
            'segments': segments, 'duration_policy': payload['presentation_policy']}
        (directory / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
        return result

    def qa(self, job_id, payload, outputs):
        if payload.get('presentation_policy') in WHOLE_POLICIES:
            result = audit_whole(self.root, job_id, payload, outputs['render']['sha256'], outputs['voice']['sha256'], timings=outputs['align']['scene_timings'])
            return {'status': 'ready', 'machine_pass': True, 'human_pass': False, **result}
        result = self.audit(job_id, payload["seconds"], self.root,
                            expected_scenes=len(payload["scenes"]), audio_window=self._duration_window(payload))
        if result.get("passed") is not True or result.get("sha256") != outputs["render"]["sha256"]:
            raise ValueError("actual final media audit failed")
        return {"status": "ready", "machine_pass": True, "human_pass": False, **result}


def executor(ledger, media_root, adapters):
    return Executor(ledger, media_root, adapters, verifier=verify)
