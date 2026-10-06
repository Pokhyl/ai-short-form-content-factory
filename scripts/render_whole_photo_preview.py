"""Render a separate viewing artifact from a reviewed, byte-bound local plan.

python -m scripts.render_whole_photo_preview MEDIA_ROOT PLAN_JSON FRESH_UUID
No provider calls, production ledger changes, or automatic/HUMAN acceptance.
Plan: seconds, audio={path,sha256}, photos=[{path,sha256},...].
Paths are relative to MEDIA_ROOT. The original photographs must be selected
and inspected before this tool is invoked.
"""
import json
import sys
from pathlib import Path
from uuid import UUID

from material_first.presentation import render_whole_photos
from material_first.rendering import sha


def verified_file(root, entry):
    relative = Path(entry['path'])
    if relative.is_absolute():
        raise ValueError('plan paths must be relative to media root')
    file = (root / relative).resolve()
    if not file.is_relative_to(root) or not file.is_file():
        raise ValueError('plan file outside media root or missing')
    if sha(file) != entry['sha256']:
        raise ValueError('reviewed file bytes changed')
    return file


def main():
    root = Path(sys.argv[1]).resolve()
    plan = json.loads(Path(sys.argv[2]).read_text())
    artifact_id = str(UUID(sys.argv[3]))
    audio = verified_file(root, plan['audio'])
    photos = [verified_file(root, p) for p in plan['photos']]
    directory = root / 'whole-photo-previews' / artifact_id
    proof = render_whole_photos(directory, audio, photos, plan['seconds'])
    proof.update({'artifact_id': artifact_id, 'mode': 'manual_cached_assembly',
                  'automatic_product': False, 'production_job_pass': False,
                  'human_pass': False, 'audio_listening_claim': False,
                  'new_search_calls': 0, 'new_model_calls': 0, 'new_tts_calls': 0})
    (directory / 'proof.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps({'output': str(directory / 'final.mp4'), 'proof': proof}))


if __name__ == '__main__':
    main()
