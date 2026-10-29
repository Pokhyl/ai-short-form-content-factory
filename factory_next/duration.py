"""Strict measured natural-voice duration contract; no tempo or word-slot fitting."""
import math


class NaturalDurationRejected(ValueError):
    pass


def duration_fits(measured_ms, seconds):
    if type(seconds) is not int or seconds not in (15, 30, 45, 60):
        raise ValueError('unsupported requested duration')
    if type(measured_ms) not in (int, float) or not math.isfinite(measured_ms) or measured_ms <= 0:
        raise ValueError('positive finite measured duration required')
    return seconds * 1000 - 2100 <= measured_ms <= seconds * 1000


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


def revision_length_window(script, measured_ms, seconds, *, centered=False):
    """Bound a draft *before* a metered voice attempt; audio remains authoritative.

    Word count alone did not protect the real UK45 run: a 91-word hint
    produced 161 words and 83.616 seconds. Character count also constrains
    very long inflected sentences without requiring mechanical word slots.
    """
    words=revision_word_target(script,measured_ms,seconds)
    target_ms=seconds*1000-500
    characters=round(len(script)*target_ms/measured_ms)
    words_slack=max(4,round(words*0.06))
    chars_slack=max(25,round(characters*0.08))
    if centered:
        # The accepted audio interval is [target-2100ms, target]. Aim at its
        # midpoint, not its upper edge. An 8% character tolerance previously
        # admitted a LONGER draft after a 45096ms recording exceeded 45s.
        target_ms=seconds*1000-1050
        characters=round(len(script)*target_ms/measured_ms)
        words=max(1,round(len(script.split())*target_ms/measured_ms))
        words_slack=max(3,round(words*.06))
        chars_slack=max(1,math.floor(len(script)*450/measured_ms))
        low=max(1,characters-chars_slack)
        high=characters+chars_slack
        if measured_ms>seconds*1000:
            high=min(high,len(script)-1)
        elif measured_ms<seconds*1000-2100:
            low=max(low,len(script)+1)
        return {'target_words':words,'min_words':max(1,words-words_slack),
                'max_words':words+words_slack,'target_characters':characters,
                'min_characters':low,'max_characters':high}
    return {'target_words':words,'min_words':max(1,words-words_slack),
            'max_words':words+words_slack,
            'target_characters':characters,
            'min_characters':max(1,characters-chars_slack),
            'max_characters':characters+chars_slack}


def revision_length_fits(text, window):
    if not isinstance(text,str) or not text.strip():return False
    count=len(text.split())
    return (window['min_words']<=count<=window['max_words'] and
            window['min_characters']<=len(text)<=window['max_characters'])
