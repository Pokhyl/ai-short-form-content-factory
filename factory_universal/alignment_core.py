"""Pure alignment logic retained from this project media worker."""
import re,unicodedata,difflib
MAX_WHISPER_TERMINAL_OVERRUN_MS = 1000

JOB_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
    r"[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-"
    r"[0-9a-fA-F]{12}$"
)

ALIGNMENT_NUMBER_VALUES = {
    # English
    "zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,
    "eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12,"thirteen":13,
    "fourteen":14,"fifteen":15,"sixteen":16,"seventeen":17,"eighteen":18,
    "nineteen":19,"twenty":20,"thirty":30,"forty":40,"fifty":50,"sixty":60,
    "seventy":70,"eighty":80,"ninety":90,"hundred":100,"thousand":1000,
    # Polish
    "zero":0,"jeden":1,"jedna":1,"jedno":1,"dwa":2,"dwie":2,"trzy":3,
    "cztery":4,"pięć":5,"piec":5,"sześć":6,"szesc":6,"siedem":7,"osiem":8,
    "dziewięć":9,"dziewiec":9,"dziesięć":10,"dziesiec":10,
    "jedenaście":11,"jedenascie":11,"dwanaście":12,"dwanascie":12,
    "trzynaście":13,"trzynascie":13,"czternaście":14,"czternascie":14,
    "piętnaście":15,"pietnascie":15,"szesnaście":16,"szesnascie":16,
    "siedemnaście":17,"siedemnascie":17,"osiemnaście":18,"osiemnascie":18,
    "dziewiętnaście":19,"dziewietnascie":19,"dwadzieścia":20,"dwadziescia":20,
    "trzydzieści":30,"trzydziesci":30,"czterdzieści":40,"czterdziesci":40,
    "pięćdziesiąt":50,"piecdziesiat":50,"sześćdziesiąt":60,"szescdziesiat":60,
    "siedemdziesiąt":70,"siedemdziesiat":70,"osiemdziesiąt":80,
    "osiemdziesiat":80,"dziewięćdziesiąt":90,"dziewiecdziesiat":90,
    "sto":100,"tysiąc":1000,"tysiac":1000,
    # Russian
    "ноль":0,"один":1,"одна":1,"одно":1,"два":2,"две":2,"три":3,"четыре":4,
    "пять":5,"шесть":6,"семь":7,"восемь":8,"девять":9,"десять":10,
    "одиннадцать":11,"двенадцать":12,"тринадцать":13,"четырнадцать":14,
    "пятнадцать":15,"шестнадцать":16,"семнадцать":17,"восемнадцать":18,
    "девятнадцать":19,"двадцать":20,"тридцать":30,"сорок":40,"пятьдесят":50,
    "шестьдесят":60,"семьдесят":70,"восемьдесят":80,"девяносто":90,
    "сто":100,"тысяча":1000,"тысяч":1000,
    # Ukrainian
    "нуль":0,"один":1,"одна":1,"одне":1,"два":2,"дві":2,"три":3,"чотири":4,
    "п’ять":5,"п'ять":5,"шість":6,"сім":7,"вісім":8,"дев’ять":9,"дев'ять":9,
    "десять":10,"одинадцять":11,"дванадцять":12,"тринадцять":13,
    "чотирнадцять":14,"п’ятнадцять":15,"п'ятнадцять":15,"шістнадцять":16,
    "сімнадцять":17,"вісімнадцять":18,"дев’ятнадцять":19,"дев'ятнадцять":19,
    "двадцять":20,"тридцять":30,"сорок":40,"п’ятдесят":50,"п'ятдесят":50,
    "шістдесят":60,"сімдесят":70,"вісімдесят":80,"дев’яносто":90,
    "дев'яносто":90,"сто":100,"тисяча":1000,"тисяч":1000,
}

# Lexemes remove apostrophes; number dictionary keys must use the same spelling.
ALIGNMENT_NUMBER_VALUES = {re.sub(r"['’ʼ‘]", "", word):value for word,value in ALIGNMENT_NUMBER_VALUES.items()}

ALIGNMENT_ORDINAL_PREFIX_VALUES = {
    # English 11th-20th
    "eleventh":11,"twelfth":12,"thirteenth":13,"fourteenth":14,"fifteenth":15,
    "sixteenth":16,"seventeenth":17,"eighteenth":18,"nineteenth":19,"twentieth":20,
    # Polish inflected ordinal stems
    "jedenast":11,"dwunast":12,"trzynast":13,"czternast":14,"piętnast":15,
    "pietnast":15,"szesnast":16,"siedemnast":17,"osiemnast":18,
    "dziewiętnast":19,"dziewietnast":19,"dwudziest":20,
    # Russian inflected ordinal stems
    "одиннадцат":11,"двенадцат":12,"тринадцат":13,"четырнадцат":14,
    "пятнадцат":15,"шестнадцат":16,"семнадцат":17,"восемнадцат":18,
    "девятнадцат":19,"двадцат":20,
    # Ukrainian inflected ordinal stems
    "одинадцят":11,"дванадцят":12,"тринадцят":13,"чотирнадцят":14,
    "пятнадцят":15,"шістнадцят":16,"сімнадцят":17,"вісімнадцят":18,
    "девятнадцят":19,"двадцят":20,
}

