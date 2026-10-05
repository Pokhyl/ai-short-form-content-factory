"""Local photo renderer: immutable inputs, natural audio, no provider calls."""
import hashlib
import json
from pathlib import Path
import subprocess
from uuid import UUID


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def run(command, timeout=180):
    return subprocess.run(command, check=True, capture_output=True, text=True, timeout=timeout)


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                          '-of', 'json', str(path)], timeout=20).stdout)


def render(root, job_id, request):
    root = Path(root).resolve()
    job_id = str(UUID(job_id))
    audio = root / 'voiceovers' / job_id / 'final.mp3'
    if sha(audio) != request['input_audio_sha256']:
        raise ValueError('stored natural voice changed')
    actual = round(float(probe(audio)['format']['duration']) * 1000)
    requested, target = request['requested_duration_ms'], request['target_duration_ms']
    if requested not in {15000, 30000, 45000, 60000}:
        raise ValueError('unsupported requested duration')
    if actual != request['audio_duration_ms'] or not requested * .8 <= actual <= requested * 1.2:
        raise ValueError('natural voice outside practical duration window')
    if target != max(requested, actual):
        raise ValueError('render target differs from natural voice contract')
    scenes = request['scenes']
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 12:
        raise ValueError('bounded scenes required')
    # Validate all inputs before creating any render side effect.
    previous, seen, verified = 0, set(), []
    for order, scene in enumerate(scenes, 1):
        if scene['media_type'] != 'photo' or scene['scene_order'] != order:
            raise ValueError('photo story order changed')
        start, end = scene['segment_start_ms'], scene['segment_end_ms']
        if start != previous or not start < end <= target:
            raise ValueError('photo timeline has a gap or overlap')
        if not start <= scene['speech_start_ms'] < scene['speech_end_ms'] <= min(end, actual):
            raise ValueError('speech outside exact photo beat')
        asset = Path(scene['asset_path']).resolve()
        expected = root / 'visuals' / job_id / str(UUID(scene['shot_uuid']))
        if asset.parent != expected or not asset.name.startswith('selected.'):
            raise ValueError('photo outside frozen staged directory')
        observed = sha(asset)
        if observed != scene['asset_sha256'] or observed in seen:
            raise ValueError('changed or repeated photo bytes')
        seen.add(observed); previous = end
        verified.append((scene, asset))
    if previous != target:
        raise ValueError('photos do not cover output timeline')
    directory = root / 'renders' / job_id
    directory.mkdir(parents=True, exist_ok=False)
    work = directory / '.work'
    work.mkdir()
    segments, manifest_segments = [], []
    graph = ('[0:v]scale=1080:1920:force_original_aspect_ratio=increase:force_divisible_by=2,'
             'crop=1080:1920,fps=30,format=yuv420p,setsar=1[v]')
    for index, (scene, asset) in enumerate(verified):
        duration = scene['segment_end_ms'] - scene['segment_start_ms']
        segment = work / f'segment-{index:02d}.mp4'
        run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-loop', '1', '-framerate', '30',
             '-i', str(asset), '-filter_complex_threads', '1', '-filter_complex', graph,
             '-map', '[v]', '-an', '-c:v', 'libx264', '-threads', '1', '-preset', 'veryfast',
             '-crf', '18', '-pix_fmt', 'yuv420p', '-t', f'{duration / 1000:.3f}', str(segment)])
        segments.append(segment)
        manifest_segments.append({'scene_uuid': scene['scene_uuid'], 'shot_uuid': scene['shot_uuid'],
            'visual_asset_id': scene['visual_asset_id'], 'segment_order': index + 1,
            'start_ms': scene['segment_start_ms'], 'end_ms': scene['segment_end_ms'],
            'duration_ms': duration, 'asset_sha256': scene['asset_sha256'], 'media_type': 'photo'})
    concat = work / 'concat.txt'
    concat.write_text(''.join(f"file '{segment}'\n" for segment in segments))
    silent = work / 'video.mp4'
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'concat', '-safe', '0',
         '-i', str(concat), '-c', 'copy', str(silent)])
    final = directory / 'final.mp4'
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(silent), '-i', str(audio),
         '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
         '-t', f'{target / 1000:.3f}', '-movflags', '+faststart', str(final)])
    output = probe(final)
    video = [s for s in output['streams'] if s['codec_type'] == 'video']
    sound = [s for s in output['streams'] if s['codec_type'] == 'audio']
    if (len(output['streams']) != 2 or len(video) != 1 or len(sound) != 1
            or video[0]['width'] != 1080 or video[0]['height'] != 1920
            or video[0]['codec_name'] != 'h264' or sound[0]['codec_name'] != 'aac'
            or abs(round(float(output['format']['duration']) * 1000) - target) > 100):
        raise ValueError('actual rendered media contract failed')
    run(['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-i', str(final), '-f', 'null', '-'])
    result = {'status': 'ready', 'qa_passed': True, 'job_id': job_id, 'sha256': sha(final),
        'storage_path': str(final), 'bytes': final.stat().st_size,
        'input_audio_sha256': request['input_audio_sha256'], 'audio_duration_ms': actual,
        'requested_duration_ms': requested, 'target_duration_ms': target,
        'segments': manifest_segments, 'duration_policy': 'material-first-natural'}
    (directory / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    return result
