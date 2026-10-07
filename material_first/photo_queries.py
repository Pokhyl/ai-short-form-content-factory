"""Keep real-photo searches focused on entities, before paid inspection work."""
import re

SYNTHETIC = re.compile(
    r"\b(?:artist(?:['’]s)?[- _]*(?:concept|impression)|concept\s+art|"
    r"artistic\s+(?:concept|impression|rendering)|illustrations?|schematic|diagram|"
    r"cross[- ]section|synthetic\s+rendering|3d\s+render(?:ing)?|"
    r"computer[- ]generated|animation|visuali[sz]ation)\b", re.I)
INVISIBLE = re.compile(r"\b(?:magnetic\s+field\s+beams?|field\s+lines|imagined\s+particle\s+beams?)\b", re.I)


def photograph_query(query):
    cleaned = INVISIBLE.sub(" ", SYNTHETIC.sub(" ", query))
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,:;-.")
    cleaned = re.sub(r"^(?:of|a|an|the)\s+", "", cleaned, flags=re.I)
    if not cleaned or not re.search(r"[A-Za-z]", cleaned):
        raise ValueError("photo query has no actual subject after excluding synthetic scene modifiers")
    return cleaned


def described_as_synthetic(candidate):
    # Credits can mention an illustrator of a companion figure. Evaluate the
    # actual file title/description, not its credit string.
    text = str(candidate.get("description", "")) + " " + str(candidate.get("source_metadata", {}).get("title", ""))
    return bool(SYNTHETIC.search(text))


def relevance(candidate, query):
    from .metadata import words
    return len(words(str(candidate.get("description", ""))) & words(query))