def _roman_numeral_to_int(token):
    values = {"I":1,"V":5,"X":10,"L":50,"C":100,"D":500,"M":1000}
    total = 0
    previous = 0
    for char in reversed(token):
        value = values[char]
        if value < previous:
            total -= value
        else:
            total += value
            previous = value
    return total

def _replace_alignment_roman_numerals(value):
    text = str(value or "")
    def replace(match):
        token = match.group(0)
        value = _roman_numeral_to_int(token)
        if value <= 0 or value > 3999:
            return token
        return str(value)
    # Require uppercase and at least two Roman characters so English pronoun
    # "I" and ordinary lowercase words are never interpreted as numbers.
    return re.sub(r"(?<![\w])(?:[IVXLCDM]{2,})(?![\w])", replace, text)

def _alignment_lexemes(value):
    normalized = unicodedata.normalize(
        "NFKC",
        _replace_alignment_roman_numerals(value),
    ).casefold()
    # Whisper may preserve an apostrophe in the segment transcript while
    # dropping it at token boundaries (for example Ukrainian в'язкою).
    # Apostrophes are punctuation, not lexical content, so remove common
    # apostrophe variants before both transcript and token normalization.
    normalized = re.sub(r"['’ʼ‘]", "", normalized)
    return re.findall(
        r"\d+|[^\W\d_]+",
        normalized,
        flags=re.UNICODE,
    )

def _number_words_to_int(words):
    current = 0
    total = 0
    for word in words:
        value = ALIGNMENT_NUMBER_VALUES[word]
        if value == 100:
            current = max(1, current) * 100
        elif value == 1000:
            total += max(1, current) * 1000
            current = 0
        else:
            current += value
    return total + current

def _canonical_alignment_lexemes(lexemes):
    out = []
    index = 0
    while index < len(lexemes):
        token = lexemes[index]
        if token.isdigit():
            out.append(str(int(token)))
            index += 1
            continue

        ordinal_value = next(
            (
                value
                for prefix, value in ALIGNMENT_ORDINAL_PREFIX_VALUES.items()
                if token.startswith(prefix)
            ),
            None,
        )
        if ordinal_value is not None:
            out.append(str(ordinal_value))
            index += 1
            continue

        if token in ALIGNMENT_NUMBER_VALUES:
            end = index + 1
            while end < len(lexemes) and lexemes[end] in ALIGNMENT_NUMBER_VALUES:
                end += 1
            out.append(str(_number_words_to_int(lexemes[index:end])))
            index = end
            continue

        out.append(token)
        index += 1
    return out

def normalize_alignment_text(value):
    return "".join(_canonical_alignment_lexemes(_alignment_lexemes(value)))

