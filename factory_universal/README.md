# Universal Video Factory

Topic and language → source-grounded vertical MP4 with the selected native voice, distinct photographs, aligned captions and cited sources.

Studio: https://studio.hodor.com.pl/ — no password.

## Delivery

The automatic MP4 workflow is deployed and verified. Evidence: acceptance/factory-universal/2026-11-18/acceptance.json. Five normal outputs cover manufacturing, biology, astronomy and biographies across EN/PL/RU/UK and 15/30/45/60 seconds. All 72 photographs and complete captions were inspected. A further public API create-to-ready run produced a byte-identical copy of a reviewed output. Page/health, video ranges and credits downloads pass.

Owner listening approval remains separate and pending. Inputs require an identifiable source and enough suitable licensed photos; ambiguous or unsupported requests ask for context.

## Pipeline

1. Resolve a primary native-language Wikipedia article and Wikidata identity; preserve exact source spans and revision provenance.
2. Plan complete facts with source-linked biography objects, primary-topic context for other subjects and physical manufacturing stages. Compare feasible fact counts against measured native speaking duration; keep production stages in causal order.
3. Search bounded Commons pools across the entire job: three broad queries, twelve process queries or forty-eight source-linked queries, at most fifty candidates each. Cache source/search results for 24 hours.
4. Verify all 6/12/18/24 unique images before synthesis, minimum two per beat. Require metadata context, pinned local CLIP subject/genre screening and crop/resize deduplication. Preserve the complete photograph on a solid matte.
5. Synthesize with the exact selected Google voice through the retained native credential gateway and PostgreSQL free-tier ledger. Try at most three distinct complete texts to fit the natural window; never change speed, pitch or voice, append filler, or repeat an ambiguous send.
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
