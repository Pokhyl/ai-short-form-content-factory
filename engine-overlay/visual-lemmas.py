"""Pinned dictionary lookups only: no stemming, edit distance or suffix guessing."""
import json
import sys
from simplemma.strategies.dictionary_lookup import DictionaryLookupStrategy

request = json.load(sys.stdin)
if request['lang'] not in ('uk', 'ru', 'pl', 'en'):
    raise ValueError('Unsupported visual language')
lookup = DictionaryLookupStrategy()
if request['lang'] == 'pl':
    import morfeusz2
    polish = morfeusz2.Morfeusz()

def lemmas(word):
    if request['lang'] == 'pl':
        # Retain all dictionary analyses (e.g. noun/verb homographs), never guess
        # a suffix or privilege the dictionary's first interpretation.
        return sorted({word, *(edge[2][1].split(':')[0].lower()
                             for edge in polish.analyse(word)
                             if edge[2][2] != 'ign')})
    return sorted({word, (lookup.get_lemma(word, request['lang']) or word).lower()})

print(json.dumps([lemmas(word) for word in request['words']], ensure_ascii=False))