def _lexical_tokens(whisper_payload):
    raw_rows = []
    pending_boundary = True

    for segment_index, segment in enumerate(
        whisper_payload.get("transcription") or []
    ):
        segment_boundary = True
        for token in segment.get("tokens") or []:
            token_text = str(token.get("text") or "")
            stripped = token_text.strip()

            if stripped.startswith("[_") and stripped.endswith("]"):
                pending_boundary = True
                continue

            lexemes = _alignment_lexemes(token_text)
            if not lexemes:
                # An apostrophe emitted as its own token remains inside a word.
                if stripped and not re.fullmatch(r"['’ʼ‘]+", stripped):
                    pending_boundary = True
                continue

            offsets = token.get("offsets") or {}
            try:
                start_ms = int(offsets.get("from"))
                end_ms = int(offsets.get("to"))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "whisper lexical token is missing numeric offsets"
                ) from exc

            if start_ms < 0 or end_ms < start_ms:
                raise ValueError("whisper lexical token has invalid offsets")

            starts_word = bool(re.match(r"\s", token_text))
            raw_rows.append(
                {
                    "text": token_text,
                    "lexemes": lexemes,
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "segment_index": segment_index,
                    "starts_word": (
                        starts_word or pending_boundary or segment_boundary
                    ),
                }
            )
            pending_boundary = False
            segment_boundary = False

    if not raw_rows:
        raise ValueError("whisper returned no lexical tokens")

    # Whisper tokens are model subwords, not guaranteed lexical words.
    # Rejoin adjacent subword pieces before semantic normalization so a
    # lexical item has the same representation in transcript text and
    # token timing data.
    word_rows = []
    current = None
    for row in raw_rows:
        if current is None or row["starts_word"]:
            if current is not None:
                word_rows.append(current)
            current = {
                "text": row["text"],
                "start_ms": row["start_ms"],
                "end_ms": row["end_ms"],
                "segment_index": row["segment_index"],
            }
        else:
            current["text"] += row["text"]
            current["end_ms"] = row["end_ms"]

    if current is not None:
        word_rows.append(current)

    for row in word_rows:
        row["lexemes"] = _alignment_lexemes(row["text"])

    rows = []
    index = 0
    while index < len(word_rows):
        row = word_rows[index]
        lexemes = row["lexemes"]

        if lexemes and all(
            token in ALIGNMENT_NUMBER_VALUES for token in lexemes
        ):
            end = index + 1
            merged_lexemes = list(lexemes)
            while end < len(word_rows):
                next_lexemes = word_rows[end]["lexemes"]
                if not next_lexemes or not all(
                    token in ALIGNMENT_NUMBER_VALUES
                    for token in next_lexemes
                ):
                    break
                merged_lexemes.extend(next_lexemes)
                end += 1

            rows.append(
                {
                    "text": "".join(
                        word_rows[pos]["text"]
                        for pos in range(index, end)
                    ),
                    "normalized": str(
                        _number_words_to_int(merged_lexemes)
                    ),
                    "start_ms": row["start_ms"],
                    "end_ms": word_rows[end - 1]["end_ms"],
                }
            )
            index = end
            continue

        token_normalized = "".join(
            _canonical_alignment_lexemes(lexemes)
        )
        if token_normalized:
            rows.append(
                {
                    "text": row["text"],
                    "normalized": token_normalized,
                    "start_ms": row["start_ms"],
                    "end_ms": row["end_ms"],
                }
            )
        index += 1

    if not rows:
        raise ValueError("whisper returned no lexical tokens")

    return rows

