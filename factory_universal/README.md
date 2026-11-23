# Universal Video Factory

Topic and language → source-grounded vertical MP4 with the selected native voice, distinct photographs, aligned captions and cited sources.

Studio: https://studio.hodor.com.pl/ — no password.

## Delivery

The current release resolves verified split-title spellings and checks historical dates and catalog identifiers when the narration names them. The unauthenticated browser request «супер нова» completed a 45-second Ukrainian MP4. Frame and caption review accepted astronomy and English plant-biology outputs. The Polish microscope result requires stronger visual grounding for named historical facts and remains outside accepted examples. See acceptance/factory-universal/2026-11-22-source-resolution/.

Owner listening approval remains separate and pending. Inputs require an identifiable source and enough suitable licensed photos. A brief starting with an exact alphanumeric identifier can resolve its subject through another Wikipedia edition and follow a published link to the selected language. Studio reports when the native article is unavailable. The script must cover the requested focus.

The staged local translation path covers English source articles for verified identifiers with no Ukrainian or Russian edition. It requires `FACTORY_TRANSLATION_MODEL_DIR`, the checksum-pinned CTranslate2 model specified in `source_translation.py`, CTranslate2 4.9.1 and SentencePiece 0.2.1. A translated beat carries both the original sentence and its translated text, plus the article revision. The normal source scope, image, voice and render gates still apply. Production currently uses native sources.

## Pipeline

1. Resolve a primary native-language Wikipedia article and Wikidata identity; preserve exact source spans and revision provenance.
2. Plan complete facts with source-linked biography objects, primary-topic context for other subjects and physical manufacturing stages. Compare feasible fact counts against completed native measurements, combining character counts with silent pronunciation estimates; keep production stages in causal order.
3. Search bounded Commons pools across the entire job: three broad queries, eight for named places or insect scenes, twelve process queries or forty-eight source-linked queries, at most fifty candidates each. Cache source/search results for 24 hours.
4. Verify all 6/12/18/24 unique images before synthesis, minimum two per beat. Require metadata context, pinned local CLIP subject/genre screening and crop/resize deduplication. Preserve the complete photograph on a solid matte.
5. Synthesize with the exact selected Google voice through the retained native credential gateway and PostgreSQL free-tier ledger. Exclude verified cached recordings outside the requested speech window before photo preparation. Try at most three distinct complete source-backed texts, stop on an ambiguous send, and preserve the selected recording's voice, pitch and speed.
6. Align the unchanged native recording using the existing media worker; render 1080×1920 H.264/AAC at 30 fps with exactly 450/900/1350/1800 frames, then fully decode and verify the result.

No Gemini or paid model APIs. eSpeak is an internal duration estimate only and is never audible output.

| Language | Owner-selected voice |
|---|---|
| EN | en-US-Chirp3-HD-Algenib |
| PL | pl-PL-Chirp3-HD-Enceladus |
| RU | ru-RU-Wavenet-D |
| UK | uk-UA-Chirp3-HD-Enceladus |

Subject CLIP gates remain .24 positive/.015 margin; ASR .95 global/.85 per scene. Bounded CLIP caches retain 256 image vectors and 128 complete text batches. Real-image verification found zero score difference versus full encoder execution; repeated inputs avoid inference. See visual_cache_checks.py and the dated evidence.

## Licenses and review

New adaptations use CC BY-SA 4.0. Compatible Commons media, including CC BY-SA 3.0/4.0, retain their original author/source/license/change notices. NC/ND/unknown media are rejected. MP4 tags embed full attribution; credits.txt and credits.json accompany the output, with /api/jobs/{id}/credits available in Studio. The manifest records sources, licenses, hashes, voice receipts, alignment and renderer gates.

The current Examples view contains the five reviewed outputs. Old tests and failures remain in history. Assistant frame inspection and automated checks do not constitute owner listening approval.

## Operation

Active server checkout: /opt/factory-universal. Docker Compose: factory_universal/compose.yaml, app service only. Delivery branch: codex/factory-universal-20261112. Read docs/CODEX_START_HERE.md and root AGENTS.md before work. Existing server credentials/settings remain retained; never print or commit them or modify shared services.

One worker, 900-second deadline, 2-GiB owned output limit including ASR/reviews, 512-MiB cache, 30-day retention and a 2-GiB free-disk reserve. Cleanup selects exact factory SQLite-owned UUID directories. No global Docker prune or unrelated-file removal. Image GET 503 permits two delayed retries; 429 and ambiguous native sends are never blindly replayed.

Run runtime checks with:

```sh
docker compose -f factory_universal/compose.yaml run --rm --no-deps -T app python3 - <factory_universal/checks.py
```

Run alignment_checks.py and renderer_checks.py when relevant. visual_cache_checks.py accepts --images and --receipt for local real-image encoder-equivalence checks. stage_outputs.py exercises the normal worker from a staged image; its receipt is immutable and never replayed. preflight_outputs.py is image-only. review_outputs.py collects existing outputs and actual midpoint frames without creating jobs or synthesis.

Before deployment verify no active jobs, publish source/evidence and recreate only app with --no-deps. Verify the running image, implementation hashes, public routes and a normal public create-to-ready flow. Preserve the owner-rejected historical IDs and their review decisions.

Browser QA uses the existing Chrome installation in an isolated headless context, without credentials. Install the optional pinned requirements in a project-local environment and run browser_regression.py --receipt /absolute/path/result.json. Its default is read-only; --submit-topic explicitly creates one recorded job with --language and --duration. Existing receipts are never replayed. The check covers default/user and example views, continuous video playback across refresh, mobile overflow, JavaScript errors and retained form selections.
