"""Create a narration view of an English article without changing its evidence."""

from collections import Counter
import hashlib
import os
from pathlib import Path
import re


MODEL = 'opus-mt-tc-big-en-zle-ct2-int8@60e35c8d683875ff7ead041d6b9c2ef69237e4e7'
TARGETS = {'uk': 'ukr', 'ru': 'rus'}
MODEL_HASHES = {
    'config.json': '72901fbd8abd89fb5cf4a388f26fc681f5c4c58a1e1a88b30b879f107270e7ee',
    'model.bin': 'fbd24e6fdfa27fb69d4bbce7968eccef693b7a6249ec09733269e96cf2d1a319',
    'shared_vocabulary.json': '558fb7414f75540fc3e9f272dac90cb85272083014978e5a8f81c7e35ae2a49b',
    'source.spm': '3612abfe04bf08344ba91115f0e15e228a7a15a621ea856bfd548097dbaeb43c',
    'target.spm': '22940e744b3a9fd166a04880938fb61f7dfa8ba4b5d2d3f6371a6c4ba8f3b019',
}
MAX_SENTENCES = 36


def configured_for(language):
    return language in TARGETS and bool(os.environ.get('FACTORY_TRANSLATION_MODEL_DIR'))


def translate_batch(sentences, language):
    import ctranslate2
    import sentencepiece

    model_dir = Path(os.environ['FACTORY_TRANSLATION_MODEL_DIR'])
    for name, expected in MODEL_HASHES.items():
        with (model_dir / name).open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != expected:
                raise ValueError('Local translation model checksum mismatch: ' + name)
    encoder = sentencepiece.SentencePieceProcessor(model_file=str(model_dir / 'source.spm'))
    decoder = sentencepiece.SentencePieceProcessor(model_file=str(model_dir / 'target.spm'))
    model = ctranslate2.Translator(str(model_dir), device='cpu', compute_type='int8', intra_threads=2)
    inputs = [[f'>>{TARGETS[language]}<<', *encoder.encode(sentence, out_type=str), '</s>']
              for sentence in sentences]
    results = model.translate_batch(inputs, beam_size=4, max_batch_size=8, max_decoding_length=150)
    return [decoder.decode(result.hypotheses[0]) for result in results]


def identifiers(text):
    return Counter(word.casefold() for word in re.findall(r'\b[A-Za-z0-9]+(?:[-.][A-Za-z0-9]+)*\b', text)
                   if any(c.isdigit() for c in word) and any(c.isalpha() for c in word))


def number_parts(text):
    text = re.sub(r'(?<=\d)[ \u00a0\u202f](?=\d{3}\b)', '', text)
    return re.findall(r'\d+', text)


def usable_translation(original, translated):
    cyrillic = re.findall(r'[А-Яа-яІіЇїЄєҐґЁё]', translated)
    return (translated.endswith(('.', '!', '?')) and len(cyrillic) >= 12
            and number_parts(original) == number_parts(translated)
            and identifiers(original) == identifiers(translated))


def article_view(source, language, split_sentences, translate=translate_batch):
    if not source.get('revision_id') or not source.get('revision_url'):
        raise ValueError('The English source revision could not be verified')
    originals = []
    position = 0
    for sentence in (item for paragraph in source['text'].splitlines() for item in split_sentences(paragraph)):
        sentence = sentence.strip()
        if not sentence:
            continue
        start = source['text'].index(sentence, position)
        position = start + len(sentence)
        if 5 <= len(sentence.split()) <= 60 and sentence.endswith(('.', '!', '?')):
            originals.append((start, sentence))
        if len(originals) == MAX_SENTENCES:
            break
    if not originals:
        return {}

    translations = translate([sentence for _, sentence in originals], language)
    lines = []
    evidence = {}
    offset = 0
    for (start, original), raw in zip(originals, translations, strict=True):
        translated = ' '.join(raw.split())
        if not usable_translation(original, translated) or translated in lines:
            continue
        evidence[str(offset)] = {'source_start': start, 'source_span': original,
                                 'translated_span': translated}
        lines.append(translated)
        offset += len(translated) + 1
    if not lines:
        return {}
    return {**source, 'text': '\n'.join(lines), 'source_language': 'en',
            'translation_model': MODEL, 'translated_spans': evidence}
