from __future__ import annotations

import re
import unicodedata

# V4 deliberately makes the semantic director produce spoken-form text.  This
# module is a safety boundary, not a topic dictionary or a second language
# model.  Ambiguous written forms fail before TTS instead of being guessed.

_SPACE_RE = re.compile(r"\s+")
_DIGIT_RE = re.compile(r"\d")
_URL_RE = re.compile(r"(?:https?://|www\.|\b\S+@\S+\.\S+\b)", re.IGNORECASE)
_SYMBOL_RE = re.compile(r"[%‰€$£₴₽¥₹+×÷=<>№#@]")
_PARENS_RE = re.compile(r"[()\[\]{}]")
_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


def normalize_surface(text: str) -> str:
    """Apply language-independent cleanup while preserving spoken wording."""
    value = unicodedata.normalize("NFKC", str(text or ""))
    # Editorial stress marks from dictionary/encyclopedia copy are not TTS
    # instructions and were audible noise in semantic-v3.
    value = value.replace("\u0301", "")
    value = value.replace("\u00a0", " ")
    value = value.replace("…", "...")
    value = value.replace("–", "-").replace("—", " - ")
    value = _SPACE_RE.sub(" ", value).strip()
    return value


def _looks_like_abbreviation(token: str) -> bool:
    if len(token) < 2 or len(token) > 8:
        return False
    letters = [ch for ch in token if ch.isalpha()]
    if len(letters) != len(token):
        return False
    upper_positions = [i for i, ch in enumerate(token) if ch.isupper()]
    if len(upper_positions) >= 2:
        return True
    # Mixed-case short forms such as kHz / кГц have an internal capital.
    return any(i > 0 for i in upper_positions)


def speech_issues(text: str) -> list[str]:
    value = normalize_surface(text)
    issues: list[str] = []
    if not value:
        return ["empty spoken text"]
    if _DIGIT_RE.search(value):
        issues.append("digits must be written as spoken words")
    if _SYMBOL_RE.search(value):
        issues.append("symbols must be verbalized")
    if _PARENS_RE.search(value):
        issues.append("parenthetical/editorial notation is not allowed in spoken text")
    if _URL_RE.search(value):
        issues.append("URLs/emails must not be sent to TTS")
    abbreviations = sorted({tok for tok in _WORD_RE.findall(value) if _looks_like_abbreviation(tok)})
    if abbreviations:
        issues.append("ambiguous abbreviations must be expanded: " + ", ".join(abbreviations))
    return issues


def ensure_speech_ready(text: str) -> str:
    value = normalize_surface(text)
    issues = speech_issues(value)
    if issues:
        raise ValueError("speech-ready validation failed: " + "; ".join(issues))
    return value
