"""Strict measured natural-voice duration contract; no tempo or word-slot fitting."""
import math


class NaturalDurationRejected(ValueError):
    pass


def duration_fits(measured_ms, seconds):
    if type(seconds) is not int or seconds not in (15, 30, 45, 60):
        raise ValueError('unsupported requested duration')
    if type(measured_ms) not in (int, float) or not math.isfinite(measured_ms) or measured_ms <= 0:
        raise ValueError('positive finite measured duration required')
    return seconds * 1000 - 1000 <= measured_ms <= seconds * 1000


def revision_word_target(script, measured_ms, seconds):
    """A nonbinding prompt hint; only the *second measured MP3* can pass."""
    duration_fits(measured_ms, seconds)
    if not isinstance(script,str) or not script.strip():
        raise ValueError('nonempty reviewed narration required')
    words=len(script.split())
    estimate=round(words*(seconds*1000-400)/measured_ms)
    return max(1,min(estimate,words*2))


def require_reviewed_revision(original, replacement):
    if not isinstance(replacement,dict):
        raise NaturalDurationRejected('reviewed story object required')
    if not isinstance(replacement.get('script'),str) or not replacement['script'].strip():
        raise NaturalDurationRejected('revised script missing')
    if replacement['script'].strip()==original['script'].strip():
        raise NaturalDurationRejected('duration revision did not change narration')
    if not isinstance(replacement.get('scenes'),list) or not replacement['scenes']:
        raise NaturalDurationRejected('revised source-bound scenes missing')
    review=replacement.get('review')
    if not isinstance(review,dict) or review.get('native_language_quality') is not True:
        raise NaturalDurationRejected('independent revised native review required')
    if not all(isinstance(s,dict) and s.get('narration') and s.get('evidence_ids')
               and s.get('material_id') for s in replacement['scenes']):
        raise NaturalDurationRejected('revised narration lacks evidence or photo anchors')
    return replacement