def _build_scene_timings(
    narration,
    scenes,
    whisper_payload,
    audio_duration_ms,
):
    if not isinstance(narration, str) or not narration.strip():
        raise ValueError("narration is required")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("scenes must be a non-empty array")

    expected_normalized = normalize_alignment_text(narration)
    if not expected_normalized:
        raise ValueError("normalized narration is empty")

    whisper_segments = whisper_payload.get("transcription") or []
    transcript = "".join(
        str(segment.get("text") or "")
        for segment in whisper_segments
    ).strip()
    transcript_normalized = normalize_alignment_text(transcript)
    if not transcript_normalized:
        raise ValueError("normalized whisper transcript is empty")

    tokens = _lexical_tokens(whisper_payload)
    token_normalized = "".join(token["normalized"] for token in tokens)

    if token_normalized != transcript_normalized:
        raise ValueError(
            "whisper lexical tokens do not reconstruct the normalized transcript"
        )

    scene_joined = " ".join(
        str(scene.get("narration") or "").strip()
        for scene in scenes
    )
    if normalize_alignment_text(scene_joined) != expected_normalized:
        raise ValueError("scene narrations do not reconstruct the final narration")

    matcher = difflib.SequenceMatcher(
        a=expected_normalized,
        b=transcript_normalized,
        autojunk=False,
    )
    matching_blocks = [
        block
        for block in matcher.get_matching_blocks()
        if block.size > 0
    ]

    matched_chars = sum(block.size for block in matching_blocks)
    global_coverage = matched_chars / len(expected_normalized)

    if global_coverage < 0.95:
        raise ValueError(
            "global lexical alignment coverage below 0.95: "
            f"{global_coverage:.4f}"
        )

    token_ranges = []
    char_cursor = 0
    for token in tokens:
        start_char = char_cursor
        end_char = start_char + len(token["normalized"])
        token_ranges.append(
            {
                **token,
                "start_char": start_char,
                "end_char": end_char,
            }
        )
        char_cursor = end_char

    matched_actual_spans = [
        (block.b, block.b + block.size)
        for block in matching_blocks
    ]
    matched_tokens = [
        token
        for token in token_ranges
        if any(
            token["end_char"] > span_start
            and token["start_char"] < span_end
            for span_start, span_end in matched_actual_spans
        )
    ]
    if not matched_tokens:
        raise ValueError("whisper returned no matched lexical timing coverage")

    # Terminal timing belongs to the expected narration, not to unmatched ASR
    # hallucinations after it (for example a trailing "[music]" annotation).
    # Real narration tokens that run beyond the audio remain fail-closed.
    raw_lexical_end_ms = matched_tokens[-1]["end_ms"]
    terminal_overrun_ms = max(0, raw_lexical_end_ms - audio_duration_ms)
    if terminal_overrun_ms > MAX_WHISPER_TERMINAL_OVERRUN_MS:
        raise ValueError(
            "whisper lexical timing exceeds audio duration beyond tolerance: "
            f"{terminal_overrun_ms}ms"
        )

    scene_timings = []
    expected_cursor = 0
    previous_end_ms = 0

    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            raise ValueError(f"scene {index} must be an object")

        scene_uuid = str(scene.get("scene_uuid") or "").strip().lower()
        scene_key = str(scene.get("scene_key") or "").strip()
        scene_narration = str(scene.get("narration") or "").strip()

        if not JOB_ID_RE.fullmatch(scene_uuid):
            raise ValueError(f"scene {index} has invalid scene_uuid")
        if not scene_key:
            raise ValueError(f"scene {index} has empty scene_key")

        scene_normalized = normalize_alignment_text(scene_narration)
        if not scene_normalized:
            raise ValueError(f"scene {scene_key} has empty narration")

        scene_start_char = expected_cursor
        scene_end_char = scene_start_char + len(scene_normalized)

        if expected_normalized[scene_start_char:scene_end_char] != scene_normalized:
            raise ValueError(f"scene {scene_key} is not contiguous in narration")

        scene_matched_chars = 0
        matched_actual_spans = []

        for block in matching_blocks:
            overlap_start = max(scene_start_char, block.a)
            overlap_end = min(scene_end_char, block.a + block.size)
            if overlap_end <= overlap_start:
                continue

            span_size = overlap_end - overlap_start
            scene_matched_chars += span_size

            actual_start = block.b + (overlap_start - block.a)
            actual_end = actual_start + span_size
            matched_actual_spans.append((actual_start, actual_end))

        scene_coverage = scene_matched_chars / len(scene_normalized)
        if scene_coverage < 0.85:
            raise ValueError(
                f"scene {scene_key} lexical coverage below 0.85: "
                f"{scene_coverage:.4f}"
            )

        overlapping = [
            token
            for token in token_ranges
            if any(
                token["end_char"] > span_start
                and token["start_char"] < span_end
                for span_start, span_end in matched_actual_spans
            )
        ]

        if not overlapping:
            raise ValueError(f"scene {scene_key} has no matched lexical timing coverage")

        # Whisper may merge two spoken words across a visual scene cut into
        # one lexical token. Attribute each scene its matched character span
        # within that token, preserving the token's original time interval.
        def matched_token_time(token, *, first):
            intersections = [
                (max(token["start_char"], span_start),
                 min(token["end_char"], span_end))
                for span_start, span_end in matched_actual_spans
                if token["end_char"] > span_start
                and token["start_char"] < span_end
            ]
            char_index = (
                min(start for start, _ in intersections)
                if first else max(end for _, end in intersections)
            )
            width = token["end_char"] - token["start_char"]
            if width <= 0:
                raise ValueError("whisper lexical token has empty character span")
            offset = round(
                (char_index - token["start_char"])
                * (token["end_ms"] - token["start_ms"]) / width
            )
            return token["start_ms"] + offset

        start_ms = matched_token_time(overlapping[0], first=True)
        raw_end_ms = matched_token_time(overlapping[-1], first=False)
        end_ms = min(raw_end_ms, audio_duration_ms)

        if start_ms < previous_end_ms:
            raise ValueError(f"scene {scene_key} timing is not monotonic")
        if start_ms >= audio_duration_ms:
            raise ValueError(f"scene {scene_key} starts beyond audio duration")
        if end_ms <= start_ms:
            raise ValueError(f"scene {scene_key} timing has non-positive duration")

        scene_timings.append(
            {
                "scene_uuid": scene_uuid,
                "scene_key": scene_key,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "coverage": round(scene_coverage, 6),
            }
        )

        previous_end_ms = end_ms
        expected_cursor = scene_end_char

    if expected_cursor != len(expected_normalized):
        raise ValueError("scene timing coverage does not reach narration end")

    return {
        "transcript": transcript,
        "normalized_match": transcript_normalized == expected_normalized,
        "alignment_method": "whisper_token_sequence_match",
        "global_coverage": round(global_coverage, 6),
        "lexical_token_count": len(tokens),
        "lexical_start_ms": tokens[0]["start_ms"],
        "lexical_end_ms": min(raw_lexical_end_ms, audio_duration_ms),
        "lexical_end_ms_raw": raw_lexical_end_ms,
        "terminal_overrun_ms": terminal_overrun_ms,
        "scene_timings": scene_timings,
    }
