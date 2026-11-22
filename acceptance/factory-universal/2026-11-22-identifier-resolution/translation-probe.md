# Offline translation and revision provenance

Runtime checks passed with isolated SQLite and cache. The parser now requests the MediaWiki revision in the same response as text and links. Live snapshots for N8n, Papermaking, Наднова and Mikroskop returned revision IDs and link maps. An older cache entry whose response did not include the revision cannot overwrite the new snapshot.

- N8n, English, revision 1382794918, 62 links.
- Papermaking, English, revision 1385509448, 81 links.
- Наднова, Ukrainian, revision 49154553, 183 links.
- Mikroskop, Polish, revision 76719573, 37 links.

The translation comparison ran locally with no provider calls. Argos English–Ukrainian 1.4 distorted a description of a node-based editor and mistranslated a financing round. The quantized OPUS-MT English–East Slavic model translated both examples correctly in Ukrainian and Russian, and retained negation and numbers in independent probes. On nine selected sentences from the pinned N8n revision, it still produced literal phrases that are unsuitable as automatic narration, such as translating press coverage as «охоплення». These are translation probes, with no playback or MP4 acceptance. Polish translation was outside this comparison.

Commons queries for n8n, n8n workflow and n8n conference found the logo and unrelated items, with no suitable photographs among the returned candidates. There is no accepted visual storyboard for this topic. Producing a compliant 45-second MP4 still requires 18 distinct relevant images with suitable licences.

Translation weights were used in local scratch space only. Translation and revision changes have no production acceptance in this evidence.

References

- [MediaWiki parse response properties](https://www.mediawiki.org/wiki/API:Parsing_wikitext)
- [Argos model index](https://github.com/argosopentech/argospm-index)
- [Helsinki-NLP original multilingual model](https://huggingface.co/Helsinki-NLP/opus-mt-tc-big-en-zle)
- [Pinned CTranslate2 int8 conversion](https://huggingface.co/NothingSoftware/opus-mt-tc-big-en-zle-ct2-int8/tree/60e35c8d683875ff7ead041d6b9c2ef69237e4e7)
