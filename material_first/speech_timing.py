"""Server-owned, voice-specific timing estimates from immutable TTS samples.

An estimate never authorizes stretching audio. Actual duration remains a gate.
Only numeric measurements and hashes are retained, never narration text.
"""
import json
import math
import statistics
from pathlib import Path
from factory_v3.worker_adapters import VOICES


def record_sample(root, job_id, language, text, duration_ms, audio_hash):
    if language not in VOICES or not isinstance(text, str) or not text.strip():
        raise ValueError('invalid speech calibration identity')
    if type(duration_ms) is not int or not 1000 <= duration_ms <= 180000:
        raise ValueError('invalid speech calibration duration')
    locale, voice = VOICES[language]
    sample = {'job_id':str(job_id), 'locale':locale, 'voice':voice,
              'characters':len(text.strip()), 'words':len(text.split()),
              'duration_ms':duration_ms, 'audio_sha256':audio_hash}
    path=Path(root)/'speech-calibration'/voice/(str(job_id)+'.json')
    path.parent.mkdir(parents=True,exist_ok=True)
    # Each case contributes once, including a measured out-of-window voice.
    if path.exists():
        if json.loads(path.read_text()) != sample:raise ValueError('speech calibration changed')
    else:
        with path.open('x') as stream:json.dump(sample,stream)
    return sample


def timing_budget(root, language, seconds):
    if language not in VOICES or type(seconds) is not int or seconds not in {15,30,45,60}:
        raise ValueError('invalid speech timing request')
    locale, voice=VOICES[language]
    directory=Path(root)/'speech-calibration'/voice
    samples=[]
    for path in sorted(directory.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:20]:
        row=json.loads(path.read_text())
        if row['locale'] != locale or row['voice'] != voice:raise ValueError('speech profile voice mismatch')
        duration=row['duration_ms']/1000
        if not 1 <= duration <= 180 or not 0 < row['words'] <= row['characters']:
            raise ValueError('invalid speech profile sample')
        samples.append(row)
    if not samples:return None
    words_rate=statistics.median(s['words']/(s['duration_ms']/1000) for s in samples)
    chars_rate=statistics.median(s['characters']/(s['duration_ms']/1000) for s in samples)
    if not .5 <= words_rate <= 5 or not 3 <= chars_rate <= 50:raise ValueError('implausible speech profile')
    target=seconds-.5
    return {'protocol':'natural-voice-timing-v1','locale':locale,'voice':voice,
            'sample_count':len(samples),'words_per_second':words_rate,'characters_per_second':chars_rate,
            'preferred_words':round(target*words_rate),'preferred_characters':round(target*chars_rate),
            'minimum_words':max(1,math.floor((seconds-1)*words_rate)),
            'maximum_words':math.ceil(seconds*words_rate),
            'minimum_estimated_seconds':seconds-1,'maximum_estimated_seconds':seconds}


def estimated_seconds(text, budget):
    return (len(text.split())/budget['words_per_second'] + len(text.strip())/budget['characters_per_second'])/2


def validate_timing(text, budget, language=None, seconds=None):
    if budget is None:return
    if budget['protocol']!='natural-voice-timing-v1':raise ValueError('unsupported speech timing contract')
    for key in ['words_per_second','characters_per_second']:
        if not isinstance(budget[key],(int,float)) or not math.isfinite(budget[key]) or budget[key] <= 0:
            raise ValueError('invalid natural-voice timing rate')
    if language is not None and (budget['locale'],budget['voice']) != VOICES[language]:
        raise ValueError('natural-voice timing belongs to another voice')
    if seconds is not None and (budget['minimum_estimated_seconds'],budget['maximum_estimated_seconds']) != (seconds-1,seconds):
        raise ValueError('natural-voice timing target changed')
    duration=estimated_seconds(text,budget)
    if not budget['minimum_estimated_seconds'] <= duration <= budget['maximum_estimated_seconds']:
        raise ValueError('narration misses calibrated natural-voice timing before synthesis')


def validate_plan_timing(payload):
    # Measured-feedback plans must be allowed to reach their first measurement;
    # the historical text estimate is guidance, not proof of actual duration.
    if 'voice_correction' in payload:
        from .voice_correction import POLICY
        if payload['voice_correction'] != POLICY:
            raise ValueError('unsupported measured voice correction policy')
        return
    validate_timing(payload['script'],payload.get('speech_timing'),payload['language'],payload['seconds'])
