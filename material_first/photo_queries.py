"""Keep real-photo searches focused on entities, before image inspection."""
import re
from urllib.parse import urlsplit, unquote

SYNTHETIC = re.compile(
    r"\b(?:artist(?:['’]s|\s+s)?[- _]*(?:concept|impression)|concept\s+art|"
    r"artistic\s+(?:concept|impression|rendering)|illustrations?|schematic|diagram|"
    r"cross[- ]section|synthetic\s+rendering|3d\s+render(?:ing)?|"
    r"computer[- ]generated|(?:this|computer|supercomputer|numerical)\s+simulations?|"
    r"simulated\s+(?:image|scene|view)|animation|visuali[sz]ation)\b", re.I)
INVISIBLE = re.compile(r"\b(?:magnetospheres?|magnetic\s+field\s+beams?|field\s+lines|imagined\s+particle\s+beams?)\b", re.I)


def photograph_query(query):
    cleaned = INVISIBLE.sub(" ", SYNTHETIC.sub(" ", query))
    cleaned = re.sub(r"\b(?:art|artwork|render|rendering|artistic)\b", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,:;-.")
    cleaned = re.sub(r"^(?:of|a|an|the)\s+", "", cleaned, flags=re.I)
    if not cleaned or not re.search(r"[A-Za-z]", cleaned):
        raise ValueError("photo query has no actual subject after excluding synthetic scene modifiers")
    return cleaned


def described_as_synthetic(candidate):
    # Credits can mention an illustrator of a companion figure. Evaluate the
    # actual file title/description, not its credit string.
    source_path = unquote(urlsplit(str(candidate.get("source_url", ""))).path).replace("-", " ").replace("_", " ")
    text = str(candidate.get("description", "")) + " " + str(candidate.get("source_metadata", {}).get("title", "")) + " " + source_path
    return bool(SYNTHETIC.search(text))


def relevance(candidate, query):
    from .metadata import words
    text = str(candidate.get("description", "")) + " " + str(candidate.get("source_metadata", {}).get("title", ""))
    return len(words(text) & words(query))
