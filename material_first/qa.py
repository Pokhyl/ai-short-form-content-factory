"""Independent final-file audit for whole-photo, exact-duration delivery."""
import json
import math
from pathlib import Path
from .rendering import probe, run, sha
from .presentation import visual_timeline, tempo_factor, phrase_frames, CALM_POLICY
from scripts.audit_final_media import pcm


def audit_whole(root, job_id, payload, expected_hash, expected_voice_hash, *, timings=None):
    directory = Path(root) / 'renders' / job_id
    final, fitted = directory / 'final.mp4', directory / 'fitted.wav'
    source = Path(root) / 'voiceovers' / job_id / 'final.mp3'
    manifest = json.loads((directory / 'manifest.json').read_text())
    info = probe(final)
    v = [s for s in info['streams'] if s['codec_type'] == 'video']
    a = [s for s in info['streams'] if s['codec_type'] == 'audio']
    if len(v) != 1 or len(a) != 1 or len(info['streams']) != 2:
        raise ValueError('unexpected final streams')
    seconds = payload['seconds']
    segments = manifest['segments']
    policy = payload['presentation_policy']
    boundaries = phrase_frames(timings,manifest['audio_duration_ms'],seconds) if policy == CALM_POLICY else ()
    cuts = visual_timeline(seconds, len(payload['visuals']),policy,boundaries)
    expected_assets = {x['sha256'] for x in payload['assets']}
    gates = {
        'exact_duration': all(round(float(d) * 1000) == seconds * 1000
                              for d in [info['format']['duration'], v[0]['duration'], a[0]['duration']]),
        'video_format': (v[0]['width'], v[0]['height'], v[0]['codec_name'], v[0]['pix_fmt'], v[0]['r_frame_rate'])
                        == (1080, 1920, 'h264', 'yuv420p', '30/1'),
        'audio_format': a[0]['codec_name'] == 'aac',
        'frame_count': int(v[0]['nb_frames']) == seconds * 30,
        'original_audio_unchanged': sha(source) == manifest['input_audio_sha256'] == expected_voice_hash,
        'fitted_audio_unchanged': sha(fitted) == manifest['fitted_audio_sha256'],
        'video_sha256': sha(final) == manifest['sha256'] == expected_hash,
        'distinct_photo_count': len(segments) == len(expected_assets) == len(payload['visuals']),
        'reviewed_photo_set': {s['asset_sha256'] for s in segments} == expected_assets,
        'exact_visual_timeline': [{'start_frame': s['start_frame'], 'end_frame': s['end_frame']} for s in segments] == cuts,
        'staged_photo_bytes': all(sha(Path(s['asset_path'])) == s['asset_sha256'] for s in segments),
        'whole_photo_policy': manifest['duration_policy'] == payload['presentation_policy'],
        'tempo_bound': math.isclose(manifest['audio_tempo_factor'], tempo_factor(manifest['audio_duration_ms'] / 1000, seconds)),
    }
    run(['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-i', str(final), '-f', 'null', '-'])
    gates['full_decode'] = True
    left, right = pcm(fitted), pcm(final)
    count = min(len(left), len(right))
    energy = sum(x*x for x in left[:count]) * sum(x*x for x in right[:count])
    correlation = (sum(x*y for x,y in zip(left[:count], right[:count])) / math.sqrt(energy)) if energy else 0
    gates['fitted_narration_preserved'] = correlation >= .99 and abs(len(left)-len(right)) <= 1600
    if not all(gates.values()):
        raise ValueError('whole-photo media audit failed: ' + ','.join(k for k,v in gates.items() if not v))
    return {'passed': True, 'sha256': expected_hash, 'gates': gates,
            'duration_ms': seconds * 1000, 'scene_count': len(segments),
            'audio_correlation': correlation}
